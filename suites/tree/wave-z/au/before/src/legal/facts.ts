// The seller facts and prices as the legal texts print them. Every value comes from src/landing/config.ts, so the
// landing page, the checkout and the legal pages can never disagree.
import type { Lang } from '../landing/copy';
import { CONTACT_EMAIL, DELIVERY_MAX_HOURS, MAX_EYES, PHONE_OMITTED_BY_OWNER, PRICE_CENTS, SELLER } from '../landing/config';
import { money } from '../shared/markets';

export const company = (lang: Lang) => (lang === 'de' ? `MB „${SELLER.name}“` : `MB "${SELLER.name}"`);
export const country = (lang: Lang) => (lang === 'de' ? 'Litauen' : 'Lithuania');
export const address = (lang: Lang) => `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${country(lang)}`;

/** The contact email as a mailto link in the inline markup. */
export const MAIL = `[${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL})`;

/** ", phone +370 ..." while SELLER.phone is set, else '': for sentences that name the seller's contact details. */
export const phoneSuffix = (lang: Lang) => (SELLER.phone ? (lang === 'de' ? `, Telefon ${SELLER.phone}` : `, phone ${SELLER.phone}`) : '');

/** ", represented by ..." while SELLER.representative is set, else ''. */
export const representedSuffix = (lang: Lang) =>
  SELLER.representative ? (lang === 'de' ? `, vertreten durch ${SELLER.representative}` : `, represented by ${SELLER.representative}`) : '';

/** The name, postal address and email: exactly what the model withdrawal FORM's "To:" line asks for (Annex I(B)
 *  Directive 2011/83/EU as amended by Directive (EU) 2019/2161; Anlage 2 EGBGB), with no telephone number. */
export const formLine = (lang: Lang) => `${company(lang)}, ${address(lang)}, ${lang === 'de' ? 'E-Mail' : 'email'}: ${CONTACT_EMAIL}`;

/** The contact details for the model withdrawal INFORMATION's "[2]" (Annex I(A) note 2; Anlage 1 Gestaltungshinweis 2:
 *  name, address, telephone number and email): formLine plus the phone while SELLER.phone is set. The owner decided to
 *  show no phone (PHONE_OMITTED_BY_OWNER in src/landing/config.ts), so today it equals formLine. */
export const contactLine = (lang: Lang) => {
  const phone = SELLER.phone ? (lang === 'de' ? `, Telefon: ${SELLER.phone}` : `, phone: ${SELLER.phone}`) : '';
  return `${formLine(lang)}${phone}`;
};

// the terms print the default market's euro prices (src/landing/config.ts PRICE_CENTS, read from api/_lib/markets.py)
export const eur = (cents: number, lang: Lang) => money(cents, 'eur', lang);

export { CONTACT_EMAIL, DELIVERY_MAX_HOURS, MAX_EYES, PHONE_OMITTED_BY_OWNER, PRICE_CENTS, SELLER };
