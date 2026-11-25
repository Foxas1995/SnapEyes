// Value vouchers as the page code reads them (the owner's decision of 2026-11-25 (value vouchers): a voucher is an amount, 30, 60, 100, 120 or 170 EUR, and a
// balance spent on artworks and prints until it is used up; api/_lib/voucher.py). The gift page (src/gift/GiftApp.tsx, src/gift/copy.ts): five amount buttons,
// 100 chosen first, one short line of what it covers as an example, the buy request with the amount; the order page's print offer (src/order/PrintOffer.tsx,
// src/order/printAddon.ts): the balance of the voucher the artwork was paid with and the price after it, the small field for a code when there is none, the
// check of a typed code and the buy request that carries it; /try's field sends the order it made. The server's side is scripts/styles_tests/test_gift.py
// (v3gift) and test_prints.py (v3prints).
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'node:fs';
import { GiftApp } from '../../src/gift/GiftApp';
import { GIFT_COPY } from '../../src/gift/copy';
import { DEFAULT_GIFT_AMOUNT, GIFT_AMOUNTS } from '../../src/shared/gift';
import { PrintOffer } from '../../src/order/PrintOffer';
import { buyPrint, checkPrintVoucher, offerVoucher, voucherSplit, type PrintOfferReply } from '../../src/order/printAddon';
import { ORDER_COPY } from '../../src/order/copy';
import type { OrderStatus } from '../../src/order/api';
import { COPY } from '../../src/try/copy';
import { printCountries, printProducts, printShipping } from '../../src/shared/prints';
import { money } from '../../src/shared/markets';

type Row = [string, boolean, string?];
const text = (h: string) => h.replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/\s+/g, ' ').trim();
const has = (h: string, id: string) => h.includes(`data-testid="${id}"`);
const DASH = new RegExp('[' + [0x2012, 0x2013, 0x2014, 0x2015].map((c) => String.fromCharCode(c)).join('') + ']');
const LANGS = ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'] as const;
const noop = () => undefined;

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  // the amounts: the page's list is the server's
  const py = readFileSync('api/_lib/voucher.py', 'utf8');
  const m = /^AMOUNTS = \(([0-9, ]+)\)/m.exec(py);
  const server = m ? m[1].split(',').map((x) => Number(x.trim())) : [];
  check('the five amounts of the gift page are the server\'s (api/_lib/voucher.py AMOUNTS): 30, 60, 100, 120 and 170 EUR, and 100 is chosen first',
    JSON.stringify([...GIFT_AMOUNTS]) === JSON.stringify(server) && JSON.stringify(server) === '[3000,6000,10000,12000,17000]' && DEFAULT_GIFT_AMOUNT === 10000, JSON.stringify(server));

  // the words of the gift page
  check('every language has one short line per amount, said as an example ("for example"), no dash, and the rule is 12 months without "one order"', LANGS.every((l) => {
    const g = GIFT_COPY[l];
    const lines = GIFT_AMOUNTS.map((a) => g.amounts[a]);
    return lines.every((x) => typeof x === 'string' && x.length > 10 && x.length < 90 && !DASH.test(x)) && new Set(lines).size === 5 && /12/.test(g.rules)
      && g.rules.length < 30 && !!g.valueFor && !DASH.test(g.valueFor + g.choose);
  }), LANGS.map((l) => GIFT_COPY[l].rules).join(' | '));
  const lt = GIFT_COPY.lt;
  check('the Lithuanian lines are plain and short: "Pavyzdžiui, užtenka ..." (30 an artwork; 60 for two or with a keyring; 100 a 30 cm acrylic or metal print; 120 and 170 acrylic of 40 and 60 cm), "Galioja 12 mėnesių."',
    lt.amounts[3000] === 'Pavyzdžiui, užtenka vienos akies kūriniui.' && lt.amounts[6000] === 'Pavyzdžiui, užtenka kūriniui porai arba kūriniui ir raktų pakabukui.'
      && lt.amounts[10000] === 'Pavyzdžiui, užtenka kūriniui ir 30 cm akrilo ar metalo spaudiniui.' && lt.amounts[12000] === 'Pavyzdžiui, užtenka kūriniui ir 40 cm akrilo spaudiniui.'
      && lt.amounts[17000] === 'Pavyzdžiui, užtenka kūriniui ir 60 cm akrilo spaudiniui.' && lt.rules === 'Galioja 12 mėnesių.', JSON.stringify(lt.amounts));
  check('every line says "for example" in its language (never a promise that differs by country)', LANGS.every((l) => GIFT_AMOUNTS.every((a) =>
    /^(For example|Zum Beispiel|Pavyzdžiui|Például|Na primjer|Esimerkiksi|Näiteks|Piemēram)\b/.test(GIFT_COPY[l].amounts[a]))));

  // the page itself
  let page = '';
  try {
    page = renderToStaticMarkup(createElement(GiftApp));
  } catch (e) {
    page = `THREW ${String(e)}`;
  }
  const C = GIFT_COPY.en;
  check('the gift page: five amount buttons, 100 checked first, its one line under them, the button with 100 EUR; no buttons of the old kinds, no artwork pictures in the chooser',
    GIFT_AMOUNTS.every((a) => has(page, `gift-amount-${a}`)) && /data-testid="gift-amount-10000"[^>]*aria-checked="true"|aria-checked="true"[^>]*data-testid="gift-amount-10000"/.test(page)
      && (page.match(/aria-checked="true"/g) ?? []).length === 1 && has(page, 'gift-hint') && text(page).includes(C.amounts[10000])
      && text(page).includes(text(C.buy(money(10000, 'eur', 'en')))) && !has(page, 'gift-kind-one') && !has(page, 'gift-kind-two') && !page.includes('gift-two-900')
      && page.includes('XXXX XXXX XXXX') && has(page, 'gift-flow'), text(page).slice(0, 600));
  const src = readFileSync('src/gift/GiftApp.tsx', 'utf8');
  check('the page buys with {gift: {amount}} (never a kind) and reads a code of the old kinds too', src.includes('gift: { amount }') && !src.includes('gift: { kind }')
    && src.includes("k === 'value'") && src.includes("k === 'one'"));

  // the print offer: the balance of the voucher the artwork was paid with
  const offer: PrintOfferReply = {
    currency: 'EUR',
    products: printProducts().map((p) => ({ id: p.id, kind: p.kind, cm: p.cm, price: p.price, ship: Object.fromEntries(printCountries().map((cc) => [cc, printShipping(cc, p.id)])) })),
    consent: { en: 'SERVER BOX TEXT' },
  };
  const ready = (over: Partial<OrderStatus> = {}): OrderStatus => ({
    order: '261125-0123456789abcdef', state: 'ready', eyes: [{ eye: 1, made: true }], count: 1, style: 'solo.powder', market: 'lt', currency: 'EUR', amount: 0,
    download: { url: 'https://files.test/a.jpg', download_url: 'https://files.test/a.jpg?download=1' }, print_offer: offer, ...over,
  } as OrderStatus);
  const link = { o: '261125-0123456789abcdef', k: 'a'.repeat(32), s: null };
  const card = (o: Record<string, unknown> = {}, lang: (typeof LANGS)[number] = 'en') => renderToStaticMarkup(createElement(PrintOffer, {
    C: ORDER_COPY[lang], lang, link, st: ready(), market: 'lt', back: null, email: true, onReload: noop, onRecheck: noop, ...o,
  } as never));
  const W = ORDER_COPY.en.offer.voucher;
  const withV = ready({ print_offer: { ...offer, voucher: { balance: 7503, valid_until: '2027-11-25' } } });
  check('offerVoucher: the balance of the offer, 0 without one or for nonsense', offerVoucher(withV) === 7503 && offerVoucher(ready()) === 0
    && offerVoucher(ready({ print_offer: { ...offer, voucher: { balance: -5 } } })) === 0 && offerVoucher(null) === 0);
  check('voucherSplit: the voucher takes the whole total (the shipping too) up to its balance; the rest is to pay', JSON.stringify(voucherSplit(6749, 7503)) === '{"discount":6749,"pay":0}'
    && JSON.stringify(voucherSplit(8749, 7503)) === '{"discount":7503,"pay":1246}' && JSON.stringify(voucherSplit(100, 0)) === '{"discount":0,"pay":100}');
  const v0 = card({ st: withV });
  check('the offer of an order paid with a voucher that has a balance: one line "Gift voucher balance: 75.03", no field to type a code, no price rows before a print is chosen',
    has(v0, 'print-voucher') && text(v0).includes(W.balance(money(7503, 'eur', 'en'))) && !has(v0, 'print-voucher-open') && !has(v0, 'print-voucher-field')
      && !has(v0, 'print-voucher-split'), text(v0).slice(0, 400));
  const v1 = card({ st: withV, initial: { choice: { product: 'acrylic30', country: 'LT' }, consent: true } });
  check('a 30 cm acrylic to Lithuania (59 + 8.49): the total, the voucher takes all of it, to pay 0.00, the button open',
    text(v1).includes(money(6749, 'eur', 'en')) && has(v1, 'print-voucher-split') && text(v1).includes(`−${money(6749, 'eur', 'en')}`)
      && /data-testid="print-to-pay"[^]*?0\.00/.test(v1) && !/data-testid="print-buy"[^>]*disabled/.test(v1), text(v1).slice(-500));
  const v2 = card({ st: withV, initial: { choice: { product: 'acrylic40', country: 'LT' }, consent: true } });
  check('a 40 cm acrylic (79 + 8.49) with 75.03 left: the voucher takes 75.03, the rest is to pay', text(v2).includes(`−${money(7503, 'eur', 'en')}`)
    && text(v2).includes(money(1246, 'eur', 'en')), text(v2).slice(-400));
  const v3 = card();
  check('an order paid without a voucher: the small link "I have a gift voucher" only (no field until it is pressed, no balance)', has(v3, 'print-voucher-open')
    && text(v3).includes(W.open) && !has(v3, 'print-voucher-field') && !has(v3, 'print-voucher'));
  const v4 = card({ initial: { field: true } });
  check('pressed: the code field and its button', has(v4, 'print-voucher-field') && has(v4, 'print-voucher-code') && has(v4, 'print-voucher-apply'));
  const v5 = card({ initial: { typed: { code: 'K7MWQ2XH9PRD', value: 3000 }, choice: { product: 'poster50', country: 'LT' }, consent: true } });
  check('a typed code accepted with 30.00: the balance line, the voucher row and what is left to pay of the poster (35 + 8.49)', has(v5, 'print-voucher')
    && text(v5).includes(`−${money(3000, 'eur', 'en')}`) && text(v5).includes(money(1349, 'eur', 'en')) && !has(v5, 'print-voucher-open'), text(v5).slice(-400));
  const v6 = card({ initial: { error: 'voucher' } });
  check('a code the server refused at the checkout: its one sentence', text(v6).includes(W.bad));

  // the requests
  const seen: { path: string; body?: Record<string, unknown> }[] = [];
  const api = (reply: Record<string, unknown>) => (async (path: string, init?: { body?: Record<string, unknown> }) => {
    seen.push({ path, body: init?.body });
    return reply;
  }) as never;
  const okv = await checkPrintVoucher('k7mw-q2xh-9prd', 'lt', link.o, api({ ok: true, status: 200, data: { ok: true, valid: true, value: 3000 }, reason: '', error: '' }));
  const q = new URL('https://x' + seen[0].path).searchParams;
  check('checkPrintVoucher asks GET /api/checkout?voucher=<code>&m=<market>&o=<order>&u=print and answers the balance', 'value' in okv && okv.value === 3000
    && q.get('voucher') === 'K7MWQ2XH9PRD' && q.get('m') === 'lt' && q.get('o') === link.o && q.get('u') === 'print', seen[0].path);
  const old = await checkPrintVoucher('K7MWQ2XH9PRD', 'lt', link.o, api({ ok: false, status: 409, data: { ok: false, reason: 'voucher_invalid', why: 'artwork' }, reason: 'voucher_invalid', error: '' }));
  const used = await checkPrintVoucher('K7MWQ2XH9PRD', 'lt', link.o, api({ ok: false, status: 409, data: { ok: false, reason: 'voucher_invalid', why: 'used' }, reason: 'voucher_invalid', error: '' }));
  const short = await checkPrintVoucher('K7M', 'lt', link.o, api({ ok: true, status: 200, data: {}, reason: '', error: '' }));
  check('an old voucher: why artwork; any other refusal: bad; a code of the wrong length is not even sent', 'why' in old && old.why === 'artwork' && 'why' in used && used.why === 'bad'
    && 'why' in short && short.why === 'bad' && seen.length === 3);
  seen.length = 0;
  const b1 = await buyPrint(link, { product: 'poster50', country: 'LT' }, 'lt', 4349, api({ ok: true, status: 200, data: { url: 'https://checkout.stripe.test/c' }, reason: '', error: '' }), 'K7MWQ2XH9PRD');
  const b2 = await buyPrint(link, { product: 'poster50', country: 'LT' }, 'lt', 4349, api({ ok: true, status: 200, data: { url: 'https://checkout.stripe.test/c' }, reason: '', error: '' }));
  const b3 = await buyPrint(link, { product: 'poster50', country: 'LT' }, 'lt', 4349, api({ ok: false, status: 409, data: { why: 'used' }, reason: 'voucher_invalid', error: '' }), 'K7MWQ2XH9PRD');
  check('buyPrint sends a typed code as voucher (and no voucher key without one); 409 voucher_invalid is the error "voucher"', b1.kind === 'redirect' && seen[0].body?.voucher === 'K7MWQ2XH9PRD'
    && b2.kind === 'redirect' && !('voucher' in (seen[1].body ?? {})) && b3.kind === 'error' && b3.code === 'voucher', JSON.stringify(seen.map((s) => s.body)));

  // the words
  check('the offer\'s voucher words in every language, without dashes; the link says what /try\'s does', LANGS.every((l) => {
    const v = ORDER_COPY[l].offer.voucher;
    return v.balance('X').includes('X') && !!v.row && !!v.pay && !!v.apply && !!v.bad && !!v.artwork && v.open === COPY[l].gift.open
      && !DASH.test(JSON.stringify(v) + v.balance('X'));
  }), LANGS.filter((l) => ORDER_COPY[l].offer.voucher.open !== COPY[l].gift.open).join());
  check('/try\'s voucher note says the rest stays on the voucher (never that it is lost) in every language', LANGS.every((l) => !/not paid out|negrąžinamas|nicht ausgezahlt/.test(COPY[l].gift.note))
    && COPY.lt.gift.note === 'Kuponas panaudojamas, kai užbaigiate mokėjimą. Likutis lieka kupone.');
  const field = readFileSync('src/try/GiftField.tsx', 'utf8');
  check('/try\'s field sends the order it made already (o), so a customer back from Stripe sees the voucher without their own reservation', field.includes('&o=${encodeURIComponent(order)}'));
  return out;
}
