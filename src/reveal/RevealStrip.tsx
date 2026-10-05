import React, { useEffect, useRef, useState } from 'react';
import { NO_SAVE, NO_SAVE_BOX, NO_SAVE_IMG_STYLE } from '../try/noSave';
import { RestoredDisc, usePrefersReducedMotion } from './Reveal';
import { stripFadeMs, type Geometry } from './revealMath';

interface Props {
  wide: string;                    // column 1: the wide frame of the Reveal, photo only (the same window)
  restored: string;                // column 2: the restored iris (display copy on /try, clean restoration on the landing / order page)
  art?: string | null;             // column 3: the artwork preview (watermarked, on /try). null: not made yet (an empty frame); omitted: two columns only (several eyes on one artwork)
  geometry: Geometry;              // the SAME circle and centre in columns 1 and 2, so the eye does not move between them
  captions: { photo: string; iris: string; art?: string };
  alts: { photo: string; iris: string; art?: string };
  promise?: string;                // "We never repaint or recolour your iris."
  reducedMotion?: boolean;
  className?: string;
}

/** Photo | Restored iris | Art: three equal squares (two without the art), gap 12 px (8 px below 400 px), three columns down to 340 px, stacked below that.
 *  On entering the viewport the columns fade 1 -> 2 -> 3, 500 ms each (not with reduced motion). */
export const RevealStrip: React.FC<Props> = ({ wide, restored, art, geometry, captions, alts, promise, reducedMotion, className = '' }) => {
  const rm = usePrefersReducedMotion(reducedMotion);
  const ref = useRef<HTMLDivElement>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || rm || typeof IntersectionObserver === 'undefined') { setSeen(true); return; }
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { setSeen(true); io.disconnect(); } }, { threshold: 0.25 });
    io.observe(el);
    return () => io.disconnect();
  }, [rm]);

  const col = (i: number): React.CSSProperties => {
    const f = stripFadeMs(i, rm);
    return { opacity: seen ? 1 : 0, transition: f.duration ? `opacity ${f.duration}ms ${f.delay}ms ease-out` : 'none' };
  };
  const frame = 'relative aspect-square w-full overflow-hidden rounded-xl bg-black border border-white/10';

  return (
    <div ref={ref} className={className} data-testid="strip" {...NO_SAVE_BOX}>
      <div className={`grid gap-2 min-[400px]:gap-3 max-[339px]:grid-cols-1 ${art === undefined ? 'grid-cols-2' : 'grid-cols-3'}`}>
        <figure style={col(0)} data-testid="strip-photo">
          <div className={frame}><img {...NO_SAVE} src={wide} alt={alts.photo} className="absolute inset-0 w-full h-full pointer-events-none" style={{ ...NO_SAVE_IMG_STYLE, maxWidth: 'none' }} /></div>
          <figcaption className="mt-2 text-[11px] sm:text-xs font-semibold tracking-wide text-zinc-300 text-center">{captions.photo}</figcaption>
        </figure>
        <figure style={col(1)} data-testid="strip-iris">
          <div className={frame}><RestoredDisc src={restored} g={geometry} alt={alts.iris} /></div>
          <figcaption className="mt-2 text-[11px] sm:text-xs font-semibold tracking-wide text-[#f5c542] text-center">{captions.iris}</figcaption>
        </figure>
        {art !== undefined && (
          <figure style={col(2)} data-testid="strip-art">
            <div className={frame}>
              {art && <img {...NO_SAVE} src={art} alt={alts.art ?? ''} className="absolute inset-0 w-full h-full object-contain pointer-events-none" style={{ ...NO_SAVE_IMG_STYLE, maxWidth: 'none' }} />}
            </div>
            <figcaption className="mt-2 text-[11px] sm:text-xs font-semibold tracking-wide text-zinc-300 text-center">{captions.art}</figcaption>
          </figure>
        )}
      </div>
      {promise && <p className="mt-3 text-xs text-zinc-300 text-center" data-testid="promise">{promise}</p>}
    </div>
  );
};
