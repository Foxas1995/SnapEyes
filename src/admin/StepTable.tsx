// The master plan of one order or lab test, as the owner reads it (api/_lib/styles/steps.py; the admin actions order_steps and lab_steps send the
// StepsView): what will be drawn (the plan), what the step needs against what this function has (capacity), what each step really took (time, CPU, the
// increase of the process's resident size, the instance's own high-water mark: both labelled as that), how often it was killed, how many plate faults
// and errors it had, who made it, the claims, and the colour class and sealed gate result of each eye. Lithuanian only, like the rest of the page.
import type React from 'react';
import type { StepsView } from './api';
import { fmtNum, fmtSec, STYLE_LT } from './format';
import { Chip, JsonView, MUTED, Rows } from './ui';

type J = Record<string, unknown>;
const s = (v: unknown): string => (typeof v === 'string' ? v : typeof v === 'number' || typeof v === 'boolean' ? String(v) : '');
const obj = (v: unknown): J => (v && typeof v === 'object' && !Array.isArray(v) ? (v as J) : {});
const dash = (v: unknown): string => (v === null || v === undefined || v === '' ? '-' : String(v));

const WHY_LT: Record<string, string> = {
  time: 'laikas viršija darbo biudžetą: tokio žingsnio šiame serveryje niekada neužbaigtų',
  memory: 'atmintis viršija biudžetą',
  no_cost: 'kainų lentelėje šiam stiliui eilutės nėra',
};
const FAMILY_LT: Record<string, string> = { legacy: 'senasis variklis', singles: 'pavienės akys', collision: 'susidūrimas', universe: 'visata' };

/** One order's plan and steps. view is partial on purpose: a dry lab run has a plan and a capacity and nothing else. */
export const StepTable: React.FC<{ view: Partial<StepsView> }> = ({ view }) => {
  const plan = view.plan ? obj(view.plan) : null;
  if (!plan) return <p className={`text-xs ${MUTED}`}>Plano dar nėra: jį sukuria pirmas gamybos žingsnis.</p>;
  const cap = view.capacity;
  const steps = view.steps ?? [];
  const spec = obj(plan.opts);
  return (
    <div className="flex flex-col gap-3 min-w-0">
      <Rows rows={[
        ['Plano žyma (plan8)', <code key="p">{dash(plan.plan8)}</code>],
        ['Stilius', `${STYLE_LT[s(plan.style)] || s(plan.style)} (${FAMILY_LT[s(plan.family)] || s(plan.family)}), ${s(plan.eyes)} ak.`],
        ['Kaip nupiešta', `dizainas ${dash(plan.design_used)}${plan.fallback ? `, atsarginis variantas ${s(plan.fallback)}` : ''}, išdėstymas ${dash(plan.layout)}, drobė ${dash(plan.canvas)}`],
        ['Parinktys', Object.keys(spec).filter((k) => spec[k] !== null && spec[k] !== undefined).map((k) => `${k} ${s(spec[k])}`).join(', ') || '-'],
        ['Variklio versija / registras / plokštelės', `${dash(view.engine_v)} (plano: ${dash(plan.engine_v)}) / ${dash(plan.reg)} (dabar: ${dash(view.registry_hash)}) / pv ${dash(plan.pv)}`],
        ['Akių id', (Array.isArray(plan.eye_ids) ? (plan.eye_ids as unknown[]).map((x) => s(x) || '?').join(', ') : '-') || '-'],
        ['Darbinė kopija', plan.work_side ? `${s(plan.work_side)} px` : 'be registro ribos'],
        ['Perpiešimų (rerun) skaičius', String(view.rerun ?? 0)],
        ['Pažanga', view.progress ? `${view.progress.done} iš ${view.progress.of}${view.progress.step ? `, kitas: ${view.progress.step}` : ''}` : '-'],
      ]} />
      {cap && (
        <div className="flex flex-wrap gap-2 items-center">
          <Chip tone={cap.ok ? 'good' : 'bad'}>{cap.ok ? 'telpa į vieną iškvietimą' : (WHY_LT[cap.why || ''] || 'netelpa')}</Chip>
          <span className={`text-xs ${MUTED}`}>
            reikia ~{fmtNum(cap.need_s)} s iš {fmtNum(cap.budget_s)} s, ~{fmtNum(cap.est_mb)} MB iš {fmtNum(cap.mem_budget_mb)} MB, lėtėjimo koeficientas {fmtNum(cap.factor)}
          </span>
        </div>
      )}
      {steps.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead className={MUTED}>
              <tr>
                {['Žingsnis', 'Planuota', 'Faktiškai', 'CPU', 'Atmintis (prieaugis)', 'Instancijos HWM', 'Bandymai', 'Žūtys', 'Plokštelės', 'Klaidos', 'Kas', 'Kada'].map((h) => (
                  <th key={h} className="py-1 pr-3 font-semibold whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {steps.map((r) => {
                const d = r.done, t = r.try;
                const drift = Array.isArray(d?.drift) ? (d!.drift as unknown[]).map(obj).filter((x) => x.d_rgb !== undefined) : [];
                return (
                  <tr key={r.name} className="border-t border-white/5 align-top">
                    <td className="py-1.5 pr-3 font-semibold whitespace-nowrap">{r.name}{d ? '' : ' (nepadaryta)'}</td>
                    <td className="py-1.5 pr-3 whitespace-nowrap">{r.need_s != null ? `${fmtNum(r.need_s)} s` : '-'}{r.est_mb != null ? `, ${fmtNum(r.est_mb)} MB` : ''}</td>
                    <td className="py-1.5 pr-3 whitespace-nowrap">{d ? fmtSec(d.ms) : '-'}</td>
                    <td className="py-1.5 pr-3 whitespace-nowrap">{d?.cpu_s != null ? `${fmtNum(d.cpu_s)} s` : '-'}</td>
                    <td className="py-1.5 pr-3 whitespace-nowrap">{d?.peak_mb != null ? `+${fmtNum(d.peak_mb)} MB` : '-'}</td>
                    <td className="py-1.5 pr-3 whitespace-nowrap">{d?.hwm_mb != null ? `${fmtNum(d.hwm_mb)} MB` : '-'}</td>
                    <td className="py-1.5 pr-3">{t ? t.attempts : '-'}</td>
                    <td className="py-1.5 pr-3">{t ? <Chip tone={t.kills ? 'warn' : 'muted'}>{t.kills}</Chip> : '-'}{t?.open ? <Chip tone="warn">atidarytas</Chip> : null}</td>
                    <td className="py-1.5 pr-3">{t ? t.plate : '-'}{t?.plate_id ? ` (${t.plate_id})` : ''}</td>
                    <td className="py-1.5 pr-3 break-all">{t && t.errors.length ? t.errors.join(', ') : '-'}</td>
                    <td className="py-1.5 pr-3 whitespace-nowrap">{d ? dash(d.by) : '-'}</td>
                    <td className="py-1.5 pr-3 whitespace-nowrap">{d ? dash(d.at) : '-'}{drift.length ? ` · spalvų nuokrypis ${drift.map((x) => s(x.d_rgb)).join('/')}` : ''}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {view.locks && (
        <p className={`text-xs ${MUTED}`}>
          Užraktai: {Object.entries(view.locks).map(([k, v]) => `${k} ${v ? `laikomas ${fmtNum(v.age_s)} s${v.stale ? ' (pasenęs, bus perimtas)' : ''}` : 'laisvas'}`).join('; ')}
        </p>
      )}
      {view.eyes && view.eyes.length > 0 && (
        <div className="flex flex-col gap-0.5">
          {view.eyes.map((e) => (
            <p key={e.eye} className="text-xs break-words">
              Akis {e.eye}: id <code>{dash(e.eye_id)}</code>, klasė {dash(e.cls)}, vyzdys {dash(e.pupil)}, vartai lid {e.gate.lid === null ? '-' : e.gate.lid ? 'praėjo' : 'nepraėjo'}, fill {e.gate.fill === null ? '-' : e.gate.fill ? 'praėjo' : 'nepraėjo'}
            </p>
          ))}
        </div>
      )}
      {view.artwork && <JsonView label="Kūrinio įrašas (patikros, sėkla, laikai, plokštelės)" value={view.artwork} />}
      <JsonView label="Planas (plan.json)" value={plan} />
    </div>
  );
};
