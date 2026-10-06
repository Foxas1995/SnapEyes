// Stiliai: everything the owner sees and controls about the styles (spec 3.3 WP13): the attention card (what crossed a limit he set), the catalogue with the audited switch
// (stage per style and eye count, the checks L0 to L11, the opening criterion beside every count), then the numbers (the set level gate funnel, demand for styles that cannot be
// bought yet, recommended against chosen, previews, the funnel after the preview, the restoration gate, fallbacks, render times against the estimate, errors and review, Reveal)
// with a period, one filter at a time (a market or a language), and the audit log of the switch. The server decides and counts (api/_lib/ops.py, style_stats.py,
// stage_overrides.py); this page asks, shows with the n behind every share, and sends the owner's confirmed changes. Lithuanian only; codes and counts, never a customer's words.
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import type { Reply, StyleAuditEntry, StyleCatalogue, StyleChange, StyleLimits, StylesStats } from './api';
import type { Call } from './AdminApp';
import { explain, fmtTime, STYLE_LT } from './format';
import { StyleCard } from './StyleSwitch';
import type { SwitchNote } from './StyleSwitch';
import {
  ChosenBlock, ConversionBlock, DemandBlock, ErrorsBlock, FallbackBlock, FunnelBlock, GateBlock, RevealBlock, TimesBlock,
} from './StyleNumbers';
import {
  attentionText, auditNumbers, auditText, eyesRangeText, failText, filterBody, fixedIds, fmtPct, groupedStyles, heldText, HEALTH_LT, REASON_KIND_LT, SLICE_LANG_LT, SLICE_MARKET_LT, stageLt,
} from './stylesView';
import { BTN, CARD, Chip, ConfirmDialog, GOLD, H2, INPUT, MUTED, Notice, Spinner, Toast, ToneLine } from './ui';
import type { ConfirmSpec } from './ui';

const PERIODS: [number, string][] = [[7, '7 d.'], [30, '30 d.'], [90, '90 d.']];
const nameOf = (id: string): string => STYLE_LT[id] || id;

const LimitsForm: React.FC<{ cat: StyleCatalogue; call: Call; setConfirm: (c: ConfirmSpec | null) => void; report: (n: SwitchNote | null) => void; onSaved: (l: StyleLimits, rev: number) => void }> = ({ cat, call, setConfirm, report, onSaved }) => {
  const L = cat.limits;
  const pct = (v: number) => String(Math.round(v * 1000) / 10).replace('.', ',');
  const [f, setF] = useState({ min_n: String(L.min_n), error_rate: pct(L.error_rate), review_rate: pct(L.review_rate), gate_fail_rate: pct(L.gate_fail_rate) });
  const [problem, setProblem] = useState('');
  const num = (t: string) => Number(t.trim().replace(',', '.'));
  const submit = () => {
    const min_n = num(f.min_n);
    const shares = [num(f.error_rate), num(f.review_rate), num(f.gate_fail_rate)];
    if (!Number.isInteger(min_n) || min_n < 0 || min_n > 10000 || shares.some((v) => !Number.isFinite(v) || v < 0 || v > 100)) {
      setProblem('Mažiausias n yra sveikas skaičius nuo 0 iki 10 000, dalys yra procentai nuo 0 iki 100.');
      return;
    }
    setProblem('');
    const limits = { min_n, error_rate: Math.round(shares[0] * 10) / 1000, review_rate: Math.round(shares[1] * 10) / 1000, gate_fail_rate: Math.round(shares[2] * 10) / 1000 };
    setConfirm({
      title: 'Pakeisti dėmesio kortelės ribas', confirmLabel: 'Pakeisti',
      text: `Dėmesio kortelė rodys stilių, kurio klaidų dalis viršija ${f.error_rate} %, laukiančių peržiūros kūrinių dalis ${f.review_rate} %, nepraėjusių vartų akių dalis ${f.gate_fail_rate} %, kai už dalies yra bent ${min_n} įvykių. Pakeitimas įrašomas į žurnalą.`,
      run: async () => {
        const r = await call<{ limits: StyleLimits; rev: number }>('styles_limits', { limits, confirm: true, rev: cat.rev });
        if (r.ok && r.data) { onSaved(r.data.limits, r.data.rev); report({ tone: 'good', text: 'Ribos pakeistos.' }); } else report({ tone: 'bad', text: failText(r) });
      },
    });
  };
  const field = (k: keyof typeof f, label: string) => (
    <label className="flex flex-col gap-1 text-xs"><span className={MUTED}>{label}</span>
      <input className={INPUT} inputMode="decimal" value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} aria-label={label} /></label>
  );
  return (
    <details className="rounded-xl border border-white/10 bg-black/20">
      <summary className="cursor-pointer select-none px-3 py-2 text-xs font-semibold">Dėmesio kortelės ribos: n bent {L.min_n}, klaidos {fmtPct(L.error_rate)}, peržiūra {fmtPct(L.review_rate)}, vartai {fmtPct(L.gate_fail_rate)}</summary>
      <div className="p-3 flex flex-col gap-3">
        <div className="grid gap-2 sm:grid-cols-4">
          {field('min_n', 'Mažiausias n')}
          {field('error_rate', 'Klaidų dalis, %')}
          {field('review_rate', 'Laukiančių peržiūros dalis, %')}
          {field('gate_fail_rate', 'Nepraėjusių vartų dalis, %')}
        </div>
        {problem && <Notice>{problem}</Notice>}
        <div><button type="button" className={BTN} onClick={submit}>Keisti ribas</button></div>
      </div>
    </details>
  );
};

const Audit: React.FC<{ entries: StyleAuditEntry[] | null }> = ({ entries }) => (
  <section className={`${CARD} flex flex-col gap-2`} aria-label="Perjungiklio žurnalas">
    <h3 className="text-sm font-bold">Perjungiklio žurnalas (naujausi viršuje)</h3>
    <p className={`text-xs ${MUTED}`}>Kiekvienas pakeitimas: kas, ką, kodėl, kokie buvo rinkinių skaičiai tą akimirką (su n), ar veikė kainų testas ir ką pasirinkai gaminamiems užsakymams.</p>
    {entries === null && <p className={`text-xs ${MUTED}`}>Žurnalas kraunamas.</p>}
    {entries && entries.length === 0 && <p className={`text-xs ${MUTED}`}>Pakeitimų dar nebuvo.</p>}
    <ul className="flex flex-col">
      {(entries || []).map((e, i) => (
        <li key={`${e.t}-${i}`} className="border-t border-white/5 py-2 text-xs flex flex-col gap-0.5 min-w-0">
          <p className="break-words"><span className="text-white/60">{fmtTime(e.t, true)}</span> · <b>{auditText(e)}</b></p>
          {e.reason && <p className="text-white/70 break-words">Priežastis{e.reason_kind ? ` (${REASON_KIND_LT[e.reason_kind] || e.reason_kind})` : ''}: {e.reason}</p>}
          {auditNumbers(e).length > 2 ? (
            <details className="text-white/60"><summary className="cursor-pointer select-none">Skaičiai tą akimirką ({auditNumbers(e).length} akių skaičiai)</summary>
              {auditNumbers(e).map((t) => <p key={t} className="break-words">{t}</p>)}</details>
          ) : auditNumbers(e).map((t) => <p key={t} className="text-white/60 break-words">Skaičiai: {t}</p>)}
          {e.price_test && e.price_test.length > 0 && <p className="text-amber-200 break-words">Veikė kainų testas ({e.price_test.join(', ')}){e.price_test_seen ? ': perskaitei, kad pakeitimas keičia jo imtį' : ''}.</p>}
          {e.in_flight && <p className="text-white/60">Gaminami užsakymai: {e.in_flight === 'hold' ? 'sulaikyti' : 'baigiami kaip įprasta'}. {e.held ? heldText(e.held) : ''}</p>}
        </li>
      ))}
    </ul>
  </section>
);

export const StylesPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [filter, setFilter] = useState('');
  const [cat, setCat] = useState<StyleCatalogue | null>(null);
  const [stats, setStats] = useState<StylesStats | null>(null);
  const [audit, setAudit] = useState<StyleAuditEntry[] | null>(null);
  const [err, setErr] = useState<string[]>([]);
  const [busy, setBusy] = useState(true);
  const [note, setNote] = useState<SwitchNote | null>(null);
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);
  const [retrying, setRetrying] = useState(false);

  const apply = useCallback(([c, s, a]: [Reply<StyleCatalogue>, Reply<StylesStats>, Reply<{ entries: StyleAuditEntry[] }>]) => {
    const e: string[] = [];
    if (c.ok && c.data) setCat(c.data); else e.push(`Katalogas: ${explain(c)}`);
    if (s.ok && s.data) setStats(s.data); else e.push(`Skaičiai: ${explain(s)}`);
    if (a.ok && a.data) setAudit(a.data.entries); else e.push(`Žurnalas: ${explain(a)}`);
    setErr(e); setBusy(false);
  }, []);

  const fetchAll = useCallback((d: number, f: string) => Promise.all([
    call<StyleCatalogue>('styles_catalogue'), call<StylesStats>('styles_stats', { days: d, ...filterBody(f) }, 90_000), call<{ entries: StyleAuditEntry[] }>('styles_audit', { limit: 60 }),
  ]), [call]);

  useEffect(() => {
    let live = true;
    void fetchAll(30, '').then((x) => { if (live) apply(x); });
    return () => { live = false; };
  }, [fetchAll, apply]);

  const reload = useCallback(async () => { setBusy(true); apply(await fetchAll(days, filter)); }, [fetchAll, apply, days, filter]);

  const loadStats = async (d: number, f: string) => {
    setBusy(true);
    const r = await call<StylesStats>('styles_stats', { days: d, ...filterBody(f) }, 90_000);
    setBusy(false);
    if (r.ok && r.data) { setStats(r.data); setErr((cur) => cur.filter((x) => !x.startsWith('Skaičiai'))); } else setErr((cur) => [...cur.filter((x) => !x.startsWith('Skaičiai')), `Skaičiai: ${explain(r)}`]);
  };

  // a plain success closes itself after a while; a warning, a failure or a retry stays until closed
  useEffect(() => {
    if (!note || note.tone !== 'good') return;
    const t = setTimeout(() => setNote((cur) => (cur === note ? null : cur)), 12000);
    return () => clearTimeout(t);
  }, [note]);

  const onChanged = (c: StyleChange) => {
    setCat((cur) => (cur ? { ...cur, rev: c.rev, styles: cur.styles.map((s) => (s.id === c.style ? c.view : s)) } : cur));
    void call<{ entries: StyleAuditEntry[] }>('styles_audit', { limit: 60 }).then((a) => { if (a.ok && a.data) setAudit(a.data.entries); });
  };

  const retry = async (body: Record<string, unknown>) => {
    setRetrying(true);
    const r = await call<StyleChange>('styles_override', body, 60_000);
    setRetrying(false);
    if (r.ok && r.data) {
      onChanged(r.data);
      setNote({ tone: r.data.held && r.data.held.incomplete ? 'warn' : 'good', text: `Sulaikymas pakartotas. ${heldText(r.data.held)}${r.data.held && r.data.held.incomplete ? ' Dar ne viskas: gali pakartoti dar kartą.' : ''}`,
        retry: r.data.held && r.data.held.incomplete ? { ...body, rev: r.data.rev } : undefined });
    } else setNote({ tone: 'bad', text: failText(r) });
  };

  const groups = groupedStyles(cat);
  const priceTest = cat?.price_test || [];
  const slice = stats?.filter.slice || '';
  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} onClick={() => void reload()} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>}>Stiliai</H2>
      {err.map((e, i) => <Notice key={i}>{e}</Notice>)}

      <section className={`${CARD} flex flex-col gap-2`} aria-label="Kaip tai veikia">
        <h3 className="text-sm font-bold">Kaip čia viskas veikia</h3>
        <p className={`text-xs ${MUTED}`}>
          Kiekvieno stiliaus „registro riba“ yra kodas: aukščiau jos šis puslapis stiliaus pakelti negali, tik peržiūrėtas kodo pakeitimas. „Dabar galioja“ yra žemesnė iš registro ribos ir tavo paties ribos. Stilius tampa
          „Parduodamas“ tik kai pažymi savo žvilgsnį į galutinius kūrinius (L1) ir nepriklausomą vertinimą (L0) arba rašytinį atsisakymą jo. Užsakymų priėmimas atidaromas atskirai.
        </p>
        {cat && (
          <div className="flex flex-wrap gap-1.5 items-center">
            <Chip tone={cat.ordering_open ? 'good' : 'warn'}>užsakymų priėmimas: {cat.ordering_open ? 'atidarytas' : 'uždarytas'}</Chip>
            <Chip>iš viso parduodama iki {cat.orderable_max_eyes} akių</Chip>
            <Chip>pradinė būsena be tavo ribos: {cat.default_effective || 'registro riba'}</Chip>
            <span className="text-[11px] text-white/45">registro santrauka {cat.registry_hash}</span>
          </div>
        )}
        {priceTest.length > 0 && (
          <ToneLine tone="warn">Veikia kainų testas ({priceTest.join(', ')}): kiekvienas pakeitimas, keičiantis kas perkama, keičia jo imtį. Jis bus įrašytas ir to testo puslapyje, o patvirtinimo lange tai pasakoma.</ToneLine>
        )}
      </section>

      <section className={`${CARD} flex flex-col gap-3`} aria-label="Dėmesio kortelė">
        <h3 className="text-sm font-bold">Dėmesio kortelė</h3>
        {!stats && busy && <p className="flex items-center gap-2 text-sm"><Spinner />Kraunama...</p>}
        {stats && stats.attention.length === 0 && (
          <ToneLine tone="good">Nei vienas stilius nekirto tavo ribų ({days} d.), sveikatos patikra praėjo, sulaikytų dėl stiliaus užsakymų nėra.</ToneLine>
        )}
        <ul className="flex flex-col gap-1.5">
          {(stats?.attention || []).map((a, i) => (
            <li key={i}>
              <ToneLine tone={a.kind === 'health' || a.kind === 'hold' ? 'bad' : 'warn'}>
                {attentionText(a, nameOf)}{a.kind === 'hold' && <> <a href="#orders" className="underline underline-offset-4">Atidaryti užsakymų sąrašą</a></>}
              </ToneLine>
            </li>
          ))}
        </ul>
        {stats?.health && (
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(stats.health).map(([k, ok]) => <Chip key={k} tone={ok ? 'good' : 'bad'}>{HEALTH_LT[k] || k}: {ok ? 'gerai' : 'nepraėjo'}</Chip>)}
          </div>
        )}
        {cat && <LimitsForm key={cat.rev} cat={cat} call={call} setConfirm={setConfirm} report={setNote}
          onSaved={(l, rev) => { setCat((cur) => (cur ? { ...cur, limits: l, rev } : cur)); void loadStats(days, filter); }} />}
      </section>

      <section className="flex flex-col gap-3" aria-label="Katalogas ir perjungiklis">
        <h3 className="text-base font-bold">Katalogas ir perjungiklis</h3>
        {!cat && busy && <p className="flex items-center gap-2 text-sm"><Spinner />Kraunama...</p>}
        {cat && groups.map((g) => (
          <div key={g.group} className="flex flex-col gap-3">
            <h4 className="text-sm font-semibold text-white/80 border-b border-white/10 pb-1">{g.label}</h4>
            {g.rows.map((row) => (
              <StyleCard key={row.id} row={row} ctx={{ call, cat, stats, onChanged, setConfirm, report: setNote, reload: () => void reload() }} />
            ))}
            {g.fixed.length > 0 && (
              <p className={`text-xs ${MUTED} break-words`}>
                Suplanuoti arba išjungti, perjungti negalima ({g.fixed.map((r) => `${r.name}, ${eyesRangeText(r.eyes)}: ${stageLt(r.ranges[0]?.ceiling)}`).join('; ')}). Tai registro, ne šio puslapio pakeitimas.
              </p>
            )}
          </div>
        ))}
        {cat && cat.styles.some((s) => s.legacy) && (
          <p className={`text-xs ${MUTED}`}>Seni šeši stiliai ({cat.styles.filter((s) => s.legacy).map((s) => s.name).join(', ')}) išjungti ir jų perjungti negalima: jie piešiami tik jau apmokėtiems senesniems užsakymams.</p>
        )}
      </section>

      <section className={`${CARD} flex flex-col gap-3`} aria-label="Laikotarpis ir filtras">
        <h3 className="text-sm font-bold">Skaičiai</h3>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Laikotarpis">
            {PERIODS.map(([d, l]) => (
              <button key={d} type="button" aria-pressed={days === d} onClick={() => { setDays(d); void loadStats(d, filter); }}
                className={`px-3 py-1.5 rounded-lg text-sm border ${days === d ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{l}</button>
            ))}
          </div>
          <label className="flex items-center gap-2 text-sm">
            <span className={MUTED}>Filtras</span>
            <select className={`${INPUT} !w-auto`} value={filter} aria-label="Rinkos ar kalbos filtras" onChange={(e) => { setFilter(e.target.value); void loadStats(days, e.target.value); }}>
              <option value="">Visos rinkos ir kalbos</option>
              <optgroup label="Rinka">{Object.entries(SLICE_MARKET_LT).map(([k, v]) => <option key={k} value={`market:${k}`}>{v}</option>)}</optgroup>
              <optgroup label="Kalba">{Object.entries(SLICE_LANG_LT).map(([k, v]) => <option key={k} value={`lang:${k}`}>{v}</option>)}</optgroup>
            </select>
          </label>
        </div>
        <p className={`text-xs ${MUTED}`}>
          Vienu metu vienas filtras. Filtras taikomas rinkinių piltuvui, paklausai, peržiūroms ir atsarginiams variantams; kitos lentelės (vartai, laikai, klaidos, apmokėjimai) filtro neturi ir pažymėtos „visi duomenys“.
          Kainų testo šakos filtro čia nėra: šakų piltuvai yra puslapyje „Kainų testai“. Dienos skaičiuojamos pagal UTC.
          {stats?.partial ? ' Dalis dienų dar skaičiuojama: atnaujink po minutės.' : ''}
          {stats && !stats.recording ? ' Šiame serveryje įvykiai nerenkami (nėra CRON_SECRET), todėl skaičiai tušti.' : ''}
          {slice ? ` Dabar rodoma: ${slice.startsWith('market:') ? `rinka ${SLICE_MARKET_LT[slice.slice(7)] || slice.slice(7)}` : `kalba ${SLICE_LANG_LT[slice.slice(5)] || slice.slice(5)}`}.` : ''}
        </p>
      </section>

      {stats && (
        <>
          <FunnelBlock s={stats} />
          <DemandBlock s={stats} />
          <ChosenBlock s={stats} cat={cat} />
          <ConversionBlock s={stats} />
          <GateBlock s={stats} skip={fixedIds(cat)} />
          <FallbackBlock s={stats} />
          <TimesBlock s={stats} />
          <ErrorsBlock s={stats} />
          <RevealBlock s={stats} />
        </>
      )}
      <Audit entries={audit} />

      {note && (
        <Toast tone={note.tone} onClose={() => setNote(null)}>
          <p>{note.text}</p>
          {note.retry && (
            <div className="mt-2"><button type="button" className={GOLD} disabled={retrying} onClick={() => void retry(note.retry!)}>{retrying && <Spinner />}Pakartoti sulaikymą</button></div>
          )}
        </Toast>
      )}
      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
    </div>
  );
};
