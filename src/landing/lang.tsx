import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { COPY, copyFor, type Copy } from './copy';
import { useMarket } from '../shared/useMarket';
import { LANGS, LOCALES, detectLang, langAllowed, langFor, langQuery, rememberLang, type Lang } from '../shared/lang';
import { currentMarket, type Market } from '../shared/markets';

// The language rule lives in src/shared/lang.ts (?lang=, then the visitor's earlier choice, then the market's own
// language, then the browser's), shared with /try, /order and the legal pages.
export { detectLang };

// One URL per language, each its own canonical: English at /, the others at /?lang=de, /?lang=lt, /?lang=hu (index.html
// lists them all as hreflang alternates). index.html has no static canonical on purpose: this is the only one, so a
// rendered German page is never canonicalised to the English root.
const SITE_ORIGIN = 'https://snapeyes.com';
const canonicalUrl = (lang: Lang) => `${SITE_ORIGIN}/${langQuery(lang)}`;

export function setMeta(attr: 'name' | 'property', key: string, content: string) {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

/** The page's one rel=canonical, created on first use (any extra ones are removed). */
export function setCanonical(url: string) {
  const links = document.head.querySelectorAll<HTMLLinkElement>('link[rel="canonical"]');
  let canonical = links[0];
  links.forEach((l, i) => { if (i > 0) l.remove(); });
  if (!canonical) {
    canonical = document.createElement('link');
    canonical.rel = 'canonical';
    document.head.appendChild(canonical);
  }
  canonical.href = url;
}

/** Every meta tag of this kind, one per value (og:locale:alternate is repeated once per other language). */
function setMetaAll(attr: 'name' | 'property', key: string, values: string[]) {
  document.head.querySelectorAll(`meta[${attr}="${key}"]`).forEach((el) => el.remove());
  for (const v of values) {
    const el = document.createElement('meta');
    el.setAttribute(attr, key);
    el.setAttribute('content', v);
    document.head.appendChild(el);
  }
}

// What the head tags say about a language (the meta block of a copy): today's landing copy (./copy.ts) and the new
// landing's copy (./copy/en.json and the other languages) both have it.
interface HeadMeta { title: string; description: string; shareDescription: string; locale: string }

function writeHead(lang: Lang, meta: HeadMeta, alternateLocales: string[]) {
  const url = canonicalUrl(lang);
  setCanonical(url);
  setMeta('name', 'description', meta.description);
  setMeta('property', 'og:url', url);
  setMeta('property', 'og:locale', meta.locale);
  setMetaAll('property', 'og:locale:alternate', alternateLocales);
  setMeta('property', 'og:title', meta.title);
  setMeta('property', 'og:description', meta.shareDescription);
  setMeta('name', 'twitter:title', meta.title);
  setMeta('name', 'twitter:description', meta.shareDescription);
}

function applyHeadTags(lang: Lang, t: Copy, market: Market) {
  writeHead(lang, t.meta, LANGS.filter((l) => l !== lang && langAllowed(l, market)).map((l) => COPY[l].meta.locale));
}

/** The head of the new landing: the tab title, the description, the canonical, the Open Graph and Twitter tags, all from the
 *  meta of the language's copy (src/landing/copy/CopyProvider.tsx calls it once the language's words are here). The other
 *  languages' og:locale values come from src/shared/lang.ts LOCALES (scripts/check_texts.mjs checks the copy's own locale
 *  against it). */
export function applyLandingHead(lang: Lang, meta: HeadMeta, market: Market) {
  document.title = meta.title;
  writeHead(lang, meta, LANGS.filter((l) => l !== lang && langAllowed(l, market)).map((l) => LOCALES[l].og));
}

interface LangState {
  lang: Lang;
  t: Copy;
  setLang: (l: Lang) => void;
  /** A component that writes the head tags itself (the new landing's CopyProvider) claims them while it is mounted: this
   *  provider then leaves title, description and canonical alone (its own effect runs after the child's, so without a claim
   *  it would write today's copy over the new one). Returns the release. */
  claimHead: () => () => void;
}

const LangContext = createContext<LangState | null>(null);

// applyHead: the legal pages set their own title, description and canonical; without it the landing's tags apply.
export function LangProvider({ children, applyHead }: { children: ReactNode; applyHead?: (lang: Lang) => void }) {
  const [chosen, setChosen] = useState<Lang>(() => detectLang(currentMarket()));
  // the language the page shows: the visitor's, unless the market has no texts in it (the Australian market: English
  // and German only); the choice itself is kept, so going back to a market that has it shows it again
  const market = useMarket();
  const lang = langFor(chosen, market);

  const setLang = useCallback((l: Lang) => {
    setChosen(l);
    rememberLang(l);
  }, []);

  const headClaims = useRef(0);
  const claimHead = useCallback(() => {
    headClaims.current += 1;
    return () => { headClaims.current -= 1; };
  }, []);

  useEffect(() => {
    const t = COPY[lang];
    document.documentElement.lang = lang;
    if (headClaims.current > 0) return;
    if (applyHead) {
      applyHead(lang);
      return;
    }
    document.title = t.meta.title;
    applyHeadTags(lang, t, market);
  }, [lang, market, applyHead]);

  // the copy of the language, with the lines of the visitor's market where it has its own (copyFor: Australia)
  const value = useMemo(() => ({ lang, t: copyFor(lang, market), setLang, claimHead }), [lang, market, setLang, claimHead]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): LangState {
  const v = useContext(LangContext);
  if (!v) throw new Error('useLang outside LangProvider');
  return v;
}
