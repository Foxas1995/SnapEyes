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
import { Camera, Check, X, Flashlight } from 'lucide-react';
import {
  BURST, BURST_GAP_MS, DARK_EVERY_MS, DARK_SIDE, FRAME_WAIT_MS, GRANT_WAIT_MS, SETTLE_MS, type Cap, type Facts, type LiveFail, type LiveMethod, type ZoomMode,
  centreCrop, chooseStill, chooseZoom, circleCentre, debugLine, failClass, inApp, liveCap, meanLuma, photoSettings, takeBurst, tooDark, viewInsets,
} from './logic';

export interface LiveCameraProps {
  /** the camera, asked by the page inside the tap (getUserMedia keeps the user's gesture; nothing is awaited before it) */
  stream: Promise<MediaStream>;
  hint: string;
  /** the second line while the picture is too dark (instead of burstLine) */
  darkLine: string;
  /** under the hint before the tap: how many pictures one tap takes and to hold still (the number is BURST) */
  burstLine: string;
  /** during the burst, large, with the count */
  holdStill: string;
  /** when the last picture is in */
  done: string;
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
type PhotoSettings = { imageWidth?: number; imageHeight?: number; fillLightMode?: string };
interface ImageCaptureLike { takePhoto(settings?: PhotoSettings): Promise<Blob>; getPhotoCapabilities?(): Promise<{ imageWidth?: Range; imageHeight?: Range }> }
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

const LiveCamera: React.FC<LiveCameraProps> = ({ stream: asked, hint, darkLine, burstLine, holdStill, done, light, shutter, close, debug, onFrames, onFail, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const doneRef = useRef(false);
  const [zoom, setZoom] = useState<{ mode: ZoomMode; value: number }>({ mode: 'css', value: 2 });
  const [torch, setTorch] = useState<{ has: boolean; on: boolean }>({ has: false, on: false });
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [taken, setTaken] = useState(0);          // the picture of the burst being taken (1 to BURST); 0 before the tap
  const [finished, setFinished] = useState(false);
  const [dark, setDark] = useState(false);          // the middle of the picture is too dark (the second line warns; the shutter stays usable)
  const [settling, setSettling] = useState(false);  // the torch was just switched: the exposure settles
  const [takes, setTakes] = useState<Facts['takes']>(null);
  const still = typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
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
        // the still that will be taken (its pixels decide whether our crop may be 3x: 1.3 MP or more must remain), then the zoom: the track's own up to 3x,
        // otherwise our crop of 2x or 3x; the preview is scaled the same, so the circle shows what will be kept
        let stillPx = 0;
        if (window.ImageCapture) {
          try { const sz = chooseStill(await new window.ImageCapture(t).getPhotoCapabilities?.()); stillPx = sz ? sz.w * sz.h : 0; } catch { stillPx = 0; }
        }
        const z = chooseZoom(caps, stillPx);
        if (z.mode === 'track') {
          try { await t.applyConstraints({ advanced: [{ zoom: z.value } as MediaTrackConstraintSet] }); } catch { Object.assign(z, chooseZoom(null, stillPx)); }
        }
        // continuous focus, exposure and white balance, metered at the middle (the circle), each only where the track offers it, each on its own
        const modes = caps as Caps & { exposureMode?: string[]; whiteBalanceMode?: string[] };
        const sup = (navigator.mediaDevices?.getSupportedConstraints?.() ?? {}) as Record<string, boolean>;
        for (const c of [
          Array.isArray(caps.focusMode) && caps.focusMode.includes('continuous') ? { focusMode: 'continuous' } : null,
          Array.isArray(modes.exposureMode) && modes.exposureMode.includes('continuous') ? { exposureMode: 'continuous' } : null,
          Array.isArray(modes.whiteBalanceMode) && modes.whiteBalanceMode.includes('continuous') ? { whiteBalanceMode: 'continuous' } : null,
          sup.pointsOfInterest ? { pointsOfInterest: [{ x: 0.5, y: 0.5 }] } : null,
        ]) {
          if (!c) continue;
          try { await t.applyConstraints({ advanced: [c as unknown as MediaTrackConstraintSet] }); } catch { /* not this one */ }
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

  // after the torch is switched the shutter waits SETTLE_MS, so the camera's exposure settles before a picture (the owner's burnt and dark stills)
  const toggleTorch = () => {
    const t = track();
    if (!t || !torch.has) return;
    const on = !torch.on;
    setSettling(true);
    t.applyConstraints({ advanced: [{ torch: on } as unknown as MediaTrackConstraintSet] }).then(() => setTorch({ has: true, on })).catch(() => undefined)
      .finally(() => { window.setTimeout(() => setSettling(false), SETTLE_MS); });
  };

  // the darkness warning: twice a second the middle of the video (the picture as it is, with the torch in its current state) is averaged in a 32 x 32
  // canvas; it stops during the burst and when the view closes
  useEffect(() => {
    if (!ready || busy || finished) return;
    const c = document.createElement('canvas');
    c.width = DARK_SIDE; c.height = DARK_SIDE;
    const g = c.getContext('2d', { willReadFrequently: true });
    if (!g) return;
    const id = window.setInterval(() => {
      const v = videoRef.current;
      if (!v || !v.videoWidth) return;
      try {
        const r = centreCrop(v.videoWidth, v.videoHeight, (zoom.mode === 'css' ? zoom.value : 1) * 2);
        g.drawImage(v, r.sx, r.sy, r.sw, r.sh, 0, 0, DARK_SIDE, DARK_SIDE);
        setDark(tooDark(meanLuma(g.getImageData(0, 0, DARK_SIDE, DARK_SIDE).data)));
      } catch { /* a frame that cannot be read: no warning */ }
    }, DARK_EVERY_MS);
    return () => { window.clearInterval(id); c.width = 0; c.height = 0; };
  }, [ready, busy, finished, zoom]);

  const shoot = async () => {
    const t = track(), v = videoRef.current;
    if (!t || !v || busy || doneRef.current) return;
    setBusy(true);
    const darkAtTap = dark;
    try {
      let method: LiveMethod = window.ImageCapture ? 'still' : 'frame';
      const ic = method === 'still' && window.ImageCapture ? new window.ImageCapture(t) : null;
      // the largest still the camera offers, up to about 12 MP, and no flash where the camera lets us say so (the torch stays as the person set it); a plain
      // takePhoto when it says nothing or the asked one is refused, the video's frames when stills fail
      let settings: PhotoSettings | null = null;
      let size: { w: number; h: number } | null = null;
      if (ic?.getPhotoCapabilities) {
        try { const pc = await ic.getPhotoCapabilities(); size = chooseStill(pc); settings = photoSettings(size, (pc as { fillLightMode?: unknown }).fillLightMode); } catch { settings = null; }
      }
      const crop = zoom.mode === 'css' ? zoom.value : 1;          // real zoom on the track: no crop on top of it
      const meter = document.createElement('canvas');
      meter.width = DARK_SIDE; meter.height = DARK_SIDE;
      const mg = meter.getContext('2d', { willReadFrequently: true });
      const lumaOf = (src: CanvasImageSource, w: number, h: number): number => {
        if (!mg) return 128;
        const r = centreCrop(w, h, crop * 2);
        mg.drawImage(src, r.sx, r.sy, r.sw, r.sh, 0, 0, DARK_SIDE, DARK_SIDE);
        return meanLuma(mg.getImageData(0, 0, DARK_SIDE, DARK_SIDE).data);
      };
      let got: { w: number; h: number } | null = null;
      let last = 0;
      // the number of usable pictures is fixed before the burst starts (the line under the hint and the count say it): a burnt or black one is thrown away and
      // another taken (at most MAX_TAKES), so the burst may be longer, never shorter, and the count never goes back
      const res = await takeBurst<{ blob: Blob; w: number; h: number; luma: number }>(async (i) => {
        if (i > 0) await sleep(Math.max(0, BURST_GAP_MS - (Date.now() - last)));
        last = Date.now();
        let pic: { blob: Blob; w: number; h: number; luma: number } | null = null;
        if (method === 'still' && ic) {
          try {
            let still: Blob;
            if (settings) { try { still = await ic.takePhoto(settings); } catch { settings = null; size = null; still = await ic.takePhoto(); } }
            else still = await ic.takePhoto();
            const bmp = await createImageBitmap(still);                  // one still at a time: measured, cropped, released
            const luma = lumaOf(bmp, bmp.width, bmp.height);
            const c = crop > 1 ? await cropped(bmp, bmp.width, bmp.height, crop) : { blob: still, w: bmp.width, h: bmp.height };
            bmp.close();
            if (c) pic = { ...c, luma };
          } catch {
            method = 'frame';       // a browser whose stills fail: the video's frames for the rest of the burst (and the codes say so)
          }
        }
        if (!pic) {
          const luma = lumaOf(v, v.videoWidth, v.videoHeight);
          const c = await cropped(v, v.videoWidth, v.videoHeight, crop);
          if (c) pic = { ...c, luma };
        }
        if (pic) got = { w: pic.w, h: pic.h };
        setShot((s) => ({ ...s, method, asked: method === 'still' ? size : null, got }));
        return pic;
      }, (k) => setTaken(k));
      meter.width = 0; meter.height = 0;
      setTakes({ n: res.takes, burnt: res.burnt, black: res.black });
      const files = res.kept.map((p, i) => new File([p.blob], `live-${i + 1}.jpg`, { type: 'image/jpeg' }));
      if (!files.length || !got) throw new Error('no frame');
      const size0 = { w: res.kept[0].w, h: res.kept[0].h };
      doneRef.current = true;
      stop();
      // the last one is in: "Done" with a check (the page keeps the view a moment while the pictures are already on their way) and one short buzz where allowed
      setFinished(true);
      try { navigator.vibrate?.(40); } catch { /* blocked or missing */ }
      onFrames(files, liveCap(method, size0.w, size0.h, zoom.mode, torch.has, darkAtTap, zoom.value));
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
      {/* before the tap: the hint and how many pictures one tap takes; during the burst: "Hold still" with the count; at the end: "Done" with a check.
          Kept clear of the close button on both sides (px-14) and inside the band the in-app browsers surely show */}
      <div data-testid="live-hint" role="status" className="absolute inset-x-0 px-14 text-center drop-shadow" style={{ top: `calc(${top} + 14px)` }}>
        {finished ? (
          <p data-testid="live-done" className="text-2xl font-bold flex items-center justify-center gap-2"><Check className="w-7 h-7 text-emerald-300" /> {done}</p>
        ) : busy && taken > 0 ? (
          <>
            <p className="text-2xl font-bold">{holdStill}</p>
            <p data-testid="live-count" className="text-lg font-semibold tabular-nums">{taken} / {BURST}</p>
          </>
        ) : (
          <>
            <p className="text-base font-semibold">{hint}</p>
            {dark
              ? <p data-testid="live-dark" className="text-sm font-semibold text-amber-200">{darkLine}</p>
              : <p data-testid="live-burst" className="text-sm text-zinc-200">{burstLine}</p>}
          </>
        )}
      </div>
      <button type="button" data-testid="live-close" onClick={shut} aria-label={close} className="absolute right-3 w-11 h-11 rounded-full bg-black/50 flex items-center justify-center"
        style={{ top: `calc(${top} + 10px)` }}>
        <X className="w-6 h-6" />
      </button>
      <div className="absolute inset-x-0 flex items-center justify-center h-28" style={{ bottom }}>
        {torch.has && (
          <button type="button" onClick={toggleTorch} aria-pressed={torch.on}
            className={`absolute left-4 px-3 py-2 rounded-full text-sm font-semibold flex items-center gap-1 ${torch.on ? 'bg-gold text-black' : 'bg-black/50'} ${dark && !torch.on ? 'ring-2 ring-gold' : ''}`}>
            <Flashlight className="w-4 h-4" /> {light}
          </button>
        )}
        <span className="relative w-20 h-20">
          <button type="button" data-testid="live-shutter" onClick={shoot} disabled={!ready || busy || settling} aria-label={shutter}
            className={`w-20 h-20 rounded-full border-4 border-white bg-white/20 flex items-center justify-center active:scale-95 ${busy ? 'disabled:opacity-70' : 'disabled:opacity-40'}`}>
            <Camera className="w-8 h-8" />
          </button>
          {/* the ring around the shutter fills one step per picture (under reduced motion the count above says it alone) */}
          {busy && !still && (
            <svg data-testid="live-ring" aria-hidden viewBox="0 0 100 100" className="pointer-events-none absolute -inset-2 w-24 h-24 -rotate-90">
              <circle cx="50" cy="50" r="46" fill="none" stroke="rgb(212 175 55)" strokeWidth="6" strokeLinecap="round" pathLength={100}
                strokeDasharray="100" strokeDashoffset={100 - (100 * (finished ? BURST : taken)) / BURST} style={{ transition: 'stroke-dashoffset 450ms ease-out' }} />
            </svg>
          )}
        </span>
        {debug && (
          <p data-testid="live-facts" className="absolute -bottom-1 inset-x-0 text-center text-[10px] text-zinc-300 drop-shadow">
            {debugLine({ geo: view, ...shot, takes, zoom: zoom.mode, zoomValue: zoom.value, torch: torch.has })}
          </p>
        )}
      </div>
    </div>
  );
};

export default LiveCamera;
