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
//    names as one JSON string, title, date, opts (swap, rotate, look), lang, amount, consent version and time, and since WP12 the
//    plan8, plates version pv and engine version ev of the frozen plan), so names, date and inscription reach Stripe
//  - the derived eye profile (api/_lib/styles/eye.py: ring colours, colour class, pupil class, gate values, eye_id) is sealed in the
//    preview and stored in draft/eye_<n>.json with the two images (deleted with them); order.json keeps checkout.plan with a short
//    summary (class, mean ring colour, pupil class), and the style folder's plan.json goes 14 days after delivery
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
//  - price tests (api/_lib/abtest.py, src/shared/pricing.ts; only while the owner has one running, and only for a visitor
//    whose market runs one): localStorage "snapeyes.vid" (a random anonymous visitor number and its day, made only while a
//    test runs for the visitor's market, deleted when none runs, replaced after 90 days; sent in the request header
//    X-Snapeyes-Visitor to GET /api/checkout, never in a URL, never stored by the application), "snapeyes.pricing" (the
//    last answer), "snapeyes.expseen" (which anonymous counts were sent) and "snapeyes.notest" (the visitor's opt-out, the
//    link /?pricetest=off in the storage section); the server answers with a signed note of the visitor's price list and
//    records anonymous counts per price list (events kind "exp", order.json checkout.experiment, the Stripe metadata exp,
//    exp_var and exp_lad, paid.json experiment). See the storage section
//  - browser storage: localStorage "snapeyes.lang" (src/landing/lang.tsx, src/try/lang.ts) and, in the order flow,
//    sessionStorage "snapeyes.order" and "snapeyes.checkout" (src/try/checkout.ts); no cookie of our own
//  - the Meta pixel (the owner's decision of 2026-11-25; src/shared/metaPixel.ts, src/landing/shell/scripts.ts pixelScript,
//    api/_lib/meta.py): section "meta". Meta's script on the landing, /try and the legal pages after the load (cookies _fbp, _fbc),
//    single requests to www.facebook.com/tr from /order and /gift (the path only), sessionStorage "snapeyes.fbc"; events PageView,
//    ViewContent, Lead, InitiateCheckout, Purchase; the server's Purchase (Conversions API) with the hashed email, fbp, fbc, IP and
//    user agent carried in the Stripe metadata (fbp, fbc, cip, cua). No consent is asked and there is no banner: the policy says so
//  - the online withdrawal function: see WITHDRAWAL_ONLINE in src/shared/legal.ts and the "withdrawal" section
// PRIVACY_AU (the end of this file) is the Australian edition (src/shared/legal.ts legalEdition "au"): the same policy
// with a section for people in Australia (eye photos as possible biometric information, never used to identify
// anyone; data processed outside Australia; the Australian Privacy Principles and the small business exemption as they
// stand; the statutory privacy tort since 10 June 2025; the OAIC). PRIVACY_US (after it) is the US edition (legalEdition
// "us", English only): the same policy with a section for people in the United States (the state laws on biometric
// identifiers, the retention schedule of the eye images as the daily clean-up keeps it, no sale; since the Meta pixel of 2026-11-25 it says that
// the pixel may count as "sharing" for targeted advertising and how to object).
// Not reviewed by a lawyer. Keep every sentence true when the code or a service changes.
import type { EditionDocs, LegalDoc, LegalDocs } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';
import { patchDoc } from '../patch';
import { lt } from './privacy.lt';
import { hu } from './privacy.hu';
import { hr } from './privacy.hr';
import { fi } from './privacy.fi';
import { et } from './privacy.et';
import { lv } from './privacy.lv';

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
      'To see whether the service works, how fast it is and what it costs, our server records small technical events in our private storage at Supabase in the EU. For example: that a photo was checked (with the result, such as "no eye found", the kind of device, such as iPhone, Android or computer, whether the photo came from the camera or the gallery, and the page language), that reflections were removed, that a preview or an ordered file was made and how long it took, or that a request failed (with its error code). While we test prices, the events also say which price list (a short code) was shown, previewed, opened for payment or paid, with the amount of a paid order. Our admin panel shows them to us, mostly as counts per day.',
    counter:
      'To see how many people reach each step of the site, our server also counts the steps a page reaches: that the first page was opened, that the photo page was opened, that a photo was chosen or taken, that the preview was shown (with the seconds it took from the photo), that the buy card showed that ordering is not open yet, that the buy button was pressed, and that the order page was opened. Each count is a small record of numbers and short codes: the step, the page language, the market (currency), the kind of device (iPhone, Android or computer), the kind of browser (for example Chrome, Safari, or the built-in browser of the Facebook or Instagram app) and the country (two letters, which Vercel derives from your IP address). To work out the device and the browser our server reads your browser identification (user agent) for a moment, and to hold back a client that sends far too many counts it keeps a hash of your IP address in its memory for under a minute, made with a key that is lost when the server restarts; it stores neither. These counts use no cookie and no visitor number and hold no IP address, no browser identification, no address of a page and no link you came from, so they cannot be traced back to you. In our admin panel we see them added up per day.',
    campaign:
      'If you reach us through an advertisement or a link of ours that carries a campaign code, or from another website, your browser keeps that code for the length of your visit (see [Cookies and local storage](#storage)), and the counts above, the photo checks and previews you make, the payment page and your order carry it, so that we can see which advertisement led to which step, what it cost per step and which order it brought. The code is the same for everyone who followed that advertisement and is not derived from you.',
    feedback:
      'On the result screen and on the card that asks for another photo, a small feedback box offers six answers (for example "I love it" or "The colours look off") and, if you wish, a text of up to 300 characters. Nothing is sent until you press Send. The box has no field for your name or email address: please do not write any, nor telephone numbers or links. When you press Send, our server records your answer as one more small event of codes (the answer, the style that was on screen or the reason a photo was refused, the number of eyes, whether a text came with it, and the same details as in the step counts above: the campaign code, the page language, the market, the kind of device and browser, and the country). A text is stored separately, with those codes and nothing else, and only if it passes a check: a text that contains an at sign, a telephone number, a link or what looks like spam is not kept (your answer is still counted). We read the texts in our admin panel; we cannot reply, because we do not know who wrote them. Every text is deleted automatically after 90 days, and we can delete one earlier. Because nothing in the box identifies you, we can find your text later only if you tell us what it said. The box writes nothing to your browser.',
    content:
      '**These events hold no image, no text you typed (a text written in the feedback box is stored apart from them, as described above), no name, no email address, no IP address, no browser identification (user agent) and no link.** Events from the free preview cannot be traced back to you. Only the events about making the file of a paid order also hold its order number, so that we can find a slow or failed rendering; through our order records, that number relates to your order.',
    basis:
      'Legal basis: our legitimate interest in running the service reliably, finding faults and keeping its costs under control and learning what puts visitors off (Art. 6(1)(f) GDPR). The events, and the daily counts made from them, are deleted automatically after 12 months; the texts of the feedback box after 90 days. You may object at any time (see [Your rights](#rights)).',
    admin: ADMIN_LOG.en.log,
    signin: ADMIN_LOG.en.signin,
    // the day's ceiling of free previews per connection (api/_lib/previewcap.py, 2026-11-11): a keyed hash of the address and the day, ops/previewcap/<day>/, deleted after 2 days
    previewcap: 'To keep the free preview free for everyone, one internet connection can make a limited number of previews a day. For each preview our server stores a hash of the IP address it came from and of the day, made with a secret key, never the address itself: the address cannot be read back from it, and the next day the same address gives another hash. These entries are deleted automatically after 2 days. Legal basis: our legitimate interest in keeping the free preview available and its costs under control (Art. 6(1)(f) GDPR).',
  },
  de: {
    events:
      'Um zu sehen, ob der Dienst funktioniert, wie schnell er ist und was er kostet, legt unser Server kleine technische Ereignisse in unserem privaten Speicher bei Supabase in der EU ab. Zum Beispiel: dass ein Foto geprüft wurde (mit dem Ergebnis, etwa „kein Auge gefunden“, der Art des Geräts, etwa iPhone, Android oder Computer, ob das Foto von der Kamera oder aus der Galerie stammt, und der Sprache der Seite), dass Spiegelungen entfernt wurden, dass eine Vorschau oder eine bestellte Datei erstellt wurde und wie lange das dauerte, oder dass eine Anfrage fehlschlug (mit ihrem Fehlercode). Solange wir Preise testen, sagen die Ereignisse außerdem, welche Preisliste (ein kurzer Code) angezeigt, in der Vorschau gesehen, zur Zahlung geöffnet oder bezahlt wurde, bei einer bezahlten Bestellung mit dem Betrag. Unser Admin-Bereich zeigt sie uns, meist als Zahlen pro Tag.',
    counter:
      'Um zu sehen, wie viele Menschen die einzelnen Schritte der Website erreichen, zählt unser Server außerdem die Schritte, die eine Seite erreicht: dass die erste Seite geöffnet wurde, dass die Fotoseite geöffnet wurde, dass ein Foto ausgewählt oder aufgenommen wurde, dass die Vorschau angezeigt wurde (mit den Sekunden, die sie ab dem Foto brauchte), dass die Kaufkarte zeigte, dass Bestellungen noch nicht möglich sind, dass die Kauf-Schaltfläche gedrückt wurde und dass die Bestellseite geöffnet wurde. Jede Zählung ist ein kleiner Datensatz aus Zahlen und kurzen Codes: der Schritt, die Sprache der Seite, der Markt (die Währung), die Art des Geräts (iPhone, Android oder Computer), die Art des Browsers (zum Beispiel Chrome, Safari oder der eingebaute Browser der Facebook- oder Instagram-App) und das Land (zwei Buchstaben, die Vercel aus Ihrer IP-Adresse ableitet). Um Gerät und Browser zu bestimmen, liest unser Server kurz Ihre Browserkennung (User-Agent), und um einen Client auszubremsen, der viel zu viele Zählungen sendet, hält er weniger als eine Minute lang einen Hashwert Ihrer IP-Adresse im Arbeitsspeicher, gebildet mit einem Schlüssel, der beim Neustart des Servers verloren geht; beides wird nicht gespeichert. Diese Zählungen verwenden keinen Cookie und keine Besuchernummer und enthalten keine IP-Adresse, keine Browserkennung, keine Adresse einer Seite und keinen Link, von dem Sie kamen; sie lassen sich daher nicht auf Sie zurückführen. In unserem Admin-Bereich sehen wir sie pro Tag aufsummiert.',
    campaign:
      'Wenn Sie über eine Werbeanzeige oder einen Link von uns mit einem Kampagnencode oder von einer anderen Website zu uns kommen, behält Ihr Browser diesen Code für die Dauer Ihres Besuchs (siehe [Cookies und lokaler Speicher](#storage)), und die obigen Zählungen, die Fotoprüfungen und Vorschauen, die Zahlungsseite und Ihre Bestellung tragen ihn, damit wir sehen können, welche Anzeige zu welchem Schritt geführt hat, was sie pro Schritt gekostet hat und welche Bestellung sie gebracht hat. Der Code ist für alle gleich, die derselben Anzeige gefolgt sind, und wird nicht aus Ihnen abgeleitet.',
    feedback:
      'Auf dem Ergebnisbildschirm und auf der Karte, die um ein anderes Foto bittet, bietet ein kleines Feedback-Feld sechs Antworten (zum Beispiel „Ich liebe es“ oder „Die Farben stimmen nicht“) und, wenn Sie möchten, einen Text von bis zu 300 Zeichen. Es wird nichts gesendet, bis Sie auf „Senden“ drücken. Das Feedback-Feld hat kein Eingabefeld für Ihren Namen oder Ihre E-Mail-Adresse: Bitte schreiben Sie keine, auch keine Telefonnummern oder Links. Wenn Sie auf „Senden“ drücken, hält unser Server Ihre Antwort als ein weiteres kleines Ereignis aus Codes fest (die Antwort, den Stil, der auf dem Bildschirm war, oder den Grund, aus dem ein Foto abgelehnt wurde, die Zahl der Augen, ob ein Text dabei war, und dieselben Angaben wie bei den Schrittzählungen oben: den Kampagnencode, die Sprache der Seite, den Markt, die Art des Geräts und des Browsers und das Land). Ein Text wird getrennt gespeichert, mit diesen Codes und sonst nichts, und nur, wenn er eine Prüfung besteht: Ein Text mit einem At-Zeichen, einer Telefonnummer, einem Link oder mit dem Anschein von Spam wird nicht gespeichert (Ihre Antwort wird trotzdem gezählt). Wir lesen die Texte in unserem Admin-Bereich; antworten können wir nicht, weil wir nicht wissen, wer sie geschrieben hat. Jeder Text wird nach 90 Tagen automatisch gelöscht, und wir können ihn auch früher löschen. Da nichts im Feld Sie identifiziert, können wir Ihren Text später nur finden, wenn Sie uns sagen, was darin stand. Das Feld schreibt nichts in Ihren Browser.',
    content:
      '**Diese Ereignisse enthalten kein Bild, keinen von Ihnen eingegebenen Text (ein Text aus dem Feedback-Feld wird getrennt davon gespeichert, wie oben beschrieben), keinen Namen, keine E-Mail-Adresse, keine IP-Adresse, keine Browserkennung (User-Agent) und keinen Link.** Ereignisse aus der kostenlosen Vorschau lassen sich nicht auf Sie zurückführen. Nur die Ereignisse zur Erstellung der Datei einer bezahlten Bestellung enthalten auch deren Bestellnummer, damit wir eine langsame oder fehlgeschlagene Erstellung finden können; über unsere Bestelldatensätze gehört diese Nummer zu Ihrer Bestellung.',
    basis:
      'Rechtsgrundlage: unser berechtigtes Interesse, den Dienst zuverlässig zu betreiben, Fehler zu finden, seine Kosten im Griff zu behalten und zu erfahren, was Besucher abschreckt (Art. 6 Abs. 1 lit. f DSGVO). Die Ereignisse und die daraus gebildeten Tageszahlen werden nach 12 Monaten automatisch gelöscht, die Texte des Feedback-Felds nach 90 Tagen. Sie können jederzeit widersprechen (siehe [Ihre Rechte](#rights)).',
    admin: ADMIN_LOG.de.log,
    signin: ADMIN_LOG.de.signin,
    previewcap: 'Damit die kostenlose Vorschau für alle kostenlos bleibt, kann eine Internetverbindung nur eine begrenzte Zahl von Vorschauen pro Tag erstellen. Für jede Vorschau speichert unser Server einen mit einem geheimen Schlüssel gebildeten Hashwert der IP-Adresse, von der sie kam, und des Tages, nie die Adresse selbst: Die Adresse lässt sich daraus nicht zurückgewinnen, und am nächsten Tag ergibt dieselbe Adresse einen anderen Hashwert. Diese Einträge werden nach 2 Tagen automatisch gelöscht. Rechtsgrundlage: unser berechtigtes Interesse, die kostenlose Vorschau verfügbar und ihre Kosten im Griff zu halten (Art. 6 Abs. 1 lit. f DSGVO).',
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
    'This policy explains what happens to your data when you use snapeyes.com: the free preview and, when you order, your digital artwork. In short: your photo is used to make your artwork and to check its quality, never to identify anyone and never to train AI. We keep free previews for up to 30 days to check and improve their quality, then delete them. The files of paid orders are kept for 12 months so you can download them again, then deleted.',
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
        'To be able to suggest prices in your own currency, our server can also read the country that Vercel derives from your IP address (for example "AU"). It is used for that suggestion and never changes the prices you see. It is stored with nothing that could identify you: its only trace is the two letters of the country in our anonymous counts (see [Service statistics and our admin log](#operations)).',
        'Legal basis: our legitimate interest in a secure, working website (Art. 6(1)(f) GDPR).',
        'Our fonts are served from our own server, so no data goes to Google Fonts or any other font service. Our own anonymous service statistics are described under [Service statistics and our admin log](#operations). Of the tools of other companies we use one on this website, the Meta pixel for our advertisements: see [The Meta pixel and our advertisements](#meta).',
      ],
    },
    {
      id: 'preview',
      title: 'Your free preview',
      blocks: [
        "To make your preview, you send one or more photos of an eye from your browser to our server functions. There the photo is processed in memory: we find the iris, cut it out, check whether it is sharp and bright enough, remove reflections, restore the fine fibres with Google's Gemini API and set the iris in the styles you see. The result goes back to your browser. Every transfer is encrypted (HTTPS).",
        '**We keep a copy of your free preview for up to 30 days.** Our server stores in our private storage at Supabase in the EU: the photos you send (made smaller, at most 1280 pixels on the longer side), the square cut around your iris, its restoration, the previews shown to you, and anonymous codes: what our checks found (for example whether a photo could be used and, if not, why), the style, the time, and the same anonymous context as our service statistics (campaign code, kind of device and browser, language and country). We keep them to check and improve the quality of our previews and to find out why photos fail. Only we see them, in our admin panel. They are not linked to your name, email address or IP address, and like everything else they are never used to identify anyone, never sold and never used to train AI. Our daily clean-up deletes them automatically after 30 days at the latest. The preview also stays in your browser until you close the page (while you are on the payment page, in the session storage of your browser tab: see [Cookies and local storage](#storage)), unless you save it yourself. When you start an order, we also keep the iris crop and the preview you approved with the order: see [When you order](#orders).',
        "Google processes the image to make the restoration. We use Google's paid API service, under whose terms Google does not use the images to improve its products or to train its models. Google may keep requests for a limited period, solely to detect misuse and for disclosures the law requires.",
        'Legal basis: you ask us to make your preview, and the photo is needed for it (Art. 6(1)(b) GDPR, steps taken at your request).',
        `Legal basis for this copy: our legitimate interest in checking and improving the quality of our previews and in finding out why photos fail (Art. 6(1)(f) GDPR). You may object at any time or ask us to delete it: write to ${MAIL} with the approximate date and time of your visit, so that we can find it.`,
        'Our software decides automatically whether a photo can be used (for example when it is too blurry or too dark). This decision has no legal or similarly significant effect on you: you can simply take another photo.',
      ],
    },
    {
      id: 'iris',
      title: 'Your iris is never used to identify anyone',
      blocks: [
        "An iris can, in principle, be used to recognise a person. We do not do that. We never create, compare or store an iris template or any other biometric identifier, we never use your images to identify or verify anyone, we never sell them, and we never use them to train AI, neither our own nor anyone else's.",
        'Please only use your own eye, or the eye of someone who has agreed to it. For a child, a parent or guardian must agree.',
        "If you add the eyes of other people (for example for a pair), we process their images only to make the artwork they agreed to. Legal basis: your and our legitimate interest in making that artwork (Art. 6(1)(f) GDPR). Please show them this policy.",
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
      blocks: [OPS.en.events, OPS.en.counter, OPS.en.campaign, OPS.en.feedback, OPS.en.content, OPS.en.basis, OPS.en.admin, OPS.en.signin, OPS.en.previewcap],
    },
    {
      id: 'meta',
      title: 'The Meta pixel and our advertisements',
      blocks: [
        'We advertise on Facebook and Instagram. To learn which of our advertisements bring visitors and orders, and so that Meta can show them to people who are likely to be interested, our pages use the Meta pixel, a tool of Meta Platforms Ireland Limited, Merrion Road, Dublin 4, D04 X2K5, Ireland ("Meta"). It runs on our pages for every visitor; we do not ask you about it first.',
        'The pixel tells Meta when a page is opened, when the photo page is opened, when a free preview is shown to you, when you go on to the payment page and when a payment is made, with the amount and the currency of the payment and whether it was for an artwork, a gift voucher or a print. With each of these reports your browser sends Meta, as with any request, your IP address and browser identification (user agent), the address of the page and of the page you came from, and the Meta cookies described below. From our order page and our gift voucher page only the path of the page is sent ("/order", "/gift"), never its full address, which holds the key to your order or the number of your payment. If you use Facebook or Instagram, Meta can link these reports to your account.',
        '**We never send Meta your photo, your iris, your eye colour, the style you chose, names or a date you add, your artwork or any other image.** The automatic functions of the pixel that would read the buttons and the form fields of a page are switched off.',
        'Meta\'s script, which your browser loads from connect.facebook.net only after our page itself has loaded, sets two cookies on snapeyes.com: "_fbp", a random number by which Meta recognises your browser on later visits, kept for 90 days from your last visit, and, only when you came through a link with a Meta click number ("fbclid", for example from an advertisement), "_fbc", which holds that number, also for 90 days. If you came through such a link and your browser has no "_fbc" cookie, our page keeps the click number in the session storage of your browser tab under the key "snapeyes.fbc" until you close the tab. The reports go to www.facebook.com. Our order page and our gift voucher page do not load Meta\'s script: they send their reports as single requests to www.facebook.com.',
        'When you pay for an artwork, a gift voucher or a print, our server also reports the payment to Meta directly (the Meta Conversions API), so that it is counted even when the report from your browser does not arrive. This report holds: that a payment was made, when, its amount and currency, whether it was for an artwork, a voucher or a print, the path of the page ("/order" or "/gift"), a hash of the email address you paid with (SHA-256: the address cannot be read back from it, but Meta can compare it with the hashed addresses of its own users), your country (from your payment details or the prices you chose), and the values of the "_fbp" and "_fbc" cookies, the IP address and the browser identification your browser had when you opened the payment page. The two reports of one payment carry the same number, so that Meta counts it once. So that our server has them at the payment, these four values travel with the payment page to Stripe, in the metadata of the payment, and stay with Stripe\'s payment record (see [When you order](#orders)); we store them nowhere else.',
        'We use these reports to measure which of our advertisements work and to show them to people who are likely to be interested. Legal basis: our legitimate interest in measuring and directing our own advertising (Art. 6(1)(f) GDPR). For collecting these data on our website and passing them to Meta, we and Meta are jointly responsible (Art. 26 GDPR) under Meta\'s terms for its business tools, and you can use your rights with either of us. What Meta does with the data afterwards, Meta decides as its own controller, under its own privacy policy; Meta may process them in the USA, under the EU-US Data Privacy Framework.',
        'You may object at any time: write to us (see [Your rights](#rights)). You can also delete or block Meta\'s cookies and the session storage in your browser settings, or use a browser or an extension that blocks such tools; our site works the same without them. In your Facebook or Instagram account (Accounts Center, ad preferences) you can choose whether Meta may use information from other websites to show you advertisements.',
      ],
    },
    {
      id: 'orders',
      title: 'When you order',
      blocks: [
        'When you start an order, two images of each eye are uploaded to our private storage, so that your file is made from exactly what you saw: the square around your iris cut from your photo (with reflections removed) and the preview you approved. With them we keep a short record of measurements made from that preview (the colours around your iris, a colour class, the shape of the pupil, two quality values and a code that identifies the preview). It holds no image and is deleted together with the images. **Your order does not keep your full phone photo;** the copy of the photos you sent for the free preview is kept apart for up to 30 days (see [Your free preview](#preview)). An order that is not paid within 24 hours can no longer be paid. An automatic clean-up that runs once a day then deletes its images and records, normally within two days of the order and at the latest within 30 days.',
        'To keep uploads within limits, our server also writes a small marker for each upload (its size, the day and the order number, no image). These markers are deleted automatically after a few days.',
        'To sell and deliver your artwork, we process: the order (order number, date, eyes, style, layout, the order of the eyes, any names, date or inscription you add, language, price), your email address (you enter it on the payment page), the payment status we receive from Stripe, your consent to the immediate start (see [Right of withdrawal](doc:withdrawal)), and the files of your order: the two images of each eye named above, the 4096\u00a0px rendering of each eye and the finished artwork, with technical quality records.',
        'We keep these files in a private storage bucket at Supabase, located in the EU. You reach them through your order page, whose link we email to you; it contains a private key, so anyone with the link can download your artwork. Each download link it creates expires after 7 days.',
        'We may look at the files of your order to check their quality, for example when our automatic check reports a difference from the preview you approved.',
        'Legal basis: the contract with you (Art. 6(1)(b) GDPR); for accounting records, our legal obligations (Art. 6(1)(c) GDPR).',
        'When you continue to the payment page, we pass the order details to Stripe with your payment: the order number, the price (and, when a price test applied, its name, the code of your price list and the prices of that list), the number of eyes, the style (and its look), the layout, the order of the eyes, the language, any names, date or inscription you added, a short code that identifies the plan of the artwork and the version of our software that makes it, the version and time of your consent and, if you came through an advertisement, its campaign code. Stripe keeps them with the payment record, and we read them back from there to make exactly the artwork you paid for. While we report payments to Meta, the payment also carries the values of the Meta cookies "_fbp" and "_fbc" if your browser has them, and the IP address and browser identification your browser had at that moment (see [The Meta pixel and our advertisements](#meta)).',
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
            'Supabase: private storage of the files of orders and of the 30-day copies of free previews, in an EU region.',
            'Stripe: payment processing, with the order details named in [When you order](#orders).',
            hostingerEn,
            ...senderEn,
            'Meta (Meta Platforms Ireland Limited): the Meta pixel and the reports of payments, see [The Meta pixel and our advertisements](#meta). Meta may process data in the USA.',
          ],
        },
        `These providers process your data on our behalf and on our instructions (Stripe partly as an independent controller, see [When you order](#orders); Meta as described under [The Meta pixel and our advertisements](#meta)). Where data is transferred outside the EU or EEA, this happens under the safeguards the providers offer, such as the European Commission's standard contractual clauses or the EU-US Data Privacy Framework. You can ask us for a copy of these safeguards at ${MAIL}.`,
        'We do not sell your data and we do not pass it on to anyone else, unless the law obliges us to.',
      ],
    },
    {
      id: 'retention',
      title: 'How long we keep your data',
      blocks: [
        {
          dl: [
            ['Free previews', 'The copy of the photos you sent, the iris crop, the restoration, the previews and their anonymous codes: deleted automatically after 30 days at the latest, or earlier on request.'],
            ['Unpaid orders', 'An order that is not paid within 24 hours can no longer be paid. Our daily automatic clean-up deletes its images and records, normally within two days of the order and at the latest within 30 days.'],
            ['Upload and statement markers', 'Small counters without images, names or email addresses (a counter of acknowledgements of receipt holds only a short hash of the email address), deleted automatically after a few days; the monthly counters of acknowledgements about 40 days after the end of their month.'],
            ['Paid orders', 'The files of your order are kept for 12 months from your payment, so that you can download them again from your order page, and then deleted by our daily automatic clean-up. On request we delete them earlier; after that your order page can no longer deliver the file.'],
            ['Withdrawn orders', 'If the withdrawal takes effect, our daily clean-up deletes the images of the order once 14 days have passed since the withdrawal (if the payment was still being processed, once it has been settled).'],
            ['Withdrawal statements that match no order', 'Kept separately, checked by hand and deleted automatically about 13 months after the end of the month in which they reached us.'],
            ['Order records', 'When the files are deleted (after 12 months, after a withdrawal or on request), we keep the record of a paid order: order number, date, price, payment and any refund, your email address, the campaign code of the advertisement you came from (if any), the details of the artwork you ordered (which can include names, a date or an inscription you added, and a short summary of the measurements made from your previews: the colour class, the average ring colour and the pupil shape of each eye), your consent to the immediate start, if you withdrew, your withdrawal statement, and the entries of our admin log about your order. No images. We keep it as proof of the contract and for accounting, for as long as Lithuanian accounting and tax law requires.'],
            ['Server logs and measurements', 'Kept by our hosting provider for a short time, then deleted.'],
            ['Service statistics', 'The technical events and their daily counts (see [Service statistics and our admin log](#operations)): deleted automatically after 12 months.'],
            ['Feedback texts', 'The optional texts of the feedback box (see [Service statistics and our admin log](#operations)): deleted automatically after 90 days, or earlier by us. The answers themselves are only codes and part of the technical events, kept as described above.'],
            ['Admin log', 'What we did with an order in our admin panel: deleted automatically after 24 months; the entries about an order stay with its order record.'],
            ['Failed sign-ins to our admin panel', 'A hash of the IP address, made with a secret key, deleted automatically after 2 days.'],
            ['Free previews per connection', 'A hash of the IP address and the day, made with a secret key, deleted automatically after 2 days.'],
            ['Meta cookies and reports', '"_fbp" and "_fbc" in your browser: 90 days from your last visit, unless you delete them earlier; "snapeyes.fbc": until you close the tab. The cookie values, IP address and browser identification passed with a payment: with Stripe\'s payment record. How long Meta keeps its reports, Meta decides (see its privacy policy).'],
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
        'Our own pages set no cookies. The Meta pixel sets two cookies of Meta, "_fbp" and "_fbc", and our page may keep the key "snapeyes.fbc": see [The Meta pixel and our advertisements](#meta). Apart from it, the site uses no analytics, advertising or tracking tools of other companies.',
        'When you choose a language with the language switch, your browser remembers the choice in its local storage under the key "snapeyes.lang" (the value is the language code, for example "lt"). It is never sent to us, and you can delete it at any time in your browser settings. It is strictly necessary for a function you asked for, so it needs no consent (Art. 5(3) ePrivacy Directive).',
        'If you come to us through a link with prices in another currency (for example in Australian dollars), or choose a currency with our currency switch or in our offer of prices in your own currency, your browser also remembers that choice in its local storage under the key "snapeyes.market" (for example "au", or "eu" once you have declined that offer), so that the site keeps showing you the same prices. Our pages carry it in their links (m=au) and send it with an order, so that you are charged the prices you saw. You can delete it at any time in your browser settings; it is strictly necessary for a function you asked for, so it needs no consent either (Art. 5(3) ePrivacy Directive).',
        'When we test prices (only now and then, for a limited time), your browser may keep a random anonymous visitor number in its local storage under the key "snapeyes.vid". It is made only while a price test is running for the market (currency) you are viewing, and it is deleted again as soon as no test runs; at the latest it is replaced after 90 days. It consists of 32 random characters and the day it was made: it is not derived from you, holds no name, email address or device data, and is never linked to an order. Your browser sends it to our server in a request header (never in the address of a page) when it asks for the prices; our application uses it only to work out, the same way every time, which of the test\'s price lists you see, and does not store it: we keep no list of visitor numbers. The server answers with a signed note of your price list, which your browser sends back when you go to the payment page, so that you are charged exactly the prices you were shown (a price or price list sent by a browser is never used). For the statistics our server records anonymous counts per price list: that a price list was shown, that a preview was made, that the payment page was opened and that an order was paid (see [Service statistics and our admin log](#operations)); these counts hold no visitor number. Your browser also remembers in local storage which of these counts it has already sent ("snapeyes.expseen") and your last price list ("snapeyes.pricing"), so that the same prices show at once. Which price list you see never depends on where you live beyond the market (currency) you choose, and the price you pay is always the one shown to you before you pay; your order confirmation names the price list that applied. We use these entries only for this price test, never for advertising and never to follow you across other websites. If you would rather not take part, [open this link](/?pricetest=off&lang=en): your browser then keeps only the note "snapeyes.notest", deletes the visitor number and the other entries named here, and shows and charges the standard prices; [this link](/?pricetest=on&lang=en) takes part again. If your browser sends the "Global Privacy Control" signal, that counts as this choice as well. You can also delete all these entries at any time in your browser settings (you then get a new random draw). Legal basis: our legitimate interest in setting fair prices (Art. 6(1)(f) GDPR). You may object at any time (see [Your rights](#rights)).',
        'If you reach us through an advertisement or a link of ours that carries a campaign code, or from another website, your browser keeps a short code in the session storage of your browser tab under the key "snapeyes.c": the parameters of the address that name the advertisement, as its maker typed them (utm_source, utm_medium, utm_campaign, utm_term and utm_content: the platform, the kind, the campaign, the group and the advertisement; for example "utm_source=fb&utm_medium=paid&utm_campaign=spring"), or, when there are none, only the kind of website you came from (for example "ref=facebook": facebook, instagram, tiktok, google, direct or other). Session storage belongs to that one tab and is deleted when you close it. The code is the same for everyone who followed the same advertisement: it is not derived from you and holds no name, email address, device data or click number (a "fbclid" click number in the address is never part of it; what happens to that number is described under [The Meta pixel and our advertisements](#meta)). Our pages send it with their anonymous page counts and requests (photo check, preview, payment page); the order record keeps it, and Stripe\'s payment page receives it in the metadata of the payment, so that we can see which advertisement led to which step and to an order (see [Service statistics and our admin log](#operations) and [When you order](#orders)). We use it only for that, never for advertising, profiling or to follow you across other websites. You do not need it to use the site: if you delete it or your browser blocks session storage, everything works the same and only that count is missing. Legal basis: our legitimate interest in knowing whether our own advertising works (Art. 6(1)(f) GDPR). You may object at any time (see [Your rights](#rights)).',
        'When you order, the page also keeps two entries in the session storage of your browser tab. Session storage belongs to that one tab and is deleted when you close it:',
        {
          ul: [
            '"snapeyes.order": the number of the order you are building and its private key, so that the page can continue your order, for example when you come back from the payment page. It is removed when the page of your paid order opens in that tab, and replaced when you start a new order.',
            '"snapeyes.checkout": only while you are on the payment page, your artwork as you left it (the iris crops from your photos, the previews, a few numbers measured from them, the style and its look, the layout, the order of the eyes, and any names and date), so that going back from the payment page shows it again. It is removed as soon as you come back, or when the page of your paid order opens in that tab.',
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
    'Diese Erklärung beschreibt, was mit Ihren Daten geschieht, wenn Sie snapeyes.com nutzen: die kostenlose Vorschau und, wenn Sie bestellen, Ihr digitales Kunstwerk. Kurz gesagt: Ihr Foto dient dazu, Ihr Kunstwerk zu erstellen und seine Qualität zu prüfen, nie dazu, jemanden zu identifizieren, und nie zum Training von KI. Kostenlose Vorschauen bewahren wir bis zu 30 Tage auf, um ihre Qualität zu prüfen und zu verbessern, danach löschen wir sie. Die Dateien bezahlter Bestellungen bewahren wir 12 Monate auf, damit Sie sie erneut herunterladen können, danach werden sie gelöscht.',
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
        'Um Ihnen Preise in Ihrer eigenen Währung vorschlagen zu können, kann unser Server außerdem das Land lesen, das Vercel aus Ihrer IP-Adresse ableitet (zum Beispiel „AU“). Es dient diesem Vorschlag und ändert nie die angezeigten Preise. Es wird mit nichts gespeichert, was Sie identifizieren könnte: Seine einzige Spur sind die zwei Buchstaben des Landes in unseren anonymen Zählungen (siehe [Betriebsstatistik und Admin-Protokoll](#operations)).',
        'Rechtsgrundlage: unser berechtigtes Interesse an einer sicheren, funktionierenden Website (Art. 6 Abs. 1 lit. f DSGVO).',
        'Unsere Schriftarten kommen von unserem eigenen Server, es werden also keine Daten an Google Fonts oder andere Schriftdienste übertragen. Unsere eigene anonyme Betriebsstatistik ist unter [Betriebsstatistik und Admin-Protokoll](#operations) beschrieben. Von den Werkzeugen anderer Unternehmen setzen wir auf dieser Website eines ein, das Meta-Pixel für unsere Werbung: siehe [Das Meta-Pixel und unsere Werbung](#meta).',
      ],
    },
    {
      id: 'preview',
      title: 'Ihre kostenlose Vorschau',
      blocks: [
        'Für Ihre Vorschau senden Sie ein oder mehrere Fotos eines Auges aus Ihrem Browser an unsere Server-Funktionen. Dort wird das Foto im Arbeitsspeicher verarbeitet: Wir finden die Iris, schneiden sie aus, prüfen, ob sie scharf und hell genug ist, entfernen Spiegelungen, stellen die feinen Fasern mit der Gemini-API von Google wieder her und setzen die Iris in die Stile, die Sie sehen. Das Ergebnis geht an Ihren Browser zurück. Jede Übertragung ist verschlüsselt (HTTPS).',
        '**Eine Kopie Ihrer kostenlosen Vorschau bewahren wir bis zu 30 Tage auf.** Unser Server speichert in unserem privaten Speicher bei Supabase in der EU: die Fotos, die Sie senden (verkleinert, höchstens 1280 Pixel an der längeren Seite), das Quadrat um Ihre Iris, seine Restaurierung, die Ihnen gezeigten Vorschauen und anonyme Codes: was unsere Prüfungen ergaben (zum Beispiel, ob ein Foto verwendbar war und, wenn nicht, warum), den Stil, die Uhrzeit und denselben anonymen Kontext wie unsere Dienststatistik (Kampagnencode, Art des Geräts und des Browsers, Sprache und Land). Wir bewahren sie auf, um die Qualität unserer Vorschauen zu prüfen und zu verbessern und herauszufinden, warum Fotos scheitern. Nur wir sehen sie, in unserem Admin-Bereich. Sie werden nicht mit Ihrem Namen, Ihrer E-Mail-Adresse oder Ihrer IP-Adresse verknüpft und, wie alles andere, nie zur Identifizierung verwendet, nie verkauft und nie zum Training von KI genutzt. Unsere tägliche Bereinigung löscht sie spätestens nach 30 Tagen automatisch. Die Vorschau bleibt außerdem in Ihrem Browser, bis Sie die Seite schließen (während Sie auf der Zahlungsseite sind, im Sitzungsspeicher des Tabs: siehe [Cookies und lokaler Speicher](#storage)), es sei denn, Sie speichern sie selbst. Wenn Sie eine Bestellung beginnen, bewahren wir den Iris-Ausschnitt und die freigegebene Vorschau zusätzlich mit der Bestellung auf: siehe [Wenn Sie bestellen](#orders).',
        'Google verarbeitet das Bild, um die Restaurierung zu erstellen. Wir nutzen den kostenpflichtigen API-Dienst von Google; nach dessen Bedingungen verwendet Google die Bilder weder zur Verbesserung seiner Produkte noch zum Training seiner Modelle. Google kann Anfragen für begrenzte Zeit speichern, ausschließlich um Missbrauch zu erkennen und gesetzlich vorgeschriebene Offenlegungen zu erfüllen.',
        'Rechtsgrundlage: Sie bitten uns, Ihre Vorschau zu erstellen, und dafür wird das Foto benötigt (Art. 6 Abs. 1 lit. b DSGVO, Maßnahmen auf Ihre Anfrage).',
        `Rechtsgrundlage für diese Kopie: unser berechtigtes Interesse, die Qualität unserer Vorschauen zu prüfen und zu verbessern und herauszufinden, warum Fotos scheitern (Art. 6 Abs. 1 lit. f DSGVO). Sie können jederzeit widersprechen oder die Löschung verlangen: Schreiben Sie an ${MAIL} mit dem ungefähren Datum und der Uhrzeit Ihres Besuchs, damit wir die Kopie finden.`,
        'Unsere Software entscheidet automatisch, ob ein Foto verwendbar ist (zum Beispiel, wenn es zu unscharf oder zu dunkel ist). Diese Entscheidung hat für Sie keine rechtliche oder ähnlich erhebliche Wirkung: Sie können einfach ein neues Foto aufnehmen.',
      ],
    },
    {
      id: 'iris',
      title: 'Ihre Iris dient nie zur Identifizierung',
      blocks: [
        'Eine Iris kann grundsätzlich dazu dienen, einen Menschen wiederzuerkennen. Das tun wir nicht. Wir erstellen, vergleichen oder speichern keine Iris-Merkmalsvorlage und keine anderen biometrischen Kennungen, wir nutzen Ihre Bilder nie, um jemanden zu identifizieren oder zu verifizieren, wir verkaufen sie nie, und wir verwenden sie nie zum Training von KI, weder unserer eigenen noch der anderer.',
        'Bitte verwenden Sie nur Ihr eigenes Auge oder das Auge einer Person, die damit einverstanden ist. Bei einem Kind muss ein Elternteil oder eine sorgeberechtigte Person einverstanden sein.',
        'Wenn Sie Augen anderer Personen hinzufügen (zum Beispiel für ein Paar), verarbeiten wir deren Bilder nur, um das Kunstwerk zu erstellen, dem diese Personen zugestimmt haben. Rechtsgrundlage: Ihr und unser berechtigtes Interesse an diesem Kunstwerk (Art. 6 Abs. 1 lit. f DSGVO). Bitte zeigen Sie ihnen diese Erklärung.',
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
      blocks: [OPS.de.events, OPS.de.counter, OPS.de.campaign, OPS.de.feedback, OPS.de.content, OPS.de.basis, OPS.de.admin, OPS.de.signin, OPS.de.previewcap],
    },
    {
      id: 'meta',
      title: 'Das Meta-Pixel und unsere Werbung',
      blocks: [
        'Wir werben auf Facebook und Instagram. Um zu erfahren, welche unserer Anzeigen Besucher und Bestellungen bringen, und damit Meta sie Menschen zeigen kann, die sich wahrscheinlich dafür interessieren, verwenden unsere Seiten das Meta-Pixel, ein Werkzeug der Meta Platforms Ireland Limited, Merrion Road, Dublin 4, D04 X2K5, Irland („Meta“). Es läuft auf unseren Seiten bei jedem Besucher; wir fragen Sie vorher nicht danach.',
        'Das Pixel meldet Meta, wenn eine Seite geöffnet wird, wenn die Fotoseite geöffnet wird, wenn Ihnen eine kostenlose Vorschau gezeigt wird, wenn Sie zur Zahlungsseite weitergehen und wenn eine Zahlung erfolgt, mit Betrag und Währung der Zahlung und der Angabe, ob sie für ein Kunstwerk, einen Geschenkgutschein oder einen Druck war. Mit jeder dieser Meldungen sendet Ihr Browser Meta, wie bei jeder Anfrage, Ihre IP-Adresse und Browserkennung (User-Agent), die Adresse der Seite und der Seite, von der Sie kamen, und die unten beschriebenen Meta-Cookies. Von unserer Bestellseite und unserer Gutscheinseite wird nur der Pfad der Seite gesendet („/order“, „/gift“), nie ihre vollständige Adresse, die den Schlüssel zu Ihrer Bestellung oder die Nummer Ihrer Zahlung enthält. Wenn Sie Facebook oder Instagram nutzen, kann Meta diese Meldungen mit Ihrem Konto verknüpfen.',
        '**Wir senden Meta nie Ihr Foto, Ihre Iris, Ihre Augenfarbe, den gewählten Stil, von Ihnen eingegebene Namen oder ein Datum, Ihr Kunstwerk oder ein anderes Bild.** Die automatischen Funktionen des Pixels, die die Schaltflächen und Formularfelder einer Seite auslesen würden, sind ausgeschaltet.',
        'Das Skript von Meta, das Ihr Browser erst nach dem Laden unserer Seite von connect.facebook.net lädt, setzt zwei Cookies auf snapeyes.com: „_fbp“, eine Zufallszahl, an der Meta Ihren Browser bei späteren Besuchen wiedererkennt, gespeichert für 90 Tage ab Ihrem letzten Besuch, und nur wenn Sie über einen Link mit einer Meta-Klicknummer („fbclid“, etwa aus einer Anzeige) kamen, „_fbc“, das diese Nummer enthält, ebenfalls für 90 Tage. Kamen Sie über einen solchen Link und hat Ihr Browser kein Cookie „_fbc“, behält unsere Seite die Klicknummer im Sitzungsspeicher Ihres Browser-Tabs unter dem Schlüssel „snapeyes.fbc“, bis Sie den Tab schließen. Die Meldungen gehen an www.facebook.com. Unsere Bestellseite und unsere Gutscheinseite laden das Skript von Meta nicht: Sie senden ihre Meldungen als einzelne Anfragen an www.facebook.com.',
        'Wenn Sie für ein Kunstwerk, einen Geschenkgutschein oder einen Druck bezahlen, meldet unser Server die Zahlung außerdem direkt an Meta (die Conversions API von Meta), damit sie auch dann gezählt wird, wenn die Meldung Ihres Browsers nicht ankommt. Diese Meldung enthält: dass eine Zahlung erfolgte, wann, ihren Betrag und ihre Währung, ob sie für ein Kunstwerk, einen Gutschein oder einen Druck war, den Pfad der Seite („/order“ oder „/gift“), einen Hashwert der E-Mail-Adresse, mit der Sie bezahlt haben (SHA-256: Die Adresse lässt sich daraus nicht zurückgewinnen, Meta kann ihn aber mit den Hashwerten der Adressen seiner eigenen Nutzer vergleichen), Ihr Land (aus Ihren Zahlungsangaben oder den gewählten Preisen) sowie die Werte der Cookies „_fbp“ und „_fbc“, die IP-Adresse und die Browserkennung, die Ihr Browser beim Öffnen der Zahlungsseite hatte. Die beiden Meldungen einer Zahlung tragen dieselbe Nummer, damit Meta sie nur einmal zählt. Damit unser Server sie bei der Zahlung hat, gehen diese vier Werte mit der Zahlungsseite an Stripe, in den Metadaten der Zahlung, und bleiben beim Zahlungsdatensatz von Stripe (siehe [Wenn Sie bestellen](#orders)); sonst speichern wir sie nirgends.',
        'Wir nutzen diese Meldungen, um zu messen, welche unserer Anzeigen wirken, und um sie Menschen zu zeigen, die sich wahrscheinlich dafür interessieren. Rechtsgrundlage: unser berechtigtes Interesse, unsere eigene Werbung zu messen und auszurichten (Art. 6 Abs. 1 lit. f DSGVO). Für das Erheben dieser Daten auf unserer Website und ihre Übermittlung an Meta sind wir und Meta gemeinsam verantwortlich (Art. 26 DSGVO), nach den Bedingungen von Meta für seine Business-Tools, und Sie können Ihre Rechte bei jedem von uns beiden ausüben. Was Meta danach mit den Daten tut, entscheidet Meta als eigener Verantwortlicher nach seiner eigenen Datenschutzrichtlinie; Meta kann sie in den USA verarbeiten, auf Grundlage des EU-US Data Privacy Framework.',
        'Sie können jederzeit widersprechen: Schreiben Sie uns (siehe [Ihre Rechte](#rights)). Sie können die Cookies von Meta und den Sitzungsspeicher auch in Ihren Browsereinstellungen löschen oder blockieren oder einen Browser oder eine Erweiterung verwenden, die solche Werkzeuge blockiert; unsere Website funktioniert ohne sie genauso. In Ihrem Facebook- oder Instagram-Konto (Kontenübersicht, Werbeeinstellungen) können Sie wählen, ob Meta Informationen von anderen Websites nutzen darf, um Ihnen Werbung zu zeigen.',
      ],
    },
    {
      id: 'orders',
      title: 'Wenn Sie bestellen',
      blocks: [
        'Wenn Sie eine Bestellung beginnen, werden von jedem Auge zwei Bilder in unseren privaten Speicher hochgeladen, damit Ihre Datei genau aus dem entsteht, was Sie gesehen haben: das Quadrat um Ihre Iris, aus Ihrem Foto ausgeschnitten (ohne Spiegelungen), und die von Ihnen freigegebene Vorschau. Dazu speichern wir eine kurze Aufzeichnung von Messwerten, die aus dieser Vorschau gewonnen wurden (die Farben rund um Ihre Iris, eine Farbklasse, die Form der Pupille, zwei Qualitätswerte und eine Kennung der Vorschau). Sie enthält kein Bild und wird zusammen mit den Bildern gelöscht. **Ihre Bestellung enthält Ihr vollständiges Smartphone-Foto nicht;** die Kopie der Fotos, die Sie für die kostenlose Vorschau gesendet haben, wird getrennt davon bis zu 30 Tage aufbewahrt (siehe [Ihre kostenlose Vorschau](#preview)). Eine Bestellung, die nicht innerhalb von 24 Stunden bezahlt wird, kann nicht mehr bezahlt werden. Eine automatische Bereinigung, die einmal täglich läuft, löscht dann ihre Bilder und Aufzeichnungen, normalerweise innerhalb von zwei Tagen nach der Bestellung und spätestens innerhalb von 30 Tagen.',
        'Damit die Uploads in Grenzen bleiben, legt unser Server außerdem zu jedem Upload eine kleine Markierung an (Größe, Tag und Bestellnummer, kein Bild). Diese Markierungen werden nach wenigen Tagen automatisch gelöscht.',
        'Um Ihr Kunstwerk zu verkaufen und zu liefern, verarbeiten wir: die Bestellung (Bestellnummer, Datum, Augen, Stil, Anordnung, Reihenfolge der Augen, von Ihnen eingegebene Namen, Datum oder Widmung, Sprache, Preis), Ihre E-Mail-Adresse (Sie geben sie auf der Zahlungsseite ein), den Zahlungsstatus, den wir von Stripe erhalten, Ihre Zustimmung zum sofortigen Beginn (siehe [Widerrufsbelehrung](doc:withdrawal)) und die Dateien Ihrer Bestellung: die beiden oben genannten Bilder jedes Auges, die 4096-px-Fassung jedes Auges und das fertige Kunstwerk, mit technischen Qualitätsprotokollen.',
        'Diese Dateien bewahren wir in einem privaten Speicher bei Supabase in der EU auf. Sie erreichen sie über Ihre Bestellseite, deren Link wir Ihnen per E-Mail senden; er enthält einen privaten Schlüssel, daher kann jede Person mit diesem Link Ihr Kunstwerk herunterladen. Jeder Download-Link, den die Seite erzeugt, läuft nach 7 Tagen ab.',
        'Wir können die Dateien Ihrer Bestellung ansehen, um ihre Qualität zu prüfen, etwa wenn unsere automatische Prüfung eine Abweichung von der freigegebenen Vorschau meldet.',
        'Rechtsgrundlage: der Vertrag mit Ihnen (Art. 6 Abs. 1 lit. b DSGVO); für Buchhaltungsunterlagen unsere gesetzlichen Pflichten (Art. 6 Abs. 1 lit. c DSGVO).',
        'Wenn Sie zur Zahlungsseite weitergehen, übermitteln wir Stripe mit Ihrer Zahlung die Bestelldaten: Bestellnummer, Preis (und, wenn ein Preistest galt, dessen Name, die Kennung Ihrer Preisliste und deren Preise), Anzahl der Augen, Stil (und gegebenenfalls seine Variante), Anordnung, Reihenfolge der Augen, Sprache, von Ihnen eingegebene Namen, Datum oder Widmung, eine kurze Kennung des Plans des Kunstwerks und die Version unserer Software, die es erstellt, sowie Fassung und Zeitpunkt Ihrer Zustimmung und, falls Sie über eine Anzeige kamen, deren Kampagnencode. Stripe speichert sie mit dem Zahlungsdatensatz, und wir lesen sie von dort wieder aus, um genau das Kunstwerk zu erstellen, das Sie bezahlt haben. Solange wir Zahlungen an Meta melden, trägt die Zahlung außerdem die Werte der Meta-Cookies „_fbp“ und „_fbc“, falls Ihr Browser sie hat, sowie die IP-Adresse und die Browserkennung, die Ihr Browser in diesem Moment hatte (siehe [Das Meta-Pixel und unsere Werbung](#meta)).',
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
            'Supabase: privater Speicher für die Dateien von Bestellungen und die 30-Tage-Kopien kostenloser Vorschauen, in einer EU-Region.',
            'Stripe: Zahlungsabwicklung, mit den unter [Wenn Sie bestellen](#orders) genannten Bestelldaten.',
            hostingerDe,
            ...senderDe,
            'Meta (Meta Platforms Ireland Limited): das Meta-Pixel und die Meldungen von Zahlungen, siehe [Das Meta-Pixel und unsere Werbung](#meta). Meta kann Daten in den USA verarbeiten.',
          ],
        },
        `Diese Anbieter verarbeiten Ihre Daten in unserem Auftrag und nach unseren Weisungen (Stripe teilweise als eigenständig Verantwortlicher, siehe [Wenn Sie bestellen](#orders); Meta wie unter [Das Meta-Pixel und unsere Werbung](#meta) beschrieben). Werden Daten außerhalb der EU oder des EWR übermittelt, geschieht dies auf Grundlage der Garantien, die die Anbieter bieten, etwa der Standardvertragsklauseln der EU-Kommission oder des EU-US Data Privacy Framework. Eine Kopie dieser Garantien erhalten Sie auf Anfrage unter ${MAIL}.`,
        'Wir verkaufen Ihre Daten nicht und geben sie an niemanden sonst weiter, es sei denn, wir sind gesetzlich dazu verpflichtet.',
      ],
    },
    {
      id: 'retention',
      title: 'Wie lange wir Ihre Daten speichern',
      blocks: [
        {
          dl: [
            ['Kostenlose Vorschauen', 'Die Kopie der gesendeten Fotos, des Iris-Ausschnitts, der Restaurierung, der Vorschauen und ihrer anonymen Codes: spätestens nach 30 Tagen automatisch gelöscht, auf Wunsch früher.'],
            ['Unbezahlte Bestellungen', 'Eine Bestellung, die nicht innerhalb von 24 Stunden bezahlt wird, kann nicht mehr bezahlt werden. Unsere tägliche automatische Bereinigung löscht ihre Bilder und Aufzeichnungen, normalerweise innerhalb von zwei Tagen nach der Bestellung und spätestens innerhalb von 30 Tagen.'],
            ['Upload- und Erklärungsmarkierungen', 'Kleine Zähler ohne Bilder, Namen oder E-Mail-Adressen (ein Zähler für Eingangsbestätigungen enthält nur einen kurzen Hashwert der E-Mail-Adresse), die nach wenigen Tagen automatisch gelöscht werden; die monatlichen Zähler für Eingangsbestätigungen rund 40 Tage nach Ende ihres Monats.'],
            ['Bezahlte Bestellungen', 'Die Dateien Ihrer Bestellung bewahren wir 12 Monate ab Ihrer Zahlung auf, damit Sie sie über Ihre Bestellseite erneut herunterladen können; danach löscht sie unsere tägliche automatische Bereinigung. Auf Wunsch löschen wir sie früher; danach kann Ihre Bestellseite die Datei nicht mehr liefern.'],
            ['Widerrufene Bestellungen', 'Wird der Widerruf wirksam, löscht unsere tägliche Bereinigung die Bilder der Bestellung, sobald 14 Tage seit dem Widerruf vergangen sind (war die Zahlung noch in Bearbeitung, sobald sie abgeschlossen ist).'],
            ['Widerrufserklärungen ohne passende Bestellung', 'Werden gesondert aufbewahrt, von uns geprüft und rund 13 Monate nach Ende des Monats, in dem sie eingegangen sind, automatisch gelöscht.'],
            ['Bestelldatensätze', 'Wenn die Dateien gelöscht sind (nach 12 Monaten, nach einem Widerruf oder auf Wunsch), bewahren wir den Datensatz einer bezahlten Bestellung auf: Bestellnummer, Datum, Preis, Zahlung und gegebenenfalls Erstattung, Ihre E-Mail-Adresse, der Kampagnencode der Anzeige, über die Sie kamen (falls vorhanden), die Angaben zum bestellten Kunstwerk (darunter gegebenenfalls von Ihnen eingegebene Namen, ein Datum oder eine Widmung sowie eine kurze Zusammenfassung der aus Ihren Vorschauen gewonnenen Messwerte: Farbklasse, durchschnittliche Ringfarbe und Pupillenform jedes Auges), Ihre Zustimmung zum sofortigen Beginn, falls Sie widerrufen haben, Ihre Widerrufserklärung, und die Einträge unseres Admin-Protokolls zu Ihrer Bestellung. Keine Bilder. Wir bewahren ihn als Nachweis des Vertrags und für die Buchhaltung so lange auf, wie es das litauische Buchführungs- und Steuerrecht verlangt.'],
            ['Server-Protokolle und Messwerte', 'Werden bei unserem Hosting-Anbieter für kurze Zeit gespeichert und dann gelöscht.'],
            ['Betriebsstatistik', 'Die technischen Ereignisse und ihre Tageszahlen (siehe [Betriebsstatistik und Admin-Protokoll](#operations)): werden nach 12 Monaten automatisch gelöscht.'],
            ['Feedback-Texte', 'Die freiwilligen Texte des Feedback-Felds (siehe [Betriebsstatistik und Admin-Protokoll](#operations)): werden nach 90 Tagen automatisch gelöscht, von uns auch früher. Die Antworten selbst sind nur Codes und Teil der technischen Ereignisse, die wie oben beschrieben aufbewahrt werden.'],
            ['Admin-Protokoll', 'Was wir in unserem Admin-Bereich mit einer Bestellung getan haben: wird nach 24 Monaten automatisch gelöscht; die Einträge zu einer Bestellung bleiben bei ihrem Bestelldatensatz.'],
            ['Fehlgeschlagene Anmeldungen im Admin-Bereich', 'Ein mit einem geheimen Schlüssel gebildeter Hashwert der IP-Adresse, nach 2 Tagen automatisch gelöscht.'],
            ['Kostenlose Vorschauen pro Verbindung', 'Ein mit einem geheimen Schlüssel gebildeter Hashwert der IP-Adresse und des Tages, nach 2 Tagen automatisch gelöscht.'],
            ['Meta-Cookies und Meldungen', '„_fbp“ und „_fbc“ in Ihrem Browser: 90 Tage ab Ihrem letzten Besuch, sofern Sie sie nicht vorher löschen; „snapeyes.fbc“: bis Sie den Tab schließen. Die mit einer Zahlung übermittelten Cookie-Werte, IP-Adresse und Browserkennung: beim Zahlungsdatensatz von Stripe. Wie lange Meta seine Meldungen aufbewahrt, entscheidet Meta (siehe dessen Datenschutzrichtlinie).'],
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
        'Unsere eigenen Seiten setzen keine Cookies. Das Meta-Pixel setzt zwei Cookies von Meta, „_fbp“ und „_fbc“, und unsere Seite kann den Schlüssel „snapeyes.fbc“ ablegen: siehe [Das Meta-Pixel und unsere Werbung](#meta). Davon abgesehen nutzt die Website keine Analyse-, Werbe- oder Tracking-Werkzeuge anderer Unternehmen.',
        'Wenn Sie mit dem Sprachschalter eine Sprache wählen, merkt sich Ihr Browser diese Wahl in seinem lokalen Speicher unter dem Schlüssel „snapeyes.lang“ (der Wert ist der Sprachcode, zum Beispiel „lt“). Dieser Eintrag wird nie an uns übertragen, und Sie können ihn jederzeit in Ihren Browsereinstellungen löschen. Er ist für eine von Ihnen gewünschte Funktion unbedingt erforderlich und braucht daher keine Einwilligung (§ 25 Abs. 2 Nr. 2 TDDDG, Art. 5 Abs. 3 ePrivacy-Richtlinie).',
        'Wenn Sie über einen Link mit Preisen in einer anderen Währung zu uns kommen (zum Beispiel in australischen Dollar) oder mit unserem Währungsschalter oder in unserem Angebot von Preisen in Ihrer eigenen Währung eine Währung wählen, merkt sich Ihr Browser diese Wahl außerdem in seinem lokalen Speicher unter dem Schlüssel „snapeyes.market“ (zum Beispiel „au“, oder „eu“, wenn Sie dieses Angebot abgelehnt haben), damit die Website Ihnen weiter dieselben Preise zeigt. Unsere Seiten tragen sie in ihren Links (m=au) und senden sie mit einer Bestellung, damit Ihnen die Preise berechnet werden, die Sie gesehen haben. Sie können den Eintrag jederzeit in Ihren Browsereinstellungen löschen; er ist für eine von Ihnen gewünschte Funktion unbedingt erforderlich und braucht daher ebenfalls keine Einwilligung (§ 25 Abs. 2 Nr. 2 TDDDG, Art. 5 Abs. 3 ePrivacy-Richtlinie).',
        'Wenn wir Preise testen (nur gelegentlich und für begrenzte Zeit), speichert Ihr Browser gegebenenfalls eine zufällige anonyme Besuchernummer in seinem lokalen Speicher unter dem Schlüssel „snapeyes.vid“. Sie wird nur angelegt, solange für den Markt (die Währung), den Sie gerade ansehen, ein Preistest läuft, und wieder gelöscht, sobald kein Test mehr läuft; spätestens nach 90 Tagen wird sie ersetzt. Sie besteht aus 32 zufälligen Zeichen und dem Tag der Erstellung: Sie wird nicht aus Ihnen abgeleitet, enthält keinen Namen, keine E-Mail-Adresse und keine Gerätedaten und wird nie mit einer Bestellung verknüpft. Ihr Browser sendet sie in einem Anfrage-Header (nie in der Adresse einer Seite) an unseren Server, wenn er die Preise abfragt; unsere Anwendung verwendet sie nur, um jedes Mal auf dieselbe Weise zu bestimmen, welche der Preislisten des Tests Sie sehen, und speichert sie nicht: Wir führen keine Liste von Besuchernummern. Der Server antwortet mit einem signierten Vermerk Ihrer Preisliste, den Ihr Browser beim Wechsel zur Zahlungsseite zurücksendet, damit Ihnen genau die Preise berechnet werden, die Ihnen gezeigt wurden (ein vom Browser gesendeter Preis oder eine gesendete Preisliste wird nie verwendet). Für die Statistik erfasst unser Server anonyme Zählungen je Preisliste: dass eine Preisliste angezeigt wurde, dass eine Vorschau erstellt wurde, dass die Zahlungsseite geöffnet wurde und dass eine Bestellung bezahlt wurde (siehe [Statistiken zum Betrieb und unser Admin-Protokoll](#operations)); diese Zählungen enthalten keine Besuchernummer. Ihr Browser merkt sich im lokalen Speicher außerdem, welche dieser Zählungen er schon gesendet hat („snapeyes.expseen“), und Ihre letzte Preisliste („snapeyes.pricing“), damit sofort dieselben Preise erscheinen. Welche Preisliste Sie sehen, hängt nie davon ab, wo Sie wohnen, sondern nur vom Markt (der Währung), den Sie gewählt haben, und der Preis, den Sie zahlen, ist immer der, der Ihnen vor der Zahlung angezeigt wurde; Ihre Bestellbestätigung nennt die Preisliste, die galt. Wir verwenden diese Einträge nur für diesen Preistest, nie für Werbung und nie, um Sie über andere Websites zu verfolgen. Wenn Sie lieber nicht teilnehmen möchten, [öffnen Sie diesen Link](/?pricetest=off&lang=de): Ihr Browser behält dann nur den Vermerk „snapeyes.notest“, löscht die Besuchernummer und die übrigen hier genannten Einträge und zeigt und berechnet die Standardpreise; mit [diesem Link](/?pricetest=on&lang=de) nehmen Sie wieder teil. Sendet Ihr Browser das Signal „Global Privacy Control“, gilt auch das als diese Entscheidung. Sie können alle diese Einträge auch jederzeit in Ihren Browsereinstellungen löschen (Sie erhalten dann eine neue Zufallsauswahl). Rechtsgrundlage: unser berechtigtes Interesse an fairen Preisen (Art. 6 Abs. 1 lit. f DSGVO). Sie können jederzeit widersprechen (siehe [Ihre Rechte](#rights)).',
        'Wenn Sie über eine Werbeanzeige oder einen Link von uns mit einem Kampagnencode oder von einer anderen Website zu uns kommen, legt Ihr Browser einen kurzen Code im Sitzungsspeicher Ihres Browser-Tabs unter dem Schlüssel „snapeyes.c“ ab: die Parameter der Adresse, die die Anzeige benennen, wie ihr Ersteller sie geschrieben hat (utm_source, utm_medium, utm_campaign, utm_term und utm_content: die Plattform, die Art, die Kampagne, die Gruppe und die Anzeige; zum Beispiel „utm_source=fb&utm_medium=paid&utm_campaign=frühling“), oder, wenn es keine gibt, nur die Art der Website, von der Sie kamen (zum Beispiel „ref=facebook“: facebook, instagram, tiktok, google, direct oder other). Der Sitzungsspeicher gehört nur zu diesem einen Tab und wird gelöscht, wenn Sie ihn schließen. Der Code ist für alle gleich, die derselben Anzeige gefolgt sind: Er wird nicht aus Ihnen abgeleitet und enthält keinen Namen, keine E-Mail-Adresse, keine Gerätedaten und keine Klicknummer (eine Klicknummer „fbclid“ in der Adresse ist nie Teil davon; was mit dieser Nummer geschieht, steht unter [Das Meta-Pixel und unsere Werbung](#meta)). Unsere Seiten senden ihn mit ihren anonymen Seitenzählungen und Anfragen (Fotoprüfung, Vorschau, Zahlungsseite); der Bestelldatensatz behält ihn, und die Zahlungsseite von Stripe erhält ihn in den Metadaten der Zahlung, damit wir sehen, welche Anzeige zu welchem Schritt und zu einer Bestellung geführt hat (siehe [Betriebsstatistik und Admin-Protokoll](#operations) und [Wenn Sie bestellen](#orders)). Wir verwenden ihn nur dafür, nie für Werbung, Profilbildung oder um Sie über andere Websites zu verfolgen. Sie brauchen ihn nicht, um die Website zu nutzen: Löschen Sie ihn oder blockiert Ihr Browser den Sitzungsspeicher, funktioniert alles gleich, nur diese Zählung fehlt. Rechtsgrundlage: unser berechtigtes Interesse zu wissen, ob unsere eigene Werbung wirkt (Art. 6 Abs. 1 lit. f DSGVO). Sie können jederzeit widersprechen (siehe [Ihre Rechte](#rights)).',
        'Wenn Sie bestellen, legt die Seite außerdem zwei Einträge im Sitzungsspeicher (Session Storage) Ihres Browser-Tabs an. Der Sitzungsspeicher gehört nur zu diesem einen Tab und wird gelöscht, wenn Sie ihn schließen:',
        {
          ul: [
            '„snapeyes.order“: die Nummer der Bestellung, die Sie gerade anlegen, und ihr privater Schlüssel, damit die Seite Ihre Bestellung fortsetzen kann, etwa wenn Sie von der Zahlungsseite zurückkommen. Der Eintrag wird entfernt, wenn sich in diesem Tab die Seite Ihrer bezahlten Bestellung öffnet, und ersetzt, wenn Sie eine neue Bestellung beginnen.',
            '„snapeyes.checkout“: nur während Sie auf der Zahlungsseite sind, Ihr Kunstwerk so, wie Sie es verlassen haben (die Iris-Ausschnitte aus Ihren Fotos, die Vorschauen, einige daraus gemessene Zahlen, der Stil und seine Variante, die Anordnung, die Reihenfolge der Augen und gegebenenfalls Namen und ein Datum), damit es beim Zurückgehen von der Zahlungsseite wieder erscheint. Der Eintrag wird entfernt, sobald Sie zurückkommen oder sich in diesem Tab die Seite Ihrer bezahlten Bestellung öffnet.',
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

export const PRIVACY: LegalDocs = { en, de, lt, hu, hr, fi, et, lv };

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
          '**Your eye photos.** A photo of an eye can be biometric information, which the Australian Privacy Act 1988 treats as sensitive information when it is used to identify or verify a person. We never use it that way: we never create, compare or store an iris template or any other biometric identifier, never identify or verify anyone, never sell your photos and never use them to train AI (see [Your iris is never used to identify anyone](#iris)). We collect your eye photos only because you send them to us to make your preview and your artwork, and we use them only for that and, for up to 30 days, to check and improve the quality of our previews (see [Your free preview](#preview)).',
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
          '**Ihre Augenfotos.** Ein Foto eines Auges kann eine biometrische Information sein, die der australische Privacy Act 1988 als sensible Information behandelt, wenn sie zur Identifizierung oder Verifizierung einer Person dient. So verwenden wir sie nie: Wir erstellen, vergleichen oder speichern nie ein Iris-Template oder ein anderes biometrisches Merkmal, identifizieren oder verifizieren niemanden, verkaufen Ihre Fotos nie und nutzen sie nie zum Training von KI (siehe [Ihre Iris dient nie zur Identifizierung](#iris)). Wir erheben Ihre Augenfotos nur, weil Sie sie uns senden, damit wir Ihre Vorschau und Ihr Kunstwerk erstellen, und verwenden sie nur dafür und, bis zu 30 Tage lang, um die Qualität unserer Vorschauen zu prüfen und zu verbessern (siehe [Ihre kostenlose Vorschau](#preview)).',
          '**Wohin Ihre Daten gehen.** Wir sitzen in Litauen, Ihre Daten werden also außerhalb Australiens verarbeitet: in der EU und bei den unter [Dienste, die wir nutzen](#services) genannten Diensten, von denen einige sie in den USA oder in anderen Ländern verarbeiten können. Die Garantien für diese Übermittlungen sind dort beschrieben.',
          '**Australian Privacy Principles.** Wir behandeln Ihre Daten so, wie diese Erklärung es beschreibt, ob die Australian Privacy Principles für uns gelten oder nicht: Als kleines Unternehmen mit einem Jahresumsatz von höchstens 3 Millionen australischen Dollar sind wir nach dem Privacy Act in seiner heutigen Fassung in der Regel davon ausgenommen. Ihr Recht, wegen einer schweren Verletzung Ihrer Privatsphäre zu klagen, das seit dem 10. Juni 2025 gilt, bleibt davon unberührt.',
          `**Auskunft, Berichtigung und Beschwerden.** Sie können jederzeit Auskunft über die Daten verlangen, die wir über Sie speichern, und ihre Berichtigung (siehe [Ihre Rechte](#rights)): Schreiben Sie an ${MAIL}. Gelten die Australian Privacy Principles für uns und sind Sie mit unserer Antwort nicht zufrieden, können Sie sich beim Office of the Australian Information Commissioner ([oaic.gov.au](https://www.oaic.gov.au)) beschweren.`,
        ],
      },
    ],
  },
});

export const PRIVACY_AU: EditionDocs = { en: auEn, de: auDe };

// ------------------------------------------------------------------------------------------ the US edition
// Written from the owner's draft of 2026-10-28 and checked against what the code does (see the header): free previews are
// made in memory and never stored for a US visitor (api/_lib/keep.py keeps nothing of the market us or the country US; the EU sections' 30-day copy
// is for everyone else: the sentence "Free previews" below says so); the eye images of an order are uploaded when it starts (before the checkbox), deleted
// by the daily clean-up (api/_lib/cleanup.py) within 30 days at the latest when unpaid, 12 months after the payment when
// paid (pay.PAID_KEEP_DAYS), 14 days after an effective withdrawal; the Meta pixel and the Conversions API (section "meta") may count as
// "sharing" for targeted advertising under some state laws, which the section says.
const usEn = patchDoc(en, {
  after: {
    rights: [
      {
        id: 'united-states',
        title: 'Your data if you live in the United States',
        blocks: [
          'This policy follows the EU General Data Protection Regulation (GDPR), which applies to everything we do with your data, wherever you live. If you live in the United States, this section adds what you should know under the privacy laws of the US states.',
          "**Your eye photos.** Some US state laws (for example Illinois, Texas and Washington) protect biometric identifiers such as an iris scan. We never use your photos as one: we never create, compare or store an iris template or any other biometric identifier, never identify or verify anyone, never sell or lease your photos or share them for anyone's profit, and never use them to train AI (see [Your iris is never used to identify anyone](#iris)). We use the photos of your eyes only because you send them to us to make your preview and your artwork, and for an order you also agree to this use at checkout.",
          `**How long we keep them.** We do not store free previews, and we never store your full photo. The eye images and files of an unpaid order are deleted automatically within 30 days at the latest; those of a paid order 12 months after your payment, so that you can download your file again; those of a withdrawn order 14 days after the withdrawal. You can ask us to delete them earlier at any time: write to ${MAIL}. This schedule is public and applies to every order.`,
          '**Free previews.** The 30-day copy of the free preview described under [Your free preview](#preview) is not made for visitors in the United States: your free preview is made in memory and not stored.',
          '**Where your data goes.** We are based in Lithuania, so your data is processed in the EU and by the services named under [Services we use](#services), some of which may process it in the USA.',
          `**Your rights.** We do not sell your personal information. We use the Meta pixel and report payments to Meta to measure and show our advertisements (see [The Meta pixel and our advertisements](#meta)); under some US state laws this counts as "sharing" personal information for targeted advertising. You can object to it at any time by writing to us at ${MAIL}, and you can delete or block Meta's cookies in your browser. You can ask us at any time for access to the data we hold about you, its correction or deletion, and we answer within one month (see [Your rights](#rights)); we will not treat you differently for asking.`,
        ],
      },
    ],
  },
});

export const PRIVACY_US: EditionDocs = { en: usEn };
