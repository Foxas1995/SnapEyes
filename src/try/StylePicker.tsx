import React from 'react';
import { AlertTriangle, RefreshCcw, Trash2 } from 'lucide-react';
import { T } from './copy';
import { NO_SAVE } from './noSave';
import type { Art } from './multi';
import { CONTACT_EMAIL } from '../landing/config';
import { styleName } from '../shared/styles';
import {
  type Catalog, type Changed, type RetakeView, type ServerTile,
  groupAllSoon, groupOf, isSoon, looksOf, lookName, tileState,
} from './picker';

/** Everything the picker draws, as TryApp (src/try/usePreviews.ts and picker.ts) worked it out. The page owns no list of styles: `catalog` is what the
 *  server said for these very eyes (null while it is being asked), and every state below is a function of it. */
export interface PickerModel {
  n: number;
  catalog: Catalog | null;
  error: string | null;                         // the tile list could not be had (the server's sentence)
  onRetryCatalog: () => void;
  style: string | null;                         // the style on screen (the customer's choice when the eyes can take it, else the recommended tile)
  selected: ServerTile | undefined;
  changed: Changed | null;                      // why the style on screen is not the one the customer chose
  tilePicture: (t: ServerTile) => Art | undefined;
  tileBusy: (t: ServerTile) => boolean;         // its picture is being made
  tileFailed: (t: ServerTile) => boolean;
  onRetryTiles: () => void;
  paused: string | null;                        // the server's sentence when it makes no more pictures today (503 tiles_paused)
  priceOf: (t: ServerTile) => string | null;    // printed on the tile (one eye, a style that can be bought now), else null
  onStyle: (id: string) => void;
  look: string | null;                          // the chosen look of the style that has looks (the default when the customer chose none)
  onLook: (code: string) => void;
  retake: RetakeView | null;
  advisory: number[];                           // 1-based eyes that only warn on the selected style
  onRetakeEye: (position: number) => void;
  onRemoveEye: (position: number) => void;      // take an eye off the artwork (the pupil state offers it: an eye the styles of the list cannot take)
  onManual: () => void;                         // one counted click on the manual route
}

/** A picker with nothing in it: no tile list yet. */
export function emptyPicker(n = 1): PickerModel {
  const no = () => undefined;
  return {
    n, catalog: null, error: null, onRetryCatalog: no, style: null, selected: undefined, changed: null, tilePicture: no, tileBusy: () => false,
    tileFailed: () => false, onRetryTiles: no, paused: null, priceOf: () => null, onStyle: no, look: null, onLook: no, retake: null, advisory: [], onRetakeEye: no, onRemoveEye: no, onManual: no,
  };
}

/** The line that says why the style on screen is not the one chosen: the eye count (the eyes kind names the artwork's own), a retake, a pupil. */
export function changedLine(c: Changed, n: number, name: (id: string) => string): string {
  const from = name(c.from), to = name(c.to);
  switch (c.kind) {
    case 'eyes': return T.picker.changed.eyes(from, to, n);
    case 'gate': return T.picker.changed.gate(from, to, c.eye);
    case 'reseal': return T.picker.changed.reseal(from, to, c.eye);
    case 'pupil': return T.picker.changed.pupil(from, to);
  }
}

/** The group's heading and line (the landing page's words), the line that says once that a group opens soon, the line that says why the style on screen
 *  is not the chosen one, and the tiles: the recommended one first and framed, every other in the server's order. */
export const StylePicker: React.FC<{ model: PickerModel }> = ({ model: m }) => {
  const group = groupOf(m.n);
  const tiles = m.catalog?.tiles ?? [];
  const allSoon = groupAllSoon(tiles);
  // a style that is not in this list (the customer chose it for another number of eyes) is named by the registry
  const nameOf = (id: string) => tiles.find((t) => t.id === id)?.name ?? styleName(id);
  const eyes = m.catalog?.eyes ?? [];
  return (
    <div data-testid="style-picker" data-group={group}>
      <div className="mt-4">
        <h3 className="font-luxury text-base font-bold text-zinc-100">{T.picker.groups[group]}</h3>
        <p className="text-xs text-zinc-300 mt-0.5">{T.picker.groupIntro[group]}</p>
        {allSoon && <p data-testid="group-soon" className="text-xs text-amber-200 mt-1.5">{T.picker.groupSoon}</p>}
      </div>
      {m.changed && <p role="status" data-testid="style-changed" className="text-xs text-sky-100 mt-2 bg-sky-950/30 border border-sky-400/30 rounded-xl p-3">{changedLine(m.changed, m.n, nameOf)}</p>}

      {m.error && !m.catalog ? (
        <div data-testid="picker-error" className="mt-2 text-xs text-rose-200 bg-rose-950/40 border border-rose-500/40 rounded-xl p-3 flex flex-col items-start gap-2">
          <span>{m.error}</span>
          <button type="button" onClick={m.onRetryCatalog} className="min-h-[44px] px-3 rounded-xl bg-white/10 border border-white/20 text-sm font-semibold flex items-center gap-2 text-zinc-100">
            <RefreshCcw className="w-4 h-4" /> {T.result.retry}
          </button>
        </div>
      ) : !m.catalog ? (
        <ul aria-label={T.picker.listLabel} aria-busy="true" data-testid="tile-list" className="mt-2 grid gap-2 grid-cols-[repeat(auto-fill,minmax(160px,1fr))]">
          {[0, 1, 2, 3].map((i) => (
            <li key={i} className="rounded-xl border border-white/10 overflow-hidden" aria-hidden="true">
              <span className="block aspect-[4/3] bg-white/5 motion-safe:animate-pulse" />
              <span className="block h-9" />
            </li>
          ))}
        </ul>
      ) : (
        <ul aria-label={T.picker.listLabel} data-testid="tile-list" className="mt-2 grid gap-2 grid-cols-[repeat(auto-fill,minmax(160px,1fr))]">
          {tiles.map((t) => <Tile key={t.id} t={t} m={m} allSoon={allSoon} eyes={eyes} />)}
        </ul>
      )}
      {m.paused && <p role="status" data-testid="tiles-paused" className="text-xs text-amber-100 mt-2 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3">{m.paused}</p>}
    </div>
  );
};

const Tile: React.FC<{ t: ServerTile; m: PickerModel; allSoon: boolean; eyes: Catalog['eyes'] }> = ({ t, m, allSoon, eyes }) => {
  const st = tileState(t, eyes);
  const held = st.kind === 'gate' || st.kind === 'reseal' || st.kind === 'pupil';
  const selected = m.style === t.id;
  const pick = !!m.catalog && m.catalog.pick === t.id && t.available;
  const art = held ? undefined : m.tilePicture(t);
  const busy = !held && !art && m.tileBusy(t);
  const failed = !held && !art && !busy && m.tileFailed(t);
  const price = m.priceOf(t);
  const looks = looksOf(t);
  const reason = pick && m.catalog?.reasonKey ? (T.picker.reasons as Record<string, string>)[m.catalog.reasonKey] : undefined;
  const label = st.kind === 'gate' ? T.picker.retakeFirst(st.eye) : st.kind === 'reseal' ? T.picker.resealFirst(st.eye) : st.kind === 'pupil' ? T.picker.pupil : '';
  const ring = selected ? 'border-[#f5c542] ring-2 ring-[#f5c542]' : pick ? 'border-[#f5c542]/60' : 'border-white/15';
  // a tile that is held back cannot be chosen: pressing it takes the customer to the retake state, which says why
  const press = () => {
    if (!held) { m.onStyle(t.id); return; }
    try {
      const el = document.getElementById('retake-state');
      el?.scrollIntoView({ block: 'center' });
      el?.querySelector<HTMLElement>('h3')?.focus();
    } catch { /* no document: nothing to show */ }
  };
  return (
    <li data-testid={`tile-${t.slug}`} data-state={st.kind} data-stage={t.stage} className={`rounded-xl border overflow-hidden bg-[#0b0e17] flex flex-col ${ring} ${held ? 'opacity-75' : ''}`}>
      <button type="button" onClick={press} aria-pressed={held ? undefined : selected} aria-disabled={held || undefined} aria-busy={busy || undefined}
        className="block w-full text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542]">
        <span className="relative block w-full aspect-[4/3] bg-black overflow-hidden">
          {art && <img {...NO_SAVE} src={art.src} alt={T.picker.tileAlt(t.name)} className="absolute inset-0 w-full h-full object-contain" />}
          {busy && (
            <>
              <span aria-hidden="true" className="absolute inset-0 bg-white/5 motion-safe:animate-pulse" />
              <span className="sr-only">{T.picker.tileMaking(t.name)}</span>
            </>
          )}
          {failed && <span className="absolute inset-0 flex items-center justify-center px-2 text-center text-[11px] text-zinc-300 bg-white/5">{T.picker.tileFailed}</span>}
          {held && (
            <span aria-hidden="true" className="absolute inset-0 flex items-center justify-center bg-white/5"><AlertTriangle className="w-6 h-6 text-amber-300/80" /></span>
          )}
          {pick && (
            <span data-testid="recommended" className="absolute top-1.5 left-1.5 rounded-full bg-[#f5c542] text-black text-[10px] font-bold uppercase tracking-wider px-2 py-0.5">{T.picker.recommended}</span>
          )}
        </span>
        <span className="block px-2 py-1.5">
          <span className="flex items-baseline justify-between gap-2">
            <span className="text-xs font-bold text-zinc-100 min-w-0 truncate">{t.name}</span>
            {price && <span data-testid="tile-price" className="shrink-0 text-xs font-semibold text-[#f5c542] whitespace-nowrap">{price}</span>}
            {!allSoon && isSoon(t) && !held && (
              <span data-testid="soon" className="shrink-0 text-[10px] font-bold uppercase tracking-wider text-amber-200 border border-amber-400/40 rounded-full px-1.5 py-px">{T.picker.soon}</span>
            )}
          </span>
          {reason && <span data-testid="reason" className="block text-[11px] text-zinc-300 mt-0.5">{reason}</span>}
          {label && <span data-testid="held-label" className="block text-[11px] font-semibold text-amber-200 mt-0.5">{label}</span>}
        </span>
      </button>
      {failed && (
        <div className="px-2 pb-2">
          <button type="button" data-testid="tile-retry" onClick={m.onRetryTiles}
            className="min-h-[36px] px-2.5 rounded-lg border border-white/20 bg-white/10 text-[11px] font-semibold text-zinc-100 flex items-center gap-1.5">
            <RefreshCcw className="w-3 h-3" /> {T.result.retry}
          </button>
        </div>
      )}
      {looks.length > 1 && !held && (
        <div role="group" aria-label={T.picker.options.look} className="flex flex-wrap gap-1.5 px-2 pb-2">
          {looks.map((l) => (
            <button key={l.code} type="button" aria-pressed={selected && m.look === l.code} data-testid={`look-${l.code}`}
              onClick={() => { m.onLook(l.code); m.onStyle(t.id); }}
              className={`min-h-[36px] px-2.5 rounded-lg border text-[11px] font-semibold ${selected && m.look === l.code ? 'border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]' : 'border-white/15 bg-white/5 text-zinc-200'}`}>
              {lookName(l.code)}{l.soon && !allSoon ? ` · ${T.picker.soon}` : ''}
            </button>
          ))}
        </div>
      )}
    </li>
  );
};

// ------------------------------------------------------------------------------------------------ the retake state

/** The way to ask us when nothing can be bought (the landing page's FAQ answer: the owner looks at the best photos, no promise of a time): the e-mail is a
 *  link and its click is the one counted click of the manual route. */
export const ManualRoute: React.FC<{ onManual: () => void }> = ({ onManual }) => {
  const [before, after] = T.picker.retake.manual.split('{link}');
  return (
    <p data-testid="manual-route" className="mt-2.5 text-zinc-200">
      {before}
      <a href={`mailto:${CONTACT_EMAIL}`} onClick={onManual} className="underline underline-offset-2 font-semibold text-amber-100">{CONTACT_EMAIL}</a>
      {after}
    </p>
  );
};

/** The retake state (INTEGRATION_SPEC 1.6.2 rule 3, 2.5): which eyes, why in plain sentences (a rule the iris fails, or a pupil that is not round), the one
 *  tip that fits, the retake buttons (and, for a pupil the styles cannot take, a button that takes the eye off the artwork), and where nothing can be
 *  bought the way to ask us. Never a dead end. `inPlace`: shown where the preview would be. */
export const RetakePanel: React.FC<{
  view: RetakeView; total: number; onRetake: (position: number) => void; onManual: () => void; onRemove?: (position: number) => void; inPlace?: boolean;
}> = ({ view, total, onRetake, onManual, onRemove, inPlace }) => {
  const all = [...new Set([...view.eyes, ...view.reseal, ...view.pupil])].sort((a, b) => a - b);
  return (
    <section id="retake-state" data-testid="retake-state" aria-labelledby="retake-title" className={`text-xs text-amber-50 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3 ${inPlace ? '' : 'mt-3'}`}>
      <h3 id="retake-title" tabIndex={-1} className="font-bold text-sm text-amber-100 flex items-center gap-2 focus:outline-none"><AlertTriangle className="w-4 h-4 shrink-0 text-amber-300" /> {T.picker.retake.title(view.eyes.length ? view.eyes : view.reseal.length ? view.reseal : view.pupil, total)}</h3>
      {view.reasons.length > 0 && view.eyes.length > 0 && view.reasons.map((r) => <p key={r} data-testid={`retake-${r}`} className="mt-1.5">{T.picker.retake[r]}</p>)}
      {view.pupil.length > 0 && <p data-testid="retake-pupil" className="mt-1.5">{T.picker.retake.pupil}</p>}
      {view.reseal.length > 0 && <p data-testid="retake-reseal" className="mt-1.5">{T.picker.retake.reseal(view.reseal, total)}</p>}
      {(view.eyes.length > 0 || view.pupil.length > 0) && <p data-testid={`retake-tip-${view.tip}`} className="mt-1.5 text-amber-100">{T.picker.retake.tips[view.tip]}</p>}
      {view.holds && <p className="mt-1.5 text-zinc-300">{T.picker.retake.held}</p>}
      <div className="flex flex-wrap gap-2 mt-2.5">
        {all.map((i) => (
          <button key={i} type="button" data-testid={`retake-eye-${i}`} onClick={() => onRetake(i)}
            className="min-h-[44px] px-3 rounded-xl border border-amber-400/50 bg-amber-500/10 text-amber-100 text-xs font-semibold flex items-center gap-1.5">
            <RefreshCcw className="w-3.5 h-3.5" /> {total === 1 ? T.result.retakeOnly : T.result.retakeEye(i)}
          </button>
        ))}
        {/* a pupil the styles cannot take is a reason to leave that eye out as well as to photograph it again (the others may still make an artwork) */}
        {onRemove && total > 1 && view.pupil.map((i) => (
          <button key={`rm${i}`} type="button" data-testid={`remove-eye-${i}`} onClick={() => onRemove(i)}
            className="min-h-[44px] px-3 rounded-xl border border-white/20 bg-white/10 text-zinc-100 text-xs font-semibold flex items-center gap-1.5">
            <Trash2 className="w-3.5 h-3.5" /> {T.result.remove(i)}
          </button>
        ))}
      </div>
      {view.deadEnd && <ManualRoute onManual={onManual} />}
    </section>
  );
};
