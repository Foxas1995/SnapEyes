import React, { useState } from 'react';
import { Gift, X } from 'lucide-react';
import { T } from './copy';
import { callApi } from '../order/api';
import type { Market } from '../shared/markets';
import { giftMarket } from '../shared/gift';

/** A gift voucher the server accepted for this market (GET /api/checkout?voucher=, api/_lib/voucher.py check): the code as typed and its value in the
 *  market's smallest unit. The checkout sends the code again and the server checks it once more before it opens Stripe's page. */
export interface GiftApplied { code: string; value: number }

type Why = keyof typeof T.gift.errors;
const WHY = new Set<string>(['format', 'unknown', 'used', 'expired', 'currency']);

export { giftMarket };

/** The code as people read it, from what was typed: capitals, no spaces; a dash after every 4 characters once there are 12. */
export function tidyCode(v: string): string {
  const c = v.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);
  return c.length === 12 ? `${c.slice(0, 4)}-${c.slice(4, 8)}-${c.slice(8)}` : c;
}

interface Props {
  market: Market;
  applied: GiftApplied | null;
  onApplied: (g: GiftApplied | null) => void;
  /** the voucher's value as money in the page's currency */
  fmt: (cents: number) => string;
  busy: boolean;
}

/** "I have a gift voucher": a closed link until it is pressed, then the code field and its button. An accepted voucher shows as one line with its value
 *  and a way to remove it. Nothing here is ticked or entered for the customer. */
export const GiftField: React.FC<Props> = ({ market, applied, onApplied, fmt, busy }) => {
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState('');
  const [checking, setChecking] = useState(false);
  const [why, setWhy] = useState<Why | null>(null);

  if (applied) {
    return (
      <div data-testid="gift-applied" className="mt-3 flex items-center justify-between gap-3 text-sm text-emerald-200 bg-emerald-950/30 border border-emerald-500/30 rounded-xl px-3 py-2">
        <span className="flex items-center gap-2"><Gift className="w-4 h-4 shrink-0" /> {T.gift.applied(fmt(applied.value))}</span>
        <button type="button" data-testid="gift-remove" disabled={busy} onClick={() => { onApplied(null); setWhy(null); }}
          className="min-h-[40px] px-2 text-xs text-zinc-300 underline underline-offset-2 flex items-center gap-1">
          <X className="w-3.5 h-3.5" /> {T.gift.remove}
        </button>
      </div>
    );
  }
  if (!open) {
    return (
      <button type="button" data-testid="gift-open" disabled={busy} onClick={() => setOpen(true)}
        className="mt-3 min-h-[40px] text-xs text-zinc-300 underline underline-offset-2 flex items-center gap-1.5">
        <Gift className="w-3.5 h-3.5" /> {T.gift.open}
      </button>
    );
  }
  const apply = async () => {
    const c = code.replace(/[^A-Za-z0-9]/g, '');
    if (c.length !== 12) { setWhy('format'); return; }
    setChecking(true);
    setWhy(null);
    const r = await callApi<{ valid?: boolean; value?: number }>(`/api/checkout?voucher=${encodeURIComponent(c.toUpperCase())}&m=${encodeURIComponent(market)}`, { timeoutMs: 15_000 });
    setChecking(false);
    if (r.ok && r.data && r.data.valid === true && typeof r.data.value === 'number' && r.data.value > 0) {
      onApplied({ code: c.toUpperCase(), value: r.data.value });
      return;
    }
    const w = r.data && typeof (r.data as { why?: unknown }).why === 'string' ? (r.data as { why: string }).why : '';
    setWhy(WHY.has(w) ? (w as Why) : 'failed');
  };
  return (
    <div data-testid="gift-field" className="mt-3">
      <label htmlFor="gift-code" className="text-[11px] text-zinc-300">{T.gift.label}</label>
      <div className="flex gap-2 mt-1">
        <input id="gift-code" data-testid="gift-code" type="text" inputMode="text" autoComplete="off" autoCapitalize="characters" spellCheck={false}
          maxLength={20} value={code} disabled={busy || checking} placeholder="ABCD-EFGH-JKLM"
          onChange={(e) => { setCode(tidyCode(e.target.value)); setWhy(null); }}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void apply(); } }}
          className="flex-1 min-w-0 min-h-[44px] px-3 rounded-xl bg-white/5 border border-white/15 text-zinc-100 text-sm tracking-widest font-mono" />
        <button type="button" data-testid="gift-apply" disabled={busy || checking || !code} onClick={() => void apply()}
          className="min-h-[44px] px-4 rounded-xl border border-gold/40 text-gold-light text-sm font-semibold disabled:opacity-50">
          {checking ? T.gift.checking : T.gift.apply}
        </button>
      </div>
      {why && <p role="alert" data-testid="gift-error" className="text-[11px] text-rose-200 mt-2">{T.gift.errors[why]}</p>}
      <p className="text-[11px] text-zinc-400 mt-2">{T.gift.note}</p>
    </div>
  );
};
