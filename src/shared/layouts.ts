// The words for the layouts (how the irises of an artwork are arranged), shared by the picker (/try), the order page and the checks. Plain
// data and functions only, no React, so the build's checks (scripts/check_styles.mjs, scripts/check_texts.mjs) can import it too.
//
// THE ONE PLACE for these words is api/_lib/layout_names.py: the server reads it through api/_lib/catalogue.py layout_name (the e-mails),
// and this module reads that same file as text at build time and parses its LAYOUT_NAMES literal as JSON (as src/shared/styles.ts does with
// the style registry). No dictionary of the pages and no table of a Python file names layouts any more; the build fails when one does.
// Which layout ids a style takes for each number of eyes is the registry's (src/shared/styles.ts layoutsFor), not this file's.
import LAYOUT_NAMES_SOURCE from '../../api/_lib/layout_names.py?raw';

/** The languages every layout has a word in (the site's four: src/shared/lang.ts). */
export const LAYOUT_LANGS = ['en', 'de', 'lt', 'hu'] as const;
export type LayoutWords = Record<(typeof LAYOUT_LANGS)[number], string>;

/** The LAYOUT_NAMES literal of api/_lib/layout_names.py's text (plain JSON, it ends the file). scripts/styles_source.mjs parses it the same
 *  way and the build compares the two readings. */
export function parseLayoutNamesSource(src: string): Record<string, LayoutWords> {
  const at = src.search(/^LAYOUT_NAMES = \{/m);
  if (at < 0) throw new Error('api/_lib/layout_names.py: LAYOUT_NAMES not found');
  return JSON.parse(src.slice(at + 'LAYOUT_NAMES = '.length)) as Record<string, LayoutWords>;
}

/** {layout id: {en, de, lt, hu}} of every layout any style takes: the legacy ids that old orders carry and the v3 ones. */
export const LAYOUT_NAMES: Readonly<Record<string, LayoutWords>> = parseLayoutNamesSource(LAYOUT_NAMES_SOURCE);
/** Every layout id that has a word, in the order of the file. */
export const LAYOUT_IDS: readonly string[] = Object.keys(LAYOUT_NAMES);

export const isLayout = (v: unknown): v is string => typeof v === 'string' && Object.prototype.hasOwnProperty.call(LAYOUT_NAMES, v);

/** The word for a layout in a language ("Side by side", "Nebeneinander", "Greta", "Egymás mellett"); any language this does not know reads
 *  English, an id with no word gives `fallback` (api/_lib/catalogue.py layout_name: the same rule; the order page passes the raw id). */
export function layoutName(lang: string, id: string, fallback = ''): string {
  if (!isLayout(id)) return fallback;
  const row = LAYOUT_NAMES[id];
  return (LAYOUT_LANGS as readonly string[]).includes(lang) ? row[lang as (typeof LAYOUT_LANGS)[number]] : row.en;
}
