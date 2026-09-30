// Every link of the new landing that leaves the page for a legal page or /try, in one place, so none is written by hand.
// The legal links go only through src/shared/legal.ts (legalHref, withdrawFunctionHref: they carry ?lang= and, through
// editionHref, the market's edition m=au / m=hu exactly as the legal pack and the footer do today), the /try link through
// ./config.ts tryUrl (?lang= and m=). The links read the page's market when they are made, so each hook subscribes to it.
import { useMemo } from 'react';
import { useLang } from './lang';
import { useCopy } from './copy/useCopy';
import { tryUrl } from './config';
import { LEGAL_DOCS, legalHref, withdrawFunctionHref, type LegalDocId } from '../shared/legal';
import type { Lang } from '../shared/lang';
import { useMarket } from '../shared/useMarket';
import type { LandingCopy } from './copy/types';

export interface LegalLink {
  /** The four documents, then the online withdrawal function. */
  key: LegalDocId | 'withdrawFn';
  label: string;
  href: string;
}

/** The footer's legal links in the page's order (privacy, terms, withdrawal, legal notice) and the withdrawal function last,
 *  with the labels of the copy (scripts/check_texts.mjs checks they are the statutory ones of src/shared/legal.ts). */
export function legalLinkList(lang: Lang, footer: LandingCopy['footer']): LegalLink[] {
  return [
    ...LEGAL_DOCS.map((doc): LegalLink => ({ key: doc, label: footer.legal[doc], href: legalHref(doc, lang) })),
    { key: 'withdrawFn', label: footer.legal.withdrawFn, href: withdrawFunctionHref(lang) },
  ];
}

export function useLegalLinks(): LegalLink[] {
  const { lang } = useLang();
  const { c } = useCopy();
  const market = useMarket();
  // the market is read by legalHref itself; it is a dependency so the links follow the currency switch
  return useMemo(() => (market ? legalLinkList(lang, c.footer) : []), [lang, c.footer, market]);
}

/** One legal page (and optionally a section of it): the privacy policy next to the privacy promise, the terms of sale next
 *  to the prices. */
export function useLegalHref(doc: LegalDocId, section = ''): string {
  const { lang } = useLang();
  const market = useMarket();
  return useMemo(() => (market ? legalHref(doc, lang, section) : ''), [doc, lang, section, market]);
}

/** The address of the capture tool in the page's language and market: the target of every call to action. */
export function useTryHref(): string {
  const { lang } = useLang();
  const market = useMarket();
  return useMemo(() => (market ? tryUrl(lang) : ''), [lang, market]);
}
