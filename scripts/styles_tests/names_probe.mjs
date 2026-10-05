// Loads src/try/names.ts through Vite's module runner (as scripts/check_texts.mjs loads the page code) and answers the questions of test_picker.py:
// JSON on stdin ({codes: [code points], strings: [texts]}), JSON on stdout. Run from the repository root.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const require = createRequire(join(root, 'package.json'));
const { runnerImport } = await import(pathToFileURL(require.resolve('vite')).href);
const { module: N } = await runnerImport(join(root, 'src', 'try', 'names.ts'), { configFile: false, logLevel: 'silent', root });
const req = JSON.parse(readFileSync(0, 'utf8'));
const out = { limits: { NAME_MAX: N.NAME_MAX, NAMES_TOTAL_MAX: N.NAMES_TOTAL_MAX, DATE_MAX: N.DATE_MAX, FAMILY_MAX: N.FAMILY_MAX }, family_layouts: [...N.FAMILY_NAME_LAYOUTS] };
if (req.codes) out.unsupported = req.codes.map((c) => N.unsupportedChars(String.fromCodePoint(c)));
if (req.strings) {
  out.clean = req.strings.map((s) => N.cleanText(s));
  out.split = req.strings.map((s) => N.splitNames(s));
  out.unsupported_strings = req.strings.map((s) => N.unsupportedChars(s));
}
process.stdout.write(JSON.stringify(out));
