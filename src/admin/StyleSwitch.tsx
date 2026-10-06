// The catalogue and its switch on the Stiliai page: one card per style, one row per range of eye counts that read the same (the ceiling the registry's code sets, the owner's own limit, the
// stage that holds now, the checks L0 to L11 with who ticked them and when, the independent score or the written waiver of L0), and a panel to change one range. A change is a request of
// styles_override (api/_lib/ops.py): the page sends the revision it was drawn from (a second tab's change is a 409, not a silent overwrite), asks for confirmation first (the dialog says
// what changes, that a price test is running when one is, and what happens to the paid orders in flight when an orderable style is taken back), and shows what the server did: the
// stage that holds, the orders held, a hold that stopped half way (with the button that sends it again) and a log line that could not be written. The page decides nothing: the ceiling,
// the ticks and the refusals are the server's.
import { useState } from 'react';
import type React from 'react';
import type { StyleCatalogue, StyleChange, StyleRange, StyleRow } from './api';
import type { Call } from './AdminApp';
import type { OpeningBasis } from './stylesLoad';
import { fmtTime } from './format';
import {
  allowedStages, buildChange, changeNote, changeSummary, checkName, CHECK_LT, dec, eyesRangeText, failText, GATE_POLICY_LT, initialPanel, l0Text, L0_TONE, OPENING_BASIS_LT, openingBasisView, openingView, PRICE_CLASS_LT,
  rangeCounts, REASON_KIND_LT, STAGE_ABOUT_LT, STAGE_TONE, stageLt, type PanelState,
} from './stylesView';
import { BTN, CARD, GOLD, INPUT, MUTED, Notice, Rows, ToneLine, WrapChip } from './ui';
import type { ConfirmSpec, Tone } from './ui';

export interface SwitchNote { tone: Tone; text: string; retry?: Record<string, unknown> }
export interface SwitchCtx {
  call: Call;
  cat: StyleCatalogue;
  basis: OpeningBasis;
  onChanged: (c: StyleChange) => void;
  setConfirm: (c: ConfirmSpec | null) => void;
  report: (n: SwitchNote | null) => void;
  reload: () => void;
}

const isoOf = (s: string | null | undefined): string => {
  const t = s ? Date.parse(s) / 1000 : NaN;
  return Number.isFinite(t) ? fmtTime(t) : s || '-';
};

const Mark: React.FC<{ code: string; range: StyleRange }> = ({ code, range }) => {
  const m = range.checklist[code];
  return m ? <>pažymėta {isoOf(m.ticked_at)}{m.by ? `, ${m.by}` : ''}</> : <span className={MUTED}>nepažymėta</span>;
};

const L0Line: React.FC<{ range: StyleRange }> = ({ range }) => {
  const m = range.checklist.L0;
  const sc = m?.score;
  return (
    <p className="text-xs break-words">
      <b>L0 nepriklausomas vertinimas: </b>
      <WrapChip tone={L0_TONE[range.l0 || ''] || 'muted'}>{l0Text(range.l0)}</WrapChip>
      {sc && (sc.mean !== undefined || sc.min_axis !== undefined) && (
        <span className={MUTED}> vidurkis {dec(sc.mean)}, silpniausia ašis {dec(sc.min_axis)}{m?.director ? `, vertino ${m.director}` : ''}, {isoOf(m?.ticked_at)}</span>
      )}
      {range.waiver && <span className={MUTED}> · tavo atsisakymas ({isoOf(range.waiver.at)}): {range.waiver.text}</span>}
    </p>
  );
};

/** The opening criterion beside the count's switch: one green or red line per count of two or more eyes, the numbers with n, and each line says what it was counted over (the last 30
 *  days, the whole market: what the audit entry of a change keeps), not the period or filter of the numbers below. */
export const OpeningLines: React.FC<{ range: StyleRange; basis: OpeningBasis }> = ({ range, basis }) => {
  const counts = rangeCounts(range.eyes).filter((n) => n >= 2);
  if (!counts.length) return null;
  if (basis === 'failed') return <p className={`text-xs ${MUTED}`}>Atidarymo kriterijaus skaičių ({OPENING_BASIS_LT}) perskaityti nepavyko: paspausk „Atnaujinti“.</p>;
  if (!basis) return <p className={`text-xs ${MUTED}`}>Atidarymo kriterijaus skaičiai kraunami.</p>;
  if (counts.length === 1) {
    const v = openingBasisView(counts[0], basis.opening[String(counts[0])], basis.partial);
    return <ToneLine tone={v.tone}>{eyesRangeText([counts[0], counts[0]])}: {v.text}</ToneLine>;
  }
  // several counts share one fold: its heading names the basis once, so the lines inside do not repeat it
  const lines = counts.map((n) => ({ n, v: openingView(n, basis.opening[String(n)]) }));
  const green = lines.filter((l) => l.v.tone === 'good').length;
  return (
    <details className="rounded-lg border border-white/10 bg-black/20">
      <summary className="cursor-pointer select-none px-2.5 py-1.5 text-xs font-semibold">
        Atidarymo kriterijus pagal akių skaičių ({OPENING_BASIS_LT}{basis.partial ? ', dalis dienų dar neperskaityta' : ''}): įvykdytas {green} iš {lines.length}
      </summary>
      <div className="flex flex-col gap-1.5 p-2">
        {lines.map((l) => <ToneLine key={l.n} tone={l.v.tone}>{eyesRangeText([l.n, l.n])}: {l.v.text}</ToneLine>)}
      </div>
    </details>
  );
};

export const RangePanel: React.FC<{ row: StyleRow; range: StyleRange; ctx: SwitchCtx; onClose: () => void }> = ({ row, range, ctx, onClose }) => {
  const [p, setP] = useState<PanelState>(() => initialPanel(range));
  const [problems, setProblems] = useState<string[]>([]);
  const set = (patch: Partial<PanelState>) => setP((cur) => ({ ...cur, ...patch }));
  const stages = allowedStages(range);
  const priceTest = ctx.cat.price_test;
  const live = buildChange(row.id, range, p, ctx.cat.rev, priceTest, ctx.cat.default_effective);
  const opts: [PanelState['stage'], string][] = [
    ['', 'Etapo nekeisti (tik žymos ar vertinimas)'],
    ...stages.map((s) => [s as PanelState['stage'], `${stageLt(s)}: ${STAGE_ABOUT_LT[s]}`] as [PanelState['stage'], string]),
    ['restore', `Atstatyti pradinę būseną: ${STAGE_ABOUT_LT.restore}`],
  ];
  const id = `${row.id}-${range.eyes.join('-')}`;

  const submit = () => {
    const b = buildChange(row.id, range, p, ctx.cat.rev, priceTest, ctx.cat.default_effective);
    setProblems(b.problems);
    if (!b.body) return;
    const body = b.body;
    ctx.setConfirm({
      title: p.stage ? 'Keisti stiliaus būseną' : 'Įrašyti žymas',
      text: changeSummary(row, range, p, b, priceTest, ctx.cat.default_effective, ctx.cat.l0_bar),
      confirmLabel: p.stage ? 'Patvirtinti pakeitimą' : 'Įrašyti',
      danger: b.lowersOrderable,
      run: async () => {
        const r = await ctx.call<StyleChange>('styles_override', body, 60_000);
        if (r.ok && r.data) {
          ctx.onChanged(r.data);
          ctx.report(changeNote(r.data, body));
          onClose();
        } else {
          ctx.report({ tone: 'bad', text: failText(r) });
          if (r.reason === 'stale_view') ctx.reload();
        }
      },
    });
  };

  return (
    <div className="rounded-xl border border-[#f5c542]/30 bg-black/25 p-3 sm:p-4 flex flex-col gap-4" role="group" aria-label={`Keisti: ${row.name}, ${eyesRangeText(range.eyes)}`}>
      {range.eyes[0] !== range.eyes[1] && (
        <fieldset className="flex flex-col gap-1.5">
          <legend className="text-xs font-bold mb-1">Akių skaičius, kuriam keičiama</legend>
          <div className="flex flex-wrap gap-1.5">
            {rangeCounts(range.eyes).map((n) => (
              <button key={n} type="button" aria-pressed={p.counts.includes(n)} onClick={() => set({ counts: p.counts.includes(n) ? p.counts.filter((x) => x !== n) : [...p.counts, n].sort((a, b) => a - b) })}
                className={`px-3 py-1.5 rounded-lg text-sm border ${p.counts.includes(n) ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{n}</button>
            ))}
          </div>
        </fieldset>
      )}

      <fieldset className="flex flex-col gap-1.5">
        <legend className="text-xs font-bold mb-1">Etapas (registro riba: {stageLt(range.ceiling)})</legend>
        {opts.map(([v, label]) => (
          <label key={v || 'none'} className="flex items-start gap-2 text-sm">
            <input type="radio" name={`stage-${id}`} className="mt-1 accent-[#f5c542]" checked={p.stage === v} onChange={() => set({ stage: v })} />
            <span className="min-w-0 break-words">{label}</span>
          </label>
        ))}
        {!stages.includes('live') && <p className={`text-xs ${MUTED}`}>„Parduodamas“ pasirinkti negalima: registro riba žemesnė, ją gali pakelti tik peržiūrėtas kodo pakeitimas.</p>}
      </fieldset>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-xs font-bold mb-1">Patikros prieš „Parduodamas“ (kiekviena datuojama ir tavo vardu)</legend>
        <div className="rounded-lg border border-white/10 p-2.5 flex flex-col gap-2">
          <p className="text-sm font-semibold">{CHECK_LT.L0.name}</p>
          <p className={`text-xs ${MUTED}`}>{CHECK_LT.L0.hint}</p>
          <L0Line range={range} />
          <div className="grid gap-2 sm:grid-cols-3">
            <label className="flex flex-col gap-1 text-xs"><span className={MUTED}>Vidurkis (0 iki 5)</span>
              <input className={INPUT} inputMode="decimal" value={p.l0.mean} onChange={(e) => set({ l0: { ...p.l0, mean: e.target.value } })} aria-label="L0 vidurkis" /></label>
            <label className="flex flex-col gap-1 text-xs"><span className={MUTED}>Silpniausia ašis (0 iki 5)</span>
              <input className={INPUT} inputMode="decimal" value={p.l0.axis} onChange={(e) => set({ l0: { ...p.l0, axis: e.target.value } })} aria-label="L0 silpniausia ašis" /></label>
            <label className="flex flex-col gap-1 text-xs"><span className={MUTED}>Vertino (vardas)</span>
              <input className={INPUT} maxLength={80} value={p.l0.by} onChange={(e) => set({ l0: { ...p.l0, by: e.target.value } })} aria-label="L0 vertintojas" /></label>
          </div>
          <label className="flex flex-col gap-1 text-xs"><span className={MUTED}>Arba tavo rašytinis atsisakymas L0 (tavo žodžiais, 8 iki 300 ženklų)</span>
            <textarea className={`${INPUT} min-h-[64px]`} maxLength={300} value={p.waiver} onChange={(e) => set({ waiver: e.target.value, removeWaiver: false })} aria-label="L0 atsisakymas" /></label>
          {range.waiver && (
            <label className="flex items-center gap-2 text-xs">
              <input type="checkbox" className="accent-[#f5c542]" checked={p.removeWaiver} disabled={!!p.waiver.trim()} onChange={(e) => set({ removeWaiver: e.target.checked })} />
              Pašalinti esamą atsisakymą
            </label>
          )}
        </div>
        {ctx.cat.checks.filter((c) => c !== 'L0').map((c) => (
          <label key={c} className="flex items-start gap-2 text-sm">
            <input type="checkbox" className="w-4 h-4 mt-1 accent-[#f5c542]" checked={!!p.ticks[c]} onChange={(e) => set({ ticks: { ...p.ticks, [c]: e.target.checked } })} />
            <span className="min-w-0">
              <span className="font-semibold break-words">{CHECK_LT[c]?.name || c}</span>
              <span className={`block text-xs ${MUTED} break-words`}>{CHECK_LT[c]?.hint}</span>
              <span className="block text-xs text-white/65"><Mark code={c} range={range} /></span>
            </span>
          </label>
        ))}
      </fieldset>

      {live.lowersOrderable && (
        <fieldset className="flex flex-col gap-1.5">
          <legend className="text-xs font-bold mb-1">Jau apmokėti užsakymai, kurie dar gaminami šiuo stiliumi</legend>
          {([['', 'Pagal priežastį: kokybė sulaiko, kita baigia kaip įprasta'], ['finish', 'Baigti kaip įprasta'], ['hold', 'Sulaikyti ir peržiūrėti pačiam']] as const).map(([v, label]) => (
            <label key={v || 'auto'} className="flex items-start gap-2 text-sm">
              <input type="radio" name={`flight-${id}`} className="mt-1 accent-[#f5c542]" checked={p.inFlight === v} onChange={() => set({ inFlight: v })} />
              <span className="min-w-0 break-words">{label}</span>
            </label>
          ))}
        </fieldset>
      )}

      {(p.stage !== '' || live.lowersOrderable) && (
        <div className="grid gap-2 sm:grid-cols-[1fr_12rem]">
          <label className="flex flex-col gap-1 text-xs"><span className={MUTED}>Priežastis (nebūtina, iki 200 ženklų)</span>
            <input className={INPUT} maxLength={200} value={p.reason} onChange={(e) => set({ reason: e.target.value })} aria-label="Priežastis" /></label>
          <label className="flex flex-col gap-1 text-xs"><span className={MUTED}>Rūšis</span>
            <select className={INPUT} value={p.reasonKind} onChange={(e) => set({ reasonKind: e.target.value })} aria-label="Priežasties rūšis">
              {Object.entries(REASON_KIND_LT).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select></label>
        </div>
      )}

      {live.flips && priceTest.length > 0 && (
        <ToneLine tone="warn">Veikia kainų testas ({priceTest.join(', ')}): šis pakeitimas keičia jo imtį. Pakeitimas bus įrašytas ir to testo puslapyje.</ToneLine>
      )}
      {problems.length > 0 && <Notice>{problems.join(' ')}</Notice>}
      <div className="flex flex-wrap gap-2">
        <button type="button" className={GOLD} onClick={submit}>Peržiūrėti ir patvirtinti</button>
        <button type="button" className={BTN} onClick={onClose}>Uždaryti</button>
      </div>
    </div>
  );
};

const RangeRow: React.FC<{ row: StyleRow; range: StyleRange; ctx: SwitchCtx; open: boolean; onToggle: () => void }> = ({ row, range, ctx, open, onToggle }) => (
  <div className="border-t border-white/5 pt-3 flex flex-col gap-2">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex flex-wrap items-center gap-1.5 min-w-0">
        <p className="text-sm font-bold mr-1">{eyesRangeText(range.eyes)}</p>
        <WrapChip>registro riba: {stageLt(range.ceiling)}</WrapChip>
        <WrapChip>mano riba: {range.override ? stageLt(range.override) : 'nėra'}</WrapChip>
        <WrapChip tone={STAGE_TONE[range.effective || ''] || 'muted'}>dabar galioja: {stageLt(range.effective)}</WrapChip>
        {range.orderable ? <WrapChip tone="good">perkamas</WrapChip> : <WrapChip tone="muted">neperkamas</WrapChip>}
        {!row.built && <WrapChip tone="warn">variklio šiame serveryje nėra</WrapChip>}
      </div>
      <button type="button" className={BTN} disabled={!range.switchable} aria-expanded={open} onClick={onToggle}>{open ? 'Uždaryti' : 'Keisti'}</button>
    </div>
    {!range.switchable && <p className={`text-xs ${MUTED}`}>Perjungti negalima: stilius suplanuotas arba išjungtas. Tai registro, ne šio puslapio pakeitimas.</p>}
    <L0Line range={range} />
    <p className="text-xs"><b>L1 tavo žvilgsnis į galutinius kūrinius: </b><Mark code="L1" range={range} /></p>
    {range.effective !== 'live' && range.missing_for_live.length > 0 && range.switchable && (
      <p className={`text-xs ${MUTED}`}>Kad taptų „Parduodamas“, dar trūksta: {range.missing_for_live.map(checkName).join('; ')}.</p>
    )}
    <OpeningLines range={range} basis={ctx.basis} />
    {open && <RangePanel key={`${range.eyes.join('-')}-${ctx.cat.rev}`} row={row} range={range} ctx={ctx} onClose={onToggle} />}
  </div>
);

export const StyleCard: React.FC<{ row: StyleRow; ctx: SwitchCtx }> = ({ row, ctx }) => {
  const [open, setOpen] = useState<number | null>(null);
  const last = row.last;
  return (
    <section className={`${CARD} flex flex-col gap-3`} aria-label={`${row.name}, ${eyesRangeText(row.eyes)}`}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h4 className="text-base font-bold">{row.name}</h4>
        <p className="text-xs text-white/50"><code>{row.id}</code></p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        <WrapChip>{eyesRangeText(row.eyes)}</WrapChip>
        <WrapChip>{GATE_POLICY_LT[row.gate] || row.gate}</WrapChip>
        <WrapChip>{PRICE_CLASS_LT[row.price_class] || row.price_class}</WrapChip>
      </div>
      {row.ranges.map((rg, i) => (
        <RangeRow key={rg.eyes.join('-')} row={row} range={rg} ctx={ctx} open={open === i} onToggle={() => setOpen(open === i ? null : i)} />
      ))}
      {last && (last.at || last.by) && (
        <Rows rows={[['Paskutinis pakeitimas', `${isoOf(last.at)}${last.by ? `, ${last.by}` : ''}${last.reason_kind ? `, ${REASON_KIND_LT[last.reason_kind] || last.reason_kind}` : ''}${last.reason ? `: ${last.reason}` : ''}`]]} />
      )}
    </section>
  );
};
