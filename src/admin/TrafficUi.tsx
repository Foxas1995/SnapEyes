// The pieces the visitor pages share: the loader that asks one admin action and drops a slow answer to an older question, the filter bar (period, market, language, device, browser), the funnel
// bar, the table of a split and the light. Text only through React text nodes. The words are Lithuanian.
import { useCallback, useEffect, useRef, useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { explain } from './format';
import { BTN, CARD, INPUT, MUTED, Spinner, Tbl, type Tone } from './ui';
import { BR_LT, DEV_LT, LANG_LT, MARKET_LT, bars, groupLt, label, fxLines, valueLt, type Available, type Filters, type Fx, STEP_LT } from './traffic';
import { gateCodeLt, shareText } from './stylesView';

export interface Loaded<T> { data: T | null; err: string; busy: boolean; reload: () => void }

/** Ask one admin action with a body; asking again with another body (a filter changed) drops the answer of the older question. */
export function useReport<T>(call: Call, action: string, body: Record<string, unknown>): Loaded<T> {
  const [state, setState] = useState<{ data: T | null; err: string; busy: boolean }>({ data: null, err: '', busy: true });
  const seq = useRef(0);
  const key = JSON.stringify(body);
  const [nonce, setNonce] = useState(0);
  useEffect(() => {
    const mine = ++seq.current;
    setState((s) => ({ ...s, busy: true }));
    void call<T>(action, JSON.parse(key) as Record<string, unknown>, 90_000).then((r) => {
      if (mine !== seq.current) return;
      setState(r.ok && r.data ? { data: r.data, err: '', busy: false } : { data: null, err: explain(r), busy: false });
    });
  }, [call, action, key, nonce]);
  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { ...state, reload };
}

export const PERIODS: [number, string][] = [[1, 'Šiandien'], [7, '7 d.'], [30, '30 d.'], [90, 'Viskas (90 d.)']];

const SELECT = `${INPUT} !min-h-[36px] !py-1 text-xs`;

/** Period buttons and the filters. `only` names the filters the page can answer (the others are not shown). */
export const FilterBar: React.FC<{
  days: number; setDays: (n: number) => void; filters: Filters; setFilters: (f: Filters) => void; available: Available | undefined;
  only?: (keyof Filters)[]; note?: string; busy?: boolean; onReload?: () => void; extra?: React.ReactNode;
}> = ({ days, setDays, filters, setFilters, available, only = ['market', 'lang', 'dev', 'br'], note, busy, onReload, extra }) => {
  const sel = (k: keyof Filters, title: string, names: Record<string, string>) => only.includes(k) && (
    <label key={k} className="flex flex-col gap-0.5 text-[11px] text-white/60 min-w-[7.5rem] flex-1">
      <span>{title}</span>
      <select className={SELECT} value={filters[k] ?? ''} onChange={(e) => setFilters({ ...filters, [k]: e.target.value || undefined })} aria-label={title}>
        <option value="">Visi</option>
        {(available?.[k] ?? []).map((v) => <option key={v} value={v}>{label(names, v)}</option>)}
        {filters[k] && !(available?.[k] ?? []).includes(filters[k] as string) && <option value={filters[k]}>{label(names, filters[k] as string)}</option>}
      </select>
    </label>
  );
  return (
    <div className={`${CARD} flex flex-col gap-3`}>
      <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Laikotarpis">
        {PERIODS.map(([d, l]) => (
          <button key={d} type="button" onClick={() => setDays(d)} aria-pressed={days === d}
            className={`px-3 py-1.5 rounded-lg text-sm border ${days === d ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{l}</button>
        ))}
        {onReload && <button type="button" className={BTN} onClick={onReload} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>}
        {extra}
      </div>
      <div className="flex flex-wrap gap-2">
        {sel('market', 'Rinka', MARKET_LT)}
        {sel('lang', 'Kalba', LANG_LT)}
        {sel('dev', 'Įrenginys', DEV_LT)}
        {sel('br', 'Naršyklė', BR_LT)}
      </div>
      {note && <p className={`text-[11px] ${MUTED}`}>{note}</p>}
    </div>
  );
};

/** The funnel as bars: each step with its count, its share of the first step, and what was lost since the step before. */
export const FunnelBars: React.FC<{ steps: Record<string, number>; order: readonly string[]; title: string }> = ({ steps, order, title }) => {
  const rows = bars(steps, order);
  return (
    <div className="flex flex-col gap-2" role="list" aria-label={title}>
      {rows.map((r) => (
        <div key={r.step} role="listitem" className="text-sm">
          <div className="flex flex-wrap items-baseline justify-between gap-x-3">
            <span className="min-w-0 break-words">{label(STEP_LT, r.step)}</span>
            <span className="text-white/80 shrink-0"><b>{r.n}</b>{r.ofTop !== null && r.step !== order[0] ? ` (${Math.round(r.ofTop * 100)} % nuo pirmo)` : ''}</span>
          </div>
          <div className="h-2 mt-0.5 rounded-full bg-white/5 overflow-hidden"><div className="h-full rounded-full bg-[#f5c542]/80" style={{ width: `${Math.max(r.n > 0 ? 2 : 0, Math.round((r.ofTop ?? 0) * 100))}%` }} /></div>
          {r.lost !== null && r.step !== order[0] && <p className="text-[11px] text-white/50 mt-0.5">{r.lost > 0 ? `Atkrito ${Math.round(r.lost * 100)} % nuo ankstesnio žingsnio` : 'Niekas neatkrito nuo ankstesnio žingsnio'}</p>}
        </div>
      ))}
    </div>
  );
};

const LIGHT_TONE: Record<Tone, string> = {
  good: 'bg-emerald-400/15 text-emerald-200 border-emerald-300/30', warn: 'bg-amber-400/15 text-amber-100 border-amber-300/35',
  bad: 'bg-red-500/15 text-red-200 border-red-400/35', muted: 'bg-white/5 text-white/70 border-white/15', info: 'bg-sky-400/15 text-sky-100 border-sky-300/30',
};
const LIGHT_WORD: Record<Tone, string> = { good: 'sveika', warn: 'ribinė', bad: 'bloga', muted: 'nėra duomenų', info: '' };

/** A traffic light: a dot, the word and the number (never a colour alone). */
export const Light: React.FC<{ tone: Tone; label: string; text: string }> = ({ tone, label: l, text }) => (
  <div className={`rounded-xl border px-3 py-2 text-xs flex flex-col gap-0.5 ${LIGHT_TONE[tone]}`}>
    <span className="opacity-80">{l}</span>
    <span className="text-sm font-bold break-words">{text}</span>
    <span className="opacity-80">{LIGHT_WORD[tone]}</span>
  </div>
);

/** One metric of the fx tables: its values, each with its count and share, and (with a split) a column per group. */
export const FxCard: React.FC<{ title: string; hint?: string; fx: Fx | undefined; metric: string; by: string | null; groups: string[]; limit?: number }> = ({ title, hint, fx, metric, by, groups, limit = 12 }) => {
  const lines = fxLines(fx, metric);
  const total = lines.reduce((s, l) => s + l.total, 0);
  const gtot: Record<string, number> = {};
  for (const g of groups) gtot[g] = lines.reduce((s, l) => s + (l.by[g] ?? 0), 0);
  const head = ['Reikšmė', 'Viso', ...groups.map((g) => groupLt(by, g))];
  const rows = lines.slice(0, limit).map((l) => [
    <span key="v">{valueLt(metric, l.value, gateCodeLt)}</span>, <span key="t">{shareText(l.total, total)}</span>,
    ...groups.map((g) => <span key={g}>{(l.by[g] ?? 0) > 0 ? shareText(l.by[g] ?? 0, gtot[g]) : '0'}</span>),
  ]);
  return (
    <section className={`${CARD} flex flex-col gap-2`} aria-label={title}>
      <h3 className="text-sm font-bold">{title}</h3>
      {hint && <p className={`text-[11px] ${MUTED}`}>{hint}</p>}
      <Tbl head={head} rows={rows} label={title} empty="Dar nėra duomenų." />
      {lines.length > limit && <p className={`text-[11px] ${MUTED}`}>Rodoma {limit} iš {lines.length} reikšmių.</p>}
    </section>
  );
};

/** A sentence about a report that is partly counted. */
export const Partial: React.FC<{ partial: boolean; recording: boolean }> = ({ partial, recording }) => (
  <>
    {!recording && <p className="rounded-xl border border-amber-300/35 bg-amber-400/15 text-amber-100 px-3 py-2 text-sm">Statistika nerenkama: šiame serveryje nenustatytas CRON_SECRET (bent 16 simbolių), todėl skaitiklis išjungtas.</p>}
    {partial && <p className="rounded-xl border border-amber-300/35 bg-amber-400/15 text-amber-100 px-3 py-2 text-sm">Dalis dienų dar skaičiuojama (pirmą kartą skaitomi visi įvykiai). Atnaujink po minutės.</p>}
  </>
);

/** Save a text as a file the browser downloads (CSV). */
export function download(name: string, text: string): void {
  try {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([String.fromCharCode(0xfeff) + text], { type: 'text/csv;charset=utf-8' }));
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  } catch { /* no download here */ }
}

export const useFilters = (): [Filters, (f: Filters) => void] => useState<Filters>({});
