// Yritystiedot: the Finnish twin of `en` in src/legal/docs/imprint.ts, same section ids and rows. "Yritystiedot"
// (company details) is the plain Finnish name for the page with the provider's details (the information a service
// provider has to show under the e-commerce rules, Directive 2000/31/EC Art. 5). The "Edustaja" and "Puhelin" rows appear
// only when SELLER.representative and SELLER.phone are set (today: the representative is set, the phone is not, owner
// decision PHONE_OMITTED_BY_OWNER). No VAT number: the MB is not a VAT payer. The seller stays the Lithuanian company,
// with its Lithuanian register and legal form named in Finnish next to their Lithuanian names. Formal "te", as every
// Finnish legal text of the site.
import type { LegalDoc } from '../types';
import { MAIL, SELLER, company, country } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionHref } from '../../shared/legal';

const companyFi = company('fi');
const countryFi = country('fi');
const WITHDRAWAL_ONLINE_FI = WITHDRAWAL_ONLINE.fi;
const withdrawFunctionHrefFi = () => withdrawFunctionHref('fi');

const rowsFi = (): Array<[string, string]> => {
  const out: Array<[string, string]> = [
    ['Palveluntarjoaja', companyFi],
    ['Yhtiömuoto', 'mažoji bendrija (MB), Liettuan lain mukainen pienyhtiö'],
    ['Osoite', `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${countryFi}`],
  ];
  if (SELLER.representative) out.push(['Edustaja', SELLER.representative]);
  out.push(['Sähköposti', MAIL]);
  if (SELLER.phone) out.push(['Puhelin', SELLER.phone]);
  out.push(
    ['Rekisteri', 'Liettuan tasavallan oikeushenkilörekisteri (Juridinių asmenų registras), jota pitää valtionyritys Rekisterikeskus (Registrų centras)'],
    ['Yritystunnus (rekisterinumero)', SELLER.code],
    ['Arvonlisävero', 'Ei arvonlisäverovelvollinen, joten arvonlisäverotunnistetta ei ole.'],
  );
  return out;
};

export const fi: LegalDoc = {
  title: 'Yritystiedot',
  description: `Kuka ylläpitää SnapEyes-palvelua: ${companyFi}, ${SELLER.city}, ${countryFi}. Yritystiedot, rekisteri, yhteystiedot.`,
  sections: [
    {
      id: 'provider',
      title: 'Palveluntarjoaja',
      blocks: [`Verkkosivustoa snapeyes.com ja SnapEyes-tuotemerkkiä ylläpitää ${companyFi}.`, { dl: rowsFi() }],
    },
    {
      id: 'contact',
      title: 'Yhteystiedot',
      blocks: [
        SELLER.phone ? `Nopeimmin tavoitatte meidät sähköpostitse: ${MAIL}. Puhelimitse: ${SELLER.phone}.` : `Nopeimmin tavoitatte meidät sähköpostitse: ${MAIL}.`,
        `Tilauksen peruuttamiseen voitte käyttää myös verkkotoimintoamme [”${WITHDRAWAL_ONLINE_FI.button}”](${withdrawFunctionHrefFi()}).`,
      ],
    },
    {
      id: 'images',
      title: 'Tietoa kuvista',
      blocks: [
        'Etusivumme esimerkkikuvissa on oma silmämme, puhelimella kuvattuna ja ohjelmistollamme käsiteltynä. Näytesilmä, jota voitte kokeilla esikatselutyökalussa, on tekoälyn luoma, ja se on aina merkitty sellaiseksi.',
      ],
    },
    {
      id: 'more',
      title: 'Lisää oikeudellisia tietoja',
      blocks: [
        'Miten käsittelemme tietojanne: [Tietosuojaseloste](doc:privacy). Tiedoston ostaminen: [Myyntiehdot](doc:terms) ja [Peruuttamisoikeus](doc:withdrawal). Kuluttajariidat: [Riidat ja sovellettava laki](doc:terms#disputes).',
      ],
    },
  ],
};
