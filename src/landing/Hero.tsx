// The hero of the live page: the markup is ./HeroView.tsx (also what the prerendered first screen is made of), this gives it the
// visitor's words, the price of their own ladder (only while a style can be bought now), the link to /try, and the globe.
//
// The globe (2026-10-22): the first screen paints its poster (./HeroScene.tsx, the LCP picture); its interactive code and its pictures are a chunk of
// their own (./globe/Globe.tsx), fetched only when the hero's stage is on screen, the page has loaded and the browser is idle, so the first load does
// not carry them. Once the globe's first pictures are decoded it takes the poster's place (the same arrangement: nothing is seen to change).
//
//   <HeroSection ctaRef={heroCta} />   live, inside <main id="main"> (needs <LangProvider> and <CopyProvider>)
import { useEffect, useState, type ComponentType, type Ref } from 'react';
import { useCopy } from './copy/useCopy';
import { useLandingPrices } from './prices';
import { useSaleCatalogue } from './ordering';
import { useTryHref } from './links';
import { HeroView } from './HeroView';
import { heroPrice } from './heroPrice';
import { loadRetry } from './lazy';
import type { GlobeProps } from './globe/Globe';

/** Fetch the globe's chunk once its stage is on screen while the page has loaded, when the browser has a moment (an idle callback that never comes
 *  waits 2 s at most). A visitor who arrives further down (a link to #faq) fetches nothing until the hero comes back on screen. A chunk that cannot
 *  be fetched (after one more try, ./lazy.ts) leaves the poster: the first screen stays whole. */
function watchGlobe(done: (c: ComponentType<GlobeProps>) => void): () => void {
  const stage = document.querySelector('#root #heroGlobe');
  if (!stage || typeof IntersectionObserver === 'undefined') return () => undefined;
  let alive = true;
  let idle = 0;
  let timer = 0;
  let seen = false;
  const fetchIt = () => {
    loadRetry(() => import('./globe/Globe')).then(
      (m) => {
        if (alive && m.default) done(m.default);
      },
      () => undefined,
    );
  };
  const go = () => {
    if (!seen || document.readyState !== 'complete') return;
    io.disconnect();
    window.removeEventListener('load', go);
    if (typeof requestIdleCallback === 'function') idle = requestIdleCallback(fetchIt, { timeout: 2000 });
    else timer = window.setTimeout(fetchIt, 200);
  };
  const io = new IntersectionObserver((entries) => {
    seen = entries.at(-1)!.isIntersecting;
    go();
  });
  io.observe(stage);
  window.addEventListener('load', go);
  return () => {
    alive = false;
    io.disconnect();
    window.removeEventListener('load', go);
    if (idle) cancelIdleCallback(idle);
    clearTimeout(timer);
  };
}

export function HeroSection({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const tryHref = useTryHref();
  // the line prints the lowest price among the styles that can be bought now for one eye and is held back while there is none (./heroPrice.ts)
  const hero = heroPrice(prices, prices.pending, useSaleCatalogue());
  // the globe reads its own words, catalogue and link (./globe/Globe.tsx): this only fetches it and lets it take the poster's place
  const [Globe, setGlobe] = useState<ComponentType<GlobeProps> | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => watchGlobe((g) => setGlobe(() => g)), []);
  return (
    <HeroView
      copy={c}
      tryHref={tryHref}
      priceLine={t('hero.fromPrice', { from: hero.from })}
      pricePending={hero.held}
      ctaRef={ctaRef}
      globe={Globe ? <Globe onReady={() => setReady(true)} /> : null}
      globeReady={ready}
    />
  );
}
