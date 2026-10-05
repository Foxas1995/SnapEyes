// Stilių laboratorija: one style of the v3 engine drawn on ONE restored iris, whatever the style's stage (api/_lib/ops.py a_styles_lab).
// No image model is called and nothing is stored: a held or not yet visible style is looked at here and nowhere else. The eye is a
// restored iris square: the site's own restored sample, a file the owner picks (its centre square is sent), or the stored 4K eye of a
// lab test order (the real masters, no new Gemini call). The reply is the picture, the self checks that ran on it (T1 iris untouched,
// T6, T7 text, T12, T4 black share), the colour class, the seed, what the design picked (plates, wind) and the times. The seed is the one a customer's
// picture has (made from the eye's id and the plan's seed key) or, for the owner's before and after look at a board, the old one (from the iris bytes).
import { useEffect, useRef, useState } from 'react';
import type React from 'react';
import type { LabRow, StyleLabList, StyleLabResult } from './api';
import type { Call } from './AdminApp';
import { explain, fmtSec } from './format';
import { BTN, CARD, Chip, GOLD, INPUT, JsonView, MUTED, Notice, Spinner } from './ui';

const SAMPLE = '/assets/sample_eye_blue_restored.jpg';
const STAGE_LT: Record<string, string> = { planned: 'planuojamas', lab: 'laboratorija', preview: 'peržiūra (Greitai)', live: 'parduodamas', retired: 'išjungtas' };
const CHECK_LT: Record<string, string> = {
  t1: 'T1 rainelė nepaliesta', t6: 'T6 nieko ant rainelės', t7: 'T7 tekstas tik kliento', t12: 'T12 jokių širdžių', t4: 'T4 juodo dalis',
};

type Source = { kind: 'sample' } | { kind: 'file'; file: File } | { kind: 'order'; order: string };

function toB64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(String(fr.result).split(',')[1] || '');
    fr.onerror = () => reject(new Error('Failo nepavyko perskaityti.'));
    fr.readAsDataURL(blob);
  });
}

/** The centre square of an image, at most 2048 px, as JPEG base64: the form of a restored iris the server expects. */
async function squareB64(blob: Blob): Promise<string> {
  const url = URL.createObjectURL(blob);
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error('Nuotraukos nepavyko perskaityti.'));
      el.src = url;
    });
    const s = Math.min(img.naturalWidth, img.naturalHeight);
    const out = Math.min(2048, s);
    const c = document.createElement('canvas');
    c.width = out; c.height = out;
    const ctx = c.getContext('2d')!;
    ctx.drawImage(img, (img.naturalWidth - s) / 2, (img.naturalHeight - s) / 2, s, s, 0, 0, out, out);
    return c.toDataURL('image/jpeg', 0.95).split(',')[1] || '';
  } finally {
    URL.revokeObjectURL(url);
  }
}

export const StyleLab: React.FC<{ call: Call; lab: LabRow[] }> = ({ call, lab }) => {
  const [list, setList] = useState<StyleLabList | null>(null);
  const [listErr, setListErr] = useState('');
  const [style, setStyle] = useState('');
  const [canvas, setCanvas] = useState('');
  const [size, setSize] = useState(1024);
  const [names, setNames] = useState('');
  const [date, setDate] = useState('');
  const [seed, setSeed] = useState<'eye_id' | 'legacy'>('eye_id');
  const [src, setSrc] = useState<Source>({ kind: 'sample' });
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState('');
  const [res, setRes] = useState<StyleLabResult | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let live = true;
    void call<StyleLabList>('styles_lab', {}).then((r) => {
      if (!live) return;
      if (r.ok && r.data) {
        setList(r.data);
        setStyle((cur) => cur || r.data!.styles[0]?.id || '');
      } else setListErr(explain(r));
    });
    return () => { live = false; };
  }, [call]);

  const row = list?.styles.find((s) => s.id === style);
  const canvases = row?.canvases || [];
  const orders = lab.filter((l) => l.eyes > 0);

  const run = async () => {
    if (!row) return;
    setErr(''); setRes(null); setRunning(true);
    try {
      const body: Record<string, unknown> = { style: row.id, size, format: canvases.includes(canvas) ? canvas : canvases[0], names, date, seed };
      if (src.kind === 'order') { body.order = src.order; body.n = 1; }
      else if (src.kind === 'file') body.eye = await squareB64(src.file);
      else body.eye = await toB64(await (await fetch(SAMPLE)).blob());
      const r = await call<StyleLabResult>('styles_lab', body, 120_000);
      if (r.ok && r.data) setRes({ ...r.data, ms: r.ms });
      else setErr(explain(r));
    } catch (x) {
      setErr((x as Error).message || 'Nepavyko.');
    } finally {
      setRunning(false);
    }
  };

  const sc = res?.selfcheck;
  return (
    <section className={`${CARD} flex flex-col gap-3`}>
      <h3 className="text-base font-bold">Stilių laboratorija (v3 variklis)</h3>
      <p className={`text-sm ${MUTED}`}>
        Vienas stilius ant vienos jau restauruotos akies, bet kuriame etape (laboratorijos stiliai matomi tik čia). Gemini nekviečiamas, nieko nesaugoma,
        pirkėjas šių stilių neužsisakys, kol pats neatidarysi. Akis: svetainės restauruotas pavyzdys, tavo failas (siunčiamas vidurio kvadratas) arba
        laboratorijos testinio užsakymo 4K akis.
      </p>
      {listErr && <Notice>{listErr}</Notice>}
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Stilius</span>
          <select className={INPUT} value={style} onChange={(e) => { setStyle(e.target.value); setCanvas(''); }} disabled={running || !list}>
            {(list?.styles || []).map((s) => <option key={s.id} value={s.id}>{s.name} ({STAGE_LT[s.stage || ''] || s.stage})</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Drobė</span>
          <select className={INPUT} value={canvases.includes(canvas) ? canvas : canvases[0] || ''} onChange={(e) => setCanvas(e.target.value)} disabled={running || !row}>
            {canvases.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Dydis (ilgoji kraštinė, px)</span>
          <select className={INPUT} value={size} onChange={(e) => setSize(Number(e.target.value))} disabled={running}>
            {(list?.sizes || [1024]).map((n) => <option key={n} value={n}>{n}{n === 4096 ? ' (rodoma sumažinta + 100 % langas)' : ''}</option>)}
          </select>
        </label>
        <div className="flex flex-col gap-1 text-sm">
          <label htmlFor="stylelab-eye" className={MUTED}>Akis</label>
          <div className="flex gap-2 min-w-0">
            <select id="stylelab-eye" className={INPUT} disabled={running}
              value={src.kind === 'order' ? `order:${src.order}` : src.kind === 'file' ? 'file' : 'sample'}
              onChange={(e) => {
                const v = e.target.value;
                if (v.startsWith('order:')) setSrc({ kind: 'order', order: v.slice(6) });
                else if (v === 'sample') setSrc({ kind: 'sample' });
              }}>
              <option value="sample">Svetainės restauruotas pavyzdys</option>
              {src.kind === 'file' && <option value="file">Failas: {src.file.name}</option>}
              {orders.map((l) => <option key={l.order} value={`order:${l.order}`}>Testinis užsakymas {l.order}, 4K akis</option>)}
            </select>
            <button type="button" className={BTN} disabled={running} onClick={() => fileRef.current?.click()}>Failas</button>
          </div>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" aria-label="Restauruota akis"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) setSrc({ kind: 'file', file: f }); e.target.value = ''; }} />
        </div>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Vardai ant kūrinio (nebūtina)</span>
          <input className={INPUT} value={names} maxLength={60} onChange={(e) => setNames(e.target.value)} disabled={running} />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Data (nebūtina)</span>
          <input className={INPUT} value={date} maxLength={20} onChange={(e) => setDate(e.target.value)} disabled={running} />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className={MUTED}>Sėkla</span>
          <select className={INPUT} value={seed} onChange={(e) => setSeed(e.target.value === 'legacy' ? 'legacy' : 'eye_id')} disabled={running}>
            <option value="eye_id">nauja: iš akies id (tokia pati kaip pirkėjo kūrinio)</option>
            <option value="legacy">sena: iš rainelės baitų (kaip prieš sėklos pakeitimą, tik palyginimui)</option>
          </select>
        </label>
      </div>
      {row && row.plates.length > 0 && size === 4096 && (
        <p className={`text-xs ${MUTED}`}>Šis stilius 4096 px piešia iš 4K plokštelių ({row.plates.join(', ')}); jei jų saugykloje dar nėra, atsakymas bus „plate_unavailable“.</p>
      )}
      <button type="button" className={GOLD} disabled={!row || running} onClick={() => void run()}>{running && <Spinner />}Piešti</button>
      {err && <Notice>{err}</Notice>}
      {res && (
        <div className="flex flex-col gap-3 min-w-0">
          <p className="text-sm">
            {res.width} x {res.height} px, rainelės klasė <b>{res.cls}</b>, sėkla {res.seed}{res.seed_mode === 'legacy' ? ' (sena)' : ''}{res.eye_id ? `, akies id ${res.eye_id}` : ''}
            <span className={MUTED}> · serveryje {fmtSec(res.ms)}{res.times?.effect !== undefined ? `, efektas ${res.times.effect.toFixed(2)} s, iš viso ${res.times.total?.toFixed(2)} s` : ''}</span>
          </p>
          <img src={`data:image/jpeg;base64,${res.image}`} alt="Stiliaus rezultatas" className="max-w-full rounded-lg border border-white/10 bg-black" style={{ maxHeight: 640, objectFit: 'contain' }} />
          {res.crop && (
            <figure className="flex flex-col gap-1">
              <img src={`data:image/jpeg;base64,${res.crop.image}`} alt="100 % langas" className="max-w-full rounded-lg border border-white/10 bg-black" />
              <figcaption className={`text-xs ${MUTED}`}>100 % langas, x {res.crop.x}, y {res.crop.y}, {res.crop.w} x {res.crop.h} px</figcaption>
            </figure>
          )}
          {sc && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(sc.checks).map(([k, v]) => <Chip key={k} tone={v.ok ? 'good' : 'bad'}>{CHECK_LT[k] || k}: {v.ok ? 'gerai' : 'nepraėjo'}</Chip>)}
            </div>
          )}
          <JsonView label="Ką pasirinko stilius (plokštelės, vėjas, paletė)" value={res.facts} />
          <JsonView label="Planas (be pikselių)" value={res.plan} />
          <JsonView label="Patikrų ir laiko skaičiai" value={{ selfcheck: res.selfcheck, times: res.times, estimate: res.estimate }} />
        </div>
      )}
    </section>
  );
};
