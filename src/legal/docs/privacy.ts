// Privacy policy (GDPR Art. 13), English and German. Written from what the code really does on 2026-09-29:
//  - free previews: api/analyze, deglare, enhance, compose work in memory and store nothing (the /try
//    "training memory" opt-in only appears when BLOB_READ_WRITE_TOKEN is set; it is off live and must stay off,
//    or the "never used to train AI" promise below becomes false)
//  - capture telemetry: the "snapeyes capture" / "snapeyes shake" log lines of api/analyze.py, no image
//  - the admin panel's usage events (api/_lib/events.py, ops/events/ and ops/daily/, 12 months) and its admin log
//    (api/_lib/ops.py): the "operations" section, see OPS and ADMIN_LOG below
//  - orders (api/order.py, api/_lib/pay.py): starting an order uploads, per eye, the deglared iris crop and the
//    approved preview to orders/<order>/draft/ in the private Supabase bucket (the full phone photo never leaves
//    the browser whole); paid.json holds the email, amount and consent; the 4K eyes, the artwork and small json
//    records follow (master_eye, master_compose). The emailed order page link carries the access key and makes
//    7-day signed download links (store.SIGNED_MAX). Emails go through Resend (pay.send_mail).
//  - Stripe: create_session puts the order spec into the Checkout Session metadata (order, eyes, style, layout,
//    names, title, lang, amount, consent version and time), so names and inscription reach Stripe
//  - upload markers outside the order folders: ticketuse/ and draftlog/ (no image), removed after MARKER_DAYS
//  - deletion: the daily clean-up (GET /api/order?cron=purge, vercel.json crons + CRON_SECRET; pay.purge_unpaid)
//    (api/_lib/cleanup.py) deletes unpaid orders older than 26 h (the policy promises "at the latest within 30 days"),
//    the images of withdrawn orders 14 days after the withdrawal, and the files of paid orders 12 months after
//    payment; the records stay (order.json, paid.json: email, spec with names, consent; withdrawal statements)
//  - withdrawals (api/_lib/withdraw.py): the statement (name, email, order, text, time, outcome) is stored with the
//    order; one that matches no order (without the link key, the email must be the paid one) goes to withdrawals/,
//    gets the neutral receipt email (withdraw.unmatched_mail, within withdraw._receipt_to's limits) and
//    is deleted by the daily clean-up with its month once UNMATCHED_KEEP_DAYS = 396 days have passed since the month
//    ended ("about 13 months"); the owner is emailed every statement (unmatched and never-paid ones in the daily
//    digest); withdrawlog/ counters (a few days) and withdrawaddr/<yymm>/ monthly receipt counters (withdraw.
//    purge_addr_marks: about 40 days after their month) hold no name or address, the receipt counters a short hash of the address
//  - withdrawn orders: cleanup/withdrawn/ is written only for an EFFECTIVE withdrawal; its images go at the first
//    daily run 14 days after it (an order whose payment is still settling waits for Stripe)
//  - the market (src/shared/markets.ts): localStorage "snapeyes.market" when a link named a market other than the
//    default one or the currency switch chose one, and "eu" when the visitor declined the landing page's offer of
//    their own currency (src/landing/MarketHint.tsx; m= in the site's links, "market" in the checkout request); GET
//    /api/checkout reads Vercel's x-vercel-ip-country and answers it with a suggested market (api/checkout.py
//    country_hint), stored nowhere, only offered
//  - browser storage: localStorage "snapeyes.lang" (src/landing/lang.tsx, src/try/lang.ts) and, in the order flow,
//    sessionStorage "snapeyes.order" and "snapeyes.checkout" (src/try/checkout.ts); no cookies, no analytics
//  - the online withdrawal function: see WITHDRAWAL_ONLINE in src/shared/legal.ts and the "withdrawal" section
// PRIVACY_AU (the end of this file) is the Australian edition (src/shared/legal.ts legalEdition "au"): the same policy
// with a section for people in Australia (eye photos as possible biometric information, never used to identify
// anyone; data processed outside Australia; the Australian Privacy Principles and the small business exemption as they
// stand; the statutory privacy tort since 10 June 2025; the OAIC).
// Not reviewed by a lawyer. Keep every sentence true when the code or a service changes.
import type { EditionDocs, LegalDoc, LegalDocs } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';
import { patchDoc } from '../patch';
import { lt } from './privacy.lt';
import { hu } from './privacy.hu';

// What the online withdrawal function keeps (the "withdrawal" section): keep it in step with the order page's form
// and the API action behind it.
const WITHDRAW_PRIVACY = {
  en: `If you withdraw from an order with our online function (the button "${WITHDRAWAL_ONLINE.en.button}", see [Right of withdrawal](doc:withdrawal#online)), we store your withdrawal statement with your order: your name, your email address, the order number, its wording and the date and time it reached us. We use it to stop work on your file if we have not started yet, to email you an acknowledgement of receipt with its content, date and time, and to refund you. We also receive every statement by email: one by one, or, for statements that match none of our orders and those about orders that were never paid, in one summary a day. If your withdrawal takes effect, the images of your order are deleted automatically by our daily clean-up once 14 days have passed since your withdrawal (if your payment was still being processed, only once it has been settled); the order record with your statement stays (see [How long we keep your data](#retention)). If the details you give match none of our orders (without the link from your order page or the withdrawal link in your order confirmation email, the email address must be the one you paid with), we keep the statement separately, check it by hand, email you an acknowledgement of receipt all the same (within the limits against misuse set out under [Withdraw online](doc:withdrawal#online)) and delete it automatically about 13 months after the end of the month in which it reached us.`,
  de: `Wenn Sie eine Bestellung mit unserer Online-Funktion widerrufen (Schaltfläche „${WITHDRAWAL_ONLINE.de.button}“, siehe [Widerrufsbelehrung](doc:withdrawal#online)), speichern wir Ihre Widerrufserklärung bei Ihrer Bestellung: Ihren Namen, Ihre E-Mail-Adresse, die Bestellnummer, ihren Wortlaut sowie Datum und Uhrzeit ihres Eingangs. Wir verwenden sie, um die Arbeit an Ihrer Datei anzuhalten, falls wir noch nicht begonnen haben, um Ihnen eine Eingangsbestätigung mit Inhalt, Datum und Uhrzeit per E-Mail zu senden und um Ihnen den Preis zu erstatten. Jede Erklärung erhalten wir außerdem per E-Mail: einzeln oder, bei Erklärungen, die zu keiner unserer Bestellungen passen, und bei solchen zu nie bezahlten Bestellungen, in einer Zusammenfassung pro Tag. Wird Ihr Widerruf wirksam, löscht unsere tägliche automatische Bereinigung die Bilder Ihrer Bestellung, sobald 14 Tage seit Ihrem Widerruf vergangen sind (war Ihre Zahlung noch in Bearbeitung, erst wenn sie abgeschlossen ist); der Bestelldatensatz mit Ihrer Erklärung bleibt (siehe [Wie lange wir Ihre Daten speichern](#retention)). Passen Ihre Angaben zu keiner unserer Bestellungen (ohne den Link von Ihrer Bestellseite oder den Widerrufslink in Ihrer Bestellbestätigung muss die E-Mail-Adresse die sein, mit der Sie bezahlt haben), bewahren wir die Erklärung gesondert auf, prüfen sie selbst, senden Ihnen trotzdem eine Eingangsbestätigung per E-Mail (in den unter [Online widerrufen](doc:withdrawal#online) genannten Grenzen gegen Missbrauch) und löschen sie automatisch rund 13 Monate nach Ende des Monats, in dem sie eingegangen ist.`,
};

// The admin log and the admin sign-in guard (api/_lib/ops.py, the admin role, 2026-09-29): every admin action writes
// {action, order, ok, result code, eye, detail with emails masked} to ops/audit/<day>/ (no email address, no link, no
// key), purged after AUDIT_KEEP_MONTHS = 24 months by the daily clean-up (api/_lib/cleanup.py _audit), and a copy to
// ops/orderlog/<order>/, which the panel shows with the order and which stays with the order record. A failed sign-in
// stores only a keyed hash of the client address (ops/adminfail/<hour>/), deleted after 2 days (events.purge_old).
const ADMIN_LOG = {
  en: {
    log: "When we handle an order in our admin panel, for example release a file after our quality check, send an email again, make a refund or delete files, the panel writes an entry to our admin log: what was done, when, for which order number and how it ended. The admin log holds no images, no email addresses and no links. Legal basis: our legitimate interest in handling orders securely and traceably (Art. 6(1)(f) GDPR). It is deleted automatically after 24 months; the entries about an order are also kept with that order's record, for as long as the record is kept (see [How long we keep your data](#retention)).",
    signin: 'Our admin panel is only for us. To stop anyone guessing its key, a failed sign-in stores a hash of the IP address it came from, made with a secret key, never the address itself, and this is deleted automatically after 2 days. Legal basis: our legitimate interest in keeping our systems secure (Art. 6(1)(f) GDPR).',
  },
  de: {
    log: 'Wenn wir eine Bestellung in unserem Admin-Bereich bearbeiten, etwa eine Datei nach unserer Qualitätsprüfung freigeben, eine E-Mail erneut senden, eine Erstattung vornehmen oder Dateien löschen, schreibt der Admin-Bereich einen Eintrag in unser Admin-Protokoll: was getan wurde, wann, für welche Bestellnummer und mit welchem Ergebnis. Das Admin-Protokoll enthält keine Bilder, keine E-Mail-Adressen und keine Links. Rechtsgrundlage: unser berechtigtes Interesse an einer sicheren und nachvollziehbaren Bearbeitung von Bestellungen (Art. 6 Abs. 1 lit. f DSGVO). Es wird nach 24 Monaten automatisch gelöscht; die Einträge zu einer Bestellung bleiben außerdem beim Datensatz dieser Bestellung, solange dieser aufbewahrt wird (siehe [Wie lange wir Ihre Daten speichern](#retention)).',
    signin: 'Unser Admin-Bereich ist nur für uns. Damit niemand seinen Schlüssel erraten kann, speichert eine fehlgeschlagene Anmeldung einen mit einem geheimen Schlüssel gebildeten Hashwert der IP-Adresse, von der sie kam, nie die Adresse selbst; er wird nach 2 Tagen automatisch gelöscht. Rechtsgrundlage: unser berechtigtes Interesse an der Sicherheit unserer Systeme (Art. 6 Abs. 1 lit. f DSGVO).',
  },
};

// The admin panel's usage statistics and its admin log (the "operations" section and two retention rows). Written from
// api/_lib/events.py (the admin role, 2026-09-29): one small JSON object per event under ops/events/<day>/ in the
// private Supabase bucket, only numbers, booleans and short codes (FIELDS); no image, no typed text, no name, no
// email, no IP address, no user agent, no signed link, no ticket; an order id ONLY in the "master" event (the file of
// a paid order was made); day counts under ops/daily/; both deleted after 365 days by events.purge_old, which the daily
// clean-up runs (api/_lib/cleanup.py _events). Keep every sentence in step with those files.
const OPS = {
  en: {
    events:
      'To see whether the service works, how fast it is and what it costs, our server records small technical events in our private storage at Supabase in the EU. For example: that a photo was checked (with the result, such as "no eye found", the kind of device, such as iPhone, Android or computer, whether the photo came from the camera or the gallery, and the page language), that reflections were removed, that a preview or an ordered file was made and how long it took, or that a request failed (with its error code). Our admin panel shows them to us, mostly as counts per day.',
    content:
      '**These events hold no image, no text you typed, no name, no email address, no IP address, no browser identification (user agent) and no link.** Events from the free preview cannot be traced back to you. Only the events about making the file of a paid order also hold its order number, so that we can find a slow or failed rendering; through our order records, that number relates to your order.',
    basis:
      'Legal basis: our legitimate interest in running the service reliably, finding faults and keeping its costs under control (Art. 6(1)(f) GDPR). The events, and the daily counts made from them, are deleted automatically after 12 months. You may object at any time (see [Your rights](#rights)).',
    admin: ADMIN_LOG.en.log,
    signin: ADMIN_LOG.en.signin,
  },
  de: {
    events:
      'Um zu sehen, ob der Dienst funktioniert, wie schnell er ist und was er kostet, legt unser Server kleine technische Ereignisse in unserem privaten Speicher bei Supabase in der EU ab. Zum Beispiel: dass ein Foto geprüft wurde (mit dem Ergebnis, etwa „kein Auge gefunden“, der Art des Geräts, etwa iPhone, Android oder Computer, ob das Foto von der Kamera oder aus der Galerie stammt, und der Sprache der Seite), dass Spiegelungen entfernt wurden, dass eine Vorschau oder eine bestellte Datei erstellt wurde und wie lange das dauerte, oder dass eine Anfrage fehlschlug (mit ihrem Fehlercode). Unser Admin-Bereich zeigt sie uns, meist als Zahlen pro Tag.',
    content:
      '**Diese Ereignisse enthalten kein Bild, keinen von Ihnen eingegebenen Text, keinen Namen, keine E-Mail-Adresse, keine IP-Adresse, keine Browserkennung (User-Agent) und keinen Link.** Ereignisse aus der kostenlosen Vorschau lassen sich nicht auf Sie zurückführen. Nur die Ereignisse zur Erstellung der Datei einer bezahlten Bestellung enthalten auch deren Bestellnummer, damit wir eine langsame oder fehlgeschlagene Erstellung finden können; über unsere Bestelldatensätze gehört diese Nummer zu Ihrer Bestellung.',
    basis:
      'Rechtsgrundlage: unser berechtigtes Interesse, den Dienst zuverlässig zu betreiben, Fehler zu finden und seine Kosten im Griff zu behalten (Art. 6 Abs. 1 lit. f DSGVO). Die Ereignisse und die daraus gebildeten Tageszahlen werden nach 12 Monaten automatisch gelöscht. Sie können jederzeit widersprechen (siehe [Ihre Rechte](#rights)).',
    admin: ADMIN_LOG.de.log,
    signin: ADMIN_LOG.de.signin,
  },
};

const rep = (label: string) => (SELLER.representative ? ` ${label} ${SELLER.representative}.` : '');
const senderEn = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: sending the emails about your order (the link to your order page, the order confirmation and, if you withdraw, the acknowledgement of receipt). Its servers may be outside the EU.`];
const senderDe = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: Versand der E-Mails zu Ihrer Bestellung (Link zu Ihrer Bestellseite, Bestellbestätigung und, falls Sie widerrufen, Eingangsbestätigung). Die Server können außerhalb der EU liegen.`];
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
    'This policy explains what happens to your data when you use snapeyes.com: the free preview and, when you order, your digital artwork. In short: your photo is used only to make your artwork, never to identify anyone and never to train AI. We do not store free previews. The files of paid orders are kept for 12 months so you can download them again, then deleted.',
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
        'To be able to suggest prices in your own currency, our server can also read the country that Vercel derives from your IP address (for example "AU"). It is used only for that suggestion, never changes the prices you see, and is not stored.',
        'Legal basis: our legitimate interest in a secure, working website (Art. 6(1)(f) GDPR).',
        'Our fonts are served from our own server, so no data goes to Google Fonts or any other font service. We do not use analytics, advertising or tracking tools of other companies on this website, and nothing follows you from page to page or across websites. Our own anonymous service statistics are described under [Service statistics and our admin log](#operations).',
      ],
    },
    {
      id: 'preview',
      title: 'Your free preview',
      blocks: [
        "To make your preview, you send one or more photos of an eye from your browser to our server functions. There the photo is processed in memory: we find the iris, cut it out, check whether it is sharp and bright enough, remove reflections, restore the fine fibres with Google's Gemini API and set the iris in the styles you see. The result goes back to your browser. Every transfer is encrypted (HTTPS).",
        '**We do not store your photo, the iris crop or the preview on our servers.** They are discarded when the request ends. The preview stays in your browser until you close the page (while you are on the payment page, in the session storage of your browser tab: see [Cookies and local storage](#storage)), unless you save it yourself. Only when you start an order do we keep the iris crop and the preview you approved: see [When you order](#orders).',
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
        "If you add the eyes of other people (for example for a Couple Duo), we process their images only to make the artwork they agreed to. Legal basis: your and our legitimate interest in making that artwork (Art. 6(1)(f) GDPR). Please show them this policy.",
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
      id: 'operations',
      title: 'Service statistics and our admin log',
      blocks: [OPS.en.events, OPS.en.content, OPS.en.basis, OPS.en.admin, OPS.en.signin],
    },
    {
      id: 'orders',
      title: 'When you order',
      blocks: [
        'When you start an order, two images of each eye are uploaded to our private storage, so that your file is made from exactly what you saw: the square around your iris cut from your photo (with reflections removed) and the preview you approved. **Your full phone photo is not stored, not even for an order.** An order that is not paid within 24 hours can no longer be paid. An automatic clean-up that runs once a day then deletes its images and records, normally within two days of the order and at the latest within 30 days.',
        'To keep uploads within limits, our server also writes a small marker for each upload (its size, the day and the order number, no image). These markers are deleted automatically after a few days.',
        'To sell and deliver your artwork, we process: the order (order number, date, eyes, style, layout, any names or inscription you add, language, price), your email address (you enter it on the payment page), the payment status we receive from Stripe, your consent to the immediate start (see [Right of withdrawal](doc:withdrawal)), and the files of your order: the two images of each eye named above, the 4096\u00a0px rendering of each eye and the finished artwork, with technical quality records.',
        'We keep these files in a private storage bucket at Supabase, located in the EU. You reach them through your order page, whose link we email to you; it contains a private key, so anyone with the link can download your artwork. Each download link it creates expires after 7 days.',
        'We may look at the files of your order to check their quality, for example when our automatic check reports a difference from the preview you approved.',
        'Legal basis: the contract with you (Art. 6(1)(b) GDPR); for accounting records, our legal obligations (Art. 6(1)(c) GDPR).',
        'When you continue to the payment page, we pass the order details to Stripe with your payment: the order number, the price, the number of eyes, the style, the layout, the language, any names or inscription you added, and the version and time of your consent. Stripe keeps them with the payment record, and we read them back from there to make exactly the artwork you paid for.',
        'Payment: Stripe processes your payment. We never see your full card number. Stripe also processes payment data under its own privacy policy, for fraud prevention and for its own legal duties.',
        'We need your email address to send you the link to your order page and the order confirmation. Without it you could lose access to your file.',
      ],
    },
    {
      id: 'email',
      title: 'When you write to us',
      blocks: [
        'If you email us, we use your address and your message to answer you and, where it concerns an order, to handle that order. Legal basis: Art. 6(1)(b) GDPR for orders, otherwise our legitimate interest in answering you (Art. 6(1)(f) GDPR). If you send us photos, for example of your eye so that we can advise you on a better shot, we use them only for your request. We keep your emails, with any photos, for as long as we need them for your request and any follow-up.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'When you withdraw from an order online',
      blocks: [
        WITHDRAW_PRIVACY.en,
        'Legal basis: our legal obligation to accept your withdrawal and to confirm it to you (Art. 6(1)(c) GDPR) and the contract with you (Art. 6(1)(b) GDPR). We keep the statement with your order record, as proof, for as long as that record is kept (see [How long we keep your data](#retention)).',
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
            'Stripe: payment processing, with the order details named in [When you order](#orders).',
            hostingerEn,
            ...senderEn,
          ],
        },
        `These providers process your data on our behalf and on our instructions (Stripe partly as an independent controller, see [When you order](#orders)). Where data is transferred outside the EU or EEA, this happens under the safeguards the providers offer, such as the European Commission's standard contractual clauses or the EU-US Data Privacy Framework. You can ask us for a copy of these safeguards at ${MAIL}.`,
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
            ['Unpaid orders', 'An order that is not paid within 24 hours can no longer be paid. Our daily automatic clean-up deletes its images and records, normally within two days of the order and at the latest within 30 days.'],
            ['Upload and statement markers', 'Small counters without images, names or email addresses (a counter of acknowledgements of receipt holds only a short hash of the email address), deleted automatically after a few days; the monthly counters of acknowledgements about 40 days after the end of their month.'],
            ['Paid orders', 'The files of your order are kept for 12 months from your payment, so that you can download them again from your order page, and then deleted by our daily automatic clean-up. On request we delete them earlier; after that your order page can no longer deliver the file.'],
            ['Withdrawn orders', 'If the withdrawal takes effect, our daily clean-up deletes the images of the order once 14 days have passed since the withdrawal (if the payment was still being processed, once it has been settled).'],
            ['Withdrawal statements that match no order', 'Kept separately, checked by hand and deleted automatically about 13 months after the end of the month in which they reached us.'],
            ['Order records', 'When the files are deleted (after 12 months, after a withdrawal or on request), we keep the record of a paid order: order number, date, price, payment and any refund, your email address, the details of the artwork you ordered (which can include names or an inscription you added), your consent to the immediate start, if you withdrew, your withdrawal statement, and the entries of our admin log about your order. No images. We keep it as proof of the contract and for accounting, for as long as Lithuanian accounting and tax law requires.'],
            ['Server logs and measurements', 'Kept by our hosting provider for a short time, then deleted.'],
            ['Service statistics', 'The technical events and their daily counts (see [Service statistics and our admin log](#operations)): deleted automatically after 12 months.'],
            ['Admin log', 'What we did with an order in our admin panel: deleted automatically after 24 months; the entries about an order stay with its order record.'],
            ['Failed sign-ins to our admin panel', 'A hash of the IP address, made with a secret key, deleted automatically after 2 days.'],
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
        'This website sets no cookies. It uses no analytics, advertising or tracking tools of other companies.',
        'When you choose a language with the language switch, your browser remembers the choice in its local storage under the key "snapeyes.lang" (the value is the language code, for example "lt"). It is never sent to us, and you can delete it at any time in your browser settings. It is strictly necessary for a function you asked for, so it needs no consent (Art. 5(3) ePrivacy Directive).',
        'If you come to us through a link with prices in another currency (for example in Australian dollars), or choose a currency with our currency switch or in our offer of prices in your own currency, your browser also remembers that choice in its local storage under the key "snapeyes.market" (for example "au", or "eu" once you have declined that offer), so that the site keeps showing you the same prices. Our pages carry it in their links (m=au) and send it with an order, so that you are charged the prices you saw. You can delete it at any time in your browser settings; it is strictly necessary for a function you asked for, so it needs no consent either (Art. 5(3) ePrivacy Directive).',
        'When you order, the page also keeps two entries in the session storage of your browser tab. Session storage belongs to that one tab and is deleted when you close it:',
        {
          ul: [
            '"snapeyes.order": the number of the order you are building and its private key, so that the page can continue your order, for example when you come back from the payment page. It is removed when the page of your paid order opens in that tab, and replaced when you start a new order.',
            '"snapeyes.checkout": only while you are on the payment page, your artwork as you left it (the iris crops from your photos, the previews, the style, the layout and any names), so that going back from the payment page shows it again. It is removed as soon as you come back, or when the page of your paid order opens in that tab.',
          ],
        },
        'The page uses them only for your order, and they are strictly necessary for it, so they need no consent either (Art. 5(3) ePrivacy Directive).',
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
    'Diese Erklärung beschreibt, was mit Ihren Daten geschieht, wenn Sie snapeyes.com nutzen: die kostenlose Vorschau und, wenn Sie bestellen, Ihr digitales Kunstwerk. Kurz gesagt: Ihr Foto dient nur dazu, Ihr Kunstwerk zu erstellen, nie dazu, jemanden zu identifizieren, und nie zum Training von KI. Kostenlose Vorschauen speichern wir nicht. Die Dateien bezahlter Bestellungen bewahren wir 12 Monate auf, damit Sie sie erneut herunterladen können, danach werden sie gelöscht.',
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
        'Um Ihnen Preise in Ihrer eigenen Währung vorschlagen zu können, kann unser Server außerdem das Land lesen, das Vercel aus Ihrer IP-Adresse ableitet (zum Beispiel „AU“). Es dient nur diesem Vorschlag, ändert nie die angezeigten Preise und wird nicht gespeichert.',
        'Rechtsgrundlage: unser berechtigtes Interesse an einer sicheren, funktionierenden Website (Art. 6 Abs. 1 lit. f DSGVO).',
        'Unsere Schriftarten kommen von unserem eigenen Server, es werden also keine Daten an Google Fonts oder andere Schriftdienste übertragen. Wir setzen auf dieser Website keine Analyse-, Werbe- oder Tracking-Werkzeuge anderer Unternehmen ein, und nichts verfolgt Sie von Seite zu Seite oder über Websites hinweg. Unsere eigene anonyme Betriebsstatistik ist unter [Betriebsstatistik und Admin-Protokoll](#operations) beschrieben.',
      ],
    },
    {
      id: 'preview',
      title: 'Ihre kostenlose Vorschau',
      blocks: [
        'Für Ihre Vorschau senden Sie ein oder mehrere Fotos eines Auges aus Ihrem Browser an unsere Server-Funktionen. Dort wird das Foto im Arbeitsspeicher verarbeitet: Wir finden die Iris, schneiden sie aus, prüfen, ob sie scharf und hell genug ist, entfernen Spiegelungen, stellen die feinen Fasern mit der Gemini-API von Google wieder her und setzen die Iris in die Stile, die Sie sehen. Das Ergebnis geht an Ihren Browser zurück. Jede Übertragung ist verschlüsselt (HTTPS).',
        '**Ihr Foto, den Iris-Ausschnitt und die Vorschau speichern wir nicht auf unseren Servern.** Sie werden verworfen, sobald die Anfrage abgeschlossen ist. Die Vorschau bleibt in Ihrem Browser, bis Sie die Seite schließen (während Sie auf der Zahlungsseite sind, im Sitzungsspeicher des Tabs: siehe [Cookies und lokaler Speicher](#storage)), es sei denn, Sie speichern sie selbst. Nur wenn Sie eine Bestellung beginnen, bewahren wir den Iris-Ausschnitt und die freigegebene Vorschau auf: siehe [Wenn Sie bestellen](#orders).',
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
        'Wenn Sie Augen anderer Personen hinzufügen (zum Beispiel für ein Couple Duo), verarbeiten wir deren Bilder nur, um das Kunstwerk zu erstellen, dem diese Personen zugestimmt haben. Rechtsgrundlage: Ihr und unser berechtigtes Interesse an diesem Kunstwerk (Art. 6 Abs. 1 lit. f DSGVO). Bitte zeigen Sie ihnen diese Erklärung.',
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
      id: 'operations',
      title: 'Betriebsstatistik und Admin-Protokoll',
      blocks: [OPS.de.events, OPS.de.content, OPS.de.basis, OPS.de.admin, OPS.de.signin],
    },
    {
      id: 'orders',
      title: 'Wenn Sie bestellen',
      blocks: [
        'Wenn Sie eine Bestellung beginnen, werden von jedem Auge zwei Bilder in unseren privaten Speicher hochgeladen, damit Ihre Datei genau aus dem entsteht, was Sie gesehen haben: das Quadrat um Ihre Iris, aus Ihrem Foto ausgeschnitten (ohne Spiegelungen), und die von Ihnen freigegebene Vorschau. **Ihr vollständiges Smartphone-Foto wird nicht gespeichert, auch nicht bei einer Bestellung.** Eine Bestellung, die nicht innerhalb von 24 Stunden bezahlt wird, kann nicht mehr bezahlt werden. Eine automatische Bereinigung, die einmal täglich läuft, löscht dann ihre Bilder und Aufzeichnungen, normalerweise innerhalb von zwei Tagen nach der Bestellung und spätestens innerhalb von 30 Tagen.',
        'Damit die Uploads in Grenzen bleiben, legt unser Server außerdem zu jedem Upload eine kleine Markierung an (Größe, Tag und Bestellnummer, kein Bild). Diese Markierungen werden nach wenigen Tagen automatisch gelöscht.',
        'Um Ihr Kunstwerk zu verkaufen und zu liefern, verarbeiten wir: die Bestellung (Bestellnummer, Datum, Augen, Stil, Anordnung, von Ihnen eingegebene Namen oder Widmung, Sprache, Preis), Ihre E-Mail-Adresse (Sie geben sie auf der Zahlungsseite ein), den Zahlungsstatus, den wir von Stripe erhalten, Ihre Zustimmung zum sofortigen Beginn (siehe [Widerrufsbelehrung](doc:withdrawal)) und die Dateien Ihrer Bestellung: die beiden oben genannten Bilder jedes Auges, die 4096-px-Fassung jedes Auges und das fertige Kunstwerk, mit technischen Qualitätsprotokollen.',
        'Diese Dateien bewahren wir in einem privaten Speicher bei Supabase in der EU auf. Sie erreichen sie über Ihre Bestellseite, deren Link wir Ihnen per E-Mail senden; er enthält einen privaten Schlüssel, daher kann jede Person mit diesem Link Ihr Kunstwerk herunterladen. Jeder Download-Link, den die Seite erzeugt, läuft nach 7 Tagen ab.',
        'Wir können die Dateien Ihrer Bestellung ansehen, um ihre Qualität zu prüfen, etwa wenn unsere automatische Prüfung eine Abweichung von der freigegebenen Vorschau meldet.',
        'Rechtsgrundlage: der Vertrag mit Ihnen (Art. 6 Abs. 1 lit. b DSGVO); für Buchhaltungsunterlagen unsere gesetzlichen Pflichten (Art. 6 Abs. 1 lit. c DSGVO).',
        'Wenn Sie zur Zahlungsseite weitergehen, übermitteln wir Stripe mit Ihrer Zahlung die Bestelldaten: Bestellnummer, Preis, Anzahl der Augen, Stil, Anordnung, Sprache, von Ihnen eingegebene Namen oder Widmung sowie Fassung und Zeitpunkt Ihrer Zustimmung. Stripe speichert sie mit dem Zahlungsdatensatz, und wir lesen sie von dort wieder aus, um genau das Kunstwerk zu erstellen, das Sie bezahlt haben.',
        'Zahlung: Stripe wickelt Ihre Zahlung ab. Ihre vollständige Kartennummer sehen wir nie. Stripe verarbeitet Zahlungsdaten außerdem nach seiner eigenen Datenschutzerklärung, zur Betrugsvorbeugung und für seine eigenen gesetzlichen Pflichten.',
        'Ihre E-Mail-Adresse brauchen wir, um Ihnen den Link zu Ihrer Bestellseite und die Bestellbestätigung zu senden. Ohne sie könnten Sie den Zugang zu Ihrer Datei verlieren.',
      ],
    },
    {
      id: 'email',
      title: 'Wenn Sie uns schreiben',
      blocks: [
        'Wenn Sie uns eine E-Mail senden, nutzen wir Ihre Adresse und Ihre Nachricht, um Ihnen zu antworten und, falls es um eine Bestellung geht, diese abzuwickeln. Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO bei Bestellungen, sonst unser berechtigtes Interesse, Ihnen zu antworten (Art. 6 Abs. 1 lit. f DSGVO). Wenn Sie uns Fotos senden, etwa von Ihrem Auge, damit wir Sie zu einer besseren Aufnahme beraten, verwenden wir sie nur für Ihr Anliegen. Wir bewahren Ihre E-Mails samt Fotos so lange auf, wie wir sie für Ihr Anliegen und etwaige Rückfragen brauchen.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Wenn Sie online widerrufen',
      blocks: [
        WITHDRAW_PRIVACY.de,
        'Rechtsgrundlage: unsere gesetzliche Pflicht, Ihren Widerruf entgegenzunehmen und Ihnen zu bestätigen (Art. 6 Abs. 1 lit. c DSGVO), und der Vertrag mit Ihnen (Art. 6 Abs. 1 lit. b DSGVO). Die Erklärung bleibt als Nachweis bei Ihrem Bestelldatensatz, solange dieser aufbewahrt wird (siehe [Wie lange wir Ihre Daten speichern](#retention)).',
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
            'Google (Gemini-API): die KI-Restaurierung der Iris und die Prüfung Ihres Fotos. Die Server von Google können außerhalb der EU liegen.',
            'Supabase: privater Speicher für die Dateien von Bestellungen, in einer EU-Region.',
            'Stripe: Zahlungsabwicklung, mit den unter [Wenn Sie bestellen](#orders) genannten Bestelldaten.',
            hostingerDe,
            ...senderDe,
          ],
        },
        `Diese Anbieter verarbeiten Ihre Daten in unserem Auftrag und nach unseren Weisungen (Stripe teilweise als eigenständig Verantwortlicher, siehe [Wenn Sie bestellen](#orders)). Werden Daten außerhalb der EU oder des EWR übermittelt, geschieht dies auf Grundlage der Garantien, die die Anbieter bieten, etwa der Standardvertragsklauseln der EU-Kommission oder des EU-US Data Privacy Framework. Eine Kopie dieser Garantien erhalten Sie auf Anfrage unter ${MAIL}.`,
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
            ['Unbezahlte Bestellungen', 'Eine Bestellung, die nicht innerhalb von 24 Stunden bezahlt wird, kann nicht mehr bezahlt werden. Unsere tägliche automatische Bereinigung löscht ihre Bilder und Aufzeichnungen, normalerweise innerhalb von zwei Tagen nach der Bestellung und spätestens innerhalb von 30 Tagen.'],
            ['Upload- und Erklärungsmarkierungen', 'Kleine Zähler ohne Bilder, Namen oder E-Mail-Adressen (ein Zähler für Eingangsbestätigungen enthält nur einen kurzen Hashwert der E-Mail-Adresse), die nach wenigen Tagen automatisch gelöscht werden; die monatlichen Zähler für Eingangsbestätigungen rund 40 Tage nach Ende ihres Monats.'],
            ['Bezahlte Bestellungen', 'Die Dateien Ihrer Bestellung bewahren wir 12 Monate ab Ihrer Zahlung auf, damit Sie sie über Ihre Bestellseite erneut herunterladen können; danach löscht sie unsere tägliche automatische Bereinigung. Auf Wunsch löschen wir sie früher; danach kann Ihre Bestellseite die Datei nicht mehr liefern.'],
            ['Widerrufene Bestellungen', 'Wird der Widerruf wirksam, löscht unsere tägliche Bereinigung die Bilder der Bestellung, sobald 14 Tage seit dem Widerruf vergangen sind (war die Zahlung noch in Bearbeitung, sobald sie abgeschlossen ist).'],
            ['Widerrufserklärungen ohne passende Bestellung', 'Werden gesondert aufbewahrt, von uns geprüft und rund 13 Monate nach Ende des Monats, in dem sie eingegangen sind, automatisch gelöscht.'],
            ['Bestelldatensätze', 'Wenn die Dateien gelöscht sind (nach 12 Monaten, nach einem Widerruf oder auf Wunsch), bewahren wir den Datensatz einer bezahlten Bestellung auf: Bestellnummer, Datum, Preis, Zahlung und gegebenenfalls Erstattung, Ihre E-Mail-Adresse, die Angaben zum bestellten Kunstwerk (darunter gegebenenfalls von Ihnen eingegebene Namen oder eine Widmung), Ihre Zustimmung zum sofortigen Beginn, falls Sie widerrufen haben, Ihre Widerrufserklärung, und die Einträge unseres Admin-Protokolls zu Ihrer Bestellung. Keine Bilder. Wir bewahren ihn als Nachweis des Vertrags und für die Buchhaltung so lange auf, wie es das litauische Buchführungs- und Steuerrecht verlangt.'],
            ['Server-Protokolle und Messwerte', 'Werden bei unserem Hosting-Anbieter für kurze Zeit gespeichert und dann gelöscht.'],
            ['Betriebsstatistik', 'Die technischen Ereignisse und ihre Tageszahlen (siehe [Betriebsstatistik und Admin-Protokoll](#operations)): werden nach 12 Monaten automatisch gelöscht.'],
            ['Admin-Protokoll', 'Was wir in unserem Admin-Bereich mit einer Bestellung getan haben: wird nach 24 Monaten automatisch gelöscht; die Einträge zu einer Bestellung bleiben bei ihrem Bestelldatensatz.'],
            ['Fehlgeschlagene Anmeldungen im Admin-Bereich', 'Ein mit einem geheimen Schlüssel gebildeter Hashwert der IP-Adresse, nach 2 Tagen automatisch gelöscht.'],
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
        'Diese Website setzt keine Cookies. Sie nutzt keine Analyse-, Werbe- oder Tracking-Werkzeuge anderer Unternehmen.',
        'Wenn Sie mit dem Sprachschalter eine Sprache wählen, merkt sich Ihr Browser diese Wahl in seinem lokalen Speicher unter dem Schlüssel „snapeyes.lang“ (der Wert ist der Sprachcode, zum Beispiel „lt“). Dieser Eintrag wird nie an uns übertragen, und Sie können ihn jederzeit in Ihren Browsereinstellungen löschen. Er ist für eine von Ihnen gewünschte Funktion unbedingt erforderlich und braucht daher keine Einwilligung (§ 25 Abs. 2 Nr. 2 TDDDG, Art. 5 Abs. 3 ePrivacy-Richtlinie).',
        'Wenn Sie über einen Link mit Preisen in einer anderen Währung zu uns kommen (zum Beispiel in australischen Dollar) oder mit unserem Währungsschalter oder in unserem Angebot von Preisen in Ihrer eigenen Währung eine Währung wählen, merkt sich Ihr Browser diese Wahl außerdem in seinem lokalen Speicher unter dem Schlüssel „snapeyes.market“ (zum Beispiel „au“, oder „eu“, wenn Sie dieses Angebot abgelehnt haben), damit die Website Ihnen weiter dieselben Preise zeigt. Unsere Seiten tragen sie in ihren Links (m=au) und senden sie mit einer Bestellung, damit Ihnen die Preise berechnet werden, die Sie gesehen haben. Sie können den Eintrag jederzeit in Ihren Browsereinstellungen löschen; er ist für eine von Ihnen gewünschte Funktion unbedingt erforderlich und braucht daher ebenfalls keine Einwilligung (§ 25 Abs. 2 Nr. 2 TDDDG, Art. 5 Abs. 3 ePrivacy-Richtlinie).',
        'Wenn Sie bestellen, legt die Seite außerdem zwei Einträge im Sitzungsspeicher (Session Storage) Ihres Browser-Tabs an. Der Sitzungsspeicher gehört nur zu diesem einen Tab und wird gelöscht, wenn Sie ihn schließen:',
        {
          ul: [
            '„snapeyes.order“: die Nummer der Bestellung, die Sie gerade anlegen, und ihr privater Schlüssel, damit die Seite Ihre Bestellung fortsetzen kann, etwa wenn Sie von der Zahlungsseite zurückkommen. Der Eintrag wird entfernt, wenn sich in diesem Tab die Seite Ihrer bezahlten Bestellung öffnet, und ersetzt, wenn Sie eine neue Bestellung beginnen.',
            '„snapeyes.checkout“: nur während Sie auf der Zahlungsseite sind, Ihr Kunstwerk so, wie Sie es verlassen haben (die Iris-Ausschnitte aus Ihren Fotos, die Vorschauen, der Stil, die Anordnung und gegebenenfalls Namen), damit es beim Zurückgehen von der Zahlungsseite wieder erscheint. Der Eintrag wird entfernt, sobald Sie zurückkommen oder sich in diesem Tab die Seite Ihrer bezahlten Bestellung öffnet.',
          ],
        },
        'Die Seite nutzt sie nur für Ihre Bestellung, und sie sind dafür unbedingt erforderlich; auch sie brauchen daher keine Einwilligung (§ 25 Abs. 2 Nr. 2 TDDDG, Art. 5 Abs. 3 ePrivacy-Richtlinie).',
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

export const PRIVACY: LegalDocs = { en, de, lt, hu };

// ------------------------------------------------------------------------------------------ the Australian edition
// Written from what the code does (see the header) and the Australian sources of 2026-09-29: OAIC on biometric
// information (sensitive when used to identify or verify), the small business exemption (A$3 million turnover, still
// in force; its removal is expected, not passed) and the statutory tort for serious invasions of privacy (10 June 2025).
const auEn = patchDoc(en, {
  after: {
    rights: [
      {
        id: 'australia',
        title: 'Your data if you live in Australia',
        blocks: [
          'This policy follows the EU General Data Protection Regulation (GDPR), which applies to everything we do with your data, wherever you live. If you live in Australia, this section adds what you should know under Australian privacy law.',
          '**Your eye photos.** A photo of an eye can be biometric information, which the Australian Privacy Act 1988 treats as sensitive information when it is used to identify or verify a person. We never use it that way: we never create, compare or store an iris template or any other biometric identifier, never identify or verify anyone, never sell your photos and never use them to train AI (see [Your iris is never used to identify anyone](#iris)). We collect your eye photos only because you send them to us to make your preview and your artwork, and we use them only for that.',
          '**Where your data goes.** We are based in Lithuania, so your data is processed outside Australia: in the EU and by the services named under [Services we use](#services), some of which may process it in the USA or in other countries. The safeguards for these transfers are described there.',
          '**Australian Privacy Principles.** We handle your data as this policy describes, whether or not the Australian Privacy Principles apply to us: as a small business with an annual turnover of A$3 million or less, we are generally exempt from them under the Privacy Act as it stands today. Your right to sue for a serious invasion of privacy, which has applied since 10 June 2025, is not affected.',
          `**Access, correction and complaints.** You can ask us at any time for access to the data we hold about you and to have it corrected (see [Your rights](#rights)): write to ${MAIL}. If the Australian Privacy Principles apply to us and you are not satisfied with our answer, you can complain to the Office of the Australian Information Commissioner ([oaic.gov.au](https://www.oaic.gov.au)).`,
        ],
      },
    ],
  },
});

const auDe = patchDoc(de, {
  after: {
    rights: [
      {
        id: 'australia',
        title: 'Ihre Daten, wenn Sie in Australien leben',
        blocks: [
          'Diese Erklärung folgt der EU-Datenschutz-Grundverordnung (DSGVO), die für alles gilt, was wir mit Ihren Daten tun, wo auch immer Sie leben. Wenn Sie in Australien leben, ergänzt dieser Abschnitt, was Sie nach australischem Datenschutzrecht wissen sollten.',
          '**Ihre Augenfotos.** Ein Foto eines Auges kann eine biometrische Information sein, die der australische Privacy Act 1988 als sensible Information behandelt, wenn sie zur Identifizierung oder Verifizierung einer Person dient. So verwenden wir sie nie: Wir erstellen, vergleichen oder speichern nie ein Iris-Template oder ein anderes biometrisches Merkmal, identifizieren oder verifizieren niemanden, verkaufen Ihre Fotos nie und nutzen sie nie zum Training von KI (siehe [Ihre Iris dient nie zur Identifizierung](#iris)). Wir erheben Ihre Augenfotos nur, weil Sie sie uns senden, damit wir Ihre Vorschau und Ihr Kunstwerk erstellen, und verwenden sie nur dafür.',
          '**Wohin Ihre Daten gehen.** Wir sitzen in Litauen, Ihre Daten werden also außerhalb Australiens verarbeitet: in der EU und bei den unter [Dienste, die wir nutzen](#services) genannten Diensten, von denen einige sie in den USA oder in anderen Ländern verarbeiten können. Die Garantien für diese Übermittlungen sind dort beschrieben.',
          '**Australian Privacy Principles.** Wir behandeln Ihre Daten so, wie diese Erklärung es beschreibt, ob die Australian Privacy Principles für uns gelten oder nicht: Als kleines Unternehmen mit einem Jahresumsatz von höchstens 3 Millionen australischen Dollar sind wir nach dem Privacy Act in seiner heutigen Fassung in der Regel davon ausgenommen. Ihr Recht, wegen einer schweren Verletzung Ihrer Privatsphäre zu klagen, das seit dem 10. Juni 2025 gilt, bleibt davon unberührt.',
          `**Auskunft, Berichtigung und Beschwerden.** Sie können jederzeit Auskunft über die Daten verlangen, die wir über Sie speichern, und ihre Berichtigung (siehe [Ihre Rechte](#rights)): Schreiben Sie an ${MAIL}. Gelten die Australian Privacy Principles für uns und sind Sie mit unserer Antwort nicht zufrieden, können Sie sich beim Office of the Australian Information Commissioner ([oaic.gov.au](https://www.oaic.gov.au)) beschweren.`,
        ],
      },
    ],
  },
});

export const PRIVACY_AU: EditionDocs = { en: auEn, de: auDe };
