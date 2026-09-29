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
    // paid, but the order confirmation email (it confirms the withdrawal waiver) has not gone out yet: nothing is made
    // before it has (api/order.py status: state "pending", waiting_for "confirmation_email")
    mailTitle: 'Payment received',
    mailBody: 'Your payment is confirmed. We are sending your order confirmation by email and start on your artwork right after. This page checks again by itself.',
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
  // The online withdrawal function (Art. 11a Directive 2011/83/EU as amended by Directive (EU) 2023/2673; § 356a
  // BGB): a button labelled with the statutory words, a short statement form (name, contract, email for the receipt),
  // and a second button with the statutory words that sends it (./WithdrawPanel.tsx). The two button labels are
  // src/shared/legal.ts WITHDRAWAL_ONLINE, which the legal pages quote.
  withdraw: {
    heading: 'Withdraw from the contract',
    lead: 'At checkout you agreed that we start making your file right away. Until we have started, you can withdraw from this contract here. Once making has started, your right of withdrawal has ended.',
    info: 'Right of withdrawal',
    formLead: (confirm: string) => `Please check your details. With "${confirm}" you send us this statement:`,
    statement: (o: string) => `I hereby withdraw from the contract I concluded for the supply of the following digital content: SnapEyes artwork, order ${o}.`,
    statementNoOrder: 'I hereby withdraw from the contract I concluded for the supply of the following digital content: SnapEyes artwork, the order named below.',
    name: 'Your name',
    email: 'Email address for the confirmation',
    emailHint: 'We send the confirmation of receipt, with the date and time, to this address.',
    emailHintNoLink: 'Please use the email address you paid with: it shows us that the order is yours. We send the confirmation of receipt, with the date and time, to this address.',
    order: 'Order number',
    orderHint: 'You find it in your order confirmation email and on the order page.',
    sending: 'Sending your withdrawal…',
    cancel: 'Cancel',
    back: 'Back to your order',
    invalid: {
      name: 'Please enter your name.',
      email: 'Please enter a valid email address.',
      order: 'Please enter your order number as it appears in your email.',
    },
    errors: {
      network: 'We could not reach SnapEyes, so we cannot tell whether your withdrawal arrived. Please check your connection and try again: sending it again does no harm.',
      busy: `Our system is busy right now, so your withdrawal could not be recorded. Please try again in a moment, or write your withdrawal to ${CONTACT_EMAIL}: an email is just as valid.`,
      unmatched: (when: string | null) => `We could not match your statement to an order with these details. We have kept it${when ? ` (received on ${when})` : ''} and check it by hand. Please check the order number and, if you came without the link to your order, use the email address you paid with. You can also write to ${CONTACT_EMAIL}.`,
      // api/_lib/withdraw.py 409 no_order: nothing was stored, so nothing here may say it was kept
      no_order: `We could not find an order with this number; nothing was recorded. Check it or write to ${CONTACT_EMAIL}.`,
      not_paid: 'This order was never paid, so there is no contract to withdraw from. Nothing was charged.',
      invalid: 'Please check your name and email address and try again.',
      paused: `We cannot take online withdrawals at the moment. Please write your withdrawal to ${CONTACT_EMAIL}: an email is just as valid.`,
      too_many: `We have already received several withdrawal statements for this order today. If something is missing, please write to ${CONTACT_EMAIL}.`,
      failed: `Your withdrawal could not be sent. Please try again, or write your withdrawal to ${CONTACT_EMAIL}: an email is just as valid.`,
    },
    done: {
      effectiveTitle: 'Your withdrawal was received',
      lapsedTitle: 'Your statement was received',
      checking: 'We now check your order by hand and email you the result.',
      received: (when: string) => `We received your withdrawal on ${when}.`,
      effective: 'Your contract is withdrawn. We do not make your file.',
      refund: (amount: string) => `We refund the ${amount} you paid to the payment method you used, within 14 days at the latest.`,
      refundNoAmount: 'We refund what you paid to the payment method you used, within 14 days at the latest.',
      refundBy: (amount: string, date: string) => `We refund the ${amount} you paid to the payment method you used, by ${date} at the latest. You pay no fees for this.`,
      settling: 'Your payment was still being processed when you withdrew. If it reaches us, we refund it in full to the payment method you used, within 14 days at the latest.',
      refundStarted: (amount: string) => `The refund of ${amount} to the payment method you used has been started. Depending on your bank it can take a few days to arrive.`,
      lapsed: 'Making your file had already started. At checkout you agreed that we start right away and confirmed that you lose your right of withdrawal once we have started, so the right had already ended. Your order stays in place: you find your file on your order page.',
      lapsedPeriod: 'The 14-day withdrawal period for this order had already ended, so your right of withdrawal had ended when your statement arrived.',
      lapsedHelp: 'We still look at your statement personally and reply to you by email. Your statutory rights for a defective file are not affected.',
      mailSent: (email: string) => `A confirmation of receipt is on its way to ${email}.`,
      mailRedirected: 'A confirmation of receipt is on its way to the email address you paid with.',
      mailLater: (email: string) => `We could not send the confirmation of receipt to ${email} just now. We send it as soon as we can. Your withdrawal counts from the time above.`,
      mailFailed: (email: string) => `We could not send the confirmation of receipt to ${email}. Your withdrawal is on record from the time above. Please check that address, or write to ${CONTACT_EMAIL} for a copy.`,
    },
    withdrawn: {
      title: 'This order was withdrawn',
      body: (when: string) => `Your withdrawal was received on ${when}. Nothing is made for this order.`,
      bodyNoTime: 'Your withdrawal was received. Nothing is made for this order.',
    },
    unpaid: 'This order is not paid, so there is no contract to withdraw from. Nothing was charged.',
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
    mailTitle: 'Zahlung eingegangen',
    mailBody: 'Ihre Zahlung ist bestätigt. Wir senden Ihnen jetzt die Bestellbestätigung per E-Mail und beginnen direkt danach mit Ihrem Kunstwerk. Diese Seite prüft das von selbst.',
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
  withdraw: {
    heading: 'Vertrag widerrufen',
    lead: 'Sie haben bei der Bestellung zugestimmt, dass wir sofort mit der Erstellung Ihrer Datei beginnen. Solange wir noch nicht begonnen haben, können Sie diesen Vertrag hier widerrufen. Sobald die Erstellung begonnen hat, ist Ihr Widerrufsrecht erloschen.',
    info: 'Widerrufsbelehrung',
    formLead: (confirm: string) => `Bitte prüfen Sie Ihre Angaben. Mit „${confirm}“ senden Sie uns diese Erklärung:`,
    statement: (o: string) => `Hiermit widerrufe ich den von mir abgeschlossenen Vertrag über die Bereitstellung der folgenden digitalen Inhalte: SnapEyes-Kunstwerk, Bestellung ${o}.`,
    statementNoOrder: 'Hiermit widerrufe ich den von mir abgeschlossenen Vertrag über die Bereitstellung der folgenden digitalen Inhalte: SnapEyes-Kunstwerk, Bestellung wie unten angegeben.',
    name: 'Ihr Name',
    email: 'E-Mail-Adresse für die Bestätigung',
    emailHint: 'An diese Adresse senden wir die Eingangsbestätigung mit Datum und Uhrzeit.',
    emailHintNoLink: 'Bitte verwenden Sie die E-Mail-Adresse, mit der Sie bezahlt haben: Daran erkennen wir, dass die Bestellung Ihre ist. An diese Adresse senden wir die Eingangsbestätigung mit Datum und Uhrzeit.',
    order: 'Bestellnummer',
    orderHint: 'Sie finden sie in Ihrer Bestellbestätigung per E-Mail und auf der Bestellseite.',
    sending: 'Ihr Widerruf wird gesendet…',
    cancel: 'Abbrechen',
    back: 'Zurück zu Ihrer Bestellung',
    invalid: {
      name: 'Bitte geben Sie Ihren Namen ein.',
      email: 'Bitte geben Sie eine gültige E-Mail-Adresse ein.',
      order: 'Bitte geben Sie Ihre Bestellnummer so ein, wie sie in Ihrer E-Mail steht.',
    },
    errors: {
      network: 'Wir konnten SnapEyes nicht erreichen und wissen daher nicht, ob Ihr Widerruf angekommen ist. Bitte prüfen Sie Ihre Verbindung und versuchen Sie es erneut: Ein erneutes Senden schadet nicht.',
      busy: `Unser System ist gerade ausgelastet, daher konnte Ihr Widerruf nicht erfasst werden. Bitte versuchen Sie es gleich noch einmal oder senden Sie Ihren Widerruf an ${CONTACT_EMAIL}: Eine E-Mail ist genauso gültig.`,
      unmatched: (when: string | null) => `Wir konnten Ihre Erklärung keiner Bestellung mit diesen Angaben zuordnen. Wir haben sie${when ? ` (eingegangen am ${when})` : ''} aufbewahrt und prüfen sie von Hand. Bitte prüfen Sie die Bestellnummer und verwenden Sie, wenn Sie ohne den Link zu Ihrer Bestellung gekommen sind, die E-Mail-Adresse, mit der Sie bezahlt haben. Sie können auch an ${CONTACT_EMAIL} schreiben.`,
      no_order: `Wir konnten keine Bestellung mit dieser Nummer finden; es wurde nichts erfasst. Bitte prüfen Sie die Nummer oder schreiben Sie an ${CONTACT_EMAIL}.`,
      not_paid: 'Diese Bestellung wurde nie bezahlt, daher gibt es keinen Vertrag, den Sie widerrufen könnten. Es wurde nichts berechnet.',
      invalid: 'Bitte prüfen Sie Ihren Namen und Ihre E-Mail-Adresse und versuchen Sie es erneut.',
      paused: `Online-Widerrufe sind gerade nicht möglich. Bitte senden Sie Ihren Widerruf an ${CONTACT_EMAIL}: Eine E-Mail ist genauso gültig.`,
      too_many: `Für diese Bestellung sind heute bereits mehrere Widerrufserklärungen eingegangen. Falls etwas fehlt, schreiben Sie bitte an ${CONTACT_EMAIL}.`,
      failed: `Ihr Widerruf konnte nicht gesendet werden. Bitte versuchen Sie es erneut oder senden Sie Ihren Widerruf an ${CONTACT_EMAIL}: Eine E-Mail ist genauso gültig.`,
    },
    done: {
      effectiveTitle: 'Ihr Widerruf ist eingegangen',
      lapsedTitle: 'Ihre Erklärung ist eingegangen',
      checking: 'Wir prüfen Ihre Bestellung jetzt von Hand und teilen Ihnen das Ergebnis per E-Mail mit.',
      received: (when: string) => `Ihr Widerruf ist am ${when} bei uns eingegangen.`,
      effective: 'Ihr Vertrag ist widerrufen. Wir erstellen Ihre Datei nicht.',
      refund: (amount: string) => `Wir erstatten Ihnen die gezahlten ${amount} über das Zahlungsmittel, mit dem Sie bezahlt haben, spätestens binnen 14 Tagen.`,
      refundNoAmount: 'Wir erstatten Ihnen den gezahlten Betrag über das Zahlungsmittel, mit dem Sie bezahlt haben, spätestens binnen 14 Tagen.',
      refundBy: (amount: string, date: string) => `Wir erstatten Ihnen die gezahlten ${amount} über das Zahlungsmittel, mit dem Sie bezahlt haben, spätestens bis zum ${date}. Dafür fallen für Sie keine Gebühren an.`,
      settling: 'Ihre Zahlung war bei Ihrem Widerruf noch in Bearbeitung. Falls sie eingeht, erstatten wir sie Ihnen vollständig über das Zahlungsmittel, mit dem Sie bezahlt haben, spätestens binnen 14 Tagen.',
      refundStarted: (amount: string) => `Die Erstattung von ${amount} über das Zahlungsmittel, mit dem Sie bezahlt haben, ist veranlasst. Je nach Bank kann es einige Tage dauern, bis sie ankommt.`,
      lapsed: 'Die Erstellung Ihrer Datei hatte bereits begonnen. Sie haben bei der Bestellung zugestimmt, dass wir sofort beginnen, und bestätigt, dass Sie Ihr Widerrufsrecht mit Beginn der Erstellung verlieren. Ihr Widerrufsrecht war daher bereits erloschen. Ihre Bestellung bleibt bestehen: Ihre Datei finden Sie auf Ihrer Bestellseite.',
      lapsedPeriod: 'Die 14-tägige Widerrufsfrist für diese Bestellung war bereits abgelaufen. Ihr Widerrufsrecht war daher bei Eingang Ihrer Erklärung bereits erloschen.',
      lapsedHelp: 'Wir sehen uns Ihre Erklärung trotzdem persönlich an und antworten Ihnen per E-Mail. Ihre gesetzlichen Rechte bei einer mangelhaften Datei bleiben unberührt.',
      mailSent: (email: string) => `Eine Eingangsbestätigung ist an ${email} unterwegs.`,
      mailRedirected: 'Eine Eingangsbestätigung ist an die E-Mail-Adresse unterwegs, mit der Sie bezahlt haben.',
      mailLater: (email: string) => `Wir konnten die Eingangsbestätigung an ${email} gerade nicht senden. Wir senden sie, sobald es geht. Ihr Widerruf gilt ab dem oben genannten Zeitpunkt.`,
      mailFailed: (email: string) => `Wir konnten die Eingangsbestätigung nicht an ${email} senden. Ihr Widerruf ist ab dem oben genannten Zeitpunkt erfasst. Bitte prüfen Sie diese Adresse oder schreiben Sie an ${CONTACT_EMAIL}, wenn Sie eine Kopie möchten.`,
    },
    withdrawn: {
      title: 'Diese Bestellung wurde widerrufen',
      body: (when: string) => `Ihr Widerruf ist am ${when} bei uns eingegangen. Für diese Bestellung wird nichts erstellt.`,
      bodyNoTime: 'Ihr Widerruf ist bei uns eingegangen. Für diese Bestellung wird nichts erstellt.',
    },
    unpaid: 'Diese Bestellung ist nicht bezahlt, daher gibt es keinen Vertrag, den Sie widerrufen könnten. Es wurde nichts berechnet.',
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

/** A day in the language's own words (the date a refund is due by). */
export const dateOf = (unixSeconds: number, lang: Lang) =>
  new Intl.DateTimeFormat(lang === 'de' ? 'de-DE' : 'en-GB', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(unixSeconds * 1000));

/** A moment in the language's own words, with its time zone (the withdrawal receipt names the date and time). */
export const whenOf = (unixSeconds: number, lang: Lang) =>
  new Intl.DateTimeFormat(lang === 'de' ? 'de-DE' : 'en-GB', {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
  }).format(new Date(unixSeconds * 1000));
