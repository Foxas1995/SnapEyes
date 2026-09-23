import React from 'react';
import { T } from './copy';
import { LIGHT_ANSWERS, type LightAnswer, type StudyPayload } from './multi';

/** The two quick questions after each analysed shot in study mode (?study=1), including the shots the engine
 *  found no eye in. Answers are kept in the page only and ride along with the next /api/analyze requests
 *  until one the engine logs comes back; nothing is written to the browser. */
export const StudyCard: React.FC<{
  ask: StudyPayload;
  onLight: (l: LightAnswer) => void;
  onComfort: (c: number) => void;
  onSkip: () => void;
}> = ({ ask, onLight, onComfort, onSkip }) => {
  const done = ask.light !== null && ask.comfort !== null;
  return (
    <section aria-label={T.study.title(ask.shot, ask.photos)} className="mb-4 bg-sky-950/30 border border-sky-400/30 rounded-2xl p-3 text-xs text-sky-100">
      <div className="flex items-center justify-between gap-2">
        <span className="font-bold uppercase tracking-widest text-[10px] text-sky-300">{T.study.title(ask.shot, ask.photos)}</span>
        {!done && <button onClick={onSkip} className="text-[11px] text-sky-300/80 underline underline-offset-2">{T.study.skip}</button>}
      </div>
      {done ? (
        <p className="mt-2 text-sky-200">{T.study.thanks}</p>
      ) : (
        <>
          <p className="mt-2 font-semibold">{T.study.light}</p>
          <div className="grid grid-cols-2 gap-1.5 mt-1.5">
            {LIGHT_ANSWERS.map((l) => (
              <button key={l} onClick={() => onLight(l)} aria-pressed={ask.light === l}
                className={`py-2 px-2 rounded-lg border text-[11px] font-semibold ${ask.light === l ? 'bg-sky-400 text-black border-sky-300' : 'bg-white/5 border-white/10'}`}>
                {T.study.lights[l]}
              </button>
            ))}
          </div>
          <p className="mt-3 font-semibold">{T.study.comfort}</p>
          <div className="grid grid-cols-5 gap-1.5 mt-1.5">
            {[1, 2, 3, 4, 5].map((c) => (
              <button key={c} onClick={() => onComfort(c)} aria-pressed={ask.comfort === c}
                className={`py-2 rounded-lg border text-sm font-bold ${ask.comfort === c ? 'bg-sky-400 text-black border-sky-300' : 'bg-white/5 border-white/10'}`}>
                {c}
              </button>
            ))}
          </div>
        </>
      )}
    </section>
  );
};
