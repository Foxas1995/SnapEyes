// Saltiniai: where the visits and the orders come from. One row per source, campaign, ad set or advertisement (the campaign code of the link, api/_lib/counter.py), with the steps each reached and
// the share of the step before it, the orders and the revenue (the order records), filters for the period, market, language, device and browser, and a CSV file of the table.
import { useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { BTN, CARD, H2, MUTED, Notice, Spinner, Tbl } from './ui';
import { FilterBar, Partial, download, useFilters, useReport } from './TrafficUi';
import { GROUP_LT, SOURCE_PREV, SOURCE_STEPS, STEP_LT, keyText, moneyText, num, rate, sourcesCsv, type Group, type SourcesReply, type Steps } from './traffic';
import { fmtPct } from './stylesView';

const GROUPS: Group[] = ['src', 'cmp', 'trm', 'cnt'];

/** A count with the share of the step before it: "45 (63 %)"; the first step has no share. */
const Cell: React.FC<{ n: number; prev?: number }> = ({ n, prev }) => (
  <span>{n}{prev !== undefined && prev > 0 ? <span className="text-white/50"> ({fmtPct(rate(n, prev))})</span> : ''}</span>
);

export const SourcesPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [group, setGroup] = useState<Group>('cmp');
  const [filters, setFilters] = useFilters();
  const { data, err, busy, reload } = useReport<SourcesReply>(call, 'sources', { days, group, ...filters });
  const rows = data?.rows ?? [];
  const prevOf = (s: Steps, st: string) => { const p = SOURCE_PREV[st]; return p ? num(s[p]) : undefined; };
  const head = ['Kas', ...SOURCE_STEPS.map((s) => STEP_LT[s]), 'Užsakymai', 'Pajamos'];
  const line = (key: string, s: Steps, orders: number | undefined, revenue: Record<string, number> | undefined, bold = false) => [
    <span key="k" className={`break-words ${bold ? 'font-bold' : ''}`}>{key}</span>,
    ...SOURCE_STEPS.map((st) => <Cell key={st} n={num(s[st])} prev={prevOf(s, st)} />),
    <span key="o">{data?.orders_comparable === false ? '-' : num(orders)}</span>,
    <span key="r">{data?.orders_comparable === false ? '-' : moneyText(revenue)}</span>,
  ];
  const body = rows.map((r) => line(keyText(r.key, group), r.steps, r.orders, r.revenue));
  const all = data ? [line('Iš viso', data.totals, data.orders, data.revenue, true), ...body] : body;
  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} onClick={() => { if (data) download(`saltiniai-${days}d.csv`, sourcesCsv(data)); }} disabled={!rows.length}>Eksportuoti CSV</button>}>Šaltiniai</H2>
      <FilterBar days={days} setDays={setDays} filters={filters} setFilters={setFilters} available={data?.available} busy={busy} onReload={reload}
        note="Nusileidimai, /try, nuotrauka, peržiūra, pirkti ir užsakymo puslapis yra puslapių skaičiai (kartą atidarius); stilius, mokėjimo puslapis ir apmokėta yra serverio užklausos. Skliausteliuose: dalis ankstesnio žingsnio (pirkti: dalis tų, kuriems parodyta peržiūra; stiliaus peržiūrų skaičius yra užklausų, vienas lankytojas jų daro kelias). Dienos pagal UTC." />
      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Grupuoti pagal">
        <span className={`text-xs self-center ${MUTED}`}>Grupuoti pagal:</span>
        {GROUPS.map((g) => (
          <button key={g} type="button" onClick={() => setGroup(g)} aria-pressed={group === g}
            className={`px-2.5 py-1 rounded-lg text-xs border ${group === g ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{GROUP_LT[g]}</button>
        ))}
      </div>
      {err && <Notice>{err}</Notice>}
      {data && <Partial partial={data.partial} recording={data.recording} />}
      {busy && !data && <Spinner />}
      <section className={`${CARD} flex flex-col gap-2`}>
        {data && rows.length === 0 && <p className={`text-sm ${MUTED}`}>Šiuo laikotarpiu dar nieko nėra. Skaitiklis laukia pirmų apsilankymų; nuorodose būtinos utm_ žymos (reklamų planas, 7 skyrius).</p>}
        {all.length > 0 && <Tbl head={head} rows={all} label="Šaltiniai" />}
        {data?.orders_comparable === false && <p className={`text-xs ${MUTED}`}>Užsakymai nerodomi, kai pasirinktas įrenginys ar naršyklė: užsakymo įraše jų nesaugome.</p>}
        {data?.orders_more && <p className={`text-xs ${MUTED}`}>Užsakymų daugiau nei perskaityta: pasirink trumpesnį laikotarpį.</p>}
        {data && data.other > 0 && <p className={`text-xs ${MUTED}`}>Dar {data.other} įvykių sumesta į bendrą eilutę (per daug skirtingų kodų per dieną).</p>}
        <p className={`text-[11px] ${MUTED}`}>Pajamos: tikri apmokėti užsakymai iš užsakymų įrašų, be atsisakytų užsakymų ir bandomųjų mokėjimų; kiti grąžinimai neatimti. Tas pats žmogus, atidaręs puslapį du kartus, skaičiuojamas du kartus: tai ne unikalūs lankytojai.</p>
      </section>
    </div>
  );
};
