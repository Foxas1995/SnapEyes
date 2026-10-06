// The landing page's speed, measured the way BUILD_PLAN section 5 measures it: real Chrome over CDP, a phone (375 px wide, pixel
// ratio 2.6), the CPU 4 times slower, 1.6 Mbit/s down, 150 ms round trip (slow 4G), no cache, brotli from the server like the
// CDN. Reports LCP (and its element), CLS (and what moved), total blocking time, what was fetched, and when React took the page
// over from the prerendered shell.
//   node scripts/measure_landing.mjs [--dist dist] [--runs 3] [--path /] [--desktop] [--flicker] [--waterfall] [--budget]
// --flicker: a screencast through the handoff, and a count of frames in which the hero picture disappears for a moment.
// --budget: exit 1 when a run is over the budget (LCP 1.6 s, CLS 0.05).
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const runs = +opt('--runs', 3);
const path = opt('--path', '/');
const desktop = flag('--desktop');
const SWAP = `
window.__swap = null;
new MutationObserver((_, o) => { if (!document.getElementById('shell') && document.getElementById('root') && document.getElementById('root').childElementCount) { window.__swap = Math.round(performance.now()); o.disconnect(); } }).observe(document, { childList: true, subtree: true });
`;

const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json') });
const chrome = await launch();
const origin = `http://127.0.0.1:${site.port}`;
const rows = [];
let over = 0;
try {
  for (let i = 0; i < runs; i++) {
    const page = await chrome.page(desktop
      ? { width: 1366, height: 768, dpr: 1, vitals: true, cpu: 4, throttle: { latency: 150, down: 200000, up: 93750 } }
      : { width: 375, height: 812, mobile: true, dpr: 2.6, vitals: true, cpu: 4, throttle: { latency: 150, down: 200000, up: 93750 } });
    await page.send('Page.addScriptToEvaluateOnNewDocument', { source: SWAP });
    const reqs = new Map();
    page.on((e) => {
      if (e.method === 'Network.requestWillBeSent') reqs.set(e.params.requestId, { url: e.params.request.url, bytes: 0, t: e.params.timestamp });
      if (e.method === 'Network.loadingFinished' && reqs.has(e.params.requestId)) {
        reqs.get(e.params.requestId).bytes = e.params.encodedDataLength;
        reqs.get(e.params.requestId).end = e.params.timestamp;
      }
    });
    const frames = [];
    if (flag('--flicker')) {
      page.on((e) => {
        if (e.method === 'Page.screencastFrame') {
          frames.push({ t: e.params.metadata.timestamp, data: e.params.data });
          page.send('Page.screencastFrameAck', { sessionId: e.params.sessionId }).catch(() => undefined);
        }
      });
      await page.send('Page.startScreencast', { format: 'jpeg', quality: 55, maxWidth: desktop ? 683 : 375, maxHeight: desktop ? 384 : 812, everyNthFrame: 1 });
    }
    await page.goto(`${origin}${path}`);
    await sleep(9000);
    const v = JSON.parse(await page.eval('JSON.stringify({ lcp: window.__lcp, cls: window.__cls, shifts: window.__shifts, tbt: Math.round(window.__tbt), paint: window.__paint, swap: window.__swap, h: document.documentElement.scrollHeight })'));
    const lcp = v.lcp.at(-1) || [0, '', 0];
    const fetched = [...reqs.values()].filter((r) => r.bytes > 0);
    const kb = (n) => Math.round(n / 1000);
    const first = fetched.filter((r) => (r.t - [...reqs.values()][0].t) * 1000 < 3000);
    let flicker = null;
    if (frames.length) {
      const probe = await chrome.page({ width: 400, height: 300 });
      // per frame: the mean brightness of the hero picture's area (the lower half of the screen on a phone, the right half on a desktop)
      const expr = `(async () => {
        const out = [];
        for (const f of ${JSON.stringify(frames.map((x) => x.data))}) {
          const im = await new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = 'data:image/jpeg;base64,' + f; });
          const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0);
          const r = ${desktop ? '[im.width * 0.58, im.height * 0.25, im.width * 0.4, im.height * 0.6]' : '[im.width * 0.1, im.height * 0.72, im.width * 0.8, im.height * 0.25]'};
          const d = g.getImageData(r[0], r[1], r[2], r[3]).data; let s = 0; for (let k = 0; k < d.length; k += 4) s += d[k] * 0.3 + d[k + 1] * 0.6 + d[k + 2] * 0.1;
          out.push(Math.round(s / (d.length / 4)));
        }
        return JSON.stringify(out);
      })()`;
      const lum = JSON.parse(await probe.eval(expr));
      await probe.close();
      // the picture is on screen once its area is clearly brighter than the page; a flicker is a later frame where it falls back to the page colour
      const base = lum[0];
      const seen = lum.findIndex((x) => x > base + 25);
      const dips = seen < 0 ? [] : lum.slice(seen + 1).map((x, k) => [k + seen + 1, x]).filter(([, x]) => x < base + 10);
      flicker = { frames: lum.length, pictureAtFrame: seen, dips: dips.length, lum: lum.join(',') };
    }
    if (flag('--waterfall')) {
      const t0 = Math.min(...[...reqs.values()].map((r) => r.t));
      console.log(`run ${i + 1} waterfall (ms from the first request: start-end, kB, file):`);
      for (const r of [...reqs.values()].sort((a, b) => a.t - b.t)) console.log(`  ${Math.round((r.t - t0) * 1000)}-${r.end ? Math.round((r.end - t0) * 1000) : '?'} ${Math.round(r.bytes / 100) / 10} ${r.url.replace(origin, '').slice(0, 90)}`);
    }
    rows.push({ run: i + 1, lcp: lcp[0], el: lcp[1], cls: +v.cls.toFixed(4), shifts: v.shifts, tbt: v.tbt, fcp: v.paint['first-contentful-paint'], swap: v.swap, requests: fetched.length, kb: kb(fetched.reduce((s, r) => s + r.bytes, 0)), kbFirst3s: kb(first.reduce((s, r) => s + r.bytes, 0)), flicker });
    if (lcp[0] > 1600 || v.cls > 0.05) over++;
    await page.close();
  }
} finally {
  await chrome.close();
  await site.close();
}
console.log(`${desktop ? 'desktop 1366x768' : 'phone 375 px, pixel ratio 2.6'}, CPU x4, 1.6 Mbit/s, 150 ms, ${path}, ${runs} runs`);
for (const r of rows) {
  console.log(`run ${r.run}: LCP ${r.lcp} ms (${r.el.slice(0, 60)}), FCP ${r.fcp} ms, CLS ${r.cls}, TBT ${r.tbt} ms, React took over at ${r.swap} ms, ${r.requests} requests ${r.kb} kB (${r.kbFirst3s} kB in the first 3 s)${r.shifts.length ? ', shifts ' + JSON.stringify(r.shifts) : ''}`);
  if (r.flicker) console.log(`   screencast: ${r.flicker.frames} frames, picture on screen from frame ${r.flicker.pictureAtFrame}, frames where it disappears again: ${r.flicker.dips}\n   brightness per frame: ${r.flicker.lum}`);
}
const med = (k) => rows.map((r) => r[k]).sort((a, b) => a - b)[Math.floor(rows.length / 2)];
console.log(`median LCP ${med('lcp')} ms, CLS ${med('cls')}`);
if (flag('--budget') && over) {
  console.error(`${over} run(s) over the budget (LCP 1600 ms, CLS 0.05)`);
  process.exit(1);
}
