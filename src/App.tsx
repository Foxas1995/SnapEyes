import { createElement, useEffect, useRef } from 'react';
import { useCopy } from './landing/copy/useCopy';
import { LangProvider } from './landing/lang';
import { CopyProvider } from './landing/copy/CopyProvider';
import { SiteTop } from './landing/SiteTop';
import { MarketHintBar } from './landing/MarketHint';
import { HeroSection } from './landing/Hero';
import { SiteFooter } from './landing/Footer';
import { StickyBar } from './landing/StickyCta';
import { SLOT_HEIGHTS, slotStyle } from './landing/slots';
import { useHashTarget } from './landing/useHashTarget';
import { SectionBoundary } from './landing/SectionBoundary';
import { NEAR_OPTIONS, openSection, startSections, useSection } from './landing/sectionQueue';
import type { SectionName } from './landing/sectionLoaders';

// SnapEyes Private Atelier: one honest page (landing v2). The visitor buys a DIGITAL file; every picture of a room, a wall or a
// hand is an AI visualisation and says so in the picture; every primary action goes to /try; ordering is announced as "opens soon"
// until checkout exists (src/landing/ordering.ts).
//
// What is on the page, in the order of BUILD_PLAN section 2:
//   first render (this bundle):  notice bar, header, hero (the same markup as the prerendered first screen in index.html, so the
//                                handoff moves nothing), the footer and the sticky phone button;
//   one chunk each, let in one at a time after the first render (src/landing/sectionQueue.ts: page order, one per idle slice, at once
//                                when the visitor comes near): the Reveal, the wall chapter (its size guide and "More ways to see
//                                it" are chunks of their own), the styles gallery, how it works, pricing, the close-ups, trust,
//                                the FAQ and the closing scene. Each brings its own stylesheet. Until a section is here its place
//                                is held by an empty slot of the section's height (src/landing/slots.ts), carrying the section's
//                                id, so the page does not move when it arrives and a link to #pricing already has a target. A chunk
//                                that fails to load is asked for once more, and if it still fails the section is left out and the
//                                page stays (src/landing/lazy.ts).
// A language or currency switch is a React transition (the header and the currency switch start it), so the page stays responsive
// while every section re-renders.

/** A lazy section with its place held: an empty section of the right height and id until its turn has come (src/landing/sectionQueue.ts:
 *  in page order, one per idle slice, at once when the visitor comes near) and its code is here. A section whose code cannot be
 *  fetched is left out and the rest of the page stays (src/landing/lazy.ts, SectionBoundary). */
function Slot({ name }: { name: SectionName }) {
  const section = useSection(name);
  const { lang } = useCopy();
  const hole = useRef<HTMLElement>(null);
  const waiting = section === 'waiting';
  useEffect(() => {
    const el = hole.current;
    if (!waiting || !el || !('IntersectionObserver' in window)) return;
    const near = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) openSection(name);
    }, NEAR_OPTIONS);
    near.observe(el);
    return () => near.disconnect();
  }, [waiting, name]);
  if (section === 'failed') return null;
  if (typeof section === 'string') {
    // the closing scene is not a .lp-sec (no separator line above it): its slot is not one either
    return <section ref={hole} className={name === 'final' ? 'lp-slot' : 'lp-sec lp-slot'} id={SLOT_HEIGHTS[name].id} aria-hidden="true" style={slotStyle(name, lang)} />;
  }
  return <SectionBoundary>{createElement(section)}</SectionBoundary>;
}

/** Starts the queue of the sections once the page's words are on screen (it renders inside the copy provider, so nothing is let in
 *  before there is something to render it with). */
function StartSections() {
  useEffect(() => {
    startSections();
  }, []);
  return null;
}

export function App() {
  return (
    <LangProvider>
      <Page />
    </LangProvider>
  );
}

function Page() {
  const heroCta = useRef<HTMLAnchorElement>(null);
  // an address with a #section lands on it although the section arrives after the page (src/landing/useHashTarget.ts)
  useHashTarget();
  // until the visitor's language file is here a first render shows nothing, so the prerendered shell stays on screen under it
  return (
    <CopyProvider fallback={null}>
      <StartSections />
      <SiteTop />
      <main id="main">
        <MarketHintBar />
        <HeroSection ctaRef={heroCta} />
        {/* Three chapters, three rounded sheets that roll over what is above them (motion spec 6.0, src/motion/motion.css): the proof (the
            Reveal), the choice (the wall, the styles, how it works), the price and the trust (pricing, the close-ups, trust, the FAQ). The
            closing scene and the footer are flat bands. The slots are inside the sheets, so a section arrives where its place was held. */}
        <div className="lp-sheet lp-sheet-a">
          <Slot name="reveal" />
        </div>
        <div className="lp-sheet lp-sheet-c">
          <Slot name="wall" />
          <Slot name="styles" />
          <Slot name="how" />
        </div>
        <div className="lp-sheet lp-sheet-d">
          <Slot name="pricing" />
          <Slot name="closeups" />
          <Slot name="trust" />
          <Slot name="faq" />
        </div>
        <Slot name="final" />
      </main>
      <SiteFooter />
      <StickyBar heroRef={heroCta} />
    </CopyProvider>
  );
}

export default App;
