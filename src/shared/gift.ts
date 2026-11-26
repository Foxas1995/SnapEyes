// Gift vouchers (api/_lib/voucher.py markets): sold and redeemed in euros, on the markets that read the EU edition of the legal texts. The checkout's voucher
// field (src/try/GiftField.tsx) and the gift page (src/gift) ask this one rule.
import { currencyOf, type Market } from './markets';
import { legalEdition } from './legal';

export const giftMarket = (m: Market): boolean => currencyOf(m) === 'eur' && legalEdition(m) === 'eu';

// The amounts a gift voucher is sold for, in euro cents (the owner's decision of 2026-11-25 (value vouchers): a voucher is a balance, spent on artworks and
// prints until it is used up). api/_lib/voucher.py AMOUNTS is the server's list; suites/ts/gift.test.ts holds the two to the same numbers.
export const GIFT_AMOUNTS = [3000, 6000, 10000, 12000, 17000] as const;
export type GiftAmount = (typeof GIFT_AMOUNTS)[number];
// The amount the page opens with: the smallest (the owner's word of 2026-11-26: the first two ad visitors who went on to pay saw 100 euros preselected
// and left; 100 until then).
export const DEFAULT_GIFT_AMOUNT: GiftAmount = 3000;

/** Stripe's minimum charge in euros (0.50 EUR): what is left to pay after a voucher is 0 or at least this (api/_lib/voucher.py MIN_CHARGE). */
export const MIN_CHARGE = 50;

/** What a voucher with this much left pays of a total, as the server reserves it (api/_lib/voucher.py pays): all it can, but a remainder under
 *  Stripe's minimum charge is made the minimum and the voucher keeps the difference. */
export function voucherPays(total: number, left: number): number {
  let amount = Math.max(0, Math.min(left, total));
  if (total - amount > 0 && total - amount < MIN_CHARGE) amount = Math.max(0, total - MIN_CHARGE);
  return amount;
}
