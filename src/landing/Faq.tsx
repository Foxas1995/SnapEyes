// The FAQ of the new landing (BUILD_PLAN section 2, "FAQ"): sixteen questions in native <details> elements, so Enter and Space,
// the "expanded" state for a screen reader and find in page work without a script. Each item keeps its place by its id, not
// by its position or its words: an open answer stays open when the language changes, when ordering opens (the items about
// ordering take their "open" wording) and when the market changes (on the Australian market the answers about cancelling and
// about a result you do not like are the Australian ones, which copyForMarket swaps in by the same ids). The words are the
// copy's (faq.items, faqAu). Importing this file brings its own stylesheet, so it can be loaded lazily with its section.
import { useCopy } from './copy/useCopy';
import { faqEntries } from './copy/index';
import { useOrderingOpen, useSaleCatalogue } from './ordering';
import { Disclosure } from './ui';
import { Title } from '../motion/Title';
import './css/faq.css';

export function Faq() {
  const { c, fmt } = useCopy();
  const open = useOrderingOpen();
  // the largest number of eyes some style can be ordered for now (the run-time catalogue): the answer about other people's eyes prints it only when it is more than one
  const max = useSaleCatalogue().max;
  return (
    <section className="lp-sec" id="faq" aria-labelledby="faqH">
      <div className="lp-wrap lp-faq-grid">
        <div className="lp-sec-head">
          <p className="lp-eyebrow" data-reveal="fade-s">{c.faq.eyebrow}</p>
          <Title id="faqH" text={c.faq.title} />
        </div>
        {/* the items rise one after the other when the list comes into view (src/motion/motion.ts: a child of data-stagger is revealed on its own) */}
        <div className="lp-faq-list" data-stagger>
          {faqEntries(c, open, max).map((item) => (
            <Disclosure key={item.id} id={`faq-${item.id}`} className="lp-qa" summary={<span>{fmt(item.q)}</span>}>
              <p>{fmt(item.a, { max })}</p>
            </Disclosure>
          ))}
        </div>
      </div>
    </section>
  );
}

export default Faq;
