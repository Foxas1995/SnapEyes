// The trust section of the new landing (BUILD_PLAN section 2, "Trust"): the four promises, the identity line of the seller, the
// founder with his note, and the privacy promise with the link to the privacy policy (the full notice is /privacy, through
// legalHref, so it carries ?lang= and the market's edition). The #privacy anchor of the footer's navigation is the block that
// holds the founder and the privacy promise. The promises must stay true to the privacy policy (src/legal/docs/privacy.ts):
// free previews are not stored, paid orders keep their files (not the phone photo) for 12 months. Importing this file brings
// its own stylesheet, so it can be loaded lazily with its section.
import { useContext } from 'react';
import { CopyContext, useCopy } from './copy/useCopy';
import { TrustLegacy } from './TrustLegacy';
import { useLegalHref } from './links';
import { Never } from './Never';
import { Curator } from './Curator';
import { PrivacyList } from './PrivacyList';
import './css/trust.css';

export function TrustSection() {
  const { c } = useCopy();
  const tr = c.trust;
  const privacyHref = useLegalHref('privacy');
  return (
    <section className="lp-sec" id="trust" aria-labelledby="trustH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{tr.eyebrow}</p>
          <h2 id="trustH">{tr.title}</h2>
        </div>
        <Never />
        <p className="lp-id-line">{tr.idLine}</p>

        <div className="lp-cur-priv" id="privacy">
          <Curator />
          <div>
            <p className="lp-eyebrow">{tr.privacyEyebrow}</p>
            <h2>{tr.privacyTitle}</h2>
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

/** What the page renders: the new section inside a CopyProvider (every visitor the new landing serves, src/landing/gate.ts), today's
 *  trust section outside it (Lithuanian, Hungarian and the forint market keep today's page until their copy exists). Delete the
 *  fallback with TrustLegacy.tsx when the last old section goes. */
export function Trust() {
  return useContext(CopyContext) ? <TrustSection /> : <TrustLegacy />;
}

export default Trust;
