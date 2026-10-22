import React from 'react';
import { AlertTriangle, Check, Download, Info, Plus, RefreshCcw, Trash2 } from 'lucide-react';
import { CompareSlider } from './CompareSlider';
import { ArtImage } from '../motion/ArtImage';
import { Reveal } from '../reveal/Reveal';
import { withheldByColour } from '../reveal/revealMath';
import { useRevealFrame } from '../reveal/useRevealFrame';
import { AI_MATERIAL_PUBLISHED } from '../shared/aiMaterial';
import { T, layoutLabel } from './copy';
import { NO_SAVE, NO_SAVE_BOX } from './noSave';
import { type Art, type Eye, MAX_EYES, canvasSize, pupilWide } from './multi';
import { CalmRetake, ManualRoute, StylePicker, type PickerModel } from './StylePicker';
import { Words, type WordsModel } from './Words';
import { FeedbackBox } from './Feedback';
import { type Opts, lookName, retakeEyes, soonChoice } from './picker';
import { CROP_MAX_PX } from './crop';

interface Props {
  eyes: Eye[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRemove: (id: string) => void;
  onRetake: (id: string) => void;
  onAdd: () => void;
  onMove: (id: string, delta: -1 | 1) => void;   // an eye one place earlier or later on the artwork (four to eight eyes)
  onCentre: (id: string) => void;                // an eye in the centre of an arrangement that has one (the layout orbit: the first eye is the hub)
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
  // an arrangement with an eye in its centre (the layout orbit of Family Orbit: the first eye of the order is the hub, the customer chooses which)
  const hub = n >= 3 && p.layout === 'orbit' && !!p.picker.selected && p.picker.selected.legacy !== 1;
  const samples = p.eyes.filter((e) => e.sample).length;
  const allSample = samples > 0 && samples === n;
  if (!eye) return null;
  // the frame's shape: the picture's own once there is one (a style draws its own canvas), else the legacy shape of the old layouts
  const expected = shown && shown.w > 0 && shown.h > 0 ? { w: shown.w, h: shown.h } : canvasSize(n, p.layout ?? '');
  const artTitle = allSample ? T.result.sampleArtwork : T.result.artwork;
  const artAlt = samples ? `${artTitle} (${T.result.sampleBadge})` : artTitle;
  const retakeLabel = eye.sample ? T.result.replaceSample : n > 1 ? T.result.retakeEye(idx + 1) : T.result.retakeOnly;
  // the tile list is here and no style can be drawn from it: the frame never waits for a picture that will not come, whatever the retake state is (it is
  // null for a list with no style at all; held tiles are not shown, so this and the buy card's retake line are the only places that ask for a retake)
  const noPreview = !!p.picker.catalog && !p.picker.style;
  // the eyes marked on their chips: the ones a style on screen warns about (advisory) and, when no style can be drawn, the ones to photograph again. An eye
  // that only holds back a style which is not shown is not marked (the owner, 2026-10-22: not telling every customer what does not fit)
  const flagged = new Set<number>([...(noPreview ? retakeEyes(p.picker.retake) : []), ...p.picker.advisory]);

  // The before/after leads every eye (the owner, 2026-10-20: "the before and after that slides is the most important thing"). The Reveal (src/reveal, WP9: the
  // photo left of a line through the pupil, the restored iris right of it) when the server gives its numbers and passes them; every other eye gets the plain
  // slider: the client crop /api/deglare took against the display copy made from it, the same square by construction, so it needs no registration. That is
  // also the eye whose Reveal the server withheld (the colour drifted, or photo and restoration do not register): no strip of thumbnails and no note about a
  // "cut" any more, only the colour note below when the colour drifted.
  const R = T.result.reveal;
  const revealLabels = { photo: R.photo, iris: R.iris, slider: R.slider, valueText: R.valueText };
  const hero = rev.view === 'cut' ? (
    <div className="mx-auto w-full max-w-[640px]" data-testid="reveal-hero">
      {rev.frame
        ? <Reveal key={eye.id} photo={rev.frame.url} restored={rev.restored} geometry={rev.frame.geometry} labels={revealLabels} ready={rev.ready} />
        : <div className="aspect-square w-full rounded-2xl bg-black border border-white/10" />}
    </div>
  ) : (
    <div data-testid="slider-hero">
      <CompareSlider key={eye.id} sweepKey={eye.id} before={eye.before} after={`data:image/jpeg;base64,${eye.image}`}
        beforeLabel={eye.sample ? T.result.samplePhoto : T.result.yourPhoto} afterLabel={T.result.after} />
    </div>
  );
  // The colour check's warning (the engine's own check failed for this eye, or the Reveal was withheld because the restored colour drifted from the photo).
  // It comes BEFORE the transparency sentence, and while it shows the promise line ("we never recolour your iris") does not: the two together would
  // contradict each other on exactly the eyes where the promise is under strain (the p09f case). The transparency sentence stays (in the disclosure): it is
  // also the AI disclosure, and it says where the colour comes from, which the warning then qualifies.
  const colourNote = !eye.sample && (eye.colourOff || withheldByColour(rev.rv));
  const colourWarning = colourNote ? (
    <p data-testid="colour-off" className="text-xs text-amber-200/90 mt-3 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 flex gap-2">
      <AlertTriangle className="w-4 h-4 shrink-0 mt-px text-amber-300" /> <span>{T.result.colourOff}</span>
    </p>
  ) : null;
  // the server measured this eye against its photo (the Reveal's numbers came, shown or withheld for registration): the promise may stand where the colour is fine
  const measured = rev.view !== 'plain';

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
      {hero}
      {colourWarning}
      {/* one line, only for a wide pupil: the studio keeps the photo's pupil, more light is what makes it smaller */}
      {pupilWide(eye) && (
        <p data-testid="pupil-hint" className="text-[11px] text-zinc-300 mt-3 flex gap-1.5"><Info aria-hidden="true" className="w-3.5 h-3.5 shrink-0 mt-px text-zinc-400" /> <span>{T.result.pupilWide}</span></p>
      )}
      {/* decision 5 speaks about the customer's own photo, so the sample gets its own line instead of the card */}
      {eye.sample
        ? <p className="text-xs text-amber-100 mt-3 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3">{T.result.sampleNote}</p>
        : <WhatWeDid eye={eye} colourNote={colourNote} promised={measured && !colourNote} soft={measured && !!rev.rv?.soft} />}
      {eye.stored && <p className="text-[11px] text-emerald-400 mt-2 flex items-center gap-1"><Check className="w-3 h-3" /> {T.result.stored}</p>}
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
        {hub && (
          <button type="button" data-testid="centre-eye" disabled={idx === 0} aria-pressed={idx === 0} aria-label={T.picker.options.centreLabel(idx + 1)} onClick={() => p.onCentre(eye.id)}
            className={`fx-pick min-h-[44px] px-3 rounded-xl border text-sm font-semibold ${idx === 0 ? 'border-[#f5c542] bg-[#f5c542]/10 text-[#f5c542]' : 'border-white/10 bg-white/5 text-zinc-200'}`}>{T.picker.options.centre}</button>
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
            // every style of the list is held back for these eyes: one calm line and the retake button (no reasons, no tips, no warning)
            <CalmRetake view={p.picker.retake} total={n} onRetake={p.picker.onRetakeEye} onRemove={p.picker.onRemoveEye} />
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
      {/* the style on screen draws an eye that failed its rule: one calm line, no warning sign (the eye's own retake button is under its before/after) */}
      {p.picker.advisory.length > 0 && (
        <p role="status" data-testid="advisory-note" className="text-[11px] text-zinc-300 mt-2 flex gap-1.5">
          <Info aria-hidden="true" className="w-3.5 h-3.5 shrink-0 mt-px text-zinc-400" /> <span>{T.picker.advisory(p.picker.advisory, n)}</span>
        </p>
      )}
      {samples > 0 && <p className="text-[11px] text-amber-200/90 mt-2">{allSample ? T.result.sampleArtworkNote : T.result.mixedArtworkNote}</p>}

      <p className="text-[10px] uppercase tracking-widest text-zinc-300 mt-4">{T.result.style}</p>
      {/* the styles these eyes can take; a style held back for them is not shown, and nothing under the list asks for a retake (the owner, 2026-10-22) */}
      <StylePicker model={p.picker} />

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
      {hub && <p data-testid="centre-note" className="text-[11px] text-zinc-300 mt-2">{T.picker.options.centreNote}</p>}
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
      {n > 1 ? <>{artwork}{beforeAfter}</> : <>{beforeAfter}{artwork}</>}

      {p.purchase}

      {/* the anonymous feedback box (api/_lib/feedback.py): after the price, never in the way of it, and only once a preview is on screen; it shows itself only when the server keeps the answers */}
      {p.art && <FeedbackBox where="result" ctx={p.picker.style ?? undefined} eyes={n} />}

      <button onClick={p.onStartOver} className="text-xs text-zinc-300 underline underline-offset-4 self-center">{T.result.startOver}</button>
    </section>
  );
};

/** At most this many check lines say what was done (the owner, 2026-10-20: one compact block, no long text under the before/after). */
const DID_MAX = 3;

/** What the studio did to this photo (the owner, 2026-10-20; the words: copy.ts result.did): one compact card under the before/after, at most DID_MAX short check
 *  lines and, under them, the one closed disclosure for everything longer. The reflection line only when one was found, the eyelid line only when an eyelid was
 *  filled from the iris itself; the colour line steps aside while the colour note shows (it says the light moved) and when the reflection and the eyelid lines
 *  both show (the eyelid line is the one the owner asked for).
 *  The disclosure (closed until the visitor opens it, the same screen): where the colour comes from and what the AI restores (transparency, decision 5: also the
 *  AI disclosure), the promise where the server measured the eye and the colour is fine, else "nothing painted on top" (never both: they say one thing; neither
 *  beside the colour note), the shared library of plates (the sentence the terms carry, while published), what the photo goes through (the camera's quality),
 *  and the notes of a small photo. Folded, never deleted: what counsel may need stays on the page. */
const WhatWeDid: React.FC<{ eye: Eye; colourNote: boolean; promised: boolean; soft: boolean }> = ({ eye, colourNote, promised, soft }) => {
  const D = T.result.did;
  const lid = (eye.lidPct ?? 0) > 0;
  const all = [eye.glarePct >= 0.4 ? D.glare : '', D.sharp, colourNote ? '' : D.colour, lid ? D.lid : ''].filter(Boolean);
  const lines = all.length > DID_MAX ? all.filter((l) => l !== D.colour) : all;
  return (
    <div data-testid="what-we-did" className="mt-3 rounded-xl border border-white/10 bg-white/5">
      <div className="px-3 pt-3 pb-2">
        <h3 className="text-xs font-bold text-zinc-100">{D.title}</h3>
        <ul className="mt-1.5 space-y-1">
          {lines.map((l) => (
            <li key={l} className="flex gap-2 text-xs text-zinc-200"><Check className="w-3.5 h-3.5 shrink-0 mt-px text-emerald-400" aria-hidden="true" /><span>{l}</span></li>
          ))}
        </ul>
      </div>
      <details data-testid="how-it-works" className="border-t border-white/10">
        <summary className="cursor-pointer px-3 py-3 min-h-[44px] text-xs font-semibold text-zinc-200">{T.result.how}</summary>
        <div className="px-3 pb-3 flex flex-col gap-2 text-[11px] leading-snug text-zinc-300">
          <p data-testid="transparency">{T.result.transparency}</p>
          {!colourNote && (promised ? <p data-testid="promise">{T.result.reveal.promise}</p> : <p data-testid="nothing">{D.nothing}</p>)}
          {/* the shared library of plates (release review H-M1): the page says "we never hide what the AI does", so the sentence the terms carry is here too */}
          {AI_MATERIAL_PUBLISHED && <p data-testid="ai-material">{T.result.aiMaterial}</p>}
          <p data-testid="quality-note">{D.quality(CROP_MAX_PX)}</p>
          {eye.usedSr && <p>{T.result.upscaled}</p>}
          {soft && <p data-testid="soft-tip">{T.result.reveal.softTip}</p>}
        </div>
      </details>
    </div>
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
    case 'flower': case 'orbit': return { pts: [[10, 8], ...ring(Math.max(2, n - 1))], r: 2.2 };
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
