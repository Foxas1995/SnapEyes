// Terms of sale (AGB), English and German. Prices, seller and contact come from src/landing/config.ts.
// Deliberately NOT here: a link to the EU ODR platform (the platform was shut down on 20 July 2025, Regulation
// (EU) 2024/3228), a VAT number (the MB is not VAT-registered), any promise the code does not keep.
// The latest delivery time is DELIVERY_MAX_HOURS (src/landing/config.ts). The "contract" section says how the contract
// text is kept: the order record in the bucket, and these terms plus the withdrawal information as text in the order
// confirmation email (src/legal/plain.ts builds them into /legal/order-mail.json for api/_lib/pay.py).
// The right of withdrawal ends when making the file begins, as the checkout's checkbox and api/_lib/withdraw.py have
// it (see src/shared/legal.ts); "delivery" and "withdrawal" below say so in the same words as the withdrawal page.
// Not reviewed by a lawyer.
import type { LegalDoc, LegalDocs } from '../types';
import { DELIVERY_MAX_HOURS, MAIL, MAX_EYES, PRICE_CENTS, SELLER, address, company, eur, phoneSuffix, representedSuffix } from '../facts';
import { WITHDRAWAL_ONLINE } from '../../shared/legal';

const TRANSPARENCY_EN = 'Colour from your own photo. Where your phone could not capture the finest fibres, our AI restores them.';
const TRANSPARENCY_DE = 'Die Farbe stammt aus Ihrem eigenen Foto. Wo Ihr Smartphone die feinsten Fasern nicht erfassen konnte, stellt unsere KI sie wieder her.';
const ART = 'Celestial Gold, Deep Nebula, Emerald Aurora, Obsidian Smoke, Supernova';
const PX = '4096\u00a0px';
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
      ],
    },
    {
      id: 'preview',
      title: 'Your preview and your file',
      blocks: [
        'Before you order, you see a free preview with a watermark and approve it. Your file follows the preview you approved: the same eye, style, layout and inscription, with the same colour and tone, rendered once in full resolution. At full size our AI adds the fine fibre detail that the preview is too small to show, so the very finest details can differ slightly from the preview.',
        'If your file clearly differs from the preview you approved (for example in colour, brightness or the pupil), that is a defect: see [Complaints and defects](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'How the contract is made',
      blocks: [
        'The previews and prices on our website are not yet a binding offer. Before you pay, you can check your eyes, style, layout and inscription and correct any input by going back or retaking a photo. You then open the payment page of our payment provider Stripe, where you enter your email address and payment details and can correct them. You place a binding order when you confirm the payment there with the pay button.',
        'The contract is concluded when your payment is confirmed. Your order page then opens, and we email you its link with your order confirmation. We start making your file there as soon as that email has gone out.',
        'The contract languages are English and German.',
        'We store your order with the details of the contract: the artwork you ordered, the price, the date, your email address and your consent to the immediate start. Your order page shows these details for as long as we keep your order. We do not keep a separate copy of these terms for each order. Instead, your order confirmation email contains, as text, your order details, these terms and the withdrawal information with the model withdrawal form, in the version in force when you ordered: please keep that email. You can also save or print this page at any time.',
      ],
    },
    {
      id: 'prices',
      title: 'Prices and payment',
      blocks: [
        {
          dl: [
            ['One eye, Studio Black', eur(PRICE_CENTS.studioBlack, 'en')],
            ['One eye with an art background', `${eur(PRICE_CENTS.artBackground, 'en')} (${ART})`],
            ['Two eyes (Couple Duo), any style', eur(PRICE_CENTS.coupleDuo, 'en')],
            ['Each further eye', `+${eur(PRICE_CENTS.extraEye, 'en')}, up to ${MAX_EYES} eyes on one artwork`],
          ],
        },
        'All prices are final prices in euros. We are not registered for VAT, so no VAT is charged or shown. There are no delivery costs.',
        'You pay in advance through our payment provider Stripe, with the payment methods shown on the payment page.',
      ],
    },
    {
      id: 'delivery',
      title: 'Delivery',
      blocks: [
        `Your order page makes your file as soon as your order confirmation email has gone out, which is normally right after your payment; this usually takes a few minutes (about half a minute per eye). If you close the page before your file is finished, it carries on when you open it again from the link in the email. If our automatic quality check flags a file, we look at it ourselves before we release it, and we email you when it is ready. **At the latest, your file is ready for download on your order page within ${DELIVERY_MAX_HOURS} hours after your payment is confirmed.** From your order page you can download your file at any time while we keep it: 12 months from your payment (see our [Privacy policy](doc:privacy)). Each download link it creates is valid for 7 days; the page makes a new one whenever you open it. If you lose the email, write to us.`,
        'The link to your order page contains a private key: anyone who has it can download your artwork, so please keep it to yourself. Please download your file and keep a copy. After 12 months it is deleted and cannot be restored.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Right of withdrawal',
      blocks: [
        `As a consumer you generally have a 14-day right of withdrawal. For a digital file it ends early: before you pay, we ask you to agree that we start making your file straight away, before the withdrawal period ends, and to confirm that you know you lose your right of withdrawal once we have started. It therefore ends as soon as we have started making your file (the performance of the contract); we start only after your order confirmation email has gone out. This applies even while the file is still being made or is waiting for our quality check. While your right of withdrawal lasts, you can withdraw by email, by post or online with the button "${WITHDRAWAL_ONLINE.en.button}". The full information, the online function and a model withdrawal form are on our [Right of withdrawal](doc:withdrawal) page.`,
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
      ],
    },
    {
      id: 'preview',
      title: 'Ihre Vorschau und Ihre Datei',
      blocks: [
        'Vor der Bestellung sehen Sie eine kostenlose Vorschau mit Wasserzeichen und geben sie frei. Ihre Datei folgt der freigegebenen Vorschau: dasselbe Auge, derselbe Stil, dieselbe Anordnung und Widmung, mit derselben Farbe und Tonalität, einmalig in voller Auflösung erstellt. In voller Größe ergänzt unsere KI die feinen Faserdetails, für die die Vorschau zu klein ist; die allerfeinsten Details können daher leicht von der Vorschau abweichen.',
        'Weicht Ihre Datei deutlich von der freigegebenen Vorschau ab (zum Beispiel in Farbe, Helligkeit oder bei der Pupille), ist das ein Mangel: siehe [Reklamationen und Mängel](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'Vertragsschluss',
      blocks: [
        'Die Vorschauen und Preise auf unserer Website sind noch kein verbindliches Angebot. Vor der Zahlung können Sie Ihre Augen, den Stil, die Anordnung und die Widmung prüfen und Eingaben korrigieren, indem Sie zurückgehen oder ein Foto neu aufnehmen. Danach öffnen Sie die Zahlungsseite unseres Zahlungsdienstleisters Stripe, auf der Sie Ihre E-Mail-Adresse und Zahlungsangaben eingeben und korrigieren können. Eine verbindliche Bestellung geben Sie ab, wenn Sie dort die Zahlung mit der Zahlungsschaltfläche bestätigen.',
        'Der Vertrag kommt zustande, sobald Ihre Zahlung bestätigt ist. Dann öffnet sich Ihre Bestellseite, und wir senden Ihnen deren Link mit Ihrer Bestellbestätigung per E-Mail. Sobald diese E-Mail versandt ist, beginnen wir dort mit Ihrer Datei.',
        'Vertragssprachen sind Deutsch und Englisch.',
        'Wir speichern Ihre Bestellung mit den Vertragsdaten: das bestellte Kunstwerk, den Preis, das Datum, Ihre E-Mail-Adresse und Ihre Zustimmung zum sofortigen Beginn. Ihre Bestellseite zeigt diese Angaben, solange wir Ihre Bestellung aufbewahren. Eine eigene Kopie dieser Bedingungen je Bestellung bewahren wir nicht auf. Stattdessen enthält Ihre Bestellbestätigung per E-Mail als Text Ihre Bestelldaten, diese Bedingungen und die Widerrufsbelehrung mit dem Muster-Widerrufsformular, in der bei Ihrer Bestellung gültigen Fassung: Bitte bewahren Sie diese E-Mail auf. Sie können diese Seite außerdem jederzeit speichern oder ausdrucken.',
      ],
    },
    {
      id: 'prices',
      title: 'Preise und Zahlung',
      blocks: [
        {
          dl: [
            ['Ein Auge, Studio Black', eur(PRICE_CENTS.studioBlack, 'de')],
            ['Ein Auge mit Kunsthintergrund', `${eur(PRICE_CENTS.artBackground, 'de')} (${ART})`],
            ['Zwei Augen (Couple Duo), jeder Stil', eur(PRICE_CENTS.coupleDuo, 'de')],
            ['Jedes weitere Auge', `+${eur(PRICE_CENTS.extraEye, 'de')}, bis zu ${MAX_EYES} Augen auf einem Kunstwerk`],
          ],
        },
        'Alle Preise sind Endpreise in Euro. Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet oder ausgewiesen. Versandkosten fallen nicht an.',
        'Sie zahlen im Voraus über unseren Zahlungsdienstleister Stripe, mit den auf der Zahlungsseite angezeigten Zahlungsarten.',
      ],
    },
    {
      id: 'delivery',
      title: 'Lieferung',
      blocks: [
        `Ihre Bestellseite erstellt Ihre Datei, sobald Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise direkt nach der Zahlung; das dauert meist wenige Minuten (etwa eine halbe Minute pro Auge). Schließen Sie die Seite, bevor Ihre Datei fertig ist, macht sie weiter, wenn Sie sie über den Link in der E-Mail wieder öffnen. Meldet unsere automatische Qualitätsprüfung eine Datei, sehen wir sie uns vor der Freigabe selbst an und benachrichtigen Sie per E-Mail, sobald sie fertig ist. **Spätestens ${DELIVERY_MAX_HOURS} Stunden nach der Bestätigung Ihrer Zahlung steht Ihre Datei auf Ihrer Bestellseite zum Download bereit.** Über Ihre Bestellseite können Sie Ihre Datei jederzeit herunterladen, solange wir sie aufbewahren: 12 Monate ab Ihrer Zahlung (siehe [Datenschutzerklärung](doc:privacy)). Jeder Download-Link, den die Seite erzeugt, ist 7 Tage gültig; beim nächsten Öffnen erzeugt sie einen neuen. Haben Sie die E-Mail verloren, schreiben Sie uns.`,
        'Der Link zu Ihrer Bestellseite enthält einen privaten Schlüssel: Jede Person, die ihn hat, kann Ihr Kunstwerk herunterladen. Bitte geben Sie ihn nicht weiter. Laden Sie Ihre Datei herunter und bewahren Sie eine Kopie auf. Nach 12 Monaten wird sie gelöscht und kann nicht wiederhergestellt werden.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Widerrufsrecht',
      blocks: [
        `Als Verbraucher haben Sie grundsätzlich ein 14-tägiges Widerrufsrecht. Bei einer digitalen Datei erlischt es vorzeitig: Vor der Zahlung bitten wir Sie, zuzustimmen, dass wir sofort, vor Ablauf der Widerrufsfrist, mit der Erstellung Ihrer Datei beginnen, und zu bestätigen, dass Ihnen bekannt ist, dass Sie dadurch Ihr Widerrufsrecht verlieren, sobald damit begonnen wurde. Es erlischt daher, sobald wir mit der Erstellung Ihrer Datei (der Vertragserfüllung) begonnen haben; damit beginnen wir erst, nachdem Ihre Bestellbestätigung per E-Mail versandt ist. Das gilt auch, solange die Datei noch erstellt wird oder auf unsere Qualitätsprüfung wartet. Solange Ihr Widerrufsrecht besteht, können Sie per E-Mail, per Post oder online mit der Schaltfläche „${WITHDRAWAL_ONLINE.de.button}“ widerrufen. Alle Einzelheiten, die Online-Funktion und ein Muster-Widerrufsformular finden Sie in unserer [Widerrufsbelehrung](doc:withdrawal).`,
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

export const TERMS: LegalDocs = { en, de };
