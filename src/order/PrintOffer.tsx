import React, { useState } from 'react';
import { Lock, RefreshCcw } from 'lucide-react';
import type { OrderCopy } from './copy';
import type { OrderStatus } from './api';
import type { OrderLink } from './driver';
import { PRINT_BUSY, buyPrint, marketCountry, offerPrints, type BuyPrintOutcome, type PrintBack } from './printAddon';
import { CARD, PLAIN_BTN } from './ui';
import { NO_PRINT, PrintPick, printPart, type PrintChoice } from '../try/PrintPick';
import { defaultCountry } from '../shared/prints';
import { money } from '../shared/markets';
import { checkoutLegal } from '../shared/legal';
import { LegalParts } from '../shared/LegalLinks';
import { Dot, Waiting } from '../motion/Tick';
import type { Lang } from '../try/lang';

// A print of the artwork, offered under a delivered artwork that has none (the status reply's print_offer; api/_lib/prints.py). The owner
// wanted the print out of the first checkout, where a big price scares, and offered once the customer has the file: so the card is calm,
// below the artwork, and nothing on it is chosen or ticked in advance. The print is a second order with its own payment page; the button
// opens Stripe's (./printAddon.ts buyPrint). After the way back from Stripe the page asks until the print is on record (the parent runs
// watchPrint and hands the result down as `back`); while a payment is being confirmed or is on record the card stays away, so a second
// payment is never invited.

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
  initial?: { choice?: PrintChoice; consent?: boolean; error?: OfferError };
}

export type OfferError = Exclude<Extract<BuyPrintOutcome, { kind: 'error' }>['code'], 'has'>;

export const PrintOffer: React.FC<Props> = ({ C, lang, link, st, market, back, email, onReload, onRecheck, go, buy, initial }) => {
  const [choice, setChoice] = useState<PrintChoice>(initial?.choice ?? NO_PRINT);
  const [consent, setConsent] = useState(initial?.consent ?? false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<OfferError | null>(initial?.error ?? null);
  const W = C.offer;
  const offered = st.print ? [] : offerPrints(st);
  const fmt = (c: number) => money(c, 'eur', lang);
  const part = printPart(choice, offered);
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
    const out = await (buy ?? buyPrint)(link, { product: choice.product, country: choice.country }, lang, part.price + part.ship);
    if (out.kind === 'redirect') { (go ?? ((u: string) => window.location.assign(u)))(out.url); return; }   // leaving for Stripe: the button stays busy
    setBusy(false);
    if (out.code === 'changed' || out.code === 'unavailable' || out.code === 'has') onReload();   // the offer as the server has it now, or the print the order already has
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
  const errorText = error === 'changed' ? W.changed : error === 'unavailable' ? W.unavailable : error ? C.errors[error] : null;
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
