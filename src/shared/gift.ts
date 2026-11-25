// Gift vouchers (api/_lib/voucher.py markets): sold and redeemed in euros, on the markets that read the EU edition of the legal texts. The checkout's voucher
// field (src/try/GiftField.tsx) and the gift page (src/gift) ask this one rule.
import { currencyOf, type Market } from './markets';
import { legalEdition } from './legal';

export const giftMarket = (m: Market): boolean => currencyOf(m) === 'eur' && legalEdition(m) === 'eu';

// The amounts a gift voucher is sold for, in euro cents (the owner's decision of 2026-11-25 (value vouchers): a voucher is a balance, spent on artworks and
// prints until it is used up). api/_lib/voucher.py AMOUNTS is the server's list; suites/ts/gift.test.ts holds the two to the same numbers.
export const GIFT_AMOUNTS = [3000, 6000, 10000, 12000, 17000] as const;
export type GiftAmount = (typeof GIFT_AMOUNTS)[number];
export const DEFAULT_GIFT_AMOUNT: GiftAmount = 10000;
