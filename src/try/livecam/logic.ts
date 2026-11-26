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
/** What the page asks of the camera: the rear one at the highest resolution the device gives (asked inside the tap, src/try/TryApp.tsx startCamera). */
export const VIDEO: MediaStreamConstraints = { audio: false, video: { facingMode: { ideal: 'environment' }, width: { ideal: IDEAL.width }, height: { ideal: IDEAL.height } } };
export const STILL_LONG_MAX = 4096;       // a still asked of ImageCapture: at most this on its long side...
export const STILL_PIXELS_MAX = 12e6;     // ...and about 12 MP (memory: one still is decoded, cropped and released at a time)
export const SLOW_STILL_MS = 1200;        // a sized still slower than this: the burst takes 3, not 4
// Facebook's, Messenger's and Instagram's Android web views report a height about 85 to 90 px larger than what is visible (the owner's phone, 2026-11-26) and
// can pan: in them every control keeps out of the top and the bottom of the view (the video still fills it). The same browser test as the server's
// (api/_lib/counter.py ua_classes).
export const INAPP_TOP = 72;
export const INAPP_BOTTOM = 100;
export const inApp = (ua: string): boolean => /Instagram/.test(ua) || /FBAN|FBAV|FB_IAB|FBIOS|FB4A|FBMD|MESSENGER/.test(ua);

type Range = { min?: number; max?: number } | undefined;
/** The still to ask ImageCapture.takePhoto for: the largest the photo capabilities offer, at most STILL_LONG_MAX on its long side and STILL_PIXELS_MAX in
 *  all, the camera's own shape kept; null when the capabilities say nothing usable (then a plain takePhoto()). */
export function chooseStill(caps: { imageWidth?: Range; imageHeight?: Range } | null | undefined): { w: number; h: number } | null {
  const W = caps?.imageWidth?.max, H = caps?.imageHeight?.max;
  if (typeof W !== 'number' || typeof H !== 'number' || !(W > 0) || !(H > 0)) return null;
  let f = Math.min(1, STILL_LONG_MAX / Math.max(W, H));
  if (W * H * f * f > STILL_PIXELS_MAX) f = Math.sqrt(STILL_PIXELS_MAX / (W * H));
  const wMin = caps?.imageWidth?.min ?? 0, hMin = caps?.imageHeight?.min ?? 0;
  return { w: Math.max(wMin, Math.floor(W * f)), h: Math.max(hMin, Math.floor(H * f)) };
}

/** Where the controls may stand in a view of height h: the top and bottom margins (in-app browsers keep clear of the parts they hide) and the middle of the
 *  part that is surely visible, where the circle goes. */
export function viewInsets(inAppBrowser: boolean): { top: number; bottom: number } {
  return inAppBrowser ? { top: INAPP_TOP, bottom: INAPP_BOTTOM } : { top: 0, bottom: 0 };
}
export const circleCentre = (h: number, top: number, bottom: number): number => Math.round(top + (h - top - bottom) / 2);

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

/** The plain line the owner reads on the camera view (?cam=1 only): the geometry the browser reports, then what the camera gave:
 *  "vv 780/0 in 866 sc 915 · still 4000x3000 > 2000x1500 · zoom 2x crop · light yes" (a still asked of that size, kept cropped to that size). */
export interface Facts {
  geo: { vvH: number; vvTop: number; inner: number; screen: number };
  method: LiveMethod | null;      // null: nothing taken yet (the video's own size is shown)
  video: { w: number; h: number };
  asked: { w: number; h: number } | null;   // the still asked of ImageCapture (null: a plain takePhoto, or frames)
  got: { w: number; h: number } | null;     // what one picture of the burst really was, after the crop
  zoom: ZoomMode;
  zoomValue: number;
  torch: boolean;
}
export function debugLine(f: Facts): string {
  const g = f.geo;
  const geo = `vv ${Math.round(g.vvH)}/${Math.round(g.vvTop)} in ${Math.round(g.inner)} sc ${Math.round(g.screen)}`;
  const sz = (x: { w: number; h: number }) => `${x.w}x${x.h}`;
  const what = !f.method ? `video ${sz(f.video)}`
    : f.method === 'still' ? `still ${f.asked ? sz(f.asked) : 'plain'}${f.got ? ` > ${sz(f.got)}` : ''}`
    : `frame ${f.got ? sz(f.got) : sz(f.video)}`;
  const zoom = f.zoom === 'track' ? `zoom ${Math.round(f.zoomValue * 10) / 10}x track` : `zoom ${Math.round(f.zoomValue * 10) / 10}x crop`;
  return [geo, what, zoom, `light ${f.torch ? 'yes' : 'no'}`].join(' · ');
}
