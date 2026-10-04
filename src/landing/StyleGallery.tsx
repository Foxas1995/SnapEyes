// The styles chapter (BUILD_PLAN section 2, "Styles"): group tabs, the eye colour dots, the legend, the tiles. The composition
// only: the tabs are ./StyleTabs.tsx, the dots ./EyeChips.tsx, a tile ./StyleTile.tsx, the data and the release gate
// ./gallery.ts, the look css/styles.css. Words come from the copy layer, prices from the visitor's own ladder, pictures from
// the asset manifest; nothing is written here. Importing this file brings its own stylesheet, so it can be loaded lazily
// with its section.
import { useContext, useState } from 'react';
import { CopyContext, useCopy } from './copy/useCopy';
import { DEFAULT_EYE, DEFAULT_GROUP, hasEyeSwitch, isWide, tileKey, tilesOf, type EyeId, type GalleryGroup } from './gallery';
import { useLandingPrices } from './prices';
import { EyeChips } from './EyeChips';
import { StyleGalleryLegacy } from './StyleGalleryLegacy';
import { StyleTabs } from './StyleTabs';
import { StyleTile } from './StyleTile';
import { PriceGate } from './ui';
import { useScrollableRegion } from './useScrollableRegion';
import './css/styles.css';

/** The chapter. Inside the new landing's copy layer it is the new gallery; outside it (a visitor the new landing does not
 *  serve yet: Lithuanian, Hungarian, the forint market) it is today's gallery, as it was. The fallback goes with the last old
 *  section (./StyleGalleryLegacy.tsx). */
export function StyleGallery() {
  return useContext(CopyContext) ? <Styles /> : <StyleGalleryLegacy />;
}

function Styles() {
  const { c, t } = useCopy();
  const prices = useLandingPrices();
  const [group, setGroup] = useState<GalleryGroup>(DEFAULT_GROUP);
  const [eye, setEye] = useState<EyeId>(DEFAULT_EYE);
  // the wall views the visitor asked for, by tile key: a key that is there has been asked for once (its picture is loaded)
  const [wall, setWall] = useState<Readonly<Record<string, boolean>>>({});
  const { ref: railRef, props: railProps } = useScrollableRegion<HTMLDivElement>();
  const eyeSwitch = hasEyeSwitch(group);
  const wide = isWide(group);
  return (
    <section className="lp-sec" id="styles" aria-labelledby="stylesH">
      <div className="lp-wrap">
        <div className="lp-sec-head">
          <p className="lp-eyebrow">{c.styles.eyebrow}</p>
          <h2 id="stylesH">{c.styles.title}</h2>
          <p className="lp-intro">{c.styles.intro}</p>
        </div>
        <StyleTabs group={group} onPick={setGroup} />
        <div className="lp-gpanel" id="gPanel" role="tabpanel" tabIndex={0} aria-labelledby={`gtab-${group}`}>
          <p className="lp-group-intro lp-gintro" id="gIntro">{c.styles.groupIntro[group]}</p>
          <p className="lp-legend">{c.styles.legend}</p>
          <EyeChips eye={eye} onPick={setEye} hidden={!eyeSwitch} />
          <div className={wide ? 'lp-grid lp-wide' : 'lp-grid'} id="gGrid" ref={railRef} {...railProps(c.styles.title, 'group')}>
            {tilesOf(group).map((tile) => {
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
