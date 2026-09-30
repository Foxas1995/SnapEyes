import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { COPY, copyFor, type Copy } from './copy';
import { useMarket } from '../shared/useMarket';
import { LANGS, detectLang, langAllowed, langFor, langQuery, rememberLang, type Lang } from '../shared/lang';
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

function applyHeadTags(lang: Lang, t: Copy, market: Market) {
  const url = canonicalUrl(lang);
  setCanonical(url);
  setMeta('name', 'description', t.meta.description);
  setMeta('property', 'og:url', url);
  setMeta('property', 'og:locale', t.meta.locale);
  setMetaAll('property', 'og:locale:alternate', LANGS.filter((l) => l !== lang && langAllowed(l, market)).map((l) => COPY[l].meta.locale));
  setMeta('property', 'og:title', t.meta.title);
  setMeta('property', 'og:description', t.meta.shareDescription);
  setMeta('name', 'twitter:title', t.meta.title);
  setMeta('name', 'twitter:description', t.meta.shareDescription);
}

interface LangState { lang: Lang; t: Copy; setLang: (l: Lang) => void }

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

  useEffect(() => {
    const t = COPY[lang];
    document.documentElement.lang = lang;
    if (applyHead) {
      applyHead(lang);
      return;
    }
    document.title = t.meta.title;
    applyHeadTags(lang, t, market);
  }, [lang, market, applyHead]);

  // the copy of the language, with the lines of the visitor's market where it has its own (copyFor: Australia)
  const value = useMemo(() => ({ lang, t: copyFor(lang, market), setLang }), [lang, market, setLang]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): LangState {
  const v = useContext(LangContext);
  if (!v) throw new Error('useLang outside LangProvider');
  return v;
}
