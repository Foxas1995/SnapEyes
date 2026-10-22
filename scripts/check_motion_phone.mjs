// The checks of the scroll linked scenes made for phones (the owner's request of 2026-10-17; src/motion/phone.ts, src/landing/RevealScene.tsx with `phone`, WallStage.tsx,
// SizeGuide.tsx, ClosingScene.tsx and the phone blocks at the end of css/reveal.css, wall.css, sizes.css, final.css), in real Chrome, against a build (dist/) served the way
// Vercel serves it, with a stub of the two API calls the page makes. Not part of `vite build`; run it after a build:
//   npm run build && npm run check:motion:phone
//   node scripts/check_motion_phone.mjs [--dist dist] [--only absent,reveal,fit,wall,size,how,final,failsafe,cls,identity]
//   --mutate-css "Chunk::from@@to" and --mutate-js "Chunk::from@@to" change the stylesheet or the code of one lazy chunk (Reveal, Wall, SizeGuide, ClosingScene, phone) on its way to the
//   browser: a deliberate defect, to see that a check really fails (the mutation proof of the work is in the commit message).
// Exit code 1 when any check fails. Every phone value is read at rest (the engine's smoothing has come to an end) at progress values written out here from the design, on
// purpose: the check is of the design, not of the code.
//
//   absent    the scenes exist only where they are meant to: not at 1280 px, not at 768 px (the desktop scene is there instead), not under reduced motion at 390 px and 375 px (no
//             html.mo, no mark, no value written, nothing pinned, nothing moved or clipped)
//   reveal    390 x 844: the phone's scene is a pinned wrapper (the stage holds still, one screen of scrolling long); the cut, the aperture, the line, the ring, the chips and the steps
//             follow the table of the Reveal at p = 0 .25 .5 .75 1, and monotonically both ways; at p = 0, .56 and 1 the frame is the photo, the iris and the artwork alone, pixel for
//             pixel; no layer is filtered, tilted, scaled or faded and the frame keeps its size; the labels never move; the three steps are buttons that scroll to their state; the
//             artwork layer is asked for only when the scene is near; the slider is still under the scene
//   fit       en de lt hu at 390 x 844, 375 x 667, 360 x 740, 412 x 915, 320 x 568 and 280 x 653 (a folded phone): the stage sits between the header and the sticky button bar, nothing wider than its box, no
//             sideways scroll, all three steps seen
//   wall      the stage plate opens like a mat and settles while it arrives (inset 7 to 0 percent, scale 1.03 to exactly 1, never more, never a move), monotonic, with the frame, its
//             ring and its label never clipped; the light on the acrylic print follows the scroll (10 percent white at most, screen blended) and there is no single sweep
//   size      the drawing is drawn by the scroll: every outline's dash offset falls from 1 to 0 in its turn, the squares and their labels fade in after, monotonic, whole from 90 percent on,
//             and the clock's animations do not run under it
//   how       the line through the numerals of the swipe rail is drawn by the scroll: each step's hairline scales from 0 to 1 in its turn (18 percent after the one before), monotonic, whole by
//             the end of the crossing, and the steps, their pictures and the rail's own scroll never move
//   final     the closing picture opens with the scroll (inset 7 to 0 percent, corners 28 to 0 px, scale 1.03 to 1), monotonic, whole at the end; the label and the button are
//             where they were (the sentence about the file under the button went in the lean pass of 2026-10-22)
//   failsafe  a dead IntersectionObserver (an in-app browser): html.mo-fail lifts every phone scene at 3.5 s: nothing pinned, clipped, scaled or undrawn
//   cls       no layout shift over a slow scroll of the whole page at 390 px, and none at 1280 px
//   identity  the artwork rectangles of the plate, the closing picture and the drawing are the same with the motion off and after the scenes have played (charter AC-5): the same visual
//             state, and where both runs put them at the same sub-pixel position the same pixels with zero tolerance
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const only = opt('--only') ? new Set(opt('--only').split(',')) : null;
const wants = (name) => !only || only.has(name);
const LANGS = ['en', 'de', 'lt', 'hu'];

const problems = [];
const fail = (check, msg) => { problems.push(`${check}: ${msg}`); console.log(`  FAIL ${check}: ${msg}`); };
const pass = (check, msg) => console.log(`  ok   ${check}: ${msg}`);
const expect = (check, cond, msg) => { if (!cond) fail(check, msg); return !!cond; };
const note = (msg) => console.log(`  note ${msg}`);
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const clean = (check) => !problems.some((x) => x.startsWith(check));

// a deliberate defect: the text of one lazy chunk's stylesheet or code, changed on its way to the browser ("Chunk::from@@to")
const mutation = (kind) => { const spec = opt(kind === 'css' ? '--mutate-css' : '--mutate-js'); if (!spec) return null; const i = spec.indexOf('::'), chunk = spec.slice(0, i), change = spec.slice(i + 2), j = change.indexOf('@@'); return { chunk, from: change.slice(0, j), to: change.slice(j + 2) }; };
const mutations = { css: mutation('css'), js: mutation('js') };
let mutated = 0;   // files that a deliberate defect was put into
const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
  if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { json({ ok: true, open: false, suggest: null }); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404); res.end('{}'); return true; }
  const m = /^\/assets\/([A-Za-z]+)-[^/]+\.(css|js)$/.exec(url.pathname);
  const mu = m && mutations[m[2]];
  if (mu && m[1] === mu.chunk) {
    const text = readFileSync(join(dist, url.pathname), 'utf8');
    if (!text.includes(mu.from)) return false;   // another file of the same name (the entry of /try, say): left as it is
    mutated++;
    res.writeHead(200, { 'content-type': m[2] === 'css' ? 'text/css' : 'text/javascript', 'cache-control': 'no-store' });
    res.end(text.split(mu.from).join(mu.to));
    return true;
  }
  return false;
};
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();

// ---------------------------------------------------------------------------------------------------- helpers
async function mounted(page) {
  for (let i = 0; i < 200; i++) {
    if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) return;
    await sleep(100);
  }
}
/** A fresh visit (nothing remembered), the page open, every lazy section mounted, nothing scrolled to yet. */
async function open({ lang = 'en', width = 390, height = 844, dpr, pre, settle = true, ...more } = {}) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: dpr ?? (width < 800 ? 2 : 1), ...more });
  page.errors = [];
  page.on((d) => { if (d.method === 'Runtime.exceptionThrown') page.errors.push(String(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text).slice(0, 240)); });
  await page.send('Page.bringToFront');
  if (pre) await page.send('Page.addScriptToEvaluateOnNewDocument', { source: pre });
  await page.goto(`${origin}/?lang=${lang}`);
  await page.loaded();
  if (settle) { await mounted(page); await sleep(500); }
  return page;
}
const top = (page, sel) => page.eval(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); return e ? e.getBoundingClientRect().top + scrollY : null; })()`);
const scrollY = (page) => page.eval('scrollY');
/** Scroll by the finger: instant steps of `step` px, `pause` ms apart, from where the page is to `to` (so that every observer on the way sees the screen pass). */
async function walk(page, to, step = 120, pause = 20) {
  let y = await scrollY(page);
  const dir = to >= y ? 1 : -1;
  while (dir * (to - y) > 0) {
    y += dir * Math.min(step, Math.abs(to - y));
    await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`);
    await sleep(pause);
  }
}
/** Walk to y and wait until `sel`'s inline style (the scene's own values) stops changing: the engine's smoothing is over. */
async function rest(page, y, sel, pause = 60) {
  await walk(page, y);
  await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`);
  let last = '';
  for (let i = 0; i < 40; i++) {
    await sleep(pause + 40);
    const now = await page.eval(`(document.querySelector(${JSON.stringify(sel)}) || {}).getAttribute ? document.querySelector(${JSON.stringify(sel)}).getAttribute('style') : ''`);
    if (now === last && i > 2) break;
    last = now;
  }
  await sleep(120);
}
/** Scroll until `sel`'s top is `want` px from the top of the screen. The chapters below the first screen are skipped until they are near (content-visibility) and change height when
 *  they are drawn, so a position measured once is only a first guess: read the element again and correct, until it is where it should be (or give up after five tries). */
async function place(page, sel, want, restSel = sel) {
  for (let i = 0; i < 5; i++) {
    const t = await page.eval(`document.querySelector(${JSON.stringify(sel)}).getBoundingClientRect().top`);
    if (Math.abs(t - want) <= 1) break;
    await page.eval(`window.scrollTo({ top: ${Math.round((await scrollY(page)) + t - want)}, behavior: 'instant' })`);
    await sleep(250);
  }
  await rest(page, await scrollY(page), restSel);
}
/** Wait until nothing on the page animates or transitions any more (the clock's entrances are over), for 12 s at most. */
async function quiet(page, max = 12000) {
  const t0 = Date.now();
  while (Date.now() - t0 < max) {
    const n = await page.eval("document.getAnimations().filter((a) => a.playState === 'running').length");
    if (n === 0) { await sleep(300); return; }
    await sleep(250);
  }
}
/** How many pixels differ (any channel, and by how much) inside the rectangle [x, y, w, h] of two PNGs of the same size. */
async function pngDiff(a, b, rect) {
  const page = await chrome.page({ width: 400, height: 300 });
  const r = JSON.parse(await page.eval(`(async () => {
    const load = (b64) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'data:image/png;base64,' + b64; });
    const [x, y] = await Promise.all([load(${JSON.stringify(a.toString('base64'))}), load(${JSON.stringify(b.toString('base64'))})]);
    if (x.width !== y.width || x.height !== y.height) return JSON.stringify({ size: [x.width, x.height, y.width, y.height] });
    const data = (im) => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0); return g.getImageData(0, 0, im.width, im.height).data; };
    const p = data(x), q = data(y), R = ${JSON.stringify(rect)}; let n = 0, max = 0;
    for (let i = 0; i < p.length; i += 4) { const k = i / 4, px = k % x.width, py = Math.floor(k / x.width); if (px < R[0] || py < R[1] || px >= R[0] + R[2] || py >= R[1] + R[3]) continue;
      if (p[i] !== q[i] || p[i + 1] !== q[i + 1] || p[i + 2] !== q[i + 2]) { n++; max = Math.max(max, Math.abs(p[i] - q[i]), Math.abs(p[i + 1] - q[i + 1]), Math.abs(p[i + 2] - q[i + 2])); } }
    return JSON.stringify({ n, max });
  })()`));
  await page.close();
  return r;
}
const shot = async (page) => Buffer.from((await page.send('Page.captureScreenshot', { format: 'png' })).data, 'base64');
const style = (page, id, css) => page.eval(`(() => { let s = document.getElementById(${JSON.stringify(id)}); if (!s) { s = document.createElement('style'); s.id = ${JSON.stringify(id)}; document.head.append(s); } s.textContent = ${JSON.stringify(css)}; })()`);
/** The page's own chrome lies over the frame at times (header, sticky button bar, top notice): out of the picture while pixels are compared. */
const HIDE_CHROME = '.lp-hdr, .lp-topbar, .lp-sticky, .lp-skip, #sticky, #hdr { visibility: hidden !important; }';
const ramp = (p, a, b) => Math.min(1, Math.max(0, (p - a) / (b - a)));
const monotone = (xs, dir, tol) => xs.every((v, i) => i === 0 || dir * (v - xs[i - 1]) >= -tol);

// ---------------------------------------------------------------------------------------------------- absent
// every mark, value and rule of the phone scenes, looked for on a page where it must not be
const TRACES = `JSON.stringify((() => {
  const out = [];
  const marks = document.querySelectorAll('[data-scrub]'); if (marks.length) out.push(marks.length + ' elements carry data-scrub');
  for (const e of document.querySelectorAll('[style*="--ps"], [style*="--dp"], [style*="--op"]')) out.push('a phone value is written on ' + e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0]);
  if (document.querySelector('.lp-rvp, .lp-rvp-stage')) out.push('the phone scene of the Reveal is in the page');
  return out;
})())`;
async function checkAbsent() {
  console.log('absent');
  const cases = [
    ['1280 x 800', { width: 1280, height: 800 }, { desktopScene: true }],
    ['768 x 1024', { width: 768, height: 1024 }, { desktopScene: true }],
    ['390 reduced motion', { width: 390, height: 844, reduceMotion: true }, {}],
    ['375 reduced motion', { width: 375, height: 812, reduceMotion: true }, {}],
    ['1280 reduced motion', { width: 1280, height: 800, reduceMotion: true }, {}],
  ];
  for (const [tag, o, want] of cases) {
    const page = await open(o);
    // the whole page, by the finger: a scene that is going to start has started by the end of it
    const H = await page.eval('document.documentElement.scrollHeight - innerHeight');
    await walk(page, H, Math.round(o.height * 0.5), 140);
    await quiet(page);   // the clock's entrances end (the closing settle is 2 s, the drawing 2.3 s)
    const traces = JSON.parse(await page.eval(TRACES));
    expect('absent', traces.length === 0, `${tag}: ${traces.join('; ')}`);
    const r = JSON.parse(await page.eval(`JSON.stringify({
      mo: document.documentElement.classList.contains('mo'), fail: document.documentElement.classList.contains('mo-fail'),
      sticky: [...document.querySelectorAll('#reveal *')].filter((e) => getComputedStyle(e).position === 'sticky').map((e) => e.className),
      scene: !!document.querySelector('.lp-rv-scene'),
      plate: [...document.querySelectorAll('#stage img')].map((i) => { const c = getComputedStyle(i); return c.scale + ' ' + c.clipPath; }),
      draw: [...document.querySelectorAll('#ruler .lp-dr')].map((e) => getComputedStyle(e).strokeDashoffset),
      band: (() => { const b = document.querySelector('.lp-final .lp-bg'), c = getComputedStyle(b), i = getComputedStyle(b.querySelector('img')); return c.clipPath + ' ' + i.scale; })(),
      hair: [...document.querySelectorAll('#steps .lp-num')].map((n) => getComputedStyle(n, '::after').scale),
      anims: document.getAnimations().filter((a) => a instanceof CSSAnimation && a.playState === 'running').map((a) => a.animationName),
    })`));
    if (o.reduceMotion) {
      expect('absent', !r.mo && !r.fail, `${tag}: html carries mo (${r.mo}) or mo-fail (${r.fail}) under reduced motion`);
      expect('absent', r.anims.length === 0, `${tag}: ${r.anims.length} animations are running under reduced motion: ${r.anims.join(', ')}`);
    }
    expect('absent', want.desktopScene === !!r.scene || o.reduceMotion || o.width < 768, `${tag}: the desktop scene is ${r.scene ? 'there' : 'missing'}`);
    if (want.desktopScene) expect('absent', r.sticky.length > 0, `${tag}: the pinned scene of the desktop has no sticky stage`);
    else expect('absent', r.sticky.length === 0, `${tag}: a sticky element in the Reveal: ${r.sticky.join(', ')}`);
    expect('absent', r.plate.every((v) => v === 'none none'), `${tag}: the plate images have a scale or a clip: ${r.plate.join(' | ')}`);
    // under reduced motion nothing animates, so what is left of a scene would show; on a desktop the clock's own entrances may still be ending (the marks and values above are the verdict there)
    if (o.reduceMotion) {
      expect('absent', r.draw.every((v) => v === '0px' || v === '0'), `${tag}: an outline of the drawing is not whole: ${r.draw.join(' ')}`);
      expect('absent', r.band === 'none none', `${tag}: the closing picture has a clip or a scale: ${r.band}`);
      expect('absent', r.hair.length === 3 && r.hair.every((v) => v === 'none'), `${tag}: a hairline of the steps is scaled: ${r.hair.join(' | ')}`);
    }
    expect('absent', page.errors.length === 0, `${tag}: script errors: ${page.errors.join(' | ')}`);
    await page.close();
  }
  if (clean('absent')) pass('absent', 'no scene, mark, value, pin, clip or scale of the phone at 1280 px, at 768 px, or under reduced motion at 1280, 390 and 375 px (the desktop has its own pinned scene)');
}

// ---------------------------------------------------------------------------------------------------- reveal
const rvGeo = async (page) => JSON.parse(await page.eval(`JSON.stringify((() => { const w = document.querySelector('.lp-rvp'), s = document.querySelector('.lp-rvp-stage'); if (!w || !s) return null;
  return { top: w.getBoundingClientRect().top + scrollY, h: w.offsetHeight, sh: s.offsetHeight, span: w.offsetHeight - s.offsetHeight, stick: parseFloat(getComputedStyle(s).top), pos: getComputedStyle(s).position, vh: innerHeight, after: getComputedStyle(w, '::after').height, afterContent: getComputedStyle(w, '::after').content }; })())`));
const rvState = async (page) => JSON.parse(await page.eval(`JSON.stringify((() => { const f = document.querySelector('.lp-rv-frame'), cs = getComputedStyle(f), s = document.querySelector('.lp-rvp-stage'), w = document.querySelector('.lp-rvp');
  return { pos: +cs.getPropertyValue('--rv-pos'), ap: +cs.getPropertyValue('--rv-ap'), line: +cs.getPropertyValue('--rv-line'), ring: +cs.getPropertyValue('--rv-ring'), c: f.dataset.c,
    stageTop: s.getBoundingClientRect().top, stageBottom: s.getBoundingClientRect().bottom, wrapTop: w.getBoundingClientRect().top, fw: f.getBoundingClientRect().width, fh: f.getBoundingClientRect().height,
    step: [...document.querySelectorAll('.lp-rvp .lp-rv-step')].findIndex((b) => b.getAttribute('aria-current') === 'step'),
    chips: [...f.querySelectorAll('.lp-rv-chip')].filter((c) => +getComputedStyle(c).opacity > 0.5).map((c) => c.dataset.k).join(' ') }; })())`));
const goP = async (page, g, p) => rest(page, Math.round(g.top - g.stick + g.span * p), '.lp-rv-frame');
/** The expected frame at p, written out here from the design (the table of the Reveal: 6 percent of the way the photo alone, the cut to 50, the iris, the aperture from 56 to 94). */
const wantRv = (p) => ({ pos: 100 * (1 - ramp(p, 0.06, 0.5)), ap: 72 * ramp(p, 0.56, 0.94), step: p >= 0.72 ? 2 : p >= 0.34 ? 1 : 0 });
async function checkReveal() {
  console.log('reveal');
  const page = await open({ width: 390, height: 844 });
  const art0 = await page.eval("document.querySelector('.lp-rv-art') ? document.querySelector('.lp-rv-art').hasAttribute('src') : 'none'");
  const g = await rvGeo(page);
  if (!expect('reveal', g, 'there is no phone scene at 390 x 844 (.lp-rvp)')) { await page.close(); return; }
  expect('reveal', art0 === false, `the artwork layer has its address (${art0}) before the scene is near: a phone has no use for 48 kB there`);
  expect('reveal', g.pos === 'sticky' && g.stick >= 75.5, `the stage is ${g.pos} at ${g.stick} px (want sticky, 76 px or lower: under the 64 px header)`);
  expect('reveal', near(g.span, 844, 2) && g.after === '844px', `the pin is ${g.span} px long and its spacer ${g.after} (want one screen, 100svh = 844 px)`);
  for (const p of [0, 0.25, 0.5, 0.75, 1]) {
    await goP(page, g, p);
    const s = await rvState(page), w = wantRv(p);
    expect('reveal', near(s.stageTop, g.stick, 0.6), `p ${p}: the stage is ${s.stageTop.toFixed(1)} px from the top (want ${g.stick}: it must hold still)`);
    expect('reveal', near(s.pos, w.pos, 0.6) && near(s.ap, w.ap, 0.6), `p ${p}: the cut is at ${s.pos.toFixed(1)} and the aperture ${s.ap.toFixed(1)} (want ${w.pos.toFixed(1)} and ${w.ap.toFixed(1)})`);
    expect('reveal', s.step === w.step, `p ${p}: step ${s.step + 1} is current (want ${w.step + 1})`);
    if (p === 0) expect('reveal', s.line === 0 && s.chips === 'photo', `p 0: the line has opacity ${s.line} and the chips are "${s.chips}" (want no line, "photo")`);
    if (p === 0.25) expect('reveal', s.line > 0.99 && s.chips === 'photo iris', `p .25: the line has opacity ${s.line} and the chips are "${s.chips}" (want the line shown and "photo iris")`);
    if (p === 0.5) expect('reveal', s.chips === 'iris', `p .5: the chips are "${s.chips}" (want "iris")`);
    if (p === 0.75) expect('reveal', s.chips === 'art' && s.ring > 0.9, `p .75: the chips are "${s.chips}", the ring ${s.ring} (want "art" and a visible ring)`);
    if (p === 1) expect('reveal', s.ring === 0 && s.line === 0 && s.chips === 'art', `p 1: the ring ${s.ring} and the line ${s.line} are still there, the chips "${s.chips}" (want none, "art")`);
  }
  // the artwork layer has its address now, and is loaded long before the aperture shows it
  const art1 = await page.eval("(() => { const a = document.querySelector('.lp-rv-art'); return a.hasAttribute('src') && a.complete && a.naturalWidth > 0; })()");
  expect('reveal', art1 === true, 'the artwork layer is not loaded in the middle of the scene');
  // both ways, in steps: the cut only goes left, the aperture only opens, the step only counts up (and back down on the way up)
  const track = async (ps) => { const out = []; for (const p of ps) { await goP(page, g, p); out.push(await rvState(page)); } return out; };
  const grid = Array.from({ length: 21 }, (_, i) => -0.05 + (1.1 * i) / 20);
  const down = await track(grid), up = await track([...grid].reverse());
  expect('reveal', monotone(down.map((s) => s.pos), -1, 0.6) && monotone(down.map((s) => s.ap), 1, 0.6) && monotone(down.map((s) => s.step), 1, 0), `going down the cut, the aperture or the step is not monotone: ${down.map((s) => `${s.pos.toFixed(0)}/${s.ap.toFixed(0)}/${s.step}`).join(' ')}`);
  expect('reveal', monotone(up.map((s) => s.pos), 1, 0.6) && monotone(up.map((s) => s.ap), -1, 0.6) && monotone(up.map((s) => s.step), -1, 0), `going up the cut, the aperture or the step is not monotone: ${up.map((s) => `${s.pos.toFixed(0)}/${s.ap.toFixed(0)}/${s.step}`).join(' ')}`);
  expect('reveal', new Set([...down, ...up].filter((s) => s.stageTop <= g.stick + 0.6).map((s) => `${Math.round(s.fw)}x${Math.round(s.fh)}`)).size === 1, 'the frame changed size during the scroll');
  // the Artwork Charter on every layer across the scroll: no filter, no blur, no tilt, no scale, no fade of a picture; the labels do not move
  const probe = `JSON.stringify((() => { const f = document.querySelector('.lp-rv-frame'), bad = [], label = [...f.querySelectorAll('.lp-rv-who, .lp-rv-chip')].map((e) => { const r = e.getBoundingClientRect(), c = getComputedStyle(f).getPropertyValue('--x'); return Math.round(r.left - f.getBoundingClientRect().left) + ',' + Math.round(r.top - f.getBoundingClientRect().top); }).join(' ');
    for (const el of [f, ...f.querySelectorAll('img, svg, .lp-rv-chip, .lp-rv-line, .lp-rv-who')]) { const c = getComputedStyle(el), n = el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className;
      if (c.filter !== 'none' || c.backdropFilter !== 'none') bad.push(n + ' filter ' + c.filter + ' ' + c.backdropFilter);
      if (c.transform !== 'none' || c.rotate !== 'none' || (c.scale !== 'none' && c.scale !== '1')) bad.push(n + ' transform ' + c.transform + ' ' + c.rotate + ' ' + c.scale);
      if (el.tagName === 'IMG' && (+c.opacity !== 1 || c.visibility !== 'visible' || c.display === 'none')) bad.push(n + ' opacity ' + c.opacity + ' ' + c.visibility); }
    const who = f.querySelector('.lp-rv-who'), wc = getComputedStyle(who);
    if (wc.visibility !== 'visible' || +wc.opacity !== 1 || !who.textContent.trim()) bad.push('the label of whose eye it is is not shown (' + wc.visibility + ', ' + wc.opacity + ')');
    // one caption line under the frame (how the photo was taken): the line with the photo's size in pixels went in the lean pass of 2026-10-22 (the owner: no pixel counts for a visitor)
    const cap = [...document.querySelectorAll('.lp-rvp .lp-rv-cap span')].map((e) => +getComputedStyle(e).opacity);
    if (cap.length !== 1 || cap.some((o) => o !== 1)) bad.push('a caption line is not shown');
    return { label, bad, who: who.textContent.trim() }; })())`;
  const labels = new Set(), bads = new Set(), whos = new Set();
  for (const p of [0, 0.1, 0.3, 0.5, 0.6, 0.8, 1]) { await goP(page, g, p); const r = JSON.parse(await page.eval(probe)); r.bad.forEach((b) => bads.add(b)); whos.add(r.who); labels.add(r.label.split(' ')[0]); }
  expect('reveal', bads.size === 0, `across the scroll: ${[...bads].join(' | ')}`);
  expect('reveal', whos.size === 1 && [...whos][0].length > 3, `the label of whose eye it is changed or is empty: ${[...whos].join(' | ')}`);
  expect('reveal', labels.size === 1, `the label of whose eye it is moved inside the frame: ${[...labels].join(' | ')}`);
  // the sticky button bar at the foot of the screen is left clear, and the heading and the sentence stay above the pin
  await goP(page, g, 0.5);
  const clear = JSON.parse(await page.eval(`JSON.stringify((() => { const b = document.getElementById('sticky').getBoundingClientRect(), s = document.querySelector('.lp-rvp-stage').getBoundingClientRect(), h = document.getElementById('hdr').getBoundingClientRect(); return { bar: Math.round(b.top), stage: Math.round(s.bottom), hdr: Math.round(h.bottom), stageTop: Math.round(s.top), shown: document.getElementById('sticky').classList.contains('lp-show') }; })())`));
  expect('reveal', clear.stage <= clear.bar && clear.stageTop >= clear.hdr, `the stage (${clear.stageTop} to ${clear.stage} px) is not between the header (${clear.hdr}) and the sticky bar (${clear.bar})`);
  // the table of what comes from the photo and what the AI adds went into the FAQ's answer "How does it work?" in the lean pass of 2026-10-22: heading, scene, slider, strip
  const order = JSON.parse(await page.eval(`JSON.stringify((() => { const y = (s) => document.querySelector(s).getBoundingClientRect().top + scrollY; return { h2: y('#revealH'), scene: y('.lp-rvp'), slider: y('.lp-cmp'), strip: y('.lp-strip'), table: document.querySelectorAll('#reveal .lp-ai').length }; })())`));
  expect('reveal', order.h2 < order.scene && order.scene + g.h <= order.slider + 2 && order.slider < order.strip && order.table === 0, `the order of the section is not heading, scene, slider, strip: ${JSON.stringify(order)}`);
  expect('reveal', (await page.eval("document.querySelectorAll('#reveal .lp-cmp-range').length")) === 1, 'the slider (one native range) is not in the section');
  expect('reveal', page.errors.length === 0, `script errors: ${page.errors.join(' | ')}`);
  await page.close();

  // pixels: at rest the frame is the photo, the iris and the artwork alone (nothing lies over a resting state)
  const px = await open({ width: 390, height: 844, dpr: 1 });
  const g2 = await rvGeo(px);
  const rect = async () => JSON.parse(await px.eval(`JSON.stringify((() => { const b = document.querySelector('.lp-rv-frame').getBoundingClientRect(); return [Math.round(b.left + 24), Math.round(b.top + 24), Math.round(b.width - 48), Math.round(b.height - 48)]; })())`));
  for (const [p, layer] of [[0, 'photo'], [0.56, 'iris'], [1, 'art']]) {
    await style(px, 'px', '');
    await goP(px, g2, p);
    await style(px, 'px', `${HIDE_CHROME} .lp-rv-chip, .lp-rv-who { visibility: hidden !important; transition: none !important; }`);
    await sleep(300);
    const a = await shot(px);
    await style(px, 'px', `${HIDE_CHROME} .lp-rv-chip, .lp-rv-who { visibility: hidden !important; } .lp-rv-frame > :not(.lp-rv-${layer}) { visibility: hidden !important; } .lp-rv-${layer} { clip-path: none !important; }`);
    await sleep(300);
    const b = await shot(px);
    const d = await pngDiff(a, b, await rect());
    expect('reveal', d.n <= 600 && d.max <= 2, `p ${p}: the frame differs from the ${layer} alone in ${d.n} pixels (by up to ${d.max} levels${d.size ? ', sizes ' + d.size : ''}): something lies over a resting state`);
  }
  await px.close();

  // keyboard: the steps are buttons in the tab order; Enter scrolls to their state and aria-current follows
  const kb = await open({ width: 390, height: 844 });
  const g3 = await rvGeo(kb);
  const n = await kb.eval("document.querySelectorAll('.lp-rvp .lp-rv-step').length");
  const tabs = await kb.eval("[...document.querySelectorAll('.lp-rvp .lp-rv-step')].map((b) => b.tabIndex + b.tagName).join()");
  expect('reveal', n === 3 && tabs === '0BUTTON,0BUTTON,0BUTTON', `the step rows are ${n} elements (${tabs}); want three buttons in the tab order`);
  await goP(kb, g3, 0);
  const KEYS = { Enter: 13 };
  const key = async (k) => { await kb.send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code: k, windowsVirtualKeyCode: KEYS[k], text: '\r' }); await kb.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code: k, windowsVirtualKeyCode: KEYS[k] }); await sleep(250); };
  await kb.eval("document.querySelectorAll('.lp-rvp .lp-rv-step')[2].focus({ preventScroll: true })");
  await key('Enter'); await sleep(2400);
  let s = await rvState(kb);
  expect('reveal', s.step === 2 && s.ap > 70, `Enter on step 3: step ${s.step + 1} is current, the aperture ${s.ap.toFixed(1)} (want 3 and 72)`);
  await kb.eval("document.querySelectorAll('.lp-rvp .lp-rv-step')[1].focus({ preventScroll: true })");
  await key('Enter'); await sleep(2400);
  s = await rvState(kb);
  expect('reveal', s.step === 1 && s.pos < 1 && s.ap === 0, `Enter on step 2: step ${s.step + 1} is current, the cut ${s.pos.toFixed(1)}, the aperture ${s.ap.toFixed(1)} (want 2, 0, 0)`);
  await kb.eval("document.querySelectorAll('.lp-rvp .lp-rv-step')[0].focus({ preventScroll: true })");
  await key('Enter'); await sleep(2400);
  s = await rvState(kb);
  expect('reveal', s.step === 0 && near(s.pos, 100, 0.6), `Enter on step 1: step ${s.step + 1} is current, the cut ${s.pos.toFixed(1)} (want 1 and 100)`);
  await kb.close();
  if (clean('reveal')) pass('reveal', 'the phone scene is a pinned wrapper one screen long, the stage holds, the frame follows the table at p = 0 .25 .5 .75 1 and monotonically both ways, is the photo, the iris and the artwork alone at rest, labels never move, steps are buttons that scroll to their state, the artwork is asked for only when near, the slider is still under it');
}

// ---------------------------------------------------------------------------------------------------- fit
async function checkFit() {
  console.log('fit');
  for (const lang of LANGS) {
    for (const [w, h] of [[390, 844], [375, 667], [360, 740], [412, 915], [320, 568], [280, 653]]) {
      const page = await open({ lang, width: w, height: h });
      const g = await rvGeo(page);
      if (!expect('fit', g, `${lang} ${w} x ${h}: no phone scene`)) { await page.close(); continue; }
      for (const p of [0, 0.5, 1]) {
        await goP(page, g, p);
        const r = JSON.parse(await page.eval(`JSON.stringify((() => { const s = document.querySelector('.lp-rvp-stage').getBoundingClientRect(), bar = document.getElementById('sticky').getBoundingClientRect(), hdr = document.getElementById('hdr').getBoundingClientRect(), f = document.querySelector('.lp-rv-frame').getBoundingClientRect();
          const steps = [...document.querySelectorAll('.lp-rvp .lp-rv-step')].map((e) => e.getBoundingClientRect());
          return { stageTop: Math.round(s.top), stageBottom: Math.round(s.bottom), bar: Math.round(bar.top), hdr: Math.round(hdr.bottom), fw: Math.round(f.width), fl: Math.round(f.left), fr: Math.round(f.right), iw: innerWidth, sw: document.documentElement.scrollWidth,
            wide: [...document.querySelectorAll('.lp-rvp .lp-rv-step, .lp-rvp .lp-rv-step span, .lp-rvp .lp-rv-cap span')].filter((e) => e.scrollWidth > e.clientWidth + 1).map((e) => e.textContent.slice(0, 20)),
            stepsSeen: steps.length === 3 && steps.every((b) => b.top >= 0 && b.bottom <= innerHeight && b.width > 40 && b.height >= 40),
            stepsBelowBar: steps.some((b) => b.bottom > bar.top + 1) }; })())`));
        const tag = `${lang} ${w} x ${h} p ${p}`;
        expect('fit', r.stageBottom <= r.bar + 1 && r.stageTop >= r.hdr, `${tag}: the stage (${r.stageTop} to ${r.stageBottom} px) is not between the header (${r.hdr}) and the sticky bar (${r.bar})`);
        expect('fit', r.wide.length === 0, `${tag}: wider than its box: ${r.wide.join(' | ')}`);
        expect('fit', r.sw <= r.iw && r.fl >= 15 && r.iw - r.fr >= 15, `${tag}: the page scrolls sideways (${r.sw} of ${r.iw} px) or the frame leaves its gutters (${r.fl} to ${r.fr})`);
        expect('fit', r.stepsSeen && !r.stepsBelowBar, `${tag}: the three steps are not all seen above the bar`);
        expect('fit', r.fw >= Math.min(260, r.iw - 34), `${tag}: the frame is only ${r.fw} px wide`);
      }
      await page.close();
    }
  }
  if (clean('fit')) pass('fit', 'en de lt hu at 390 x 844, 375 x 667, 360 x 740, 412 x 915, 320 x 568 and 280 x 653: the stage sits between the header and the sticky bar, nothing is wider than its box, no sideways scroll, three steps seen');
}

// ---------------------------------------------------------------------------------------------------- wall
// the stage crosses the screen (traverse from the plate's top at the bottom edge to its bottom at the top edge: p = (vh - top) / (vh + h)); the plate settles over the first 45 percent
async function checkWall() {
  console.log('wall');
  const page = await open({ width: 390, height: 844 });
  const h = await page.eval("document.querySelector('.lp-stage').getBoundingClientRect().height"), vh = 844;
  const goto = (p) => place(page, '.lp-stage', vh - p * (vh + h));
  const PROBE = `JSON.stringify((() => { const f = document.querySelector('.lp-stage'), fr = f.getBoundingClientRect(), cs = getComputedStyle(f);
    const imgs = [...f.querySelectorAll('img')].map((i) => { const c = getComputedStyle(i), m = /^inset\\(([\\d.e+-]+)(%|px)(?: round ([\\d.e+-]+)px)?/.exec(c.clipPath); return { raw: c.clipPath + ' ' + c.scale, scale: c.scale === 'none' ? 1 : +c.scale, clip: c.clipPath === 'none' ? 0 : m ? +m[1] : -1, round: m && m[3] ? +m[3] : 0, tr: c.translate + '|' + c.transform + '|' + c.rotate, filter: c.filter }; });
    const chip = f.querySelector('.lp-vis-chip'), cc = getComputedStyle(chip), cr = chip.getBoundingClientRect(), g = document.getElementById('stGlint'), ga = getComputedStyle(g, '::after');
    return { ps: +f.style.getPropertyValue('--ps'), gx: parseFloat(f.style.getPropertyValue('--gx')), scrub: f.dataset.scrub !== undefined, run: f.hasAttribute('data-run'), imgs, ring: cs.boxShadow, rect: [fr.left, fr.top, fr.width, fr.height],
      chip: cc.visibility === 'visible' && +cc.opacity === 1 && cr.left >= fr.left && cr.top >= fr.top && cr.right <= fr.right && cr.bottom <= fr.bottom && !!chip.textContent.trim(),
      glint: { shine: g.hasAttribute('data-shine'), op: +ga.opacity, tr: parseFloat(ga.translate), bg: ga.backgroundImage, blend: ga.mixBlendMode, rect: g.getBoundingClientRect().toJSON(), swept: g.hasAttribute('data-sweep') },
      sweep: document.getAnimations().filter((a) => a instanceof CSSAnimation && a.animationName === 'lp-sweep').length }; })())`;
  const ps = [0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1];
  const rows = [];
  for (const p of ps) { await goto(p); rows.push([p, JSON.parse(await page.eval(PROBE))]); }
  const rings = new Set();
  for (const [p, r] of rows) {
    const s1 = Math.min(1, p / 0.45);
    expect('wall', near(r.ps, s1, 0.02) && r.scrub, `p ${p}: --ps is ${r.ps} (want ${s1.toFixed(3)}), marked ${r.scrub}`);
    expect('wall', r.run === (r.ps < 0.9995), `p ${p}: data-run is ${r.run} at --ps ${r.ps} (want it on while the plate is settling and off at the end)`);
    for (const im of r.imgs) {
      expect('wall', near(im.scale, 1 + 0.03 * (1 - s1), 0.0008) && im.scale <= 1.0301, `p ${p}: the plate's scale is ${im.scale} (want ${(1 + 0.03 * (1 - s1)).toFixed(4)}, never above 1.03)`);
      expect('wall', near(im.clip, 7 * (1 - s1), 0.12) && near(im.round, 22 * (1 - s1), 0.6), `p ${p}: the plate's clip is an inset of ${im.clip} percent with corners of ${im.round} px (want ${(7 * (1 - s1)).toFixed(2)} and ${(22 * (1 - s1)).toFixed(1)})`);
      expect('wall', im.tr === 'none|none|none' && im.filter === 'none', `p ${p}: the picture moved, turned or got a filter: ${im.tr} ${im.filter}`);
    }
    expect('wall', r.chip, `p ${p}: the label "AI visualisation" is clipped, faded or gone`);
    rings.add(r.ring);
  }
  expect('wall', rings.size === 1, `the frame's ring changed during the crossing: ${[...rings].join(' | ')}`);
  expect('wall', monotone(rows.map(([, r]) => r.ps), 1, 0.003) && monotone(rows.map(([, r]) => r.imgs[0].scale), -1, 0.0006) && monotone(rows.map(([, r]) => r.imgs[0].clip), -1, 0.1), 'going down, the settle is not monotone');
  const e = rows.at(-1)[1];
  expect('wall', e.imgs.every((im) => im.raw === 'none none'), `at the end the plate is not the static one (clip-path and scale should be none): ${JSON.stringify(e.imgs.map((im) => im.raw))}`);
  // both ways: back up the same values come back
  const back = [];
  for (const p of [...ps].reverse()) { await goto(p); back.push(JSON.parse(await page.eval(PROBE)).ps); }
  expect('wall', monotone(back, -1, 0.003), `going up, --ps is not monotone: ${back.join(' ')}`);
  // the light on a polished print: pick acrylic, wait for its picture, and the band follows the scroll (30 percent wide, 10 percent white at the most, screen blended, on the print face)
  await goto(0.3);
  await page.eval("document.getElementById('mat-acrylic').click()");
  await sleep(2600);
  const bands = [];
  for (const p of [0.05, 0.25, 0.5, 0.75, 0.95]) { await goto(p); bands.push([p, JSON.parse(await page.eval(PROBE))]); }
  for (const [p, r] of bands) {
    const gl = r.glint;
    expect('wall', gl.shine && gl.op === 1 && gl.blend === 'screen' && /rgba\(255, 255, 255, 0\.1\)/.test(gl.bg), `p ${p}: the band is not on the acrylic print (shine ${gl.shine}, opacity ${gl.op}, ${gl.blend}, ${gl.bg.slice(0, 90)})`);
    expect('wall', near(gl.tr, p * 80 - 40, 2.5), `p ${p}: the band is at ${gl.tr} percent (want ${(p * 80 - 40).toFixed(1)})`);
    const f = r.rect, q = gl.rect;
    expect('wall', q.left >= f[0] - 0.5 && q.right <= f[0] + f[2] + 0.5 && q.top >= f[1] - 0.5 && q.bottom <= f[1] + f[3] + 0.5, `p ${p}: the band's box is not inside the stage`);
  }
  expect('wall', monotone(bands.map(([, r]) => r.glint.tr), 1, 0.05) && bands[0][1].glint.tr < bands.at(-1)[1].glint.tr - 40, `the band does not travel with the scroll: ${bands.map(([, r]) => r.glint.tr.toFixed(1)).join(' ')}`);
  expect('wall', bands.every(([, r]) => r.sweep === 0 && !r.glint.swept), 'a single sweep is still running on a phone');
  expect('wall', page.errors.length === 0, `script errors: ${page.errors.join(' | ')}`);
  await page.close();
  if (clean('wall')) pass('wall', 'the plate opens like a mat and settles as it arrives (inset 7 to 0 percent, scale 1.03 to exactly 1, never a move), monotonic both ways, frame, ring and label never clipped; the light on the acrylic print follows the scroll and no single sweep runs');
}

// ---------------------------------------------------------------------------------------------------- size
// the drawing crosses the middle of the screen (traverse from its top at 90 percent to its bottom at 50 percent: p = (.9 vh - top) / (.4 vh + h))
async function checkSize() {
  console.log('size');
  const page = await open({ width: 390, height: 844 });
  const h = await page.eval("document.querySelector('.lp-ruler').getBoundingClientRect().height"), vh = 844;
  const goto = (p) => place(page, '.lp-ruler', 0.9 * vh - p * (0.4 * vh + h));
  const PROBE = `JSON.stringify((() => { const f = document.querySelector('.lp-ruler'), k = (e) => +(e.style.getPropertyValue('--k') || 0);
    return { dp: +f.style.getPropertyValue('--dp'), scrub: f.dataset.scrub !== undefined, run: f.hasAttribute('data-run'), inView: f.dataset.in !== undefined,
      dr: [...f.querySelectorAll('.lp-dr')].map((e) => [k(e), parseFloat(getComputedStyle(e).strokeDashoffset.replace('calc(', ''))]),
      sq: [...f.querySelectorAll('.lp-sqg')].map((e) => [k(e), +getComputedStyle(e).opacity]),
      lb: [...f.querySelectorAll('.lp-lbl')].filter((e) => getComputedStyle(e).display !== 'none').map((e) => [k(e), +getComputedStyle(e).opacity]),
      clock: document.getAnimations().filter((a) => a instanceof CSSAnimation && /^lp-(draw|sq-in)$/.test(a.animationName)).length }; })())`;
  const clamp01 = (x) => Math.min(1, Math.max(0, x));
  const ps = [0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.75, 0.9, 1];
  const rows = [];
  for (const p of ps) { await goto(p); rows.push([p, JSON.parse(await page.eval(PROBE))]); }
  for (const [p, r] of rows) {
    expect('size', near(r.dp, p, 0.02) && r.scrub && r.run === (r.dp < 0.9995), `p ${p}: --dp is ${r.dp} (want ${p}), marked ${r.scrub}, data-run ${r.run} (want it off at the end)`);
    expect('size', r.dr.length === 8 && r.dr.every(([k, o]) => near(o, 1 - clamp01((r.dp - k * 0.06) * 3.125), 0.02)), `p ${p}: an outline is not where the design puts it: ${r.dr.map(([k, o]) => `${k}:${o.toFixed(2)}`).join(' ')}`);
    expect('size', r.sq.length === 4 && r.sq.every(([k, o]) => near(o, clamp01((r.dp - 0.45 - k * 0.06) * 5), 0.03)), `p ${p}: a square is not where the design puts it: ${r.sq.map(([k, o]) => `${k}:${o.toFixed(2)}`).join(' ')}`);
    expect('size', r.lb.length >= 3 && r.lb.every(([k, o]) => near(o, clamp01((r.dp - 0.5 - k * 0.06) * 5), 0.03)), `p ${p}: a label is not where the design puts it: ${r.lb.map(([k, o]) => `${k}:${o.toFixed(2)}`).join(' ')}`);
    if (p > 0 && p < 1) expect('size', r.clock === 0, `p ${p}: ${r.clock} animations of the clock are running under the scroll`);
  }
  const first = rows[0][1], last = rows.at(-1)[1];
  expect('size', first.dr.every(([, o]) => o >= 0.97) && first.sq.every(([, o]) => o <= 0.03) && first.lb.every(([, o]) => o <= 0.03), `at the start the drawing is not blank: ${JSON.stringify(first)}`);
  expect('size', last.dr.every(([, o]) => o === 0) && last.sq.every(([, o]) => o === 1) && last.lb.every(([, o]) => o === 1), `at the end the drawing is not whole: ${JSON.stringify(last)}`);
  expect('size', rows.filter(([p]) => p >= 0.9).every(([, r]) => r.dr.every(([, o]) => o === 0) && r.sq.every(([, o]) => o === 1) && r.lb.every(([, o]) => o === 1)), 'the drawing is not whole by 90 percent of the crossing (it must be done well before the end, so that a stop anywhere near the end shows it whole)');
  const many = [], up = [];
  for (const p of Array.from({ length: 17 }, (_, i) => -0.05 + (1.1 * i) / 16)) { await goto(p); many.push(JSON.parse(await page.eval(PROBE))); }
  for (const p of Array.from({ length: 17 }, (_, i) => 1.05 - (1.1 * i) / 16)) { await goto(p); up.push(JSON.parse(await page.eval(PROBE))); }
  const sum = (r, key) => r[key].reduce((a, [, v]) => a + v, 0);
  expect('size', monotone(many.map((r) => sum(r, 'dr')), -1, 0.02) && monotone(many.map((r) => sum(r, 'sq')), 1, 0.02) && monotone(many.map((r) => sum(r, 'lb')), 1, 0.02), 'going down, the outlines, squares or labels are not monotone');
  expect('size', monotone(up.map((r) => sum(r, 'dr')), 1, 0.02) && monotone(up.map((r) => sum(r, 'sq')), -1, 0.02), 'going up, the outlines or squares are not monotone');
  expect('size', page.errors.length === 0, `script errors: ${page.errors.join(' | ')}`);
  // a pick still draws its gold outline (the clock of the chips is untouched)
  await goto(1);
  await page.eval("document.querySelector('#sizeChips [data-cm=\"30\"]').click()");
  await sleep(900);
  const gold = JSON.parse(await page.eval(`JSON.stringify([...document.querySelectorAll('.lp-sqg')].map((g) => [g.dataset.cm, getComputedStyle(g.querySelector('.lp-sq-on')).strokeDashoffset]))`));
  expect('size', gold.filter(([, o]) => o === '0px').length === 1 && gold.find(([c]) => c === '30')[1] === '0px', `a pick does not draw the gold outline of that size: ${JSON.stringify(gold)}`);
  await page.close();
  if (clean('size')) pass('size', 'the drawing is drawn by the scroll: each outline falls from 1 to 0 in its turn, then the squares and their labels fade in, monotonic both ways, blank at the start and whole at the end, no animation of the clock under it, a pick still draws its outline');
}

// ---------------------------------------------------------------------------------------------------- how
// the swipe rail crosses the screen (traverse from its top at 85 percent to its bottom at 50: p = (.85 vh - top) / (.35 vh + h))
async function checkHow() {
  console.log('how');
  const page = await open({ width: 390, height: 844 });
  const h = await page.eval("document.getElementById('steps').getBoundingClientRect().height"), vh = 844;
  const goto = (p) => place(page, '#steps', 0.85 * vh - p * (0.35 * vh + h), '#steps');
  const PROBE = `JSON.stringify((() => { const r = document.getElementById('steps'), lis = [...r.children];
    return { sp: +r.style.getPropertyValue('--sp'), scrub: r.dataset.scrub !== undefined, run: r.hasAttribute('data-run'), left: r.scrollLeft, hair: lis.map((li) => { const s = getComputedStyle(li.querySelector('.lp-num'), '::after').scale; return [+li.style.getPropertyValue('--i'), s === 'none' ? 1 : parseFloat(s)]; }),
      moved: lis.map((li) => { const c = getComputedStyle(li); return c.translate + '|' + c.transform + '|' + c.scale + '|' + c.opacity; }).join(' / '), box: lis.map((li) => Math.round(li.getBoundingClientRect().left - r.getBoundingClientRect().left)).join(',') }; })())`;
  const clamp01 = (x) => Math.min(1, Math.max(0, x));
  const ps = [0, 0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1];
  const rows = [];
  for (const p of ps) { await goto(p); rows.push([p, JSON.parse(await page.eval(PROBE))]); }
  for (const [p, r] of rows) {
    expect('how', near(r.sp, p, 0.02) && r.scrub && r.run === (r.sp < 0.9995), `p ${p}: --sp is ${r.sp} (want ${p}), marked ${r.scrub}, data-run ${r.run} (want it off at the end)`);
    expect('how', r.hair.length === 3 && r.hair.every(([i, v]) => near(v, clamp01((r.sp - i * 0.18) * 2.22), 0.03)), `p ${p}: a hairline is not where the design puts it: ${r.hair.map(([i, v]) => `${i}:${v.toFixed(2)}`).join(' ')}`);
    expect('how', r.left === 0 && r.moved === rows[0][1].moved && r.box === rows[0][1].box, `p ${p}: the rail scrolled or a step moved (scrollLeft ${r.left}, ${r.moved})`);
  }
  expect('how', rows[0][1].hair.every(([, v]) => v <= 0.03) && rows.filter(([p]) => p >= 0.85).every(([, r]) => r.hair.every(([, v]) => v === 1)), `the lines are not blank at the start and whole from 85 percent on: ${JSON.stringify(rows.map(([p, r]) => [p, r.hair.map(([, v]) => +v.toFixed(2))]))}`);
  const many = [], up = [];
  for (const p of Array.from({ length: 17 }, (_, i) => -0.05 + (1.1 * i) / 16)) { await goto(p); many.push(JSON.parse(await page.eval(PROBE))); }
  for (const p of Array.from({ length: 17 }, (_, i) => 1.05 - (1.1 * i) / 16)) { await goto(p); up.push(JSON.parse(await page.eval(PROBE))); }
  const sum = (r) => r.hair.reduce((a, [, v]) => a + v, 0);
  expect('how', monotone(many.map(sum), 1, 0.03) && monotone(up.map(sum), -1, 0.03), 'the lines are not monotone with the scroll, down or up');
  expect('how', page.errors.length === 0, `script errors: ${page.errors.join(' | ')}`);
  await page.close();
  if (clean('how')) pass('how', 'the line through the numerals is drawn by the scroll, one step after the other, monotonic both ways, blank at the start and whole from 85 percent on; the steps and the rail never move');
}

// ---------------------------------------------------------------------------------------------------- final
// the band crosses the screen (traverse from its top at 92 percent to its bottom at 108: p = (.92 vh - top) / (h - .16 vh))
async function checkFinal() {
  console.log('final');
  const page = await open({ width: 390, height: 844 });
  const h = await page.eval("document.querySelector('.lp-final').getBoundingClientRect().height"), vh = 844;
  const goto = (p) => place(page, '.lp-final', 0.92 * vh - p * (h - 0.16 * vh), '.lp-bg');
  const PROBE = `JSON.stringify((() => { const s = document.querySelector('.lp-final'), b = s.querySelector('.lp-bg'), c = getComputedStyle(b), i = getComputedStyle(b.querySelector('img')), m = /^inset\\(([\\d.e+-]+)%(?: round ([\\d.e+-]+)px)?/.exec(c.clipPath);
    // the honesty words of the band are its label; the line that the file is digital went in the lean pass of 2026-10-22 (the price list and the FAQ say it), so there is no second line to hold
    const chip = s.querySelector('.lp-final-chip'), cc = getComputedStyle(chip), fine = s.querySelector('.lp-fine'), sr = s.getBoundingClientRect(), cr = chip.getBoundingClientRect();
    return { op: +b.style.getPropertyValue('--op'), scrub: b.dataset.scrub !== undefined, run: b.hasAttribute('data-run'), raw: c.clipPath + ' ' + i.scale, clip: c.clipPath === 'none' ? 0 : m ? +m[1] : -1, round: m && m[2] ? +m[2] : 0, scale: i.scale === 'none' ? 1 : +i.scale, tr: i.translate + '|' + i.transform + '|' + b.style.opacity,
      chip: cc.visibility === 'visible' && +cc.opacity === 1 && cr.left >= sr.left && cr.right <= sr.right && !!chip.textContent.trim(), fine: fine === null,
      clock: document.getAnimations().filter((a) => a instanceof CSSAnimation && /^(lp-open|lp-rv-settle)$/.test(a.animationName) && b.contains(a.effect.target)).length }; })())`;
  const ps = [0, 0.15, 0.3, 0.5, 0.7, 0.85, 1.04];   // the last stop is a little past the end of the crossing: a stop AT 1 can only be placed to within a pixel, which is a few thousandths either side
  const rows = [];
  for (const p of ps) { await goto(p); rows.push([p, JSON.parse(await page.eval(PROBE))]); }
  for (const [p, r] of rows) {
    expect('final', near(r.op, Math.min(1, p), 0.02) && r.scrub && r.run === (r.op < 0.9995), `p ${p}: --op is ${r.op} (want ${Math.min(1, p)}), marked ${r.scrub}, data-run ${r.run} (want it off at the end)`);
    expect('final', near(r.clip, 7 * (1 - r.op), 0.12) && near(r.round, 28 * (1 - r.op), 0.6), `p ${p}: the clip is an inset of ${r.clip} percent with corners of ${r.round} px (want ${(7 * (1 - r.op)).toFixed(2)} and ${(28 * (1 - r.op)).toFixed(1)})`);
    expect('final', near(r.scale, 1 + 0.03 * (1 - r.op), 0.0008) && r.scale <= 1.0301, `p ${p}: the picture's scale is ${r.scale} (want ${(1 + 0.03 * (1 - r.op)).toFixed(4)}, never above 1.03)`);
    expect('final', r.tr === 'none|none|', `p ${p}: the picture moved or faded: ${r.tr}`);
    expect('final', r.chip && r.fine, `p ${p}: the label (${r.chip}) is not as it was, or the sentence about the file is back under the button (${!r.fine})`);
    expect('final', r.clock === 0, `p ${p}: ${r.clock} animations of the clock are running under the scroll`);
  }
  expect('final', monotone(rows.map(([, r]) => r.op), 1, 0.003) && monotone(rows.map(([, r]) => r.clip), -1, 0.1) && monotone(rows.map(([, r]) => r.scale), -1, 0.0006), 'going down the opening is not monotone');
  const e = rows.at(-1)[1];
  expect('final', e.raw === 'none none', `at the end the picture is not the static one (clip-path and scale should be none): ${e.raw}`);
  const back = [];
  for (const p of [...ps].reverse()) { await goto(p); back.push(JSON.parse(await page.eval(PROBE)).op); }
  expect('final', monotone(back, -1, 0.003), `going up, --op is not monotone: ${back.join(' ')}`);
  expect('final', page.errors.length === 0, `script errors: ${page.errors.join(' | ')}`);
  await page.close();
  if (clean('final')) pass('final', 'the closing picture opens with the scroll (inset 7 to 0 percent, corners 28 to 0 px, scale 1.03 to 1), monotonic both ways, whole at the end, no animation of the clock under it, the label and the sentence about the file as they were');
}

// ---------------------------------------------------------------------------------------------------- failsafe
async function checkFailsafe() {
  console.log('failsafe');
  // an in-app browser whose IntersectionObserver never reports: the engine switches on (html.mo), nothing is ever seen, and at 3.5 s html.mo-fail lifts every hidden state
  const dead = 'window.IntersectionObserver = class { constructor() {} observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } };';
  const t0 = Date.now();
  const page = await open({ width: 390, height: 844, pre: dead });
  const early = await page.eval('document.documentElement.className');
  await sleep(Math.max(0, 4600 - (Date.now() - t0)));
  const late = JSON.parse(await page.eval(`JSON.stringify({ cls: document.documentElement.className,
    scene: !!document.querySelector('.lp-rvp, .lp-rvp-stage'), sticky: [...document.querySelectorAll('#reveal *')].filter((e) => getComputedStyle(e).position === 'sticky').length,
    marks: document.querySelectorAll('[data-scrub]').length,
    plate: [...document.querySelectorAll('#stage img')].map((i) => { const c = getComputedStyle(i); return c.scale + ' ' + c.clipPath; }),
    draw: [...document.querySelectorAll('#ruler .lp-dr')].map((e) => getComputedStyle(e).strokeDashoffset), sq: [...document.querySelectorAll('#ruler .lp-sqg')].map((e) => getComputedStyle(e).opacity),
    band: (() => { const b = document.querySelector('.lp-final .lp-bg'); return getComputedStyle(b).clipPath + ' ' + getComputedStyle(b.querySelector('img')).scale; })(),
    hair: [...document.querySelectorAll('#steps .lp-num')].map((n) => getComputedStyle(n, '::after').scale) })`));
  expect('failsafe', /\bmo\b/.test(early) || /mo-fail/.test(early), `with a dead observer html is "${early}" at the start (want mo)`);
  expect('failsafe', /\bmo-fail\b/.test(late.cls), `html is "${late.cls}" 4.6 s after the start (want mo-fail: the failsafe)`);
  expect('failsafe', !late.scene && late.sticky === 0 && late.marks === 0, `after the failsafe: the phone's scene is ${late.scene ? 'still there' : 'gone'}, ${late.sticky} sticky elements, ${late.marks} marks`);
  expect('failsafe', late.plate.every((v) => v === 'none none') && late.draw.every((v) => v === '0px') && late.sq.every((v) => v === '1') && late.band === 'none none' && late.hair.every((v) => v === 'none'), `after the failsafe something is still hidden, clipped or scaled: ${JSON.stringify(late)}`);
  await page.close();
  // with a live observer it never appears
  const live = await open({ width: 390, height: 844 });
  await sleep(4200);
  const cls = await live.eval('document.documentElement.className');
  expect('failsafe', !/mo-fail/.test(cls) && /\bmo\b/.test(cls), `with a live observer html is "${cls}" (want mo and no mo-fail)`);
  await live.close();
  if (clean('failsafe')) pass('failsafe', 'a dead observer: html.mo-fail at 3.5 s, no phone scene, nothing pinned, clipped, scaled or undrawn; a live observer never gets it');
}

// ---------------------------------------------------------------------------------------------------- cls
async function checkCls() {
  console.log('cls');
  for (const [tag, o] of [['390 px', { width: 390, height: 844 }], ['1280 px', { width: 1280, height: 800 }]]) {
    const page = await open({ ...o, vitals: true });
    const H = await page.eval('document.documentElement.scrollHeight - innerHeight');
    await walk(page, H, 90, 55);
    await sleep(1200);
    await walk(page, 0, 120, 30);
    await sleep(600);
    const r = JSON.parse(await page.eval('JSON.stringify({ cls: window.__cls, shifts: window.__shifts })'));
    note(`cls ${tag}: ${r.cls.toFixed(4)} ${JSON.stringify(r.shifts.slice(0, 3))}`);
    expect('cls', r.cls <= 0.0005, `${tag}: layout shift ${r.cls.toFixed(4)} over a slow scroll of the whole page, down and up: ${JSON.stringify(r.shifts.slice(0, 4))}`);
    await page.close();
  }
  if (clean('cls')) pass('cls', 'no layout shift over a slow scroll of the whole page, down and up, at 390 and 1280 px');
}

// ---------------------------------------------------------------------------------------------------- identity
// The artwork rectangles of the scenes, with whatever is laid over them hidden. At rest they must be the same with the motion off and after the scenes have played: (1) the element and every
// ancestor carry exactly the same visual state (the end of a scene leaves no clip, scale or opacity behind), and (2) the pixels are identical with zero tolerance. Chrome draws a picture a
// little differently at another place of the page (tiles, dither and the position of a layer depend on the offset from the top of the page, whatever any motion does: measured on the build
// WITHOUT the phone scenes, a margin of one pixel above a picture changes up to 85 percent of its pixels by a level or two), and the phone's Reveal makes the page taller under motion. So the
// run with the motion off gets an empty block of exactly that height (a fraction of a pixel included) at the end of the Reveal: from there on every box lies at the same place.
async function checkIdentity() {
  console.log('identity');
  const TARGETS = [['#stage', 100], ['.lp-final', 60], ['#ruler .lp-sqg image', 140]];   // the plate, the closing band, and the artwork of the drawing (the four thumbnails of the owner's eye in the squares: the union of their boxes)
  const SIG = (sel) => `JSON.stringify((() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return null; const keys = ['opacity', 'transform', 'translate', 'scale', 'rotate', 'filter', 'clipPath', 'mixBlendMode', 'maskImage', 'visibility']; const out = [];
    const all = [e, ...e.querySelectorAll('img, svg, image, rect, path, circle, .lp-bg')];
    for (const x of all) for (let n = x; n && n !== document.documentElement; n = n.parentElement) { const c = getComputedStyle(n); out.push(keys.map((k) => c[k]).join('|')); }
    return [...new Set(out)].sort().join(' / '); })())`;
  const HIDE = '.lp-vis-chip, .lp-chip-ex, .lp-glint, .lp-final-chip, #sticky, #hdr, .lp-hdr, .lp-topbar { visibility: hidden !important; }';
  const shoot = async (reduceMotion, padTo) => {
    const page = await open({ width: 390, height: 844, dpr: 1, reduceMotion });
    await page.eval("document.documentElement.style.overflowAnchor = 'none'; document.body.style.overflowAnchor = 'none'");
    const rh = await page.eval("document.getElementById('reveal').getBoundingClientRect().height");
    if (padTo !== undefined) await page.eval(`(() => { const d = document.createElement('div'); d.style.height = '${padTo - rh}px'; document.getElementById('reveal').append(d); })()`);
    const out = [];
    for (const [sel, at] of TARGETS) {
      const y0 = await top(page, sel);
      if (y0 === null) { out.push(null); continue; }
      await walk(page, Math.max(0, Math.round(y0 - 1100)));
      await walk(page, Math.round(y0 - at), 90, 40);
      await place(page, sel, at);
      await sleep(5200);   // every entrance of the chapter is over, every scene is at rest
      await style(page, 'hide', HIDE);
      await page.eval('new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))');
      await sleep(150);
      // the box of the target; for a list (the four thumbnails) the union of their boxes
      const r = JSON.parse(await page.eval(`JSON.stringify((() => { const bs = [...document.querySelectorAll(${JSON.stringify(sel)})].map((e) => e.getBoundingClientRect()), l = Math.min(...bs.map((b) => b.left)), t = Math.min(...bs.map((b) => b.top)), rr = Math.max(...bs.map((b) => b.right)), bb = Math.max(...bs.map((b) => b.bottom)); return [Math.round(l), Math.round(t), Math.round(rr - l), Math.round(bb - t), t + scrollY]; })())`));
      out.push({ png: await shot(page), rect: r.slice(0, 4), abs: r[4], fits: r[1] >= 0 && r[1] + r[3] <= 844, sig: await page.eval(SIG(sel)) });
      await style(page, 'hide', '');
    }
    await page.close();
    return { out, rh };
  };
  const m = await shoot(false);
  const a = await shoot(true, m.rh);
  for (let i = 0; i < TARGETS.length; i++) {
    const name = TARGETS[i][0], A = a.out[i], M = m.out[i];
    if (!expect('identity', A && M, `${name} was not found in both runs`)) continue;
    expect('identity', A.sig === M.sig, `${name}: its visual state differs between reduced motion and motion after the scenes:\n    ${A.sig}\n    ${M.sig}`);
    expect('identity', A.rect[2] === M.rect[2] && A.rect[3] === M.rect[3], `${name}: its size differs (${A.rect.slice(2)} against ${M.rect.slice(2)})`);
    expect('identity', A.fits && M.fits, `${name} does not fit the screen, so its pixels cannot be compared`);
    if (Math.abs(A.abs - M.abs) > 0.01) { note(`identity: ${name} lies at another place of the page (${A.abs.toFixed(3)} and ${M.abs.toFixed(3)}): the visual state is the verdict`); continue; }
    const inner = name === '.lp-final' ? A.rect : name.includes('image') ? A.rect : [A.rect[0] + 24, A.rect[1] + 24, A.rect[2] - 48, A.rect[3] - 48];   // without the rounded corners: Chrome anti-aliases the corners of a clipped frame a little differently from one layer to the next (check_reveal compares the same way)
    const d = await pngDiff(A.png, M.png, inner);
    expect('identity', !d.size && d.n === 0, `${name}: ${d.n} pixels differ between reduced motion and motion after the scenes (by up to ${d.max} levels${d.size ? ', sizes ' + d.size : ''})`);
    note(`identity: ${name} ${A.rect[2]} x ${A.rect[3]} px (the band whole, the frames without their 24 px corners) at ${A.abs.toFixed(3)} from the top of the page in both runs: ${d.n} pixels differ`);
  }
  if (clean('identity')) pass('identity', 'the plate, the closing picture and the drawing: the same visual state and the same pixels (zero tolerance) with the motion off and after the scenes have played, at the same place of the page');
}

// ---------------------------------------------------------------------------------------------------- run
const RUN = { absent: checkAbsent, reveal: checkReveal, fit: checkFit, wall: checkWall, size: checkSize, how: checkHow, final: checkFinal, failsafe: checkFailsafe, cls: checkCls, identity: checkIdentity };
for (const [name, fn] of Object.entries(RUN)) if (wants(name)) await fn();
await chrome.close();
await site.close();
if ((mutations.css || mutations.js) && !mutated) fail('mutation', 'the text to change was not found in any file of the chunk: a mistyped mutation proves nothing');
console.log(problems.length ? `\n${problems.length} problem(s)` : '\nall ok');
process.exit(problems.length ? 1 : 0);
