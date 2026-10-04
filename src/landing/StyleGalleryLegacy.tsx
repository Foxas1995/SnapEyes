// TEMPORARY BRIDGE (landing v2 port, task S4): today's style gallery, unchanged except for its name. src/landing/StyleGallery.tsx
// renders the new gallery inside a CopyProvider (every visitor the new landing serves, src/landing/gate.ts) and this one
// outside it (Lithuanian, Hungarian and the forint market, which keep today's page until their copy exists). Delete this file
// and the fallback in StyleGallery.tsx with the last old section.
import { useLang } from './lang';
import { STYLES, styleSrc, styleSrcSet } from './config';
import { currencyOf, money, priceMinor } from '../shared/markets';
import { useMarket } from '../shared/useMarket';
import { usePrices, usePricesReady } from '../shared/usePrices';
import { useOrderingOpen } from './ordering';
import { SectionHead } from './ui';

export function StyleGalleryLegacy() {
  const { t, lang } = useLang();
  const open = useOrderingOpen();
  const market = useMarket();
  const prices = usePrices(market);          // the visitor's own ladder while a price experiment runs for them
  const pending = !usePricesReady();         // the server's first answer is waited for (a moment) before a price is printed
  const s = t.styles;
  return (
    <section id="styles" className="scroll-mt-16 border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <SectionHead eyebrow={s.eyebrow} title={s.title} intro={s.intro} />
        {/* prices appear below, so the pricing notice ("ordering opens soon", or its open wording) sits right here too (owner decision 2) */}
        <p role="note" className="mt-5 flex items-start gap-2.5 text-sm font-medium text-[#f7d77a]">
          <span aria-hidden="true" className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-[#f5c542]" />
          <span>{open ? t.pricing.noticeOpen : t.pricing.notice}</span>
        </p>
        <ul className="mt-12 grid grid-cols-2 gap-x-3 gap-y-8 sm:gap-x-5 md:grid-cols-3 md:gap-y-12">
          {STYLES.map((st) => {
            const cents = priceMinor(1, st.id, market, prices);
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
                        {s.oneEye} · <span className={`text-zinc-300 ${pending ? 'opacity-0' : ''}`} aria-hidden={pending || undefined}>{money(cents, currencyOf(market), lang)}</span>
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
