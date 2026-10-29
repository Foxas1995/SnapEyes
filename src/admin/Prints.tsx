// Spaudiniai: the print offer (api/_lib/prints.py, the admin actions print_status, print_switch, print_retry, print_refresh, print_cancel).
// The owner's switch (OFF until he turns it on, after the merchOne store is active and its wallet funded), merchOne's configuration (the API
// user and key, live or test orders, whether it answers), the webhook URL to paste into the merchOne store settings, the offer with what each
// print earns, and the prints that are not shipped or closed, each with Retry, Refresh and Cancel. Lithuanian only, as the whole panel.
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import type { Call } from './AdminApp';
import { explain, fmtEur } from './format';
import { BTN, CARD, ConfirmDialog, CopyField, DANGER, GOLD, H2, MUTED, Notice, Spinner, Tbl, type ConfirmSpec } from './ui';

export interface PrintOfferRow { id: string; name: string; on: boolean; price: number; sku: string; cost?: number | null; margin_min?: number | null; margin_max?: number | null; ship_min?: number; ship_max?: number }
export interface PrintOpenRow { order: string; state?: string | null; product?: string | null; country?: string | null; attempts?: number | null; error?: string | null; merchone_id?: string | null; updated_iso?: string | null }
export interface PrintStatus {
  switch: { on: boolean; iso?: string | null; by?: string | null; rev: number; unreadable?: boolean };
  configured: boolean; problem?: string; live: boolean; api?: string | null; hook_url: string;
  rates_fetched?: string; countries: number; markets: string[]; offer: PrintOfferRow[]; margin_floor: number; open: PrintOpenRow[];
}

/** The words of a print's state (print.json state, api/_lib/prints.py). */
export const PRINT_STATE_LT: Record<string, string> = {
  waiting: 'laukia (kūrinys dar ne pristatytas arba merchOne neatsakė)', creating: 'siunčiama į merchOne', created: 'merchOne gavo, gaminama',
  shipped: 'išsiųsta', failed: 'nepavyko: reikia Tavo veiksmo', held: 'sulaikyta: adresas ar šalis nesutampa', canceled: 'atšaukta',
  canceled_partner: 'merchOne atšaukė',
};
export const printStateLt = (s: string | null | undefined): string => (s ? PRINT_STATE_LT[s] ?? s : 'laukia');

/** The actions of one print, shared by this page and the order detail: retry (send it now, again), refresh (read it back from merchOne),
 *  cancel (at merchOne, before production). Every one goes through the confirmation dialog. */
export function usePrintActions(call: Call, done: () => void) {
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);
  const [msg, setMsg] = useState<{ tone: 'good' | 'bad'; text: string } | null>(null);
  const run = async (action: string, body: Record<string, unknown>, ok: (d: Record<string, unknown>) => string) => {
    setMsg(null);
    const r = await call<Record<string, unknown>>(action, body);
    if (r.ok && r.data) setMsg({ tone: 'good', text: ok(r.data) }); else setMsg({ tone: 'bad', text: r.error || explain(r) });
    done();
  };
  const retry = (order: string) => setConfirm({
    title: 'Siųsti spaudinį į merchOne?', confirmLabel: 'Siųsti',
    text: `Užsakymo ${order} spaudinys siunčiamas į merchOne dabar (jei ankstesnis bandymas nepavyko arba merchOne jį atšaukė, kuriamas naujas merchOne užsakymas). Kūrinys turi būti pristatytas.`,
    run: () => run('print_retry', { order }, (d) => `Rezultatas: ${String(d.result)}${d.merchone_id ? `, merchOne ${String(d.merchone_id)}` : ''}${d.error ? ` (${String(d.error)})` : ''}.`),
  });
  const refresh = (order: string) => setConfirm({
    title: 'Paklausti merchOne?', confirmLabel: 'Paklausti', text: `Perskaitoma užsakymo ${order} spaudinio būsena merchOne pusėje (ir siuntos sekimas, jei jau išsiųsta).`,
    run: () => run('print_refresh', { order }, (d) => `Būsena: ${printStateLt(String(d.state))}.`),
  });
  const cancel = (order: string) => setConfirm({
    title: 'Atšaukti spaudinį merchOne?', confirmLabel: 'Atšaukti spaudinį', danger: true, typeToConfirm: order,
    text: `merchOne užsakymas atšaukiamas, kol jis dar negaminamas. Pinigai klientui negrąžinami automatiškai: jei reikia, grąžink spaudinio sumą Stripe.`,
    run: () => run('print_cancel', { order, confirm: order }, () => 'Atšaukta.'),
  });
  return { confirm, setConfirm, msg, retry, refresh, cancel };
}

export const PrintsPage: React.FC<{ call: Call }> = ({ call }) => {
  const [data, setData] = useState<PrintStatus | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(async (check = false) => {
    setBusy(true); setErr(null);
    const r = await call<PrintStatus>('print_status', { check });
    setBusy(false);
    if (r.ok && r.data) setData(r.data); else setErr(r.error || explain(r));
  }, [call]);
  useEffect(() => { void load(); }, [load]);
  const acts = usePrintActions(call, () => { void load(); });
  const sw = data?.switch;
  const flip = () => {
    if (!data || !sw) return;
    const on = !sw.on;
    acts.setConfirm({
      title: on ? 'Įjungti spaudinius?' : 'Išjungti spaudinius?', confirmLabel: on ? 'Įjungti' : 'Išjungti', danger: !on,
      text: on
        ? `Klientai galės prie užsakymo pridėti spaudinį (rinkos: ${data.markets.join(', ')}). Prieš įjungdamas: merchOne parduotuvė aktyvuota (ne sandbox), piniginė papildyta, MERCHONE_LIVE=1 Vercel, webhook URL įklijuotas merchOne. ${data.live ? '' : '\nDĖMESIO: MERCHONE_LIVE neįjungtas, todėl merchOne užsakymai bus TEST (negaminami).'}`
        : 'Naujų spaudinių nupirkti nebebus galima. Jau apmokėti spaudiniai vis tiek bus išsiųsti į merchOne.',
      run: async () => {
        const r = await call<{ switch?: unknown }>('print_switch', { on, confirm: 'spaudiniai', rev: sw.rev });
        if (!r.ok) setErr(r.error || explain(r));
        void load();
      },
    });
  };
  return (
    <div className="flex flex-col gap-4">
      <H2 right={<button type="button" className={BTN} onClick={() => load(true)} disabled={busy}>{busy ? <Spinner /> : null}Atnaujinti ir patikrinti merchOne</button>}>Spaudiniai</H2>
      {err && <Notice>{err}</Notice>}
      {acts.msg && <Notice tone={acts.msg.tone}>{acts.msg.text}</Notice>}
      {!data && busy && <Spinner />}
      {data && sw && (
        <>
          <section className={`${CARD} flex flex-col gap-3`} data-testid="print-switch">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-base font-bold">Spaudinių pardavimas: <span className={sw.on ? 'text-emerald-300' : 'text-white/70'}>{sw.on ? 'ĮJUNGTAS' : 'IŠJUNGTAS'}</span></p>
              <button type="button" className={sw.on ? DANGER : GOLD} onClick={flip} disabled={sw.unreadable || (!sw.on && !data.configured)}>{sw.on ? 'Išjungti' : 'Įjungti'}</button>
            </div>
            {sw.unreadable && <Notice>Jungiklio nepavyko perskaityti iš saugyklos: kol taip yra, spaudiniai neparduodami.</Notice>}
            {sw.iso && <p className={`text-xs ${MUTED}`}>Paskutinis pakeitimas: {sw.iso} ({sw.by || 'admin'}), versija {sw.rev}.</p>}
            <ul className="text-sm flex flex-col gap-1">
              <li>merchOne API: {data.configured ? <b className="text-emerald-300">nustatytas</b> : <b className="text-red-200">nenustatytas</b>}{data.problem ? ` (${data.problem})` : ''}{data.api ? `, atsako: ${data.api}` : ''}</li>
              <li>Užsakymai merchOne: {data.live ? <b className="text-emerald-300">TIKRI (MERCHONE_LIVE)</b> : <b>TEST (negaminami, neapmokestinami)</b>}; Stripe test mokėjimai visada TEST.</li>
              <li>Tarifų lentelė: {data.rates_fetched}, {data.countries} šalys; rinkos: {data.markets.join(', ')}.</li>
            </ul>
            <div>
              <p className={`text-xs ${MUTED} mb-1`}>Webhook URL (merchOne: Stores, Settings, Webhook URL). Jame yra slaptas raktas: niekam neduok.</p>
              <CopyField value={data.hook_url} label="Webhook URL" />
            </div>
          </section>
          <section className={CARD}>
            <h3 className="text-sm font-bold mb-2">Pasiūlymas ir marža</h3>
            <Tbl label="Spaudiniai" head={['Spaudinys', 'Kaina', 'merchOne be PVM', 'Siuntimas klientui', 'Uždarbis (po PVM ir mokesčių)']}
              rows={data.offer.map((p) => [
                <span key="n">{p.name}{p.on ? '' : ' (išjungtas)'}<br /><span className={`text-[11px] ${MUTED}`}>{p.sku}</span></span>,
                fmtEur(p.price), fmtEur(p.cost ?? null), `${fmtEur(p.ship_min ?? null)} ... ${fmtEur(p.ship_max ?? null)}`,
                <span key="m" className={(p.margin_min ?? 0) < 2500 ? 'text-amber-300' : ''}>{fmtEur(p.margin_min ?? null)} ... {fmtEur(p.margin_max ?? null)}</span>,
              ])} />
            <p className={`text-[11px] ${MUTED} mt-2`}>Kainos keičiamos api/_lib/print_offer.py, tarifai atnaujinami scripts/print_rates.py. Kainų patikra neleidžia parduoti su mažesniu nei {fmtEur(data.margin_floor)} uždarbiu.</p>
          </section>
          <section className={CARD}>
            <h3 className="text-sm font-bold mb-2">Neužbaigti spaudiniai</h3>
            <Tbl label="Neužbaigti spaudiniai" empty="Nėra." head={['Užsakymas', 'Būsena', 'Spaudinys', 'Bandymai', 'Klaida', 'Veiksmai']}
              rows={data.open.map((r) => [
                <a key="o" href={`#order/${r.order}`} className="underline break-all">{r.order}</a>,
                <span key="s">{printStateLt(r.state)}{r.merchone_id ? <><br /><span className={`text-[11px] ${MUTED}`}>{r.merchone_id}</span></> : null}</span>,
                `${r.product ?? ''} ${r.country ?? ''}`, String(r.attempts ?? 0), <span key="e" className="text-xs break-words">{r.error ?? ''}</span>,
                <span key="a" className="flex flex-wrap gap-1.5">
                  {r.state !== 'created' && <button type="button" className={`${BTN} !min-h-[32px] !px-2`} onClick={() => acts.retry(r.order)}>Siųsti</button>}
                  {r.merchone_id && <button type="button" className={`${BTN} !min-h-[32px] !px-2`} onClick={() => acts.refresh(r.order)}>Paklausti</button>}
                  {r.merchone_id && r.state === 'created' && <button type="button" className={`${DANGER} !min-h-[32px] !px-2`} onClick={() => acts.cancel(r.order)}>Atšaukti</button>}
                </span>,
              ])} />
          </section>
        </>
      )}
      <ConfirmDialog spec={acts.confirm} onClose={() => acts.setConfirm(null)} />
    </div>
  );
};

/** The order detail's print block (a_order "print": api/_lib/prints.py admin_view). */
export interface PrintView {
  product: string; name: string; country?: string; price?: number; ship?: number; city?: string; mismatch?: string[] | null; margin?: number | null;
  state: string; attempts?: number | null; merchone_id?: string | null; external_id?: string | null; is_test?: boolean | null; error?: string | null;
  partner_status?: string | null; tracking?: { url?: string | null; number?: string | null; carrier?: string | null } | null;
  file?: { width?: number; dpi?: number; bytes?: number } | null; history?: { t: number; state: string; why?: string }[] | null; updated_iso?: string | null;
}

export const OrderPrint: React.FC<{ call: Call; order: string; p: PrintView; onDone: () => void }> = ({ call, order, p, onDone }) => {
  const acts = usePrintActions(call, onDone);
  return (
    <section className={`${CARD} flex flex-col gap-2`} data-testid="admin-print">
      <h3 className="text-sm font-bold">Spaudinys</h3>
      {acts.msg && <Notice tone={acts.msg.tone}>{acts.msg.text}</Notice>}
      <ul className="text-sm flex flex-col gap-1">
        <li>{p.name}, {p.country} ({p.city}): {fmtEur(p.price ?? null)} + siuntimas {fmtEur(p.ship ?? null)}; uždarbis apie {fmtEur(p.margin ?? null)}</li>
        <li>Būsena: <b>{printStateLt(p.state)}</b>{p.attempts ? `, bandymų ${p.attempts}` : ''}{p.updated_iso ? `, ${p.updated_iso}` : ''}</li>
        {p.mismatch && p.mismatch.length > 0 && <li className="text-amber-300">Nesutampa: {p.mismatch.join(', ')} (spaudinys sulaikytas)</li>}
        {p.merchone_id && <li>merchOne: {p.merchone_id} ({p.is_test ? 'TEST' : 'tikras'}), išorinis nr. {p.external_id}{p.partner_status ? `, jų būsena ${p.partner_status}` : ''}</li>}
        {p.file && <li className={MUTED}>Spaudos failas: {p.file.width} px, {p.file.dpi} dpi, {Math.round((p.file.bytes ?? 0) / 1e5) / 10} MB</li>}
        {p.tracking && <li>Siunta: {p.tracking.carrier ?? ''} {p.tracking.number ?? ''} {p.tracking.url && <a href={p.tracking.url} target="_blank" rel="noopener noreferrer" className="underline">sekti</a>}</li>}
        {p.error && <li className="text-red-200 break-words">Klaida: {p.error}</li>}
      </ul>
      <div className="flex flex-wrap gap-2">
        {p.state !== 'created' && p.state !== 'shipped' && <button type="button" className={BTN} onClick={() => acts.retry(order)}>Siųsti į merchOne</button>}
        {p.merchone_id && <button type="button" className={BTN} onClick={() => acts.refresh(order)}>Paklausti merchOne</button>}
        {p.merchone_id && p.state === 'created' && <button type="button" className={DANGER} onClick={() => acts.cancel(order)}>Atšaukti merchOne</button>}
      </div>
      <ConfirmDialog spec={acts.confirm} onClose={() => acts.setConfirm(null)} />
    </section>
  );
};
