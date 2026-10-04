// The hero's picture (prototype: .hero-fig): the lounge with the acrylic print in a 4:5 frame sized to the viewport, the label
// INSIDE the frame (top left: "AI visualisation" and "You receive the digital file. Printing is not included."), the disc over
// its corner (Mantas's own eye cut through the pupil, phone photo left, restored iris right) and the caption under it.
// A PURE component (props in, markup out, no hook and no window): it is rendered to static HTML at build time for the
// prerendered first screen and live by ./Hero.tsx, and it is the LCP element of the page.
//
// The markup is kept plain so motion can be added later: the picture, the glint (an empty span positioned over the print, nothing
// plays it yet) and the disc are separate elements (.lp-glint, #heroDisc).
// The picture's address, srcset and sizes come from src/landing/shell/hero.ts, the one place that also writes the <link rel=preload>
// in the head, so the preload and the image can never ask for different files.
import type { LandingCopy } from './copy/types';
import { HERO_SIZES, heroDisc, heroPicture } from './shell/hero';

export function HeroScene({ hero }: { hero: LandingCopy['hero'] }) {
  const pic = heroPicture();
  const disc = heroDisc();
  return (
    <figure className="lp-hero-fig" aria-labelledby="heroCap">
      <div className="lp-hero-stage">
        <div className="lp-hero-frame">
          <img id="heroImg" src={pic.src} srcSet={pic.srcset} sizes={HERO_SIZES} width={pic.w} height={pic.h} fetchPriority="high" decoding="async" alt={hero.imageAlt} />
          <span className="lp-glint" aria-hidden="true" />
          <div className="lp-frame-chip" data-chip="vis">
            <b>{hero.chipTitle}</b>
            <span>{hero.chipBody}</span>
          </div>
        </div>
        <a className="lp-disc" href="#reveal" id="heroDisc" aria-label={hero.discLink}>
          <img src={disc.src} width={disc.w} height={disc.h} loading="lazy" fetchPriority="low" decoding="async" alt={hero.discAlt} />
          <span className="lp-disc-label" aria-hidden="true">{hero.discLabel}</span>
        </a>
      </div>
      <figcaption className="lp-hero-cap" id="heroCap">{hero.caption}</figcaption>
    </figure>
  );
}
