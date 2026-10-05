// The customer's own words on the artwork: a name per eye, an optional date and an optional family name, and the rules that keep them drawable.
// Pure functions, no React and no DOM. The studio writes nothing on the artwork but these (owner rule); the limits and the cleaning are the
// server's (api/_lib/styles/text.py NAME_MAX, NAMES_TOTAL_MAX, DATE_MAX, FAMILY_MAX, clean(), split_names()) and the suite v3picker keeps the two
// sides equal, letter by letter: a letter the artwork font cannot draw would print as an empty box in the delivered file, so the page refuses it
// before checkout (the server's own check is text.unsupported(); this page carries the same list as src/try/nameChars.ts).
import { NAME_FONT_RANGES } from './nameChars';

/** characters in one name (api/_lib/styles/text.py NAME_MAX) */
export const NAME_MAX = 24;
/** characters in all names of one order (NAMES_TOTAL_MAX) */
export const NAMES_TOTAL_MAX = 200;
/** the optional date line (DATE_MAX) */
export const DATE_MAX = 20;
/** the optional family name (FAMILY_MAX) */
export const FAMILY_MAX = 24;
/** the old wire form: one string, the names joined by a semicolon (text.py SEPARATOR); checkout still takes it */
export const NAMES_SEPARATOR = ';';

/** The layouts whose artwork really draws a family name in the hollow of the arrangement. EMPTY today: the collision engine (WP7) records where
 *  the hollow centre of a ring is (scenes.py hollow_centre) but draws no line there, so offering the field would promise text the file lacks.
 *  The field is shown only for a layout listed here; WP7 adds "ring" when its drawer calls text.draw_line. */
export const FAMILY_NAME_LAYOUTS: readonly string[] = [];

const ch = String.fromCharCode;
// control and zero width characters (text.py _CONTROL): out of every customer string
const CONTROL = new RegExp(`[${ch(0)}-${ch(0x1f)}${ch(0x7f)}-${ch(0x9f)}${ch(0x200b)}-${ch(0x200f)}${ch(0x2028)}-${ch(0x202e)}${ch(0x2060)}-${ch(0x2064)}${ch(0xfeff)}]`, 'g');

/** One customer string as it is drawn: NFC, control and zero width characters out, runs of white space one space, trimmed (text.py clean). */
export function cleanText(s: unknown): string {
  if (typeof s !== 'string') return '';
  return s.normalize('NFC').replace(CONTROL, '').replace(/\s+/g, ' ').trim();
}

/** A string kept for typing: control characters out and the semicolon (which separates names on the wire) out, nothing else touched, so a
 *  trailing space typed between two words stays. Cut at max characters (counted in code points, as the server counts). */
export function typed(s: string, max: number): string {
  const t = [...s.replace(/[;\n\r]/g, ' ').replace(CONTROL, '')];
  return t.length > max ? t.slice(0, max).join('') : t.join('');
}

/** The names of an old wire string ("Anna;Max", or one name per line) as a list, empty names dropped (text.py split_names). */
export function splitNames(wire: unknown): string[] {
  if (Array.isArray(wire)) return wire.map(cleanText).filter(Boolean);
  if (typeof wire !== 'string') return [];
  return wire.split(/[;\n]/).map(cleanText).filter(Boolean);
}

const covered = (cp: number): boolean => NAME_FONT_RANGES.some(([a, b]) => cp >= a && cp <= b);

/** The distinct characters of a string, as the drawer sets it (upper case), that the artwork font cannot draw, sorted (text.py unsupported).
 *  Spaces are always fine. [] means the string draws completely. */
export function unsupportedChars(text: string): string[] {
  const bad = new Set<string>();
  for (const c of cleanText(text).toUpperCase()) {
    if (/\s/u.test(c)) continue;
    if (!covered(c.codePointAt(0)!)) bad.add(c);
  }
  return [...bad].sort();
}

export type NameProblem =
  | { code: 'name_long'; eye: number }                    // one name over NAME_MAX
  | { code: 'names_long' }                                // the names together over NAMES_TOTAL_MAX
  | { code: 'glyph'; eye: number; chars: string[]; field?: 'date' | 'family' }   // a letter the font cannot draw (eye 0 and a field: the date or the family name)
  | { code: 'date_long' } | { code: 'family_long' };

/** What is wrong with the words, in the order the form shows them (eye: 1-based position on the artwork). A name is checked as the drawer will set
 *  it, so a name that fits only before cleaning is not a problem and one that does not fit after it is. */
export function problems(names: readonly string[], date = '', family = ''): NameProblem[] {
  const out: NameProblem[] = [];
  const cleaned = names.map(cleanText);
  cleaned.forEach((n, i) => {
    if ([...n].length > NAME_MAX) out.push({ code: 'name_long', eye: i + 1 });
    const bad = unsupportedChars(n);
    if (bad.length) out.push({ code: 'glyph', eye: i + 1, chars: bad });
  });
  if (cleaned.reduce((s, n) => s + [...n].length, 0) > NAMES_TOTAL_MAX) out.push({ code: 'names_long' });
  const d = cleanText(date), f = cleanText(family);
  if ([...d].length > DATE_MAX) out.push({ code: 'date_long' });
  if (unsupportedChars(d).length) out.push({ code: 'glyph', eye: 0, chars: unsupportedChars(d), field: 'date' });
  if ([...f].length > FAMILY_MAX) out.push({ code: 'family_long' });
  if (unsupportedChars(f).length) out.push({ code: 'glyph', eye: 0, chars: unsupportedChars(f), field: 'family' });
  return out;
}

/** The names the server draws: the cleaned, non-empty ones in the order of the eyes (it joins them into one line, "ANNA · MAX"; an empty name
 *  takes no place). The list form of /api/compose. */
export function composeNames(names: readonly string[]): string[] {
  return names.map(cleanText).filter(Boolean);
}

/** The old wire string of checkout (one string, names joined by a semicolon): the form the server reads today and keeps reading. */
export function wireNames(names: readonly string[]): string {
  return composeNames(names).join(NAMES_SEPARATOR);
}

/** The names of eyes in canvas order, by the eyes' ids (a name belongs to its eye: moving, removing and putting an eye back keep it). */
export function namesOf(byId: Readonly<Record<string, string>>, ids: readonly string[]): string[] {
  return ids.map((id) => byId[id] ?? '');
}

/** The names of a saved artwork (a snapshot's string, "Anna;Max") as one entry per eye id, the first name to the first eye. */
export function namesFromWire(wire: unknown, ids: readonly string[]): Record<string, string> {
  const list = typeof wire === 'string' ? wire.split(/[;\n]/).map((s) => typed(s, NAME_MAX)) : [];
  const out: Record<string, string> = {};
  ids.forEach((id, i) => { if (list[i]) out[id] = list[i]; });
  return out;
}

/** Does this layout draw a family name (FAMILY_NAME_LAYOUTS)? */
export const drawsFamilyName = (layout: string): boolean => FAMILY_NAME_LAYOUTS.includes(layout);
