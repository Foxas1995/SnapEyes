// The offer of the visitor's own currency, at the top of the page (src/shared/markets.ts hintMarket). Not in the prototype: it is a
// fact of the live site, kept.
//
// GET /api/checkout names a market for the visitor's country (Vercel's x-vercel-ip-country; ./ordering.ts asks it once per page
// load anyway), and hintMarket decides whether it may be offered: a market the site sells in, in another currency, to a visitor
// on the default market who came through no ?m= link and never chose. Nothing changes by itself: only the visitor's click
// switches the market (setMarket, remembered like the currency switch), and closing it is remembered too (declineHint), so it is
// never offered again. A market is offered only in a language its legal edition has texts in (langAllowed: the Australian one has
// English and German), as on the page before this one. It sits in the page's flow (it scrolls away) below the fixed header and pushes the hero down by its own
// height (.lp-market in src/landing/css/bar.css). The words are the copy's marketHint.* (Australian dollars and forints).
import { useState } from 'react';
import { useCopy } from './copy/useCopy';
import { useSuggestedMarket } from './ordering';
import { langAllowed } from '../shared/lang';
import { currencyOf, declineHint, hintMarket, setMarket, type Currency } from '../shared/markets';
import { useMarket } from '../shared/useMarket';

interface OfferWords { text: string; show: string }

export function MarketHintBar() {
  const { c, lang } = useCopy();
  const market = useMarket();
  const suggest = useSuggestedMarket();
  const [closed, setClosed] = useState(false);
  const hint = closed ? null : hintMarket(suggest, market);
  // only a market whose edition can be read in the language of this page: a Lithuanian or Hungarian reader is not offered the
  // Australian market (its edition has English and German only, so accepting would throw them into English)
  const offer = hint && langAllowed(lang, hint) ? hint : null;
  const byCurrency: Partial<Record<Currency, OfferWords>> = { aud: c.marketHint.aud, huf: c.marketHint.huf };
  const words = offer ? byCurrency[currencyOf(offer)] : undefined;
  if (!offer || !words?.text) return null;
  return (
    <div className="lp-market">
      <section aria-label={c.marketHint.label}>
        <div className="lp-wrap lp-market-in">
          <p>{words.text}</p>
          <div className="lp-market-btns">
            <button type="button" className="lp-market-show" onClick={() => setMarket(offer)}>{words.show}</button>
            <button type="button" className="lp-market-close" onClick={() => { declineHint(); setClosed(true); }}>{c.marketHint.close}</button>
          </div>
        </div>
      </section>
    </div>
  );
}
