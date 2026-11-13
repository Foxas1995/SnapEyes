// Rekvizīti: the Latvian twin of `en` in src/legal/docs/imprint.ts, same section ids and rows. "Rekvizīti" is the name
// Latvian websites give the page with the provider's details (company, register, address, contact). The "Pārstāvis"
// and "Tālrunis" rows appear only when SELLER.representative and SELLER.phone are set (today: the representative is
// set, the phone is not, owner decision PHONE_OMITTED_BY_OWNER). No VAT number: the MB is not VAT-registered (the
// English sentence). The seller stays the Lithuanian company, with its Lithuanian register and legal form named in
// Latvian next to their Lithuanian names.
import type { LegalDoc } from '../types';
import { MAIL, SELLER, company, country } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionHref } from '../../shared/legal';

const companyLv = company('lv');
const countryLv = country('lv');
const WITHDRAWAL_ONLINE_LV = WITHDRAWAL_ONLINE.lv;
const withdrawFunctionHrefLv = () => withdrawFunctionHref('lv');

const rowsLv = (): Array<[string, string]> => {
  const out: Array<[string, string]> = [
    ['Pakalpojuma sniedzējs', companyLv],
    ['Juridiskā forma', 'mažoji bendrija (MB), mazā sabiedrība saskaņā ar Lietuvas tiesībām'],
    ['Adrese', `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${countryLv}`],
  ];
  if (SELLER.representative) out.push(['Pārstāvis', SELLER.representative]);
  out.push(['E-pasts', MAIL]);
  if (SELLER.phone) out.push(['Tālrunis', SELLER.phone]);
  out.push(
    ['Reģistrs', 'Lietuvas Republikas Juridisko personu reģistrs (Juridinių asmenų registras), ko uztur valsts uzņēmums Reģistru centrs (Registrų centras)'],
    ['Reģistrācijas numurs (numurs reģistrā)', SELLER.code],
    ['PVN', 'Nav reģistrēts kā PVN maksātājs, tāpēc PVN numura nav.'],
  );
  return out;
};

export const lv: LegalDoc = {
  title: 'Rekvizīti',
  description: `Kas uztur SnapEyes: ${companyLv}, ${SELLER.city}, ${countryLv}. Uzņēmuma dati, reģistrs, kontakti.`,
  sections: [
    {
      id: 'provider',
      title: 'Pakalpojuma sniedzējs',
      blocks: [`Vietni snapeyes.com un zīmolu SnapEyes uztur ${companyLv}.`, { dl: rowsLv() }],
    },
    {
      id: 'contact',
      title: 'Kontakti',
      blocks: [
        SELLER.phone ? `Visātrāk mūs var sasniegt pa e-pastu: ${MAIL}. Pa tālruni: ${SELLER.phone}.` : `Visātrāk mūs var sasniegt pa e-pastu: ${MAIL}.`,
        `Lai atteiktos no pasūtījuma, varat izmantot arī mūsu tiešsaistes funkciju [„${WITHDRAWAL_ONLINE_LV.button}”](${withdrawFunctionHrefLv()}).`,
      ],
    },
    {
      id: 'images',
      title: 'Par attēliem',
      blocks: [
        'Piemēru attēlos mūsu sākumlapā redzama mūsu pašu acs, nofotografēta ar telefonu un apstrādāta ar mūsu programmatūru. Parauga acs, ko varat izmēģināt priekšskatījuma rīkā, ir mākslīgā intelekta radīta un vienmēr attiecīgi apzīmēta.',
      ],
    },
    {
      id: 'more',
      title: 'Vairāk juridiskās informācijas',
      blocks: [
        'Kā rīkojamies ar jūsu datiem: [Privātuma politika](doc:privacy). Faila iegāde: [Pārdošanas noteikumi](doc:terms) un [Atteikuma tiesības](doc:withdrawal). Patērētāju strīdi: [Strīdi un piemērojamās tiesības](doc:terms#disputes).',
      ],
    },
  ],
};
