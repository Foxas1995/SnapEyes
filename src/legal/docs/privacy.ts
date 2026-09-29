// Privacy policy (GDPR Art. 13), English and German. Written from what the code really does on 2026-09-29:
//  - free previews: api/analyze, deglare, enhance, compose work in memory and store nothing (the /try
//    "training memory" opt-in only appears when BLOB_READ_WRITE_TOKEN is set; it is off live and must stay off,
//    or the "never used to train AI" promise below becomes false)
//  - capture telemetry: the "snapeyes capture" / "snapeyes shake" log lines of api/analyze.py, no image
//  - orders (api/order.py, api/_lib/pay.py): starting an order uploads, per eye, the deglared iris crop and the
//    approved preview to orders/<order>/draft/ in the private Supabase bucket (the full phone photo never leaves
//    the browser whole); paid.json holds the email, amount and consent; the 4K eyes, the artwork and small json
//    records follow (master_eye, master_compose). The emailed order page link carries the access key and makes
//    7-day signed download links (store.SIGNED_MAX). Emails go through Resend (pay.send_mail).
//  - NOT automated yet, but promised below: deleting unpaid drafts within 30 days and paid orders after 12 months
//  - browser storage: only localStorage "snapeyes.lang" (src/landing/lang.tsx); no cookies, no analytics
// Not reviewed by a lawyer. Keep every sentence true when the code or a service changes.
import type { LegalDoc, LegalDocs } from '../types';
import { ORDER_EMAIL_SENDER } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';

const rep = (label: string) => (SELLER.representative ? ` ${label} ${SELLER.representative}.` : '');
const senderEn = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: sending the emails about your order (the link to your order page and the confirmation). Its servers may be outside the EU.`];
const senderDe = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: Versand der E-Mails zu Ihrer Bestellung (Link zu Ihrer Bestellseite und Bestätigung). Die Server können außerhalb der EU liegen.`];
const hostingerEn = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: our email, the mailbox info@snapeyes.com, including the emails about your order.'
  : 'Hostinger: our mailbox info@snapeyes.com.';
const hostingerDe = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: unsere E-Mail, das Postfach info@snapeyes.com, einschließlich der E-Mails zu Ihrer Bestellung.'
  : 'Hostinger: unser Postfach info@snapeyes.com.';

const en: LegalDoc = {
  title: 'Privacy policy',
  description:
    'How SnapEyes handles your eye photo, your preview and, when you order, your order data: what we process, why, with which services, for how long, and your rights.',
  lead:
    'This policy explains what happens to your data when you use snapeyes.com: the free preview and, when you order, your digital artwork. In short: your photo is used only to make your artwork, never to identify anyone and never to train AI. We do not store free previews. Paid orders are kept for 12 months so you can download your file again, then deleted.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Who is responsible',
      blocks: [
        `The controller for your data is ${company('en')} (company code ${SELLER.code}), ${address('en')}. SnapEyes is its brand.${rep('It is represented by')}`,
        `For every privacy question, and to use any of your rights, write to ${MAIL}. We have not appointed a data protection officer.`,
      ],
    },
    {
      id: 'website',
      title: 'When you visit the website',
      blocks: [
        'When you open a page of snapeyes.com, your browser sends technical data to our hosting provider Vercel, such as your IP address, the date and time, the page requested and your browser type (user agent). Vercel needs this data to deliver the page and to protect the service against attacks. It is kept in server logs for a short time and then deleted.',
        'Legal basis: our legitimate interest in a secure, working website (Art. 6(1)(f) GDPR).',
        'Our fonts are served from our own server, so no data goes to Google Fonts or any other font service. We do not use analytics, advertising or tracking tools on this website.',
      ],
    },
    {
      id: 'preview',
      title: 'Your free preview',
      blocks: [
        "To make your preview, you send one or more photos of an eye from your browser to our server functions. There the photo is processed in memory: we find the iris, cut it out, check whether it is sharp and bright enough, remove reflections, restore the fine fibres with Google's Gemini API and set the iris in the styles you see. The result goes back to your browser. Every transfer is encrypted (HTTPS).",
        '**We do not store your photo, the iris crop or the preview on our servers.** They are discarded when the request ends. The preview stays in your browser until you close the page, unless you save it yourself. Only when you start an order do we keep the iris crop and the preview you approved: see [When you order](#orders).',
        "Google processes the image to make the restoration. We use Google's paid API service, under whose terms Google does not use the images to improve its products or to train its models. Google may keep requests for a limited period, solely to detect misuse and for disclosures the law requires.",
        'Legal basis: you ask us to make your preview, and the photo is needed for it (Art. 6(1)(b) GDPR, steps taken at your request).',
        'Our software decides automatically whether a photo can be used (for example when it is too blurry or too dark). This decision has no legal or similarly significant effect on you: you can simply take another photo.',
      ],
    },
    {
      id: 'iris',
      title: 'Your iris is never used to identify anyone',
      blocks: [
        "An iris can, in principle, be used to recognise a person. We do not do that. We never create, compare or store an iris template or any other biometric identifier, we never use your images to identify or verify anyone, we never sell them, and we never use them to train AI, neither our own nor anyone else's.",
        'Please only use your own eye, or the eye of someone who has agreed to it. For a child, a parent or guardian must agree.',
      ],
    },
    {
      id: 'measurements',
      title: 'Technical measurements (no images)',
      blocks: [
        'With each photo, our server writes one line to its logs so that we can improve the capture guide and the quality of the service. It holds measurements of the photo (for example the size of the iris in pixels, sharpness, brightness, a colour cast of the light and whether the photo could be used), technical facts about your device (browser type and version, screen size, whether the photo came from the camera or the gallery) and, if you answer our optional questions about a shot, your answers. It holds no image, no name and no contact details.',
        'These log lines are kept by our hosting provider for a short time and then deleted. Legal basis: our legitimate interest in improving the service (Art. 6(1)(f) GDPR). You may object at any time (see [Your rights](#rights)).',
      ],
    },
    {
      id: 'orders',
      title: 'When you order',
      blocks: [
        'When you start an order, two images of each eye are uploaded to our private storage, so that your file is made from exactly what you saw: the square around your iris cut from your photo (with reflections removed) and the preview you approved. **Your full phone photo is not stored, not even for an order.** An order that is not paid within 24 hours can no longer be paid; its images are then deleted within 30 days.',
        'To sell and deliver your artwork, we process: the order (order number, date, eyes, style, layout, any names or inscription you add, language, price), your email address (you enter it on the payment page), the payment status we receive from Stripe, your consent to the immediate start (see [Right of withdrawal](doc:withdrawal)), and the files of your order: the two images of each eye named above, the 4096\u00a0px rendering of each eye and the finished artwork, with technical quality records.',
        'We keep these files in a private storage bucket at Supabase, located in the EU. You reach them through your order page, whose link we email to you; it contains a private key, so anyone with the link can download your artwork. Each download link it creates expires after 7 days.',
        'We may look at the files of your order to check their quality, for example when our automatic check reports a difference from the preview you approved.',
        'Legal basis: the contract with you (Art. 6(1)(b) GDPR); for accounting records, our legal obligations (Art. 6(1)(c) GDPR).',
        'Payment: Stripe processes your payment. We never see your full card number. Stripe also processes payment data under its own privacy policy, for fraud prevention and for its own legal duties.',
        'We need your email address to send you the link to your order page and the order confirmation. Without it you could lose access to your file.',
      ],
    },
    {
      id: 'email',
      title: 'When you write to us',
      blocks: [
        'If you email us, we use your address and your message to answer you and, where it concerns an order, to handle that order. Legal basis: Art. 6(1)(b) GDPR for orders, otherwise our legitimate interest in answering you (Art. 6(1)(f) GDPR). We keep your emails for as long as we need them for your request and any follow-up.',
      ],
    },
    {
      id: 'services',
      title: 'Services we use',
      blocks: [
        'We use these services to run SnapEyes:',
        {
          ul: [
            "Vercel: hosting of the website and of the server functions that make your preview and your file. Vercel's data centres may be outside the EU, for example in the USA.",
            "Google (Gemini API): the AI restoration of the iris and the checks of your photo. Google's servers may be outside the EU.",
            'Supabase: private storage of the files of orders, in an EU region.',
            'Stripe: payment processing.',
            hostingerEn,
            ...senderEn,
          ],
        },
        'These providers process your data on our behalf and on our instructions (Stripe partly as an independent controller, see [When you order](#orders)). Where data is transferred outside the EU or EEA, this happens under the safeguards the providers offer, such as the European Commission\'s standard contractual clauses or the EU-US Data Privacy Framework.',
        'We do not sell your data and we do not pass it on to anyone else, unless the law obliges us to.',
      ],
    },
    {
      id: 'retention',
      title: 'How long we keep your data',
      blocks: [
        {
          dl: [
            ['Free previews', 'Not stored by us. They are discarded when the request ends.'],
            ['Unpaid orders', 'An order that is not paid within 24 hours can no longer be paid; its images are deleted within 30 days.'],
            ['Paid orders', 'The files of your order are kept for 12 months from the order, so that you can download them again from your order page, and then deleted. On request we delete them earlier; after that your order page can no longer deliver the file.'],
            ['Accounting records', 'Records the law obliges us to keep (such as the date, price and payment of an order; no images) are kept for as long as Lithuanian accounting and tax law requires.'],
            ['Server logs and measurements', 'Kept by our hosting provider for a short time, then deleted.'],
            ['Emails', 'For as long as we need them for your request and any follow-up.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Your rights',
      blocks: [
        'You have these rights at any time:',
        {
          ul: [
            'Access: to learn which data we hold about you and to receive a copy (Art. 15 GDPR).',
            'Rectification: to have wrong data corrected (Art. 16 GDPR).',
            'Erasure: to have your data deleted, for example the files of your order before the 12 months are over (Art. 17 GDPR).',
            'Restriction: to have the processing limited while a question is being clarified (Art. 18 GDPR).',
            'Data portability: to receive the data you gave us in a common, machine-readable format (Art. 20 GDPR).',
            'Objection: to object at any time, on grounds relating to your particular situation, to processing based on our legitimate interests (Art. 21 GDPR).',
          ],
        },
        `To use any of these rights, write to ${MAIL}. We answer within one month.`,
        'You also have the right to lodge a complaint with a supervisory authority. Ours is the Lithuanian State Data Protection Inspectorate (Valstybinė duomenų apsaugos inspekcija, VDAI) in Vilnius, [vdai.lrv.lt](https://vdai.lrv.lt). You can also turn to the authority of the EU country where you live or work.',
      ],
    },
    {
      id: 'storage',
      title: 'Cookies and local storage',
      blocks: [
        'This website sets no cookies. It uses no analytics, advertising or tracking tools.',
        'When you choose a language with the EN/DE switch, your browser remembers the choice in its local storage under the key "snapeyes.lang" (the value "en" or "de"). It is never sent to us, and you can delete it at any time in your browser settings. It is strictly necessary for a function you asked for, so it needs no consent (Art. 5(3) ePrivacy Directive).',
        "When you pay, Stripe's payment page may use its own cookies that are needed for secure payment and fraud prevention; Stripe's own privacy and cookie policy applies there.",
      ],
    },
    {
      id: 'required',
      title: 'Do you have to give us data?',
      blocks: ['No. But without a photo we cannot make a preview, and without an email address and payment we cannot deliver an order.'],
    },
    {
      id: 'changes',
      title: 'Changes to this policy',
      blocks: ['We update this policy when our service or the law changes. The date at the top shows the current version.'],
    },
  ],
};

const de: LegalDoc = {
  title: 'Datenschutz\u00ADerklärung',
  description:
    'Wie SnapEyes mit Ihrem Augenfoto, Ihrer Vorschau und bei Bestellungen mit Ihren Bestelldaten umgeht: was wir verarbeiten, warum, mit welchen Diensten, wie lange, und welche Rechte Sie haben.',
  lead:
    'Diese Erklärung beschreibt, was mit Ihren Daten geschieht, wenn Sie snapeyes.com nutzen: die kostenlose Vorschau und, wenn Sie bestellen, Ihr digitales Kunstwerk. Kurz gesagt: Ihr Foto dient nur dazu, Ihr Kunstwerk zu erstellen, nie dazu, jemanden zu identifizieren, und nie zum Training von KI. Kostenlose Vorschauen speichern wir nicht. Bezahlte Bestellungen bewahren wir 12 Monate auf, damit Sie Ihre Datei erneut herunterladen können, danach werden sie gelöscht.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Verantwortlicher',
      blocks: [
        `Verantwortlich für Ihre Daten ist ${company('de')} (Unternehmenscode ${SELLER.code}), ${address('de')}. SnapEyes ist eine Marke dieses Unternehmens.${rep('Vertreten durch')}`,
        `Für alle Fragen zum Datenschutz und um Ihre Rechte auszuüben, schreiben Sie an ${MAIL}. Einen Datenschutzbeauftragten haben wir nicht benannt.`,
      ],
    },
    {
      id: 'website',
      title: 'Beim Besuch der Website',
      blocks: [
        'Wenn Sie eine Seite von snapeyes.com aufrufen, sendet Ihr Browser technische Daten an unseren Hosting-Anbieter Vercel, etwa Ihre IP-Adresse, Datum und Uhrzeit, die aufgerufene Seite und Ihren Browsertyp (User-Agent). Vercel braucht diese Daten, um die Seite auszuliefern und den Dienst vor Angriffen zu schützen. Sie werden für kurze Zeit in Server-Protokollen gespeichert und dann gelöscht.',
        'Rechtsgrundlage: unser berechtigtes Interesse an einer sicheren, funktionierenden Website (Art. 6 Abs. 1 lit. f DSGVO).',
        'Unsere Schriftarten kommen von unserem eigenen Server, es werden also keine Daten an Google Fonts oder andere Schriftdienste übertragen. Wir setzen auf dieser Website keine Analyse-, Werbe- oder Tracking-Werkzeuge ein.',
      ],
    },
    {
      id: 'preview',
      title: 'Ihre kostenlose Vorschau',
      blocks: [
        'Für Ihre Vorschau senden Sie ein oder mehrere Fotos eines Auges aus Ihrem Browser an unsere Server-Funktionen. Dort wird das Foto im Arbeitsspeicher verarbeitet: Wir finden die Iris, schneiden sie aus, prüfen, ob sie scharf und hell genug ist, entfernen Reflexionen, stellen die feinen Fasern mit der Gemini API von Google wieder her und setzen die Iris in die Stile, die Sie sehen. Das Ergebnis geht an Ihren Browser zurück. Jede Übertragung ist verschlüsselt (HTTPS).',
        '**Ihr Foto, den Iris-Ausschnitt und die Vorschau speichern wir nicht auf unseren Servern.** Sie werden verworfen, sobald die Anfrage abgeschlossen ist. Die Vorschau bleibt in Ihrem Browser, bis Sie die Seite schließen, es sei denn, Sie speichern sie selbst. Nur wenn Sie eine Bestellung beginnen, bewahren wir den Iris-Ausschnitt und die freigegebene Vorschau auf: siehe [Wenn Sie bestellen](#orders).',
        'Google verarbeitet das Bild, um die Restaurierung zu erstellen. Wir nutzen den kostenpflichtigen API-Dienst von Google; nach dessen Bedingungen verwendet Google die Bilder weder zur Verbesserung seiner Produkte noch zum Training seiner Modelle. Google kann Anfragen für begrenzte Zeit speichern, ausschließlich um Missbrauch zu erkennen und gesetzlich vorgeschriebene Offenlegungen zu erfüllen.',
        'Rechtsgrundlage: Sie bitten uns, Ihre Vorschau zu erstellen, und dafür wird das Foto benötigt (Art. 6 Abs. 1 lit. b DSGVO, Maßnahmen auf Ihre Anfrage).',
        'Unsere Software entscheidet automatisch, ob ein Foto verwendbar ist (zum Beispiel, wenn es zu unscharf oder zu dunkel ist). Diese Entscheidung hat für Sie keine rechtliche oder ähnlich erhebliche Wirkung: Sie können einfach ein neues Foto aufnehmen.',
      ],
    },
    {
      id: 'iris',
      title: 'Ihre Iris dient nie zur Identifizierung',
      blocks: [
        'Eine Iris kann grundsätzlich dazu dienen, einen Menschen wiederzuerkennen. Das tun wir nicht. Wir erstellen, vergleichen oder speichern keine Iris-Merkmalsvorlage und keine anderen biometrischen Kennungen, wir nutzen Ihre Bilder nie, um jemanden zu identifizieren oder zu verifizieren, wir verkaufen sie nie, und wir verwenden sie nie zum Training von KI, weder unserer eigenen noch der anderer.',
        'Bitte verwenden Sie nur Ihr eigenes Auge oder das Auge einer Person, die damit einverstanden ist. Bei einem Kind muss ein Elternteil oder eine sorgeberechtigte Person einverstanden sein.',
      ],
    },
    {
      id: 'measurements',
      title: 'Technische Messwerte (ohne Bilder)',
      blocks: [
        'Zu jedem Foto schreibt unser Server eine Zeile in seine Protokolle, damit wir die Aufnahmeanleitung und die Qualität des Dienstes verbessern können. Sie enthält Messwerte des Fotos (zum Beispiel die Größe der Iris in Pixeln, Schärfe, Helligkeit, einen Farbstich des Lichts und ob das Foto verwendbar war), technische Angaben zu Ihrem Gerät (Browsertyp und -version, Bildschirmgröße, ob das Foto von der Kamera oder aus der Galerie stammt) und, falls Sie unsere freiwilligen Fragen zu einer Aufnahme beantworten, Ihre Antworten. Sie enthält kein Bild, keinen Namen und keine Kontaktdaten.',
        'Diese Protokollzeilen werden bei unserem Hosting-Anbieter für kurze Zeit gespeichert und dann gelöscht. Rechtsgrundlage: unser berechtigtes Interesse an der Verbesserung des Dienstes (Art. 6 Abs. 1 lit. f DSGVO). Sie können jederzeit widersprechen (siehe [Ihre Rechte](#rights)).',
      ],
    },
    {
      id: 'orders',
      title: 'Wenn Sie bestellen',
      blocks: [
        'Wenn Sie eine Bestellung beginnen, werden von jedem Auge zwei Bilder in unseren privaten Speicher hochgeladen, damit Ihre Datei genau aus dem entsteht, was Sie gesehen haben: das Quadrat um Ihre Iris, aus Ihrem Foto ausgeschnitten (ohne Reflexionen), und die von Ihnen freigegebene Vorschau. **Ihr vollständiges Smartphone-Foto wird nicht gespeichert, auch nicht bei einer Bestellung.** Eine Bestellung, die nicht innerhalb von 24 Stunden bezahlt wird, kann nicht mehr bezahlt werden; ihre Bilder werden dann innerhalb von 30 Tagen gelöscht.',
        'Um Ihr Kunstwerk zu verkaufen und zu liefern, verarbeiten wir: die Bestellung (Bestellnummer, Datum, Augen, Stil, Anordnung, von Ihnen eingegebene Namen oder Widmung, Sprache, Preis), Ihre E-Mail-Adresse (Sie geben sie auf der Zahlungsseite ein), den Zahlungsstatus, den wir von Stripe erhalten, Ihre Zustimmung zum sofortigen Beginn (siehe [Widerrufsbelehrung](doc:withdrawal)) und die Dateien Ihrer Bestellung: die beiden oben genannten Bilder jedes Auges, die 4096-px-Fassung jedes Auges und das fertige Kunstwerk, mit technischen Qualitätsprotokollen.',
        'Diese Dateien bewahren wir in einem privaten Speicher bei Supabase in der EU auf. Sie erreichen sie über Ihre Bestellseite, deren Link wir Ihnen per E-Mail senden; er enthält einen privaten Schlüssel, daher kann jede Person mit diesem Link Ihr Kunstwerk herunterladen. Jeder Download-Link, den die Seite erzeugt, läuft nach 7 Tagen ab.',
        'Wir können die Dateien Ihrer Bestellung ansehen, um ihre Qualität zu prüfen, etwa wenn unsere automatische Prüfung eine Abweichung von der freigegebenen Vorschau meldet.',
        'Rechtsgrundlage: der Vertrag mit Ihnen (Art. 6 Abs. 1 lit. b DSGVO); für Buchhaltungsunterlagen unsere gesetzlichen Pflichten (Art. 6 Abs. 1 lit. c DSGVO).',
        'Zahlung: Stripe wickelt Ihre Zahlung ab. Ihre vollständige Kartennummer sehen wir nie. Stripe verarbeitet Zahlungsdaten außerdem nach seiner eigenen Datenschutzerklärung, zur Betrugsvorbeugung und für seine eigenen gesetzlichen Pflichten.',
        'Ihre E-Mail-Adresse brauchen wir, um Ihnen den Link zu Ihrer Bestellseite und die Bestellbestätigung zu senden. Ohne sie könnten Sie den Zugang zu Ihrer Datei verlieren.',
      ],
    },
    {
      id: 'email',
      title: 'Wenn Sie uns schreiben',
      blocks: [
        'Wenn Sie uns eine E-Mail senden, nutzen wir Ihre Adresse und Ihre Nachricht, um Ihnen zu antworten und, falls es um eine Bestellung geht, diese abzuwickeln. Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO bei Bestellungen, sonst unser berechtigtes Interesse, Ihnen zu antworten (Art. 6 Abs. 1 lit. f DSGVO). Wir bewahren Ihre E-Mails so lange auf, wie wir sie für Ihr Anliegen und etwaige Rückfragen brauchen.',
      ],
    },
    {
      id: 'services',
      title: 'Dienste, die wir nutzen',
      blocks: [
        'Für den Betrieb von SnapEyes nutzen wir diese Dienste:',
        {
          ul: [
            'Vercel: Hosting der Website und der Server-Funktionen, die Ihre Vorschau und Ihre Datei erstellen. Die Rechenzentren von Vercel können außerhalb der EU liegen, zum Beispiel in den USA.',
            'Google (Gemini API): die KI-Restaurierung der Iris und die Prüfung Ihres Fotos. Die Server von Google können außerhalb der EU liegen.',
            'Supabase: privater Speicher für die Dateien von Bestellungen, in einer EU-Region.',
            'Stripe: Zahlungsabwicklung.',
            hostingerDe,
            ...senderDe,
          ],
        },
        'Diese Anbieter verarbeiten Ihre Daten in unserem Auftrag und nach unseren Weisungen (Stripe teilweise als eigenständig Verantwortlicher, siehe [Wenn Sie bestellen](#orders)). Werden Daten außerhalb der EU oder des EWR übermittelt, geschieht dies auf Grundlage der Garantien, die die Anbieter bieten, etwa der Standardvertragsklauseln der EU-Kommission oder des EU-US Data Privacy Framework.',
        'Wir verkaufen Ihre Daten nicht und geben sie an niemanden sonst weiter, es sei denn, wir sind gesetzlich dazu verpflichtet.',
      ],
    },
    {
      id: 'retention',
      title: 'Wie lange wir Ihre Daten speichern',
      blocks: [
        {
          dl: [
            ['Kostenlose Vorschauen', 'Werden von uns nicht gespeichert. Sie werden verworfen, sobald die Anfrage abgeschlossen ist.'],
            ['Unbezahlte Bestellungen', 'Eine Bestellung, die nicht innerhalb von 24 Stunden bezahlt wird, kann nicht mehr bezahlt werden; ihre Bilder werden innerhalb von 30 Tagen gelöscht.'],
            ['Bezahlte Bestellungen', 'Die Dateien Ihrer Bestellung bewahren wir 12 Monate ab der Bestellung auf, damit Sie sie über Ihre Bestellseite erneut herunterladen können, und löschen sie danach. Auf Wunsch löschen wir sie früher; danach kann Ihre Bestellseite die Datei nicht mehr liefern.'],
            ['Buchhaltungsunterlagen', 'Unterlagen, die wir gesetzlich aufbewahren müssen (etwa Datum, Preis und Zahlung einer Bestellung; keine Bilder), bewahren wir so lange auf, wie es das litauische Buchführungs- und Steuerrecht verlangt.'],
            ['Server-Protokolle und Messwerte', 'Werden bei unserem Hosting-Anbieter für kurze Zeit gespeichert und dann gelöscht.'],
            ['E-Mails', 'So lange, wie wir sie für Ihr Anliegen und etwaige Rückfragen brauchen.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Ihre Rechte',
      blocks: [
        'Sie haben jederzeit folgende Rechte:',
        {
          ul: [
            'Auskunft: zu erfahren, welche Daten wir über Sie gespeichert haben, und eine Kopie zu erhalten (Art. 15 DSGVO).',
            'Berichtigung: falsche Daten korrigieren zu lassen (Art. 16 DSGVO).',
            'Löschung: Ihre Daten löschen zu lassen, zum Beispiel die Dateien Ihrer Bestellung vor Ablauf der 12 Monate (Art. 17 DSGVO).',
            'Einschränkung: die Verarbeitung einschränken zu lassen, solange eine Frage geklärt wird (Art. 18 DSGVO).',
            'Datenübertragbarkeit: die Daten, die Sie uns gegeben haben, in einem gängigen, maschinenlesbaren Format zu erhalten (Art. 20 DSGVO).',
            'Widerspruch: einer Verarbeitung auf Grundlage unserer berechtigten Interessen jederzeit aus Gründen, die sich aus Ihrer besonderen Situation ergeben, zu widersprechen (Art. 21 DSGVO).',
          ],
        },
        `Um eines dieser Rechte auszuüben, schreiben Sie an ${MAIL}. Wir antworten innerhalb eines Monats.`,
        'Sie haben außerdem das Recht, sich bei einer Datenschutz-Aufsichtsbehörde zu beschweren. Für uns zuständig ist die litauische Staatliche Datenschutzinspektion (Valstybinė duomenų apsaugos inspekcija, VDAI) in Vilnius, [vdai.lrv.lt](https://vdai.lrv.lt). Sie können sich auch an die Aufsichtsbehörde des EU-Landes wenden, in dem Sie leben oder arbeiten.',
      ],
    },
    {
      id: 'storage',
      title: 'Cookies und lokaler Speicher',
      blocks: [
        'Diese Website setzt keine Cookies. Sie nutzt keine Analyse-, Werbe- oder Tracking-Werkzeuge.',
        'Wenn Sie mit dem Schalter EN/DE eine Sprache wählen, merkt sich Ihr Browser diese Wahl in seinem lokalen Speicher unter dem Schlüssel „snapeyes.lang“ (Wert „en“ oder „de“). Dieser Eintrag wird nie an uns übertragen, und Sie können ihn jederzeit in Ihren Browsereinstellungen löschen. Er ist für eine von Ihnen gewünschte Funktion unbedingt erforderlich und braucht daher keine Einwilligung (§ 25 Abs. 2 Nr. 2 TDDDG, Art. 5 Abs. 3 ePrivacy-Richtlinie).',
        'Wenn Sie bezahlen, kann die Zahlungsseite von Stripe eigene Cookies verwenden, die für eine sichere Zahlung und zur Betrugsvorbeugung nötig sind; dort gilt die Datenschutz- und Cookie-Richtlinie von Stripe.',
      ],
    },
    {
      id: 'required',
      title: 'Müssen Sie uns Daten geben?',
      blocks: ['Nein. Ohne Foto können wir aber keine Vorschau erstellen, und ohne E-Mail-Adresse und Zahlung keine Bestellung liefern.'],
    },
    {
      id: 'changes',
      title: 'Änderungen dieser Erklärung',
      blocks: ['Wir passen diese Erklärung an, wenn sich unser Dienst oder die Rechtslage ändert. Das Datum oben zeigt die aktuelle Fassung.'],
    },
  ],
};

export const PRIVACY: LegalDocs = { en, de };
