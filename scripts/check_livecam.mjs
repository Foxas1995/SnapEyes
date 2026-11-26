// The live camera of /try (?cam=1, 2026-11-26, src/try/livecam), in real Chrome with Chrome's fake camera (--use-fake-device-for-media-stream,
// --use-fake-ui-for-media-stream: a test pattern and the permission granted) on the built page and the stand-in API (scripts/lib/flowstub.mjs).
//   npm run build && node scripts/check_livecam.mjs [--dist dist]
//   burst     with ?cam=1 the gold button opens our camera view (its facts line shows what the camera gave), one tap on the shutter sends the frames to
//             /api/analyze as live photos with their codes, the view closes and the camera is stopped; the tab remembers ?cam=1
//   fallback  getUserMedia refused (NotAllowedError) or missing: the capture input is opened instead, with no error text and no camera view
//   off       without ?cam=1 the gold button opens the capture input as before and the camera's chunk is never loaded
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
async function open(url, gum = 'fake') {
  const page = await chrome.page({ width: 390, height: 844, mobile: true });
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
    await tap(page, 'camera-direct');
    const opened = await waitFor(page, "!!document.querySelector('[data-testid=live-camera]')", 10000);
    ok('burst', opened, 'the gold button opens the camera view (the tab kept ?cam=1)');
    const ready = await waitFor(page, "!!document.querySelector('[data-testid=live-shutter]') && !document.querySelector('[data-testid=live-shutter]').disabled", 10000);
    const facts = await page.eval("(document.querySelector('[data-testid=live-facts]') || {}).textContent || ''");
    const hint = await page.eval("document.querySelector('[data-testid=live-camera]').textContent");
    ok('burst', ready && /^video \d+x\d+, zoom/.test(facts) && hint.includes('Laikykite akį apskritime'), `the view is ready, shows the hint and the camera's facts: "${facts}"`);
    const clicksBefore = (await j(page, 'window.__clicks')).length;
    await tap(page, 'live-shutter');
    const sent = await waitFor(page, "window.__sent.filter((b) => b.device && b.device.source === 'live').length >= 4", 20000);
    const bodies = await j(page, "window.__sent.map((b) => ({ source: b.device && b.device.source, cap: b.device && b.device.cap, w: b.origWidth, h: b.origHeight }))");
    const cap = bodies[0]?.cap ?? {};
    ok('burst', sent && bodies.length === 4 && bodies.every((b) => b.source === 'live' && b.cap && b.cap.how === 'live' && ['still', 'frame'].includes(b.cap.lm) && /^mp\d+$/.test(b.cap.lres) && ['track', 'css'].includes(b.cap.zoom) && ['yes', 'no'].includes(b.cap.torch) && b.w > 0),
      `one tap sent 4 frames to /api/analyze as live photos with their codes: ${JSON.stringify(bodies.map((b) => [b.w, b.h]))} ${JSON.stringify(cap)}`);
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
    await page.eval("document.querySelector('[data-testid=live-camera] button[aria-label]').click()");
    await sleep(500);
    const st = await j(page, "({ view: !!document.querySelector('[data-testid=live-camera]'), live: window.__streams.flatMap((s) => s.getTracks()).filter((t) => t.readyState !== 'ended').length, sent: window.__sent.length })");
    ok('burst', !st.view && st.live === 0 && st.sent === 0, `the close button closes the view and stops the camera, nothing sent: ${JSON.stringify(st)}`);
    await page.close();
  }

  // ---- fallback
  for (const gum of ['deny', 'none']) {
    const page = await open('/try?lang=lt&cam=1', gum);
    await tap(page, 'camera-direct');
    const got = await waitFor(page, "window.__clicks.some((c) => c.capture === 'environment')", 8000);
    const st = await j(page, "({ view: !!document.querySelector('[data-testid=live-camera]'), clicks: window.__clicks, alert: [...document.querySelectorAll('[role=alert]')].map((e) => e.textContent).join('|') })");
    ok('fallback', got && !st.view && !st.alert, `${gum === 'deny' ? 'getUserMedia refused' : 'no camera API'}: the capture input opens instead, no view, no error text (${JSON.stringify(st)})`);
    await page.close();
  }

  // ---- off
  {
    const page = await open('/try?lang=lt');
    await tap(page, 'camera-direct');
    await sleep(800);
    const st = await j(page, "({ view: !!document.querySelector('[data-testid=live-camera]'), clicks: window.__clicks, chunk: performance.getEntriesByType('resource').some((r) => /LiveCamera/.test(r.name)), streams: window.__streams.length })");
    ok('off', !st.view && st.clicks.length === 1 && st.clicks[0].capture === 'environment' && !st.chunk && st.streams === 0,
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
