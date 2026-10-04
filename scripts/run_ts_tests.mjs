// The page-code tests: every `*.test.ts` under src/ and under suites/ts/ (or the files named on the command line), run from the
// repository root:   node scripts/run_ts_tests.mjs [file.test.ts ...]        (suites/run_main.sh runs it as the entry "ts")
//
// A test file is one of two kinds:
//   * a module that exports `run()`, which returns a list of [name, ok, detail?] and prints nothing (the checkout and
//     multi-eye page code in suites/ts/): loaded through Vite's module runner, so the page's TypeScript and its imports
//     (`../../src/...`) are compiled the way the build compiles them;
//   * a file that imports `node:test` (the reveal maths of the v3 work): run by `node --test` (Node strips the types), its
//     counts read from the TAP report.
// Every check prints one line, "PASS name" or "FAIL name   <- detail", then "N of M passed". The exit code is 1 on any failure
// and also when no test file was found: an empty run is never green. Vite comes from the repository's node_modules.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runnerImport } from 'vite';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const SEARCH = ['src', path.join('suites', 'ts')];

function findTests(dir, acc = []) {
  let names = [];
  try { names = readdirSync(dir); } catch { return acc; }
  for (const n of names.sort()) {
    if (n === 'node_modules' || n.startsWith('.')) continue;
    const p = path.join(dir, n);
    if (statSync(p).isDirectory()) findTests(p, acc);
    else if (n.endsWith('.test.ts')) acc.push(p);
  }
  return acc;
}

const given = process.argv.slice(2);
const files = (given.length ? given.map((f) => path.resolve(f)) : SEARCH.flatMap((d) => findTests(path.join(root, d))));
const rel = (f) => path.relative(root, f).split(path.sep).join('/');

let total = 0;
let bad = 0;
const line = (ok, name, detail) => {
  total++;
  if (!ok) bad++;
  console.log((ok ? 'PASS ' : 'FAIL ') + name + (ok ? '' : `   <- ${detail ?? ''}`));
};

if (!files.length) {
  console.log('FAIL no *.test.ts found under src/ or suites/ts/   <- an empty run is not a green one');
  console.log('\n0 of 0 passed');
  process.exit(1);
}

for (const file of files) {
  const text = readFileSync(file, 'utf8');
  if (/from\s+['"]node:test['"]/.test(text)) {
    const r = spawnSync(process.execPath, ['--test', '--test-reporter=tap', file], { cwd: root, encoding: 'utf8' });
    const pass = Number(/^# pass (\d+)/m.exec(r.stdout)?.[1] ?? 0);
    const fail = Number(/^# fail (\d+)/m.exec(r.stdout)?.[1] ?? 0);
    line(r.status === 0 && fail === 0 && pass > 0, `${rel(file)}: ${pass} node:test checks`, (r.stdout + r.stderr).slice(-600));
    continue;
  }
  try {
    const { module } = await runnerImport(file, { configFile: false, logLevel: 'silent' });
    if (typeof module.run !== 'function') { line(false, rel(file), 'exports no run()'); continue; }
    for (const [name, ok, detail] of await module.run()) line(Boolean(ok), name, detail);
  } catch (e) {
    line(false, `${rel(file)} (could not run)`, e instanceof Error ? e.message : String(e));
  }
}
console.log(`\n${total - bad} of ${total} passed`);
process.exit(bad ? 1 : 0);
