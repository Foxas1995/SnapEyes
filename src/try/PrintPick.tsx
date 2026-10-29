import React from 'react';
import { T } from './copy';
import { countriesByName, countryName, type OfferedPrint, type PrintKind, kindName, printSize } from '../shared/prints';

/** The customer's choice of a print: none (the digital file only), or a product and the country it ships to ('' until chosen). */
export interface PrintChoice { product: string | null; country: string }
export const NO_PRINT: PrintChoice = { product: null, country: '' };

/** The print and its shipping the choice adds (cents), or null for the file only or a choice that is not complete. */
export function printPart(choice: PrintChoice, offered: readonly OfferedPrint[]): { price: number; ship: number } | null {
  const p = choice.product ? offered.find((x) => x.id === choice.product) : undefined;
  const ship = p && choice.country ? p.ship[choice.country] : undefined;
  return p && typeof ship === 'number' ? { price: p.price, ship } : null;
}

interface Props {
  offered: readonly OfferedPrint[];
  choice: PrintChoice;
  onChoice: (c: PrintChoice) => void;
  consent: boolean;
  onConsent: (v: boolean) => void;
  /** the exact text of the print box (GET /api/checkout consent.print, else src/shared/legal.ts CHECKOUT_LEGAL printConsent) */
  consentText: string;
  /** the preview of the artwork on screen (its watermarked display copy) */
  artSrc?: string;
  fmt: (cents: number) => string;
  busy: boolean;
}

// a select as the card's other controls look
const SELECT = 'mt-1 w-full min-h-[44px] rounded-xl bg-[#0b0e17] border border-white/15 text-sm text-zinc-100 px-3';

/** The print option of the buy card: one choice (the file only, or a print with its price), the delivery country and its shipping, a picture
 *  of the artwork as that print, and the print box (never ticked in advance). Nothing here when no print is offered. */
export const PrintPick: React.FC<Props> = (p) => {
  const lang = T.lang;
  const sel = p.choice.product ? p.offered.find((x) => x.id === p.choice.product) : undefined;
  const list = sel ? countriesByName(lang, Object.keys(sel.ship)) : [];
  const ship = sel && p.choice.country ? sel.ship[p.choice.country] : undefined;
  return (
    <div data-testid="print-pick" className="mt-4 bg-white/5 border border-white/10 rounded-xl p-3">
      <label className="block text-[10px] uppercase tracking-widest text-zinc-400" htmlFor="print-product">{T.print.title}</label>
      <select id="print-product" data-testid="print-product" className={SELECT} disabled={p.busy} value={p.choice.product ?? ''}
        onChange={(e) => {
          const id = e.target.value || null;
          const next = id ? p.offered.find((x) => x.id === id) : undefined;
          // the country stays when the new print ships there too
          p.onChoice({ product: id, country: next && p.choice.country && next.ship[p.choice.country] ? p.choice.country : '' });
        }}>
        <option value="">{T.print.none}</option>
        {p.offered.map((o) => (
          <option key={o.id} value={o.id}>{T.print.option(`${kindName(o.kind, lang)} ${printSize(o.cm)}`, p.fmt(o.price))}</option>
        ))}
      </select>
      {sel && (
        <>
          <div className="mt-3 flex gap-3 items-start">
            <PrintMock kind={sel.kind} src={p.artSrc} alt={T.print.mockAlt(`${kindName(sel.kind, lang)} ${printSize(sel.cm)}`)} />
            <div className="flex-1 min-w-0">
              <label className="block text-[11px] text-zinc-300" htmlFor="print-country">{T.print.country}</label>
              <select id="print-country" data-testid="print-country" className={SELECT} disabled={p.busy} value={p.choice.country}
                onChange={(e) => p.onChoice({ product: sel.id, country: e.target.value })}>
                <option value="">{T.print.pick}</option>
                {list.map((cc) => <option key={cc} value={cc}>{countryName(cc, lang)}</option>)}
              </select>
              {typeof ship === 'number' && (
                <p data-testid="print-shipping" className="mt-2 text-xs text-zinc-200 flex justify-between gap-2">
                  <span>{T.print.shipping}</span><span className="whitespace-nowrap">{p.fmt(ship)}</span>
                </p>
              )}
              <p className="mt-1 text-[11px] text-zinc-400">{T.print.arrives}</p>
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

// a flat picture of the artwork as each kind of print: acrylic glass (a glossy edge and a soft reflection), a canvas in a black floating
// frame (the frame, a shadow gap, the canvas), a poster (paper, a thin shadow). The artwork is never cropped (an artwork that is not square
// sits on its own dark ground, as the print file continues its background).
const MOCK: Record<PrintKind, { outer: string; inner: string; gloss: boolean }> = {
  acrylic: { outer: 'p-[2px] bg-gradient-to-br from-white/50 via-white/10 to-white/30 shadow-[0_6px_18px_rgba(0,0,0,0.6)]', inner: '', gloss: true },
  canvas: { outer: 'p-[5px] bg-[#111] shadow-[0_6px_18px_rgba(0,0,0,0.6)] ring-1 ring-white/10', inner: 'p-[3px] bg-black', gloss: false },
  poster: { outer: 'p-0 bg-[#0d0d0d] shadow-[0_3px_10px_rgba(0,0,0,0.55)]', inner: '', gloss: false },
};

export const PrintMock: React.FC<{ kind: PrintKind; src?: string; alt: string }> = ({ kind, src, alt }) => {
  const m = MOCK[kind];
  return (
    <div data-testid="print-mock" data-kind={kind} className={`relative w-24 h-24 shrink-0 rounded-[3px] ${m.outer}`}>
      <div className={`relative w-full h-full overflow-hidden bg-black ${m.inner}`}>
        {src ? <img src={src} alt={alt} draggable={false} className="w-full h-full object-contain select-none" /> : <span className="sr-only">{alt}</span>}
        {m.gloss && <span aria-hidden="true" className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/25 via-transparent to-transparent" />}
      </div>
    </div>
  );
};
