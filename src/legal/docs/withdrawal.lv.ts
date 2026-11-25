// Atteikuma tiesības: the Latvian twin of `en` in src/legal/docs/withdrawal.ts, same section ids and blocks in the same
// order. Every rule of the English header (when the right ends, as api/_lib/withdraw.py decides it; the online
// function; the receipts and their limits) holds here word for word in meaning.
//
// The right of withdrawal is "atteikuma tiesības", the period "atteikuma termiņš", the statement "paziņojums par
// atteikumu", the receipt "apstiprinājums par atteikuma saņemšanu", a durable medium "pastāvīgs informācijas nesējs":
// the words of the official Latvian text of Directive 2011/83/EU. The statutory parts are the EU models in that text,
// kept word for word (checked 2026-11-13 against the Publications Office's Formex files: the consolidated text of
// 2011/83/EU of 28.05.2022 and OJ L, 2023/2673, 28.11.2023, Latvian editions). Unlike the Croatian twin, no national
// model is used here: this file follows the English one block for block.
//  - "right": Annex I(A) "Paraugs norādījumiem par atteikumu" in the wording of Directive (EU) 2019/2161 ("pa pastu
//    nosūtītu vēstuli vai e-pastu"). Its gaps are filled as its own instructions say: [1] "līguma noslēgšanas dienas"
//    (instruction 1 a: digital content not supplied on a tangible medium), [2] the seller's details in brackets
//    (contactLineLv: name, address, email, and the phone once the owner shows one; the owner decided to show none,
//    PHONE_OMITTED_BY_OWNER), [3] the sentence of instruction 3 as replaced by Annex I of Directive (EU) 2023/2673 for
//    an obligatory online function, with the address and the button inserted where the model says "[ievietot interneta
//    adresi vai citu piemērotu paskaidrojumu par to, kur ir pieejama atteikuma funkcija]" (the word "adresē" before the
//    address is part of that explanation).
//  - "effects": the model's paragraph, unchanged. Delivery costs do not exist here, but the clause stays: it is the
//    unchanged model.
//  - "form": Annex I(B) "Atteikuma veidlapas paraugs", word for word, its "Adresāts" line filled with formLineLv. One
//    typographic change: the model starts its lines with an em dash; here they are the lines of a box (owner rule: no
//    en or em dashes anywhere).
// The online function's labels are the Directive's, Art. 11a(1) and (3) in the Latvian text ("Atteikties no līguma",
// "Apstiprināt atteikumu": the Latvian text has no word for the English "here"), held in src/shared/legal.ts
// WITHDRAWAL_ONLINE.lv. The early end for digital content is Art. 16(m) of the Directive.
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { CONTACT_EMAIL, contactLine, formLine } from '../facts';
import { WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';

const formLineLv = formLine('lv');
const contactLineLv = contactLine('lv');
const WITHDRAWAL_ONLINE_LV = WITHDRAWAL_ONLINE.lv;
const withdrawFunctionHrefLv = () => withdrawFunctionHref('lv');
const withdrawFunctionAddressLv = () => withdrawFunctionAddress('lv');

const W = WITHDRAWAL_ONLINE_LV;

export const lv: LegalDoc = {
  title: 'Atteikuma tiesības',
  description:
    'Informācija par atteikuma tiesībām SnapEyes digitālajiem failiem: 14 dienu atteikuma tiesības un atteikuma veidlapas paraugs.',
  lead:
    'Patērētājiem ES ir 14 dienu atteikuma tiesības, pērkot tiešsaistē. No pasūtījuma varat atteikties 14 dienu laikā un saņemt atpakaļ visu naudu, pat ja fails jau ir jūsu rīcībā. Šeit ir visa informācija.',
  sections: [
    {
      id: 'right',
      title: 'Atteikuma tiesības',
      blocks: [
        'Jums ir tiesības 14 dienu laikā atteikties no šā līguma, neminot iemeslu.',
        'Atteikuma termiņš beigsies pēc 14 dienām, sākot no līguma noslēgšanas dienas.',
        `Lai izmantotu atteikuma tiesības, jums ar nepārprotamu paziņojumu (piemēram, pa pastu nosūtītu vēstuli vai e-pastu) mūs (${contactLineLv}) ir jāinformē par lēmumu atteikties no šā līguma. Jūs varat izmantot pievienoto atteikuma veidlapas paraugu, bet tas nav obligāti. Atteikuma tiesības varat izmantot arī tiešsaistē adresē [${withdrawFunctionAddressLv()}](${withdrawFunctionHrefLv()}) (poga „${W.button}”). Ja izmantojat šo tiešsaistes funkciju, mēs jums bez nepamatotas kavēšanās nosūtīsim apstiprinājumu par atteikuma saņemšanu uz pastāvīga informācijas nesēja (piemēram, pa e-pastu), norādot tā saturu un iesniegšanas datumu un laiku.`,
        'Lai atteikuma termiņš būtu ievērots, pietiek, ja savu paziņojumu par atteikuma tiesību izmantošanu jūs nosūtīsiet pirms atteikuma termiņa beigām.',
      ],
    },
    {
      id: 'effects',
      title: 'Atteikuma radītās sekas',
      blocks: [
        'Ja jūs atteiksieties no šā līguma, mēs jums atmaksāsim visus no jums saņemtos maksājumus, tostarp piegādes izmaksas (izņemot papildu izmaksas, kas radušās tādēļ, ka jūs esat izvēlējies piegādes veidu, kas nav mūsu piedāvātais vislētākais standarta piegādes veids), bez nepamatotas kavēšanās un jebkurā gadījumā ne vēlāk kā 14 dienu laikā no dienas, kad mēs tikām informēti par jūsu lēmumu atteikties no šā līguma. Šādu atmaksāšanu mēs veiksim, izmantojot tādu pašu maksāšanas līdzekli, kādu jūs izmantojāt sākotnējam darījumam, ja vien jūs neesat skaidri piekritis to darīt citādi. Jebkurā gadījumā jums šādas atmaksāšanas rezultātā nebūs jāmaksā nekāda maksa.',
      ],
    },
    {
      id: 'expiry',
      title: 'Cik ilgi ir spēkā atteikuma tiesības',
      blocks: [
        'Jūsu failu sākam veidot uzreiz pēc samaksas un piegādājam to jūsu pasūtījuma lapā. **Tas nebeidz jūsu atteikuma tiesības:** no līguma varat atteikties 14 dienu laikā no līguma noslēgšanas dienas, arī tad, kad jūsu fails vēl tiek veidots vai jau ir jūsu rīcībā, un jūs saņemat atpakaļ visu samaksāto (skatiet [Atteikuma radītās sekas](#effects)).',
        'Kā skaita 14 dienu atteikuma termiņu: jūsu samaksas diena netiek ieskaitīta, un, ja termiņa pēdējā diena ir sestdiena, svētdiena vai svētku diena, termiņš beidzas nākamās darba dienas beigās. Tas neietekmē jūsu likumīgās tiesības, ja failam ir trūkumi: skatiet mūsu pārdošanas noteikumu sadaļu [Sūdzības un trūkumi](doc:terms#defects).',
      ],
    },
    {
      id: 'online',
      title: 'Atteikšanās tiešsaistē',
      blocks: [
        `Kamēr jūsu atteikuma tiesības ir spēkā, no līguma jebkurā laikā varat atteikties tiešsaistē ar funkciju [„${W.button}”](${withdrawFunctionHrefLv()}). Tā atrodama mūsu sākumlapas un juridiskās informācijas lapu apakšā, jūsu pasūtījuma lapā un aiz atteikuma saites pasūtījuma apstiprinājuma e-pastā. Šī saite atver funkciju jūsu pasūtījumam, neko nesākot.`,
        `Kā tas notiek: ievadiet savu vārdu un uzvārdu, pasūtījuma numuru (tas jau ir ierakstīts, ja nākat no savas pasūtījuma lapas vai pa atteikuma saiti) un e-pasta adresi apstiprinājumam par saņemšanu, pēc tam nosūtiet savu paziņojumu par atteikumu ar pogu „${W.confirm}”. Ja nākat bez kādas no šīm saitēm, lūdzu, norādiet e-pasta adresi, ar kuru maksājāt, lai mēs varētu atrast jūsu pasūtījumu. Ja dati neatbilst nevienam mūsu pasūtījumam, lapa jums to pateiks; jūsu paziņojumu tomēr saglabājam, pārbaudām paši un nosūtām jums e-pastā apstiprinājumu par saņemšanu. Lai novērstu mūsu e-pastu ļaunprātīgu izmantošanu, apstiprinājumu par saņemšanu skaits ir ierobežots: paziņojumiem, kas neatbilst nevienam mūsu pasūtījumam, līdz diviem dienā un četriem mēnesī uz vienu adresi; vienam pasūtījumam kopā līdz trim uz adresēm, kas nav adrese, ar kuru par to maksāts (turpmākie tiek sūtīti uz adresi, ar kuru maksājāt); un atkārtotam paziņojumam par pasūtījumu, uz kuru jau esam atbildējuši, līdz vienam dienā šim pasūtījumam un pieciem dienā visiem pasūtījumiem kopā. Ja lapa nevar pieņemt jūsu paziņojumu, piemēram, tehniskas kļūmes dēļ vai tāpēc, ka pienāk neparasti daudz paziņojumu, tā jums to pateiks: tad, lūdzu, nosūtiet mums atteikumu pa e-pastu; e-pasts ir tikpat derīgs.`,
        'Kas notiek pēc tam: jūsu paziņojumu reģistrējam ar datumu un laiku, kad tas mūs sasniedza. Ja jūsu pasūtījums ir apmaksāts un 14 dienu atteikuma termiņš nav beidzies, jūsu atteikums stājas spēkā: apturam jūsu pasūtījumu, ja jūsu fails vēl nav pabeigts, un atmaksājam naudu, kā aprakstīts sadaļā [Atteikuma radītās sekas](#effects). Ja jūsu maksājums vēl tika apstrādāts, kad atteicāties, nekas netiek veidots, un, ja maksājums mūs sasniedz, atmaksājam to pilnībā. Bez kavēšanās nosūtām jums e-pastā apstiprinājumu par saņemšanu ar jūsu atteikuma saturu, datumu un laiku.',
        'Ja 14 dienu atteikuma termiņš bija beidzies, jūsu atteikuma tiesības jau bija beigušās (skatiet [Cik ilgi ir spēkā atteikuma tiesības](#expiry)): lapa un apstiprinājums par saņemšanu jums to pateiks, un jūsu paziņojumu mēs tomēr izskatām personīgi. Ja jūsu pasūtījums nekad nav apmaksāts, nav līguma, no kura atteikties: lapa jums to pateiks, un nekas nav iekasēts. Tas neietekmē jūsu tiesības, ja failam ir trūkumi.',
      ],
    },
    {
      id: 'form',
      title: 'Atteikuma veidlapas paraugs',
      blocks: [
        '(Aizpildiet un nosūtiet šo veidlapu tikai tad, ja vēlaties atteikties no līguma.)',
        {
          box: [
            `Adresāts: ${formLineLv}`,
            'Es/mēs (*) paziņoju/paziņojam, ka es/mēs (*) vēlos/vēlamies atteikties no manis/mūsu (*) noslēgtā pārdošanas līguma par šādu preču iegādi (*)/pakalpojumu sniegšanu (*):',
            'Pasūtīšanas datums (*)/saņemšanas datums (*):',
            'Patērētāja(-u) vārds(-i) un uzvārds(-i):',
            'Patērētāja(-u) adrese:',
            'Patērētāja(-u) paraksts (tikai tad, ja šo veidlapu nosūta uz papīra):',
            'Datums:',
            '(*) Nevajadzīgo svītrot.',
          ],
        },
        `Pa e-pastu vienkārši nosūtiet aizpildīto veidlapu vai savu paziņojumu uz [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Atteikums%20no%20l%C4%ABguma). Ja jums ir pasūtījuma numurs, lūdzu, norādiet to. Tiešsaistē izmantojiet augstāk aprakstīto funkciju [„${W.button}”](${withdrawFunctionHrefLv()}).`,
      ],
    },
  ],
};
