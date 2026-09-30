// The markets the site sells in (a market = one currency and one price list), shared by the landing page, /try, the
// order page, the legal pages and the admin panel. Plain data and functions only, no React (./useMarket.ts has the
// hook), so the build's legal pack (src/legal/plain.ts, run in Node) can import it too.
//
// THE ONE PLACE for prices is api/_lib/markets.py: the server charges from it, and this module reads that same file as
// text at build time and parses its MARKETS literal as JSON. Nothing here or anywhere else in src holds a price of its
// own; the build fails when one does, or when the literal breaks a rule (scripts/check_prices.mjs, run by
// vite.config.ts). The server stays the authority: it prices every checkout itself (GET /api/checkout also returns its
// price lists, and the buy card prefers those).
//
// Which market a visitor sees: the link (?m=au), then the visitor's earlier choice (localStorage "snapeyes.market",
// like "snapeyes.lang"), then the default. Never the IP address: the server's country hint (GET /api/checkout suggest)
// may only be offered (hintMarket, the landing page's MarketHint), never applied. A market that is not selectable
// (MARKETS "selectable": 0) is ignored in links, except by the legal pages and the order page, which keep showing the
// texts an order was made under (linkMarket, adoptMarket).
// Every internal link carries the market as m= (withMarket), except for the default market, whose links stay as they
// always were.
import MARKETS_SOURCE from '../../api/_lib/markets.py?raw';

export type Currency = 'eur' | 'aud' | 'huf';
export type Market = string;

/** A market's prices in Stripe's smallest unit (cents; for HUF the forint x 100), in the server's names. */
export interface PriceList { one_eye_studio_black: number; one_eye_art: number; two_eyes: number; each_further_eye: number }

export interface MarketDef {
  currency: Currency;
  prices: PriceList;
  selectable: number;
  lang: string;
  stripe_locale: Record<string, string>;
  countries: string[];
}

export const CURRENCIES: readonly Currency[] = ['eur', 'aud', 'huf'];
export const PRICE_KEYS: readonly (keyof PriceList)[] = ['one_eye_studio_black', 'one_eye_art', 'two_eyes', 'each_further_eye'];
export const MAX_EYES = 8;

/** The DEFAULT_MARKET and MARKETS of api/_lib/markets.py's text (the MARKETS literal is plain JSON and ends the file).
 *  scripts/check_prices.mjs parses it the same way and the build compares the two. */
export function parseMarketsSource(src: string): { defaultMarket: Market; markets: Record<Market, MarketDef> } {
  const d = /^DEFAULT_MARKET = "([a-z]{2,8})"\s*$/m.exec(src);
  const at = src.search(/^MARKETS = \{/m);
  if (!d || at < 0) throw new Error('api/_lib/markets.py: DEFAULT_MARKET or MARKETS not found');
  const markets = JSON.parse(src.slice(at + 'MARKETS = '.length)) as Record<Market, MarketDef>;
  return { defaultMarket: d[1], markets };
}

const PARSED = parseMarketsSource(MARKETS_SOURCE);
export const DEFAULT_MARKET: Market = PARSED.defaultMarket;
export const MARKETS: Readonly<Record<Market, MarketDef>> = PARSED.markets;
/** The markets the site offers, in the order of the file. */
export const SELECTABLE: readonly Market[] = Object.keys(MARKETS).filter((m) => MARKETS[m].selectable === 1);

export const isMarket = (v: unknown): v is Market => typeof v === 'string' && Object.prototype.hasOwnProperty.call(MARKETS, v);
export const isSelectable = (v: unknown): v is Market => isMarket(v) && MARKETS[v].selectable === 1;
export const currencyOf = (m: Market): Currency => (isMarket(m) ? MARKETS[m] : MARKETS[DEFAULT_MARKET]).currency;
/** A currency as an API reply names it ("EUR", "aud", ...), or the default market's when it names none we know. */
export const asCurrency = (v: unknown): Currency => {
  const c = typeof v === 'string' ? v.toLowerCase() : '';
  return (CURRENCIES as readonly string[]).includes(c) ? (c as Currency) : currencyOf(DEFAULT_MARKET);
};

/** A market's four prices (the default market's for an unknown key). */
export function priceList(m: Market): PriceList {
  return { ...(isMarket(m) ? MARKETS[m] : MARKETS[DEFAULT_MARKET]).prices };
}

/** The price of n eyes in a style (api/_lib/pay.py price_cents, the same rule): one eye by its style, two eyes the
 *  Couple Duo, every further eye the same amount. list: the server's own price list when it sent one. */
export function priceMinor(n: number, style: string, m: Market, list?: Partial<PriceList>): number {
  const p = priceList(m);
  for (const k of PRICE_KEYS) {
    const v = list?.[k];
    if (typeof v === 'number' && Number.isInteger(v) && v > 0) p[k] = v;
  }
  const eyes = Math.max(1, Math.min(Math.floor(n), MAX_EYES));
  if (eyes <= 1) return style === 'studio_black' ? p.one_eye_studio_black : p.one_eye_art;
  return p.two_eyes + (eyes - 2) * p.each_further_eye;
}

/** GET /api/checkout's price list for a market (its "markets" map; for the default market also its top-level
 *  "prices", as servers from before markets answer), or undefined when it sent none for it. */
export function serverPrices(info: { prices?: Partial<PriceList>; markets?: Record<string, { prices?: Partial<PriceList> } | undefined> } | null | undefined, m: Market): Partial<PriceList> | undefined {
  const own = info?.markets?.[m]?.prices;
  if (own && typeof own === 'object') return own;
  return m === DEFAULT_MARKET ? info?.prices : undefined;
}

// ---------------------------------------------------------------------------------------------------- money

const NBSP = ' ';
const EUR_FMT: Record<'en' | 'de', Intl.NumberFormat> = {
  en: new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR' }),
  de: new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }),
};

function grouped(n: number, sep: string): string {
  return String(Math.abs(Math.round(n))).replace(/\B(?=(\d{3})+(?!\d))/g, sep);
}

/** A price as the site writes it, from Stripe's smallest unit (api/_lib/pay.py price_text is the same rule for the
 *  emails): euros "€19.97" in English, "19,97 €" in German, Lithuanian and Hungarian (a decimal comma and a no-break
 *  space before the sign; Lithuanian and Hungarian are written by hand, never by Intl, whose hu-HU prints
 *  "19,97 EUR"); Australian dollars "A$39" (whole dollars without decimals, never a bare "$"); forints "6 990 Ft"
 *  (whole forints, Stripe's amount / 100, no-break spaces, in every language). */
export function money(minor: number, currency: Currency | string, lang: string = 'en'): string {
  const cur = asCurrency(currency);
  const de = lang === 'de';
  if (cur === 'huf') return `${grouped(minor / 100, NBSP)}${NBSP}Ft`;
  if (cur === 'aud') {
    const whole = minor % 100 === 0;
    const units = Math.floor(Math.abs(minor) / 100);
    const cents = String(Math.abs(minor) % 100).padStart(2, '0');
    return `A$${grouped(units, de ? '.' : ',')}${whole ? '' : `${de ? ',' : '.'}${cents}`}`;
  }
  if (lang === 'lt' || lang === 'hu') {
    const units = Math.floor(Math.abs(minor) / 100);
    const cents = String(Math.abs(minor) % 100).padStart(2, '0');
    return `${minor < 0 ? '-' : ''}${grouped(units, NBSP)},${cents}${NBSP}€`;
  }
  return EUR_FMT[de ? 'de' : 'en'].format(minor / 100);
}

// ---------------------------------------------------------------------------------------------------- the visitor's market

const STORE_KEY = 'snapeyes.market';

/** A market key as a link may spell it (?m=AU, ?m=au%20): trimmed and in lower case. The server takes only the exact
 *  key; the page sends the key it read this way. */
const normalMarket = (v: string | null): string | null => (typeof v === 'string' ? v.trim().toLowerCase() : null);

/** The market this page shows: ?m= when it names a market the site offers (then also remembered), else the visitor's
 *  earlier choice, else the default. Never the IP address. */
export function detectMarket(): Market {
  try {
    const q = normalMarket(new URLSearchParams(window.location.search).get('m'));
    if (isSelectable(q)) {
      remember(q);
      return q;
    }
  } catch { /* no URL access: fall through */ }
  try {
    const s = window.localStorage.getItem(STORE_KEY);
    if (isSelectable(s)) return s;
  } catch { /* storage blocked: fall through */ }
  return DEFAULT_MARKET;
}

function remember(m: Market): void {
  try {
    if (m === DEFAULT_MARKET) window.localStorage.removeItem(STORE_KEY);
    else window.localStorage.setItem(STORE_KEY, m);
  } catch { /* per-visitor convenience only */ }
}

let current: Market | null = null;
const listeners = new Set<() => void>();

/** The page's market (detected once; the default market where there is no browser, as in the build). */
export function currentMarket(): Market {
  if (current === null) current = typeof window !== 'undefined' ? detectMarket() : DEFAULT_MARKET;
  return current;
}

/** The visitor chose a market (the landing page's currency switch): remember it and put it in the address, as the
 *  language switch does with ?lang=. */
export function setMarket(m: Market): void {
  if (!isSelectable(m) || m === currentMarket()) return;
  current = m;
  if (typeof window !== 'undefined') {
    remember(m);
    try {
      const url = new URL(window.location.href);
      if (m === DEFAULT_MARKET) url.searchParams.delete('m');
      else url.searchParams.set('m', m);
      window.history.replaceState(null, '', url);
    } catch { /* keep the page working without history access */ }
  }
  listeners.forEach((l) => l());
}

/** The order page learned its order's market from the server (its status, or the withdrawal answer): its links follow
 *  that market (nothing is stored). Any market of api/_lib/markets.py, also one the site no longer sells in: an order
 *  keeps the legal texts it was made under (src/shared/legal.ts legalHref). */
export function adoptMarket(m: unknown): void {
  if (!isMarket(m) || m === currentMarket()) return;
  current = m;
  listeners.forEach((l) => l());
}

/** The market this page's own link names (?m=), whether or not the site sells in it today, or null. Only for what a
 *  link must keep showing: the legal texts an order was made under (src/legal/LegalApp.tsx), also after the owner
 *  paused that market ("selectable": 0). Prices and checkout follow detectMarket, never this. */
export function linkMarket(): Market | null {
  try {
    const q = normalMarket(new URLSearchParams(window.location.search).get('m'));
    return isMarket(q) ? q : null;
  } catch {
    return null;
  }
}

/** The market the server's country hint (GET /api/checkout "suggest", from Vercel's x-vercel-ip-country) may OFFER
 *  this visitor (src/landing/MarketHint.tsx), or null. Only a market the site sells in, in another currency than the
 *  page shows; only while the page shows the default market that no link named and the visitor never chose (nothing
 *  under "snapeyes.market"); so never again once the visitor took it (setMarket) or declined it (declineHint). Never
 *  applied by itself: only the visitor's click changes the market. */
export function hintMarket(suggest: unknown, market: Market = currentMarket()): Market | null {
  if (typeof suggest !== 'string' || !isSelectable(suggest) || market !== DEFAULT_MARKET) return null;
  if (currencyOf(suggest) === currencyOf(market)) return null;
  try {
    if (new URLSearchParams(window.location.search).get('m') !== null) return null;
  } catch { /* no URL access: fall through */ }
  try {
    if (window.localStorage.getItem(STORE_KEY) !== null) return null;
  } catch { /* storage blocked: the offer still shows; closing it lasts this page view */ }
  return suggest;
}

/** The visitor closed the offer of another currency: remembered as their choice of the default market (the same
 *  "snapeyes.market" the currency switch uses), so it is not offered again. */
export function declineHint(): void {
  try {
    window.localStorage.setItem(STORE_KEY, DEFAULT_MARKET);
  } catch { /* per-visitor convenience only */ }
}

export function subscribeMarket(fn: () => void): () => void {
  listeners.add(fn);
  return () => { listeners.delete(fn); };
}

/** An internal link with the page's market in it (m=), before any #section; the default market's links are left as
 *  they are. */
export function withMarket(href: string, m: Market = currentMarket()): string {
  if (!isSelectable(m) || m === DEFAULT_MARKET) return href;
  const hash = href.indexOf('#');
  const path = hash < 0 ? href : href.slice(0, hash);
  const frag = hash < 0 ? '' : href.slice(hash);
  return `${path}${path.includes('?') ? '&' : '?'}m=${m}${frag}`;
}
