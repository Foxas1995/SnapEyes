import { useRef } from 'react';
import './landing/landing.css';
import { LangProvider, useLang } from './landing/lang';
import { CopyProvider } from './landing/copy/CopyProvider';
import { newLandingFor } from './landing/gate';
import { FirstScreenHero, FirstScreenTop } from './landing/shell/FirstScreen';
import { Header } from './landing/Header';
import { Hero } from './landing/Hero';
import { BeforeAfter } from './landing/BeforeAfter';
import { HowItWorks } from './landing/HowItWorks';
import { StyleGallery } from './landing/StyleGallery';
import { Pricing } from './landing/Pricing';
import { Trust } from './landing/Trust';
import { Faq } from './landing/Faq';
import { FinalCta, Footer } from './landing/Footer';
import { StickyCta } from './landing/StickyCta';
import { MarketHint } from './landing/MarketHint';
import { useMarket } from './shared/useMarket';

// SnapEyes Private Atelier: one honest page. Every image is the founder's own eye, every primary
// action goes to /try, and ordering is announced as "opens soon" until checkout exists.
//
// Landing v2 is being put in place section by section (BUILD_PLAN section 4). The first screen is the new one (the very
// components the prerendered shell in index.html is made of, src/landing/shell) for every visitor the new landing serves
// (src/landing/gate.ts); the sections below it are today's until their new versions replace them one by one. A visitor the
// new landing does not serve yet (a language without its copy, the forint market) gets today's page as it was.
export function App() {
  return (
    <LangProvider>
      <Page />
    </LangProvider>
  );
}

function Page() {
  const heroCta = useRef<HTMLAnchorElement>(null);
  const finalCta = useRef<HTMLAnchorElement>(null);
  const { lang } = useLang();
  // the visitor's market (src/shared/markets.ts): every section re-renders when it changes (the footer's currency
  // switch), so every price and every link (m=) follows at once
  const market = useMarket();
  const fresh = newLandingFor(lang, market);
  // the new first screen sits on the body's own background (src/landing/css/base.css): no wrapper colour over it
  const page = (
    <div className={fresh ? undefined : 'min-h-screen bg-[#030408] text-[#f0f3fa] selection:bg-[#f5c542] selection:text-black'}>
      {fresh ? <FirstScreenTop /> : <Header />}
      <main id="main">
        <MarketHint />
        {fresh ? <FirstScreenHero ctaRef={heroCta} /> : <Hero ctaRef={heroCta} />}
        <BeforeAfter />
        <HowItWorks />
        <StyleGallery />
        <Pricing />
        <Trust />
        <Faq />
        <FinalCta ctaRef={finalCta} />
      </main>
      <Footer />
      <StickyCta heroRef={heroCta} finalRef={finalCta} />
    </div>
  );
  // until the new language file is here a first render shows nothing, so the prerendered shell stays on screen under it
  return fresh ? <CopyProvider fallback={null}>{page}</CopyProvider> : page;
}

export default App;
