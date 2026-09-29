// Sums of the per-day counts (api/_lib/events.py summarize) over a window, and the order rows' windows.
import type { Counts, OrderRow, StatsDay, Table } from './api';

export function emptyCounts(): Counts {
  return {
    events: 0, kinds: {}, verdict: {}, block_reason: {}, blocked: 0, locked: 0, unlocked: 0, device: {}, source: {}, lang: {},
    enhance_qa_fail: 0, enhance_fallback: 0, deglare_glare: 0, deglare_lid: 0, compose_style: {}, compose_eyes: {},
    compose_clean: 0, master_eye: 0, master_compose: 0, master_review: 0, master_rerender: 0, master_lab: 0,
    master_existing: 0, errors: {}, error_endpoint: {}, error_reason: {}, busy: 0,
    gemini: { vision: 0, image_1k: 0, image_4k: 0 }, ms: {},
  };
}

const isTable = (v: unknown): v is Table => !!v && typeof v === 'object' && !Array.isArray(v);

/** a + b, field by field (unknown fields are ignored, missing ones count as 0). */
export function addCounts(a: Counts, b: Partial<Counts> | undefined): Counts {
  if (!b) return a;
  const out = { ...a } as unknown as Record<string, unknown>;
  for (const [k, v] of Object.entries(b)) {
    const cur = out[k];
    if (k === 'ms' && isTable(v)) {
      const ms = { ...(cur as Counts['ms']) };
      for (const [step, pair] of Object.entries(v as Record<string, unknown>)) {
        if (Array.isArray(pair) && pair.length === 2) {
          const [s, n] = ms[step] || [0, 0];
          ms[step] = [s + Number(pair[0] || 0), n + Number(pair[1] || 0)];
        }
      }
      out.ms = ms;
    } else if (typeof v === 'number' && typeof cur === 'number') {
      out[k] = cur + v;
    } else if (isTable(v) && isTable(cur)) {
      const t: Table = { ...cur };
      for (const [kk, vv] of Object.entries(v)) if (typeof vv === 'number') t[kk] = (t[kk] || 0) + vv;
      out[k] = t;
    }
  }
  return out as unknown as Counts;
}

/** The counts of the last n days of `days` (oldest first, today last). */
export function lastDays(days: StatsDay[], n: number): Counts {
  return days.slice(-n).reduce((acc, d) => addCounts(acc, d.counts), emptyCounts());
}

export const sumTable = (t: Table | undefined) => Object.values(t || {}).reduce((s, v) => s + v, 0);

export function avgMs(c: Counts, step: string): number | null {
  const p = c.ms[step];
  return p && p[1] > 0 ? p[0] / p[1] : null;
}

const DAY = 86400;

export function ordersSince(rows: OrderRow[], days: number, now: number): OrderRow[] {
  const cut = startOfDay(now) - (days - 1) * DAY;
  return rows.filter((r) => (r.created_at ?? 0) >= cut);
}

/** The paid orders of the last n days, summed PER CURRENCY (an amount in forints is never added to euros):
 *  {currency (lower case): {live, test, n}}, the default currency first. */
export function revenue(rows: OrderRow[], days: number, now: number): Record<string, { live: number; test: number; n: number }> {
  const cut = startOfDay(now) - (days - 1) * DAY;
  const out: Record<string, { live: number; test: number; n: number }> = {};
  for (const r of rows) {
    if (!r.paid || (r.paid_at ?? 0) < cut || typeof r.amount !== 'number') continue;
    const cur = (r.currency || 'eur').toLowerCase();
    const v = out[cur] || (out[cur] = { live: 0, test: 0, n: 0 });
    if (r.live) { v.live += r.amount; v.n += 1; } else v.test += r.amount;
  }
  return out;
}

/** 00:00 UTC of the day `t` (unix seconds) falls in: the event days are UTC days. */
export function startOfDay(t: number): number {
  return t - (t % DAY);
}

export function countBy<T>(rows: T[], key: (r: T) => string): Table {
  const t: Table = {};
  for (const r of rows) { const k = key(r); t[k] = (t[k] || 0) + 1; }
  return t;
}
