// The seller facts and prices as the legal texts print them. Every value comes from src/landing/config.ts, so the
// landing page, the checkout and the legal pages can never disagree.
import type { Lang } from '../landing/copy';
import { CONTACT_EMAIL, DELIVERY_MAX_HOURS, MAX_EYES, PRICE_CENTS, SELLER } from '../landing/config';

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

/** The full postal and email contact, for the withdrawal information and the model form. */
export const contactLine = (lang: Lang) => {
  const phone = SELLER.phone ? (lang === 'de' ? `, Telefon: ${SELLER.phone}` : `, phone: ${SELLER.phone}`) : '';
  return `${company(lang)}, ${address(lang)}, ${lang === 'de' ? 'E-Mail' : 'email'}: ${CONTACT_EMAIL}${phone}`;
};

export const eur = (cents: number, lang: Lang) =>
  new Intl.NumberFormat(lang === 'de' ? 'de-DE' : 'en-IE', { style: 'currency', currency: 'EUR' }).format(cents / 100);

export { CONTACT_EMAIL, DELIVERY_MAX_HOURS, MAX_EYES, PRICE_CENTS, SELLER };
