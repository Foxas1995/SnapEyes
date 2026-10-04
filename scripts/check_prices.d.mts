// Types of ./check_prices.mjs for vite.config.ts (tsconfig.node.json checks that file with Node's module rules).
export interface MarketsSource {
  defaultMarket: string;
  markets: Record<string, {
    currency: string;
    prices: Record<string, number>;
    selectable: number;
    lang: string;
    stripe_locale: Record<string, string>;
    countries: string[];
  }>;
}

/** src/shared/markets.ts as the build loaded it: its reading of api/_lib/markets.py and its price rule. */
export interface ClientMarkets {
  DEFAULT_MARKET: string;
  MARKETS: unknown;
  priceMinor: (n: number, style: string, market: string, list?: Partial<Record<string, number>>) => number;
}

export const MARKETS_FILE: string;
export function parseMarketsSource(src: string): MarketsSource;
/** The price of n eyes by the price class ("black" or "art") of the style: one eye by its class, then the same amount per further eye. */
export function priceRule(markets: MarketsSource['markets'], market: string, eyes: number, cls: string): number;
export function checkPrices(root: string, client?: ClientMarkets): string[];
