// Lithuanian landing page copy: the twin of `en` in src/landing/copy.ts, same keys, same order, typed by the same Copy
// interface. Polite "Jūs" (capitalised in every form: Jūs, Jūsų, Jums, Jus), one word per idea
// on every page (rainelė, kūrinys, peržiūra, atkurti, skaidulos, DI). Every sentence says only what the English one says: no reviews, counts, guarantees or products.
import type { Copy } from './copy';
import { WITHDRAWAL_ONLINE } from '../shared/legal';
import { akiuWord, akys } from '../shared/lt';

// the landing page's transparency promise (owner decision 5), word for word the same in /try (src/try/copy.lt.ts)
const TRANSPARENCY_LT = 'Spalva paimta iš Jūsų pačių nuotraukos. Kur telefonas neužfiksavo smulkiausių skaidulų, jas atkuria mūsų DI.';

// Measured deliverable, as in the English file: one eye 4096 x 4096 px, several eyes 4096 px on the longest side.
const PX = '4096 px';
const SQUARE = '4096 × 4096 px';

export const lt: Copy = {
  meta: {
    title: 'SnapEyes Private Atelier - preciziškas rainelės menas iš išmaniojo telefono',
    description:
      'Nufotografuokite vieną akį galine telefono kamera ir pamatykite savo rainelę kaip meno kūrinį įvairiais stiliais. Peržiūra su vandens ženklu nemokama.',
    shareDescription: 'Nufotografuokite vieną akį telefonu ir pamatykite savo rainelę kaip meno kūrinį įvairiais stiliais. Peržiūra su vandens ženklu nemokama.',
    locale: 'lt_LT',
  },
  langName: 'Lietuvių',
  switchLabel: 'Kalba',
  brandTag: 'Private Atelier',
  nav: { beforeAfter: 'Prieš ir po', how: 'Kaip tai veikia', styles: 'Stiliai', pricing: 'Kainos', faq: 'Klausimai', privacy: 'Privatumas' },
  navLabels: { main: 'Pagrindinė navigacija', footer: 'Poraštė' },
  cta: 'Sukurti nemokamą peržiūrą',
  ctaShort: 'Nemokama peržiūra',
  // /try speaks Lithuanian too (src/try/copy.lt.ts): nothing to note under the calls to action
  ctaNote: '',
  hero: {
    eyebrow: 'SnapEyes Private Atelier',
    title: 'Preciziškas rainelės menas iš išmaniojo telefono',
    lead:
      'Nufotografuokite vieną akį galine telefono kamera. Surasime Jūsų rainelę, ją atkursime ir perteiksime Jūsų pasirinktu stiliumi. Rezultatą pirmiausia pamatysite nemokamai.',
    points: ['Nemokama peržiūra kiekvienu stiliumi, su vandens ženklu', 'Maždaug minutė, be registracijos'],
    soon: `Netrukus: Jūsų kūrinys kaip skaitmeninis ${PX} failas`,
    ready: (from) => `Jūsų kūrinys kaip skaitmeninis ${PX} failas, nuo ${from}`,
    secondary: 'Pamatyti tikrą vaizdą prieš ir po',
    imageAlt: 'Įkūrėjo rainelė Celestial Gold stiliumi',
    insetAlt: 'Įkūrėjo tos pačios akies nuotrauka telefonu',
    insetLabel: 'Nuotrauka telefonu, 315 px',
    caption: 'Mantas, įkūrėjas: nufotografuota namuose telefonu',
    styleNote: 'Kūrinys Celestial Gold stiliumi',
  },
  beforeAfter: {
    eyebrow: 'Tikras vaizdas prieš ir po',
    title: 'Viena akis, vienas telefonas, vienas rezultatas',
    intro:
      'Tai paties įkūrėjo akis. Kairėje: nuotrauka telefonu, apkirpta iki rainelės, originalaus 315 px dydžio. Dešinėje: ta pati akis Clean Iris stiliumi, sukurta ta pačia programa, kuri kuria ir Jūsų peržiūrą.',
    before: 'Prieš: nuotrauka telefonu',
    after: 'Po: Clean Iris',
    beforeAlt: 'Prieš: įkūrėjo akis, kaip ją užfiksavo telefonas',
    afterAlt: 'Po: ta pati akis Clean Iris stiliumi',
    sliderLabel: 'Palyginti prieš ir po',
    caption: 'Mantas, įkūrėjas: nufotografuota namuose telefonu',
    transparencyTitle: 'Kas paimta iš Jūsų, o ką prideda DI',
    transparency: TRANSPARENCY_LT,
  },
  how: {
    eyebrow: 'Kaip tai veikia',
    title: 'Trys žingsniai, jokios studijos',
    steps: [
      {
        title: 'Nufotografuokite vieną akį',
        body: 'Naudokite galinę kamerą su 2x arba 3x priartinimu, ne priekinę kamerą. Dienos šviesa pro langą, iš šono, maždaug 10 cm atstumu. Padarykite nuo trijų iki penkių kadrų: įvertiname kiekvieną ir panaudojame geriausią.',
      },
      {
        title: 'Pamatykite nemokamą peržiūrą',
        body: 'Maždaug per minutę Jūsų rainelė pasirodys kiekvienu stiliumi, su vandens ženklu. Be registracijos, nieko mokėti nereikia.',
      },
      {
        title: `Užsisakykite ${PX} failą`,
        body: `Pasirinkite stilių ir gaukite savo kūrinį kaip skaitmeninį failą, kurio ilgoji kraštinė yra ${PX}. Jis sukuriamas vieną kartą visa raiška, kai patvirtinate peržiūrą. Užsakymus pradėsime priimti netrukus.`,
        bodyOpen: `Pasirinkite stilių, sumokėkite per Stripe ir gaukite savo kūrinį kaip skaitmeninį failą, kurio ilgoji kraštinė yra ${PX}. Jis sukuriamas vieną kartą visa raiška, kai tik patvirtinamas Jūsų užsakymas.`,
      },
    ],
  },
  styles: {
    eyebrow: 'Stiliai',
    title: 'Ta pati akis, skirtingi stiliai',
    intro:
      'Kiekvienas toliau esantis vaizdas yra įkūrėjo akis iš aukščiau pateikto palyginimo prieš ir po, mūsų programos sukurta kiekvienu stiliumi. Jūsų peržiūroje bus vandens ženklas; čia jo nėra.',
    oneEye: 'Viena akis',
    desc: {
      'solo.powder': 'Kraštas skyla į grūdelius Jūsų akies spalvomis.',
      'solo.universe': 'Padidinta Jūsų rainelė užpildo visą kūrinio plotą.',
      'solo.splash': 'Kraštas iškyla kaip vandens karūna.',
      'solo.gold': 'Plonas auksinis žiedas ir šviesos aureolė aplink rainelę.',
      'solo.radiance': 'Ploni šviesos spinduliai Jūsų rainelės spalvomis.',
      'solo.clean': 'Tik Jūsų atkurta rainelė grynai juodame fone.',
      'duo.kiss_collision': 'Dvi rainelės, besiliečiančios kraštais.',
      'duo.collision_infinity': 'Dvi rainelės persidengia kaip begalybės ženklas.',
      'duo.clean': 'Ta pati pora be miltelių.',
      'grp.collision': 'Trys rainelės trikampyje.',
    },
    alt: (name) => `Įkūrėjo rainelė ${name} stiliumi`,
  },
  pricing: {
    eyebrow: 'Kainos',
    title: 'Aiškios kainos už vieną skaitmeninį failą',
    notice: 'Užsakymus pradėsime priimti netrukus - peržiūra jau šiandien nemokama.',
    noticeOpen: 'Pradėkite nuo nemokamos peržiūros: užsisakysite tik tada, kai rezultatas Jums patiks.',
    previewTitle: 'Peržiūra',
    previewPrice: 'Nemokamai',
    previewItems: ['Kiekvienas stilius', 'Su vandens ženklu', 'Jau šiandien'],
    oneEyeTitle: 'Viena akis',
    oneEyeNote: 'Jūsų rainelė kaip atskiras kūrinys, Jūsų pasirinktu stiliumi.',
    artBackground: 'Bet kuris kitas stilius',
    artBackgroundNote: '{styles}',
    severalTitle: 'Kelios akys',
    severalNote: 'Nuo dviejų iki {max} akių viename kūrinyje: Jūsų ir Jūsų artimųjų.',
    severalSoon: 'Nemokama peržiūra jau dabar. Šios grupės užsakymai bus galimi netrukus.',
    eyes: (n) => akys(n),
    perEye: (price, max) => `+${price} už kiekvieną papildomą akį, iki ${max} ${akiuWord(max)}`,
    footnote: `Kiekvienas užsakymas yra vienas skaitmeninis failas be vandens ženklo, kurio ilgoji kraštinė yra ${PX} (vienos akies: ${SQUARE}). Kainos nurodytos eurais. Tai galutinės kainos: MB „Portretizuokis“ nėra PVM mokėtoja, todėl PVM netaikomas.`,
    footnoteAud: `Kiekvienas užsakymas yra vienas skaitmeninis failas be vandens ženklo, kurio ilgoji kraštinė yra ${PX} (vienos akies: ${SQUARE}). Kainos nurodytos Australijos doleriais (A$). Kiekviena kaina yra bendra kaina: GST netaikomas.`,
    footnoteHuf: `Kiekvienas užsakymas yra vienas skaitmeninis failas be vandens ženklo, kurio ilgoji kraštinė yra ${PX} (vienos akies: ${SQUARE}). Kainos nurodytos Vengrijos forintais (Ft). Tai galutinės kainos: MB „Portretizuokis“ nėra PVM mokėtoja, todėl PVM netaikomas.`,
  },
  curator: {
    eyebrow: 'Kuratorius',
    title: 'Ateljė užkulisiuose',
    role: 'SnapEyes studijos kuratorius',
    note:
      'Akis šiame puslapyje yra mano, nufotografuota namuose mano telefonu. Peržiūra nemokama, kad rezultatą galėtumėte įvertinti savo akimis dar prieš bet kokį mokėjimą.',
    photoAlt: 'Manto rainelė',
    offer: 'Nepavyksta padaryti ryškaus kadro? Atsiųskite man geriausias savo nuotraukas ir per 24 valandas asmeniškai jas peržiūrėsiu.',
    offerCta: 'Rašyti Mantui',
  },
  privacy: {
    eyebrow: 'Jūsų nuotrauka',
    title: 'Pažadas dėl Jūsų akies',
    items: [
      { title: 'Tik Jūsų kūriniui', body: 'Jūsų nuotrauka naudojama tik Jūsų kūriniui sukurti. Iš kiekvieno kadro įrašome kelis matavimus, niekada ne patį vaizdą, kad tobulintume fotografavimo patarimus.' },
      { title: 'Niekada tapatybei nustatyti', body: 'Ji niekada nenaudojama kieno nors tapatybei nustatyti, niekada neparduodama ir nenaudojama DI mokyti.' },
      {
        title: 'Nemokamos peržiūros nesaugomos',
        body: 'Jūsų nuotrauka apdorojama, o po to ištrinama; mes jos nesaugome. Jei užsisakote, Jūsų užsakymo failus (ne Jūsų telefono nuotrauką) saugome 12 mėnesių, kad galėtumėte juos atsisiųsti.',
      },
      {
        title: 'Keletas išorinių paslaugų',
        body: 'Puslapį ir peržiūrą aptarnauja Vercel, atkūrimą atlieka Google Gemini API (Google užklausų žurnalus saugo ribotą laiką). Užsakymams dar naudojame Stripe mokėjimams ir privačią Supabase saugyklą ES.',
      },
    ],
    controller: 'Už Jūsų duomenis atsako MB „Portretizuokis“, Kaunas, Lietuva (visi rekvizitai pateikti šio puslapio apačioje).',
    rights: 'Galite paprašyti informacijos, kokius Jūsų duomenis turime, juos ištaisyti ar ištrinti, taip pat pateikti skundą duomenų apsaugos priežiūros institucijai.',
    policyLink: 'Skaityti visą privatumo politiką',
  },
  faq: {
    eyebrow: 'Klausimai',
    title: 'Prieš pradedant',
    items: [
      {
        q: 'Kokį telefoną ir kamerą naudoti?',
        a: 'Tinka bet kuris naujesnis išmanusis telefonas su gera galine kamera. Naudokite galinę kamerą su 2x arba 3x priartinimu, ne priekinę kamerą. Fotografuokite dienos šviesoje pro langą, iš šono, ne su lempa ir ne su blykste. Laikykite telefoną maždaug 10 cm nuo akies, bakstelėkite rainelę, kad kamera ją sufokusuotų, ir padarykite nuo trijų iki penkių kadrų.',
      },
      {
        q: 'Ar tai tikrai mano akis?',
        a: `Taip. ${TRANSPARENCY_LT} Taigi pačios smulkiausios detalės yra atkurtos, o ne nufotografuotos mikroskopu. Nemokama peržiūra leidžia įvertinti rezultatą dar prieš bet kokį mokėjimą.`,
      },
      {
        q: 'Ką gausiu?',
        a: `Savo kūrinį kaip vieną skaitmeninį failą be vandens ženklo, Jūsų pasirinktu stiliumi: vienos akies kūrinys yra ${SQUARE}, o kelių akių kūrinio ilgoji kraštinė yra ${PX}.`,
      },
      {
        q: 'Kiek tai užtrunka?',
        a: 'Nemokama peržiūra užtrunka maždaug minutę. Kai pradėsime priimti užsakymus, Jūsų failas bus sukurtas vieną kartą visa raiška, Jums patvirtinus peržiūrą; tai užtrunka maždaug pusę minutės vienai akiai.',
        aOpen: 'Nemokama peržiūra užtrunka maždaug minutę. Jums sumokėjus, failas sukuriamas vieną kartą visa raiška, paprastai per maždaug pusę minutės vienai akiai.',
      },
      {
        q: 'Kas nutinka mano nuotraukai?',
        a: 'Nemokamai peržiūrai Jūsų nuotrauka apdorojama, o po to ištrinama; mes jos nesaugome. Jei užsisakote, Jūsų užsakymo failus (ne Jūsų telefono nuotrauką) saugome 12 mėnesių, kad galėtumėte juos vėl atsisiųsti, o tada ištriname. Jūsų rainelė niekada nenaudojama tapatybei nustatyti ar DI mokyti. Išsamiau apie tai rašoma mūsų privatumo politikoje, kurios nuoroda yra šio puslapio apačioje.',
      },
      {
        q: 'Ar galiu atsisakyti užsakymo?',
        a: `Jūsų failą pradedame kurti, kai tik išsiunčiamas užsakymo patvirtinimo el. laiškas, paprastai per minutę nuo apmokėjimo. Prieš mokėjimą Jūs sutinkate, kad pradėtume iš karto, todėl 14 dienų teisė atsisakyti sutarties baigiasi, kai tik pradedame kurti Jūsų failą. Iki tol sutarties galite atsisakyti el. paštu arba internetu mygtuku „${WITHDRAWAL_ONLINE.lt.button}“, kurį rasite šio puslapio apačioje arba per sutarties atsisakymo nuorodą užsakymo patvirtinimo el. laiške. Jei Jūsų failas turi trūkumų arba aiškiai skiriasi nuo patvirtintos peržiūros, parašykite mums: sukursime jį iš naujo arba grąžinsime pinigus. Išsamiau apie tai rašoma mūsų pardavimo sąlygose ir informacijoje apie teisę atsisakyti sutarties, kurių nuorodos yra šio puslapio apačioje.`,
      },
      {
        q: 'Kada galėsiu užsisakyti?',
        a: 'Užsakymus pradėsime priimti netrukus. Iki tol peržiūra nemokama.',
        qOpen: 'Kaip užsisakyti?',
        aOpen: 'Iš karto po nemokamos peržiūros, tame pačiame puslapyje: pasirinkite stilių, pažymėkite langelį dėl skaitmeninio failo ir pereikite į Stripe mokėjimo puslapį, kuriame sumokėsite. Iš karto atsidarys Jūsų užsakymo puslapis, o jo nuorodą gausite el. paštu.',
      },
    ],
  },
  final: {
    title: 'Pamatykite savo rainelę',
    body: 'Tereikia telefono, geros šviesos ir maždaug minutės.',
  },
  footer: {
    operatedBy: 'SnapEyes paslaugą teikia',
    company: 'MB „Portretizuokis“',
    companyCode: 'Įmonės kodas',
    country: 'Lietuva',
    contact: 'Kontaktai',
    representedBy: 'Atstovauja',
    phone: 'Telefonas',
    rights: 'SnapEyes',
    currency: 'Kainų valiuta',
  },
  // no Australian offer in Lithuanian: the Australian market's pages exist in English and German only
  marketHint: {
    label: 'Kainos Jūsų valiuta',
    close: 'Ne, ačiū',
    huf: { text: 'Perkate iš Vengrijos? Peržiūrėkite mūsų kainas Vengrijos forintais (Ft).', show: 'Rodyti kainas forintais' },
  },
};
