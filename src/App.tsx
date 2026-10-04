import { Suspense, lazy, useRef, type ReactNode } from 'react';
import { LangProvider } from './landing/lang';
import { CopyProvider } from './landing/copy/CopyProvider';
import { SiteTop } from './landing/SiteTop';
import { MarketHintBar } from './landing/MarketHint';
import { HeroSection } from './landing/Hero';
import { SiteFooter } from './landing/Footer';
import { StickyBar } from './landing/StickyCta';
import { SLOT_HEIGHTS, slotStyle, type SlotName } from './landing/slots';
import { useHashTarget } from './landing/useHashTarget';

// SnapEyes Private Atelier: one honest page (landing v2). The visitor buys a DIGITAL file; every picture of a room, a wall or a
// hand is an AI visualisation and says so in the picture; every primary action goes to /try; ordering is announced as "opens soon"
// until checkout exists (src/landing/ordering.ts).
//
// What is on the page, in the order of BUILD_PLAN section 2:
//   first render (this bundle):  notice bar, header, hero (the same markup as the prerendered first screen in index.html, so the
//                                handoff moves nothing), the footer and the sticky phone button;
//   one chunk each, loaded as soon as the first render has run: the Reveal, the wall chapter (its size guide and "More ways to see
//                                it" are chunks of their own), the styles gallery, how it works, pricing, the close-ups, trust,
//                                the FAQ and the closing scene. Each brings its own stylesheet. While a chunk is on its way its
//                                place is held by an empty slot of the section's height (src/landing/slots.ts), carrying the
//                                section's id, so the page does not move when it arrives and a link to #pricing already has a target.
// A language or currency switch is a React transition (the header and the currency switch start it), so the page stays responsive
// while every section re-renders.
const Reveal = lazy(() => import('./landing/Reveal'));
const Wall = lazy(() => import('./landing/Wall'));
const StyleGallery = lazy(() => import('./landing/StyleGallery').then((m) => ({ default: m.StyleGallery })));
const HowItWorks = lazy(() => import('./landing/HowItWorks').then((m) => ({ default: m.HowItWorks })));
const Pricing = lazy(() => import('./landing/Pricing'));
const CloseUps = lazy(() => import('./landing/CloseUps'));
const Trust = lazy(() => import('./landing/Trust'));
const Faq = lazy(() => import('./landing/Faq'));
const ClosingScene = lazy(() => import('./landing/ClosingScene'));

/** A lazy section with its place held: an empty section of the right height and id until the chunk is here. */
function Slot({ name, children }: { name: SlotName; children: ReactNode }) {
  return (
    // the closing scene is not a .lp-sec (no separator line above it): its slot is not one either
    <Suspense fallback={<section className={name === 'final' ? 'lp-slot' : 'lp-sec lp-slot'} id={SLOT_HEIGHTS[name].id} aria-hidden="true" style={slotStyle(name)} />}>
      {children}
    </Suspense>
  );
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
      <SiteTop />
      <main id="main">
        <MarketHintBar />
        <HeroSection ctaRef={heroCta} />
        <Slot name="reveal"><Reveal /></Slot>
        <Slot name="wall"><Wall /></Slot>
        <Slot name="styles"><StyleGallery /></Slot>
        <Slot name="how"><HowItWorks /></Slot>
        <Slot name="pricing"><Pricing /></Slot>
        <Slot name="closeups"><CloseUps /></Slot>
        <Slot name="trust"><Trust /></Slot>
        <Slot name="faq"><Faq /></Slot>
        <Slot name="final"><ClosingScene /></Slot>
      </main>
      <SiteFooter />
      <StickyBar heroRef={heroCta} />
    </CopyProvider>
  );
}

export default App;
