// The anonymous counter, the tools' half (api/_lib/counter.py, api/checkout.py): one small beacon for each step of a visit (/try was opened, a photo was
// chosen, the preview was shown, the buy card could not be bought yet, the buy button was pressed, the order page was opened). It holds no cookie and no visitor number: a beacon is the step,
// the page's language and market, the campaign code and what the caller adds (eyes, style, took).
// The server decides whether it counts: every page asks /api/health, whose answer says counter true or false, and calls note() with it. A beacon waits for that answer; if it says no (the
// kill switch SNAPEYES_COUNTER, or no store to keep the counts), or never comes, nothing is sent. A beacon never blocks anything and never reports a failure.
// The campaign code is the only thing kept in the browser, in sessionStorage "snapeyes.c" (until the tab is closed): see capture(). The landing page does not load this file: its beacon is
// the inline script counterScript (src/landing/shell/scripts.ts), so the landing's JavaScript does not grow; the two make the same code (suites/ts/counter_landing.test.ts).

let answer!: (counts: boolean) => void;
const asked = new Promise<boolean>((resolve) => { answer = resolve; });

/** The server's answer (/api/health "counter"): the beacons that waited go out on a yes and are dropped on anything else. */
export const note = (counter: unknown): void => answer(counter === true);

/** The campaign code of the advertisement this visit came from: the utm_ parameters of the address as they stand there ("utm_source=fb&utm_medium=paid&utm_campaign=...", at most 60 characters a
 *  value; the server turns them into short codes or drops them), else the code this tab already holds, else "ref=" and the kind of page the visitor came from (facebook, instagram, tiktok,
 *  google, direct, other). Nothing else of the address is read: a fbclid or any other click number never leaves the browser. */
export const capture = (search: string, referrer: string, stored: string | null): string =>
  (search.match(/utm_(source|medium|campaign|term|content)=[^&]{0,60}/g) ?? []).join('&') || stored || 'ref=' + (referrer.match(/(facebook|instagram|tiktok|google)[.]/)?.[1] ?? (referrer ? 'other' : 'direct'));

let camp: string | undefined;

/** This tab's campaign code, worked out once and kept in sessionStorage "snapeyes.c" (in memory when the browser has none). */
export function campaign(): string {
  if (camp === undefined) {
    let stored: string | null = null;
    try { stored = sessionStorage.getItem('snapeyes.c'); } catch { /* no storage */ }
    camp = capture(location.search, document.referrer, stored);
    try { sessionStorage.setItem('snapeyes.c', camp); } catch { /* the code lives in memory for this page */ }
  }
  return camp;
}

/** A request body with the campaign code added (the analysis, the restoration, the previews and the checkout carry it). */
export const withCamp = <T extends object>(body: T): T => ({ ...body, camp: campaign() });

/** One step reached: hit is the step, lang and market are the page's, extra is what the step adds. */
export function count(hit: 'try' | 'photo' | 'result' | 'soon' | 'buy' | 'order', lang: string, market: string, extra?: object): void {
  const body = JSON.stringify(withCamp({ hit, lang, market, ...extra }));
  void asked.then((on) => on && navigator.sendBeacon('/api/checkout', new Blob([body], { type: 'application/json' })));
}
