// The active-link marker of the header (motion spec 6.1): ONE 1 px gold hairline that slides under the navigation link of the section
// being read, whose text goes to full colour while the others stay quiet. No second scroll listener: src/landing/shell/chrome.ts calls
// update() from the header's own (the one permanent passive listener of the page). The position is MEASURED, never assumed, because the
// labels change width with the language and with the font: measure() runs again on a language change, when the fonts arrive and when
// the navigation changes size (a ResizeObserver there). While the navigation is hidden (below 960 px, display none) every rect is 0:
// the marker stays out. A section with no link (the close-ups, trust, the closing scene) clears it. Decorative: aria-hidden; the
// link's own state is aria-current="location".
export function navMark(nav: HTMLElement) {
  const links = [...nav.querySelectorAll<HTMLAnchorElement>('a[href^="#"]')];
  const ids = links.map((a) => (a.getAttribute('href') ?? '#').slice(1));
  let current = -1;
  /** Move the marker under the current link (or take it away). A marker that appears for the first time is put in place at once. */
  const place = (jump = false) => {
    const a = links[current];
    if (!a || nav.offsetWidth === 0) { nav.style.setProperty('--mo', '0'); return; }
    if (jump) nav.classList.add('lp-nm-jump');
    nav.style.setProperty('--mx', `${a.offsetLeft}px`);
    nav.style.setProperty('--mw', String(a.offsetWidth));
    nav.style.setProperty('--mo', '1');
    if (jump) { void nav.offsetWidth; requestAnimationFrame(() => nav.classList.remove('lp-nm-jump')); }
  };
  /** Which section holds the line at 45 percent of the screen? Cheap: a handful of rects, once per scroll frame. */
  const update = () => {
    const mid = innerHeight * 0.45;
    let next = -1;
    ids.forEach((id, i) => {
      const el = document.getElementById(id);
      if (!el) return;
      const r = el.getBoundingClientRect();
      if (r.top <= mid && r.bottom > mid) next = i;
    });
    if (next === current) return;
    const first = current < 0;
    if (current >= 0) links[current].removeAttribute('aria-current');
    current = next;
    if (current >= 0) links[current].setAttribute('aria-current', 'location');
    place(first);
  };
  return { update, measure: () => place() };
}
