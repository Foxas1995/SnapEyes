// "More ways to see it": four pictures that are not on the stage (in your hands, on a shelf, two of you in a hall, seen from an
// angle), in a disclosure that is open on a desktop and closed on a phone (where it would add about 450 px of scrolling). The
// rail scrolls sideways; it is a named region with a tab stop so the keyboard can scroll it. Every picture is an AI
// visualisation and carries its chip inside its frame.
import { useState } from 'react';
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

export function MoreRooms() {
  const { c } = useCopy();
  const m = c.more;
  // read once: a later render (a material picked above, a language change) must not reopen what the visitor closed
  const [open0] = useState(initiallyOpen);
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
      <div className="lp-rail" id="rail" role="region" tabIndex={0} aria-label={m.railLabel}>
        {m.scenes.map((s) => {
          const room = MORE.find((r) => r.id === s.id);
          if (!room) return null;
          // the smallest file is the src, every width is in the srcset; the width and height are the widest file's (the same
          // shape). The frame is 280 px high (300 on a desktop), so the picture is that high times its aspect ratio wide.
          const pic = asset(room.base, { pick: 0 });
          const big = asset(room.base, { pick: 100000 });
          const ratio = big.w / big.h;
          return (
            <figure key={s.id}>
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
    </Disclosure>
  );
}
