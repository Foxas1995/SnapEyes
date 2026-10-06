// The run-time catalogue as a page reads it: what GET /api/checkout says can be ordered NOW (the effective stage of every style, which the owner's
// switch in the admin page lowers without a deploy), so that the landing page and the buy card print the number of eyes and the list of styles from
// the server and never from a text. Plain data and functions, no React (the hook of the landing page is src/landing/ordering.ts), so the build's
// checks and the node tests can load it.
//
// Two tokens stand in the copy files where a number of eyes or a list of styles would be printed: {max} (the largest number of eyes some style can be
// ordered for) and {styles} (the art styles that can be ordered for one eye). The legal texts print neither: they are build-time texts and the
// catalogue changes without a build (src/legal, scripts/check_styles.mjs item 7).
//
// When the catalogue cannot be read (offline, the Vite dev server without the API) the build-time registry's CEILINGS are the fallback
// (src/shared/styles.ts): the same answer the server gives while no override is set.
import { STYLE_IDS, STYLES, buildStage, priceClass } from './styles';

export interface RunCatalogue {
  /** The largest number of eyes some style can be ordered for (0: nothing can be ordered). */
  max: number;
  /** The names of the styles of the art price class that can be ordered for one eye, in the registry's tile order. */
  styles: string[];
  /** The ids of the styles (any price class) that can be ordered for one eye NOW: the landing prints a price beside a tile only for these. */
  one: string[];
}

const MAX_EYES = 8;

function artNames(live: (id: string) => boolean, nameOf: (id: string) => string): string[] {
  return STYLE_IDS.filter((id) => priceClass(id) === 'art' && STYLES[id].tile_order > 0 && live(id))
    .sort((a, b) => STYLES[a].legacy - STYLES[b].legacy || STYLES[a].tile_order - STYLES[b].tile_order)
    .map(nameOf);
}

/** The catalogue the build knows: a style counts when its stage is live as the build can tell it (buildStage: the ceiling, held at the registry's
 *  EFFECTIVE_DEFAULT for a style of the v3 engine, so that nothing is orderable before the owner's tick: since the cutover that is nothing at all). What the
 *  page shows until (and unless) the server answers. */
export function fallbackCatalogue(): RunCatalogue {
  let max = 0;
  for (let n = 1; n <= MAX_EYES; n++) if (STYLE_IDS.some((id) => buildStage(id, n) === 'live')) max = n;
  return { max, styles: artNames((id) => buildStage(id, 1) === 'live', (id) => STYLES[id].name), one: STYLE_IDS.filter((id) => buildStage(id, 1) === 'live') };
}

const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);

/** The run-time catalogue from a GET /api/checkout answer (its styles and orderable_max_eyes), or null when the answer has none (an older server):
 *  the caller then keeps the fallback. A style is listed when the server says it is live for one eye; its price class is the registry's. */
export function readCatalogue(info: unknown): RunCatalogue | null {
  if (!isObj(info) || !Array.isArray(info.styles)) return null;
  const max = info.orderable_max_eyes;
  if (typeof max !== 'number' || !Number.isInteger(max) || max < 0 || max > MAX_EYES) return null;
  const liveOne = new Map<string, string>();
  for (const s of info.styles) {
    if (!isObj(s) || typeof s.id !== 'string' || !isObj(s.stages)) continue;
    if (s.stages['1'] === 'live') liveOne.set(s.id, typeof s.name === 'string' && s.name ? s.name : (STYLES[s.id]?.name ?? s.id));
  }
  return { max, styles: artNames((id) => liveOne.has(id), (id) => liveOne.get(id) ?? STYLES[id].name), one: STYLE_IDS.filter((id) => liveOne.has(id)) };
}

/** A text with its tokens filled: {max} the number of eyes, {styles} the list of art styles ("A, B and C" is a language's matter: a plain comma list here). */
export function fillTokens(text: string, c: RunCatalogue): string {
  return text.replace(/\{max\}/g, String(Math.max(c.max, 1))).replace(/\{styles\}/g, c.styles.join(', '));
}
