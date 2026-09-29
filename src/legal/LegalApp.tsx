// One component for the four legal pages (privacy, terms, withdrawal, imprint). Each HTML page names its document
// in <div id="root" data-doc="...">; the language follows the landing page's rules (?lang=, then the visitor's
// earlier choice, then the browser) and the EN/DE switch is the landing's own. The edition follows the page's market
// (src/shared/legal.ts legalEdition: ?m=au or the visitor's remembered market shows the Australian texts); the
// canonical address stays the plain one of the language.
import { useCallback, useEffect } from 'react';
import { ArrowLeft, Printer } from 'lucide-react';
import { LangProvider, setCanonical, setMeta, useLang } from '../landing/lang';
import { LangSwitch } from '../landing/Header';
import { Logo } from '../landing/ui';
import type { Lang } from '../landing/copy';
import {
  LEGAL_DOCS, LEGAL_LABELS, LEGAL_PATH, LEGAL_UPDATED, WITHDRAWAL_ONLINE, formatLegalDate, legalEdition, legalHref, withdrawFunctionHref,
  type LegalDocId,
} from '../shared/legal';
import { CONTACT_EMAIL, SELLER, address, company } from './facts';
import { withMarket } from '../shared/markets';
import { useMarket } from '../shared/useMarket';
import { Inline } from './Inline';
import type { Block } from './types';
import { EDITIONS } from './editions';

const ORIGIN = 'https://snapeyes.com';

const UI: Record<Lang, { updated: string; back: string; contents: string; print: string }> = {
  en: { updated: 'Last updated', back: 'Back to SnapEyes', contents: 'Contents', print: 'Print or save as PDF' },
  de: { updated: 'Zuletzt aktualisiert am', back: 'Zurück zu SnapEyes', contents: 'Inhalt', print: 'Drucken oder als PDF speichern' },
};

const FOCUS = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] rounded-sm';

function BlockView({ block, lang }: { block: Block; lang: Lang }) {
  if (typeof block === 'string') {
    return <p><Inline text={block} lang={lang} /></p>;
  }
  if ('ul' in block) {
    return (
      <ul className="list-disc space-y-2 pl-5 marker:text-[#f5c542]/70">
        {block.ul.map((li, i) => <li key={i}><Inline text={li} lang={lang} /></li>)}
      </ul>
    );
  }
  if ('dl' in block) {
    return (
      <dl className="divide-y divide-white/[0.06] rounded-xl border border-white/[0.08] bg-white/[0.02]">
        {block.dl.map(([term, value], i) => (
          <div key={i} className="grid gap-1 px-4 py-3 sm:grid-cols-[minmax(0,13rem)_1fr] sm:gap-5">
            <dt className="text-[13px] font-semibold text-zinc-400">{term}</dt>
            <dd className="text-zinc-100 break-words"><Inline text={value} lang={lang} /></dd>
          </div>
        ))}
      </dl>
    );
  }
  return (
    <figure className="rounded-xl border border-[#f5c542]/25 bg-[#f5c542]/[0.04] px-5 py-4">
      {block.label && (
        <figcaption className="mb-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f5c542]">{block.label}</figcaption>
      )}
      <div className="space-y-2 text-zinc-100">
        {block.box.map((line, i) => <p key={i}><Inline text={line} lang={lang} /></p>)}
      </div>
    </figure>
  );
}

function LegalPage({ id }: { id: LegalDocId }) {
  const { lang, t } = useLang();
  const doc = EDITIONS[legalEdition(useMarket())][id][lang];
  const ui = UI[lang];
  const labels = LEGAL_LABELS[lang];
  const home = withMarket(`/?lang=${lang}`);

  // the page renders after load, so the browser's own jump to #section happens too early: do it once here
  useEffect(() => {
    const target = decodeURIComponent(window.location.hash.slice(1));
    if (target) document.getElementById(target)?.scrollIntoView({ behavior: 'instant' });   // not the CSS smooth scroll
  }, []);

  return (
    <div className="legal-page min-h-screen bg-[#030408] text-[#f0f3fa] selection:bg-[#f5c542] selection:text-black">
      <header className="legal-noprint border-b border-white/[0.06]">
        <div className="mx-auto flex h-16 max-w-3xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo tag={t.brandTag} href={home} />
          <LangSwitch />
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 pb-20 pt-8 sm:px-6 sm:pt-12">
        <a href={home} className={`legal-noprint inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-white ${FOCUS}`}>
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          {ui.back}
        </a>
        <p className="mt-8 flex items-center gap-3 text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f5c542]">
          <span aria-hidden="true" className="h-px w-7 bg-[#f5c542]/60" />
          <span>{labels.nav}</span>
        </p>
        {/* German titles are single long words (Datenschutzerklärung): they carry soft hyphens (docs/*.ts), and
            overflow-wrap keeps any other long word from pushing the page wider */}
        <h1 className="mt-4 font-luxury text-[24px] font-semibold leading-tight text-white text-balance hyphens-auto [overflow-wrap:anywhere] min-[400px]:text-[28px] sm:text-[40px]">{doc.title}</h1>
        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-[13px] text-zinc-400">
          <p>{ui.updated} {formatLegalDate(LEGAL_UPDATED, lang)}</p>
          <button type="button" onClick={() => window.print()} className={`legal-noprint inline-flex items-center gap-1.5 hover:text-white ${FOCUS}`}>
            <Printer aria-hidden="true" className="h-3.5 w-3.5" />
            {ui.print}
          </button>
        </div>
        {doc.lead && (
          <p className="mt-6 text-[16px] leading-relaxed text-zinc-200 sm:text-[17px]"><Inline text={doc.lead} lang={lang} /></p>
        )}

        {doc.toc && (
          <nav aria-label={ui.contents} className="legal-noprint mt-8 rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 sm:p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-zinc-400">{ui.contents}</p>
            <ol className="mt-3 grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2">
              {doc.sections.map((s, i) => (
                <li key={s.id}>
                  <a href={`#${s.id}`} className={`text-zinc-300 hover:text-white ${FOCUS}`}>
                    {doc.numbered ? `${i + 1}. ` : ''}{s.title}
                  </a>
                </li>
              ))}
            </ol>
          </nav>
        )}

        {doc.sections.map((s, i) => (
          <section key={s.id} id={s.id} aria-labelledby={`${s.id}-title`} className="mt-10 scroll-mt-6 border-t border-white/[0.06] pt-8">
            <h2 id={`${s.id}-title`} className="font-luxury text-[19px] font-semibold leading-snug text-white hyphens-auto [overflow-wrap:anywhere] sm:text-[23px]">
              {doc.numbered ? `${i + 1}. ` : ''}{s.title}
            </h2>
            <div className="mt-4 space-y-4 text-[15px] leading-relaxed text-zinc-300 break-words">
              {s.blocks.map((b, j) => <BlockView key={j} block={b} lang={lang} />)}
            </div>
          </section>
        ))}
      </main>

      <footer className="border-t border-white/[0.06] bg-[#020306] pb-12 pt-10">
        <div className="mx-auto max-w-3xl px-4 text-sm text-zinc-400 sm:px-6">
          <nav aria-label={labels.nav} className="legal-noprint flex flex-wrap gap-x-6 gap-y-2">
            {LEGAL_DOCS.map((d) => (
              <a
                key={d}
                href={legalHref(d, lang)}
                aria-current={d === id ? 'page' : undefined}
                className={`${d === id ? 'text-white' : 'hover:text-white'} ${FOCUS}`}
              >
                {labels[d]}
              </a>
            ))}
            {/* the online withdrawal function (Art. 11a Directive 2011/83/EU), on every legal page */}
            <a href={withdrawFunctionHref(lang)} className={`hover:text-white ${FOCUS}`}>{WITHDRAWAL_ONLINE[lang].button}</a>
          </nav>
          <p className="mt-6 text-xs leading-relaxed">
            {company(lang)}, {address(lang)},{' '}
            <a href={`mailto:${CONTACT_EMAIL}`} className={`underline underline-offset-4 hover:text-white ${FOCUS}`}>{CONTACT_EMAIL}</a>
            {SELLER.phone && (
              <>
                ,{' '}
                <a href={`tel:${SELLER.phone.replace(/[^+\d]/g, '')}`} className={`underline underline-offset-4 hover:text-white ${FOCUS}`}>{SELLER.phone}</a>
              </>
            )}
          </p>
          <p className="mt-2 text-xs">© 2026 SnapEyes</p>
        </div>
      </footer>
    </div>
  );
}

export function LegalApp({ doc }: { doc: LegalDocId }) {
  const applyHead = useCallback((lang: Lang) => {
    const d = EDITIONS[legalEdition()][doc][lang];
    document.title = `${d.title.replace(/\u00AD/g, '')} | SnapEyes`;   // the German titles carry soft hyphens for the h1
    setMeta('name', 'description', d.description);
    setCanonical(`${ORIGIN}${LEGAL_PATH[doc]}${lang === 'de' ? '?lang=de' : ''}`);
  }, [doc]);
  return (
    <LangProvider applyHead={applyHead}>
      <LegalPage id={doc} />
    </LangProvider>
  );
}
