// The admin panel's API client. adminCall talks to POST /api/admin with the admin key as a Bearer header; the key
// lives in this browser's localStorage only (never in an address, never sent to any other endpoint). publicCall is
// for the site's own public endpoints the lab drives (/api/analyze, deglare, enhance, compose, master_*) and
// /api/health: those never see the admin key. A call never throws: it resolves to a Reply.

const KEY = 'snapeyes.admin.key';

export function loadKey(): string {
  try { return localStorage.getItem(KEY) || ''; } catch { return ''; }
}

export function saveKey(k: string): void {
  try { localStorage.setItem(KEY, k); } catch { /* private mode: the key lives for this page only */ }
}

export function dropKey(): void {
  try { localStorage.removeItem(KEY); } catch { /* nothing stored */ }
}

/** The shape of an admin key: admin-v<epoch>.<expiry>.<32 hex>. Anything else is not sent at all. */
export const KEY_RE = /^admin-v[0-9]{1,6}\.[0-9]{9,11}\.[0-9a-f]{32}$/;

export interface Reply<T> {
  ok: boolean;
  status: number;        // 0 = no answer (offline, or our own time limit)
  data: T | null;
  reason: string;
  error: string;
  ms: number;            // the time the call took in this browser
}

type Json = Record<string, unknown>;

async function call<T>(path: string, init: RequestInit, timeoutMs: number): Promise<Reply<T>> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  const t0 = performance.now();
  try {
    const r = await fetch(path, { ...init, cache: 'no-store', credentials: 'same-origin', signal: ctrl.signal });
    const raw = await r.text();
    let j: unknown = null;
    try { j = JSON.parse(raw); } catch { /* the platform's own answer (a timeout, a 413) */ }
    const o = j && typeof j === 'object' && !Array.isArray(j) ? (j as Json) : null;
    return {
      ok: r.ok && !!o && o.ok !== false, status: r.status, data: o as T | null,
      reason: typeof o?.reason === 'string' ? o.reason : '', error: typeof o?.error === 'string' ? o.error : '',
      ms: Math.round(performance.now() - t0),
    };
  } catch {
    return { ok: false, status: 0, data: null, reason: '', error: '', ms: Math.round(performance.now() - t0) };
  } finally {
    clearTimeout(timer);
  }
}

/** POST /api/admin {action, ...}. Actions that render take up to a minute. */
export function adminCall<T>(action: string, body: Json = {}, key = loadKey(), timeoutMs = 75_000): Promise<Reply<T>> {
  return call<T>('/api/admin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json', Authorization: `Bearer ${key}` },
    body: JSON.stringify({ ...body, action }),
  }, timeoutMs);
}

/** POST JSON to one of the site's public endpoints (no admin key). */
export function publicCall<T>(path: string, body: Json, timeoutMs = 75_000): Promise<Reply<T>> {
  return call<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  }, timeoutMs);
}

export function getHealth(): Promise<Reply<Health>> {
  return call<Health>('/api/health', { method: 'GET', headers: { Accept: 'application/json' } }, 20_000);
}

// ---------------------------------------------------------------------------------------------------- replies

export interface Health {
  ok?: boolean; commit?: string; gemini_key?: boolean; blob_store?: boolean; master_store?: boolean; stripe?: boolean;
  stripe_live?: boolean; email?: boolean; ordering?: boolean; test_orders?: boolean; cron?: boolean;
  deglare_model?: boolean; sr_model?: boolean;
}

export interface Me { kind: string; expires_at: number; storage: boolean; now: number }

export interface Prices { vision: number; image_1k: number; image_4k: number }

export interface Summary {
  now: number;
  ordering: { open: boolean; problem: string };
  storage: { configured: boolean; problem: string };
  payments: { stripe: boolean; live: boolean; problem: string; email: boolean; test_orders: boolean; production: boolean };
  admin: { kind: string; expires_at: number; secret?: string };
  /** events and failed-login markers are stored only while the daily clean-up (CRON_SECRET) can delete them */
  retention?: { cron: boolean; events: boolean };
  prices_usd: Prices;
}

export type Table = Record<string, number>;

export interface Counts {
  events: number; kinds: Table; verdict: Table; block_reason: Table; blocked: number; locked: number; unlocked: number;
  device: Table; source: Table; lang: Table; enhance_qa_fail: number; enhance_fallback: number; deglare_glare: number;
  deglare_lid: number; compose_style: Table; compose_eyes: Table; compose_clean: number; master_eye: number;
  master_compose: number; master_review: number; master_rerender: number; master_lab: number; master_existing: number;
  errors: Table; error_endpoint: Table; error_reason: Table; busy: number;
  gemini: { vision: number; image_1k: number; image_4k: number };
  ms: Record<string, [number, number]>;
}

export interface StatsDay { day: string; counts: Counts; complete: boolean }
export interface Stats { days: StatsDay[]; partial: boolean; prices_usd: Prices; recording?: boolean }

export interface ErrorRow { t?: number; day?: string; endpoint?: string; kind?: string; reason?: string; status?: number; ms?: number }
export interface Errors { errors: ErrorRow[]; partial: boolean }

export interface OrderRow {
  order: string; state: string; created_at: number | null; lang: string | null; eyes: number | null; style: string | null;
  layout: string | null; amount: number | null; currency: string; paid: boolean; live: boolean | null; paid_at: number | null;
  email: string | null; drafts: number; made: number; files: number; delivery: boolean; held: boolean; review: boolean;
  withdrawal: boolean; extra_payments: number; mail: string | null;
}
export interface Orders { days: number; orders: OrderRow[]; total: number; more: boolean }

export interface Qa { ok?: boolean; ring_de00?: number | null; pupil_neutral?: boolean | null }
export interface PreviewQa { ok?: boolean; render_ok?: boolean; score?: number; [k: string]: unknown }

export interface EyeView {
  eye: number;
  draft: null | { pad?: number; uploaded?: string; crop_url?: string; preview_url?: string; crop_side?: number; preview_side?: number };
  master: null | {
    url?: string; preview_copy_url?: string; first_url?: string; second_url?: string; qa?: Qa | null;
    preview?: PreviewQa | null; needs_review: boolean; rerendered: boolean; rerender_available: boolean | null;
    render_seconds?: number; created?: string; bytes?: number;
  };
}

export interface ArtworkView {
  key: string; url?: string; created?: string; bytes?: number; width?: number; height?: number; style?: string;
  qa?: unknown; current: boolean;
}

export interface Payment { payment_intent: string; amount?: number; currency?: string; live: boolean; kind: string; paid?: string; refunded: boolean }

export interface LogEntry { t?: number; iso?: string; action?: string; order?: string | null; ok?: boolean; result?: string | null; eye?: number; detail?: string }

export interface OrderDetail {
  order: string; state: string; lab: boolean; paid: boolean; count: number; email: string | null;
  consent: null | { version?: string; at?: string; lang?: string; text?: string; text_sha256?: string };
  files: { path: string; url?: string }[];
  records: Record<string, Json>;
  eyes: EyeView[]; artworks: ArtworkView[]; payments: Payment[]; refunds: Json[]; log: LogEntry[];
  /** began: the customer's order page started making (the right of withdrawal ended); period_over: 14 days passed */
  making?: { began: boolean; period_over: boolean };
  /** start: an eye not made yet may be made from here (making began, or the withdrawal period is over) */
  can: { email: boolean; stripe: boolean; link: boolean; counts: boolean; start?: boolean };
}

export interface LabRow { order: string; files: number; eyes: number; artwork_url: string | null; eye_url: string | null }
export interface LabStart { order: string; ticket: string; expires_in: number; prices_usd: Prices }
