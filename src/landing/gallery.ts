// The style gallery's data and rules, without React: which tiles a group has, which picture is a tile in an eye colour, which
// tiles have a wall view, which carry the "Example photo" label. The pictures come from the asset manifest (./assets), the structure
// of the gallery from ./assets.data (generated with the pictures), the words from the copy; no text and no price is written here.
// (The release gate, which tile the order flow can make today, is not a page matter: it is checked at build time by
// scripts/check_landing_assets.mjs from ENGINE_STYLE in ./assets.data.)
import { asset, type AssetFamily, type PictureAsset } from './assets';
import { GALLERY, type EyeId, type GalleryGroup, type GalleryTile } from './assets.data';
import type { LandingCopy } from './copy/types';

export type { EyeId, GalleryGroup, GalleryTile };

/** The groups in the order of the tabs ("Just you", "Two of you", "Family"; there is no animals group). */
export const GROUPS: readonly GalleryGroup[] = GALLERY.groups;

/** The eye colours of the dots, in the order shown. The example photos are not customers (styles.eyeNote.other). */
export const EYES = GALLERY.eyes;

/** The page opens on "Just you" in Mantas's own eye. */
export const DEFAULT_GROUP: GalleryGroup = 'one';
export const DEFAULT_EYE: EyeId = 'own';

export function tilesOf(group: GalleryGroup): readonly GalleryTile[] {
  return GALLERY[group];
}

/** Only the single-eye styles are shown in other eye colours; the pairs and the families are fixed artworks. */
export function hasEyeSwitch(group: GalleryGroup): boolean {
  return group === 'one';
}

/** The pairs and the families are wide (3:2) tiles, one column on a phone. */
export function isWide(group: GalleryGroup): boolean {
  return group === 'two' || group === 'family';
}

/** What a tile's picture says about its width, for the srcset: the grid is 3 columns of 360 px from 960 px, 2 from 640 px, a
 *  rail of 72 percent (86 percent for the wide tiles) below. */
export function tileSizes(wide: boolean): string {
  return wide ? '(min-width: 960px) 360px, (min-width: 640px) 46vw, 86vw' : '(min-width: 960px) 360px, (min-width: 640px) 31vw, 72vw';
}

/** The key of a tile in the page and in the wall toggles: the group and the tile's id (a tile keeps its key when the eye
 *  colour changes, so nothing is remounted and a focused button stays focused). */
export function tileKey(group: GalleryGroup, tile: GalleryTile): string {
  return group + tile.id;
}

/** The id of a tile in the copy (styles.items.<id>). */
export type TileCopyId = keyof LandingCopy['styles']['items'];

/** The name and description of a tile, from the copy. */
export function tileCopy(c: LandingCopy, tile: GalleryTile): { n: string; d: string } {
  return c.styles.items[tile.id as TileCopyId];
}

/** The flat artwork of a tile: a single-eye style in the chosen eye colour (two widths), or the fixed pair or family artwork.
 *  The wide ones are 900 x 600, the others 900 x 900, so width and height reserve the right space. */
export function artPicture(tile: GalleryTile, eye: EyeId): PictureAsset {
  const name = tile.design ? `art/${tile.design}_${eye}` : `art/${tile.file}`;
  return asset(name as AssetFamily, { pick: 900 });
}

/** The tile on a wall (an AI visualisation), or null when it has none. Mantas's own eye has wall pictures for two styles; the
 *  other eye colours have none (an example photo is never put on a wall); a pair has one fixed scene. The widest file is the
 *  src, the srcset offers every width (the picture is not fetched before the visitor asks for the wall: no src until then). */
export function wallPicture(group: GalleryGroup, tile: GalleryTile, eye: EyeId): PictureAsset | null {
  const w = hasEyeSwitch(group) ? (eye === 'own' ? tile.wallOwn : undefined) : tile.wall;
  return w ? asset(w.base, { pick: Number.MAX_SAFE_INTEGER }) : null;
}

/** The tile shows another person's eye and says so in the picture ("Example photo"): an eye colour other than Mantas's own, or
 *  a pair or family that mixes his eye with example photos. */
export function hasPhotoChip(group: GalleryGroup, tile: GalleryTile, eye: EyeId): boolean {
  return hasEyeSwitch(group) ? eye !== 'own' : tile.src === 'mixed';
}

/** Whose eyes a tile shows, for the line under it (styles.own, styles.licensed, styles.mixed). */
export type Provenance = 'own' | 'licensed' | 'mixed';
export function provenance(tile: GalleryTile, eye: EyeId): Provenance {
  if (tile.src === 'mixed') return 'mixed';
  return eye === 'own' ? 'own' : 'licensed';
}
