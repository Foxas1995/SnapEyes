// Gives the new landing its words: the copy of the page's language (./index.ts), the visitor's market layer on top (the
// Australian FAQ answers), t()/fmt()/rich() bound to that copy, and the page's head tags (title, description, share
// texts) written from the copy's own meta.
//
// Inside <LangProvider> (src/landing/lang.tsx), which still decides WHICH language the page is in:
//   <LangProvider><CopyProvider fallback={...}>...</CopyProvider></LangProvider>
//
// Loading: English is part of the page, so an English page renders at once. Another language's file is fetched when the
// page first needs it; until it arrives a first render shows `fallback` (the prerendered shell stays on screen under
// createRoot, so a visitor sees the shell, never half English text), and a later switch keeps the language on screen until
// the new one is here (no flash of English on the way from German to Lithuanian). A file that cannot be fetched falls back
// to English. Call preloadCopy(detectLang()) in the entry file to start the fetch before React renders anything.
import { Fragment, useEffect, useLayoutEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from 'react';
import { applyLandingHead, useLang } from '../lang';
import { useMarket } from '../../shared/useMarket';
import type { Lang } from '../../shared/lang';
import { TOKEN_RE, fill, getPath } from './format';
import { copyFailed, copyForMarket, copyVersion, peekCopy, preloadCopy, subscribeCopy, type LandingCopy } from './index';
import { CopyContext, type CopyApi } from './useCopy';
import type { CopyPath, CopyTokens } from './types';

function makeApi(c: LandingCopy, lang: Lang): CopyApi {
  const facts: Readonly<Record<string, string>> = c.facts;
  const fmt = (text: string, tokens?: CopyTokens) => fill(text, facts, tokens);
  const t = (key: CopyPath, tokens?: CopyTokens) => {
    const v = getPath(c, key);
    return typeof v === 'string' ? fill(v, facts, tokens) : '';
  };
  // a sentence with elements in it: the text between the tokens stays text, each token becomes its value
  const rich = (text: string, tokens: Readonly<Record<string, ReactNode>>): ReactNode => {
    const out: ReactNode[] = [];
    let last = 0;
    for (const m of text.matchAll(TOKEN_RE)) {
      const at = m.index ?? 0;
      if (at > last) out.push(<Fragment key={`t${last}`}>{text.slice(last, at)}</Fragment>);
      const k = m[1];
      out.push(<Fragment key={`k${at}`}>{k in tokens ? tokens[k] : facts[k] ?? m[0]}</Fragment>);
      last = at + m[0].length;
    }
    if (last < text.length) out.push(<Fragment key={`t${last}`}>{text.slice(last)}</Fragment>);
    return out;
  };
  return { c, lang, t, fmt, rich };
}

export function CopyProvider({ children, fallback = null }: { children: ReactNode; fallback?: ReactNode }) {
  const { lang: want, claimHead } = useLang();
  const market = useMarket();

  // re-render when a language's file arrives or fails (the loader is outside React)
  useSyncExternalStore(subscribeCopy, copyVersion, copyVersion);
  useEffect(() => { preloadCopy(want); }, [want]);

  // the language whose words are on screen: the wanted one once its file is here (English if it could not be fetched),
  // until then the one shown before (nothing yet on a first render: the fallback)
  const [kept, setKept] = useState<Lang | null>(() => (peekCopy(want) ? want : null));
  const ready: Lang | null = peekCopy(want) ? want : copyFailed(want) ? 'en' : null;
  if (ready !== null && ready !== kept) setKept(ready);     // adjusting state while rendering, the documented pattern
  const shown = ready ?? kept;

  const base = shown ? peekCopy(shown) : undefined;
  const copy = useMemo(() => (base ? copyForMarket(base, market) : null), [base, market]);
  const api = useMemo(() => (copy && shown ? makeApi(copy, shown) : null), [copy, shown]);

  // the head tags are this component's: LangProvider keeps its hands off them while it is mounted
  useLayoutEffect(() => claimHead(), [claimHead]);
  useEffect(() => {
    if (copy && shown) applyLandingHead(shown, copy.meta, market);
  }, [copy, shown, market]);

  if (!api) return <>{fallback}</>;
  return <CopyContext.Provider value={api}>{children}</CopyContext.Provider>;
}
