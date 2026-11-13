// Finnish words of the older landing copy that survive the port (see copy.ts): the label of the legal pages' language switch,
// the brand line, and the landing page's transparency promise, which /try (src/try/copy.fi.ts result.transparency) repeats word
// for word. The landing's own words are src/landing/copy/fi.json: informal singular "sinä", as Finnish consumer shops write; the
// terms, privacy and withdrawal texts are formal ("te"), so the terms carry the same promise in their own register
// (src/legal/docs/terms.fi.ts). The iris is "iiris", "to restore" is "entisöidä" (the Finnish word for restoring a photograph).
import type { Copy } from './copy';

export const TRANSPARENCY_FI =
  'Väri tulee omasta valokuvastasi. Kohdissa, joissa puhelimesi ei saanut hienoimpia säikeitä talteen, tekoälymme entisöi ne.';

export const fi: Copy = { switchLabel: 'Kieli', brandTag: '' };
