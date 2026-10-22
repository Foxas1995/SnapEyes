// LAB: what the centrepiece costs on the wire, from the production build of the lab page (./vite.lab.config.mjs) in headless Chrome:
//   * the lazy code of each prototype: its own chunk, the shared chunk and its stylesheet, gzip (what the landing would add; React is already there);
//   * the pictures a visitor actually downloads: the poster, the discs of the first view, and after a tap (the globe) the sharp picture in front,
//     on a phone (412 x 915 at pixel ratio 2.625) and a desktop (1440 x 900), counted from the network (Network.loadingFinished).
//   node scripts/lab/sphere/bytes.mjs <base url> <dist dir> <out.json>
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { launch, sleep } from '../../lib/cdp.mjs';

const [base = 'http://127.0.0.1:5282', dist, outPath = 'bytes.json'] = process.argv.slice(2);
const assets = join(dist, 'assets');
const files = readdirSync(assets);
const gz = (f) => gzipSync(readFileSync(join(assets, f)), { level: 9 }).length;
const pick = (re) => files.filter((f) => re.test(f));
const code = {};
for (const piece of ['Globe', 'Ring']) {
  const js = [...pick(new RegExp(`^${piece}-.*\\.js$`)), ...pick(/^motion-.*\.js$/)];
  const css = pick(new RegExp(`^${piece}-.*\\.css$`));
  code[piece.toLowerCase()] = {
    files: [...js, ...css],
    jsGzip: js.reduce((a, f) => a + gz(f), 0),
    cssGzip: css.reduce((a, f) => a + gz(f), 0),
  };
}

const chrome = await launch();
const views = { phone: { width: 412, height: 915, dpr: 2.625, mobile: true }, desktop: { width: 1440, height: 900, dpr: 1, mobile: false } };
const wire = [];
try {
  for (const piece of ['globe', 'ring']) {
    for (const [device, view] of Object.entries(views)) {
      const page = await chrome.page(view);
      await page.send('Network.setCacheDisabled', { cacheDisabled: true });
      const req = new Map();
      const done = [];
      page.on((d) => {
        if (d.method === 'Network.responseReceived') req.set(d.params.requestId, d.params.response.url);
        if (d.method === 'Network.loadingFinished') done.push({ url: req.get(d.params.requestId) || '', bytes: d.params.encodedDataLength, t: Date.now() });
      });
      await page.goto(`${base}/src/lab/sphere.html?p=${piece}&lang=lt&ui=0`);
      await page.loaded(30000);
      for (let i = 0; i < 100 && !(await page.eval("!!document.querySelector('.lab-frame[data-ready]')")); i++) await sleep(50);
      const sum = (fn) => done.filter((x) => fn(x.url)).reduce((a, x) => a + x.bytes, 0);
      const count = (fn) => done.filter((x) => fn(x.url)).length;
      const isDisc0 = (u) => /-(160|240)-[^/]*\.webp/.test(u);
      const first = { discs: sum(isDisc0), count: count(isDisc0) };
      await sleep(3000);
      const isPoster = (u) => /\/(globe|ring)-(640|1200)-[^/]*\.webp/.test(u);
      const isDisc = (u) => /-(160|240)-[^/]*\.webp/.test(u);
      const isSharp = (u) => /-480-[^/]*\.webp/.test(u);
      const isChunk = (u) => /\/(Globe|Ring|motion)-[^/]*\.(js|css)$/.test(u);
      const row = { piece, device, poster: sum(isPoster), discsFirstView: first.discs, discCountFirstView: first.count, discsAfter3s: sum(isDisc), discCountAfter3s: count(isDisc), chunkOnWire: sum(isChunk) };
      if (piece === 'globe') {
        const p = await page.eval("(() => { const b = [...document.querySelectorAll('.sx-disc')].find((x) => x.style.pointerEvents !== 'none' && x.getAttribute('aria-label').startsWith('Halo')); const r = b.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()");
        await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: p.x, y: p.y, button: 'left', buttons: 1, clickCount: 1 });
        await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x, y: p.y, button: 'left', buttons: 0, clickCount: 1 });
        await sleep(1500);
        row.sharpOnTap = sum(isSharp);
      }
      wire.push(row);
      await page.close();
    }
  }
} finally {
  await chrome.close();
}
const img = (px) => files.filter((f) => new RegExp(`-${px}-[^.]*\\.webp$`).test(f) && !/^(globe|ring)-/.test(f)).reduce((a, f) => a + readFileSync(join(assets, f)).length, 0);
const out = { code, imageSets: { disc160: img(160), disc240: img(240), sharp480: img(480) }, wire };
writeFileSync(outPath, JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
