// The Python files the pages read as text reach the bundle slimmed (vite.config.ts pySourceSlim, scripts/py_source_slim.mjs, 2026-10-20: the landing's
// JavaScript was at +7,873 B of its +8,000 B hard stop and the registry's docstring was 3.1 kB of it). This runner loads the files with Vite's own ?raw
// (configFile: false, so the plugin is not in the way): the pages' own readers must read the same values from the slim text as from the file.
import REGISTRY from '../../api/_lib/styles_registry.py?raw';
import LAYOUTS from '../../api/_lib/layout_names.py?raw';
import { SLIM_FILES, slimPySource } from '../../scripts/py_source_slim.mjs';
import { parseStylesSource } from '../../src/shared/styles';
import { parseLayoutNamesSource } from '../../src/shared/layouts';
import OFFER from '../../api/_lib/print_offer.py?raw';
import RATES from '../../api/_lib/print_rates.py?raw';
import NAMES from '../../api/_lib/print_names.py?raw';
import { parseLiteral } from '../../src/shared/prints';

type Row = [string, boolean, string?];

const throws = (f: () => unknown): string => {
  try {
    f();
    return '';
  } catch (e) {
    return e instanceof Error ? e.message : String(e);
  }
};

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const reg = slimPySource(REGISTRY, 'api/_lib/styles_registry.py', 'STYLES');
  const lay = slimPySource(LAYOUTS, 'api/_lib/layout_names.py', 'LAYOUT_NAMES');

  check('the slim registry reads as the file does for a page: the schema, the plates version, the default style, the effective default and every style, field for field and in order',
    JSON.stringify(parseStylesSource(reg)) === JSON.stringify(parseStylesSource(REGISTRY)) && Object.keys(parseStylesSource(reg).styles).join() === Object.keys(parseStylesSource(REGISTRY).styles).join(),
    reg.slice(0, 200));
  check('the slim layout words read as the file does: every layout id and its four words, in order',
    JSON.stringify(parseLayoutNamesSource(lay)) === JSON.stringify(parseLayoutNamesSource(LAYOUTS)), lay.slice(0, 200));
  // 2026-10-28: the three files of the prints are slimmed too (the offer, the rate table, the words); each reads back to the same literal
  const printSlim = ([['api/_lib/print_offer.py', OFFER, 'PRINT_OFFER'], ['api/_lib/print_rates.py', RATES, 'PRINT_RATES'], ['api/_lib/print_names.py', NAMES, 'PRINT_NAMES']] as const)
    .map(([rel, src, name]) => {
      const t = slimPySource(src, rel, name);
      return !t.includes('"""') && !/^\s*#/m.test(t) && !/\n\s*\n/.test(t) && t.length < src.length && JSON.stringify(parseLiteral(t, name)) === JSON.stringify(parseLiteral(src, name));
    });
  check('the slim texts carry no docstring, no comment and no blank line, and the build slims exactly these two files (the registry to under half its size)'
    + ' - 2026-10-28: and the three files of the prints, each read back to the same literal',
    ![reg, lay].some((t) => t.includes('"""') || /^\s*#/m.test(t) || /\n\s*\n/.test(t)) && reg.length * 2 < REGISTRY.length && lay.length < LAYOUTS.length
    && Object.keys(SLIM_FILES).join() === 'api/_lib/styles_registry.py,api/_lib/layout_names.py,api/_lib/print_offer.py,api/_lib/print_rates.py,api/_lib/print_names.py'
    && printSlim.every(Boolean), `${reg.length} of ${REGISTRY.length}, ${lay.length} of ${LAYOUTS.length}, ${printSlim.join()}`);
  const head = '# -*- coding: utf-8 -*-\n"""Doc.\n"""\n';
  const lit = 'STYLES = {"a": {"b": 1}}\n';
  const bad = {
    statement: throws(() => slimPySource(`${head}import os\nSTYLES_SCHEMA = 1\n${lit}`, 'x.py', 'STYLES')),
    unclosed: throws(() => slimPySource(`# c\n"""Doc that never ends\nSTYLES_SCHEMA = 1\n${lit}`, 'x.py', 'STYLES')),
    shadow: throws(() => slimPySource(`"""Doc.\nSTYLES_SCHEMA = 2\n"""\nSTYLES_SCHEMA = 1\n${lit}`, 'x.py', 'STYLES')),
    trailing: throws(() => slimPySource(`${head}STYLES_SCHEMA = 1\n${lit}X = 1\n`, 'x.py', 'STYLES')),
  };
  check('a file that leaves the shape stops the slimming, and so the build: a statement that is not NAME = value, a docstring that never ends, a docstring line a reader '
    + 'would take for a constant, anything after the literal', Object.values(bad).every((m) => m !== '') && slimPySource(`${head}STYLES_SCHEMA = 1\n${lit}`, 'x.py', 'STYLES') === `STYLES_SCHEMA = 1\nSTYLES = {"a":{"b":1}}\n`,
    JSON.stringify(bad));
  return out;
}
