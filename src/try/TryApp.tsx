import React, { useEffect, useRef, useState } from 'react';
import { Camera, Upload, Sparkles, RefreshCcw, Download, Video, Check, AlertTriangle, ZoomIn } from 'lucide-react';
import { CompareSlider } from './CompareSlider';

type Step = 'capture' | 'analyzing' | 'quality' | 'processing' | 'result';
type Mode = 'faithful' | 'artistic';

interface Analysis {
  ok: boolean;
  reason?: string;
  message?: string;
  ticket?: string;
  pupil_r?: number | null;
  iris?: { cx: number; cy: number; r: number };
  pad?: number;
  glare_boxes_crop?: number[][];
  quality?: { diameter_px: number; sharpness: number; sharpness_label: string; occlusion_pct: number; glare: boolean; verdict: 'good' | 'ok' | 'weak'; message: string; tips: string[] };
  preview?: string;
}

interface Enhanced { image: string; fidelity: number; used_sr: boolean; fallback: boolean; seconds: number; stored?: boolean }

const STYLES: Array<{ id: string; name: string; thumb: string }> = [
  { id: 'celestial_gold', name: 'Celestial Gold', thumb: '/assets/style_thumb_celestial_gold.jpg' },
  { id: 'deep_nebula', name: 'Deep Nebula', thumb: '/assets/style_thumb_deep_nebula.jpg' },
  { id: 'emerald_aurora', name: 'Emerald Aurora', thumb: '/assets/style_thumb_emerald_aurora.jpg' },
  { id: 'obsidian_smoke', name: 'Obsidian Smoke', thumb: '/assets/style_thumb_obsidian_smoke.jpg' },
  { id: 'supernova', name: 'Supernova', thumb: '/assets/style_thumb_supernova.jpg' },
  { id: 'studio_black', name: 'Studio Black', thumb: '/assets/style_thumb_studio_black.jpg' },
];

const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  });
  // Vercel answers a timeout or an oversized body with text/plain, so read text first and never let
  // JSON.parse throw the real status away
  const raw = await r.text();
  let j: any = null;
  try { j = JSON.parse(raw); } catch { /* platform error, not ours */ }
  if (!j) {
    if (r.status === 413) throw new Error('That photo is too large. Try again with a normal camera photo.');
    if (r.status === 504 || /TIMEOUT/i.test(raw)) throw new Error('That took too long on our side. Please try again.');
    throw new Error('The studio is not responding right now. Please try again in a moment.');
  }
  if (!r.ok || j.ok === false) throw new Error(j.error || j.message || `Request failed (${r.status})`);
  return j as T;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Could not read this image'));
    img.src = src;
  });
}

function drawToDataUrl(img: HTMLImageElement, sx: number, sy: number, sw: number, sh: number, outW: number, outH: number, quality = 0.92): string {
  const c = document.createElement('canvas');
  c.width = outW; c.height = outH;
  const ctx = c.getContext('2d')!;
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, outW, outH);
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, outW, outH);
  return c.toDataURL('image/jpeg', quality);
}

function stripDataUrl(s: string) { return s.includes(',') ? s.split(',')[1] : s; }

export const TryApp: React.FC = () => {
  const [step, setStep] = useState<Step>('capture');
  const [error, setError] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);
  const [storageOn, setStorageOn] = useState(false);
  const [session] = useState(() => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`);
  const [origUrl, setOrigUrl] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [clientCrop, setClientCrop] = useState<string | null>(null);
  const [cleanCrop, setCleanCrop] = useState<string | null>(null);
  const [glarePct, setGlarePct] = useState<number>(0);
  const [results, setResults] = useState<Partial<Record<Mode, Enhanced>>>({});
  const [mode, setMode] = useState<Mode>('faithful');
  const [style, setStyle] = useState('celestial_gold');
  const [names, setNames] = useState('');
  const [artCache, setArtCache] = useState<Record<string, string>>({});
  const [composing, setComposing] = useState(false);
  const [progress, setProgress] = useState<string[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [liveOpen, setLiveOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);

  // only offer the training-memory checkbox when this deployment can really store something
  useEffect(() => {
    let alive = true;
    fetch('/api/health')
      .then((r) => r.json())
      .then((h) => { if (alive) setStorageOn(!!h.blob_store); })
      .catch(() => { /* health is optional */ });
    return () => { alive = false; };
  }, []);

  // elapsed timer while the engine works
  useEffect(() => {
    if (step !== 'analyzing' && step !== 'processing') return;
    setElapsed(0);
    const id = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(id);
  }, [step]);

  const reset = () => {
    setStep('capture'); setError(null); setAnalysis(null); setClientCrop(null); setCleanCrop(null); setResults({}); setArtCache({});
    setMode('faithful'); setProgress([]); setOrigUrl(null); imgRef.current = null;
  };

  const onFile = async (file: File | Blob) => {
    setError(null);
    const url = URL.createObjectURL(file);
    try {
      const img = await loadImage(url);
      imgRef.current = img; setOrigUrl(url);
      await analyze(img);
    } catch (e) {
      setError((e as Error).message); setStep('capture');
    }
  };

  const analyze = async (img: HTMLImageElement) => {
    setStep('analyzing');
    const W = img.naturalWidth, H = img.naturalHeight;
    const f = Math.min(1, 1600 / Math.max(W, H));
    const small = drawToDataUrl(img, 0, 0, W, H, Math.round(W * f), Math.round(H * f), 0.9);
    const a = await post<Analysis>('/api/analyze', { image: stripDataUrl(small), origWidth: W, origHeight: H });
    setAnalysis(a);
    if (!a.ok || !a.iris) { setError(a.message || 'No eye found'); setStep('capture'); return; }
    if (a.quality?.verdict === 'good') { await process(img, a); } else { setStep('quality'); }
  };

  const process = async (img: HTMLImageElement, a: Analysis) => {
    setStep('processing'); setProgress(['Cutting out your iris']);
    const W = img.naturalWidth, H = img.naturalHeight;
    const { cx, cy, r } = a.iris!; const pad = a.pad || 1.12;
    const S = 2 * r * W * pad;
    const out = Math.min(1400, Math.round(S));
    const crop = drawToDataUrl(img, cx * W - S / 2, cy * H - S / 2, S, S, out, out, 0.95);
    setClientCrop(crop);
    try {
      setProgress((p) => [...p, 'Removing reflections']);
      const d = await post<{ crop: string; glare_pct: number; changed: boolean; used_sr: boolean }>('/api/deglare', { crop: stripDataUrl(crop), pad, ticket: a.ticket, pupil_r: a.pupil_r, glare_boxes: a.glare_boxes_crop || [] });
      const clean = `data:image/jpeg;base64,${d.crop}`; setCleanCrop(clean); setGlarePct(d.glare_pct);
      setProgress((p) => [...p, 'Restoring fibres faithfully (about 30 s)']);
      const e = await post<Enhanced>('/api/enhance', { crop: d.crop, mode: 'faithful', pad, ticket: a.ticket, session, consent, used_sr: d.used_sr, meta: a.quality });
      setResults({ faithful: e });
      setProgress((p) => [...p, 'Composing your artwork']);
      // the restoration is paid for by this point: a free composition failure must never send the user
      // back to a screen whose only button buys it again
      try {
        const c = await post<{ image: string }>('/api/compose', { iris: e.image, style, names, pad });
        setArtCache({ [`faithful:${style}:${names}`]: `data:image/jpeg;base64,${c.image}` });
      } catch { /* the effect below retries as soon as the user touches a style or a name */ }
      setStep('result');
    } catch (err) {
      setError((err as Error).message);
      setStep(results.faithful ? 'result' : 'quality');
    }
  };

  const ensureArtistic = async () => {
    if (results.artistic || !cleanCrop || !analysis) return;
    setComposing(true);
    try {
      const e = await post<Enhanced>('/api/enhance', { crop: stripDataUrl(cleanCrop), mode: 'artistic', pad: analysis.pad, ticket: analysis.ticket, session, consent, used_sr: true, meta: analysis.quality });
      setResults((r) => ({ ...r, artistic: e }));
    } catch (err) { setError((err as Error).message); setMode('faithful'); }
    setComposing(false);
  };

  // re-compose whenever mode / style / names change on the result screen
  useEffect(() => {
    if (step !== 'result') return;
    const res = results[mode];
    if (!res) return;
    const key = `${mode}:${style}:${names}`;
    if (artCache[key]) return;
    let cancelled = false;
    const t = setTimeout(async () => {
      setComposing(true);
      try {
        const c = await post<{ image: string }>('/api/compose', { iris: res.image, style, names, pad: analysis?.pad });
        if (!cancelled) setArtCache((a) => ({ ...a, [key]: `data:image/jpeg;base64,${c.image}` }));
      } catch (err) { if (!cancelled) setError((err as Error).message); }
      if (!cancelled) setComposing(false);
    }, names ? 500 : 0);
    return () => { cancelled = true; clearTimeout(t); };
  }, [step, mode, style, names, results, artCache, analysis]);

  const current = results[mode];
  // while the artistic version is still generating (or if it failed) keep showing the faithful one,
  // so the toggle, the style picker and the reset button never disappear from under the user
  const shown = current ?? results.faithful ?? results.artistic!;
  const artKey = `${mode}:${style}:${names}`;
  const artwork = artCache[artKey];

  return (
    <div className="min-h-screen bg-[#07090e] text-[#f0f3fa]">
      <header className="px-4 py-4 flex items-center justify-between max-w-3xl mx-auto">
        <a href="/" className="font-luxury font-black tracking-wider text-lg">SNAP<span className="text-gold-gradient">EYES</span></a>
        <span className="text-[10px] uppercase tracking-widest text-zinc-500">Real studio · beta</span>
      </header>

      <main className="max-w-3xl mx-auto px-4 pb-24">
        {error && (
          <div className="mb-4 bg-rose-950/40 border border-rose-500/40 text-rose-200 text-sm rounded-xl p-3 flex gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> <span>{error}</span>
          </div>
        )}

        {step === 'capture' && (
          <section className="flex flex-col gap-5">
            <div className="text-center mt-2">
              <h1 className="font-luxury text-3xl sm:text-4xl font-bold">YOUR EYE, <span className="text-gold-gradient">FOR REAL.</span></h1>
              <p className="text-zinc-400 text-sm mt-2">Photograph one eye. We find the iris, remove reflections, restore the fibres and place it in cosmic art. About a minute.</p>
            </div>

            <div className="bg-[#0b0e17] border border-white/10 rounded-2xl p-4 text-xs text-zinc-300 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div><span className="text-[#f5c542] font-bold block">1. Back camera</span>2x or 3x zoom, not the selfie camera.</div>
              <div><span className="text-[#f5c542] font-bold block">2. 10 cm away</span>The iris should fill a third of the frame.</div>
              <div><span className="text-[#f5c542] font-bold block">3. Light from the side</span>Window or lamp at 45°, never straight in.</div>
              <div><span className="text-[#f5c542] font-bold block">4. Tap to focus</span>Tap the iris on screen, hold still, shoot.</div>
            </div>

            <button onClick={() => fileRef.current?.click()} className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black font-luxury font-bold uppercase tracking-widest text-sm flex items-center justify-center gap-2 shadow-lg shadow-[#f5c542]/20 active:scale-[0.98]">
              <Camera className="w-5 h-5" /> Take a photo
            </button>
            <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} />

            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => galleryRef.current?.click()} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                <Upload className="w-4 h-4 text-[#f5c542]" /> From gallery
              </button>
              <input ref={galleryRef} type="file" accept="image/*" className="hidden" onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} />
              {!isIOS && 'mediaDevices' in navigator ? (
                <button onClick={() => setLiveOpen(true)} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                  <Video className="w-4 h-4 text-emerald-400" /> Live camera + zoom
                </button>
              ) : (
                <button onClick={async () => { const r = await fetch('/assets/sample_eye_blue_1789706902835.jpg'); onFile(await r.blob()); }} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                  <Sparkles className="w-4 h-4 text-[#f5c542]" /> Try a sample eye
                </button>
              )}
            </div>
            {!isIOS && 'mediaDevices' in navigator && (
              <button onClick={async () => { const r = await fetch('/assets/sample_eye_blue_1789706902835.jpg'); onFile(await r.blob()); }} className="text-xs text-zinc-400 underline underline-offset-4 self-center">
                or try with a sample eye
              </button>
            )}

            {storageOn && (
            <label className="flex items-start gap-3 text-xs text-zinc-400 bg-white/5 border border-white/5 rounded-xl p-3 cursor-pointer">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5 w-4 h-4" />
              <span>Save my eye photo and result to SnapEyes' training memory so restorations get better over time. Anonymous, no name or face. You can ask us to delete it any time.</span>
            </label>
            )}
          </section>
        )}

        {step === 'analyzing' && (
          <Working title="Finding your iris…" lines={['Locating the iris and pupil', 'Measuring size and sharpness']} elapsed={elapsed} />
        )}

        {step === 'quality' && analysis?.quality && (
          <section className="flex flex-col gap-4">
            <div className="grid grid-cols-[120px_1fr] gap-4 items-center bg-[#0b0e17] border border-white/10 rounded-2xl p-4">
              {analysis.preview && <img src={`data:image/jpeg;base64,${analysis.preview}`} alt="Detected iris" className="w-[120px] h-[120px] rounded-full border border-[#f5c542]/40 object-cover" />}
              <div>
                <Verdict v={analysis.quality.verdict} />
                <p className="text-sm text-zinc-200 mt-2">{analysis.quality.message}</p>
                <p className="text-[11px] text-zinc-500 mt-1 font-mono">iris {analysis.quality.diameter_px}px · sharpness {analysis.quality.sharpness}{analysis.quality.glare ? ' · reflection detected' : ''}</p>
              </div>
            </div>
            {analysis.quality.tips.length > 0 && (
              <ul className="text-xs text-zinc-300 bg-white/5 border border-white/10 rounded-xl p-3 space-y-1.5">
                {analysis.quality.tips.map((t) => <li key={t}>• {t}</li>)}
              </ul>
            )}
            <div className="grid grid-cols-2 gap-3">
              <button onClick={reset} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2"><RefreshCcw className="w-4 h-4" /> Retake</button>
              <button onClick={() => imgRef.current && process(imgRef.current, analysis)} className="py-3 rounded-xl bg-[#f5c542] text-black text-sm font-bold flex items-center justify-center gap-2"><Sparkles className="w-4 h-4" /> Continue anyway</button>
            </div>
          </section>
        )}

        {step === 'processing' && (
          <Working title="Restoring your iris…" lines={progress} elapsed={elapsed} image={clientCrop} />
        )}

        {step === 'result' && (results.faithful || results.artistic) && (
          <section className="flex flex-col gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-luxury text-xl font-bold">Before / after</h2>
                <FidelityBadge res={shown} mode={results[mode] ? mode : 'faithful'} />
              </div>
              <CompareSlider before={clientCrop || cleanCrop || ''} after={`data:image/jpeg;base64,${shown.image}`} beforeLabel="Your photo" afterLabel={results[mode] ? (mode === 'faithful' ? 'Restored' : 'Artistic') : 'Restored'} />
              <p className="text-[11px] text-zinc-500 mt-2">Drag the handle. {analysis?.quality ? `Iris in your photo: ${analysis.quality.diameter_px}px.` : ''} {glarePct >= 0.4 ? 'Reflection removed.' : ''} {shown.used_sr ? 'Small photo: faithful upscale applied before restoration.' : ''}</p>
            </div>

            <div className="grid grid-cols-2 gap-2 bg-white/5 border border-white/10 rounded-xl p-1">
              <button onClick={() => setMode('faithful')} className={`py-2 rounded-lg text-xs font-bold ${mode === 'faithful' ? 'bg-[#f5c542] text-black' : 'text-zinc-300'}`}>Faithful (your fibres)</button>
              <button onClick={() => { setMode('artistic'); ensureArtistic(); }} className={`py-2 rounded-lg text-xs font-bold ${mode === 'artistic' ? 'bg-[#f5c542] text-black' : 'text-zinc-300'}`}>Artistic (AI macro)</button>
            </div>
            {mode === 'artistic' && !results.artistic && (
              <p className="text-xs text-zinc-400 flex items-center gap-2"><span className="w-3 h-3 border-2 border-[#f5c542]/30 border-t-[#f5c542] rounded-full animate-spin" /> Generating the artistic version (about 15 s)…</p>
            )}

            {shown && (
              <div>
                <h2 className="font-luxury text-xl font-bold mb-2">Your artwork</h2>
                <div className="relative aspect-square w-full rounded-2xl overflow-hidden border border-white/10 bg-black">
                  {artwork ? <img src={artwork} alt="Artwork preview" className="w-full h-full object-cover" /> : <div className="absolute inset-0 flex items-center justify-center text-zinc-500 text-sm">Composing…</div>}
                  {composing && <div className="absolute top-3 right-3 w-5 h-5 border-2 border-[#f5c542]/30 border-t-[#f5c542] rounded-full animate-spin" />}
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-3">
                  {STYLES.map((s) => (
                    <button key={s.id} onClick={() => setStyle(s.id)} className={`rounded-lg overflow-hidden border text-left ${style === s.id ? 'border-[#f5c542] ring-2 ring-[#f5c542]' : 'border-white/10'}`}>
                      <img src={s.thumb} alt={s.name} className="w-full aspect-[16/11] object-cover" />
                      <span className="block text-[10px] font-bold px-1.5 py-1 truncate">{s.name}</span>
                    </button>
                  ))}
                </div>
                <input value={names} onChange={(e) => setNames(e.target.value)} placeholder="Names or inscription (optional)" className="mt-3 w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm placeholder-zinc-500 focus:outline-none focus:border-[#f5c542]" />
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <a href={artwork || '#'} download={`snapeyes-${style}.jpg`} className={`py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 ${artwork ? 'bg-[#f5c542] text-black' : 'bg-white/5 text-zinc-500 pointer-events-none'}`}><Download className="w-4 h-4" /> Save preview</a>
                  <button onClick={reset} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2"><RefreshCcw className="w-4 h-4" /> Another photo</button>
                </div>
                {shown.stored && <p className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1"><Check className="w-3 h-3" /> Saved to training memory</p>}
              </div>
            )}
          </section>
        )}
      </main>

      {liveOpen && <LiveCamera onClose={() => setLiveOpen(false)} onCapture={(b) => { setLiveOpen(false); onFile(b); }} />}
      {origUrl && step === 'result' && <span className="hidden">{origUrl}</span>}
    </div>
  );
};

const Verdict: React.FC<{ v: 'good' | 'ok' | 'weak' }> = ({ v }) => {
  const map = { good: ['Great photo', 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'], ok: ['Usable photo', 'bg-amber-500/15 text-amber-300 border-amber-500/40'], weak: ['Weak photo', 'bg-rose-500/15 text-rose-300 border-rose-500/40'] } as const;
  return <span className={`inline-block text-[11px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border ${map[v][1]}`}>{map[v][0]}</span>;
};

const FidelityBadge: React.FC<{ res: Enhanced; mode: Mode }> = ({ res, mode }) => {
  if (mode === 'artistic') return <span className="text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-purple-400/40 text-purple-200 bg-purple-500/10">AI interpretation</span>;
  if (res.fallback) return <span className="text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-amber-400/40 text-amber-200 bg-amber-500/10">Faithful upscale only</span>;
  const pct = Math.round(res.fidelity * 100);
  return <span className="text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-emerald-400/40 text-emerald-200 bg-emerald-500/10">Fidelity {pct}%</span>;
};

const Working: React.FC<{ title: string; lines: string[]; elapsed: number; image?: string | null }> = ({ title, lines, elapsed, image }) => (
  <section className="flex flex-col items-center gap-5 py-6 text-center">
    {image ? <img src={image} alt="Your iris" className="w-40 h-40 rounded-full object-cover border-2 border-[#f5c542]/40 shadow-[0_0_40px_rgba(245,197,66,0.25)] animate-pulse" /> : <div className="w-16 h-16 border-4 border-[#f5c542]/20 border-t-[#f5c542] rounded-full animate-spin" />}
    <h2 className="font-luxury text-xl font-bold">{title}</h2>
    <ul className="text-sm text-zinc-300 space-y-1.5">
      {lines.map((l, i) => (
        <li key={l} className="flex items-center gap-2 justify-center">
          {i < lines.length - 1 ? <Check className="w-4 h-4 text-emerald-400" /> : <span className="w-3.5 h-3.5 border-2 border-[#f5c542]/30 border-t-[#f5c542] rounded-full animate-spin" />}
          {l}
        </li>
      ))}
    </ul>
    <span className="text-[11px] font-mono text-zinc-500">{elapsed}s</span>
  </section>
);

/** Live camera with hardware zoom where the browser supports it (Android Chrome). Captures a full-resolution still. */
const LiveCamera: React.FC<{ onClose: () => void; onCapture: (b: Blob) => void }> = ({ onClose, onCapture }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [zoom, setZoom] = useState<{ min: number; max: number; step: number; value: number } | null>(null);
  const [sharp, setSharp] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' }, width: { ideal: 4096 }, height: { ideal: 3072 } }, audio: false });
        if (!alive) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        const track = stream.getVideoTracks()[0];
        const caps = (track.getCapabilities?.() || {}) as { zoom?: { min: number; max: number; step: number } };
        if (caps.zoom) {
          const value = Math.min(2, caps.zoom.max);
          await track.applyConstraints({ advanced: [{ zoom: value } as MediaTrackConstraintSet] });
          setZoom({ ...caps.zoom, value });
        }
      } catch (e) { setErr((e as Error).message || 'Camera not available'); }
    })();
    const id = setInterval(() => {
      const v = videoRef.current; if (!v || v.videoWidth === 0) return;
      const c = document.createElement('canvas'); const n = 160; c.width = n; c.height = n;
      const ctx = c.getContext('2d')!; const s = Math.min(v.videoWidth, v.videoHeight) * 0.35;
      ctx.drawImage(v, (v.videoWidth - s) / 2, (v.videoHeight - s) / 2, s, s, 0, 0, n, n);
      const d = ctx.getImageData(0, 0, n, n).data; let sum = 0, sq = 0, k = 0;
      for (let y = 1; y < n - 1; y++) for (let x = 1; x < n - 1; x++) {
        const i = (y * n + x) * 4; const g = (i2: number) => d[i2] * 0.299 + d[i2 + 1] * 0.587 + d[i2 + 2] * 0.114;
        const lap = -4 * g(i) + g(i - 4) + g(i + 4) + g(i - n * 4) + g(i + n * 4); sum += lap; sq += lap * lap; k++;
      }
      setSharp(Math.round(sq / k - (sum / k) ** 2));
    }, 500);
    return () => { alive = false; clearInterval(id); streamRef.current?.getTracks().forEach((t) => t.stop()); };
  }, []);

  const applyZoom = async (value: number) => {
    const track = streamRef.current?.getVideoTracks()[0]; if (!track || !zoom) return;
    try { await track.applyConstraints({ advanced: [{ zoom: value } as MediaTrackConstraintSet] }); setZoom({ ...zoom, value }); } catch { /* ignore */ }
  };

  const capture = async () => {
    const track = streamRef.current?.getVideoTracks()[0]; const v = videoRef.current; if (!track || !v) return;
    const IC = (window as unknown as { ImageCapture?: new (t: MediaStreamTrack) => { takePhoto: () => Promise<Blob> } }).ImageCapture;
    if (IC) { try { const blob = await new IC(track).takePhoto(); onCapture(blob); return; } catch { /* fall through */ } }
    const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight; c.getContext('2d')!.drawImage(v, 0, 0);
    c.toBlob((b) => b && onCapture(b), 'image/jpeg', 0.95);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      <div className="relative flex-1 overflow-hidden">
        <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <div className="w-[46%] aspect-square rounded-full border-2 border-[#f5c542]/80 shadow-[0_0_0_9999px_rgba(0,0,0,0.35)] flex items-end justify-center pb-2">
            <span className="text-[10px] font-mono bg-black/70 px-2 py-0.5 rounded text-white/80">fit your iris here</span>
          </div>
        </div>
        <div className="absolute top-4 left-4 right-4 flex items-center justify-between text-xs">
          <span className={`px-2.5 py-1 rounded-full font-bold ${sharp > 60 ? 'bg-emerald-500/80 text-black' : 'bg-black/70 text-amber-300'}`}>{sharp > 60 ? 'Sharp ✓' : 'Hold still / tap to focus'}</span>
          <button onClick={onClose} className="px-3 py-1 rounded-full bg-black/70 text-white">Close</button>
        </div>
        {err && <div className="absolute bottom-4 left-4 right-4 text-xs text-rose-200 bg-rose-950/70 rounded-xl p-3">{err}</div>}
      </div>
      <div className="bg-[#07090e] px-4 py-4 flex flex-col gap-3">
        {zoom ? (
          <label className="flex items-center gap-3 text-xs text-zinc-300"><ZoomIn className="w-4 h-4 text-[#f5c542]" /> Zoom {zoom.value.toFixed(1)}x
            <input type="range" min={zoom.min} max={zoom.max} step={zoom.step || 0.1} value={zoom.value} onChange={(e) => applyZoom(parseFloat(e.target.value))} className="flex-1" />
          </label>
        ) : (
          <p className="text-[11px] text-zinc-500">This browser does not expose camera zoom. Use "Take a photo" and pinch to 2x in your camera app instead.</p>
        )}
        <button onClick={capture} className="w-full py-4 rounded-2xl bg-[#f5c542] text-black font-luxury font-bold uppercase tracking-widest text-sm">Capture</button>
      </div>
    </div>
  );
};
