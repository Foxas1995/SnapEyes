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
import { useEffect, useLayoutEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from 'react';
import { applyLandingHead, useLang } from '../lang';
import { useMarket } from '../../shared/useMarket';
import type { Lang } from '../../shared/lang';
import { copyFailed, copyForMarket, copyVersion, peekCopy, preloadCopy, subscribeCopy } from './index';
import { CopyContext } from './useCopy';
import { makeApi } from './makeApi';

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
