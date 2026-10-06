// The small helpers of the motion of /try and /order (src/motion/flow.css). Plain ES, no library, nothing here touches layout or hides content:
// a helper that fails ends in the finished page, never in a blank one (flow.css says how).
//
//   stillMotion()   true while the visitor has asked for reduced motion (the CSS needs no help with that; a script that starts a timer or a decode
//                   does: it does not start one)
//   watchAway()     once per page, in the entry: html[data-away] while the tab is hidden, which pauses the loops (flow.css)
//   whenDecoded()   resolves when a picture has decoded, or after a failsafe delay whatever happened: the aperture starts on it and never waits for ever
//
// The landing's engine (src/motion/motion.ts: boot, reveals, scenes) is not imported here on purpose: nothing of /try or /order is hidden until it
// is revealed, and a module that both the landing and the tools import would become a shared chunk that the landing then has to fetch.

/** True while the visitor has asked for reduced motion. */
export const stillMotion = (): boolean => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

/** html[data-away] while the tab is hidden: a loop (the arc, the hairline) is paused while nobody can see it. */
export function watchAway(): void {
  if (typeof document === 'undefined') return;
  const set = () => document.documentElement.toggleAttribute('data-away', document.hidden);
  document.addEventListener('visibilitychange', set);
  set();
}

/** How long a picture may take to decode before it is shown anyway, without its opening (the same 3.5 s as the landing's failsafe). */
export const DECODE_MS = 3500;

/** Resolves 'decoded' when the picture at `src` has decoded (img.decode()), 'late' when it did not within `ms` or could not be decoded at all. It
 *  always resolves, so a preview is never held back by a decode that never comes. */
export function whenDecoded(src: string, ms = DECODE_MS): Promise<'decoded' | 'late'> {
  return new Promise((resolve) => {
    let done = false;
    const end = (r: 'decoded' | 'late') => { if (!done) { done = true; clearTimeout(timer); resolve(r); } };
    const timer = setTimeout(() => end('late'), ms);
    try {
      const im = new Image();
      im.src = src;
      im.decode().then(() => end('decoded'), () => end('late'));
    } catch { end('late'); }
  });
}
