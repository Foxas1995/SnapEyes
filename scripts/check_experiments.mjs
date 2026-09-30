// The build's check of the price experiments (api/_lib/experiments.py; the server side is api/_lib/abtest.py). Called by
// scripts/check_prices.mjs, so `npm run check:prices` and every build (vite.config.ts) run it. It refuses the build when
//   1. the COSTS and EXPERIMENTS literals of experiments.py are not plain JSON, or an experiment breaks a rule: fields,
//      a key, markets that exist and share one currency, a split of whole percents adding up to 100, a variant "control"
//      and at least one other, and for EVERY variant a FULL ladder (all four prices) for EVERY market of the experiment;
//   2. a ladder breaks a price rule (Stripe's smallest unit and minimum charge, whole Australian dollars and forints,
//      more eyes never cheaper, eight eyes within one Stripe payment), or the control ladder is not the standard ladder
//      of markets.py (a test marked "retired": 1 is exempt from this and from 3), or the prices that differ between the
//      variants are not exactly the ones "changes" names;
//   3. a variant would sell at a loss (its price after Stripe's fee and about 0.22 US dollars of image work per eye is
//      negative for some number of eyes and style: the same estimate the admin page warns with);
//   4. the site's own price rule (src/shared/markets.ts priceMinor, fed the variant's ladder as the server's answer feeds
//      it) gives another price than the server's rule for any variant, market, number of eyes and style;
//   5. (scripts/check_prices.mjs, with withVariantLadders) no other file holds a price of a variant of its own.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export const EXPERIMENTS_FILE = 'api/_lib/experiments.py';
const PRICE_KEYS = ['one_eye_studio_black', 'one_eye_art', 'two_eyes', 'each_further_eye'];
const STYLES = ['studio_black', 'celestial_gold', 'deep_nebula', 'emerald_aurora', 'obsidian_smoke', 'supernova'];
const MAX_EYES = 8;
const STRIPE_MIN = { eur: 50, aud: 50, huf: 17500 };
const isInt = (v) => typeof v === 'number' && Number.isInteger(v);

/** {costs, experiments} of api/_lib/experiments.py's text: two JSON literals, COSTS first and EXPERIMENTS last. */
export function parseExperimentsSource(src) {
  const c = src.search(/^COSTS = \{/m);
  const e = src.search(/^EXPERIMENTS = \{/m);
  if (c < 0 || e < 0 || e < c) throw new Error(`${EXPERIMENTS_FILE}: COSTS and EXPERIMENTS not found (COSTS first, EXPERIMENTS last)`);
  return {
    costs: JSON.parse(src.slice(c + 'COSTS = '.length, e)),
    experiments: JSON.parse(src.slice(e + 'EXPERIMENTS = '.length)),
  };
}

/** One price of a ladder rule, restated (api/_lib/pay.py price_cents and abtest.ladder_price are the same rule). */
export function ladderRule(l, eyes, style) {
  if (eyes <= 1) return style === 'studio_black' ? l.one_eye_studio_black : l.one_eye_art;
  return l.two_eyes + (eyes - 2) * l.each_further_eye;
}

/** What is left of a price after Stripe's fee and the image work (experiments.py COSTS), in the smallest unit. */
export function netMinor(costs, currency, priceMinor, eyes) {
  const price = priceMinor / 100;
  const cost = eyes * costs.unit_usd_per_eye * costs.per_usd[currency] + costs.fee_fixed_eur * costs.per_eur[currency]
    + (price * costs.fee_pct[currency]) / 100;
  return Math.round((price - cost) * 100);
}

/** markets plus one pseudo market per variant ladder ("<experiment>:<variant>:<market>"), so scripts/check_prices.mjs's
 *  copy scan knows every price a variant can charge. */
export function withVariantLadders(markets, experiments) {
  if (!experiments) return markets;
  const out = { ...markets };
  for (const [key, d] of Object.entries(experiments)) {
    for (const [name, v] of Object.entries(d?.variants ?? {})) {
      for (const [m, prices] of Object.entries(v?.prices ?? {})) {
        if (markets[m] && prices && typeof prices === 'object') out[`${key}:${name}:${m}`] = { ...markets[m], prices, variant: true };
      }
    }
  }
  return out;
}

function checkLadder(at, currency, p, out) {
  if (!p || typeof p !== 'object' || Object.keys(p).sort().join() !== [...PRICE_KEYS].sort().join()) {
    out.push(`${at}: a FULL ladder is required: exactly ${PRICE_KEYS.join(', ')}`);
    return false;
  }
  let ok = true;
  for (const k of PRICE_KEYS) {
    const v = p[k];
    if (!isInt(v) || v <= 0) { out.push(`${at}: ${k} must be a positive whole number in Stripe's smallest unit`); ok = false; continue; }
    if (v < STRIPE_MIN[currency]) out.push(`${at}: ${k} ${v} is below Stripe's minimum charge`);
    if (currency === 'huf' && v % 100 !== 0) out.push(`${at}: ${k} ${v} is not whole forints`);
    if (currency === 'aud' && v % 100 !== 0) out.push(`${at}: ${k} ${v} is not whole Australian dollars`);
  }
  if (!ok) return false;
  if (p.two_eyes + (MAX_EYES - 2) * p.each_further_eye > 99999999) out.push(`${at}: ${MAX_EYES} eyes cost more than Stripe takes in one payment`);
  if (p.one_eye_art < p.one_eye_studio_black) out.push(`${at}: one eye on an art background must not cost less than Studio Black`);
  for (const style of ['studio_black', 'celestial_gold']) {
    for (let n = 1; n < MAX_EYES; n++) {
      if (ladderRule(p, n + 1, style) <= ladderRule(p, n, style)) out.push(`${at}: ${n + 1} eyes must cost more than ${n} (${style})`);
    }
  }
  return true;
}

/** Every problem of the experiments as sentences, appended to out; returns the parsed experiments (null when the file
 *  cannot be read). client: src/shared/markets.ts as the build loaded it, for check 4 (left out without it). */
export function checkExperiments(root, markets, out, client) {
  let parsed;
  let src;
  try {
    src = readFileSync(join(root, EXPERIMENTS_FILE), 'utf8');
    parsed = parseExperimentsSource(src);
  } catch (e) {
    out.push(`${EXPERIMENTS_FILE}: the COSTS and EXPERIMENTS literals cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`);
    return null;
  }
  const { costs, experiments } = parsed;
  if (new RegExp('[' + String.fromCharCode(0x2013, 0x2014) + ']').test(src)) out.push(`${EXPERIMENTS_FILE}: no en or em dash anywhere in this file`);
  for (const k of ['unit_usd_per_eye', 'fee_fixed_eur']) if (typeof costs?.[k] !== 'number' || !(costs[k] >= 0)) out.push(`${EXPERIMENTS_FILE} COSTS: ${k} must be a number`);
  for (const k of ['per_usd', 'per_eur', 'fee_pct']) {
    for (const cur of Object.keys(STRIPE_MIN)) if (typeof costs?.[k]?.[cur] !== 'number' || !(costs[k][cur] >= 0)) out.push(`${EXPERIMENTS_FILE} COSTS: ${k}.${cur} must be a number`);
  }
  if (!experiments || typeof experiments !== 'object' || Array.isArray(experiments)) {
    out.push(`${EXPERIMENTS_FILE}: EXPERIMENTS is not an object`);
    return null;
  }
  for (const [key, d] of Object.entries(experiments)) {
    const at = `${EXPERIMENTS_FILE} experiment "${key}"`;
    if (!/^[a-z][a-z0-9_]{2,39}$/.test(key)) out.push(`${at}: the key must be lower case letters, digits and _ (3 to 40 characters)`);
    if (!d || typeof d !== 'object') { out.push(`${at}: not an object`); continue; }
    const want = ['about', 'changes', 'hit_label', 'markets', 'split', 'title', 'variants'];
    // "retired": 1 (optional) keeps a finished test for its history: never assigned, never started again, and its control
    // ladder may differ from the standard one after the owner adopted a winner (markets.py changed)
    const retired = d.retired === 1;
    if ('retired' in d && d.retired !== 0 && d.retired !== 1) out.push(`${at}: retired is 1 or left out`);
    const have = Object.keys(d).filter((f) => f !== 'retired').sort();
    if (have.join() !== want.join()) out.push(`${at}: its fields must be exactly ${want.join(', ')} (and optionally retired) (has ${have.join(', ')})`);
    for (const f of ['title', 'about', 'hit_label']) if (typeof d[f] !== 'string' || !d[f].trim()) out.push(`${at}: ${f} must be a sentence`);
    const ms = d.markets;
    if (!Array.isArray(ms) || !ms.length || new Set(ms).size !== ms.length || ms.some((m) => typeof m !== 'string' || !markets[m])) {
      out.push(`${at}: markets must be a non-empty list of distinct markets of api/_lib/markets.py`);
      continue;
    }
    const currencies = new Set(ms.map((m) => markets[m].currency));
    if (currencies.size !== 1) { out.push(`${at}: its markets must share one currency (has ${[...currencies].join(', ')})`); continue; }
    const currency = [...currencies][0];
    if (!Array.isArray(d.changes) || !d.changes.length || d.changes.some((c) => !PRICE_KEYS.includes(c)) || new Set(d.changes).size !== d.changes.length) {
      out.push(`${at}: changes must list which of ${PRICE_KEYS.join(', ')} differ between the variants`);
    }
    const vs = d.variants;
    if (!vs || typeof vs !== 'object' || Array.isArray(vs) || !vs.control || Object.keys(vs).length < 2) {
      out.push(`${at}: variants needs "control" and at least one other variant`);
      continue;
    }
    const names = Object.keys(vs);
    if (names.some((n) => !/^[a-z][a-z0-9_]{1,39}$/.test(n))) out.push(`${at}: a variant name must be lower case letters, digits and _`);
    const split = d.split;
    if (!split || typeof split !== 'object' || Object.keys(split).sort().join() !== [...names].sort().join()
      || Object.values(split).some((x) => !isInt(x) || x <= 0) || Object.values(split).reduce((a, b) => a + b, 0) !== 100) {
      out.push(`${at}: split must give every variant a whole percent above 0, adding up to 100`);
    }
    const ladders = {};
    for (const [name, v] of Object.entries(vs)) {
      const vat = `${at} variant "${name}"`;
      if (!v || typeof v !== 'object' || Object.keys(v).sort().join() !== 'label,prices') { out.push(`${vat}: its fields must be exactly label, prices`); continue; }
      if (typeof v.label !== 'string' || !v.label.trim()) out.push(`${vat}: label must be a sentence`);
      if (!v.prices || typeof v.prices !== 'object' || Object.keys(v.prices).sort().join() !== [...ms].sort().join()) {
        out.push(`${vat}: prices must have a full ladder for exactly the markets ${ms.join(', ')}`);
        continue;
      }
      for (const m of ms) {
        if (checkLadder(`${vat} market "${m}"`, currency, v.prices[m], out)) {
          (ladders[m] ||= {})[name] = v.prices[m];
          if (name === 'control' && !retired && PRICE_KEYS.some((k) => v.prices[m][k] !== markets[m].prices[k])) {
            out.push(`${vat} market "${m}": the control ladder is not the standard ladder of api/_lib/markets.py (they must be the same)`);
          }
          for (const eyes of Array.from({ length: MAX_EYES }, (_, i) => i + 1)) {
            for (const style of eyes === 1 ? ['studio_black', 'celestial_gold'] : ['studio_black']) {
              const price = ladderRule(v.prices[m], eyes, style);
              if (!retired && netMinor(costs, currency, price, eyes) < 0) {
                out.push(`${vat} market "${m}": ${eyes} eye(s), ${style} would sell at a loss (price ${price}, after Stripe's fee and the image work ${netMinor(costs, currency, price, eyes)})`);
              }
            }
          }
        }
      }
    }
    for (const m of ms) {
      const set = ladders[m];
      if (!set || Object.keys(set).length < 2) continue;
      const differ = PRICE_KEYS.filter((k) => new Set(Object.values(set).map((l) => l[k])).size > 1);
      if (!differ.length) out.push(`${at} market "${m}": the variants have the same ladder, so there is nothing to test`);
      else if (Array.isArray(d.changes) && differ.slice().sort().join() !== d.changes.slice().sort().join()) {
        out.push(`${at} market "${m}": the ladders differ in ${differ.join(', ')} but changes says ${d.changes.join(', ')}`);
      }
      if (client && typeof client.priceMinor === 'function') {
        for (const [name, l] of Object.entries(set)) {
          for (let eyes = 1; eyes <= MAX_EYES; eyes++) {
            for (const style of STYLES) {
              const got = client.priceMinor(eyes, style, m, l);
              const wantPrice = ladderRule(l, eyes, style);
              if (got !== wantPrice) out.push(`src/shared/markets.ts priceMinor(${eyes}, ${style}, ${m}, ladder of "${key}"/"${name}") = ${got}, the server charges ${wantPrice}`);
            }
          }
        }
      }
    }
  }
  return experiments;
}
