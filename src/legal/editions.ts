// The legal pages of each edition (src/shared/legal.ts legalEdition): the EU texts for every market but Australia,
// and the Australian edition for the au market. LegalApp shows the page's own; the build's order-mail pack carries
// both (src/legal/plain.ts), so the confirmation email of an order quotes the texts of its market.
import type { LegalDocs } from './types';
import type { LegalDocId, LegalEdition } from '../shared/legal';
import { PRIVACY, PRIVACY_AU } from './docs/privacy';
import { TERMS, TERMS_AU } from './docs/terms';
import { WITHDRAWAL, WITHDRAWAL_AU } from './docs/withdrawal';
import { IMPRINT, IMPRINT_AU } from './docs/imprint';

export const EDITIONS: Readonly<Record<LegalEdition, Readonly<Record<LegalDocId, LegalDocs>>>> = {
  eu: { privacy: PRIVACY, terms: TERMS, withdrawal: WITHDRAWAL, imprint: IMPRINT },
  au: { privacy: PRIVACY_AU, terms: TERMS_AU, withdrawal: WITHDRAWAL_AU, imprint: IMPRINT_AU },
};
