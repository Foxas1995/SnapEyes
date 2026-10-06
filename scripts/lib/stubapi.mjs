// The answer of GET /api/checkout as the landing reads it, for the checks that run against a build with no server behind it (check_landing.mjs,
// check_motion_close.mjs, check_landing_states.mjs, the build's gate in check_landing_assets.mjs) and for the local viewer (serve_preview.mjs). It is made from the
// registry (api/_lib/styles_registry.py), the way the server makes it (api/_lib/catalogue.py public_catalogue): every style at preview or live, with its stage per
// number of eyes.
//
//   closed (open: false)  the owner has ticked nothing: every style is held at the registry's EFFECTIVE_DEFAULT (preview), orderable_max_eyes is 0;
//   open   (open: true)   the owner has switched on every style whose ceiling is live (what the cutover's table allows): Clean Iris, Powder Burst, Universe,
//                         Splash, Celestial Gold with one eye and Family Colours with three; the others stay at preview. This is the state in which the
//                         page prints prices (src/landing/ordering.ts: open needs the deployment to take orders AND a style that can be ordered now).
//   ticked                which styles the owner has switched on: true (every live ceiling), false (none) or a list of registry ids (only those, each up to its
//                         ceiling). The default follows `open`, so the two states above are what they always were; the states "ordering open, nothing ticked" and
//                         "one style ticked" are { open: true, ticked: false } and { open: true, ticked: [id] }.
//
// No price is written here and no style id: the registry is read.
import { join } from 'node:path';
import { loadRegistry, ceilingOf } from '../styles_source.mjs';

const RANK = { planned: 0, lab: 1, preview: 2, live: 3 };
const MAX_EYES = 8;

/** The public catalogue ({styles, orderable_max_eyes}) of a state: ticked = true switches the live ceilings on, a list of ids switches those on, false (or an id that
 *  is not listed) holds the style at the effective default. */
export function catalogueAnswer(root, ticked) {
  const reg = loadRegistry(root);
  const hold = reg.effectiveDefault || 'live';
  const on = (id) => (Array.isArray(ticked) ? ticked.includes(id) : !!ticked);
  const styles = [];
  let max = 0;
  for (const [id, d] of Object.entries(reg.styles)) {
    if (d.legacy === 1) continue;
    const stages = {};
    for (let n = d.eyes[0]; n <= d.eyes[1]; n++) {
      const c = ceilingOf(d, n);
      if (c === null || c === 'retired') continue;
      const s = on(id) || RANK[c] <= RANK[hold] ? c : hold;
      if (s === 'preview' || s === 'live') stages[String(n)] = s;
      if (s === 'live' && n > max) max = n;
    }
    if (Object.keys(stages).length) styles.push({ id, name: d.name, slug: d.slug, group: d.group, eyes: [...d.eyes], stages });
  }
  return { styles, orderable_max_eyes: Math.min(max, MAX_EYES) };
}

/** The whole answer: {ok, open, suggest, styles, orderable_max_eyes}. ticked follows `open` unless it is given. */
export function checkoutAnswer(root, { open, suggest = null, ticked = open }) {
  return { ok: true, open, suggest, ...catalogueAnswer(root, ticked) };
}

/** The first style of the registry (in tile order) the owner could switch on for one eye: a live ceiling, the art class, a tile in the picker's first group. Used
 *  by the checks for the state "one style ticked": the id comes from the registry, never from a written list. */
export function firstLiveOneEyeStyle(root) {
  const reg = loadRegistry(root);
  const ids = Object.entries(reg.styles)
    .filter(([, d]) => d.legacy === 0 && d.price_class === 'art' && d.tile_order > 0 && ceilingOf(d, 1) === 'live')
    .sort((a, b) => a[1].tile_order - b[1].tile_order)
    .map(([id]) => id);
  return ids[0] ?? null;
}

export const repoRoot = (scriptsDir) => join(scriptsDir, '..');
