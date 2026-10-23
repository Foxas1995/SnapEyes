// The SnapEyes logo: the owner's own design (2026-10-22), the dark version for the dark page (his black strokes in a warm cream, the gold
// untouched). The files are cut and scaled from his master by scripts/make_brand.py into public/brand, WebP with a PNG twin, 1x 2x 3x.
//
// The header logo is the FULL logo (the eye, the swooshes and the script name "SnapEyes") at every width (the owner, 2026-10-23: the full
// logo on phones too, like on a computer; until then a phone had the eye alone beside SNAPEYES set in Cinzel). It is the 56 px file set
// (151 x 56 at 1x, sharp at 2x and 3x), shown 56 px tall from 375 px and a little smaller on the narrowest phones (the caller's CSS), so it
// never meets the language switch or the menu button. The picture's alt is the one name of the link ("SnapEyes"): the link has no
// aria-label and no text of its own, so a screen reader says the name once.
// Every <source> carries its own width and height, so the box is known before the file arrives (no layout shift).
// The full logo alone (the footer, the 404 page) is BrandFull: 96 px tall, lazy where it is below the fold.

/** The sizes at 1x (scripts/make_brand.py prints them; the PNG and WebP files are made at exactly these sizes). */
const BRAND = {
  full56: { w: 151, h: 56 },
  full96: { w: 259, h: 96 },
} as const;

const set = (name: string, ext: 'webp' | 'png') => `/brand/${name}.${ext} 1x, /brand/${name}@2x.${ext} 2x, /brand/${name}@3x.${ext} 3x`;

/** The header logo: the full logo at every width. `imgClass` sizes the <img> (its height; the width follows the source's ratio). */
export function BrandPicture({ imgClass, className }: { imgClass?: string; className?: string }) {
  const f = BRAND.full56;
  return (
    <picture className={className}>
      <source type="image/webp" srcSet={set('logo-dark-h56', 'webp')} width={f.w} height={f.h} />
      <img className={imgClass} src="/brand/logo-dark-h56.png" srcSet={set('logo-dark-h56', 'png')} width={f.w} height={f.h} alt="SnapEyes" decoding="async" />
    </picture>
  );
}

/** The full logo at 96 px (the footer). Lazy by default: it is below the fold. */
export function BrandFull({ lazy = true, imgClass }: { lazy?: boolean; imgClass?: string }) {
  const f = BRAND.full96;
  return (
    <picture>
      <source type="image/webp" srcSet={set('logo-dark-h96', 'webp')} width={f.w} height={f.h} />
      <img className={imgClass} src="/brand/logo-dark-h96.png" srcSet={set('logo-dark-h96', 'png')} width={f.w} height={f.h} alt="SnapEyes"
        loading={lazy ? 'lazy' : undefined} decoding="async" />
    </picture>
  );
}
