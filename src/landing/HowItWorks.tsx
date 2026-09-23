import { Camera, FileImage, ScanEye } from 'lucide-react';
import { useLang } from './lang';
import { CtaLink, SectionHead } from './ui';

const ICONS = [Camera, ScanEye, FileImage];

export function HowItWorks() {
  const { t } = useLang();
  return (
    <section id="how" className="scroll-mt-16 border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <SectionHead eyebrow={t.how.eyebrow} title={t.how.title} />
        <ol className="mt-12 grid gap-4 md:grid-cols-3 md:gap-5">
          {t.how.steps.map((s, i) => {
            const Icon = ICONS[i];
            return (
              <li key={s.title} className="relative rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 sm:p-7">
                <div className="flex items-center justify-between">
                  <span className="font-luxury text-[26px] font-semibold text-[#f5c542]">0{i + 1}</span>
                  <Icon aria-hidden="true" className="h-5 w-5 text-zinc-500" strokeWidth={1.5} />
                </div>
                <h3 className="mt-5 font-body text-lg font-semibold text-white">{s.title}</h3>
                <p className="mt-2 text-[15px] leading-relaxed text-zinc-400">{s.body}</p>
              </li>
            );
          })}
        </ol>
        <div className="mt-10 flex flex-col sm:block">
          <CtaLink label={t.cta} />
        </div>
      </div>
    </section>
  );
}
