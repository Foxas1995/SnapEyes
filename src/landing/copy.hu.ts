// Hungarian words of the older landing copy that survive the port (see copy.ts): the label of the legal pages' language switch,
// the brand line, and the landing page's transparency promise, which /try (src/try/copy.hu.ts result.transparency) and the
// terms (src/legal/docs/terms.hu.ts) repeat word for word. The landing's own words are src/landing/copy/hu.json: friendly "te"
// (tegeződés), as Hungarian iris studios and gift shops write; the terms, privacy and withdrawal texts are in "Ön".
import type { Copy } from './copy';

export const TRANSPARENCY_HU =
  'A szín a saját fotódból származik. Ahol a telefonod nem tudta rögzíteni a legfinomabb rostokat, ott a mesterséges intelligenciánk állítja helyre őket.';

export const hu: Copy = { switchLabel: 'Nyelv', brandTag: 'Private Atelier' };
