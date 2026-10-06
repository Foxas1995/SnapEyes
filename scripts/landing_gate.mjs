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
//   2. the promise (promiseGate): the page is RENDERED, by the very components the live page uses, WIRED as the live page is (src/landing/shell/gate.tsx: the styles chapter of
//      every group, the price table, the hero, the FAQ; the page's own asking code runs against a stand-in server), in every state of the catalogue a visitor can meet
//      (gateInputs: closed, ordering open with nothing ticked, one style ticked, every live ceiling ticked, every style live beyond the ceilings, the server not reachable)
//      and in the four languages, and the markup is read against the registry, the catalogue's answer and the server's price rule, independently of the page's own helpers:
//        * a tile whose style the catalogue does not list live for its number of eyes (or while ordering is closed) carries the Soon chip of its language and no price;
//        * a tile that can be bought carries its price (an under-sell is a notice, not a promise), and the VALUE of every price the page prints (a tile, a row of the table, the
//          hero's "from", the several-eyes card) is the one the server's rule gives (src/shared/markets.ts priceMinor) for the style the REGISTRY says it is: a price of the wrong
//          class or the wrong count of eyes is a broken promise as much as a price that should not be there;
//        * every name a tile prints is the registry's name of the style the tile stands for, and a name of no style of the registry is refused;
//        * the price table prints a price in a row only when the catalogue lists a style of that class (or count of eyes) live, says Soon in the others, and names in
//          the rows of styles only styles whose tiles can be bought;
//        * where nothing can be bought, no price stands anywhere in the table or on a tile;
//        * the line a group adds under its intro and the several-eyes card of the pairs and the families follow how many of the group's tiles and which counts of eyes can be bought;
//        * every answer of the FAQ is the wording the state calls for (the open wording only while ordering is open, a number of eyes only up to what can be sold);
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
 *  that could not be read (the page keeps the build's own fallback). 'every style live' is a state no server answers today (every style of the registry live for every
 *  number of eyes it takes): the page must be honest in it too, and it is the only state in which the several-eyes ladder, the combo card's price and the pairs' prices are printed. */
export function gateInputs(root) {
  const one = firstLiveOneEyeStyle(root);
  return [
    { name: 'closed', answer: checkoutAnswer(root, { open: false }) },
    { name: 'ordering open, nothing ticked', answer: checkoutAnswer(root, { open: true, ticked: false }) },
    { name: 'closed, every live ceiling ticked', answer: checkoutAnswer(root, { open: false, ticked: true }) },
    ...(one ? [{ name: 'one style ticked', answer: checkoutAnswer(root, { open: true, ticked: [one] }) }] : []),
    { name: 'every live ceiling ticked', answer: checkoutAnswer(root, { open: true, ticked: true }) },
    { name: 'every style live, beyond the ceilings', answer: checkoutAnswer(root, { open: true, ticked: 'beyond' }) },
    { name: 'server not reachable', answer: null },
  ];
}

const decode = (s) => s.replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
const text = (html) => decode(html.replace(/<[^>]*>/g, ''));
const norm = (s) => s.replace(/\s+/g, ' ').trim();
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

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

/** The price a tile prints (the words inside its <b>), or null. */
export function readTilePrice(html) {
  const m = /<b>([\s\S]*?)<\/b>/.exec(html);
  return m ? norm(text(m[1])) : null;
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

/** The line a group adds under its intro ({ kind: 'soon' | 'more', text }), or null when it adds none. A line whose span has no kind (the guard that leaves the span out
 *  when there is no line is gone) has the kind ''. */
export function readLine(html) {
  const m = /<span class="lp-gline"([^>]*)>([\s\S]*?)<\/span>/.exec(html);
  return m ? { kind: /\sdata-line="([^"]*)"/.exec(m[1])?.[1] ?? '', text: norm(text(m[2])) } : null;
}

/** The card of the pairs and the families ({ title, body }), or null when the group has none. */
export function readCombo(html) {
  const m = /<div class="lp-combo"><h3>([\s\S]*?)<\/h3><p>([\s\S]*?)<\/p>/.exec(html);
  return m ? { title: norm(text(m[1])), body: norm(text(m[2])) } : null;
}

/** The questions of the FAQ's markup: [{ id, q, a }] in the page's order. */
export function readFaq(html) {
  const out = [];
  const re = /<details id="faq-([^"]*)"[^>]*><summary[^>]*>([\s\S]*?)<\/summary><p>([\s\S]*?)<\/p><\/details>/g;
  for (const m of html.matchAll(re)) out.push({ id: m[1], q: norm(text(m[2])), a: norm(text(m[3])) });
  return out;
}

/** The sentence of the notice bar, or null. */
export function readBar(html) {
  const m = /<span id="barText">([\s\S]*?)<\/span>/.exec(html);
  return m ? norm(text(m[1])) : null;
}

/** The pricing block's notice and its payment line ({ notice, pay }, each null when the block has none). */
export function readNotice(html) {
  const n = /<p class="lp-notice"[^>]*>([\s\S]*?)<\/p>/.exec(html);
  const p = /<p class="lp-pay-open">([\s\S]*?)<\/p>/.exec(html);
  return { notice: n ? norm(text(n[1])) : null, pay: p ? norm(text(p[1])) : null };
}

/** The sentence under each step of how it works, in order. */
export function readSteps(html) {
  return [...html.matchAll(/<div class="lp-step-body"><span class="lp-num">0\d<\/span><h3>[\s\S]*?<\/h3><p>([\s\S]*?)<\/p>/g)].map((m) => norm(text(m[1])));
}

/** A copy text (with its {tokens}) as a pattern for what the page printed: the facts and prices of the copy are anything, {max} is the number of eyes the state allows. */
function faqPattern(raw, maxText) {
  const parts = norm(raw).split(/(\{[A-Za-z0-9_]+\})/);
  const src = parts.map((p) => (/^\{[A-Za-z0-9_]+\}$/.test(p) ? (p === '{max}' && maxText !== null ? escapeRe(maxText) : '.*?') : escapeRe(p))).join('');
  return new RegExp(`^${src}$`);
}

/** The promise: `rendered` is renderGate()'s output (src/landing/shell/gate.tsx) for `inputs` (gateInputs), with `expect` added by the caller (scripts/check_landing_assets.mjs
 *  renderLanding): for each language, the price of each style of the registry for each number of eyes it takes, by the server's own price rule ({ minor, text }), and the price
 *  of each further eye, so that a price the page prints is held to its VALUE and not only to its being there. styles is the registry's, tileStyle TILE_STYLE, gallery GALLERY.
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
  if (!rendered.expect || typeof rendered.expect !== 'object') {
    promises.add('the gate was given no expected prices (scripts/check_landing_assets.mjs renderLanding works them out from the server\'s price rule): it cannot tell what a price must say');
    return { promises: [...promises], underSells: [], pictures };
  }
  // the price the server's rule gives for n eyes of a style of the registry, in a language ({ minor, text }), or null
  // (the page writes a space of money as a no-break space: both sides are compared with every space made plain)
  const cell = (c) => (c ? { minor: c.minor, text: norm(c.text) } : null);
  const priceOf = (lang, id, n) => (id ? cell(rendered.expect?.[lang]?.price?.[id]?.[String(n)]) : null);
  // a style of the registry (of a price class, or any) that takes n eyes: the price of more than one eye does not depend on the class, so any style stands in for it
  const classId = (cls, n) => Object.entries(styles ?? {}).find(([, d]) => d.legacy === 0 && (cls === null || d.price_class === cls) && d.eyes[0] <= n && n <= d.eyes[1])?.[0] ?? null;
  inputs.forEach((input, i) => {
    const sc = rendered.scenarios[i];
    const { open, live } = reading(input.answer);
    const at = `${input.name}`;
    if (sc.open !== open) promises.add(`${at}: the page treats ordering as ${sc.open ? 'open' : 'closed'} but the catalogue says ${open ? 'open' : 'closed'}`);
    const buyable = (id, n) => open && live.has(id) && live.get(id).has(n);
    // the counts of eyes some style can be bought for now, the most of them, and the several-eyes ladder: every count from two eyes up to that many (0 when two eyes cannot be bought)
    const eyesLive = new Set();
    if (open) for (const set of live.values()) for (const n of set) eyesLive.add(n);
    const maxEyes = eyesLive.size ? Math.max(...eyesLive) : 0;
    let several = 1;
    while (eyesLive.has(several + 1)) several += 1;
    if (several < 2) several = 0;
    // for every group: how many of its tiles can be bought
    const bought = {};
    for (const g of gallery?.groups ?? []) {
      const ids = (gallery[g] ?? []).map((t) => t.id);
      bought[g] = { n: ids.filter((id) => { const r = rowOf(id); return r && buyable(r.id, r.eyes); }).length, total: ids.length };
    }
    for (const [lang, view] of Object.entries(sc.langs ?? {})) {
      const further = cell(rendered.expect?.[lang]?.further);
      // the groups: the line under the intro and the combo card, read from the markup of the styles chapter
      for (const g of gallery?.groups ?? []) {
        const html = view.groups?.[g];
        if (typeof html !== 'string' || !html) { promises.add(`${at}: the styles chapter of the group "${g}" was not rendered in ${lang}`); continue; }
        const { n, total } = bought[g];
        const wantKind = !open ? null : n === 0 ? 'soon' : n < total ? 'more' : null;
        const wantWords = wantKind === 'soon' ? view.words.severalSoon : view.words.moreSoon;
        const line = readLine(html);
        if ((line?.kind ?? null) !== wantKind) promises.add(`${at}: the group "${g}" adds the line "${line?.kind ?? null}" under its intro, ${n} of its ${total} tiles can be bought so it should add "${wantKind}" (${lang})`);
        else if (line && line.text !== wantWords) promises.add(`${at}: the group "${g}" says "${line.text}" under its intro, the words of the "${wantKind}" line are "${wantWords}" (${lang})`);
        const combo = readCombo(html);
        // a group whose tiles all take two eyes or more has the card (the page's `wide` groups): a card the gate cannot read would be a card it cannot hold to the truth
        const multi = (gallery[g] ?? []).length > 0 && (gallery[g] ?? []).every((t) => (rowOf(t.id)?.eyes ?? 0) >= 2);
        if (multi && !combo) promises.add(`${at}: the several-eyes card of the group "${g}" cannot be read from the markup (${lang}): scripts/landing_gate.mjs readCombo reads <div class="lp-combo"><h3>title</h3><p>body</p>`);
        if (combo) {
          const label = `the several-eyes card of the group "${g}"`;
          if (several >= 2) {
            const wantTitle = view.words.comboTitle.replace('{max}', String(several));
            if (combo.title !== wantTitle) promises.add(`${at}: ${label} says "${combo.title}", two to ${several} eyes can be bought so it should say "${wantTitle}" (${lang})`);
            // each further eye adds the price of the ladder: the server's rule, written in the page's money
            if (!further) promises.add(`${at}: the gate has no price for a further eye in ${lang}`);
            else if (!combo.body.includes(further.text)) promises.add(`${at}: ${label} says "${combo.body}", each further eye adds ${further.text} (${lang})`);
          } else {
            const wantBody = n > 0 ? view.words.moreSoon : view.words.severalSoon;
            if (combo.title !== view.words.comboTitleSoon) promises.add(`${at}: ${label} says "${combo.title}" but no count of eyes from two can be bought, it should say "${view.words.comboTitleSoon}" (${lang})`);
            if (combo.body !== wantBody) promises.add(`${at}: ${label} says "${combo.body}" but nothing is for sale for several eyes, it should say "${wantBody}" (${lang})`);
            if (/\d/.test(combo.title + combo.body)) promises.add(`${at}: ${label} prints a number while no count of eyes from two can be bought (${lang})`);
          }
        }
      }
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
          // the price it prints is the server's price of that style for that many eyes (the class of the REGISTRY, not the tile table's own idea of it)
          const wantPrice = priceOf(lang, row.id, row.eyes);
          const gotPrice = readTilePrice(out.html);
          if (!wantPrice) promises.add(`${at}: ${label}: the gate has no price for ${row.id} with ${row.eyes} eye${row.eyes === 1 ? '' : 's'} in ${lang}`);
          else if (got.price && gotPrice !== wantPrice.text) promises.add(`${at}: ${label} prints the price "${gotPrice}", the server charges ${wantPrice.text} for ${row.id} with ${row.eyes} eye${row.eyes === 1 ? '' : 's'} (${lang})`);
        }
      }
      // the hero's "Digital file from" line is shown only while some style can be bought for one eye, and says the lowest price among those
      const hero = readHero(view.hero ?? '');
      const heroWant = open && [...live].some(([, set]) => set.has(1));
      if (!hero) promises.add(`${at}: the hero has no price line to read (${lang})`);
      else if (!heroWant && !hero.held) promises.add(`${at}: no style can be bought for one eye but the hero says "${hero.text}"`);
      else if (heroWant && (hero.held || !/\d/.test(hero.text))) underSells.add(`${at}: a style can be bought for one eye but the hero's price line is ${hero.held ? 'held back' : 'without a price'}`);
      else if (heroWant) {
        const lows = [...live].filter(([, set]) => set.has(1)).map(([id]) => priceOf(lang, id, 1)).filter(Boolean);
        const low = lows.length ? lows.reduce((a, b) => (b.minor < a.minor ? b : a)) : null;
        if (!low) promises.add(`${at}: the gate has no price for the styles that can be bought for one eye in ${lang}`);
        else if (!norm(hero.text).includes(low.text)) promises.add(`${at}: the hero says "${hero.text}", the lowest price among the styles that can be bought for one eye is ${low.text} (${lang})`);
      }
      // the price table
      const rows = readTable(view.table);
      if (rows.length !== 5) { promises.add(`${at}: the price table has ${rows.length} rows, the gate reads 5 (free, black, art, two eyes, three eyes)`); continue; }
      const liveOne = (cls) => open && [...live].some(([id, set]) => set.has(1) && styles[id]?.price_class === cls);
      const liveFor = (n) => open && [...live].some(([, set]) => set.has(n));
      const wantRow = { black: liveOne('black'), art: liveOne('art'), two: liveFor(2), more: liveFor(3) };
      // what each row must print: the price of one eye of the class, of two eyes, of three
      const rowPrice = { black: priceOf(lang, classId('black', 1), 1), art: priceOf(lang, classId('art', 1), 1), two: priceOf(lang, classId(null, 2), 2), more: priceOf(lang, classId(null, 3), 3) };
      const names = Object.keys(wantRow);
      names.forEach((key, k) => {
        const r = rows[k + 1];
        const label = `the price table row "${r.title}" (${key})`;
        if (wantRow[key]) {
          if (!r.price || r.soon) underSells.add(`${at}: ${label} can be bought but shows ${r.price ? 'a price' : 'no price'}${r.soon ? ' and says Soon' : ''}`);
          else if (!rowPrice[key]) promises.add(`${at}: the gate has no price for ${label} in ${lang}`);
          else if (norm(r.value) !== rowPrice[key].text) promises.add(`${at}: ${label} prints "${r.value}", the server charges ${rowPrice[key].text} (${lang})`);
        } else {
          if (!r.soon) promises.add(`${at}: ${label} cannot be bought but does not say Soon (${lang})`);
          else if (r.value !== view.soon) promises.add(`${at}: ${label} cannot be bought but its chip says "${r.value}", not "${view.soon}" (${lang})`);
          if (r.price) promises.add(`${at}: ${label} cannot be bought but prints a price`);
        }
      });
      // the sentence of the three eyes row states the ladder (two eyes, each further eye, up to how many): only when two to three eyes can all be bought, and then with the server's prices
      if (several >= 3 && wantRow.more) {
        const note = norm(rows[4].note);
        if (!note.includes(String(several))) promises.add(`${at}: the price table row "${rows[4].title}" does not say up to ${several} eyes (${lang}): "${note}"`);
        if (rowPrice.two && !note.includes(rowPrice.two.text)) promises.add(`${at}: the price table row "${rows[4].title}" does not say the price of two eyes ${rowPrice.two.text} (${lang}): "${note}"`);
        if (further && !note.includes(further.text)) promises.add(`${at}: the price table row "${rows[4].title}" does not say the price of each further eye ${further.text} (${lang}): "${note}"`);
      }
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
      // where nothing can be bought, no price stands anywhere in the table (the free row aside), on a tile or on a card
      if (!live.size || !open) {
        const rest = rows.slice(1);
        if (rest.some((r) => /\d/.test(r.value) || /\d/.test(r.note))) promises.add(`${at}: nothing can be bought but the price table prints a number`);
        if (view.tiles.some((t) => readTile(t.html).price)) promises.add(`${at}: nothing can be bought but a tile prints a price`);
        if (Object.values(view.groups ?? {}).some((h) => { const c = readCombo(h); return c && /\d/.test(c.title + c.body); })) promises.add(`${at}: nothing can be bought but a several-eyes card prints a number`);
      }
      // the other places that say whether ordering is open: the notice bar, the pricing notice with its payment line, the third step ("pay through Stripe" only once ordering is open)
      const w = view.words;
      const state = `ordering is ${open ? 'open' : 'not open'}`;
      const bar = readBar(view.top ?? '');
      if (bar !== (open ? w.barOpen : w.barSoon)) promises.add(`${at}: the notice bar says ${bar === null ? 'nothing the gate can read' : `"${bar}"`} in ${lang}, ${state} so it should say "${open ? w.barOpen : w.barSoon}"`);
      const pnote = readNotice(view.pricing ?? '');
      if (pnote.notice !== (open ? w.noticeOpen : w.notice)) promises.add(`${at}: the pricing notice says ${pnote.notice === null ? 'nothing the gate can read' : `"${pnote.notice}"`} in ${lang}, ${state} so it should say "${open ? w.noticeOpen : w.notice}"`);
      if (pnote.pay !== (open ? norm(w.payOpen) : null)) promises.add(`${at}: the pricing block ${pnote.pay === null ? 'has no payment line' : `says "${pnote.pay}"`} in ${lang}, ${state}`);
      const steps = readSteps(view.how ?? '');
      if (steps.length !== 3) promises.add(`${at}: the steps of how it works are ${steps.length} in ${lang}, the gate reads 3 (scripts/landing_gate.mjs readSteps)`);
      else if (!faqPattern(open && w.step3Open ? w.step3Open : w.step3, null).test(steps[2])) promises.add(`${at}: the third step says "${steps[2].slice(0, 120)}" in ${lang}, ${state} so it should say "${(open && w.step3Open ? w.step3Open : w.step3).slice(0, 120)}"`);
      // the FAQ: each answer is the wording this state calls for. While ordering is closed the plain one; once it is open the open one, and an answer that holds the number of
      // eyes ({max}) only while several eyes can be bought, with the number the catalogue allows (the page never prints a count of eyes the engine cannot sell)
      const faq = readFaq(view.faq ?? '');
      const items = view.faqItems ?? [];
      if (!items.length || faq.length !== items.length) promises.add(`${at}: the FAQ has ${faq.length} questions in ${lang}, the copy has ${items.length} (scripts/landing_gate.mjs readFaq reads <details id="faq-..."> with the question in its <summary> and the answer in a <p>)`);
      else {
        items.forEach((it, k) => {
          const got = faq[k];
          if (got.id !== it.id) { promises.add(`${at}: the FAQ's question ${k + 1} is "${got.id}" in ${lang}, the copy's is "${it.id}"`); return; }
          const counted = typeof it.aOpen === 'string' && it.aOpen.includes('{max}') && maxEyes < 2;
          const wantQ = open ? it.qOpen || it.q : it.q;
          const wantA = open ? (counted ? it.a : it.aOpen || it.a) : it.a;
          const label = `the FAQ answer "${it.id}" (${lang})`;
          if (!faqPattern(wantQ, null).test(got.q)) {
            if (open && faqPattern(it.q, null).test(got.q)) underSells.add(`${at}: the FAQ question "${it.id}" keeps its plain wording although ordering is open (${lang})`);
            else promises.add(`${at}: the FAQ question "${it.id}" says "${got.q}" in ${lang}, ordering is ${open ? 'open' : 'not open'} so it should say "${wantQ}"`);
          }
          if (!faqPattern(wantA, maxEyes >= 2 ? String(maxEyes) : null).test(got.a)) {
            if (open && faqPattern(it.a, null).test(got.a)) underSells.add(`${at}: ${label} keeps its plain wording although ordering is open`);
            else promises.add(`${at}: ${label} says "${got.a.slice(0, 160)}" but ordering is ${open ? 'open' : 'not open'} and ${maxEyes >= 2 ? `up to ${maxEyes} eyes` : 'one eye at most'} can be bought, so it should say "${wantA.slice(0, 160)}"`);
          }
        });
      }
    }
  });
  return { promises: [...promises], underSells: [...underSells], pictures };
}
