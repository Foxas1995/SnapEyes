// The closing scene and the footer of the new landing (prototype: section.final and footer.ftr).
//
//   <ClosingScene ctaRef={...} />     the last section of <main>: a dark dining room with Mantas's iris on aluminium, the headline,
//                                     the gold button, and the line that the file is digital and printing is not part of the order
//   <SiteFooter />                    after </main>: logo, the seller, the page's links, the currency switch, the legal links
//
// Both need <LangProvider> and <CopyProvider> above them. The closing picture is an AI visualisation and says so in its corner
// (the "AI visualisation" chip, the words of final.chip). The seller is MB Portretizuokis (src/landing/config.ts SELLER): its
// lines come from there, never from here, and the legal links only through src/landing/links.ts (legalHref, which carries the
// language and the market's edition).
import type { Ref } from 'react';
import { useCopy } from './copy/useCopy';
import { useLegalLinks, useTryHref } from './links';
import { CONTACT_EMAIL, SELLER } from './config';
import { asset } from './assets';
import { ExampleChip } from './ui';
import { CurrencySwitch } from './CurrencySwitch';
import { SiteLogo } from './Header';

// Today's closing call to action and footer, for the visitors the new landing does not serve yet (src/landing/gate.ts). Delete with
// that fallback.
export { FinalCta, Footer } from './legacy/Footer';

/** The links of the footer, in the prototype's order: the header's sections except "how it works", and the privacy promise after the prices. */
const FOOTER_NAV = ['reveal', 'wall', 'styles', 'pricing', 'privacy', 'faq'] as const;

export function ClosingScene({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c } = useCopy();
  const tryHref = useTryHref();
  const pic = asset('m/dining_metal__eye__wide', { pick: 2000 });
  return (
    <section className="lp-final" id="final" aria-labelledby="finalH">
      <div className="lp-bg">
        <img src={pic.src} srcSet={pic.srcset} sizes="(min-width: 960px) 1800px, 1200px" width={pic.w} height={pic.h} loading="lazy" decoding="async" alt={c.final.imageAlt} />
      </div>
      <ExampleChip variant="vis" label={c.final.chip} className="lp-final-chip" />
      <div className="lp-wrap">
        <h2 id="finalH">{c.final.title}</h2>
        <p className="lp-lede">{c.final.body}</p>
        <a className="lp-btn lp-btn-gold" id="ctaFinal" href={tryHref} ref={ctaRef}>
          <span>{c.cta}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </a>
        <p className="lp-fine">{c.final.small}</p>
      </div>
    </section>
  );
}

export function SiteFooter() {
  const { c } = useCopy();
  const f = c.footer;
  const legal = useLegalLinks();
  return (
    <footer className="lp-ftr">
      <div className="lp-wrap">
        <div className="lp-ftr-grid">
          <div>
            <SiteLogo brandTag={c.brandTag} />
          </div>
          <address>
            <span className="lp-ftr-by">{f.operatedBy}</span>
            <b>{f.company}</b>
            <br />
            <span>{f.companyCode}</span> {SELLER.code}
            <br />
            {SELLER.street}
            <br />
            {SELLER.postcode} {SELLER.city}, <span>{f.country}</span>
            <br />
            {SELLER.representative && (
              <>
                <span>{f.representedBy}</span> {SELLER.representative}
                <br />
              </>
            )}
            {SELLER.phone && (
              <span className="lp-ftr-line">
                <a href={`tel:${SELLER.phone.replace(/[^+\d]/g, '')}`}>{SELLER.phone}</a>
              </span>
            )}
            {CONTACT_EMAIL && (
              <span className="lp-ftr-line">
                <span>{f.contact}</span>: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
              </span>
            )}
          </address>
          <nav id="ftrNav" aria-label={c.navLabels.footer}>
            {FOOTER_NAV.map((k) => (
              <a key={k} href={`#${k}`}>{c.nav[k]}</a>
            ))}
          </nav>
        </div>
        <div className="lp-ftr-bottom">
          <div className="lp-ftr-l">
            <p>© {new Date().getFullYear()} {f.rights}</p>
            <CurrencySwitch label={f.currency} flush />
          </div>
          {/* the legal pages (src/legal) in the language the visitor reads now and the market's edition, and the online withdrawal
              function (Art. 11a Directive 2011/83/EU: clearly labelled and easy to reach while the right of withdrawal lasts) */}
          <nav id="legalNav" aria-label={f.legalNav}>
            {legal.map((l) => (
              <a key={l.key} href={l.href}>{l.label}</a>
            ))}
          </nav>
        </div>
      </div>
    </footer>
  );
}
