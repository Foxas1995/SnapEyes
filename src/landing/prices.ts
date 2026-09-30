// The hook the new landing reads its prices through. A thin layer over src/shared/usePrices.ts: the visitor's own ladder
// (their variant's while a price experiment runs for them in their market, else the standard one) and whether the
// server's first answer about it has arrived, turned into the texts of ./priceText.ts.
//
// Rules of the page (scripts/check_prices.mjs enforces the first):
//   1. no price is written in any landing file or copy file, and none is read from MARKETS, priceList or PRICE_CENTS: every
//      price text comes from here;
//   2. a price is never printed before `ready`, or it sits in a <PriceGate pending={pending}> (ui.tsx), so a visitor in an
//      experiment never sees the standard price for a moment (the same rule as the price table today);
//   3. the page's money follows the visitor's market (the currency switch) and the page's language, both subscribed here.
import { useMemo } from 'react';
import { useLang } from './lang';
import { useMarket } from '../shared/useMarket';
import { usePrices, usePricesReady } from '../shared/usePrices';
import { useOrderingOpen } from './ordering';
import { landingPrices, type LandingPrices } from './priceText';

export type { LandingPrices, PriceStyle } from './priceText';

export interface LandingPricesState extends LandingPrices {
  /** The server's first answer about the prices has arrived, or was given up on. */
  ready: boolean;
  /** !ready: hold the prices back (PriceGate). */
  pending: boolean;
  /** This deployment takes orders (src/landing/ordering.ts): the "open" variants of the copy apply. */
  open: boolean;
}

export function useLandingPrices(): LandingPricesState {
  const market = useMarket();
  const { lang } = useLang();
  const list = usePrices(market);
  const ready = usePricesReady();
  // the page's one question to the server (src/landing/ordering.ts) is also what brings the visitor's ladder and ends the
  // wait for it: asking here means the prices settle even on a page where nothing else needs to know whether ordering is open
  const open = useOrderingOpen();
  return useMemo(() => ({ ...landingPrices(list, market, lang), ready, pending: !ready, open }), [list, market, lang, ready, open]);
}
