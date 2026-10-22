// LAB: the motion of the two centrepiece prototypes in plain TypeScript: one clock, one frame loop that sleeps while the stage is out of view or the
// tab is hidden, the two easing curves of the landing (src/motion/tokens.css), a damped spring, and one pointer gesture that turns the piece with a
// horizontal drag and leaves a vertical one to the page (the stage has touch-action: pan-y, so the browser scrolls and the turn never traps the page).
//
// The recorder (scripts/lab/sphere/record.mjs) opens the page with ?rec: then nothing runs on its own. Time is virtual and moves only when the recorder
// calls window.__sx.step(ms), which runs one frame; pointer events sent between two steps read the same virtual clock. So a recording is the page's own
// motion, frame for frame, whatever the speed of the machine that captures it.

const params = typeof location === 'undefined' ? new URLSearchParams() : new URLSearchParams(location.search);
export const REC = params.has('rec');

let virtual = 0;
/** The time every movement reads, in ms (virtual under ?rec). */
export const now = (): number => (REC ? virtual : performance.now());

export type Frame = (t: number, dt: number) => void;
const recorded = new Set<Frame>();

export interface Loop {
  start(): void;
  stop(): void;
}

/** A frame loop. Under ?rec it is driven by window.__sx.step instead of requestAnimationFrame. */
export function loop(frame: Frame): Loop {
  if (REC) {
    return { start: () => void recorded.add(frame), stop: () => void recorded.delete(frame) };
  }
  let id = 0;
  let last = 0;
  const tick = (t: number) => {
    const dt = last ? Math.min(50, t - last) : 16.7;
    last = t;
    const prof = window.__sxProf;
    if (prof) {
      const a = performance.now();
      frame(t, dt);
      prof.push(performance.now() - a);
    } else frame(t, dt);
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

export interface RecApi {
  /** advance the virtual clock by ms and run one frame */
  step(ms: number): number;
  /** set by the prototype when its first pictures are decoded */
  ready: boolean;
  /** the centre of an artwork's button on screen (CSS px of the viewport), for the recorder's taps */
  where(id: string): { x: number; y: number } | null;
  /** what the prototype is doing (for the recorder's log) */
  state(): unknown;
}

declare global {
  interface Window {
    __sx?: RecApi;
    /** set by the frame rate probe (scripts/lab/sphere/fps.mjs): the time each frame of the piece's own code took, in ms */
    __sxProf?: number[];
  }
}

if (REC && typeof window !== 'undefined') {
  window.__sx = {
    step(ms: number) {
      virtual += ms;
      for (const f of recorded) f(virtual, ms);
      return virtual;
    },
    ready: false,
    where: () => null,
    state: () => null,
  };
}

/** The visitor asked for less motion (live: it follows a change of the setting). */
export function reducedMotion(): boolean {
  return typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// ---------------------------------------------------------------------------------------------------------------- curves

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

/** the landing's two curves: entrances and settles, and wipes and overlays */
export const easeOut = bezier(0.16, 1, 0.3, 1);
export const easeInOut = bezier(0.76, 0, 0.24, 1);
/** a softer in and out for turning the whole piece */
export const easeTurn = bezier(0.45, 0, 0.2, 1);

export const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));
export const mix = (a: number, b: number, p: number): number => a + (b - a) * p;
export const smooth = (e0: number, e1: number, v: number): number => {
  const p = clamp((v - e0) / (e1 - e0), 0, 1);
  return p * p * (3 - 2 * p);
};

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

/** A critically damped spring towards a target (semi-implicit Euler; stable for the frame times of a phone). */
export class Spring {
  x = 0;
  v = 0;
  target = 0;
  stiffness: number;
  constructor(stiffness = 120) {
    this.stiffness = stiffness;
  }
  step(dt: number): void {
    const k = this.stiffness;
    const c = 2 * Math.sqrt(k);
    let left = dt / 1000;
    while (left > 0) {
      const h = Math.min(left, 1 / 120);
      this.v += (-k * (this.x - this.target) - c * this.v) * h;
      this.x += this.v * h;
      left -= h;
    }
  }
  settled(eps = 0.01): boolean {
    return Math.abs(this.x - this.target) < eps && Math.abs(this.v) < eps * 10;
  }
}

// ---------------------------------------------------------------------------------------------------------------- the gesture

export interface DragHandler {
  /** the gesture became a turn */
  begin(): void;
  /** the distance moved since the pointer went down, in CSS px (dy is 0 except for a mouse when both axes are allowed) */
  move(dx: number, dy: number): void;
  /** the pointer let go: its speed over the last 100 ms, in px per second (0 when cancelled) */
  end(vx: number, vy: number): void;
}

/**
 * The stage's one gesture. A finger or a pen turns the piece only when it moves sideways first (8 px, more sideways than up or down); a vertical
 * swipe is left to the browser, which scrolls the page (touch-action: pan-y on the stage) and sends pointercancel. A mouse turns it after 4 px, in
 * both axes when `free`. A press that never became a turn is a tap: the button's own click runs. The click that follows a turn is swallowed, so a
 * drag that ends on an artwork does not open it.
 */
export function bindDrag(el: HTMLElement, h: DragHandler, free: boolean): () => void {
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
    samples = [[now(), x0, y0]];
  };
  const move = (e: PointerEvent) => {
    if (e.pointerId !== id || state === 'none') return;
    const dx = e.clientX - x0;
    const dy = e.clientY - y0;
    if (state === 'wait') {
      const ax = Math.abs(dx);
      const ay = Math.abs(dy);
      if (mouse) {
        if (Math.hypot(dx, dy) < 4 || (!free && ax <= ay)) return;
      } else if (ax > 8 && ax > ay * 1.2) {
        // a sideways finger: from here on this gesture is ours
      } else {
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
    const t = now();
    samples.push([t, e.clientX, e.clientY]);
    while (samples.length > 2 && t - samples[0][0] > 120) samples.shift();
    h.move(dx, mouse && free ? dy : 0);
  };
  const up = (e: PointerEvent) => {
    if (e.pointerId !== id) return;
    if (state === 'drag') {
      const t = now();
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
      h.end(vx, mouse && free ? vy : 0);
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
  if (REC) {
    l.start();
    return () => l.stop();
  }
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

/** Wait for pictures to be decoded (a picture that fails counts as done: the disc keeps its dark ground). */
export function decoded(imgs: HTMLImageElement[]): Promise<void> {
  return Promise.all(imgs.map((i) => (i.complete && i.naturalWidth ? Promise.resolve() : i.decode().catch(() => undefined)))).then(() => undefined);
}
