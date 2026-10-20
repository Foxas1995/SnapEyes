// The anonymous feedback box, the tools' half (api/_lib/feedback.py, api/checkout.py): six chips and an optional text of up to 300 characters, on the result screen and on the card that asks for
// another photo (src/try/Feedback.tsx). It holds no cookie, no visitor number and writes nothing to the browser: that a place has been answered is remembered in this page's memory only, so
// the box does not ask twice in one visit, and a reload may show it again.
// The server decides whether the box is offered: /api/health says feedback true or false (the switch SNAPEYES_FEEDBACK, somewhere to keep the answers, the daily clean-up that deletes the
// texts after 90 days), and the page calls noteFeedback() with it. Until that answer comes, or when it says no, the box is not shown.
// Nothing is sent until the visitor presses Send, and then ONE request: the chip, the style on screen or the block reason, the number of eyes, the text, the campaign code, the language.

import { campaign } from './counter';

let answer!: (on: boolean) => void;
const asked = new Promise<boolean>((resolve) => { answer = resolve; });

/** The server's answer (/api/health "feedback"): the boxes that waited are shown on a yes and stay away on anything else. */
export const noteFeedback = (feedback: unknown): void => answer(feedback === true);

/** The promise of that answer (the box waits for it). */
export const feedbackAsked = (): Promise<boolean> => asked;

export type Place = 'result' | 'retake';

/** The six chips of each place: the codes api/_lib/feedback.py CHIPS accepts (a test holds the two equal). The words are src/try/copy*.ts feedback.chips. */
export const CHIPS: Record<Place, readonly string[]> = {
  result: ['love', 'likeness', 'colour', 'style', 'price', 'other'],
  retake: ['unclear', 'fine', 'device', 'only', 'effort', 'other'],
};

export const TEXT_MAX = 300;
const TIMEOUT_MS = 12_000;

/** What the box sends: w the place, c the chip, x the style on screen (result) or the block reason (retake), eyes how many eyes are on the artwork, t the text, hp the honeypot (always empty for a person). */
export interface Answer { w: Place; c: string; x?: string; eyes?: number; t?: string; hp?: string }

/** What came of it: kept (the text was stored), none (no text came, or it was counted without one), dropped (the text looked like contact details, a link or noise and was not kept), lost (the
 *  server could not store the text), failed (nothing reached the server: say so and let the visitor try again). */
export type Outcome = 'kept' | 'none' | 'dropped' | 'lost' | 'failed';

const answered = new Set<Place>();
/** Has this place been answered in this visit (this page's memory only)? */
export const wasAnswered = (w: Place): boolean => answered.has(w);
export const markAnswered = (w: Place): void => { answered.add(w); };
/** For the tests: forget what was answered. */
export const forgetAnswered = (): void => answered.clear();

/** Send one answer. The campaign code (src/shared/counter.ts) rides along, as in every request of the tools; no credentials are sent (no cookie). Never throws. */
export async function sendFeedback(a: Answer, lang: string, market: string, post: typeof fetch = fetch): Promise<Outcome> {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  try {
    const t = (a.t ?? '').trim().slice(0, TEXT_MAX);
    const body = JSON.stringify({ feedback: { w: a.w, c: a.c, ...(a.x ? { x: a.x } : {}), ...(a.eyes ? { eyes: a.eyes } : {}), ...(t ? { t } : {}), hp: a.hp ?? '' }, camp: campaign(), lang, market });
    const r = await post('/api/checkout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, credentials: 'omit', keepalive: true, signal: ctl.signal });
    if (!r.ok) return 'failed';
    const d = (await r.json()) as { ok?: unknown; text?: unknown };
    if (d?.ok !== true) return 'failed';
    return d.text === 'kept' || d.text === 'dropped' || d.text === 'lost' ? d.text : 'none';
  } catch {
    return 'failed';
  } finally {
    clearTimeout(timer);
  }
}
