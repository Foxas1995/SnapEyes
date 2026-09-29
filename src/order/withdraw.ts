// The online withdrawal function of the /order page (Art. 11a Directive 2011/83/EU as amended by Directive (EU)
// 2023/2673, in force since 19 June 2026; § 356a BGB): the customer gives their name, the order and an email address
// for the receipt, confirms, and the server (api/_lib/withdraw.py, POST /api/order {action: "withdraw"}) records the
// statement with the time it arrived, stops the order if nothing was made yet and emails the receipt. The server
// alone decides whether the withdrawal takes effect (the right ends once making has started, see
// src/legal/docs/withdrawal.ts); this module only sends the statement and reads the answer. No React here.
import { callApi, ORDER_RE, KEY_RE, type ApiReply } from './api';
import type { Lang } from '../try/lang';

export interface WithdrawInput {
  order: string;
  k: string | null;    // the order's key from the link; null when the customer typed the order number
  name: string;
  email: string;
  lang: Lang;
  nonce: string;       // one per form: a statement sent again after a lost answer is the same statement, not a second
}

/** How the receipt email went: sent; to be sent again later (the provider was busy); refused (a bad address);
 *  null: the server said nothing about it, or sends none on this deployment. */
export type ReceiptMail = 'sent' | 'later' | 'failed' | null;

/** What the server made of the statement. */
export interface WithdrawDone {
  // true: the contract is withdrawn (nothing is made, the payment is refunded); false: the right had already ended;
  // null: recorded, and the owner checks the order by hand
  effective: boolean | null;
  reason: string | null;          // the server's why: nothing_made, making_began, period_over, payment_settling, ...
  at: number | null;              // when the statement arrived (unix seconds), as the server recorded it
  mail: ReceiptMail;
  refundStarted: boolean;         // the refund is already under way at the payment provider
  refundBy: number | null;        // the refund is due by then (unix seconds)
  amount: number | null;          // euro cents paid, when the server named them
  already: boolean;               // the same statement (or the order's withdrawal) was on record before
}

export type WithdrawError = 'network' | 'busy' | 'unmatched' | 'not_paid' | 'invalid' | 'paused' | 'too_many' | 'failed';

export type WithdrawOutcome = { kind: 'done'; done: WithdrawDone } | { kind: 'error'; code: WithdrawError; at: number | null };

export const NAME_MAX = 100;
export const EMAIL_MAX = 254;

// api/_lib/pay.py _EMAIL, the server's own check, so the page never sends what the server refuses nor refuses what
// it takes
const EMAIL_RE = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$/;

export const emailOk = (s: string) => s.length <= EMAIL_MAX && EMAIL_RE.test(s);
export const nameOk = (s: string) => s.length >= 1 && s.length <= NAME_MAX;
/** An order number as typed: spaces and a leading "#" dropped, lower case (the ids are lower case). */
export const cleanOrder = (s: string) => s.replace(/\s+/g, '').replace(/^#/, '').toLowerCase();
export const orderOk = (s: string) => ORDER_RE.test(s);

/** A fresh statement nonce (api/_lib/withdraw.py NONCE_RE: 8 to 64 of [A-Za-z0-9_-]). */
export function newNonce(): string {
  try {
    const b = new Uint8Array(12);
    crypto.getRandomValues(b);
    return Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
  } catch {
    return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`.replace(/[^a-z0-9]/g, '').padEnd(8, '0');
  }
}

/** The address of the withdrawal form: the order page in its withdrawal mode, which never starts making anything.
 *  Without an order (src/shared/legal.ts withdrawFunctionHref, from the footers) the customer types the order number. */
export function withdrawHref(lang: Lang, link?: { o: string; k: string } | null): string {
  const q = new URLSearchParams();
  if (link && ORDER_RE.test(link.o) && KEY_RE.test(link.k)) { q.set('o', link.o); q.set('k', link.k); }
  q.set('withdraw', '1');
  if (lang === 'de') q.set('lang', 'de');
  return `/order?${q.toString()}`;
}

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) && v > 0 ? v : null);
const obj = (v: unknown): Record<string, unknown> | null => (v && typeof v === 'object' && !Array.isArray(v) ? v as Record<string, unknown> : null);
const isoSeconds = (v: unknown): number | null => {
  if (typeof v !== 'string') return num(v);
  const t = Date.parse(v);
  return Number.isFinite(t) ? Math.floor(t / 1000) : null;
};

function receipt(v: unknown): ReceiptMail {
  if (v === 'sent' || v === true) return 'sent';
  if (v === 'pending' || v === 'retry') return 'later';
  if (v === 'not_sent' || v === 'failed' || v === 'bad_address' || v === false) return 'failed';
  return null;   // "off" (no email on this deployment) or nothing said
}

/** The server's record of a withdrawal: a withdraw reply's "withdrawal", or a status reply's "withdrawal" object. */
export function readWithdrawal(v: unknown): WithdrawDone | null {
  const w = obj(v);
  if (!w) return null;
  const effective = w.effective === true || w.state === 'withdrawn';
  const lapsed = !effective && (w.effective === false || w.state === 'lapsed');
  const checking = !effective && !lapsed && (w.state === 'review' || w.state === 'received');
  if (!effective && !lapsed && !checking) return null;
  return {
    effective: effective ? true : lapsed ? false : null,
    reason: typeof w.reason === 'string' ? w.reason : null,
    at: num(w.at) ?? isoSeconds(w.received) ?? num(w.received_at),
    mail: receipt(w.mail),
    refundStarted: w.refund === 'started' || w.refund === 'refunded',
    refundBy: isoSeconds(w.refund_by),
    amount: num(w.amount),
    already: w.already === true,
  };
}

function failure(r: ApiReply<unknown>): WithdrawError {
  if (r.status === 0 || (r.status >= 500 && !r.data)) return 'network';
  if (r.reason === 'withdraw_paused') return 'paused';
  if (r.reason === 'too_many' || r.status === 429) return 'too_many';
  if (r.reason === 'storage_busy' || r.reason === 'payments_busy' || r.status === 503) return 'busy';
  if (r.reason === 'not_found' || r.status === 404) return 'unmatched';
  if (r.reason === 'not_paid' || r.reason === 'no_contract') return 'not_paid';
  if (r.status === 400) return 'invalid';
  return 'failed';
}

/** Send the statement: POST /api/order {action: "withdraw", order, k?, name, email, lang, nonce}. Never throws. */
export async function sendWithdrawal(inp: WithdrawInput, api: typeof callApi = callApi): Promise<WithdrawOutcome> {
  const body: Record<string, unknown> = { action: 'withdraw', order: inp.order, name: inp.name, email: inp.email, lang: inp.lang, nonce: inp.nonce };
  if (inp.k) body.k = inp.k;
  const r = await api<Record<string, unknown>>('/api/order', { body, timeoutMs: 45_000 });
  if (r.ok && r.data) {
    const done = readWithdrawal(r.data.withdrawal);
    if (done) return { kind: 'done', done };
    return { kind: 'error', code: 'failed', at: null };
  }
  // a refusal the server still recorded (an order it could not match) names the time the statement arrived
  const rec = obj(r.data?.withdrawal);
  return { kind: 'error', code: failure(r), at: rec ? num(rec.at) : null };
}
