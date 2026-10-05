// The close-ups of the new landing (BUILD_PLAN section 2, "Close-ups"): a 1200 px square cut straight from the 4096 px file, with a
// little map of where it was cut, and an AI visualisation of the polished edge of an acrylic print. Two pictures, two kinds of
// honesty: the crop is real engine output and says what it is (its size, and in the intro that the source photo was only 315 px
// wide, so the fine fibres are a reconstruction); the edge is an AI visualisation and carries that label inside the picture.
//
// On a phone the two cards sit side by side in a sideways scroller (the stylesheet); a scroller that really scrolls gets a tab
// stop and a name (useScrollableRegion), so a keyboard user can reach it too. Importing this file brings its own stylesheet.
//
// Motion (motion spec 6.10, the fourth of the page's signature moments): when most of the crop is on screen the small gold square on the
// map of the iris draws its outline (a plain closed square, 1.2 s: no corner brackets, no crosshair, no pulse), and the crop itself opens
// from the square's own place: its clip-path grows from the square's rectangle (measured in the crop's own box, so it is right at every width)
// to the whole panel in 1.4 s, starting .6 s after the square. The crop's pixels never scale: only the clip moves, so what opens is the
// very square that was cut. The badge and the map are static. The polished edge below opens the way a scene plate does (a mat opening
// from the middle, the settle 1.03 to 1) and its label, set inside the frame, is never touched.
import { useCallback, useEffect, useRef, type CSSProperties } from 'react';
import { Title } from '../motion/Title';
import { useInViewOnce } from './useInView';
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

  // the crop opens from the little square on the map: its rectangle in the crop's own box becomes the starting clip (--crop-from)
  const cropBox = useRef<HTMLDivElement | null>(null);
  const cropSeen = useInViewOnce<HTMLDivElement>(0.45);
  const cropRef = useCallback(
    (el: HTMLDivElement | null) => {
      cropBox.current = el;
      return cropSeen(el);
    },
    [cropSeen],
  );
  const edgeRef = useInViewOnce<HTMLDivElement>(0.3);
  // measured when the browser has laid the crop out (a ResizeObserver reports once as soon as it starts observing, and again when the crop's box
  // changes): no read of a rectangle during the commit, which would force the layout of the whole page inside React's own task
  useEffect(() => {
    const box = cropBox.current;
    const frame = box?.querySelector<HTMLElement>('.lp-cu-img');
    const mark = box?.querySelector<SVGElement>('.lp-loc-sq');
    if (!box || !frame || !mark) return;
    const measure = () => {
      const f = frame.getBoundingClientRect();
      const m = mark.getBoundingClientRect();
      if (!f.width) return;
      box.style.setProperty('--crop-from', `inset(${m.top - f.top}px ${f.right - m.right}px ${f.bottom - m.bottom}px ${m.left - f.left}px)`);
    };
    const ro = new ResizeObserver(measure);
    ro.observe(frame);
    return () => ro.disconnect();
  }, []);
  return (
    <section className="lp-sec" id="closeups" aria-labelledby="cuH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{cu.eyebrow}</p>
          <Title id="cuH" text={cu.title} />
          <p className="lp-intro">{t('closeups.intro', figures)}</p>
        </div>
        <div ref={railRef} className="lp-cu-grid" {...railProps(cu.title, 'group')}>
          <figure className="lp-cu-fibre">
            <div className="lp-cu-open" data-open ref={cropRef}>
              <Picture asset={CROP} alt={cu.fibreAlt} chip="none" className="lp-cu-img">
                <span className="lp-cu-badge">{t('closeups.badge', figures)}</span>
                <div className="lp-locator" title={cu.locatorLabel}>
                  <img src={FULL.src} width={FULL.w} height={FULL.h} loading="lazy" decoding="async" alt={cu.locatorAlt} />
                  {/* the square that marks the cut: a plain closed outline (pathLength 1, so one dash is the whole outline), drawn by css/closeups.css */}
                  <svg className="lp-loc-sq" viewBox="0 0 100 100" style={locatorBox() as CSSProperties} aria-hidden="true" focusable="false">
                    <rect className="lp-loc-back" x="2.25" y="2.25" width="95.5" height="95.5" />
                    <rect className="lp-loc-draw" x="2.25" y="2.25" width="95.5" height="95.5" pathLength={1} />
                  </svg>
                </div>
              </Picture>
            </div>
            <figcaption className="lp-cu-cap">
              <h3>{t('closeups.fibreTitle', figures)}</h3>
            </figcaption>
          </figure>
          <figure className="lp-cu-edge">
            <div className="lp-edge-open" data-open ref={edgeRef}>
              <Picture asset={EDGE} alt={cu.edgeAlt} chip="vis" sizes="(min-width: 960px) 520px, calc(100vw + -32px)" className="lp-edge-img" />
            </div>
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
