// The copy API (t, fmt, rich) bound to one language's words. Kept apart from ./CopyProvider.tsx (which reads the language, the market and the head tags) so that the
// build can give the same API to a component it renders in Node (src/landing/shell/gate.tsx): the words and the tokens are filled by this one function.
import { Fragment, type ReactNode } from 'react';
import type { Lang } from '../../shared/lang';
import { TOKEN_RE, fill, getPath } from './format';
import type { LandingCopy } from './index';
import type { CopyApi } from './useCopy';
import type { CopyPath, CopyTokens } from './types';

export function makeApi(c: LandingCopy, lang: Lang): CopyApi {
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
