// The phone's scenes (the owner's request of 2026-10-17: scroll linked scenes made for phones). The engine (./motion.ts) is untouched: a phone scene
// is a track() or traverse() of the engine, started by whenPhone() below and gated by the same three things as every hidden state of the page:
// a window up to 767 px wide, motion allowed, and <html> carrying "mo" but not "mo-fail" (the engine's failsafe). Every rule of the stylesheets that
// reads what a phone scene writes is under the same condition (@media (max-width: 767px) and (prefers-reduced-motion: no-preference), html.mo:not(.mo-fail)),
// so a desktop, a visitor who asked for reduced motion and a page whose engine gave up never see any of it. A scene writes custom properties on its own
// frame element only, never on html or body, and marks that element with data-scrub the first time it has a value (the stylesheet's phone rules need that mark, so a
// scene whose script never runs leaves the quiet once only reveals of the page exactly as they are) and with data-run while it is under way (put() below).
const PHONE = '(max-width: 767px) and (prefers-reduced-motion: no-preference)';

/** Runs start() while the page is a phone page with a live engine and stops it when the window stops matching (rotation, resize, the OS setting
 *  flipping). start() returns its cleanup. The sibling of whenPinned() in ./motion.ts, which is for 768 px and up. */
export function whenPhone(start: () => () => void) {
  const mq = matchMedia(PHONE);
  const root = document.documentElement.classList;
  let stop: (() => void) | undefined;
  const sync = () => {
    stop?.();
    stop = root.contains('mo') && !root.contains('mo-fail') && mq.matches ? start() : undefined;
  };
  sync();
  mq.addEventListener('change', sync);
  return () => {
    mq.removeEventListener('change', sync);
    stop?.();
  };
}

// The engine's traverse is handed over once by the entry (src/main.tsx), not imported here: a section that the release gate renders on the server (src/landing/shell/gate.tsx,
// the steps of how it works) cannot import the engine, which reads the document the moment it is loaded, and this file must be safe to import anywhere.
let traverse: typeof import('./motion').traverse | undefined;
export const lend = (t: typeof import('./motion').traverse) => { traverse = t; };

/** whenPhone() around the engine's traverse() of an element (nothing until the entry has lent the engine). */
export const scrub = (el: HTMLElement, onP: (p: number) => void, opts?: Parameters<typeof import('./motion').traverse>[2]) => whenPhone(() => (traverse ? traverse(el, onP, opts) : () => {}));

/** Writes a scene's values on its frame element (the custom properties of `vars`) and keeps the two marks the stylesheet reads: data-scrub, once it has a value (the phone's rules
 *  may stand in for the clock's), and data-run while the scene is under way (progress `p` below 1), so that at the end the element carries none of the scene's own styles and is
 *  exactly the static one: nothing clipped, scaled or undrawn is left behind for the picture to differ by. */
export function put(el: HTMLElement, vars: Record<string, string>, p: number) {
  el.dataset.scrub ??= '';
  el.toggleAttribute('data-run', p <= 0.9995);   // the values are written with three decimals: from 0.9995 on they read 1.000 and the frame is the static one
  for (const k in vars) el.style.setProperty(k, vars[k]);
}
