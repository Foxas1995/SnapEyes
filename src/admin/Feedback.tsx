// Atsiliepimai: what visitors said in the anonymous feedback box of /try (src/try/Feedback.tsx, api/_lib/feedback.py): the chips they chose on the result screen and on the card that asks for another
// photo, which style was on screen or which block reason was shown, what became of the texts, and the texts themselves (kept 90 days, deleted here or by the daily clean-up). Nobody is asked for
// an e-mail address, so nobody can be answered. The counts are the day counts of the events (twelve months, no text in them); every text is shown as text (a React text node, never markup).
import { useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { BLOCK_LT, STYLE_LT, explain } from './format';
import { BTN, CARD, ConfirmDialog, H2, MUTED, Notice, Spinner, type ConfirmSpec } from './ui';
import { FilterBar, FxCard, Partial, useFilters, useReport } from './TrafficUi';
import { BR_LT, DEV_LT, FB_PLACE_LT, LANG_LT, campText, fbChipLt, fxLines, fxTotal, groupLt, groupsOf, label, type FeedbackReply, type FeedbackText } from './traffic';

const FB = ['fb_result', 'fb_retake', 'fb_style', 'fb_block', 'fb_text'] as const;

/** The day and minute (UTC) a text was written: "2026-10-20 12:31". */
export const whenText = (r: Pick<FeedbackText, 'day' | 'at'>): string => `${r.day} ${r.at.slice(0, 2)}:${r.at.slice(2, 4)}`;

/** The line under a text: when, where, which style or block reason, how many eyes, the source, the device, the browser, the language, the country. */
export function metaText(r: FeedbackText): string {
  const ctx = r.x ? (r.w === 'result' ? label(STYLE_LT, r.x) : label(BLOCK_LT, r.x)) : '';
  const eyes = r.eyes ? `${r.eyes} ${r.eyes === 1 ? 'akis' : 'akys'}` : '';
  const camp = campText([r.src, r.med, r.cmp, r.trm, r.cnt].map((v) => v ?? '').join('|').replace(/[|]+$/, ''));
  return [`${whenText(r)} UTC`, FB_PLACE_LT[r.w] ?? r.w, ctx, eyes, camp, r.dev ? label(DEV_LT, r.dev) : '', r.br ? label(BR_LT, r.br) : '', r.lang ? label(LANG_LT, r.lang) : '', r.cc ? r.cc.toUpperCase() : ''].filter(Boolean).join(' · ');
}

const TextRow: React.FC<{ r: FeedbackText; busy: boolean; onDelete: (r: FeedbackText) => void }> = ({ r, busy, onDelete }) => (
  <li className="rounded-xl border border-white/10 bg-black/20 p-3 flex flex-col gap-1.5" data-testid="feedback-row">
    <div className="flex flex-wrap items-start justify-between gap-2">
      <span className="text-xs font-semibold text-[#f5c542]">{fbChipLt(r.w, r.c)}</span>
      <button type="button" className={`${BTN} !min-h-[32px] !px-2`} disabled={busy} onClick={() => onDelete(r)}>Ištrinti</button>
    </div>
    <p className="text-sm whitespace-pre-wrap break-words">{r.txt}</p>
    <p className={`text-[11px] ${MUTED} break-words`}>{metaText(r)}</p>
  </li>
);

export const FeedbackPage: React.FC<{ call: Call }> = ({ call }) => {
  const [days, setDays] = useState(30);
  const [by, setBy] = useState<'cmp' | 'dev' | 'br'>('cmp');
  const [filters, setFilters] = useFilters();
  const { data, err, busy, reload } = useReport<FeedbackReply>(call, 'feedback', { days, by, ...filters });
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);
  const [msg, setMsg] = useState<{ tone: 'good' | 'bad'; text: string } | null>(null);
  const [working, setWorking] = useState(false);
  const fx = data?.fx;
  const groups = groupsOf(fx, FB, 5);
  const answers = fxTotal(fx, 'fb_result') + fxTotal(fx, 'fb_retake');
  const typed = fxTotal(fx, 'fb_text');
  const kept = fxLines(fx, 'fb_text').find((l) => l.value === 'kept')?.total ?? 0;
  const texts = data?.texts ?? [];

  const remove = (r: FeedbackText) => setConfirm({
    title: 'Ištrinti tekstą?', text: `${whenText(r)} UTC: ${r.txt.length > 80 ? `${r.txt.slice(0, 80)}...` : r.txt}. Skaičiai liks (juose teksto nėra), pats tekstas dings visiems laikams.`, confirmLabel: 'Ištrinti', danger: true,
    run: async () => {
      setWorking(true); setMsg(null);
      const res = await call<{ result?: string }>('feedback_delete', { id: r.id });
      setWorking(false);
      if (res.ok) { setMsg({ tone: 'good', text: res.data?.result === 'not_found' ? 'Teksto jau nebėra.' : 'Ištrinta.' }); reload(); } else setMsg({ tone: 'bad', text: res.error || explain(res) });
    },
  });

  return (
    <div className="flex flex-col gap-4">
      <H2>Atsiliepimai</H2>
      <FilterBar days={days} setDays={setDays} filters={filters} setFilters={setFilters} available={data?.available} only={['dev', 'br']} busy={busy} onReload={reload}
        note="Lankytojai pasirenka vieną iš šešių atsakymų (rezultato ekrane arba kortelėje, kuri prašo kitos nuotraukos) ir, jei nori, parašo iki 300 simbolių. Nei vardo, nei el. pašto: atsakyti negalima. Skaičiai (be tekstų) saugomi 12 mėnesių, tekstai 90 dienų."
        extra={
          <span className="flex flex-wrap gap-1.5 items-center ml-1" role="group" aria-label="Išskaidyti">
            <span className={`text-xs ${MUTED}`}>Išskaidyti:</span>
            {([['cmp', 'pagal kampaniją'], ['dev', 'pagal įrenginį'], ['br', 'pagal naršyklę']] as const).map(([k, l]) => (
              <button key={k} type="button" onClick={() => setBy(k)} aria-pressed={by === k} className={`px-2.5 py-1 rounded-lg text-xs border ${by === k ? 'bg-white/15 border-white/30' : 'border-white/10 text-white/70'}`}>{l}</button>
            ))}
          </span>
        } />
      {err && <Notice>{err}</Notice>}
      {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}
      {data && <Partial partial={data.partial} recording={data.recording} />}
      {data && !data.on && <Notice>Atsiliepimų dėžutė šiame serveryje išjungta (SNAPEYES_FEEDBACK išjungtas, nėra saugyklos arba CRON_SECRET): lankytojai jos nemato.</Notice>}
      {busy && !data && <Spinner />}
      {data && answers === 0 && texts.length === 0 && <p className={`text-sm ${MUTED}`}>Šiuo laikotarpiu dar nėra atsiliepimų. Dėžutė rodoma po kaina rezultato ekrane ir po kortelės, kuri prašo kitos nuotraukos.</p>}
      {data && (answers > 0 || texts.length > 0) && (
        <>
          <section className={`${CARD} flex flex-col gap-1`}>
            <h3 className="text-sm font-bold">Iš viso</h3>
            <p className="text-sm">Atsakymų: <b>{answers}</b>. Su tekstu: <b>{typed}</b> (išsaugota <b>{kept}</b>).</p>
            <p className={`text-[11px] ${MUTED}`}>Tekstas neišsaugomas, jei jame yra el. paštas, telefono numeris, nuoroda arba jis atrodo kaip šlamštas; atsakymas vis tiek skaičiuojamas.</p>
          </section>
          <FxCard title="Rezultato ekranas: ką pasirinko" fx={fx} metric="fb_result" by={by} groups={groups} />
          <FxCard title="Kortelė „padaryk kitą nuotrauką“: ką pasirinko" fx={fx} metric="fb_retake" by={by} groups={groups} />
          <FxCard title="Rezultato ekranas pagal stilių" hint="Atsakymas ir stilius, kuris buvo ekrane: kuris stilius ką sako." fx={fx} metric="fb_style" by={by} groups={groups} limit={20} />
          <FxCard title="Kortelė pagal atmetimo priežastį" fx={fx} metric="fb_block" by={by} groups={groups} limit={20} />
          <FxCard title="Kas nutiko tekstams" fx={fx} metric="fb_text" by={by} groups={groups} />
          <section className={`${CARD} flex flex-col gap-2`} aria-label="Tekstai">
            <h3 className="text-sm font-bold">Tekstai ({texts.length}{data.texts_more ? ' ir daugiau' : ''}; saugomi {data.retention_days} dienų)</h3>
            {texts.length === 0 && <p className={`text-sm ${MUTED}`}>Šiuo laikotarpiu tekstų nėra.</p>}
            <ul className="flex flex-col gap-2">{texts.map((r) => <TextRow key={r.id} r={r} busy={working} onDelete={remove} />)}</ul>
            <p className={`text-[11px] ${MUTED}`}>Jei tekste yra asmens duomenų, ištrink jį čia. Stulpeliai: {groups.map((g) => groupLt(by, g)).join(', ') || 'nėra'}. Mažas n rodo kryptį, ne išvadą.</p>
          </section>
        </>
      )}
      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
    </div>
  );
};
