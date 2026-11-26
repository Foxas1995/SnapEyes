import React, { useEffect, useRef, useState } from 'react';
import { T } from './copy';

// The waiting screens' slideshow (the owner on his phone, 2026-11-26: "it could show something, other eyes, effects, a slow motion slide show, so that
// waiting is interesting"): finished artworks of the landing's own examples, one at a time, a slow cross-fade and a very slow zoom, about 4 s each, looping.
// It never slows the real work: nothing loads until the page has sent its first /api/analyze (analyzeSent, called by TryApp's post), the pictures load one at
// a time (the next while the current one shows), decode off the main thread, and the square is reserved so nothing moves. A picture that fails is skipped.
// Under prefers-reduced-motion: one still picture. The show is kept where it was (module state) when the page goes from one waiting step to the next.

/** The landing's example artworks (public/assets/landing/art, 480 px webp, all under 40 KB): clean eyes, one style each, a pair among them. The content hash
 *  is the file's own (src/landing/assets.ts); a test holds the two equal. */
export const SLIDES = [
  ['powder_br_480', '86e47a817d'],
  ['splash_gr_480', 'ae704210a6'],
  ['radiance_yg_480', '6e92f7d95a'],
  ['supernova1_br_480', '728bc7849f'],
  ['galaxy_gr_480', 'ecf4a33cbf'],
  ['duo_radiance_go_480', '14fb19a78f'],
  ['universe_yg_480', '6d94ae6523'],
  ['duo_supernova_gd_480', '769c0b17a8'],
] as const;
export const slideUrl = (i: number) => `/assets/landing/art/${SLIDES[i][0]}.${SLIDES[i][1]}.webp`;

export const SHOW_MS = 4200;      // one picture on screen
const FADE_MS = 1400;             // the cross-fade
const ZOOM = 1.08;                // the slow zoom over a picture's time

// the gate: the first analysis has left the page (TryApp's post calls analyzeSent), so the pictures never compete with it
let sent = false;
const waiting = new Set<() => void>();
export function analyzeSent(): void {
  if (sent) return;
  sent = true;
  waiting.forEach((f) => f());
  waiting.clear();
}
const afterSent = (): Promise<void> => (sent ? Promise.resolve() : new Promise((r) => { waiting.add(r); }));

let at = 0;                       // the picture the show is on: a remount goes on from here, it never restarts from the first

/** Load and decode one picture; null when it cannot be read (it is skipped). */
async function load(i: number): Promise<string | null> {
  const url = slideUrl(i);
  try {
    const img = new Image();
    img.decoding = 'async';
    img.src = url;
    await img.decode();
    return url;
  } catch {
    return null;
  }
}

const Layer: React.FC<{ src: string; still: boolean }> = ({ src, still }) => {
  const ref = useRef<HTMLImageElement>(null);
  const [on, setOn] = useState(still);
  useEffect(() => {
    if (still) return;
    const t = window.setTimeout(() => setOn(true), 30);
    const a = ref.current?.animate?.([{ transform: 'scale(1)' }, { transform: `scale(${ZOOM})` }], { duration: SHOW_MS + FADE_MS, easing: 'linear', fill: 'forwards' });
    return () => { window.clearTimeout(t); a?.cancel(); };
  }, [still]);
  return (
    <img ref={ref} src={src} alt="" aria-hidden="true" draggable={false}
      className="absolute inset-0 w-full h-full object-contain select-none"
      style={{ opacity: on ? 1 : 0, transition: still ? undefined : `opacity ${FADE_MS}ms ease-in-out` }} />
  );
};

/** The slideshow with its one line. size: the square's side as a CSS length (the page keeps the progress above it on the first screen). */
export const Slideshow: React.FC<{ size: string }> = ({ size }) => {
  const [layers, setLayers] = useState<{ id: number; src: string }[]>([]);
  const still = typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  useEffect(() => {
    let alive = true;
    let id = 0;
    let timer = 0;
    (async () => {
      await afterSent();
      let misses = 0;
      let next: Promise<string | null> = load(at);
      for (;;) {
        const src = await next;
        if (!alive) return;
        const shown = at;
        at = (at + 1) % SLIDES.length;
        if (!src) {
          if (++misses >= SLIDES.length) return;      // nothing can be read: show nothing
          next = load(at);
          continue;
        }
        misses = 0;
        id += 1;
        const layer = { id, src };
        setLayers((l) => [...l.slice(-1), layer]);
        if (still) { at = shown; return; }             // one still picture, no loop
        next = load(at);                               // the next one loads while this one shows
        await new Promise<void>((r) => { timer = window.setTimeout(r, SHOW_MS); });
        if (!alive) return;
      }
    })();
    return () => { alive = false; window.clearTimeout(timer); };
  }, [still]);
  return (
    <div data-testid="slideshow" className="flex flex-col items-center gap-2">
      <p className="text-xs text-zinc-300">{T.working.slidesLine}</p>
      <div className="relative overflow-hidden rounded-2xl bg-black" style={{ width: size, height: size }}>
        {layers.map((l) => <Layer key={l.id} src={l.src} still={still} />)}
      </div>
    </div>
  );
};
