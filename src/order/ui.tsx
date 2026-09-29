// The /order page's shared looks: its cards, buttons and spinner (./OrderApp.tsx, ./WithdrawPanel.tsx).
import type React from 'react';

export const CARD = 'bg-[#0b0e17] border border-white/10 rounded-2xl p-4 sm:p-5';
export const GOLD_BTN = 'w-full min-h-[48px] px-4 py-3 rounded-xl bg-gradient-to-r from-[#f5c542] to-[#d4af37] text-black text-sm font-bold flex items-center justify-center gap-2 text-center shadow-lg shadow-[#f5c542]/20 active:scale-[0.98]';
export const PLAIN_BTN = 'min-h-[44px] px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 text-center hover:bg-white/10';
export const LINK = 'underline underline-offset-4 decoration-white/30 hover:text-white';

export const Spinner: React.FC = () => (
  <span aria-hidden className="inline-block w-4 h-4 shrink-0 border-2 border-[#f5c542]/30 border-t-[#f5c542] rounded-full animate-spin" />
);
