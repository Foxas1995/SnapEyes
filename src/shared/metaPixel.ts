// The Meta (Facebook) pixel, the pages' half (the owner's decision of 2026-11-25: the pixel and the Conversions API "the way TaleInTune does it", for
// everyone, with no cookie banner; the privacy policy says what it does, src/legal/docs/privacy*.ts section "meta"). The server's half is api/_lib/meta.py.
//
// WHERE AND HOW. /try and the legal pages load Meta's script (connect.facebook.net/en_US/fbevents.js) once the page has loaded and the browser is idle, never
// before (it must not delay the page): startPixel('script'). The landing page does the same with an inline script of its head (src/landing/shell/scripts.ts
// pixelScript), so the landing's own JavaScript does not grow. The order page and the gift page never load it: their address holds the order's key or the
// voucher's payment, which Meta's script would read and send with every event, so they send each event as one request to www.facebook.com/tr that names the
// page's path and nothing of its query (startPixel('image'); their HTML sends no referrer either). Off /admin. Nothing at all when the dataset id is empty
// (PIXEL_ID, from api/_lib/meta.py PIXEL_ID or META_PIXEL_ID at build time: vite.config.ts) or the page is not served from snapeyes.com (a Preview, a local
// server, the checks: nothing reaches Meta from them).
//
// WHAT. PageView on every page that starts it; ViewContent when /try opens; Lead when a free preview was shown; InitiateCheckout when the visitor leaves for
// Stripe's payment page; Purchase when the order page, the print's way back or the gift page confirm a payment, with the event id the server's Conversions API
// uses for the same payment (purchaseId, voucherPurchaseId). An event carries its name and at most these: content_category ("artwork", "voucher", "print"),
// value and currency, and the event id: params() lets nothing else through, so nothing about the photo, the iris, the eye colour, the style, the names or any
// image can ever be sent. Meta's automatic configuration is switched off (autoConfig false): no button texts, no form fields, no automatic advanced matching.
// No page of the site holds the buyer's e-mail address, so the pixel does no advanced matching at all; the server sends the hashed address (api/_lib/meta.py).
//
// WHAT IT KEEPS. Meta's script sets the cookie _fbp (and _fbc when the address carries a "fbclid" click id). When the address carries a click id and there is
// no _fbc, this keeps "fb.1.<time>.<click id>" in sessionStorage "snapeyes.fbc" (the tab's life), so the checkout can still send it. metaIds() is what the
// three checkouts send (src/order/api.ts callApi): fbp and fbc, well formed or not at all.

declare const __META_PIXEL_ID__: string | undefined;

/** The dataset id the build wrote in (vite.config.ts define), '' when there is none: the whole module is then a no-op. */
export const PIXEL_ID: string = typeof __META_PIXEL_ID__ === 'string' ? __META_PIXEL_ID__ : '';
/** Only the site itself reports to Meta. */
export const PIXEL_HOSTS = /^(www\.)?snapeyes\.com$/;
export const SCRIPT_URL = 'https://connect.facebook.net/en_US/fbevents.js';
export const EVENTS_URL = 'https://www.facebook.com/tr';
export const FBC_KEY = 'snapeyes.fbc';
export const CATEGORIES = ['artwork', 'voucher', 'print'] as const;
export type Category = (typeof CATEGORIES)[number];
export type PixelEvent = 'PageView' | 'ViewContent' | 'Lead' | 'InitiateCheckout' | 'Purchase';
export type PixelMode = 'script' | 'image';
/** What an event may say: its category and, for a payment, the amount in the currency's smallest unit (cents) and the currency. */
export interface EventData { category?: Category; minor?: number; currency?: string }

const FBP_RE = /^fb\.[0-9]\.[0-9]{10,14}\.[0-9]{1,30}$/;
const FBC_RE = /^fb\.[0-9]\.[0-9]{10,14}\.[A-Za-z0-9_-]{8,300}$/;
const CLICK_RE = /^[A-Za-z0-9_-]{8,300}$/;
const WAIT_MAX = 20;

type Fbq = ((...a: unknown[]) => void) & { callMethod?: (...a: unknown[]) => void; queue: unknown[]; push?: unknown; loaded?: boolean; version?: string };
type W = Window & { fbq?: Fbq; _fbq?: Fbq };

const state = { id: PIXEL_ID, mode: null as PixelMode | null, started: false };
const waiting: [PixelEvent, Record<string, string | number>, string | undefined][] = [];

/** The suites only: another dataset id (the build's is '' outside a build), and the state of a fresh page. */
export function resetPixelForTests(id: string): void {
  state.id = id;
  state.mode = null;
  state.started = false;
  waiting.length = 0;
}

/** Does this page report to Meta at all: a dataset id, and the site's own host. */
export function pixelOn(): boolean {
  try { return /^[0-9]{5,20}$/.test(state.id) && PIXEL_HOSTS.test(location.hostname); } catch { return false; }
}

/** The parameters of an event, and nothing else (see above). */
export function params(d: EventData = {}): Record<string, string | number> {
  const out: Record<string, string | number> = {};
  if (d.category && (CATEGORIES as readonly string[]).includes(d.category)) out.content_category = d.category;
  if (typeof d.minor === 'number' && Number.isFinite(d.minor) && d.minor >= 0) out.value = Math.round(d.minor) / 100;
  if (typeof d.currency === 'string' && /^[A-Za-z]{3}$/.test(d.currency)) out.currency = d.currency.toUpperCase();
  return out;
}

/** The event id of a payment's Purchase (api/_lib/meta.py event_id): purchase_<Stripe session id>. */
export const purchaseId = (sid: string): string => `purchase_${sid}`;

/** A gift voucher's: its session id shows the code, so Meta gets the first 32 hex characters of its SHA-256 instead (api/_lib/meta.py event_id). */
export async function voucherPurchaseId(sid: string): Promise<string | null> {
  try {
    const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(sid));
    return 'purchase_' + [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 32);
  } catch { return null; }
}

/** A payment of Stripe's test mode (a Preview's test order) is never reported. */
export const livePayment = (sid: string | null | undefined): sid is string => typeof sid === 'string' && sid.startsWith('cs_live_');

function cookie(name: string): string {
  try {
    const hit = document.cookie.split('; ').find((c) => c.startsWith(`${name}=`));
    return hit ? decodeURIComponent(hit.slice(name.length + 1)) : '';
  } catch { return ''; }
}

/** The values a checkout sends for the Conversions API (api/_lib/meta.py checkout_meta): the _fbp cookie, and the _fbc cookie or the click id this tab
 *  kept. Nothing when the pixel is off here. */
export function metaIds(): { fbp?: string; fbc?: string } {
  if (!pixelOn()) return {};
  const fbp = cookie('_fbp');
  let fbc = cookie('_fbc');
  if (!fbc) { try { fbc = sessionStorage.getItem(FBC_KEY) ?? ''; } catch { /* no storage */ } }
  return { ...(FBP_RE.test(fbp) ? { fbp } : {}), ...(FBC_RE.test(fbc) ? { fbc } : {}) };
}

/** A click id in the address, and no _fbc yet: kept for the checkout (sessionStorage "snapeyes.fbc"). */
function keepClick(): void {
  try {
    const id = new URLSearchParams(location.search).get('fbclid') ?? '';
    if (CLICK_RE.test(id) && !cookie('_fbc')) sessionStorage.setItem(FBC_KEY, `fb.1.${Date.now()}.${id}`);
  } catch { /* nothing kept */ }
}

/** One event as a request to www.facebook.com/tr: the page's address without its query, the event id, the parameters, the cookies' values. */
function request(name: PixelEvent, p: Record<string, string | number>, eid?: string): void {
  try {
    const q = new URLSearchParams({ id: state.id, ev: name, dl: location.origin + location.pathname, ts: String(Date.now()) });
    if (eid) q.set('eid', eid);
    for (const [k, v] of Object.entries(p)) q.set(`cd[${k}]`, String(v));
    const ids = metaIds();
    if (ids.fbp) q.set('fbp', ids.fbp);
    if (ids.fbc) q.set('fbc', ids.fbc);
    const url = `${EVENTS_URL}?${q.toString()}`;
    // keepalive: the request outlives the page, so an event sent as the page leaves for Stripe still arrives
    if (typeof fetch === 'function') { void fetch(url, { mode: 'no-cors', keepalive: true, credentials: 'include' }).catch(() => undefined); return; }
    new Image().src = url;
  } catch { /* never the page's failure */ }
}

function send(name: PixelEvent, p: Record<string, string | number>, eid?: string): void {
  const w = window as W;
  if (state.mode === 'script' && w.fbq) {
    try { w.fbq('track', name, p, ...(eid ? [{ eventID: eid }] : [])); } catch { /* never the page's failure */ }
  } else request(name, p, eid);
}

function loadScript(): void {
  const w = window as W;
  if (!w.fbq) {
    const n = function (...a: unknown[]) { if (n.callMethod) n.callMethod.apply(n, a); else n.queue.push(a); } as Fbq;
    if (!w._fbq) w._fbq = n;
    n.push = n; n.loaded = true; n.version = '2.0'; n.queue = [];
    w.fbq = n;
    const s = document.createElement('script');
    s.async = true;
    s.src = SCRIPT_URL;
    document.head.appendChild(s);
  }
  // no automatic events, no reading of buttons or form fields, no automatic advanced matching
  w.fbq!('set', 'autoConfig', false, state.id);
  w.fbq!('init', state.id);
  w.fbq!('track', 'PageView');
}

/** Start the pixel on this page (once): after the page has loaded and the browser is idle (at the latest 6 s after it was asked), PageView, then what waited. */
export function startPixel(mode: PixelMode): void {
  if (state.mode || !pixelOn()) return;
  state.mode = mode;
  keepClick();
  const go = () => {
    if (state.started || state.mode !== mode || !pixelOn()) return;
    state.started = true;
    if (mode === 'script') { try { loadScript(); } catch { /* never the page's failure */ } } else request('PageView', {});
    for (const [name, p, eid] of waiting.splice(0)) send(name, p, eid);
  };
  try {
    const idle = () => {
      const ric = (window as Window & { requestIdleCallback?: (cb: () => void, o?: { timeout: number }) => number }).requestIdleCallback;
      if (ric) ric(go, { timeout: 3000 }); else setTimeout(go, 1000);
    };
    if (document.readyState === 'complete') idle(); else window.addEventListener('load', idle, { once: true });
    setTimeout(go, 6000);
  } catch { go(); }
}

/** Report one event. leaving: the page is about to go to Stripe's payment page: the event goes out now, as a request that outlives the page. */
export function track(name: Exclude<PixelEvent, 'PageView'>, data: EventData = {}, eid?: string, leaving = false): void {
  if (!pixelOn()) return;
  const p = params(data);
  if (leaving) { request(name, p, eid); return; }
  if (state.started) send(name, p, eid);
  else if (state.mode && waiting.length < WAIT_MAX) waiting.push([name, p, eid]);
}
