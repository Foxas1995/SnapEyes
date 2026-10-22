// The "How it works" chapter (BUILD_PLAN section 2): three steps, each with a picture of what you see (the guide video of how to
// photograph an eye, the free preview, the file card), an icon, a title of two to four words and one short line, and the call to action
// (the lean pass of 2026-10-22: the long step texts, the tips and the captions under the pictures went; the tips are in the FAQ's answer
// about the phone and camera, and the guide video shows them). The guide video is
// src/shared/GuideVideo.tsx (the square cut in the page's language; the owner, 2026-10-22: the phone drawing before it showed the eye far
// too close), the preview's phone ./PhoneMock.tsx, the file card ./FileCard.tsx, the look css/how.css. Words come from the copy layer; the open wording of
// step 3 ("pay through Stripe") is used only once ordering is open (src/landing/ordering.ts). Importing this file brings its own
// stylesheet, so it can be loaded lazily with its section.
//
// Motion (motion spec 6.5, kept to the page's own composition of three columns, each with its own picture): the title rises out of its
// mask, the three steps rise one after the other and a single hairline runs through their numerals, drawing itself from 01 to 03 while
// each numeral warms to gold as the line reaches it (css/how.css). On a phone the steps are a swipe rail: the rail appears as one
// piece, and the step that is most on screen is the current one (aria-current="step", its numeral gold and its title white, the
// others at the dimmest legible tone). Nothing here moves a picture; the guide video of step 1 plays by itself only while half of it is on
// screen, and never under reduced motion (GuideVideo.tsx).
import { useEffect, useState, type CSSProperties } from 'react';
import { Title } from '../motion/Title';
import { put, scrub } from '../motion/phone';
import { GuideVideo } from '../shared/GuideVideo';
import { useCopy } from './copy/useCopy';
import { FileCard } from './FileCard';
import { Icon, type IconName } from './Icons';
import { useTryHref } from './links';
import { useOrderingOpen } from './ordering';
import { PhoneMock } from './PhoneMock';
import { useScrollableRegion } from './useScrollableRegion';
import './css/how.css';

/** The icon of each step: the photo, the preview, the file. */
const STEP_ICONS: readonly IconName[] = ['camera', 'eye', 'file'];

function Arrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function HowItWorks() {
  const { c, fmt, lang } = useCopy();
  const open = useOrderingOpen();
  const tryHref = useTryHref();
  const { ref: railRef, props: railProps, scrolls } = useScrollableRegion<HTMLOListElement>();
  // the step that is most on screen in the swipe rail (the three columns of a wide screen have no current step)
  const [current, setCurrent] = useState(0);
  useEffect(() => {
    const rail = railRef.current;
    if (!rail || !scrolls || !('IntersectionObserver' in window)) return;
    const steps = [...rail.children];
    const seen = new Map<Element, number>();
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) seen.set(e.target, e.intersectionRatio);
        let best = 0;
        steps.forEach((li, i) => {
          if ((seen.get(li) ?? 0) > (seen.get(steps[best]) ?? 0) + 0.02) best = i;
        });
        setCurrent(best);
      },
      { root: rail, threshold: [0, 0.15, 0.3, 0.5, 0.7, 0.9, 1] },
    );
    steps.forEach((li) => io.observe(li));
    return () => io.disconnect();
  }, [railRef, scrolls]);
  // on a phone with the engine running (the owner's request of 2026-10-17) the line through the numerals is drawn by the scroll as the rail crosses the screen: --sp, 0 to 1,
  // is written on the rail and the stylesheet draws one step's hairline after the other from it (css/how.css; src/motion/phone.ts). The steps themselves never move. The engine
  // is not imported here: the release gate renders this section on the server (src/landing/shell/gate.tsx), where the engine cannot be loaded; the entry lends it to phone.ts.
  useEffect(() => {
    const rail = railRef.current;
    return rail ? scrub(rail, (p) => put(rail, { '--sp': p.toFixed(3) }, p), { start: 0.85, end: 0.5 }) : undefined;
  }, [railRef]);
  return (
    <section className="lp-sec" id="how" aria-labelledby="howH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{c.how.eyebrow}</p>
          <Title id="howH" text={c.how.title} />
        </div>
        {/* data-reveal on the list is for the swipe rail (it appears as one piece), on each step for the three columns (css/how.css says
            which of the two is live at which width) */}
        <ol className="lp-steps" id="steps" data-reveal="soft" ref={railRef} {...railProps(c.how.title)}>
          {c.how.steps.map((s, i) => (
            // the index is the key: the same three nodes stay when the language changes
            <li className="lp-step" key={i} data-reveal="fade" style={{ '--i': i } as CSSProperties} aria-current={scrolls && current === i ? 'step' : undefined}>
              <div className={i === 2 ? 'lp-vis lp-file' : 'lp-vis'}>
                {i === 0 && (
                  <GuideVideo src={`/assets/howto/howto-11-${lang}.mp4`} poster={`/assets/howto/howto-11-${lang}.jpg`} w={720} h={720}
                    play={c.how.videoPlay} pause={c.how.videoPause} style={{ width: '100%' }} />
                )}
                {i === 1 && <PhoneMock open={open} />}
                {i === 2 && <FileCard />}
              </div>
              <div className="lp-step-body">
                <span className="lp-num">{`0${i + 1}`}</span>
                <h3>
                  <Icon name={STEP_ICONS[i] ?? 'check'} />
                  {fmt(s.t)}
                </h3>
                <p>{fmt(open && s.bOpen ? s.bOpen : s.b)}</p>
              </div>
            </li>
          ))}
        </ol>
        <div className="lp-how-cta" data-reveal="fade">
          <a className="lp-btn lp-btn-gold gold-metal" href={tryHref}>
            <span>{c.cta}</span>
            <Arrow />
          </a>
        </div>
      </div>
    </section>
  );
}
