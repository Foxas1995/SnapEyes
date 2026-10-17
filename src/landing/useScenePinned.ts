// Whether the page can pin a scene right now: motion allowed, 768 px and up, a screen tall enough to hold the stage, overflow: clip supported
// (the same conditions as whenPinned in src/motion/motion.ts, plus the height), the engine switched on (html.mo) and not given up (html.mo-fail:
// then no observer reports and a pin would hold the picture still while the page scrolls under it). A reduced motion visitor, a short window
// and a stalled engine all get the static layout, which holds the same content. The answer follows the window and the root's classes.
//
// The phone has its own, shorter scene (the owner's request of 2026-10-17, src/landing/RevealScene.tsx with `phone`): the same conditions on a window
// up to 767 px wide (the two never hold together: 768 px is the line), at least 540 px tall (a stage of a frame and three step buttons does not fit
// below that; a phone on its side is wider than 767 px and has no scene), overflow: clip supported (Safari 16) and svh supported (the spacer of the pin).
import { useSyncExternalStore } from 'react';

/** The media part of the condition. The stage is 100svh minus the header and it holds the copy beside the frame: below 560 px it would not fit. */
export const PIN_QUERY = '(prefers-reduced-motion: no-preference) and (min-width: 48rem) and (min-height: 560px)';
/** The phone's scene: a window up to 767 px wide (px, like the stylesheet's own phone rules, so the two always agree). */
export const PHONE_QUERY = '(prefers-reduced-motion: no-preference) and (max-width: 767px) and (min-height: 540px)';

function watch(query: string, supported: () => boolean) {
  return {
    subscribe(onChange: () => void) {
      const mq = window.matchMedia(query);
      mq.addEventListener('change', onChange);
      // the engine's classes (mo, mo-fail) are set on the root, the second one up to 3.5 s after boot
      const mo = new MutationObserver(onChange);
      mo.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
      return () => {
        mq.removeEventListener('change', onChange);
        mo.disconnect();
      };
    },
    snapshot() {
      const cl = document.documentElement.classList;
      return window.matchMedia(query).matches && cl.contains('mo') && !cl.contains('mo-fail') && supported();
    },
  };
}

const pinned = watch(PIN_QUERY, () => CSS.supports('overflow', 'clip'));
// the phone's pin needs its spacer of one screen (100svh, Chrome 108 and Safari 15.4): without it the wrapper would be no taller than the stage and the scene would hold its first state for ever
const phone = watch(PHONE_QUERY, () => CSS.supports('overflow', 'clip') && CSS.supports('height', '100svh'));

export function useScenePinned(): boolean {
  return useSyncExternalStore(pinned.subscribe, pinned.snapshot, () => false);
}

/** The phone's scene (see above). */
export function usePhoneScene(): boolean {
  return useSyncExternalStore(phone.subscribe, phone.snapshot, () => false);
}
