// Price experiments on the page (server side: api/_lib/abtest.py, definitions api/_lib/experiments.py). Plain data and
// functions, no React (./usePrices.ts has the hooks), so it can be loaded in Node too.
//
// What this keeps in the browser, and when. The page asks GET /api/checkout as it always did, WITHOUT any id. Only while the
// owner has a price test running does that answer also name the markets that run one ("exp_markets"). Only a visitor whose
// market is one of them (and who has not opted out, below) gets localStorage "snapeyes.vid": a random anonymous visitor id
// ({id: 32 hex characters made here, t: the day it was made}, no personal data; kept at most 90 days; removed again as soon
// as the server says no test runs). The page then asks once more, with the id in the request header X-Snapeyes-Visitor (never
// in an address), and the server answers with the ladders of the visitor's variant and a signed token. So while no test runs,
// nothing is created, stored or sent. "snapeyes.pricing" is the last such answer (a returning visitor sees the price of
// their variant at once) and "snapeyes.expseen" says which funnel events were already sent for which run of a test, so each
// is sent once per visitor and run. "snapeyes.notest" = 1 is the visitor's opt-out ("?pricetest=off" on any page of the
// site, the link in the privacy policy; "?pricetest=on" takes part again), and a browser that sends the Global Privacy Control
// signal is out too: no id, no token, the standard prices.
// Without a working localStorage there is no visitor id, so the visitor is not part of any experiment: the page shows and
// charges the standard prices.
//
// What the server answers with an id while an experiment runs (and ordering is open): the ladders of the visitor's variant for
// the markets it covers (GET /api/checkout "markets", "prices"), the variants ("experiments") and a signed assignment token
// ("exp_token"). Every price the site prints comes from those ladders, never from a difference this file invents; the
// token is sent back with the checkout so the server prices the order from it (the client cannot name a variant), together
// with the price the page showed ("shown"), so a price that changed meanwhile is shown again instead of charged.
import { PRICE_KEYS, currentMarket, isMarket, priceList, subscribeMarket, type Market, type PriceList } from './markets';

const VID_KEY = 'snapeyes.vid';
const OPT_KEY = 'snapeyes.notest';
const CACHE_KEY = 'snapeyes.pricing';
const SEEN_KEY = 'snapeyes.expseen';
const VISITOR_HEADER = 'X-Snapeyes-Visitor';
const VID_TTL_S = 90 * 86_400;    // the visitor id lives this long at most (then a new random draw, if a test still runs)
const CACHE_MS = 10 * 60_000;     // a stored answer is used at once for this long (a fresh one is always asked for)
const HOLD_MS = 3400;             // the longest the landing page waits for the first answers before it prints the standard prices
const FETCH_MS = 3000;            // the longest the second request (the one with the id) may take
const VID_RE = /^[a-f0-9]{32}$/;
const TOKEN_RE = /^x1\.[A-Za-z0-9_-]{2,1100}\.[a-f0-9]{32}$/;

export interface Assignment { key: string; variant: string; markets: Market[]; run: number }

interface State {
  token: string | null;
  ladders: Record<Market, PriceList>;
  experiments: Assignment[];
  ready: boolean;
}

let state: State = { token: null, ladders: {}, experiments: [], ready: false };
const listeners = new Set<() => void>();
let holdTimer: ReturnType<typeof setTimeout> | null = null;
let lastPlain: unknown = null;                        // the last plain answer of GET /api/checkout (the one without an id)
let chain: Promise<unknown> = Promise.resolve();      // answers are settled one after the other

function emit(): void {
  listeners.forEach((l) => l());
}

const validLadder = (p: unknown): p is PriceList =>
  !!p && typeof p === 'object' && PRICE_KEYS.every((k) => Number.isInteger((p as Record<string, unknown>)[k]) && ((p as Record<string, number>)[k]) > 0);

// ---------------------------------------------------------------------------------------------------- the opt-out

function store(): Storage | null {
  try { return typeof window === 'undefined' ? null : window.localStorage; } catch { return null; }
}

/** Has this visitor asked to stay out of price tests: "snapeyes.notest", or the browser's Global Privacy Control signal? */
export function optedOut(): boolean {
  try {
    if (typeof window === 'undefined') return false;
    if ((window.navigator as { globalPrivacyControl?: unknown } | undefined)?.globalPrivacyControl === true) return true;
    return store()?.getItem(OPT_KEY) === '1';
  } catch { return false; }
}

/** "?pricetest=off" (or "on") in the address: the opt-out. Off removes the visitor id, the stored answer and the funnel
 *  notes and keeps "snapeyes.notest"; on removes that note. The parameter is taken out of the address afterwards. */
function readOptParam(): void {
  try {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location?.search ?? '');
    const v = params.get('pricetest');
    if (v !== 'off' && v !== 'on') return;
    const ls = store();
    if (ls) {
      if (v === 'off') {
        ls.setItem(OPT_KEY, '1');
        for (const k of [VID_KEY, CACHE_KEY, SEEN_KEY]) ls.removeItem(k);
      } else {
        ls.removeItem(OPT_KEY);
      }
    }
    params.delete('pricetest');
    const rest = params.toString();
    window.history?.replaceState?.(window.history.state, '', `${window.location.pathname ?? '/'}${rest ? `?${rest}` : ''}${window.location.hash ?? ''}`);
  } catch { /* the opt-out is best effort; the page still works */ }
}

// ---------------------------------------------------------------------------------------------------- the visitor id

function parseVid(raw: string | null): { id: string; t: number } | null {
  try {
    const j = JSON.parse(raw ?? 'null') as { id?: unknown; t?: unknown } | null;
    return j && typeof j.id === 'string' && VID_RE.test(j.id) && typeof j.t === 'number' && Number.isFinite(j.t) ? { id: j.id, t: j.t } : null;
  } catch { return null; }
}

/** The visitor's anonymous id, or null (opted out, no working storage, or none yet and create is false). A missing,
 *  damaged or expired one is replaced by a new random one when `create` is true. Callers create one only after the
 *  server said a test runs for the visitor's market. */
export function visitorId(create = true): string | null {
  try {
    const ls = store();
    if (!ls || optedOut()) return null;
    const raw = ls.getItem(VID_KEY);
    const have = parseVid(raw);
    const now = Date.now() / 1000;
    if (have && have.t <= now + 300 && now - have.t < VID_TTL_S) return have.id;
    if (raw !== null) ls.removeItem(VID_KEY);
    if (!create) return null;
    const bytes = new Uint8Array(16);
    window.crypto.getRandomValues(bytes);
    const id = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
    ls.setItem(VID_KEY, JSON.stringify({ id, t: Math.floor(now) }));
    return parseVid(ls.getItem(VID_KEY))?.id === id ? id : null;
  } catch {
    return null;
  }
}

/** No test runs: the visitor id, the stored answer and the funnel notes are removed (nothing is kept for a test that is over). */
function dropStored(): void {
  try {
    const ls = store();
    if (ls) for (const k of [VID_KEY, CACHE_KEY, SEEN_KEY]) ls.removeItem(k);
  } catch { /* nothing to remove */ }
}

// ---------------------------------------------------------------------------------------------------- what the server said

function parseLadders(info: unknown): Record<Market, PriceList> {
  const out: Record<Market, PriceList> = {};
  const markets = (info as { markets?: unknown } | null)?.markets;
  if (markets && typeof markets === 'object') {
    for (const [m, v] of Object.entries(markets as Record<string, unknown>)) {
      const p = (v as { prices?: unknown } | null)?.prices;
      if (isMarket(m) && validLadder(p)) out[m] = { ...p };
    }
  }
  return out;
}

function parseAssignments(info: unknown): Assignment[] {
  const list = (info as { experiments?: unknown } | null)?.experiments;
  if (!Array.isArray(list)) return [];
  return list.flatMap((e): Assignment[] => {
    const o = e as { key?: unknown; variant?: unknown; markets?: unknown; run?: unknown };
    if (typeof o?.key !== 'string' || typeof o.variant !== 'string' || !Array.isArray(o.markets)) return [];
    return [{ key: o.key, variant: o.variant, run: typeof o.run === 'number' && Number.isFinite(o.run) ? o.run : 0,
      markets: o.markets.filter((m): m is string => typeof m === 'string' && isMarket(m)) }];
  });
}

/** The markets the server says run a price test now (plain GET /api/checkout "exp_markets"; none when nothing runs). */
function runningMarkets(info: unknown): Market[] {
  const l = (info as { exp_markets?: unknown } | null)?.exp_markets;
  return Array.isArray(l) ? l.filter((m): m is string => typeof m === 'string' && isMarket(m)) : [];
}

/** An answer to keep: the ladders of the visitor's variant, the assignments and the token, told to the pages (they re-render
 *  with the variant's prices), and the once-per-visitor "visit" event. The server answers the standard ladders and no token
 *  when nothing applies to this visitor: then the stored answer is dropped. */
function apply(info: unknown): void {
  const token = (info as { exp_token?: unknown } | null)?.exp_token;
  const experiments = parseAssignments(info);
  const ladders = parseLadders(info);
  // an assignment is kept only whole: a token, its experiments and a valid ladder for every market they name. Anything less
  // and the page could show a price the checkout would not charge, so it is dropped (standard prices, no token)
  const ok = typeof token === 'string' && TOKEN_RE.test(token) && experiments.length > 0
    && experiments.every((e) => e.markets.length > 0 && e.markets.every((m) => !!ladders[m]));
  state = {
    token: ok ? token : null,
    ladders: ok ? ladders : {},
    experiments: ok ? experiments : [],
    ready: true,
  };
  try {
    const ls = store();
    if (ls) {
      if (ok) ls.setItem(CACHE_KEY, JSON.stringify({ t: Date.now(), token, experiments, ladders: state.ladders }));
      else ls.removeItem(CACHE_KEY);
    }
  } catch { /* the stored answer is a convenience */ }
  emit();
  noteVisit();
}

/** The second request: GET /api/checkout with the visitor id in a header. null when it fails or takes too long. */
async function fetchWithId(id: string): Promise<Record<string, unknown> | null> {
  let timer: ReturnType<typeof setTimeout> | null = null;
  try {
    const ctl = typeof AbortController === 'undefined' ? null : new AbortController();
    if (ctl) timer = setTimeout(() => ctl.abort(), FETCH_MS);
    const r = await fetch('/api/checkout', {
      method: 'GET', headers: { Accept: 'application/json', [VISITOR_HEADER]: id }, cache: 'no-store', credentials: 'same-origin',
      ...(ctl ? { signal: ctl.signal } : {}),
    });
    if (!r.ok) return null;
    const j = (await r.json()) as unknown;
    return j && typeof j === 'object' && !Array.isArray(j) ? (j as Record<string, unknown>) : null;
  } catch {
    return null;
  } finally {
    if (timer !== null) clearTimeout(timer);
  }
}

async function settle(info: unknown): Promise<unknown> {
  lastPlain = info;
  const running = runningMarkets(info);
  if (running.length === 0) {       // no test runs anywhere: nothing is created, and what an earlier test left is removed
    dropStored();
    apply(info);
    return info;
  }
  // a test runs, but not for this visitor's market (or they opted out, or their browser keeps nothing): the standard prices.
  // An id made earlier is kept (switching the currency back and forth must not re-draw the variant), but not created or sent
  if (!running.includes(currentMarket()) || optedOut()) { apply(info); return info; }
  const id = visitorId(true);
  if (!id) { apply(info); return info; }
  const again = await fetchWithId(id);
  if (again && typeof again.exp_token === 'string') { apply(again); return again; }
  apply(info);
  return info;
}

/** GET /api/checkout (the plain one, no id) answered. Resolves to the answer the page should use: the same one, or, for a
 *  visitor whose market runs a price test, the answer of the second request with the variant's ladders and token. */
export function noteCheckoutInfo(info: unknown): Promise<unknown> {
  const p = chain.then(() => settle(info), () => settle(info));
  chain = p.catch(() => undefined);
  return p;
}

/** The server could not be asked (offline, no API, payments off): the standard prices are right, print them. */
export function noteInfoUnavailable(): void {
  if (state.ready) return;
  state = { ...state, ready: true };
  emit();
}

/** A checkout answered 409 price_changed: {amount, prices, market, exp_token?}. The page shows the new price and asks
 *  again; a token the server re-signed replaces ours, none means the experiment is over for this visitor. */
export function noteChanged(reply: unknown): void {
  const r = (reply ?? {}) as { prices?: unknown; market?: unknown; exp_token?: unknown };
  const market = typeof r.market === 'string' && isMarket(r.market) ? r.market : currentMarket();
  const ladders = { ...state.ladders };
  if (validLadder(r.prices)) ladders[market] = { ...r.prices };
  const token = typeof r.exp_token === 'string' && TOKEN_RE.test(r.exp_token) ? r.exp_token : null;
  state = { ...state, ladders, token, experiments: token ? state.experiments : [] };
  emit();
}

// ---------------------------------------------------------------------------------------------------- reading

const baseLists = new Map<Market, PriceList>();
function baseList(market: Market): PriceList {
  let b = baseLists.get(market);
  if (!b) { b = priceList(market); baseLists.set(market, b); }
  return b;
}

/** The ladder this visitor is charged in a market: the variant's while an experiment runs for them there, else the
 *  standard one (src/shared/markets.ts priceList). The same object until something changes. */
export function effectiveList(market: Market): PriceList {
  return state.ladders[market] ?? baseList(market);
}

/** The token to send with a checkout (null: the standard ladder). */
export function experimentToken(): string | null {
  return state.token;
}

export function pricingReady(): boolean {
  return state.ready;
}

export function subscribePricing(fn: () => void): () => void {
  listeners.add(fn);
  if (!state.ready && holdTimer === null && typeof window !== 'undefined') {
    // the landing page waits for the first answers before it prints a price; never longer than this
    holdTimer = setTimeout(noteInfoUnavailable, HOLD_MS);
  }
  return () => { listeners.delete(fn); };
}

/** The price list the server sent for a market, merged over the standard one: for a page that got the list with its
 *  own GET /api/checkout (a partial list overrides only the keys it has). */
export function listFor(market: Market, server?: Partial<PriceList>): PriceList {
  const out = { ...effectiveList(market) };
  for (const k of PRICE_KEYS) {
    const v = server?.[k];
    if (typeof v === 'number' && Number.isInteger(v) && v > 0) out[k] = v;
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------- funnel events

type Seen = Record<string, { visit?: 1; preview?: 1 }>;

function readSeen(): Seen {
  try {
    const j = JSON.parse(store()?.getItem(SEEN_KEY) || '{}') as unknown;
    return j && typeof j === 'object' && !Array.isArray(j) ? (j as Seen) : {};
  } catch { return {}; }
}

function send(body: Record<string, unknown>): void {
  try {
    void fetch('/api/checkout', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body), cache: 'no-store', credentials: 'same-origin', keepalive: true,
    }).catch(() => { /* an event is best effort */ });
  } catch { /* no fetch: nothing to send */ }
}

/** Tell the server once per visitor and run of an experiment that this visitor was shown the variant's prices (in a market
 *  the experiment covers). No id is sent: the signed token only says which variant. */
export function noteVisit(market: Market = currentMarket()): void {
  mark('visit', market);
}

/** The visitor made a preview (eyes: how many, style: the chosen one): once per visitor and run of an experiment. */
export function notePreview(eyes: number, style: string, market: Market = currentMarket()): void {
  mark('preview', market, { eyes, style });
}

function mark(stage: 'visit' | 'preview', market: Market, extra: Record<string, unknown> = {}): void {
  if (typeof window === 'undefined' || !state.token) return;
  const seen = readSeen();
  let changed = false;
  for (const e of state.experiments) {
    const at = `${e.key}@${e.run}`;       // a new run of a test (stopped and started again) counts its visitors anew
    if (!e.markets.includes(market) || seen[at]?.[stage]) continue;
    (seen[at] ||= {})[stage] = 1;
    changed = true;
    send({ exp_event: stage, exp_token: state.token, market, ...extra });
    break;    // one experiment per market at a time (the server refuses a second one there)
  }
  if (changed) {
    try { store()?.setItem(SEEN_KEY, JSON.stringify(seen)); } catch { /* the event may repeat, never the price */ }
  }
}

// a returning visitor: the stored answer, at once, if it is recent (the page still asks the server and replaces it)
function restore(): void {
  if (typeof window === 'undefined') return;
  try {
    if (optedOut()) return;
    const c = JSON.parse(store()?.getItem(CACHE_KEY) || 'null') as { t?: number; token?: unknown; experiments?: unknown; ladders?: unknown } | null;
    if (!c || typeof c.t !== 'number' || Date.now() - c.t > CACHE_MS || typeof c.token !== 'string' || !TOKEN_RE.test(c.token)) return;
    const experiments = parseAssignments({ experiments: c.experiments });
    const ladders = parseLadders({ markets: Object.fromEntries(Object.entries((c.ladders ?? {}) as Record<string, unknown>).map(([m, p]) => [m, { prices: p }])) });
    if (experiments.length && Object.keys(ladders).length) state = { token: c.token, ladders, experiments, ready: true };
  } catch { /* no stored answer */ }
}

readOptParam();
restore();
// the visitor changed the currency: a test may run there (an id is then made), or may not (the standard prices)
if (typeof window !== 'undefined') subscribeMarket(() => { if (lastPlain !== null) void noteCheckoutInfo(lastPlain); });
