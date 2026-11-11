// Gift vouchers as the page code reads them (src/shared/gift.ts, src/try/GiftField.tsx, src/try/BuyCard.tsx, src/try/checkout.ts, src/gift/copy.ts,
// src/legal/docs/vouchers.ts): where the voucher field shows, what the button then charges, what the checkout sends, the words in five languages and
// the legal texts of each edition. The server's side is scripts/styles_tests/test_gift.py (v3gift).
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { BuyCard } from '../../src/try/BuyCard';
import { tidyCode } from '../../src/try/GiftField';
import { giftMarket } from '../../src/shared/gift';
import { COPY, setCopyLang } from '../../src/try/copy';
import { GIFT_COPY } from '../../src/gift/copy';
import { runCheckout } from '../../src/try/checkout';
import { EDITIONS } from '../../src/legal/editions';
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
const LANGS = ['en', 'de', 'lt', 'hu', 'hr'] as const;
const noop = () => undefined;

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);

  check('vouchers are sold and used on the euro markets of the EU edition only (eu, lt, hr; not au, hu, us, uk)',
    ['eu', 'lt', 'hr'].every(giftMarket) && !['au', 'hu', 'us', 'uk'].some(giftMarket));
  check('a typed code is tidied as people read it: capitals, the dashes once it has 12 characters, nothing else',
    tidyCode('k7mw q2xh 9prd') === 'K7MW-Q2XH-9PRD' && tidyCode('k7m') === 'K7M' && tidyCode('K7MW-Q2XH-9PRD-XX') === 'K7MW-Q2XH-9PRD', tidyCode('k7mw q2xh 9prd'));

  // the buy card
  setCopyLang('en');
  const eyeObj = (id: string): Eye => ({ id, before: 'data:,b', image: 'D', thumb: 'data:,t', pad: 1.12, fallback: false, usedSr: false, stored: false, glarePct: 0, sample: false, colourOff: false }) as Eye;
  const prices = { one_eye_studio_black: 1997, one_eye_art: 2497, two_eyes: 3997, each_further_eye: 1500 };
  const buy = (o: Record<string, unknown> = {}) => renderToStaticMarkup(createElement(BuyCard, {
    eyes: [eyeObj('e1')], style: 'solo.powder', styleName: 'Powder Burst', ordering: { open: true, prices, maxEyes: 8 },
    preview: 'ready', stale: [], onRetake: noop, waiver: true, onWaiver: noop, busy: false, step: null, error: null, onBuy: noop,
    state: { kind: 'normal' }, loading: false, advisory: [], wordsBlocked: false, ...o,
  } as never));
  const h0 = buy();
  check('a card without onGift offers no voucher (the card of before vouchers)', !has(h0, 'gift-open') && !has(h0, 'gift-applied'), text(h0).slice(0, 200));
  const h1 = buy({ onGift: noop, gift: null });
  check('with onGift on a euro market: the closed link "I have a gift voucher", the button the full price', has(h1, 'gift-open') && text(h1).includes(COPY.en.gift.open)
    && text(h1).includes(sp(`Continue to payment · ${money(2497, 'eur', 'en')}`)), text(h1).slice(0, 400));
  const h2 = buy({ onGift: noop, gift: { code: 'K7MWQ2XH9PRD', value: 2497 } });
  check('an accepted voucher of the full price: its line with the value and Remove, the button says 0', has(h2, 'gift-applied') && has(h2, 'gift-remove')
    && text(h2).includes(sp(COPY.en.gift.applied(money(2497, 'eur', 'en')))) && text(h2).includes(sp(`Continue to payment · ${money(0, 'eur', 'en')}`)), text(h2).slice(0, 500));
  const h3 = buy({ onGift: noop, gift: { code: 'K7MWQ2XH9PRD', value: 1000 } });
  check('a voucher worth less than the artwork: the button says the rest', text(h3).includes(sp(`Continue to payment · ${money(1497, 'eur', 'en')}`)), text(h3).slice(0, 500));

  // the checkout request
  const bodies: Record<string, unknown>[] = [];
  const api = async (path: string, init?: { body?: Record<string, unknown> }) => {
    bodies.push({ path, ...(init?.body ?? {}) });
    if (path === '/api/order') return { ok: true, status: 200, data: { order: '261028-0123456789abcdef', k: 'a'.repeat(32), eye: 1, created: true, expires_at: Math.floor(Date.now() / 1000) + 86400 }, reason: '', error: '' };
    if (bodies.filter((b) => b.path === '/api/checkout').length > 1) return { ok: false, status: 409, data: { ok: false, reason: 'voucher_invalid', why: 'used' }, reason: 'voucher_invalid', error: '' };
    return { ok: true, status: 200, data: { url: 'https://checkout.stripe.test/c', expires_at: Math.floor(Date.now() / 1000) + 3600 }, reason: '', error: '' };
  };
  const eye1 = { ...eyeObj('e1'), sealed: 'S', draft: { crop: 'C', ticket: 'T', until: Date.now() + 600_000 } } as Eye;
  const base = { eyes: [eye1], style: 'solo.powder', layout: 'single' as never, names: '', lang: 'en' as never, ref: null, market: 'lt', shown: 2497 };
  await runCheckout({ ...base, voucher: 'K7MWQ2XH9PRD' }, noop, api as never);
  const cb = bodies.find((b) => b.path === '/api/checkout') ?? {};
  check('the checkout request carries the voucher code', cb.voucher === 'K7MWQ2XH9PRD' && cb.consent_digital === true, JSON.stringify(cb));
  const again = await runCheckout({ ...base, voucher: 'K7MWQ2XH9PRD' }, noop, api as never);
  check('409 voucher_invalid: the checkout ends with the error "voucher" (the page takes the voucher off the card)', again.kind === 'error' && 'code' in again && again.code === 'voucher', JSON.stringify(again));
  bodies.length = 0;
  await runCheckout(base, noop, api as never);
  const cb2 = bodies.find((b) => b.path === '/api/checkout') ?? {};
  check('a checkout without a voucher sends no voucher key (the request of before vouchers)', !('voucher' in cb2), JSON.stringify(cb2));

  // the words
  check('the checkout\'s voucher words and its error in every language, without dashes', LANGS.every((l) => {
    const g = COPY[l].gift;
    return !!g.open && !!g.apply && !!g.note && Object.values(g.errors).every(Boolean) && g.applied('X').includes('X') && !!COPY[l].buy.errors.voucher
      && !DASH.test(JSON.stringify(g)) && !DASH.test(COPY[l].buy.errors.voucher);
  }));
  check('the gift page\'s words in every language, the price in the button, without dashes', LANGS.every((l) => {
    const g = GIFT_COPY[l];
    return g.buy('PRICE').includes('PRICE') && g.steps.length === 3 && !!g.ready.title && g.card.until('X').includes('X') && !DASH.test(JSON.stringify(g, (_k, v) => (typeof v === 'function' ? v('') : v)));
  }));
  check('the email\'s button word matches the checkout\'s link: the code is entered after "I have a gift voucher"', COPY.lt.gift.open === 'Turiu dovanų kuponą'
    && COPY.hu.gift.open === 'Van ajándékutalványom' && COPY.hr.gift.open === 'Imam poklon-bon' && COPY.de.gift.open === 'Ich habe einen Geschenkgutschein');

  // the legal texts
  const eu = EDITIONS.eu;
  check('the EU edition: the terms, the privacy policy and the withdrawal page have a section "vouchers" in all five languages',
    LANGS.every((l) => !!eu.terms[l]?.sections.some((s) => s.id === 'vouchers') && !!eu.privacy[l]?.sections.some((s) => s.id === 'vouchers')
      && !!eu.withdrawal[l]?.sections.some((s) => s.id === 'vouchers')));
  const tv = sectionText(eu.terms.en, 'vouchers');
  check('the English terms: the two vouchers with their prices, 12 months, one order, the rest not paid out, the 14 days while unused',
    tv.includes(money(2497, 'eur', 'en')) && tv.includes(money(3997, 'eur', 'en')) && tv.includes('12 months') && tv.includes('once')
      && tv.includes('not paid out') && tv.includes('14 days') && !DASH.test(tv), tv.slice(0, 300));
  const order = eu.terms.en?.sections.map((s) => s.id).join() ?? '';
  check('the voucher section follows the prices, whose last sentence points to it', /prices,vouchers,/.test(order)
    && sectionText(eu.terms.en, 'prices').includes('Gift vouchers'), order);
  const hu = EDITIONS.hu.terms;
  check('the Hungarian edition (forints): a voucher section without euro prices, the price section says vouchers are euros only',
    (['en', 'de', 'lt', 'hu'] as const).every((l) => !!hu[l]?.sections.some((s) => s.id === 'vouchers') && !sectionText(hu[l], 'vouchers').includes(money(2497, 'eur', l))
      && !sectionText(hu[l], 'vouchers').includes(money(3997, 'eur', l))) && sectionText(hu.en, 'prices').includes('cannot pay for an order in forints'), sectionText(hu.en, 'vouchers').slice(0, 300));
  check('the Australian and the US editions have no voucher section', !EDITIONS.au.terms.en?.sections.some((s) => s.id === 'vouchers')
    && !EDITIONS.us.terms.en?.sections.some((s) => s.id === 'vouchers') && !EDITIONS.au.privacy.en?.sections.some((s) => s.id === 'vouchers'));
  const pv = sectionText(eu.privacy.en, 'vouchers');
  check('the privacy policy: the email only at Stripe and in the email, no address and no code in our record', pv.includes('holds no email address')
    && pv.includes('The code itself is not stored') && sectionText(eu.privacy.lt, 'retention').includes('Dovanų kuponai'), pv.slice(0, 300));
  return out;
}
