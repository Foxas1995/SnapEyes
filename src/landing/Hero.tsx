// The hero (prototype: section.hero). Copy and call to action on the left, the picture with its in-frame label and the disc on
// the right (./HeroScene.tsx). On a phone the order is headline, lead, button, picture, micro line (the CSS unwraps the copy
// column); from 960 px it is two columns, the picture sized to the viewport so it is whole on a 1366 x 768 screen.
//
//   <HeroSection ctaRef={heroCta} />   live, inside <main id="main"> (needs <LangProvider> and <CopyProvider>)
//   <HeroView ... />                   the same markup as a pure component: props in, markup out
//
// The micro line's price ("Digital file from {from}") is the visitor's own price, held back (invisible, out of the tab order, its
// space kept) until the server has answered about the visitor's prices, so nobody in a price experiment sees the standard price
// for a moment and nothing moves when it appears (src/landing/prices.ts).
import type { Ref } from 'react';
import type { LandingCopy } from './copy/types';
import { fill } from './copy/format';
import { useCopy } from './copy/useCopy';
import { useLandingPrices } from './prices';
import { useTryHref } from './links';
import { HeroScene } from './HeroScene';

// Today's hero, for the visitors the new landing does not serve yet (src/landing/gate.ts). Delete with that fallback.
export { Hero } from './legacy/Hero';

function Arrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export interface HeroViewProps {
  copy: LandingCopy;
  tryHref: string;
  /** "Digital file from {from}" with the price filled in. */
  priceLine: string;
  /** Hold the price line back until the visitor's prices are known. */
  pricePending: boolean;
  ctaRef?: Ref<HTMLAnchorElement>;
}

export function HeroView({ copy, tryHref, priceLine, pricePending, ctaRef }: HeroViewProps) {
  const h = copy.hero;
  return (
    <section className="lp-hero" id="top" aria-labelledby="h1">
      <div className="lp-wrap lp-hero-grid">
        <div className="lp-hero-copy">
          <p className="lp-eyebrow">{h.eyebrow}</p>
          <h1 id="h1">{h.title}</h1>
          <p className="lp-lead">{fill(h.lead, copy.facts)}</p>
          <div className="lp-cta-row">
            <a className="lp-btn lp-btn-gold" id="ctaHero" href={tryHref} ref={ctaRef}>
              <span>{copy.cta}</span>
              <Arrow />
            </a>
            <a className="lp-link-quiet" href="#reveal">{h.secondary}</a>
          </div>
          <ul className="lp-micro" id="heroMicro">
            {h.micro.map((x) => (
              <li key={x}>{x}</li>
            ))}
            <li className="lp-price" inert={pricePending || undefined} style={pricePending ? { opacity: 0, userSelect: 'none' } : undefined}>
              <a href="#pricing">{priceLine}</a>
            </li>
          </ul>
          <p className="lp-computer-hint">{h.computerHint}</p>
        </div>
        <HeroScene hero={h} />
      </div>
    </section>
  );
}

export function HeroSection({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const tryHref = useTryHref();
  return <HeroView copy={c} tryHref={tryHref} priceLine={t('hero.fromPrice', { from: prices.from })} pricePending={prices.pending} ctaRef={ctaRef} />;
}
