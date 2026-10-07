// The online withdrawal function on the /order page (Art. 11a Directive 2011/83/EU as amended by Directive (EU)
// 2023/2673; § 356a BGB). Three parts:
//  - WithdrawEntry: on the order page, a button with the statutory words ("Withdraw from contract here" / "Vertrag hier
//    widerrufen") that opens the form. It is a link to the page's withdrawal mode (./withdraw.ts withdrawHref), which
//    never starts making anything, so opening the form cannot itself end the right of withdrawal.
//  - WithdrawForm: name, email for the receipt, the order (filled in from the link), the statement as it is sent, and
//    the confirmation button with the statutory words ("Confirm withdrawal" / "Widerruf bestätigen").
//  - the honest answer: the server alone decides whether the withdrawal takes effect (nothing made yet) or the right
//    had already ended (making had started after the customer's express consent and its email confirmation), and
//    the page says exactly that, with the time the statement arrived.
import React, { useRef, useState } from 'react';
import { ExternalLink, FileX2 } from 'lucide-react';
import { dateOf, whenOf, type OrderCopy } from './copy';
import { adoptMarket, money } from '../shared/markets';
import type { OrderLink } from './driver';
import type { OrderStatus } from './api';
import { cleanOrder, emailOk, nameOk, newNonce, orderOk, readWithdrawal, sendWithdrawal, withdrawHref, NAME_MAX, EMAIL_MAX, type WithdrawDone, type WithdrawError } from './withdraw';
import { WITHDRAWAL_ONLINE, legalEdition, legalHref } from '../shared/legal';
import { useMarket } from '../shared/useMarket';
import type { Lang } from '../try/lang';
import { CARD, LINK, PLAIN_BTN, Spinner } from './ui';

const FIELD = 'mt-1 w-full min-h-[44px] rounded-xl bg-black/40 border px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-[#f5c542]/70';
const CONFIRM_BTN = 'min-h-[48px] px-4 py-3 rounded-xl bg-[#f0f3fa] text-black text-sm font-bold flex items-center justify-center gap-2 text-center active:scale-[0.98] disabled:opacity-60';

/** An order of the Australian market (the page adopts its order's market): the line that keeps the Australian
 *  Consumer Law next to anything about the end of the right of withdrawal. */
const AclNote: React.FC<{ C: OrderCopy }> = ({ C }) =>
  legalEdition(useMarket()) === 'au' ? <p data-testid="withdraw-acl" className="text-xs text-zinc-400 mt-2 leading-relaxed">{C.withdraw.acl}</p> : null;

/** The order page's withdrawal section: what the right is, and the button to the form. */
export const WithdrawEntry: React.FC<{ C: OrderCopy; lang: Lang; link: OrderLink }> = ({ C, lang, link }) => (
  <section data-testid="withdraw-entry" aria-labelledby="withdraw-entry-h" className={CARD}>
    <h2 id="withdraw-entry-h" className="font-luxury text-lg font-bold">{C.withdraw.heading}</h2>
    <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{C.withdraw.lead}</p>
    <AclNote C={C} />
    <div className="flex flex-wrap items-center gap-x-5 gap-y-3 mt-4">
      <a data-testid="withdraw-open" href={withdrawHref(lang, link)} className={`${PLAIN_BTN} w-full sm:w-auto`}>
        <FileX2 className="w-4 h-4 shrink-0" /> {WITHDRAWAL_ONLINE[lang].button}
      </a>
      <a href={legalHref('withdrawal', lang)} target="_blank" rel="noopener" className={`text-xs text-zinc-400 inline-flex items-center gap-1 ${LINK}`}>
        <ExternalLink className="w-3.5 h-3.5" /> {C.withdraw.info}
      </a>
    </div>
  </section>
);

/** A withdrawn order, as its status reports it. */
export const WithdrawnCard: React.FC<{ C: OrderCopy; lang: Lang; st: OrderStatus }> = ({ C, lang, st }) => {
  const w = readWithdrawal(st.withdrawal);
  return (
    <section data-testid="state-withdrawn" className={CARD}>
      <h2 className="font-luxury text-xl font-bold">{C.withdraw.withdrawn.title}</h2>
      <p className="text-sm text-zinc-300 mt-2">{w?.at ? C.withdraw.withdrawn.body(whenOf(w.at, lang)) : C.withdraw.withdrawn.bodyNoTime}</p>
    </section>
  );
};

interface FormProps {
  C: OrderCopy;
  lang: Lang;
  link: OrderLink | null;      // null: opened without an order link, the customer types the order number
  initialOrder?: string;       // without a link: an order number to start from
  amount: number | null;       // what the order cost, when the page knows it
  currency?: string | null;    // ...and in which currency (the status reply's "currency"; euros when unknown)
  backHref: string | null;     // the order page itself (normal mode), when there is an order link
}

/** The withdrawal statement form and, once sent, the server's answer. */
export const WithdrawForm: React.FC<FormProps> = ({ C, lang, link, initialOrder = '', amount, currency = null, backHref }) => {
  const W = C.withdraw;
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [order, setOrder] = useState(initialOrder);
  const [tried, setTried] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<{ code: WithdrawError; at: number | null } | null>(null);
  const [done, setDone] = useState<{ d: WithdrawDone; email: string } | null>(null);
  // one nonce for this form: sending again after a lost answer finds the same statement on the server
  const [nonce] = useState(newNonce);
  const refs = { name: useRef<HTMLInputElement>(null), email: useRef<HTMLInputElement>(null), order: useRef<HTMLInputElement>(null) };

  const n = name.trim().replace(/\s+/g, ' '), e = email.trim(), o = link ? link.o : cleanOrder(order);
  const bad = { name: !nameOk(n), email: !emailOk(e), order: !link && !orderOk(o) };

  if (done) return <WithdrawResult C={C} lang={lang} d={done.d} email={done.email} amount={done.d.amount ?? amount} currency={done.d.amount ? done.d.currency : currency} backHref={backHref} />;

  const submit = async (ev: React.FormEvent) => {
    ev.preventDefault();
    if (sending) return;
    setTried(true);
    const first = (['name', 'email', 'order'] as const).find((f) => bad[f]);
    if (first) { refs[first].current?.focus(); return; }
    setSending(true); setError(null);
    const out = await sendWithdrawal({ order: o, k: link?.k ?? null, name: n, email: e, lang, nonce });
    setSending(false);
    if (out.kind === 'done') {
      // the order's own market, as the server names it: the Australian note and the links follow the order, not a
      // market this browser remembers
      adoptMarket(out.done.market);
      setDone({ d: out.done, email: e });
    } else {
      setError({ code: out.code, at: out.at });
    }
  };

  const invalid = (f: keyof typeof bad) => tried && bad[f];
  const border = (f: keyof typeof bad) => (invalid(f) ? 'border-rose-400/70' : 'border-white/15');
  return (
    <section data-testid="withdraw-form" aria-labelledby="withdraw-h" className={CARD}>
      <h2 id="withdraw-h" className="font-luxury text-xl font-bold">{W.heading}</h2>
      <p className="text-sm text-zinc-300 mt-2">{W.formLead(WITHDRAWAL_ONLINE[lang].confirm)}</p>
      <p data-testid="withdraw-statement" className="text-sm text-zinc-100 mt-3 bg-white/5 border border-white/10 rounded-xl p-3 break-words">
        {link ? W.statement(link.o) : W.statementNoOrder}
      </p>
      {/* after the statement the lead introduces, never between them: the note is not part of what is sent */}
      <AclNote C={C} />
      <form noValidate onSubmit={submit} className="mt-4 flex flex-col gap-4">
        <label className="block text-xs font-semibold text-zinc-300">
          {W.name}
          <input ref={refs.name} data-testid="withdraw-name" type="text" name="name" autoComplete="name" maxLength={NAME_MAX} value={name}
            onChange={(ev) => setName(ev.target.value)} disabled={sending} aria-invalid={invalid('name') || undefined}
            aria-describedby={invalid('name') ? 'withdraw-name-err' : undefined} className={`${FIELD} ${border('name')}`} />
          {invalid('name') && <span id="withdraw-name-err" className="block mt-1 text-[11px] font-normal text-rose-200">{W.invalid.name}</span>}
        </label>
        <label className="block text-xs font-semibold text-zinc-300">
          {W.email}
          <input ref={refs.email} data-testid="withdraw-email" type="email" name="email" autoComplete="email" inputMode="email" maxLength={EMAIL_MAX}
            value={email} onChange={(ev) => setEmail(ev.target.value)} disabled={sending} aria-invalid={invalid('email') || undefined}
            aria-describedby={`withdraw-email-hint${invalid('email') ? ' withdraw-email-err' : ''}`} className={`${FIELD} ${border('email')}`} />
          <span id="withdraw-email-hint" className="block mt-1 text-[11px] font-normal text-zinc-400">{link ? W.emailHint : W.emailHintNoLink}</span>
          {invalid('email') && <span id="withdraw-email-err" className="block mt-1 text-[11px] font-normal text-rose-200">{W.invalid.email}</span>}
        </label>
        <label className="block text-xs font-semibold text-zinc-300">
          {W.order}
          {link ? (
            <input data-testid="withdraw-order" type="text" name="order" value={link.o} readOnly aria-readonly="true"
              className={`${FIELD} border-white/10 text-zinc-400 font-mono`} />
          ) : (
            <>
              <input ref={refs.order} data-testid="withdraw-order" type="text" name="order" autoComplete="off" autoCapitalize="none" spellCheck={false}
                maxLength={64} value={order} onChange={(ev) => setOrder(ev.target.value)} disabled={sending}
                aria-invalid={invalid('order') || undefined} aria-describedby={`withdraw-order-hint${invalid('order') ? ' withdraw-order-err' : ''}`}
                className={`${FIELD} ${border('order')} font-mono`} />
              <span id="withdraw-order-hint" className="block mt-1 text-[11px] font-normal text-zinc-400">{W.orderHint}</span>
              {invalid('order') && <span id="withdraw-order-err" className="block mt-1 text-[11px] font-normal text-rose-200">{W.invalid.order}</span>}
            </>
          )}
        </label>
        {error && (
          <p role="alert" data-testid="withdraw-error" data-code={error.code} className="text-xs text-rose-100 bg-rose-950/40 border border-rose-500/40 rounded-xl p-3 break-words">
            {error.code === 'unmatched' ? W.errors.unmatched(error.at ? whenOf(error.at, lang) : null) : W.errors[error.code]}
          </p>
        )}
        <div className="flex flex-col-reverse sm:flex-row sm:items-center gap-3">
          {backHref && <a data-testid="withdraw-back" href={backHref} className={PLAIN_BTN}>{W.cancel}</a>}
          <button data-testid="withdraw-confirm" type="submit" disabled={sending} aria-busy={sending || undefined} className={`${CONFIRM_BTN} sm:flex-1`}>
            {sending && <Spinner />} {sending ? W.sending : WITHDRAWAL_ONLINE[lang].confirm}
          </button>
        </div>
      </form>
    </section>
  );
};

const WithdrawResult: React.FC<{ C: OrderCopy; lang: Lang; d: WithdrawDone; email: string; amount: number | null; currency: string | null; backHref: string | null }> = ({ C, lang, d, email, amount, currency, backHref }) => {
  const D = C.withdraw.done;
  const price = amount ? money(amount, currency ?? 'eur', lang) : null;
  const settling = d.reason === 'payment_settling' || d.reason === 'payment_unknown';
  const refund = settling ? D.settling
    : d.refundStarted && price ? D.refundStarted(price)
    : price && d.refundBy ? D.refundBy(price, dateOf(d.refundBy, lang))
    : price ? D.refund(price) : D.refundNoAmount;
  return (
    <section role="status" data-testid="withdraw-done" data-effective={String(d.effective)} className={CARD}>
      <h2 className="font-luxury text-xl font-bold">{d.effective === false ? D.lapsedTitle : D.effectiveTitle}</h2>
      {d.at && <p data-testid="withdraw-at" className="text-sm text-zinc-200 mt-2">{D.received(whenOf(d.at, lang))}</p>}
      {d.effective === null ? (
        <p className="text-sm text-zinc-300 mt-2">{D.checking}</p>
      ) : d.effective ? (
        <>
          <p className="text-sm text-zinc-300 mt-2">{D.effective}</p>
          <p data-testid="withdraw-refund" className="text-sm text-zinc-300 mt-2">{refund}</p>
        </>
      ) : (
        <>
          <p className="text-sm text-zinc-300 mt-2">{d.reason === 'period_over' ? D.lapsedPeriod : D.lapsed}</p>
          <p className="text-xs text-zinc-400 mt-2">{D.lapsedHelp}</p>
          <AclNote C={C} />
        </>
      )}
      {d.mail === 'sent' && <p data-testid="withdraw-mail" className="text-xs text-zinc-400 mt-3 break-words">{D.mailSent(email)}</p>}
      {d.mail === 'redirected' && <p data-testid="withdraw-mail" className="text-xs text-zinc-400 mt-3 break-words">{D.mailRedirected}</p>}
      {d.mail === 'later' && <p data-testid="withdraw-mail" className="text-xs text-amber-100/90 mt-3 break-words">{D.mailLater(email)}</p>}
      {d.mail === 'failed' && <p data-testid="withdraw-mail" className="text-xs text-amber-100/90 mt-3 break-words">{D.mailFailed(email)}</p>}
      {backHref && <a data-testid="withdraw-back" href={backHref} className={`${PLAIN_BTN} mt-4 w-full sm:w-auto`}>{C.withdraw.back}</a>}
    </section>
  );
};
