// The Python files the pages read as text, as the bundle carries them. src/shared/styles.ts and src/shared/layouts.ts import
// api/_lib/styles_registry.py and api/_lib/layout_names.py with Vite's ?raw and parse their constants and their JSON literal; every page,
// the landing too, ships that text. Their docstrings and comments are written for the people who change the files and for the server
// (they say what each field means and why), never read by a page: the build (vite.config.ts pySourceSlim) hands the pages each file
// without its module docstring, its comment lines and its blank lines, and with its literal in compact JSON. Nothing a page reads changes:
// slimPySource keeps every NAME = value line as it is, throws when the head of the file holds anything else, and proves that the first
// line of every name is the same in both texts and that the literal parses to the same value. The server, the build's checks, the
// tests and the dev tools read the files themselves. 2026-10-20: about 3.1 kB (the registry) and 1.4 kB (the layout words) of gzip off
// the landing's JavaScript (scripts/check_budget.mjs). The files' own rules (one line per constant, the literal ends the file) are
// what make this safe; scripts/check_styles.mjs enforces them.

/** The files the pages import as text and the build slims, with the name of the literal that ends each. */
// 2026-10-28: and the three files of the prints (src/shared/prints.ts: the offer, the rate table, the words of the products and the countries)
export const SLIM_FILES = {
  'api/_lib/styles_registry.py': 'STYLES', 'api/_lib/layout_names.py': 'LAYOUT_NAMES',
  'api/_lib/print_offer.py': 'PRINT_OFFER', 'api/_lib/print_rates.py': 'PRINT_RATES', 'api/_lib/print_names.py': 'PRINT_NAMES',
};

const CONST_LINE = /^([A-Z_][A-Z0-9_]*) = (\S.*)$/;

/** The text of a Python file of SLIM_FILES as the pages get it: the NAME = value lines of its head and its literal in compact JSON.
 *  Throws (and so stops the build) when the file does not have the shape the pages' readers expect or a reading would differ. */
export function slimPySource(src, file, literal) {
  const head = new RegExp(`^${literal} = \\{`, 'm');
  const at = src.search(head);
  if (at < 0) throw new Error(`${file}: ${literal} not found`);
  const lines = src.slice(0, at).split(/\r?\n/);
  const keep = [];
  let doc = null;              // the quote of the open module docstring
  let seenDoc = false;
  for (const l of lines) {
    if (doc) {
      if (l.includes(doc)) {
        if (l.trimEnd().slice(-3) !== doc) throw new Error(`${file}: text after the end of the module docstring: "${l.slice(0, 60)}"`);
        doc = null;
      }
      continue;
    }
    const t = l.trim();
    if (t === '' || t.startsWith('#')) continue;
    if (!seenDoc && !keep.length && (t.startsWith('"""') || t.startsWith("'''"))) {
      seenDoc = true;
      const q = t.slice(0, 3);
      const rest = t.slice(3);
      if (!rest.includes(q)) doc = q;
      else if (rest.trimEnd().slice(-3) !== q) throw new Error(`${file}: text after the end of the module docstring: "${l.slice(0, 60)}"`);
      continue;
    }
    if (!CONST_LINE.test(l)) throw new Error(`${file}: "${l.slice(0, 60)}" is not a line NAME = value (the pages' readers expect only those before ${literal})`);
    keep.push(l);
  }
  if (doc) throw new Error(`${file}: the module docstring is not closed before ${literal}`);
  const value = JSON.parse(src.slice(at + `${literal} = `.length));
  const slim = `${keep.map((l) => `${l}\n`).join('')}${literal} = ${JSON.stringify(value)}\n`;
  // what any reader of the pages finds: the first line of each name (a docstring line that looked like one would have been found first)
  const first = (text) => {
    const seen = new Map();
    for (const l of text.split(/\r?\n/)) {
      const m = CONST_LINE.exec(l);
      if (m && !seen.has(m[1])) seen.set(m[1], l);
    }
    return seen;
  };
  const a = first(src);
  const b = first(slim);
  for (const [name, l] of b) if (name !== literal && a.get(name) !== l) throw new Error(`${file}: the first line of ${name} would read "${a.get(name)}" in the file and "${l}" in the bundle`);
  for (const [name] of a) if (!b.has(name)) throw new Error(`${file}: the bundle would lose the line of ${name}`);
  if (JSON.stringify(JSON.parse(slim.slice(slim.search(head) + `${literal} = `.length))) !== JSON.stringify(value)) throw new Error(`${file}: ${literal} reads differently`);
  return slim;
}
