// The "How it works" chapter (BUILD_PLAN section 2): three steps, each with a picture of what you see (the phone at your eye, the
// free preview, the file card), the tips disclosure under step 1 and the call to action. The phone visuals are
// ./PhoneMock.tsx, the file card ./FileCard.tsx, the look css/how.css. Words come from the copy layer; the open wording of
// step 3 ("pay through Stripe") is used only once ordering is open (src/landing/ordering.ts). Importing this file brings its own
// stylesheet, so it can be loaded lazily with its section.
//
// Motion (motion spec 6.5, kept to the page's own composition of three columns, each with its own picture): the title rises out of its
// mask, the three steps rise one after the other and a single hairline runs through their numerals, drawing itself from 01 to 03 while
// each numeral warms to gold as the line reaches it (css/how.css). On a phone the steps are a swipe rail: the rail appears as one
// piece, and the step that is most on screen is the current one (aria-current="step", its numeral gold and its title white, the
// others at the dimmest legible tone). Nothing here moves a picture.
import { useEffect, useState, type CSSProperties } from 'react';
import { Title } from '../motion/Title';
import { useCopy } from './copy/useCopy';
import { FileCard } from './FileCard';
import { useTryHref } from './links';
import { useOrderingOpen } from './ordering';
import { PhoneMock } from './PhoneMock';
import { Disclosure } from './ui';
import { useScrollableRegion } from './useScrollableRegion';
import './css/how.css';

function Arrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function HowItWorks() {
  const { c, fmt } = useCopy();
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
  return (
    <section className="lp-sec" id="how" aria-labelledby="howH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow" data-reveal="fade-s">{c.how.eyebrow}</p>
          <Title id="howH" text={c.how.title} />
        </div>
        {/* data-reveal on the list is for the swipe rail (it appears as one piece), on each step for the three columns (css/how.css says
            which of the two is live at which width) */}
        <ol className="lp-steps" id="steps" data-reveal="soft" ref={railRef} {...railProps(c.how.title)}>
          {c.how.steps.map((s, i) => (
            // the index is the key: the same three nodes stay when the language changes, so an open tips list stays open
            <li className="lp-step" key={i} data-reveal="fade" style={{ '--i': i } as CSSProperties} aria-current={scrolls && current === i ? 'step' : undefined}>
              <div className={i === 2 ? 'lp-vis lp-file' : 'lp-vis'}>
                {i === 0 && <PhoneMock kind="camera" open={open} />}
                {i === 1 && <PhoneMock kind="preview" open={open} />}
                {i === 2 && <FileCard />}
              </div>
              <div className="lp-step-body">
                <span className="lp-num">{`0${i + 1}`}</span>
                <h3>{fmt(s.t)}</h3>
                <p>{fmt(open && s.bOpen ? s.bOpen : s.b)}</p>
                {i === 0 && (
                  <Disclosure className="lp-tips" summary={<span>{c.how.tipsTitle}</span>}>
                    <ul>
                      {c.how.tips.map((x, k) => (
                        <li key={k}>{x}</li>
                      ))}
                    </ul>
                  </Disclosure>
                )}
                <p className="lp-vcap">
                  <span>{s.v}</span>
                </p>
              </div>
            </li>
          ))}
        </ol>
        <div className="lp-how-cta" data-reveal="fade">
          <a className="lp-btn lp-btn-gold" href={tryHref}>
            <span>{c.cta}</span>
            <Arrow />
          </a>
        </div>
      </div>
    </section>
  );
}
