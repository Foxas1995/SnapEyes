// The prints of the artwork (an option of an order on the euro markets of the EU edition): the offer, the shipping per country and their
// words, shared by /try, the order page, the terms and the admin panel. Plain data and functions only, no React.
//
// THE ONE PLACE for a print's retail price is api/_lib/print_offer.py, what a print costs us is api/_lib/print_rates.py (written by
// scripts/print_rates.py from the merchOne API) and the words of the products and countries are api/_lib/print_names.py: this module reads
// those three files as text at build time and parses their literals as JSON, as src/shared/markets.ts reads the markets. The server stays
// the authority: it prices every print itself (api/_lib/prints.py), and GET /api/checkout says whether prints can be bought now (the owner's
// switch) with the server's own prices and shipping; the page prefers those.
import OFFER_SOURCE from '../../api/_lib/print_offer.py?raw';
import RATES_SOURCE from '../../api/_lib/print_rates.py?raw';
import NAMES_SOURCE from '../../api/_lib/print_names.py?raw';
import type { Lang } from './lang';

export type PrintKind = 'acrylic' | 'canvas' | 'poster';
export interface PrintProduct { id: string; kind: PrintKind; cm: number; sku: string; price: number; on: number }
export interface PrintOffer { currency: string; markets: string[]; vat_pct: number; fee_pct: number; margin_floor: number; products: PrintProduct[] }
export interface SkuRate { cost: number; blueprint: number; variant: number; design_mm: number[]; design_px: number[]; file_mm: number[]; file_px: number[]; trim_mm: number; dpi: number }
export interface PrintRates { fetched: string; skus: Record<string, SkuRate>; shipping: Record<string, Record<string, number>> }
type Words = Record<Lang, string>;
export interface PrintNames { kinds: Record<PrintKind, Words>; countries: Record<string, Words> }

/** The literal NAME = { ... } that ends a Python file of this kind (plain JSON; scripts/check_prices.mjs reads it the same way). */
export function parseLiteral<T>(src: string, name: string): T {
  const at = src.search(new RegExp(`^${name} = \\{`, 'm'));
  if (at < 0) throw new Error(`${name} not found`);
  return JSON.parse(src.slice(at + name.length + 3)) as T;
}

export const PRINT_OFFER: Readonly<PrintOffer> = parseLiteral<PrintOffer>(OFFER_SOURCE, 'PRINT_OFFER');
export const PRINT_RATES: Readonly<PrintRates> = parseLiteral<PrintRates>(RATES_SOURCE, 'PRINT_RATES');
export const PRINT_NAMES: Readonly<PrintNames> = parseLiteral<PrintNames>(NAMES_SOURCE, 'PRINT_NAMES');

/** The prints of the offer, in its order (offered: only the ones with on 1). */
export const printProducts = (offered = true): PrintProduct[] => PRINT_OFFER.products.filter((p) => !offered || p.on === 1);
export const printProduct = (id: unknown, offered = false): PrintProduct | undefined =>
  printProducts(offered).find((p) => p.id === id);

/** The countries prints ship to, by code. */
export const printCountries = (): string[] => Object.keys(PRINT_RATES.shipping).sort();

/** cents x (100 + vat_pct) / 100, rounded up to the cent (api/_lib/prints.py with_vat). */
export const withVat = (cents: number, vat = PRINT_OFFER.vat_pct): number => Math.ceil((cents * (100 + vat)) / 100 - 1e-9);

/** What the customer pays for shipping: the cost with VAT, rounded UP to the next amount ending in .49 or .99 (api/_lib/prints.py ship_price,
 *  the same rule; scripts/check_prices.mjs compares them for every country and print). */
export function shipPrice(cost: number, vat = PRINT_OFFER.vat_pct): number {
  const c = withVat(cost, vat);
  for (let v = c; v < c + 100; v++) if (v % 100 === 49 || v % 100 === 99) return v;
  return c;
}

/** The shipping of a print to a country from the build's table (cents), or null when it does not ship there. */
export function printShipping(country: string, id: string): number | null {
  const p = printProduct(id);
  const cost = p ? PRINT_RATES.shipping[country]?.[p.sku] : undefined;
  return typeof cost === 'number' ? shipPrice(cost) : null;
}

/** What a print earns (cents): api/_lib/prints.py margin, restated. */
export function printMargin(id: string, country: string, offer: PrintOffer = PRINT_OFFER, rates: PrintRates = PRINT_RATES): number | null {
  const p = offer.products.find((x) => x.id === id);
  const s = p ? rates.skus[p.sku] : undefined;
  const sc = p ? rates.shipping[country]?.[p.sku] : undefined;
  if (!p || !s || typeof sc !== 'number') return null;
  const paid = p.price + shipPrice(sc, offer.vat_pct);
  return paid - withVat(s.cost + sc, offer.vat_pct) - Math.ceil((paid * offer.fee_pct) / 100 - 1e-9);
}

const NBSP = ' ';
export const printSize = (cm: number): string => `${cm}${NBSP}×${NBSP}${cm}${NBSP}cm`;
const lng = (lang: string): Lang => (['en', 'de', 'lt', 'hu', 'hr'].includes(lang) ? lang : 'en') as Lang;

/** "Acrylic glass print 40 × 40 cm" in a language (api/_lib/prints.py product_name). */
export function printName(id: string, lang: string): string {
  const p = printProduct(id);
  return p ? `${PRINT_NAMES.kinds[p.kind][lng(lang)]} ${printSize(p.cm)}` : id;
}

export const kindName = (kind: PrintKind, lang: string): string => PRINT_NAMES.kinds[kind]?.[lng(lang)] ?? kind;
export const countryName = (cc: string, lang: string): string => PRINT_NAMES.countries[cc]?.[lng(lang)] ?? cc;

/** The countries sorted by their name in a language (the checkout's list). */
export function countriesByName(lang: string, list: string[] = printCountries()): string[] {
  const coll = new Intl.Collator(lng(lang));
  return [...list].sort((a, b) => coll.compare(countryName(a, lang), countryName(b, lang)));
}

// ---------------------------------------------------------------------------------------------------- the server's answer

/** GET /api/checkout prints (absent while prints cannot be bought). */
export interface ServerPrints {
  on: boolean; currency?: string; markets?: string[];
  products?: { id: string; kind: PrintKind; cm: number; price: number; ship: Record<string, number | null> }[];
}

/** The prints a page of this market may offer: the server's list when it says prints are on in this market, else none. Each with the server's
 *  own price and its shipping per country (the build's table only where the server sent nothing for a country). */
export interface OfferedPrint { id: string; kind: PrintKind; cm: number; price: number; ship: Record<string, number> }
export function offeredPrints(server: ServerPrints | null | undefined, market: string): OfferedPrint[] {
  if (!server || server.on !== true || !Array.isArray(server.products) || !(server.markets ?? []).includes(market)) return [];
  const out: OfferedPrint[] = [];
  for (const p of server.products) {
    const mine = printProduct(p.id);
    if (!mine || typeof p.price !== 'number' || !Number.isInteger(p.price) || p.price <= 0) continue;
    const ship: Record<string, number> = {};
    for (const [cc, v] of Object.entries(p.ship ?? {})) if (typeof v === 'number' && Number.isInteger(v) && v > 0) ship[cc] = v;
    if (!Object.keys(ship).length) continue;
    out.push({ id: p.id, kind: mine.kind, cm: mine.cm, price: p.price, ship });
  }
  return out;
}

/** The country to preselect: the visitor's country when prints ship there (GET /api/checkout country), else none (the customer picks). */
export function defaultCountry(hint: string | null | undefined, ship: Record<string, number>): string {
  const cc = typeof hint === 'string' ? hint.toUpperCase() : '';
  return cc && ship[cc] ? cc : '';
}
