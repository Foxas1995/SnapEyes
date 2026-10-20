// Reklamos: the owner's spend ledger (typed or pasted from Ads Manager) put beside the counter's steps and the order records: the cost of a visit, of a started and a completed preview and of an
// order, the return on the spend, and the traffic lights of the ads plan (phase 0: section 2.3, the decision of 2.4, phase 1: section 6). Meta adds 21 percent VAT: Ads Manager's figures have none,
// the card pays 21 percent more, and the ledger says which of the two a typed amount is.
import { useCallback, useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { explain } from './format';
import { BTN, CARD, ConfirmDialog, GOLD, H2, INPUT, MUTED, Notice, Spinner, Tbl, type ConfirmSpec } from './ui';
import { FilterBar, Light, Partial, download, useReport } from './TrafficUi';
import {
  adRows, centsOf, eur, fromDay, keyText, marketOfTerm, moneyText, netOf, cardOf, num, phase0, phase0Decision, phase1, rowsFor, toCsv, totalsOf, type AdRow, type AdsReply, type Group, type SrcRow,
} from './traffic';
import { fmtPct } from './stylesView';

const LEVELS: ['cmp' | 'trm' | 'cnt', string][] = [['cmp', 'Kampanijos'], ['trm', 'Reklamų rinkiniai'], ['cnt', 'Reklamos']];
const PASTE_HELP = 'diena; kampanija; rinkinys; reklama; suma eurais; parodymai; paspaudimai   (rinkinys, reklama, parodymai ir paspaudimai gali būti tušti; pirma eilutė su antraštėmis praleidžiama)';

/** A cost per step: nothing when no spend was typed (null) or the step did not happen. */
const per = (cents: number | null, n: number): string => (cents !== null && n > 0 ? eur(Math.round(cents / n)) : 'nėra duomenų');

export const ReportCard: React.FC<{ row: SrcRow; level: 'cmp' | 'trm' | 'cnt'; ledger: AdRow[]; from: string; vat: number; ltCost: number | null }> = ({ row, level, ledger, from, vat, ltCost }) => {
  const rows = rowsFor(ledger, row.key, level as Group, from);
  const t = totalsOf(rows, vat);
  const spend = t.rows > 0 ? t.spend : null;
  const s = row.steps;
  const market = row.key.trm ? marketOfTerm(row.key.trm) : null;
  const eurRev = num(row.revenue?.eur);
  const lights = [...phase0(t, s, market, ltCost), ...(spend !== null && num(row.orders) > 0 ? phase1(spend, num(row.orders), eurRev) : [])];
  const cells: [string, string][] = [
    ['Išleista (Ads Manager)', t.rows ? eur(t.spend) : 'nėra įrašų'], ['Nuo kortelės (+21 % PVM)', t.rows ? eur(t.card) : '-'],
    ['Paspaudimai', t.hasClicks ? String(t.clicks) : 'neįrašyta'], ['Nusileidimai', String(num(s.landing))], ['Atidarė /try', String(num(s.try))], ['Pradėta peržiūra', String(num(s.en))], ['Užbaigta peržiūra', String(num(s.rs))],
    ['Pirkimo kortelė uždaryta', String(num(s.soon))], ['Paspaudė pirkti', String(num(s.buy))], ['Užsakymai', String(num(row.orders))], ['Pajamos', moneyText(row.revenue)],
    ['Kaina už nusileidimą', per(spend, num(s.landing))], ['Kaina už /try', per(spend, num(s.try))], ['Kaina už pradėtą', per(spend, num(s.en))], ['Kaina už užbaigtą', per(spend, num(s.rs))],
    ['Kaina už užsakymą', per(spend, num(row.orders))], ['CTR', t.hasImpr && t.impr > 0 && t.hasClicks ? fmtPct(t.clicks / t.impr) : 'neįrašyta'],
  ];
  return (
    <section className={`${CARD} flex flex-col gap-3`} aria-label={keyText(row.key, 'cnt')}>
      <h3 className="text-sm font-bold break-words">{[row.key.cmp, row.key.trm, row.key.cnt].filter(Boolean).join(' / ') || 'Be kampanijos'}</h3>
      <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1.5 text-xs">
        {cells.map(([k, v]) => <div key={k} className="min-w-0"><dt className="text-white/55">{k}</dt><dd className="break-words font-semibold">{v}</dd></div>)}
      </dl>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">{lights.map((l) => <Light key={l.key} tone={l.tone} label={l.label} text={l.text} />)}</div>
    </section>
  );
};

export const AdsPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [level, setLevel] = useState<'cmp' | 'trm' | 'cnt'>('cmp');
  const { data, err, busy, reload } = useReport<AdsReply>(call, 'ads', { days });
  const [form, setForm] = useState({ day: new Date().toISOString().slice(0, 10), cmp: '', trm: '', cnt: '', amount: '', vat: false, impr: '', clicks: '' });
  const [paste, setPaste] = useState('');
  const [msg, setMsg] = useState<{ tone: 'good' | 'bad'; text: string } | null>(null);
  const [working, setWorking] = useState(false);
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);
  const vat = data?.vat ?? 1.21;
  const from = fromDay(days);
  const ledger = data?.rows ?? [];
  const inWindow = ledger.filter((r) => r.day >= from);

  const send = useCallback(async (action: 'ads_put' | 'ads_delete', body: Record<string, unknown>, ok: string) => {
    setWorking(true); setMsg(null);
    const r = await call<{ stored?: number; deleted?: number }>(action, { ...body, rev: data?.rev });
    setWorking(false);
    if (r.ok) { setMsg({ tone: 'good', text: ok }); reload(); return true; }
    setMsg({ tone: 'bad', text: r.reason === 'stale_view' ? 'Žurnalas pasikeitė po to, kai šis puslapis buvo nupieštas: atnaujink puslapį ir bandyk dar kartą.' : (r.error || explain(r)) });
    return false;
  }, [call, data?.rev, reload]);

  const add = async () => {
    const cents = centsOf(form.amount);
    if (!form.cmp.trim()) return setMsg({ tone: 'bad', text: 'Įrašyk kampanijos pavadinimą (kaip jis yra nuorodoje, pvz. se-p0-test).' });
    if (cents === null) return setMsg({ tone: 'bad', text: 'Suma eurais, pvz. 2,50.' });
    const row: Record<string, unknown> = { day: form.day, cmp: form.cmp.trim(), amount: cents, vat: form.vat };
    if (form.trm.trim()) row.trm = form.trm.trim();
    if (form.cnt.trim()) row.cnt = form.cnt.trim();
    if (form.impr.trim()) row.impr = Number(form.impr);
    if (form.clicks.trim()) row.clicks = Number(form.clicks);
    if (await send('ads_put', { rows: [row] }, 'Įrašyta.')) setForm({ ...form, amount: '', impr: '', clicks: '' });
  };

  // only advertising is on this page: the counter's rows of utm_medium paid and the campaigns that have spend typed in the window (organic links and visits without a code have no cost)
  const rowsOf = (lv: 'cmp' | 'trm' | 'cnt') => adRows(data?.groups ?? [], ledger, lv, from);
  const adCmp = rowsOf('cmp');
  const adTrm = rowsOf('trm');
  const groups = level === 'cmp' ? adCmp : level === 'trm' ? adTrm : rowsOf('cnt');
  const camps = [...new Set(ledger.map((r) => r.cmp).concat(adCmp.map((g) => g.key.cmp)).filter(Boolean))].sort();
  const ltRows = adTrm.filter((g) => marketOfTerm(g.key.trm) === 'lt');
  const ltSpend = ltRows.reduce((s, g) => s + totalsOf(rowsFor(ledger, g.key, 'trm', from), vat).spend, 0);
  const ltDone = ltRows.reduce((s, g) => s + num(g.steps.rs), 0);
  const ltCost = ltDone > 0 && ltSpend > 0 ? Math.round(ltSpend / ltDone) : null;
  const doneAll = adCmp.reduce((s, g) => s + num(g.steps.rs), 0);
  const bestMarket = ['lt', 'de', 'hu'].map((m) => {
    const rs = adTrm.filter((g) => marketOfTerm(g.key.trm) === m);
    const done = rs.reduce((s, g) => s + num(g.steps.rs), 0);
    const spend = rs.reduce((s, g) => s + totalsOf(rowsFor(ledger, g.key, 'trm', from), vat).spend, 0);
    return { m, done, cost: done > 0 && spend > 0 ? Math.round(spend / done) : null };
  }).sort((a, b) => (a.cost ?? 1e12) - (b.cost ?? 1e12))[0];
  // landings against clicks only where the clicks were typed (a campaign without them would make the share look larger)
  const clicked = adCmp.map((g) => ({ g, t: totalsOf(rowsFor(ledger, g.key, 'cmp', from), vat) })).filter((x) => x.t.hasClicks);
  const decision = phase0Decision(doneAll, bestMarket?.done ?? 0, bestMarket?.cost ?? null, clicked.reduce((s, x) => s + num(x.g.steps.landing), 0), clicked.reduce((s, x) => s + x.t.clicks, 0));

  const ledgerRows = [...inWindow].reverse().map((r) => [
    <span key="d" className="whitespace-nowrap">{r.day}</span>, <span key="c" className="break-words">{[r.cmp, r.trm, r.cnt].filter(Boolean).join(' / ')}</span>,
    <span key="a">{eur(netOf(r, vat))}</span>, <span key="k">{eur(cardOf(r, vat))}</span>, <span key="p">{r.impr ?? '-'}</span>, <span key="l">{r.clicks ?? '-'}</span>,
    <button key="x" type="button" className={`${BTN} !min-h-[32px] !px-2`} disabled={working}
      onClick={() => setConfirm({ title: 'Ištrinti įrašą?', text: `${r.day}, ${r.cmp}, ${eur(netOf(r, vat))}. Tai tavo išlaidų žurnalas; įrašas dings visiems laikams.`, confirmLabel: 'Ištrinti', danger: true, run: async () => { await send('ads_delete', { ids: [r.id] }, 'Ištrinta.'); } })}>Ištrinti</button>,
  ]);

  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} disabled={!inWindow.length} onClick={() => download(`reklamos-${days}d.csv`, toCsv(['Diena', 'Kampanija', 'Rinkinys', 'Reklama', 'Ads Manager EUR', 'Nuo kortelės EUR', 'Parodymai', 'Paspaudimai'],
        inWindow.map((r) => [r.day, r.cmp, r.trm ?? '', r.cnt ?? '', netOf(r, vat) / 100, cardOf(r, vat) / 100, r.impr ?? null, r.clicks ?? null])))}>Eksportuoti CSV</button>}>Reklamos</H2>
      <FilterBar days={days} setDays={setDays} filters={{}} setFilters={() => undefined} available={undefined} only={[]} busy={busy} onReload={reload}
        note="Meta prideda 21 % PVM: Ads Manager rodo sumas be PVM, kortelė nuskaičiuoja 21 % daugiau. Skaičiuojame Ads Manager sumomis (kaip reklamų planas); jei įrašai sumą nuo kortelės, pažymėk „su PVM“." />
      {err && <Notice>{err}</Notice>}
      {data && <Partial partial={data.partial} recording={data.recording} />}
      {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}
      {busy && !data && <Spinner />}
      {data && (
        <>
          <section className={`${CARD} flex flex-col gap-3`}>
            <h3 className="text-sm font-bold">Įrašyti išlaidas</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <label className="flex flex-col gap-0.5"><span className="text-white/60">Diena</span><input className={INPUT} type="date" value={form.day} onChange={(e) => setForm({ ...form, day: e.target.value })} aria-label="Diena" /></label>
              <label className="flex flex-col gap-0.5"><span className="text-white/60">Kampanija</span><input className={INPUT} list="ad-camps" value={form.cmp} onChange={(e) => setForm({ ...form, cmp: e.target.value })} placeholder="se-p0-test" aria-label="Kampanija" autoComplete="off" /></label>
              <label className="flex flex-col gap-0.5"><span className="text-white/60">Rinkinys</span><input className={INPUT} value={form.trm} onChange={(e) => setForm({ ...form, trm: e.target.value })} placeholder="lt-a1-eye" aria-label="Reklamų rinkinys" autoComplete="off" /></label>
              <label className="flex flex-col gap-0.5"><span className="text-white/60">Reklama</span><input className={INPUT} value={form.cnt} onChange={(e) => setForm({ ...form, cnt: e.target.value })} placeholder="a1-lt-s1" aria-label="Reklama" autoComplete="off" /></label>
              <label className="flex flex-col gap-0.5"><span className="text-white/60">Suma, €</span><input className={INPUT} inputMode="decimal" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="2,50" aria-label="Suma eurais" /></label>
              <label className="flex flex-col gap-0.5"><span className="text-white/60">Parodymai</span><input className={INPUT} inputMode="numeric" value={form.impr} onChange={(e) => setForm({ ...form, impr: e.target.value })} aria-label="Parodymai" /></label>
              <label className="flex flex-col gap-0.5"><span className="text-white/60">Paspaudimai (link)</span><input className={INPUT} inputMode="numeric" value={form.clicks} onChange={(e) => setForm({ ...form, clicks: e.target.value })} aria-label="Paspaudimai" /></label>
              <label className="flex items-end gap-2 pb-2"><input type="checkbox" className="w-4 h-4 accent-[#f5c542]" checked={form.vat} onChange={(e) => setForm({ ...form, vat: e.target.checked })} /><span>suma su PVM (nuo kortelės)</span></label>
            </div>
            <datalist id="ad-camps">{camps.map((c) => <option key={c} value={c} />)}</datalist>
            <div><button type="button" className={GOLD} onClick={() => void add()} disabled={working}>{working && <Spinner />}Įrašyti</button></div>
            <details className="rounded-xl border border-white/10 bg-black/20">
              <summary className="cursor-pointer select-none px-3 py-2 text-xs font-semibold text-white/70">Įklijuoti kelias eilutes</summary>
              <div className="p-3 flex flex-col gap-2">
                <p className={`text-[11px] ${MUTED} break-words`}>{PASTE_HELP}</p>
                <textarea className={`${INPUT} min-h-[96px] font-mono text-xs`} value={paste} onChange={(e) => setPaste(e.target.value)} aria-label="Įklijuotos eilutės" spellCheck={false} placeholder="2026-10-21; se-p0-test; lt-a1-eye; a1-lt-s1; 2,50; 1200; 18" />
                <div><button type="button" className={BTN} disabled={working || !paste.trim()} onClick={async () => { if (await send('ads_put', { paste }, 'Įrašyta.')) setPaste(''); }}>Įrašyti eilutes</button></div>
              </div>
            </details>
          </section>
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Ar eiti į 1 fazę (reklamų plano 2.4 skyrius)</h3>
            <ul className="flex flex-col gap-1 text-sm">
              {decision.lines.map((l) => <li key={l.text}>{l.ok === null ? '? ' : l.ok ? 'taip: ' : 'ne: '}{l.text}</li>)}
              <li>? Nėra neišspręstų reklamų atmetimų ar paskyros ribojimo (tai žinai tik tu).</li>
            </ul>
            <p className="text-sm font-semibold">{decision.ok === null ? 'Dar per mažai duomenų sprendimui.' : decision.ok ? 'Skaičiai leidžia eiti į 1 fazę (jei ketvirta sąlyga irgi tinka).' : 'Skaičiai dar neleidžia: pratęsk 0 fazę tuo pačiu biudžetu arba nedidink.'}</p>
            <p className={`text-[11px] ${MUTED}`}>Peržiūros skaičiuojamos pagal skaitiklį (pirma peržiūros užklausa rinkiniui). Maži skaičiai rodo kryptį, ne išvadą.</p>
          </section>
          <div className="flex flex-wrap gap-1.5" role="group" aria-label="Lygis">
            <span className={`text-xs self-center ${MUTED}`}>Rodyti:</span>
            {LEVELS.map(([k, l]) => <button key={k} type="button" onClick={() => setLevel(k)} aria-pressed={level === k} className={`px-2.5 py-1 rounded-lg text-xs border ${level === k ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{l}</button>)}
          </div>
          {groups.length === 0 && <p className={`text-sm ${MUTED}`}>Dar nėra nei išlaidų įrašų, nei nuorodų su kampanijos kodu šiuo laikotarpiu.</p>}
          {groups.map((g) => <ReportCard key={[g.key.cmp, g.key.trm, g.key.cnt].join('|')} row={g} level={level} ledger={ledger} from={from} vat={vat} ltCost={ltCost} />)}
          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Išlaidų žurnalas ({inWindow.length} iš {ledger.length})</h3>
            <Tbl head={['Diena', 'Kas', 'Ads Manager', 'Nuo kortelės', 'Parodymai', 'Paspaudimai', '']} rows={ledgerRows} label="Išlaidų žurnalas" empty="Dar nėra įrašų." />
          </section>
        </>
      )}
      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
    </div>
  );
};
