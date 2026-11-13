// Latvian words of the older landing copy that survive the port (see copy.ts): the label of the legal pages' language switch,
// the brand line, and the landing page's transparency promise, which /try (src/try/copy.lv.ts result.transparency) and the
// terms (src/legal/docs/terms.lv.ts) repeat word for word. The landing's own words are src/landing/copy/lv.json: polite plural
// "jūs", written in lower case inside a sentence as Latvian web copy does; the terms, privacy and withdrawal texts are formal.
// "AI" is "mākslīgais intelekts" (MI only in the shortest labels).
import type { Copy } from './copy';

export const TRANSPARENCY_LV =
  'Krāsa nāk no jūsu pašu fotogrāfijas. Tur, kur telefons nespēja uztvert vissmalkākās šķiedras, tās atjauno mūsu mākslīgais intelekts.';

export const lv: Copy = { switchLabel: 'Valoda', brandTag: '' };
