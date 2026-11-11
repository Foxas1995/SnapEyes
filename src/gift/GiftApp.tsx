import React, { useEffect, useState } from 'react';
import { Check, Copy, Gift, Lock, Mail, Printer } from 'lucide-react';
import { GIFT_COPY, type GiftKind } from './copy';
import { DEFAULT_MARKET, MARKETS, money, withMarket } from '../shared/markets';
import { useMarket } from '../shared/useMarket';
import { callApi } from '../order/api';
import { CARD, GOLD_BTN, PLAIN_BTN } from '../order/ui';
import { Dot } from '../motion/Tick';
import { detectLang, rememberLang, type Lang } from '../try/lang';
import { LANG_NAMES } from '../shared/lang';
import { LEGAL_DOCS, LEGAL_LABELS, legalHref } from '../shared/legal';
import { CONTACT_EMAIL } from '../landing/config';
import { BrandPicture } from '../shared/BrandLogo';
import { giftMarket } from '../shared/gift';
import './gift.css';

// The gift voucher page (/gift; api/_lib/voucher.py). Without ?s= it sells a voucher: the two kinds with their prices (the server's standard euro list, GET
// /api/checkout), how it works, and the button to Stripe's page (POST /api/checkout {gift: {kind}}). With ?s=<Stripe session> (Stripe's success page) it asks
// GET /api/checkout?gift=<session> until the payment is confirmed and shows the code, its value and its last day, a copy button and a card to print.
// ?cancelled=1: Stripe's back link. The page carries no third-party script and sends no referrer (the session id in its address shows the code).

const SESSION_RE = /^cs_(test|live)_[A-Za-z0-9]{8,240}$/;
const LANGS: readonly Lang[] = ['en', 'de', 'lt', 'hu', 'hr'];
const KINDS: readonly GiftKind[] = ['one', 'two'];
const PICTURE: Record<GiftKind, string> = { one: '/assets/atelier/style-celestial-gold-480.webp', two: '/assets/atelier/style-clean-duo-480.webp' };

interface Ready { state: 'ready'; code: string; kind: GiftKind; value: number; currency: string; valid_until: string | null; mail?: string }
type Status = { state: 'idle' } | { state: 'pending' | 'slow' | 'expired' | 'unknown' } | Ready;

function readQuery(): { s: string | null; cancelled: boolean } {
  try {
    const q = new URLSearchParams(window.location.search);
    const s = q.get('s') || '';
    return { s: SESSION_RE.test(s) ? s : null, cancelled: q.get('cancelled') === '1' };
  } catch { return { s: null, cancelled: false }; }
}
const QUERY = typeof window !== 'undefined' ? readQuery() : { s: null, cancelled: false };

/** A day "YYYY-MM-DD" as the page's language writes it. */
function dayText(day: string | null, lang: Lang): string {
  if (!day || !/^\d{4}-\d{2}-\d{2}$/.test(day)) return day ?? '';
  const [y, m, d] = day.split('-').map(Number);
  try {
    return new Intl.DateTimeFormat(lang === 'en' ? 'en-GB' : lang, { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC' }).format(new Date(Date.UTC(y, m - 1, d)));
  } catch { return day; }
}

export const GiftApp: React.FC = () => {
  const pageMarket = useMarket();
  // vouchers are sold in euros on the markets of the EU edition: elsewhere the page sells the default market's voucher and says so
  const market = giftMarket(pageMarket) ? pageMarket : DEFAULT_MARKET;
  const [lang, setLang] = useState<Lang>(() => detectLang(market));
  const C = GIFT_COPY[lang];
  const [kind, setKind] = useState<GiftKind>('one');
  const [prices, setPrices] = useState<Record<GiftKind, number>>(() => ({
    one: MARKETS[market].prices.one_eye_art, two: MARKETS[market].prices.two_eyes,
  }));
  const [open, setOpen] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<keyof typeof C.errors | null>(null);
  const [status, setStatus] = useState<Status>(QUERY.s ? { state: 'pending' } : { state: 'idle' });
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    try {
      document.documentElement.lang = lang;
      document.title = C.meta.title;
      document.head.querySelector<HTMLMetaElement>('meta[name="description"]')?.setAttribute('content', C.meta.description);
    } catch { /* no document */ }
  }, [lang, C]);

  // whether vouchers can be bought here now, and the server's standard prices (no visitor id is sent: never a price test's list)
  useEffect(() => {
    if (QUERY.s) return;
    let gone = false;
    void callApi<{ open?: boolean; markets?: Record<string, { prices?: Record<string, number> }> }>('/api/checkout').then((r) => {
      if (gone) return;
      const p = r.data?.markets?.[market]?.prices;
      if (p && typeof p.one_eye_art === 'number' && typeof p.two_eyes === 'number') setPrices({ one: p.one_eye_art, two: p.two_eyes });
      setOpen(r.ok && r.data?.open === true);
    });
    return () => { gone = true; };
  }, [market]);

  // after the payment: ask until the code is there (about a minute), then say it comes by email
  useEffect(() => {
    if (!QUERY.s) return;
    let gone = false;
    let tries = 0;
    const ask = async () => {
      if (gone) return;
      tries += 1;
      const r = await callApi<Omit<Partial<Ready>, 'state'> & { state?: string }>(`/api/checkout?gift=${encodeURIComponent(QUERY.s!)}`, { timeoutMs: 25_000 });
      if (gone) return;
      const d = r.data;
      if (r.ok && d?.state === 'ready' && typeof d.code === 'string' && (d.kind === 'one' || d.kind === 'two') && typeof d.value === 'number') {
        setStatus({ state: 'ready', code: d.code, kind: d.kind, value: d.value, currency: d.currency ?? 'EUR', valid_until: d.valid_until ?? null, mail: d.mail });
        return;
      }
      if (r.ok && (d?.state === 'expired' || d?.state === 'unknown')) { setStatus({ state: d.state }); return; }
      if (tries >= 20) { setStatus({ state: 'slow' }); return; }
      setTimeout(() => void ask(), 3000);
    };
    void ask();
    return () => { gone = true; };
  }, []);

  const switchLang = (l: Lang) => { if (l !== lang) { rememberLang(l); setLang(l); } };
  const fmt = (c: number) => money(c, 'eur', lang);

  const buy = async () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    const r = await callApi<{ url?: string }>('/api/checkout', { body: { gift: { kind }, market, lang }, timeoutMs: 30_000 });
    if (r.ok && typeof r.data?.url === 'string' && r.data.url.startsWith('https://')) {
      window.location.assign(r.data.url);
      return;   // leaving for Stripe: the button stays busy
    }
    setBusy(false);
    if (r.reason === 'payments_not_configured' || r.reason === 'storage_not_configured') { setOpen(false); return; }
    setError(r.status === 0 ? 'network' : r.reason === 'payments_busy' || r.reason === 'storage_busy' ? 'busy' : 'failed');
  };

  const copy = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch { /* the code stays on screen to copy by hand */ }
  };

  let content: React.ReactNode;
  if (status.state === 'ready') {
    content = (
      <>
        <section data-testid="gift-ready" className={`${CARD} gift-noprint`}>
          <h2 className="font-luxury text-2xl font-bold text-center">{C.ready.title}</h2>
          <p data-testid="gift-code-shown" className="mt-4 text-center font-mono text-2xl sm:text-3xl tracking-[0.18em] text-gold-light select-all break-all">{status.code}</p>
          <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
            <dt className="text-zinc-400">{C.ready.rows.value}</dt><dd className="text-zinc-100">{fmt(status.value)}</dd>
            <dt className="text-zinc-400">{C.ready.rows.for}</dt><dd className="text-zinc-100">{C.kinds[status.kind].note}</dd>
            {status.valid_until && <><dt className="text-zinc-400">{C.ready.rows.until}</dt><dd className="text-zinc-100">{dayText(status.valid_until, lang)}</dd></>}
          </dl>
          {(status.mail === 'sent' || status.mail === 'done') && (
            <p className="mt-3 text-xs text-emerald-200 flex items-center gap-1.5"><Mail className="w-3.5 h-3.5 shrink-0" /> {C.ready.mailed}</p>
          )}
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button type="button" data-testid="gift-copy" onClick={() => void copy(status.code)} className={PLAIN_BTN}>
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />} {copied ? C.ready.copied : C.ready.copy}
            </button>
            <button type="button" data-testid="gift-print" onClick={() => window.print()} className={PLAIN_BTN}>
              <Printer className="w-4 h-4" /> {C.ready.print}
            </button>
          </div>
          <p className="mt-4 text-[11px] text-zinc-400">{C.rules}</p>
        </section>
        {/* the card to print (gift.css: only this is printed) */}
        <section aria-hidden="true" className="gift-card">
          <p className="gift-card-brand">SnapEyes</p>
          <p className="gift-card-heading">{C.card.heading}</p>
          <p className="gift-card-line">{C.card.line}</p>
          <img className="gift-card-art" src={PICTURE[status.kind]} alt="" />
          <p className="gift-card-code">{status.code}</p>
          <p className="gift-card-how">{C.card.how}</p>
          {status.valid_until && <p className="gift-card-until">{C.card.until(dayText(status.valid_until, lang))}</p>}
        </section>
        <a href={withMarket(`/gift?lang=${lang}`)} className="gift-noprint text-center text-sm text-zinc-300 underline underline-offset-4 decoration-white/30 hover:text-white">{C.ready.again}</a>
      </>
    );
  } else if (status.state !== 'idle') {
    const line = status.state === 'pending' ? C.waiting : status.state === 'slow' ? C.slow : status.state === 'expired' ? C.expired : C.unknown;
    content = (
      <section data-testid={`gift-${status.state}`} className={CARD}>
        <p className="text-sm text-zinc-200 flex items-center gap-2">{status.state === 'pending' && <Dot />} {line}</p>
        {status.state !== 'pending' && (
          <a href={withMarket(`/gift?lang=${lang}`)} className="mt-3 inline-block text-sm text-zinc-300 underline underline-offset-4 decoration-white/30 hover:text-white">{C.ready.again}</a>
        )}
      </section>
    );
  } else {
    const disabled = busy || open !== true;
    content = (
      <>
        {QUERY.cancelled && <p role="status" data-testid="gift-cancelled" className="text-xs text-amber-100 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3">{C.cancelled}</p>}
        <section className={CARD} aria-labelledby="gift-choose">
          <h2 id="gift-choose" className="text-[10px] uppercase tracking-widest text-zinc-400">{C.choose}</h2>
          <div role="radiogroup" aria-labelledby="gift-choose" className="mt-3 grid grid-cols-2 gap-3">
            {KINDS.map((k) => (
              <button key={k} type="button" role="radio" aria-checked={kind === k} data-testid={`gift-kind-${k}`} onClick={() => setKind(k)} disabled={busy}
                className={`text-left rounded-xl border p-2 transition-colors ${kind === k ? 'border-gold/70 bg-gold/10' : 'border-white/10 bg-white/5 hover:border-white/25'}`}>
                <img src={PICTURE[k]} alt={C.kinds[k].alt} width={480} height={480} loading="lazy" className="w-full aspect-square object-cover rounded-lg" />
                <span className="mt-2 block text-sm font-semibold text-zinc-100">{C.kinds[k].name}</span>
                <span className="block font-luxury text-lg font-bold text-gold-light whitespace-nowrap">{fmt(prices[k])}</span>
                <span className="block text-[11px] text-zinc-300 mt-1 leading-snug">{C.kinds[k].note}</span>
              </button>
            ))}
          </div>
          {!giftMarket(pageMarket) && <p className="mt-3 text-[11px] text-zinc-400">{C.euroOnly}</p>}
          <h2 className="mt-5 text-[10px] uppercase tracking-widest text-zinc-400">{C.stepsTitle}</h2>
          <ol className="mt-2 flex flex-col gap-1.5 text-sm text-zinc-200">
            {C.steps.map((s, i) => (
              <li key={i} className="flex gap-2"><span className="text-gold-light font-semibold">{i + 1}.</span><span>{s}</span></li>
            ))}
          </ol>
          <p className="mt-3 text-[11px] text-zinc-400">{C.rules}</p>
          {open === false
            ? <p data-testid="gift-closed" className="mt-4 text-sm font-semibold text-emerald-300">{C.closed}</p>
            : (
              <button type="button" data-testid="gift-buy" onClick={() => void buy()} disabled={disabled}
                className={`mt-4 ${disabled && !busy ? 'w-full min-h-[48px] px-4 py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-zinc-500' : GOLD_BTN}`}>
                {busy ? <Dot /> : <Lock className="w-4 h-4 shrink-0" />} {C.buy(fmt(prices[kind]))}
              </button>
            )}
          {error && <p role="alert" data-testid="gift-error" className="mt-3 text-xs text-rose-200 bg-rose-950/40 border border-rose-500/40 rounded-xl p-3">{C.errors[error]}</p>}
          <p className="mt-3 text-[11px] text-zinc-400">{C.next}</p>
          <p className="mt-1 text-[11px] text-zinc-400">
            {C.accept[0]}<a href={legalHref('terms', lang, 'vouchers')} className="underline underline-offset-2 decoration-white/30 hover:text-white">{C.accept[1]}</a>{C.accept[2]}
          </p>
        </section>
      </>
    );
  }

  return (
    <div className="min-h-screen bg-[#07090e] text-[#f0f3fa]">
      <header className="gift-noprint px-4 py-4 flex items-center justify-between gap-3 max-w-2xl mx-auto">
        <a href={withMarket(`/?lang=${lang}`)} className="shrink-0 flex items-center">
          <BrandPicture className="shrink-0" imgClass="block h-11 w-auto min-[341px]:h-[50px] min-[375px]:h-14" />
        </a>
        <div role="group" aria-label={C.switchLabel} className="shrink-0 flex items-center rounded-full border border-white/10 p-0.5 text-[11px] font-semibold tracking-[0.12em]">
          {LANGS.map((l) => (
            <button key={l} type="button" onClick={() => switchLang(l)} aria-pressed={lang === l} lang={l} title={LANG_NAMES[l]}
              className={`min-w-[40px] rounded-full px-2.5 py-1.5 max-[400px]:min-w-[28px] max-[400px]:px-1.5 uppercase transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold ${lang === l ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'}`}>
              {l}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 pb-10">
        <div className="gift-noprint">
          <p className="text-center text-[10px] uppercase tracking-widest text-zinc-400 flex items-center justify-center gap-1.5"><Gift className="w-3.5 h-3.5" /> {C.tag}</p>
          {status.state === 'idle' && (
            <>
              <h1 className="font-luxury text-3xl sm:text-4xl font-bold text-center mt-2">{C.title}</h1>
              <p className="text-center text-sm text-zinc-300 mt-3 max-w-[32rem] mx-auto">{C.lead}</p>
            </>
          )}
        </div>
        <div className="mt-6 flex flex-col gap-4">
          {content}
          <p className="gift-noprint text-center text-xs text-zinc-400 mt-2">
            {C.contact}{' '}
            <a href={`mailto:${CONTACT_EMAIL}`} className="underline underline-offset-4 decoration-white/30 hover:text-white">{CONTACT_EMAIL}</a>
          </p>
        </div>
      </main>

      <footer className="gift-noprint max-w-2xl mx-auto px-4 pb-10">
        <nav aria-label={LEGAL_LABELS[lang].nav} className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-zinc-400">
          {LEGAL_DOCS.map((d) => (
            <a key={d} href={legalHref(d, lang)} className="hover:text-white hover:underline underline-offset-4 rounded-sm">{LEGAL_LABELS[lang][d]}</a>
          ))}
        </nav>
      </footer>
    </div>
  );
};
