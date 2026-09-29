// Buying the artwork from /try: the order's drafts (api/order.py) and the Stripe checkout (api/checkout.py), plus
// what this tab keeps in sessionStorage for the way back from Stripe's page. No React here.
//
// Nothing is uploaded before the customer taps Buy: the privacy policy says the iris crop and the approved preview
// are kept only once an order is started (src/legal/docs/privacy.ts). The server accepts an eye's draft only with the
// work ticket /api/analyze gave its photo, and that ticket lives 15 minutes, so an eye taken earlier than that and
// not yet uploaded has to be taken again before it can be ordered.
import { callApi, isStatus, orderPageUrl, statusPath, type ApiReply, type CheckoutReply, type DraftReply } from '../order/api';
import type { Eye, Layout } from './multi';
import type { Lang } from './lang';

/** api/_lib/iris.py TICKET_TTL: a work ticket from /api/analyze is good for 15 minutes. */
export const TICKET_MS = 900_000;
/** Uploading takes a moment: a ticket this close to its end already counts as too old. */
export const TICKET_MARGIN_MS = 45_000;
/** api/_lib/pay.py SESSION_MIN is 32 minutes of draft life left; an order with less than this starts afresh. */
const ORDER_FRESH_MS = 40 * 60_000;

/** The order this tab is building. eyes: the ids of the eyes the order holds (as far as this tab knows); checkout: the
 *  eyes, in canvas order, of the last checkout this tab opened (so a paid artwork is never paid for twice). */
export interface OrderRef { order: string; k: string; expiresAt: number; eyes: string[]; checkout: string[] }

// ---------------------------------------------------------------------------------------------------- storage
// sessionStorage belongs to this tab and is gone when the tab closes. It holds the order number and its key (needed
// again after Stripe's cancel link, which carries no key) and, only while the customer is on Stripe's page, the
// artwork's eyes, so "back" from the payment page finds the artwork as it was.

const ORDER_KEY = 'snapeyes.order';
const SNAP_KEY = 'snapeyes.checkout';

function readJson(key: string): unknown {
  try {
    const s = window.sessionStorage.getItem(key);
    return s ? JSON.parse(s) : null;
  } catch { return null; }
}

function remove(key: string): void {
  try { window.sessionStorage.removeItem(key); } catch { /* storage blocked: nothing kept */ }
}

const strings = (v: unknown): string[] => (Array.isArray(v) ? v.filter((x): x is string => typeof x === 'string') : []);

export function loadOrderRef(): OrderRef | null {
  const o = readJson(ORDER_KEY) as Partial<OrderRef> | null;
  if (!o || typeof o.order !== 'string' || typeof o.k !== 'string' || typeof o.expiresAt !== 'number') return null;
  return { order: o.order, k: o.k, expiresAt: o.expiresAt, eyes: strings(o.eyes), checkout: strings(o.checkout) };
}

export function saveOrderRef(r: OrderRef | null): void {
  if (!r) { remove(ORDER_KEY); return; }
  try { window.sessionStorage.setItem(ORDER_KEY, JSON.stringify(r)); } catch { /* the order then lives in memory only */ }
}

/** One eye as the snapshot keeps it: everything the result screen shows, never the draft (it is uploaded by then). */
export type SnapEye = Omit<Eye, 'draft'>;

export interface Snapshot { v: 1; order: string; at: number; style: string; layoutWant: Layout | null; names: string; eyes: SnapEye[] }

/** Keep the artwork for the way back from Stripe. Returns false when the browser would not hold it. */
export function saveSnapshot(s: Snapshot): boolean {
  try {
    window.sessionStorage.setItem(SNAP_KEY, JSON.stringify(s));
    return true;
  } catch {
    remove(SNAP_KEY);
    return false;
  }
}

/** The kept artwork, read once and removed. order: only the snapshot of that order (the cancel link names it). */
export function takeSnapshot(order: string | null): Snapshot | null {
  const s = readJson(SNAP_KEY) as Snapshot | null;
  remove(SNAP_KEY);
  if (!s || s.v !== 1 || typeof s.order !== 'string' || !Array.isArray(s.eyes) || !s.eyes.length) return null;
  if (order && s.order !== order) return null;
  if (typeof s.at !== 'number' || Date.now() - s.at > 24 * 3600_000) return null;
  const good = s.eyes.every((e) => e && typeof e.id === 'string' && typeof e.image === 'string' && typeof e.thumb === 'string'
    && typeof e.before === 'string' && typeof e.pad === 'number' && !e.sample);
  return good ? s : null;
}

/** The order page calls this once an order is paid: the tab's order and kept artwork are done with. */
export function clearCheckoutStorage(order: string): void {
  const r = loadOrderRef();
  if (r && r.order === order) remove(ORDER_KEY);
  const s = readJson(SNAP_KEY) as Snapshot | null;
  if (s && s.order === order) remove(SNAP_KEY);
}

// ---------------------------------------------------------------------------------------------------- buying

/** The eyes (1-based positions on the artwork) that cannot be ordered as they are: the order does not hold them and
 *  their work ticket is too old (or they never had one). */
export function staleEyes(list: readonly Eye[], ref: OrderRef | null, now: number): number[] {
  const held = new Set(ref && ref.expiresAt * 1000 - now > ORDER_FRESH_MS ? ref.eyes : []);
  return list.flatMap((e, i) => (!held.has(e.id) && !(e.draft && e.draft.until > now) ? [i + 1] : []));
}

export type CheckoutStep = { kind: 'sync' } | { kind: 'upload'; i: number; n: number } | { kind: 'arrange' } | { kind: 'checkout' };

/** paused: the server's daily ceiling on unpaid uploads is reached (draft 503 uploads_paused); too_many: this order had
 *  its 30 uploads of the day (draft 429 too_many_uploads). Both clear the next day (UTC). */
export type CheckoutError = 'network' | 'busy' | 'payments' | 'too_large' | 'paused' | 'too_many' | 'failed';

export type CheckoutOutcome =
  | { kind: 'redirect'; url: string; ref: OrderRef }            // Stripe's payment page
  | { kind: 'paid'; url: string; ref: null }                    // this very artwork is paid already: its order page
  | { kind: 'stale'; eyes: number[]; ref: OrderRef | null }     // these eyes have to be taken again
  | { kind: 'closed'; ref: OrderRef | null }                    // ordering is not open on this deployment
  | { kind: 'error'; code: CheckoutError; ref: OrderRef | null };

export interface CheckoutInput {
  eyes: readonly Eye[];
  style: string;
  layout: Layout;
  names: string;
  lang: Lang;
  ref: OrderRef | null;
}

type Api = typeof callApi;
type Attempt = CheckoutOutcome | { kind: 'restart' } | { kind: 'resync'; ref: OrderRef | null };

const sameList = (a: readonly string[], b: readonly string[]) => a.length > 0 && a.length === b.length && a.every((x, i) => x === b[i]);

function failure(r: ApiReply<unknown>, ref: OrderRef | null): CheckoutOutcome {
  if (r.status === 0 || (r.status >= 500 && !r.data)) return { kind: 'error', code: 'network', ref };
  if (r.reason === 'payments_not_configured' || r.reason === 'storage_not_configured') return { kind: 'closed', ref };
  if (r.reason === 'payments_busy' || r.reason === 'storage_busy') return { kind: 'error', code: 'busy', ref };
  if (r.reason === 'payments_error') return { kind: 'error', code: 'payments', ref };
  if (r.status === 413 || r.reason === 'too_large') return { kind: 'error', code: 'too_large', ref };
  if (r.reason === 'uploads_paused') return { kind: 'error', code: 'paused', ref };
  if (r.reason === 'too_many_uploads' || r.status === 429) return { kind: 'error', code: 'too_many', ref };
  return { kind: 'error', code: 'failed', ref };
}

/** Upload what the order still lacks, put its eyes in canvas order, and open a Stripe checkout for them. Every step
 *  is safe to repeat: each attempt first asks the server what the order holds. */
export async function runCheckout(inp: CheckoutInput, onStep: (s: CheckoutStep) => void, api: Api = callApi): Promise<CheckoutOutcome> {
  let ref = inp.ref ? { ...inp.ref } : null;
  for (let attempt = 0; attempt < 3; attempt++) {
    const out = await attemptCheckout(inp, ref, onStep, api);
    if (out.kind === 'restart') { ref = null; continue; }
    if (out.kind === 'resync') { ref = out.ref; continue; }
    return out;
  }
  return { kind: 'error', code: 'failed', ref };
}

async function attemptCheckout(inp: CheckoutInput, start: OrderRef | null, onStep: (s: CheckoutStep) => void, api: Api): Promise<Attempt> {
  const list = inp.eyes;
  const n = list.length;
  const ids = list.map((e) => e.id);
  let ref: OrderRef | null = start ? { ...start, eyes: [...start.eyes] } : null;
  const server = new Map<string, number>();   // eye id -> the slot the order holds it in
  let slots: number[] = [];                   // every slot the order holds

  // 1. what the order holds, by the server's own record
  if (ref) {
    if (ref.expiresAt * 1000 - Date.now() < ORDER_FRESH_MS) return { kind: 'restart' };
    onStep({ kind: 'sync' });
    const r = await api<unknown>(statusPath(ref.order, ref.k));
    if (r.status === 403) return { kind: 'restart' };
    if (!r.ok || !isStatus(r.data)) return failure(r, ref);
    const st = r.data;
    // withdrawn (api/_lib/withdraw.py): that contract is over, so buying again is a new order
    if (st.state === 'withdrawn') return { kind: 'restart' };
    if (st.state !== 'unpaid') {
      // paid, or being paid: the same artwork goes to its order page and is never paid for twice; a changed artwork
      // is a new purchase and gets a new order
      return sameList(ref.checkout, ids) ? { kind: 'paid', url: orderPageUrl(ref.order, ref.k, inp.lang), ref: null } : { kind: 'restart' };
    }
    if (st.expired || ((st.expires_at ?? 0) * 1000 - Date.now() < ORDER_FRESH_MS)) return { kind: 'restart' };
    for (const e of st.eyes) {
      if (typeof e.eye !== 'number') continue;
      slots.push(e.eye);
      if (e.ref) server.set(e.ref, e.eye);
    }
    ref.eyes = [...server.keys()];
  }

  // 2. an eye the order lacks is uploaded with its own work ticket, which must still be good
  const now = Date.now();
  const stale = list.flatMap((e, i) => (!server.has(e.id) && !(e.draft && e.draft.until > now) ? [i + 1] : []));
  if (stale.length) return { kind: 'stale', eyes: stale, ref };

  const arrange = async (o: OrderRef, want: number[]): Promise<Attempt | null> => {
    onStep({ kind: 'arrange' });
    const r = await api<unknown>('/api/order', { body: { action: 'arrange', order: o.order, k: o.k, slots: want } });
    if (r.ok) return null;
    if (r.reason === 'eyes_missing') return { kind: 'resync', ref: o };
    if (r.reason === 'draft_expired' || r.reason === 'order_paid' || r.reason === 'withdrawn' || r.status === 403) return { kind: 'restart' };
    return failure(r, o);
  };

  // 3. eyes the order holds keep their files: slots 1..m in canvas order, anything else dropped
  const kept = list.filter((e) => server.has(e.id));
  const slotOf = new Map<string, number>();
  if (ref && kept.length) {
    const want = kept.map((e) => server.get(e.id)!);
    if (!(want.every((s, i) => s === i + 1) && slots.length === kept.length)) {
      const bad = await arrange(ref, want);
      if (bad) return bad;
      ref.eyes = kept.map((e) => e.id);
    }
    kept.forEach((e, i) => slotOf.set(e.id, i + 1));
    slots = kept.map((_, i) => i + 1);
  }

  // 4. the new eyes, one request each (Vercel's 4.5 MB limit), into the slots after the kept ones
  const need = list.filter((e) => !server.has(e.id));
  let next = kept.length + 1;
  for (const [j, e] of need.entries()) {
    const slot = next++;
    const d = e.draft!;
    onStep({ kind: 'upload', i: j + 1, n: need.length });
    const body: Record<string, unknown> = {
      action: 'draft', eye: slot, crop: d.crop, preview: e.image, pad: e.pad, ticket: d.ticket, lang: inp.lang, ref: e.id,
    };
    if (ref) { body.order = ref.order; body.k = ref.k; }
    const r = await api<DraftReply>('/api/order', { body, timeoutMs: 60_000 });
    if (!r.ok || !r.data || typeof r.data.order !== 'string' || typeof r.data.k !== 'string') {
      // a 403 without a reason is the work ticket: this eye has to be taken again
      if (r.status === 403 && !r.reason) return { kind: 'stale', eyes: [list.indexOf(e) + 1], ref };
      if (r.reason === 'draft_expired' || r.reason === 'bad_link' || r.reason === 'order_paid' || r.reason === 'withdrawn') return { kind: 'restart' };
      return failure(r, ref);
    }
    if (!ref) ref = { order: r.data.order, k: r.data.k, expiresAt: r.data.expires_at, eyes: [], checkout: [] };
    // a slot that held another eye holds this one now
    ref.eyes = ref.eyes.filter((id) => server.get(id) !== slot || slotOf.has(id));
    ref.eyes.push(e.id);
    slotOf.set(e.id, slot);
    if (!slots.includes(slot)) slots.push(slot);
  }
  if (!ref) return { kind: 'error', code: 'failed', ref };

  // 5. canvas order, and nothing in the order that is no longer on the artwork
  const want = list.map((e) => slotOf.get(e.id)!);
  if (!want.every((s, i) => s === i + 1) || slots.some((s) => s > n)) {
    const bad = await arrange(ref, want);
    if (bad) return bad;
  }
  ref.eyes = [...ids];
  ref.checkout = [...ids];

  // 6. Stripe's page. The server prices the order itself and records the waiver the customer ticked.
  onStep({ kind: 'checkout' });
  const r = await api<CheckoutReply>('/api/checkout', {
    body: { order: ref.order, k: ref.k, eyes: n, style: inp.style, layout: inp.layout, names: inp.names, title: '', lang: inp.lang, consent_digital: true },
    timeoutMs: 30_000,
  });
  if (r.ok && r.data && typeof r.data.url === 'string' && r.data.url.startsWith('https://')) {
    return { kind: 'redirect', url: r.data.url, ref: { ...ref, expiresAt: r.data.expires_at || ref.expiresAt } };
  }
  if (r.reason === 'eyes_missing') return { kind: 'resync', ref };
  if (r.reason === 'already_paid') return { kind: 'paid', url: orderPageUrl(ref.order, ref.k, inp.lang), ref: null };
  if (r.reason === 'draft_expired' || r.reason === 'bad_link' || r.reason === 'withdrawn') return { kind: 'restart' };
  return failure(r, ref);
}
