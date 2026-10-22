// The hero's centrepiece (2026-10-22, the owner's choice of the prototypes: "the sphere reminds of the eyeball itself"): a globe of round artworks in
// our styles. The wall visualisation and the before/after disc that stood here before live in the wall section and the Reveal.
// A PURE component (props in, markup out, no hook and no window): it is rendered to static HTML at build time for the prerendered first screen and
// live by ./Hero.tsx. The first paint is the POSTER, a still picture of the globe's first view (#heroImg: the LCP element, preloaded with the same
// srcset and sizes by src/landing/shell/render.tsx, and the picture the page's own script waits for, src/landing/shell/scripts.ts loaderScript); the
// stage keeps its box from the first paint, so nothing moves (CLS 0). The live page puts the interactive globe (its own lazy chunk, ./globe/Globe.tsx)
// into the same box once the hero is on screen and the browser is idle (`live`), and the poster steps back when the globe's first pictures are in
// (`liveReady`, the attribute data-live: the two show the same arrangement, so the swap is not seen). The line under the stage is the honest label of
// what the globe shows: our own eye and example photos, never a customer (hero.globeNote).
import type { ReactNode } from 'react';
import type { LandingCopy } from './copy/types';
import { HERO_SIZES, heroPicture } from './shell/hero';

export function HeroScene({ copy, live, liveReady = false }: { copy: LandingCopy; live?: ReactNode; liveReady?: boolean }) {
  const pic = heroPicture();
  return (
    <figure className="lp-hero-fig">
      <div className="lp-globe" id="heroGlobe" data-live={liveReady ? '' : undefined}>
        {/* once the live globe is in, it speaks for itself (a group of labelled buttons): the poster is hidden from assistive technology then */}
        <img id="heroImg" className="lp-globe-poster" src={pic.src} srcSet={pic.srcset} sizes={HERO_SIZES} width={pic.w} height={pic.h} fetchPriority="high" decoding="async" alt={copy.hero.globeAlt} aria-hidden={liveReady || undefined} />
        {live}
      </div>
      <figcaption className="lp-globe-note">{copy.hero.globeNote}</figcaption>
    </figure>
  );
}
