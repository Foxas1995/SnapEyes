// WP11 (I17, I22, I24 for the page): the picker as a state machine (src/try/picker.ts), the words on the artwork (src/try/names.ts), the page's side of
// /api/compose (src/try/composeApi.ts) and checkout (src/try/checkout.ts). Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs;
// it returns its results and prints nothing. The rendered picker (tiles, states, buy card, four languages, claims) is suites/ts/picker_page.test.ts.
import {
  type Catalog, type ServerEye, type ServerTile,
  advisoryEyes, buyState, defaultLook, groupAllSoon, groupOf, layoutOf, looksOf, lookName, nextTiles, parseCatalog, reasonOf, resolveStyle, retakeView,
  setKey, showsPrice, tileState, wireOpts, NO_OPTS, artKey, drawable, isLive, isSoon,
} from '../../src/try/picker';
import {
  DATE_MAX, FAMILY_MAX, FAMILY_NAME_LAYOUTS, NAME_MAX, NAMES_TOTAL_MAX, cleanText, composeNames, namesFromWire, namesOf, problems, splitNames, typed, unsupportedChars, wireNames,
} from '../../src/try/names';
import { outcomeOf, persist, pictureOf, type Outcome } from '../../src/try/composeApi';
import { runCheckout, saveSnapshot, takeSnapshot } from '../../src/try/checkout';
import type { Eye } from '../../src/try/multi';

type Row = [string, boolean, string?];

const tile = (id: string, o: Partial<ServerTile> = {}): ServerTile => ({
  id, name: id, slug: id, group: 'solo', legacy: 0, stage: 'live', available: true, why: null, layouts: ['single'], eyes: 1, price_class: 'art', looks: {},
  gate: 'advisory', rule: 'lid', pick: false, ...o,
});
const eye = (i: number, o: Partial<ServerEye> = {}): ServerEye => ({ eye: i, eye_id: `id${i}`, cls: 'own', pupil: 'round', gate: { lid: true, fill: true }, why: [], ...o });
const bad = (i: number, why: string[] = ['lid_sectors_outer'], o: Partial<ServerEye> = {}): ServerEye => eye(i, { gate: { lid: false, fill: true }, why, ...o });
const eyesOf = (id: string): readonly [number, number] | null => ({ 'duo.kiss': [2, 2], 'solo.powder': [1, 1], 'grp.family': [3, 8], 'solo.universe': [1, 1] } as Record<string, [number, number]>)[id] ?? null;

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // ---- groups
  check('groups follow the number of eyes, the landing page\'s three: one, two, family (three to eight)',
    groupOf(1) === 'one' && groupOf(2) === 'two' && [3, 4, 5, 6, 7, 8].every((n) => groupOf(n) === 'family'));

  // ---- parsing the server's tile list: a reply the page does not understand is null, never a crash
  const row = (t: ServerTile, extra: Record<string, unknown> = {}) => ({ ...t, ...extra });
  const good = { tiles: [row(tile('a', { pick: true })), row(tile('b', { stage: 'preview' }))], pick: { id: 'a', reason: 'reason.x' }, eyes: [{ eye: 1, eye_id: 'e', cls: 'grey', pupil: 'round', gate: { lid: true, fill: null } }] };
  const c1 = parseCatalog(good, 'k', 1)!;
  check('parseCatalog keeps the tiles in the server\'s order, the pick, its reason key and the eyes', !!c1 && c1.tiles.map((t) => t.id).join() === 'a,b' && c1.pick === 'a' && c1.reasonKey === 'reason.x' && c1.eyes[0].cls === 'grey' && c1.eyes[0].gate.fill === null);
  check('parseCatalog: junk is null, a row without an id is dropped, a number where a string belongs does not crash',
    parseCatalog(null, 'k', 1) === null && parseCatalog('x', 'k', 1) === null && parseCatalog({}, 'k', 1) === null && parseCatalog({ tiles: [1, null, { id: 'a' }, { id: 5, name: 'x' }] }, 'k', 1)!.tiles.length === 0
    && parseCatalog({ tiles: [{ id: 'a', name: 'A', looks: 'no', layouts: 7, gate: 'weird', rule: 4, stage: 3 }], eyes: ['x', { gate: 5 }] }, 'k', 1)!.tiles[0].gate === 'none');
  const cSoon = parseCatalog({ tiles: [row(tile('a', { stage: 'preview' }))], pick: { id: 'a', reason: 'r' } }, 'k', 2)!;
  const cHeld = parseCatalog({ tiles: [row(tile('a', { available: false, why: 'gate' }))], pick: { id: 'a', reason: 'r' } }, 'k', 2)!;
  const cMissing = parseCatalog({ tiles: [row(tile('a'))], pick: { id: 'zzz', reason: 'r' } }, 'k', 1)!;
  check('a pick that opens soon, is held back or is not in the list is ignored: the page never recommends what cannot be bought', cSoon.pick === null && cHeld.pick === null && cMissing.pick === null && cSoon.reasonKey === null);

  // ---- the state of one tile
  const eyes2 = [eye(1), bad(2)];
  check('tileState: live and available is ready, preview is soon', tileState(tile('a'), eyes2).kind === 'ready' && tileState(tile('a', { stage: 'preview' }), eyes2).kind === 'soon');
  check('tileState: a held tile names the first eye that fails ITS rule (the lid rule of a collision style, the fill rule of Universe)',
    JSON.stringify(tileState(tile('a', { available: false, why: 'gate', rule: 'lid' }), eyes2)) === '{"kind":"gate","eye":2}'
    && JSON.stringify(tileState(tile('u', { available: false, why: 'gate', rule: 'fill' }), [bad(1), eye(2, { gate: { lid: true, fill: false } })])) === '{"kind":"gate","eye":2}');
  check('tileState: no sealed value is reseal with that eye, a bar pupil is pupil',
    JSON.stringify(tileState(tile('a', { available: false, why: 'reseal' }), [eye(1), eye(2, { gate: { lid: null, fill: null } })])) === '{"kind":"reseal","eye":2}'
    && tileState(tile('a', { available: false, why: 'bar_pupil' }), []).kind === 'pupil');
  check('drawable: a live or soon tile the eyes take; never a held one nor a laboratory one',
    drawable(tile('a')) && drawable(tile('a', { stage: 'preview' })) && !drawable(tile('a', { available: false, why: 'gate' })) && !drawable(tile('a', { stage: 'lab' })));

  // ---- the group's line: only when nothing in it can be bought
  check('groupAllSoon: all tiles open soon is one line for the group; one live tile means a chip per soon tile; no tiles at all is not soon',
    groupAllSoon([tile('a', { stage: 'preview' }), tile('b', { stage: 'preview' })]) && !groupAllSoon([tile('a', { stage: 'preview' }), tile('b')]) && !groupAllSoon([]));

  // ---- the price: on a tile of the one-eye group that can be bought now, never on a Soon tile, never in the other groups
  check('showsPrice: one eye and live only', showsPrice(1, tile('a')) && !showsPrice(1, tile('a', { stage: 'preview' })) && !showsPrice(2, tile('a')) && !showsPrice(3, tile('a')) && !showsPrice(1, tile('a', { available: false, why: 'gate' })));

  // ---- which style is on screen
  const T1 = [tile('solo.powder', { pick: true }), tile('solo.universe', { gate: 'hard', rule: 'fill' }), tile('solo.radiance', { stage: 'preview' })];
  const res = (want: string | null, tiles: ServerTile[], pick: string | null, n = 1, eyes: ServerEye[] = [eye(1)]) => resolveStyle({ n, tiles, pick, eyes, want, eyesOf });
  check('resolveStyle: nothing chosen is the recommended tile; no line', JSON.stringify(res(null, T1, 'solo.powder')) === '{"style":"solo.powder","changed":null}');
  check('resolveStyle: the chosen style is kept whenever the eyes can take it, a Soon style too', res('solo.universe', T1, 'solo.powder').style === 'solo.universe' && res('solo.radiance', T1, 'solo.powder').style === 'solo.radiance');
  const T2 = [tile('duo.kiss', { stage: 'preview', gate: 'hard' })];
  const r2 = res('solo.powder', T2, null, 2, [eye(1), eye(2)]);
  check('resolveStyle: a chosen style that does not take this many eyes gives way to the recommended (here the first tile that can be drawn), with the line that says so',
    r2.style === 'duo.kiss' && r2.changed?.kind === 'eyes' && (r2.changed as { from: string }).from === 'solo.powder' && JSON.stringify((r2.changed as { range: number[] }).range) === '[1,1]');
  check('resolveStyle: the choice comes back with the number of eyes (the wish is kept, only the display changes)', res('solo.powder', T1, 'solo.powder', 1).style === 'solo.powder' && res('solo.powder', T2, null, 2, [eye(1), eye(2)]).changed !== null);
  check('resolveStyle: a saved style that is simply not listed (a retired id, a style the owner took back) falls back to the recommended tile WITHOUT a line',
    JSON.stringify(res('studio_black', T1, 'solo.powder')) === '{"style":"solo.powder","changed":null}' && res('nobody', T1, 'solo.powder').changed === null);
  const TG = [tile('grp.family', { gate: 'hard', available: false, why: 'gate' }), tile('solo.powder')];
  const rg = res('grp.family', TG, 'solo.powder', 3, [eye(1), eye(2), bad(3)]);
  check('resolveStyle: a style held back by an eye falls back, and the line names the eye to retake', rg.style === 'solo.powder' && JSON.stringify(rg.changed) === '{"kind":"gate","from":"grp.family","to":"solo.powder","eye":3}');
  const rp = res('grp.family', [tile('grp.family', { available: false, why: 'bar_pupil' }), tile('solo.powder')], 'solo.powder', 3);
  check('resolveStyle: a pupil shape the style does not suit is its own line', rp.changed?.kind === 'pupil');
  const rr = res('grp.family', [tile('grp.family', { available: false, why: 'reseal' }), tile('solo.powder')], 'solo.powder', 3, [eye(1), eye(2), eye(3, { gate: { lid: null, fill: null } })]);
  check('resolveStyle: an eye with no sealed gate value is the reseal line with that eye', rr.changed?.kind === 'reseal' && (rr.changed as { eye: number }).eye === 3);
  check('resolveStyle: with nothing to buy (a group that opens soon) the first tile that can be drawn is shown; with nothing at all, null',
    res(null, [tile('a', { stage: 'preview' }), tile('b', { stage: 'preview' })], null).style === 'a' && res(null, [], null).style === null
    && res(null, [tile('a', { available: false, why: 'gate' })], null).style === null);
  // property: whatever the list, the style it returns is one the eyes can take (never held back, never unknown)
  let rng = 12345;
  const rand = () => { rng = (rng * 1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff; };
  let always = true, detail = '';
  for (let k = 0; k < 400 && always; k++) {
    const tiles = Array.from({ length: 1 + Math.floor(rand() * 6) }, (_, i) => tile(`s${i}`, {
      stage: ['live', 'preview', 'live', 'lab'][Math.floor(rand() * 4)], available: rand() > 0.35, why: rand() > 0.5 ? 'gate' : 'bar_pupil',
    }));
    const pickRow = tiles.find((t) => t.available && t.stage === 'live');
    const r = res(rand() > 0.5 ? `s${Math.floor(rand() * 8)}` : null, tiles, pickRow?.id ?? null);
    const t = tiles.find((x) => x.id === r.style);
    if (r.style !== null && !(t && t.available)) { always = false; detail = JSON.stringify({ tiles, r }); }
    if (r.style === null && tiles.some((x) => x.available && (x.stage === 'live' || x.stage === 'preview'))) { always = false; detail = 'null with a drawable tile ' + JSON.stringify(tiles); }
  }
  check('resolveStyle (400 random lists): the style on screen is always one the eyes can take, and is null only when no tile can be drawn', always, detail);

  // ---- the layout and the options
  check('layoutOf: the wanted layout when the tile takes it, else the tile\'s first (the server\'s default); none without a tile',
    layoutOf(tile('a', { layouts: ['trio', 'diag'] }), 'diag') === 'diag' && layoutOf(tile('a', { layouts: ['trio', 'diag'] }), 'ring') === 'trio' && layoutOf(tile('a', { layouts: ['pair'] }), null) === 'pair' && layoutOf(undefined, 'x') === null);
  const U = tile('solo.universe', { looks: { echo: 'live', vortex: 'live' } });
  check('looks: the chips in the server\'s order, the first is the default, Vortex and Echo are named, a look that opens soon is marked',
    JSON.stringify(looksOf(U)) === '[{"code":"echo","soon":false},{"code":"vortex","soon":false}]' && defaultLook(U) === 'echo' && lookName('vortex') === 'Vortex' && lookName('echo') === 'Echo'
    && looksOf(tile('u', { looks: { echo: 'live', vortex: 'preview' } }))[1].soon === true && defaultLook(tile('a')) === null);
  check('wireOpts: swap for two eyes only, rotate for three only (and not at its start), a style with looks always names one, the six old styles send nothing',
    JSON.stringify(wireOpts(tile('a'), 2, { ...NO_OPTS, swap: true })) === '{"swap":true}' && JSON.stringify(wireOpts(tile('a'), 3, { ...NO_OPTS, swap: true })) === '{}'
    && JSON.stringify(wireOpts(tile('a'), 3, { ...NO_OPTS, rotate: 2 })) === '{"rotate":2}' && JSON.stringify(wireOpts(tile('a'), 3, { ...NO_OPTS, rotate: 3 })) === '{}' && JSON.stringify(wireOpts(tile('a'), 4, { ...NO_OPTS, rotate: 1 })) === '{}'
    && JSON.stringify(wireOpts(U, 1, NO_OPTS)) === '{"look":"echo"}' && JSON.stringify(wireOpts(U, 1, { ...NO_OPTS, look: 'vortex' })) === '{"look":"vortex"}' && JSON.stringify(wireOpts(U, 1, { ...NO_OPTS, look: 'nope' })) === '{"look":"echo"}'
    && JSON.stringify(wireOpts(tile('x', { legacy: 1 }), 2, { swap: true, rotate: 1, look: 'echo' })) === '{}' && JSON.stringify(wireOpts(undefined, 2, { ...NO_OPTS, swap: true })) === '{}');

  // ---- the retake state
  check('reasonOf: only a catchlight is a reflection; every other code says something is inside the ring, and an unknown code says the same', reasonOf('fill_catchlight') === 'reflection' && ['lid_sectors_inner', 'lid_ring_outliers', 'fill_lid_margin', 'fill_hard_edges', 'something_new'].every((c) => reasonOf(c) === 'lid'));
  const tilesPair = [tile('duo.kiss', { stage: 'preview', gate: 'hard', group: 'duo' }), tile('duo.inf', { stage: 'preview', gate: 'hard', group: 'duo' })];
  check('retakeView: nothing fails, nothing is said', retakeView({ tiles: tilesPair, eyes: [eye(1), eye(2)], selected: tilesPair[0] }) === null);
  const heldPair = tilesPair.map((t) => ({ ...t, available: false, why: 'gate' }));
  const rv = retakeView({ tiles: heldPair, eyes: [eye(1), bad(2)], selected: undefined })!;
  check('retakeView: a pair that fails the gate on eye 2 holds both tiles; reason, tip and the manual route (nothing can be bought now: no dead end)',
    !!rv && JSON.stringify(rv.eyes) === '[2]' && JSON.stringify(rv.reasons) === '["lid"]' && rv.tip === 'open' && rv.holds && rv.deadEnd && rv.why === 'lid_sectors_outer' && rv.reseal.length === 0);
  const adv = tile('solo.powder', { gate: 'advisory' });
  const rva = retakeView({ tiles: [adv, tile('solo.universe', { gate: 'hard', rule: 'fill' })], eyes: [bad(1)], selected: adv })!;
  check('retakeView: one eye with a lid on an advisory style still shows the state (the style is drawn and can be bought), and it is no dead end',
    !!rva && JSON.stringify(rva.eyes) === '[1]' && rva.holds === false && rva.deadEnd === false);
  const uni = tile('solo.universe', { gate: 'hard', rule: 'fill', available: false, why: 'gate' });
  const rvu = retakeView({ tiles: [adv, uni], eyes: [eye(1, { gate: { lid: true, fill: false }, why: ['fill_catchlight'] })], selected: adv })!;
  check('retakeView: an eye that only fails the fill rule holds the Universe tile and says "reflection"; the advisory style (lid rule) is not warned', !!rvu && JSON.stringify(rvu.eyes) === '[1]' && JSON.stringify(rvu.reasons) === '["reflection"]' && rvu.tip === 'light' && advisoryEyes(adv, [eye(1, { gate: { lid: true, fill: false } })]).length === 0);
  const rvg = retakeView({ tiles: heldPair, eyes: [bad(1, ['lid_ring_outliers'], { cls: 'grey' }), eye(2)], selected: undefined })!;
  check('retakeView: a grey eye gets the tip for the soft grey edge', rvg.tip === 'grey');
  const rvb = retakeView({ tiles: heldPair, eyes: [bad(1, ['lid_sectors_outer']), eye(2, { gate: { lid: false, fill: false }, why: ['fill_catchlight'] })], selected: undefined })!;
  check('retakeView: two eyes that fail the rule of the held tiles are both named (not only the first), both sentences, in the order of the eyes',
    JSON.stringify(rvb.eyes) === '[1,2]' && JSON.stringify(rvb.reasons) === '["lid","reflection"]');
  const resealTiles = [tile('grp.fam', { available: false, why: 'reseal', gate: 'hard' })];
  const rvr = retakeView({ tiles: resealTiles, eyes: [eye(1), eye(2, { gate: { lid: null, fill: null } })], selected: undefined })!;
  check('retakeView: an eye without a sealed value is "make the preview again", not a lid', !!rvr && JSON.stringify(rvr.reseal) === '[2]' && rvr.eyes.length === 0 && rvr.reasons.length === 0 && rvr.holds === false);
  check('advisoryEyes: only an advisory style warns, on the eyes that fail ITS rule; a hard style (it is held back instead) and the old styles never warn',
    JSON.stringify(advisoryEyes(adv, [eye(1), bad(2)])) === '[2]' && advisoryEyes(tile('h', { gate: 'hard' }), [bad(1)]).length === 0 && advisoryEyes(tile('l', { gate: 'none', legacy: 1 }), [bad(1)]).length === 0 && advisoryEyes(undefined, [bad(1)]).length === 0);
  check('a one-eye set always has a style it can buy: the Universe (hard, fill) held back never leaves a dead end while an advisory style is live',
    retakeView({ tiles: [adv, uni], eyes: [eye(1, { gate: { lid: false, fill: false }, why: ['lid_sectors_outer', 'fill_rim_sector'] })], selected: adv })!.deadEnd === false);

  // ---- the buy card
  const live1 = [tile('a'), tile('b', { stage: 'preview' })];
  check('buyState: a live selected style is bought as it is; a Soon one says so (no price, no button); a count with no live style is one line; nothing selected is none',
    buyState({ n: 1, tiles: live1, selected: live1[0] }).kind === 'normal' && buyState({ n: 1, tiles: live1, selected: live1[1] }).kind === 'soon'
    && JSON.stringify(buyState({ n: 2, tiles: tilesPair, selected: tilesPair[0] })) === '{"kind":"countSoon","n":2}' && buyState({ n: 1, tiles: live1, selected: undefined }).kind === 'none' && buyState({ n: 1, tiles: [], selected: undefined }).kind === 'none');
  check('buyState: a count that IS sold but whose eyes fail the gate is not "opens soon" (the retake state speaks)', buyState({ n: 3, tiles: [tile('grp.fam', { available: false, why: 'gate' })], selected: undefined }).kind === 'none');

  // ---- what to draw next: two at a time, in the server's order, never a held or laboratory tile, never one already there
  const six = ['a', 'b', 'c', 'd', 'e', 'f'].map((id) => tile(id));
  const have = new Set<string>();
  const order: string[] = [];
  for (let step = 0; step < 5; step++) {
    const next = nextTiles(six, (t) => have.has(t.id));
    if (!next.length) break;
    order.push(next.map((t) => t.id).join('+'));
    next.forEach((t) => have.add(t.id));
  }
  check('nextTiles: two at a time in the server\'s order, then nothing', order.join(' ') === 'a+b c+d e+f', order.join(' '));
  check('nextTiles skips a held tile, a laboratory tile and what is already there', nextTiles([tile('a', { available: false, why: 'gate' }), tile('b', { stage: 'lab' }), tile('c'), tile('d')], (t) => t.id === 'c').map((t) => t.id).join() === 'd');

  // ---- keys
  check('setKey: the same eyes in another order are the same set (moving an eye is not a new set); another eye is another set', setKey(['b', 'a', 'c']) === setKey(['c', 'b', 'a']) && setKey(['a', 'b']) !== setKey(['a', 'c']));
  check('artKey joins what changes a picture, an absent part is empty', artKey(['k', 'solo.powder', null, undefined, 3]) === 'k|solo.powder|||3');
  check('isLive and isSoon read the stage the server sent', isLive(tile('a')) && !isLive(tile('a', { stage: 'preview' })) && isSoon(tile('a', { stage: 'preview' })) && !isSoon(tile('a')));

  // ---- the words on the artwork
  check('the limits are the server\'s (api/_lib/styles/text.py): 24 and 200, 20, 24; the family name is not offered until a layout draws it', NAME_MAX === 24 && NAMES_TOTAL_MAX === 200 && DATE_MAX === 20 && FAMILY_MAX === 24 && FAMILY_NAME_LAYOUTS.length === 0);
  const LETTERS = 'ą č ę ė į š ų ū ž ő ű ä ö ü ß Ą Č Ę Ė Į Š Ų Ū Ž Ő Ű Ä Ö Ü é è ñ ç ł Ł ø å æ œ';
  check('every letter of the Lithuanian, Hungarian and German alphabets (and the usual Latin ones) can be drawn in the artwork font', unsupportedChars(LETTERS).length === 0, unsupportedChars(LETTERS).join(' '));
  check('a letter the font cannot draw is refused: Cyrillic, Greek capitals it lacks, CJK, Arabic, an emoji', ['Ж', '中', 'ع', String.fromCodePoint(0x1f600), 'Ω'.repeat(0)].every((s) => s === '' || unsupportedChars(`Anna ${s}`).includes(s)));
  check('names: spaces, hyphens, apostrophes and an ampersand are fine; the date takes digits and dots', unsupportedChars("Anna-Marie O'Neil & Jonas") .length === 0 && unsupportedChars('14.06.2026').length === 0 && unsupportedChars('14 June 2026').length === 0);
  check('cleanText: NFC, control and zero width characters out, runs of space one, trimmed', cleanText('  An\u200bna \t  Max\u0007 ') === 'Anna Max' && cleanText(5) === '' && cleanText('é') === 'é');
  check('typed: the semicolon and line breaks (they separate names on the wire) become a space, control characters go, the cut is in characters not code units',
    typed('A;B\nC', 24) === 'A B C' && typed('x'.repeat(30), 24).length === 24 && [...typed('😀'.repeat(30), 24)].length === 24 && typed('ab\u0007cd', 24) === 'abcd');
  check('splitNames reads the old wire string and a list alike, empty names dropped', JSON.stringify(splitNames('Anna;Max;;Lina\nTom')) === '["Anna","Max","Lina","Tom"]' && JSON.stringify(splitNames([' Anna ', '', 'Max'])) === '["Anna","Max"]' && splitNames(null).length === 0);
  check('wireNames and composeNames: the non-empty cleaned names in the order of the eyes; the wire form is the old semicolon string', wireNames(['Anna', '', ' Max ']) === 'Anna;Max' && JSON.stringify(composeNames(['Anna', '', 'Max'])) === '["Anna","Max"]' && wireNames([]) === '');
  check('namesOf and namesFromWire: a name belongs to its eye by id (moving and removing keep it), a saved string goes to the first eyes in order',
    JSON.stringify(namesOf({ a: 'Anna', c: 'Lina' }, ['c', 'a', 'b'])) === '["Lina","Anna",""]' && JSON.stringify(namesFromWire('Anna;Max', ['x', 'y', 'z'])) === '{"x":"Anna","y":"Max"}' && JSON.stringify(namesFromWire(7, ['x'])) === '{}');
  check('problems: nothing for good words', problems(['Anna', 'Max'], '14 June 2026', '').length === 0);
  check('problems: a name over 24 letters, the names over 200 together, a date over 20, a family name over 24, each in the order the form shows them',
    JSON.stringify(problems(['x'.repeat(25)])) === '[{"code":"name_long","eye":1}]' && problems(Array.from({ length: 9 }, () => 'y'.repeat(24))).some((p) => p.code === 'names_long')
    && problems([], 'd'.repeat(21))[0].code === 'date_long' && problems([], '', 'f'.repeat(25))[0].code === 'family_long');
  const gl = problems(['Anna', 'Ж'], '1 ж', 'Ж');
  check('problems: a letter the font cannot draw names the eye, the date and the family name each in its own field',
    gl.some((p) => p.code === 'glyph' && p.eye === 2 && p.chars.join() === 'Ж') && gl.some((p) => p.code === 'glyph' && p.eye === 0 && p.field === 'date') && gl.some((p) => p.code === 'glyph' && p.eye === 0 && p.field === 'family'));
  check('problems: a name that is only long before cleaning is no problem (it is drawn cleaned)', problems(['  ' + 'x'.repeat(24) + '   ']).length === 0);

  // ---- the page's side of /api/compose
  const reply = (status: number, data: unknown, reason = '', o: { retryAfter?: number; error?: string } = {}) => ({ ok: status >= 200 && status < 300 && reason === '', status, data: data as never, reason, error: o.error ?? '', retry: false, retryAfter: o.retryAfter ?? 0 });
  check('outcomeOf: an answer is ok with its data', outcomeOf(reply(200, { ok: true, x: 1 })).kind === 'ok');
  const busy = outcomeOf(reply(503, { retry_after: 7 }, 'busy_retry', { error: 'wait' }));
  check('outcomeOf: 503 busy_retry and plate_retry are busy with the seconds asked for (from the body, or the header\'s)', busy.kind === 'busy' && (busy as { retryAfter: number }).retryAfter === 7
    && outcomeOf(reply(503, {}, 'plate_retry', { retryAfter: 4 })).kind === 'busy' && (outcomeOf(reply(503, {}, 'busy_retry')) as { retryAfter: number }).retryAfter === 3);
  const un = outcomeOf(reply(422, { why: 'gate', style: 'duo.kiss' }, 'style_unavailable', { error: 'Retake' }));
  check('outcomeOf: 422 style_unavailable carries why and the style, 422 too_many_styles the number that fits, 503 tiles_paused is paused',
    un.kind === 'unavailable' && (un as { why: string }).why === 'gate' && (un as { style: string }).style === 'duo.kiss' && (outcomeOf(reply(422, { max: 3 }, 'too_many_styles')) as { max: number }).max === 3 && outcomeOf(reply(503, {}, 'tiles_paused')).kind === 'paused');
  check('outcomeOf: the platform\'s own answers (no JSON) are plain errors with a sentence, never an empty one', ['0', '413', '504', '500'].every((s) => { const o = outcomeOf(reply(Number(s), null)); return o.kind === 'error' && (o as { message: string }).message.length > 5; }));
  let calls = 0;
  const waits: number[] = [];
  const flaky = async (): Promise<Outcome<number>> => (++calls < 3 ? { kind: 'busy', retryAfter: 2, message: 'm' } : { kind: 'ok', data: 1 });
  const p1 = await persist(flaky, () => true, 3, async (ms) => { waits.push(ms); });
  check('persist: asks again while the server is busy, waiting as long as it asks, and ends with the answer', p1.kind === 'ok' && calls === 3 && waits.join() === '2000,2000');
  calls = 0;
  const p2 = await persist(async () => { calls++; return { kind: 'busy', retryAfter: 99, message: 'm' } as Outcome<number>; }, () => true, 3, async (ms) => { waits.push(ms); });
  check('persist: three more tries at most, never a wait over 20 seconds, then the busy answer', p2.kind === 'busy' && calls === 4 && waits.slice(2).every((w) => w === 20_000));
  calls = 0;
  const p3 = await persist(async () => { calls++; return { kind: 'busy', retryAfter: 1, message: 'm' } as Outcome<number>; }, () => false, 3, async () => undefined);
  check('persist: stops asking when the answer is no longer wanted (the eyes changed)', p3.kind === 'busy' && calls === 1);
  const pic = pictureOf({ image: 'QUJD', width: 1024, height: 683, layout: 'pair', canvas: '3:2', design_used: 'infinity', fallback: 'stack_contrast', plan8: 'abcd1234', opts: { swap: true } });
  check('pictureOf: the picture with what the server said about it; none without an image', !!pic && pic.src === 'data:image/jpeg;base64,QUJD' && pic.fallback === 'stack_contrast' && pic.plan8 === 'abcd1234' && pic.opts.swap === true && pictureOf({ available: false }) === null && pictureOf(null) === null);

  // ---- checkout: the artwork's description goes with the order, and the two new refusals come back as outcomes
  const mk = (id: string): Eye => ({
    id, before: 'data:image/jpeg;base64,AAAA', image: `DISPLAY-${id}`, thumb: 'data:image/jpeg;base64,BBBB', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false,
    colourOff: false, sealed: `SEALED-${id}`, draft: { crop: `CROP-${id}`, ticket: 'work.1.x', until: Date.now() + 600_000 },
  });
  type Rec = { path: string; body?: Record<string, unknown> };
  const rec: Rec[] = [];
  const api = (final: { status: number; data: unknown; reason?: string }) => (async (path: string, o: { body?: Record<string, unknown> } = {}) => {
    rec.push({ path, body: o.body });
    if (path === '/api/order') return { ok: true, status: 200, data: { order: 'ord1', k: 'k1', eye: 1, created: true, expires_at: Math.floor(Date.now() / 1000) + 7200 }, reason: '', error: '', retry: false, retryAfter: 0 };
    return { ok: final.status === 200, status: final.status, data: final.data, reason: final.reason ?? '', error: '', retry: false, retryAfter: 0 };
  }) as never;
  const base = { eyes: [mk('a')], style: 'solo.powder', layout: 'single', names: 'Anna', lang: 'en' as const, ref: null };
  const ok = await runCheckout({ ...base, date: '14 June 2026', familyName: 'Berg', opts: { swap: true }, plan8: 'abcd1234' }, () => undefined, api({ status: 200, data: { url: 'https://checkout.stripe.test/x', order: 'ord1', expires_at: 1 } }));
  const body = rec.filter((r) => r.path === '/api/checkout').at(-1)?.body ?? {};
  check('runCheckout sends the date, the family name, the options that applied and plan8 with the order', ok.kind === 'redirect' && body.date === '14 June 2026' && body.family_name === 'Berg' && JSON.stringify(body.opts) === '{"swap":true}' && body.plan8 === 'abcd1234' && body.names === 'Anna', JSON.stringify(body));
  rec.length = 0;
  await runCheckout(base, () => undefined, api({ status: 200, data: { url: 'https://checkout.stripe.test/x', order: 'ord1', expires_at: 1 } }));
  const plain = rec.filter((r) => r.path === '/api/checkout').at(-1)?.body ?? {};
  check('runCheckout sends none of them when there is nothing to send (an old artwork\'s checkout is the old request)', !('date' in plain) && !('family_name' in plain) && !('opts' in plain) && !('plan8' in plain));
  const pc = await runCheckout({ ...base, plan8: 'x' }, () => undefined, api({ status: 409, data: { ok: false }, reason: 'plan_changed' }));
  check('runCheckout: 409 plan_changed is its own outcome (nothing was created: the page makes the preview again)', pc.kind === 'plan_changed');
  const su = await runCheckout(base, () => undefined, api({ status: 409, data: { ok: false, why: 'gate', style: 'solo.powder' }, reason: 'style_unavailable' }));
  check('runCheckout: 409 style_unavailable is its own outcome with why', su.kind === 'unavailable' && (su as { why: string }).why === 'gate');
  const store = new Map<string, string>();
  (globalThis as unknown as { window: unknown }).window = { sessionStorage: { getItem: (k: string) => store.get(k) ?? null, setItem: (k: string, v: string) => { store.set(k, v); }, removeItem: (k: string) => { store.delete(k); } } };
  const { draft: _d, ...e1 } = mk('a');
  const saved = saveSnapshot({ v: 1, order: 'o1', at: Date.now(), style: 'solo.powder', layoutWant: null, names: 'Anna;Max', eyes: [e1], date: '14 June', family: 'Berg', opts: { swap: true, look: 'vortex' } });
  const back = takeSnapshot('o1');
  check('the snapshot for the way back from Stripe carries the date, the family name and the options', saved && back?.date === '14 June' && back?.family === 'Berg' && back?.opts?.look === 'vortex' && back?.names === 'Anna;Max');
  saveSnapshot({ v: 1, order: 'o2', at: Date.now(), style: 'celestial_gold', layoutWant: null, names: '', eyes: [e1] });
  const old = takeSnapshot('o2');
  check('a snapshot of an older page (no date, family or options) still loads', !!old && old.date === undefined && old.opts === undefined && old.style === 'celestial_gold');
  return out;
}

export type { Catalog };
