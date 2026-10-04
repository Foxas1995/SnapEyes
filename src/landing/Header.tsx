// The fixed header of the new landing: logo, navigation, language switch and the short call to action (prototype: #hdr). A PURE
// component (props in, markup out, no hook and no window), so the same markup can be rendered to static HTML at build time
// (src/landing/shell) and live (./SiteTop.tsx, which also gives it its behaviour: it sits under the notice bar and follows it up
// as the page scrolls, goes solid after 24 px).
//
// It imports nothing that carries the landing's words or pictures: types only, plus the language names (the legal pages have
// their own language switch, src/legal/LangSwitch.tsx).
import type { CSSProperties, Ref } from 'react';
import { LANG_NAMES, type Lang } from '../shared/lang';
import type { LandingCopy } from './copy/types';

/** The header's navigation, in the order of the page's sections (copy nav.*). */
export const NAV_KEYS = ['reveal', 'wall', 'styles', 'how', 'pricing', 'faq'] as const;

export function LogoMark() {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="15" fill="none" stroke="#f5c542" strokeOpacity=".55" />
      <circle cx="16" cy="16" r="9.5" fill="none" stroke="#f5c542" strokeWidth="1.4" />
      <circle cx="16" cy="16" r="4" fill="#f5c542" />
    </svg>
  );
}

/** The logo link: the mark, SNAPEYES and the brand tag under it. It goes to the top of the page; the header and the footer use it. */
export function SiteLogo({ brandTag }: { brandTag: string }) {
  return (
    <a className="lp-logo" href="#top" aria-label={`SnapEyes ${brandTag}`}>
      <LogoMark />
      <span>
        <b>SNAPEYES</b>
        <small>{brandTag}</small>
      </span>
    </a>
  );
}

export interface SiteHeaderViewProps {
  copy: LandingCopy;
  lang: Lang;
  /** The language buttons: the languages the new landing speaks in the visitor's market. */
  langs: readonly Lang[];
  tryHref: string;
  /** Only the live page gives these: the static shell has no handlers and no refs. */
  onLang?: (l: Lang) => void;
  /** The visitor is about to press a language button (pointer over it, finger down, focus): the live page starts fetching that
   *  language's words, so the first switch does not wait for the file after the press. */
  onLangIntent?: (l: Lang) => void;
  headerRef?: Ref<HTMLElement>;
}

export function SiteHeaderView({ copy, lang, langs, tryHref, onLang, onLangIntent, headerRef }: SiteHeaderViewProps) {
  return (
    <header className="lp-hdr" id="hdr" ref={headerRef}>
      <div className="lp-wrap">
        <SiteLogo brandTag={copy.brandTag} />
        <nav className="lp-nav" id="nav" aria-label={copy.navLabels.main}>
          {NAV_KEYS.map((k) => (
            <a key={k} href={`#${k}`}>{copy.nav[k]}</a>
          ))}
          {/* the one gold hairline that slides under the link of the section being read (src/landing/shell/navMark.ts; decorative) */}
          <i className="lp-nav-mark" aria-hidden="true" />
        </nav>
        <div className="lp-hdr-r">
          {/* --n is the pressed button's place: the one pressed background slides to it in .3 s (css/header.css); the words change at once */}
          <div className="lp-seg" role="group" id="langSeg" aria-label={copy.switchLabel} style={{ '--n': Math.max(0, langs.indexOf(lang)) } as CSSProperties}>
            <span className="lp-seg-ind" aria-hidden="true" />
            {langs.map((l) => (
              <button
                key={l}
                type="button"
                lang={l}
                aria-pressed={lang === l}
                title={LANG_NAMES[l]}
                onClick={onLang ? () => onLang(l) : undefined}
                onPointerEnter={onLangIntent ? () => onLangIntent(l) : undefined}
                onTouchStart={onLangIntent ? () => onLangIntent(l) : undefined}
                onFocus={onLangIntent ? () => onLangIntent(l) : undefined}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>
          <a className="lp-btn lp-btn-line" href={tryHref}>{copy.ctaShort}</a>
          {/* phones and tablets: the page's links in a real dialog (showModal: focus kept inside, the page behind inert, Escape closes it).
              It works before React has started too: one delegated handler (src/landing/shell/scripts.ts menuScript) opens and closes it. */}
          <button type="button" className="lp-menu-btn" id="menuBtn" aria-haspopup="dialog" aria-controls="menu" aria-expanded="false" aria-label={copy.navLabels.menu}>
            <span aria-hidden="true" />
          </button>
        </div>
      </div>
    </header>
  );
}
