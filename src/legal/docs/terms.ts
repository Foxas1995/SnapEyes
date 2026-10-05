// Terms of sale (AGB), English, German, Lithuanian (./terms.lt.ts) and Hungarian (./terms.hu.ts). Prices, seller and
// contact come from src/landing/config.ts.
// Deliberately NOT here: a link to the EU ODR platform (the platform was shut down on 20 July 2025, Regulation
// (EU) 2024/3228), a VAT number (the MB is not VAT-registered), any promise the code does not keep.
// The latest delivery time is DELIVERY_MAX_HOURS (src/landing/config.ts). The "contract" section says how the contract
// text is kept: the order record in the bucket, and these terms plus the withdrawal information as text in the order
// confirmation email (src/legal/plain.ts builds them into /legal/order-mail.json for api/_lib/pay.py). It also names
// the /try button that opens Stripe's page (CHECKOUT_LEGAL continueButton, the label src/try/copy.ts buy.button
// shows): that button places no order, the binding order is Stripe's own pay button (§ 312j Abs. 3 BGB).
// The right of withdrawal ends when making the file begins, as the checkout's checkbox and api/_lib/withdraw.py have
// it (see src/shared/legal.ts), or, when nothing was made, at the end of the 14-day period (the day of payment not
// counted, a last day on a Saturday, Sunday or public holiday moved to the next working day: withdraw.py
// period_end, the withdrawal page's "expiry" in the same words); "delivery" and
// "withdrawal" below say so in the same words as the withdrawal page (see its header for the server's rules). The
// seller line has no phone: owner decision (PHONE_OMITTED_BY_OWNER, src/landing/config.ts).
// Not reviewed by a lawyer.
// TERMS_AU (the end of this file) is the Australian edition (src/shared/legal.ts legalEdition "au"): the EU terms with
// prices in A$ and "no GST charged", the right of withdrawal framed as EU law and as cancelling for a change of mind
// only, complaints without any promise of our own beyond the law (no free-redo promise: that would be a warranty
// against defects needing the reg 90 text and a phone number, Competition and Consumer Regulations 2010), a new
// "Your rights in Australia" section that opens with the ACCC's own sentence, and liability and disputes that keep the
// Australian Consumer Law. Nothing in it may read as "no refunds" (ACCC: consumer guarantees cannot be excluded).
import type { EditionDocs, LegalDoc, LegalDocs, LegalSection } from '../types';
import {
  AU_PRICES, DELIVERY_MAX_HOURS, HU_PRICES, MAIL, PRICE_CENTS, SELLER, address, aud, company, eur, huf, phoneSuffix,
  representedSuffix,
} from '../facts';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { aiBlocks } from '../../shared/aiMaterial';
import { patchDoc } from '../patch';
import { lt, ltHufPrices } from './terms.lt';
import { hu, huHufPrices } from './terms.hu';

const TRANSPARENCY_EN = 'Colour from your own photo. Where your phone could not capture the finest fibres, our AI restores them.';
const TRANSPARENCY_DE = 'Die Farbe stammt aus Ihrem eigenen Foto. Wo Ihr Smartphone die feinsten Fasern nicht erfassen konnte, stellt unsere KI sie wieder her.';
const PX = '4096\u00a0px';
// The price tables below are the standard price lists. A price test (api/_lib/abtest.py; only while the owner runs one) shows
// some visitors, at random, another list: what is charged is what was shown before payment, and the order confirmation
// email names the list that applied (pay.confirmation_mail). This sentence follows every price table, in both editions.
const STANDARD_LIST_NOTE = {
  en: 'The table above is our standard price list. From time to time, for a limited period, we try other price lists on some visitors, chosen at random. You are always charged the prices shown to you on the artwork page before you pay and on the payment page, and your order confirmation email names the price list that applied to your order. Which price list you see never depends on the country you live in, only on the market (currency) you choose.',
  de: 'Die obige Tabelle ist unsere Standardpreisliste. Von Zeit zu Zeit erproben wir für einen begrenzten Zeitraum andere Preislisten bei einzelnen, zufällig ausgewählten Besuchern. Berechnet werden Ihnen immer die Preise, die Ihnen vor der Zahlung auf der Kunstwerk-Seite und auf der Zahlungsseite angezeigt werden, und Ihre Bestellbestätigung per E-Mail nennt die Preisliste, die für Ihre Bestellung galt. Welche Preisliste Sie sehen, hängt nie vom Land ab, in dem Sie wohnen, sondern nur vom Markt (der Währung), den Sie wählen.',
};
const SQUARE = '4096\u00a0×\u00a04096\u00a0px';

const en: LegalDoc = {
  title: 'Terms of sale',
  description:
    'The terms for ordering a SnapEyes digital iris artwork: the product, prices, payment, delivery, your licence, the right of withdrawal and complaints.',
  lead: 'These terms apply to every order placed on snapeyes.com. Please read them before you order. The free preview is offered without any obligation.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'Who you contract with',
      blocks: [
        `Your contract is with ${company('en')}, a small partnership under Lithuanian law (mažoji bendrija)${representedSuffix('en')}, company code ${SELLER.code}, ${address('en')}, email ${MAIL}${phoneSuffix('en')} ("we", "SnapEyes"). All details are in our [Legal notice](doc:imprint).`,
        'Our offer is made to consumers. If you are under 18, please ask a parent or guardian to order for you.',
      ],
    },
    {
      id: 'product',
      title: 'What you buy',
      blocks: [
        `A personalised digital artwork made from your own photo of an eye (or of several eyes), in the style, layout and inscription you choose. You receive one image file (JPEG) without watermark: ${SQUARE} for one eye, ${PX} on the longest side for several eyes. The artwork is delivered only as a digital file, by download. We do not sell prints, frames or any other physical product.`,
        `${TRANSPARENCY_EN} The artwork is therefore an artistic restoration, not a medical or microscope image, and it is not suitable for any medical purpose or for identifying a person.`,
        ...aiBlocks('en'),
      ],
    },
    {
      id: 'preview',
      title: 'Your preview and your file',
      blocks: [
        'Before you order, you see a free preview with a watermark and approve it. Your file follows the preview you approved: the same eye, style, layout, arrangement of the eyes and inscription, with the same colour and tone, rendered once in full resolution. At full size our AI adds the fine fibre detail that the preview is too small to show, so the very finest details can differ slightly from the preview. A preview of five to eight eyes is made from smaller copies of your photos, so it is coarser than your file.',
        'If your file clearly differs from the preview you approved (for example in colour, brightness or the pupil), that is a defect: see [Complaints and defects](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'How the contract is made',
      blocks: [
        `The previews and prices on our website are not yet a binding offer. Before you pay, you can check your eyes, style, layout and inscription and correct any input by going back or retaking a photo. You then open the payment page of our payment provider Stripe with our button "${CHECKOUT_LEGAL.en.continueButton}"; this button does not yet place an order. On that page you enter your email address and payment details and can correct them. You place a binding order when you confirm the payment there with the pay button.`,
        'The contract is concluded when your payment is confirmed. Your order page then opens, and we email you its link with your order confirmation. We start making your file there as soon as that email has gone out.',
        'The contract languages are English, German, Lithuanian and Hungarian.',
        'We store your order with the details of the contract: the artwork you ordered, the price, the date, your email address and your consent to the immediate start. Your order page shows these details for as long as we keep your order. We do not keep a separate copy of these terms for each order. Instead, your order confirmation email contains, as text, your order details, these terms and the withdrawal information with the model withdrawal form, in the version in force when you ordered: please keep that email. You can also save or print this page at any time.',
      ],
    },
    {
      id: 'prices',
      title: 'Prices and payment',
      blocks: [
        {
          dl: [
            ['One eye, Clean Iris', eur(PRICE_CENTS.studioBlack, 'en')],
            ['One eye, any other style', eur(PRICE_CENTS.artBackground, 'en')],
            ['Two eyes, any style', eur(PRICE_CENTS.coupleDuo, 'en')],
            ['Each further eye', `+${eur(PRICE_CENTS.extraEye, 'en')}`],
          ],
        },
        'All prices are final prices in euros. We are not registered for VAT, so no VAT is charged or shown. There are no delivery costs.',
        STANDARD_LIST_NOTE.en,
        'You pay in advance through our payment provider Stripe, with the payment methods shown on the payment page.',
      ],
    },
    {
      id: 'delivery',
      title: 'Delivery',
      blocks: [
        `Your order page makes your file as soon as your order confirmation email has gone out, normally within a minute of your payment; making it usually takes a few minutes. If you close the page before your file is finished, it carries on when you open it again from the link in the email. If our automatic quality check flags a file, we look at it ourselves before we release it, and we email you when it is ready. **At the latest, your file is ready for download on your order page within ${DELIVERY_MAX_HOURS} hours after your payment is confirmed.** From your order page you can download your file at any time while we keep it: 12 months from your payment (see our [Privacy policy](doc:privacy)). Each download link it creates is valid for 7 days; the page makes a new one whenever you open it. If you lose the email, write to us.`,
        'The link to your order page contains a private key: anyone who has it can download your artwork, so please keep it to yourself. Please download your file and keep a copy. After 12 months it is deleted and cannot be restored.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Right of withdrawal',
      blocks: [
        `As a consumer you generally have a 14-day right of withdrawal. For a digital file it ends early: before you pay, we ask you to agree that we start making your file straight away, before the withdrawal period ends, and to confirm that you know you lose your right of withdrawal once we have started. It therefore ends as soon as we have started making your file (the performance of the contract); we start only after your order confirmation email has gone out, normally within a minute of your payment, while your order page is open. This applies even while the file is still being made or is waiting for our quality check. If we have not started, it ends when the 14-day withdrawal period is over: the day of your payment is not counted, and if the last day of the period is a Saturday, a Sunday or a public holiday, the period ends at the end of the next working day. While your right of withdrawal lasts, you can withdraw by email, by post or online with the button "${WITHDRAWAL_ONLINE.en.button}"; the withdrawal link in your order confirmation email opens it for your order without starting to make your file. The full information, the online function and a model withdrawal form are on our [Right of withdrawal](doc:withdrawal) page.`,
      ],
    },
    {
      id: 'photos',
      title: 'Your photos',
      blocks: [
        'Only upload photos of your own eye, or of the eye of someone who has agreed to it (for a child: a parent or guardian). By uploading a photo you confirm that you may use it for this purpose.',
        'The rights in your photo remain yours. We use it only to make your preview and your artwork, as described in our [Privacy policy](doc:privacy).',
        'We may refuse an order, and refund any payment in full, if a photo clearly breaks these rules.',
      ],
    },
    {
      id: 'licence',
      title: 'What you may do with your artwork',
      blocks: [
        'You receive a non-exclusive, permanent licence to use your artwork for personal, non-commercial purposes. You may, for example, print it for yourself (at home or through a print shop), frame it, give it as a gift, use it as a background on your devices and share it on your personal social media.',
        'Without our permission (an email is enough) you may not sell the artwork or products made from it, grant others rights to it, or use it for advertising or other commercial purposes.',
        'The styles, backgrounds, layouts and the SnapEyes design remain ours, including any copyright in them. The same applies to the watermarked previews.',
      ],
    },
    {
      id: 'defects',
      title: 'Complaints and defects',
      blocks: [
        `Your statutory rights for digital content that does not conform to the contract apply in full. If your file is defective, for example it cannot be downloaded or opened, is damaged, is smaller than promised or clearly differs from the preview you approved, please write to ${MAIL} with your order number. We will render the file again free of charge or, if that does not fix it, refund you.`,
      ],
    },
    {
      id: 'liability',
      title: 'Liability',
      blocks: [
        'We are liable without limitation for intent and gross negligence, for injury to life, body or health, and wherever mandatory law provides for it. Otherwise, for slight negligence we are liable only for the breach of essential contractual obligations, and only for the damage that is typical and foreseeable for this kind of contract. The free preview is offered as it is, without any claim to its availability.',
      ],
    },
    {
      id: 'disputes',
      title: 'Disputes and applicable law',
      blocks: [
        'If something is wrong, please write to us first: most problems are solved quickly by email.',
        'If we cannot agree, consumers can turn to the Lithuanian State Consumer Rights Protection Authority (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)), which settles consumer disputes out of court, or to the consumer bodies and courts of their own country.',
        'Lithuanian law applies. If you are a consumer living in another EU country, you keep the protection of the mandatory consumer law of that country.',
      ],
    },
    {
      id: 'changes',
      title: 'Changes to these terms',
      blocks: ['The terms in force when you place your order apply to that order.'],
    },
  ],
};

const de: LegalDoc = {
  title: 'Allgemeine Geschäfts\u00ADbedingungen (AGB)',
  description:
    'Die Bedingungen für die Bestellung eines digitalen Iris-Kunstwerks bei SnapEyes: Produkt, Preise, Zahlung, Lieferung, Nutzungsrecht, Widerrufsrecht und Reklamationen.',
  lead: 'Diese Bedingungen gelten für jede Bestellung auf snapeyes.com. Bitte lesen Sie sie, bevor Sie bestellen. Die kostenlose Vorschau ist unverbindlich.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'Ihr Vertragspartner',
      blocks: [
        `Ihr Vertrag kommt zustande mit ${company('de')}, einer Kleingesellschaft nach litauischem Recht (mažoji bendrija)${representedSuffix('de')}, Unternehmenscode ${SELLER.code}, ${address('de')}, E-Mail ${MAIL}${phoneSuffix('de')} („wir“, „SnapEyes“). Alle Angaben finden Sie im [Impressum](doc:imprint).`,
        'Unser Angebot richtet sich an Verbraucher. Wenn Sie jünger als 18 Jahre sind, bitten Sie einen Elternteil oder eine sorgeberechtigte Person, für Sie zu bestellen.',
      ],
    },
    {
      id: 'product',
      title: 'Was Sie kaufen',
      blocks: [
        `Ein personalisiertes digitales Kunstwerk aus Ihrem eigenen Foto eines Auges (oder mehrerer Augen), im Stil, in der Anordnung und mit der Widmung Ihrer Wahl. Sie erhalten eine Bilddatei (JPEG) ohne Wasserzeichen: ${SQUARE} bei einem Auge, bei mehreren Augen ${PX} an der längsten Seite. Das Kunstwerk wird ausschließlich als digitale Datei zum Download geliefert. Drucke, Rahmen oder andere physische Produkte verkaufen wir nicht.`,
        `${TRANSPARENCY_DE} Das Kunstwerk ist daher eine künstlerische Restaurierung, keine medizinische Aufnahme und keine Mikroskopaufnahme, und es eignet sich weder für medizinische Zwecke noch zur Identifizierung einer Person.`,
        ...aiBlocks('de'),
      ],
    },
    {
      id: 'preview',
      title: 'Ihre Vorschau und Ihre Datei',
      blocks: [
        'Vor der Bestellung sehen Sie eine kostenlose Vorschau mit Wasserzeichen und geben sie frei. Ihre Datei folgt der freigegebenen Vorschau: dasselbe Auge, derselbe Stil, dieselbe Anordnung, dieselbe Reihenfolge der Augen und dieselbe Widmung, mit derselben Farbe und Tonalität, einmalig in voller Auflösung erstellt. In voller Größe ergänzt unsere KI die feinen Faserdetails, für die die Vorschau zu klein ist; die allerfeinsten Details können daher leicht von der Vorschau abweichen. Eine Vorschau mit fünf bis acht Augen wird aus kleineren Kopien Ihrer Fotos erstellt und ist daher gröber als Ihre Datei.',
        'Weicht Ihre Datei deutlich von der freigegebenen Vorschau ab (zum Beispiel in Farbe, Helligkeit oder bei der Pupille), ist das ein Mangel: siehe [Reklamationen und Mängel](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'Vertragsschluss',
      blocks: [
        `Die Vorschauen und Preise auf unserer Website sind noch kein verbindliches Angebot. Vor der Zahlung können Sie Ihre Augen, den Stil, die Anordnung und die Widmung prüfen und Eingaben korrigieren, indem Sie zurückgehen oder ein Foto neu aufnehmen. Danach öffnen Sie mit unserer Schaltfläche „${CHECKOUT_LEGAL.de.continueButton}“ die Zahlungsseite unseres Zahlungsdienstleisters Stripe; diese Schaltfläche löst noch keine Bestellung aus. Auf dieser Seite geben Sie Ihre E-Mail-Adresse und Zahlungsangaben ein und können sie korrigieren. Eine verbindliche Bestellung geben Sie ab, wenn Sie dort die Zahlung mit der Zahlungsschaltfläche bestätigen.`,
        'Der Vertrag kommt zustande, sobald Ihre Zahlung bestätigt ist. Dann öffnet sich Ihre Bestellseite, und wir senden Ihnen deren Link mit Ihrer Bestellbestätigung per E-Mail. Sobald diese E-Mail versandt ist, beginnen wir dort mit Ihrer Datei.',
        'Vertragssprachen sind Deutsch, Englisch, Litauisch und Ungarisch.',
        'Wir speichern Ihre Bestellung mit den Vertragsdaten: das bestellte Kunstwerk, den Preis, das Datum, Ihre E-Mail-Adresse und Ihre Zustimmung zum sofortigen Beginn. Ihre Bestellseite zeigt diese Angaben, solange wir Ihre Bestellung aufbewahren. Eine eigene Kopie dieser Bedingungen je Bestellung bewahren wir nicht auf. Stattdessen enthält Ihre Bestellbestätigung per E-Mail als Text Ihre Bestelldaten, diese Bedingungen und die Widerrufsbelehrung mit dem Muster-Widerrufsformular, in der bei Ihrer Bestellung gültigen Fassung: Bitte bewahren Sie diese E-Mail auf. Sie können diese Seite außerdem jederzeit speichern oder ausdrucken.',
      ],
    },
    {
      id: 'prices',
      title: 'Preise und Zahlung',
      blocks: [
        {
          dl: [
            ['Ein Auge, Clean Iris', eur(PRICE_CENTS.studioBlack, 'de')],
            ['Ein Auge, jeder andere Stil', eur(PRICE_CENTS.artBackground, 'de')],
            ['Zwei Augen, jeder Stil', eur(PRICE_CENTS.coupleDuo, 'de')],
            ['Jedes weitere Auge', `+${eur(PRICE_CENTS.extraEye, 'de')}`],
          ],
        },
        'Alle Preise sind Endpreise in Euro. Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet oder ausgewiesen. Versandkosten fallen nicht an.',
        STANDARD_LIST_NOTE.de,
        'Sie zahlen im Voraus über unseren Zahlungsdienstleister Stripe, mit den auf der Zahlungsseite angezeigten Zahlungsarten.',
      ],
    },
    {
      id: 'delivery',
      title: 'Lieferung',
      blocks: [
        `Ihre Bestellseite erstellt Ihre Datei, sobald Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise innerhalb einer Minute nach Ihrer Zahlung; die Erstellung dauert meist wenige Minuten. Schließen Sie die Seite, bevor Ihre Datei fertig ist, macht sie weiter, wenn Sie sie über den Link in der E-Mail wieder öffnen. Meldet unsere automatische Qualitätsprüfung eine Datei, sehen wir sie uns vor der Freigabe selbst an und benachrichtigen Sie per E-Mail, sobald sie fertig ist. **Spätestens ${DELIVERY_MAX_HOURS} Stunden nach der Bestätigung Ihrer Zahlung steht Ihre Datei auf Ihrer Bestellseite zum Download bereit.** Über Ihre Bestellseite können Sie Ihre Datei jederzeit herunterladen, solange wir sie aufbewahren: 12 Monate ab Ihrer Zahlung (siehe [Datenschutzerklärung](doc:privacy)). Jeder Download-Link, den die Seite erzeugt, ist 7 Tage gültig; beim nächsten Öffnen erzeugt sie einen neuen. Haben Sie die E-Mail verloren, schreiben Sie uns.`,
        'Der Link zu Ihrer Bestellseite enthält einen privaten Schlüssel: Jede Person, die ihn hat, kann Ihr Kunstwerk herunterladen. Bitte geben Sie ihn nicht weiter. Laden Sie Ihre Datei herunter und bewahren Sie eine Kopie auf. Nach 12 Monaten wird sie gelöscht und kann nicht wiederhergestellt werden.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Widerrufsrecht',
      blocks: [
        `Als Verbraucher haben Sie grundsätzlich ein 14-tägiges Widerrufsrecht. Bei einer digitalen Datei erlischt es vorzeitig: Vor der Zahlung bitten wir Sie, zuzustimmen, dass wir sofort, vor Ablauf der Widerrufsfrist, mit der Erstellung Ihrer Datei beginnen, und zu bestätigen, dass Ihnen bekannt ist, dass Sie dadurch Ihr Widerrufsrecht verlieren, sobald damit begonnen wurde. Es erlischt daher, sobald wir mit der Erstellung Ihrer Datei (der Vertragserfüllung) begonnen haben; damit beginnen wir erst, nachdem Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise innerhalb einer Minute nach Ihrer Zahlung, während Ihre Bestellseite geöffnet ist. Das gilt auch, solange die Datei noch erstellt wird oder auf unsere Qualitätsprüfung wartet. Haben wir noch nicht begonnen, erlischt es mit Ablauf der 14-tägigen Widerrufsfrist: Der Tag Ihrer Zahlung wird nicht mitgezählt, und fällt der letzte Tag der Frist auf einen Samstag, einen Sonntag oder einen gesetzlichen Feiertag, endet die Frist mit Ablauf des nächsten Arbeitstags. Solange Ihr Widerrufsrecht besteht, können Sie per E-Mail, per Post oder online mit der Schaltfläche „${WITHDRAWAL_ONLINE.de.button}“ widerrufen; der Widerrufslink in Ihrer Bestellbestätigung per E-Mail öffnet sie für Ihre Bestellung, ohne dass wir mit der Erstellung Ihrer Datei beginnen. Alle Einzelheiten, die Online-Funktion und ein Muster-Widerrufsformular finden Sie in unserer [Widerrufsbelehrung](doc:withdrawal).`,
      ],
    },
    {
      id: 'photos',
      title: 'Ihre Fotos',
      blocks: [
        'Laden Sie nur Fotos Ihres eigenen Auges hoch oder des Auges einer Person, die damit einverstanden ist (bei einem Kind: ein Elternteil oder eine sorgeberechtigte Person). Mit dem Hochladen bestätigen Sie, dass Sie das Foto für diesen Zweck verwenden dürfen.',
        'Die Rechte an Ihrem Foto bleiben bei Ihnen. Wir verwenden es nur, um Ihre Vorschau und Ihr Kunstwerk zu erstellen, wie in unserer [Datenschutzerklärung](doc:privacy) beschrieben.',
        'Wir können eine Bestellung ablehnen und eine bereits geleistete Zahlung vollständig erstatten, wenn ein Foto offensichtlich gegen diese Regeln verstößt.',
      ],
    },
    {
      id: 'licence',
      title: 'Was Sie mit Ihrem Kunstwerk tun dürfen',
      blocks: [
        'Sie erhalten ein einfaches, zeitlich unbegrenztes Nutzungsrecht an Ihrem Kunstwerk für private, nicht kommerzielle Zwecke. Sie dürfen es zum Beispiel für sich ausdrucken (zu Hause oder in einer Druckerei), rahmen, verschenken, als Hintergrundbild auf Ihren Geräten nutzen und in Ihren privaten sozialen Netzwerken teilen.',
        'Ohne unsere Zustimmung (eine E-Mail genügt) dürfen Sie das Kunstwerk oder daraus hergestellte Produkte nicht verkaufen, Dritten Rechte daran einräumen oder es für Werbung oder andere kommerzielle Zwecke verwenden.',
        'Die Stile, Hintergründe, Anordnungen und das Design von SnapEyes bleiben unser Eigentum, einschließlich etwaiger Urheberrechte daran. Das gilt auch für die Vorschauen mit Wasserzeichen.',
      ],
    },
    {
      id: 'defects',
      title: 'Reklamationen und Mängel',
      blocks: [
        `Ihre gesetzlichen Rechte bei digitalen Inhalten, die nicht vertragsgemäß sind, gelten uneingeschränkt. Ist Ihre Datei mangelhaft, lässt sie sich zum Beispiel nicht herunterladen oder öffnen, ist sie beschädigt, kleiner als zugesagt oder weicht sie deutlich von der freigegebenen Vorschau ab, schreiben Sie bitte mit Ihrer Bestellnummer an ${MAIL}. Wir erstellen die Datei kostenlos neu oder erstatten Ihnen den Preis, wenn das den Mangel nicht behebt.`,
      ],
    },
    {
      id: 'liability',
      title: 'Haftung',
      blocks: [
        'Wir haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit, bei Verletzung von Leben, Körper oder Gesundheit und soweit zwingendes Recht es vorsieht. Im Übrigen haften wir bei leichter Fahrlässigkeit nur für die Verletzung wesentlicher Vertragspflichten und nur für den vertragstypischen, vorhersehbaren Schaden. Die kostenlose Vorschau wird so angeboten, wie sie ist, ohne Anspruch auf ihre Verfügbarkeit.',
      ],
    },
    {
      id: 'disputes',
      title: 'Streitigkeiten und anwendbares Recht',
      blocks: [
        'Wenn etwas nicht stimmt, schreiben Sie uns bitte zuerst: Die meisten Probleme lassen sich schnell per E-Mail lösen.',
        'Können wir uns nicht einigen, können sich Verbraucher an die litauische Staatliche Verbraucherschutzbehörde (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)) wenden, die Verbraucherstreitigkeiten außergerichtlich beilegt, oder an die Verbraucherschutzstellen und Gerichte ihres eigenen Landes.',
        'Es gilt litauisches Recht. Wenn Sie als Verbraucher in einem anderen EU-Land leben, behalten Sie den Schutz der zwingenden Verbraucherschutzvorschriften dieses Landes.',
      ],
    },
    {
      id: 'changes',
      title: 'Änderungen dieser Bedingungen',
      blocks: ['Für Ihre Bestellung gelten die Bedingungen, die zum Zeitpunkt Ihrer Bestellung gültig sind.'],
    },
  ],
};

export const TERMS: LegalDocs = { en, de, lt, hu };

// ------------------------------------------------------------------------------------------ the Australian edition
// The opening sentence of "australia" is the ACCC's wording, word for word, in both languages (the German text follows
// it with a translation). The remedies are the prescribed text for services (Competition and Consumer Regulations 2010
// reg 90, as the ACCC publishes it), word for word in English and translated in German: never more than the law gives
// (a remedy stated more generously would itself be an extra promise, a warranty against defects with its own document
// rules), and never a promise of ours to redo or refund. The guarantees are paraphrased from ss 60-62 (due care and
// skill, fit for any purpose made known, reasonable time).
const AU_ID = 'australia';

/** A shared section whose link to "defects" names that section's Australian title (the build stops if the EU wording
 *  it replaces is not there any more). */
const relabel = (from: string, to: string) => (s: LegalSection): LegalSection => {
  const blocks = s.blocks.map((b) => (typeof b === 'string' ? b.replace(from, to) : b));
  if (JSON.stringify(blocks) === JSON.stringify(s.blocks)) throw new Error(`terms, Australian edition: "${from}" not found`);
  return { ...s, blocks };
};

const auEn = patchDoc(en, {
  description:
    'The terms for ordering a SnapEyes digital iris artwork in Australian dollars: the product, prices, payment, delivery, your licence, cancelling, your rights under the Australian Consumer Law and complaints.',
  lead: `These terms apply to every order placed on snapeyes.com in Australian dollars (A$), and they include [your rights in Australia](#${AU_ID}). Please read them before you order. The free preview is offered without any obligation.`,
  replace: {
    preview: relabel('[Complaints and defects](#defects)', '[Complaints and faulty files](#defects)'),
    contract: relabel('The contract languages are English, German, Lithuanian and Hungarian.', 'The contract languages are English and German.'),
    prices: (s): LegalSection => ({
      ...s,
      blocks: [
        {
          dl: [
            ['One eye, Clean Iris', aud(AU_PRICES.one_eye_studio_black, 'en')],
            ['One eye, any other style', aud(AU_PRICES.one_eye_art, 'en')],
            ['Two eyes, any style', aud(AU_PRICES.two_eyes, 'en')],
            ['Each further eye', `+${aud(AU_PRICES.each_further_eye, 'en')}`],
          ],
        },
        'All prices are in Australian dollars (A$), and each is the total price you pay: no GST, no delivery cost, no card surcharge and no other fee is added. We are not registered for GST in Australia, so no GST is charged. Your order confirmation email includes your invoice.',
        'You pay in advance through our payment provider Stripe, with the payment methods shown on the payment page. Your card issuer may charge its own fee for a payment to a business based outside Australia; we do not charge it and do not receive it.',
        STANDARD_LIST_NOTE.en,
      ],
    }),
    withdrawal: {
      id: 'withdrawal',
      title: 'Cancelling for a change of mind (right of withdrawal)',
      blocks: [
        `Your contract is governed by Lithuanian law (see [Disputes and applicable law](#disputes)), and EU consumer law gives consumers a 14-day right of withdrawal: a right to cancel without giving a reason. For a digital file it ends early: before you pay, we ask you to agree that we start making your file straight away, before the withdrawal period ends, and to confirm that you know you lose your right of withdrawal, and so can no longer cancel for a change of mind, once we have started. It therefore ends as soon as we have started making your file (the performance of the contract); we start only after your order confirmation email has gone out, normally within a minute of your payment, while your order page is open. This applies even while the file is still being made or is waiting for our quality check. If we have not started, it ends when the 14-day withdrawal period is over: the day of your payment is not counted, and if the last day of the period is a Saturday, a Sunday or a public holiday, the period ends at the end of the next working day. While your right of withdrawal lasts, you can withdraw by email, by post or online with the button "${WITHDRAWAL_ONLINE.en.button}", and we refund you in full; the withdrawal link in your order confirmation email opens it for your order without starting to make your file. The full information, the online function and a model withdrawal form are on our [Right of withdrawal](doc:withdrawal) page.`,
        `**This is only about cancelling for a change of mind.** It never limits your rights if your file is faulty or not as described: see [Complaints and faulty files](#defects) and [Your rights in Australia](#${AU_ID}).`,
      ],
    },
    defects: {
      id: 'defects',
      title: 'Complaints and faulty files',
      blocks: [
        `If your file is faulty, for example it cannot be downloaded or opened, is damaged, is smaller than promised, clearly differs from the preview you approved or is not ready in time, please write to ${MAIL} with your order number. We look at every complaint personally. Your rights are the ones the law gives you, and these terms do not limit them: in Australia, the consumer guarantees of the Australian Consumer Law (see [Your rights in Australia](#${AU_ID})); in the EU, the statutory rights for digital content that does not conform to the contract.`,
      ],
    },
    liability: {
      id: 'liability',
      title: 'Liability',
      blocks: [
        `Nothing in these terms excludes, restricts or modifies your rights under the Australian Consumer Law or under any other law that cannot be excluded (see [Your rights in Australia](#${AU_ID})). Subject to that, we are liable without limitation for intent and gross negligence, for injury to life, body or health, and wherever mandatory law provides for it; otherwise we are liable for the loss or damage that was reasonably foreseeable when the contract was made. The free preview is offered as it is, without any claim to its availability.`,
      ],
    },
    disputes: {
      id: 'disputes',
      title: 'Disputes and applicable law',
      blocks: [
        'If something is wrong, please write to us first: most problems are solved quickly by email.',
        'If we cannot agree and you are a consumer in Australia, you can turn to the consumer protection agency (fair trading office) of your state or territory, which helps with complaints about businesses, and read about your rights on the website of the Australian Competition and Consumer Commission ([accc.gov.au](https://www.accc.gov.au)).',
        'Consumers in the EU can turn to the Lithuanian State Consumer Rights Protection Authority (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)), which settles consumer disputes out of court, or to the consumer bodies and courts of their own country.',
        'Lithuanian law applies. You keep the protection of the mandatory consumer law of the country where you live: in Australia, the Australian Consumer Law; in another EU country, the mandatory consumer law of that country.',
      ],
    },
  },
  after: {
    defects: [
      {
        id: AU_ID,
        title: 'Your rights in Australia',
        blocks: [
          '**Our services come with guarantees that cannot be excluded under the Australian Consumer Law.**',
          `If you are a consumer in Australia, these guarantees apply to your order, whatever else these terms say. We make your artwork for you as a service, from your own photo, and under the Australian Consumer Law it must be made with due care and skill, be reasonably fit for any purpose you tell us about or that we describe (for example your personal artwork, matching the preview you approved and the description on our website) and be delivered within a reasonable time (we deliver at the latest ${DELIVERY_MAX_HOURS} hours after your payment, see [Delivery](#delivery)).`,
          'For major failures with the service, you are entitled: to cancel your service contract with us; and to a refund for the unused portion, or to compensation for its reduced value. You are also entitled to be compensated for any other reasonably foreseeable loss or damage. If the failure does not amount to a major failure, you are entitled to have problems with the service rectified in a reasonable time and, if this is not done, to cancel your contract and obtain a refund for the unused portion of the contract.',
          `Changing your mind: once we have started making your file, you can't cancel just because you changed your mind (you agreed to this at checkout, see [Cancelling for a change of mind](#withdrawal)). That doesn't affect any of the rights above.`,
          `To make a claim, reply to your order confirmation email or write to ${MAIL} with your order number and what is wrong. You don't need to send anything back. We deal with every claim personally.`,
          'Nothing in these terms excludes, restricts or modifies any right or remedy, or any guarantee, warranty or other term or condition, implied or imposed by the Australian Consumer Law that cannot lawfully be excluded, restricted or modified. Where anything in these terms seems to do so, it does not apply to that extent.',
          'How we handle your eye photos under Australian privacy law: see [Your data if you live in Australia](doc:privacy#australia) in our privacy policy.',
        ],
      },
    ],
  },
});

const auDe = patchDoc(de, {
  description:
    'Die Bedingungen für die Bestellung eines digitalen Iris-Kunstwerks bei SnapEyes in australischen Dollar: Produkt, Preise, Zahlung, Lieferung, Nutzungsrecht, Widerruf, Ihre Rechte nach dem Australian Consumer Law und Reklamationen.',
  lead: `Diese Bedingungen gelten für jede Bestellung auf snapeyes.com in australischen Dollar (A$) und enthalten [Ihre Rechte in Australien](#${AU_ID}). Bitte lesen Sie sie, bevor Sie bestellen. Die kostenlose Vorschau ist unverbindlich.`,
  replace: {
    preview: relabel('[Reklamationen und Mängel](#defects)', '[Reklamationen und mangelhafte Dateien](#defects)'),
    contract: relabel('Vertragssprachen sind Deutsch, Englisch, Litauisch und Ungarisch.', 'Vertragssprachen sind Deutsch und Englisch.'),
    prices: (s): LegalSection => ({
      ...s,
      blocks: [
        {
          dl: [
            ['Ein Auge, Clean Iris', aud(AU_PRICES.one_eye_studio_black, 'de')],
            ['Ein Auge, jeder andere Stil', aud(AU_PRICES.one_eye_art, 'de')],
            ['Zwei Augen, jeder Stil', aud(AU_PRICES.two_eyes, 'de')],
            ['Jedes weitere Auge', `+${aud(AU_PRICES.each_further_eye, 'de')}`],
          ],
        },
        'Alle Preise sind in australischen Dollar (A$) angegeben und jeweils der Gesamtpreis, den Sie zahlen: Es kommen keine GST, keine Versandkosten, kein Kartenzuschlag und keine sonstigen Gebühren hinzu. Wir sind in Australien nicht für die GST registriert, daher wird keine GST berechnet. Ihre Bestellbestätigung per E-Mail enthält Ihre Rechnung.',
        'Sie zahlen im Voraus über unseren Zahlungsdienstleister Stripe, mit den auf der Zahlungsseite angezeigten Zahlungsarten. Ihr Kartenaussteller kann für eine Zahlung an ein Unternehmen außerhalb Australiens eigene Gebühren berechnen; diese berechnen nicht wir, und wir erhalten sie nicht.',
        STANDARD_LIST_NOTE.de,
      ],
    }),
    withdrawal: {
      id: 'withdrawal',
      title: 'Widerruf ohne Angabe von Gründen (Widerrufsrecht)',
      blocks: [
        `Für Ihren Vertrag gilt litauisches Recht (siehe [Streitigkeiten und anwendbares Recht](#disputes)), und das EU-Verbraucherrecht gibt Verbrauchern ein 14-tägiges Widerrufsrecht: das Recht, den Vertrag ohne Angabe von Gründen zu lösen. Bei einer digitalen Datei erlischt es vorzeitig: Vor der Zahlung bitten wir Sie, zuzustimmen, dass wir sofort, vor Ablauf der Widerrufsfrist, mit der Erstellung Ihrer Datei beginnen, und zu bestätigen, dass Ihnen bekannt ist, dass Sie dadurch Ihr Widerrufsrecht verlieren, sobald damit begonnen wurde, und den Vertrag dann nicht mehr ohne Angabe von Gründen lösen können. Es erlischt daher, sobald wir mit der Erstellung Ihrer Datei (der Vertragserfüllung) begonnen haben; damit beginnen wir erst, nachdem Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise innerhalb einer Minute nach Ihrer Zahlung, während Ihre Bestellseite geöffnet ist. Das gilt auch, solange die Datei noch erstellt wird oder auf unsere Qualitätsprüfung wartet. Haben wir noch nicht begonnen, erlischt es mit Ablauf der 14-tägigen Widerrufsfrist: Der Tag Ihrer Zahlung wird nicht mitgezählt, und fällt der letzte Tag der Frist auf einen Samstag, einen Sonntag oder einen gesetzlichen Feiertag, endet die Frist mit Ablauf des nächsten Arbeitstags. Solange Ihr Widerrufsrecht besteht, können Sie per E-Mail, per Post oder online mit der Schaltfläche „${WITHDRAWAL_ONLINE.de.button}“ widerrufen, und wir erstatten Ihnen den vollen Preis; der Widerrufslink in Ihrer Bestellbestätigung per E-Mail öffnet sie für Ihre Bestellung, ohne dass wir mit der Erstellung Ihrer Datei beginnen. Alle Einzelheiten, die Online-Funktion und ein Muster-Widerrufsformular finden Sie in unserer [Widerrufsbelehrung](doc:withdrawal).`,
        `**Das betrifft nur den Widerruf ohne Angabe von Gründen.** Ihre Rechte, wenn Ihre Datei mangelhaft ist oder nicht der Beschreibung entspricht, schränkt es nie ein: siehe [Reklamationen und mangelhafte Dateien](#defects) und [Ihre Rechte in Australien](#${AU_ID}).`,
      ],
    },
    defects: {
      id: 'defects',
      title: 'Reklamationen und mangelhafte Dateien',
      blocks: [
        `Ist Ihre Datei mangelhaft, lässt sie sich zum Beispiel nicht herunterladen oder öffnen, ist sie beschädigt, kleiner als zugesagt, weicht sie deutlich von der freigegebenen Vorschau ab oder ist sie nicht rechtzeitig fertig, schreiben Sie bitte mit Ihrer Bestellnummer an ${MAIL}. Wir sehen uns jede Reklamation persönlich an. Es gelten Ihre gesetzlichen Rechte, und diese Bedingungen schränken sie nicht ein: in Australien die Verbrauchergarantien des Australian Consumer Law (siehe [Ihre Rechte in Australien](#${AU_ID})); in der EU die gesetzlichen Rechte bei digitalen Inhalten, die nicht vertragsgemäß sind.`,
      ],
    },
    liability: {
      id: 'liability',
      title: 'Haftung',
      blocks: [
        `Nichts in diesen Bedingungen schließt Ihre Rechte nach dem Australian Consumer Law oder nach anderem Recht, das nicht ausgeschlossen werden kann, aus, beschränkt oder ändert sie (siehe [Ihre Rechte in Australien](#${AU_ID})). Im Übrigen haften wir unbeschränkt bei Vorsatz und grober Fahrlässigkeit, bei Verletzung von Leben, Körper oder Gesundheit und soweit zwingendes Recht es vorsieht; ansonsten haften wir für die Verluste und Schäden, die bei Vertragsschluss vernünftigerweise vorhersehbar waren. Die kostenlose Vorschau wird so angeboten, wie sie ist, ohne Anspruch auf ihre Verfügbarkeit.`,
      ],
    },
    disputes: {
      id: 'disputes',
      title: 'Streitigkeiten und anwendbares Recht',
      blocks: [
        'Wenn etwas nicht stimmt, schreiben Sie uns bitte zuerst: Die meisten Probleme lassen sich schnell per E-Mail lösen.',
        'Können wir uns nicht einigen und sind Sie Verbraucher in Australien, können Sie sich an die Verbraucherschutzbehörde (Fair Trading) Ihres Bundesstaats oder Territoriums wenden, die bei Beschwerden über Unternehmen hilft, und sich auf der Website der Australian Competition and Consumer Commission ([accc.gov.au](https://www.accc.gov.au)) über Ihre Rechte informieren.',
        'Verbraucher in der EU können sich an die litauische Staatliche Verbraucherschutzbehörde (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)) wenden, die Verbraucherstreitigkeiten außergerichtlich beilegt, oder an die Verbraucherschutzstellen und Gerichte ihres eigenen Landes.',
        'Es gilt litauisches Recht. Den Schutz der zwingenden Verbraucherschutzvorschriften des Landes, in dem Sie leben, behalten Sie: in Australien das Australian Consumer Law, in einem anderen EU-Land die zwingenden Verbraucherschutzvorschriften dieses Landes.',
      ],
    },
  },
  after: {
    defects: [
      {
        id: AU_ID,
        title: 'Ihre Rechte in Australien',
        blocks: [
          '**Our services come with guarantees that cannot be excluded under the Australian Consumer Law.** (Unsere Leistungen sind mit Garantien verbunden, die nach dem australischen Verbraucherrecht, dem Australian Consumer Law, nicht ausgeschlossen werden können.)',
          `Wenn Sie als Verbraucher in Australien bestellen, gelten diese Garantien für Ihre Bestellung, unabhängig davon, was diese Bedingungen sonst sagen. Wir erstellen Ihr Kunstwerk für Sie als Dienstleistung aus Ihrem eigenen Foto, und nach dem Australian Consumer Law muss es mit der gebotenen Sorgfalt und Sachkunde erstellt werden, für jeden Zweck, den Sie uns mitteilen oder den wir beschreiben, vernünftigerweise geeignet sein (zum Beispiel Ihr persönliches Kunstwerk, entsprechend der freigegebenen Vorschau und der Beschreibung auf unserer Website) und innerhalb einer angemessenen Zeit geliefert werden (wir liefern spätestens ${DELIVERY_MAX_HOURS} Stunden nach Ihrer Zahlung, siehe [Lieferung](#delivery)).`,
          'Bei einem erheblichen Mangel der Leistung (major failure) haben Sie Anspruch darauf, Ihren Dienstleistungsvertrag mit uns zu kündigen, und auf eine Erstattung für den nicht genutzten Teil oder einen Ausgleich für dessen Minderwert. Außerdem haben Sie Anspruch auf Ersatz für jeden anderen vernünftigerweise vorhersehbaren Verlust oder Schaden. Ist der Mangel nicht erheblich, haben Sie Anspruch darauf, dass die Probleme mit der Leistung innerhalb angemessener Zeit behoben werden, und wenn das nicht geschieht, den Vertrag zu kündigen und eine Erstattung für den nicht genutzten Teil des Vertrags zu erhalten.',
          `Meinungsänderung: Sobald wir mit der Erstellung Ihrer Datei begonnen haben, können Sie den Vertrag nicht mehr nur deshalb lösen, weil Sie es sich anders überlegt haben (dem haben Sie bei der Bestellung zugestimmt, siehe [Widerruf ohne Angabe von Gründen](#withdrawal)). Die oben genannten Rechte bleiben davon unberührt.`,
          `Für eine Reklamation antworten Sie auf Ihre Bestellbestätigung oder schreiben an ${MAIL}, mit Ihrer Bestellnummer und dem, was nicht stimmt. Sie müssen nichts zurücksenden. Wir bearbeiten jede Reklamation persönlich.`,
          'Nichts in diesen Bedingungen schließt Rechte, Rechtsbehelfe, Garantien, Gewährleistungen oder sonstige Bedingungen, die das Australian Consumer Law vorsieht und die rechtlich nicht ausgeschlossen, beschränkt oder geändert werden können, aus, beschränkt oder ändert sie. Soweit diese Bedingungen etwas anderes zu sagen scheinen, gelten sie insoweit nicht.',
          'Wie wir Ihre Augenfotos nach australischem Datenschutzrecht behandeln: siehe [Ihre Daten, wenn Sie in Australien leben](doc:privacy#australia) in unserer Datenschutzerklärung.',
        ],
      },
    ],
  },
});

// the Australian pages exist in English and German only (src/shared/legal.ts EDITION_LANGS), so its contract languages
// are those two
export const TERMS_AU: EditionDocs = { en: auEn, de: auDe };

// ------------------------------------------------------------------------------------------ the Hungarian edition
// The EU texts with the prices of the Hungarian market in forints (api/_lib/markets.py, "6 990 Ft"): only the "prices"
// section changes, in every language (the Hungarian and Lithuanian ones are in ./terms.hu.ts and ./terms.lt.ts). Every
// other section is shared word for word, so a change to it reaches both editions.
const AFTER_CURRENCY_EN = 'If our website shows you prices in another currency, the payment page and your order confirmation email show the currency and amount you actually pay.';
const AFTER_CURRENCY_DE = 'Zeigt Ihnen unsere Website Preise in einer anderen Währung, nennen die Zahlungsseite und Ihre Bestellbestätigung per E-Mail die Währung und den Betrag, die Sie tatsächlich zahlen.';

const enHufPrices: LegalSection = {
  id: 'prices',
  title: 'Prices and payment',
  blocks: [
    {
      dl: [
        ['One eye, Clean Iris', huf(HU_PRICES.one_eye_studio_black, 'en')],
        ['One eye, any other style', huf(HU_PRICES.one_eye_art, 'en')],
        ['Two eyes, any style', huf(HU_PRICES.two_eyes, 'en')],
        ['Each further eye', `+${huf(HU_PRICES.each_further_eye, 'en')}`],
      ],
    },
    `All prices are final prices in Hungarian forints (Ft). We are not registered for VAT, so no VAT is charged or shown. There are no delivery costs. ${AFTER_CURRENCY_EN}`,
    STANDARD_LIST_NOTE.en,
    'You pay in advance through our payment provider Stripe, with the payment methods shown on the payment page.',
  ],
};

const deHufPrices: LegalSection = {
  id: 'prices',
  title: 'Preise und Zahlung',
  blocks: [
    {
      dl: [
        ['Ein Auge, Clean Iris', huf(HU_PRICES.one_eye_studio_black, 'de')],
        ['Ein Auge, jeder andere Stil', huf(HU_PRICES.one_eye_art, 'de')],
        ['Zwei Augen, jeder Stil', huf(HU_PRICES.two_eyes, 'de')],
        ['Jedes weitere Auge', `+${huf(HU_PRICES.each_further_eye, 'de')}`],
      ],
    },
    `Alle Preise sind Endpreise in ungarischen Forint (Ft). Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet oder ausgewiesen. Versandkosten fallen nicht an. ${AFTER_CURRENCY_DE}`,
    STANDARD_LIST_NOTE.de,
    'Sie zahlen im Voraus über unseren Zahlungsdienstleister Stripe, mit den auf der Zahlungsseite angezeigten Zahlungsarten.',
  ],
};

export const TERMS_HU: LegalDocs = {
  en: patchDoc(en, { replace: { prices: enHufPrices } }),
  de: patchDoc(de, { replace: { prices: deHufPrices } }),
  lt: patchDoc(lt, { replace: { prices: ltHufPrices } }),
  hu: patchDoc(hu, { replace: { prices: huHufPrices } }),
};
