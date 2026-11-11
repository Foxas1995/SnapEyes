// Gift vouchers (api/_lib/voucher.py markets): sold and redeemed in euros, on the markets that read the EU edition of the legal texts. The checkout's voucher
// field (src/try/GiftField.tsx) and the gift page (src/gift) ask this one rule.
import { currencyOf, type Market } from './markets';
import { legalEdition } from './legal';

export const giftMarket = (m: Market): boolean => currencyOf(m) === 'eur' && legalEdition(m) === 'eu';
