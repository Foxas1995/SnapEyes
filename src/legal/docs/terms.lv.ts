// Pārdošanas noteikumi: the Latvian twin of `en` in src/legal/docs/terms.ts, same section ids and blocks in the same
// order, the same facts from src/landing/config.ts (through ../facts). Everything the English header says holds here
// too: no ODR link, no VAT number, no promise the code does not keep, the right of withdrawal ends when making the file
// begins (or with the 14-day period, counted as withdraw.py period_end counts it), the seller line has no phone (owner
// decision).
// The law behind the wording is named as the English text names it (Directive 2011/83/EU), in the words of its official
// Latvian text: "atteikuma tiesības", "atteikuma termiņš", "atteikuma veidlapas paraugs", "pastāvīgs informācijas nesējs":
//  - Art. 8(2): the order button says "pasūtījums ar pienākumu maksāt" or a similar unambiguous wording. Our button
//    (CHECKOUT_LEGAL.lv.continueButton) places no order; the binding order is Stripe's pay button (Stripe Checkout,
//    locale "lv"), which the terms say ("Saistošu pasūtījumu ar pienākumu maksāt jūs veicat, kad tur apstiprināt
//    maksājumu ar maksāšanas pogu."). Whether Stripe's own Latvian label alone is unambiguous enough is a question for a
//    lawyer, as the German "Bezahlen" is.
//  - Art. 9: 14 days from the conclusion of the contract for digital content; Art. 16(m): the digital content exception
//    (express prior consent, acknowledgement of losing the right, the confirmation of Art. 8(7)); Art. 11a: the online
//    function ("Atteikties no līguma", "Apstiprināt atteikumu"); Art. 13: refund within 14 days.
//  - The counting of the period (the day of payment not counted, a last day on a Saturday, Sunday or public holiday
//    moved to the next working day) is Regulation 1182/71 Art. 3, as withdraw.py period_end counts it.
//  - Out of court: the seller is Lithuanian, so the out-of-court body stays the Lithuanian Valstybinė vartotojų teisių
//    apsaugos tarnyba (VVTAT); no ODR link (the platform closed on 20 July 2025). "disputes" names the Latvian Act
//    (Patērētāju tiesību aizsardzības likums) as the mandatory law a consumer living in Latvia keeps (Rome I Art. 6(2));
//    no other Latvian statute or authority is named.
//  - VAT: the English sentence wherever a price is final ("Mēs neesam reģistrēti kā PVN maksātāji, ...").
//  - The contract languages are named ("Līguma valodas: latviešu, angļu, vācu, lietuviešu, ungāru, horvātu, somu un
//    igauņu."): the other languages' terms must name Latvian too (the build checks it, scripts/check_texts.mjs CONTRACT).
//  - The latest delivery time is "N stundu laikā" (stunduGen below: the genitive before "laikā", "1 stundas", "2 stundu",
//    "48 stundu").
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { DELIVERY_MAX_HOURS, MAIL, PRICE_CENTS, SELLER, address, company, eur, phoneSuffix, representedSuffix } from '../facts';
import { aiBlocks } from '../../shared/aiMaterial';
import { lvForm } from '../../shared/lv';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../../shared/legal';

const companyLv = company('lv');
const addressLv = address('lv');
const phoneSuffixLv = phoneSuffix('lv');
const representedSuffixLv = representedSuffix('lv');
const eurLv = (cents: number) => eur(cents, 'lv');
const WITHDRAWAL_ONLINE_LV = WITHDRAWAL_ONLINE.lv;
const CHECKOUT_LEGAL_LV = CHECKOUT_LEGAL.lv;

/** "48 stundu", "1 stundas", "2 stundu": hours in the genitive, before "laikā". */
const stunduGen = (n: number) => `${n} ${lvForm(n, 'stundas', 'stundu', 'stundu')}`;

const TRANSPARENCY_LV = 'Krāsa nāk no jūsu pašu fotogrāfijas. Tur, kur telefons nespēja uztvert vissmalkākās šķiedras, tās atjauno mūsu mākslīgais intelekts.';
const PX = '4096\u00a0px';
const SQUARE = '4096\u00a0×\u00a04096\u00a0px';

const STANDARD_LIST_NOTE_LV =
  'Iepriekš redzamā tabula ir mūsu standarta cenrādis. Laiku pa laikam uz ierobežotu laiku dažiem nejauši izvēlētiem apmeklētājiem izmēģinām citus cenrāžus. Jūs vienmēr maksājat cenas, kas jums parādītas mākslas darba lapā pirms maksāšanas un maksājuma lapā, un pasūtījuma apstiprinājuma e-pastā ir norādīts cenrādis, kas tika piemērots jūsu pasūtījumam. Tas, kuru cenrādi redzat, nekad nav atkarīgs no valsts, kurā dzīvojat, bet tikai no tirgus (valūtas), ko izvēlaties.';
const PAY_LV = 'Jūs maksājat avansā ar mūsu maksājumu pakalpojumu sniedzēja Stripe starpniecību, izmantojot maksājuma lapā redzamos maksāšanas veidus.';

export const lv: LegalDoc = {
  title: 'Pārdošanas noteikumi',
  description:
    'SnapEyes digitālā varavīksnenes mākslas darba pasūtīšanas noteikumi: produkts, cenas, maksāšana, piegāde, jūsu licence, atteikuma tiesības un sūdzības.',
  lead: 'Šie noteikumi attiecas uz katru pasūtījumu, kas veikts vietnē snapeyes.com. Lūdzu, izlasiet tos pirms pasūtīšanas. Bezmaksas priekšskatījums tiek piedāvāts bez jebkādām saistībām.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'Ar ko jūs slēdzat līgumu',
      blocks: [
        `Līgumu jūs slēdzat ar ${companyLv}, mazo sabiedrību saskaņā ar Lietuvas tiesībām (mažoji bendrija)${representedSuffixLv}, reģistrācijas numurs ${SELLER.code}, ${addressLv}, e-pasts ${MAIL}${phoneSuffixLv} (turpmāk „mēs” vai „SnapEyes”). Visi dati ir mūsu [Rekvizītos](doc:imprint).`,
        'Mūsu piedāvājums ir paredzēts patērētājiem. Ja jums nav 18 gadu, lūdziet vecākam vai aizbildnim pasūtīt jūsu vietā.',
      ],
    },
    {
      id: 'product',
      title: 'Ko jūs pērkat',
      blocks: [
        `Personalizētu digitālu mākslas darbu, kas veidots no jūsu pašu acs (vai vairāku acu) fotogrāfijas, jūsu izvēlētajā stilā, izkārtojumā un ar jūsu izvēlēto uzrakstu. Jūs saņemat vienu attēla failu (JPEG) bez ūdenszīmes: ${SQUARE} vienai acij, ${PX} garākajā malā vairākām acīm. Mākslas darbs tiek piegādāts tikai kā digitāls fails, lejupielādējot. Mēs nepārdodam izdrukas, rāmjus vai citus fiziskus produktus.`,
        `${TRANSPARENCY_LV} Tāpēc mākslas darbs ir māksliniecisks atjaunojums, nevis medicīnisks vai mikroskopa attēls, un tas nav piemērots nekādam medicīniskam nolūkam vai personas identificēšanai.`,
        ...aiBlocks('lv'),
      ],
    },
    {
      id: 'preview',
      title: 'Jūsu priekšskatījums un jūsu fails',
      blocks: [
        'Pirms pasūtīšanas jūs redzat bezmaksas priekšskatījumu ar ūdenszīmi un to apstiprināt. Jūsu fails atbilst priekšskatījumam, ko apstiprinājāt: tā pati acs, stils, izkārtojums, acu secība un uzraksts, ar to pašu krāsu un toni, izveidots vienu reizi pilnā izšķirtspējā. Pilnā izmērā mūsu mākslīgais intelekts pievieno smalkās šķiedru detaļas, kuras priekšskatījums sava mazā izmēra dēļ nevar parādīt, tāpēc vissmalkākās detaļas var nedaudz atšķirties no priekšskatījuma. Piecu līdz astoņu acu priekšskatījums tiek veidots no mazākām jūsu fotogrāfiju kopijām, tāpēc tas ir rupjāks nekā jūsu fails.',
        'Ja jūsu fails skaidri atšķiras no priekšskatījuma, ko apstiprinājāt (piemēram, krāsā, spilgtumā vai zīlītē), tas ir trūkums: skatiet [Sūdzības un trūkumi](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'Kā tiek noslēgts līgums',
      blocks: [
        `Priekšskatījumi un cenas mūsu vietnē vēl nav saistošs piedāvājums. Pirms maksāšanas varat pārbaudīt savas acis, stilu, izkārtojumu un uzrakstu un izlabot jebkuru ievadi, atgriežoties atpakaļ vai nofotografējot vēlreiz. Pēc tam ar mūsu pogu „${CHECKOUT_LEGAL_LV.continueButton}” atverat mūsu maksājumu pakalpojumu sniedzēja Stripe maksājuma lapu; šī poga vēl neveic pasūtījumu. Šajā lapā ievadāt savu e-pasta adresi un maksājuma datus un varat tos izlabot. Saistošu pasūtījumu ar pienākumu maksāt jūs veicat, kad tur apstiprināt maksājumu ar maksāšanas pogu.`,
        'Līgums ir noslēgts, kad jūsu maksājums ir apstiprināts. Tad atveras jūsu pasūtījuma lapa, un tās saiti kopā ar pasūtījuma apstiprinājumu nosūtām jums e-pastā. Tiklīdz šis e-pasts ir nosūtīts, tur sākam veidot jūsu failu.',
        'Līguma valodas: latviešu, angļu, vācu, lietuviešu, ungāru, horvātu, somu un igauņu.',
        'Jūsu pasūtījumu glabājam kopā ar līguma datiem: pasūtītais mākslas darbs, cena, datums, jūsu e-pasta adrese un jūsu piekrišana sākt uzreiz. Jūsu pasūtījuma lapa rāda šos datus tik ilgi, kamēr glabājam jūsu pasūtījumu. Atsevišķu šo noteikumu kopiju katram pasūtījumam neglabājam. Tā vietā pasūtījuma apstiprinājuma e-pastā teksta veidā ir jūsu pasūtījuma dati, šie noteikumi un informācija par atteikuma tiesībām ar atteikuma veidlapas paraugu tajā redakcijā, kas bija spēkā pasūtīšanas brīdī: lūdzu, saglabājiet šo e-pastu. Šo lapu arī varat jebkurā laikā saglabāt vai izdrukāt.',
      ],
    },
    {
      id: 'prices',
      title: 'Cenas un maksāšana',
      blocks: [
        {
          dl: [
            ['Viena acs, Clean Iris', eurLv(PRICE_CENTS.studioBlack)],
            ['Viena acs, jebkurš cits stils', eurLv(PRICE_CENTS.artBackground)],
            ['Divas acis, jebkurš stils', eurLv(PRICE_CENTS.coupleDuo)],
            ['Katra nākamā acs', `+${eurLv(PRICE_CENTS.extraEye)}`],
          ],
        },
        'Visas cenas ir galīgās cenas eiro. Mēs neesam reģistrēti kā PVN maksātāji, tāpēc PVN netiek ne piemērots, ne norādīts. Piegādes izmaksu nav.',
        STANDARD_LIST_NOTE_LV,
        PAY_LV,
      ],
    },
    {
      id: 'delivery',
      title: 'Piegāde',
      blocks: [
        `Jūsu pasūtījuma lapa veido jūsu failu, tiklīdz ir nosūtīts pasūtījuma apstiprinājuma e-pasts, parasti minūtes laikā pēc samaksas; veidošana parasti aizņem dažas minūtes. Ja aizverat lapu, pirms fails ir gatavs, veidošana turpinās, kad to atkal atverat ar saiti no e-pasta. Ja mūsu automātiskā kvalitātes pārbaude atzīmē failu, pirms nodošanas to apskatām paši un nosūtām jums e-pastu, kad tas ir gatavs. **Vēlākais ${stunduGen(DELIVERY_MAX_HOURS)} laikā pēc jūsu maksājuma apstiprināšanas jūsu fails būs gatavs lejupielādei jūsu pasūtījuma lapā.** No savas pasūtījuma lapas failu varat lejupielādēt jebkurā laikā, kamēr to glabājam: 12 mēnešus no samaksas (skatiet mūsu [Privātuma politiku](doc:privacy)). Katra lapas izveidotā lejupielādes saite ir derīga 7 dienas; lapa izveido jaunu katru reizi, kad to atverat. Ja pazaudējat e-pastu, rakstiet mums.`,
        'Saite uz jūsu pasūtījuma lapu satur privātu atslēgu: ikviens, kam tā ir, var lejupielādēt jūsu mākslas darbu, tāpēc, lūdzu, nedodiet to nevienam. Lūdzu, lejupielādējiet savu failu un saglabājiet kopiju. Pēc 12 mēnešiem tas tiek dzēsts, un to nevar atjaunot.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Atteikuma tiesības',
      blocks: [
        `Kā patērētājam jums parasti ir 14 dienu atteikuma tiesības. Digitālam failam tās beidzas agrāk: pirms maksāšanas lūdzam jūs piekrist, ka jūsu failu sākam veidot uzreiz, pirms atteikuma termiņa beigām, un apliecināt, ka zināt, ka zaudējat atteikuma tiesības, tiklīdz esam sākuši. Tāpēc tās beidzas, tiklīdz esam sākuši veidot jūsu failu (līguma izpilde); sākam tikai pēc tam, kad ir nosūtīts pasūtījuma apstiprinājuma e-pasts, parasti minūtes laikā pēc samaksas, kamēr ir atvērta jūsu pasūtījuma lapa. Tas attiecas arī uz laiku, kamēr fails vēl tiek veidots vai gaida mūsu kvalitātes pārbaudi. Ja neesam sākuši, tās beidzas, kad beidzas 14 dienu atteikuma termiņš: jūsu samaksas diena netiek ieskaitīta, un, ja termiņa pēdējā diena ir sestdiena, svētdiena vai svētku diena, termiņš beidzas nākamās darba dienas beigās. Kamēr jūsu atteikuma tiesības ir spēkā, no līguma varat atteikties pa e-pastu, pa pastu vai tiešsaistē ar pogu „${WITHDRAWAL_ONLINE_LV.button}”; atteikuma saite pasūtījuma apstiprinājuma e-pastā atver šo funkciju jūsu pasūtījumam, nesākot veidot jūsu failu. Pilna informācija, tiešsaistes funkcija un atteikuma veidlapas paraugs ir lapā [Atteikuma tiesības](doc:withdrawal).`,
      ],
    },
    {
      id: 'photos',
      title: 'Jūsu fotogrāfijas',
      blocks: [
        'Augšupielādējiet tikai savas acs fotogrāfijas vai tāda cilvēka acs fotogrāfijas, kurš tam ir piekritis (bērna gadījumā: vecāks vai aizbildnis). Augšupielādējot fotogrāfiju, jūs apliecināt, ka drīkstat to izmantot šim nolūkam.',
        'Tiesības uz jūsu fotogrāfiju paliek jums. Mēs to izmantojam tikai jūsu priekšskatījuma un jūsu mākslas darba izveidei, kā aprakstīts mūsu [Privātuma politikā](doc:privacy).',
        'Mēs varam atteikt pasūtījumu un pilnībā atmaksāt jebkuru maksājumu, ja fotogrāfija acīmredzami pārkāpj šos noteikumus.',
      ],
    },
    {
      id: 'licence',
      title: 'Ko drīkstat darīt ar savu mākslas darbu',
      blocks: [
        'Jūs saņemat neekskluzīvu, pastāvīgu licenci izmantot savu mākslas darbu personīgiem, nekomerciāliem nolūkiem. Jūs varat, piemēram, izdrukāt to sev (mājās vai tipogrāfijā), ierāmēt, uzdāvināt, izmantot kā fona attēlu savās ierīcēs un dalīties ar to savos personīgajos sociālajos tīklos.',
        'Bez mūsu atļaujas (pietiek ar e-pastu) jūs nedrīkstat pārdot mākslas darbu vai no tā izgatavotus produktus, piešķirt citiem tiesības uz to vai izmantot to reklāmai vai citiem komerciāliem nolūkiem.',
        'Stili, foni, izkārtojumi un SnapEyes dizains paliek mūsu, tostarp visas autortiesības uz tiem. Tas pats attiecas uz priekšskatījumiem ar ūdenszīmi.',
      ],
    },
    {
      id: 'defects',
      title: 'Sūdzības un trūkumi',
      blocks: [
        `Jūsu likumīgās tiesības attiecībā uz digitālo saturu, kas neatbilst līgumam, ir spēkā pilnībā. Ja jūsu failam ir trūkumi, piemēram, to nevar lejupielādēt vai atvērt, tas ir bojāts, ir mazāks, nekā solīts, vai skaidri atšķiras no priekšskatījuma, ko apstiprinājāt, lūdzu, rakstiet uz ${MAIL} un norādiet pasūtījuma numuru. Mēs bez maksas izveidosim failu vēlreiz vai, ja tas trūkumu nenovērš, atmaksāsim naudu.`,
      ],
    },
    {
      id: 'liability',
      title: 'Atbildība',
      blocks: [
        'Mēs atbildam bez ierobežojumiem par nodomu un rupju neuzmanību, par kaitējumu dzīvībai, miesai vai veselībai un visos gadījumos, kad to paredz imperatīvas tiesību normas. Citādi par vieglu neuzmanību atbildam tikai par būtisku līguma pienākumu pārkāpumu un tikai par kaitējumu, kas ir tipisks un paredzams šāda veida līgumam. Bezmaksas priekšskatījums tiek piedāvāts tāds, kāds tas ir, bez jebkādām tiesībām prasīt tā pieejamību.',
      ],
    },
    {
      id: 'disputes',
      title: 'Strīdi un piemērojamās tiesības',
      blocks: [
        'Ja kaut kas nav kārtībā, lūdzu, vispirms rakstiet mums: lielāko daļu problēmu ātri atrisinām pa e-pastu.',
        'Ja nevaram vienoties, patērētāji var vērsties Lietuvas Valsts patērētāju tiesību aizsardzības dienestā (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)), kas patērētāju strīdus risina ārpus tiesas, vai savas valsts patērētāju tiesību aizsardzības iestādēs un tiesās.',
        'Piemērojamas ir Lietuvas tiesības. Ja esat patērētājs, kas dzīvo citā ES valstī, jūs saglabājat aizsardzību, ko sniedz šīs valsts imperatīvās patērētāju tiesību normas (Latvijā: Patērētāju tiesību aizsardzības likums).',
      ],
    },
    {
      id: 'changes',
      title: 'Šo noteikumu izmaiņas',
      blocks: ['Jūsu pasūtījumam piemērojami noteikumi, kas ir spēkā pasūtīšanas brīdī.'],
    },
  ],
};

// No forint edition: the Hungarian edition (the hu market) has no Latvian texts (src/shared/legal.ts EDITION_LANGS), so there
// is no Latvian twin of huHufPrices.
