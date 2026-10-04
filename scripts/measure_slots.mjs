// The heights of the empty slots that hold the place of the lazy sections (src/landing/slots.ts), measured on a build in real Chrome.
//   node scripts/measure_slots.mjs [--dist dist] [--write | --check]
// It opens the page in English, German, Lithuanian and Hungarian at 375 px (phone), 768 px (tablet) and 1280 px (desktop), waits until
// every section is mounted, and reads the height of each section. Without a flag it prints the table; --write rewrites
// src/landing/slots.ts from it; --check exits 1 when a slot in slots.ts is more than 12 percent away from the real section (a section
// that grew or shrank after a copy change: the page then jumps by the difference when the section arrives, in a browser without scroll
// anchoring). Run it after a build (npm run build) whenever the copy or a section's layout changes.
import { readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { launch, sleep } from './lib/cdp.mjs';
import { serve } from './lib/static.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const dist = resolve(opt('--dist', join(ROOT, 'dist')));
const LANGS = ['en', 'de', 'lt', 'hu'];
const LAYOUTS = [['phone', 375], ['tablet', 768], ['desktop', 1280]];
const IDS = ['reveal', 'wall', 'styles', 'how', 'pricing', 'closeups', 'trust', 'faq', 'final', 'sizes', 'more'];
const SLOTS = join(ROOT, 'src/landing/slots.ts');
const TOLERANCE = 0.12;

const handler = (req, res) => {
  const url = new URL(req.url, 'http://x');
  const json = (o) => { res.writeHead(200, { 'content-type': 'application/json', 'cache-control': 'no-store' }); res.end(JSON.stringify(o)); };
  if (url.pathname === '/api/health') { json({ stripe: true, stripe_live: false, email: false }); return true; }
  if (url.pathname === '/api/checkout') { json({ ok: true, open: false, suggest: null }); return true; }
  if (url.pathname.startsWith('/api/')) { res.writeHead(404, { 'content-type': 'application/json' }); res.end('{}'); return true; }
  return false;
};

async function measure() {
  const site = await serve(dist, { vercelFile: join(ROOT, 'vercel.json'), handler });
  const chrome = await launch();
  const origin = `http://127.0.0.1:${site.port}`;
  const out = {};
  try {
    for (const lang of LANGS) {
      out[lang] = {};
      for (const [label, width] of LAYOUTS) {
        // a first visit every time: the page remembers a chosen language
        const wipe = await chrome.page({ width: 400, height: 300 });
        await wipe.goto(`${origin}/imprint?lang=en`);
        await wipe.loaded();
        await wipe.send('Storage.clearDataForOrigin', { origin, storageTypes: 'all' }).catch(() => undefined);
        await wipe.close();
        const page = await chrome.page({ width, height: 900, mobile: width < 800, dpr: 1 });
        await page.goto(`${origin}/?lang=${lang}`);
        await page.loaded();
        for (let i = 0; i < 150; i++) {
          if (await page.eval("document.querySelector('.lp-slot') === null && !!document.getElementById('faq') && !!document.querySelector('.lp-ftr')")) break;
          await sleep(100);
        }
        await sleep(600);
        const H = await page.eval('document.documentElement.scrollHeight');
        for (let y = 0; y < H + 200; y += 600) { await page.eval(`window.scrollTo({ top: ${y}, behavior: 'instant' })`); await sleep(40); }
        await page.eval('Promise.all([...document.images].map((i) => (i.complete ? 1 : new Promise((r) => { i.onload = i.onerror = r; setTimeout(r, 3000); }))))');
        await sleep(300);
        out[lang][label] = JSON.parse(await page.eval(`JSON.stringify(Object.fromEntries(${JSON.stringify(IDS)}.map((id) => [id, Math.round(document.getElementById(id)?.getBoundingClientRect().height ?? -1)])))`));
        await page.close();
      }
    }
  } finally {
    await chrome.close();
    await site.close();
  }
  return out;
}

function render(d) {
  const rows = IDS.map((id) => `  ${id}: { id: '${id}', h: { ${LANGS.map((l) => `${l}: [${LAYOUTS.map(([lay]) => d[l][lay][id]).join(', ')}]`).join(', ')} } },`).join('\n');
  return `import type { CSSProperties } from 'react';
import type { Lang } from '../shared/lang';

// The height of each lazy section of the page, so that the empty slot that holds its place until the section is mounted is as tall as the
// section will be (src/App.tsx Slot). Written by \`node scripts/measure_slots.mjs --write\` from the built page in real Chrome: [phone, tablet,
// desktop] per language, where phone is the layout below 640 px (measured at 375 px), tablet from 640 px (768 px) and desktop from 960 px
// (1280 px), ordering closed, EU market, details closed. The words differ in length between the languages, so each language has its own
// numbers: with one mean for all four a slot was up to 190 px off and the page jumped by that much when a section arrived above the
// reader (a browser without scroll anchoring, Safari, shows it). The numbers only have to be near: a slot is replaced within a moment, and
// a section's real height also depends on the market and on whether ordering is open (\`--check\` fails above ${TOLERANCE * 100} percent). The
// ids are the sections' own: a link to #pricing has its target while the section is on its way.
export const SLOT_HEIGHTS = {
${rows}
} as const;

export type SlotName = keyof typeof SLOT_HEIGHTS;

/** The style that gives the empty slot (class lp-slot, src/landing/css/base.css) its three heights, in the page's language. */
export function slotStyle(name: SlotName, lang: Lang): CSSProperties {
  const [phone, tablet, desktop] = SLOT_HEIGHTS[name].h[lang];
  return { '--slot-p': \`\${phone}px\`, '--slot-t': \`\${tablet}px\`, '--slot-d': \`\${desktop}px\` } as CSSProperties;
}
`;
}

const real = await measure();
if (args.includes('--write')) {
  writeFileSync(SLOTS, render(real), 'utf8');
  console.log('src/landing/slots.ts written');
} else if (args.includes('--check')) {
  const text = readFileSync(SLOTS, 'utf8');
  const bad = [];
  for (const id of IDS) {
    const m = new RegExp(`${id}: \\{ id: '${id}', h: \\{ ([^}]*) \\}`).exec(text);
    if (!m) { bad.push(`${id}: not in slots.ts`); continue; }
    for (const l of LANGS) {
      const nums = new RegExp(`${l}: \\[(\\d+), (\\d+), (\\d+)\\]`).exec(m[1]);
      if (!nums) { bad.push(`${id} ${l}: not in slots.ts`); continue; }
      LAYOUTS.forEach(([lay], i) => {
        const want = +nums[i + 1], got = real[l][lay][id];
        if (got < 0 || Math.abs(got - want) / got > TOLERANCE) bad.push(`${id} ${l} ${lay}: slot ${want} px, section ${got} px`);
      });
    }
  }
  if (bad.length) {
    console.error(`slot heights are off (${bad.length}); run node scripts/measure_slots.mjs --write:\n  ${bad.join('\n  ')}`);
    process.exit(1);
  }
  console.log('slot heights ok (every slot within 12 percent of its section, 4 languages x 3 layouts)');
} else {
  console.log(JSON.stringify(real));
}
