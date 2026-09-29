import type { Ref } from 'react';
import { useLang } from './lang';
import { CONTACT_EMAIL, SELLER } from './config';
import { CtaLink, CtaNote, Logo } from './ui';
import { LEGAL_DOCS, LEGAL_LABELS, WITHDRAWAL_ONLINE, legalHref, withdrawFunctionHref } from '../shared/legal';

export function FinalCta({ ctaRef }: { ctaRef: Ref<HTMLAnchorElement> }) {
  const { t } = useLang();
  return (
    <section className="relative overflow-hidden border-t border-white/[0.06] py-24 sm:py-32">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-1/2 h-[560px] w-[560px] -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{ background: 'radial-gradient(closest-side, rgba(245,197,66,0.09), transparent)' }}
      />
      <div className="relative mx-auto max-w-2xl px-4 text-center sm:px-6">
        <h2 className="font-luxury text-[30px] font-semibold leading-tight text-white text-balance sm:text-[44px]">{t.final.title}</h2>
        <p className="mt-4 text-base text-zinc-400 sm:text-lg">{t.final.body}</p>
        <div className="mt-9 flex justify-center">
          <CtaLink ref={ctaRef} label={t.cta} />
        </div>
        <CtaNote text={t.ctaNote} className="mt-4" />
      </div>
    </section>
  );
}

export function Footer() {
  const { t, lang } = useLang();
  const f = t.footer;
  const legal = LEGAL_LABELS[lang];
  const year = 2026;
  return (
    <footer className="border-t border-white/[0.06] bg-[#020306] pb-28 pt-14 md:pb-14">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 text-sm text-zinc-400 sm:px-6 md:grid-cols-[1fr_1.2fr_0.8fr]">
        <div>
          <Logo tag={t.brandTag} />
        </div>
        <address className="not-italic leading-relaxed">
          <span className="block text-zinc-400">{f.operatedBy}</span>
          <span className="block text-zinc-200">{f.company}</span>
          <span className="block">
            {f.companyCode} {SELLER.code}
          </span>
          <span className="block">{SELLER.street}</span>
          <span className="block">
            {SELLER.postcode} {SELLER.city}, {f.country}
          </span>
          {SELLER.representative && (
            <span className="block">
              {f.representedBy} {SELLER.representative}
            </span>
          )}
          {SELLER.phone && (
            <span className="mt-3 block">
              {f.phone}:{' '}
              <a href={`tel:${SELLER.phone.replace(/[^+\d]/g, '')}`} className="text-zinc-200 underline underline-offset-4 hover:text-[#f5c542]">
                {SELLER.phone}
              </a>
            </span>
          )}
          {CONTACT_EMAIL && (
            <span className="mt-3 block">
              {f.contact}:{' '}
              <a href={`mailto:${CONTACT_EMAIL}`} className="text-zinc-200 underline underline-offset-4 hover:text-[#f5c542]">
                {CONTACT_EMAIL}
              </a>
            </span>
          )}
        </address>
        <nav aria-label={t.navLabels.footer} className="flex flex-col gap-2.5">
          <a href="#before-after" className="hover:text-white">{t.nav.beforeAfter}</a>
          <a href="#styles" className="hover:text-white">{t.nav.styles}</a>
          <a href="#pricing" className="hover:text-white">{t.nav.pricing}</a>
          <a href="#privacy" className="hover:text-white">{t.nav.privacy}</a>
          <a href="#faq" className="hover:text-white">{t.nav.faq}</a>
        </nav>
      </div>
      <div className="mx-auto mt-12 flex max-w-6xl flex-col gap-4 border-t border-white/[0.06] px-4 pt-6 text-xs text-zinc-400 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>
          © {year} {f.rights}
        </p>
        {/* the legal pages (src/legal), in the language the visitor reads now, and the online withdrawal function
            (Art. 11a Directive 2011/83/EU: clearly labelled and easy to reach while the right of withdrawal lasts) */}
        <nav aria-label={legal.nav} className="flex flex-wrap gap-x-5 gap-y-2">
          {LEGAL_DOCS.map((d) => (
            <a key={d} href={legalHref(d, lang)} className="hover:text-white">
              {legal[d]}
            </a>
          ))}
          <a href={withdrawFunctionHref(lang)} className="hover:text-white">
            {WITHDRAWAL_ONLINE[lang].button}
          </a>
        </nav>
      </div>
    </footer>
  );
}
