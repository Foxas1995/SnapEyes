// Kodel nepavyksta: why a visit does not get through. Photos the analysis refused by reason, the restoration gate by code and sub-code, the share that needed a retake or a second restoration, the
// time of each server step (p50 and p95) and the errors per endpoint with the requests behind them; every count can be split by device class or browser family.
import { useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { CARD, H2, MUTED, Notice, Spinner, Tbl } from './ui';
import { FilterBar, FxCard, Partial, useFilters, useReport } from './TrafficUi';
import { BR_LT, DEV_LT, fxLines, fxTotal, groupLt, groupsOf, label, pctText, type FxReply } from './traffic';
import { shareText } from './stylesView';
import { ENDPOINT_LT } from './format';

const WHY = ['an_verdict', 'an_block', 'an_lock', 'en_gate', 'en_reason', 'en_retry', 'en_qa', 'set_gate', 'set_retake', 'err_ep', 'err_cls', 'err_reason'] as const;
const STEP_NAME: Record<string, string> = { analyze: 'Nuotraukos patikra', enhance: 'Restauravimas', compose: 'Stiliaus peržiūra' };

export const WhyPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [by, setBy] = useState<'' | 'dev' | 'br'>('');
  const [filters, setFilters] = useFilters();
  const { data, err, busy, reload } = useReport<FxReply>(call, 'why', { days, by: by || undefined, ...filters });
  const groups = by ? groupsOf(data?.fx, WHY, 5) : [];
  const fx = data?.fx;
  const retry = fxLines(fx, 'en_retry');
  const restor = fxTotal(fx, 'en_retry');
  const second = retry.filter((l) => l.value !== 'none').reduce((s, l) => s + l.total, 0);
  const sets = fxTotal(fx, 'set_retake');
  const retaken = fxLines(fx, 'set_retake').filter((l) => l.value !== '0').reduce((s, l) => s + l.total, 0);
  const reqs = fxLines(fx, 'req');
  const errs = fxLines(fx, 'err_ep');
  const errRows = reqs.map((r) => {
    const e = errs.find((x) => x.value === r.value)?.total ?? 0;
    return [<span key="e">{label(ENDPOINT_LT, r.value)}</span>, <span key="r">{r.total}</span>, <span key="x">{e}</span>, <span key="s">{shareText(e, r.total + e)}</span>];
  });
  return (
    <div className="flex flex-col gap-4">
      <H2>Kodėl nepavyksta</H2>
      <FilterBar days={days} setDays={setDays} filters={filters} setFilters={setFilters} available={data?.available} only={['dev', 'br']} busy={busy} onReload={reload}
        note="Šie skaičiai nefiltruojami pagal rinką ar kalbą (serverio įvykiai jų nenurodo), tik pagal įrenginį ir naršyklę. Kiekvienas skaičius rodomas su tuo, iš ko jis paimtas."
        extra={
          <span className="flex flex-wrap gap-1.5 items-center ml-1" role="group" aria-label="Išskaidyti">
            <span className={`text-xs ${MUTED}`}>Išskaidyti:</span>
            {([['', 'nereikia'], ['dev', 'pagal įrenginį'], ['br', 'pagal naršyklę']] as const).map(([k, l]) => (
              <button key={k} type="button" onClick={() => setBy(k)} aria-pressed={by === k} className={`px-2.5 py-1 rounded-lg text-xs border ${by === k ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{l}</button>
            ))}
          </span>
        } />
      {err && <Notice>{err}</Notice>}
      {data && <Partial partial={data.partial} recording={data.recording} />}
      {busy && !data && <Spinner />}
      {data && (
        <>
          <div className="grid gap-3 md:grid-cols-2">
            <section className={`${CARD} flex flex-col gap-1`}>
              <h3 className="text-sm font-bold">Pakartotinės nuotraukos ir antra restauracija</h3>
              <p className="text-sm">Rinkiniai, kuriems reikėjo pakartoti nuotrauką: <b>{shareText(retaken, sets)}</b></p>
              <p className="text-sm">Restauracijos, kurioms reikėjo antros: <b>{shareText(second, restor)}</b></p>
              <p className={`text-[11px] ${MUTED}`}>Antra restauracija kainuoja dar vieną 1K vaizdo kvietimą ir apie 14 s; ją daro tik tada, kai pirmoji neišlaikė voko taisyklės.</p>
            </section>
            <section className={`${CARD} flex flex-col gap-2`}>
              <h3 className="text-sm font-bold">Serverio laikai</h3>
              <Tbl head={['Žingsnis', 'p50', 'p95']} rows={Object.entries(data.times).map(([k, v]) => [<span key="k">{label(STEP_NAME, k)}</span>, <span key="a">{pctText(v.all.p50)}</span>, <span key="b">{pctText(v.all.p95)}</span>])} label="Serverio laikai" />
              {by && Object.entries(data.times).map(([k, v]) => {
                const m = by === 'dev' ? v.by_dev : v.by_br;
                return (
                  <p key={k} className="text-[11px] text-white/60 break-words">{label(STEP_NAME, k)}: {Object.entries(m).map(([g, p]) => `${groupLt(by, g)} ${pctText(p.p50)} / ${pctText(p.p95)}`).join('; ') || 'nėra duomenų'}</p>
                );
              })}
            </section>
          </div>
          <FxCard title="Nuotraukos patikra: verdiktas" hint="Ką serveris pasakė apie kiekvieną nuotrauką (viena peržiūra gali turėti kelias patikras)." fx={fx} metric="an_verdict" by={by || null} groups={groups} />
          <FxCard title="Kodėl nuotrauka atmesta" fx={fx} metric="an_block" by={by || null} groups={groups} />
          <FxCard title="Rainelės užfiksavimas" fx={fx} metric="an_lock" by={by || null} groups={groups} />
          <FxCard title="Atkūrimo vartai: kodas" hint="Vartai tikrina voką ir užpildymą; nepraėjusios akys eina į antrą restauraciją arba pakartojimą." fx={fx} metric="en_gate" by={by || null} groups={groups} />
          <FxCard title="Atkūrimo vartai: priežasties kodai" hint="Pirmasis priežasties kodas nepraėjusiai akiai (pvz. voko spalvos pleištas)." fx={fx} metric="en_reason" by={by || null} groups={groups} />
          <FxCard title="Antra restauracija" fx={fx} metric="en_retry" by={by || null} groups={groups} />
          <FxCard title="Spalvų patikra" fx={fx} metric="en_qa" by={by || null} groups={groups} />
          <FxCard title="Rinkinių vartai" hint="Rinkinys: akių rinkinys, kurį puslapis parodo vieną kartą; skaičiuojama pirma užklausa." fx={fx} metric="set_gate" by={by || null} groups={groups} />
          <FxCard title="Pakartojimai" fx={fx} metric="set_retake" by={by || null} groups={groups} />
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Klaidos pagal galinį tašką</h3>
            <Tbl head={['Galinis taškas', 'Užklausos', 'Klaidos', 'Klaidų dalis']} rows={errRows} label="Klaidos pagal galinį tašką" empty="Dar nėra duomenų." />
          </section>
          <FxCard title="Klaidų rūšys" fx={fx} metric="err_cls" by={by || null} groups={groups} />
          <FxCard title="Klaidų priežasčių kodai" fx={fx} metric="err_reason" by={by || null} groups={groups} />
          {by && <p className={`text-[11px] ${MUTED}`}>Išskaidyta pagal {by === 'dev' ? 'įrenginį' : 'naršyklę'}: {groups.map((g) => groupLt(by, g)).join(', ') || label(by === 'dev' ? DEV_LT : BR_LT, '-')}.</p>}
        </>
      )}
    </div>
  );
};
