// A print of the artwork, bought AFTER the artwork (api/_lib/prints.py, the add-on): what the order page does with the offer the status
// reply carries (print_offer), the request that opens Stripe's payment page of the print, and the watch after the way back from it (the
// page asks until the print is on record, as the gift page asks about its voucher: Stripe's webhook may not have arrived yet). No React
// here: ./PrintOffer.tsx draws it, suites/ts/print_offer.test.ts drives it with a fake server.
import { callApi, type ApiReply, type OrderPrint, type OrderStatus } from './api';
import { offeredPrints, type OfferedPrint, type ServerPrints } from '../shared/prints';
import type { Lang } from '../shared/lang';

/** The status reply's print_offer: the prints with the prices and the shipping the server would charge (euro cents), and the exact text of
 *  the print box per language. Present only while this order can buy a print (delivered, no print yet, the owner's switch on). */
export interface PrintOfferReply {
  currency?: string;
  products?: ServerPrints['products'];
  consent?: Partial<Record<Lang, string>>;
}

/** The prints the order page offers: the server's list, each one the page knows and well formed (src/shared/prints.ts offeredPrints holds
 *  the rule); none without an offer. The server has decided that this order's market offers prints, so the page asks no second time. */
export function offerPrints(st: Pick<OrderStatus, 'print_offer'> | null | undefined): OfferedPrint[] {
  const o = st?.print_offer;
  if (!o || !Array.isArray(o.products)) return [];
  return offeredPrints({ on: true, markets: ['order'], products: o.products }, 'order');
}

/** Where the order page is after Stripe's page of a print: nothing to say (null), the payment is being confirmed (checking), it takes long
 *  (slow: the page stops asking; the e-mail and the next visit show the print), a method that settles later (processing), the payment page
 *  had expired, the order had a print already (extra: the owner refunds this payment), it is on record (done), or the customer came back
 *  without paying (cancelled, Stripe's back link). */
export type PrintBack = 'checking' | 'slow' | 'processing' | 'expired' | 'extra' | 'done' | 'cancelled' | null;

/** While one of these shows, the offer card stays away: a payment is on its way or on record, and a second one must not be invited. */
export const PRINT_BUSY: readonly PrintBack[] = ['checking', 'slow', 'processing', 'done', 'extra'];

export function printCheckPath(order: string, k: string, ps: string): string {
  return `/api/checkout?${new URLSearchParams({ addon: ps, o: order, k }).toString()}`;
}

interface PrintCheck { state?: string; print?: OrderPrint; amount?: number; currency?: string }
/** What the print's own payment was, as the paid answer says it (for the Meta pixel's Purchase, src/shared/metaPixel.ts). */
export interface PrintPaid { amount: number; currency: string }
const isPrint = (p: unknown): p is OrderPrint => !!p && typeof p === 'object' && typeof (p as OrderPrint).product === 'string' && typeof (p as OrderPrint).state === 'string';

export interface WatchDeps { api: typeof callApi; sleep: (ms: number) => Promise<void> }
export const WATCH_TRIES = 20;        // about a minute, as the gift page waits for its voucher
export const WATCH_EVERY = 3_000;
export const WATCH_SETTLING = 15_000; // a payment that settles later is asked about less often

/** Ask about the print's payment until it is on record (emit 'done' or 'extra' with the print block), expired, or not this order's
 *  (emit null), at most `tries` times; then 'slow' (or 'processing' when the method settles later). A dropped connection is simply asked
 *  again. alive() turns false when the page no longer wants answers. */
export async function watchPrint(link: { o: string; k: string }, ps: string, deps: WatchDeps, emit: (back: PrintBack, print?: OrderPrint, paid?: PrintPaid) => void,
  alive: () => boolean, tries = WATCH_TRIES): Promise<void> {
  let settling = false;
  for (let i = 0; i < tries && alive(); i++) {
    const r: ApiReply<PrintCheck> = await deps.api<PrintCheck>(printCheckPath(link.o, link.k, ps), { timeoutMs: 25_000 });
    if (!alive()) return;
    const state = r.ok ? r.data?.state : undefined;
    if (state === 'paid' || state === 'extra') {
      const d = r.data;
      const paid = state === 'paid' && typeof d?.amount === 'number' && typeof d.currency === 'string' ? { amount: d.amount, currency: d.currency } : undefined;
      emit(state === 'paid' ? 'done' : 'extra', isPrint(d?.print) ? d.print : undefined, ...(paid ? [paid] : []));
      return;
    }
    if (state === 'expired') { emit('expired'); return; }
    // not a print payment of this order (or a link that does not fit): nothing to wait for, the page is the page it would be without ps
    if (state === 'unknown' || r.status === 400 || r.status === 403) { emit(null); return; }
    if (state === 'processing' && !settling) { settling = true; emit('processing'); }
    await deps.sleep(settling ? WATCH_SETTLING : WATCH_EVERY);
  }
  if (alive() && !settling) emit('slow');
}

/** How a press on the offer's button ended: Stripe's page, or why not. changed: the price or the shipping is not the one shown (nothing was
 *  created; the page reads the offer again). has: the order has a print already (another tab bought it). unavailable: prints cannot be
 *  bought for this order now (the switch went off, the order was refunded). */
export type BuyPrintOutcome = { kind: 'redirect'; url: string } | { kind: 'error'; code: 'changed' | 'has' | 'unavailable' | 'network' | 'busy' | 'failed' };

/** POST /api/checkout {addon}: the payment page of this print for this order. shown: the print and its shipping as the card showed them
 *  (the server only compares it). The box is ticked: the button is shut until it is. */
export async function buyPrint(link: { o: string; k: string }, print: { product: string; country: string }, lang: Lang, shown: number,
  api: typeof callApi = callApi): Promise<BuyPrintOutcome> {
  const r = await api<{ url?: string; why?: string }>('/api/checkout', {
    body: { addon: { order: link.o, key: link.k }, print, consent_print: true, print_shown: shown, lang }, timeoutMs: 30_000,
  });
  if (r.ok && typeof r.data?.url === 'string' && r.data.url.startsWith('https://')) return { kind: 'redirect', url: r.data.url };
  if (r.reason === 'print_price_changed') return { kind: 'error', code: 'changed' };
  if (r.reason === 'print_not_offered' && r.data?.why === 'has_print') return { kind: 'error', code: 'has' };
  if (r.reason === 'print_not_offered' || r.reason === 'print_unavailable') return { kind: 'error', code: 'unavailable' };
  if (r.status === 0) return { kind: 'error', code: 'network' };
  if (r.reason === 'payments_busy' || r.reason === 'storage_busy') return { kind: 'error', code: 'busy' };
  return { kind: 'error', code: 'failed' };
}

/** The country to preselect for a print: the order's own market names one (lt: Lithuania, hr: Croatia); the common euro market does not. */
export function marketCountry(market: string | undefined): string | null {
  return market === 'lt' ? 'LT' : market === 'hr' ? 'HR' : null;
}
