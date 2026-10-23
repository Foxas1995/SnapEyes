// What each round artwork of the hero's globe (src/landing/globe/Globe.tsx) shows, in the registry's terms: the style (api/_lib/styles_registry.py),
// the number of eyes, and whose eyes they are. This table is the globe's only link to the registry: the name an opened artwork prints is the registry's
// name of its style (src/shared/styles.ts styleName) and whether it can be bought now comes from the run-time catalogue (src/landing/tileState.ts), so
// no name and no price is written here. scripts/check_styles.mjs (item 17) keeps the table equal to the globe's pictures (scripts/landing_assets.json
// "globe", made by scripts/make_globe_assets.py) and to the registry: every style exists, is not retired, takes that many eyes and can be previewed.
// Every picture is an existing artwork of the site: our own eye, the licensed example photos, or both; never a customer (the owner's sample rule of
// 2026-10-20 chose them: no eyelid or lashes over an iris, no very large pupil, no pair or family with one much larger pupil).

/** Whose eyes a picture shows (the honest label of an opened artwork): our own eye, an example photo, or both. Never a customer. */
export type GlobeProv = 'own' | 'licensed' | 'mixed';

export interface GlobeArt {
  /** the picture's name (public/assets/landing/globe/<id>_<width>.<hash>.webp) */
  id: string;
  /** the registry id of the style it shows */
  style: string;
  eyes: number;
  prov: GlobeProv;
}

const one = (id: string, style: string, prov: 'own' | 'licensed'): GlobeArt => ({ id, style, eyes: 1, prov });
const many = (id: string, style: string, eyes: number): GlobeArt => ({ id, style, eyes, prov: 'mixed' });

export const GLOBE_ART: readonly GlobeArt[] = [
  one('halo_own', 'solo.halo', 'own'), one('sparks_own', 'solo.sparks', 'own'), one('aurora_own', 'solo.aurora', 'own'),
  one('nebula_own', 'solo.nebula', 'own'), one('supernova_own', 'solo.supernova', 'own'),
  one('radiance_own', 'solo.radiance', 'own'), one('radiance_yg', 'solo.radiance', 'licensed'), one('radiance_br', 'solo.radiance', 'licensed'),
  one('powder_own', 'solo.powder', 'own'), one('powder_yg', 'solo.powder', 'licensed'), one('powder_br', 'solo.powder', 'licensed'),
  one('universe_own', 'solo.universe', 'own'), one('universe_yg', 'solo.universe', 'licensed'),
  one('splash_own', 'solo.splash', 'own'), one('splash_yg', 'solo.splash', 'licensed'), one('splash_br', 'solo.splash', 'licensed'),
  one('clean_own', 'solo.clean', 'own'), one('clean_yg', 'solo.clean', 'licensed'),
  one('gold_own', 'solo.gold', 'own'),
  many('duo_infinity_by', 'duo.collision_infinity', 2), many('duo_clean_by', 'duo.clean', 2), many('duo_kiss_bb', 'duo.kiss_collision', 2),
  many('duo_thread_by', 'duo.clean_duo', 2), many('duo_radiance_bd', 'duo.radiance', 2), many('nebula_duo', 'duo.nebula', 2), many('supernova_duo', 'duo.supernova', 2),
  many('fam_trio', 'grp.collision', 3), many('fam_orbit_4', 'grp.orbit', 4), many('fam_circle_4', 'grp.light_circle', 4), many('fam_radiance_4', 'grp.radiance', 4),
  many('nebula_family', 'grp.nebula', 4), many('supernova_family', 'grp.supernova', 4),
];

/** The globe's five latitude rows, written from the front (longitude 0) round to the right. The first one faces the visitor at the start: Halo, with
 *  Aurora and Sparks beside it, Radiance and Nebula above, Supernova and the Trio below; Celestial Gold sits in the top cap.
 *  The caps are at 70 degrees, not 72 (the owner's review of 2026-10-23): at 72 the three discs round a pole were 31 degrees apart, less than a
 *  disc (33), so they overlapped; at 70 no two of the 32 discs are closer than 34.2 degrees, a gap of at least 1.2 degrees in every orientation. */
export const GLOBE_ROWS: readonly { lat: number; offset: number; ids: readonly string[] }[] = [
  { lat: 0, offset: 0, ids: ['halo_own', 'sparks_own', 'fam_orbit_4', 'powder_yg', 'nebula_duo', 'universe_own', 'splash_br', 'duo_thread_by', 'radiance_yg', 'aurora_own'] },
  { lat: 36, offset: 22.5, ids: ['nebula_own', 'splash_yg', 'clean_own', 'fam_radiance_4', 'powder_br', 'supernova_duo', 'universe_yg', 'radiance_own'] },
  { lat: -36, offset: 22.5, ids: ['fam_trio', 'powder_own', 'duo_infinity_by', 'clean_yg', 'supernova_family', 'splash_own', 'duo_kiss_bb', 'supernova_own'] },
  { lat: 70, offset: 0, ids: ['duo_clean_by', 'gold_own', 'nebula_family'] },
  { lat: -70, offset: 60, ids: ['radiance_br', 'duo_radiance_bd', 'fam_circle_4'] },
];
