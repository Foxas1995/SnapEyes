// Right of withdrawal: the statutory information for digital content not supplied on a tangible medium (model
// wording of Annex I(A) Directive 2011/83/EU; German: Muster-Widerrufsbelehrung, Anlage 1 zu Art. 246a § 1 Abs. 2
// EGBGB in the version in force since 19.06.2026), the early expiry (Art. 16(m) Directive 2011/83/EU, § 356 Abs. 5
// BGB) and the model withdrawal form (Annex I(B); Anlage 2). The checkbox text is imported from src/shared/legal.ts,
// the same text the checkout shows.
// The model sentences are kept word for word, including the delivery-cost clause of "Effects of withdrawal" (there
// are no delivery costs, but leaving it out would make this no longer the unchanged statutory model). The model form
// keeps only its own alternatives (goods / service): no added line. The telephone number the model asks for
// (Gestaltungshinweis 2; Annex I(A) note 2) is printed by contactLine as soon as SELLER.phone is set
// (src/landing/config.ts). Checked 2026-09-29 against Anlage 1 and 2 EGBGB (buzer.de, gesetze-im-internet.de) and
// Annex I of Directive 2011/83/EU.
// We are obliged to offer the online withdrawal function (Art. 11a Directive 2011/83/EU, § 356a BGB), so "right"
// carries the model sentence for exactly that case (Gestaltungshinweis 3, first alternative, as replaced by Art. 2
// Nr. 7 of the law of 03.02.2026, BGBl. 2026 I Nr. 28: "Sie können Ihr Widerrufsrecht auch online unter ...
// ausüben. Wenn Sie diese Online-Funktion nutzen, ..."), not the older sentence for an optional web form. The German
// sentence is the statutory one word for word; the English one renders it faithfully (Annex I(A) note 3 as amended by
// Directive (EU) 2023/2673; to be confirmed against the Official Journal's English text). The address, the labels and
// the link come from src/shared/legal.ts (withdrawFunctionAddress, WITHDRAWAL_ONLINE, withdrawFunctionHref), the ones
// the order page's form uses. The "online" section describes the function; what the server does with a statement is
// api/order.py action "withdraw" (api/_lib/withdraw.py). Keep this text in step with both.
// The right ends when we START MAKING the file, the beginning of performance ("mit der Vertragserfüllung begonnen",
// § 356 Abs. 5 BGB): withdraw.py treats making.json or a stored eye as that moment, and the checkbox says the same.
// Not reviewed by a lawyer.
import type { LegalDoc, LegalDocs } from '../types';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';
import { CONTACT_EMAIL, contactLine } from '../facts';

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
        `To exercise the right of withdrawal, you must inform us (${contactLine('en')}) of your decision to withdraw from this contract by an unequivocal statement (e.g. a letter sent by post or e-mail). You may use the attached model withdrawal form, but it is not obligatory. You can also exercise your right of withdrawal online at [${withdrawFunctionAddress('en')}](${withdrawFunctionHref('en')}) (the button "${W.en.button}"). If you use this online function, we will communicate to you an acknowledgement of receipt on a durable medium (e.g. by e-mail) without delay, with information on the content of the withdrawal statement and the date and time of its receipt.`,
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
        'In practice your right of withdrawal therefore ends when we start making your file, which is normally right after you pay, as soon as your order confirmation email has gone out. From then on it has ended, even while your file is still being made or is waiting for our quality check. Your statutory rights for a defective file are not affected: see [Complaints and defects](doc:terms#defects) in our terms of sale.',
      ],
    },
    {
      id: 'online',
      title: 'Withdraw online',
      blocks: [
        `While your right of withdrawal lasts, you can withdraw online at any time with the function ["${W.en.button}"](${withdrawFunctionHref('en')}). You find it at the foot of our home page and of our legal pages, and on your order page (the link in your order confirmation email).`,
        `How it works: enter your name, your order number (it is filled in when you come from your order page) and the email address for the acknowledgement, then send your withdrawal with the button "${W.en.confirm}". If you do not come from your order page, please give the email address you paid with, so that we can match your order. If the details match none of our orders, the page tells you so; we still keep your statement, email you the acknowledgement of receipt and check it by hand.`,
        'What happens then: we record your withdrawal with the date and time it reached us. If we have not started making your file yet, we stop your order, so nothing is made. Without delay we email you an acknowledgement of receipt with the content of your withdrawal and its date and time, and we refund you as described under [Effects of withdrawal](#effects).',
        'If we had already started making your file with your consent, your right of withdrawal had already ended (see [When the right of withdrawal ends early](#expiry)), and we tell you so. Your rights for a defective file are not affected.',
      ],
    },
    {
      id: 'form',
      title: 'Model withdrawal form',
      blocks: [
        '(Complete and return this form only if you wish to withdraw from the contract.)',
        {
          box: [
            `To: ${contactLine('en')}`,
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
        'In der Praxis erlischt Ihr Widerrufsrecht daher, sobald wir mit der Erstellung Ihrer Datei beginnen, normalerweise direkt nach der Zahlung, sobald Ihre Bestellbestätigung per E-Mail versandt ist. Ab dann ist es erloschen, auch wenn Ihre Datei noch erstellt wird oder auf unsere Qualitätsprüfung wartet. Ihre gesetzlichen Rechte bei einer mangelhaften Datei bleiben davon unberührt: siehe [Reklamationen und Mängel](doc:terms#defects) in unseren AGB.',
      ],
    },
    {
      id: 'online',
      title: 'Online widerrufen',
      blocks: [
        `Solange Ihr Widerrufsrecht besteht, können Sie jederzeit online mit der Funktion [„${W.de.button}“](${withdrawFunctionHref('de')}) widerrufen. Sie finden sie am Ende unserer Startseite und unserer Rechtstexte sowie auf Ihrer Bestellseite (Link in Ihrer Bestellbestätigung per E-Mail).`,
        `So geht es: Geben Sie Ihren Namen, Ihre Bestellnummer (sie ist bereits eingetragen, wenn Sie von Ihrer Bestellseite kommen) und die E-Mail-Adresse für die Eingangsbestätigung ein und senden Sie Ihren Widerruf mit der Schaltfläche „${W.de.confirm}“ ab. Kommen Sie nicht von Ihrer Bestellseite, geben Sie bitte die E-Mail-Adresse an, mit der Sie bezahlt haben, damit wir Ihre Bestellung zuordnen können. Passen die Angaben zu keiner unserer Bestellungen, zeigt die Seite das an; Ihre Erklärung bewahren wir trotzdem auf, senden Ihnen die Eingangsbestätigung per E-Mail und prüfen sie selbst.`,
        'Was dann geschieht: Wir erfassen Ihren Widerruf mit Datum und Uhrzeit seines Eingangs. Haben wir mit Ihrer Datei noch nicht begonnen, halten wir Ihre Bestellung an, sodass nichts erstellt wird. Wir senden Ihnen unverzüglich eine Eingangsbestätigung mit dem Inhalt Ihres Widerrufs sowie Datum und Uhrzeit per E-Mail und erstatten Ihnen Ihre Zahlung, wie unter [Folgen des Widerrufs](#effects) beschrieben.',
        'Hatten wir mit Ihrer Zustimmung bereits mit Ihrer Datei begonnen, war Ihr Widerrufsrecht schon erloschen (siehe [Vorzeitiges Erlöschen des Widerrufsrechts](#expiry)); das teilen wir Ihnen mit. Ihre Rechte bei einer mangelhaften Datei bleiben davon unberührt.',
      ],
    },
    {
      id: 'form',
      title: 'Muster-Widerrufsformular',
      blocks: [
        '(Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular aus und senden Sie es zurück.)',
        {
          box: [
            `An: ${contactLine('de')}`,
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
