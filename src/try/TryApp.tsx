import React, { useEffect, useRef, useState } from 'react';
import { Camera, Upload, Sparkles, RefreshCcw, Video, Check, AlertTriangle, ZoomIn, Info, Lightbulb, ArrowLeft } from 'lucide-react';
import {
  type Analysis, type Quality, type Targets, targetsOf, detailOf, rawFibre, bestIndex, visibleTips, topTip, mapPool,
  autoContinue, fibreRatio, meterBand, PUPIL_NOTE, LAMP_FALLBACK,
} from './shots';
import {
  type Art, type ColourQa, type Eye, type Layout, type LightAnswer, type ShotOrigin, type StudyPayload,
  MAX_EYES, STUDY_PENDING_MAX, colourOff, composeSide, deviceInfo, effectiveLayout, outcomeOf, studyAnswered, studyBody, studyOn,
} from './multi';
import { T } from './copy';
import { ResultView, type StyleOption } from './ResultView';
import { StudyCard } from './StudyCard';

type Step = 'capture' | 'analyzing' | 'quality' | 'processing' | 'result';
type ShotSource = 'input' | 'live';

// Several photos are measured at once: each /api/analyze call is mostly waiting on the vision model, so
// three in flight cut the wait roughly threefold without piling a whole gallery onto the server at once.
const ANALYZE_CONCURRENCY = 3;

// Composed previews kept per set of eyes: enough to flip between styles and layouts without a new request.
const ART_CACHE_MAX = 12;

// The owner's capture study (?study=1): two questions after each analysed shot, sent with the next analyze.
const STUDY = typeof window !== 'undefined' && studyOn(window.location.search);

interface Enhanced { image: string; fidelity: number; used_sr: boolean; fallback: boolean; seconds: number; stored?: boolean; qa?: ColourQa | null }
interface ComposeReply { image: string; width: number; height: number; layout: string }

// accent = api/_lib/iris.py STYLES[id].accent. The picker draws each swatch from it around the customer's
// own iris: the old style_thumb_*.jpg showed a stock blue eye next to the customer's result.
const STYLES: StyleOption[] = [
  { id: 'celestial_gold', name: 'Celestial Gold', accent: [245, 197, 66] },
  { id: 'deep_nebula', name: 'Deep Nebula', accent: [129, 140, 248] },
  { id: 'emerald_aurora', name: 'Emerald Aurora', accent: [52, 211, 153] },
  { id: 'obsidian_smoke', name: 'Obsidian Smoke', accent: [203, 213, 225] },
  { id: 'supernova', name: 'Supernova', accent: [251, 146, 60] },
  { id: 'studio_black', name: 'Studio Black', accent: null },   // bare: no glow, no text
];

const SAMPLE_EYE = '/assets/sample_eye_blue_1789706902835.jpg';   // AI-generated: always labelled as such

// A user-agent test was hiding the live camera from every iPhone. WebKit has shipped zoom and torch for a
// while and ImageCapture landed in Safari 18.4, so ask the device instead of guessing from its name.
const hasCameraApi = typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia;
const hasStillCapture = typeof window !== 'undefined' && 'ImageCapture' in window;

/** POST JSON and return the reply. Throws with the server's own message on any failure, except that with
 *  answerNotOk a 2xx reply saying ok:false is returned: /api/analyze answers a photo with no eye in it that
 *  way, and the capture flow has its own branches for it. */
async function post<T>(path: string, body: unknown, answerNotOk = false): Promise<T> {
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
  if (!r.ok || (j.ok === false && !answerNotOk)) throw new Error(j.error || j.message || `Request failed (${r.status})`);
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

/** A 160 px copy of a restored iris for the eye chips. Never throws: the restoration it comes from is paid for. */
async function thumbOf(b64: string): Promise<string> {
  const full = `data:image/jpeg;base64,${b64}`;
  try {
    const img = await loadImage(full);
    return drawToDataUrl(img, 0, 0, img.naturalWidth, img.naturalHeight, 160, 160, 0.85);
  } catch { return full; }
}

let eyeSeq = 0;
const newEyeId = () => `e${Date.now().toString(36)}${(eyeSeq++).toString(36)}`;
const eyesPrefix = (list: Eye[]) => `${list.map((e) => e.id).join('.')}|`;
const artKeyOf = (list: Eye[], layout: Layout, style: string, names: string) => `${eyesPrefix(list)}${layout}|${style}|${names}`;

export const TryApp: React.FC = () => {
  const [step, setStep] = useState<Step>('capture');
  const [error, setError] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);
  const [storageOn, setStorageOn] = useState(false);
  const [session] = useState(() => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`);
  // ---- the eye being captured now
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [clientCrop, setClientCrop] = useState<string | null>(null);
  const [working, setWorking] = useState<{ eye: number; sample: boolean }>({ eye: 1, sample: false });
  // ---- the finished eyes, in canvas order. One restored iris each; the photos they came from are released.
  const [eyes, setEyes] = useState<Eye[]>([]);
  const eyesRef = useRef<Eye[]>([]);   // async steps read this, never a render's stale copy
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [layoutWant, setLayoutWant] = useState<Layout | null>(null);
  const [style, setStyle] = useState('celestial_gold');
  const [names, setNames] = useState('');
  const [artCache, setArtCache] = useState<Record<string, Art>>({});
  const [composeFail, setComposeFail] = useState<Record<string, string>>({});
  const inflightRef = useRef(new Set<string>());
  const sizedRef = useRef(new Map<string, string>());   // `${eyeId}:${side}` -> iris re-encoded for /api/compose
  const [progress, setProgress] = useState<string[]>([]);
  const [clock, setClock] = useState<{ step: Step | null; secs: number }>({ step: null, secs: 0 });
  const [liveOpen, setLiveOpen] = useState(false);
  // Camera shot collector: one analysis per camera shot (up to targets.max_shots). Only the best shot keeps
  // its full-size image; five 12 MP photos held at once is how a phone tab gets killed.
  const [shots, setShots] = useState<Analysis[]>([]);
  const [shotSource, setShotSource] = useState<ShotSource>('input');
  const [shotNote, setShotNote] = useState<string | null>(null);
  const shotsRef = useRef<Analysis[]>([]);
  const bestShotRef = useRef<{ img: HTMLImageElement; url: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const photoUrlRef = useRef<string | null>(null);
  // The site's own demo eye is a studio photo whose ring light covers part of the fibres, so on the glare
  // cap it reads 'ok', not 'good'. We know it restores well, so it is not parked on the quality screen.
  const sampleRef = useRef(false);
  // ---- capture study: the open question card, and the answers waiting for an analyze request the engine
  // logs. The engine writes them only with an analyze that found an eye, so answers stay here until one
  // such reply comes back. Held in the page only; nothing is written to the browser.
  const [studyAsk, setStudyAsk] = useState<StudyPayload | null>(null);
  const pendingStudyRef = useRef<StudyPayload[]>([]);
  const [pendingShots, setPendingShots] = useState<number[]>([]);   // for the "not sent yet" note
  const studyInflightRef = useRef(new Set<number>());               // shots whose answers ride on a request now
  const shotNoRef = useRef(0);
  // ---- retaking one eye of the artwork: its id, so the new restoration takes that eye's place
  const [replacing, setReplacingState] = useState<string | null>(null);
  const replacingRef = useRef<string | null>(null);
  // ---- the eye just removed, kept for a few seconds so one mistaken tap never throws a paid restoration away
  const [undo, setUndo] = useState<{ eye: Eye; index: number } | null>(null);

  // only offer the training-memory checkbox when this deployment can really store something
  useEffect(() => {
    let alive = true;
    fetch('/api/health')
      .then((r) => r.json())
      .then((h) => { if (alive) setStorageOn(!!h.blob_store); })
      .catch(() => { /* health is optional */ });
    return () => { alive = false; };
  }, []);

  // elapsed timer while the engine works. Counted per step and only set from the timer, so a new step
  // starts at 0 without a synchronous reset.
  useEffect(() => {
    if (step !== 'analyzing' && step !== 'processing') return;
    const t0 = Date.now();
    const id = setInterval(() => setClock({ step, secs: Math.round((Date.now() - t0) / 1000) }), 1000);
    return () => { clearInterval(id); setClock({ step: null, secs: 0 }); };
  }, [step]);
  const elapsed = clock.step === step ? clock.secs : 0;

  // a fully answered study card says thank you, then gets out of the way (the answers stay pending)
  useEffect(() => {
    if (!studyAsk || studyAsk.light === null || studyAsk.comfort === null) return;
    const id = setTimeout(() => setStudyAsk(null), 2500);
    return () => clearTimeout(id);
  }, [studyAsk]);

  // the Undo offer for a removed eye lasts a few seconds
  useEffect(() => {
    if (!undo) return;
    const id = setTimeout(() => setUndo(null), 8000);
    return () => clearTimeout(id);
  }, [undo]);

  const clearShots = () => {
    if (bestShotRef.current) URL.revokeObjectURL(bestShotRef.current.url);
    bestShotRef.current = null; shotsRef.current = []; setShots([]); setShotNote(null);
  };

  const setPhoto = (img: HTMLImageElement, url: string) => {
    if (photoUrlRef.current && photoUrlRef.current !== url) URL.revokeObjectURL(photoUrlRef.current);
    photoUrlRef.current = url; imgRef.current = img;
  };

  /** Let go of every full-size photo of the eye being captured. */
  const releasePhoto = () => {
    clearShots();
    if (photoUrlRef.current) URL.revokeObjectURL(photoUrlRef.current);
    photoUrlRef.current = null; imgRef.current = null;
  };

  /** Forget the eye being captured. The finished eyes stay. */
  const clearCapture = () => {
    releasePhoto();
    setError(null); setAnalysis(null); setClientCrop(null); setProgress([]);
    sampleRef.current = false;
  };

  const commitEyes = (next: Eye[]) => {
    eyesRef.current = next; setEyes(next);
    const ids = new Set(next.map((e) => e.id));
    for (const k of [...sizedRef.current.keys()]) if (!ids.has(k.split(':')[0])) sizedRef.current.delete(k);
    // a preview of another set of eyes is never shown again
    const prefix = eyesPrefix(next);
    setArtCache((c) => Object.fromEntries(Object.entries(c).filter(([k]) => k.startsWith(prefix))));
    setComposeFail({});
  };

  const toTop = () => { try { window.scrollTo({ top: 0 }); } catch { /* old browsers */ } };

  const setReplacing = (id: string | null) => { replacingRef.current = id; setReplacingState(id); };

  /** Where the eye being captured goes on the artwork, 0-based: the place of the eye being retaken, or
   *  the end for a new eye. */
  const capturePos = () => {
    const r = replacingRef.current;
    const i = r ? eyesRef.current.findIndex((e) => e.id === r) : -1;
    return i >= 0 ? i : eyesRef.current.length;
  };

  /** Retake the eye being captured: back to the capture screen, the finished eyes untouched. */
  const retake = () => { clearCapture(); setStep('capture'); };

  const backToArtwork = () => { clearCapture(); setReplacing(null); setStep('result'); toTop(); };

  const addEye = () => {
    if (eyesRef.current.length >= MAX_EYES) return;
    clearCapture(); setReplacing(null); setUndo(null); setStep('capture'); toTop();
  };

  /** Photograph one eye of the artwork again. Nothing changes until the new eye is restored. */
  const retakeEye = (id: string) => {
    if (!eyesRef.current.some((e) => e.id === id)) return;
    clearCapture(); setReplacing(id); setUndo(null); setStep('capture'); toTop();
  };

  const startOver = () => {
    const n = eyesRef.current.length;
    if (n > 1 && !window.confirm(T.result.confirmStartOver(n))) return;
    clearCapture(); commitEyes([]); setSelectedId(null); setLayoutWant(null); setArtCache({});
    setReplacing(null); setUndo(null);
    sizedRef.current.clear(); setStep('capture'); toTop();
  };

  const removeEye = (id: string) => {
    const list = eyesRef.current;
    const index = list.findIndex((e) => e.id === id);
    if (index < 0) return;
    const next = list.filter((e) => e.id !== id);
    if (!next.length) { startOver(); return; }
    commitEyes(next);
    setSelectedId(next[Math.min(index, next.length - 1)].id);
    setUndo({ eye: list[index], index });
  };

  const undoRemove = () => {
    const u = undo;
    setUndo(null);
    const list = eyesRef.current;
    if (!u || list.length >= MAX_EYES || list.some((e) => e.id === u.eye.id)) return;
    commitEyes([...list.slice(0, u.index), u.eye, ...list.slice(u.index)]);
    setSelectedId(u.eye.id);
  };

  // ---- capture study
  const setPending = (list: StudyPayload[]) => {
    pendingStudyRef.current = list.slice(-STUDY_PENDING_MAX);
    setPendingShots(pendingStudyRef.current.filter(studyAnswered).map((s) => s.shot));
  };
  /** The two questions about the shot (or gallery pick) just measured, whatever the engine made of it: the
   *  shots it could not use are the ones the study most needs to hear about. */
  const askStudy = (source: ShotOrigin, photos: number, outcome: string) => {
    if (!STUDY || source === 'sample' || photos < 1) return;
    setStudyAsk({ session, eye: capturePos() + 1, shot: shotNoRef.current, photos, source, outcome, light: null, comfort: null });
  };
  const answerStudy = (patch: { light?: LightAnswer; comfort?: number }) => {
    if (!studyAsk) return;
    const next = { ...studyAsk, ...patch };
    setPending([...pendingStudyRef.current.filter((s) => s.shot !== next.shot), next]);
    setStudyAsk(next);
  };
  const skipStudy = () => {
    const shot = studyAsk?.shot;
    setPending(pendingStudyRef.current.filter((s) => s.shot !== shot));
    setStudyAsk(null);
  };

  const onFile = async (file: File | Blob, isSample = false) => {
    sampleRef.current = isSample;
    setError(null); setProgress([]); clearShots();
    const url = URL.createObjectURL(file);
    try {
      const img = await loadImage(url);
      setPhoto(img, url);
      await analyze(img, isSample ? 'sample' : 'gallery');
    } catch (e) {
      if (photoUrlRef.current !== url) URL.revokeObjectURL(url);   // an unreadable file never became the photo
      setError((e as Error).message); setStep('capture');
    }
  };

  /** Several shots of the same eye are never equally good. On four real photos of one eye the sharpest
   *  carried 3.7x the fibre detail of the softest, and the largest iris of the four was the softest - so
   *  the customer cannot pick by eye and neither can a size rule. Measure each and use the best. */
  const onFiles = async (files: File[]) => {
    if (files.length === 1) return onFile(files[0]);
    sampleRef.current = false;
    setError(null); setStep('analyzing'); clearShots();
    // several run at once, so "photo 3 of 5" would be a lie: count the ones that are finished
    let done = 0, sent = 0;
    const tick = () => setProgress([`Checking ${files.length} photos: ${done} of ${files.length} done`]);
    tick();
    const measured = await mapPool(files, ANALYZE_CONCURRENCY, async (file) => {
      const url = URL.createObjectURL(file);
      try {
        const img = await loadImage(url);
        sent++;
        const a = await measure(img, 'gallery');
        if (a.ok && a.iris) return { img, url, a };
      } catch { /* an unreadable file just does not compete */ }
      finally { done++; tick(); }
      URL.revokeObjectURL(url);
      return null;
    });
    // mapPool keeps input order, so i is the photo's position in the customer's own selection
    const scored = measured.flatMap((m, i) => (m ? [{ ...m, i }] : []));
    const win = scored.length ? scored[bestIndex(scored.map((s) => s.a))] : null;
    askStudy('gallery', sent, win ? outcomeOf(win.a) : 'no_eye');
    if (!win) {
      setError('We could not find an eye in any of those photos.'); setStep('capture'); return;
    }
    scored.forEach((s) => { if (s !== win) URL.revokeObjectURL(s.url); });
    const chosen: Analysis = {
      ...win.a,
      picked: { used: win.i + 1, of: files.length, fibre: rawFibre(win.a), worst: Math.min(...scored.map((s) => rawFibre(s.a))) },
    };
    setPhoto(win.img, win.url); setAnalysis(chosen); setProgress([]);
    if (autoContinue(chosen)) { await process(win.img, chosen); } else { setStep('quality'); }
  };

  /** One photo from the camera (the capture input or the live camera). Measured at once and kept if it is
   *  the best so far, so the customer can shoot, see the score, and shoot again until one is good. */
  const onCameraShot = async (file: Blob, source: ShotSource) => {
    sampleRef.current = false;
    setError(null); setShotNote(null); setShotSource(source);
    const t = targetsOf(analysis);
    const prev = shotsRef.current;
    // a shot that fails keeps the collection alive when there is one, and falls back to the old error otherwise
    const fail = (msg: string) => {
      if (!prev.length) { setError(msg); setStep('capture'); return; }
      setShotNote(msg); setStep('quality');
    };
    if (prev.length >= t.max_shots) { setStep('quality'); return; }
    setStep('analyzing'); setProgress([`Measuring shot ${prev.length + 1} of ${t.max_shots}`]);
    const url = URL.createObjectURL(file);
    const origin: ShotOrigin = source === 'live' ? 'live' : 'camera';
    let img: HTMLImageElement; let a: Analysis;
    try {
      img = await loadImage(url);
      a = await measure(img, origin);
    } catch (e) { URL.revokeObjectURL(url); fail((e as Error).message); return; }
    // measure() hands back a no-eye reply instead of throwing, so this shot gets its questions too
    askStudy(origin, 1, outcomeOf(a));
    if (!a.ok || !a.iris) { URL.revokeObjectURL(url); fail(a.message || 'We could not find an eye in that shot.'); return; }
    const next = [...prev, a];
    const bi = bestIndex(next);
    if (bi === next.length - 1) {
      if (bestShotRef.current) URL.revokeObjectURL(bestShotRef.current.url);
      bestShotRef.current = { img, url };
    } else {
      URL.revokeObjectURL(url);
    }
    const best = bestShotRef.current;
    if (!best) { fail('Something went wrong keeping your shots. Please take the photo again.'); return; }
    shotsRef.current = next; setShots(next); setProgress([]);
    const chosen = next[bi];
    setPhoto(best.img, best.url); setAnalysis(chosen);
    // go on by itself only when the shot that will be processed is good and lamp-free. Asking this of the
    // latest shot instead once sent an earlier 'weak' shot (sharp, but glared) to the studio unseen.
    if (autoContinue(chosen)) { await process(best.img, chosen); return; }
    setStep('quality');
  };

  const takeAnother = () => {
    setError(null);
    if (shotSource === 'live' && hasCameraApi) setLiveOpen(true); else fileRef.current?.click();
  };

  /** /api/analyze for one photo. Always says what kind of device and source it came from. In study mode every
   *  answer that no logged analyze has carried yet rides along; the engine logs only a reply that found an
   *  eye, so the answers are dropped here only after such a reply (a no-eye shot or a failed request keeps
   *  them for the next photo). A no-eye reply is returned, not thrown. */
  const measure = async (img: HTMLImageElement, source: ShotOrigin): Promise<Analysis> => {
    const W = img.naturalWidth, H = img.naturalHeight;
    const f = Math.min(1, 1600 / Math.max(W, H));
    const small = drawToDataUrl(img, 0, 0, W, H, Math.round(W * f), Math.round(H * f), 0.9);
    const body: Record<string, unknown> = { image: stripDataUrl(small), origWidth: W, origHeight: H, device: deviceInfo(source) };
    // photos of one gallery pick are measured side by side: each answer rides on one request at a time
    const sending = pendingStudyRef.current.filter((s) => studyAnswered(s) && !studyInflightRef.current.has(s.shot));
    const study = studyBody(sending);
    if (study) body.study = study;
    sending.forEach((s) => studyInflightRef.current.add(s.shot));
    if (STUDY) setStudyAsk(null);
    shotNoRef.current += 1;
    try {
      const a = await post<Analysis>('/api/analyze', body, true);
      if (a.ok && sending.length) {
        const sent = new Set(sending.map((s) => s.shot));
        setPending(pendingStudyRef.current.filter((s) => !sent.has(s.shot)));
      }
      return a;
    } finally {
      sending.forEach((s) => studyInflightRef.current.delete(s.shot));
    }
  };

  const analyze = async (img: HTMLImageElement, source: ShotOrigin) => {
    setStep('analyzing');
    const a = await measure(img, source);
    askStudy(source, 1, outcomeOf(a));
    if (!a.ok || !a.iris) { setError(a.message || 'No eye found'); setStep('capture'); return; }
    setAnalysis(a);
    const sampleOk = sampleRef.current && a.quality?.verdict !== 'weak' && a.quality?.locked !== false;
    if (autoContinue(a) || sampleOk) { await process(img, a); } else { setStep('quality'); }
  };

  /** The iris re-encoded at the side /api/compose needs for this many eyes (cached per eye). */
  const sizedIris = async (e: Eye, side: number | null): Promise<string> => {
    if (!side) return e.image;
    const k = `${e.id}:${side}`;
    const hit = sizedRef.current.get(k);
    if (hit) return hit;
    const img = await loadImage(`data:image/jpeg;base64,${e.image}`);
    const s = Math.min(side, img.naturalWidth, img.naturalHeight);
    const b64 = stripDataUrl(drawToDataUrl(img, 0, 0, img.naturalWidth, img.naturalHeight, s, s, 0.9));
    sizedRef.current.set(k, b64);
    return b64;
  };

  /** One preview of these eyes. The watermark is the server's business: no unlock ticket is ever sent. */
  const composeArt = async (list: Eye[], layout: Layout, st: string, nm: string): Promise<Art> => {
    const irises = await Promise.all(list.map((e) => sizedIris(e, composeSide(list.length))));
    const body: Record<string, unknown> = { irises, style: st, names: nm, pad: list[0].pad };
    if (list.length > 1) body.layout = layout;
    // the sample eye's label goes into the picture itself (the caption title), so a saved preview keeps it
    if (list.some((e) => e.sample)) body.title = T.result.sampleTitle;
    const c = await post<ComposeReply>('/api/compose', body);
    return { src: `data:image/jpeg;base64,${c.image}`, w: c.width, h: c.height, layout: c.layout };
  };

  const cacheArt = (key: string, art: Art) => setArtCache((c) => {
    // an answer for eyes that were removed or added meanwhile is dropped
    if (!key.startsWith(eyesPrefix(eyesRef.current))) return c;
    const entries = Object.entries({ ...c, [key]: art });
    return Object.fromEntries(entries.slice(-ART_CACHE_MAX));
  });

  const process = async (img: HTMLImageElement, a: Analysis) => {
    // A crop that is not centred on an iris must never reach the studio: from a crop of eyelid skin the image
    // model invented a complete brown iris, and nothing downstream can tell. The server issues no work
    // ticket for it either; this stops the button before the customer waits for an error.
    if (a.quality?.locked === false) {
      setError(T.quality.notCentred);
      setStep('quality'); return;
    }
    const replaceId = replacingRef.current && eyesRef.current.some((x) => x.id === replacingRef.current) ? replacingRef.current : null;
    const eyeNo = capturePos() + 1;
    if (!replaceId && eyeNo > MAX_EYES) { backToArtwork(); return; }
    const sample = sampleRef.current;
    // The eye's own id names its storage folder. A count (eyes + 1) repeats after a removal, and the new eye
    // then overwrote the training-memory files of an eye still on the artwork.
    const id = newEyeId();
    setError(null); setWorking({ eye: eyeNo, sample });
    setStep('processing'); setProgress([T.working.cut]);
    const W = img.naturalWidth, H = img.naturalHeight;
    const { cx, cy, r } = a.iris!; const pad = a.pad || 1.12;
    const S = 2 * r * W * pad;
    const out = Math.min(1400, Math.round(S));
    const crop = drawToDataUrl(img, cx * W - S / 2, cy * H - S / 2, S, S, out, out, 0.95);
    setClientCrop(crop);
    let d: { crop: string; glare_pct: number; changed: boolean; used_sr: boolean };
    let e: Enhanced;
    try {
      setProgress((p) => [...p, T.working.reflections]);
      d = await post('/api/deglare', { crop: stripDataUrl(crop), pad, ticket: a.ticket, pupil_r: a.pupil_r, glare_boxes: a.glare_boxes_crop || [] });
      setProgress((p) => [...p, T.working.macro]);
      // each eye has its own storage folder, or one eye would overwrite another one's files
      e = await post<Enhanced>('/api/enhance', { crop: d.crop, mode: 'artistic', pad, ticket: a.ticket, session: `${session}-${id}`, consent, used_sr: d.used_sr, meta: a.quality });
    } catch (err) {
      // the photo is still held, so "Continue anyway" / "Use this shot" can run it again
      setError((err as Error).message);
      setStep('quality');
      return;
    }
    // The restoration is paid for by this point. The eye joins the artwork before anything else can fail,
    // and a free composition failure must never send the customer back to a screen that buys it again.
    const eye: Eye = {
      id, before: crop, image: e.image, thumb: await thumbOf(e.image), pad,
      fallback: !!e.fallback, usedSr: !!e.used_sr, stored: !!e.stored, glarePct: d.glare_pct,
      diameterPx: a.quality?.diameter_px, sample, colourOff: colourOff(e.qa),
    };
    // a retaken eye takes the old one's place; the old restoration goes only now that the new one exists
    const cur = eyesRef.current;
    const list = replaceId && cur.some((x) => x.id === replaceId)
      ? cur.map((x) => (x.id === replaceId ? eye : x))
      : [...cur, eye];
    setReplacing(null);
    commitEyes(list); setSelectedId(eye.id);
    releasePhoto(); sampleRef.current = false;
    setProgress((p) => [...p, T.working.composing(list.length)]);
    const lay = effectiveLayout(list.length, layoutWant);
    try {
      cacheArt(artKeyOf(list, lay, style, names), await composeArt(list, lay, style, names));
    } catch { /* the effect below retries once on the result screen, then offers "Try again" */ }
    setAnalysis(null); setClientCrop(null);
    setStep('result'); toTop();
  };

  // ---- the result screen composes whenever the eyes, the layout, the style or the names change
  const layout = effectiveLayout(eyes.length, layoutWant);
  const artKey = artKeyOf(eyes, layout, style, names);
  const art = artCache[artKey];
  const staleArt = art ?? Object.values(artCache).at(-1);

  useEffect(() => {
    if (step !== 'result' || !eyes.length) return;
    if (artCache[artKey] || composeFail[artKey] !== undefined || inflightRef.current.has(artKey)) return;
    const list = eyes, l = layout, st = style, nm = names, key = artKey;
    const t = setTimeout(async () => {
      inflightRef.current.add(key);
      try {
        cacheArt(key, await composeArt(list, l, st, nm));
      } catch (err) {
        setComposeFail((f) => ({ ...f, [key]: (err as Error).message }));
      } finally {
        inflightRef.current.delete(key);
      }
    }, names ? 500 : 0);
    return () => clearTimeout(t);
    // composeArt and cacheArt are left out on purpose: they read only refs and their own arguments
  }, [step, eyes, layout, style, names, artKey, artCache, composeFail]);

  const retryCompose = () => setComposeFail((f) => { const n = { ...f }; delete n[artKey]; return n; });

  const adding = eyes.length > 0;   // the capture screens are for eye n + 1 of an artwork that already exists
  const replaceNo = replacing ? eyes.findIndex((e) => e.id === replacing) + 1 : 0;   // 0: not retaking an eye
  // The AI-generated sample is a demo for someone without a photo at hand. It is never offered once a real
  // eye is on the artwork, so it cannot slip into a real couple's artwork, nor as a "retake" of an eye.
  const offerSample = !replaceNo && !eyes.some((e) => !e.sample);
  const backLink = adding && (
    <button onClick={backToArtwork} className="text-xs text-zinc-400 underline underline-offset-4 self-center flex items-center gap-1">
      <ArrowLeft className="w-3 h-3" /> {T.capture.back(eyes.length)}
    </button>
  );
  const trySample = async () => {
    try {
      const r = await fetch(SAMPLE_EYE);
      if (!r.ok) throw new Error(T.capture.sampleLoadFailed);
      await onFile(await r.blob(), true);
    } catch (e) { setError((e as Error).message); }
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-[#f0f3fa]">
      <header className="px-4 py-4 flex items-center justify-between max-w-3xl mx-auto">
        <a href="/" className="font-luxury font-black tracking-wider text-lg">SNAP<span className="text-gold-gradient">EYES</span></a>
        <span className="text-[10px] uppercase tracking-widest text-zinc-500 flex items-center gap-2">
          {STUDY && <span className="text-sky-300 border border-sky-400/40 rounded-full px-2 py-0.5">{T.header.study}</span>}
          {T.header.tag}
        </span>
      </header>

      <main className="max-w-3xl mx-auto px-4 pb-24">
        {error && (
          <div className="mb-4 bg-rose-950/40 border border-rose-500/40 text-rose-200 text-sm rounded-xl p-3 flex gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> <span>{error}</span>
          </div>
        )}

        {studyAsk && (
          <StudyCard ask={studyAsk} onLight={(light) => answerStudy({ light })} onComfort={(comfort) => answerStudy({ comfort })} onSkip={skipStudy} />
        )}

        {/* Both pickers live outside the capture screen so "Take another" can reopen the camera from the
            shot collector. The value is cleared after every pick so the same file can be chosen again. */}
        <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) onCameraShot(f, 'input'); }} />
        <input ref={galleryRef} type="file" accept="image/*" multiple className="hidden"
          onChange={(e) => { const fs = Array.from(e.target.files || []); e.target.value = ''; if (fs.length) onFiles(fs); }} />

        {step === 'capture' && (
          <section className="flex flex-col gap-5">
            {adding ? (
              <div className="text-center mt-2">
                <h1 className="font-luxury text-3xl sm:text-4xl font-bold">{(replaceNo ? T.capture.retakeTitle(replaceNo) : T.capture.addTitle(eyes.length + 1)).toUpperCase()}</h1>
                <p className="text-zinc-400 text-sm mt-2">{replaceNo ? T.capture.retakeLead : T.capture.addLead}</p>
                <div className="flex flex-wrap justify-center gap-x-2 gap-y-1 mt-3">
                  {eyes.map((e, i) => (
                    <span key={e.id} className="flex flex-col items-center gap-0.5 w-16">
                      <img src={e.thumb} alt="" className={`w-9 h-9 rounded-full object-cover ${e.id === replacing ? 'border-2 border-dashed border-[#f5c542]/70 opacity-50' : 'border border-[#f5c542]/40'}`} />
                      <span className={`text-[8px] leading-tight text-center ${e.sample ? 'font-semibold text-amber-200/90' : 'text-zinc-500'}`}>
                        {e.sample ? T.capture.sampleThumb : T.capture.thumbLabel(i + 1)}
                      </span>
                    </span>
                  ))}
                  {!replaceNo && <span className="w-9 h-9 rounded-full border-2 border-dashed border-[#f5c542]/60" aria-hidden />}
                </div>
                <p className="text-xs text-[#f5c542]/90 bg-[#f5c542]/5 border border-[#f5c542]/20 rounded-xl px-3 py-2 mt-3">{T.capture.takeTurns}</p>
              </div>
            ) : (
              <div className="text-center mt-2">
                <h1 className="font-luxury text-3xl sm:text-4xl font-bold">YOUR EYE, <span className="text-gold-gradient">FOR REAL.</span></h1>
                <p className="text-zinc-400 text-sm mt-2">{T.capture.lead}</p>
              </div>
            )}

            <div className="bg-[#0b0e17] border border-white/10 rounded-2xl p-4 text-xs text-zinc-300 grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div><span className="text-[#f5c542] font-bold block">1. Back camera</span>2x or 3x zoom, not the selfie camera.</div>
              <div><span className="text-[#f5c542] font-bold block">2. 10 cm away</span>The iris should fill a third of the frame.</div>
              <div><span className="text-[#f5c542] font-bold block">3. Light from the side</span>Window or lamp at 45°, never straight in.</div>
              <div><span className="text-[#f5c542] font-bold block">4. Tap to focus</span>Tap the iris on screen, hold still, shoot.</div>
              <div className="col-span-2 sm:col-span-4 pt-1 border-t border-white/10"><span className="text-[#f5c542] font-bold">Take 3-5 shots and send them all.</span> Move the light a little between shots. We measure every one and use the sharpest; on a real test the best shot had 3.7x the detail of the worst.</div>
              {!adding && <div className="col-span-2 sm:col-span-4 text-zinc-400">{T.capture.helper}</div>}
            </div>

            {/* the first camera shot starts a fresh collection */}
            <button onClick={() => { clearShots(); fileRef.current?.click(); }} className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black font-luxury font-bold uppercase tracking-widest text-sm flex items-center justify-center gap-2 shadow-lg shadow-[#f5c542]/20 active:scale-[0.98]">
              <Camera className="w-5 h-5" /> Take a photo
            </button>

            <div className={`grid gap-3 ${hasCameraApi || offerSample ? 'grid-cols-2' : 'grid-cols-1'}`}>
              <button onClick={() => galleryRef.current?.click()} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                <Upload className="w-4 h-4 text-[#f5c542]" /> Pick 3-5 shots
              </button>
              {hasCameraApi ? (
                <button onClick={() => { clearShots(); setLiveOpen(true); }} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                  <Video className="w-4 h-4 text-emerald-400" /> Live camera + zoom
                </button>
              ) : offerSample ? (
                <button onClick={trySample} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                  <Sparkles className="w-4 h-4 text-[#f5c542]" /> {T.capture.sampleButton}
                </button>
              ) : null}
            </div>
            {hasCameraApi && offerSample && (
              <button onClick={trySample} className="text-xs text-zinc-400 underline underline-offset-4 self-center">
                {T.capture.sampleLink}
              </button>
            )}

            {storageOn && (
            <label className="flex items-start gap-3 text-xs text-zinc-400 bg-white/5 border border-white/5 rounded-xl p-3 cursor-pointer">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5 w-4 h-4" />
              <span>Save my eye photo and result to SnapEyes' training memory so restorations get better over time. Anonymous, no name or face. You can ask us to delete it any time.</span>
            </label>
            )}
            {backLink}
          </section>
        )}

        {step === 'analyzing' && (
          <Working title="Finding your iris…" lines={progress.length ? progress : ['Locating the iris and pupil', 'Measuring size and sharpness']} elapsed={elapsed} />
        )}

        {step === 'quality' && analysis?.quality && shots.length > 0 && (
          <>
            <ShotCollector shots={shots} t={targetsOf(analysis)} note={shotNote} onTakeAnother={takeAnother}
              canUse={analysis.quality.locked !== false}
              onContinue={() => imgRef.current && process(imgRef.current, analysis)} onStartOver={retake} />
            {backLink && <div className="flex justify-center mt-4">{backLink}</div>}
          </>
        )}

        {step === 'quality' && analysis?.quality && shots.length === 0 && (
          <section className="flex flex-col gap-4">
            <div className="grid grid-cols-[120px_1fr] gap-4 items-center bg-[#0b0e17] border border-white/10 rounded-2xl p-4">
              {analysis.preview && <img src={`data:image/jpeg;base64,${analysis.preview}`} alt="Detected iris" className="w-[120px] h-[120px] rounded-full border border-[#f5c542]/40 object-cover" />}
              <div className="min-w-0">
                <Verdict v={analysis.quality.verdict} />
                <p className="text-sm text-zinc-200 mt-2">{analysis.quality.message}</p>
                <DetailMeter a={analysis} t={targetsOf(analysis)} />
              </div>
            </div>
            {analysis.picked && (
              <p className="text-xs text-emerald-300/90 bg-emerald-950/25 border border-emerald-500/30 rounded-xl p-3">
                {/* "best", not "sharpest": the verdict ranks first, so a glared photo can be sharper and still lose */}
                We compared {analysis.picked.of} photos and used the best one (photo {analysis.picked.used}).
                {fibreRatio(analysis.picked) !== null &&
                  ` It carries ${fibreRatio(analysis.picked)!.toFixed(1)}x the fibre detail of the softest.`}
              </p>
            )}
            <ShotNotes q={analysis.quality} onRetake={retake} />
            {visibleTips(analysis.quality).length > 0 && (
              <ul className="text-xs text-zinc-300 bg-white/5 border border-white/10 rounded-xl p-3 space-y-1.5">
                {visibleTips(analysis.quality).map((t) => <li key={t}>• {t}</li>)}
              </ul>
            )}
            <div className={`grid gap-3 ${analysis.quality.locked !== false ? 'grid-cols-2' : 'grid-cols-1'}`}>
              <button onClick={retake} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2"><RefreshCcw className="w-4 h-4" /> {T.quality.retake}</button>
              {/* no way forward from a crop that is not an iris: the studio would invent one */}
              {analysis.quality.locked !== false && (
                <button onClick={() => imgRef.current && process(imgRef.current, analysis)} className="py-3 rounded-xl bg-[#f5c542] text-black text-sm font-bold flex items-center justify-center gap-2"><Sparkles className="w-4 h-4" /> {T.quality.continueAnyway}</button>
              )}
            </div>
            {backLink}
          </section>
        )}

        {step === 'processing' && (
          <Working title={working.eye > 1 ? T.working.restoringEye(working.eye) : T.working.restoring} lines={progress} elapsed={elapsed} image={clientCrop}
            caption={working.sample ? T.working.sampleCaption : undefined}
            note={analysis?.quality?.pupil_reflection ? PUPIL_NOTE : undefined} />
        )}

        {step === 'result' && STUDY && !studyAsk && pendingShots.length > 0 && (
          <p data-testid="study-pending" className="mb-4 text-xs text-sky-200 bg-sky-950/30 border border-sky-400/30 rounded-xl p-3">
            {T.study.pending(pendingShots)}
          </p>
        )}

        {step === 'result' && eyes.length > 0 && (
          <ResultView
            eyes={eyes} selectedId={selectedId} onSelect={setSelectedId} onRemove={removeEye} onRetake={retakeEye} onAdd={addEye}
            art={art} staleArt={staleArt} composeError={composeFail[artKey] ?? null} onRetryCompose={retryCompose}
            layout={layout} onLayout={setLayoutWant}
            styles={STYLES} style={style} onStyle={setStyle} names={names} onNames={setNames}
            onStartOver={startOver} />
        )}
      </main>

      {step === 'result' && undo && (
        <div role="status" className="fixed bottom-4 inset-x-4 z-40 mx-auto max-w-sm bg-zinc-900 border border-white/15 rounded-xl pl-4 pr-1 flex items-center justify-between gap-3 text-sm text-zinc-100 shadow-lg shadow-black/50">
          <span>{T.result.removed(undo.index + 1)}</span>
          <button onClick={undoRemove} className="min-h-[44px] min-w-[44px] px-3 font-bold text-[#f5c542] underline underline-offset-4">{T.result.undo}</button>
        </div>
      )}

      {liveOpen && <LiveCamera onClose={() => setLiveOpen(false)} onCapture={(b) => { setLiveOpen(false); onCameraShot(b, 'live'); }} />}
    </div>
  );
};

const Verdict: React.FC<{ v: 'good' | 'ok' | 'weak' }> = ({ v }) => {
  const map = { good: ['Great photo', 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'], ok: ['Usable photo', 'bg-amber-500/15 text-amber-300 border-amber-500/40'], weak: ['Weak photo', 'bg-rose-500/15 text-rose-300 border-rose-500/40'] } as const;
  return <span className={`inline-block text-[11px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border ${map[v][1]}`}>{map[v][0]}</span>;
};

/** Detail N/100 with the ok and good targets marked, so the customer sees how far a retake has to go.
 *  Renders nothing against an older server that sends no score: the verdict badge still speaks there. */
const DetailMeter: React.FC<{ a: Analysis; t: Targets; label?: boolean }> = ({ a, t, label = true }) => {
  const d = detailOf(a);
  if (d === undefined) return null;
  const { band, caption } = meterBand(d, a.quality, t);
  const [text, bar] = { good: ['text-emerald-300', 'bg-emerald-400'], ok: ['text-amber-300', 'bg-amber-400'], low: ['text-rose-300', 'bg-rose-400'] }[band];
  return (
    <div className="mt-3" role="meter" aria-label="Detail" aria-valuemin={0} aria-valuemax={100} aria-valuenow={d}>
      <div className="flex items-baseline justify-between gap-2 text-xs">
        {label ? <span className="font-bold text-zinc-200">Detail <span className={text}>{d}</span><span className="text-zinc-500">/100</span></span> : <span />}
        {caption && <span className="text-[10px] text-zinc-500">{caption}</span>}
      </div>
      <div className="relative h-2 mt-1.5 rounded-full bg-white/10 overflow-hidden">
        <div className={`h-full rounded-full ${bar}`} style={{ width: `${Math.max(d, 2)}%` }} />
        <span className="absolute inset-y-0 w-px bg-white/35" style={{ left: `${t.detail_ok}%` }} />
        <span className="absolute inset-y-0 w-px bg-white/70" style={{ left: `${t.detail_good}%` }} />
      </div>
    </div>
  );
};

/** Notes that come from the light in the photo rather than its sharpness. The pupil one reassures (the
 *  engine rebuilds the pupil anyway); the lamp one warns gently and offers a retake. */
const ShotNotes: React.FC<{ q: Quality; onRetake?: () => void }> = ({ q, onRetake }) => (
  <>
    {q.pupil_reflection && (
      <p className="text-xs text-sky-200/90 bg-sky-950/25 border border-sky-500/25 rounded-xl p-3 flex gap-2">
        <Info className="w-4 h-4 shrink-0 mt-px text-sky-300" /> <span>{PUPIL_NOTE}</span>
      </p>
    )}
    {q.lamp_cast && (
      <div className="text-xs text-amber-200/90 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 flex gap-2">
        <Lightbulb className="w-4 h-4 shrink-0 mt-px text-amber-300" />
        <span>
          {q.lamp_message || LAMP_FALLBACK}
          {onRetake && <> <button onClick={onRetake} className="underline underline-offset-2 font-semibold text-amber-100">Try a retake</button></>}
        </span>
      </div>
    )}
  </>
);

/** The camera shot collector: the latest shot's score and the one tip for the next shot, every shot so far
 *  with the best one ringed, and a way to shoot again or go on with the best at any point. */
const ShotCollector: React.FC<{
  shots: Analysis[]; t: Targets; note: string | null;
  onTakeAnother: () => void; onContinue: () => void; onStartOver: () => void; canUse?: boolean;
}> = ({ shots, t, note, onTakeAnother, onContinue, onStartOver, canUse = true }) => {
  const n = shots.length;
  const latest = shots[n - 1];
  const q = latest.quality;
  const d = detailOf(latest);
  const bi = bestIndex(shots);
  const best = shots[bi];
  const bestD = detailOf(best);
  const full = n >= t.max_shots;
  // Prompting ends when the shot we would process is good and lamp-free (the page then goes on by itself).
  // Judged on the best shot, not the latest: a good but lamp-tinted latest shot must still leave room for
  // the daylight retake its own warning asks for.
  const canTakeMore = !full && !autoContinue(best);
  const tip = q && canTakeMore ? topTip(q, t) : null;
  const bestLabel = `shot ${bi + 1}${bestD !== undefined ? ` (Detail ${bestD})` : ''}`;
  // the one case where the latest shot reads "Great photo" and is still not used: say why
  const skippedForLamp = bi !== n - 1 && !!q?.lamp_cast && !best.quality?.lamp_cast;
  const summary = full ? `That is ${t.max_shots} shots. We will use your best one, ${bestLabel}.`
    : n === 1 ? (canTakeMore ? `Take up to ${t.max_shots - 1} more. We measure every shot and keep the best one.` : 'This one is sharp enough to use.')
    : bi === n - 1 ? 'This is your best shot so far.'
    : skippedForLamp ? `Lamp light tinted shot ${n}, so we will use ${bestLabel}, your best shot in true colour.`
    : `Your best so far is ${bestLabel}. That is the one we will use.`;
  return (
    <section className="flex flex-col gap-4">
      <div className="grid grid-cols-[96px_1fr] gap-4 items-center bg-[#0b0e17] border border-white/10 rounded-2xl p-4">
        {latest.preview
          ? <img src={`data:image/jpeg;base64,${latest.preview}`} alt={`Shot ${n}`} className="w-24 h-24 rounded-full border border-[#f5c542]/40 object-cover" />
          : <span className="w-24 h-24 rounded-full bg-white/5" />}
        <div className="min-w-0">
          <p className="text-sm font-bold text-zinc-100">Shot {n} of {t.max_shots}{d !== undefined && ` · Detail ${d}`}</p>
          {q && <div className="mt-1.5"><Verdict v={q.verdict} /></div>}
          <DetailMeter a={latest} t={t} label={false} />
        </div>
      </div>

      {note && (
        <p className="text-xs text-amber-200/90 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3">
          That last shot could not be used: {note} Your best shot so far is kept.
        </p>
      )}
      {tip && (
        <p className="text-sm text-zinc-200 bg-white/5 border border-white/10 rounded-xl p-3 flex gap-2">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-[#f5c542]" /> <span>{tip}</span>
        </p>
      )}
      {/* the notes follow the shot that will be processed, so a lamp warning never disappears while its
          shot is still the one we use. No retake link here: "Take another" below already covers it. */}
      {best.quality && <ShotNotes q={best.quality} />}

      <div>
        <div className="flex items-start gap-3">
          {shots.map((s, i) => {
            const sd = detailOf(s);
            return (
              <div key={i} className="flex flex-col items-center gap-1">
                {s.preview
                  ? <img src={`data:image/jpeg;base64,${s.preview}`} alt={`Shot ${i + 1}`} className={`w-11 h-11 rounded-full object-cover border-2 ${i === bi ? 'border-[#f5c542]' : 'border-white/10 opacity-60'}`} />
                  : <span className={`w-11 h-11 rounded-full bg-white/5 border-2 ${i === bi ? 'border-[#f5c542]' : 'border-white/10'}`} />}
                <span className={`text-[10px] font-mono ${i === bi ? 'text-[#f5c542]' : 'text-zinc-500'}`}>{sd ?? `#${i + 1}`}</span>
              </div>
            );
          })}
          {canTakeMore && Array.from({ length: t.max_shots - n }, (_, i) => (
            <span key={`slot-${i}`} className="w-11 h-11 rounded-full border-2 border-dashed border-white/10" aria-hidden />
          ))}
        </div>
        <p className="text-[11px] text-zinc-500 mt-2">{summary}</p>
      </div>

      <div className={`grid gap-3 ${canTakeMore && canUse ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {canTakeMore && (
          <button onClick={onTakeAnother} className="py-3 rounded-xl bg-[#f5c542] text-black text-sm font-bold flex items-center justify-center gap-2"><Camera className="w-4 h-4" /> Take another</button>
        )}
        {/* the best shot is not centred on an iris: offer only another shot, never the studio */}
        {canUse && (
          <button onClick={onContinue} className={`py-3 rounded-xl text-sm flex items-center justify-center gap-2 ${canTakeMore ? 'bg-white/5 border border-white/10 font-semibold' : 'bg-[#f5c542] text-black font-bold'}`}>
            <Sparkles className="w-4 h-4" /> {n > 1 ? 'Use best shot' : 'Use this shot'}
          </button>
        )}
      </div>
      <button onClick={onStartOver} className="text-xs text-zinc-400 underline underline-offset-4 self-center">Start over</button>
    </section>
  );
};

const Working: React.FC<{ title: string; lines: string[]; elapsed: number; image?: string | null; note?: string; caption?: string }> = ({ title, lines, elapsed, image, note, caption }) => (
  <section className="flex flex-col items-center gap-5 py-6 text-center">
    {image ? <img src={image} alt="Your iris" className="w-40 h-40 rounded-full object-cover border-2 border-[#f5c542]/40 shadow-[0_0_40px_rgba(245,197,66,0.25)] animate-pulse" /> : <div className="w-16 h-16 border-4 border-[#f5c542]/20 border-t-[#f5c542] rounded-full animate-spin" />}
    {image && caption && <span className="-mt-3 text-[10px] uppercase tracking-widest text-amber-200/90">{caption}</span>}
    <h2 className="font-luxury text-xl font-bold">{title}</h2>
    <ul className="text-sm text-zinc-300 space-y-1.5">
      {lines.map((l, i) => (
        <li key={l} className="flex items-center gap-2 justify-center">
          {i < lines.length - 1 ? <Check className="w-4 h-4 text-emerald-400" /> : <span className="w-3.5 h-3.5 border-2 border-[#f5c542]/30 border-t-[#f5c542] rounded-full animate-spin" />}
          {l}
        </li>
      ))}
    </ul>
    {note && <p className="text-xs text-sky-200/90 bg-sky-950/25 border border-sky-500/25 rounded-xl px-3 py-2 max-w-sm">{note}</p>}
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
    // typed as optional on purpose: the DOM lib declares ImageCapture, but iOS Safari before 18.4 has none
    const IC = (window as unknown as { ImageCapture?: typeof ImageCapture }).ImageCapture;
    if (IC) {
      try {
        const ic = new IC(track);
        // Ask for the sensor's largest still. Without settings some Chrome builds return the photo at the
        // preview stream's size, which throws away the iris pixels the 2x zoom was there to gain.
        let settings: PhotoSettings | undefined;
        try {
          const caps = await ic.getPhotoCapabilities?.();
          const w = caps?.imageWidth?.max, h = caps?.imageHeight?.max;
          if (w && h) settings = { imageWidth: w, imageHeight: h };
        } catch { /* capabilities are optional: take the default photo */ }
        let blob: Blob;
        try { blob = await ic.takePhoto(settings); }
        catch (e) { if (!settings) throw e; blob = await ic.takePhoto(); }   // a camera that refuses the size still shoots
        onCapture(blob); return;
      } catch { /* fall through to a video frame */ }
    }
    const c = document.createElement('canvas'); c.width = v.videoWidth; c.height = v.videoHeight; c.getContext('2d')!.drawImage(v, 0, 0);
    c.toBlob((b) => b && onCapture(b), 'image/jpeg', 0.95);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      <div className="relative flex-1 overflow-hidden">
        <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <div className="w-[17%] aspect-square rounded-full border-2 border-[#f5c542] shadow-[0_0_0_9999px_rgba(0,0,0,0.45)] flex items-end justify-center">
            <span className="absolute top-[58%] text-[10px] font-mono bg-black/75 px-2 py-0.5 rounded text-white/90 whitespace-nowrap">iris fills this circle · 12-15 cm · 2x</span>
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
        {!hasStillCapture && (
          // without ImageCapture we can only grab a video frame, and a video frame of this framing is about
          // 250px of iris: below our own 300px floor, so it would fail the quality gate anyway
          <p className="text-[11px] text-amber-300/80">This browser can only grab a low-resolution frame here. For a sharp result use "Take a photo" instead, which opens the real camera.</p>
        )}
        <button onClick={capture} className="w-full py-4 rounded-2xl bg-[#f5c542] text-black font-luxury font-bold uppercase tracking-widest text-sm">Capture</button>
      </div>
    </div>
  );
};
