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

/** A running (or idle) price experiment as the summary lists it (api/_lib/abtest.py summary). */
export interface ExpBrief { key: string; title: string; markets: string[]; running: boolean; since: number | null; started_at: number | null }

export interface Summary {
  now: number;
  ordering: { open: boolean; problem: string };
  storage: { configured: boolean; problem: string };
  payments: { stripe: boolean; live: boolean; problem: string; email: boolean; test_orders: boolean; production: boolean };
  admin: { kind: string; expires_at: number; secret?: string };
  /** events and failed-login markers are stored only while the daily clean-up (CRON_SECRET) can delete them */
  retention?: { cron: boolean; events: boolean };
  /** the price experiments and whether each runs (api/_lib/experiments.py) */
  experiments?: ExpBrief[];
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
  layout: string | null; amount: number | null; currency: string; market?: string; paid: boolean; live: boolean | null; paid_at: number | null;
  email: string | null; drafts: number; made: number; files: number; delivery: boolean; held: boolean; review: boolean;
  withdrawal: boolean; extra_payments: number; mail: string | null;
  /** the set level gate result of the style's rule at checkout: ok, unknown or the failing eye's reason code (order.json checkout.gate); null for an order that never reached the payment page */
  gate?: string | null;
  /** the price experiment and variant the order was priced under, if any */
  experiment?: { key: string; variant: string; label?: string | null } | null;
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
  /** the price experiment the order was made under: its variant and the price list that applied (paid.json, else the checkout) */
  experiment?: null | { key: string; variant: string; title?: string | null; label?: string | null; prices: ExpLadder | null; source: string; known: boolean };
  /** start: an eye not made yet may be made from here (making began, or the withdrawal period is over) */
  can: { email: boolean; stripe: boolean; link: boolean; counts: boolean; start?: boolean };
}

// ---------------------------------------------------------------------------------------------------- price experiments

export interface ExpLadder { one_eye_studio_black: number; one_eye_art: number; two_eyes: number; each_further_eye: number }
export interface ExpVariant { variant: string; label: string; split: number; prices: Record<string, ExpLadder> }
export interface ExpStats {
  variant: string; visitors: number; previews: number; checkouts: number; paid: number; paid_test: number;
  hit_previews: number; hit_checkouts: number; hit_paid: number; revenue: number; revenue_hit: number;
  avg_order: number | null; avg_order_hit: number | null; revenue_per_visitor: number | null;
  rate_preview: number | null; rate_checkout: number | null; rate_paid: number | null; rate_hit_paid: number | null;
  rate_paid_of_checkout: number | null;
  /** paid orders given back (refunded or withdrawn) and their amount: not in paid or revenue */
  returned: number; returned_revenue: number;
  /** what the anonymous events say about paid orders (the cross-check of the order records) */
  paid_events: number; revenue_events: number;
  /** where paid and revenue come from: the order records, or the events when the records could not be read */
  source: 'orders' | 'events';
}
export interface ExpTest { p: number | null; z: number | null; enough: boolean; why: string | null; diff?: number }
export interface ExpCompare extends ExpTest {
  variant: string;
  /** revenue per visitor against the control (the decision metric): difference in the smallest unit, z, p */
  rpv: { diff: number; z: number; p: number } | null;
  /** only for a test that changes some of the prices: the conversion to the affected orders alone */
  hit: ExpTest | null;
  /** every arm has reached the size the note asks for: only then a verdict is allowed */
  planned: boolean;
}
export interface ExpWarning {
  code: 'loss' | 'spread' | 'events_differ'; variant?: string; market?: string; eyes?: number; style?: string; price?: number; net?: number;
  ratio?: number; orders?: number; events?: number;
}
export interface ExpNeed { visitors: number; paid: number; rate: number; rel: number; assumed: boolean }
export interface Experiment {
  key: string; title: string; about: string; markets: string[]; currency: string; changes: string[]; hit_label: string;
  partial: boolean; retired: boolean; stats_error: boolean;
  state: { running: boolean; since: number | null; started_at: number | null; stopped_at: number | null; updated: number | null;
    runs: { start: number | null; stop: number | null }[] };
  conflict: string | null;
  variants: ExpVariant[];
  stats: ExpStats[];
  compare: ExpCompare[];
  need: ExpNeed | null;
  need_hit: ExpNeed | null;
  /** orders of the test's markets made while it ran that carry no variant */
  untokened: { orders: number; paid: number } | null;
  days: number;
  warnings: ExpWarning[];
  /** changes of the style switch made while this test ran that changed what could be ordered (api/_lib/abtest.py catalogue_changes), newest first */
  catalogue?: CatalogueChange[];
}
export interface Experiments {
  now: number; experiments: Experiment[]; partial: boolean; log: LogEntry[];
  runs: { key: string; title: string; start: number; stop: number | null }[];
  ordering_open: boolean | null;
  /** does this deployment store events at all (CRON_SECRET)? */
  collecting: boolean | null;
  orders_source: 'orders' | 'events' | 'events_cut';
  costs: { unit_usd_per_eye: number };
  rules: { min_arm_paid: number; min_arm_visitors: number; spread_warn: number; rel_effect: number };
}

export interface LabRow { order: string; files: number; eyes: number; artwork_url: string | null; eye_url: string | null }

/** styles_lab without a style: the styles of the v3 engine this deployment can draw, to build the menu from */
export interface StyleLabRow { id: string; name: string; design: string; module: string; ceiling: string | null; stage: string | null; gate: string; canvases: string[]; plates: string[]; looks?: string[] }
export interface StyleLabList { styles: StyleLabRow[]; sizes: number[] }
export interface SelfcheckItem { ok: boolean; [k: string]: unknown }
/** styles_lab with a style: one picture, the checks that ran on it and what the engine says it did */
export interface StyleLabResult {
  style: string; design: string; canvas: string; width: number; height: number; cls: string; seed: string; seed_mode?: string; eye_id?: string;
  image: string; view: [number, number];
  crop: null | { x: number; y: number; w: number; h: number; image: string };
  facts: Record<string, unknown>; plan: Record<string, unknown>;
  selfcheck: null | { ok: boolean; checks: Record<string, SelfcheckItem>; ms: number };
  times: Record<string, number>;
  estimate: null | { need_s: number | null; est_mb: number | null; ok: boolean; why: string | null };
  ms?: number;
}
export interface LabStart { order: string; ticket: string; expires_in: number; prices_usd: Prices }

// The master plan of an order or a lab test (api/_lib/styles/steps.py): the admin actions order_steps, rerun_step and lab_steps.
export interface StepDone {
  step: string; rerun?: number; ms?: number; cpu_s?: number; peak_mb?: number | null; rss_mb?: number | null; hwm_mb?: number | null; attempt?: number;
  need_s?: number | null; est_mb?: number | null; by?: string; at?: string; drift?: unknown; inputs?: unknown;
  outputs?: { path: string; bytes?: number | null; sha12?: string | null }[]; result?: Record<string, unknown>;
}
export interface StepTry { kills: number; open: boolean; plate: number; errors: string[]; watchdog: number; attempts: number; last?: string; plate_id?: string }
export interface StepRow { name: string; kind: string; eyes?: number[]; need_s?: number | null; est_mb?: number | null; done: StepDone | null; try: StepTry | null }
/** steps.capacity(): can the plan's step run at all on this function (why: time, memory or no_cost when it cannot) */
export interface StepCapacity { ok: boolean; why: string | null; need_s: number | null; est_mb: number | null; factor: number; budget_s: number; mem_budget_mb: number }
export interface StepEye { eye: number; eye_id?: string | null; cls?: string | null; pupil?: string | null; gate: { lid: boolean | null; fill: boolean | null }; gate_why?: { lid: string[]; fill: string[] } }
export interface StepsView {
  plan: Record<string, unknown> | null; steps: StepRow[]; rerun: number; progress: { done: number; of: number; step: string | null };
  locks: Record<string, { age_s: number; stale: boolean } | null>; capacity: StepCapacity | null; factor: number; registry_hash: string; engine_v: number;
  eyes: StepEye[]; artwork?: Record<string, unknown> | null;
}
/** lab_steps: a dry run has a plan and a capacity; a run the whole view and the artwork (with a signed link) */
export type LabStepsResult = Partial<StepsView> & { result: string; artwork?: Record<string, unknown> | null };

// ---------------------------------------------------------------------------------------------------- the style switch and its numbers (WP13)

/** A change of the style switch seen from a price test's card: the effective stage of each eye count before and after. */
export interface CatalogueChange { t?: number; iso?: string; style?: string; eyes?: number[]; stage?: string | null; before?: Record<string, string | null>; after?: Record<string, string | null> }

export type StageCode = 'planned' | 'lab' | 'preview' | 'live' | 'retired';
export type L0State = 'pass' | 'below_bar' | 'incomplete' | 'waiver' | null;
export interface StyleMark { ticked_at: string; by: string; score?: { mean?: number; min_axis?: number }; director?: string }
export interface StyleWaiver { at: string; by: string; text: string }
export interface StyleRange {
  eyes: [number, number]; ceiling: StageCode | null; override: 'lab' | 'preview' | 'live' | null; effective: StageCode | null; orderable: boolean; switchable: boolean;
  checklist: Record<string, StyleMark>; waiver: StyleWaiver | null; missing_for_live: string[]; l0: L0State;
}
export interface StyleLast { by?: string | null; at?: string | null; reason?: string | null; reason_kind?: string | null }
export interface StyleRow {
  id: string; name: string; group: string; legacy: boolean; eyes: [number, number]; gate: string; price_class: string; built: boolean;
  ranges: StyleRange[]; last: StyleLast | null;
}
export interface StyleLimits { min_n: number; error_rate: number; review_rate: number; gate_fail_rate: number }
export interface StyleCatalogue {
  rev: number; at: string | null; checks: string[]; limits: StyleLimits; l0_bar: { mean: number; min_axis: number };
  default_effective: string | null; fallback_stage: string; registry_hash: string; ordering_open: boolean; price_test: string[];
  orderable_max_eyes: number; styles: StyleRow[];
}
export interface StyleHeld { count: number; orders: string[]; checked: number; more: boolean; failed: string[]; unread: number; error: string | null; incomplete: boolean }
export interface StyleChange {
  result: 'changed' | 'ticked' | 'same'; style: string; eyes: number[]; rev: number; before: Record<string, string | null>; after: Record<string, string | null>;
  effective: Record<string, string | null>; ceiling: Record<string, string | null>; ticked?: string[]; unticked?: string[]; waiver?: string | null;
  l0: Record<string, L0State>; price_test?: string[]; in_flight: 'finish' | 'hold' | null; held: StyleHeld | null; audit_written?: boolean; view: StyleRow;
}

/** One row of the set level funnel: per eye count (and per colour class), always with n. */
export interface FunnelLine { ok: boolean; n: number; need_n: number; first: number | null; need_first: number; retake: number | null; need_retake: number; why: string[] }
export interface FunnelRow {
  eyes: number; cls: string | null; first: number; first_pass: number; unknown: number; retake1: number; retake1_pass: number; retake2: number; retake2_pass: number;
  fails: Record<string, number>; rate_first: number | null; rate_retake: number | null; line: FunnelLine | null;
}
export interface DemandRow { style: string; name: string; eyes: number; stage: string; tiles: number; large: number; soon: number; blocked: number }
export interface PreviewRow { style: string; name: string; previews: number; tiles: number }
export interface ConversionRow { style: string; name: string; eyes: number; previews: number; started: number; paid: number; rate_started: number | null; rate_paid: number | null }
export interface AfterFailureRow { eyes: number; started: number; paid: number; started_failed: number; paid_failed: number; by_code: Record<string, number>; share_paid_failed: number | null }
export interface FallbackRow { style: string; name: string; fallback: string; count: number; of: number; share: number | null }
export interface TimeRow { what: string; style: string; name: string; eyes: number; n: number; p50_ms: number | null; p95_ms: number | null; over: number; need_s: number | null }
export interface ErrorStyleRow { style: string; name: string; errors: number; asked: number; rate: number | null }
export interface QaStyleRow { style: string; name: string; qa_fail: number; of: number; rate: number | null }
export interface ReviewStyleRow { style: string; name: string; review: number; made: number; rate: number | null }
export interface BusyRow { endpoint: string; style: string; name: string | null; count: number }
export interface GateStyleRow { style: string; name: string; policy: string; rule: string; seen: number; failed: number; rate: number | null }
export interface AttentionItem { kind: 'error' | 'review' | 'gate' | 'health' | 'hold'; style?: string; rate?: number; n?: number; limit?: number; key?: string; code?: string }
export interface StylesStats {
  days: number; partial: boolean; recording: boolean; market: string | null; lang: string | null; limits: StyleLimits; health: Record<string, boolean> | null;
  requests: { total: number; drew_nothing: number };
  funnel: FunnelRow[]; funnel_by_class: FunnelRow[]; opening: Record<string, FunnelLine>;
  demand: DemandRow[]; chosen: { pick: number; other: number; share: number | null };
  chosen_by_class: { cls: string; pick: number; other: number; n: number; share: number | null }[];
  previews: PreviewRow[]; conversion: { recorded: boolean; rows: ConversionRow[] }; after_failure: AfterFailureRow[]; fallbacks: FallbackRow[];
  times: TimeRow[]; busy_retry: BusyRow[]; errors: ErrorStyleRow[]; qa: QaStyleRow[]; review: ReviewStyleRow[];
  gate: { codes: Table; reasons: Table; classes: Table; pupils: Table; by_style: GateStyleRow[] };
  holds: Table; master: { made_by_style: Table; fallback: Table };
  help: { routes: Table; why: Table; eyes: Table };
  reveal: { codes: Table; n: number; ok_share: number | null; ms: number | null };
  attention: AttentionItem[];
  memory: { peak_mb_avg: number | null; n: number; peak_mb_is: string; hwm_is: string };
  filter: { slice: string | null; sliced: string[]; whole: string[] };
}

/** One entry of the switch's audit log (api/_lib/stage_overrides.py audit_put). */
export interface StyleAuditEntry {
  kind: 'override' | 'limits' | 'hold'; t?: number; iso?: string; by?: string; style?: string; name?: string; eyes?: number[]; stage?: string | null;
  before?: Record<string, string | null>; after?: Record<string, string | null>; effective_before?: Record<string, string | null>; effective_after?: Record<string, string | null>;
  ceiling?: Record<string, string | null>; reason?: string; reason_kind?: string; ticked?: string[]; unticked?: string[]; waiver?: string | null; l0?: Record<string, L0State>;
  numbers?: Record<string, { n: number; first_pass: number | null; with_retake: number | null; unknown: number; line_ok: boolean | null; why: string[]; partial?: boolean }> | null;
  price_test?: string[]; price_test_seen?: boolean; in_flight?: string | null; held?: StyleHeld | null; rev?: number; limits?: StyleLimits;
}

/** styles_lab with eyes or order and ns: the contact sheet of a group (api/_lib/ops.py a_styles_lab_group). */
export interface GroupGateRule { ok: boolean | null; values?: Record<string, unknown>; why?: string[] }
export interface GroupEye { eye: number; eye_id: string | null; cls: string | null; pupil: string | null; gate: { lid: GroupGateRule | null; fill: GroupGateRule | null } }
export interface GroupTile {
  id: string; name: string; look: string | null; stage: StageCode | null; ceiling: StageCode | null; available: boolean; why: string | null; image: string | null;
  width?: number; height?: number; layout?: string; canvas?: string | null; design_used?: string | null; fallback?: string | null;
  selfcheck?: { ok: boolean | null; failed?: unknown } | null; times?: Record<string, number> | null; ms?: number; plate?: string; error?: string;
}
export interface GroupSheet { group: number; size: number; eyes: GroupEye[]; tiles: GroupTile[]; pick: string | null; partial: boolean; timing: { total_ms: number; eyes_ms: number } }

/** order_link: one signed link of one file of an order, made when the owner asks for it. */
export interface OrderLink { url: string; expires_in: number; path: string }
