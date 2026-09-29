// One order: every stored record, the images (signed links valid 1 h), the checks, the payments and the admin log,
// and the actions, each behind a confirmation (a refund and the deletion also need the order number typed). An
// action's result shows in a toast pinned to the bottom of the screen, next to wherever its button was.
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import type { EyeView, OrderDetail, Payment, Reply } from './api';
import type { Call } from './AdminApp';
import { explain, fmtBytes, fmtEur, fmtNum, fmtTime, RESULT_LT, STATE_LT, STATE_TONE, STYLE_LT } from './format';
import { BTN, CARD, Chip, ConfirmDialog, CopyField, DANGER, ExtLink, H2, JsonView, MUTED, Notice, Rows, Spinner, Thumb, Toast } from './ui';
import type { ConfirmSpec, Tone } from './ui';

type J = Record<string, unknown>;
const s = (v: unknown): string => (typeof v === 'string' ? v : typeof v === 'number' || typeof v === 'boolean' ? String(v) : '');
const n = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const obj = (v: unknown): J => (v && typeof v === 'object' && !Array.isArray(v) ? (v as J) : {});
const isoTime = (v: unknown): string => {
  const t = typeof v === 'number' ? v : typeof v === 'string' ? Date.parse(v) / 1000 : NaN;
  return Number.isFinite(t) ? fmtTime(t, true) : s(v) || '-';
};
const yesNo = (v: unknown) => (v === true ? 'taip' : v === false ? 'ne' : '-');

const QaLine: React.FC<{ label: string; qa: J | null | undefined }> = ({ label, qa }) => {
  if (!qa || !Object.keys(qa).length) return null;
  const ok = qa.ok;
  return (
    <p className="text-xs break-words">
      <span className={MUTED}>{label}: </span>
      <b className={ok === false ? 'text-red-200' : ok === true ? 'text-emerald-200' : ''}>{ok === false ? 'nepraėjo' : ok === true ? 'gerai' : '-'}</b>
      {n(qa.ring_de00) !== null ? ` · dE00 ${fmtNum(n(qa.ring_de00))}` : ''}
      {qa.render_ok !== undefined ? ` · sekė peržiūrą: ${yesNo(qa.render_ok)}` : ''}
      {qa.pupil_neutral !== undefined && qa.pupil_neutral !== null ? ` · vyzdys neutralus: ${yesNo(qa.pupil_neutral)}` : ''}
      {n(qa.score) !== null ? ` · balas ${fmtNum(n(qa.score))}` : ''}
    </p>
  );
};

export const OrderDetailPage: React.FC<{ call: Call; order: string }> = ({ call, order }) => {
  const [d, setD] = useState<OrderDetail | null>(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(true);
  const [note, setNote] = useState<{ tone: Tone; text: string; busy?: boolean; link?: string; withdraw?: string; order?: string } | null>(null);
  const [confirm, setConfirm] = useState<ConfirmSpec | null>(null);

  const apply = useCallback((r: Reply<OrderDetail>) => {
    setBusy(false);
    if (r.ok && r.data) { setD(r.data); setErr(''); } else { setErr(explain(r)); if (r.status === 404) setD(null); }
  }, []);

  useEffect(() => {
    let live = true;
    void call<OrderDetail>('order', { order }).then((r) => { if (live) apply(r); });
    return () => { live = false; };
  }, [call, order, apply]);

  // a plain success closes itself after a while; a failure, a warning or links stay until closed
  useEffect(() => {
    if (!note || note.tone !== 'good' || note.link || note.withdraw || note.order) return;
    const t = setTimeout(() => setNote((cur) => (cur === note ? null : cur)), 9000);
    return () => clearTimeout(t);
  }, [note]);

  const load = async () => { setBusy(true); apply(await call<OrderDetail>('order', { order })); };

  const act = async (action: string, extra: J, done: (x: J) => string) => {
    setNote({ tone: 'info', text: 'Vykdoma...', busy: true });
    const r = await call<J>(action, { order, ...extra }, 90_000);
    if (r.ok && r.data) {
      setNote({ tone: r.data.sent === false ? 'warn' : 'good', text: done(r.data), link: s(r.data.url) || undefined,
        withdraw: s(r.data.withdraw_url) || undefined, order: s(r.data.order_url) || undefined });
    } else setNote({ tone: 'bad', text: explain(r) });
    if (action !== 'link') await load();
  };
  const mailWord = (x: J) => RESULT_LT[s(x.result)] || s(x.result);

  const rec = (name: string) => obj(d?.records[name]);
  const paidRec = rec('paid.json');
  const spec = obj(paidRec.spec);
  const orderRec = rec('order.json');
  const checkout = obj(orderRec.checkout);
  const mail = rec('mail_delivery.json');
  const delivery = rec('delivery.json');
  const review = rec('review.json');
  const withdrawals = d ? Object.entries(d.records).filter(([p]) => /^withdrawal_[^/]+\.json$/.test(p) && !/_(ack|note)\.json$/.test(p)) : [];
  const allMade = !!d && d.count > 0 && d.eyes.filter((e) => e.master?.url).length >= d.count;
  const held = !!d?.records['delivery.json'] && delivery.needs_review === true && !d?.records['release.json'];

  const eyeActions = (e: EyeView) => {
    if (!d?.paid || d.lab || !d.can.counts || e.eye > d.count) return null;
    if (!e.master?.url) {
      // making ends the customer's right of withdrawal; the published texts let only the customer's own order page
      // start it, so this is offered only once it has begun there (or the 14-day period is over)
      if (!d.can.start) {
        return (
          <span className={`text-xs ${MUTED} max-w-[26rem]`}>
            Gamyba dar neprasidėjo: ją pradeda pirkėjo užsakymo puslapis. Pradėjus čia pirkėjas netektų teisės atsisakyti,
            o paskelbtos sąlygos to nenumato. Palauk, kol pirkėjas atidarys puslapį, arba parašyk jam.
          </span>
        );
      }
      return (
        <button type="button" className={BTN} onClick={() => setConfirm({
          title: `Pagaminti ${e.eye} akies 4K`, confirmLabel: 'Pagaminti',
          text: `${d.making?.began ? 'Gamybą jau pradėjo pirkėjo užsakymo puslapis' : 'Pirkėjo 14 dienų atsisakymo terminas jau baigėsi'}, todėl tai pirkėjo teisių nekeičia. Pagamina šią akį taip pat, kaip užsakymo puslapis. Trunka 30-50 s, vienas 4K vaizdas (apie $0,15).`,
          run: () => act('render', { eye: e.eye }, (x) => (x.result === 'made' ? 'Akis pagaminta.' : 'Akis jau buvo pagaminta.')),
        })}>Pagaminti 4K</button>
      );
    }
    if (e.master.rerender_available) {
      return (
        <button type="button" className={BTN} onClick={() => setConfirm({
          title: `Perpiešti ${e.eye} akį`, confirmLabel: 'Perpiešti',
          text: 'Pagal master_eye taisykles: ta pati patvirtinta peržiūra, antras 4K piešinys. Lieka geresnis iš dviejų, kitas saugomas šalia. Trunka 30-50 s, apie $0,15. Po to sudėk kūrinį iš naujo.',
          run: () => act('render', { eye: e.eye }, (x) => (x.result === 'rerendered' ? 'Akis perpiešta. Dabar sudėk kūrinį iš naujo.' : 'Nieko nepiešta: akis jau saugoma.')),
        })}>Perpiešti</button>
      );
    }
    return <span className={`text-xs ${MUTED}`}>{e.master.rerendered ? 'Jau perpiešta kartą.' : 'Perpiešti negalima: 4K praėjo patikrą.'}</span>;
  };

  const refundButton = (p: Payment) => (
    <button type="button" className={DANGER} disabled={!d?.can.stripe || p.refunded} onClick={() => setConfirm({
      title: 'Grąžinti pinigus', danger: true, confirmLabel: 'Grąžinti', typeToConfirm: order,
      text: `Stripe grąžins visą šio mokėjimo sumą (${fmtEur(p.amount)}${p.live ? '' : ', testo režimas'}) pirkėjui. To atšaukti negalima.\nMokėjimas: ${p.payment_intent}`,
      run: () => act('refund', { payment_intent: p.payment_intent, confirm: order }, (x) => `Grąžinimas: ${s(obj(x.refund).status) || s(x.result)} (${fmtEur(n(obj(x.refund).amount))}).`),
    })}>{p.refunded ? 'Grąžinta' : 'Grąžinti pinigus'}</button>
  );

  return (
    <div className="flex flex-col gap-4">
      {note && (
        <Toast tone={note.tone} onClose={note.busy ? undefined : () => setNote(null)}>
          <span className="inline-flex items-center gap-2">{note.busy && <Spinner />}{note.text}</span>
          {note.link && <div className="mt-1">Failas: <ExtLink href={note.link}>atidaryti</ExtLink></div>}
          {note.withdraw && (
            <div className="mt-2">
              Atsisakymo forma (atidarius nieko nepradedama): <ExtLink href={note.withdraw}>{note.withdraw}</ExtLink>
            </div>
          )}
          {note.order && (
            <div className="mt-2">
              Užsakymo puslapis, tik nukopijuoti pirkėjui. Neatidaryk pats: atidarius prasideda gamyba ir pirkėjas netenka teisės atsisakyti.
              <CopyField value={note.order} label="Užsakymo puslapio nuoroda" />
            </div>
          )}
        </Toast>
      )}
      <H2 right={
        <div className="flex flex-wrap gap-2">
          <a href="#orders" className={BTN}>Atgal į sąrašą</a>
          <button type="button" className={BTN} onClick={() => void load()} disabled={busy}>{busy && <Spinner />}Atnaujinti</button>
        </div>
      }>
        <span className="break-all">Užsakymas {order}</span>
      </H2>
      {err && <Notice>{err}</Notice>}
      {!d && busy && <p className="flex items-center gap-2 text-sm"><Spinner />Kraunama...</p>}
      {d && (
        <>
          <section className={`${CARD} flex flex-col gap-3`}>
            <div className="flex flex-wrap items-center gap-2">
              <Chip tone={STATE_TONE[d.state] || 'muted'}>{STATE_LT[d.state] || d.state}</Chip>
              {d.lab && <Chip tone="info">TESTAS (laboratorija)</Chip>}
              {d.paid && paidRec.livemode === false && <Chip tone="warn">Stripe testo mokėjimas</Chip>}
              {held && <Chip tone="warn">Kūrinys laukia tavo peržiūros</Chip>}
              {d.records['review.json'] && <Chip tone="warn">Peržiūros žyma: {s(review.reason)}</Chip>}
            </div>
            <Rows rows={[
              ['Sukurtas', s(orderRec.created) ? isoTime(orderRec.created) : '-'],
              ['Kalba', s(spec.lang) || s(orderRec.lang) || '-'],
              ['Kūrinys', d.paid ? `${s(spec.eyes)} ${n(spec.eyes) === 1 ? 'akis' : 'akys'}, ${STYLE_LT[s(spec.style)] || s(spec.style)}, išdėstymas ${s(spec.layout) || '-'}`
                : s(obj(checkout.spec).style) ? `mokėjimas pradėtas: ${s(obj(checkout.spec).eyes)} akys, ${STYLE_LT[s(obj(checkout.spec).style)] || s(obj(checkout.spec).style)}` : 'neapmokėtas'],
              ['Vardai ant kūrinio', s(spec.names) || '-'],
              ['Pavadinimas', s(spec.title) || '-'],
              ['Kaina', d.paid ? `${fmtEur(n(paidRec.amount_total))}${paidRec.amount_mismatch ? ' (nesutampa su kainoraščiu!)' : ''}` : checkout.amount ? fmtEur(n(checkout.amount)) : '-'],
              ['Apmokėta', d.paid ? `${isoTime(paidRec.paid_iso)} per ${s(paidRec.source)}` : '-'],
              ['Pirkėjo el. paštas', d.email || '-'],
              ['Stripe sesija', s(paidRec.session_id) || s(checkout.session_id) || '-'],
            ]} />
          </section>

          {d.paid && (
            <section className={`${CARD} flex flex-col gap-3`}>
              <h3 className="text-sm font-bold">Sutikimas ir laiškai</h3>
              {d.consent?.text ? (
                <blockquote className="border-l-2 border-[#f5c542]/60 pl-3 text-sm text-white/85 break-words">{d.consent.text}</blockquote>
              ) : <Notice tone="warn">Sutikimas neužfiksuotas.</Notice>}
              <Rows rows={[
                ['Sutikimo laikas', d.consent?.at ? isoTime(d.consent.at) : '-'],
                ['Teksto versija', `${d.consent?.version || '-'} (${d.consent?.lang || '-'})`],
                ['Patvirtinimo laiškas', d.records['mail_delivery.json'] ? `${s(mail.state)}${s(mail.result) ? `, ${RESULT_LT[s(mail.result)] || s(mail.result)}` : ''}, ${isoTime(mail.t)}${mail.by === 'owner' ? ' (pažymėjai ranka)' : ''}` : 'dar nesiųstas'],
                ['Laiškai „paruošta“', d.log.filter((l) => l.action === 'release' || l.action === 'resend_ready').map((l) => `${fmtTime(l.t)} ${l.action} ${l.ok ? 'ok' : 'nepavyko'}`).join('; ') || '-'],
                ['Gamybos pradžia', d.records['making.json'] ? isoTime(rec('making.json').t) : '-'],
                ['Pristatymas', d.records['delivery.json'] ? `${isoTime(delivery.created)}${delivery.needs_review ? ', patikra liepė peržiūrėti' : ''}${d.records['release.json'] ? `, išleista ${isoTime(rec('release.json').t)}` : ''}` : '-'],
                ['Atsisakyta', d.records['withdrawn.json'] ? isoTime(rec('withdrawn.json').t ?? rec('withdrawn.json').iso) : '-'],
                ['Failai ištrinti', d.records['deleted.json'] ? isoTime(rec('deleted.json').t) : d.records['expired.json'] ? isoTime(rec('expired.json').t) : '-'],
              ]} />
            </section>
          )}

          <section className={`${CARD} flex flex-col gap-3`}>
            <h3 className="text-sm font-bold">Veiksmai</h3>
            <div className="flex flex-wrap gap-2">
              {d.paid && !d.lab && (
                <>
                  <button type="button" className={BTN} disabled={!d.can.email} onClick={() => setConfirm({
                    title: 'Siųsti patvirtinimo laišką', confirmLabel: 'Siųsti',
                    text: mail.state === 'sent' ? 'Patvirtinimas jau buvo išsiųstas. Pirkėjas gaus tą patį laišką dar kartą (kopiją).' : 'Bandoma išsiųsti patvirtinimo laišką dar kartą. Kai jis išeis, užsakymas tęsiasi.',
                    run: () => act('resend_confirmation', {}, (x) => `Patvirtinimo laiškas: ${mailWord(x)}${x.hold_cleared ? '. Peržiūros žyma nuimta.' : '.'}`),
                  })}>Siųsti patvirtinimą</button>
                  {held ? (
                    <button type="button" className={BTN} onClick={() => setConfirm({
                      title: 'Išleisti kūrinį', confirmLabel: 'Išleisti',
                      text: 'Kūrinys taps atsisiunčiamas užsakymo puslapyje. Prieš tai peržiūrėk 4K kūrinį žemiau.',
                      option: { label: 'Išsiųsti pirkėjui laišką „paruošta“', value: true },
                      run: (mailIt) => act('release', { mail: mailIt }, (x) => `Išleista. Laiškas: ${x.mail ? RESULT_LT[s(x.mail)] || s(x.mail) : 'nesiųstas'}.`),
                    })}>Išleisti kūrinį</button>
                  ) : d.records['delivery.json'] ? (
                    <button type="button" className={BTN} disabled={!d.can.email} onClick={() => setConfirm({
                      title: 'Siųsti laišką „paruošta“', confirmLabel: 'Siųsti',
                      text: 'Pirkėjas gaus trumpą laišką su užsakymo puslapio nuoroda.',
                      run: () => act('resend_ready', {}, (x) => `Laiškas „paruošta“: ${mailWord(x)}.`),
                    })}>Siųsti „paruošta“</button>
                  ) : null}
                  {d.records['review.json'] && (
                    <button type="button" className={BTN} onClick={() => setConfirm({
                      title: 'Nuimti peržiūros žymą', confirmLabel: 'Nuimti',
                      text: `Priežastis: ${s(review.reason)}. Nuėmus užsakymo puslapis vėl galės gaminti akis (kitas bandymas kainuoja dar vieną 4K).`,
                      run: () => act('clear_review', {}, (x) => (x.removed ? 'Žyma nuimta.' : 'Žymos nebuvo.')),
                    })}>Nuimti peržiūros žymą</button>
                  )}
                  {mail.state !== 'sent' && (
                    <button type="button" className={BTN} onClick={() => setConfirm({
                      title: 'Patvirtinimą išsiunčiau pats', confirmLabel: 'Pažymėti', danger: true,
                      text: 'Spausk tik jei pats išsiuntei pirkėjui patvirtinimą su tais pačiais tekstais (užsakymas, sutikimas, atsisakymo informacija, sąlygos). Po to užsakymas tęsiasi.',
                      run: () => act('mailed_by_hand', {}, () => 'Pažymėta: patvirtinimas išsiųstas ranka.'),
                    })}>Išsiunčiau ranka</button>
                  )}
                  {allMade && (
                    <button type="button" className={BTN} disabled={!d.can.counts} onClick={() => setConfirm({
                      title: 'Sudėti kūrinį iš naujo', confirmLabel: 'Sudėti',
                      text: 'Sudeda 4K kūrinį iš saugomų akių (po perpiešimo bus naujas failas; jei niekas nepasikeitė, tas pats). Jei patikra jį pažymės, jis lauks tavo išleidimo. Trunka 10-35 s, Gemini nekviečiamas.',
                      run: () => act('recompose', {}, (x) => `${x.changed ? 'Naujas kūrinys sudėtas' : 'Kūrinys tas pats'}${x.held ? ', laukia tavo peržiūros' : ''}.`),
                    })}>Sudėti kūrinį iš naujo</button>
                  )}
                </>
              )}
              {!d.lab && d.records['order.json'] && (
                <button type="button" className={BTN} disabled={!d.can.link} onClick={() => setConfirm({
                  title: 'Rodyti pirkėjo nuorodą', confirmLabel: 'Rodyti',
                  text: 'Parodys atsisakymo formos nuorodą (ją atidaryti saugu) ir užsakymo puslapio nuorodą, kurią tik nukopijuosi. Neatidaryk užsakymo puslapio pats: atidarius apmokėto užsakymo puslapį prasideda gamyba, ir pirkėjas netenka teisės atsisakyti.\nAbi nuorodos yra pirkėjo raktas: su jomis bet kas mato užsakymą. Siųsk jas tik pačiam pirkėjui.',
                  run: () => act('link', {}, () => 'Pirkėjo nuorodos:'),
                })}>Pirkėjo nuoroda</button>
              )}
              <button type="button" className={DANGER} onClick={() => setConfirm({
                title: 'Ištrinti failus', danger: true, confirmLabel: 'Ištrinti', typeToConfirm: order,
                text: d.paid ? 'Ištrinami visi vaizdai. Įrašai (užsakymas, mokėjimas, sutikimas, atsisakymai) lieka, užsakymo puslapis rodys „ištrinta“. To atšaukti negalima.'
                  : 'Ištrinamas visas užsakymas su visais failais. To atšaukti negalima.',
                run: () => act('delete_files', { confirm: order }, (x) => `Ištrinta failų: ${s(x.deleted)} iš ${s(x.of)}.`),
              })}>Ištrinti failus</button>
            </div>
            {d.paid && !d.can.counts && <p className={`text-xs ${MUTED}`}>Apmokėta Stripe testo režimu: šiame serveryje tam nieko negaminama.</p>}
          </section>

          {d.eyes.length > 0 && (
            <section className={`${CARD} flex flex-col gap-3`}>
              <h3 className="text-sm font-bold">Akys</h3>
              {d.eyes.map((e) => (
                <div key={e.eye} className="border-t border-white/5 pt-3 flex flex-col gap-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-semibold">Akis {e.eye}{e.master?.needs_review ? ' · reikia peržiūros' : ''}</p>
                    {eyeActions(e)}
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {e.draft?.crop_url && <Thumb src={e.draft.crop_url} alt={e.draft.crop_side ? `Iškarpa (${s(e.draft.crop_side)} px)` : 'Iškarpa'} />}
                    {e.draft?.preview_url && <Thumb src={e.draft.preview_url} alt="Patvirtinta peržiūra" />}
                    {e.master?.url && <Thumb src={e.master.url} alt="4K akis" heavy />}
                    {e.master?.first_url && <Thumb src={e.master.first_url} alt="Pirmas 4K" heavy />}
                    {e.master?.second_url && <Thumb src={e.master.second_url} alt="Antras 4K" heavy />}
                  </div>
                  {e.master && (
                    <div className="flex flex-col gap-0.5">
                      <QaLine label="Spalvų patikra (prieš nuotrauką)" qa={obj(e.master.qa)} />
                      <QaLine label="Atitiktis peržiūrai" qa={obj(e.master.preview)} />
                      <p className={`text-xs ${MUTED}`}>Piešta {fmtNum(e.master.render_seconds)} s · {fmtBytes(e.master.bytes)} · {isoTime(e.master.created)}{e.master.rerendered ? ' · perpiešta' : ''}</p>
                    </div>
                  )}
                  {e.draft && <p className={`text-xs ${MUTED}`}>Įkelta {isoTime(e.draft.uploaded)} · pad {fmtNum(e.draft.pad)}</p>}
                </div>
              ))}
            </section>
          )}

          {d.artworks.length > 0 && (
            <section className={`${CARD} flex flex-col gap-3`}>
              <h3 className="text-sm font-bold">Kūriniai</h3>
              {d.artworks.map((a) => (
                <div key={a.key} className="border-t border-white/5 pt-3 flex flex-wrap gap-3 items-start">
                  <Thumb src={a.url} alt={a.current ? 'Pristatomas kūrinys' : 'Ankstesnis kūrinys'} heavy />
                  <div className="flex flex-col gap-1 min-w-0 text-xs">
                    <p className="break-all"><code>{a.key.split('/').pop()}</code>{a.current ? ' · pristatomas' : ''}</p>
                    <p className={MUTED}>{s(a.width)}x{s(a.height)} · {fmtBytes(a.bytes)} · {isoTime(a.created)}</p>
                    <QaLine label="Patikra" qa={obj(a.qa)} />
                    <ExtLink href={a.url}>Atidaryti</ExtLink>
                  </div>
                </div>
              ))}
            </section>
          )}

          {(d.payments.length > 0 || d.refunds.length > 0) && (
            <section className={`${CARD} flex flex-col gap-3`}>
              <h3 className="text-sm font-bold">Mokėjimai</h3>
              {d.payments.map((p) => (
                <div key={p.payment_intent} className="border-t border-white/5 pt-2 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm min-w-0 break-all">
                    <p>{p.kind === 'extra' ? 'Papildomas (dvigubas) mokėjimas' : 'Užsakymo mokėjimas'}: <b>{fmtEur(p.amount)}</b>{p.live ? '' : ' (testas)'}</p>
                    <p className={`text-xs ${MUTED}`}>{p.payment_intent} · {isoTime(p.paid)}{p.refunded ? ' · grąžinta' : ''}</p>
                  </div>
                  {refundButton(p)}
                </div>
              ))}
              {!d.can.stripe && <p className={`text-xs ${MUTED}`}>Stripe šiame serveryje nenustatytas: grąžinti galima Stripe svetainėje.</p>}
              {d.records['refunded.json'] ? (
                <p className="text-xs text-emerald-200">Pažymėta, kad grąžinta: {isoTime(rec('refunded.json').t)} ({s(rec('refunded.json').by)})</p>
              ) : d.paid && (
                <div>
                  <button type="button" className={BTN} onClick={() => setConfirm({
                    title: 'Pažymėti: pinigus grąžinau', confirmLabel: 'Pažymėti',
                    text: 'Spausk, kai pinigus grąžinai pats Stripe svetainėje. Įrašas lieka prie užsakymo, o kasdienis valymas nebesiųs priminimo.',
                    run: () => act('mark_refunded', {}, () => 'Pažymėta: grąžinta.'),
                  })}>Grąžinau Stripe svetainėje</button>
                </div>
              )}
              {d.refunds.map((r, i) => (
                <p key={i} className="text-xs break-all">Grąžinimas {s(r.refund)}: {s(r.status)}, {fmtEur(n(r.amount))}, {isoTime(r.t)}</p>
              ))}
            </section>
          )}

          {withdrawals.length > 0 && (
            <section className={`${CARD} flex flex-col gap-3`}>
              <h3 className="text-sm font-bold">Atsisakymo pareiškimai</h3>
              {withdrawals.map(([p, w]) => (
                <div key={p} className="border-t border-white/5 pt-2">
                  <Rows rows={[
                    ['Gauta', isoTime(w.received)],
                    ['Rezultatas', `${s(w.outcome)} (${s(w.reason)})`],
                    ['Kas', `${s(w.name)} · ${s(w.email)}`],
                    ['Patvirtinta per', s(w.verified) || '-'],
                    ['Grąžinti iki', w.refund === 'due' ? isoTime(w.refund_by) : '-'],
                  ]} />
                </div>
              ))}
            </section>
          )}

          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Administratoriaus veiksmai su šiuo užsakymu</h3>
            {d.log.length === 0 && <p className={`text-xs ${MUTED}`}>Dar nieko.</p>}
            {d.log.map((l, i) => (
              <p key={i} className="text-xs break-words">
                {fmtTime(l.t, true)} · <b>{l.action}</b>{l.eye ? ` (akis ${l.eye})` : ''} · {l.ok ? 'pavyko' : 'nepavyko'}{l.result ? ` · ${l.result}` : ''}{l.detail ? ` · ${l.detail}` : ''}
              </p>
            ))}
          </section>

          <section className={`${CARD} flex flex-col gap-2`}>
            <h3 className="text-sm font-bold">Visi įrašai</h3>
            {Object.entries(d.records).sort(([a], [b]) => a.localeCompare(b)).map(([p, r]) => <JsonView key={p} label={p} value={r} />)}
          </section>

          <section className={`${CARD} flex flex-col gap-1`}>
            <h3 className="text-sm font-bold mb-1">Failai ({d.files.length})</h3>
            {d.files.map((f) => (
              <p key={f.path} className="text-xs break-all">{f.url ? <ExtLink href={f.url}>{f.path}</ExtLink> : f.path}</p>
            ))}
          </section>
        </>
      )}
      <ConfirmDialog spec={confirm} onClose={() => setConfirm(null)} />
    </div>
  );
};
