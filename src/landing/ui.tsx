import type { ReactNode, Ref } from 'react';
import { ArrowRight } from 'lucide-react';
import { TRY_URL } from './config';

export function Eyebrow({ children, center = false }: { children: ReactNode; center?: boolean }) {
  return (
    <p className={`flex items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f5c542] ${center ? 'justify-center' : ''}`}>
      <span aria-hidden="true" className="h-px w-7 bg-[#f5c542]/60" />
      <span>{children}</span>
    </p>
  );
}

export function SectionHead({ eyebrow, title, intro, center = false }: { eyebrow: string; title: string; intro?: string; center?: boolean }) {
  return (
    <div className={center ? 'mx-auto max-w-2xl text-center' : 'max-w-2xl'}>
      <Eyebrow center={center}>{eyebrow}</Eyebrow>
      <h2 className="mt-4 font-luxury text-[28px] leading-[1.15] font-semibold text-white sm:text-[40px] text-balance">{title}</h2>
      {intro && <p className="mt-4 text-[15px] leading-relaxed text-zinc-400 sm:text-base">{intro}</p>}
    </div>
  );
}

// The one primary action on the page: straight to the capture tool. min-h, not a fixed height: on a 320 px
// screen a long German label may still need two lines, and then the pill grows instead of clipping it.
export function CtaLink({ label, full = false, ref }: { label: string; full?: boolean; ref?: Ref<HTMLAnchorElement> }) {
  return (
    <a
      ref={ref}
      href={TRY_URL}
      className={`group inline-flex min-h-[52px] items-center justify-center gap-2.5 rounded-full bg-[#f5c542] px-6 py-3 text-center text-[15px] leading-tight font-semibold tracking-[0.01em] text-[#030408] shadow-[0_10px_40px_-12px_rgba(245,197,66,0.55)] transition-colors hover:bg-[#ffd666] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#f5c542] max-[359px]:px-4 max-[359px]:text-[14px] sm:px-7 ${full ? 'w-full' : ''}`}
    >
      <span>{label}</span>
      <ArrowRight aria-hidden="true" className="h-4 w-4 shrink-0 transition-transform group-hover:translate-x-0.5" />
    </a>
  );
}

// A quiet line under a call to action (German: the preview app is in English for now). Renders nothing when empty.
export function CtaNote({ text, className = '' }: { text: string; className?: string }) {
  if (!text) return null;
  return <p className={`text-[13px] leading-relaxed text-zinc-400 ${className}`}>{text}</p>;
}

export function Logo({ tag }: { tag: string }) {
  return (
    <a href="#top" className="flex items-center gap-2.5 rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#f5c542]" aria-label="SnapEyes Private Atelier">
      <svg aria-hidden="true" viewBox="0 0 32 32" className="h-8 w-8 shrink-0">
        <circle cx="16" cy="16" r="15" fill="none" stroke="#f5c542" strokeOpacity="0.55" strokeWidth="1" />
        <circle cx="16" cy="16" r="9.5" fill="none" stroke="#f5c542" strokeWidth="1.4" />
        <circle cx="16" cy="16" r="4" fill="#f5c542" />
      </svg>
      <span className="flex flex-col leading-none">
        <span className="font-luxury text-[17px] font-semibold tracking-[0.18em] text-white">SNAPEYES</span>
        <span className="mt-1 text-[9px] font-medium uppercase tracking-[0.34em] text-zinc-400">{tag}</span>
      </span>
    </a>
  );
}
