// The four promises of the trust section ("What we never do"): a numbered list, each item a short title and one sentence. The
// words are the copy's (trust.items); the numbers are decoration, so a screen reader hears the promise, not "01".
import { useCopy } from './copy/useCopy';

export function Never() {
  const { c } = useCopy();
  return (
    <ul className="lp-never-list">
      {c.trust.items.map((item, i) => (
        <li key={item.t}>
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
