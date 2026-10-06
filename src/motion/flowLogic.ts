// The decisions of the motion of /try and /order that need no browser: kept apart so that the page-code tests can run them (suites/ts/motion_flow.test.ts).
// No DOM here, no React.

/** The states of an order that are not yet ready: the ones a visit may be in before a file becomes ready. */
const BEFORE_READY: readonly string[] = ['unpaid', 'pending', 'paid', 'making', 'review'];

/** /order: does the state that has just appeared mean "the file became ready while this visit was open"? Only from a state this visit has seen: on the first
 *  load there is no previous state (undefined or null), and a page opened from the e-mail link in ready must not play the reveal (spec 8, finding F-1). */
export const intoReady = (prev: string | null | undefined, next: string | null | undefined): boolean => next === 'ready' && typeof prev === 'string' && BEFORE_READY.includes(prev);

/** /order: which card is on screen. A card is named by what it shows, so that "paid" and "making" (one card) do not count as a change between cards. */
export const cardOf = (state: string | null | undefined, stop: string | null | undefined): string => (stop ? `stop:${stop}` : !state ? 'load' : state === 'paid' ? 'making' : state);

/** /order: has the visit moved from one card to another? The first card (the one that replaces the loading card) is not a move: it is the page arriving. */
export const moved = (prev: string, next: string): boolean => prev !== next && prev !== 'load' && next !== 'load';

/** /try, the plain before and after slider: the one auto sweep that teaches the drag (7.5). From 92 to 50 percent, after 400 ms in view, 1 s, expo out. */
export const SWEEP = { from: 92, to: 50, delayMs: 400, durationMs: 1000 } as const;

/** The position of the sweep after `ms` of its duration: expo out (the page's own curve, cubic-bezier(.16, 1, .3, 1), to within a pixel). */
export function sweepAt(ms: number): number {
  const t = Math.min(1, Math.max(0, ms / SWEEP.durationMs));
  const e = t >= 1 ? 1 : 1 - 2 ** (-10 * t);
  return SWEEP.from + (SWEEP.to - SWEEP.from) * e;
}

/** How much of the slider must be in the window before it counts as seen (the sweep starts 400 ms after that): 60 percent of the slider. */
export const SWEEP_SEEN = 0.6;

/** How long a slider that is only PART in the window (at least half of what it needs, less than all of it) may wait before it counts as seen anyway. A bar over it, a window it
 *  hardly fits, a browser that reports another height than the one the customer sees: the handle is never left at 92 (the customer's photo, the picture hidden). */
export const SWEEP_PARTIAL_MS = 3500;

/** The share of the slider (its height) that must be in the window for the sweep: SWEEP_SEEN of the slider, or, when the slider is taller than the window (a
 *  phone held sideways, a page zoomed to 200 percent, a short window: the slider is a square as wide as the page), SWEEP_SEEN of what the window can show of it.
 *  Asking 60 percent of a slider that cannot be shown to 60 percent left the handle at 92 for ever (review I3, M1). */
export function sweepNeed(boxH: number, viewH: number): number {
  if (!(boxH > 0) || !(viewH > 0)) return SWEEP_SEEN;
  return SWEEP_SEEN * Math.min(1, viewH / boxH);
}

/** Is `ratio` (the observer's share of the slider in the window) enough? A hair of tolerance: the observer's ratio and the threshold are floats of two kinds. */
export const sweepSeen = (ratio: number, need: number): boolean => ratio >= need - 0.005;

/** Is `ratio` at least half of what is needed? Only such a slider counts as part in the window (SWEEP_PARTIAL_MS): one that peeks into the window by a few pixels
 *  is not looked at, and its sweep, which happens once per eye, must not be spent on nobody. */
export const sweepPart = (ratio: number, need: number): boolean => ratio >= need / 2 - 0.005;

/** A picture of an artwork frame (src/motion/ArtImage.tsx): the motion it comes in with. */
export interface Layer { id: number; src: string; mode: 'plain' | 'open' | 'fade' }

/** Is the arrival of a frame spent by this change of its top picture (`prev` to `next`)? Two changes spend it without the opening's own `animationend`: the
 *  picture that was opening was replaced by another (the customer chose another style within the 1.3 s: the end event never comes), and the first picture came in
 *  plain (a decode that came late, or reduced motion: no opening will run). An arrival that stays unspent opens again at the next mount of the frame, for
 *  instance when an eye is taken away (review I3, m4). The ordinary end of the opening is `settle` in ArtImage. */
export const arrivalSpent = (prev: Layer | null, next: Layer | null): boolean => !!next && ((!!prev && prev.mode === 'open' && next.id !== prev.id) || (prev === null && next.mode === 'plain'));

/** The eyes whose slider has already swept in this tab: it never plays twice for one eye (the slider is keyed by the eye, so it remounts when the customer
 *  switches eyes and comes back). A module-level set, as the spec asks. */
const swept = new Set<string>();
export const hasSwept = (eyeId: string): boolean => swept.has(eyeId);
export const markSwept = (eyeId: string): void => { swept.add(eyeId); };
