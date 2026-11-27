// The live camera of /try (?cam=1, 2026-11-26, src/try/livecam), in real Chrome with Chrome's fake camera (--use-fake-device-for-media-stream,
// --use-fake-ui-for-media-stream: a test pattern and the permission granted) on the built page and the stand-in API (scripts/lib/flowstub.mjs).
//   npm run build && node scripts/check_livecam.mjs [--dist dist]
//   burst     with ?cam=1 the gold button opens our camera view (its facts line shows what the camera gave), one tap on the shutter sends the frames to
//             /api/analyze as live photos with their codes, the view closes and the camera is stopped; the tab remembers ?cam=1
//   fallback  getUserMedia refused (NotAllowedError) or missing: the capture input is opened instead, with no error text and no camera view
//             (the owner's grey line names the class: cam: denied, cam: unsupported)
//   lock      the page behind is at its top and does not scroll while the view is open, and is given back on close
//   inapp     in Messenger's browser the hint and the close button keep 72 px below the view's top, the shutter 100 px above its bottom
//   still     where the camera offers photo sizes the page asks the largest up to 4096 px and 12 MP
//   dark      a fake camera filming black: the second line says it is too dark, the shutter stays usable
//   off       without ?cam=1 the gold button opens the capture input as before and the camera's chunk is never loaded
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';
import { flowApi } from './lib/flowstub.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const dist = resolve(args.includes('--dist') ? args[args.indexOf('--dist') + 1] : join(ROOT, 'dist'));
const problems = [];
let n = 0;
const ok = (c, cond, m) => { n++; if (!cond) { problems.push(`${c}: ${m}`); console.log(`  FAIL ${c}: ${m}`); } else console.log(`  ok   ${c}: ${m.slice(0, 160)}`); return !!cond; };

// what the page sends and opens, recorded before any of its scripts runs: the analyze bodies, the beacons, the inputs it clicks (not opened: a
// headless browser has no file chooser) and every camera stream it gets
const SPY = (gum) => `(() => {
  window.__sent = []; window.__beacons = []; window.__clicks = []; window.__streams = [];
  const f = window.fetch;
  window.fetch = function (u, o) { try { if (String(u).includes('/api/analyze')) window.__sent.push(JSON.parse(o.body)); } catch (e) {} return f.apply(this, arguments); };
  const sb = navigator.sendBeacon && navigator.sendBeacon.bind(navigator);
  if (sb) navigator.sendBeacon = (u, d) => { try { d.text().then((t) => window.__beacons.push(JSON.parse(t))); } catch (e) {} return sb(u, d); };
  HTMLInputElement.prototype.click = function () { window.__clicks.push({ type: this.type, capture: this.getAttribute('capture'), multiple: this.multiple }); };
  // the stills: what the page asks of ImageCapture (the size) and what the camera offers
  window.__takes = []; window.__photoCaps = null;
  if (window.ImageCapture) {
    const tp = ImageCapture.prototype.takePhoto, gc = ImageCapture.prototype.getPhotoCapabilities;
    ImageCapture.prototype.takePhoto = function (o) { window.__takes.push(o ? { w: o.imageWidth, h: o.imageHeight } : null); return tp.apply(this, arguments); };
    if (gc) ImageCapture.prototype.getPhotoCapabilities = function () { return gc.apply(this, arguments).then((c) => { window.__photoCaps = { w: c.imageWidth, h: c.imageHeight }; return c; }); };
  }
  const md = navigator.mediaDevices;
  ${gum === 'deny' ? "if (md) md.getUserMedia = () => Promise.reject(new DOMException('denied', 'NotAllowedError'));"
    : gum === 'none' ? "try { Object.defineProperty(navigator, 'mediaDevices', { value: undefined, configurable: true }); } catch (e) {}"
    : "if (md && md.getUserMedia) { const g = md.getUserMedia.bind(md); md.getUserMedia = (c) => g(c).then((s) => { window.__streams.push(s); return s; }); }"}
})();`;

const api = flowApi(ROOT);
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler: api.handler });
const origin = `http://127.0.0.1:${site.port}`;
const chrome = await launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });
const waitFor = async (page, expr, ms = 15000) => { const t0 = Date.now(); for (;;) { let v = false; try { v = await page.eval(expr); } catch { /* busy */ } if (v) return true; if (Date.now() - t0 > ms) return false; await sleep(80); } };
const FB_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.0.0 Mobile Safari/537.36 [FB_IAB/MESSENGER;FBAV/480.0.0.0;]';
async function open(url, gum = 'fake', ua = null, size = [390, 844]) {
  const page = await chrome.page({ width: size[0], height: size[1], mobile: true });
  if (ua) await page.send('Network.setUserAgentOverride', { userAgent: ua });
  await page.send('Page.addScriptToEvaluateOnNewDocument', { source: SPY(gum) });
  await page.goto(origin + url);
  await page.loaded();
  await waitFor(page, "!!document.querySelector('[data-testid=camera-direct]')", 20000);
  await sleep(600);
  return page;
}
const tap = (page, id) => page.eval(`document.querySelector('[data-testid=${id}]').click()`);
const j = async (page, expr) => JSON.parse(await page.eval(`JSON.stringify(${expr})`));

try {
  // ---- burst
  {
    const page = await open('/try?lang=lt&cam=1');
    await page.goto(`${origin}/try?lang=lt`);           // the same tab without ?cam=1: it remembers
    await page.loaded();
    await waitFor(page, "!!document.querySelector('[data-testid=camera-direct]')", 20000);
    await sleep(600);
    await page.eval('window.scrollTo(0, 240)');
    await sleep(200);
    const y0 = await page.eval('Math.round(scrollY)');
    await tap(page, 'camera-direct');
    const opened = await waitFor(page, "!!document.querySelector('[data-testid=live-camera]')", 10000);
    ok('burst', opened, 'the gold button opens the camera view (the tab kept ?cam=1)');
    await sleep(300);
    const lock = await j(page, "({ y: Math.round(scrollY), html: document.documentElement.style.overflow, body: document.body.style.overflow })");
    await page.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: 195, y: 400, deltaX: 0, deltaY: 600 });
    await sleep(400);
    const y2 = await page.eval('Math.round(scrollY)');
    ok('lock', y0 > 0 && lock.y === 0 && lock.html === 'hidden' && lock.body === 'hidden' && y2 === 0,
      `the page behind is at its top and does not scroll while the view is open (before ${y0}, open ${JSON.stringify(lock)}, after a wheel ${y2})`);
    const ready = await waitFor(page, "!!document.querySelector('[data-testid=live-shutter]') && !document.querySelector('[data-testid=live-shutter]').disabled", 10000);
    const facts = await page.eval("(document.querySelector('[data-testid=live-facts]') || {}).textContent || ''");
    const hint = await page.eval("document.querySelector('[data-testid=live-camera]').textContent");
    ok('burst', ready && /^vv \d+\/\d+ in \d+ sc \d+ . video \d+x\d+ . zoom/.test(facts) && hint.includes('Laikykite akį apskritime'), `the view is ready, shows the hint and the camera's facts: "${facts}"`);
    const before = await page.eval("(document.querySelector('[data-testid=live-burst]') || {}).textContent || ''");
    ok('burst', before === 'Padarysime 4 kadrus. Nejudėkite iki signalo.', `before the tap the second line says how many pictures one tap takes: "${before}"`);
    const clicksBefore = (await j(page, 'window.__clicks')).length;
    await tap(page, 'live-shutter');
    // what the person sees during the burst, sampled until the view closes: the count, the shutter, the "Done"
    const seen = { counts: [], disabled: true, done: false, ring: false };
    for (let t0 = Date.now(); Date.now() - t0 < 30000;) {
      const s = await j(page, "(() => { const v = document.querySelector('[data-testid=live-camera]'); if (!v) return null; const c = v.querySelector('[data-testid=live-count]'); const b = v.querySelector('[data-testid=live-shutter]'); return { c: c ? c.textContent : null, d: !!(b && b.disabled), done: !!v.querySelector('[data-testid=live-done]'), ring: !!v.querySelector('[data-testid=live-ring]') }; })()");
      if (!s) break;
      if (s.c && seen.counts[seen.counts.length - 1] !== s.c) seen.counts.push(s.c);
      if ((s.c || s.done) && !s.d) seen.disabled = false;
      seen.done = seen.done || s.done; seen.ring = seen.ring || s.ring;
      await sleep(60);
    }
    ok('burst', seen.counts.join() === '1 / 4,2 / 4,3 / 4,4 / 4' && seen.disabled && seen.done && seen.ring,
      `during the burst the count goes 1 / 4 to 4 / 4 with the ring, the shutter stays disabled, then "Done" shows and the view closes (${JSON.stringify(seen)})`);
    const sent = await waitFor(page, "window.__sent.filter((b) => b.device && b.device.source === 'live').length >= 4 && !document.querySelector('[data-testid=live-camera]')", 30000);
    await sleep(1500);
    const bodies = await j(page, "window.__sent.map((b) => ({ source: b.device && b.device.source, cap: b.device && b.device.cap, w: b.origWidth, h: b.origHeight }))");
    const cap = bodies[0]?.cap ?? {};
    const stills = await j(page, '({ takes: window.__takes, caps: window.__photoCaps })');
    const offered = !!(stills.caps && stills.caps.w && stills.caps.w.max > 0);
    ok('still', !offered || (stills.takes.length >= 3 && !!stills.takes[0] && stills.takes[0].w > 0 && stills.takes[0].w <= 4096 && stills.takes[0].w * stills.takes[0].h <= 12e6),
      `the camera offers stills ${JSON.stringify(stills.caps)}: the page asks the largest up to 4096 px and 12 MP (${JSON.stringify(stills.takes)})`);
    ok('burst', sent && bodies.length === 4 && bodies.every((b) => b.source === 'live' && b.cap && b.cap.how === 'live' && ['still', 'frame'].includes(b.cap.lm) && /^mp\d+$/.test(b.cap.lres) && ['track', 'css'].includes(b.cap.zoom) && ['yes', 'no'].includes(b.cap.torch) && b.w > 0),
      `one tap sent 4 pictures to /api/analyze as live photos with their codes: ${JSON.stringify(bodies.map((b) => [b.w, b.h]))} ${JSON.stringify(cap)}`);
    const after = await j(page, "({ view: !!document.querySelector('[data-testid=live-camera]'), live: window.__streams.flatMap((s) => s.getTracks()).filter((t) => t.readyState !== 'ended').length, streams: window.__streams.length })");
    ok('burst', !after.view && after.live === 0 && after.streams === 1, `the view closed and the camera is stopped: ${JSON.stringify(after)}`);
    const clicks = (await j(page, 'window.__clicks')).length;
    ok('burst', clicks === clicksBefore, 'no input was opened on the way');
    await page.close();
  }
  // the close button stops the camera too (a hidden page does the same in the code: not drivable in a headless tab)
  {
    const page = await open('/try?lang=en&cam=1');
    await tap(page, 'camera-direct');
    await waitFor(page, "!!document.querySelector('[data-testid=live-shutter]') && !document.querySelector('[data-testid=live-shutter]').disabled", 10000);
    await page.eval("document.querySelector('[data-testid=live-close]').click()");
    await sleep(500);
    const st = await j(page, "({ view: !!document.querySelector('[data-testid=live-camera]'), live: window.__streams.flatMap((s) => s.getTracks()).filter((t) => t.readyState !== 'ended').length, sent: window.__sent.length, html: document.documentElement.style.overflow, body: document.body.style.overflow })");
    ok('burst', !st.view && st.live === 0 && st.sent === 0 && st.html === '' && st.body === '', `the close button closes the view, stops the camera and gives the page back, nothing sent: ${JSON.stringify(st)}`);
    await page.close();
  }

  // ---- an in-app browser (Messenger's Android web view reports more height than it shows): the controls keep out of the top 72 and the bottom 100 px
  {
    const page = await open('/try?lang=lt&cam=1', 'fake', FB_UA, [360, 740]);
    await tap(page, 'camera-direct');
    await waitFor(page, "!!document.querySelector('[data-testid=live-shutter]') && !document.querySelector('[data-testid=live-shutter]').disabled", 10000);
    // the words at the top (before the tap, and the count during the burst) keep clear of the close button and inside the band the web view surely shows:
    // every line's text (its own rectangle, not its box) ends before the button's left edge or below its bottom, and starts 72 px or more below the view's top
    const words = `(() => { const v = document.querySelector('[data-testid=live-camera]').getBoundingClientRect(); const x = document.querySelector('[data-testid=live-close]').getBoundingClientRect(); const out = []; for (const p of document.querySelectorAll('[data-testid=live-hint] p')) { const rg = document.createRange(); rg.selectNodeContents(p); for (const r of rg.getClientRects()) out.push({ t: Math.round(r.top - v.top), b: Math.round(r.bottom - v.top), l: Math.round(r.left), r: Math.round(r.right) }); } return { lines: out, x: { l: Math.round(x.left), b: Math.round(x.bottom - v.top) }, circle: Math.round(document.querySelector('[data-testid=live-camera] > div[aria-hidden]').getBoundingClientRect().top - v.top) }; })()`;
    const clear = (w) => w.lines.length > 0 && w.lines.every((r) => r.t >= 72 && (r.r <= w.x.l || r.t >= w.x.b));
    const w1 = await j(page, words);
    await tap(page, 'live-shutter');
    await waitFor(page, "!!document.querySelector('[data-testid=live-count]')", 5000);
    const w2 = await j(page, words);
    ok('inapp', clear(w1) && clear(w2) && w1.lines.length >= 2 && w2.lines.length >= 2,
      `at 360 x 740 in Messenger's browser the hint, the second line and the count keep 72 px below the top and clear of the close button (before ${JSON.stringify(w1)}, during ${JSON.stringify(w2)})`);
    await waitFor(page, "!document.querySelector('[data-testid=live-camera]')", 20000);
    await page.close();
    const page2 = await open('/try?lang=lt&cam=1', 'fake', FB_UA);
    await tap(page2, 'camera-direct');
    await waitFor(page2, "!!document.querySelector('[data-testid=live-shutter]') && !document.querySelector('[data-testid=live-shutter]').disabled", 10000);
    const g = await j(page2, "(() => { const r = (s) => document.querySelector(s).getBoundingClientRect(); const v = r('[data-testid=live-camera]'), h = r('[data-testid=live-hint]'), x = r('[data-testid=live-close]'), s = r('[data-testid=live-shutter]'); return { vTop: Math.round(v.top), vBottom: Math.round(v.bottom), hint: Math.round(h.top - v.top), close: Math.round(x.top - v.top), shutter: Math.round(v.bottom - s.bottom), vv: Math.round(visualViewport.height) }; })()");
    ok('inapp', g.hint >= 72 && g.close >= 72 && g.shutter >= 100 && g.vBottom - g.vTop === g.vv,
      `in Messenger's browser the hint and the close button stand 72 px or more below the view's top and the shutter 100 px or more above its bottom; the view is the visual viewport (${JSON.stringify(g)})`);
    await page2.close();
    const plain = await open('/try?lang=lt&cam=1');
    await tap(plain, 'camera-direct');
    await waitFor(plain, "!!document.querySelector('[data-testid=live-shutter]') && !document.querySelector('[data-testid=live-shutter]').disabled", 10000);
    const p2 = await j(plain, "(() => { const r = (s) => document.querySelector(s).getBoundingClientRect(); const v = r('[data-testid=live-camera]'), s = r('[data-testid=live-shutter]'); return { shutter: Math.round(v.bottom - s.bottom) }; })()");
    ok('inapp', p2.shutter < 100, `in Chrome the bar is not raised (${JSON.stringify(p2)})`);
    await plain.close();
  }

  // ---- darkness: a fake camera that films black (a one-frame Y4M file, looped by Chrome): the second line warns, the shutter stays usable
  {
    const dir = mkdtempSync(join(tmpdir(), 'livecam-'));
    const y4m = join(dir, 'black.y4m');
    writeFileSync(y4m, Buffer.concat([Buffer.from('YUV4MPEG2 W320 H240 F30:1 Ip A1:1 C420jpeg\nFRAME\n'), Buffer.alloc(320 * 240, 16), Buffer.alloc(160 * 120 * 2, 128)]));
    const dark = await launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', `--use-file-for-fake-video-capture=${y4m}`] });
    try {
      const page = await dark.page({ width: 390, height: 844, mobile: true });
      await page.send('Page.addScriptToEvaluateOnNewDocument', { source: SPY('fake') });
      await page.goto(`${origin}/try?lang=lt&cam=1`);
      await page.loaded();
      await waitFor(page, "!!document.querySelector('[data-testid=camera-direct]')", 20000);
      await sleep(600);
      await tap(page, 'camera-direct');
      const warned = await waitFor(page, "!!document.querySelector('[data-testid=live-dark]')", 10000);
      const st = await j(page, "({ line: (document.querySelector('[data-testid=live-dark]') || {}).textContent || '', shutter: !!document.querySelector('[data-testid=live-shutter]') && !document.querySelector('[data-testid=live-shutter]').disabled, burst: !!document.querySelector('[data-testid=live-burst]') })");
      ok('dark', warned && st.line === 'Per tamsu. Prieikite prie lango arba įjunkite šviesą.' && st.shutter && !st.burst,
        `a black picture: the second line says it is too dark, the shutter stays usable (${JSON.stringify(st)})`);
      await page.close();
    } finally {
      await dark.close();
    }
  }

  // ---- fallback
  for (const gum of ['deny', 'none']) {
    const page = await open('/try?lang=lt&cam=1', gum);
    await tap(page, 'camera-direct');
    const got = await waitFor(page, "window.__clicks.some((c) => c.capture === 'environment')", 8000);
    await sleep(300);
    const st = await j(page, "({ view: !!document.querySelector('[data-testid=live-camera]'), clicks: window.__clicks, alert: [...document.querySelectorAll('[role=alert]')].map((e) => e.textContent).join('|'), line: (document.querySelector('[data-testid=cam-fail]') || {}).textContent || '' })");
    ok('fallback', got && !st.view && !st.alert && st.line === `cam: ${gum === 'deny' ? 'denied' : 'unsupported'}`, `${gum === 'deny' ? 'getUserMedia refused' : 'no camera API'}: the capture input opens instead, no view, no error text (${JSON.stringify(st)})`);
    await page.close();
  }

  // ---- off
  {
    const page = await open('/try?lang=lt');
    await tap(page, 'camera-direct');
    await sleep(800);
    const st = await j(page, "({ view: !!document.querySelector('[data-testid=live-camera]'), clicks: window.__clicks, chunk: performance.getEntriesByType('resource').some((r) => /LiveCamera/.test(r.name)), streams: window.__streams.length, line: !!document.querySelector('[data-testid=cam-fail]') })");
    ok('off', !st.view && st.clicks.length === 1 && st.clicks[0].capture === 'environment' && !st.chunk && st.streams === 0 && !st.line,
      `without ?cam=1 the gold button opens the capture input and the camera's chunk is never loaded (${JSON.stringify(st)})`);
    await page.close();
  }
} finally {
  await chrome.close();
  site.close?.();
}
if (problems.length) { console.log(`\nlive camera check FAILED (${problems.length} of ${n}):\n  ${problems.join('\n  ')}`); process.exit(1); }
console.log(`\nlive camera check ok: ${n} checks (the burst with Chrome's fake camera, the fallback to the capture input, nothing for a page without ?cam=1)`);
process.exit(0);
