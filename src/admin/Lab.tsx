// Laboratorija: any photo (or the site's AI sample eye) through the REAL pipeline, from this browser, exactly as /try
// calls it: /api/analyze -> /api/deglare -> /api/enhance -> /api/compose, with every stage's image, reply and time,
// and the estimated cost shown before it runs. Optionally a 4K master too: /api/admin lab_start gives a test order
// (lab-<date>-<rand>) and its unlock ticket, then /api/master_eye and /api/master_compose make the 4K files. The
// test orders are listed below and can be deleted. Results show next to what started them: the run's progress card is
// brought into view when it starts and a failed stage when it fails; a deletion's result is a toast at the bottom.
import { useCallback, useEffect, useRef, useState } from 'react';
import type React from 'react';
import { getHealth, publicCall } from './api';
import type { LabRow, LabStart, Reply } from './api';
import type { Call } from './AdminApp';
import { DEFAULT_PRICES, explain, fmtSec, fmtUsd, STYLE_LT } from './format';
import { BTN, CARD, ConfirmDialog, DANGER, ExtLink, GOLD, H2, INPUT, JsonView, MUTED, Notice, Spinner, Thumb, Toast } from './ui';
import type { ConfirmSpec, Tone } from './ui';
import { DEFAULT_STYLE, LEGACY_IDS } from '../shared/styles';
import { StyleLab } from './StyleLab';
import { GroupLab } from './GroupLab';
import { LabSteps } from './LabSteps';

const SAMPLE = '/assets/sample_eye_blue_1789706902835.jpg';
const STYLES = LEGACY_IDS;   // the styles the legacy pipeline above draws (api/_lib/styles_registry.py); the v3 engine's styles are looked at in StyleLab below, without the image model

type J = Record<string, unknown>;
type Status = 'wait' | 'run' | 'ok' | 'fail' | 'skip';
interface Stage { key: string; label: string; status: Status; ms?: number; serverMs?: number; image?: string; link?: string; json?: unknown; note?: string }

const STAGES: [string, string][] = [
  ['analyze', '1. Analizė (/api/analyze)'], ['deglare', '2. Atspindžiai ir vokai (/api/deglare)'],
  ['enhance', '3. Restauravimas (/api/enhance)'], ['compose', '4. Peržiūros kompozicija (/api/compose)'],
  ['lab_start', '5. Testo užsakymas (/api/admin lab_start)'], ['master_eye', '6. 4K akis (/api/master_eye)'],
  ['master_compose', '7. 4K kūrinys (/api/master_compose)'],
];

const B64 = /^[A-Za-z0-9+/]+={0,2}$/;
const jpeg = (b64: unknown): string | undefined => (typeof b64 === 'string' && b64.length > 100 && B64.test(b64.slice(0, 2000)) ? `data:image/jpeg;base64,${b64}` : undefined);
const strip = (s: string) => (s.includes(',') ? s.split(',')[1] : s);

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Nuotraukos nepavyko perskaityti.'));
    img.src = src;
  });
}

/** The same canvas cut /try makes (src/try/TryApp.tsx drawToDataUrl). */
function draw(img: HTMLImageElement, sx: number, sy: number, sw: number, sh: number, w: number, h: number, q: number): string {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d')!;
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h);
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, w, h);
  return c.toDataURL('image/jpeg', q);
}

const ICON: Record<Status, string> = { wait: 'laukia', run: 'vykdoma', ok: 'baigta', fail: 'klaida', skip: 'praleista' };
const TONE: Record<Status, string> = { wait: 'text-white/50', run: 'text-sky-200', ok: 'text-emerald-200', fail: 'text-red-200', skip: 'text-white/40' };

export const LabPage: React.FC<{ call: Call }> = ({ call }) => {
  const [src, setSrc] = useState<{ url: string; name: string; sample: boolean } | null>(null);
  const [style, setStyle] = useState(DEFAULT_STYLE);
  const [names, setNames] = useState('');
  const [want4k, setWant4k] = useState(false);
  const [stages, setStages] = useState<Stage[]>([]);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState('');
  const [deglareModel, setDeglareModel] = useState(false);
  const [lab, setLab] = useState<LabRow[]>([]);
  const [labErr, setLabErr] = useState('');
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);
  const [toast, setToast] = useState<{ tone: Tone; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const progressRef = useRef<HTMLElement>(null);
  const [runId, setRunId] = useState(0);

  // a run's progress card comes into view when the run starts (on a phone it begins below the Paleisti button) ...
  useEffect(() => {
    if (runId) progressRef.current?.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }, [runId]);
  // ... and so does the stage that failed, with its reason
  const failed = stages.find((x) => x.status === 'fail')?.key;
  useEffect(() => {
    if (failed) document.getElementById(`lab-stage-${failed}`)?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [failed, runId]);
  // a plain success closes itself; a failure stays until closed
  useEffect(() => {
    if (!toast || toast.tone !== 'good') return;
    const t = setTimeout(() => setToast((cur) => (cur === toast ? null : cur)), 9000);
    return () => clearTimeout(t);
  }, [toast]);

  const loadLab = useCallback(async () => {
    const r = await call<{ lab: LabRow[] }>('lab_list');
    if (r.ok && r.data) { setLab(r.data.lab); setLabErr(''); } else setLabErr(explain(r));
  }, [call]);

  useEffect(() => {
    let live = true;
    void call<{ lab: LabRow[] }>('lab_list').then((r) => {
      if (!live) return;
      if (r.ok && r.data) setLab(r.data.lab); else setLabErr(explain(r));
    });
    void getHealth().then((h) => { if (live) setDeglareModel(!!h.data?.deglare_model); });
    return () => { live = false; };
  }, [call]);

  useEffect(() => () => { if (src && !src.sample) URL.revokeObjectURL(src.url); }, [src]);

  const p = DEFAULT_PRICES;
  const base = p.vision + p.image_1k + (deglareModel ? p.image_1k : 0);
  const estimate = base + (want4k ? p.image_4k : 0);

  const set = (key: string, patch: Partial<Stage>) => setStages((all) => all.map((s) => (s.key === key ? { ...s, ...patch } : s)));

  const step = async <T,>(key: string, run: () => Promise<Reply<T>>, show: (d: T) => Partial<Stage>): Promise<T | null> => {
    set(key, { status: 'run' });
    const r = await run();
    const d = r.data as unknown as J | null;
    const serverMs = d && typeof d.ms === 'number' ? d.ms : undefined;
    if (!r.ok || !r.data) {
      set(key, { status: 'fail', ms: r.ms, serverMs, json: r.data, note: d && typeof d.message === 'string' && d.message ? d.message : explain(r as Reply<unknown>) });
      return null;
    }
    set(key, { status: 'ok', ms: r.ms, serverMs, json: r.data, ...show(r.data) });
    return r.data;
  };

  const run = async () => {
    if (!src) return;
    setErr(''); setRunning(true);
    setStages(STAGES.map(([key, label]) => ({ key, label, status: (!want4k && ['lab_start', 'master_eye', 'master_compose'].includes(key) ? 'skip' : 'wait') as Status })));
    setRunId((n) => n + 1);
    try {
      const img = await loadImage(src.url);
      const W = img.naturalWidth, H = img.naturalHeight;
      const f = Math.min(1, 1600 / Math.max(W, H));
      const small = draw(img, 0, 0, W, H, Math.round(W * f), Math.round(H * f), 0.9);
      const device = { ua: navigator.userAgent.slice(0, 300), w: screen.width, h: screen.height, source: 'lab' };
      const a = await step<J>('analyze', () => publicCall('/api/analyze', { image: strip(small), origWidth: W, origHeight: H, device, lang: 'en' }), (d) => ({ image: jpeg(d.preview) }));
      if (!a) return;
      const q = (a.quality || {}) as J;
      if (a.ok === false || !a.iris) { set('analyze', { status: 'fail', note: `Akies nerasta: ${String(a.message || '')}` }); return; }
      if (!a.ticket) {
        set('analyze', { status: 'fail', note: `Nuotrauka užblokuota: ${String(q.block_reason || (q.locked === false ? 'rainelės kraštas nerastas' : 'nežinoma'))}. ${String(q.message || '')}` });
        return;
      }
      const iris = a.iris as { cx: number; cy: number; r: number };
      const pad = typeof a.pad === 'number' ? a.pad : 1.12;
      const S = 2 * iris.r * W * pad;
      const out = Math.min(1400, Math.round(S));
      const crop = draw(img, iris.cx * W - S / 2, iris.cy * H - S / 2, S, S, out, out, 0.95);
      const d = await step<J>('deglare', () => publicCall('/api/deglare', { crop: strip(crop), pad, ticket: a.ticket, pupil_r: a.pupil_r, glare_boxes: a.glare_boxes_crop || [], lang: 'en' }), (x) => ({ image: jpeg(x.crop) }));
      if (!d) return;
      const e = await step<J>('enhance', () => publicCall('/api/enhance', { crop: d.crop, mode: 'artistic', pad, ticket: a.ticket, used_sr: d.used_sr, meta: q, lang: 'en' }), (x) => ({ image: jpeg(x.image) }));
      if (!e) return;
      // e.image is the watermarked 800 px display copy /try shows; the clean restoration comes back only sealed
      // (api/_lib/preview.py), and the server opens it for the preview and for the 4K master
      const sealed = typeof e.sealed === 'string' && e.sealed ? e.sealed : null;
      const c = await step<J>('compose', () => publicCall('/api/compose', { ...(sealed ? { sealed: [sealed] } : { irises: [e.image] }), style, names, pad, lang: 'en' }), (x) => ({ image: jpeg(x.image) }));
      if (!c || !want4k) return;
      const ls = await step<LabStart>('lab_start', () => call<LabStart>('lab_start', {}), (x) => ({ note: `Testo užsakymas ${x.order}` }));
      if (!ls) return;
      const m = await step<J>('master_eye', () => publicCall('/api/master_eye', { crop: d.crop, ...(sealed ? { sealed } : { preview: e.image }), pad, ticket: ls.ticket, order: ls.order, eye: 1 }),
        (x) => ({ note: `4K ${String(x.width)}x${String(x.height)}${x.needs_review ? ', patikra liepė peržiūrėti' : ''}` }));
      if (!m) return;
      await step<J>('master_compose', () => publicCall('/api/master_compose', { order: ls.order, ticket: ls.ticket, keys: [`orders/${ls.order}/eye_1.jpg`], style, layout: 'single', names, title: '' }),
        (x) => ({ link: typeof x.url === 'string' ? x.url : undefined, note: `${String(x.width)}x${String(x.height)}${x.needs_review ? ', patikra liepė peržiūrėti' : ''}` }));
      void loadLab();
    } catch (x) {
      setErr((x as Error).message || 'Nepavyko.');
    } finally {
      setRunning(false);
    }
  };

  const pick = (file: File | undefined) => {
    if (!file) return;
    setSrc({ url: URL.createObjectURL(file), name: file.name, sample: false });
    setStages([]);
  };

  const total = stages.reduce((s, x) => s + (x.status === 'ok' ? x.ms || 0 : 0), 0);

  return (
    <div className="flex flex-col gap-4">
      <H2>Laboratorija</H2>
      <section className={`${CARD} flex flex-col gap-3`}>
        <p className={`text-sm ${MUTED}`}>
          Tikras procesas, tie patys adresai kaip /try. Kiekvienas paleidimas kainuoja tikrus Gemini pinigus.
          Tavo nuotrauka niekur nesaugoma (tik 4K testo failai, kuriuos gali ištrinti žemiau).
        </p>
        <div className="flex flex-wrap gap-2">
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={(e) => pick(e.target.files?.[0])} aria-label="Nuotrauka" />
          <button type="button" className={BTN} onClick={() => fileRef.current?.click()} disabled={running}>Pasirinkti nuotrauką</button>
          <button type="button" className={BTN} disabled={running} onClick={() => { setSrc({ url: SAMPLE, name: 'Svetainės pavyzdys (AI akis)', sample: true }); setStages([]); }}>
            Svetainės pavyzdys
          </button>
        </div>
        {src && (
          <div className="flex items-center gap-3 min-w-0">
            <img src={src.url} alt="" className="w-16 h-16 object-cover rounded-lg border border-white/10" />
            <p className="text-sm break-all min-w-0">{src.name}</p>
          </div>
        )}
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm">
            <span className={MUTED}>Stilius</span>
            <select className={INPUT} value={style} onChange={(e) => setStyle(e.target.value)} disabled={running}>
              {STYLES.map((s) => <option key={s} value={s}>{STYLE_LT[s]}</option>)}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className={MUTED}>Vardai ant kūrinio (nebūtina)</span>
            <input className={INPUT} value={names} maxLength={60} onChange={(e) => setNames(e.target.value)} disabled={running} />
          </label>
        </div>
        <label className="flex items-start gap-2 text-sm">
          <input type="checkbox" className="w-4 h-4 mt-0.5 accent-[#f5c542]" checked={want4k} onChange={(e) => setWant4k(e.target.checked)} disabled={running} />
          <span>Pagaminti ir 4K (testo užsakymas „lab-...“, pažymėtas kaip testas, jį galima ištrinti). Prideda apie {fmtUsd(p.image_4k)} ir 30-50 s.</span>
        </label>
        <p className="text-sm">
          Įvertis prieš paleidžiant: <b>apie {fmtUsd(estimate)}</b>
          <span className={MUTED}> (analizė {fmtUsd(p.vision)}-{fmtUsd(2 * p.vision)}, restauravimas 1K {fmtUsd(p.image_1k)}{deglareModel ? `, atspindžiai iki ${fmtUsd(p.image_1k)}` : ''}{want4k ? `, 4K ${fmtUsd(p.image_4k)}` : ''}; kompozicija nemokama)</span>
        </p>
        <button type="button" className={GOLD} disabled={!src || running} onClick={() => void run()}>{running && <Spinner />}Paleisti</button>
        {err && stages.length === 0 && <Notice>{err}</Notice>}
      </section>

      {stages.length > 0 && (
        <section ref={progressRef} className={`${CARD} flex flex-col gap-3 scroll-mt-28`}>
          <h3 className="text-sm font-bold">Eiga{total ? ` · iš viso ${fmtSec(total)}` : ''}</h3>
          {err && <Notice>{err}</Notice>}
          {stages.map((s) => (
            <div key={s.key} id={`lab-stage-${s.key}`} className="border-t border-white/5 pt-3 flex flex-col gap-2 min-w-0 scroll-mt-28">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold">{s.label}</p>
                <p className={`text-xs ${TONE[s.status]} flex items-center gap-1.5`}>
                  {s.status === 'run' && <Spinner />}{ICON[s.status]}
                  {s.ms !== undefined ? ` · naršyklėje ${fmtSec(s.ms)}` : ''}{s.serverMs !== undefined ? ` · serveryje ${fmtSec(s.serverMs)}` : ''}
                </p>
              </div>
              {s.note && <p className={`text-xs break-words ${s.status === 'fail' ? 'text-red-200' : 'text-white/75'}`}>{s.note}</p>}
              {s.image && <img src={s.image} alt={s.label} className="w-40 h-40 object-contain rounded-lg border border-white/10 bg-black" />}
              {s.link && <ExtLink href={s.link}>Atidaryti 4K kūrinį</ExtLink>}
              {s.json !== undefined && <JsonView label="Atsakymas (JSON)" value={s.json} />}
            </div>
          ))}
        </section>
      )}

      <section className={`${CARD} flex flex-col gap-3`}>
        <H2 right={<button type="button" className={BTN} onClick={() => void loadLab()}>Atnaujinti</button>}>Testo užsakymai (lab)</H2>
        {labErr && <Notice>{labErr}</Notice>}
        {lab.length === 0 && !labErr && <p className={`text-xs ${MUTED}`}>Testo užsakymų nėra.</p>}
        {lab.map((l) => (
          <div key={l.order} className="border-t border-white/5 pt-3 flex flex-wrap items-start justify-between gap-3">
            <div className="flex flex-wrap gap-3 min-w-0">
              {l.eye_url && <Thumb src={l.eye_url} alt="4K akis" heavy size={96} />}
              {l.artwork_url && <Thumb src={l.artwork_url} alt="4K kūrinys" heavy size={96} />}
              <div className="text-xs min-w-0">
                <a href={`#order/${l.order}`} className="font-semibold break-all underline underline-offset-4 decoration-white/30">{l.order}</a>
                <p className={MUTED}>failų: {l.files}, 4K akių: {l.eyes}</p>
              </div>
            </div>
            <button type="button" className={DANGER} onClick={() => setConfirm({
              title: 'Ištrinti testo užsakymą', danger: true, confirmLabel: 'Ištrinti',
              text: `Ištrinami visi ${l.order} failai.`,
              run: async () => {
                const r = await call<J>('lab_delete', { order: l.order });
                setToast(r.ok ? { tone: 'good', text: `Testo užsakymas ${l.order} ištrintas.` } : { tone: 'bad', text: `${l.order} ištrinti nepavyko: ${explain(r)}` });
                await loadLab();
              },
            })}>Ištrinti</button>
          </div>
        ))}
      </section>
      <StyleLab call={call} lab={lab} />
      <GroupLab call={call} lab={lab} />
      <LabSteps call={call} lab={lab} />
      {toast && <Toast tone={toast.tone} onClose={() => setToast(null)}>{toast.text}</Toast>}
      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
    </div>
  );
};
