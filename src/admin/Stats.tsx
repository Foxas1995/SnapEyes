// Statistika: per-day bars of the usage events (analyses, blocked, previews, compositions, 4K, errors, the estimated
// Gemini spend), the average time of each step, and the distributions (verdicts, block reasons, devices, sources,
// languages, styles). The same numbers as a table below the charts.
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import type { Counts, Reply, Stats, Table } from './api';
import type { Call } from './AdminApp';
import { avgMs, lastDays, sumTable } from './agg';
import { BarChart } from './charts';
import { BLOCK_LT, DEFAULT_PRICES, DEVICE_LT, explain, fmtSec, fmtUsd, KARTAI, ltCount, SOURCE_LT, STEP_LT, STYLE_LT, VERDICT_LT } from './format';
import { BTN, CARD, H2, MUTED, Notice, Spinner } from './ui';

const PERIODS = [7, 30, 90];

const Dist: React.FC<{ title: string; t: Table; names?: Record<string, string> }> = ({ title, t, names = {} }) => {
  const total = sumTable(t);
  const rows = Object.entries(t).sort((a, b) => b[1] - a[1]);
  return (
    <div className={CARD}>
      <p className="text-sm font-bold mb-2">{title}</p>
      {rows.length === 0 && <p className={`text-xs ${MUTED}`}>Nėra duomenų.</p>}
      <ul className="flex flex-col gap-1.5">
        {rows.map(([k, v]) => (
          <li key={k} className="text-xs">
            <div className="flex justify-between gap-2"><span className="break-words min-w-0">{names[k] || k}</span><span className="text-white/70 shrink-0">{v} ({total ? Math.round((v / total) * 100) : 0} %)</span></div>
            <div className="h-1.5 mt-0.5 rounded-full bg-white/5 overflow-hidden"><div className="h-full rounded-full bg-[#f5c542]/80" style={{ width: `${total ? (v / total) * 100 : 0}%` }} /></div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export const StatsPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<Stats | null>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(true);

  const apply = useCallback((r: Reply<Stats>) => {
    setBusy(false);
    if (r.ok && r.data) { setData(r.data); setErr(''); } else setErr(explain(r));
  }, []);

  useEffect(() => {
    let live = true;
    void call<Stats>('stats', { days }).then((r) => { if (live) apply(r); });
    return () => { live = false; };
  }, [call, days, apply]);

  const load = async (n: number) => { setBusy(true); apply(await call<Stats>('stats', { days: n })); };

  const list = data?.days || [];
  const p = data?.prices_usd || DEFAULT_PRICES;
  const label = (d: string) => d.slice(5);
  const series = (f: (c: Counts) => number) => list.map((d) => ({ label: label(d.day), value: f(d.counts) }));
  const all = lastDays(list, list.length);
  const cost = (c: Counts) => c.gemini.vision * p.vision + c.gemini.image_1k * p.image_1k + c.gemini.image_4k * p.image_4k;

  return (
    <div className="flex flex-col gap-4">
      <H2 right={
        <div className="flex flex-wrap gap-1.5">
          {PERIODS.map((n) => (
            <button key={n} type="button" onClick={() => { setBusy(true); setDays(n); }} aria-pressed={days === n}
              className={`px-3 py-1.5 rounded-lg text-sm border ${days === n ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{n} d.</button>
          ))}
          <button type="button" className={BTN} onClick={() => void load(days)} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>
        </div>
      }>Statistika</H2>
      {err && <Notice>{err}</Notice>}
      {data?.recording === false && <Notice tone="warn">Statistika nerenkama: šiame serveryje nenustatytas CRON_SECRET (bent 16 simbolių). Privatumo politika žada įvykius ištrinti po 12 mėnesių, o nesėkmingų prisijungimų žymas po 2 dienų, bet juos ištrina tik kasdienis valymas, kuriam reikia CRON_SECRET. Kol jo nėra, niekas nerašoma.</Notice>}
      {data?.partial && <Notice tone="warn">Dalis dienų dar skaičiuojama (pirmą kartą skaitomi visi įvykiai). Atnaujink po minutės.</Notice>}
      {list.length > 0 && (
        <>
          <div className="grid gap-3 md:grid-cols-2">
            <BarChart title="Analizės per dieną" bars={series((c) => c.kinds.analyze || 0)} />
            <BarChart title="Užblokuotos nuotraukos" bars={series((c) => c.blocked)} />
            <BarChart title="Peržiūros (restauruotos akys)" bars={series((c) => c.kinds.enhance || 0)} />
            <BarChart title="Kompozicijos" bars={series((c) => c.kinds.compose || 0)} />
            <BarChart title="4K akys" bars={series((c) => c.master_eye)} />
            <BarChart title="Klaidos" bars={series((c) => sumTable(c.errors))} />
            <BarChart title="Gemini išlaidos (įvertis)" bars={series(cost)} format={(v) => fmtUsd(v)} note="USD" />
            <BarChart title="Gemini užimtas" bars={series((c) => c.busy)} />
          </div>
          <section className={CARD}>
            <p className="text-sm font-bold mb-2">Vidutinė trukmė per žingsnį ({days} d.)</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.keys(STEP_LT).map((k) => (
                <div key={k} className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <p className="text-xs text-white/60">{STEP_LT[k]}</p>
                  <p className="text-lg font-bold">{fmtSec(avgMs(all, k))}</p>
                  <p className="text-[11px] text-white/45">{ltCount(all.ms[k]?.[1] || 0, KARTAI)}</p>
                </div>
              ))}
            </div>
          </section>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <Dist title="Vertinimai" t={all.verdict} names={VERDICT_LT} />
            <Dist title="Blokavimo priežastys" t={all.block_reason} names={BLOCK_LT} />
            <Dist title="Įrenginiai" t={all.device} names={DEVICE_LT} />
            <Dist title="Šaltinis" t={all.source} names={SOURCE_LT} />
            <Dist title="Kalba" t={all.lang} names={{ en: 'Anglų', de: 'Vokiečių' }} />
            <Dist title="Stiliai (kompozicijos)" t={all.compose_style} names={STYLE_LT} />
          </div>
          <section className={CARD}>
            <details>
              <summary className="cursor-pointer text-sm font-bold">Lentelė pagal dienas</summary>
              <div className="overflow-x-auto mt-2">
                <table className="text-xs min-w-[560px] w-full">
                  <thead>
                    <tr className="text-left text-white/60">
                      {['Diena', 'Analizės', 'Užblok.', 'Peržiūros', 'Kompoz.', '4K akys', '4K kūr.', 'Klaidos', 'Gemini $'].map((h) => <th key={h} className="py-1 pr-2 font-semibold">{h}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {[...list].reverse().map((d) => (
                      <tr key={d.day} className="border-t border-white/5">
                        <td className="py-1 pr-2 whitespace-nowrap">{d.day}{d.complete ? '' : ' *'}</td>
                        <td className="py-1 pr-2">{d.counts.kinds.analyze || 0}</td>
                        <td className="py-1 pr-2">{d.counts.blocked}</td>
                        <td className="py-1 pr-2">{d.counts.kinds.enhance || 0}</td>
                        <td className="py-1 pr-2">{d.counts.kinds.compose || 0}</td>
                        <td className="py-1 pr-2">{d.counts.master_eye}</td>
                        <td className="py-1 pr-2">{d.counts.master_compose}</td>
                        <td className="py-1 pr-2">{sumTable(d.counts.errors)}</td>
                        <td className="py-1 pr-2">{fmtUsd(cost(d.counts))}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className={`text-[11px] mt-2 ${MUTED}`}>* diena dar skaičiuojama. Dienos pagal UTC.</p>
            </details>
          </section>
        </>
      )}
    </div>
  );
};
