// The answer of GET /api/checkout as the landing reads it, for the checks that run against a build with no server behind it (check_landing.mjs,
// check_motion_close.mjs) and for the local viewer (serve_preview.mjs). It is made from the registry (api/_lib/styles_registry.py), the way the server
// makes it (api/_lib/catalogue.py public_catalogue): every style at preview or live, with its stage per number of eyes.
//
//   closed (open: false)  the owner has ticked nothing: every style is held at the registry's EFFECTIVE_DEFAULT (preview), orderable_max_eyes is 0;
//   open   (open: true)   the owner has switched on every style whose ceiling is live (what the cutover's table allows): Clean Iris, Powder Burst, Universe,
//                         Splash, Celestial Gold with one eye and Family Colours with three; the others stay at preview. This is the state in which the
//                         page prints prices (src/landing/ordering.ts: open needs the deployment to take orders AND a style that can be ordered now).
//
// No price is written here and no style id: the registry is read.
import { join } from 'node:path';
import { loadRegistry, ceilingOf } from '../styles_source.mjs';

const RANK = { planned: 0, lab: 1, preview: 2, live: 3 };
const MAX_EYES = 8;

/** The public catalogue ({styles, orderable_max_eyes}) of a state: ticked = the live ceilings are switched on, else every style is held at the effective default. */
export function catalogueAnswer(root, ticked) {
  const reg = loadRegistry(root);
  const hold = reg.effectiveDefault || 'live';
  const styles = [];
  let max = 0;
  for (const [id, d] of Object.entries(reg.styles)) {
    if (d.legacy === 1) continue;
    const stages = {};
    for (let n = d.eyes[0]; n <= d.eyes[1]; n++) {
      const c = ceilingOf(d, n);
      if (c === null || c === 'retired') continue;
      const s = ticked || RANK[c] <= RANK[hold] ? c : hold;
      if (s === 'preview' || s === 'live') stages[String(n)] = s;
      if (s === 'live' && n > max) max = n;
    }
    if (Object.keys(stages).length) styles.push({ id, name: d.name, slug: d.slug, group: d.group, eyes: [...d.eyes], stages });
  }
  return { styles, orderable_max_eyes: Math.min(max, MAX_EYES) };
}

/** The whole answer: {ok, open, suggest, styles, orderable_max_eyes}. */
export function checkoutAnswer(root, { open, suggest = null }) {
  return { ok: true, open, suggest, ...catalogueAnswer(root, open) };
}

export const repoRoot = (scriptsDir) => join(scriptsDir, '..');
