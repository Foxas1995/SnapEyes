// The few words of the older landing copy that survive the landing v2 port (the new landing's words are src/landing/copy/*.json,
// read through src/landing/copy/useCopy.ts). Two kinds of reader are left:
//   * the pages that are not the landing: the legal pages' language switch and logo line (src/landing/lang.tsx useLang().t: the
//     label of the switch group and the brand line under the logo);
//   * the sentences other pages repeat word for word: the transparency promise of /try and of the terms (TRANSPARENCY_* here and
//     in copy.lt.ts and copy.hu.ts: src/try/copy.ts, copy.lt.ts, copy.hu.ts and the legal texts say the same words) and the
//     question of the FAQ item about withdrawing, which scripts/check_texts.mjs pins in the new copy.
import type { Lang } from '../shared/lang';
import { lt } from './copy.lt';
import { hu } from './copy.hu';

export type { Lang };

export interface Copy {
  /** The accessible name of the language switch of the legal pages. */
  switchLabel: string;
  /** The line under the logo. */
  brandTag: string;
}

export const TRANSPARENCY_EN = 'Colour from your own photo. Where your phone could not capture the finest fibres, our AI restores them.';
export const TRANSPARENCY_DE = 'Die Farbe stammt aus Ihrem eigenen Foto. Wo Ihr Smartphone die feinsten Fasern nicht erfassen konnte, stellt unsere KI sie wieder her.';

/** The question of the FAQ item "withdraw": the Australian market answers it in its own words (faqAu in the copy files), and the
 *  words of the question are not to drift (scripts/check_texts.mjs). Only English and German keyed on them in the old landing. */
export const WITHDRAW_Q: Record<'en' | 'de', string> = { en: 'Can I withdraw from an order?', de: 'Kann ich eine Bestellung widerrufen?' };

const en: Copy = { switchLabel: 'Language', brandTag: 'Private Atelier' };
const de: Copy = { switchLabel: 'Sprache', brandTag: 'Private Atelier' };

export const COPY: Record<Lang, Copy> = { en, de, lt, hu };
