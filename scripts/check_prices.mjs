// The price check of the build: every price lives in ONE place, api/_lib/markets.py (the server charges from it and
// src/shared/markets.ts reads the same file for every page). This refuses the build when
//   1. that file's MARKETS literal is not plain JSON, or breaks a rule (currencies, Stripe's smallest units and minimum
//      charges, whole Australian dollars and whole forints, a selectable default market, ...);
//   2. the site's own reading of it (src/shared/markets.ts, loaded by vite.config.ts) differs from this one, or its
//      price rule (priceMinor) gives another price than api/_lib/pay.py's rule for any market, number of eyes and style (every id
//      of api/_lib/styles_registry.py, by its price class: scripts/check_styles.mjs also compares the rules);
//   3. any other file of the site or the server holds a price of its own: a price in Stripe's units in the files that
//      deal with prices, or a written price ("19.97", "A$39", "6 990 Ft") anywhere in src/ or api/ (comments aside);
//   5. every price experiment (api/_lib/experiments.py, checked by scripts/check_experiments.mjs): full ladders per
//      variant and market, control = the standard ladder, no variant that sells at a loss, the site's price rule
//      agrees with the server's for every variant, and no other file holds a variant's price;
//   6. the new landing (src/landing, every file but today's landing) prints only the visitor's own ladder: none of its files
//      reads the standard ladder or calls priceMinor without a ladder, and for every market, language and ladder (each
//      variant of each experiment, and a probe ladder that changes all four prices) every price text it can make is the
//      ladder's own price and changes when the ladder does (src/landing/priceText.ts, checkLandingPrices below);
//   4. a market is selectable in another currency than the default market's without its own edition of the legal
//      texts (src/shared/legal.ts EDITION_MARKETS = api/_lib/pay.py EDITION_MARKETS): the EU texts print euro prices
//      only. The two lists, and the languages each edition has (EDITION_LANGS in both files), must agree.
// vite.config.ts runs it before every build (with the site's reading, check 2, and the landing's price texts, check 6);
// `npm run check:prices` loads both as well and runs everything.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { checkExperiments, ladderRule, withVariantLadders } from './check_experiments.mjs';
import { STYLES_FILE, loadRegistry, priceClassOf } from './styles_source.mjs';

export const MARKETS_FILE = 'api/_lib/markets.py';
const CURRENCIES = ['eur', 'aud', 'huf'];
const PRICE_KEYS = ['one_eye_studio_black', 'one_eye_art', 'two_eyes', 'each_further_eye'];
const CLASSES = ['black', 'art'];   // the price classes (api/_lib/styles_registry.py price_class)
const MAX_EYES = 8;
// Stripe's minimum charge per currency, in its smallest unit (docs.stripe.com/currencies: EUR 0.50, AUD 0.50, HUF 175)
const STRIPE_MIN = { eur: 50, aud: 50, huf: 17500 };

// The files that deal with prices: none of them may hold a price in Stripe's units (1997, 3900, 699000, ...).
const PRICE_FILES = [
  'api/_lib/pay.py', 'api/checkout.py', 'api/order.py', 'api/stripe_webhook.py', 'api/_lib/ops.py', 'api/_lib/withdraw.py',
  'api/_lib/cleanup.py', 'scripts/order_admin.py',
  'src/landing/config.ts', 'src/landing/copy.ts', 'src/landing/Pricing.tsx', 'src/landing/Hero.tsx',
  'src/landing/StyleGallery.tsx', 'src/landing/Faq.tsx', 'src/landing/Footer.tsx',
  'src/try/BuyCard.tsx', 'src/try/multi.ts', 'src/try/checkout.ts', 'src/try/copy.ts',
  'src/order/api.ts', 'src/order/copy.ts', 'src/order/OrderApp.tsx', 'src/order/WithdrawPanel.tsx', 'src/order/withdraw.ts',
  'src/legal/facts.ts', 'src/legal/docs/terms.ts', 'src/legal/docs/terms.lt.ts', 'src/legal/docs/terms.hu.ts', 'src/legal/plain.ts',
  'src/landing/copy.lt.ts', 'src/landing/copy.hu.ts', 'src/try/copy.lt.ts', 'src/try/copy.hu.ts', 'src/order/copy.lt.ts',
  'src/order/copy.hu.ts', 'api/_lib/pay_lt.py', 'api/_lib/pay_hu.py', 'api/_lib/withdraw_lt.py', 'api/_lib/withdraw_hu.py',
  'src/admin/format.ts', 'src/admin/agg.ts', 'src/admin/Summary.tsx', 'src/admin/Orders.tsx', 'src/admin/OrderDetail.tsx',
  'src/admin/Tests.tsx', 'api/_lib/abtest.py', 'src/shared/pricing.ts', 'src/shared/usePrices.ts', 'src/try/priceNote.ts',
  'src/shared/markets.ts', 'src/shared/legal.ts',
  // the files of the new landing that print prices (BUILD_PLAN section 2; a file that does not exist yet is skipped) and its
  // copy (every file of src/landing/copy, see checkCopies). A number in these files that equals a price in Stripe's smallest
  // unit is taken for a price: image sizes come from the asset manifest, never typed here.
  'src/landing/priceText.ts', 'src/landing/prices.ts', 'src/landing/PriceTable.tsx', 'src/landing/HeroScene.tsx', 'src/landing/StyleTile.tsx',
  // the first screen's shell (BUILD_PLAN section 4 step 1: the hero's price line is made here; the build hands render.tsx its one price)
  'src/landing/shell/render.tsx', 'src/landing/HeroView.tsx',
];
const PRICE_DIRS = ['src/landing/copy'];
// Never scanned for written prices: the one place itself, the place of the price experiments' ladders
// (scripts/check_experiments.mjs checks those) and the image engine (another team's, no prices in it).
const SKIP = new Set([MARKETS_FILE, 'api/_lib/experiments.py', 'api/_lib/iris.py']);

/** DEFAULT_MARKET and MARKETS of api/_lib/markets.py's text (src/shared/markets.ts parseMarketsSource, the same rule). */
export function parseMarketsSource(src) {
  const d = /^DEFAULT_MARKET = "([a-z]{2,8})"\s*$/m.exec(src);
  const at = src.search(/^MARKETS = \{/m);
  if (!d || at < 0) throw new Error(`${MARKETS_FILE}: DEFAULT_MARKET or MARKETS not found`);
  return { defaultMarket: d[1], markets: JSON.parse(src.slice(at + 'MARKETS = '.length)) };
}

/** api/_lib/pay.py price_cents, restated: one eye by the price class of its style (the registry's price_class, "black" or "art"),
 *  two eyes, then the same amount per further eye. */
export function priceRule(markets, market, eyes, cls) {
  const p = markets[market].prices;
  if (eyes <= 1) return cls === 'black' ? p.one_eye_studio_black : p.one_eye_art;
  return p.two_eyes + (eyes - 2) * p.each_further_eye;
}

const isInt = (v) => typeof v === 'number' && Number.isInteger(v);

function checkRules(defaultMarket, markets, out) {
  if (!markets || typeof markets !== 'object' || Array.isArray(markets)) {
    out.push(`${MARKETS_FILE}: MARKETS is not an object`);
    return;
  }
  if (!markets[defaultMarket]) out.push(`${MARKETS_FILE}: DEFAULT_MARKET "${defaultMarket}" is not in MARKETS`);
  else if (markets[defaultMarket].selectable !== 1) out.push(`${MARKETS_FILE}: the default market "${defaultMarket}" must be selectable`);
  for (const [key, m] of Object.entries(markets)) {
    const at = `${MARKETS_FILE} market "${key}"`;
    if (!/^[a-z]{2,8}$/.test(key)) out.push(`${at}: the key must be 2 to 8 lower-case letters`);
    if (!m || typeof m !== 'object') { out.push(`${at}: not an object`); continue; }
    const want = ['countries', 'currency', 'lang', 'prices', 'selectable', 'stripe_locale'];
    const keys = Object.keys(m).sort();
    if (keys.join() !== want.join()) out.push(`${at}: its fields must be exactly ${want.join(', ')} (has ${keys.join(', ')})`);
    if (!CURRENCIES.includes(m.currency)) out.push(`${at}: currency must be one of ${CURRENCIES.join(', ')}`);
    if (m.selectable !== 0 && m.selectable !== 1) out.push(`${at}: selectable must be 1 or 0`);
    if (typeof m.lang !== 'string' || !/^[a-z]{2}$/.test(m.lang)) out.push(`${at}: lang must be a two-letter language`);
    if (!m.stripe_locale || typeof m.stripe_locale !== 'object' || Array.isArray(m.stripe_locale)
      || !Object.entries(m.stripe_locale).every(([l, v]) => /^[a-z]{2}$/.test(l) && typeof v === 'string' && /^[a-z]{2}(-[A-Z]{2})?$/.test(v))) {
      out.push(`${at}: stripe_locale must map page languages to Stripe locales ({"en": "en-GB"})`);
    }
    if (!Array.isArray(m.countries) || !m.countries.every((c) => typeof c === 'string' && /^[A-Z]{2}$/.test(c))) {
      out.push(`${at}: countries must be a list of two-letter country codes`);
    }
    const p = m.prices;
    if (!p || typeof p !== 'object' || Object.keys(p).sort().join() !== [...PRICE_KEYS].sort().join()) {
      out.push(`${at}: prices must have exactly ${PRICE_KEYS.join(', ')}`);
      continue;
    }
    for (const k of PRICE_KEYS) {
      const v = p[k];
      if (!isInt(v) || v <= 0) { out.push(`${at}: ${k} must be a positive whole number in Stripe's smallest unit`); continue; }
      if (CURRENCIES.includes(m.currency) && v < STRIPE_MIN[m.currency]) out.push(`${at}: ${k} ${v} is below Stripe's minimum charge`);
      if (m.currency === 'huf' && v % 100 !== 0) out.push(`${at}: ${k} ${v} is not whole forints (HUF goes to Stripe as the forint x 100)`);
      if (m.currency === 'aud' && v % 100 !== 0) out.push(`${at}: ${k} ${v} is not whole Australian dollars (owner decision: no cents)`);
    }
    if (isInt(p.two_eyes) && isInt(p.each_further_eye) && p.two_eyes + (MAX_EYES - 2) * p.each_further_eye > 99999999) {
      out.push(`${at}: ${MAX_EYES} eyes cost more than Stripe takes in one payment`);
    }
  }
}

// Which markets have their own edition of the legal texts: src/shared/legal.ts EDITION_MARKETS (the pages) and
// api/_lib/pay.py EDITION_MARKETS (the emails), two lists that must agree, and the languages each edition has
// (EDITION_LANGS, in both files). Every other market reads the EU edition, whose terms print the euro price list only.
const LEGAL_FILE = 'src/shared/legal.ts';
const PAY_FILE = 'api/_lib/pay.py';

function readOptional(root, rel) {
  try { return readFileSync(join(root, rel), 'utf8'); } catch { return null; }
}

/** EDITION_LANGS of src/shared/legal.ts as {edition: [lang, ...]} (or null when the table is not there). */
export function pageEditionLangs(legal) {
  const m = /export const EDITION_LANGS[^=]*=\s*\{([^}]*)\}/.exec(legal);
  if (!m) return null;
  const out = {};
  for (const x of m[1].matchAll(/\b([a-z]{2,8})\s*:\s*\[([^\]]*)\]/g)) out[x[1]] = [...x[2].matchAll(/'([a-z]{2})'/g)].map((y) => y[1]).sort();
  return out;
}

/** EDITION_LANGS of api/_lib/pay.py as {edition: [lang, ...]} (or null). */
export function serverEditionLangs(payPy) {
  const m = /^EDITION_LANGS = \{([^}]*)\}/m.exec(payPy);
  if (!m) return null;
  const out = {};
  for (const x of m[1].matchAll(/"([a-z]{2,8})"\s*:\s*\(([^)]*)\)/g)) out[x[1]] = [...x[2].matchAll(/"([a-z]{2})"/g)].map((y) => y[1]).sort();
  return out;
}

/** 4. A selectable market in another currency than the default market's must have its own edition of the legal texts
 *  (the EU terms and emails quote euro prices only, so an order in forints would get a contract with a euro price
 *  table). And the pages' and the server's lists agree: the markets with an edition and the languages of each. */
function checkEditions(root, defaultMarket, markets, out) {
  const legal = readOptional(root, LEGAL_FILE);
  const payPy = readOptional(root, PAY_FILE);
  let pages = null, server = null;
  if (legal !== null) {
    const m = /export const EDITION_MARKETS[^=]*=\s*\{([^}]*)\}/.exec(legal);
    if (!m) out.push(`${LEGAL_FILE}: EDITION_MARKETS not found (the price check reads it)`);
    else pages = [...m[1].matchAll(/[a-z]+\s*:\s*'([a-z]{2,8})'/g)].map((x) => x[1]).sort();
  }
  if (payPy !== null) {
    const m = /^EDITION_MARKETS = \(([^)]*)\)/m.exec(payPy);
    if (!m) out.push(`${PAY_FILE}: EDITION_MARKETS not found (the price check reads it)`);
    else server = [...m[1].matchAll(/"([a-z]{2,8})"/g)].map((x) => x[1]).sort();
  }
  if (pages && server && pages.join() !== server.join()) {
    out.push(`${LEGAL_FILE} EDITION_MARKETS (${pages.join(', ')}) and ${PAY_FILE} EDITION_MARKETS (${server.join(', ')}) must name the same markets`);
  }
  if (legal !== null && payPy !== null) {
    const a = pageEditionLangs(legal), b = serverEditionLangs(payPy);
    if (!a) out.push(`${LEGAL_FILE}: EDITION_LANGS not found (the price check reads it)`);
    else if (!b) out.push(`${PAY_FILE}: EDITION_LANGS not found (the price check reads it)`);
    else if (JSON.stringify(a, Object.keys(a).sort()) !== JSON.stringify(b, Object.keys(b).sort())) {
      out.push(`${LEGAL_FILE} EDITION_LANGS (${JSON.stringify(a)}) and ${PAY_FILE} EDITION_LANGS (${JSON.stringify(b)}) must list the same languages per edition`);
    }
  }
  // the server's Australian part (pay.py ACL_MARKETS: the Australian checkbox, note and invoice) is exactly the market the
  // pages give the "au" edition (legal.ts EDITION_MARKETS.au), and inside the server's EDITION_MARKETS
  if (payPy !== null) {
    const m = /^ACL_MARKETS = \(([^)]*)\)/m.exec(payPy);
    if (!m) out.push(`${PAY_FILE}: ACL_MARKETS not found (the price check reads it)`);
    else {
      const acl = [...m[1].matchAll(/"([a-z]{2,8})"/g)].map((x) => x[1]);
      const table = legal !== null ? /export const EDITION_MARKETS[^=]*=\s*\{([^}]*)\}/.exec(legal)?.[1] : undefined;
      const au = table !== undefined ? /\bau\s*:\s*'([a-z]{2,8})'/.exec(table)?.[1] : undefined;
      if (au !== undefined && acl.join() !== au) {
        out.push(`${PAY_FILE} ACL_MARKETS (${acl.join(', ')}) must be exactly the market of the Australian edition in ${LEGAL_FILE} EDITION_MARKETS (${au})`);
      }
      if (server && !acl.every((x) => server.includes(x))) {
        out.push(`${PAY_FILE} ACL_MARKETS (${acl.join(', ')}) must be inside its EDITION_MARKETS (${server.join(', ')})`);
      }
    }
  }
  const own = pages ?? server;
  if (!own) return;
  for (const m of own) if (!markets[m]) out.push(`${LEGAL_FILE}: the legal edition of market "${m}" names no market of ${MARKETS_FILE}`);
  const base = markets[defaultMarket]?.currency;
  for (const [key, m] of Object.entries(markets)) {
    if (m.selectable === 1 && m.currency !== base && !own.includes(key)) {
      out.push(`${MARKETS_FILE} market "${key}": selectable, but no edition of the legal texts prints its ${m.currency.toUpperCase()} prices `
        + `(the EU terms and emails list ${String(base).toUpperCase()} prices only): keep "selectable": 0 until its own texts exist `
        + `(${LEGAL_FILE} EDITION_MARKETS, ${PAY_FILE} EDITION_MARKETS)`);
    }
  }
}

function sameJson(a, b) {
  if (a === b) return true;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
  const ka = Object.keys(a).sort(), kb = Object.keys(b).sort();
  return ka.join() === kb.join() && ka.every((k) => sameJson(a[k], b[k]));
}

function checkClient(defaultMarket, markets, client, out, registry) {
  if (client.DEFAULT_MARKET !== defaultMarket) out.push(`src/shared/markets.ts reads DEFAULT_MARKET "${client.DEFAULT_MARKET}", not "${defaultMarket}"`);
  if (!sameJson(client.MARKETS, markets)) out.push('src/shared/markets.ts reads another MARKETS than api/_lib/markets.py holds');
  for (const market of Object.keys(markets)) {
    for (let eyes = 1; eyes <= MAX_EYES; eyes++) {
      for (const style of Object.keys(registry.styles)) {
        const want = priceRule(markets, market, eyes, priceClassOf(registry.styles, style));
        const got = client.priceMinor(eyes, style, market);
        if (got !== want) out.push(`src/shared/markets.ts priceMinor(${eyes}, ${style}, ${market}) = ${got}, api/_lib/pay.py charges ${want}`);
      }
    }
  }
}

function stripComments(text, py) {
  if (py) {
    return text
      .replace(/^[ \t]*[rRbBuU]?("""|''')[\s\S]*?\1/gm, '')        // docstrings (triple-quoted blocks starting a line)
      .replace(/(^|[ \t])#.*$/gm, '$1');
  }
  return text
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:'"`\\])\/\/.*$/gm, '$1');
}

function listFiles(root, dir, exts, acc = []) {
  let names = [];
  try { names = readdirSync(join(root, dir)); } catch { return acc; }
  for (const n of names) {
    if (n === 'node_modules' || n === '__pycache__' || n.startsWith('.')) continue;
    const rel = `${dir}/${n}`;
    const st = statSync(join(root, rel));
    if (st.isDirectory()) listFiles(root, rel, exts, acc);
    else if (exts.some((e) => n.endsWith(e))) acc.push(rel);
  }
  return acc;
}

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** Written forms of every price (the ways the pages and emails print them). */
function writtenPatterns(markets) {
  const out = new Map();
  for (const [key, m] of Object.entries(markets)) {
    for (let eyes = 1; eyes <= MAX_EYES; eyes++) {
      for (const cls of CLASSES) {
        const minor = priceRule(markets, key, eyes, cls);
        const units = Math.floor(minor / 100);
        const cents = String(minor % 100).padStart(2, '0');
        if (m.currency === 'huf') {
          const s = String(units);
          const g = s.length > 3 ? `${s.slice(0, -3)}[ \\u00a0.,]?${s.slice(-3)}` : s;
          out.set(`${units} Ft`, new RegExp(`(?<![\\d.,])${g}[ \\u00a0]?(Ft|HUF)\\b`));
        } else if (minor % 100 !== 0) {
          out.set(`${units}.${cents}`, new RegExp(`(?<![\\d.,])${units}[.,]${cents}(?![\\d])`));
        } else if (m.currency === 'aud') {
          out.set(`A$${units}`, new RegExp(`A\\$[ \\u00a0]?${units}(?![\\d])`));
        }
      }
    }
    for (const k of PRICE_KEYS) {
      const minor = m.prices[k];
      if (m.currency !== 'huf' && minor % 100 !== 0) {
        const units = Math.floor(minor / 100), cents = String(minor % 100).padStart(2, '0');
        out.set(`${units}.${cents}`, new RegExp(`(?<![\\d.,])${units}[.,]${cents}(?![\\d])`));
      }
    }
  }
  return out;
}

function checkCopies(root, markets, out) {
  const minors = new Set();
  // a variant's round thousands (1000, 2000 ...) are too common in code to mean a price: only its other amounts are looked for
  for (const m of Object.values(markets)) for (const k of PRICE_KEYS) if (!(m.variant && m.prices[k] % 1000 === 0)) minors.add(m.prices[k]);
  const minorRe = new RegExp(`(?<![\\w.$])(${[...minors].map(String).map(esc).join('|')})(?![\\w.])`);
  for (const rel of [...PRICE_FILES, ...PRICE_DIRS.flatMap((d) => listFiles(root, d, ['.ts', '.tsx', '.json']))]) {
    let text;
    try { text = readFileSync(join(root, rel), 'utf8'); } catch { continue; }
    const code = stripComments(text, rel.endsWith('.py'));
    code.split('\n').forEach((line, i) => {
      const hit = minorRe.exec(line);
      if (hit) out.push(`${rel}: holds the price ${hit[1]} of its own (line ~${i + 1}); take it from ${MARKETS_FILE} (src/shared/markets.ts, api/_lib/pay.py)`);
    });
  }
  const written = writtenPatterns(markets);
  const files = [...listFiles(root, 'src', ['.ts', '.tsx']), ...listFiles(root, 'api', ['.py']), ...listFiles(root, 'scripts', ['.py']), ...PRICE_DIRS.flatMap((d) => listFiles(root, d, ['.json']))];
  for (const rel of files) {
    if (SKIP.has(rel)) continue;
    const text = readFileSync(join(root, rel), 'utf8');
    const code = stripComments(text, rel.endsWith('.py'));
    for (const [label, re] of written) {
      const lines = code.split('\n');
      const i = lines.findIndex((l) => re.test(l));
      if (i >= 0) out.push(`${rel}: writes the price ${label} itself (line ~${i + 1}); print it from ${MARKETS_FILE} instead`);
    }
  }
}

// ------------------------------------------------------------------------------------------ the new landing's prices
// The new landing (BUILD_PLAN section 2) prints every price through src/landing/prices.ts (useLandingPrices), which makes
// its texts with src/landing/priceText.ts from the ladder of src/shared/usePrices.ts: the visitor's variant while a price
// experiment runs for them, else the standard one. Two checks keep that true.
//   a. Static: no file of the new landing reads the standard ladder itself (priceList, effectiveList, listFor, MARKETS,
//      PRICE_CENTS, DEFAULT_PRICES) or calls priceMinor without the ladder (its fourth argument): either would print the
//      standard price to a visitor in an experiment. Every file of src/landing except today's landing is a file of the new one.
//   b. Dynamic (the "client rule" of scripts/check_experiments.mjs, here for the page's texts): for every market, language and
//      ladder (every variant of every experiment of the market, and a probe ladder whose four prices all differ from the
//      standard ones) each text the page can print (from, black, art, price, price2, every number of eyes in both one-eye
//      styles) is exactly the ladder's own price by the server's rule in the site's money format, and changes when the ladder
//      changes it: with the probe ladder EVERY text differs from the standard one.

// the files of src/landing that are not the landing's own sections (the facts of the seller, the words other pages still use, the
// language and ordering state, the primitives the legal pages import): not governed by the rules above
export const OLD_LANDING_FILES = new Set([
  'config.ts', 'copy.hu.ts', 'copy.lt.ts', 'copy.ts', 'lang.tsx', 'ordering.ts', 'ui.tsx',
]);

// the standard ladder may be read by nothing in the new landing
const STANDARD_LADDER_READS = /\b(priceList|effectiveList|listFor|PRICE_CENTS|DEFAULT_PRICES|MARKETS)\b/;

/** The number of top-level arguments of each priceMinor( ... ) call of a source text (comments already stripped). */
function priceMinorArgCounts(code) {
  const counts = [];
  for (const m of code.matchAll(/\bpriceMinor\s*\(/g)) {
    let depth = 1, args = 1, empty = true;
    for (let i = m.index + m[0].length; i < code.length && depth > 0; i++) {
      const c = code[i];
      if (c === '(' || c === '[' || c === '{') { depth++; empty = false; }
      else if (c === ')' || c === ']' || c === '}') depth--;
      else if (c === ',' && depth === 1) args++;
      else if (!/\s/.test(c)) empty = false;
    }
    counts.push(empty ? 0 : args);
  }
  return counts;
}

function checkLandingSources(root, out) {
  const files = listFiles(root, 'src/landing', ['.ts', '.tsx']).filter((rel) => {
    const inside = rel.slice('src/landing/'.length);
    return inside.includes('/') || !OLD_LANDING_FILES.has(inside);
  });
  for (const rel of files) {
    const code = stripComments(readFileSync(join(root, rel), 'utf8'), false);
    const lines = code.split('\n');
    const i = lines.findIndex((l) => STANDARD_LADDER_READS.test(l));
    if (i >= 0) out.push(`${rel}: reads the standard price ladder itself (${STANDARD_LADDER_READS.exec(lines[i])[1]}, line ~${i + 1}); the new landing prints the visitor's ladder only, through src/landing/prices.ts (useLandingPrices)`);
    const bad = priceMinorArgCounts(code).some((n) => n < 4);
    if (bad) out.push(`${rel}: calls priceMinor without the ladder (its fourth argument): that prints the standard price to a visitor in a price experiment`);
  }
}

const LANDING_LANGS = ['en', 'de', 'lt', 'hu'];

/** Every text the page can print for a ladder, with the amount it must show (in Stripe's smallest unit). */
function landingTexts(p, L, styles) {
  const rows = [
    ['from', p.from, Math.min(L.one_eye_studio_black, L.one_eye_art)],
    ['black', p.black, L.one_eye_studio_black],
    ['art', p.art, L.one_eye_art],
    ['price (each further eye)', p.price, L.each_further_eye],
    ['price2 (two eyes)', p.price2, L.two_eyes],
  ];
  for (let n = 1; n <= MAX_EYES; n++) {
    // one eye by the price class of its style (the registry's price_class: "black" or "art"), more eyes cost the same in any style
    rows.push([`eyes(${n}, black)`, p.eyes(n, 'black'), ladderRule(L, n, 'black')]);
    rows.push([`eyes(${n}, art)`, p.eyes(n, 'art'), ladderRule(L, n, 'art')]);
  }
  // the price of n eyes in a style of the registry (the gallery's tiles and the hero's "from" line ask for it by style id): by the style's price class
  for (const id of Object.keys(styles ?? {})) {
    for (const n of [1, 2, 3, MAX_EYES]) rows.push([`of(${id}, ${n})`, p.of(id, n), ladderRule(L, n, priceClassOf(styles, id))]);
  }
  // the lowest one-eye price among some styles: both classes, one class, none (no text at all)
  const ids = Object.keys(styles ?? {});
  const black = ids.filter((id) => priceClassOf(styles, id) === 'black'), art = ids.filter((id) => priceClassOf(styles, id) === 'art');
  if (black.length && art.length) {
    rows.push(['fromOf(both classes)', p.fromOf([black[0], art[0]]), Math.min(L.one_eye_studio_black, L.one_eye_art)]);
    rows.push(['fromOf(black)', p.fromOf([black[0]]), L.one_eye_studio_black]);
    rows.push(['fromOf(art)', p.fromOf([art[0]]), L.one_eye_art]);
  }
  return rows;
}

/** The dynamic check above. landing: src/landing/priceText.ts as the build loaded it; client: src/shared/markets.ts. */
export function checkLandingPrices(markets, experiments, client, landing, out, styles) {
  const at = 'src/landing/priceText.ts';
  if (typeof landing?.landingPrices !== 'function') { out.push(`${at}: landingPrices not found (the price check reads it)`); return; }
  if (typeof client?.money !== 'function') { out.push('src/shared/markets.ts: money not found (the price check reads it)'); return; }
  let cases = 0;
  for (const [m, def] of Object.entries(markets)) {
    const standard = def.prices;
    // a ladder whose four prices all differ from the standard ones, and from each other's sums
    const probe = Object.fromEntries(PRICE_KEYS.map((k) => [k, standard[k] * 2 + 7]));
    const ladders = [['probe ladder', probe, true]];
    for (const [key, d] of Object.entries(experiments ?? {})) {
      for (const [name, v] of Object.entries(d?.variants ?? {})) {
        if (v?.prices?.[m] && typeof v.prices[m] === 'object') ladders.push([`experiment "${key}" variant "${name}"`, v.prices[m], false]);
      }
    }
    for (const lang of LANDING_LANGS) {
      let base;
      try { base = landingTexts(landing.landingPrices(standard, m, lang), standard, styles); } catch (e) { out.push(`${at}: landingPrices threw for market "${m}" in ${lang}: ${e instanceof Error ? e.message : String(e)}`); continue; }
      for (const [label, L, every] of ladders) {
        cases++;
        let got;
        try { got = landingTexts(landing.landingPrices(L, m, lang), L, styles); } catch (e) { out.push(`${at}: landingPrices threw for ${label}, market "${m}" in ${lang}: ${e instanceof Error ? e.message : String(e)}`); continue; }
        got.forEach(([what, text, minor], i) => {
          const want = client.money(minor, def.currency, lang);
          if (text !== want) out.push(`${at}: ${what} is "${text}" for ${label}, market "${m}" in ${lang}; the ladder's price is ${want}`);
          else if ((every || minor !== base[i][2]) && text === base[i][1]) out.push(`${at}: ${what} stays "${text}" under ${label}, market "${m}" in ${lang}, although the ladder changed it (a price that ignores the visitor's ladder)`);
        });
      }
    }
  }
  if (cases === 0) out.push(`${at}: no market to check`);
}

/** Every problem found, as sentences ([] when the prices are sound). client: src/shared/markets.ts as the build loaded
 *  it (vite.config.ts), for the agreement check; without it that check is left out. landing: src/landing/priceText.ts as
 *  the build loaded it, for the check of the new landing's price texts (also left out without it). */
export function checkPrices(root, client, landing) {
  const out = [];
  let parsed;
  try {
    parsed = parseMarketsSource(readFileSync(join(root, MARKETS_FILE), 'utf8'));
  } catch (e) {
    return [`${MARKETS_FILE}: the MARKETS literal cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`];
  }
  const { defaultMarket, markets } = parsed;
  checkRules(defaultMarket, markets, out);
  if (out.length) return out;
  checkEditions(root, defaultMarket, markets, out);
  let registry;
  try {
    registry = loadRegistry(root);
  } catch (e) {
    out.push(`${STYLES_FILE}: the STYLES literal cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`);
    return out;
  }
  if (client) checkClient(defaultMarket, markets, client, out, registry);
  // the price experiments' variant ladders (api/_lib/experiments.py): validated, and no other file may hold their prices
  const experiments = checkExperiments(root, markets, out, client);
  checkCopies(root, withVariantLadders(markets, experiments), out);
  // the new landing prints only the visitor's own ladder (source rules, then its price texts for every ladder)
  checkLandingSources(root, out);
  if (client && landing) {
    checkLandingPrices(markets, experiments, client, landing, out, registry.styles);
    if (landing.landingPrices(markets[defaultMarket].prices, defaultMarket, 'en').fromOf([]) !== null) out.push('src/landing/priceText.ts: fromOf([]) must be null (no style for sale: the line is not printed)');
  }
  return out;
}

// `node scripts/check_prices.mjs` (npm run check:prices): every check, exit code 1 on any problem. src/ is loaded through
// Vite's module runner, as check_texts.mjs and vite.config.ts do, for the checks that run the site's own code.
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  // src/ is loaded through Vite for the checks that run the site's own code (the client reading of the prices, the landing's price texts). A tree without Vite (a
  // throw-away copy of the files, made by a test) still gets every file check: only a MISSING vite is excused, with a note; any other failure stops the check.
  let client, landing;
  try {
    const require = createRequire(join(root, 'package.json'));
    const { runnerImport } = await import(pathToFileURL(require.resolve('vite')).href);
    const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root })).module;
    client = await load('./src/shared/markets.ts');
    landing = await load('./src/landing/priceText.ts');
  } catch (e) {
    if (e?.code !== 'MODULE_NOT_FOUND') throw e;
    console.error(`note: vite is not installed under ${root}, so the checks that run the site's code (src/shared/markets.ts, the landing's price texts) are skipped; the file checks run`);
  }
  const problems = checkPrices(root, client, landing);
  const { markets } = parseMarketsSource(readFileSync(join(root, MARKETS_FILE), 'utf8'));
  if (problems.length) {
    console.error(`price check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
    process.exit(1);
  }
  console.log(`price check ok: ${Object.keys(markets).length} markets in ${relative(process.cwd(), join(root, MARKETS_FILE)).split(sep).join('/')}, no other copy`);
}
