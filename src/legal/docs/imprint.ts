// Legal notice (EN) / Impressum (DE). The "Represented by" and "Phone" rows appear only when SELLER.representative
// and SELLER.phone are set in src/landing/config.ts; the owner decided to show no phone (PHONE_OMITTED_BY_OWNER), so
// the contact is the email address and, for withdrawals, the online withdrawal function. No VAT number: the MB is not
// VAT-registered.
import type { LegalDoc, LegalDocs } from '../types';
import { MAIL, SELLER, company, country } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionHref } from '../../shared/legal';

const rows = (lang: 'en' | 'de'): Array<[string, string]> => {
  const de = lang === 'de';
  const out: Array<[string, string]> = [
    [de ? 'Anbieter' : 'Provider', company(lang)],
    [de ? 'Rechtsform' : 'Legal form', de ? 'mažoji bendrija (MB), Kleingesellschaft nach litauischem Recht' : 'mažoji bendrija (MB), a small partnership under Lithuanian law'],
    [de ? 'Anschrift' : 'Address', `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${country(lang)}`],
  ];
  if (SELLER.representative) out.push([de ? 'Vertreten durch' : 'Represented by', SELLER.representative]);
  out.push([de ? 'E-Mail' : 'Email', MAIL]);
  if (SELLER.phone) out.push([de ? 'Telefon' : 'Phone', SELLER.phone]);
  out.push(
    [
      'Register',
      de
        ? 'Register der juristischen Personen der Republik Litauen (Juridinių asmenų registras), geführt vom staatlichen Unternehmen Registrų centras'
        : 'Register of Legal Entities of the Republic of Lithuania (Juridinių asmenų registras), kept by the State Enterprise Centre of Registers (Registrų centras)',
    ],
    [de ? 'Unternehmenscode (Registernummer)' : 'Company code (register number)', SELLER.code],
    [de ? 'Umsatzsteuer' : 'VAT', de ? 'Nicht umsatzsteuerlich registriert, daher keine USt-IdNr.' : 'Not registered for VAT, so there is no VAT number.'],
  );
  return out;
};

const en: LegalDoc = {
  title: 'Legal notice',
  description: `Who runs SnapEyes: ${company('en')}, ${SELLER.city}, ${country('en')}. Company details, register, contact.`,
  sections: [
    {
      id: 'provider',
      title: 'Service provider',
      blocks: [`snapeyes.com and the SnapEyes brand are run by ${company('en')}.`, { dl: rows('en') }],
    },
    {
      id: 'contact',
      title: 'Contact',
      blocks: [
        SELLER.phone ? `The quickest way to reach us is by email: ${MAIL}. By phone: ${SELLER.phone}.` : `The quickest way to reach us is by email: ${MAIL}.`,
        `To withdraw from an order, you can also use our online function ["${WITHDRAWAL_ONLINE.en.button}"](${withdrawFunctionHref('en')}).`,
      ],
    },
    {
      id: 'images',
      title: 'About the images',
      blocks: [
        "The example images on our home page show the founder's own eye, photographed with a phone and rendered by our software. The sample eye you can try in the preview tool is AI-generated and always labelled as such.",
      ],
    },
    {
      id: 'more',
      title: 'More legal information',
      blocks: [
        'How we handle your data: [Privacy policy](doc:privacy). Buying a file: [Terms of sale](doc:terms) and [Right of withdrawal](doc:withdrawal). Consumer disputes: [Disputes and applicable law](doc:terms#disputes).',
      ],
    },
  ],
};

const de: LegalDoc = {
  title: 'Impressum',
  description: `Wer SnapEyes betreibt: ${company('de')}, ${SELLER.city}, ${country('de')}. Unternehmensangaben, Register, Kontakt.`,
  sections: [
    {
      id: 'provider',
      title: 'Anbieter',
      blocks: [`snapeyes.com und die Marke SnapEyes werden betrieben von ${company('de')}.`, { dl: rows('de') }],
    },
    {
      id: 'contact',
      title: 'Kontakt',
      blocks: [
        SELLER.phone ? `Am schnellsten erreichen Sie uns per E-Mail: ${MAIL}. Telefonisch: ${SELLER.phone}.` : `Am schnellsten erreichen Sie uns per E-Mail: ${MAIL}.`,
        `Um eine Bestellung zu widerrufen, können Sie auch unsere Online-Funktion [„${WITHDRAWAL_ONLINE.de.button}“](${withdrawFunctionHref('de')}) nutzen.`,
      ],
    },
    {
      id: 'images',
      title: 'Zu den Bildern',
      blocks: [
        'Die Beispielbilder auf unserer Startseite zeigen das eigene Auge des Gründers, mit dem Smartphone fotografiert und von unserer Software gerendert. Das Beispielauge, das Sie in der Vorschau-App ausprobieren können, ist KI-generiert und immer als solches gekennzeichnet.',
      ],
    },
    {
      id: 'more',
      title: 'Weitere rechtliche Informationen',
      blocks: [
        'Wie wir mit Ihren Daten umgehen: [Datenschutzerklärung](doc:privacy). Kauf einer Datei: [AGB](doc:terms) und [Widerrufsbelehrung](doc:withdrawal). Verbraucherstreitigkeiten: [Streitigkeiten und anwendbares Recht](doc:terms#disputes).',
      ],
    },
  ],
};

export const IMPRINT: LegalDocs = { en, de };
