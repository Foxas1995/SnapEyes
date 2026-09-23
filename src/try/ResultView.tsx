import React from 'react';
import { AlertTriangle, Check, Download, Plus, RefreshCcw, Trash2 } from 'lucide-react';
import { CompareSlider } from './CompareSlider';
import { T } from './copy';
import {
  type Art, type Eye, type Layout, MAX_EYES, PRICE_CENTS, billableEyes, canvasSize, euro, layoutsFor, priceCents,
} from './multi';

/** accent: the style's accent colour (api/_lib/iris.py STYLES), null for the bare Studio Black. */
export interface StyleOption { id: string; name: string; accent: readonly [number, number, number] | null }

/** A light swatch of the style: its accent glow on near-black, or plain black for Studio Black. */
const swatch = (accent: StyleOption['accent']) => (accent
  ? `radial-gradient(circle at 50% 50%, rgba(${accent.join(',')},0.55) 0%, rgba(${accent.join(',')},0.16) 40%, #06070b 74%)`
  : '#030304');

interface Props {
  eyes: Eye[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  onRetake: (id: string) => void;
  onAdd: () => void;
  art: Art | undefined;          // the preview for exactly the current eyes, layout, style and names
  staleArt: Art | undefined;     // the last preview shown, kept on screen while the next one composes
  composeError: string | null;
  onRetryCompose: () => void;
  layout: Layout;
  onLayout: (l: Layout) => void;
  styles: StyleOption[];
  style: string;
  onStyle: (s: string) => void;
  names: string;
  onNames: (s: string) => void;
  onStartOver: () => void;
}

export const ResultView: React.FC<Props> = (p) => {
  const n = p.eyes.length;
  const idx = Math.max(0, p.eyes.findIndex((e) => e.id === p.selectedId));
  const eye = p.eyes[idx];
  const layouts = layoutsFor(n);
  const expected = canvasSize(n, p.layout);
  const shown = p.art ?? p.staleArt;
  const composing = !p.art && !p.composeError;
  const styleName = p.styles.find((s) => s.id === p.style)?.name ?? p.style;
  const samples = p.eyes.filter((e) => e.sample).length;
  const allSample = samples > 0 && samples === n;
  if (!eye) return null;
  const artTitle = allSample ? T.result.sampleArtwork : T.result.artwork;
  const artAlt = samples ? `${artTitle} (${T.result.sampleBadge})` : artTitle;
  const retakeLabel = eye.sample ? T.result.replaceSample : n > 1 ? T.result.retakeEye(idx + 1) : T.result.retakeOnly;

  // every eye on the artwork, each with its own before/after
  const beforeAfter = (
    <div>
      <div className="flex items-center justify-between mb-2 gap-2">
        <h2 className="font-luxury text-xl font-bold">{T.result.beforeAfter}</h2>
        <FidelityBadge eye={eye} />
      </div>
      {n > 1 && (
        // No remove control on the chips: a small x on the thumbnail took taps meant to select the eye and
        // threw a paid restoration away. Removing is a full-size action on the selected eye, with Undo.
        <div role="tablist" aria-label={T.result.eyes} className="flex gap-2 overflow-x-auto pb-2 mb-1 -mx-1 px-1">
          {p.eyes.map((e, i) => (
            <button key={e.id} role="tab" aria-selected={i === idx} onClick={() => p.onSelect(e.id)}
              className="shrink-0 flex flex-col items-center gap-1 w-16 pt-1">
              <img src={e.thumb} alt="" className={`w-12 h-12 rounded-full object-cover border-2 ${i === idx ? 'border-[#f5c542] ring-2 ring-[#f5c542]/40' : 'border-white/15 opacity-75'}`} />
              <span className={`text-[10px] font-bold leading-tight text-center ${i === idx ? 'text-[#f5c542]' : 'text-zinc-400'}`}>
                {T.result.eyeLabel(i + 1)}
                {e.sample && <span className="block text-[9px] font-semibold text-amber-200/90">{T.result.sampleLabel}</span>}
              </span>
            </button>
          ))}
          {n < MAX_EYES && (
            <button onClick={p.onAdd} aria-label={T.result.addAnother}
              className="shrink-0 mt-1 w-12 h-12 rounded-full border-2 border-dashed border-[#f5c542]/50 text-[#f5c542] flex items-center justify-center">
              <Plus className="w-5 h-5" />
            </button>
          )}
        </div>
      )}
      <CompareSlider key={eye.id} before={eye.before} after={`data:image/jpeg;base64,${eye.image}`}
        beforeLabel={eye.sample ? T.result.samplePhoto : T.result.yourPhoto} afterLabel={T.result.after} />
      {/* decision 5 speaks about the customer's own photo, so the sample gets its own line instead */}
      {eye.sample
        ? <p className="text-xs text-amber-100 mt-3 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3">{T.result.sampleNote}</p>
        : <p className="text-xs text-zinc-200 mt-3 bg-white/5 border border-white/10 rounded-xl p-3">{T.result.transparency}</p>}
      {!eye.sample && eye.colourOff && (
        <p data-testid="colour-off" className="text-xs text-amber-200/90 mt-2 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 flex gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-px text-amber-300" /> <span>{T.result.colourOff}</span>
        </p>
      )}
      <p className="text-[11px] text-zinc-500 mt-2">
        {[
          T.result.drag,
          eye.diameterPx && !eye.sample ? T.result.irisPx(eye.diameterPx) : '',
          eye.glarePct >= 0.4 ? T.result.reflection : '',
          eye.usedSr ? T.result.upscaled : '',
        ].filter(Boolean).join(' ')}
      </p>
      {eye.stored && <p className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1"><Check className="w-3 h-3" /> {T.result.stored}</p>}
      <div className={`grid gap-2 mt-3 ${n > 1 ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <button onClick={() => p.onRetake(eye.id)}
          className={`min-h-[44px] px-3 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 ${eye.colourOff && !eye.sample ? 'border-amber-400/50 bg-amber-500/10 text-amber-100' : 'border-white/10 bg-white/5 text-zinc-200'}`}>
          <RefreshCcw className="w-4 h-4" /> {retakeLabel}
        </button>
        {n > 1 && (
          <button onClick={() => p.onRemove(eye.id)}
            className="min-h-[44px] px-3 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-zinc-300 flex items-center justify-center gap-2">
            <Trash2 className="w-4 h-4" /> {T.result.remove(idx + 1)}
          </button>
        )}
      </div>
    </div>
  );

  const artwork = (
    <div>
      <div className="flex items-center justify-between gap-2 mb-2">
        <h2 className="font-luxury text-xl font-bold">{artTitle}</h2>
        {/* beside the picture, not over it: the engine's watermark banner runs along its top edge */}
        {samples > 0 && (
          <span data-testid="sample-badge" className="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-amber-400/50 text-amber-200 bg-amber-500/10">{T.result.sampleBadge}</span>
        )}
      </div>
      <div data-testid="artwork" className="relative w-full rounded-2xl overflow-hidden border border-white/10 bg-black"
        style={{ aspectRatio: `${expected.w} / ${expected.h}` }}>
        {shown && <img src={shown.src} alt={artAlt} className={`absolute inset-0 w-full h-full object-contain transition-opacity ${p.art ? '' : 'opacity-50'}`} />}
        {!shown && composing && <div className="absolute inset-0 flex items-center justify-center text-zinc-500 text-sm">{T.result.composing}</div>}
        {composing && <div aria-label={T.result.composing} className="absolute top-3 right-3 w-5 h-5 border-2 border-[#f5c542]/30 border-t-[#f5c542] rounded-full animate-spin" />}
        {!p.art && p.composeError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/70 text-center px-6">
            <p className="text-sm text-rose-200">{T.result.composeFailed} {p.composeError}</p>
            <button onClick={p.onRetryCompose} className="px-4 py-2 rounded-xl bg-white/10 border border-white/20 text-sm font-semibold flex items-center gap-2"><RefreshCcw className="w-4 h-4" /> {T.result.retry}</button>
          </div>
        )}
      </div>
      {samples > 0 && <p className="text-[11px] text-amber-200/90 mt-2">{allSample ? T.result.sampleArtworkNote : T.result.mixedArtworkNote}</p>}

      {layouts.length > 1 && (
        <div className="mt-3">
          <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1.5">{T.result.layout}</p>
          <div role="radiogroup" aria-label={T.result.layout} className={`grid gap-2 ${layouts.length === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
            {layouts.map((l) => (
              <button key={l} role="radio" aria-checked={p.layout === l} onClick={() => p.onLayout(l)}
                className={`py-2.5 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 ${p.layout === l ? 'border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]' : 'border-white/10 bg-white/5 text-zinc-300'}`}>
                <LayoutGlyph layout={l} n={n} /> {T.result.layouts[l]}
              </button>
            ))}
          </div>
        </div>
      )}

      <p className="text-[10px] uppercase tracking-widest text-zinc-500 mt-3 mb-1.5">{T.result.style}</p>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {p.styles.map((s) => (
          <button key={s.id} onClick={() => p.onStyle(s.id)} aria-pressed={p.style === s.id}
            className={`rounded-lg overflow-hidden border text-left ${p.style === s.id ? 'border-[#f5c542] ring-2 ring-[#f5c542]' : 'border-white/10'}`}>
            {/* the customer's own iris, never a stock eye */}
            <span className="relative block w-full aspect-[16/11]" style={{ background: swatch(s.accent) }}>
              <img src={eye.thumb} alt="" className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[64%] aspect-square rounded-full object-cover" />
            </span>
            <span className="block text-[10px] font-bold px-1.5 py-1 truncate">{s.name}</span>
          </button>
        ))}
      </div>
      <input value={p.names} maxLength={60} onChange={(e) => p.onNames(e.target.value)} placeholder={T.result.namesPlaceholder}
        className="mt-3 w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm placeholder-zinc-500 focus:outline-none focus:border-[#f5c542]" />

      <div className={`grid gap-3 mt-3 ${n < MAX_EYES ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <a href={p.art?.src || '#'} download={`snapeyes-preview-${p.style}-${n}-${n === 1 ? 'eye' : 'eyes'}${samples ? '-ai-generated-sample' : ''}.jpg`}
          aria-disabled={!p.art}
          className={`py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 ${p.art ? 'bg-white/10 border border-white/15 text-zinc-100' : 'bg-white/5 text-zinc-500 pointer-events-none'}`}>
          <Download className="w-4 h-4" /> {T.result.save}
        </a>
        {n < MAX_EYES && (
          <button onClick={p.onAdd} className="py-3 rounded-xl bg-[#f5c542] text-black text-sm font-bold flex items-center justify-center gap-2">
            <Plus className="w-4 h-4" /> {n === 1 ? T.result.addSecond : T.result.addAnother}
          </button>
        )}
      </div>
      <p className="text-[11px] text-zinc-500 mt-2">{n < MAX_EYES ? T.result.addHint(MAX_EYES - n) : T.result.full(MAX_EYES)}</p>
    </div>
  );

  return (
    <section className="flex flex-col gap-6">
      {/* One eye: its before/after is the surprise, so it leads. Two or more: the artwork of all of them is
          what the couple came for, so it leads and the per-eye before/after follows. */}
      {n > 1 ? <>{artwork}{beforeAfter}</> : <>{beforeAfter}{artwork}</>}

      <PriceCard billable={billableEyes(p.eyes)} samples={samples} style={p.style} styleName={styleName} />

      <button onClick={p.onStartOver} className="text-xs text-zinc-400 underline underline-offset-4 self-center">{T.result.startOver}</button>
    </section>
  );
};

/** The price for the eyes on this artwork. Ordering is not open yet, so this informs and sells nothing:
 *  no button, no checkout, and the notice says so in plain words. The AI-generated sample eye is never
 *  priced: nobody can order it as their own eye. */
const PriceCard: React.FC<{ billable: number; samples: number; style: string; styleName: string }> = ({ billable, samples, style, styleName }) => {
  const n = billable;
  if (n === 0) {
    return (
      <section aria-label={T.price.title} className="bg-[#0b0e17] border border-[#f5c542]/25 rounded-2xl p-4">
        <p className="text-[10px] uppercase tracking-widest text-zinc-500">{T.price.title}</p>
        <p data-testid="price-demo" className="text-sm text-zinc-200 mt-1.5">{T.price.demo}</p>
        <p className="text-sm font-semibold text-emerald-300 mt-3">{T.price.notice}</p>
      </section>
    );
  }
  const label = n === 1 ? T.price.oneEye(styleName) : n === 2 ? T.price.duo : T.price.many(n);
  const hint = n === 1
    ? `${T.price.oneEyeOther(euro(PRICE_CENTS.studioBlack), euro(PRICE_CENTS.artBackground))} ${T.price.duoOffer(euro(PRICE_CENTS.coupleDuo))}`
    : T.price.extra(euro(PRICE_CENTS.coupleDuo), euro(PRICE_CENTS.extraEye), MAX_EYES);
  return (
    <section aria-label={T.price.title} className="bg-[#0b0e17] border border-[#f5c542]/25 rounded-2xl p-4">
      <p className="text-[10px] uppercase tracking-widest text-zinc-500">{T.price.title}</p>
      <div className="flex items-baseline justify-between gap-3 mt-1.5">
        <span className="text-sm font-semibold text-zinc-100">{label}</span>
        <span data-testid="price" className="font-luxury text-2xl font-bold text-[#f5c542] whitespace-nowrap">{euro(priceCents(n, style))}</span>
      </div>
      <p className="text-[11px] text-zinc-400 mt-2">{hint}</p>
      {samples > 0 && <p className="text-[11px] text-amber-200/90 mt-2">{T.price.sampleNotCounted(samples)}</p>}
      <p className="text-sm font-semibold text-emerald-300 mt-3">{T.price.notice}</p>
      <p className="text-[11px] text-zinc-500 mt-1">{T.price.footnote}</p>
    </section>
  );
};

const FidelityBadge: React.FC<{ eye: Eye }> = ({ eye }) => (eye.fallback
  ? <span className="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-amber-400/40 text-amber-200 bg-amber-500/10">{T.result.badgeFallback}</span>
  : <span className="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-[#f5c542]/50 text-[#f5c542] bg-[#f5c542]/10">{T.result.badgeMacro}</span>);

/** A tiny drawing of where the discs go, so "Fusion" and "Side by side" read at a glance. */
const LayoutGlyph: React.FC<{ layout: Layout; n: number }> = ({ layout, n }) => {
  const r = 3.2;
  const pts: Array<[number, number]> =
    layout === 'duo' ? [[6, 8], [14, 8]]
      : layout === 'fusion' ? [[7.5, 8], [12.5, 8]]
        : layout === 'triangle' ? [[10, 4.5], [6, 11.5], [14, 11.5]]
          : layout === 'grid' ? [[6.5, 4.5], [13.5, 4.5], [6.5, 11.5], [13.5, 11.5]]
            : layout === 'row' ? Array.from({ length: n }, (_, i) => [2 + (16 / Math.max(1, n - 1)) * i, 8] as [number, number])
              : [[10, 8]];
  const rr = layout === 'row' ? Math.min(r, 16 / Math.max(1, n - 1) / 2 - 0.5) : r;
  return (
    <svg viewBox="0 0 20 16" className="w-5 h-4" aria-hidden>
      {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={rr} fill="none" stroke="currentColor" strokeWidth="1.2" />)}
    </svg>
  );
};
