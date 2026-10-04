// The top of the page as a PURE component: skip link, notice bar and fixed header (props in, markup out, no hook and no window). The
// same markup is rendered twice: to static HTML at build time (src/landing/shell/render.tsx, the prerendered first screen) and live
// by ./SiteTop.tsx, which gives it the visitor's words, the language buttons and the header's behaviour.
import type { Ref } from 'react';
import type { Lang } from '../shared/lang';
import type { LandingCopy } from './copy/types';
import { SiteHeaderView } from './Header';
import { TopBarView } from './TopBar';
import { MenuDialogView } from './MenuDialog';

export interface SiteTopViewProps {
  copy: LandingCopy;
  lang: Lang;
  /** The language buttons: the languages the visitor's market can be read in. */
  langs: readonly Lang[];
  /** The notice bar's sentence (bar.soon, or bar.open once ordering is open): both have the same length, so the flip moves nothing. */
  barText: string;
  tryHref: string;
  /** Only the live page gives these: the static shell has no handlers and no refs. */
  onLang?: (l: Lang) => void;
  /** The visitor is about to press a language button (see Header.tsx): the live page starts fetching that language's words. */
  onLangIntent?: (l: Lang) => void;
  barRef?: Ref<HTMLDivElement>;
  headerRef?: Ref<HTMLElement>;
}

export function SiteTopView({ copy, lang, langs, barText, tryHref, onLang, onLangIntent, barRef, headerRef }: SiteTopViewProps) {
  return (
    <>
      <a className="lp-skip" href="#main">{copy.skip}</a>
      <TopBarView label={copy.bar.label} text={barText} barRef={barRef} />
      <SiteHeaderView copy={copy} lang={lang} langs={langs} tryHref={tryHref} onLang={onLang} onLangIntent={onLangIntent} headerRef={headerRef} />
      <MenuDialogView copy={copy} tryHref={tryHref} />
    </>
  );
}
