// What the /order page does with a paid order: nothing renders in the background on the server, so the page asks for
// each eye's 4096 px rendering (action "make", at most two at a time), then for the artwork (action "compose"), and
// shows the download. Every server step is idempotent (an eye or an artwork is never made twice), so opening the
// page again, from the email a day later or after a dropped connection, simply carries on. No React here.
import { callApi, isStatus, statusPath, type ApiReply, type OrderStatus } from './api';

export interface OrderLink { o: string; k: string; s: string | null }

/** Why the page is waiting before it asks again. */
export type WaitReason = 'busy' | 'network' | 'rendering' | 'confirming';

/** Why the page stopped asking; it shows this with a button to try again. */
export type StopReason = 'bad_link' | 'network' | 'busy' | 'failed';

export interface DriveView {
  status: OrderStatus | null;                        // the server's latest word on the order
  making: number[];                                  // eyes being made right now
  composing: boolean;                                // the artwork is being put together
  wait: { reason: WaitReason; until: number } | null;
  stop: StopReason | null;
}

export const EMPTY_VIEW: DriveView = { status: null, making: [], composing: false, wait: null, stop: null };

export interface DriveDeps {
  api: typeof callApi;
  sleep: (ms: number) => Promise<void>;
  now: () => number;
}

export const REAL_DEPS: DriveDeps = {
  api: callApi,
  sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
  now: () => Date.now(),
};

const BUSY = new Set(['model_busy', 'storage_busy', 'payments_busy']);
// an answer that means "the order is no longer what this step expected": ask for its status and go from there
const RELOAD = new Set(['in_review', 'render_rejected', 'deleted', 'not_paid', 'payment_processing', 'eyes_not_ready']);
const MAKE_TIMEOUT = 75_000;     // API.md: a make or compose takes up to about 50 s; Vercel stops it at 60 s
const STATUS_TIMEOUT = 25_000;
const PARALLEL = 2;              // API.md: one eye at a time, or at most two in parallel

const clampS = (s: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, s || lo));

/** The stop reason for an answer the page cannot go on from. */
export function stopOf(r: ApiReply<unknown>): StopReason {
  if (r.status === 403) return 'bad_link';
  if (r.status === 0 || (r.status >= 500 && !r.data)) return 'network';
  if (r.reason === 'busy_retry' || r.reason === 'rendering' || BUSY.has(r.reason)) return 'busy';
  return 'failed';
}

/** Drive one order until it is ready, held for review, deleted, not paid, or the page has to stop. emit patches the
 *  view; alive() turns false when the page no longer wants answers (it then returns at the next step and starts
 *  nothing new). */
export async function driveOrder(link: OrderLink, deps: DriveDeps, emit: (v: Partial<DriveView>) => void, alive: () => boolean): Promise<void> {
  const { api, sleep, now } = deps;
  const extra = link.s ? { s: link.s } : {};
  const post = (body: Record<string, unknown>) => api<unknown>('/api/order', { body: { ...body, order: link.o, k: link.k, ...extra }, timeoutMs: MAKE_TIMEOUT });
  const pause = async (reason: WaitReason, ms: number) => {
    emit({ wait: { reason, until: now() + ms } });
    await sleep(ms);
    if (alive()) emit({ wait: null });
  };

  /** One request, asked again after a dropped connection or a busy answer, with the server's own wait hint. */
  const patiently = async (fn: () => Promise<ApiReply<unknown>>): Promise<ApiReply<unknown>> => {
    let net = 0, busy = 0;
    for (;;) {
      const r = await fn();
      if (!alive() || r.ok) return r;
      if (r.status === 0 || (r.status >= 500 && !r.data)) {
        // offline, our time limit, or the platform's own 502/504 (a make that ran past Vercel's 60 s): the server
        // keeps what it finished, so asking again is safe
        if (++net > 4) return r;
        await pause('network', Math.min(5000 * net, 20_000));
      } else if (r.reason === 'busy_retry') {
        if (++busy > 12) return r;
        await pause('busy', 1000);
      } else if (BUSY.has(r.reason)) {
        if (++busy > 12) return r;
        await pause('busy', clampS(r.retryAfter || 10, 2, 60) * 1000);
      } else if (r.reason === 'rendering') {
        if (++busy > 12) return r;
        await pause('rendering', clampS(r.retryAfter || 15, 2, 60) * 1000);
      } else {
        return r;
      }
      if (!alive()) return r;
    }
  };

  const stop = (r: ApiReply<unknown>) => { if (alive()) emit({ stop: stopOf(r), wait: null, making: [], composing: false }); };

  const load = async (): Promise<OrderStatus | null> => {
    const r = await patiently(() => api<unknown>(statusPath(link.o, link.k, link.s, true), { timeoutMs: STATUS_TIMEOUT }));
    if (!alive()) return null;
    if (r.ok && isStatus(r.data)) { emit({ status: r.data }); return r.data; }
    stop(r);
    return null;
  };

  let st = await load();
  let unpaidChecks = 0, reloads = 0;
  while (st && alive()) {
    if (st.state === 'ready' || st.state === 'review' || st.state === 'deleted') return;
    if (st.state === 'unpaid') {
      // straight from Stripe (s in the link) the payment is confirmed within seconds; the same when the server could
      // not ask Stripe just now. Otherwise the order simply is not paid.
      if (!st.expired && (st.payment_check === 'unavailable' || (link.s && unpaidChecks < 6)) && unpaidChecks < 12) {
        unpaidChecks++;
        await pause('confirming', 5000);
        st = alive() ? await load() : null;
        continue;
      }
      return;
    }
    if (st.state === 'pending') {
      await pause('confirming', 15_000);
      st = alive() ? await load() : null;
      continue;
    }

    // paid or making: the eyes first, then the artwork
    if (++reloads > 8) { emit({ stop: 'failed', making: [], composing: false, wait: null }); return; }
    const todo = st.eyes.filter((e) => !e.made).map((e) => e.eye);
    if (todo.length) {
      const queue = [...todo];
      const making = new Set<number>();
      let outcome = 'ok' as 'ok' | 'reload' | 'stop';   // set by the workers
      const going = () => outcome === 'ok' && alive();
      const worker = async () => {
        while (queue.length && going()) {
          const eye = queue.shift()!;
          making.add(eye); emit({ making: [...making].sort((a, b) => a - b) });
          const r = await patiently(() => post({ action: 'make', eye }));
          making.delete(eye);
          if (!alive()) return;
          emit({ making: [...making].sort((a, b) => a - b) });
          if (r.ok) {
            const cur: OrderStatus = st!;
            st = { ...cur, state: 'making', eyes: cur.eyes.map((e) => (e.eye === eye ? { ...e, made: true } : e)) };
            emit({ status: st });
          } else if (RELOAD.has(r.reason) || r.status === 402 || r.status === 410) {
            if (outcome === 'ok') outcome = 'reload';
          } else {
            if (outcome !== 'stop') stop(r);
            outcome = 'stop';
          }
        }
      };
      await Promise.all(Array.from({ length: Math.min(PARALLEL, todo.length) }, worker));
      if (!alive() || outcome === 'stop') return;
      if (outcome === 'reload') { st = await load(); continue; }
    }

    emit({ composing: true });
    const r = await patiently(() => post({ action: 'compose' }));
    if (!alive()) return;
    emit({ composing: false });
    if (r.ok && isStatus(r.data)) { st = r.data; emit({ status: st }); continue; }
    if (RELOAD.has(r.reason) || r.status === 402 || r.status === 410) { st = await load(); continue; }
    stop(r);
    return;
  }
}
