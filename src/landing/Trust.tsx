// The trust section of the new landing (BUILD_PLAN section 2, "Trust"): the four promises, the identity line of the seller, the
// founder with his note, and the privacy promise with the link to the privacy policy (the full notice is /privacy, through
// legalHref, so it carries ?lang= and the market's edition). The #privacy anchor of the footer's navigation is the block that
// holds the founder and the privacy promise. The promises must stay true to the privacy policy (src/legal/docs/privacy.ts):
// free previews are not stored, paid orders keep their files (not the phone photo) for 12 months. Importing this file brings
// its own stylesheet, so it can be loaded lazily with its section.
// Motion (motion spec 6.11): the headings rise out of their masks, the four promises appear one by one (the hairline above each draws, then its words
// rise), a thin gold ring draws itself around the founder's portrait (the portrait never moves) and his words rise after it, the privacy items rise one
// after the other. The seller's identity line, the privacy footer and the link to the policy never move (src/landing/Never.tsx, Curator.tsx,
// PrivacyList.tsx, css/trust.css).
import { useCopy } from './copy/useCopy';
import { useLegalHref } from './links';
import { Never } from './Never';
import { Curator } from './Curator';
import { PrivacyList } from './PrivacyList';
import { Title } from '../motion/Title';
import './css/trust.css';

export function Trust() {
  const { c } = useCopy();
  const tr = c.trust;
  const privacyHref = useLegalHref('privacy');
  return (
    <section className="lp-sec" id="trust" aria-labelledby="trustH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow" data-reveal="fade-s">{tr.eyebrow}</p>
          <Title id="trustH" text={tr.title} />
        </div>
        <Never />
        <p className="lp-id-line">{tr.idLine}</p>

        <div className="lp-cur-priv" id="privacy">
          <Curator />
          <div>
            <p className="lp-eyebrow" data-reveal="fade-s">{tr.privacyEyebrow}</p>
            <Title text={tr.privacyTitle} />
            <PrivacyList />
            <div className="lp-priv-foot">
              <p>{tr.controller}</p>
              <p>{tr.rights}</p>
              <a href={privacyHref}>{tr.policyLink}</a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Trust;
