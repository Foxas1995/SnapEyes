import { useEffect, useRef, useState } from 'react';

/** A rail that really scrolls sideways (the style tiles and the three steps on a phone) gets a tab stop and a name, so a
 *  keyboard user can scroll it too (axe: scrollable-region-focusable). A rail that fits gets neither. The page measures
 *  when the rail's box changes, when its children change and when the window is resized, never while rendering.
 *    const rail = useScrollableRegion<HTMLDivElement>();
 *    <div ref={rail.ref} {...rail.props(label, 'group')}>...</div>
 *  role: 'group' for a plain div (a named group is what a screen reader needs to announce it); leave it out on an element
 *  that has a role of its own, such as the <ol> of the steps (the list stays a list). */
export function useScrollableRegion<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [scrolls, setScrolls] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const measure = () => setScrolls(el.scrollWidth > el.clientWidth + 2);
    // a ResizeObserver reports once when it starts observing, which is the first measurement
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    const children = new MutationObserver(measure);
    children.observe(el, { childList: true });
    return () => {
      resize.disconnect();
      children.disconnect();
    };
  }, []);
  const props = (label: string, role?: 'group') => (scrolls ? { tabIndex: 0, 'aria-label': label, role } : {});
  return { ref, scrolls, props };
}
