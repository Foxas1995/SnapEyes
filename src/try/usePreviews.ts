// The previews of /try, asked of the server in the order the plan gives (INTEGRATION_SPEC 2.8): for one set of eyes first the tile list alone (no pixel:
// which styles exist for this many eyes, which is recommended, which are held back and why), then the style on screen at 1024 px (the large preview), then
// the other tiles at 480 px, two at a time. The page owns no list of styles and decides nothing about them: it keeps what the server answered and
// src/try/picker.ts turns it into what is shown. Every answer is checked against the eyes that are on screen NOW, so a reply for eyes that were removed or
// retaken meanwhile is dropped. Refs (not effect-local flags) say what is current, so React's double effects in development ask nothing twice.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Art, Eye } from './multi';
import type { Lang } from './lang';
import { T } from './copy';
import { composeCall, persist, pictureOf, type Ctx, type Outcome } from './composeApi';
import { composeNames } from './names';
import {
  type Catalog, type Changed, type Opts, type ServerTile,
  artKey, defaultLook, layoutOf, nextTiles, parseCatalog, resolveStyle, setKey, wireOpts,
} from './picker';

const BIG_MAX = 12;      // large previews kept per page: enough to flip between styles and layouts without a new request
const TILE_MAX = 40;     // tile pictures kept
const BATCH = 2;         // tiles asked for in one call ("loading two at a time")

export interface PreviewInput {
  active: boolean;                                   // the result screen is up and there are eyes
  eyes: Eye[];
  lang: Lang;
  market: string | null;
  want: string | null;                               // the style the customer chose (null: none yet, the recommended tile is shown)
  layoutWant: string | null;
  names: string[];                                   // a name per eye in canvas order, as typed
  date: string;
  family: string;
  opts: Opts;
  retakes: { current: number };                      // a ref: eyes replaced since the last set of eyes was asked about (the funnel's "retake")
  sized: Ctx['sized'];
  eyesOf: (id: string) => readonly [number, number] | null;
}

export interface Previews {
  catalog: Catalog | null;                           // the tile list for exactly these eyes (null while it is asked for)
  catalogError: string | null;
  style: string | null;
  changed: Changed | null;
  selected: ServerTile | undefined;
  layout: string | null;
  art: Art | undefined;                              // the large preview of exactly the current choice
  staleArt: Art | undefined;                         // what to show until it is there: the tile's picture, else the last preview of these eyes
  composeError: string | null;
  tilePicture: (t: ServerTile) => Art | undefined;
  tileBusy: (t: ServerTile) => boolean;
  tileFailed: (t: ServerTile) => boolean;
  tilesPaused: string | null;                        // the server's sentence when it makes no more pictures today
  retryCompose: () => void;
  retryTiles: () => void;
  retryCatalog: () => void;
  refresh: () => void;                               // ask for the tile list again (a checkout refused the style, or the plan changed)
}

const trim = <V,>(m: Record<string, V>, max: number): Record<string, V> => {
  const e = Object.entries(m);
  return e.length > max ? Object.fromEntries(e.slice(-max)) : m;
};

export function usePreviews(p: PreviewInput): Previews {
  const n = p.eyes.length;
  const key = useMemo(() => p.eyes.map((e) => e.id).join('.'), [p.eyes]);
  const keyRef = useRef(key);
  const bigRef = useRef<string | null>(null);
  const inflight = useRef(new Set<string>());
  const seen = useRef(new Set<string>());                    // sets of eyes already asked about (the funnel counts a set once)
  const unavailableOnce = useRef(new Set<string>());
  const pausedRef = useRef<string | null>(null);
  const catalogMissing = useRef(false);
  const eyesRef = useRef(p.eyes);
  const langRef = useRef(p.lang);
  const sizedRef = useRef(p.sized);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catErr, setCatErr] = useState<{ key: string; message: string } | null>(null);
  const [bigs, setBigs] = useState<Record<string, Art>>({});
  const [bigFail, setBigFail] = useState<Record<string, string>>({});
  const [tiles, setTiles] = useState<Record<string, Art>>({});
  const [tileFail, setTileFail] = useState<Record<string, true>>({});
  const [busy, setBusy] = useState<Record<string, true>>({});
  const [paused, setPaused] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => { keyRef.current = key; eyesRef.current = p.eyes; langRef.current = p.lang; sizedRef.current = p.sized; }, [key, p.eyes, p.lang, p.sized]);

  // what a request carries is read when it is made (the refs), so a re-render of the page never restarts a timer
  const ctx = useCallback((): Ctx => ({ eyes: eyesRef.current, lang: langRef.current, market: p.market, sized: (e, side) => sizedRef.current(e, side) }), [p.market]);

  // pictures of another set of eyes are never shown again
  useEffect(() => {
    const keep = <V,>(m: Record<string, V>) => Object.fromEntries(Object.entries(m).filter(([k]) => k.startsWith(`${key}|`)));
    setBigs(keep); setBigFail(keep); setTiles(keep); setTileFail(keep); setBusy(keep);
  }, [key]);

  const cat = catalog && catalog.key === key ? catalog : null;
  const resolved = useMemo(
    () => (cat ? resolveStyle({ n, tiles: cat.tiles, pick: cat.pick, eyes: cat.eyes, want: p.want, eyesOf: p.eyesOf }) : { style: null, changed: null }),
    [cat, n, p.want, p.eyesOf],
  );
  const selected = cat?.tiles.find((t) => t.id === resolved.style);
  const layout = layoutOf(selected, p.layoutWant);
  const wopts = useMemo(() => wireOpts(selected, n, p.opts), [selected, n, p.opts]);
  const names = useMemo(() => composeNames(p.names), [p.names]);
  const words = JSON.stringify([names, p.date.trim(), p.family.trim()]);
  const bigKey = cat && selected ? artKey([key, selected.id, layout, JSON.stringify(wopts), words, p.lang]) : null;
  useEffect(() => { bigRef.current = bigKey; }, [bigKey]);
  const tileKey = useCallback((t: ServerTile) => artKey([key, t.id, t.looks[p.opts.look ?? ''] ? p.opts.look : defaultLook(t)]), [key, p.opts.look]);

  // ---- 1. the tile list of these eyes (no pixel)
  useEffect(() => {
    if (!p.active || !n) return;
    const k = key;
    if ((catalog && catalog.key === k) || catErr?.key === k || inflight.current.has(`c:${k}`)) return;
    inflight.current.add(`c:${k}`);
    const sk = setKey(eyesRef.current.map((e) => e.id));
    const retake = Math.min(8, p.retakes.current);
    void (async () => {
      const out = await persist(() => composeCall(ctx(), { styles: [], size: 480, retake, again: seen.current.has(sk) }), () => keyRef.current === k);
      inflight.current.delete(`c:${k}`);
      if (keyRef.current !== k) return;
      const c = out.kind === 'ok' ? parseCatalog(out.data, k, eyesRef.current.length) : null;
      if (c) {
        seen.current.add(sk);
        p.retakes.current = Math.max(0, p.retakes.current - retake);
        setCatalog(c); setCatErr(null);
      } else {
        setCatErr({ key: k, message: out.kind === 'ok' ? T.errors.requestFailed(200) : messageOf(out) });
      }
    })();
  }, [p.active, n, key, catalog, catErr, nonce, ctx, p.retakes]);

  // ---- 2. the style on screen, at 1024 px
  useEffect(() => {
    if (!p.active || !cat || !selected || !bigKey) return;
    const k = bigKey;
    if (bigs[k] || bigFail[k] !== undefined || inflight.current.has(`b:${k}`)) return;
    const styleId = selected.id, lay = layout, o = wopts, dt = p.date, fam = p.family, nm = names, set = key;
    const t = setTimeout(() => {
      if (inflight.current.has(`b:${k}`)) return;
      inflight.current.add(`b:${k}`);
      void (async () => {
        const extra: Record<string, unknown> = { style: styleId, size: 1024, again: true, retake: 0 };
        if (n > 1 && lay) extra.layout = lay;
        if (nm.length) extra.names = nm;
        if (dt.trim()) extra.date = dt.trim();
        if (fam.trim()) extra.family_name = fam.trim();
        if (Object.keys(o).length) extra.opts = o;
        const out = await persist(() => composeCall(ctx(), extra), () => keyRef.current === set && bigRef.current === k);
        inflight.current.delete(`b:${k}`);
        if (keyRef.current !== set) return;
        if (out.kind === 'ok') {
          const pic = pictureOf(out.data, o);
          if (pic) {
            const art: Art = { src: pic.src, w: pic.w, h: pic.h, layout: pic.layout, canvas: pic.canvas, design: pic.design, fallback: pic.fallback, plan8: pic.plan8, opts: pic.opts };
            setBigs((c) => trim({ ...c, [k]: art }, BIG_MAX));
            // the style's own tile shows this picture until (and unless) a tile of its own is made: the style on screen needs no second render
            const tk = artKey([set, styleId, (o as { look?: string }).look ?? null]);
            setTiles((c) => (c[tk] ? c : trim({ ...c, [tk]: art }, TILE_MAX)));
            return;
          }
          setBigFail((f) => ({ ...f, [k]: T.errors.requestFailed(200) }));
          return;
        }
        if (out.kind === 'unavailable') {
          // the server will not draw this style for these eyes: the tile list on screen is out of date (or the engine saw a pupil the profile did not)
          const again = `${set}|${styleId}|${out.why}`;
          if (out.why === 'bar_pupil') {
            setCatalog((c) => (c && c.key === set ? { ...c, tiles: c.tiles.map((x) => (x.id === styleId ? { ...x, available: false, why: 'bar_pupil', pick: false } : x)), pick: c.pick === styleId ? null : c.pick } : c));
            return;
          }
          if (!unavailableOnce.current.has(again)) {
            unavailableOnce.current.add(again);
            setCatalog(null); setNonce((x) => x + 1);
            return;
          }
        }
        if (out.kind === 'paused') { pausedRef.current = out.message; setPaused(out.message); }
        setBigFail((f) => ({ ...f, [k]: messageOf(out) }));
      })();
    }, names.length || p.date.trim() || p.family.trim() ? 500 : 0);
    return () => clearTimeout(t);
    // ctx and the request's own parts are read when the timer fires; the key names every one of them
  }, [p.active, cat, selected, bigKey, bigs, bigFail, nonce, key, n, layout, wopts, names, p.date, p.family, ctx]);

  // ---- 3. the other tiles at 480 px, two at a time, after the large preview has settled
  const settled = !!bigKey && (bigs[bigKey] !== undefined || bigFail[bigKey] !== undefined);
  useEffect(() => {
    if (!p.active || !cat || !settled || pausedRef.current) return;
    const set = key;
    const todo = nextTiles(cat.tiles, (t) => tiles[tileKey(t)] !== undefined || tileFail[tileKey(t)] !== undefined || inflight.current.has(`t:${tileKey(t)}`), BATCH);
    if (!todo.length) return;
    const ks = todo.map((t) => tileKey(t));
    ks.forEach((x) => inflight.current.add(`t:${x}`));
    setBusy((b) => ({ ...b, ...Object.fromEntries(ks.map((x) => [x, true as const])) }));
    const withLooks = todo.find((t) => Object.keys(t.looks).length > 0);
    const look = withLooks ? (withLooks.looks[p.opts.look ?? ''] ? p.opts.look : defaultLook(withLooks)) : null;
    void (async () => {
      const out = await persist(() => composeCall(ctx(), { styles: todo.map((t) => t.id), size: 480, again: true, retake: 0, ...(look ? { opts: { look } } : {}) }), () => keyRef.current === set);
      ks.forEach((x) => inflight.current.delete(`t:${x}`));
      if (keyRef.current !== set) return;
      setBusy((b) => { const c = { ...b }; ks.forEach((x) => delete c[x]); return c; });
      if (out.kind === 'ok') {
        const rows = Array.isArray((out.data as { tiles?: unknown }).tiles) ? ((out.data as { tiles: Array<Record<string, unknown>> }).tiles) : [];
        const got: Record<string, Art> = {};
        const failed: Record<string, true> = {};
        const held: Record<string, string> = {};                 // a tile the server held back after all: its own reason (a pupil the profile did not show)
        todo.forEach((t, i) => {
          const row = rows.find((r) => r && r.id === t.id);
          const pic = pictureOf(row);
          if (pic) got[ks[i]] = { src: pic.src, w: pic.w, h: pic.h, layout: pic.layout, canvas: pic.canvas, design: pic.design, fallback: pic.fallback, plan8: pic.plan8 };
          else if (row && row.available === false) held[t.id] = typeof row.why === 'string' && row.why ? row.why : 'bar_pupil';
          else failed[ks[i]] = true;
        });
        if (Object.keys(got).length) setTiles((c) => trim({ ...c, ...got }, TILE_MAX));
        if (Object.keys(failed).length) setTileFail((f) => ({ ...f, ...failed }));
        if (Object.keys(held).length) setCatalog((c) => (c && c.key === set ? { ...c, tiles: c.tiles.map((x) => (x.id in held ? { ...x, available: false, why: held[x.id], pick: false } : x)), pick: (c.pick ?? '') in held ? null : c.pick } : c));
        return;
      }
      if (out.kind === 'paused') { pausedRef.current = out.message; setPaused(out.message); }
      setTileFail((f) => ({ ...f, ...Object.fromEntries(ks.map((x) => [x, true as const])) }));
    })();
  }, [p.active, cat, settled, key, tiles, tileFail, tileKey, p.opts.look, ctx]);

  // the large preview's own failure, or (no tile list, so no style on screen) the failure of the list: the frame where the picture would be says it either way
  const catalogError = catErr && catErr.key === key ? catErr.message : null;
  catalogMissing.current = !cat && catalogError !== null;
  const art = bigKey ? bigs[bigKey] ?? otherLanguage(bigs, key, selected?.id, layout, wopts, words, p.lang) : undefined;
  const lastOfSet = useMemo(() => Object.entries(bigs).filter(([k]) => k.startsWith(`${key}|`)).map(([, v]) => v).at(-1), [bigs, key]);
  const staleArt = art ?? (selected ? tiles[tileKey(selected)] : undefined) ?? lastOfSet;

  const retryCatalog = useCallback(() => { setCatErr(null); setNonce((x) => x + 1); }, []);
  const retryCompose = useCallback(() => {
    pausedRef.current = null; setPaused(null);
    // without a tile list there is no style on screen to make again: asking for the list is what a retry means then
    if (catalogMissing.current) { retryCatalog(); return; }
    setBigFail((f) => { const c = { ...f }; if (bigRef.current) delete c[bigRef.current]; return c; });
  }, [retryCatalog]);
  const retryTiles = useCallback(() => { pausedRef.current = null; setPaused(null); setTileFail({}); }, []);
  const refresh = useCallback(() => {
    // a checkout refused the style, or the plan changed: the tile list and the large previews of these eyes are made again
    setCatalog(null); setBigs({}); setBigFail({}); setNonce((x) => x + 1);
  }, []);

  return {
    catalog: cat, catalogError,
    style: resolved.style, changed: resolved.changed, selected, layout, art, staleArt,
    composeError: bigKey ? bigFail[bigKey] ?? null : catalogError,
    tilePicture: (t) => tiles[tileKey(t)],
    tileBusy: (t) => busy[tileKey(t)] === true,
    // a server that makes no more pictures today stops the loop: the tiles it never got to say so as the ones it refused do, instead of sitting empty
    tileFailed: (t) => { const k = tileKey(t); return tileFail[k] === true || (paused !== null && tiles[k] === undefined && busy[k] !== true); },
    tilesPaused: paused, retryCompose, retryTiles, retryCatalog, refresh,
  };
}

function messageOf(o: Outcome<unknown>): string {
  return o.kind === 'busy' || o.kind === 'paused' || o.kind === 'unavailable' || o.kind === 'error' ? o.message : T.errors.requestFailed(0);
}

/** Right after a language switch the same choice's preview in another language stands in (shown, saved, orderable: only the words of its watermark differ)
 *  until the one in the new language is made. */
function otherLanguage(bigs: Record<string, Art>, key: string, style: string | undefined, layout: string | null, opts: Record<string, unknown>, words: string, lang: Lang): Art | undefined {
  if (!style) return undefined;
  for (const l of ['en', 'de', 'lt', 'hu'] as const) {
    if (l === lang) continue;
    const hit = bigs[artKey([key, style, layout, JSON.stringify(opts), words, l])];
    if (hit) return hit;
  }
  return undefined;
}
