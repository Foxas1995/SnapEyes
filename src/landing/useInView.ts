import { useCallback } from 'react';

/** A ref callback that sets the attribute data-in on its element once the element has been `threshold` visible (a share of its own
 *  height, 0 to 1) and then stops watching. It is the one-time trigger of the scenes that should start when most of them is on
 *  screen: the size guide's drawing, the close-up's marker and crop, the plate of the polished edge. The engine's own reveals
 *  (src/motion/motion.ts) start when the first pixel shows, which is right for a line of text and too early for a scene.
 *    <figure ref={useInViewOnce(0.4)} data-draw>
 *  The state is an attribute, never a class (React rewrites className), and the CSS that hides a scene before it starts lives only under
 *  html.mo:not(.mo-fail), so a scene is visible without script, under reduced motion and once the engine's failsafe has fired.
 *  Without IntersectionObserver the attribute is set at once. */
export function useInViewOnce<T extends HTMLElement>(threshold = 0.4) {
  return useCallback(
    (el: T | null) => {
      if (!el || el.dataset.in !== undefined) return;
      if (!('IntersectionObserver' in window)) {
        el.dataset.in = '';
        return;
      }
      const io = new IntersectionObserver(
        ([e]) => {
          if (!e.isIntersecting) return;
          el.dataset.in = '';
          io.disconnect();
        },
        { threshold, rootMargin: '0px 0px -6% 0px' },
      );
      io.observe(el);
      return () => io.disconnect();
    },
    [threshold],
  );
}
