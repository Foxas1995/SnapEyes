// The behaviour of the notice bar and the fixed header (the prototype's initHeader): the header sits under the bar while the bar
// is on screen and follows it up as the page scrolls, goes solid after 24 px, and --bar-h (the bar's height, which places the
// header and the hero) follows the bar when the window is resized, the fonts arrive or the bar's words change. No re-render
// per scroll event: the class and the offset (a transform) are set on the elements directly.
import { useLayoutEffect, useRef, type RefObject } from 'react';
import { navMark } from './navMark';

export function useHeaderChrome(barRef: RefObject<HTMLElement | null>, headerRef: RefObject<HTMLElement | null>, barText: string, lang: string): void {
  // the marker under the navigation link of the section being read (src/landing/shell/navMark.ts)
  const mark = useRef<ReturnType<typeof navMark> | null>(null);
  useLayoutEffect(() => {
    const bar = barRef.current;
    const hdr = headerRef.current;
    if (!bar || !hdr) return;
    const root = document.documentElement;
    const nav = hdr.querySelector<HTMLElement>('.lp-nav');
    const m = nav ? navMark(nav) : null;
    mark.current = m;
    let ticking = false;
    const place = () => {
      ticking = false;
      const bh = bar.offsetHeight;
      root.style.setProperty('--bar-h', `${bh}px`);
      const y = window.scrollY;
      // a transform, not `top`: the header follows the bar every frame, and a layout property would be a layout shift each time
      hdr.style.transform = `translateY(${Math.max(0, bh - y)}px)`;
      hdr.classList.toggle('lp-solid', y > 24);
      m?.update();
    };
    const onScroll = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(place);
      }
    };
    place();
    window.addEventListener('resize', place);
    window.addEventListener('scroll', onScroll, { passive: true });
    void document.fonts?.ready.then(place);
    // the labels change width with the language and the font, and the navigation appears and disappears with the width
    const ro = nav && m && typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => m.measure()) : null;
    if (nav) ro?.observe(nav);
    return () => {
      window.removeEventListener('resize', place);
      window.removeEventListener('scroll', onScroll);
      ro?.disconnect();
      mark.current = null;
      hdr.style.transform = '';
    };
  }, [barRef, headerRef]);

  // the bar's sentence changed (ordering opened, another language): its height may have too, and the navigation's labels have another width
  useLayoutEffect(() => {
    const bar = barRef.current;
    if (bar) document.documentElement.style.setProperty('--bar-h', `${bar.offsetHeight}px`);
    mark.current?.measure();
  }, [barRef, barText, lang]);
}
