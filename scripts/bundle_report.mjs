// What each Vercel Python function holds, against the byte budget of the v3 plan (a 235 MiB tripwire; the documented limit for
// Python is 500 MB, the old assumption 250 MB).        node scripts/bundle_report.mjs [options]
//
//   (no option)         the files each function bundles, computed here from the repository and vercel.json (see "The model"),
//                       plus the installed size of the Python packages in THIS interpreter (Windows wheels on the development
//                       machine: a floor, not a Linux size), and a Linux range from the plan's factor 1.2 to 1.75
//   --pypi              the Linux wheels PyPI lists for the pinned versions, sized from their zip directories (scripts/bundle_deps.py;
//                       network, about 1 MB in all): the best figure this machine can give without a Linux build
//   --func-dir DIR      measured: the folders DIR/*.func or DIR/api/*.func of a `vercel build` made on Linux (WSL, Docker, a CI job;
//                       never a local Windows build, whose wheels are Windows wheels)
//   --sizes FILE|JSON   measured: {"compose": 143.2, ...} in MiB, typed from the Preview deployment's function list
//   --budget-mb N       the tripwire (default 235)
//   --json              the report as JSON
//   --check             exit 1 when a MEASURED function is over the budget, or when a function bundles a folder that is not
//                       the api folder (a new top-level folder not in excludeFiles would ride into all 11 functions; read WITHOUT
//                       .vercelignore, which may not be honoured by Git deployments: V2), or
//                       when vercel.json and the budget disagree with the function files. Estimates only warn.
//
// The model (what Vercel is believed to bundle; closing steps V1 and V2 of the plan check it on a Preview): every function holds
// the whole deployment minus `excludeFiles` (a glob from the project root) minus `.vercelignore`, plus the installed packages.
// `excludeFiles` is read two ways because its dotfile and matchBase behaviour is not documented: STRICT (a pattern without a slash,
// such as *.json, matches the project root only, dotfiles are not matched by *: the larger bundle) and LOOSE (such a pattern matches
// at any depth, dotfiles included: the smaller one). The files are the ones git tracks plus new ones it does not ignore.
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const MIB = 1048576;
const LINUX_FACTOR = [1.2, 1.75];      // the plan's guess for Linux wheels against the Windows ones, used only without --pypi
const LIMITS = { tripwire: 235, assumed_old: 250, documented_python: 500 };

// ----------------------------------------------------------------------------- globs
function expandBraces(p) {
  const m = /\{([^{}]*)\}/.exec(p);
  if (!m) return [p];
  return m[1].split(',').flatMap((alt) => expandBraces(p.slice(0, m.index) + alt + p.slice(m.index + m[0].length)));
}
function globToRegex(g, dot) {
  let re = '';
  for (let i = 0; i < g.length; i++) {
    const c = g[i];
    if (c === '*') {
      if (g[i + 1] === '*') {
        i++;
        if (g[i + 1] === '/') { i++; re += '(?:[^/]+/)*'; } else re += '.*';
      } else {
        const segStart = i === 0 || g[i - 1] === '/';
        re += (!dot && segStart ? '(?!\\.)' : '') + '[^/]*';
      }
    } else if (c === '?') re += '[^/]';
    else re += c.replace(/[.+^${}()|[\]\\]/g, '\\$&');
  }
  return new RegExp(`^${re}$`);
}
/** A matcher for a brace glob (as in excludeFiles): strict = root-relative, loose = matchBase and dotfiles. */
function matcher(glob, loose) {
  const parts = expandBraces(glob).map((g) => ({ g, re: globToRegex(g, loose), base: loose && !g.includes('/') }));
  return (file) => parts.some(({ re, base }) => re.test(base ? file.slice(file.lastIndexOf('/') + 1) : file));
}
/** .vercelignore lines, gitignore style in the small: `dir/`, `name`, `*.ext`, `path/**`. */
function ignoreMatcher(text) {
  const rules = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => l && !l.startsWith('#')).map((l) => {
    const dir = l.endsWith('/');
    const g = l.replace(/^\/+|\/+$/g, '');
    const anchored = l.startsWith('/') || g.includes('/');
    const re = globToRegex(g, true);
    return (file) => {
      const segs = file.split('/');
      for (let i = 1; i <= segs.length; i++) {
        if (dir && i === segs.length) break;               // `dir/` names folders only: a file of that name is not it
        const sub = anchored ? segs.slice(0, i).join('/') : segs[i - 1];
        if (re.test(sub)) return true;
      }
      return false;
    };
  });
  return (file) => rules.some((r) => r(file));
}

// ----------------------------------------------------------------------------- the files of the deployment
function git(args) {
  const r = spawnSync('git', args, { cwd: root, encoding: 'utf8', maxBuffer: 64 * MIB });
  return r.status === 0 ? r.stdout : null;
}
function deployedFiles() {
  const out = git(['ls-files', '--cached', '--others', '--exclude-standard', '-z']);
  let list;
  if (out !== null) list = out.split('\0').filter(Boolean);
  else {
    list = [];
    const walk = (dir) => {
      for (const n of readdirSync(path.join(root, dir))) {
        if (['node_modules', '.git', '.vercel', '__pycache__'].includes(n)) continue;
        const rel = dir ? `${dir}/${n}` : n;
        if (statSync(path.join(root, rel)).isDirectory()) walk(rel); else list.push(rel);
      }
    };
    walk('');
  }
  const vi = path.join(root, '.vercelignore');
  const ignored = existsSync(vi) ? ignoreMatcher(readFileSync(vi, 'utf8')) : () => false;
  const files = [];    // as deployed if .vercelignore is honoured
  const raw = [];      // the same without it: whether Git deployments honour .vercelignore is open (V2), so --check reads this one
  for (const f of list) {
    if (f.includes('__pycache__') || f.endsWith('.pyc')) continue;
    let bytes;
    try { bytes = statSync(path.join(root, f)).size; } catch { continue; /* a file git lists and the disk lost */ }
    raw.push({ f, bytes });
    if (!ignored(f)) files.push({ f, bytes });
  }
  return { files, raw };
}

// ----------------------------------------------------------------------------- the functions of vercel.json
const vercel = JSON.parse(readFileSync(path.join(root, 'vercel.json'), 'utf8'));
const entries = Object.entries(vercel.functions ?? {}).map(([pat, cfg]) => ({ pat, cfg, re: globToRegex(pat, true) }));
const { files, raw: filesRaw } = deployedFiles();
const functions = files
  .map((x) => x.f)
  .filter((f) => /^api\/[^/_][^/]*\.py$/.test(f) || /^api\/[^_][^/]*\/.*\.py$/.test(f))
  .sort();
const notes = [];
function configFor(fn) {
  const hits = entries.filter((e) => e.re.test(fn));
  const note = `${fn}: ${hits.length} functions patterns match (${hits.map((h) => h.pat).join(', ')}); which one wins is unverified (V2), the longest pattern is read`;
  if (hits.length > 1 && !notes.includes(note)) notes.push(note);
  return hits.sort((a, b) => b.pat.length - a.pat.length)[0] ?? null;
}

function bundle(fn, fileSet = files) {
  const cfg = configFor(fn);
  const ex = cfg?.cfg?.excludeFiles;
  const patterns = Array.isArray(ex) ? `{${ex.join(',')}}` : (ex ?? '');
  const out = {};
  for (const [mode, loose] of [['strict', false], ['loose', true]]) {
    const excl = patterns ? matcher(patterns, loose) : () => false;
    const inc = fileSet.filter((x) => !excl(x.f));
    const top = {};
    for (const x of inc) {
      const t = x.f.includes('/') ? x.f.split('/')[0] : '(root files)';
      top[t] = (top[t] ?? 0) + x.bytes;
    }
    out[mode] = { bytes: inc.reduce((s, x) => s + x.bytes, 0), files: inc.length, top };
  }
  return { fn, pattern: cfg?.pat ?? null, maxDuration: cfg?.cfg?.maxDuration ?? null, exclude: patterns, ...out };
}
const bundles = functions.map((fn) => bundle(fn));
const bundlesRaw = functions.map((fn) => bundle(fn, filesRaw));    // without .vercelignore: the reading that --check holds to

// ----------------------------------------------------------------------------- the dependencies
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const value = (n) => (args.includes(n) ? args[args.indexOf(n) + 1] : null);
const budget = Number(value('--budget-mb') ?? LIMITS.tripwire);
const python = process.env.PYTHON || 'python';
function deps(how) {
  const r = spawnSync(python, [path.join(root, 'scripts', 'bundle_deps.py'), how], { cwd: root, encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' }, maxBuffer: 32 * MIB });
  try {
    const v = JSON.parse(r.stdout);
    if (v && typeof v === 'object') return v;       // JSON.parse(null) is null, not an error: a missing interpreter must not read as a report
  } catch { /* falls through */ }
  return { how, error: (r.error ? String(r.error.code ?? r.error.message) : r.stderr || r.stdout || 'no output').slice(-300) };
}
const local = deps('local');
const linux = flag('--pypi') ? deps('pypi') : null;

// ----------------------------------------------------------------------------- measured sizes (a Linux build or the dashboard)
function folderBytes(dir) {
  let s = 0;
  for (const n of readdirSync(dir)) {
    const p = path.join(dir, n);
    const st = statSync(p, { throwIfNoEntry: false });
    if (st) s += st.isDirectory() ? folderBytes(p) : st.size;
  }
  return s;
}
const measured = {};
if (value('--func-dir')) {
  const base = path.resolve(value('--func-dir'));
  const dirs = [base, path.join(base, 'api')].filter((d) => existsSync(d));
  for (const d of dirs) for (const n of readdirSync(d)) if (n.endsWith('.func')) measured[n.slice(0, -5)] = folderBytes(path.join(d, n)) / MIB;
  if (!Object.keys(measured).length) notes.push(`--func-dir ${base}: no *.func folder found`);
}
if (value('--sizes')) {
  const raw = value('--sizes');
  const text = existsSync(raw) ? readFileSync(raw, 'utf8') : raw;
  try { for (const [k, v] of Object.entries(JSON.parse(text))) measured[k.replace(/^api\//, '').replace(/\.py$/, '')] = Number(v); } catch { notes.push('--sizes: not valid JSON'); }
}

// ----------------------------------------------------------------------------- the report
const mb = (b) => b / MIB;
const f1 = (x) => x.toFixed(1);
const depsLow = local.error ? null : mb(local.total);
const rows = bundles.map((b) => {
  const name = b.fn.replace(/^api\//, '').replace(/\.py$/, '');
  const lo = mb(b.loose.bytes), hi = mb(b.strict.bytes);
  const est = linux && !linux.error
    ? { low: lo + mb(linux.total), high: hi + mb(linux.total), basis: 'linux wheels from PyPI' }
    : depsLow === null ? null : { low: lo + depsLow * LINUX_FACTOR[0], high: hi + depsLow * LINUX_FACTOR[1], basis: `Windows packages x ${LINUX_FACTOR.join(' to ')}` };
  return { name, files_mib: { loose: lo, strict: hi }, estimate_mib: est, measured_mib: measured[name] ?? null };
});

const report = {
  budget_mib: budget, limits_mb: LIMITS, units: 'MiB (2^20 bytes)', functions: rows.length,
  vercel_json: { patterns: entries.map((e) => e.pat), maxDuration: [...new Set(bundles.map((b) => b.maxDuration))], exclude: bundles[0]?.exclude ?? '' },
  python: { windows_or_local: local.error ? { error: local.error } : { platform: local.platform, python: local.python, total_mib: mb(local.total), dists: local.dists.map((d) => ({ name: d.name, version: d.version, mib: mb(d.bytes) })), notes: local.notes },
            linux: linux ? (linux.error ? { error: linux.error } : { python: linux.python, total_mib: mb(linux.total), dists: linux.dists.map((d) => ({ name: d.name, version: d.version, mib: mb(d.bytes), wheel: d.file })), notes: linux.notes }) : null },
  top_level_included: Object.fromEntries(Object.keys(bundles[0]?.strict.top ?? {}).map((k) => [k, { strict_mib: mb(bundles[0].strict.top[k]), loose_mib: mb(bundles[0].loose.top[k] ?? 0) }])),
  top_level_without_vercelignore: Object.fromEntries(Object.keys(bundlesRaw[0]?.strict.top ?? {}).map((k) => [k, { strict_mib: mb(bundlesRaw[0].strict.top[k]), loose_mib: mb(bundlesRaw[0].loose.top[k] ?? 0) }])),
  rows, notes,
};

const problems = [];
const warnings = [];
const strangeBy = new Map();
// A folder that rides along only because .vercelignore is not read is still a problem: whether Git deployments honour that file
// is open (V2), and excludeFiles is the one that does not depend on it. So the check reads the bundle WITHOUT .vercelignore.
for (const b of bundlesRaw) {
  const strange = Object.keys(b.strict.top).filter((t) => t !== 'api' && t !== '(root files)').join(', ');
  if (strange) strangeBy.set(strange, [...(strangeBy.get(strange) ?? []), b.fn]);
}
for (const [folders, fns] of strangeBy) {
  problems.push(`${fns.length === bundles.length ? `all ${fns.length} functions bundle` : `${fns.join(', ')} bundle`} folder(s) outside api/: ${folders} (add them to excludeFiles in vercel.json; .vercelignore alone is not relied on)`);
}
for (const r of rows) {
  if (r.measured_mib !== null && r.measured_mib > budget) problems.push(`${r.name}: measured ${f1(r.measured_mib)} MiB is over the ${budget} MiB budget`);
  else if (r.measured_mib === null && r.estimate_mib && r.estimate_mib.high > budget) warnings.push(`${r.name}: the estimate reaches ${f1(r.estimate_mib.high)} MiB (${r.estimate_mib.basis}), over the ${budget} MiB budget`);
}
if (new Set(bundles.map((b) => b.maxDuration)).size > 1) warnings.push('the functions do not share one maxDuration');
report.problems = problems; report.warnings = warnings;

if (flag('--json')) console.log(JSON.stringify(report, null, 1));
else {
  console.log(`Functions: ${rows.length} (${bundles[0]?.pattern ?? 'no functions entry'}, maxDuration ${report.vercel_json.maxDuration.join('/')} s)`);
  console.log(`Budget ${budget} MiB (documented limit for Python ${LIMITS.documented_python} MB, the old assumption ${LIMITS.assumed_old} MB). Units: MiB.\n`);
  console.log('Files bundled in each function (strict = larger, loose = smaller reading of excludeFiles):');
  const top = report.top_level_included;
  for (const [k, v] of Object.entries(top)) console.log(`  ${k.padEnd(14)} ${f1(v.strict_mib).padStart(7)} strict ${f1(v.loose_mib).padStart(7)} loose`);
  console.log('\nPython packages:');
  if (local.error) console.log(`  this interpreter: ${local.error}`);
  else console.log(`  this interpreter (${local.platform}, Python ${local.python}): ${f1(mb(local.total))} MiB in ${local.dists.length} packages: ${local.dists.map((d) => `${d.name} ${f1(mb(d.bytes))}`).join(', ')}`);
  if (linux) {
    if (linux.error) console.log(`  Linux wheels: ${linux.error}`);
    else console.log(`  Linux wheels (Python ${linux.python}, manylinux x86_64, from PyPI): ${f1(mb(linux.total))} MiB in ${linux.dists.length} packages: ${linux.dists.map((d) => `${d.name} ${f1(mb(d.bytes))}`).join(', ')}`);
  } else console.log('  Linux wheels: not read (run with --pypi)');
  console.log('\nPer function (MiB):');
  const groups = new Map();
  for (const r of rows) {
    const key = JSON.stringify([r.files_mib, r.estimate_mib, r.measured_mib]);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r);
  }
  for (const g of groups.values()) {
    const r = g[0];
    const names = g.length > 3 ? `${g.length} functions (${g.map((x) => x.name).join(', ')})` : g.map((x) => x.name).join(', ');
    const est = r.estimate_mib ? `estimate ${f1(r.estimate_mib.low)} to ${f1(r.estimate_mib.high)} (${r.estimate_mib.basis})` : 'no estimate (packages unreadable)';
    const meas = r.measured_mib !== null ? `MEASURED ${f1(r.measured_mib)}` : 'not measured';
    console.log(`  ${names}\n    files ${f1(r.files_mib.loose)} to ${f1(r.files_mib.strict)}; ${est}; ${meas}`);
  }
  if (Object.keys(measured).length === 0) console.log('\nNo measured size yet: the numbers above are estimates. Close V1 with --func-dir (a Linux build) or --sizes (the Preview function list).');
  for (const n of notes) console.log(`note: ${n}`);
  for (const w of warnings) console.log(`WARNING: ${w}`);
  for (const p of problems) console.log(`PROBLEM: ${p}`);
}
if (flag('--check') && problems.length) process.exit(1);
