// The price line of the hero ("Digital file from {from}"): which price it prints and whether it is held back. Pure, so the page (./Hero.tsx) and the build's gate
// (src/landing/shell/gate.tsx, which renders the hero in every state of the catalogue) read ONE rule.
//
// "From" is the lowest price among the styles that can be bought now for one eye (the run-time catalogue while ordering is open: src/shared/catalogue.ts saleCatalogue).
// With none the line is held back for good, exactly like a price that is still pending (invisible, out of the accessibility tree, its words and so its space kept: the
// prerendered first screen has the same box and nothing moves when the server answers), so no price of a style nobody can buy is ever shown or read out.
import type { RunCatalogue } from '../shared/catalogue';
import type { LandingPrices } from './priceText';

export interface HeroPrice {
  /** The price text for {from}: the lowest among what can be bought now, else the ladder's own lowest (held back, so never shown). */
  from: string;
  /** The line is invisible and inert: the prices have not arrived, or nothing can be bought for one eye. */
  held: boolean;
}

export function heroPrice(prices: LandingPrices, pending: boolean, sale: RunCatalogue): HeroPrice {
  const lowest = prices.fromOf(sale.one);
  return { from: lowest ?? prices.from, held: pending || lowest === null };
}
