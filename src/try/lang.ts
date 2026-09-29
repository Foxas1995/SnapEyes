// The capture tool's language, by the landing page's own rule (src/landing/lang.tsx detectLang and its switch):
// ?lang= wins, then the visitor's earlier choice (localStorage "snapeyes.lang", shared by both pages), then the
// browser language (German for "de*"). A copy, not an import: lang.tsx also pulls in the whole landing copy,
// which would then ride in the chunk both pages load. Keep the two in step.
import type { Lang } from '../landing/copy';

export type { Lang };

const STORE_KEY = 'snapeyes.lang';   // src/landing/lang.tsx STORE_KEY

export const isLang = (v: unknown): v is Lang => v === 'en' || v === 'de';

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

/** The visitor picked a language on /try: remember it for both pages and put it in the URL, as the landing's
 *  switch does, so a reload or the way back to the landing page keeps it. */
export function rememberLang(l: Lang): void {
  try { window.localStorage.setItem(STORE_KEY, l); } catch { /* per-visitor convenience only */ }
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('lang', l);
    window.history.replaceState(null, '', url);
  } catch { /* keep the page working without history access */ }
}
