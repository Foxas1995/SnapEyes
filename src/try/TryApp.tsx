import React, { useEffect, useRef, useState } from 'react';
import { Camera, Upload, Sparkles, RefreshCcw, AlertTriangle, Info, Lightbulb, ArrowLeft, X } from 'lucide-react';
import {
  type Analysis, type Quality, type Targets, targetsOf, shownDetail, rawFibre, bestIndex, visibleTips, topTip, mapPool,
  autoContinue, fibreRatio, meterBand, usable, blockedShot, blockOf,
} from './shots';
import {
  type ColourQa, type Eye, type Layout, type LightAnswer, type ShotOrigin, type StudyPayload,
  MAX_EYES, STUDY_PENDING_MAX, colourOff, deviceInfo, keptSealed, outcomeOf, savedEye, studyAnswered, studyBody, studyOn,
} from './multi';
import { T, setCopyLang, type BlockCopy } from './copy';
import { detectLang, rememberLang, type Lang } from './lang';
import { LANG_NAMES, marketLangs } from '../shared/lang';
import { ResultView } from './ResultView';
import { Working } from './Working';
import { CaptureDiagram } from '../motion/CaptureDiagram';
import { usePreviews } from './usePreviews';
import { sendHelp } from './composeApi';
import { type Opts, type ServerTile, NO_OPTS, advisoryEyes, buyState, lookOf, retakeView, showsPrice } from './picker';
import type { PickerModel } from './StylePicker';
import type { WordsModel } from './Words';
import { DATE_MAX, FAMILY_MAX, NAME_MAX, drawsFamilyName, namesFromWire, namesOf, problems, typed, wireNames } from './names';
import { StudyCard } from './StudyCard';
import { RetakeGuide } from './RetakeGuide';
import { BuyCard, type Ordering } from './BuyCard';
import {
  type CheckoutError, type CheckoutOutcome, type CheckoutStep, type OrderRef, type Snapshot, TICKET_MARGIN_MS, TICKET_MS,
  loadOrderRef, runCheckout, saveOrderRef, saveSnapshot, staleEyes, takeSnapshot,
} from './checkout';
import { callApi, type CheckoutInfo } from '../order/api';
import { experimentToken, listFor, noteChanged, noteCheckoutInfo, noteInfoUnavailable, notePreview } from '../shared/pricing';
import { priceChangedNote } from './priceNote';
import { readCatalogue } from '../shared/catalogue';
import { CHECKOUT_LEGAL, LEGAL_DOCS, LEGAL_LABELS, legalHref } from '../shared/legal';
import { currencyOf, currentMarket, money, priceMinor, serverPrices, withMarket } from '../shared/markets';
import { STYLES as REGISTRY, isStyle } from '../shared/styles';
import { LegalParts } from '../shared/LegalLinks';
import { NO_SAVE } from './noSave';
import { parseReveal } from '../reveal/revealMath';
import { wideFrame, type WideFrame } from '../reveal/wideFrame';

type Step = 'capture' | 'analyzing' | 'quality' | 'processing' | 'result';

// Several photos are measured at once: each /api/analyze call is mostly waiting on the vision model, so
// three in flight cut the wait roughly threefold without piling a whole gallery onto the server at once.
const ANALYZE_CONCURRENCY = 3;

// The owner's capture study (?study=1): two questions after each analysed shot, sent with the next analyze.
const STUDY = typeof window !== 'undefined' && studyOn(window.location.search);

// The page's language, by the landing page's rule (./lang). Set before the first render, so no screen ever shows in
// the wrong language; after that only the language switch in the header changes it.
if (typeof window !== 'undefined') setCopyLang(detectLang());

// The way back from Stripe's payment page (its cancel link, or the browser's back button after a fresh load): the
// artwork this tab kept in sessionStorage just before it opened that page (./checkout.ts). Read once, when the page
// loads, and removed from storage at once; the cancel link's own parameters leave the address bar, so a reload does not
// announce the cancelled payment again.
const RETURN: { snap: Snapshot | null; cancelled: boolean } | null = typeof window !== 'undefined' ? readReturn() : null;

function readReturn(): { snap: Snapshot | null; cancelled: boolean } | null {
  let cancelled = false;
  let order: string | null = null;
  try {
    const q = new URLSearchParams(window.location.search);
    cancelled = q.get('checkout') === 'cancelled';
    order = q.get('o');
  } catch { /* no URL access */ }
  const snap = takeSnapshot(cancelled ? order : null);
  if (cancelled) {
    try {
      const url = new URL(window.location.href);
      url.searchParams.delete('checkout'); url.searchParams.delete('o');
      window.history.replaceState(null, '', url);
    } catch { /* keep the page working without history access */ }
  }
  return snap || cancelled ? { snap, cancelled } : null;
}

// the analysis replies carry the time they arrived: the work ticket in them lives 15 minutes from then
type Stamped = Analysis & { receivedAt?: number };

// image: the display copy (800 px, watermarked across the iris); sealed / sealed_sizes: the clean restoration, sealed by
// the server (api/_lib/preview.py). An older server sent the clean image alone.
interface Enhanced {
  image: string; sealed?: string; sealed_sizes?: Record<string, string>;
  reveal?: unknown;   // the numbers for the Reveal (src/reveal: parseReveal checks them); absent: not measured, the plain slider stays
  fidelity: number; used_sr: boolean; fallback: boolean; seconds: number; stored?: boolean; qa?: ColourQa | null;
}
/** The eye counts a style id takes (the registry, src/shared/styles.ts), for the line that says why a chosen style was not kept. */
const eyesOf = (id: string): readonly [number, number] | null => (isStyle(id) ? REGISTRY[id].eyes : null);

/** The options a saved artwork carries (a snapshot of an older page has none): only the kinds this page makes itself. */
function optsOf(v: unknown): Partial<Opts> {
  if (!v || typeof v !== 'object') return {};
  const o = v as Record<string, unknown>;
  return {
    ...(o.swap === true ? { swap: true } : {}),
    ...(typeof o.rotate === 'number' && Number.isInteger(o.rotate) && o.rotate >= 0 && o.rotate < 8 ? { rotate: o.rotate } : {}),
    ...(typeof o.look === 'string' && /^[a-z0-9_]{1,24}$/.test(o.look) ? { look: o.look } : {}),
  };
}

const SAMPLE_EYE = '/assets/sample_eye_blue_1789706902835.jpg';   // AI-generated: always labelled as such
// The sample's restoration, made once by the live engine (2026-09-29: analyze, deglare, enhance artistic) and shipped
// as files: every "Try the sample" click ran the whole paid restoration again (about 0.07 USD each) for the same
// demo eye. before is the client crop, restored the exact JPEG /api/enhance returned. Composing it stays free. The page
// shows it the way it shows every restoration: /api/enhance {sample: true} turns this very file (and no other) into the
// watermarked display copy and the sealed originals, without a ticket or a model call.
const SAMPLE_BEFORE = '/assets/sample_eye_blue_before.jpg';
const SAMPLE_RESTORED = '/assets/sample_eye_blue_restored.jpg';
const SAMPLE_PAD = 1.12;
// A gallery selection is measured photo by photo (one vision call each): more than this many of the same eye adds
// cost and waiting, not a better pick.
const GALLERY_MAX = 8;
// There is no in-page live camera any more (owner decision 2026-09-29): a browser camera stream gives much softer photos
// than the phone's own camera app (no multi-frame processing, no switch to the telephoto lens, poor close focus), so
// "Take a photo" opens the phone's camera through the file input and "Pick 3-5 shots" the gallery.

/** The restored iris for a new eye, from what /api/enhance returned. */
const restored = (e: Pick<Enhanced, 'image' | 'sealed' | 'sealed_sizes'>) => ({
  image: e.image,
  ...(typeof e.sealed === 'string' && e.sealed ? { sealed: e.sealed } : {}),
  ...(e.sealed_sizes && typeof e.sealed_sizes === 'object' ? { sealedSizes: e.sealed_sizes } : {}),
});

/** POST JSON and return the reply. Throws with the server's own message on any failure, except that with
 *  answerNotOk a 2xx reply saying ok:false is returned: /api/analyze answers a photo with no eye in it that
 *  way, and the capture flow has its own branches for it. Every request carries the page's language, so the
 *  server's own sentences (the quality message, tips and errors) and the preview watermark come back in it. A body
 *  that names its own lang keeps it. */
async function post<R>(path: string, body: Record<string, unknown>, answerNotOk = false): Promise<R> {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ lang: T.lang, ...body }),
  });
  // Vercel answers a timeout or an oversized body with text/plain, so read text first and never let
  // JSON.parse throw the real status away
  const raw = await r.text();
  let j: any = null;
  try { j = JSON.parse(raw); } catch { /* platform error, not ours */ }
  if (!j) {
    if (r.status === 413) throw new Error(T.errors.tooLarge);
    if (r.status === 504 || /TIMEOUT/i.test(raw)) throw new Error(T.errors.timeout);
    throw new Error(T.errors.notResponding);
  }
  if (!r.ok || (j.ok === false && !answerNotOk)) throw new Error(j.error || j.message || T.errors.requestFailed(r.status));
  return j as R;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(T.errors.unreadable));
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
function blobToDataUrl(b: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result));
    r.onerror = () => reject(r.error);
    r.readAsDataURL(b);
  });
}

/** A smaller JPEG data URL of an image (never larger than it was), for the copy kept while Stripe's page is open. */
async function shrunk(src: string, side: number, quality: number): Promise<string> {
  const img = await loadImage(src);
  const s = Math.min(side, img.naturalWidth, img.naturalHeight);
  return drawToDataUrl(img, 0, 0, img.naturalWidth, img.naturalHeight, s, s, quality);
}

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

// the eyes brought back from the payment page: in the order already, so they need no draft of their own
const RESTORED: Eye[] = RETURN?.snap ? RETURN.snap.eyes.slice(0, MAX_EYES).map((e) => ({ ...e, draft: null })) : [];

export const TryApp: React.FC = () => {
  const [lang, setLangState] = useState<Lang>(() => T.lang);
  const [step, setStepRaw] = useState<Step>(RESTORED.length ? 'result' : 'capture');
  // Motion (src/motion/flow.css): a step fades up when it mounts, but only after the page has changed step once (the first screen is the page itself, and an
  // artwork brought back from the payment page is simply there), and the aperture of an artwork that has just been restored opens once, on the first
  // display after the studio finished (arriving), never on a restored or returning session and never after the customer has left the result screen.
  const [stepped, setStepped] = useState(false);
  const [arriving, setArriving] = useState(false);
  const setStep = (s: Step) => { setStepRaw(s); setStepped(true); if (s !== 'result') setArriving(false); };
  const [error, setError] = useState<string | null>(null);
  const [consent, setConsent] = useState(false);
  const [storageOn, setStorageOn] = useState(false);
  const [session] = useState(() => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`);
  // ---- the eye being captured now
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [clientCrop, setClientCrop] = useState<string | null>(null);
  const [working, setWorking] = useState<{ eye: number; sample: boolean }>({ eye: 1, sample: false });
  // ---- the finished eyes, in canvas order. One restored iris each; the photos they came from are released.
  const [eyes, setEyes] = useState<Eye[]>(RESTORED);
  const eyesRef = useRef<Eye[]>(RESTORED);   // async steps read this, never a render's stale copy
  const [selectedId, setSelectedId] = useState<string | null>(RESTORED[0]?.id ?? null);
  const [layoutWant, setLayoutWant] = useState<Layout | null>(RETURN?.snap?.layoutWant ?? null);
  // the style the customer chose (null: none yet, the recommended tile is shown). A saved choice is only a wish: the server's tile list says whether these
  // eyes can take it (src/try/picker.ts resolveStyle), so a choice kept across a change of the number of eyes comes back when the number does
  const [want, setWant] = useState<string | null>(() => (isStyle(RETURN?.snap?.style) ? RETURN!.snap!.style : null));
  // the words on the artwork: a name per eye (by the eye's id, so moving, removing and putting an eye back keep its name), a date, a family name
  const [nameById, setNameById] = useState<Record<string, string>>(() => namesFromWire(RETURN?.snap?.names, RESTORED.map((e) => e.id)));
  const [date, setDate] = useState(() => typed(typeof RETURN?.snap?.date === 'string' ? RETURN.snap.date : '', DATE_MAX));
  const [family, setFamily] = useState(() => typed(typeof RETURN?.snap?.family === 'string' ? RETURN.snap.family : '', FAMILY_MAX));
  const [opts, setOpts] = useState<Opts>(() => ({ ...NO_OPTS, ...optsOf(RETURN?.snap?.opts) }));
  // ---- ordering (./BuyCard.tsx, ./checkout.ts): whether this deployment takes orders, the order this tab builds, the
  // withdrawal waiver (never ticked in advance) and the purchase under way
  const [ordering, setOrdering] = useState<Ordering | null>(null);
  const [orderRef, setOrderRefState] = useState<OrderRef | null>(() => loadOrderRef());
  const orderRefRef = useRef<OrderRef | null>(orderRef);
  const [waiver, setWaiver] = useState(false);
  const [priceNote, setPriceNote] = useState<string | null>(null);   // the price changed while the customer looked (409 price_changed)
  const [buy, setBuy] = useState<{ busy: boolean; step: CheckoutStep | null; error: CheckoutError | 'plan_changed' | 'unavailable' | null }>({ busy: false, step: null, error: null });
  const buyingRef = useRef(false);
  const [now, setNow] = useState(() => Date.now());   // for the 15-minute ticket check, refreshed while ordering is open
  const [notice, setNotice] = useState<'cancelled' | 'lost' | null>(RETURN?.cancelled ? (RESTORED.length ? 'cancelled' : 'lost') : null);
  const retakesRef = useRef(0);   // eyes replaced since the last set of eyes was asked about: sent with the next tile list (the gate funnel's "retake")
  const sizedRef = useRef(new Map<string, string>());   // `${eyeId}:${side}` -> iris re-encoded for /api/compose
  const [progress, setProgress] = useState<string[]>([]);
  const [clock, setClock] = useState<{ step: Step | null; secs: number }>({ step: null, secs: 0 });
  // Camera shot collector: one analysis per camera shot (up to targets.max_shots). Only the best shot keeps
  // its full-size image; five 12 MP photos held at once is how a phone tab gets killed.
  const [shots, setShots] = useState<Analysis[]>([]);
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

  /** The language switch: the whole page re-renders in the new language. Words already on screen that came from
   *  the server (a shot's message and tips) stay as they were until the next photo. */
  const switchLang = (l: Lang) => {
    if (l === T.lang) return;
    setCopyLang(l); rememberLang(l); setLangState(l);
  };

  // the document's language, title and description follow the page's (try.html carries the English ones)
  useEffect(() => {
    try {
      document.documentElement.lang = lang;
      document.title = T.meta.title;
      document.head.querySelector<HTMLMetaElement>('meta[name="description"]')?.setAttribute('content', T.meta.description);
    } catch { /* no document: nothing to label */ }
  }, [lang]);

  // only offer the training-memory checkbox when this deployment can really store something, and the buy button only
  // when it takes orders: /api/health says whether Stripe is set up, GET /api/checkout whether ordering is open (Stripe
  // and the private store) and gives the server's prices and waiver text. Until both say yes: "ordering opens soon".
  useEffect(() => {
    let alive = true;
    fetch('/api/health')
      .then((r) => r.json())
      .then(async (h) => {
        if (!alive) return;
        setStorageOn(!!h.blob_store);
        // live payments only with the delivery email: it carries the confirmation of the withdrawal waiver that the
        // law asks for (src/shared/legal.ts), so a live key without Resend sells nothing yet. Test mode may try it.
        if (h.stripe !== true || (h.stripe_live === true && h.email !== true)) { noteInfoUnavailable(); setOrdering({ open: false }); return; }
        // asked without any id. While a price experiment runs for the visitor's market, noteCheckoutInfo asks once more with the
        // visitor's anonymous id (in a header) and hands back the answer with the ladders of the visitor's variant and the
        // signed token the checkout sends back (src/shared/pricing.ts); otherwise it hands back the same answer
        const c = await callApi<CheckoutInfo>('/api/checkout');
        if (!alive) return;
        let d = c.ok ? c.data : null;
        if (d) d = ((await noteCheckoutInfo(d)) ?? d) as CheckoutInfo; else noteInfoUnavailable();
        if (!alive) return;
        // the most eyes an artwork can be ordered with now is the run-time catalogue's (orderable_max_eyes: the owner's switch lowers it); max_eyes is only the structural limit of an older server
        const orderable = d ? readCatalogue(d) : null;
        setOrdering(d && d.open === true ? { open: true, prices: serverPrices(d, currentMarket()), consent: d.consent, maxEyes: orderable ? orderable.max : typeof d.max_eyes === 'number' ? d.max_eyes : undefined } : { open: false });
      })
      .catch(() => { noteInfoUnavailable(); if (alive) setOrdering({ open: false }); });
    return () => { alive = false; };
  }, []);

  // the "payment cancelled" note belongs to the screen it came back to: once the customer moves on, it is done
  useEffect(() => {
    if (!notice || (notice === 'cancelled' && step === 'result') || (notice === 'lost' && step === 'capture')) return;
    const id = setTimeout(() => setNotice(null), 0);
    return () => clearTimeout(id);
  }, [notice, step]);

  // the 15-minute ticket check looks at the clock again now and then while the buy card is on screen
  const ticking = step === 'result' && !!ordering?.open;
  useEffect(() => {
    if (!ticking) return;
    const first = setTimeout(() => setNow(Date.now()), 0);
    const id = setInterval(() => setNow(Date.now()), 15_000);
    return () => { clearTimeout(first); clearInterval(id); };
  }, [ticking]);

  // back from Stripe's page out of the browser's page cache: this page still holds the artwork as it was, so the copy
  // kept for the way back goes, and the buy button works again
  useEffect(() => {
    const onShow = (e: PageTransitionEvent) => {
      if (!e.persisted) return;
      takeSnapshot(null);
      buyingRef.current = false;
      setBuy({ busy: false, step: null, error: null });
      setOrderRefState(loadOrderRef()); orderRefRef.current = loadOrderRef();
    };
    window.addEventListener('pageshow', onShow);
    return () => window.removeEventListener('pageshow', onShow);
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
    // the places of the eyes mean something else for another number of eyes: swap is for two, rotate for three
    if (next.length !== eyesRef.current.length) setOpts((o) => (o.swap || o.rotate ? { ...o, swap: false, rotate: 0 } : o));
    eyesRef.current = next; setEyes(next);
    const ids = new Set(next.map((e) => e.id));
    for (const k of [...sizedRef.current.keys()]) if (!ids.has(k.split(':')[0])) sizedRef.current.delete(k);
    // (the previews of another set of eyes are dropped by usePreviews)
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
    clearCapture(); commitEyes([]); setSelectedId(null); setLayoutWant(null); setWant(null);
    setNameById({}); setDate(''); setFamily(''); setOpts(NO_OPTS); retakesRef.current = 0;
    setReplacing(null); setUndo(null);
    // a new artwork is a new decision: the waiver is asked again (the order itself is reused for its eyes)
    setWaiver(false); setBuy({ busy: false, step: null, error: null });
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

  /** An eye one place earlier or later on the artwork (four to eight eyes): the order of the eyes is the order on the canvas, and checkout puts the drafts in it. */
  const moveEye = (id: string, delta: -1 | 1) => {
    const list = eyesRef.current;
    const i = list.findIndex((e) => e.id === id), j = i + delta;
    if (i < 0 || j < 0 || j >= list.length) return;
    const next = [...list];
    [next[i], next[j]] = [next[j], next[i]];
    commitEyes(next); setSelectedId(id);
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
  const onFiles = async (all: File[]) => {
    const files = all.slice(0, GALLERY_MAX);
    if (files.length === 1) return onFile(files[0]);
    sampleRef.current = false;
    setError(null); setStep('analyzing'); clearShots();
    // several run at once, so "photo 3 of 5" would be a lie: count the ones that are finished
    let done = 0, sent = 0;
    const tick = () => setProgress([T.working.checking(files.length, done)]);
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
      setError(T.errors.noEyeAny); setStep('capture'); return;
    }
    scored.forEach((s) => { if (s !== win) URL.revokeObjectURL(s.url); });
    const chosen: Analysis = {
      ...win.a,
      picked: { used: win.i + 1, of: files.length, fibre: rawFibre(win.a), worst: Math.min(...scored.map((s) => rawFibre(s.a))) },
    };
    setPhoto(win.img, win.url); setAnalysis(chosen); setProgress([]);
    if (autoContinue(chosen)) { await process(win.img, chosen); } else { setStep('quality'); }
  };

  /** One photo from the phone's camera (the capture input). Measured at once and kept if it is the best so far,
   *  so the customer can shoot, see the score, and shoot again until one is good. */
  const onCameraShot = async (file: Blob) => {
    sampleRef.current = false;
    setError(null); setShotNote(null);
    const t = targetsOf(analysis);
    let prev = shotsRef.current;
    if (prev.length >= t.max_shots) {
      if (usable(prev[bestIndex(prev)])) { setStep('quality'); return; }
      // a full set with nothing the studio may use (too blurry, or not centred): this shot starts a fresh set,
      // so "Take another" always leads somewhere
      clearShots(); prev = [];
    }
    // a shot that fails keeps the collection alive when there is one, and falls back to the old error otherwise
    const fail = (msg: string) => {
      if (!prev.length) { setError(msg); setStep('capture'); return; }
      setShotNote(msg); setStep('quality');
    };
    setStep('analyzing'); setProgress([T.working.measuringShot(prev.length + 1, t.max_shots)]);
    const url = URL.createObjectURL(file);
    const origin: ShotOrigin = 'camera';
    let img: HTMLImageElement; let a: Analysis;
    try {
      img = await loadImage(url);
      a = await measure(img, origin);
    } catch (e) { URL.revokeObjectURL(url); fail((e as Error).message); return; }
    // measure() hands back a no-eye reply instead of throwing, so this shot gets its questions too
    askStudy(origin, 1, outcomeOf(a));
    if (!a.ok || !a.iris) { URL.revokeObjectURL(url); fail(a.message || T.errors.noEyeShot); return; }
    const next = [...prev, a];
    const bi = bestIndex(next);
    if (bi === next.length - 1) {
      if (bestShotRef.current) URL.revokeObjectURL(bestShotRef.current.url);
      bestShotRef.current = { img, url };
    } else {
      URL.revokeObjectURL(url);
    }
    const best = bestShotRef.current;
    if (!best) { fail(T.errors.keepFailed); return; }
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
    fileRef.current?.click();
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
      (a as Stamped).receivedAt = Date.now();
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
    if (!a.ok || !a.iris) { setError(a.message || T.errors.noEye); setStep('capture'); return; }
    setAnalysis(a);
    const sampleOk = sampleRef.current && a.quality?.verdict !== 'weak' && usable(a);
    if (autoContinue(a) || sampleOk) { await process(img, a); } else { setStep('quality'); }
  };

  /** The eye's image re-encoded at the side /api/compose needs for this many eyes (cached per eye). Only for an
   *  artwork with an eye that has no sealed copy (see composeArt). */
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

  const process = async (img: HTMLImageElement, a: Analysis) => {
    // A crop that is not centred on an iris must never reach the studio: from a crop of eyelid skin the image
    // model invented a complete brown iris, and nothing downstream can tell. The server issues no work
    // ticket for it either; this stops the button before the customer waits for an error.
    if (a.quality?.locked === false) {
      setError(T.quality.notCentred);
      setStep('quality'); return;
    }
    // Nor a photo the engine blocked (too blurry to restore the customer's own iris, a pupil too wide): the
    // model would invent the iris. No ticket either.
    const block = blockOf(a);
    if (block) {
      setError(block.error);
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
    // sealed is the clean preview /api/enhance made, as the server sealed it and never re-encoded: an order uploads
    // exactly it, with the deglared crop it was made from and the photo's work ticket (./checkout.ts), and the server
    // opens it. image is only the watermarked display copy. The sample eye is never ordered.
    const draft = !sample && a.ticket && typeof d.crop === 'string' && d.crop
      ? { crop: d.crop, ticket: a.ticket, until: ((a as Stamped).receivedAt ?? Date.now()) + TICKET_MS - TICKET_MARGIN_MS }
      : null;
    // The Reveal (src/reveal): the numbers /api/enhance measured for it and, cut now while this page still holds the photo (it is released below), the
    // customer's own photo in the Reveal's frame. The frame lives in this tab's memory only: never uploaded, never saved (keepForReturn leaves it out).
    // Without it the Reveal is built from the client crop (src/reveal/useRevealFrame.ts); without the numbers the plain slider stays.
    const reveal = sample ? undefined : parseReveal(e.reveal) ?? undefined;
    let wide: WideFrame | undefined;
    if (reveal) {
      try { wide = wideFrame(img, { cx: cx * W, cy: cy * H, r: r * W, W, H, pad }, reveal); } catch { /* the frame is built from the crop instead */ }
    }
    const eye: Eye = {
      id, before: crop, ...restored(e), thumb: await thumbOf(e.image), pad,
      fallback: !!e.fallback, usedSr: !!e.used_sr, stored: !!e.stored, glarePct: d.glare_pct,
      diameterPx: a.quality?.diameter_px, sample, colourOff: colourOff(e.qa), draft,
      ...(reveal ? { reveal } : {}), ...(wide ? { wide } : {}),
    };
    // a retaken eye takes the old one's place; the old restoration goes only now that the new one exists
    const cur = eyesRef.current;
    const list = replaceId && cur.some((x) => x.id === replaceId)
      ? cur.map((x) => (x.id === replaceId ? eye : x))
      : [...cur, eye];
    // a retaken eye takes the old one's place AND its name; the gate funnel hears that an eye of the set was replaced (api/compose.py retake)
    if (replaceId) {
      setNameById((m) => { const { [replaceId]: kept, ...rest } = m; return kept ? { ...rest, [eye.id]: kept } : rest; });
      retakesRef.current += 1;
    }
    setReplacing(null);
    commitEyes(list); setSelectedId(eye.id);
    releasePhoto(); sampleRef.current = false;
    setAnalysis(null); setClientCrop(null);
    setStep('result'); setArriving(true); toTop();
  };

  // ---- the result screen: the server's tile list for these eyes, the style on screen and its previews (src/try/usePreviews.ts)
  const namesList = namesOf(nameById, eyes.map((e) => e.id));
  const previews = usePreviews({
    active: step === 'result' && eyes.length > 0, eyes, lang, market: currentMarket(), want, layoutWant, names: namesList, date, family, opts,
    retakes: retakesRef, sized: sizedIris, eyesOf,
  });
  const { catalog, art, style } = previews;
  const selectedTile = previews.selected;
  const wordProblems = problems(namesList, date, family);

  // a preview was made: once per visitor and price experiment the server hears it (anonymously; src/shared/pricing.ts)
  useEffect(() => {
    if (step !== 'result' || !style) return;
    const real = eyes.filter((e) => !e.sample).length;
    if (real > 0) notePreview(real, style);
  }, [step, eyes, style, ordering]);   // ordering: the server's answer (the token) may arrive after the first preview

  // what the picker shows: everything is a function of the server's tile list (src/try/picker.ts)
  const market = currentMarket();
  const priceList = listFor(market, ordering?.open ? ordering.prices : undefined);
  const priceOf = (tl: ServerTile) => (!eyes.some((e) => e.sample) && showsPrice(eyes.length, tl) ? money(priceMinor(1, tl.id, market, priceList), currencyOf(market), T.lang) : null);
  const retakeState = catalog ? retakeView({ tiles: catalog.tiles, eyes: catalog.eyes, selected: selectedTile }) : null;
  const advisory = advisoryEyes(selectedTile, catalog?.eyes ?? []);
  const lookNow = lookOf(selectedTile, opts.look);
  // what the buy card does: the price and the button only for a style AND a look that can be bought (a Soon look under a live style is drawn, never sold)
  const buying = buyState({ n: eyes.length, tiles: catalog?.tiles ?? [], selected: selectedTile, look: lookNow });
  const picker: PickerModel = {
    n: eyes.length, catalog, error: previews.catalogError, onRetryCatalog: previews.retryCatalog, style, selected: selectedTile, changed: previews.changed,
    tilePicture: previews.tilePicture, tileBusy: previews.tileBusy, tileFailed: previews.tileFailed, onRetryTiles: previews.retryTiles, paused: previews.tilesPaused, priceOf,
    onStyle: (id) => setWant(id), look: lookNow, onLook: (code) => setOpts((o) => ({ ...o, look: code })), retake: retakeState, advisory,
    onRetakeEye: (i) => { const e = eyes[i - 1]; if (e) retakeEye(e.id); },
    onRemoveEye: (i) => { const e = eyes[i - 1]; if (e) removeEye(e.id); },
    onManual: () => sendHelp({ route: 'manual', eyes: eyes.length, why: retakeState?.why ?? (catalog && !style ? 'no_style' : 'unknown'), lang: T.lang }),
  };
  const words: WordsModel = {
    names: namesList,
    onName: (i, v) => { const e = eyes[i]; if (e) setNameById((m) => ({ ...m, [e.id]: typed(v, NAME_MAX) })); },
    date, onDate: (v) => setDate(typed(v, DATE_MAX)), family, onFamily: (v) => setFamily(typed(v, FAMILY_MAX)),
    showFamily: !!previews.layout && drawsFamilyName(previews.layout), problems: wordProblems,
  };

  // ---- buying
  const setOrderRef = (r: OrderRef | null) => { orderRefRef.current = r; setOrderRefState(r); saveOrderRef(r); };

  /** Keep the artwork in this tab while Stripe's page is open, so its cancel link (or "back") finds it as it was. When
   *  the browser will not hold it at full size, a smaller copy; when not even that, nothing (the page then says so). */
  const keepForReturn = async (order: string, list: Eye[], st: string, lw: Layout | null, nm: string) => {
    const base = { v: 1 as const, order, at: Date.now(), style: st, layoutWant: lw, names: nm, date, family, opts };
    // the Reveal's frame is memory only: never saved, even here (savedEye leaves it out; the way back builds it again from the crop it keeps)
    const plain = list.map(savedEye);
    if (saveSnapshot({ ...base, eyes: plain })) return;
    try {
      // the sealed irises cannot be shrunk here: the smaller copy leaves one of them out (keptSealed)
      const small = await Promise.all(plain.map(async ({ sealed, sealedSizes, ...e }) => ({
        ...e,
        ...keptSealed({ sealed, sealedSizes }, plain.length),
        before: await shrunk(e.before, 480, 0.8),
        image: stripDataUrl(await shrunk(`data:image/jpeg;base64,${e.image}`, 768, 0.88)),
      })));
      saveSnapshot({ ...base, eyes: small });
    } catch { /* nothing kept: the way back says so */ }
  };

  const onBuy = async () => {
    const list = eyesRef.current;
    if (buyingRef.current || !list.length || list.some((e) => e.sample) || !waiver || !ordering?.open || !style || !art || wordProblems.length || buying.kind !== 'normal') return;
    buyingRef.current = true;
    setNotice(null);
    setPriceNote(null);
    setBuy({ busy: true, step: null, error: null });
    const lay = previews.layout ?? '';
    let out: CheckoutOutcome;
    try {
      // the price on the button is what the server is asked to confirm (shown); the token names the visitor's variant
      const market = currentMarket();
      const shown = priceMinor(list.length, style, market, listFor(market, ordering?.prices));
      // the artwork on screen, as the server described it: its plan (plan8) and the options that applied are sent back, so a checkout of something else is a 409
      out = await runCheckout({ eyes: list, style, layout: lay, names: wireNames(namesList), date, familyName: family, opts: art.opts, plan8: art.plan8, plan8Core: art.plan8Core, lang: T.lang, ref: orderRefRef.current, expToken: experimentToken(), shown },
        (s) => setBuy((b) => ({ ...b, step: s })));
    } catch {
      out = { kind: 'error', code: 'failed', ref: orderRefRef.current };
    }
    setOrderRef(out.ref);
    if (out.kind === 'redirect') {
      await keepForReturn(out.ref.order, list, style, layoutWant, wireNames(namesList));
      window.location.assign(out.url);
      return;   // the page is leaving for Stripe: the button stays busy
    }
    if (out.kind === 'paid') { window.location.assign(out.url); return; }
    buyingRef.current = false;
    if (out.kind === 'stale') {
      // those eyes' tickets are spent: they show as "take again" from now on
      const bad = new Set(out.eyes.map((i) => eyesRef.current[i - 1]?.id));
      commitEyes(eyesRef.current.map((e) => (bad.has(e.id) ? { ...e, draft: null } : e)));
      setNow(Date.now());
      setBuy({ busy: false, step: null, error: null });
      return;
    }
    if (out.kind === 'closed') { setOrdering({ open: false }); setBuy({ busy: false, step: null, error: null }); return; }
    if (out.kind === 'plan_changed' || out.kind === 'unavailable') {
      // nothing was created: the tile list and the previews are made again, and the customer looks at the artwork once more before going on
      previews.refresh();
      setBuy({ busy: false, step: null, error: out.kind });
      return;
    }
    if (out.kind === 'price_changed') {
      // the price is not the one shown: nothing was created. Show the server's price and let the customer decide again
      noteChanged(out.reply);
      const market = currentMarket();
      setOrdering((o) => (o ? { ...o, prices: serverPrices({ prices: out.reply.prices, markets: { [market]: { prices: out.reply.prices } } }, market) } : o));
      setPriceNote(priceChangedNote(T.lang, money(out.reply.amount, currencyOf(market), T.lang)));
      setBuy({ busy: false, step: null, error: null });
      return;
    }
    setBuy({ busy: false, step: null, error: out.code });
  };

  const stepText = (s: CheckoutStep | null): string | null => {
    if (!s) return null;
    if (s.kind === 'upload') return T.buy.steps.upload(s.i, s.n);
    return T.buy.steps[s.kind];
  };
  const purchase = (
    <BuyCard
      eyes={eyes} style={style ?? ''} styleName={selectedTile?.name ?? style ?? ''} ordering={ordering}
      preview={art ? 'ready' : previews.composeError !== null ? 'failed' : 'composing'}
      state={buying} loading={!catalog && !previews.catalogError}
      advisory={advisory} wordsBlocked={wordProblems.length > 0}
      stale={ordering?.open && !eyes.some((e) => e.sample) ? staleEyes(eyes, orderRef, now) : []}
      onRetake={(i) => { const e = eyes[i - 1]; if (e) retakeEye(e.id); }}
      waiver={waiver} onWaiver={setWaiver}
      busy={buy.busy} step={stepText(buy.step)} error={buy.error ? T.buy.errors[buy.error] : null}
      priceNote={priceNote}
      onBuy={onBuy} />
  );

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
    // the prepared restoration (SAMPLE_RESTORED): no paid call. The server makes its display copy and seals it, as for
    // every restoration. If the files cannot be read or the server does not take them, the sample photo goes through
    // the studio as before
    try {
      const [rb, ra] = await Promise.all([fetch(SAMPLE_BEFORE), fetch(SAMPLE_RESTORED)]);
      if (!rb.ok || !ra.ok) throw new Error('sample files');
      const [before, file] = await Promise.all([blobToDataUrl(await rb.blob()), blobToDataUrl(await ra.blob())]);
      const r = await post<Enhanced>('/api/enhance', { sample: true, image: stripDataUrl(file) });
      if (typeof r.image !== 'string' || !r.image || typeof r.sealed !== 'string') throw new Error('sample preview');
      const eye: Eye = {
        id: newEyeId(), before, ...restored(r), thumb: await thumbOf(r.image), pad: SAMPLE_PAD,
        fallback: false, usedSr: false, stored: false, glarePct: 0, sample: true, colourOff: false, draft: null,
      };
      sampleRef.current = false;
      setError(null); setWorking({ eye: 1, sample: true });
      setStep('processing'); setProgress([T.working.composing(1)]);
      const list = [eye];
      commitEyes(list); setSelectedId(eye.id);
      releasePhoto(); setAnalysis(null); setClientCrop(null);
      setStep('result'); setArriving(true); toTop();
      return;
    } catch { /* fall back to the studio below */ }
    try {
      const r = await fetch(SAMPLE_EYE);
      if (!r.ok) throw new Error(T.capture.sampleLoadFailed);
      await onFile(await r.blob(), true);
    } catch (e) { setError((e as Error).message); }
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-[#f0f3fa]">
      <header className="px-4 py-4 flex items-center justify-between gap-3 max-w-3xl mx-auto">
        {/* back to the landing page in the same language */}
        <a href={withMarket(`/?lang=${lang}`)} className="shrink-0 font-luxury font-semibold tracking-wider text-lg">SNAP<span className="text-[#f5c542]">EYES</span></a>
        <div className="flex items-center justify-end gap-3 min-w-0">
          <span className="min-w-0 text-[10px] uppercase tracking-widest text-zinc-400 text-right flex flex-wrap items-center justify-end gap-x-2 gap-y-1">
            {STUDY && <span className="text-sky-300 border border-sky-400/40 rounded-full px-2 py-0.5">{T.header.study}</span>}
            <span>{T.header.tag}</span>
          </span>
          <LangSwitch lang={lang} onSwitch={switchLang} />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 pb-12">
        {/* every screen after the first has its headings below this one: the page's own title for a screen reader (the first screen has its own h1) */}
        {step !== 'capture' && <h1 className="sr-only">{T.meta.title}</h1>}
        {error && (
          <div className="fx-note mb-4 bg-rose-950/40 border border-rose-500/40 text-rose-200 text-sm rounded-xl p-3 flex gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> <span>{error}</span>
          </div>
        )}

        {/* back from Stripe's page without paying */}
        {((notice === 'cancelled' && step === 'result') || (notice === 'lost' && step === 'capture')) && (
          <div role="status" data-testid="checkout-notice" className="fx-note mb-4 bg-sky-950/40 border border-sky-400/40 text-sky-100 text-sm rounded-xl p-3 flex gap-2 items-start">
            <Info className="w-4 h-4 shrink-0 mt-0.5 text-sky-300" />
            <span className="flex-1 min-w-0">{notice === 'cancelled' ? T.buy.cancelled : T.buy.cancelledLost}</span>
            <button type="button" onClick={() => setNotice(null)} aria-label={T.buy.close} className="shrink-0 -m-1 p-1 text-sky-200 hover:text-white"><X className="w-4 h-4" /></button>
          </div>
        )}

        {studyAsk && (
          <StudyCard ask={studyAsk} onLight={(light) => answerStudy({ light })} onComfort={(comfort) => answerStudy({ comfort })} onSkip={skipStudy} />
        )}

        {/* Both pickers live outside the capture screen so "Take another" can reopen the camera from the
            shot collector. The value is cleared after every pick so the same file can be chosen again. */}
        <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; e.target.value = ''; if (f) onCameraShot(f); }} />
        <input ref={galleryRef} type="file" accept="image/*" multiple className="hidden"
          onChange={(e) => { const fs = Array.from(e.target.files || []); e.target.value = ''; if (fs.length) onFiles(fs); }} />

        {step === 'capture' && (
          <section className={`flex flex-col gap-5${stepped ? ' fx-step' : ''}`}>
            {adding ? (
              <div className="text-center mt-2">
                <h1 className="font-luxury text-3xl sm:text-4xl font-bold">{(replaceNo ? T.capture.retakeTitle(replaceNo) : T.capture.addTitle(eyes.length + 1)).toUpperCase()}</h1>
                <p className="text-zinc-400 text-sm mt-2">{replaceNo ? T.capture.retakeLead : T.capture.addLead}</p>
                <div className="flex flex-wrap justify-center gap-x-2 gap-y-1 mt-3">
                  {eyes.map((e, i) => (
                    <span key={e.id} className="flex flex-col items-center gap-0.5 w-16">
                      <img {...NO_SAVE} src={e.thumb} alt="" className={`w-9 h-9 rounded-full object-cover ${e.id === replacing ? 'border-2 border-dashed border-[#f5c542]/70 opacity-50' : 'border border-[#f5c542]/40'}`} />
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
                <h1 className="font-luxury text-3xl sm:text-4xl font-bold">{T.capture.titleA}<span className="text-[#f5c542]">{T.capture.titleB}</span></h1>
                <p className="text-zinc-400 text-sm mt-2">{T.capture.lead}</p>
              </div>
            )}

            <CaptureDiagram />

            <div className="bg-[#0b0e17] border border-white/10 rounded-2xl p-4 text-xs text-zinc-300 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {T.capture.steps.map((s) => (
                <div key={s.title}><span className="text-[#f5c542] font-bold block">{s.title}</span>{s.text}</div>
              ))}
              <div className="col-span-2 sm:col-span-4 pt-1 border-t border-white/10"><span className="text-[#f5c542] font-bold">{T.capture.stepsOpen}</span>{T.capture.stepsOpenMore}</div>
              <div className="col-span-2 sm:col-span-4 pt-1 border-t border-white/10"><span className="text-[#f5c542] font-bold">{T.capture.stepsShots}</span>{T.capture.stepsShotsMore}</div>
              {!adding && <div className="col-span-2 sm:col-span-4 text-zinc-400">{T.capture.helper}</div>}
            </div>

            {/* the first camera shot starts a fresh collection */}
            <button onClick={() => { clearShots(); fileRef.current?.click(); }} className="fx-gold w-full py-4 rounded-2xl font-luxury font-bold uppercase tracking-widest text-sm flex items-center justify-center gap-2">
              <Camera className="w-5 h-5" /> {T.capture.takePhoto}
            </button>

            <div className={`grid gap-3 ${offerSample ? 'grid-cols-2' : 'grid-cols-1'}`}>
              <button onClick={() => galleryRef.current?.click()} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                <Upload className="w-4 h-4 text-[#f5c542]" /> {T.capture.pickShots}
              </button>
              {offerSample && (
                <button onClick={trySample} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                  <Sparkles className="w-4 h-4 text-[#f5c542]" /> {T.capture.sampleButton}
                </button>
              )}
            </div>

            {/* whose eye may be photographed (the terms of sale), and where the photo goes */}
            <p data-testid="photo-notice" className="text-[11px] leading-relaxed text-zinc-500 text-center">
              <LegalParts parts={CHECKOUT_LEGAL[lang].photoNotice} lang={lang} />
            </p>

            {storageOn && (
            <label className="flex items-start gap-3 text-xs text-zinc-400 bg-white/5 border border-white/5 rounded-xl p-3 cursor-pointer">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5 w-4 h-4" />
              <span>{T.capture.consent}</span>
            </label>
            )}
            {backLink}
          </section>
        )}

        {step === 'analyzing' && (
          <Working title={T.working.finding} lines={progress.length ? progress : [T.working.locating, T.working.measuringSize]} active={progress.length ? 1 : 2} elapsed={elapsed} enter={stepped} />
        )}

        {step === 'quality' && analysis?.quality && shots.length > 0 && (
          <>
            <ShotCollector shots={shots} t={targetsOf(analysis)} note={shotNote} onTakeAnother={takeAnother} enter={stepped}
              canUse={usable(analysis)}
              onContinue={() => imgRef.current && process(imgRef.current, analysis)} onStartOver={retake} />
            {backLink && <div className="flex justify-center mt-4">{backLink}</div>}
          </>
        )}

        {step === 'quality' && analysis?.quality && shots.length === 0 && (
          <section className={`flex flex-col gap-4${stepped ? ' fx-step' : ''}`}>
            <div className="grid grid-cols-[120px_1fr] gap-4 items-center bg-[#0b0e17] border border-white/10 rounded-2xl p-4">
              {analysis.preview && <img src={`data:image/jpeg;base64,${analysis.preview}`} alt={T.quality.detectedIris} className="w-[120px] h-[120px] rounded-full border border-[#f5c542]/40 object-cover" />}
              <div className="min-w-0">
                <Verdict v={analysis.quality.verdict} block={blockOf(analysis)} />
                {/* blocked: the one-line reason; the retake steps are in the guide below (the server's message
                    lists them too, and shown together every step was read twice) */}
                <p className="text-sm text-zinc-200 mt-2">{blockOf(analysis)?.reason ?? analysis.quality.message}</p>
                <DetailMeter a={analysis} t={targetsOf(analysis)} />
              </div>
            </div>
            {analysis.picked && (usable(analysis) ? (
              <p className="text-xs text-emerald-300/90 bg-emerald-950/25 border border-emerald-500/30 rounded-xl p-3">
                {/* "best", not "sharpest": the verdict ranks first, so a glared photo can be sharper and still lose */}
                {T.quality.picked(analysis.picked.of, analysis.picked.used)}
                {fibreRatio(analysis.picked) !== null && T.quality.pickedRatio(T.dec1(fibreRatio(analysis.picked)!))}
              </p>
            ) : (
              // the best of the pick still cannot be used: never say "used"
              <p className="text-xs text-rose-200/90 bg-rose-950/25 border border-rose-500/30 rounded-xl p-3">{T.quality.noneUsable(analysis.picked.of)}</p>
            ))}
            {/* blocked: the retake steps for its reason replace the tips list, which would only repeat them */}
            {blockOf(analysis) && <RetakeGuide block={blockOf(analysis)!} />}
            <ShotNotes q={analysis.quality} onRetake={retake} />
            {!blockedShot(analysis) && visibleTips(analysis.quality).length > 0 && (
              <ul className="text-xs text-zinc-300 bg-white/5 border border-white/10 rounded-xl p-3 space-y-1.5">
                {visibleTips(analysis.quality).map((t) => <li key={t}>• {t}</li>)}
              </ul>
            )}
            <div className={`grid gap-3 ${usable(analysis) ? 'grid-cols-2' : 'grid-cols-1'}`}>
              <button onClick={retake} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2"><RefreshCcw className="w-4 h-4" /> {T.quality.retake}</button>
              {/* no way forward from a crop that is not an iris, nor from one the engine blocked: the studio
                  would invent one, and the server gave neither a work ticket */}
              {usable(analysis) && (
                <button onClick={() => imgRef.current && process(imgRef.current, analysis)} className="py-3 rounded-xl bg-[#f5c542] text-black text-sm font-bold flex items-center justify-center gap-2"><Sparkles className="w-4 h-4" /> {T.quality.continueAnyway}</button>
              )}
            </div>
            {backLink}
          </section>
        )}

        {step === 'processing' && (
          <Working title={working.eye > 1 ? T.working.restoringEye(working.eye) : T.working.restoring} lines={progress} elapsed={elapsed} image={clientCrop}
            caption={working.sample ? T.working.sampleCaption : undefined} enter={stepped}
            note={analysis?.quality?.pupil_reflection ? T.quality.pupilNote : undefined} />
        )}

        {step === 'result' && STUDY && !studyAsk && pendingShots.length > 0 && (
          <p data-testid="study-pending" className="mb-4 text-xs text-sky-200 bg-sky-950/30 border border-sky-400/30 rounded-xl p-3">
            {T.study.pending(pendingShots)}
          </p>
        )}

        {step === 'result' && eyes.length > 0 && (
          <ResultView
            eyes={eyes} selectedId={selectedId} onSelect={setSelectedId} onRemove={removeEye} onRetake={retakeEye} onAdd={addEye} onMove={moveEye}
            art={art} staleArt={previews.staleArt} composeError={previews.composeError} onRetryCompose={previews.retryCompose}
            picker={picker} layout={previews.layout} layoutOptions={selectedTile?.layouts ?? []} onLayout={setLayoutWant}
            opts={opts} onOpts={setOpts} words={words}
            onStartOver={startOver} purchase={purchase} enter={stepped} arrive={arriving} onArrived={() => setArriving(false)} />
        )}
      </main>

      {/* the four legal pages (the Impressum must be one click away from every page), opened in a new tab so a
          capture or an artwork is never lost */}
      <footer className="max-w-3xl mx-auto px-4 pb-24">
        <nav aria-label={LEGAL_LABELS[lang].nav} className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-zinc-400">
          {LEGAL_DOCS.map((d) => (
            <a key={d} href={legalHref(d, lang)} target="_blank" rel="noopener" className="hover:text-white hover:underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] rounded-sm">
              {LEGAL_LABELS[lang][d]}
            </a>
          ))}
        </nav>
      </footer>

      {step === 'result' && undo && (
        <div role="status" className="fx-toast fixed bottom-4 inset-x-4 z-40 mx-auto max-w-sm bg-zinc-900 border border-white/15 rounded-xl pl-4 pr-1 flex items-center justify-between gap-3 text-sm text-zinc-100 shadow-lg shadow-black/50">
          <span>{T.result.removed(undo.index + 1)}</span>
          <button onClick={undoRemove} className="min-h-[44px] min-w-[44px] px-3 font-bold text-[#f5c542] underline underline-offset-4">{T.result.undo}</button>
        </div>
      )}
    </div>
  );
};

/** The language switch, as on the landing page (src/landing/Header.tsx LangSwitch): one button per language the page's
 *  market can be read in. */
const LangSwitch: React.FC<{ lang: Lang; onSwitch: (l: Lang) => void }> = ({ lang, onSwitch }) => (
  <div role="group" aria-label={T.switchLabel} className="shrink-0 flex items-center rounded-full border border-white/10 p-0.5 text-[11px] font-semibold tracking-[0.12em]">
    {marketLangs(currentMarket()).map((l) => (
      <button key={l} type="button" onClick={() => onSwitch(l)} aria-pressed={lang === l} lang={l} title={LANG_NAMES[l]}
        className={`min-w-[40px] rounded-full px-2.5 py-1.5 max-[340px]:min-w-[28px] max-[340px]:px-1.5 uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] ${lang === l ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'}`}>
        {l}
      </button>
    ))}
  </div>
);

const Verdict: React.FC<{ v: 'good' | 'ok' | 'weak'; block?: BlockCopy | null }> = ({ v, block = null }) => {
  const map = { good: [T.quality.verdicts.good, 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40'], ok: [T.quality.verdicts.ok, 'bg-amber-500/15 text-amber-300 border-amber-500/40'], weak: [T.quality.verdicts.weak, 'bg-rose-500/15 text-rose-300 border-rose-500/40'] } as const;
  // a blocked shot is not merely weak: nothing will be made from it, and its badge says why
  const [label, cls] = block ? [block.badge, map.weak[1]] : map[v];
  return <span className={`inline-block text-[11px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border ${cls}`}>{label}</span>;
};

/** Detail N/100 with the ok and good targets marked, so the customer sees how far a retake has to go.
 *  Renders nothing against an older server that sends no score (the verdict badge still speaks there), nor
 *  for a blocked shot, whose number would contradict its "Too blurry" badge (shownDetail). */
const DetailMeter: React.FC<{ a: Analysis; t: Targets; label?: boolean }> = ({ a, t, label = true }) => {
  const d = shownDetail(a);
  if (d === undefined) return null;
  const { band, caption } = meterBand(d, a.quality, t);
  const [text, bar] = { good: ['text-emerald-300', 'bg-emerald-400'], ok: ['text-amber-300', 'bg-amber-400'], low: ['text-rose-300', 'bg-rose-400'] }[band];
  return (
    <div className="mt-3" role="meter" aria-label={T.quality.detail} aria-valuemin={0} aria-valuemax={100} aria-valuenow={d}>
      <div className="flex items-baseline justify-between gap-2 text-xs">
        {label ? <span className="font-bold text-zinc-200">{T.quality.detail} <span className={text}>{d}</span><span className="text-zinc-500">/100</span></span> : <span />}
        {caption && <span className="text-[10px] text-zinc-500">{caption}</span>}
      </div>
      <div className="relative h-2 mt-1.5 rounded-full bg-white/10 overflow-hidden">
        <div className={`fx-fill h-full rounded-full ${bar}`} style={{ width: `${Math.max(d, 2)}%` }} />
        <span className="absolute inset-y-0 w-px bg-white/35" style={{ left: `${t.detail_ok}%` }} />
        <span className="absolute inset-y-0 w-px bg-white/70" style={{ left: `${t.detail_good}%` }} />
      </div>
    </div>
  );
};

/** Notes that come from the light in the photo rather than its sharpness. The pupil one reassures (the
 *  engine rebuilds the pupil anyway), so it is left out for a blocked shot that will not be rebuilt at all;
 *  the lamp one warns gently and offers a retake. */
const ShotNotes: React.FC<{ q: Quality; onRetake?: () => void }> = ({ q, onRetake }) => (
  <>
    {q.pupil_reflection && !q.blocked && (
      <p className="text-xs text-sky-200/90 bg-sky-950/25 border border-sky-500/25 rounded-xl p-3 flex gap-2">
        <Info className="w-4 h-4 shrink-0 mt-px text-sky-300" /> <span>{T.quality.pupilNote}</span>
      </p>
    )}
    {q.lamp_cast && (
      <div className="text-xs text-amber-200/90 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 flex gap-2">
        <Lightbulb className="w-4 h-4 shrink-0 mt-px text-amber-300" />
        <span>
          {q.lamp_message || T.quality.lampFallback}
          {onRetake && <> <button onClick={onRetake} className="underline underline-offset-2 font-semibold text-amber-100">{T.quality.tryRetake}</button></>}
        </span>
      </div>
    )}
  </>
);

/** The camera shot collector: the latest shot's score and the one tip for the next shot, every shot so far
 *  with the best one ringed, and a way to shoot again or go on with the best at any point. */
const ShotCollector: React.FC<{
  shots: Analysis[]; t: Targets; note: string | null;
  onTakeAnother: () => void; onContinue: () => void; onStartOver: () => void; canUse?: boolean; enter?: boolean;
}> = ({ shots, t, note, onTakeAnother, onContinue, onStartOver, canUse = true, enter = false }) => {
  const n = shots.length;
  const latest = shots[n - 1];
  const q = latest.quality;
  // a blocked shot shows no Detail anywhere here: its number could read higher than the usable shot we pick
  const d = shownDetail(latest);
  const bi = bestIndex(shots);
  const best = shots[bi];
  const bestD = shownDetail(best);
  const full = n >= t.max_shots;
  const bestUsable = usable(best);
  const use = canUse && bestUsable;
  // Prompting ends when the shot we would process is good and lamp-free (the page then goes on by itself).
  // Judged on the best shot, not the latest: a good but lamp-tinted latest shot must still leave room for
  // the daylight retake its own warning asks for. A full set with nothing usable in it still takes another
  // shot, which starts a fresh set (onCameraShot).
  const canTakeMore = !autoContinue(best) && (!full || !bestUsable);
  // nothing usable yet and the latest shot was blocked: the retake card with the steps for its reason (the
  // one the customer just saw fail). With a usable best shot the one-line tip below covers it instead.
  const guide = !bestUsable ? blockOf(latest) : null;
  // the latest shot's tip, unless the retake card already says it (the server's message lists the same steps)
  const tip = q && canTakeMore && !guide ? topTip(q, t) : null;
  const bestLabel = T.collector.bestLabel(bi + 1, bestD);
  // the one case where the latest shot reads "Great photo" and is still not used: say why
  const skippedForLamp = bi !== n - 1 && !!q?.lamp_cast && !best.quality?.lamp_cast;
  const summary = !bestUsable ? (full ? T.quality.fullUnusable(t.max_shots) : n === 1 ? T.quality.shotUnusable : T.quality.shotsUnusable)
    : full ? T.collector.full(t.max_shots, bestLabel)
    : n === 1 ? (canTakeMore ? T.collector.more(t.max_shots - 1) : T.collector.sharpEnough)
    : bi === n - 1 ? T.collector.bestSoFar
    : skippedForLamp ? T.collector.lampSkipped(n, bestLabel)
    : T.collector.bestIs(bestLabel);
  return (
    <section className={`flex flex-col gap-4${enter ? ' fx-step' : ''}`}>
      <div className="grid grid-cols-[96px_1fr] gap-4 items-center bg-[#0b0e17] border border-white/10 rounded-2xl p-4">
        {latest.preview
          ? <img src={`data:image/jpeg;base64,${latest.preview}`} alt={T.collector.shotAlt(n)} className="w-24 h-24 rounded-full border border-[#f5c542]/40 object-cover" />
          : <span className="w-24 h-24 rounded-full bg-white/5" />}
        <div className="min-w-0">
          <p className="text-sm font-bold text-zinc-100">{T.collector.header(n, t.max_shots)}{d !== undefined && T.collector.headerDetail(d)}</p>
          {q && <div className="mt-1.5"><Verdict v={q.verdict} block={blockOf(latest)} /></div>}
          <DetailMeter a={latest} t={t} label={false} />
        </div>
      </div>

      {note && (
        <p className="text-xs text-amber-200/90 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3">
          {T.collector.lastFailed(note)}
        </p>
      )}
      {tip && (
        <p className="text-sm text-zinc-200 bg-white/5 border border-white/10 rounded-xl p-3 flex gap-2">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-[#f5c542]" /> <span>{tip}</span>
        </p>
      )}
      {/* nothing usable and the latest shot blocked: the capture guide's steps for the next one. Its title says
          why; the server's message is left out because it lists the same steps */}
      {guide && <RetakeGuide block={guide} />}
      {/* the notes follow the shot that will be processed, so a lamp warning never disappears while its
          shot is still the one we use. No retake link here: "Take another" below already covers it. */}
      {best.quality && <ShotNotes q={best.quality} />}

      <div>
        <div className="flex items-start gap-3">
          {shots.map((s, i) => {
            // a blocked shot's thumbnail names its reason: its Detail number is not a measure of anything usable
            const sd = blockOf(s)?.thumb ?? shownDetail(s);
            // the best shot is ringed in gold only when it is one we would really use
            const ring = i !== bi ? 'border-white/10' : usable(s) ? 'border-[#f5c542]' : 'border-rose-400/70';
            const ink = i !== bi ? (usable(s) ? 'text-zinc-500' : 'text-rose-300/70') : usable(s) ? 'text-[#f5c542]' : 'text-rose-300';
            return (
              <div key={i} className="fx-tile flex flex-col items-center gap-1">
                {s.preview
                  ? <img src={`data:image/jpeg;base64,${s.preview}`} alt={T.collector.shotAlt(i + 1)} className={`w-11 h-11 rounded-full object-cover border-2 ${ring} ${i === bi ? '' : 'opacity-60'}`} />
                  : <span className={`w-11 h-11 rounded-full bg-white/5 border-2 ${ring}`} />}
                <span className={`text-[10px] font-mono ${ink}`}>{sd ?? `#${i + 1}`}</span>
              </div>
            );
          })}
          {canTakeMore && Array.from({ length: t.max_shots - n }, (_, i) => (
            <span key={`slot-${i}`} className="w-11 h-11 rounded-full border-2 border-dashed border-white/10" aria-hidden />
          ))}
        </div>
        <p className="text-[11px] text-zinc-500 mt-2">{summary}</p>
      </div>

      <div className={`grid gap-3 ${canTakeMore && use ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {canTakeMore && (
          <button onClick={onTakeAnother} className="py-3 rounded-xl bg-[#f5c542] text-black text-sm font-bold flex items-center justify-center gap-2"><Camera className="w-4 h-4" /> {T.collector.takeAnother}</button>
        )}
        {/* the best shot is not centred on an iris, or the engine blocked it: offer only another shot, never
            the studio */}
        {use && (
          <button onClick={onContinue} className={`py-3 rounded-xl text-sm flex items-center justify-center gap-2 ${canTakeMore ? 'bg-white/5 border border-white/10 font-semibold' : 'bg-[#f5c542] text-black font-bold'}`}>
            <Sparkles className="w-4 h-4" /> {n > 1 ? T.collector.useBest : T.collector.useThis}
          </button>
        )}
      </div>
      <button onClick={onStartOver} className="text-xs text-zinc-400 underline underline-offset-4 self-center">{T.collector.startOver}</button>
    </section>
  );
};
