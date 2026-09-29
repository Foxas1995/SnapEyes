// Right of withdrawal: the statutory information for digital content not supplied on a tangible medium (model
// wording of Annex I(A) Directive 2011/83/EU; German: Muster-Widerrufsbelehrung, Anlage 1 zu Art. 246a § 1 Abs. 2
// EGBGB), the early expiry (Art. 16(m) Directive 2011/83/EU, § 356 Abs. 5 BGB) and the model withdrawal form
// (Annex I(B); Anlage 2). The checkbox text is imported from src/shared/legal.ts, the same text the checkout shows.
// The model sentences are kept word for word, including the delivery-cost clause of "Effects of withdrawal" (there
// are no delivery costs, but leaving it out would make this no longer the unchanged statutory model). The telephone
// number the model asks for is printed by contactLine as soon as SELLER.phone is set (src/landing/config.ts).
// Not reviewed by a lawyer.
import type { LegalDoc, LegalDocs } from '../types';
import { CHECKOUT_LEGAL } from '../../shared/legal';
import { CONTACT_EMAIL, contactLine } from '../facts';

const en: LegalDoc = {
  title: 'Right of withdrawal',
  description:
    'Withdrawal information for SnapEyes digital files: the 14-day right of withdrawal, when it ends early, and a model withdrawal form.',
  lead:
    'Consumers in the EU have a right of withdrawal for purchases made online. For a digital file like ours, it ends as soon as delivery begins with your consent. Here is the full information.',
  sections: [
    {
      id: 'right',
      title: 'Right of withdrawal',
      blocks: [
        'You have the right to withdraw from this contract within 14 days without giving any reason.',
        'The withdrawal period will expire after 14 days from the day of the conclusion of the contract.',
        `To exercise the right of withdrawal, you must inform us (${contactLine('en')}) of your decision to withdraw from this contract by an unequivocal statement (for example a letter sent by post or an email). You may use the model withdrawal form below, but it is not obligatory.`,
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
        '**Your right of withdrawal ends early** once we have begun to deliver the digital file, if (1) you expressly agreed that we begin before the withdrawal period ends, (2) you confirmed that you know you lose your right of withdrawal as soon as delivery begins, and (3) we have confirmed this to you on a durable medium (we do so in the order confirmation email). This follows from Art. 16(m) of Directive 2011/83/EU.',
        'Before you pay, you give this consent by ticking this box:',
        { box: [CHECKOUT_LEGAL.en.withdrawalConsent], label: 'The checkbox at checkout' },
        'In practice your right of withdrawal therefore ends when we start making your file, which is normally right after you pay. Your statutory rights for a defective file are not affected: see [Complaints and defects](doc:terms#defects) in our terms of sale.',
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
            'I/We (*) hereby give notice that I/We (*) withdraw from my/our (*) contract of sale of the following goods (*)/for the provision of the following service (*)/for the supply of the following digital content (*):',
            'Ordered on (*)/received on (*):',
            'Name of consumer(s):',
            'Address of consumer(s):',
            'Signature of consumer(s) (only if this form is notified on paper):',
            'Date:',
            '(*) Delete as appropriate.',
          ],
        },
        `By email, simply send the completed form, or your own statement, to [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Withdrawal). Please add your order number if you have it.`,
      ],
    },
  ],
};

const de: LegalDoc = {
  title: 'Widerrufs\u00ADbelehrung',
  description:
    'Widerrufsbelehrung für digitale Dateien von SnapEyes: das 14-tägige Widerrufsrecht, wann es vorzeitig erlischt, und ein Muster-Widerrufsformular.',
  lead:
    'Verbraucher in der EU haben bei Online-Käufen ein Widerrufsrecht. Bei einer digitalen Datei wie unserer erlischt es, sobald die Bereitstellung mit Ihrer Zustimmung beginnt. Hier finden Sie alle Informationen.',
  sections: [
    {
      id: 'right',
      title: 'Widerrufsrecht',
      blocks: [
        'Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen.',
        'Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses.',
        `Um Ihr Widerrufsrecht auszuüben, müssen Sie uns (${contactLine('de')}) mittels einer eindeutigen Erklärung (z.\u00a0B. ein mit der Post versandter Brief oder E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür das beigefügte Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben ist.`,
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
        '**Ihr Widerrufsrecht erlischt vorzeitig**, sobald wir mit der Bereitstellung der digitalen Datei begonnen haben, wenn Sie (1) ausdrücklich zugestimmt haben, dass wir vor Ablauf der Widerrufsfrist mit der Vertragserfüllung beginnen, (2) Ihre Kenntnis davon bestätigt haben, dass Sie durch Ihre Zustimmung mit Beginn der Vertragserfüllung Ihr Widerrufsrecht verlieren, und (3) wir Ihnen dies auf einem dauerhaften Datenträger bestätigt haben (das tun wir mit der Bestellbestätigung per E-Mail). Das ergibt sich aus § 356 Abs. 5 BGB und Art. 16 Buchst. m der Richtlinie 2011/83/EU.',
        'Vor der Zahlung geben Sie diese Zustimmung, indem Sie dieses Kästchen ankreuzen:',
        { box: [CHECKOUT_LEGAL.de.withdrawalConsent], label: 'Das Kästchen im Bestellvorgang' },
        'In der Praxis erlischt Ihr Widerrufsrecht daher, sobald wir mit Ihrer Datei beginnen, normalerweise direkt nach der Zahlung. Ihre gesetzlichen Rechte bei einer mangelhaften Datei bleiben davon unberührt: siehe [Reklamationen und Mängel](doc:terms#defects) in unseren AGB.',
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
            'Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über den Kauf der folgenden Waren (*)/die Erbringung der folgenden Dienstleistung (*)/die Bereitstellung der folgenden digitalen Inhalte (*):',
            'Bestellt am (*)/erhalten am (*):',
            'Name des/der Verbraucher(s):',
            'Anschrift des/der Verbraucher(s):',
            'Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf Papier):',
            'Datum:',
            '(*) Unzutreffendes streichen.',
          ],
        },
        `Per E-Mail senden Sie einfach das ausgefüllte Formular oder Ihre eigene Erklärung an [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Widerruf). Bitte geben Sie, falls vorhanden, Ihre Bestellnummer an.`,
      ],
    },
  ],
};

export const WITHDRAWAL: LegalDocs = { en, de };
