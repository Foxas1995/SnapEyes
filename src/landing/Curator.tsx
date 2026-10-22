// The help block of the trust section: the offer to look at a difficult photo, with the mail button. Since 2026-10-22 it names
// no person (the owner: no "Mantas, founder" on the page): no portrait, no name, no role, no note in the first person; the
// seller's representative stays where the law wants him, in the footer and on the legal pages. The block appears only while
// CONTACT_EMAIL is set (src/landing/config.ts, the one place that names the address); the words are the copy's (trust.*).
// Motion (motion spec 6.11): the eyebrow and the title rise like the privacy column's beside it, then the offer and its button.
import type { CSSProperties } from 'react';
import { useCopy } from './copy/useCopy';
import { CONTACT_EMAIL } from './config';
import { Title } from '../motion/Title';

/** a reveal that starts after a delay of this many stagger steps (80 ms each): the title first, then the offer */
const after = (steps: number) => ({ '--i': steps }) as CSSProperties;

export function Curator() {
  const { c } = useCopy();
  const tr = c.trust;
  return CONTACT_EMAIL ? (
    <div>
      <p className="lp-eyebrow" data-reveal="fade-s">{tr.curatorEyebrow}</p>
      <Title text={tr.curatorTitle} />
      <div className="lp-curator">
        <div data-reveal="fade-s" style={after(4)}>
          <p className="lp-offer">{tr.offer}</p>
          <a className="lp-btn lp-btn-line" href={`mailto:${CONTACT_EMAIL}`}>
            <span>{tr.offerCta}</span>
          </a>
        </div>
      </div>
    </div>
  ) : null;
}

export default Curator;
