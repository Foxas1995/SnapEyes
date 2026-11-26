// Nuotrauku kokybe: what the server saw of the photos people sent, as anonymous classes (the resolution class of the original, its orientation, the size of the iris in it, the colour class of the eye,
// the pupil class, the lid and fill results with their reason codes, how many eyes, the style chosen) and the server times, by campaign (default), device class or browser family. These are
// counts of classes; the photos themselves are kept up to 30 days since 2026-11-26 and shown on the page Peržiūros (api/_lib/keep.py, src/admin/Previews.tsx).
import { useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { CARD, H2, MUTED, Notice, Spinner, Tbl } from './ui';
import { FilterBar, FxCard, Partial, useFilters, useReport } from './TrafficUi';
import { fxTotal, groupLt, groupsOf, label, pctText, type FxReply } from './traffic';

const PHOTO = ['an_res', 'an_ori', 'an_iris', 'an_source', 'an_how', 'an_lm', 'an_lres', 'an_zoom', 'an_torch', 'an_lfail', 'an_dark', 'an_zv', 'an_verdict', 'en_cls', 'en_pupil', 'en_gate', 'en_reason', 'set_eyes', 'sv_style'] as const;
const STEP_NAME: Record<string, string> = { analyze: 'Nuotraukos patikra', enhance: 'Restauravimas', compose: 'Stiliaus peržiūra' };

export const PhotosPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [by, setBy] = useState<'cmp' | 'dev' | 'br'>('cmp');
  const [filters, setFilters] = useFilters();
  const { data, err, busy, reload } = useReport<FxReply>(call, 'photos', { days, by, ...filters });
  const groups = groupsOf(data?.fx, PHOTO, 5);
  const fx = data?.fx;
  const checked = fxTotal(fx, 'an_res');
  return (
    <div className="flex flex-col gap-4">
      <H2>Nuotraukų kokybė</H2>
      <FilterBar days={days} setDays={setDays} filters={filters} setFilters={setFilters} available={data?.available} only={['dev', 'br']} busy={busy} onReload={reload}
        note="Pačios nuotraukos matomos puslapyje „Peržiūros“ (saugomos iki 30 dienų). Čia tik klasės: nuotraukos dydžio klasė, padėtis, rainelės dydis, akies spalvos klasė, vyzdžio klasė, vartų rezultatai su priežasčių kodais, akių skaičius ir pasirinktas stilius."
        extra={
          <span className="flex flex-wrap gap-1.5 items-center ml-1" role="group" aria-label="Išskaidyti">
            <span className={`text-xs ${MUTED}`}>Išskaidyti:</span>
            {([['cmp', 'pagal kampaniją'], ['dev', 'pagal įrenginį'], ['br', 'pagal naršyklę']] as const).map(([k, l]) => (
              <button key={k} type="button" onClick={() => setBy(k)} aria-pressed={by === k} className={`px-2.5 py-1 rounded-lg text-xs border ${by === k ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{l}</button>
            ))}
          </span>
        } />
      {err && <Notice>{err}</Notice>}
      {data && <Partial partial={data.partial} recording={data.recording} />}
      {busy && !data && <Spinner />}
      {data && checked === 0 && <p className={`text-sm ${MUTED}`}>Šiuo laikotarpiu dar nėra nuotraukų patikrų.</p>}
      {data && checked > 0 && (
        <>
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Serverio laikai</h3>
            <Tbl head={['Žingsnis', 'p50', 'p95']} rows={Object.entries(data.times).map(([k, v]) => [<span key="k">{label(STEP_NAME, k)}</span>, <span key="a">{pctText(v.all.p50)}</span>, <span key="b">{pctText(v.all.p95)}</span>])} label="Serverio laikai" />
          </section>
          <FxCard title="Nuotraukos dydis (originalas)" fx={fx} metric="an_res" by={by} groups={groups} />
          <FxCard title="Padėtis" fx={fx} metric="an_ori" by={by} groups={groups} />
          <FxCard title="Rainelės dydis nuotraukoje" hint="Žemiau 280 px nieko geriau už „silpną“ nebūna; nuo 420 px nuotrauka gali būti „gera“." fx={fx} metric="an_iris" by={by} groups={groups} />
          <FxCard title="Iš kur nuotrauka" fx={fx} metric="an_source" by={by} groups={groups} />
          {/* the page's own live camera (?cam=1, 2026-11-26): how the photo was taken and what the camera gave */}
          {fxTotal(fx, 'an_how') > 0 && <FxCard title="Kaip nufotografuota" fx={fx} metric="an_how" by={by} groups={groups} />}
          {fxTotal(fx, 'an_lm') > 0 && <FxCard title="Gyva kamera: kadro būdas" fx={fx} metric="an_lm" by={by} groups={groups} />}
          {fxTotal(fx, 'an_lres') > 0 && <FxCard title="Gyva kamera: kadro dydis" fx={fx} metric="an_lres" by={by} groups={groups} />}
          {fxTotal(fx, 'an_zoom') > 0 && <FxCard title="Gyva kamera: priartinimas" fx={fx} metric="an_zoom" by={by} groups={groups} />}
          {fxTotal(fx, 'an_torch') > 0 && <FxCard title="Gyva kamera: šviesa (žibintuvėlis)" fx={fx} metric="an_torch" by={by} groups={groups} />}
          {fxTotal(fx, 'an_lfail') > 0 && <FxCard title="Gyva kamera neveikė" fx={fx} metric="an_lfail" by={by} groups={groups} />}
          {fxTotal(fx, 'an_zv') > 0 && <FxCard title="Gyva kamera: kiek priartinta" fx={fx} metric="an_zv" by={by} groups={groups} />}
          {fxTotal(fx, 'an_dark') > 0 && <FxCard title="Gyva kamera: per tamsu paspaudus" fx={fx} metric="an_dark" by={by} groups={groups} />}
          <FxCard title="Verdiktas" fx={fx} metric="an_verdict" by={by} groups={groups} />
          <FxCard title="Akies spalvos klasė" fx={fx} metric="en_cls" by={by} groups={groups} />
          <FxCard title="Vyzdžio klasė" fx={fx} metric="en_pupil" by={by} groups={groups} />
          <FxCard title="Atkūrimo vartai (voko ir užpildymo taisyklės)" fx={fx} metric="en_gate" by={by} groups={groups} />
          <FxCard title="Vartų priežasčių kodai" fx={fx} metric="en_reason" by={by} groups={groups} />
          <FxCard title="Kiek akių viename rinkinyje" fx={fx} metric="set_eyes" by={by} groups={groups} />
          <FxCard title="Pasirinktas stilius (didelės peržiūros)" fx={fx} metric="sv_style" by={by} groups={groups} />
          <p className={`text-[11px] ${MUTED}`}>Stulpeliai: {groups.map((g) => groupLt(by, g)).join(', ') || 'nėra'}. Skaičiai su n; mažas n reiškia kryptį, ne išvadą.</p>
        </>
      )}
    </div>
  );
};
