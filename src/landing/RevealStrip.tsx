// Under the Reveal: the three up strip (your photo, your iris, your art), the line that says nothing is ever repainted, the note
// about how the examples were taken, and the quiet call to action ("Your turn"). The strip follows the eye that is on show
// in the frame above it, and fades in 1, 2, 3 the first time it is seen (plain CSS transitions, see css/reveal.css).
import { useEffect, useRef, useState } from 'react';
import { useCopy } from './copy/useCopy';
import { useTryHref } from './links';
import type { RevealEye } from './revealEyes';

export interface RevealStripProps {
  eye: RevealEye;
}

export function RevealStrip({ eye }: RevealStripProps) {
  const { c } = useCopy();
  const tryHref = useTryHref();
  const root = useRef<HTMLDivElement>(null);
  // without IntersectionObserver the strip is simply there
  const [seen, setSeen] = useState(() => !('IntersectionObserver' in window));
  useEffect(() => {
    const el = root.current;
    if (!el || seen) return;
    const io = new IntersectionObserver(
      (es) => {
        if (es[0].isIntersecting) {
          setSeen(true);
          io.disconnect();
        }
      },
      { threshold: 0.3 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [seen]);

  const r = c.reveal;
  const steps = [
    { key: 'photo', pic: eye.stripPhoto, alt: eye.photoAlt, caption: r.strip.photo },
    { key: 'iris', pic: eye.stripIris, alt: eye.irisAlt, caption: r.strip.iris },
    { key: 'art', pic: eye.art, alt: eye.artAlt, caption: r.strip.art },
  ];
  return (
    <div ref={root} className={seen ? 'lp-wrap lp-strip lp-in' : 'lp-wrap lp-strip'}>
      <ol>
        {steps.map((s, i) => (
          <li key={s.key}>
            <figure>
              <div>
                <img src={s.pic.src} width={s.pic.w} height={s.pic.h} loading="lazy" decoding="async" alt={s.alt} />
              </div>
              <figcaption>
                <i>{i + 1}</i>
                {s.caption}
              </figcaption>
            </figure>
          </li>
        ))}
      </ol>
      <p className="lp-never">{r.never}</p>
      <p className="lp-reveal-note">{r.note}</p>
      <div className="lp-your-turn">
        <p>{r.yourTurn}</p>
        <a className="lp-btn lp-btn-gold" href={tryHref}>
          <span>{c.cta}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </a>
      </div>
    </div>
  );
}
