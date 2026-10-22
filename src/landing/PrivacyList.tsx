// The privacy promise: four short items, each a disclosure (a native <details>, closed) at every width: the lean pass of 2026-10-22 folded
// them on a desktop too, where they were plain text (the words are the copy's, trust.privacy, unchanged; the policy is one link away).
// Motion (motion spec 6.11): the four items rise one after the other when the list comes into view (data-stagger: the engine in
// src/motion/motion.ts gives each child a reveal of its own).
import { Plus } from 'lucide-react';
import { useCopy } from './copy/useCopy';

export function PrivacyList() {
  const { c } = useCopy();
  return (
    <div className="lp-priv-list" data-stagger>
      {c.trust.privacy.map((item, i) => (
        // keyed by place, not by words: a language switch changes every word, and a node that is re-keyed is a new node that would be revealed again
        <details key={i} className="lp-pv">
          <summary>
            <h3>{item.t}</h3>
            <Plus aria-hidden="true" strokeWidth={2.2} />
          </summary>
          <p>{item.b}</p>
        </details>
      ))}
    </div>
  );
}

export default PrivacyList;
