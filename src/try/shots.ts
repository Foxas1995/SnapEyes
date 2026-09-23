// Types and pure helpers for the capture flow: reading /api/analyze defensively, ranking shots and picking
// the one tip worth showing. No React and no DOM here, so the rules can be checked on their own.

export interface Quality {
  diameter_px: number;
  sharpness: number;
  fibre?: number;
  sharpness_label: string;
  occlusion_pct: number;
  glare: boolean;
  locked?: boolean;
  verdict: 'good' | 'ok' | 'weak';
  message: string;
  tips: string[];
  // Added by the glare-robust engine. All optional: an older deployed server does not send them and the
  // page has to keep working against it.
  detail?: number | null;
  fibre_score?: number | null;
  glare_on_fibres_pct?: number | null;
  pupil_reflection?: boolean;
  lamp_cast?: boolean;
  lamp_message?: string | null;
}

export interface Targets {
  detail_good: number;
  detail_ok: number;
  min_diameter_px: number;
  good_diameter_px: number;
  max_shots: number;
}

export interface Analysis {
  ok: boolean;
  reason?: string;
  message?: string;
  ticket?: string;
  pupil_r?: number | null;
  fibre?: number;
  iris?: { cx: number; cy: number; r: number };
  pad?: number;
  glare_boxes_crop?: number[][];
  picked?: { used: number; of: number; fibre: number; worst: number };
  quality?: Quality;
  targets?: Partial<Targets>;
  preview?: string;
}

// Only used when a server predates "targets". The detail bands are placeholders for the colour of the
// meter; the size floors are the ones the old verdict used (280 px usable, 420 px good).
export const DEFAULT_TARGETS: Targets = { detail_good: 70, detail_ok: 40, min_diameter_px: 280, good_diameter_px: 420, max_shots: 5 };

export const PUPIL_NOTE = 'A reflection on the pupil is fine: we rebuild the pupil as clean darkness.';
export const LAMP_FALLBACK = 'Lamp light is tinting the white of your eye, so the colours may come out warmer than they really are.';

export const num = (v: unknown): number | undefined => (typeof v === 'number' && Number.isFinite(v) ? v : undefined);

export function targetsOf(a?: Analysis | null): Targets {
  const t = a?.targets || {};
  const pick = (k: keyof Targets) => num(t[k]) ?? DEFAULT_TARGETS[k];
  return {
    detail_good: pick('detail_good'),
    detail_ok: pick('detail_ok'),
    min_diameter_px: pick('min_diameter_px'),
    good_diameter_px: pick('good_diameter_px'),
    // a bad value must never ask for zero shots or an endless loop of them
    max_shots: Math.max(1, Math.min(10, Math.round(pick('max_shots')))),
  };
}

/** Customer-facing Detail 0-100, or undefined when the server does not send it. */
export const detailOf = (a?: Analysis | null): number | undefined => {
  const d = num(a?.quality?.detail);
  return d === undefined ? undefined : Math.max(0, Math.min(100, Math.round(d)));
};

/** The raw fibre measure behind the score: the glare-masked one when present, the old one otherwise. */
export const rawFibre = (a: Analysis): number => num(a.quality?.fibre_score) ?? num(a.quality?.fibre) ?? num(a.fibre) ?? 0;

const VERDICT_RANK = { weak: 0, ok: 1, good: 2 } as const;
/** good 2, ok 1, weak 0. A missing verdict ranks as weak: no evidence the shot is usable. */
const verdictRank = (a: Analysis): number => VERDICT_RANK[a.quality?.verdict as keyof typeof VERDICT_RANK] ?? 0;

/** Positive when shot x is better than shot y. Compared in this order, each step only breaking ties of the
 *  one before:
 *  1. locked: a crop that never locked onto the iris edge loses, its "detail" may be eyelash or skin texture.
 *  2. usable: any 'ok' or 'good' shot beats a 'weak' one. Detail is glare-masked on purpose, so it cannot see
 *     the glare cap, the iris-size floor or the eyelid floor that the engine's verdict applies.
 *  3. lamp-free: a usable shot without a lamp colour cast beats a tinted one. The colour in the print comes
 *     straight from the photo, and "Try a retake" asks for exactly this daylight shot, so it must win.
 *  4. verdict: good beats ok.
 *  5. Detail, then the raw score (Detail is a capped integer, so two sharp shots can both read 100). */
export function compareShots(x: Analysis, y: Analysis): number {
  const key = (a: Analysis) => [
    a.quality?.locked === false ? 0 : 1,
    verdictRank(a) > 0 ? 1 : 0,
    a.quality?.lamp_cast ? 0 : 1,
    verdictRank(a),
    detailOf(a) ?? rawFibre(a),
    rawFibre(a),
  ];
  const kx = key(x), ky = key(y);
  for (let i = 0; i < kx.length; i++) if (kx[i] !== ky[i]) return kx[i] - ky[i];
  return 0;
}

/** A good shot goes straight to the studio, unless lamp light tinted it: then the customer sees the warning
 *  and decides, instead of learning about it from a yellow print. Always asked of the shot that will
 *  actually be processed, never of the latest one. */
export const autoContinue = (a: Analysis): boolean => a.quality?.verdict === 'good' && !a.quality?.lamp_cast;

/** Index of the best shot; on a full tie the earlier shot wins. -1 for an empty list. */
export function bestIndex(shots: Analysis[]): number {
  let best = -1;
  shots.forEach((s, i) => { if (best < 0 || compareShots(s, shots[best]) > 0) best = i; });
  return best;
}

/** The ratio for "It carries Nx the fibre detail of the softest", or null when it should not be said.
 *  The engine returns fibre_score 0.0 when glare hides every sector of the ring, so a softest shot near
 *  zero is not a measurement and would give "780x". A ratio under 1.2 says nothing; one over 10 is not
 *  believable even when it is real. */
export function fibreRatio(p: { fibre: number; worst: number }): number | null {
  if (!(p.worst >= 0.5)) return null;
  const r = p.fibre / p.worst;
  return r >= 1.2 && r <= 10 ? r : null;
}

export type Band = 'good' | 'ok' | 'low';
/** Colour band and caption for the Detail meter. Detail sees only the fibres the glare mask left, so the
 *  verdict caps the band: a sharp shot the engine calls 'weak' (glare, size, eyelid, no lock) must not show
 *  green or "Fibres resolved" next to a message saying its fibres will be rebuilt. */
export function meterBand(d: number, q: Quality | undefined, t: Targets): { band: Band; caption: string | null } {
  const byDetail = d >= t.detail_good ? 2 : d >= t.detail_ok ? 1 : 0;
  const cap = !q?.verdict ? 2 : q.locked === false ? 0 : VERDICT_RANK[q.verdict] ?? 2;
  const band = (['low', 'ok', 'good'] as const)[Math.min(byDetail, cap)];
  // above the target but capped: the reason is on the card (message or tip), so the meter stays quiet
  const caption = d < t.detail_good ? `Aim for ${t.detail_good}+` : band === 'good' ? 'Fibres resolved' : null;
  return { band, caption };
}

/** Tips worth showing. "We will remove it automatically" instructs nothing, and the old "reflection sits on
 *  your pupil, move the light" tip contradicts the calm pupil note whenever the server sets pupil_reflection. */
export function visibleTips(q: Quality): string[] {
  return (q.tips || []).filter((s) => !/automatically/i.test(s) && !(q.pupil_reflection && /reflection/i.test(s) && /pupil/i.test(s)));
}

/** The single tip that would most improve the next shot. Someone holding a phone to their eye reads one
 *  line, so pick what blocks the most detail: a crop that missed the iris, then an iris too small to carry
 *  fibres at all, then whatever the server ranked first. */
export function topTip(q: Quality, t: Targets): string | null {
  const tips = visibleTips(q);
  if (q.locked === false) return tips[0] ?? q.message ?? null;
  if (num(q.diameter_px) !== undefined && q.diameter_px < t.min_diameter_px) {
    return tips.find((s) => /closer|zoom/i.test(s)) ?? 'Move closer or zoom in so the iris fills more of the frame.';
  }
  return tips[0] ?? null;
}

/** Run fn over items with at most `limit` calls in flight. Results come back in input order whatever order
 *  they finish in. fn must not throw: a rejection would end the wait while other calls are still running. */
export async function mapPool<T, R>(items: T[], limit: number, fn: (item: T, index: number) => Promise<R>): Promise<R[]> {
  const out = new Array<R>(items.length);
  let next = 0;
  const worker = async () => {
    while (next < items.length) {
      const i = next++;
      out[i] = await fn(items[i], i);
    }
  };
  await Promise.all(Array.from({ length: Math.max(1, Math.min(limit, items.length)) }, worker));
  return out;
}
