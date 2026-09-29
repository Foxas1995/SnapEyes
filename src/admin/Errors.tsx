// Klaidos: the latest error events of the last 7 days (which endpoint, what class of error, the reply's reason code;
// never a message text), counted by kind, and the admin audit log (what was done in this panel).
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import type { Errors, LogEntry } from './api';
import type { Call } from './AdminApp';
import { countBy } from './agg';
import { actionLt, ENDPOINT_LT, explain, fmtSec, fmtTime, KIND_LT, kindLabel, logResultLt, REASON_LT } from './format';
import { BTN, CARD, Chip, H2, MUTED, Notice, Spinner } from './ui';

export const ErrorsPage: React.FC<{ call: Call }> = ({ call }) => {
  const [data, setData] = useState<Errors | null>(null);
  const [audit, setAudit] = useState<LogEntry[]>([]);
  const [err, setErr] = useState<string[]>([]);
  const [busy, setBusy] = useState(true);

  const fetchAll = useCallback(() => Promise.all([call<Errors>('errors'), call<{ entries: LogEntry[] }>('audit')]), [call]);

  const apply = useCallback(([e, a]: Awaited<ReturnType<typeof fetchAll>>) => {
    const out: string[] = [];
    if (e.ok && e.data) setData(e.data); else out.push(`Klaidos: ${explain(e)}`);
    if (a.ok && a.data) setAudit(a.data.entries); else out.push(`Veiksmų žurnalas: ${explain(a)}`);
    setErr(out); setBusy(false);
  }, []);

  useEffect(() => {
    let live = true;
    void fetchAll().then((x) => { if (live) apply(x); });
    return () => { live = false; };
  }, [fetchAll, apply]);

  const load = async () => { setBusy(true); apply(await fetchAll()); };

  const rows = data?.errors || [];
  const byKind = countBy(rows, (r) => r.kind || 'unknown');

  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} onClick={() => void load()} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>}>Klaidos</H2>
      {err.map((e, i) => <Notice key={i}>{e}</Notice>)}
      <section className={`${CARD} flex flex-col gap-3`}>
        <p className={`text-xs ${MUTED}`}>
          Paskutinės 7 dienos, naujausios viršuje. Saugoma tik vieta, klaidos rūšis ir priežasties kodas, jokio teksto ar
          asmens duomenų. Užklausos iš svetimų svetainių ir be JSON neskaičiuojamos.
          {data?.partial ? ' Dalis dienų dar skaičiuojama.' : ''}
        </p>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(byKind).map(([k, v]) => <Chip key={k} tone={k === 'busy' || k === '403' ? 'warn' : 'bad'}>{KIND_LT[k] || k}: {v}</Chip>)}
        </div>
        {data && rows.length === 0 && <p className="text-sm text-emerald-200">Klaidų nėra.</p>}
        <ul className="flex flex-col">
          {rows.map((r, i) => (
            <li key={i} className="border-t border-white/5 py-2 text-xs flex flex-col sm:flex-row sm:items-baseline gap-x-3 gap-y-0.5">
              <span className="text-white/60 whitespace-nowrap">{fmtTime(r.t, true)}</span>
              <span className="font-semibold">{ENDPOINT_LT[r.endpoint || ''] || r.endpoint}</span>
              <span>{kindLabel(r.kind, r.status)}</span>
              <span className="text-white/70 break-words min-w-0">{r.reason ? `${r.reason}${REASON_LT[r.reason] ? `: ${REASON_LT[r.reason]}` : ''}` : ''}</span>
              {typeof r.ms === 'number' && <span className="text-white/45 whitespace-nowrap">{fmtSec(r.ms)}</span>}
            </li>
          ))}
        </ul>
      </section>
      <section className={`${CARD} flex flex-col gap-2`}>
        <h3 className="text-sm font-bold">Administratoriaus veiksmai (paskutiniai)</h3>
        {audit.length === 0 && <p className={`text-xs ${MUTED}`}>Dar nieko.</p>}
        {audit.map((l, i) => (
          <p key={i} className="text-xs break-words border-t border-white/5 pt-1.5">
            {fmtTime(l.t, true)} · <b>{actionLt(l.action)}</b>
            {l.order ? <> · <a className="underline underline-offset-4 decoration-white/30 break-all" href={`#order/${l.order}`}>{l.order}</a></> : ''}
            {l.eye ? ` (akis ${l.eye})` : ''} · {l.ok ? 'pavyko' : 'nepavyko'}{l.result ? ` · ${logResultLt(l.result)}` : ''}{l.detail ? ` · ${l.detail}` : ''}
          </p>
        ))}
      </section>
    </div>
  );
};
