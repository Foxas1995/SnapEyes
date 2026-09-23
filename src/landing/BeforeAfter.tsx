import { useRef, useState, type PointerEvent } from 'react';
import { useLang } from './lang';
import { BEFORE_SRC, styleSrc, styleSrcSet } from './config';
import { SectionHead } from './ui';

// Real before and after: the founder's 315 px phone crop against the same eye rendered in Studio Black.
// Both images keep the iris at almost the same size (about 90 % of the frame), so the split lines up.
function CompareSlider() {
  const { t } = useLang();
  const b = t.beforeAfter;
  const [pos, setPos] = useState(50);
  const box = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const fromX = (clientX: number) => {
    const el = box.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    setPos(Math.round(Math.min(100, Math.max(0, ((clientX - r.left) / r.width) * 100))));
  };
  const down = (e: PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    e.currentTarget.setPointerCapture(e.pointerId);
    fromX(e.clientX);
  };
  const move = (e: PointerEvent<HTMLDivElement>) => {
    if (dragging.current) fromX(e.clientX);
  };
  const up = () => {
    dragging.current = false;
  };

  return (
    <div
      ref={box}
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      onPointerCancel={up}
      className="relative aspect-square w-full cursor-ew-resize touch-pan-y select-none overflow-hidden rounded-[24px] bg-black ring-1 ring-white/10"
    >
      <img
        src={styleSrc('studio-black', 800)}
        srcSet={styleSrcSet('studio-black')}
        sizes="(min-width: 1024px) 540px, calc(100vw - 32px)"
        width={800}
        height={800}
        loading="lazy"
        decoding="async"
        draggable={false}
        alt={b.afterAlt}
        className="absolute inset-0 h-full w-full object-cover"
      />
      <img
        src={BEFORE_SRC}
        width={315}
        height={315}
        loading="lazy"
        decoding="async"
        draggable={false}
        alt={b.beforeAlt}
        className="absolute inset-0 h-full w-full object-cover"
        style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
      />
      <span className="pointer-events-none absolute left-2.5 top-2.5 rounded-full bg-black/70 px-2.5 py-1 text-[10px] font-medium text-zinc-200 ring-1 ring-white/15 backdrop-blur transition-opacity sm:left-3 sm:top-3 sm:px-3 sm:py-1.5 sm:text-[11px]" style={{ opacity: pos > 18 ? 1 : 0 }}>
        {b.before}
      </span>
      <span className="pointer-events-none absolute right-2.5 top-2.5 rounded-full bg-black/70 px-2.5 py-1 text-[10px] font-medium text-[#f5c542] ring-1 ring-[#f5c542]/30 backdrop-blur transition-opacity sm:right-3 sm:top-3 sm:px-3 sm:py-1.5 sm:text-[11px]" style={{ opacity: pos < 82 ? 1 : 0 }}>
        {b.after}
      </span>
      <input
        type="range"
        min={0}
        max={100}
        value={pos}
        onChange={(e) => setPos(Number(e.target.value))}
        aria-label={b.sliderLabel}
        aria-valuetext={`${pos}%`}
        className="peer sr-only"
      />
      <div aria-hidden="true" className="pointer-events-none absolute inset-y-0 w-px bg-[#f5c542]/90" style={{ left: `${pos}%` }}>
        <div className="absolute left-1/2 top-1/2 flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-[#030408]/80 ring-1 ring-[#f5c542] backdrop-blur">
          <svg viewBox="0 0 24 24" className="h-5 w-5 text-[#f5c542]" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 7l-5 5 5 5M15 7l5 5-5 5" />
          </svg>
        </div>
      </div>
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 rounded-[24px] ring-2 ring-inset ring-transparent peer-focus-visible:ring-[#f5c542]" />
    </div>
  );
}

export function BeforeAfter() {
  const { t } = useLang();
  const b = t.beforeAfter;
  return (
    <section id="before-after" className="scroll-mt-16 border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
        <div>
          <SectionHead eyebrow={b.eyebrow} title={b.title} intro={b.intro} />
          <div className="mt-9 border-l-2 border-[#f5c542]/70 pl-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-300">{b.transparencyTitle}</p>
            <p className="mt-2 text-lg leading-relaxed text-white">{b.transparency}</p>
          </div>
        </div>
        <figure className="mx-auto w-full max-w-[540px]">
          <CompareSlider />
          <figcaption className="mt-4 text-[13px] leading-relaxed text-zinc-300">{b.caption}</figcaption>
        </figure>
      </div>
    </section>
  );
}
