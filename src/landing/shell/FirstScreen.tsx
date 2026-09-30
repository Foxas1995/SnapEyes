// The live first screen: the same components the build rendered into index.html (./parts.tsx), now with the visitor's words,
// language buttons, prices and the header's behaviour. Because the markup is the very same, the static shell and this render
// occupy the same boxes (scripts/check_shell.mjs measures it), so nothing moves when React takes over.
//   <FirstScreenTop /> skip link, notice bar, header        <main><FirstScreenHero ctaRef={...} /> ...the sections... </main>
// Needs <LangProvider> and <CopyProvider> above it.
import { useRef, type Ref } from 'react';
import { useLang } from '../lang';
import { useCopy } from '../copy/useCopy';
import { useLandingPrices } from '../prices';
import { useTryHref } from '../links';
import { useOrderingOpen } from '../ordering';
import { NEW_LANDING_LANGS } from '../gate';
import { marketLangs } from '../../shared/lang';
import { useMarket } from '../../shared/useMarket';
import { useHeaderChrome } from './chrome';
import { ShellHero, ShellTop } from './parts';

export function FirstScreenTop() {
  const { c, lang } = useCopy();
  const { setLang } = useLang();
  const market = useMarket();
  const open = useOrderingOpen();
  const tryHref = useTryHref();
  const barRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  // the two sentences are the same length (BUILD_PLAN section 1), so the flip moves nothing
  const barText = open ? c.bar.open : c.bar.soon;
  useHeaderChrome(barRef, headerRef, barText);
  const langs = marketLangs(market).filter((l) => NEW_LANDING_LANGS.includes(l));
  return <ShellTop copy={c} lang={lang} langs={langs} barText={barText} tryHref={tryHref} onLang={setLang} barRef={barRef} headerRef={headerRef} />;
}

export function FirstScreenHero({ ctaRef }: { ctaRef?: Ref<HTMLAnchorElement> }) {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const tryHref = useTryHref();
  return <ShellHero copy={c} tryHref={tryHref} priceLine={t('hero.fromPrice', { from: prices.from })} pricePending={prices.pending} ctaRef={ctaRef} />;
}
