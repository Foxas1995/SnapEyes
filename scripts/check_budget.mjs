// The byte budget of the landing's motion work (motion spec 10), as a gate and not a report.
//   npm run build && npm run check:budget          (or: node scripts/check_budget.mjs [--dist dist])
// It adds up the gzip size (level 6) of every script and stylesheet of dist/assets that the landing can request (the chunks of /try, /order, /admin and the legal
// pages are left out) and compares it with the page without any motion (commit 37e61c8, built the same way): JS 233,345 B, CSS 26,921 B. The spec's budget for the
// motion work is +6 kB of JS (hard stop +8 kB, no new dependency) and +7 kB of CSS; a number over the budget is printed, a number over the hard stop fails.
// The hard stop of the CSS is not in the spec: +7.5 kB is the figure this gate uses until the owner says otherwise (the review of 2026-10-05 measured +6.9 kB before
// its own fixes and the page is at +7.3 kB now). Vercel serves brotli, which is smaller: the unit is the same on both sides of the comparison, so the difference is what counts.
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const dist = resolve(args.includes('--dist') ? args[args.indexOf('--dist') + 1] : join(ROOT, 'dist'));

// The base moved with the release integration (landing-v2 merged with the style engine): the registry text and its reader (src/shared/styles.ts), the run-time
// catalogue (src/shared/catalogue.ts) and the price class in src/shared/markets.ts are shared modules that the landing now bundles too, and the page gates its tiles
// and prices by them (src/landing/tileStyle.ts, StyleTile, PriceTable, ordering.ts). That is not motion: INTEGRATION is what this script measured on the merged tree
// minus what it measured on the landing-v2 tip (4e541c6: JS 240,524 B, CSS 34,182 B, the numbers the owner accepted at +7.2 kB and +7.3 kB over the motionless page).
// Re-measure it after a change of those modules: build both trees, run this script on each, take the difference.
const MOTIONLESS = { js: 233345, css: 26921 };
// The release review fixes (2026-10-07) moved it by +827 B JS and +90 B CSS: the sentence about the shared plate library and the other honesty wordings in four languages
// (src/landing/copy), the price line that carries no price while it is held (heroPrice.ts), the forced-colours rules. Not motion either; the motion still has the room it had.
const INTEGRATION = { js: 9344 + 827, css: 727 + 90 };
// The shared chunk of /try and /order (checkout-*.js and checkout-*.css: what the two tools import together) is not named after a page, so this script counts it, but the
// landing never loads it (wiring check of scripts/check_motion_flow.mjs, and src/main.tsx imports none of it). The motion of the tools (task I3: the flow stylesheet, the arc, the
// rings, the picture that opens, the capture diagram) lives there: TOOLS is its growth, measured as that chunk's gzip size (level 6) on the commit with the motion minus the commit
// before it (5c9054c). Re-measure it when the motion of the tools changes: build both, `gzip -6` the two checkout-* files of each, take the difference.
const TOOLS = { js: 1515, css: 2008 };   // the review fix of the motion changed the shared chunk by +157 B JS (the slider's in-view rule, the arrival that is spent, the frame's waiting marks) and -10 B CSS (the tile fade left); measured on the two builds
const BASE = { js: MOTIONLESS.js + INTEGRATION.js + TOOLS.js, css: MOTIONLESS.css + INTEGRATION.css + TOOLS.css };
const BUDGET = { js: 6000, css: 7000 };
const HARD = { js: 8000, css: 7500 };
const OTHER_PAGES = /^(try|order|admin|terms|privacy|imprint|withdrawal)(-|\.)/;

const sum = { js: 0, css: 0 };
for (const f of readdirSync(join(dist, 'assets'))) {
  const ext = f.endsWith('.js') ? 'js' : f.endsWith('.css') ? 'css' : null;
  if (!ext || OTHER_PAGES.test(f)) continue;
  sum[ext] += gzipSync(readFileSync(join(dist, 'assets', f)), { level: 6 }).length;
}

let failed = false;
for (const ext of ['js', 'css']) {
  const added = sum[ext] - BASE[ext];
  const label = ext === 'js' ? 'JavaScript' : 'CSS';
  const text = `${label}: ${sum[ext]} B gzip, ${added >= 0 ? '+' : ''}${added} B over the page without motion (budget +${BUDGET[ext]}, hard stop +${HARD[ext]})`;
  if (added > HARD[ext]) { failed = true; console.log(`  FAIL ${text}`); }
  else if (added > BUDGET[ext]) console.log(`  note ${text}: over the budget, under the hard stop`);
  else console.log(`  ok   ${text}`);
}
console.log(failed ? '\nbudget check FAILED' : '\nbudget check ok');
process.exit(failed ? 1 : 0);
