// Užsakymai: the order folders of the chosen period with their state (from the stored files only), eyes, style,
// price and the customer's email masked. A filter by state; a tap opens the order.
import { useCallback, useEffect, useMemo, useState } from 'react';
import type React from 'react';
import type { Orders, Reply } from './api';
import type { Call } from './AdminApp';
import { countBy } from './agg';
import { explain, fmtEur, fmtTime, STATE_LT, STATE_TONE, STYLE_LT } from './format';
import { BTN, CARD, Chip, H2, INPUT, MUTED, Notice, Spinner } from './ui';

const PERIODS: [number, string][] = [[7, '7 d.'], [30, '30 d.'], [90, '90 d.'], [400, 'Visi']];

export const OrdersPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<Orders | null>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(true);
  const [state, setState] = useState('');
  const [find, setFind] = useState('');

  const apply = useCallback((r: Reply<Orders>) => {
    setBusy(false);
    if (r.ok && r.data) { setData(r.data); setErr(''); } else setErr(explain(r));
  }, []);

  useEffect(() => {
    let live = true;
    void call<Orders>('orders', { days }).then((r) => { if (live) apply(r); });
    return () => { live = false; };
  }, [call, days, apply]);

  const load = async (d: number) => { setBusy(true); apply(await call<Orders>('orders', { days: d })); };

  const rows = useMemo(() => data?.orders || [], [data]);
  const byState = useMemo(() => countBy(rows, (r) => r.state), [rows]);
  const q = find.trim().toLowerCase();
  const shown = rows.filter((r) => (!state || r.state === state) && (!q || r.order.includes(q)));

  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} onClick={() => void load(days)} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>}>
        Užsakymai
      </H2>
      <div className={`${CARD} flex flex-col gap-3`}>
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Laikotarpis">
          {PERIODS.map(([d, l]) => (
            <button key={d} type="button" onClick={() => { setBusy(true); setDays(d); }} aria-pressed={days === d}
              className={`px-3 py-1.5 rounded-lg text-sm border ${days === d ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{l}</button>
          ))}
        </div>
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Būsena">
          <button type="button" onClick={() => setState('')} aria-pressed={!state}
            className={`px-2.5 py-1 rounded-lg text-xs border ${!state ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>Visi ({rows.length})</button>
          {Object.keys(byState).sort().map((s) => (
            <button key={s} type="button" onClick={() => setState(s)} aria-pressed={state === s}
              className={`px-2.5 py-1 rounded-lg text-xs border ${state === s ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>
              {STATE_LT[s] || s} ({byState[s]})
            </button>
          ))}
        </div>
        <input className={INPUT} placeholder="Ieškoti pagal užsakymo numerį" value={find} onChange={(e) => setFind(e.target.value)}
          aria-label="Ieškoti pagal užsakymo numerį" spellCheck={false} />
        <p className={`text-xs ${MUTED}`}>
          Neapmokėti užsakymai ištrinami po 26 val., todėl sąraše daugiausia apmokėti ir šiandienos.
          {data?.more ? ' Rodoma ne viskas: pasirink trumpesnį laikotarpį.' : ''}
        </p>
      </div>
      {err && <Notice>{err}</Notice>}
      {!busy && data && shown.length === 0 && <p className={`text-sm ${MUTED}`}>Užsakymų nėra.</p>}
      <ul className="grid gap-2 md:grid-cols-2">
        {shown.map((r) => (
          <li key={r.order}>
            <a href={`#order/${r.order}`} className={`${CARD} !p-3 flex flex-col gap-1.5 hover:border-white/25`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <code className="text-sm font-semibold break-all">{r.order}</code>
                <Chip tone={STATE_TONE[r.state] || 'muted'}>{STATE_LT[r.state] || r.state}</Chip>
              </div>
              <p className="text-xs text-white/70 break-words">
                {fmtTime(r.created_at)}
                {r.eyes ? ` · ${r.eyes} ${r.eyes === 1 ? 'akis' : 'akys'}` : ''}
                {r.style ? ` · ${STYLE_LT[r.style] || r.style}` : ''}
                {typeof r.amount === 'number' ? ` · ${fmtEur(r.amount)}` : ''}
                {r.paid && r.live === false ? ' · testas' : ''}
              </p>
              <p className="text-xs text-white/55 break-words">
                {r.email || (r.paid ? 'be el. pašto' : 'neapmokėtas')}
                {r.extra_payments ? ` · papildomi mokėjimai: ${r.extra_payments}` : ''}
                {r.withdrawal ? ' · atsisakymo pareiškimas' : ''}
                {r.held ? ' · laukia tavo peržiūros' : ''}
              </p>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
};
