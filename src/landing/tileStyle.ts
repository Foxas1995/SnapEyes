// What each tile of the style gallery stands for in the engine: the registry style (api/_lib/styles_registry.py) and the number of eyes the
// tile shows. The page never decides by itself that a tile can be bought: a tile is "for sale now" only when the run-time catalogue
// (src/shared/catalogue.ts liveFor, what GET /api/checkout says at the owner's switch) lists this style as live for this count of eyes;
// every other tile is shown as Soon and carries no price, whatever its picture says (the picture is an example, the gate is the registry).
//
// The tile names of the landing's copy (copy/<lang>.json styles.items.<id>.n) are the landing's words; the registry's names are the engine's.
// Where they differ the table below says which is which:
//   Infinity, Infinity two colours   -> Collision Infinity (two eyes)
//   Infinity Universe                -> Universe, the pair (two eyes, held in the laboratory)
//   Kiss                             -> Kiss Collision
//   Trio, Family of four, five, six  -> Family Colours at three, four, five and six eyes (the Trio is its three-eye layout)
//   Family Universe                  -> Universe, the family
// scripts/check_styles.mjs (item 15) keeps this table equal to the gallery: every tile has a row, every row names a style of the registry that takes
// this many eyes, and the price class of a one-eye tile is the registry's.
import type { GalleryTile } from './gallery';

export interface TileStyle {
  /** The registry id of the style. */
  id: string;
  /** The number of eyes the tile shows. */
  eyes: number;
}

export const TILE_STYLE: Readonly<Record<string, TileStyle>> = {
  radiance: { id: 'solo.radiance', eyes: 1 },
  powder: { id: 'solo.powder', eyes: 1 },
  universe: { id: 'solo.universe', eyes: 1 },
  gold: { id: 'solo.gold', eyes: 1 },
  splash: { id: 'solo.splash', eyes: 1 },
  clean: { id: 'solo.clean', eyes: 1 },
  duo_infinity: { id: 'duo.collision_infinity', eyes: 2 },
  duo_infinity_bb: { id: 'duo.collision_infinity', eyes: 2 },
  duo_infinity_uni: { id: 'duo.universe', eyes: 2 },
  duo_kiss: { id: 'duo.kiss_collision', eyes: 2 },
  duo_clean: { id: 'duo.clean', eyes: 2 },
  fam_trio: { id: 'grp.collision', eyes: 3 },
  fam_4: { id: 'grp.collision', eyes: 4 },
  fam_5: { id: 'grp.collision', eyes: 5 },
  fam_6: { id: 'grp.collision', eyes: 6 },
  fam_6_uni: { id: 'grp.universe', eyes: 6 },
};

/** The style and the count of eyes of a tile, or null for a tile this table does not know (the build check refuses that: a tile without a row never carries a price). */
export function tileStyle(tile: GalleryTile): TileStyle | null {
  return TILE_STYLE[tile.id] ?? null;
}
