// The footer of the new landing (prototype: footer.ftr), after </main>: logo, the seller, the page's links, the currency switch, the
// legal links. Needs <LangProvider> and <CopyProvider> above it. The seller is MB Portretizuokis (src/landing/config.ts SELLER): its
// lines come from there, never from here, and the legal links only through src/landing/links.ts (legalHref, which carries the
// language and the market's edition). (The closing scene above it is ./ClosingScene.tsx.)
import { useCopy } from './copy/useCopy';
import { useLegalLinks } from './links';
import { CONTACT_EMAIL, SELLER } from './config';
import { CurrencySwitch } from './CurrencySwitch';
import { SiteLogo } from './Header';

/** The links of the footer, in the prototype's order: the header's sections except "how it works", and the privacy promise after the prices. */
const FOOTER_NAV = ['reveal', 'wall', 'styles', 'pricing', 'privacy', 'faq'] as const;

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
