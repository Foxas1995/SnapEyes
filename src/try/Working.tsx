import React from 'react';
import { T } from './copy';
import { Arc, Dot, Tick } from '../motion/Tick';

interface Props {
  title: string;
  /** the steps so far, in order: every line but the last `active` ones is finished, the last ones are in hand (the page's own progress, nothing is added) */
  lines: string[];
  /** how many of the last lines are being worked on at once: the first analysis is one request that locates the iris and measures it together, so
   *  neither line may show a check before the answer is there. Default 1. */
  active?: number;
  elapsed: number;
  /** the customer's own crop of the eye: it stays still, a thin gold arc turns around it. Without it (the first analysis) one thin ring carries the arc. */
  image?: string | null;
  note?: string;
  caption?: string;
  /** the step arrives with a transition (the page has changed step before: src/try/TryApp.tsx) */
  enter?: boolean;
}

/** The waiting screens of /try (analysing the photo, restoring the iris), motion spec 7.3. Progress that means something: the list is the real steps the
 *  page has sent to the studio, a finished one gets a drawn check, the one in hand a still dot, and the seconds are the real seconds. No percentage, no bar,
 *  no scan line over the eye (BR-2): the one thing that moves is the arc, and it pauses when the tab is hidden or the screen scrolled away. */
export const Working: React.FC<Props> = ({ title, lines, active = 1, elapsed, image, note, caption, enter = false }) => (
  <section className={`flex flex-col items-center gap-5 py-6 text-center${enter ? ' fx-step' : ''}`}>
    <div className={`wk-disc${image ? '' : ' wk-bare'}`}>
      {image ? <span className="crop"><img src={image} alt={T.working.yourIris} /></span> : null}
      <Arc />
    </div>
    {image && caption && <span className="-mt-3 text-[10px] uppercase tracking-widest text-amber-200/90">{caption}</span>}
    <h2 className="font-luxury text-xl font-bold">{title}</h2>
    {/* a real list that a screen reader announces as it grows: each finished step is heard once (the spec's role="status" on a ul would take the list roles away) */}
    <ul aria-live="polite" className="text-sm text-zinc-300 space-y-1.5">
      {lines.map((l, i) => (
        // keyed by place: two steps with the same words are two steps
        <li key={i} className="fx-line flex items-center gap-2 justify-center">
          {i < lines.length - active ? <Tick /> : <Dot />}
          <span className={i < lines.length - active ? undefined : 'text-zinc-100'}>{l}</span>
        </li>
      ))}
    </ul>
    {note && <p className="fx-note text-xs text-sky-200/90 bg-sky-950/25 border border-sky-500/25 rounded-xl px-3 py-2 max-w-sm">{note}</p>}
    <span className="text-[11px] font-mono tabular-nums text-zinc-500">{T.working.elapsed(elapsed)}</span>
  </section>
);
