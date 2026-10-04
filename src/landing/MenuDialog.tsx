// The page's links in a real dialog, for the widths where the header has no room for its navigation (below 960 px). A PURE component (props
// in, markup out, no hook, no window): the same markup is rendered to static HTML at build time (the prerendered first screen) and live.
//
// It is a native <dialog> opened with showModal(), so the browser does the hard parts: the focus is kept inside, the page behind is inert,
// Escape closes it, the focus returns to the button that opened it. The close button is a <form method="dialog">: it closes the dialog with
// no script at all. One delegated handler (src/landing/shell/scripts.ts menuScript, inline in index.html) opens it from the header's menu
// button and closes it when a link is chosen, so the menu works before React has started and keeps working after it took the page over.
// The page's hash links stay plain links. The dialog fades and rises in .5 s (css/header.css; under reduced motion it just appears).
import type { CSSProperties } from 'react';
import type { LandingCopy } from './copy/types';
import { NAV_KEYS } from './Header';

export function MenuDialogView({ copy, tryHref }: { copy: LandingCopy; tryHref: string }) {
  return (
    <dialog className="lp-menu" id="menu" aria-label={copy.navLabels.menu}>
      <div className="lp-menu-in lp-wrap">
        <form method="dialog" className="lp-menu-bar">
          <button type="submit" className="lp-menu-x" aria-label={copy.ui.close}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </form>
        <nav aria-label={copy.navLabels.main}>
          <ul>
            {NAV_KEYS.map((k, i) => (
              <li key={k} style={{ '--i': i } as CSSProperties}>
                <a href={`#${k}`}>{copy.nav[k]}</a>
              </li>
            ))}
          </ul>
        </nav>
        <a className="lp-btn lp-btn-gold" href={tryHref}>
          <span>{copy.cta}</span>
        </a>
      </div>
    </dialog>
  );
}
