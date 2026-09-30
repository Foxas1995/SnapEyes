// Rekvizitai: the Lithuanian twin of `en` in src/legal/docs/imprint.ts, same section ids and rows. The
// "Atstovas" and "Telefonas" rows appear only when SELLER.representative and SELLER.phone are set (today: the
// representative is set, the phone is not, owner decision PHONE_OMITTED_BY_OWNER). No VAT number: the MB is not a
// VAT payer (the owner's sentence, word for word).
import type { LegalDoc } from '../types';
import { MAIL, SELLER, company, country } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionHref } from '../../shared/legal';

const companyLt = company('lt');
const countryLt = country('lt');
const WITHDRAWAL_ONLINE_LT = WITHDRAWAL_ONLINE.lt;
const withdrawFunctionHrefLt = () => withdrawFunctionHref('lt');

const rowsLt = (): Array<[string, string]> => {
  const out: Array<[string, string]> = [
    ['Paslaugų teikėjas', companyLt],
    ['Teisinė forma', 'mažoji bendrija (MB), veikianti pagal Lietuvos Respublikos teisę'],
    ['Adresas', `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${countryLt}`],
  ];
  if (SELLER.representative) out.push(['Atstovas', SELLER.representative]);
  out.push(['El. paštas', MAIL]);
  if (SELLER.phone) out.push(['Telefonas', SELLER.phone]);
  out.push(
    ['Registras', 'Lietuvos Respublikos juridinių asmenų registras, kurį tvarko valstybės įmonė Registrų centras'],
    ['Juridinio asmens kodas', SELLER.code],
    ['PVM', `${companyLt} nėra PVM mokėtoja, todėl PVM netaikomas ir PVM mokėtojo kodo nėra.`],
  );
  return out;
};

export const lt: LegalDoc = {
  title: 'Rekvizitai',
  description: `Kas valdo SnapEyes: ${companyLt}, ${SELLER.city}, ${countryLt}. Įmonės duomenys, registras, kontaktai.`,
  sections: [
    {
      id: 'provider',
      title: 'Paslaugų teikėjas',
      blocks: [`Svetainę snapeyes.com ir prekės ženklą SnapEyes valdo ${companyLt}.`, { dl: rowsLt() }],
    },
    {
      id: 'contact',
      title: 'Kontaktai',
      blocks: [
        SELLER.phone ? `Greičiausiai su mumis susisieksite el. paštu: ${MAIL}. Telefonu: ${SELLER.phone}.` : `Greičiausiai su mumis susisieksite el. paštu: ${MAIL}.`,
        `Sutarties atsisakyti taip pat galite mūsų internetine funkcija [„${WITHDRAWAL_ONLINE_LT.button}“](${withdrawFunctionHrefLt()}).`,
      ],
    },
    {
      id: 'images',
      title: 'Apie vaizdus',
      blocks: [
        'Mūsų pagrindinio puslapio pavyzdiniuose vaizduose matote paties įkūrėjo akį, nufotografuotą telefonu ir apdorotą mūsų programos. Pavyzdinė akis, kurią galite išbandyti peržiūros įrankyje, yra sugeneruota DI ir visada taip pažymėta.',
      ],
    },
    {
      id: 'more',
      title: 'Daugiau teisinės informacijos',
      blocks: [
        'Kaip tvarkome Jūsų duomenis: [Privatumo politika](doc:privacy). Failo pirkimas: [Pardavimo sąlygos](doc:terms) ir [Teisė atsisakyti sutarties](doc:withdrawal). Vartojimo ginčai: [Ginčai ir taikytina teisė](doc:terms#disputes).',
      ],
    },
  ],
};
