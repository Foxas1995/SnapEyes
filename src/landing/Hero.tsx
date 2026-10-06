// The hero of the live page: the markup is ./HeroView.tsx (also what the prerendered first screen is made of), this gives it the
// visitor's words, the price of their own ladder and the link to /try.
//
//   <HeroSection ctaRef={heroCta} />   live, inside <main id="main"> (needs <LangProvider> and <CopyProvider>)
import type { Ref } from 'react';
import { useCopy } from './copy/useCopy';
import { useLandingPrices } from './prices';
import { useTryHref } from './links';
import { HeroView } from './HeroView';

export function HeroSection({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const tryHref = useTryHref();
  return <HeroView copy={c} tryHref={tryHref} priceLine={t('hero.fromPrice', { from: prices.from })} pricePending={prices.pending} ctaRef={ctaRef} />;
}
