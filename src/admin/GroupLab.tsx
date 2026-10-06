// Grupės laboratorija: one set of 1 to 8 restored eyes drawn in every style of that eye count at once (the contact sheet of the group, api/_lib/ops.py a_styles_lab_group), held and not yet visible
// styles included, with the restoration gate of every eye beside it; and, for the stored 4096 px masters of a lab test order, the real 4K master of any style on the sheet through the master plan's
// step runner (the action lab_steps: its time, the memory it added, the file size, the checks T1 to T12, the step table). No image model is called and nothing is stored but what a lab test order
// already holds. The owner looks at the sheet, then at the real 4K file, before he ticks L1 on the Stiliai page. Lithuanian only.
import { useRef, useState } from 'react';
import type React from 'react';
import type { GroupSheet, GroupTile, LabRow, LabStepsResult, StepsView } from './api';
import type { Call } from './AdminApp';
import { ArtworkFacts } from './ArtworkFacts';
import { AKYS, explain, fmtSec, ltCount, STYLE_LT } from './format';
import { fileEyes, isFirstN, sampleEyes } from './groupEyes';
import { StepTable } from './StepTable';
import { CLASS_LT, fallbackLt, gateCodeLt, PUPIL_LT, STAGE_TONE, stageLt, tileWhyLt } from './stylesView';
import { BTN, CARD, ExtLink, GOLD, INPUT, JsonView, MUTED, Notice, Spinner, Tbl, WrapChip } from './ui';

type J = Record<string, unknown>;
type Source = 'order' | 'files' | 'sample';

interface Run { key: string; label: string; busy: boolean; err: string; dry: boolean; res: LabStepsResult | null; steps: StepsView | null }
const tileKey = (t: GroupTile): string => `${t.id}|${t.look || ''}`;

const ruleText = (r: { ok: boolean | null; why?: string[] } | null | undefined): string =>
  !r || r.ok === null || r.ok === undefined ? 'nežinoma' : r.ok ? 'praėjo' : `nepraėjo${r.why && r.why.length ? `: ${r.why.map(gateCodeLt).join(', ')}` : ''}`;

export const GroupLab: React.FC<{ call: Call; lab: LabRow[] }> = ({ call, lab }) => {
  const orders = lab.filter((l) => l.eyes > 0);
  const [kind, setKind] = useState<Source>('sample');
  const [order, setOrder] = useState('');
  const [ns, setNs] = useState<number[]>([1, 2]);
  const [files, setFiles] = useState<File[]>([]);
  const [sampleN, setSampleN] = useState(2);
  const [size, setSize] = useState(480);
  const [names, setNames] = useState('');
  const [date, setDate] = useState('');
  const [swap, setSwap] = useState(false);
  const [rotate, setRotate] = useState(0);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState('');
  const [sheet, setSheet] = useState<(GroupSheet & { ms: number }) | null>(null);
  const [made, setMade] = useState<{ kind: Source; order: string; ns: number[]; names: string; date: string; opts: J } | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const chosen = orders.find((l) => l.order === (order || orders[0]?.order));
  const count = kind === 'order' ? ns.length : kind === 'files' ? files.length : sampleN;
  const opts: J = {};
  if (count === 2 && swap) opts.swap = true;
  if (count >= 3 && rotate > 0) opts.rotate = rotate;

  const run = async () => {
    setErr(''); setSheet(null); setRuns([]); setRunning(true);
    try {
      const body: J = { size, names, date, opts };
      if (kind === 'order') {
        if (!chosen || !ns.length) { setErr('Pasirink testinį užsakymą ir bent vieną jo akį.'); return; }
        body.order = chosen.order; body.ns = ns;
      } else if (kind === 'files') {
        if (!files.length) { setErr('Pasirink nuo 1 iki 8 failų.'); return; }
        body.eyes = await fileEyes(files);
      } else body.eyes = await sampleEyes(sampleN);
      const r = await call<GroupSheet>('styles_lab', body, 150_000);
      if (r.ok && r.data) {
        setSheet({ ...r.data, ms: r.ms });
        setMade({ kind, order: chosen?.order || '', ns: [...ns], names, date, opts });
      } else setErr(explain(r));
    } catch (x) {
      setErr((x as Error).message || 'Nepavyko.');
    } finally {
      setRunning(false);
    }
  };

  const can4k = !!made && made.kind === 'order' && isFirstN(made.ns);
  const anyBusy = runs.some((r) => r.busy);

  /** The real 4K master of one style of the sheet on the stored masters of the lab order (eyes 1 to n), then the artwork's own record for its checks. */
  const run4k = async (t: GroupTile, dry: boolean) => {
    if (!made) return;
    const key = `${tileKey(t)}|${dry ? 'dry' : 'run'}`;
    const label = `${t.name}${t.look ? ` (${t.look})` : ''}, ${ltCount(made.ns.length, AKYS)}${dry ? ', tik planas' : ''}`;
    const mine: Run = { key, label, busy: true, err: '', dry, res: null, steps: null };
    setRuns((cur) => [mine, ...cur.filter((x) => x.key !== key)]);
    const patch = (p: Partial<Run>) => setRuns((cur) => cur.map((x) => (x.key === key ? { ...x, ...p } : x)));
    const o: J = { ...made.opts };
    if (t.look) o.look = t.look;
    const r = await call<LabStepsResult>('lab_steps', { order: made.order, style: t.id, n: made.ns.length, layout: t.layout, names: made.names, date: made.date, opts: o, dry, fresh: !dry }, 150_000);
    if (!r.ok || !r.data) { patch({ busy: false, err: explain(r) }); return; }
    let steps: StepsView | null = null;
    if (!dry) {
      const s = await call<StepsView>('order_steps', { order: made.order });
      if (s.ok && s.data) steps = s.data;
    }
    patch({ busy: false, res: r.data, steps });
  };

  return (
    <section className={`${CARD} flex flex-col gap-3`} aria-label="Grupės laboratorija">
      <h3 className="text-base font-bold">Grupės laboratorija: vienas rinkinys visais stiliais</h3>
      <p className={`text-sm ${MUTED}`}>
        Nuo 1 iki 8 jau restauruotų akių vienu metu nupiešiamos kiekvienu to akių skaičiaus stiliumi, laboratorijos ir sulaikytais taip pat (be vandens ženklo: tai tavo paties žvilgsnis). Vartų rezultatas rodomas šalia ir
        paveikslėlio nesulaiko. Gemini nekviečiamas ir nieko nesaugoma. Testinio užsakymo saugomoms 4096 px akims bet kurio paveikslėlio tikras 4K kūrinys piešiamas mygtuku po lentele.
      </p>
      <fieldset className="flex flex-wrap gap-4">
        <legend className="text-xs font-bold mb-1">Akys</legend>
        {([['sample', 'Svetainės pavyzdys, kelis kartus'], ['files', 'Mano failai'], ['order', 'Testinio užsakymo 4K akys']] as const).map(([k, label]) => (
          <label key={k} className="flex items-center gap-2 text-sm">
            <input type="radio" name="grouplab-source" className="accent-[#f5c542]" checked={kind === k} disabled={running || (k === 'order' && orders.length === 0)} onChange={() => setKind(k)} />{label}
          </label>
        ))}
      </fieldset>
      {kind === 'sample' && (
        <label className="flex flex-col gap-1 text-sm max-w-[16rem]"><span className={MUTED}>Kiek akių (1 iki 8)</span>
          <select className={INPUT} value={sampleN} disabled={running} onChange={(e) => setSampleN(Number(e.target.value))}>{[1, 2, 3, 4, 5, 6, 7, 8].map((n) => <option key={n} value={n}>{n}</option>)}</select></label>
      )}
      {kind === 'files' && (
        <div className="flex flex-wrap items-center gap-2">
          <input ref={fileRef} type="file" accept="image/*" multiple className="hidden" aria-label="Restauruotos akys"
            onChange={(e) => { setFiles(Array.from(e.target.files || []).slice(0, 8)); e.target.value = ''; }} />
          <button type="button" className={BTN} disabled={running} onClick={() => fileRef.current?.click()}>Pasirinkti failus (iki 8)</button>
          <span className="text-xs text-white/70 break-all">{files.length ? files.map((f) => f.name).join(', ') : 'nepasirinkta'}</span>
        </div>
      )}
      {kind === 'order' && (
        <div className="flex flex-col gap-2">
          <label className="flex flex-col gap-1 text-sm max-w-[28rem]"><span className={MUTED}>Testinis užsakymas</span>
            <select className={INPUT} value={chosen?.order || ''} disabled={running} onChange={(e) => { setOrder(e.target.value); setNs([1]); }}>
              {orders.map((l) => <option key={l.order} value={l.order}>{l.order} ({l.eyes} 4K akių)</option>)}
            </select></label>
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Akių numeriai">
            {Array.from({ length: chosen?.eyes || 0 }, (_, i) => i + 1).map((n) => (
              <button key={n} type="button" aria-pressed={ns.includes(n)} disabled={running}
                onClick={() => setNs(ns.includes(n) ? ns.filter((x) => x !== n) : [...ns, n].sort((a, b) => a - b))}
                className={`px-3 py-1.5 rounded-lg text-sm border ${ns.includes(n) ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{n}</button>
            ))}
          </div>
          <p className={`text-xs ${MUTED}`}>Tikras 4K kūrinys galimas tik akims nuo 1 iki n be tarpų (lab_steps skaito akis 1 iki n).</p>
        </div>
      )}
      {orders.length === 0 && kind !== 'order' && <p className={`text-xs ${MUTED}`}>Testinių užsakymų su 4K akimis nėra: tikram 4K kūriniui sukurk vieną pirmiau (Laboratorija, „Pagaminti ir 4K“).</p>}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <label className="flex flex-col gap-1 text-sm"><span className={MUTED}>Paveikslėlio dydis (px)</span>
          <select className={INPUT} value={size} disabled={running} onChange={(e) => setSize(Number(e.target.value))}><option value={480}>480</option><option value={1024}>1024</option></select></label>
        <label className="flex flex-col gap-1 text-sm"><span className={MUTED}>Vardai (nebūtina)</span>
          <input className={INPUT} value={names} maxLength={200} disabled={running} onChange={(e) => setNames(e.target.value)} /></label>
        <label className="flex flex-col gap-1 text-sm"><span className={MUTED}>Data (nebūtina)</span>
          <input className={INPUT} value={date} maxLength={20} disabled={running} onChange={(e) => setDate(e.target.value)} /></label>
        {count === 2 && (
          <label className="flex items-center gap-2 text-sm self-end pb-2"><input type="checkbox" className="w-4 h-4 accent-[#f5c542]" checked={swap} disabled={running} onChange={(e) => setSwap(e.target.checked)} />Sukeisti akis vietomis</label>
        )}
        {count >= 3 && (
          <label className="flex flex-col gap-1 text-sm"><span className={MUTED}>Pasukimas (0 iki {Math.max(0, count - 1)})</span>
            <select className={INPUT} value={rotate} disabled={running} onChange={(e) => setRotate(Number(e.target.value))}>
              {Array.from({ length: count }, (_, i) => i).map((n) => <option key={n} value={n}>{n}</option>)}
            </select></label>
        )}
      </div>
      <div><button type="button" className={GOLD} disabled={running || count < 1} onClick={() => void run()}>{running && <Spinner />}Nupiešti visais stiliais</button></div>
      {err && <Notice>{err}</Notice>}

      {sheet && made && (
        <div className="flex flex-col gap-4 min-w-0">
          <p className="text-sm">
            {ltCount(sheet.group, AKYS)}, paveikslėlio dydis {sheet.size} px, serveryje {fmtSec(sheet.timing.total_ms)} (akių paruošimas {fmtSec(sheet.timing.eyes_ms)}).
            {sheet.pick ? ` Serverio rekomendacija: ${sheet.tiles.find((t) => t.id === sheet.pick)?.name || STYLE_LT[sheet.pick] || sheet.pick}${sheet.tiles.some((t) => t.id === sheet.pick) ? '' : ' (šioje lentelėje jo nėra)'}.` : ' Serverio rekomendacijos nėra.'}
          </p>
          {sheet.partial && <Notice tone="warn">Pritrūko laiko: parodyti tik tie paveikslėliai, kuriuos spėta nupiešti. Pabandyk dar kartą su 480 px arba mažiau akių.</Notice>}
          <Tbl label="Vartų rezultatas pagal akį" head={['Akis', 'Akies id', 'Klasė', 'Vyzdys', 'Voko taisyklė (lid)', 'Užpildymo taisyklė (fill)']}
            rows={sheet.eyes.map((e) => [String(e.eye), <code key="i">{e.eye_id || '-'}</code>, CLASS_LT[e.cls || ''] || e.cls || '-', PUPIL_LT[e.pupil || ''] || e.pupil || '-', ruleText(e.gate.lid), ruleText(e.gate.fill)])} />
          <JsonView label="Vartų skaičiai (values)" value={sheet.eyes.map((e) => ({ eye: e.eye, lid: e.gate.lid?.values, fill: e.gate.fill?.values }))} />
          <ul className="grid gap-3 grid-cols-1 min-[420px]:grid-cols-2 lg:grid-cols-3">
            {sheet.tiles.map((t) => (
              <li key={tileKey(t)} className="rounded-xl border border-white/10 bg-black/25 p-2.5 flex flex-col gap-2 min-w-0" data-testid={`tile-${t.id}`}>
                {t.image ? (
                  <img src={`data:image/jpeg;base64,${t.image}`} alt={`${t.name}${t.look ? ` (${t.look})` : ''}`} width={t.width} height={t.height} className="w-full h-auto rounded-lg border border-white/10 bg-black" />
                ) : (
                  <div className="aspect-[3/2] w-full rounded-lg border border-dashed border-white/20 flex items-center justify-center text-xs text-white/55 p-2 text-center">Nenupiešta: {tileWhyLt(t.why) || 'nežinoma priežastis'}</div>
                )}
                <p className="text-sm font-bold break-words">{t.name}{t.look ? ` (${t.look})` : ''}</p>
                <div className="flex flex-wrap gap-1">
                  <WrapChip>riba: {stageLt(t.ceiling)}</WrapChip>
                  <WrapChip tone={STAGE_TONE[t.stage || ''] || 'muted'}>galioja: {stageLt(t.stage)}</WrapChip>
                  {t.available && t.why && <WrapChip tone="warn">{tileWhyLt(t.why)}</WrapChip>}
                  {t.selfcheck && <WrapChip tone={t.selfcheck.ok ? 'good' : 'bad'}>savitikra: {t.selfcheck.ok ? 'gerai' : 'nepraėjo'}</WrapChip>}
                </div>
                <p className="text-[11px] text-white/60 break-words">
                  {t.layout ? `išdėstymas ${t.layout}` : ''}{t.design_used ? `, dizainas ${t.design_used}` : ''}{t.fallback ? `, atsarginis: ${fallbackLt(t.fallback)}` : ''}{t.ms !== undefined ? `, ${fmtSec(t.ms)}` : ''}
                </p>
                {t.available && (
                  <div className="flex flex-wrap gap-1.5">
                    <button type="button" className={`${BTN} !min-h-[34px] !px-2.5 text-xs`} disabled={!can4k || anyBusy} onClick={() => void run4k(t, true)}>4K planas</button>
                    <button type="button" className={`${BTN} !min-h-[34px] !px-2.5 text-xs`} disabled={!can4k || anyBusy} onClick={() => void run4k(t, false)}>4K kūrinys</button>
                  </div>
                )}
              </li>
            ))}
          </ul>
          {!can4k && <p className={`text-xs ${MUTED}`}>Tikras 4K kūrinys galimas tik tada, kai akys paimtos iš testinio užsakymo ir yra jo akys nuo 1 iki n be tarpų.</p>}
        </div>
      )}

      {runs.length > 0 && (
        <div className="flex flex-col gap-4" aria-label="4K rezultatai">
          <h4 className="text-sm font-bold">4K kūriniai ir planai</h4>
          {runs.map((r) => (
            <div key={r.key} className="border-t border-white/5 pt-3 flex flex-col gap-2 min-w-0">
              <p className="text-sm font-semibold break-words">{r.label}</p>
              {r.busy && <p className="flex items-center gap-2 text-xs"><Spinner />Gaminama: tai gali trukti iki minutės.</p>}
              {r.err && <Notice>{r.err}</Notice>}
              {r.res && r.dry && <StepTable view={r.res} />}
              {r.res && !r.dry && (
                <>
                  <p className="text-sm">{r.res.result === 'made' ? 'Kūrinys nupieštas.' : 'Kūrinys jau buvo nupieštas (rodomas tas pats failas).'}</p>
                  {typeof (r.res.artwork as J | null | undefined)?.url === 'string' && <ExtLink href={(r.res.artwork as J).url}>Atidaryti 4K kūrinį</ExtLink>}
                  <ArtworkFacts art={(r.steps?.artwork as J | null | undefined) ?? null} done={r.steps?.steps?.[r.steps.steps.length - 1]?.done ?? null} />
                  {r.steps && <StepTable view={r.steps} />}
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
