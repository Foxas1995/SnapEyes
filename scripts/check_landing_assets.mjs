// The check of the landing page's pictures (run by vite.config.ts before every build; `npm run check:assets` runs it alone).
// public/assets/landing and src/landing/assets.ts (the manifest, written by scripts/build_landing_assets.py) must agree:
//   1. every picture of the manifest exists under its content hashed name, its bytes hash to the name, its size in bytes and
//      its width and height (read from the webp header) are the manifest's;
//   2. no file in public/assets/landing is left out of the manifest (only what the page uses is in the repository), and the
//      manifest is exactly what scripts/landing_assets.json names (its families and extras): nothing unused, nothing missing;
//   3. the budgets: the whole folder, the biggest file, the LCP picture of the first screen (phone, slow 4G: BUILD_PLAN section 5);
//   4. the cache headers: vercel.json gives every picture of the folder and every hashed script and stylesheet of the build
//      "immutable" for a year, and gives nothing that is not hashed (the pages, the pictures of /assets/atelier, the fonts) that;
// and the RELEASE GATE: whether the page can sell what its gallery shows. Each of the 16 tiles of the style gallery stands for a style of the
// registry (api/_lib/styles_registry.py, the one place for style ids and stages) and a number of eyes (src/landing/tileStyle.ts TILE_STYLE); a
// tile is blocked when the engine could never make it: no row, a style the registry does not have, a retired style, an eye count the style does
// not take, or a style that is only planned (no engine behind it). Every other tile is fine whatever its stage: what can be BOUGHT is decided at
// run time (the registry's ceiling per eye count, then the owner's tick in the admin page; src/landing/StyleTile.tsx shows a tile that cannot be
// bought as Soon and prints no price beside it), so the owner's ticks never touch the build. While a tile is blocked the build prints a notice,
// and the build of a PRODUCTION deploy (VERCEL_ENV=production, or LANDING_GATE=strict anywhere) fails: the page must not go live with a tile
// of something the engine cannot make.
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { headersFor } from './lib/static.mjs';
import { loadRegistry, ceilingOf } from './styles_source.mjs';

export const LANDING_DIR = 'public/assets/landing';
const HASH_LEN = 10;
const TOTAL_BUDGET = 10.5e6;       // bytes of all pictures together (9.2 MB today: 163 files)
const FILE_BUDGET = 350e3;         // bytes of any one picture
const HERO_FAMILY = 'm/lounge_acrylic__eye__tight';
const HERO_BUDGET = 38e3;          // the LCP picture the phone fetches (900 px) on slow 4G: the measuring rig (scripts/measure_landing.mjs) shows a cliff of about 100 ms of LCP between a 38.5 and a 39.3 kB file
const HERO_WIDTHS = [900, 1200];   // the 1200 px file is fetched by phones at pixel ratio 3 and 412 px Androids (pixel ratio 2.6 and more), so it gets the same cap
const WIDTH_RE = /^(.*)_(\d+)$/;

function listFiles(dir, acc = []) {
  if (!existsSync(dir)) return acc;
  for (const n of readdirSync(dir)) {
    const p = join(dir, n);
    if (statSync(p).isDirectory()) listFiles(p, acc);
    else acc.push(p);
  }
  return acc;
}

/** Width and height of a webp file from its header (lossy VP8, lossless VP8L, extended VP8X), or null. */
export function webpSize(buf) {
  if (buf.length < 30 || buf.toString('ascii', 0, 4) !== 'RIFF' || buf.toString('ascii', 8, 12) !== 'WEBP') return null;
  const kind = buf.toString('ascii', 12, 16);
  if (kind === 'VP8 ') return { w: buf.readUInt16LE(26) & 0x3fff, h: buf.readUInt16LE(28) & 0x3fff };
  if (kind === 'VP8L') {
    const b = buf.readUInt32LE(21);
    return { w: (b & 0x3fff) + 1, h: ((b >> 14) & 0x3fff) + 1 };
  }
  if (kind === 'VP8X') return { w: (buf.readUIntLE(24, 3)) + 1, h: (buf.readUIntLE(27, 3)) + 1 };
  return null;
}

/** The file names (without extension) a landing_assets.json names, given which names exist (the rule of build_landing_assets.py collect). */
export function usedNames(spec, available) {
  const used = new Set(spec.extras);
  const missing = [];
  const fam = (base, only) => {
    const ws = [...available].map((n) => WIDTH_RE.exec(n)).filter((m) => m && m[1] === base).map((m) => +m[2]).filter((w) => !only || only.includes(w));
    if (!ws.length) missing.push(`no picture for the family ${base}`);
    ws.forEach((w) => used.add(`${base}_${w}`));
  };
  for (const mat of Object.values(spec.stage)) {
    for (const a of Object.values(mat)) {
      fam(a.base);
      if (a.de) fam(a.de);
    }
  }
  for (const g of spec.gallery.groups) {
    for (const it of spec.gallery[g]) {
      for (const k of ['wall', 'wallOwn']) if (it[k]) fam(it[k].base);
      if (it.design) for (const e of spec.gallery.eyes) fam(`art/${it.design}_${e.id}`, [480, 900]);
      else fam(`art/${it.file}`, [480, 900]);
    }
  }
  for (const e of spec.gallery.eyes) used.add(e.thumb);
  for (const r of spec.more) fam(r.base);
  for (const e of spec.reveal.eyes) {
    fam(e.photo, [900, 1200]);
    fam(e.iris, [900, 1200]);
    used.add(e.art);
  }
  for (const v of Object.values(spec.wallThumbs)) used.add(v);
  return { used, missing };
}

/** Is the release gate an error in this environment? A production deploy (Vercel sets VERCEL_ENV=production) or an explicit
 *  LANDING_GATE=strict: yes. A local build, a preview deploy: a notice only. There is deliberately no switch that turns a production
 *  gate off: the way to a production build is to make the gate empty. */
export function gateIsStrict(env) {
  return env.LANDING_GATE === 'strict' || env.VERCEL_ENV === 'production';
}

/** The gate table against the registry: { total, live, preview, lab, blocked: [{ tile, reason }] }. One row per tile of the gallery; live, preview and lab
 *  list the tile ids by the registry's CEILING for the tile's style and number of eyes (the most the owner can ever switch on: live means he can tick it
 *  live in the admin page, preview and lab mean the page shows it as Soon until the ceiling is raised in the registry); blocked lists the tiles the
 *  engine could never make, with the reason. styles: the registry's STYLES; tileStyle: TILE_STYLE of src/landing/tileStyle.ts; gallery: GALLERY of
 *  src/landing/assets.data.ts. Pure: it reads nothing. */
export function releaseGate(styles, tileStyle, gallery) {
  const has = (o, k) => o !== null && typeof o === 'object' && Object.prototype.hasOwnProperty.call(o, k);
  const gate = { total: 0, live: [], preview: [], lab: [], blocked: [] };
  for (const g of gallery?.groups ?? []) {
    for (const it of gallery[g] ?? []) {
      gate.total += 1;
      const row = has(tileStyle, it.id) ? tileStyle[it.id] : undefined;
      const d = row && has(styles, row.id) ? styles[row.id] : undefined;
      let reason = '';
      if (!row) reason = 'src/landing/tileStyle.ts has no row for it';
      else if (!d) reason = `the registry has no style "${row.id}"`;
      else {
        const ceiling = ceilingOf(d, row.eyes);
        if (ceiling === null) reason = `"${row.id}" takes ${d.eyes[0]} to ${d.eyes[1]} eyes, the tile shows ${row.eyes}`;
        else if (ceiling === 'retired') reason = `"${row.id}" is retired: it can never be bought again`;
        else if (ceiling === 'planned') reason = `"${row.id}" is only planned for ${row.eyes} eye(s): no engine makes it yet`;
        else if (ceiling === 'live' || ceiling === 'preview' || ceiling === 'lab') gate[ceiling].push(it.id);
        else reason = `"${row.id}" has the stage "${ceiling}", which this check does not know`;
      }
      if (reason) gate.blocked.push({ tile: it.id, reason });
    }
  }
  return gate;
}

/** One line for the CLI: what the page can sell in principle, by the registry's ceilings. */
export function gateSummary(gate) {
  const part = (name, ids) => `${ids.length} ${name}${ids.length ? ` (${ids.join(', ')})` : ''}`;
  return `${gate.total} tiles: ${part('with a live ceiling', gate.live)}, ${part('at preview', gate.preview)}, ${part('in the laboratory', gate.lab)}, ${gate.blocked.length} that the engine cannot make`;
}

/** { problems, notices, gate } for the committed pictures. assets: src/landing/assets.ts, data: src/landing/assets.data.ts, tiles: src/landing/tileStyle.ts
 *  (as the build loaded them). */
export function checkLandingAssets(root, assets, data, tiles) {
  const problems = [];
  const notices = [];
  const dir = join(root, LANDING_DIR);
  const files = assets?.ASSET_HASH;
  if (!files) return { problems: ['src/landing/assets.ts: ASSET_HASH not found (run scripts/build_landing_assets.py)'], notices, gate: null };
  let total = 0;
  const want = new Set();
  for (const [name, [hash, w, h, bytes]] of Object.entries(files)) {
    const slash = name.lastIndexOf('/');
    const rel = `${name.slice(0, slash + 1)}${name.slice(slash + 1)}.${hash}.webp`;
    want.add(rel);
    const p = join(dir, rel);
    if (!existsSync(p)) { problems.push(`${LANDING_DIR}/${rel} is missing (run scripts/build_landing_assets.py)`); continue; }
    const buf = readFileSync(p);
    total += buf.length;
    if (buf.length !== bytes) problems.push(`${LANDING_DIR}/${rel}: ${buf.length} bytes, the manifest says ${bytes}`);
    if (createHash('sha256').update(buf).digest('hex').slice(0, HASH_LEN) !== hash) problems.push(`${LANDING_DIR}/${rel}: its content does not hash to the name (a picture was changed without a new name)`);
    const size = webpSize(buf);
    if (!size) problems.push(`${LANDING_DIR}/${rel}: not a webp file`);
    else if (size.w !== w || size.h !== h) problems.push(`${LANDING_DIR}/${rel}: ${size.w} x ${size.h} px, the manifest says ${w} x ${h}`);
    if (buf.length > FILE_BUDGET) problems.push(`${LANDING_DIR}/${rel}: ${Math.round(buf.length / 1000)} kB, over the ${FILE_BUDGET / 1000} kB budget of one picture`);
  }
  for (const f of listFiles(dir)) {
    const rel = relative(dir, f).split(sep).join('/');
    if (!want.has(rel)) problems.push(`${LANDING_DIR}/${rel} is not in the manifest (only pictures the page uses belong in the repository)`);
  }
  if (total > TOTAL_BUDGET) problems.push(`${LANDING_DIR}: ${(total / 1e6).toFixed(2)} MB, over the ${TOTAL_BUDGET / 1e6} MB budget`);
  for (const w of HERO_WIDTHS) {
    const hero = files[`${HERO_FAMILY}_${w}`];
    if (!hero) problems.push(`the LCP picture ${HERO_FAMILY}_${w} is not in the manifest`);
    else if (hero[3] > HERO_BUDGET) problems.push(`the LCP picture ${HERO_FAMILY}_${w} is ${hero[3]} bytes, over the ${HERO_BUDGET} byte budget`);
  }

  // the manifest against the list that makes it
  let spec = null;
  try { spec = JSON.parse(readFileSync(join(root, 'scripts/landing_assets.json'), 'utf8')); } catch { problems.push('scripts/landing_assets.json cannot be read'); }
  if (spec) {
    const { used, missing } = usedNames(spec, new Set(Object.keys(files)));
    problems.push(...missing);
    for (const n of Object.keys(files)) if (!used.has(n)) problems.push(`${n} is in the manifest but nothing in scripts/landing_assets.json names it`);
    for (const n of used) if (!(n in files)) problems.push(`${n} is named in scripts/landing_assets.json but is not in the manifest`);
    // a room picture never offers a file wider than the plate it was made from: stage and More 1200 px, the phone 1856 px, the gallery wall views
    // 1200 px. (Five old prototype phone files of 2000 px were served to tablets and foldables; the family had a width nobody had made again.)
    const cap = (base, max) => {
      for (const n of Object.keys(files)) {
        const m = WIDTH_RE.exec(n);
        if (m && m[1] === base && +m[2] > max) problems.push(`${n} is wider than the ${max} px cap of its picture family (a stale width of an older design?)`);
      }
    };
    for (const [mat, arts] of Object.entries(spec.stage)) for (const a of Object.values(arts)) cap(a.base, mat === 'phone' ? 1856 : 1200);
    for (const r of spec.more) cap(r.base, 1200);
    for (const g of spec.gallery.groups) for (const it of spec.gallery[g]) for (const k of ['wall', 'wallOwn']) if (it[k]) cap(it[k].base, 1200);
  }

  // cache headers
  let vercel = null;
  try { vercel = JSON.parse(readFileSync(join(root, 'vercel.json'), 'utf8')); } catch { problems.push('vercel.json cannot be read'); }
  if (vercel) {
    const immutable = (path) => {
      const v = headersFor(vercel, path)['cache-control'] || '';
      return /\bimmutable\b/.test(v) && /max-age=31536000\b/.test(v);
    };
    for (const rel of want) if (!immutable(`/assets/landing/${rel}`)) { problems.push(`vercel.json: /assets/landing/${rel} is not served "immutable" for a year`); break; }
    for (const p of ['/assets/main-AbCdEf12.js', '/assets/jsx-runtime-0NXTbTUk.css']) if (!immutable(p)) problems.push(`vercel.json: a hashed bundle file like ${p} is not served "immutable" for a year`);
    for (const p of ['/', '/index.html', '/terms', '/assets/atelier/style-celestial-gold-800.webp', '/assets/atelier/fonts/cinzel-var.woff2', '/assets/bg_studio_black.jpg', '/legal/order-mail.json']) {
      if (immutable(p)) problems.push(`vercel.json: ${p} is not hashed but is served "immutable"`);
    }
  }

  // the release gate (a notice, an error for a production build: see the top)
  let gate = null;
  let styles = null;
  try { styles = loadRegistry(root).styles; } catch (e) { problems.push(`the release gate cannot read the registry: ${e instanceof Error ? e.message : String(e)}`); }
  if (styles && !tiles?.TILE_STYLE) problems.push('src/landing/tileStyle.ts: TILE_STYLE not found (the release gate reads it)');
  else if (styles) {
    gate = releaseGate(styles, tiles.TILE_STYLE, data?.GALLERY);
    if (!gate.total) problems.push('src/landing/assets.data.ts: GALLERY has no tiles (the release gate reads it)');
    if (gate.blocked.length) {
      const why = gate.blocked.map((b) => `${b.tile} (${b.reason})`).join('; ');
      const line = `RELEASE GATE: ${gate.blocked.length} of ${gate.total} tiles of the style gallery are of something the engine cannot make: ${why}. Give each tile a row in src/landing/tileStyle.ts that names a style of the registry (api/_lib/styles_registry.py) which takes that many eyes and is not retired or only planned, or cut the tile from the gallery (scripts/landing_assets.json).`;
      if (gateIsStrict(process.env)) problems.push(`${line} This is a production build (VERCEL_ENV=production or LANDING_GATE=strict): it must not go live before the gate is empty.`);
      else notices.push(line);
    }
  }
  return { problems, notices, gate };
}

// `node scripts/check_landing_assets.mjs` (npm run check:assets): loads the two manifests through Vite's module runner
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const { runnerImport } = await import('vite');
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  const load = async (p) => (await runnerImport(p, { root, configFile: false, logLevel: 'silent' })).module;
  const { problems, notices, gate } = checkLandingAssets(root, await load('./src/landing/assets.ts'), await load('./src/landing/assets.data.ts'), await load('./src/landing/tileStyle.ts'));
  for (const n of notices) console.log(n);
  if (gate) console.log(`release gate: ${gateSummary(gate)}`);
  if (problems.length) {
    console.error(`landing assets check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
    process.exit(1);
  }
  console.log('landing assets check ok');
}
