// The print offered AFTER the purchase, as the order page does it (src/order/PrintOffer.tsx, src/order/printAddon.ts, src/order/OrderApp.tsx; the
// server's side is api/_lib/prints.py, suite v3prints section 10): the offer the status reply carries, the card in its states (nothing chosen, a
// print without its country, with its country and the box unticked, ticked with the total and the open button, an error), the request that opens
// Stripe's page, the watch after the way back from it (until the print is on record), the notes of that way back, the print line of a delivered
// order, the words in the eight languages, and /try without the picker.
// Pure page code, loaded through Vite's module runner by scripts/run_ts_tests.mjs; returns its results, prints nothing.
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { PrintOffer } from '../../src/order/PrintOffer';
import {
  PRINT_BUSY, WATCH_TRIES, buyPrint, marketCountry, offerPrints, printCheckPath, watchPrint, type PrintBack, type PrintOfferReply,
} from '../../src/order/printAddon';
import { ORDER_COPY } from '../../src/order/copy';
import type { OrderPrint, OrderStatus } from '../../src/order/api';
import { BuyCard } from '../../src/try/BuyCard';
import { COPY, setCopyLang } from '../../src/try/copy';
import { CHECKOUT_LEGAL } from '../../src/shared/legal';
import { countryName, kindAbout, kindName, madeText, printCountries, printName, printProducts, printShipping, wayText } from '../../src/shared/prints';
import { money } from '../../src/shared/markets';
import type { Eye } from '../../src/try/multi';

type Row = [string, boolean, string?];
const text = (h: string) => h.replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();
const sp = (x: string) => x.replace(/\s+/g, ' ');
const has = (h: string, id: string) => h.includes(`data-testid="${id}"`);
const DASH = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');
const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
const noop = () => undefined;
const read = (p: string) => readFileSync(p, 'utf8');

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // the offer of the status reply (what api/_lib/prints.py addon_offer sends)
  const offer: PrintOfferReply = {
    currency: 'EUR',
    products: printProducts().map((p) => ({ id: p.id, kind: p.kind, cm: p.cm, price: p.price, ship: Object.fromEntries(printCountries().map((cc) => [cc, printShipping(cc, p.id)])) })),
    consent: { en: 'SERVER BOX TEXT', lt: 'SERVERIO LANGELIO TEKSTAS' },
  };
  const download = { url: 'https://files.test/a.jpg', download_url: 'https://files.test/a.jpg?download=1', display_url: 'https://files.test/display.jpg' };
  const ready = (over: Partial<OrderStatus> = {}): OrderStatus => ({
    order: '261121-0123456789abcdef', state: 'ready', eyes: [{ eye: 1, made: true }], count: 1, style: 'solo.powder', market: 'eu', currency: 'EUR', amount: 2497,
    download, print_offer: offer, ...over,
  });
  const link = { o: '261121-0123456789abcdef', k: 'a'.repeat(32), s: null };

  check('offerPrints: the five prints of the reply with the server\'s prices and shipping; none without an offer, and what the page does not know or is not well formed is left out'
    + ' - 1124: the eleven prints of the final list',
    offerPrints(ready()).length === 11 && offerPrints(ready()).map((p) => p.id).join() === 'acrylic30,acrylic40,acrylic60,metal30,metal40,metal60,canvas40,canvas60,poster50,block10,block20' && offerPrints(ready())[1].ship.DE === 499
      && offerPrints(ready({ print_offer: undefined })).length === 0 && offerPrints(null).length === 0
      && offerPrints(ready({ print_offer: { products: [...offer.products!, { id: 'mug', kind: 'poster', cm: 10, price: 900, ship: { LT: 100 } }, { id: 'poster50', kind: 'poster', cm: 50, price: 0, ship: { LT: 1 } }] } })).length === 11);
  check('the country to preselect is the order\'s own market\'s (lt, hr); the common euro market names none', marketCountry('lt') === 'LT' && marketCountry('hr') === 'HR'
    && marketCountry('eu') === null && marketCountry(undefined) === null);

  // the card
  const card = (o: Record<string, unknown> = {}, lang: (typeof LANGS)[number] = 'en') => renderToStaticMarkup(createElement(PrintOffer, {
    C: ORDER_COPY[lang], lang, link, st: ready(), market: 'eu', back: null, email: true, onReload: noop, onRecheck: noop, ...o,
  } as never));
  const W = ORDER_COPY.en.offer;
  const h0 = card();
  check('a delivered order with an offer: the card with its heading and lead, one list with "Choose a print" first and every print with its price, nothing chosen, '
    + 'no country, no box, no total, the button shut, and no hint that presses',
    has(h0, 'print-offer') && text(h0).includes(W.title) && text(h0).includes(W.lead) && text(h0).includes(W.choose)
      && text(h0).includes(sp(`${printName('acrylic40', 'en')}, ${money(7900, 'eur', 'en')}`)) && !has(h0, 'print-country') && !has(h0, 'print-consent') && !has(h0, 'print-total')
      && /data-testid="print-buy"[^>]*disabled/.test(h0) && !has(h0, 'print-hint') && !has(h0, 'print-back') && text(h0).includes(CHECKOUT_LEGAL.en.continueButton), text(h0).slice(0, 400));
  check('the card carries the terms line of the checkout (the print is an order of its own) and says the price is final and where the address is entered',
    text(h0).includes('By ordering you accept our') && h0.includes('/terms') && text(h0).includes(W.footnote), text(h0).slice(-400));
  const h1 = card({ initial: { choice: { product: 'acrylic40', country: '' } } });
  check('a print chosen without its country: the country list by name, the picture of the artwork as that print (the display copy), the button shut with the hint to choose the country',
    has(h1, 'print-country') && has(h1, 'print-mock') && /data-kind="acrylic"/.test(h1) && h1.includes('src="https://files.test/display.jpg"') && /data-testid="print-buy"[^>]*disabled/.test(h1)
      && text(h1).includes(W.countryMissing) && h1.indexOf('Austria') < h1.indexOf('Germany') && !has(h1, 'print-shipping') && !has(h1, 'print-total'), text(h1).slice(0, 500));
  const h2 = card({ initial: { choice: { product: 'acrylic40', country: 'DE' } } });
  check('with its country: the shipping line, the total (the print and its shipping), the print box with the server\'s text, never ticked, the button shut until it is',
    has(h2, 'print-shipping') && text(h2).includes(sp(`${W.shipping} ${money(499, 'eur', 'en')}`)) && text(h2).includes(sp(`${W.total} ${money(8399, 'eur', 'en')}`))
      && text(h2).includes('SERVER BOX TEXT') && !/data-testid="print-consent"[^>]*checked/.test(h2) && /data-testid="print-buy"[^>]*disabled/.test(h2)
      && text(h2).includes(W.consentMissing), text(h2).slice(0, 700));
  const h3 = card({ initial: { choice: { product: 'acrylic40', country: 'DE' }, consent: true } });
  check('ticked: the button is open, no hint', !/data-testid="print-buy"[^>]*disabled/.test(h3) && !has(h3, 'print-hint') && /data-testid="print-consent"[^>]*checked/.test(h3));
  const h4 = card({ st: ready({ print_offer: { ...offer, consent: undefined } }), initial: { choice: { product: 'poster50', country: 'LT' } } });
  check('without the server\'s box text the page shows its own (the same words, held by the build)', text(h4).includes(sp(CHECKOUT_LEGAL.en.printConsent)));
  const h5 = card({ initial: { choice: { product: 'poster50', country: 'LT' }, consent: true, error: 'changed' } });
  const h6 = card({ initial: { error: 'unavailable' } });
  const h7 = card({ initial: { error: 'network' } });
  check('an answer that was not the payment page is said calmly on the card: the price changed, prints cannot be ordered now, no connection (the order page\'s own words)',
    has(h5, 'print-error') && text(h5).includes(W.changed) && text(h6).includes(W.unavailable) && text(h7).includes(ORDER_COPY.en.errors.network));
  check('no offer in the reply, or an order that has its print: no card at all (the page is the page it was)',
    card({ st: ready({ print_offer: undefined }) }) === '' && card({ st: ready({ print: { product: 'poster50', state: 'preparing' } as OrderPrint }) }) === '');

  // the way back from Stripe
  const notes: Record<Exclude<PrintBack, null>, string> = {
    checking: W.checking, slow: W.slow, processing: W.processing, expired: W.expired, extra: W.extra, done: W.done, cancelled: W.cancelled,
  };
  check('the notes of the way back: each state its own calm sentence; while a payment is being confirmed or is on record (checking, slow, processing, done, extra) the '
    + 'offer card stays away; after a cancelled or expired page the card is there again under the note',
    (Object.keys(notes) as Exclude<PrintBack, null>[]).every((b) => {
      const h = card({ back: b });
      return has(h, 'print-back') && h.includes(`data-state="${b}"`) && text(h).includes(notes[b]) && has(h, 'print-offer') === !PRINT_BUSY.includes(b);
    }) && PRINT_BUSY.join() === 'checking,slow,processing,done,extra');
  check('done says the confirmation comes by e-mail only where e-mail is sent; slow offers "Check again"',
    text(card({ back: 'done' })).includes(W.doneEmail) && !text(card({ back: 'done', email: false })).includes(W.doneEmail) && has(card({ back: 'slow' }), 'print-recheck')
      && text(card({ back: 'slow' })).includes(ORDER_COPY.en.unpaid.check) && !has(card({ back: 'checking' }), 'print-recheck'));
  check('a note without an offer (the print is on record: the status has the print, not the offer) is the note alone',
    has(card({ back: 'done', st: ready({ print_offer: undefined, print: { product: 'poster50', state: 'preparing' } as OrderPrint }) }), 'print-back')
      && !has(card({ back: 'done', st: ready({ print_offer: undefined }) }), 'print-offer'));

  // the request
  const bodies: Record<string, unknown>[] = [];
  const reply = (status: number, data: Record<string, unknown> | null, reason = '') =>
    ({ ok: status >= 200 && status < 300 && reason === '', status, data, reason, error: '', retry: false, retryAfter: 0 });
  const apiWith = (answer: ReturnType<typeof reply>) => (async (path: string, init?: { body?: Record<string, unknown> }) => {
    bodies.push({ path, ...(init?.body ?? {}) });
    return answer;
  }) as never;
  const o1 = await buyPrint(link, { product: 'acrylic40', country: 'DE' }, 'lt', 8399, apiWith(reply(200, { url: 'https://checkout.stripe.test/p' })));
  const b = bodies[0] ?? {};
  check('the button\'s request: POST /api/checkout {addon: {order, key}, print, consent_print, print_shown, lang}, and the answer\'s URL is where the page goes',
    b.path === '/api/checkout' && JSON.stringify(b.addon) === JSON.stringify({ order: link.o, key: link.k }) && JSON.stringify(b.print) === '{"product":"acrylic40","country":"DE"}'
      && b.consent_print === true && b.print_shown === 8399 && b.lang === 'lt' && !('consent_digital' in b) && !('eyes' in b)
      && o1.kind === 'redirect' && o1.url === 'https://checkout.stripe.test/p', JSON.stringify(b));
  const codes = await Promise.all([
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(409, { why: 'has_print' }, 'print_not_offered'))),
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(409, { why: 'refunded' }, 'print_not_offered'))),
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(409, { why: 'off' }, 'print_unavailable'))),
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(409, {}, 'print_price_changed'))),
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(0, null))),
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(503, {}, 'payments_busy'))),
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(403, {}, 'bad_link'))),
    buyPrint(link, { product: 'x', country: 'DE' }, 'en', 1, apiWith(reply(200, { url: 'http://not-https.test' }))),
  ]);
  check('the refusals as the card reads them: has (the order has a print), unavailable (the order or the offer), changed, network, busy, failed; a URL that is not https is never followed',
    codes.map((c) => (c.kind === 'error' ? c.code : 'redirect')).join() === 'has,unavailable,unavailable,changed,network,busy,failed,failed', JSON.stringify(codes));

  // the watch
  const watch = async (answers: (n: number) => ReturnType<typeof reply>, tries = WATCH_TRIES) => {
    const emitted: [PrintBack, OrderPrint | undefined][] = [];
    const sleeps: number[] = [];
    const paths: string[] = [];
    let n = 0;
    const api = (async (path: string) => { paths.push(path); n++; return answers(n); }) as never;
    await watchPrint(link, 'cs_test_abcdefgh12345678', { api, sleep: async (ms) => { sleeps.push(ms); } }, (bk, p) => emitted.push([bk, p]), () => true, tries);
    return { emitted, sleeps, paths, n };
  };
  const printBlock = { product: 'acrylic40', kind: 'acrylic', cm: 40, country: 'DE', state: 'preparing', tracking_url: null };
  let w = await watch((n) => (n < 3 ? reply(200, { state: 'pending' }) : reply(200, { state: 'paid', print: printBlock })));
  check('the watch asks GET /api/checkout?addon=<session>&o=&k= every 3 s until the print is on record, then says done with the print block and asks no more',
    w.n === 3 && w.paths[0] === printCheckPath(link.o, link.k, 'cs_test_abcdefgh12345678') && w.paths[0].startsWith('/api/checkout?addon=cs_test_abcdefgh12345678&o=261121-')
      && w.sleeps.join() === '3000,3000' && w.emitted.length === 1 && w.emitted[0][0] === 'done' && w.emitted[0][1]?.product === 'acrylic40', JSON.stringify(w));
  w = await watch(() => reply(200, { state: 'pending' }));
  check('a payment that is not confirmed within the tries: slow, once, after twenty questions (about a minute)', w.n === WATCH_TRIES && w.emitted.length === 1 && w.emitted[0][0] === 'slow');
  w = await watch((n) => (n === 1 ? reply(0, null) : n === 2 ? reply(503, { reason: 'payments_busy' }, 'payments_busy') : reply(200, { state: 'extra', print: printBlock })));
  check('a dropped connection or a busy answer is simply asked again; a second payment of an order that had its print says extra', w.n === 3 && w.emitted.map((e) => e[0]).join() === 'extra');
  w = await watch(() => reply(200, { state: 'expired' }));
  const w2 = await watch(() => reply(200, { state: 'unknown' }));
  const w3 = await watch(() => reply(403, { reason: 'bad_link' }, 'bad_link'));
  check('an expired page says so at once; a session that is not this order\'s print (unknown, or a link that does not fit) ends the watch with nothing to say',
    w.n === 1 && w.emitted[0][0] === 'expired' && w2.n === 1 && w2.emitted[0][0] === null && w3.n === 1 && w3.emitted[0][0] === null);
  w = await watch(() => reply(200, { state: 'processing' }), 4);
  check('a method that settles later: processing is said once, asked about less often (15 s), and the watch never turns it into slow',
    w.emitted.map((e) => e[0]).join() === 'processing' && w.sleeps.every((s) => s === 15000) && w.n === 4, JSON.stringify(w.emitted));
  let live = true;
  const stopped: PrintBack[] = [];
  await watchPrint(link, 'cs_test_abcdefgh12345678', { api: (async () => { live = false; return reply(200, { state: 'paid', print: printBlock }); }) as never, sleep: async () => {} },
    (bk) => stopped.push(bk), () => live);
  check('a page that has gone hears nothing more', stopped.length === 0);

  // the order page itself
  const app = read('src/order/OrderApp.tsx');
  check('the order page: the card stands in the ready state between the artwork and the summary, the way back reads ps (a Stripe session id) and print=cancelled, never in the '
    + 'withdrawal mode, and a recorded print is put into the status the page shows',
    /<Ready [^>]*\/>\s*\{\/\*[^]*?\*\/\}\s*<PrintOffer [^]*?\/>\s*<Summary /.test(app) && app.includes("q.get('ps')") && app.includes('SESSION_RE.test(ps)')
      && app.includes("q.get('print') === 'cancelled'") && /!WITHDRAW_MODE \? readPrintReturn\(\)/.test(app) && app.includes('print_offer: undefined') && app.includes('watchPrint(LINK, PRINT_RETURN.ps'));
  check('a print of a delivered order that is not sent yet reads "we are sending it to production now", never "as soon as your file is ready"',
    app.includes("p.state === 'preparing' && delivered ? C.print.preparingNow : C.print[p.state]") && app.includes("delivered={st.state === 'ready'}"));

  // the words
  // 2026-11-24, the final list: the lead lists what a print can be (behind acrylic glass, on glossy metal, on canvas, as a poster, as an acrylic block) and holds no
  // number; what each thing is stands under the list once it is chosen (the line of its kind, api/_lib/print_names.py about: the block's 2.5 cm, the canvas ready to
  // hang without an outer frame). The keyring is not named: it is not offered yet
  check('the lead of every language lists the five kinds that are offered (the block by the name the list shows) and no keyring; the card with a print chosen shows the '
    + 'line of its kind: the block\'s (2.5 cm, it stands by itself), the canvas\' (ready to hang, without an outer frame), with its picture, name, price and shipping',
    LANGS.every((l) => ORDER_COPY[l].offer.lead.toLowerCase().includes(kindName('block', l).toLowerCase().slice(0, 5)) && !/\d/.test(ORDER_COPY[l].offer.lead)
      && !ORDER_COPY[l].offer.lead.toLowerCase().includes(kindName('keyring', l).toLowerCase().slice(0, 6)))
      && /behind acrylic glass, on glossy metal, on canvas, as a poster or as an acrylic block\. Each one is made to order/.test(W.lead)
      && /po akriliniu stiklu, ant blizgaus metalo, ant drobės, kaip plakatą arba kaip akrilo bloką\./.test(ORDER_COPY.lt.offer.lead)
      && (() => {
        const hb = card({ initial: { choice: { product: 'block20', country: 'DE' } } });
        const hc = card({ initial: { choice: { product: 'canvas60', country: 'LT' } } }, 'lt');
        const h0 = card();
        return /data-kind="block"/.test(hb) && text(hb).includes(sp(`${printName('block20', 'en')}, ${money(7900, 'eur', 'en')}`)) && sp(printName('block20', 'en')) === 'Acrylic block 20 × 20 cm'
          && text(hb).includes(sp(`${W.shipping} ${money(499, 'eur', 'en')}`)) && text(hb).includes(W.consentMissing) && has(hb, 'print-about') && text(hb).includes(kindAbout('block', 'en'))
          && /data-kind="canvas"/.test(hc) && text(hc).includes(kindAbout('canvas', 'lt')) && text(hc).includes(sp(`${printName('canvas60', 'lt')}, ${money(6900, 'eur', 'lt')}`))
          && !has(h0, 'print-about');
      })(), LANGS.map((l) => (ORDER_COPY[l].offer.lead.match(/\d/g) ?? []).join('')).join());
  // 2026-11-24: the card says how long the chosen print takes: its own production time under the list, and the delivery to the chosen country beside the shipping
  // (api/_lib/print_times.py); "Arrives in about 1 to 2 weeks" for everything is gone, the line that the parcel is tracked stays
  const tl = card({ initial: { choice: { product: 'canvas60', country: 'LT' } } }, 'lt');
  const tb = card({ initial: { choice: { product: 'block20', country: 'DE' } } });
  const ts = card({ initial: { choice: { product: 'poster50', country: 'SE' } } });
  const tn = card({ initial: { choice: { product: 'acrylic40', country: '' } } });
  check('the card says the chosen print\'s own production time (a canvas or a poster 2 business days, the others 3) and, once the country is chosen, the delivery to it '
    + '(Lithuania 4 to 6 working days, Germany 3 to 6; a country without a published time "about a week"); no delivery line before a country is chosen',
    has(tl, 'print-made') && text(tl).includes('Gamyba: apie 2 darbo dienas.') && has(tl, 'print-way') && text(tl).includes('Pristatymas (Lietuva): po to paprastai nuo 4 iki 6 darbo dienų.')
      && text(tb).includes(madeText('block', 'en')) && text(tb).includes('Production: about 3 business days.') && text(tb).includes('Delivery (Germany): then usually 3 to 6 working days.')
      && text(ts).includes('Production: about 2 business days.') && text(ts).includes(wayText('SE', 'en')) && text(ts).includes('then usually about a week')
      && has(tn, 'print-made') && !has(tn, 'print-way') && !has(card(), 'print-made')
      && LANGS.every((l) => !/1 (to|bis|ar|vagy|do|kuni|līdz) 2|1-2/.test(ORDER_COPY[l].offer.arrives) && !/\d/.test(ORDER_COPY[l].offer.arrives) && ORDER_COPY[l].offer.arrives.length > 10)
      && text(tb).includes(W.arrives) && W.arrives === 'The parcel is tracked.', text(tl).slice(0, 400));
  // the keyring is ready and not offered (it earns less than the floor until the owner decides): were the server to offer it, the card would show it without a size
  const withKeyring = { ...offer, products: printProducts(false).map((p) => ({ id: p.id, kind: p.kind, cm: p.cm, price: p.price, ship: Object.fromEntries(printCountries().map((cc) => [cc, printShipping(cc, p.id)])) })) };
  const hk = card({ st: ready({ print_offer: withKeyring }), initial: { choice: { product: 'keyring', country: 'LT' } } });
  check('the keyring, were it offered: the list names it without a size ("Keyring, EUR 15.00"), its picture is the upright tag, its line says what it is, and its shipping and total are shown',
    !offerPrints(ready()).some((p) => p.kind === 'keyring') && offerPrints(ready({ print_offer: withKeyring })).length === 12
      && text(hk).includes(`Keyring, ${money(1500, 'eur', 'en')}`) && !/Keyring \d/.test(sp(text(hk))) && /data-kind="keyring"/.test(hk) && text(hk).includes(kindAbout('keyring', 'en'))
      && has(hk, 'print-shipping') && has(hk, 'print-total'), text(hk).slice(0, 300));
  check('the offer\'s words in the eight languages: every string filled, eight different titles and leads, no dash, no price and no digit in the lead, the function '
    + 'words keep their arguments', LANGS.every((l) => {
    const o = ORDER_COPY[l].offer;
    const strings = Object.values(o).filter((v): v is string => typeof v === 'string');
    return strings.length === 23 &&strings.every((s) => s.trim().length > 2) && !DASH.test(JSON.stringify(o)) && !/[\d€]/.test(o.lead) && o.option('NAME', 'PRICE').includes('NAME')
      && o.option('NAME', 'PRICE').includes('PRICE') && o.mockAlt('NAME').includes('NAME') && !!ORDER_COPY[l].print.preparingNow && !DASH.test(ORDER_COPY[l].print.preparingNow);
  }) && new Set(LANGS.map((l) => ORDER_COPY[l].offer.title)).size === 8 && new Set(LANGS.map((l) => ORDER_COPY[l].offer.lead)).size === 8
    && new Set(LANGS.map((l) => ORDER_COPY[l].offer.done)).size === 8, LANGS.map((l) => Object.values(ORDER_COPY[l].offer).filter((v) => typeof v === 'string').length).join());
  for (const [l, cc] of [['lt', 'LT'], ['de', 'DE'], ['hu', 'HU'], ['hr', 'HR'], ['fi', 'FI'], ['et', 'EE'], ['lv', 'LV']] as const) {
    const hx = card({ C: ORDER_COPY[l], lang: l, market: l === 'lt' || l === 'hr' ? l : 'eu', initial: { choice: { product: 'poster50', country: cc } } }, l);
    const o = ORDER_COPY[l].offer;
    check(`${l}: the card in that language (its heading, the print's and the country's names, its shipping and total words, the button's statutory words, the print box of that language)`,
      text(hx).includes(o.title) && text(hx).includes(sp(printName('poster50', l))) && text(hx).includes(countryName(cc, l)) && text(hx).includes(o.shipping) && text(hx).includes(o.total)
        && text(hx).includes(CHECKOUT_LEGAL[l].continueButton) && text(hx).includes(sp(l === 'lt' ? 'SERVERIO LANGELIO TEKSTAS' : CHECKOUT_LEGAL[l].printConsent))
        && text(hx).includes(o.consentMissing) && !text(hx).includes(W.title), text(hx).slice(0, 300));
  }

  // /try without the picker
  setCopyLang('en');
  const eyeObj = (id: string): Eye => ({ id, before: 'data:,b', image: 'D', thumb: 'data:,t', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false, colourOff: false }) as Eye;
  const prices = { one_eye_studio_black: 1997, one_eye_art: 2497, two_eyes: 3997, each_further_eye: 1500 };
  const server = { on: true, currency: 'EUR', markets: ['eu', 'lt', 'hr'], products: offer.products };
  const buy = renderToStaticMarkup(createElement(BuyCard, {
    eyes: [eyeObj('e1')], style: 'solo.powder', styleName: 'Powder Burst', ordering: { open: true, prices, maxEyes: 8, prints: server, consent: { print: { en: 'SERVER BOX TEXT' } } },
    preview: 'ready', stale: [], onRetake: noop, waiver: true, onWaiver: noop, busy: false, step: null, error: null, onBuy: noop,
    state: { kind: 'normal' }, loading: false, advisory: [], wordsBlocked: false,
  } as never));
  check('/try: the buy card shows no print choice even while the server offers prints (the first checkout shows the artwork\'s price alone), and its button is the artwork\'s price and open',
    !has(buy, 'print-pick') && !has(buy, 'print-product') && !text(buy).includes('SERVER BOX TEXT') && text(buy).includes(sp(`Continue to payment · ${money(2497, 'eur', 'en')}`))
      && !/data-testid="buy"[^>]*disabled/.test(buy), text(buy).slice(0, 300));
  const tryApp = read('src/try/TryApp.tsx'), buyCard = read('src/try/BuyCard.tsx');
  check('/try sends no print with its checkout and holds no print state; the picker component stays for the order page and reads no /try dictionary',
    !/PrintPick|printChoice|printConsent|printsOffered/.test(tryApp) && !/PrintPick|printChoice/.test(buyCard) && !/print(Shown)?[:,]/.test(tryApp.slice(tryApp.indexOf('out = await runCheckout'), tryApp.indexOf('out = await runCheckout') + 600))
      && !/from '\.\/copy'/.test(read('src/try/PrintPick.tsx')) && read('src/order/PrintOffer.tsx').includes("from '../try/PrintPick'"));
  check('the /try dictionaries carry no print picker words any more (they moved to the order page\'s), and keep the two answers of the server\'s print path',
    LANGS.every((l) => !('print' in COPY[l]) && !!COPY[l].buy.errors.print_unavailable && !!COPY[l].buy.errors.print_changed));
  return out;
}
