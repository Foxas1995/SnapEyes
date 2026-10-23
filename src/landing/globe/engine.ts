// The motion of the hero's globe (./Globe.tsx) in plain TypeScript: a frame loop that sleeps while the globe is out of view or the tab is hidden,
// the landing's two easing curves (src/motion/tokens.css) for JavaScript, and one pointer gesture that turns the globe with a sideways drag and leaves a
// vertical one to the page (the stage has touch-action: pan-y, so the browser scrolls and the globe never traps the page).
// Part of the globe's own lazy chunk: the landing's first load carries none of it.

export type Frame = (t: number, dt: number) => void;

export interface Loop {
  start(): void;
  stop(): void;
}

/** A requestAnimationFrame loop with the frame's time and the time since the last frame (capped, so a frame after a pause does not jump). */
export function loop(frame: Frame): Loop {
  let id = 0;
  let last = 0;
  const tick = (t: number) => {
    const dt = last ? Math.min(50, t - last) : 16.7;
    last = t;
    frame(t, dt);
    id = requestAnimationFrame(tick);
  };
  return {
    start() {
      if (id) return;
      last = 0;
      id = requestAnimationFrame(tick);
    },
    stop() {
      cancelAnimationFrame(id);
      id = 0;
    },
  };
}

/** The visitor asked for less motion. */
export function reducedMotion(): boolean {
  return typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** A CSS cubic-bezier as a function of progress (Newton's method on x, then y). */
export function bezier(x1: number, y1: number, x2: number, y2: number): (p: number) => number {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const x = (s: number) => ((ax * s + bx) * s + cx) * s;
  const dx = (s: number) => (3 * ax * s + 2 * bx) * s + cx;
  const y = (s: number) => ((ay * s + by) * s + cy) * s;
  return (p: number) => {
    if (p <= 0) return 0;
    if (p >= 1) return 1;
    let s = p;
    for (let i = 0; i < 6; i++) {
      const d = dx(s);
      if (Math.abs(d) < 1e-6) break;
      s -= (x(s) - p) / d;
    }
    return y(Math.min(1, Math.max(0, s)));
  };
}

/** the landing's two curves (--ease-out, --ease-inout) and a softer in and out for turning the whole globe */
export const easeOut = bezier(0.16, 1, 0.3, 1);
export const easeInOut = bezier(0.76, 0, 0.24, 1);
export const easeTurn = bezier(0.45, 0, 0.2, 1);

export const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));
export const mix = (a: number, b: number, p: number): number => a + (b - a) * p;
export const smooth = (e0: number, e1: number, v: number): number => {
  const p = clamp((v - e0) / (e1 - e0), 0, 1);
  return p * p * (3 - 2 * p);
};

/**
 * The globe's orientation as a unit quaternion [w, x, y, z] in the page's 3D frame (x right, y down, z to the viewer: the frame of a CSS transform).
 * A turn about any axis of the screen is one multiplication, so the globe can roll on in whichever direction it was dragged without the flip that
 * two angles (a yaw and a pitch) make at the poles.
 */
export type Quat = [number, number, number, number];
const DEG = Math.PI / 180;

/** a turn of deg degrees about the unit axis (ax, ay, az), in the sense of CSS rotate3d */
export const qAxis = (ax: number, ay: number, az: number, deg: number): Quat => {
  const h = (deg * DEG) / 2;
  const s = Math.sin(h);
  return [Math.cos(h), ax * s, ay * s, az * s];
};

/** a then b applied after it is qMul(b, a) */
export const qMul = (a: Quat, b: Quat): Quat => [
  a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3],
  a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
  a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1],
  a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0],
];

export const qNorm = (q: Quat): Quat => {
  const n = Math.hypot(q[0], q[1], q[2], q[3]) || 1;
  return [q[0] / n, q[1] / n, q[2] / n, q[3] / n];
};

/** the shortest way from a to b, at p (0 to 1) */
export function qSlerp(a: Quat, b: Quat, p: number): Quat {
  let d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
  const c: Quat = d < 0 ? [-b[0], -b[1], -b[2], -b[3]] : b;
  d = Math.abs(d);
  if (d > 0.9995) return qNorm([mix(a[0], c[0], p), mix(a[1], c[1], p), mix(a[2], c[2], p), mix(a[3], c[3], p)]);
  const th = Math.acos(d);
  const sa = Math.sin((1 - p) * th) / Math.sin(th);
  const sb = Math.sin(p * th) / Math.sin(th);
  return [a[0] * sa + c[0] * sb, a[1] * sa + c[1] * sb, a[2] * sa + c[2] * sb, a[3] * sa + c[3] * sb];
}

/** the rotation matrix of q, row by row (m[0..2] the first row) */
export function qMat(q: Quat): number[] {
  const [w, x, y, z] = q;
  return [
    1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
    2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
    2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y),
  ];
}

/** CSS matrix3d of a rotation matrix (CSS lists it column by column) */
export const cssMatrix = (m: number[]): string =>
  `matrix3d(${[m[0], m[3], m[6], 0, m[1], m[4], m[7], 0, m[2], m[5], m[8], 0, 0, 0, 0, 1].map((v) => (v === 0 || v === 1 ? String(v) : v.toFixed(6))).join(',')})`;

/** One value tweened from a to b over dur ms from t0 with a curve. */
export class Tween {
  a = 0;
  b = 0;
  t0 = 0;
  dur = 1;
  ease: (p: number) => number = easeOut;
  set(a: number, b: number, t0: number, dur: number, ease = easeOut): void {
    this.a = a;
    this.b = b;
    this.t0 = t0;
    this.dur = Math.max(1, dur);
    this.ease = ease;
  }
  at(t: number): number {
    return mix(this.a, this.b, this.ease(clamp((t - this.t0) / this.dur, 0, 1)));
  }
  done(t: number): boolean {
    return t - this.t0 >= this.dur;
  }
}

export interface DragHandler {
  /** the gesture became a turn */
  begin(): void;
  /** the distance moved since the pointer went down, in CSS px (both axes: a finger that started sideways may then go up, down or round) */
  move(dx: number, dy: number): void;
  /** the pointer let go: its speed over the last 100 ms, in px per second (0 when cancelled) */
  end(vx: number, vy: number): void;
}

/**
 * The stage's one gesture. A finger or a pen turns the globe only when it moves sideways first (8 px, more sideways than up or down); a vertical
 * swipe is left to the browser, which scrolls the page (touch-action: pan-y on the stage) and sends pointercancel. Once the turn has begun the
 * browser no longer pans, so the finger may go on in any direction and the globe follows it in both axes. A mouse turns it after 4 px, in both
 * axes. A press that never became a turn is a tap: the button's own click runs. The click that follows a turn is swallowed, so a drag that ends
 * on an artwork does not open it.
 */
export function bindDrag(el: HTMLElement, h: DragHandler): () => void {
  let id = -1;
  let x0 = 0;
  let y0 = 0;
  let state: 'none' | 'wait' | 'drag' = 'none';
  let mouse = false;
  let samples: [number, number, number][] = [];
  let swallow = false;

  const down = (e: PointerEvent) => {
    if (!e.isPrimary || (e.pointerType === 'mouse' && e.button !== 0)) return;
    id = e.pointerId;
    x0 = e.clientX;
    y0 = e.clientY;
    mouse = e.pointerType === 'mouse';
    state = 'wait';
    samples = [[performance.now(), x0, y0]];
  };
  const move = (e: PointerEvent) => {
    if (e.pointerId !== id || state === 'none') return;
    const dx = e.clientX - x0;
    const dy = e.clientY - y0;
    if (state === 'wait') {
      const ax = Math.abs(dx);
      const ay = Math.abs(dy);
      if (mouse) {
        if (Math.hypot(dx, dy) < 4) return;
      } else if (!(ax > 8 && ax > ay * 1.2)) {
        if (ay > 10) state = 'none';
        return;
      }
      state = 'drag';
      try {
        el.setPointerCapture(id);
      } catch {
        /* the pointer is gone already */
      }
      h.begin();
    }
    const t = performance.now();
    samples.push([t, e.clientX, e.clientY]);
    while (samples.length > 2 && t - samples[0][0] > 120) samples.shift();
    h.move(dx, dy);
  };
  const up = (e: PointerEvent) => {
    if (e.pointerId !== id) return;
    if (state === 'drag') {
      const t = performance.now();
      const recent = samples.filter((s) => t - s[0] <= 100);
      let vx = 0;
      let vy = 0;
      if (recent.length >= 2) {
        const a = recent[0];
        const b = recent[recent.length - 1];
        const span = Math.max(16, b[0] - a[0]);
        vx = ((b[1] - a[1]) / span) * 1000;
        vy = ((b[2] - a[2]) / span) * 1000;
      }
      h.end(vx, vy);
      swallow = true;
      setTimeout(() => (swallow = false), 0);
    }
    state = 'none';
    id = -1;
  };
  const cancel = (e: PointerEvent) => {
    if (e.pointerId !== id) return;
    if (state === 'drag') h.end(0, 0);
    state = 'none';
    id = -1;
  };
  const click = (e: MouseEvent) => {
    if (!swallow) return;
    e.preventDefault();
    e.stopPropagation();
    swallow = false;
  };
  el.addEventListener('pointerdown', down);
  el.addEventListener('pointermove', move);
  el.addEventListener('pointerup', up);
  el.addEventListener('pointercancel', cancel);
  el.addEventListener('click', click, true);
  return () => {
    el.removeEventListener('pointerdown', down);
    el.removeEventListener('pointermove', move);
    el.removeEventListener('pointerup', up);
    el.removeEventListener('pointercancel', cancel);
    el.removeEventListener('click', click, true);
  };
}

/** Run the loop only while the stage is on screen and the tab is visible (a phone's battery; the landing's own scenes do the same). */
export function whileVisible(el: Element, l: Loop): () => void {
  let seen = true;
  const sync = () => (seen && !document.hidden ? l.start() : l.stop());
  const io = new IntersectionObserver((es) => {
    seen = es.some((e) => e.isIntersecting);
    sync();
  });
  io.observe(el);
  document.addEventListener('visibilitychange', sync);
  sync();
  return () => {
    io.disconnect();
    document.removeEventListener('visibilitychange', sync);
    l.stop();
  };
}

/** Wait for pictures to be decoded (a picture that fails counts as done: its disc keeps its dark ground). */
export function decoded(imgs: HTMLImageElement[]): Promise<void> {
  return Promise.all(imgs.map((i) => (i.complete && i.naturalWidth ? Promise.resolve() : i.decode().catch(() => undefined)))).then(() => undefined);
}
