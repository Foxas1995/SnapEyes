import { useSyncExternalStore } from 'react';
import { currentMarket, type Market, type PriceList } from './markets';
import { effectiveList, pricingReady, subscribePricing } from './pricing';

/** The ladder the visitor is charged in a market (./pricing.ts effectiveList: their variant's while a price experiment
 *  runs for them there, else the standard one), re-rendering when the server's answer arrives. */
export function usePrices(market: Market = currentMarket()): PriceList {
  return useSyncExternalStore(subscribePricing, () => effectiveList(market), () => effectiveList(market));
}

/** Has the server's first answer about the prices arrived (or been given up on)? A page that prints prices outside the
 *  first screen waits for it, so a visitor in an experiment never sees the standard price for a moment. */
export function usePricesReady(): boolean {
  return useSyncExternalStore(subscribePricing, pricingReady, () => true);
}
