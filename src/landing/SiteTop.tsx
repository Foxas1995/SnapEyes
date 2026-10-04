// The top of the live page: skip link, notice bar and fixed header, with the visitor's words and the header's behaviour.
//   <SiteTop />            above <main id="main">
// The bar and the header are pure components (./TopBar.tsx, ./Header.tsx); this one is where they meet: the header sits under the
// bar and follows it up as the page scrolls, goes solid after 24 px, and --bar-h (the bar's height, which also places the hero)
// follows the bar when the window is resized, the fonts arrive or the bar's words change (src/landing/shell/chrome.ts).
// Needs <LangProvider> and <CopyProvider> above it.
import { useRef } from 'react';
import { useLang } from './lang';
import { useCopy } from './copy/useCopy';
import { useOrderingOpen } from './ordering';
import { useTryHref } from './links';
import { NEW_LANDING_LANGS } from './gate';
import { useHeaderChrome } from './shell/chrome';
import { TopBarView } from './TopBar';
import { SiteHeaderView } from './Header';
import { marketLangs } from '../shared/lang';
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
  useHeaderChrome(barRef, headerRef, barText);
  // one button per language the visitor's market can be read in and the new landing speaks
  const langs = marketLangs(market).filter((l) => NEW_LANDING_LANGS.includes(l));
  return (
    <>
      <a className="lp-skip" href="#main">{c.skip}</a>
      <TopBarView label={c.bar.label} text={barText} barRef={barRef} />
      <SiteHeaderView copy={c} lang={lang} langs={langs} tryHref={tryHref} onLang={setLang} headerRef={headerRef} />
    </>
  );
}
