// The check of the landing page's pictures (run by vite.config.ts before every build; `npm run check:assets` runs it alone).
// public/assets/landing and src/landing/assets.ts (the manifest, written by scripts/build_landing_assets.py) must agree:
//   1. every picture of the manifest exists under its content hashed name, its bytes hash to the name, its size in bytes and
//      its width and height (read from the webp header) are the manifest's;
//   2. no file in public/assets/landing is left out of the manifest (only what the page uses is in the repository), and the
//      manifest is exactly what scripts/landing_assets.json names (its families and extras): nothing unused, nothing missing;
//   3. the budgets: the whole folder, the biggest file, the LCP picture of the first screen (phone, slow 4G: BUILD_PLAN section 5);
//   4. the cache headers: vercel.json gives every picture of the folder and every hashed script and stylesheet of the build
//      "immutable" for a year, and gives nothing that is not hashed (the pages, the pictures of /assets/atelier, the fonts) that;
// and, as a notice that never fails the build (the owner's decision, BUILD_PLAN section 3 item 1): the RELEASE GATE, which tiles of
// the style gallery the engine (api/_lib/iris.py STYLES) can make today. LANDING_GATE=strict makes an unorderable tile an error
// (for the go-live build).
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { headersFor } from './lib/static.mjs';

export const LANDING_DIR = 'public/assets/landing';
const HASH_LEN = 10;
const TOTAL_BUDGET = 10.5e6;       // bytes of all pictures together (9.2 MB today: 163 files)
const FILE_BUDGET = 350e3;         // bytes of any one picture
const HERO_FAMILY = 'm/lounge_acrylic__eye__tight';
const HERO_BUDGET = 60e3;          // the LCP picture the phone fetches (900 px) on slow 4G
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

/** The styles api/_lib/iris.py can make today. */
export function liveEngineStyles(root) {
  try {
    const text = readFileSync(join(root, 'api/_lib/iris.py'), 'utf8').replace(/\r\n/g, '\n');   // the file may have Windows line ends
    let body = text.slice(text.indexOf('STYLES = {'));
    body = body.slice(0, body.indexOf('\n}\n'));
    return [...new Set([...body.matchAll(/^[ ]{4}"([a-z_]+)":[ ]*\{/gm)].map((m) => m[1]))].sort();
  } catch {
    return [];
  }
}

/** { problems, notices } for the committed pictures. assets: src/landing/assets.ts, data: src/landing/assets.data.ts (as the build loaded them). */
export function checkLandingAssets(root, assets, data) {
  const problems = [];
  const notices = [];
  const dir = join(root, LANDING_DIR);
  const files = assets?.ASSET_HASH;
  if (!files) return { problems: ['src/landing/assets.ts: ASSET_HASH not found (run scripts/build_landing_assets.py)'], notices };
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
  const hero = files[`${HERO_FAMILY}_900`];
  if (!hero) problems.push(`the LCP picture ${HERO_FAMILY}_900 is not in the manifest`);
  else if (hero[3] > HERO_BUDGET) problems.push(`the LCP picture ${HERO_FAMILY}_900 is ${hero[3]} bytes, over the ${HERO_BUDGET} byte budget`);

  // the manifest against the list that makes it
  let spec = null;
  try { spec = JSON.parse(readFileSync(join(root, 'scripts/landing_assets.json'), 'utf8')); } catch { problems.push('scripts/landing_assets.json cannot be read'); }
  if (spec) {
    const { used, missing } = usedNames(spec, new Set(Object.keys(files)));
    problems.push(...missing);
    for (const n of Object.keys(files)) if (!used.has(n)) problems.push(`${n} is in the manifest but nothing in scripts/landing_assets.json names it`);
    for (const n of used) if (!(n in files)) problems.push(`${n} is named in scripts/landing_assets.json but is not in the manifest`);
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

  // the release gate (a notice, see the top)
  const live = liveEngineStyles(root);
  const tiles = [];
  for (const g of data?.GALLERY?.groups ?? []) for (const it of data.GALLERY[g]) tiles.push(it.id);
  const notLive = tiles.filter((t) => !data.ENGINE_STYLE[t] || !live.includes(data.ENGINE_STYLE[t]));
  if (notLive.length) {
    const line = `RELEASE GATE: the engine (api/_lib/iris.py) makes ${live.join(', ')}; ${notLive.length} of ${tiles.length} tiles of the style gallery cannot be ordered yet (${notLive.join(', ')}). Ship the v3 engine, pay.py style ids, terms.ts and the checkout consent in the same deploy, or cut the gallery to what exists (BUILD_PLAN section 3, item 1).`;
    if (process.env.LANDING_GATE === 'strict') problems.push(line);
    else notices.push(line);
  }
  return { problems, notices };
}

// `node scripts/check_landing_assets.mjs` (npm run check:assets): loads the two manifests through Vite's module runner
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const { runnerImport } = await import('vite');
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  const load = async (p) => (await runnerImport(p, { root, configFile: false, logLevel: 'silent' })).module;
  const { problems, notices } = checkLandingAssets(root, await load('./src/landing/assets.ts'), await load('./src/landing/assets.data.ts'));
  for (const n of notices) console.log(n);
  if (problems.length) {
    console.error(`landing assets check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
    process.exit(1);
  }
  console.log('landing assets check ok');
}
