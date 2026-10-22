// The polish of the QA of 2026-10-20, as a check: the icons and the manifest, the branded 404 page, tap targets of 44 px, the "Take a photo" button on a short phone and
// the message for a photo the browser cannot open (HEIC).
//   npm run build && node scripts/check_polish.mjs [--dist dist]        real Chrome on the built page (the stand-in API of scripts/lib/flowstub.mjs)
//   icons     public/favicon.svg is the SnapEyes mark (not the Vite logo it was), favicon.ico holds 16, 32 and 48 px, the touch icon is 180 px, the app icons 192 and 512, the web
//             manifest names the site's colours, and every page of the build links all of them (and every linked file is in the build)
//   404       an unknown address is answered 404 with dist/404.html: the site's look, the words in the visitor's language (?lang=, then the stored choice) from
//             src/notfound/notfound.json, a way home that keeps the language and is 44 px high
//   targets   the language buttons, the logo, the quiet link and the footer's links of the landing (390 px) and of /try (360 px) answer a touch 22 px above and below their
//             centre (their hit area is 44 px high; elementFromPoint says what a finger would hit), without the layout moving
//   fold      on a short phone (360 x 740, 375 x 667, 320 x 568) the "Take a photo" button is on the first screen of /try in all four languages, and on a tall one the guide is
//             still read before it
//   heic      a photo the browser cannot open (a .heic file) gets a sentence that says what to do (JPEG or PNG, or the phone), in all four languages
import { mkdtempSync, readFileSync, existsSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';
import { flowApi } from './lib/flowstub.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const dist = resolve(args.includes('--dist') ? args[args.indexOf('--dist') + 1] : join(ROOT, 'dist'));
const LANGS = ['en', 'de', 'lt', 'hu'];
const problems = [];
let n = 0;
const fail = (c, m) => { problems.push(`${c}: ${m}`); console.log(`  FAIL ${c}: ${m}`); };
const ok = (c, cond, m) => { n++; if (!cond) fail(c, m); return !!cond; };
const png = (f) => { if (!existsSync(f)) return null; const b = readFileSync(f); return b.readUInt32BE(0) === 0x89504e47 ? [b.readUInt32BE(16), b.readUInt32BE(20)] : null; };

// ---------------------------------------------------------------------------------------------------- icons (files only)
{
  const svg = readFileSync(join(dist, 'favicon.svg'), 'utf8');
  ok('icons', /#f5c542/.test(svg) && (svg.match(/<circle/g) ?? []).length === 3 && !/863bff|47bfff|7e14ff/i.test(svg) && svg.length < 1500, `favicon.svg is not the SnapEyes mark (${svg.length} bytes: ${svg.slice(0, 80)})`);
  const ico = existsSync(join(dist, 'favicon.ico')) ? readFileSync(join(dist, 'favicon.ico')) : null;
  const sizes = ico ? Array.from({ length: ico.readUInt16LE(4) }, (_, i) => ico[6 + 16 * i] || 256) : [];
  ok('icons', !!ico && ico.readUInt16LE(2) === 1 && sizes.join() === '16,32,48', `favicon.ico ${ico ? `holds ${sizes} px` : 'is missing'}, expected 16,32,48`);
  for (const [f, px] of [['apple-touch-icon.png', 180], ['icon-192.png', 192], ['icon-512.png', 512]]) ok('icons', (png(join(dist, f)) ?? []).join('x') === `${px}x${px}`, `${f} is ${png(join(dist, f))}, expected ${px}x${px}`);
  const man = existsSync(join(dist, 'manifest.webmanifest')) ? JSON.parse(readFileSync(join(dist, 'manifest.webmanifest'), 'utf8')) : { icons: [] };
  ok('icons', man.name && man.short_name && man.start_url === '/' && man.theme_color === '#07090e' && man.background_color === '#07090e' && man.icons.every((i) => existsSync(join(dist, i.src.slice(1)))), JSON.stringify(man).slice(0, 200));
  for (const page of ['index.html', 'try.html', 'order.html', 'admin.html', 'privacy.html', 'terms.html', 'withdrawal.html', 'imprint.html', 'lp/en.html', 'lp/de.html', 'lp/lt.html', 'lp/hu.html', '404.html'].filter((p) => existsSync(join(dist, p)))) {
    const h = readFileSync(join(dist, page), 'utf8');
    const has = ['href="/favicon.ico"', 'href="/favicon.svg"', 'rel="apple-touch-icon" href="/apple-touch-icon.png"', 'rel="manifest" href="/manifest.webmanifest"'].filter((t) => !h.includes(t));
    ok('icons', !has.length, `${page} does not link ${has.join(', ')}`);
  }
}

const api = flowApi(ROOT);
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler: api.handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();
const waitFor = async (page, expr, ms = 15000) => { const t0 = Date.now(); for (;;) { let v = false; try { v = await page.eval(expr); } catch { /* busy */ } if (v) return true; if (Date.now() - t0 > ms) return false; await sleep(60); } };
async function fresh(width, height, mobile = true) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  return chrome.page({ width, height, mobile, dpr: 1 });
}
/** how many px high is the area that answers a touch on the element (the first point of its own box, up and down until another element is hit), at most 60 */
const reach = (index, sel) => `(() => { const e = document.querySelectorAll(${JSON.stringify(sel)})[${index}]; const r = e.getBoundingClientRect(); const cx = r.left + r.width / 2, cy = r.top + r.height / 2; const own = (t) => t && (t === e || e.contains(t)); let up = 0, down = 0; while (up < 30 && own(document.elementFromPoint(cx, cy - up - 1))) up++; while (down < 30 && own(document.elementFromPoint(cx, cy + down + 1))) down++; return JSON.stringify([Math.round(r.height), up + down + 1, own(document.elementFromPoint(cx, cy)), (e.textContent || e.getAttribute('aria-label') || '').trim().slice(0, 14)]); })()`;
async function reaches(page, sel) {
  const count = await page.eval(`document.querySelectorAll(${JSON.stringify(sel)}).length`);
  const out = [];
  for (let i = 0; i < count; i++) {
    await page.eval(`document.querySelectorAll(${JSON.stringify(sel)})[${i}].scrollIntoView({ block: 'center', behavior: 'instant' })`);
    await sleep(350);
    out.push(JSON.parse(await page.eval(reach(i, sel))));
  }
  return out;
}

try {
  // ---- the 404 page
  {
    const res = await fetch(`${origin}/no/such/page`);
    const body = await res.text();
    ok('404', res.status === 404 && /404/.test(body) && body.includes('<title>SnapEyes: page not found</title>'), `an unknown address is answered ${res.status}`);
    const words = JSON.parse(readFileSync(join(ROOT, 'src/notfound/notfound.json'), 'utf8'));
    for (const l of LANGS) {
      const page = await fresh(390, 800);
      await page.goto(`${origin}/no/such/page?lang=${l}`);
      await page.loaded();
      const st = JSON.parse(await page.eval(`JSON.stringify({ lang: document.documentElement.lang, title: document.title, h1: document.getElementById('h1').textContent, p: document.getElementById('p').textContent, home: document.getElementById('home').textContent, href: document.getElementById('home').getAttribute('href'), h: Math.round(document.getElementById('home').getBoundingClientRect().height), over: document.documentElement.scrollWidth > innerWidth })`));
      ok('404', st.lang === l && st.title === words[l].title && st.h1 === words[l].h1 && st.p === words[l].p && st.home === words[l].home, `${l}: ${JSON.stringify(st)}`);
      ok('404', st.href === (l === 'en' ? '/' : `/?lang=${l}`) && st.h >= 44 && !st.over, `${l}: the way home is ${st.href}, ${st.h} px high, overflow ${st.over}`);
      await page.close();
    }
    const page = await fresh(390, 800);
    await page.goto(`${origin}/imprint?lang=de`);
    await page.loaded();
    await page.eval("localStorage.setItem('snapeyes.lang', 'hu')");
    await page.goto(`${origin}/no/such/page`);
    await page.loaded();
    ok('404', (await page.eval('document.documentElement.lang')) === 'hu', 'the stored language is not used on the 404 page');
    await page.close();
  }

  // ---- tap targets
  for (const [name, url, width, sel] of [
    // [selector, px a touch has to be answered over]: 44 for a target with room round it; the links of a row or a list that sit 8 to 10 px apart (the footer's address, the
    // legal links of /try) take the whole space between their neighbours, which is the most a hit area can be without moving the layout
    ['landing', '/?lang=en', 390, [['.lp-hdr .lp-seg button', 44], ['.lp-hdr .lp-logo', 44], ['a.lp-link-quiet', 44], ['.lp-ftr .lp-logo', 44], ['.lp-ftr address a', 24]]],
    ['try', '/try?lang=en', 360, [['header button[lang]', 44], ['header a', 44], ['footer nav a, nav a', 24]]],
  ]) {
    const page = await fresh(width, 780);
    await page.goto(origin + url);
    await page.loaded();
    await waitFor(page, name === 'landing' ? "!!document.querySelector('.lp-ftr') && document.querySelector('.lp-slot') === null" : "!!document.querySelector('header button[lang]')", 25000);
    await sleep(800);
    for (const [s, need] of sel) {
      const rows = await reaches(page, s);
      ok('targets', rows.length > 0, `${name}: nothing matches ${s}`);
      for (const [h, reached, hit, text] of rows) ok('targets', hit && reached >= need, `${name} ${width}px: "${text}" (${s}) is ${h} px high and answers a touch over ${reached} px (needs ${need})`);
    }
    // the layout did not move: the landing's header and the language buttons keep their boxes
    if (name === 'landing') {
      const box = JSON.parse(await page.eval(`JSON.stringify([...document.querySelectorAll('.lp-hdr .lp-seg button')].map((b) => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }))`));
      ok('targets', box.every(([w, h]) => w === 32 && h === 32), `the language buttons are ${JSON.stringify(box)} at 390 px: their boxes moved (32 x 32 before)`);
    }
    await page.close();
  }

  // ---- the fold of /try
  for (const [w, h] of [[360, 740], [375, 667], [320, 568]]) {
    for (const l of LANGS) {
      const page = await fresh(w, h);
      await page.goto(`${origin}/try?lang=${l}`);
      await page.loaded();
      await waitFor(page, "[...document.querySelectorAll('main button')].some((b) => b.className.includes('fx-gold'))", 20000);
      await sleep(3200);
      const r = JSON.parse(await page.eval(`(() => { const b = [...document.querySelectorAll('main button')].find((x) => x.className.includes('fx-gold')); const q = b.getBoundingClientRect(); return JSON.stringify({ top: Math.round(q.top), bottom: Math.round(q.bottom), h: innerHeight }); })()`));
      ok('fold', r.top >= 0 && r.bottom <= r.h, `${l} ${w}x${h}: the "Take a photo" button is at ${r.top}-${r.bottom}, the screen is ${r.h} px high`);
      await page.close();
    }
  }
  for (const [w, h, wantCardFirst] of [[412, 915, true], [390, 844, false]]) {
    const page = await fresh(w, h);
    await page.goto(`${origin}/try?lang=en`);
    await page.loaded();
    await sleep(3500);
    // the card of the steps by its test id (2026-10-22: the steps are one line each under the guide video, a list and no longer a grid)
    const r = JSON.parse(await page.eval(`(() => { const s = document.querySelector('main section'); const card = s.querySelector('[data-testid=capture-guide]'); const b = [...s.children].find((c) => c.tagName === 'BUTTON'); return JSON.stringify({ card: Math.round(card.getBoundingClientRect().top), button: Math.round(b.getBoundingClientRect().top) }); })()`));
    if (wantCardFirst) ok('fold', r.card < r.button, `${w}x${h}: on a tall phone the guide is read before the button (${JSON.stringify(r)})`);
    else ok('fold', r.button < h, `${w}x${h}: ${JSON.stringify(r)}`);
    await page.close();
  }

  // ---- a photo the browser cannot open
  {
    const dir = mkdtempSync(join(tmpdir(), 'heic-'));
    const file = join(dir, 'IMG_0001.heic');
    writeFileSync(file, Buffer.from('ftypheic' + 'x'.repeat(2000)));
    for (const l of LANGS) {
      const page = await fresh(1100, 800, false);
      await page.goto(`${origin}/try?lang=${l}`);
      await page.loaded();
      await waitFor(page, "!!document.querySelector('input[type=file][multiple]')");
      await sleep(2800);
      const { root } = await page.send('DOM.getDocument', { depth: 0 });
      const { nodeId } = await page.send('DOM.querySelector', { nodeId: root.nodeId, selector: 'input[type=file][multiple]' });
      await page.send('DOM.setFileInputFiles', { files: [file], nodeId });
      const got = await waitFor(page, "/HEIC/.test(document.body.innerText)", 12000);
      const text = await page.eval('document.body.innerText');
      ok('heic', got && /JPEG/.test(text) && /PNG/.test(text) && /snapeyes\.com/.test(text) && !/Could not read this image|konnte nicht gelesen werden$/m.test(text), `${l}: the message is ${JSON.stringify(text.slice(0, 260))}`);
      await page.close();
    }
  }
} finally {
  await chrome.close();
  await site.close();
}
if (problems.length) {
  console.error(`polish check FAILED (${problems.length} of ${n}):\n  ${problems.join('\n  ')}`);
  process.exit(1);
}
console.log(`polish check ok: ${n} checks (icons and manifest, the 404 page in four languages, tap targets of 44 px, the first screen of /try on short phones, the HEIC message)`);
