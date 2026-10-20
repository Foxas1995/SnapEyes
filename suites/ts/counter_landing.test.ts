// The anonymous counter on the landing page (2026-10-20): the beacon is a script in the head of index.html (src/landing/shell/scripts.ts counterScript), not part of the page's JavaScript. This
// runs that very string in a sandbox with a stand-in window and checks what it sends against src/shared/counter.ts capture() over a matrix of addresses, referrers and stored codes: the two
// must make the same campaign code. Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import vm from 'node:vm';
import { gzipSync } from 'node:zlib';
import { readFileSync } from 'node:fs';
import { counterScript, prefetchScript } from '../../src/landing/shell/scripts';
import { capture } from '../../src/shared/counter';

type Row = [string, boolean, string?];

interface Page { search: string; referrer: string; stored: string | null; counter: unknown; readyState?: string; lang?: string; market?: string; noShell?: boolean; noApi?: boolean; throwStorage?: boolean }
interface Result { sent: { url: string; type: string; body: string }[]; stored: string | null; setCalls: number }

async function runPage(p: Page): Promise<Result> {
  const sent: Result['sent'] = [];
  const store = new Map<string, string>();
  if (p.stored !== null) store.set('snapeyes.c', p.stored);
  let setCalls = 0;
  const loadFns: (() => void)[] = [];
  const health = Promise.resolve({ clone: () => ({ json: () => Promise.resolve({ counter: p.counter }) }) });
  const win: Record<string, unknown> = {};
  win.__lpShell = p.noShell ? undefined : { l: p.lang ?? 'lt', m: p.market ?? 'lt' };
  win.__lpApi = p.noApi ? undefined : { '/api/health': health, '/api/checkout': Promise.resolve({}) };
  const sandbox: Record<string, unknown> = {
    window: win,
    location: { search: p.search },
    document: { referrer: p.referrer, readyState: p.readyState ?? 'complete' },
    // a Storage reads and writes by property (the script says sessionStorage[K]); a blocked one throws
    sessionStorage: new Proxy({}, {
      get: (_t, k) => { if (p.throwStorage) throw new Error('blocked'); return store.get(String(k)); },
      set: (_t, k, v) => { if (p.throwStorage) throw new Error('blocked'); setCalls++; store.set(String(k), String(v)); return true; },
    }),
    navigator: { sendBeacon: (url: string, blob: { type: string; text: () => string }) => { sent.push({ url, type: blob.type, body: blob.text() }); return true; } },
    Blob: class { constructor(public parts: string[], public o: { type: string }) {} get type() { return this.o.type; } text() { return this.parts.join(''); } },
    URLSearchParams, JSON, Promise,
    addEventListener: (ev: string, fn: () => void) => { if (ev === 'load') loadFns.push(fn); },
  };
  vm.createContext(sandbox);
  vm.runInContext(counterScript, sandbox);
  await new Promise((r) => setTimeout(r, 20));
  if (p.readyState && p.readyState !== 'complete') {
    if (sent.length) throw new Error('sent before load');
    loadFns.forEach((f) => f());
  }
  return { sent, stored: store.get('snapeyes.c') ?? null, setCalls };
}

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const AD = '?lang=lt&m=lt&utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1';
  const WIRE = 'utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1';

  const r1 = await runPage({ search: AD, referrer: '', stored: null, counter: true });
  const b1 = JSON.parse(r1.sent[0]?.body ?? '{}');
  check('with counter true the head script sends ONE beacon: a POST of JSON to /api/checkout with the step landing, the shell\'s language and market and the campaign code',
    r1.sent.length === 1 && r1.sent[0].url === '/api/checkout' && r1.sent[0].type === 'application/json' && b1.hit === 'landing' && b1.lang === 'lt' && b1.market === 'lt' && b1.camp === WIRE
    && Object.keys(b1).sort().join() === 'camp,hit,lang,market', JSON.stringify(r1.sent));
  check('and keeps that code in sessionStorage snapeyes.c (written once)', r1.stored === WIRE && r1.setCalls === 1);
  for (const counter of [false, undefined, null, 'true', 1, {}]) {
    const r = await runPage({ search: AD, referrer: '', stored: null, counter });
    check(`counter ${JSON.stringify(counter) ?? 'missing'} from /api/health: nothing is sent and nothing is stored`, r.sent.length === 0 && r.stored === null);
  }
  const noShell = await runPage({ search: AD, referrer: '', stored: null, counter: true, noShell: true });
  const noApi = await runPage({ search: AD, referrer: '', stored: null, counter: true, noApi: true });
  check('without the decision script\'s answer or the early ask the script does nothing (no error, nothing sent)', noShell.sent.length === 0 && noApi.sent.length === 0);
  const late = await runPage({ search: AD, referrer: '', stored: null, counter: true, readyState: 'loading' });
  check('while the page is still loading the beacon waits for the load event, then goes', late.sent.length === 1);
  const blocked = await runPage({ search: AD, referrer: '', stored: null, counter: true, throwStorage: true });
  check('a browser that blocks sessionStorage still counts the visit, with the code in the beacon', blocked.sent.length === 1 && JSON.parse(blocked.sent[0].body).camp === WIRE);

  const matrix: [string, string, string | null][] = [
    [AD, '', null], [AD + '&fbclid=IwAR0x&gclid=1', 'https://l.facebook.com/', null], ['?utm_source=ig&utm_medium=bio', '', null], ['?utm_source=ig&utm_medium=story', '', 'utm_source=fb&utm_medium=paid'], ['?lang=de', 'https://snapeyes.com/', 'utm_source=fb&utm_medium=paid'],
    ['', 'https://l.facebook.com/l.php?u=x&h=secret', null], ['', 'https://www.instagram.com/', null], ['', 'https://vm.tiktok.com/x', null], ['', 'https://www.google.com/search?q=snapeyes', null], ['', 'https://news.example/post', null], ['', '', null],
    ['?utm_source=fb&utm_campaign=' + 'a'.repeat(80), '', null], ['?utm_source=%3Cscript%3E&utm_medium=a%7Cb', '', null], ['?utm_source=', 'https://www.google.com/', null], ['?utm_source=fb', '', 'utm_source=ig&utm_medium=bio'],
  ];
  const diffs: string[] = [];
  for (const [search, referrer, stored] of matrix) {
    const r = await runPage({ search, referrer, stored, counter: true });
    const got = JSON.parse(r.sent[0]?.body ?? '{}').camp;
    const want = capture(search, referrer, stored);
    if (got !== want || r.stored !== want) diffs.push(`${search} | ${referrer} | ${stored}: ${got} / ${r.stored} / ${want}`);
  }
  check(`the head script and capture() make the same code over ${matrix.length} combinations of address, referrer and stored code`, diffs.length === 0, diffs.join('; '));

  const gz = gzipSync(Buffer.from(counterScript), { level: 6 }).length;
  check(`the script is small: ${gz} bytes gzip on its own (about 300 inside the page, where gzip has seen the other scripts), ${counterScript.length} characters; the page's bundles do not grow`, gz < 460, String(gz));
  check('it reads no cookie, no localStorage, no fbclid and no part of the address but the utm_ parameters; it sends only to /api/checkout', !/cookie|localStorage|fbclid|gclid|location\.href|location\.pathname|hash/.test(counterScript) && (counterScript.match(/sendBeacon/g) ?? []).length === 1);
  check('it is part of the head, after the early ask whose answer it reads, and not part of the page\'s modules', prefetchScript.includes('__lpApi') && counterScript.includes('__lpApi') && /counter: scripts\.counterScript/.test(readFileSync(new URL('../../vite.config.ts', import.meta.url), 'utf8')));
  return out;
}
