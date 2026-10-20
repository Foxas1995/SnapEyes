// The campaign code, the page's half (2026-10-20): src/shared/counter.ts capture() turns the address and the referrer into the one code the tab keeps (sessionStorage "snapeyes.c") and sends with
// its beacons and its requests. Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { campaign, capture, withCamp } from '../../src/shared/counter';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const AD = '?lang=lt&m=lt&utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1';

  const WIRE = 'utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1';
  check('the five utm_ parameters of the ads plan are the code, as they stand in the link (the server turns them into short codes)', capture(AD, '', null) === WIRE, capture(AD, '', null));
  check('a fbclid, a gclid and every other parameter of the address are never read: not in the code', capture(AD + '&fbclid=IwAR0xyz&gclid=abc&email=a@b.c', '', null) === WIRE);
  check('a link that names only a source leaves the other parts empty', capture('?utm_source=ig&utm_medium=bio', '', null) === 'utm_source=ig&utm_medium=bio');
  check('a link with a new campaign replaces the code the tab already holds (the last advertisement clicked wins)', capture('?utm_source=ig&utm_medium=story', '', 'utm_source=fb&utm_medium=paid') === 'utm_source=ig&utm_medium=story');
  check('a link without a campaign keeps the code the tab holds, whatever the referrer says (the landing page links to /try and /try to /order)', capture('?lang=de', 'https://snapeyes.com/', 'utm_source=fb&utm_medium=paid') === 'utm_source=fb&utm_medium=paid');
  check('no code anywhere: the kind of page the visitor came from (facebook, instagram, tiktok, google), else other, and direct for none',
    capture('', 'https://l.facebook.com/l.php?u=x', null) === 'ref=facebook' && capture('', 'https://www.instagram.com/', null) === 'ref=instagram' && capture('', 'https://vm.tiktok.com/x', null) === 'ref=tiktok'
    && capture('', 'https://www.google.com/', null) === 'ref=google' && capture('', 'https://news.example/post', null) === 'ref=other' && capture('', '', null) === 'ref=direct');
  check('a value is cut at 60 characters, and a text that is no code travels as it is (the server drops what is no code)',
    capture('?utm_source=fb&utm_campaign=' + 'a'.repeat(80), '', null) === 'utm_source=fb&utm_campaign=' + 'a'.repeat(60) && capture('?utm_source=%3Cscript%3E', '', null) === 'utm_source=%3Cscript%3E');
  check('the referrer is looked at for its class only: the code never holds a path or a query', capture('', 'https://l.facebook.com/l.php?u=https%3A%2F%2Fsnapeyes.com&h=secret', null) === 'ref=facebook');

  // the tab's code: sessionStorage "snapeyes.c", worked out once
  const store = new Map<string, string>();
  const g = globalThis as unknown as Record<string, unknown>;
  const had = { location: g.location, document: g.document, sessionStorage: g.sessionStorage };
  g.location = { search: AD };
  g.document = { referrer: '' };
  g.sessionStorage = { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => { store.set(k, v); } };
  try {
    const first = campaign();
    check('the tab\'s code is worked out from the address and kept in sessionStorage under snapeyes.c, nowhere else', first === WIRE && store.get('snapeyes.c') === first && store.size === 1, JSON.stringify([...store]));
    g.location = { search: '?other=1' };
    check('and is the same afterwards, however the address changes (worked out once per page)', campaign() === first);
    check('withCamp adds it to a request body and changes nothing else', JSON.stringify(withCamp({ a: 1, lang: 'lt' })) === '{"a":1,"lang":"lt","camp":"' + WIRE + '"}', JSON.stringify(withCamp({ a: 1, lang: 'lt' })));
  } finally {
    g.location = had.location; g.document = had.document; g.sessionStorage = had.sessionStorage;
  }

  // where the code travels
  const tryApp = read('src/try/TryApp.tsx');
  const api = read('src/order/api.ts');
  const compose = read('src/try/composeApi.ts');
  check('the analysis, the reflection removal and the restoration of /try carry the code and the market (TryApp post)', /JSON\.stringify\(withCamp\(\{ lang: T\.lang, market: currentMarket\(\), \.\.\.body \}\)\)/.test(tryApp));
  check('a request to /api/checkout or /api/compose carries it (callApi), a request to any other endpoint does not (the order drafts, the status, the withdrawal)',
    /\[\/\]api\[\/\]\(checkout\|compose\)/.test(api) && /withCamp\(opts\.body/.test(api));
  check('the manual route click of the retake card carries it', /withCamp\(\{ action: 'help'/.test(compose));
  const mod = read('src/shared/counter.ts').replace(/[/][*][\s\S]*?[*][/]/g, '').replace(/[/][/].*$/gm, '');
  check('the module reads only the utm_ parameters and the referrer, writes only snapeyes.c, and has no cookie', !/cookie|localStorage|indexedDB/.test(mod) && (mod.match(/sessionStorage\.setItem/g) ?? []).length === 1 && !/fbclid|gclid/.test(mod));
  return out;
}
