import React, { useEffect, useRef, useState } from 'react';
import { AlertTriangle, Check, Clock, Download, ExternalLink, Mail, RefreshCcw } from 'lucide-react';
import { ORDER_COPY, euroOf, mbOf, type OrderCopy } from './copy';
import { EMPTY_VIEW, REAL_DEPS, driveOrder, stopOf, type DriveView, type OrderLink } from './driver';
import { KEY_RE, ORDER_RE, SESSION_RE, callApi, isStatus, orderPageUrl, statusPath, type OrderState, type OrderStatus } from './api';
import { WithdrawEntry, WithdrawForm, WithdrawnCard } from './WithdrawPanel';
import { CARD, GOLD_BTN, PLAIN_BTN, Spinner } from './ui';
import { detectLang, rememberLang, type Lang } from '../try/lang';
import { clearCheckoutStorage } from '../try/checkout';
import { CONTACT_EMAIL, STYLES } from '../landing/config';
import { LEGAL_DOCS, LEGAL_LABELS, WITHDRAWAL_ONLINE, legalHref } from '../shared/legal';
import { withdrawHref } from './withdraw';

// The order and its private key come from the address (the Stripe success page and the emails link here); s is the
// Stripe session the success page names, so the payment is confirmed even before Stripe's webhook has arrived.
function readLink(): OrderLink | null {
  try {
    const q = new URLSearchParams(window.location.search);
    const o = q.get('o') || '', k = q.get('k') || '', s = q.get('s') || '';
    if (!ORDER_RE.test(o) || !KEY_RE.test(k)) return null;
    return { o, k, s: SESSION_RE.test(s) ? s : null };
  } catch { return null; }
}

const LINK: OrderLink | null = typeof window !== 'undefined' ? readLink() : null;

// ?withdraw=1: the withdrawal form (./WithdrawPanel.tsx). In this mode the page only reads the order's status and never
// asks for anything to be made, so opening the form cannot itself start the work that ends the right of withdrawal.
// Without an order link (the footer's and the legal pages' link) the customer types the order number.
function readWithdrawMode(): boolean {
  try { return new URLSearchParams(window.location.search).get('withdraw') === '1'; } catch { return false; }
}
const WITHDRAW_MODE: boolean = typeof window !== 'undefined' ? readWithdrawMode() : false;

// the states of a concluded contract: the withdrawal function stays on the page for all of them (the server decides
// whether the right still exists and says so in its answer)
const CONTRACT_STATES: readonly OrderState[] = ['pending', 'paid', 'making', 'review', 'ready'];

const secondsLeft = (until: number, now: number) => Math.max(0, Math.ceil((until - now) / 1000));

export const OrderApp: React.FC = () => {
  const [lang, setLangState] = useState<Lang>(() => detectLang());
  const C = ORDER_COPY[lang];
  const [view, setView] = useState<DriveView>(EMPTY_VIEW);
  const [running, setRunning] = useState(!!LINK && !WITHDRAW_MODE);
  const runningRef = useRef(!!LINK && !WITHDRAW_MODE);
  const [run, setRun] = useState(0);
  const [email, setEmail] = useState(false);
  const [clock, setClock] = useState(() => Date.now());
  const [makingSince, setMakingSince] = useState<number | null>(null);

  const switchLang = (l: Lang) => { if (l !== lang) { rememberLang(l); setLangState(l); } };

  useEffect(() => {
    try {
      document.documentElement.lang = lang;
      document.title = WITHDRAW_MODE ? `${C.withdraw.heading} | SnapEyes` : C.meta.title;
      document.head.querySelector<HTMLMetaElement>('meta[name="description"]')?.setAttribute('content', C.meta.description);
    } catch { /* no document */ }
  }, [lang, C]);

  // whether the delivery email is configured: only then does the page say the link is in the email
  useEffect(() => {
    let alive = true;
    fetch('/api/health', { cache: 'no-store' })
      .then((r) => r.json())
      .then((h) => { if (alive) setEmail(h?.email === true); })
      .catch(() => { /* the page works without it */ });
    return () => { alive = false; };
  }, []);

  // the withdrawal mode reads the order once, for its summary and whether there is a contract to withdraw from
  useEffect(() => {
    if (!LINK || !WITHDRAW_MODE) return;
    let alive = true;
    callApi<unknown>(statusPath(LINK.o, LINK.k, LINK.s), { timeoutMs: 25_000 }).then((r) => {
      if (!alive) return;
      if (r.ok && isStatus(r.data)) { const st = r.data; setView((v) => ({ ...v, status: st })); } else setView((v) => ({ ...v, stop: stopOf(r) }));
    });
    return () => { alive = false; };
  }, []);

  // one driver at a time: a new one starts only from "Try again" / "Check again", which show once the last has ended
  useEffect(() => {
    if (!LINK || WITHDRAW_MODE) return;
    let alive = true;
    driveOrder(LINK, REAL_DEPS, (patch) => { if (alive) setView((v) => ({ ...v, ...patch })); }, () => alive)
      .catch(() => { if (alive) setView((v) => ({ ...v, stop: 'failed', making: [], composing: false, wait: null })); })
      .finally(() => { if (alive) { runningRef.current = false; setRunning(false); } });
    return () => { alive = false; };
  }, [run]);

  const again = () => {
    if (runningRef.current) return;
    runningRef.current = true;
    setRunning(true);
    setView((v) => ({ ...v, stop: null, wait: null, making: [], composing: false }));
    setRun((r) => r + 1);
  };

  // a phone that put the tab to sleep drops the connection: coming back to the page picks the work up again
  useEffect(() => {
    if (view.stop !== 'network' || WITHDRAW_MODE) return;   // the withdrawal mode drives nothing
    const onVisible = () => { if (document.visibilityState === 'visible') again(); };
    document.addEventListener('visibilitychange', onVisible);
    return () => document.removeEventListener('visibilitychange', onVisible);
  }, [view.stop]);

  // a paid order: this tab's order and the artwork kept for the way back from Stripe are done with
  const state = view.status?.state;
  useEffect(() => {
    if (LINK && state && state !== 'unpaid') clearCheckoutStorage(LINK.o);
  }, [state]);

  // a clock for the countdowns and the time spent making
  const active = !!view.wait || view.making.length > 0 || view.composing;
  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => setClock(Date.now()), 1000);
    const first = setTimeout(() => setClock(Date.now()), 0);
    return () => { clearInterval(id); clearTimeout(first); };
  }, [active]);
  const makingNow = view.making.length > 0 || view.composing;
  useEffect(() => {
    if (!makingNow) return;
    const t = setTimeout(() => setMakingSince((s) => s ?? Date.now()), 0);
    return () => clearTimeout(t);
  }, [makingNow]);

  let content: React.ReactNode;
  const st = view.status;
  if (WITHDRAW_MODE) {
    const back = LINK ? orderPageUrl(LINK.o, LINK.k, lang) : null;
    if (LINK && !st && !view.stop) {
      content = (
        <section className={`${CARD} flex items-center gap-3`} aria-busy="true">
          <Spinner /> <span className="text-sm text-zinc-300">{C.loading}</span>
        </section>
      );
    } else if (view.stop === 'bad_link') {
      // the key does not fit: the statement can still go out with the order number alone
      content = (
        <>
          <Problem C={C} text={C.errors.bad_link} />
          <WithdrawForm C={C} lang={lang} link={null} initialOrder={LINK?.o ?? ''} amount={null} backHref={null} />
        </>
      );
    } else if (st?.state === 'withdrawn') {
      content = <><Summary C={C} st={st} lang={lang} /><WithdrawnCard C={C} lang={lang} st={st} /></>;
    } else if (st?.state === 'unpaid' && st.payment_check !== 'unavailable') {
      // (when Stripe could not be asked just now the order may well be paid: the form stays, the server decides)
      content = (
        <section data-testid="withdraw-unpaid" className={CARD}>
          <h2 className="font-luxury text-xl font-bold">{C.withdraw.heading}</h2>
          <p className="text-sm text-zinc-300 mt-2">{C.withdraw.unpaid}</p>
        </section>
      );
    } else {
      // a status that could not be read (offline, busy) still leaves the form: sending it gives its own answer
      content = (
        <>
          {st && <Summary C={C} st={st} lang={lang} />}
          <WithdrawForm C={C} lang={lang} link={LINK} amount={typeof st?.amount === 'number' ? st.amount : null} backHref={back} />
        </>
      );
    }
  } else if (!LINK) {
    content = <Problem C={C} text={C.errors.missing} />;
  } else if (view.stop) {
    content = (
      <>
        {st && <Summary C={C} st={st} lang={lang} />}
        <Problem C={C} text={C.errors[view.stop]} onRetry={view.stop === 'bad_link' || running ? undefined : again} />
      </>
    );
  } else if (!st) {
    content = (
      <section className={`${CARD} flex items-center gap-3`} aria-busy="true">
        <Spinner /> <span className="text-sm text-zinc-300">{C.loading}</span>
      </section>
    );
  } else if (st.state === 'unpaid') {
    // straight from Stripe the page asks again for a few seconds before it says "not paid"
    const checking = running;
    content = (
      <section data-testid="state-unpaid" className={CARD}>
        <h2 className="font-luxury text-xl font-bold">{C.unpaid.title}</h2>
        {checking ? (
          <p className="text-sm text-zinc-300 mt-2 flex items-center gap-2"><Spinner /> {C.unpaid.confirming}</p>
        ) : (
          <>
            <p className="text-sm text-zinc-300 mt-2">{C.unpaid.body}</p>
            <p className="text-sm text-zinc-400 mt-2">{st.expired ? C.unpaid.expired : C.unpaid.hint}</p>
            <div className={`grid gap-3 mt-4 ${st.expired ? 'grid-cols-1' : 'sm:grid-cols-2'}`}>
              {!st.expired && <button type="button" onClick={again} disabled={running} className={PLAIN_BTN}><RefreshCcw className="w-4 h-4" /> {C.unpaid.check}</button>}
              <a href={`/try?lang=${lang}`} className={PLAIN_BTN}>{C.unpaid.studio}</a>
            </div>
          </>
        )}
      </section>
    );
  } else if (st.state === 'pending') {
    // two kinds: a payment that settles later (unpaid as yet), or a paid order whose confirmation email is on its way
    const mailing = st.waiting_for === 'confirmation_email';
    content = (
      <>
        {mailing && <Summary C={C} st={st} lang={lang} />}
        <section data-testid="state-pending" data-waiting={st.waiting_for || ''} className={CARD}>
          <h2 className="font-luxury text-xl font-bold">{mailing ? C.pending.mailTitle : C.pending.title}</h2>
          <p className="text-sm text-zinc-300 mt-2">{mailing ? C.pending.mailBody : C.pending.body}</p>
          {view.wait && <p className="text-xs text-zinc-500 mt-3 flex items-center gap-2"><Clock className="w-3.5 h-3.5" /> {C.wait.confirming(secondsLeft(view.wait.until, clock))}</p>}
          {/* the email with this page's link has not gone out yet: never say it is in the email */}
          <p className="text-xs text-zinc-400 mt-3">{email && !mailing ? C.ready.email : C.ready.bookmark}</p>
        </section>
      </>
    );
  } else if (st.state === 'paid' || st.state === 'making') {
    content = (
      <>
        <Summary C={C} st={st} lang={lang} />
        <Making C={C} st={st} view={view} clock={clock} since={makingSince} email={email} />
      </>
    );
  } else if (st.state === 'review') {
    content = (
      <>
        <Summary C={C} st={st} lang={lang} />
        <section data-testid="state-review" className={CARD}>
          <h2 className="font-luxury text-xl font-bold">{C.review.title}</h2>
          <p className="text-sm text-zinc-300 mt-2">{C.review.body}</p>
        </section>
      </>
    );
  } else if (st.state === 'withdrawn') {
    content = (
      <>
        <Summary C={C} st={st} lang={lang} />
        <WithdrawnCard C={C} lang={lang} st={st} />
      </>
    );
  } else if (st.state === 'ready' && st.download) {
    content = (
      <>
        <Ready C={C} st={st} lang={lang} email={email} />
        <Summary C={C} st={st} lang={lang} />
      </>
    );
  } else if (st.state !== 'deleted') {
    // a ready reply without its link: the server never sends one, so ask again
    content = <Problem C={C} text={C.errors.failed} onRetry={running ? undefined : again} />;
  } else {
    content = (
      <>
        <Summary C={C} st={st} lang={lang} />
        <section data-testid="state-deleted" className={CARD}>
          <h2 className="font-luxury text-xl font-bold">{C.deleted.title}</h2>
          <p className="text-sm text-zinc-300 mt-2">{C.deleted.body}</p>
        </section>
      </>
    );
  }

  const mail = `mailto:${CONTACT_EMAIL}${LINK ? `?subject=${encodeURIComponent(C.contact.subject(LINK.o))}` : ''}`;
  return (
    <div className="min-h-screen bg-[#07090e] text-[#f0f3fa]">
      <header className="px-4 py-4 flex items-center justify-between gap-3 max-w-2xl mx-auto">
        <a href={`/?lang=${lang}`} className="shrink-0 font-luxury font-black tracking-wider text-lg">SNAP<span className="text-gold-gradient">EYES</span></a>
        <div className="flex items-center justify-end gap-3 min-w-0">
          <span className="min-w-0 text-[10px] uppercase tracking-widest text-zinc-500 text-right">{C.tag}</span>
          <LangSwitch C={C} lang={lang} onSwitch={switchLang} />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pb-10">
        <h1 className="font-luxury text-3xl sm:text-4xl font-bold text-center mt-2">{C.title}</h1>
        {LINK && <p data-testid="order-no" className="text-center text-xs text-zinc-500 mt-2 break-all">{C.orderNo(LINK.o)}</p>}
        <div className="mt-6 flex flex-col gap-4">
          {content}
          {!WITHDRAW_MODE && LINK && st && CONTRACT_STATES.includes(st.state) && <WithdrawEntry C={C} lang={lang} link={LINK} />}
          <p className="text-center text-xs text-zinc-400 mt-2">
            {C.contact.lead}{' '}
            <a href={mail} className="inline-flex items-center gap-1 underline underline-offset-4 decoration-white/30 hover:text-white">
              <Mail className="w-3.5 h-3.5" /> {C.contact.write(CONTACT_EMAIL)}
            </a>
          </p>
        </div>
      </main>

      {/* the legal pages open in a new tab, so an artwork being made is never interrupted; the withdrawal function, as
          on every page's foot (src/shared/legal.ts), leads to this page's own form with this order filled in */}
      <footer className="max-w-2xl mx-auto px-4 pb-10">
        <nav aria-label={LEGAL_LABELS[lang].nav} className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-zinc-400">
          {LEGAL_DOCS.map((d) => (
            <a key={d} href={legalHref(d, lang)} target="_blank" rel="noopener" className="hover:text-white hover:underline underline-offset-4 rounded-sm">
              {LEGAL_LABELS[lang][d]}
            </a>
          ))}
          {!WITHDRAW_MODE && (
            <a data-testid="footer-withdraw" href={withdrawHref(lang, LINK)} className="hover:text-white hover:underline underline-offset-4 rounded-sm">
              {WITHDRAWAL_ONLINE[lang].button}
            </a>
          )}
        </nav>
      </footer>
    </div>
  );
};

const Problem: React.FC<{ C: OrderCopy; text: string; onRetry?: () => void }> = ({ C, text, onRetry }) => (
  <section role="alert" data-testid="state-error" className="bg-rose-950/30 border border-rose-500/40 rounded-2xl p-4 sm:p-5">
    <h2 className="font-luxury text-lg font-bold text-rose-100 flex items-center gap-2"><AlertTriangle className="w-5 h-5 shrink-0 text-rose-300" /> {C.errors.title}</h2>
    <p className="text-sm text-rose-100/90 mt-2">{text}</p>
    {onRetry && (
      <button type="button" onClick={onRetry} className={`${PLAIN_BTN} mt-4 w-full sm:w-auto`}><RefreshCcw className="w-4 h-4" /> {C.errors.retry}</button>
    )}
  </section>
);

const Summary: React.FC<{ C: OrderCopy; st: OrderStatus; lang: Lang }> = ({ C, st, lang }) => {
  const n = typeof st.count === 'number' ? st.count : 0;
  if (!n) return null;
  const style = STYLES.find((s) => s.id === st.style)?.name ?? st.style;
  const layout = n > 1 && st.layout ? C.layouts[st.layout] ?? st.layout : null;
  const parts = [C.summary.eyes(n), style, layout].filter(Boolean).join(' · ');
  return (
    <section data-testid="summary" className={`${CARD} text-sm`}>
      <p className="font-semibold text-zinc-100">{parts}</p>
      {st.names && <p className="text-xs text-zinc-400 mt-1 break-words">{C.summary.inscription(st.names)}</p>}
      {typeof st.amount === 'number' && <p className="text-xs text-zinc-400 mt-1">{C.summary.paid(euroOf(st.amount, lang))}</p>}
    </section>
  );
};

const Making: React.FC<{ C: OrderCopy; st: OrderStatus; view: DriveView; clock: number; since: number | null; email: boolean }> = ({ C, st, view, clock, since, email }) => {
  const n = st.eyes.length;
  const done = st.eyes.filter((e) => e.made).length;
  // the artwork itself is one more step after the eyes
  const pct = Math.round(((done + (view.composing ? 0.5 : 0)) / (n + 1)) * 100);
  const w = view.wait;
  const line = w ? C.wait[w.reason](secondsLeft(w.until, clock))
    : view.composing ? C.making.composing
    : C.making.progress(done, n);
  return (
    <section data-testid="state-making" className={CARD} aria-busy="true">
      <h2 className="font-luxury text-xl font-bold">{C.making.title}</h2>
      <p className="text-sm text-zinc-300 mt-2">{C.making.lead}</p>
      <ul className="flex flex-wrap gap-x-3 gap-y-3 mt-4">
        {st.eyes.map((e) => {
          const busy = view.making.includes(e.eye);
          const ring = e.made ? 'border-emerald-400' : busy ? 'border-[#f5c542] animate-pulse' : 'border-white/15 opacity-60';
          return (
            <li key={e.eye} data-testid={`eye-${e.eye}`} className="w-[72px] flex flex-col items-center gap-1 text-center">
              <span className={`relative w-14 h-14 rounded-full border-2 overflow-hidden bg-white/5 ${ring}`}>
                {e.preview_url && <img src={e.preview_url} alt="" className="w-full h-full object-cover" />}
                {e.made && <span className="absolute inset-0 flex items-center justify-center bg-black/35"><Check className="w-5 h-5 text-emerald-300" /></span>}
              </span>
              <span className="text-[10px] font-bold text-zinc-300 leading-tight">{C.making.eye(e.eye)}</span>
              <span className={`text-[10px] leading-tight ${e.made ? 'text-emerald-300' : busy ? 'text-[#f5c542]' : 'text-zinc-500'}`}>
                {e.made ? C.making.done : busy ? C.making.working : C.making.waiting}
              </span>
            </li>
          );
        })}
      </ul>
      <div className="mt-4 h-2 rounded-full bg-white/10 overflow-hidden" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}>
        <div className="h-full rounded-full bg-gradient-to-r from-[#f5c542] to-[#d4af37] transition-all duration-700" style={{ width: `${Math.max(pct, 4)}%` }} />
      </div>
      <div className="flex items-start justify-between gap-3 mt-2">
        <p data-testid="making-line" className="text-xs text-zinc-300 flex items-center gap-2 min-w-0">{(view.making.length > 0 || view.composing) && !w && <Spinner />}<span>{line}</span></p>
        {since !== null && <span className="shrink-0 text-[11px] font-mono text-zinc-500">{C.making.elapsed(Math.max(0, Math.round((clock - since) / 1000)))}</span>}
      </div>
      <p className="text-xs text-amber-100/90 bg-amber-950/25 border border-amber-500/30 rounded-xl p-3 mt-4">
        {C.making.keepOpen} {email ? C.making.closeEmail : C.making.closeNoEmail}
      </p>
    </section>
  );
};

const Ready: React.FC<{ C: OrderCopy; st: OrderStatus; lang: Lang; email: boolean }> = ({ C, st, lang, email }) => {
  const d = st.download!;
  const w = typeof d.width === 'number' ? d.width : null;
  const h = typeof d.height === 'number' ? d.height : null;
  return (
    <section data-testid="state-ready" className={CARD}>
      <h2 className="font-luxury text-xl font-bold">{C.ready.title}</h2>
      <div className="mt-4 rounded-2xl overflow-hidden border border-white/10 bg-black" style={w && h ? { aspectRatio: `${w} / ${h}` } : undefined}>
        <img src={d.url} alt={C.ready.alt} decoding="async" className="w-full h-full object-contain" />
      </div>
      <a data-testid="download" href={d.download_url} className={`${GOLD_BTN} mt-4`}><Download className="w-4 h-4 shrink-0" /> {C.ready.download}</a>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 mt-3">
        <a href={d.url} target="_blank" rel="noopener noreferrer" className="text-xs text-zinc-300 underline underline-offset-4 decoration-white/30 hover:text-white inline-flex items-center gap-1">
          <ExternalLink className="w-3.5 h-3.5" /> {C.ready.open}
        </a>
        {w && h && typeof d.bytes === 'number' && <span className="text-[11px] text-zinc-500">{C.ready.details(w, h, mbOf(d.bytes, lang))}</span>}
      </div>
      <p className="text-xs text-zinc-300 mt-4">{C.ready.link}</p>
      <p className="text-xs text-zinc-400 mt-1">{email ? C.ready.email : C.ready.bookmark}</p>
    </section>
  );
};

/** EN/DE, as on /try and the landing page. */
const LangSwitch: React.FC<{ C: OrderCopy; lang: Lang; onSwitch: (l: Lang) => void }> = ({ C, lang, onSwitch }) => (
  <div role="group" aria-label={C.switchLabel} className="shrink-0 flex items-center rounded-full border border-white/10 p-0.5 text-[11px] font-semibold tracking-[0.12em]">
    {(['en', 'de'] as const).map((l) => (
      <button key={l} type="button" onClick={() => onSwitch(l)} aria-pressed={lang === l} lang={l} title={l === 'en' ? 'English' : 'Deutsch'}
        className={`min-w-[40px] rounded-full px-2.5 py-1.5 uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] ${lang === l ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'}`}>
        {l}
      </button>
    ))}
  </div>
);
