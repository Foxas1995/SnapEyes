// The types of the landing copy. Type-only (nothing here is bundled): the shape of the page's words IS the shape of
// en.json, so every key a component reads is checked by the TypeScript compiler, and every other language's file
// must fit the same type (index.ts asCopy).
import type en from './en.json';

/** The copy of one language: exactly the keys of en.json (nested objects, arrays, strings, a few numbers). */
export type LandingCopy = typeof en;

type Join<P extends string, K extends string | number> = P extends '' ? `${K}` : `${P}.${K}`;

/** Every dotted path to a STRING of the copy, array items as numbers: 'hero.title', 'how.steps.0.b'. t() takes these,
 *  so a mistyped key is a compile error and a path to an object or an array is refused. */
export type CopyPath<T = LandingCopy, P extends string = ''> = T extends string
  ? P
  : T extends readonly (infer U)[]
    ? CopyPath<U, Join<P, number>>
    : T extends object
      ? { [K in keyof T & string]: CopyPath<T[K], Join<P, K>> }[keyof T & string]
      : never;

/** What t() and fmt() may substitute: {price} and the like. The facts of the copy ({px}, {square}, {printMax},
 *  {printMaxCm}, {email}, {hours}) are filled in by the copy itself. */
export type CopyTokens = Readonly<Record<string, string | number>>;
