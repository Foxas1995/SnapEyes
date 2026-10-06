// The currency switch of the new landing: one button per currency the site sells in, used in the pricing block and in the
// footer (the prototype's #curSeg and #curSeg2). A choice is a market (src/shared/markets.ts setMarket): remembered, carried
// to /try and the legal pages as m=, and every price, link and FAQ answer of the page follows it at once.
//
// Who sees it is today's rule (Footer.tsx, which this replaces): only a visitor who already sees another currency than the
// default market's (they came through an m= link, or chose it before), and from then on for the rest of the visit, so they
// can go back and forth. The default page stays as it was: nobody is offered Australian dollars by the page itself (the
// country hint of MarketHint.tsx may offer one; only the visitor's click changes the market). `always` shows it to everyone,
// as the prototype did, for the integrator or the owner to decide.
//
// Markets are offered in the languages their legal edition has texts in (an Australian page is English or German only), and
// never the forint market while the page has no Hungarian copy: the HUF button appears only on a page that already is in
// forints (a review visit with ?m=hu), exactly as the prototype's currencyChoices.
//
// The buttons are keyed by currency, so a click keeps the same nodes (and the focus on the one just used) while the market
// behind each of them changes.
import { useState } from 'react';
import { useLang } from './lang';
import { langAllowed } from '../shared/lang';
import { DEFAULT_MARKET, SELECTABLE, currencyOf, setMarket, type Currency, type Market } from '../shared/markets';
import { useMarket } from '../shared/useMarket';
import './css/currency.css';

// symbols and ISO codes are the same in every language: not copy
const CURRENCY_LABEL: Record<Currency, string> = { eur: '€ EUR', aud: 'A$ AUD', huf: 'Ft HUF' };

export interface CurrencySwitchProps {
  /** The words before the buttons, also the name of the button group (pricing.currencyLabel, footer.currency). */
  label: string;
  /** Show the switch to every visitor, not only to one who sees another currency than the default market's. */
  always?: boolean;
  /** No bottom margin: the footer row. */
  flush?: boolean;
  className?: string;
}

function choicesFor(market: Market, lang: Parameters<typeof langAllowed>[0]): Array<{ currency: Currency; market: Market }> {
  const own = currencyOf(market);
  const out: Array<{ currency: Currency; market: Market }> = [];
  for (const m of SELECTABLE) {
    if (m !== market && !langAllowed(lang, m)) continue;
    const currency = currencyOf(m);
    if (currency === 'huf' && own !== 'huf') continue;
    if (out.some((x) => x.currency === currency)) continue;
    // the visitor's own market stands for its currency (lt stays lt), otherwise the first market of that currency
    out.push({ currency, market: currency === own ? market : m });
  }
  return out;
}

export function CurrencySwitch({ label, always = false, flush = false, className = '' }: CurrencySwitchProps) {
  const { lang } = useLang();
  const market = useMarket();
  const own = currencyOf(market);
  // latched: once the visitor has seen another currency the switch stays, so they can return to the first one
  const [offered, setOffered] = useState(own !== currencyOf(DEFAULT_MARKET));
  if (own !== currencyOf(DEFAULT_MARKET) && !offered) setOffered(true);
  if (!always && !offered) return null;
  const choices = choicesFor(market, lang);
  if (choices.length < 2) return null;
  return (
    <div className={`lp-cur-sw ${className}`.trim()} style={flush ? { margin: 0 } : undefined}>
      <span>{label}</span>
      <div className="lp-seg lp-cur-seg" role="group" aria-label={label}>
        {choices.map((x) => (
          <button key={x.currency} type="button" data-market={x.market} aria-pressed={own === x.currency} onClick={() => setMarket(x.market)}>
            {CURRENCY_LABEL[x.currency]}
          </button>
        ))}
      </div>
    </div>
  );
}

export default CurrencySwitch;
