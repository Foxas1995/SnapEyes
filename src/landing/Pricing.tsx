import type { ReactNode } from 'react';
import { Check } from 'lucide-react';
import { useLang } from './lang';
import { tryUrl } from './config';
import { priceFootnote } from './copy';
import { useCatalogue, useOrderingOpen } from './ordering';
import { currencyOf, money, priceMinor } from '../shared/markets';
import { fillTokens, oneEyeRows, severalMax } from '../shared/catalogue';
import { classStyle, styleName } from '../shared/styles';
import { useMarket } from '../shared/useMarket';
import { usePrices, usePricesReady } from '../shared/usePrices';
import { SectionHead } from './ui';

function Card({ title, children, accent = false, className = '' }: { title: string; children: ReactNode; accent?: boolean; className?: string }) {
  return (
    <div className={`flex flex-col rounded-2xl border p-6 sm:p-7 ${accent ? 'border-[#f5c542]/35 bg-[#f5c542]/[0.04]' : 'border-white/[0.07] bg-white/[0.02]'} ${className}`}>
      <h3 className="font-body text-[11px] font-semibold uppercase tracking-[0.22em] text-zinc-400">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value, note, pending = false }: { label: string; value: string; note?: string; pending?: boolean }) {
  return (
    <div className="border-t border-white/[0.06] py-3 first:border-t-0 first:pt-0">
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-sm text-zinc-300">{label}</span>
        <span className={`shrink-0 font-luxury text-lg font-semibold text-white ${pending ? 'opacity-0' : ''}`} aria-hidden={pending || undefined}>{value}</span>
      </div>
      {note && <p className="mt-1 text-xs leading-relaxed text-zinc-400">{note}</p>}
    </div>
  );
}

// No purchase buttons here: an order starts from the customer's own preview on /try, so the only action is the free
// preview. The notice says "ordering opens soon" until src/landing/ordering.ts finds that this deployment takes orders.
// The rows name PRICE CLASSES, not a list of styles or a number of eyes: the black class by its one style, every other style as "any other style" with
// the list of the styles that can be ordered now, and the number of eyes, all from the run-time catalogue (src/shared/catalogue.ts: the tokens {styles}
// and {max}); a price is printed only for a count of eyes some style can be ordered for (a group that cannot be ordered yet is "free preview now").
export function Pricing() {
  const { t, lang } = useLang();
  const open = useOrderingOpen();
  const cat = useCatalogue();
  const p = t.pricing;
  // the visitor's market (src/shared/markets.ts: the link's m=, or their earlier choice): its currency and prices
  const market = useMarket();
  const currency = currencyOf(market);
  // the visitor's own ladder while a price experiment runs for them (src/shared/pricing.ts); the first answer of the
  // server is waited for (a moment), so no visitor sees the standard price before their own
  const prices = usePrices(market);
  const ready = usePricesReady();
  const pending = !ready;
  const fmt = (c: number) => money(c, currency, lang);
  const black = classStyle('black');
  const rows = oneEyeRows(cat, black);       // a price row only for a class with a style that can be ordered for one eye now
  const several = severalMax(cat);           // the several-eyes ladder only up to the count every smaller count of which can be ordered too (the Trio alone is none)
  return (
    <section id="pricing" className="scroll-mt-16 border-t border-white/[0.06] py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <SectionHead eyebrow={p.eyebrow} title={p.title} />

        <p role="note" className="mt-8 inline-flex items-start gap-3 rounded-2xl border border-[#f5c542]/30 bg-[#f5c542]/[0.06] px-5 py-3.5 text-[15px] font-medium text-[#f7d77a]">
          <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#f5c542]" />
          <span>{open ? p.noticeOpen : p.notice}</span>
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card title={p.previewTitle} accent>
            <p className="mt-4 font-luxury text-[32px] font-semibold leading-none text-white">{p.previewPrice}</p>
            <ul className="mt-5 grid gap-2.5 text-sm text-zinc-300">
              {p.previewItems.map((it) => (
                <li key={it} className="flex items-center gap-2.5">
                  <Check aria-hidden="true" className="h-4 w-4 shrink-0 text-[#f5c542]" />
                  {it}
                </li>
              ))}
            </ul>
            <a
              href={tryUrl(lang)}
              className="mt-7 inline-flex min-h-11 items-center justify-center rounded-full border border-[#f5c542]/60 px-5 py-2.5 text-center text-sm font-semibold text-[#f5c542] transition-colors hover:bg-[#f5c542] hover:text-[#030408] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] sm:mt-auto"
            >
              {t.cta}
            </a>
          </Card>

          <Card title={p.oneEyeTitle}>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">{p.oneEyeNote}</p>
            {rows.black || rows.art ? (
              <div className="mt-5">
                {rows.black && <Row label={styleName(black)} value={fmt(prices.one_eye_studio_black)} pending={pending} />}
                {rows.art && <Row label={p.artBackground} value={fmt(prices.one_eye_art)} note={fillTokens(p.artBackgroundNote, cat)} pending={pending} />}
              </div>
            ) : (
              <p className="mt-5 text-sm leading-relaxed text-zinc-300">{p.severalSoon}</p>
            )}
          </Card>

          <Card title={p.severalTitle} className="sm:col-span-2 lg:col-span-1">
            <p className="mt-3 text-sm leading-relaxed text-zinc-400">{several >= 2 ? fillTokens(p.severalNote, { ...cat, max: several }) : p.severalSoon}</p>
            {several >= 2 && (
              <>
                <div className="mt-5">
                  {[2, 3, 4, 5].filter((n) => n <= several).map((n) => (
                    <Row key={n} label={p.eyes(n)} value={fmt(priceMinor(n, classStyle('black'), market, prices))} pending={pending} />
                  ))}
                </div>
                {several > 2 && (
                  <p className={`mt-1 text-xs leading-relaxed text-zinc-400 ${pending ? 'opacity-0' : ''}`}>{p.perEye(fmt(prices.each_further_eye), several)}</p>
                )}
              </>
            )}
          </Card>
        </div>

        <p className="mt-6 text-sm leading-relaxed text-zinc-400">{priceFootnote(p, currency)}</p>
      </div>
    </section>
  );
}
