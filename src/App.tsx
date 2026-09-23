import { useRef } from 'react';
import './landing/landing.css';
import { LangProvider } from './landing/lang';
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

// SnapEyes Private Atelier: one honest page. Every image is the founder's own eye, every primary
// action goes to /try, and ordering is announced as "opens soon" until checkout exists.
export function App() {
  const heroCta = useRef<HTMLAnchorElement>(null);
  const finalCta = useRef<HTMLAnchorElement>(null);
  return (
    <LangProvider>
      <div className="min-h-screen bg-[#030408] text-[#f0f3fa] selection:bg-[#f5c542] selection:text-black">
        <Header />
        <main>
          <Hero ctaRef={heroCta} />
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
    </LangProvider>
  );
}

export default App;
