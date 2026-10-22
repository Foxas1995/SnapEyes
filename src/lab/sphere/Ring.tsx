// LAB, prototype B: the Iris ring. A calm turntable of the same 32 artworks, like a jeweller's display seen a little from above: the one in front is
// lifted out of the ring, large and sharp, with its name and whose eye it is (the button stays the hero's own); the others stand on the ring and
// recede into the dark. A sideways swipe or drag turns it and it settles on the nearest artwork (a quick flick may pass two to four); a tapped
// artwork comes to the front; the arrow keys turn it one step. By itself it moves on one step every few seconds, slowly, until the visitor touches it.
//
// Light on a phone: only the artworks of the visible half are placed each frame (about nine transforms and opacities); the reflection under each
// one is the browser's own (-webkit-box-reflect, drawn once with the disc); a picture is only fetched when its place comes near the front, and
// the sharp one (480 px) only for the artwork that reaches the front.
import { useEffect, useLayoutEffect, useMemo, useRef, type CSSProperties } from 'react';
import './ring.css';
import { ART, RING_ORDER, discSet, pic } from './art';
import { Info } from './Info';
import type { PieceProps } from './Globe';
import type { Words } from './words';
import { REC, Spring, Tween, bindDrag, clamp, decoded, easeOut, easeTurn, loop, mix, now, reducedMotion, smooth, whileVisible } from './motion';

const RAD = Math.PI / 180;
const SLOTS = 12;                 // places on the ring
const STEP = 360 / SLOTS;
const N = RING_ORDER.length;
const AUTO_EVERY = 4800;          // ms between the steps it takes by itself
const AUTO_AFTER = 7000;          // ms of quiet after the visitor's last touch before it moves by itself again

const mod = (a: number, n: number) => ((a % n) + n) % n;

function geometry(w: number, h: number) {
  // every size is a share of the stage's width (or height), so one still poster fits the stage at any size
  const t = 0.44 * w;                     // the front artwork, as large as it is drawn (sharp: its layout size)
  return {
    w, h, t,
    r: 0.74 * w,                           // the ring's radius
    p: 2.2 * w,                            // the perspective
    lift: 0.5 * w,                         // how far the front artwork comes out of the ring towards the visitor
    tilt: 14,                              // the ring seen from above, degrees
    ring: 0.6,                             // the size of an artwork standing on the ring, against the front one
    y0: h * 0.5,                           // where the front of the ring is (the words sit under it)
    up: -0.1 * t,                          // the lifted artwork sits a little higher than the ring's front
  };
}
type Geo = ReturnType<typeof geometry>;

class RingCtl {
  stage: HTMLElement;
  tiles: HTMLButtonElement[];
  info: HTMLElement;
  words: Words;
  geo: Geo;
  reduce = reducedMotion();
  /** the ring's turn in steps: artwork position j is in front when pos = j */
  spring = new Spring(70);
  auto = new Tween();
  mode: 'rest' | 'drag' | 'spring' | 'auto' = 'rest';
  drag0 = 0;
  lastTouch = -1e9;
  nextAuto = AUTO_EVERY;
  holdAuto = false;
  front = 0;              // the artwork position in front (integer)
  current = 0;            // the artwork that holds the tab stop
  shown = 0;              // the artwork the words are about
  wordsT = new Tween();   // the words: 1 shown, 0 changing
  placed = new Map<number, number>();  // artwork index -> its place this frame
  /** what each tile's style was last written as */
  st: { tr: string; op: string; vis: string; pe: string; lit: string }[];
  infoO = '';
  infoPE = '';
  loaded: boolean[];
  sharp: boolean[];
  stopLoop: () => void;
  unbind: () => void;
  ro: ResizeObserver;

  constructor(stage: HTMLElement, info: HTMLElement, words: Words) {
    this.stage = stage;
    this.info = info;
    this.words = words;
    this.tiles = [...stage.querySelectorAll<HTMLButtonElement>('.sx-tile')];
    this.st = this.tiles.map(() => ({ tr: '', op: '', vis: 'hidden', pe: '', lit: '' }));
    this.loaded = this.tiles.map(() => false);
    this.sharp = this.tiles.map(() => false);
    this.geo = geometry(stage.clientWidth, stage.clientHeight);
    this.applyGeo();
    this.ro = new ResizeObserver(() => {
      this.geo = geometry(this.stage.clientWidth, this.stage.clientHeight);
      this.applyGeo();
      for (const st of this.st) st.tr = '';
    });
    this.ro.observe(stage);
    this.wordsT.set(1, 1, 0, 1);
    this.info.style.opacity = '1';
    this.unbind = bindDrag(stage, {
      begin: () => {
        this.mode = 'drag';
        this.drag0 = this.spring.x;
        this.spring.v = 0;
        this.lastTouch = now();
      },
      move: (dx) => {
        if (this.mode !== 'drag') return;
        this.spring.x = this.drag0 - dx / this.pxPerStep();
      },
      end: (vx) => {
        if (this.mode !== 'drag') return;
        this.lastTouch = now();
        const v = -vx / this.pxPerStep();            // steps per second
        const aim = Math.round(this.spring.x + clamp(v * 0.24, -3, 3));
        this.settle(aim, this.reduce ? 0 : v);
      },
    }, false);
    stage.addEventListener('click', this.onClick);
    stage.addEventListener('keydown', this.onKey);
    stage.addEventListener('focusin', this.onFocusIn);
    stage.addEventListener('focusout', this.onFocusOut);
    stage.addEventListener('pointerenter', this.onEnter);
    stage.addEventListener('pointerleave', this.onLeave);
    this.stopLoop = whileVisible(stage, loop((t, dt) => this.frame(t, dt)));
    this.frame(now(), 0);
  }

  applyGeo(): void {
    const g = this.geo;
    const s = this.stage.style;
    s.setProperty('--T', `${g.t.toFixed(1)}px`);
    s.setProperty('--P', `${g.p.toFixed(1)}px`);
    s.setProperty('--y0', `${g.y0.toFixed(1)}px`);
    s.setProperty('--up', `${g.up.toFixed(1)}px`);
    for (const b of this.tiles) b.querySelector('img')!.sizes = `${Math.ceil(g.t)}px`;
  }

  destroy(): void {
    this.stopLoop();
    this.unbind();
    this.ro.disconnect();
    this.stage.removeEventListener('click', this.onClick);
    this.stage.removeEventListener('keydown', this.onKey);
    this.stage.removeEventListener('focusin', this.onFocusIn);
    this.stage.removeEventListener('focusout', this.onFocusOut);
    this.stage.removeEventListener('pointerenter', this.onEnter);
    this.stage.removeEventListener('pointerleave', this.onLeave);
  }

  /** how many CSS px of a drag turn the ring one step (the front of the ring follows the finger) */
  pxPerStep(): number {
    const g = this.geo;
    const depth = g.p / (g.p + g.lift);
    return g.r * Math.sin(STEP * RAD) * depth * 1.15;
  }

  settle(aim: number, v: number): void {
    this.spring.target = aim;
    if (this.reduce) {
      this.spring.x = aim;
      this.spring.v = 0;
      this.mode = 'rest';
      return;
    }
    this.spring.v = v;
    this.mode = 'spring';
  }

  /** bring artwork position j (the one nearest the front that shows artwork i) to the front */
  bringArt(i: number): void {
    const j = this.positionOf(i);
    if (j === null) return;
    this.lastTouch = now();
    this.settle(j, 0);
  }

  positionOf(i: number): number | null {
    for (const [art, j] of this.placed) if (art === i) return j;
    return null;
  }

  onClick = (e: MouseEvent): void => {
    const b = (e.target as HTMLElement).closest<HTMLButtonElement>('.sx-tile');
    if (!b) return;
    const i = this.tiles.indexOf(b);
    if (i >= 0 && mod(this.front, N) !== i) this.bringArt(i);
  };

  onKey = (e: KeyboardEvent): void => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    if (!(e.target as HTMLElement).closest('.sx-tile')) return;
    e.preventDefault();
    const aim = Math.round(this.spring.target) + (e.key === 'ArrowRight' ? 1 : -1);
    this.lastTouch = now();
    this.settle(aim, 0);
    const i = mod(aim, N);
    this.setCurrent(i);
    this.tiles[i].focus({ preventScroll: true });
  };

  onFocusIn = (e: FocusEvent): void => {
    if ((e.target as HTMLElement).matches(':focus-visible')) this.holdAuto = true;
  };
  onFocusOut = (e: FocusEvent): void => {
    if (!this.stage.contains(e.relatedTarget as Node)) this.holdAuto = false;
  };
  onEnter = (e: PointerEvent): void => {
    if (e.pointerType === 'mouse') this.holdAuto = true;
  };
  onLeave = (e: PointerEvent): void => {
    if (e.pointerType === 'mouse' && !this.stage.contains(document.activeElement)) this.holdAuto = false;
  };

  setCurrent(i: number): void {
    if (i === this.current) return;
    this.tiles[this.current].tabIndex = -1;
    this.tiles[i].tabIndex = 0;
    this.current = i;
  }

  frame(t: number, dt: number): void {
    switch (this.mode) {
      case 'spring':
        this.spring.step(dt);
        if (this.spring.settled(0.002)) {
          this.spring.x = this.spring.target;
          this.spring.v = 0;
          this.mode = 'rest';
        }
        break;
      case 'auto':
        this.spring.x = this.auto.at(t);
        if (this.auto.done(t)) this.mode = 'rest';
        break;
      case 'rest':
        if (!this.reduce && !this.holdAuto && t - this.lastTouch > AUTO_AFTER && t >= this.nextAuto) {
          const from = this.spring.x;
          this.spring.target = Math.round(from) + 1;
          this.auto.set(from, this.spring.target, t, 1500, easeTurn);
          this.mode = 'auto';
          this.nextAuto = t + 1500 + AUTO_EVERY;
        }
        break;
      default:
        break;
    }
    if (this.mode !== 'rest' && this.mode !== 'auto') this.nextAuto = Math.max(this.nextAuto, t + AUTO_EVERY);
    this.place();
    this.caption(t);
  }

  /**
   * Put the artworks of the visible part of the ring in their places. Every style is written only when its own value changes (a tile's transform,
   * its opacity to a hundredth, its gold rim and glow to a twentieth, whether it can be tapped), and a tile the fog has hidden is not placed at all:
   * at rest nothing is written, while it turns about seven tiles are.
   */
  place(): void {
    const g = this.geo;
    const pos = this.spring.x;
    const front = Math.round(pos);
    const sinT = Math.sin(g.tilt * RAD);
    const cosT = Math.cos(g.tilt * RAD);
    const seen = new Set<number>();
    this.placed.clear();
    for (let j = front - SLOTS / 2 + 1; j <= front + SLOTS / 2; j++) {
      const i = mod(j, N);
      const th = (j - pos) * STEP;                         // degrees from the front
      const s = Math.sin(th * RAD);
      const c = Math.cos(th * RAD);
      const lift = Math.exp(-((th / 13) ** 2));
      const o = Math.max(lift, ((1 + c) / 2) ** 1.4 * smooth(112, 92, Math.abs(th)));
      if (o < 0.01) continue;
      seen.add(i);
      this.placed.set(i, j);
      const d = g.r * (c - 1);                             // how far back on the ring
      const x = g.r * s;
      const y = d * sinT + lift * g.up;
      const z = d * cosT - g.lift + lift * g.lift;
      const sc = mix(g.ring, 1, lift);
      // the artworks on the ring face out of it, as on a real display (a little less, so the ones at the sides stay readable)
      const ry = th * 0.8 * (1 - lift);
      const b = this.tiles[i];
      const st = this.st[i];
      const tr = `translate3d(${x.toFixed(2)}px,${y.toFixed(2)}px,${z.toFixed(2)}px) rotateY(${ry.toFixed(2)}deg) scale(${sc.toFixed(4)})`;
      if (tr !== st.tr) b.style.transform = st.tr = tr;
      const op = String(Math.round(o * 100) / 100);
      if (op !== st.op) b.style.opacity = st.op = op;
      if (st.vis !== '') b.style.visibility = st.vis = '';
      const pe = o < 0.2 ? 'none' : '';
      if (pe !== st.pe) b.style.pointerEvents = st.pe = pe;
      const lit = String(Math.round(lift ** 1.4 * 20) / 20);
      if (lit !== st.lit) {
        st.lit = lit;
        b.querySelector<HTMLElement>('.sx-rim')!.style.opacity = lit;
        b.querySelector<HTMLElement>('.sx-glow')!.style.opacity = lit;
      }
      if (!this.loaded[i] && Math.abs(th) < 125) {
        const img = b.querySelector('img')!;
        img.srcset = discSet(RING_ORDER[i]);
        img.src = pic(RING_ORDER[i], 240);
        this.loaded[i] = true;
      }
      // the artwork in front is drawn at its full size: it gets the sharp picture (480 px) once the ring has stopped with it there (not for every
      // artwork a swipe carries past), swapped in when decoded
      if (lift > 0.6 && this.mode === 'rest' && !this.sharp[i]) {
        this.sharp[i] = true;
        const big = new Image();
        big.src = pic(RING_ORDER[i], 480);
        big.decode().then(() => {
          const img = b.querySelector('img')!;
          img.srcset = '';
          img.src = big.src;
        }, () => undefined);
      }
    }
    for (let i = 0; i < N; i++) {
      const st = this.st[i];
      if (seen.has(i) || st.vis === 'hidden') continue;
      this.tiles[i].style.visibility = st.vis = 'hidden';
      st.tr = '';
    }
    if (front !== this.front) {
      this.front = front;
      this.setCurrent(mod(front, N));
    }
  }

  /** the words follow the front artwork: out, change, in */
  caption(t: number): void {
    const i = mod(this.front, N);
    if (i !== this.shown && this.wordsT.b === 1) {
      this.wordsT.set(this.wordsT.at(t), 0, t, this.reduce ? 60 : 140, easeOut);
    }
    if (this.wordsT.b === 0 && this.wordsT.done(t)) {
      this.shown = i;
      // the words, written straight into the page while they are invisible (no render of the component)
      const a = ART[RING_ORDER[i]];
      this.info.querySelector('.sx-name')!.textContent = a.name;
      this.info.querySelector('.sx-prov')!.textContent = this.words.prov[a.prov];
      this.wordsT.set(0, 1, t, this.reduce ? 120 : 320, easeOut);
    }
    const q = this.wordsT.at(t);
    const o = q.toFixed(3);
    if (o !== this.infoO) {
      this.infoO = o;
      this.info.style.opacity = o;
      this.info.style.transform = this.reduce ? '' : `translate3d(0,${((1 - q) * 6).toFixed(2)}px,0)`;
    }
    const pe = q > 0.5 ? 'auto' : 'none';
    if (pe !== this.infoPE) this.info.style.pointerEvents = this.infoPE = pe;
  }
}

export default function Ring({ words, onReady }: PieceProps) {
  const stage = useRef<HTMLDivElement>(null);
  const info = useRef<HTMLDivElement>(null);

  // the controller lives as long as the component; it reads the latest words and callback through this
  const props = useRef({ words, onReady });
  useLayoutEffect(() => {
    props.current = { words, onReady };
  });

  useEffect(() => {
    const ctl = new RingCtl(stage.current!, info.current!, props.current.words);
    let alive = true;
    const first = ctl.tiles.filter((_, i) => ctl.loaded[i]).map((b) => b.querySelector('img')!);
    decoded(first).then(() => {
      if (!alive) return;
      props.current.onReady?.();
      if (window.__sx) window.__sx.ready = true;
    });
    if (REC && window.__sx) {
      window.__sx.where = (id: string) => {
        // '@front', '@next' (the one to the right of the front), '@prev', or an artwork's id
        const i = id === '@front' ? mod(ctl.front, N) : id === '@next' ? mod(ctl.front + 1, N) : id === '@prev' ? mod(ctl.front - 1, N) : RING_ORDER.indexOf(id);
        if (i < 0) return null;
        const r = ctl.tiles[i].getBoundingClientRect();
        return { x: r.left + r.width / 2, y: r.top + r.height * 0.42 };
      };
      window.__sx.state = () => ({ mode: ctl.mode, pos: ctl.spring.x, front: RING_ORDER[mod(ctl.front, N)] });
    }
    return () => {
      alive = false;
      ctl.destroy();
    };
  }, []);

  const tiles = useMemo(
    () =>
      RING_ORDER.map((id, i) => {
        const a = ART[id];
        return (
          <button key={id} type="button" className="sx-tile" tabIndex={i === 0 ? 0 : -1} aria-label={`${a.name}, ${words.prov[a.prov]}`} style={{ visibility: 'hidden' } as CSSProperties}>
            <img alt="" draggable={false} decoding="async" />
            <span className="sx-glow" aria-hidden="true" />
            <span className="sx-rim" aria-hidden="true" />
          </button>
        );
      }),
    [words],
  );

  return (
    <div className="sx-stage sx-ring" ref={stage} role="group" aria-label={words.group}>
      <div className="sx-floor" aria-hidden="true" />
      <div className="sx-scene">
        <div className="sx-carousel">{tiles}</div>
      </div>
      <div className="sx-info" ref={info}>
        <Info art={ART[RING_ORDER[0]]} words={words} />
      </div>
    </div>
  );
}
