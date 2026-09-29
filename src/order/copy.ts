// Every string the /order page shows, in English and German (formal "Sie", the words of /try and the landing page:
// Kunstwerk, Vorschau, Auge, Datei). The server's own sentences are English only, so the page never shows them: it
// words every answer itself from the server's reason code.
import { CONTACT_EMAIL } from '../landing/config';
import type { Lang } from '../try/lang';

const en = {
  lang: 'en' as Lang,
  meta: {
    title: 'Your order | SnapEyes',
    description: 'Your SnapEyes order: your iris artwork is made here and ready to download.',
  },
  switchLabel: 'Language',
  tag: 'Private Atelier · order',
  title: 'Your order',
  orderNo: (o: string) => `Order ${o}`,
  loading: 'Opening your order…',
  summary: {
    eyes: (n: number) => (n === 1 ? '1 eye' : `${n} eyes`),
    paid: (amount: string) => `Paid ${amount}`,
    inscription: (s: string) => `Inscription: ${s}`,
  },
  layouts: {
    single: 'Single', duo: 'Side by side', fusion: 'Fusion', triangle: 'Triangle', row: 'In a row', grid: 'Grid', galaxy: 'Galaxy',
  } as Record<string, string>,
  unpaid: {
    title: 'Not paid yet',
    body: 'We have not received a payment for this order.',
    confirming: 'We are checking your payment with Stripe…',
    expired: 'This order was not paid within 24 hours, so it can no longer be paid. Nothing was charged for it.',
    hint: 'If you have just paid, check again in a moment. Otherwise you can go back to the studio and order from there.',
    check: 'Check again',
    studio: 'Back to the studio',
  },
  pending: {
    title: 'Your payment is being confirmed',
    body: 'Your payment method takes a little longer to confirm. We start on your artwork as soon as it is confirmed. This page checks again by itself.',
  },
  making: {
    title: 'Making your artwork',
    lead: 'Your file is made at 4096 px from exactly the previews you approved. This takes about 30 seconds per eye.',
    keepOpen: 'Please keep this page open until your download is ready.',
    closeEmail: 'If you close it, open the link in your email to continue.',
    closeNoEmail: 'If you close it, open this page again at the same address to continue.',
    eye: (i: number) => `Eye ${i}`,
    done: 'Ready',
    working: 'In progress…',
    waiting: 'Waiting',
    composing: 'Putting your artwork together…',
    progress: (done: number, n: number) => `${done} of ${n} ${n === 1 ? 'eye' : 'eyes'} ready`,
    elapsed: (s: number) => `${s} s`,
  },
  wait: {
    busy: (s: number) => `The studio is busy right now. Trying again in ${s} s…`,
    network: (s: number) => `The connection was interrupted. Trying again in ${s} s…`,
    rendering: (s: number) => `This eye is already being made. Checking again in ${s} s…`,
    confirming: (s: number) => `Checking again in ${s} s…`,
  },
  review: {
    title: 'We are checking your artwork',
    body: 'We are checking your artwork by hand before it is delivered and will email you. You do not need to do anything.',
  },
  ready: {
    title: 'Your artwork is ready',
    download: 'Download the full-size file',
    open: 'Open the image',
    alt: 'Your SnapEyes artwork',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} MB`,
    link: 'The download link works for 7 days. Open this page again at any time for a fresh link: we keep your file for 12 months.',
    email: 'The link to this page is also in your email.',
    bookmark: 'Keep the address of this page: it is your access to your file.',
  },
  deleted: {
    title: 'Files deleted',
    body: `The files of this order were deleted. Write to ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Something went wrong',
    bad_link: `This order link is not valid. Please open the link from your email again, or write to ${CONTACT_EMAIL}.`,
    missing: `This page needs the full link from your email or from the payment page. If you cannot find it, write to ${CONTACT_EMAIL}.`,
    network: 'We could not reach SnapEyes. Please check your internet connection and try again.',
    busy: 'The studio is very busy right now. Please try again in a few minutes.',
    failed: `Something went wrong on our side. Please try again. If it happens again, write to ${CONTACT_EMAIL} with your order number.`,
    retry: 'Try again',
  },
  contact: {
    lead: 'Questions about your order?',
    write: (email: string) => `Write to ${email}`,
    subject: (o: string) => `SnapEyes order ${o}`,
  },
};

export type OrderCopy = typeof en;

const de: OrderCopy = {
  lang: 'de',
  meta: {
    title: 'Ihre Bestellung | SnapEyes',
    description: 'Ihre SnapEyes-Bestellung: Hier wird Ihr Iris-Kunstwerk erstellt und steht zum Download bereit.',
  },
  switchLabel: 'Sprache',
  tag: 'Private Atelier · Bestellung',
  title: 'Ihre Bestellung',
  orderNo: (o: string) => `Bestellung ${o}`,
  loading: 'Ihre Bestellung wird geöffnet…',
  summary: {
    eyes: (n: number) => (n === 1 ? '1 Auge' : `${n} Augen`),
    paid: (amount: string) => `Bezahlt: ${amount}`,
    inscription: (s: string) => `Widmung: ${s}`,
  },
  layouts: {
    single: 'Einzeln', duo: 'Nebeneinander', fusion: 'Fusion', triangle: 'Dreieck', row: 'In einer Reihe', grid: 'Raster', galaxy: 'Galaxie',
  },
  unpaid: {
    title: 'Noch nicht bezahlt',
    body: 'Für diese Bestellung ist bei uns noch keine Zahlung eingegangen.',
    confirming: 'Wir prüfen Ihre Zahlung bei Stripe…',
    expired: 'Diese Bestellung wurde nicht innerhalb von 24 Stunden bezahlt und kann daher nicht mehr bezahlt werden. Dafür wurde nichts berechnet.',
    hint: 'Wenn Sie gerade bezahlt haben, prüfen Sie es gleich noch einmal. Andernfalls können Sie zurück ins Studio gehen und dort bestellen.',
    check: 'Erneut prüfen',
    studio: 'Zurück ins Studio',
  },
  pending: {
    title: 'Ihre Zahlung wird bestätigt',
    body: 'Ihre Zahlungsart braucht etwas länger für die Bestätigung. Sobald die Zahlung bestätigt ist, beginnen wir mit Ihrem Kunstwerk. Diese Seite prüft das von selbst.',
  },
  making: {
    title: 'Ihr Kunstwerk wird erstellt',
    lead: 'Ihre Datei wird mit 4096 px aus genau den Vorschauen erstellt, die Sie freigegeben haben. Das dauert etwa 30 Sekunden pro Auge.',
    keepOpen: 'Bitte lassen Sie diese Seite geöffnet, bis Ihr Download bereit ist.',
    closeEmail: 'Wenn Sie sie schließen, öffnen Sie den Link aus Ihrer E-Mail, um fortzufahren.',
    closeNoEmail: 'Wenn Sie sie schließen, öffnen Sie diese Seite unter derselben Adresse erneut, um fortzufahren.',
    eye: (i: number) => `Auge ${i}`,
    done: 'Fertig',
    working: 'In Arbeit…',
    waiting: 'Wartet',
    composing: 'Ihr Kunstwerk wird zusammengesetzt…',
    progress: (done: number, n: number) => `${done} von ${n} ${n === 1 ? 'Auge' : 'Augen'} fertig`,
    elapsed: (s: number) => `${s} s`,
  },
  wait: {
    busy: (s: number) => `Das Studio ist gerade ausgelastet. Neuer Versuch in ${s} s…`,
    network: (s: number) => `Die Verbindung wurde unterbrochen. Neuer Versuch in ${s} s…`,
    rendering: (s: number) => `Dieses Auge wird bereits erstellt. Erneute Prüfung in ${s} s…`,
    confirming: (s: number) => `Erneute Prüfung in ${s} s…`,
  },
  review: {
    title: 'Wir prüfen Ihr Kunstwerk',
    body: 'Wir prüfen Ihr Kunstwerk vor der Auslieferung von Hand und schreiben Ihnen eine E-Mail. Sie müssen nichts weiter tun.',
  },
  ready: {
    title: 'Ihr Kunstwerk ist fertig',
    download: 'Datei in voller Größe herunterladen',
    open: 'Bild öffnen',
    alt: 'Ihr SnapEyes-Kunstwerk',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} MB`,
    link: 'Der Download-Link gilt 7 Tage. Sie können diese Seite jederzeit erneut öffnen und erhalten dann einen neuen Link: Wir bewahren Ihre Datei 12 Monate auf.',
    email: 'Den Link zu dieser Seite finden Sie auch in Ihrer E-Mail.',
    bookmark: 'Bewahren Sie die Adresse dieser Seite auf: Sie ist Ihr Zugang zu Ihrer Datei.',
  },
  deleted: {
    title: 'Dateien gelöscht',
    body: `Die Dateien dieser Bestellung wurden gelöscht. Schreiben Sie an ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Etwas ist schiefgelaufen',
    bad_link: `Dieser Bestelllink ist ungültig. Bitte öffnen Sie den Link aus Ihrer E-Mail erneut oder schreiben Sie an ${CONTACT_EMAIL}.`,
    missing: `Diese Seite braucht den vollständigen Link aus Ihrer E-Mail oder von der Zahlungsseite. Falls Sie ihn nicht finden, schreiben Sie an ${CONTACT_EMAIL}.`,
    network: 'Wir konnten SnapEyes nicht erreichen. Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.',
    busy: 'Das Studio ist gerade sehr ausgelastet. Bitte versuchen Sie es in ein paar Minuten erneut.',
    failed: `Bei uns ist etwas schiefgelaufen. Bitte versuchen Sie es erneut. Wenn es wieder passiert, schreiben Sie mit Ihrer Bestellnummer an ${CONTACT_EMAIL}.`,
    retry: 'Erneut versuchen',
  },
  contact: {
    lead: 'Fragen zu Ihrer Bestellung?',
    write: (email: string) => `Schreiben Sie an ${email}`,
    subject: (o: string) => `SnapEyes-Bestellung ${o}`,
  },
};

export const ORDER_COPY: Record<Lang, OrderCopy> = { en, de };

// as the landing page writes a price (src/landing/copy.ts formatEuro): "€39.97" in English, "39,97 €" in German
export const euroOf = (cents: number, lang: Lang) =>
  new Intl.NumberFormat(lang === 'de' ? 'de-DE' : 'en-IE', { style: 'currency', currency: 'EUR' }).format(cents / 100);

/** Megabytes with one decimal, as the language writes it. */
export const mbOf = (bytes: number, lang: Lang) =>
  new Intl.NumberFormat(lang === 'de' ? 'de-DE' : 'en-IE', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(bytes / 1_000_000);
