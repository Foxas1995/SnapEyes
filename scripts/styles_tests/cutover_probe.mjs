// Loads the page code that reads the registry through Vite's module runner (as picker_probe.mjs does) and answers the questions of test_cutover.py: what the PAGES make of
// the cutover (the effective default, the stage a page may assume before the server answers, the landing's list of one-eye styles, the fallback catalogue, the reading of a
// server catalogue) and what the build's cutover check (scripts/check_styles.mjs item 14) says of registries that break the rule. JSON on stdin, JSON on stdout.
// Run from the repository root.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = process.cwd();
const require = createRequire(join(root, 'package.json'));
const { runnerImport } = await import(pathToFileURL(require.resolve('vite')).href);
const load = async (p) => (await runnerImport(join(root, p), { configFile: false, logLevel: 'silent', root })).module;
const S = await load('src/shared/styles.ts');
const CAT = await load('src/shared/catalogue.ts');
const MKT = await load('src/shared/markets.ts');
const CK = await load('scripts/check_styles.mjs');
const SRC = await load('scripts/styles_source.mjs');
const LP = await load('src/landing/priceText.ts');
const TILES = await load('src/landing/tileStyle.ts');
const GAL = await load('src/landing/assets.data.ts');
const req = JSON.parse(readFileSync(0, 'utf8'));

const reg = SRC.parseRegistrySource(readFileSync(join(root, 'api', '_lib', 'styles_registry.py'), 'utf8'));
const out = {
  effectiveDefault: S.EFFECTIVE_DEFAULT,
  defaultStyle: S.DEFAULT_STYLE,
  fileEffectiveDefault: reg.effectiveDefault,
  buildStages: Object.fromEntries(S.STYLE_IDS.map((id) => [id, Array.from({ length: 8 }, (_, i) => S.buildStage(id, i + 1))])),
  landing: S.landingStyles().map((s) => s.id),
  fallback: CAT.fallbackCatalogue(),
  server: CAT.readCatalogue(req.server),
  guard: [],
  // what the landing makes of a GET /api/checkout answer, by the page's own functions (src/landing/ordering.ts: ordersOpen over the deployment's "open" and the catalogue it read, the
  // fallback when the answer has none, and the SALE catalogue, which is empty while ordering is closed; Hero.tsx: fromOf over the one-eye styles for sale; PriceTable.tsx: the class rows
  // and severalMax; StyleTile.tsx: liveFor by the tile table), in the euro market with the standard ladder
  landingReading: (req.answers ?? []).map((a) => {
    const cat = CAT.readCatalogue(a) ?? CAT.fallbackCatalogue();
    const deploymentOpen = a.ok !== false && a.open === true;
    const open = CAT.ordersOpen(deploymentOpen, cat);
    const sale = open ? cat : { max: 0, styles: [], one: [], eyes: [], by: {} };      // src/landing/ordering.ts: what can be bought right now
    const lp = LP.landingPrices(MKT.priceList('eu'), 'eu', 'en');
    const tiles = [...GAL.GALLERY.one, ...GAL.GALLERY.two, ...GAL.GALLERY.family];
    return {
      deploymentOpen,
      open,
      from: lp.fromOf(sale.one),
      rows: { black: sale.one.some((id) => S.priceClass(id) === 'black'), art: sale.one.some((id) => S.priceClass(id) === 'art') },
      max: cat.max,
      several: CAT.severalMax(sale),
      eyes: sale.eyes,
      forSale: tiles.filter((t) => CAT.liveFor(sale, TILES.TILE_STYLE[t.id].id, TILES.TILE_STYLE[t.id].eyes)).map((t) => t.id),
      texts: { black: lp.black, art: lp.art, from: lp.from },
    };
  }),
};
for (const m of req.mutations ?? []) {
  const copy = JSON.parse(JSON.stringify(reg));
  if ('effectiveDefault' in m) copy.effectiveDefault = m.effectiveDefault;
  if ('defaultStyle' in m) copy.defaultStyle = m.defaultStyle;
  for (const d of Object.values(copy.styles)) {          // allV3 and allLegacy set a whole block at once (the state before the cutover is "lab" and "live")
    if (m.allV3 && d.legacy === 0 && d.stage !== 'planned') { d.stage = m.allV3; d.stage_by_eyes = {}; }
    if (m.allLegacy && d.legacy === 1) d.stage = m.allLegacy;
  }
  for (const [id, st] of Object.entries(m.stages ?? {})) copy.styles[id].stage = st;
  for (const [id, by] of Object.entries(m.stagesByEyes ?? {})) copy.styles[id].stage_by_eyes = by;
  const problems = [];
  CK.checkCutover(copy, problems);
  out.guard.push({ name: m.name, problems });
}
process.stdout.write(JSON.stringify(out));
