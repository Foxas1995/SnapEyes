// The checks of the motion of /try and /order (docs: the motion spec, sections 7, 8, 5.5, 11 and the Artwork Charter 2.2), in real Chrome, against a build
// (dist/) served the way Vercel serves it, with the API of the tools stood in for (scripts/lib/flowstub.mjs: the models are stubbed, nothing leaves this machine,
// every answer takes a moment so that the waiting screens can be looked at). Not part of `vite build` (it needs Chrome and a few minutes); run it after a build:
//   npm run build && npm run check:motion:flow
//   node scripts/check_motion_flow.mjs [--dist dist] [--only reduced,loops,arc,aperture,crossfade,order,slider,arrival,failsafe,shift,wiring,bundle] [--mutate-css "from@@to"]
// --mutate-css changes every stylesheet of the build on its way to the browser (every occurrence of `from` becomes `to`): a deliberate defect, to see that a check
// really fails. Example: replacing the reduced-motion clamp of the first rule (`:root:has(>body.fx) *{scroll-behavior:auto!important;transition-duration:.01ms!important;transition-delay:0s!important;animation:none!important}`) with
// `.wk-arc{animation:wk-rot 3.2s linear infinite}` takes the safety net away and leaks a loop into reduced motion: the `reduced` check must fail on the arc.
// (Taking the clamp away alone changes nothing: every moving rule is inside prefers-reduced-motion: no-preference anyway, the clamp is the second line of defence.)
// What it checks (each name is a value of --only):
//   reduced    prefers-reduced-motion: reduce, the whole flow of /try (capture, waiting, result) and of /order (making, ready): nothing animates at any moment, the
//              diagram, the checks and the rings are drawn, the arc stands still at 12 o'clock, the preview is there at once and never clipped, the slider rests at 50
//   loops      with motion: nothing loops at rest, the waiting screens hold exactly ONE loop (the arc: 22 percent of a ring, 1.5 px, 3.2 s, linear), a composing frame
//              one (the hairline), and the page never has more than one at any frame of the flow (BR-3)
//   arc        the waiting arc's own numbers, the customer's crop standing still (no filter, no glow, no animation on it), the real steps (a drawn check per finished
//              one, a still dot, the real seconds), the arc paused in a hidden tab
//   aperture   the first display of an artwork opens from the centre, circle(0) to circle(75) in 1.3 s, never before the picture has decoded, the watermarked picture
//              the server sent and no other, the frame's border back to rest; it never plays again for a style change; never on a restored session
//   crossfade  a second style: a second layer of opacity only, no scale, no clip, no blur, gone when it is over
//   order      /order: a ring per eye (dim, the arc, closed in the success colour with its check), the status dot (no spinner), the waiting hairline, the ready reveal
//              (the aperture after the picture has decoded, the hairline that passes once around the button), a page opened already ready (the picture there at the
//              first frame, never faded, only the words fade; the largest paint is the picture)
//   slider     the plain before and after slider sweeps once in every shape of window a customer really has (a phone upright and held sideways, a page zoomed to 200
//              percent, a short window): where the slider is taller than the window the window need only show 60 percent of what it can; a slider that is only part in
//              the window counts as seen after 3.5 s, one that is not in the window waits (review I3, M1)
//   arrival    the aperture is an event that is spent: it runs once, and a style chosen while it runs spends it too, so that the frame never opens again (review I3, m4);
//              a slow decode leaves the frame the composing status and hairline, never a black frame with nothing in it (m1)
//   failsafe   a decode that never comes, a browser that blocks every animation, an IntersectionObserver that never reports, a hidden tab: the picture is there
//              within 3.5 s, the slider is not left half hidden, nothing stays hidden, nothing stays clipped
//   shift      the layout shifts of the whole flow with motion are the same as with reduced motion (motion adds none: it moves transform, opacity and clip only)
//   wiring     the head script that skips the page transition for an order, a payment or the withdrawal form is in both pages; no html.mo (nothing is hidden until
//              a script reveals it); the landing's engine is not loaded by the tools
//   bundle     the first-load bytes of /try and /order (gzip): the motion adds at most the budget of the spec (CSS +2 kB each) and the numbers are printed
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';
import { flowApi } from './lib/flowstub.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const only = opt('--only') ? new Set(opt('--only').split(',')) : null;
const wants = (name) => !only || only.has(name);
const PHOTO = join(ROOT, 'public', 'assets', 'sample_eye_blue_1789706902835.jpg');   // the site's own AI-generated sample eye: an image file the file input can take
const KEY = 'a'.repeat(32);

const problems = [];
const fail = (check, msg) => { problems.push(`${check}: ${msg}`); console.log(`  FAIL ${check}: ${msg}`); };
const pass = (check, msg) => console.log(`  ok   ${check}: ${msg}`);
const expect = (check, cond, msg, okMsg = '') => { if (!cond) fail(check, msg); else if (okMsg) pass(check, okMsg); return !!cond; };

const api = flowApi(ROOT);
const mutate = opt('--mutate-css') ? opt('--mutate-css').split('@@') : null;
const handler = (req, res) => {
  const path = req.url.split('?')[0];
  if (mutate && /^\/assets\/[^/]+\.css$/.test(path) && existsSync(join(dist, path))) {
    res.writeHead(200, { 'content-type': 'text/css; charset=utf-8', 'cache-control': 'no-store' });
    res.end(readFileSync(join(dist, path), 'utf8').split(mutate[0]).join(mutate[1]));
    return true;
  }
  return api.handler(req, res);
};
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch();
const errorsOf = new WeakMap();

// ---------------------------------------------------------------------------------------------------- helpers
async function open(path, { width = 375, height = 812, reduceMotion = false, pre = '', ...more } = {}) {
  const page = await chrome.page({ width, height, mobile: width < 800, dpr: 1, reduceMotion, vitals: true, ...more });
  const errors = [];
  errorsOf.set(page, errors);
  page.on((e) => {
    if (e.method === 'Runtime.exceptionThrown') errors.push((e.params.exceptionDetails.exception?.description || e.params.exceptionDetails.text || '').split('\n')[0]);
    else if (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error') errors.push(e.params.args.map((a) => a.value || a.description || '').join(' '));
  });
  if (pre) await page.send('Page.addScriptToEvaluateOnNewDocument', { source: pre });
  await page.goto(`${origin}${path}`);
  await page.loaded();
  return page;
}
const waitFor = async (page, expr, ms = 20000, step = 40) => {
  const t0 = Date.now();
  for (;;) {
    let v = false;
    try { v = await page.eval(expr); } catch { /* navigating */ }
    if (v) return true;
    if (Date.now() - t0 > ms) return false;
    await sleep(step);
  }
};
async function setFile(page, selector, path) {
  const { root } = await page.send('DOM.getDocument', { depth: 0 });
  const { nodeId } = await page.send('DOM.querySelector', { nodeId: root.nodeId, selector });
  await page.send('DOM.setFileInputFiles', { files: [path], nodeId });
}
/** records `expr` at every frame into window.__rec until stopped; read it back with rec(page) */
const startRec = (page, expr, cap = 900) => page.eval(`window.__rec = []; window.__gen = (window.__gen || 0) + 1; window.__t0 = performance.now(); ((gen, rows) => { (function f() { if (window.__gen !== gen) return; try { rows.push([Math.round(performance.now() - window.__t0), (${expr})]); } catch (e) { rows.push([0, null]); } if (rows.length < ${cap}) requestAnimationFrame(f); })(); })(window.__gen, window.__rec)`);
const rec = async (page) => { await page.eval('window.__gen = (window.__gen || 0) + 1'); return JSON.parse(await page.eval('JSON.stringify(window.__rec)')); };
const ANIMS = `document.getAnimations().map((a) => { const t = a.effect.getComputedTiming(); return { n: a.animationName || ('transition:' + a.transitionProperty), loop: t.iterations === Infinity, dur: t.duration, ease: t.easing, state: a.playState, on: a.effect.target && a.effect.target.className && a.effect.target.className.baseVal !== undefined ? a.effect.target.className.baseVal : (a.effect.target && a.effect.target.className) || '' }; })`;
const anims = async (page) => JSON.parse(await page.eval(`JSON.stringify(${ANIMS})`));
const running = (a) => a.filter((x) => x.state === 'running');

/** The flow of /try up to `stage`: capture, a photo, the two waiting screens, the result and its artwork. Returns when the stage is on screen. */
async function walkTry(page, stage) {
  await sleep(2800);   // the capture screen has finished its own entrance
  if (stage === 'capture') return true;
  await setFile(page, 'input[type=file][multiple]', PHOTO);
  if (stage === 'analyzing') return waitFor(page, "!!document.querySelector('.wk-disc')", 10000);
  if (!(await waitFor(page, "!!document.querySelector('.wk-disc .crop img')", 20000))) return false;
  if (stage === 'processing') return true;
  return waitFor(page, "!!document.querySelector('[data-testid=artwork]')", 30000);
}
const imgInFrame = "(() => { const f = document.querySelector('[data-testid=artwork]'); return f ? [...f.querySelectorAll('img')] : []; })()";

// ---------------------------------------------------------------------------------------------------- reduced
async function checkReduced() {
  console.log('reduced');
  const page = await open('/try?lang=de', { reduceMotion: true });
  await startRec(page, `document.getAnimations().length + '|' + document.documentElement.className`, 2400);
  expect('reduced', await walkTry(page, 'capture'), 'the capture screen did not come');
  const cap = await page.eval(`JSON.stringify({ anims: document.getAnimations().length, offsets: [...document.querySelectorAll('.fx-diagram .dr')].map((p) => getComputedStyle(p).strokeDashoffset), rest: getComputedStyle(document.querySelector('.fx-diagram .rest')).opacity })`);
  const c = JSON.parse(cap);
  expect('reduced', c.anims === 0 && c.offsets.length === 7 && c.offsets.every((o) => o === '0px') && c.rest === '1', `capture: ${cap}`, 'the capture diagram is drawn at once, nothing animates');
  await setFile(page, 'input[type=file][multiple]', PHOTO);
  expect('reduced', await waitFor(page, "!!document.querySelector('.wk-disc .crop img')", 20000), 'the processing screen did not come');
  await sleep(500);
  const proc = JSON.parse(await page.eval(`JSON.stringify({ anims: document.getAnimations().length, arcAnim: getComputedStyle(document.querySelector('.wk-arc')).animationName, dash: getComputedStyle(document.querySelector('.wk-arc circle')).strokeDasharray, turn: getComputedStyle(document.querySelector('.wk-arc')).rotate, ticks: [...document.querySelectorAll('.wk-tick path')].map((p) => getComputedStyle(p).strokeDashoffset) })`));
  expect('reduced', proc.anims === 0 && proc.arcAnim === 'none' && /^22(px)?,? 78(px)?$/.test(proc.dash) && (proc.turn === 'none' || proc.turn === '0deg') && proc.ticks.every((t) => t === '0px'), `processing: ${JSON.stringify(proc)}`, 'processing: the arc stands still at 12 o\'clock (22 78), the checks are drawn');
  expect('reduced', await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000), 'the artwork did not come');
  await startRec(page, `(() => { const f = document.querySelector('[data-testid=artwork]'); const i = f && f.querySelector('img'); return i ? [getComputedStyle(i).clipPath, i.className, f.querySelectorAll('img').length].join('|') : 'none'; })()`, 300);
  await sleep(1800);
  const frames = (await rec(page)).map((r) => r[1]);
  expect('reduced', frames.length > 20 && frames.every((f) => f === 'none' || (f.startsWith('none|') && !/fx-open|fx-xfade/.test(f) && f.endsWith('|1'))), `the artwork frames: ${[...new Set(frames)].join(' ; ')}`, `the preview is there at the first frame, one picture, never clipped or faded (${frames.length} frames)`);
  const rest = JSON.parse(await page.eval(`JSON.stringify({ anims: document.getAnimations().length, hair: [...document.querySelectorAll('.fx-hair')].map((h) => getComputedStyle(h).animationName), mo: document.documentElement.classList.contains('mo'), slider: (() => { const s = [...document.querySelectorAll('.cursor-ew-resize')][0]; return s ? [...s.querySelectorAll('img')][1].style.clipPath : 'none present'; })() })`));
  expect('reduced', rest.anims === 0 && !rest.mo && (rest.slider === 'inset(0px 0px 0px 50%)' || rest.slider === 'inset(0 0 0 50%)' || /^none/.test(rest.slider)), `result: ${JSON.stringify(rest)}`, 'the result rests: no animation, the plain slider at 50');
  expect('reduced', (errorsOf.get(page) || []).length === 0, `console errors: ${(errorsOf.get(page) || []).join(' | ')}`);
  await page.close();

  // /order, reduced: making and ready
  api.setOrder({ scenario: 'making', eyes: 2, made: 0 });
  const o = await open(`/order?o=i3check&k=${KEY}&lang=en`, { reduceMotion: true, width: 1280, height: 900 });
  expect('reduced', await waitFor(o, "!!document.querySelector('[data-testid=state-making]')", 20000), 'the making card did not come');
  await sleep(600);
  const mk = JSON.parse(await o.eval(`JSON.stringify({ anims: document.getAnimations().length, arcs: [...document.querySelectorAll('.wk-arc')].map((a) => getComputedStyle(a).animationName), dot: !!document.querySelector('[data-testid=making-line] .fx-dot'), spin: !!document.querySelector('.animate-spin, .animate-pulse') })`));
  expect('reduced', mk.anims === 0 && mk.arcs.length >= 1 && mk.arcs.every((n) => n === 'none') && mk.dot && !mk.spin, `making: ${JSON.stringify(mk)}`, 'making: the arcs stand still, the status is a still dot');
  expect('reduced', await waitFor(o, "!!document.querySelector('[data-testid=eye-1] .wk-ring .on')", 20000), 'eye 1 was not made');
  const ring = JSON.parse(await o.eval(`JSON.stringify({ fresh: !!document.querySelector('.fx-fresh'), anims: document.getAnimations().length, dash: getComputedStyle(document.querySelector('[data-testid=eye-1] .wk-ring .on')).strokeDashoffset })`));
  expect('reduced', ring.anims <= 1 && ring.dash === '0px', `ring: ${JSON.stringify(ring)}`, 'a made eye\'s ring is closed at once (a transition on the progress bar width may run: it ends in .01 ms)');
  await startRec(o, `(() => { const i = document.querySelector('[data-testid=state-ready] img'); return i ? [getComputedStyle(i).clipPath, i.className, getComputedStyle(i).opacity].join('|') : 'none'; })()`, 600);
  expect('reduced', await waitFor(o, "!!document.querySelector('[data-testid=state-ready] img')", 40000), 'the ready card did not come');
  await sleep(1500);
  const fr = (await rec(o)).map((r) => r[1]).filter((f) => f !== 'none');
  expect('reduced', fr.length > 10 && fr.every((f) => f.startsWith('none|') && f.endsWith('|1')) && (await o.eval('document.getAnimations().length')) === 0, `the picture frames: ${[...new Set(fr)].join(' ; ')}`, 'ready: the picture is there at the first frame, never clipped, nothing animates, no ring passes');
  expect('reduced', (errorsOf.get(o) || []).length === 0, `console errors: ${(errorsOf.get(o) || []).join(' | ')}`);
  await o.close();
}

// ---------------------------------------------------------------------------------------------------- loops, arc, aperture, crossfade (one flow with motion)
async function checkTryWithMotion() {
  console.log('loops, arc, aperture, crossfade');
  const page = await open('/try?lang=en');
  await startRec(page, `JSON.stringify(document.getAnimations().filter((a) => a.effect.getComputedTiming().iterations === Infinity && a.playState === 'running').map((a) => a.animationName))`, 2600);
  expect('loops', await walkTry(page, 'capture'), 'the capture screen did not come');
  // rest: nothing loops, nothing runs
  const restA = await anims(page);
  expect('loops', restA.length === 0, `the capture screen is at rest after its entrance, ${restA.length} animation(s) still run: ${restA.map((a) => a.n).join()}`, 'the capture screen is at rest after its own entrance: no animation at all');
  await setFile(page, 'input[type=file][multiple]', PHOTO);
  expect('loops', await waitFor(page, "!!document.querySelector('.wk-disc')", 10000), 'the analysing screen did not come');
  await sleep(150);
  const an = JSON.parse(await page.eval(`JSON.stringify({ bare: !!document.querySelector('.wk-bare'), ticks: document.querySelectorAll('.wk-tick').length, dots: document.querySelectorAll('.fx-dot').length, live: document.querySelector('ul[aria-live]') && document.querySelector('ul[aria-live]').getAttribute('aria-live') })`));
  expect('arc', an.bare && an.ticks === 0 && an.dots === 2 && an.live === 'polite', `analysing: ${JSON.stringify(an)}`, 'analysing: one thin ring with the arc, two steps in hand (two dots, no check yet), announced politely');
  expect('arc', await waitFor(page, "!!document.querySelector('.wk-disc .crop img')", 20000), 'the processing screen did not come');
  await sleep(1300);
  const proc = JSON.parse(await page.eval(`JSON.stringify((() => {
    const arc = document.querySelector('.wk-disc .wk-arc'), circ = arc.querySelector('circle'), crop = document.querySelector('.wk-disc .crop'), img = crop.querySelector('img');
    const cs = getComputedStyle(circ), r = arc.getBoundingClientRect();
    const own = img.getAnimations({ subtree: false }).length + crop.getAnimations({ subtree: false }).length + document.querySelector('.wk-disc').getAnimations({ subtree: false }).length;
    return { pathLength: circ.getAttribute('pathLength'), dash: cs.strokeDasharray, width: cs.strokeWidth, size: Math.round(parseFloat(getComputedStyle(arc).width) || r.width), turn: arc.getAnimations()[0] && { n: arc.getAnimations()[0].animationName, dur: arc.getAnimations()[0].effect.getComputedTiming().duration, ease: arc.getAnimations()[0].effect.getComputedTiming().easing, it: arc.getAnimations()[0].effect.getComputedTiming().iterations === Infinity ? 'inf' : 1 },
      cropFilter: getComputedStyle(img).filter, cropShadow: getComputedStyle(crop).boxShadow, imgShadow: getComputedStyle(img).boxShadow, own, stroke: cs.stroke,
      lines: [...document.querySelectorAll('ul[aria-live] li')].map((l) => [!!l.querySelector('.wk-tick'), !!l.querySelector('.fx-dot'), l.textContent.trim()]), secs: document.querySelector('.tabular-nums').textContent, tnum: getComputedStyle(document.querySelector('.tabular-nums')).fontVariantNumeric,
      spinners: document.querySelectorAll('.animate-spin, .animate-pulse').length, bars: document.querySelectorAll('[role=progressbar]').length };
  })())`));
  expect('arc', proc.pathLength === '100' && /^22(px)?,? 78(px)?$/.test(proc.dash) && proc.width === '1.5px' && proc.size === 172 && proc.turn && proc.turn.n === 'wk-rot' && proc.turn.dur === 3200 && proc.turn.ease === 'linear' && proc.turn.it === 'inf',
    `the arc: ${JSON.stringify(proc)}`, 'the arc is 22 percent of a ring (22 78 of pathLength 100), 1.5 px, 3.2 s, linear, forever');
  expect('arc', proc.cropFilter === 'none' && proc.own === 0 && !/245, 197, 66/.test(proc.cropShadow + proc.imgShadow) && proc.spinners === 0 && proc.bars === 0,
    `the customer's photo: filter ${proc.cropFilter}, shadow ${proc.cropShadow}, animations on it ${proc.own}, spinners ${proc.spinners}, bars ${proc.bars}`, 'the customer\'s own crop stands still: no animation, no filter, no glow, no pulse; no progress bar, no percentage');
  expect('arc', proc.lines.length >= 2 && proc.lines.slice(0, -1).every((l) => l[0] && !l[1]) && proc.lines.at(-1)[1] && !proc.lines.at(-1)[0] && /^\d+ ?s$/.test(proc.secs.trim()) && /tabular/.test(proc.tnum),
    `the steps: ${JSON.stringify(proc.lines)} ${proc.secs} ${proc.tnum}`, 'the real steps: a drawn check for every finished one, a still dot for the one in hand, the real seconds in tabular figures');
  const during = (await anims(page)).filter((a) => a.state === 'running');
  expect('loops', during.filter((a) => a.loop).length === 1 && during.find((a) => a.loop).n === 'wk-rot', `loops while processing: ${during.map((a) => a.n + (a.loop ? ' (loop)' : '')).join()}`, 'processing: exactly one loop, the arc');
  // a hidden tab pauses the arc
  await page.eval(`Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange'))`);
  await sleep(100);
  const hid = JSON.parse(await page.eval(`JSON.stringify({ away: document.documentElement.hasAttribute('data-away'), state: document.querySelector('.wk-arc').getAnimations()[0].playState })`));
  await page.eval(`delete document.hidden; document.dispatchEvent(new Event('visibilitychange'))`);
  await sleep(100);
  const back = JSON.parse(await page.eval(`JSON.stringify({ away: document.documentElement.hasAttribute('data-away'), state: document.querySelector('.wk-arc').getAnimations()[0].playState })`));
  expect('arc', hid.away && hid.state === 'paused' && !back.away && back.state === 'running', `hidden tab: ${JSON.stringify(hid)} back: ${JSON.stringify(back)}`, 'a hidden tab pauses the arc, coming back runs it again');

  // the result: the aperture frame by frame
  await startRec(page, `(() => { const f = document.querySelector('[data-testid=artwork]'); if (!f) return null; const i = f.querySelector('img'); return { img: i ? [getComputedStyle(i).clipPath, i.className, i.getAttribute('src').slice(-24), f.querySelectorAll('img').length] : null, border: getComputedStyle(f).borderTopColor, hair: !!f.querySelector('.fx-hair'), status: [...f.querySelectorAll('[role=status]')].map((s) => s.textContent) }; })()`, 1500);
  expect('aperture', await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 30), 'the artwork did not come');
  await sleep(2000);
  const R = (await rec(page)).filter((r) => r[1]);
  const comp = R.filter((r) => !r[1].img);
  const withImg = R.filter((r) => r[1].img);
  const composing = comp.filter((r) => r[1].hair), gap = comp.filter((r) => !r[1].hair);
  expect('loops', composing.length > 5 && composing.every((r) => r[1].status.length === 1 && r[1].status[0].length > 0) && gap.length === 0,
    `composing frames: ${composing.length} with the hairline, ${gap.length} without (a black frame with no status while the picture decodes): ${[...new Set(comp.map((r) => JSON.stringify([r[1].hair, r[1].status])))].join(' ; ')}`,
    `composing: the hairline and one status line for a screen reader in all ${composing.length} frames before the picture, the decode of the picture included (the frame is never black and mute); then it opens`);
  const clips = withImg.map((r) => parseFloat((/circle\(([\d.]+)%/.exec(r[1].img[0]) || [])[1] ?? NaN)).filter((x) => !Number.isNaN(x));
  const first = withImg[0];
  const opening = withImg.filter((r) => /circle/.test(r[1].img[0]));
  const dur = opening.length ? opening.at(-1)[0] - opening[0][0] : 0;
  expect('aperture', first && /circle\(0%\)/.test(first[1].img[0]) && /fx-open/.test(first[1].img[1]), `the first frame of the picture: ${first && first[1].img.join(' | ')}`, 'the picture is put in with its clip already at circle(0): never a frame of the whole picture before the opening');
  expect('aperture', clips.length > 30 && clips.every((v, i) => i === 0 || v >= clips[i - 1] - 0.01) && Math.max(...clips) > 72 && Math.max(...clips) <= 75.01, `radius series: ${clips.slice(0, 5)} ... ${clips.slice(-3)}, max ${Math.max(...clips)}`, `the aperture opens monotonically from circle(0) to circle(75) (${clips.length} frames)`);
  expect('aperture', dur > 1000 && dur < 1650, `the opening took ${dur} ms`, `the opening takes ${dur} ms (the token says 1300)`);
  const lastImg = withImg.at(-1)[1];
  expect('aperture', lastImg.img[0] === 'none' && !/fx-open|fx-xfade/.test(lastImg.img[1]) && lastImg.img[3] === 1 && withImg.every((r) => r[1].img[3] === 1), `end: ${lastImg.img.join(' | ')}`, 'it ends with no clip left behind and a single picture');
  expect('aperture', withImg.every((r) => r[1].img[2] === withImg[0][1].img[2]) && withImg[0][1].img[2] === api.restoredDataUrl.slice(-24), `the picture's source: ${withImg[0][1].img[2]} against ${api.restoredDataUrl.slice(-24)}`, 'the picture is the one the server sent (the display copy), and no other picture is ever layered with it');
  const colours = [...new Set(withImg.map((r) => r[1].border))];
  const rgba = JSON.parse(await page.eval(`JSON.stringify(${JSON.stringify(colours)}.map((c) => { const x = document.createElement('canvas').getContext('2d', { willReadFrequently: true }); x.clearRect(0, 0, 1, 1); x.fillStyle = c; x.fillRect(0, 0, 1, 1); return [...x.getImageData(0, 0, 1, 1).data]; }))`));
  const byColour = new Map(colours.map((c, i) => [c, rgba[i]]));
  const first_ = byColour.get(withImg[0][1].border), end_ = byColour.get(withImg.at(-1)[1].border), warmest = rgba.reduce((m, p) => (p[0] - p[2] > m[0] - m[2] ? p : m), rgba[0]);
  expect('aperture', first_ && end_ && Math.abs(first_[3] - end_[3]) <= 1 && Math.abs(first_[0] - end_[0]) <= 2 && warmest[3] > first_[3] + 20 && warmest[0] - warmest[2] > 40 && warmest[3] <= 0.30 * 255, `the border: start ${first_}, end ${end_}, warmest ${warmest}`, 'the frame\'s border warms (to the gold ring colour, alpha at most .28) while it opens and is back at rest at the end');
  // the slider: once, from 92 to 50
  const sl = await page.eval(`(() => { const s = document.querySelector('.cursor-ew-resize'); return s ? s.querySelectorAll('img')[1].style.clipPath : null; })()`);
  expect('aperture', sl === 'inset(0px 0px 0px 50%)' || sl === 'inset(0 0 0 50%)', `the plain slider after its one sweep rests at 50: ${sl}`, 'the plain slider has swept once (92 to 50) and rests at 50');
  // a second style: crossfade, no aperture
  await page.eval(`document.querySelector('[data-testid=tile-${api.slugs.second}] button').click()`);
  await startRec(page, `(() => { const f = document.querySelector('[data-testid=artwork]'); const is = f ? [...f.querySelectorAll('img')] : []; return is.map((i) => [i.getAttribute('src').slice(-24), getComputedStyle(i).clipPath, getComputedStyle(i).opacity, getComputedStyle(i).scale, getComputedStyle(i).filter, i.className.replace(/absolute inset-0 w-full h-full object-contain/, '').trim()]); })()`, 900);
  await sleep(3200);
  const X = (await rec(page)).map((r) => r[1]);
  const two = X.filter((f) => f.length === 2);
  const srcs = new Set(X.flat().map((i) => i[0]));
  expect('crossfade', srcs.has(api.secondDataUrl.slice(-24)) && X.at(-1).length === 1 && X.at(-1)[0][0] === api.secondDataUrl.slice(-24), `sources ${[...srcs].join()}, last ${JSON.stringify(X.at(-1))}`, 'a second style\'s picture replaces the first one and only one picture is left');
  expect('crossfade', X.flat().every((i) => i[1] === 'none' && i[3] === 'none' && i[4] === 'none' && !/fx-open/.test(i[5])), `layers: ${[...new Set(X.flat().map((i) => i.slice(1).join('|')))].slice(0, 6).join(' ; ')}`, `crossfade: opacity only (${two.length} frames with two layers): no clip, no scale, no filter, no aperture a second time`);
  const during2 = X.filter((f) => f.length === 2).map((f) => +f[1][2]);
  expect('crossfade', two.length === 0 || (during2.some((o) => o < 1) && during2.every((o, i) => i === 0 || o >= during2[i - 1] - 0.001)), `the new layer's opacity: ${during2.slice(0, 6)}`);
  expect('loops', (errorsOf.get(page) || []).length === 0, `console errors: ${(errorsOf.get(page) || []).join(' | ')}`);
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- the loops of the whole flow, from the first recording
async function checkLoopsAcrossFlow() {
  const page = await open('/try?lang=en');
  await startRec(page, `document.getAnimations().filter((a) => a.effect.getComputedTiming().iterations === Infinity && a.playState === 'running').map((a) => a.animationName).join()`, 2600);
  await walkTry(page, 'result');
  await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 40);
  await sleep(2500);
  const S = (await rec(page)).map((r) => r[1]);
  const most = Math.max(...S.map((s) => (s ? s.split(',').length : 0)));
  expect('loops', most <= 2 && S.filter((s) => s.split(',').length > 1).every((s) => /fx-sweep|wk-rot/.test(s)), `loops at a frame: most ${most}: ${[...new Set(S)].join(' ; ')}`, `across the whole flow no frame has more than the waiting arc and a hairline (${[...new Set(S)].filter(Boolean).join(' ; ')})`);
  expect('loops', S.at(-1) === '', `the last frame still loops: ${S.at(-1)}`, 'at the end of the flow nothing loops any more');
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- order
async function checkOrder() {
  console.log('order');
  api.setOrder({ scenario: 'making', eyes: 3, made: 0 });
  const page = await open(`/order?o=i3check&k=${KEY}&lang=en`, { width: 1280, height: 900 });
  expect('order', await waitFor(page, "!!document.querySelector('[data-testid=state-making]')", 20000), 'the making card did not come');
  await sleep(600);
  const mk = JSON.parse(await page.eval(`JSON.stringify({ eyes: [...document.querySelectorAll('[data-testid^=eye-]')].map((li) => ({ waits: !!li.querySelector('.wk-waits'), arc: !!li.querySelector('.wk-arc'), made: !!li.querySelector('.wk-ring .on') })), dot: !!document.querySelector('[data-testid=making-line] .fx-dot'), spin: document.querySelectorAll('.animate-spin, .animate-pulse').length, bar: getComputedStyle(document.querySelector('[role=progressbar] > div')).backgroundImage, barW: document.querySelector('[role=progressbar] > div').style.width })`));
  expect('order', mk.eyes.length === 3 && mk.eyes.filter((e) => e.arc).length === 2 && mk.eyes.filter((e) => e.waits).length === 1 && mk.dot && mk.spin === 0 && mk.bar === 'none', `making: ${JSON.stringify(mk)}`, 'making: the two eyes in hand have the arc, the third a dim still ring, a still dot in the status line, a flat bar, no spinner');
  const loops = running(await anims(page)).filter((a) => a.loop);
  expect('order', loops.length === 2 && loops.every((a) => a.n === 'wk-rot'), `loops: ${loops.map((a) => a.n).join()}`, 'one arc per eye that is being made and nothing else loops');
  expect('order', await waitFor(page, "!!document.querySelector('[data-testid=eye-1] .wk-ring .on')", 20000, 30), 'eye 1 was not made');
  await sleep(120);
  const fresh = JSON.parse(await page.eval(`JSON.stringify({ fresh: !!document.querySelector('[data-testid=eye-1] .wk-ring.fx-fresh'), drawing: document.getAnimations().filter((a) => a.animationName === 'fx-draw').length, badge: !!document.querySelector('[data-testid=eye-1] .wk-badge'), colour: getComputedStyle(document.querySelector('[data-testid=eye-1] .wk-ring .on')).stroke, arcStill: !!document.querySelector('[data-testid=eye-1] .wk-arc') })`));
  expect('order', fresh.fresh && fresh.drawing >= 2 && fresh.badge && fresh.colour === 'rgb(116, 184, 148)' && !fresh.arcStill, `eye 1 made: ${JSON.stringify(fresh)}`, 'a made eye\'s ring closes in the success colour (--ok) and its check draws; the arc is gone from it');
  // the ready reveal
  await startRec(page, `(() => { const i = document.querySelector('[data-testid=state-ready] img'); const d = document.querySelector('[data-testid=download]'); return { img: i ? [getComputedStyle(i).clipPath, i.className] : null, ring: d ? +getComputedStyle(d, '::after').opacity : null, ringAnim: document.getAnimations().filter((a) => a.animationName === 'fx-pass').length }; })()`, 1500);
  expect('order', await waitFor(page, "!!document.querySelector('[data-testid=state-ready]')", 40000, 30), 'the ready card did not come');
  await sleep(4200);
  const Q = (await rec(page)).map((r) => [r[0], r[1]]).filter((r) => r[1]);
  const imgs = Q.filter((r) => r[1].img);
  const clips = imgs.map((r) => parseFloat((/circle\(([\d.]+)%/.exec(r[1].img[0]) || [])[1] ?? NaN)).filter((x) => !Number.isNaN(x));
  expect('order', imgs.length > 50 && /circle\(0%\)/.test(imgs[0][1].img[0]) && clips.every((v, i) => i === 0 || v >= clips[i - 1] - 0.01) && Math.max(...clips) > 72 && imgs.at(-1)[1].img[0] === 'none' && !/fx-open/.test(imgs.at(-1)[1].img[1]), `ready aperture: ${imgs[0][1].img.join('|')} ... ${imgs.at(-1)[1].img.join('|')} max ${Math.max(...clips)}`, 'ready: the delivered picture opens from circle(0) to circle(75) once it has decoded and leaves no clip behind');
  const opens = imgs.filter((r) => /circle/.test(r[1].img[0]));
  const ringOn = Q.filter((r) => r[1].ring !== null && r[1].ring > 0.05);
  expect('order', ringOn.length > 20 && ringOn[0][0] >= opens[0][0] + 1100 && ringOn.at(-1)[0] - ringOn[0][0] < 1700 && Math.max(...Q.map((r) => r[1].ring || 0)) > 0.5 && Q.at(-1)[1].ring === 0 && Q.at(-1)[1].ringAnim === 0, `ring passes from ${ringOn[0] && ringOn[0][0]} to ${ringOn.at(-1) && ringOn.at(-1)[0]} ms, the opening began at ${opens[0] && opens[0][0]}; at the end ${JSON.stringify(Q.at(-1)[1])}`, 'a hairline passes once around the download button after the aperture and is gone (no loop, no pulse)');
  const live = running(await anims(page));
  expect('order', live.length === 0, `still running at the end: ${live.map((a) => a.n).join()}`, 'at the end of the ready reveal nothing animates');
  expect('order', (errorsOf.get(page) || []).length === 0, `console errors: ${(errorsOf.get(page) || []).join(' | ')}`);
  await page.close();

  // a page opened already ready: the picture is there at once, only the words fade
  api.setOrder({ scenario: 'ready', eyes: 3 });
  const p2 = await open(`/order?o=i3check&k=${KEY}&lang=en`, { width: 375, height: 812, pre: `window.__seen = []; new MutationObserver(() => { const i = document.querySelector('[data-testid=state-ready] img'); if (i && !window.__first) { window.__first = true; (function f() { const c = getComputedStyle(i); window.__seen.push([c.clipPath, c.opacity, c.scale, c.filter, i.className]); if (window.__seen.length < 80) requestAnimationFrame(f); })(); } }).observe(document, { childList: true, subtree: true });` });
  expect('order', await waitFor(p2, "!!document.querySelector('[data-testid=state-ready] img')", 20000), 'the ready card did not come');
  await sleep(1500);
  const seen = JSON.parse(await p2.eval('JSON.stringify(window.__seen)'));
  const words = JSON.parse(await p2.eval(`JSON.stringify({ soft: [...document.querySelectorAll('.fx-soft')].map((e) => e.tagName), pass: !!document.querySelector('.fx-pass'), lcp: window.__lcp.slice(-1)[0] && window.__lcp.slice(-1)[0][1], cls: window.__cls })`));
  expect('order', seen.length > 30 && seen.every((s) => s[0] === 'none' && s[1] === '1' && s[2] === 'none' && s[3] === 'none' && !/fx-/.test(s[4])), `the picture on a page opened ready: ${[...new Set(seen.map((s) => s.join('|')))].join(' ; ')}`, 'opened already ready: the picture is at its first frame untouched (no clip, no fade, no scale, no filter: Artwork Charter AC-1)');
  expect('order', words.soft.length >= 4 && !words.pass && /^IMG/.test(words.lcp || ''), `words: ${JSON.stringify(words)}`, `opened already ready: only the words around it fade (${words.soft.join()}), no ring passes, the largest paint is the picture (${words.lcp})`);
  await p2.close();

  // a pending card waits: a hairline along its top edge
  api.setOrder({ scenario: 'pending', eyes: 2, pendingMs: 60000 });
  const p3 = await open(`/order?o=i3check&k=${KEY}&lang=en`, { width: 375, height: 812 });
  expect('order', await waitFor(p3, "!!document.querySelector('[data-testid=state-pending]')", 20000), 'the pending card did not come');
  await sleep(400);
  const pend = JSON.parse(await p3.eval(`JSON.stringify({ hair: !!document.querySelector('[data-testid=state-pending] .fx-hair'), anim: document.getAnimations().filter((a) => a.animationName === 'fx-sweep').map((a) => a.effect.getComputedTiming().duration), h: Math.round(document.querySelector('.fx-hair').getBoundingClientRect().height) })`));
  expect('order', pend.hair && pend.anim.length === 1 && pend.anim[0] === 2000 && pend.h === 1, `pending: ${JSON.stringify(pend)}`, 'a pending card has a 1 px hairline that sweeps its top edge in 2 s');
  await p3.close();

  // a card held for the owner's check holds calm text only: no motion at all (spec 8)
  api.setOrder({ scenario: 'review', eyes: 2 });
  const p4 = await open(`/order?o=i3check&k=${KEY}&lang=en`, { width: 375, height: 812 });
  expect('order', await waitFor(p4, "!!document.querySelector('[data-testid=state-review]')", 20000), 'the review card did not come');
  await sleep(900);
  const rv = JSON.parse(await p4.eval(`JSON.stringify({ anims: document.getAnimations().map((a) => a.animationName || a.transitionProperty), fx: document.querySelector('[data-testid=state-review]').closest('.fx-step') !== null })`));
  expect('order', rv.anims.length === 0 && !rv.fx, `review: ${JSON.stringify(rv)}`, 'the review card (held for the owner) is calm text: no animation, no step transition');
  await p4.close();
}

// ---------------------------------------------------------------------------------------------------- slider
// The plain before and after slider of the result rests at 92 (the customer's photo) and sweeps once to 50 when it has been SEEN. Seen is 60 percent of the slider in
// the window, or, where the slider is taller than the window (it is a square as wide as the page: a phone held sideways, a page zoomed to 200 percent, a short
// window), 60 percent of what the window can show of it. Review I3, M1: the observer was asked for 60 percent of the slider flat, which such a window can never show,
// and the handle stayed at 92 for ever, the restored picture hidden under the photo.
async function checkSlider() {
  console.log('slider');
  const CLIP = `(() => { const s = document.querySelector('.cursor-ew-resize'); return s ? s.querySelectorAll('img')[1].style.clipPath : null; })()`;
  const pct = (c) => { const m = /(\d+(?:\.\d+)?)%/.exec(c || ''); return m ? Number(m[1]) : Number.NaN; };
  // 1. every shape of window a customer really has: in the end the handle rests at 50, and where the slider is in the window at once nothing needs scrolling
  for (const [w, h, label, atOnce] of [[375, 812, 'a phone upright', true], [667, 375, 'a phone held sideways', true], [844, 390, 'a large phone held sideways', true], [640, 360, 'a desktop page zoomed to 200 percent', true], [1280, 500, 'a short laptop window', false], [320, 568, 'a small phone upright', true]]) {
    const page = await open('/try?lang=en', { width: w, height: h });
    const came = (await walkTry(page, 'result')) && (await waitFor(page, "!!document.querySelector('.cursor-ew-resize')", 40000, 50));
    expect('slider', came, `${label}: the slider did not come`);
    if (!came) { await page.close(); continue; }
    const geo = JSON.parse(await page.eval(`JSON.stringify((() => { const r = document.querySelector('.cursor-ew-resize').getBoundingClientRect(); return { h: Math.round(r.height), top: Math.round(r.top), vh: innerHeight }; })())`));
    await sleep(2400);   // 400 ms to wait, 1 s to sweep, and a margin
    const at = pct(await page.eval(CLIP));
    if (atOnce) expect('slider', at === 50, `${label} (${w}x${h}, slider ${geo.h} px tall, its top at ${geo.top}, window ${geo.vh}): the handle is at ${at} 2.4 s after the slider came, with no scrolling`, `${label} (${w}x${h}, slider ${geo.h} px in a window ${geo.vh} px tall): it sweeps by itself and rests at 50`);
    // the customer scrolls the slider into the middle of the window and looks at it: it rests at 50 (it never stays at 92)
    await page.eval(`document.querySelector('.cursor-ew-resize').scrollIntoView({ block: 'center' })`);
    const rests = await waitFor(page, `(() => { const s = document.querySelector('.cursor-ew-resize'); return !!s && /(^|[^0-9.])50%/.test(s.querySelectorAll('img')[1].style.clipPath); })()`, 6000, 100);
    expect('slider', rests, `${label}: the handle is at ${pct(await page.eval(CLIP))} six seconds after the slider was scrolled into the middle of the window`, atOnce ? '' : `${label} (${w}x${h}, slider ${geo.h} px in a window ${geo.vh} px tall): scrolled into view it sweeps and rests at 50`);
    expect('slider', (errorsOf.get(page) || []).length === 0, `console errors: ${(errorsOf.get(page) || []).join(' | ')}`);
    await page.close();
  }
  // 2. an observer that reports a slider that is only PART in the window (a bar over it, a browser that reports another height): it counts as seen after 3.5 s; one that is
  // out of the window altogether is not seen, and waits for the customer
  const fake = (ratio, inter) => `window.IntersectionObserver = class { constructor(cb) { this.cb = cb; } observe(el) { setTimeout(() => this.cb([{ target: el, isIntersecting: ${inter}, intersectionRatio: ${ratio} }], this), 60); } unobserve() {} disconnect() {} takeRecords() { return []; } };`;
  for (const [ratio, inter, label] of [[0.4, true, 'part of the slider in the window (40 percent where 60 are needed)'], [0.1, true, 'a few pixels of the slider in the window (10 percent)'], [0, false, 'the slider outside the window']]) {
    const page = await open('/try?lang=en', { pre: fake(ratio, inter) });
    await walkTry(page, 'result');
    expect('slider', await waitFor(page, "!!document.querySelector('.cursor-ew-resize')", 40000, 50), `${label}: the slider did not come`);
    await sleep(2200);
    const early = pct(await page.eval(CLIP));
    await sleep(5000);
    const late = pct(await page.eval(CLIP));
    if (ratio >= 0.3) expect('slider', early === 92 && late === 50, `${label}: ${early} after 2.2 s, ${late} after 7.2 s`, `${label}: the handle waits at 92 for 3.5 s, then the slider counts as seen and sweeps to 50 (${early} then ${late})`);
    else expect('slider', early === 92 && late === 92, `${label}: ${early} after 2.2 s, ${late} after 7.2 s`, `${label}: nothing sweeps that nobody looks at (${early} then ${late})`);
    await page.close();
  }
  // 3. a window that GROWS: at 375x220 the slider is only part in the window (about 30 percent of it where 38 percent are needed), so by the part-visible rule alone it would
  // count as seen after 3.5 s and sweep at 4.9 s; a window that grows to a phone upright shows all of it and it sweeps at once
  {
    const page = await open('/try?lang=en', { width: 375, height: 220 });
    await walkTry(page, 'result');
    expect('slider', await waitFor(page, "!!document.querySelector('.cursor-ew-resize')", 40000, 50), 'the small window: the slider did not come');
    await sleep(300);
    const small = pct(await page.eval(CLIP));
    await page.send('Emulation.setDeviceMetricsOverride', { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
    await sleep(2200);
    const grown = pct(await page.eval(CLIP));
    expect('slider', small === 92 && grown === 50, `a window that grows: ${small} in the small window, ${grown} 2.2 s after it grew`, `a window that grows shows the slider at once: ${small} in the small window, ${grown} 2.2 s after it grew (not after 3.5 s)`);
    await page.close();
  }
  // 4. a phone turned sideways BEFORE the slider was seen (it was out of the window, a spacer of 2000 px over the page keeps it there): the threshold the observer was given for
  // the upright window (60 percent of the slider) can never be reached in the sideways one (the slider is taller than the window), so only the new threshold lets it
  // count as seen when it is scrolled into the middle: within 2.4 s, long before the part-visible rule (3.5 s) could do it
  {
    const spacer = `document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = 'body::before{content:"";display:block;height:2000px}'; document.head.appendChild(s); });`;
    const page = await open('/try?lang=en', { width: 375, height: 812, pre: spacer });
    await walkTry(page, 'result');
    expect('slider', await waitFor(page, "!!document.querySelector('.cursor-ew-resize')", 40000, 50), 'the turned phone: the slider did not come');
    await sleep(900);
    const upright = pct(await page.eval(CLIP));
    await page.send('Emulation.setDeviceMetricsOverride', { width: 667, height: 375, deviceScaleFactor: 1, mobile: true });
    await sleep(300);
    await page.eval(`document.querySelector('.cursor-ew-resize').scrollIntoView({ block: 'center' })`);
    await sleep(2400);
    const turned = pct(await page.eval(CLIP));
    expect('slider', upright === 92 && turned === 50, `a phone turned before the slider was seen: ${upright} while out of the window, ${turned} 2.4 s after it was scrolled into the middle of the sideways window`, `a phone turned sideways before the slider was seen: it waits at ${upright}, and the new window's threshold lets it count as seen (${turned} 2.4 s after it was scrolled into the middle)`);
    await page.close();
  }
}

// ---------------------------------------------------------------------------------------------------- arrival
// The aperture is an EVENT of one arrival. It runs once and the arrival is then spent (TryApp `arriving`, ArtImage `arrive`), however it ends: by its own animationend, by
// a style chosen while it runs (the end event never comes: review I3, m4, the next mount of the frame would open again), by a decode that came late. And the frame
// is never black and mute while a large picture decodes (m1).
async function checkArrival() {
  console.log('arrival');
  // what ResultView told ArtImage: the `arrive` prop of the component that holds the picture of the frame (React keeps its props on the fibre, also in a production build)
  const ARRIVE = `(() => { const img = document.querySelector('[data-testid=artwork] img'); if (!img) return null; const k = Object.keys(img).find((x) => x.startsWith('__reactFiber$')); for (let f = k ? img[k] : null; f; f = f.return) { const p = f.memoizedProps; if (p && typeof p === 'object' && 'arrive' in p && 'onOpened' in p) return p.arrive; } return null; })()`;
  // 1. the opening runs to its end
  let page = await open('/try?lang=en');
  await walkTry(page, 'result');
  expect('arrival', await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 20), 'the artwork did not come');
  const during = await page.eval(ARRIVE);
  await sleep(2800);
  const after = await page.eval(ARRIVE);
  expect('arrival', during === true && after === false, `the arrival while the aperture runs: ${during}, 2.8 s later: ${after}`, 'the arrival is true while the aperture opens and spent when it has ended');
  await page.close();
  // 2. a style chosen while the aperture runs: the arrival is spent all the same, one picture is left, nothing is clipped
  page = await open('/try?lang=en');
  await walkTry(page, 'result');
  expect('arrival', await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 20), 'the artwork did not come');
  await sleep(250);
  const cutAt = await page.eval(`getComputedStyle(document.querySelector('[data-testid=artwork] img')).clipPath`);
  await page.eval(`document.querySelector('[data-testid=tile-${api.slugs.second}] button').click()`);
  await sleep(3200);
  const end = JSON.parse(await page.eval(`JSON.stringify({ arrive: ${ARRIVE}, imgs: document.querySelectorAll('[data-testid=artwork] img').length, cls: document.querySelector('[data-testid=artwork] img').className, clip: getComputedStyle(document.querySelector('[data-testid=artwork] img')).clipPath })`));
  expect('arrival', /circle/.test(cutAt) && end.arrive === false && end.imgs === 1 && !/fx-open|fx-xfade/.test(end.cls) && end.clip === 'none',
    `a style chosen while the aperture ran (clip then ${cutAt}): ${JSON.stringify(end)}`, 'a style chosen while the aperture runs spends the arrival (its end event never comes): one picture, no clip, the frame will not open again');
  expect('arrival', (errorsOf.get(page) || []).length === 0, `console errors: ${(errorsOf.get(page) || []).join(' | ')}`);
  await page.close();
  // 3. a slow decode (1.8 s): until the picture is in, the frame keeps the composing status and the hairline, never a black frame with nothing in it
  page = await open('/try?lang=en', { pre: 'const d = HTMLImageElement.prototype.decode; HTMLImageElement.prototype.decode = function () { return new Promise((res, rej) => setTimeout(() => d.call(this).then(res, rej), 1800)); };' });
  await startRec(page, `(() => { const f = document.querySelector('[data-testid=artwork]'); if (!f) return null; return { imgs: f.querySelectorAll('img').length, hair: !!f.querySelector('.fx-hair'), status: [...f.querySelectorAll('[role=status]')].length }; })()`, 2400);
  await walkTry(page, 'result');
  expect('arrival', await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 20), 'the artwork did not come with a slow decode');
  await sleep(2000);
  const F = (await rec(page)).filter((r) => r[1]);
  const empty = F.filter((r) => r[1].imgs === 0);
  const bare = empty.filter((r) => !r[1].hair || r[1].status !== 1);
  const span = empty.length ? empty.at(-1)[0] - empty[0][0] : 0;
  expect('arrival', empty.length > 60 && bare.length === 0 && span > 2000, `frames of the frame with no picture: ${empty.length} over ${span} ms, ${bare.length} of them without the hairline or without exactly one status: ${JSON.stringify(bare.slice(0, 3))}`,
    `a decode of 1.8 s: the frame keeps the hairline and one status line in all ${empty.length} frames without a picture (${span} ms), never black and mute`);
  expect('arrival', F.at(-1)[1].imgs === 1 && F.at(-1)[1].status === 0 && !F.at(-1)[1].hair, `at the end: ${JSON.stringify(F.at(-1)[1])}`, 'when the picture is in, the status and the hairline are gone');
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- failsafe
async function checkFailsafe() {
  console.log('failsafe');
  // 1. a decode that never comes: the preview is there anyway within 3.5 s, whole, and the arrival is spent
  let page = await open('/try?lang=en', { pre: 'HTMLImageElement.prototype.decode = () => new Promise(() => {});' });
  await walkTry(page, 'result');
  await startRec(page, `(() => { const f = document.querySelector('[data-testid=artwork]'); const i = f && f.querySelector('img'); return i ? [getComputedStyle(i).clipPath, i.className, f.querySelectorAll('img').length].join('|') : null; })()`, 1200);
  const came = await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 50);
  await sleep(2600);
  const F1 = (await rec(page)).filter((r) => r[1]).map((r) => r[1]);
  expect('failsafe', came && F1.length > 10 && F1.every((f) => f.startsWith('none|') && f.endsWith('|1') && !/fx-open/.test(f)), `after a decode that never comes: ${[...new Set(F1)].join(' ; ')}`, 'a decode that never comes: the preview is put in anyway, whole, with no clip');
  expect('failsafe', (errorsOf.get(page) || []).length === 0, `console errors: ${(errorsOf.get(page) || []).join(' | ')}`);
  await page.close();

  // 2. every animation blocked by the browser: the preview comes, the arrival is spent (no second layer, no clip left)
  page = await open('/try?lang=en', { pre: "const s = document.createElement('style'); s.textContent = '*, *::before, *::after { animation: none !important; transition: none !important }'; document.addEventListener('DOMContentLoaded', () => document.head.appendChild(s));" });
  await walkTry(page, 'result');
  expect('failsafe', await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 50), 'with animation blocked the preview did not come');
  await sleep(2800);
  const blocked = JSON.parse(await page.eval(`JSON.stringify({ imgs: document.querySelectorAll('[data-testid=artwork] img').length, cls: document.querySelector('[data-testid=artwork] img').className, clip: getComputedStyle(document.querySelector('[data-testid=artwork] img')).clipPath })`));
  expect('failsafe', blocked.imgs === 1 && !/fx-open|fx-xfade/.test(blocked.cls) && blocked.clip === 'none', `animation blocked: ${JSON.stringify(blocked)}`, 'every animation blocked: the preview is there, one picture, no class of the opening left on it (the timer settles what the event never did)');
  await page.close();

  // 3. an IntersectionObserver that never reports: the plain slider is not left at 92 percent
  page = await open('/try?lang=en', { pre: 'window.IntersectionObserver = class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } };' });
  await walkTry(page, 'result');
  expect('failsafe', await waitFor(page, "!!document.querySelector('.cursor-ew-resize')", 40000, 50), 'the slider did not come');
  const at0 = await page.eval(`[...document.querySelectorAll('.cursor-ew-resize img')][1].style.clipPath`);
  await sleep(4200);
  const at4 = await page.eval(`[...document.querySelectorAll('.cursor-ew-resize img')][1].style.clipPath`);
  expect('failsafe', /92%/.test(at0) && /50%/.test(at4), `the slider with a dead observer: ${at0} then ${at4}`, 'a dead IntersectionObserver: the slider waits at 92 and is at 50 after 3.5 s, never left half hidden');
  expect('failsafe', !(await page.eval("document.documentElement.classList.contains('mo') || document.documentElement.classList.contains('mo-fail')")), 'html.mo is set on a tool: something is hidden until a script reveals it');
  await page.close();

  // 4. /order: a decode that never comes, the file is delivered
  api.setOrder({ scenario: 'making', eyes: 1, made: 0 });
  page = await open(`/order?o=i3check&k=${KEY}&lang=en`, { width: 375, height: 812, pre: 'HTMLImageElement.prototype.decode = () => new Promise(() => {});' });
  expect('failsafe', await waitFor(page, "!!document.querySelector('[data-testid=state-ready]')", 40000, 50), 'the ready card did not come');
  // the download link is there, focusable and visible, from the first frame of the ready card: the reveal never delays it
  const link = JSON.parse(await page.eval(`JSON.stringify((() => { const a = document.querySelector('[data-testid=download]'); const r = a.getBoundingClientRect(); const c = getComputedStyle(a); return { href: a.getAttribute('href').length > 0, h: Math.round(r.height), vis: c.visibility, op: c.opacity, hidden: !!a.closest('[aria-hidden=true], [hidden]'), img: !!document.querySelector('[data-testid=state-ready] img') }; })())`));
  expect('failsafe', link.href && link.h >= 44 && link.vis === 'visible' && link.op === '1' && !link.hidden, `the download link at the first frame of the ready card: ${JSON.stringify(link)}`, `the download link is there, visible and at least 44 px high at the first frame of the ready card, before the picture (${link.img ? 'the picture was already in' : 'the picture was not in yet'})`);
  const t1 = Date.now();
  const imgCame = await waitFor(page, "!!document.querySelector('[data-testid=state-ready] img')", 8000, 50);
  const waited = Date.now() - t1;
  expect('failsafe', imgCame && waited < 4500, `ready with a decode that never comes: the picture after ${waited} ms`, `ready, a decode that never comes: the delivered picture is there ${waited} ms after the card (the failsafe is 3.5 s)`);
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- shift
async function checkShift() {
  console.log('shift');
  // The clamp of the reduced-motion rule gives every transition .01 ms: a style change of an element (the buy card's link when the preview arrives, a line of text that
  // changes class) starts one that ends in the frame it starts in. Whether the sampler's tick (getAnimations() flushes the style) lands in that frame is chance, so
  // the sampler leaves out what lasts 1 ms or less (review I3 fix: the gate failed on a build that changed nothing about reduced motion, and passed on its parent).
  // What can move the layout is a property that has layout (width, height, margin, padding, top, left, font size, border width): the motion of the tools animates none of them
  // (a sampler collects every property any animation or transition of the flow touches, at 50 ms) except the width of the progress bar's fill, which is the bar's own and
  // stands inside a box of fixed size. The numbers of the layout shifts of the whole flow with and without motion are printed (the page's own shifts, a new screen under the
  // old one, vary by a few hundredths from one run to the next, so they only gate a motion that would add a real one: .06).
  const LAYOUT = /^(width|height|min-|max-|margin|padding|top|left|right|bottom|inset|font|line-height|letter-spacing|border-(top|right|bottom|left)?-?width|gap|flex|grid|display|position)/;
  const SAMPLER = `window.__props = new Set(); setInterval(() => { for (const a of document.getAnimations()) { if (a.effect && a.effect.getComputedTiming().duration <= 1) continue; const t = a.effect && a.effect.target; const cls = t && t.className && t.className.baseVal !== undefined ? t.className.baseVal : (t && t.className) || ''; const props = a.transitionProperty ? [a.transitionProperty] : (a.effect && a.effect.getKeyframes ? a.effect.getKeyframes().flatMap((k) => Object.keys(k)).filter((k) => !['offset', 'easing', 'composite', 'computedOffset'].includes(k)) : []); for (const p of props) window.__props.add(p + ' @ ' + String(cls).split(' ').filter((c) => /^(fx|wk)-/.test(c)).join('.')); } }, 50);`;
  const flow = async (reduceMotion) => {
    const page = await open('/try?lang=en', { reduceMotion, pre: SAMPLER });
    await walkTry(page, 'result');
    await waitFor(page, "!!document.querySelector('[data-testid=artwork] img')", 40000, 50);
    await sleep(3500);
    const cls = await page.eval('window.__cls');
    const props = JSON.parse(await page.eval('JSON.stringify([...window.__props])'));
    await page.close();
    api.setOrder({ scenario: 'making', eyes: 2, made: 0 });
    const o = await open(`/order?o=i3check&k=${KEY}&lang=en`, { reduceMotion, width: 375, height: 812, pre: SAMPLER });
    await waitFor(o, "!!document.querySelector('[data-testid=state-ready] img')", 40000, 50);
    await sleep(3200);
    const ocls = await o.eval('window.__cls');
    props.push(...JSON.parse(await o.eval('JSON.stringify([...window.__props])')));
    await o.close();
    return { cls, ocls, props: [...new Set(props)] };
  };
  const a = await flow(false), b = await flow(true);
  const layout = a.props.filter((p) => LAYOUT.test(p.split(' @ ')[0]) && !/^width @ .*fx-bar/.test(p));
  expect('shift', a.props.length >= 8 && layout.length === 0 && b.props.length === 0, `properties touched by the motion: ${a.props.join(' | ')}; layout properties: ${layout.join(' | ')}; with reduced motion: ${b.props.join(' | ')}`,
    `the motion touches no property that has layout (${a.props.map((p) => p.split(' @ ')[0]).filter((p, i, l) => l.indexOf(p) === i).join(', ')}), and nothing at all under reduced motion`);
  expect('shift', Math.abs(a.cls - b.cls) < 0.06 && Math.abs(a.ocls - b.ocls) < 0.06, `/try ${a.cls.toFixed(4)} with motion, ${b.cls.toFixed(4)} without; /order ${a.ocls.toFixed(4)} with, ${b.ocls.toFixed(4)} without`,
    `the layout shifts of the whole flow with and without motion: /try ${a.cls.toFixed(3)} against ${b.cls.toFixed(3)}, /order ${a.ocls.toFixed(3)} against ${b.ocls.toFixed(3)} (the page's own, unchanged by the motion)`);
}

// ---------------------------------------------------------------------------------------------------- wiring
async function checkWiring() {
  console.log('wiring');
  for (const f of ['try.html', 'order.html']) {
    const html = readFileSync(join(dist, f), 'utf8');
    expect('wiring', html.includes('skipTransition') && html.includes('(o|k|s|checkout|session_id|withdraw)=') && /<body class="fx /.test(html), `${f}: the page transition script or the body class is missing`, `${f}: the head script skips the page transition for an order, a payment or the withdrawal form; the body carries fx`);
    const mods = [...html.matchAll(/(?:src|href)="(\/assets\/[^"]+\.js)"/g)].map((m) => m[1]);
    const engine = readFileSync(join(ROOT, 'src', 'motion', 'motion.ts'), 'utf8').includes('reveals');
    let loadsEngine = false;
    const seen = new Set();
    const walk = (f2) => { if (seen.has(f2) || !existsSync(join(dist, f2))) return; seen.add(f2); const t = readFileSync(join(dist, f2), 'utf8'); if (/mo-fail/.test(t)) loadsEngine = true; for (const m of t.matchAll(/(?:import|from)\s*["']\.\/([^"']+\.js)["']/g)) walk('assets/' + m[1]); };
    mods.forEach((m) => walk(m.slice(1)));
    expect('wiring', engine && !loadsEngine, `${f} loads the landing's engine (mo-fail found in its first-load scripts)`, `${f}: the landing's motion engine is not among its first-load scripts`);
  }
  const page = await open('/try?lang=en');
  expect('wiring', !(await page.eval("document.documentElement.classList.contains('mo')")), 'html.mo on /try');
  await page.close();
}

// ---------------------------------------------------------------------------------------------------- bundle
// The first-load bytes of the two pages (gzip level 6: the html's scripts and stylesheets and their static imports) on the commit before the motion of the tools
// (5c9054c, measured the same way). The budget is the spec's (section 10: CSS +2 kB each for /try and /order); the JS has no number in the spec, so this gate says
// +4 kB. A change of a module that /try and /order share with other work (src/shared) moves the base: re-measure it on the commit before, as scripts/check_budget.mjs says.
const BEFORE = { try: { js: 152765, css: 10975 }, order: { js: 108723, css: 10975 } };
function firstLoad(page) {
  const html = readFileSync(join(dist, page), 'utf8');
  const seen = new Map();
  const add = (href) => {
    const f = href.replace(/^\//, '');
    if (seen.has(f) || !existsSync(join(dist, f))) return;
    const buf = readFileSync(join(dist, f));
    seen.set(f, buf);
    if (f.endsWith('.js')) for (const m of buf.toString('utf8').matchAll(/(?:import|from)\s*["']\.\/([^"']+\.js)["']/g)) add(`assets/${m[1]}`);
  };
  for (const m of html.matchAll(/(?:src|href)="(\/assets\/[^"]+\.(?:js|css))"/g)) add(m[1]);
  const sum = { js: 0, css: 0 };
  for (const [f, b] of seen) sum[f.endsWith('.js') ? 'js' : 'css'] += gzipSync(b, { level: 6 }).length;
  return sum;
}
function checkBundle() {
  console.log('bundle');
  for (const [name, page] of [['try', 'try.html'], ['order', 'order.html']]) {
    const now = firstLoad(page), was = BEFORE[name];
    const dj = now.js - was.js, dc = now.css - was.css;
    expect('bundle', dc <= 2048, `${page}: CSS ${now.css} B gzip, ${dc >= 0 ? '+' : ''}${dc} B over the page before the motion (budget +2048)`, `${page}: JS ${now.js} B gzip (${dj >= 0 ? '+' : ''}${dj} B), CSS ${now.css} B gzip (${dc >= 0 ? '+' : ''}${dc} B, budget +2048) over the page before the motion`);
    expect('bundle', dj <= 4096, `${page}: JS ${now.js} B gzip, ${dj >= 0 ? '+' : ''}${dj} B over the page before the motion (budget +4096)`);
  }
}

// ---------------------------------------------------------------------------------------------------- run
try {
  if (wants('reduced')) await checkReduced();
  if (wants('loops') || wants('arc') || wants('aperture') || wants('crossfade')) { await checkTryWithMotion(); await checkLoopsAcrossFlow(); }
  if (wants('order')) await checkOrder();
  if (wants('slider')) await checkSlider();
  if (wants('arrival')) await checkArrival();
  if (wants('failsafe')) await checkFailsafe();
  if (wants('shift')) await checkShift();
  if (wants('wiring')) await checkWiring();
  if (wants('bundle')) checkBundle();
} finally {
  await chrome.close();
  await site.close();
}
console.log(problems.length ? `\nmotion flow check FAILED (${problems.length})` : '\nmotion flow check ok');
process.exit(problems.length ? 1 : 0);
