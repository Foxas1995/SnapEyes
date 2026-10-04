// The wall chapter's data and rules, without React: which picture is the stage for a material and an artwork, which
// caption goes with it, where the glint sits, and the warm-up of a picture on intent. The pictures themselves (families of
// files, their hashed addresses) come from the asset manifest; the words come from the copy, never from here.
import { asset, type AssetFamily, type PictureAsset } from './assets';
import { STAGE, type Material, type StageScene, type WallArt } from './assets.data';
import type { Lang } from '../shared/lang';

export type { Material, WallArt };

/** The materials in the order of the tab list (the prototype's order). */
export const MATERIALS: readonly Material[] = ['acrylic', 'metal', 'canvas', 'framed', 'block', 'phone'];

/** The artworks in the order of the chips. */
export const ARTS: readonly WallArt[] = ['eye', 'universe', 'family4', 'collision'];

/** The wall opens on aluminium in the home office with the Radiance artwork, not on the hero picture. */
export const DEFAULT_MATERIAL: Material = 'metal';
export const DEFAULT_ART: WallArt = 'eye';

/** What the stage picture says about its width (the frame is 540 px at most on a desktop, the screen less 32 px on a phone). */
export const STAGE_SIZES = '(min-width: 960px) 540px, calc(100vw - 32px)';

/** The materials whose caption may name a size ("about 50 cm"): only the wall materials have one in the copy. */
export type SizedMaterial = Exclude<Material, 'block' | 'phone'>;

export function isSized(mat: Material): mat is SizedMaterial {
  return mat !== 'block' && mat !== 'phone';
}

/** Is there a picture of this material with this artwork? (An acrylic block has no "two of you".) */
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
  /** The drawn size was estimated at 40 to 55 cm, so the caption may say "about 50 cm" (the copy's captionsSize). */
  sizeOk: boolean;
}

/** The picture of a material with an artwork; the phone scene with the Radiance artwork has a German version (its text is in
 *  the picture). Null if the material has none for that artwork. */
export function stagePicture(mat: Material, art: WallArt, lang: Lang): StagePicture | null {
  const s: StageScene | undefined = STAGE[mat][art];
  if (!s) return null;
  const family = mat === 'phone' && art === 'eye' && lang === 'de' && s.de ? s.de : s.base;
  // the widest file is the src, every width is in the srcset (the browser picks by the sizes above)
  return { family, key: family, asset: asset(family, { pick: 100000 }), sizeOk: s.sizeOk };
}

/** The glint of a polished surface: left, top, width, height of the sweep in percent of the stage. Acrylic only. The boxes are the
 *  face of the print in the living room plates (the pictures' rooms_slots.json): the square plate for one eye, the 3:2 plate of the
 *  same room for the pair and the family. */
export type GlintBox = readonly [number, number, number, number];
const GLINT: Readonly<Record<'single' | 'wide', GlintBox>> = { single: [28.08, 23.62, 43.85, 35.14], wide: [17.02, 22.75, 65.97, 34.5] };

export function glintFor(mat: Material, art: WallArt): GlintBox | null {
  if (mat !== 'acrylic') return null;
  return art === 'collision' || art === 'family4' ? GLINT.wide : GLINT.single;
}

// One material is warmed on hover, focus or touch (the visitor's intent), not all six on idle: no speculative 400 KB. A
// module level set, because the pictures are the browser's cache, which outlives any one mount of the section.
const warmed = new Set<string>();

/** Start loading the stage picture of a material (with the artwork on the stage, or Radiance where the material lacks it). */
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
