// Peržiūros: the kept copies of the free preview (api/_lib/keep.py, the owner's decision of 2026-11-26): by UTC day, each visit (one browser tab on /try)
// with every photo it sent and what the analysis said of it (accepted, or refused and why), the crop and the clean restoration, and the large previews
// it was shown, with the codes the server computed and the anonymous context (campaign, device, browser, language, country). The links are signed for
// ten minutes. A visit's copies can be deleted here (for a person who asks us to; audited). Kept 30 days, then the daily clean-up deletes them.
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { BLOCK_LT, STYLE_LT, VERDICT_LT, explain } from './format';
import { BTN, CARD, ConfirmDialog, DANGER, H2, MUTED, Notice, Spinner, Thumb, type ConfirmSpec } from './ui';
import { BR_LT, CAP_LT, DEV_LT, LANG_LT, campText, label } from './traffic';

export interface KeptStep {
  time: string;
  step: 'analyze' | 'enhance' | 'compose';
  meta: Record<string, unknown> | null;
  /** the step's record exists and could not be read now (not a step that broke off) */
  meta_error?: boolean;
  pictures: Partial<Record<'photo' | 'before' | 'after' | 'art', string>>;
}
export interface KeptVisit { visit: string; steps: KeptStep[] }
/** The kept area against its cap and today's visits against their ceiling (api/_lib/keep.py status). */
export interface KeptArea {
  on?: boolean; area_mb?: number; today_mb?: number; cap_mb?: number; margin_mb?: number; visits_today?: number; visits_day_max?: number;
  held?: 'cap' | 'day' | null; checked?: string | null;
}
export interface KeptReply {
  on: boolean; keep_days: number; days: string[]; day: string | null; visits: KeptVisit[]; total: number; offset: number; more: boolean; area?: KeptArea;
}

/** The line about the kept area: its size against the cap, today's visits against their ceiling, and what holds keeping back now. */
export function areaText(a: KeptArea | undefined): { text: string; held: string | null } {
  if (!a || typeof a.area_mb !== 'number') return { text: 'Saugyklos dydis nežinomas.', held: null };
  const text = `Užimta ${a.area_mb} MB iš ${a.cap_mb} MB (šiandien ${a.today_mb} MB). Šiandien apsilankymų ${a.visits_today} iš ${a.visits_day_max}.`;
  const held = a.held === 'cap' ? `Saugojimas sustabdytas: viršyta riba (${a.cap_mb} MB). Ją didina SNAPEYES_KEEP_MAX_MB.`
    : a.held === 'day' ? `Šiandien daugiau nesaugoma: pasiekta dienos riba (${a.visits_day_max} apsilankymų). Ją didina SNAPEYES_KEEP_VISITS_DAY.` : null;
  return { text, held };
}

const STEP_LT: Record<string, string> = { analyze: 'Nuotrauka', enhance: 'Restauravimas', compose: 'Peržiūra' };
const PIC_LT: Record<string, string> = { photo: 'Atsiųsta nuotrauka', before: 'Iškarpa (prieš)', after: 'Restauruota (po)', art: 'Parodyta peržiūra' };
// the refusal reasons of the analysis (api/analyze.py) in words: the admin's own list, and the two that are not a block
const REASON_LT: Record<string, string> = { ...BLOCK_LT, no_eye: 'Akies nerasta', unlocked: 'Neužfiksuotas rainelės kraštas', too_shaky: 'Sujudinta' };

const str = (v: unknown): string => (typeof v === 'string' ? v : typeof v === 'number' || typeof v === 'boolean' ? String(v) : '');

/** The outcome of one step in words: "Priimta", "Atmesta: Per neryški", "Restauruota", "Parodyta"; null when the step left no record. */
export function outcomeText(s: KeptStep): { text: string; bad: boolean } | null {
  const m = s.meta;
  if (!m) return null;
  const o = str(m.outcome);
  if (o === 'refused') return { text: `Atmesta: ${label(REASON_LT, str(m.reason))}`, bad: true };
  if (o === 'accepted') return { text: `Priimta${m.verdict ? ` (${label(VERDICT_LT, str(m.verdict))})` : ''}`, bad: false };
  if (o === 'restored') return { text: m.gate && m.gate !== 'ok' ? `Restauruota, vartai: ${str(m.gate)}` : 'Restauruota', bad: !!m.gate && m.gate !== 'ok' && m.gate !== 'unknown' };
  if (o === 'shown') return { text: `Parodyta: ${label(STYLE_LT, str(m.style))}`, bad: false };
  if (o === 'failed') return { text: `Nepavyko${m.error ? ` (${str(m.error)})` : ''}`, bad: true };
  return { text: o || '-', bad: false };
}

/** How the photo was taken (api/_lib/events.py CAPTURE), in words: "puslapio kamera, tikra nuotrauka nuo 12 MP, kameros priartinimas, šviesa yra". */
export function capText(c: unknown): string {
  if (!c || typeof c !== 'object') return '';
  const m = c as Record<string, unknown>;
  const w = (k: string) => (typeof m[k] === 'string' ? (CAP_LT[m[k] as string] ?? String(m[k])).toLowerCase() : '');
  return [w('how'), w('lm'), typeof m.lres === 'string' ? String(m.lres) : '', w('zoom'), typeof m.zv === 'string' ? String(m.zv).replace(/^z/, '') + 'x' : '', m.torch ? `šviesa ${w('torch')}` : '', m.dark ? `tamsu ${w('dark')}` : '', m.lfail ? `gyva kamera: ${w('lfail')}` : '']
    .filter(Boolean).join(', ');
}

/** The anonymous context of a step (the same for every step of a visit): campaign, device, browser, language, country. */
export function contextText(s: KeptStep | undefined): string {
  const m = s?.meta ?? {};
  const ctx = (m.ctx && typeof m.ctx === 'object' ? m.ctx : {}) as Record<string, unknown>;
  const camp = campText(['src', 'med', 'cmp', 'trm', 'cnt'].map((k) => str(ctx[k])).join('|').replace(/[|]+$/, ''));
  return [camp, ctx.dev ? label(DEV_LT, str(ctx.dev)) : '', ctx.br ? label(BR_LT, str(ctx.br)) : '', ctx.lang ? label(LANG_LT, str(ctx.lang)) : '', ctx.cc ? str(ctx.cc).toUpperCase() : '']
    .filter(Boolean).join(' · ');
}

/** The codes beside a step, short: the numbers the server measured and, unless the caller shows it once for the whole attempt, the anonymous context. */
export function codesText(s: KeptStep, withContext = true): string {
  const m = s.meta ?? {};
  const parts = [
    m.detail !== undefined ? `detalumas ${str(m.detail)}` : '', m.diameter_px !== undefined ? `rainelė ${str(m.diameter_px)} px` : '',
    m.glare_on_fibres_pct !== undefined ? `atspindys ${str(m.glare_on_fibres_pct)} %` : '', m.lid_wedge_pct ? `vokas ${str(m.lid_wedge_pct)} %` : '',
    m.source ? str(m.source) : '', capText(m.cap), m.qa_ok === false ? 'spalvos patikra nepraėjo' : '', m.retry ? `antras bandymas ${str(m.retry)}` : '',
    m.eyes ? `${str(m.eyes)} ${m.eyes === 1 ? 'akis' : 'akys'}` : '', withContext ? contextText(s) : '',
  ];
  return parts.filter(Boolean).join(' · ');
}

/** A step's time in the browser's own time zone (the folder's day and the file's time are UTC): "12:26:17". */
export function stepTime(day: string | null, t: string): string {
  const utc = `${t.slice(0, 2)}:${t.slice(2, 4)}:${t.slice(4, 6)}`;
  const d = day ? new Date(`${day}T${utc}Z`) : null;
  if (!d || Number.isNaN(d.getTime())) return utc;
  const p = (n: number) => String(n).padStart(2, '0');
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

/** What to say of a step without a record: it could not be read now (try again), or the step broke off before it wrote one. */
export function missingText(s: KeptStep): { text: string; bad: boolean } {
  return s.meta_error ? { text: 'Įrašo nepavyko įkelti: spauskite „Atnaujinti“', bad: false } : { text: 'Nėra rezultato (žingsnis nutrūko)', bad: true };
}

export interface KeptAttempt { n: number; time: string; photos: KeptStep[]; rest: KeptStep[] }
const secs = (t: string) => Number(t.slice(0, 2)) * 3600 + Number(t.slice(2, 4)) * 60 + Number(t.slice(4, 6));
/** A visit's steps (in time order) as attempts, the NEWEST first, like the visits themselves: an attempt is the photos of one go (one tap of the camera or
 *  one pick, sent within ATTEMPT_GAP_S of each other) with the restoration and the previews that followed. A photo after a restoration or a preview,
 *  or after a pause, starts the next attempt. Inside an attempt the order is the order things happened in. (2026-11-26: the owner tried four times in one
 *  tab and read one long list, newest at the bottom, as out of order.) */
export const ATTEMPT_GAP_S = 45;
export function attemptsOf(steps: KeptStep[]): KeptAttempt[] {
  const out: KeptAttempt[] = [];
  let prev: KeptStep | null = null;
  for (const s of steps) {
    const fresh = !prev || (s.step === 'analyze' && (prev.step !== 'analyze' || secs(s.time) - secs(prev.time) > ATTEMPT_GAP_S));
    if (fresh) out.push({ n: out.length + 1, time: s.time, photos: [], rest: [] });
    const a = out[out.length - 1];
    (s.step === 'analyze' ? a.photos : a.rest).push(s);
    prev = s;
  }
  return out.reverse();
}

/** One photo of an attempt, small: the picture, what the analysis said of it, its numbers. */
const PhotoTile: React.FC<{ s: KeptStep }> = ({ s }) => {
  const out = outcomeText(s) ?? missingText(s);
  return (
    <li className="rounded-xl border border-white/10 bg-black/20 p-2 flex flex-col gap-1" style={{ width: 166 }} data-testid="kept-step">
      {s.pictures.photo ? <Thumb src={s.pictures.photo} alt={PIC_LT.photo} size={150} /> : <div className="rounded-lg border border-white/10 bg-black" style={{ width: 150, height: 150 }} />}
      <p className={`text-xs font-semibold ${out.bad ? 'text-red-300' : s.meta ? 'text-emerald-300' : 'text-amber-300'}`}>{out.text}</p>
      <p className={`text-[11px] ${MUTED} break-words`}>{codesText(s, false)}</p>
    </li>
  );
};

const StepRow: React.FC<{ s: KeptStep; day: string | null; withContext?: boolean }> = ({ s, day, withContext = true }) => {
  const out = outcomeText(s) ?? missingText(s);
  const pics = (['photo', 'before', 'after', 'art'] as const).filter((p) => s.pictures[p]);
  return (
    <li className="rounded-xl border border-white/10 bg-black/20 p-3 flex flex-col gap-2" data-testid="kept-step">
      <p className="text-sm flex flex-wrap gap-x-2">
        <span className="font-mono text-white/70">{stepTime(day, s.time)}</span>
        <b>{STEP_LT[s.step] ?? s.step}</b>
        <span className={out.bad ? 'text-red-300' : s.meta ? 'text-emerald-300' : 'text-amber-300'}>{out.text}</span>
      </p>
      {pics.length > 0 && <div className="flex flex-wrap gap-2">{pics.map((p) => <Thumb key={p} src={s.pictures[p]} alt={PIC_LT[p]} size={150} />)}</div>}
      <p className={`text-[11px] ${MUTED} break-words`}>{codesText(s, withContext)}</p>
    </li>
  );
};

/** One attempt of a visit: its number and time, the context once, its photos side by side, then the restoration and the previews. */
const AttemptBlock: React.FC<{ a: KeptAttempt; day: string | null; only: boolean }> = ({ a, day, only }) => {
  const ctx = contextText([...a.photos, ...a.rest].find((s) => s.meta));
  return (
    <div className="flex flex-col gap-2" data-testid="kept-attempt">
      <p className="text-sm flex flex-wrap gap-x-2 items-baseline">
        <b>{only ? 'Bandymas' : `Bandymas ${a.n}`}</b>
        <span className="font-mono text-white/70">{stepTime(day, a.time)}</span>
        {ctx && <span className={`text-[11px] ${MUTED}`}>{ctx}</span>}
      </p>
      {a.photos.length > 0 && <ul className="flex flex-wrap gap-2">{a.photos.map((s, i) => <PhotoTile key={`${s.time}-${i}`} s={s} />)}</ul>}
      {a.rest.length > 0 && <ul className="flex flex-col gap-2">{a.rest.map((s, i) => <StepRow key={`${s.time}-${s.step}-${i}`} s={s} day={day} withContext={false} />)}</ul>}
    </div>
  );
};

export const PreviewsPage: React.FC<{ call: Call }> = ({ call }) => {
  const [day, setDay] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<KeptReply | null>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);
  const [msg, setMsg] = useState<{ tone: 'good' | 'bad'; text: string } | null>(null);

  const load = useCallback(async () => {
    setBusy(true); setErr('');
    const r = await call<KeptReply>('kept', { ...(day ? { day } : {}), offset }, 60_000);
    setBusy(false);
    if (r.ok && r.data) setData(r.data); else setErr(r.error || explain(r));
  }, [call, day, offset]);
  useEffect(() => { void load(); }, [load]);

  const remove = (v: KeptVisit) => setConfirm({
    title: 'Ištrinti šio apsilankymo peržiūras?', text: `${data?.day ?? ''}, ${v.visit}: visos nuotraukos, rezultatai ir įrašai dings visiems laikams. Taip daroma, kai žmogus paprašo ištrinti.`,
    confirmLabel: 'Ištrinti', danger: true,
    run: async () => {
      setMsg(null);
      const r = await call<{ result?: string; deleted?: number }>('kept_delete', { day: data?.day, visit: v.visit, confirm: v.visit });
      if (r.ok) { setMsg({ tone: 'good', text: `Ištrinta: ${r.data?.deleted ?? 0} failų.` }); void load(); } else setMsg({ tone: 'bad', text: r.error || explain(r) });
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} onClick={() => void load()} disabled={busy}>Atnaujinti</button>}>Peržiūros</H2>
      <p className={`text-xs ${MUTED}`}>Kiekviena nemokamos peržiūros nuotrauka ir rezultatas saugomi iki {data?.keep_days ?? 30} dienų (seniausios dienos ištrinamos anksčiau, jei viršijama riba). JAV lankytojų peržiūros nesaugomos. Be vardo, el. pašto ir IP adreso.</p>
      {data && (() => { const a = areaText(data.area); return (
        <div className="flex flex-col gap-1" data-testid="kept-area">
          <p className={`text-xs ${MUTED}`}>{a.text}</p>
          {a.held && <Notice>{a.held}</Notice>}
        </div>
      ); })()}
      {data && !data.on && <Notice>Saugojimas šiame serveryje išjungtas (SNAPEYES_KEEP, nėra saugyklos arba CRON_SECRET): naujos peržiūros nesaugomos.</Notice>}
      {err && <Notice>{err}</Notice>}
      {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}
      {data && data.days.length > 0 && (
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Diena">
          {data.days.map((d) => (
            <button key={d} type="button" aria-pressed={d === data.day} onClick={() => { setDay(d); setOffset(0); }}
              className={`px-2.5 py-1 rounded-lg text-xs border ${d === data.day ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{d}</button>
          ))}
        </div>
      )}
      {busy && !data && <Spinner />}
      {data && data.days.length === 0 && <p className={`text-sm ${MUTED}`}>Dar nėra išsaugotų peržiūrų.</p>}
      {data && data.day && (
        <p className="text-sm">Apsilankymų {data.day}: <b>{data.total}</b>{data.total > data.visits.length ? ` (rodomi ${data.offset + 1} iki ${data.offset + data.visits.length})` : ''}</p>
      )}
      {data?.visits.map((v) => (
        <section key={v.visit} className={`${CARD} flex flex-col gap-2`} data-testid="kept-visit">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-bold font-mono break-all">{v.visit}</h3>
            <button type="button" className={`${DANGER} !min-h-[32px] !px-2`} onClick={() => remove(v)}>Ištrinti</button>
          </div>
          {(() => { const at = attemptsOf(v.steps); return at.map((a, i) => (
            <div key={`${a.n}-${a.time}`} className={i > 0 ? 'border-t border-white/10 pt-3' : ''}><AttemptBlock a={a} day={data.day} only={at.length === 1} /></div>
          )); })()}
        </section>
      ))}
      {data && (data.offset > 0 || data.more) && (
        <div className="flex gap-2">
          <button type="button" className={BTN} disabled={busy || data.offset === 0} onClick={() => setOffset(Math.max(0, data.offset - 12))}>Ankstesni</button>
          <button type="button" className={BTN} disabled={busy || !data.more} onClick={() => setOffset(data.offset + 12)}>Kiti</button>
        </div>
      )}
      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
    </div>
  );
};
