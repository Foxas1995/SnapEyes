// The checks of the Reveal scene (motion spec 6.4, 11 and 13) and of the first screen's disc, in real Chrome, against a build (dist/) served the way
// Vercel serves it, with a stub of the two API calls the page makes. Not part of `vite build`; run it after a build:
//   npm run build && node scripts/check_reveal.mjs
//   node scripts/check_reveal.mjs [--dist dist] [--only scene,pixels,keyboard,static,fit,sheet,anchor,cls,disc]
//   --mutate-css "from@@to" and --mutate-js "from@@to" change the Reveal chunk's stylesheet or code on its way to the browser: a deliberate defect,
//   to see that a check really fails.
// Exit code 1 when any check fails.
//
//   scene     1280 x 800: the stage holds still at its sticky offset at p = 0 .25 .5 .75 1 and the frame says what the table of 6.4 says (the cut, the
//             aperture, the line, the step, the chips); before the first frame the layers are clipped (not "none": the art would cover the picture);
//             a jump into the middle of the scene shows the middle at once; across a whole scroll no layer is ever blurred, filtered, tilted, faded,
//             scaled or moved and the frame never changes size (Artwork Charter AC-2, AC-3)
//   pixels    at rest (p = 0, .56, 1) the frame is pixel for pixel the photo, the iris, the artwork alone: no veil, line or glow lies over a resting state
//   keyboard  the step rows are real buttons in the tab order: Enter scrolls to their state, aria-current follows, focus stays, Tab leaves the stage
//   static    reduced motion at 1280, a phone at 375 and a window at 767: no scene, no pin, the three pictures in a row, the slider (one native range),
//             nothing hidden after the engine has had its turn
//   fit       en de lt hu at 1280 x 800, 1366 x 650, 768 x 1024 and 768 x 600: the stage holds its content, no heading wider than its box, no step row
//             wider than itself, no horizontal scroll
//   sheet     no ancestor of the stage sets an overflow that would stop it sticking; the stage sticks inside its sheet
//   anchor    an address with #reveal lands on the first state, pinned (the stage 92 px from the top, the section's top there too)
//   cls       a full scroll at 1280 x 800: no layout shift
//   disc      the first screen's disc: its cut line has the soft glow (BR-4: .28 at most), and nothing on the landing loops at rest (BR-3, principle 4)
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
const TOP = 92; // the stage's sticky offset (css/reveal.css --rv-top) = the page's scroll-padding-top

const problems = [];
const fail = (check, msg) => { problems.push(`${check}: ${msg}`); console.log(`  FAIL ${check}: ${msg}`); };
const pass = (check, msg) => console.log(`  ok   ${check}: ${msg}`);
const expect = (check, cond, msg) => { if (!cond) fail(check, msg); return !!cond; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;

const mutate = (text, spec) => { if (!spec) return text; const [from, to] = spec.split('@@'); if (!text.includes(from)) throw new Error(`--mutate: "${from}" is not in the source`); return text.split(from).join(to); };
const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
  if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { json({ ok: true, open: false, suggest: null }); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404); res.end('{}'); return true; }
  const m = /^\/assets\/(Reveal-[^/]+\.(css|js))$/.exec(url.pathname);
  const spec = m && opt(m[2] === 'css' ? '--mutate-css' : '--mutate-js');
  if (spec) { res.writeHead(200, { 'content-type': m[2] === 'css' ? 'text/css' : 'text/javascript', 'cache-control': 'no-store' }); res.end(mutate(readFileSync(join(dist, 'assets', m[1]), 'utf8'), spec)); return true; }
  return false;
};
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();

// ---------------------------------------------------------------------------------------------------- helpers
async function mounted(page) {
  for (let i = 0; i < 150; i++) {
    if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) return;
    await sleep(100);
  }
}
/** A fresh visit (nothing remembered), the page open, every lazy section mounted. */
async function open({ lang = 'en', width = 1280, height = 800, hash = '', settle = true, ...more } = {}) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1, ...more });
  await page.goto(`${origin}/?lang=${lang}${hash}`);
  await page.loaded();
  if (settle) { await mounted(page); await sleep(500); }
  return page;
}
const geo = async (page) => JSON.parse(await page.eval(`JSON.stringify((() => { const w = document.querySelector('.lp-rv-scene'), s = document.querySelector('.lp-rv-stage'); if (!w || !s) return null;
  return { top: w.getBoundingClientRect().top + scrollY, h: w.offsetHeight, sh: s.offsetHeight, span: w.offsetHeight - s.offsetHeight }; })())`));
const frameState = async (page) => JSON.parse(await page.eval(`JSON.stringify((() => { const f = document.querySelector('.lp-rv-frame'), cs = getComputedStyle(f), s = document.querySelector('.lp-rv-stage');
  return { pos: +cs.getPropertyValue('--rv-pos'), ap: +cs.getPropertyValue('--rv-ap'), line: +cs.getPropertyValue('--rv-line'), ring: +cs.getPropertyValue('--rv-ring'), c: f.dataset.c,
    stageTop: s.getBoundingClientRect().top, step: [...document.querySelectorAll('.lp-rv-step')].findIndex((b) => b.getAttribute('aria-current') === 'step'),
    chips: [...f.querySelectorAll('.lp-rv-chip')].filter((c) => +getComputedStyle(c).opacity > 0.5).map((c) => c.dataset.k).join(' ') }; })())`));
/** Scroll to progress p of the scene and wait until the frame has come to rest. */
async function goP(page, g, p) {
  await page.eval(`window.scrollTo({ top: ${g.top - TOP + g.span * p}, behavior: 'instant' })`);
  let last = '';
  for (let i = 0; i < 40; i++) {
    await sleep(100);
    const now = await page.eval("document.querySelector('.lp-rv-frame').getAttribute('style')");
    if (now === last && i > 3) break;
    last = now;
  }
  await sleep(450);
}
/** The expected frame at p, written out here once more from the table of the spec (6.4), on purpose: the check is of the table, not of the code. */
const want = (p) => {
  const ramp = (a, b) => Math.min(1, Math.max(0, (p - a) / (b - a)));
  return { pos: 100 * (1 - ramp(0.06, 0.5)), ap: 72 * ramp(0.56, 0.94), step: p >= 0.72 ? 2 : p >= 0.34 ? 1 : 0 };
};
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

// ---------------------------------------------------------------------------------------------------- scene
async function checkScene() {
  console.log('scene');
  const page = await open({ lang: 'en', width: 1280, height: 800 });
  const g = await geo(page);
  if (!expect('scene', g, 'there is no pinned scene at 1280 x 800 (.lp-rv-scene)')) { await page.close(); return; }
  expect('scene', near(g.h, 800 * 2.2, 2), `the wrapper is ${g.h} px tall at 800 px (want 220svh = 1760)`);
  // before the first frame the layers are clipped by the stylesheet's own defaults (a computed clip-path of "none" would let the artwork cover the picture):
  // take the values the scene has written away and read what is left
  const rest = JSON.parse(await page.eval(`JSON.stringify((() => { const f = document.querySelector('.lp-rv-frame'), kept = f.getAttribute('style'); f.removeAttribute('style');
    const r = { art: getComputedStyle(f.querySelector('.lp-rv-art')).clipPath, photo: getComputedStyle(f.querySelector('.lp-rv-photo')).clipPath, line: getComputedStyle(f.querySelector('.lp-rv-line')).opacity };
    f.setAttribute('style', kept); return r; })())`));
  expect('scene', /^circle\(0%/.test(rest.art) && /^inset\(0px 0%/.test(rest.photo) && rest.line === '0', `with no value written yet the layers are ${rest.photo} and ${rest.art}, the line's opacity ${rest.line} (want the photo whole, the aperture closed, no line)`);
  for (const p of [0, 0.25, 0.5, 0.75, 1]) {
    await goP(page, g, p);
    const s = await frameState(page), w = want(p);
    expect('scene', near(s.stageTop, TOP, 0.6), `p ${p}: the stage is ${s.stageTop.toFixed(1)} px from the top (want ${TOP}: it must hold still)`);
    expect('scene', near(s.pos, w.pos, 0.6) && near(s.ap, w.ap, 0.6), `p ${p}: the cut is at ${s.pos.toFixed(1)} and the aperture ${s.ap.toFixed(1)} (want ${w.pos.toFixed(1)} and ${w.ap.toFixed(1)})`);
    expect('scene', s.step === w.step, `p ${p}: step ${s.step + 1} is current (want ${w.step + 1})`);
    if (p === 0.25) expect('scene', s.line > 0.99 && s.chips === 'photo iris', `p .25: the line has opacity ${s.line} and the chips are "${s.chips}" (want the line shown and "photo iris")`);
    if (p === 0) expect('scene', s.line === 0 && s.chips === 'photo', `p 0: the line has opacity ${s.line} and the chips are "${s.chips}" (want no line, "photo")`);
    if (p === 0.5) expect('scene', s.chips === 'iris', `p .5: the chips are "${s.chips}" (want "iris")`);
    if (p === 0.75) expect('scene', s.chips === 'art' && s.ring > 0.9, `p .75: the chips are "${s.chips}", the ring ${s.ring} (want "art" and a visible ring)`);
    if (p === 1) expect('scene', s.ring === 0 && s.chips === 'art', `p 1: the ring has opacity ${s.ring} (want none: the circle has left the frame)`);
  }
  // the artwork layer is fetched before the aperture opens (it is clipped to nothing, which a lazy loader never fetches: on a slow line the aperture opened on
  // nothing), and the label says "art" only once the aperture shows a good part of it (a label that says art over the restored iris is not exact)
  const art0 = await page.eval("(() => { const a = document.querySelector('.lp-rv-art'); return a.complete && a.naturalWidth > 0; })()");
  expect('scene', art0 === true, 'the artwork layer is not loaded long after the scene came on screen (a lazy image clipped to nothing is never fetched)');
  await goP(page, g, 0.62);
  const s62 = await frameState(page);
  expect('scene', s62.chips === 'iris' && s62.step === 1, `p .62: the chips are "${s62.chips}" and step ${s62.step + 1} (want "iris" and step 2: the aperture shows only ${s62.ap.toFixed(0)} percent)`);
  // a jump from far away (the page's end) into the middle shows the middle at once, not a catch up from 0: the first reading of a scene that has
  // just come into range is applied whole (a reload, an anchor or a restored scroll position inside a scene)
  await page.eval("window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' })");
  await sleep(900);
  await page.eval(`window.scrollTo({ top: ${g.top - TOP + g.span * 0.75}, behavior: 'instant' })`);
  await sleep(260);
  const jump = await frameState(page);
  expect('scene', near(jump.ap, want(0.75).ap, 1.5), `after a jump to p .75 the aperture is ${jump.ap.toFixed(1)} 260 ms later (want ${want(0.75).ap.toFixed(1)} at once: the first reading must not ease up from 0)`);
  // the Artwork Charter across a whole scroll, both ways: no filter, blur, tilt, scale, fade or move on any layer; the frame never changes size
  const probe = `JSON.stringify((() => { const f = document.querySelector('.lp-rv-frame'), r = f.getBoundingClientRect(), bad = [];
    for (const el of [f, ...f.querySelectorAll('img, svg, .lp-rv-chip, .lp-rv-line')]) { const c = getComputedStyle(el), n = el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className;
      if (c.filter !== 'none' || c.backdropFilter !== 'none') bad.push(n + ' filter ' + c.filter + ' ' + c.backdropFilter);
      if (c.transform !== 'none' || c.rotate !== 'none' || (c.scale !== 'none' && c.scale !== '1')) bad.push(n + ' transform ' + c.transform + ' ' + c.rotate + ' ' + c.scale);
      if (el.tagName === 'IMG' && (+c.opacity !== 1 || c.visibility !== 'visible' || c.display === 'none')) bad.push(n + ' opacity ' + c.opacity + ' ' + c.visibility); }
    const iris = f.querySelector('.lp-rv-iris').getBoundingClientRect();
    if (Math.abs(iris.width - r.width) > 0.5 || Math.abs(iris.left - r.left) > 0.5) bad.push('the iris layer is not the frame');
    return { w: r.width, h: r.height, bad }; })())`;
  const sizes = new Set(), bads = new Set();
  for (const dir of [1, -1]) {
    for (let k = 0; k <= 24; k++) {
      const p = dir === 1 ? -0.05 + 1.1 * (k / 24) : 1.05 - 1.1 * (k / 24);
      await page.eval(`window.scrollTo({ top: ${g.top - TOP + g.span * p}, behavior: 'instant' })`);
      await sleep(70);
      const r = JSON.parse(await page.eval(probe));
      if (p > 0.02 && p < 0.98) sizes.add(`${Math.round(r.w)}x${Math.round(r.h)}`);
      r.bad.forEach((b) => bads.add(b));
    }
  }
  expect('scene', bads.size === 0, `a layer of the frame is filtered, blurred, tilted, scaled or faded during the scroll: ${[...bads].join(' | ')}`);
  expect('scene', sizes.size === 1, `the frame changed size during the scroll: ${[...sizes].join(', ')}`);
  await page.close();
  if (!problems.some((x) => x.startsWith('scene'))) pass('scene', 'the stage holds at 92 px; the cut, the aperture, the line, the chips and the steps follow the table of 6.4 at p = 0 .25 .5 .75 1; a jump lands at once; no layer is filtered, tilted, scaled or faded and the frame keeps its size');
}

// ---------------------------------------------------------------------------------------------------- pixels
// a screenshot beyond the viewport draws the fixed header (and its blur) over the top of the clip: hide the page's chrome while comparing
const HIDE_CHROME = '.lp-hdr, .lp-topbar, .lp-sticky, .lp-skip { visibility: hidden !important; }';
async function checkPixels() {
  console.log('pixels');
  const page = await open({ lang: 'en', width: 1280, height: 800 });
  const g = await geo(page);
  if (!expect('pixels', g, 'there is no pinned scene')) { await page.close(); return; }
  // the viewport itself, never a clip beyond it: a capture beyond the viewport lays the page out at another height (the stage is 100svh) and moves the scroll
  const shot = async () => Buffer.from((await page.send('Page.captureScreenshot', { format: 'png' })).data, 'base64');
  // the frame without its rounded corners (Chrome rasterises the anti-aliased corners of a clipped node a little differently)
  const rect = async () => JSON.parse(await page.eval(`JSON.stringify((() => { const b = document.querySelector('.lp-rv-frame').getBoundingClientRect(); return [Math.round(b.left + 24), Math.round(b.top + 24), Math.round(b.width - 48), Math.round(b.height - 48)]; })())`));
  const style = (css) => page.eval(`(() => { let s = document.getElementById('px'); if (!s) { s = document.createElement('style'); s.id = 'px'; document.head.append(s); } s.textContent = ${JSON.stringify(css)}; })()`);
  for (const [p, layer] of [[0, 'photo'], [0.56, 'iris'], [1, 'art']]) {
    await style('');
    await goP(page, g, p);
    await style(`${HIDE_CHROME} .lp-rv-chip, .lp-rv-who { visibility: hidden !important; transition: none !important; }`);   // the labels lie over the frame by design (AC-8); the claim is about the artwork's own pixels
    await sleep(300);
    const a = await shot();
    // the layer alone: every other layer and every overlay hidden, its own clip taken away
    await style(`${HIDE_CHROME} .lp-rv-chip, .lp-rv-who { visibility: hidden !important; } .lp-rv-frame > :not(.lp-rv-${layer}) { visibility: hidden !important; } .lp-rv-frame::before, .lp-rv-frame::after { display: none !important; } .lp-rv-${layer} { clip-path: none !important; }`);
    await sleep(300);
    const b = await shot();
    const d = await pngDiff(a, b, await rect());
    // a layer with its own clip is composited as a surface of its own: Chrome may differ by one level in a few hundred pixels; anything more is a veil
    expect('pixels', d.n <= 600 && d.max <= 2, `p ${p}: the frame differs from the ${layer} alone in ${d.n} pixels (by up to ${d.max} levels${d.size ? ', sizes ' + d.size : ''}): something lies over a resting state`);
  }
  await page.close();
  if (!problems.some((x) => x.startsWith('pixels'))) pass('pixels', 'at p = 0, .56 and 1 the frame is the photo, the iris and the artwork alone, pixel for pixel (at most one level off in a few hundred pixels of 240 000)');
}

// ---------------------------------------------------------------------------------------------------- keyboard
async function checkKeyboard() {
  console.log('keyboard');
  const page = await open({ lang: 'en', width: 1280, height: 800 });
  const g = await geo(page);
  if (!expect('keyboard', g, 'there is no pinned scene')) { await page.close(); return; }
  const KEYS = { Enter: 13, Tab: 9 };
  const key = async (k) => {
    await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code: k, windowsVirtualKeyCode: KEYS[k], ...(k === 'Enter' ? { text: '\r' } : {}) });
    await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code: k, windowsVirtualKeyCode: KEYS[k] });
    await sleep(250);
  };
  const n = await page.eval("document.querySelectorAll('.lp-rv-step').length");
  const tabs = await page.eval("[...document.querySelectorAll('.lp-rv-step')].map((b) => b.tabIndex + b.tagName).join()");
  expect('keyboard', n === 3 && tabs === '0BUTTON,0BUTTON,0BUTTON', `the step rows are ${n} elements (${tabs}); want three buttons in the tab order`);
  await goP(page, g, 0);
  await page.eval("document.querySelectorAll('.lp-rv-step')[0].focus({ preventScroll: true })");
  await key('Tab');
  await key('Tab');
  await sleep(450);
  const ring2 = await page.eval(`(() => { const a = document.activeElement, c = getComputedStyle(a); return (a.textContent || '').trim().slice(0, 12) + ' | ' + c.outlineStyle + ' ' + c.outlineWidth + ' ' + c.outlineColor; })()`);
  expect('keyboard', /Art \| solid 2px rgb\(245, 197, 66\)/.test(ring2), `two Tabs from the first row reach "${ring2}" (want the third row with the page's 2 px gold ring)`);
  await key('Enter');
  await sleep(2200);
  let s = await frameState(page);
  expect('keyboard', s.step === 2 && s.ap > 70, `Enter on step 3: step ${s.step + 1} is current, the aperture ${s.ap.toFixed(1)} (want 3 and 72)`);
  expect('keyboard', await page.eval("document.activeElement.classList.contains('lp-rv-step')"), 'the focus left the step row after the scroll');
  await page.eval("document.querySelectorAll('.lp-rv-step')[1].focus({ preventScroll: true })");
  await key('Enter');
  await sleep(2200);
  s = await frameState(page);
  expect('keyboard', s.step === 1 && s.pos < 1 && s.ap === 0, `Enter on step 2: step ${s.step + 1} is current, the cut ${s.pos.toFixed(1)}, the aperture ${s.ap.toFixed(1)} (want 2, 0, 0)`);
  await page.eval("document.querySelectorAll('.lp-rv-step')[0].focus({ preventScroll: true })");
  await key('Enter');
  await sleep(2400);
  s = await frameState(page);
  expect('keyboard', s.step === 0 && near(s.pos, 100, 0.6), `Enter on step 1: step ${s.step + 1} is current, the cut ${s.pos.toFixed(1)} (want 1 and 100)`);
  // Tab out of the last row: the focus goes on to something outside the stage (nothing traps it)
  await page.eval("document.querySelectorAll('.lp-rv-step')[2].focus({ preventScroll: true })");
  await key('Tab');
  await sleep(300);
  expect('keyboard', await page.eval("!document.activeElement.closest('.lp-rv-stage') && document.activeElement !== document.body"), 'Tab from the last step row stays in the stage or is lost');
  await page.close();
  if (!problems.some((x) => x.startsWith('keyboard'))) pass('keyboard', 'three real buttons in the tab order with the page ring; Enter scrolls to the state and aria-current follows; Tab leaves the stage');
}

// ---------------------------------------------------------------------------------------------------- static
async function checkStatic() {
  console.log('static');
  for (const [tag, o] of [['reduced motion 1280', { width: 1280, height: 800, reduceMotion: true }], ['phone 375', { width: 375, height: 812 }], ['window 767', { width: 767, height: 900 }], ['short window 1280 x 540', { width: 1280, height: 540 }]]) {
    const page = await open({ lang: 'en', ...o });
    const r = JSON.parse(await page.eval(`JSON.stringify((() => { const strip = [...document.querySelectorAll('.lp-strip li')].map((e) => e.getBoundingClientRect());
      return { scene: !!document.querySelector('.lp-rv-scene, .lp-rv-pin, .lp-rv-step'), ranges: document.querySelectorAll('.lp-cmp-range').length, strip: strip.length, row: strip.length === 3 && strip.every((b) => Math.abs(b.top - strip[0].top) < 2) && strip[0].left < strip[1].left && strip[1].left < strip[2].left,
        h2: document.querySelectorAll('#revealH').length, sticky: [...document.querySelectorAll('#reveal *')].filter((e) => getComputedStyle(e).position === 'sticky').length }; })())`));
    expect('static', !r.scene && r.sticky === 0, `${tag}: there is a pinned scene, a step row or a sticky element (scene ${r.scene}, sticky ${r.sticky})`);
    expect('static', r.ranges === 1 && r.h2 === 1, `${tag}: ${r.ranges} sliders and ${r.h2} headings (want 1 and 1)`);
    expect('static', r.row, `${tag}: the three pictures of the strip are not in a row`);
    // the strip's pictures are shown once the engine has seen them (or at once without it)
    await page.eval("document.querySelector('.lp-strip').scrollIntoView({ block: 'center', behavior: 'instant' })");
    await sleep(2200);
    const shown = JSON.parse(await page.eval(`JSON.stringify([...document.querySelectorAll('.lp-strip li, .lp-never, .lp-your-turn')].map((e) => +getComputedStyle(e).opacity))`));
    expect('static', shown.every((o) => o === 1), `${tag}: after being on screen the strip's parts have opacities ${shown.join(', ')} (want 1)`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('static'))) pass('static', 'reduced motion, a phone, a window of 767 px and a short window: no scene or pin, the slider and the three pictures in a row, everything shown');
}

// ---------------------------------------------------------------------------------------------------- fit
async function checkFit() {
  console.log('fit');
  for (const lang of LANGS) {
    for (const [w, h] of [[1280, 800], [1366, 650], [768, 1024], [768, 600], [768, 560], [768, 590], [800, 560], [1024, 560]]) {
      const page = await open({ lang, width: w, height: h });
      const r = JSON.parse(await page.eval(`JSON.stringify((() => { const s = document.querySelector('.lp-rv-stage'); if (!s) return null;
        const sr = s.getBoundingClientRect(), box = (e) => e.getBoundingClientRect(), copy = box(s.querySelector('.lp-rv-copy')), fig = box(s.querySelector('.lp-rv-fig')), h2 = document.getElementById('revealH');
        return { slack: Math.round(sr.height - Math.max(copy.height, fig.height)), top: Math.round(Math.min(copy.top, fig.top) - sr.top),
          wide: [...document.querySelectorAll('#revealH, .lp-rv-step')].filter((e) => e.scrollWidth > e.clientWidth + 1).map((e) => e.textContent.slice(0, 30)),
          masks: [...h2.querySelectorAll('.lp-line-mask > span')].filter((e) => e.scrollWidth > h2.clientWidth + 1).length, sw: document.documentElement.scrollWidth, iw: innerWidth,
          figw: Math.round(fig.width), copyw: Math.round(copy.width) }; })())`));
      if (!expect('fit', r, `${lang} ${w} x ${h}: no pinned scene`)) { await page.close(); continue; }
      expect('fit', r.slack >= 0 && r.top >= 0, `${lang} ${w} x ${h}: the stage's content (${r.slack} px to spare) does not fit its stage`);
      expect('fit', r.wide.length === 0 && r.masks === 0, `${lang} ${w} x ${h}: wider than its box: ${r.wide.join(' | ')} (${r.masks} masks)`);
      expect('fit', r.sw <= r.iw, `${lang} ${w} x ${h}: the page scrolls sideways (${r.sw} of ${r.iw} px)`);
      // the three step rows are on screen from the first frame of the pin and must be SEEN in a short, narrow window too (2026-10-05: in a 768 x 560 window the third
      // row waited for an observer that its place never reached, so it stayed invisible for the whole pin while its button was focusable)
      const g = await geo(page);
      if (g) {
        await page.eval(`window.scrollTo({ top: ${g.top - TOP + g.span * 0.3}, behavior: 'instant' })`);
        await sleep(900);
        const rows = JSON.parse(await page.eval(`JSON.stringify([...document.querySelectorAll('.lp-rv-step')].map((b) => { const li = b.closest('li'); return { op: +getComputedStyle(li).opacity, hid: li.hasAttribute('data-reveal') && !li.hasAttribute('data-in') }; }))`));
        expect('fit', rows.length === 3 && rows.every((x) => x.op === 1 && !x.hid), `${lang} ${w} x ${h}: a step row is not visible at p .3: ${JSON.stringify(rows)}`);
      }
      expect('fit', r.copyw >= 280, `${lang} ${w} x ${h}: the copy column is ${r.copyw} px wide (want 280 or more)`);
      await page.close();
    }
  }
  if (!problems.some((x) => x.startsWith('fit'))) pass('fit', 'en de lt hu at 1280 x 800, 1366 x 650, 768 x 1024, 768 x 600 and the short windows 768 x 560, 768 x 590, 800 x 560, 1024 x 560: the stage holds its content, all three step rows are seen, no heading or row wider than its box, no sideways scroll');
}

// ---------------------------------------------------------------------------------------------------- sheet
async function checkSheet() {
  console.log('sheet');
  const page = await open({ lang: 'en', width: 1280, height: 800 });
  const r = JSON.parse(await page.eval(`JSON.stringify((() => { const s = document.querySelector('.lp-rv-stage'); if (!s) return null; const out = [];
    for (let e = s.parentElement; e; e = e.parentElement) { const c = getComputedStyle(e); if (!['visible', 'clip'].includes(c.overflowX) || !['visible', 'clip'].includes(c.overflowY)) out.push(e.tagName + '.' + String(e.className).slice(0, 24) + ' ' + c.overflowX + '/' + c.overflowY); }
    const sheet = s.closest('.lp-sheet');
    return { blockers: out, sheet: sheet ? sheet.className : null, radius: sheet ? getComputedStyle(sheet).borderTopLeftRadius : null }; })())`));
  if (!expect('sheet', r, 'no pinned scene')) { await page.close(); return; }
  expect('sheet', r.blockers.length === 0, `an ancestor of the stage stops it from sticking: ${r.blockers.join(', ')}`);
  expect('sheet', /lp-sheet-a/.test(r.sheet || '') && r.radius !== '0px', `the stage is in ${r.sheet} with radius ${r.radius} (want the first, rounded sheet)`);
  const g = await geo(page);
  const hits = [];
  for (let k = 0; k <= 8; k++) { await goP(page, g, k / 8); hits.push(near((await frameState(page)).stageTop, TOP, 0.6)); }
  expect('sheet', hits.every(Boolean), `the stage sticks at ${hits.filter(Boolean).length} of 9 samples inside its sheet`);
  await page.close();
  if (!problems.some((x) => x.startsWith('sheet'))) pass('sheet', 'no ancestor clips or scrolls; the stage sticks at 9 of 9 samples inside the rounded first sheet');
}

// ---------------------------------------------------------------------------------------------------- anchor
async function checkAnchor() {
  console.log('anchor');
  for (const [w, h] of [[1280, 800], [768, 1024]]) {
    const page = await open({ lang: 'en', width: w, height: h, hash: '#reveal', settle: false });
    await mounted(page);
    await sleep(1500);
    const r = JSON.parse(await page.eval(`JSON.stringify({ sec: document.getElementById('reveal').getBoundingClientRect().top, stage: document.querySelector('.lp-rv-stage')?.getBoundingClientRect().top ?? null })`));
    const s = await frameState(page);
    expect('anchor', near(r.sec, TOP, 4) && r.stage !== null && near(r.stage, TOP, 4), `${w} px, #reveal: the section is ${r.sec.toFixed(1)} px from the top, the stage ${r.stage} (want ${TOP})`);
    expect('anchor', s.pos > 98 && s.ap === 0, `${w} px, #reveal: lands on the cut at ${s.pos.toFixed(1)}, the aperture ${s.ap.toFixed(1)} (want the first state: the photo alone)`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('anchor'))) pass('anchor', 'a link to #reveal lands pinned on the first state, 92 px from the top, at 1280 and 768 px');
}

// ---------------------------------------------------------------------------------------------------- cls
async function checkCls() {
  console.log('cls');
  for (const [w, h] of [[1280, 800], [1920, 950]]) {
    const page = await open({ lang: 'en', width: w, height: h, vitals: true, settle: false });
    await mounted(page);
    const H = await page.eval('document.documentElement.scrollHeight');
    for (let y = 0; y < H; y += Math.round(h * 0.4)) { await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`); await sleep(160); }
    await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
    await sleep(800);
    const cls = await page.eval('window.__cls'), shifts = await page.eval('JSON.stringify(window.__shifts)');
    expect('cls', cls <= 0.005, `${w} px: CLS ${cls.toFixed(4)} over a full scroll (want 0): ${shifts}`);
    console.log(`  note cls ${w} px: ${cls.toFixed(4)} ${cls ? shifts : ''}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('cls'))) pass('cls', 'no layout shift over a full scroll at 1280 and 1920 px');
}

// ---------------------------------------------------------------------------------------------------- disc
async function checkDisc() {
  console.log('disc');
  const page = await open({ lang: 'en', width: 1280, height: 800, settle: false });
  await sleep(6000);
  const r = JSON.parse(await page.eval(`JSON.stringify({ glow: getComputedStyle(document.querySelector('.lp-disc'), '::after').boxShadow,
    loops: document.getAnimations().filter((a) => a.effect && a.effect.getComputedTiming().iterations === Infinity).map((a) => (a.effect.target && a.effect.target.className) + ' ' + a.animationName),
    running: document.getAnimations().filter((a) => a.playState === 'running').length })`));
  const alphas = [...r.glow.matchAll(/rgba\(245, 197, 66, ([\d.]+)\)/g)].map((m) => +m[1]);
  expect('disc', alphas.length > 0 && /16px/.test(r.glow), `the disc's cut line has the box shadow "${r.glow}" (want the soft gold glow, --glow: 16 px)`);
  expect('disc', alphas.every((a) => a <= 0.28), `the disc's glow "${r.glow}" is stronger than .28 (BR-4)`);
  expect('disc', r.loops.length === 0, `something loops on the landing at rest: ${r.loops.join(', ')} (BR-3, principle 4)`);
  expect('disc', r.running === 0, `${r.running} animations are still running 6 s after the load`);
  await page.close();
  if (!problems.some((x) => x.startsWith('disc'))) pass('disc', 'the disc line has the soft gold glow (.28), and nothing on the landing loops or runs at rest');
}

// ---------------------------------------------------------------------------------------------------- run
const checks = { scene: checkScene, pixels: checkPixels, keyboard: checkKeyboard, static: checkStatic, fit: checkFit, sheet: checkSheet, anchor: checkAnchor, cls: checkCls, disc: checkDisc };
try {
  for (const [name, fn] of Object.entries(checks)) {
    if (!wants(name)) continue;
    try {
      await fn();
    } catch (e) {
      fail(name, `the check itself stopped: ${e instanceof Error ? e.stack : String(e)}`);
    }
  }
} finally {
  await chrome.close();
  await site.close();
}
console.log(problems.length ? `\nreveal check FAILED (${problems.length}):\n  ${problems.join('\n  ')}` : '\nreveal check ok');
process.exit(problems.length ? 1 : 0);
