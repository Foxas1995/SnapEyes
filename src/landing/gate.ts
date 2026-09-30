// Which visitors get the new landing page, and which keep today's (BUILD_PLAN section 4, step 5: the language gate).
//
//   * a language whose landing copy is still an English stand-in (src/landing/copy/PLACEHOLDERS.txt: lt.json, hu.json today)
//     keeps today's landing: a Lithuanian or Hungarian advertisement has to be in that language;
//   * the forint market keeps today's landing too (the new page has no HUF button; ?m=hu is a review switch only).
//
// One rule for three readers: the page (src/App.tsx), the prerendered first screen (the plugin in vite.config.ts writes an
// inline script from it, so a visitor the new page does not serve never sees the English shell) and the check that proves
// both agree with src/shared/lang.ts (scripts/check_shell.mjs).
import { currencyOf, type Market } from '../shared/markets';
import type { Lang } from '../shared/lang';
import { COPY_LANGS } from './copy/index';

/** The languages the new landing speaks: every language whose copy is a translation. */
export const NEW_LANDING_LANGS: readonly Lang[] = COPY_LANGS;

/** Does a visitor reading this language in this market get the new landing? */
export function newLandingFor(lang: Lang, market: Market): boolean {
  return NEW_LANDING_LANGS.includes(lang) && currencyOf(market) !== 'huf';
}
