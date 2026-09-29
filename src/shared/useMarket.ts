import { useSyncExternalStore } from 'react';
import { DEFAULT_MARKET, currentMarket, subscribeMarket, type Market } from './markets';

/** The page's market (./markets.ts currentMarket), re-rendering when the visitor switches it or the order page adopts
 *  its order's market. */
export function useMarket(): Market {
  return useSyncExternalStore(subscribeMarket, currentMarket, () => DEFAULT_MARKET);
}
