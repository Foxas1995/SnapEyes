// The close-ups of the new landing (BUILD_PLAN section 2, "Close-ups"): a 1200 px square cut straight from the 4096 px file, with a
// little map of where it was cut, and an AI visualisation of the polished edge of an acrylic print. Two pictures, two kinds of
// honesty: the crop is real engine output and says what it is (its size, and in the intro that the source photo was only 315 px
// wide, so the fine fibres are a reconstruction); the edge is an AI visualisation and carries that label inside the picture.
//
// On a phone the two cards sit side by side in a sideways scroller (the stylesheet); a scroller that really scrolls gets a tab
// stop and a name (useScrollableRegion), so a keyboard user can reach it too. Importing this file brings its own stylesheet.
import { useCopy } from './copy/useCopy';
import { Picture } from './ui';
import { asset } from './assets';
import { FIBRE } from './assets.data';
import { useScrollableRegion } from './useScrollableRegion';
import './css/closeups.css';

// Everything the section says about sizes is read from the picture files and the crop data, not typed: the crop is as wide as
// the rectangle cut from the big file, and the source photo was the phone shot of the before picture (its file name says 315).
const CROP = asset('art/fibre_crop_1200');
const FULL = asset('art/fibre_full_480');
const EDGE = asset('m/macro_acrylic_corner__universe__wide', 1200);
const SOURCE_PHOTO = asset('ui/before-phone-crop-315');

// the distance from one edge of the crop to the other
const extent = (from: number, to: number) => to + -from;
const [X0, Y0, X1, Y1] = FIBRE.crop_px;

// where the crop sits in the whole iris, as the percentages of the locator picture
function locatorBox(): { left: string; top: string; width: string; height: string } {
  const pct = (n: number) => `${((n / FIBRE.of) * 100).toFixed(2)}%`;
  return { left: pct(X0), top: pct(Y0), width: pct(extent(X0, X1)), height: pct(extent(Y0, Y1)) };
}

export function CloseUps() {
  const { c, t } = useCopy();
  const cu = c.closeups;
  const { ref: railRef, props: railProps } = useScrollableRegion<HTMLDivElement>();
  const figures = { n: extent(X0, X1), src: SOURCE_PHOTO.w };
  return (
    <section className="lp-sec" id="closeups" aria-labelledby="cuH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{cu.eyebrow}</p>
          <h2 id="cuH">{cu.title}</h2>
          <p className="lp-intro">{t('closeups.intro', figures)}</p>
        </div>
        <div ref={railRef} className="lp-cu-grid" {...railProps(cu.title, 'group')}>
          <figure className="lp-cu-fibre">
            <Picture asset={CROP} alt={cu.fibreAlt} chip="none" className="lp-cu-img">
              <span className="lp-cu-badge">{t('closeups.badge', figures)}</span>
              <div className="lp-locator" title={cu.locatorLabel}>
                <img src={FULL.src} width={FULL.w} height={FULL.h} loading="lazy" decoding="async" alt={cu.locatorAlt} />
                <i style={locatorBox()} />
              </div>
            </Picture>
            <figcaption className="lp-cu-cap">
              <h3>{t('closeups.fibreTitle', figures)}</h3>
            </figcaption>
          </figure>
          <figure className="lp-cu-edge">
            <Picture asset={EDGE} alt={cu.edgeAlt} chip="vis" sizes="(min-width: 960px) 520px, calc(100vw + -32px)" className="lp-edge-img" />
            <figcaption>
              <div className="lp-edge-cap">
                <span>{cu.edgeCaption}</span>
              </div>
              <div className="lp-cu-cap">
                <h3>{cu.edgeTitle}</h3>
                <p>{cu.edgeBody}</p>
              </div>
            </figcaption>
          </figure>
        </div>
      </div>
    </section>
  );
}

export default CloseUps;
