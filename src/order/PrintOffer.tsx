import React, { useState } from 'react';
import { Gift, Lock, RefreshCcw } from 'lucide-react';
import type { OrderCopy } from './copy';
import type { OrderStatus } from './api';
import type { OrderLink } from './driver';
import { PRINT_BUSY, buyPrint, checkPrintVoucher, marketCountry, offerPrints, offerVoucher, voucherSplit, type BuyPrintOutcome, type PrintBack } from './printAddon';
import { CARD, PLAIN_BTN } from './ui';
import { NO_PRINT, PrintPick, printPart, type PrintChoice } from '../try/PrintPick';
import { defaultCountry } from '../shared/prints';
import { money } from '../shared/markets';
import { checkoutLegal } from '../shared/legal';
import { LegalParts } from '../shared/LegalLinks';
import { track } from '../shared/metaPixel';
import { Dot, Waiting } from '../motion/Tick';
import type { Lang } from '../try/lang';

// A print of the artwork, offered under a delivered artwork that has none (the status reply's print_offer; api/_lib/prints.py). The owner
// wanted the print out of the first checkout, where a big price scares, and offered once the customer has the file: so the card is calm,
// below the artwork, and nothing on it is chosen or ticked in advance. The print is a second order with its own payment page; the button
// opens Stripe's (./printAddon.ts buyPrint). After the way back from Stripe the page asks until the print is on record (the parent runs
// watchPrint and hands the result down as `back`); while a payment is being confirmed or is on record the card stays away, so a second
// payment is never invited.
// A gift voucher (the owner's decision of 2026-11-25 (value vouchers)): when the artwork was paid with one that has a balance left, the offer says so
// and the price after it, and the server applies it by itself; otherwise a small "I have a gift voucher" link opens a field for a code. Few words.

interface Props {
  C: OrderCopy;
  lang: Lang;
  link: OrderLink;
  st: OrderStatus;
  /** the order's market (the legal line's edition, the country to preselect) */
  market: string;
  back: PrintBack;
  /** whether this deployment sends e-mail (/api/health): only then the page says the confirmation comes by e-mail */
  email: boolean;
  /** read the order's status again (the offer with the server's numbers of now, or the print another tab bought) */
  onReload: () => void;
  /** ask about the payment again after the watch gave up (slow) */
  onRecheck: () => void;
  /** the leap to Stripe's page (the tests replace it) */
  go?: (url: string) => void;
  /** the request that opens the payment page (the tests replace it) */
  buy?: typeof buyPrint;
  /** the state the card starts in (the tests draw its states with it; the page starts with nothing chosen and nothing ticked) */
  initial?: { choice?: PrintChoice; consent?: boolean; error?: OfferError; typed?: { code: string; value: number }; field?: boolean };
  /** the check of a typed voucher code (the tests replace it) */
  checkVoucher?: typeof checkPrintVoucher;
}

export type OfferError = Exclude<Extract<BuyPrintOutcome, { kind: 'error' }>['code'], 'has'>;

export const PrintOffer: React.FC<Props> = ({ C, lang, link, st, market, back, email, onReload, onRecheck, go, buy, initial, checkVoucher }) => {
  const [choice, setChoice] = useState<PrintChoice>(initial?.choice ?? NO_PRINT);
  const [consent, setConsent] = useState(initial?.consent ?? false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<OfferError | null>(initial?.error ?? null);
  // a voucher code typed into the offer and accepted by the server (its balance), the field, the code being typed, and why a code was refused
  const [typed, setTyped] = useState<{ code: string; value: number } | null>(initial?.typed ?? null);
  const [field, setField] = useState(initial?.field ?? false);
  const [code, setCode] = useState('');
  const [checking, setChecking] = useState(false);
  const [vWhy, setVWhy] = useState<'bad' | 'artwork' | null>(null);
  const W = C.offer;
  const V = W.voucher;
  const offered = st.print ? [] : offerPrints(st);
  const fmt = (c: number) => money(c, 'eur', lang);
  const part = printPart(choice, offered);
  // the balance that pays for the print: the voucher the artwork was paid with (the server applies it), else a code typed here
  const auto = offerVoucher(st);
  const balance = auto || typed?.value || 0;
  const split = part && balance ? voucherSplit(part.price + part.ship, balance) : null;
  const legal = checkoutLegal(lang, market);
  // the print box's words: the server's (it records a fingerprint of its own text), else the page's copy of the same words
  const consentText = st.print_offer?.consent?.[lang] || legal.printConsent;

  const onChoice = (c: PrintChoice) => {
    const p = c.product ? offered.find((x) => x.id === c.product) : undefined;
    // a print chosen for the first time: the country of the order's own market, when prints ship there, is preselected (the customer can change it)
    setChoice(p && !c.country ? { ...c, country: defaultCountry(marketCountry(market), p.ship) } : c);
    setError(null);
  };

  const press = async () => {
    if (busy || !part || !choice.product || !consent) return;
    setBusy(true);
    setError(null);
    const out = await (buy ?? buyPrint)(link, { product: choice.product, country: choice.country }, lang, part.price + part.ship, undefined, auto ? null : typed?.code ?? null);
    if (out.kind === 'redirect') {
      track('InitiateCheckout', { category: 'print' }, undefined, true);       // the Meta pixel (src/shared/metaPixel.ts): off to Stripe's payment page
      (go ?? ((u: string) => window.location.assign(u)))(out.url);
      return;   // leaving for Stripe: the button stays busy
    }
    setBusy(false);
    if (out.code === 'changed' || out.code === 'unavailable' || out.code === 'has') onReload();   // the offer as the server has it now, or the print the order already has
    if (out.code === 'voucher') { setTyped(null); onReload(); }       // the code cannot pay (any more): it is taken off, the offer read again
    if (out.code !== 'has') setError(out.code);
  };

  const note = back ? (
    <section data-testid="print-back" data-state={back} role="status" className={`${CARD} text-sm`}>
      {back === 'checking' ? (
        <p className="text-zinc-300 flex items-center gap-2"><Waiting /> {W.checking}</p>
      ) : back === 'done' ? (
        <p className="text-zinc-200">{W.done}{email ? ` ${W.doneEmail}` : ''}</p>
      ) : (
        <p className="text-zinc-300">{W[back]}</p>
      )}
      {back === 'slow' && (
        <button type="button" data-testid="print-recheck" onClick={onRecheck} className={`${PLAIN_BTN} mt-3 w-full sm:w-auto`}><RefreshCcw className="w-4 h-4" /> {C.unpaid.check}</button>
      )}
    </section>
  ) : null;

  if (!offered.length || PRINT_BUSY.includes(back)) return note;

  const blockedBy = !choice.product ? 'product' : !choice.country || !part ? 'country' : !consent ? 'consent' : null;
  const disabled = busy || blockedBy !== null;
  const errorText = error === 'changed' ? W.changed : error === 'unavailable' ? W.unavailable : error === 'voucher' ? V.bad : error ? C.errors[error] : null;
  const apply = async () => {
    if (checking || busy) return;
    setChecking(true);
    setVWhy(null);
    const r = await (checkVoucher ?? checkPrintVoucher)(code, market, link.o);
    setChecking(false);
    if ('value' in r) { setTyped({ code: code.toUpperCase().replace(/[^A-Z0-9]/g, ''), value: r.value }); setField(false); setError(null); return; }
    setVWhy(r.why);
  };
  return (
    <>
      {note}
      <section data-testid="print-offer" aria-label={W.title} className={CARD}>
        <h2 className="font-luxury text-xl font-bold">{W.title}</h2>
        <p className="text-sm text-zinc-300 mt-2">{W.lead}</p>
        <PrintPick lang={lang} words={{ ...W, none: W.choose }} offered={offered} choice={choice} onChoice={onChoice} consent={consent} onConsent={setConsent}
          consentText={consentText} artSrc={st.download?.display_url ?? st.download?.url} fmt={fmt} busy={busy} />
        {part && (
          <p data-testid="print-total" className="mt-3 text-sm font-semibold text-zinc-100 flex justify-between gap-2">
            <span>{W.total}</span><span className="whitespace-nowrap">{fmt(part.price + part.ship)}</span>
          </p>
        )}
        {balance > 0 && (
          <p data-testid="print-voucher" className="mt-3 text-sm text-emerald-200 flex items-center gap-2"><Gift className="w-4 h-4 shrink-0" /> {V.balance(fmt(balance))}</p>
        )}
        {split && (
          <div data-testid="print-voucher-split" className="mt-1 text-sm">
            <p className="text-emerald-200 flex justify-between gap-2"><span>{V.row}</span><span className="whitespace-nowrap">−{fmt(split.discount)}</span></p>
            <p data-testid="print-to-pay" className="font-semibold text-zinc-100 flex justify-between gap-2"><span>{V.pay}</span><span className="whitespace-nowrap">{fmt(split.pay)}</span></p>
          </div>
        )}
        {!balance && !field && (
          <button type="button" data-testid="print-voucher-open" disabled={busy} onClick={() => setField(true)}
            className="mt-3 min-h-[40px] text-xs text-zinc-300 underline underline-offset-2 flex items-center gap-1.5">
            <Gift className="w-3.5 h-3.5" /> {V.open}
          </button>
        )}
        {!balance && field && (
          <div data-testid="print-voucher-field" className="mt-3">
            <div className="flex gap-2">
              <input aria-label={V.open} data-testid="print-voucher-code" type="text" autoComplete="off" autoCapitalize="characters" spellCheck={false} maxLength={20}
                value={code} disabled={busy || checking} placeholder="ABCD-EFGH-JKLM" onChange={(e) => { setCode(e.target.value.toUpperCase()); setVWhy(null); }}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void apply(); } }}
                className="flex-1 min-w-0 min-h-[44px] px-3 rounded-xl bg-white/5 border border-white/15 text-zinc-100 text-sm tracking-widest font-mono" />
              <button type="button" data-testid="print-voucher-apply" disabled={busy || checking || !code} onClick={() => void apply()}
                className="min-h-[44px] px-4 rounded-xl border border-gold/40 text-gold-light text-sm font-semibold disabled:opacity-50">
                {checking ? <Dot /> : V.apply}
              </button>
            </div>
            {vWhy && <p role="alert" data-testid="print-voucher-error" className="text-[11px] text-rose-200 mt-2">{vWhy === 'artwork' ? V.artwork : V.bad}</p>}
          </div>
        )}
        <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed"><LegalParts parts={legal.acceptance} lang={lang} /></p>
        <button data-testid="print-buy" type="button" onClick={() => { void press(); }} disabled={disabled}
          className={`mt-3 w-full min-h-[48px] px-3 py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 text-center ${disabled
            ? 'bg-white/5 border border-white/10 text-zinc-400 cursor-not-allowed'
            : 'fx-gold gold-metal'}`}>
          {busy ? <Dot /> : <Lock className="w-4 h-4 shrink-0" />}
          <span>{busy ? W.opening : legal.continueButton}</span>
        </button>
        {!busy && blockedBy === 'country' && <p data-testid="print-hint" className="text-[11px] text-zinc-400 mt-2">{W.countryMissing}</p>}
        {!busy && blockedBy === 'consent' && <p data-testid="print-hint" className="text-[11px] text-zinc-400 mt-2">{W.consentMissing}</p>}
        {errorText && !busy && <p role="alert" data-testid="print-error" className="mt-3 text-xs text-amber-100 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3">{errorText}</p>}
        <p className="text-[11px] text-zinc-400 mt-3 leading-relaxed">{W.footnote}</p>
      </section>
    </>
  );
};
