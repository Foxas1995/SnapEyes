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

/** The eyes whose slider has already swept in this tab: it never plays twice for one eye (the slider is keyed by the eye, so it remounts when the customer
 *  switches eyes and comes back). A module-level set, as the spec asks. */
const swept = new Set<string>();
export const hasSwept = (eyeId: string): boolean => swept.has(eyeId);
export const markSwept = (eyeId: string): void => { swept.add(eyeId); };
