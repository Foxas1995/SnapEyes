// What each tile of the style gallery stands for in the engine: the registry style (api/_lib/styles_registry.py) and the number of eyes the
// tile shows. This table is the ONLY link between the gallery's pictures (which have their own ids) and the registry: the name a tile prints, whether it
// can be bought and its price class all come from the registry through it (src/landing/tileState.ts), and the copy files hold no tile name.
// The page never decides by itself that a tile can be bought: a tile is "for sale now" only when the run-time catalogue (src/shared/catalogue.ts liveFor,
// what GET /api/checkout says at the owner's switch) lists this style as live for this count of eyes and ordering is open; every other tile is shown as
// Soon and carries no price, whatever its picture says (the picture is an example, the stage is the registry's).
//
// Where the picture's own id and the registry's name differ the table says which tile is which style (the registry's name is what the page prints):
//   duo_infinity, duo_infinity_bb    -> Collision Infinity (two eyes; the second shows the pair of two eye colours)
//   duo_infinity_uni                 -> Universe, the pair (two eyes, held in the laboratory)
//   duo_kiss                         -> Kiss Collision
//   duo_clean                        -> Clean Infinity
//   fam_trio, fam_4, fam_5, fam_6    -> Family Colours at three, four, five and six eyes (the Trio is its three-eye layout)
//   fam_6_uni                        -> Universe, the family (held in the laboratory)
// scripts/check_styles.mjs (item 15) keeps this table equal to the gallery: every tile has a row, every row names a style of the registry that takes
// this many eyes, and the price class of a one-eye tile is the registry's; scripts/check_landing_assets.mjs (the gate) renders every tile and refuses
// a name that is not the registry's and a tile that would promise what the catalogue does not sell.

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
