// Privātuma politika (VDAR 13. pants): the Latvian twin of `en` in src/legal/docs/privacy.ts, same section ids and
// blocks in the same order. Written from the same facts as the English file (see its header: what the code really does
// on 2026-09-29) and to be kept in step with it. The GDPR is "Vispārīgā datu aizsardzības regula" (VDAR) in Latvian, and
// its articles are cited the Latvian way ("VDAR 6. panta 1. punkta f) apakšpunkts"); a hash is "jaucējvērtība", cookies
// are "sīkdatnes", local and session storage "lokālā krātuve" and "sesijas krātuve". "rights" keeps the lead authority of
// the English text (the controller is established in Lithuania: the State Data Protection Inspectorate, VDAI) and names
// the Latvian authority a reader in Latvia may also turn to (Art. 77 GDPR), Datu valsts inspekcija, by its name only:
// no link is added, so the links stay exactly the English ones.
// Not reviewed by a lawyer. Keep every sentence true when the code or a service changes.
import type { LegalDoc } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';

const companyLv = company('lv');
const addressLv = address('lv');
const WITHDRAWAL_ONLINE_LV = WITHDRAWAL_ONLINE.lv;

// What the online withdrawal function keeps (the "withdrawal" section), as WITHDRAW_PRIVACY.en
const WITHDRAW_PRIVACY_LV = `Ja no pasūtījuma atsakāties ar mūsu tiešsaistes funkciju (poga „${WITHDRAWAL_ONLINE_LV.button}”, skatiet [Atteikuma tiesības](doc:withdrawal#online)), jūsu paziņojumu par atteikumu glabājam kopā ar jūsu pasūtījumu: jūsu vārdu un uzvārdu, e-pasta adresi, pasūtījuma numuru, paziņojuma tekstu un datumu un laiku, kad tas mūs sasniedza. Mēs to izmantojam, lai apturētu darbu pie jūsu faila, ja vēl neesam sākuši, lai nosūtītu jums e-pastā apstiprinājumu par saņemšanu ar tā saturu, datumu un laiku un lai atmaksātu jums naudu. Katru paziņojumu saņemam arī e-pastā: pa vienam vai, ja paziņojums neatbilst nevienam mūsu pasūtījumam vai attiecas uz pasūtījumu, kas nekad nav apmaksāts, vienā kopsavilkumā dienā. Ja jūsu atteikums stājas spēkā, mūsu ikdienas automātiskā tīrīšana dzēš jūsu pasūtījuma attēlus, kad kopš atteikuma ir pagājušas 14 dienas (ja jūsu maksājums vēl tika apstrādāts, tikai tad, kad tas ir pabeigts); pasūtījuma ieraksts ar jūsu paziņojumu paliek (skatiet [Cik ilgi glabājam jūsu datus](#retention)). Ja jūsu norādītie dati neatbilst nevienam mūsu pasūtījumam (bez saites no jūsu pasūtījuma lapas vai atteikuma saites pasūtījuma apstiprinājuma e-pastā e-pasta adresei jābūt tai, ar kuru maksājāt), paziņojumu glabājam atsevišķi, pārbaudām paši, tomēr nosūtām jums e-pastā apstiprinājumu par saņemšanu (ievērojot ierobežojumus pret ļaunprātīgu izmantošanu, kas norādīti sadaļā [Atteikšanās tiešsaistē](doc:withdrawal#online)) un automātiski dzēšam aptuveni 13 mēnešus pēc tā mēneša beigām, kurā tas mūs sasniedza.`;

// The admin log and the admin sign-in guard, as ADMIN_LOG.en
const ADMIN_LOG_LV = {
  log: 'Kad apstrādājam pasūtījumu savā administrēšanas panelī, piemēram, pēc kvalitātes pārbaudes nododam failu, atkārtoti nosūtām e-pastu, veicam atmaksu vai dzēšam failus, panelis ieraksta ierakstu mūsu administrēšanas žurnālā: kas izdarīts, kad, kuram pasūtījuma numuram un ar kādu iznākumu. Administrēšanas žurnālā nav attēlu, e-pasta adrešu un saišu. Juridiskais pamats: mūsu leģitīmās intereses apstrādāt pasūtījumus droši un izsekojami (VDAR 6. panta 1. punkta f) apakšpunkts). Tas tiek automātiski dzēsts pēc 24 mēnešiem; ieraksti par pasūtījumu tiek glabāti arī kopā ar šī pasūtījuma ierakstu tik ilgi, kamēr šis ieraksts tiek glabāts (skatiet [Cik ilgi glabājam jūsu datus](#retention)).',
  signin: 'Mūsu administrēšanas panelis ir paredzēts tikai mums. Lai neviens nevarētu uzminēt tā atslēgu, neveiksmīga pieteikšanās saglabā tās IP adreses jaucējvērtību, no kuras tā nākusi, izveidotu ar slepenu atslēgu, nekad pašu adresi, un tā tiek automātiski dzēsta pēc 2 dienām. Juridiskais pamats: mūsu leģitīmās intereses uzturēt savas sistēmas drošas (VDAR 6. panta 1. punkta f) apakšpunkts).',
};

// The admin panel's usage statistics and its admin log, as OPS.en
const OPS_LV = {
  events:
    'Lai redzētu, vai pakalpojums darbojas, cik tas ir ātrs un cik tas maksā, mūsu serveris reģistrē nelielus tehniskus notikumus mūsu privātajā krātuvē pie Supabase ES. Piemēram: ka fotogrāfija ir pārbaudīta (ar rezultātu, piemēram, „acs nav atrasta”, ierīces veidu, piemēram, iPhone, Android vai dators, to, vai fotogrāfija nāk no kameras vai galerijas, un lapas valodu), ka noņemti atspīdumi, ka izveidots priekšskatījums vai pasūtīts fails un cik ilgi tas aizņēma, vai ka pieprasījums neizdevās (ar kļūdas kodu). Kamēr testējam cenas, notikumos ir norādīts arī tas, kurš cenrādis (īss kods) tika parādīts, skatīts priekšskatījumā, atvērts maksāšanai vai apmaksāts, un apmaksāta pasūtījuma summa. Mūsu administrēšanas panelis tos mums rāda galvenokārt kā dienas kopskaitus.',
  counter:
    'Lai redzētu, cik cilvēku sasniedz katru vietnes soli, mūsu serveris skaita arī soļus, ko lapa sasniedz: ka atvērta pirmā lapa, ka atvērta fotografēšanas lapa, ka fotogrāfija izvēlēta vai uzņemta, ka parādīts priekšskatījums (ar sekundēm, kas pagāja kopš fotogrāfijas), ka pirkuma kartīte parādīja, ka pasūtījumus vēl nepieņemam, ka nospiesta pirkuma poga un ka atvērta pasūtījuma lapa. Katrs skaitījums ir neliels skaitļu un īsu kodu ieraksts: solis, lapas valoda, tirgus (valūta), ierīces veids (iPhone, Android vai dators), pārlūkprogrammas veids (piemēram, Chrome, Safari vai Facebook vai Instagram lietotnes iebūvētā pārlūkprogramma) un valsts (divi burti, ko Vercel nosaka pēc jūsu IP adreses). Lai noteiktu ierīci un pārlūkprogrammu, mūsu serveris uz mirkli nolasa jūsu pārlūkprogrammas identifikatoru (user agent), un, lai apturētu klientu, kas sūta pārāk daudz skaitījumu, tas mazāk nekā minūti tur atmiņā jūsu IP adreses jaucējvērtību, izveidotu ar atslēgu, kas zūd, serverim restartējoties; ne vienu, ne otru tas neglabā. Šie skaitījumi neizmanto sīkdatni un apmeklētāja numuru, un tajos nav IP adreses, pārlūkprogrammas identifikatora, lapas adreses un saites, no kuras atnācāt, tāpēc tos nevar saistīt ar jums. Savā administrēšanas panelī tos redzam saskaitītus pa dienām.',
  campaign:
    'Ja pie mums nonākat caur reklāmu vai mūsu saiti ar kampaņas kodu, vai no citas vietnes, jūsu pārlūkprogramma glabā šo kodu jūsu apmeklējuma laikā (skatiet [Sīkdatnes un lokālā krātuve](#storage)), un iepriekš minētie skaitījumi, jūsu veiktās fotogrāfiju pārbaudes un priekšskatījumi, maksājuma lapa un jūsu pasūtījums to nes līdzi, lai mēs varētu redzēt, kura reklāma noveda līdz kuram solim, cik tā maksāja par soli un kuru pasūtījumu tā atnesa. Kods ir vienāds visiem, kas atnāca, noklikšķinot uz šīs reklāmas, un nav atvasināts no jūsu datiem.',
  feedback:
    'Rezultāta ekrānā un kartītē, kas lūdz citu fotogrāfiju, neliels atsauksmju lodziņš piedāvā sešas atbildes (piemēram, „Man ļoti patīk” vai „Krāsas nešķiet pareizas”) un, ja vēlaties, tekstu līdz 300 rakstzīmēm. Nekas netiek nosūtīts, kamēr nenospiežat „Nosūtīt”. Lodziņā nav lauka jūsu vārdam vai e-pasta adresei: lūdzu, nerakstiet tos, kā arī tālruņa numurus un saites. Kad nospiežat „Nosūtīt”, mūsu serveris reģistrē jūsu atbildi kā vēl vienu nelielu kodu notikumu (atbilde, stils, kas bija ekrānā, vai iemesls, kāpēc fotogrāfija tika noraidīta, acu skaits, vai tai bija pievienots teksts, un tie paši dati kā iepriekš aprakstītajos soļu skaitījumos: kampaņas kods, lapas valoda, tirgus, ierīces un pārlūkprogrammas veids un valsts). Teksts tiek glabāts atsevišķi, ar šiem kodiem un neko citu, un tikai tad, ja tas iztur pārbaudi: teksts, kurā ir zīme „@”, tālruņa numurs, saite vai kas tāds, kas izskatās pēc surogātpasta, netiek saglabāts (jūsu atbilde tomēr tiek ieskaitīta). Tekstus lasām savā administrēšanas panelī; atbildēt nevaram, jo nezinām, kas tos rakstījis. Katrs teksts tiek automātiski dzēsts pēc 90 dienām, un mēs varam to izdzēst agrāk. Tā kā nekas lodziņā jūs neidentificē, jūsu tekstu vēlāk varam atrast tikai tad, ja pasakāt mums, kas tajā bija rakstīts. Lodziņš jūsu pārlūkprogrammā neko neieraksta.',
  content:
    '**Šajos notikumos nav attēla, jūsu ievadīta teksta (atsauksmju lodziņā rakstīts teksts tiek glabāts atsevišķi no tiem, kā aprakstīts iepriekš), vārda, e-pasta adreses, IP adreses, pārlūkprogrammas identifikatora (user agent) un saites.** Bezmaksas priekšskatījuma notikumus nevar saistīt ar jums. Tikai notikumos par apmaksāta pasūtījuma faila veidošanu ir arī tā pasūtījuma numurs, lai mēs varētu atrast lēnu vai neizdevušos veidošanu; ar mūsu pasūtījumu ierakstu starpniecību šis numurs ir saistīts ar jūsu pasūtījumu.',
  basis:
    'Juridiskais pamats: mūsu leģitīmās intereses nodrošināt uzticamu pakalpojuma darbību, atrast kļūdas, kontrolēt tā izmaksas un uzzināt, kas apmeklētājus atbaida (VDAR 6. panta 1. punkta f) apakšpunkts). Notikumi un no tiem veidotie dienas kopskaiti tiek automātiski dzēsti pēc 12 mēnešiem; atsauksmju lodziņa teksti pēc 90 dienām. Jūs jebkurā laikā varat iebilst (skatiet [Jūsu tiesības](#rights)).',
  admin: ADMIN_LOG_LV.log,
  signin: ADMIN_LOG_LV.signin,
  previewcap: 'Lai bezmaksas priekšskatījums paliktu bez maksas visiem, no viena interneta savienojuma dienā var izveidot ierobežotu skaitu priekšskatījumu. Par katru priekšskatījumu mūsu serveris saglabā tās IP adreses, no kuras tas nācis, un dienas jaucējvērtību, izveidotu ar slepenu atslēgu, nekad pašu adresi: adresi no tās nevar nolasīt atpakaļ, un nākamajā dienā tā pati adrese dod citu jaucējvērtību. Šie ieraksti tiek automātiski dzēsti pēc 2 dienām. Juridiskais pamats: mūsu leģitīmās intereses saglabāt bezmaksas priekšskatījumu pieejamu un kontrolēt tā izmaksas (VDAR 6. panta 1. punkta f) apakšpunkts).',
};

const repLv = SELLER.representative ? ` To pārstāv ${SELLER.representative}.` : '';
const senderLv = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: e-pastu par jūsu pasūtījumu nosūtīšana (saite uz jūsu pasūtījuma lapu, pasūtījuma apstiprinājums un, ja atsakāties no līguma, apstiprinājums par saņemšanu). Tā serveri var atrasties ārpus ES.`];
const hostingerLv = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: mūsu e-pasts, pastkaste info@snapeyes.com, tostarp e-pasti par jūsu pasūtījumu.'
  : 'Hostinger: mūsu pastkaste info@snapeyes.com.';

export const lv: LegalDoc = {
  title: 'Privātuma politika',
  description:
    'Kā SnapEyes rīkojas ar jūsu acs fotogrāfiju, jūsu priekšskatījumu un, ja pasūtāt, jūsu pasūtījuma datiem: ko apstrādājam, kāpēc, ar kādiem pakalpojumiem, cik ilgi, un jūsu tiesības.',
  lead:
    'Šī politika skaidro, kas notiek ar jūsu datiem, kad izmantojat snapeyes.com: bezmaksas priekšskatījumu un, ja pasūtāt, jūsu digitālo mākslas darbu. Īsumā: jūsu fotogrāfija tiek izmantota tikai jūsu mākslas darba izveidei, nekad lai kādu identificētu un nekad mākslīgā intelekta apmācībai. Bezmaksas priekšskatījumus neglabājam. Apmaksātu pasūtījumu faili tiek glabāti 12 mēnešus, lai varat tos lejupielādēt vēlreiz, un pēc tam dzēsti.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Kas atbild par jūsu datiem',
      blocks: [
        `Jūsu datu pārzinis ir ${companyLv} (reģistrācijas numurs ${SELLER.code}), ${addressLv}. SnapEyes ir tā zīmols.${repLv}`,
        `Par visiem privātuma jautājumiem un lai izmantotu jebkuras savas tiesības, rakstiet uz ${MAIL}. Datu aizsardzības speciālistu neesam iecēluši.`,
      ],
    },
    {
      id: 'website',
      title: 'Kad apmeklējat vietni',
      blocks: [
        'Kad atverat kādu snapeyes.com lapu, jūsu pārlūkprogramma nosūta tehniskus datus mūsu mitināšanas pakalpojumu sniedzējam Vercel, piemēram, jūsu IP adresi, datumu un laiku, pieprasīto lapu un pārlūkprogrammas veidu (user agent). Vercel šie dati ir vajadzīgi, lai piegādātu lapu un aizsargātu pakalpojumu pret uzbrukumiem. Tie īsu laiku tiek glabāti servera žurnālos un pēc tam dzēsti.',
        'Lai varētu ieteikt cenas jūsu valūtā, mūsu serveris var nolasīt arī valsti, ko Vercel nosaka pēc jūsu IP adreses (piemēram, „AU”). Tā tiek izmantota šim ieteikumam un nekad nemaina cenas, ko redzat. Tā netiek glabāta kopā ar neko, kas varētu jūs identificēt: tās vienīgā pēda ir divi valsts burti mūsu anonīmajos skaitījumos (skatiet [Pakalpojuma statistika un mūsu administrēšanas žurnāls](#operations)).',
        'Juridiskais pamats: mūsu leģitīmās intereses nodrošināt drošu, strādājošu vietni (VDAR 6. panta 1. punkta f) apakšpunkts).',
        'Mūsu fonti tiek piegādāti no mūsu pašu servera, tāpēc nekādi dati nenonāk pie Google Fonts vai cita fontu pakalpojuma. Mūsu pašu anonīmā pakalpojuma statistika ir aprakstīta sadaļā [Pakalpojuma statistika un mūsu administrēšanas žurnāls](#operations). No citu uzņēmumu rīkiem šajā vietnē izmantojam vienu, Meta pikseli mūsu reklāmām: skatiet [Meta pikselis un mūsu reklāmas](#meta).',
      ],
    },
    {
      id: 'preview',
      title: 'Jūsu bezmaksas priekšskatījums',
      blocks: [
        'Lai izveidotu jūsu priekšskatījumu, jūs no savas pārlūkprogrammas nosūtāt vienu vai vairākas acs fotogrāfijas mūsu servera funkcijām. Tur fotogrāfija tiek apstrādāta atmiņā: atrodam varavīksneni, izgriežam to, pārbaudām, vai tā ir pietiekami asa un gaiša, noņemam atspīdumus, atjaunojam smalkās šķiedras ar Google Gemini API un ietērpjam varavīksneni stilos, ko redzat. Rezultāts atgriežas jūsu pārlūkprogrammā. Katra pārsūtīšana ir šifrēta (HTTPS).',
        '**Jūsu fotogrāfiju, varavīksnenes izgriezumu un priekšskatījumu savos serveros neglabājam.** Tie tiek atmesti, kad pieprasījums beidzas. Priekšskatījums paliek jūsu pārlūkprogrammā, līdz aizverat lapu (kamēr esat maksājuma lapā, jūsu pārlūkprogrammas cilnes sesijas krātuvē: skatiet [Sīkdatnes un lokālā krātuve](#storage)), ja vien to nesaglabājat paši. Varavīksnenes izgriezumu un priekšskatījumu, ko apstiprinājāt, saglabājam tikai tad, kad sākat pasūtījumu: skatiet [Kad pasūtāt](#orders).',
        'Google apstrādā attēlu, lai veiktu atjaunošanu. Mēs izmantojam Google maksas API pakalpojumu, saskaņā ar kura noteikumiem Google neizmanto attēlus savu produktu uzlabošanai vai savu modeļu apmācībai. Google var ierobežotu laiku glabāt pieprasījumus tikai tādēļ, lai atklātu ļaunprātīgu izmantošanu, un likumā prasītai informācijas izpaušanai.',
        'Juridiskais pamats: jūs lūdzat mūs izveidot jūsu priekšskatījumu, un tam ir vajadzīga fotogrāfija (VDAR 6. panta 1. punkta b) apakšpunkts, pasākumi pēc jūsu pieprasījuma).',
        'Mūsu programmatūra automātiski izlemj, vai fotogrāfiju var izmantot (piemēram, ja tā ir pārāk izplūdusi vai pārāk tumša). Šim lēmumam nav juridisku vai līdzīgi būtisku seku attiecībā uz jums: varat vienkārši uzņemt citu fotogrāfiju.',
      ],
    },
    {
      id: 'iris',
      title: 'Jūsu varavīksnene nekad netiek izmantota identificēšanai',
      blocks: [
        'Varavīksneni principā var izmantot, lai atpazītu cilvēku. Mēs to nedarām. Mēs nekad neveidojam, nesalīdzinām un neglabājam varavīksnenes veidni vai jebkādu citu biometrisko identifikatoru, nekad neizmantojam jūsu attēlus, lai kādu identificētu vai pārbaudītu, nekad tos nepārdodam un nekad neizmantojam mākslīgā intelekta apmācībai, ne mūsu pašu, ne kāda cita.',
        'Lūdzu, izmantojiet tikai savu aci vai tāda cilvēka aci, kurš tam ir piekritis. Par bērnu jāpiekrīt vecākam vai aizbildnim.',
        'Ja pievienojat citu cilvēku acis (piemēram, pārim), viņu attēlus apstrādājam tikai tāda mākslas darba izveidei, kuram viņi ir piekrituši. Juridiskais pamats: jūsu un mūsu leģitīmās intereses izveidot šo mākslas darbu (VDAR 6. panta 1. punkta f) apakšpunkts). Lūdzu, parādiet viņiem šo politiku.',
      ],
    },
    {
      id: 'measurements',
      title: 'Tehniskie mērījumi (bez attēliem)',
      blocks: [
        'Ar katru fotogrāfiju mūsu serveris ieraksta vienu rindu savos žurnālos, lai mēs varētu uzlabot fotografēšanas pamācību un pakalpojuma kvalitāti. Tajā ir fotogrāfijas mērījumi (piemēram, varavīksnenes izmērs pikseļos, asums, spilgtums, gaismas krāsas nokrāsa un tas, vai fotogrāfiju varēja izmantot), tehniski dati par jūsu ierīci (pārlūkprogrammas veids un versija, ekrāna izmērs, vai fotogrāfija nāk no kameras vai galerijas) un, ja atbildat uz mūsu neobligātajiem jautājumiem par kadru, jūsu atbildes. Tajā nav attēla, vārda un kontaktinformācijas.',
        'Šīs žurnāla rindas mūsu mitināšanas pakalpojumu sniedzējs glabā īsu laiku, un pēc tam tās tiek dzēstas. Juridiskais pamats: mūsu leģitīmās intereses uzlabot pakalpojumu (VDAR 6. panta 1. punkta f) apakšpunkts). Jūs jebkurā laikā varat iebilst (skatiet [Jūsu tiesības](#rights)).',
      ],
    },
    {
      id: 'operations',
      title: 'Pakalpojuma statistika un mūsu administrēšanas žurnāls',
      blocks: [OPS_LV.events, OPS_LV.counter, OPS_LV.campaign, OPS_LV.feedback, OPS_LV.content, OPS_LV.basis, OPS_LV.admin, OPS_LV.signin, OPS_LV.previewcap],
    },
    {
      id: 'meta',
      title: 'Meta pikselis un mūsu reklāmas',
      blocks: [
        'Mēs reklamējamies Facebook un Instagram. Lai uzzinātu, kuras mūsu reklāmas atved apmeklētājus un pasūtījumus, un lai Meta varētu tās rādīt cilvēkiem, kurus tās, visticamāk, interesēs, mūsu lapas izmanto Meta pikseli, uzņēmuma Meta Platforms Ireland Limited (Merrion Road, Dublin 4, D04 X2K5, Īrija; „Meta”) rīku. Tas darbojas mūsu lapās katram apmeklētājam; mēs par to iepriekš jums nejautājam.',
        'Pikselis paziņo Meta, kad tiek atvērta lapa, kad tiek atvērta fotogrāfijas lapa, kad jums tiek parādīts bezmaksas priekšskatījums, kad pārejat uz maksājuma lapu un kad tiek veikts maksājums, norādot maksājuma summu un valūtu un to, vai tas bija par mākslas darbu, dāvanu karti vai izdruku. Ar katru šādu paziņojumu jūsu pārlūkprogramma, tāpat kā ar jebkuru pieprasījumu, nosūta Meta jūsu IP adresi un pārlūkprogrammas identifikatoru (user agent), lapas un tās lapas adresi, no kuras atnācāt, un tālāk aprakstītās Meta sīkdatnes. No mūsu pasūtījuma lapas un dāvanu karšu lapas tiek nosūtīts tikai lapas ceļš („/order”, „/gift”), nekad tās pilnā adrese, kurā ir jūsu pasūtījuma atslēga vai jūsu maksājuma numurs. Ja izmantojat Facebook vai Instagram, Meta var šos paziņojumus saistīt ar jūsu kontu.',
        '**Mēs nekad nesūtām Meta jūsu fotogrāfiju, varavīksneni, acu krāsu, izvēlēto stilu, jūsu pievienotos vārdus vai datumu, jūsu mākslas darbu vai jebkuru citu attēlu.** Pikseļa automātiskās funkcijas, kas nolasītu lapas pogas un veidlapu laukus, ir izslēgtas.',
        'Meta skripts, ko jūsu pārlūkprogramma ielādē no connect.facebook.net tikai pēc tam, kad mūsu lapa jau ir ielādēta, iestata snapeyes.com divas sīkdatnes: „_fbp”, nejaušu numuru, pēc kura Meta atpazīst jūsu pārlūkprogrammu turpmākos apmeklējumos un kas tiek glabāts 90 dienas no jūsu pēdējā apmeklējuma, un tikai tad, ja atnācāt caur saiti ar Meta klikšķa numuru („fbclid”, piemēram, no reklāmas), „_fbc”, kurā ir šis numurs, arī 90 dienas. Ja atnācāt caur šādu saiti un jūsu pārlūkprogrammā nav sīkdatnes „_fbc”, mūsu lapa klikšķa numuru glabā jūsu pārlūkprogrammas cilnes sesijas krātuvē ar atslēgu „snapeyes.fbc”, līdz aizverat cilni. Paziņojumi tiek sūtīti uz www.facebook.com. Mūsu pasūtījuma lapa un dāvanu karšu lapa Meta skriptu neielādē: savus paziņojumus tās sūta kā atsevišķus pieprasījumus uz www.facebook.com.',
        'Kad maksājat par mākslas darbu, dāvanu karti vai izdruku, mūsu serveris par maksājumu paziņo arī tieši Meta (izmantojot Meta Conversions API), lai tas tiktu ieskaitīts arī tad, ja jūsu pārlūkprogrammas paziņojums nenonāk galā. Šajā paziņojumā ir: ka maksājums ir veikts, kad, tā summa un valūta, vai tas bija par mākslas darbu, dāvanu karti vai izdruku, lapas ceļš („/order” vai „/gift”), tās e-pasta adreses jaucējvērtība, ar kuru maksājāt (SHA-256: adresi no tās nevar nolasīt atpakaļ, bet Meta var to salīdzināt ar savu lietotāju adrešu jaucējvērtībām), jūsu valsts (no jūsu maksājuma datiem vai izvēlētajām cenām) un sīkdatņu „_fbp” un „_fbc” vērtības, IP adrese un pārlūkprogrammas identifikators, kas jūsu pārlūkprogrammai bija, atverot maksājuma lapu. Abiem viena maksājuma paziņojumiem ir viens un tas pats numurs, lai Meta to ieskaitītu vienreiz. Lai mūsu serverim tās būtu maksājuma brīdī, šīs četras vērtības kopā ar maksājuma lapu nonāk pie Stripe maksājuma metadatos un paliek kopā ar Stripe maksājuma ierakstu (skatiet [Kad pasūtāt](#orders)); citur mēs tās neglabājam.',
        'Šos paziņojumus izmantojam, lai novērtētu, kuras mūsu reklāmas darbojas, un rādītu tās cilvēkiem, kurus tās, visticamāk, interesēs. Juridiskais pamats: mūsu leģitīmās intereses novērtēt un virzīt savu reklāmu (VDAR 6. panta 1. punkta f) apakšpunkts). Par šo datu vākšanu mūsu vietnē un to nodošanu Meta mēs un Meta esam kopīgi pārziņi (VDAR 26. pants) saskaņā ar Meta biznesa rīku noteikumiem, un savas tiesības varat izmantot attiecībā pret jebkuru no mums. To, ko Meta pēc tam dara ar datiem, Meta nosaka kā neatkarīgs pārzinis saskaņā ar savu privātuma politiku; Meta var tos apstrādāt ASV, pamatojoties uz ES un ASV datu privātuma regulējumu.',
        'Jūs jebkurā laikā varat iebilst: rakstiet mums (skatiet [Jūsu tiesības](#rights)). Meta sīkdatnes un sesijas krātuvi varat arī dzēst vai bloķēt savas pārlūkprogrammas iestatījumos vai izmantot pārlūkprogrammu vai paplašinājumu, kas bloķē šādus rīkus; mūsu vietne bez tiem darbojas tāpat. Savā Facebook vai Instagram kontā (Kontu centrs, reklāmu preferences) varat izvēlēties, vai Meta drīkst izmantot informāciju no citām vietnēm, lai rādītu jums reklāmas.',
      ],
    },
    {
      id: 'orders',
      title: 'Kad pasūtāt',
      blocks: [
        'Kad sākat pasūtījumu, mūsu privātajā krātuvē tiek augšupielādēti divi katras acs attēli, lai jūsu fails tiktu veidots tieši no tā, ko redzējāt: kvadrāts ap jūsu varavīksneni, izgriezts no jūsu fotogrāfijas (ar noņemtiem atspīdumiem), un priekšskatījums, ko apstiprinājāt. Kopā ar tiem glabājam īsu no šī priekšskatījuma veikto mērījumu ierakstu (krāsas ap jūsu varavīksneni, krāsas klase, zīlītes forma, divas kvalitātes vērtības un kods, kas identificē priekšskatījumu). Tajā nav attēla, un tas tiek dzēsts kopā ar attēliem. **Jūsu pilnā telefona fotogrāfija netiek glabāta, pat ne pasūtījumam.** Pasūtījumu, kas nav apmaksāts 24 stundu laikā, vairs nevar apmaksāt. Automātiska tīrīšana, kas notiek reizi dienā, pēc tam dzēš tā attēlus un ierakstus, parasti divu dienu laikā pēc pasūtījuma un vēlākais 30 dienu laikā.',
        'Lai augšupielādes paliktu noteiktās robežās, mūsu serveris par katru augšupielādi ieraksta arī nelielu atzīmi (tās izmērs, diena un pasūtījuma numurs, bez attēla). Šīs atzīmes tiek automātiski dzēstas pēc dažām dienām.',
        'Lai pārdotu un piegādātu jūsu mākslas darbu, mēs apstrādājam: pasūtījumu (pasūtījuma numurs, datums, acis, stils, izkārtojums, acu secība, jūsu pievienotie vārdi, datums vai uzraksts, valoda, cena), jūsu e-pasta adresi (to ievadāt maksājuma lapā), maksājuma statusu, ko saņemam no Stripe, jūsu piekrišanu sākt uzreiz (skatiet [Atteikuma tiesības](doc:withdrawal)) un jūsu pasūtījuma failus: divus iepriekš minētos katras acs attēlus, katras acs 4096\u00a0px attēlojumu un gatavo mākslas darbu, ar tehniskiem kvalitātes ierakstiem.',
        'Šos failus glabājam privātā krātuvē pie Supabase, kas atrodas ES. Jūs tiem piekļūstat ar savas pasūtījuma lapas starpniecību, kuras saiti nosūtām jums e-pastā; tā satur privātu atslēgu, tāpēc ikviens, kam ir saite, var lejupielādēt jūsu mākslas darbu. Katra lapas izveidotā lejupielādes saite beidz darboties pēc 7 dienām.',
        'Mēs varam apskatīt jūsu pasūtījuma failus, lai pārbaudītu to kvalitāti, piemēram, ja mūsu automātiskā pārbaude ziņo par atšķirību no priekšskatījuma, ko apstiprinājāt.',
        'Juridiskais pamats: līgums ar jums (VDAR 6. panta 1. punkta b) apakšpunkts); grāmatvedības ierakstiem mūsu juridiskie pienākumi (VDAR 6. panta 1. punkta c) apakšpunkts).',
        'Kad pārejat uz maksājuma lapu, kopā ar jūsu maksājumu nododam Stripe pasūtījuma datus: pasūtījuma numuru, cenu (un, ja tika piemērots cenu tests, tā nosaukumu, jūsu cenrāža kodu un šī cenrāža cenas), acu skaitu, stilu (un tā variantu), izkārtojumu, acu secību, valodu, jūsu pievienotos vārdus, datumu vai uzrakstu, īsu kodu, kas identificē mākslas darba plānu un mūsu programmatūras versiju, kas to veido, jūsu piekrišanas versiju un laiku un, ja atnācāt caur reklāmu, tās kampaņas kodu. Stripe tos glabā kopā ar maksājuma ierakstu, un mēs tos no turienes nolasām atpakaļ, lai izveidotu tieši to mākslas darbu, par kuru samaksājāt. Kamēr par maksājumiem paziņojam Meta, maksājums nes arī Meta sīkdatņu „_fbp” un „_fbc” vērtības, ja tās ir jūsu pārlūkprogrammā, un IP adresi un pārlūkprogrammas identifikatoru, kas jūsu pārlūkprogrammai bija tajā brīdī (skatiet [Meta pikselis un mūsu reklāmas](#meta)).',
        'Maksājums: jūsu maksājumu apstrādā Stripe. Mēs nekad neredzam jūsu pilno kartes numuru. Stripe maksājumu datus apstrādā arī saskaņā ar savu privātuma politiku, krāpšanas novēršanai un savu juridisko pienākumu izpildei.',
        'Jūsu e-pasta adrese mums ir vajadzīga, lai nosūtītu jums saiti uz jūsu pasūtījuma lapu un pasūtījuma apstiprinājumu. Bez tās jūs varētu zaudēt piekļuvi savam failam.',
      ],
    },
    {
      id: 'email',
      title: 'Kad rakstāt mums',
      blocks: [
        'Ja rakstāt mums e-pastu, jūsu adresi un ziņu izmantojam, lai jums atbildētu un, ja tā attiecas uz pasūtījumu, lai apstrādātu šo pasūtījumu. Juridiskais pamats: pasūtījumiem VDAR 6. panta 1. punkta b) apakšpunkts, citādi mūsu leģitīmās intereses jums atbildēt (VDAR 6. panta 1. punkta f) apakšpunkts). Ja atsūtāt mums fotogrāfijas, piemēram, savas acs fotogrāfijas, lai mēs ieteiktu, kā uzņemt labāku kadru, izmantojam tās tikai jūsu pieprasījumam. Jūsu e-pastus kopā ar fotogrāfijām glabājam tik ilgi, cik tie mums vajadzīgi jūsu pieprasījumam un turpmākai saziņai.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Kad no pasūtījuma atsakāties tiešsaistē',
      blocks: [
        WITHDRAW_PRIVACY_LV,
        'Juridiskais pamats: mūsu juridiskais pienākums pieņemt jūsu atteikumu un to jums apstiprināt (VDAR 6. panta 1. punkta c) apakšpunkts) un līgums ar jums (VDAR 6. panta 1. punkta b) apakšpunkts). Paziņojumu kā pierādījumu glabājam kopā ar jūsu pasūtījuma ierakstu tik ilgi, kamēr šis ieraksts tiek glabāts (skatiet [Cik ilgi glabājam jūsu datus](#retention)).',
      ],
    },
    {
      id: 'services',
      title: 'Pakalpojumi, ko izmantojam',
      blocks: [
        'SnapEyes darbībai izmantojam šos pakalpojumus:',
        {
          ul: [
            'Vercel: vietnes un to servera funkciju mitināšana, kas veido jūsu priekšskatījumu un jūsu failu. Vercel datu centri var atrasties ārpus ES, piemēram, ASV.',
            'Google (Gemini API): varavīksnenes atjaunošana ar mākslīgo intelektu un jūsu fotogrāfijas pārbaudes. Google serveri var atrasties ārpus ES.',
            'Supabase: privāta pasūtījumu failu krātuve ES reģionā.',
            'Stripe: maksājumu apstrāde, ar pasūtījuma datiem, kas minēti sadaļā [Kad pasūtāt](#orders).',
            hostingerLv,
            ...senderLv,
            'Meta (Meta Platforms Ireland Limited): Meta pikselis un paziņojumi par maksājumiem, skatiet [Meta pikselis un mūsu reklāmas](#meta). Meta var apstrādāt datus ASV.',
          ],
        },
        `Šie pakalpojumu sniedzēji apstrādā jūsu datus mūsu vārdā un saskaņā ar mūsu norādījumiem (Stripe daļēji kā neatkarīgs pārzinis, skatiet [Kad pasūtāt](#orders); Meta, kā aprakstīts sadaļā [Meta pikselis un mūsu reklāmas](#meta)). Ja dati tiek nosūtīti ārpus ES vai EEZ, tas notiek, ievērojot pakalpojumu sniedzēju piedāvātās garantijas, piemēram, Eiropas Komisijas līguma standartklauzulas vai ES un ASV datu privātuma regulējumu. Šo garantiju kopiju varat lūgt, rakstot uz ${MAIL}.`,
        'Mēs nepārdodam jūsu datus un nenododam tos nevienam citam, ja vien to neprasa likums.',
      ],
    },
    {
      id: 'retention',
      title: 'Cik ilgi glabājam jūsu datus',
      blocks: [
        {
          dl: [
            ['Bezmaksas priekšskatījumi', 'Mēs tos neglabājam. Tie tiek atmesti, kad pieprasījums beidzas.'],
            ['Neapmaksāti pasūtījumi', 'Pasūtījumu, kas nav apmaksāts 24 stundu laikā, vairs nevar apmaksāt. Mūsu ikdienas automātiskā tīrīšana dzēš tā attēlus un ierakstus, parasti divu dienu laikā pēc pasūtījuma un vēlākais 30 dienu laikā.'],
            ['Augšupielāžu un paziņojumu atzīmes', 'Nelieli skaitītāji bez attēliem, vārdiem un e-pasta adresēm (apstiprinājumu par saņemšanu skaitītājā ir tikai īsa e-pasta adreses jaucējvērtība), tiek automātiski dzēsti pēc dažām dienām; apstiprinājumu mēneša skaitītāji aptuveni 40 dienas pēc sava mēneša beigām.'],
            ['Apmaksāti pasūtījumi', 'Jūsu pasūtījuma faili tiek glabāti 12 mēnešus no samaksas, lai varat tos lejupielādēt vēlreiz no savas pasūtījuma lapas, un pēc tam tos dzēš mūsu ikdienas automātiskā tīrīšana. Pēc pieprasījuma tos dzēšam agrāk; pēc tam jūsu pasūtījuma lapa vairs nevar piegādāt failu.'],
            ['Pasūtījumi, no kuriem notikusi atteikšanās', 'Ja atteikums stājas spēkā, mūsu ikdienas tīrīšana dzēš pasūtījuma attēlus, kad kopš atteikuma ir pagājušas 14 dienas (ja maksājums vēl tika apstrādāts, tad, kad tas ir pabeigts).'],
            ['Paziņojumi par atteikumu, kas neatbilst nevienam pasūtījumam', 'Tiek glabāti atsevišķi, mēs tos pārbaudām paši, un tie tiek automātiski dzēsti aptuveni 13 mēnešus pēc tā mēneša beigām, kurā tie mūs sasniedza.'],
            ['Pasūtījumu ieraksti', 'Kad faili ir dzēsti (pēc 12 mēnešiem, pēc atteikuma vai pēc pieprasījuma), glabājam apmaksāta pasūtījuma ierakstu: pasūtījuma numurs, datums, cena, maksājums un atmaksa, ja tāda bijusi, jūsu e-pasta adrese, tās reklāmas kampaņas kods, caur kuru atnācāt (ja tāds ir), dati par pasūtīto mākslas darbu (tajos var būt jūsu pievienotie vārdi, datums vai uzraksts un īss no jūsu priekšskatījumiem veikto mērījumu kopsavilkums: katras acs krāsas klase, gredzena vidējā krāsa un zīlītes forma), jūsu piekrišana sākt uzreiz, jūsu paziņojums par atteikumu (ja atteicāties) un mūsu administrēšanas žurnāla ieraksti par jūsu pasūtījumu. Bez attēliem. Glabājam to kā līguma pierādījumu un grāmatvedībai tik ilgi, cik to prasa Lietuvas grāmatvedības un nodokļu tiesību akti.'],
            ['Servera žurnāli un mērījumi', 'Mūsu mitināšanas pakalpojumu sniedzējs tos glabā īsu laiku, pēc tam tie tiek dzēsti.'],
            ['Pakalpojuma statistika', 'Tehniskie notikumi un to dienas kopskaiti (skatiet [Pakalpojuma statistika un mūsu administrēšanas žurnāls](#operations)): tiek automātiski dzēsti pēc 12 mēnešiem.'],
            ['Atsauksmju teksti', 'Neobligātie atsauksmju lodziņa teksti (skatiet [Pakalpojuma statistika un mūsu administrēšanas žurnāls](#operations)): tiek automātiski dzēsti pēc 90 dienām vai agrāk, ja tos izdzēšam mēs. Pašas atbildes ir tikai kodi un daļa no tehniskajiem notikumiem, un tās tiek glabātas, kā aprakstīts iepriekš.'],
            ['Administrēšanas žurnāls', 'Ko esam darījuši ar pasūtījumu savā administrēšanas panelī: tiek automātiski dzēsts pēc 24 mēnešiem; ieraksti par pasūtījumu paliek kopā ar tā pasūtījuma ierakstu.'],
            ['Neveiksmīgas pieteikšanās mūsu administrēšanas panelī', 'IP adreses jaucējvērtība, izveidota ar slepenu atslēgu, tiek automātiski dzēsta pēc 2 dienām.'],
            ['Bezmaksas priekšskatījumi uz savienojumu', 'IP adreses un dienas jaucējvērtība, izveidota ar slepenu atslēgu, tiek automātiski dzēsta pēc 2 dienām.'],
            ['Meta sīkdatnes un paziņojumi', '„_fbp” un „_fbc” jūsu pārlūkprogrammā: 90 dienas no jūsu pēdējā apmeklējuma, ja vien tās neizdzēšat agrāk; „snapeyes.fbc”: līdz aizverat cilni. Kopā ar maksājumu nodotās sīkdatņu vērtības, IP adrese un pārlūkprogrammas identifikators: kopā ar Stripe maksājuma ierakstu. Cik ilgi Meta glabā savus paziņojumus, nosaka Meta (skatiet tās privātuma politiku).'],
            ['E-pasti', 'Tik ilgi, cik tie mums vajadzīgi jūsu pieprasījumam un turpmākai saziņai.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Jūsu tiesības',
      blocks: [
        'Šīs tiesības jums ir jebkurā laikā:',
        {
          ul: [
            'Piekļuve: uzzināt, kādus datus par jums glabājam, un saņemt to kopiju (VDAR 15. pants).',
            'Labošana: panākt nepareizu datu labošanu (VDAR 16. pants).',
            'Dzēšana: panākt savu datu dzēšanu, piemēram, sava pasūtījuma failu dzēšanu pirms 12 mēnešu beigām (VDAR 17. pants).',
            'Apstrādes ierobežošana: panākt apstrādes ierobežošanu, kamēr jautājums tiek noskaidrots (VDAR 18. pants).',
            'Datu pārnesamība: saņemt datus, ko mums sniedzāt, plaši izmantotā, mašīnlasāmā formātā (VDAR 20. pants).',
            'Iebildumi: jebkurā laikā, pamatojoties uz iemesliem saistībā ar jūsu īpašo situāciju, iebilst pret apstrādi, kas balstīta uz mūsu leģitīmajām interesēm (VDAR 21. pants).',
          ],
        },
        `Lai izmantotu jebkuras no šīm tiesībām, rakstiet uz ${MAIL}. Atbildam viena mēneša laikā.`,
        'Jums ir arī tiesības iesniegt sūdzību uzraudzības iestādē. Mūsu uzraudzības iestāde ir Lietuvas Valsts datu aizsardzības inspekcija (Valstybinė duomenų apsaugos inspekcija, VDAI) Viļņā, [vdai.lrv.lt](https://vdai.lrv.lt). Varat vērsties arī tās ES valsts uzraudzības iestādē, kurā dzīvojat vai strādājat; Latvijā tā ir Datu valsts inspekcija.',
      ],
    },
    {
      id: 'storage',
      title: 'Sīkdatnes un lokālā krātuve',
      blocks: [
        'Mūsu pašu lapas neiestata sīkdatnes. Meta pikselis iestata divas Meta sīkdatnes, „_fbp” un „_fbc”, un mūsu lapa var glabāt atslēgu „snapeyes.fbc”: skatiet [Meta pikselis un mūsu reklāmas](#meta). Bez tā vietne neizmanto citu uzņēmumu analītikas, reklāmas vai izsekošanas rīkus.',
        'Kad ar valodas pārslēdzēju izvēlaties valodu, jūsu pārlūkprogramma šo izvēli atceras savā lokālajā krātuvē ar atslēgu „snapeyes.lang” (vērtība ir valodas kods, piemēram, „lv”). Tā nekad netiek nosūtīta mums, un jūs to jebkurā laikā varat izdzēst pārlūkprogrammas iestatījumos. Tā ir noteikti nepieciešama funkcijai, ko pieprasījāt, tāpēc tai nav vajadzīga piekrišana (Direktīvas 2002/58/EK jeb e-privātuma direktīvas 5. panta 3. punkts).',
        'Ja pie mums nonākat pa saiti ar cenām citā valūtā (piemēram, Austrālijas dolāros) vai izvēlaties valūtu ar mūsu valūtas pārslēdzēju vai mūsu piedāvājumā rādīt cenas jūsu valūtā, jūsu pārlūkprogramma arī šo izvēli atceras savā lokālajā krātuvē ar atslēgu „snapeyes.market” (piemēram, „au” vai, pēc šī piedāvājuma noraidīšanas, „eu”), lai vietne turpinātu rādīt jums tās pašas cenas. Mūsu lapas to nes savās saitēs (m=au) un nosūta kopā ar pasūtījumu, lai jūs maksātu cenas, ko redzējāt. Jūs to jebkurā laikā varat izdzēst pārlūkprogrammas iestatījumos; tā ir noteikti nepieciešama funkcijai, ko pieprasījāt, tāpēc arī tai nav vajadzīga piekrišana (Direktīvas 2002/58/EK jeb e-privātuma direktīvas 5. panta 3. punkts).',
        'Kad testējam cenas (tikai laiku pa laikam un uz ierobežotu laiku), jūsu pārlūkprogramma savā lokālajā krātuvē ar atslēgu „snapeyes.vid” var glabāt nejaušu anonīmu apmeklētāja numuru. Tas tiek izveidots tikai tad, kad tirgum (valūtai), ko skatāt, notiek cenu tests, un tiek atkal dzēsts, tiklīdz neviens tests vairs nenotiek; vēlākais pēc 90 dienām tas tiek aizstāts ar jaunu. Tas sastāv no 32 nejaušām rakstzīmēm un dienas, kad tas izveidots: tas nav atvasināts no jūsu datiem, tajā nav vārda, e-pasta adreses vai ierīces datu, un tas nekad netiek saistīts ar pasūtījumu. Jūsu pārlūkprogramma to nosūta mūsu serverim pieprasījuma galvenē (nekad lapas adresē), kad tā prasa cenas; mūsu lietotne to izmanto tikai tam, lai katru reizi vienādi noteiktu, kuru no testa cenrāžiem redzat, un to neglabā: apmeklētāju numuru sarakstu mēs nevedam. Serveris atbild ar parakstītu jūsu cenrāža atzīmi, ko jūsu pārlūkprogramma nosūta atpakaļ, kad pārejat uz maksājuma lapu, lai jūs maksātu tieši tās cenas, kas jums tika parādītas (pārlūkprogrammas nosūtīta cena vai cenrādis nekad netiek izmantots). Statistikai mūsu serveris reģistrē anonīmus skaitījumus par katru cenrādi: ka cenrādis parādīts, ka izveidots priekšskatījums, ka atvērta maksājuma lapa un ka pasūtījums apmaksāts (skatiet [Pakalpojuma statistika un mūsu administrēšanas žurnāls](#operations)); šajos skaitījumos nav apmeklētāja numura. Jūsu pārlūkprogramma lokālajā krātuvē atceras arī to, kurus no šiem skaitījumiem tā jau ir nosūtījusi („snapeyes.expseen”), un jūsu pēdējo cenrādi („snapeyes.pricing”), lai tās pašas cenas parādītos uzreiz. Tas, kuru cenrādi redzat, nekad nav atkarīgs no tā, kur dzīvojat, bet tikai no tirgus (valūtas), ko izvēlaties, un cena, ko maksājat, vienmēr ir tā, kas jums parādīta pirms maksāšanas; jūsu pasūtījuma apstiprinājumā ir norādīts piemērotais cenrādis. Šos ierakstus izmantojam tikai šim cenu testam, nekad reklāmai un nekad tam, lai sekotu jums citās vietnēs. Ja nevēlaties piedalīties, [atveriet šo saiti](/?pricetest=off&lang=lv): tad jūsu pārlūkprogramma glabā tikai atzīmi „snapeyes.notest”, dzēš apmeklētāja numuru un pārējos šeit minētos ierakstus un rāda un piemēro standarta cenas; ar [šo saiti](/?pricetest=on&lang=lv) jūs atkal piedalāties. Ja jūsu pārlūkprogramma sūta signālu „Global Privacy Control”, arī tas tiek uzskatīts par šādu izvēli. Visus šos ierakstus varat arī jebkurā laikā izdzēst pārlūkprogrammas iestatījumos (tad jums tiek veikta jauna nejauša izloze). Juridiskais pamats: mūsu leģitīmās intereses noteikt godīgas cenas (VDAR 6. panta 1. punkta f) apakšpunkts). Jūs jebkurā laikā varat iebilst (skatiet [Jūsu tiesības](#rights)).',
        'Ja pie mums nonākat caur reklāmu vai mūsu saiti ar kampaņas kodu, vai no citas vietnes, jūsu pārlūkprogramma glabā īsu kodu jūsu pārlūkprogrammas cilnes sesijas krātuvē ar atslēgu „snapeyes.c”: adreses parametrus, kas nosauc reklāmu, tādus, kādus tos ierakstījis tās veidotājs (utm_source, utm_medium, utm_campaign, utm_term un utm_content: platforma, veids, kampaņa, grupa un reklāma; piemēram, „utm_source=fb&utm_medium=maksas&utm_campaign=pavasaris”), vai, ja to nav, tikai tās vietnes veidu, no kuras atnācāt (piemēram, „ref=facebook”: Facebook, Instagram, TikTok, Google, tieša atnākšana vai cita vietne). Sesijas krātuve pieder tikai šai vienai cilnei un tiek dzēsta, kad to aizverat. Kods ir vienāds visiem, kas atnāca, noklikšķinot uz tās pašas reklāmas: tas nav atvasināts no jūsu datiem, un tajā nav vārda, e-pasta adreses, ierīces datu vai klikšķa numura (klikšķa numurs „fbclid” adresē nekad nav tā daļa; kas notiek ar šo numuru, ir aprakstīts sadaļā [Meta pikselis un mūsu reklāmas](#meta)). Mūsu lapas to nosūta kopā ar saviem anonīmajiem lapu skaitījumiem un pieprasījumiem (fotogrāfijas pārbaude, priekšskatījums, maksājuma lapa); pasūtījuma ieraksts to saglabā, un Stripe maksājuma lapa to saņem maksājuma metadatos, lai mēs varētu redzēt, kura reklāma noveda līdz kuram solim un līdz pasūtījumam (skatiet [Pakalpojuma statistika un mūsu administrēšanas žurnāls](#operations) un [Kad pasūtāt](#orders)). Mēs to izmantojam tikai šim nolūkam, nekad reklāmai, profilēšanai vai tam, lai sekotu jums citās vietnēs. Vietnes lietošanai tas jums nav vajadzīgs: ja to izdzēšat vai jūsu pārlūkprogramma bloķē sesijas krātuvi, viss darbojas tāpat, tikai trūkst šī skaitījuma. Juridiskais pamats: mūsu leģitīmās intereses zināt, vai mūsu pašu reklāma darbojas (VDAR 6. panta 1. punkta f) apakšpunkts). Jūs jebkurā laikā varat iebilst (skatiet [Jūsu tiesības](#rights)).',
        'Kad pasūtāt, lapa jūsu pārlūkprogrammas cilnes sesijas krātuvē glabā arī divus ierakstus. Sesijas krātuve pieder tikai šai vienai cilnei un tiek dzēsta, kad to aizverat:',
        {
          ul: [
            '„snapeyes.order”: tā pasūtījuma numurs, ko veidojat, un tā privātā atslēga, lai lapa varētu turpināt jūsu pasūtījumu, piemēram, kad atgriežaties no maksājuma lapas. Tas tiek noņemts, kad šajā cilnē atveras jūsu apmaksātā pasūtījuma lapa, un aizstāts, kad sākat jaunu pasūtījumu.',
            '„snapeyes.checkout”: tikai kamēr esat maksājuma lapā, jūsu mākslas darbs tāds, kādu to atstājāt (varavīksneņu izgriezumi no jūsu fotogrāfijām, priekšskatījumi, daži no tiem izmērīti skaitļi, stils un tā variants, izkārtojums, acu secība, kā arī vārdi un datums), lai, atgriežoties no maksājuma lapas, tas atkal tiktu parādīts. Tas tiek noņemts, tiklīdz atgriežaties vai kad šajā cilnē atveras jūsu apmaksātā pasūtījuma lapa.',
          ],
        },
        'Lapa tos izmanto tikai jūsu pasūtījumam, un tie tam ir noteikti nepieciešami, tāpēc arī tiem nav vajadzīga piekrišana (Direktīvas 2002/58/EK jeb e-privātuma direktīvas 5. panta 3. punkts).',
        'Kad maksājat, Stripe maksājuma lapa var izmantot savas sīkdatnes, kas vajadzīgas drošam maksājumam un krāpšanas novēršanai; tur ir spēkā Stripe privātuma un sīkdatņu politika.',
      ],
    },
    {
      id: 'required',
      title: 'Vai jums ir jāsniedz mums dati?',
      blocks: ['Nē. Taču bez fotogrāfijas nevaram izveidot priekšskatījumu, un bez e-pasta adreses un maksājuma nevaram piegādāt pasūtījumu.'],
    },
    {
      id: 'changes',
      title: 'Šīs politikas izmaiņas',
      blocks: ['Mēs atjauninām šo politiku, kad mainās mūsu pakalpojums vai tiesību akti. Datums augšā rāda spēkā esošo redakciju.'],
    },
  ],
};
