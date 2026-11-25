// The Meta pixel, the pages' half (the owner's decision of 2026-11-25): src/shared/metaPixel.ts and the landing's inline head script (src/landing/shell/scripts.ts
// pixelScript). An event carries its name, a category, a value and a currency and the event id of a payment, nothing else (no photo, iris, colour, style or image);
// the order and gift pages never load Meta's script and name their path alone; nothing at all off snapeyes.com or without a dataset id; the event id of a payment
// is the server's (api/_lib/meta.py event_id). Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import vm from 'node:vm';
import {
  CATEGORIES, EVENTS_URL, FBC_KEY, PIXEL_HOSTS, SCRIPT_URL, livePayment, metaIds, params, pixelOn, purchaseId, resetPixelForTests, startPixel, track, voucherPurchaseId,
} from '../../src/shared/metaPixel';
import { pixelScript } from '../../src/landing/shell/scripts';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');
const tick = () => new Promise<void>((r) => setTimeout(r, 15));
const ID = '1804549607500630';

interface Env { fetched: string[]; scripts: string[]; store: Map<string, string>; loads: (() => void)[] }

function page(href: string, cookie = ''): Env {
  const u = new URL(href);
  const env: Env = { fetched: [], scripts: [], store: new Map(), loads: [] };
  const g = globalThis as unknown as Record<string, unknown>;
  g.window = globalThis;
  g.location = { href, hostname: u.hostname, search: u.search, pathname: u.pathname, origin: u.origin };
  g.document = {
    cookie, readyState: 'loading',
    createElement: () => ({ async: false, src: '' }),
    head: { appendChild: (s: { src: string }) => { env.scripts.push(s.src); } },
  };
  g.sessionStorage = { getItem: (k: string) => env.store.get(k) ?? null, setItem: (k: string, v: string) => { env.store.set(k, v); } };
  g.fetch = (url: string) => { env.fetched.push(String(url)); return Promise.resolve({}); };
  g.addEventListener = (ev: string, fn: () => void) => { if (ev === 'load') env.loads.push(fn); };
  g.requestIdleCallback = (fn: () => void) => { setTimeout(fn, 0); return 1; };
  delete g.fbq; delete g._fbq;
  return env;
}
const loaded = async (env: Env) => { (globalThis as unknown as { document: { readyState: string } }).document.readyState = 'complete'; env.loads.splice(0).forEach((f) => f()); await tick(); };
const cd = (url: string) => Object.fromEntries([...new URL(url).searchParams].filter(([k]) => k.startsWith('cd[')));

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const g = globalThis as unknown as Record<string, unknown>;
  const keep = ['window', 'location', 'document', 'sessionStorage', 'fetch', 'addEventListener', 'requestIdleCallback'].map((k) => [k, Object.getOwnPropertyDescriptor(g, k)] as const);
  try {
    // ---- what an event may say
    const p = params({ category: 'artwork', minor: 4999, currency: 'eur', style: 'clean', image: 'data:image/jpeg;base64,xx', colour: 'blue', names: 'Anna' } as never);
    check('an event\'s parameters are content_category, value (cents / 100) and currency, nothing else: the style, the colour, the names and an image are dropped',
      JSON.stringify(p) === '{"content_category":"artwork","value":49.99,"currency":"EUR"}', JSON.stringify(p));
    check('the categories are artwork, voucher and print; another is dropped, a negative value too', CATEGORIES.join() === 'artwork,voucher,print'
      && JSON.stringify(params({ category: 'eye' as never, minor: -5, currency: 'euro' })) === '{}');
    check('the event id of a payment is purchase_<session>, the server\'s (api/_lib/meta.py event_id)', purchaseId('cs_live_abc123') === 'purchase_cs_live_abc123');
    const vid = await voucherPurchaseId('cs_live_abc123');
    check('a voucher\'s event id is purchase_ and 32 hex of SHA-256 of the session (its session shows the code, so the raw id never goes to Meta)',
      vid === 'purchase_' + createHash('sha256').update('cs_live_abc123').digest('hex').slice(0, 32) && !vid.includes('abc123'), String(vid));
    check('only a live payment is reported', livePayment('cs_live_x') && !livePayment('cs_test_x') && !livePayment(null));

    // ---- off: no id, or not the site
    let env = page('https://snapeyes.com/try?fbclid=AbCdEfGh1234');
    resetPixelForTests('');
    startPixel('script'); track('Lead', { category: 'artwork' });
    await loaded(env);
    check('no dataset id: nothing loads, nothing is sent, nothing is kept, metaIds is empty', !pixelOn() && env.fetched.length === 0 && env.scripts.length === 0 && env.store.size === 0
      && JSON.stringify(metaIds()) === '{}');
    for (const host of ['localhost', '127.0.0.1', 'snapeyes-git-pixel.vercel.app', 'evilsnapeyes.com']) {
      env = page(`https://${host}/try`);
      resetPixelForTests(ID);
      startPixel('script'); track('ViewContent', { category: 'artwork' });
      await loaded(env);
      check(`off snapeyes.com (${host}) nothing reaches Meta: a Preview, a local server and the checks report nothing`, env.fetched.length === 0 && env.scripts.length === 0);
    }

    // ---- the script mode (/try, the legal pages)
    env = page('https://snapeyes.com/try?lang=lt&utm_source=fb&fbclid=AbCdEfGh1234');
    resetPixelForTests(ID);
    startPixel('script');
    track('ViewContent', { category: 'artwork' });
    check('before the page has loaded nothing is loaded or sent (the pixel never delays the page)', env.scripts.length === 0 && env.fetched.length === 0);
    await loaded(env);
    const q = ((g.fbq as { queue?: unknown[][] })?.queue ?? []).map((a) => JSON.stringify(a));
    check('after the load: Meta\'s script from connect.facebook.net, automatic configuration off before init, PageView, then what waited (ViewContent with its category)',
      env.scripts.length === 1 && env.scripts[0] === SCRIPT_URL && SCRIPT_URL === 'https://connect.facebook.net/en_US/fbevents.js'
      && q[0] === `["set","autoConfig",false,"${ID}"]` && q[1] === `["init","${ID}"]` && q[2] === '["track","PageView"]' && q[3] === '["track","ViewContent",{"content_category":"artwork"}]', q.join(' '));
    check('a click id in the address and no _fbc cookie: the tab keeps fb.1.<time>.<click id> in sessionStorage snapeyes.fbc', /^fb\.1\.\d{13}\.AbCdEfGh1234$/.test(env.store.get(FBC_KEY) ?? ''), env.store.get(FBC_KEY));
    track('Lead', { category: 'artwork' });
    check('Lead after the start goes straight to fbq', JSON.stringify(((g.fbq as { queue: unknown[][] }).queue).at(-1)) === '["track","Lead",{"content_category":"artwork"}]');
    (g.document as { cookie: string }).cookie = '_fbp=fb.1.1764000000000.123456789; other=1';
    track('InitiateCheckout', { category: 'artwork' }, undefined, true);
    const ic = env.fetched.at(-1) ?? '';
    const icu = new URL(ic);
    check('InitiateCheckout as the page leaves for Stripe: one request to www.facebook.com/tr (it outlives the page) with the page\'s path only, the category, _fbp and the kept click id',
      ic.startsWith(EVENTS_URL + '?') && icu.searchParams.get('ev') === 'InitiateCheckout' && icu.searchParams.get('dl') === 'https://snapeyes.com/try'
      && JSON.stringify(cd(ic)) === '{"cd[content_category]":"artwork"}' && icu.searchParams.get('fbp') === 'fb.1.1764000000000.123456789'
      && /^fb\.1\.\d{13}\.AbCdEfGh1234$/.test(icu.searchParams.get('fbc') ?? '') && icu.searchParams.get('id') === ID, ic);
    check('metaIds: the _fbp cookie and, without an _fbc cookie, the click id the tab kept', metaIds().fbp === 'fb.1.1764000000000.123456789' && /AbCdEfGh1234$/.test(metaIds().fbc ?? ''));
    (g.document as { cookie: string }).cookie = '_fbp=junk; _fbc=fb.1.1764000000001.ZyXwVu987654';
    check('metaIds: a malformed _fbp is not sent; an _fbc cookie wins over the kept one', JSON.stringify(metaIds()) === '{"fbc":"fb.1.1764000000001.ZyXwVu987654"}', JSON.stringify(metaIds()));

    // ---- the image mode (/order, /gift): no script, the path alone
    env = page('https://snapeyes.com/order?o=ab12-cd34&k=0123456789abcdef0123456789abcdef&s=cs_live_abc123&lang=lt');
    resetPixelForTests(ID);
    startPixel('image');
    track('Purchase', { category: 'artwork', minor: 4999, currency: 'eur' }, purchaseId('cs_live_abc123'));
    await loaded(env);
    const [pv, pu] = env.fetched;
    check('the order page loads no script: PageView and the Purchase that waited are single requests to www.facebook.com/tr', env.scripts.length === 0 && env.fetched.length === 2
      && new URL(pv).searchParams.get('ev') === 'PageView' && new URL(pu).searchParams.get('ev') === 'Purchase', env.fetched.join(' '));
    check('... that name the page\'s path and nothing of its address: not the order, not its key, not the payment\'s session (but in the event id)',
      env.fetched.every((u) => new URL(u).searchParams.get('dl') === 'https://snapeyes.com/order' && !u.includes('0123456789abcdef0123456789abcdef') && !u.includes('ab12-cd34')),
      env.fetched.join(' '));
    check('the Purchase carries the event id the server sends, the value, the currency and the category, nothing else',
      new URL(pu).searchParams.get('eid') === 'purchase_cs_live_abc123' && JSON.stringify(cd(pu)) === '{"cd[content_category]":"artwork","cd[value]":"49.99","cd[currency]":"EUR"}', pu);

    // ---- the landing's head script
    const src = pixelScript(ID);
    check('the landing\'s head script: none without a dataset id or with a malformed one', pixelScript('') === '' && pixelScript('12a') === '');
    check('it checks the same hosts as the module, carries the id, switches automatic configuration off and reports PageView only',
      src.includes(`/^(www\\.)?snapeyes\\.com$/`) && PIXEL_HOSTS.source === '^(www\\.)?snapeyes\\.com$' && src.includes(`I='${ID}'`)
      && src.includes("n('set','autoConfig',false,I);n('init',I);n('track','PageView')") && (src.match(/n\('track'/g) ?? []).length === 1
      && !/sendBeacon|fetch\(|localStorage/.test(src), src);
    for (const [host, want] of [['snapeyes.com', true], ['127.0.0.1', false]] as const) {
      const loads: (() => void)[] = [];
      const added: string[] = [];
      const store = new Map<string, string>();
      const sb: Record<string, unknown> = {
        location: { hostname: host, search: '?fbclid=AbCdEfGh1234' }, Date,
        URLSearchParams, setTimeout: () => 0,
        sessionStorage: { setItem: (k: string, v: string) => store.set(k, v) },
        addEventListener: (_: string, f: () => void) => loads.push(f),
      };
      sb.document = { readyState: 'loading', cookie: '', createElement: () => ({}), head: { appendChild: (s: { src: string }) => added.push(s.src) } };
      sb.requestIdleCallback = (f: () => void) => f();
      sb.window = sb;
      vm.createContext(sb);
      vm.runInContext(src, sb);
      check(`the head script on ${host}: nothing before the load`, added.length === 0);
      loads.forEach((f) => f());
      const qq = ((sb.fbq as { queue?: unknown[] } | undefined)?.queue ?? []).map((a) => JSON.stringify(Array.from(a as ArrayLike<unknown>)));
      check(`the head script on ${host}: ${want ? 'after the load Meta\'s script, autoConfig off, init and PageView, and the click id kept for the checkout' : 'nothing at all'}`,
        want ? added[0] === SCRIPT_URL && qq.join() === `["set","autoConfig",false,"${ID}"],["init","${ID}"],["track","PageView"]` && /AbCdEfGh1234$/.test(store.get('snapeyes.fbc') ?? '')
          : added.length === 0 && qq.length === 0 && store.size === 0, qq.join(' '));
    }
  } finally {
    for (const [k, d] of keep) { if (d) Object.defineProperty(g, k, d); else delete g[k]; }
    delete g.fbq; delete g._fbq;
    resetPixelForTests('');
  }

  // ---- where the pages call it, and the one place of the id
  const tryApp = read('src/try/TryApp.tsx'), order = read('src/order/OrderApp.tsx'), gift = read('src/gift/GiftApp.tsx'), offer = read('src/order/PrintOffer.tsx');
  check('/try: ViewContent when it opens, Lead once at the first free preview of a photo (not the sample), InitiateCheckout as it leaves for Stripe',
    /track\('ViewContent', \{ category: 'artwork' \}\)/.test(tryApp) && /if \(!sample && !leadSent\) \{ leadSent = true; track\('Lead'/.test(tryApp)
    && /track\('InitiateCheckout', \{ category: 'artwork' \}, undefined, true\);[^\n]*\n\s*window\.location\.assign\(out\.url\)/.test(tryApp));
  check('/order: the Purchase of a live payment (s) with the server\'s event id, the order\'s amount and currency; the print\'s with its own; InitiateCheckout of a print',
    /livePayment\(LINK\.s\)/.test(order) && /track\('Purchase', \{ category: 'artwork', minor: paidAmount, currency: paidCurrency \}, purchaseId\(LINK\.s\)\)/.test(order)
    && /track\('Purchase', \{ category: 'print'[^}]*\}, purchaseId\(PRINT_RETURN\.ps\)\)/.test(order) && /track\('InitiateCheckout', \{ category: 'print' \}, undefined, true\)/.test(offer));
  check('/gift: InitiateCheckout, and the Purchase with the hashed event id', /track\('InitiateCheckout', \{ category: 'voucher' \}, undefined, true\)/.test(gift)
    && /voucherPurchaseId\(sid\)\.then/.test(gift) && /livePayment\(sid\)/.test(gift));
  check('Meta\'s script on /try and the legal pages; the order and gift pages send requests only (their address holds a key or a payment) and keep their no-referrer',
    /startPixel\('script'\)/.test(read('src/try/main.tsx')) && /startPixel\('script'\)/.test(read('src/legal/main.tsx')) && /startPixel\('image'\)/.test(read('src/order/main.tsx'))
    && /startPixel\('image'\)/.test(read('src/gift/main.tsx')) && /<meta name="referrer" content="no-referrer" \/>/.test(read('order.html')) && /<meta name="referrer" content="no-referrer" \/>/.test(read('gift.html')));
  check('the admin panel and the landing\'s bundle do not load the module (the landing has its head script)', !/metaPixel/.test(read('src/admin/AdminApp.tsx') + read('src/admin/main.tsx') + read('src/main.tsx')));
  check('the checkouts send the two cookie values (src/order/api.ts: only to /api/checkout)', /\[\/\]api\[\/\]checkout\(\[\?\]\|\$\)\/\.test\(path\) \? metaIds\(\)/.test(read('src/order/api.ts')));
  const py = /^PIXEL_ID = "(\d+)"/m.exec(read('api/_lib/meta.py'))?.[1];
  check('the dataset id lives in ONE place, api/_lib/meta.py PIXEL_ID; vite.config.ts reads it there (META_PIXEL_ID overrides it) for the pages and the head script',
    py === ID && /readFileSync\('\.\/api\/_lib\/meta\.py'/.test(read('vite.config.ts')) && /process\.env\.META_PIXEL_ID/.test(read('vite.config.ts'))
    && !new RegExp(ID).test(read('src/shared/metaPixel.ts') + read('src/landing/shell/scripts.ts') + read('vite.config.ts')));
  check('no token in the pages: META_CAPI_TOKEN is named by no file of src/', !/META_CAPI_TOKEN/.test(read('src/shared/metaPixel.ts') + read('src/order/api.ts') + read('vite.config.ts')));
  return out;
}
