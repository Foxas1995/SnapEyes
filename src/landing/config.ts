// Facts the landing page prints. Keep every value here true; the copy dictionary only words them.
import { MARKETS, DEFAULT_MARKET, MAX_EYES, withMarket } from '../shared/markets';
import type { Lang } from '../shared/lang';

// Every email address on the page and the curator's "send me your photos" offer come from this one constant
// and stay hidden while it is empty. Owner decision 2026-09-23: info@snapeyes.com at Hostinger; the owner confirmed
// on 2026-09-29 that the mailbox exists. The legal pages (src/legal) name it as the contact for every request.
export const CONTACT_EMAIL = 'info@snapeyes.com';

// Every primary call to action goes straight to the capture tool: people should see their own result.
export const TRY_URL = '/try';
// ...in the page's language: /try reads ?lang= first (src/try/lang.ts, the same rule as ./lang.tsx), so a visitor
// who reads this page in German through /?lang=de, without ever touching the switch, still gets /try in German.
// And in the page's market (m=, src/shared/markets.ts withMarket), so /try shows the same currency.
export const tryUrl = (lang: Lang) => withMarket(`${TRY_URL}?lang=${lang}`);

// Seller shown in the footer and on the legal pages (owner decision 2026-09-23). MB is not VAT-registered: no VAT
// number, no "incl. VAT". Every page prints the "Represented by" and "Phone" lines only when the value is set.
// PHONE: owner decision (2026-09-29): NO telephone number is shown anywhere, so phone stays '' and
// PHONE_OMITTED_BY_OWNER is true. The law asks for one: Art. 6(1)(c) Directive 2011/83/EU as amended by Directive (EU)
// 2019/2161 (pre-contract information; in Germany Art. 246a § 1 Abs. 1 Nr. 2 EGBGB), Annex I(A) note 2 and Anlage 1
// EGBGB Gestaltungshinweis 2 (the model withdrawal information: name, address, telephone number and email). The model
// withdrawal FORM needs none (Annex I(B), Anlage 2 EGBGB: name, address, email). Leaving it out is therefore a known
// risk the owner accepts (explained to him in Lithuanian on 2026-09-29: the rules, the risk, a cheap separate number).
// The pages stay correct without it: they name the postal address, the email address and the online withdrawal
// function, and never claim a phone line.
// The build's /legal/order-mail.json (src/legal/plain.ts) lists the phone under "waived" (owner decision), not under
// "missing", so a live-sales gate in api/_lib/pay.py that refuses on "missing" does not block on it.
// To show a number after all: write it into phone in international form (with the country code) and set
// PHONE_OMITTED_BY_OWNER to false; every page, the model information and the order email pick it up.
export const PHONE_OMITTED_BY_OWNER = true;
export interface Seller {
  name: string;           // the MB's name, printed as MB "<name>"
  code: string;           // company code (juridinio asmens kodas) in the Register of Legal Entities
  street: string;
  postcode: string;
  city: string;
  representative: string; // the authorised representative (vadovas); '' = not known yet, line hidden
  phone: string;          // '' = no phone line anywhere (owner decision, see PHONE_OMITTED_BY_OWNER above)
}
export const SELLER: Readonly<Seller> = {
  name: 'Portretizuokis',
  code: '305605052',
  street: 'Gedimino g. 22A-14',
  postcode: 'LT-44319',
  city: 'Kaunas',
  representative: 'Mantas Bakšys',
  phone: '',
};

// The DEFAULT market's prices in euro cents, in the names the landing page and the terms of sale use. They are not a
// copy: every price lives in api/_lib/markets.py (the server charges from it, src/shared/markets.ts reads it at build
// time), and a price change there changes the pages, the terms and what Stripe charges together. The landing page
// shows its visitor's own market (src/shared/markets.ts priceList); the terms print these. No purchase buttons here: an
// order starts from the customer's own preview on /try, and the page says "ordering opens soon" until the deployment
// takes orders (src/landing/ordering.ts).
const DEFAULT_PRICES = MARKETS[DEFAULT_MARKET].prices;
export const PRICE_CENTS = {
  studioBlack: DEFAULT_PRICES.one_eye_studio_black,   // 1 eye, Studio Black
  artBackground: DEFAULT_PRICES.one_eye_art,          // 1 eye, any of the five art backgrounds
  coupleDuo: DEFAULT_PRICES.two_eyes,                 // 2 eyes
  extraEye: DEFAULT_PRICES.each_further_eye,          // each eye after the second
} as const;
export { MAX_EYES };

// The latest delivery the terms of sale promise (Art. 6(1)(g) Directive 2011/83/EU, Art. 246a § 1 Abs. 1 Nr. 7
// EGBGB). Normally the file is ready on the order page within minutes of payment (the page makes it as soon as the
// order confirmation email has gone out). This bound covers the slow cases: an order held for the owner's own check
// (review.json, released with scripts/order_admin.py release --mail) or held because its confirmation email could not
// go out. Owner decision: a time that can always be kept, weekends included. src/legal/docs/terms.ts prints it.
export const DELIVERY_MAX_HOURS = 48;
