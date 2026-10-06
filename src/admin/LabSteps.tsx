// Gamybos žingsniai (laboratorija): the master steps of a v3 style on the 4096 px masters stored for a lab test order (api/_lib/ops.py a_lab_steps).
// The same plan, process guards, claim and executor a paid order's master goes through (api/_lib/styles/steps.py), with no payment and no image model:
// this is how the real time and memory of a design are read on the real instance (a fresh instance: the increase of the resident size is the design's own)
// and set against what the cost table said. "Tik planas" shows the plan and whether it fits this function without drawing anything.
import { useEffect, useState } from 'react';
import type React from 'react';
import type { LabRow, LabStepsResult, StepsView, StyleLabList } from './api';
import type { Call } from './AdminApp';
import { explain, fmtBytes, fmtSec } from './format';
import { StepTable } from './StepTable';
import { ArtworkFacts } from './ArtworkFacts';
import { BTN, CARD, ExtLink, GOLD, INPUT, MUTED, Notice, Spinner } from './ui';

type J = Record<string, unknown>;

export const LabSteps: React.FC<{ call: Call; lab: LabRow[] }> = ({ call, lab }) => {
  const [list, setList] = useState<StyleLabList | null>(null);
  const [style, setStyle] = useState('');
  const [order, setOrder] = useState('');
  const [names, setNames] = useState('');
  const [date, setDate] = useState('');
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState('');
  const [res, setRes] = useState<LabStepsResult | null>(null);
  const [view, setView] = useState<StepsView | null>(null);       // the order's plan and the artwork's own record (order_steps): the checks T1 to T12, the memory the step added, the plates
  const orders = lab.filter((l) => l.eyes > 0);

  useEffect(() => {
    let live = true;
    void call<StyleLabList>('styles_lab', {}).then((r) => {
      if (live && r.ok && r.data) { setList(r.data); setStyle((cur) => cur || r.data!.styles[0]?.id || ''); }
    });
    return () => { live = false; };
  }, [call]);

  const run = async (mode: 'dry' | 'run' | 'fresh') => {
    const o = order || orders[0]?.order;
    if (!o || !style) return;
    setErr(''); setRes(null); setView(null); setRunning(true);
    const r = await call<LabStepsResult>('lab_steps', { order: o, style, names, date, dry: mode === 'dry', fresh: mode === 'fresh' }, 120_000);
    if (r.ok && r.data) {
      setRes(r.data);
      if (mode !== 'dry') {
        const v = await call<StepsView>('order_steps', { order: o });
        if (v.ok && v.data) setView(v.data);
      }
    } else setErr(explain(r));
    setRunning(false);
  };

  const art = (res?.artwork || null) as J | null;
  const url = art && typeof art.url === 'string' ? art.url : null;
  return (
    <section className={`${CARD} flex flex-col gap-3`}>
      <h3 className="text-base font-bold">Gamybos žingsniai (4K meistras be mokėjimo)</h3>
      <p className={`text-sm ${MUTED}`}>
        Tas pats gamybos planas, atminties ir procesoriaus apsaugos, užraktas ir piešėjas, pagal kuriuos gaminamas apmokėto užsakymo kūrinys, bet su laboratorijos
        testinio užsakymo (lab-...) saugomomis 4096 px akimis: be mokėjimo ir be Gemini. Šviežioje instancijoje atminties prieaugis yra paties dizaino. Rezultatą
        lyginama su kainų lentele (planuota ir faktiškai). „Tik planas“ nieko nepiešia: parodo planą ir ar jis telpa į šio serverio vieną iškvietimą.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Stilius</span>
          <select className={INPUT} value={style} onChange={(e) => setStyle(e.target.value)} disabled={running || !list}>
            {(list?.styles || []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Testinis užsakymas (jo akys 1 iki n)</span>
          <select className={INPUT} value={order || orders[0]?.order || ''} onChange={(e) => setOrder(e.target.value)} disabled={running || orders.length === 0}>
            {orders.map((l) => <option key={l.order} value={l.order}>{l.order} ({l.eyes} 4K akių)</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Vardai ant kūrinio (nebūtina)</span>
          <input className={INPUT} value={names} maxLength={60} onChange={(e) => setNames(e.target.value)} disabled={running} />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Data (nebūtina)</span>
          <input className={INPUT} value={date} maxLength={20} onChange={(e) => setDate(e.target.value)} disabled={running} />
        </label>
      </div>
      {orders.length === 0 && <p className={`text-xs ${MUTED}`}>Testinių užsakymų su 4K akimis nėra: sukurk vieną pirmiau (Laboratorija, „Pagaminti ir 4K“).</p>}
      <div className="flex flex-wrap gap-2">
        <button type="button" className={BTN} disabled={running || !style || orders.length === 0} onClick={() => void run('dry')}>Tik planas</button>
        <button type="button" className={GOLD} disabled={running || !style || orders.length === 0} onClick={() => void run('run')}>{running && <Spinner />}Paleisti žingsnius</button>
        <button type="button" className={BTN} disabled={running || !style || orders.length === 0} onClick={() => void run('fresh')}>Piešti iš naujo</button>
      </div>
      {err && <Notice>{err}</Notice>}
      {res && (
        <div className="flex flex-col gap-3 min-w-0">
          <p className="text-sm">
            {res.result === 'dry' ? 'Tik planas (nieko nepiešta).' : res.result === 'made' ? 'Kūrinys nupieštas.' : 'Kūrinys jau buvo nupieštas (rodomas tas pats failas).'}
            {art && typeof art.bytes === 'number' ? <span className={MUTED}> {String(art.width)} x {String(art.height)} px, {fmtBytes(art.bytes)}{typeof art.seconds === 'number' ? `, ${fmtSec(art.seconds * 1000)}` : ''}</span> : null}
          </p>
          {url && <ExtLink href={url}>Atidaryti 4K kūrinį</ExtLink>}
          {res.result !== 'dry' && <ArtworkFacts art={(view?.artwork as J | null | undefined) ?? null} done={view?.steps?.[view.steps.length - 1]?.done ?? null} />}
          <StepTable view={res} />
        </div>
      )}
    </section>
  );
};
