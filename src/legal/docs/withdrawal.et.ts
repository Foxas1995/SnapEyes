// Taganemisõigus: the Estonian twin of `en` in src/legal/docs/withdrawal.ts, same section ids and blocks in the same
// order. Every rule of the English header (when the right ends, as api/_lib/withdraw.py decides it; the online
// function; the receipts and their limits) holds here word for word in meaning.
//
// Estonian law and the Estonian text of Directive 2011/83/EU use the same words: "taganemisõigus" (the right of
// withdrawal), "lepingust taganema" (to withdraw), "taganemistähtaeg" (the period), "taganemisavaldus" (the statement),
// "püsiv andmekandja" (a durable medium). The statutory parts are the Estonian national model, which transposes Annex I
// of the Directive: justiitsministri 17.12.2013 määrus nr 41 „Sidevahendi abil sõlmitud lepingust ja väljaspool
// äriruume sõlmitud lepingust taganemise avalduse tüüpvormi ja taganemise näidisjuhendi kehtestamine“, lisa 1 (the
// form) and lisa 2 (the instructions), read 2026-11-13 from riigiteataja.ee. Kept word for word, including the model's
// capitals "Teil", "Te", "Teie" (our own sentences use the lower-case "teie" of the other Estonian legal texts):
//  - "right": the first sentence; the period sentence with option 1(a) „mil leping sõlmiti“ (digital content not
//    supplied on a tangible medium); the sentence on how to withdraw, with the seller's details inserted after "meid"
//    as the model's [2] asks (contactLineEt: name, address, email, and the phone once the owner shows one; the owner
//    decided to show none, PHONE_OMITTED_BY_OWNER) and its example without the fax, as Directive (EU) 2019/2161 has
//    it; then the sentence for an obligatory online function (Annex I(A) instruction 3 as replaced by Directive (EU)
//    2023/2673), word for word from the Estonian text of the Official Journal (OJ L, 2023/2673, read 2026-11-13; it
//    writes "te", "teile" in lower case), with the address and the button inserted; and the model's deadline sentence.
//  - "effects": the model's paragraph for a contract without goods, word for word. Delivery costs do not exist here,
//    but the clause stays: it is the unchanged model.
//  - "form": lisa 1, „taganemise avalduse tüüpvorm“, word for word, its "Kellele" line filled with formLineEt. One
//    typographic change: the model starts each line with an em dash; here the lines stand alone (owner rule: no en or
//    em dashes anywhere).
// The online function's labels are those of Art. 11a of the Directive in its Estonian text and of Võlaõigusseadus § 56⁴
// lg 1 and 3 (RT I, 27.05.2026, 2: „Taganen lepingust“, „Kinnitan taganemise“), held in src/shared/legal.ts WITHDRAWAL_ONLINE.et. The early
// end for digital content is Võlaõigusseadus § 53 lg 4 p 7¹, which "expiry" names next to Art. 16(m) of the Directive.
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { CONTACT_EMAIL, contactLine, formLine } from '../facts';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';

const formLineEt = formLine('et');
const contactLineEt = contactLine('et');
const WITHDRAWAL_ONLINE_ET = WITHDRAWAL_ONLINE.et;
const CHECKOUT_LEGAL_ET = CHECKOUT_LEGAL.et;
const withdrawFunctionHrefEt = () => withdrawFunctionHref('et');
const withdrawFunctionAddressEt = () => withdrawFunctionAddress('et');

const W = WITHDRAWAL_ONLINE_ET;

export const et: LegalDoc = {
  title: 'Taganemisõigus',
  description:
    'Taganemisõiguse teave SnapEyesi digitaalsete failide kohta: 14-päevane taganemisõigus, millal see varem lõpeb, ja taganemisavalduse tüüpvorm.',
  lead:
    'ELi tarbijatel on veebis tehtud ostude puhul taganemisõigus. Sellise digitaalse faili puhul nagu meie oma lõpeb see varem: niipea, kui hakkame teie nõusolekul teie faili valmistama. Siin on kogu teave.',
  sections: [
    {
      id: 'right',
      title: 'Taganemisõigus',
      blocks: [
        'Teil on õigus põhjust avaldamata taganeda kõnesolevast lepingust 14 päeva jooksul.',
        'Taganemistähtaeg lõpeb 14 päeva möödumisel alates päevast, mil leping sõlmiti.',
        `Taganemisõiguse kasutamiseks teavitage meid (${contactLineEt}) oma otsusest taganeda kõnesolevast lepingust ühemõttelise avaldusega (nt posti või e-postiga saadetud kiri). Te võite selleks kasutada lisatud taganemisavalduse tüüpvormi, kuid see ei ole kohustuslik. Teil on võimalik kasutada oma taganemisõigust ka internetis aadressil [${withdrawFunctionAddressEt()}](${withdrawFunctionHrefEt()}) (nupp „${W.button}“). Kui te kasutate seda internetipõhist funktsiooni, saadame teile põhjendamatu viivituseta püsival andmekandjal (näiteks e-kirjaga) kinnituse taganemisteate kättesaamise, sealhulgas selle sisu ning selle esitamise kuupäeva ja kellaaja kohta.`,
        'Taganemisõiguse kasutamise tähtajast kinnipidamiseks piisab, kui saadate teate taganemisõiguse kasutamise kohta ära enne taganemistähtaja lõppu.',
      ],
    },
    {
      id: 'effects',
      title: 'Lepingust taganemise tagajärjed',
      blocks: [
        'Kui Te taganete kõnesolevast lepingust, tagastame Teile kõik Teilt saadud maksed, sealhulgas kättetoimetamiskulud (välja arvatud täiendavad kulud, mis tulenevad Teie valitud kättetoimetamise viisist, mis erineb meie pakutud kõige odavamast tavapärasest kättetoimetamise viisist) viivitamata, kuid hiljemalt 14 päeva möödumisel alates päevast, mil saame teada Teie otsusest kõnesolevast lepingust taganeda. Teeme nimetatud tagasimaksed, kasutades sama makseviisi, mida kasutasite makse tegemiseks, välja arvatud juhul, kui olete sõnaselgelt andnud nõusoleku teistsuguse makseviisi kasutamiseks; igal juhul ei kaasne Teile sellise maksete tagastamisega teenustasu ega muud kulu.',
      ],
    },
    {
      id: 'expiry',
      title: 'Millal taganemisõigus varem lõpeb',
      blocks: [
        '**Teie taganemisõigus lõpeb varem**, niipea kui oleme alustanud lepingu täitmist, see tähendab niipea, kui oleme hakanud teie faili valmistama, kui (1) andsite sõnaselge nõusoleku, et alustame täitmist enne taganemistähtaja lõppu, (2) kinnitasite, et olete teadlik, et kaotate sellega oma taganemisõiguse, kui oleme alustanud, ja (3) oleme seda teile kinnitanud püsival andmekandjal (teeme seda tellimuse kinnituskirjas, mis saadetakse välja enne alustamist). See tuleneb direktiivi 2011/83/EL artikli 16 punktist m (Eestis võlaõigusseaduse § 53 lõike 4 punkt 7¹).',
        'Enne maksmist annate selle nõusoleku, märkides selle kasti:',
        { box: [CHECKOUT_LEGAL_ET.withdrawalConsent], label: 'Märkeruut tellimisel' },
        'Praktikas lõpeb teie taganemisõigus seega hetkel, mil hakkame teie faili valmistama. Alustame alles pärast seda, kui tellimuse kinnituskiri on välja saadetud, tavaliselt minuti jooksul pärast makset, kui teie tellimuse leht on avatud: makseleht viib teid otse sinna. Kui te selleks ajaks oma tellimuse lehel ei ole, alustame siis, kui avate selle uuesti selles e-kirjas oleva tellimuse lehe lingi kaudu. Samas e-kirjas olev taganemislink avab teie tellimuse veebipõhise taganemisfunktsiooni, ilma et midagi käivitataks. Alates hetkest, mil alustame, on teie taganemisõigus lõppenud, isegi kui teie faili alles valmistatakse või see ootab meie kvaliteedikontrolli. Kui me ei ole teie faili valmistamist alustanud, lõpeb teie taganemisõigus 14-päevase taganemistähtaja möödumisel: makse tegemise päeva ei arvestata ning kui tähtaja viimane päev on laupäev, pühapäev või riigipüha, lõpeb tähtaeg järgmise tööpäeva lõpus. See ei mõjuta teie seadusest tulenevaid õigusi puudusega faili korral: vt meie müügitingimuste jaotist [Kaebused ja puudused](doc:terms#defects).',
      ],
    },
    {
      id: 'online',
      title: 'Taganemine veebis',
      blocks: [
        `Seni, kuni teie taganemisõigus kehtib, saate igal ajal taganeda veebis funktsiooniga [„${W.button}“](${withdrawFunctionHrefEt()}). Leiate selle meie avalehe ja õigusliku teabe lehtede jalusest, oma tellimuse lehelt ning tellimuse kinnituskirjas oleva taganemislingi tagant. See link avab funktsiooni teie tellimuse jaoks, ilma et midagi käivitataks. Tellimuse lehe enda avamine käivitab aga teie faili valmistamise, kui tellimuse kinnituskiri on välja saadetud, ja sellega lõpeb teie taganemisõigus (vt [Millal taganemisõigus varem lõpeb](#expiry)).`,
        `Kuidas see toimib: sisestage oma nimi, tellimuse number (see on juba täidetud, kui tulete oma tellimuse lehelt või taganemislingi kaudu) ja e-posti aadress kättesaamise kinnituse jaoks ning saatke seejärel oma taganemisavaldus nupuga „${W.confirm}“. Kui tulete ilma kummagi lingita, märkige palun e-posti aadress, millega maksite, et saaksime teie tellimuse üles leida. Kui andmed ei vasta ühelegi meie tellimusele, ütleb leht teile seda; säilitame teie avalduse siiski, kontrollime seda käsitsi ja saadame teile e-kirjaga kättesaamise kinnituse. Meie e-kirjade kuritarvitamise vältimiseks on kättesaamise kinnituste arv piiratud: avalduste puhul, mis ei vasta ühelegi meie tellimusele, kahe kinnitusega päevas ja nelja kinnitusega kuus samale aadressile; ühe tellimuse puhul kokku kolme kinnitusega aadressidele, mis erinevad maksmisel kasutatud aadressist (järgmised saadetakse aadressile, millega maksite); ning korduva avalduse puhul tellimuse kohta, millele oleme juba vastanud, ühe kinnitusega päevas selle tellimuse kohta ja viie kinnitusega päevas kõigi tellimuste kohta kokku. Kui leht ei saa teie avaldust vastu võtta, näiteks tehnilise rikke tõttu või seetõttu, et avaldusi saabub ebatavaliselt palju, ütleb leht teile seda: saatke meile siis palun oma taganemisavaldus e-kirjaga; e-kiri kehtib samamoodi.`,
        'Mis edasi saab: salvestame teie avalduse koos kuupäeva ja kellaajaga, mil see meieni jõudis. Kui teie tellimuse eest on makstud, me ei ole teie faili valmistamist alustanud ja 14-päevane taganemistähtaeg ei ole möödunud, jõustub teie taganemine: peatame teie tellimuse, nii et midagi ei valmistata, ja tagastame teile raha, nagu on kirjeldatud jaotises [Lepingust taganemise tagajärjed](#effects). Kui teie makse oli taganemise ajal veel töötlemisel, ei valmistata samuti midagi, ja kui makse meieni jõuab, tagastame selle täies ulatuses. Saadame teile viivitamata e-kirjaga kättesaamise kinnituse, mis sisaldab teie taganemisavalduse sisu ning selle kuupäeva ja kellaaega.',
        'Kui olime teie nõusolekul teie faili valmistamist juba alustanud või 14-päevane taganemistähtaeg oli möödunud, oli teie taganemisõigus juba lõppenud (vt [Millal taganemisõigus varem lõpeb](#expiry)): leht ja kättesaamise kinnitus ütlevad teile seda ning me vaatame teie avalduse siiski isiklikult üle. Kui teie tellimuse eest ei ole kunagi makstud, ei ole lepingut, millest taganeda: leht ütleb teile seda ja raha ei ole võetud. See ei mõjuta teie õigusi puudusega faili korral.',
      ],
    },
    {
      id: 'form',
      title: 'Taganemisavalduse tüüpvorm',
      blocks: [
        '(täitke ja tagastage käesolev vorm üksnes juhul, kui soovite lepingust taganeda)',
        {
          box: [
            `Kellele: ${formLineEt}`,
            'Käesolevaga taganen/taganeme (*) lepingust, mille esemeks on järgmine asi (*) / järgmine teenus (*)',
            'Tellimuse esitamise kuupäev (*) / asja kättesaamise kuupäev (*)',
            'Tarbija nimi / tarbijate nimed',
            'Tarbija aadress / tarbijate aadressid',
            'Tarbija allkiri / tarbijate allkirjad (ainult juhul, kui käesolev vorm esitatakse paberil)',
            'Kuupäev',
            '(*) Mittevajalik maha tõmmata.',
          ],
        },
        `E-posti teel saatke täidetud vorm või oma avaldus lihtsalt aadressile [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Lepingust%20taganemine). Kui teil on tellimuse number, lisage see palun. Veebis kasutage eespool kirjeldatud funktsiooni [„${W.button}“](${withdrawFunctionHrefEt()}).`,
      ],
    },
  ],
};
