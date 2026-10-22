// How the first screen asks for its picture: constants and small pure functions shared by the static shell (./render.tsx, the
// preload in the head) and the live hero (src/landing/HeroScene.tsx).
import { asset } from '../assets';

/** What the hero picture says about its width: the globe's stage is a column of at most 600 px from 960 px, and the full width of a phone (its
 *  stage reaches the screen's edges; on a short phone it is narrower, so the screen's width is the most it asks for). */
export const HERO_SIZES = '(min-width: 960px) 600px, 100vw';
/** The hero picture: the poster of the globe (its first view, scripts/make_globe_poster.mjs), offered at 600, 900 and 1200 px (the LCP budget of
 *  scripts/check_landing_assets.mjs), src 900. */
export const heroPicture = () => asset('globe/poster', { pick: 900, max: 1200 });
