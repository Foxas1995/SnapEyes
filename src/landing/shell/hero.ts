// What the first screen shows and how it asks for its picture: constants and small pure functions shared by the static shell
// (./render.tsx) and the live first screen (./parts.tsx). Kept out of parts.tsx, which holds components only.
import { asset } from '../assets';

/** What the hero picture says about its width (the prototype's rule: a 500 px column from 960 px, else the screen minus the gutters). */
export const HERO_SIZES = '(min-width: 960px) 500px, calc(100vw - 32px)';
/** The hero picture: the lounge with the acrylic print, offered at 600, 900 and 1200 px only (the LCP budget), src 900. */
export const heroPicture = () => asset('m/lounge_acrylic__eye__tight', { pick: 900, max: 1200 });
/** The disc over the picture's corner: the owner's eye cut at the pupil, phone photo left, restored iris right. */
export const heroDisc = () => asset('reveal/disc_own_420');

/** The header's navigation, in the order of the page's sections (copy nav.*). */
export const NAV_KEYS = ['reveal', 'wall', 'styles', 'how', 'pricing', 'faq'] as const;
