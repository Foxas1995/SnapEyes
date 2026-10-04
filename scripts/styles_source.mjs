// The registry files as the build scripts read them (no checks here, so scripts/check_prices.mjs, scripts/check_experiments.mjs and
// scripts/check_styles.mjs can all import it without importing each other): api/_lib/styles_registry.py (the public literal, the
// one place for style ids, names, layouts, stages and the price class) and api/_lib/styles_engine.py (how each style is drawn,
// Python only). Both are a JSON literal inside a Python file that ends the file, as api/_lib/markets.py is.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';

export const STYLES_FILE = 'api/_lib/styles_registry.py';
export const ENGINE_FILE = 'api/_lib/styles_engine.py';

/** The JSON literal that ends a file, after "<name> = " at the start of a line. Throws when it is not there or is not plain JSON. */
export function parseLiteral(src, name, file) {
  const at = src.search(new RegExp(`^${name} = \\{`, 'm'));
  if (at < 0) throw new Error(`${file}: ${name} not found`);
  return JSON.parse(src.slice(at + `${name} = `.length));
}

/** {schema, platesVersion, defaultStyle, styles} of styles_registry.py's text. */
export function parseRegistrySource(src) {
  const schema = /^STYLES_SCHEMA = (\d+)\s*$/m.exec(src);
  const pv = /^PLATES_VERSION = (\d+)\s*$/m.exec(src);
  const def = /^DEFAULT_STYLE = "([a-z][a-z0-9_.]*)"\s*$/m.exec(src);
  if (!schema || !pv || !def) throw new Error(`${STYLES_FILE}: STYLES_SCHEMA, PLATES_VERSION or DEFAULT_STYLE not found (one line each: NAME = value)`);
  return { schema: Number(schema[1]), platesVersion: Number(pv[1]), defaultStyle: def[1], styles: parseLiteral(src, 'STYLES', STYLES_FILE) };
}

/** The ENGINE literal of styles_engine.py's text. */
export function parseEngineSource(src) {
  return parseLiteral(src, 'ENGINE', ENGINE_FILE);
}

export function loadRegistry(root) {
  return parseRegistrySource(readFileSync(join(root, STYLES_FILE), 'utf8'));
}

export function loadEngine(root) {
  return parseEngineSource(readFileSync(join(root, ENGINE_FILE), 'utf8'));
}

/** JSON with sorted keys and no spaces: the same text api/_lib/catalogue.py canonical() makes (ASCII and whole numbers only). */
export function canon(v) {
  if (Array.isArray(v)) return `[${v.map(canon).join(',')}]`;
  if (v && typeof v === 'object') return `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${canon(v[k])}`).join(',')}}`;
  return JSON.stringify(v);
}

/** The registry hash: 12 hex digits of the sha256 of both literals and the constants in canonical form (catalogue.registry_hash). */
export function registryHash(registry, engine) {
  const text = canon({ schema: registry.schema, pv: registry.platesVersion, default: registry.defaultStyle, styles: registry.styles, engine });
  return createHash('sha256').update(text, 'ascii').digest('hex').slice(0, 12);
}

/** The price class of a style id: "black" or "art" (an unknown id is "art", as catalogue.price_class says). */
export function priceClassOf(styles, id) {
  return Object.prototype.hasOwnProperty.call(styles, id) ? styles[id].price_class : 'art';
}

/** [lo, hi] of a range key: "3" is [3, 3], "4-8" is [4, 8]. */
export function rangeOf(key) {
  const [a, b] = String(key).split('-');
  return [Number(a), Number(b ?? a)];
}

/** The value of a range-keyed map ({"3": x, "4-8": y}) for n eyes, or the fallback. */
export function byEyes(map, n, fallback) {
  for (const [k, v] of Object.entries(map ?? {})) {
    const [lo, hi] = rangeOf(k);
    if (lo <= n && n <= hi) return v;
  }
  return fallback;
}

/** The ceiling stage of an entry for n eyes (catalogue.ceiling), or null when it takes no n eyes. */
export function ceilingOf(d, n) {
  return d.eyes[0] <= n && n <= d.eyes[1] ? byEyes(d.stage_by_eyes, n, d.stage) : null;
}

/** A style a customer can buy in a class, for the messages that name one (catalogue.class_style): the first live style that takes one
 *  eye, else the first of the class that is neither planned nor retired, else the first of the class. */
export function classStyle(styles, cls) {
  const pool = Object.entries(styles).filter(([, d]) => d.price_class === cls && d.eyes[0] <= 1);
  const live = pool.filter(([, d]) => ceilingOf(d, 1) === 'live');
  const open = pool.filter(([, d]) => !['planned', 'retired', null].includes(ceilingOf(d, 1)));
  return (live[0] ?? open[0] ?? pool[0])?.[0] ?? cls;
}
