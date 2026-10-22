// The four promises of the trust section ("What we never do"): a list, each item an icon and a few words (trust.items; the lean pass of
// 2026-10-22 took off the sentence under each one: what they promise is said in full in the FAQ). The icon is decoration, so a screen reader
// hears the promise only.
// Motion (motion spec 6.11): the promises appear one by one when the list comes into view. Each item is its own reveal (data-reveal="rule",
// data-stagger gives it its place in the row): the hairline above it draws from the left, and its words rise 10 px a moment after the
// line has begun (src/landing/css/trust.css). The icons are the gold hallmark of the list: no further gold mark is added to a title.
import { useCopy } from './copy/useCopy';
import { Icon, type IconName } from './Icons';

/** The icon of each promise (trust.items, in order): no repainting, examples labelled as examples, nothing hidden, no rush. */
const PROMISE_ICONS: readonly IconName[] = ['pen', 'tag', 'noEye', 'hourglass'];

export function Never() {
  const { c } = useCopy();
  return (
    <ul className="lp-never-list" data-stagger>
      {c.trust.items.map((item, i) => (
        // keyed by place, not by words: a language switch changes every word, and a node that is re-keyed is a new node that would be revealed again
        <li key={i} data-reveal="rule">
          <h3>
            <Icon name={PROMISE_ICONS[i] ?? 'check'} />
            <span>{item}</span>
          </h3>
        </li>
      ))}
    </ul>
  );
}

export default Never;
