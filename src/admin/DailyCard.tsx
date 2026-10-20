// The daily block of the Suvestinė page: yesterday and the last seven days of the visitor counter (landing page opened, /try, photo, preview shown, the buy card), the orders and the revenue (the
// order records already loaded by the page), the estimated Gemini spend (the same arithmetic as the numbers below: calls times the list prices) and the errors, and the five sources that brought the
// most visits this week. Days are UTC days; yesterday is the day before today.
import type React from 'react';
import type { Call } from './AdminApp';
import type { OrderRow, Prices } from './api';
import { fmtUsd, spend } from './format';
import { CARD, MUTED, Notice, Spinner, Tbl } from './ui';
import { useReport } from './TrafficUi';
import { keyText, moneyText, num, type SrcRow, type Steps } from './traffic';

export interface DailyDay { day: string; complete: boolean; steps: Steps; errors: number; gemini: { vision: number; image_1k: number; image_4k: number } }
export interface DailyReply { ok: boolean; days: DailyDay[]; top: SrcRow[]; prices_usd: Prices; recording: boolean; partial: boolean }

const sum = (days: DailyDay[], f: (d: DailyDay) => number): number => days.reduce((s, d) => s + f(d), 0);

/** The paid, live orders of the given UTC days, their number and their revenue per currency. */
export function ordersOf(rows: OrderRow[], days: string[]): { n: number; revenue: Record<string, number> } {
  const want = new Set(days);
  const revenue: Record<string, number> = {};
  let n = 0;
  for (const r of rows) {
    if (!r.paid || r.live !== true || typeof r.amount !== 'number' || !r.paid_at || r.state === 'withdrawn') continue;
    if (!want.has(new Date(r.paid_at * 1000).toISOString().slice(0, 10))) continue;
    n += 1;
    const cur = (r.currency || 'eur').toLowerCase();
    revenue[cur] = (revenue[cur] ?? 0) + r.amount;
  }
  return { n, revenue };
}

export const DailyCard: React.FC<{ call: Call; rows: OrderRow[]; prices: Prices }> = ({ call, rows, prices }) => {
  const { data, err, busy } = useReport<DailyReply>(call, 'daily', {});
  const days = data?.days ?? [];
  const yesterday = days.length >= 2 ? [days[days.length - 2]] : [];
  const week = days.slice(-7);
  const col = (ds: DailyDay[]) => {
    const o = ordersOf(rows, ds.map((d) => d.day));
    const buyBox = sum(ds, (d) => num(d.steps.buy));
    return [
      String(sum(ds, (d) => num(d.steps.landing))), String(sum(ds, (d) => num(d.steps.try))), String(sum(ds, (d) => num(d.steps.photo))), String(sum(ds, (d) => num(d.steps.result))),
      `${buyBox} paspaudė pirkti, ${sum(ds, (d) => num(d.steps.soon))} rado kortelę uždarytą`, String(o.n), moneyText(o.revenue),
      fmtUsd(sum(ds, (d) => spend({ gemini: d.gemini }, prices))), String(sum(ds, (d) => d.errors)),
    ];
  };
  const labels = ['Nusileidimai', 'Atidarė /try', 'Pasirinko nuotrauką', 'Peržiūra parodyta', 'Pirkimo kortelė', 'Apmokėti užsakymai', 'Pajamos', 'Gemini išlaidos (įvertis)', 'Klaidos'];
  const y = col(yesterday), w = col(week);
  return (
    <section className={`${CARD} flex flex-col gap-3`} aria-label="Vakar ir 7 dienos">
      <h3 className="text-sm font-bold">Vakar ir paskutinės 7 dienos</h3>
      {err && <Notice tone="warn">{err}</Notice>}
      {busy && !data && <Spinner />}
      {data && !data.recording && <p className={`text-xs ${MUTED}`}>Skaitiklis šiame serveryje nerenka duomenų (nėra CRON_SECRET).</p>}
      {data && (
        <Tbl head={['', 'Vakar', 'Paskutinės 7 d. (su šiandiena)']} rows={labels.map((l, i) => [<span key="l">{l}</span>, <span key="y">{yesterday.length ? y[i] : '-'}</span>, <span key="w">{w[i]}</span>])} label="Vakar ir 7 dienos" />
      )}
      {data && data.top.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-white/70 mb-1">Daugiausia lankytojų atvedę šaltiniai (7 d.)</p>
          <ul className="flex flex-col gap-0.5 text-xs">
            {data.top.map((r) => <li key={keyText(r.key, 'src')} className="break-words">{keyText(r.key, 'src')}: {num(r.steps.landing)} nusileidimų, {num(r.steps.result)} peržiūrų</li>)}
          </ul>
        </div>
      )}
      {data && data.top.length === 0 && <p className={`text-xs ${MUTED}`}>Savaitės šaltinių dar nėra: skaitiklis laukia pirmų apsilankymų.</p>}
      <p className={`text-[11px] ${MUTED}`}>Užsakymai ir pajamos iš užsakymų įrašų: tikri mokėjimai be atsisakytų užsakymų (todėl gali būti mažiau nei lentelėje žemiau); kiti grąžinimai neatimti. Dienos pagal UTC.</p>
    </section>
  );
};
