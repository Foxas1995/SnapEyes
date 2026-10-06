// "More ways to see it": five pictures that are not on the stage (two of you on walnut, four of you in a frame, in your hands, seen
// from an angle, on a shelf), in a disclosure that is open on a desktop and closed on a phone (where it would add about 450 px of scrolling). The
// rail scrolls sideways; it is a named region with a tab stop so the keyboard can scroll it. Every picture is an AI
// visualisation and carries its chip inside its frame.
//
// Motion (motion spec 6.9): the rail appears as one piece (opacity only: nothing moves inside a scroller); above it a counter ("03 / 05",
// Plus Jakarta Sans with tabular figures, so it never shifts) and a gold hairline of 1 px show how far the rail has been scrolled, directly
// and without a transition; the picture the rail has scrolled to is in full tone and the others a shade softer (.82, no scale: a moving crop
// is jitter, not luxury; the captions are always in full tone); from 768 px two real buttons scroll by one picture and are aria-disabled at
// the ends. The counter, the line and the buttons report and move the scroll position, so they work the same under reduced motion.
import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { asset } from './assets';
import { MORE } from './assets.data';
import { useCopy } from './copy/useCopy';
import { Disclosure, ExampleChip } from './ui';
import './css/more.css';

/** Open on a desktop or when the visitor came by the link #more; read once, on the first render, and left to the visitor after. */
function initiallyOpen(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(min-width: 960px)').matches || window.location.hash === '#more';
}

const two = (n: number) => String(n).padStart(2, '0');

export function MoreRooms() {
  const { c } = useCopy();
  const m = c.more;
  // read once: a later render (a material picked above, a language change) must not reopen what the visitor closed
  const [open0] = useState(initiallyOpen);
  const total = m.scenes.length;

  const rail = useRef<HTMLDivElement>(null);
  const line = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);
  const [atStart, setAtStart] = useState(true);
  const [atEnd, setAtEnd] = useState(false);

  // where the rail has been scrolled to: the line, the counter, the picture in full tone and the ends of the buttons follow it. One read
  // per frame while it scrolls, and again when the rail's box changes (a disclosure that has just been opened, a resized window).
  useEffect(() => {
    const el = rail.current;
    if (!el) return;
    let frame = 0;
    const read = () => {
      frame = 0;
      const max = el.scrollWidth - el.clientWidth;
      const p = max > 1 ? Math.min(1, Math.max(0, el.scrollLeft / max)) : 0;
      if (line.current) line.current.style.scale = `${p} 1`;
      setActive(Math.round(p * (total - 1)));
      setAtStart(el.scrollLeft <= 2);
      setAtEnd(max <= 1 || el.scrollLeft >= max - 2);
    };
    const queue = () => {
      if (!frame) frame = requestAnimationFrame(read);
    };
    el.addEventListener('scroll', queue, { passive: true });
    const ro = new ResizeObserver(queue);
    ro.observe(el);
    return () => {
      el.removeEventListener('scroll', queue);
      ro.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [total]);

  // one picture further: the width of a picture and the gap between two
  function go(dir: 1 | -1) {
    const el = rail.current;
    const card = el?.querySelector('figure');
    if (!el || !card) return;
    const gap = parseFloat(getComputedStyle(el).columnGap) || 0;
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollBy({ left: dir * (card.getBoundingClientRect().width + gap), behavior: calm ? 'auto' : 'smooth' });
  }

  return (
    <Disclosure
      id="more"
      className="lp-more"
      defaultOpen={open0}
      summary={
        <span>
          <b>{m.title}</b>
          <small>{m.intro}</small>
        </span>
      }
    >
      <div className="lp-rail-wrap" data-reveal="soft">
        <div className="lp-rail-bar">
          <span className="lp-rail-count">
            <b>{two(active + 1)}</b> / {two(total)}
          </span>
          <span className="lp-rail-line" aria-hidden="true">
            <i ref={line} />
          </span>
          <button type="button" className="lp-rail-btn" aria-label={m.prev} aria-disabled={atStart || undefined} onClick={() => !atStart && go(-1)}>
            <ArrowLeft aria-hidden="true" strokeWidth={1.8} />
          </button>
          <button type="button" className="lp-rail-btn" aria-label={m.next} aria-disabled={atEnd || undefined} onClick={() => !atEnd && go(1)}>
            <ArrowRight aria-hidden="true" strokeWidth={1.8} />
          </button>
        </div>
        <div className="lp-rail" id="rail" ref={rail} role="region" tabIndex={0} aria-label={m.railLabel}>
          {m.scenes.map((s, i) => {
            const room = MORE.find((r) => r.id === s.id);
            if (!room) return null;
            // the smallest file is the src, every width is in the srcset; the width and height are the widest file's (the same
            // shape). The frame is 280 px high (300 on a desktop), so the picture is that high times its aspect ratio wide.
            const pic = asset(room.base, { pick: 0 });
            const big = asset(room.base, { pick: 100000 });
            const ratio = big.w / big.h;
            return (
              <figure key={s.id} className={i === active ? 'lp-on' : undefined}>
                <div data-chip-area="vis">
                  <img
                    src={pic.src}
                    srcSet={pic.srcset}
                    sizes={`(min-width: 960px) ${Math.round(300 * ratio)}px, ${Math.round(260 * ratio)}px`}
                    width={big.w}
                    height={big.h}
                    loading="lazy"
                    decoding="async"
                    alt={`${c.example.vis}. ${s.c}`}
                  />
                  <ExampleChip variant="vis" />
                </div>
                <figcaption>
                  <b>{s.t}</b>
                  <span>{s.c}</span>
                </figcaption>
              </figure>
            );
          })}
        </div>
      </div>
    </Disclosure>
  );
}
