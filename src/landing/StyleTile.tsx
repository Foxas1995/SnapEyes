import type { ReactNode } from 'react';
import { useCopy } from './copy/useCopy';
import { artPicture, hasPhotoChip, provenance, tileCopy, tileKey, tileSizes, wallPicture, type EyeId, type GalleryGroup, type GalleryTile } from './gallery';
import type { LandingPricesState } from './prices';
import { ExampleChip, Picture, PriceGate } from './ui';

function WallIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="5" y="5" width="14" height="11" rx="1" />
      <path d="M9 20h6M12 16v4" />
    </svg>
  );
}

/** The line under a tile's name: "One eye, <b>price</b>", "Two eyes, <b>price</b>" or "4 eyes, <b>price</b>". The price comes
 *  from the visitor's own ladder (src/landing/prices.ts); the sentence is the copy's. */
function PriceLine({ tile, prices }: { tile: GalleryTile; prices: LandingPricesState }): ReactNode {
  const { c, t, rich } = useCopy();
  if (tile.price === 'art') return rich(c.styles.priceOne, { price: <b>{prices.art}</b> });
  if (tile.price === 'black') return rich(c.styles.priceOne, { price: <b>{prices.black}</b> });
  if (tile.price === 'two') return rich(c.styles.priceTwo, { price: <b>{prices.price2}</b> });
  const n = tile.n ?? 3;
  return (
    <>
      {t('pricing.eyes', { n })}, <b>{prices.eyes(n)}</b>
    </>
  );
}

export interface StyleTileProps {
  tile: GalleryTile;
  group: GalleryGroup;
  eye: EyeId;
  /** The wall view is on for this tile (only a tile that has one can be on). */
  wallOn: boolean;
  /** The wall picture has been asked for once: its src stays in place afterwards, so flipping back and forth never fetches again. */
  wallAsked: boolean;
  onWall: (key: string) => void;
  prices: LandingPricesState;
}

/** One tile of the gallery: the flat artwork (an Example), optionally the same artwork on a wall (an AI visualisation,
 *  fetched only when asked for), the labels, the name, the price line and whose eye it is.
 *  Labels (BUILD_PLAN section 7): the flat artworks of Mantas's own eye carry no chip, the legend line under the styles intro
 *  is their label; "Example photo" (example.photo) sits in the picture of every tile that shows someone else's eye; the
 *  wall view carries "AI visualisation" (example.vis), which is only visible while the wall is on. */
export function StyleTile({ tile, group, eye, wallOn, wallAsked, onWall, prices }: StyleTileProps) {
  const { c, t } = useCopy();
  const key = tileKey(group, tile);
  const { n: name, d: desc } = tileCopy(c, tile);
  const wide = group === 'two' || group === 'family';
  const sizes = tileSizes(wide);
  const art = artPicture(tile, eye);
  const wall = wallPicture(group, tile, eye);
  const on = wallOn && !!wall;
  const photo = hasPhotoChip(group, tile, eye);
  const prov = provenance(tile, eye);
  return (
    <figure className={on ? 'lp-tile lp-on-wall' : 'lp-tile'} data-k={key}>
      {/* The picture's own chip: "AI visualisation" when the tile has a wall view (shown only while the wall is on), else
          "Example photo" when it shows another person's eye, else none (the legend line is the label). A tile with both
          gets the photo chip as a second layer; the two never show at the same time (css/styles.css). */}
      <Picture
        className="lp-tile-img"
        imgClassName="lp-art"
        asset={art}
        sizes={sizes}
        alt={`${name}. ${desc}`}
        chip={wall ? 'vis' : photo ? 'example' : 'none'}
        photo={!wall && photo}
        imgProps={{ 'aria-hidden': on || undefined, style: tile.square ? { objectFit: 'contain' } : undefined }}
      >
        {wall && (
          <img
            className="lp-wall"
            src={wallAsked ? wall.src : undefined}
            srcSet={wallAsked ? wall.srcset : undefined}
            sizes={wallAsked ? sizes : undefined}
            width={wall.w}
            height={wall.h}
            alt={on ? `${c.example.vis}. ${name}. ${c.wall.captions.acrylic}` : ''}
            aria-hidden={!on}
            decoding="async"
          />
        )}
        {wall && photo && <ExampleChip variant="example" photo />}
        {wall && (
          <button
            type="button"
            className="lp-wallbtn"
            aria-pressed={on}
            aria-label={t(on ? 'styles.wallOffAria' : 'styles.wallOnAria', { name })}
            data-k={key}
            onClick={() => onWall(key)}
          >
            <WallIcon />
            <span>{t(on ? 'styles.wallOff' : 'styles.wallOn')}</span>
          </button>
        )}
      </Picture>
      <figcaption>
        <div className="lp-tile-top">
          <h3>{name}</h3>
          <PriceGate pending={prices.pending} className="lp-price">
            <PriceLine tile={tile} prices={prices} />
          </PriceGate>
        </div>
        <p>{desc}</p>
        <p className="lp-src">{c.styles[prov]}</p>
      </figcaption>
    </figure>
  );
}
