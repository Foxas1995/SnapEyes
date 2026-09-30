// The first screen of the landing page: skip link, notice bar, fixed header, and the hero. These are PURE components (props in,
// markup out, no hook, no window), so the same markup is rendered twice and can only look the same twice:
//   * at build time, to static HTML (src/landing/shell/render.tsx, called by the plugin in vite.config.ts), which is what a
//     visitor sees before any script has run (the LCP picture is in it, preloaded);
//   * in the browser, by src/landing/shell/FirstScreen.tsx, which gives the same components the live words, prices and handlers.
// The markup and the class names are the prototype's (prototype/src/index.src.html), the classes prefixed lp- (src/landing/css).
// Words come from the copy (src/landing/copy/en.json and the other languages), never from here.
import type { Ref } from 'react';
import { LANG_NAMES, type Lang } from '../../shared/lang';
import { HERO_SIZES, NAV_KEYS, heroDisc, heroPicture } from './hero';
import { fill } from '../copy/format';
import type { LandingCopy } from '../copy/types';

function Arrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function LogoMark() {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="15" fill="none" stroke="#f5c542" strokeOpacity=".55" />
      <circle cx="16" cy="16" r="9.5" fill="none" stroke="#f5c542" strokeWidth="1.4" />
      <circle cx="16" cy="16" r="4" fill="#f5c542" />
    </svg>
  );
}

export interface ShellTopProps {
  copy: LandingCopy;
  lang: Lang;
  /** The language buttons (the languages the page speaks in the visitor's market). */
  langs: readonly Lang[];
  /** The notice bar's sentence (bar.soon, or bar.open once ordering is open): both have the same length, so the flip moves nothing. */
  barText: string;
  tryHref: string;
  /** Only the live page gives these: the static shell has no handlers and no refs. */
  onLang?: (l: Lang) => void;
  barRef?: Ref<HTMLDivElement>;
  headerRef?: Ref<HTMLElement>;
}

/** Skip link, notice bar and the fixed header with logo, navigation, language switch and the short call to action. */
export function ShellTop({ copy, lang, langs, barText, tryHref, onLang, barRef, headerRef }: ShellTopProps) {
  return (
    <>
      <a className="lp-skip" href="#main">{copy.skip}</a>
      <div className="lp-topbar" id="topbar" ref={barRef} role="region" aria-label={copy.bar.label}>
        <span id="barText">{barText}</span>
      </div>
      <header className="lp-hdr" id="hdr" ref={headerRef}>
        <div className="lp-wrap">
          <a className="lp-logo" href="#top" aria-label={`SnapEyes ${copy.brandTag}`}>
            <LogoMark />
            <span><b>SNAPEYES</b><small>{copy.brandTag}</small></span>
          </a>
          <nav className="lp-nav" id="nav" aria-label={copy.navLabels.main}>
            {NAV_KEYS.map((k) => (
              <a key={k} href={`#${k}`}>{copy.nav[k]}</a>
            ))}
          </nav>
          <div className="lp-hdr-r">
            <div className="lp-seg" role="group" id="langSeg" aria-label={copy.switchLabel}>
              {langs.map((l) => (
                <button key={l} type="button" lang={l} aria-pressed={lang === l} title={LANG_NAMES[l]} onClick={onLang ? () => onLang(l) : undefined}>
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
            <a className="lp-btn lp-btn-line" href={tryHref}>{copy.ctaShort}</a>
          </div>
        </div>
      </header>
    </>
  );
}

export interface ShellHeroProps {
  copy: LandingCopy;
  tryHref: string;
  /** "Digital file from {from}" with the price filled in. Held back (invisible, out of the tab order, its space kept) until the
   *  server has answered about the visitor's prices, so nobody in a price experiment sees the standard price for a moment. */
  priceLine: string;
  pricePending: boolean;
  ctaRef?: Ref<HTMLAnchorElement>;
}

/** The hero section: copy and call to action on the left, the picture with its in-frame label and the disc on the right. */
export function ShellHero({ copy, tryHref, priceLine, pricePending, ctaRef }: ShellHeroProps) {
  const h = copy.hero;
  const pic = heroPicture();
  const disc = heroDisc();
  const f = (s: string) => fill(s, copy.facts);
  return (
    <section className="lp-hero" id="top" aria-labelledby="h1">
      <div className="lp-wrap lp-hero-grid">
        <div className="lp-hero-copy">
          <p className="lp-eyebrow">{h.eyebrow}</p>
          <h1 id="h1">{h.title}</h1>
          <p className="lp-lead">{f(h.lead)}</p>
          <div className="lp-cta-row">
            <a className="lp-btn lp-btn-gold" id="ctaHero" href={tryHref} ref={ctaRef}>
              <span>{copy.cta}</span>
              <Arrow />
            </a>
            <a className="lp-link-quiet" href="#reveal">{h.secondary}</a>
          </div>
          <ul className="lp-micro" id="heroMicro">
            {h.micro.map((x) => (
              <li key={x}>{x}</li>
            ))}
            <li className="lp-price" inert={pricePending || undefined} style={pricePending ? { opacity: 0, userSelect: 'none' } : undefined}>
              <a href="#pricing">{priceLine}</a>
            </li>
          </ul>
          <p className="lp-computer-hint">{h.computerHint}</p>
        </div>
        <figure className="lp-hero-fig" aria-labelledby="heroCap">
          <div className="lp-hero-stage">
            <div className="lp-hero-frame">
              <img id="heroImg" src={pic.src} srcSet={pic.srcset} sizes={HERO_SIZES} width={pic.w} height={pic.h} fetchPriority="high" decoding="async" alt={h.imageAlt} />
              <span className="lp-glint" aria-hidden="true" />
              <div className="lp-frame-chip" data-chip="vis">
                <b>{h.chipTitle}</b>
                <span>{h.chipBody}</span>
              </div>
            </div>
            <a className="lp-disc" href="#reveal" id="heroDisc" aria-label={h.discLink}>
              <img src={disc.src} width={disc.w} height={disc.h} loading="lazy" fetchPriority="low" decoding="async" alt={h.discAlt} />
              <span className="lp-disc-label" aria-hidden="true">{h.discLabel}</span>
            </a>
          </div>
          <figcaption className="lp-hero-cap" id="heroCap">{h.caption}</figcaption>
        </figure>
      </div>
    </section>
  );
}
