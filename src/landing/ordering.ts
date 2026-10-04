import { useSyncExternalStore } from 'react';
import { noteCheckoutInfo, noteInfoUnavailable } from '../shared/pricing';

// Whether this deployment takes orders, by the capture tool's own rule (src/try/TryApp.tsx): /api/health says Stripe
// is set up (and, with a live key, the delivery email too), then GET /api/checkout says "open". The landing page is
// static, and the owner opens ordering by setting the Stripe keys, which does not rebuild it: so it asks at run time
// and swaps its "ordering opens soon" lines for the open ones (src/landing/copy.ts, the *Open variants).
// Until both answers say yes, and whenever either cannot be read (offline, the Vite dev server without the API), the
// page keeps the "soon" lines: it never promises more than /try sells. Asked once per page load, never per component.

// The two requests are started from the head of index.html (src/landing/shell/scripts.ts prefetchScript: window.__lpApi), before the
// page's script has loaded, and this takes their answers; startOrdering() lets src/main.tsx wait a moment for them before the first
// render, so an offer of another currency (below) is in the first render and not added above the hero afterwards (a layout shift).
// The same GET /api/checkout answer also names a market the visitor's country may suggest ("suggest", from Vercel's
// x-vercel-ip-country): kept here for the landing page's offer of that currency (./MarketHint.tsx), never applied.
// It is asked WITHOUT any id. While a price test runs for the visitor's market the pricing store (src/shared/pricing.ts)
// asks once more with the visitor's anonymous id in a header and keeps the ladders of the visitor's variant, so this page
// prints the price it will charge; while none runs nothing is created or sent.
let open = false;
let suggested: string | null = null;
let started: Promise<void> | null = null;
const listeners = new Set<() => void>();

// the request the head of index.html already made for this path, once (a body can be read once)
function takeEarly(path: string): Promise<Response> | undefined {
  const api = (window as unknown as { __lpApi?: Record<string, Promise<Response> | undefined> }).__lpApi;
  const p = api?.[path];
  if (api) delete api[path];
  return p;
}

async function getJson(path: string, needOk: boolean): Promise<Record<string, unknown> | null> {
  const ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = ctrl ? setTimeout(() => ctrl.abort(), 15_000) : null;
  try {
    const r = await (takeEarly(path) ?? fetch(path, { headers: { Accept: 'application/json' }, cache: 'no-store', credentials: 'same-origin', signal: ctrl?.signal }));
    if (needOk && !r.ok) return null;
    const j: unknown = await r.json();
    return j && typeof j === 'object' && !Array.isArray(j) ? (j as Record<string, unknown>) : null;
  } catch {
    return null;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function check(): Promise<{ open: boolean; suggest: string | null }> {
  const none = { open: false, suggest: null };
  const h = await getJson('/api/health', false);
  if (!h || h.stripe !== true || (h.stripe_live === true && h.email !== true)) { noteInfoUnavailable(); return none; }
  const plain = await getJson('/api/checkout', true);
  if (!plain) { noteInfoUnavailable(); return none; }
  const c = ((await noteCheckoutInfo(plain)) ?? plain) as Record<string, unknown>;
  return { open: c.ok !== false && c.open === true, suggest: typeof c.suggest === 'string' ? c.suggest : null };
}

function start(): Promise<void> {
  started ??= check().then((v) => {
    if (!v.open && v.suggest === null) return;
    open = v.open;
    suggested = v.suggest;
    listeners.forEach((l) => l());
  });
  return started;
}

/** Ask now (once per page load) and resolve when the answers are in or could not be had. src/main.tsx waits for it, for a moment
 *  at most, before the first render. */
export function startOrdering(): Promise<void> {
  return start();
}

function subscribe(onChange: () => void): () => void {
  listeners.add(onChange);
  void start();
  return () => { listeners.delete(onChange); };
}

/** true once this deployment is known to take orders; false until then (and on the server-less dev page). */
export function useOrderingOpen(): boolean {
  return useSyncExternalStore(subscribe, () => open, () => false);
}

/** The market GET /api/checkout suggests for the visitor's country, or null (src/shared/markets.ts hintMarket decides
 *  whether it may be offered). */
export function useSuggestedMarket(): string | null {
  return useSyncExternalStore(subscribe, () => suggested, () => null);
}
