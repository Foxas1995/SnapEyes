// The seller facts and prices as the legal texts print them. Every value comes from src/landing/config.ts, so the
// landing page, the checkout and the legal pages can never disagree.
import type { Lang } from '../shared/lang';
import { CONTACT_EMAIL, DELIVERY_MAX_HOURS, MAX_EYES, PHONE_OMITTED_BY_OWNER, PRICE_CENTS, SELLER } from '../landing/config';
import { money, priceList } from '../shared/markets';
import { EDITION_MARKETS } from '../shared/legal';

// The words around the seller's facts, per language. The company name is quoted the way the language quotes (the
// Lithuanian marks are the German ones, the Hungarian ones close with a raised ” ), and the Lithuanian and Hungarian
// pages name the country in their own language.
interface SellerWords {
  quotes: readonly [string, string];
  country: string;
  phone: string;            // before the number in a sentence naming the seller: ", phone +370 ..."
  phoneLine: string;        // before the number in a contact line: ", phone: +370 ..."
  represented: string;      // before the representative's name: ", represented by Mantas ..."
  email: string;            // the word before the address in the model form's "To:" line
}
const WORDS: Record<Lang, SellerWords> = {
  en: { quotes: ['"', '"'], country: 'Lithuania', phone: ', phone', phoneLine: ', phone:', represented: ', represented by', email: 'email' },
  de: { quotes: ['„', '“'], country: 'Litauen', phone: ', Telefon', phoneLine: ', Telefon:', represented: ', vertreten durch', email: 'E-Mail' },
  // "kuriai atstovauja": the active voice on purpose, so that the representative's name stays in the nominative as
  // config.ts holds it ("atstovaujama" would need the genitive, which code cannot build reliably)
  lt: { quotes: ['„', '“'], country: 'Lietuva', phone: ', telefonas', phoneLine: ', telefonas:', represented: ', kuriai atstovauja', email: 'el. paštas' },
  hu: { quotes: ['„', '”'], country: 'Litvánia', phone: ', telefon:', phoneLine: ', telefon:', represented: ', képviseli:', email: 'e-mail' },
};

export const company = (lang: Lang) => `MB ${WORDS[lang].quotes[0]}${SELLER.name}${WORDS[lang].quotes[1]}`;
export const country = (lang: Lang) => WORDS[lang].country;
export const address = (lang: Lang) => `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${country(lang)}`;

/** The contact email as a mailto link in the inline markup. */
export const MAIL = `[${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL})`;

/** ", phone +370 ..." while SELLER.phone is set, else '': for sentences that name the seller's contact details. */
export const phoneSuffix = (lang: Lang) => (SELLER.phone ? `${WORDS[lang].phone} ${SELLER.phone}` : '');

/** ", represented by ..." while SELLER.representative is set, else ''. */
export const representedSuffix = (lang: Lang) => (SELLER.representative ? `${WORDS[lang].represented} ${SELLER.representative}` : '');

/** The name, postal address and email: exactly what the model withdrawal FORM's "To:" line asks for (Annex I(B)
 *  Directive 2011/83/EU as amended by Directive (EU) 2019/2161; Anlage 2 EGBGB; Lithuania's model form, order
 *  1R-154; Hungary's 45/2014. (II. 26.) Korm. rendelet 2. melléklet), with no telephone number. */
export const formLine = (lang: Lang) => `${company(lang)}, ${address(lang)}, ${WORDS[lang].email}: ${CONTACT_EMAIL}`;

/** The contact details for the model withdrawal INFORMATION's "[2]" (Annex I(A) note 2; Anlage 1 Gestaltungshinweis 2:
 *  name, address, telephone number and email): formLine plus the phone while SELLER.phone is set. The owner decided to
 *  show no phone (PHONE_OMITTED_BY_OWNER in src/landing/config.ts), so today it equals formLine. */
export const contactLine = (lang: Lang) => `${formLine(lang)}${SELLER.phone ? `${WORDS[lang].phoneLine} ${SELLER.phone}` : ''}`;

// the terms print the default market's euro prices (src/landing/config.ts PRICE_CENTS, read from api/_lib/markets.py)
export const eur = (cents: number, lang: Lang) => money(cents, 'eur', lang);

// the Australian edition's terms print the Australian market's prices (api/_lib/markets.py, in A$: "A$39", never "$")
export const AU_PRICES = priceList(EDITION_MARKETS.au);
export const aud = (cents: number, lang: Lang) => money(cents, 'aud', lang);

// the Hungarian edition's terms print the Hungarian market's prices (in forints: "6 990 Ft", in every language)
export const HU_PRICES = priceList(EDITION_MARKETS.hu);
export const huf = (minor: number, lang: Lang) => money(minor, 'huf', lang);

export { CONTACT_EMAIL, DELIVERY_MAX_HOURS, MAX_EYES, PHONE_OMITTED_BY_OWNER, PRICE_CENTS, SELLER };
