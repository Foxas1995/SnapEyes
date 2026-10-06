// The test of the landing's release gate (scripts/landing_gate.mjs): deliberate defects, each of which must make a PRODUCTION build fail, and honest pages that must pass.
//
//   node scripts/check_landing_gate_defects.mjs [--only <name>[,<name>...]] [--no-build] [--verbose] [--json <file>]      (npm run check:gate)
//
// The cases run in a throw-away COPY of the tree (src, scripts and the root files are copied, api, public, assets, suites and node_modules are junctions to the
// originals, which no case touches), so a defect never lands in the working tree and another job editing the tree at the same time cannot meet one. For each case the
// files to edit are reset from the original, edited, and then
//   1. the gate alone (`node scripts/check_landing_assets.mjs` in the copy) runs with VERCEL_ENV=production: the case says whether it must pass or fail and which words its message
//      must hold, so a defect is caught by the RIGHT rule and not by some other check of the build;
//   2. the real production build (`vite build`, VERCEL_ENV=production, into a scratch folder outside the project) runs: it must fail for a defect, pass for an honest page.
// A last case shows the other half of the policy: the same defect in a PREVIEW build is only a notice (exit 0).
// It is not part of `npm run build` (a build per case, about 15 seconds each, three at a time never) and not of the guard suites; run it when the gate, the tile
// component, the price table or the tile table change. Everything is local: no network, no key, no model.
import { spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, rmSync, statSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (n) => (args.includes(n) ? args[args.indexOf(n) + 1] : null);
const only = opt('--only')?.split(',') ?? null;
const noBuild = args.includes('--no-build');
const jsonOut = opt('--json');

const TILES = 'src/landing/tileStyle.ts';
const TILE = 'src/landing/StyleTile.tsx';
const TABLE = 'src/landing/PriceTable.tsx';

/** A case: edits (file, from, to; `from` must be in the file exactly once), what the gate must do (pass or fail, with the words its message holds) and what the build must do. */
const CASES = [
  { name: 'baseline', note: 'the tree as it is: the non-live tiles say Soon, so a production build passes', edits: [], gate: 'pass', build: 'pass' },
  {
    name: 'planned-style tile says Soon',
    note: 'a tile that stands for a style with no engine yet (Reflection, planned) is fine while it says Soon: the production build passes',
    edits: [{ file: TILES, from: "duo_clean: { id: 'duo.clean', eyes: 2 }", to: "duo_clean: { id: 'duo.reflection', eyes: 2 }" }],
    gate: 'pass', build: 'pass',
  },
  {
    name: 'tile ignores the catalogue',
    note: 'a tile of a style that is not live prints a price and no Soon chip',
    edits: [{ file: TILE, from: "const forSale = state.sale === 'sale';", to: 'const forSale = true;' }],
    gate: 'fail', words: ['cannot be bought', 'does not say Soon', 'prints a price'], build: 'fail',
  },
  {
    name: 'tile without the Soon chip',
    note: 'a tile of a style that is not live says nothing: no Soon, no price',
    edits: [{ file: TILE, from: '<span className="lp-soon">{c.styles.soonTag}</span>', to: 'null' }],
    gate: 'fail', words: ['cannot be bought', 'does not say Soon'], build: 'fail',
  },
  {
    name: 'price row prices what cannot be bought',
    note: 'the price table prints the price of two eyes while no style can be bought for two eyes',
    edits: [{ file: TABLE, from: 'value={cat.eyes.includes(2) ? gate(p.price2) : soon}', to: 'value={gate(p.price2)}' }],
    gate: 'fail', words: ['the price table row', 'cannot be bought but'], build: 'fail',
  },
  {
    name: 'price row names a style that cannot be bought',
    note: 'the art row of the price table names Radiance, a style at preview',
    edits: [{ file: TABLE, from: 'const names = s.names.length ? s.names : fallback;', to: "const names = ['Radiance'];" }],
    gate: 'fail', words: ['names "Radiance", a style that cannot be bought'], build: 'fail',
  },
  {
    name: 'style name not in the registry (tile table)',
    note: 'a tile that names a style the registry does not have',
    edits: [{ file: TILES, from: "duo_kiss: { id: 'duo.kiss_collision', eyes: 2 }", to: "duo_kiss: { id: 'duo.kiss', eyes: 2 }" }],
    gate: 'fail', words: ['the registry has no style "duo.kiss"', 'stands for no style of the registry'], build: 'fail',
  },
  {
    name: 'tile name from the copy, not the registry',
    note: 'a tile that prints "Kiss", the landing\'s old word, instead of the registry\'s "Kiss Collision"',
    edits: [{ file: 'src/landing/gallery.ts', from: 'n: tileName(tile.id),', to: "n: tile.id === 'duo_kiss' ? 'Kiss' : tileName(tile.id)," }],
    gate: 'fail', words: ['is called "Kiss"', 'no style name of the registry'], build: 'fail',
  },
  {
    name: 'missing tile picture',
    note: 'a tile whose picture family is not in the manifest',
    edits: [{ file: 'src/landing/assets.data.ts', from: '"file": "duo_kiss_bb"', to: '"file": "duo_kiss_zz"' }],
    gate: 'fail', words: ['a tile picture is missing'], build: 'fail', hard: true,
  },
  {
    name: 'price while ordering is closed',
    note: 'the page treats the catalogue as for sale although the deployment takes no orders',
    edits: [{ file: 'src/shared/catalogue.ts', from: 'return ordersOpen(deploymentOpen, c) ? c : NOTHING_FOR_SALE;', to: 'return c;' }],
    gate: 'fail', words: ['cannot be bought (ordering is closed)'], build: 'fail',
  },
  {
    name: 'group line wrong',
    note: 'a group with nothing for sale says "more styles soon" instead of "ordering for this group opens soon"',
    edits: [{ file: 'src/landing/tileState.ts', from: "return n === 0 ? 'soon' : n < total ? 'more' : null;", to: "return n === 0 ? 'more' : n < total ? 'more' : null;" }],
    gate: 'fail', words: ['adds the line'], build: 'fail',
  },
  {
    name: 'hero price while nothing can be bought',
    note: 'the hero prints "Digital file from ..." although no style can be bought for one eye',
    edits: [{ file: 'src/landing/heroPrice.ts', from: 'held: pending || lowest === null', to: 'held: pending' }],
    gate: 'fail', words: ['no style can be bought for one eye but the hero says'], build: 'fail',
  },
  {
    name: 'the same defect in a preview build',
    note: 'only a notice in a preview build (exit 0, the message is printed); the production build of the same tree fails',
    edits: [{ file: TILE, from: "const forSale = state.sale === 'sale';", to: 'const forSale = true;' }],
    env: { VERCEL_ENV: 'preview' }, gate: 'notice', words: ['RELEASE GATE'], build: 'pass',
  },
];

const scratch = mkdtempSync(join(tmpdir(), 'snapeyes_gate_defects_'));
const WORK = join(scratch, 'tree');
const JUNCTIONS = ['api', 'assets', 'public', 'suites', 'node_modules'];
const SKIP = new Set(['.git', 'dist', 'src', 'scripts', ...JUNCTIONS]);

/** The copy: src and scripts as they are now, every file at the root, a junction for each big read-only folder. */
function makeWorkTree() {
  mkdirSync(WORK, { recursive: true });
  cpSync(join(ROOT, 'src'), join(WORK, 'src'), { recursive: true });
  cpSync(join(ROOT, 'scripts'), join(WORK, 'scripts'), { recursive: true });
  for (const n of readdirSync(ROOT)) if (!SKIP.has(n) && statSync(join(ROOT, n)).isFile()) cpSync(join(ROOT, n), join(WORK, n));
  for (const n of JUNCTIONS) if (existsSync(join(ROOT, n))) symlinkSync(realpathSync(join(ROOT, n)), join(WORK, n), 'junction');
}

function run(cmd, cmdArgs, env) {
  const r = spawnSync(cmd, cmdArgs, { cwd: WORK, env: { ...process.env, ...env }, encoding: 'utf8', maxBuffer: 64 << 20 });
  return { code: r.status ?? 1, out: `${r.stdout ?? ''}\n${r.stderr ?? ''}` };
}

const touched = new Set();
/** Put the files a case edited back as they are in the real tree (the copy is only ever edited here). */
function restore() {
  for (const file of touched) cpSync(join(ROOT, file), join(WORK, file));
  touched.clear();
}
process.on('exit', () => rmSync(scratch, { recursive: true, force: true }));
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => process.exit(130));

function apply(edits) {
  for (const e of edits) {
    const p = join(WORK, e.file);
    touched.add(e.file);
    const text = readFileSync(p, 'utf8');
    const crlf = text.includes('\r\n');
    const from = crlf ? e.from.replace(/\n/g, '\r\n') : e.from;
    const to = crlf ? e.to.replace(/\n/g, '\r\n') : e.to;
    const n = text.split(from).length - 1;
    if (n !== 1) throw new Error(`${e.file}: expected the text to edit exactly once, found it ${n} times: ${e.from.slice(0, 80)}`);
    writeFileSync(p, text.replace(from, () => to));
  }
}

makeWorkTree();
const results = [];
let bad = 0;
const vite = join(WORK, 'node_modules', 'vite', 'bin', 'vite.js');
for (const c of CASES) {
  if (only && !only.includes(c.name)) continue;
  const env = { VERCEL_ENV: 'production', LANDING_GATE: '', ...(c.env ?? {}) };
  const row = { name: c.name, gate: '', build: '', ok: true, notes: [] };
  try {
    apply(c.edits);
    const g = run(process.execPath, ['scripts/check_landing_assets.mjs'], env);
    if (args.includes('--verbose')) console.log(`--- ${c.name}: the gate says (exit ${g.code})` + String.fromCharCode(10) + g.out.trim().slice(0, 3000));
    const holds = (c.words ?? []).filter((w) => !g.out.includes(w));
    if (c.gate === 'pass') { row.gate = g.code === 0 && !/RELEASE GATE/.test(g.out) ? 'passes' : 'FAILS'; if (row.gate === 'FAILS') row.ok = false; }
    else if (c.gate === 'fail') {
      row.gate = g.code !== 0 ? 'fails' : 'PASSES';
      if (g.code === 0) row.ok = false;
      if (holds.length) { row.ok = false; row.notes.push(`message lacks: ${holds.join(' | ')}`); }
    } else {
      row.gate = g.code === 0 && /RELEASE GATE/.test(g.out) ? 'notice only' : 'WRONG';
      if (row.gate === 'WRONG') row.ok = false;
      if (holds.length) { row.ok = false; row.notes.push(`message lacks: ${holds.join(' | ')}`); }
    }
    if (c.hard && c.gate === 'fail') {
      // a missing picture is an error in every build, not a matter of promises
      const l = run(process.execPath, ['scripts/check_landing_assets.mjs'], { VERCEL_ENV: 'preview', LANDING_GATE: '' });
      if (l.code === 0) { row.ok = false; row.notes.push('a missing picture passed in a preview build'); }
    }
    if (!noBuild) {
      const out = join(scratch, `dist-${c.name.replace(/[^a-z0-9]+/gi, '-')}`);
      const b = run(process.execPath, [vite, 'build', '--outDir', out, '--emptyOutDir'], env);
      if (args.includes('--verbose')) console.log(`--- ${c.name}: the build says (exit ${b.code})` + String.fromCharCode(10) + b.out.trim().slice(-2500));
      row.build = b.code === 0 ? 'passes' : 'fails';
      if ((c.build === 'pass') !== (b.code === 0)) { row.ok = false; row.build = c.build === 'pass' ? 'FAILS' : 'PASSES'; row.notes.push(b.out.split('\n').filter((l) => /error|failed|RELEASE GATE/i.test(l)).slice(0, 3).join(' / ').slice(0, 300)); }
      rmSync(out, { recursive: true, force: true });
    }
  } catch (e) {
    row.ok = false;
    row.notes.push(e instanceof Error ? e.message : String(e));
  } finally {
    restore();
  }
  if (!row.ok) bad += 1;
  results.push(row);
  console.log(`${row.ok ? 'ok  ' : 'FAIL'} ${c.name.padEnd(46)} gate ${row.gate.padEnd(11)} build ${(row.build || '-').padEnd(7)} ${row.notes.join(' ; ')}`);
}
if (jsonOut) writeFileSync(jsonOut, JSON.stringify(results, null, 2));
console.log(`${results.length - bad} of ${results.length} cases as expected (each ran in a copy: the working tree was not touched)`);
process.exit(bad ? 1 : 0);
