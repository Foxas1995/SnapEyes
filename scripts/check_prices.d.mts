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
  /** A price as the site writes it (src/shared/markets.ts money): the check compares the landing's texts with it. */
  money?: (minor: number, currency: string, lang?: string) => string;
}

/** src/landing/priceText.ts as the build loaded it: every price text of the new landing for a ladder, a market and a language. */
export interface LandingPriceModule {
  landingPrices: (list: Record<string, number>, market: string, lang: string) => {
    from: string; black: string; art: string; price: string; price2: string;
    eyes: (n: number, style?: 'studio_black' | 'art') => string;
  };
}

export const MARKETS_FILE: string;
export function parseMarketsSource(src: string): MarketsSource;
export function priceRule(markets: MarketsSource['markets'], market: string, eyes: number, style: string): number;
export function checkPrices(root: string, client?: ClientMarkets, landing?: LandingPriceModule): string[];
