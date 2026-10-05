// The Reveal as a pinned scene (motion spec 6.4, the page's signature moment): from 768 px, while motion is allowed, the section's first
// screen is a stage that holds still (position: sticky) while the visitor scrolls through a tall wrapper, and scroll progress drives one
// frame through three states of the founder's own eye: the phone photo, a gold line crossing the pupil that uncovers the restored iris,
// then an aperture, a circle opening from the pupil, that shows the artwork. Nothing is hidden before it is in view, nothing is scaled,
// blurred or tilted: the clip edge, the line and the ring are the only things that move on the frame (Artwork Charter AC-2, AC-3).
//
// The numbers are in ./revealScript.ts, the engine is src/motion/motion.ts (track: smoothed progress, listeners only while the wrapper is near
// the screen). The frame is driven by custom properties written on the frame itself (never on html or body): --rv-pos (the cut), --rv-ap (the
// aperture), --rv-line and --rv-ring (their opacity; the page's own --r is a radius token, so the spec's names --pos and --r are not used); the
// ring is an SVG circle whose radius is set directly, because its 1 px stroke must not scale with it. The three step rows are real buttons that scroll to their state, so a keyboard has a way to every state. The honesty lines
// (whose eye it is, the photo's size) are static text under the frame. Below 768 px, under reduced motion and when the window is too short,
// Reveal.tsx renders the static layout instead of this one (./useScenePinned.ts): the same words, the pictures in a row, the slider.
import { useEffect, useRef, useState } from 'react';
import { useCopy } from './copy/useCopy';
import type { RevealEye } from './revealEyes';
import { sceneState, STEP_GOTO, type Chip } from './revealScript';
import { Title } from '../motion/Title';
import { track } from '../motion/motion';

/** What the frame says about its width: a 540 px frame from 960 px, else about 46 percent of the screen (css/reveal.css). */
const SCENE_SIZES = '(min-width: 960px) 540px, 46vw';

export function RevealScene({ eye }: { eye: RevealEye }) {
  const { c, t } = useCopy();
  const r = c.reveal;
  const wrap = useRef<HTMLDivElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const frame = useRef<HTMLDivElement>(null);
  const ring = useRef<SVGCircleElement>(null);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const w = wrap.current, s = stage.current, f = frame.current, ap = ring.current;
    if (!w || !s || !f || !ap) return;
    let chips = '';
    return track(
      w,
      () => {
        // p = 0 when the stage has just stuck (its top is at its sticky offset), p = 1 when the wrapper lets it go
        const span = w.offsetHeight - s.offsetHeight;
        return span > 0 ? (parseFloat(getComputedStyle(s).top) - w.getBoundingClientRect().top) / span : 0;
      },
      (p) => {
        const st = sceneState(p);
        f.style.setProperty('--rv-pos', st.pos.toFixed(2));
        f.style.setProperty('--rv-ap', st.r.toFixed(2));
        f.style.setProperty('--rv-line', st.line.toFixed(2));
        f.style.setProperty('--rv-ring', st.ring.toFixed(2));
        ap.setAttribute('r', st.r.toFixed(2));
        const now = st.chips.join(' ');
        if (now !== chips) f.dataset.c = chips = now;
        setStep(st.step);
      },
    );
  }, []);

  /** A click on a step row scrolls to that state: the wrapper's position plus the share of the pin's length. */
  const go = (i: number) => {
    const w = wrap.current, s = stage.current;
    if (!w || !s) return;
    const span = w.offsetHeight - s.offsetHeight;
    const top = window.scrollY + w.getBoundingClientRect().top - parseFloat(getComputedStyle(s).top) + span * STEP_GOTO[i];
    window.scrollTo({ top, behavior: 'smooth' });
  };

  const names = [r.strip.photo, r.strip.iris, r.strip.art];
  const label: Record<Chip, string> = { photo: eye.phone ? r.before : r.beforeWeb, iris: r.after, art: r.strip.art };
  return (
    <div ref={wrap} className="lp-rv-scene">
      <div ref={stage} className="lp-rv-stage">
        <div className="lp-wrap lp-rv-grid">
          <div className="lp-rv-copy">
            <div className="lp-sec-head">
              <p className="lp-eyebrow" data-reveal="fade-s">{r.eyebrow}</p>
              <Title id="revealH" text={r.title} />
              <p className="lp-intro" data-reveal="fade">{eye.phone ? r.intro : r.introWeb}</p>
            </div>
            <ol className="lp-rv-steps" data-stagger>
              {names.map((name, i) => (
                <li key={i}>
                  <button type="button" className="lp-rv-step" aria-current={step === i ? 'step' : undefined} onClick={() => go(i)}>
                    <i aria-hidden="true">{`0${i + 1}`}</i>
                    <span>{name}</span>
                  </button>
                </li>
              ))}
            </ol>
          </div>
          <figure className="lp-rv-fig">
            <div ref={frame} className="lp-rv-frame" data-c="photo">
              <img className="lp-rv-iris" src={eye.iris.src} srcSet={eye.iris.srcset} sizes={SCENE_SIZES} width={eye.iris.w} height={eye.iris.h} loading="lazy" decoding="async" alt={eye.irisAlt} />
              <img className="lp-rv-photo" src={eye.photo.src} srcSet={eye.photo.srcset} sizes={SCENE_SIZES} width={eye.photo.w} height={eye.photo.h} loading="lazy" decoding="async" alt={eye.photoAlt} />
              <img className="lp-rv-art" src={eye.art.src} width={eye.art.w} height={eye.art.h} loading="lazy" decoding="async" alt={eye.artAlt} />
              <svg className="lp-rv-ap" viewBox="0 0 100 100" aria-hidden="true">
                <circle ref={ring} cx="50" cy="50" r="0" fill="none" stroke="currentColor" strokeWidth="1" vectorEffect="non-scaling-stroke" />
              </svg>
              <span className="lp-rv-line" aria-hidden="true" />
              {(['photo', 'iris', 'art'] as const).map((k) => (
                <span key={k} className="lp-rv-chip" data-k={k} aria-hidden="true">{label[k]}</span>
              ))}
            </div>
            <figcaption className="lp-rv-cap">
              <span>{eye.note}</span>
              <span className="lp-rv-scale">{t(eye.phone ? 'reveal.scale' : 'reveal.scaleWeb', { n: eye.n })}</span>
            </figcaption>
          </figure>
        </div>
      </div>
    </div>
  );
}
