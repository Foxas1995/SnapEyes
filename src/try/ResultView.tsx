import React from 'react';
import { AlertTriangle, Check, Download, Plus, RefreshCcw, Trash2 } from 'lucide-react';
import { CompareSlider } from './CompareSlider';
import { ArtImage } from '../motion/ArtImage';
import { Reveal } from '../reveal/Reveal';
import { RevealStrip } from '../reveal/RevealStrip';
import { withheldByColour } from '../reveal/revealMath';
import { useRevealFrame } from '../reveal/useRevealFrame';
import { AI_MATERIAL_PUBLISHED } from '../shared/aiMaterial';
import { T, layoutLabel } from './copy';
import { NO_SAVE, NO_SAVE_BOX } from './noSave';
import { type Art, type Eye, MAX_EYES, canvasSize } from './multi';
import { ManualRoute, RetakePanel, StylePicker, type PickerModel } from './StylePicker';
import { Words, type WordsModel } from './Words';
import { type Opts, lookName, soonChoice } from './picker';

interface Props {
  eyes: Eye[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  onRetake: (id: string) => void;
  onAdd: () => void;
  onMove: (id: string, delta: -1 | 1) => void;   // an eye one place earlier or later on the artwork (four to eight eyes)
  art: Art | undefined;          // the preview for exactly the current eyes, layout, style and words
  staleArt: Art | undefined;     // the last preview shown, kept on screen while the next one composes
  composeError: string | null;
  onRetryCompose: () => void;
  picker: PickerModel;           // the tiles, the retake state, the style on screen (./StylePicker.tsx)
  layout: string | null;         // the layout on screen
  layoutOptions: readonly string[];
  onLayout: (l: string) => void;
  opts: Opts;                    // swap places (two eyes), rotate places (three), the look of a style that has looks
  onOpts: (o: Opts) => void;
  words: WordsModel;             // a name per eye, a date, a family name
  onStartOver: () => void;
  purchase: React.ReactNode;     // the price and the way to buy it (./BuyCard.tsx)
  enter?: boolean;               // the screen arrives with a transition (the page changed step before: src/try/TryApp.tsx)
  arrive?: boolean;              // the artwork has just been made: its first display opens like a diaphragm (spec 7.5); never for a restored one
  onArrived?: () => void;        // that opening is over
}

export const ResultView: React.FC<Props> = (p) => {
  const n = p.eyes.length;
  const idx = Math.max(0, p.eyes.findIndex((e) => e.id === p.selectedId));
  const eye = p.eyes[idx];
  const rev = useRevealFrame(eye);       // the Reveal's frame for the selected eye (a hook: it runs before the early return below)
  const sel = p.picker.selected;
  const shown = p.art ?? p.staleArt;
  const composing = !p.art && !p.composeError;
  // the frame of an artwork that has just been made is empty until its picture has decoded (src/motion/ArtImage.tsx): it keeps the composing marks meanwhile,
  // the status for a screen reader and the hairline, so that it is never black and mute for the second a large picture takes
  const waitingMarks = (
    <>
      <span role="status" className="sr-only">{T.result.composing}</span>
      <span aria-hidden="true" className="fx-hair" />
    </>
  );
  const samples = p.eyes.filter((e) => e.sample).length;
  const allSample = samples > 0 && samples === n;
  if (!eye) return null;
  // the frame's shape: the picture's own once there is one (a style draws its own canvas), else the legacy shape of the old layouts
  const expected = shown && shown.w > 0 && shown.h > 0 ? { w: shown.w, h: shown.h } : canvasSize(n, p.layout ?? '');
  const artTitle = allSample ? T.result.sampleArtwork : T.result.artwork;
  const artAlt = samples ? `${artTitle} (${T.result.sampleBadge})` : artTitle;
  const retakeLabel = eye.sample ? T.result.replaceSample : n > 1 ? T.result.retakeEye(idx + 1) : T.result.retakeOnly;
  // the eyes the retake state names (a rule they fail holds a tile back, or warns on the style on screen): a badge on the chip
  const flagged = new Set<number>([...(p.picker.retake?.eyes ?? []), ...(p.picker.retake?.reseal ?? []), ...(p.picker.retake?.pupil ?? []), ...p.picker.advisory]);
  // the tile list is here and no style can be drawn from it: the frame never waits for a picture that will not come, whatever the retake state is (it is
  // null for a list with no style at all, and a pupil or a gate has its own sentences)
  const noPreview = !!p.picker.catalog && !p.picker.style;

  // The Reveal (src/reveal, WP9): the photo left of a hard cut, the restored iris right of it. When the server withheld the cut (the colour drifted, or
  // photo and restoration do not register) the same two pictures show side by side as a strip, with the note and, for a colour drift, the colour check's
  // retake advice. Without the server's numbers (an older server, the sample eye, no time left there) the plain slider below stays.
  const R = T.result.reveal;
  const revealLabels = { photo: R.photo, iris: R.iris, slider: R.slider, valueText: R.valueText };
  const stripAlts = { photo: R.photo, iris: R.iris, art: T.result.artwork };
  const stripCaptions = { photo: R.photo, iris: R.iris, art: R.art };
  const revealHero = rev.view === 'cut' ? (
    <div className="mx-auto w-full max-w-[640px]" data-testid="reveal-hero">
      {rev.frame
        ? <Reveal key={eye.id} photo={rev.frame.url} restored={rev.restored} geometry={rev.frame.geometry} labels={revealLabels} ready={rev.ready} />
        : <div className="aspect-square w-full rounded-2xl bg-black border border-white/10" />}
    </div>
  ) : rev.view === 'strip' ? (
    <div data-testid="reveal-withheld">
      {rev.frame && (
        <RevealStrip key={eye.id} wide={rev.frame.url} restored={rev.restored} art={n === 1 ? (shown?.src ?? null) : undefined} geometry={rev.frame.geometry}
          captions={stripCaptions} alts={stripAlts} />
      )}
      <p data-testid="no-cut" className="text-xs text-amber-200/90 mt-3 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 flex gap-2">
        <AlertTriangle className="w-4 h-4 shrink-0 mt-px text-amber-300" /> <span>{R.noCut}</span>
      </p>
    </div>
  ) : null;
  // The colour check's warning (the engine's own check failed for this eye, or the Reveal was withheld because the restored colour drifted from the photo).
  // It comes BEFORE the transparency sentence, and while it shows the promise line ("we never recolour your iris") does not: the two together would
  // contradict each other on exactly the eyes where the promise is under strain (the p09f case). The transparency sentence stays: it is also the AI
  // disclosure, and it says where the colour comes from, which the warning then qualifies.
  const colourNote = !eye.sample && (eye.colourOff || withheldByColour(rev.rv));
  const colourWarning = colourNote ? (
    <p data-testid="colour-off" className="text-xs text-amber-200/90 mt-3 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 flex gap-2">
      <AlertTriangle className="w-4 h-4 shrink-0 mt-px text-amber-300" /> <span>{T.result.colourOff}</span>
    </p>
  ) : null;
  // one eye on the artwork: the same eye three times, between the Reveal and the style tiles
  const stripSection = n === 1 && rev.view === 'cut' && rev.frame ? (
    <div data-testid="strip-section">
      <h2 className="font-luxury text-xl font-bold">{R.stripTitle}</h2>
      <p className="text-xs text-zinc-400 mt-1 mb-3">{R.stripIntro}</p>
      <RevealStrip key={eye.id} wide={rev.frame.url} restored={rev.restored} art={shown?.src ?? null} geometry={rev.frame.geometry}
        captions={stripCaptions} alts={stripAlts} />
    </div>
  ) : null;

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
        <div className="flex gap-2 overflow-x-auto pb-2 mb-1 -mx-1 px-1">
          <div role="tablist" aria-label={T.result.eyes} className="flex gap-2">
            {p.eyes.map((e, i) => (
              <button key={e.id} role="tab" aria-selected={i === idx} onClick={() => p.onSelect(e.id)} data-flagged={flagged.has(i + 1) || undefined}
                aria-label={flagged.has(i + 1) ? T.picker.chipLabel(i + 1) : undefined}
                className="shrink-0 flex flex-col items-center gap-1 w-16 pt-1">
                <img {...NO_SAVE} src={e.thumb} alt="" className={`fx-pick w-12 h-12 rounded-full object-cover border-2 ${flagged.has(i + 1) ? 'border-amber-400' : i === idx ? 'fx-pop border-[#f5c542] ring-2 ring-[#f5c542]/40' : 'border-white/15 opacity-75'}`} />
                <span className={`text-[10px] font-bold leading-tight text-center ${i === idx ? 'text-[#f5c542]' : 'text-zinc-300'}`}>
                  {T.result.eyeLabel(i + 1)}
                  {e.sample && <span className="block text-[9px] font-semibold text-amber-200/90">{T.result.sampleLabel}</span>}
                  {flagged.has(i + 1) && <span data-testid={`chip-retake-${i + 1}`} className="block text-[9px] font-semibold text-amber-200">{T.picker.chipRetake}</span>}
                </span>
              </button>
            ))}
          </div>
          {/* the add button is no tab: it stands beside the tab list, not inside it */}
          {n < MAX_EYES && (
            <button onClick={p.onAdd} aria-label={T.result.addAnother}
              className="shrink-0 mt-1 w-12 h-12 rounded-full border-2 border-dashed border-[#f5c542]/50 text-[#f5c542] flex items-center justify-center">
              <Plus className="w-5 h-5" />
            </button>
          )}
        </div>
      )}
      {revealHero ?? (
        <CompareSlider key={eye.id} sweepKey={eye.id} before={eye.before} after={`data:image/jpeg;base64,${eye.image}`}
          beforeLabel={eye.sample ? T.result.samplePhoto : T.result.yourPhoto} afterLabel={T.result.after} />
      )}
      {colourWarning}
      {/* decision 5 speaks about the customer's own photo, so the sample gets its own line instead */}
      {eye.sample
        ? <p className="text-xs text-amber-100 mt-3 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3">{T.result.sampleNote}</p>
        : <p data-testid="transparency" className="text-xs text-zinc-200 mt-3 bg-white/5 border border-white/10 rounded-xl p-3">{T.result.transparency}</p>}
      {/* the shared library of plates (release review H-M1): the page says "we never hide what the AI does", so the sentence the terms carry is here too, under the line above,
          for the customer's own photo (the sample has no style of its own to sell) */}
      {!eye.sample && AI_MATERIAL_PUBLISHED && <p data-testid="ai-material" className="text-xs text-zinc-300 mt-2">{T.result.aiMaterial}</p>}
      {revealHero && !colourNote && <p data-testid="promise" className="text-xs text-zinc-300 mt-2">{R.promise}</p>}
      <p className="text-[11px] text-zinc-400 mt-2">
        {[
          rev.view === 'cut' ? R.drag : rev.view === 'strip' ? '' : T.result.drag,
          eye.diameterPx && !eye.sample ? T.result.irisPx(eye.diameterPx) : '',
          eye.glarePct >= 0.4 ? T.result.reflection : '',
          eye.usedSr ? T.result.upscaled : '',
        ].filter(Boolean).join(' ')}
      </p>
      {rev.view !== 'plain' && rev.rv?.soft && <p data-testid="soft-tip" className="text-[11px] text-amber-200 mt-1">{R.softTip}</p>}
      {rev.view === 'cut' && rev.frame && (
        <p data-testid="frame-note" className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
          <Check className="w-3 h-3" /> {rev.frame.geometry.plan.mode === 'wide' ? R.frameWide : R.frameTight}
        </p>
      )}
      {eye.stored && <p className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1"><Check className="w-3 h-3" /> {T.result.stored}</p>}
      <div className={`grid gap-2 mt-3 ${n > 1 ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <button onClick={() => p.onRetake(eye.id)}
          className={`min-h-[44px] px-3 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 ${(eye.colourOff && !eye.sample) || flagged.has(idx + 1) ? 'border-amber-400/50 bg-amber-500/10 text-amber-100' : 'border-white/10 bg-white/5 text-zinc-200'}`}>
          <RefreshCcw className="w-4 h-4" /> {retakeLabel}
        </button>
        {n > 1 && (
          <button onClick={() => p.onRemove(eye.id)}
            className="min-h-[44px] px-3 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-zinc-300 flex items-center justify-center gap-2">
            <Trash2 className="w-4 h-4" /> {T.result.remove(idx + 1)}
          </button>
        )}
        {/* four to eight eyes: the order on the artwork is the order of the eyes, so an eye moves one place at a time */}
        {n >= 4 && (
          <>
            <button type="button" data-testid="move-earlier" disabled={idx === 0} aria-label={T.picker.options.earlierLabel(idx + 1)} onClick={() => p.onMove(eye.id, -1)}
              className="min-h-[44px] px-3 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-zinc-200 disabled:opacity-40">{T.picker.options.earlier}</button>
            <button type="button" data-testid="move-later" disabled={idx === n - 1} aria-label={T.picker.options.laterLabel(idx + 1)} onClick={() => p.onMove(eye.id, 1)}
              className="min-h-[44px] px-3 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-zinc-200 disabled:opacity-40">{T.picker.options.later}</button>
          </>
        )}
      </div>
    </div>
  );

  // what the customer has chosen opens soon: the style, or (a style that can be bought) the look on screen
  const soonSelected = soonChoice(sel, p.picker.look);
  const soonLook = !!sel && !!p.picker.look && sel.looks[p.picker.look] === 'preview' && sel.stage !== 'preview' ? p.picker.look : null;
  const fallback = shown?.fallback;
  const artwork = (
    <div>
      <div className="flex items-center justify-between gap-2 mb-2">
        <h2 className="font-luxury text-xl font-bold">{artTitle}</h2>
        {/* beside the picture, not over it: the engine's watermark banner runs along its top edge */}
        {samples > 0 && (
          <span data-testid="sample-badge" className="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-amber-400/50 text-amber-200 bg-amber-500/10">{T.result.sampleBadge}</span>
        )}
      </div>
      {noPreview ? (
        <div data-testid="no-preview">
          {p.picker.retake ? (
            <>
              <p className="text-sm text-zinc-200 mb-2">{T.picker.retake.noPreview}</p>
              <RetakePanel view={p.picker.retake} total={n} onRetake={p.picker.onRetakeEye} onRemove={p.picker.onRemoveEye} onManual={p.picker.onManual} inPlace />
            </>
          ) : (
            // no style for this many eyes at all: say so, and the way to ask us (the eye's own retake and remove buttons are under the picture)
            <div data-testid="no-styles" className="text-xs text-amber-50 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3">
              <p className="text-sm text-amber-100">{T.picker.retake.noStyles}</p>
              <ManualRoute onManual={p.picker.onManual} />
            </div>
          )}
        </div>
      ) : (
        <>
          <div data-testid="artwork" className="fx-frame relative w-full rounded-2xl overflow-hidden border border-white/10 bg-black"
            {...NO_SAVE_BOX} style={{ ...NO_SAVE_BOX.style, aspectRatio: `${expected.w} / ${expected.h}` }}>
            {shown && <ArtImage {...NO_SAVE} src={shown.src} alt={artAlt} arrive={p.arrive} onOpened={p.onArrived} waiting={composing ? null : waitingMarks} className={`fx-dim absolute inset-0 w-full h-full object-contain ${p.art ? '' : 'opacity-50'}`} />}
            {/* composing: the stale picture stays, dimmed (it tells the truth), and a hairline of gold runs along the frame's top edge; a screen reader hears the state once */}
            {composing && (shown
              ? <span role="status" className="sr-only">{T.result.composing}</span>
              : <div role="status" className="absolute inset-0 flex items-center justify-center text-zinc-300 text-sm">{T.result.composing}</div>)}
            {composing && <span aria-hidden="true" className="fx-hair" />}
            {!p.art && p.composeError && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/70 text-center px-6">
                <p className="text-sm text-rose-200">{T.result.composeFailed} {p.composeError}</p>
                <button onClick={p.onRetryCompose} className="px-4 py-2 rounded-xl bg-white/10 border border-white/20 text-sm font-semibold flex items-center gap-2"><RefreshCcw className="w-4 h-4" /> {T.result.retry}</button>
              </div>
            )}
          </div>
          {/* under a shown artwork only; what the file is, only when this artwork can be bought (not the AI sample alone, not a style that opens soon) */}
          {shown && (
            <p data-testid="preview-note" className="text-[11px] text-zinc-300 mt-2">
              {allSample ? T.result.previewReduced : soonSelected ? `${T.result.previewReduced} ${soonLook ? T.picker.soonLookNote(lookName(soonLook)) : T.picker.soonNote}` : `${T.result.previewReduced} ${T.result.previewFile(expected.w === expected.h)}`}
            </p>
          )}
        </>
      )}
      {fallback === 'overlap_fallback' && <p data-testid="wide-pupil" className="text-[11px] text-sky-100 mt-2">{T.picker.widePupil}</p>}
      {fallback === 'stack_contrast' && <p data-testid="stack-note" className="text-[11px] text-sky-100 mt-2">{T.picker.stack}</p>}
      {p.picker.advisory.length > 0 && (
        <p role="status" data-testid="advisory-note" className="text-xs text-amber-100 mt-2 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 flex gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-px text-amber-300" /> <span>{T.picker.advisory(p.picker.advisory, n)}</span>
        </p>
      )}
      {samples > 0 && <p className="text-[11px] text-amber-200/90 mt-2">{allSample ? T.result.sampleArtworkNote : T.result.mixedArtworkNote}</p>}

      <p className="text-[10px] uppercase tracking-widest text-zinc-300 mt-4">{T.result.style}</p>
      <StylePicker model={p.picker} />
      {p.picker.retake && !noPreview && <RetakePanel view={p.picker.retake} total={n} onRetake={p.picker.onRetakeEye} onRemove={p.picker.onRemoveEye} onManual={p.picker.onManual} />}

      {p.layoutOptions.length > 1 && (
        <div className="mt-3">
          <p className="text-[10px] uppercase tracking-widest text-zinc-300 mb-1.5">{T.result.layout}</p>
          <div role="radiogroup" aria-label={T.result.layout} className={`grid gap-2 ${p.layoutOptions.length === 2 ? 'grid-cols-2' : 'grid-cols-3'}`}>
            {p.layoutOptions.map((l) => (
              <button key={l} role="radio" aria-checked={p.layout === l} onClick={() => p.onLayout(l)}
                className={`fx-pick min-h-[44px] py-2.5 rounded-xl border text-sm font-semibold flex items-center justify-center gap-2 ${p.layout === l ? 'border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]' : 'border-white/10 bg-white/5 text-zinc-300'}`}>
                <LayoutGlyph layout={l} n={n} /> {layoutLabel(l)}
              </button>
            ))}
          </div>
        </div>
      )}
      {/* the places of the eyes: two eyes swap, three rotate (a new arrangement of the same eyes; the style keeps its look) */}
      {sel && sel.legacy !== 1 && (n === 2 || n === 3) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {n === 2 && (
            <button type="button" data-testid="swap-places" aria-pressed={p.opts.swap} onClick={() => p.onOpts({ ...p.opts, swap: !p.opts.swap })}
              className={`fx-pick min-h-[44px] px-3 rounded-xl border text-sm font-semibold ${p.opts.swap ? 'border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]' : 'border-white/10 bg-white/5 text-zinc-200'}`}>{T.picker.options.swap}</button>
          )}
          {n === 3 && (
            <button type="button" data-testid="rotate-places" onClick={() => p.onOpts({ ...p.opts, rotate: (p.opts.rotate + 1) % 3 })}
              className="min-h-[44px] px-3 rounded-xl border border-white/10 bg-white/5 text-sm font-semibold text-zinc-200">{T.picker.options.rotate}</button>
          )}
        </div>
      )}

      <Words model={p.words} />

      <div className={`grid gap-3 mt-3 ${n < MAX_EYES ? 'grid-cols-2' : 'grid-cols-1'}`}>
        <a href={p.art?.src || '#'} download={T.result.fileName(sel?.slug ?? 'artwork', n, samples > 0)}
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
      <p className="text-[11px] text-zinc-400 mt-2">{n < MAX_EYES ? T.result.addHint(MAX_EYES - n) : T.result.full(MAX_EYES)}</p>
    </div>
  );

  return (
    <section className={`flex flex-col gap-6${p.enter ? ' fx-step' : ''}`}>
      {/* One eye: its before/after is the surprise, so it leads. Two or more: the artwork of all of them is
          what the couple came for, so it leads and the per-eye before/after follows. */}
      {n > 1 ? <>{artwork}{beforeAfter}</> : <>{beforeAfter}{stripSection}{artwork}</>}

      {p.purchase}

      <button onClick={p.onStartOver} className="text-xs text-zinc-300 underline underline-offset-4 self-center">{T.result.startOver}</button>
    </section>
  );
};

const FidelityBadge: React.FC<{ eye: Eye }> = ({ eye }) => (eye.fallback
  ? <span className="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-amber-400/40 text-amber-200 bg-amber-500/10">{T.result.badgeFallback}</span>
  : <span className="shrink-0 text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border border-[#f5c542]/50 text-[#f5c542] bg-[#f5c542]/10">{T.result.badgeMacro}</span>);

/** Where the discs of a layout go in a 20 x 16 box, so that "Fusion" and "Side by side", a trio, a ring and the rest read at a glance. The ids are the
 *  registry's (api/_lib/styles_registry.py layouts): the old ones and the v3 ones; an id this does not know draws as one disc. */
export function glyphPoints(layout: string, n: number): { pts: Array<[number, number]>; r: number } {
  const line = (k: number): Array<[number, number]> => Array.from({ length: k }, (_, i) => [2 + (16 / Math.max(1, k - 1)) * i, 8] as [number, number]);
  const ring = (k: number): Array<[number, number]> => Array.from({ length: k }, (_, i) => [10 + 5.5 * Math.cos((2 * Math.PI * i) / k - Math.PI / 2), 8 + 5 * Math.sin((2 * Math.PI * i) / k - Math.PI / 2)] as [number, number]);
  switch (layout) {
    case 'duo': case 'pair': return { pts: [[6, 8], [14, 8]], r: 3.2 };
    case 'fusion': return { pts: [[7.5, 8], [12.5, 8]], r: 3.2 };
    case 'triangle': case 'trio': return { pts: [[10, 4.5], [6, 11.5], [14, 11.5]], r: 3.2 };
    case 'diag': return { pts: [[5, 12], [10, 8], [15, 4]], r: 3 };
    case 'grid': return { pts: [[6.5, 4.5], [13.5, 4.5], [6.5, 11.5], [13.5, 11.5]], r: 3.2 };
    case 'row': case 'chain': return { pts: line(Math.max(2, n)), r: Math.min(3.2, 16 / Math.max(1, n - 1) / 2 - 0.5) };
    case 'zigzag': return { pts: line(Math.max(2, n)).map(([x], i) => [x, i % 2 ? 11 : 5] as [number, number]), r: Math.min(2.8, 16 / Math.max(1, n - 1) / 2) };
    case 'brick': {
      const top = Math.ceil(n / 2), bottom = n - top;
      const row = (k: number, y: number): Array<[number, number]> => Array.from({ length: k }, (_, i) => [10 + (i - (k - 1) / 2) * 5.5, y] as [number, number]);
      return { pts: [...row(top, 4.8), ...row(bottom, 11.2)], r: 2.5 };
    }
    case 'ring': return { pts: ring(Math.max(3, n)), r: 2.3 };
    case 'flower': return { pts: [[10, 8], ...ring(Math.max(2, n - 1))], r: 2.2 };
    case 'cluster': return { pts: ring(Math.max(3, n)).map(([x, y], i) => [10 + (x - 10) * (i % 2 ? 0.6 : 1), 8 + (y - 8) * (i % 2 ? 0.6 : 1)] as [number, number]), r: 2.6 };
    default: return { pts: [[10, 8]], r: 3.2 };
  }
}

const LayoutGlyph: React.FC<{ layout: string; n: number }> = ({ layout, n }) => {
  const { pts, r } = glyphPoints(layout, n);
  return (
    <svg viewBox="0 0 20 16" className="w-5 h-4" aria-hidden>
      {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={r} fill="none" stroke="currentColor" strokeWidth="1.2" />)}
    </svg>
  );
};
