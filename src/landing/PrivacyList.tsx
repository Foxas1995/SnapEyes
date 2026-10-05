// The privacy promise: four short items. On a phone each is a disclosure (a native <details>, closed), from 960 px up they are
// plain text, so a desktop visitor has no phantom tab stops: the same rule as the prototype (renderTrust), now from one media
// query that the component follows when the window changes. The words are the copy's (trust.privacy).
// Motion (motion spec 6.11): the four items rise one after the other when the list comes into view (data-stagger: the engine in
// src/motion/motion.ts gives each child a reveal of its own).
import { Plus } from 'lucide-react';
import { useCopy } from './copy/useCopy';
import { useMediaQuery } from './ui';

export function PrivacyList() {
  const { c } = useCopy();
  const plain = useMediaQuery('(min-width: 960px)');
  return (
    <div className="lp-priv-list" data-stagger>
      {c.trust.privacy.map((item, i) =>
        plain ? (
          // keyed by place, not by words: a language switch changes every word, and a node that is re-keyed is a new node that would be revealed again
          <div key={i} className="lp-pv lp-pv-plain">
            <h3>{item.t}</h3>
            <p>{item.b}</p>
          </div>
        ) : (
          <details key={i} className="lp-pv">
            <summary>
              <h3>{item.t}</h3>
              <Plus aria-hidden="true" strokeWidth={2.2} />
            </summary>
            <p>{item.b}</p>
          </details>
        ),
      )}
    </div>
  );
}

export default PrivacyList;
