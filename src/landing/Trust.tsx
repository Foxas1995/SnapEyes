import { Ban, Clock, Lock, Mail, Trash2 } from 'lucide-react';
import { useLang } from './lang';
import { CONTACT_EMAIL, styleSrc } from './config';
import { SectionHead } from './ui';

const PRIVACY_ICONS = [Lock, Ban, Trash2, Clock];

// Curator note and privacy promise. The personal "send me your photos" offer only renders when
// CONTACT_EMAIL is set: snapeyes.com cannot receive mail yet.
export function Trust() {
  const { t } = useLang();
  const c = t.curator;
  const pv = t.privacy;
  return (
    <section className="border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto grid max-w-6xl gap-14 px-4 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:gap-16">
        <div>
          <SectionHead eyebrow={c.eyebrow} title={c.title} />
          <figure className="mt-8 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 sm:p-8">
            <div className="flex items-center gap-4">
              <img
                src={styleSrc('studio-black', 480)}
                width={480}
                height={480}
                loading="lazy"
                decoding="async"
                alt={c.photoAlt}
                className="h-16 w-16 shrink-0 rounded-full object-cover ring-1 ring-[#f5c542]/40"
              />
              <div>
                <p className="font-luxury text-xl font-semibold text-white">Mantas</p>
                <p className="mt-0.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f5c542]">{c.role}</p>
              </div>
            </div>
            <blockquote className="mt-6 text-[17px] leading-relaxed text-zinc-200">{c.note}</blockquote>
            {CONTACT_EMAIL && (
              <div className="mt-6 border-t border-white/[0.06] pt-6">
                <p className="text-[15px] leading-relaxed text-zinc-300">{c.offer}</p>
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="mt-4 inline-flex h-11 items-center gap-2 rounded-full border border-white/15 px-5 text-sm font-semibold text-white transition-colors hover:border-[#f5c542]/60 hover:text-[#f5c542] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542]"
                >
                  <Mail aria-hidden="true" className="h-4 w-4" />
                  {c.offerCta}
                </a>
              </div>
            )}
          </figure>
        </div>

        <div id="privacy" className="scroll-mt-16">
          <SectionHead eyebrow={pv.eyebrow} title={pv.title} />
          <ul className="mt-8 grid gap-x-6 gap-y-7 sm:grid-cols-2">
            {pv.items.map((it, i) => {
              const Icon = PRIVACY_ICONS[i];
              return (
                <li key={it.title} className="flex gap-4">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10">
                    <Icon aria-hidden="true" className="h-4 w-4 text-[#f5c542]" strokeWidth={1.6} />
                  </span>
                  <div>
                    <h3 className="font-body text-[15px] font-semibold text-white">{it.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-zinc-400">{it.body}</p>
                  </div>
                </li>
              );
            })}
          </ul>
          {/* who is responsible, and the rights every visitor has (GDPR Art. 13 basics; full notice: owner) */}
          <div className="mt-8 border-t border-white/[0.06] pt-6 text-sm leading-relaxed text-zinc-400">
            <p>{pv.controller}</p>
            <p className="mt-2">{pv.rights}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
