// The price check of the build: every price lives in ONE place, api/_lib/markets.py (the server charges from it and
// src/shared/markets.ts reads the same file for every page). This refuses the build when
//   1. that file's MARKETS literal is not plain JSON, or breaks a rule (currencies, Stripe's smallest units and minimum
//      charges, whole Australian dollars and whole forints, a selectable default market, ...);
//   2. the site's own reading of it (src/shared/markets.ts, loaded by vite.config.ts) differs from this one, or its
//      price rule (priceMinor) gives another price than api/_lib/pay.py's rule for any market, number of eyes and style;
//   3. any other file of the site or the server holds a price of its own: a price in Stripe's units in the files that
//      deal with prices, or a written price ("19.97", "A$39", "6 990 Ft") anywhere in src/ or api/ (comments aside);
//   4. a market is selectable in another currency than the default market's without its own edition of the legal
//      texts (src/shared/legal.ts EDITION_MARKETS = api/_lib/pay.py EDITION_MARKETS): the EU texts print euro prices
//      only. The two lists, and the languages each edition has (EDITION_LANGS in both files), must agree.
// vite.config.ts runs it before every build (with the site's reading, check 2); `npm run check:prices` runs 1, 3, 4.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const MARKETS_FILE = 'api/_lib/markets.py';
const CURRENCIES = ['eur', 'aud', 'huf'];
const PRICE_KEYS = ['one_eye_studio_black', 'one_eye_art', 'two_eyes', 'each_further_eye'];
const STYLES = ['studio_black', 'celestial_gold', 'deep_nebula', 'emerald_aurora', 'obsidian_smoke', 'supernova'];
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
  'src/shared/markets.ts', 'src/shared/legal.ts',
];
// Never scanned for written prices: the one place itself, and the image engine (another team's, no prices in it).
const SKIP = new Set([MARKETS_FILE, 'api/_lib/iris.py']);

/** DEFAULT_MARKET and MARKETS of api/_lib/markets.py's text (src/shared/markets.ts parseMarketsSource, the same rule). */
export function parseMarketsSource(src) {
  const d = /^DEFAULT_MARKET = "([a-z]{2,8})"\s*$/m.exec(src);
  const at = src.search(/^MARKETS = \{/m);
  if (!d || at < 0) throw new Error(`${MARKETS_FILE}: DEFAULT_MARKET or MARKETS not found`);
  return { defaultMarket: d[1], markets: JSON.parse(src.slice(at + 'MARKETS = '.length)) };
}

/** api/_lib/pay.py price_cents, restated: one eye by its style, two eyes, then the same amount per further eye. */
export function priceRule(markets, market, eyes, style) {
  const p = markets[market].prices;
  if (eyes <= 1) return style === 'studio_black' ? p.one_eye_studio_black : p.one_eye_art;
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

function checkClient(defaultMarket, markets, client, out) {
  if (client.DEFAULT_MARKET !== defaultMarket) out.push(`src/shared/markets.ts reads DEFAULT_MARKET "${client.DEFAULT_MARKET}", not "${defaultMarket}"`);
  if (!sameJson(client.MARKETS, markets)) out.push('src/shared/markets.ts reads another MARKETS than api/_lib/markets.py holds');
  for (const market of Object.keys(markets)) {
    for (let eyes = 1; eyes <= MAX_EYES; eyes++) {
      for (const style of STYLES) {
        const want = priceRule(markets, market, eyes, style);
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
      for (const style of ['studio_black', 'celestial_gold']) {
        const minor = priceRule(markets, key, eyes, style);
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
  for (const m of Object.values(markets)) for (const k of PRICE_KEYS) minors.add(m.prices[k]);
  const minorRe = new RegExp(`(?<![\\w.$])(${[...minors].map(String).map(esc).join('|')})(?![\\w.])`);
  for (const rel of PRICE_FILES) {
    let text;
    try { text = readFileSync(join(root, rel), 'utf8'); } catch { continue; }
    const code = stripComments(text, rel.endsWith('.py'));
    code.split('\n').forEach((line, i) => {
      const hit = minorRe.exec(line);
      if (hit) out.push(`${rel}: holds the price ${hit[1]} of its own (line ~${i + 1}); take it from ${MARKETS_FILE} (src/shared/markets.ts, api/_lib/pay.py)`);
    });
  }
  const written = writtenPatterns(markets);
  const files = [...listFiles(root, 'src', ['.ts', '.tsx']), ...listFiles(root, 'api', ['.py']), ...listFiles(root, 'scripts', ['.py'])];
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

/** Every problem found, as sentences ([] when the prices are sound). client: src/shared/markets.ts as the build loaded
 *  it (vite.config.ts), for the agreement check; without it that check is left out. */
export function checkPrices(root, client) {
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
  if (client) checkClient(defaultMarket, markets, client, out);
  checkCopies(root, markets, out);
  return out;
}

// `node scripts/check_prices.mjs` (npm run check:prices): checks 1 and 3, exit code 1 on any problem
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  const problems = checkPrices(root);
  const { markets } = parseMarketsSource(readFileSync(join(root, MARKETS_FILE), 'utf8'));
  if (problems.length) {
    console.error(`price check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
    process.exit(1);
  }
  console.log(`price check ok: ${Object.keys(markets).length} markets in ${relative(process.cwd(), join(root, MARKETS_FILE)).split(sep).join('/')}, no other copy`);
}
