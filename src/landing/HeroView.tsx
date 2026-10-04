// The hero (prototype: section.hero) as a PURE component: props in, markup out, no hook and no window. Copy and call to action on
// the left, the picture with its in-frame label and the disc on the right (./HeroScene.tsx). On a phone the order is headline,
// lead, button, picture, micro line (the CSS unwraps the copy column); from 960 px it is two columns, the picture sized to the
// viewport so it is whole on a 1366 x 768 screen.
//
// The same markup is rendered twice: to static HTML at build time (src/landing/shell/render.tsx, the prerendered first screen) and
// live by ./Hero.tsx, so the two cannot drift apart (scripts/check_shell.mjs measures that they also occupy the same boxes).
// The micro line's price ("Digital file from {from}") is the visitor's own price, held back (invisible, out of the tab order, its
// space kept) until the server has answered about the visitor's prices, so nobody in a price experiment sees the standard price
// for a moment and nothing moves when it appears (src/landing/prices.ts).
import type { CSSProperties, Ref } from 'react';
import type { LandingCopy } from './copy/types';
import { fill } from './copy/format';
import { HeroScene } from './HeroScene';
import { Title } from '../motion/Title';

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

/** The entrance of the first screen (motion spec 6.2): when this element starts, in seconds. The CSS (src/motion/motion.css lp-rise,
 *  lp-rise-s) plays from the markup that is already painted, the prerendered shell included; nothing here waits for a script. */
const at = (s: number): CSSProperties => ({ '--d': `${s}s` }) as CSSProperties;

export function HeroView({ copy, tryHref, priceLine, pricePending, ctaRef }: HeroViewProps) {
  const h = copy.hero;
  return (
    <section className="lp-hero" id="top" aria-labelledby="h1">
      <div className="lp-wrap lp-hero-grid">
        <div className="lp-hero-copy">
          <p className="lp-eyebrow lp-rise-s" style={at(0.1)}>{h.eyebrow}</p>
          <Title as="h1" id="h1" text={h.title} intro className="lp-t-display" />
          <p className="lp-lead lp-rise" style={at(0.5)}>{fill(h.lead, copy.facts)}</p>
          <div className="lp-cta-row lp-rise" style={at(0.62)}>
            <a className="lp-btn lp-btn-gold" id="ctaHero" href={tryHref} ref={ctaRef}>
              <span>{copy.cta}</span>
              <Arrow />
            </a>
            <a className="lp-link-quiet" href="#reveal">{h.secondary}</a>
          </div>
          <ul className="lp-micro lp-rise-s" id="heroMicro" style={at(0.76)}>
            {h.micro.map((x) => (
              <li key={x}>{x}</li>
            ))}
            <li className="lp-price" inert={pricePending || undefined} style={pricePending ? { opacity: 0, userSelect: 'none' } : undefined}>
              <a href="#pricing">{priceLine}</a>
            </li>
          </ul>
          <p className="lp-computer-hint lp-rise-s" style={at(0.8)}>{h.computerHint}</p>
        </div>
        <HeroScene hero={h} />
      </div>
    </section>
  );
}
