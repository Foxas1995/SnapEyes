import React, { useEffect, useRef, useState } from 'react';
import { NO_SAVE, NO_SAVE_BOX, NO_SAVE_IMG_STYLE } from '../try/noSave';
import { PAD, PUPIL_CUT, entersSnap, keyCut, maskCss, snapCut, sweepFor, toggleCut, valueText, type Geometry } from './revealMath';

/** prefers-reduced-motion, with an override for tests and the prototype (?rm=1). */
export function usePrefersReducedMotion(force?: boolean): boolean {
  const [rm, setRm] = useState<boolean>(() => force ?? (typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches));
  useEffect(() => {
    if (force !== undefined) { setRm(force); return; }
    const mq = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    if (!mq) return;
    const on = () => setRm(mq.matches);
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [force]);
  return rm;
}

/** The restored iris on the frame circle: a square wrapper exactly the disc's bounding square (side 2 R_f), the restored image
 *  (the clean restoration on the landing, the watermarked display copy on /try: a square in which the iris radius is 1 / (2 PAD)
 *  of the side) 1.12 times that square, centred on it, and the restored edge as a radial mask. Nothing is drawn around it. */
export const RestoredDisc: React.FC<{ src: string; g: Geometry; alt: string }> = ({ src, g, alt }) => {
  const mask = maskCss(g.disc.e0, g.disc.e1);
  const ia = g.disc.ia || 1;                                      // an oval iris (horse): the wrapper is the ellipse's bounding box, the mask an ellipse
  const offX = `${(-(PAD - 1) / 2) * 100}%`;
  const offY = `${((1 - PAD * ia) / 2) * 100}%`;
  return (
    <div className="absolute pointer-events-none" style={{ left: `${g.disc.left}%`, top: `${g.disc.top}%`, width: `${g.disc.w}%`, aspectRatio: `${ia} / 1`, maskImage: mask, WebkitMaskImage: mask }}>
      <img {...NO_SAVE} src={src} alt={alt} decoding="async"
        style={{ ...NO_SAVE_IMG_STYLE, position: 'absolute', left: offX, top: offY, width: `${PAD * 100}%`, height: `${PAD * ia * 100}%`, maxWidth: 'none' }} />
    </div>
  );
};

/** The words of the page language: the pills, the slider's name and its spoken value (a template with {n} for the percent of the frame the photo takes). */
export interface RevealLabels { photo: string; iris: string; slider: string; valueText: string }

interface Props {
  photo: string;                  // the wide frame (data URL from wideFrame(), or the tight crop)
  restored: string;               // the restored iris image: the display copy (prepared and watermarked by the server) on /try, a clean example on the landing
  geometry: Geometry;
  labels: RevealLabels;
  ready?: boolean;                // both layers decoded: the arrival sweep starts then
  reducedMotion?: boolean;        // test / prototype override
  onCut?: (pos: number) => void;
  className?: string;
}

/** The Reveal: left of a hard cut the customer's own photo, right of it the restored iris on black, registered, the cut through
 *  the pupil centre. Arrival sweep 100 % -> 50 % (900 ms after 400 ms), drag with snapping, keys, double tap; no stroke, no glow. */
export const Reveal: React.FC<Props> = ({ photo, restored, geometry, labels, ready = true, reducedMotion, onCut, className = '' }) => {
  const rm = usePrefersReducedMotion(reducedMotion);
  const [pos, setPos] = useState<number>(() => (rm ? PUPIL_CUT : 100));
  const [sweeping, setSweeping] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [hot, setHot] = useState(false);          // hover or focus
  const [pills, setPills] = useState(true);
  const box = useRef<HTMLDivElement>(null);
  const last = useRef({ t: 0, x: 0, moved: 0, down: 0, pre: PUPIL_CUT });
  const posRef = useRef(pos);
  posRef.current = pos;

  const move = (p: number) => {
    if (entersSnap(posRef.current, p)) { try { navigator.vibrate?.(10); } catch { /* no haptics */ } }
    setPos(p);
    onCut?.(p);
  };

  // arrival sweep: when both layers have decoded, wait 400 ms, then 900 ms from all photo to the pupil cut (compositor only)
  useEffect(() => {
    if (!ready) return;
    const sw = sweepFor(rm);
    if (sw.durationMs === 0) { setPos(sw.to); return; }
    setPos(sw.from);
    const t1 = window.setTimeout(() => { setSweeping(true); setPos(sw.to); }, sw.delayMs);
    const t2 = window.setTimeout(() => setSweeping(false), sw.delayMs + sw.durationMs + 60);
    return () => { window.clearTimeout(t1); window.clearTimeout(t2); };
  }, [ready, rm]);

  // the pills ("Your photo" / "Your iris") fade out three seconds after the picture has settled
  useEffect(() => {
    if (!ready) return;
    const t = window.setTimeout(() => setPills(false), (rm ? 0 : 1360) + 3000);
    return () => window.clearTimeout(t);
  }, [ready, rm]);

  const cutFromX = (clientX: number) => {
    const el = box.current;
    if (!el) return posRef.current;
    const r = el.getBoundingClientRect();
    return snapCut(((clientX - r.left) / r.width) * 100);
  };

  const onDown = (e: React.PointerEvent<HTMLDivElement>) => {
    const now = performance.now();
    // a double tap (two quick taps that did not move) toggles pupil cut / all photo / all restored, counted from where the cut
    // was before the first tap moved it
    if (now - last.current.t < 320 && Math.abs(e.clientX - last.current.x) < 24) {
      last.current.t = 0; last.current.moved = 99;      // the second tap is consumed: it arms nothing
      setSweeping(false);
      move(toggleCut(last.current.pre));
      return;
    }
    try { (e.currentTarget as Element).setPointerCapture?.(e.pointerId); } catch { /* a synthetic or ended pointer: no capture */ }
    setSweeping(false); setDragging(true); setPills(true);
    last.current.down = e.clientX; last.current.moved = 0; last.current.pre = posRef.current;
    move(cutFromX(e.clientX));
  };
  const onMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging) return;
    last.current.moved = Math.max(last.current.moved, Math.abs(e.clientX - last.current.down));
    move(cutFromX(e.clientX));
  };
  const onUp = (e: React.PointerEvent<HTMLDivElement>) => {
    setDragging(false);
    if (last.current.moved < 6) { last.current.t = performance.now(); last.current.x = e.clientX; }   // a tap: a second one may follow
  };
  const onKey = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const p = keyCut(posRef.current, e.key);
    if (p === null) return;
    e.preventDefault();
    setSweeping(false);
    move(p);
  };

  const tr = sweeping ? 'clip-path 900ms cubic-bezier(.2,.7,.2,1)' : 'none';
  const trLeft = sweeping ? 'left 900ms cubic-bezier(.2,.7,.2,1)' : 'none';
  const showHandle = dragging || hot || sweeping || Math.abs(pos - PUPIL_CUT) > 0.5;

  return (
    <div
      ref={box}
      role="slider" tabIndex={0} aria-label={labels.slider} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(pos)} aria-valuetext={valueText(pos, labels.valueText)}
      data-testid="reveal" data-pos={pos.toFixed(2)}
      className={`relative aspect-square w-full overflow-hidden rounded-2xl bg-black border border-white/10 select-none touch-none cursor-ew-resize outline-none focus-visible:ring-2 focus-visible:ring-[#f5c542] ${className}`}
      {...NO_SAVE_BOX}
      onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={() => setDragging(false)}
      onPointerEnter={() => setHot(true)} onPointerLeave={() => setHot(false)} onFocus={() => setHot(true)} onBlur={() => setHot(false)} onKeyDown={onKey}
    >
      {/* layer P: the customer's photo, untouched */}
      <img {...NO_SAVE} src={photo} alt={labels.photo} className="absolute inset-0 w-full h-full pointer-events-none" style={{ ...NO_SAVE_IMG_STYLE, maxWidth: 'none' }} />
      {/* layer Rr: the restored iris on pure black, right of the cut (hard edge, 1 px anti-aliased by the compositor) */}
      <div className="absolute inset-0 pointer-events-none bg-black" data-testid="restored-layer" style={{ clipPath: `inset(0 0 0 ${pos}%)`, transition: tr }}>
        <RestoredDisc src={restored} g={geometry} alt={labels.iris} />
      </div>
      <span className="pointer-events-none absolute top-3 left-3 text-[10px] font-bold tracking-widest uppercase bg-black/70 px-2.5 py-1 rounded-full text-zinc-200 transition-opacity duration-700" style={{ opacity: pills && pos > 18 ? 1 : 0 }}>{labels.photo}</span>
      <span className="pointer-events-none absolute top-3 right-3 text-[10px] font-bold tracking-widest uppercase bg-black/70 px-2.5 py-1 rounded-full text-[#f5c542] transition-opacity duration-700" style={{ opacity: pills && pos < 82 ? 1 : 0 }}>{labels.iris}</span>
      {/* the handle: hidden at rest (the owner's clean look), shown on hover, touch, focus and while it moves */}
      <div aria-hidden="true" className="pointer-events-none absolute top-0 bottom-0 w-0.5 bg-[#f5c542] transition-opacity duration-300" data-testid="handle"
        style={{ left: `${pos}%`, opacity: showHandle ? 1 : 0, transition: `opacity 300ms, ${trLeft === 'none' ? 'left 0s' : trLeft}` }}>
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-[#f5c542] text-black flex items-center justify-center border-2 border-white shadow-lg">
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9 7l-5 5 5 5M15 7l5 5-5 5" /></svg>
        </div>
      </div>
    </div>
  );
};
