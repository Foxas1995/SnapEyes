// What a tile of the style gallery IS, in the registry's terms and the run-time catalogue's: pure functions, no React, so the page, the build's gate
// (src/landing/shell/gate.tsx, scripts/check_landing_assets.mjs) and the node tests read ONE rule.
//
//   * the name a tile prints is the registry's name of the style it stands for (api/_lib/styles_registry.py, through src/shared/styles.ts styleName): the
//     copy files hold no tile name any more, so there is no second list of names to drift (a tile of a style the registry does not have prints nothing, and
//     the build's gate refuses it);
//   * a tile is "for sale" only when the run-time catalogue lists its style live for the number of eyes the tile shows (liveFor) AND ordering is open
//     (the catalogue handed in is the SALE catalogue, src/shared/catalogue.ts saleCatalogue: empty while ordering is closed); every other tile is Soon:
//     a style at preview, in the laboratory, only planned, or one that no catalogue lists, and it never carries a price;
//   * the group line ("More styles soon." / "Free preview now. Ordering for this group opens soon.") and the names of the price rows follow from the
//     same states, so the intros, the rows and the tiles can never disagree about what can be bought.
// Which style a tile stands for is src/landing/tileStyle.ts (scripts/check_styles.mjs item 15 keeps it equal to the gallery and the registry).
import { liveFor, type RunCatalogue } from '../shared/catalogue';
import { isStyle, styleName } from '../shared/styles';
import { TILE_STYLE, type TileStyle } from './tileStyle';

const has = (o: object, k: string): boolean => Object.prototype.hasOwnProperty.call(o, k);

/** 'sale': can be bought now. 'soon': everything else (the tile says Soon and prints no price). */
export type TileSale = 'sale' | 'soon';

export interface TileState {
  /** The registry id of the style the tile stands for, or null for a tile the table does not know or that names a style the registry does not have. */
  style: string | null;
  /** The number of eyes the tile shows (0 without a row). */
  eyes: number;
  /** The registry's name of the style ('' when there is none: such a tile is refused by the build). */
  name: string;
  sale: TileSale;
}

/** The row of the tile table for a tile id, or null (a hostile id such as "constructor" has none). */
export function tileRow(id: string): TileStyle | null {
  return has(TILE_STYLE, id) ? TILE_STYLE[id] : null;
}

/** The name a tile prints: the registry's name of its style, or '' when the tile names no style of the registry. */
export function tileName(id: string): string {
  const row = tileRow(id);
  return row && isStyle(row.id) ? styleName(row.id) : '';
}

/** The state of one tile for a sale catalogue (what can be bought now). */
export function tileState(id: string, sale: RunCatalogue): TileState {
  const row = tileRow(id);
  const style = row && isStyle(row.id) ? row.id : null;
  return {
    style,
    eyes: row ? row.eyes : 0,
    name: style ? styleName(style) : '',
    sale: style !== null && liveFor(sale, style, row ? row.eyes : 0) ? 'sale' : 'soon',
  };
}

/** The tiles of a list (a group, or the one-eye art tiles) that can be bought now: how many, how many tiles there are, and the registry names of the ones
 *  for sale in tile order, each name once (two tiles of one style, such as the two Infinity pairs, name it once). */
export function saleTiles(ids: readonly string[], sale: RunCatalogue): { names: string[]; sale: number; total: number } {
  const names: string[] = [];
  let n = 0;
  for (const id of ids) {
    const s = tileState(id, sale);
    if (s.sale !== 'sale') continue;
    n += 1;
    if (!names.includes(s.name)) names.push(s.name);
  }
  return { names, sale: n, total: ids.length };
}

/** The line a group adds under its intro: only while ordering is open (the page's notice says it while it is closed). Nothing in the group can be
 *  bought: 'soon' ("Free preview now. Ordering for this group opens soon."); some can: 'more' ("More styles soon."); all can: null. */
export function groupLine(ids: readonly string[], sale: RunCatalogue): 'soon' | 'more' | null {
  if (sale.max < 1) return null;
  const { sale: n, total } = saleTiles(ids, sale);
  return n === 0 ? 'soon' : n < total ? 'more' : null;
}
