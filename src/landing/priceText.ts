// The prices the new landing prints, from ONE price ladder. Pure (no React, no window), so the build can load it in Node
// and prove that a price experiment's ladder changes every price the page shows (scripts/check_prices.mjs
// checkLandingPrices). The hook that feeds it the visitor's own ladder is ./prices.ts.
//
// Nothing here knows a price. The ladder comes in (the visitor's: src/shared/pricing.ts effectiveList, the variant's while
// a test runs for them), and every text is made from it by the server's own rule (src/shared/markets.ts priceMinor) and
// the site's money format (markets.ts money). There is no second price rule in the landing: priceFor() of the prototype
// was not ported.
import { MAX_EYES, currencyOf, money, priceMinor, type Currency, type Market, type PriceList } from '../shared/markets';
import { classStyle, type PriceClass } from '../shared/styles';

/** Which one-eye price: the black class (Clean Iris, the registry's price_class "black") is its own price, every style of the art class
 *  shares the other. More eyes cost the same in any style. The class is the registry's (src/shared/styles.ts), never a style id written here. */
export type PriceStyle = PriceClass;

export interface LandingPrices {
  market: Market;
  currency: Currency;
  /** The ladder these texts were made from. */
  list: PriceList;
  /** Any amount in Stripe's smallest unit, as the site writes it in this market's currency and the page's language. */
  fmt: (minor: number) => string;
  /** The lowest price of one eye: "Digital file from {from}" (hero.fromPrice). */
  from: string;
  /** One eye on black (Clean Iris) and one eye in an art style. */
  black: string;
  art: string;
  /** Each further eye after the second: {price} of pricing.rows.more.b and styles.comboBody. */
  price: string;
  /** Two eyes: {price2} of pricing.rows.more.b. */
  price2: string;
  /** The most eyes one artwork holds: {max}. */
  max: number;
  /** The price of n eyes (1 to MAX_EYES) by the server's rule; the class only matters for one eye. */
  eyes: (n: number, cls?: PriceStyle) => string;
  /** The tokens the copy asks for, ready for t() and fmt(): { from, price, price2, max }. */
  tokens: { from: string; price: string; price2: string; max: number };
}

/** Every price text of the landing for a ladder, a market and a language. list must be a full ladder (the four prices of
 *  api/_lib/markets.py). */
export function landingPrices(list: PriceList, market: Market, lang: string): LandingPrices {
  const currency = currencyOf(market);
  const fmt = (minor: number) => money(minor, currency, lang);
  // priceMinor takes a style and finds its class in the registry: a representative style of the class stands in for the class
  const eyes = (n: number, cls: PriceStyle = 'black') => fmt(priceMinor(n, classStyle(cls), market, list));
  const from = fmt(Math.min(list.one_eye_studio_black, list.one_eye_art));
  const price = fmt(list.each_further_eye);
  const price2 = fmt(list.two_eyes);
  return {
    market,
    currency,
    list,
    fmt,
    from,
    black: eyes(1, 'black'),
    art: eyes(1, 'art'),
    price,
    price2,
    max: MAX_EYES,
    eyes,
    tokens: { from, price, price2, max: MAX_EYES },
  };
}
