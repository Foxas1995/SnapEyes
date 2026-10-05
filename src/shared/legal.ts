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

import { adoptMarket, currentMarket, linkMarket, withMarket, type Market } from './markets';
import type { Lang } from './lang';

/** The languages the legal texts, the checkout wording and the emails exist in (src/shared/lang.ts): English, German,
 *  Lithuanian and Hungarian. Which of them an edition has is EDITION_LANGS. */
export type LegalLang = Lang;

/** The date every legal page prints as "Last updated" (terms, privacy, withdrawal, imprint), and the pack /legal/order-mail.json that the confirmation
 *  e-mail quotes carries it. ONE date versions every legal page: change it whenever ANY legal text changes (2026-10-05, work package WP12: the price rows of
 *  the terms name price classes and print no number of eyes, "and the same arrangement", the delivery time, the privacy policy's lists). It is not the
 *  consent version (WITHDRAWAL_CONSENT_VERSION), which moves only when the withdrawal-waiver wording does. A change of the set of live styles needs no new
 *  date: no legal text prints a list of styles or a number of eyes (scripts/check_styles.mjs item 7 holds it). The AI-made material sentence
 *  (src/shared/aiMaterial.ts) enters the terms in the cutover deploy, which moves this date again. */
export const LEGAL_UPDATED = '2026-10-05';

/** Which edition of the legal texts a market's customers read. "au" (the Australian market, api/_lib/markets.py): the
 *  terms with the Australian Consumer Law ("Your rights in Australia"), prices in A$ without GST, the withdrawal right
 *  framed as EU law, its own checkout consent, and an Australian part in the privacy policy. "hu" (the Hungarian
 *  market): the EU texts with the forint prices in the terms (the EU terms print euros, and an order in forints must
 *  be under a contract that prints forints). Every other market (eu, lt) reads the EU edition, unchanged.
 *  api/_lib/pay.py EDITION_MARKETS is the same list (and ACL_MARKETS the Australian part of it): keep them in step;
 *  the build checks it (scripts/check_prices.mjs). The build's legal pack carries the other editions apart
 *  (src/legal/plain.ts), with links that carry m=au / m=hu. */
export type LegalEdition = 'eu' | 'au' | 'hu';
export const EDITION_MARKETS: Readonly<Record<Exclude<LegalEdition, 'eu'>, Market>> = { au: 'au', hu: 'hu' };
export function legalEdition(m: Market = currentMarket()): LegalEdition {
  return m === EDITION_MARKETS.au ? 'au' : m === EDITION_MARKETS.hu ? 'hu' : 'eu';
}

/** The languages each edition has texts in. The Australian edition is English and German only (its Australian
 *  Consumer Law text is not translated into Lithuanian or Hungarian), so a page of the Australian market never shows
 *  those two languages (src/shared/lang.ts langFor). api/_lib/pay.py EDITION_LANGS is the same table. */
export const EDITION_LANGS: Readonly<Record<LegalEdition, readonly LegalLang[]>> = {
  eu: ['en', 'de', 'lt', 'hu'],
  au: ['en', 'de'],
  hu: ['en', 'de', 'lt', 'hu'],
};

/** The language an edition's texts are read in: the asked one, or English where the edition has none in it. */
export function editionLang(lang: LegalLang, m: Market = currentMarket()): LegalLang {
  return EDITION_LANGS[legalEdition(m)].includes(lang) ? lang : 'en';
}

/** A link with a market in it: a market with its own edition always carries it (m=au), also while the owner has
 *  paused that market ("selectable": 0), so that the links in an order's emails and pages keep opening the texts the
 *  order was made under; any other market as src/shared/markets.ts withMarket does (m= only for a selectable market
 *  other than the default one). */
function editionHref(href: string, m: Market): string {
  if (legalEdition(m) === 'eu') return withMarket(href, m);
  const hash = href.indexOf('#');
  const path = hash < 0 ? href : href.slice(0, hash);
  return `${path}${path.includes('?') ? '&' : '?'}m=${m}${hash < 0 ? '' : href.slice(hash)}`;
}

/** The legal pages and the order page: a link that names a market with its own edition (?m=au) shows that edition and
 *  keeps it in every link, even while the market is paused (then src/shared/markets.ts detectMarket ignores it for
 *  prices and checkout). Call once, before the page renders. */
export function adoptLinkedEdition(): void {
  const m = linkMarket();
  if (m !== null && legalEdition(m) !== 'eu') adoptMarket(m);
}

/** A legal date as the language writes it: German "30.09.2026", Hungarian "2026. 09. 30.", English and Lithuanian keep
 *  the ISO order ("2026-09-30": Lithuanian writes dates that way, LST ISO 8601). */
export function formatLegalDate(iso: string, lang: LegalLang): string {
  const [y, m, d] = iso.split('-');
  return lang === 'de' ? `${d}.${m}.${y}` : lang === 'hu' ? `${y}. ${m}. ${d}.` : iso;
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
 *  market (editionHref: m=, never for the default market; always for a market with its own edition); the build's legal
 *  pack, made without a browser, gets the plain link, or the link of the market it names (its au edition: m=au). */
export function legalHref(doc: LegalDocId, lang: LegalLang = 'en', section = '', market?: Market): string {
  return `${editionHref(`${LEGAL_PATH[doc]}?lang=${lang}`, market ?? currentMarket())}${section ? `#${section}` : ''}`;
}

export const LEGAL_LABELS: Record<LegalLang, Record<LegalDocId, string> & { nav: string }> = {
  en: { privacy: 'Privacy policy', terms: 'Terms of sale', withdrawal: 'Right of withdrawal', imprint: 'Legal notice', nav: 'Legal' },
  de: { privacy: 'Datenschutzerklärung', terms: 'AGB', withdrawal: 'Widerrufsbelehrung', imprint: 'Impressum', nav: 'Rechtliches' },
  // Terms of sale = "Pardavimo sąlygos", the legal notice = "Rekvizitai" (the Lithuanian name of a company-details page)
  lt: { privacy: 'Privatumo politika', terms: 'Pardavimo sąlygos', withdrawal: 'Teisė atsisakyti sutarties', imprint: 'Rekvizitai', nav: 'Teisinė informacija' },
  hu: { privacy: 'Adatkezelési tájékoztató', terms: 'ÁSZF', withdrawal: 'Elállási tájékoztató', imprint: 'Impresszum', nav: 'Jogi információk' },
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
  // the statutory labels, word for word (a label starts with a capital, as a button does; the statute prints it in lower
  // case inside a sentence): Lithuania, Civilinis kodeksas 6.228(10) str. 11 and 13 d. ("atsisakyti sutarties čia",
  // "patvirtinti sutarties atsisakymą"); Hungary, 45/2014. (II. 26.) Korm. rendelet 22. § (1b) ("elállás a szerződéstől",
  // "elállás megerősítése")
  lt: { button: 'Atsisakyti sutarties čia', confirm: 'Patvirtinti sutarties atsisakymą' },
  hu: { button: 'Elállás a szerződéstől', confirm: 'Elállás megerősítése' },
};

/** Where the function is: the order page in its withdrawal mode (src/order/withdraw.ts withdrawHref), which never
 *  starts making anything. Without an order link the customer types the order number there. The landing footer and
 *  the legal pages link here with the label WITHDRAWAL_ONLINE[lang].button; the withdrawal page describes it. */
export function withdrawFunctionHref(lang: LegalLang = 'en'): string {
  return editionHref(withdrawFunctionPath(lang), currentMarket());
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

/** Text, or a link to one of the legal pages (and one of its sections), for sentences that mix both. */
export interface LegalPart { text: string; doc?: LegalDocId; section?: string }

// The withdrawal waiver exactly as the server records it: api/_lib/pay.py CONSENT_TEXT (and CONSENT_TEXT_AU for the
// Australian market, CHECKOUT_LEGAL_AU below), version CONSENT_VERSION (GET /api/checkout also returns them).
// /api/checkout refuses an order without it and stores its version, time and a fingerprint of the text; the delivery
// email confirms it (the durable-medium confirmation of Art. 16(m)(iii) Directive 2011/83/EU and § 356 Abs. 5 Nr. 3
// BGB). Change both files together and bump the version (2026-09-30.1: the Australian text added, the EU text as it
// was; 2026-09-30.2: the Lithuanian and the Hungarian texts added, the English, German and Australian texts as they
// were). The build refuses a consent text that changed under the same version, and a version without its fingerprint
// (scripts/check_texts.mjs CONSENT_FINGERPRINTS: the check prints the new one).
export const WITHDRAWAL_CONSENT_VERSION = '2026-09-30.2';

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
  // Lithuanian: the two things Civilinis kodeksas 6.228(10) str. 2 d. 13 p. (a) and (b) ask for, in the customer's own
  // voice. Our button only opens Stripe's page and places no order; the binding order is Stripe's own pay button (CK
  // 6.228(8) str. 3 d.: "užsakymas su prievole sumokėti" or an equally unambiguous wording; Stripe's Lithuanian
  // Checkout labels it "Mokėti"). Identical to api/_lib/pay.py CONSENT_TEXT["lt"].
  lt: {
    withdrawalConsent:
      'Aiškiai sutinku, kad SnapEyes pradėtų kurti mano skaitmeninį kūrinį iš karto, dar nepasibaigus sutarties atsisakymo terminui. Pripažįstu, kad pradėjus kurti kūrinį neteksiu teisės atsisakyti sutarties.',
    withdrawalConsentMissing: 'Pažymėkite langelį aukščiau: Jūsų kūrinį pradėti kurti galime tik gavę Jūsų sutikimą.',
    acceptance: [
      { text: 'Užsakydami sutinkate su mūsų ' },
      { text: 'pardavimo sąlygomis', doc: 'terms' },
      { text: '. Taip pat perskaitykite mūsų ' },
      { text: 'privatumo politiką', doc: 'privacy' },
      { text: ' ir ' },
      { text: 'informaciją apie teisę atsisakyti sutarties', doc: 'withdrawal' },
      { text: '.' },
    ],
    continueButton: 'Pereiti prie apmokėjimo',
    photoNotice: [
      { text: 'Fotografuokite tik savo akį arba kito žmogaus akį, jei jis su tuo sutiko (vaiko atveju sutikti turi vienas iš tėvų, globėjas ar rūpintojas). Jūsų nuotrauka naudojama tik Jūsų kūriniui sukurti. ' },
      { text: 'Privatumo politika', doc: 'privacy' },
    ],
  },
  // Hungarian: 45/2014. (II. 26.) Korm. rendelet 29. § (1) m): both elements, the express prior consent to start AND the
  // acknowledgement that the right of withdrawal is lost once performance has started. The buy button carries the
  // label of the owner's Hungarian launch plan "Megrendelés fizetési kötelezettséggel" (an equivalent, unambiguous wording under 15. § (2);
  // the decree's own words "fizetési kötelezettséggel járó megrendelés" stand above Stripe's pay button, the click that
  // binds: api/_lib/pay_hu.py SUBMIT_NOTE_HU). The legal reviewer may prefer "Fizetési kötelezettséggel járó
  // megrendelés" or "Tovább a fizetéshez": this one line, every other place reads it from here. Identical to
  // api/_lib/pay.py CONSENT_TEXT["hu"].
  hu: {
    withdrawalConsent:
      'Kifejezetten hozzájárulok ahhoz, hogy a SnapEyes még az elállási határidő lejárta előtt azonnal megkezdje a digitális alkotásom elkészítését. Tudomásul veszem, hogy a teljesítés megkezdését követően elveszítem az elállási jogomat.',
    withdrawalConsentMissing: 'Kérjük, jelöld be a fenti négyzetet: az alkotásod elkészítését csak a hozzájárulásoddal kezdhetjük meg.',
    acceptance: [
      { text: 'A megrendeléssel elfogadod az ' },
      { text: 'ÁSZF-et', doc: 'terms' },
      { text: '. Kérjük, olvasd el az ' },
      { text: 'adatkezelési tájékoztatót', doc: 'privacy' },
      { text: ' és az ' },
      { text: 'elállási tájékoztatót', doc: 'withdrawal' },
      { text: ' is.' },
    ],
    continueButton: 'Megrendelés fizetési kötelezettséggel',
    photoNotice: [
      { text: 'Csak a saját szemedet fotózd le, vagy olyan személy szemét, aki ehhez hozzájárult (gyermek esetén a szülő vagy a gondviselő). A fotódat kizárólag az alkotásod elkészítéséhez használjuk. ' },
      { text: 'Adatkezelési tájékoztató', doc: 'privacy' },
    ],
  },
};

/** The checkout of the Australian market (legalEdition "au"): the same checkbox, with a text that keeps both EU
 *  elements (the express consent to start before the withdrawal period ends and the acknowledgement of losing the
 *  right of withdrawal: an EU consumer may buy in A$ too) and adds what an Australian reads in it: no cancelling for a
 *  change of mind once making has started, and that the Australian Consumer Law is not affected (its guarantees cannot
 *  be excluded, so nothing here may read as "no refunds"). Identical to api/_lib/pay.py CONSENT_TEXT_AU. The line
 *  under it names the terms' "Your rights in Australia" section. */
export const CHECKOUT_LEGAL_AU: Record<'en' | 'de', Pick<CheckoutLegal, 'withdrawalConsent' | 'acceptance'>> = {
  en: {
    withdrawalConsent:
      "I expressly agree that SnapEyes starts making my personalised digital artwork right away, before the withdrawal period ends. I know that once this has started, I lose my right of withdrawal and can't cancel for a change of mind. This doesn't affect my rights under the Australian Consumer Law.",
    acceptance: [
      { text: 'By ordering you accept our ' },
      { text: 'Terms of sale', doc: 'terms' },
      { text: ', including ' },
      { text: 'your rights in Australia', doc: 'terms', section: 'australia' },
      { text: '. Please also read our ' },
      { text: 'Privacy policy', doc: 'privacy' },
      { text: ' and the ' },
      { text: 'information on the right of withdrawal', doc: 'withdrawal' },
      { text: '.' },
    ],
  },
  de: {
    withdrawalConsent:
      'Ich stimme ausdrücklich zu, dass SnapEyes sofort, vor Ablauf der Widerrufsfrist, mit der Erstellung meines personalisierten digitalen Kunstwerks beginnt. Mir ist bekannt, dass ich dadurch mein Widerrufsrecht verliere, sobald damit begonnen wurde, und den Vertrag dann nicht mehr ohne Angabe von Gründen widerrufen kann. Meine Rechte nach dem australischen Verbraucherrecht (Australian Consumer Law) bleiben davon unberührt.',
    acceptance: [
      { text: 'Mit Ihrer Bestellung akzeptieren Sie unsere ' },
      { text: 'AGB', doc: 'terms' },
      { text: ', einschließlich ' },
      { text: 'Ihrer Rechte in Australien', doc: 'terms', section: 'australia' },
      { text: '. Bitte beachten Sie auch unsere ' },
      { text: 'Datenschutzerklärung', doc: 'privacy' },
      { text: ' und die ' },
      { text: 'Widerrufsbelehrung', doc: 'withdrawal' },
      { text: '.' },
    ],
  },
};

/** The checkout wording for a market: the EU wording (also for the hu edition: the same checkbox, the prices differ
 *  only in the terms), with the Australian checkbox and line for the au edition. A language the edition has no texts
 *  in (editionLang) reads the edition's English. */
export function checkoutLegal(lang: LegalLang, market: Market = currentMarket()): CheckoutLegal {
  const l = editionLang(lang, market);
  return legalEdition(market) === 'au' ? { ...CHECKOUT_LEGAL[l], ...CHECKOUT_LEGAL_AU[l === 'de' ? 'de' : 'en'] } : CHECKOUT_LEGAL[l];
}
