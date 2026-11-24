import React from 'react';
import type { Lang } from '../shared/lang';
import { countriesByName, countryName, type OfferedPrint, type PrintKind, kindAbout, madeText, printLabel, wayText } from '../shared/prints';

// The print picker. It was the print option of /try's buy card; since 2026-11-21 a print is offered AFTER the purchase, on the order page
// (src/order/PrintOffer.tsx), and the buy card shows none (the owner: a big price at the first checkout scares). The component takes its
// words and its language from the page that shows it, so the order page does not load /try's dictionary for it.

/** The words of the picker (src/order/copy*.ts offer has them). none: the first line of the list, chosen while no print is. */
export interface PrintWords {
  product: string;
  none: string;
  option: (name: string, price: string) => string;
  country: string;
  pick: string;
  shipping: string;
  arrives: string;
  mockAlt: (name: string) => string;
}

/** The customer's choice of a print: none, or a product and the country it ships to ('' until chosen). */
export interface PrintChoice { product: string | null; country: string }
export const NO_PRINT: PrintChoice = { product: null, country: '' };

/** The print and its shipping the choice adds (cents), or null for the file only or a choice that is not complete. */
export function printPart(choice: PrintChoice, offered: readonly OfferedPrint[]): { price: number; ship: number } | null {
  const p = choice.product ? offered.find((x) => x.id === choice.product) : undefined;
  const ship = p && choice.country ? p.ship[choice.country] : undefined;
  return p && typeof ship === 'number' ? { price: p.price, ship } : null;
}

interface Props {
  lang: Lang;
  words: PrintWords;
  offered: readonly OfferedPrint[];
  choice: PrintChoice;
  onChoice: (c: PrintChoice) => void;
  consent: boolean;
  onConsent: (v: boolean) => void;
  /** the exact text of the print box (the order status reply's print_offer.consent, else src/shared/legal.ts CHECKOUT_LEGAL printConsent) */
  consentText: string;
  /** the preview of the artwork on screen (its watermarked display copy) */
  artSrc?: string;
  fmt: (cents: number) => string;
  busy: boolean;
}

// a select as the card's other controls look
const SELECT = 'mt-1 w-full min-h-[44px] rounded-xl bg-[#0b0e17] border border-white/15 text-sm text-zinc-100 px-3';

/** The choice of a print: the print with its price, the delivery country and its shipping, a picture of the artwork as that print, and the
 *  print box (never ticked in advance). */
export const PrintPick: React.FC<Props> = (p) => {
  const lang = p.lang;
  const w = p.words;
  const sel = p.choice.product ? p.offered.find((x) => x.id === p.choice.product) : undefined;
  const list = sel ? countriesByName(lang, Object.keys(sel.ship)) : [];
  const ship = sel && p.choice.country ? sel.ship[p.choice.country] : undefined;
  return (
    <div data-testid="print-pick" className="mt-4 bg-white/5 border border-white/10 rounded-xl p-3">
      <label className="block text-[10px] uppercase tracking-widest text-zinc-400" htmlFor="print-product">{w.product}</label>
      <select id="print-product" data-testid="print-product" className={SELECT} disabled={p.busy} value={p.choice.product ?? ''}
        onChange={(e) => {
          const id = e.target.value || null;
          const next = id ? p.offered.find((x) => x.id === id) : undefined;
          // the country stays when the new print ships there too
          p.onChoice({ product: id, country: next && p.choice.country && next.ship[p.choice.country] ? p.choice.country : '' });
        }}>
        <option value="">{w.none}</option>
        {p.offered.map((o) => (
          <option key={o.id} value={o.id}>{w.option(printLabel(o.kind, o.cm, lang), p.fmt(o.price))}</option>
        ))}
      </select>
      {sel && (
        <>
          {kindAbout(sel.kind, lang) && <p data-testid="print-about" className="mt-2 text-[11px] text-zinc-300 leading-relaxed">{kindAbout(sel.kind, lang)}</p>}
          <p data-testid="print-made" className="mt-1 text-[11px] text-zinc-300 leading-relaxed">{madeText(sel.kind, lang)}</p>
          <div className="mt-3 flex gap-3 items-start">
            <PrintMock kind={sel.kind} src={p.artSrc} alt={w.mockAlt(printLabel(sel.kind, sel.cm, lang))} />
            <div className="flex-1 min-w-0">
              <label className="block text-[11px] text-zinc-300" htmlFor="print-country">{w.country}</label>
              <select id="print-country" data-testid="print-country" className={SELECT} disabled={p.busy} value={p.choice.country}
                onChange={(e) => p.onChoice({ product: sel.id, country: e.target.value })}>
                <option value="">{w.pick}</option>
                {list.map((cc) => <option key={cc} value={cc}>{countryName(cc, lang)}</option>)}
              </select>
              {typeof ship === 'number' && (
                <p data-testid="print-shipping" className="mt-2 text-xs text-zinc-200 flex justify-between gap-2">
                  <span>{w.shipping}</span><span className="whitespace-nowrap">{p.fmt(ship)}</span>
                </p>
              )}
              {p.choice.country && typeof ship === 'number' && <p data-testid="print-way" className="mt-1 text-[11px] text-zinc-300">{wayText(p.choice.country, lang)}</p>}
              <p className="mt-1 text-[11px] text-zinc-400">{w.arrives}</p>
            </div>
          </div>
          <label className="mt-3 flex items-start gap-3 text-xs leading-relaxed text-zinc-200 cursor-pointer">
            <input data-testid="print-consent" type="checkbox" checked={p.consent} disabled={p.busy} onChange={(e) => p.onConsent(e.target.checked)}
              className="mt-0.5 w-5 h-5 shrink-0 accent-gold" />
            <span>{p.consentText}</span>
          </label>
        </>
      )}
    </div>
  );
};

// a flat picture of the artwork as each kind of print: acrylic glass (a glossy edge and a soft reflection), glossy metal (a thin bright rim
// and a reflection), a canvas on its stretcher frame (no outer frame: the picture to the edge and a side shadow), a poster (paper, a thin
// shadow), an acrylic block (a thick clear edge all round, the gloss of the acrylic), a keyring (a small upright tag with its ring; it is
// not a square and not a thing for a wall). The artwork is never cropped (an artwork that is not square sits on its own dark ground, as the
// print file continues its background).
const MOCK: Record<PrintKind, { outer: string; inner: string; gloss: boolean; box?: string }> = {
  acrylic: { outer: 'p-[2px] bg-gradient-to-br from-white/50 via-white/10 to-white/30 shadow-[0_6px_18px_rgba(0,0,0,0.6)]', inner: '', gloss: true },
  metal: { outer: 'p-0 bg-zinc-400 shadow-[0_6px_18px_rgba(0,0,0,0.6)] ring-1 ring-white/30', inner: '', gloss: true },
  canvas: { outer: 'p-0 bg-[#111] shadow-[3px_6px_14px_rgba(0,0,0,0.6)]', inner: '', gloss: false },
  poster: { outer: 'p-0 bg-[#0d0d0d] shadow-[0_3px_10px_rgba(0,0,0,0.55)]', inner: '', gloss: false },
  block: { outer: 'p-[5px] bg-gradient-to-br from-white/50 via-white/10 to-white/30 shadow-[0_6px_18px_rgba(0,0,0,0.6)] ring-1 ring-white/10', inner: '', gloss: true },
  keyring: { outer: 'p-[3px] bg-gradient-to-br from-white/50 via-white/10 to-white/30 shadow-[0_3px_10px_rgba(0,0,0,0.55)]', inner: 'rounded-[5px]', gloss: true, box: 'w-[70px] h-24 mx-[13px] rounded-[8px]' },
};

export const PrintMock: React.FC<{ kind: PrintKind; src?: string; alt: string }> = ({ kind, src, alt }) => {
  const m = MOCK[kind];
  return (
    <div data-testid="print-mock" data-kind={kind} className={`relative ${m.box ?? 'w-24 h-24 rounded-[3px]'} shrink-0 ${m.outer}`}>
      {kind === 'keyring' && <span aria-hidden="true" className="absolute -top-2 left-1/2 -ml-[6px] w-3 h-3 rounded-full border-2 border-zinc-300" />}
      <div className={`relative w-full h-full overflow-hidden bg-black ${m.inner}`}>
        {src ? <img src={src} alt={alt} draggable={false} className="w-full h-full object-contain select-none" /> : <span className="sr-only">{alt}</span>}
        {m.gloss && <span aria-hidden="true" className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/25 via-transparent to-transparent" />}
      </div>
    </div>
  );
};
