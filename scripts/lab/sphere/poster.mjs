// LAB: the still poster of each prototype: its first view (the virtual clock at 0, ?rec), the stage alone (?shot), without the words, captured
// in headless Chrome at 1200 px and saved as WebP at 1200 and 640 px into src/lab/poster (the lab page paints it before the code arrives).
//   node scripts/lab/sphere/poster.mjs [base url]     (then python scripts/lab/sphere/poster_webp.py)
import { launch, sleep } from '../../lib/cdp.mjs';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const base = process.argv[2] || 'http://127.0.0.1:5281';
const out = join(process.cwd(), 'src', 'lab', 'poster');
mkdirSync(out, { recursive: true });
const chrome = await launch();
try {
  for (const piece of ['globe', 'ring']) {
    const page = await chrome.page({ width: 800, height: 1000, dpr: 1.5, mobile: false });
    await page.goto(`${base}/src/lab/sphere.html?p=${piece}&shot&rec&lang=en`);
    await page.loaded(30000);
    for (let i = 0; i < 200 && !(await page.eval('!!(window.__sx && window.__sx.ready)')); i++) await sleep(100);
    await page.eval('Promise.all([...document.images].map((i) => i.decode().catch(() => 0))).then(() => true)');
    await page.eval('window.__sx.step(0)');
    await sleep(300);
    const r = JSON.parse(await page.eval("JSON.stringify(document.querySelector('.lab-frame').getBoundingClientRect())"));
    const shot = await page.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false, clip: { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 } });
    writeFileSync(join(out, `${piece}.png`), Buffer.from(shot.data, 'base64'));
    console.log(piece, Math.round(r.width), 'x', Math.round(r.height));
    await page.close();
  }
} finally {
  await chrome.close();
}
