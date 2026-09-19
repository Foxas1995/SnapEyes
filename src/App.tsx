import { useEffect } from 'react';
import Lenis from 'lenis';
import { Header } from './components/Header';
import { ScrollyHero } from './components/ScrollyHero';
import { BeforeAfterSlider } from './components/BeforeAfterSlider';
import { IrisStudio } from './components/IrisStudio';
import { PhotoGuide } from './components/PhotoGuide';
import { WallMockupGallery } from './components/WallMockupGallery';
import { MarketComparison } from './components/MarketComparison';

export function App() {
  // Initialize Lenis smooth scroll for 60fps cinematic feel
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#030408] text-[#f0f3fa] selection:bg-[#f5c542] selection:text-black">
      <Header />
      
      {/* 1. Cinematic 3D Continuous Spatial Camera Dive Hero */}
      <ScrollyHero />

      {/* 2. Interactive Before / After Split Slider (Phone Snap vs 4K Cosmic Art) */}
      <BeforeAfterSlider />

      {/* 3. Interactive AI Iris Studio (1-8 Eyes, 5x Macro Loupe, Color DNA, Plaque, Presets) */}
      <IrisStudio />

      {/* 4. Smartphone Photography Guide (3 Rules, Pet Mode, Veo 3.1 Prompt Studio) */}
      <PhotoGuide />

      {/* 5. Luxury Wall Mockup Gallery with Room Ambience Simulator (Daylight, Warm, Spotlight) */}
      <WallMockupGallery />

      {/* 6. Transparent Market Audit (SnapEyes vs Lithuanian Studios & World Apps) */}
      <MarketComparison />

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 px-6 text-center text-xs text-zinc-500 bg-[#020306]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="font-luxury font-bold tracking-widest text-[#f5c542]">SNAPEYES.COM</span>
            <span>· The World's #1 Instant Iris Art Studio © 2026</span>
          </div>
          <div className="flex gap-6 text-zinc-400">
            <a href="#scrolly" className="hover:text-white transition-colors">The Journey</a>
            <a href="#studio" className="hover:text-white transition-colors">Interactive Studio</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">Photo Guide</a>
            <a href="#wall-gallery" className="hover:text-white transition-colors">Wall Gallery</a>
            <a href="#comparison" className="hover:text-white transition-colors">Guarantee</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
