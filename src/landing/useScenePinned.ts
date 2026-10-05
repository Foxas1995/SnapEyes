// Whether the page can pin a scene right now: motion allowed, 768 px and up, a screen tall enough to hold the stage, overflow: clip supported
// (the same conditions as whenPinned in src/motion/motion.ts, plus the height), the engine switched on (html.mo) and not given up (html.mo-fail:
// then no observer reports and a pin would hold the picture still while the page scrolls under it). A phone, reduced motion, a short window
// and a stalled engine all get the static layout, which holds the same content. The answer follows the window and the root's classes.
import { useSyncExternalStore } from 'react';

/** The media part of the condition. The stage is 100svh minus the header and it holds the copy beside the frame: below 560 px it would not fit. */
export const PIN_QUERY = '(prefers-reduced-motion: no-preference) and (min-width: 48rem) and (min-height: 560px)';

function subscribe(onChange: () => void) {
  const mq = window.matchMedia(PIN_QUERY);
  mq.addEventListener('change', onChange);
  // the engine's classes (mo, mo-fail) are set on the root, the second one up to 3.5 s after boot
  const mo = new MutationObserver(onChange);
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  return () => {
    mq.removeEventListener('change', onChange);
    mo.disconnect();
  };
}

function snapshot() {
  const cl = document.documentElement.classList;
  return window.matchMedia(PIN_QUERY).matches && cl.contains('mo') && !cl.contains('mo-fail') && CSS.supports('overflow', 'clip');
}

export function useScenePinned(): boolean {
  return useSyncExternalStore(subscribe, snapshot, () => false);
}
