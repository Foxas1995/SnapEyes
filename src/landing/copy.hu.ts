// Hungarian ("hu") landing page copy: every key of src/landing/copy.ts `en`, in the same order. Friendly "te"
// (tegeződés), as Hungarian iris studios and gift shops write. Every sentence must stay as true as
// the English one: no reviews, customer counts, guarantees, awards, physical products, struck-through prices, timers
// or "only today". Honest naming: Hungarians know „íriszfotózás” as studio macro photography, so the
// product is an „íriszalkotás a telefonos fotódból”, never a studio macro photo.
// Prices arrive already formatted (hero.ready, pricing.perEye) by src/shared/markets.ts money(): "6 990 Ft" on the
// forint list, "19,97 €" on the euro list. The footnotes name the currency (pricing.footnote for euros, footnoteHuf).
import type { Copy } from './copy';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../shared/legal';

// src/try/copy.hu.ts result.transparency and src/legal/docs/terms.hu.ts repeat this word for word
export const TRANSPARENCY_HU =
  'A szín a saját fotódból származik. Ahol a telefonod nem tudta rögzíteni a legfinomabb rostokat, ott a mesterséges intelligenciánk állítja helyre őket.';

// the measured deliverable, as in copy.ts (4096 px on the longest side; one eye is square)
const PX = '4096 px';
const SQUARE = '4096 × 4096 px';

export const hu: Copy = {
  meta: {
    title: 'SnapEyes Private Atelier - Precíz íriszalkotás a telefonos fotódból',
    description:
      'Fotózd le az egyik szemed a telefonod hátsó kamerájával, és nézd meg a saját íriszed műalkotásként, többféle stílusban. A vízjeles előnézet ingyenes.',
    shareDescription:
      'Fotózd le az egyik szemed a telefonoddal, és nézd meg a saját íriszed műalkotásként, többféle stílusban. A vízjeles előnézet ingyenes.',
    locale: 'hu_HU',
  },
  langName: 'Magyar',
  switchLabel: 'Nyelv',
  brandTag: 'Private Atelier',
  nav: { beforeAfter: 'Előtte és utána', how: 'Így működik', styles: 'Stílusok', pricing: 'Árak', faq: 'GYIK', privacy: 'Adatvédelem' },
  navLabels: { main: 'Fő navigáció', footer: 'Lábléc' },
  cta: 'Ingyenes előnézetet kérek',
  ctaShort: 'Ingyenes előnézet',
  ctaNote: '',
  hero: {
    eyebrow: 'SnapEyes Private Atelier',
    title: 'Precíz íriszalkotás a telefonos fotódból',
    lead:
      'Fotózd le az egyik szemed a telefonod hátsó kamerájával. Megkeressük az íriszed, helyreállítjuk, és a választott stílusban műalkotássá formáljuk. Az eredményt először te látod, ingyen.',
    points: ['Ingyenes vízjeles előnézet minden stílusban', 'Kb. egy perc, regisztráció nélkül'],
    soon: `Hamarosan: az alkotásod ${PX}-es digitális fájlként`,
    ready: (from) => `Az alkotásod ${PX}-es digitális fájlként, ${from}-tól`,
    secondary: 'Nézz meg egy valódi előtte-utána képet',
    imageAlt: 'Az alapító saját írisze Celestial Gold stílusban',
    insetAlt: 'Az alapító telefonos fotója ugyanarról a szemről',
    insetLabel: 'Telefonos fotó, 315 px',
    caption: 'Mantas, alapító - otthon, telefonnal fotózva',
    styleNote: 'Alkotás Celestial Gold stílusban',
  },
  beforeAfter: {
    eyebrow: 'Valódi előtte-utána',
    title: 'Egy szem, egy telefon, egy eredmény',
    intro:
      'Ez az alapító saját szeme. Balra a telefonos fotó, az íriszre vágva, eredeti, 315 px-es méretében. Jobbra ugyanez a szem Clean Iris stílusban, ugyanazzal a motorral elkészítve, amely a te előnézetedet is készíti.',
    before: 'Előtte: telefonos fotó',
    after: 'Utána: Clean Iris',
    beforeAlt: 'Előtte: az alapító szeme, ahogy a telefon rögzítette',
    afterAlt: 'Utána: ugyanez a szem Clean Iris stílusban',
    sliderLabel: 'Előtte és utána összehasonlítása',
    caption: 'Mantas, alapító - otthon, telefonnal fotózva',
    transparencyTitle: 'Mi származik tőled, és mit ad hozzá a mesterséges intelligencia',
    transparency: TRANSPARENCY_HU,
  },
  how: {
    eyebrow: 'Így működik',
    title: 'Három lépés, stúdió nélkül',
    steps: [
      {
        title: 'Fotózd le az egyik szemed',
        body: 'A hátsó kamerát használd 2x-es vagy 3x-os zoommal, ne a szelfikamerát. Nappali fény egy ablakból, oldalról, kb. 10 cm távolságból. Készíts három-öt felvételt: mindegyiket megmérjük, és a legjobbat használjuk.',
      },
      {
        title: 'Nézd meg az ingyenes előnézeted',
        body: 'Körülbelül egy perc alatt megjelenik az íriszed minden stílusban, vízjellel. Regisztráció és fizetés nélkül.',
      },
      {
        title: `Rendeld meg a ${PX}-es fájlt`,
        body: `Válassz stílust, és az alkotásodat digitális fájlként kapod meg, a hosszabbik oldalán ${PX} méretben: amikor jóváhagyod, egyszer, teljes felbontásban készítjük el. A rendelés hamarosan indul.`,
        bodyOpen: `Válassz stílust, fizess a Stripe-on keresztül, és az alkotásodat digitális fájlként kapod meg, a hosszabbik oldalán ${PX} méretben, egyszer, teljes felbontásban elkészítve, amint visszaigazoltuk a rendelésedet.`,
      },
    ],
  },
  styles: {
    eyebrow: 'Stílusok',
    title: 'Ugyanaz a szem, különböző stílusokban',
    intro:
      'Minden kép az alapító szemét mutatja a fenti előtte-utána képről, a motorunkkal az adott stílusban elkészítve. Az előnézeteden vízjel is van; itt azt elhagytuk.',
    oneEye: 'Egy szem',
    desc: {
      studio_black: 'Csak az íriszed, tiszta feketén.',
      celestial_gold: 'Aranyló csillagpor sávja.',
      deep_nebula: 'Csillagmező indigóban és ibolyában.',
      emerald_aurora: 'Zöld csillagpor egy leheletnyi rózsaszínnel.',
      obsidian_smoke: 'Ezüst csillagok mélyfekete háttéren.',
      supernova: 'Csillagpor vörösben és narancsban.',
    },
    alt: (name) => `Az alapító írisze ${name} stílusban`,
  },
  pricing: {
    eyebrow: 'Árak',
    title: 'Átlátható árak egy digitális fájlért',
    notice: 'A rendelés hamarosan indul: az előnézeted már ma ingyenes.',
    noticeOpen: 'Kezdd az ingyenes előnézettel: csak akkor rendelsz, ha tetszik az eredmény.',
    previewTitle: 'Előnézet',
    previewPrice: 'Ingyenes',
    previewItems: ['Minden stílus', 'Vízjellel', 'Már ma elérhető'],
    oneEyeTitle: 'Egy szem',
    oneEyeNote: 'Az íriszed egyetlen alkotásként, a választott stílusban.',
    artBackground: 'Bármely más stílus',
    artBackgroundNote: '{styles}',
    severalTitle: 'Több szem',
    severalNote: 'Kettőtől {max} szemig egy alkotáson: a tiéd és azoké, akiket szeretsz.',
    severalSoon: 'Az előnézet már most ingyenes. Ennek a csoportnak a rendelése hamarosan indul.',
    eyes: (n) => `${n} szem`,
    perEye: (price, max) => `+${price} minden további szemért, legfeljebb ${max} szemig`,
    footnote: `Minden rendelés egy vízjel nélküli digitális fájl, a hosszabbik oldalán ${PX} (egy szem esetén ${SQUARE}). Az árak euróban értendő végső árak: nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel.`,
    footnoteAud: `Minden rendelés egy vízjel nélküli digitális fájl, a hosszabbik oldalán ${PX} (egy szem esetén ${SQUARE}). Az árak ausztrál dollárban (A$) értendők. Minden ár teljes ár: GST-t nem számítunk fel.`,
    footnoteHuf: `Minden rendelés egy vízjel nélküli digitális fájl, a hosszabbik oldalán ${PX} (egy szem esetén ${SQUARE}). Az árak forintban értendő végső árak: nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel.`,
  },
  curator: {
    eyebrow: 'A kurátor',
    title: 'Az atelier mögött',
    role: 'A SnapEyes stúdió kurátora',
    note:
      'Az ezen az oldalon látható szem az enyém, otthon fotóztam a telefonommal. Az előnézet azért ingyenes, hogy a saját szemeddel ítélhesd meg az eredményt, mielőtt bármit fizetnél.',
    photoAlt: 'Mantas saját írisze',
    offer: 'Nem sikerül éles felvételt készíteni? Küldd el nekem a legjobb fotóidat, és 24 órán belül személyesen átnézem őket.',
    offerCta: 'Írj Mantasnak',
  },
  privacy: {
    eyebrow: 'A fotód',
    title: 'Ígéretünk a szemedről',
    items: [
      { title: 'Csak az alkotásodhoz', body: 'A fotódat kizárólag az alkotásod elkészítéséhez használjuk. Minden felvételből néhány mérési adatot naplózunk, a képet soha, hogy javítsuk a fotózási útmutatót.' },
      { title: 'Soha nem azonosításra', body: 'Soha nem használjuk senki azonosítására, soha nem adjuk el, és mesterséges intelligencia tanítására sem használjuk.' },
      {
        title: 'Az ingyenes előnézeteket nem őrizzük meg',
        body: 'A fotódat feldolgozzuk, majd töröljük; nem tároljuk. Ha rendelsz, a rendelésed fájljait (a telefonos fotódat nem) 12 hónapig megőrizzük, hogy újra letölthesd őket.',
      },
      {
        title: 'Néhány külső szolgáltatás',
        body: 'Az oldalt és az előnézetet a Vercel futtatja, a helyreállítást a Google Gemini API-ja végzi (a Google a kéréseket korlátozott ideig naplózza). Rendelésnél ehhez jön a Stripe a fizetéshez és egy privát Supabase-tárhely az EU-ban.',
      },
    ],
    controller: 'Az adataidért felelős: MB „Portretizuokis”, Kaunas, Litvánia (a teljes adatokat az oldal alján találod).',
    rights: 'Megkérdezheted, milyen adatokat tárolunk rólad, kérheted a helyesbítésüket vagy a törlésüket, és panaszt tehetsz egy adatvédelmi hatóságnál.',
    policyLink: 'A teljes adatkezelési tájékoztató',
  },
  faq: {
    eyebrow: 'Kérdések',
    title: 'Mielőtt belekezdesz',
    items: [
      {
        q: 'Milyen telefont és kamerát használjak?',
        a: 'Bármilyen újabb okostelefont, amelynek jó a hátsó kamerája. A hátsó kamerát használd 2x-es vagy 3x-os zoommal, ne a szelfikamerát. Nappali fénynél fotózz, egy oldalt lévő ablaknál, ne lámpafénynél és ne vakuval. Tartsd a telefont kb. 10 cm-re a szemedtől, koppints az íriszre az élességállításhoz, és készíts három-öt felvételt.',
      },
      {
        q: 'Tényleg az én szemem lesz?',
        a: `Igen. ${TRANSPARENCY_HU} A legapróbb részletek tehát helyreállítás eredményei: ez nem mikroszkópos felvétel és nem stúdiós makrofotó. Az ingyenes előnézettel megítélheted az eredményt, mielőtt bármit fizetnél.`,
      },
      {
        q: 'Mit kapok?',
        a: `Az alkotásodat egyetlen, vízjel nélküli digitális fájlként, a választott stílusban: egy szem esetén ${SQUARE}, több szem esetén a hosszabbik oldalán ${PX}.`,
      },
      {
        q: 'Mennyi ideig tart?',
        a: 'Az ingyenes előnézet kb. egy percig tart. Amint a rendelés elindul, a fájlodat a jóváhagyásod után egyszer, teljes felbontásban készítjük el, ez szemenként kb. fél percet vesz igénybe.',
        aOpen: 'Az ingyenes előnézet kb. egy percig tart. A fizetés után a fájlodat egyszer, teljes felbontásban készítjük el, általában szemenként kb. fél perc alatt.',
      },
      {
        q: 'Mi történik a fotómmal?',
        a: 'Az ingyenes előnézethez a fotódat feldolgozzuk, majd töröljük; nem tároljuk. Ha rendelsz, a rendelésed fájljait (a telefonos fotódat nem) 12 hónapig megőrizzük, hogy újra letölthesd őket, azután töröljük. Az íriszedet soha nem használjuk senki azonosítására, sem mesterséges intelligencia tanítására. A részleteket az adatkezelési tájékoztatóban találod, az oldal alján.',
      },
      {
        q: 'Elállhatok a rendeléstől?',
        a: `A fájlod elkészítését akkor kezdjük meg, amikor elment a rendelésed visszaigazoló e-mailje, ez általában a fizetés után egy percen belül megtörténik. Fizetés előtt hozzájárulsz, hogy azonnal elkezdjük, ezért a 14 napos elállási jog megszűnik, amint megkezdtük a fájlod elkészítését. Addig e-mailben vagy online, az „${WITHDRAWAL_ONLINE.hu.button}” funkcióval állhatsz el: megtalálod az oldal alján, és a visszaigazoló e-mailben kapott elállási link is oda vezet. Ha a fájlod hibás, vagy egyértelműen eltér a jóváhagyott előnézettől, írj nekünk: újra elkészítjük, vagy visszatérítjük az árát. A részleteket az ÁSZF-ben és az elállási tájékoztatóban találod, az oldal alján.`,
      },
      {
        q: 'Mikor rendelhetek?',
        a: 'A rendelés hamarosan indul. Addig az előnézet ingyenes.',
        qOpen: 'Hogyan rendelhetek?',
        aOpen: `Közvetlenül az ingyenes előnézeted után, ugyanazon az oldalon: válaszd ki a stílust, jelöld be a digitális fájlra vonatkozó négyzetet, majd a „${CHECKOUT_LEGAL.hu.continueButton}” gombbal lépj tovább a Stripe fizetési oldalára, ahol fizetsz. A rendelési oldalad azonnal megnyílik, a linkjét pedig e-mailben is elküldjük.`,
      },
    ],
  },
  final: {
    title: 'Nézd meg a saját íriszed',
    body: 'Csak a telefonodra, jó fényre és kb. egy percre van szükséged.',
  },
  footer: {
    operatedBy: 'A SnapEyes üzemeltetője',
    company: 'MB „Portretizuokis”',
    companyCode: 'Cégazonosító szám:',
    country: 'Litvánia',
    contact: 'Kapcsolat',
    representedBy: 'Képviseli:',
    phone: 'Telefon',
    rights: 'SnapEyes',
    currency: 'Árak pénzneme',
  },
  // no Australian offer in Hungarian: the Australian market's pages exist in English and German only
  marketHint: {
    label: 'Árak a saját pénznemedben',
    close: 'Nem, köszönöm',
    huf: { text: 'Magyarországról vásárolsz? Nézd meg az árainkat forintban (Ft).', show: 'Árak megjelenítése Ft-ban' },
  },
};
