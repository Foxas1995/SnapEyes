import React from 'react';
import { T } from './copy';
import { DATE_MAX, FAMILY_MAX, NAME_MAX, NAMES_TOTAL_MAX, type NameProblem } from './names';

/** The customer's own words on the artwork (src/try/names.ts): a name per eye, an optional date and, only for an arrangement that draws one, a family
 *  name. The studio writes nothing else on the artwork. */
export interface WordsModel {
  names: string[];                       // one per eye, in canvas order ('' for none)
  onName: (position: number, v: string) => void;   // 0-based
  date: string;
  onDate: (v: string) => void;
  family: string;
  onFamily: (v: string) => void;
  showFamily: boolean;
  problems: NameProblem[];
}

export function emptyWords(n = 1): WordsModel {
  const no = () => undefined;
  return { names: Array.from({ length: n }, () => ''), onName: no, date: '', onDate: no, family: '', onFamily: no, showFamily: false, problems: [] };
}

const INPUT = 'w-full bg-white/5 border border-white/15 rounded-lg px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-400 focus:outline-none focus:border-[#f5c542] aria-[invalid=true]:border-rose-400/70';
const LABEL = 'block text-[11px] font-semibold text-zinc-300 mb-1';
const BAD = 'text-[11px] text-rose-200 mt-1';

/** The sentence for a problem of the words (the form shows it under the field it belongs to). */
export function problemText(p: NameProblem): string {
  const P = T.picker.names.problem;
  switch (p.code) {
    case 'name_long': return P.nameLong(p.eye, NAME_MAX);
    case 'names_long': return P.namesLong(NAMES_TOTAL_MAX);
    case 'glyph': return P.glyph(p.chars.join(' '));
    case 'date_long': return P.dateLong(DATE_MAX);
    case 'family_long': return P.familyLong(FAMILY_MAX);
  }
}

export const Words: React.FC<{ model: WordsModel }> = ({ model: w }) => {
  const total = w.names.length;
  const at = (i: number) => w.problems.filter((p) => (p.code === 'name_long' || (p.code === 'glyph' && !p.field)) && p.eye === i + 1);
  const dateProblems = w.problems.filter((p) => p.code === 'date_long' || (p.code === 'glyph' && p.field === 'date'));
  const general = w.problems.filter((p) => p.code === 'names_long');
  const famProblems = w.problems.filter((p) => p.code === 'family_long' || (p.code === 'glyph' && p.field === 'family'));
  return (
    <fieldset data-testid="words" className="mt-4 border-0 p-0 m-0 min-w-0">
      <legend className="text-[10px] uppercase tracking-widest text-zinc-300 mb-1.5 p-0">{T.picker.names.title}</legend>
      <div className={`grid gap-2 ${total > 1 ? 'sm:grid-cols-2' : ''}`}>
        {w.names.map((v, i) => {
          const id = `name-${i + 1}`;
          const bad = at(i);
          return (
            <div key={i} className="min-w-0">
              <label htmlFor={id} className={LABEL}>{T.picker.names.nameFor(i + 1, total)}</label>
              <input id={id} data-testid={id} value={v} maxLength={NAME_MAX} autoComplete="off" spellCheck={false} onChange={(e) => w.onName(i, e.target.value)}
                aria-invalid={bad.length ? true : undefined} aria-describedby={bad.length ? `${id}-problem` : undefined} className={INPUT} />
              {bad.length > 0 && <p id={`${id}-problem`} role="alert" className={BAD}>{bad.map(problemText).join(' ')}</p>}
            </div>
          );
        })}
      </div>
      {general.length > 0 && <p role="alert" className={BAD}>{general.map(problemText).join(' ')}</p>}
      <div className={`grid gap-2 mt-2 ${w.showFamily ? 'sm:grid-cols-2' : ''}`}>
        <div className="min-w-0">
          <label htmlFor="words-date" className={LABEL}>{T.picker.names.date}</label>
          <input id="words-date" data-testid="words-date" value={w.date} maxLength={DATE_MAX} autoComplete="off" placeholder={T.picker.names.datePlaceholder} onChange={(e) => w.onDate(e.target.value)}
            aria-invalid={dateProblems.length ? true : undefined} aria-describedby={dateProblems.length ? 'words-date-problem' : undefined} className={INPUT} />
          {dateProblems.length > 0 && <p id="words-date-problem" role="alert" className={BAD}>{dateProblems.map(problemText).join(' ')}</p>}
        </div>
        {w.showFamily && (
          <div className="min-w-0">
            <label htmlFor="words-family" className={LABEL}>{T.picker.names.family}</label>
            <input id="words-family" data-testid="words-family" value={w.family} maxLength={FAMILY_MAX} autoComplete="off" onChange={(e) => w.onFamily(e.target.value)}
              aria-invalid={famProblems.length ? true : undefined} aria-describedby={famProblems.length ? 'words-family-problem' : undefined} className={INPUT} />
            {famProblems.length > 0 && <p id="words-family-problem" role="alert" className={BAD}>{famProblems.map(problemText).join(' ')}</p>}
          </div>
        )}
      </div>
    </fieldset>
  );
};
