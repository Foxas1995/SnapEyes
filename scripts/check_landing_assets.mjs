// The check of the landing page's pictures (run by vite.config.ts before every build; `npm run check:assets` runs it alone).
// public/assets/landing and src/landing/assets.ts (the manifest, written by scripts/build_landing_assets.py) must agree:
//   1. every picture of the manifest exists under its content hashed name, its bytes hash to the name, its size in bytes and
//      its width and height (read from the webp header) are the manifest's;
//   2. no file in public/assets/landing is left out of the manifest (only what the page uses is in the repository), and the
//      manifest is exactly what scripts/landing_assets.json names (its families and extras): nothing unused, nothing missing;
//   3. the budgets: the whole folder, the biggest file, the LCP picture of the first screen (phone, slow 4G: BUILD_PLAN section 5);
//   4. the cache headers: vercel.json gives every picture of the folder and every hashed script and stylesheet of the build
//      "immutable" for a year, and gives nothing that is not hashed (the pages, the pictures of /assets/atelier, the fonts) that;
// and the RELEASE GATE (scripts/landing_gate.mjs): the page must never promise what the engine cannot sell. Each of the 16 tiles of the style gallery stands for a style
// of the registry (api/_lib/styles_registry.py, the one place for style ids, names and stages) and a number of eyes (src/landing/tileStyle.ts TILE_STYLE). What can be BOUGHT
// is decided at run time (the registry's ceiling per number of eyes, then the owner's tick in the admin page: no build ever sees it), so the gate does not ask that
// tiles can be bought; it renders the page (src/landing/shell/gate.tsx) in every state of the catalogue a visitor can meet and refuses a promise: a tile of a style that is
// not live without its Soon chip, a price for a style that is not live, a style name that is not the registry's, a price row that names or prices what cannot be bought,
// a tile of something that does not exist (no row, a style the registry does not have, a retired style, a wrong number of eyes), and, in every build, a missing tile picture.
// The tiles that stand for a style that is only planned (no engine yet), in the laboratory or at preview are fine: they say Soon. While a promise is broken the build prints a
// notice, and the build of a PRODUCTION deploy (VERCEL_ENV=production, or LANDING_GATE=strict anywhere) fails.
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { headersFor } from './lib/static.mjs';
import { cssStub } from './lib/cssstub.mjs';
import { loadRegistry } from './styles_source.mjs';
import { gateInputs, gateIsStrict, gateSummary, promiseGate, releaseGate } from './landing_gate.mjs';

export { gateInputs, gateIsStrict, gateSummary, promiseGate, releaseGate };

/** What every price the page prints must say, from the SERVER's own price rule (src/shared/markets.ts priceMinor, the rule api/_lib/pay.py applies) and the registry's price class of
 *  each style: { [lang]: { price: { [style id]: { [eyes]: { minor, text } } }, further: { minor, text } | null } } for the default market's ladder, in each language's money.
 *  `further` is what each eye after the second adds (the step of the ladder). The landing's own price helpers (src/landing/priceText.ts, the gallery's price kinds) are not used, so
 *  a tile or a row that reads the wrong class or the wrong count of eyes is held to the value the server charges. Plain data (it survives a JSON copy). */
export function expectedPrices(markets, styles, langs) {
  const market = markets.DEFAULT_MARKET;
  const list = markets.priceList(market);
  const currency = markets.currencyOf(market);
  const ids = Object.entries(styles).filter(([, d]) => d.legacy !== 1);
  const steppable = ids.find(([, d]) => d.eyes[0] <= 3 && 4 <= d.eyes[1])?.[0] ?? null;
  const out = {};
  for (const lang of langs) {
    const cell = (minor) => ({ minor, text: markets.money(minor, currency, lang) });
    const price = {};
    for (const [id, d] of ids) {
      price[id] = {};
      for (let n = d.eyes[0]; n <= d.eyes[1]; n++) price[id][String(n)] = cell(markets.priceMinor(n, id, market, list));
    }
    out[lang] = { price, further: steppable ? cell(markets.priceMinor(4, steppable, market, list) - markets.priceMinor(3, steppable, market, list)) : null };
  }
  return out;
}

/** The page rendered for the gate in every state of the catalogue (src/landing/shell/gate.tsx renderGate: the styles chapter, the price table, the hero and the FAQ, wired as the
 *  live page is), with the prices it must print worked out beside it (expectedPrices): load(path) is Vite's module runner. */
export async function renderLanding(load, root) {
  const markets = await load('./src/shared/markets.ts');
  const { LANGS } = await load('./src/shared/lang.ts');
  // the chapter's components import their own stylesheet: the gate's own runner stubs the stylesheets (scripts/lib/cssstub.mjs)
  const { runnerImport } = await import('vite');
  const gate = (await runnerImport('./src/landing/shell/gate.tsx', { configFile: false, logLevel: 'silent', root, plugins: [cssStub()] })).module;
  const rendered = await gate.renderGate(gateInputs(root));
  rendered.expect = expectedPrices(markets, loadRegistry(root).styles, LANGS);
  return rendered;
}

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

/** { problems, notices, gate } for the committed pictures. assets: src/landing/assets.ts, data: src/landing/assets.data.ts, tiles: src/landing/tileStyle.ts
 *  (as the build loaded them), rendered: what src/landing/shell/gate.tsx renderGate(gateInputs(root)) gave for the page (the gate reads the markup). */
export function checkLandingAssets(root, assets, data, tiles, rendered) {
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

  // the release gate (a notice, an error for a production build: see the top and scripts/landing_gate.mjs)
  let gate = null;
  let styles = null;
  try { styles = loadRegistry(root).styles; } catch (e) { problems.push(`the release gate cannot read the registry: ${e instanceof Error ? e.message : String(e)}`); }
  if (styles && !tiles?.TILE_STYLE) problems.push('src/landing/tileStyle.ts: TILE_STYLE not found (the release gate reads it)');
  else if (styles) {
    gate = releaseGate(styles, tiles.TILE_STYLE, data?.GALLERY);
    if (!gate.total) problems.push('src/landing/assets.data.ts: GALLERY has no tiles (the release gate reads it)');
    const broken = [];
    if (gate.blocked.length) {
      const why = gate.blocked.map((b) => `${b.tile} (${b.reason})`).join('; ');
      broken.push(`${gate.blocked.length} of ${gate.total} tiles of the style gallery stand for something that does not exist: ${why}. Give each tile a row in src/landing/tileStyle.ts that names a style of the registry (api/_lib/styles_registry.py) which takes that many eyes and is not retired, or cut the tile from the gallery (scripts/landing_assets.json)`);
    }
    if (!rendered) problems.push('the release gate was not given the rendered page (src/landing/shell/gate.tsx renderGate): it cannot tell what the page promises');
    else {
      const inputs = gateInputs(root);
      const { promises, underSells, pictures } = promiseGate(rendered, inputs, styles, tiles.TILE_STYLE, data?.GALLERY);
      for (const p of pictures) problems.push(`a tile picture is missing: ${p}`);
      for (const e of rendered.errors ?? []) problems.push(`the page could not be rendered for the gate: ${e}`);
      if (promises.length) broken.push(`the page promises what the engine cannot sell (${promises.length}): ${promises.join('; ')}. A tile that cannot be bought says Soon and prints no price; a name is the registry's; a price row names and prices only what the run-time catalogue lists live`);
      for (const u of underSells) notices.push(`the page offers less than it can sell: ${u}`);
    }
    for (const line of broken) {
      if (gateIsStrict(process.env)) problems.push(`RELEASE GATE: ${line}. This is a production build (VERCEL_ENV=production or LANDING_GATE=strict): it must not go live while the page promises what it cannot sell.`);
      else notices.push(`RELEASE GATE: ${line}`);
    }
  }
  return { problems, notices, gate };
}

// `node scripts/check_landing_assets.mjs` (npm run check:assets): loads the manifests and the gate's view of the page through Vite's module runner
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const { runnerImport } = await import('vite');
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent' })).module;
  const rendered = await renderLanding(load, root);
  const { problems, notices, gate } = checkLandingAssets(root, await load('./src/landing/assets.ts'), await load('./src/landing/assets.data.ts'), await load('./src/landing/tileStyle.ts'), rendered);
  for (const n of notices) console.log(n);
  if (gate) console.log(`release gate: ${gateSummary(gate)}; ${rendered.scenarios.length} states of the catalogue rendered in ${Object.keys(rendered.scenarios[0]?.langs ?? {}).length} languages`);
  if (problems.length) {
    console.error(`landing assets check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
    process.exit(1);
  }
  console.log('landing assets check ok');
}
