// Croatian words of the older landing copy that survive the port (see copy.ts): the label of the legal pages' language switch,
// the brand line, and the landing page's transparency promise, which /try (src/try/copy.hr.ts result.transparency) and the
// terms (src/legal/docs/terms.hr.ts) repeat word for word. The landing's own words are src/landing/copy/hr.json: polite plural
// "vi", written in lower case inside a sentence as modern Croatian web copy does; the terms, privacy and withdrawal texts are
// formal. "Oko" is also the Croatian word for "about", so the copy writes "otprilike" for "about" and keeps "oko" for the eye.
import type { Copy } from './copy';

export const TRANSPARENCY_HR =
  'Boja dolazi s vaše vlastite fotografije. Gdje vaš mobitel nije mogao snimiti najfinija vlakna, naša ih umjetna inteligencija obnavlja.';

export const hr: Copy = { switchLabel: 'Jezik', brandTag: '' };
