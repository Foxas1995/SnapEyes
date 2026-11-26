// The live camera inside /try (?cam=1 only, loaded lazily so /try's bundle does not grow for anybody else). The rear camera at the highest
// resolution the device gives, 2x zoom (on the track when it has zoom, otherwise shown and cropped by us), continuous focus and tap to focus
// where the browser offers them, a torch button only when the track has one. One tap on the shutter takes BURST frames over about a second and
// a half: real stills (ImageCapture.takePhoto) where they exist, frames of the video otherwise; they go into the page's multi-photo path, which
// rates each and keeps the sharpest. Any failure gives way to the capture input with no error text (onFail); the camera is stopped on close,
// on unmount and when the page is hidden. Pure parts: ./logic.ts.
import React, { useEffect, useRef, useState } from 'react';
import { Camera, X, Flashlight } from 'lucide-react';
import {
  BURST, BURST_GAP_MS, FRAME_WAIT_MS, GRANT_WAIT_MS, IDEAL, type Cap, type LiveFail, type LiveMethod, type ZoomMode,
  centreCrop, chooseZoom, debugLine, failClass, liveCap,
} from './logic';

export interface LiveCameraProps {
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
interface ImageCaptureLike { takePhoto(): Promise<Blob> }
declare global { interface Window { ImageCapture?: new (t: MediaStreamTrack) => ImageCaptureLike } }

const timeout = (ms: number) => new Promise<never>((_, rej) => setTimeout(() => rej(Object.assign(new Error('timeout'), { name: 'TimeoutError' })), ms));
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const toBlob = (c: HTMLCanvasElement) => new Promise<Blob | null>((r) => c.toBlob(r, 'image/jpeg', 0.92));

/** A picture cropped to its middle for the CSS zoom (a still or a frame), as a JPEG. */
async function cropped(src: CanvasImageSource, w: number, h: number, factor: number): Promise<{ blob: Blob; w: number; h: number } | null> {
  const r = centreCrop(w, h, factor);
  const c = document.createElement('canvas');
  c.width = r.sw; c.height = r.sh;
  const g = c.getContext('2d');
  if (!g) return null;
  g.drawImage(src, r.sx, r.sy, r.sw, r.sh, 0, 0, r.sw, r.sh);
  const blob = await toBlob(c);
  return blob ? { blob, w: r.sw, h: r.sh } : null;
}

const LiveCamera: React.FC<LiveCameraProps> = ({ hint, light, shutter, close, debug, onFrames, onFail, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const doneRef = useRef(false);
  const [zoom, setZoom] = useState<{ mode: ZoomMode; value: number }>({ mode: 'css', value: 2 });
  const [torch, setTorch] = useState<{ has: boolean; on: boolean }>({ has: false, on: false });
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [info, setInfo] = useState<{ method: LiveMethod | null; w: number; h: number }>({ method: null, w: 0, h: 0 });

  const stop = () => { streamRef.current?.getTracks().forEach((t) => { try { t.stop(); } catch { /* gone */ } }); streamRef.current = null; };
  const fail = (e: unknown) => { if (doneRef.current) return; doneRef.current = true; stop(); onFail(failClass(e)); };
  const track = () => streamRef.current?.getVideoTracks()[0] ?? null;

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const md = navigator.mediaDevices;
        if (!md?.getUserMedia) throw Object.assign(new Error('no mediaDevices'), { name: 'NotSupportedError' });
        const stream = await Promise.race([
          md.getUserMedia({ audio: false, video: { facingMode: { ideal: 'environment' }, width: { ideal: IDEAL.width }, height: { ideal: IDEAL.height } } }),
          timeout(GRANT_WAIT_MS),
        ]);
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
        setInfo({ method: null, w: v.videoWidth, h: v.videoHeight });
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
      let w = 0, h = 0;
      for (let i = 0; i < BURST; i++) {
        const t0 = Date.now();
        let got: { blob: Blob; w: number; h: number } | null = null;
        if (method === 'still' && ic) {
          try {
            const still = await ic.takePhoto();
            const bmp = await createImageBitmap(still);
            got = zoom.mode === 'css' ? await cropped(bmp, bmp.width, bmp.height, zoom.value) : { blob: still, w: bmp.width, h: bmp.height };
            bmp.close();
          } catch {
            method = 'frame';       // a browser whose stills fail: the video's frames for the rest of the burst (and the codes say so)
          }
        }
        if (!got) got = await cropped(v, v.videoWidth, v.videoHeight, zoom.mode === 'css' ? zoom.value : 1);
        if (got) { files.push(new File([got.blob], `live-${i + 1}.jpg`, { type: 'image/jpeg' })); w = got.w; h = got.h; }
        setInfo({ method, w, h });
        if (i < BURST - 1) await sleep(Math.max(0, BURST_GAP_MS - (Date.now() - t0)));
      }
      if (!files.length) throw new Error('no frame');
      doneRef.current = true;
      stop();
      onFrames(files, liveCap(method, w, h, zoom.mode, torch.has));
    } catch (e) {
      fail(e);
    }
  };

  const shut = () => { if (doneRef.current) return; doneRef.current = true; stop(); onClose(); };

  return (
    <div data-testid="live-camera" className="fixed inset-0 z-50 bg-black text-white flex flex-col" role="dialog" aria-modal="true">
      <div className="relative flex-1 overflow-hidden">
        <video ref={videoRef} playsInline muted autoPlay onPointerDown={focusAt} className="absolute inset-0 w-full h-full object-cover"
          style={zoom.mode === 'css' ? { transform: `scale(${zoom.value})` } : undefined} />
        {/* where the eye goes */}
        <div aria-hidden className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white/80 shadow-[0_0_0_9999px_rgba(0,0,0,0.35)]"
          style={{ width: '58vmin', height: '58vmin' }} />
        <p className="absolute top-4 inset-x-0 text-center text-base font-semibold drop-shadow">{hint}</p>
        <button type="button" onClick={shut} aria-label={close} className="absolute top-3 right-3 w-11 h-11 rounded-full bg-black/50 flex items-center justify-center">
          <X className="w-6 h-6" />
        </button>
      </div>
      <div className="relative h-28 flex items-center justify-center">
        {torch.has && (
          <button type="button" onClick={toggleTorch} aria-pressed={torch.on}
            className={`absolute left-4 px-3 py-2 rounded-full text-sm font-semibold flex items-center gap-1 ${torch.on ? 'bg-gold text-black' : 'bg-white/10'}`}>
            <Flashlight className="w-4 h-4" /> {light}
          </button>
        )}
        <button type="button" data-testid="live-shutter" onClick={shoot} disabled={!ready || busy} aria-label={shutter}
          className="w-20 h-20 rounded-full border-4 border-white bg-white/20 disabled:opacity-40 flex items-center justify-center active:scale-95">
          <Camera className="w-8 h-8" />
        </button>
        {debug && <p data-testid="live-facts" className="absolute bottom-1 inset-x-0 text-center text-[10px] text-zinc-400">{debugLine({ ...info, zoom: zoom.mode, zoomValue: zoom.value, torch: torch.has })}</p>}
      </div>
    </div>
  );
};

export default LiveCamera;
