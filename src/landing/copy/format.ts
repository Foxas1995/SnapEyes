// The {token} substitution and the path lookup of the landing copy. Pure and light on purpose: no JSON, no React, so the
// primitives in ../ui.tsx and the build's checks (scripts/check_texts.mjs reads TOKENS from here) can use it freely.
import type { CopyTokens } from './types';

/** {px}, {price}: a token is letters and digits in braces, and it is always a whole word of the sentence, never a piece of
 *  a word (Lithuanian and Hungarian inflect: a translator moves the whole token, never attaches an ending to it). */
export const TOKEN_RE = /\{([a-zA-Z0-9]+)\}/g;

/** The facts of the copy (en.json "facts", each language writes them its own way): filled in by the copy itself. */
export const FACT_TOKENS = ['px', 'square', 'printMax', 'printMaxCm', 'email', 'hours'] as const;

/** What the page gives (src/landing/prices.ts gives from, price, price2, max; the others are figures of the section). */
export const PAGE_TOKENS = ['from', 'price', 'price2', 'max', 'n', 'name', 'size', 'src', 'styles'] as const;

/** Every token a copy file may hold. A token outside this list is a typo (scripts/check_texts.mjs refuses it). */
export const TOKENS: readonly string[] = [...FACT_TOKENS, ...PAGE_TOKENS];

/** The tokens a string holds, in order. */
export function tokensIn(s: string): string[] {
  return [...s.matchAll(TOKEN_RE)].map((m) => m[1]);
}

/** The value at a dotted path ('hero.title', 'how.steps.0.b'); array items are addressed by their number. */
export function getPath(root: unknown, path: string): unknown {
  let o: unknown = root;
  for (const k of path.split('.')) {
    if (o === null || typeof o !== 'object') return undefined;
    o = Array.isArray(o) ? o[Number(k)] : (o as Record<string, unknown>)[k];
  }
  return o;
}

const warned = new Set<string>();

/** Dev only: a token that neither the page nor the facts gave stays in the sentence as {token}; say so once, loudly, so
 *  it is seen while the page is built and never by a visitor. (The production build removes this branch.) */
function warnLeft(out: string, source: string): void {
  const left = tokensIn(out);
  if (left.length === 0 || warned.has(source)) return;
  warned.add(source);
  console.error(`[landing copy] no value for {${left.join('}, {')}} in: ${source.slice(0, 140)}`);
}

/** Substitute {tokens}: the page's own values first, then the facts. An unknown token is left as it is (and reported in
 *  development). */
export function fill(text: string, facts: Readonly<Record<string, string>>, tokens?: CopyTokens): string {
  const out = text.replace(TOKEN_RE, (whole, k: string) => {
    const v = tokens?.[k];
    return v !== undefined && v !== null ? String(v) : facts[k] ?? whole;
  });
  if (import.meta.env.DEV) warnLeft(out, text);
  return out;
}
