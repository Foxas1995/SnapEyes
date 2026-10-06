import { useEffect, useRef } from 'react';

// The pieces of a waiting screen (motion spec 7.3 and 8; the rules are in ./flow.css). Markup only: the look and the motion come from the stylesheet, and
// none of them carries a Tailwind utility (src/motion is not scanned for them, see src/index.css).

/** The drawn check of a finished step. lucide's Check has no pathLength, so a dash of 1 would draw dots: this path has one. `still`: a check that was
 *  already there when the screen opened is not drawn again. */
export const Tick = ({ className = '', still = false }: { className?: string; still?: boolean }) => (
  <svg aria-hidden="true" focusable="false" viewBox="0 0 16 16" className={`wk-tick${still ? ' wk-still' : ''} ${className}`.trim()} fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 8.5 6.5 12 13 4.5" pathLength="1" />
  </svg>
);

/** The waiting arc: a circle of pathLength 100, so stroke-dasharray 22 78 is exactly 22 percent of the ring. It turns while it is on screen and the tab is
 *  visible; scrolled out of the screen it pauses (an IntersectionObserver that never reports leaves it running, which is the safe side). Put it inside
 *  an element with the class wk-disc. */
export const Arc = () => {
  const ref = useRef<SVGSVGElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === 'undefined') return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) el.removeAttribute('data-paused'); else el.setAttribute('data-paused', ''); });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <svg ref={ref} aria-hidden="true" focusable="false" viewBox="0 0 172 172" className="wk-arc">
      <circle cx="86" cy="86" r="85" pathLength="100" />
    </svg>
  );
};

/** The step that is being worked on, and a button that has been pressed: a still 4 px gold dot. */
export const Dot = () => <span aria-hidden="true" className="fx-dot" />;

/** A small thin ring with the arc on it, where a card says it is loading: the same way of waiting as everywhere else (BR-7). */
export const Waiting = () => (
  <span aria-hidden="true" className="wk-disc wk-mini"><Arc /></span>
);
