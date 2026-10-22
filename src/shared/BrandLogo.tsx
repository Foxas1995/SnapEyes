// The SnapEyes logo: the owner's own design (2026-10-22), the dark version for the dark page (his black strokes in a warm cream, the gold
// untouched). The files are cut and scaled from his master by scripts/make_brand.py into public/brand, WebP with a PNG twin, 1x 2x 3x.
//
// Two pictures, one <picture> (art direction, so only one is fetched):
//   - from 768 px: the FULL logo, 56 px tall (the script name is part of it);
//   - under 768 px: the eye with a short swoosh, beside the name SNAPEYES set in the site's Cinzel (the caller prints it), because the
//     script name of the full logo is too small to read in a phone's header.
// Every <source> carries its own width and height, so the box is known before the file arrives (no layout shift), whichever is chosen.
// The full logo alone (the footer, the 404 page) is BrandFull: 96 px tall, lazy where it is below the fold.

/** The sizes at 1x (scripts/make_brand.py prints them; the PNG and WebP files are made at exactly these sizes). */
const BRAND = {
  full56: { w: 151, h: 56 },
  full96: { w: 259, h: 96 },
  eye34: { w: 58, h: 34 },
} as const;

const set = (name: string, ext: 'webp' | 'png') => `/brand/${name}.${ext} 1x, /brand/${name}@2x.${ext} 2x, /brand/${name}@3x.${ext} 3x`;

/** The header logo: the full logo from 768 px, the eye under it. `imgClass` sizes the <img> (its height; the width follows the source's ratio). */
export function BrandPicture({ imgClass, className }: { imgClass?: string; className?: string }) {
  const f = BRAND.full56;
  const e = BRAND.eye34;
  return (
    <picture className={className}>
      <source media="(min-width: 768px)" type="image/webp" srcSet={set('logo-dark-h56', 'webp')} width={f.w} height={f.h} />
      <source media="(min-width: 768px)" type="image/png" srcSet={set('logo-dark-h56', 'png')} width={f.w} height={f.h} />
      <source type="image/webp" srcSet={set('eye-dark-h34', 'webp')} width={e.w} height={e.h} />
      <img className={imgClass} src="/brand/eye-dark-h34.png" srcSet={set('eye-dark-h34', 'png')} width={e.w} height={e.h} alt="SnapEyes" decoding="async" />
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
