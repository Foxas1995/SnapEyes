// The /order page's shared looks: its cards, buttons and spinner (./OrderApp.tsx, ./WithdrawPanel.tsx).
import type React from 'react';
import { Dot } from '../motion/Tick';

export const CARD = 'bg-[#0b0e17] border border-white/10 rounded-2xl p-4 sm:p-5';
// fx-gold (src/motion/flow.css): a flat fill that brightens on hover and presses to .97, a contact shadow and no halo
export const GOLD_BTN = 'fx-gold w-full min-h-[48px] px-4 py-3 rounded-xl text-sm font-bold flex items-center justify-center gap-2 text-center';
export const PLAIN_BTN = 'min-h-[44px] px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-sm font-semibold flex items-center justify-center gap-2 text-center hover:bg-white/10';
export const LINK = 'underline underline-offset-4 decoration-white/30 hover:text-white';

/** A button that has been pressed, a step that is being worked on: a still gold dot (src/motion/Tick.tsx). The one thing on these pages that turns is the
 *  waiting arc, and only where something is really being made or waited for. */
export const Spinner: React.FC = () => <Dot />;
