import { useState } from 'react';
import { useLang } from './lang';
import { useSuggestedMarket } from './ordering';
import { currencyOf, declineHint, hintMarket, setMarket } from '../shared/markets';
import { useMarket } from '../shared/useMarket';

// The offer of the visitor's own currency, at the top of the landing page. GET /api/checkout names a market for the
// visitor's country (Vercel's x-vercel-ip-country; ./ordering.ts asks it once per page load anyway), and
// src/shared/markets.ts hintMarket decides whether it may be offered: a market the site sells in, in another currency,
// to a visitor on the default market who came through no ?m= link and never chose. Nothing changes by itself: only
// the visitor's click switches the market (setMarket, remembered like the currency switch), and closing it is
// remembered too (declineHint), so it is never offered again. It sits in the page's flow (it scrolls away) and pushes
// the hero down by its own height, below the fixed header.
export function MarketHint() {
  const { t } = useLang();
  const market = useMarket();
  const suggest = useSuggestedMarket();
  const [closed, setClosed] = useState(false);
  const offer = closed ? null : hintMarket(suggest, market);
  const words = offer ? t.marketHint[currencyOf(offer)] : undefined;
  if (!offer || !words) return null;
  return (
    <div className="relative z-10 -mb-16 pt-16">
      <section aria-label={t.marketHint.label} className="border-b border-white/[0.06] bg-[#0b0e16]">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3 text-[13px] leading-relaxed text-zinc-300 sm:px-6">
          <p className="min-w-0 flex-1 basis-64">{words.text}</p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setMarket(offer)}
              className="min-h-[36px] rounded-full border border-[#f5c542]/50 px-3.5 text-[13px] font-semibold text-[#f5c542] transition-colors hover:bg-[#f5c542] hover:text-[#030408] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542]"
            >
              {words.show}
            </button>
            <button
              type="button"
              onClick={() => { declineHint(); setClosed(true); }}
              className="min-h-[36px] rounded-full px-3 text-[13px] text-zinc-400 transition-colors hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542]"
            >
              {t.marketHint.close}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
