// The three example eyes of the Reveal: the words of the copy (reveal.eyes) joined to the pictures of the asset manifest
// (REVEAL in ./assets.data.ts). Pure data, no hook: Reveal.tsx, RevealSlider.tsx and RevealStrip.tsx share the type.
import { asset, type PictureAsset } from './assets';
import { REVEAL } from './assets.data';
import type { LandingCopy } from './copy/types';

/** What the Reveal's frame says about its width (the prototype's rule: a 560 px column from 960 px, else the screen minus the
 *  gutters). The two layers offer 900 and 1200 px, so a dense phone screen gets the larger file. */
export const REVEAL_SIZES = '(min-width: 960px) 560px, calc(100vw - 32px)';

export interface RevealEye {
  id: string;
  /** The pill's words (Grey green eye, Brown eye, Mantas's eye). */
  label: string;
  /** The width of the phone photo in pixels: the number in "Phone photo: {n} px". */
  n: number;
  note: string;
  photoAlt: string;
  irisAlt: string;
  artAlt: string;
  /** The two registered layers of the slider: the same square crop of the same eye, phone photo and restored iris. Both come
   *  with a 900 and a 1200 px file (a srcset). */
  photo: PictureAsset;
  iris: PictureAsset;
  /** The same two layers as single 900 px files, and the Radiance artwork, for the three up strip. */
  stripPhoto: PictureAsset;
  stripIris: PictureAsset;
  art: PictureAsset;
}

interface Pictures {
  photo: PictureAsset;
  iris: PictureAsset;
  stripPhoto: PictureAsset;
  stripIris: PictureAsset;
  art: PictureAsset;
}

const PICTURES = new Map<string, Pictures>(
  REVEAL.eyes.map((e) => [
    e.id,
    {
      photo: asset(e.photo, { pick: 900 }),
      iris: asset(e.iris, { pick: 900 }),
      stripPhoto: asset(e.photo, { max: 900 }),
      stripIris: asset(e.iris, { max: 900 }),
      art: asset(e.art),
    },
  ]),
);

/** The eyes of one language, in the copy's order. An id the manifest does not know is a build mistake, so it throws. */
export function revealEyes(copy: LandingCopy['reveal']): RevealEye[] {
  return copy.eyes.map((e) => {
    const p = PICTURES.get(e.id);
    if (!p) throw new Error(`reveal eye "${e.id}" has no pictures in REVEAL (src/landing/assets.data.ts)`);
    return { id: e.id, label: e.label, n: e.n, note: e.note, photoAlt: e.photoAlt, irisAlt: e.irisAlt, artAlt: e.artAlt, ...p };
  });
}
