// The Reveal (BUILD_PLAN section 2): "Photo left. Iris right." A real phone photo and the same iris restored, cut through the
// pupil, for three example eyes (grey green, brown, and the owner's own). Next to it what comes from the visitor's photo and
// what the AI adds; under it the three up strip and the quiet call to action. Replaces BeforeAfter.tsx.
//
// Every word is the copy's (c.reveal, c.cta), every picture the asset manifest's (revealEyes), the link to /try is useTryHref.
// The sections below the first screen are meant to be loaded lazily, so this file has a default export for React.lazy.
import { useEffect, useMemo, useRef, useState } from 'react';
import { useCopy } from './copy/useCopy';
import { Pill, useKeepFocus, useRoving } from './ui';
import { RevealSlider } from './RevealSlider';
import { RevealStrip } from './RevealStrip';
import { REVEAL_SIZES, revealEyes, type RevealEye } from './revealEyes';
import type { PictureAsset } from './assets';
import './css/reveal.css';

/** A picture fetched and decoded ahead of the frame, so both layers of the next eye can change in the same frame. */
function ready(a: PictureAsset): Promise<void> {
  return new Promise((done) => {
    const im = new Image();
    im.sizes = REVEAL_SIZES;
    if (a.srcset) im.srcset = a.srcset;
    im.src = a.src;
    im.decode().then(() => done(), () => done());
  });
}

const GIVE_UP_MS = 5000;

/** The eye whose pictures are in the frame. A pick changes the pill at once, but the frame, the note, the scale line and the
 *  strip change together once both layers of the new eye have arrived (or after a few seconds whatever happens): on a slow
 *  connection the half that came first would otherwise show one eye next to the other half of another. The words follow the
 *  language at once, because the eye is looked up again in the current copy. */
function useShownEye(eyes: readonly RevealEye[], picked: string): RevealEye {
  const [shownId, setShownId] = useState(picked);
  const target = eyes.find((e) => e.id === picked) ?? eyes[0];
  const { photo, iris } = target;
  useEffect(() => {
    if (picked === shownId) return;
    let live = true;
    const giveUp = window.setTimeout(() => {
      if (live) setShownId(picked);
    }, GIVE_UP_MS);
    void Promise.all([ready(photo), ready(iris)]).then(() => {
      if (!live) return;
      window.clearTimeout(giveUp);
      setShownId(picked);
    });
    return () => {
      live = false;
      window.clearTimeout(giveUp);
    };
  }, [picked, shownId, photo, iris]);
  return eyes.find((e) => e.id === shownId) ?? eyes[0];
}

export function Reveal() {
  const { c } = useCopy();
  const r = c.reveal;
  const eyes = useMemo(() => revealEyes(r), [r]);
  const [picked, setPicked] = useState(eyes[0].id);
  const shown = useShownEye(eyes, picked);

  // the pills are a radio group with a roving tab stop: one Tab stop for the group, the arrows move and pick
  const wrap = useRef<HTMLDivElement>(null);
  const keepFocus = useKeepFocus(wrap);
  const pick = (id: string) => keepFocus(() => setPicked(id), `[data-eye="${id}"]`);
  const roving = useRoving<HTMLDivElement>((el) => pick(el.dataset.eye ?? ''));

  return (
    <section className="lp-sec" id="reveal" aria-labelledby="revealH">
      <div className="lp-wrap lp-reveal-grid">
        <div className="lp-reveal-text">
          <div className="lp-sec-head">
            <p className="lp-eyebrow">{r.eyebrow}</p>
            <h2 id="revealH">{r.title}</h2>
            <p className="lp-intro">{shown.phone ? r.intro : r.introWeb}</p>
          </div>
          <div className="lp-ai">
            <h3>{r.aiTitle}</h3>
            <dl>
              {r.ai.map((x) => (
                <div key={x.t}>
                  <dt>{x.t}</dt>
                  <dd>{x.b}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
        <div ref={wrap} className="lp-cmp-wrap">
          <RevealSlider eye={shown} />
          <div ref={roving.ref} onKeyDown={roving.onKeyDown} className="lp-pills" role="radiogroup" aria-label={r.eyeGroup}>
            {eyes.map((e) => (
              <Pill key={e.id} role="radio" on={e.id === picked} data-eye={e.id} onClick={() => pick(e.id)}>
                {e.label}
              </Pill>
            ))}
          </div>
        </div>
      </div>
      <RevealStrip eye={shown} />
    </section>
  );
}

export default Reveal;
