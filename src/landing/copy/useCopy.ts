// The hook and the context of the landing copy. Kept apart from ./CopyProvider.tsx and ./index.ts on purpose: this file
// holds no JSON and no loader, so src/landing/ui.tsx (which the legal pages also import, for the logo) can read the copy
// without the legal bundles carrying the landing's words.
import { createContext, useContext, type ReactNode } from 'react';
import type { Lang } from '../../shared/lang';
import type { CopyPath, CopyTokens, LandingCopy } from './types';

export interface CopyApi {
  /** The copy of the page, typed from en.json: the language's own words, with the Australian FAQ answers on the
   *  Australian market. Read it with plain property access (c.hero.title, c.how.steps.map(...)). */
  c: LandingCopy;
  /** The language of `c`: what the page shows. It lags the visitor's choice by a moment while that language's file loads. */
  lang: Lang;
  /** A string of the copy by its dotted path, {tokens} filled: t('hero.fromPrice', { from }). A path that is not a string
   *  of en.json does not compile. */
  t: (key: CopyPath, tokens?: CopyTokens) => string;
  /** The same substitution for a string you already hold (an item of a list of c): fmt(step.b). */
  fmt: (text: string, tokens?: CopyTokens) => string;
  /** A sentence with elements inside it (a bold price): rich(c.styles.priceOne, { price: <b>{p.art}</b> }). Every token
   *  must be given (or be a fact); the parts come back keyed, ready to render. */
  rich: (text: string, tokens: Readonly<Record<string, ReactNode>>) => ReactNode;
}

export const CopyContext = createContext<CopyApi | null>(null);

export function useCopy(): CopyApi {
  const v = useContext(CopyContext);
  if (!v) throw new Error('useCopy outside CopyProvider (src/landing/copy/CopyProvider.tsx)');
  return v;
}
