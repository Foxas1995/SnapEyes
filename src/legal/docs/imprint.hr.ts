// Impresum: the Croatian twin of `en` in src/legal/docs/imprint.ts, same section ids and rows. "Impresum" is the name
// Croatian websites give the page with the provider's details (the information Zakon o elektroničkoj trgovini asks a
// service provider to show). The "Zastupnik" and "Telefon" rows appear only when SELLER.representative and SELLER.phone
// are set (today: the representative is set, the phone is not, owner decision PHONE_OMITTED_BY_OWNER). No VAT number:
// the MB is not a VAT payer (the owner's sentence, as the Lithuanian page has it). The seller stays the Lithuanian
// company, with its Lithuanian register and legal form named in Croatian next to their Lithuanian names.
import type { LegalDoc } from '../types';
import { MAIL, SELLER, company, country } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionHref } from '../../shared/legal';

const companyHr = company('hr');
const countryHr = country('hr');
const WITHDRAWAL_ONLINE_HR = WITHDRAWAL_ONLINE.hr;
const withdrawFunctionHrefHr = () => withdrawFunctionHref('hr');

const rowsHr = (): Array<[string, string]> => {
  const out: Array<[string, string]> = [
    ['Pružatelj usluga', companyHr],
    ['Pravni oblik', 'mažoji bendrija (MB), malo partnersko društvo prema pravu Republike Litve'],
    ['Adresa', `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${countryHr}`],
  ];
  if (SELLER.representative) out.push(['Zastupnik', SELLER.representative]);
  out.push(['E-pošta', MAIL]);
  if (SELLER.phone) out.push(['Telefon', SELLER.phone]);
  out.push(
    ['Registar', 'Registar pravnih osoba Republike Litve (Juridinių asmenų registras), koji vodi državno poduzeće Centar registara (Registrų centras)'],
    ['Matični broj (broj u registru)', SELLER.code],
    ['PDV', `${companyHr} nije obveznik PDV-a, stoga se PDV ne obračunava i nema PDV identifikacijskog broja.`],
  );
  return out;
};

export const hr: LegalDoc = {
  title: 'Impresum',
  description: `Tko vodi SnapEyes: ${companyHr}, ${SELLER.city}, ${countryHr}. Podaci o društvu, registar, kontakt.`,
  sections: [
    {
      id: 'provider',
      title: 'Pružatelj usluga',
      blocks: [`Internetskom stranicom snapeyes.com i robnom markom SnapEyes upravlja ${companyHr}.`, { dl: rowsHr() }],
    },
    {
      id: 'contact',
      title: 'Kontakt',
      blocks: [
        SELLER.phone ? `Najbrže nas možete dobiti e-poštom: ${MAIL}. Telefonom: ${SELLER.phone}.` : `Najbrže nas možete dobiti e-poštom: ${MAIL}.`,
        `Za jednostrani raskid narudžbe možete se koristiti i našom mrežnom funkcijom [„${WITHDRAWAL_ONLINE_HR.button}“](${withdrawFunctionHrefHr()}).`,
      ],
    },
    {
      id: 'images',
      title: 'O slikama',
      blocks: [
        'Primjeri slika na našoj početnoj stranici prikazuju naše vlastito oko, fotografirano mobitelom i obrađeno našim softverom. Primjer oka koji možete isprobati u alatu za pregled izradila je umjetna inteligencija i uvijek je tako označen.',
      ],
    },
    {
      id: 'more',
      title: 'Više pravnih informacija',
      blocks: [
        'Kako postupamo s vašim podacima: [Politika privatnosti](doc:privacy). Kupnja datoteke: [Opći uvjeti prodaje](doc:terms) i [Pravo na jednostrani raskid ugovora](doc:withdrawal). Potrošački sporovi: [Sporovi i mjerodavno pravo](doc:terms#disputes).',
      ],
    },
  ],
};
