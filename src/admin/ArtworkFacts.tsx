// What one 4K artwork of the v3 engine says about itself (the artwork_<digest>.json record, api/_lib/styles/steps.py _exec_engine): its size and file weight, how long it took and how much memory
// the step added (the increase of the process's resident size, with the instance's own high-water mark beside it: the two are different numbers), the checks T1 to T12 that ran on it, the colour
// check, the design and seed, the edge mode of every contact, the plates it drew from. Used by the order detail and by the laboratory's 4K runs. Lithuanian only; codes and numbers.
import type React from 'react';
import type { StepDone } from './api';
import { fmtBytes, fmtNum, fmtSec } from './format';
import { edgeText, selfcheckLt, selfcheckRows } from './stylesView';
import { JsonView, MUTED, Rows, WrapChip } from './ui';

type J = Record<string, unknown>;
const obj = (v: unknown): J => (v && typeof v === 'object' && !Array.isArray(v) ? (v as J) : {});
const numOr = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const text = (v: unknown): string => (typeof v === 'string' ? v : typeof v === 'number' || typeof v === 'boolean' ? String(v) : '');

export const ArtworkFacts: React.FC<{ art: J | null; done?: StepDone | null }> = ({ art, done }) => {
  if (!art) return <p className={`text-xs ${MUTED}`}>Kūrinio įrašo nėra (kūrinys dar nepagamintas arba įrašas neperskaitytas).</p>;
  const sc = selfcheckRows(art);
  const qa = obj(art.qa);
  const times = obj(art.times);
  const plates = Array.isArray(obj(art.facts).plates) ? (obj(art.facts).plates as unknown[]).map(text).filter(Boolean) : [];
  return (
    <div className="flex flex-col gap-3 min-w-0">
      <div className="flex flex-wrap gap-1.5">
        {sc.length === 0 && <WrapChip tone="muted">savitikros įrašo nėra</WrapChip>}
        {sc.map(([k, ok, det]) => <WrapChip key={k} tone={ok ? 'good' : 'bad'}>{selfcheckLt(k)}: {ok ? 'gerai' : 'nepraėjo'}{det ? ` (${det})` : ''}</WrapChip>)}
        {qa.ok !== undefined && qa.ok !== null && <WrapChip tone={qa.ok ? 'good' : 'bad'}>spalvų patikra: {qa.ok ? 'gerai' : 'nepraėjo'}</WrapChip>}
        {art.needs_review === true && <WrapChip tone="warn">laukia tavo peržiūros</WrapChip>}
      </div>
      <Rows rows={[
        ['Failas', `${text(art.width) || '?'} x ${text(art.height) || '?'} px, ${fmtBytes(numOr(art.bytes))}`],
        ['Gamybos laikas', done ? `${fmtSec(done.ms)}${done.cpu_s != null ? `, procesorius ${fmtNum(done.cpu_s)} s` : ''}` : numOr(art.seconds) !== null ? `${fmtNum(numOr(art.seconds))} s` : '-'],
        ['Atminties prieaugis', done?.peak_mb != null ? `+${fmtNum(done.peak_mb)} MB (proceso VmRSS padidėjimas per žingsnį)${done.hwm_mb != null ? `, instancijos aukščiausia reikšmė (VmHWM) ${fmtNum(done.hwm_mb)} MB` : ''}` : '-'],
        ['Piešimo dalys (s)', Object.keys(times).length ? Object.entries(times).map(([k, v]) => `${k} ${fmtNum(numOr(v))}`).join(', ') : '-'],
        ['Dizainas ir sėkla', `${text(art.design_used) || '-'}, sėkla ${text(art.seed) || '-'}`],
        ['Krašto režimas', edgeText(art)],
        ['Panaudotos plokštelės', plates.length ? plates.join(', ') : 'nėra'],
        ['Variklis', `versija ${text(art.engine_v) || '-'}, plokštelių versija ${text(art.pv) || '-'}, registras ${text(art.reg) || '-'}, perpiešimų ${text(art.rerun) || '0'}`],
      ]} />
      {sc.length > 0 && <JsonView label="Savitikros skaičiai" value={art.selfcheck} />}
    </div>
  );
};
