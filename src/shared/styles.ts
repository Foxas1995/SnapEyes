// The styles the site knows, shared by the landing page, /try, the order page and the admin panel. Plain data and functions only, no
// React, so the build's checks (scripts/check_styles.mjs) and the legal pack can import it too.
//
// THE ONE PLACE for style ids, names, slugs, layouts, stages and the price class is api/_lib/styles_registry.py: the server reads
// it through api/_lib/catalogue.py, and this module reads that same file as text at build time and parses its STYLES literal as
// JSON (as src/shared/markets.ts does with api/_lib/markets.py). Nothing here or anywhere else in src holds a list of style ids,
// a style name or the rule that makes a style cost the black price; the build fails when one does (scripts/check_styles.mjs, run
// by vite.config.ts). What a page may know is in that literal; how an engine draws a style is not (api/_lib/styles_engine.py).
//
// The stage here is the CEILING from the literal. The stage a customer meets is the server's: the effective stage, the ceiling
// lowered by the owner's override in the admin page (catalogue.stage_of), which the pages get from the server's catalogue and tile
// answers. A page never decides by itself that a style can be bought.
import STYLES_SOURCE from '../../api/_lib/styles_registry.py?raw';

export type Stage = 'planned' | 'lab' | 'preview' | 'live' | 'retired';
export type PriceClass = 'black' | 'art';
export type StyleGroup = 'solo' | 'duo' | 'grp' | 'pet';
export type EyeClass = 'own' | 'dark_brown' | 'grey';
export type GatePolicy = 'none' | 'advisory' | 'hard';

export interface StyleDef {
  group: StyleGroup;
  slug: string;
  name: string;
  legacy: number;
  eyes: [number, number];
  layouts: Record<string, string[]>;
  stage: Stage;
  stage_by_eyes: Record<string, Stage>;
  price_class: PriceClass;
  gate: GatePolicy;
  pick: EyeClass[];
  reason: Record<string, string>;
  tile_order: number;
  work_side: Record<string, number>;
  accent: number[];
}

/** The STYLES_SCHEMA, PLATES_VERSION, DEFAULT_STYLE and STYLES of api/_lib/styles_registry.py's text (the STYLES literal is plain
 *  JSON and ends the file). scripts/styles_source.mjs parses it the same way and the build compares the two readings. */
export function parseStylesSource(src: string): { schema: number; platesVersion: number; defaultStyle: string; effectiveDefault: string; styles: Record<string, StyleDef> } {
  const schema = /^STYLES_SCHEMA = (\d+)\s*$/m.exec(src);
  const pv = /^PLATES_VERSION = (\d+)\s*$/m.exec(src);
  const def = /^DEFAULT_STYLE = "([a-z][a-z0-9_.]*)"\s*$/m.exec(src);
  const eff = /^EFFECTIVE_DEFAULT = "([a-z]*)"\s*$/m.exec(src);
  const at = src.search(/^STYLES = \{/m);
  if (!schema || !pv || !def || !eff || at < 0) throw new Error('api/_lib/styles_registry.py: STYLES_SCHEMA, PLATES_VERSION, DEFAULT_STYLE, EFFECTIVE_DEFAULT or STYLES not found');
  return {
    schema: Number(schema[1]),
    platesVersion: Number(pv[1]),
    defaultStyle: def[1],
    effectiveDefault: eff[1],
    styles: JSON.parse(src.slice(at + 'STYLES = '.length)) as Record<string, StyleDef>,
  };
}

const PARSED = parseStylesSource(STYLES_SOURCE);
export const STYLES_SCHEMA: number = PARSED.schema;
export const PLATES_VERSION: number = PARSED.platesVersion;
/** The style a preview falls back to when a request names none the server knows. */
export const DEFAULT_STYLE: string = PARSED.defaultStyle;
/** The stage a style of the v3 engine has until the owner's tick says otherwise ("preview" since the cutover; "" means the ceiling alone decides).
 *  api/_lib/catalogue.py EFFECTIVE_DEFAULT reads the same line. */
export const EFFECTIVE_DEFAULT: Stage | '' = PARSED.effectiveDefault as Stage | '';
export const STYLES: Readonly<Record<string, StyleDef>> = PARSED.styles;
/** Every id, in the order of the file. */
export const STYLE_IDS: readonly string[] = Object.keys(STYLES);
/** The six engine ids of today, in the order of the engine (api/_lib/iris.py STYLES); they leave at the v3 cutover. */
export const LEGACY_IDS: readonly string[] = STYLE_IDS.filter((id) => STYLES[id].legacy === 1);
/** {id: brand name} of every id: the admin's names. Brand names are English in every language. */
export const STYLE_NAMES: Readonly<Record<string, string>> = Object.fromEntries(STYLE_IDS.map((id) => [id, STYLES[id].name]));

export const isStyle = (v: unknown): v is string => typeof v === 'string' && Object.prototype.hasOwnProperty.call(STYLES, v);
/** The brand name; an unknown id is returned as it came. */
export const styleName = (id: string): string => (isStyle(id) ? STYLES[id].name : id);
/** black or art. An unknown id is art (api/_lib/catalogue.py price_class: the same rule). */
export const priceClass = (id: string): PriceClass => (isStyle(id) ? STYLES[id].price_class : 'art');
/** The one predicate behind the black price (api/_lib/catalogue.py is_black). */
export const isBlack = (id: string): boolean => priceClass(id) === 'black';

const rangeOf = (key: string): [number, number] => {
  const [a, b] = key.split('-');
  return [Number(a), Number(b ?? a)];
};

/** The ceiling stage of a style for n eyes (api/_lib/catalogue.py ceiling), or null when it takes no n eyes. */
export function ceilingStage(id: string, n: number): Stage | null {
  if (!isStyle(id)) return null;
  const d = STYLES[id];
  if (!Number.isInteger(n) || n < d.eyes[0] || n > d.eyes[1]) return null;
  for (const [k, v] of Object.entries(d.stage_by_eyes)) {
    const [lo, hi] = rangeOf(k);
    if (lo <= n && n <= hi) return v;
  }
  return d.stage;
}

const STAGE_RANK: Readonly<Record<string, number>> = { planned: 0, lab: 1, preview: 2, live: 3 };

/** The stage a page may assume for n eyes before the server has answered: the ceiling, held at EFFECTIVE_DEFAULT for a style of the v3 engine (the owner's
 *  recorded tick, not the literal, makes a style orderable: api/_lib/catalogue.py stage_with does the same on the server). The legacy ids are never held to
 *  it, and a retired ceiling is final. Null when the style takes no n eyes. The server's answer (src/shared/catalogue.ts) replaces this the moment it comes. */
export function buildStage(id: string, n: number): Stage | null {
  const c = ceilingStage(id, n);
  if (c === null || c === 'retired' || !EFFECTIVE_DEFAULT || STYLES[id].legacy === 1) return c;
  return STAGE_RANK[c] <= STAGE_RANK[EFFECTIVE_DEFAULT] ? c : EFFECTIVE_DEFAULT;
}

/** The layouts n eyes can take in this style, the default first (empty when it takes no n eyes). */
export function layoutsFor(id: string, n: number): readonly string[] {
  return ceilingStage(id, n) === null ? [] : STYLES[id].layouts[String(n)] ?? [];
}

let legacyLayouts: Record<string, string[]> | null = null;
/** The layouts of the six legacy styles for n eyes, the default first (empty for any other n): the one table they share (api/_lib/catalogue.py
 *  legacy_layouts_table). The /try picker offers the legacy styles only until the new picker lands, so this is what it offers for n eyes. */
export function legacyLayoutsFor(n: number): readonly string[] {
  if (!legacyLayouts) {
    if (new Set(LEGACY_IDS.map((id) => JSON.stringify(STYLES[id].layouts))).size !== 1) {
      throw new Error('the legacy styles of api/_lib/styles_registry.py do not share one layout table');
    }
    legacyLayouts = STYLES[LEGACY_IDS[0]].layouts;
  }
  return legacyLayouts[String(n)] ?? [];
}

/** A style a customer can buy in a price class, for the places that show one example (api/_lib/catalogue.py class_style). */
export function classStyle(cls: PriceClass): string {
  const pool = STYLE_IDS.filter((id) => STYLES[id].price_class === cls && STYLES[id].eyes[0] <= 1);
  const live = pool.filter((id) => ceilingStage(id, 1) === 'live');
  const open = pool.filter((id) => !['planned', 'retired', null].includes(ceilingStage(id, 1)));
  return live[0] ?? open[0] ?? pool[0] ?? cls;
}

/** The six legacy styles in the order of the engine, as the picker draws them: id, name, and the accent colour of the swatch
 *  (null for the bare black one). */
export function legacyStyles(): { id: string; name: string; accent: [number, number, number] | null }[] {
  return LEGACY_IDS.map((id) => {
    const a = STYLES[id].accent;
    return { id, name: STYLES[id].name, accent: a.length === 3 ? [a[0], a[1], a[2]] : null };
  });
}

/** The styles of ONE eye as the landing gallery lists them: the ones of the v3 engine whose ceiling is live, in tile order (the registry's tile_order), with
 *  the slug of their tile images. A style that only opens soon (ceiling preview) is not listed (INTEGRATION_SPEC 1.8 rule 1: a Soon tile stays off the landing
 *  until the landing team and the owner accept it in writing); the six legacy ids are retired and never listed. Whether a listed style can be bought NOW is
 *  the run-time catalogue's answer (src/shared/catalogue.ts), never this list's. */
export function landingStyles(): { id: string; name: string; slug: string }[] {
  return STYLE_IDS.filter((id) => STYLES[id].legacy === 0 && STYLES[id].tile_order > 0 && STYLES[id].eyes[0] <= 1 && ceilingStage(id, 1) === 'live')
    .sort((a, b) => STYLES[a].tile_order - STYLES[b].tile_order)
    .map((id) => ({ id, name: STYLES[id].name, slug: STYLES[id].slug }));
}
