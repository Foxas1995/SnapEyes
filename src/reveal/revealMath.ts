// The Reveal's arithmetic, no React and no DOM: where the customer's photo and the restored iris sit on ONE circle, when the
// frame is wide and when it is tight, where the cut snaps, what the keys do. A port of designs/presentation.py (plan_frame,
// choose_rf, tight_rf, photo_box, reveal_geometry); revealMath.test.ts checks every number against the vectors Python wrote
// (src/reveal/vectors.json: made by the prototype's numpy twin, which the server does not carry: no server code builds a frame, decision C10),
// so the page's arithmetic and the prototype's cannot drift apart.
//
// FINAL pass: the planner zooms a wide frame up to D 0.70 to stay inside the photo, the tight frame is capped at D 0.90, the registration
// shift enters the window, every input is validated (checkFit, pair, edgePair). contextBox is the crop a paid order would upload for the 4:5
// card: the card and the stored wide frame are NOT in release 1 (C10), so nothing calls it; it stays, tested, for the day owner decision 9 allows them.
//
// Units: R = the limbus radius, W = the frame width. The frame is centred on the PUPIL centre (the cut runs through it), the
// iris circle has radius rf x W. Angles and offsets are in iris radii (right, down), as /api/enhance's `reveal` hands them.

export const PAD = 1.12;                       // the crop padding the site uses (api/_lib/iris.py, TryApp.process)
export const R_FRAC = 1 / (2 * PAD);           // iris radius as a share of the restored square's side
export const RF = 0.335;                       // iris radius / frame width: D = 0.67 W, the owner's example
export const RF_MIN = 0.30;
export const RF_MAX = 0.36;                    // 0.60 to 0.72 W
export const RF_SNAP_MAX = 0.350;              // the wide frame may zoom this far (D 0.70) to keep its window inside the photo
export const TIGHT_D = 0.90;                   // a tight crop (4.5): D as a share of the frame (the cap, AD3)
export const TIGHT_RF_MAX = 0.49;              // ... larger only when more than UNCOVERED_MAX would be uncovered at D 0.90
export const TIGHT_FILL = 0.85;                // an iris wider than this share of the photo's short side is a tight crop
export const UNCOVERED_MAX = 0.15;             // more of the frame beyond the photo: the tight frame
export const SHIFT_MAX = 0.06;                 // iris radii: a larger registration shift is a mis-registration
export const PUPIL_MAX = 0.30;                 // iris radii: |pupil offset| the frame accepts
export const CONTEXT_MARGIN = 0.05;            // of the window: the context crop's margin
export const CONTEXT_MAX_SIDE = 1600;          // longest side of the context crop the page uploads with a paid order
export const SNAP = 3;                         // percent: the cut snaps to the pupil cut within +-3 %
export const PUPIL_CUT = 50;                   // percent
export const CARD_ASPECT: Aspect = [4, 5];

export type Aspect = readonly [number, number];

/** The limbus circle in the photo the page holds, in that photo's pixels (the analysis fit, /api/analyze `iris` times W, H). */
export interface Fit { cx: number; cy: number; r: number; W: number; H: number; pad?: number }

/** What /api/enhance returns next to the display copy (the "reveal" field: api/_lib/styles/reveal.py reveal_for, about 150 bytes). */
export interface RevealParams {
  pupil: readonly [number, number];            // pupil centre, iris radii from the crop centre (right, down)
  shift: readonly [number, number];            // translation of the photo layer, iris radii (registration, measured server side)
  edge: readonly [number, number];             // the restored edge: alpha 1 up to e0 R (e0 >= 0.95), 0 from e1 R
  ok: boolean;                                 // false: registration or colour could not be trusted, show the strip without the cut
  rho?: number | null;                         // pupil radius, iris radii
  cls?: 'round' | 'slit' | 'bar' | null;       // the restored pupil's shape class
  soft?: boolean;                              // fewer than 100 photo px per iris radius: say "move closer"
  drift?: number;                              // dE00 between the photo's iris band and the restored one
  lid?: number;                                // share of the disc the server hid (baked into the display copy)
  ia?: number;                                 // rx / ry of an oval iris (horse); absent = a circle
}

export interface Plan { mode: 'wide' | 'tight'; rf: number }

export interface Geometry {
  plan: Plan;
  box: readonly [number, number, number, number];     // source rectangle of the frame in photo px
  cut: number;
  disc: { cx: number; cy: number; w: number; h: number; left: number; top: number; e0: number; e1: number; ia: number };   // % of the frame
  restored: { cx: number; cy: number; w: number; h: number; left: number; top: number };
}

const ratio = (a: Aspect): number => a[1] / a[0];
type Pair = readonly [number, number];

/** Throws for a fit the frame cannot be built from (the twin of presentation.check_fit). */
export function checkFit(fit: Fit): Fit {
  const v = [fit.cx, fit.cy, fit.r, fit.W, fit.H, fit.pad ?? PAD];
  if (!v.every((x) => typeof x === 'number' && Number.isFinite(x))) throw new Error('fit: not finite');
  if (fit.W < 1 || fit.H < 1) throw new Error('fit: photo without pixels');
  if (fit.r < 2) throw new Error('fit: iris under 2 px');
  if (fit.r > 2 * Math.max(fit.W, fit.H)) throw new Error('fit: iris larger than twice the photo');
  const pad = fit.pad ?? PAD;
  if (pad < 1 || pad > 2) throw new Error('fit: pad');
  return fit;
}

const clampf = (x: number, lo: number, hi: number, dflt: number): number => (Number.isFinite(x) ? Math.min(Math.max(x, lo), hi) : dflt);
const pair = (v: Pair | undefined, lim: number): [number, number] => (v ? [clampf(v[0], -lim, lim, 0), clampf(v[1], -lim, lim, 0)] : [0, 0]);
/** (e0, e1) with e0 in [0.5, 1.2] and e1 >= e0 + 0.005: the radial mask never divides by zero. */
export function edgePair(e: Pair | undefined): [number, number] {
  if (!e) return [0.985, 1.015];
  const e0 = clampf(e[0], 0.5, 1.2, 0.985);
  const e1 = clampf(e[1], 0.5, 1.4, 1.015);
  return [e0, Math.max(e1, e0 + 0.005)];
}

/** Share of the frame's window (r / (2 rf) wide, centred on the pupil, shifted by the registration) that lies beyond the photo. */
export function uncoveredWindow(fit: Fit, pupil: Pair, shift: Pair, rf: number, aspect: Aspect): number {
  const ccx = fit.cx + (pupil[0] - shift[0]) * fit.r;
  const ccy = fit.cy + (pupil[1] - shift[1]) * fit.r;
  const hw = fit.r / (2 * rf);
  const hh = hw * ratio(aspect);
  const w = Math.max(0, Math.min(ccx + hw, fit.W) - Math.max(ccx - hw, 0));
  const h = Math.max(0, Math.min(ccy + hh, fit.H) - Math.max(ccy - hh, 0));
  return 1 - (w * h) / (4 * hw * hh);
}

/** Iris radius (share of the width) of the WIDE frame and whether the wide frame works at all: zoom to RF_SNAP_MAX to keep the window inside
 *  the photo, else keep `rf` (the uncovered part is clamped, blurred, darkened); ok false when more than UNCOVERED_MAX would be uncovered. */
export function chooseRf(fit: Fit, rf: number = RF, pupil: Pair = [0, 0], aspect: Aspect = [1, 1], shift: Pair = [0, 0]): { rf: number; ok: boolean } {
  let cur = rf;
  while (cur <= RF_SNAP_MAX + 1e-9) {
    if (uncoveredWindow(fit, pupil, shift, cur, aspect) <= 1e-9) return { rf: cur, ok: true };
    cur += 0.0025;
  }
  return { rf, ok: uncoveredWindow(fit, pupil, shift, rf, aspect) <= UNCOVERED_MAX };
}

/** True when the photo is a tight crop (4.5): no lid, lash or sclera to show, or no wide frame stays inside the photo. */
export function tightNeeded(fit: Fit, pupil: Pair = [0, 0], aspect: Aspect = [1, 1], shift: Pair = [0, 0]): boolean {
  return 2 * fit.r > TIGHT_FILL * Math.min(fit.W, fit.H) || !chooseRf(fit, RF, pupil, aspect, shift).ok;
}

/** The tight frame's iris radius: D = 0.90 (the cap), larger only when more than UNCOVERED_MAX of the frame would be uncovered. */
export function tightRf(fit: Fit, pupil: Pair = [0, 0], aspect: Aspect = [1, 1], shift: Pair = [0, 0]): number {
  let cur = TIGHT_D / 2;
  while (cur < TIGHT_RF_MAX && uncoveredWindow(fit, pupil, shift, cur, aspect) > UNCOVERED_MAX) cur += 0.002;
  return Math.min(cur, TIGHT_RF_MAX);
}

/** What the page does with this photo. One function, the twin of presentation.plan_frame. */
export function planFrame(fit: Fit, pupil: Pair = [0, 0], aspect: Aspect = [1, 1], shift: Pair = [0, 0]): Plan {
  checkFit(fit);
  const p = pair(pupil, PUPIL_MAX);
  const sh = pair(shift, SHIFT_MAX);
  if (tightNeeded(fit, p, aspect, sh)) return { mode: 'tight', rf: tightRf(fit, p, aspect, sh) };
  return { mode: 'wide', rf: chooseRf(fit, RF, p, aspect, sh).rf };
}

/** The source rectangle (photo px) the frame shows; resolution independent (the shift is in iris radii). */
export function photoBox(fit: Fit, pupil: Pair, rf: number, shift: Pair, aspect: Aspect = [1, 1]): [number, number, number, number] {
  const hw = fit.r / (2 * rf);
  const hh = hw * ratio(aspect);
  const ccx = fit.cx + (pupil[0] - shift[0]) * fit.r;
  const ccy = fit.cy + (pupil[1] - shift[1]) * fit.r;
  return [ccx - hw, ccy - hh, ccx + hw, ccy + hh];
}

/** Everything the page needs to put the two layers on the frame, as numbers (percent of the frame). */
export function revealGeometry(fit: Fit, params: Pick<RevealParams, 'pupil' | 'shift' | 'edge'> & { ia?: number }, aspect: Aspect = [1, 1]): Geometry {
  checkFit(fit);
  const W = 1000;
  const H = Math.max(1, Math.round(W * ratio(aspect)));          // the frame is whole pixels, as presentation.frame_size
  const pupil = pair(params.pupil, PUPIL_MAX);
  const shift = pair(params.shift, SHIFT_MAX);
  const [e0, e1] = edgePair(params.edge);
  const ia = clampf(params.ia ?? 1, 1, 2, 1);
  const plan = planFrame(fit, pupil, aspect, shift);
  const rf = plan.rf;
  const cx = ((W / 2 - pupil[0] * rf * W) / W) * 100;
  const cy = ((H / 2 - pupil[1] * rf * W) / H) * 100;
  const dw = 2 * rf * 100;
  const dh = (((2 * rf * W) / H) * 100) / ia;
  const sw = (rf / R_FRAC) * 100;
  const sh2 = ((rf / R_FRAC) * W / H) * 100;
  return {
    plan,
    box: photoBox(fit, pupil, rf, shift, aspect),
    cut: 0.5,
    disc: { cx, cy, w: dw, h: dh, left: cx - dw / 2, top: cy - dh / 2, e0, e1, ia },
    restored: { cx, cy, w: sw, h: sh2, left: cx - sw / 2, top: cy - sh2 / 2 },
  };
}

/** The context crop a paid card would need (integer photo px): the window of the tallest frame (the 4:5 card) plus CONTEXT_MARGIN, clipped to the
 *  photo. The twin of presentation.context_box. NOT USED in release 1 (decision C10: nothing is uploaded, no wide frame is stored). */
export function contextBox(fit: Fit, params: Pick<RevealParams, 'pupil' | 'shift'>, aspect: Aspect = CARD_ASPECT): [number, number, number, number] {
  checkFit(fit);
  const pupil = pair(params.pupil, PUPIL_MAX);
  const shift = pair(params.shift, SHIFT_MAX);
  const one = planFrame(fit, pupil, [1, 1], shift);
  const card = planFrame(fit, pupil, aspect, shift);
  const rf = Math.min(one.rf, card.rf);
  const [x0, y0, x1, y1] = photoBox(fit, pupil, rf, shift, aspect);
  const mx = (x1 - x0) * CONTEXT_MARGIN;
  const my = (y1 - y0) * CONTEXT_MARGIN;
  const bx0 = Math.max(0, Math.floor(x0 - mx));
  const by0 = Math.max(0, Math.floor(y0 - my));
  const bx1 = Math.min(fit.W, Math.ceil(x1 + mx));
  const by1 = Math.min(fit.H, Math.ceil(y1 + my));
  if (bx1 <= bx0 || by1 <= by0) return [0, 0, Math.floor(fit.W), Math.floor(fit.H)];
  return [bx0, by0, bx1, by1];
}

/** Share of the frame the photo does not cover (0..1), from the source box. */
export function uncoveredShare(box: readonly [number, number, number, number], W: number, H: number): number {
  const [x0, y0, x1, y1] = box;
  const w = Math.max(0, Math.min(x1, W) - Math.max(x0, 0));
  const h = Math.max(0, Math.min(y1, H) - Math.max(y0, 0));
  return 1 - (w * h) / ((x1 - x0) * (y1 - y0));
}

const smooth = (x: number): number => { const t = Math.min(1, Math.max(0, x)); return t * t * (3 - 2 * t); };

/** The restored edge as CSS mask stops: alpha 1 up to e0, smoothstep down to 0 at e1 (positions as a share of R, the mask's
 *  radius when the wrapper is the disc's bounding square and the gradient is `closest-side`). */
export function maskStops(e0: number, e1: number, n = 12): Array<{ pos: number; alpha: number }> {
  const out: Array<{ pos: number; alpha: number }> = [{ pos: 0, alpha: 1 }];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    out.push({ pos: e0 + (e1 - e0) * t, alpha: 1 - smooth(t) });
  }
  return out;
}

/** `radial-gradient(closest-side, rgba(0,0,0,a) p%, ...)` for maskImage / WebkitMaskImage. */
export function maskCss(e0: number, e1: number): string {
  const s = maskStops(e0, e1).map((p) => `rgba(0,0,0,${p.alpha.toFixed(4)}) ${(p.pos * 100).toFixed(2)}%`);
  return `radial-gradient(closest-side, ${s.join(', ')})`;
}

// ---- the cut: snapping and keys (percent of the frame width, 0 = all restored, 100 = all photo)

export const clampCut = (p: number): number => Math.max(0, Math.min(100, p));

/** Snap to the pupil cut within +-SNAP percent. */
export function snapCut(p: number, target: number = PUPIL_CUT, tol: number = SNAP): number {
  const c = clampCut(p);
  return Math.abs(c - target) <= tol ? target : c;
}

/** True when moving from `from` to `to` enters the snap zone (the page ticks the haptic once). */
export const entersSnap = (from: number, to: number, tol: number = SNAP): boolean =>
  Math.abs(from - PUPIL_CUT) > tol && Math.abs(to - PUPIL_CUT) <= tol;

/** The key's effect on the cut, null for a key the slider ignores: arrows +-2, Home 0, End 100, Enter snaps to the pupil cut. */
export function keyCut(pos: number, key: string): number | null {
  switch (key) {
    case 'ArrowLeft': case 'ArrowDown': return clampCut(pos - 2);
    case 'ArrowRight': case 'ArrowUp': return clampCut(pos + 2);
    case 'Home': return 0;
    case 'End': return 100;
    case 'Enter': return PUPIL_CUT;
    default: return null;
  }
}

/** Double tap toggles 0 % / 50 % / 100 %: pupil cut -> all photo -> all restored -> pupil cut. */
export function toggleCut(pos: number): number {
  if (Math.abs(pos - PUPIL_CUT) <= SNAP) return 100;
  if (pos >= 100 - SNAP) return 0;
  return PUPIL_CUT;
}

/** aria-valuetext of the slider: how much of the frame the photo takes. `template` is the page language's words with {n} for the percent
 *  (src/try/copy.ts T.result.reveal.valueText: the four languages live in the copy files, where the build's text check reads them). */
export const valueText = (pos: number, template: string = 'photo {n} percent'): string => template.replace('{n}', String(Math.round(pos)));

/** The arrival sweep of 4.2: wait 400 ms, then 900 ms from all photo to the pupil cut; none with reduced motion. */
export interface Sweep { from: number; to: number; delayMs: number; durationMs: number; easing: string }
export function sweepFor(reducedMotion: boolean): Sweep {
  return reducedMotion
    ? { from: PUPIL_CUT, to: PUPIL_CUT, delayMs: 0, durationMs: 0, easing: 'linear' }
    : { from: 100, to: PUPIL_CUT, delayMs: 400, durationMs: 900, easing: 'cubic-bezier(.2,.7,.2,1)' };
}

/** The step of the three-up strip's fade-in (500 ms each, in order); none with reduced motion. */
export const stripFadeMs = (col: number, reducedMotion: boolean): { delay: number; duration: number } =>
  reducedMotion ? { delay: 0, duration: 0 } : { delay: col * 500, duration: 500 };

// ---- what the page does with the server's answer (work package WP9)

/** The colour gate of reveal.py: the restored colour is this many dE00 or more away from the photo's: the cut would show two different eyes. */
export const DRIFT_FAIL = 8;

/** The fit of a photo that IS the client crop (the crop /api/deglare took, which the page keeps as `before`): its limbus circle is the crop's own
 *  inscribed iris circle, so the frame is the tight one and nothing around the iris is invented. Any side works: the geometry is in percent. After
 *  a return from Stripe's page the wide frame is gone (it is kept in memory only), and this is what the Reveal is built from. */
export function tightFit(side: number, pad: number = PAD): Fit {
  return { cx: side / 2, cy: side / 2, r: side / (2 * pad), W: side, H: side, pad };
}

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isPair = (v: unknown): v is [number, number] => Array.isArray(v) && v.length === 2 && isNum(v[0]) && isNum(v[1]);

/** The "reveal" field of /api/enhance, checked: null for anything that is not what the server sends (an older server sends none, the sample
 *  eye has none, and a copy kept by an older page may hold anything). The page then keeps the plain before and after slider. */
export function parseReveal(raw: unknown): RevealParams | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  if (!isPair(r.pupil) || !isPair(r.shift) || !isPair(r.edge) || typeof r.ok !== 'boolean') return null;
  const out: RevealParams = { pupil: [r.pupil[0], r.pupil[1]], shift: [r.shift[0], r.shift[1]], edge: [r.edge[0], r.edge[1]], ok: r.ok };
  if (isNum(r.rho)) out.rho = r.rho;
  if (r.cls === 'round' || r.cls === 'slit' || r.cls === 'bar') out.cls = r.cls;
  if (typeof r.soft === 'boolean') out.soft = r.soft;
  if (isNum(r.drift)) out.drift = r.drift;
  if (isNum(r.lid)) out.lid = r.lid;
  if (isNum(r.ia) && r.ia >= 1 && r.ia <= 2) out.ia = r.ia;
  return out;
}

/** What the page shows for one eye: 'cut' (the Reveal: photo left of a hard cut, restored iris right), 'strip' (the Reveal is withheld: the
 *  strip of photo and restored iris side by side, with the note that the cut could not be shown), or 'plain' (the old before and after slider:
 *  no reveal numbers: an older server, no time left on the server, or the AI-generated sample eye). */
export type RevealView = 'cut' | 'strip' | 'plain';
export const revealView = (rv: RevealParams | null | undefined, sample = false): RevealView => (sample || !rv ? 'plain' : rv.ok ? 'cut' : 'strip');

/** True when the Reveal is withheld because the restored colour drifted from the photo (the p09f case): the colour check's retake advice shows for that eye. */
export const withheldByColour = (rv: RevealParams | null | undefined): boolean => !!rv && !rv.ok && (rv.drift ?? 0) > DRIFT_FAIL;
