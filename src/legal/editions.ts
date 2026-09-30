// The legal pages of each edition (src/shared/legal.ts legalEdition): the EU texts for the euro markets, the Australian
// edition for the au market and the Hungarian edition (the EU texts with the prices in forints) for the hu market.
// LegalApp shows the page's own; the build's order-mail pack carries all of them (src/legal/plain.ts), so the
// confirmation email of an order quotes the texts of its market. An edition has texts in the languages
// src/shared/legal.ts EDITION_LANGS lists for it (the Australian one: English and German).
import type { EditionDocs } from './types';
import type { LegalDocId, LegalEdition } from '../shared/legal';
import { PRIVACY, PRIVACY_AU } from './docs/privacy';
import { TERMS, TERMS_AU, TERMS_HU } from './docs/terms';
import { WITHDRAWAL, WITHDRAWAL_AU } from './docs/withdrawal';
import { IMPRINT, IMPRINT_AU } from './docs/imprint';

export const EDITIONS: Readonly<Record<LegalEdition, Readonly<Record<LegalDocId, EditionDocs>>>> = {
  eu: { privacy: PRIVACY, terms: TERMS, withdrawal: WITHDRAWAL, imprint: IMPRINT },
  au: { privacy: PRIVACY_AU, terms: TERMS_AU, withdrawal: WITHDRAWAL_AU, imprint: IMPRINT_AU },
  hu: { privacy: PRIVACY, terms: TERMS_HU, withdrawal: WITHDRAWAL, imprint: IMPRINT },
};
