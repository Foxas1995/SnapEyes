// The polish of the QA of 2026-10-20, as a check: the icons and the manifest, the branded 404 page, tap targets of 44 px, the "Take a photo" button on a short phone and
// the message for a photo the browser cannot open (HEIC).
//   npm run build && node scripts/check_polish.mjs [--dist dist]        real Chrome on the built page (the stand-in API of scripts/lib/flowstub.mjs)
//   icons     the icon is the iris of the owner's logo (2026-10-22: no favicon.svg; favicon-16/32/48.png), favicon.ico holds 16, 32 and 48 px, the touch icon is 180 px, the app icons 192 and 512, the web
//             manifest names the site's colours, and every page of the build links all of them (and every linked file is in the build)
//   404       an unknown address is answered 404 with dist/404.html: the site's look, the words in the visitor's language (?lang=, then the stored choice) from
//             src/notfound/notfound.json, a way home that keeps the language and is 44 px high
//   targets   the language buttons, the logo, the quiet link and the footer's links of the landing (390 px) and of /try (360 px) answer a touch 22 px above and below their
//             centre (their hit area is 44 px high; elementFromPoint says what a finger would hit), without the layout moving
//   fold      on a phone (360 x 740, 390 x 844, 412 x 915, 375 x 667, 320 x 568) the gold camera button is on the first screen of /try in every language, on 360 x 740,
//             390 x 844, 412 x 915 and 390 x 660 (an in-app browser) the quiet row (upload, sample eye) too and the steps after it (2026-11-26)
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
const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'];
const problems = [];
let n = 0;
const fail = (c, m) => { problems.push(`${c}: ${m}`); console.log(`  FAIL ${c}: ${m}`); };
const ok = (c, cond, m) => { n++; if (!cond) fail(c, m); return !!cond; };
const png = (f) => { if (!existsSync(f)) return null; const b = readFileSync(f); return b.readUInt32BE(0) === 0x89504e47 ? [b.readUInt32BE(16), b.readUInt32BE(20)] : null; };

// ---------------------------------------------------------------------------------------------------- icons (files only)
{
  // since 2026-10-22 the icon is the iris of the owner's logo (scripts/make_brand.py): a picture, so no SVG; favicon-16/32/48.png beside the ICO
  ok('icons', !existsSync(join(dist, 'favicon.svg')), 'favicon.svg is back: the icon is the iris of the logo (favicon.ico and the PNGs)');
  for (const px of [16, 32, 48]) ok('icons', (png(join(dist, `favicon-${px}.png`)) ?? []).join('x') === `${px}x${px}`, `favicon-${px}.png is ${png(join(dist, `favicon-${px}.png`))}, expected ${px}x${px}`);
  const ico = existsSync(join(dist, 'favicon.ico')) ? readFileSync(join(dist, 'favicon.ico')) : null;
  const sizes = ico ? Array.from({ length: ico.readUInt16LE(4) }, (_, i) => ico[6 + 16 * i] || 256) : [];
  ok('icons', !!ico && ico.readUInt16LE(2) === 1 && sizes.join() === '16,32,48', `favicon.ico ${ico ? `holds ${sizes} px` : 'is missing'}, expected 16,32,48`);
  for (const [f, px] of [['apple-touch-icon.png', 180], ['icon-192.png', 192], ['icon-512.png', 512]]) ok('icons', (png(join(dist, f)) ?? []).join('x') === `${px}x${px}`, `${f} is ${png(join(dist, f))}, expected ${px}x${px}`);
  const man = existsSync(join(dist, 'manifest.webmanifest')) ? JSON.parse(readFileSync(join(dist, 'manifest.webmanifest'), 'utf8')) : { icons: [] };
  ok('icons', man.name && man.short_name && man.start_url === '/' && man.theme_color === '#07090e' && man.background_color === '#07090e' && man.icons.every((i) => existsSync(join(dist, i.src.slice(1)))), JSON.stringify(man).slice(0, 200));
  for (const page of ['index.html', 'try.html', 'order.html', 'admin.html', 'privacy.html', 'terms.html', 'withdrawal.html', 'imprint.html', 'lp/en.html', 'lp/de.html', 'lp/lt.html', 'lp/hu.html', 'lp/hr.html', 'lp/fi.html', 'lp/et.html', 'lp/lv.html', '404.html'].filter((p) => existsSync(join(dist, p)))) {
    const h = readFileSync(join(dist, page), 'utf8');
    const has = ['href="/favicon.ico"', 'href="/favicon-32.png"', 'rel="apple-touch-icon" href="/apple-touch-icon.png"', 'rel="manifest" href="/manifest.webmanifest"'].filter((t) => !h.includes(t));
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
    // the language switch is a menu since the eight languages of 2026-11-13 (src/landing/Header.tsx, src/shared/LangMenu.tsx): its pill is measured closed, its
    // list of languages once it is open (below)
    ['landing', '/?lang=en', 390, [['.lp-hdr .lp-lang summary', 44], ['.lp-hdr .lp-logo', 44], ['a.lp-link-quiet', 44], ['.lp-ftr .lp-logo', 44], ['.lp-ftr address a', 24]]],
    // (2026-11-25, the owner's decision: /try's footer of legal links shows only under the result and the photo check, so the capture screen measured here has none)
    ['try', '/try?lang=en', 360, [['header summary', 44], ['header a', 44]]],
  ]) {
    const page = await fresh(width, 780);
    await page.goto(origin + url);
    await page.loaded();
    const [menu, items] = [name === 'landing' ? '#langMenu' : 'header details', name === 'landing' ? '#langSeg button[lang]' : 'header button[lang]'];
    await waitFor(page, name === 'landing' ? "!!document.querySelector('.lp-ftr') && document.querySelector('.lp-slot') === null" : "!!document.querySelector('header button[lang]')", 25000);
    await sleep(800);
    for (const [s, need] of sel) {
      const rows = await reaches(page, s);
      ok('targets', rows.length > 0, `${name}: nothing matches ${s}`);
      for (const [h, reached, hit, text] of rows) ok('targets', hit && reached >= need, `${name} ${width}px: "${text}" (${s}) is ${h} px high and answers a touch over ${reached} px (needs ${need})`);
    }
    // the layout did not move: the pill of the language menu keeps its box (36 px high, its hit area 44), and the menu is closed until it is pressed
    // (the landing's pill is its <summary>, with a taller hit area drawn round it; on /try the <summary> is the 44 px hit area and the pill is the span inside it)
    const pill = JSON.parse(await page.eval(`JSON.stringify((() => { const d = document.querySelector(${JSON.stringify(menu)}); const r = d.querySelector(${JSON.stringify(name === 'landing' ? 'summary' : 'summary > span')}).getBoundingClientRect(); return { h: Math.round(r.height), w: Math.round(r.width), open: d.open, n: d.querySelectorAll('button[lang]').length }; })())`));
    ok('targets', pill.h === 36 && pill.w >= 44 && pill.w <= 64 && !pill.open && pill.n === LANGS.length, `${name}: the language menu's pill is ${JSON.stringify(pill)} at ${width} px (36 px high, 44 to 64 wide, closed, ${LANGS.length} languages)`);
    // opened: every language is a row of 44 px that answers a touch, inside the screen
    await page.eval(`document.querySelector(${JSON.stringify(menu)}).open = true`);
    await sleep(300);
    const rows = await reaches(page, items);
    ok('targets', rows.length === LANGS.length, `${name}: the open language menu shows ${rows.length} languages, not ${LANGS.length}`);
    for (const [h, reached, hit, text] of rows) ok('targets', hit && reached >= 44, `${name} ${width}px: "${text}" of the open language menu is ${h} px high and answers a touch over ${reached} px (needs 44)`);
    const inside = JSON.parse(await page.eval(`JSON.stringify((() => { const r = document.querySelector(${JSON.stringify(items)}).parentElement.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right), innerWidth, document.documentElement.scrollWidth]; })())`));
    ok('targets', inside[0] >= 0 && inside[1] <= inside[2] && inside[3] <= inside[2], `${name}: the open language menu runs off the screen (${JSON.stringify(inside)})`);
    await page.close();
  }

  // ---- the fold of /try (2026-11-26: ads send strangers straight to /try; the gold button is the page's camera again, the quiet row under it uploads a photo or
  // tries the sample eye). On every phone the gold button is on the first screen in every language; on 360 x 740, 390 x 844 and 412 x 915 the quiet row too,
  // and the four steps come after the buttons; 390 x 660 is what an in-app browser (Facebook, Instagram) leaves visible of a 390 x 844 phone, the quiet row too
  for (const [w, h, row] of [[360, 740, true], [390, 844, true], [412, 915, true], [390, 660, true], [375, 667, false], [320, 568, false]]) {
    for (const l of LANGS) {
      const page = await fresh(w, h);
      await page.goto(`${origin}/try?lang=${l}`);
      await page.loaded();
      await waitFor(page, "[...document.querySelectorAll('main button')].some((b) => b.className.includes('fx-gold'))", 20000);
      await sleep(3200);
      const r = JSON.parse(await page.eval(`(() => { const s = document.querySelector('main section'); const box = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.top), Math.round(q.bottom)]; }; const b = [...s.querySelectorAll('button')].find((x) => x.className.includes('fx-gold')); return JSON.stringify({ gold: box(b), camera: b.dataset.testid, row: [...s.querySelectorAll('.grid button')].map(box), guide: box(s.querySelector('[data-testid=capture-guide]')), h: innerHeight }); })()`));
      ok('fold', r.camera === 'camera-direct' && r.gold[0] >= 0 && r.gold[1] <= r.h, `${l} ${w}x${h}: the gold camera button (${r.camera}) is at ${r.gold.join('-')}, the screen is ${r.h} px high`);
      if (row) ok('fold', r.row.length >= 1 && r.row.every(([t, b]) => t >= 0 && b <= r.h) && r.guide[0] > Math.max(...r.row.map(([, b]) => b)), `${l} ${w}x${h}: the quiet row ${JSON.stringify(r.row)} on the first screen of ${r.h} px and the steps after it (${r.guide.join('-')})`);
      await page.close();
    }
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
console.log(`polish check ok: ${n} checks (icons and manifest, the 404 page in ${LANGS.length} languages, tap targets of 44 px, the first screen of /try on short phones, the HEIC message)`);
