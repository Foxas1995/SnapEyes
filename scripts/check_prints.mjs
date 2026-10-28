// The print check of the build (scripts/check_prices.mjs runs it with the price check, so every build and `npm run check:prices` run it):
// the prints of api/_lib/print_offer.py (the one place of a print's retail price), the cost table api/_lib/print_rates.py (written by
// scripts/print_rates.py from the merchOne API) and the words api/_lib/print_names.py. It refuses
//   1. a literal that is not plain JSON, or a field that breaks a rule (euro cents, Stripe's minimum, a known kind, a SKU in the rate table, one
//      id once, a market that is a selectable or paused euro market of the EU edition: never one with its own edition of the legal texts);
//   2. a country of the rate table without a rate for every SKU of the offer, or without its name in every language; a kind without its words;
//   3. a print that earns less than margin_floor in any country it ships to, after merchOne's price and shipping with VAT and the fee
//      (marginTable says what each one earns: the output of `npm run check:prices` prints it);
//   4. with the site's module (src/shared/prints.ts, loaded by `npm run check:prices`): its reading of the three files differs from this one, or
//      its shipping rule (shipPrice) or its margin gives another number than the rule restated here, for any country and print;
//   5. a written print price ("59,00 €", "€59.00") in any file of src/ or api/ but the offer itself.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

export const OFFER_FILE = 'api/_lib/print_offer.py';
export const RATES_FILE = 'api/_lib/print_rates.py';
export const NAMES_FILE = 'api/_lib/print_names.py';
const LANGS = ['en', 'de', 'lt', 'hu', 'hr'];
const KINDS = ['acrylic', 'canvas', 'poster'];
const STRIPE_MIN_EUR = 50;

/** The literal NAME = { ... } that ends a Python file (src/shared/prints.ts parseLiteral, the same rule). */
export function parseLiteral(src, name) {
  const at = src.search(new RegExp(`^${name} = \\{`, 'm'));
  if (at < 0) throw new Error(`${name} not found`);
  return JSON.parse(src.slice(at + name.length + 3));
}

const isInt = (v) => typeof v === 'number' && Number.isInteger(v);
export const withVat = (cents, vat) => Math.ceil((cents * (100 + vat)) / 100 - 1e-9);
/** The customer's shipping: the cost with VAT, rounded UP to the next amount that ends in .49 or .99 (api/_lib/prints.py ship_price). */
export function shipRule(cost, vat) {
  const c = withVat(cost, vat);
  for (let v = c; v < c + 100; v++) if (v % 100 === 49 || v % 100 === 99) return v;
  return c;
}
/** What a print earns in a country (api/_lib/prints.py margin): its price and shipping, less merchOne's price and shipping with VAT and the fee. */
export function marginRule(offer, rates, id, cc) {
  const p = offer.products.find((x) => x.id === id);
  const s = p && rates.skus[p.sku];
  const sc = p && rates.shipping[cc]?.[p.sku];
  if (!p || !s || !isInt(sc)) return null;
  const paid = p.price + shipRule(sc, offer.vat_pct);
  return paid - withVat(s.cost + sc, offer.vat_pct) - Math.ceil((paid * offer.fee_pct) / 100 - 1e-9);
}

export function readPrints(root) {
  const read = (rel, name) => parseLiteral(readFileSync(join(root, rel), 'utf8'), name);
  return { offer: read(OFFER_FILE, 'PRINT_OFFER'), rates: read(RATES_FILE, 'PRINT_RATES'), names: read(NAMES_FILE, 'PRINT_NAMES') };
}

/** {id: {min, max, worst}} of what each print earns, in cents, over the countries it ships to. */
export function marginTable(offer, rates) {
  const out = {};
  for (const p of offer.products) {
    let min = Infinity, max = -Infinity, worst = '';
    for (const cc of Object.keys(rates.shipping)) {
      const m = marginRule(offer, rates, p.id, cc);
      if (m === null) continue;
      if (m < min) { min = m; worst = cc; }
      if (m > max) max = m;
    }
    out[p.id] = { min, max, worst };
  }
  return out;
}

function listFiles(root, dir, exts, acc = []) {
  let names = [];
  try { names = readdirSync(join(root, dir)); } catch { return acc; }
  for (const n of names) {
    if (n === 'node_modules' || n === '__pycache__' || n.startsWith('.')) continue;
    const rel = `${dir}/${n}`;
    if (statSync(join(root, rel)).isDirectory()) listFiles(root, rel, exts, acc);
    else if (exts.some((e) => n.endsWith(e))) acc.push(rel);
  }
  return acc;
}

const stripComments = (text, py) => (py
  ? text.replace(/^[ \t]*[rRbBuU]?("""|''')[\s\S]*?\1/gm, '').replace(/(^|[ \t])#.*$/gm, '$1')
  : text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`\\])\/\/.*$/gm, '$1'));

/** Every problem of the prints (a list of sentences; empty when everything holds). markets: api/_lib/markets.py's MARKETS; editionMarkets: the
 *  markets with their own edition of the legal texts (pay.py EDITION_MARKETS); client: src/shared/prints.ts as the site loaded it, or none. */
export function checkPrints(root, markets, editionMarkets, client) {
  const out = [];
  let t;
  try {
    t = readPrints(root);
  } catch (e) {
    return [`${OFFER_FILE}, ${RATES_FILE} or ${NAMES_FILE}: a literal cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`];
  }
  const { offer, rates, names } = t;
  const at = OFFER_FILE;
  if (offer.currency !== 'eur') out.push(`${at}: currency must be "eur" (prints are sold on the euro price lists only)`);
  for (const k of ['vat_pct', 'fee_pct', 'margin_floor']) if (!isInt(offer[k]) || offer[k] < 0) out.push(`${at}: ${k} must be a whole number of 0 or more`);
  if (!Array.isArray(offer.markets) || !offer.markets.length) out.push(`${at}: markets must name at least one market`);
  for (const m of offer.markets ?? []) {
    if (!markets?.[m]) out.push(`${at}: market "${m}" is not in api/_lib/markets.py`);
    else if (markets[m].currency !== 'eur') out.push(`${at}: market "${m}" is not a euro market`);
    if (editionMarkets.includes(m)) out.push(`${at}: market "${m}" reads its own edition of the legal texts, whose terms have no prints`);
  }
  const ids = new Set();
  if (!Array.isArray(offer.products) || !offer.products.length) out.push(`${at}: products must hold at least one print`);
  for (const p of offer.products ?? []) {
    const where = `${at} product "${p?.id}"`;
    const keys = Object.keys(p ?? {}).sort().join();
    if (keys !== ['cm', 'id', 'kind', 'on', 'price', 'sku'].join()) out.push(`${where}: its fields must be exactly cm, id, kind, on, price, sku (has ${keys})`);
    if (typeof p.id !== 'string' || !/^[a-z0-9]{2,20}$/.test(p.id)) out.push(`${where}: id must be 2 to 20 lower-case letters and digits`);
    if (ids.has(p.id)) out.push(`${where}: the id is there twice`);
    ids.add(p.id);
    if (!KINDS.includes(p.kind)) out.push(`${where}: kind must be one of ${KINDS.join(', ')}`);
    if (!isInt(p.cm) || p.cm < 10 || p.cm > 200) out.push(`${where}: cm must be a whole number of centimetres`);
    if (!isInt(p.price) || p.price < STRIPE_MIN_EUR) out.push(`${where}: price must be whole euro cents, at least Stripe's minimum`);
    if (p.on !== 0 && p.on !== 1) out.push(`${where}: on must be 1 or 0`);
    if (!rates.skus?.[p.sku]) out.push(`${where}: its SKU ${p.sku} is not in ${RATES_FILE} (run scripts/print_rates.py)`);
  }
  // the rate table and the words
  for (const [sku, r] of Object.entries(rates.skus ?? {})) {
    if (!isInt(r.cost) || r.cost <= 0 || !Array.isArray(r.file_px) || !Array.isArray(r.design_px) || !isInt(r.dpi)) out.push(`${RATES_FILE}: ${sku} is not complete (cost, print file, design area, dpi)`);
  }
  const ccs = Object.keys(rates.shipping ?? {});
  if (!ccs.length) out.push(`${RATES_FILE}: no country to ship to`);
  for (const cc of ccs) {
    for (const p of offer.products ?? []) if (!isInt(rates.shipping[cc]?.[p.sku])) out.push(`${RATES_FILE}: ${cc} has no rate for ${p.sku} (run scripts/print_rates.py)`);
    const w = names.countries?.[cc];
    for (const l of LANGS) if (!(w && typeof w[l] === 'string' && w[l])) out.push(`${NAMES_FILE}: country ${cc} has no ${l} name`);
  }
  for (const k of new Set((offer.products ?? []).map((p) => p.kind))) {
    for (const l of LANGS) if (!(names.kinds?.[k] && typeof names.kinds[k][l] === 'string')) out.push(`${NAMES_FILE}: kind ${k} has no ${l} words`);
  }
  // the margin of every print in every country
  if (!out.length) {
    const table = marginTable(offer, rates);
    for (const p of offer.products) {
      if (p.on !== 1) continue;
      const m = table[p.id];
      if (m.min < offer.margin_floor) out.push(`${at} product "${p.id}": earns only ${(m.min / 100).toFixed(2)} EUR in ${m.worst} (under the floor of ${(offer.margin_floor / 100).toFixed(2)}): raise its price or take it off the offer`);
    }
  }
  // the site's own reading and rules
  if (client && !out.length) {
    const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
    if (!same(client.PRINT_OFFER, offer)) out.push(`src/shared/prints.ts reads ${OFFER_FILE} differently from this check`);
    if (!same(client.PRINT_RATES, rates)) out.push(`src/shared/prints.ts reads ${RATES_FILE} differently from this check`);
    if (!same(client.PRINT_NAMES, names)) out.push(`src/shared/prints.ts reads ${NAMES_FILE} differently from this check`);
    for (const p of offer.products) {
      for (const cc of ccs) {
        const want = shipRule(rates.shipping[cc][p.sku], offer.vat_pct);
        if (p.on === 1 && client.printShipping(cc, p.id) !== want) out.push(`src/shared/prints.ts printShipping(${cc}, ${p.id}) is not ${want} (the shipping rule of api/_lib/prints.py)`);
        if (client.printMargin(p.id, cc) !== marginRule(offer, rates, p.id, cc)) out.push(`src/shared/prints.ts printMargin(${p.id}, ${cc}) differs from the rule`);
      }
    }
    for (const c of [1, 49, 50, 99, 100, 399, 550, 699, 799, 1099]) if (client.shipPrice(c) !== shipRule(c, offer.vat_pct)) out.push(`src/shared/prints.ts shipPrice(${c}) differs from the rule`);
  }
  // no written print price outside the offer
  const written = (offer.products ?? []).filter((p) => isInt(p.price) && p.price % 100 === 0).map((p) => [p.price, new RegExp(`(?<![\\d.,])${p.price / 100}[.,]00(?![\\d])`)]);
  const files = [...listFiles(root, 'src', ['.ts', '.tsx']), ...listFiles(root, 'api', ['.py'])].filter((f) => f !== OFFER_FILE);
  for (const rel of files) {
    const code = stripComments(readFileSync(join(root, rel), 'utf8'), rel.endsWith('.py'));
    for (const [price, re] of written) {
      const i = code.split('\n').findIndex((l) => re.test(l));
      if (i >= 0) out.push(`${rel}: writes the print price ${(price / 100).toFixed(2)} itself (line ~${i + 1}); print it from ${OFFER_FILE} instead`);
    }
  }
  return out;
}
