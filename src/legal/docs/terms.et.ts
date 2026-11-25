// Müügitingimused: the Estonian twin of `en` in src/legal/docs/terms.ts, same section ids and blocks in the same
// order, the same facts from src/landing/config.ts (through ../facts). Everything the English header says holds here
// too: no ODR link, no VAT number, no promise the code does not keep, the right of withdrawal ends when making the file
// begins (or with the 14-day period, counted as withdraw.py period_end counts it), the seller line has no phone (owner
// decision).
// Estonian law behind the wording (Võlaõigusseadus, VÕS, read 2026-11-13 from riigiteataja.ee; it and the Estonian text
// of Directive 2011/83/EU call the right of withdrawal "taganemisõigus", so these terms do too):
//  - § 62¹ lg 3: the order button says „tellimus koos maksekohustusega“ or a similar unambiguous wording. Our button
//    (CHECKOUT_LEGAL.et.continueButton) places no order; the binding order is Stripe's pay button (Stripe Checkout,
//    locale "et"), which the terms say („Maksekohustusega tellimuse esitate siis, kui kinnitate seal makse
//    maksenupuga.“). Whether Stripe's own Estonian label alone is unambiguous enough is a question for a lawyer, as the
//    German "Bezahlen" is.
//  - § 56 lg 1 and lg 1³: 14 days from the conclusion of the contract for digital content; § 53 lg 4 p 7¹: the digital
//    content exception (express prior consent, acknowledgement of losing the right, the confirmation of § 55);
//    § 56⁴: the online function („Taganen lepingust“, „Kinnitan taganemise“); § 56¹ lg 1: refund within 14 days.
//  - The counting of the period (the day of payment not counted, a last day on a Saturday, Sunday or public holiday
//    moved to the next working day) is Regulation 1182/71 Art. 3, as withdraw.py period_end counts it.
//  - Out of court: the seller is Lithuanian, so the out-of-court body stays the Lithuanian Valstybinė vartotojų teisių
//    apsaugos tarnyba (VVTAT); no ODR link (the platform closed on 20 July 2025). "disputes" names the Estonian Acts as
//    the mandatory law a consumer living in Estonia keeps (Rome I Art. 6(2)): võlaõigusseadus and tarbijakaitseseadus.
//  - VAT: the English sentence, in Estonian („Me ei ole käibemaksukohustuslane, seega käibemaksu ei arvestata ega
//    näidata.“).
//  - The contract languages are named („Lepingu keeled: eesti, inglise, saksa, leedu, ungari, horvaadi, soome ja
//    läti.“): the other languages' terms must name Estonian too (the build checks it, scripts/check_texts.mjs CONTRACT).
//  - The latest delivery time is "N tunni jooksul" (tunniJooksul below: the genitive, which is "tunni" after every
//    number).
// Formal "teie", written in lower case. Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { DELIVERY_MAX_HOURS, MAIL, PRICE_CENTS, SELLER, address, company, eur, phoneSuffix, representedSuffix } from '../facts';
import { aiBlocks } from '../../shared/aiMaterial';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../../shared/legal';

const companyEt = company('et');
const addressEt = address('et');
const phoneSuffixEt = phoneSuffix('et');
const representedSuffixEt = representedSuffix('et');
const eurEt = (cents: number) => eur(cents, 'et');
const WITHDRAWAL_ONLINE_ET = WITHDRAWAL_ONLINE.et;
const CHECKOUT_LEGAL_ET = CHECKOUT_LEGAL.et;

/** "48 tunni jooksul", "1 tunni jooksul": hours in the genitive (the same form after every number). */
const tunniJooksul = (n: number) => `${n} tunni jooksul`;

const TRANSPARENCY_ET = 'Värv tuleb teie enda fotolt. Seal, kus teie telefon ei suutnud kõige peenemaid kiude jäädvustada, taastab need meie tehisintellekt.';
const PX = '4096 px';
const SQUARE = '4096 × 4096 px';

const STANDARD_LIST_NOTE_ET =
  'Ülaltoodud tabel on meie standardhinnakiri. Aeg-ajalt proovime piiratud aja jooksul mõne juhuslikult valitud külastaja puhul teisi hinnakirju. Teilt võetakse alati need hinnad, mida teile näidati kunstiteose lehel enne maksmist ja makselehel, ning tellimuse kinnituskirjas on nimetatud hinnakiri, mis teie tellimuse puhul kehtis. See, millist hinnakirja te näete, ei sõltu kunagi riigist, kus te elate, vaid ainult teie valitud turust (valuutast).';
const PAY_ET = 'Maksate ette meie makseteenuse pakkuja Stripe’i kaudu, makselehel näidatud makseviisidega.';

export const et: LegalDoc = {
  title: 'Müügitingimused',
  description:
    'SnapEyesi digitaalse iirisekunstiteose tellimise tingimused: toode, hinnad, maksmine, üleandmine, teie litsents, taganemisõigus ja kaebused.',
  lead: 'Need tingimused kehtivad iga tellimuse kohta, mis esitatakse veebilehel snapeyes.com. Palun lugege need enne tellimist läbi. Tasuta eelvaadet pakutakse ilma igasuguse kohustuseta.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'Kellega te lepingu sõlmite',
      blocks: [
        `Sõlmite lepingu ettevõttega ${companyEt}, mis on Leedu õiguse alusel asutatud väikeühing (mažoji bendrija)${representedSuffixEt}, registrikood ${SELLER.code}, ${addressEt}, e-post ${MAIL}${phoneSuffixEt} (edaspidi „meie“ või „SnapEyes“). Kõik andmed on lehel [Ettevõtte andmed](doc:imprint).`,
        'Meie pakkumine on mõeldud tarbijatele. Kui olete alla 18-aastane, paluge vanemal või eestkostjal enda eest tellida.',
      ],
    },
    {
      id: 'product',
      title: 'Mida te ostate',
      blocks: [
        `Isikupärastatud digitaalne kunstiteos, mis on valmistatud teie enda silmafotost (või mitme silma fotodest), teie valitud stiilis, paigutuses ja tekstiga. Saate ühe pildifaili (JPEG) ilma vesimärgita: ${SQUARE} ühe silma puhul, ${PX} pikimal küljel mitme silma puhul. Kunstiteos antakse üle ainult digitaalse failina, allalaadimise teel. Me ei müü trükitud pilte, raame ega muid füüsilisi tooteid.`,
        `${TRANSPARENCY_ET} Kunstiteos on seega kunstiline taastamine, mitte meditsiiniline pilt ega mikroskoobipilt, ning see ei sobi ühekski meditsiiniliseks otstarbeks ega isiku tuvastamiseks.`,
        ...aiBlocks('et'),
      ],
    },
    {
      id: 'preview',
      title: 'Teie eelvaade ja teie fail',
      blocks: [
        'Enne tellimist näete tasuta vesimärgiga eelvaadet ja kiidate selle heaks. Teie fail järgib eelvaadet, mille heaks kiitsite: sama silm, stiil, paigutus, silmade järjestus ja tekst, sama värvi ja tooniga, valmistatud üks kord täisresolutsioonis. Täissuuruses lisab meie tehisintellekt peened kiudude detailid, mille näitamiseks on eelvaade liiga väike, seega võivad kõige peenemad detailid eelvaatest veidi erineda. Viie kuni kaheksa silmaga eelvaade tehakse teie fotode väiksematest koopiatest, seega on see teie failist jämedam.',
        'Kui teie fail erineb selgelt eelvaatest, mille heaks kiitsite (näiteks värvi, heleduse või pupilli poolest), on see puudus: vt [Kaebused ja puudused](#defects).',
      ],
    },
    {
      id: 'contract',
      title: 'Kuidas leping sõlmitakse',
      blocks: [
        `Eelvaated ja hinnad meie veebilehel ei ole veel siduv pakkumine. Enne maksmist saate oma silmad, stiili, paigutuse ja teksti üle kontrollida ning parandada mis tahes sisestust, minnes tagasi või pildistades uuesti. Seejärel avate meie nupuga „${CHECKOUT_LEGAL_ET.continueButton}“ meie makseteenuse pakkuja Stripe’i makselehe; see nupp ei esita veel tellimust. Sellel lehel sisestate oma e-posti aadressi ja makseandmed ning saate neid parandada. Maksekohustusega tellimuse esitate siis, kui kinnitate seal makse maksenupuga.`,
        'Leping on sõlmitud, kui teie makse on kinnitatud. Seejärel avaneb teie tellimuse leht ja me saadame teile selle lingi e-kirjaga koos tellimuse kinnitusega. Niipea kui see e-kiri on välja saadetud, hakkame seal teie faili valmistama.',
        'Lepingu keeled: eesti, inglise, saksa, leedu, ungari, horvaadi, soome ja läti.',
        'Säilitame teie tellimuse koos lepingu andmetega: tellitud kunstiteos, hind, kuupäev, teie e-posti aadress ja teie nõusolek kohe alustada. Teie tellimuse leht näitab neid andmeid seni, kuni me teie tellimust säilitame. Me ei säilita iga tellimuse kohta nende tingimuste eraldi koopiat. Selle asemel sisaldab tellimuse kinnituskiri tekstina teie tellimuse andmeid, neid tingimusi ja taganemisõiguse teavet koos taganemisavalduse tüüpvormiga, tellimise ajal kehtinud versioonis: palun hoidke see e-kiri alles. Samuti võite selle lehe igal ajal salvestada või välja trükkida.',
      ],
    },
    {
      id: 'prices',
      title: 'Hinnad ja maksmine',
      blocks: [
        {
          dl: [
            ['Üks silm, Clean Iris', eurEt(PRICE_CENTS.studioBlack)],
            ['Üks silm, mis tahes muu stiil', eurEt(PRICE_CENTS.artBackground)],
            ['Kaks silma, mis tahes stiil', eurEt(PRICE_CENTS.coupleDuo)],
            ['Iga järgmine silm', `+${eurEt(PRICE_CENTS.extraEye)}`],
          ],
        },
        'Kõik hinnad on lõpphinnad eurodes. Me ei ole käibemaksukohustuslane, seega käibemaksu ei arvestata ega näidata. Kättetoimetamiskulusid ei ole.',
        STANDARD_LIST_NOTE_ET,
        PAY_ET,
      ],
    },
    {
      id: 'delivery',
      title: 'Üleandmine',
      blocks: [
        `Teie tellimuse leht valmistab teie faili niipea, kui tellimuse kinnituskiri on välja saadetud, tavaliselt minuti jooksul pärast makset; valmistamine võtab tavaliselt paar minutit. Kui sulgete lehe enne faili valmimist, jätkub valmistamine siis, kui avate lehe uuesti e-kirjas oleva lingi kaudu. Kui meie automaatne kvaliteedikontroll märgib faili, vaatame selle enne väljastamist ise üle ja saadame teile e-kirja, kui see on valmis. **Teie fail on teie tellimuse lehel allalaadimiseks valmis hiljemalt ${tunniJooksul(DELIVERY_MAX_HOURS)} pärast teie makse kinnitamist.** Oma tellimuse lehelt saate faili igal ajal alla laadida seni, kuni me seda säilitame: 12 kuud alates maksest (vt meie [Privaatsuspoliitikat](doc:privacy)). Iga allalaadimislink, mille leht loob, kehtib 7 päeva; leht loob uue lingi iga kord, kui selle avate. Kui kaotate e-kirja, kirjutage meile.`,
        'Teie tellimuse lehe link sisaldab privaatset võtit: igaüks, kellel see on, saab teie kunstiteose alla laadida, seega hoidke see palun enda teada. Palun laadige oma fail alla ja hoidke koopia alles. 12 kuu pärast see kustutatakse ja seda ei saa taastada.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Taganemisõigus',
      blocks: [
        `Teie kunstiteos on teie jaoks valmistatud digitaalne fail ja enne ostu näete tasuta selle eelvaadet. **Makstes nõustute, et hakkame teie faili kohe valmistama ja et pärast alustamist ei saa lepingust enam taganeda ning hinda ei tagastata.** Alustame kohe pärast seda, kui tellimuse kinnituskiri on välja saadetud, tavaliselt minuti jooksul pärast makset. Kui me ei saa teie faili üle anda, tagastame kogu summa; kui fail on puudusega, vt [Kaebused ja puudused](#defects).`,
        `Seni, kuni me ei ole alustanud, saate 14-päevase taganemistähtaja jooksul taganeda e-kirjaga, postiga või veebis nupuga „${WITHDRAWAL_ONLINE_ET.button}“ ja tagastame kogu summa. Kogu teave, veebipõhine funktsioon ja taganemisavalduse tüüpvorm on lehel [Taganemisõigus](doc:withdrawal).`,
      ],
    },
    {
      id: 'photos',
      title: 'Teie fotod',
      blocks: [
        'Laadige üles ainult fotosid oma silmast või sellise inimese silmast, kes on sellega nõustunud (lapse puhul: vanem või eestkostja). Foto üleslaadimisega kinnitate, et tohite seda sel eesmärgil kasutada.',
        'Õigused teie fotole jäävad teile. Kasutame seda ainult teie eelvaate ja teie kunstiteose valmistamiseks, nagu on kirjeldatud meie [Privaatsuspoliitikas](doc:privacy).',
        'Võime tellimusest keelduda ja tagastada makse täies ulatuses, kui foto rikub selgelt neid reegleid.',
      ],
    },
    {
      id: 'licence',
      title: 'Mida te oma kunstiteosega teha tohite',
      blocks: [
        'Saate tähtajatu lihtlitsentsi (mitteainuõigusliku litsentsi) oma kunstiteose kasutamiseks isiklikel, mitteärilistel eesmärkidel. Võite selle näiteks endale välja trükkida (kodus või trükikojas), raamida, kinkida, kasutada taustapildina oma seadmetes ja jagada oma isiklikus sotsiaalmeedias.',
        'Ilma meie loata (piisab e-kirjast) ei tohi te kunstiteost ega sellest valmistatud tooteid müüa, anda teistele selle suhtes õigusi ega kasutada seda reklaamiks või muul ärilisel eesmärgil.',
        'Stiilid, taustad, paigutused ja SnapEyesi kujundus jäävad meile, sealhulgas kõik nendega seotud autoriõigused. Sama kehtib vesimärgiga eelvaadete kohta.',
      ],
    },
    {
      id: 'defects',
      title: 'Kaebused ja puudused',
      blocks: [
        `Teie seadusest tulenevad õigused lepingutingimustele mittevastava digitaalse sisu korral kehtivad täies ulatuses. Kui teie fail on puudusega, näiteks seda ei saa alla laadida või avada, see on kahjustatud, lubatust väiksem või erineb selgelt eelvaatest, mille heaks kiitsite, kirjutage palun aadressile ${MAIL} ja lisage oma tellimuse number. Valmistame faili tasuta uuesti või kui see puudust ei kõrvalda, tagastame teile raha.`,
      ],
    },
    {
      id: 'liability',
      title: 'Vastutus',
      blocks: [
        'Vastutame piiranguteta tahtluse ja raske hooletuse eest, elu, keha või tervise kahjustamise eest ning alati, kui kohustuslikud õigusnormid seda ette näevad. Muudel juhtudel vastutame kerge hooletuse korral ainult oluliste lepinguliste kohustuste rikkumise eest ja ainult kahju eest, mis on seda liiki lepingu puhul tüüpiline ja ettenähtav. Tasuta eelvaadet pakutakse sellisena, nagu see on, ilma igasuguse õiguseta selle kättesaadavusele.',
      ],
    },
    {
      id: 'disputes',
      title: 'Vaidlused ja kohaldatav õigus',
      blocks: [
        'Kui midagi on valesti, kirjutage palun esmalt meile: enamik probleeme laheneb e-kirja teel kiiresti.',
        'Kui me kokkuleppele ei jõua, võivad tarbijad pöörduda Leedu riikliku tarbijaõiguste kaitse ameti poole (Valstybinė vartotojų teisių apsaugos tarnyba, [vvtat.lt](https://vvtat.lt)), mis lahendab tarbijavaidlusi kohtuväliselt, või oma riigi tarbijakaitseasutuste ja kohtute poole.',
        'Kohaldatakse Leedu õigust. Kui olete tarbija, kes elab mõnes teises ELi riigis, säilib teile selle riigi kohustuslike tarbijakaitsenormide kaitse (Eestis: võlaõigusseadus ja tarbijakaitseseadus).',
      ],
    },
    {
      id: 'changes',
      title: 'Nende tingimuste muutmine',
      blocks: ['Tellimuse suhtes kohaldatakse tingimusi, mis kehtisid selle esitamise ajal.'],
    },
  ],
};

// No forint edition: the Hungarian edition (the hu market) has no Estonian texts (src/shared/legal.ts EDITION_LANGS), so there
// is no Estonian twin of huHufPrices.
