// The copy of the new landing: ALL its words live in JSON, one file per language in this folder (en.json, de.json, lt.json,
// hu.json), the same keys in each. English is bundled with the page; every other language is its own chunk, loaded when
// the page needs it (loadCopy). The shape of the words is the shape of en.json (./types.ts), so a component cannot read
// a key that does not exist, and a language file that does not fit the type does not compile (asCopy below).
//
// A language's file has the keys and {tokens} of en.json, and scripts/check_texts.mjs checks that and the words (a dash, an
// untranslated sentence, the legal labels, the honesty lines). All four languages of the site (src/shared/lang.ts LANGS) have
// their translation here.
//
// A language that src/shared/lang.ts lists (LANGS) and has no file here fails the build twice: the loader table below is
// a Record over those languages (tsc), and scripts/check_texts.mjs wants every file (vite build).
import en from './en.json';
import type { Lang } from '../../shared/lang';
import { legalEdition } from '../../shared/legal';
import type { Market } from '../../shared/markets';
import type { CopyPath, CopyTokens, LandingCopy } from './types';
import { fill, getPath } from './format';

export type { CopyPath, CopyTokens, LandingCopy };
export { fill, getPath };

/** A language's file must have the type of en.json: compile-time proof that no key is missing, added or another kind. */
const asCopy = (c: LandingCopy): LandingCopy => c;

/** English: part of the page, always at hand. */
export const COPY_EN: LandingCopy = en;

const LOADERS: Record<Exclude<Lang, 'en'>, () => Promise<LandingCopy>> = {
  de: () => import('./de.json').then((m) => asCopy(m.default)),
  lt: () => import('./lt.json').then((m) => asCopy(m.default)),
  hu: () => import('./hu.json').then((m) => asCopy(m.default)),
};

const loaded = new Map<Lang, LandingCopy>([['en', COPY_EN]]);
const loading = new Map<Lang, Promise<LandingCopy>>();
const failed = new Set<Lang>();
const listeners = new Set<() => void>();
let version = 0;

function changed(): void {
  version += 1;
  listeners.forEach((l) => l());
}

/** A counter that goes up whenever a language's file arrives or fails to (for useSyncExternalStore: CopyProvider re-renders
 *  on it). subscribeCopy(listener) returns the unsubscribe. */
export const copyVersion = (): number => version;
export function subscribeCopy(listener: () => void): () => void {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

/** The copy of a language if it is here already (English always is), else undefined. */
export function peekCopy(lang: Lang): LandingCopy | undefined {
  return loaded.get(lang);
}

/** Did fetching this language's file fail (offline, a stale deploy)? The page then shows English. */
export function copyFailed(lang: Lang): boolean {
  return failed.has(lang);
}

/** The copy of a language: at once when it is here, else after its file is fetched (once per page load; a failure is
 *  remembered, see copyFailed). */
export function loadCopy(lang: Lang): Promise<LandingCopy> {
  const have = loaded.get(lang);
  if (have) return Promise.resolve(have);
  if (lang === 'en') return Promise.resolve(COPY_EN);
  let p = loading.get(lang);
  if (!p) {
    p = LOADERS[lang]().then(
      (c) => {
        loaded.set(lang, c);
        loading.delete(lang);
        changed();
        return c;
      },
      (e: unknown) => {
        loading.delete(lang);
        failed.add(lang);
        changed();
        throw e;
      },
    );
    loading.set(lang, p);
  }
  return p;
}

/** Start fetching a language's file without waiting for it (call it as early as the language is known, for instance with
 *  detectLang() before the first render, so a German visitor's file travels while the page boots). A file that failed once
 *  is not asked for again in this page load. */
export function preloadCopy(lang: Lang): void {
  if (failed.has(lang)) return;
  void loadCopy(lang).catch(() => undefined);
}

// ---------------------------------------------------------------------------------------------------- the market layer

// The Australian market's lines (src/shared/legal.ts legalEdition "au") replace the matching FAQ items, by id, in place of
// the language's own: the answer about cancelling keeps the Australian Consumer Law (its guarantees cannot be excluded,
// so nothing may read as "no refunds"), and "what if I do not like the result" makes no promise of its own to redo a
// file (see src/legal/docs/terms.ts TERMS_AU). The words are the copy's own (faqAu in each language's file).
const auCopies = new WeakMap<LandingCopy, LandingCopy>();

/** The copy of a language for the visitor's market: the language's own, with the FAQ answers of faqAu in place of the items
 *  with the same id on the Australian market. Same object back for the same copy (stable for memoised components). */
export function copyForMarket(copy: LandingCopy, market: Market): LandingCopy {
  if (legalEdition(market) !== 'au') return copy;
  let au = auCopies.get(copy);
  if (!au) {
    const own = copy.faqAu as Readonly<Record<string, { q: string; a: string } | undefined>>;
    const items = copy.faq.items.map((it) => {
      const o = Object.prototype.hasOwnProperty.call(own, it.id) ? own[it.id] : undefined;
      return o ? { id: it.id, q: o.q, a: o.a } : it;
    });
    au = { ...copy, faq: { ...copy.faq, items } };
    auCopies.set(copy, au);
  }
  return au;
}

/** One question and answer of the FAQ as the page prints it. */
export interface FaqEntry { id: string; q: string; a: string }

/** The FAQ items as the page prints them: the plain text while ordering is not open, the "open" variant of an item (qOpen,
 *  aOpen) once it is. Items the Australian layer replaced (copyForMarket) have no open variant and stay as they are. */
export function faqEntries(copy: LandingCopy, open: boolean): FaqEntry[] {
  return copy.faq.items.map((it) => (open ? { id: it.id, q: it.qOpen || it.q, a: it.aOpen || it.a } : { id: it.id, q: it.q, a: it.a }));
}
