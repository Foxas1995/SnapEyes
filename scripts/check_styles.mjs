// The style check of the build: every style id, name, layout and price rule lives in ONE place, api/_lib/styles_registry.py (the
// public literal, which the pages read too) with the engine facts in api/_lib/styles_engine.py (Python only). This refuses the
// build when
//   1. a literal is not plain JSON (or is JSON that Python cannot read: null, true, false, a float, non-ASCII text), or an entry
//      breaks the schema (an unknown or missing field, eyes outside 1 to 8, layouts outside the eyes or not covering them, a
//      stage that is not one of the five, a planned style with an engine, a live one without), the two literals do not hold the
//      same ids, the pages' reading of the file (src/shared/styles.ts) differs from this one, or the engine table of
//      api/_lib/iris.py (the six legacy ids) no longer has the registry's legacy ids, in the same order, with the same accents;
//   2. two ids share a slug (a legacy id and a v3 id of the same name may), or an id, slug or name holds a heart or a pet symbol
//      (owner rule: no hearts anywhere, pets out of scope; test T12);
//   3. a style id is written in a file of api/, src/ or scripts/ outside the registry, the engine table of the legacy engine and
//      the copy dictionaries the allow list below names (the "no other copy" scan check_prices.mjs does for prices; a word
//      boundary that counts "_" as a word character, so the price keys one_eye_studio_black and one_eye_art are not style ids);
//   4. a copy dictionary keyed by style id (the landing page's styles.desc) has other keys than the ids shown to customers
//      (stage preview or live) in some language; and, from the work package that rewrites the texts (WP12_RULES below), a string
//      that states a number of styles;
//   5. the layout words (api/_lib/layout_names.py, the one table of them) are not plain JSON, lack one of the four languages for a layout
//      id, name a layout no style takes, or leave out a layout some style takes; the pages' reading of the file (src/shared/layouts.ts)
//      differs from this one; or any other file of api/, src/ or scripts/ holds a table that names layouts again (the 14 tables of the
//      e-mails, the picker, the order page and the Python files moved into that file with work package 2);
//   6. the price rules disagree: for every id, every eye count of 1 to 8, every market and every price experiment ladder the
//      site's rule (src/shared/markets.ts priceMinor), this build's restatements (check_prices.mjs priceRule,
//      check_experiments.mjs ladderRule) and the registry's price class give one price (api/_lib/pay.py and abtest.py are
//      compared by the style suites);
//   7. the terms of sale name the price classes: the rows of the black class print the name of its one v3 member (the legacy ids retire at the
//      cutover and are not named; a second member, or a rename, needs a text change and a new LEGAL_UPDATED); and, from WP12_RULES, no terms
//      table prints a number of eyes as a maximum (neither \${MAX_EYES} nor a digit before "eyes") and the landing's art row and eye limit come
//      from the run-time tokens ({styles}, {max});
//   8. the plate library baked into api/_lib/plates_registry.py is sound (its version is the registry's, every plate is well formed, every
//      usable plate's 1K file is in api/_assets/plates with the recorded size and sha256 and no file rides in unlisted, the two atlases
//      likewise, the engine entries name only families and atlases that exist) and every style shown to customers (stage preview or live) has
//      usable plates for the families it reads and its tile images (public/assets/atelier/style-<slug>-480.webp and -800.webp);
//   9. the byte budget: the files of api/ plus the recorded size of the Python packages stay under 235 MiB for a rendering function (the
//      documented limit is 500 MB; 235 is the plan's own tripwire until the real size is read from a deployment);
//  10. vercel.json names every function of api/ on its own (no catch-all glob), with one shared maxDuration, and only compose, master_compose,
//      order and admin keep the plates and the atlases (the other seven exclude them);
//  11. (not a refusal) the registry hash is printed: 12 hex digits of the sha256 of both literals in canonical form;
//  12. provenance: no image of the repository is byte for byte one of the owner's reference works or one of the calibration irises (the deny list of
//      hashes in scripts/hygiene_denylist.json): the originals never enter the repository;
//  13. the one duration constant: every maxDuration of vercel.json equals DURATION_S of api/_lib/duration.py, from which the work budget, the leases of
//      every claim and the waits of the server's own chain derive (raising the limit is one coordinated change, never one number in one file: a longer
//      function with the old lease lets a second caller take over a render that is still alive).
// Items 8, 9, 10, 12 and 13 read the deployment tree and run only where there is a vercel.json (the registry suite's mutation copies carry no such file).
// vite.config.ts runs it before every build (src/ is loaded through Vite's module runner, as for the text check);
// `npm run check:styles` runs it alone.
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import {
  STYLES_FILE, ENGINE_FILE, LAYOUTS_FILE, PLATES_FILE, parseRegistrySource, parseEngineSource, parseLayoutNamesSource, parsePlatesSource, registryHash, rangeOf, ceilingOf,
} from './styles_source.mjs';
import { parseMarketsSource, MARKETS_FILE, priceRule } from './check_prices.mjs';
import { parseExperimentsSource, EXPERIMENTS_FILE, ladderRule } from './check_experiments.mjs';

/** The rules of items 4 and 7 that the texts of work package 12 meet: no string states a number of styles, no terms table prints a number of eyes
 *  as a maximum (they are count-free, and so is every price row), the landing's pricing rows take the list of art styles and the eye limit from the
 *  run-time tokens. Work package 12 rewrote the landing, the picker's price lines and the terms and set this to true in the same change. */
export const WP12_RULES = true;

const STAGES = ['planned', 'lab', 'preview', 'live', 'retired'];
const CEILINGS = ['planned', 'lab', 'preview', 'live'];
const RANK = Object.fromEntries(STAGES.map((s, i) => [s, i]));
const GROUPS = ['solo', 'duo', 'grp', 'pet'];
const CLASSES = ['black', 'art'];
const GATES = ['none', 'advisory', 'hard'];
const EYE_CLASSES = ['own', 'dark_brown', 'grey'];
const MODULES = ['singles', 'collision', 'universe', 'legacy'];
const RULE_SETS = ['lid', 'fill'];
const ATLASES = ['chips', 'drops'];
const STEP_KINDS = ['prep', 'art', 'scene', 'finish', 'bands'];
const WAVES = ['R1', 'R2', 'R3', 'legacy'];
const MAX_EYES = 8;
/** The languages every layout has a word in (the site's four: src/shared/lang.ts). */
export const LAYOUT_LANGS = ['en', 'de', 'lt', 'hu'];
const PUBLIC_FIELDS = ['accent', 'eyes', 'gate', 'group', 'layouts', 'legacy', 'name', 'pick', 'price_class', 'reason', 'slug', 'stage', 'stage_by_eyes', 'tile_order', 'work_side'];
const ENGINE_FIELDS = ['atlas', 'canvases', 'design_by_eyes', 'engine', 'fill_side', 'gate_rules', 'plates', 'steps', 'wave'];
const HEART_WORDS = ['heart', 'hearts', 'love', 'loves', 'valentine', 'valentines', 'cupid'];
const PET_WORDS = ['paw', 'paws', 'bone', 'bones', 'cat', 'cats', 'dog', 'dogs', 'puppy', 'kitten'];

/** Files outside the registry that may write a style id, and why. Everything else reads the registry. */
export const ID_ALLOW = {
  'api/_lib/iris.py': 'the legacy engine\'s own table (STYLES: background, accent, title per legacy id); item 1 keeps its keys and accents equal to the registry\'s legacy block',
  'src/landing/copy.ts': 'copy dictionary keyed by style id (styles.desc), item 4 keeps its keys equal to the shown ids',
  'src/landing/copy.lt.ts': 'copy dictionary keyed by style id (styles.desc), item 4',
  'src/landing/copy.hu.ts': 'copy dictionary keyed by style id (styles.desc), item 4',
  'api/_lib/styles/collision/scenes.py': 'the scene key of a collision artwork is the registry id of its style: it is part of the prototype\'s seed in step A (WP7A), which step B (WP7B) replaces by the plan\'s seed key',
};
// folders of a scan that never hold customer-facing code: the style suites (they name ids to test them) and this check's own files
const ID_SKIP_DIRS = ['scripts/styles_tests'];
const ID_SKIP_FILES = [STYLES_FILE, ENGINE_FILE, 'scripts/check_styles.mjs', 'scripts/styles_source.mjs', 'scripts/check_styles.d.mts'];

const isInt = (v) => typeof v === 'number' && Number.isInteger(v);
const isObj = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
const asciiOnly = (s) => /^[\x20-\x7e]*$/.test(s);
const dedupe = (a) => [...new Set(a)];
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

function sameJson(a, b) {
  if (a === b) return true;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object' || Array.isArray(a) !== Array.isArray(b)) return false;
  const ka = Object.keys(a).sort(), kb = Object.keys(b).sort();
  return ka.join() === kb.join() && ka.every((k) => sameJson(a[k], b[k]));
}

/** Every value of a literal must be one Python reads from the same text: strings (ASCII), whole numbers, lists, objects. */
function checkPlainValues(v, at, out) {
  if (v === null || typeof v === 'boolean') out.push(`${at}: null, true and false are not Python (use 0, 1, {} or [])`);
  else if (typeof v === 'number') { if (!Number.isInteger(v)) out.push(`${at}: whole numbers only (${v})`); }
  else if (typeof v === 'string') { if (!asciiOnly(v)) out.push(`${at}: ASCII only: ${JSON.stringify(v)}`); }
  else if (Array.isArray(v)) v.forEach((x, i) => checkPlainValues(x, `${at}[${i}]`, out));
  else if (isObj(v)) for (const [k, x] of Object.entries(v)) { if (!asciiOnly(k)) out.push(`${at}: a key that is not ASCII: ${JSON.stringify(k)}`); checkPlainValues(x, `${at}.${k}`, out); }
}

/** A range-keyed map ({"3": x, "4-8": y}) for the eyes of an entry: keys are ranges inside the eyes, none overlapping. Returns the ranges. */
function checkRanges(map, eyes, at, out) {
  const ranges = [];
  for (const k of Object.keys(map)) {
    if (!/^[1-8](-[1-8])?$/.test(k)) { out.push(`${at}: "${k}" is not an eye range ("3" or "4-8")`); continue; }
    const [lo, hi] = rangeOf(k);
    if (lo > hi || lo < eyes[0] || hi > eyes[1]) { out.push(`${at}: the range "${k}" is not inside the eyes ${eyes[0]} to ${eyes[1]}`); continue; }
    for (const [a, b] of ranges) if (lo <= b && a <= hi) out.push(`${at}: the range "${k}" overlaps another range`);
    ranges.push([lo, hi]);
  }
  return ranges;
}

const covers = (ranges, eyes) => {
  for (let n = eyes[0]; n <= eyes[1]; n++) if (!ranges.some(([a, b]) => a <= n && n <= b)) return n;
  return 0;
};

function words(s) {
  return String(s).toLowerCase().split(/[^a-z]+/).filter(Boolean);
}

/** 1 and 2 for the public literal. layoutIds: the vocabulary, the ids api/_lib/layout_names.py has words for. */
function checkPublic(reg, out, layoutIds) {
  const at0 = STYLES_FILE;
  if (reg.schema !== 1) out.push(`${at0}: STYLES_SCHEMA is ${reg.schema}, this check knows 1`);
  if (!isInt(reg.platesVersion) || reg.platesVersion < 1) out.push(`${at0}: PLATES_VERSION must be a whole number from 1`);
  const styles = reg.styles;
  if (!isObj(styles) || !Object.keys(styles).length) { out.push(`${at0}: STYLES is not an object of styles`); return; }
  checkPlainValues(styles, `${at0} STYLES`, out);
  const slugs = new Map();
  const orders = new Map();
  for (const [id, d] of Object.entries(styles)) {
    const at = `${at0} style "${id}"`;
    if (!/^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)?$/.test(id)) out.push(`${at}: the id must be lower case letters, digits and _ (group.name for a v3 id)`);
    if (!isObj(d)) { out.push(`${at}: not an object`); continue; }
    const have = Object.keys(d).sort();
    if (have.join() !== PUBLIC_FIELDS.join()) {
      const missing = PUBLIC_FIELDS.filter((f) => !(f in d)), extra = have.filter((f) => !PUBLIC_FIELDS.includes(f));
      out.push(`${at}: its fields must be exactly ${PUBLIC_FIELDS.join(', ')} (missing ${missing.join(', ') || 'none'}, unknown ${extra.join(', ') || 'none'})`);
      continue;
    }
    if (!GROUPS.includes(d.group)) out.push(`${at}: group must be one of ${GROUPS.join(', ')}`);
    if (d.legacy !== 0 && d.legacy !== 1) out.push(`${at}: legacy must be 1 or 0`);
    if (d.legacy === 1 ? id.includes('.') : !id.startsWith(`${d.group}.`)) {
      out.push(`${at}: ${d.legacy === 1 ? 'a legacy id is bare (no dot)' : `a v3 id is "${d.group}.name", its group`}`);
    }
    if (typeof d.slug !== 'string' || !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(d.slug)) out.push(`${at}: slug must be lower case letters, digits and hyphens`);
    if (typeof d.name !== 'string' || !d.name.trim() || d.name !== d.name.trim()) out.push(`${at}: name must be a brand name`);
    // eyes
    const eyes = d.eyes;
    const eyesOk = Array.isArray(eyes) && eyes.length === 2 && eyes.every(isInt) && eyes[0] >= 1 && eyes[1] <= MAX_EYES && eyes[0] <= eyes[1];
    if (!eyesOk) { out.push(`${at}: eyes must be [min, max] inside 1 to ${MAX_EYES}`); continue; }
    // layouts
    if (!isObj(d.layouts)) out.push(`${at}: layouts must map an eye count to its layout ids`);
    else {
      for (const [k, list] of Object.entries(d.layouts)) {
        if (!/^[1-8]$/.test(k) || Number(k) < eyes[0] || Number(k) > eyes[1]) out.push(`${at}: layouts key "${k}" is not an eye count inside ${eyes[0]} to ${eyes[1]}`);
        if (!Array.isArray(list) || !list.length || new Set(list).size !== list.length || list.some((x) => !layoutIds.includes(x))) {
          out.push(`${at}: layouts["${k}"] must be a list of distinct layout ids (${layoutIds.join(', ')}: the ones ${LAYOUTS_FILE} has words for), the default first`);
        }
      }
      for (let n = eyes[0]; n <= eyes[1]; n++) if (!(String(n) in d.layouts)) out.push(`${at}: layouts has nothing for ${n} eyes`);
    }
    // stages
    if (!STAGES.includes(d.stage)) out.push(`${at}: stage must be one of ${STAGES.join(', ')}`);
    if (!isObj(d.stage_by_eyes)) out.push(`${at}: stage_by_eyes must be an object`);
    else {
      checkRanges(d.stage_by_eyes, eyes, `${at} stage_by_eyes`, out);
      for (const [k, s] of Object.entries(d.stage_by_eyes)) if (!CEILINGS.includes(s)) out.push(`${at}: stage_by_eyes["${k}"] must be one of ${CEILINGS.join(', ')}`);
    }
    if (d.legacy === 1 && !['live', 'retired'].includes(d.stage)) out.push(`${at}: a legacy style is live or retired`);
    if (!CLASSES.includes(d.price_class)) out.push(`${at}: price_class must be black or art`);
    if (!GATES.includes(d.gate)) out.push(`${at}: gate must be one of ${GATES.join(', ')}`);
    else if ((d.gate === 'none') !== (d.legacy === 1)) out.push(`${at}: gate none belongs to the legacy styles only (a v3 style is advisory or hard)`);
    // pick and reason
    if (!Array.isArray(d.pick) || new Set(d.pick).size !== d.pick.length || d.pick.some((c) => !EYE_CLASSES.includes(c))) out.push(`${at}: pick must be distinct classes of ${EYE_CLASSES.join(', ')}`);
    if (!isObj(d.reason) || (Array.isArray(d.pick) && Object.keys(d.reason).sort().join() !== [...d.pick].sort().join())) out.push(`${at}: reason must have a key for exactly the classes of pick`);
    else for (const [c, key] of Object.entries(d.reason)) if (typeof key !== 'string' || !new RegExp(`^reason\\.[a-z0-9_]+\\.${c}$`).test(key)) out.push(`${at}: reason["${c}"] must be a copy key like reason.<id>.${c}`);
    // tile order
    if (!isInt(d.tile_order) || d.tile_order < 0) out.push(`${at}: tile_order must be a whole number from 0 (0: not in the tile list)`);
    else if (d.tile_order > 0) {
      const key = `${d.group}/${d.legacy}/${d.tile_order}`;
      if (orders.has(key)) out.push(`${at}: tile_order ${d.tile_order} is also ${orders.get(key)}'s (unique per group, among legacy ids and among v3 ids)`);
      else orders.set(key, `"${id}"`);
    }
    // work_side
    if (!isObj(d.work_side)) out.push(`${at}: work_side must be an object`);
    else {
      const ranges = checkRanges(d.work_side, eyes, `${at} work_side`, out);
      for (const [k, v] of Object.entries(d.work_side)) if (!isInt(v) || v < 512 || v > 4096) out.push(`${at}: work_side["${k}"] must be a size from 512 to 4096`);
      if (d.legacy === 1) { if (Object.keys(d.work_side).length) out.push(`${at}: the legacy engine has its own limits: work_side is {}`); }
      else { const gap = covers(ranges, eyes); if (gap) out.push(`${at}: work_side must cover every eye count (nothing for ${gap} eyes)`); }
    }
    // accent
    const a = d.accent;
    if (!Array.isArray(a) || !(a.length === 0 || (a.length === 3 && a.every((x) => isInt(x) && x >= 0 && x <= 255)))) out.push(`${at}: accent must be [] or [r, g, b]`);
    else if (d.legacy !== 1 && a.length) out.push(`${at}: accent is for the legacy styles only`);
    // slugs, forbidden words
    if (typeof d.slug === 'string') {
      const prev = slugs.get(d.slug);
      if (prev && !(prev.legacy !== d.legacy && prev.name === d.name)) out.push(`${at}: the slug "${d.slug}" is also the slug of "${prev.id}" (slugs are unique; only a legacy id and a v3 id of the same name may share one)`);
      else if (!prev) slugs.set(d.slug, { id, legacy: d.legacy, name: d.name });
    }
    for (const [field, text] of [['id', id], ['slug', d.slug], ['name', d.name]]) {
      for (const w of words(text)) {
        if (HEART_WORDS.includes(w)) out.push(`${at}: the ${field} "${text}" holds the word "${w}" (owner rule: no hearts anywhere)`);
        if (PET_WORDS.includes(w)) out.push(`${at}: the ${field} "${text}" holds the pet symbol word "${w}" (pets are out of scope)`);
      }
    }
  }
  // the legacy block: one layout table
  const legacy = Object.entries(styles).filter(([, d]) => isObj(d) && d.legacy === 1);
  if (legacy.length > 1 && !legacy.every(([, d]) => sameJson(d.layouts, legacy[0][1].layouts))) out.push(`${at0}: the legacy styles must share one layout table`);
  // the default style
  const def = styles[reg.defaultStyle];
  if (!def) out.push(`${at0}: DEFAULT_STYLE "${reg.defaultStyle}" is not a style of the registry`);
  else if (!['preview', 'live'].includes(ceilingOf(def, 1))) out.push(`${at0}: DEFAULT_STYLE "${reg.defaultStyle}" must be a style of one eye at preview or live`);
}

/** 1 for the engine literal, against the public one. */
function checkEngine(reg, engine, out) {
  const at0 = ENGINE_FILE;
  if (!isObj(engine) || !Object.keys(engine).length) { out.push(`${at0}: ENGINE is not an object of entries`); return; }
  checkPlainValues(engine, `${at0} ENGINE`, out);
  const ids = Object.keys(reg.styles), eids = Object.keys(engine);
  for (const id of ids) if (!(id in engine)) out.push(`${at0}: no entry for the style "${id}" of ${STYLES_FILE}`);
  for (const id of eids) if (!(id in reg.styles)) out.push(`${at0}: an entry for "${id}", which ${STYLES_FILE} does not have`);
  for (const [id, e] of Object.entries(engine)) {
    const d = reg.styles[id];
    const at = `${at0} style "${id}"`;
    if (!isObj(e)) { out.push(`${at}: not an object`); continue; }
    const have = Object.keys(e).sort();
    if (have.join() !== ENGINE_FIELDS.join()) { out.push(`${at}: its fields must be exactly ${ENGINE_FIELDS.join(', ')}`); continue; }
    if (!isObj(d) || !Array.isArray(d.eyes)) continue;
    const eng = e.engine;
    const top = Math.max(RANK[d.stage] ?? 0, ...Object.values(isObj(d.stage_by_eyes) ? d.stage_by_eyes : {}).map((s) => RANK[s] ?? 0));
    if (!isObj(eng)) out.push(`${at}: engine must be an object ({} while planned)`);
    else if (!Object.keys(eng).length) { if (top > RANK.planned) out.push(`${at}: a style at stage ${STAGES[top]} needs an engine (only a planned style has none)`); }
    else {
      if (top === RANK.planned) out.push(`${at}: a planned style has no engine (engine is {})`);
      if (!MODULES.includes(eng.module)) out.push(`${at}: engine.module must be one of ${MODULES.join(', ')}`);
      if (typeof eng.design !== 'string' || !/^[a-z][a-z0-9_]*$/.test(eng.design)) out.push(`${at}: engine.design must be the engine's own key`);
      const extra = Object.keys(eng).filter((k) => !['module', 'design', 'looks', 'clean'].includes(k));
      if (extra.length) out.push(`${at}: engine has unknown fields ${extra.join(', ')}`);
      if ('clean' in eng && eng.clean !== 0 && eng.clean !== 1) out.push(`${at}: engine.clean must be 1 or 0`);
      if ('looks' in eng) {
        if (!isObj(eng.looks)) out.push(`${at}: engine.looks must be an object`);
        else for (const [look, s] of Object.entries(eng.looks)) {
          if (!/^[a-z][a-z0-9_]*$/.test(look) || !CEILINGS.includes(s)) out.push(`${at}: engine.looks["${look}"] must be a look id with a stage of ${CEILINGS.join(', ')}`);
          else if (RANK[s] > top) out.push(`${at}: the look "${look}" is at stage ${s}, above its style (${STAGES[top]})`);
        }
      }
      if ((eng.module === 'legacy') !== (d.legacy === 1)) out.push(`${at}: the module legacy belongs to the legacy styles, and only to them`);
    }
    if (!isObj(e.design_by_eyes)) out.push(`${at}: design_by_eyes must be an object`);
    else {
      checkRanges(e.design_by_eyes, d.eyes, `${at} design_by_eyes`, out);
      for (const [k, v] of Object.entries(e.design_by_eyes)) if (typeof v !== 'string' || !/^[a-z][a-z0-9_]*$/.test(v)) out.push(`${at}: design_by_eyes["${k}"] must be a design key`);
    }
    if (!Array.isArray(e.canvases) || new Set(e.canvases).size !== e.canvases.length
      || e.canvases.some((c) => typeof c !== 'string' || !(/^\d+(\.\d+)?:\d+(\.\d+)?$/.test(c) || (d.legacy === 1 && ['artwork', 'wallpaper'].includes(c))))) {
      out.push(`${at}: canvases must be distinct ratios like "3:2", the default first`);
    } else if (isObj(eng) && Object.keys(eng).length && !e.canvases.length) out.push(`${at}: a style with an engine needs at least one canvas`);
    if (!RULE_SETS.includes(e.gate_rules)) out.push(`${at}: gate_rules must be one of ${RULE_SETS.join(', ')}`);
    if (!Array.isArray(e.plates) || e.plates.some((p) => typeof p !== 'string' || !/^P-[A-Z]{2}-[A-Z]+$/.test(p))) out.push(`${at}: plates must be plate family ids like P-SN-CLOUD`);
    if (!Array.isArray(e.atlas) || e.atlas.some((p) => !ATLASES.includes(p))) out.push(`${at}: atlas must list ${ATLASES.join(', ')}`);
    if (!isObj(e.steps)) out.push(`${at}: steps must be an object`);
    else {
      checkRanges(e.steps, d.eyes, `${at} steps`, out);
      for (const [k, v] of Object.entries(e.steps)) if (!Array.isArray(v) || !v.length || v.some((s) => !STEP_KINDS.includes(s))) out.push(`${at}: steps["${k}"] must be a list of ${STEP_KINDS.join(', ')}`);
    }
    if (!isInt(e.fill_side) || e.fill_side < 0 || e.fill_side > 1536) out.push(`${at}: fill_side must be 0 or a size up to 1536`);
    if (!WAVES.includes(e.wave)) out.push(`${at}: wave must be one of ${WAVES.join(', ')}`);
  }
}

/** api/_lib/iris.py's STYLES: the legacy ids in the registry's order, with the registry's accent where it has one. */
function checkLegacyTable(root, reg, out) {
  let text;
  try { text = readFileSync(join(root, 'api/_lib/iris.py'), 'utf8'); } catch { return; }
  const at = text.search(/^STYLES = \{/m);
  if (at < 0) { out.push('api/_lib/iris.py: STYLES not found (the style check reads it)'); return; }
  const block = text.slice(at, text.indexOf('\n}', at));
  const rows = [...block.matchAll(/^\s*"([a-z_]+)":\s*\{[^}]*"accent":\s*\((\d+),\s*(\d+),\s*(\d+)\)/gm)].map((m) => ({ id: m[1], accent: [Number(m[2]), Number(m[3]), Number(m[4])] }));
  const legacy = Object.entries(reg.styles).filter(([, d]) => d.legacy === 1);
  if (rows.map((r) => r.id).join() !== legacy.map(([id]) => id).join()) {
    out.push(`api/_lib/iris.py STYLES has the ids ${rows.map((r) => r.id).join(', ')}; the legacy styles of ${STYLES_FILE} are ${legacy.map(([id]) => id).join(', ')} (the same ids in the same order)`);
    return;
  }
  for (const [i, [id, d]] of legacy.entries()) {
    if (d.accent.length && !same(d.accent, rows[i].accent)) out.push(`api/_lib/iris.py STYLES "${id}" accent is ${JSON.stringify(rows[i].accent)}; ${STYLES_FILE} says ${JSON.stringify(d.accent)}`);
  }
}

// ---------------------------------------------------------------------------------------------------- 3. literal ids
function sourceFiles(root, dir, acc = []) {
  let names = [];
  try { names = readdirSync(join(root, dir)); } catch { return acc; }
  for (const n of names) {
    if (n === 'node_modules' || n === '__pycache__' || n.startsWith('.')) continue;
    const rel = `${dir}/${n}`;
    if (ID_SKIP_DIRS.includes(rel)) continue;
    const st = statSync(join(root, rel));
    if (st.isDirectory()) sourceFiles(root, rel, acc);
    else if (/\.(py|ts|tsx|mjs|mts|js|cjs)$/.test(n) && !ID_SKIP_FILES.includes(rel)) acc.push(rel);
  }
  return acc;
}

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** Every style id written in a file of api/, src/ or scripts/ outside the allow list. */
export function checkLiteralIds(root, ids, out, allow = ID_ALLOW) {
  if (!ids.length) return;
  const re = new RegExp(`(?<![\\w.])(${ids.map(esc).join('|')})(?![\\w])`, 'g');
  for (const dir of ['api', 'src', 'scripts']) {
    for (const rel of sourceFiles(root, dir)) {
      if (rel in allow) continue;
      const lines = readFileSync(join(root, rel), 'utf8').split('\n');
      lines.forEach((line, i) => {
        re.lastIndex = 0;
        const m = re.exec(line);
        if (m) out.push(`${rel}: writes the style id "${m[1]}" itself (line ${i + 1}); read it from ${STYLES_FILE} (api/_lib/catalogue.py, src/shared/styles.ts)`);
      });
    }
  }
}

// ---------------------------------------------------------------------------------------------------- 4. copy dictionaries
const shownIds = (styles) => Object.entries(styles).filter(([, d]) => [d.stage, ...Object.values(d.stage_by_eyes ?? {})].some((s) => s === 'preview' || s === 'live')).map(([id]) => id);

function walkObjects(v, path, fn) {
  if (!isObj(v)) return;
  fn(v, path);
  for (const [k, x] of Object.entries(v)) walkObjects(x, `${path}.${k}`, fn);
}

function walkStrings(v, path, fn) {
  if (typeof v === 'string') fn(v, path);
  else if (Array.isArray(v)) v.forEach((x, i) => walkStrings(x, `${path}[${i}]`, fn));
  else if (isObj(v)) for (const [k, x] of Object.entries(v)) walkStrings(x, `${path}.${k}`, fn);
}

/** Every copy dictionary keyed by style id has exactly the ids shown to customers, in every language of every surface. */
export function checkCopyDictionaries(surfaces, styles, out) {
  const ids = Object.keys(styles);
  const shown = shownIds(styles).sort();
  for (const [name, dict] of surfaces) {
    for (const [lang, copy] of Object.entries(dict ?? {})) {
      walkObjects(copy, `${name}.${lang}`, (o, path) => {
        const keys = Object.keys(o);
        if (!keys.some((k) => ids.includes(k))) return;
        if (keys.slice().sort().join() !== shown.join()) {
          out.push(`${path} is a dictionary keyed by style id with ${keys.slice().sort().join(', ')}; the styles shown to customers (stage preview or live) are ${shown.join(', ')}: they must be the same`);
        }
      });
    }
  }
}

const NUMBER_WORDS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'ein', 'zwei', 'drei', 'vier', 'f\u00fcnf', 'sechs', 'sieben', 'acht', 'neun', 'zehn',
  'vienas', 'du', 'trys', 'keturi', 'penki', '\u0161e\u0161i', 'septyni', 'a\u0161tuoni', 'devyni', 'de\u0161imt', 'egy', 'k\u00e9t', 'h\u00e1rom', 'n\u00e9gy', '\u00f6t', 'hat', 'h\u00e9t', 'nyolc', 'kilenc', 't\u00edz'];
/** A string that states a number of styles ("six styles", "All 6 styles", "in allen sechs Stilen", "6 stiliais", "hat st\u00edlusban"). */
export const NUMBER_OF_STYLES = new RegExp(`(?<![\\p{L}\\d])(\\d+|${NUMBER_WORDS.join('|')})\\s+(?:\\p{L}+\\s+)?(styles?|stile[ns]?|stili\\p{L}*|st\u00edl\\p{L}*)(?![\\p{L}])`, 'iu');

/** The words of index.html's head (the title and every meta content): the share and search copy, which the page's dictionary cannot reach. */
export function indexTexts(root) {
  let html = '';
  try { html = readFileSync(join(root, 'index.html'), 'utf8'); } catch { return []; }
  const texts = [...html.matchAll(/<title>([^<]*)<\/title>/g)].map((m) => ['index.html title', m[1]]);
  for (const m of html.matchAll(/<meta\s+(?:name|property)="([^"]+)"\s+content="([^"]*)"/g)) texts.push([`index.html ${m[1]}`, m[2]]);
  return texts;
}

export function checkNumberOfStyles(surfaces, out, extraTexts = []) {
  for (const [name, dict] of surfaces) {
    for (const [lang, copy] of Object.entries(dict ?? {})) {
      walkStrings(copy, `${name}.${lang}`, (s, path) => { if (NUMBER_OF_STYLES.test(s)) out.push(`${path}: states a number of styles ("${s.slice(0, 80)}"): the number comes from the catalogue, never from a text`); });
    }
  }
  for (const [path, s] of extraTexts) if (NUMBER_OF_STYLES.test(s)) out.push(`${path}: states a number of styles ("${s.slice(0, 80)}")`);
}

// ---------------------------------------------------------------------------------------------------- 5. layout names
/** The words themselves: an object of layout ids, each with exactly the four languages, each word a short text with no space at either end. */
export function checkLayoutNames(names, out) {
  const at0 = LAYOUTS_FILE;
  if (!isObj(names) || !Object.keys(names).length) { out.push(`${at0}: LAYOUT_NAMES is not an object of layout ids`); return; }
  for (const [id, row] of Object.entries(names)) {
    const at = `${at0} layout "${id}"`;
    if (!/^[a-z][a-z0-9_]*$/.test(id)) out.push(`${at}: a layout id is lower case letters, digits and _`);
    if (!isObj(row)) { out.push(`${at}: not an object of words`); continue; }
    if (Object.keys(row).sort().join() !== [...LAYOUT_LANGS].sort().join()) {
      out.push(`${at}: it must have a word in exactly ${LAYOUT_LANGS.join(', ')} (it has ${Object.keys(row).join(', ') || 'none'})`);
      continue;
    }
    for (const l of LAYOUT_LANGS) {
      const w = row[l];
      if (typeof w !== 'string' || !w.length || w !== w.trim() || [...w].some((c) => c.charCodeAt(0) < 32) || w.length > 40) {
        out.push(`${at}: the ${l} word must be a short text (1 to 40 characters, no space at either end, no line break): ${JSON.stringify(w)}`);
      }
    }
  }
}

/** The files that may hold the ids of layouts next to words: this check, its source reader and the registry files themselves. */
const LAYOUT_SKIP_FILES = [LAYOUTS_FILE, STYLES_FILE, ENGINE_FILE, 'scripts/check_styles.mjs', 'scripts/styles_source.mjs', 'scripts/check_styles.d.mts'];
const LAYOUT_TABLE_WINDOW = 400;       // characters: two layout ids that each name a word within this are one table

/** Another table that names layouts: in one file, two different layout ids, each as a key with a word that starts with a capital letter, as
 *  every layout word does (`single: 'Single'`, `"duo": "Greta"`; a lower case value such as a caption mode is not a word), within a few
 *  hundred characters of each other. The e-mails, the picker, the order page and the Python files each had
 *  one; they read api/_lib/layout_names.py now (catalogue.layout_name, src/shared/layouts.ts layoutName). */
export function checkLayoutTables(root, ids, out, skip = LAYOUT_SKIP_FILES) {
  if (!ids.length) return;
  const re = new RegExp(`(?<![\\w.])["'\\x60]?(${ids.map(esc).join('|')})["'\\x60]?\\s*:\\s*["'\\x60]\\p{Lu}`, 'gu');
  for (const dir of ['api', 'src', 'scripts']) {
    for (const rel of sourceFiles(root, dir)) {
      if (skip.includes(rel)) continue;
      const text = readFileSync(join(root, rel), 'utf8');
      const hits = [...text.matchAll(re)].map((m) => ({ id: m[1], at: m.index }));
      for (let i = 1; i < hits.length; i++) {
        const prev = hits.slice(0, i).reverse().find((h) => h.id !== hits[i].id && hits[i].at - h.at <= LAYOUT_TABLE_WINDOW);
        if (prev) {
          out.push(`${rel}: a table that names layouts again ("${prev.id}" and "${hits[i].id}" with words, line ${text.slice(0, prev.at).split('\n').length}): the words are in ${LAYOUTS_FILE} only (catalogue.layout_name, src/shared/layouts.ts layoutName)`);
          break;
        }
      }
    }
  }
}

/** Every word belongs to a layout some style takes, the pages read the same words, and no other table names layouts (a layout id a style
 *  takes that has no words is refused earlier, by checkPublic, which knows the vocabulary). pageNames: the LAYOUT_NAMES src/shared/layouts.ts parsed (without the page code loaded, that comparison is left out). */
export function checkLayouts(root, styles, names, out, pageNames) {
  const taken = new Set(Object.values(styles).flatMap((d) => Object.values(d.layouts).flat()));
  for (const l of Object.keys(names)) if (!taken.has(l)) out.push(`${LAYOUTS_FILE} has words for the layout "${l}", which no style of ${STYLES_FILE} takes (a word nobody uses: remove it, or give the style its layout)`);
  if (pageNames !== undefined && !sameJson(pageNames, names)) out.push(`src/shared/layouts.ts reads another LAYOUT_NAMES than ${LAYOUTS_FILE} holds`);
  checkLayoutTables(root, Object.keys(names), out);
}

// ---------------------------------------------------------------------------------------------------- 6. price rules
export function checkPriceRules(root, styles, client, out) {
  let markets;
  try { markets = parseMarketsSource(readFileSync(join(root, MARKETS_FILE), 'utf8')).markets; } catch { return; }
  let experiments = {};
  try { experiments = parseExperimentsSource(readFileSync(join(root, EXPERIMENTS_FILE), 'utf8')).experiments; } catch { /* checked by check_experiments */ }
  for (const [id, d] of Object.entries(styles)) {
    for (const [market, m] of Object.entries(markets)) {
      for (let eyes = 1; eyes <= MAX_EYES; eyes++) {
        const want = priceRule(markets, market, eyes, d.price_class);
        const viaLadder = ladderRule(m.prices, eyes, d.price_class);
        if (want !== viaLadder) out.push(`price rules disagree for "${id}", ${eyes} eye(s), market ${market}: check_prices priceRule ${want}, check_experiments ladderRule ${viaLadder}`);
        if (client && typeof client.priceMinor === 'function') {
          const got = client.priceMinor(eyes, id, market);
          if (got !== want) out.push(`src/shared/markets.ts priceMinor(${eyes}, ${id}, ${market}) = ${got}; the registry's price class "${d.price_class}" gives ${want}`);
        }
      }
    }
    if (client && typeof client.priceMinor === 'function') {
      for (const [key, e] of Object.entries(experiments ?? {})) {
        for (const [name, v] of Object.entries(e?.variants ?? {})) {
          for (const [market, ladder] of Object.entries(v?.prices ?? {})) {
            for (let eyes = 1; eyes <= MAX_EYES; eyes++) {
              const want = ladderRule(ladder, eyes, d.price_class);
              const got = client.priceMinor(eyes, id, market, ladder);
              if (got !== want) out.push(`src/shared/markets.ts priceMinor(${eyes}, ${id}, ${market}, ladder of "${key}"/"${name}") = ${got}; the price class "${d.price_class}" gives ${want}`);
            }
          }
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------------------------------- 7. terms of sale
export const TERMS_FILES = ['src/legal/docs/terms.ts', 'src/legal/docs/terms.lt.ts', 'src/legal/docs/terms.hu.ts'];
const BLACK_ROW = /\[\s*'([^'\\]*)'\s*,\s*\w+\(\s*(?:PRICE_CENTS\.studioBlack|(?:AU|HU)_PRICES\.one_eye_studio_black)/g;

/** The rows of the black price class (in every terms table) print the name of the class's one member. When enforcing the
 *  count-free rule (WP12_RULES): no terms table prints a number of eyes as a maximum. */
export function checkTerms(root, styles, out, files = TERMS_FILES, enforce = WP12_RULES) {
  // the black class as the terms name it: its v3 style (the legacy ids retire at the cutover, so their Studio Black is not named; a planned id has no engine)
  const members = Object.keys(styles).filter((id) => styles[id].price_class === 'black' && styles[id].legacy === 0 && !['planned', 'retired'].includes(styles[id].stage));
  if (members.length !== 1) { out.push(`the black price class has ${members.length} styles that are not legacy or planned (${members.join(', ') || 'none'}); the terms of sale name exactly one: a second member needs a text change and a new LEGAL_UPDATED`); return; }
  const name = styles[members[0]].name;
  for (const rel of files) {
    let text;
    try { text = readFileSync(join(root, rel), 'utf8'); } catch { continue; }
    const rows = [...text.matchAll(BLACK_ROW)];
    if (!rows.length) out.push(`${rel}: no row of the black price class found (the style check reads the terms tables)`);
    for (const r of rows) if (!r[1].includes(name)) out.push(`${rel}: the row "${r[1]}" prices the black class, whose one member is "${name}": the row must name it (a renamed or replaced style needs a text change and a new LEGAL_UPDATED)`);
    if (enforce && /\$\{MAX_EYES\}/.test(text)) out.push(`${rel}: prints the maximum number of eyes (\${MAX_EYES}): the terms print none (a build-time text cannot follow the catalogue)`);
    const digits = enforce ? /(?<![\w.])(\d{1,2})\s+(eyes|Augen|akys|akių|szem)(?![\p{L}])/iu.exec(text) : null;
    if (digits) out.push(`${rel}: prints a number of eyes ("${digits[0]}"): the terms print none (a build-time text cannot follow the catalogue)`);
    // a price row prints no list of styles (the art styles come from the run-time catalogue): the old constant is gone
    if (enforce && /\bconst ART\b/.test(text)) out.push(`${rel}: holds a list of art styles (const ART): the price rows name classes, the list is the run-time catalogue's`);
  }
}

/** The landing's pricing rows take the list of art styles and the eye limit only from the run-time tokens (enforced from WP12_RULES). */
export function checkRuntimeTokens(copy, out) {
  for (const [lang, c] of Object.entries(copy ?? {})) {
    const note = c?.pricing?.artBackgroundNote;
    if (typeof note === 'string' && !note.includes('{styles}')) out.push(`landing.${lang}.pricing.artBackgroundNote must be the token {styles} (the list of art styles comes from the run-time catalogue), not a written list`);
    const several = c?.pricing?.severalNote;
    if (typeof several === 'string' && !several.includes('{max}')) out.push(`landing.${lang}.pricing.severalNote must hold the token {max} (the number of eyes comes from the run-time catalogue), not a written number`);
  }
}

// ---------------------------------------------------------------------------------------------------- 8. plates, 9. byte budget, 10. function entries, 12. provenance
// These read the deployment tree (the plate files, vercel.json, the tile images, the reference-image deny list). A copy of the repository that
// has no vercel.json is not a deployment tree (the mutation copies of the registry suite carry api/, src/ and scripts/ only): they are skipped there.
export const BUDGET_MIB = 235;
/** The four functions that render (compose, master_compose, order and admin: order calls master_compose in process, admin recomposes through
 *  the same module): the only ones that carry the plates and the atlases. */
export const RENDERING = ['admin', 'compose', 'master_compose', 'order'];
const BASE_EXCLUDE = ['node_modules/**', 'dist/**', 'public/**', 'src/**', 'assets/**', 'scripts/**', 'suites/**', '.git/**', '*.html', '*.json', '*.ts', '*.md'];
const PLATES_EXCLUDE = ['api/_assets/plates/**', 'api/_assets/atlas/**'];
/** The only keys a function entry of vercel.json may carry: memory is not settable under Fluid compute, and includeFiles would undo the exclusions. */
const FUNCTION_KEYS = ['maxDuration', 'excludeFiles'];
export const PLATE_FAMILY_SOURCES = ['y2', 'uv', 'cx'];
const PLATE_FIELDS = ['family', 'since', 'until', 'usable', 'mono', 'kind', 'variables', 'score', 'k1', 'k4'];
const PLATE_OPTIONAL = ['void', 'void_diam', 'strong_angle', 'strength', 'fit', 'crisp', 'extra'];
const STORE_SEGMENT = /^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}$/;
const IMAGE_EXT = /\.(png|jpe?g|webp|gif|bmp|tiff?)$/i;
export const DENYLIST_FILE = 'scripts/hygiene_denylist.json';

const sha256File = (p) => createHash('sha256').update(readFileSync(p)).digest('hex');
const isFile = (p) => { try { return statSync(p).isFile(); } catch { return false; } };

function checkPlainValuesLoose(v, at, out) {
  if (v === null || typeof v === 'boolean') out.push(`${at}: null, true and false are not Python (use 0, 1, {} or [])`);
  else if (typeof v === 'string') { if (!asciiOnly(v)) out.push(`${at}: ASCII only: ${JSON.stringify(v)}`); }
  else if (Array.isArray(v)) v.forEach((x, i) => checkPlainValuesLoose(x, `${at}[${i}]`, out));
  else if (isObj(v)) for (const [k, x] of Object.entries(v)) { if (!asciiOnly(k)) out.push(`${at}: a key that is not ASCII: ${JSON.stringify(k)}`); checkPlainValuesLoose(x, `${at}.${k}`, out); }
}

function filesUnder(root, dir) {
  const out = [];
  const walk = (rel) => {
    let names = [];
    try { names = readdirSync(join(root, rel)); } catch { return; }
    for (const n of names) {
      if (n === '__pycache__') continue;
      const r = `${rel}/${n}`;
      if (statSync(join(root, r)).isDirectory()) walk(r); else if (!n.endsWith('.pyc')) out.push(r);
    }
  };
  walk(dir);
  return out;
}

/** Item 8: the baked plate library (api/_lib/plates_registry.py) is sound and the bundle holds exactly it. */
export function checkPlates(root, reg, engine, out) {
  const at0 = PLATES_FILE;
  let pr;
  try { pr = parsePlatesSource(readFileSync(join(root, PLATES_FILE), 'utf8')); } catch (e) {
    out.push(`${at0}: cannot be read (${e instanceof Error ? e.message : String(e)})`);
    return null;
  }
  if (pr.schema !== 1) out.push(`${at0}: PLATES_REGISTRY_SCHEMA is ${pr.schema}, this check knows 1`);
  if (pr.platesVersion !== reg.platesVersion) out.push(`${at0}: PLATES_VERSION ${pr.platesVersion} is not the registry's ${reg.platesVersion} (${STYLES_FILE}): one number names the library`);
  if (!(pr.dependenciesMib > 0 && pr.dependenciesMib < BUDGET_MIB)) out.push(`${at0}: DEPENDENCIES_MIB ${pr.dependenciesMib} must be the size of the Python packages in MiB (more than 0, less than the ${BUDGET_MIB} budget)`);
  if (!isObj(pr.families) || !isObj(pr.plates) || !isObj(pr.atlas)) { out.push(`${at0}: the literal must hold atlas, families and plates objects`); return null; }
  checkPlainValuesLoose(pr, at0, out);
  for (const [f, d] of Object.entries(pr.families)) {
    if (!/^P-[A-Z]{2}-[A-Z]+$/.test(f)) out.push(`${at0}: the family "${f}" must look like P-SN-CLOUD`);
    if (!isObj(d) || Object.keys(d).sort().join() !== 'release1,source,store4k' || ![0, 1].includes(d.store4k) || ![0, 1].includes(d.release1) || !PLATE_FAMILY_SOURCES.includes(d.source)) {
      out.push(`${at0}: the family "${f}" must be {store4k 0 or 1, release1 0 or 1, source ${PLATE_FAMILY_SOURCES.join(' or ')}}`);
    }
  }
  // the engine entries only name families and atlases that exist
  for (const [id, e] of Object.entries(engine)) {
    for (const f of e.plates ?? []) if (!(f in pr.families)) out.push(`${ENGINE_FILE} style "${id}" reads the plate family "${f}", which ${PLATES_FILE} does not have`);
    for (const a of e.atlas ?? []) if (!(a in pr.atlas)) out.push(`${ENGINE_FILE} style "${id}" reads the atlas "${a}", which ${PLATES_FILE} does not have`);
  }
  const shown = Object.entries(reg.styles).filter(([, d]) => [d.stage, ...Object.values(d.stage_by_eyes ?? {})].some((s) => s === 'preview' || s === 'live'));
  const usableByFamily = {};
  const wanted = new Set();
  for (const [id, p] of Object.entries(pr.plates)) {
    const at = `${at0} plate "${id}"`;
    if (!STORE_SEGMENT.test(id)) out.push(`${at}: the id must be a storage path segment (letters, digits, "_", "-", ".", at most 80 characters)`);
    if (!isObj(p)) { out.push(`${at}: not an object`); continue; }
    const have = Object.keys(p);
    const missing = PLATE_FIELDS.filter((f) => !have.includes(f)), extra = have.filter((f) => !PLATE_FIELDS.includes(f) && !PLATE_OPTIONAL.includes(f));
    if (missing.length || extra.length) { out.push(`${at}: fields missing ${missing.join(', ') || 'none'}, unknown ${extra.join(', ') || 'none'}`); continue; }
    if (!(p.family in pr.families)) { out.push(`${at}: the family "${p.family}" is not in families`); continue; }
    if (!id.startsWith(`${p.family}__`)) out.push(`${at}: the id must start with its family and two underscores`);
    if (!isInt(p.since) || p.since < 1 || p.since > pr.platesVersion) out.push(`${at}: since must be a version from 1 to ${pr.platesVersion}`);
    if (!isInt(p.until) || (p.until !== 0 && p.until <= p.since)) out.push(`${at}: until must be 0 (never retired) or a version after since`);
    if (![0, 1].includes(p.usable) || ![0, 1].includes(p.mono)) out.push(`${at}: usable and mono must be 1 or 0`);
    if (p.usable === 1) {
      usableByFamily[p.family] = (usableByFamily[p.family] ?? 0) + 1;
      if (!isObj(p.k1) || !STORE_SEGMENT.test(p.k1.file ?? '') || !isInt(p.k1.bytes) || !/^[0-9a-f]{64}$/.test(p.k1.sha256 ?? '') || p.k1.px !== 1024) out.push(`${at}: a usable plate has a 1K file {file, bytes, sha256, px 1024}`);
      else {
        const rel = `api/_assets/plates/${p.family}/${p.k1.file}`;
        wanted.add(rel);
        if (!isFile(join(root, rel))) out.push(`${rel}: the plate "${id}" is in the registry and its 1K file is not in the bundle`);
        else if (statSync(join(root, rel)).size !== p.k1.bytes) out.push(`${rel}: ${statSync(join(root, rel)).size} bytes, the registry says ${p.k1.bytes}`);
        else if (sha256File(join(root, rel)) !== p.k1.sha256) out.push(`${rel}: not the file the registry names (sha256 differs)`);
      }
      if (isObj(p.k4) && Object.keys(p.k4).length) {
        if (!pr.families[p.family].store4k) out.push(`${at}: the family keeps no 4K files in storage (store4k 0) but the plate has one`);
        if (!STORE_SEGMENT.test(p.k4.file ?? '') || !isInt(p.k4.bytes) || p.k4.bytes < 1 || p.k4.bytes > (16 << 20) || !/^[0-9a-f]{64}$/.test(p.k4.sha256 ?? '') || p.k4.px !== 4096) {
          out.push(`${at}: a 4K file is {file, bytes up to 16 MiB, sha256, px 4096}`);
        }
      }
    } else if ((isObj(p.k1) && Object.keys(p.k1).length) || (isObj(p.k4) && Object.keys(p.k4).length)) out.push(`${at}: a plate that is not usable ships no file (k1 and k4 are empty)`);
  }
  for (const rel of filesUnder(root, 'api/_assets/plates')) if (!wanted.has(rel)) out.push(`${rel}: a file in the plate bundle that no usable plate of ${PLATES_FILE} names (the library is the registry: nothing rides in unlisted)`);
  for (const [key, a] of Object.entries(pr.atlas)) {
    const rel = `api/_assets/atlas/${a?.file}`;
    if (!isObj(a) || !STORE_SEGMENT.test(a.file ?? '') || !isInt(a.bytes) || !/^[0-9a-f]{64}$/.test(a.sha256 ?? '')) out.push(`${at0}: the atlas "${key}" is {file, bytes, sha256}`);
    else if (!isFile(join(root, rel))) out.push(`${rel}: the atlas "${key}" is in the registry and its file is not in the bundle`);
    else if (statSync(join(root, rel)).size !== a.bytes || sha256File(join(root, rel)) !== a.sha256) out.push(`${rel}: not the file the registry names`);
  }
  for (const rel of filesUnder(root, 'api/_assets/atlas')) if (!Object.values(pr.atlas).some((a) => `api/_assets/atlas/${a?.file}` === rel)) out.push(`${rel}: a file in the atlas bundle that ${PLATES_FILE} does not name`);
  // a style shown to customers: its plate families have plates, and its tile images exist at both widths
  for (const [id, d] of shown) {
    for (const f of engine[id]?.plates ?? []) if (!usableByFamily[f]) out.push(`style "${id}" (stage preview or live) reads the plate family "${f}", which has no usable plate`);
    if (existsSync(join(root, 'public'))) {
      for (const w of [480, 800]) {
        const rel = `public/assets/atelier/style-${d.slug}-${w}.webp`;
        if (!isFile(join(root, rel))) out.push(`${rel}: the style "${id}" is shown to customers and has no tile image at ${w} px (the file name is the slug)`);
      }
    }
  }
  return pr;
}

/** Item 9: the files a rendering function bundles (everything under api/) plus the Python packages (the recorded figure) stay under the budget. */
export function checkByteBudget(root, pr, out, budget = BUDGET_MIB) {
  const files = filesUnder(root, 'api');
  const size = (rel) => statSync(join(root, rel)).size;
  const total = files.reduce((s, f) => s + size(f), 0);
  const plates = files.filter((f) => f.startsWith('api/_assets/plates/') || f.startsWith('api/_assets/atlas/')).reduce((s, f) => s + size(f), 0);
  const MIB = 1048576;
  const rendering = total / MIB + pr.dependenciesMib, other = (total - plates) / MIB + pr.dependenciesMib;
  if (rendering > budget) out.push(`a rendering function would hold ${rendering.toFixed(1)} MiB (api/ ${(total / MIB).toFixed(1)} MiB, with the plates ${(plates / MIB).toFixed(1)} MiB, plus the Python packages ${pr.dependenciesMib} MiB recorded in ${PLATES_FILE}): over the ${budget} MiB budget`);
  return { apiMib: total / MIB, platesMib: plates / MIB, rendering, other, budget };
}

/** Item 10: vercel.json names every function of api/ on its own, with no catch-all glob (two overlapping globs resolve in a way nobody has verified), and
 *  only the four rendering functions keep the plates and the atlases. */
export function checkFunctions(root, out, rendering = RENDERING) {
  let v;
  try { v = JSON.parse(readFileSync(join(root, 'vercel.json'), 'utf8')); } catch (e) { out.push(`vercel.json: cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`); return; }
  const fns = isObj(v.functions) ? v.functions : {};
  const handlers = readdirSync(join(root, 'api')).filter((n) => /^[^_.][^/]*\.py$/.test(n) && isFile(join(root, 'api', n))).map((n) => n.slice(0, -3)).sort();
  for (const h of handlers) if (!(`api/${h}.py` in fns)) out.push(`vercel.json: no functions entry for api/${h}.py (one entry per function: a catch-all glob leaves the size and the plates of each function to a rule nobody verified)`);
  for (const key of Object.keys(fns)) {
    const m = /^api\/([^/*?{}[\]]+)\.py$/.exec(key);
    if (!m) out.push(`vercel.json: the functions pattern "${key}" is a glob; name each function (api/<name>.py)`);
    else if (!handlers.includes(m[1])) out.push(`vercel.json: the functions entry "${key}" names no function of api/`);
  }
  for (const r of rendering) if (!handlers.includes(r)) out.push(`the check's list of rendering functions names "${r}", which is not a function of api/`);
  const durations = new Set();
  for (const h of handlers) {
    const cfg = fns[`api/${h}.py`];
    if (!isObj(cfg)) continue;
    durations.add(cfg.maxDuration);
    for (const k of Object.keys(cfg)) {
      if (FUNCTION_KEYS.includes(k)) continue;
      out.push(k === 'includeFiles'
        ? `vercel.json api/${h}.py: includeFiles puts files back into the function that excludeFiles took out (the plates and atlases of a function that never renders, the scripts, the suites): the entry holds only ${FUNCTION_KEYS.join(' and ')}`
        : `vercel.json api/${h}.py: the key "${k}" is not one this check reads (it knows ${FUNCTION_KEYS.join(' and ')}): a setting that changes what a function holds or how much it may use must be added to the check with its rule first`);
    }
    const ex = typeof cfg.excludeFiles === 'string' ? cfg.excludeFiles : '';
    const m = /^\{(.*)\}$/.exec(ex);
    const have = (m ? m[1] : ex).split(',').map((s) => s.trim()).filter(Boolean).sort();
    const want = [...BASE_EXCLUDE, ...(rendering.includes(h) ? [] : PLATES_EXCLUDE)].sort();
    if (have.join() !== want.join()) {
      const miss = want.filter((x) => !have.includes(x)), more = have.filter((x) => !want.includes(x));
      out.push(`vercel.json api/${h}.py: excludeFiles must be ${rendering.includes(h) ? 'the base list' : 'the base list and the plates and atlases (this function never renders)'} (missing ${miss.join(', ') || 'none'}, unexpected ${more.join(', ') || 'none'})`);
    }
  }
  if (durations.size > 1) out.push(`vercel.json: the functions do not share one maxDuration (${[...durations].join(', ')})`);
  // item 13: the one duration constant
  let dur = null;
  try { const m = /^DURATION_S\s*=\s*(\d+)\b/m.exec(readFileSync(join(root, 'api', '_lib', 'duration.py'), 'utf8')); dur = m ? Number(m[1]) : null; } catch { dur = null; }
  if (dur === null) out.push('api/_lib/duration.py: cannot be read, or holds no line "DURATION_S = <seconds>" (the one duration constant: vercel.json maxDuration is held equal to it)');
  else {
    for (const h of handlers) {
      const cfg = fns[`api/${h}.py`];
      if (isObj(cfg) && cfg.maxDuration !== dur) {
        out.push(`vercel.json api/${h}.py: maxDuration ${cfg.maxDuration} is not api/_lib/duration.py DURATION_S ${dur}: change both together (the work budget, every lease and the chain's waits derive from DURATION_S; a longer function with the old leases lets a second caller take over a render that is still alive)`);
      }
    }
  }
}

/** Item 12 (provenance): no repository image is byte for byte one of the owner's reference works or one of the calibration irises (volunteers' eyes,
 *  biometric-adjacent): the originals never enter the repository. The deny list holds hashes and labels only (scripts/make_denylist.py makes it from the
 *  scratch tree). A tripwire against the original bytes, not a detector of derived images. */
export function checkProvenance(root, out, listFile = DENYLIST_FILE) {
  let deny;
  try { deny = JSON.parse(readFileSync(join(root, listFile), 'utf8')).sha256; } catch (e) { out.push(`${listFile}: cannot be read (${e instanceof Error ? e.message : String(e)})`); return 0; }
  if (!isObj(deny) || !Object.keys(deny).length || Object.keys(deny).some((h) => !/^[0-9a-f]{64}$/.test(h))) { out.push(`${listFile}: sha256 must map sha256 hashes to labels`); return 0; }
  let n = 0;
  const walk = (rel) => {
    let names = [];
    try { names = readdirSync(join(root, rel)); } catch { return; }
    for (const name of names) {
      if (['node_modules', '.git', '.vercel', 'dist', '__pycache__', 'private', 'out'].includes(name) || (rel === '' && name.startsWith('.'))) continue;
      const r = rel ? `${rel}/${name}` : name;
      const st = statSync(join(root, r));
      if (st.isDirectory()) walk(r);
      else if (IMAGE_EXT.test(name) && st.size > 0) {
        n++;
        const h = sha256File(join(root, r));
        if (h in deny) out.push(`${r}: is byte for byte "${deny[h]}", a reference work or a calibration iris that never enters the repository (the originals are not committed: provenance, T20 of the plan)`);
      }
    }
  };
  walk('');
  return n;
}

/** The one line the build prints for items 8 and 9, or "" when the tree has none (a copy without vercel.json). */
export function describePlates(root) {
  try {
    const pr = parsePlatesSource(readFileSync(join(root, PLATES_FILE), 'utf8'));
    const usable = Object.values(pr.plates).filter((p) => p.usable === 1);
    const k1 = usable.reduce((s, p) => s + p.k1.bytes, 0) / 1048576, k4 = usable.reduce((s, p) => s + (p.k4?.bytes ?? 0), 0) / 1048576;
    const b = checkByteBudget(root, pr, []);
    return `plates ok: ${Object.keys(pr.plates).length} plates, ${usable.length} usable (1K files ${k1.toFixed(1)} MiB in the bundle, 4K files ${k4.toFixed(0)} MiB for storage); a rendering function ${b.rendering.toFixed(1)} MiB and any other ${b.other.toFixed(1)} MiB of ${b.budget} (Python packages ${pr.dependenciesMib} MiB, an estimate until V1)`;
  } catch { return ''; }
}

// ---------------------------------------------------------------------------------------------------- the whole check
/** Every problem found, as sentences ([] when the registry is sound). load(path): a module of src/ through Vite's module runner
 *  (vite.config.ts); without it the checks that need the page code (the pages' reading of the registry and of the layout words, 4, 6) are left out. */
export async function checkStyles(root, load) {
  const out = [];
  let reg, engine, names;
  try { reg = parseRegistrySource(readFileSync(join(root, STYLES_FILE), 'utf8')); } catch (e) {
    return [`${STYLES_FILE}: the STYLES literal cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`];
  }
  try { engine = parseEngineSource(readFileSync(join(root, ENGINE_FILE), 'utf8')); } catch (e) {
    return [`${ENGINE_FILE}: the ENGINE literal cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`];
  }
  try { names = parseLayoutNamesSource(readFileSync(join(root, LAYOUTS_FILE), 'utf8')); } catch (e) {
    return [`${LAYOUTS_FILE}: the LAYOUT_NAMES literal cannot be read as JSON (${e instanceof Error ? e.message : String(e)})`];
  }
  checkLayoutNames(names, out);
  checkPublic(reg, out, isObj(names) ? Object.keys(names) : []);
  checkEngine(reg, engine, out);
  if (out.length) return out;       // nothing below makes sense on a broken registry
  checkLegacyTable(root, reg, out);
  checkLiteralIds(root, Object.keys(reg.styles), out);
  checkTerms(root, reg.styles, out);
  if (existsSync(join(root, 'vercel.json'))) {       // a deployment tree: the plates, the byte budget, the function entries, the provenance
    const pr = checkPlates(root, reg, engine, out);
    if (pr) checkByteBudget(root, pr, out);
    checkFunctions(root, out);
    checkProvenance(root, out);
  }
  let surfaces = null;
  let client = null;
  let pageNames;
  if (load) {
    const [stylesTs, layoutsTs, markets, landing, tryCopy, orderCopy] = await Promise.all([
      load('./src/shared/styles.ts'), load('./src/shared/layouts.ts'), load('./src/shared/markets.ts'), load('./src/landing/copy.ts'), load('./src/try/copy.ts'),
      load('./src/order/copy.ts'),
    ]);
    client = markets;
    pageNames = layoutsTs.LAYOUT_NAMES;
    if (!sameJson(stylesTs.STYLES, reg.styles)) out.push('src/shared/styles.ts reads another STYLES than api/_lib/styles_registry.py holds');
    if (stylesTs.DEFAULT_STYLE !== reg.defaultStyle) out.push(`src/shared/styles.ts reads DEFAULT_STYLE "${stylesTs.DEFAULT_STYLE}", not "${reg.defaultStyle}"`);
    if (stylesTs.STYLES_SCHEMA !== reg.schema || stylesTs.PLATES_VERSION !== reg.platesVersion) out.push('src/shared/styles.ts reads another STYLES_SCHEMA or PLATES_VERSION');
    surfaces = [['landing', landing.COPY], ['try', tryCopy.COPY], ['order', orderCopy.ORDER_COPY]];
    checkCopyDictionaries(surfaces, reg.styles, out);
    if (WP12_RULES) {
      checkNumberOfStyles(surfaces, out, indexTexts(root));
      checkRuntimeTokens(landing.COPY, out);
    }
  }
  checkLayouts(root, reg.styles, names, out, pageNames);
  checkPriceRules(root, reg.styles, client, out);
  return dedupe(out);
}

/** One line for the log: how many styles, at which stages, and the registry hash (item 11). */
export function describeRegistry(root) {
  const reg = parseRegistrySource(readFileSync(join(root, STYLES_FILE), 'utf8'));
  const engine = parseEngineSource(readFileSync(join(root, ENGINE_FILE), 'utf8'));
  const by = {};
  for (const d of Object.values(reg.styles)) by[d.stage] = (by[d.stage] ?? 0) + 1;
  const stages = STAGES.filter((s) => by[s]).map((s) => `${by[s]} ${s}`).join(', ');
  const layouts = Object.keys(parseLayoutNamesSource(readFileSync(join(root, LAYOUTS_FILE), 'utf8'))).length;
  return `styles registry ok: ${Object.keys(reg.styles).length} ids (${stages}), registry hash ${registryHash(reg, engine)}; ${layouts} layouts named in ${LAYOUT_LANGS.join(', ')}`;
}

// `node scripts/check_styles.mjs` (npm run check:styles): loads src/ through Vite's module runner, exit code 1 on any problem
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  const require = createRequire(join(root, 'package.json'));
  const { runnerImport } = await import(pathToFileURL(require.resolve('vite')).href);
  const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root })).module;
  const problems = await checkStyles(root, load);
  if (problems.length) {
    console.error(`style check FAILED (${problems.length}):\n  ${problems.join('\n  ')}`);
    process.exit(1);
  }
  console.log(describeRegistry(root));
  const plates = describePlates(root);
  if (plates) console.log(plates);
}
