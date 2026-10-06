// The top of the live page: skip link, notice bar and fixed header, with the visitor's words and the header's behaviour.
//   <SiteTop />            above <main id="main">
// The markup is ./SiteTopView.tsx (the bar and the header are pure components, ./TopBar.tsx and ./Header.tsx, and it is also what the
// prerendered first screen is made of); this one is where they get their behaviour: the header sits under the
// bar and follows it up as the page scrolls, goes solid after 24 px, and --bar-h (the bar's height, which also places the hero)
// follows the bar when the window is resized, the fonts arrive or the bar's words change (src/landing/shell/chrome.ts).
// Needs <LangProvider> and <CopyProvider> above it.
import { startTransition, useRef } from 'react';
import { useLang } from './lang';
import { useCopy } from './copy/useCopy';
import { useOrderingOpen } from './ordering';
import { useTryHref } from './links';
import { useHeaderChrome } from './shell/chrome';
import { SiteTopView } from './SiteTopView';
import { marketLangs, type Lang } from '../shared/lang';
import { preloadCopy } from './copy/index';
import { useMarket } from '../shared/useMarket';

export function SiteTop() {
  const { c } = useCopy();
  // the pressed button follows the visitor's choice at once; the words follow when that language's file has arrived
  const { lang, setLang } = useLang();
  const market = useMarket();
  const open = useOrderingOpen();
  const tryHref = useTryHref();
  const barRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  // the two sentences are the same length (BUILD_PLAN section 1), so the flip moves nothing
  const barText = open ? c.bar.open : c.bar.soon;
  useHeaderChrome(barRef, headerRef, barText, lang);
  // one button per language the visitor's market can be read in
  const langs = marketLangs(market);
  // a language switch re-renders the whole page: a transition, so the page stays responsive while it does
  const onLang = (l: Lang) => startTransition(() => setLang(l));
  return <SiteTopView copy={c} lang={lang} langs={langs} barText={barText} tryHref={tryHref} onLang={onLang} onLangIntent={preloadCopy} barRef={barRef} headerRef={headerRef} />;
}
