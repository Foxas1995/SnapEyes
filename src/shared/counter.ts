// The anonymous counter, the page's half (api/_lib/counter.py, api/checkout.py): one small beacon for each step of a visit (the landing page was opened, /try was opened, a photo was
// chosen, the preview was shown, the buy card could not be bought yet, the buy button was pressed, the order page was opened). It holds no cookie and no visitor number and keeps nothing
// in the browser: a beacon is the step, the page's language and market and what the caller adds (eyes, style, took).
// The server decides whether it counts: every page asks /api/health, whose answer says counter true or false, and calls note() with it. A beacon waits for that answer; if it says no (the
// kill switch SNAPEYES_COUNTER, or no store to keep the counts), or never comes, nothing is sent. A beacon never blocks anything and never reports a failure.
// Small on purpose: the landing page carries it (npm run check:budget).

let answer!: (counts: boolean) => void;
const asked = new Promise<boolean>((resolve) => { answer = resolve; });

/** The server's answer (/api/health "counter"): the beacons that waited go out on a yes and are dropped on anything else. */
export const note = (counter: unknown): void => answer(counter === true);

/** One step reached: hit is the step, lang and market are the page's, extra is what the step adds. */
export function count(hit: 'landing' | 'try' | 'photo' | 'result' | 'soon' | 'buy' | 'order', lang: string, market: string, extra?: object): void {
  const body = JSON.stringify({ hit, lang, market, ...extra });
  void asked.then((on) => on && navigator.sendBeacon('/api/checkout', new Blob([body], { type: 'application/json' })));
}
