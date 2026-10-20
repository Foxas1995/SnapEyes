// The header of /try on narrow phones: the brand line ("Private Atelier · preview") must not run over the logo. Under 380 px its longest
// word (peržiūra, előnézet, Vorschau) did not fit beside the logo and the language switch and printed over the logo (QA, 2026-10-20).
//   node scripts/check_try_header.mjs [--dist dist]        real Chrome on the built page, 320 to 412 px, four languages
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const dist = resolve(args.includes('--dist') ? args[args.indexOf('--dist') + 1] : join(ROOT, 'dist'));
const WIDTHS = [320, 340, 360, 375, 390, 412];
const LANGS = ['en', 'de', 'lt', 'hu'];

// every text box of the header outside the logo, against the logo's box
const PROBE = `(() => {
  const h = document.querySelector('header');
  const logo = h && h.querySelector('a');
  if (!h || !logo) return JSON.stringify({ err: 'no header' });
  const lr = logo.getBoundingClientRect();
  const hit = [];
  const range = document.createRange();
  const walker = document.createTreeWalker(h, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (!n.textContent.trim() || logo.contains(n)) continue;
    range.selectNodeContents(n);
    for (const r of range.getClientRects()) {
      if (r.width > 0 && r.left < lr.right - 0.5 && r.right > lr.left && r.top < lr.bottom && r.bottom > lr.top) hit.push(n.textContent.trim().slice(0, 30) + ' ' + Math.round(r.left) + '-' + Math.round(r.right));
    }
  }
  return JSON.stringify({ hit, over: document.documentElement.scrollWidth > innerWidth + 1 });
})()`;

const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json') });
const chrome = await launch();
const problems = [];
let n = 0;
try {
  for (const lang of LANGS) {
    for (const width of WIDTHS) {
      const page = await chrome.page({ width, height: 740, mobile: true, dpr: 2 });
      await page.goto(`http://127.0.0.1:${site.port}/try?lang=${lang}`);
      let r = null;
      for (let i = 0; i < 80 && !r; i++) {
        await sleep(100);
        try { const v = JSON.parse(await page.eval(PROBE)); if (!v.err) r = v; } catch { /* still loading */ }
      }
      await page.close();
      n++;
      if (!r) problems.push(`${lang} ${width}px: the header did not render`);
      else if (r.hit.length) problems.push(`${lang} ${width}px: text over the logo: ${r.hit.join('; ')}`);
      else if (r.over) problems.push(`${lang} ${width}px: the page is wider than the screen`);
    }
  }
} finally {
  await chrome.close();
  await site.close();
}
if (problems.length) {
  console.log(problems.map((p) => `  FAIL ${p}`).join('\n'));
  console.log(`${problems.length} of ${n} fail`);
  process.exit(1);
}
console.log(`  ok   /try header: no text over the logo in ${LANGS.length} languages at ${WIDTHS.join(', ')} px (${n} pages)`);
