// The styles chapter (BUILD_PLAN section 2, "Styles"): group tabs, the eye colour dots, the legend, the tiles. The composition
// only: the tabs are ./StyleTabs.tsx, the dots ./EyeChips.tsx, a tile ./StyleTile.tsx, the data and the release gate
// ./gallery.ts, the look css/styles.css. Words come from the copy layer, prices from the visitor's own ladder, pictures from
// the asset manifest; nothing is written here. Importing this file brings its own stylesheet, so it can be loaded lazily
// with its section.
//
// Motion (motion spec 6.6): the title rises out of its mask; the tiles rise one after the other the first time the grid comes into view
// (fade up, 90 ms apart, the index capped at 4: tiles are artworks, so no scale, no blur, no tilt); a change of group is a repeated
// action and stays quiet: the new tiles only fade in, 300 ms, 40 ms apart, no rise. On a phone the tiles are a swipe rail, which appears
// as one piece. A tile's picture cross-fades when the eye colour changes (StyleTile.tsx).
import { useState } from 'react';
import { Title } from '../motion/Title';
import { useCopy } from './copy/useCopy';
import { DEFAULT_EYE, DEFAULT_GROUP, hasEyeSwitch, isWide, tileKey, tilesOf, type EyeId, type GalleryGroup } from './gallery';
import { useLandingPrices } from './prices';
import { EyeChips } from './EyeChips';
import { StyleTabs } from './StyleTabs';
import { StyleTile } from './StyleTile';
import { PriceGate } from './ui';
import { useScrollableRegion } from './useScrollableRegion';
import './css/styles.css';

export function StyleGallery() {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const [group, setGroup] = useState<GalleryGroup>(DEFAULT_GROUP);
  const [eye, setEye] = useState<EyeId>(DEFAULT_EYE);
  // the wall views the visitor asked for, by tile key: a key that is there has been asked for once (its picture is loaded)
  // false until the visitor has changed the group once: the first grid is revealed by scrolling, the later ones fade in on their own
  const [swapped, setSwapped] = useState(false);
  const pickGroup = (next: GalleryGroup) => {
    if (next === group) return;
    setSwapped(true);
    setGroup(next);
  };
  const [wall, setWall] = useState<Readonly<Record<string, boolean>>>({});
  const { ref: railRef, props: railProps } = useScrollableRegion<HTMLDivElement>();
  const eyeSwitch = hasEyeSwitch(group);
  const wide = isWide(group);
  return (
    <section className="lp-sec" id="styles" aria-labelledby="stylesH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow" data-reveal="fade-s">{c.styles.eyebrow}</p>
          <Title id="stylesH" text={c.styles.title} />
          <p className="lp-intro">{c.styles.intro}</p>
        </div>
        <StyleTabs group={group} onPick={pickGroup} />
        <div className="lp-gpanel" id="gPanel" role="tabpanel" tabIndex={0} aria-labelledby={`gtab-${group}`}>
          <p className="lp-group-intro lp-gintro" id="gIntro">{c.styles.groupIntro[group]}</p>
          <p className="lp-legend">{c.styles.legend}</p>
          <EyeChips eye={eye} onPick={setEye} hidden={!eyeSwitch} />
          <div className={wide ? 'lp-grid lp-wide' : 'lp-grid'} id="gGrid" data-reveal="soft" ref={railRef} {...railProps(c.styles.title, 'group')}>
            {tilesOf(group).map((tile, n) => {
              const key = tileKey(group, tile);
              return (
                <StyleTile
                  key={key}
                  tile={tile}
                  group={group}
                  eye={eye}
                  wallOn={!!wall[key]}
                  wallAsked={key in wall}
                  onWall={(k) => setWall((w) => ({ ...w, [k]: !w[k] }))}
                  prices={prices}
                  enter={swapped ? 'swap' : 'reveal'}
                  index={n}
                />
              );
            })}
            {wide && (
              <div className="lp-combo">
                <h3>{c.styles.comboTitle}</h3>
                <p>
                  <PriceGate pending={prices.pending}>{t('styles.comboBody', { price: prices.price })}</PriceGate>
                </p>
                <a className="lp-btn lp-btn-line" href="#pricing">{c.nav.pricing}</a>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
