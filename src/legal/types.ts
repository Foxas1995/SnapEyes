// The shape of a legal page. Text may carry two kinds of inline markup, parsed by src/legal/Inline.tsx:
//   [label](href)  a link. href: "doc:terms" or "doc:terms#defects" (another legal page, same language),
//                  "#section" (this page), "/path?query" (another page of this site, such as the online
//                  withdrawal function), "mailto:..." or "https://..." (external, opens in a new tab)
//   **text**       strong emphasis
import type { Lang } from '../shared/lang';

export type Block =
  | string                                  // a paragraph
  | { ul: string[] }                        // a bulleted list
  | { dl: Array<[string, string]> }         // label and value rows (the legal notice, retention periods)
  | { box: string[]; label?: string };      // a framed block: the model form, the checkout checkbox text

export interface LegalSection {
  id: string;        // the #anchor, stable across languages so links survive a language switch
  title: string;
  blocks: Block[];
}

export interface LegalDoc {
  title: string;       // h1 and the browser tab
  description: string; // meta description
  lead?: string;
  toc?: boolean;       // show a contents list (long documents)
  numbered?: boolean;  // number the section headings
  sections: LegalSection[];
}

export type LegalDocs = Record<Lang, LegalDoc>;

/** The texts of one edition (src/shared/legal.ts legalEdition): the languages EDITION_LANGS lists for it. The
 *  Australian edition has English and German only. */
export type EditionDocs = Partial<Record<Lang, LegalDoc>>;
