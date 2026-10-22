// The poster of the hero's globe: its first view (the still arrangement every visitor sees first, the one prefers-reduced-motion keeps), captured
// from the built landing in headless Chrome over a transparent page (scripts/make_globe_assets.py paints it on the page's own dark: the hero has no
// other background behind the stage). 1440 x 900 at pixel ratio 2.5 (the stage is about 545 px wide there: a picture of more than 1200 px, cut down
// to the three widths).
//   npm run build && node scripts/make_globe_poster.mjs <out.png> [--dist dist]
// then: python scripts/make_globe_assets.py --src <folder> --poster <out.png> && python scripts/build_landing_assets.py --src <folder> && npm run build
import { writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const out = args.find((a) => a.endsWith('.png'));
if (!out) {
  console.error('give the PNG to write: node scripts/make_globe_poster.mjs <out.png>');
  process.exit(2);
}
const dist = resolve(args.includes('--dist') ? args[args.indexOf('--dist') + 1] : join(ROOT, 'dist'));
const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(o)); };
  if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { json({ ok: true, open: false, suggest: null }); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404); res.end('{}'); return true; }
  return false;
};
const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
const chrome = await launch();
try {
  const page = await chrome.page({ width: 1440, height: 900, dpr: 2.5, reduceMotion: true });
  await page.goto(`http://127.0.0.1:${site.port}/?lang=en`);
  await page.loaded(30000);
  for (let i = 0; i < 200 && !(await page.eval("!!document.querySelector('#root #heroGlobe[data-live]')")); i++) await sleep(100);
  if (!(await page.eval("!!document.querySelector('#root #heroGlobe[data-live]')"))) throw new Error('the live globe did not come');
  await page.eval('Promise.all([...document.querySelectorAll(".lp-gl img")].map((i) => i.decode().catch(() => 0))).then(() => true)');
  // only the globe, over nothing: the page, the hero's bloom, the poster under it and the closed copy of an opened artwork are hidden
  await page.eval(`(() => { const s = document.createElement('style'); s.textContent = 'html, body { background: transparent !important } body * { visibility: hidden !important } .lp-gl, .lp-gl * { visibility: visible !important } .lp-gl-open, .lp-gl-open * { visibility: hidden !important }'; document.head.appendChild(s); return 1; })()`);
  await page.send('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  await sleep(500);
  const r = JSON.parse(await page.eval("JSON.stringify(document.querySelector('#root #heroGlobe').getBoundingClientRect())"));
  const shot = await page.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false, clip: { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 } });
  writeFileSync(out, Buffer.from(shot.data, 'base64'));
  console.log(`poster: the stage ${Math.round(r.width)} x ${Math.round(r.height)} CSS px at pixel ratio 2.5 -> ${out}`);
} finally {
  await chrome.close();
  await site.close();
}
