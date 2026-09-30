// Impresszum, the Hungarian ("hu") version of src/legal/docs/imprint.ts: the same rows and sections. The "Képviseli"
// and "Telefon" rows appear only when SELLER.representative and SELLER.phone are set (the owner shows no phone).
// No VAT number: the MB is not VAT-registered. Hungarian readers are told plainly that the seller is a Lithuanian
// company (the GVH advises checking whether a Hungarian-language shop is really Hungarian).
import type { LegalDoc } from '../types';
import { MAIL, SELLER, company, country } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionHref } from '../../shared/legal';

const companyHu = () => company('hu');
const countryHu = () => country('hu');
const WITHDRAWAL_ONLINE_HU = WITHDRAWAL_ONLINE.hu;
const withdrawFunctionHrefHu = () => withdrawFunctionHref('hu');

export const rowsHu = (): Array<[string, string]> => {
  const out: Array<[string, string]> = [
    ['Szolgáltató', companyHu()],
    ['Jogi forma', 'mažoji bendrija (MB), litván jog szerinti kis társaság'],
    ['Székhely', `${SELLER.street}, ${SELLER.postcode} ${SELLER.city}, ${countryHu()}`],
  ];
  if (SELLER.representative) out.push(['Képviseli', SELLER.representative]);
  out.push(['E-mail', MAIL]);
  if (SELLER.phone) out.push(['Telefon', SELLER.phone]);
  out.push(
    ['Nyilvántartás', 'A Litván Köztársaság jogi személyeinek nyilvántartása (Juridinių asmenų registras), vezeti a Registrų centras állami vállalat'],
    ['Cégazonosító szám (nyilvántartási szám)', SELLER.code],
    ['Áfa', 'Nem vagyunk áfafizetőként nyilvántartásba véve, ezért nincs közösségi adószámunk.'],
  );
  return out;
};

export const hu: LegalDoc = {
  title: 'Impresszum',
  description: `A SnapEyes üzemeltetője: ${companyHu()}, ${SELLER.city}, ${countryHu()}. Cégadatok, nyilvántartás, kapcsolat.`,
  sections: [
    {
      id: 'provider',
      title: 'Szolgáltató',
      blocks: [`A snapeyes.com oldalt és a SnapEyes márkát az ${companyHu()}, egy litvániai székhelyű vállalkozás üzemelteti.`, { dl: rowsHu() }],
    },
    {
      id: 'contact',
      title: 'Kapcsolat',
      blocks: [
        SELLER.phone ? `A leggyorsabban e-mailben érhet el minket: ${MAIL}. Telefonon: ${SELLER.phone}.` : `A leggyorsabban e-mailben érhet el minket: ${MAIL}.`,
        `Ha el szeretne állni egy megrendeléstől, az online [„${WITHDRAWAL_ONLINE_HU.button}”](${withdrawFunctionHrefHu()}) funkciónkat is használhatja.`,
      ],
    },
    {
      id: 'images',
      title: 'A képekről',
      blocks: [
        'A kezdőlapunk mintaképei az alapító saját szemét mutatják, telefonnal fotózva és a szoftverünkkel elkészítve. Az előnézeti eszközben kipróbálható mintaszemet mesterséges intelligencia generálta, és ezt mindig jelöljük is.',
      ],
    },
    {
      id: 'more',
      title: 'További jogi információk',
      blocks: [
        'Hogyan kezeljük az adatait: [Adatkezelési tájékoztató](doc:privacy). Fájl vásárlása: [ÁSZF](doc:terms) és [Elállási tájékoztató](doc:withdrawal). Fogyasztói jogviták: [Panaszkezelés, jogviták és alkalmazandó jog](doc:terms#disputes).',
      ],
    },
  ],
};
