import { Plus } from 'lucide-react';
import { useLang } from './lang';
import { SectionHead } from './ui';

export function Faq() {
  const { t } = useLang();
  return (
    <section id="faq" className="scroll-mt-16 border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:px-6 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16">
        <SectionHead eyebrow={t.faq.eyebrow} title={t.faq.title} />
        <div className="border-t border-white/[0.08]">
          {t.faq.items.map((it) => (
            <details key={it.q} className="faq group border-b border-white/[0.08]">
              <summary className="flex cursor-pointer items-center justify-between gap-6 py-5 text-left text-base font-medium text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] sm:text-[17px]">
                <span>{it.q}</span>
                <Plus aria-hidden="true" className="h-4 w-4 shrink-0 text-[#f5c542] transition-transform duration-200 group-open:rotate-45" />
              </summary>
              <p className="pb-6 pr-8 text-[15px] leading-relaxed text-zinc-400">{it.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
