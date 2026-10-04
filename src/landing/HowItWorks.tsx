// The "How it works" chapter (BUILD_PLAN section 2): three steps, each with a picture of what you see (the phone at your eye, the
// free preview, the file card), the tips disclosure under step 1 and the call to action. The phone visuals are
// ./PhoneMock.tsx, the file card ./FileCard.tsx, the look css/how.css. Words come from the copy layer; the open wording of
// step 3 ("pay through Stripe") is used only once ordering is open (src/landing/ordering.ts). Importing this file brings its own
// stylesheet, so it can be loaded lazily with its section.
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
  const { ref: railRef, props: railProps } = useScrollableRegion<HTMLOListElement>();
  return (
    <section className="lp-sec" id="how" aria-labelledby="howH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{c.how.eyebrow}</p>
          <h2 id="howH">{c.how.title}</h2>
        </div>
        <ol className="lp-steps" id="steps" ref={railRef} {...railProps(c.how.title)}>
          {c.how.steps.map((s, i) => (
            // the index is the key: the same three nodes stay when the language changes, so an open tips list stays open
            <li className="lp-step" key={i}>
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
        <div className="lp-how-cta">
          <a className="lp-btn lp-btn-gold" href={tryHref}>
            <span>{c.cta}</span>
            <Arrow />
          </a>
        </div>
      </div>
    </section>
  );
}
