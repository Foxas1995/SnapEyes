import { useSyncExternalStore } from 'react';

// Whether this deployment takes orders, by the capture tool's own rule (src/try/TryApp.tsx): /api/health says Stripe
// is set up (and, with a live key, the delivery email too), then GET /api/checkout says "open". The landing page is
// static, and the owner opens ordering by setting the Stripe keys, which does not rebuild it: so it asks at run time
// and swaps its "ordering opens soon" lines for the open ones (src/landing/copy.ts, the *Open variants).
// Until both answers say yes, and whenever either cannot be read (offline, the Vite dev server without the API), the
// page keeps the "soon" lines: it never promises more than /try sells. Asked once per page load, never per component.

// The same GET /api/checkout answer also names a market the visitor's country may suggest ("suggest", from Vercel's
// x-vercel-ip-country): kept here for the landing page's offer of that currency (./MarketHint.tsx), never applied.
let open = false;
let suggested: string | null = null;
let started = false;
const listeners = new Set<() => void>();

async function getJson(path: string, needOk: boolean): Promise<Record<string, unknown> | null> {
  const ctrl = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = ctrl ? setTimeout(() => ctrl.abort(), 15_000) : null;
  try {
    const r = await fetch(path, { headers: { Accept: 'application/json' }, cache: 'no-store', credentials: 'same-origin', signal: ctrl?.signal });
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
  if (!h || h.stripe !== true || (h.stripe_live === true && h.email !== true)) return none;
  const c = await getJson('/api/checkout', true);
  if (!c) return none;
  return { open: c.ok !== false && c.open === true, suggest: typeof c.suggest === 'string' ? c.suggest : null };
}

function subscribe(onChange: () => void): () => void {
  listeners.add(onChange);
  if (!started) {
    started = true;
    void check().then((v) => {
      if (!v.open && v.suggest === null) return;
      open = v.open;
      suggested = v.suggest;
      listeners.forEach((l) => l());
    });
  }
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
