// The page's side of POST /api/compose (api/compose.py): the request body of a set of eyes, and what the server's answers mean. No React here.
//
// One set of eyes is asked about in up to three ways, all through compose(): the tile list alone (styles: [], no pixel), one style at 1024 px (the
// large preview) and a few styles at 480 px (tiles, two at a time). The irises always go as the server sealed them (it opens them itself): the page
// never holds a clean restoration. Only an eye from before sealed previews (brought back from the payment page by the previous release) goes as an
// image, its own, at the size the server's request limit allows.
import { callApi, type ApiReply } from '../order/api';
import type { Eye } from './multi';
import { composeSide, sealedFor } from './multi';
import type { Lang } from './lang';
import { T } from './copy';

/** What a compose call came to. busy: another render holds this instance, ask again after retryAfter seconds; paused: this instance's ceiling of
 *  pictures for today is reached (not worth retrying now); unavailable: the server will not draw this style for these eyes (stage, eyes, gate,
 *  reseal, bar_pupil), so the page's tile list is out of date; too_many: the batch was too big, max fits. */
export type Outcome<D> =
  | { kind: 'ok'; data: D }
  | { kind: 'busy'; retryAfter: number; message: string }
  | { kind: 'paused'; message: string }
  | { kind: 'unavailable'; why: string; style: string; message: string }
  | { kind: 'too_many'; max: number }
  | { kind: 'error'; message: string; status: number };

const isObj = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);

/** An ApiReply of /api/compose as an Outcome. The sentences of a refusal come from the server in the page's language (the request carries it). */
export function outcomeOf<D>(r: ApiReply<D>): Outcome<D> {
  if (r.ok && r.data) return { kind: 'ok', data: r.data };
  const d: Record<string, unknown> = isObj(r.data) ? r.data : {};
  const message = r.error || (r.status === 413 ? T.errors.tooLarge : r.status === 504 ? T.errors.timeout : r.status === 0 ? T.errors.notResponding : T.errors.requestFailed(r.status));
  if (r.status === 503 && (r.reason === 'busy_retry' || r.reason === 'plate_retry')) {
    return { kind: 'busy', retryAfter: r.retryAfter || (typeof d.retry_after === 'number' ? d.retry_after : 3), message };
  }
  if (r.status === 503 && r.reason === 'tiles_paused') return { kind: 'paused', message };
  if (r.status === 422 && r.reason === 'style_unavailable') {
    return { kind: 'unavailable', why: typeof d.why === 'string' ? d.why : 'stage', style: typeof d.style === 'string' ? d.style : '', message };
  }
  if (r.status === 422 && r.reason === 'too_many_styles') return { kind: 'too_many', max: typeof d.max === 'number' ? d.max : 1 };
  return { kind: 'error', message, status: r.status };
}

/** What every request of one set of eyes carries. */
export interface Ctx {
  eyes: readonly Eye[];
  lang: Lang;
  market: string | null;
  /** an eye's image re-encoded at a side, for an eye without a sealed copy (TryApp sizedIris) */
  sized: (e: Eye, side: number | null) => Promise<string>;
}

/** The part of the body that names the eyes: the sealed irises in canvas order (the size composeSide asks for: the server sealed them at those),
 *  or, for an artwork holding an eye from before sealed previews, each eye's own image. */
export async function eyesBody(ctx: Ctx): Promise<Record<string, unknown>> {
  const list = ctx.eyes;
  const n = list.length;
  const sealed = list.map((e) => sealedFor(e, n));
  const pad = list[0]?.pad ?? 1.12;
  const body: Record<string, unknown> = sealed.every((s): s is string => !!s)
    ? { sealed, pad }
    : { irises: await Promise.all(list.map((e) => ctx.sized(e, composeSide(n)))), pad };
  // the sample eye's label goes into the picture itself (the caption title), so a saved preview keeps it
  if (list.some((e) => e.sample)) body.title = T.result.sampleTitle;
  return body;
}

export interface CallOptions { timeoutMs?: number; api?: typeof callApi }

/** One call of /api/compose for these eyes. extra: style or styles, size, layout, names, date, family_name, opts, retake, again. */
export async function composeCall<D = Record<string, unknown>>(ctx: Ctx, extra: Record<string, unknown>, o: CallOptions = {}): Promise<Outcome<D>> {
  const body = { lang: ctx.lang, ...(ctx.market ? { market: ctx.market } : {}), ...(await eyesBody(ctx)), ...extra };
  const api = o.api ?? callApi;
  return outcomeOf(await api<D>('/api/compose', { body, timeoutMs: o.timeoutMs ?? 60_000 }));
}

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

/** Ask again while the server says it is busy (up to `tries` more times, waiting as long as it asks, at most 20 s), so a moment of load shows as a
 *  slightly longer wait and not as a failure. `go` says whether the answer is still wanted (the eyes may have changed meanwhile). */
export async function persist<D>(call: () => Promise<Outcome<D>>, go: () => boolean = () => true, tries = 3, wait: (ms: number) => Promise<void> = sleep): Promise<Outcome<D>> {
  let out = await call();
  for (let i = 0; i < tries && out.kind === 'busy' && go(); i++) {
    await wait(Math.min(20, Math.max(1, out.retryAfter)) * 1000);
    if (!go()) break;
    out = await call();
  }
  return out;
}

/** One click on the manual route of the retake state (the e-mail link), counted by the server: a count and nothing else (api/compose.py action
 *  help). Best effort: it never throws and never waits. */
export function sendHelp(f: { route: 'manual'; eyes: number; why: string; lang: Lang }): void {
  try {
    void fetch('/api/compose', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ action: 'help', route: f.route, eyes: f.eyes, why: f.why, lang: f.lang }), keepalive: true, credentials: 'same-origin',
    }).catch(() => { /* a count is best effort */ });
  } catch { /* no fetch: nothing to count */ }
}

/** The picture a tile or a one-style reply carries, as the page keeps it (null when there is none: a tile that was held back). */
export interface Picture { src: string; w: number; h: number; layout: string; canvas: string | null; design: string | null; fallback: string | null; plan8: string | null; opts: Record<string, unknown> }

export function pictureOf(r: unknown, opts: Record<string, unknown> = {}): Picture | null {
  if (!isObj(r) || typeof r.image !== 'string' || !r.image) return null;
  return {
    src: `data:image/jpeg;base64,${r.image}`, w: typeof r.width === 'number' ? r.width : 0, h: typeof r.height === 'number' ? r.height : 0,
    layout: typeof r.layout === 'string' ? r.layout : '', canvas: typeof r.canvas === 'string' ? r.canvas : null,
    design: typeof r.design_used === 'string' ? r.design_used : null, fallback: typeof r.fallback === 'string' ? r.fallback : null,
    plan8: typeof r.plan8 === 'string' ? r.plan8 : null, opts: isObj(r.opts) ? r.opts : opts,
  };
}
