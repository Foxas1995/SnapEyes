import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { COPY, type Copy, type Lang } from './copy';

const STORE_KEY = 'snapeyes.lang';

const isLang = (v: unknown): v is Lang => v === 'en' || v === 'de';

// ?lang= wins, then the visitor's own earlier choice, then the browser language (German for "de*").
export function detectLang(): Lang {
  try {
    const q = new URLSearchParams(window.location.search).get('lang');
    if (isLang(q)) return q;
  } catch { /* no URL access: fall through */ }
  try {
    const s = window.localStorage.getItem(STORE_KEY);
    if (isLang(s)) return s;
  } catch { /* storage blocked: fall through */ }
  const nav = typeof navigator !== 'undefined' ? navigator.language || '' : '';
  return nav.toLowerCase().startsWith('de') ? 'de' : 'en';
}

// One URL per language, each its own canonical: English at /, German at /?lang=de (index.html lists both as
// hreflang alternates). index.html has no static canonical on purpose: this is the only one, so the rendered
// German page is never canonicalised to the English root.
const SITE_ORIGIN = 'https://snapeyes.com';
const canonicalUrl = (lang: Lang) => (lang === 'de' ? `${SITE_ORIGIN}/?lang=de` : `${SITE_ORIGIN}/`);

function setMeta(attr: 'name' | 'property', key: string, content: string) {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function applyHeadTags(lang: Lang, t: Copy) {
  const url = canonicalUrl(lang);
  const links = document.head.querySelectorAll<HTMLLinkElement>('link[rel="canonical"]');
  let canonical = links[0];
  links.forEach((l, i) => { if (i > 0) l.remove(); });
  if (!canonical) {
    canonical = document.createElement('link');
    canonical.rel = 'canonical';
    document.head.appendChild(canonical);
  }
  canonical.href = url;
  setMeta('name', 'description', t.meta.description);
  setMeta('property', 'og:url', url);
  setMeta('property', 'og:locale', t.meta.locale);
  setMeta('property', 'og:locale:alternate', COPY[lang === 'de' ? 'en' : 'de'].meta.locale);
  setMeta('property', 'og:title', t.meta.title);
  setMeta('property', 'og:description', t.meta.shareDescription);
  setMeta('name', 'twitter:title', t.meta.title);
  setMeta('name', 'twitter:description', t.meta.shareDescription);
}

interface LangState { lang: Lang; t: Copy; setLang: (l: Lang) => void }

const LangContext = createContext<LangState | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectLang);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try { window.localStorage.setItem(STORE_KEY, l); } catch { /* per-visitor convenience only */ }
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('lang', l);
      window.history.replaceState(null, '', url);
    } catch { /* keep the page working without history access */ }
  }, []);

  useEffect(() => {
    const t = COPY[lang];
    document.documentElement.lang = lang;
    document.title = t.meta.title;
    applyHeadTags(lang, t);
  }, [lang]);

  const value = useMemo(() => ({ lang, t: COPY[lang], setLang }), [lang, setLang]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): LangState {
  const v = useContext(LangContext);
  if (!v) throw new Error('useLang outside LangProvider');
  return v;
}
