// The style half of an order's detail page (spec 3.3 WP13): the style's own options and what the plan froze, the restoration gate of every eye and the set level result at checkout, the fallback,
// the edge mode, the file and its checks and plates, the intermediates, the plan's identity at checkout against the one the page showed, and the approved preview beside the delivered file.
// The plan and its steps are the StepTable above it; this is what the owner reads to say "is this the picture the customer approved". The links to the images are made on click
// (the action order_link), so nothing heavy is loaded until he asks. Lithuanian only; codes and numbers, and the customer's names only in the order's own block above.
import { useState } from 'react';
import type React from 'react';
import type { OrderDetail, OrderLink, StepsView } from './api';
import type { Call } from './AdminApp';
import { ArtworkFacts } from './ArtworkFacts';
import { explain, fmtBytes } from './format';
import { CLASS_LT, fallbackLt, gateCodeLt, optionsText, PLAN8_NOTE_LT, PUPIL_LT, relPath } from './stylesView';
import { BTN, MUTED, Notice, Rows, Spinner, Thumb, Tbl } from './ui';

type J = Record<string, unknown>;
const obj = (v: unknown): J => (v && typeof v === 'object' && !Array.isArray(v) ? (v as J) : {});
const text = (v: unknown): string => (typeof v === 'string' ? v : typeof v === 'number' || typeof v === 'boolean' ? String(v) : '');
const dash = (v: unknown): string => (v === null || v === undefined || v === '' ? '-' : String(v));

const Compare: React.FC<{ order: string; call: Call; previews: { eye: number; path: string }[]; file: string | null }> = ({ order, call, previews, file }) => {
  const [links, setLinks] = useState<{ eye: number; url: string }[] | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const show = async () => {
    setBusy(true); setErr('');
    const all = await Promise.all([...previews.map((p) => call<OrderLink>('order_link', { order, path: p.path })), ...(file ? [call<OrderLink>('order_link', { order, path: file })] : [])]);
    setBusy(false);
    const bad = all.find((r) => !r.ok || !r.data);
    if (bad) { setErr(bad.reason === 'not_found' ? 'Failo nebėra: užsakymo failai ištrinti arba pasenę.' : explain(bad)); return; }
    setLinks(previews.map((p, i) => ({ eye: p.eye, url: all[i].data!.url })));
    setFileUrl(file ? all[previews.length].data!.url : null);
  };
  if (!previews.length && !file) return <p className={`text-xs ${MUTED}`}>Peržiūros ir kūrinio failų palyginti nėra ko.</p>;
  return (
    <div className="flex flex-col gap-2">
      <p className={`text-xs ${MUTED}`}>Patvirtinta peržiūra yra pirkėjo patvirtinta restauruota rainelė (1024 px, be vandens ženklo). Nuorodos sukuriamos paspaudus ir galioja valandą.</p>
      {!links && <div><button type="button" className={BTN} disabled={busy} onClick={() => void show()}>{busy && <Spinner />}Parodyti peržiūrą ir failą</button></div>}
      {err && <Notice>{err}</Notice>}
      {links && (
        <div className="flex flex-wrap gap-3">
          {links.map((l) => <Thumb key={l.eye} src={l.url} alt={`Patvirtinta peržiūra, akis ${l.eye}`} size={180} />)}
          {fileUrl && <Thumb src={fileUrl} alt="Pristatytas kūrinys" size={300} />}
        </div>
      )}
    </div>
  );
};

export const OrderStyle: React.FC<{ d: OrderDetail; steps: StepsView; call: Call }> = ({ d, steps, call }) => {
  const plan = obj(steps.plan);
  const art = steps.artwork ? obj(steps.artwork) : null;
  const order = d.order;
  const checkout = obj(obj(d.records['order.json']).checkout);
  const last = steps.steps.length ? steps.steps[steps.steps.length - 1] : null;
  const done = last?.done ?? null;
  const gate = typeof checkout.gate === 'string' ? checkout.gate : null;
  const note = typeof checkout.plan8_note === 'string' ? checkout.plan8_note : null;
  const previews = d.eyes.flatMap((e) => {
    const p = relPath(order, obj(obj(d.records[`draft/eye_${e.eye}.json`]).preview).path);
    return p ? [{ eye: e.eye, path: p }] : [];
  });
  const file = relPath(order, obj(d.records['delivery.json']).key);
  const plates = Array.isArray(plan.plates_needed) ? (plan.plates_needed as J[]) : [];
  const styleFiles = d.files.filter((f) => f.path.startsWith('style/'));
  const outputs = (done?.outputs ?? []).filter((o) => o && typeof o.path === 'string');
  return (
    <div className="flex flex-col gap-4">
      <Rows rows={[
        ['Parinktys', optionsText(plan)],
        ['Atsarginis variantas', plan.fallback ? fallbackLt(text(plan.fallback)) : 'nebuvo'],
        ['Vartai pirkimo metu (visam rinkiniui)', gate ? gateCodeLt(gate) : 'neužfiksuota (užsakymas be mokėjimo puslapio)'],
        ['Plano žyma pirkimo metu', `${dash(checkout.plan && obj(checkout.plan).plan8)}${checkout.plan8_shown === false ? ' (puslapis plano žymos nesiuntė)' : ''}`],
        ['Žyma, kurią rodė puslapis', checkout.plan8_page ? text(checkout.plan8_page) : '-'],
        ['Pastaba apie planą', note ? PLAN8_NOTE_LT[note] || note : 'nėra'],
      ]} />

      <div className="flex flex-col gap-1.5">
        <h4 className="text-xs font-bold text-white/80">Vartai pagal akį (užantspauduotas profilis)</h4>
        {steps.eyes.length === 0 && <p className={`text-xs ${MUTED}`}>Akių profilių įrašų nėra.</p>}
        {steps.eyes.map((e) => {
          const why = [...(e.gate_why?.lid ?? []), ...(e.gate_why?.fill ?? [])];
          const r = (v: boolean | null) => (v === null ? 'nežinoma' : v ? 'praėjo' : 'nepraėjo');
          return (
            <p key={e.eye} className="text-xs break-words">
              Akis {e.eye}: klasė {CLASS_LT[e.cls || ''] || dash(e.cls)}, vyzdys {PUPIL_LT[e.pupil || ''] || dash(e.pupil)}, voko taisyklė (lid) {r(e.gate.lid)}, užpildymo taisyklė (fill) {r(e.gate.fill)}
              {why.length ? `: ${why.map(gateCodeLt).join(', ')}` : ''}
            </p>
          );
        })}
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="text-xs font-bold text-white/80">Kūrinys ir jo patikros</h4>
        <ArtworkFacts art={art} done={done} />
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="text-xs font-bold text-white/80">Plokštelės, kurių reikėjo pagal planą</h4>
        <Tbl label="Plano plokštelės" head={['Plokštelė', 'Šeima', 'Dydis', 'sha256']} empty="Šis stilius plokštelių nenaudoja, arba planas jų nepasakė iš anksto."
          rows={plates.map((p) => [text(p.id), text(p.family), fmtBytes(typeof p.bytes === 'number' ? p.bytes : null), text(p.sha256).slice(0, 12)])} />
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="text-xs font-bold text-white/80">Žingsnio išvestis ir tarpiniai failai</h4>
        <Tbl label="Žingsnio išvestis" head={['Failas', 'Dydis', 'sha12']} empty="Žingsnis dar nepadarytas."
          rows={outputs.map((o) => [o.path.split('/').slice(-2).join('/'), o.bytes != null ? fmtBytes(o.bytes) : '-', o.sha12 || '-'])} />
        <p className={`text-xs ${MUTED}`}>
          Stiliaus aplanko failai: {styleFiles.length ? styleFiles.map((f) => f.path.replace(/^style\//, '')).join(', ') : 'nėra'}.
          {styleFiles.some((f) => /\.png$/.test(f.path)) ? '' : ' Tarpinių vaizdų (žingsnių rėmų) nėra: kūrinys piešiamas vienu žingsniu.'}
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="text-xs font-bold text-white/80">Patvirtinta peržiūra ir pristatytas failas</h4>
        <Compare order={order} call={call} previews={previews} file={file} />
      </div>
    </div>
  );
};
