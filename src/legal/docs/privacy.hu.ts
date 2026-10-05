// Adatkezelési tájékoztató, the Hungarian ("hu") version of src/legal/docs/privacy.ts (GDPR 13. cikk): the same
// section ids and the same facts, in the "Ön" register. Every sentence says what the code does, as the English one
// does (see the header of privacy.ts for where each fact comes from); keep them in step when either changes.
// GDPR references use the Hungarian official style: „GDPR 6. cikk (1) bekezdés f) pont”. Two additions a Hungarian
// reader needs: the Hungarian supervisory authority (NAIH) next to the Lithuanian one, and the language key "hu" in
// the local storage section. Not reviewed by a Hungarian lawyer.
import type { LegalDoc } from '../types';
import { ORDER_EMAIL_SENDER, WITHDRAWAL_ONLINE } from '../../shared/legal';
import { MAIL, SELLER, address, company } from '../facts';

const companyHu = () => company('hu');
const addressHu = () => address('hu');
const WITHDRAWAL_ONLINE_HU = WITHDRAWAL_ONLINE.hu;

// what the online withdrawal function keeps (privacy.ts WITHDRAW_PRIVACY.en)
const WITHDRAW_PRIVACY_HU = `Ha online funkciónkkal áll el egy megrendeléstől (az „${WITHDRAWAL_ONLINE_HU.button}” gomb, lásd az [Elállási tájékoztatót](doc:withdrawal#online)), az elállási nyilatkozatát a megrendelésével együtt tároljuk: a nevét, az e-mail-címét, a rendelésszámot, a nyilatkozat szövegét, valamint beérkezésének dátumát és időpontját. Arra használjuk, hogy leállítsuk a fájl elkészítését, ha még nem kezdtük meg, hogy e-mailben átvételi elismervényt küldjünk Önnek a nyilatkozat tartalmával, dátumával és időpontjával, és hogy visszatérítsük a kifizetett összeget. Minden nyilatkozatról e-mailt is kapunk: egyenként, illetve az egyik megrendelésünkkel sem egyező, valamint a soha ki nem fizetett megrendelésekre vonatkozó nyilatkozatokról naponta egy összesítőben. Ha az elállása hatályos, a megrendelése képeit a napi automatikus törlésünk törli, amint az elállás óta 14 nap eltelt (ha a fizetése még feldolgozás alatt állt, csak miután lezárult); a megrendelés adatai a nyilatkozatával együtt megmaradnak (lásd: [Meddig őrizzük az adatait](#retention)). Ha az Ön által megadott adatok egyik megrendelésünkkel sem egyeznek (ha nem a rendelési oldaláról vagy a visszaigazoló e-mailben kapott elállási linkről érkezik, annak az e-mail-címnek kell szerepelnie, amellyel fizetett), a nyilatkozatot külön megőrizzük, kézzel ellenőrizzük, ennek ellenére e-mailben átvételi elismervényt küldünk (a visszaélés elleni, az [Online elállás](doc:withdrawal#online) pontban leírt korlátokon belül), és a beérkezése hónapjának végétől számított kb. 13 hónap után automatikusan töröljük.`;

// the admin log and the admin sign-in guard (privacy.ts ADMIN_LOG.en)
const ADMIN_LOG_HU = {
  log: 'Ha egy megrendelést az adminisztrációs felületünkön kezelünk, például a minőségellenőrzés után kiadunk egy fájlt, újraküldünk egy e-mailt, visszatérítést indítunk vagy fájlokat törlünk, a felület bejegyzést ír az adminisztrációs naplónkba: mi történt, mikor, melyik rendelésszámmal és milyen eredménnyel. Az adminisztrációs napló nem tartalmaz képet, e-mail-címet és linket. Jogalap: a megrendelések biztonságos és nyomon követhető kezeléséhez fűződő jogos érdekünk (GDPR 6. cikk (1) bekezdés f) pont). 24 hónap után automatikusan töröljük; a megrendelésre vonatkozó bejegyzések emellett a megrendelés adatainál is megmaradnak, amíg azokat megőrizzük (lásd: [Meddig őrizzük az adatait](#retention)).',
  signin: 'Az adminisztrációs felület csak nekünk szól. Hogy senki ne találhassa ki a kulcsát, egy sikertelen bejelentkezésnél a kérés IP-címének egy titkos kulccsal képzett hash-értékét tároljuk, magát a címet soha, és ezt 2 nap után automatikusan töröljük. Jogalap: a rendszereink biztonságához fűződő jogos érdekünk (GDPR 6. cikk (1) bekezdés f) pont).',
};

// the usage statistics (privacy.ts OPS.en)
const OPS_HU = {
  events:
    'Hogy lássuk, működik-e a szolgáltatás, milyen gyors, és mennyibe kerül, a szerverünk apró technikai eseményeket rögzít a Supabase nevű szolgáltatónál, az EU-ban lévő privát tárhelyünkön. Például: hogy egy fotót ellenőriztünk (az eredménnyel, például „nem található szem”, az eszköz típusával, például iPhone, Android vagy számítógép, azzal, hogy a fotó a kamerából vagy a galériából jött, és az oldal nyelvével), hogy eltávolítottuk a tükröződéseket, hogy elkészült egy előnézet vagy egy megrendelt fájl, és mennyi ideig tartott, vagy hogy egy kérés hibával végződött (a hibakóddal). Amíg árakat tesztelünk, az események azt is megmondják, melyik árlista (egy rövid kód) jelent meg, lett előnézetben látva, nyílt meg fizetésre vagy lett kifizetve, kifizetett megrendelésnél az összeggel. Az adminisztrációs felületünk ezeket főként napi darabszámként mutatja nekünk.',
  content:
    '**Ezek az események nem tartalmaznak képet, Ön által beírt szöveget, nevet, e-mail-címet, IP-címet, böngészőazonosítót (user agent) és linket.** Az ingyenes előnézet eseményei nem vezethetők vissza Önre. Csak a kifizetett megrendelés fájljának elkészítéséről szóló események tartalmazzák a rendelésszámot is, hogy megtaláljuk a lassú vagy sikertelen elkészítést; ez a szám a megrendelési adatainkon keresztül az Ön megrendeléséhez kapcsolódik.',
  basis:
    'Jogalap: a szolgáltatás megbízható működtetéséhez, a hibák felderítéséhez és a költségek kézben tartásához fűződő jogos érdekünk (GDPR 6. cikk (1) bekezdés f) pont). Az eseményeket és a belőlük képzett napi számokat 12 hónap után automatikusan töröljük. Ön bármikor tiltakozhat (lásd: [Az Ön jogai](#rights)).',
  admin: ADMIN_LOG_HU.log,
  signin: ADMIN_LOG_HU.signin,
};

const rep = (label: string) => (SELLER.representative ? ` ${label} ${SELLER.representative}.` : '');
const senderHu = ORDER_EMAIL_SENDER === 'Hostinger' ? [] : [`${ORDER_EMAIL_SENDER}: a megrendelésével kapcsolatos e-mailek küldése (a rendelési oldal linkje, a megrendelés visszaigazolása és elállás esetén az átvételi elismervény). A szerverei az EU-n kívül is lehetnek.`];
const hostingerHu = ORDER_EMAIL_SENDER === 'Hostinger'
  ? 'Hostinger: az e-mail-szolgáltatásunk, az info@snapeyes.com postafiók, a megrendelésével kapcsolatos e-mailekkel együtt.'
  : 'Hostinger: az info@snapeyes.com postafiókunk.';

export const hu: LegalDoc = {
  title: 'Adatkezelési tájékoztató',
  description:
    'Hogyan kezeli a SnapEyes a szeméről készült fotót, az előnézetet és rendelés esetén a megrendelési adatokat: mit, miért, milyen szolgáltatókkal és meddig kezelünk, és milyen jogai vannak.',
  lead:
    'Ez a tájékoztató elmondja, mi történik az adataival, amikor a snapeyes.com oldalt használja: az ingyenes előnézetnél és rendelés esetén a digitális alkotásánál. Röviden: a fotóját kizárólag az alkotása elkészítéséhez használjuk, soha nem azonosításra, és soha nem mesterséges intelligencia tanítására. Az ingyenes előnézeteket nem tároljuk. A kifizetett megrendelések fájljait 12 hónapig őrizzük meg, hogy újra letölthesse őket, azután töröljük.',
  toc: true,
  numbered: true,
  sections: [
    {
      id: 'controller',
      title: 'Ki az adatkezelő',
      blocks: [
        `Az adatai kezelője az ${companyHu()} (cégazonosító szám: ${SELLER.code}), ${addressHu()}. A SnapEyes a márkaneve.${rep('Képviseli:')}`,
        `Minden adatvédelmi kérdésével, és bármely joga gyakorlásához írjon az ${MAIL} címre. Adatvédelmi tisztviselőt nem neveztünk ki.`,
      ],
    },
    {
      id: 'website',
      title: 'Amikor a weboldalt látogatja',
      blocks: [
        'Amikor megnyitja a snapeyes.com egy oldalát, a böngészője technikai adatokat küld a tárhelyszolgáltatónknak, a Vercelnek, például az IP-címét, a dátumot és az időpontot, a kért oldalt és a böngészője típusát (user agent). A Vercelnek ezekre az adatokra az oldal kiszolgálásához és a szolgáltatás támadások elleni védelméhez van szüksége. Rövid ideig szervernaplókban tárolja, majd törli őket.',
        'Hogy a saját pénznemében tudjunk árakat javasolni, a szerverünk azt az országot is le tudja olvasni, amelyet a Vercel az IP-címéből származtat (például „AU”). Ezt kizárólag erre a javaslatra használjuk, soha nem változtatja meg a látott árakat, és nem tároljuk.',
        'Jogalap: a biztonságos, működő weboldalhoz fűződő jogos érdekünk (GDPR 6. cikk (1) bekezdés f) pont).',
        'A betűtípusokat a saját szerverünkről szolgáltatjuk, így semmilyen adat nem jut a Google Fonts vagy más betűtípus-szolgáltató részére. Ezen a weboldalon nem használunk más cégek webanalitikai, hirdetési vagy követő eszközeit, és semmi nem követi Önt oldalról oldalra vagy weboldalak között. Saját, névtelen szolgáltatási statisztikánkat a [Szolgáltatási statisztika és adminisztrációs napló](#operations) pont írja le.',
      ],
    },
    {
      id: 'preview',
      title: 'Az ingyenes előnézet',
      blocks: [
        'Az előnézethez egy vagy több, egy szemről készült fotót küld a böngészőjéből a szerverfunkcióinknak. Ott a fotót a memóriában dolgozzuk fel: megkeressük az íriszt, kivágjuk, ellenőrizzük, hogy elég éles és világos-e, eltávolítjuk a tükröződéseket, a Google Gemini API-jával helyreállítjuk a finom rostokat, és az íriszt a látott stílusokba illesztjük. Az eredmény visszakerül a böngészőjébe. Minden adatátvitel titkosított (HTTPS).',
        '**A fotóját, az íriszkivágást és az előnézetet nem tároljuk a szervereinken.** A kérés végén elvetjük őket. Az előnézet az oldal bezárásáig a böngészőjében marad (amíg a fizetési oldalon van, a böngészőlap munkamenet-tárhelyén: lásd a [Sütik és helyi tárhely](#storage) pontot), kivéve, ha maga menti el. Csak amikor megrendelést indít, akkor őrizzük meg az íriszkivágást és az Ön által jóváhagyott előnézetet: lásd a [Rendelés esetén](#orders) pontot.',
        'A Google a helyreállítás elkészítéséhez dolgozza fel a képet. A Google fizetős API-szolgáltatását használjuk, amelynek feltételei szerint a Google nem használja a képeket a termékei fejlesztésére vagy a modelljei tanítására. A Google a kéréseket korlátozott ideig megőrizheti, kizárólag a visszaélések felderítésére és a jogszabály által előírt adatszolgáltatásokhoz.',
        'Jogalap: Ön kéri az előnézet elkészítését, és ehhez szükség van a fotóra (GDPR 6. cikk (1) bekezdés b) pont, az Ön kérésére tett lépések).',
        'A szoftverünk automatikusan dönti el, hogy egy fotó használható-e (például ha túl elmosódott vagy túl sötét). Ennek a döntésnek nincs Önre nézve joghatása vagy hasonlóan jelentős hatása: egyszerűen készíthet egy másik fotót.',
      ],
    },
    {
      id: 'iris',
      title: 'Az íriszét soha nem használjuk azonosításra',
      blocks: [
        'Az írisz elvileg alkalmas lehet egy személy felismerésére. Mi ezt nem tesszük. Soha nem hozunk létre, nem hasonlítunk össze és nem tárolunk íriszmintát (template) vagy más biometrikus azonosítót, soha nem használjuk a képeit senki azonosítására vagy ellenőrzésére, soha nem adjuk el őket, és soha nem használjuk őket mesterséges intelligencia tanítására, sem a sajátunkéra, sem másokéra.',
        'Kérjük, csak a saját szemét használja, vagy olyan személy szemét, aki ehhez hozzájárult. Gyermek esetén a szülő vagy a gondviselő hozzájárulása szükséges.',
        'Ha más személyek szemét is hozzáadja (például egy páros képhez), az ő képeiket kizárólag annak az alkotásnak az elkészítéséhez kezeljük, amelyhez hozzájárultak. Jogalap: az alkotás elkészítéséhez fűződő jogos érdek, az Öné és a miénk (GDPR 6. cikk (1) bekezdés f) pont). Kérjük, mutassa meg nekik ezt a tájékoztatót.',
      ],
    },
    {
      id: 'measurements',
      title: 'Technikai mérések (képek nélkül)',
      blocks: [
        'Minden fotónál a szerverünk egy sort ír a naplóiba, hogy javíthassuk a fotózási útmutatót és a szolgáltatás minőségét. Ez a fotó mérési adatait tartalmazza (például az írisz méretét pixelben, az élességet, a világosságot, a fény színeltolódását és azt, hogy a fotó használható volt-e), az eszköze technikai adatait (böngésző típusa és verziója, képernyőméret, a fotó a kamerából vagy a galériából jött-e), és ha válaszol a felvételről feltett, nem kötelező kérdéseinkre, a válaszait. Nem tartalmaz képet, nevet és elérhetőséget.',
        'Ezeket a naplósorokat a tárhelyszolgáltatónk rövid ideig őrzi, majd törli. Jogalap: a szolgáltatás fejlesztéséhez fűződő jogos érdekünk (GDPR 6. cikk (1) bekezdés f) pont). Ön bármikor tiltakozhat (lásd: [Az Ön jogai](#rights)).',
      ],
    },
    {
      id: 'operations',
      title: 'Szolgáltatási statisztika és adminisztrációs napló',
      blocks: [OPS_HU.events, OPS_HU.content, OPS_HU.basis, OPS_HU.admin, OPS_HU.signin],
    },
    {
      id: 'orders',
      title: 'Rendelés esetén',
      blocks: [
        'Amikor megrendelést indít, minden szemről két kép kerül fel a privát tárhelyünkre, hogy a fájl pontosan abból készüljön, amit Ön látott: az írisz körüli, a fotójából kivágott négyzet (a tükröződések eltávolítása után) és az Ön által jóváhagyott előnézet. Ezekkel együtt egy rövid mérési adatsort is tárolunk, amely ebből az előnézetből készült (az íriszét körülvevő színeket, egy színosztályt, a pupilla alakját, két minőségi értéket és az előnézet azonosítóját). Képet nem tartalmaz, és a képekkel együtt törlődik. **A teljes telefonos fotóját nem tároljuk, rendelés esetén sem.** A 24 órán belül ki nem fizetett megrendelés már nem fizethető ki. Egy naponta egyszer lefutó automatikus törlés ezután törli a képeit és adatait, általában a megrendeléstől számított két napon belül, de legkésőbb 30 napon belül.',
        'Hogy a feltöltések a korlátokon belül maradjanak, a szerverünk minden feltöltésről egy kis jelölőt is ír (a méretét, a napot és a rendelésszámot, képet nem). Ezeket a jelölőket néhány nap után automatikusan töröljük.',
        'Az alkotás értékesítéséhez és szolgáltatásához a következőket kezeljük: a megrendelést (rendelésszám, dátum, szemek, stílus, elrendezés, a szemek sorrendje, az Ön által megadott nevek, dátum vagy felirat, nyelv, ár), az e-mail-címét (a fizetési oldalon adja meg), a Stripe-tól kapott fizetési állapotot, az azonnali kezdéshez adott hozzájárulását (lásd az [Elállási tájékoztatót](doc:withdrawal)), valamint a megrendelés fájljait: a fent említett két képet szemenként, minden szem 4096 px-es változatát és az elkészült alkotást, technikai minőségi adatokkal.',
        'Ezeket a fájlokat a Supabase nevű szolgáltatónál, egy EU-ban lévő privát tárhelyen őrizzük. A rendelési oldalán érheti el őket, amelynek linkjét e-mailben elküldjük Önnek; a link egy privát kulcsot tartalmaz, így aki ismeri, letöltheti az alkotását. Az oldal által létrehozott minden letöltési link 7 nap után lejár.',
        'A megrendelése fájljait a minőségük ellenőrzése céljából megnézhetjük, például ha az automatikus ellenőrzésünk eltérést jelez az Ön által jóváhagyott előnézethez képest.',
        'Jogalap: az Önnel kötött szerződés (GDPR 6. cikk (1) bekezdés b) pont); a számviteli nyilvántartások esetében a jogi kötelezettségeink (GDPR 6. cikk (1) bekezdés c) pont).',
        'Amikor továbblép a fizetési oldalra, a fizetésével együtt átadjuk a Stripe-nak a megrendelés adatait: a rendelésszámot, az árat (és ha árteszt érvényes, annak nevét, az Ön árlistájának kódját és az árlista árait), a szemek számát, a stílust (és annak változatát), az elrendezést, a szemek sorrendjét, a nyelvet, az Ön által megadott neveket, dátumot vagy feliratot, egy rövid kódot, amely az alkotás tervét azonosítja, és az azt elkészítő szoftverünk verzióját, valamint a hozzájárulása verzióját és időpontját. A Stripe ezeket a fizetési adatokkal együtt őrzi, mi pedig onnan olvassuk vissza őket, hogy pontosan azt az alkotást készítsük el, amelyért Ön fizetett.',
        'Fizetés: a fizetését a Stripe dolgozza fel. A teljes kártyaszámát soha nem látjuk. A Stripe a fizetési adatokat a saját adatvédelmi szabályzata szerint is kezeli, a csalások megelőzésére és a saját jogi kötelezettségei teljesítésére.',
        'Az e-mail-címére azért van szükségünk, hogy elküldjük Önnek a rendelési oldala linkjét és a megrendelés visszaigazolását. Nélküle elveszítheti a hozzáférést a fájljához.',
      ],
    },
    {
      id: 'email',
      title: 'Ha ír nekünk',
      blocks: [
        'Ha e-mailt ír nekünk, a címét és az üzenetét a válaszadáshoz, és ha megrendelést érint, annak kezeléséhez használjuk. Jogalap: megrendelés esetén a GDPR 6. cikk (1) bekezdés b) pontja, egyébként a válaszadáshoz fűződő jogos érdekünk (GDPR 6. cikk (1) bekezdés f) pont). Ha fotókat küld nekünk, például a szeméről, hogy jobb felvételhez adjunk tanácsot, azokat kizárólag a kérése teljesítéséhez használjuk. Az e-mailjeit a fotókkal együtt addig őrizzük meg, ameddig a kéréséhez és az esetleges további ügyintézéshez szükségünk van rájuk.',
      ],
    },
    {
      id: 'withdrawal',
      title: 'Ha online áll el egy megrendeléstől',
      blocks: [
        WITHDRAW_PRIVACY_HU,
        'Jogalap: jogi kötelezettségünk az elállás fogadására és visszaigazolására (GDPR 6. cikk (1) bekezdés c) pont) és az Önnel kötött szerződés (GDPR 6. cikk (1) bekezdés b) pont). A nyilatkozatot bizonyítékként a megrendelés adataival együtt őrizzük meg, ameddig azokat megőrizzük (lásd: [Meddig őrizzük az adatait](#retention)).',
      ],
    },
    {
      id: 'services',
      title: 'Az általunk igénybe vett szolgáltatók',
      blocks: [
        'A SnapEyes működtetéséhez a következő szolgáltatókat vesszük igénybe:',
        {
          ul: [
            'Vercel: a weboldal és az előnézetet, illetve a fájlt elkészítő szerverfunkciók tárhelye. A Vercel adatközpontjai az EU-n kívül, például az USA-ban is lehetnek.',
            'Google (Gemini API): az írisz mesterséges intelligenciával végzett helyreállítása és a fotó ellenőrzése. A Google szerverei az EU-n kívül is lehetnek.',
            'Supabase: a megrendelések fájljainak privát tárhelye, EU-s régióban.',
            'Stripe: fizetésfeldolgozás, a [Rendelés esetén](#orders) pontban felsorolt megrendelési adatokkal.',
            hostingerHu,
            ...senderHu,
          ],
        },
        `Ezek a szolgáltatók a nevünkben és az utasításaink szerint kezelik az adatait (a Stripe részben önálló adatkezelőként, lásd a [Rendelés esetén](#orders) pontot). Ha adatok az EU-n vagy az EGT-n kívülre kerülnek, ez a szolgáltatók által nyújtott garanciák mellett történik, például az Európai Bizottság által elfogadott általános adatvédelmi kikötések vagy az EU-USA adatvédelmi keretrendszer alapján. Ezekről a garanciákról másolatot kérhet az ${MAIL} címen.`,
        'Az adatait nem adjuk el, és senki másnak nem adjuk át, kivéve, ha jogszabály kötelez rá.',
      ],
    },
    {
      id: 'retention',
      title: 'Meddig őrizzük az adatait',
      blocks: [
        {
          dl: [
            ['Ingyenes előnézetek', 'Nem tároljuk őket. A kérés végén elvetjük őket.'],
            ['Ki nem fizetett megrendelések', 'A 24 órán belül ki nem fizetett megrendelés már nem fizethető ki. A napi automatikus törlésünk törli a képeit és adatait, általában a megrendeléstől számított két napon belül, de legkésőbb 30 napon belül.'],
            ['Feltöltési és nyilatkozati jelölők', 'Kis számlálók képek, nevek és e-mail-címek nélkül (az átvételi elismervények számlálója csak az e-mail-cím egy rövid hash-értékét tartalmazza); néhány nap után automatikusan töröljük őket, az átvételi elismervények havi számlálóit a hónapjuk végétől számított kb. 40 nap után.'],
            ['Kifizetett megrendelések', 'A megrendelés fájljait a fizetéstől számított 12 hónapig őrizzük meg, hogy a rendelési oldaláról újra letölthesse őket, azután a napi automatikus törlésünk törli őket. Kérésére korábban is töröljük őket; utána a rendelési oldala már nem tudja szolgáltatni a fájlt.'],
            ['Elállással érintett megrendelések', 'Ha az elállás hatályos, a napi törlésünk a megrendelés képeit az elállástól számított 14 nap elteltével törli (ha a fizetés még feldolgozás alatt állt, azután, hogy lezárult).'],
            ['Egyik megrendeléssel sem egyező elállási nyilatkozatok', 'Külön megőrizzük, kézzel ellenőrizzük, és a beérkezésük hónapjának végétől számított kb. 13 hónap után automatikusan töröljük őket.'],
            ['Megrendelési adatok', 'A fájlok törlésekor (12 hónap után, elállás után vagy kérésre) megőrizzük a kifizetett megrendelés adatait: rendelésszám, dátum, ár, fizetés és az esetleges visszatérítés, az e-mail-címe, a megrendelt alkotás adatai (amelyek az Ön által megadott neveket, dátumot vagy feliratot, valamint az előnézeteiből készült mérések rövid összefoglalóját is tartalmazhatják: minden szem színosztályát, átlagos gyűrűszínét és pupillaalakját), az azonnali kezdéshez adott hozzájárulása, elállás esetén az elállási nyilatkozata, valamint az adminisztrációs naplónk bejegyzései a megrendeléséről. Képeket nem. A szerződés bizonyítékaként és a számvitel céljára őrizzük meg, ameddig a litván számviteli és adójogszabályok előírják.'],
            ['Szervernaplók és mérések', 'A tárhelyszolgáltatónk rövid ideig őrzi, majd törli őket.'],
            ['Szolgáltatási statisztika', 'A technikai eseményeket és napi számaikat (lásd: [Szolgáltatási statisztika és adminisztrációs napló](#operations)) 12 hónap után automatikusan töröljük.'],
            ['Adminisztrációs napló', 'Hogy mit tettünk egy megrendeléssel az adminisztrációs felületünkön: 24 hónap után automatikusan töröljük; a megrendelésre vonatkozó bejegyzések a megrendelés adatainál maradnak.'],
            ['Sikertelen bejelentkezések az adminisztrációs felületre', 'Az IP-cím egy titkos kulccsal képzett hash-értéke, 2 nap után automatikusan töröljük.'],
            ['E-mailek', 'Ameddig a kéréséhez és az esetleges további ügyintézéshez szükségünk van rájuk.'],
          ],
        },
      ],
    },
    {
      id: 'rights',
      title: 'Az Ön jogai',
      blocks: [
        'Ezek a jogok bármikor megilletik:',
        {
          ul: [
            'Hozzáférés: megtudhatja, milyen adatokat kezelünk Önről, és másolatot kaphat róluk (GDPR 15. cikk).',
            'Helyesbítés: kérheti a téves adatok kijavítását (GDPR 16. cikk).',
            'Törlés: kérheti az adatai törlését, például a megrendelése fájljainak törlését a 12 hónap letelte előtt (GDPR 17. cikk).',
            'Az adatkezelés korlátozása: kérheti az adatkezelés korlátozását, amíg egy kérdés tisztázása folyik (GDPR 18. cikk).',
            'Adathordozhatóság: az Ön által megadott adatokat tagolt, széles körben használt, géppel olvasható formátumban megkaphatja (GDPR 20. cikk).',
            'Tiltakozás: a saját helyzetével kapcsolatos okokból bármikor tiltakozhat a jogos érdekünkön alapuló adatkezelés ellen (GDPR 21. cikk).',
          ],
        },
        `Bármely joga gyakorlásához írjon az ${MAIL} címre. Egy hónapon belül válaszolunk.`,
        'Joga van panaszt tenni egy felügyeleti hatóságnál is. A mi felügyeleti hatóságunk a litván Állami Adatvédelmi Felügyelőség (Valstybinė duomenų apsaugos inspekcija, VDAI), Vilnius, [vdai.lrv.lt](https://vdai.lrv.lt). Ahhoz az EU-országhoz tartozó hatósághoz is fordulhat, ahol él vagy dolgozik; Magyarországon ez a Nemzeti Adatvédelmi és Információszabadság Hatóság (NAIH, [naih.hu](https://naih.hu)).',
      ],
    },
    {
      id: 'storage',
      title: 'Sütik és helyi tárhely',
      blocks: [
        'Ez a weboldal nem használ sütiket. Nem használ más cégektől származó webanalitikai, hirdetési vagy követő eszközöket.',
        'Ha a nyelvválasztóval nyelvet választ, a böngészője ezt a helyi tárhelyén (local storage) jegyzi meg, a „snapeyes.lang” kulcs alatt (értéke a nyelv kódja, például „hu”). Ezt soha nem küldi el nekünk, és a böngésző beállításaiban bármikor törölheti. Egy Ön által kért funkcióhoz feltétlenül szükséges, ezért nem igényel hozzájárulást (az elektronikus hírközlési adatvédelmi irányelv 5. cikk (3) bekezdése).',
        'Ha egy másik pénznemben feltüntetett árakat tartalmazó linken (például ausztrál dollárban) érkezik hozzánk, vagy a pénznemváltónkkal, illetve a saját pénznemében megjelenített árakra tett ajánlatunkban pénznemet választ, a böngészője ezt a választást ugyancsak megjegyzi a helyi tárhelyén (local storage), a „snapeyes.market” kulcs alatt (például „au”, vagy „eu”, ha elutasította az ajánlatot), hogy az oldal továbbra is ugyanazokat az árakat mutassa. Oldalaink a linkjeikben (m=au) továbbviszik, és a megrendeléssel együtt elküldik, hogy Önnek a látott árakat számítsuk fel. A böngésző beállításaiban bármikor törölheti; az Ön által kért funkcióhoz feltétlenül szükséges, ezért ez sem igényel hozzájárulást (az elektronikus hírközlési adatvédelmi irányelv 5. cikk (3) bekezdése).',
        'Amikor árakat tesztelünk (csak időnként és korlátozott ideig), a böngészője egy véletlenszerű, névtelen látogatószámot tárolhat a helyi tárhelyén (local storage), a „snapeyes.vid” kulcs alatt. Csak akkor jön létre, amikor az Ön által megtekintett piacon (pénznemben) árteszt fut, és törlődik, amint már nem fut teszt; legkésőbb 90 nap után lecserélődik. 32 véletlenszerű karakterből és a létrehozásának napjából áll: nem Önből van levezetve, nem tartalmaz nevet, e-mail-címet vagy eszközadatot, és soha nem kapcsolódik megrendeléshez. A böngészője egy kérésfejlécben (soha nem egy oldal címében) küldi el a szerverünknek, amikor az árakat kéri; az alkalmazásunk csak arra használja, hogy minden alkalommal ugyanúgy meghatározza, a teszt melyik árlistáját látja, és nem tárolja el: nem vezetünk látogatószám-listát. A szerver az árlistája aláírt jelölésével válaszol, amelyet a böngészője visszaküld, amikor a fizetési oldalra lép, hogy pontosan azokat az árakat számítsuk fel Önnek, amelyeket mutattunk (a böngésző által küldött árat vagy árlistát soha nem használjuk). A statisztikához a szerverünk névtelen darabszámokat rögzít árlistánként: hogy egy árlistát megmutattunk, hogy előnézet készült, hogy megnyílt a fizetési oldal, és hogy egy megrendelést kifizettek (lásd a [Működési statisztikák és az adminisztrációs naplónk](#operations) részt); ezek a darabszámok nem tartalmaznak látogatószámot. A böngészője a helyi tárhelyén azt is megjegyzi, hogy e darabszámok közül melyeket küldte el már („snapeyes.expseen”), és az utolsó árlistáját („snapeyes.pricing”), hogy azonnal ugyanazok az árak jelenjenek meg. Az, hogy melyik árlistát látja, sosem függ attól, hol él, csak az Ön által választott piactól (pénznemtől), és az ár, amelyet fizet, mindig az, amelyet a fizetés előtt mutattunk Önnek; a megrendelés visszaigazolása megnevezi az alkalmazott árlistát. Ezeket a bejegyzéseket kizárólag erre az árteszt céljára használjuk, soha nem hirdetésre, és soha nem azért, hogy más weboldalakon kövessük Önt. Ha nem szeretne részt venni, [nyissa meg ezt a linket](/?pricetest=off&lang=hu): a böngészője ekkor csak a „snapeyes.notest” jelölést őrzi meg, törli a látogatószámot és az itt említett többi bejegyzést, és a szokásos árakat mutatja és számítja fel; [ezzel a linkkel](/?pricetest=on&lang=hu) ismét részt vesz. Ha a böngészője a „Global Privacy Control” jelzést küldi, az is ennek a döntésnek számít. Ezeket a bejegyzéseket a böngésző beállításaiban bármikor törölheti is (ekkor új véletlenszerű besorolást kap). Jogalap: a tisztességes árak megállapításához fűződő jogos érdekünk (GDPR 6. cikk (1) bekezdés f) pont). Bármikor tiltakozhat (lásd a [Jogai](#rights) részt).',
        'Rendelés esetén az oldal két bejegyzést is tárol a böngészőlap munkamenet-tárhelyén (session storage). A munkamenet-tárhely csak ahhoz az egy böngészőlaphoz tartozik, és a lap bezárásakor törlődik:',
        {
          ul: [
            '„snapeyes.order”: az Ön által összeállított megrendelés száma és privát kulcsa, hogy az oldal folytathassa a megrendelést, például amikor visszatér a fizetési oldalról. Törlődik, amikor a kifizetett megrendelés oldala megnyílik abban a lapban, és lecserélődik, ha új megrendelést kezd.',
            '„snapeyes.checkout”: csak amíg a fizetési oldalon van, az alkotása abban az állapotban, ahogy otthagyta (a fotóiból kivágott íriszek, az előnézetek, néhány belőlük mért szám, a stílus és annak változata, az elrendezés, a szemek sorrendje, a nevek és a dátum), hogy a fizetési oldalról visszalépve újra megjelenjen. Törlődik, amint visszatér, vagy amikor a kifizetett megrendelés oldala megnyílik abban a lapban.',
          ],
        },
        'Az oldal ezeket kizárólag a megrendeléséhez használja, és ehhez feltétlenül szükségesek, így ezek sem igényelnek hozzájárulást (az elektronikus hírközlési adatvédelmi irányelv 5. cikk (3) bekezdése).',
        'Fizetéskor a Stripe fizetési oldala saját sütiket használhat, amelyek a biztonságos fizetéshez és a csalások megelőzéséhez szükségesek; ott a Stripe saját adatvédelmi és sütiszabályzata érvényes.',
      ],
    },
    {
      id: 'required',
      title: 'Köteles-e megadni nekünk adatokat?',
      blocks: ['Nem. Fotó nélkül azonban nem tudunk előnézetet készíteni, e-mail-cím és fizetés nélkül pedig nem tudunk megrendelést teljesíteni.'],
    },
    {
      id: 'changes',
      title: 'A tájékoztató módosítása',
      blocks: ['Ezt a tájékoztatót frissítjük, ha a szolgáltatásunk vagy a jogszabályok változnak. A fenti dátum mutatja a hatályos változatot.'],
    },
  ],
};
