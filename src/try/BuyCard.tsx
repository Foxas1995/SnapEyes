import React from 'react';
import { Lock, RefreshCcw } from 'lucide-react';
import { T } from './copy';
import { type Eye, MAX_EYES, PRICE_CENTS, billableEyes, euro, priceCents } from './multi';
import { priceFromList, type PriceList } from '../order/api';
import { CHECKOUT_LEGAL } from '../shared/legal';
import { LegalParts } from '../shared/LegalLinks';

/** Whether this deployment takes orders (/api/health stripe and GET /api/checkout open), with the server's own price
 *  list and withdrawal-waiver text. null: not known yet, shown as closed. */
export interface Ordering { open: boolean; prices?: Partial<PriceList>; consent?: { en?: string; de?: string } }

// src/landing/config.ts PRICE_CENTS in the server's names: the fallback when the server sent no price list
const CONFIG_PRICES: PriceList = {
  one_eye_studio_black: PRICE_CENTS.studioBlack,
  one_eye_art: PRICE_CENTS.artBackground,
  two_eyes: PRICE_CENTS.coupleDuo,
  each_further_eye: PRICE_CENTS.extraEye,
};

interface Props {
  eyes: Eye[];
  style: string;
  styleName: string;
  ordering: Ordering | null;
  preview: 'ready' | 'composing' | 'failed';   // the preview of exactly this choice: nobody orders what they have not seen
  stale: number[];                              // eyes (1-based) that must be taken again before ordering
  onRetake: (position: number) => void;
  waiver: boolean;
  onWaiver: (v: boolean) => void;
  busy: boolean;
  step: string | null;
  error: string | null;
  onBuy: () => void;
}

const CARD = 'bg-[#0b0e17] border border-[#f5c542]/25 rounded-2xl p-4';

/** The price of this artwork and, where this deployment takes orders, the way to buy it: the withdrawal waiver (never
 *  ticked in advance), the legal links and the button to Stripe's page. Where it does not, today's plain "ordering
 *  opens soon" and no button. The AI-generated sample eye is never priced nor ordered. */
export const BuyCard: React.FC<Props> = (p) => {
  const billable = billableEyes(p.eyes);
  const samples = p.eyes.length - billable;
  const open = !!p.ordering?.open;
  const lang = T.lang;

  if (billable === 0) {
    return (
      <section aria-label={T.price.title} className={CARD}>
        <p className="text-[10px] uppercase tracking-widest text-zinc-500">{T.price.title}</p>
        <p data-testid="price-demo" className="text-sm text-zinc-200 mt-1.5">{T.price.demo}</p>
        {open
          ? <SampleSwap eyes={p.eyes} onRetake={p.onRetake} />
          : <p className="text-sm font-semibold text-emerald-300 mt-3">{T.price.notice}</p>}
      </section>
    );
  }

  const n = billable;
  const cents = open ? priceFromList(p.ordering?.prices, CONFIG_PRICES, n, p.style) : priceCents(n, p.style);
  const label = n === 1 ? T.price.oneEye(p.styleName) : n === 2 ? T.price.duo : T.price.many(n);
  const hint = n === 1
    ? `${T.price.oneEyeOther(euro(PRICE_CENTS.studioBlack, lang), euro(PRICE_CENTS.artBackground, lang))} ${T.price.duoOffer(euro(PRICE_CENTS.coupleDuo, lang))}`
    : T.price.extra(euro(PRICE_CENTS.coupleDuo, lang), euro(PRICE_CENTS.extraEye, lang), MAX_EYES);
  const head = (
    <>
      <p className="text-[10px] uppercase tracking-widest text-zinc-500">{T.price.title}</p>
      <div className="flex items-baseline justify-between gap-3 mt-1.5">
        <span className="text-sm font-semibold text-zinc-100">{label}</span>
        <span data-testid="price" className="font-luxury text-2xl font-bold text-[#f5c542] whitespace-nowrap">{euro(cents, lang)}</span>
      </div>
      <p className="text-[11px] text-zinc-400 mt-2">{hint}</p>
      {samples > 0 && <p className="text-[11px] text-amber-200/90 mt-2">{T.price.sampleNotCounted(samples)}</p>}
    </>
  );

  // ordering is not open on this deployment (no Stripe keys yet): inform, sell nothing
  if (!open) {
    return (
      <section aria-label={T.price.title} className={CARD}>
        {head}
        <p className="text-sm font-semibold text-emerald-300 mt-3">{T.price.notice}</p>
        <p className="text-[11px] text-zinc-500 mt-1">{T.price.footnote}</p>
      </section>
    );
  }

  // an artwork with the AI-generated sample eye in it is never for sale
  if (samples > 0) {
    return (
      <section aria-label={T.price.title} className={CARD}>
        {head}
        <SampleSwap eyes={p.eyes} onRetake={p.onRetake} />
      </section>
    );
  }

  const legal = CHECKOUT_LEGAL[lang];
  // the server records a fingerprint of its own waiver text: show exactly that one (it equals CHECKOUT_LEGAL's)
  const waiverText = (lang === 'de' ? p.ordering?.consent?.de : p.ordering?.consent?.en) || legal.withdrawalConsent;
  const blockedBy = p.stale.length ? 'stale' : p.preview !== 'ready' ? p.preview : !p.waiver ? 'waiver' : null;
  const disabled = p.busy || blockedBy !== null;
  return (
    <section aria-label={T.price.title} data-testid="buy-card" className={CARD}>
      {head}

      {p.stale.length > 0 && (
        <div data-testid="buy-stale" className="mt-3 text-xs text-amber-100 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3">
          <p>{T.buy.stale(p.stale, p.eyes.length)}</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {p.stale.map((i) => (
              <button key={i} type="button" onClick={() => p.onRetake(i)} disabled={p.busy}
                className="min-h-[40px] px-3 rounded-lg border border-amber-400/50 bg-amber-500/10 text-amber-100 text-xs font-semibold flex items-center gap-1.5">
                <RefreshCcw className="w-3.5 h-3.5" /> {p.eyes.length === 1 ? T.result.retakeOnly : T.result.retakeEye(i)}
              </button>
            ))}
          </div>
        </div>
      )}

      <label className="mt-4 flex items-start gap-3 text-xs leading-relaxed text-zinc-200 bg-white/5 border border-white/10 rounded-xl p-3 cursor-pointer">
        <input data-testid="waiver" type="checkbox" checked={p.waiver} disabled={p.busy} onChange={(e) => p.onWaiver(e.target.checked)}
          className="mt-0.5 w-5 h-5 shrink-0 accent-[#f5c542]" />
        <span>{waiverText}</span>
      </label>
      <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed"><LegalParts parts={legal.acceptance} lang={lang} /></p>

      <button data-testid="buy" type="button" onClick={p.onBuy} disabled={disabled}
        className={`mt-3 w-full min-h-[48px] px-3 py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 text-center ${disabled
          ? 'bg-white/5 border border-white/10 text-zinc-500 cursor-not-allowed'
          : 'bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black shadow-lg shadow-[#f5c542]/20 active:scale-[0.98]'}`}>
        {p.busy
          ? <span className="w-4 h-4 shrink-0 border-2 border-zinc-500/40 border-t-zinc-300 rounded-full animate-spin" aria-hidden />
          : <Lock className="w-4 h-4 shrink-0" />}
        <span>{p.busy && p.step ? p.step : T.buy.button(euro(cents, lang))}</span>
      </button>
      {!p.busy && blockedBy === 'waiver' && <p data-testid="buy-hint" className="text-[11px] text-zinc-400 mt-2">{legal.withdrawalConsentMissing}</p>}
      {!p.busy && blockedBy === 'composing' && <p data-testid="buy-hint" className="text-[11px] text-zinc-400 mt-2">{T.buy.waitPreview}</p>}
      {!p.busy && blockedBy === 'failed' && <p data-testid="buy-hint" className="text-[11px] text-zinc-400 mt-2">{T.buy.previewFailed}</p>}
      {p.error && (
        <p role="alert" data-testid="buy-error" className="mt-3 text-xs text-rose-200 bg-rose-950/40 border border-rose-500/40 rounded-xl p-3">{p.error}</p>
      )}
      <p className="text-[11px] text-zinc-400 mt-3">{T.buy.next}</p>
      <p className="text-[11px] text-zinc-500 mt-1">{T.buy.footnote}</p>
    </section>
  );
};

/** Why an artwork with the AI-generated sample eye cannot be bought, and the way out right here: one button per sample
 *  eye that retakes it with the customer's own eye. The card never names a button elsewhere on the page, because the
 *  result screen shows the sample's own "use your own eye" button only while that eye is the one selected. */
const SampleSwap: React.FC<{ eyes: Eye[]; onRetake: (position: number) => void }> = ({ eyes, onRetake }) => {
  const at = eyes.flatMap((e, i) => (e.sample ? [i + 1] : []));
  return (
    <div data-testid="buy-sample" className="mt-3">
      <p className="text-sm text-amber-200/90">{T.buy.sample(at.length)}</p>
      <div className="flex flex-wrap gap-2 mt-2">
        {at.map((i) => (
          <button key={i} type="button" data-testid={`buy-sample-swap-${i}`} onClick={() => onRetake(i)}
            className="min-h-[44px] px-3 rounded-xl border border-amber-400/50 bg-amber-500/10 text-amber-100 text-sm font-semibold flex items-center gap-2 text-left">
            <RefreshCcw className="w-4 h-4 shrink-0" /> {at.length === 1 ? T.result.replaceSample : T.buy.replaceSampleEye(i)}
          </button>
        ))}
      </div>
    </div>
  );
};
