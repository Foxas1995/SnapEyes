// Piltuvas: the whole funnel of a visit with what was lost at each step, and the same steps split by device class and by browser family (the Facebook and Instagram apps' own browsers are marked:
// the ads plan's gate G4), the time from a photo to its preview, and the server's steps (requests) and the countries.
import { useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { CARD, Chip, H2, MUTED, Notice, Spinner, Tbl } from './ui';
import { FilterBar, FunnelBars, Partial, useFilters, useReport } from './TrafficUi';
import { BR_LT, DEV_LT, FUNNEL_STEPS, SERVER_STEPS, STEP_LT, inApp, label, num, pctText, rate, type FunnelReply, type Steps } from './traffic';
import { fmtPct, shareText } from './stylesView';

/** The funnel steps of one group as a row: the count of each and, in the last cell, how many of the landings got to an order page. */
const splitRows = (by: Record<string, Steps>, names: Record<string, string>, mark: (k: string) => boolean) =>
  Object.entries(by).sort((a, b) => num(b[1].landing) - num(a[1].landing) || a[0].localeCompare(b[0])).map(([k, s]) => [
    <span key="k" className="break-words">{label(names, k)}{mark(k) && <> <Chip tone="info">programos naršyklė</Chip></>}</span>,
    ...FUNNEL_STEPS.map((st, i) => (
      <span key={st}>{num(s[st])}{i > 0 && num(s[FUNNEL_STEPS[i - 1]]) > 0 ? <span className="text-white/50"> ({fmtPct(rate(num(s[st]), num(s[FUNNEL_STEPS[i - 1]])))})</span> : ''}</span>
    )),
    <span key="e">{num(s.landing) > 0 ? shareText(num(s.order), num(s.landing)) : 'nėra duomenų'}</span>,
  ]);

export const FunnelPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [filters, setFilters] = useFilters();
  const { data, err, busy, reload } = useReport<FunnelReply>(call, 'funnel', { days, ...filters });
  const head = (first: string) => [first, ...FUNNEL_STEPS.map((s) => STEP_LT[s]), 'Nuo nusileidimo iki užsakymo'];
  const steps = data?.steps ?? {};
  const cc = Object.entries(data?.cc.landing ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 8);
  return (
    <div className="flex flex-col gap-4">
      <H2>Piltuvas</H2>
      <FilterBar days={days} setDays={setDays} filters={filters} setFilters={setFilters} available={data?.available} busy={busy} onReload={reload}
        note="Žingsniai eina tokia tvarka, kokia lankytojas juos pasiekia. Skaičiai yra puslapių atidarymai ir paspaudimai (ne unikalūs žmonės). „Atidarė užsakymo puslapį“ yra grįžimas po apmokėjimo: skirtumas tarp „Paspaudė pirkti“ ir jo rodo, kiek žmonių nebaigė mokėti." />
      {err && <Notice>{err}</Notice>}
      {data && <Partial partial={data.partial} recording={data.recording} />}
      {busy && !data && <Spinner />}
      {data && (
        <>
          <section className={`${CARD} flex flex-col gap-3`}>
            <h3 className="text-sm font-bold">Visas piltuvas</h3>
            {num(steps.landing) === 0 && num(steps.try) === 0 ? <p className={`text-sm ${MUTED}`}>Šiuo laikotarpiu dar nėra apsilankymų.</p> : <FunnelBars steps={steps} order={FUNNEL_STEPS} title="Piltuvas" />}
            {num(steps.soon) > 0 && <p className="text-sm">Pirkimo kortelę uždarytą (užsakymai dar neatidaryti) matė: <b>{num(steps.soon)}</b>. Tai žmonės, kurie būtų galėję pirkti.</p>}
          </section>
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Pagal įrenginį</h3>
            <Tbl head={head('Įrenginys')} rows={splitRows(data.by_dev, DEV_LT, () => false)} label="Piltuvas pagal įrenginį" empty="Dar nėra duomenų." />
          </section>
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Pagal naršyklę</h3>
            <p className={`text-[11px] ${MUTED}`}>Facebook ir Instagram programų naršyklės pažymėtos: reklamų plano G4 vartai klausia, ar iš jų peržiūra pasiekiama taip pat gerai kaip iš Chrome ar Safari.</p>
            <Tbl head={head('Naršyklė')} rows={splitRows(data.by_br, BR_LT, inApp)} label="Piltuvas pagal naršyklę" empty="Dar nėra duomenų." />
          </section>
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Laikas nuo nuotraukos iki peržiūros</h3>
            <p className={`text-[11px] ${MUTED}`}>Matuoja pats puslapis (tinklas ir serveris kartu). Rodoma viršutinė laiko kraičio riba: pusė peržiūrų (p50) ir 95 % peržiūrų (p95) buvo greitesnės.</p>
            <Tbl head={['Grupė', 'p50', 'p95', 'Peržiūrų']}
              rows={[['Visos', data.ttp.all], ...Object.entries(data.ttp.by_dev).map(([k, v]) => [label(DEV_LT, k), v] as const), ...Object.entries(data.ttp.by_br).map(([k, v]) => [label(BR_LT, k), v] as const)].map(([k, v]) => [
                <span key="k">{k as string}</span>, <span key="a">{pctText((v as FunnelReply['ttp']['all']).p50)}</span>, <span key="b">{pctText((v as FunnelReply['ttp']['all']).p95)}</span>, <span key="n">{(v as FunnelReply['ttp']['all']).p50.n}</span>])}
              label="Laikas iki peržiūros" empty="Dar nėra duomenų." />
          </section>
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Serverio žingsniai (užklausos)</h3>
            <p className={`text-[11px] ${MUTED}`}>Čia skaičiuojamos užklausos, ne žmonės: vienai peržiūrai reikia kelių nuotraukų patikrų.</p>
            <Tbl head={['Žingsnis', 'Skaičius']} rows={SERVER_STEPS.map((s) => [<span key="s">{label(STEP_LT, s)}</span>, <span key="n">{num(steps[s])}</span>])} label="Serverio žingsniai" />
          </section>
          {cc.length > 0 && (
            <section className={`${CARD} flex flex-col gap-2`}>
              <h3 className="text-sm font-bold">Šalys (nusileidimai)</h3>
              <Tbl head={['Šalis', 'Nusileidimai']} rows={cc.map(([c, n]) => [<span key="c">{c === 'xx' ? 'nežinoma' : c.toUpperCase()}</span>, <span key="n">{shareText(n, num(steps.landing) || n)}</span>])} label="Šalys" />
            </section>
          )}
        </>
      )}
    </div>
  );
};
