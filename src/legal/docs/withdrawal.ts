// Right of withdrawal: the statutory information for digital content not supplied on a tangible medium (model
// wording of Annex I(A) Directive 2011/83/EU as amended by Directives (EU) 2019/2161 and 2023/2673; German:
// Muster-Widerrufsbelehrung, Anlage 1 zu Art. 246a § 1 Abs. 2 EGBGB in the version in force since 19.06.2026), the
// early expiry (Art. 16(m) Directive 2011/83/EU, § 356 Abs. 5 BGB) and the model withdrawal form (Annex I(B);
// Anlage 2). The checkbox text is imported from src/shared/legal.ts, the same text the checkout shows.
// The model sentences are kept word for word, including the delivery-cost clause of "Effects of withdrawal" (there
// are no delivery costs, but leaving it out would make this no longer the unchanged statutory model). The model form
// keeps only its own alternatives (goods / service): no added line, and its "To:" line is formLine (name, address,
// email: exactly what Annex I(B) and Anlage 2 ask for).
// The "[2]" contact details: the model asks for name, address, telephone number and email (Annex I(A) note 2;
// Gestaltungshinweis 2). The OWNER DECIDED TO SHOW NO PHONE (PHONE_OMITTED_BY_OWNER, src/landing/config.ts), so
// contactLine prints name, address and email only; this one deviation from the model is a risk the owner accepted.
// We are obliged to offer the online withdrawal function (Art. 11a Directive 2011/83/EU, § 356a BGB), so "right"
// carries the model sentence for exactly that case, not the older sentence for an optional web form:
//  - German: Gestaltungshinweis 3, first alternative, as replaced by Art. 2 Nr. 7 of the law of 03.02.2026 (BGBl.
//    2026 I Nr. 28), word for word; checked 2026-09-29 against gesetze-im-internet.de and buzer.de.
//  - English: Annex I(A) instruction 3 as replaced by Annex I of Directive (EU) 2023/2673, word for word; checked
//    2026-09-29 against the Official Journal text (OJ L, 2023/2673, 28.11.2023, from publications.europa.eu). The
//    third paragraph uses the wording of Directive (EU) 2019/2161 ("a letter sent by post or email").
// The inserted place is the function's address and its button (withdrawFunctionAddress, WITHDRAWAL_ONLINE,
// withdrawFunctionHref in src/shared/legal.ts, the ones the order page's form uses), which the model allows ("internet
// address or another appropriate explanation of where the withdrawal function is available").
// WHEN THE RIGHT ENDS, as api/_lib/withdraw.py decides it (keep both in step):
//  - once making the file begins (withdraw.py _began: making.json, delivery.json or a stored eye; api/order.py make
//    writes making.json at the first render, which it starts only after the order confirmation email went out), with
//    the recorded consent and that confirmation sent first ("lapsed, making_began"); making that began without them
//    does not end it ("withdrawn, began_without_confirmation")
//  - otherwise when the 14-day period is over ("lapsed, period_over"): withdraw.py period_end() does not count the
//    day of payment, ends the period at the end of the 14th day after it, and moves a last day on a Saturday, a
//    Sunday or a public holiday to the next working day (Regulation 1182/71 Art. 3(4), § 193 BGB; the server knows
//    the national holidays of Lithuania and Germany, and the owner looks at every lapsed statement by hand, so a
//    customer's own holiday elsewhere is answered personally), taking the latest end anywhere in the EU. The texts
//    keep the statutory sentence ("14 days from the day of the conclusion of the contract") and add only these two
//    counting rules, in the words of the Regulation ("working day" / "Arbeitstag": not a Saturday, Sunday or
//    holiday); the terms' "withdrawal" section says the same
//  - an order never paid has no contract (409 not_paid, no receipt); one whose payment is still settling is stopped and
//    refunded if the payment arrives ("withdrawn, payment_settling")
// The "online" section describes the function as api/order.py action "withdraw" (api/_lib/withdraw.py) runs it:
// receipts and their limits (withdraw.py _receipt_to: RECEIPT_ADDR_MAX = 2 a day and RECEIPT_ADDR_MONTH_MAX = 4 a
// month to one address for statements that match no order; RECEIPT_OTHER_MAX = 3 per order to addresses other than
// the payment email, then the payment email; REPEAT_RECEIPT_ORDER_MAX = 1 a day per order and REPEAT_RECEIPT_DAY_MAX
// = 5 a day on the whole site for repeats), and the refusals that
// ask for an email instead (503 withdraw_paused, 429 too_many, storage errors). On a deployment that cannot sell yet
// (pay.sells() false) a statement naming no stored order is not recorded (409 no_order); no contract can exist there,
// so the texts, which describe the shop while it sells, do not mention it.
// Not reviewed by a lawyer.
// WITHDRAWAL_AU (the end of this file) is the Australian edition (src/shared/legal.ts legalEdition "au"): the same
// statutory EU text, with a lead that frames it as the EU right to cancel for a change of mind (never as "no refunds":
// the Australian Consumer Law's guarantees cannot be excluded), the Australian checkbox text in its box and links to
// the terms' "Your rights in Australia".
import type { Block, LegalDoc, LegalDocs, LegalSection } from '../types';
import { CHECKOUT_LEGAL, CHECKOUT_LEGAL_AU, WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';
import { CONTACT_EMAIL, contactLine, formLine } from '../facts';
import { patchDoc } from '../patch';

const W = WITHDRAWAL_ONLINE;

const en: LegalDoc = {
  title: 'Right of withdrawal',
  description:
    'Withdrawal information for SnapEyes digital files: the 14-day right of withdrawal, when it ends early, and a model withdrawal form.',
  lead:
    'Consumers in the EU have a right of withdrawal for purchases made online. For a digital file like ours, it ends early once we start making your file with your consent. Here is the full information.',
  sections: [
    {
      id: 'right',
      title: 'Right of withdrawal',
      blocks: [
        'You have the right to withdraw from this contract within 14 days without giving any reason.',
        'The withdrawal period will expire after 14 days from the day of the conclusion of the contract.',
        `To exercise the right of withdrawal, you must inform us (${contactLine('en')}) of your decision to withdraw from this contract by an unequivocal statement (e.g. a letter sent by post or email). You may use the attached model withdrawal form, but it is not obligatory. You can also exercise your right of withdrawal online at [${withdrawFunctionAddress('en')}](${withdrawFunctionHref('en')}) (the button "${W.en.button}"). If you use this online feature, we will send you an acknowledgement of receipt of the withdrawal on a durable medium (e.g. by email), including its content and the date and time of its submission, without undue delay.`,
        'To meet the withdrawal deadline, it is sufficient for you to send your communication concerning your exercise of the right of withdrawal before the withdrawal period has expired.',
      ],
    },
    {
      id: 'effects',
      title: 'Effects of withdrawal',
      blocks: [
        'If you withdraw from this contract, we shall reimburse to you all payments received from you, including the costs of delivery (with the exception of the supplementary costs resulting from your choice of a type of delivery other than the least expensive type of standard delivery offered by us), without undue delay and in any event not later than 14 days from the day on which we are informed about your decision to withdraw from this contract. We will carry out such reimbursement using the same means of payment as you used for the initial transaction, unless you have expressly agreed otherwise; in any event, you will not incur any fees as a result of such reimbursement.',
      ],
    },
    {
      id: 'expiry',
      title: 'When the right of withdrawal ends early',
      blocks: [
        '**Your right of withdrawal ends early** once we have begun the performance of the contract, that is, once we have started making your file, if (1) you expressly agreed that we begin the performance before the withdrawal period ends, (2) you acknowledged that you thereby lose your right of withdrawal once we have begun, and (3) we have confirmed this to you on a durable medium (we do so in the order confirmation email, which goes out before we start). This follows from Art. 16(m) of Directive 2011/83/EU.',
        'Before you pay, you give this consent by ticking this box:',
        { box: [CHECKOUT_LEGAL.en.withdrawalConsent], label: 'The checkbox at checkout' },
        'In practice your right of withdrawal therefore ends at the moment we start making your file. We start only after your order confirmation email has gone out, normally within a minute of your payment, while your order page is open: the payment page takes you straight there. If you are not on your order page by then, we start when you open it again with the order page link in that email. The withdrawal link in the same email opens the online withdrawal function for your order without starting anything. From the moment we start, your right of withdrawal has ended, even while your file is still being made or is waiting for our quality check. If we have not started making your file, your right of withdrawal ends when the 14-day withdrawal period is over: the day of your payment is not counted, and if the last day of the period is a Saturday, a Sunday or a public holiday, the period ends at the end of the next working day. Your statutory rights for a defective file are not affected: see [Complaints and defects](doc:terms#defects) in our terms of sale.',
      ],
    },
    {
      id: 'online',
      title: 'Withdraw online',
      blocks: [
        `While your right of withdrawal lasts, you can withdraw online at any time with the function ["${W.en.button}"](${withdrawFunctionHref('en')}). You find it at the foot of our home page and of our legal pages, on your order page, and behind the withdrawal link in your order confirmation email. That link opens the function for your order without starting anything. Opening your order page itself starts making your file once your order confirmation email has gone out, and that ends your right of withdrawal (see [When the right of withdrawal ends early](#expiry)).`,
        `How it works: enter your name, your order number (it is filled in when you come from your order page or through the withdrawal link) and the email address for the acknowledgement, then send your withdrawal with the button "${W.en.confirm}". If you come without one of these links, please give the email address you paid with, so that we can match your order. If the details match none of our orders, the page tells you so; we still keep your statement, check it by hand and email you an acknowledgement of receipt. To prevent misuse of our emails, acknowledgements of receipt are limited: for statements that match none of our orders, to two a day and four a month to the same address; for an order, to three in all to addresses other than the one it was paid with (further ones go to the address you paid with); and for a repeated statement about an order we have already answered, to one a day for that order and five a day for all orders together. If the page cannot take your statement, for example because of a technical fault or because unusually many statements are arriving, it tells you so: please then send us your withdrawal by email; an email is just as valid.`,
        'What happens then: we record your statement with the date and time it reached us. If your order is paid, we have not started making your file and the 14-day withdrawal period is not over, your withdrawal takes effect: we stop your order, so nothing is made, and we refund you as described under [Effects of withdrawal](#effects). If your payment was still being processed when you withdrew, nothing is made either, and if the payment reaches us, we refund it in full. Without delay we email you an acknowledgement of receipt with the content of your withdrawal and its date and time.',
        'If we had already started making your file with your consent, or the 14-day withdrawal period was over, your right of withdrawal had already ended (see [When the right of withdrawal ends early](#expiry)): the page and the acknowledgement of receipt tell you so, and we still look at your statement personally. If your order was never paid, there is no contract to withdraw from: the page tells you so, and nothing was charged. Your rights for a defective file are not affected.',
      ],
    },
    {
      id: 'form',
      title: 'Model withdrawal form',
      blocks: [
        '(Complete and return this form only if you wish to withdraw from the contract.)',
        {
          box: [
            `To: ${formLine('en')}`,
            'I/We (*) hereby give notice that I/We (*) withdraw from my/our (*) contract of sale of the following goods (*)/for the provision of the following service (*):',
            'Ordered on (*)/received on (*):',
            'Name of consumer(s):',
            'Address of consumer(s):',
            'Signature of consumer(s) (only if this form is notified on paper):',
            'Date:',
            '(*) Delete as appropriate.',
          ],
        },
        `By email, simply send the completed form, or your own statement, to [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Withdrawal). Please add your order number if you have it. Online, use the function ["${W.en.button}"](${withdrawFunctionHref('en')}) described above.`,
      ],
    },
  ],
};

const de: LegalDoc = {
  title: 'Widerrufs\u00ADbelehrung',
  description:
    'Widerrufsbelehrung für digitale Dateien von SnapEyes: das 14-tägige Widerrufsrecht, wann es vorzeitig erlischt, und ein Muster-Widerrufsformular.',
  lead:
    'Verbraucher in der EU haben bei Online-Käufen ein Widerrufsrecht. Bei einer digitalen Datei wie unserer erlischt es vorzeitig, sobald wir mit Ihrer Zustimmung mit der Erstellung Ihrer Datei beginnen. Hier finden Sie alle Informationen.',
  sections: [
    {
      id: 'right',
      title: 'Widerrufsrecht',
      blocks: [
        'Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen.',
        'Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses.',
        `Um Ihr Widerrufsrecht auszuüben, müssen Sie uns (${contactLine('de')}) mittels einer eindeutigen Erklärung (z.\u00a0B. ein mit der Post versandter Brief oder eine E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür das beigefügte Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben ist. Sie können Ihr Widerrufsrecht auch online unter [${withdrawFunctionAddress('de')}](${withdrawFunctionHref('de')}) (Schaltfläche „${W.de.button}“) ausüben. Wenn Sie diese Online-Funktion nutzen, übermitteln wir Ihnen auf einem dauerhaften Datenträger (z.\u00a0B. durch eine E-Mail) unverzüglich eine Eingangsbestätigung mit Informationen zum Inhalt der Widerrufserklärung sowie dem Datum und der Uhrzeit ihres Eingangs.`,
        'Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.',
      ],
    },
    {
      id: 'effects',
      title: 'Folgen des Widerrufs',
      blocks: [
        'Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, einschließlich der Lieferkosten (mit Ausnahme der zusätzlichen Kosten, die sich daraus ergeben, dass Sie eine andere Art der Lieferung als die von uns angebotene, günstigste Standardlieferung gewählt haben), unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung verwenden wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte berechnet.',
      ],
    },
    {
      id: 'expiry',
      title: 'Vorzeitiges Erlöschen des Widerrufsrechts',
      blocks: [
        '**Ihr Widerrufsrecht erlischt vorzeitig**, sobald wir mit der Vertragserfüllung begonnen haben, also mit der Erstellung Ihrer Datei, wenn Sie (1) ausdrücklich zugestimmt haben, dass wir vor Ablauf der Widerrufsfrist mit der Vertragserfüllung beginnen, (2) Ihre Kenntnis davon bestätigt haben, dass Sie durch Ihre Zustimmung mit Beginn der Vertragserfüllung Ihr Widerrufsrecht verlieren, und (3) wir Ihnen dies auf einem dauerhaften Datenträger bestätigt haben (das tun wir mit der Bestellbestätigung per E-Mail, die versandt wird, bevor wir beginnen). Das ergibt sich aus § 356 Abs. 5 BGB und Art. 16 Buchst. m der Richtlinie 2011/83/EU.',
        'Vor der Zahlung geben Sie diese Zustimmung, indem Sie in diesem Kästchen das Häkchen setzen:',
        { box: [CHECKOUT_LEGAL.de.withdrawalConsent], label: 'Das Kästchen im Bestellvorgang' },
        'In der Praxis erlischt Ihr Widerrufsrecht daher in dem Moment, in dem wir mit der Erstellung Ihrer Datei beginnen. Wir beginnen erst, nachdem Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise innerhalb einer Minute nach Ihrer Zahlung, während Ihre Bestellseite geöffnet ist: Die Zahlungsseite führt Sie direkt dorthin. Sind Sie bis dahin nicht auf Ihrer Bestellseite, beginnen wir, wenn Sie sie mit dem Link zu Ihrer Bestellseite aus dieser E-Mail wieder öffnen. Der Widerrufslink in derselben E-Mail öffnet die Online-Widerrufsfunktion für Ihre Bestellung, ohne etwas zu starten. Ab dem Moment, in dem wir beginnen, ist Ihr Widerrufsrecht erloschen, auch wenn Ihre Datei noch erstellt wird oder auf unsere Qualitätsprüfung wartet. Haben wir mit Ihrer Datei noch nicht begonnen, erlischt Ihr Widerrufsrecht mit Ablauf der 14-tägigen Widerrufsfrist: Der Tag Ihrer Zahlung wird nicht mitgezählt, und fällt der letzte Tag der Frist auf einen Samstag, einen Sonntag oder einen gesetzlichen Feiertag, endet die Frist mit Ablauf des nächsten Arbeitstags. Ihre gesetzlichen Rechte bei einer mangelhaften Datei bleiben davon unberührt: siehe [Reklamationen und Mängel](doc:terms#defects) in unseren AGB.',
      ],
    },
    {
      id: 'online',
      title: 'Online widerrufen',
      blocks: [
        `Solange Ihr Widerrufsrecht besteht, können Sie jederzeit online mit der Funktion [„${W.de.button}“](${withdrawFunctionHref('de')}) widerrufen. Sie finden sie am Ende unserer Startseite und unserer Rechtstexte, auf Ihrer Bestellseite und hinter dem Widerrufslink in Ihrer Bestellbestätigung per E-Mail. Dieser Link öffnet die Funktion für Ihre Bestellung, ohne etwas zu starten. Das Öffnen Ihrer Bestellseite selbst startet die Erstellung Ihrer Datei, sobald Ihre Bestellbestätigung per E-Mail versandt ist, und damit erlischt Ihr Widerrufsrecht (siehe [Vorzeitiges Erlöschen des Widerrufsrechts](#expiry)).`,
        `So geht es: Geben Sie Ihren Namen, Ihre Bestellnummer (sie ist bereits eingetragen, wenn Sie von Ihrer Bestellseite oder über den Widerrufslink kommen) und die E-Mail-Adresse für die Eingangsbestätigung ein und senden Sie Ihren Widerruf mit der Schaltfläche „${W.de.confirm}“ ab. Kommen Sie ohne einen dieser Links, geben Sie bitte die E-Mail-Adresse an, mit der Sie bezahlt haben, damit wir Ihre Bestellung zuordnen können. Passen die Angaben zu keiner unserer Bestellungen, zeigt die Seite das an; Ihre Erklärung bewahren wir trotzdem auf, prüfen sie selbst und senden Ihnen eine Eingangsbestätigung per E-Mail. Um Missbrauch unserer E-Mails zu verhindern, sind Eingangsbestätigungen begrenzt: bei Erklärungen, die zu keiner unserer Bestellungen passen, auf zwei am Tag und vier im Monat an dieselbe Adresse; je Bestellung auf insgesamt drei an andere Adressen als die, mit der bezahlt wurde (weitere gehen an die Adresse, mit der Sie bezahlt haben); und bei einer wiederholten Erklärung zu einer Bestellung, die wir bereits beantwortet haben, auf eine am Tag für diese Bestellung und fünf am Tag für alle Bestellungen zusammen. Kann die Seite Ihre Erklärung nicht annehmen, etwa wegen einer technischen Störung oder weil ungewöhnlich viele Erklärungen eingehen, zeigt sie das an: Senden Sie uns Ihren Widerruf dann bitte per E-Mail; eine E-Mail ist genauso wirksam.`,
        'Was dann geschieht: Wir erfassen Ihre Erklärung mit Datum und Uhrzeit ihres Eingangs. Ist Ihre Bestellung bezahlt, haben wir mit Ihrer Datei noch nicht begonnen und ist die 14-tägige Widerrufsfrist nicht abgelaufen, ist Ihr Widerruf wirksam: Wir halten Ihre Bestellung an, sodass nichts erstellt wird, und erstatten Ihnen Ihre Zahlung, wie unter [Folgen des Widerrufs](#effects) beschrieben. War Ihre Zahlung bei Ihrem Widerruf noch in Bearbeitung, wird ebenfalls nichts erstellt, und geht die Zahlung bei uns ein, erstatten wir sie vollständig. Wir senden Ihnen unverzüglich eine Eingangsbestätigung mit dem Inhalt Ihres Widerrufs sowie Datum und Uhrzeit per E-Mail.',
        'Hatten wir mit Ihrer Zustimmung bereits mit Ihrer Datei begonnen oder war die 14-tägige Widerrufsfrist abgelaufen, war Ihr Widerrufsrecht schon erloschen (siehe [Vorzeitiges Erlöschen des Widerrufsrechts](#expiry)): Die Seite und die Eingangsbestätigung teilen Ihnen das mit, und wir sehen uns Ihre Erklärung trotzdem persönlich an. Wurde Ihre Bestellung nie bezahlt, gibt es keinen Vertrag, den Sie widerrufen könnten: Die Seite zeigt das an, und es wurde nichts berechnet. Ihre Rechte bei einer mangelhaften Datei bleiben davon unberührt.',
      ],
    },
    {
      id: 'form',
      title: 'Muster-Widerrufsformular',
      blocks: [
        '(Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular aus und senden Sie es zurück.)',
        {
          box: [
            `An: ${formLine('de')}`,
            'Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über den Kauf der folgenden Waren (*)/die Erbringung der folgenden Dienstleistung (*):',
            'Bestellt am (*)/erhalten am (*):',
            'Name des/der Verbraucher(s):',
            'Anschrift des/der Verbraucher(s):',
            'Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf Papier):',
            'Datum:',
            '(*) Unzutreffendes streichen.',
          ],
        },
        `Per E-Mail senden Sie einfach das ausgefüllte Formular oder Ihre eigene Erklärung an [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Widerruf). Bitte geben Sie, falls vorhanden, Ihre Bestellnummer an. Online nutzen Sie die oben beschriebene Funktion [„${W.de.button}“](${withdrawFunctionHref('de')}).`,
      ],
    },
  ],
};

export const WITHDRAWAL: LegalDocs = { en, de };

// ------------------------------------------------------------------------------------------ the Australian edition
/** The "expiry" section with the Australian checkbox text in its box and its closing sentence pointing at the
 *  Australian rights (the build stops if the EU sentence it replaces is not there any more). */
function expiryAu(s: LegalSection, consent: string, from: string, to: string): LegalSection {
  let hit = false;
  const blocks = s.blocks.map((b): Block => {
    if (typeof b === 'string') {
      if (!b.includes(from)) return b;
      hit = true;
      return b.replace(from, to);
    }
    return 'box' in b ? { ...b, box: [consent] } : b;
  });
  if (!hit) throw new Error('withdrawal page, Australian edition: the closing sentence of "expiry" changed');
  return { ...s, blocks };
}

const auEn = patchDoc(en, {
  lead:
    'This page sets out the right of withdrawal under EU consumer law, which applies to your contract through Lithuanian law: the right to cancel within 14 days without giving a reason. For a digital file like ours, it ends early once we start making your file with your consent. It is only about cancelling for a change of mind and never limits your rights if your file is faulty: see [Your rights in Australia](doc:terms#australia). Here is the full information.',
  replace: {
    expiry: (s) => expiryAu(s, CHECKOUT_LEGAL_AU.en.withdrawalConsent,
      'Your statutory rights for a defective file are not affected: see [Complaints and defects](doc:terms#defects) in our terms of sale.',
      'Your rights for a faulty file are not affected: see [Complaints and faulty files](doc:terms#defects) and [Your rights in Australia](doc:terms#australia) in our terms of sale.'),
  },
});

const auDe = patchDoc(de, {
  lead:
    'Diese Seite beschreibt das Widerrufsrecht nach dem EU-Verbraucherrecht, das über das litauische Recht für Ihren Vertrag gilt: das Recht, den Vertrag binnen 14 Tagen ohne Angabe von Gründen zu widerrufen. Bei einer digitalen Datei wie unserer erlischt es vorzeitig, sobald wir mit Ihrer Zustimmung mit der Erstellung Ihrer Datei beginnen. Es betrifft nur den Widerruf ohne Angabe von Gründen und schränkt Ihre Rechte bei einer mangelhaften Datei nie ein: siehe [Ihre Rechte in Australien](doc:terms#australia). Hier finden Sie alle Informationen.',
  replace: {
    expiry: (s) => expiryAu(s, CHECKOUT_LEGAL_AU.de.withdrawalConsent,
      'Ihre gesetzlichen Rechte bei einer mangelhaften Datei bleiben davon unberührt: siehe [Reklamationen und Mängel](doc:terms#defects) in unseren AGB.',
      'Ihre Rechte bei einer mangelhaften Datei bleiben davon unberührt: siehe [Reklamationen und mangelhafte Dateien](doc:terms#defects) und [Ihre Rechte in Australien](doc:terms#australia) in unseren AGB.'),
  },
});

export const WITHDRAWAL_AU: LegalDocs = { en: auEn, de: auDe };
