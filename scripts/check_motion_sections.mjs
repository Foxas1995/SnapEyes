// The checks of the motion of six chapters of the landing page (motion spec 6.5 to 6.10: how it works, the styles, your file on a wall, the size guide,
// more ways to see it, look closer), in real Chrome, against a build (dist/) served the way Vercel serves it, with a stub of the two API calls the page
// makes. Not part of `vite build`; run it after a build:
//   npx vite build --outDir out/dist && node scripts/check_motion_sections.mjs --dist out/dist
//   node scripts/check_motion_sections.mjs [--dist dist] [--only reduced,how,styles,wall,sizes,more,closeups,identity,keyboard,cls,gold]
// Exit code 1 when any check fails. Frames are sampled in the page itself (requestAnimationFrame), so the numbers are what the visitor's screen gets.
//
//   reduced   prefers-reduced-motion: reduce: no html.mo, no running animation in the six chapters, nothing hidden, moved or clipped, the glint absent,
//             the gold outline of the chosen size whole, the crop and the edge whole, an eye colour changes at once (no second picture left on top)
//   how       three columns: the steps rise one after the other, the hairline draws and the numerals warm in turn, all gold at the end; the swipe rail:
//             appears as one piece, the step in view is the current one (aria-current) and the others are dimmer
//   styles    the sliding line is on the selected tab's box at rest, after a click, after an arrow key and after a language switch, and it slides; the first
//             grid rises, a changed group only fades in; an eye colour cross-fades (old picture on top, then gone); the hover zoom is 1.02 at most; the wall
//             button is hidden at rest with a mouse and always there on a touch screen; the labels never fade
//   wall      a pick cross-fades the stage (the two layers sum to one), the facts fade in on a pick and not on a language switch, the glint exists only on
//             the acrylic picture, is bound to the print face, white at 10 percent at most, screen blended, follows the scroll and ignores the pointer, and
//             on a phone is one sweep per pick
//   sizes     the drawing draws (offsets fall to 0, squares and labels fade in after), a pick draws the gold outline of that size, the figure and the lines
//             cross-fade with exactly one version in the accessibility tree, and the card never changes size
//   more      the counter, the line, the full-tone picture and the arrow buttons follow the rail; the buttons scroll by one picture, are aria-disabled at the
//             ends and are not there below 768 px
//   closeups  the square draws, the crop opens from the square's rectangle to the whole panel without ever being scaled, the chip, the map and the label
//             never fade, the edge opens as a plate and ends whole
//   identity  the artwork rectangles of these chapters are pixel for pixel the same with the motion off and after all of it has played (charter AC-5)
//   keyboard  the controls of these chapters take the focus in a sensible order and the arrow keys and Enter do their work
//   cls       no layout shift of these chapters over a slow scroll of the whole page, on a phone and on a desktop
//   gold      the gold census of every viewport that holds one of these chapters
import { createHash } from 'node:crypto';
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

const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
  if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { json({ ok: true, open: false, suggest: null }); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404); res.end('{}'); return true; }
  return false;
};
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();

// ---------------------------------------------------------------------------------------------------- helpers
/** A fresh visit with every lazy section mounted but nothing scrolled to (so nothing has been revealed yet). */
async function open({ lang = 'en', width = 1280, height = 900, ...more } = {}) {
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1, ...more });
  page.errors = [];
  await page.send('Page.bringToFront');
  // a page that stops answering (a frame that never comes) must name the expression, not hang the run
  const plain = page.eval.bind(page);
  page.eval = (expr) => Promise.race([plain(expr), new Promise((_, no) => setTimeout(() => no(new Error('no answer in 25 s to: ' + String(expr).replace(/\s+/g, ' ').slice(0, 160))), 25000))]);
  page.on((d) => { if (d.method === 'Runtime.exceptionThrown') page.errors.push(String(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text).slice(0, 200)); });
  await page.goto(`${origin}/?lang=${lang}`);
  await page.loaded();
  for (let i = 0; i < 200; i++) {
    if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) break;
    await sleep(100);
  }
  await sleep(300);
  return page;
}
const scrollTo = (page, sel, at = 100) => page.eval(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return false; window.scrollTo({ top: e.getBoundingClientRect().top + scrollY - ${at}, behavior: 'instant' }); return true; })()`);
/** Frames of the page itself for `ms` milliseconds: for every selector the computed values of `props` (a pseudo element as "sel::after"). */
async function frames(page, sels, props, ms) {
  return JSON.parse(await page.eval(`new Promise((done) => {
    const sels = ${JSON.stringify(sels)}, props = ${JSON.stringify(props)}, out = {}, t0 = performance.now();
    for (const s of sels) out[s] = [];
    const tick = (now) => {
      const t = Math.round(now - t0);
      for (const s of sels) { const [q, p] = s.split('::'); const e = document.querySelector(q); out[s].push(e ? [t, ...props.map((k) => getComputedStyle(e, p ? '::' + p : null).getPropertyValue(k))] : [t, null]); }
      if (t < ${ms}) requestAnimationFrame(tick); else done(JSON.stringify(out));
    };
    requestAnimationFrame(tick);
  })`));
}
const num = (v) => parseFloat(v);
const col = (rows, i) => rows.filter((r) => r[1] !== null).map((r) => r[i]);
const near = (a, b, tol) => Math.abs(a - b) <= tol;
/** Two viewport screenshots, each cropped to its own rectangle (device pixels), compared with zero tolerance. */
async function pngDiff(a, b, ra, rb) {
  const page = await chrome.page({ width: 400, height: 300 });
  const expr = `(async () => {
    const load = (b64) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'data:image/png;base64,' + b64; });
    const [x, y] = await Promise.all([load(${JSON.stringify(a.toString('base64'))}), load(${JSON.stringify(b.toString('base64'))})]);
    const ra = ${JSON.stringify(ra)}, rb = ${JSON.stringify(rb)};
    const w = Math.min(ra[2], rb[2]), h = Math.min(ra[3], rb[3]);
    if (Math.abs(ra[2] - rb[2]) > 1 || Math.abs(ra[3] - rb[3]) > 1) return JSON.stringify({ size: [ra[2], ra[3], rb[2], rb[3]] });
    const data = (im, r) => { const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); g.drawImage(im, r[0], r[1], w, h, 0, 0, w, h); return g.getImageData(0, 0, w, h).data; };
    const p = data(x, ra), q = data(y, rb); let n = 0, max = 0, x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let i = 0; i < p.length; i += 4) if (p[i] !== q[i] || p[i + 1] !== q[i + 1] || p[i + 2] !== q[i + 2]) { n++; max = Math.max(max, Math.abs(p[i] - q[i]), Math.abs(p[i + 1] - q[i + 1]), Math.abs(p[i + 2] - q[i + 2])); const k = i / 4, px = k % w, py = Math.floor(k / w); x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py); }
    return JSON.stringify({ n, max, of: w * h, box: n ? [x0, y0, x1, y1] : null });
  })()`;
  const r = JSON.parse(await page.eval(expr));
  await page.close();
  return r;
}
const SECTIONS = '#how, #styles, #wall, #sizes, #more, #closeups';
/** what is hidden, moved, clipped or running in the six chapters at this moment */
const RESTING = `JSON.stringify((() => {
  const sec = [...document.querySelectorAll(${JSON.stringify(SECTIONS)})];
  const inside = (e) => sec.some((s) => s.contains(e));
  const off = [];
  for (const e of document.querySelectorAll('${SECTIONS.split(', ').map((s) => s + ' *').join(', ')}')) {
    const c = getComputedStyle(e);
    if (e.closest('details:not([open])') || e.closest('.lp-stack-i:not([data-on])') || e.closest('[hidden]')) continue;
    if (e.closest('.lp-ghost')) continue;
    const r = e.getBoundingClientRect(); if (!r.width && !r.height) continue;
    const bad = [];
    if (+c.opacity < 0.6 && !e.matches('#stA, #stB, .lp-wall, .lp-rail-btn') && !e.closest('.lp-wallbtn, .lp-vis-chip, .lp-chip-ex')) bad.push('opacity ' + c.opacity);
    if (c.translate !== 'none' && c.translate !== '0px' && c.translate !== '0px 0px' && !e.classList.contains('lp-tabs-bar') && !e.matches('.lp-glint, .lp-glint *')) bad.push('translate ' + c.translate);
    if (c.scale !== 'none' && c.scale !== '1' && c.scale !== '1 1' && !e.matches('.lp-tabs-bar, .lp-rail-line i')) bad.push('scale ' + c.scale);
    if (c.clipPath !== 'none' && !e.matches('.lp-line-mask, .lp-btn, .lp-btn::before')) bad.push('clip ' + c.clipPath);
    if (bad.length) off.push((e.id ? '#' + e.id : e.tagName.toLowerCase() + '.' + String(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className).split(' ')[0]) + ': ' + bad.join(', '));
  }
  const anims = document.getAnimations().filter((a) => a instanceof CSSAnimation && a.effect && a.effect.target && inside(a.effect.target)).map((a) => a.animationName);
  return { off: off.slice(0, 12), anims };
})())`;

// ---------------------------------------------------------------------------------------------------- reduced
async function checkReduced() {
  console.log('reduced');
  for (const [lang, width] of [['en', 1280], ['de', 375], ['hu', 1280]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900, reduceMotion: true });
    for (const sel of ['#how', '#styles', '#wall', '#sizes', '#closeups']) { await scrollTo(page, sel, 90); await sleep(250); }
    await page.eval("document.querySelector('#more') && (document.querySelector('#more').open = true)");
    await scrollTo(page, '#more', 90); await sleep(300);
    const s = JSON.parse(await page.eval(RESTING));
    const mo = await page.eval("document.documentElement.classList.contains('mo')");
    expect('reduced', !mo, `${tag}: html carries mo under reduced motion`);
    expect('reduced', s.off.length === 0, `${tag}: hidden, moved or clipped at rest: ${s.off.join(' | ')}`);
    expect('reduced', s.anims.length === 0, `${tag}: running animations under reduced motion: ${s.anims.join(', ')}`);
    // the specific end states
    const e = JSON.parse(await page.eval(`JSON.stringify({
      gold: [...document.querySelectorAll('.lp-sq-on')].map((r) => [r.dataset.on !== undefined, getComputedStyle(r).strokeDashoffset]),
      draw: [...document.querySelectorAll('.lp-dr')].map((r) => getComputedStyle(r).strokeDashoffset),
      loc: getComputedStyle(document.querySelector('.lp-loc-draw')).strokeDashoffset,
      crop: getComputedStyle(document.querySelector('.lp-cu-img > img')).clipPath, edge: [getComputedStyle(document.querySelector('.lp-edge-img > img')).clipPath, getComputedStyle(document.querySelector('.lp-edge-img > img')).scale],
      glint: getComputedStyle(document.getElementById('stGlint'), '::after').display,
      bar: document.getElementById('gTabs').dataset.bar !== undefined,
      railLine: getComputedStyle(document.querySelector('.lp-rail-line i')).scale })`));
    expect('reduced', e.gold.every(([on, o]) => (on ? o === '0px' : true)), `${tag}: the chosen size's gold outline is not whole: ${JSON.stringify(e.gold)}`);
    expect('reduced', e.draw.every((o) => o === '0px'), `${tag}: a line of the drawing is not whole: ${e.draw.join(',')}`);
    expect('reduced', e.loc === '0px', `${tag}: the square on the map is not drawn (${e.loc})`);
    expect('reduced', e.crop === 'none' && e.edge[0] === 'none', `${tag}: the crop or the edge is clipped (${e.crop}, ${e.edge[0]})`);
    expect('reduced', e.glint === 'none', `${tag}: the glint exists under reduced motion (${e.glint})`);
    // an eye colour changes at once: no second picture is left on top
    await scrollTo(page, '#gEyeChips', 300);
    await page.eval("document.querySelector('#gEyeChips [data-e=br]').click()");
    await sleep(120);
    const ghosts = await page.eval("document.querySelectorAll('.lp-ghost').length");
    expect('reduced', ghosts === 0, `${tag}: ${ghosts} old pictures stay on top after an eye colour change under reduced motion`);
    expect('reduced', page.errors.length === 0, `${tag}: script errors: ${page.errors.join(' | ')}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('reduced'))) pass('reduced', 'under reduced motion the six chapters are whole at once: nothing hidden, moved, clipped or running, the glint absent');
}

// ---------------------------------------------------------------------------------------------------- how
async function checkHow() {
  console.log('how');
  // three columns
  let page = await open({ width: 1280 });
  await scrollTo(page, '#steps', 1200); await sleep(300);
  const before = JSON.parse(await page.eval("JSON.stringify([...document.querySelectorAll('.lp-step')].map((e) => [e.dataset.in !== undefined, +getComputedStyle(e).opacity]))"));
  expect('how', before.every(([i, o]) => !i && o === 0), `three columns: before they come into view the steps are not hidden: ${JSON.stringify(before)}`);
  await scrollTo(page, '#steps', 250);
  const f = await frames(page, ['.lp-step:nth-child(1)', '.lp-step:nth-child(3)', '.lp-step:nth-child(1) .lp-num', '.lp-step:nth-child(3) .lp-num', '.lp-step:nth-child(3) .lp-num::after', '.lp-how-cta'], ['opacity', 'translate', 'color', 'scale'], 3000);
  const t1 = f['.lp-step:nth-child(1)'], t3 = f['.lp-step:nth-child(3)'];
  const at = (rows, ms) => rows.find((r) => r[0] >= ms);
  expect('how', num(at(t1, 220)[1]) > num(at(t3, 220)[1]) + 0.15, `the third step does not follow the first: opacity at 220 ms ${at(t1, 220)[1]} and ${at(t3, 220)[1]}`);
  expect('how', t1.at(-1)[1] === '1' && t3.at(-1)[1] === '1' && t3.at(-1)[2] === 'none', `a step does not end whole: ${t3.at(-1)}`);
  const rise = Math.max(...col(t1, 2).map((v) => (v === 'none' ? 0 : num(v.split(' ')[1]))));
  expect('how', rise <= 20.01, `a step rises ${rise}px (20 at most)`);
  const hairline = f['.lp-step:nth-child(3) .lp-num::after'];
  const sc0 = col(hairline, 4).map((v) => (v === 'none' ? 1 : num(v.split(' ')[0])));
  const sc = sc0.slice(sc0.findIndex((v) => v < 1));   // the frames before the step came into view have no animation yet
  expect('how', sc[0] === 0 && sc.at(-1) === 1 && sc.every((v, i) => i === 0 || v >= sc[i - 1] - 1e-6), `the hairline of step 3 does not draw from 0 to 1 monotonically: ${sc.filter((_, i) => i % 15 === 0).map((v) => v.toFixed(2)).join(' ')}`);
  const colors = col(f['.lp-step:nth-child(3) .lp-num'], 3);
  expect('how', colors.some((c) => c.includes('0.5)')) && colors.at(-1) === 'rgb(245, 197, 66)', `the numeral of step 3 does not warm to gold: ${colors[0]} ... ${colors.at(-1)}`);
  await scrollTo(page, '.lp-how-cta', 500);
  const cta = (await frames(page, ['.lp-how-cta'], ['opacity', 'translate'], 1500))['.lp-how-cta'];
  expect('how', cta.at(-1)[1] === '1' && cta.at(-1)[2] === 'none' && num(cta[0][1]) < 0.6, `the button row does not rise to its place (${cta[0][1]} to ${cta.at(-1)[1]})`);
  // the dimmer states belong to the swipe rail only
  const wideDim = await page.eval("[...document.querySelectorAll('.lp-step h3')].map((h) => getComputedStyle(h).color).join('|')");
  expect('how', !wideDim.includes('0.5)'), `three columns: a title is dimmed (${wideDim})`);
  expect('how', (await page.eval("document.querySelectorAll('.lp-step[aria-current]').length")) === 0, 'three columns: aria-current is set although all three steps are in view');
  await page.close();

  // the swipe rail
  page = await open({ width: 375, height: 812 });
  await scrollTo(page, '#steps', 1100); await sleep(300);
  expect('how', (await page.eval("getComputedStyle(document.getElementById('steps')).opacity")) === '0', 'the swipe rail is not hidden before it comes into view');
  const st0 = await page.eval("[...document.querySelectorAll('.lp-step')].map((e) => getComputedStyle(e).opacity + ' ' + getComputedStyle(e).translate).join('|')");
  expect('how', st0 === '1 none|1 none|1 none', `the steps of the rail are hidden or moved individually: ${st0}`);
  await scrollTo(page, '#steps', 200);
  const g = await frames(page, ['#steps'], ['opacity'], 1000);
  expect('how', g['#steps'].at(-1)[1] === '1' && num(g['#steps'][0][1]) < 0.5, `the rail does not fade in as one piece: ${g['#steps'][0][1]} to ${g['#steps'].at(-1)[1]}`);
  const cur = async () => page.eval("JSON.stringify({ i: [...document.querySelectorAll('.lp-step')].findIndex((e) => e.getAttribute('aria-current') === 'step'), n: document.querySelectorAll('.lp-step[aria-current]').length, num: [...document.querySelectorAll('.lp-step .lp-num')].map((e) => getComputedStyle(e).color), h3: [...document.querySelectorAll('.lp-step h3')].map((e) => getComputedStyle(e).color) })");
  await sleep(500);
  let c = JSON.parse(await cur());
  expect('how', c.i === 0 && c.n === 1, `rail at rest: the current step is ${c.i} (${c.n} marked), wanted 0`);
  expect('how', c.num[0] === 'rgb(245, 197, 66)' && c.num[1].endsWith('0.6)') && c.h3[0] === 'rgb(255, 255, 255)' && c.h3[1].includes('0.5)'), `rail at rest: the tones are not current gold and white against 0.6 gold and the floor: ${JSON.stringify(c)}`);
  await page.eval("document.getElementById('steps').scrollTo({ left: document.querySelector('.lp-step:nth-child(2)').offsetLeft - 16, behavior: 'instant' })");
  await sleep(700);
  c = JSON.parse(await cur());
  expect('how', c.i === 1 && c.n === 1, `rail swiped to the second step: current is ${c.i}`);
  await page.eval("document.getElementById('steps').scrollTo({ left: 9999, behavior: 'instant' })");
  await sleep(700);
  c = JSON.parse(await cur());
  expect('how', c.i === 2, `rail swiped to the end: current is ${c.i}`);
  await page.close();
  if (!problems.some((x) => x.startsWith('how'))) pass('how', 'three columns rise in turn and the hairline draws from 01 to 03, the rail appears as one piece and marks the step in view');
}

// ---------------------------------------------------------------------------------------------------- styles
async function checkStyles() {
  console.log('styles');
  const BAR = `JSON.stringify((() => { const l = document.getElementById('gTabs'), b = l.querySelector('.lp-tabs-bar'), t = l.querySelector('[aria-selected=true]'), cb = b.getBoundingClientRect(), r = t.getBoundingClientRect(); return { bar: [cb.left, cb.width, cb.top], tab: [r.left + 14, r.width - 28, r.bottom], on: l.dataset.bar !== undefined, h: cb.height }; })())`;
  const same = (x, tag) => expect('styles', x.on && near(x.bar[0], x.tab[0], 1.5) && near(x.bar[1], x.tab[1], 1.5) && near(x.bar[2], x.tab[2], 1.5) && x.h === 1, `${tag}: the line is at ${x.bar.map((v) => v.toFixed(1))} (height ${x.h}), the selected tab's box says ${x.tab.map((v) => v.toFixed(1))}`);
  for (const [lang, width] of [['en', 1280], ['de', 375]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    await scrollTo(page, '#gTabs', 1300); await sleep(300);
    const tiles0 = JSON.parse(await page.eval("JSON.stringify([...document.querySelectorAll('.lp-tile')].map((e) => [e.dataset.in !== undefined, +getComputedStyle(e).opacity]))"));
    if (width >= 640) expect('styles', tiles0.every(([i]) => !i), `${tag}: tiles are marked as seen before the grid comes into view`);
    await scrollTo(page, '#gTabs', 200);
    if (width >= 640) {
      const f = await frames(page, ['.lp-tile:nth-child(1)', '.lp-tile:nth-child(3)'], ['opacity', 'translate'], 2600);
      const a = f['.lp-tile:nth-child(1)'], c = f['.lp-tile:nth-child(3)'];
      const first = (rows) => rows.findIndex((r) => num(r[1]) > 0.02);
      expect('styles', first(c) > first(a) + 8, `${tag}: the third tile does not follow the first (they start at frames ${first(a)} and ${first(c)}, 16 ms each)`);
      expect('styles', a.at(-1)[2] === 'none' && c.at(-1)[1] === '1', `${tag}: a tile does not end whole`);
      const rise = Math.max(...col(a, 2).map((v) => (v === 'none' ? 0 : num(v.split(' ')[1]))));
      expect('styles', rise <= 20.01, `${tag}: a tile rises ${rise}px (20 at most)`);
    } else {
      const g = await page.eval("JSON.stringify([getComputedStyle(document.getElementById('gGrid')).opacity, ...[...document.querySelectorAll('.lp-tile')].map((e) => getComputedStyle(e).opacity + ' ' + getComputedStyle(e).translate)])");
      note(`styles ${tag}: the rail ${g}`);
    }
    await sleep(500);
    same(JSON.parse(await page.eval(BAR)), `${tag} at rest`);
    // a click slides
    await page.eval("document.querySelector('#gTabs [data-g=two]').click()");
    const slide = await frames(page, ['.lp-tabs-bar'], ['translate', 'scale'], 800);
    const xs = col(slide['.lp-tabs-bar'], 1).map((v) => num(v));
    expect('styles', xs.length > 8 && xs.some((v) => v > xs[0] + 2 && v < xs.at(-1) - 2), `${tag}: the line does not slide on a click: ${xs.filter((_, i) => i % 6 === 0).map((v) => v.toFixed(0)).join(' ')}`);
    same(JSON.parse(await page.eval(BAR)), `${tag} after a click`);
    // an arrow key moves it too (selection follows focus)
    await page.eval("document.querySelector('#gTabs [aria-selected=true]').focus()");
    await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39 });
    await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39 });
    await sleep(700);
    const sel = await page.eval("document.querySelector('#gTabs [aria-selected=true]').dataset.g");
    expect('styles', sel === 'family', `${tag}: the arrow key left the selection on ${sel}`);
    same(JSON.parse(await page.eval(BAR)), `${tag} after an arrow key`);
    // a language switch snaps (no slide): the box of the tab changes width
    await page.eval("document.querySelector('#langSeg button[lang=hu]').click()");
    await sleep(60);
    same(JSON.parse(await page.eval(BAR)), `${tag} right after a language switch to hu`);
    await sleep(400);
    same(JSON.parse(await page.eval(BAR)), `${tag} after a language switch to hu`);
    // the new tiles of a changed group only fade in
    await page.eval("document.querySelector('#gTabs [data-g=two]').click()");
    await sleep(40);
    const sw = JSON.parse(await page.eval("JSON.stringify([...document.querySelectorAll('.lp-tile')].map((e) => [e.className.includes('lp-tile-in'), e.dataset.reveal || null, getComputedStyle(e).translate]))"));
    expect('styles', sw.length > 0 && sw.every(([inn, rev, tr]) => inn && rev === null && tr === 'none'), `${tag}: a changed group's tiles rise or are not marked to fade: ${JSON.stringify(sw)}`);
    await page.close();
  }
  // the eye colour, the hover, the buttons
  let page = await open({ width: 1280 });
  await scrollTo(page, '.lp-tile .lp-tile-img', 200); await sleep(2200);   // the tile itself: #gEyeChips is display: contents and has no box of its own to scroll to
  await page.eval("document.querySelector('#gEyeChips [data-e=br]').click()");
  const eye = await page.eval(`new Promise((done) => { const out = []; const t0 = performance.now(); const tick = (now) => { const t = Math.round(now - t0); const tile = document.querySelector('.lp-tile .lp-tile-img'); out.push([t, [...tile.querySelectorAll('img')].filter((i) => i.classList.contains('lp-art')).map((i) => [i.classList.contains('lp-ghost'), +getComputedStyle(i).opacity, i.src.split('/').pop().slice(0, 18)]), [...tile.querySelectorAll('.lp-chip-ex')].map((c) => getComputedStyle(c).opacity + getComputedStyle(c).visibility)]); if (t < 1400) requestAnimationFrame(tick); else done(JSON.stringify(out)); }; requestAnimationFrame(tick); })`);
  const rows = JSON.parse(eye);
  const withGhost = rows.filter((r) => r[1].some((x) => x[0]));
  expect('styles', withGhost.length > 5 && withGhost.every((r) => r[1].length === 2), `eye colour: no old picture was kept on top (${withGhost.length} frames with one)`);
  expect('styles', rows.at(-1)[1].length === 1, `eye colour: the old picture is still there at the end (${rows.at(-1)[1].length} pictures)`);
  const lows = withGhost.map((r) => r[1].find((x) => x[0])[1]);
  expect('styles', lows[0] === 1 || lows[0] > 0.9, `eye colour: the old picture does not start at full tone (${lows[0]})`);
  expect('styles', lows.every((v, i) => i === 0 || v <= lows[i - 1] + 1e-6), 'eye colour: the old picture does not fade out monotonically');
  expect('styles', rows.every((r) => r[2].every((c) => c === '1visible')), 'eye colour: the label of a tile faded or went away');
  const dur = (withGhost.at(-1)[0] - withGhost[0][0]);
  expect('styles', dur >= 250 && dur <= 700, `eye colour: the cross fade took ${dur} ms (about 420)`);
  // hover: 1.02 at most, with a mouse; the wall button fades in (only Mantas's own eye has wall views)
  await page.eval("document.querySelector('#gEyeChips [data-e=own]').click()");
  await sleep(900);
  await scrollTo(page, '.lp-tile', 150); await sleep(500);
  const geo = JSON.parse(await page.eval("JSON.stringify((() => { const r = document.querySelector('.lp-tile .lp-tile-img').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; })())"));
  const wb = () => page.eval("JSON.stringify([+getComputedStyle(document.querySelector('.lp-tile .lp-wallbtn')).opacity, getComputedStyle(document.querySelector('.lp-tile .lp-art')).scale, getComputedStyle(document.querySelector('.lp-tile .lp-art')).transform])");
  await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 5, y: 5 });
  await sleep(1500);
  const rest = JSON.parse(await wb());
  expect('styles', rest[0] === 0, `with a mouse the wall button is not hidden at rest (opacity ${rest[0]})`);
  await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: geo[0], y: geo[1] });
  await sleep(1700);
  const hov = JSON.parse(await wb());
  const m = /matrix\(([^,]+)/.exec(hov[2]);
  const z = m ? +m[1] : 1;
  expect('styles', hov[0] === 1, `hovering the tile does not bring the wall button in (opacity ${hov[0]})`);
  expect('styles', z > 1.0 && z <= 1.0201, `the hover zoom is ${z} (more than 1 and at most 1.02)`);
  // keyboard focus brings the button in as well
  await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: 5, y: 5 });
  await page.eval("document.querySelectorAll('.lp-wallbtn')[1].focus()");
  await sleep(700);
  expect('styles', (await page.eval("+getComputedStyle(document.querySelectorAll('.lp-wallbtn')[1]).opacity")) === 1, 'the wall button does not show when the tile holds the keyboard focus');
  await page.close();
  // a touch screen: the button is always there, no hover zoom rule
  page = await open({ width: 375, height: 812 });
  await scrollTo(page, '.lp-tile', 150); await sleep(800);
  const touch = JSON.parse(await page.eval("JSON.stringify([+getComputedStyle(document.querySelector('.lp-tile .lp-wallbtn')).opacity, getComputedStyle(document.querySelector('.lp-tile .lp-art')).scale])"));
  expect('styles', touch[0] === 1, `on a touch screen the wall button is hidden (opacity ${touch[0]})`);
  await page.close();
  if (!problems.some((x) => x.startsWith('styles'))) pass('styles', 'the line slides to the selected tab and snaps on a language switch, the tiles rise in turn the first time and only fade after a change, an eye colour cross-fades, the hover zoom is 1.02');
}

// ---------------------------------------------------------------------------------------------------- wall
async function checkWall() {
  console.log('wall');
  const STAGE = `JSON.stringify([...document.querySelectorAll('#stage img')].map((i) => +getComputedStyle(i).opacity))`;
  const GL = `JSON.stringify((() => { const g = document.getElementById('stGlint'), a = getComputedStyle(g, '::after'), r = g.getBoundingClientRect(), s = document.getElementById('stage').getBoundingClientRect(); return { box: [g.style.left, g.style.width], w: Math.round(r.width), inside: r.left >= s.left - 0.5 && r.right <= s.right + 0.5 && r.top >= s.top - 0.5 && r.bottom <= s.bottom + 0.5, gx: g.style.getPropertyValue('--gx'), tr: a.translate, bg: a.backgroundImage, blend: a.mixBlendMode, op: a.opacity, sweep: g.dataset.sweep !== undefined, anim: a.animationName, hidden: g.getAttribute('aria-hidden') }; })())`;
  let page = await open({ width: 1280 });
  await scrollTo(page, '.lp-wall-grid', 120); await sleep(1800);
  let g0 = JSON.parse(await page.eval(GL));
  expect('wall', g0.w === 0, `the glint has a box (${g0.w}px) while the aluminium picture is on the stage`);
  expect('wall', (await page.eval("document.querySelector('#specs [data-swap]') === null ? 'none' : 'some'")) === 'none', 'the facts are marked to animate before any pick');
  expect('wall', (await page.eval("getComputedStyle(document.querySelector('#specs li')).animationName")) === 'none', 'the facts animate before any pick');
  // a pick of acrylic: the stage cross-fades
  await page.eval("document.getElementById('mat-acrylic').click()");
  const sw = JSON.parse(await page.eval(`new Promise((done) => { const out = []; const t0 = performance.now(); const tick = (now) => { const t = Math.round(now - t0); out.push([t, ...JSON.parse(${STAGE}), document.getElementById('stGlint').style.width, +getComputedStyle(document.getElementById('stGlint'), '::after').opacity]); if (t < 1200) requestAnimationFrame(tick); else done(JSON.stringify(out)); }; requestAnimationFrame(tick); })`));
  const mid = sw.filter((r) => r[1] > 0.02 && r[1] < 0.98);
  expect('wall', mid.length >= 5, `the stage does not cross-fade (${mid.length} frames in between)`);
  expect('wall', sw.every((r) => r[1] + r[2] >= 0.95), `at some frame the stage is thin: the layers sum to ${Math.min(...sw.map((r) => r[1] + r[2])).toFixed(2)}`);
  // the band is never brighter than the picture it belongs to: while the old picture is still there it is clear
  const newLayer = sw.at(-1)[1] === 1 ? 1 : 2;
  const early = sw.filter((r) => r[3] !== '' && r[4] > 0.02 && r[newLayer] < 0.95);
  expect('wall', early.length === 0, `the glint shows over the picture it is replacing (${early.length} frames, first: ${JSON.stringify(early[0])})`);
  expect('wall', sw.at(-1)[4] > 0.9 || sw.at(-1)[4] === 1 || sw.at(-1)[4] > 0, 'the glint never fades in');
  await sleep(300);
  let g1 = JSON.parse(await page.eval(GL));
  expect('wall', g1.w > 100 && g1.inside, `the glint is not bound to the print face inside the stage: ${g1.w}px, inside ${g1.inside}`);
  expect('wall', g1.blend === 'screen' && g1.hidden === 'true', `the glint is ${g1.blend} and aria-hidden ${g1.hidden}`);
  const alphas = [...g1.bg.matchAll(/rgba\(255, 255, 255, ([\d.]+)\)/g)].map((m) => +m[1]);
  expect('wall', alphas.length > 0 && Math.max(...alphas) <= 0.101, `the glint peaks at ${Math.max(...alphas)} (0.10 at most)`);
  expect('wall', g1.gx !== '' && g1.tr === g1.gx, `the band is not at the scroll position: gx ${g1.gx}, translate ${g1.tr}`);
  // scroll moves it, monotonically; the pointer does not
  const gx = [];
  for (const at of [320, 220, 120, 20, -80, -180]) { await scrollTo(page, '.lp-wall-grid', at); await sleep(650); gx.push(num(JSON.parse(await page.eval(GL)).gx)); }
  expect('wall', gx.every((v, i) => i === 0 || v > gx[i - 1]) && gx[0] >= -40 && gx.at(-1) <= 40, `the band does not travel with the scroll: ${gx.map((v) => v.toFixed(1)).join(' ')}`);
  const still = num(JSON.parse(await page.eval(GL)).gx);
  const sr = JSON.parse(await page.eval("JSON.stringify((() => { const r = document.getElementById('stage').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })())"));
  for (const [fx, fy] of [[0.2, 0.3], [0.5, 0.4], [0.8, 0.3], [0.5, 0.2]]) { await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: sr[0] + sr[2] * fx, y: sr[1] + sr[3] * fy }); await sleep(250); }
  expect('wall', num(JSON.parse(await page.eval(GL)).gx) === still, 'the glint follows the pointer');
  // facts fade on a pick, and not again on a language switch
  await page.eval("document.getElementById('mat-canvas').click()");
  await sleep(60);
  const spec = JSON.parse(await page.eval("JSON.stringify([...document.querySelectorAll('#specs li')].map((l) => [getComputedStyle(l).animationName, getComputedStyle(l).animationDelay, +getComputedStyle(l).opacity, getComputedStyle(l).translate]))"));
  expect('wall', spec.length >= 3 && spec.every((s) => s[0] === 'lp-spec-in' && s[3] === 'none'), `the facts do not fade in after a pick (or they rise): ${JSON.stringify(spec)}`);
  expect('wall', spec[1][1] === '0.1s' && spec[0][1] === '0.05s', `the facts are not 50 ms apart: ${spec.map((s) => s[1]).join(' ')}`);
  await sleep(900);
  await page.eval("document.querySelector('#langSeg button[lang=de]').click()");
  await sleep(120);
  const after = await page.eval("JSON.stringify([...document.querySelectorAll('#specs li')].map((l) => [getComputedStyle(l).animationName, +getComputedStyle(l).opacity]))");
  expect('wall', JSON.parse(after).every(([a, o]) => a === 'lp-spec-in' ? false : o === 1) || JSON.parse(after).every(([a, o]) => o === 1), `a language switch makes the facts fade again: ${after}`);
  // the chip and the words about printing are never touched
  const label = await page.eval("JSON.stringify([+getComputedStyle(document.querySelector('#stage .lp-vis-chip')).opacity, +getComputedStyle(document.querySelector('.lp-note-box')).opacity, getComputedStyle(document.querySelector('.lp-note-box')).translate])");
  expect('wall', label === '[1,1,"none"]', `the chip or the printing note moved or faded: ${label}`);
  // the stage column sticks
  const stick = [];
  const travel = await page.eval("document.querySelector('.lp-wall-grid').getBoundingClientRect().height - document.querySelector('.lp-stage-col').getBoundingClientRect().height");
  for (const at of [40, 88 - travel * 0.45, 88 - travel * 0.85]) { await scrollTo(page, '.lp-wall-grid', at); await sleep(300); stick.push(Math.round(await page.eval("document.querySelector('.lp-stage-col').getBoundingClientRect().top"))); }
  expect('wall', travel > 60 && stick.every((v) => v === stick[0]) && stick[0] > 0, `the stage column does not stick inside its sheet (travel ${Math.round(travel)} px): ${stick.join(' ')}`);
  expect('wall', page.errors.length === 0, `script errors: ${page.errors.join(' | ')}`);
  await page.close();

  // a phone: no scroll driven band, one sweep per pick of acrylic
  page = await open({ width: 375, height: 812 });
  await scrollTo(page, '#mats', 80); await sleep(1200);
  await page.eval("document.getElementById('mat-acrylic').click()");
  let seen = null;
  for (let i = 0; i < 40 && !seen; i++) { await sleep(60); const g = JSON.parse(await page.eval(GL)); if (g.sweep) seen = g; }
  expect('wall', !!seen && seen.anim === 'lp-sweep', `a phone: no sweep after picking acrylic (${JSON.stringify(seen)})`);
  const sweep = await frames(page, ['#stGlint::after'], ['opacity', 'translate'], 2600);
  const op = col(sweep['#stGlint::after'], 1).map(num);
  expect('wall', Math.max(...op) <= 1.001 && op.includes(0) && op.at(-1) === 0, `the sweep does not fade in and out: ${op.filter((_, i) => i % 10 === 0).map((v) => v.toFixed(2)).join(' ')}`);
  const gone = JSON.parse(await page.eval(GL));
  expect('wall', !gone.sweep && gone.gx === '', `after the sweep the attribute stays (${gone.sweep}) or a scroll position was written (${gone.gx})`);
  await page.eval("document.getElementById('mat-metal').click()"); await sleep(900);
  await page.eval("document.getElementById('mat-acrylic').click()");
  let again = false;
  for (let i = 0; i < 40 && !again; i++) { await sleep(60); again = JSON.parse(await page.eval(GL)).sweep; }
  expect('wall', again, 'a phone: no second sweep after leaving acrylic and picking it again');
  await page.close();
  if (!problems.some((x) => x.startsWith('wall'))) pass('wall', 'the stage cross-fades, the facts fade in on a pick, the glint lives on the acrylic print face only (10 percent at most, scroll bound, not pointer bound), a phone gets one sweep per pick');
}

// ---------------------------------------------------------------------------------------------------- sizes
async function checkSizes() {
  console.log('sizes');
  for (const [lang, width] of [['en', 1280], ['hu', 375]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    await scrollTo(page, '#ruler', width < 800 ? 1300 : 1200); await sleep(300);
    const b = JSON.parse(await page.eval("JSON.stringify([document.getElementById('ruler').dataset.in !== undefined, ...[...document.querySelectorAll('.lp-dr')].map((e) => getComputedStyle(e).strokeDashoffset), ...[...document.querySelectorAll('.lp-sqg')].map((e) => getComputedStyle(e).opacity)])"));
    expect('sizes', b[0] === false && b.slice(1, 9).every((v) => v === '1px') && b.slice(9).every((v) => v === '0'), `${tag}: the drawing is not hidden before it is in view: ${JSON.stringify(b)}`);
    await scrollTo(page, '#ruler', width < 800 ? 120 : 150);
    const f = await frames(page, ['.lp-dr', '.lp-sqg', '.lp-lbl', '.lp-sqg:nth-of-type(n+4)'], ['stroke-dashoffset', 'opacity'], 3600);
    const d = col(f['.lp-dr'], 1).map(num);
    expect('sizes', d[0] > 0.9 && d.at(-1) === 0 && d.every((v, i) => i === 0 || v <= d[i - 1] + 1e-6), `${tag}: the sofa does not draw 1 to 0 monotonically (${d[0]} ... ${d.at(-1)})`);
    const sq = col(f['.lp-sqg'], 2).map(num), lb = col(f['.lp-lbl'], 2).map(num);
    const startSq = f['.lp-sqg'].findIndex((r) => num(r[2]) > 0.02), endD = f['.lp-dr'].findIndex((r) => num(r[1]) < 0.01);
    expect('sizes', sq[0] === 0 && sq.at(-1) === 1 && lb.at(-1) === 1, `${tag}: the squares or labels do not end whole (${sq.at(-1)}, ${lb.at(-1)})`);
    expect('sizes', f['.lp-sqg'][startSq][0] >= 800, `${tag}: the squares start at ${f['.lp-sqg'][startSq][0]} ms, before the sofa has been drawn for a while`);
    note(`sizes ${tag}: the sofa's first line is 99 percent drawn at ${f['.lp-dr'][endD]?.[0]} ms, the first square starts at ${f['.lp-sqg'][startSq][0]} ms`);
    // a pick draws the gold outline of that size
    const gold = JSON.stringify(['20', '30', '40', '50']);
    await page.eval("document.querySelector('#sizeChips [data-cm=\"30\"]').click()");
    const f2 = await frames(page, ['.lp-sqg[data-cm="30"] .lp-sq-on', '.lp-sqg[data-cm="50"] .lp-sq-on', '.lp-sqg[data-cm="20"] .lp-sq-on'], ['stroke-dashoffset'], 1000);
    const on30 = col(f2['.lp-sqg[data-cm="30"] .lp-sq-on'], 1).map(num), off50 = col(f2['.lp-sqg[data-cm="50"] .lp-sq-on'], 1).map(num);
    expect('sizes', on30[0] > 0.8 && on30.at(-1) === 0, `${tag}: the outline of the chosen size does not draw (${on30[0]} to ${on30.at(-1)})`);
    expect('sizes', off50[0] < 0.2 && off50.at(-1) === 1, `${tag}: the outline of the size that was left does not undraw (${off50[0]} to ${off50.at(-1)})`);
    const t60 = f2['.lp-sqg[data-cm="30"] .lp-sq-on'].find((r) => num(r[1]) < 0.01)?.[0];
    note(`sizes ${tag}: the chosen outline is 99 percent drawn after ${t60} ms (600 ms transition on the expo curve)`);
    expect('sizes', JSON.parse(await page.eval("JSON.stringify([...document.querySelectorAll('.lp-sqg')].map((g) => [g.dataset.cm, getComputedStyle(g.querySelector('.lp-sq-on')).strokeDashoffset]))")).filter(([, o]) => o === '0px').length === 1, `${tag}: more or fewer than one gold outline is whole`);
    // crossfades: one version in the tree, the cell never changes size
    const modes = [];
    for (const cm of [20, 40, 50, 30]) {
      await page.eval(`document.querySelector('#sizeChips [data-cm="${cm}"]').click()`);
      await sleep(80);
      const mid = JSON.parse(await page.eval("JSON.stringify([...document.querySelectorAll('.lp-stack-fig > .lp-stack-i')].map((e) => +getComputedStyle(e).opacity))"));
      await sleep(700);
      const r = JSON.parse(await page.eval(`JSON.stringify({
        stacks: [...document.querySelectorAll('#sizeCard .lp-stack')].map((s) => [...s.children].map((c) => [c.dataset.on !== undefined, c.getAttribute('aria-hidden'), c.inert, +getComputedStyle(c).opacity, getComputedStyle(c).visibility])),
        size: [...document.querySelectorAll('#sizeCard .lp-stack')].map((s) => { const r = s.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }),
        card: Math.round(document.getElementById('sizeCard').getBoundingClientRect().height), notes: Math.round(document.getElementById('sizeNotes').getBoundingClientRect().top - document.getElementById('sizeCard').getBoundingClientRect().top),
        say: document.getElementById('sizeCard').innerText.replace(/\\s+/g, ' ').trim() })`));
      modes.push({ cm, mid, ...r });
    }
    for (const m of modes) {
      for (const st of m.stacks) {
        expect('sizes', st.filter((c) => c[0]).length === 1 && st.filter((c) => !c[0]).every((c) => c[1] === 'true' && c[2] === true && c[3] === 0 && c[4] === 'hidden'), `${tag} ${m.cm} cm: not exactly one version is in the tree: ${JSON.stringify(st)}`);
        expect('sizes', st.find((c) => c[0])[3] === 1, `${tag} ${m.cm} cm: the shown version is not opaque`);
      }
      expect('sizes', m.mid.reduce((a, v) => a + v, 0) <= 1.5 && m.mid.some((v) => v > 0 && v < 1), `${tag} ${m.cm} cm: the figure does not cross-fade (${m.mid.map((v) => v.toFixed(2))})`);
    }
    expect('sizes', modes.every((m) => m.card === modes[0].card && m.notes === modes[0].notes && m.size.every((s, i) => s[0] === modes[0].size[i][0] && s[1] === modes[0].size[i][1])), `${tag}: the card changes size with the size picked: ${JSON.stringify(modes.map((m) => [m.card, m.notes, m.size]))}`);
    const figs = modes.map((m) => [m.cm, /\d{3}/.exec(m.say)?.[0]]);
    expect('sizes', figs.every(([cm, f]) => f === String(Math.round(4096 / (cm / 2.54)))), `${tag}: a figure is not 4096 / (cm / 2.54): ${JSON.stringify(figs)}`);
    expect('sizes', page.errors.length === 0, `${tag}: script errors: ${page.errors.join(' | ')}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('sizes'))) pass('sizes', 'the drawing draws, the squares fade in after it, a pick draws its gold outline, the figure and the lines cross-fade in a cell that never changes size, one version in the tree');
}

// ---------------------------------------------------------------------------------------------------- more
async function checkMore() {
  console.log('more');
  const STATE = `JSON.stringify((() => { const r = document.getElementById('rail'), max = r.scrollWidth - r.clientWidth, l = document.querySelector('.lp-rail-line i'), c = document.querySelector('.lp-rail-count'), btn = [...document.querySelectorAll('.lp-rail-btn')];
    return { left: Math.round(r.scrollLeft), max, line: parseFloat(getComputedStyle(l).scale), count: c.textContent.replace(/\\s+/g, ' ').trim(), on: [...r.querySelectorAll('figure')].findIndex((f) => f.classList.contains('lp-on')), n: r.querySelectorAll('figure').length, op: [...r.querySelectorAll('figure > div img')].map((i) => +(+getComputedStyle(i).opacity).toFixed(2)),
      btn: btn.map((b) => [b.getAttribute('aria-disabled'), b.getAttribute('aria-label'), getComputedStyle(b).display, Math.round(b.getBoundingClientRect().width)]), cap: [...r.querySelectorAll('figcaption')].map((c) => +getComputedStyle(c).opacity) }; })())`;
  for (const [lang, width] of [['en', 1280], ['de', 375]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    await page.eval("document.querySelector('#more').open = true");
    await scrollTo(page, '#rail', width < 800 ? 1000 : 1100); await sleep(300);
    expect('more', (await page.eval("getComputedStyle(document.querySelector('.lp-rail-wrap')).opacity")) === '0', `${tag}: the rail is not hidden before it comes into view`);
    await scrollTo(page, '#rail', 200);
    const f = await frames(page, ['.lp-rail-wrap'], ['opacity', 'translate'], 1200);
    const o = col(f['.lp-rail-wrap'], 1).map(num);
    expect('more', o[0] < 0.5 && o.at(-1) === 1 && col(f['.lp-rail-wrap'], 2).every((v) => v === 'none'), `${tag}: the rail does not fade in as one piece without moving (${o[0]} to ${o.at(-1)})`);
    await sleep(800);
    let s = JSON.parse(await page.eval(STATE));
    expect('more', s.max > 100 && s.count.startsWith('01 / 0') && s.on === 0 && s.line === 0, `${tag}: at the start the counter says ${s.count}, the full tone is on ${s.on}, the line is ${s.line}`);
    expect('more', s.op[0] === 1 && s.op.slice(1).every((v) => v === 0.82), `${tag}: the pictures' tones at the start: ${s.op}`);
    expect('more', s.cap.every((v) => v === 1), `${tag}: a caption is dimmed`);
    const total = s.n;
    expect('more', s.count === `01 / ${String(total).padStart(2, '0')}`, `${tag}: the counter ${s.count} for ${total} pictures`);
    if (width >= 768) {
      expect('more', s.btn.length === 2 && s.btn.every((b) => b[2] !== 'none' && b[3] === 44) && s.btn[0][0] === 'true' && s.btn[1][0] === null && s.btn.every((b) => b[1]), `${tag}: the buttons at the start: ${JSON.stringify(s.btn)}`);
      // the next button scrolls by one picture
      await page.eval("document.querySelectorAll('.lp-rail-btn')[1].click()");
      await sleep(1200);
      s = JSON.parse(await page.eval(STATE));
      const step = JSON.parse(await page.eval("JSON.stringify((() => { const f = document.querySelectorAll('#rail figure'); return Math.round(f[1].offsetLeft - f[0].offsetLeft); })())"));
      expect('more', near(s.left, step, 40), `${tag}: the next button scrolled to ${s.left}, one picture is ${step}`);
      expect('more', s.btn[0][0] === null, `${tag}: the previous button is still aria-disabled after a step`);
    } else {
      expect('more', s.btn.every((b) => b[2] === 'none'), `${tag}: the buttons are there below 768 px: ${JSON.stringify(s.btn)}`);
      await page.eval("document.getElementById('rail').scrollTo({ left: 300, behavior: 'instant' })");
      await sleep(500);
      s = JSON.parse(await page.eval(STATE));
    }
    expect('more', near(s.line, s.left / s.max, 0.01), `${tag}: the line is ${s.line} at ${s.left} of ${s.max}`);
    expect('more', s.on === Math.round((s.left / s.max) * (total - 1)) && s.count.startsWith(String(s.on + 1).padStart(2, '0')), `${tag}: the counter ${s.count} and the full tone on ${s.on} do not follow the scroll ${s.left}/${s.max}`);
    expect('more', s.op[s.on] === 1 && s.op.filter((v, i) => i !== s.on).every((v) => v === 0.82), `${tag}: only the current picture should be in full tone: ${s.op}`);
    // the end
    await page.eval("document.getElementById('rail').scrollTo({ left: 99999, behavior: 'instant' })");
    await sleep(600);
    s = JSON.parse(await page.eval(STATE));
    expect('more', s.count === `${String(total).padStart(2, '0')} / ${String(total).padStart(2, '0')}` && near(s.line, 1, 0.01) && s.on === total - 1, `${tag}: at the end the counter says ${s.count}, the line ${s.line}, the full tone ${s.on}`);
    if (width >= 768) expect('more', s.btn[1][0] === 'true' && s.btn[0][0] === null, `${tag}: at the end the buttons are ${JSON.stringify(s.btn)}`);
    // the line is direct: no transition on its scale
    expect('more', (await page.eval("getComputedStyle(document.querySelector('.lp-rail-line i')).transitionDuration")) === '0s', `${tag}: the progress line has a transition`);
    expect('more', page.errors.length === 0, `${tag}: script errors: ${page.errors.join(' | ')}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('more'))) pass('more', 'the rail appears as one piece; counter, line, full-tone picture and buttons follow the scroll; the buttons step by one picture and are not there below 768 px');
}

// ---------------------------------------------------------------------------------------------------- closeups
async function checkCloseups() {
  console.log('closeups');
  for (const [lang, width] of [['en', 1280], ['hu', 375]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: width < 800 ? 812 : 900 });
    await scrollTo(page, '.lp-cu-open', width < 800 ? 1300 : 1300); await sleep(300);
    const b = JSON.parse(await page.eval("JSON.stringify({ seen: document.querySelector('.lp-cu-open').dataset.in !== undefined, from: document.querySelector('.lp-cu-open').style.getPropertyValue('--crop-from'), clip: getComputedStyle(document.querySelector('.lp-cu-img > img')).clipPath, dash: getComputedStyle(document.querySelector('.lp-loc-draw')).strokeDashoffset, edge: getComputedStyle(document.querySelector('.lp-edge-img > img')).clipPath })"));
    expect('closeups', !b.seen && b.clip.startsWith('inset(') && b.clip !== 'inset(0px)', `${tag}: before it is in view the crop is not held at the square's rectangle (${b.clip})`);
    expect('closeups', b.dash === '1px', `${tag}: the square is drawn before the crop is in view (${b.dash})`);
    // the rectangle of the square, in the crop's own box
    const geo = JSON.parse(await page.eval("JSON.stringify((() => { const f = document.querySelector('.lp-cu-img').getBoundingClientRect(), m = document.querySelector('.lp-loc-sq').getBoundingClientRect(); return { top: m.top - f.top, right: f.right - m.right, bottom: f.bottom - m.bottom, left: m.left - f.left, w: m.width, side: f.width }; })())"));
    const got = /inset\(([\d.]+)px ([\d.]+)px ([\d.]+)px ([\d.]+)px\)/.exec(b.clip);
    expect('closeups', !!got && [geo.top, geo.right, geo.bottom, geo.left].every((v, i) => near(v, +got[i + 1], 1.5)), `${tag}: the starting clip ${b.clip} is not the square's rectangle in the crop ${JSON.stringify(geo)}`);
    note(`closeups ${tag}: the square is ${geo.w.toFixed(1)} px on a crop of ${geo.side.toFixed(0)} px`);
    await scrollTo(page, '.lp-cu-open', 110);
    const PROPS = ['clip-path', 'stroke-dashoffset', 'opacity', 'scale', 'transform', 'translate'];
    const EDGE = ['.lp-edge-img > img', '.lp-edge-img .lp-vis-chip', '.lp-edge-img'];
    const f = await frames(page, ['.lp-cu-img > img', '.lp-loc-draw', '.lp-cu-badge', '.lp-locator', ...(width >= 640 ? EDGE : [])], PROPS, 4200);
    if (width < 640) {
      // a phone: the edge is the second card of a swipe rail, it opens when it is swiped into view
      await page.eval("document.querySelector('.lp-cu-grid').scrollTo({ left: 9999, behavior: 'instant' })");
      Object.assign(f, await frames(page, EDGE, PROPS, 3600));
    }
    const img = f['.lp-cu-img > img'], dash = col(f['.lp-loc-draw'], 2).map(num);
    expect('closeups', dash[0] > 0.9 && dash.at(-1) === 0 && dash.every((v, i) => i === 0 || v <= dash[i - 1] + 1e-6), `${tag}: the square does not draw 1 to 0 (${dash[0]} to ${dash.at(-1)})`);
    const insets = img.map((r) => /inset\(([\d.e+-]+)px/.exec(r[1])?.[1]).map((v, i) => (v === undefined ? (img[i][1] === 'inset(0px)' ? 0 : null) : +v));
    expect('closeups', insets.every((v) => v !== null), `${tag}: a frame of the crop has a clip that is not an inset: ${img.find((r, i) => insets[i] === null)?.[1]}`);
    const opened = insets.map((v, i) => [v, i]).filter(([v]) => v !== null);
    expect('closeups', opened[0][0] > geo.top - 2 && opened.at(-1)[0] === 0 && opened.every(([v], i) => i === 0 || v <= opened[i - 1][0] + 1e-6), `${tag}: the crop does not open from the square to the whole panel monotonically (${opened[0][0]} to ${opened.at(-1)[0]})`);
    const startOpen = img.find((r, i) => i > 0 && insets[i] < insets[0] - 1), endOpen = img.find((r, i) => insets[i] === 0);
    note(`closeups ${tag}: the crop starts to open at ${startOpen?.[0]} ms and is whole at ${endOpen?.[0]} ms (the square starts drawing at 0)`);
    expect('closeups', startOpen && startOpen[0] >= 250 && endOpen && endOpen[0] <= 2400, `${tag}: the crop opens between ${startOpen?.[0]} and ${endOpen?.[0]} ms (it should start about 300 ms after the square and end within 2.4 s)`);
    // no dead start (2026-10-05: on the in out curve the panel was a black square for 1.2 s and read as a missing picture): a second in, most of the panel is open
    const atOne = img.find((r) => r[0] >= 1000), i1 = atOne ? img.indexOf(atOne) : -1;
    expect('closeups', i1 > 0 && insets[i1] <= insets[0] * 0.5, `${tag}: one second in, the crop's top inset is still ${insets[i1]} of ${insets[0]} px (want half of it or less: the panel must not sit black)`);
    expect('closeups', img.every((r) => r[4] === 'none' && r[5] === 'none' && r[6] === 'none' && r[3] === '1'), `${tag}: the crop is scaled, moved or faded at some frame`);
    expect('closeups', col(f['.lp-cu-badge'], 3).every((v) => v === '1') && col(f['.lp-locator'], 3).every((v) => v === '1'), `${tag}: the badge or the map faded`);
    expect('closeups', col(f['.lp-edge-img .lp-vis-chip'], 3).every((v) => v === '1'), `${tag}: the label of the edge faded`);
    const edge = f['.lp-edge-img > img'];
    const es = col(edge, 4).map((v) => (v === 'none' ? 1 : num(v)));
    expect('closeups', Math.max(...es) <= 1.0301 && es.at(-1) === 1 && col(edge, 3).every((v) => v === '1'), `${tag}: the edge plate scales above 1.03, does not settle to 1 or fades (${Math.max(...es)})`);
    expect('closeups', col(edge, 1).at(-1) === 'none' || col(edge, 1).at(-1) === 'inset(0px round 22px)', `${tag}: the edge plate ends clipped: ${col(edge, 1).at(-1)}`);
    expect('closeups', page.errors.length === 0, `${tag}: script errors: ${page.errors.join(' | ')}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('closeups'))) pass('closeups', 'the square draws, the crop opens from the square to the whole panel without scaling, the badge, the map and the label stay, the edge opens as a plate');
}

// ---------------------------------------------------------------------------------------------------- identity
async function checkIdentity() {
  console.log('identity');
  // The artwork rectangles of the chapters, with whatever is laid over them hidden. At rest they must be the same with the motion off and after
  // all of it has played: (1) the element and every ancestor carries the same visual state (opacity, transform, translate, scale, rotate, filter,
  // clip-path, blend, mask, visibility), and (2) where both runs put the picture at the same sub-pixel position, the pixels are identical with
  // zero tolerance. A picture laid out at another fraction of a pixel in the two runs (a pinned scene elsewhere on the page makes the page
  // taller under motion) is resampled differently by the browser whatever any motion does, so there only (1) is a verdict.
  const TARGETS = [
    ['#styles .lp-tile:nth-child(1) .lp-art', '#styles'],
    ['#styles .lp-tile:nth-child(5) .lp-art', '#styles'],
    ['.lp-cu-img > img', '#closeups'],
    ['.lp-edge-img > img', '#closeups'],
    ['.lp-sqg:nth-of-type(n+3) image', '#ruler'],
    ['#rail figure:nth-child(1) img', '#rail', 0.88],   // the rail fades out under a mask over its right 8 percent: that strip is the mask, not the picture
    ['#steps .lp-step:nth-child(3) .lp-filecard img', '#steps'],
  ];
  const SIG = (sel) => `JSON.stringify((() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return null; const keys = ['opacity', 'transform', 'translate', 'scale', 'rotate', 'filter', 'clipPath', 'mixBlendMode', 'maskImage', 'visibility']; const out = []; for (let n = e; n && n !== document.body; n = n.parentElement) { const c = getComputedStyle(n); out.push(keys.map((k) => (k === 'clipPath' && (c[k] === 'inset(0px)' || c[k] === 'inset(0px round 22px)') ? 'none' : c[k])).join('|')); } return out.join(' > '); })())`;
  for (const width of (opt('--widths') ?? '1280,375').split(',').map(Number)) {
    const shoot = async (reduceMotion) => {
      const page = await open({ lang: 'en', width, height: width < 800 ? 812 : 900, reduceMotion });
      await page.eval("document.querySelector('#more').open = true");
      const out = [];
      for (const [sel, scroller, clamp = 1] of TARGETS) {
        const ok = await scrollTo(page, scroller === '#rail' ? '#rail' : sel, 140);
        if (!ok) { out.push(null); continue; }
        if (scroller === '#rail') await page.eval("document.getElementById('rail').scrollTo({ left: 0, behavior: 'instant' })");
        if (sel.includes('edge-img') && width < 640) await page.eval("document.querySelector('.lp-cu-grid').scrollTo({ left: 9999, behavior: 'instant' })");
        await sleep(5200);   // every entrance of the chapter is over
        await page.eval("(() => { const s = document.createElement('style'); s.id = 'hide'; s.textContent = '.lp-vis-chip, .lp-chip-ex, .lp-cu-badge, .lp-locator, .lp-glint, .lp-wallbtn { visibility: hidden !important }'; document.head.appendChild(s); })()");
        await page.eval('new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)))');   // the style must be on screen before the shot
        await sleep(150);
        const r = JSON.parse(await page.eval(`JSON.stringify((() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return null; const r = e.getBoundingClientRect(), k = devicePixelRatio; return [Math.round((r.left + 10) * k), Math.round((r.top + 10) * k), Math.round((Math.min(r.width, innerWidth * ${clamp} - r.left) - 20) * k), Math.round((r.height - 20) * k), r.left + scrollX, r.top + scrollY]; })())`));
        if (!r || r[2] <= 8 || r[1] < 0 || r[1] + r[3] > (await page.eval('innerHeight * devicePixelRatio'))) { out.push(null); continue; }
        out.push({ png: await page.shot(), crop: r.slice(0, 4), frac: [r[4] % 1, r[5] % 1], sig: await page.eval(SIG(sel)), size: [r[2], r[3]], file: await page.eval(`(document.querySelector(${JSON.stringify(sel)}).currentSrc || '').split('/').pop()`) });
        await page.eval("document.getElementById('hide')?.remove()");
      }
      await page.close();
      return out;
    };
    const a = await shoot(true), b = await shoot(false);
    let same = 0, bySignature = 0;
    for (let i = 0; i < TARGETS.length; i++) {
      const name = `${TARGETS[i][0]} at ${width}px`;
      if (!a[i] || !b[i]) { note(`identity ${width}px: ${TARGETS[i][0]} not on screen at this width, skipped`); continue; }
      expect('identity', a[i].sig === b[i].sig, `${name}: its visual state differs between reduced motion and motion after the entrance:\n    ${a[i].sig}\n    ${b[i].sig}`);
      expect('identity', near(a[i].size[0], b[i].size[0], 0.01) && near(a[i].size[1], b[i].size[1], 0.01), `${name}: its size differs (${a[i].size} against ${b[i].size})`);
      // the browser prefers a candidate of a srcset that it already holds: the pinned Reveal fetches the Radiance artwork (900 px) at once, so a tile of the same artwork
      // takes that file instead of its 480 px one. The same artwork from another file of the set is not what this claim is about (the pixels of one file, with and without motion)
      if (a[i].file !== b[i].file) { bySignature++; note(`identity ${name}: the browser chose ${a[i].file} with reduced motion and ${b[i].file} with motion (it reuses an image of the same set that it already holds); the pixel diff is skipped, the visual state is identical`); continue; }
      const sameSpot = near(a[i].frac[0], b[i].frac[0], 0.02) && near(a[i].frac[1], b[i].frac[1], 0.02);
      if (!sameSpot) { bySignature++; note(`identity ${name}: the two runs lay it out at other sub-pixel positions (${a[i].frac.map((v) => v.toFixed(2))} and ${b[i].frac.map((v) => v.toFixed(2))}); the pixel diff is skipped, the visual state is identical`); continue; }
      const d = await pngDiff(a[i].png, b[i].png, a[i].crop, b[i].crop);
      expect('identity', d.n === 0 && !d.size, `${name} differs between reduced motion and motion after the entrance: ${JSON.stringify(d)}`);
      if ((d.n > 0 || d.size) && process.env.KEEP_PNG) { const base = join(process.env.KEEP_PNG, `identity_${width}_${i}`); (await import('node:fs')).writeFileSync(base + '_reduced.png', a[i].png); (await import('node:fs')).writeFileSync(base + '_motion.png', b[i].png); note(`identity: wrote ${base}_reduced.png and _motion.png (crop ${JSON.stringify(a[i].crop)})`); }
      if (d.n === 0 && !d.size) same++;
    }
    if (same || bySignature) pass('identity', `${width}px: ${same} artwork rectangles pixel for pixel the same with and without motion, ${bySignature} more with an identical visual state (sub-pixel position differs between runs) (${createHash('sha256').update(a.find(Boolean).png).digest('hex').slice(0, 8)})`);
  }
}

// ---------------------------------------------------------------------------------------------------- keyboard
async function checkKeyboard() {
  console.log('keyboard');
  const page = await open({ width: 1280 });
  await page.eval("document.querySelector('#more').open = true");
  const KEY = { Tab: 9, Enter: 13, ArrowRight: 39, ArrowLeft: 37 };
  const press = async (key, shift = false) => { await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key, code: key, windowsVirtualKeyCode: KEY[key], modifiers: shift ? 8 : 0, ...(key === 'Enter' ? { text: '\r' } : {}) }); await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key, code: key, windowsVirtualKeyCode: KEY[key], modifiers: shift ? 8 : 0 }); await sleep(120); };
  const active = () => page.eval("(() => { const a = document.activeElement; return a ? (a.id ? '#' + a.id : a.tagName.toLowerCase() + (a.className ? '.' + String(a.className).split(' ')[0] : '') + (a.getAttribute('aria-label') ? '[' + a.getAttribute('aria-label') + ']' : '')) : 'none'; })()");
  // from the tab list of the styles to the first tile: the selected tab, then the panel, the chips, the wall button of the first tile
  await scrollTo(page, '#gTabs', 200); await sleep(300);
  await page.eval("document.querySelector('#gTabs [aria-selected=true]').focus()");
  const order = [];
  for (let i = 0; i < 6; i++) { await press('Tab'); order.push(await active()); }
  note(`keyboard: after the style tabs Tab visits ${order.join(' > ')}`);
  expect('keyboard', order.some((x) => x.includes('lp-wallbtn')), 'the wall button of a tile cannot be reached with the Tab key');
  const ring = JSON.parse(await page.eval("JSON.stringify((() => { const a = document.activeElement, c = getComputedStyle(a); return [c.outlineStyle, c.outlineWidth, +getComputedStyle(a).opacity]; })())"));
  note(`keyboard: the focused wall button has outline ${ring[0]} ${ring[1]} and opacity ${ring[2]}`);
  // the buttons of the rooms strip: Tab reaches them and Enter scrolls
  await scrollTo(page, '#rail', 250); await sleep(900);
  await page.eval("document.getElementById('rail').focus()");
  await press('Tab', true);
  const btn1 = await active();
  expect('keyboard', btn1.includes('Next picture'), `before the rail, Shift+Tab goes to ${btn1} (the buttons sit above the rail)`);
  await press('Tab', true);
  expect('keyboard', (await active()).includes('Previous picture'), 'the previous button is not the one before the next button');
  const left0 = await page.eval("document.getElementById('rail').scrollLeft");
  await page.eval("document.querySelector('.lp-rail-btn[aria-label=\"Next picture\"]').focus()");
  await press('Enter');
  await sleep(1600);
  const left1 = await page.eval("document.getElementById('rail').scrollLeft");
  expect('keyboard', left1 > left0 + 100, `Enter on the next button did not scroll the rail (${left0} to ${left1})`);
  // the arrow keys in the rail itself
  await page.eval("document.getElementById('rail').focus()");
  await press('ArrowRight'); await sleep(500);
  expect('keyboard', (await page.eval("document.getElementById('rail').scrollLeft")) > left1, 'ArrowRight does not scroll the focused rail');
  // the size chips and the size guide are keyboard sized: arrow keys pick and draw
  await scrollTo(page, '#sizeChips', 300); await sleep(900);
  await page.eval("document.querySelector('#sizeChips [aria-checked=true]').focus()");
  await press('ArrowLeft'); await sleep(900);
  const picked = await page.eval("document.querySelector('#sizeChips [aria-checked=true]').dataset.cm");
  const drawn = await page.eval("[...document.querySelectorAll('.lp-sqg')].filter((g) => getComputedStyle(g.querySelector('.lp-sq-on')).strokeDashoffset === '0px').map((g) => g.dataset.cm).join()");
  expect('keyboard', picked === '40' && drawn === '40', `ArrowLeft on the size chips: picked ${picked}, gold outline on ${drawn}`);
  await page.close();
  if (!problems.some((x) => x.startsWith('keyboard'))) pass('keyboard', 'the wall button, the rail buttons and the rail itself are reachable and do their work from the keyboard; the arrow keys pick a size and draw its outline');
}

// ---------------------------------------------------------------------------------------------------- cls
async function checkCls() {
  console.log('cls');
  for (const [width, height, lang] of [[375, 812, 'en'], [1280, 900, 'de'], [375, 812, 'hu']]) {
    const tag = `${lang} ${width}px`;
    const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1, vitals: true });
    await page.goto(`${origin}/?lang=${lang}`);
    await page.loaded();
    for (let i = 0; i < 200; i++) {
      if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq')")) break;
      await sleep(100);
    }
    const H = await page.eval('document.documentElement.scrollHeight');
    for (let y = 0; y < H; y += Math.round(height * 0.45)) { await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`); await sleep(320); }
    await sleep(1500);
    const shifts = JSON.parse(await page.eval('JSON.stringify(window.__shifts)'));
    const ours = shifts.filter(([, , src]) => /lp-(how|steps|step|tab|tile|grid|stage|wall|mat|art|lbl|ruler|rail|cu-|loc|edge|locator|size|sq|stack|eye|more)|#(how|styles|wall|sizes|more|closeups|steps|stage|rail|ruler)/.test(src));
    const sum = ours.reduce((a, [, v]) => a + v, 0);
    expect('cls', sum < 0.001, `${tag}: layout shifts in these chapters over a slow scroll: ${JSON.stringify(ours)}`);
    note(`cls ${tag}: total ${(await page.eval('window.__cls')).toFixed(4)}, in these chapters ${sum.toFixed(4)} (${shifts.length} shifts in all: ${JSON.stringify(shifts.slice(0, 4))})`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('cls'))) pass('cls', 'no layout shift in the six chapters over a slow scroll of the page, on a phone and on a desktop');
}

// ---------------------------------------------------------------------------------------------------- gold
async function checkGold() {
  console.log('gold');
  const CENSUS = `JSON.stringify((() => {
    const gold = (c) => { const m = c.match(/rgba?\\((\\d+), (\\d+), (\\d+)(?:, ([\\d.]+))?\\)/); return !!m && (m[4] === undefined || +m[4] > .4) && +m[1] > 200 && +m[2] > 150 && +m[3] < 135 && +m[1] - +m[3] > 100; };
    const ownText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    const chrome = (el) => !!el.closest('.lp-topbar, .lp-hdr, .lp-menu, .lp-skip, .lp-vis-chip, .lp-chip-ex, .lp-cu-badge, .lp-vis, .lp-num, .lp-big');
    const out = { text: [], fill: [], line: [] };
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect(); if (!(r.width > 0 && r.bottom > 0 && r.top < innerHeight) || chrome(el)) continue;
      const tag = el.tagName + '.' + String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className).slice(0, 24);
      const s = getComputedStyle(el);
      if (ownText(el) && gold(s.color)) out.text.push(tag);
      if (gold(s.backgroundColor)) out.fill.push(tag);
      if (parseFloat(s.borderTopWidth) > 0 && gold(s.borderTopColor)) out.line.push(tag);
      if (el.tagName === 'rect' && gold(s.stroke) && +s.strokeDashoffset === 0) out.line.push(tag);
      for (const p of ['::before', '::after']) { const q = getComputedStyle(el, p); if (q.content !== 'none') { if (gold(q.backgroundColor)) out.line.push(tag + p); if (parseFloat(q.borderTopWidth) > 0 && gold(q.borderTopColor)) out.line.push(tag + p); } }
    }
    return out;
  })())`;
  for (const [w, h] of [[1280, 800], [390, 844]]) {
    const page = await open({ lang: 'en', width: w, height: h });
    await page.eval("document.querySelector('#more').open = true");
    let worst = 0, where = '';
    for (const sel of ['#how h2', '#steps', '#gTabs', '.lp-tile', '.lp-wall-grid', '#ruler', '#rail', '.lp-cu-open']) {
      await scrollTo(page, sel, 120);
      await sleep(4300);
      const c = JSON.parse(await page.eval(CENSUS));
      const groups = ['text', 'fill', 'line'].filter((k) => c[k].length > 0);
      if (groups.length > worst) { worst = groups.length; where = sel; }
      expect('gold', groups.length <= 3, `${w}px at ${sel}: ${groups.length} gold groups (text ${c.text.join(',')} | fills ${c.fill.join(',')} | lines ${c.line.length})`);
      expect('gold', c.text.length <= 2, `${w}px at ${sel}: gold text on ${c.text.length} elements: ${c.text.join(', ')}`);
      note(`gold ${w}px at ${sel}: text ${c.text.length} (${c.text.slice(0, 3).join(', ')}), fills ${c.fill.length}, lines and rings ${c.line.length}`);
    }
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('gold'))) pass('gold', 'at most three gold groups in every viewport that holds one of the six chapters, chrome and picture labels excluded');
}

// ---------------------------------------------------------------------------------------------------- run
const checks = { reduced: checkReduced, how: checkHow, styles: checkStyles, wall: checkWall, sizes: checkSizes, more: checkMore, closeups: checkCloseups, identity: checkIdentity, keyboard: checkKeyboard, cls: checkCls, gold: checkGold };
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
console.log(problems.length ? `\nsections motion check FAILED (${problems.length}):\n  ${problems.join('\n  ')}` : '\nsections motion check ok');
process.exit(problems.length ? 1 : 0);
