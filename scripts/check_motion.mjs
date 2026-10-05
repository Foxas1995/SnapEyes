// The checks of the landing page's motion (docs: the motion spec, sections 4.4, 5.5 and 13), in real Chrome, against a build (dist/) served the
// way Vercel serves it, with a stub of the two API calls the page makes. Not part of `vite build` (it needs Chrome and a minute or two); run it
// after a build:
//   npm run build && npm run check:motion
//   node scripts/check_motion.mjs [--dist dist] [--only reduced,nojs,failsafe,engine,hero,header,menu,handoff,sheets,gold,overflow,skip]
// Exit code 1 when any check fails.
//
// What it checks (each name is a value of --only):
//   reduced   prefers-reduced-motion: reduce: no html.mo, nothing hidden, no running animation, every [data-reveal] in its final state, the
//             first screen in its final state at once, the hero artwork pixel for pixel the same as with motion after the entrance (AC-5)
//   nojs      the page without JavaScript: the static first screen's entrance still ends in the final state, nothing stays hidden
//   failsafe  a dead IntersectionObserver (an in-app browser): html.mo-fail lifts every hidden state 3.5 s after boot; with a live one it never
//             appears; a full scroll reveals every [data-reveal] it passed, leaves no animation behind and no transition delay
//   engine    the engine's own code (src/motion/motion.ts, transpiled) and motion.css in a sandbox page with real frames: reveals, late mounts,
//             stagger cap, failsafe, pinned scene at p = 0 .25 .5 .75 1, no pin on a phone, whenPinned following the width, lit() gated by html.mo,
//             reduced motion doing nothing at all, and the padded mask keeping Hungarian and Lithuanian accents and ogoneks inside the clip
//   hero      the first screen: the picture is never faded, filtered, rotated or scaled above 1.03 at any frame; the honesty labels are visible
//             from the first frame; one headline, real text, a space between phrases, no stray star
//   header    the glass after 24 px, the gold marker under the link of the section being read (and gone on a section with no link), measured
//             again after a language switch, the language switch's pressed background sliding
//   menu      the dialog of the narrow widths: opens before React has started, keeps the focus inside, Escape and the close button close it, a
//             link closes it, the focus returns to the button, a wide window closes it
//   handoff   phone profile (slow 4G, CPU x4): the entrance does not start again when React takes the page (no frame where the lead or the
//             headline goes back); a deliberate defect (the adoption switched off) must be caught
//   sheets    the three stacked sheets: tones, rounded top, rim, nothing of the content under the next sheet's overlap, and every sticky element of
//             the page (the Reveal's stage, how it works, the FAQ's head) still sticks inside a sheet
//   gold      the gold census of the first screen (13.9): at most 3 gold groups per viewport, chrome excluded
//   overflow  no headline wider than its box and no horizontal scroll at 320 and 390 px in every language; no headline word cut by its mask
//   skip      the chapters below the first screen are skipped until near the screen (content-visibility), the pinned Reveal is not, a jump to a section lands on it
//             and the page keeps its height from the first moment to the end of a full scroll (within 3.5 percent)
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
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
/** A fresh visit (nothing remembered), the page open, every lazy section mounted. */
async function open({ lang = 'en', query = '', width = 1280, height = 900, settle = true, ...more } = {}) {
  const wipe = await chrome.page({ width: 400, height: 300 });
  await wipe.goto(`${origin}/imprint?lang=en`);
  await wipe.loaded();
  await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
  await wipe.close();
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: width < 800 ? 2 : 1, ...more });
  if (more.pre) await page.send('Page.addScriptToEvaluateOnNewDocument', { source: more.pre });
  const q = new URLSearchParams(query);
  if (lang) q.set('lang', lang);
  await page.goto(`${origin}/?${q}`);
  await page.loaded();
  if (settle) await mounted(page);
  return page;
}
async function mounted(page) {
  for (let i = 0; i < 150; i++) {
    if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) return;
    await sleep(100);
  }
}
/** Scroll top to bottom in steps of 60 percent of the screen (so that nothing is jumped over: a node is revealed by being on screen, and a step
 *  longer than the screen would skip the nodes between two stops), a pause at each. Returns the last scroll position. */
async function scrollThrough(page, pause = 350) {
  const H = await page.eval('document.documentElement.scrollHeight');
  const vh = await page.eval('innerHeight');
  let y = 0;
  for (let t = 0; ; t += Math.round(vh * 0.6)) {
    y = Math.min(t, H - vh);
    await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`);
    await sleep(pause);
    if (y >= H - vh) break;
  }
  return y;
}
const finalState = (sel) => `[...document.querySelectorAll(${JSON.stringify(sel)})].filter((e) => { const c = getComputedStyle(e); return +c.opacity < 0.99 || (c.translate !== 'none' && c.translate !== '0px' && c.translate !== '0px 0px') || (c.scale !== 'none' && c.scale !== '1' && c.scale !== '1 1'); }).map((e) => e.tagName + '.' + String(e.className).slice(0, 30))`;

// ---------------------------------------------------------------------------------------------------- reduced
async function checkReduced() {
  console.log('reduced');
  for (const [lang, width] of [['en', 1280], ['hu', 375], ['de', 1280]]) {
    const page = await open({ lang, width, height: width < 800 ? 812 : 900, reduceMotion: true });
    const tag = `${lang} ${width}px`;
    const s = JSON.parse(await page.eval(`JSON.stringify({
      mo: document.documentElement.classList.contains('mo'), fail: document.documentElement.classList.contains('mo-fail'),
      anims: document.getAnimations().filter((a) => a instanceof CSSAnimation).length,
      hidden: ${finalState('[data-reveal], [data-reveal] .lp-line-mask > span')}, heroHidden: ${finalState('.lp-hero .lp-rise, .lp-hero .lp-rise-s, .lp-hero .lp-rise-line, .lp-hero .lp-disc, .lp-hero-frame img')},
      inlineLit: [...document.querySelectorAll('.lp-lit [data-w]')].filter((w) => w.style.opacity).length, reveals: document.querySelectorAll('[data-reveal]').length })`));
    expect('reduced', !s.mo && !s.fail, `${tag}: html carries mo (${s.mo}) or mo-fail (${s.fail}) under reduced motion`);
    expect('reduced', s.anims === 0, `${tag}: ${s.anims} CSS animations are running under reduced motion`);
    expect('reduced', s.hidden.length === 0, `${tag}: hidden or moved at rest: ${s.hidden.join(', ')}`);
    expect('reduced', s.heroHidden.length === 0, `${tag}: the first screen is not in its final state: ${s.heroHidden.join(', ')}`);
    expect('reduced', s.inlineLit === 0, `${tag}: ${s.inlineLit} scroll lit words carry an inline opacity under reduced motion`);
    await scrollThrough(page, 120);
    const after = JSON.parse(await page.eval(`JSON.stringify({ hidden: ${finalState('[data-reveal], [data-reveal] .lp-line-mask > span')}, mo: document.documentElement.classList.contains('mo') })`));
    expect('reduced', after.hidden.length === 0 && !after.mo, `${tag}: after a full scroll: hidden ${after.hidden.join(', ')}, mo ${after.mo}`);
    await page.close();
  }
  // the artwork at rest is pixel for pixel the same with the motion off and with it on, after the entrance (AC-5, zero tolerance)
  for (const width of [1280, 375]) {
    const shot = async (reduceMotion) => {
      const page = await open({ lang: 'en', width, height: width < 800 ? 812 : 900, reduceMotion, settle: false });
      await sleep(6000);   // the entrance, the glint sweep (it ends at 4.5 s) and the handoff are over
      // the artwork's own pixels: what is laid over it (the disc, the chip, the glint, the ring, the bloom) is hidden in both, and the clip stays 24 px
      // inside the frame, away from the anti-aliased edge of its rounded corners (which Chrome rasterises a little differently for a node that has
      // been animated). The overlays are checked on their own: the hero check follows their opacity frame by frame.
      await page.eval("(() => { const s = document.createElement('style'); s.textContent = '.lp-disc, .lp-frame-chip, .lp-glint, .lp-hero::before, .lp-hero-stage::before { visibility: hidden !important }'; document.head.appendChild(s); })()");
      const clip = JSON.parse(await page.eval("JSON.stringify((() => { const r = document.getElementById('heroImg').getBoundingClientRect(); return [r.left + 24, r.top + scrollY + 24, r.width - 48, r.height - 48]; })())"));
      const png = await page.shot(clip);
      await page.close();
      return png;
    };
    const a = await shot(true), b = await shot(false);
    const d = await pngDiff(a, b);
    expect('reduced', d.n === 0 && !d.size, `hero artwork at ${width}px differs between reduced motion and motion after the entrance: ${JSON.stringify(d)}`);
    if (d.n === 0 && !d.size) pass('reduced', `the hero artwork at ${width}px is identical with and without motion (${createHash('sha256').update(a).digest('hex').slice(0, 8)})`);
  }
  pass('reduced', 'reduced motion: no html.mo, no running animation, nothing hidden or moved, the first screen final at once, in en, hu and de');
}
/** Compare two PNGs in Chrome itself (canvas): how many pixels differ in any channel. */
async function pngDiff(a, b) {
  const page = await chrome.page({ width: 400, height: 300 });
  const expr = `(async () => {
    const load = (b64) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'data:image/png;base64,' + b64; });
    const [x, y] = await Promise.all([load(${JSON.stringify(a.toString('base64'))}), load(${JSON.stringify(b.toString('base64'))})]);
    if (x.width !== y.width || x.height !== y.height) return JSON.stringify({ size: [x.width, x.height, y.width, y.height] });
    const data = (im) => { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0); return g.getImageData(0, 0, im.width, im.height).data; };
    const p = data(x), q = data(y); let n = 0, max = 0, x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let i = 0; i < p.length; i += 4) if (p[i] !== q[i] || p[i + 1] !== q[i + 1] || p[i + 2] !== q[i + 2]) { n++; max = Math.max(max, Math.abs(p[i] - q[i]), Math.abs(p[i + 1] - q[i + 1]), Math.abs(p[i + 2] - q[i + 2])); const k = i / 4, px = k % x.width, py = Math.floor(k / x.width); x0 = Math.min(x0, px); y0 = Math.min(y0, py); x1 = Math.max(x1, px); y1 = Math.max(y1, py); }
    return JSON.stringify({ n, max, box: n ? [x0, y0, x1, y1] : null });
  })()`;
  const r = JSON.parse(await page.eval(expr));
  await page.close();
  return r;
}

// ---------------------------------------------------------------------------------------------------- nojs
async function checkNoJs() {
  console.log('nojs');
  for (const [lang, width] of [['en', 1280], ['hu', 375]]) {
    const page = await chrome.page({ width, height: width < 800 ? 812 : 900, mobile: width < 800, dpr: 1, noJs: true });
    await page.goto(`${origin}/?lang=${lang}`);
    await page.loaded();
    await sleep(5200);   // the entrance runs to 2.1 s and the glint to 4.5 s, in CSS alone
    const s = JSON.parse(await page.eval(`JSON.stringify({ shell: !!document.getElementById('shell'), mo: document.documentElement.classList.contains('mo'),
      hidden: ${finalState('#shell .lp-hero *:not(.lp-price), #shell .lp-hdr, #shell .lp-topbar')}, reveals: document.querySelectorAll('[data-reveal]').length,
      h1: document.getElementById('h1')?.textContent || '', lead: getComputedStyle(document.querySelector('.lp-lead')).opacity, img: getComputedStyle(document.getElementById('heroImg')).opacity })`));
    const tag = `${lang} ${width}px no JS`;
    expect('nojs', s.shell && !s.mo, `${tag}: the static first screen is missing or html has mo (${JSON.stringify({ shell: s.shell, mo: s.mo })})`);
    expect('nojs', s.hidden.length === 0, `${tag}: still hidden or moved after the entrance: ${s.hidden.slice(0, 8).join(', ')}`);
    expect('nojs', s.reveals === 0, `${tag}: ${s.reveals} [data-reveal] nodes in the static page (they would stay hidden without a script)`);
    expect('nojs', s.h1.trim().length > 10 && !/\*/.test(s.h1), `${tag}: the headline reads "${s.h1}"`);
    await page.close();
  }
  pass('nojs', 'without JavaScript the first screen ends in its final state and nothing waits for a script');
}

// ---------------------------------------------------------------------------------------------------- failsafe
async function checkFailsafe() {
  console.log('failsafe');
  // a dead IntersectionObserver: it never reports (an in-app browser, a broken polyfill)
  const dead = 'window.IntersectionObserver = class { constructor() {} observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } };';
  const page = await open({ lang: 'en', width: 1280, pre: dead, settle: false });
  await sleep(6500);
  await mounted(page);
  const s = JSON.parse(await page.eval(`JSON.stringify({ mo: document.documentElement.classList.contains('mo'), fail: document.documentElement.classList.contains('mo-fail'),
    hidden: ${finalState('[data-reveal]')}, n: document.querySelectorAll('[data-reveal]').length })`));
  expect('failsafe', s.mo && s.fail, `with a dead observer html.mo-fail never came (mo ${s.mo}, fail ${s.fail})`);
  expect('failsafe', s.hidden.length === 0, `with a dead observer these stay hidden: ${s.hidden.join(', ')} (of ${s.n})`);
  await page.close();

  // a live one: the failsafe never fires, and a full scroll reveals everything it passed and leaves nothing behind
  const live = await open({ lang: 'en', width: 1280, height: 800 });
  const y = await scrollThrough(live, 220);
  await sleep(1800);
  // a section that has been scrolled past is skipped again (content-visibility, css/base.css) and the browser does not update the animations inside a skipped subtree:
  // an animation that finished there is still listed. So every section is made to render first (the engine's work is over by now) and the frames get their turn
  await live.eval("document.head.appendChild(Object.assign(document.createElement('style'), { textContent: '.lp-sheet > .lp-sec, .lp-final { content-visibility: visible !important }' }))");
  await sleep(500);
  const r = JSON.parse(await live.eval(`JSON.stringify((() => {
    const out = { fail: document.documentElement.classList.contains('mo-fail'), mo: document.documentElement.classList.contains('mo'), passed: 0, notIn: [], left: [], delayed: [], n: document.querySelectorAll('[data-reveal]').length };
    for (const e of document.querySelectorAll('[data-reveal]')) {
      if (e.getBoundingClientRect().top + scrollY > ${y} + innerHeight) continue;
      out.passed++;
      if (!('in' in e.dataset)) out.notIn.push(e.tagName + '.' + String(e.className).slice(0, 24));
      if (e.getAnimations({ subtree: true }).length) out.left.push(e.tagName + '.' + String(e.className).slice(0, 24));
      const c = getComputedStyle(e);
      if (c.transitionDelay.split(',').some((d) => parseFloat(d) > 0) || /^opacity, translate/.test(c.transitionProperty)) out.delayed.push(e.tagName + ' ' + c.transitionProperty + ' ' + c.transitionDelay);
    }
    return out;
  })())`));
  expect('failsafe', r.mo && !r.fail, `with a live observer: mo ${r.mo}, mo-fail ${r.fail}`);
  expect('failsafe', r.notIn.length === 0, `scrolled past but never revealed: ${r.notIn.join(', ')}`);
  expect('failsafe', r.left.length === 0, `an animation is left behind on a revealed node: ${r.left.join(', ')}`);
  expect('failsafe', r.delayed.length === 0, `a revealed node kept a transition (it would slow its hover): ${r.delayed.join('; ')}`);
  if (!r.n) fail('failsafe', 'the page has no [data-reveal] node at all: the test saw nothing to reveal');
  else pass('failsafe', `${r.passed} of ${r.n} [data-reveal] nodes passed and revealed, no mo-fail, no animation or transition left behind; with a dead observer mo-fail lifted every hidden state`);
  await live.close();
}

// ---------------------------------------------------------------------------------------------------- engine (the module itself, in a sandbox page)
const TS = readFileSync(join(ROOT, 'src/motion/motion.ts'), 'utf8');
// --mutate-js "from@@to" and --mutate-css "from@@to" change the engine's code or the stylesheet in the sandbox only: a deliberate defect, to see
// that a check really fails (documented in the README, like check_landing's --mutate)
const mutate = (text, spec) => { if (!spec) return text; const [from, to] = spec.split('@@'); if (!text.includes(from)) throw new Error(`--mutate: "${from}" is not in the source`); return text.split(from).join(to); };
const JS = mutate(ts.transpileModule(TS, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText, opt('--mutate-js'));
const CSS = mutate(readFileSync(join(ROOT, 'src/motion/motion.css'), 'utf8'), opt('--mutate-css'));
const SANDBOX_CSS = `@font-face { font-family: 'Cinzel'; src: url('/assets/atelier/fonts/cinzel-var.woff2') format('woff2'); font-weight: 400 900; }
:root { --display: 'Cinzel', serif; --gold: #f5c542; --hdr-h: 64px; color-scheme: dark; } body { margin: 0; background: #07090e; color: #f0f3fa; } .pad { height: 1400px; }`;
/** An empty page of the site's own origin with motion.css in it and the engine's code ready to be imported, fresh each time. */
async function sandbox({ width = 1280, height = 800, reduceMotion = false } = {}) {
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: 1, reduceMotion });
  await page.goto(`${origin}/robots.txt`);
  await page.loaded();
  await page.eval(`(async () => { document.open(); document.write('<!doctype html><html><head><meta name="viewport" content="width=device-width"><style>' + ${JSON.stringify(SANDBOX_CSS)} + '</style><style>' + ${JSON.stringify(CSS)} + '</style></head><body class="lp"></body></html>'); document.close(); await document.fonts.load('500 40px Cinzel'); return 1; })()`);
  await page.eval(`window.importMotion = () => import(URL.createObjectURL(new Blob([${JSON.stringify(JS)}], { type: 'text/javascript' })));`);
  return page;
}
async function checkEngine() {
  console.log('engine');
  // 1. reveals: static and late nodes, stagger cap, nothing left behind
  let p = await sandbox();
  const r1 = JSON.parse(await p.eval(`(async () => {
    document.body.innerHTML = '<div class="pad"></div><div id="a" data-reveal="fade">A</div><ul id="g" data-stagger><li>1</li><li>2</li><li>3</li><li>4</li><li>5</li><li>6</li><li>7</li></ul><div class="pad"></div>';
    const m = await window.importMotion(); m.boot(); m.reveals();
    const root = document.documentElement, out = { mo: root.classList.contains('mo') };
    await new Promise((r) => setTimeout(r, 300));
    const a = document.getElementById('a');
    out.hiddenAtStart = getComputedStyle(a).opacity; out.inAtStart = 'in' in a.dataset;
    out.staggerIdx = [...document.getElementById('g').children].map((c) => c.style.getPropertyValue('--i')).join(',');
    out.staggerReveal = [...document.getElementById('g').children].every((c) => c.dataset.reveal === 'fade');
    window.scrollTo({ top: a.getBoundingClientRect().top + scrollY - 300, behavior: 'instant' });
    await new Promise((r) => setTimeout(r, 400));
    out.inAfterScroll = 'in' in a.dataset;
    // a node mounted later, in view
    const late = document.createElement('div'); late.dataset.reveal = 'fade-s'; late.textContent = 'late'; late.style.cssText = 'position:fixed;top:100px;left:10px';
    document.body.append(late);
    // a child added to a stagger list later
    const li = document.createElement('li'); li.textContent = 'late li'; document.getElementById('g').append(li);
    await new Promise((r) => setTimeout(r, 400));
    out.lateIn = 'in' in late.dataset; out.lateLiIdx = li.style.getPropertyValue('--i');
    // React rewrites className: the state must survive
    a.className = 'something else'; out.survivesClassName = 'in' in a.dataset;
    await new Promise((r) => setTimeout(r, 1500));
    out.after = { opacity: getComputedStyle(a).opacity, translate: getComputedStyle(a).translate, anims: a.getAnimations().length, tp: getComputedStyle(a).transitionProperty, td: getComputedStyle(a).transitionDelay, fail: root.classList.contains('mo-fail') };
    return JSON.stringify(out);
  })()`));
  expect('engine', r1.mo, 'boot() did not switch html.mo on');
  expect('engine', r1.hiddenAtStart === '0' && !r1.inAtStart, `an off-screen [data-reveal] was not hidden at the start (opacity ${r1.hiddenAtStart})`);
  expect('engine', r1.staggerIdx === '0,1,2,3,4,4,4' && r1.staggerReveal, `the stagger index is ${r1.staggerIdx} (want 0,1,2,3,4,4,4) or a child has no reveal of its own`);
  expect('engine', r1.inAfterScroll, 'scrolling a [data-reveal] into view did not set data-in');
  expect('engine', r1.lateIn, 'a [data-reveal] node mounted later was never revealed (it would stay hidden for good)');
  expect('engine', r1.lateLiIdx === '4', `a child added to a stagger list later got --i "${r1.lateLiIdx}" (want 4, the cap)`);
  expect('engine', r1.survivesClassName, 'data-in was lost when the className was rewritten');
  expect('engine', r1.after.opacity === '1' && r1.after.translate === 'none' && r1.after.anims === 0 && !r1.after.fail && !/^opacity, translate/.test(r1.after.tp) && parseFloat(r1.after.td) === 0, `after the reveal: ${JSON.stringify(r1.after)}`);
  await p.close();

  // 2. failsafe: a dead observer lifts the hidden state at 3.5 s; a live one never does
  p = await sandbox();
  const r2 = JSON.parse(await p.eval(`(async () => {
    document.body.innerHTML = '<div class="pad"></div><div id="a" data-reveal="fade">A</div><div class="pad"></div>';
    const real = window.IntersectionObserver; window.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} };
    const m = await window.importMotion(); m.boot(); m.reveals(); window.IntersectionObserver = real;
    const root = document.documentElement, a = document.getElementById('a'); const out = {};
    await new Promise((r) => setTimeout(r, 3000)); out.at3 = [root.classList.contains('mo-fail'), getComputedStyle(a).opacity];
    await new Promise((r) => setTimeout(r, 900)); out.at39 = [root.classList.contains('mo-fail'), getComputedStyle(a).opacity];
    return JSON.stringify(out);
  })()`));
  expect('engine', r2.at3[0] === false && r2.at3[1] === '0', `before 3.5 s with a dead observer: ${JSON.stringify(r2.at3)}`);
  expect('engine', r2.at39[0] === true && r2.at39[1] === '1', `after 3.5 s with a dead observer: ${JSON.stringify(r2.at39)} (want mo-fail and opacity 1)`);
  await p.close();

  // 2b. a page opened in a background tab gets its failsafe clock only when the tab is first seen (nothing is rendered, so no observer could report)
  p = await sandbox();
  const r2b = JSON.parse(await p.eval(`(async () => {
    document.body.innerHTML = '<div class="pad"></div><div id="a" data-reveal="fade">A</div><div class="pad"></div>';
    let hidden = true; Object.defineProperty(document, 'hidden', { get: () => hidden });
    const real = window.IntersectionObserver; window.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} };
    const m = await window.importMotion(); m.boot(); m.reveals(); window.IntersectionObserver = real;
    const root = document.documentElement, out = {};
    await new Promise((r) => setTimeout(r, 4200)); out.hiddenFor42 = root.classList.contains('mo-fail');
    hidden = false; document.dispatchEvent(new Event('visibilitychange'));
    await new Promise((r) => setTimeout(r, 3000)); out.seen3 = root.classList.contains('mo-fail');
    await new Promise((r) => setTimeout(r, 900)); out.seen39 = root.classList.contains('mo-fail');
    return JSON.stringify(out);
  })()`));
  expect('engine', r2b.hiddenFor42 === false && r2b.seen3 === false && r2b.seen39 === true, `the failsafe clock of a page opened in a background tab: ${JSON.stringify(r2b)} (want false, false, true)`);
  await p.close();

  // 3. the pinned scene at 1280 x 800: the stage holds the top at every p, the progress reads p
  p = await sandbox({ width: 1280, height: 800 });
  const r3 = JSON.parse(await p.eval(`(async () => {
    document.body.innerHTML = '<div class="pad"></div><div id="w" class="lp-scene" style="--scene-h:220svh"><div class="lp-stage" id="st"><div id="fr" style="width:300px;height:300px;background:#333"></div></div></div><div class="pad"></div>';
    const m = await window.importMotion(); m.boot(); m.reveals();
    const w = document.getElementById('w'), st = document.getElementById('st'), out = { rows: [], height: getComputedStyle(w).height };
    let last = -1; const stop = m.whenPinned(() => m.scene(w, (p) => { last = p; document.getElementById('fr').style.setProperty('--p', String(p)); }));
    const wrapTop = w.getBoundingClientRect().top + scrollY, span = w.offsetHeight - st.offsetHeight;
    for (const p of [0, 0.25, 0.5, 0.75, 1]) {
      window.scrollTo({ top: wrapTop + span * p, behavior: 'instant' });
      await new Promise((r) => setTimeout(r, 700));
      out.rows.push([p, Math.round(last * 1000) / 1000, Math.round(st.getBoundingClientRect().top * 10) / 10]);
    }
    // a reload in the middle of the scene starts at the measured progress, not at 0
    stop(); let first = -1; window.scrollTo({ top: wrapTop + span * 0.5, behavior: 'instant' }); await new Promise((r) => setTimeout(r, 300));
    const stop2 = m.scene(w, (p) => { if (first < 0) first = p; }); await new Promise((r) => setTimeout(r, 300)); out.first = Math.round(first * 1000) / 1000; stop2();
    return JSON.stringify(out);
  })()`));
  for (const [want, got, top] of r3.rows) {
    expect('engine', Math.abs(got - want) <= 0.02, `scene progress at p = ${want} reads ${got}`);
    expect('engine', Math.abs(top) <= 0.6, `the stage is at ${top} px from the top at p = ${want} (want 0: it must be pinned)`);
  }
  expect('engine', Math.abs(r3.first - 0.5) <= 0.02, `a scene started in the middle first reads ${r3.first} (want 0.5, not an ease up from 0)`);
  expect('engine', parseFloat(r3.height) > 800 * 2, `the scene wrapper is ${r3.height} high (want 220 percent of the screen)`);
  await p.close();

  // 4. a phone: no pin at all, the wrapper is an ordinary block, whenPinned never starts; the window growing starts it, shrinking stops it
  p = await sandbox({ width: 375, height: 812 });
  const r4 = JSON.parse(await p.eval(`(async () => {
    document.body.innerHTML = '<div id="w" class="lp-scene" style="--scene-h:220svh"><div class="lp-stage" id="st"><p>stage</p></div></div>';
    const m = await window.importMotion(); m.boot();
    const w = document.getElementById('w'), st = document.getElementById('st'), out = { starts: 0, stops: 0 };
    out.pos = getComputedStyle(st).position; out.heightIsAuto = w.offsetHeight === st.offsetHeight;
    m.whenPinned(() => { out.starts++; return () => { out.stops++; }; });
    return JSON.stringify(out);
  })()`));
  expect('engine', r4.pos === 'static' && r4.heightIsAuto, `on a phone the stage is "${r4.pos}" and the wrapper ${r4.heightIsAuto ? 'is' : 'is not'} an ordinary block`);
  expect('engine', r4.starts === 0, `on a phone whenPinned started ${r4.starts} time(s)`);
  await p.send('Emulation.setDeviceMetricsOverride', { width: 1100, height: 800, deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  const grown = await p.eval('JSON.stringify([getComputedStyle(document.getElementById("st")).position, getComputedStyle(document.getElementById("w")).height])');
  await p.send('Emulation.setDeviceMetricsOverride', { width: 600, height: 800, deviceScaleFactor: 1, mobile: false });
  await sleep(300);
  const shrunk = await p.eval('JSON.stringify([getComputedStyle(document.getElementById("st")).position, getComputedStyle(document.getElementById("w")).height])');
  expect('engine', JSON.parse(grown)[0] === 'sticky', `at 1100 px the stage is ${grown} (want sticky)`);
  expect('engine', JSON.parse(shrunk)[0] === 'static', `back at 600 px the stage is ${shrunk} (want static)`);
  await p.close();

  // 5. lit(): the words go from .5 to 1 in sequence; the gold word is marked; without html.mo nothing is dimmed and nothing is written
  p = await sandbox({ width: 1280, height: 800 });
  const r5 = JSON.parse(await p.eval(`(async () => {
    const words = 'Restored never repainted we keep every fibre of the eye you photographed and set it in a style you choose'.split(' ');
    document.body.innerHTML = '<div class="pad"></div><p class="lp-lit lp-t-lead" id="l" style="max-width:520px">' + words.map((w, i) => '<span><span data-w' + (i === 3 ? ' class="lp-g"' : '') + '>' + w + '</span> </span>').join('') + '</p><div class="pad"></div>';
    const m = await window.importMotion(); m.boot(); m.reveals();
    const l = document.getElementById('l'), ws = [...l.querySelectorAll('[data-w]')], out = {};
    out.dimAtRest = getComputedStyle(ws[0]).opacity;
    const stop = m.lit(l);
    const top = l.getBoundingClientRect().top + scrollY;
    // the scroll position that puts the sentence at progress q (traverse: 0 when its top is at 80 percent of the screen, 1 when its bottom is at 45)
    const h = l.getBoundingClientRect().height, a = innerHeight * 0.8, b = innerHeight * 0.45 - h;
    const read = async (q) => { window.scrollTo({ top: top - (a - q * (a - b)), behavior: 'instant' }); await new Promise((r) => setTimeout(r, 700)); return ws.map((w) => +getComputedStyle(w).opacity); };
    const before = await read(-0.2), mid = await read(0.45), after = await read(1.2);
    out.before = [before[0], before.at(-1)]; out.after = [after[0], after.at(-1)];
    out.mid = mid; out.sequence = mid.every((v, i) => i === 0 || v <= mid[i - 1] + 0.001) && mid[0] > mid.at(-1) + 0.1;
    out.gold = getComputedStyle(ws[3]).color; out.floor = Math.min(...before, ...mid, ...after);
    stop();
    return JSON.stringify(out);
  })()`));
  expect('engine', r5.before[0] === 0.5 && r5.before[1] === 0.5 && r5.after[0] === 1 && r5.after[1] === 1, `lit() ends: before ${JSON.stringify(r5.before)}, after ${JSON.stringify(r5.after)} (want .5 and 1)`);
  expect('engine', r5.sequence && r5.floor >= 0.5, `lit() is not a sequence from the first word on, or went under the .50 floor (${r5.floor}; the middle frame reads ${JSON.stringify(r5.mid)})`);
  expect('engine', /245, 197, 66/.test(r5.gold), `the marked word is not gold (${r5.gold})`);
  await p.close();
  p = await sandbox({ width: 1280, height: 800, reduceMotion: true });
  const r6 = JSON.parse(await p.eval(`(async () => {
    document.body.innerHTML = '<div class="pad"></div><p class="lp-lit" id="l"><span data-w>one</span> <span data-w>two</span></p><div id="a" data-reveal="fade">A</div><div class="pad"></div><div id="w" class="lp-scene"><div class="lp-stage" id="st">s</div></div>';
    const m = await window.importMotion(); m.boot(); m.reveals();
    const l = document.getElementById('l'); const stop = m.lit(l); let calls = 0; const stop2 = m.scene(document.getElementById('w'), () => { calls++; });
    window.scrollTo({ top: l.getBoundingClientRect().top + scrollY - 400, behavior: 'instant' }); await new Promise((r) => setTimeout(r, 800));
    const ws = [...l.querySelectorAll('[data-w]')];
    return JSON.stringify({ mo: document.documentElement.classList.contains('mo'), inline: ws.filter((w) => w.style.opacity).length, op: ws.map((w) => getComputedStyle(w).opacity), hidden: getComputedStyle(document.getElementById('a')).opacity, calls, pos: getComputedStyle(document.getElementById('st')).position, stopIsFn: typeof stop === 'function' && typeof stop2 === 'function' });
  })()`));
  expect('engine', !r6.mo && r6.inline === 0 && r6.op.every((v) => v === '1') && r6.hidden === '1' && r6.calls === 0 && r6.pos === 'static' && r6.stopIsFn, `under reduced motion the engine did something: ${JSON.stringify(r6)}`);
  await p.close();

  // 7. the padded mask: accents above capitals and ogoneks under letters stay inside the clip, measured with the real font
  p = await sandbox({ width: 1280, height: 800 });
  const r7 = JSON.parse(await p.eval(`(async () => {
    const out = [];
    for (const [txt, size] of [['ŐŰÓÁÉÍ ŎŬ', 100], ['ĄĘĮŲ Ž Š Č Ė', 100], ['Őű Ąę', 28]]) {
      document.body.innerHTML = '<h2 class="lp-t-title lp-phrased" style="font-size:' + size + 'px;margin:40px 0 0"><span class="lp-line-mask"><span>' + txt + '</span></span></h2>';
      const mask = document.querySelector('.lp-line-mask'), span = mask.firstElementChild, h = document.querySelector('h2');
      await document.fonts.ready;
      const c = document.createElement('canvas').getContext('2d'); const cs = getComputedStyle(h);
      c.font = cs.fontWeight + ' ' + cs.fontSize + ' Cinzel'; const m = c.measureText(txt);
      // the baseline: a zero size inline block at the end of the text sits on it
      const probe = document.createElement('i'); probe.style.cssText = 'display:inline-block;width:0;height:0'; span.append(probe);
      const base = probe.getBoundingClientRect().bottom, box = mask.getBoundingClientRect();
      probe.remove();
      out.push({ txt, topRoom: Math.round((base - m.actualBoundingBoxAscent) - box.top), bottomRoom: Math.round(box.bottom - (base + m.actualBoundingBoxDescent)), padTop: getComputedStyle(mask).paddingTop, em: size });
    }
    return JSON.stringify(out);
  })()`));
  for (const r of r7) {
    expect('engine', r.topRoom >= 0, `the mask clips the accents of "${r.txt}" (${r.em} px): ${r.topRoom} px of room above the tallest accent`);
    expect('engine', r.bottomRoom >= 0, `the mask clips the ogoneks of "${r.txt}" (${r.em} px): ${r.bottomRoom} px of room below the deepest tail`);
  }
  await p.close();
  if (!problems.some((x) => x.startsWith('engine'))) pass('engine', 'reveals (static, late, stagger cap, className survival), failsafe, scene at p 0 to 1 pinned, no pin on a phone, whenPinned following the width, lit(), reduced motion inert, masks keep accents and ogoneks');
}

// ---------------------------------------------------------------------------------------------------- hero
async function checkHero() {
  console.log('hero');
  // sampled every frame from the very start, on the phone profile so the entrance is slow enough to see
  const SAMPLER = `window.__f = []; (function loop() { const i = document.getElementById('heroImg'); if (i) { let min = 1, filt = 'none', tf = 0; for (let e = i; e && e !== document.documentElement; e = e.parentElement) { const c = getComputedStyle(e); min = Math.min(min, +c.opacity); if (c.filter !== 'none') filt = c.filter; } const c = getComputedStyle(i); const sc = c.scale === 'none' ? 1 : parseFloat(c.scale); const rot = c.rotate; const chip = document.querySelector('.lp-frame-chip'), cap = document.querySelector('.lp-hero-cap'), gl = document.querySelector('.lp-hero-frame .lp-glint'); window.__f.push({ t: Math.round(performance.now()), min, filt, sc, rot, tr: c.transform, chip: chip ? +getComputedStyle(chip).opacity : -1, cap: cap ? +getComputedStyle(cap).opacity : -1, vis: i.getBoundingClientRect().width > 0, gl: gl ? +getComputedStyle(gl, '::after').opacity : -1 }); } requestAnimationFrame(loop); })();`;
  for (const [lang, width] of [['en', 375], ['de', 1280]]) {
    const page = await chrome.page({ width, height: width < 800 ? 812 : 900, mobile: width < 800, dpr: 1, cpu: 4, throttle: { latency: 150, down: 200000, up: 93750 } });
    await page.send('Page.addScriptToEvaluateOnNewDocument', { source: SAMPLER });
    await page.goto(`${origin}/?lang=${lang}`);
    await sleep(7000);
    const f = JSON.parse(await page.eval('JSON.stringify(window.__f)'));
    const tag = `${lang} ${width}px`;
    expect('hero', f.length > 30, `${tag}: only ${f.length} frames were sampled`);
    expect('hero', f.every((x) => x.min === 1), `${tag}: the picture or an ancestor was below full opacity in ${f.filter((x) => x.min < 1).length} frames (min ${Math.min(...f.map((x) => x.min))}): the LCP picture must never be faded`);
    expect('hero', f.every((x) => x.filt === 'none'), `${tag}: a filter on the picture or an ancestor`);
    expect('hero', f.every((x) => x.sc <= 1.0301 && x.sc >= 0.9999), `${tag}: the picture scales to ${Math.max(...f.map((x) => x.sc))} (the charter allows 1.03)`);
    expect('hero', f.every((x) => x.rot === 'none' && !/matrix\(.*,\s*-?[1-9]/.test(x.tr.replace(/matrix\(1, 0, 0, 1,[^)]*\)/, ''))), `${tag}: the picture is rotated or skewed`);
    expect('hero', f.every((x) => x.chip === 1 && x.cap === 1), `${tag}: the honesty chip or the caption was below full opacity in some frame (chip min ${Math.min(...f.map((x) => x.chip))}, caption min ${Math.min(...f.map((x) => x.cap))})`);
    // the glint on the print face is one quiet sweep at .10 (spec 6.2, ledger 16.2 C). Its keyframes once shared a global name with the wall's glint, whose chunk arrives
    // after the first render and replaces the running keyframes (2026-10-05: a white slab at opacity 1 over the print face): so the painted opacity is read every frame,
    // after every chunk that could replace it, and the sweep must have been seen at all
    const gl = f.map((x) => x.gl).filter((x) => x >= 0);
    expect('hero', gl.length > 30, `${tag}: the glint element was not found`);
    expect('hero', Math.max(0, ...gl) <= 0.1005, `${tag}: the hero glint reached opacity ${Math.max(0, ...gl)} (the spec's sweep peaks at .10: a second @keyframes of the same name replaced it?)`);
    expect('hero', Math.max(0, ...gl) >= 0.05, `${tag}: the hero glint never showed (peak ${Math.max(0, ...gl)})`);
    const last = f.at(-1);
    expect('hero', last.sc === 1, `${tag}: the picture ends at scale ${last.sc}`);
    await page.close();
  }
  // one headline, real text, a space between phrases, no stray star, in every language
  for (const lang of LANGS) {
    const page = await open({ lang, width: 1280 });
    const s = JSON.parse(await page.eval(`JSON.stringify({ h1: document.querySelectorAll('h1').length, text: document.getElementById('h1').textContent, masks: [...document.querySelectorAll('#h1 .lp-line-mask')].length,
      stars: [...document.querySelectorAll('h1, h2, h3, .lp-lit')].filter((h) => /\\*/.test(h.textContent)).map((h) => h.textContent.slice(0, 30)),
      glued: [...document.querySelectorAll('h1, h2')].filter((h) => h.querySelectorAll('.lp-line-mask').length > 1 && /[,.;:!?][^\\s\\u00a0]/.test(h.textContent.replace(/\\d[.,]\\d/g, ''))).map((h) => h.textContent.slice(0, 40)),
      eyebrowSize: getComputedStyle(document.querySelector('.lp-hero .lp-eyebrow')).opacity })`));
    expect('hero', s.h1 === 1 && s.text.trim().length > 10, `${lang}: ${s.h1} h1 elements, text "${s.text}"`);
    expect('hero', s.stars.length === 0, `${lang}: a stray star in ${s.stars.join(' | ')}`);
    expect('hero', s.glued.length === 0, `${lang}: no space between phrases in ${s.glued.join(' | ')}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('hero'))) pass('hero', 'the picture is opaque, unfiltered, unrotated and at most 1.03 in every frame from the first; both honesty labels are visible from the first frame; headline is real text in all four languages');
}

// ---------------------------------------------------------------------------------------------------- header
async function checkHeader() {
  console.log('header');
  const page = await open({ lang: 'en', width: 1280, height: 800 });
  // the glass: solid after 24 px, in .5 s
  const top = JSON.parse(await page.eval("JSON.stringify({ solid: document.getElementById('hdr').classList.contains('lp-solid'), tp: getComputedStyle(document.getElementById('hdr')).transitionProperty, td: getComputedStyle(document.getElementById('hdr')).transitionDuration })"));
  expect('header', !top.solid, 'the header is already solid at the top of the page');
  expect('header', /background-color/.test(top.tp) && /0\.5s/.test(top.td), `the header's glass transition is "${top.tp}" over "${top.td}" (want background-color over .5 s)`);
  await page.eval("window.scrollTo({ top: 200, behavior: 'instant' })");
  await sleep(900);
  const solid = JSON.parse(await page.eval("JSON.stringify({ solid: document.getElementById('hdr').classList.contains('lp-solid'), bg: getComputedStyle(document.getElementById('hdr')).backgroundColor, blur: getComputedStyle(document.getElementById('hdr')).backdropFilter })"));
  expect('header', solid.solid && /rgba\(3, 4, 8, 0\.85\)/.test(solid.bg) && /blur\(24px\)/.test(solid.blur), `the glass after 24 px: ${JSON.stringify(solid)} (want rgba(3, 4, 8, .85) and blur 24 px)`);
  // the marker: under the link of the section being read, gone where there is no link
  const marker = async (sel) => {
    await page.eval(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); window.scrollTo({ top: e.getBoundingClientRect().top + scrollY - innerHeight * 0.3, behavior: 'instant' }); })()`);
    await sleep(1400);
    return JSON.parse(await page.eval(`JSON.stringify((() => { const cur = document.querySelector('.lp-nav a[aria-current]'), m = document.querySelector('.lp-nav-mark'); const mr = m.getBoundingClientRect(), cr = cur && cur.getBoundingClientRect();
      return { href: cur && cur.getAttribute('href'), mo: getComputedStyle(m).opacity, dx: cr ? Math.round(mr.left - cr.left) : null, dw: cr ? Math.round(mr.width - cr.width) : null, color: cur ? getComputedStyle(cur).color : null, other: getComputedStyle(document.querySelector('.lp-nav a:not([aria-current])')).color }; })())`));
  };
  const m1 = await marker('#pricing');
  expect('header', m1.href === '#pricing' && m1.mo === '1' && Math.abs(m1.dx) <= 1 && Math.abs(m1.dw) <= 1, `at the pricing section the marker is ${JSON.stringify(m1)} (want #pricing, visible, on the link)`);
  expect('header', m1.color !== m1.other, `the current link has the same colour as the others (${m1.color})`);
  const m2 = await marker('#trust');
  expect('header', m2.href === null && m2.mo === '0', `at the trust section (no link) the marker is ${JSON.stringify(m2)} (want none)`);
  // a language switch: the labels change width, the marker is measured again
  const m3 = await marker('#styles');
  expect('header', m3.href === '#styles', `at the styles section the current link is ${m3.href}`);
  await page.eval("document.querySelector('#langSeg button[lang=de]').click()");
  await sleep(1600);
  const m4 = JSON.parse(await page.eval(`JSON.stringify((() => { const cur = document.querySelector('.lp-nav a[aria-current]'), m = document.querySelector('.lp-nav-mark'); const mr = m.getBoundingClientRect(), cr = cur.getBoundingClientRect(); return { href: cur.getAttribute('href'), text: cur.textContent, dx: Math.round(mr.left - cr.left), dw: Math.round(mr.width - cr.width), n: getComputedStyle(document.getElementById('langSeg')).getPropertyValue('--n') }; })())`));
  expect('header', Math.abs(m4.dx) <= 1 && Math.abs(m4.dw) <= 1, `after switching to German the marker is off its link (${JSON.stringify(m4)})`);
  expect('header', m4.n.trim() === '1', `the language switch's place is --n ${m4.n} after choosing German (want 1)`);
  const ind = JSON.parse(await page.eval(`JSON.stringify((() => { const i = document.querySelector('.lp-seg-ind').getBoundingClientRect(), b = document.querySelector('#langSeg button[aria-pressed=true]').getBoundingClientRect(); return { dx: Math.round(i.left - b.left), dw: Math.round(i.width - b.width), pressed: document.querySelector('#langSeg button[aria-pressed=true]').lang }; })())`));
  expect('header', ind.pressed === 'de' && Math.abs(ind.dx) <= 2 && Math.abs(ind.dw) <= 2, `the pressed background is off the pressed button (${JSON.stringify(ind)})`);
  await page.close();
  // no horizontal overflow of the header with the menu button, at the narrow widths
  for (const [lang, w] of [['de', 320], ['hu', 320], ['en', 360], ['lt', 375], ['de', 640], ['en', 768], ['de', 959]]) {
    const p = await open({ lang, width: w, height: 700, settle: false });
    await sleep(500);
    const o = JSON.parse(await p.eval(`JSON.stringify((() => { const hr = document.querySelector('.lp-hdr .lp-wrap'); const kids = [...hr.querySelectorAll('.lp-logo, .lp-hdr-r > *')].filter((e) => e.getBoundingClientRect().width > 0); const R = kids.map((e) => e.getBoundingClientRect()); const bad = []; for (let i = 1; i < R.length; i++) if (R[i].left < R[i - 1].right - 0.5) bad.push(i); return { sw: document.documentElement.scrollWidth, iw: innerWidth, right: Math.max(...R.map((r) => r.right)), overlap: bad, btn: !!document.querySelector('#menuBtn') && getComputedStyle(document.querySelector('#menuBtn')).display }; })())`));
    expect('header', o.sw <= o.iw && o.right <= o.iw + 0.5 && o.overlap.length === 0, `${lang} ${w}px: the header overflows or its parts overlap (${JSON.stringify(o)})`);
    await p.close();
  }
  if (!problems.some((x) => x.startsWith('header'))) pass('header', 'glass .5 s, the marker follows the section, clears on a section with no link and re-measures after a language switch, the pressed background sits on its button, no overflow from 320 to 959 px');
}

// ---------------------------------------------------------------------------------------------------- menu
async function checkMenu() {
  console.log('menu');
  // before React has started: the main script blocked, only the static first screen
  const stat = await chrome.page({ width: 375, height: 812, mobile: true, dpr: 2 });
  await stat.send('Network.setBlockedURLs', { urls: ['*/assets/main-*.js'] });
  await stat.goto(`${origin}/?lang=en`);
  await stat.loaded();
  await sleep(1500);
  const before = JSON.parse(await stat.eval("JSON.stringify({ shell: !!document.getElementById('shell'), root: document.getElementById('root').childElementCount })"));
  if (!before.shell || before.root) fail('menu', `the test setup failed (${JSON.stringify(before)})`);
  await stat.eval("document.getElementById('menuBtn').focus(); document.getElementById('menuBtn').click()");   // a real tap focuses the button first
  await sleep(700);
  const s1 = JSON.parse(await stat.eval("JSON.stringify({ open: document.getElementById('menu').open, modal: document.getElementById('menu').matches(':modal'), exp: document.getElementById('menuBtn').getAttribute('aria-expanded'), focus: document.activeElement.className })"));
  expect('menu', s1.open && s1.modal && s1.exp === 'true', `before React: the menu did not open as a modal (${JSON.stringify(s1)})`);
  expect('menu', /lp-menu-x/.test(s1.focus), `before React: the focus is on "${s1.focus}" (want the close button inside the dialog)`);
  // the close button is a form method=dialog: no script involved (click it for real: a native submit)
  await stat.eval("document.querySelector('#menu .lp-menu-x').click()");
  await sleep(700);
  const s2 = JSON.parse(await stat.eval("JSON.stringify({ open: document.getElementById('menu').open, exp: document.getElementById('menuBtn').getAttribute('aria-expanded'), focus: document.activeElement.id })"));
  expect('menu', !s2.open && s2.exp === 'false' && s2.focus === 'menuBtn', `before React: the close button left it as ${JSON.stringify(s2)} (want closed, aria-expanded false, the focus back on the button)`);
  await stat.close();

  // the live page: a key, a link, a wide window
  const page = await open({ lang: 'en', width: 375, height: 812 });
  const key = async (k) => { await page.send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code: k, windowsVirtualKeyCode: 27 }); await page.send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code: k, windowsVirtualKeyCode: 27 }); await sleep(700); };
  await page.eval("document.getElementById('menuBtn').focus(); document.getElementById('menuBtn').click()");
  await sleep(700);
  const o1 = JSON.parse(await page.eval("JSON.stringify({ open: document.getElementById('menu').open, links: document.querySelectorAll('#menu nav a').length, scroll: getComputedStyle(document.documentElement).overflow })"));
  expect('menu', o1.open && o1.links === 6 && o1.scroll === 'hidden', `live: ${JSON.stringify(o1)} (want open, six links, the page behind locked)`);
  await key('Escape');
  const o2 = JSON.parse(await page.eval("JSON.stringify({ open: document.getElementById('menu').open, focus: document.activeElement.id, exp: document.getElementById('menuBtn').getAttribute('aria-expanded'), scroll: getComputedStyle(document.documentElement).overflow })"));
  expect('menu', !o2.open && o2.focus === 'menuBtn' && o2.exp === 'false' && o2.scroll !== 'hidden', `live: after Escape ${JSON.stringify(o2)}`);
  await page.eval("document.getElementById('menuBtn').click()");
  await sleep(600);
  await page.eval("document.querySelector('#menu nav a[href=\"#pricing\"]').click()");
  await sleep(1800);
  const o3 = JSON.parse(await page.eval("JSON.stringify({ open: document.getElementById('menu').open, hash: location.hash, top: Math.round(document.getElementById('pricing').getBoundingClientRect().top) })"));
  expect('menu', !o3.open && o3.hash === '#pricing' && Math.abs(o3.top) < 400, `live: after choosing Pricing ${JSON.stringify(o3)} (want closed, #pricing, the section in view)`);
  await page.eval("document.getElementById('menuBtn').click()");
  await sleep(500);
  await page.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
  await sleep(600);
  const o4 = await page.eval("document.getElementById('menu').open");
  expect('menu', o4 === false, 'live: a window grown to 1280 px left the dialog open');
  await page.close();
  if (!problems.some((x) => x.startsWith('menu'))) pass('menu', 'opens as a modal before React has started, the focus goes inside, the close button and Escape close it and return the focus, a link closes it, a wide window closes it');
}

// ---------------------------------------------------------------------------------------------------- handoff
async function checkHandoff() {
  console.log('handoff');
  const SAMPLER = `window.__s = []; window.__swap = null;
    new MutationObserver((_, o) => { if (!document.getElementById('shell') && document.getElementById('root') && document.getElementById('root').childElementCount) { window.__swap = Math.round(performance.now()); o.disconnect(); } }).observe(document, { childList: true, subtree: true });
    // sampled in a task after each frame's rendering (a timer set inside the animation callback), so what it reads is what was painted: reading in the
    // callback itself would see the state before the frame's own callbacks (the handoff's included) have run
    const sample = () => { const l = document.querySelector('.lp-hero .lp-lead'), s = document.querySelector('.lp-hero h1 .lp-line-mask > span'), c = document.querySelector('.lp-hero .lp-cta-row');
      if (l && s && c) { const ty = (e) => { const v = getComputedStyle(e).translate; const p = v.split(' '); return p.length > 1 ? parseFloat(p[1]) : 0; }; window.__s.push([Math.round(performance.now()), +getComputedStyle(l).opacity, ty(s), +getComputedStyle(c).opacity, ty(c)]); } };
    (function loop() { setTimeout(sample, 0); requestAnimationFrame(loop); })();`;
  const run = async (mutate) => {
    const page = await chrome.page({ width: 375, height: 812, mobile: true, dpr: 2, cpu: 4, throttle: { latency: 150, down: 200000, up: 93750 } });
    await page.send('Page.addScriptToEvaluateOnNewDocument', { source: (mutate ? 'Element.prototype.getAnimations = function () { return []; };' : '') + SAMPLER });
    await page.goto(`${origin}/?lang=en`);
    await sleep(7000);
    const v = JSON.parse(await page.eval('JSON.stringify({ s: window.__s, swap: window.__swap })'));
    await page.close();
    return v;
  };
  /** the frames after the swap: has anything gone back (opacity down, the headline or the button lower again)? */
  const jumps = (v) => {
    const out = [];
    for (let i = 1; i < v.s.length; i++) {
      const a = v.s[i - 1], b = v.s[i];
      if (b[1] < a[1] - 0.02) out.push(`lead opacity ${a[1]} to ${b[1]} at ${b[0]} ms`);
      if (b[2] > a[2] + 1) out.push(`headline ${a[2]} to ${b[2]} px at ${b[0]} ms`);
      if (b[3] < a[3] - 0.02) out.push(`button row opacity ${a[3]} to ${b[3]} at ${b[0]} ms`);
      if (b[4] > a[4] + 1) out.push(`button row ${a[4]} to ${b[4]} px at ${b[0]} ms`);
    }
    return out;
  };
  const good = await run(false);
  const midIntro = good.swap !== null && good.s.some((x) => x[0] < good.swap && x[1] > 0.05 && x[1] < 0.95);
  expect('handoff', good.swap !== null && good.s.length > 60, `the handoff or the sampler did not work (swap ${good.swap}, ${good.s.length} frames)`);
  const j = jumps(good);
  expect('handoff', j.length === 0, `the entrance started again when React took the page: ${j.slice(0, 4).join('; ')}`);
  if (!midIntro) console.log(`  note handoff: the swap came at ${good.swap} ms, after the entrance had finished: the test did not see a handoff in the middle of it (a slow machine makes it more likely)`);
  const bad = await run(true);
  const jb = jumps(bad);
  expect('handoff', jb.length > 0 || !midIntro, 'the deliberate defect (the adoption switched off) was NOT caught: the test cannot see a restarted entrance');
  if (!problems.some((x) => x.startsWith('handoff'))) pass('handoff', `no frame goes back across the handoff (${good.s.length} frames, swap at ${good.swap} ms${midIntro ? ', in the middle of the entrance' : ''}); with the adoption switched off the test sees ${jb.length} jumps`);
}

// ---------------------------------------------------------------------------------------------------- sheets
async function checkSheets() {
  console.log('sheets');
  for (const [w, h] of [[1280, 800], [375, 812]]) {
    const page = await open({ lang: 'en', width: w, height: h });
    const r = JSON.parse(await page.eval(`JSON.stringify((() => {
      const sheets = [...document.querySelectorAll('.lp-sheet')], top = (e) => e.getBoundingClientRect().top + scrollY, bottom = (e) => e.getBoundingClientRect().bottom + scrollY;
      const out = { n: sheets.length, rows: [], hero: null };
      const caps = [...document.querySelectorAll('.lp-hero-cap, .lp-micro, .lp-computer-hint, .lp-hero-fig')].map(bottom);
      out.hero = sheets.length ? Math.round(top(sheets[0]) - Math.max(...caps)) : null;
      sheets.forEach((s, i) => {
        const cs = getComputedStyle(s), last = s.lastElementChild, next = sheets[i + 1] || document.querySelector('.lp-final');
        out.rows.push({ cls: s.className.replace('lp-sheet ', ''), bg: cs.backgroundColor, radius: cs.borderTopLeftRadius, overflow: cs.overflow, rim: getComputedStyle(s, '::before').height, shadow: cs.boxShadow !== 'none',
          room: next ? Math.round(top(next) - bottom(last)) : null, secs: s.querySelectorAll(':scope > section').length });
      });
      return out;
    })())`));
    const tag = `${w}px`;
    expect('sheets', r.n === 3, `${tag}: ${r.n} sheets (want 3)`);
    const bgs = new Set(r.rows.map((x) => x.bg));
    expect('sheets', bgs.size === 2 && r.rows[0].bg === r.rows[2].bg && r.rows[0].bg !== r.rows[1].bg, `${tag}: the sheet tones are ${[...bgs].join(' | ')} (want A and D alike, C another)`);
    expect('sheets', r.rows.every((x) => x.overflow === 'visible' && x.rim === '1px' && x.shadow && x.radius === (w >= 1024 ? '32px' : '24px')), `${tag}: a sheet has the wrong overflow (it must stay visible: a clip stops native lazy loading of the pictures of a horizontal rail), rim, shadow or radius: ${JSON.stringify(r.rows)}`);
    expect('sheets', r.rows.every((x) => x.secs > 0), `${tag}: a sheet holds no section`);
    expect('sheets', r.rows.every((x) => x.room === null || x.room <= 0.5), `${tag}: the next piece starts below a sheet's last section (${JSON.stringify(r.rows.map((x) => x.room))}): the overlap would lie over content`);
    expect('sheets', r.hero !== null && r.hero >= 16, `${tag}: the first sheet starts ${r.hero} px below the hero's last line (want 16 px or more: it rolls over padding only)`);
    // every sticky element sticks: a plateau of samples at its top offset while its container is long enough
    const st = JSON.parse(await page.eval(`(async () => {
      const out = [];
      const els = [...document.querySelectorAll('body *')].filter((e) => getComputedStyle(e).position === 'sticky' && e.getBoundingClientRect().width > 0);
      for (const e of els) {
        const cs = getComputedStyle(e), want = parseFloat(cs.top), box = e.parentElement.getBoundingClientRect();
        const room = box.height - e.getBoundingClientRect().height;
        if (!(room > 120)) { out.push({ el: e.tagName + '.' + String(e.className).slice(0, 24), skipped: Math.round(room) }); continue; }
        const y0 = box.top + scrollY - want, hits = [];
        for (let k = 0; k * 40 <= room; k++) { window.scrollTo({ top: y0 + k * 40, behavior: 'instant' }); await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); hits.push(Math.abs(e.getBoundingClientRect().top - want) <= 0.6); }
        out.push({ el: e.tagName + '.' + String(e.className).slice(0, 24), want, stuck: hits.filter(Boolean).length, of: hits.length });
      }
      window.scrollTo({ top: 0, behavior: 'instant' });
      return JSON.stringify(out);
    })()`));
    for (const x of st) if (!x.skipped) expect('sheets', x.stuck >= Math.min(3, Math.floor(x.of / 2)), `${tag}: the sticky ${x.el} does not stick inside the sheet (${x.stuck} of ${x.of} samples at its top offset)`);
    console.log(`  note sheets ${tag}: ${st.length} sticky elements: ${st.map((x) => `${x.el} ${x.skipped !== undefined ? 'no room' : `${x.stuck}/${x.of}`}`).join(', ')}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('sheets'))) pass('sheets', 'three sheets with their tones, rim, radius and shadow; nothing of the content under an overlap; every sticky element still sticks');
}

// ---------------------------------------------------------------------------------------------------- gold
async function checkGold() {
  console.log('gold');
  const CENSUS = `JSON.stringify((() => {
    const gold = (c) => { const m = c.match(/rgba?\\((\\d+), (\\d+), (\\d+)(?:, ([\\d.]+))?\\)/); return !!m && (m[4] === undefined || +m[4] > .4) && +m[1] > 200 && +m[2] > 150 && +m[3] < 135 && +m[1] - +m[3] > 100; };
    const ownText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    const chrome = (el) => !!el.closest('.lp-topbar, .lp-hdr, .lp-menu, .lp-skip');
    const out = { text: [], fill: [], line: [] };
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect(); if (!(r.width > 0 && r.bottom > 0 && r.top < innerHeight) || chrome(el)) continue;
      const tag = el.tagName + '.' + String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className).slice(0, 30);
      const s = getComputedStyle(el);
      if (ownText(el) && gold(s.color)) out.text.push(tag);
      if (gold(s.backgroundColor)) out.fill.push(tag);
      if (parseFloat(s.borderTopWidth) > 0 && gold(s.borderTopColor)) out.line.push(tag);
      for (const p of ['::before', '::after']) { const q = getComputedStyle(el, p); if (q.content !== 'none') { if (gold(q.backgroundColor)) out.line.push(tag + p); if (parseFloat(q.borderTopWidth) > 0 && gold(q.borderTopColor)) out.line.push(tag + p); } }
    }
    return out;
  })())`;
  for (const [w, h, lang] of [[1280, 800, 'en'], [390, 844, 'en'], [1280, 800, 'hu']]) {
    const page = await open({ lang, width: w, height: h, settle: false });
    await sleep(6000);
    const c = JSON.parse(await page.eval(CENSUS));
    const groups = ['text', 'fill', 'line'].filter((k) => c[k].length > 0);
    expect('gold', groups.length <= 3, `${lang} ${w}px: ${groups.length} gold groups`);
    expect('gold', c.text.length <= 2, `${lang} ${w}px: gold text on ${c.text.length} elements (${c.text.join(', ')}): only an accent word or full stop per heading is allowed (BR-1)`);
    console.log(`  note gold ${lang} ${w}px: text ${c.text.length} (${c.text.join(', ')}), fills ${c.fill.length} (${c.fill.join(', ')}), lines and rings ${c.line.length}`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('gold'))) pass('gold', 'at most three gold groups on the first screen, chrome excluded, gold text only on an accent word or full stop');
}

// ---------------------------------------------------------------------------------------------------- overflow
async function checkOverflow() {
  console.log('overflow');
  for (const w of [320, 390]) {
    for (const lang of LANGS) {
      const page = await open({ lang, width: w, height: w === 320 ? 568 : 844 });
      await scrollThrough(page, 120);
      await page.eval("window.scrollTo({ top: 0, behavior: 'instant' })");
      await sleep(1500);
      const r = JSON.parse(await page.eval(`JSON.stringify({
        wide: [...document.querySelectorAll('h1,h2,h3')].filter((h) => h.scrollWidth > h.clientWidth + 1 || [...h.querySelectorAll('.lp-line-mask > span')].some((s) => s.scrollWidth > h.clientWidth + 1)).map((h) => h.textContent.slice(0, 40)),
        sw: document.documentElement.scrollWidth, iw: innerWidth })`));
      expect('overflow', r.wide.length === 0 && r.sw <= r.iw, `${lang} ${w}px: headings wider than their box: ${r.wide.join(' | ')}, page ${r.sw} of ${r.iw} px`);
      await page.close();
    }
  }
  if (!problems.some((x) => x.startsWith('overflow'))) pass('overflow', 'no headline wider than its box and no horizontal scroll at 320 and 390 px in en, de, lt, hu');
}

// ---------------------------------------------------------------------------------------------------- skip
async function checkSkip() {
  console.log('skip');
  // The chapters below the first screen are skipped until they are near the screen (content-visibility: auto, css/base.css) and stand in for the height their slot had
  // (src/App.tsx). Three claims: it is really on (a far section's content is not rendered while the visitor is at the top: take the rule away and this fails), the page does
  // not change height when the sections are drawn (the intrinsic size is the CONTENT box: forgetting the sections' own padding made the page 1,000 px too tall on a desktop
  // until it had been scrolled), and a jump to a section lands on it (the offsets above it are estimates).
  for (const [lang, width] of [['en', 1280], ['de', 768], ['lt', 375], ['hu', 1280]]) {
    const tag = `${lang} ${width}px`;
    const page = await open({ lang, width, height: 900 });
    await sleep(600);
    const top = JSON.parse(await page.eval(`JSON.stringify({ h: document.documentElement.scrollHeight,
      on: ['wall', 'styles', 'how', 'pricing', 'closeups', 'trust', 'faq', 'final'].map((id) => [id, getComputedStyle(document.getElementById(id)).contentVisibility, document.getElementById(id).firstElementChild.checkVisibility({ contentVisibilityAuto: true })]),
      reveal: getComputedStyle(document.getElementById('reveal')).contentVisibility })`));
    expect('skip', top.on.every(([, cv]) => cv === 'auto'), `${tag}: content-visibility is not auto on ${top.on.filter(([, cv]) => cv !== 'auto').map((x) => x[0]).join(', ')}`);
    expect('skip', top.on.filter(([id, , vis]) => ['pricing', 'closeups', 'trust', 'faq'].includes(id) && vis).length === 0, `${tag}: a section far below the screen is rendered at the top of the page: ${top.on.filter(([, , vis]) => vis).map((x) => x[0]).join(', ')}`);
    expect('skip', top.reveal !== 'auto', `${tag}: the pinned Reveal is skipped (its sticky stage must always be laid out)`);
    // a jump to a section lands on it, whatever has been drawn above it
    for (const id of ['how', 'pricing', 'faq']) {
      await page.eval(`window.scrollTo({ top: 0, behavior: 'instant' })`);
      await sleep(300);
      await page.eval(`document.getElementById(${JSON.stringify(id)}).scrollIntoView({ behavior: 'instant', block: 'start' })`);
      await sleep(1200);
      const r = JSON.parse(await page.eval(`JSON.stringify({ top: Math.round(document.getElementById(${JSON.stringify(id)}).getBoundingClientRect().top), head: Math.round(document.querySelector('#${id} h2').getBoundingClientRect().top) })`));
      expect('skip', r.head >= 0 && r.head < 700, `${tag}: after a jump to #${id} its heading is ${r.head} px from the top of the screen (the section's top is at ${r.top} px)`);
    }
    // the page keeps its height from the first moment to the end of a full scroll
    await scrollThrough(page, 220);
    await sleep(800);
    const h1 = await page.eval('document.documentElement.scrollHeight');
    const drift = Math.abs(h1 - top.h) / h1;
    expect('skip', drift <= 0.035, `${tag}: the page is ${top.h} px tall before anything has been drawn and ${h1} px after a full scroll (${(drift * 100).toFixed(1)} percent: the sections' stand-in heights are off)`);
    console.log(`  note skip ${tag}: ${top.h} px before, ${h1} px after (${(drift * 100).toFixed(1)} percent)`);
    await page.close();
  }
  if (!problems.some((x) => x.startsWith('skip'))) pass('skip', 'the chapters below the first screen are skipped until near, the pinned Reveal is not, a jump lands on its section and the page keeps its height within 3.5 percent');
}

// ---------------------------------------------------------------------------------------------------- run
const checks = { reduced: checkReduced, nojs: checkNoJs, failsafe: checkFailsafe, engine: checkEngine, hero: checkHero, header: checkHeader, menu: checkMenu, handoff: checkHandoff, sheets: checkSheets, gold: checkGold, overflow: checkOverflow, skip: checkSkip };
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
console.log(problems.length ? `\nmotion check FAILED (${problems.length}):\n  ${problems.join('\n  ')}` : '\nmotion check ok');
process.exit(problems.length ? 1 : 0);
