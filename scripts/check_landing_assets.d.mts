// Types of ./check_landing_assets.mjs for vite.config.ts (tsconfig.node.json checks that file with Node's module rules).
export const LANDING_DIR: string;
/** src/landing/assets.ts, src/landing/assets.data.ts and src/landing/tileStyle.ts as the build loaded them (only what the check reads). */
export interface LandingAssetsModule { ASSET_HASH: Record<string, readonly [string, number, number, number]> }
export interface LandingGallery { groups: readonly string[]; [group: string]: unknown }
export interface LandingAssetsData { GALLERY: LandingGallery }
export interface LandingTiles { TILE_STYLE: Record<string, { id: string; eyes: number }> }
/** The release gate's table: the tiles of the gallery by the registry's ceiling for their style and eyes, and the tiles the engine could never make. */
export interface ReleaseGate { total: number; live: string[]; preview: string[]; lab: string[]; blocked: { tile: string; reason: string }[] }
export function releaseGate(styles: Record<string, unknown>, tileStyle: Record<string, unknown>, gallery: LandingGallery): ReleaseGate;
export function gateSummary(gate: ReleaseGate): string;
export function gateIsStrict(env: Record<string, string | undefined>): boolean;
export function webpSize(buf: Uint8Array): { w: number; h: number } | null;
export function checkLandingAssets(root: string, assets: LandingAssetsModule, data: LandingAssetsData, tiles: LandingTiles): { problems: string[]; notices: string[]; gate: ReleaseGate | null };
