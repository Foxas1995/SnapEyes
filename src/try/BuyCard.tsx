import React from 'react';
import { Lock, RefreshCcw } from 'lucide-react';
import { T } from './copy';
import { type Eye, MAX_EYES, billableEyes } from './multi';
import type { BuyState } from './picker';
import { classStyle, styleName } from '../shared/styles';
import { currencyOf, currentMarket, money, priceMinor, type PriceList } from '../shared/markets';
import { listFor } from '../shared/pricing';
import { checkoutLegal, legalEdition } from '../shared/legal';
import { LegalParts } from '../shared/LegalLinks';
import type { Lang } from '../shared/lang';

/** The withdrawal-waiver text per language, as GET /api/checkout sends it. */
export type ConsentTexts = Partial<Record<Lang, string>>;

/** Whether this deployment takes orders (/api/health stripe and GET /api/checkout open), with the server's own price
 *  list for this page's market and its withdrawal-waiver text. null: not known yet, shown as closed. */
export interface Ordering {
  open: boolean;
  prices?: Partial<PriceList>;
  // the most eyes an artwork can be ordered with right now (GET /api/checkout orderable_max_eyes: the run-time catalogue's maximum), printed in the hints below;
  // absent: the artwork's own limit
  maxEyes?: number;
  // the EU texts per language (also the Hungarian edition's), and per market where a market has its own (markets.au: the
  // Australian checkbox)
  consent?: ConsentTexts & { version?: string; markets?: Record<string, ConsentTexts | undefined> };
}

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
  /** The price changed while the customer looked (the server answered 409 price_changed): the sentence naming the new
   *  price, shown above the button until the next press. */
  priceNote?: string | null;
  /** What the picker says about the selected style (src/try/picker.ts buyState): bought as it is, opens soon (no price, no button), or no style of this
   *  many eyes can be bought yet (one line). */
  state?: BuyState;
  /** the tile list is still being asked for: the card waits for it (it cannot say what can be bought) */
  loading?: boolean;
  /** the eyes (1-based) whose failing rule only warns on this style: said above the waiver, before the customer ticks it */
  advisory?: number[];
  /** the words on the artwork break a rule (a letter the font cannot draw): the button waits, and says why */
  wordsBlocked?: boolean;
}

// what a card is told when its caller says nothing of the picker (the card of before the picker existed, and the checks that render it alone): the
// selected style can be bought as it is, nothing warns, the words are fine
const NORMAL: BuyState = { kind: 'normal' };

const CARD = 'bg-[#0b0e17] border border-[#f5c542]/25 rounded-2xl p-4';

/** The price of this artwork and, where this deployment takes orders, the way to buy it: the withdrawal waiver (never
 *  ticked in advance), the legal links and the button to Stripe's page. Where it does not, today's plain "ordering
 *  opens soon" and no button. The AI-generated sample eye is never priced nor ordered. */
export const BuyCard: React.FC<Props> = (props) => {
  const p = { ...props, state: props.state ?? NORMAL, loading: props.loading ?? false, advisory: props.advisory ?? [], wordsBlocked: props.wordsBlocked ?? false };
  const billable = billableEyes(p.eyes);
  const samples = p.eyes.length - billable;
  const open = !!p.ordering?.open;
  const lang = T.lang;

  if (billable === 0) {
    return (
      <section aria-label={T.price.title} className={CARD}>
        <p className="text-[10px] uppercase tracking-widest text-zinc-400">{T.price.title}</p>
        <p data-testid="price-demo" className="text-sm text-zinc-200 mt-1.5">{T.price.demo}</p>
        {open
          ? <SampleSwap eyes={p.eyes} onRetake={p.onRetake} />
          : <p className="text-sm font-semibold text-emerald-300 mt-3">{T.price.notice}</p>}
      </section>
    );
  }

  const n = billable;
  // a style that opens soon, or an eye count no style of can be bought yet: one line, no price, no button, no date (INTEGRATION_SPEC 1.8 rule 2)
  if (p.state.kind === 'soon' || p.state.kind === 'countSoon') {
    return (
      <section aria-label={T.price.title} data-testid="buy-soon" className={CARD}>
        <p className="text-[10px] uppercase tracking-widest text-zinc-300">{T.price.title}</p>
        <p data-testid="buy-soon-line" className="text-sm font-semibold text-emerald-300 mt-1.5">{p.state.kind === 'soon' ? T.picker.soonBuy : T.picker.countSoon(n)}</p>
      </section>
    );
  }
  // nothing is selected (nothing can be drawn for these eyes: the retake state above says why): no price and no button
  if (!p.loading && p.state.kind === 'none') return null;
  if (p.loading) {
    return (
      <section aria-label={T.price.title} data-testid="buy-wait" className={CARD}>
        <p className="text-[10px] uppercase tracking-widest text-zinc-300">{T.price.title}</p>
        <p className="text-sm text-zinc-200 mt-1.5">{T.buy.waitPreview}</p>
      </section>
    );
  }
  // the page's market (src/shared/markets.ts: the link's m=, or the visitor's earlier choice): its currency and prices,
  // the server's own list for it once ordering is open (the server prices the checkout itself either way)
  const market = currentMarket();
  const currency = currencyOf(market);
  const fmt = (c: number) => money(c, currency, lang);
  // the visitor's own ladder: while a price experiment runs for them, the ladder of their variant (the server's answer,
  // src/shared/pricing.ts), else the standard one; every number on this card, the button's included, comes from it
  const list = listFor(market, open ? p.ordering?.prices : undefined);
  const cents = priceMinor(n, p.style, market, list);
  // the card names the selected style and the price of THAT style; the hints name price classes, and print a number of eyes only as far as this
  // deployment sells (orderable_max_eyes of GET /api/checkout): the pair price is not printed where two eyes cannot be ordered
  const most = Math.max(1, Math.min(MAX_EYES, p.ordering?.maxEyes ?? MAX_EYES));
  const label = T.price.eyes(n, p.styleName);
  const hint = n === 1
    ? [T.price.black(styleName(classStyle('black')), fmt(list.one_eye_studio_black), fmt(list.one_eye_art)), most >= 2 ? T.price.duoOffer(fmt(list.two_eyes)) : ''].filter(Boolean).join(' ')
    : most > 2 ? T.price.extra(fmt(list.two_eyes), fmt(list.each_further_eye), most) : '';
  const head = (
    <>
      <p className="text-[10px] uppercase tracking-widest text-zinc-400">{T.price.title}</p>
      <div className="flex items-baseline justify-between gap-3 mt-1.5">
        <span className="text-sm font-semibold text-zinc-100">{label}</span>
        <span data-testid="price" className="font-luxury text-2xl font-bold text-[#f5c542] whitespace-nowrap">{fmt(cents)}</span>
      </div>
      {hint && <p className="text-[11px] text-zinc-300 mt-2">{hint}</p>}
      {samples > 0 && <p className="text-[11px] text-amber-200/90 mt-2">{T.price.sampleNotCounted(samples)}</p>}
    </>
  );

  // ordering is not open on this deployment (no Stripe keys yet): inform, sell nothing
  if (!open) {
    return (
      <section aria-label={T.price.title} className={CARD}>
        {head}
        <p className="text-sm font-semibold text-emerald-300 mt-3">{T.price.notice}</p>
        <p className="text-[11px] text-zinc-400 mt-1">{currency === 'aud' ? T.price.footnoteAud : currency === 'huf' ? T.price.footnoteHuf : T.price.footnote}</p>
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

  // the market's checkout wording (src/shared/legal.ts checkoutLegal: the Australian checkbox for au). The server records
  // a fingerprint of its own waiver text for the market: show exactly that one (it equals checkoutLegal's)
  const legal = checkoutLegal(lang, market);
  const texts = legalEdition(market) === 'au' ? p.ordering?.consent?.markets?.[market] : p.ordering?.consent;
  const waiverText = texts?.[lang] || legal.withdrawalConsent;
  const blockedBy = p.stale.length ? 'stale' : p.preview !== 'ready' ? p.preview : p.wordsBlocked ? 'words' : !p.waiver ? 'waiver' : null;
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

      {/* a style that only warns on a failing eye: said here, above the waiver, so the purchase is made knowing it (nothing is ticked for the customer) */}
      {p.advisory.length > 0 && (
        <p data-testid="buy-advisory" className="mt-3 text-xs text-amber-100 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3">{T.picker.advisory(p.advisory, p.eyes.length)}</p>
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
        <span>{p.busy && p.step ? p.step : T.buy.button(fmt(cents))}</span>
      </button>
      {!p.busy && blockedBy === 'waiver' && <p data-testid="buy-hint" className="text-[11px] text-zinc-400 mt-2">{legal.withdrawalConsentMissing}</p>}
      {!p.busy && blockedBy === 'composing' && <p data-testid="buy-hint" className="text-[11px] text-zinc-400 mt-2">{T.buy.waitPreview}</p>}
      {!p.busy && blockedBy === 'failed' && <p data-testid="buy-hint" className="text-[11px] text-zinc-400 mt-2">{T.buy.previewFailed}</p>}
      {!p.busy && blockedBy === 'words' && <p data-testid="buy-hint" className="text-[11px] text-zinc-400 mt-2">{T.buy.namesBlocked}</p>}
      {p.priceNote && !p.busy && (
        <p role="status" data-testid="buy-price-changed" className="mt-3 text-xs text-amber-100 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3">{p.priceNote}</p>
      )}
      {p.error && (
        <p role="alert" data-testid="buy-error" className="mt-3 text-xs text-rose-200 bg-rose-950/40 border border-rose-500/40 rounded-xl p-3">{p.error}</p>
      )}
      <p className="text-[11px] text-zinc-400 mt-3">{T.buy.next}</p>
      <p className="text-[11px] text-zinc-400 mt-1">{currency === 'aud' ? T.buy.footnoteAud : T.buy.footnote}</p>
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
