// Estonian words of the older landing copy that survive the port (see copy.ts): the label of the legal pages' language switch,
// the brand line, and the landing page's transparency promise, which /try (src/try/copy.et.ts result.transparency) and the
// terms (src/legal/docs/terms.et.ts) repeat word for word. The landing's own words are src/landing/copy/et.json: informal
// singular "sina", as Estonian consumer web shops write; the terms, privacy and withdrawal texts are formal ("teie").
// "Tehisintellekt" is written out in a sentence (the English "AI"); the iris is "iiris", the fibres "kiud".
import type { Copy } from './copy';

export const TRANSPARENCY_ET =
  'Värv tuleb sinu enda fotolt. Seal, kus sinu telefon ei suutnud kõige peenemaid kiude jäädvustada, taastab need meie tehisintellekt.';

export const et: Copy = { switchLabel: 'Keel', brandTag: '' };
