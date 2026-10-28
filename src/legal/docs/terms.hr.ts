// Opći uvjeti prodaje: the Croatian twin of `en` in src/legal/docs/terms.ts, same section ids and blocks in the same
// order, the same facts from src/landing/config.ts (through ../facts). Everything the English header says holds here
// too: no ODR link, no VAT number, no promise the code does not keep, the right of withdrawal ends when making the file
// begins (or with the 14-day period, counted as withdraw.py period_end counts it), the seller line has no phone (owner
// decision).
// Croatian law behind the wording (Zakon o zaštiti potrošača, NN 19/22, 59/23, 59/26; it calls the right of withdrawal
// "pravo na jednostrani raskid ugovora", so these terms do too):
//  - čl. 74. st. 3.: the order button says "narudžba s obvezom plaćanja" or a similar unambiguous wording. Our button
//    (CHECKOUT_LEGAL.hr.continueButton) places no order; the binding order is Stripe's pay button (Stripe Checkout,
//    locale "hr"), which the terms say ("Narudžbu s obvezom plaćanja izvršavate kada ondje potvrdite plaćanje gumbom za
//    plaćanje."). Whether Stripe's own Croatian label alone is unambiguous enough is a question for a lawyer, as the
//    German "Bezahlen" is.
//  - čl. 79. st. 5.: 14 days from the conclusion of the contract for digital content; čl. 86. st. 1. t. 13.: the digital
//    content exception (express prior consent, acknowledgement of losing the right, the confirmation of čl. 76.);
//    čl. 81.a: the online function ("raskid ugovora", "potvrditi raskid ugovora"); čl. 83.: refund within 14 days.
//  - The counting of the period (the day of payment not counted, a last day on a Saturday, Sunday or public holiday
//    moved to the next working day) is Regulation 1182/71 Art. 3, as withdraw.py period_end counts it.
//  - Out of court: the seller is Lithuanian, so the out-of-court body stays the Lithuanian Valstybinė vartotojų teisių
//    apsaugos tarnyba (VVTAT); no ODR link (the platform closed on 20 July 2025). "disputes" names the Croatian Act as the
//    mandatory law a consumer living in Croatia keeps (Rome I Art. 6(2)).
//  - VAT: the owner's sentence wherever a price is final ("MB „Portretizuokis“ nije obveznik PDV-a, stoga se PDV ne
//    obračunava."), built from company('hr') so that it follows config.ts.
//  - The contract languages are named ("Jezici ugovora: hrvatski, engleski, njemački, litavski i mađarski."): the other
//    languages' terms must name Croatian too (the build checks it, scripts/check_texts.mjs CONTRACT).
//  - The latest delivery time is "u roku od N sati" (satiGen below: the genitive after "od", "1 sata", "2 sata",
//    "48 sati").
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { DELIVERY_MAX_HOURS, MAIL, PRICE_CENTS, SELLER, address, company, eur, phoneSuffix, representedSuffix } from '../facts';
import { aiBlocks } from '../../shared/aiMaterial';
import { hrForm } from '../../shared/hr';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../../shared/legal';

const companyHr = company('hr');
const addressHr = address('hr');
const phoneSuffixHr = phoneSuffix('hr');
const representedSuffixHr = representedSuffix('hr');
const eurHr = (cents: number) => eur(cents, 'hr');
const WITHDRAWAL_ONLINE_HR = WITHDRAWAL_ONLINE.hr;
const CHECKOUT_LEGAL_HR = CHECKOUT_LEGAL.hr;

/** "48 sati", "1 sata", "2 sata": hours in the genitive, after "u roku od". */
const satiGen = (n: number) => `${n} ${hrForm(n, 'sata', 'sata', 'sati')}`;

const TRANSPARENCY_HR = 'Boja potječe s vaše vlastite fotografije. Ondje gdje vaš mobitel nije mogao zabilježiti najfinija vlakna, naša ih umjetna inteligencija obnavlja.';
const PX = '4096 px';
const SQUARE = '4096 × 4096 px';

const STANDARD_LIST_NOTE_HR =
  'Gornja tablica naš je standardni cjenik. S vremena na vrijeme, na ograničeno razdoblje, isprobavamo druge cjenike na nekim nasumično odabranim posjetiteljima. Uvijek plaćate cijene koje su vam prikazane na stranici umjetničkog djela prije plaćanja i na stranici za plaćanje, a e-poruka s potvrdom narudžbe navodi cjenik koji se primijenio na vašu narudžbu. Koji cjenik vidite nikada ne ovisi o zemlji u kojoj živite, nego samo o tržištu (valuti) koje odaberete.';
const PAY_HR = 'Plaćate unaprijed putem našeg pružatelja usluga plaćanja Stripe, načinima plaćanja prikazanima na stranici za plaćanje.';

export const hr: LegalDoc = {
  title: 'Opći uvjeti prodaje',
  description:
    'Uvjeti za narudžbu digitalnog umjetničkog djela šarenice SnapEyes: proizvod, cijene, plaćanje, isporuka, vaša licencija, pravo na jednostrani raskid ugovora i prigovori.',
  lead: 'Ovi uvjeti vrijede za svaku narudžbu izvršenu na snapeyes.com. Pročitajte ih prije narudžbe. Besplatni pregled nudi se bez ikakve obveze.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'S kim sklapate ugovor',
      blocks: [
        `Ugovor sklapate s ${companyHr}, malim partnerskim društvom prema pravu Republike Litve (mažoji bendrija)${representedSuffixHr}, matični broj ${SELLER.code}, ${addressHr}, e-pošta ${MAIL}${phoneSuffixHr} (u daljnjem tekstu „mi“ ili „SnapEyes“). Svi su podaci navedeni u našem [Impresumu](doc:imprint).`,
        'Naša je ponuda namijenjena potrošačima. Ako imate manje od 18 godina, zamolite roditelja ili skrbnika da naruči umjesto vas.',
      ],
    },
    {
      id: 'product',
      title: 'Što kupujete',
      blocks: [
        `Personalizirano digitalno umjetničko djelo izrađeno od vaše vlastite fotografije oka (ili više očiju), u stilu, rasporedu i s natpisom koje odaberete. Dobivate jednu slikovnu datoteku (JPEG) bez vodenog žiga: ${SQUARE} za jedno oko, ${PX} na najduljoj stranici za više očiju. Umjetničko djelo isporučuje se samo kao digitalna datoteka, preuzimanjem. Ne prodajemo otiske, okvire ni bilo kakve druge fizičke proizvode.`,
        `${TRANSPARENCY_HR} Umjetničko djelo stoga je umjetnička obnova, a ne medicinska ili mikroskopska snimka, i nije prikladno ni za kakvu medicinsku svrhu ni za identifikaciju osobe.`,
        ...aiBlocks('hr'),
      ],
    },
    {
      id: 'preview',
      title: 'Vaš pregled i vaša datoteka',
      blocks: [
        'Prije narudžbe vidite besplatni pregled s vodenim žigom i odobravate ga. Vaša datoteka slijedi pregled koji ste odobrili: isto oko, stil, raspored, redoslijed očiju i natpis, s istom bojom i tonom, izrađena jednom u punoj razlučivosti. U punoj veličini naša umjetna inteligencija dodaje fine detalje vlakana koje pregled zbog svoje male veličine ne može prikazati, pa se najfiniji detalji mogu malo razlikovati od pregleda. Pregled s pet do osam očiju izrađuje se od manjih kopija vaših fotografija, pa je grublji od vaše datoteke.',
        'Ako se vaša datoteka jasno razlikuje od pregleda koji ste odobrili (primjerice po boji, svjetlini ili zjenici), to je nedostatak: pogledajte [Prigovori i nedostaci](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'Kako se sklapa ugovor',
      blocks: [
        `Pregledi i cijene na našoj internetskoj stranici još nisu obvezujuća ponuda. Prije plaćanja možete provjeriti svoje oči, stil, raspored i natpis te ispraviti svaki unos tako da se vratite ili ponovno snimite fotografiju. Zatim našim gumbom „${CHECKOUT_LEGAL_HR.continueButton}“ otvarate stranicu za plaćanje našeg pružatelja usluga plaćanja Stripe; taj gumb još ne izvršava narudžbu. Na toj stranici upisujete svoju adresu e-pošte i podatke za plaćanje te ih možete ispraviti. Narudžbu s obvezom plaćanja izvršavate kada ondje potvrdite plaćanje gumbom za plaćanje.`,
        'Ugovor je sklopljen kada je vaše plaćanje potvrđeno. Tada se otvara vaša stranica narudžbe, a njezinu poveznicu šaljemo vam e-poštom zajedno s potvrdom narudžbe. Čim je ta e-poruka poslana, ondje počinjemo izrađivati vašu datoteku.',
        'Jezici ugovora: hrvatski, engleski, njemački, litavski i mađarski.',
        'Vašu narudžbu pohranjujemo s podacima o ugovoru: naručeno umjetničko djelo, cijena, datum, vaša adresa e-pošte i vaš pristanak da odmah započnemo. Vaša stranica narudžbe prikazuje te podatke sve dok čuvamo vašu narudžbu. Zasebnu kopiju ovih uvjeta za svaku narudžbu ne čuvamo. Umjesto toga, e-poruka s potvrdom narudžbe sadrži, kao tekst, podatke o vašoj narudžbi, ove uvjete i informacije o pravu na jednostrani raskid ugovora s primjerkom obrasca o jednostranom raskidu, u verziji koja je vrijedila kada ste naručili: sačuvajte tu e-poruku. Ovu stranicu također možete u bilo kojem trenutku spremiti ili ispisati.',
      ],
    },
    {
      id: 'prices',
      title: 'Cijene i plaćanje',
      blocks: [
        {
          dl: [
            ['Jedno oko, Clean Iris', eurHr(PRICE_CENTS.studioBlack)],
            ['Jedno oko, bilo koji drugi stil', eurHr(PRICE_CENTS.artBackground)],
            ['Dva oka, bilo koji stil', eurHr(PRICE_CENTS.coupleDuo)],
            ['Svako dodatno oko', `+${eurHr(PRICE_CENTS.extraEye)}`],
          ],
        },
        `Sve su cijene konačne i iskazane u eurima. ${companyHr} nije obveznik PDV-a, stoga se PDV ne obračunava. Troškova isporuke nema.`,
        STANDARD_LIST_NOTE_HR,
        PAY_HR,
      ],
    },
    {
      id: 'delivery',
      title: 'Isporuka',
      blocks: [
        `Vaša stranica narudžbe izrađuje vašu datoteku čim je poslana e-poruka s potvrdom narudžbe, obično u roku od minute nakon plaćanja; izrada obično traje nekoliko minuta. Ako zatvorite stranicu prije nego što je datoteka gotova, izrada se nastavlja kada je ponovno otvorite putem poveznice iz e-poruke. Ako naša automatska provjera kvalitete označi datoteku, prije isporuke sami je pregledamo i javimo vam se e-poštom kada bude spremna. **Vaša datoteka bit će spremna za preuzimanje na vašoj stranici narudžbe najkasnije u roku od ${satiGen(DELIVERY_MAX_HOURS)} nakon potvrde vašeg plaćanja.** Sa svoje stranice narudžbe datoteku možete preuzeti u bilo kojem trenutku dok je čuvamo: 12 mjeseci od plaćanja (pogledajte [Politiku privatnosti](doc:privacy)). Svaka poveznica za preuzimanje koju stranica izradi vrijedi 7 dana; stranica izrađuje novu svaki put kada je otvorite. Ako izgubite e-poruku, pišite nam.`,
        'Poveznica na vašu stranicu narudžbe sadrži privatni ključ: svatko tko je ima može preuzeti vaše umjetničko djelo, zato je nikome ne dajte. Preuzmite svoju datoteku i sačuvajte kopiju. Nakon 12 mjeseci ona se briše i ne može se vratiti.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Pravo na jednostrani raskid ugovora',
      blocks: [
        `Kao potrošač u pravilu imate pravo na jednostrani raskid ugovora u roku od 14 dana. Kod digitalne datoteke to pravo prestaje ranije: prije plaćanja tražimo od vas da pristanete da s izradom vaše datoteke započnemo odmah, prije isteka roka za jednostrani raskid, i da potvrdite da ste upoznati s time da gubite pravo na jednostrani raskid čim započnemo. Ono stoga prestaje čim počnemo izrađivati vašu datoteku (ispunjenje ugovora); počinjemo tek nakon što je poslana e-poruka s potvrdom narudžbe, obično u roku od minute nakon plaćanja, dok je vaša stranica narudžbe otvorena. To vrijedi i dok se datoteka još izrađuje ili čeka našu provjeru kvalitete. Ako još nismo počeli, ono prestaje istekom roka od 14 dana za jednostrani raskid: dan vašeg plaćanja ne računa se, a ako posljednji dan roka pada u subotu, nedjelju ili na državni praznik, rok istječe na kraju sljedećeg radnog dana. Dok traje vaše pravo na jednostrani raskid, ugovor možete raskinuti e-poštom, poštom ili putem interneta gumbom „${WITHDRAWAL_ONLINE_HR.button}“; poveznica za raskid u e-poruci s potvrdom narudžbe otvara tu funkciju za vašu narudžbu, a da ne pokrene izradu vaše datoteke. Sve informacije, mrežna funkcija i primjerak obrasca o jednostranom raskidu nalaze se na stranici [Pravo na jednostrani raskid ugovora](doc:withdrawal).`,
      ],
    },
    {
      id: 'photos',
      title: 'Vaše fotografije',
      blocks: [
        'Učitavajte samo fotografije vlastitog oka ili oka osobe koja je na to pristala (za dijete: roditelj ili skrbnik). Učitavanjem fotografije potvrđujete da je smijete upotrijebiti u tu svrhu.',
        'Prava na vašu fotografiju ostaju vaša. Koristimo je samo za izradu vašeg pregleda i vašeg umjetničkog djela, kako je opisano u našoj [Politici privatnosti](doc:privacy).',
        'Narudžbu možemo odbiti i vratiti svaku uplatu u cijelosti ako fotografija očito krši ova pravila.',
      ],
    },
    {
      id: 'licence',
      title: 'Što smijete raditi sa svojim umjetničkim djelom',
      blocks: [
        'Dobivate neisključivu, trajnu licenciju za korištenje svojeg umjetničkog djela u osobne, nekomercijalne svrhe. Možete ga, primjerice, ispisati za sebe (kod kuće ili u tiskari), uokviriti, pokloniti, koristiti kao pozadinu na svojim uređajima i dijeliti na svojim osobnim društvenim mrežama.',
        'Bez našeg dopuštenja (dovoljna je e-poruka) ne smijete prodavati umjetničko djelo ni proizvode izrađene od njega, davati drugima prava na njega niti ga koristiti za oglašavanje ili druge komercijalne svrhe.',
        'Stilovi, pozadine, rasporedi i dizajn SnapEyes ostaju naši, uključujući sva autorska prava na njima. Isto vrijedi i za preglede s vodenim žigom.',
      ],
    },
    {
      id: 'defects',
      title: 'Prigovori i nedostaci',
      blocks: [
        `Vaša zakonska prava u slučaju digitalnog sadržaja koji nije u skladu s ugovorom vrijede u cijelosti. Ako je vaša datoteka neispravna, primjerice ne može se preuzeti ili otvoriti, oštećena je, manja je od obećanog ili se jasno razlikuje od pregleda koji ste odobrili, pišite na ${MAIL} i navedite broj narudžbe. Datoteku ćemo besplatno ponovno izraditi ili vam, ako to ne otkloni nedostatak, vratiti novac.`,
      ],
    },
    {
      id: 'liability',
      title: 'Odgovornost',
      blocks: [
        'Odgovaramo bez ograničenja za namjeru i krajnju nepažnju, za povredu života, tijela ili zdravlja te uvijek kada to propisuju prisilni propisi. Inače, za običnu nepažnju odgovaramo samo za povredu bitnih ugovornih obveza i samo za štetu koja je tipična i predvidljiva za ovu vrstu ugovora. Besplatni pregled nudi se takav kakav jest, bez ikakvog prava na njegovu dostupnost.',
      ],
    },
    {
      id: 'disputes',
      title: 'Sporovi i mjerodavno pravo',
      blocks: [
        'Ako nešto nije u redu, najprije nam pišite: većina problema brzo se riješi e-poštom.',
        'Ako se ne uspijemo dogovoriti, potrošači se mogu obratiti litavskoj Državnoj službi za zaštitu prava potrošača (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)), koja izvansudski rješava potrošačke sporove, ili tijelima za zaštitu potrošača i sudovima svoje zemlje.',
        'Mjerodavno je pravo Republike Litve. Ako ste potrošač koji živi u drugoj zemlji EU-a, zadržavate zaštitu prisilnih propisa o zaštiti potrošača te zemlje (u Hrvatskoj: Zakon o zaštiti potrošača).',
      ],
    },
    {
      id: 'changes',
      title: 'Izmjene ovih uvjeta',
      blocks: ['Na vašu narudžbu primjenjuju se uvjeti koji su vrijedili u trenutku kada ste je izvršili.'],
    },
  ],
};

// No forint edition: the Hungarian edition (the hu market) has no Croatian texts (src/shared/legal.ts EDITION_LANGS), so there
// is no Croatian twin of huHufPrices.
