// Small building blocks for any page that needs to point at the legal pages: /try (its footer, the photo step,
// the checkout) and the landing page. The wording lives in ./legal.ts.
import { LEGAL_DOCS, LEGAL_LABELS, legalHref, type LegalLang, type LegalPart } from './legal';

const LINK = 'underline underline-offset-4 decoration-white/30 hover:text-white hover:decoration-[#f5c542] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] rounded-sm';

/** A row of links to the four legal pages, for a page footer. /try: <LegalLinks lang="en" className="mt-10" />. */
export function LegalLinks({ lang = 'en', className = '' }: { lang?: LegalLang; className?: string }) {
  const l = LEGAL_LABELS[lang];
  return (
    <nav aria-label={l.nav} className={`flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-zinc-400 ${className}`}>
      {LEGAL_DOCS.map((d) => (
        <a key={d} href={legalHref(d, lang)} className="hover:text-white hover:underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] rounded-sm">
          {l[d]}
        </a>
      ))}
    </nav>
  );
}

/** Renders a sentence of text and legal links (CHECKOUT_LEGAL[lang].acceptance, .photoNotice). The links open in a
 *  new tab so a half-finished order or capture is never lost. */
export function LegalParts({ parts, lang = 'en' }: { parts: LegalPart[]; lang?: LegalLang }) {
  return (
    <>
      {parts.map((p, i) =>
        p.doc ? (
          <a key={i} href={legalHref(p.doc, lang)} target="_blank" rel="noopener" className={LINK}>
            {p.text}
          </a>
        ) : (
          <span key={i}>{p.text}</span>
        ),
      )}
    </>
  );
}
