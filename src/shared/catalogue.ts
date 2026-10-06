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
  /** The numbers of eyes some style can be ordered for NOW, ascending (the Trio alone is [3]): the landing prints a price for a count of eyes only when it is in here. */
  eyes: number[];
  /** For each style that can be ordered for some count NOW, the counts it can be ordered for (an id that is not a key cannot be bought at all): the gallery's
   *  tiles ask it (liveFor) for the style and the count of eyes they show, so a Soon tile never carries a price. */
  by: Record<string, number[]>;
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
  const eyes: number[] = [];
  const by: Record<string, number[]> = {};
  for (let n = 1; n <= MAX_EYES; n++) {
    for (const id of STYLE_IDS) if (buildStage(id, n) === 'live') (by[id] ??= []).push(n);
    if (STYLE_IDS.some((id) => buildStage(id, n) === 'live')) eyes.push(n);
  }
  return { max: eyes.length ? eyes[eyes.length - 1] : 0, styles: artNames((id) => buildStage(id, 1) === 'live', (id) => STYLES[id].name), one: STYLE_IDS.filter((id) => buildStage(id, 1) === 'live'), eyes, by };
}

const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);

/** The run-time catalogue from a GET /api/checkout answer (its styles and orderable_max_eyes), or null when the answer has none (an older server):
 *  the caller then keeps the fallback. A style is listed when the server says it is live for one eye; its price class is the registry's. */
export function readCatalogue(info: unknown): RunCatalogue | null {
  if (!isObj(info) || !Array.isArray(info.styles)) return null;
  const max = info.orderable_max_eyes;
  if (typeof max !== 'number' || !Number.isInteger(max) || max < 0 || max > MAX_EYES) return null;
  const liveOne = new Map<string, string>();
  const counts = new Set<number>();
  const by: Record<string, number[]> = {};
  for (const s of info.styles) {
    if (!isObj(s) || typeof s.id !== 'string' || !isObj(s.stages)) continue;
    if (s.stages['1'] === 'live') liveOne.set(s.id, typeof s.name === 'string' && s.name ? s.name : (STYLES[s.id]?.name ?? s.id));
    for (let n = 1; n <= MAX_EYES; n++) if (s.stages[String(n)] === 'live') { counts.add(n); (by[s.id] ??= []).push(n); }
  }
  return { max, styles: artNames((id) => liveOne.has(id), (id) => liveOne.get(id) ?? STYLES[id].name), one: STYLE_IDS.filter((id) => liveOne.has(id)), eyes: [...counts].sort((a, b) => a - b), by };
}

/** Can this style be ordered for n eyes NOW (the server's effective stage is live)? A gallery tile prints its price only when this is true for the style
 *  and the number of eyes it shows; otherwise it says Soon. An id the catalogue does not know, or a count it does not list, is false. */
export function liveFor(c: RunCatalogue, id: string, n: number): boolean {
  return c.by?.[id]?.includes(n) === true;
}

/** May a page say that ordering is open? Only when the deployment takes orders (GET /api/checkout "open": Stripe, the e-mail and the legal texts, pay.ordering_problem())
 *  AND some style can be ordered now. A deployment that takes orders while the owner has ticked nothing (the state the cutover leaves) sells nothing: every checkout
 *  would be refused with 409 style_unavailable, so the landing keeps its "opens soon" lines and prints no price. */
export function ordersOpen(deploymentOpen: boolean, c: RunCatalogue): boolean {
  return deploymentOpen && c.max >= 1;
}

/** The lowest price among the styles that can be ordered for one eye now (the "from" of the hero line), or null when none can: the page then prints no price. */
export function fromOneEye(c: RunCatalogue, priceOf: (id: string) => number): number | null {
  const prices = c.one.map(priceOf).filter((p) => Number.isFinite(p) && p > 0);
  return prices.length ? Math.min(...prices) : null;
}

/** The largest number of eyes up to which EVERY count from two eyes can be ordered now (0 when two eyes cannot): the several-eyes card prints its ladder (two eyes, then each further eye) and
 *  the words "two to {max} eyes" only for counts that can all be bought. The Trio alone (three eyes, no pair) is 0: the card says "free preview now", never a price for two eyes. */
export function severalMax(c: RunCatalogue): number {
  let m = 1;
  while (m < MAX_EYES && c.eyes.includes(m + 1)) m++;
  return m >= 2 ? m : 0;
}

/** Which price rows of the one-eye card may be printed: the row of the black class only while its one style can be ordered for one eye now, the row "any other style"
 *  only while some style of the art class can. With neither, the card says "free preview now" and prints no price. */
export function oneEyeRows(c: RunCatalogue, blackStyle: string): { black: boolean; art: boolean } {
  return { black: c.one.includes(blackStyle), art: c.styles.length > 0 };
}

/** A text with its tokens filled: {max} the number of eyes, {styles} the list of art styles ("A, B and C" is a language's matter: a plain comma list here). */
export function fillTokens(text: string, c: RunCatalogue): string {
  return text.replace(/\{max\}/g, String(Math.max(c.max, 1))).replace(/\{styles\}/g, c.styles.join(', '));
}
