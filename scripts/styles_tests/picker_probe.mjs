// Loads src/try/picker.ts through Vite's module runner (as names_probe.mjs loads names.ts) and answers the question of test_picker.py section 5: what the page's
// buy card does (buyState) for the tile rows the server sends. JSON on stdin ({cases: [{n, row, look}]}), JSON on stdout ({kinds: [...]}). Run from the repository root.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const require = createRequire(join(root, 'package.json'));
const { runnerImport } = await import(pathToFileURL(require.resolve('vite')).href);
const { module: P } = await runnerImport(join(root, 'src', 'try', 'picker.ts'), { configFile: false, logLevel: 'silent', root });
const req = JSON.parse(readFileSync(0, 'utf8'));
const kinds = req.cases.map((c) => {
  // the row goes through the page's own reading of a compose reply, as it does in the browser
  const cat = P.parseCatalog({ tiles: [c.row], eyes: [] }, 'k', c.n);
  const tile = cat && cat.tiles[0];
  if (!tile) return 'unparsed';
  const look = P.lookOf(tile, c.look ?? null);
  return P.buyState({ n: c.n, tiles: [tile], selected: tile, look }).kind;
});
process.stdout.write(JSON.stringify({ kinds }));
