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

export function HeroSection({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const tryHref = useTryHref();
  // "from" is the lowest price among the styles that can be bought now for one eye (the run-time catalogue, while ordering is open). With none the line is held back
  // for good, exactly like a price that is still pending (invisible, out of the accessibility tree, its words and so its space kept: the prerendered first screen has
  // the same box and nothing moves when the server answers), so no price of a style nobody can buy is ever shown or read out
  const from = prices.fromOf(useSaleCatalogue().one);
  return <HeroView copy={c} tryHref={tryHref} priceLine={t('hero.fromPrice', { from: from ?? prices.from })} pricePending={prices.pending || from === null} ctaRef={ctaRef} />;
}
