// The wall chapter's data and rules, without React: which picture is the stage for a material and an artwork, which
// size its caption names, where the glint sits, and the warm-up of a picture on intent. The pictures themselves (families of
// files, their hashed addresses) come from the asset manifest; the words come from the copy, never from here.
import { asset, type AssetFamily, type PictureAsset } from './assets';
import { STAGE, type Material, type StageScene, type WallArt } from './assets.data';
import type { Lang } from '../shared/lang';

export type { Material, WallArt };

/** The materials in the order of the tab list. The owner's decision of 2026-11-25: exactly what is sold (api/_lib/print_offer.py) and the phone: no framed
 *  print any more, metal is the glossy metal plate that is sold, the poster is new. */
export const MATERIALS: readonly Material[] = ['acrylic', 'metal', 'canvas', 'poster', 'block', 'phone'];

/** The artworks in the order of the chips. The family is the square trio (no 3:2 artwork is shown on a print since 2026-11-25); the pair is shown on the
 *  phone only: its chip is disabled on every print, as the family's is on the poster. */
export const ARTS: readonly WallArt[] = ['eye', 'universe', 'family', 'collision'];

/** The wall opens on glossy metal over the sofa with the one-eye artwork. */
export const DEFAULT_MATERIAL: Material = 'metal';
export const DEFAULT_ART: WallArt = 'eye';

/** What the stage picture says about its width (the frame is 540 px at most on a desktop, the screen less 32 px on a phone). */
export const STAGE_SIZES = '(min-width: 960px) 540px, calc(100vw - 32px)';

/** The size a caption names ("On acrylic glass, 60 cm."): the side of the square print DRAWN in the picture (the stage's cm, a fact of the picture: the pictures
 *  of 2026-11-24/25 were made at sizes that are sold, 60 cm over the sofa, a 50 cm poster, a 20 cm block), never the largest print. Every print is square (the
 *  compare table's note says so), so one number. Written as the copy's facts write a size: a no-break space, and "cm" is the same word in the eight languages. */
export function sceneSize(cm: number): string {
  return `${cm} cm`;
}

/** The materials whose caption may name a size: the prints (the phone shows none). */
export type SizedMaterial = Exclude<Material, 'phone'>;

export function isSized(mat: Material): mat is SizedMaterial {
  return mat !== 'phone';
}

/** Is there a picture of this material with this artwork? (The poster has no family, no print has the pair.) */
export function hasScene(mat: Material, art: WallArt): boolean {
  return !!STAGE[mat][art];
}

/** The artwork to show when the visitor changes the material: the same one if that material has it, else the first. */
export function artFor(mat: Material, art: WallArt): WallArt {
  return hasScene(mat, art) ? art : DEFAULT_ART;
}

export interface StagePicture {
  /** The family of files it is (a srcset of several widths). */
  family: AssetFamily;
  /** Changes when the picture changes: two layers with the same key show the same picture. */
  key: string;
  asset: PictureAsset;
  /** The size of the print drawn in the picture in cm (the copy's captionsSize names it), 0 where the picture shows none. */
  cm: number;
}

/** The picture of a material with an artwork; the phone scene with the one-eye artwork has a German version (its text is in
 *  the picture). Null if the material has none for that artwork. */
export function stagePicture(mat: Material, art: WallArt, lang: Lang): StagePicture | null {
  const s: StageScene | undefined = STAGE[mat][art];
  if (!s) return null;
  const family = mat === 'phone' && art === 'eye' && lang === 'de' && s.de ? s.de : s.base;
  // the widest file is the src, every width is in the srcset (the browser picks by the sizes above)
  return { family, key: family, asset: asset(family, { pick: 100000 }), cm: s.cm };
}

/** The glint of a polished surface: left, top, width, height of the sweep in percent of the stage. The polished prints only, acrylic glass and glossy metal
 *  (2026-11-25: the metal over the sofa is the gloss finish that is sold; canvas and the poster are matt, the block stands on a desk). The box is the face of
 *  the 60 cm print over the sofa, measured on the pictures (pixels 360 to 840 across and 254 to 734 down of 1200 x 1500): every artwork of these two materials is
 *  square and sits in the same place, so there is one box. */
export type GlintBox = readonly [number, number, number, number];
const GLINT: GlintBox = [30.0, 16.93, 40.0, 32.0];

export function glintFor(mat: Material): GlintBox | null {
  return mat === 'acrylic' || mat === 'metal' ? GLINT : null;
}

// One material is warmed on hover, focus or touch (the visitor's intent), not all six on idle: no speculative 400 KB. A
// module level set, because the pictures are the browser's cache, which outlives any one mount of the section.
const warmed = new Set<string>();

/** Start loading the stage picture of a material (with the artwork on the stage, or the one-eye artwork where the material lacks it). */
export function warm(mat: Material, art: WallArt, lang: Lang): void {
  if (typeof Image === 'undefined') return;
  const p = stagePicture(mat, art, lang) ?? stagePicture(mat, DEFAULT_ART, lang);
  if (!p || warmed.has(p.key)) return;
  warmed.add(p.key);
  const img = new Image();
  img.decoding = 'async';
  img.sizes = STAGE_SIZES;
  if (p.asset.srcset) img.srcset = p.asset.srcset;
  img.src = p.asset.src;
}
