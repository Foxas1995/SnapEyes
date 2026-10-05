// The founder block of the trust section: his own iris as the avatar, a short note in his voice, and the offer to look at a
// difficult photo personally. The offer (and the mail button) appear only while CONTACT_EMAIL is set (src/landing/config.ts, the
// one place that names the address), as on today's page. The name is the seller's representative's first name, from the same
// constants as the footer; the words are the copy's (trust.*).
// Motion (motion spec 6.11): a thin gold ring draws itself around the round portrait (an SVG path with a dash of its own length, 1.4 s,
// from twelve o'clock, clockwise), then the quote and the offer rise. The portrait itself never moves or fades. Without the engine
// (reduced motion, no script, the failsafe) the ring is simply there, drawn.
import type { CSSProperties } from 'react';
import { useCopy } from './copy/useCopy';
import { asset } from './assets';
import { CONTACT_EMAIL, SELLER } from './config';
import { Title } from '../motion/Title';

const AVATAR = asset('art/clean_own_480');
const FOUNDER = SELLER.representative.split(' ')[0];
/** a reveal that starts after a delay of this many stagger steps (80 ms each): the portrait's ring first, then the words */
const after = (steps: number) => ({ '--i': steps }) as CSSProperties;

export function Curator() {
  const { c } = useCopy();
  const tr = c.trust;
  return (
    <div>
      <p className="lp-eyebrow" data-reveal="fade-s">{tr.curatorEyebrow}</p>
      <Title text={tr.curatorTitle} />
      <div className="lp-curator">
        <div className="lp-cur-head">
          <div className="lp-cur-ring" data-reveal="draw">
            <img src={AVATAR.src} width={AVATAR.w} height={AVATAR.h} loading="lazy" decoding="async" alt={tr.curatorPhotoAlt} />
            <svg viewBox="0 0 76 76" aria-hidden="true" focusable="false">
              <path d="M38 1.5a36.5 36.5 0 1 1 0 73a36.5 36.5 0 1 1 0-73" pathLength="1" />
            </svg>
          </div>
          <div>
            {FOUNDER && <b>{FOUNDER}</b>}
            <span>{tr.curatorRole}</span>
          </div>
        </div>
        <blockquote data-reveal="fade" style={after(2.5)}>{tr.curatorNote}</blockquote>
        {CONTACT_EMAIL && (
          <div data-reveal="fade-s" style={after(4)}>
            <p className="lp-offer">{tr.offer}</p>
            <a className="lp-btn lp-btn-line" href={`mailto:${CONTACT_EMAIL}`}>
              <span>{tr.offerCta}</span>
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

export default Curator;
