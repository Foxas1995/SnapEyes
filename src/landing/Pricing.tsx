// The pricing block of the new landing (BUILD_PLAN section 2, "Pricing"): the notice (ordering opens soon, or open), the price
// table with its free preview row and the "three eyes" row, what you receive (the licence, the printing cost sentence), the
// Australian seller line, the currency switch and the footnote with the link to the terms of sale.
//
// No purchase button here: an order starts from the visitor's own preview on /try, so the one action is the free preview. Every
// price comes through src/landing/prices.ts (PriceTable.tsx); the words come from the copy (src/landing/copy), the links from
// src/landing/links.ts. Importing this file brings its own stylesheet, so it can be loaded lazily with its section.
import { useCopy } from './copy/useCopy';
import { useLandingPrices } from './prices';
import { useLegalHref, useTryHref } from './links';
import { legalEdition } from '../shared/legal';
import { CurrencySwitch } from './CurrencySwitch';
import { PriceTable } from './PriceTable';
import './css/pricing.css';

// the prototype's arrow (a shorter head than the icon set's): the same on every button of the page
function Arrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function Pricing() {
  const { c, fmt } = useCopy();
  const p = useLandingPrices();
  const tryHref = useTryHref();
  const termsHref = useLegalHref('terms');
  const pr = c.pricing;
  const footnote = p.currency === 'aud' ? pr.footnoteAud : p.currency === 'huf' ? pr.footnoteHuf : pr.footnote;
  return (
    <section className="lp-sec" id="pricing" aria-labelledby="priceH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{pr.eyebrow}</p>
          <h2 id="priceH">{pr.title}</h2>
        </div>
        <p className="lp-notice" role="note">
          {p.open ? pr.noticeOpen : pr.notice}
        </p>
        <div className="lp-price-grid">
          <div>
            <CurrencySwitch label={pr.currencyLabel} />
            <PriceTable />
          </div>
          <div className="lp-incl">
            <h3>{pr.includesTitle}</h3>
            <ul>
              {pr.includes.map((line) => (
                <li key={line}>{fmt(line)}</li>
              ))}
            </ul>
            <p className="lp-not">{pr.notIncludes}</p>
            {p.open && <p className="lp-pay-open">{pr.payOpen}</p>}
            {legalEdition(p.market) === 'au' && <p className="lp-au-line">{pr.auLine}</p>}
            <a className="lp-btn lp-btn-gold" href={tryHref}>
              <span>{c.cta}</span>
              <Arrow />
            </a>
          </div>
        </div>
        <p className="lp-foot-price">
          <span>{footnote}</span> <a href={termsHref}>{pr.termsLink}</a>
        </p>
      </div>
    </section>
  );
}

export default Pricing;
