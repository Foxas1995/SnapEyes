import React from 'react';
import { RefreshCcw } from 'lucide-react';
import { T, type BlockCopy } from './copy';

/** Shown for a shot the engine blocked (too blurry, pupil too wide, ...): a title that says why and the capture
 *  guide's steps for that reason, once. The server's own message is not repeated here: it lists the same steps.
 *  There is deliberately no way forward from here: the server issued no work ticket. */
export const RetakeGuide: React.FC<{ block: BlockCopy }> = ({ block }) => (
  <div role="alert" data-testid="retake-guide" className="bg-rose-950/30 border border-rose-500/40 rounded-2xl p-4">
    <p className="text-sm font-bold text-rose-200 flex items-center gap-2">
      <RefreshCcw className="w-4 h-4 shrink-0 text-rose-300" /> {block.title}
    </p>
    <p className="text-[10px] uppercase tracking-widest text-zinc-400 mt-3">{T.quality.guideTitle}</p>
    <ol className="mt-1.5 space-y-1.5 text-xs text-zinc-200">
      {block.steps.map((s, i) => (
        <li key={s} className="flex gap-2">
          <span className="w-4 h-4 shrink-0 rounded-full bg-[#f5c542]/15 text-[#f5c542] text-[10px] font-bold flex items-center justify-center">{i + 1}</span>
          <span>{s}</span>
        </li>
      ))}
    </ol>
  </div>
);
