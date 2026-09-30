// The site's languages and the ONE rule that picks the language of a page. Plain data and functions, no React, so the
// landing page, /try, the order page and the legal pages (and the build's legal pack) all read the same rule.
//
// The language and the market (src/shared/markets.ts) are independent: the language comes from the link (?lang=), the
// market from the link (?m=), and neither changes the other by itself. Where a market has a language of its own it is
// only a DEFAULT (see detectLang), and nothing here ever redirects.
//
// Which languages a market can be read in: the languages of its legal edition (src/shared/legal.ts EDITION_LANGS).
// The Australian edition has English and German texts only, so a page of that market never shows Lithuanian or
// Hungarian: a link that asks for one there is read as if it asked for nothing (langFor, detectLang).
import { DEFAULT_MARKET, MARKETS, currentMarket, type Market } from './markets';
import { EDITION_LANGS, legalEdition } from './legal';

export type Lang = 'en' | 'de' | 'lt' | 'hu';

/** Every language of the site, in the order the language switch shows them. */
export const LANGS: readonly Lang[] = ['en', 'de', 'lt', 'hu'];

/** A language's name in itself (the tooltip of its switch button). */
export const LANG_NAMES: Record<Lang, string> = { en: 'English', de: 'Deutsch', lt: 'Lietuvių', hu: 'Magyar' };

/** What each language needs outside its texts: the BCP 47 tag of the page (<html lang>), the Open Graph locale, the
 *  locale Intl formats numbers and dates by, and the page's own address (English at /, the others at ?lang=). */
export interface LocaleInfo { html: string; og: string; intl: string; query: string }
export const LOCALES: Record<Lang, LocaleInfo> = {
  en: { html: 'en', og: 'en_GB', intl: 'en-GB', query: '' },
  de: { html: 'de', og: 'de_DE', intl: 'de-DE', query: '?lang=de' },
  lt: { html: 'lt', og: 'lt_LT', intl: 'lt-LT', query: '?lang=lt' },
  hu: { html: 'hu', og: 'hu_HU', intl: 'hu-HU', query: '?lang=hu' },
};

export const isLang = (v: unknown): v is Lang => typeof v === 'string' && (LANGS as readonly string[]).includes(v);

/** The languages a market can be read in: the ones its legal edition has texts in. */
export const marketLangs = (m: Market): readonly Lang[] => EDITION_LANGS[legalEdition(m)];

/** Can this market be read in this language? */
export const langAllowed = (l: Lang, m: Market): boolean => marketLangs(m).includes(l);

/** The market's own language, when it names one that is not just English (the site's language of last resort, which
 *  the browser's own language must still be able to beat: a German browser on ?m=au stays German, as it always was).
 *  lt: Lithuanian, hu: Hungarian. */
export function marketDefaultLang(m: Market): Lang | null {
  const d = MARKETS[m]?.lang ?? MARKETS[DEFAULT_MARKET].lang;
  return isLang(d) && d !== 'en' && langAllowed(d, m) ? d : null;
}

/** The language of the browser: German, Lithuanian and Hungarian are recognised ("de-AT", "lt", "hu-HU"), any other
 *  is English, as before. */
export function navigatorLang(): Lang {
  const nav = typeof navigator !== 'undefined' ? (navigator.language || '').toLowerCase() : '';
  return nav.startsWith('de') ? 'de' : nav.startsWith('lt') ? 'lt' : nav.startsWith('hu') ? 'hu' : 'en';
}

export const LANG_STORE_KEY = 'snapeyes.lang';

/** The language of a page, for the market the page shows: ?lang= wins, then the visitor's own earlier choice
 *  (localStorage "snapeyes.lang", shared by every page), then the market's own language (lt: Lithuanian, hu:
 *  Hungarian; en is no default, see marketDefaultLang), then the browser's language, then English. A language the
 *  market's edition has no texts in (Lithuanian or Hungarian on the Australian market) counts as not asked. */
export function detectLang(market: Market = currentMarket()): Lang {
  const ok = (v: unknown): v is Lang => isLang(v) && langAllowed(v, market);
  try {
    const q = new URLSearchParams(window.location.search).get('lang');
    if (ok(q)) return q;
  } catch { /* no URL access: fall through */ }
  try {
    const s = window.localStorage.getItem(LANG_STORE_KEY);
    if (ok(s)) return s;
  } catch { /* storage blocked: fall through */ }
  const own = marketDefaultLang(market);
  if (own) return own;
  const nav = navigatorLang();
  return langAllowed(nav, market) ? nav : 'en';
}

/** The language a page shows: the visitor's, unless this market has no texts in it (then the market's own, else
 *  English). The visitor's choice itself is kept, so going back to a market that has it shows it again. */
export function langFor(lang: Lang, market: Market = currentMarket()): Lang {
  if (langAllowed(lang, market)) return lang;
  const own = MARKETS[market]?.lang;
  return isLang(own) && langAllowed(own, market) ? own : 'en';
}

/** The visitor picked a language: remember it for every page and put it in the address, so a reload or the way to
 *  another page keeps it. */
export function rememberLang(l: Lang): void {
  try { window.localStorage.setItem(LANG_STORE_KEY, l); } catch { /* per-visitor convenience only */ }
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('lang', l);
    window.history.replaceState(null, '', url);
  } catch { /* keep the page working without history access */ }
}

/** The page's own address per language for the canonical link and the language alternates: English at /, the others
 *  at ?lang= (index.html and the sitemap list them all as hreflang alternates). */
export const langQuery = (l: Lang): string => LOCALES[l].query;
