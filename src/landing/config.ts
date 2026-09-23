// Facts the landing page prints. Keep every value here true; the copy dictionary only words them.

// Every email address on the page and the curator's "send me your photos" offer come from this one constant
// and stay hidden while it is empty. Owner decision 2026-09-23: info@snapeyes.com, created at Hostinger while
// the domain moves there. Until its MX records exist, mail to it bounces: check that it receives before ads run.
export const CONTACT_EMAIL = 'info@snapeyes.com';

// Every primary call to action goes straight to the capture tool: people should see their own result.
export const TRY_URL = '/try';

// Seller shown in the footer (owner decision 2026-09-23). MB is not VAT-registered: no VAT number, no "incl. VAT".
export const SELLER = {
  name: 'Portretizuokis',
  code: '305605052',
  street: 'Gedimino g. 22A-14',
  postcode: 'LT-44319',
  city: 'Kaunas',
} as const;

// Prices in euro cents (owner decision 2026-09-23). Ordering is not open yet: there is no checkout, so the
// page shows prices with a plain "ordering opens soon" notice and no purchase buttons.
export const PRICE_CENTS = {
  studioBlack: 1997,   // 1 eye, Studio Black
  artBackground: 2497, // 1 eye, any of the five art backgrounds
  coupleDuo: 3997,     // 2 eyes
  extraEye: 1500,      // each eye after the second
} as const;
export const MAX_EYES = 8;

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
