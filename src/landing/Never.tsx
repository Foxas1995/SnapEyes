// The four promises of the trust section ("What we never do"): a numbered list, each item a short title and one sentence. The
// words are the copy's (trust.items); the numbers are decoration, so a screen reader hears the promise, not "01".
// Motion (motion spec 6.11): the promises appear one by one when the list comes into view. Each item is its own reveal (data-reveal="rule",
// data-stagger gives it its place in the row): the hairline above it draws from the left, and its words rise 10 px a moment after the
// line has begun (src/landing/css/trust.css). The numerals are the page's gold hallmark here: no further gold mark is added to a title.
import { useCopy } from './copy/useCopy';

export function Never() {
  const { c } = useCopy();
  return (
    <ul className="lp-never-list" data-stagger>
      {c.trust.items.map((item, i) => (
        // keyed by place, not by words: a language switch changes every word, and a node that is re-keyed is a new node that would be revealed again
        <li key={i} data-reveal="rule">
          <h3>
            <span className="lp-num" aria-hidden="true">
              {String(i + 1).padStart(2, '0')}
            </span>
            <span>{item.t}</span>
          </h3>
          <p>{item.b}</p>
        </li>
      ))}
    </ul>
  );
}

export default Never;
