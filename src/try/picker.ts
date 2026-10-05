// The style picker of /try as a state machine: what the server's tile list says (api/compose.py: tiles, pick, eyes) turned into what the page shows.
// Pure functions, no React, no DOM, no fetch, no import of the registry: the page passes in the little it knows (which eye counts a style takes).
// The server decides everything about the list (which styles exist for this many eyes, their order, which is recommended, which are held back and
// why, which can be bought now); the page owns no list of styles and only renders this. src/try/picker.test.ts-style checks are in
// suites/ts/picker_state.test.ts.
//
// Words used below, from the plan (INTEGRATION_SPEC 1.6, 1.7, 1.8, 2.5):
//   stage     live (can be bought), preview ("Soon": drawn for free, never sold), lab and the rest never reach a customer
//   policy    the style's gate policy: advisory (a failing eye only warns: the tile is drawn and can be bought) or hard (the style is held back for
//             that set of eyes: "Retake eye N first"), none (the six old styles: nothing)
//   rule      the rule set a style's gate reads: lid (an eyelid, lash or skin inside the ring) or fill (the Universe fill: a reflection, a hard edge)

/** the three groups of the landing page (src/landing, wave-lp: one, two, family); decided by the number of eyes, never asked */
export type GroupKey = 'one' | 'two' | 'family';
export type Policy = 'none' | 'advisory' | 'hard';
export type GateRule = 'lid' | 'fill';

/** One tile as /api/compose sends it (api/_lib/catalogue.py tile_row, plus image and plan8 once a batch drew it). */
export interface ServerTile {
  id: string;
  name: string;
  slug: string;
  group: string;
  legacy: number;
  stage: string;
  available: boolean;
  why: string | null;            // gate, reseal, bar_pupil: why the eyes cannot take this style (available false)
  layouts: string[];
  eyes: number;
  price_class: string;
  looks: Record<string, string>; // {look: stage}: the Universe chips
  gate: Policy;
  rule: GateRule;
  pick: boolean;
}

/** One eye as the server read its seal (api/compose.py _eyes_reply). gate: true passes, false fails, null unknown (a seal without a profile). */
export interface ServerEye {
  eye: number;
  eye_id: string | null;
  cls: string | null;
  pupil: string | null;
  gate: { lid: boolean | null; fill: boolean | null };
  why: string[];
}

/** What the page keeps of a tile list: for the eyes of `key`, in the server's order (the recommended first). */
export interface Catalog {
  key: string;
  n: number;
  tiles: ServerTile[];
  pick: string | null;           // the recommended tile (always one that can be bought now), null when nothing can be
  reasonKey: string | null;      // the key of its reason line, null unless it was picked for the set's colour class
  eyes: ServerEye[];
}

const str = (v: unknown): string => (typeof v === 'string' ? v : '');
const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const policyOf = (v: unknown): Policy => (v === 'hard' || v === 'advisory' ? v : 'none');
const ruleOf = (v: unknown): GateRule => (v === 'fill' ? 'fill' : 'lid');
const tri = (v: unknown): boolean | null => (v === true ? true : v === false ? false : null);

/** The tile list of a compose reply, checked: a reply this page does not understand is null (never a crash). n: the eye count asked about. */
export function parseCatalog(reply: unknown, key: string, n: number): Catalog | null {
  if (!isObj(reply) || !Array.isArray(reply.tiles)) return null;
  const tiles: ServerTile[] = [];
  for (const t of reply.tiles) {
    if (!isObj(t) || !str(t.id) || !str(t.name)) continue;
    const looks: Record<string, string> = {};
    if (isObj(t.looks)) for (const [k, v] of Object.entries(t.looks)) if (typeof v === 'string') looks[k] = v;
    tiles.push({
      id: str(t.id), name: str(t.name), slug: str(t.slug) || str(t.id), group: str(t.group), legacy: t.legacy === 1 ? 1 : 0, stage: str(t.stage),
      available: t.available === true, why: typeof t.why === 'string' ? t.why : null,
      layouts: Array.isArray(t.layouts) ? t.layouts.filter((x): x is string => typeof x === 'string') : [],
      eyes: typeof t.eyes === 'number' ? t.eyes : n, price_class: str(t.price_class), looks, gate: policyOf(t.gate), rule: ruleOf(t.rule), pick: t.pick === true,
    });
  }
  const eyes: ServerEye[] = [];
  if (Array.isArray(reply.eyes)) {
    for (const e of reply.eyes) {
      if (!isObj(e)) continue;
      const g = isObj(e.gate) ? e.gate : {};
      eyes.push({
        eye: typeof e.eye === 'number' ? e.eye : eyes.length + 1, eye_id: typeof e.eye_id === 'string' ? e.eye_id : null,
        cls: typeof e.cls === 'string' ? e.cls : null, pupil: typeof e.pupil === 'string' ? e.pupil : null,
        gate: { lid: tri(g.lid), fill: tri(g.fill) }, why: Array.isArray(e.why) ? e.why.filter((x): x is string => typeof x === 'string') : [],
      });
    }
  }
  // The recommended tile is always one that can be bought now (live and the eyes take it). A pick that is not (a server that got this wrong) is ignored:
  // the page never recommends a style that opens soon, is held back, or is not in the list.
  const asked = isObj(reply.pick) && str(reply.pick.id) ? str(reply.pick.id) : null;
  const pick = asked && tiles.some((t) => t.id === asked && t.available && t.stage === 'live') ? asked : null;
  const reasonKey = pick && isObj(reply.pick) && str(reply.pick.reason) ? str(reply.pick.reason) : null;
  return { key, n, tiles, pick, reasonKey, eyes };
}

// ------------------------------------------------------------------------------------------------ groups

/** The landing page's three groups by the number of eyes. */
export const groupOf = (n: number): GroupKey => (n <= 1 ? 'one' : n === 2 ? 'two' : 'family');

export const isLive = (t: ServerTile): boolean => t.stage === 'live';
export const isSoon = (t: ServerTile): boolean => t.stage === 'preview';

/** The group has examples and none of them can be bought yet: the page then says it once for the group instead of a Soon chip on every tile
 *  (INTEGRATION_SPEC 1.8 rule 3). A group with no tiles at all is not "soon": there is nothing to show. */
export const groupAllSoon = (tiles: readonly ServerTile[]): boolean => tiles.length > 0 && !tiles.some(isLive);

// ------------------------------------------------------------------------------------------------ one tile

export type TileState =
  | { kind: 'ready' }                                  // live and the eyes take it
  | { kind: 'soon' }                                   // opens soon: drawn for free, never sold
  | { kind: 'gate'; eye: number }                      // held back: retake this eye first
  | { kind: 'reseal'; eye: number }                    // the eye has no sealed gate value (an older preview): make the preview of it again
  | { kind: 'pupil' };                                 // the eyes' pupil shape (a bar) is not for this style

/** The eyes (1-based) whose value for the tile's rule is `want` (false: it fails; null: it has no sealed value). */
const eyesWith = (t: ServerTile, eyes: readonly ServerEye[], want: boolean | null): number[] => eyes.filter((e) => e.gate[t.rule] === want).map((e) => e.eye);
const failingEye = (t: ServerTile, eyes: readonly ServerEye[], want: boolean | null): number => eyesWith(t, eyes, want)[0] ?? 1;

/** What a tile shows and does. A tile the eyes cannot take is never drawn; a Soon tile is drawn and marked. */
export function tileState(t: ServerTile, eyes: readonly ServerEye[]): TileState {
  if (!t.available) {
    if (t.why === 'bar_pupil') return { kind: 'pupil' };
    if (t.why === 'reseal') return { kind: 'reseal', eye: failingEye(t, eyes, null) };
    return { kind: 'gate', eye: failingEye(t, eyes, false) };
  }
  return isSoon(t) ? { kind: 'soon' } : { kind: 'ready' };
}

/** The tiles that need a picture: available, drawn for a customer (live or preview), in the server's order. */
export const drawable = (t: ServerTile): boolean => t.available && (isLive(t) || isSoon(t));

/** The Universe chips of a tile: its looks in the server's order, each with its stage; the first one is the style's default. */
export function looksOf(t: ServerTile): { code: string; soon: boolean }[] {
  return Object.entries(t.looks).map(([code, stage]) => ({ code, soon: stage === 'preview' }));
}
export const defaultLook = (t: ServerTile): string | null => Object.keys(t.looks)[0] ?? null;
/** The look a style is drawn and ordered in: the wanted one when the style has it, else the style's default; null for a style with no looks. A request
 *  that names no look draws the default one, and checkout asks whether THAT look can be bought (api/_lib/catalogue.py look_orderable). */
export const lookOf = (t: ServerTile | undefined, want: string | null): string | null =>
  t && Object.keys(t.looks).length ? (want && t.looks[want] ? want : defaultLook(t)) : null;
/** What the customer has chosen opens soon: the style itself, or (a style that can be bought) the look on screen. A Soon look under a live style is drawn for
 *  free and never sold: the tile is live and the look is not (the server caps a look at its style's stage and no more). */
export const soonChoice = (t: ServerTile | undefined, look: string | null): boolean => !!t && (isSoon(t) || (look !== null && t.looks[look] === 'preview'));

/** The proper names of the Universe looks (English in every language, like every style name). A code that is not listed is shown as it came. */
const LOOK_NAMES: Record<string, string> = { echo: 'Echo', vortex: 'Vortex', deepfield: 'Deep Field', starfield: 'Starfield' };
export const lookName = (code: string): string => LOOK_NAMES[code] ?? code;

// ------------------------------------------------------------------------------------------------ the selected style

export type Changed =
  | { kind: 'eyes'; from: string; to: string; range: [number, number] }    // the chosen style does not take this many eyes
  | { kind: 'gate'; from: string; to: string; eye: number }                // the eyes need a retake before the chosen style can be shown
  | { kind: 'reseal'; from: string; to: string; eye: number }
  | { kind: 'pupil'; from: string; to: string };

export interface Resolved { style: string | null; changed: Changed | null }

/** The style the page shows: what the customer asked for (want) when this tile list has it and the eyes can take it, else the recommended tile,
 *  else (nothing can be bought: a group that opens soon) the first tile that can be drawn. A saved choice that is simply not listed any more (a
 *  retired style from an older page, a style the owner took back) falls back to the recommended tile without a word; the line `changed` is only
 *  for the cases the customer can understand and act on: the eye count (the old tile list "switches to the new group"), a retake, a pupil.
 *  eyesOf: the eye counts a style id takes (the registry, src/shared/styles.ts), null for an id nobody knows. */
export function resolveStyle(a: {
  n: number; tiles: readonly ServerTile[]; pick: string | null; eyes: readonly ServerEye[]; want: string | null;
  eyesOf: (id: string) => readonly [number, number] | null;
}): Resolved {
  const { tiles, want } = a;
  const buyable = (id: string | null) => (id ? tiles.find((t) => t.id === id && t.available) : undefined);
  const fallback = (): string | null =>
    buyable(a.pick)?.id ?? tiles.find((t) => t.available && isLive(t))?.id ?? tiles.find(drawable)?.id ?? null;
  if (want) {
    const t = tiles.find((x) => x.id === want);
    if (t && t.available) return { style: want, changed: null };
    const to = fallback();
    if (t && to) {
      const st = tileState(t, a.eyes);
      if (st.kind === 'gate') return { style: to, changed: { kind: 'gate', from: want, to, eye: st.eye } };
      if (st.kind === 'reseal') return { style: to, changed: { kind: 'reseal', from: want, to, eye: st.eye } };
      if (st.kind === 'pupil') return { style: to, changed: { kind: 'pupil', from: want, to } };
    }
    if (!t && to) {
      const r = a.eyesOf(want);
      if (r && (a.n < r[0] || a.n > r[1])) return { style: to, changed: { kind: 'eyes', from: want, to, range: [r[0], r[1]] } };
    }
    return { style: to, changed: null };
  }
  return { style: fallback(), changed: null };
}

/** The layout the selected tile is drawn in: the wanted one when this tile takes it, else the tile's own first (the server's default). */
export const layoutOf = (t: ServerTile | undefined, want: string | null): string | null =>
  t ? (want && t.layouts.includes(want) ? want : t.layouts[0] ?? null) : null;

// ------------------------------------------------------------------------------------------------ the retake state

/** The two sentences a customer reads about a failing eye (INTEGRATION_SPEC 2.5, 1.6.2): something inside the ring, or a reflection left. */
export type RetakeReason = 'lid' | 'reflection';
/** The one capture tip that matches: open eye and lifted lid, daylight and no flash, or the grey iris's soft edge. */
export type RetakeTip = 'open' | 'light' | 'grey';

/** A gate reason code (api/_lib/styles/gate.py WHY) as one of the two sentences. Only a catchlight is a reflection; every other code says
 *  something is inside the ring or at its rim, and a code this page does not know says the same (the sentence never claims a cause it does not
 *  know: it names the ring). */
export function reasonOf(code: string): RetakeReason {
  return code === 'fill_catchlight' ? 'reflection' : 'lid';
}

export interface RetakeView {
  eyes: number[];              // 1-based positions whose restoration fails a rule: they hold a tile back, or warn on the selected advisory style
  reseal: number[];            // 1-based positions with no sealed gate value (an older preview): the preview of that eye has to be made again
  pupil: number[];             // 1-based positions whose pupil shape holds a tile back (the collision styles refuse a bar pupil): the eyes with a bar pupil,
                               // or every eye when the engine refused and the profiles do not say which; empty when no tile is held for the pupil
  reasons: RetakeReason[];     // the distinct sentences to show for `eyes`, in the order of the eyes
  tip: RetakeTip;
  why: string;                 // the first reason code, for the one counted click on the manual route
  holds: boolean;              // some tile is held back by these eyes (a hard style); false: the selected style only warns (advisory)
  deadEnd: boolean;            // nothing in the list can be bought now: the manual route (e-mail the best photos) is offered
}

const codesOf = (e: ServerEye): string[] => (e.why.length ? e.why : ['lid_ring_outliers']);

/** The retake state: null when no eye needs one. An eye needs a retake when it holds back at least one tile of the list (a hard style whose rule
 *  it fails, or a pupil shape the style refuses) or, for an advisory selected style, when it fails that style's rule (the style is still drawn and can be
 *  bought, with a warning). A set whose every tile is held for its pupils has a state too (no eye fails a rule, yet nothing can be drawn): never a frame
 *  that waits for a picture that will not come (INTEGRATION_SPEC 1.6.2 rule 3). */
export function retakeView(a: { tiles: readonly ServerTile[]; eyes: readonly ServerEye[]; selected: ServerTile | undefined }): RetakeView | null {
  const failing = new Set<number>();
  const reseal = new Set<number>();
  let holds = false;
  let pupilHold = false;
  for (const t of a.tiles) {
    const st = tileState(t, a.eyes);
    // every eye that fails the tile's rule needs the retake, not only the first one (the tile's own label names the first)
    if (st.kind === 'gate') { eyesWith(t, a.eyes, false).forEach((n) => failing.add(n)); failing.add(st.eye); holds = true; }
    if (st.kind === 'reseal') { eyesWith(t, a.eyes, null).forEach((n) => reseal.add(n)); reseal.add(st.eye); }
    if (st.kind === 'pupil') pupilHold = true;
  }
  for (const n of advisoryEyes(a.selected, a.eyes)) failing.add(n);
  // the eyes whose pupil is a bar; the engine can refuse a pupil the profile did not show (usePreviews marks the tile), then every eye is named
  const bars = a.eyes.filter((e) => e.pupil === 'bar').map((e) => e.eye);
  const pupil = pupilHold ? (bars.length ? bars : a.eyes.map((e) => e.eye)).sort((x, y) => x - y) : [];
  if (!failing.size && !reseal.size && !pupil.length) return null;
  const eyes = [...failing].sort((x, y) => x - y);
  const rows = eyes.map((n) => a.eyes.find((e) => e.eye === n)).filter((e): e is ServerEye => !!e);
  const reasons: RetakeReason[] = [];
  for (const e of rows) for (const c of codesOf(e)) { const r = reasonOf(c); if (!reasons.includes(r)) reasons.push(r); }
  const first = rows[0];
  // the one tip: for a pupil alone the open eye (round pupils show with the eye wide open and in even light)
  const tip: RetakeTip = !eyes.length && pupil.length ? 'open'
    : reasons.includes('reflection') && !reasons.includes('lid') ? 'light' : first?.cls === 'grey' ? 'grey' : reasons.includes('lid') ? 'open' : 'light';
  return {
    eyes, reseal: [...reseal].sort((x, y) => x - y), pupil, reasons: eyes.length && !reasons.length ? ['lid'] : reasons, tip,
    why: (first ? codesOf(first)[0] : '') || (pupil.length && !reseal.size ? 'bar_pupil' : 'reseal'), holds,
    deadEnd: !a.tiles.some((t) => isLive(t) && t.available),
  };
}

/** The eyes (1-based) that fail the rule of the selected style when that style only warns (advisory): the warning under the picture, on the chip
 *  and above the buy button. A hard style that fails is not selectable (the server holds it back), and the six old styles (policy none) never warn. */
export function advisoryEyes(selected: ServerTile | undefined, eyes: readonly ServerEye[]): number[] {
  if (!selected || selected.gate !== 'advisory') return [];
  return eyes.filter((e) => e.gate[selected.rule] === false).map((e) => e.eye);
}

// ------------------------------------------------------------------------------------------------ the buy card

export type BuyState =
  | { kind: 'normal' }                                  // the selected style can be bought (the card shows its price and the waiver)
  | { kind: 'soon'; look?: string }                     // the selected style opens soon, or (look: its code) the look on screen does: one line, no price, no button
  | { kind: 'countSoon'; n: number }                    // no style of this many eyes can be bought yet: one line
  | { kind: 'none' };                                   // nothing is selected (nothing can be drawn for these eyes: the retake state says why)

/** What the buy card does. look: the look the customer has on screen (src/try/picker.ts lookOf); absent, the style's default look, which is what a request
 *  that names none draws and what checkout asks about, so a Soon look never reaches a price or a button (checkout would refuse it: 409 style_unavailable). */
export function buyState(a: { n: number; tiles: readonly ServerTile[]; selected: ServerTile | undefined; look?: string | null }): BuyState {
  if (!a.tiles.some(isLive)) return a.tiles.length ? { kind: 'countSoon', n: a.n } : { kind: 'none' };
  if (!a.selected) return { kind: 'none' };
  if (isSoon(a.selected)) return { kind: 'soon' };
  const look = lookOf(a.selected, a.look ?? null);
  return look !== null && soonChoice(a.selected, look) ? { kind: 'soon', look } : { kind: 'normal' };
}

// ------------------------------------------------------------------------------------------------ what to draw next

/** The tiles that still need a picture, the next `k` of them in the server's order (the page draws two at a time and shows a skeleton for the rest).
 *  has(t): the picture exists or is on its way. */
export function nextTiles(tiles: readonly ServerTile[], has: (t: ServerTile) => boolean, k = 2): ServerTile[] {
  return tiles.filter((t) => drawable(t) && !has(t)).slice(0, k);
}

/** A tile's price, printed on the tile only in the one-eye group, only for a tile that can be bought now (never a Soon tile, nor a live style whose default
 *  look opens soon): the price is the caller's (src/shared/markets.ts priceMinor reads the price class), this only decides whether to print it. */
export const showsPrice = (n: number, t: ServerTile): boolean => n === 1 && isLive(t) && t.available && !soonChoice(t, defaultLook(t));

// ------------------------------------------------------------------------------------------------ keys

/** The identity of a set of eyes for the funnel: the ids, in any order (moving an eye is not a new set). */
export const setKey = (ids: readonly string[]): string => [...ids].sort().join('.');
/** A picture's cache key: eyes in canvas order, what was asked, the language (the watermark's words). */
export const artKey = (parts: ReadonlyArray<string | number | null | undefined>): string => parts.map((p) => (p === null || p === undefined ? '' : String(p))).join('|');

/** The options of the page that may reach the server (api/compose.py opts): swap for two eyes, rotate for three, a look. */
export interface Opts { swap: boolean; rotate: number; look: string | null }
export const NO_OPTS: Opts = { swap: false, rotate: 0, look: null };

/** The options that apply to this tile for n eyes, in the wire form of /api/compose (the server drops what does not apply; the page does not send
 *  it, so the cache key says only what changes the picture). The old styles ignore all three. */
export function wireOpts(t: ServerTile | undefined, n: number, o: Opts): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  if (!t || t.legacy === 1) return out;
  if (n === 2 && o.swap) out.swap = true;
  if (n === 3 && o.rotate % 3 !== 0) out.rotate = o.rotate % 3;
  // a style with looks is always asked for one by name (the chosen one, else its default): the picture and the plan then say which look they are
  const look = o.look && t.looks[o.look] ? o.look : defaultLook(t);
  if (look) out.look = look;
  return out;
}
