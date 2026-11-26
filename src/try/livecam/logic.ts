// The live camera inside /try (2026-11-26, the owner: "everything must happen in the page", and can the page's photo be as good as the phone
// camera's?). Hidden behind ?cam=1 until the owner has tried it on his own phones. This file is the pure part (no DOM, no React), so the ts
// tests can hold it: when the camera is on, which zoom we use, how a failure is classed, the anonymous codes the 'photo' beacon and the
// analysis carry, and the plain line the owner reads on the camera view.

/** How the photo reached the page: our own live camera, the phone's camera through the capture input, or the gallery. */
export type How = 'live' | 'native' | 'gallery';
/** How the live camera took a frame: a real still (ImageCapture.takePhoto) or a frame of the video. */
export type LiveMethod = 'still' | 'frame';
/** Why the live camera gave way to the capture input. */
export type LiveFail = 'unsupported' | 'denied' | 'nocamera' | 'timeout' | 'error';
/** The zoom: set on the camera track (it has zoom) or shown and cropped by us (it has not). */
export type ZoomMode = 'track' | 'css';

/** The anonymous capture codes: no device identifier, no camera label, the size only as a class. */
export interface Cap {
  how: How;
  lm?: LiveMethod;
  lres?: string;
  zoom?: ZoomMode;
  torch?: 'yes' | 'no';
  lfail?: LiveFail;
}

export const CAM_KEY = 'snapeyes.cam';
export const ZOOM_WANT = 2;               // the guide's "2x zoom"
export const BURST = 4;                   // frames per tap of the shutter...
export const BURST_GAP_MS = 500;          // ...over about a second and a half
export const FRAME_WAIT_MS = 5000;        // no picture this long after the camera was granted: give way
export const GRANT_WAIT_MS = 30000;       // a permission question nobody answers (or a browser that never answers): give way
export const IDEAL = { width: 3840, height: 2160 };

interface KV { getItem(k: string): string | null; setItem(k: string, v: string): void; removeItem(k: string): void }

/** Is the live camera on for this tab? ?cam=1 turns it on (kept in the tab's sessionStorage), ?cam=0 off; otherwise what the tab kept. */
export function camOn(search: string, store: KV | null): boolean {
  let q: string | null = null;
  try { q = new URLSearchParams(search).get('cam'); } catch { /* no address */ }
  try {
    if (q === '1') { store?.setItem(CAM_KEY, '1'); return true; }
    if (q === '0') { store?.removeItem(CAM_KEY); return false; }
    return store?.getItem(CAM_KEY) === '1';
  } catch {
    return q === '1';
  }
}

/** Can this browser try at all? (Checked at the tap, so the fallback can still open the capture input inside the same gesture.) */
export function liveSupported(nav: { mediaDevices?: { getUserMedia?: unknown } } | undefined, secure: boolean): boolean {
  return !!secure && !!nav?.mediaDevices && typeof nav.mediaDevices.getUserMedia === 'function';
}

/** The zoom we ask for: on the track when it reaches 2x (at most its max), otherwise 2x by CSS and the kept frame cropped alike. */
export function chooseZoom(caps: { zoom?: { min?: number; max?: number } } | null | undefined): { mode: ZoomMode; value: number } {
  const z = caps?.zoom;
  const max = typeof z?.max === 'number' && Number.isFinite(z.max) ? z.max : 0;
  const min = typeof z?.min === 'number' && Number.isFinite(z.min) ? z.min : 1;
  if (max >= ZOOM_WANT) return { mode: 'track', value: Math.max(min, Math.min(ZOOM_WANT, max)) };
  return { mode: 'css', value: ZOOM_WANT };
}

/** The middle part of a w x h picture that a zoom of `factor` shows (the CSS zoom's crop). */
export function centreCrop(w: number, h: number, factor: number): { sx: number; sy: number; sw: number; sh: number } {
  const f = factor > 1 ? factor : 1;
  const sw = Math.round(w / f), sh = Math.round(h / f);
  return { sx: Math.round((w - sw) / 2), sy: Math.round((h - sh) / 2), sw, sh };
}

/** The class of a failure: what getUserMedia or the wait threw. */
export function failClass(e: unknown): LiveFail {
  const name = e && typeof e === 'object' && 'name' in e ? String((e as { name: unknown }).name) : '';
  if (name === 'NotAllowedError' || name === 'PermissionDeniedError' || name === 'SecurityError') return 'denied';
  if (name === 'NotFoundError' || name === 'DevicesNotFoundError' || name === 'OverconstrainedError' || name === 'ConstraintNotSatisfiedError') return 'nocamera';
  if (name === 'TimeoutError') return 'timeout';
  if (name === 'NotSupportedError' || name === 'TypeError') return 'unsupported';
  return 'error';
}

/** The size of a frame as a class of megapixels (never the exact size): mp0 under 1, mp1, mp2, mp5, mp8, mp12 and up. */
export function resClass(w: number, h: number): string {
  const mp = (w > 0 && h > 0 ? w * h : 0) / 1e6;
  if (mp < 1) return 'mp0';
  if (mp < 2) return 'mp1';
  if (mp < 5) return 'mp2';
  if (mp < 8) return 'mp5';
  if (mp < 12) return 'mp8';
  return 'mp12';
}

/** The codes of a burst of the live camera. */
export function liveCap(method: LiveMethod, w: number, h: number, zoom: ZoomMode, torch: boolean): Cap {
  return { how: 'live', lm: method, lres: resClass(w, h), zoom, torch: torch ? 'yes' : 'no' };
}

/** The plain line the owner reads on the camera view (?cam=1 only): "still 4032x3024, zoom 2x, light yes". */
export function debugLine(f: { method: LiveMethod | null; w: number; h: number; zoom: ZoomMode; zoomValue: number; torch: boolean }): string {
  const what = f.method ? `${f.method} ${f.w}x${f.h}` : `video ${f.w}x${f.h}`;
  const zoom = f.zoom === 'track' ? `zoom ${Math.round(f.zoomValue * 10) / 10}x` : 'zoom 2x by crop';
  return `${what}, ${zoom}, light ${f.torch ? 'yes' : 'no'}`;
}
