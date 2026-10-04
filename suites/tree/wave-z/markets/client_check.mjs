// The site's own market code (src/shared/markets.ts, loaded through Vite's module runner exactly as the build loads
// it), asked for everything test_markets.py compares with the server: its reading of api/_lib/markets.py, the price of
// every market, eye count and style, how it writes money, the market links and the market detection. Prints JSON.
// Run with the repo as the working directory: node <this file>
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

// vite from the repo's own node_modules (this file lives outside the repo)
const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);

const { module: M } = await runnerImport('./src/shared/markets.ts', { configFile: false, logLevel: 'silent' });
// argv[2] (optional): a folder holding src/shared/markets.ts and api/_lib/markets.py of a table whose hu is paused ("selectable": 0),
// test_markets.py builds it. Commit 30efee7 made hu selectable, so what the links and the detection did with hu before is asked
// of this copy (the "paused" part of the output).
const PAUSED_ROOT = process.argv[2] ? process.argv[2] : null;
const MP = PAUSED_ROOT ? (await runnerImport('./src/shared/markets.ts', { configFile: false, logLevel: 'silent', root: PAUSED_ROOT })).module : null;
const { module: LEGAL } = await runnerImport('./src/shared/legal.ts', { configFile: false, logLevel: 'silent' });
const STYLES = ['studio_black', 'celestial_gold', 'deep_nebula', 'emerald_aurora', 'obsidian_smoke', 'supernova'];

const out = { defaultMarket: M.DEFAULT_MARKET, markets: M.MARKETS, selectable: M.SELECTABLE, table: {}, money: [], links: {}, detect: {} };
for (const m of Object.keys(M.MARKETS)) {
  out.table[m] = {};
  for (let n = 1; n <= 8; n++) {
    out.table[m][n] = {};
    for (const s of STYLES) out.table[m][n][s] = M.priceMinor(n, s, m);
  }
}
for (const [minor, cur] of [[1997, 'eur'], [3997, 'EUR'], [12997, 'eur'], [1500, 'eur'], [3900, 'aud'], [4900, 'AUD'], [25300, 'aud'],
  [3950, 'aud'], [125300, 'aud'], [699000, 'huf'], [1399000, 'HUF'], [4393000, 'huf'], [1997, 'xyz']]) {
  for (const lang of ['en', 'de']) out.money.push([minor, cur, lang, M.money(minor, cur, lang)]);
}
// a server list overrides the local one for its keys only
out.priceWithServerList = M.priceMinor(2, 'studio_black', 'au', { two_eyes: 7000 });
out.priceWithBadList = M.priceMinor(1, 'studio_black', 'au', { one_eye_studio_black: -5 });
out.serverPrices = {
  own: M.serverPrices({ markets: { au: { prices: { two_eyes: 7900 } } } }, 'au'),
  legacyDefault: M.serverPrices({ prices: { two_eyes: 3997 } }, M.DEFAULT_MARKET),
  legacyOther: M.serverPrices({ prices: { two_eyes: 3997 } }, 'au') ?? null,
};

// links (no browser: the default market, so the plain links; with a market named: m= before the #section)
out.links.legalPlain = LEGAL.legalHref('terms', 'en', 'prices');
out.links.withdrawPlain = LEGAL.withdrawFunctionHref('de');
out.links.address = LEGAL.withdrawFunctionAddress('de');
out.links.au = M.withMarket('/terms?lang=en#prices', 'au');
out.links.auNoQuery = M.withMarket('/try', 'au');
out.links.eu = M.withMarket('/terms?lang=en', 'eu');
out.links.hu = M.withMarket('/terms?lang=en', 'hu');
out.links.bogus = M.withMarket('/terms?lang=en', 'zz');

// detection: URL > localStorage > default; only selectable markets; a URL market is remembered
function fakeWindow(search, stored) {
  const store = new Map(stored ? [['snapeyes.market', stored]] : []);
  globalThis.window = {
    location: { search, href: `https://snapeyes.com/${search}` },
    localStorage: {
      getItem: (k) => (store.has(k) ? store.get(k) : null),
      setItem: (k, v) => { store.set(k, String(v)); },
      removeItem: (k) => { store.delete(k); },
    },
    history: { replaceState() {} },
  };
  return store;
}
function detectAll(Mod, cases) {
  const res = {};
  for (const [name, search, stored] of cases) {
    const store = fakeWindow(search, stored);
    const m = Mod.detectMarket();
    res[name] = { market: m, stored: store.get('snapeyes.market') ?? null };
  }
  delete globalThis.window;
  return res;
}
// hu is selectable since 30efee7 (before it: url_hu_ignored and stored_hu_ignored, now asked of the paused copy below)
out.detect = detectAll(M, [
  ['url_au', '?m=au', null], ['url_lt', '?lang=lt&m=lt', null], ['url_hu', '?m=hu', null],
  ['url_bogus', '?m=zz', null], ['stored_au', '', 'au'], ['stored_hu', '', 'hu'], ['url_beats_store', '?m=eu', 'au'],
  ['nothing', '', null],
]);

// the same with hu paused
if (MP) {
  out.paused = {
    selectable: MP.SELECTABLE,
    links: {
      au: MP.withMarket('/terms?lang=en#prices', 'au'), hu: MP.withMarket('/terms?lang=en', 'hu'),
      eu: MP.withMarket('/terms?lang=en', 'eu'), bogus: MP.withMarket('/terms?lang=en', 'zz'),
    },
    detect: detectAll(MP, [['url_au', '?m=au', null], ['url_hu_ignored', '?m=hu', null], ['stored_hu_ignored', '', 'hu']]),
  };
}

// the admin panel: amounts in their own currency, revenue summed per currency (never forints into euros)
const { module: AGG } = await runnerImport('./src/admin/agg.ts', { configFile: false, logLevel: 'silent' });
const { module: FMT } = await runnerImport('./src/admin/format.ts', { configFile: false, logLevel: 'silent' });
const now = Math.floor(Date.now() / 1000);
const row = (amount, currency, live) => ({ paid: true, paid_at: now - 60, amount, currency, live });
out.revenue = AGG.revenue([row(3997, 'EUR', true), row(1997, 'EUR', true), row(7900, 'AUD', true), row(1399000, 'HUF', true),
  row(3900, 'AUD', false), { paid: false, amount: 5000, currency: 'EUR' }, row(2497, undefined, true)], 7, now);
out.fmtMoney = [FMT.fmtMoney(3997, 'EUR'), FMT.fmtMoney(7900, 'aud'), FMT.fmtMoney(1399000, 'HUF'), FMT.fmtMoney(3997), FMT.fmtEur(1997), FMT.fmtMoney(null, 'eur')];
console.log(JSON.stringify(out));
