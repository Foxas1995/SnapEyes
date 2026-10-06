import { useEffect } from 'react';

// A link that names a section (https://snapeyes.com/#pricing, the footer's privacy link from another page, a shared address) has to land
// on that section. The browser does that on load, but only for an element that is there on load: most of this page arrives after it
// (the sections are chunks of their own, src/App.tsx), so the browser finds nothing and leaves the page at the top.
//
// So this hook does what the browser would have done, a little later and more than once: whenever the page's markup changes it
// scrolls the named element to the top of the screen (scroll-padding-top of src/landing/css/base.css keeps it below the fixed
// header), until every lazy section is in (so nothing above the target can still change its height), or the visitor takes over
// (any wheel, touch, key or pointer press: from then on the page is theirs), or twelve seconds have passed. It acts only when the
// address has a fragment that names an element of the page; an address without one is left alone.
const GIVE_UP_MS = 12_000;
const VISITOR_EVENTS = ['wheel', 'touchstart', 'keydown', 'pointerdown'] as const;

export function useHashTarget(): void {
  useEffect(() => {
    let id = '';
    try {
      id = decodeURIComponent(window.location.hash.slice(1));
    } catch {
      return;
    }
    if (!id) return;
    let stopped = false;
    let frame = 0;
    const jump = () => {
      document.getElementById(id)?.scrollIntoView({ behavior: 'instant', block: 'start' });
    };
    const finish = () => {
      stopped = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      clearTimeout(giveUp);
      for (const e of VISITOR_EVENTS) window.removeEventListener(e, finish, true);
    };
    const settle = () => {
      frame = 0;
      if (stopped) return;
      jump();
      // every lazy section is in: one more jump after the layout has settled, then done
      if (!document.querySelector('.lp-slot')) {
        frame = requestAnimationFrame(() => {
          jump();
          finish();
        });
      }
    };
    const observer = new MutationObserver(() => {
      if (!frame && !stopped) frame = requestAnimationFrame(settle);
    });
    observer.observe(document.body, { childList: true, subtree: true });
    for (const e of VISITOR_EVENTS) window.addEventListener(e, finish, { capture: true, passive: true });
    const giveUp = setTimeout(finish, GIVE_UP_MS);
    frame = requestAnimationFrame(settle);
    return finish;
  }, []);
}
