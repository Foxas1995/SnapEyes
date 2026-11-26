// Legal links and the legal wording of the checkout, shared by the landing page, the legal pages (src/legal), /try
// and the payments UI. Plain data only, no React and no landing copy, so any page can import it cheaply.
//
// Not reviewed by a lawyer. Every sentence here must stay true: if the checkout changes (for example it no longer
// starts the file right after payment), change the wording here and on the withdrawal page together.
// The right of withdrawal ends when MAKING the file begins (making.json, api/_lib/withdraw.py _began). Since the owner's decision of 2026-11-25, the second one of that day
// the checkbox below is shown only on the US market (consentBox); every other order is placed under the terms, whose section
// "withdrawal" and the withdrawal page say that by paying the customer agrees to the immediate start and that the contract can no
// longer be withdrawn from once making has started (nothing else on the site says it: no FAQ item, no note on Stripe's page, nothing
// in the confirmation email); and that making starts only after
// the order confirmation email, on the order page (never through the withdrawal link, withdrawFunctionHref or the
// email's own withdrawal link). When nothing was made, it ends with the 14-day period (withdraw.py period_end: the day
// of payment is not counted). If the server ever moves either moment (for example to the first download), change all
// of them together: src/legal/docs/withdrawal.ts has the full list of the server's rules in its header.

import { adoptMarket, currentMarket, linkMarket, withMarket, type Market } from './markets';
import type { Lang } from './lang';

/** The languages the legal texts, the checkout wording and the emails exist in (src/shared/lang.ts): English, German,
 *  Lithuanian, Hungarian and Croatian (the EU edition only, 2026-10-28). Which of them an edition has is EDITION_LANGS. */
export type LegalLang = Lang;

/** The date every legal page prints as "Last updated" (terms, privacy, withdrawal, imprint), and the pack /legal/order-mail.json that the confirmation
 *  e-mail quotes carries it. ONE date versions every legal page: change it whenever ANY legal text changes (2026-10-05, work package WP12: the price rows of
 *  the terms name price classes and print no number of eyes, "and the same arrangement", the delivery time, the privacy policy's lists). It is not the
 *  consent version (WITHDRAWAL_CONSENT_VERSION), which moves only when the withdrawal-waiver wording does. A change of the set of live styles needs no new
 *  date: no legal text prints a list of styles or a number of eyes (scripts/check_styles.mjs item 7 holds it). 2026-10-06, work package WP18 (the catalogue
 *  switch): the AI-made material sentence (src/shared/aiMaterial.ts) entered the terms of every edition and language in the cutover deploy. 2026-10-20: the privacy
 *  policy (every edition and language) says what the anonymous counter keeps (api/_lib/counter.py) and where the country hint goes; no other legal text moved.
 *  2026-10-28: the Croatian texts of the EU edition (src/legal/docs/*.hr.ts), Croatian named as a contract language in every terms text, and the
 *  legal notice's example images described as our own eye (no founder named). 2026-11-11: the privacy policy (every edition and language) says what the day's
 *  ceiling of free previews per connection keeps (api/_lib/previewcap.py: a keyed hash of the address and the day, deleted after 2 days); no other legal text moved.
 *  2026-11-13: the Finnish, Estonian and Latvian texts of the EU edition (src/legal/docs/*.fi.ts, *.et.ts, *.lv.ts) and the three named as contract languages in
 *  every terms text of that edition. 2026-11-21: a print is ordered from the order page AFTER the artwork is delivered, as a contract of its own
 *  (src/legal/docs/prints.ts: the terms' print section and product sentence, the withdrawal page's and the privacy policy's print paragraph, in the eight
 *  languages of the EU edition and in the Hungarian edition's terms and withdrawal page, which carry the same section); the print box's words and the consent
 *  version are as they were. 2026-11-24: the list of prints and prices in the terms' print section, which is made from api/_lib/print_offer.py (the acrylic
 *  block 20 x 20 cm joins it, the canvas has a new price), in the eight languages of the EU edition and in the Hungarian edition's terms. The same day, the
 *  final list (eleven prints; the canvas without an outer frame) and its shipping table, and ONE passage of the terms' delivery paragraph for prints: the
 *  times, which are merchOne's published ones from api/_lib/print_times.py (2 business days of production for a canvas or a poster, 3 for every other print;
 *  then 4 to 6 working days to Lithuania, Latvia and Estonia, 5 to 8 to Finland, 3 to 6 to Germany, about a week elsewhere) where the text said "about 3
 *  business days" and "2 to 9 business days" with four examples. No other sentence of a legal text changed, and the consent version is as it was.
 *  2026-11-25 (the owner's decision): the privacy policy says that the site uses the Meta pixel and reports payments to Meta from the server (a section
 *  "meta", and the sentences that said there were no cookies and no tools of other companies: website, orders, services, retention, storage, and the US
 *  edition's own section), in every language of every edition. The terms, the withdrawal page, the legal notice and the consent version are as they were. */
export const LEGAL_UPDATED = '2026-11-26';

/** Which edition of the legal texts a market's customers read. "au" (the Australian market, api/_lib/markets.py): the
 *  terms with the Australian Consumer Law ("Your rights in Australia"), prices in A$ without GST, the withdrawal right
 *  framed as EU law, its own checkout consent, and an Australian part in the privacy policy. "hu" (the Hungarian
 *  market): the EU texts with the forint prices in the terms (the EU terms print euros, and an order in forints must
 *  be under a contract that prints forints). "us" (the US market): the terms with prices in US$ without sales tax and
 *  "Your rights in the United States", the withdrawal right framed as EU law, its own checkout consent (with the
 *  consent to the use of the eye photos), and a US part in the privacy policy. Every other market (eu, lt, hr; uk,
 *  which is not sold in) reads the EU edition, unchanged.
 *  api/_lib/pay.py EDITION_MARKETS is the same list (and ACL_MARKETS the Australian part of it, US_MARKETS the US
 *  part): keep them in step; the build checks it (scripts/check_prices.mjs). The build's legal pack carries the other
 *  editions apart (src/legal/plain.ts), with links that carry m=au / m=hu / m=us. */
export type LegalEdition = 'eu' | 'au' | 'hu' | 'us';
export const EDITION_MARKETS: Readonly<Record<Exclude<LegalEdition, 'eu'>, Market>> = { au: 'au', hu: 'hu', us: 'us' };
/** Does the checkout of this market show the consent box (and the server ask for its tick)? Only the US market since 2026-11-25 (the
 *  owner's decisions of that day: "varnelę išimti visai"; its box also holds the consent to the use of the eye photos). Every other order is
 *  placed under the terms, which say that by paying the customer agrees to the immediate start (api/_lib/pay.py consent_box). */
export function consentBox(m: Market = currentMarket()): boolean {
  return legalEdition(m) === 'us';
}

export function legalEdition(m: Market = currentMarket()): LegalEdition {
  return m === EDITION_MARKETS.au ? 'au' : m === EDITION_MARKETS.hu ? 'hu' : m === EDITION_MARKETS.us ? 'us' : 'eu';
}

/** Does this edition's checkout show a checkbox text of its own (the Australian and the US one; GET /api/checkout sends
 *  them under consent.markets), not the EU text? */
export const ownConsent = (e: LegalEdition): boolean => e === 'au' || e === 'us';

/** The languages each edition has texts in. The Australian edition is English and German only (its Australian
 *  Consumer Law text is not translated into Lithuanian or Hungarian), so a page of the Australian market never shows
 *  those two languages (src/shared/lang.ts langFor); the US edition is English only, so a page of the US market is
 *  always English. api/_lib/pay.py EDITION_LANGS is the same table. */
export const EDITION_LANGS: Readonly<Record<LegalEdition, readonly LegalLang[]>> = {
  eu: ['en', 'de', 'lt', 'hu', 'hr', 'fi', 'et', 'lv'],
  au: ['en', 'de'],
  hu: ['en', 'de', 'lt', 'hu'],
  us: ['en'],
};

/** The language an edition's texts are read in: the asked one, or English where the edition has none in it. */
export function editionLang(lang: LegalLang, m: Market = currentMarket()): LegalLang {
  return EDITION_LANGS[legalEdition(m)].includes(lang) ? lang : 'en';
}

/** A link with a market in it: a market with its own edition always carries it (m=au, m=us), also while the owner has
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

/** A legal date as the language writes it: German and Estonian "30.09.2026", Hungarian "2026. 09. 30.", Croatian "30. 9. 2026.", Finnish "30.9.2026",
 *  Latvian "30.09.2026." (with its final dot), English and Lithuanian keep
 *  the ISO order ("2026-09-30": Lithuanian writes dates that way, LST ISO 8601). */
export function formatLegalDate(iso: string, lang: LegalLang): string {
  const [y, m, d] = iso.split('-');
  return lang === 'de' || lang === 'et' ? `${d}.${m}.${y}` : lang === 'hu' ? `${y}. ${m}. ${d}.` : lang === 'hr' ? `${+d}. ${+m}. ${y}.`
    : lang === 'fi' ? `${+d}.${+m}.${y}` : lang === 'lv' ? `${d}.${m}.${y}.` : iso;
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
  // Croatian: the terms are "Opći uvjeti prodaje", the company-details page "Impresum" (the Croatian spelling)
  hr: { privacy: 'Politika privatnosti', terms: 'Opći uvjeti prodaje', withdrawal: 'Pravo na jednostrani raskid ugovora', imprint: 'Impresum', nav: 'Pravne informacije' },
  // Finnish: the terms are "Myyntiehdot", the company-details page "Yritystiedot" (company details)
  fi: { privacy: 'Tietosuojaseloste', terms: 'Myyntiehdot', withdrawal: 'Peruuttamisoikeus', imprint: 'Yritystiedot', nav: 'Oikeudelliset tiedot' },
  // Estonian: the terms are "Müügitingimused", the company-details page "Ettevõtte andmed" (Estonian has no word like "Impressum")
  et: { privacy: 'Privaatsuspoliitika', terms: 'Müügitingimused', withdrawal: 'Taganemisõigus', imprint: 'Ettevõtte andmed', nav: 'Õiguslik teave' },
  // Latvian: the terms are "Pārdošanas noteikumi", the company-details page "Rekvizīti" (the Latvian name of a company-details page)
  lv: { privacy: 'Privātuma politika', terms: 'Pārdošanas noteikumi', withdrawal: 'Atteikuma tiesības', imprint: 'Rekvizīti', nav: 'Juridiskā informācija' },
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
  // Croatia, Zakon o zaštiti potrošača čl. 81.a st. 2. and 5. (NN 59/26): "raskid ugovora", "potvrditi raskid ugovora"
  hr: { button: 'Raskid ugovora', confirm: 'Potvrditi raskid ugovora' },
  // Finland: the labels of Art. 11a(1) and (3) Directive 2011/83/EU in its official Finnish text, word for word (kuluttajansuojalaki
  // 6 luku asks for a clear label and prescribes no words of its own)
  fi: { button: 'Peruuta sopimus tästä', confirm: 'Vahvista peruuttaminen' },
  // Estonia: the labels of Art. 11a(1) and (3) Directive 2011/83/EU in its official Estonian text (OJ L, 2023/2673), word for word;
  // Võlaõigusseadus § 56⁴ lg 1 and 3 (RT I, 27.05.2026, 2) prescribes the same words
  et: { button: 'Taganen lepingust', confirm: 'Kinnitan taganemise' },
  // Latvia: the labels of Art. 11a(1) and (3) Directive 2011/83/EU in its official Latvian text (OJ L, 2023/2673), word for word; that
  // text has no word for the English "here"
  lv: { button: 'Atteikties no līguma', confirm: 'Apstiprināt atteikumu' },
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
// Australian market, CHECKOUT_LEGAL_AU below, and CONSENT_TEXT_US for the US market, CHECKOUT_LEGAL_US), version
// CONSENT_VERSION (GET /api/checkout also returns them).
// /api/checkout refuses an order without it and stores its version, time and a fingerprint of the text; the delivery
// email confirms it (the durable-medium confirmation of Art. 16(m)(iii) Directive 2011/83/EU and § 356 Abs. 5 Nr. 3
// BGB). Change both files together and bump the version (2026-09-30.1: the Australian text added, the EU text as it
// was; 2026-09-30.2: the Lithuanian and the Hungarian texts added, the English, German and Australian texts as they
// were; 2026-10-28.1: the Croatian text added, every other text as it was; 2026-10-28.2: the US text added, every other
// text as it was; 2026-10-28.3: the print box added, printConsent below = api/_lib/prints.py PRINT_CONSENT_TEXT, every waiver as it was;
// 2026-11-13.1: the Finnish, Estonian and Latvian waivers and print boxes added, every other text as it was).
// The build refuses a consent text that changed under the same version, and a version without its fingerprint
// (scripts/check_texts.mjs CONSENT_FINGERPRINTS: the check prints the new one).
export const WITHDRAWAL_CONSENT_VERSION = '2026-11-13.1';

export interface CheckoutLegal {
  /** The withdrawal checkbox: unticked by default and required before the payment page opens. Art. 16(m)
   *  Directive 2011/83/EU, § 356 Abs. 5 BGB: the right of withdrawal for digital content ends early only with this
   *  prior express consent AND this acknowledgement. Identical to api/_lib/pay.py CONSENT_TEXT. */
  withdrawalConsent: string;
  /** Shown next to the checkbox when someone tries to continue without ticking it. */
  withdrawalConsentMissing: string;
  /** The print box (src/try/PrintPick.tsx, shown by the order page's offer, src/order/PrintOffer.tsx): shown, unticked, only when the customer orders a print (the euro markets of the EU edition). A print is made
   *  to the consumer's specifications and clearly personalised, so the right of withdrawal does not apply to it (Art. 16(c) Directive 2011/83/EU);
   *  the box says so before the payment and keeps the rights for a faulty or damaged print. Identical to api/_lib/prints.py PRINT_CONSENT_TEXT. */
  printConsent: string;
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
    printConsent:
      'I know that my print is made to my order from my personal artwork, so I cannot withdraw from buying it; my rights if it arrives faulty or damaged are not affected.',
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
      { text: 'Only photograph your own eye, or the eye of someone who has agreed to it (for a child: a parent or guardian). Your photo is used to make your artwork; we keep it for up to 30 days to check quality. ' },
      { text: 'Privacy policy', doc: 'privacy' },
    ],
  },
  de: {
    withdrawalConsent:
      'Ich stimme ausdrücklich zu, dass SnapEyes sofort, vor Ablauf der Widerrufsfrist, mit der Erstellung meines digitalen Kunstwerks beginnt. Mir ist bekannt, dass ich dadurch mein Widerrufsrecht verliere, sobald damit begonnen wurde.',
    withdrawalConsentMissing: 'Bitte setzen Sie oben das Häkchen: Wir können mit Ihrem Kunstwerk erst beginnen, wenn Sie zustimmen.',
    printConsent:
      'Mir ist bekannt, dass mein Druck nach meiner Bestellung aus meinem persönlichen Kunstwerk angefertigt wird und ich seinen Kauf deshalb nicht widerrufen kann; meine Rechte bei einem fehlerhaften oder beschädigten Druck bleiben unberührt.',
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
      { text: 'Fotografieren Sie nur Ihr eigenes Auge oder das Auge einer Person, die damit einverstanden ist (bei einem Kind: ein Elternteil oder eine sorgeberechtigte Person). Ihr Foto dient dazu, Ihr Kunstwerk zu erstellen; wir bewahren es bis zu 30 Tage auf, um die Qualität zu prüfen. ' },
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
    printConsent:
      'Žinau, kad mano spaudinys gaminamas pagal mano užsakymą iš mano asmeninio kūrinio, todėl jo pirkimo atsisakyti negalėsiu; tai neriboja mano teisių, jei jis atkeliaus su trūkumais ar sugadintas.',
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
      { text: 'Fotografuokite tik savo akį arba kito žmogaus akį, jei jis su tuo sutiko (vaiko atveju sutikti turi vienas iš tėvų, globėjas ar rūpintojas). Jūsų nuotrauka naudojama Jūsų kūriniui sukurti; iki 30 dienų ją saugome kokybei tikrinti. ' },
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
    printConsent:
      'Tudomásul veszem, hogy a nyomatom a megrendelésemre, a személyes alkotásomból készül, ezért a megvásárlásától nem állhatok el; ez nem érinti a jogaimat, ha hibásan vagy sérülten érkezik.',
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
      { text: 'Csak a saját szemedet fotózd le, vagy olyan személy szemét, aki ehhez hozzájárult (gyermek esetén a szülő vagy a gondviselő). A fotódat az alkotásod elkészítéséhez használjuk; legfeljebb 30 napig megőrizzük a minőség ellenőrzéséhez. ' },
      { text: 'Adatkezelési tájékoztató', doc: 'privacy' },
    ],
  },
  // Croatian: Zakon o zaštiti potrošača (Directive 2011/83/EU Art. 16(m)): the express prior consent to start AND the acknowledgement
  // that the right of unilateral termination is lost once making has started. The buy button carries the statutory order button
  // wording "narudžba s obvezom plaćanja" (Art. 8(2)); the click that binds is Stripe's pay button, and api/_lib/pay_hr.py
  // SUBMIT_NOTE_HR stands above it. Identical to api/_lib/pay.py CONSENT_TEXT["hr"].
  hr: {
    withdrawalConsent:
      'Izričito pristajem da SnapEyes odmah, prije isteka roka za jednostrani raskid ugovora, počne izrađivati moje digitalno umjetničko djelo. Znam da time gubim pravo na jednostrani raskid ugovora čim izrada započne.',
    withdrawalConsentMissing: 'Označite kućicu iznad: vaše umjetničko djelo možemo početi izrađivati tek kada pristanete.',
    printConsent:
      'Znam da se moj ispis izrađuje po mojoj narudžbi iz mojeg osobnog umjetničkog djela, pa za njegovu kupnju nemam pravo na jednostrani raskid ugovora; to ne utječe na moja prava ako stigne neispravan ili oštećen.',
    acceptance: [
      { text: 'Narudžbom prihvaćate naše ' },
      { text: 'Opće uvjete prodaje', doc: 'terms' },
      { text: '. Pročitajte i našu ' },
      { text: 'Politiku privatnosti', doc: 'privacy' },
      { text: ' i ' },
      { text: 'obavijest o pravu na jednostrani raskid ugovora', doc: 'withdrawal' },
      { text: '.' },
    ],
    continueButton: 'Narudžba s obvezom plaćanja',
    photoNotice: [
      { text: 'Fotografirajte samo svoje oko ili oko osobe koja je na to pristala (za dijete: roditelj ili skrbnik). Vaša se fotografija koristi za izradu vašeg umjetničkog djela; čuvamo je do 30 dana radi provjere kvalitete. ' },
      { text: 'Politika privatnosti', doc: 'privacy' },
    ],
  },
  // Finnish: Art. 16(m) Directive 2011/83/EU (transposed in kuluttajansuojalaki 6 luku): the express prior consent to start AND the
  // acknowledgement that the right of withdrawal is lost once making has started. The button is "Siirry maksamaan" ("continue to
  // payment", as the English one): it only opens Stripe's page and places no order. The click that binds is Stripe's pay button, and
  // api/_lib/pay_fi.py SUBMIT_NOTE_FI puts the words of Art. 8(2) in their official Finnish text ("tilaukseen liittyy
  // maksuvelvollisuus") right above it. Identical to api/_lib/pay.py CONSENT_TEXT["fi"].
  fi: {
    withdrawalConsent:
      'Annan nimenomaisen suostumukseni siihen, että SnapEyes alkaa tehdä digitaalista taideteostani heti, ennen peruuttamisajan päättymistä. Tiedän, että menetän peruuttamisoikeuteni, kun tekeminen on alkanut.',
    withdrawalConsentMissing: 'Rastita yllä oleva ruutu: voimme aloittaa taideteoksesi vasta, kun annat suostumuksesi.',
    printConsent:
      'Tiedän, että tulosteeni tehdään tilaukseni mukaan henkilökohtaisesta taideteoksestani, joten en voi peruuttaa sen ostoa; tämä ei vaikuta oikeuksiini, jos se saapuu virheellisenä tai vahingoittuneena.',
    acceptance: [
      { text: 'Tilaamalla hyväksyt ' },
      { text: 'myyntiehtomme', doc: 'terms' },
      { text: '. Lue myös ' },
      { text: 'tietosuojaselosteemme', doc: 'privacy' },
      { text: ' ja ' },
      { text: 'tiedot peruuttamisoikeudesta', doc: 'withdrawal' },
      { text: '.' },
    ],
    continueButton: 'Siirry maksamaan',
    photoNotice: [
      { text: 'Kuvaa vain omaa silmääsi tai sellaisen ihmisen silmää, joka on antanut siihen luvan (lapsen puolesta: vanhempi tai huoltaja). Kuvaasi käytetään taideteoksesi tekemiseen; säilytämme sitä enintään 30 päivää laadun tarkistamiseksi. ' },
      { text: 'Tietosuojaseloste', doc: 'privacy' },
    ],
  },
  // Estonian: Art. 16(m) Directive 2011/83/EU (Võlaõigusseadus § 53 lg 4 p 7¹): the express prior consent to start AND the acknowledgement
  // that the right of withdrawal is lost once making has started. The buy button carries the statutory order button wording "tellimus koos
  // maksekohustusega" (Art. 8(2); Võlaõigusseadus § 62¹ lg 3); the click that binds is Stripe's pay button, and api/_lib/pay_et.py
  // SUBMIT_NOTE_ET stands above it. Identical to api/_lib/pay.py CONSENT_TEXT["et"].
  et: {
    withdrawalConsent:
      'Nõustun sõnaselgelt, et SnapEyes alustab minu digitaalse kunstiteose valmistamist kohe, enne taganemistähtaja lõppu. Olen teadlik, et kaotan oma taganemisõiguse, kui valmistamine on alanud.',
    withdrawalConsentMissing: 'Palun märgi ülal olev kast: saame sinu kunstiteosega alustada alles siis, kui oled nõus.',
    printConsent:
      'Tean, et minu trükitud pilt valmistatakse minu tellimuse järgi minu isiklikust kunstiteosest, seega ei saa ma selle ostust taganeda; see ei mõjuta minu õigusi, kui see saabub puudusega või kahjustatuna.',
    acceptance: [
      { text: 'Tellides nõustud meie ' },
      { text: 'müügitingimustega', doc: 'terms' },
      { text: '. Palun loe ka meie ' },
      { text: 'privaatsuspoliitikat', doc: 'privacy' },
      { text: ' ja ' },
      { text: 'taganemisõiguse teavet', doc: 'withdrawal' },
      { text: '.' },
    ],
    continueButton: 'Tellimus koos maksekohustusega',
    photoNotice: [
      { text: 'Pildista ainult oma silma või sellise inimese silma, kes on sellega nõustunud (lapse puhul: vanem või eestkostja). Sinu fotot kasutatakse sinu kunstiteose valmistamiseks; säilitame seda kuni 30 päeva kvaliteedi kontrollimiseks. ' },
      { text: 'Privaatsuspoliitika', doc: 'privacy' },
    ],
  },
  // Latvian: Art. 16(m) Directive 2011/83/EU in the words of its official Latvian text: the express prior consent to start AND the
  // acknowledgement that the right of withdrawal is lost once making has started. The buy button carries the statutory order button wording
  // "pasūtījums ar pienākumu maksāt" (Art. 8(2)); the click that binds is Stripe's pay button, and api/_lib/pay_lv.py SUBMIT_NOTE_LV stands
  // above it. Identical to api/_lib/pay.py CONSENT_TEXT["lv"].
  lv: {
    withdrawalConsent:
      'Es skaidri piekrītu, ka SnapEyes sāk veidot manu digitālo mākslas darbu uzreiz, pirms atteikuma termiņa beigām. Es zinu, ka zaudēju atteikuma tiesības, tiklīdz veidošana ir sākta.',
    withdrawalConsentMissing: 'Lūdzu, atzīmējiet rūtiņu augstāk: jūsu mākslas darbu varam sākt veidot tikai tad, kad piekrītat.',
    printConsent:
      'Es zinu, ka mana izdruka tiek izgatavota pēc mana pasūtījuma no mana personīgā mākslas darba, tāpēc no tās pirkuma atteikties nevaru; tas neietekmē manas tiesības, ja tā pienāk ar trūkumiem vai bojāta.',
    acceptance: [
      { text: 'Pasūtot jūs piekrītat mūsu ' },
      { text: 'pārdošanas noteikumiem', doc: 'terms' },
      { text: '. Lūdzu, izlasiet arī mūsu ' },
      { text: 'privātuma politiku', doc: 'privacy' },
      { text: ' un ' },
      { text: 'informāciju par atteikuma tiesībām', doc: 'withdrawal' },
      { text: '.' },
    ],
    continueButton: 'Pasūtījums ar pienākumu maksāt',
    photoNotice: [
      { text: 'Fotografējiet tikai savu aci vai tāda cilvēka aci, kurš tam ir piekritis (bērna gadījumā: vecāks vai aizbildnis). Jūsu fotogrāfija tiek izmantota jūsu mākslas darba izveidei; glabājam to līdz 30 dienām kvalitātes pārbaudei. ' },
      { text: 'Privātuma politika', doc: 'privacy' },
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

/** The checkout of the US market (legalEdition "us", English only): the same checkbox, with a text that keeps both EU
 *  elements (the contract is under Lithuanian law: the express consent to start before the withdrawal period ends and
 *  the acknowledgement of losing the right of withdrawal), says what a US customer reads in it (no cancelling for a
 *  change of mind once making has started, the rights for a faulty file kept, so nothing reads as "no refunds"), and
 *  adds the consent to the use of the eye photos (some US state laws treat an iris image as a biometric identifier:
 *  used only for the preview and the artwork, never to identify anyone, deleted as the privacy policy describes).
 *  Identical to api/_lib/pay.py CONSENT_TEXT_US. The line under it names the terms' "Your rights in the United States". */
// photoNotice: the photo step's line as it was before the kept free previews: a US visitor's photos are not kept (api/_lib/keep.py, 2026-11-26), and the US
// checkbox says the photos are used only to make the preview and the artwork
export const CHECKOUT_LEGAL_US: Record<'en', Pick<CheckoutLegal, 'withdrawalConsent' | 'acceptance' | 'photoNotice'>> = {
  en: {
    withdrawalConsent:
      "I expressly agree that SnapEyes starts making my personalised digital artwork right away, before the withdrawal period ends. I know that once this has started, I lose my right of withdrawal and can't cancel for a change of mind; my rights if the file is faulty are not affected. I also agree that SnapEyes uses the photos of my eyes only to make my preview and my artwork, never to identify anyone, and deletes them as its privacy policy describes.",
    photoNotice: [
      { text: 'Only photograph your own eye, or the eye of someone who has agreed to it (for a child: a parent or guardian). Your photo is used only to make your artwork. ' },
      { text: 'Privacy policy', doc: 'privacy' },
    ],
    acceptance: [
      { text: 'By ordering you accept our ' },
      { text: 'Terms of sale', doc: 'terms' },
      { text: ', including ' },
      { text: 'your rights in the United States', doc: 'terms', section: 'united-states' },
      { text: '. Please also read our ' },
      { text: 'Privacy policy', doc: 'privacy' },
      { text: ' and the ' },
      { text: 'information on the right of withdrawal', doc: 'withdrawal' },
      { text: '.' },
    ],
  },
};

/** The checkout wording for a market: the EU wording (also for the hu edition: the same checkbox, the prices differ
 *  only in the terms), with the Australian checkbox and line for the au edition and the US ones for the us edition. A
 *  language the edition has no texts in (editionLang) reads the edition's English. */
export function checkoutLegal(lang: LegalLang, market: Market = currentMarket()): CheckoutLegal {
  const l = editionLang(lang, market);
  const e = legalEdition(market);
  if (e === 'au') return { ...CHECKOUT_LEGAL[l], ...CHECKOUT_LEGAL_AU[l === 'de' ? 'de' : 'en'] };
  if (e === 'us') return { ...CHECKOUT_LEGAL.en, ...CHECKOUT_LEGAL_US.en };
  return CHECKOUT_LEGAL[l];
}
