import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';
import { useCopy } from './copy/useCopy';
import type { RunCatalogue } from '../shared/catalogue';
import { tileState } from './tileState';
import { artPicture, hasPhotoChip, provenance, tileCopy, tileKey, tileSizes, wallPicture, type EyeId, type GalleryGroup, type GalleryTile } from './gallery';
import type { LandingPricesState } from './prices';
import { ExampleChip, Picture, PriceGate, type PictureAsset } from './ui';

function WallIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="5" y="5" width="14" height="11" rx="1" />
      <path d="M9 20h6M12 16v4" />
    </svg>
  );
}

/** The line under a tile's name: "One eye, <b>price</b>", "Two eyes, <b>price</b>" or "4 eyes, <b>price</b>". The price comes
 *  from the visitor's own ladder (src/landing/prices.ts); the sentence is the copy's. Only a tile that can be bought now gets it. */
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
  /** What can be bought now (src/shared/catalogue.ts saleCatalogue: the run-time catalogue while ordering is open, nothing otherwise). The tile prints its price only
   *  when its style is in it for the tile's number of eyes (src/landing/tileState.ts); every other tile says Soon. */
  sale: RunCatalogue;
  /** How the tile arrives: 'reveal' (the first grid: it rises when it scrolls into view) or 'swap' (after the visitor changed the group:
   *  it fades in, nothing rises). */
  enter: 'reveal' | 'swap';
  /** The tile's place in its grid: the stagger of the arrival. */
  index: number;
}

/** Why a tile keeps the picture it had: when the eye colour changes, the old picture stays on top until the new one has loaded, then fades
 *  out over it (a cross fade between two whole pictures, .42 s, no scale and no blur). Under reduced motion there is no old picture
 *  to keep: the new one simply replaces it. */
interface Shown { cur: PictureAsset; prev: PictureAsset | null; ready: boolean }
const calm = () => typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** One tile of the gallery: the flat artwork (an Example), optionally the same artwork on a wall (an AI visualisation,
 *  fetched only when asked for), the labels, the name, the price line and whose eye it is.
 *  Labels (BUILD_PLAN section 7): the flat artworks of Mantas's own eye carry no chip, the legend line under the styles intro
 *  is their label; "Example photo" (example.photo) sits in the picture of every tile that shows someone else's eye; the
 *  wall view carries "AI visualisation" (example.vis), which is only visible while the wall is on. */
export function StyleTile({ tile, group, eye, wallOn, wallAsked, onWall, prices, sale, enter, index }: StyleTileProps) {
  const { c, t } = useCopy();
  // for sale now: ordering is open and the run-time catalogue lists the tile's style as live for the tile's number of eyes (src/landing/tileState.ts, the style is
  // src/landing/tileStyle.ts); else the tile says Soon and prints no price. The name is the registry's.
  const state = tileState(tile.id, sale);
  const forSale = state.sale === 'sale';
  const key = tileKey(group, tile);
  const { n: name, d: desc } = tileCopy(c, tile);
  const wide = group === 'two' || group === 'family';
  const sizes = tileSizes(wide);
  const art = artPicture(tile, eye);
  // adjusting state while rendering is the documented way to derive it from a prop: the guard ends after one round
  const [shown, setShown] = useState<Shown>({ cur: art, prev: null, ready: false });
  if (shown.cur.src !== art.src) setShown({ cur: art, prev: calm() ? null : (shown.prev ?? shown.cur), ready: false });
  // the new picture's load event is what starts the fade of the old one; if it never comes, the old picture must not stay on top
  const waiting = !!shown.prev && !shown.ready;
  useEffect(() => {
    if (!waiting) return;
    const id = window.setTimeout(() => setShown((p) => ({ ...p, ready: true })), 2500);
    return () => window.clearTimeout(id);
  }, [waiting]);
  const wall = wallPicture(group, tile, eye);
  const on = wallOn && !!wall;
  const photo = hasPhotoChip(group, tile, eye);
  const prov = provenance(tile, eye);
  return (
    <figure
      className={`lp-tile${enter === 'swap' ? ' lp-tile-in' : ''}${on ? ' lp-on-wall' : ''}`}
      data-k={key}
      data-state={state.sale}
      data-reveal={enter === 'reveal' ? 'fade' : undefined}
      style={{ '--i': Math.min(index, 4), '--j': Math.min(index, 5) } as CSSProperties}
    >
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
        imgProps={{
          'aria-hidden': on || undefined,
          style: tile.square ? { objectFit: 'contain' } : undefined,
          onLoad: () => setShown((p) => (p.ready ? p : { ...p, ready: true })),
          onError: () => setShown((p) => ({ ...p, prev: null })),
        }}
      >
        {shown.prev && (
          <img
            className={`lp-art lp-ghost${shown.ready ? ' lp-out' : ''}`}
            src={shown.prev.src}
            srcSet={shown.prev.srcset}
            sizes={shown.prev.srcset ? sizes : undefined}
            width={shown.prev.w}
            height={shown.prev.h}
            alt=""
            aria-hidden="true"
            decoding="async"
            style={tile.square ? { objectFit: 'contain' } : undefined}
            onAnimationEnd={() => setShown((p) => ({ ...p, prev: null }))}
          />
        )}
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
            {forSale ? <PriceLine tile={tile} prices={prices} /> : <span className="lp-soon">{c.styles.soonTag}</span>}
          </PriceGate>
        </div>
        {/* a price next to a picture of a printed piece says what the price is for (the wall view only; the flat artwork is the file); a tile with no price (it says Soon) has
            nothing to explain (release review H-m8) */}
        {on && forSale && <p className="lp-file">{t('styles.wallFile')}</p>}
        <p>{desc}</p>
        <p className="lp-src">{c.styles[prov]}</p>
      </figcaption>
    </figure>
  );
}
