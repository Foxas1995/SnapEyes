// The legal pages of each edition (src/shared/legal.ts legalEdition): the EU texts for the euro markets, the Australian
// edition for the au market, the Hungarian edition (the EU texts with the prices in forints) for the hu market and the US
// edition for the us market.
// LegalApp shows the page's own; the build's order-mail pack carries all of them (src/legal/plain.ts), so the
// confirmation email of an order quotes the texts of its market. An edition has texts in the languages
// src/shared/legal.ts EDITION_LANGS lists for it (the Australian one: English and German; the Hungarian one: every
// language but Croatian, which is in the EU edition only; the US one: English only).
import type { EditionDocs } from './types';
import { EDITION_LANGS, type LegalDocId, type LegalEdition } from '../shared/legal';
import { PRIVACY, PRIVACY_AU, PRIVACY_US } from './docs/privacy';
import { TERMS, TERMS_AU, TERMS_HU, TERMS_US } from './docs/terms';
import { WITHDRAWAL, WITHDRAWAL_AU, WITHDRAWAL_US } from './docs/withdrawal';
import { IMPRINT, IMPRINT_AU, IMPRINT_US } from './docs/imprint';

/** The texts of a shared page in the languages of an edition only (the Hungarian edition shares the EU privacy policy,
 *  withdrawal information and legal notice, without their Croatian texts). */
const only = (docs: EditionDocs, edition: LegalEdition): EditionDocs =>
  Object.fromEntries(Object.entries(docs).filter(([l]) => (EDITION_LANGS[edition] as readonly string[]).includes(l)));

export const EDITIONS: Readonly<Record<LegalEdition, Readonly<Record<LegalDocId, EditionDocs>>>> = {
  eu: { privacy: PRIVACY, terms: TERMS, withdrawal: WITHDRAWAL, imprint: IMPRINT },
  au: { privacy: PRIVACY_AU, terms: TERMS_AU, withdrawal: WITHDRAWAL_AU, imprint: IMPRINT_AU },
  hu: { privacy: only(PRIVACY, 'hu'), terms: TERMS_HU, withdrawal: only(WITHDRAWAL, 'hu'), imprint: only(IMPRINT, 'hu') },
  us: { privacy: PRIVACY_US, terms: TERMS_US, withdrawal: WITHDRAWAL_US, imprint: IMPRINT_US },
};
