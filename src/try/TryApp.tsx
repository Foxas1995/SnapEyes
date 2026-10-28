import React, { useEffect, useRef, useState } from 'react';
import { Camera, Upload, Sparkles, RefreshCcw, AlertTriangle, Info, ArrowLeft, X } from 'lucide-react';
import {
  type Analysis, type Targets, targetsOf, rawFibre, bestIndex, topTip, wordsOf, mapPool,
  autoContinue, calmNote, usable, blockOf, blockCode,
} from './shots';
import {
  type ColourQa, type Eye, type Layout, type LightAnswer, type ShotOrigin, type StudyPayload,
  MAX_EYES, STUDY_PENDING_MAX, colourOff, deviceInfo, keptSealed, outcomeOf, savedEye, studyAnswered, studyBody, studyOn,
} from './multi';
import { T, setCopyLang } from './copy';
import { detectLang, rememberLang, type Lang } from './lang';
import { CROP_MAX_PX } from './crop';
import { LANG_NAMES, LOCALES, marketLangs } from '../shared/lang';
import { ResultView } from './ResultView';
import { Working } from './Working';
import { GuideVideo } from '../shared/GuideVideo';
import { usePreviews } from './usePreviews';
import { sendHelp } from './composeApi';
import { type Opts, type ServerTile, NO_OPTS, advisoryEyes, buyState, lookOf, retakeView, showsPrice } from './picker';
import type { PickerModel } from './StylePicker';
import type { WordsModel } from './Words';
import { DATE_MAX, FAMILY_MAX, NAME_MAX, drawsFamilyName, namesFromWire, namesOf, problems, typed, wireNames } from './names';
import { StudyCard } from './StudyCard';
import { RetakeGuide } from './RetakeGuide';
import { BuyCard, type Ordering } from './BuyCard';
import { NO_PRINT, printPart, type PrintChoice } from './PrintPick';
import { defaultCountry, offeredPrints } from '../shared/prints';
import {
  type CheckoutError, type CheckoutOutcome, type CheckoutStep, type OrderRef, type Snapshot, TICKET_MARGIN_MS, TICKET_MS,
  loadOrderRef, runCheckout, saveOrderRef, saveSnapshot, staleEyes, takeSnapshot,
} from './checkout';
import { callApi, type CheckoutInfo } from '../order/api';
import { experimentToken, listFor, noteChanged, noteCheckoutInfo, noteInfoUnavailable, notePreview } from '../shared/pricing';
import { priceChangedNote } from './priceNote';
import { count, note as noteCounter, withCamp } from '../shared/counter';
import { noteFeedback } from '../shared/feedback';
import { readCatalogue } from '../shared/catalogue';
import { CHECKOUT_LEGAL, LEGAL_DOCS, LEGAL_LABELS, legalHref } from '../shared/legal';
import { currencyOf, currentMarket, money, priceMinor, serverPrices, withMarket } from '../shared/markets';
import { STYLES as REGISTRY, isStyle } from '../shared/styles';
import { BrandPicture } from '../shared/BrandLogo';
import { LegalParts } from '../shared/LegalLinks';
import { NO_SAVE } from './noSave';
import { parseReveal } from '../reveal/revealMath';
import { wideFrame, type WideFrame } from '../reveal/wideFrame';

type Step = 'capture' | 'analyzing' | 'quality' | 'processing' | 'result';

// when the photo was chosen (milliseconds), for the anonymous counter's time to a preview (src/shared/counter.ts)
let photoAt = 0;

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
  let r: Response;
  let raw: string;
  try {
    r = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(withCamp({ lang: T.lang, market: currentMarket(), ...body })),
    });
    // Vercel answers a timeout or an oversized body with text/plain, so read text first and never let
    // JSON.parse throw the real status away
    raw = await r.text();
  } catch {
    // no connection, a dropped one or a blocked request: the browser's own words ("Failed to fetch", "Load failed") are English
    // on every page and mean nothing to the visitor, who waited a minute for them
    throw new Error(T.errors.notResponding);
  }
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
  // A screen that is replaced must not leave a keyboard or screen-reader user on <body> (WCAG 2.4.3): after the page has changed step once (the first screen is the page itself),
  // focus moves to the new step's heading (one h1 is on screen at a time: the capture screen's own, or the page title every other screen has). An error is announced (role="alert" on
  // the banner) and the arrival of the preview is announced by a polite live region that is always there (release review, perf-a11y M3).
  const stepHead = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (stepped) stepHead.current?.focus({ preventScroll: true });
  }, [step, stepped]);
  const [announce, setAnnounce] = useState('');
  useEffect(() => { setAnnounce(arriving ? T.result.previewReady : ''); }, [arriving]);
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
  // a print of the artwork (./PrintPick.tsx): none by default; its box is never ticked in advance either
  const [printChoice, setPrintChoice] = useState<PrintChoice>(NO_PRINT);
  const [printConsent, setPrintConsent] = useState(false);
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
  // the photo being captured is the site's own AI-generated demo eye (its studio is the prepared restoration, or the live one when that cannot be read)
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

  // the document's language, title, description and share tags follow the page's (try.html carries the English ones)
  useEffect(() => {
    try {
      document.documentElement.lang = lang;
      document.title = T.meta.title;
      const tags: [string, string][] = [
        ['meta[name="description"]', T.meta.description],
        ['meta[property="og:title"]', T.meta.title], ['meta[name="twitter:title"]', T.meta.title],
        ['meta[property="og:description"]', T.meta.description], ['meta[name="twitter:description"]', T.meta.description],
        ['meta[property="og:locale"]', LOCALES[lang].og],
      ];
      for (const [selector, value] of tags) document.head.querySelector<HTMLMetaElement>(selector)?.setAttribute('content', value);
    } catch { /* no document: nothing to label */ }
  }, [lang]);

  // the anonymous counter: /try was opened (sent once /api/health says the counter is on)
  useEffect(() => { count('try', T.lang, currentMarket()); }, []);
  // The preview watermark is drawn into the pixels of an eye's display copy, in the language of the request that made it (eye.wm). When the page speaks another language (the visitor
  // switched after the restoration, or while it ran and the answer came in the old one), the display copy is asked for again in the new one: /api/enhance {redisplay} draws it from
  // the sealed preview, no model call and no ticket, and the page swaps only the picture and its chip. One eye at a time; a Reveal eye is never given a plain copy (shown says which
  // the server made); an eye that cannot be done keeps the words it has (once per language, so there is no loop).
  const wmBusy = useRef(false);
  const wmGaveUp = useRef(new Set<string>());
  const [wmTick, setWmTick] = useState(0);
  useEffect(() => {
    if (wmBusy.current) return;
    const eye = eyes.find((e) => e.wm && e.wm !== lang && typeof e.sealed === 'string' && e.sealed && !wmGaveUp.current.has(`${e.id}:${lang}`));
    if (!eye) return;
    wmBusy.current = true;
    const want = lang;
    void (async () => {
      try {
        const r = await post<{ image?: string; shown?: string }>('/api/enhance', { redisplay: true, sealed: eye.sealed, lang: want, pad: eye.pad, ...(eye.draft?.crop ? { crop: eye.draft.crop } : {}) });
        const now = eyesRef.current.find((x) => x.id === eye.id);
        if (!now || typeof r.image !== 'string' || !r.image) return;
        if (now.reveal && r.shown !== 'reveal') { wmGaveUp.current.add(`${eye.id}:${want}`); return; }
        const thumb = await thumbOf(r.image);
        commitEyes(eyesRef.current.map((x) => (x.id === eye.id ? { ...x, image: r.image!, thumb, wm: want } : x)));
      } catch { wmGaveUp.current.add(`${eye.id}:${want}`); } finally { wmBusy.current = false; setWmTick((n) => n + 1); }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eyes, lang, wmTick]);

  // only offer the training-memory checkbox when this deployment can really store something, and the buy button only
  // when it takes orders: /api/health says whether Stripe is set up, GET /api/checkout whether ordering is open (Stripe
  // and the private store) and gives the server's prices and waiver text. Until both say yes: "ordering opens soon".
  useEffect(() => {
    let alive = true;
    fetch('/api/health')
      .then((r) => r.json())
      .then(async (h) => {
        if (!alive) return;
        noteCounter(h.counter);        // the anonymous counter (src/shared/counter.ts) sends its beacons only when the server says it counts
        noteFeedback(h.feedback);      // the feedback box (src/shared/feedback.ts) is shown only when the server says it keeps the answers
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
        setOrdering(d && d.open === true ? { open: true, prices: serverPrices(d, currentMarket()), consent: d.consent, maxEyes: orderable ? orderable.max : typeof d.max_eyes === 'number' ? d.max_eyes : undefined,
          prints: d.prints, country: typeof d.country === 'string' ? d.country : undefined } : { open: false });
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
    // a new artwork is a new decision: the waiver is asked again (the order itself is reused for its eyes), and so is the print
    setWaiver(false); setPrintChoice(NO_PRINT); setPrintConsent(false); setBuy({ busy: false, step: null, error: null });
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

  /** The selected eye in the centre of an arrangement that has one (the layout Orbit: the first eye of the order is the hub, the others go round it): it
   *  becomes the first eye, the others keep their order, and the places are not rotated any more (the server reads the order as it comes). */
  const centreEye = (id: string) => {
    const list = eyesRef.current;
    const i = list.findIndex((e) => e.id === id);
    if (i <= 0) return;
    commitEyes([list[i], ...list.slice(0, i), ...list.slice(i + 1)]);
    setSelectedId(id);
    setOpts((o) => (o.rotate ? { ...o, rotate: 0 } : o));
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
    photoAt = Date.now(); count('photo', T.lang, currentMarket());       // a photo was chosen or taken (the sample eye never comes through here)
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
    // the shot that will be processed goes on by itself whenever the studio can restore it (autoContinue): asked of that shot, never of the
    // latest one, so a later shot that cannot be used never sends the best one away and a usable best is never held back for it
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
    if (autoContinue(a)) { await process(img, a); } else { setStep('quality'); }
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
    const out = Math.min(CROP_MAX_PX, Math.round(S));
    const crop = drawToDataUrl(img, cx * W - S / 2, cy * H - S / 2, S, S, out, out, 0.95);
    setClientCrop(crop);
    let d: { crop: string; glare_pct: number; lid_pct?: number; changed: boolean; used_sr: boolean };
    let e: Enhanced;
    let wm: Lang = T.lang;
    try {
      setProgress((p) => [...p, T.working.reflections]);
      d = await post('/api/deglare', { crop: stripDataUrl(crop), pad, ticket: a.ticket, pupil_r: a.pupil_r, glare_boxes: a.glare_boxes_crop || [] });
      setProgress((p) => [...p, T.working.macro]);
      // each eye has its own storage folder, or one eye would overwrite another one's files. The language is named here, once: the watermark of the display copy is drawn in it
      // (and the eye remembers it, wm), so a switch of the page's language while this runs is seen when the answer is in
      wm = T.lang;
      e = await post<Enhanced>('/api/enhance', { crop: d.crop, mode: 'artistic', pad, ticket: a.ticket, session: `${session}-${id}`, consent, used_sr: d.used_sr, meta: a.quality, lang: wm });
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
      fallback: !!e.fallback, usedSr: !!e.used_sr, stored: !!e.stored, glarePct: d.glare_pct, lidPct: typeof d.lid_pct === 'number' ? d.lid_pct : 0,
      ...(typeof a.quality?.pupil_size === 'number' ? { pupil: a.quality.pupil_size } : {}),
      diameterPx: a.quality?.diameter_px, sample, colourOff: colourOff(e.qa), draft, wm,
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
    if (!sample) { count('result', T.lang, currentMarket(), { eyes: list.length, ...(photoAt ? { took: Date.now() - photoAt } : {}) }); photoAt = 0; }       // the restored eye is on screen: the time since the photo is the page's own
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
  // the prints this market's checkout offers now (none while the owner's switch is off, or in a market without prints)
  const printsOffered = offeredPrints(ordering?.open ? ordering.prints : undefined, market);
  const onPrintChoice = (c: PrintChoice) => {
    const p = c.product ? printsOffered.find((x) => x.id === c.product) : undefined;
    // a print chosen for the first time: the visitor's own country, when prints ship there, is preselected (the customer can change it)
    setPrintChoice(p && !c.country ? { ...c, country: defaultCountry(ordering?.country, p.ship) } : c);
  };
  const priceOf = (tl: ServerTile) => (!eyes.some((e) => e.sample) && showsPrice(eyes.length, tl) ? money(priceMinor(1, tl.id, market, priceList), currencyOf(market), T.lang) : null);
  const retakeState = catalog ? retakeView({ tiles: catalog.tiles, eyes: catalog.eyes, selected: selectedTile }) : null;
  const advisory = advisoryEyes(selectedTile, catalog?.eyes ?? []);
  const lookNow = lookOf(selectedTile, opts.look);
  // what the buy card does: the price and the button only for a style AND a look that can be bought (a Soon look under a live style is drawn, never sold)
  const buying = buyState({ n: eyes.length, tiles: catalog?.tiles ?? [], selected: selectedTile, look: lookNow });
  // the anonymous counter: the buy card showed that this cannot be bought yet (ordering is not open, or the style or the number of eyes opens soon), once per page load
  const soonRef = useRef(false);
  const buyClosed = step === 'result' && eyes.some((e) => !e.sample) && ordering !== null && (buying.kind === 'soon' || buying.kind === 'countSoon' || (buying.kind === 'normal' && !ordering.open));
  useEffect(() => {
    if (buyClosed && !soonRef.current) { soonRef.current = true; count('soon', T.lang, currentMarket(), { eyes: eyes.length, ...(style ? { style } : {}) }); }
  }, [buyClosed, eyes.length, style]);
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
    count('buy', T.lang, currentMarket(), { eyes: list.length, style });       // the buy button was pressed (anonymous counter)
    setNotice(null);
    setPriceNote(null);
    setBuy({ busy: true, step: null, error: null });
    const lay = previews.layout ?? '';
    let out: CheckoutOutcome;
    try {
      // the price on the button is what the server is asked to confirm (shown); the token names the visitor's variant
      const market = currentMarket();
      const shown = priceMinor(list.length, style, market, listFor(market, ordering?.prices));
      // the print, when one is chosen (complete: a product, its country and its box): its price and shipping as shown are only compared by the server
      const pp = printsOffered.length ? printPart(printChoice, printsOffered) : null;
      const print = pp && printChoice.product && printConsent ? { product: printChoice.product, country: printChoice.country } : null;
      // the artwork on screen, as the server described it: its plan (plan8) and the options that applied are sent back, so a checkout of something else is a 409
      out = await runCheckout({ eyes: list, style, layout: lay, names: wireNames(namesList), date, familyName: family, opts: art.opts, plan8: art.plan8, plan8Core: art.plan8Core, lang: T.lang, ref: orderRefRef.current, expToken: experimentToken(), shown,
        print, printShown: pp && print ? pp.price + pp.ship : undefined },
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
    if (out.code === 'print_unavailable') {
      // prints cannot be bought now (the owner switched them off meanwhile): the choice goes, the file alone can be ordered
      setOrdering((o) => (o ? { ...o, prints: undefined } : o));
      setPrintChoice(NO_PRINT);
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
      advisory={advisory} wordsBlocked={wordProblems.length > 0} retake={retakeState}
      stale={ordering?.open && !eyes.some((e) => e.sample) ? staleEyes(eyes, orderRef, now) : []}
      onRetake={(i) => { const e = eyes[i - 1]; if (e) retakeEye(e.id); }}
      waiver={waiver} onWaiver={setWaiver}
      prints={printsOffered} printChoice={printChoice} onPrintChoice={onPrintChoice} printConsent={printConsent} onPrintConsent={setPrintConsent}
      artSrc={art?.src}
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
      const wm: Lang = T.lang;
      const r = await post<Enhanced>('/api/enhance', { sample: true, image: stripDataUrl(file), lang: wm });
      if (typeof r.image !== 'string' || !r.image || typeof r.sealed !== 'string') throw new Error('sample preview');
      const eye: Eye = {
        id: newEyeId(), before, ...restored(r), thumb: await thumbOf(r.image), pad: SAMPLE_PAD,
        fallback: false, usedSr: false, stored: false, glarePct: 0, sample: true, colourOff: false, draft: null, wm,
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
        {/* the owner's full logo at every width (src/shared/BrandLogo.tsx): 56 px tall from 375 px, 50 px from 341 px and 44 px below, so that the logo and the
            language switch fit side by side at 320 px; its one name is the picture's alt */}
        <a href={withMarket(`/?lang=${lang}`)} className="shrink-0 flex items-center relative hit">
          <BrandPicture className="shrink-0" imgClass="block h-11 w-auto min-[341px]:h-[50px] min-[375px]:h-14" />
        </a>
        {/* the logo and the language switch, nothing else (the owner, 2026-10-22, asked what the tagline beside them meant: it is gone); the family test's badge only with ?study=1 */}
        <div className="flex items-center justify-end gap-3 min-w-0">
          {STUDY && <span className="min-w-0 text-[10px] uppercase tracking-widest text-sky-300 border border-sky-400/40 rounded-full px-2 py-0.5">{T.header.study}</span>}
          <LangSwitch lang={lang} onSwitch={switchLang} />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 pb-12">
        {/* every screen after the first has its headings below this one: the page's own title for a screen reader (the first screen has its own h1) */}
        {step !== 'capture' && <h1 ref={stepHead} tabIndex={-1} className="sr-only focus:outline-none">{T.meta.title}</h1>}
        <p role="status" data-testid="announce" className="sr-only">{announce}</p>
        {error && (
          <div role="alert" className="fx-note mb-4 bg-rose-950/40 border border-rose-500/40 text-rose-200 text-sm rounded-xl p-3 flex gap-2">
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
                <h1 ref={stepHead} tabIndex={-1} className="font-luxury text-3xl sm:text-4xl font-bold focus:outline-none">{(replaceNo ? T.capture.retakeTitle(replaceNo) : T.capture.addTitle(eyes.length + 1)).toUpperCase()}</h1>
                <p className="text-zinc-400 text-sm mt-2">{replaceNo ? T.capture.retakeLead : T.capture.addLead}</p>
                <div className="flex flex-wrap justify-center gap-x-2 gap-y-1 mt-3">
                  {eyes.map((e, i) => (
                    <span key={e.id} className="flex flex-col items-center gap-0.5 w-16">
                      <img {...NO_SAVE} src={e.thumb} alt="" className={`w-9 h-9 rounded-full object-cover ${e.id === replacing ? 'border-2 border-dashed border-gold/70 opacity-50' : 'border border-gold/40'}`} />
                      <span className={`text-[8px] leading-tight text-center ${e.sample ? 'font-semibold text-amber-200/90' : 'text-zinc-400'}`}>
                        {e.sample ? T.capture.sampleThumb : T.capture.thumbLabel(i + 1)}
                      </span>
                    </span>
                  ))}
                  {!replaceNo && <span className="w-9 h-9 rounded-full border-2 border-dashed border-gold/60" aria-hidden />}
                </div>
                <p className="text-xs text-gold/90 bg-gold/5 border border-gold/20 rounded-xl px-3 py-2 mt-3">{T.capture.takeTurns}</p>
              </div>
            ) : (
              <div className="text-center mt-2">
                <h1 ref={stepHead} tabIndex={-1} className="font-luxury text-3xl sm:text-4xl font-bold focus:outline-none">{T.capture.titleA}<span className="text-gold">{T.capture.titleB}</span></h1>
                <p className="text-zinc-400 text-sm mt-2">{T.capture.lead}</p>
              </div>
            )}

            {/* the guide video (2026-10-22, the owner: "make something like irisblink ... the clearer the better"): our own animation in the page's language, the
                square cut the landing shows too (one file, cached for both; the 9:16 cut is for phones full screen and social posts). At most 40 percent of the
                window tall, so the steps and the photo button stay on the first screen of a 412 x 915 phone; it loads and plays only on screen (src/shared/GuideVideo.tsx) */}
            <GuideVideo key={lang} src={`/assets/howto/howto-11-${lang}.mp4`} poster={`/assets/howto/howto-11-${lang}.jpg`} w={720} h={720}
              play={T.capture.videoPlay} pause={T.capture.videoPause} className="mx-auto rounded-2xl overflow-hidden border border-white/10"
              style={{ width: 'min(100%, 40vh)' }} />

            {/* on a short screen (a phone under 820 px tall) the steps come after the buttons: the way to take the photo is on the first screen, the steps are one scroll away (QA of 2026-10-20: at 360 x 740 the button was below the fold) */}
            {/* the four steps, one line each (the video shows them); the open eye, the 3-5 shots and the pair are one tap away in a closed disclosure (the owner, 2026-10-20: "a lot of text before the photo") */}
            <div data-testid="capture-guide" className="[@media(max-height:820px)]:order-last bg-[#0b0e17] border border-white/10 rounded-2xl p-4 text-sm text-zinc-300 flex flex-col gap-2">
              <ol className="flex flex-col gap-2">
                {T.capture.steps.map((s, i) => (
                  <li key={i}><span className="text-gold font-bold">{i + 1}.</span> {s}</li>
                ))}
              </ol>
              {/* the browser's own disclosure triangle: no stylesheet rule of its own (the landing's CSS budget is shared with the tools) */}
              <details data-testid="more-tips" className="border-t border-white/10 text-xs">
                <summary className="cursor-pointer py-3 min-h-[44px] font-semibold text-zinc-200">{T.capture.moreTips}</summary>
                <div className="flex flex-col gap-2 pb-1">
                  <p><span className="text-gold font-bold">{T.capture.stepsOpen}</span>{T.capture.stepsOpenMore}</p>
                  <p><span className="text-gold font-bold">{T.capture.stepsShots}</span>{T.capture.stepsShotsMore}</p>
                  {!adding && <p className="text-zinc-400">{T.capture.helper}</p>}
                </div>
              </details>
            </div>

            {/* the first camera shot starts a fresh collection */}
            <button onClick={() => { clearShots(); fileRef.current?.click(); }} className="fx-gold gold-metal w-full py-4 rounded-2xl font-luxury font-bold uppercase tracking-widest text-sm flex items-center justify-center gap-2">
              <Camera className="w-5 h-5" /> {T.capture.takePhoto}
            </button>

            <div className={`grid gap-3 ${offerSample ? 'grid-cols-2' : 'grid-cols-1'}`}>
              <button onClick={() => galleryRef.current?.click()} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                <Upload className="w-4 h-4 text-gold" /> {T.capture.pickShots}
              </button>
              {offerSample && (
                <button onClick={trySample} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-white/10">
                  <Sparkles className="w-4 h-4 text-gold" /> {T.capture.sampleButton}
                </button>
              )}
            </div>

            {/* whose eye may be photographed (the terms of sale), and where the photo goes */}
            <p data-testid="photo-notice" className="text-[10px] leading-relaxed text-zinc-400 text-center">
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

        {/* Only a photo the studio cannot restore stops here (a usable one goes straight on: autoContinue), or a usable one whose restoration just failed (the
            error above says why, and it can be tried again). No verdict, no Detail meter and no list of tips (the owner, 2026-10-22): the reason in one line
            and, for a photo the engine blocked, the retake steps for that reason. The numbers stay in the analysis (the ranking, the server's log, the admin). */}
        {step === 'quality' && analysis?.quality && shots.length === 0 && (
          <section data-testid="quality-step" className={`flex flex-col gap-4${stepped ? ' fx-step' : ''}`}>
            <div className="flex gap-4 items-center bg-[#0b0e17] border border-white/10 rounded-2xl p-4">
              {analysis.preview && <img src={`data:image/jpeg;base64,${analysis.preview}`} alt={T.quality.detectedIris} className="shrink-0 w-[120px] h-[120px] rounded-full border border-gold/40 object-cover" />}
              {/* blocked: the one-line reason (the retake steps are in the guide below: the server's message lists them too); not centred: the server's own line */}
              {!usable(analysis) && <p data-testid="quality-reason" className="min-w-0 text-sm text-zinc-200">{blockOf(analysis)?.reason ?? wordsOf(analysis.quality).message}</p>}
            </div>
            {/* the best of a gallery pick still cannot be used: never say "used" */}
            {analysis.picked && !usable(analysis) && <p className="text-xs text-rose-200/90 bg-rose-950/25 border border-rose-500/30 rounded-xl p-3">{T.quality.noneUsable(analysis.picked.of)}</p>}
            {blockOf(analysis) && <RetakeGuide block={blockOf(analysis)!} code={blockCode(analysis)} />}
            <div className={`grid gap-3 ${usable(analysis) ? 'grid-cols-2' : 'grid-cols-1'}`}>
              <button onClick={retake} className="py-3 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2"><RefreshCcw className="w-4 h-4" /> {T.quality.retake}</button>
              {/* no way forward from a crop that is not an iris, nor from one the engine blocked: the studio
                  would invent one, and the server gave neither a work ticket */}
              {usable(analysis) && (
                <button data-testid="quality-again" onClick={() => imgRef.current && process(imgRef.current, analysis)} className="py-3 rounded-xl gold-metal text-sm font-bold flex items-center justify-center gap-2"><Sparkles className="w-4 h-4" /> {T.result.retry}</button>
              )}
            </div>
            {backLink}
          </section>
        )}

        {step === 'processing' && (
          <Working title={working.eye > 1 ? T.working.restoringEye(working.eye) : T.working.restoring} lines={progress} elapsed={elapsed} image={clientCrop}
            caption={working.sample ? T.working.sampleCaption : undefined} enter={stepped}
            note={calmNote(analysis?.quality) ?? undefined} />
        )}

        {step === 'result' && STUDY && !studyAsk && pendingShots.length > 0 && (
          <p data-testid="study-pending" className="mb-4 text-xs text-sky-200 bg-sky-950/30 border border-sky-400/30 rounded-xl p-3">
            {T.study.pending(pendingShots)}
          </p>
        )}

        {step === 'result' && eyes.length > 0 && (
          <ResultView
            eyes={eyes} selectedId={selectedId} onSelect={setSelectedId} onRemove={removeEye} onRetake={retakeEye} onAdd={addEye} onMove={moveEye} onCentre={centreEye}
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
            <a key={d} href={legalHref(d, lang)} target="_blank" rel="noopener" className="relative hit hit-s hover:text-white hover:underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold rounded-sm">
              {LEGAL_LABELS[lang][d]}
            </a>
          ))}
        </nav>
      </footer>

      {step === 'result' && undo && (
        <div role="status" className="fx-toast fixed bottom-4 inset-x-4 z-40 mx-auto max-w-sm bg-zinc-900 border border-white/15 rounded-xl pl-4 pr-1 flex items-center justify-between gap-3 text-sm text-zinc-100 shadow-lg shadow-black/50">
          <span>{T.result.removed(undo.index + 1)}</span>
          <button onClick={undoRemove} className="min-h-[44px] min-w-[44px] px-3 font-bold text-gold underline underline-offset-4">{T.result.undo}</button>
        </div>
      )}
    </div>
  );
};

/** The language switch, as on the landing page (src/landing/Header.tsx LangSwitch): one button per language the page's
 *  market can be read in. Its buttons are narrower on small phones so that the switch never meets the logo: below 340 px with up to four
 *  languages, below 400 px with five (the euro market since Croatian, 2026-10-28: five full buttons are 206 px, which met the logo up to 375 px). */
const LangSwitch: React.FC<{ lang: Lang; onSwitch: (l: Lang) => void }> = ({ lang, onSwitch }) => {
  const langs = marketLangs(currentMarket());
  const narrow = langs.length > 4 ? 'max-[400px]:min-w-[28px] max-[400px]:px-1.5' : 'max-[340px]:min-w-[28px] max-[340px]:px-1.5';
  return (
    <div role="group" aria-label={T.switchLabel} className="shrink-0 flex items-center rounded-full border border-white/10 p-0.5 text-[11px] font-semibold tracking-[0.12em]">
      {langs.map((l) => (
        <button key={l} type="button" onClick={() => onSwitch(l)} aria-pressed={lang === l} lang={l} title={LANG_NAMES[l]}
          className={`relative hit min-w-[40px] rounded-full px-2.5 py-1.5 ${narrow} uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold ${lang === l ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'}`}>
          {l}
        </button>
      ))}
    </div>
  );
};


/** The camera shot collector. A shot the studio can restore goes on by itself (autoContinue), so this is on screen only while no shot of the set
 *  can be used (the retake steps of the latest blocked shot, or the one line of a shot whose circle did not lock), or when the restoration of a
 *  usable best shot just failed (the error above says why; the one way on is to try it again). No verdict, no Detail: the shots so far, the best one
 *  ringed, a way to shoot again or to go on. */
const ShotCollector: React.FC<{
  shots: Analysis[]; t: Targets; note: string | null;
  onTakeAnother: () => void; onContinue: () => void; onStartOver: () => void; canUse?: boolean; enter?: boolean;
}> = ({ shots, t, note, onTakeAnother, onContinue, onStartOver, canUse = true, enter = false }) => {
  const n = shots.length;
  const latest = shots[n - 1];
  const q = latest.quality;
  const bi = bestIndex(shots);
  const best = shots[bi];
  const full = n >= t.max_shots;
  const bestUsable = usable(best);
  const use = canUse && bestUsable;
  // Prompting ends when the shot we would process can be restored (it goes on by itself; it is here only after a failed restoration). Judged on the
  // best shot, not the latest. A full set with nothing usable in it still takes another shot, which starts a fresh set (onCameraShot).
  const canTakeMore = !autoContinue(best) && (!full || !bestUsable);
  // nothing usable yet and the latest shot was blocked: the retake card with the steps for its reason (the one the customer just saw fail)
  const guide = !bestUsable ? blockOf(latest) : null;
  // the latest shot's one line (a circle that did not lock), unless the retake card already says it (the server's message lists the same steps)
  const tip = q && canTakeMore && !guide ? topTip(q, t) : null;
  const bestLabel = T.collector.bestLabel(bi + 1);
  // the one case where the latest shot was a lamp-tinted one and the best is not: say which is used
  const skippedForLamp = bi !== n - 1 && !!q?.lamp_cast && !best.quality?.lamp_cast;
  const summary = !bestUsable ? (full ? T.quality.fullUnusable(t.max_shots) : n === 1 ? T.quality.shotUnusable : T.quality.shotsUnusable)
    : full ? T.collector.full(t.max_shots, bestLabel)
    : n === 1 ? (canTakeMore ? T.collector.more(t.max_shots - 1) : T.collector.sharpEnough)
    : bi === n - 1 ? T.collector.bestSoFar
    : skippedForLamp ? T.collector.lampSkipped(n, bestLabel)
    : T.collector.bestIs(bestLabel);
  return (
    <section data-testid="shot-collector" className={`flex flex-col gap-4${enter ? ' fx-step' : ''}`}>
      <div className="flex gap-4 items-center bg-[#0b0e17] border border-white/10 rounded-2xl p-4">
        {latest.preview
          ? <img src={`data:image/jpeg;base64,${latest.preview}`} alt={T.collector.shotAlt(n)} className="shrink-0 w-24 h-24 rounded-full border border-gold/40 object-cover" />
          : <span className="shrink-0 w-24 h-24 rounded-full bg-white/5" />}
        <p className="min-w-0 text-sm font-bold text-zinc-100">{T.collector.header(n, t.max_shots)}</p>
      </div>

      {note && (
        <p className="text-xs text-amber-200/90 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3">
          {T.collector.lastFailed(note)}
        </p>
      )}
      {tip && (
        <p className="text-sm text-zinc-200 bg-white/5 border border-white/10 rounded-xl p-3 flex gap-2">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-gold" /> <span>{tip}</span>
        </p>
      )}
      {/* nothing usable and the latest shot blocked: the capture guide's steps for the next one. Its title says
          why; the server's message is left out because it lists the same steps */}
      {guide && <RetakeGuide block={guide} code={blockCode(latest)} />}

      <div>
        <div className="flex items-start gap-3">
          {shots.map((s, i) => {
            // a blocked shot's thumbnail names its reason in one word; every other one its number
            const word = blockOf(s)?.thumb;
            // the best shot is ringed in gold only when it is one we would really use
            const ring = i !== bi ? 'border-white/10' : usable(s) ? 'border-gold' : 'border-rose-400/70';
            const ink = i !== bi ? (usable(s) ? 'text-zinc-400' : 'text-rose-300/70') : usable(s) ? 'text-gold' : 'text-rose-300';
            return (
              <div key={i} className="fx-tile flex flex-col items-center gap-1">
                {s.preview
                  ? <img src={`data:image/jpeg;base64,${s.preview}`} alt={T.collector.shotAlt(i + 1)} className={`w-11 h-11 rounded-full object-cover border-2 ${ring} ${i === bi ? '' : 'opacity-60'}`} />
                  : <span className={`w-11 h-11 rounded-full bg-white/5 border-2 ${ring}`} />}
                <span className={`text-[10px] font-mono ${ink}`}>{word ?? `#${i + 1}`}</span>
              </div>
            );
          })}
          {canTakeMore && Array.from({ length: t.max_shots - n }, (_, i) => (
            <span key={`slot-${i}`} className="w-11 h-11 rounded-full border-2 border-dashed border-white/10" aria-hidden />
          ))}
        </div>
        <p className="text-[11px] text-zinc-400 mt-2">{summary}</p>
      </div>

      <div className={`grid gap-3 ${canTakeMore && use ? 'grid-cols-2' : 'grid-cols-1'}`}>
        {canTakeMore && (
          <button onClick={onTakeAnother} className="py-3 rounded-xl gold-metal text-sm font-bold flex items-center justify-center gap-2"><Camera className="w-4 h-4" /> {T.collector.takeAnother}</button>
        )}
        {/* the best shot is not centred on an iris, or the engine blocked it: offer only another shot, never
            the studio */}
        {use && (
          <button onClick={onContinue} className={`py-3 rounded-xl text-sm flex items-center justify-center gap-2 ${canTakeMore ? 'bg-white/5 border border-white/10 font-semibold' : 'gold-metal font-bold'}`}>
            <Sparkles className="w-4 h-4" /> {n > 1 ? T.collector.useBest : T.collector.useThis}
          </button>
        )}
      </div>
      <button onClick={onStartOver} className="text-xs text-zinc-400 underline underline-offset-4 self-center">{T.collector.startOver}</button>
    </section>
  );
};
