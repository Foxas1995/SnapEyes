// LEGACY: today's landing (Tailwind classes, words from src/landing/copy.ts through useLang). Moved here unchanged (only the import paths) when the new
// components took the file names of src/landing; the old file re-exports it for src/App.tsx and src/legal/LegalApp.tsx (LangSwitch). It serves the
// visitors the new landing does not serve yet (src/landing/gate.ts: Lithuanian, Hungarian, the forint market). Delete with that fallback.
import { useEffect, useState, type RefObject } from 'react';
import { useLang } from '../lang';
import { CtaLink } from '../ui';

// Phone-only bar with the primary action. It appears once the hero button has scrolled away and steps
// aside while the closing call to action is on screen, so there is never a second copy right next to it.
export function StickyCta({ heroRef, finalRef }: { heroRef: RefObject<HTMLAnchorElement | null>; finalRef: RefObject<HTMLAnchorElement | null> }) {
  const { t } = useLang();
  const [pastHero, setPastHero] = useState(false);
  const [finalVisible, setFinalVisible] = useState(false);

  useEffect(() => {
    const hero = heroRef.current;
    const fin = finalRef.current;
    if (!hero || !fin || typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.target === hero) setPastHero(!e.isIntersecting && e.boundingClientRect.top < 0);
        if (e.target === fin) setFinalVisible(e.isIntersecting);
      }
    });
    io.observe(hero);
    io.observe(fin);
    return () => io.disconnect();
  }, [heroRef, finalRef]);

  const show = pastHero && !finalVisible;
  return (
    <div
      inert={!show}
      aria-hidden={!show}
      className={`fixed inset-x-0 bottom-0 z-40 border-t border-white/[0.08] bg-[#030408]/92 px-4 pt-3 backdrop-blur-xl transition-[transform,visibility] duration-300 md:hidden ${
        show ? 'visible translate-y-0' : 'invisible translate-y-full'
      }`}
      style={{ paddingBottom: 'calc(12px + env(safe-area-inset-bottom))' }}
    >
      <CtaLink label={t.cta} full />
    </div>
  );
}
