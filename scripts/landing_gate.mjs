// The landing page's RELEASE GATE: the page must never promise what the engine cannot sell. It replaces the first gate of the landing team ("a production build
// fails while any of the 16 tiles cannot be ordered"), which no owner decision could ever satisfy: what can be bought is a RUN-TIME fact (the registry's ceiling per
// number of eyes, then the owner's tick in the admin page, which needs no build), so a build can only hold the page to the honest rule:
//
//   A tile that cannot be bought is shown as Soon, with no price; a tile that can be bought shows its price. The page says nothing else about what is for sale.
//
// The gate holds the page to that rule in two parts, both pure (they read what they are given and nothing else):
//
//   1. the structure (releaseGate): every one of the gallery's tiles stands for a style of the registry (src/landing/tileStyle.ts) that takes that many eyes and is
//      not retired. A style that is only planned (no engine yet: Reflection, Radiance Duo, Clean Family ...), in the laboratory or at preview is FINE: its tile says
//      Soon. A tile with no row, a style the registry does not have, a retired style or a count of eyes the style does not take is a tile of something that does
//      not exist, so it is blocked.
//   2. the promise (promiseGate): the page is RENDERED, by the very components the live page uses (src/landing/shell/gate.tsx), in every state of the catalogue
//      a visitor can meet (gateInputs: closed, ordering open with nothing ticked, one style ticked, every live ceiling ticked, the server not reachable) and in
//      the four languages, and the markup is read against the registry and the catalogue's answer, independently of the page's own helpers:
//        * a tile whose style the catalogue does not list live for its number of eyes (or while ordering is closed) carries the Soon chip of its language and no price;
//        * a tile that can be bought carries its price (an under-sell is a notice, not a promise);
//        * every name a tile prints is the registry's name of the style the tile stands for, and a name of no style of the registry is refused;
//        * the price table prints a price in a row only when the catalogue lists a style of that class (or count of eyes) live, says Soon in the others, and names in
//          the rows of styles only styles whose tiles can be bought;
//        * where nothing can be bought, no price stands anywhere in the table or on a tile;
//        * the line a group adds under its intro follows how many of its tiles can be bought;
//        * every tile has its picture (for every eye colour, in the two widths): a missing picture is an error in every build, not a matter of promises.
// A blocked tile or a broken promise is a notice in a local or preview build and an error in a PRODUCTION build (VERCEL_ENV=production, or LANDING_GATE=strict
// anywhere). There is deliberately no switch that turns a production gate off: the way to a production build is to make the page tell the truth.
import { ceilingOf } from './styles_source.mjs';
import { checkoutAnswer, firstLiveOneEyeStyle } from './lib/stubapi.mjs';

const has = (o, k) => o !== null && typeof o === 'object' && Object.prototype.hasOwnProperty.call(o, k);

/** Is the gate an error in this environment? A production deploy (Vercel sets VERCEL_ENV=production) or an explicit LANDING_GATE=strict: yes. A local build, a
 *  preview deploy: a notice only. */
export function gateIsStrict(env) {
  return env.LANDING_GATE === 'strict' || env.VERCEL_ENV === 'production';
}

// ------------------------------------------------------------------------------------------------------------------------ 1. the structure
/** The gate table against the registry: { total, live, preview, lab, planned, blocked: [{ tile, reason }] }. One row per tile of the gallery; live, preview, lab and
 *  planned list the tile ids by the registry's CEILING for the tile's style and number of eyes (the most the owner can ever switch on: live means he can tick it live
 *  in the admin page, the others mean the page shows the tile as Soon until the ceiling is raised in the registry); blocked lists the tiles that stand for nothing
 *  that exists, with the reason. styles: the registry's STYLES; tileStyle: TILE_STYLE of src/landing/tileStyle.ts; gallery: GALLERY of src/landing/assets.data.ts. Pure. */
export function releaseGate(styles, tileStyle, gallery) {
  const gate = { total: 0, live: [], preview: [], lab: [], planned: [], blocked: [] };
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
        else if (ceiling === 'retired') reason = `"${row.id}" is retired: it can never be bought again, so its tile could never say Soon honestly`;
        else if (ceiling === 'live' || ceiling === 'preview' || ceiling === 'lab' || ceiling === 'planned') gate[ceiling].push(it.id);
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
  return `${gate.total} tiles: ${part('with a live ceiling', gate.live)}, ${part('at preview', gate.preview)}, ${part('in the laboratory', gate.lab)}, ${part('only planned', gate.planned ?? [])}, ${gate.blocked.length} of something that does not exist`;
}

// ------------------------------------------------------------------------------------------------------------------------ 2. the promise
/** The states of the catalogue the gate renders the page for: what GET /api/checkout can answer, made from the registry (scripts/lib/stubapi.mjs). null is a server
 *  that could not be read (the page keeps the build's own fallback). */
export function gateInputs(root) {
  const one = firstLiveOneEyeStyle(root);
  return [
    { name: 'closed', answer: checkoutAnswer(root, { open: false }) },
    { name: 'ordering open, nothing ticked', answer: checkoutAnswer(root, { open: true, ticked: false }) },
    { name: 'closed, every live ceiling ticked', answer: checkoutAnswer(root, { open: false, ticked: true }) },
    ...(one ? [{ name: 'one style ticked', answer: checkoutAnswer(root, { open: true, ticked: [one] }) }] : []),
    { name: 'every live ceiling ticked', answer: checkoutAnswer(root, { open: true, ticked: true }) },
    { name: 'server not reachable', answer: null },
  ];
}

const decode = (s) => s.replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const text = (html) => decode(html.replace(/<[^>]*>/g, ''));

/** What the catalogue's answer says can be bought: { open, live: Map id -> Set of eye counts }. The page's own reading (readCatalogue, saleCatalogue) is NOT used. */
function reading(answer) {
  const live = new Map();
  const ok = answer !== null && typeof answer === 'object' && !Array.isArray(answer);
  if (ok && Array.isArray(answer.styles)) {
    for (const s of answer.styles) {
      if (!s || typeof s.id !== 'string' || !s.stages || typeof s.stages !== 'object') continue;
      for (const [n, stage] of Object.entries(s.stages)) if (stage === 'live') { if (!live.has(s.id)) live.set(s.id, new Set()); live.get(s.id).add(Number(n)); }
    }
  }
  const open = ok && answer.ok !== false && answer.open === true && Number.isInteger(answer.orderable_max_eyes) && answer.orderable_max_eyes >= 1;
  return { open, live };
}

/** A tile's markup: its state attribute, the name in its heading, the Soon chip's words (or null) and whether it prints a price. */
export function readTile(html) {
  const state = /\sdata-state="([^"]*)"/.exec(html);
  const name = /<h3>([\s\S]*?)<\/h3>/.exec(html);
  const chip = /<span class="lp-soon">([\s\S]*?)<\/span>/.exec(html);
  return { state: state ? state[1] : null, name: name ? text(name[1]) : null, chip: chip ? text(chip[1]) : null, price: /<b>/.test(html) };
}

/** The hero's price line: whether it is held back (inert and invisible) and what it says. */
export function readHero(html) {
  const m = /<li class="lp-price"([^>]*)>([\s\S]*?)<\/li>/.exec(html);
  if (!m) return null;
  return { held: /\sinert(=|\s|$)/.test(m[1]) || /^inert/.test(m[1].trim()), text: text(m[2]) };
}

/** The rows of the price table's markup: [{ title, note, value, soon, price }] in the page's order (free, black, art, two, more). */
export function readTable(html) {
  const rows = [];
  const re = /<div class="lp-prow[^"]*"[^>]*><div><b>([\s\S]*?)<\/b><small>([\s\S]*?)<\/small><\/div><div class="lp-pv">([\s\S]*?)<\/div><\/div>/g;
  for (const m of html.matchAll(re)) {
    rows.push({ title: text(m[1]), note: text(m[2]), value: text(m[3]), soon: /class="lp-soon"/.test(m[3]), price: /\d/.test(text(m[3])) });
  }
  return rows;
}

/** The promise: `rendered` is renderGate()'s output (src/landing/shell/gate.tsx) for `inputs` (gateInputs), styles the registry's, tileStyle TILE_STYLE, gallery GALLERY.
 *  Returns { promises, underSells, pictures }: broken promises (an error in a production build), places where the page offers less than it could sell (a notice) and
 *  missing pictures (an error in every build). Pure. */
export function promiseGate(rendered, inputs, styles, tileStyle, gallery) {
  const promises = new Set();
  const underSells = new Set();
  const pictures = [...(rendered?.pictures ?? [])];
  const tiles = [];
  for (const g of gallery?.groups ?? []) for (const it of gallery[g] ?? []) tiles.push({ group: g, id: it.id, kind: it.price });
  const registryNames = new Set(Object.values(styles ?? {}).map((d) => d.name));
  const rowOf = (id) => (has(tileStyle, id) ? tileStyle[id] : null);
  const styleOf = (row) => (row && has(styles, row.id) ? styles[row.id] : null);
  if (!rendered?.scenarios?.length || rendered.scenarios.length !== inputs.length) {
    promises.add('the gate rendered no state of the catalogue (src/landing/shell/gate.tsx gave nothing or another number of states than scripts/landing_gate.mjs gateInputs)');
    return { promises: [...promises], underSells: [], pictures };
  }
  inputs.forEach((input, i) => {
    const sc = rendered.scenarios[i];
    const { open, live } = reading(input.answer);
    const at = `${input.name}`;
    if (sc.open !== open) promises.add(`${at}: the page treats ordering as ${sc.open ? 'open' : 'closed'} but the catalogue says ${open ? 'open' : 'closed'}`);
    const buyable = (id, n) => open && live.has(id) && live.get(id).has(n);
    // the groups' lines
    for (const g of gallery?.groups ?? []) {
      const ids = (gallery[g] ?? []).map((t) => t.id);
      const n = ids.filter((id) => { const r = rowOf(id); return r && buyable(r.id, r.eyes); }).length;
      const want = !open ? null : n === 0 ? 'soon' : n < ids.length ? 'more' : null;
      if ((sc.lines?.[g] ?? null) !== want) promises.add(`${at}: the group "${g}" adds the line "${sc.lines?.[g] ?? null}" under its intro, ${n} of its ${ids.length} tiles can be bought so it should add "${want}"`);
    }
    for (const [lang, view] of Object.entries(sc.langs ?? {})) {
      // the tiles
      const byId = new Map(view.tiles.map((t) => [t.id, t]));
      for (const tile of tiles) {
        const out = byId.get(tile.id);
        if (!out) { promises.add(`${at}: the tile "${tile.id}" was not rendered in ${lang}`); continue; }
        const row = rowOf(tile.id);
        const d = styleOf(row);
        const want = !!(row && d && buyable(row.id, row.eyes));
        const got = readTile(out.html);
        const label = `the tile "${tile.id}"${row ? ` (${row.id}, ${row.eyes} eye${row.eyes === 1 ? '' : 's'})` : ''}`;
        if (!d) promises.add(`${at}: ${label} stands for no style of the registry`);
        else if (got.name !== d.name) promises.add(`${at}: ${label} is called "${got.name}", the registry's name of ${row.id} is "${d.name}"`);
        if (got.name !== null && got.name !== '' && !registryNames.has(got.name)) promises.add(`${at}: ${label} prints the name "${got.name}", which is no style name of the registry`);
        if (got.name === '' || got.name === null) promises.add(`${at}: ${label} prints no name`);
        if (!want) {
          if (got.chip === null) promises.add(`${at}: ${label} cannot be bought${open ? ' now' : ' (ordering is closed)'} but does not say Soon`);
          else if (got.chip !== view.soon) promises.add(`${at}: ${label} cannot be bought but its chip says "${got.chip}", not "${view.soon}" (${lang})`);
          if (got.price) promises.add(`${at}: ${label} cannot be bought but prints a price`);
          if (got.state !== 'soon') promises.add(`${at}: ${label} cannot be bought but is marked "${got.state}"`);
        } else {
          if (!got.price || got.chip !== null || got.state !== 'sale') underSells.add(`${at}: ${label} can be bought but shows ${got.price ? 'a price' : 'no price'}${got.chip !== null ? ' and says Soon' : ''}`);
        }
      }
      // the hero's "Digital file from" line is shown only while some style can be bought for one eye
      const hero = readHero(view.hero ?? '');
      const heroWant = open && [...live].some(([, set]) => set.has(1));
      if (!hero) promises.add(`${at}: the hero has no price line to read (${lang})`);
      else if (!heroWant && !hero.held) promises.add(`${at}: no style can be bought for one eye but the hero says "${hero.text}"`);
      else if (heroWant && (hero.held || !/\d/.test(hero.text))) underSells.add(`${at}: a style can be bought for one eye but the hero's price line is ${hero.held ? 'held back' : 'without a price'}`);
      // the price table
      const rows = readTable(view.table);
      if (rows.length !== 5) { promises.add(`${at}: the price table has ${rows.length} rows, the gate reads 5 (free, black, art, two eyes, three eyes)`); continue; }
      const liveOne = (cls) => open && [...live].some(([id, set]) => set.has(1) && styles[id]?.price_class === cls);
      const liveFor = (n) => open && [...live].some(([, set]) => set.has(n));
      const wantRow = { black: liveOne('black'), art: liveOne('art'), two: liveFor(2), more: liveFor(3) };
      const names = Object.keys(wantRow);
      names.forEach((key, k) => {
        const r = rows[k + 1];
        const label = `the price table row "${r.title}" (${key})`;
        if (wantRow[key]) {
          if (!r.price || r.soon) underSells.add(`${at}: ${label} can be bought but shows ${r.price ? 'a price' : 'no price'}${r.soon ? ' and says Soon' : ''}`);
        } else {
          if (!r.soon) promises.add(`${at}: ${label} cannot be bought but does not say Soon (${lang})`);
          else if (r.value !== view.soon) promises.add(`${at}: ${label} cannot be bought but its chip says "${r.value}", not "${view.soon}" (${lang})`);
          if (r.price) promises.add(`${at}: ${label} cannot be bought but prints a price`);
        }
      });
      // the styles the art and two-eyes rows name are the ones whose tiles can be bought (a name of a style that cannot be bought is a promise)
      for (const [k, kind] of [[2, 'art'], [3, 'two']]) {
        const kindTiles = tiles.filter((t) => (kind === 'art' ? t.group === 'one' && t.kind === 'art' : t.group === 'two'));
        const sale = new Set(), other = new Set();
        for (const t of kindTiles) {
          const r = rowOf(t.id), d = styleOf(r);
          if (!d) continue;
          (buyable(r.id, r.eyes) ? sale : other).add(d.name);
        }
        for (const name of sale) other.delete(name);
        const note = rows[k].note;
        for (const name of other) if (note.includes(name)) promises.add(`${at}: the price table row "${rows[k].title}" names "${name}", a style that cannot be bought`);
        if (wantRow[kind === 'art' ? 'art' : 'two']) for (const name of sale) if (!note.includes(name)) underSells.add(`${at}: the price table row "${rows[k].title}" can be bought but does not name "${name}"`);
      }
      // where nothing can be bought, no price stands anywhere in the table (the free row aside) or on a tile
      if (!live.size || !open) {
        const rest = rows.slice(1);
        if (rest.some((r) => /\d/.test(r.value) || /\d/.test(r.note))) promises.add(`${at}: nothing can be bought but the price table prints a number`);
        if (view.tiles.some((t) => readTile(t.html).price)) promises.add(`${at}: nothing can be bought but a tile prints a price`);
      }
    }
  });
  return { promises: [...promises], underSells: [...underSells], pictures };
}
