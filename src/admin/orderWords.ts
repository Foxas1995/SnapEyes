// The customer's own words on an order, as the order detail page prints them (the paid record's spec). WP12 made the names of every new order a LIST (one name per
// eye: api/_lib/words.py names_list); an order made before that, and a recorded spec of the old form, keeps one text ("Anna;Max"). The page reads both.

/** "Anna, Max" for a list of names, the text itself for an old order, '' for none (never "[object Object]", never a Python list). */
export function namesText(v: unknown): string {
  if (Array.isArray(v)) return v.filter((x): x is string => typeof x === 'string' && x.trim() !== '').map((x) => x.trim()).join(', ');
  return typeof v === 'string' ? v.trim() : '';
}
