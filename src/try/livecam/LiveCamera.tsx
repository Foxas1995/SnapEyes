// The live camera inside /try (?cam=1 only, loaded lazily so /try's bundle does not grow for anybody else). The rear camera at the highest
// resolution the device gives (asked by the page inside the tap: the `stream` prop), 2x zoom (on the track when it has zoom, otherwise shown and cropped
// by us), continuous focus and tap to focus where the browser offers them, a torch button only when the track has one. One tap on the shutter takes BURST
// pictures over about a second and a half: real stills (ImageCapture.takePhoto, the largest up to about 12 MP the camera offers) where they exist, frames of
// the video otherwise; they go into the page's multi-photo path, which rates each and keeps the sharpest. Any failure gives way to the capture input with no
// error text (onFail); the camera is stopped on close, on unmount and when the page is hidden.
// 2026-11-26, the owner's Android phone in Messenger: `fixed inset-0` followed the layout viewport, which in that web view is about 90 px taller than what is
// visible and can pan, so the shutter fell below the screen. Now the page behind is locked while the view is open, the view is sized from visualViewport, and
// in Facebook's, Messenger's and Instagram's browsers the controls keep out of the top 72 and the bottom 100 px. Pure parts: ./logic.ts.
import React, { useEffect, useRef, useState } from 'react';
import { Camera, X, Flashlight } from 'lucide-react';
import {
  BURST, BURST_GAP_MS, FRAME_WAIT_MS, GRANT_WAIT_MS, SLOW_STILL_MS, type Cap, type Facts, type LiveFail, type LiveMethod, type ZoomMode,
  centreCrop, chooseStill, chooseZoom, circleCentre, debugLine, failClass, inApp, liveCap, viewInsets,
} from './logic';

export interface LiveCameraProps {
  /** the camera, asked by the page inside the tap (getUserMedia keeps the user's gesture; nothing is awaited before it) */
  stream: Promise<MediaStream>;
  hint: string;
  light: string;
  shutter: string;
  close: string;
  debug: boolean;
  onFrames: (files: File[], cap: Cap) => void;
  onFail: (why: LiveFail) => void;
  onClose: () => void;
}

type Caps = MediaTrackCapabilities & { zoom?: { min?: number; max?: number }; torch?: boolean; focusMode?: string[] };
type Range = { min?: number; max?: number };
interface ImageCaptureLike { takePhoto(settings?: { imageWidth?: number; imageHeight?: number }): Promise<Blob>; getPhotoCapabilities?(): Promise<{ imageWidth?: Range; imageHeight?: Range }> }
declare global { interface Window { ImageCapture?: new (t: MediaStreamTrack) => ImageCaptureLike } }

const timeout = (ms: number) => new Promise<never>((_, rej) => setTimeout(() => rej(Object.assign(new Error('timeout'), { name: 'TimeoutError' })), ms));
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const toBlob = (c: HTMLCanvasElement) => new Promise<Blob | null>((r) => c.toBlob(r, 'image/jpeg', 0.92));

/** A picture cropped to its middle for the CSS zoom (a still or a frame), as a JPEG; its canvas is released at once (memory: one still at a time). */
async function cropped(src: CanvasImageSource, w: number, h: number, factor: number): Promise<{ blob: Blob; w: number; h: number } | null> {
  const r = centreCrop(w, h, factor);
  const c = document.createElement('canvas');
  c.width = r.sw; c.height = r.sh;
  const g = c.getContext('2d');
  if (!g) return null;
  g.drawImage(src, r.sx, r.sy, r.sw, r.sh, 0, 0, r.sw, r.sh);
  const blob = await toBlob(c);
  c.width = 0; c.height = 0;
  return blob ? { blob, w: r.sw, h: r.sh } : null;
}

/** What the browser says of the visible area: visualViewport (its height and its top in the layout viewport), innerHeight where it has none. */
function visible(): { top: number; h: number; vvH: number; vvTop: number; inner: number; screen: number } {
  const vv = window.visualViewport;
  const inner = window.innerHeight;
  return { top: vv ? vv.offsetTop : 0, h: vv ? vv.height : inner, vvH: vv ? vv.height : 0, vvTop: vv ? vv.offsetTop : 0, inner, screen: window.screen?.height ?? 0 };
}

const LiveCamera: React.FC<LiveCameraProps> = ({ stream: asked, hint, light, shutter, close, debug, onFrames, onFail, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const doneRef = useRef(false);
  const [zoom, setZoom] = useState<{ mode: ZoomMode; value: number }>({ mode: 'css', value: 2 });
  const [torch, setTorch] = useState<{ has: boolean; on: boolean }>({ has: false, on: false });
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState(visible);
  const [shot, setShot] = useState<Pick<Facts, 'method' | 'video' | 'asked' | 'got'>>({ method: null, video: { w: 0, h: 0 }, asked: null, got: null });
  const app = typeof navigator !== 'undefined' && inApp(navigator.userAgent || '');
  const ins = viewInsets(app);

  const stop = () => { streamRef.current?.getTracks().forEach((t) => { try { t.stop(); } catch { /* gone */ } }); streamRef.current = null; };
  const fail = (e: unknown) => { if (doneRef.current) return; doneRef.current = true; stop(); onFail(failClass(e)); };
  const track = () => streamRef.current?.getVideoTracks()[0] ?? null;

  // the page behind is locked while the view is open (no scroll, no pan), and given back as it was on close
  useEffect(() => {
    const html = document.documentElement, body = document.body;
    const was = { html: html.style.overflow, body: body.style.overflow, bodyTouch: body.style.touchAction, x: window.scrollX, y: window.scrollY };
    window.scrollTo(0, 0);
    html.style.overflow = 'hidden'; body.style.overflow = 'hidden'; body.style.touchAction = 'none';
    const vv = window.visualViewport;
    const fit = () => setView(visible());
    vv?.addEventListener('resize', fit); vv?.addEventListener('scroll', fit); window.addEventListener('resize', fit);
    fit();
    return () => {
      vv?.removeEventListener('resize', fit); vv?.removeEventListener('scroll', fit); window.removeEventListener('resize', fit);
      html.style.overflow = was.html; body.style.overflow = was.body; body.style.touchAction = was.bodyTouch;
      window.scrollTo(was.x, was.y);
    };
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const stream = await Promise.race([asked, timeout(GRANT_WAIT_MS)]);
        if (!alive) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        const t = stream.getVideoTracks()[0];
        if (!t) throw Object.assign(new Error('no track'), { name: 'NotFoundError' });
        const caps = ((t.getCapabilities?.() ?? {}) as Caps);
        const z = chooseZoom(caps);
        if (z.mode === 'track') {
          try { await t.applyConstraints({ advanced: [{ zoom: z.value } as MediaTrackConstraintSet] }); } catch { z.mode = 'css'; z.value = 2; }
        }
        if (Array.isArray(caps.focusMode) && caps.focusMode.includes('continuous')) {
          try { await t.applyConstraints({ advanced: [{ focusMode: 'continuous' } as MediaTrackConstraintSet] }); } catch { /* not this one */ }
        }
        setZoom({ ...z });
        setTorch({ has: caps.torch === true, on: false });
        const v = videoRef.current;
        if (!v) throw new Error('no video');
        v.srcObject = stream;
        await Promise.race([
          (async () => { await v.play().catch(() => undefined); for (;;) { if (v.videoWidth > 0 && v.readyState >= 2) return; await sleep(80); } })(),
          timeout(FRAME_WAIT_MS),
        ]);
        if (!alive) return;
        setShot((s) => ({ ...s, video: { w: v.videoWidth, h: v.videoHeight } }));
        setReady(true);
      } catch (e) {
        if (alive) fail(e);
      }
    })();
    const hidden = () => { if (document.visibilityState === 'hidden' && !doneRef.current) { doneRef.current = true; stop(); onClose(); } };
    document.addEventListener('visibilitychange', hidden);
    return () => { alive = false; document.removeEventListener('visibilitychange', hidden); stop(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Tap to focus where the browser offers points of interest (the point in the video's own 0-1 frame). */
  const focusAt = (e: React.PointerEvent<HTMLVideoElement>) => {
    const t = track();
    const sup = (navigator.mediaDevices?.getSupportedConstraints?.() ?? {}) as Record<string, boolean>;
    if (!t || !sup.pointsOfInterest) return;
    const r = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    t.applyConstraints({ advanced: [{ pointsOfInterest: [{ x, y }], focusMode: 'single-shot' } as unknown as MediaTrackConstraintSet] }).catch(() => undefined);
  };

  const toggleTorch = () => {
    const t = track();
    if (!t || !torch.has) return;
    const on = !torch.on;
    t.applyConstraints({ advanced: [{ torch: on } as unknown as MediaTrackConstraintSet] }).then(() => setTorch({ has: true, on })).catch(() => undefined);
  };

  const shoot = async () => {
    const t = track(), v = videoRef.current;
    if (!t || !v || busy || doneRef.current) return;
    setBusy(true);
    try {
      const files: File[] = [];
      let method: LiveMethod = window.ImageCapture ? 'still' : 'frame';
      const ic = method === 'still' && window.ImageCapture ? new window.ImageCapture(t) : null;
      // the largest still the camera offers, up to about 12 MP (a plain takePhoto when it says nothing, or when the sized one fails)
      let size: { w: number; h: number } | null = null;
      if (ic?.getPhotoCapabilities) { try { size = chooseStill(await ic.getPhotoCapabilities()); } catch { size = null; } }
      const crop = zoom.mode === 'css' ? zoom.value : 1;          // real zoom on the track: no crop on top of it
      let burst = BURST;
      let got: { w: number; h: number } | null = null;
      for (let i = 0; i < burst; i++) {
        const t0 = Date.now();
        let pic: { blob: Blob; w: number; h: number } | null = null;
        if (method === 'still' && ic) {
          try {
            let still: Blob;
            if (size) { try { still = await ic.takePhoto({ imageWidth: size.w, imageHeight: size.h }); } catch { size = null; still = await ic.takePhoto(); } }
            else still = await ic.takePhoto();
            if (i === 0 && size && Date.now() - t0 > SLOW_STILL_MS) burst = Math.min(burst, 3);   // a slow sized still: 3 of them, not 4
            const bmp = await createImageBitmap(still);                  // one still at a time: decoded, cropped, released
            pic = crop > 1 ? await cropped(bmp, bmp.width, bmp.height, crop) : { blob: still, w: bmp.width, h: bmp.height };
            bmp.close();
          } catch {
            method = 'frame';       // a browser whose stills fail: the video's frames for the rest of the burst (and the codes say so)
          }
        }
        if (!pic) pic = await cropped(v, v.videoWidth, v.videoHeight, crop);
        if (pic) { files.push(new File([pic.blob], `live-${i + 1}.jpg`, { type: 'image/jpeg' })); got = { w: pic.w, h: pic.h }; }
        setShot((s) => ({ ...s, method, asked: method === 'still' ? size : null, got }));
        if (i < burst - 1) await sleep(Math.max(0, BURST_GAP_MS - (Date.now() - t0)));
      }
      if (!files.length || !got) throw new Error('no frame');
      doneRef.current = true;
      stop();
      onFrames(files, liveCap(method, got.w, got.h, zoom.mode, torch.has));
    } catch (e) {
      fail(e);
    }
  };

  const shut = () => { if (doneRef.current) return; doneRef.current = true; stop(); onClose(); };

  // the view is the visible area itself (visualViewport), not the layout viewport; the controls keep inside the part that is surely seen
  const top = `calc(${ins.top}px + env(safe-area-inset-top, 0px))`;
  const bottom = `calc(${ins.bottom}px + env(safe-area-inset-bottom, 0px))`;
  const cy = circleCentre(view.h, ins.top, ins.bottom);
  return (
    <div data-testid="live-camera" role="dialog" aria-modal="true" className="fixed left-0 right-0 z-50 bg-black text-white overflow-hidden"
      style={{ top: view.top, height: view.h, touchAction: 'none', overscrollBehavior: 'contain' }}>
      <video ref={videoRef} playsInline muted autoPlay onPointerDown={focusAt} className="absolute inset-0 w-full h-full object-cover"
        style={zoom.mode === 'css' ? { transform: `scale(${zoom.value})` } : undefined} />
      {/* where the eye goes: in the middle of the part that is surely visible */}
      <div aria-hidden className="pointer-events-none absolute left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white/80 shadow-[0_0_0_9999px_rgba(0,0,0,0.35)]"
        style={{ top: cy, width: 'min(58vw, 46vh)', height: 'min(58vw, 46vh)' }} />
      <p data-testid="live-hint" className="absolute inset-x-0 text-center text-base font-semibold drop-shadow" style={{ top: `calc(${top} + 16px)` }}>{hint}</p>
      <button type="button" data-testid="live-close" onClick={shut} aria-label={close} className="absolute right-3 w-11 h-11 rounded-full bg-black/50 flex items-center justify-center"
        style={{ top: `calc(${top} + 10px)` }}>
        <X className="w-6 h-6" />
      </button>
      <div className="absolute inset-x-0 flex items-center justify-center h-28" style={{ bottom }}>
        {torch.has && (
          <button type="button" onClick={toggleTorch} aria-pressed={torch.on}
            className={`absolute left-4 px-3 py-2 rounded-full text-sm font-semibold flex items-center gap-1 ${torch.on ? 'bg-gold text-black' : 'bg-black/50'}`}>
            <Flashlight className="w-4 h-4" /> {light}
          </button>
        )}
        <button type="button" data-testid="live-shutter" onClick={shoot} disabled={!ready || busy} aria-label={shutter}
          className="w-20 h-20 rounded-full border-4 border-white bg-white/20 disabled:opacity-40 flex items-center justify-center active:scale-95">
          <Camera className="w-8 h-8" />
        </button>
        {debug && (
          <p data-testid="live-facts" className="absolute -bottom-1 inset-x-0 text-center text-[10px] text-zinc-300 drop-shadow">
            {debugLine({ geo: view, ...shot, zoom: zoom.mode, zoomValue: zoom.value, torch: torch.has })}
          </p>
        )}
      </div>
    </div>
  );
};

export default LiveCamera;
