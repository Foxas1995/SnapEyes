// The founder block of the trust section: his own iris as the avatar, a short note in his voice, and the offer to look at a
// difficult photo personally. The offer (and the mail button) appear only while CONTACT_EMAIL is set (src/landing/config.ts, the
// one place that names the address), as on today's page. The name is the seller's representative's first name, from the same
// constants as the footer; the words are the copy's (trust.*).
import { useCopy } from './copy/useCopy';
import { asset } from './assets';
import { CONTACT_EMAIL, SELLER } from './config';

const AVATAR = asset('art/clean_own_480');
const FOUNDER = SELLER.representative.split(' ')[0];

export function Curator() {
  const { c } = useCopy();
  const tr = c.trust;
  return (
    <div>
      <p className="lp-eyebrow">{tr.curatorEyebrow}</p>
      <h2>{tr.curatorTitle}</h2>
      <div className="lp-curator">
        <div className="lp-cur-head">
          <img src={AVATAR.src} width={AVATAR.w} height={AVATAR.h} loading="lazy" decoding="async" alt={tr.curatorPhotoAlt} />
          <div>
            {FOUNDER && <b>{FOUNDER}</b>}
            <span>{tr.curatorRole}</span>
          </div>
        </div>
        <blockquote>{tr.curatorNote}</blockquote>
        {CONTACT_EMAIL && (
          <>
            <p className="lp-offer">{tr.offer}</p>
            <a className="lp-btn lp-btn-line" href={`mailto:${CONTACT_EMAIL}`}>
              <span>{tr.offerCta}</span>
            </a>
          </>
        )}
      </div>
    </div>
  );
}

export default Curator;
