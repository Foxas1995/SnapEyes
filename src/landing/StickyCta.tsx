// The sticky call to action on phones (prototype: #sticky): one gold button fixed to the bottom of the screen below 768 px.
//
//   <StickyBar heroRef={heroCta} />      anywhere in the page, after the sections
//
// It appears once the hero's own button has scrolled away and steps aside while ANY inline gold button is in view (the Reveal's
// "Your turn" row, the size guide, how it works, the pricing block, the closing scene ...) and while the pricing block is in view,
// so there is never a second gold button next to the one the visitor is looking at. The sections are lazy and arrive after this
// component, so it does not ask them to register: it looks for `a.lp-btn-gold` and `#pricing` in the document and looks again when
// the page's markup changes (one MutationObserver, scanned at most once per frame). Anything it finds is watched with
// IntersectionObserver; a node that leaves the page is forgotten.
// A hidden bar is out of the keyboard order and the accessibility tree (inert, aria-hidden, tabindex -1, and visibility hidden from
// the CSS), so a screen reader never meets a button that is not on screen. While it is shown it is a named region (the short button
// words, copy ctaShort): a fixed bar outside every landmark is an axe "region" finding, and the prototype only ever ran axe with it hidden.
import { useEffect, useRef, useState, type RefObject } from 'react';
import { useCopy } from './copy/useCopy';
import { useTryHref } from './links';

// Today's sticky bar, for the visitors the new landing does not serve yet (src/landing/gate.ts). Delete with that fallback.
export { StickyCta } from './legacy/StickyCta';

/** Which elements make the bar step aside: every inline gold button, and the pricing block. */
const SHOWS_OWN_ACTION = 'a.lp-btn-gold, #pricing';

export function StickyBar({ heroRef }: { heroRef?: RefObject<HTMLElement | null> }) {
  const { c } = useCopy();
  const tryHref = useTryHref();
  const bar = useRef<HTMLDivElement>(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const self = bar.current;
    if (!self || typeof IntersectionObserver === 'undefined') return;
    const hero = heroRef?.current ?? null;
    let past = !hero;                       // without a hero button to wait for, only the other buttons decide
    const inView = new Set<Element>();
    const watched = new Set<Element>();
    const update = () => {
      const next = past && inView.size === 0;
      setShow((was) => (was === next ? was : next));
    };

    // the hero button: the bar may show once it has gone up past the top of the screen
    const heroObserver = hero
      ? new IntersectionObserver((entries) => {
          for (const e of entries) past = !e.isIntersecting && e.boundingClientRect.top < 0;
          update();
        })
      : null;
    if (hero) heroObserver?.observe(hero);

    // every other gold button and the pricing block: in view (inside the screen less 8 percent top and bottom) hides the bar
    const others = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) inView.add(e.target);
          else inView.delete(e.target);
        }
        update();
      },
      { rootMargin: '-8% 0px -8% 0px' },
    );
    const scan = () => {
      for (const el of document.querySelectorAll(SHOWS_OWN_ACTION)) {
        if (el === hero || self.contains(el) || watched.has(el)) continue;
        watched.add(el);
        others.observe(el);
      }
      for (const el of watched) {
        if (el.isConnected) continue;
        watched.delete(el);
        inView.delete(el);
        others.unobserve(el);
      }
      update();
    };
    scan();

    let frame = 0;
    const later = () => {
      if (!frame) frame = requestAnimationFrame(() => { frame = 0; scan(); });
    };
    const changes = new MutationObserver(later);
    changes.observe(document.body, { childList: true, subtree: true });

    return () => {
      if (frame) cancelAnimationFrame(frame);
      changes.disconnect();
      heroObserver?.disconnect();
      others.disconnect();
    };
  }, [heroRef]);

  return (
    <div className={show ? 'lp-sticky lp-show' : 'lp-sticky'} id="sticky" ref={bar} role="region" aria-label={c.ctaShort} aria-hidden={!show} inert={!show || undefined}>
      <a className="lp-btn lp-btn-gold" href={tryHref} tabIndex={show ? 0 : -1}>
        <span>{c.cta}</span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      </a>
    </div>
  );
}
