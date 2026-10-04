// Types of ./check_styles.mjs for vite.config.ts (tsconfig.node.json checks that file with Node's module rules).
/** The sub-rules of items 4 and 7 that wait for work package 12's texts (a number of styles in a string, a maximum number of eyes in the
 *  terms, the run-time tokens of the landing's pricing rows): built and tested, not enforced until this is true. */
export const WP12_RULES: boolean;
/** Every layout id a style may name. */
export const LAYOUT_IDS: string[];
/** Files outside the registry that may write a style id, with the reason. */
export const ID_ALLOW: Record<string, string>;
/** Every problem found in the style registry and in what reads it, as sentences ([] when it is sound). load: a module of src/ through
 *  Vite's module runner; without it the checks that need the page code are left out. */
export function checkStyles(root: string, load?: (path: string) => Promise<any>): Promise<string[]>;
/** One line for the build log: how many styles at which stages, and the registry hash. */
export function describeRegistry(root: string): string;
