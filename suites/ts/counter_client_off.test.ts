// The anonymous counter's page half, the scenario "no" (suites/ts/counter_client.test.ts has the yes): its state is one answer, given once, so each scenario is a file of its own
// (the module runner gives every test file a fresh copy of src/shared/counter.ts).
import { count, note } from '../../src/shared/counter';

type Row = [string, boolean, string?];
const tick = () => new Promise<void>((r) => setTimeout(r, 15));

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const g = globalThis as unknown as Record<string, unknown>;
  g.location = { search: '?utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1' };      // the page the tab was opened on
  g.document = { referrer: '' };
  g.sessionStorage = { getItem: () => null, setItem: () => undefined };
  const sent: string[] = [];
  const nav = globalThis.navigator as unknown as Record<string, unknown>;
  const had = Object.getOwnPropertyDescriptor(nav, 'sendBeacon');
  Object.defineProperty(nav, 'sendBeacon', { configurable: true, value: (url: string) => { sent.push(url); return true; } });
  try {
    count('try', 'lt', 'lt');
    note(false);
    count('buy', 'hu', 'hu');
    await tick();
    check('after counter false (the kill switch SNAPEYES_COUNTER, or no store to keep the counts) nothing is sent, neither what waited nor what comes later', sent.length === 0, String(sent.length));
    note(true);
    count('order', 'en', 'eu');
    await tick();
    check('and a later yes changes nothing: the answer of the first /api/health stands', sent.length === 0, String(sent.length));
  } finally {
    if (had) Object.defineProperty(nav, 'sendBeacon', had); else delete nav.sendBeacon;
  }
  return out;
}
