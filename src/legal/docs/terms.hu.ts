// Általános Szerződési Feltételek (ÁSZF), the Hungarian ("hu") version of src/legal/docs/terms.ts: the same section
// ids (links such as doc:terms#defects survive a language switch), in the neutral / "Ön" register Hungarian webshops
// use for their ÁSZF. Prices, seller and contact come from src/landing/config.ts through src/legal/facts.ts; the forint
// prices are the "hu" market's (HU_PRICES, from api/_lib/markets.py).
// Beyond the English text, and for the same reason the English follows the EU rules, this version names what the
// pre-contract information of 45/2014. (II. 26.) Korm. rendelet 11. § (1) asks for and a Hungarian reader looks for:
//  - the buy button's label „Megrendelés fizetési kötelezettséggel” (the wording of the owner's Hungarian launch plan, an "equivalent,
//    unambiguous" label under 15. § (2); the decree's own words are „fizetési kötelezettséggel járó megrendelés”) in
//    "contract", which describes that button and Stripe's pay button in that order; the decree's own words also
//    stand right above Stripe's pay button (api/_lib/pay_hu.py SUBMIT_NOTE_HU), the click that binds (where the order
//    becomes binding is a point for the Hungarian legal reviewer);
//  - the functionality and compatibility of the file and that it has no technical protection (11. § (1) t), u));
//  - kellékszavatosság for digital content in the words of the Ptk. and of 373/2021. (VI. 30.) Korm. rendelet
//    (one-off supply: liability for a defect existing at supply, a defect found within one year presumed to have
//    existed then (21. § (3)), the consumer's duty to cooperate when the cause may be their own digital environment
//    (21. § (6)-(7)), two-month notice, two-year limitation), and that there is no voluntary guarantee (jótállás);
//  - complaint handling (panaszkezelés, 11. § (1) h)), the out-of-court body with its name and postal address (w)),
//    the European Consumer Centre Hungary for cross-border help, and that no code of conduct applies (o)).
// NOT added: the EU ODR link (the platform closed on 20 July 2025), a VAT number (the MB is not VAT-registered),
// any promise the code does not keep. The seller line has no phone: owner decision (PHONE_OMITTED_BY_OWNER); the
// decree lists a phone among the seller's details (11. § (1) c)), a risk the owner accepted for every language.
// Not reviewed by a Hungarian lawyer.
import type { LegalDoc, LegalSection } from '../types';
import { DELIVERY_MAX_HOURS, HU_PRICES, MAIL, MAX_EYES, PRICE_CENTS, SELLER, address, company, eur, huf, phoneSuffix, representedSuffix } from '../facts';
import { CHECKOUT_LEGAL, WITHDRAWAL_ONLINE } from '../../shared/legal';

const companyHu = () => company('hu');
const addressHu = () => address('hu');
const phoneSuffixHu = () => phoneSuffix('hu');
const representedSuffixHu = () => representedSuffix('hu');
const WITHDRAWAL_ONLINE_HU = WITHDRAWAL_ONLINE.hu;
const CHECKOUT_LEGAL_HU = CHECKOUT_LEGAL.hu;

// src/landing/copy.hu.ts TRANSPARENCY_HU in the ÁSZF's "Ön" register (terms.ts repeats the English sentence; the
// Hungarian site sentence says "te", which an ÁSZF does not)
const TRANSPARENCY_HU_ON =
  'A szín az Ön saját fotójából származik. Ahol a telefonja nem tudta rögzíteni a legfinomabb rostokat, ott a mesterséges intelligenciánk állítja helyre őket.';
const ART = 'Celestial Gold, Deep Nebula, Emerald Aurora, Obsidian Smoke, Supernova';
const PX = '4096 px';
const SQUARE = '4096 × 4096 px';

export const hu: LegalDoc = {
  title: 'Általános Szerződési Feltételek (ÁSZF)',
  description:
    'A SnapEyes digitális íriszalkotásának megrendelési feltételei: a termék, az árak, a fizetés, a teljesítés, a felhasználási jog, az elállási jog, a panaszkezelés és a kellékszavatosság.',
  lead: 'Ezek a feltételek a snapeyes.com oldalon leadott minden megrendelésre vonatkoznak. Kérjük, rendelés előtt olvassa el őket. Az ingyenes előnézet semmilyen kötelezettséggel nem jár.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'parties',
      title: 'Kivel köt szerződést',
      blocks: [
        `Szerződése az ${companyHu()} vállalkozással jön létre, amely litván jog szerinti kis társaság (mažoji bendrija)${representedSuffixHu()}; cégazonosító szám: ${SELLER.code}, székhely: ${addressHu()}, e-mail: ${MAIL}${phoneSuffixHu()} (a továbbiakban: „mi”, „SnapEyes”). Minden adatunkat megtalálja az [Impresszumban](doc:imprint).`,
        'Ajánlatunk fogyasztóknak szól. Ha Ön még nem töltötte be a 18. életévét, kérje meg a szülőjét vagy a gondviselőjét, hogy rendeljen Ön helyett.',
      ],
    },
    {
      id: 'product',
      title: 'Mit vásárol',
      blocks: [
        `Egy személyre szabott digitális alkotást, amely az Ön által egy szemről (vagy több szemről) készített fotóból készül, az Ön által választott stílusban, elrendezésben és felirattal. Egy vízjel nélküli képfájlt (JPEG) kap: egy szem esetén ${SQUARE}, több szem esetén a hosszabbik oldalán ${PX} méretben. Az alkotást kizárólag digitális fájlként, letöltéssel szolgáltatjuk. Nyomatot, keretet vagy más fizikai terméket nem árusítunk.`,
        `${TRANSPARENCY_HU_ON} Az alkotás ezért művészi helyreállítás, nem orvosi, nem mikroszkópos és nem stúdiós makrofelvétel, és nem alkalmas sem orvosi célra, sem személyek azonosítására.`,
        'A fájl szabványos JPEG kép, amely bármely szokásos számítógépen, telefonon vagy táblagépen megnyitható és kinyomtatható; külön program nem kell hozzá. Nem tartalmaz másolásvédelmet vagy más műszaki védelmi intézkedést, és frissítést nem igényel.',
      ],
    },
    {
      id: 'preview',
      title: 'Az előnézet és a fájl',
      blocks: [
        'Rendelés előtt egy ingyenes, vízjeles előnézetet lát, és azt jóváhagyja. A fájl a jóváhagyott előnézetet követi: ugyanaz a szem, stílus, elrendezés és felirat, ugyanazzal a színnel és tónussal, egyszer, teljes felbontásban elkészítve. Teljes méretben a mesterséges intelligenciánk hozzáadja azokat a finom rostrészleteket, amelyeket az előnézet a kis mérete miatt nem tud megmutatni, ezért a legapróbb részletek kissé eltérhetnek az előnézettől.',
        'Ha a fájl egyértelműen eltér a jóváhagyott előnézettől (például a színben, a világosságban vagy a pupillában), az hibás teljesítés: lásd a [Kellékszavatosság és hibás teljesítés](#defects) pontot.',
      ],
    },
    {
      id: 'contract',
      title: 'Hogyan jön létre a szerződés',
      blocks: [
        `A weboldalunkon látható előnézetek és árak még nem kötelező erejű ajánlatok. Fizetés előtt ellenőrizheti a szemeket, a stílust, az elrendezést és a feliratot, és bármely adatot kijavíthat, ha visszalép vagy újrafotóz egy szemet. Ezután a „${CHECKOUT_LEGAL_HU.continueButton}” gombbal a fizetési szolgáltatónk, a Stripe fizetési oldalára lép. Ott megadja e-mail-címét és fizetési adatait, és kijavíthatja azokat. Kötelező erejű megrendelését akkor adja le, amikor ott a fizetési gombbal jóváhagyja a fizetést; a megrendelés fizetési kötelezettséggel jár.`,
        'A szerződés akkor jön létre, amikor a fizetését megerősítették. Ekkor megnyílik a rendelési oldala, és e-mailben, a megrendelés visszaigazolásával együtt elküldjük Önnek a linkjét. A fájl elkészítését ott akkor kezdjük meg, amikor ez az e-mail elment.',
        'A szerződés nyelve magyar, angol, német vagy litván: az, amelyiken Ön megrendel.',
        'A megrendelését a szerződés adataival együtt tároljuk: a megrendelt alkotás, az ár, a dátum, az e-mail-címe és az azonnali kezdéshez adott hozzájárulása. A rendelési oldala addig mutatja ezeket az adatokat, ameddig a megrendelését megőrizzük. E feltételekről nem őrzünk külön példányt minden megrendeléshez. Ehelyett a megrendelés visszaigazolását tartalmazó e-mail szövegként tartalmazza a rendelés adatait, ezeket a feltételeket és az elállási tájékoztatót az elállásinyilatkozat-mintával, a megrendeléskor hatályos változatban: kérjük, őrizze meg ezt az e-mailt. Ezt az oldalt is bármikor elmentheti vagy kinyomtathatja.',
      ],
    },
    {
      id: 'prices',
      title: 'Árak és fizetés',
      blocks: [
        {
          dl: [
            ['Egy szem, Studio Black', eur(PRICE_CENTS.studioBlack, 'hu')],
            ['Egy szem művészi háttérrel', `${eur(PRICE_CENTS.artBackground, 'hu')} (${ART})`],
            ['Két szem (Couple Duo), bármely stílusban', eur(PRICE_CENTS.coupleDuo, 'hu')],
            ['Minden további szem', `+${eur(PRICE_CENTS.extraEye, 'hu')}, legfeljebb ${MAX_EYES} szem egy alkotáson`],
          ],
        },
        'Minden ár euróban értendő végső ár, amely minden adót és díjat tartalmaz. Nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel és nem tüntetünk fel. Szállítási költség nincs.',
        'Előre fizet, a fizetési szolgáltatónkon, a Stripe-on keresztül, a fizetési oldalon feltüntetett fizetési módok egyikével.',
      ],
    },
    {
      id: 'delivery',
      title: 'Teljesítés',
      blocks: [
        `A rendelési oldala akkor készíti el a fájlt, amikor elment a megrendelés visszaigazolását tartalmazó e-mail, ez általában a fizetés után egy percen belül megtörténik; az elkészítés rendszerint néhány percig tart (szemenként kb. fél percig). Ha a fájl elkészülte előtt bezárja az oldalt, az elkészítés folytatódik, amikor az e-mailben kapott linkkel újra megnyitja. Ha az automatikus minőségellenőrzésünk megjelöl egy fájlt, azt átadás előtt magunk is megnézzük, és e-mailt küldünk, amikor elkészült. **A fájl legkésőbb a fizetés megerősítését követő ${DELIVERY_MAX_HOURS} órán belül letölthető a rendelési oldalán.** A rendelési oldaláról a fájlt addig töltheti le bármikor, ameddig megőrizzük: a fizetéstől számított 12 hónapig (lásd az [Adatkezelési tájékoztatót](doc:privacy)). Az oldal által létrehozott minden letöltési link 7 napig érvényes; az oldal minden megnyitáskor újat készít. Ha az e-mail elveszett, írjon nekünk.`,
        'A rendelési oldal linkje egy privát kulcsot tartalmaz: aki ismeri, letöltheti az alkotását, ezért kérjük, ne adja tovább. Kérjük, töltse le a fájlt, és őrizzen meg róla egy másolatot. 12 hónap elteltével töröljük, és utána nem állítható helyre.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Elállási jog',
      blocks: [
        `Fogyasztóként főszabály szerint 14 napos elállási jog illeti meg. Digitális fájl esetén ez korábban megszűnik: fizetés előtt arra kérjük, hogy járuljon hozzá, hogy a fájl elkészítését még az elállási határidő lejárta előtt azonnal megkezdjük, és erősítse meg, hogy tudomásul veszi: a teljesítés megkezdését követően elveszíti az elállási jogát. Az elállási jog ezért megszűnik, amint megkezdtük a fájl elkészítését (a szerződés teljesítését); ezt csak azután kezdjük meg, hogy elment a megrendelés visszaigazolását tartalmazó e-mail, ez általában a fizetés után egy percen belül megtörténik, amíg a rendelési oldala nyitva van. Ez akkor is így van, ha a fájl még készül, vagy a minőségellenőrzésünkre vár. Ha még nem kezdtük meg, az elállási jog a 14 napos elállási határidő leteltével szűnik meg: a fizetés napja nem számít bele, és ha a határidő utolsó napja szombatra, vasárnapra vagy munkaszüneti napra esik, a határidő a következő munkanap végén jár le. Amíg az elállási joga fennáll, e-mailben, postai úton vagy online, az „${WITHDRAWAL_ONLINE_HU.button}” gombbal állhat el; a visszaigazoló e-mailben kapott elállási link ezt a funkciót a megrendeléséhez nyitja meg anélkül, hogy megkezdenénk a fájl elkészítését. A teljes tájékoztatót, az online funkciót és az elállásinyilatkozat-mintát az [Elállási tájékoztató](doc:withdrawal) oldalunkon találja.`,
      ],
    },
    {
      id: 'photos',
      title: 'Az Ön fotói',
      blocks: [
        'Csak a saját szeméről töltsön fel fotót, vagy olyan személy szeméről, aki ehhez hozzájárult (gyermek esetén a szülő vagy a gondviselő). A feltöltéssel megerősíti, hogy a fotót erre a célra felhasználhatja.',
        'A fotóhoz fűződő jogok Önnél maradnak. Kizárólag az előnézet és az alkotás elkészítéséhez használjuk, az [Adatkezelési tájékoztatóban](doc:privacy) leírtak szerint.',
        'Megtagadhatunk egy megrendelést, és a már kifizetett összeget teljes egészében visszatérítjük, ha egy fotó nyilvánvalóan sérti ezeket a szabályokat.',
      ],
    },
    {
      id: 'licence',
      title: 'Mit tehet az alkotásával',
      blocks: [
        'Nem kizárólagos, időben korlátlan felhasználási jogot kap az alkotásához, személyes, nem kereskedelmi célra. Például kinyomtathatja magának (otthon vagy nyomdában), bekeretezheti, ajándékba adhatja, háttérképként használhatja az eszközein, és megoszthatja a személyes közösségimédia-oldalain.',
        'Engedélyünk nélkül (egy e-mail elég) nem adhatja el az alkotást vagy az abból készült termékeket, harmadik személynek nem adhat hozzá felhasználási jogot, és nem használhatja reklámra vagy más kereskedelmi célra.',
        'A stílusok, a hátterek, az elrendezések és a SnapEyes arculata a miénk maradnak, a hozzájuk fűződő esetleges szerzői jogokkal együtt. Ugyanez vonatkozik a vízjeles előnézetekre.',
      ],
    },
    {
      id: 'defects',
      title: 'Kellékszavatosság és hibás teljesítés',
      blocks: [
        `A nem szerződésszerű digitális tartalomra vonatkozó, jogszabályon alapuló jogai teljes körűen megilletik. Ha a fájl hibás, például nem tölthető le vagy nem nyitható meg, sérült, kisebb a vállaltnál, vagy egyértelműen eltér a jóváhagyott előnézettől, kérjük, írjon a rendelésszámával az ${MAIL} címre. A fájlt díjmentesen újra elkészítjük, vagy ha ez nem szünteti meg a hibát, visszatérítjük az árát.`,
        'Mivel a fájlt egyszer szolgáltatjuk, azért a hibáért felelünk, amely a szolgáltatás időpontjában fennáll. Az ellenkező bizonyításáig vélelmezni kell, hogy a szolgáltatástól számított egy éven belül felismert hiba már a szolgáltatáskor is megvolt (373/2021. (VI. 30.) Korm. rendelet 21. § (3) bekezdés). Kellékszavatossági jogai alapján kérheti a fájl szerződésszerűvé tételét (nálunk: díjmentes újbóli elkészítését). Az ár arányos leszállítását kérheti, vagy megszüntetheti a szerződést, ha a szerződésszerűvé tétel lehetetlen, vagy az nekünk aránytalan többletköltséget okozna; ha azt a hiba közlésétől számított észszerű időn belül nem végezzük el; ha a hiba ismételten jelentkezik, annak ellenére, hogy megkíséreltük a fájl szerződésszerűvé tételét; ha a hiba olyan súlyú, hogy azonnali árleszállítást vagy a szerződés azonnali megszüntetését teszi indokolttá; vagy ha nem vállaljuk a fájl szerződésszerűvé tételét, illetve a körülményekből nyilvánvaló, hogy azt észszerű határidőn belül vagy az Önnek okozott jelentős érdeksérelem nélkül nem fogjuk elvégezni. A szerződés megszüntetésekor a kifizetett összeget, árleszállításkor a különbözetet legkésőbb 14 napon belül visszatérítjük.',
        'Kérjük, a hibát felfedezése után haladéktalanul közölje velünk; a felfedezéstől számított két hónapon belül közölt hibát késedelem nélkül közöltnek kell tekinteni. A teljesítéstől számított két év elteltével kellékszavatossági igényét már nem érvényesítheti.',
        'Ha a fájl az Ön eszközén nem nyílik meg, kérjük, működjön együtt velünk annak megállapításában, hogy a hiba oka az Ön digitális környezete-e: írja meg, milyen eszközzel és programmal próbálta megnyitni. Ennél többet nem kérünk.',
        'Termékszavatosság csak ingó dologra (termékre) vonatkozik, digitális fájlra nem. Önkéntes jótállást nem vállalunk; ez a jogszabályon alapuló jogait nem érinti.',
      ],
    },
    {
      id: 'liability',
      title: 'Felelősség',
      blocks: [
        'Korlátozás nélkül felelünk a szándékosan vagy súlyos gondatlansággal okozott károkért, az életet, testi épséget vagy egészséget megkárosító szerződésszegésért, valamint minden olyan esetben, amikor ezt kötelező jogszabály írja elő. Ezen túlmenően enyhe gondatlanság esetén csak a lényeges szerződéses kötelezettségek megszegéséért felelünk, és csak az ilyen szerződésnél jellemző, előre látható kárért. Az ingyenes előnézetet a mindenkori állapotában kínáljuk; folyamatos elérhetőségét nem vállaljuk.',
      ],
    },
    {
      id: 'disputes',
      title: 'Panaszkezelés, jogviták és alkalmazandó jog',
      blocks: [
        `Ha valami nem stimmel, kérjük, először nekünk írjon az ${MAIL} címre: a legtöbb problémát gyorsan megoldjuk e-mailben. Minden panaszra írásban, e-mailben válaszolunk, legkésőbb 30 napon belül.`,
        'Ha nem jutunk megegyezésre, fogyasztóként a litván Állami Fogyasztóvédelmi Hatósághoz (Valstybinė vartotojų teisių apsaugos tarnyba, Vilniaus g. 25, LT-01402 Vilnius, Litvánia, [vvtat.lt](https://vvtat.lt)) fordulhat, amely bíróságon kívül rendezi a fogyasztói jogvitákat, vagy a saját országa fogyasztóvédelmi szerveihez és bíróságaihoz. Határon átnyúló panaszában az Európai Fogyasztói Központ Magyarország ([magyarefk.hu](https://www.magyarefk.hu/hu/)) is ingyenesen segít.',
        'Magatartási kódexnek nem vetettük alá magunkat.',
        'A szerződésre a litván jog az irányadó. Ha Ön egy másik EU-országban élő fogyasztó, megmarad az ottani kötelező fogyasztóvédelmi szabályok által nyújtott védelme.',
      ],
    },
    {
      id: 'changes',
      title: 'A feltételek módosítása',
      blocks: ['Minden megrendelésre a leadásakor hatályos feltételek vonatkoznak.'],
    },
  ],
};

/** "Árak és fizetés" of the Hungarian edition (the hu market, prices in forints, src/shared/legal.ts legalEdition "hu"):
 *  the same section with the forint table, and the sentence that says which currency the payment page and the email
 *  show when the website shows another one. The rest of the ÁSZF is the base text above. */
export const huHufPrices: LegalSection = {
  id: 'prices',
  title: 'Árak és fizetés',
  blocks: [
    {
      dl: [
        ['Egy szem, Studio Black', huf(HU_PRICES.one_eye_studio_black, 'hu')],
        ['Egy szem művészi háttérrel', `${huf(HU_PRICES.one_eye_art, 'hu')} (${ART})`],
        ['Két szem (Couple Duo), bármely stílusban', huf(HU_PRICES.two_eyes, 'hu')],
        ['Minden további szem', `+${huf(HU_PRICES.each_further_eye, 'hu')}, legfeljebb ${MAX_EYES} szem egy alkotáson`],
      ],
    },
    'Minden ár forintban értendő végső ár, amely minden adót és díjat tartalmaz. Nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel és nem tüntetünk fel. Szállítási költség nincs. Ha a weboldal más pénznemben mutatja Önnek az árakat, a fizetési oldal és a visszaigazoló e-mail az Ön által fizetett pénznemet és összeget tünteti fel.',
    'Előre fizet, a fizetési szolgáltatónkon, a Stripe-on keresztül, a fizetési oldalon feltüntetett fizetési módok egyikével.',
  ],
};
