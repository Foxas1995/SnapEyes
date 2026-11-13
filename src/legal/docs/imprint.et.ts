// Ettevõtte andmed: the Estonian twin of `en` in src/legal/docs/imprint.ts, same section ids and rows. "Ettevõtte andmed"
// (company details) is what an Estonian website calls the page with the provider's details; Estonian has no word like
// "Impressum". The "Esindaja" and "Telefon" rows appear only when SELLER.representative and SELLER.phone are set (today:
// the representative is set, the phone is not, owner decision PHONE_OMITTED_BY_OWNER). No VAT number: the MB is not
// VAT-registered. The seller stays the Lithuanian company, with its Lithuanian register and legal form named in Estonian
// next to their Lithuanian names. Formal "teie", written in lower case, as the other Estonian legal texts.
import type { LegalDoc } from '../types';
import { MAIL, SELLER, company, country } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionHref } from '../../shared/legal';

const companyEt = company('et');
const countryEt = country('et');
const WITHDRAWAL_ONLINE_ET = WITHDRAWAL_ONLINE.et;
const withdrawFunctionHrefEt = () => withdrawFunctionHref('et');

const rowsEt = (): Array<[string, string]> => {
  const out: Array<[string, string]> = [
    ['Teenuseosutaja', companyEt],
    ['Õiguslik vorm', 'mažoji bendrija (MB), Leedu õiguse alusel asutatud väikeühing'],
    ['Aadress', `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${countryEt}`],
  ];
  if (SELLER.representative) out.push(['Esindaja', SELLER.representative]);
  out.push(['E-post', MAIL]);
  if (SELLER.phone) out.push(['Telefon', SELLER.phone]);
  out.push(
    ['Register', 'Leedu Vabariigi juriidiliste isikute register (Juridinių asmenų registras), mida peab riigiettevõte Registrite Keskus (Registrų centras)'],
    ['Registrikood (registrinumber)', SELLER.code],
    ['Käibemaks', 'Ei ole käibemaksukohustuslasena registreeritud, seega käibemaksukohustuslase numbrit ei ole.'],
  );
  return out;
};

export const et: LegalDoc = {
  title: 'Ettevõtte andmed',
  description: `Kes SnapEyesi haldab: ${companyEt}, ${SELLER.city}, ${countryEt}. Ettevõtte andmed, register, kontakt.`,
  sections: [
    {
      id: 'provider',
      title: 'Teenuseosutaja',
      blocks: [`Veebilehte snapeyes.com ja kaubamärki SnapEyes haldab ${companyEt}.`, { dl: rowsEt() }],
    },
    {
      id: 'contact',
      title: 'Kontakt',
      blocks: [
        SELLER.phone ? `Kõige kiiremini saate meiega ühendust e-posti teel: ${MAIL}. Telefoni teel: ${SELLER.phone}.` : `Kõige kiiremini saate meiega ühendust e-posti teel: ${MAIL}.`,
        `Tellimusest taganemiseks võite kasutada ka meie veebipõhist funktsiooni [„${WITHDRAWAL_ONLINE_ET.button}“](${withdrawFunctionHrefEt()}).`,
      ],
    },
    {
      id: 'images',
      title: 'Piltidest',
      blocks: [
        'Meie avalehe näidispildid kujutavad meie enda silma, mis on pildistatud telefoniga ja töödeldud meie tarkvaraga. Näidissilm, mida saate eelvaate tööriistas proovida, on tehisintellekti loodud ja alati vastavalt märgistatud.',
      ],
    },
    {
      id: 'more',
      title: 'Muu õiguslik teave',
      blocks: [
        'Kuidas me teie andmeid käsitleme: [Privaatsuspoliitika](doc:privacy). Faili ostmine: [Müügitingimused](doc:terms) ja [Taganemisõigus](doc:withdrawal). Tarbijavaidlused: [Vaidlused ja kohaldatav õigus](doc:terms#disputes).',
      ],
    },
  ],
};
