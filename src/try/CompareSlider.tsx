import React, { useEffect, useRef, useState } from 'react';
import { MoveHorizontal } from 'lucide-react';
import { T } from './copy';
import { NO_SAVE, NO_SAVE_BOX, NO_SAVE_IMG_STYLE } from './noSave';
import { stillMotion } from '../motion/flow';
import { SWEEP, hasSwept, markSwept, sweepAt } from '../motion/flowLogic';

interface Props {
  before: string;
  after: string;
  beforeLabel?: string;
  afterLabel?: string;
  /** the eye this slider shows: the one auto sweep that teaches the drag runs once per eye (motion spec 7.5). Without it there is no sweep. */
  sweepKey?: string;
}

// the sweep needs motion, an observer that can say when the slider is in view, and an eye it has not swept yet
const armed = (key?: string): boolean => !!key && typeof window !== 'undefined' && 'IntersectionObserver' in window && !stillMotion() && !hasSwept(key);

/** Before/after slider: both images fill the same square, the "after" layer is clipped at the handle. Works with touch and mouse.
 *  after is the watermarked display copy /api/enhance returns; neither image can be dragged out or long-pressed (./noSave).
 *  Once per eye, 400 ms after it first comes into view, the handle sweeps from 92 to 50 percent (1 s, expo out) to show that it moves; any touch or click
 *  stops it where the customer put the handle, and it never plays again for that eye. While it waits the handle rests at 92 (the photo); an observer that
 *  never reports (an in-app browser) puts it at 50 after 3.5 s, so the picture is never left half hidden. Reduced motion: no sweep, the handle is at 50. */
export const CompareSlider: React.FC<Props> = ({ before, after, beforeLabel = T.result.sliderBefore, afterLabel = T.result.sliderAfter, sweepKey }) => {
  const [waits] = useState(() => armed(sweepKey));
  const [pos, setPos] = useState(waits ? SWEEP.from : 50);
  const [dragging, setDragging] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const stopSweep = useRef<() => void>(() => {});

  useEffect(() => {
    const el = box.current;
    if (!waits || !sweepKey || !el) return;
    let done = false;
    let raf = 0, delay = 0, t0 = 0;
    const stop = () => { done = true; clearTimeout(delay); clearTimeout(failsafe); cancelAnimationFrame(raf); io.disconnect(); };
    const play = (now: number) => {
      t0 ||= now;
      const ms = now - t0;
      setPos(sweepAt(ms));
      if (ms < SWEEP.durationMs && !done) raf = requestAnimationFrame(play); else stop();
    };
    const io = new IntersectionObserver(([e]) => {
      clearTimeout(failsafe);   // the observer is alive
      if (!e.isIntersecting || done) return;
      io.disconnect();
      delay = window.setTimeout(() => { if (done) return; markSwept(sweepKey); raf = requestAnimationFrame(play); }, SWEEP.delayMs);
    }, { threshold: 0.6 });
    const failsafe = window.setTimeout(() => { stop(); setPos(SWEEP.to); }, 3500);
    io.observe(el);
    stopSweep.current = () => { markSwept(sweepKey); stop(); };
    return stop;
  }, [waits, sweepKey]);

  const update = (clientX: number) => {
    const el = box.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setPos(Math.max(0, Math.min(100, pct)));
  };

  return (
    <div
      ref={box}
      className="relative aspect-square w-full overflow-hidden rounded-2xl bg-black border border-white/10 select-none touch-none cursor-ew-resize"
      {...NO_SAVE_BOX}
      onPointerDown={(e) => { stopSweep.current(); setDragging(true); (e.target as Element).setPointerCapture?.(e.pointerId); update(e.clientX); }}
      onPointerMove={(e) => { if (dragging) update(e.clientX); }}
      onPointerUp={() => setDragging(false)}
      onPointerCancel={() => setDragging(false)}
    >
      <img {...NO_SAVE} src={before} alt={beforeLabel} className="absolute inset-0 w-full h-full object-cover pointer-events-none" />
      <img
        {...NO_SAVE}
        src={after}
        alt={afterLabel}
        className="absolute inset-0 w-full h-full object-cover pointer-events-none"
        style={{ ...NO_SAVE_IMG_STYLE, clipPath: `inset(0 0 0 ${pos}%)` }}
      />
      <span className="absolute top-3 left-3 text-[10px] font-bold tracking-widest uppercase bg-black/70 px-2.5 py-1 rounded-full text-zinc-200">{beforeLabel}</span>
      <span className="absolute top-3 right-3 text-[10px] font-bold tracking-widest uppercase bg-black/70 px-2.5 py-1 rounded-full text-[#f5c542]">{afterLabel}</span>
      {/* the cut: one pixel of gold with the soft glow the tokens allow (never above .28) */}
      <div className="absolute top-0 bottom-0 w-px bg-[#f5c542] shadow-[0_0_16px_0_rgba(245,197,66,0.28)]" style={{ left: `${pos}%` }}>
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-10 h-10 rounded-full bg-[#f5c542] text-black flex items-center justify-center border-2 border-white shadow-lg">
          <MoveHorizontal className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
};
