// The hero's globe, the interactive part (its own lazy chunk; the first screen paints its poster, src/landing/HeroScene.tsx, and src/landing/Hero.tsx
// fetches this when the hero is on screen and the browser is idle). A dark polished sphere set with 32 round artworks that turns slowly by itself; a
// drag or a swipe turns it in any direction and lets go with inertia, after which it rolls on slowly the way it was sent; a tapped artwork glides to
// the front, grows, and shows its style's name (the registry's), its honest label and one button to /try. Escape, a tap beside it or a new turn puts
// it back.
//
// MOTION SPEC EXCEPTION (the owner's choice of 2026-10-22): the landing's motion has no 3D (src/motion/motion.css); this piece is the one deliberate
// exception, a real CSS 3D scene (perspective, preserve-3d, rotations), confined to this folder and allowed by name in scripts/check_taste.mjs (rule
// "3D"). Its artworks are drawn on a turning sphere, so they are seen foreshortened as they turn; each one opens flat, whole and sharp on a tap.
//
// Printed on one sphere (the owner's review of 2026-10-23): every disc lies in the plane of the circle where its rim meets the sphere (a chord, sunk
// R (1 - cos 16.5 deg) under the surface), so no part of it is ever outside the ball and none can poke past the outline at the limb. A disc fades
// into the dark of the body as it turns away, by how squarely it faces the eye (the cosine of its tilt, with the perspective), and is gone before it
// is a sliver; one still layer over the whole sphere (the light from the upper left, the shadow and the soft rim at the limb) shades the discs and the
// body as one object.
//
// The turn: the orientation is a quaternion, so a drag turns the globe about the screen axis square to the finger's path, up, down and round
// included, with no flip at the poles. When the finger lets go the turn eases from its speed down to the calm idle speed (one turn a minute) and
// goes on about the same axis; nothing pulls it back to the equator.
//
// Why it is light on a phone:
//   * one transform per frame for the whole sphere (the orb); the 32 discs keep the transforms React gave them, so the browser only re-composites;
//   * the shading and the sheen are one still layer in front of it, the body and its gold edge one behind it, drawn once;
//   * a disc's fade and the front disc's gold rim and glow are opacities, in twentieths, written only when they change (a few discs a second);
//   * every disc's gold hairline is painted once with the disc; nothing is blurred and no shadow is repainted per frame;
//   * the opened artwork is a flat copy (the 480 px picture) that flies out of the disc's place, so it is sharp and the sphere stays untouched;
//   * a disc's picture is fetched when the disc comes near the visible half, the rest when the browser is idle.
// prefers-reduced-motion: nothing moves by itself and nothing flies: the still arrangement of the poster, a drag turns it only while the finger is
// on it, a tap opens the artwork in place (a fade).
// Keyboard: one tab stop; the arrows turn it (left and right along a row, up and down to the next row); Enter opens and puts the focus on the button;
// Escape closes and gives the focus back. Every artwork is a button labelled with its style's name and whose eyes it shows.
import { useLayoutEffect, useMemo, useRef, type CSSProperties } from 'react';
import './globe.css';
import { GLOBE_ART, GLOBE_ROWS, type GlobeArt, type GlobeProv } from '../globeArt';
import { styleName } from '../../shared/styles';
import { liveFor } from '../../shared/catalogue';
import { useCopy } from '../copy/useCopy';
import { useSaleCatalogue } from '../ordering';
import { useTryHref } from '../links';
import { globeUrl } from './assets.globe';
import {
  Tween, bindDrag, clamp, cssMatrix, decoded, easeInOut, easeOut, easeTurn, loop, mix, qAxis, qMat, qMul, qNorm, qSlerp, reducedMotion, smooth, whileVisible,
  type Quat,
} from './engine';

export interface GlobeProps {
  /** the pictures of the first view are decoded: the poster may go */
  onReady: () => void;
}

/** What the controller reads at the moment of a tap: the words (the landing's copy: the gallery's styles.soonTag, styles.eyeNote and styles.mixed),
 *  whether a style can be bought now for that many eyes (the run-time catalogue, as a tile of the gallery asks it; false: the opened artwork says
 *  Soon) and the callback. The component reads them itself (copy, catalogue and the link to /try), so the hero's code in the first load stays small. */
interface Live {
  soon: string;
  prov: Record<GlobeProv, string>;
  canBuy: (style: string, eyes: number) => boolean;
  onReady: () => void;
}

type Vec = [number, number, number];

const RAD = Math.PI / 180;
const DISC_DEG = 33;          // the angular diameter of a disc on the sphere (the rows are 36 degrees apart)
const SINK = Math.cos((DISC_DEG / 2) * RAD);   // a disc's plane from the centre, over the radius: its rim on the sphere, its middle just under it
const K = 4.4;                // the perspective distance over the radius
const REST_PITCH = -14;       // seen a little from above
const IDLE = 6;               // degrees per second: one turn a minute
const MAX_SPIN = 420;
const FLING = 0.7;            // a fling turns the globe a little less than the finger's speed: heavy, calm
const SETTLE = 0.45;          // seconds: how fast a fling eases down to the idle speed (about three of these to settle)
// a disc's fade by the cosine of its tilt to the eye: whole down to FADE_TO, gone at FADE_FROM (a disc less than about a quarter as wide as it is
// tall is never shown: no sliver at the limb)
const FADE_FROM = 0.22;
const FADE_TO = 0.5;
const PICK = 0.36;            // a disc this square to the eye (half faded or more) can be tapped; one further round cannot

const ART_BY_ID: Readonly<Record<string, GlobeArt>> = Object.fromEntries(GLOBE_ART.map((a) => [a.id, a]));

interface Disc {
  id: string;
  lon: number;
  lat: number;
  row: number;
  /** the unit normal in the sphere's own frame (x right, y down, z to the viewer) */
  n: Vec;
}

const DISCS: readonly Disc[] = GLOBE_ROWS.flatMap((r, row) =>
  r.ids.map((id, k) => {
    const lon = r.offset + (360 / r.ids.length) * k;
    const lat = r.lat;
    return { id, lon, lat, row, n: [Math.cos(lat * RAD) * Math.sin(lon * RAD), -Math.sin(lat * RAD), Math.cos(lat * RAD) * Math.cos(lon * RAD)] as Vec };
  }),
);

/** The first view (the poster's): seen a little from above, the first row's first disc at the front. */
const REST: Quat = qAxis(1, 0, 0, REST_PITCH);
/** The turn of the first view: about the sphere's own axis as the visitor sees it (tilted by REST_PITCH), so it turns like a globe on its stand. */
const REST_AXIS: Vec = [0, Math.cos(REST_PITCH * RAD), Math.sin(REST_PITCH * RAD)];

/** Disc i upright at the front: the orientation a keyboard turn or a tap glides to. */
const upright = (d: Disc): Quat => qMul(qAxis(1, 0, 0, clamp(-d.lat, -72, 72)), qAxis(0, 1, 0, -d.lon));

const discSet = (id: string) => `${globeUrl(id, 160)} 160w, ${globeUrl(id, 240)} 240w`;

/** The sizes of everything, from the stage's width and height (all of it scales with the stage, so the poster fits it at any size). */
function geometry(w: number, h: number) {
  const a = 0.43 * Math.min(w, h);                    // the radius the sphere appears to have
  const r = (a * Math.sqrt((K + 1) ** 2 - 1)) / K;     // its real radius at the perspective K * r
  const d = 2 * r * Math.sin((DISC_DEG / 2) * RAD);    // a disc, as large as it is drawn at the front
  // the opened artwork: about half the stage, and on a small stage (a short phone) at least 80 percent of its width up to 210 px, so it can still be looked at;
  // its words may then reach below the stage, over the veil's own continuation (open)
  const dh = Math.max(0.54 * Math.min(w, h * 0.94), Math.min(0.8 * w, 210));
  return { w, h, a, r, rc: r * SINK, p: K * r, d, cy: h * 0.5, dh, hy: Math.max(h * 0.4, dh / 2 + 10) };
}
type Geo = ReturnType<typeof geometry>;

const nearestTurn = (from: number, to: number) => from + ((((to - from) % 360) + 540) % 360) - 180;
const len = (v: Vec) => Math.hypot(v[0], v[1], v[2]);
/** the turn a drag of (dx, dy) px asks for: about the screen axis square to it, so the front of the sphere follows the finger */
const dragAxis = (dx: number, dy: number): Vec => {
  const l = Math.hypot(dx, dy) || 1;
  return [-dy / l, dx / l, 0];
};
/** in twentieths: a disc is repainted about twenty times as it crosses, not every frame */
const step20 = (v: number) => Math.round(v * 20) / 20;

class GlobeCtl {
  stage: HTMLElement;
  world: HTMLElement;
  orb: HTMLElement;
  discs: HTMLButtonElement[];
  hero: HTMLButtonElement;
  heroImg: HTMLImageElement;
  shade: HTMLElement;
  rim: HTMLElement;
  glow: HTMLElement;
  veil: HTMLElement;
  info: HTMLElement;
  live: () => Live;
  geo: Geo;
  reduce = reducedMotion();

  q: Quat = REST;
  m: number[] = qMat(REST);
  /** the turn now, as an axis of the screen times degrees per second */
  vel: Vec;
  /** the axis the globe turns about when it is left alone: the sphere's own at first, then the way the last drag sent it */
  axis: Vec = REST_AXIS;
  mode: 'idle' | 'drag' | 'coast' | 'turn' | 'open' | 'close' = 'idle';
  idleFrom = 0;           // the time the spin started to come back after a stop
  holdSpin = false;       // a disc has the keyboard focus: the globe keeps still
  last = { dx: 0, dy: 0 };
  turnFrom: Quat = REST;
  turnTo_: Quat = REST;
  turnT = new Tween();
  lit: number[];
  vis: number[];
  pick: boolean[];
  fetched: boolean[];
  current = 0;            // the disc that holds the tab stop
  focus = -1;             // the opened disc
  heroT = new Tween();    // 0 in the disc's place, 1 opened
  veilT = new Tween();
  infoT = new Tween();
  shadeFrom = 0;
  closing = false;
  refocus = -1;
  from = { x: 0, y: 0, sx: 1, sy: 1 };
  lastOrb = '';
  stopLoop: () => void;
  unbind: () => void;
  ro: ResizeObserver;

  constructor(els: { stage: HTMLElement; world: HTMLElement; orb: HTMLElement; hero: HTMLButtonElement; veil: HTMLElement; info: HTMLElement }, live: () => Live) {
    this.stage = els.stage;
    this.world = els.world;
    this.orb = els.orb;
    this.hero = els.hero;
    this.heroImg = els.hero.querySelector('img')!;
    this.shade = els.hero.querySelector<HTMLElement>('.lp-gl-open-shade')!;
    this.rim = els.hero.querySelector<HTMLElement>('.lp-gl-open-rim')!;
    this.glow = els.hero.querySelector<HTMLElement>('.lp-gl-open-glow')!;
    this.veil = els.veil;
    this.info = els.info;
    this.live = live;
    this.discs = [...els.orb.querySelectorAll<HTMLButtonElement>('.lp-gl-disc')];
    this.lit = DISCS.map(() => -1);
    this.vis = DISCS.map(() => -1);
    this.pick = DISCS.map(() => true);
    this.fetched = DISCS.map(() => false);
    this.vel = this.reduce ? [0, 0, 0] : [REST_AXIS[0] * IDLE, REST_AXIS[1] * IDLE, REST_AXIS[2] * IDLE];
    this.geo = geometry(this.stage.clientWidth, this.stage.clientHeight);
    this.applyGeo();
    this.ro = new ResizeObserver(() => {
      this.geo = geometry(this.stage.clientWidth, this.stage.clientHeight);
      this.applyGeo();
      this.lastOrb = '';
    });
    this.ro.observe(this.stage);
    this.unbind = bindDrag(this.stage, {
      begin: () => {
        if (this.focus >= 0) this.close(true);
        this.mode = 'drag';
        this.last = { dx: 0, dy: 0 };
      },
      move: (dx, dy) => {
        if (this.mode !== 'drag') return;
        const ix = dx - this.last.dx;
        const iy = dy - this.last.dy;
        this.last = { dx, dy };
        const l = Math.hypot(ix, iy);
        if (l < 0.01) return;
        const ax = dragAxis(ix, iy);
        this.q = qNorm(qMul(qAxis(ax[0], ax[1], ax[2], (l * 180) / Math.PI / this.geo.r), this.q));
      },
      end: (vx, vy) => {
        if (this.mode !== 'drag') return;
        // the way it goes on: the finger's last direction, or the whole drag's when the finger stopped before it let go
        const v = Math.hypot(vx, vy);
        const total = Math.hypot(this.last.dx, this.last.dy);
        if (v > 40) this.axis = dragAxis(vx, vy);
        else if (total > 4) this.axis = dragAxis(this.last.dx, this.last.dy);
        const speed = this.reduce || v <= 40 ? 0 : Math.min(MAX_SPIN, ((v * 180) / Math.PI / this.geo.r) * FLING);
        this.vel = [this.axis[0] * speed, this.axis[1] * speed, this.axis[2] * speed];
        this.mode = 'coast';
      },
    });
    this.stage.addEventListener('click', this.onClick);
    this.stage.addEventListener('keydown', this.onKey);
    document.addEventListener('keydown', this.onEscape);
    this.stage.addEventListener('focusin', this.onFocusIn);
    this.stage.addEventListener('focusout', this.onFocusOut);
    this.stopLoop = whileVisible(this.stage, loop((t, dt) => this.frame(t, dt)));
    this.frame(performance.now(), 0);
  }

  applyGeo(): void {
    const g = this.geo;
    const s = this.stage.style;
    s.setProperty('--R', `${g.r.toFixed(2)}px`);
    s.setProperty('--Rc', `${g.rc.toFixed(2)}px`);
    s.setProperty('--P', `${g.p.toFixed(1)}px`);
    s.setProperty('--D', `${g.d.toFixed(2)}px`);
    s.setProperty('--A', `${g.a.toFixed(2)}px`);
    s.setProperty('--cy', `${g.cy.toFixed(1)}px`);
    s.setProperty('--Dh', `${g.dh.toFixed(1)}px`);
    s.setProperty('--hy', `${g.hy.toFixed(1)}px`);
    // the pictures are given only once the size of a disc is known, so the browser picks one width (160 or 240 px), never both
    for (const b of this.discs) b.querySelector('img')!.sizes = `${Math.ceil(g.d)}px`;
  }

  /** a disc's picture is fetched when the disc comes near the visible half (light) or when the browser is idle after the first view */
  fetchPic(i: number): void {
    if (this.fetched[i]) return;
    this.fetched[i] = true;
    const img = this.discs[i].querySelector('img')!;
    img.srcset = discSet(DISCS[i].id);
    img.src = globeUrl(DISCS[i].id, 240);
  }

  fetchRest(): void {
    for (let i = 0; i < DISCS.length; i++) this.fetchPic(i);
  }

  destroy(): void {
    this.stopLoop();
    this.unbind();
    this.ro.disconnect();
    this.stage.removeEventListener('click', this.onClick);
    this.stage.removeEventListener('keydown', this.onKey);
    document.removeEventListener('keydown', this.onEscape);
    this.stage.removeEventListener('focusin', this.onFocusIn);
    this.stage.removeEventListener('focusout', this.onFocusOut);
  }

  /** the normal of disc i as seen now (the orb's rotation applied) */
  facing(i: number): Vec {
    const [x, y, z] = DISCS[i].n;
    const m = this.m;
    return [m[0] * x + m[1] * y + m[2] * z, m[3] * x + m[4] * y + m[5] * z, m[6] * x + m[7] * y + m[8] * z];
  }

  /** how squarely disc i faces the eye: the cosine of the angle between its normal and the line to the eye (the perspective included); its width
   *  as it is seen, over its height, is about this */
  square(f: Vec): number {
    const g = this.geo;
    const ex = -g.rc * f[0];
    const ey = -g.rc * f[1];
    const ez = g.p + g.r - g.rc * f[2];
    return (f[0] * ex + f[1] * ey + f[2] * ez) / Math.hypot(ex, ey, ez);
  }

  /**
   * Where disc i is on the stage and how large it looks, from the same geometry the browser draws with (the perspective projection of the disc's
   * centre; a disc turned away is an ellipse, narrower along the direction it turns). No layout is read: a tap costs no forced reflow.
   * Sets the flight's starting point and returns the disc's centre on the stage.
   */
  flyFrom(i: number): { cx: number; cy: number } {
    const g = this.geo;
    const [x, y, z] = this.facing(i);
    const depth = g.rc * z - g.r;
    const k = g.p / (g.p - depth);
    const cx = g.w / 2 + g.rc * x * k;
    const cy = g.cy + g.rc * y * k;
    const size = g.d * k;
    this.from = { x: cx - g.w / 2, y: cy - g.hy, sx: Math.max(0.05, (size * Math.sqrt(Math.max(0, 1 - x * x))) / g.dh), sy: Math.max(0.05, (size * Math.sqrt(Math.max(0, 1 - y * y))) / g.dh) };
    return { cx, cy };
  }

  /** glide to disc i upright at the front */
  turnTo(i: number, t: number, dur: number): void {
    const q = upright(DISCS[i]);
    if (this.reduce || dur <= 0) {
      this.q = q;
      this.turnFrom = q;
      this.turnTo_ = q;
      this.turnT.set(1, 1, t, 1);
      return;
    }
    this.turnFrom = this.q;
    this.turnTo_ = q;
    this.turnT.set(0, 1, t, dur, easeTurn);
  }

  onClick = (e: MouseEvent): void => {
    const target = e.target as HTMLElement;
    if (target.closest('.lp-gl-info')) return;
    if (this.focus >= 0) {
      if (this.mode === 'open') this.close(false);
      return;
    }
    const b = target.closest<HTMLButtonElement>('.lp-gl-disc');
    if (!b) return;
    const i = this.discs.indexOf(b);
    if (i >= 0) this.open(i, e.detail === 0);
  };

  /** Escape closes the opened artwork wherever the focus is: a click or a tap opens it without moving the focus, and the tapped disc, hidden under
   *  the flying copy, loses it (the focus is then on the page itself) */
  onEscape = (e: KeyboardEvent): void => {
    if (e.key !== 'Escape' || this.focus < 0 || this.closing) return;
    e.preventDefault();
    // the disc is hidden under the flying copy until it lands: the focus goes back to it then (finishClose)
    this.refocus = this.focus;
    this.close(false);
  };

  onKey = (e: KeyboardEvent): void => {
    const b = (e.target as HTMLElement).closest<HTMLButtonElement>('.lp-gl-disc');
    if (!b) return;
    const i = this.discs.indexOf(b);
    let next = -1;
    const d = DISCS[i];
    const inRow = DISCS.map((x, k) => [x, k] as const).filter(([x]) => x.row === d.row);
    const at = inRow.findIndex(([, k]) => k === i);
    if (e.key === 'ArrowRight') next = inRow[(at + 1) % inRow.length][1];
    else if (e.key === 'ArrowLeft') next = inRow[(at - 1 + inRow.length) % inRow.length][1];
    else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      const lats = [...new Set(DISCS.map((x) => x.lat))].sort((p, q) => p - q);
      const li = lats.indexOf(d.lat) + (e.key === 'ArrowUp' ? 1 : -1);
      if (li >= 0 && li < lats.length) {
        let best = -1;
        let bd = 999;
        DISCS.forEach((x, k) => {
          if (x.lat !== lats[li]) return;
          const dd = Math.abs(nearestTurn(d.lon, x.lon) - d.lon);
          if (dd < bd) {
            bd = dd;
            best = k;
          }
        });
        next = best;
      }
    }
    if (next < 0) return;
    e.preventDefault();
    this.setCurrent(next);
    this.discs[next].focus({ preventScroll: true });
    this.mode = 'turn';
    this.turnTo(next, performance.now(), 620);
  };

  onFocusIn = (e: FocusEvent): void => {
    // only a keyboard visitor's focus holds the globe still (a tap or a click also focuses the button, and the spin must come back after it)
    const el = e.target as HTMLElement;
    if (el.classList.contains('lp-gl-disc') && el.matches(':focus-visible')) this.holdSpin = true;
  };
  onFocusOut = (e: FocusEvent): void => {
    if (!this.stage.contains(e.relatedTarget as Node)) this.holdSpin = false;
  };

  setCurrent(i: number): void {
    if (i === this.current) return;
    this.discs[this.current].tabIndex = -1;
    this.discs[i].tabIndex = 0;
    this.current = i;
  }

  open(i: number, keyboard: boolean): void {
    const t = performance.now();
    const g = this.geo;
    const { cx, cy } = this.flyFrom(i);
    // how dark the shading made the disc where it was (the flat copy starts as dark and clears)
    this.shadeFrom = 0.85 * smooth(0.5, 1, Math.hypot(cx - g.w / 2, cy - g.cy) / g.a);
    const img = this.discs[i].querySelector('img')!;
    this.heroImg.src = img.currentSrc || img.src;
    const id = DISCS[i].id;
    const sharp = new Image();
    sharp.src = globeUrl(id, 480);
    sharp.decode().then(() => {
      if (this.focus === i) this.heroImg.src = sharp.src;
    }, () => undefined);
    this.focus = i;
    this.setCurrent(i);
    // the words of the opened artwork, written straight into the page (no render of the component at the moment of the tap): the registry's name,
    // Soon while the run-time catalogue cannot sell that style for that many eyes (as a tile of the gallery says it), and whose eyes they are. The
    // words and their button are inert while closed (not in the tab order, not read out): they wake before the name is written, so it is announced
    this.info.inert = false;
    const p = this.live();
    const a = ART_BY_ID[id];
    this.info.querySelector('.lp-gl-name')!.textContent = styleName(a.style);
    const soon = this.info.querySelector<HTMLElement>('.lp-gl-soon')!;
    soon.textContent = p.soon;
    soon.hidden = p.canBuy(a.style, a.eyes);
    this.info.querySelector('.lp-gl-prov')!.textContent = p.prov[a.prov];
    this.discs[i].style.visibility = 'hidden';
    this.hero.style.visibility = 'visible';
    this.hero.tabIndex = 0;
    this.veil.style.pointerEvents = 'auto';
    this.info.style.pointerEvents = 'auto';
    // where the words end (one layout read, at the tap): on a small stage (a short phone) they reach below it, and the veil then goes on down over the rest of
    // the first screen (--low, globe.css; the hero clips it at its foot), so they are read on the page's dark and nothing of the copy shows through them
    const below = g.hy + g.dh / 2 + 16 + this.info.offsetHeight + 12 - g.h;
    this.stage.style.setProperty('--low', below > 0 ? '200vh' : '0px');
    this.mode = 'open';
    this.closing = false;
    this.vel = [0, 0, 0];
    if (this.reduce) {
      this.turnFrom = this.q;
      this.turnTo_ = this.q;
      this.turnT.set(1, 1, t, 1);
      this.heroT.set(1, 1, t, 1);
      this.veilT.set(0, 1, t, 180, easeOut);
      this.infoT.set(0, 1, t, 180, easeOut);
    } else {
      this.turnTo(i, t, 900);
      this.heroT.set(0, 1, t, 720, easeOut);
      this.veilT.set(0, 1, t, 520, easeOut);
      this.infoT.set(0, 1, t + 260, 520, easeOut);
    }
    if (keyboard) {
      // a keyboard visitor lands on the button; Escape or the opened artwork brings them back
      setTimeout(() => this.info.querySelector<HTMLElement>('a')?.focus({ preventScroll: true }), this.reduce ? 0 : 300);
    }
  }

  close(fast: boolean): void {
    if (this.focus < 0 || this.closing) return;
    this.closing = true;
    const t = performance.now();
    this.flyFrom(this.focus);
    this.shadeFrom = 0;
    const dur = this.reduce ? 150 : fast ? 240 : 560;
    if (this.reduce) this.heroT.set(1, 1, t, 1);
    else this.heroT.set(this.heroT.at(t), 0, t, dur, easeInOut);
    this.veilT.set(this.veilT.at(t), 0, t, dur, easeOut);
    this.infoT.set(this.infoT.at(t), 0, t, Math.min(dur, 220), easeOut);
    this.hero.tabIndex = -1;
    this.veil.style.pointerEvents = '';
    this.info.style.pointerEvents = '';
    // the words go inert at once, unless the focus is on their button (Escape from it): then when the disc has landed and has the focus again
    if (!this.info.contains(document.activeElement)) this.info.inert = true;
    if (this.mode !== 'drag') this.mode = 'close';
  }

  /** turn the globe by the velocity for s seconds */
  spin(s: number): void {
    const v = this.vel;
    const speed = len(v);
    if (speed * s < 1e-5) return;
    this.q = qNorm(qMul(qAxis(v[0] / speed, v[1] / speed, v[2] / speed, speed * s), this.q));
  }

  frame(t: number, dt: number): void {
    const s = dt / 1000;
    const idle = this.reduce || this.holdSpin || this.focus >= 0 ? 0 : IDLE;
    switch (this.mode) {
      case 'idle':
      case 'coast': {
        // after a stop the spin comes back over about 1.5 s (and at the start: the first frame is the poster's still arrangement); after a fling the
        // turn eases from the finger's speed to the idle speed about the axis it was sent along, and stays on that axis
        const goal = idle * (this.mode === 'idle' ? smooth(0, 1500, t - this.idleFrom) : 1);
        const e = 1 - Math.exp(-s / (this.mode === 'idle' ? 0.35 : SETTLE));
        const a = this.axis;
        this.vel = [mix(this.vel[0], a[0] * goal, e), mix(this.vel[1], a[1] * goal, e), mix(this.vel[2], a[2] * goal, e)];
        this.spin(s);
        if (this.mode === 'coast' && len([this.vel[0] - a[0] * goal, this.vel[1] - a[1] * goal, this.vel[2] - a[2] * goal]) < 0.5) {
          this.mode = 'idle';
          this.idleFrom = t - 1500;
        }
        break;
      }
      case 'turn':
      case 'open': {
        this.q = qSlerp(this.turnFrom, this.turnTo_, this.turnT.at(t));
        this.vel = [0, 0, 0];
        if (this.mode === 'turn' && this.turnT.done(t)) {
          this.mode = 'idle';
          this.idleFrom = t;
        }
        break;
      }
      default:
        break;
    }
    this.m = qMat(this.q);
    const orb = `translate3d(0,0,${(-this.geo.r).toFixed(2)}px) ${cssMatrix(this.m)}`;
    if (orb !== this.lastOrb) {
      this.orb.style.transform = orb;
      this.lastOrb = orb;
      this.light();
    }
    if (this.focus >= 0) {
      this.paintFocus(t);
      if (this.closing && this.heroT.done(t) && this.veilT.done(t)) {
        this.finishClose();
        if (this.mode === 'close') {
          this.mode = 'idle';
          this.idleFrom = t;
        }
      }
    }
  }

  /** each disc's fade toward the limb, the gold rim and glow of the discs at the front, which discs can be tapped (none that is turned away), and
   *  which pictures to fetch */
  light(): void {
    for (let i = 0; i < DISCS.length; i++) {
      const f = this.facing(i);
      if (f[2] > -0.45) this.fetchPic(i);
      const c = this.square(f);
      const vis = step20(smooth(FADE_FROM, FADE_TO, c));
      if (vis !== this.vis[i]) {
        this.vis[i] = vis;
        this.discs[i].style.opacity = vis === 1 ? '' : String(vis);
      }
      const lit = step20(smooth(0.9, 0.995, c));
      if (lit !== this.lit[i]) {
        this.lit[i] = lit;
        this.discs[i].style.setProperty('--lit', String(lit));
      }
      const pick = c > PICK;
      if (pick !== this.pick[i]) {
        this.pick[i] = pick;
        this.discs[i].style.pointerEvents = pick ? '' : 'none';
      }
    }
  }

  paintFocus(t: number): void {
    const p = this.heroT.at(t);
    const f = this.from;
    const x = f.x * (1 - p);
    const y = f.y * (1 - p);
    this.hero.style.transform = `translate3d(${x.toFixed(2)}px,${y.toFixed(2)}px,0) scale(${mix(f.sx, 1, p).toFixed(4)},${mix(f.sy, 1, p).toFixed(4)})`;
    const o = p.toFixed(3);
    this.rim.style.opacity = o;
    this.glow.style.opacity = o;
    this.shade.style.opacity = (this.shadeFrom * (1 - p)).toFixed(3);
    const v = this.veilT.at(t);
    if (this.reduce) this.hero.style.opacity = v.toFixed(3);
    this.veil.style.opacity = v.toFixed(3);
    // the whole sphere (body, discs, shading) recedes into the dark as one picture behind the opened artwork: an even dimming with no edge of its own
    this.world.style.opacity = mix(1, 0.22, v).toFixed(3);
    const q = this.infoT.at(t);
    this.info.style.opacity = q.toFixed(3);
    this.info.style.transform = this.reduce ? '' : `translate3d(0,${((1 - q) * 10).toFixed(2)}px,0)`;
  }

  finishClose(): void {
    if (this.focus < 0) return;
    this.discs[this.focus].style.visibility = '';
    this.hero.style.visibility = 'hidden';
    this.hero.style.transform = '';
    this.veil.style.opacity = '0';
    this.world.style.opacity = '';
    this.info.style.opacity = '0';
    if (this.refocus === this.focus) this.discs[this.focus].focus({ preventScroll: true });
    this.info.inert = true;
    this.refocus = -1;
    this.focus = -1;
    this.closing = false;
  }
}

function Arrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export default function Globe({ onReady }: GlobeProps) {
  const { c } = useCopy();
  const sale = useSaleCatalogue();
  const tryHref = useTryHref();
  const h = c.hero;
  // whose eyes an artwork shows: the gallery's own words for it
  const prov = useMemo<Record<GlobeProv, string>>(() => ({ own: c.styles.eyeNote.own, licensed: c.styles.eyeNote.other, mixed: c.styles.mixed }), [c]);
  const stage = useRef<HTMLDivElement>(null);
  const world = useRef<HTMLDivElement>(null);
  const orb = useRef<HTMLDivElement>(null);
  const hero = useRef<HTMLButtonElement>(null);
  const veil = useRef<HTMLDivElement>(null);
  const info = useRef<HTMLDivElement>(null);
  // the controller lives as long as the component; it reads the latest words, catalogue and callback through this
  const live = (): Live => ({ soon: c.styles.soonTag, prov, canBuy: (style, eyes) => liveFor(sale, style, eyes), onReady });
  const latest = useRef(live);
  useLayoutEffect(() => {
    latest.current = live;
  });

  // before the browser paints the new markup: the sizes (custom properties of the stage) and the first view are written in the same frame, so nothing is
  // ever laid out without them (a frame without them would move every layer of the globe once: a layout shift)
  useLayoutEffect(() => {
    const ctl = new GlobeCtl({ stage: stage.current!, world: world.current!, orb: orb.current!, hero: hero.current!, veil: veil.current!, info: info.current! }, () => latest.current());
    const first = DISCS.map((_, i) => i).filter((i) => ctl.fetched[i]).map((i) => ctl.discs[i].querySelector('img')!);
    let alive = true;
    let idle = 0;
    decoded(first).then(() => {
      if (!alive) return;
      latest.current().onReady();
      // the far side when the browser has a moment (a fling must not meet empty discs)
      idle = window.setTimeout(() => ctl.fetchRest(), 1500);
    });
    return () => {
      alive = false;
      clearTimeout(idle);
      ctl.destroy();
    };
  }, []);

  const discs = useMemo(
    () =>
      DISCS.map((d, i) => {
        const a = ART_BY_ID[d.id];
        return (
          <button
            key={d.id}
            type="button"
            className="lp-gl-disc"
            tabIndex={i === 0 ? 0 : -1}
            aria-label={`${styleName(a.style)}, ${prov[a.prov]}`}
            style={{ transform: `rotateY(${d.lon}deg) rotateX(${d.lat}deg) translateZ(var(--Rc))` } as CSSProperties}
          >
            <span className="lp-gl-glow" aria-hidden="true" />
            <img alt="" width={240} height={240} draggable={false} decoding="async" />
            <span className="lp-gl-rim" aria-hidden="true" />
          </button>
        );
      }),
    [prov],
  );

  return (
    <div className="lp-gl" ref={stage} role="group" aria-label={h.globeLabel}>
      <div className="lp-gl-world" ref={world}>
        <div className="lp-gl-body" aria-hidden="true" />
        <div className="lp-gl-scene">
          <div className="lp-gl-orb" ref={orb}>
            {discs}
          </div>
        </div>
        <div className="lp-gl-fog" aria-hidden="true" />
      </div>
      <div className="lp-gl-veil" ref={veil} aria-hidden="true" />
      <button type="button" className="lp-gl-open" ref={hero} tabIndex={-1} aria-label={h.globeClose}>
        <img alt="" width={480} height={480} draggable={false} decoding="async" />
        <span className="lp-gl-open-glow" aria-hidden="true" />
        <span className="lp-gl-open-shade" aria-hidden="true" />
        <span className="lp-gl-open-rim" aria-hidden="true" />
      </button>
      <div className="lp-gl-info" ref={info} inert>
        <p className="lp-gl-name" aria-live="polite">{' '}</p>
        <p className="lp-gl-chips">
          <span className="lp-gl-soon" hidden />
          <span className="lp-gl-prov">{' '}</span>
        </p>
        <a className="lp-btn lp-btn-gold gold-metal lp-gl-cta" href={tryHref}>
          <span>{h.globeTry}</span>
          <Arrow />
        </a>
      </div>
    </div>
  );
}
