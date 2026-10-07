// The price line of the hero ("Digital file from {from}"): which price it prints and whether it is held back. Pure, so the page (./Hero.tsx) and the build's gate
// (src/landing/shell/gate.tsx, which renders the hero in every state of the catalogue) read ONE rule.
//
// "From" is the lowest price among the styles that can be bought now for one eye (the run-time catalogue while ordering is open: src/shared/catalogue.ts saleCatalogue).
// With none the line is held back for good, exactly like a price that is still pending (invisible, out of the accessibility tree, its words and so its space kept: the
// prerendered first screen has the same box and nothing moves when the server answers), so no price of a style nobody can buy is ever shown or read out.
import type { RunCatalogue } from '../shared/catalogue';
import type { LandingPrices } from './priceText';

/** What stands where the number would be while the line is held back: six figure spaces (U+2007, the width of a digit), about the width of a price
 *  (the line keeps its words and its box, so the prerendered first screen and the live one occupy the same space and nothing moves when a price arrives). The line is
 *  invisible and inert while it is held, and it also CARRIES no price: a crawler or a text extractor that reads the markup of a page that sells nothing yet finds
 *  "Digital file from" and nothing after it (release review H-m6, P-m5). Built from its code so that no invisible character sits in the source. */
export const HELD_PRICE = String.fromCharCode(0x2007).repeat(6);

export interface HeroPrice {
  /** The price text for {from}: the lowest among what can be bought now; HELD_PRICE (no price at all) while the line is held back. */
  from: string;
  /** The line is invisible and inert: the prices have not arrived, or nothing can be bought for one eye. */
  held: boolean;
}

export function heroPrice(prices: LandingPrices, pending: boolean, sale: RunCatalogue): HeroPrice {
  const lowest = prices.fromOf(sale.one);
  const held = pending || lowest === null;
  return { from: held || lowest === null ? HELD_PRICE : lowest, held };
}
