// Prints of the artwork as the page code reads them (src/shared/prints.ts, src/try/PrintPick.tsx, src/try/BuyCard.tsx, src/try/checkout.ts,
// src/legal/docs/prints.ts, src/admin/Prints.tsx): the offer and the shipping rule, the server's answer and the markets that offer prints,
// the picker (the choice, the country, the print box, the total, the picture), the checkout request, the legal texts of every edition and the
// admin's words. Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs.
// 2026-11-21: a print is offered AFTER the purchase, on the order page (src/order/PrintOffer.tsx; suites/ts/print_offer.test.ts has that card's
// own tests). The picker left /try's buy card, so the checks that drew it inside the buy card draw it in the order page's card now, with that
// page's words ("Choose a print" where the buy card said "Digital file only", the print's price without the plus sign, the total on its own
// line and not on the button), and the buy card's checks say that it shows no print even while the server offers them.
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  PRINT_NAMES, PRINT_OFFER, PRINT_RATES, PRINT_TIMES, countriesByName, countryName, defaultCountry, kindAbout, kindName, madeText, offeredPrints, printCountries, printLabel, printMargin, printName,
  printProduct, printProducts, printShipping, shipPrice, wayText,
  type ServerPrints,
} from '../../src/shared/prints';
import { BuyCard } from '../../src/try/BuyCard';
import { PrintMock, printPart } from '../../src/try/PrintPick';
import { COPY, setCopyLang } from '../../src/try/copy';
import { ORDER_COPY } from '../../src/order/copy';
import { PrintOffer } from '../../src/order/PrintOffer';
import type { OrderStatus } from '../../src/order/api';
import { runCheckout } from '../../src/try/checkout';
import { CHECKOUT_LEGAL, checkoutLegal, WITHDRAWAL_CONSENT_VERSION } from '../../src/shared/legal';
import { EDITIONS } from '../../src/legal/editions';
import { shippingRows, timesText } from '../../src/legal/docs/prints';
import { OrderPrint, printStateLt } from '../../src/admin/Prints';
import { money } from '../../src/shared/markets';
import type { Block, LegalDoc } from '../../src/legal/types';
import type { Eye } from '../../src/try/multi';

type Row = [string, boolean, string?];
const text = (h: string) => h.replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();
const sp = (x: string) => x.replace(/\s+/g, ' ');
const has = (h: string, id: string) => h.includes(`data-testid="${id}"`);
const DASH = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');
const blockText = (b: Block): string => (typeof b === 'string' ? b : 'ul' in b ? b.ul.join('\n') : 'dl' in b ? b.dl.map((r) => r.join(': ')).join('\n') : b.box.join('\n'));
const sectionText = (d: LegalDoc | undefined, id: string) => (d?.sections.find((s) => s.id === id)?.blocks ?? []).map(blockText).join('\n');
const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
const noop = () => undefined;

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // the tables
  check('the offer as the page reads it: five prints in the owner\'s order, euros, on eu, lt and hr - 1124: the final list of that day, eleven prints offered '
    + '(acrylic, metal, canvas, poster, block) and the keyring in the list but not offered (on 0: it earns less than the floor)'
    + ' - 1125: the keyring is offered at 20 EUR (the owner\'s decision; at that price it earns more than the floor): twelve prints',
    printProducts().map((p) => p.id).join() === 'acrylic30,acrylic40,acrylic60,metal30,metal40,metal60,canvas40,canvas60,poster50,block10,block20,keyring' && PRINT_OFFER.currency === 'eur'
      && PRINT_OFFER.markets.join() === 'eu,lt,hr' && printProducts(false).length === 12 && printProduct('keyring')?.on === 1 && printProduct('keyring')?.price === 2000
      && printCountries().every((cc) => (printMargin('keyring', cc) ?? 0) >= PRINT_OFFER.margin_floor) && PRINT_OFFER.margin_floor === 1500, printProducts().map((p) => p.id).join());
  // 2026-11-24, the owner's decisions: the acrylic block 20 x 20 cm at 79 EUR (a fourth kind, "block": it stands on a shelf, it is not hung) and the canvas at 79 EUR (it was 69)
  check('the acrylic block: a kind of its own with a name in the eight languages (eight different ones), 20 cm, 79 EUR as the canvas now, the shipping of the other small prints, '
    + 'and it earns more than the floor in every country',
    printProduct('block20')?.kind === 'block' && printProduct('block20')?.cm === 20 && printProduct('block20')?.price === 7900 && printProduct('block10')?.price === 3900
      && sp(printName('block20', 'en')) === 'Acrylic block 20 × 20 cm' && sp(printName('block20', 'lt')) === 'Akrilo blokas 20 × 20 cm' && kindName('block', 'de') === 'Acrylblock'
      && new Set(LANGS.map((l) => kindName('block', l))).size === 8 && LANGS.every((l) => kindName('block', l).length > 6 && !DASH.test(kindName('block', l)))
      && printShipping('DE', 'block20') === 499 && printShipping('LT', 'block20') === 849 && printShipping('US', 'block20') === null
      && printCountries().every((cc) => (printMargin('block20', cc) ?? 0) >= PRINT_OFFER.margin_floor) && PRINT_RATES.skus.ABS0200201?.design_mm.join() === '200,200',
    `${printName('block20', 'en')} ${printProduct('block20')?.price} ${printMargin('block20', 'LT')}`);
  check('the shipping rule: VAT and up to the next .49 or .99 (3.99 to 4.99, 5.50 to 6.99, 6.99 to 8.49, 7.99 to 9.99)',
    [399, 550, 699, 799].map((c) => shipPrice(c)).join() === '499,699,849,999');
  check('the shipping per country from the rate table: Germany 4.99 (6.99 for 60 cm), Lithuania 8.49, Sweden 9.99, none to the US',
    printShipping('DE', 'acrylic40') === 499 && printShipping('DE', 'acrylic60') === 699 && printShipping('LT', 'poster50') === 849
      && printShipping('SE', 'canvas40') === 999 && printShipping('US', 'acrylic40') === null && printCountries().length === 27);
  check('every print earns at least the floor in every country (the page\'s margin, the rule the build holds to the server\'s)',
    printProducts().every((p) => printCountries().every((cc) => (printMargin(p.id, cc) ?? 0) >= PRINT_OFFER.margin_floor)));
  check('the names: the product with its size, the countries by their names in the language', printName('acrylic30', 'de') === 'Acrylglasbild 30 × 30 cm'
    && countryName('LT', 'lt') === 'Lietuva' && countryName('HU', 'hu') === 'Magyarország' && countryName(countriesByName('lt')[0], 'lt') === 'Airija', countriesByName('lt').slice(0, 3).join());

  // the server's answer
  const server: ServerPrints = {
    on: true, currency: 'EUR', markets: ['eu', 'lt', 'hr'],
    products: printProducts().map((p) => ({ id: p.id, kind: p.kind, cm: p.cm, price: p.price, ship: Object.fromEntries(printCountries().map((cc) => [cc, printShipping(cc, p.id)])) })),
  };
  // 2026-11-24, the final list: the canvas WITHOUT an outer frame (on its wooden stretcher frame, ready to hang; no floating frame anywhere), 40 and 60 cm; glossy
  // metal 30, 40 and 60 cm; a small block; the keyring, which has no size in its name. Every kind has a line that says what it is (PRINT_NAMES about)
  const KINDS6 = ['acrylic', 'metal', 'canvas', 'poster', 'block', 'keyring'] as const;
  check('the canvas is sold without an outer frame: its name in no language says black, floating or frame alone, its line says ready to hang and without an outer frame; '
    + '40 cm and 60 cm at the owner\'s prices, on the unframed SKUs',
    printProduct('canvas40')?.sku === 'CVS0400401LMF2HC' && printProduct('canvas60')?.sku === 'CVS0600601LMF2HC' && printProduct('canvas40')?.price === 4900
      && printProduct('canvas60')?.price === 6900 && kindName('canvas', 'en') === 'Canvas on a wooden stretcher frame' && kindName('canvas', 'lt') === 'Drobė ant medinio porėmio'
      && !/black|floating|schwarz|Schattenfuge|juodame|fekete|crnom|musta|mustas|meln/i.test(JSON.stringify([PRINT_NAMES.kinds.canvas, PRINT_NAMES.about.canvas]))
      && /ready to hang, without an outer frame/.test(kindAbout('canvas', 'en')) && /paruošta kabinti, be išorinio rėmo/.test(kindAbout('canvas', 'lt'))
      && !Object.keys(PRINT_RATES.skus).some((s) => /BF/.test(s)), JSON.stringify(PRINT_NAMES.kinds.canvas));
  check('every kind has a name and a line that says what it is in the eight languages (48 lines, all different, no dash); the block\'s says 2.5 cm and that it stands '
    + 'by itself, the hung ones say ready to hang, the poster, the block and the keyring say nothing of hanging',
    KINDS6.every((k) => new Set(LANGS.map((l) => kindName(k, l))).size >= 6 && LANGS.every((l) => kindAbout(k, l).length > 12 && !DASH.test(kindAbout(k, l) + kindName(k, l))))
      && new Set(KINDS6.flatMap((k) => LANGS.map((l) => kindAbout(k, l)))).size === 48
      && LANGS.every((l) => /2[.,]5 cm/.test(kindAbout('block', l))) && /stands by itself on a shelf or desk/.test(kindAbout('block', 'en'))
      && ['acrylic', 'metal', 'canvas'].every((k) => /ready to hang/.test(kindAbout(k as 'metal', 'en'))) && ['poster', 'block', 'keyring'].every((k) => !/hang/i.test(kindAbout(k as 'block', 'en')))
      && kindName('metal', 'lt') === 'Blizgus metalas' && kindName('metal', 'en') === 'Glossy metal print' && kindName('keyring', 'lt') === 'Raktų pakabukas',
    KINDS6.map((k) => new Set(LANGS.map((l) => kindName(k, l))).size).join());
  check('a thing that is not named by a size (the keyring, cm 0) is its kind\'s name alone in every language; every other print ends in its size',
    printProduct('keyring')?.cm === 0 && LANGS.every((l) => printName('keyring', l) === kindName('keyring', l) && printLabel('keyring', 0, l) === kindName('keyring', l))
      && printName('keyring', 'en') === 'Keyring' && printProducts().filter((p) => p.kind !== 'keyring').every((p) => p.cm >= 10 && sp(printName(p.id, 'en')).endsWith(`${p.cm} × ${p.cm} cm`))
      && PRINT_RATES.skus.KRR0050041?.design_mm.join() === '56,76', printName('keyring', 'en'));
  // 2026-11-24: how long a print takes, per product and per country, from ONE table (api/_lib/print_times.py: merchOne's published times); the words are in
  // api/_lib/print_names.py times. The sentence "about 3 business days ... 2 to 9 ..." for everything is gone
  const T = PRINT_TIMES;
  check('the table of the times: a production time for every kind (canvas and poster 2 business days, every other 3), a delivery time for the five countries merchOne '
    + 'publishes one for (Lithuania, Latvia and Estonia 4 to 6 working days, Finland 5 to 8, Germany 3 to 6), and a general estimate for the others',
    Object.keys(T.production).sort().join() === [...KINDS6].sort().join() && KINDS6.filter((k) => T.production[k] === 2).join() === 'canvas,poster'
      && KINDS6.every((k) => T.production[k] === 2 || T.production[k] === 3) && Object.keys(T.transit).sort().join() === 'DE,EE,FI,LT,LV'
      && ['LT', 'LV', 'EE'].every((cc) => T.transit[cc].join() === '4,6') && T.transit.FI.join() === '5,8' && T.transit.DE.join() === '3,6'
      && Object.keys(T.transit).every((cc) => printCountries().includes(cc)) && T.transit_other[0] <= T.transit_other[1], JSON.stringify(T));
  check('the words of the times in the eight languages: a print\'s own production time, the delivery to a country with a published time by its numbers, to any other '
    + 'country "about a week" without a number; the country stands in brackets in its own form',
    madeText('canvas', 'lt') === 'Gamyba: apie 2 darbo dienas.' && madeText('acrylic', 'lt') === 'Gamyba: apie 3 darbo dienas.' && madeText('poster', 'en') === 'Production: about 2 business days.'
      && wayText('LT', 'lt') === 'Pristatymas (Lietuva): po to paprastai nuo 4 iki 6 darbo dienų.' && wayText('FI', 'en') === 'Delivery (Finland): then usually 5 to 8 working days.'
      && wayText('DE', 'de') === 'Zustellung (Deutschland): danach meist 3 bis 6 Werktage.' && wayText('SE', 'en') === 'Delivery (Sweden): then usually about a week.'
      && wayText('HR', 'lt') === 'Pristatymas (Kroatija): po to paprastai apie savaitę.'
      && LANGS.every((l) => KINDS6.every((k) => madeText(k, l).includes(String(T.production[k])) && !/[{}]/.test(madeText(k, l)))
        && printCountries().every((cc) => wayText(cc, l).includes(`(${countryName(cc, l)})`) && !/[{}]/.test(wayText(cc, l)) && !DASH.test(wayText(cc, l))
          && /\d/.test(wayText(cc, l)) === (cc in T.transit)))
      && new Set(LANGS.map((l) => madeText('block', l))).size === 8 && new Set(LANGS.map((l) => wayText('SE', l))).size === 8, wayText('LT', 'lt'));
  check('the terms\' delivery paragraph says the table\'s times in every language (2 business days for a canvas or a poster, 3 for every other print; 4 to 6 working '
    + 'days to Lithuania, Latvia and Estonia, 5 to 8 to Finland, 3 to 6 to Germany; the other countries about a week), no token left, and no "2 to 9" or example of old',
    /about 2 business days for a canvas or a poster and about 3 business days for every other print\. Delivery then usually takes 4 to 6 working days to Lithuania, Latvia and Estonia, 5 to 8 to Finland and 3 to 6 to Germany; to the other countries of the European Union the parcel is usually on its way for about a week\./.test(timesText('en'))
      && /Drobės ir plakato gamyba trunka apie 2 darbo dienas, kiekvieno kito spaudinio apie 3 darbo dienas\. Po to pristatymas į Lietuvą, Latviją ir Estiją paprastai trunka nuo 4 iki 6 darbo dienų, į Suomiją nuo 5 iki 8, į Vokietiją nuo 3 iki 6;/.test(timesText('lt'))
      && LANGS.every((l) => !/[{}]/.test(timesText(l)) && (timesText(l).match(/\d+/g) ?? []).join() === '2,3,4,6,5,8,3,6' && !DASH.test(timesText(l))
        && sectionText(EDITIONS.eu.terms[l], 'prints').includes(timesText(l)) && !/2 (to|bis|iki|és|do|kuni|līdz) 9|2-9/.test(sectionText(EDITIONS.eu.terms[l], 'prints')))
      && new Set(LANGS.map((l) => timesText(l))).size === 8 && sectionText(EDITIONS.hu.terms.hu, 'prints').includes(timesText('hu'))
      && sectionText(EDITIONS.eu.terms.en, 'prints').includes('within 30 days of the contract'), timesText('en'));
  check('offeredPrints: none without the server\'s prints, while they are off, or in a market that sells none (au, hu, us); all five on the euro markets - 1124: all eleven - 1125: all twelve, the keyring too',
    offeredPrints(undefined, 'eu').length === 0 && offeredPrints({ on: false }, 'eu').length === 0 && offeredPrints(server, 'au').length === 0
      && offeredPrints(server, 'hu').length === 0 && offeredPrints(server, 'us').length === 0 && offeredPrints(server, 'lt').length === 12);
  check('offeredPrints keeps only what the page knows and what is well formed (an unknown product, a price of 0, no country are left out)',
    offeredPrints({ ...server, products: [...server.products!, { id: 'mug', kind: 'poster', cm: 10, price: 900, ship: { LT: 100 } }, { id: 'poster50', kind: 'poster', cm: 50, price: 0, ship: { LT: 1 } }] }, 'eu').length === 12);
  const offered = offeredPrints(server, 'eu');
  check('the visitor\'s country is preselected only where prints ship to it', defaultCountry('lt', offered[0].ship) === 'LT' && defaultCountry('US', offered[0].ship) === ''
    && defaultCountry(undefined, offered[0].ship) === '');
  check('printPart: the price and the shipping of a complete choice, null for the file alone or without a country',
    JSON.stringify(printPart({ product: 'acrylic40', country: 'DE' }, offered)) === '{"price":7900,"ship":499}' && printPart({ product: 'acrylic40', country: '' }, offered) === null
      && printPart({ product: null, country: 'DE' }, offered) === null);

  // the buy card
  setCopyLang('en');
  const eyeObj = (id: string): Eye => ({ id, before: 'data:,b', image: 'D', thumb: 'data:,t', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false, colourOff: false }) as Eye;
  const prices = { one_eye_studio_black: 1997, one_eye_art: 2497, two_eyes: 3997, each_further_eye: 1500 };
  const buy = (o: Record<string, unknown> = {}) => renderToStaticMarkup(createElement(BuyCard, {
    eyes: [eyeObj('e1')], style: 'solo.powder', styleName: 'Powder Burst', ordering: { open: true, prices, maxEyes: 8, consent: { print: { en: 'SERVER BOX TEXT' } } },
    preview: 'ready', stale: [], onRetake: noop, waiver: true, onWaiver: noop, busy: false, step: null, error: null, onBuy: noop,
    state: { kind: 'normal' }, loading: false, advisory: [], wordsBlocked: false, ...o,
  } as never));
  // the picker's card, where it lives since 2026-11-21: the order page's offer under a delivered artwork (the status reply's print_offer)
  const st = (o: Partial<OrderStatus> = {}): OrderStatus => ({
    order: '261121-0123456789abcdef', state: 'ready', eyes: [{ eye: 1, made: true }], count: 1, market: 'eu',
    download: { url: 'data:,art', download_url: 'data:,art' }, print_offer: { currency: 'EUR', products: server.products, consent: { en: 'SERVER BOX TEXT' } }, ...o,
  });
  const offerCard = (o: Record<string, unknown> = {}, lang: (typeof LANGS)[number] = 'en') => renderToStaticMarkup(createElement(PrintOffer, {
    C: ORDER_COPY[lang], lang, link: { o: '261121-0123456789abcdef', k: 'a'.repeat(32), s: null }, st: st(), market: 'eu', back: null, email: true, onReload: noop, onRecheck: noop, ...o,
  } as never));
  const OW = ORDER_COPY.en.offer;
  const h0 = buy();
  check('without prints (the switch off): the card is the card of before, no print choice, the button the artwork\'s price',
    !has(h0, 'print-pick') && text(h0).includes(sp(`Continue to payment · ${money(2497, 'eur', 'en')}`)) && !/data-testid="buy"[^>]*disabled/.test(h0), text(h0).slice(0, 300));
  const h1b = buy({ ordering: { open: true, prices, maxEyes: 8, prints: server, consent: { print: { en: 'SERVER BOX TEXT' } } } });
  const h1 = offerCard();
  check('with prints: the buy card still shows none (a print is offered after the purchase), its button the artwork\'s price and open; the order page\'s card has one '
    + 'choice, "Choose a print" first, every print with its price, nothing chosen',
    !has(h1b, 'print-pick') && text(h1b).includes(sp(`Continue to payment · ${money(2497, 'eur', 'en')}`)) && !/data-testid="buy"[^>]*disabled/.test(h1b)
      && has(h1, 'print-pick') && text(h1).includes(OW.choose) && text(h1).includes(sp(`${printName('acrylic40', 'en')}, ${money(7900, 'eur', 'en')}`))
      && !has(h1, 'print-country') && !has(h1, 'print-consent') && /data-testid="print-buy"[^>]*disabled/.test(h1), text(h1).slice(0, 500));
  const h2 = offerCard({ initial: { choice: { product: 'acrylic40', country: '' } } });
  check('a print chosen without its country: the country list (by name), the picture of the print, the button shut with the hint to choose the country',
    has(h2, 'print-country') && has(h2, 'print-mock') && /data-kind="acrylic"/.test(h2) && /data-testid="print-buy"[^>]*disabled/.test(h2) && text(h2).includes(OW.countryMissing)
      && h2.indexOf('Austria') < h2.indexOf('Germany') && !has(h2, 'print-shipping'), text(h2).slice(0, 400));
  const h3 = offerCard({ initial: { choice: { product: 'acrylic40', country: 'DE' }, consent: false } });
  check('with its country: the shipping line, the print box (the server\'s text, never ticked), the button shut until it is ticked',
    has(h3, 'print-shipping') && text(h3).includes(sp(`Shipping ${money(499, 'eur', 'en')}`)) && text(h3).includes('SERVER BOX TEXT') && !/data-testid="print-consent"[^>]*checked/.test(h3)
      && /data-testid="print-buy"[^>]*disabled/.test(h3) && text(h3).includes(OW.consentMissing) && h3.includes('src="data:,art"'), text(h3).slice(0, 600));
  const h4 = offerCard({ initial: { choice: { product: 'acrylic40', country: 'DE' }, consent: true } });
  check('ticked: the button is open and the card shows the total (the print and its shipping; the artwork was paid before)', !/data-testid="print-buy"[^>]*disabled/.test(h4)
    && text(h4).includes(sp(`${OW.total} ${money(7900 + 499, 'eur', 'en')}`)) && text(h4).includes('Continue to payment'), text(h4).slice(0, 600));
  const h5 = offerCard({ st: st({ print_offer: { currency: 'EUR', products: server.products } }), initial: { choice: { product: 'acrylic40', country: 'DE' }, consent: true } });
  check('without the server\'s box text the page shows its own (the same words, held by the build)', text(h5).includes(sp(CHECKOUT_LEGAL.en.printConsent)));
  check('the picture of each kind: a frame for the canvas, a gloss for the acrylic, plain paper for the poster - 1124: six pictures, all different: the canvas '
    + 'WITHOUT a frame (no black border round it), a bright rim for the metal, a thick clear edge for the block, and the keyring as a small upright tag with its ring, not a square',
    KINDS6.every((k) => renderToStaticMarkup(createElement(PrintMock, { kind: k as never, alt: 'x' })).includes(`data-kind="${k}"`))
      && new Set(KINDS6.map((k) => renderToStaticMarkup(createElement(PrintMock, { kind: k as never, alt: 'x' })).replace(/data-kind="[a-z]+"/, ''))).size === 6
      && !/p-\[5px\] bg-\[#111\]|bg-black p-|p-\[3px\] bg-black/.test(renderToStaticMarkup(createElement(PrintMock, { kind: 'canvas' as never, alt: 'x' })))
      && /w-\[70px\] h-24/.test(renderToStaticMarkup(createElement(PrintMock, { kind: 'keyring' as never, alt: 'x' })))
      && !/w-\[70px\]/.test(renderToStaticMarkup(createElement(PrintMock, { kind: 'block' as never, alt: 'x' }))));
  // (the print box's text comes from the page's own copy here: the status reply of this card names no text for these languages)
  const noBox = st({ print_offer: { currency: 'EUR', products: server.products } });
  const hl = offerCard({ st: noBox, initial: { choice: { product: 'poster50', country: 'LT' }, consent: false } }, 'lt');
  check('Lithuanian: the words of the choice and the Lithuanian box', text(hl).includes('Pasirinkite spaudinį') && text(hl).includes(sp(printName('poster50', 'lt')))
    && sp(printName('poster50', 'lt')) === 'Plakatas 50 × 50 cm' && text(hl).includes('Lietuva') && text(hl).includes(sp(CHECKOUT_LEGAL.lt.printConsent)), text(hl).slice(0, 400));
  // 2026-11-13: Finnish, Estonian and Latvian, the same way (the words of src/order/copy.fi.ts, copy.et.ts and copy.lv.ts offer.choose, the names of api/_lib/print_names.py)
  const NEW_WORDS = { fi: ['Valitse tuloste', 'Juliste', 'FI', 'Suomi'], et: ['Vali trükitud pilt', 'Plakat', 'EE', 'Eesti'], lv: ['Izvēlieties izdruku', 'Plakāts', 'LV', 'Latvija'] } as const;
  for (const l of ['fi', 'et', 'lv'] as const) {
    const [none, poster, cc, country] = NEW_WORDS[l];
    const hx = offerCard({ st: noBox, initial: { choice: { product: 'poster50', country: cc }, consent: false } }, l);
    check(`${l}: the words of the choice and the box of that language (its own text, not the English or the Lithuanian one)`, text(hx).includes(none) && text(hx).includes(`${poster} 50 × 50 cm`)
      && sp(printName('poster50', l)) === `${poster} 50 × 50 cm` && countryName(cc, l) === country && text(hx).includes(country) && text(hx).includes(sp(CHECKOUT_LEGAL[l].printConsent))
      && CHECKOUT_LEGAL[l].printConsent !== CHECKOUT_LEGAL.en.printConsent && CHECKOUT_LEGAL[l].printConsent !== CHECKOUT_LEGAL.lt.printConsent && !text(hx).includes('Choose a print'), text(hx).slice(0, 400));
  }
  setCopyLang('en');
  check('every language has the print words, the two errors and no dash', LANGS.every((l) => {
    const c = COPY[l];
    const o = ORDER_COPY[l].offer;
    return !!o.product && !!o.choose && !!c.buy.errors.print_unavailable && !!c.buy.errors.print_changed && !DASH.test(JSON.stringify(o))
      && !!ORDER_COPY[l].print.shipped && !DASH.test(JSON.stringify(ORDER_COPY[l].print));
  }));

  // the checkout request
  const bodies: Record<string, unknown>[] = [];
  const api = async (path: string, init?: { body?: Record<string, unknown> }) => {
    const b = init?.body ?? {};
    bodies.push({ path, ...b });
    if (path === '/api/order') return { ok: true, status: 200, data: { order: '261028-0123456789abcdef', k: 'a'.repeat(32), eye: 1, created: true, expires_at: Math.floor(Date.now() / 1000) + 86400 }, reason: '', error: '' };
    return { ok: true, status: 200, data: { url: 'https://checkout.stripe.test/c', expires_at: Math.floor(Date.now() / 1000) + 3600 }, reason: '', error: '' };
  };
  const eye1 = { ...eyeObj('e1'), sealed: 'S', draft: { crop: 'C', ticket: 'T', until: Date.now() + 600_000 } } as Eye;
  const base = { eyes: [eye1], style: 'solo.powder', layout: 'single' as never, names: '', lang: 'en' as never, ref: null, market: 'eu', shown: 2497 };
  await runCheckout({ ...base, print: { product: 'acrylic40', country: 'DE' }, printShown: 8399 }, noop, api as never);
  const cb = bodies.find((b) => b.path === '/api/checkout') ?? {};
  check('the checkout request carries the print, its box and the price shown for it (the server only compares it)',
    JSON.stringify(cb.print) === '{"product":"acrylic40","country":"DE"}' && cb.consent_print === true && cb.print_shown === 8399 && cb.consent_digital === true, JSON.stringify(cb));
  bodies.length = 0;
  await runCheckout(base, noop, api as never);
  const cb2 = bodies.find((b) => b.path === '/api/checkout') ?? {};
  check('a checkout of the file alone sends no print key at all (the request of before prints existed)', !('print' in cb2) && !('consent_print' in cb2) && !('print_shown' in cb2), JSON.stringify(cb2));

  // the legal texts
  const eu = EDITIONS.eu;
  check('the EU edition: the terms, the privacy policy and the withdrawal page have a section "prints" in all eight languages (five until 2026-11-13: Finnish, Estonian and Latvian)',
    LANGS.length === 8 && LANGS.every((l) => !!eu.terms[l]?.sections.some((s) => s.id === 'prints') && !!eu.privacy[l]?.sections.some((s) => s.id === 'prints')
      && !!eu.withdrawal[l]?.sections.some((s) => s.id === 'prints')));
  const tp = sectionText(eu.terms.en, 'prints');
  check('the terms\' section: every print with its price, the shipping table, every country by name, the manufacturer, 16(c), the 7 days, the two years, 30 days',
    printProducts().every((p) => tp.includes(money(p.price, 'eur', 'en')) && tp.includes(printName(p.id, 'en'))) && printCountries().every((cc) => tp.includes(countryName(cc, 'en')))
      && tp.includes('Picanova GmbH (merchOne), Eupener Straße 67, 50933 Köln') && tp.includes('Article 16(c)') && tp.includes('7 days') && tp.includes('two years')
      && tp.includes('30 days') && !DASH.test(tp), tp.slice(0, 300));
  const rows = shippingRows('en');
  check('the shipping table groups the countries by price, and Germany says its 60 cm price apart - 1124: the prints on a tariff of their own (metal and canvas of '
    + '60 cm) have rows of their own after the usual four, named by those prints, so no country\'s entry repeats them; every country is in both parts once'
    + ' - 1125: and the keyring, which ships on a tariff of its own too (4.99 to Germany, 5.99 to Austria and France ...), has five rows after them: twelve rows',
    rows.map((r) => r[0]).join() === [499, 699, 849, 999, 699, 849, 1349, 499, 599, 699, 849, 999].map((c) => money(c, 'eur', 'en')).join()
      && rows[0][1].startsWith('Germany (') && rows[0][1].includes(money(699, 'eur', 'en')) && sp(rows[0][1]).includes(sp(printName('acrylic60', 'en')))
      && rows.slice(0, 4).every((r) => !r[1].includes(kindName('metal', 'en')) && !r[1].includes(kindName('canvas', 'en')))
      && rows.slice(4, 7).every((r) => sp(r[1]).startsWith(sp(`${printName('metal60', 'en')}, ${printName('canvas60', 'en')}: `)))
      && rows.slice(7).every((r) => r[1].startsWith('Keyring: ')) && rows[7][1] === 'Keyring: Germany' && rows[8][1] === 'Keyring: Austria, France'
      && printCountries().every((cc) => rows.slice(7).filter((r) => r[1].split(': ')[1].split(', ').includes(countryName(cc, 'en'))).length === 1)
      && rows[4][1].endsWith(': Germany') && rows[6][1].includes('Lithuania') && rows[6][1].includes('Sweden')
      && printCountries().every((cc) => rows.slice(0, 4).filter((r) => r[1].includes(countryName(cc, 'en'))).length === 1
        && rows.slice(4, 7).filter((r) => r[1].split(': ')[1].split(', ').includes(countryName(cc, 'en'))).length === 1)
      && LANGS.every((l) => shippingRows(l).length === 12), JSON.stringify(rows).slice(0, 300));
  check('the Hungarian edition\'s terms (forints) carry the section and say a print is added only to an order in euros; AU and US carry none',
    !!EDITIONS.hu.terms.hu?.sections.some((s) => s.id === 'prints') && sectionText(EDITIONS.hu.terms.en, 'prices').includes('only to an order in euros')
      && !EDITIONS.au.terms.en?.sections.some((s) => s.id === 'prints') && !EDITIONS.us.terms.en?.sections.some((s) => s.id === 'prints')
      && sectionText(EDITIONS.us.terms.en, 'product').includes('We do not sell prints'));
  check('the privacy policy names the partner in the list of services and says which data it receives (name and address, not the e-mail)',
    LANGS.every((l) => sectionText(eu.privacy[l], 'services').includes('Picanova GmbH (merchOne)') && sectionText(eu.privacy[l], 'prints').includes('Picanova'))
      && sectionText(eu.privacy.en, 'prints').includes('name and delivery address') && sectionText(eu.privacy.en, 'prints').includes('do not give it your email address'));
  check('the print box: the page\'s text in every language, version 2026-11-13.1 (the Finnish, Estonian and Latvian waivers and print boxes added, every other text as it was; 2026-10-28.3 before), eight different texts, the same for the hu edition\'s checkout',
    WITHDRAWAL_CONSENT_VERSION === '2026-11-13.1' && new Set(LANGS.map((l) => CHECKOUT_LEGAL[l].printConsent)).size === 8 && LANGS.every((l) => CHECKOUT_LEGAL[l].printConsent.length > 60 && !DASH.test(CHECKOUT_LEGAL[l].printConsent))
      && checkoutLegal('hu', 'hu').printConsent === CHECKOUT_LEGAL.hu.printConsent);

  // the admin
  const ap = renderToStaticMarkup(createElement(OrderPrint, { call: (async () => ({ ok: true })) as never, order: '261028-0123456789abcdef', onDone: noop,
    p: { product: 'acrylic40', name: 'Paveikslas po akriliniu stiklu 40 × 40 cm', country: 'DE', city: 'Berlin', price: 7900, ship: 499, margin: 4390, state: 'failed', attempts: 2, error: 'refused 422: invalid' } }));
  check('the admin\'s print block: the state in Lithuanian, the error, the Retry button', text(ap).includes(printStateLt('failed')) && text(ap).includes('refused 422') && text(ap).includes('Siųsti į merchOne'), text(ap));
  check('the rate table is the one the build checked (fetched date, 27 countries)', /^\d{4}-\d\d-\d\d$/.test(PRINT_RATES.fetched) && Object.keys(PRINT_RATES.shipping).length === 27);
  return out;
}
