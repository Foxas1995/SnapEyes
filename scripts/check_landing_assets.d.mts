// Types of ./check_landing_assets.mjs for vite.config.ts (tsconfig.node.json checks that file with Node's module rules).
export const LANDING_DIR: string;
/** src/landing/assets.ts and src/landing/assets.data.ts as the build loaded them (only what the check reads). */
export interface LandingAssetsModule { ASSET_HASH: Record<string, readonly [string, number, number, number]> }
export interface LandingAssetsData {
  GALLERY: { groups: readonly string[] } & Record<string, unknown>;
  ENGINE_STYLE: Record<string, string>;
}
export function webpSize(buf: Uint8Array): { w: number; h: number } | null;
export function checkLandingAssets(root: string, assets: LandingAssetsModule, data: LandingAssetsData): { problems: string[]; notices: string[] };
