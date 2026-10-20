// Types of ./py_source_slim.mjs for vite.config.ts (tsconfig.node.json checks that file with Node's module rules).
/** The files the pages import as text and the build slims, with the name of the literal that ends each. */
export const SLIM_FILES: Record<string, string>;
/** The text of a Python file of SLIM_FILES as the pages get it: the NAME = value lines of its head and its literal in compact JSON.
 *  Throws when the file does not have the shape the pages' readers expect or a reading would differ. */
export function slimPySource(src: string, file: string, literal: string): string;
