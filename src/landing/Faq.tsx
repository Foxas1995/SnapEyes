// The FAQ of the new landing (BUILD_PLAN section 2, "FAQ"): sixteen questions in native <details> elements, so Enter and Space,
// the "expanded" state for a screen reader and find in page work without a script. Each item keeps its place by its id, not
// by its position or its words: an open answer stays open when the language changes, when ordering opens (the items about
// ordering take their "open" wording) and when the market changes (on the Australian market the answers about cancelling and
// about a result you do not like are the Australian ones, which copyForMarket swaps in by the same ids). The words are the
// copy's (faq.items, faqAu). Importing this file brings its own stylesheet, so it can be loaded lazily with its section.
import { useContext } from 'react';
import { CopyContext, useCopy } from './copy/useCopy';
import { faqEntries } from './copy/index';
import { useOrderingOpen } from './ordering';
import { FaqLegacy } from './FaqLegacy';
import { Disclosure } from './ui';
import './css/faq.css';

export function FaqSection() {
  const { c, fmt } = useCopy();
  const open = useOrderingOpen();
  return (
    <section className="lp-sec" id="faq" aria-labelledby="faqH">
      <div className="lp-wrap lp-faq-grid">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{c.faq.eyebrow}</p>
          <h2 id="faqH">{c.faq.title}</h2>
        </div>
        <div className="lp-faq-list">
          {faqEntries(c, open).map((item) => (
            <Disclosure key={item.id} id={`faq-${item.id}`} className="lp-qa" summary={<span>{fmt(item.q)}</span>}>
              <p>{fmt(item.a)}</p>
            </Disclosure>
          ))}
        </div>
      </div>
    </section>
  );
}

/** What the page renders: the new section inside a CopyProvider (every visitor the new landing serves, src/landing/gate.ts), today's
 *  FAQ outside it (Lithuanian, Hungarian and the forint market keep today's page until their copy exists). Delete the fallback
 *  with FaqLegacy.tsx when the last old section goes. */
export function Faq() {
  return useContext(CopyContext) ? <FaqSection /> : <FaqLegacy />;
}

export default Faq;
