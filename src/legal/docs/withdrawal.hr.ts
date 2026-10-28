// Pravo na jednostrani raskid ugovora: the Croatian twin of `en` in src/legal/docs/withdrawal.ts, same section ids and
// blocks in the same order. Every rule of the English header (when the right ends, as api/_lib/withdraw.py decides it;
// the online function; the receipts and their limits) holds here word for word in meaning.
//
// Croatian law calls the right of withdrawal "pravo na jednostrani raskid ugovora" (Zakon o zaštiti potrošača, NN 19/22,
// 59/23, 59/26, čl. 79.-86.), not "odustajanje" as the Croatian text of Directive 2011/83/EU does, so every text here
// uses the Act's words. The statutory parts are the Croatian national model, which transposes Annex I of Directive
// 2011/83/EU and Directive (EU) 2023/2673: Pravilnik o sadržaju i obliku obavijesti o pravu potrošača na jednostrani
// raskid ugovora sklopljenih na daljinu i ugovora sklopljenih izvan poslovnih prostorija, NN 105/2026 (in force since
// 2026-09-26; it replaced NN 117/22), Prilog I, checked 2026-10-28 against narodne-novine.nn.hr. Kept word for word
// (including its capitals "Vas", "Vi", "Ugovor"; our own sentences use the lower-case "vi" of the site):
//  - "right": I.1, the period sentence with option (d) "sklapanja ugovora" (digital content not supplied on a tangible
//    medium), and the sentence on how to withdraw, in which two things are changed: the seller's details are inserted
//    after "morate nas" as the EU model's [2] asks (contactLineHr: name, address, email, and the phone once the owner
//    shows one; the owner decided to show none, PHONE_OMITTED_BY_OWNER), and the model's inner reference "iz dijela II
//    ovoga Priloga" (to the Pravilnik's own annex) is left out, since the form is on this page. Then the Pravilnik's
//    sentence for an obligatory online function (after Part II), with the address and the button inserted where it
//    says "[unijeti mrežnu adresu ...]". The last paragraph is the EU model's deadline sentence, which the national model
//    lacks, in the Act's words (čl. 81. st. 4. and čl. 81.a st. 7.: sending the statement before the period ends is
//    enough).
//  - "effects": I.2, its two sentences for a contract without goods (the goods sentence is left out, as the EU model's
//    instruction 4 is). Delivery costs do not exist here, but the clause stays: it is the unchanged model.
//  - "form": II, "Primjerak obrasca o jednostranom raskidu", word for word, its "Prima" line filled with formLineHr. One
//    typographic change: the model starts its last two lines with an en dash; here it is a hyphen (owner rule: no en or
//    em dashes anywhere). The opening line in brackets is ours (the national form has none).
// The online function's labels are the Act's, čl. 81.a st. 2. and 5. ("raskid ugovora", "potvrditi raskid ugovora"),
// held in src/shared/legal.ts WITHDRAWAL_ONLINE.hr. The early end for digital content is čl. 86. st. 1. t. 13.
// Not reviewed by a lawyer.
import type { LegalDoc } from '../types';
import { CONTACT_EMAIL, contactLine, formLine } from '../facts';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';

const formLineHr = formLine('hr');
const contactLineHr = contactLine('hr');
const WITHDRAWAL_ONLINE_HR = WITHDRAWAL_ONLINE.hr;
const CHECKOUT_LEGAL_HR = CHECKOUT_LEGAL.hr;
const withdrawFunctionHrefHr = () => withdrawFunctionHref('hr');
const withdrawFunctionAddressHr = () => withdrawFunctionAddress('hr');

const W = WITHDRAWAL_ONLINE_HR;

export const hr: LegalDoc = {
  title: 'Pravo na jednostrani raskid ugovora',
  description:
    'Informacije o pravu na jednostrani raskid ugovora za digitalne datoteke SnapEyes: pravo na jednostrani raskid u roku od 14 dana, kada ranije prestaje i primjerak obrasca o jednostranom raskidu.',
  lead:
    'Potrošači u EU-u imaju pravo na jednostrani raskid ugovora sklopljenog putem interneta. Kod digitalne datoteke kao što je naša to pravo prestaje ranije, čim uz vaš pristanak počnemo izrađivati vašu datoteku. Ovdje su sve informacije.',
  sections: [
    {
      id: 'right',
      title: 'Pravo na jednostrani raskid ugovora',
      blocks: [
        'Ugovor možete jednostrano raskinuti u roku od 14 dana bez navođenja razloga.',
        'Rok za jednostrani raskid iznosi 14 dana od dana sklapanja ugovora.',
        `Da biste mogli ostvariti pravo na jednostrani raskid ovoga Ugovora, morate nas (${contactLineHr}) obavijestiti o svojoj odluci o jednostranom raskidu ugovora prije isteka roka i to nedvosmislenom izjavom poslanom poštom, ili elektroničkom poštom, u kojoj ćete navesti svoje ime i prezime, adresu, broj telefona, ili adresu elektroničke pošte, a možete koristiti i priloženi primjer obrasca za jednostrani raskid ugovora. Pravo na jednostrani raskid ugovora možete ostvariti i mrežnim putem na [${withdrawFunctionAddressHr()}](${withdrawFunctionHrefHr()}) (gumb „${W.button}“). Ako upotrijebite opisanu mrežnu funkciju, poslat ćemo vam bez odgađanja potvrdu o zaprimanju Vaše izjave o jednostranom raskidu ugovora na trajnom mediju (npr. e-poštom), uključujući njezin sadržaj te datum i vrijeme podnošenja.`,
        'Da bi rok za jednostrani raskid bio poštovan, dovoljno je da nam izjavu o ostvarivanju prava na jednostrani raskid ugovora pošaljete prije isteka roka za jednostrani raskid.',
      ],
    },
    {
      id: 'effects',
      title: 'Učinci jednostranog raskida ugovora',
      blocks: [
        'Ako jednostrano raskinete ovaj Ugovor, izvršit ćemo povrat novca koji smo od Vas primili, uključujući i troškove isporuke, bez odgađanja, a najkasnije u roku od 14 dana od dana kada smo zaprimili Vašu odluku o jednostranom raskidu ugovora, osim ukoliko ste odabrali drugu vrstu isporuke a koja nije najjeftinija standardna isporuka koju smo mi ponudili. Povrat novca bit će izvršen na isti način na koji ste Vi izvršili uplatu. U slučaju da pristajete na drugi način povrata plaćenog iznosa, ne snosite nikakve troškove u odnosu na povrat.',
      ],
    },
    {
      id: 'expiry',
      title: 'Kada pravo na jednostrani raskid prestaje ranije',
      blocks: [
        '**Vaše pravo na jednostrani raskid ugovora prestaje ranije**, čim započnemo s ispunjenjem ugovora, odnosno čim počnemo izrađivati vašu datoteku, ako su ispunjena tri uvjeta: (1) izričito ste pristali da s ispunjenjem ugovora započnemo prije isteka roka za jednostrani raskid, (2) potvrdili ste da ste upoznati s time da tako gubite pravo na jednostrani raskid ugovora čim započnemo i (3) mi smo vam to potvrdili na trajnom mediju (to činimo u e-poruci s potvrdom narudžbe, koja se šalje prije nego što započnemo). To proizlazi iz članka 86. stavka 1. točke 13. Zakona o zaštiti potrošača i članka 16. točke (m) Direktive 2011/83/EU.',
        'Prije plaćanja taj pristanak dajete označavanjem ovog polja:',
        { box: [CHECKOUT_LEGAL_HR.withdrawalConsent], label: 'Polje za označavanje pri narudžbi' },
        'U praksi vaše pravo na jednostrani raskid ugovora stoga prestaje u trenutku kada počnemo izrađivati vašu datoteku. Počinjemo tek nakon što je poslana e-poruka s potvrdom narudžbe, obično u roku od minute nakon plaćanja, dok je vaša stranica narudžbe otvorena: stranica za plaćanje vodi vas izravno onamo. Ako do tada niste na svojoj stranici narudžbe, počinjemo kada je ponovno otvorite putem poveznice na stranicu narudžbe iz te e-poruke. Poveznica za raskid u istoj e-poruci otvara mrežnu funkciju za jednostrani raskid vaše narudžbe, a da ništa ne pokreće. Od trenutka kada započnemo, vaše pravo na jednostrani raskid je prestalo, čak i dok se vaša datoteka još izrađuje ili čeka našu provjeru kvalitete. Ako još nismo počeli izrađivati vašu datoteku, vaše pravo na jednostrani raskid prestaje istekom roka od 14 dana za jednostrani raskid: dan vašeg plaćanja ne računa se, a ako posljednji dan roka pada u subotu, nedjelju ili na državni praznik, rok istječe na kraju sljedećeg radnog dana. To ne utječe na vaša zakonska prava ako je datoteka neispravna: pogledajte odjeljak [Prigovori i nedostaci](doc:terms#defects) naših općih uvjeta prodaje.',
      ],
    },
    {
      id: 'online',
      title: 'Jednostrani raskid putem interneta',
      blocks: [
        `Dok traje vaše pravo na jednostrani raskid, ugovor u bilo kojem trenutku možete raskinuti putem interneta, funkcijom [„${W.button}“](${withdrawFunctionHrefHr()}). Nalazi se na dnu naše početne stranice i naših stranica s pravnim informacijama, na vašoj stranici narudžbe i iza poveznice za raskid u e-poruci s potvrdom narudžbe. Ta poveznica otvara funkciju za vašu narudžbu, a da ništa ne pokreće. Samo otvaranje vaše stranice narudžbe, naprotiv, pokreće izradu vaše datoteke čim je poslana e-poruka s potvrdom narudžbe, a time prestaje vaše pravo na jednostrani raskid (pogledajte [Kada pravo na jednostrani raskid prestaje ranije](#expiry)).`,
        `Kako to funkcionira: upišite svoje ime, broj narudžbe (već je upisan ako dolazite sa svoje stranice narudžbe ili putem poveznice za raskid) i adresu e-pošte za potvrdu primitka, a zatim pošaljite svoju izjavu o raskidu gumbom „${W.confirm}“. Ako dolazite bez neke od tih poveznica, navedite adresu e-pošte koju ste naveli pri plaćanju, kako bismo mogli pronaći vašu narudžbu. Ako se podaci ne podudaraju ni s jednom našom narudžbom, stranica će vam to reći; vašu izjavu ipak čuvamo, ručno je provjeravamo i e-poštom vam šaljemo potvrdu primitka. Kako bismo spriječili zlouporabu naših e-poruka, broj potvrda primitka je ograničen: za izjave koje se ne podudaraju ni s jednom našom narudžbom, na dvije dnevno i četiri mjesečno na istu adresu; za jednu narudžbu, na ukupno tri na adrese različite od one koja je navedena pri plaćanju (daljnje se šalju na adresu koju ste naveli pri plaćanju); a za ponovljenu izjavu o narudžbi na koju smo već odgovorili, na jednu dnevno za tu narudžbu i pet dnevno za sve narudžbe zajedno. Ako stranica ne može primiti vašu izjavu, primjerice zbog tehničke pogreške ili zato što stiže neuobičajeno mnogo izjava, reći će vam to: tada nam izjavu o raskidu pošaljite e-poštom; e-poruka vrijedi jednako.`,
        'Što se zatim događa: vašu izjavu bilježimo s datumom i vremenom kada nam je stigla. Ako je vaša narudžba plaćena, još nismo počeli izrađivati vašu datoteku i rok od 14 dana za jednostrani raskid nije istekao, vaš raskid proizvodi učinak: zaustavljamo vašu narudžbu, tako da se ništa ne izrađuje, i vraćamo vam novac kako je opisano u odjeljku [Učinci jednostranog raskida ugovora](#effects). Ako se vaše plaćanje još obrađivalo kada ste raskinuli ugovor, također se ništa ne izrađuje, a ako plaćanje stigne do nas, vraćamo ga u cijelosti. Bez odgađanja e-poštom vam šaljemo potvrdu primitka sa sadržajem vašeg raskida te njegovim datumom i vremenom.',
        'Ako smo uz vaš pristanak već počeli izrađivati vašu datoteku ili je rok od 14 dana za jednostrani raskid istekao, vaše je pravo na jednostrani raskid već prestalo (pogledajte [Kada pravo na jednostrani raskid prestaje ranije](#expiry)): stranica i potvrda primitka to će vam reći, a vašu izjavu svejedno osobno pregledavamo. Ako vaša narudžba nikada nije plaćena, nema ugovora koji biste mogli raskinuti: stranica će vam to reći i ništa nije naplaćeno. To ne utječe na vaša prava ako je datoteka neispravna.',
      ],
    },
    {
      id: 'form',
      title: 'Primjerak obrasca o jednostranom raskidu',
      blocks: [
        '(Ovaj obrazac ispunite i pošaljite nam samo ako želite jednostrano raskinuti ugovor.)',
        {
          box: [
            '1. Ime, prezime i adresa potrošača __________________________.',
            `2. Prima: ${formLineHr}`,
            '3. Ja ________________________________ ovim izjavljujem da jednostrano raskidam Ugovor o prodaji sljedeće robe/za pružanje sljedeće usluge (odabrati) ______________________________, naručene/primljene dana ______________________________.',
            '- potpis potrošača (samo ako se ovaj obrazac ispunjava na papiru),',
            '- datum.',
          ],
        },
        `E-poštom jednostavno pošaljite ispunjeni obrazac ili vlastitu izjavu na [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=Jednostrani%20raskid%20ugovora). Ako imate broj narudžbe, navedite ga. Putem interneta koristite se gore opisanom funkcijom [„${W.button}“](${withdrawFunctionHrefHr()}).`,
      ],
    },
  ],
};
