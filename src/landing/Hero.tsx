import type { Ref } from 'react';
import { Check, Clock } from 'lucide-react';
import { useLang } from './lang';
import { BEFORE_SRC, styleSrc, styleSrcSet } from './config';
import { CtaLink, CtaNote, Eyebrow } from './ui';

// Phones: headline, action, then the artwork (its centre lands on the first 390 x 844 screen), then the points.
// Desktop: text and points on the left, the artwork on the right across both rows.
export function Hero({ ctaRef }: { ctaRef: Ref<HTMLAnchorElement> }) {
  const { t } = useLang();
  const h = t.hero;
  return (
    <section id="top" className="relative overflow-hidden pt-24 pb-20 sm:pt-36 sm:pb-28">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-40 right-[-20%] h-[720px] w-[720px] rounded-full opacity-60"
        style={{ background: 'radial-gradient(closest-side, rgba(245,197,66,0.10), rgba(245,197,66,0.03) 55%, transparent)' }}
      />
      <div className="relative mx-auto grid max-w-6xl gap-y-10 px-4 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:gap-x-16 lg:gap-y-10">
        <div className="lg:col-start-1 lg:row-start-1 lg:self-end">
          <Eyebrow>{h.eyebrow}</Eyebrow>
          <h1 className="mt-5 font-luxury text-[32px] font-semibold leading-[1.1] text-white text-balance hyphens-auto sm:mt-6 sm:text-[52px] lg:text-[58px]">
            {h.title}
          </h1>
          <p className="mt-5 max-w-xl text-base leading-relaxed text-zinc-300 sm:mt-6 sm:text-lg">{h.lead}</p>
          <div className="mt-8 flex flex-col gap-4 sm:mt-9 sm:flex-row sm:items-center sm:gap-6">
            <CtaLink ref={ctaRef} label={t.cta} />
            <a href="#before-after" className="text-center text-sm text-zinc-300 underline decoration-white/20 underline-offset-[6px] transition-colors hover:text-white hover:decoration-[#f5c542] sm:text-left">
              {h.secondary}
            </a>
          </div>
          <CtaNote text={t.ctaNote} className="mt-4 text-center sm:text-left" />
        </div>

        <figure className="mx-auto w-full max-w-[520px] lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:self-center">
          <div className="aspect-square overflow-hidden rounded-[28px] bg-black ring-1 ring-white/10 shadow-[0_40px_120px_-30px_rgba(0,0,0,0.95)]">
            <img
              src={styleSrc('celestial-gold', 800)}
              srcSet={styleSrcSet('celestial-gold')}
              sizes="(min-width: 640px) 520px, calc(100vw - 32px)"
              width={800}
              height={800}
              fetchPriority="high"
              decoding="async"
              alt={h.imageAlt}
              className="h-full w-full object-cover"
            />
          </div>
          {/* the phone photo this artwork was made from sits below the frame, never over the artwork */}
          <figcaption className="mt-4 flex items-center gap-3.5">
            <img
              src={BEFORE_SRC}
              width={315}
              height={315}
              decoding="async"
              alt={h.insetAlt}
              className="h-14 w-14 shrink-0 rounded-full object-cover ring-1 ring-white/15"
            />
            <span className="text-[13px] leading-snug text-zinc-400">
              <span className="block text-zinc-200">{h.caption}</span>
              <span className="mt-0.5 block">
                {h.insetLabel} · {h.styleNote}
              </span>
            </span>
          </figcaption>
        </figure>

        <ul className="grid gap-3 text-sm text-zinc-300 lg:col-start-1 lg:row-start-2 lg:self-start">
          {h.points.map((p) => (
            <li key={p} className="flex items-start gap-3">
              <Check aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-[#f5c542]" />
              <span>{p}</span>
            </li>
          ))}
          <li className="flex items-start gap-3 text-zinc-400">
            <Clock aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" />
            <span>{h.soon}</span>
          </li>
        </ul>
      </div>
    </section>
  );
}
