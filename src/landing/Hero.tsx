// The hero of the live page: the markup is ./HeroView.tsx (also what the prerendered first screen is made of), this gives it the
// visitor's words, the price of their own ladder (only while a style can be bought now) and the link to /try.
//
//   <HeroSection ctaRef={heroCta} />   live, inside <main id="main"> (needs <LangProvider> and <CopyProvider>)
import type { Ref } from 'react';
import { useCopy } from './copy/useCopy';
import { useLandingPrices } from './prices';
import { useSaleCatalogue } from './ordering';
import { useTryHref } from './links';
import { HeroView } from './HeroView';
import { heroPrice } from './heroPrice';

export function HeroSection({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const tryHref = useTryHref();
  // the line prints the lowest price among the styles that can be bought now for one eye and is held back while there is none (./heroPrice.ts)
  const hero = heroPrice(prices, prices.pending, useSaleCatalogue());
  return <HeroView copy={c} tryHref={tryHref} priceLine={t('hero.fromPrice', { from: hero.from })} pricePending={hero.held} ctaRef={ctaRef} />;
}
