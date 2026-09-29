// Facts the landing page prints. Keep every value here true; the copy dictionary only words them.

// Every email address on the page and the curator's "send me your photos" offer come from this one constant
// and stay hidden while it is empty. Owner decision 2026-09-23: info@snapeyes.com at Hostinger; the owner confirmed
// on 2026-09-29 that the mailbox exists. The legal pages (src/legal) name it as the contact for every request.
export const CONTACT_EMAIL = 'info@snapeyes.com';

// Every primary call to action goes straight to the capture tool: people should see their own result.
export const TRY_URL = '/try';
// ...in the page's language: /try reads ?lang= first (src/try/lang.ts, the same rule as ./lang.tsx), so a visitor
// who reads this page in German through /?lang=de, without ever touching the switch, still gets /try in German.
export const tryUrl = (lang: 'en' | 'de') => `${TRY_URL}?lang=${lang}`;

// Seller shown in the footer and on the legal pages (owner decision 2026-09-23). MB is not VAT-registered: no VAT
// number, no "incl. VAT". representative and phone stay empty until the owner gives them: every page prints the
// "Represented by" and "Phone" lines only when the value is set.
// The PHONE IS REQUIRED BEFORE THE FIRST LIVE SALE: the law wants the trader's telephone number in the pre-contract
// information and in the withdrawal information (Art. 6(1)(c) Directive 2011/83/EU; Anlage 1 EGBGB Gestaltungshinweis
// 2). While it is '', the build's /legal/order-mail.json lists "seller.phone" under "missing" (src/legal/plain.ts), for
// api/_lib/pay.py to keep live ordering closed. Write it in international form, with the country code.
export interface Seller {
  name: string;           // the MB's name, printed as MB "<name>"
  code: string;           // company code (juridinio asmens kodas) in the Register of Legal Entities
  street: string;
  postcode: string;
  city: string;
  representative: string; // the authorised representative (vadovas); '' = not known yet, line hidden
  phone: string;          // '' = no phone line anywhere
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

// Prices in euro cents (owner decision 2026-09-23). The landing page shows them with no purchase buttons (an order
// starts from the customer's own preview on /try) and says "ordering opens soon" until the deployment takes orders
// (src/landing/ordering.ts). The terms of sale (src/legal/docs/terms.ts) print these same constants, so a price
// change here changes them too; api/_lib/pay.py charges its own copy of them, so change both together.
export const PRICE_CENTS = {
  studioBlack: 1997,   // 1 eye, Studio Black
  artBackground: 2497, // 1 eye, any of the five art backgrounds
  coupleDuo: 3997,     // 2 eyes
  extraEye: 1500,      // each eye after the second
} as const;
export const MAX_EYES = 8;

// The latest delivery the terms of sale promise (Art. 6(1)(g) Directive 2011/83/EU, Art. 246a § 1 Abs. 1 Nr. 7
// EGBGB). Normally the file is ready on the order page within minutes of payment (the page makes it as soon as the
// order confirmation email has gone out). This bound covers the slow cases: an order held for the owner's own check
// (review.json, released with scripts/order_admin.py release --mail) or held because its confirmation email could not
// go out. Owner decision: a time that can always be kept, weekends included. src/legal/docs/terms.ts prints it.
export const DELIVERY_MAX_HOURS = 48;

export function centsForEyes(eyes: number): number {
  if (eyes <= 1) return PRICE_CENTS.studioBlack;
  return PRICE_CENTS.coupleDuo + (eyes - 2) * PRICE_CENTS.extraEye;
}

// The six styles of the capture tool, in the order the page shows them. Every image under
// /assets/atelier/ is the founder's own eye rendered by the engine (api/_lib/iris.py compose), not a mockup.
export const STYLES = [
  { id: 'studio_black', name: 'Studio Black', slug: 'studio-black' },
  { id: 'celestial_gold', name: 'Celestial Gold', slug: 'celestial-gold' },
  { id: 'deep_nebula', name: 'Deep Nebula', slug: 'deep-nebula' },
  { id: 'emerald_aurora', name: 'Emerald Aurora', slug: 'emerald-aurora' },
  { id: 'obsidian_smoke', name: 'Obsidian Smoke', slug: 'obsidian-smoke' },
  { id: 'supernova', name: 'Supernova', slug: 'supernova' },
] as const;
export type StyleId = (typeof STYLES)[number]['id'];

export const styleSrc = (slug: string, width: 480 | 800) => `/assets/atelier/style-${slug}-${width}.webp`;
export const styleSrcSet = (slug: string) => `${styleSrc(slug, 480)} 480w, ${styleSrc(slug, 800)} 800w`;

// The founder's phone crop at its native 315 px, not upscaled and not retouched.
export const BEFORE_SRC = '/assets/atelier/before-phone-crop-315.webp';
