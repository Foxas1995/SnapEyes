// The motion engine of the landing (motion spec section 5.2, as rewritten by the engineering review): plain ES, about 1.4 kB
// gzip, no library. Everything here follows one rule: it never hides content on its own and a broken script never leaves a blank
// page. Hidden-until-revealed states exist only while <html> carries the class "mo" (set by boot() when motion is allowed and
// IntersectionObserver exists) and lift the moment "mo-fail" appears (the failsafe) or the visitor asks for reduced motion.
//
//   boot()      once per page, in the entry, before React renders: switches the hidden states on and starts the failsafe
//   reveals()   once per page, right after boot(): every [data-reveal] node, present or mounted later, gets data-in when it comes
//               into view; children of [data-stagger] get --i (0 to 4) and a default reveal of their own
//   track()     smoothed scroll progress 0..1 for one element (listeners only while the element is within 120 px of the screen)
//   scene()     progress of a pinned scene (a tall wrapper whose first child is a sticky 100svh stage)
//   traverse()  progress of an ordinary element crossing the screen
//   lit()       words of a sentence going from the dim floor to full opacity in sequence (see ./Lit.tsx)
//   whenPinned() runs a scene only while pins are possible (motion allowed, 768 px and up, overflow: clip supported)
//   whenNear()  runs a callback once when an element comes near the screen
//
// Nothing in this file touches layout: scenes write one or two custom properties on their own frame element, never on html or body.
const root = document.documentElement;

/** True while the visitor has not asked for reduced motion. */
export const motionOk = () => matchMedia('(prefers-reduced-motion: no-preference)').matches;

/** True while the page can run scroll driven scenes: html.mo is on (motion allowed, IntersectionObserver present). */
const live = () => root.classList.contains('mo');

// Hide-until-revealed is switched on only when this runs AND motion is allowed AND IntersectionObserver exists. The failsafe is
// cancelled by the first real IntersectionObserver report (reveals() starts a sentinel for it): proof that the engine is alive. If
// nothing is ever reported, html.mo-fail lifts every hidden state 3.5 s after boot.
let failTimer = 0;
export function boot() {
  if (!motionOk() || !('IntersectionObserver' in window)) return;
  root.classList.add('mo');
  const arm = () => { failTimer = window.setTimeout(() => root.classList.add('mo-fail'), 3500); };
  // a page opened in a background tab is not rendered, so no observer can report: the clock starts when the tab is first seen, not before
  // (otherwise every page opened in a new tab would give up its reveals while nobody was looking)
  if (document.hidden) document.addEventListener('visibilitychange', function seen() { if (!document.hidden) { document.removeEventListener('visibilitychange', seen); arm(); } });
  else arm();
}

// Reveal once. Call it ONCE per page (the entry, right after boot()): a MutationObserver picks up every [data-reveal] node React
// mounts later (the lazy sections, the ordering swap, a keyed list, a language with more phrases), so nothing is ever left hidden.
// The state is the attribute data-in, never a class: React rewrites className whenever a className prop changes and would wipe a
// class the observer added. Children of [data-stagger] get --i = 0,1,2,... capped at 4.
let started = false;
export function reveals() {
  if (started || !live()) return;
  started = true;
  const seen = new WeakSet<Element>();
  const io = new IntersectionObserver((es) => {
    clearTimeout(failTimer);
    for (const e of es) if (e.isIntersecting && seen.has(e.target)) { (e.target as HTMLElement).dataset.in = ''; io.unobserve(e.target); }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.01 });
  io.observe(root);   // the sentinel: its first report, whatever it says, proves that observers run
  const watch = (el: Element) => { if (!seen.has(el)) { seen.add(el); io.observe(el); } };
  const stagger = (g: Element) => [...g.children].forEach((c, i) => {
    (c as HTMLElement).style.setProperty('--i', String(Math.min(i, 4)));
    (c as HTMLElement).dataset.reveal ||= 'fade';
    watch(c);
  });
  const scan = (n: ParentNode) => {
    n.querySelectorAll('[data-stagger]').forEach(stagger);
    n.querySelectorAll('[data-reveal]').forEach(watch);
  };
  scan(document);
  new MutationObserver((ms) => ms.forEach((m) => m.addedNodes.forEach((n) => {
    if (!(n instanceof Element)) return;
    if (n.parentElement?.matches('[data-stagger]')) stagger(n.parentElement);
    if (n.matches('[data-reveal]')) watch(n);
    scan(n);
  }))).observe(document.body, { childList: true, subtree: true });
}

// Smoothed scroll progress. measure() returns the raw target 0..1; onP(p) receives the eased value. Listeners exist only while el is
// within 120 px of the viewport; smoothing is frame rate independent. The first measure after the element comes into range is
// applied at once (a reload or an anchor jump into the middle of a scene must not replay the catch up from 0). Does nothing without
// html.mo, so reduced motion never gets inline styles from a scrub.
export function track(el: Element, measure: () => number, onP: (p: number) => void, ease = 0.14) {
  if (!live()) return () => {};
  let target = 0, cur = 0, raf = 0, last = 0, near = false, primed = false;
  const tick = (now: number) => {
    raf = 0;
    cur += (target - cur) * (1 - Math.pow(1 - ease, Math.min(3, (now - last) / 16.67))); last = now;
    if (Math.abs(target - cur) < 0.0008) cur = target;
    onP(cur);
    if (cur !== target) raf = requestAnimationFrame(tick);
  };
  const read = () => {
    target = Math.min(1, Math.max(0, measure()));
    if (!primed) { primed = true; cur = target; }
    if (!raf) { last = performance.now(); raf = requestAnimationFrame(tick); }
  };
  const listen = (on: boolean) => {
    if (on) { addEventListener('scroll', read, { passive: true }); addEventListener('resize', read); }
    else { removeEventListener('scroll', read); removeEventListener('resize', read); }
  };
  const io = new IntersectionObserver(([e]) => {
    if (e.isIntersecting === near) return;
    near = e.isIntersecting;
    listen(near);
    if (near) read(); else primed = false;
  }, { rootMargin: '120px 0px' });
  io.observe(el);
  return () => { io.disconnect(); listen(false); cancelAnimationFrame(raf); };
}

// Runs start() while pins are possible (motion allowed, 768 px and up, overflow: clip supported) and stops it when the window stops
// matching (rotation, resize, the OS setting flipping). start() returns its cleanup. Use it for scene().
export function whenPinned(start: () => () => void) {
  const mq = matchMedia('(prefers-reduced-motion: no-preference) and (min-width: 48rem)');
  let stop: (() => void) | undefined;
  const sync = () => { stop?.(); stop = live() && mq.matches && CSS.supports('overflow', 'clip') ? start() : undefined; };
  sync();
  mq.addEventListener('change', sync);
  return () => { mq.removeEventListener('change', sync); stop?.(); };
}

// Runs cb once, when el comes within `margin` of the viewport. Heavy below the fold images set their src here instead of relying on
// loading="lazy", which on a phone starts 1250 px or more ahead.
export function whenNear(el: Element, cb: () => void, margin = '700px') {
  const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { io.disconnect(); cb(); } }, { rootMargin: `${margin} 0px` });
  io.observe(el);
  return () => io.disconnect();
}

// Tall wrapper whose first child is a sticky 100svh stage: p = 0 when the pin starts, 1 when it ends.
export const scene = (wrap: HTMLElement, onP: (p: number) => void, ease?: number) => track(wrap, () => {
  const span = wrap.offsetHeight - (wrap.firstElementChild as HTMLElement).offsetHeight;
  return span > 0 ? -wrap.getBoundingClientRect().top / span : 0;
}, onP, ease);

// Ordinary element crossing the viewport: p = 0 when its top is at `start` (share of the viewport height), 1 when its bottom is at `end`.
export const traverse = (el: HTMLElement, onP: (p: number) => void, { start = 0.8, end = 0.45, ease = 0.16 } = {}) => track(el, () => {
  const r = el.getBoundingClientRect(), a = innerHeight * start, b = innerHeight * end - r.height;
  return (a - r.top) / (a - b);
}, onP, ease);

// Words go from `floor` to 1 opacity in sequence as p runs 0..1. floor .5 is 4.91:1 on #07090e at every moment.
export function lit(el: HTMLElement, { floor = 0.5, span = 4 } = {}) {
  const words = [...el.querySelectorAll<HTMLElement>('[data-w]')], n = words.length, prev: number[] = [];
  return traverse(el, (p) => words.forEach((w, i) => {
    const v = Math.round((floor + (1 - floor) * Math.min(1, Math.max(0, (p * (n + span) - i) / span))) * 100) / 100;
    if (prev[i] !== v) { prev[i] = v; w.style.opacity = String(v); }
  }));
}
