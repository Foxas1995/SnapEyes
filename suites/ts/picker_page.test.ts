// WP11 (I17, I24): the picker as it is printed, with the real components rendered on the server (react-dom/server): the tile list and its states (ready, Soon,
// loading), the group line, the calm retake line where nothing can be drawn, the warning of a style that only warns, the buy card (a style that opens soon has no
// price and no button, nothing is ticked for the customer), the words on the artwork, the layout glyphs, and the four languages: every registry reason line has its
// words, no tile text claims anything the owner and the review ruled out. The state machine itself is suites/ts/picker_state.test.ts.
// 2026-10-22 (the owner, on his own phone: "why does Universe not work?", a tile with a warning sign and "Retake eye 1 first"; "we exist to raise the iris quality,
// not to tell every customer what does not fit"): a tile held back for these eyes is not shown any more, the retake card under the list is gone, and where no style at
// all can be drawn one calm line with the retake button stands where the picture would be. The checks of the held tile, the retake card's reasons, tips and e-mail were
// turned into checks of that: each says so where it was adapted.
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { COPY, T, setCopyLang } from '../../src/try/copy';
import { LANGS, type Lang } from '../../src/shared/lang';
import { STYLES } from '../../src/shared/styles';
import { StylePicker, CalmRetake, emptyPicker, type PickerModel } from '../../src/try/StylePicker';
import { ResultView, glyphPoints } from '../../src/try/ResultView';
import { BuyCard } from '../../src/try/BuyCard';
import { Words, emptyWords } from '../../src/try/Words';
import { NO_OPTS, buyState, retakeView, advisoryEyes, showsPrice, type Catalog, type ServerEye, type ServerTile } from '../../src/try/picker';
import { LAYOUT_IDS } from '../../src/shared/layouts';
import type { Art, Eye } from '../../src/try/multi';

type Row = [string, boolean, string?];

const tile = (id: string, o: Partial<ServerTile> = {}): ServerTile => ({
  id, name: o.name ?? id, slug: o.slug ?? id.replace(/[._]/g, '-'), group: 'solo', legacy: 0, stage: 'live', available: true, why: null, layouts: ['single'], eyes: 1, price_class: 'art', looks: {},
  gate: 'advisory', rule: 'lid', pick: false, ...o,
});
const eye = (i: number, o: Partial<ServerEye> = {}): ServerEye => ({ eye: i, eye_id: `id${i}`, cls: 'own', pupil: 'round', gate: { lid: true, fill: true }, why: [], ...o });
const bad = (i: number, why = ['lid_sectors_outer']): ServerEye => eye(i, { gate: { lid: false, fill: true }, why });
const art = (n = 1): Art => ({ src: `data:image/jpeg;base64,PIC${n}`, w: 480, h: 320, layout: 'single' });
const noop = () => undefined;

const text = (h: string) => h.replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();
const has = (h: string, id: string) => h.includes(`data-testid="${id}"`);

function model(n: number, tiles: ServerTile[], eyes: ServerEye[], o: Partial<PickerModel> = {}, pick: string | null = null, reasonKey: string | null = null): PickerModel {
  const catalog: Catalog = { key: 'k', n, tiles: tiles.map((t) => ({ ...t, pick: t.id === pick })), pick, reasonKey, eyes };
  const selected = tiles.find((t) => t.id === (o.style ?? pick ?? tiles[0]?.id));
  return {
    ...emptyPicker(n), catalog, style: selected?.id ?? null, selected, retake: retakeView({ tiles, eyes, selected }), advisory: advisoryEyes(selected, eyes),
    tilePicture: (t) => (t.available ? art() : undefined), ...o,
  };
}

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  (globalThis as unknown as { window: unknown }).window = { sessionStorage: { getItem: () => null, setItem: noop, removeItem: noop }, localStorage: { getItem: () => null, setItem: noop, removeItem: noop } };
  setCopyLang('en');
  // the result screen's props and an eye of it (used from the first checks on)
  const eyeObj = (id: string, extra: Partial<Eye> = {}): Eye => ({ id, before: 'data:image/jpeg;base64,B', image: 'DISPLAY', thumb: 'data:image/jpeg;base64,T', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false, colourOff: false, ...extra }) as Eye;
  const rvProps = (eyes: Eye[], picker: PickerModel, extra: Record<string, unknown> = {}) => ({
    eyes, selectedId: eyes[0].id, onSelect: noop, onRemove: noop, onRetake: noop, onAdd: noop, onMove: noop, onCentre: noop, art: art(), staleArt: undefined, composeError: null, onRetryCompose: noop,
    picker, layout: null, layoutOptions: [] as string[], onLayout: noop, opts: NO_OPTS, onOpts: noop, words: emptyWords(eyes.length), onStartOver: noop, purchase: null, ...extra,
  });

  // ---- one eye: the release 1 singles
  const singles = [
    tile('solo.powder', { name: 'Powder Burst', slug: 'powder-burst' }), tile('solo.universe', { name: 'Universe', slug: 'universe', gate: 'hard', rule: 'fill', looks: { echo: 'live', vortex: 'live' } }),
    tile('solo.radiance', { name: 'Radiance', slug: 'radiance', stage: 'preview' }), tile('solo.clean', { name: 'Clean Iris', slug: 'clean-iris', price_class: 'black', gate: 'hard' }),   // hard since 2026-10-14, as the registry says
  ];
  const priceOf = (t: ServerTile) => (t.stage === 'live' ? (t.price_class === 'black' ? 'P-BLACK' : 'P-ART') : null);
  const m1 = model(1, singles, [eye(1)], { priceOf, look: 'echo' }, 'solo.powder', 'reason.solo_powder.own');
  const h1 = renderToStaticMarkup(createElement(StylePicker, { model: m1 }));
  check('the picker: the landing\'s group word and line for one eye, the list labelled, one tile per style in the server\'s order', has(h1, 'style-picker') && h1.includes('data-group="one"') && text(h1).includes('Just you')
    && text(h1).includes('One iris, alone on black or set in a universe of its own.') && /aria-label="Styles for your eyes"/.test(h1)
    && [...h1.matchAll(/data-testid="tile-([a-z-]+)"/g)].map((m) => m[1]).filter((s) => s !== 'price' && s !== 'list').join() === 'powder-burst,universe,radiance,clean-iris');
  check('the recommended tile is framed, says Recommended and carries its reason line; it is the only one', (h1.match(/data-testid="recommended"/g) ?? []).length === 1 && text(h1).includes('Recommended') && text(h1).includes('Your own colours, turned to powder'));
  check('a live tile prints its price (the black class and the art class), a Soon tile prints none but the word Soon', (h1.match(/data-testid="tile-price"/g) ?? []).length === 3 && h1.includes('P-BLACK') && !/Radiance[^<]*<[^>]*>[^<]*P-/.test(h1)
    && (h1.match(/data-testid="soon"/g) ?? []).length === 1);
  const radiance = h1.slice(h1.indexOf('data-testid="tile-radiance"'), h1.indexOf('data-testid="tile-clean-iris"'));
  check('the Soon tile has the Soon chip, no price, and is still previewed', radiance.includes('data-testid="soon"') && !radiance.includes('tile-price') && radiance.includes('<img'));
  check('the Universe tile carries its look chips inside it (not as tiles), the default pressed', has(h1, 'look-echo') && has(h1, 'look-vortex') && /data-testid="look-echo"/.test(h1) && h1.indexOf('look-echo') > h1.indexOf('tile-universe') && h1.indexOf('look-echo') < h1.indexOf('tile-radiance'));
  const press = (h: string, id: string) => new RegExp(`aria-pressed="(true|false)"[^>]*data-testid="${id}"|data-testid="${id}"[^>]*aria-pressed="(true|false)"`).exec(h);
  const hU = renderToStaticMarkup(createElement(StylePicker, { model: model(1, singles, [eye(1)], { priceOf, look: 'vortex', style: 'solo.universe' }, 'solo.powder') }));
  check('the chips say which look is chosen (aria-pressed), on the selected tile only', press(hU, 'look-vortex')?.[1] === 'true' && press(hU, 'look-echo')?.[1] === 'false' && press(h1, 'look-echo')?.[1] === 'false', String(press(hU, 'look-vortex')));
  check('every tile is a list item with one button; the chips come after their tile\'s button (keyboard order is the visual order)',
    (h1.match(/<li /g) ?? []).length === 4 && h1.indexOf('<button', h1.indexOf('tile-universe')) < h1.indexOf('look-echo'));
  check('a tile\'s picture has an alt text that names the style', /alt="Powder Burst on your eyes: reduced preview with a watermark"/.test(h1));
  // 2026-10-20: a tile of one eye says what the look is in one line under its name (copy picker.lines; the six of release 1 say what the landing's tiles say)
  check('a tile of one eye carries the style\'s one line under its name, and only one', (h1.match(/data-testid="style-line"/g) ?? []).length === 4
    && text(h1).includes('Fine rays of light in the colours of your own iris.') && text(h1).includes('Your restored iris alone on pure black.'));
  const hNew = renderToStaticMarkup(createElement(StylePicker, { model: model(1, [tile('solo.nebula', { name: 'Nebula', slug: 'nebula', stage: 'preview' }), tile('solo.nothing', { name: 'Nothing', slug: 'nothing', stage: 'preview' })], [eye(1)]) }));
  check('a look of the light family has its line, and a style the copy has no line for prints none', text(hNew).includes('Your iris glows at the heart of a nebula.') && (hNew.match(/data-testid="style-line"/g) ?? []).length === 1);
  const lineKeys = Object.keys(COPY.en.picker.lines);
  check('the one line of each of the eleven styles of one eye is written in English, German, Lithuanian and Hungarian (the same keys), none empty, no dash',
    lineKeys.length === 11 && LANGS.every((l: Lang) => Object.keys(COPY[l].picker.lines).join() === lineKeys.join() && Object.values(COPY[l].picker.lines).every((s) => s.length > 0 && !/[\u2012-\u2015]/.test(s))));

  // ---- the same list loading
  const hLoad = renderToStaticMarkup(createElement(StylePicker, { model: { ...emptyPicker(1) } }));
  check('while the tile list is asked for: a busy list of skeletons, the group heading, no tile text', hLoad.includes('aria-busy="true"') && text(hLoad).includes('Just you') && !has(hLoad, 'tile-powder-burst'));
  const hLoadTile = renderToStaticMarkup(createElement(StylePicker, { model: model(1, singles, [eye(1)], { tilePicture: () => undefined, tileBusy: () => true }, 'solo.powder') }));
  check('a tile whose picture is being made shows a still skeleton (nothing loops, BR-3) and says so to a screen reader, not an accent swatch', hLoadTile.includes('data-testid="tile-skeleton"') && !/animate-[a-z]/.test(hLoadTile) && text(hLoadTile).includes('Powder Burst: the preview is being made') && !hLoadTile.includes('<img'));
  const hErr = renderToStaticMarkup(createElement(StylePicker, { model: { ...emptyPicker(1), error: 'We are busy.' } }));
  check('a tile list that could not be had says why and offers Try again', has(hErr, 'picker-error') && text(hErr).includes('We are busy.') && text(hErr).includes('Try again'));

  const hFail = renderToStaticMarkup(createElement(StylePicker, { model: model(1, singles, [eye(1)], { tilePicture: () => undefined, tileFailed: () => true, paused: 'We are not making more previews today. Please try again later.' }, 'solo.powder') }));
  check('a tile whose picture could not be made says so and offers Try again; a server that makes no more pictures today says so under the list',
    has(hFail, 'tile-retry') && text(hFail).includes('Preview not made') && has(hFail, 'tiles-paused') && text(hFail).includes('We are not making more previews today.') && !has(hLoad, 'tile-retry'));

  // ---- two eyes, every style opens soon: one line for the group
  const pair = ['duo.kiss', 'duo.inf', 'duo.clean'].map((id, i) => tile(id, { name: ['Kiss Collision', 'Collision Infinity', 'Clean Infinity'][i], group: 'duo', stage: 'preview', gate: 'hard', layouts: ['pair'], eyes: 2 }));
  const h2 = renderToStaticMarkup(createElement(StylePicker, { model: model(2, pair, [eye(1), eye(2)]) }));
  check('two eyes, nothing live: the group says "Free preview now. Ordering for this group opens soon." once and no tile has a Soon chip, no price, no Recommended',
    text(h2).includes('Free preview now. Ordering for this group opens soon.') && !has(h2, 'soon') && !has(h2, 'tile-price') && !has(h2, 'recommended') && text(h2).includes('Two of you'));

  // ---- a tile held back for these eyes, and the calm line where nothing can be drawn
  const trio = [tile('grp.fam', { name: 'Family Colours', group: 'grp', gate: 'hard', available: false, why: 'gate', layouts: ['trio'], eyes: 3 })];
  const eyes3 = [eye(1), eye(2), bad(3)];
  const m3 = model(3, trio, eyes3, { tilePicture: () => undefined });
  const h3 = renderToStaticMarkup(createElement(StylePicker, { model: m3 }));
  // adapted 2026-10-22: it was "a held tile is dimmed, says Retake eye 3 first": the held tile is not shown at all now
  check('a tile held back for these eyes is not shown: no tile, no "Retake eye 3 first", no warning sign, no picture', !has(h3, 'tile-grp-fam') && !text(h3).includes('Retake eye') && !/triangle-alert|alert-triangle/.test(h3) && !h3.includes('<img'));
  const rp = renderToStaticMarkup(createElement(CalmRetake, { view: m3.retake!, total: 3, onRetake: noop }));
  const rt = text(rp);
  // adapted 2026-10-22: it was "the retake state: which eye, why in plain words, one tip, the retake button and the e-mail": now one calm line and the button
  check('the calm retake: one line and the retake button of the eye it names; no reason, no tip, no warning sign, no e-mail',
    rt.includes(COPY.en.picker.retake.calm) && has(rp, 'retake-calm') && has(rp, 'retake-eye-3') && !has(rp, 'retake-eye-1') && !has(rp, 'manual-route') && !/eyelid|lash|lift the upper lid|mailto/i.test(rp) && !/triangle-alert|alert-triangle/.test(rp));
  // adapted 2026-10-22: it was "the retake state of a one-eye set that has a style to buy has no manual route": a set with something to draw has no retake state at all now
  const uniHeld = { ...singles[1], available: false, why: 'gate' } as ServerTile;
  const mUni = model(1, [singles[0], uniHeld], [eye(1, { gate: { lid: true, fill: false }, why: ['fill_rim_sector'] })], { priceOf }, 'solo.powder');
  const hUni = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], mUni)));
  check('Universe held back for one eye (the owner\'s case of 2026-10-22): its tile is not in the grid, the other styles are, nothing asks for a retake and nothing warns',
    has(hUni, 'tile-powder-burst') && !has(hUni, 'tile-universe') && !has(hUni, 'retake-calm') && !has(hUni, 'retake-state') && !text(hUni).includes('Retake eye') && !has(hUni, 'chip-retake-1') && !/triangle-alert|alert-triangle/.test(hUni.slice(hUni.indexOf('style-picker'))));

  // ---- the warning of a style that only warns, and the buy card
  const advTiles = [singles[0]];
  const mAdv = model(1, advTiles, [bad(1)], { priceOf }, 'solo.powder');
  const hAdv = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], mAdv)));
  check('a failing eye on an advisory style: the page still shows its preview, with the line under the picture and a Retake mark on the eye', has(hAdv, 'advisory-note') && text(hAdv).includes('An eyelid or lash is still in the ring of your iris. Retake it for a cleaner result.') && has(hAdv, 'artwork'));
  const buy = (o: Record<string, unknown> = {}) => renderToStaticMarkup(createElement(BuyCard, {
    eyes: [eyeObj('e1')], style: 'solo.powder', styleName: 'Powder Burst', ordering: { open: true, prices: { one_eye_studio_black: 1997, one_eye_art: 2497, two_eyes: 3997, each_further_eye: 1500 }, maxEyes: 8 },
    preview: 'ready', stale: [], onRetake: noop, waiver: false, onWaiver: noop, busy: false, step: null, error: null, onBuy: noop,
    state: { kind: 'normal' }, loading: false, advisory: [], wordsBlocked: false, ...o,
  } as never));
  const hb = buy({ advisory: [1] });
  check('the advisory warning is above the waiver, so it is read before the customer ticks it; the waiver is not ticked for them and the button is shut until they do',
    hb.indexOf('data-testid="buy-advisory"') > 0 && hb.indexOf('data-testid="buy-advisory"') < hb.indexOf('data-testid="waiver"') && !/data-testid="waiver"[^>]*checked/.test(hb) && /data-testid="buy"[^>]*disabled/.test(hb));
  const hs = buy({ state: { kind: 'soon' } });
  check('a style that opens soon: one line, no price, no waiver, no button, no date', text(hs).includes('This style opens soon. Choose another to order now.') && !has(hs, 'buy') && !has(hs, 'waiver') && !has(hs, 'price') && !/\d{4}|€|\d[,.]\d\d/.test(text(hs).replace('Price for this artwork', '')));
  const hc = buy({ state: { kind: 'countSoon', n: 2 }, eyes: [eyeObj('a'), eyeObj('b')] });
  check('a count no style of can be bought: "Ordering for 2 eyes opens soon." and nothing to press', text(hc).includes('Ordering for 2 eyes opens soon.') && !has(hc, 'buy') && !has(hc, 'price'));
  const hn = buy({ state: { kind: 'normal' } });
  check('a style that can be bought: the price of the selected style on the label, the button, no named style the customer did not choose',
    text(hn).includes('1 eye · Powder Burst') && has(hn, 'price') && has(hn, 'buy') && !/Couple Duo/.test(hn) && text(hn).includes('1 eye: €19.97 for') && text(hn).includes('€24.97 for every other style.'));
  check('the hint names the pair price only where two eyes can be ordered (max_eyes)', text(buy({ ordering: { open: true, prices: { one_eye_studio_black: 1997, one_eye_art: 2497, two_eyes: 3997, each_further_eye: 1500 }, maxEyes: 1 } })).includes('Add a second eye') === false && text(hn).includes('Add a second eye: €39.97 for both.'));
  const hw = buy({ wordsBlocked: true, waiver: true });
  check('a word the artwork font cannot draw shuts the button and says why', /data-testid="buy"[^>]*disabled/.test(hw) && text(hw).includes('Please fix the words on the artwork first'));
  check('while the tile list is asked for the card waits and says so; with nothing to select and nothing loading it is not shown at all', has(buy({ loading: true, state: { kind: 'none' } }), 'buy-wait') && buy({ state: { kind: 'none' } }) === '');

  // ---- 2026-10-14: ONE eye that fails the lid rule while Clean Iris and Celestial Gold are hard. In production those two are live and the advisory styles (Powder Burst,
  // Splash) open soon until their 4K plates are in storage, so the eye is held back from every style that can be bought: the page must say what to do and must not offer
  // a way that is false ("choose another", "buy anyway"). The server's tile list is stood in for by the tiles it sends for such an eye (api/_lib/catalogue.py tile_row).
  const liOf = (h: string, slug: string) => { const at = h.indexOf(`data-testid="tile-${slug}"`); return at < 0 ? '' : h.slice(at, h.indexOf('</li>', at)); };
  const priceOfReal = (t: ServerTile) => (showsPrice(1, t) ? (t.price_class === 'black' ? 'P-BLACK' : 'P-ART') : null);      // the page's own rule: a price only on a tile that can be bought now
  const goldHeld = tile('solo.gold', { name: 'Celestial Gold', slug: 'celestial-gold', gate: 'hard', available: false, why: 'gate' });
  const cleanHeld = { ...singles[3], available: false, why: 'gate' } as ServerTile;
  const failEye = [bad(1, ['lid_lash_lines'])];
  const soonList = [tile('solo.powder', { name: 'Powder Burst', slug: 'powder-burst', stage: 'preview' }), tile('solo.splash', { name: 'Splash', slug: 'splash', stage: 'preview' }), goldHeld, singles[2], cleanHeld];
  const mLid = model(1, soonList, failEye);
  const hLid = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], mLid)));
  const hLidBuy = buy({ state: buyState({ n: 1, tiles: soonList, selected: mLid.selected }), styleName: 'Powder Burst', advisory: [1], retake: mLid.retake });
  const tLid = text(hLid + hLidBuy);
  // adapted 2026-10-22: Clean Iris and Celestial Gold were drawn greyed with "Retake eye 1 first"; held back for these eyes, they are not shown now. The group is not
  // all Soon (two of its styles can be ordered after a retake), so its Soon tiles keep their chips and no group line says the group opens soon
  check('a single eye that fails the lid rule: Clean Iris and Celestial Gold are not shown (no "Retake eye 1 first", no warning sign), Powder Burst, Splash and Radiance are drawn with the Soon chip, nothing is recommended and no group line says the group opens soon',
    !has(hLid, 'tile-clean-iris') && !has(hLid, 'tile-celestial-gold') && !tLid.includes('Retake eye 1 first') && (hLid.match(/data-state="soon"/g) ?? []).length === 3 && (hLid.match(/data-testid="soon"/g) ?? []).length === 3
    && !has(hLid, 'recommended') && !has(hLid, 'group-soon') && !liOf(hLid, 'clean-iris') && !/triangle-alert|alert-triangle/.test(hLid.slice(hLid.indexOf('style-picker'))), hLid.slice(0, 200));
  // adapted 2026-10-22: the way out was the retake card under the list (reasons, tip, "greyed out", e-mail); it is the buy card's line and the retake button now
  check('... the way out is on the buy card: its one line and the retake button of the eye; no retake card under the list, no reasons, no tips, no e-mail',
    !has(hLid, 'retake-state') && !has(hLid, 'retake-calm') && !has(hLid, 'manual-route') && has(hLidBuy, 'retake-eye-1') && text(hLidBuy).includes('Retake this eye')
    && !tLid.includes('Your eye needs a retake') && !tLid.includes('greyed out') && !/mailto:/.test(hLid + hLidBuy));
  check('... the free preview on screen is a Soon style and says so; the warning of the advisory style stays under the picture',
    has(hLid, 'artwork') && tLid.includes('Preview reduced and watermarked. This style opens soon.') && has(hLid, 'advisory-note') && tLid.includes('An eyelid or lash is still in the ring of your iris. Retake it for a cleaner result.'));
  check('... the buy card says it in one line with the retake button under it: no price, no waiver, no button to buy, no "see above", and it is not the "choose another" line (no other style can be ordered)',
    has(hLidBuy, 'buy-retake') && text(hLidBuy).includes(COPY.en.picker.retakeBuy(1)) && !has(hLidBuy, 'buy') && !has(hLidBuy, 'waiver') && !has(hLidBuy, 'price') && !has(hLidBuy, 'buy-soon') && !text(hLidBuy).includes(COPY.en.picker.soonBuy)
    && !/see above|named above/i.test(text(hLidBuy))
    && !/\d{4}|€|\d[,.]\d\d/.test(text(hLidBuy).replace('Price for this artwork', '')), text(hLidBuy));
  check('... nothing on the page offers a way that is false: no "choose another", no "buy anyway", no "order now" for a set that cannot order, and no price is printed on any tile',
    !/choose another|buy anyway|order anyway|order now|to order now/i.test(tLid.replace(COPY.en.picker.retakeBuy(1), '')) && !has(hLid, 'tile-price'), tLid.match(/choose another|buy anyway|order anyway|order now/i)?.[0] ?? '');
  // the same eye once Powder Burst and Splash are live and ticked: they warn and sell, the hard two stay greyed, nothing is a dead end
  const sellList = [tile('solo.powder', { name: 'Powder Burst', slug: 'powder-burst' }), tile('solo.splash', { name: 'Splash', slug: 'splash' }), goldHeld, singles[2], cleanHeld];
  const mSell = model(1, sellList, failEye, { priceOf: priceOfReal }, 'solo.powder', 'reason.solo_powder.own');
  const hSell = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], mSell)));
  const hSellBuy = buy({ state: buyState({ n: 1, tiles: sellList, selected: mSell.selected }), advisory: [1] });
  // adapted 2026-10-22: Clean Iris and Celestial Gold "stay greyed" with a retake card under the list; they are not shown now, and nothing under the list asks for a retake
  check('a single eye that fails the lid rule with Powder Burst and Splash live: they warn in one calm line and sell (the warning is above the waiver, the button is there), Clean Iris and Celestial Gold are not shown, no retake card, no e-mail, and the card does not say retake',
    has(hSell, 'recommended') && !text(hSell).includes('Retake eye 1 first') && !has(hSell, 'tile-clean-iris') && !has(hSell, 'retake-state') && !has(hSell, 'manual-route') && has(hSell, 'advisory-note')
    && !/triangle-alert|alert-triangle/.test(hSell.slice(hSell.indexOf('data-testid="advisory-note"'), hSell.indexOf('data-testid="advisory-note"') + 400))
    && has(hSellBuy, 'buy') && has(hSellBuy, 'waiver') && hSellBuy.indexOf('data-testid="buy-advisory"') > 0 && hSellBuy.indexOf('data-testid="buy-advisory"') < hSellBuy.indexOf('data-testid="waiver"') && !has(hSellBuy, 'buy-retake'));
  // a set that passes: the policy changes nothing for it
  const passList = [tile('solo.powder', { name: 'Powder Burst', slug: 'powder-burst' }), tile('solo.gold', { name: 'Celestial Gold', slug: 'celestial-gold', gate: 'hard' }), { ...singles[3] } as ServerTile];
  const mPass = model(1, passList, [eye(1)], { priceOf: priceOfReal }, 'solo.powder');
  const hPass = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], mPass)));
  check('a set that passes the lid rule: nothing is held back or warned, the two hard styles are ready and carry their price, no retake state and no manual route',
    !has(hPass, 'retake-state') && !has(hPass, 'advisory-note') && !has(hPass, 'manual-route') && (hPass.match(/data-state="ready"/g) ?? []).length === 3 && (hPass.match(/data-testid="tile-price"/g) ?? []).length === 3
    && !has(buy({ state: buyState({ n: 1, tiles: passList, selected: mPass.selected }) }), 'buy-retake'));

  // ---- the notes under the picture: what the server said about the picture it drew
  const stackArt: Art = { ...art(), fallback: 'stack_contrast' };
  const wideArt: Art = { ...art(), fallback: 'overlap_fallback' };
  const mPair = model(2, pair, [eye(1), eye(2)]);
  const hStack = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], mPair, { art: stackArt })));
  const hWide = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], mPair, { art: wideArt })));
  check('a pair drawn in stack mode says so in one line; a pair with wide pupils says the irises touch; neither otherwise', text(hStack).includes('Your two irises differ strongly in colour, so one sits in front of the other.') && !has(hStack, 'wide-pupil')
    && text(hWide).includes('Your pupils are wide, so the irises touch instead of overlapping.') && !has(hWide, 'stack-note') && !has(renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], mPair))), 'stack-note'));
  check('a Soon style\'s preview note says it opens soon and does not promise a file', text(hStack).includes('Preview reduced and watermarked. This style opens soon.') && !text(hStack).includes('Your file:'));
  // ---- Family Orbit (the ensemble family, 2026-10-20): the customer chooses the eye in the middle (the layout orbit: the first eye of the order is the hub)
  const orb = [tile('grp.orb', { name: 'Family Orbit', group: 'grp', stage: 'preview', gate: 'hard', layouts: ['orbit'], eyes: 4 })];
  const mOrb = model(4, orb, [eye(1), eye(2), eye(3), eye(4)]);
  const four = [eyeObj('a'), eyeObj('b'), eyeObj('c'), eyeObj('d')];
  const hOrb2 = renderToStaticMarkup(createElement(ResultView, rvProps(four, mOrb, { layout: 'orbit', selectedId: 'b' })));
  const hOrb1 = renderToStaticMarkup(createElement(ResultView, rvProps(four, mOrb, { layout: 'orbit', selectedId: 'a' })));
  const hRing = renderToStaticMarkup(createElement(ResultView, rvProps(four, mOrb, { layout: 'ring', selectedId: 'b' })));
  check('the layout orbit (Family Orbit): the selected eye has a "Put in the centre" button with its own label, the eye already in the centre has it pressed and shut, a line says the first eye is the centre; no such button on another layout',
    has(hOrb2, 'centre-eye') && /data-testid="centre-eye"[^>]*aria-label="Put eye 2 in the centre of the artwork"/.test(hOrb2) && !/data-testid="centre-eye"[^>]*disabled/.test(hOrb2)
    && /data-testid="centre-eye"[^>]*disabled/.test(hOrb1) && has(hOrb2, 'centre-note') && text(hOrb2).includes('The first eye is in the centre') && !has(hRing, 'centre-eye') && !has(hRing, 'centre-note'));
  check('the layout glyph of orbit is one eye in the middle and the others round it', glyphPoints('orbit', 5).pts.length === 5 && glyphPoints('orbit', 5).pts[0][0] === 10 && glyphPoints('orbit', 5).pts[0][1] === 8);
  const hLive = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], m1)));
  check('a style that can be bought keeps the promise of the file under its preview', text(hLive).includes('Your file: 4096 px'));
  const hSaved = hLive.match(/download="([^"]+)"/)?.[1] ?? '';
  check('the saved preview\'s file name comes from the style\'s slug, not its id', hSaved === 'snapeyes-preview-powder-burst-1-eye.jpg', hSaved);

  // ---- no preview can be drawn (a trio that fails the gate): the retake state takes the place of the picture
  const hNone = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b'), eyeObj('c')], { ...m3, style: null, selected: undefined }, { art: undefined })));
  // adapted 2026-10-22: the retake card with "We cannot show a preview of these eyes yet." and its reasons is one calm line and the retake button now
  check('when nothing can be drawn one calm line and the retake button stand where the picture would be, the eye to retake is marked, and nothing is for sale', has(hNone, 'no-preview') && !has(hNone, 'artwork') && has(hNone, 'retake-calm') && has(hNone, 'retake-eye-3') && has(hNone, 'chip-retake-3')
    && !has(hNone, 'chip-retake-1') && text(hNone).includes(COPY.en.picker.retake.calm) && !text(hNone).includes('We cannot show a preview') && !/eyelid|lash|mailto/i.test(hNone.slice(hNone.indexOf('no-preview'))));

  // ---- every style held for the pupil (review of WP11, M2): the frame says what to do; it never waits for a picture that will not come
  const barPair = pair.map((t) => ({ ...t, available: false, why: 'bar_pupil' }));
  const barEyes = [eye(1, { pupil: 'bar' }), eye(2, { pupil: 'bar' })];
  const mBar: PickerModel = { ...model(2, barPair, barEyes, { tilePicture: () => undefined }), style: null, selected: undefined, retake: retakeView({ tiles: barPair, eyes: barEyes, selected: undefined }) };
  const hBar = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], mBar, { art: undefined, onRemove: noop })));
  const hBarPanel = renderToStaticMarkup(createElement(CalmRetake, { view: mBar.retake!, total: 2, onRetake: noop, onRemove: noop }));
  // adapted 2026-10-22: the pupil card (its sentence, the tip, the e-mail) is the calm line now; the retake and the remove buttons per eye stay
  check('two eyes, every tile held for the pupil: no "Composing" and no spinner frame; the calm line stands where the picture would be, with a retake and a remove button per eye',
    has(hBar, 'no-preview') && !has(hBar, 'artwork') && !text(hBar).includes(T.result.composing) && !hBar.includes('animate-spin') && has(hBar, 'retake-calm') && text(hBar).includes(COPY.en.picker.retake.calm)
    && has(hBar, 'retake-eye-1') && has(hBar, 'retake-eye-2') && has(hBarPanel, 'remove-eye-1') && has(hBarPanel, 'remove-eye-2') && !has(hBar, 'manual-route'));
  check('the pupil case marks the eyes on their chips and blames nothing (no pupil, lid or reflection sentence, no "cleaner iris")',
    has(hBar, 'chip-retake-1') && has(hBar, 'chip-retake-2') && !/round pupils|eyelid|reflection|cleaner iris/i.test(text(hBar)));
  check('a remove button only where there is more than one eye and a way to remove (one eye has the retake button alone)',
    !has(renderToStaticMarkup(createElement(CalmRetake, { view: mBar.retake!, total: 1, onRetake: noop, onRemove: noop })), 'remove-eye-1') && !has(renderToStaticMarkup(createElement(CalmRetake, { view: mBar.retake!, total: 2, onRetake: noop })), 'remove-eye-1'));
  const tileBar = renderToStaticMarkup(createElement(StylePicker, { model: mBar }));
  // adapted 2026-10-22: it was "every held tile says Not for this pupil shape": a held tile is not shown
  check('no tile held for the pupil is shown, and none says "Not for this pupil shape"', !/data-testid="tile-(?!list|skeleton|retry|price)/.test(tileBar) && !tileBar.includes('Not for this pupil shape'));
  const mTrioBar: PickerModel = { ...model(3, [tile('grp.fam', { group: 'grp', gate: 'hard', available: false, why: 'bar_pupil', layouts: ['trio'], eyes: 3 })], [eye(1), eye(2, { pupil: 'bar' }), eye(3)], { tilePicture: () => undefined }), style: null, selected: undefined,
    retake: retakeView({ tiles: [tile('grp.fam', { group: 'grp', gate: 'hard', available: false, why: 'bar_pupil', layouts: ['trio'], eyes: 3 })], eyes: [eye(1), eye(2, { pupil: 'bar' }), eye(3)], selected: undefined }) };
  const hTrioBar = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b'), eyeObj('c')], mTrioBar, { art: undefined })));
  // adapted 2026-10-22: "the state names eye 2 and says why" is the calm line and the retake button of eye 2 now
  check('three eyes with the Trio live and held for one pupil: the calm line with the retake button of eye 2, nothing waits; the buy card has nothing to sell and is not drawn',
    has(hTrioBar, 'no-preview') && has(hTrioBar, 'retake-eye-2') && !has(hTrioBar, 'retake-eye-1') && has(hTrioBar, 'chip-retake-2') && !has(hTrioBar, 'chip-retake-1') && !text(hTrioBar).includes(T.result.composing)
    && buy({ eyes: [eyeObj('a'), eyeObj('b'), eyeObj('c')], state: buyState({ n: 3, tiles: [tile('grp.fam', { group: 'grp', available: false, why: 'bar_pupil', eyes: 3 })], selected: undefined }) }) === '');
  // no style at all for this many eyes: the frame still never waits
  const mNone: PickerModel = { ...emptyPicker(2), catalog: { key: 'k', n: 2, tiles: [], pick: null, reasonKey: null, eyes: [eye(1), eye(2)] }, style: null, selected: undefined, retake: null };
  const hNoStyle = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], mNone, { art: undefined })));
  check('a tile list with no style in it: the frame says so, offers the way to ask us, and never shows "Composing" or the spinner',
    has(hNoStyle, 'no-preview') && has(hNoStyle, 'no-styles') && has(hNoStyle, 'manual-route') && !has(hNoStyle, 'artwork') && !text(hNoStyle).includes(T.result.composing) && !hNoStyle.includes('animate-spin')
    && text(hNoStyle).includes('No style can be shown for this number of eyes yet. Remove an eye, or write to us.'));
  const hLoadingList = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], emptyPicker(2), { art: undefined })));
  check('while the tile list is still being asked for (no catalogue yet) the frame does say "Composing": that wait is real', text(hLoadingList).includes(T.result.composing) && !has(hLoadingList, 'no-preview'));

  // ---- a Soon look under a live style (review of WP11, M1): no price, no button, one line that names the look
  const uniSoon = tile('solo.universe', { name: 'Universe', slug: 'universe', gate: 'hard', rule: 'fill', looks: { echo: 'live', vortex: 'preview' } });
  const mLook = model(1, [singles[0], uniSoon], [eye(1)], { priceOf, look: 'vortex', style: 'solo.universe' }, 'solo.powder');
  const hLook = renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], mLook)));
  check('the preview note of a live style whose look opens soon says that look opens soon and does not promise a file; the live look keeps the promise',
    text(hLook).includes('The Vortex look opens soon.') && !text(hLook).includes('Your file:')
    && text(renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], { ...mLook, look: 'echo' })))).includes('Your file: 4096 px'));
  const hLookBuy = buy({ styleName: 'Universe', state: buyState({ n: 1, tiles: [singles[0], uniSoon], selected: uniSoon, look: 'vortex' }) });
  check('the buy card of a Soon look: the line names the look, no price, no waiver, no button, no date', text(hLookBuy).includes('The Vortex look opens soon. Choose another look or style to order now.')
    && !has(hLookBuy, 'buy') && !has(hLookBuy, 'waiver') && !has(hLookBuy, 'price') && !/\d{4}|€|\d[,.]\d\d/.test(text(hLookBuy).replace('Price for this artwork', '')));
  check('the same style with its live look is for sale: the price and the button',
    has(buy({ styleName: 'Universe', state: buyState({ n: 1, tiles: [singles[0], uniSoon], selected: uniSoon, look: 'echo' }) }), 'buy'));

  // ---- four to eight eyes: an eye moves one place at a time
  const eyes4 = ['a', 'b', 'c', 'd'].map((id) => eyeObj(id));
  const grp4 = [tile('grp.fam', { name: 'Family Colours', group: 'grp', stage: 'preview', gate: 'hard', layouts: ['zigzag', 'cluster', 'ring'], eyes: 4 })];
  const h4 = renderToStaticMarkup(createElement(ResultView, { ...rvProps(eyes4, model(4, grp4, eyes4.map((_, i) => eye(i + 1))), { layout: 'zigzag', layoutOptions: ['zigzag', 'cluster', 'ring'] }), selectedId: 'a' }));
  check('four eyes: Move earlier and Move later with the eye\'s number for a screen reader, the first cannot move earlier; three layout chips', has(h4, 'move-earlier') && has(h4, 'move-later') && /data-testid="move-earlier"[^>]*disabled|disabled[^>]*data-testid="move-earlier"/.test(h4)
    && h4.includes('aria-label="Move eye 1 later on the artwork"') && (h4.match(/role="radio"/g) ?? []).length === 3 && text(h4).includes('Zigzag'));
  check('three eyes or fewer have no move buttons; two eyes can swap places, three can rotate, one eye neither',
    !has(renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], mPair))), 'move-earlier')
    && has(renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], mPair))), 'swap-places')
    && has(renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b'), eyeObj('c')], model(3, [tile('grp.fam', { stage: 'preview', gate: 'hard', layouts: ['trio'], eyes: 3 })], [eye(1), eye(2), eye(3)])))), 'rotate-places')
    && !has(hLive, 'swap-places') && !has(hLive, 'rotate-places'));
  const legacyPair = model(2, [tile('studio_black', { legacy: 1, gate: 'none', layouts: ['duo', 'fusion'], eyes: 2 })], [eye(1), eye(2)]);
  check('the six old styles take no swap and no rotate (they ignore them)', !has(renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('a'), eyeObj('b')], legacyPair))), 'swap-places'));

  // ---- the layout glyphs: every layout id of the registry draws something
  const ids = [...LAYOUT_IDS];
  check('every layout id the registry knows has a glyph with at least one disc inside the box', ids.length >= 15 && ids.every((id) => { const g = glyphPoints(id, 6); return g.pts.length >= 1 && g.r > 0 && g.pts.every(([x, y]) => x >= 0 && x <= 20 && y >= 0 && y <= 16); }), ids.filter((id) => glyphPoints(id, 6).pts.length < 1).join());

  // ---- the words on the artwork
  const wm = { ...emptyWords(2), names: ['Anna', ''], date: '14 June 2026', problems: [{ code: 'glyph', eye: 2, chars: ['Ж'] }] as never };
  const hw2 = renderToStaticMarkup(createElement(Words, { model: wm }));
  check('a name field per eye with its own label and the 24 letter limit; a letter the font cannot draw is told under its field and marks it invalid',
    (hw2.match(/maxLength="24"/g) ?? []).length === 2 && text(hw2).includes('Name for eye 1') && text(hw2).includes('Name for eye 2') && hw2.includes('aria-invalid="true"') && text(hw2).includes('The artwork font cannot draw Ж. Please use another letter.') && /maxLength="20"/.test(hw2));
  check('one eye: a single "Name (optional)"; the family name is not offered (no arrangement draws it yet)', text(renderToStaticMarkup(createElement(Words, { model: emptyWords(1) }))).includes('Name (optional)') && !has(renderToStaticMarkup(createElement(Words, { model: emptyWords(2) })), 'words-family')
    && has(renderToStaticMarkup(createElement(Words, { model: { ...emptyWords(2), showFamily: true } })), 'words-family'));

  // ---- reduced motion: nothing of the picker moves unless the visitor allows motion
  const rmHtml = hLoad + hLoadTile + renderToStaticMarkup(createElement(ResultView, rvProps([eyeObj('e1')], m1, { art: undefined })));
  check('reduced motion: nothing of the picker or the result loops or fades by a utility (no animate-*, no transition-opacity): its changes are the flow classes fx-*, which the stylesheet switches off', rmHtml.includes('fx-pick') && !/(^|[^:\w-])(animate-[a-z]+|transition-opacity)/.test(rmHtml),
    rmHtml.match(/(^|[^:\w-])(animate-[a-z]+|transition-opacity)/)?.[0] ?? '');

  // ---- the four languages
  const SOON = { en: 'Soon', de: 'Bald', lt: 'Netrukus', hu: 'Hamarosan' } as Record<Lang, string>;
  const GROUPS = { en: ['Just you', 'Two of you', 'Family'], de: ['Nur Sie', 'Sie zu zweit', 'Familie'], lt: ['Tik Jūs', 'Jūs dviese', 'Šeima'], hu: ['Csak te', 'Ti ketten', 'Család'] } as Record<Lang, string[]>;
  const reasonKeys = new Set<string>();
  for (const d of Object.values(STYLES)) for (const v of Object.values(d.reason)) reasonKeys.add(v);
  const claims = /\b(unique|one of a kind|never repeated|no two alike|handmade|hand-painted|bestseller|best seller|most chosen|most popular)\b|einzigartig|einmalig|handgemacht|legvalasztottabb|vienintel|unikali|vienetin/i;
  for (const lang of LANGS) {
    setCopyLang(lang);
    const P = COPY[lang].picker;
    check(`${lang}: the group words and lines are the landing page's, the Soon word too`, GROUPS[lang].join() === [P.groups.one, P.groups.two, P.groups.family].join() && P.soon === SOON[lang]);
    check(`${lang}: every reason line the registry can name has its words (${reasonKeys.size} keys)`, [...reasonKeys].every((k) => typeof (P.reasons as Record<string, string>)[k] === 'string' && (P.reasons as Record<string, string>)[k].length > 8), [...reasonKeys].filter((k) => !(P.reasons as Record<string, string>)[k]).join());
    const hh = renderToStaticMarkup(createElement(StylePicker, { model: m1 }));
    const all: string[] = [];
    const walk = (v: unknown, path: string) => {
      if (typeof v === 'string') all.push(v);
      else if (typeof v === 'function') { for (const args of [[2], [1, 'Kiss Collision'], ['Kiss Collision', 'Powder Burst', 2], [[1, 3], 4], [[2], 1], [2, 24], ['Ñ'], ['Kiss Collision', 'Powder Burst'], ['Powder Burst']]) { try { const r = (v as (...a: unknown[]) => unknown)(...args); if (typeof r === 'string') all.push(r); } catch { /* wrong argument kinds for this one */ } } }
      else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) walk(x, `${path}.${k}`);
    };
    walk(P, 'picker'); walk(COPY[lang].price, 'price');
    const joined = all.join(' | ');
    check(`${lang}: no claim of uniqueness, "best seller" or "most chosen" in the picker, the tiles or the price lines`, !claims.test(joined) && !claims.test(text(hh)), joined.match(claims)?.[0] ?? '');
    check(`${lang}: no dash, no "Couple Duo" and no "Studio Black" in the picker or the price lines (the black class is named by the registry)`, !new RegExp('[' + String.fromCharCode(0x2012, 0x2013, 0x2014, 0x2015) + ']').test(joined) && !/Couple Duo|Studio Black/.test(joined));
    check(`${lang}: the tile list prints in this language (group, alt text and the Recommended mark)`, text(hh).includes(GROUPS[lang][0]) && text(hh).includes(P.recommended) && hh.includes(`alt="${P.tileAlt('Powder Burst')}"`));
    // adapted 2026-10-22: the retake card (its reasons, tips and e-mail) is the calm line; it is held to speaking this language, and so are its buttons
    check(`${lang}: the calm retake line and its buttons speak this language, no English left in them`,
      (() => {
        const t1 = text(renderToStaticMarkup(createElement(CalmRetake, { view: m3.retake!, total: 3, onRetake: noop })));
        return P.retake.calm.length > 20 && t1.includes(P.retake.calm) && t1.includes(T.result.retakeEye(3)) && (lang === 'en' || (P.retake.calm !== COPY.en.picker.retake.calm && !/photo|retake|styles/i.test(t1)));
      })());
    // adapted 2026-10-22: the pupil sentence went with the retake card; the no-style sentence and the Soon look lines stay
    check(`${lang}: the no-style sentence and the Soon look lines are written out, name the look and are not the English ones (review of WP11); the calm line of a pupil case offers the remove button`,
      (() => {
        const en = COPY.en.picker;
        const pupilRender = text(renderToStaticMarkup(createElement(CalmRetake, { view: mBar.retake!, total: 2, onRetake: noop, onRemove: noop })));
        const base = P.retake.noStyles.length > 30 && P.soonLookBuy('Vortex').includes('Vortex') && P.soonLookNote('Vortex').includes('Vortex') && pupilRender.includes(T.result.remove(1));
        return base && (lang === 'en' || (P.retake.noStyles !== en.retake.noStyles && P.soonLookBuy('Vortex') !== en.soonLookBuy('Vortex') && P.soonLookNote('Vortex') !== en.soonLookNote('Vortex')));
      })());
    // adapted 2026-10-22: "Retake eye 3 first" (the held tile) and the retake card's title are gone
    check(`${lang}: the Soon note and the changed lines are written out`, P.soonBuy.length > 20 && P.countSoon(2).includes('2') && P.changed.eyes('A', 'B', 3).includes('A') && P.changed.gate('A', 'B', 2).includes('B') && P.advisory([1, 3], 4).includes('3'));
    check(`${lang}: the buy card of a single eye held back from every style it could buy (retake) is written out for one eye and for more, is not the "choose another" line, and speaks this language`,
      (() => {
        const en = COPY.en.picker;
        const rb1 = P.retakeBuy(1), rb3 = P.retakeBuy(3);
        const card = text(buy({ state: { kind: 'retake' }, eyes: [eyeObj('a')] }));
        const card3 = text(buy({ state: { kind: 'retake' }, eyes: [eyeObj('a'), eyeObj('b'), eyeObj('c')] }));
        const base = rb1.length > 40 && rb3.length > 40 && rb1 !== rb3 && rb1 !== P.soonBuy && rb3 !== P.soonBuy && card.includes(rb1) && card3.includes(rb3) && !card.includes(P.soonBuy);
        return base && (lang === 'en' || (rb1 !== en.retakeBuy(1) && rb3 !== en.retakeBuy(3) && !/Nothing can be|To order|retake/i.test(card + card3)));
      })());
    // adapted 2026-10-22: the reseal sentence went with the retake card; an eye with no sealed gate value (an unmeasured profile, an older seal) gets the same calm line and
    // its retake button, which names no cause at all
    check(`${lang}: an eye with no sealed gate value that holds every style back gets the calm line and its retake button, naming no cause`,
      (() => {
        const view = retakeView({ tiles: [tile('solo.clean', { gate: 'hard', available: false, why: 'reseal' })], eyes: [eye(1, { gate: { lid: null, fill: null } })], selected: undefined })!;
        const html = renderToStaticMarkup(createElement(CalmRetake, { view, total: 1, onRetake: noop }));
        return text(html) === `${P.retake.calm} ${T.result.retakeOnly}` && has(html, 'retake-eye-1') && !/older version|ältere|älteren|senesn|régebbi/i.test(text(html));
      })());
    check(`${lang}: the same twelve option and word labels exist and none is empty`, [P.options.swap, P.options.rotate, P.options.earlier, P.options.later, P.options.look, P.names.title, P.names.date, P.names.family, P.names.datePlaceholder, P.stack, P.widePupil, P.groupSoon].every((s) => s.trim().length > 2));
  }
  setCopyLang('en');
  check('the buy state of a Soon pair, read from the same tiles the page prints: countSoon for two eyes, the word "opens soon" nowhere with a date', JSON.stringify(buyState({ n: 2, tiles: pair, selected: pair[0] })) === '{"kind":"countSoon","n":2}' && !/\b(20\d\d|Q[1-4]|January|February|March|April|June|July)\b/.test(COPY.en.picker.soonBuy + COPY.en.picker.groupSoon + COPY.en.picker.countSoon(2)));
  void T;
  return out;
}
