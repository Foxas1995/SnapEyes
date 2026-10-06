// Types of ./check_landing_assets.mjs for vite.config.ts (tsconfig.node.json checks that file with Node's module rules).
export const LANDING_DIR: string;
/** src/landing/assets.ts, src/landing/assets.data.ts and src/landing/tileStyle.ts as the build loaded them (only what the check reads). */
export interface LandingAssetsModule { ASSET_HASH: Record<string, readonly [string, number, number, number]> }
export interface LandingGallery { groups: readonly string[]; [group: string]: unknown }
export interface LandingAssetsData { GALLERY: LandingGallery }
export interface LandingTiles { TILE_STYLE: Record<string, { id: string; eyes: number }> }
/** The release gate's table: the tiles of the gallery by the registry's ceiling for their style and eyes (the ones that are only planned say Soon like the others), and the tiles of something that does not exist. */
export interface ReleaseGate { total: number; live: string[]; preview: string[]; lab: string[]; planned: string[]; blocked: { tile: string; reason: string }[] }
/** One state of the run-time catalogue the gate renders the page for: what GET /api/checkout answered (null: the server could not be read). */
export interface GateInput { name: string; answer: unknown }
/** What src/landing/shell/gate.tsx renderGate gives back (only what the gate reads). */
export interface RenderedGate { scenarios: { name: string; open: boolean; lines: Record<string, 'soon' | 'more' | null>; langs: Record<string, { soon: string; tiles: { id: string; group: string; html: string }[]; table: string; hero: string }> }[]; errors?: string[]; pictures: string[] }
export function releaseGate(styles: Record<string, unknown>, tileStyle: Record<string, unknown>, gallery: LandingGallery): ReleaseGate;
export function promiseGate(rendered: RenderedGate, inputs: GateInput[], styles: Record<string, unknown>, tileStyle: Record<string, unknown>, gallery: LandingGallery): { promises: string[]; underSells: string[]; pictures: string[] };
export function gateInputs(root: string): GateInput[];
export function renderLanding(load: (path: string) => Promise<any>, root: string): Promise<RenderedGate>;
export function gateSummary(gate: ReleaseGate): string;
export function gateIsStrict(env: Record<string, string | undefined>): boolean;
export function webpSize(buf: Uint8Array): { w: number; h: number } | null;
export function checkLandingAssets(root: string, assets: LandingAssetsModule, data: LandingAssetsData, tiles: LandingTiles, rendered?: RenderedGate): { problems: string[]; notices: string[]; gate: ReleaseGate | null };
