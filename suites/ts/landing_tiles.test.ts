// I2 (the landing aligned with the registry): the tiles, the group lines, the price rows, the hero line and the FAQ answer read ONE rule of the registry and the run-time
// catalogue (src/landing/tileState.ts, src/shared/catalogue.ts saleCatalogue, src/landing/heroPrice.ts, src/landing/copy/index.ts faqEntries), the names a tile prints are the
// registry's and the copy holds none, and the page rendered in the states of the catalogue (src/landing/shell/gate.tsx, the build's gate) says what can be bought and nothing else.
// The page is rendered WIRED (the gallery, the price table, the hero and the FAQ as the live page builds them, reading the catalogue through the hooks of src/landing/ordering.ts from a
// store that asks a stand-in server), and the store itself is run here against stand-in answers, because the line that turns an answer into what the page can sell is the one the page's
// promise rests on (the review of I2 planted defects in exactly such lines and found nothing red but a browser check).
// Loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { NOTHING_FOR_SALE, fallbackCatalogue, liveFor, ordersOpen, readCatalogue, saleCatalogue, severalMax, type RunCatalogue } from '../../src/shared/catalogue';
import { OrderingContext, createOrdering, useOrderingOpen, useSaleCatalogue, useSuggestedMarket, type Ask } from '../../src/landing/ordering';
import { STYLES, styleName } from '../../src/shared/styles';
import { GALLERY } from '../../src/landing/assets.data';
import { groupLine, saleTiles, tileName, tileRow, tileState } from '../../src/landing/tileState';
import { tileCopy } from '../../src/landing/gallery';
import { HELD_PRICE, heroPrice } from '../../src/landing/heroPrice';
import { faqEntries } from '../../src/landing/copy/index';
import { landingPrices } from '../../src/landing/priceText';
import { priceList } from '../../src/shared/markets';
import { renderGate } from '../../src/landing/shell/gate';
import en from '../../src/landing/copy/en.json';
import de from '../../src/landing/copy/de.json';
import lt from '../../src/landing/copy/lt.json';
import hu from '../../src/landing/copy/hu.json';

type R = Array<[string, boolean, string?]>;

export async function run(): Promise<R> {
  const out: R = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const tiles = [...GALLERY.one, ...GALLERY.two, ...GALLERY.family];
  const ids = tiles.map((t) => t.id);
  const idsOf = (g: 'one' | 'two' | 'family') => GALLERY[g].map((t) => t.id);

  // a catalogue as GET /api/checkout would answer it, read by the page's own reader
  const answer = (live: Record<string, Record<string, string>>, max: number) => ({
    ok: true, open: true, orderable_max_eyes: max,
    styles: Object.entries(live).map(([id, stages]) => ({ id, name: STYLES[id].name, slug: STYLES[id].slug, group: STYLES[id].group, eyes: STYLES[id].eyes, stages })),
  });
  const trio = readCatalogue(answer({ 'solo.clean': { '1': 'live' }, 'solo.powder': { '1': 'live' }, 'grp.collision': { '3': 'live', '4': 'preview' }, 'solo.radiance': { '1': 'preview' } }, 3))!;
  const oneStyle = readCatalogue(answer({ 'solo.powder': { '1': 'live' }, 'solo.clean': { '1': 'preview' } }, 1))!;
  const nothing = readCatalogue(answer({ 'solo.powder': { '1': 'preview' }, 'solo.clean': { '1': 'preview' } }, 0))!;
  const pairs = readCatalogue(answer({ 'solo.powder': { '1': 'live' }, 'duo.kiss_collision': { '2': 'live' }, 'duo.clean': { '2': 'live' }, 'grp.collision': { '3': 'live', '4': 'live' } }, 4))!;

  // --- names: the registry's, and no tile name in any language of the copy
  check('every tile prints the registry\'s name of the style it stands for (tileName), and the name is one of the registry\'s',
    ids.every((id) => { const r = tileRow(id); return !!r && tileName(id) === STYLES[r.id].name && tileName(id) === styleName(r.id); }), ids.map((id) => `${id}=${tileName(id)}`).join());
  check('the names of the 14 tiles: Radiance, Powder Burst, Universe, Celestial Gold, Splash, Clean Iris, Collision Infinity twice, Kiss Collision, Clean Infinity, Family Colours four times (no tile for the held Universe pair and family: release review H-M3)',
    ids.map(tileName).join(', ') === 'Radiance, Powder Burst, Universe, Celestial Gold, Splash, Clean Iris, Collision Infinity, Collision Infinity, Kiss Collision, Clean Infinity, Family Colours, Family Colours, Family Colours, Family Colours',
    ids.map(tileName).join(', '));
  check('a tile id the table does not know (or a hostile one: constructor, __proto__) has no row, no name, and is never for sale',
    ['nope', 'constructor', '__proto__', 'toString', ''].every((id) => tileRow(id) === null && tileName(id) === '' && tileState(id, trio).sale === 'soon' && tileState(id, trio).style === null), '');
  for (const [lang, c] of [['en', en], ['de', de], ['lt', lt], ['hu', hu]] as const) {
    const items = c.styles.items as Record<string, Record<string, string>>;
    check(`the copy (${lang}) holds no tile name: every tile's entry is its description "d" only`,
      ids.every((id) => items[id] && Object.keys(items[id]).join() === 'd' && items[id].d.length > 10) && Object.keys(items).length === ids.length, Object.keys(items['powder'] ?? {}).join());
    check(`tileCopy (${lang}) gives the registry's name and the copy's description`,
      tiles.every((t) => { const x = tileCopy(c as never, t); return x.n === tileName(t.id) && x.d === items[t.id].d; }), '');
  }

  // --- states
  check('tileState: for sale only when the catalogue lists the tile\'s style live for the tile\'s number of eyes: with the Trio, Clean Iris and Powder Burst live that is the Trio, Clean Iris and Powder Burst tiles, every other tile (Radiance at preview, the pairs, the four to six eyes) is Soon',
    ids.filter((id) => tileState(id, trio).sale === 'sale').join() === 'powder,clean,fam_trio', ids.filter((id) => tileState(id, trio).sale === 'sale').join());
  check('tileState: one style ticked is one tile; nothing ticked, the closed page (NOTHING_FOR_SALE) and the fallback are none; a style live for one count is not for sale at another (the Trio\'s style at four eyes)',
    ids.filter((id) => tileState(id, oneStyle).sale === 'sale').join() === 'powder' && ids.every((id) => tileState(id, nothing).sale === 'soon' && tileState(id, NOTHING_FOR_SALE).sale === 'soon' && tileState(id, fallbackCatalogue()).sale === 'soon')
    && tileState('fam_4', trio).sale === 'soon' && tileState('fam_trio', trio).sale === 'sale' && liveFor(trio, 'grp.collision', 3) && !liveFor(trio, 'grp.collision', 4), '');
  check('a tile reads the catalogue for ITS style: with the Kiss and Clean pairs live the Clean Infinity tile is for sale and the Collision Infinity tiles of the same group stay Soon',
    (() => {
      const s = tileState('duo_clean', pairs);
      return s.style === 'duo.clean' && s.sale === 'sale' && tileState('duo_infinity_bb', pairs).sale === 'soon' && tileState('duo_infinity', pairs).sale === 'soon';
    })(), '');
  check('saleTiles: the registry names of the tiles for sale in tile order, each name once, with how many tiles of the list can be bought (two Collision Infinity tiles name it once)',
    JSON.stringify(saleTiles(idsOf('one'), trio)) === JSON.stringify({ names: ['Powder Burst', 'Clean Iris'], sale: 2, total: 6 })
    && JSON.stringify(saleTiles(idsOf('two'), pairs)) === JSON.stringify({ names: ['Kiss Collision', 'Clean Infinity'], sale: 2, total: 4 })
    && JSON.stringify(saleTiles(['duo_infinity', 'duo_infinity_bb'], readCatalogue(answer({ 'duo.collision_infinity': { '2': 'live' } }, 2))!)) === JSON.stringify({ names: ['Collision Infinity'], sale: 2, total: 2 })
    && JSON.stringify(saleTiles(idsOf('two'), nothing)) === JSON.stringify({ names: [], sale: 0, total: 4 }), JSON.stringify(saleTiles(idsOf('one'), trio)));

  // --- the line under a group's intro
  check('groupLine: only while ordering is open; nothing of the group for sale is "soon", some is "more", all is none',
    groupLine(idsOf('one'), NOTHING_FOR_SALE) === null && groupLine(idsOf('two'), NOTHING_FOR_SALE) === null
    && groupLine(idsOf('one'), trio) === 'more' && groupLine(idsOf('two'), trio) === 'soon' && groupLine(idsOf('family'), trio) === 'more' && groupLine(idsOf('two'), pairs) === 'more'
    && groupLine(['clean'], trio) === null && groupLine([], trio) === 'soon', [groupLine(idsOf('one'), trio), groupLine(idsOf('two'), trio), groupLine(idsOf('family'), trio)].join());

  // --- what a page can sell
  check('saleCatalogue: the catalogue only while the deployment takes orders AND some style can be ordered now; a style that is live while ordering is closed reads Soon, and an open deployment with nothing ticked sells nothing',
    saleCatalogue(true, trio) === trio && saleCatalogue(false, trio) === NOTHING_FOR_SALE && saleCatalogue(true, nothing) === NOTHING_FOR_SALE && saleCatalogue(true, fallbackCatalogue()) === NOTHING_FOR_SALE
    && ordersOpen(true, trio) && !ordersOpen(true, nothing) && !ordersOpen(false, trio) && NOTHING_FOR_SALE.max === 0 && NOTHING_FOR_SALE.eyes.length === 0 && NOTHING_FOR_SALE.one.length === 0, '');

  // --- the hero line
  const lp = landingPrices(priceList('eu'), 'eu', 'en');
  check('heroPrice: the lowest price among what can be bought for one eye now, held back while the prices are pending or nothing can be bought for one eye (the Trio alone, nothing ticked, closed)',
    (() => {
      const a = heroPrice(lp, false, oneStyle), b = heroPrice(lp, false, trio), c = heroPrice(lp, false, nothing), d = heroPrice(lp, false, NOTHING_FOR_SALE), e = heroPrice(lp, true, oneStyle);
      const onlyTrio = readCatalogue(answer({ 'grp.collision': { '3': 'live' } }, 3))!;
      // a held line carries no price at all (release review H-m6): HELD_PRICE stands where the number would be, a price only when the line is shown
      return a.from === lp.art && !a.held && b.from === lp.from && !b.held && c.held && d.held && e.held && heroPrice(lp, false, onlyTrio).held
        && c.from === HELD_PRICE && d.from === HELD_PRICE && e.from === HELD_PRICE && heroPrice(lp, false, onlyTrio).from === HELD_PRICE && !/[0-9]/.test(HELD_PRICE) && HELD_PRICE.length === 6;
    })(), '');

  // --- the FAQ answer about other people's eyes
  const other = (copy: typeof en, open: boolean, eyes: number) => faqEntries(copy as never, open, eyes).find((x) => x.id === 'other')!.a;
  for (const [lang, c] of [['en', en], ['de', de], ['lt', lt], ['hu', hu]] as const) {
    check(`faqEntries (${lang}): the answer about other people's eyes names no count while ordering is closed or only one eye can be bought, and prints {max} only when several eyes can be ordered`,
      !/\{max\}|\d/.test(other(c, false, 3)) && !/\{max\}|\d/.test(other(c, true, 1)) && !/\{max\}|\d/.test(other(c, true, 0)) && other(c, true, 3).includes('{max}') && other(c, true, 2).includes('{max}'), other(c, true, 3).slice(0, 80));
  }
  check('faqEntries: an item without a count in its open variant is not touched by the count (the order answer takes its open wording whatever the count)',
    faqEntries(en as never, true, 0).find((x) => x.id === 'order')!.a === faqEntries(en as never, true, 5).find((x) => x.id === 'order')!.a
    && faqEntries(en as never, true, 5).find((x) => x.id === 'order')!.a !== faqEntries(en as never, false, 5).find((x) => x.id === 'order')!.a, '');

  // --- the words that are new, in four languages
  for (const [lang, c] of [['en', en], ['de', de], ['lt', lt], ['hu', hu]] as const) {
    const s = c.styles;
    check(`the new words (${lang}): "more styles soon" and the combo card's two titles exist, the soon title and the soon line name no count, the title holds {max}, the black row takes its style from the registry`,
      s.moreSoon.length > 8 && s.comboTitleSoon.length > 8 && !/[0-9{]/.test(s.moreSoon + s.comboTitleSoon) && s.comboTitle.includes('{max}') && c.pricing.rows.black.b.includes('{name}') && c.pricing.rows.two.b === '{styles}.' && c.pricing.rows.art.b === '{styles}.',
      `${s.moreSoon} | ${s.comboTitleSoon} | ${s.comboTitle}`);
  }

  // --- the page rendered by the build's own view of it, in the states of the catalogue (the gate reads the same markup)
  const states = [
    { name: 'closed', answer: { ok: true, open: false, orderable_max_eyes: 0, styles: [] } },
    { name: 'open, one style', answer: answer({ 'solo.powder': { '1': 'live' } }, 1) },
    { name: 'open, nothing', answer: answer({ 'solo.powder': { '1': 'preview' } }, 0) },
    { name: 'open, the pairs and four eyes', answer: answer({ 'solo.powder': { '1': 'live' }, 'duo.kiss_collision': { '2': 'live' }, 'duo.clean': { '2': 'live' }, 'grp.collision': { '3': 'live', '4': 'live' } }, 4) },
  ];
  const rendered = await renderGate(states);
  const tileHtml = (si: number, lang: 'en' | 'de' | 'lt' | 'hu', id: string) => rendered.scenarios[si].langs[lang]!.tiles.find((t) => t.id === id)!.html;
  const shows = (html: string) => ({ chip: /class="lp-soon"/.test(html), price: /<b>/.test(html), state: /data-state="(\w+)"/.exec(html)?.[1] });
  check('rendered: closed, every tile of the page says Soon in its own language and prints no price; the open page with one style ticked prints a price on that one tile only and Soon on the 13 others; open with nothing ticked is as closed',
    rendered.errors.length === 0 && rendered.pictures.length === 0
    && (['en', 'de', 'lt', 'hu'] as const).every((lang) => {
      const soon = rendered.scenarios[0].langs[lang]!.soon;
      return rendered.scenarios[0].langs[lang]!.tiles.every((t) => shows(t.html).chip && !shows(t.html).price && t.html.includes(`>${soon}</span>`))
        && rendered.scenarios[2].langs[lang]!.tiles.every((t) => shows(t.html).chip && !shows(t.html).price)
        && rendered.scenarios[1].langs[lang]!.tiles.filter((t) => shows(t.html).price).map((t) => t.id).join() === 'powder'
        && rendered.scenarios[1].langs[lang]!.tiles.filter((t) => shows(t.html).chip).length === 13;
    }), JSON.stringify([rendered.errors, rendered.pictures]));
  check('rendered: a tile for sale is marked "sale" and shows no Soon chip, a tile that cannot be bought is marked "soon", and the tile heading is the registry\'s name',
    shows(tileHtml(1, 'en', 'powder')).state === 'sale' && !shows(tileHtml(1, 'en', 'powder')).chip && shows(tileHtml(1, 'en', 'duo_kiss')).state === 'soon' && tileHtml(1, 'en', 'duo_kiss').includes('<h3>Kiss Collision</h3>')
    && tileHtml(1, 'de', 'fam_trio').includes('<h3>Family Colours</h3>') && tileHtml(1, 'lt', 'radiance').includes('<h3>Radiance</h3>') && tileHtml(1, 'hu', 'clean').includes('<h3>Clean Iris</h3>'), '');
  check('rendered: the price table prints the art price and names the styles for sale in the state with one style ticked, and not a number in the closed state; the hero line is held back (inert) while nothing can be bought for one eye',
    (() => {
      const row = (si: number) => rendered.scenarios[si].langs.en!.table;
      const hero = (si: number) => rendered.scenarios[si].langs.en!.hero;
      return row(1).includes('Powder Burst.') && /lp-pv"><span>[^<]*\d/.test(row(1)) && !/lp-pv"><span>[^<]*\d/.test(row(0)) && !/\d/.test(row(0).replace(/class="[^"]*"/g, '').replace(/data-[a-z]+="[^"]*"/g, ''))
        && /<li class="lp-price" inert/.test(hero(0)) && !/<li class="lp-price" inert/.test(hero(1)) && /<li class="lp-price" inert/.test(hero(2));
    })(), '');
  // what the gallery printed under each group's intro, read from the markup of the styles chapter the page itself rendered
  const lineOf = (si: number, g: string) => /<span class="lp-gline"([^>]*)>/.exec(rendered.scenarios[si].langs.en!.groups[g])?.[1].replace(/^.*data-line="(\w+)".*$/, '$1') ?? null;
  const linesOf = (si: number) => JSON.stringify({ one: lineOf(si, 'one'), two: lineOf(si, 'two'), family: lineOf(si, 'family') });
  check('rendered: the lines under the groups follow the catalogue (one style ticked: "more" for the one-eye group, "soon" for the pairs and the families; closed: none; the pairs live: "more" for the pairs)',
    linesOf(1) === JSON.stringify({ one: 'more', two: 'soon', family: 'soon' }) && linesOf(0) === JSON.stringify({ one: null, two: null, family: null }) && linesOf(3) === JSON.stringify({ one: 'more', two: 'more', family: 'more' }), `${linesOf(1)} ${linesOf(0)} ${linesOf(3)}`);
  const comboOf = (si: number, g: string) => /<div class="lp-combo"><h3>([^<]*)<\/h3><p>([\s\S]*?)<\/p>/.exec(rendered.scenarios[si].langs.en!.groups[g]);
  const soonTitle = en.styles.comboTitleSoon;
  const fourTitle = en.styles.comboTitle.replace('{max}', '4');
  check('rendered: the several-eyes card of the pairs and the families carries the title without a count and no number while no count from two eyes can be bought (closed, one style, nothing ticked), and the title "to 4 eyes" with the further-eye price once two, three and four eyes can; the one-eye group has no card',
    [0, 1, 2].every((si) => comboOf(si, 'two')?.[1] === soonTitle && !/\d/.test(comboOf(si, 'two')?.[2] ?? '0') && comboOf(si, 'family')?.[1] === soonTitle)
    && comboOf(3, 'two')?.[1] === fourTitle && /\d/.test(comboOf(3, 'two')?.[2] ?? '') && comboOf(3, 'family')?.[1] === fourTitle && comboOf(0, 'one') === null, JSON.stringify([comboOf(0, 'two'), comboOf(3, 'two')]));
  const faqAnswer = (si: number, lang: 'en' | 'de' | 'lt' | 'hu') => /<details id="faq-other"[^>]*><summary[^>]*>[\s\S]*?<\/summary><p>([\s\S]*?)<\/p>/.exec(rendered.scenarios[si].langs[lang]!.faq)?.[1] ?? '';
  check('rendered: the FAQ answer about other people\'s eyes names no count while ordering is closed or one eye is the most that can be bought, and says "up to 4 eyes" once four can (in every language)',
    (['en', 'de', 'lt', 'hu'] as const).every((lang) => [0, 1, 2].every((si) => !/\d/.test(faqAnswer(si, lang))) && /4/.test(faqAnswer(3, lang)) && faqAnswer(3, lang) !== faqAnswer(1, lang)), faqAnswer(3, 'en'));
  check('rendered: the FAQ question about ordering takes its open wording only when ordering is open (open with one style ticked or with the pairs, the plain one closed or with nothing ticked)',
    (() => {
      const item = en.faq.items.find((x) => x.id === 'order')!;
      const q = (si: number) => /<details id="faq-order"[^>]*><summary[^>]*><span>([^<]*)<\/span>/.exec(rendered.scenarios[si].langs.en!.faq)?.[1];
      return !!item.qOpen && item.qOpen !== item.q && q(0) === item.q && q(2) === item.q && q(1) === item.qOpen && q(3) === item.qOpen;
    })(), '');
  check('rendered: the notice bar, the pricing notice (and its payment line) and the third step ("pay through Stripe") take their open wording only while ordering is open: open with one style ticked or with the pairs, the plain wording closed or with nothing ticked',
    (() => {
      const v = (si: number) => rendered.scenarios[si].langs.en!;
      const bar = (si: number) => /<span id="barText">([^<]*)<\/span>/.exec(v(si).top)?.[1];
      const notice = (si: number) => /<p class="lp-notice"[^>]*>([^<]*)<\/p>/.exec(v(si).pricing)?.[1];
      const pay = (si: number) => /<p class="lp-pay-open">([^<]*)<\/p>/.exec(v(si).pricing)?.[1];
      // the third <li class="lp-step"> of the steps (the split's first piece is what comes before the first step)
      const stripe = (si: number) => /Stripe/.test(v(si).how.split('<li class="lp-step"')[3] ?? '');
      const closed = [0, 2], open = [1, 3];
      return closed.every((si) => bar(si) === en.bar.soon && notice(si) === en.pricing.notice && pay(si) === undefined && !stripe(si))
        && open.every((si) => bar(si) === en.bar.open && notice(si) === en.pricing.noticeOpen && pay(si) === en.pricing.payOpen && stripe(si));
    })(), '');
  check('rendered: the hero\'s line is the price of the styles for sale: the black price is not on it while only an art style is for sale, and the line is held back in the closed state and carries no price at all (figure spaces where the number would be)',
    (() => {
      const text = (si: number) => rendered.scenarios[si].langs.en!.hero.replace(/<[^>]*>/g, ' ');
      const held = /<li class="lp-price" inert[^>]*>([\s\S]*?)<\/li>/.exec(rendered.scenarios[0].langs.en!.hero)?.[1] ?? '';
      return text(1).includes(lp.art) && !text(1).includes(lp.black) && held !== '' && !text(0).includes(lp.from) && !/[0-9]/.test(held) && held.includes('Digital file from') && held.includes(HELD_PRICE);
    })(), '');
  const unused: RunCatalogue = severalMax(pairs) >= 2 ? pairs : pairs;
  check('severalMax with the pairs and the Trio and four eyes live is 4 and with the Trio alone 0 (the combo card prints its title with {max} only from two eyes)', severalMax(unused) === 4 && severalMax(trio) === 0, `${severalMax(unused)} ${severalMax(trio)}`);

  // --- the page's asking code (src/landing/ordering.ts createOrdering), run against stand-in answers: what the page can sell is what the SERVER says, only while this deployment takes
  // orders; every way the answers can fail leaves the page closed. The line "sale = saleCatalogue(...)" is the one the whole page's promise rests on, so it is run, not read.
  const ok = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
  const server = (health: unknown, checkout: unknown, checkoutStatus = 200): Ask => async (path) => ok(path === '/api/health' ? health : checkout, path === '/api/health' ? 200 : checkoutStatus);
  const stripeOn = { ok: true, stripe: true, stripe_live: false, email: true };
  const live = answer({ 'solo.powder': { '1': 'live' }, 'solo.clean': { '1': 'live' } }, 1);
  const ask = async (a: Ask, settled = true) => { const o = createOrdering(a, settled); await o.start(); return o; };
  const sellsPowder = (o: { sale: () => RunCatalogue }) => liveFor(o.sale(), 'solo.powder', 1) && liveFor(o.sale(), 'solo.clean', 1) && o.sale().max === 1 && o.sale().one.length === 2;
  const onlyClosed = (o: { open: () => boolean; sale: () => RunCatalogue }) => !o.open() && o.sale() === NOTHING_FOR_SALE;
  const a1 = await ask(server(stripeOn, live));
  check('createOrdering: the deployment takes orders (health: Stripe set up; checkout: open) and two styles are live: the page is open and the sale is the catalogue',
    a1.open() && sellsPowder(a1) && a1.sale().max === 1, JSON.stringify(a1.sale()));
  const a2 = await ask(server(stripeOn, { ...live, open: false }));
  check('createOrdering: checkout says the deployment does not take orders although styles are live: the page is closed and the sale is NOTHING (no price stands beside "Ordering opens soon")', onlyClosed(a2), JSON.stringify(a2.sale()));
  const a3 = await ask(server(stripeOn, answer({ 'solo.powder': { '1': 'preview' } }, 0)));
  check('createOrdering: the deployment takes orders but the owner ticked nothing (orderable_max_eyes 0): the page is closed and sells nothing', onlyClosed(a3), JSON.stringify(a3.sale()));
  const a4 = await ask(server({ ok: true, stripe: false }, live));
  check('createOrdering: health says Stripe is not set up: closed, whatever checkout would say (checkout is not even asked)', onlyClosed(a4), JSON.stringify(a4.sale()));
  const a5 = await ask(server({ ok: true, stripe: true, stripe_live: true, email: false }, live));
  check('createOrdering: a live Stripe key without the delivery email is closed', onlyClosed(a5), JSON.stringify(a5.sale()));
  const a6 = await ask(server(stripeOn, live, 500));
  check('createOrdering: checkout answers 500: closed', onlyClosed(a6), JSON.stringify(a6.sale()));
  const a7 = await ask(async () => { throw new Error('offline'); });
  check('createOrdering: the server cannot be reached (offline, the dev page without the API): closed, the build\'s fallback stands in (nothing for sale)', onlyClosed(a7), JSON.stringify(a7.sale()));
  const a8 = await ask(async (path) => (path === '/api/health' ? new Response('<html>nope</html>', { status: 200 }) : ok(live)));
  check('createOrdering: an answer that is not JSON (a proxy\'s page): closed', onlyClosed(a8), JSON.stringify(a8.sale()));
  const a9 = await ask(server(stripeOn, { ...live, ok: false }));
  check('createOrdering: checkout says ok false: closed', onlyClosed(a9), JSON.stringify(a9.sale()));
  const a10 = await ask(server(stripeOn, { ok: true, open: true, suggest: 'au', styles: [] }));
  check('createOrdering: an answer that holds no catalogue (an older server) but is open: the market it suggests is kept, the sale is the build\'s fallback, which sells nothing', a10.suggested() === 'au' && !a10.open() && a10.sale() === NOTHING_FOR_SALE, JSON.stringify([a10.suggested(), a10.sale()]));
  // what a render without a browser reads: the closed page (the prerender and a hydration see the same first paint everywhere), except for the store the gate makes settled
  const Probe = () => { const o = useOrderingOpen(); const s = useSaleCatalogue(); const m = useSuggestedMarket(); return createElement('i', null, `${o}|${s.max}|${s.one.join(',')}|${m}`); };
  const seen = (o: Awaited<ReturnType<typeof ask>>) => renderToStaticMarkup(createElement(OrderingContext.Provider, { value: o }, createElement(Probe)));
  const unsettled = await ask(server(stripeOn, { ...live, suggest: 'au' }), false);
  const settled = await ask(server(stripeOn, { ...live, suggest: 'au' }), true);
  check('the hooks of the page: a store that is not settled reads the closed page in a render without a browser although it holds answers; the gate\'s settled store reads them (open, the sale, the market it suggests)',
    seen(unsettled) === '<i>false|0||null</i>' && seen(settled) === `<i>true|1|${settled.sale().one.join(',')}|au</i>` && settled.sale().one.length === 2, `${seen(unsettled)} ${seen(settled)}`);
  return out;
}
