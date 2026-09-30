// Elállási tájékoztató, the Hungarian ("hu") version of src/legal/docs/withdrawal.ts: the same section ids, the "Ön"
// register of the Hungarian statutory texts.
// The Hungarian model texts are NOT translated from English. They are taken word for word from 45/2014. (II. 26.)
// Korm. rendelet, in the version in force since 2026. IX. 27. (checked on 2026-09-29 against the official
// njt.jog.gov.hu and against net.jogtar.hu, identical):
//  - "right" and "effects": 1. melléklet (Elállási/Felmondási minta-tájékoztató), filled in for a contract without
//    goods: only the „elállás” alternatives of the "/" pairs; (1…) with text a) („a szerződés megkötésének napjától
//    számított 14 nap elteltével jár le”, as for the English "from the day of the conclusion of the contract");
//    (2…) with contactLineHu (name, postal address, email; the phone the útmutató asks for is left out by the owner's
//    decision, PHONE_OMITTED_BY_OWNER); (3…) with the first text, the one for an obligatory withdrawal function
//    (22. § (1a)-(1c)), its address being the function's address and button; (4…), (5…) and (6…) are for goods and
//    services and stay out. The model's sentence in (3…) sets off a clause with two en dashes; the owner's rule allows
//    no en or em dash in any text, so they are written as " - " (the only change to a model text; a Hungarian lawyer who wants the punctuation of the model may restore it).
//  - "form": 2. melléklet (Elállási-/Felmondásinyilatkozat-minta) word for word, its only alternatives kept as they
//    are, no line added, the "Címzett" line filled with formLineHu (name, postal address, email).
// The early end of the right (29. § (1) m)) is in "expiry", with the checkbox text of src/shared/legal.ts CHECKOUT_LEGAL.hu.
// What the server does and when the right ends: see the header of src/legal/docs/withdrawal.ts (the same rules;
// Hungarian public holidays are in api/_lib/withdraw_hu.py HOLIDAYS_HU). Not reviewed by a Hungarian lawyer.
import type { LegalDoc } from '../types';
import { CONTACT_EMAIL, contactLine, formLine } from '../facts';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE, withdrawFunctionAddress, withdrawFunctionHref } from '../../shared/legal';

const formLineHu = () => formLine('hu');
const contactLineHu = () => contactLine('hu');
const WITHDRAWAL_ONLINE_HU = WITHDRAWAL_ONLINE.hu;
const CHECKOUT_LEGAL_HU = CHECKOUT_LEGAL.hu;
const withdrawFunctionHrefHu = () => withdrawFunctionHref('hu');
const withdrawFunctionAddressHu = () => withdrawFunctionAddress('hu');

const W = WITHDRAWAL_ONLINE_HU;

export const hu: LegalDoc = {
  title: 'Elállási tájékoztató',
  description:
    'Elállási tájékoztató a SnapEyes digitális fájljaihoz: a 14 napos elállási jog, mikor szűnik meg korábban, és az elállásinyilatkozat-minta.',
  lead:
    'Az EU-ban a fogyasztókat az online vásárlásoknál elállási jog illeti meg. A miénkhez hasonló digitális fájl esetén ez korábban megszűnik, amint az Ön hozzájárulásával megkezdjük a fájl elkészítését. Alább a teljes tájékoztatót találja.',
  sections: [
    {
      id: 'right',
      title: 'Elállási jog',
      blocks: [
        'Ön 14 napon belül jogosult indokolás nélkül elállni e szerződéstől.',
        'Az elállási határidő a szerződés megkötésének napjától számított 14 nap elteltével jár le.',
        `Ha Ön elállási jogával élni kíván, elállási szándékát tartalmazó egyértelmű nyilatkozatát köteles eljuttatni (például postán vagy elektronikus úton küldött levél útján) az alábbi címre: ${contactLineHu()}. Ebből a célból felhasználhatja a mellékelt elállási nyilatkozat-mintát is. Az elállási jogát Ön online is gyakorolhatja a következő címen: [${withdrawFunctionAddressHu()}](${withdrawFunctionHrefHu()}) (az „${W.button}” gomb). Ha ezt az online funkciót veszi igénybe, az elállás megérkezését - az elállás tartalmát, valamint napját és időpontját is feltüntetve - tartós adathordozón (például elektronikus levélben) haladéktalanul visszaigazoljuk Önnek.`,
        'Ön határidőben gyakorolja elállási jogát, ha a fent megjelölt határidő lejárta előtt elküldi elállási nyilatkozatát.',
      ],
    },
    {
      id: 'effects',
      title: 'Az elállás joghatásai',
      blocks: [
        'Ha Ön eláll ettől a szerződéstől, haladéktalanul, de legkésőbb az Ön elállási nyilatkozatának kézhezvételétől számított 14 napon belül visszatérítjük az Ön által teljesített valamennyi ellenszolgáltatást, ideértve a fuvarozási költséget is (kivéve azokat a többletköltségeket, amelyek amiatt merültek fel, hogy Ön az általunk felkínált, legolcsóbb szokásos fuvarozási módtól eltérő fuvarozási módot választott.) A visszatérítés során az eredeti ügylet során alkalmazott fizetési móddal egyező fizetési módot alkalmazunk, kivéve, ha Ön más fizetési mód igénybevételéhez kifejezetten a hozzájárulását adja; e visszatérítési mód alkalmazásából kifolyólag Önt semmilyen többletköltség nem terheli.',
      ],
    },
    {
      id: 'expiry',
      title: 'Mikor szűnik meg korábban az elállási jog',
      blocks: [
        '**Az elállási joga korábban megszűnik**, amint megkezdtük a szerződés teljesítését, vagyis a fájl elkészítését, ha (1) Ön kifejezetten hozzájárult ahhoz, hogy a teljesítést az elállási határidő lejárta előtt megkezdjük, (2) egyúttal tudomásul vette, hogy a teljesítés megkezdését követően elveszíti az elállási jogát, és (3) ezt tartós adathordozón visszaigazoltuk Önnek (ezt a megrendelés visszaigazolását tartalmazó e-mailben tesszük meg, amely még a kezdés előtt elmegy). Ez a 45/2014. (II. 26.) Korm. rendelet 29. § (1) bekezdés m) pontjából és a 2011/83/EU irányelv 16. cikk m) pontjából következik.',
        'Fizetés előtt ezt a hozzájárulást ennek a négyzetnek a bejelölésével adja meg:',
        { box: [CHECKOUT_LEGAL_HU.withdrawalConsent], label: 'A jelölőnégyzet a megrendeléskor' },
        'A gyakorlatban ezért az elállási joga abban a pillanatban szűnik meg, amikor megkezdjük a fájl elkészítését. Ezt csak azután kezdjük meg, hogy elment a megrendelés visszaigazolását tartalmazó e-mail, ez általában a fizetés után egy percen belül megtörténik, amíg a rendelési oldala nyitva van: a fizetési oldal egyenesen oda vezeti. Ha addig nincs a rendelési oldalán, akkor kezdjük meg, amikor az e-mailben kapott, a rendelési oldalára vezető linkkel újra megnyitja. Ugyanebben az e-mailben az elállási link a megrendeléséhez nyitja meg az online elállási funkciót, anélkül, hogy bármit elindítana. A kezdés pillanatától az elállási joga megszűnt, akkor is, ha a fájl még készül, vagy a minőségellenőrzésünkre vár. Ha még nem kezdtük meg a fájl elkészítését, az elállási joga a 14 napos elállási határidő leteltével szűnik meg: a fizetés napja nem számít bele, és ha a határidő utolsó napja szombatra, vasárnapra vagy munkaszüneti napra esik, a határidő a következő munkanap végén jár le. Hibás fájl esetén a jogszabályon alapuló jogait ez nem érinti: lásd az ÁSZF [Kellékszavatosság és hibás teljesítés](doc:terms#defects) pontját.',
      ],
    },
    {
      id: 'online',
      title: 'Online elállás',
      blocks: [
        `Amíg az elállási joga fennáll, bármikor elállhat online, az [„${W.button}”](${withdrawFunctionHrefHu()}) funkcióval. Megtalálja a kezdőlapunk és a jogi oldalaink alján, a rendelési oldalán, valamint a megrendelés visszaigazolását tartalmazó e-mailben kapott elállási link mögött. Ez a link a megrendeléséhez nyitja meg a funkciót, anélkül, hogy bármit elindítana. Maga a rendelési oldal megnyitása viszont elindítja a fájl elkészítését, amint elment a visszaigazoló e-mail, és ezzel megszűnik az elállási joga (lásd: [Mikor szűnik meg korábban az elállási jog](#expiry)).`,
        `Így működik: adja meg a nevét, a rendelésszámát (ez már ki van töltve, ha a rendelési oldaláról vagy az elállási linkről érkezik) és azt az e-mail-címet, ahová az átvételi elismervényt kéri, majd küldje el az elállását az „${W.confirm}” gombbal. Ha nem e linkek valamelyikén keresztül érkezik, kérjük, azt az e-mail-címet adja meg, amellyel fizetett, hogy a megrendeléséhez tudjuk rendelni. Ha az adatok egyik megrendelésünkkel sem egyeznek, az oldal ezt jelzi; a nyilatkozatát ennek ellenére megőrizzük, kézzel ellenőrizzük, és e-mailben átvételi elismervényt küldünk. Hogy e-mailjeinkkel ne lehessen visszaélni, az átvételi elismervények száma korlátozott: az egyik megrendelésünkkel sem egyező nyilatkozatoknál ugyanarra a címre naponta kettő és havonta négy; egy megrendeléshez összesen három mehet más címre, mint amellyel fizettek (a továbbiak arra a címre mennek, amellyel Ön fizetett); egy már megválaszolt megrendelésről ismételten küldött nyilatkozatnál pedig az adott megrendeléshez naponta egy, az összes megrendeléshez együtt naponta öt. Ha az oldal nem tudja fogadni a nyilatkozatát, például műszaki hiba miatt vagy mert szokatlanul sok nyilatkozat érkezik, ezt jelzi: ilyenkor kérjük, e-mailben küldje el nekünk az elállását; az e-mail ugyanolyan érvényes.`,
        'Mi történik ezután: a nyilatkozatát a beérkezés dátumával és időpontjával rögzítjük. Ha a megrendelése ki van fizetve, még nem kezdtük meg a fájl elkészítését, és a 14 napos elállási határidő nem járt le, az elállása hatályos: leállítjuk a megrendelést, így semmi nem készül el, és a kifizetett összeget visszatérítjük (lásd: [Az elállás joghatásai](#effects)). Ha az elálláskor a fizetése még feldolgozás alatt állt, szintén semmi nem készül el, és ha a fizetés megérkezik hozzánk, teljes egészében visszatérítjük. Indokolatlan késedelem nélkül e-mailben átvételi elismervényt küldünk Önnek az elállás tartalmával, valamint napjával és időpontjával.',
        'Ha az Ön hozzájárulásával már megkezdtük a fájl elkészítését, vagy a 14 napos elállási határidő lejárt, az elállási joga már megszűnt (lásd: [Mikor szűnik meg korábban az elállási jog](#expiry)): az oldal és az átvételi elismervény ezt közli Önnel, a nyilatkozatát pedig ennek ellenére személyesen is megnézzük. Ha a megrendelést soha nem fizették ki, nincs szerződés, amelytől el lehetne állni: az oldal ezt jelzi, és terhelés nem történt. Hibás fájl esetén az Önt megillető jogokat ez nem érinti.',
      ],
    },
    {
      id: 'form',
      title: 'Elállásinyilatkozat-minta',
      blocks: [
        '(csak a szerződéstől való elállási szándék esetén töltse ki és juttassa vissza)',
        {
          box: [
            `Címzett: ${formLineHu()}`,
            'Alulírott(ak) kijelenti(k), hogy gyakorlom/gyakoroljuk elállási/felmondási jogomat/jogunkat az alábbi áru(k) adásvételére vagy az alábbi szolgáltatás nyújtására irányuló szerződés tekintetében:',
            'Szerződéskötés időpontja/átvétel időpontja:',
            'Fogyasztó(k) neve:',
            'Fogyasztó(k) címe:',
            'A fogyasztó(k) aláírása (kizárólag papír alapon tett nyilatkozat esetén):',
            'Kelt',
          ],
        },
        `E-mailben egyszerűen küldje el a kitöltött nyilatkozatmintát vagy a saját nyilatkozatát az [${CONTACT_EMAIL}](mailto:${CONTACT_EMAIL}?subject=El%C3%A1ll%C3%A1s) címre. Ha megvan, kérjük, adja meg a rendelésszámát is. Online használja a fent leírt [„${W.button}”](${withdrawFunctionHrefHu()}) funkciót.`,
      ],
    },
  ],
};
