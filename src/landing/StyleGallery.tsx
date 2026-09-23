import { useLang } from './lang';
import { PRICE_CENTS, STYLES, styleSrc, styleSrcSet } from './config';
import { formatEuro } from './copy';
import { SectionHead } from './ui';

export function StyleGallery() {
  const { t, lang } = useLang();
  const s = t.styles;
  return (
    <section id="styles" className="scroll-mt-16 border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <SectionHead eyebrow={s.eyebrow} title={s.title} intro={s.intro} />
        {/* prices appear below, so the "ordering opens soon" notice sits right here too (owner decision 2) */}
        <p role="note" className="mt-5 flex items-start gap-2.5 text-sm font-medium text-[#f7d77a]">
          <span aria-hidden="true" className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-[#f5c542]" />
          <span>{t.pricing.notice}</span>
        </p>
        <ul className="mt-12 grid grid-cols-2 gap-x-3 gap-y-8 sm:gap-x-5 md:grid-cols-3 md:gap-y-12">
          {STYLES.map((st) => {
            const cents = st.id === 'studio_black' ? PRICE_CENTS.studioBlack : PRICE_CENTS.artBackground;
            return (
              <li key={st.id}>
                <figure>
                  <div className="aspect-square overflow-hidden rounded-2xl bg-black ring-1 ring-white/[0.08]">
                    <img
                      src={styleSrc(st.slug, 800)}
                      srcSet={styleSrcSet(st.slug)}
                      sizes="(min-width: 1152px) 355px, (min-width: 768px) 30vw, calc(50vw - 22px)"
                      width={800}
                      height={800}
                      loading="lazy"
                      decoding="async"
                      alt={s.alt(st.name)}
                      className="h-full w-full object-cover"
                    />
                  </div>
                  <figcaption className="mt-4">
                    <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                      <h3 className="font-luxury text-[15px] font-semibold tracking-[0.04em] text-white sm:text-base">{st.name}</h3>
                      <span className="text-xs text-zinc-400">
                        {s.oneEye} · <span className="text-zinc-300">{formatEuro(cents, lang)}</span>
                      </span>
                    </div>
                    <p className="mt-1.5 text-[13px] leading-relaxed text-zinc-400 sm:text-sm">{s.desc[st.id]}</p>
                  </figcaption>
                </figure>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
