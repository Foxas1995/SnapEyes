// LAB (2026-10-22, not part of any page the build ships): the artworks of the two centrepiece prototypes, the Iris globe and the Iris ring.
// Every picture is one the site already publishes (public/assets/landing/art and public/assets/atelier); scripts/lab/sphere/make_thumbs.py cut the
// round thumbnails in ./img (160 and 240 px for the discs, 480 px for the one in front). The names are the registry's (api/_lib/styles_registry.py):
// in the landing they would come from src/landing/tileState.ts tileName and src/shared/styles.ts styleName instead of this table.
// The owner's sample rule (2026-10-20) decided the set: no eyelid skin or lashes over an iris, no very large pupil, and in a pair or a family no pupil
// much larger than the others (the grey example eye and the five and six eye families with the red eye are left out).

/** Whose eyes a picture shows (the small honest label): our own eye, an example photo, or both. Never a customer. */
export type Prov = 'own' | 'licensed' | 'mixed';

export interface Art {
  id: string;
  /** the registry's name of the style */
  name: string;
  prov: Prov;
}

const own = (id: string, name: string): Art => ({ id, name, prov: 'own' });
const lic = (id: string, name: string): Art => ({ id, name, prov: 'licensed' });
const mix = (id: string, name: string): Art => ({ id, name, prov: 'mixed' });

const ALL: readonly Art[] = [
  own('halo_own', 'Halo'), own('sparks_own', 'Sparks'), own('aurora_own', 'Aurora'), own('nebula_own', 'Nebula'), own('supernova_own', 'Supernova'),
  own('radiance_own', 'Radiance'), lic('radiance_yg', 'Radiance'), lic('radiance_br', 'Radiance'),
  own('powder_own', 'Powder Burst'), lic('powder_yg', 'Powder Burst'), lic('powder_br', 'Powder Burst'),
  own('universe_own', 'Universe'), lic('universe_yg', 'Universe'),
  own('splash_own', 'Splash'), lic('splash_yg', 'Splash'), lic('splash_br', 'Splash'),
  own('clean_own', 'Clean Iris'), lic('clean_yg', 'Clean Iris'),
  own('gold_own', 'Celestial Gold'),
  mix('duo_infinity_by', 'Collision Infinity'), mix('duo_clean_by', 'Clean Infinity'), mix('kiss_collision', 'Kiss Collision'),
  mix('duo_thread_by', 'Clean Duo'), mix('duo_radiance_bd', 'Radiance Duo'), mix('nebula_duo', 'Nebula Duo'), mix('supernova_duo', 'Supernova Duo'),
  mix('fam_trio', 'Family Colours'), mix('fam_orbit_4', 'Family Orbit'), mix('fam_circle_4', 'Light Circle'), mix('fam_radiance_4', 'Radiance Family'),
  mix('nebula_family', 'Nebula Family'), mix('supernova_family', 'Supernova Family'),
];

export const ART: Readonly<Record<string, Art>> = Object.fromEntries(ALL.map((a) => [a.id, a]));

const files = import.meta.glob<string>('./img/*.webp', { eager: true, query: '?url', import: 'default' });

/** The address of a thumbnail: 160 or 240 px for a disc, 480 px for the one in front. */
export function pic(id: string, px: 160 | 240 | 480): string {
  const url = files[`./img/${id}-${px}.webp`];
  if (!url) throw new Error(`lab sphere: no picture ${id}-${px}`);
  return url;
}

/** The srcset of a disc (the browser picks 160 or 240 px for the disc's width and the screen's pixel ratio). */
export const discSet = (id: string): string => `${pic(id, 160)} 160w, ${pic(id, 240)} 240w`;

/** The globe: 32 discs on five latitude rows, written from the front (longitude 0) round to the right. The first one faces the visitor at the start:
 *  Halo, with Aurora and Sparks beside it, Radiance and Nebula above, Supernova and the Trio below. Celestial Gold sits in the top cap. */
export const GLOBE_ROWS: readonly { lat: number; offset: number; ids: readonly string[] }[] = [
  { lat: 0, offset: 0, ids: ['halo_own', 'sparks_own', 'fam_orbit_4', 'powder_yg', 'nebula_duo', 'universe_own', 'splash_br', 'duo_thread_by', 'radiance_yg', 'aurora_own'] },
  { lat: 36, offset: 22.5, ids: ['nebula_own', 'splash_yg', 'clean_own', 'fam_radiance_4', 'powder_br', 'supernova_duo', 'universe_yg', 'radiance_own'] },
  { lat: -36, offset: 22.5, ids: ['fam_trio', 'powder_own', 'duo_infinity_by', 'clean_yg', 'supernova_family', 'splash_own', 'kiss_collision', 'supernova_own'] },
  { lat: 72, offset: 0, ids: ['duo_clean_by', 'gold_own', 'nebula_family'] },
  { lat: -72, offset: 60, ids: ['radiance_br', 'duo_radiance_bd', 'fam_circle_4'] },
];

/** The ring: the same 32 artworks in the order they come to the front, a single, a pair or a family in turn. */
export const RING_ORDER: readonly string[] = [
  'halo_own', 'nebula_duo', 'sparks_own', 'fam_orbit_4', 'aurora_own', 'supernova_duo', 'radiance_own', 'fam_circle_4', 'splash_yg', 'duo_thread_by',
  'powder_yg', 'nebula_family', 'universe_own', 'kiss_collision', 'clean_own', 'fam_radiance_4', 'supernova_own', 'duo_infinity_by', 'radiance_yg',
  'supernova_family', 'splash_br', 'duo_radiance_bd', 'powder_br', 'fam_trio', 'universe_yg', 'duo_clean_by', 'nebula_own', 'clean_yg', 'splash_own',
  'powder_own', 'radiance_br', 'gold_own',
];
