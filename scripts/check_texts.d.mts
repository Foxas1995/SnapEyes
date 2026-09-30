// Types of ./check_texts.mjs for vite.config.ts (tsconfig.node.json checks that file with Node's module rules).
/** Sample arguments per function of the copy dictionaries (a function without an entry stops the text check). */
export const SAMPLES: Record<string, unknown[][]>;
/** sha256 of the consent texts of each consent version (a changed text under the same version fails the text check). */
export const CONSENT_FINGERPRINTS: Record<string, string>;
/** Every problem found in the legal pack the order confirmation email carries (the object legalMailPack() makes, or the
 *  built /legal/order-mail.json parsed): every edition complete in its languages, its prices, its contract languages, and
 *  no dash, typographic slip or untranslated English in a Lithuanian or Hungarian text. legal, markets: the loaded
 *  src/shared/legal.ts and src/shared/markets.ts. */
export function checkPack(pack: any, legal: any, markets: any): string[];
/** The withdrawal waiver and the withdrawal statement as the pages (src/) and the server (api/) have them, word for word in
 *  every language. Reads the Python files as text. legal, orderCopy: the loaded src/shared/legal.ts and src/order/copy.ts. */
export function checkServerTexts(root: string, legal: any, orderCopy: any): string[];
/** The customer sentences of api/analyze.py: the same keys and placeholders in German, Lithuanian and Hungarian, and a
 *  sentence in each for every block reason (and a block on the /try page). Reads the Python files as text. */
export function checkAnalyzeTexts(root: string): string[];
/** Every problem found in the texts, as sentences ([] when they are sound). load: a module of src/ through Vite's
 *  module runner; root: the repository. */
export function checkTexts(load: (path: string) => Promise<any>, root: string): Promise<string[]>;
