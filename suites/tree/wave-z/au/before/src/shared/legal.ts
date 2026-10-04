// Legal links and the legal wording of the checkout, shared by the landing page, the legal pages (src/legal), /try
// and the payments UI. Plain data only, no React and no landing copy, so any page can import it cheaply.
//
// Not reviewed by a lawyer. Every sentence here must stay true: if the checkout changes (for example it no longer
// starts the file right after payment), change the wording here and on the withdrawal page together.
// The right of withdrawal ends when MAKING the file begins (making.json, api/_lib/withdraw.py _began), which is what
// the checkbox below says; the withdrawal page, the terms and the landing FAQ say the same ("once we have started
// making your file", "sobald wir mit der Erstellung Ihrer Datei begonnen haben"), and that making starts only after
// the order confirmation email, on the order page (never through the withdrawal link, withdrawFunctionHref or the
// email's own withdrawal link). When nothing was made, it ends with the 14-day period (withdraw.py period_end: the day
// of payment is not counted). If the server ever moves either moment (for example to the first download), change all
// of them together: src/legal/docs/withdrawal.ts has the full list of the server's rules in its header.

import { withMarket } from './markets';

export type LegalLang = 'en' | 'de';

/** The date every legal page prints as "Last updated". Change it whenever a legal text changes. */
export const LEGAL_UPDATED = '2026-09-30';

export function formatLegalDate(iso: string, lang: LegalLang): string {
  const [y, m, d] = iso.split('-');
  return lang === 'de' ? `${d}.${m}.${y}` : iso;
}

export type LegalDocId = 'privacy' | 'terms' | 'withdrawal' | 'imprint';
export const LEGAL_DOCS: readonly LegalDocId[] = ['privacy', 'terms', 'withdrawal', 'imprint'];

// One page per document (privacy.html, terms.html, withdrawal.html, imprint.html; vercel.json cleanUrls serves
// them without the .html). The language travels as ?lang=, like on the landing page.
export const LEGAL_PATH: Record<LegalDocId, string> = {
  privacy: '/privacy',
  terms: '/terms',
  withdrawal: '/withdrawal',
  imprint: '/imprint',
};

/** The link to a legal page in a language, optionally to one of its sections (#id). In a browser it carries the page's
 *  market (src/shared/markets.ts withMarket: m=, never for the default market); the build's legal pack, made without a
 *  browser, gets the plain link. */
export function legalHref(doc: LegalDocId, lang: LegalLang = 'en', section = ''): string {
  return `${withMarket(`${LEGAL_PATH[doc]}?lang=${lang}`)}${section ? `#${section}` : ''}`;
}

export const LEGAL_LABELS: Record<LegalLang, Record<LegalDocId, string> & { nav: string }> = {
  en: { privacy: 'Privacy policy', terms: 'Terms of sale', withdrawal: 'Right of withdrawal', imprint: 'Legal notice', nav: 'Legal' },
  de: { privacy: 'Datenschutzerklärung', terms: 'AGB', withdrawal: 'Widerrufsbelehrung', imprint: 'Impressum', nav: 'Rechtliches' },
};

// The service that sends the order emails (the order page link and the confirmation): api/_lib/pay.py send_mail,
// through Resend. The privacy policy names it next to Hostinger (the mailbox info@snapeyes.com). If the sender
// changes, change this line and the policy follows.
export const ORDER_EMAIL_SENDER: string = 'Resend';

/** The online withdrawal function (Art. 11a Directive 2011/83/EU, added by Directive (EU) 2023/2673 and applied since
 *  19 June 2026; § 356a BGB): a clearly labelled function to withdraw, a confirming step, and an acknowledgement on a
 *  durable medium. The withdrawal page, the terms and the privacy policy quote these labels, so the order page's
 *  button and its confirming button must carry exactly these words (import them from here). */
export interface WithdrawalOnline {
  /** The function's label: "withdraw from contract here" or an equally unambiguous wording (Art. 11a(1)). */
  button: string;
  /** The label of the step that sends the statement: "confirm withdrawal" or equivalent (Art. 11a(3)). */
  confirm: string;
}

export const WITHDRAWAL_ONLINE: Record<LegalLang, WithdrawalOnline> = {
  en: { button: 'Withdraw from contract here', confirm: 'Confirm withdrawal' },
  de: { button: 'Vertrag hier widerrufen', confirm: 'Widerruf bestätigen' },
};

/** Where the function is: the order page in its withdrawal mode (src/order/withdraw.ts withdrawHref), which never
 *  starts making anything. Without an order link the customer types the order number there. The landing footer and
 *  the legal pages link here with the label WITHDRAWAL_ONLINE[lang].button; the withdrawal page describes it. */
export function withdrawFunctionHref(lang: LegalLang = 'en'): string {
  return withMarket(withdrawFunctionPath(lang));
}

/** The same link without the market: the address the legal texts print (withdrawFunctionAddress). */
function withdrawFunctionPath(lang: LegalLang): string {
  return `/order?withdraw=1&lang=${lang}`;
}

/** The same address as people read and type it ("snapeyes.com/order?withdraw=1&lang=de"): the internet address the
 *  statutory withdrawal information names for the function (Anlage 1 EGBGB, Gestaltungshinweis 3, since 19.06.2026;
 *  Annex I(A) Directive 2011/83/EU, note 3 as amended by Directive (EU) 2023/2673). */
export const SITE_HOST = 'snapeyes.com';
export function withdrawFunctionAddress(lang: LegalLang = 'en'): string {
  return `${SITE_HOST}${withdrawFunctionPath(lang)}`;
}

/** Text, or a link to one of the legal pages, for sentences that mix both. */
export interface LegalPart { text: string; doc?: LegalDocId }

// The withdrawal waiver exactly as the server records it: api/_lib/pay.py CONSENT_TEXT, version CONSENT_VERSION
// (GET /api/checkout also returns it). /api/checkout refuses an order without it and stores its version, time and
// a fingerprint of the text; the delivery email confirms it (the durable-medium confirmation of Art. 16(m)(iii)
// Directive 2011/83/EU and § 356 Abs. 5 Nr. 3 BGB). Change both files together and bump the version.
export const WITHDRAWAL_CONSENT_VERSION = '2026-09-29.1';

export interface CheckoutLegal {
  /** The withdrawal checkbox: unticked by default and required before the payment page opens. Art. 16(m)
   *  Directive 2011/83/EU, § 356 Abs. 5 BGB: the right of withdrawal for digital content ends early only with this
   *  prior express consent AND this acknowledgement. Identical to api/_lib/pay.py CONSENT_TEXT. */
  withdrawalConsent: string;
  /** Shown next to the checkbox when someone tries to continue without ticking it. */
  withdrawalConsentMissing: string;
  /** The line under the checkbox, as text and links (render each part with a doc as a link to legalHref). */
  acceptance: LegalPart[];
  /** Our button that opens Stripe's payment page. It is not the binding order button: the order becomes binding
   *  on Stripe's own pay button, which already says that it costs money (§ 312j Abs. 3 BGB). */
  continueButton: string;
  /** Short notice for the photo step: whose eye may be photographed. */
  photoNotice: LegalPart[];
}

export const CHECKOUT_LEGAL: Record<LegalLang, CheckoutLegal> = {
  en: {
    withdrawalConsent:
      'I expressly agree that SnapEyes starts making my digital artwork right away, before the withdrawal period ends. I know that I lose my right of withdrawal once this has started.',
    withdrawalConsentMissing: 'Please tick the box above: we can only start on your artwork once you agree.',
    acceptance: [
      { text: 'By ordering you accept our ' },
      { text: 'Terms of sale', doc: 'terms' },
      { text: '. Please also read our ' },
      { text: 'Privacy policy', doc: 'privacy' },
      { text: ' and the ' },
      { text: 'information on the right of withdrawal', doc: 'withdrawal' },
      { text: '.' },
    ],
    continueButton: 'Continue to payment',
    photoNotice: [
      { text: 'Only photograph your own eye, or the eye of someone who has agreed to it (for a child: a parent or guardian). Your photo is used only to make your artwork. ' },
      { text: 'Privacy policy', doc: 'privacy' },
    ],
  },
  de: {
    withdrawalConsent:
      'Ich stimme ausdrücklich zu, dass SnapEyes sofort, vor Ablauf der Widerrufsfrist, mit der Erstellung meines digitalen Kunstwerks beginnt. Mir ist bekannt, dass ich dadurch mein Widerrufsrecht verliere, sobald damit begonnen wurde.',
    withdrawalConsentMissing: 'Bitte setzen Sie oben das Häkchen: Wir können mit Ihrem Kunstwerk erst beginnen, wenn Sie zustimmen.',
    acceptance: [
      { text: 'Mit Ihrer Bestellung akzeptieren Sie unsere ' },
      { text: 'AGB', doc: 'terms' },
      { text: '. Bitte beachten Sie auch unsere ' },
      { text: 'Datenschutzerklärung', doc: 'privacy' },
      { text: ' und die ' },
      { text: 'Widerrufsbelehrung', doc: 'withdrawal' },
      { text: '.' },
    ],
    continueButton: 'Weiter zur Zahlung',
    photoNotice: [
      { text: 'Fotografieren Sie nur Ihr eigenes Auge oder das Auge einer Person, die damit einverstanden ist (bei einem Kind: ein Elternteil oder eine sorgeberechtigte Person). Ihr Foto dient nur dazu, Ihr Kunstwerk zu erstellen. ' },
      { text: 'Datenschutzerklärung', doc: 'privacy' },
    ],
  },
};
