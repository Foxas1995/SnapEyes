// The site's own code (through Vite's module runner, as the build loads it) for the fixer's checks: ?m= spelling,
// the country offer (hintMarket, declineHint), a paused Australian market (legal links and pages keep m=au, prices and
// checkout do not), adoptMarket, the withdrawal answer's market, and the corrected Australian texts.
// Prints JSON for test_fixer.py. Run with the repo as the working directory: node <this file> <this folder>
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const req = createRequire(join(process.cwd(), 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const opt = { configFile: false, logLevel: 'silent' };
const ENTRY = pathToFileURL(join(process.argv[2], 'fixer_entry.ts')).pathname.replace(/^\/([A-Za-z]:)/, '$1');

const store = new Map();
function fakeWindow(search, stored) {
  store.clear();
  if (stored !== undefined && stored !== null) store.set('snapeyes.market', stored);
  globalThis.window = {
    location: { search, href: `https://snapeyes.com/${search}` },
    localStorage: { getItem: (k) => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: (k) => store.delete(k) },
    history: { replaceState() {} },
  };
}
/** A build in which the owner has paused these markets ("selectable": 0 in api/_lib/markets.py) BEFORE the page loads:
 *  a Vite plugin that rewrites the markets file the site reads as text. Setting selectable to 0 after the page has loaded
 *  (as the older scenarios below do) is too late for what the page decides at load (its market, detected once). */
function pausePlugin(paused) {
  return {
    name: 'pause-markets',
    transform(code, id) {
      if (!/api\/_lib\/markets\.py\?raw$/.test(id.split('\\').join('/'))) return null;
      let src = JSON.parse(code.replace(/^export default /, '').replace(/;\s*$/, ''));
      for (const m of paused) {
        const re = new RegExp(`("${m}": \\{[\\s\\S]*?"selectable": )1`);
        if (!re.test(src)) throw new Error(`market ${m}: no "selectable": 1 to pause in api/_lib/markets.py`);
        src = src.replace(re, '$10');
      }
      return { code: `export default ${JSON.stringify(src)}`, map: null };
    },
  };
}
/** A fresh page: a new module graph (the page's market is detected once per page load). paused: markets the owner has
 *  paused in this build (see pausePlugin). */
async function page(search, stored, paused = []) {
  fakeWindow(search, stored);
  const { module } = await runnerImport(ENTRY, paused.length ? { ...opt, plugins: [pausePlugin(paused)] } : opt);
  return module;
}

const out = { detect: {}, link: {}, hint: {}, paused: {}, adopt: {}, withdraw: {}, texts: {} };

// ?m= as a link may spell it
for (const [name, search] of [['upper', '?m=AU'], ['padded', '?m=%20au%20'], ['mixed_hu', '?m=Hu'], ['upper_lt', '?lang=de&m=LT']]) {
  const X = await page(search, null);
  out.detect[name] = { market: X.M.detectMarket(), stored: store.get('snapeyes.market') ?? null };
}
// 30efee7: Hungary (hu) is selectable now, so ?m=Hu is taken like ?m=AU (above). What stays ignored is a market the owner
// has PAUSED, however its link is spelled: hu paused before the page loads
{
  const X = await page('?m=Hu', null, ['hu']);
  out.detect.mixed_hu_paused = { market: X.M.detectMarket(), stored: store.get('snapeyes.market') ?? null };
}
// linkMarket: any market of the file, selectable or not
for (const [name, search] of [['hu', '?m=HU'], ['au', '?m=au'], ['junk', '?m=zz'], ['none', '']]) {
  const X = await page(search, null);
  out.link[name] = X.M.linkMarket();
}
// the country offer
{
  let X = await page('', null);
  out.hint.fresh_au = X.M.hintMarket('au', 'eu');
  out.hint.fresh_hu = X.M.hintMarket('hu', 'eu');        // 30efee7: Hungary is selectable, so a Hungarian visitor is offered forints
  out.hint.same_currency_lt = X.M.hintMarket('lt', 'eu');
  out.hint.already_au = X.M.hintMarket('au', 'au');
  out.hint.junk = [X.M.hintMarket('zz', 'eu'), X.M.hintMarket(null, 'eu'), X.M.hintMarket(7, 'eu'), X.M.hintMarket('AU', 'eu')];
  X.M.declineHint();
  out.hint.declined_store = store.get('snapeyes.market') ?? null;
  out.hint.after_decline = X.M.hintMarket('au', 'eu');
  out.hint.after_decline_market = X.M.detectMarket();
  X = await page('?m=eu', null);
  out.hint.link_named_eu = X.M.hintMarket('au', 'eu');
  X = await page('', 'au');
  out.hint.stored_au_page = X.M.currentMarket();
  out.hint.stored_au = X.M.hintMarket('au', X.M.currentMarket());
  X = await page('', null);
  X.M.setMarket('au');
  out.hint.after_accept = { market: X.M.currentMarket(), stored: store.get('snapeyes.market') ?? null, again: X.M.hintMarket('au', X.M.currentMarket()) };
  X = await page('', null);
  X.M.setMarket('hu');
  out.hint.after_accept_hu = { market: X.M.currentMarket(), stored: store.get('snapeyes.market') ?? null, again: X.M.hintMarket('hu', X.M.currentMarket()) };
  // a market the owner has paused is never offered (what the old not_selectable_hu pinned while hu was not sellable)
  X = await page('', null, ['hu']);
  out.hint.not_selectable_hu = X.M.hintMarket('hu', 'eu');
  X = await page('', null, ['au']);
  out.hint.not_selectable_au = X.M.hintMarket('au', 'eu');
}
// the owner paused Australia ("selectable": 0): prices and checkout ignore it, the legal links and pages keep it
{
  let X = await page('?m=au&lang=en', null);
  X.M.MARKETS.au.selectable = 0;
  out.paused.detect = X.M.detectMarket();
  out.paused.tryLink = X.M.withMarket('/try?lang=en', 'au');
  out.paused.legalAu = X.L.legalHref('terms', 'en', 'australia', 'au');
  out.paused.legalEu = X.L.legalHref('terms', 'en', 'australia', 'eu');
  X.L.adoptLinkedEdition();
  out.paused.adopted = X.M.currentMarket();
  out.paused.edition = X.L.legalEdition();
  out.paused.legalHere = X.L.legalHref('privacy', 'de');
  out.paused.withdrawHere = X.L.withdrawFunctionHref('en');
  out.paused.homeHere = X.M.withMarket('/?lang=en');
  X = await page('?m=hu', null);
  X.L.adoptLinkedEdition();
  // 30efee7: hu has its own edition of the legal texts and is selectable (the page takes its market and its edition)
  out.paused.huPage = { market: X.M.currentMarket(), edition: X.L.legalEdition(), legal: X.L.legalHref('terms', 'en') };
  X = await page('', 'au');
  X.M.MARKETS.au.selectable = 0;
  out.paused.storedOnly = { market: X.M.detectMarket() };
  // paused BEFORE the page loads (the page decides its market at load): a market with its own edition keeps its legal
  // links and its legal page (au, and since 30efee7 hu); a paused market WITHOUT an edition of its own (lt: the EU texts)
  // is not adopted and its links stay plain (what the old huPage pinned while hu had no edition)
  for (const [name, m] of [['au', 'au'], ['hu', 'hu'], ['lt', 'lt']]) {
    X = await page(`?m=${m}&lang=en`, null, [m]);
    const r = { detect: X.M.detectMarket(), stored: store.get('snapeyes.market') ?? null, tryLink: X.M.withMarket('/try?lang=en', m) };
    X.L.adoptLinkedEdition();
    r.adopted = X.M.currentMarket();
    r.edition = X.L.legalEdition();
    r.legal = X.L.legalHref('terms', 'en');
    r.withdraw = X.L.withdrawFunctionHref('en');
    r.home = X.M.withMarket('/?lang=en');
    out.paused['load_' + name] = r;
  }
}
// selectable Australia: the same links as before this fix
{
  const X = await page('?m=au', null);
  out.adopt.selectableLinks = { legal: X.L.legalHref('terms', 'en', 'australia'), withdraw: X.L.withdrawFunctionHref('de') };
  const Y = await page('', null);
  out.adopt.plainLinks = { legal: Y.L.legalHref('terms', 'en', 'australia'), withdraw: Y.L.withdrawFunctionHref('de') };
  Y.M.adoptMarket('zz');
  out.adopt.junk = Y.M.currentMarket();
  Y.M.adoptMarket('hu');
  out.adopt.hu = Y.M.currentMarket();
  Y.M.adoptMarket('au');
  out.adopt.au = { market: Y.M.currentMarket(), legal: Y.L.legalHref('terms', 'en') };
  Y.M.adoptMarket('eu');
  out.adopt.backToEu = { market: Y.M.currentMarket(), legal: Y.L.legalHref('terms', 'en') };
}
// the withdrawal answer names the order's market
{
  const X = await page('', null);
  out.withdraw.au = X.readWithdrawal({ state: 'lapsed', effective: false, market: 'au' })?.market ?? 'MISSING';
  out.withdraw.none = X.readWithdrawal({ state: 'withdrawn', effective: true })?.market;
  out.withdraw.bad = X.readWithdrawal({ state: 'lapsed', market: 7 })?.market;
  // the corrected Australian texts and the landing offer's copy
  const T = X.EDITIONS.au.terms, P = X.EDITIONS.au.privacy;
  const sec = (doc, lang, id) => doc[lang].sections.find((s) => s.id === id);
  out.texts.australiaEn = sec(T, 'en', 'australia').blocks;
  out.texts.australiaDe = sec(T, 'de', 'australia').blocks;
  out.texts.privacyEn = sec(P, 'en', 'australia').blocks;
  out.texts.privacyDe = sec(P, 'de', 'australia').blocks;
  out.texts.euTermsEn = X.EDITIONS.eu.terms.en;
  out.texts.hint = { en: X.COPY.en.marketHint, de: X.COPY.de.marketHint };
  out.texts.hintAll = { lt: X.COPY.lt.marketHint, hu: X.COPY.hu.marketHint };     // 30efee7: Lithuanian and Hungarian
}
delete globalThis.window;
console.log(JSON.stringify(out));
