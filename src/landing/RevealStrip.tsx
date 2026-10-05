// Under the Reveal: the three up strip (your photo, your iris, your art), the line that says nothing is ever repainted, the note
// about how the examples were taken, and the quiet call to action ("Your turn"). The strip follows the eye that is on show
// in the frame above it, and its three pictures rise one after the other the first time they are seen (the engine's reveal and stagger,
// src/motion/motion.ts: 120 ms apart here, see css/reveal.css; under reduced motion and without the engine they are simply there).
import { useCopy } from './copy/useCopy';
import { useTryHref } from './links';
import type { RevealEye } from './revealEyes';

export interface RevealStripProps {
  eye: RevealEye;
}

export function RevealStrip({ eye }: RevealStripProps) {
  const { c } = useCopy();
  const tryHref = useTryHref();
  const r = c.reveal;
  const steps = [
    { key: 'photo', pic: eye.stripPhoto, alt: eye.photoAlt, caption: r.strip.photo },
    { key: 'iris', pic: eye.stripIris, alt: eye.irisAlt, caption: r.strip.iris },
    { key: 'art', pic: eye.art, alt: eye.artAlt, caption: r.strip.art },
  ];
  return (
    <div className="lp-wrap lp-strip">
      <ol data-stagger>
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
      <div className="lp-your-turn" data-reveal="fade">
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
