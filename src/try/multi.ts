// Pure helpers for the multi-eye result: layouts the engine accepts, the canvas shape it returns, the price
// for the eyes on the artwork, and the capture-study payloads. No React and no DOM here.
import { PRICE_CENTS } from '../landing/config';
import type { Analysis } from './shots';

/** api/_lib/iris.py MULTI_MAX: the most eyes one artwork holds. */
export const MAX_EYES = 8;

export type Layout = 'single' | 'duo' | 'fusion' | 'triangle' | 'row' | 'grid' | 'galaxy';

/** One finished eye. Only its restored iris and the small crop it came from are kept: the full-size photo
 *  is released as soon as the eye is done, so eight eyes never mean eight 12 MP photos in a phone tab. */
export interface Eye {
  id: string;
  before: string;       // data URL: the iris crop cut from the customer's photo (at most 1400 px)
  image: string;        // base64 JPEG: the restored iris square from /api/enhance (1024 px)
  thumb: string;        // data URL: a 160 px copy of image for the eye chips
  pad: number;
  fallback: boolean;
  usedSr: boolean;
  stored: boolean;
  glarePct: number;
  diameterPx?: number;
  sample: boolean;      // the site's AI-generated demo eye, never a customer's
  colourOff: boolean;   // the engine's own colour check measured this restoration as off from the photo
}

/** The colour QA /api/enhance returns (api/_lib/iris.py colour_qa). All optional: an older server sends none. */
export interface ColourQa { ring_de00?: number | null; pupil_neutral?: boolean | null; ok?: boolean }

/** True only when the engine measured the ring colour and judged it off. A QA that could not measure
 *  (ring_de00 null) says nothing about the eye, so it never raises the note. */
export const colourOff = (qa: ColourQa | null | undefined): boolean =>
  !!qa && qa.ok === false && typeof qa.ring_de00 === 'number' && Number.isFinite(qa.ring_de00);

/** The eyes an order would be for: the AI-generated sample eye is never one of them. */
export const billableEyes = (list: readonly Eye[]): number => list.filter((e) => !e.sample).length;

/** One composed preview as /api/compose returned it. */
export interface Art { src: string; w: number; h: number; layout: string }

// api/_lib/iris.py LAYOUTS, the first entry of each is the engine's default for that count
const LAYOUTS: Record<number, readonly Layout[]> = {
  1: ['single'],
  2: ['duo', 'fusion'],
  3: ['triangle', 'row'],
  4: ['grid', 'row'],
  5: ['galaxy'], 6: ['galaxy'], 7: ['galaxy'], 8: ['galaxy'],
};

export const layoutsFor = (n: number): readonly Layout[] => LAYOUTS[n] ?? [];

/** The layout n eyes will be composed in: the wanted one when n can take it, else the engine's default. */
export function effectiveLayout(n: number, want: Layout | null | undefined): Layout {
  const options = layoutsFor(n);
  return want && options.includes(want) ? want : options[0] ?? 'single';
}

/** api/_lib/iris.py multi_canvas at 1024: (W, H) of the preview before the reply says so. */
export function canvasSize(n: number, layout: Layout): { w: number; h: number } {
  const l = effectiveLayout(n, layout);
  const [a, b] = l === 'single' ? [1, 1] : l === 'duo' || l === 'fusion' ? [3, 2]
    : l === 'row' ? (n === 3 ? [2, 1] : [21, 9]) : [4, 5];
  return a >= b ? { w: 1024, h: Math.max(8, Math.round((1024 * b) / a)) } : { w: Math.max(8, Math.round((1024 * a) / b)), h: 1024 };
}

/** Side in px each restored iris is re-encoded at for /api/compose, or null to send it as it came (1024).
 *  The engine never needs more than 1.5x the pixels a disc shows: about 850 px for a duo, 650 for three or
 *  four discs, 430 for a galaxy, so these keep eight eyes far under the 4.4 MB request limit. */
export function composeSide(n: number): number | null {
  if (n <= 2) return null;
  return n <= 4 ? 768 : 560;
}

/** Price in euro cents for n eyes (owner decision 2026-09-23): one eye depends on the style, two eyes are
 *  the Couple Duo, and every eye after the second adds the same amount. */
export function priceCents(n: number, style: string): number {
  if (n <= 1) return style === 'studio_black' ? PRICE_CENTS.studioBlack : PRICE_CENTS.artBackground;
  return PRICE_CENTS.coupleDuo + (Math.min(n, MAX_EYES) - 2) * PRICE_CENTS.extraEye;
}

export { PRICE_CENTS };

const EURO = new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR' });
export const euro = (cents: number): string => EURO.format(cents / 100);

// ---- capture study (?study=1): the owner's family test

export type LightAnswer = 'window_daylight' | 'room_lamp' | 'phone_torch' | 'someone_helped';
export const LIGHT_ANSWERS: readonly LightAnswer[] = ['window_daylight', 'room_lamp', 'phone_torch', 'someone_helped'];

/** Where the analysed photo came from. 'sample' is the site's own AI-generated demo eye, not a capture. */
export type ShotOrigin = 'camera' | 'gallery' | 'live' | 'sample';

/** Sent with every /api/analyze request. w and h are the screen in CSS pixels. */
export interface DeviceInfo { ua: string; w: number; h: number; source: ShotOrigin }

/** The two answers about one analysed shot (or one gallery pick), sent with the NEXT analyze request. */
export interface StudyPayload {
  session: string;
  eye: number;          // which eye of the artwork was being captured, 1-based
  shot: number;         // the analysed shot these answers describe, counted over the whole visit, 1-based
  photos: number;       // how many photos that analysis covered (a gallery pick measures several at once)
  source: ShotOrigin;
  outcome: string;      // what the engine said about that shot: good / ok / weak / not_centred / no_eye
  light: LightAnswer | null;
  comfort: number | null;   // 1 hard .. 5 easy
}

/** Answers kept waiting at most: older ones are dropped first. Keeps the "study" object far under the
 *  engine's telemetry limits (24 fields, 1500 characters). */
export const STUDY_PENDING_MAX = 6;

/** What the engine said about one analysed shot, in one word for the study answers. A shot with no eye in it
 *  is never logged by the engine, so this word is the only trace of it. */
export function outcomeOf(a: Analysis | null | undefined): string {
  if (!a) return 'failed';
  if (!a.ok || !a.iris) return a.reason || 'no_eye';
  if (a.quality?.locked === false) return 'not_centred';
  return a.quality?.verdict || 'ok';
}

/** The "study" object of an analyze request: the newest waiting answers in the agreed shape, plus every older
 *  answer no logged analyze has carried yet as prev1, prev2, ... (newest first). The engine logs only an
 *  analyze that found an eye, so answers that rode along with a no-eye shot are sent again this way. */
export function studyBody(list: readonly StudyPayload[]): Record<string, unknown> | null {
  const ready = list.filter(studyAnswered).sort((a, b) => b.shot - a.shot).slice(0, STUDY_PENDING_MAX);
  if (!ready.length) return null;
  const [newest, ...older] = ready;
  const out: Record<string, unknown> = { ...newest };
  older.forEach(({ eye, shot, photos, source, outcome, light, comfort }, i) => {
    out[`prev${i + 1}`] = { eye, shot, photos, source, outcome, light, comfort };
  });
  return out;
}

export const studyOn = (search: string): boolean => {
  try { return new URLSearchParams(search).get('study') === '1'; } catch { return false; }
};

export function deviceInfo(source: ShotOrigin): DeviceInfo {
  const ua = typeof navigator !== 'undefined' ? String(navigator.userAgent || '').slice(0, 300) : '';
  const w = typeof screen !== 'undefined' ? screen.width : 0;
  const h = typeof screen !== 'undefined' ? screen.height : 0;
  return { ua, w, h, source };
}

/** A study payload is worth sending only when at least one question was answered. */
export const studyAnswered = (s: StudyPayload | null): s is StudyPayload =>
  !!s && (s.light !== null || s.comfort !== null);
