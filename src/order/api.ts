// The payments API client (api/order.py, api/checkout.py, api/health.py), shared by the buy card on /try and the
// /order page. A call never throws for an HTTP answer: it resolves to an ApiReply, so the callers branch on the status
// and the server's reason code (the work notes' API.md lists them all). Nothing here talks to a third party or writes
// to the browser.

import type { PriceList } from '../shared/markets';

export interface ApiReply<T> {
  ok: boolean;          // HTTP 2xx and the body did not say ok: false
  status: number;       // the HTTP status; 0 = no answer at all (offline, or our own time limit)
  data: T | null;       // the JSON body; null when the platform answered with text (a Vercel timeout, a 413)
  reason: string;       // the server's reason code, '' when it gave none
  error: string;        // the server's own sentence (always English), '' when none
  retry: boolean;       // the server says the same request can succeed later
  retryAfter: number;   // seconds the server asks us to wait, 0 when it named none
}

const str = (v: unknown): string => (typeof v === 'string' ? v : '');
const num = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) && v > 0 ? v : 0);

/** GET (no body) or POST JSON to one of our own endpoints, within timeoutMs. */
export async function callApi<T>(path: string, opts: { body?: Record<string, unknown>; timeoutMs?: number } = {}): Promise<ApiReply<T>> {
  const ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = ctrl ? setTimeout(() => ctrl.abort(), opts.timeoutMs ?? 20_000) : null;
  try {
    const post = opts.body !== undefined;
    const r = await fetch(path, {
      method: post ? 'POST' : 'GET',
      headers: post ? { 'Content-Type': 'application/json', Accept: 'application/json' } : { Accept: 'application/json' },
      body: post ? JSON.stringify(opts.body) : undefined,
      cache: 'no-store',
      credentials: 'same-origin',
      signal: ctrl?.signal,
    });
    // Vercel answers a timeout or an oversized body with text: read text first, so the status is never lost
    const raw = await r.text();
    let j: unknown = null;
    try { j = JSON.parse(raw); } catch { /* the platform's own answer */ }
    const o = j && typeof j === 'object' && !Array.isArray(j) ? (j as Record<string, unknown>) : null;
    const header = Number(r.headers.get('Retry-After') || 0);
    return {
      ok: r.ok && !!o && o.ok !== false,
      status: r.status,
      data: o as T | null,
      reason: str(o?.reason),
      error: str(o?.error),
      retry: o?.retry === true,
      retryAfter: num(o?.retry_after) || num(header),
    };
  } catch {
    return { ok: false, status: 0, data: null, reason: '', error: '', retry: true, retryAfter: 0 };
  } finally {
    if (timer) clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------------------------------- replies

/** GET /api/health: which pieces this deployment has (booleans only). */
export interface Health { stripe?: boolean; stripe_live?: boolean; email?: boolean; blob_store?: boolean }

/** The prices api/_lib/pay.py charges in one market, in Stripe's smallest unit (src/shared/markets.ts). */
export type { PriceList };

/** GET /api/checkout: whether ordering is open here, the price lists and the exact withdrawal-waiver text. currency and
 *  prices: the default market's; markets: every market the site sells in; country and suggest: the visitor's country
 *  (Vercel) and a market the page may offer for it (a hint only, never applied by itself). */
export interface CheckoutInfo {
  open: boolean;
  currency?: string;
  prices?: Partial<PriceList>;
  market?: string;
  markets?: Record<string, { currency?: string; prices?: Partial<PriceList> } | undefined>;
  max_eyes?: number;
  // the waiver text per language (the EU edition), and per market where a market has its own (markets.au: the
  // Australian checkbox, src/shared/legal.ts CHECKOUT_LEGAL_AU)
  consent?: { version?: string; en?: string; de?: string; markets?: Record<string, { en?: string; de?: string } | undefined> };
  country?: string;
  suggest?: string | null;
}

export interface DraftReply { order: string; k: string; eye: number; created: boolean; expires_at: number }
export interface CheckoutReply { url: string; order: string; amount: number; currency: string; market?: string; eyes: number; style: string; expires_at: number; order_url?: string }

// withdrawn: the customer withdrew from the contract before anything was made (./withdraw.ts); nothing is made
export type OrderState = 'unpaid' | 'pending' | 'paid' | 'making' | 'review' | 'ready' | 'deleted' | 'withdrawn';

export interface OrderEye { eye: number; made?: boolean; uploaded?: boolean; ref?: string | null; preview_url?: string | null }

export interface Download { url: string; download_url: string; expires_in?: number; width?: number | null; height?: number | null; bytes?: number | null }

/** The server's own making of a paid order (api/_lib/maker.py), as the status of a "paid" or "making" order says it:
 *  while `active`, the server makes the order without this page (the page only watches), `step` "eye" (with `eye`)
 *  or "compose" when it says what it is doing. */
export interface ServerMaking { active?: boolean; step?: string | null; eye?: number | null }

/** GET /api/order (or action "status" / "compose"): one order as the server sees it. */
export interface OrderStatus {
  order: string;
  state: OrderState;
  lang?: string;
  eyes: OrderEye[];
  // paid orders
  count?: number;
  style?: string;
  layout?: string;
  names?: string;
  title?: string;
  amount?: number | null;
  // the currency the order was paid (or is priced) in ("EUR", "AUD", "HUF") and its market (src/shared/markets.ts)
  currency?: string;
  market?: string;
  download?: Download;
  // unpaid orders
  expires_at?: number;
  expired?: boolean;
  payments?: boolean;
  checkout?: { eyes?: number; style?: string; amount?: number; currency?: string; market?: string };
  payment_check?: string;
  // "pending" of a paid order: what it waits for ("confirmation_email": the order confirmation has not gone out yet)
  waiting_for?: string;
  // the withdrawal the server recorded for this order, if any (./withdraw.ts readWithdrawal reads it)
  withdrawal?: unknown;
  // "paid" or "making": whether the server is making it by itself right now (./driver.ts then only watches)
  server?: ServerMaking;
}

export const ORDER_STATES: readonly OrderState[] = ['unpaid', 'pending', 'paid', 'making', 'review', 'ready', 'deleted', 'withdrawn'];

/** A status reply we can act on: a known state and a list of eyes. */
export function isStatus(d: unknown): d is OrderStatus {
  const o = d as OrderStatus | null;
  return !!o && typeof o === 'object' && typeof o.order === 'string' && ORDER_STATES.includes(o.state) && Array.isArray(o.eyes);
}

// ---------------------------------------------------------------------------------------------------- orders

/** An order id and access key as the server accepts them (api/_lib/store.py ORDER_RE, api/_lib/pay.py KEY_RE). */
export const ORDER_RE = /^[a-z0-9][a-z0-9-]{3,63}$/;
export const KEY_RE = /^[a-f0-9]{32}$/;
export const SESSION_RE = /^cs_(test|live)_[A-Za-z0-9]{8,240}$/;

export function statusPath(order: string, k: string, s?: string | null, previews = false): string {
  const q = new URLSearchParams({ o: order, k });
  if (s) q.set('s', s);
  if (previews) q.set('p', '1');
  return `/api/order?${q.toString()}`;
}

/** The order page of an order, in the page's language (the address the Stripe success page and the emails use). */
export function orderPageUrl(order: string, k: string, lang: 'en' | 'de'): string {
  const q = new URLSearchParams({ o: order, k });
  if (lang === 'de') q.set('lang', 'de');
  return `/order?${q.toString()}`;
}
