// Hungarian ("hu") copy for /order: every key of src/order/copy.ts `en`, in the same structure. Friendly "te", the
// words of /try and the landing page (alkotás, előnézet, szem, fájl). The page words every server answer itself from
// its reason code, as in English.
// The withdrawal form uses the statutory words of 45/2014. (II. 26.) Korm. rendelet 22. § (1a)-(1c): the function
// „elállás a szerződéstől”, the confirming step „elállás megerősítése” (src/shared/legal.ts WITHDRAWAL_ONLINE.hu),
// and the receipt is an „átvételi elismervény”. The statement follows the model form of the decree's 2. melléklet
// („Alulírott ... kijelentem, hogy gyakorlom elállási jogomat ... szerződés tekintetében”) and must stay word for word
// the same as api/_lib/withdraw_hu.py STATEMENT_HU.
import type { OrderCopy } from './copy';
import { CONTACT_EMAIL } from '../landing/config';

export const hu: OrderCopy = {
  lang: 'hu',
  meta: {
    title: 'A rendelésed | SnapEyes',
    description: 'A SnapEyes-rendelésed: itt készül el az íriszalkotásod, és innen töltheted le.',
  },
  switchLabel: 'Nyelv',
  tag: 'Private Atelier · rendelés',
  title: 'A rendelésed',
  orderNo: (o: string) => `Rendelés: ${o}`,
  loading: 'A rendelésed megnyitása…',
  summary: {
    eyes: (n: number) => `${n} szem`,
    paid: (amount: string) => `Fizetve: ${amount}`,
    inscription: (s: string) => `Felirat: ${s}`,
  },
  unpaid: {
    title: 'Még nincs kifizetve',
    body: 'Ehhez a rendeléshez még nem érkezett fizetés.',
    confirming: 'Ellenőrizzük a fizetésedet a Stripe-nál…',
    expired: 'Ezt a rendelést 24 órán belül nem fizették ki, ezért már nem fizethető ki. Nem történt érte terhelés.',
    hint: 'Ha most fizettél, nézd meg újra egy kicsit később. Ha nem, visszatérhetsz a stúdióba, és onnan rendelhetsz.',
    check: 'Újraellenőrzés',
    studio: 'Vissza a stúdióba',
  },
  pending: {
    title: 'A fizetésed megerősítése folyamatban',
    body: 'A fizetési módod megerősítése kicsit tovább tart. Amint megerősítették, nekilátunk az alkotásodnak. Ez az oldal magától újra ellenőrzi.',
    mailTitle: 'A fizetés beérkezett',
    mailBody: 'A fizetésedet megerősítettük. Most küldjük el e-mailben a rendelésed visszaigazolását, és utána rögtön nekilátunk az alkotásodnak. Ez az oldal magától újra ellenőrzi.',
  },
  making: {
    title: 'Készül az alkotásod',
    lead: 'A fájlod 4096 px-es méretben készül, pontosan az általad jóváhagyott előnézetekből. Ez szemenként kb. 30 másodpercig tart.',
    keepOpen: 'Kérjük, hagyd nyitva ezt az oldalt, amíg elkészül a letöltés.',
    closeEmail: 'Ha bezárod, a folytatáshoz nyisd meg az e-mailben kapott linket.',
    closeNoEmail: 'Ha bezárod, a folytatáshoz nyisd meg újra ezt az oldalt ugyanazon a címen.',
    serverOn: 'Az alkotásodat a mi oldalunkon készítjük, így bezárhatod ezt az oldalt.',
    serverEmail: 'E-mailt küldünk, amikor elkészült.',
    serverNoEmail: 'A letöltéshez később nyisd meg újra ezt az oldalt ugyanazon a címen.',
    eye: (i: number) => `${i}. szem`,
    done: 'Kész',
    working: 'Folyamatban…',
    waiting: 'Várakozik',
    composing: 'Az alkotásod összeállítása…',
    part: (k: number, of: number) => `Az alkotásod összeállítása (${k}/${of})…`,
    progress: (done: number, n: number) => `${done}/${n} szem kész`,
    elapsed: (s: number) => `${s} mp`,
  },
  wait: {
    busy: (s: number) => `A stúdió most leterhelt. Újrapróbálkozás ${s} mp múlva…`,
    network: (s: number) => `Megszakadt a kapcsolat. Újrapróbálkozás ${s} mp múlva…`,
    rendering: (s: number) => `Ez a szem már készül. Újraellenőrzés ${s} mp múlva…`,
    confirming: (s: number) => `Újraellenőrzés ${s} mp múlva…`,
  },
  review: {
    title: 'Ellenőrizzük az alkotásodat',
    body: 'Az alkotásodat átadás előtt kézzel is ellenőrizzük, és e-mailt küldünk. Neked nincs teendőd.',
  },
  ready: {
    title: 'Elkészült az alkotásod',
    download: 'A teljes méretű fájl letöltése',
    open: 'A kép megnyitása',
    alt: 'A SnapEyes-alkotásod',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} MB`,
    link: 'A letöltési link 7 napig érvényes. Friss linkért bármikor nyisd meg újra ezt az oldalt: a fájlodat 12 hónapig őrizzük.',
    email: 'Ennek az oldalnak a linkjét az e-mailedben is megtalálod.',
    bookmark: 'Őrizd meg ennek az oldalnak a címét: ezzel férsz hozzá a fájlodhoz.',
  },
  deleted: {
    title: 'Fájlok törölve',
    body: `Ennek a rendelésnek a fájljait töröltük. Írj nekünk: ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Hiba történt',
    bad_link: `Ez a rendelési link érvénytelen. Kérjük, nyisd meg újra az e-mailben kapott linket, vagy írj nekünk: ${CONTACT_EMAIL}.`,
    missing: `Ehhez az oldalhoz az e-mailben vagy a fizetési oldalon kapott teljes link szükséges. Ha nem találod, írj nekünk: ${CONTACT_EMAIL}.`,
    network: 'Nem sikerült elérni a SnapEyes szolgáltatást. Kérjük, ellenőrizd az internetkapcsolatodat, és próbáld újra.',
    busy: 'A stúdió most nagyon leterhelt. Kérjük, próbáld újra néhány perc múlva.',
    failed: `Hiba történt nálunk. Kérjük, próbáld újra. Ha újra előfordul, írj nekünk a rendelésszámoddal: ${CONTACT_EMAIL}.`,
    retry: 'Próbáld újra',
  },
  withdraw: {
    heading: 'Elállás a szerződéstől',
    lead: 'A rendeléskor hozzájárultál, hogy azonnal megkezdjük a fájlod elkészítését. Amíg nem kezdtük el, itt elállhatsz ettől a szerződéstől. Amint az elkészítés megkezdődik, az elállási jogod megszűnik.',
    acl: 'Ez az uniós fogyasztóvédelmi jog szerinti elállási jog, amellyel meggondolás esetén állhatsz el a szerződéstől. Az ausztrál fogyasztóvédelmi törvény (Australian Consumer Law) szerinti jogaidat ez nem érinti: ha a fájlod hibás, vagy nem felel meg a leírásnak, írj nekünk a rendelésszámoddal.',
    info: 'Elállási tájékoztató',
    formLead: (confirm: string) => `Kérjük, ellenőrizd az adataidat. Az „${confirm}” gombbal ezt a nyilatkozatot küldöd el nekünk:`,
    statement: (o: string) => `Alulírott kijelentem, hogy gyakorlom elállási jogomat az alábbi digitális tartalom szolgáltatására irányuló szerződés tekintetében: SnapEyes-alkotás, rendelésszám: ${o}.`,
    statementNoOrder: 'Alulírott kijelentem, hogy gyakorlom elállási jogomat az alábbi digitális tartalom szolgáltatására irányuló szerződés tekintetében: SnapEyes-alkotás, az alább megadott rendelés.',
    name: 'A neved',
    email: 'E-mail-cím a visszaigazoláshoz',
    emailHint: 'Erre a címre küldjük az átvételi elismervényt, a dátummal és az időponttal.',
    emailHintNoLink: 'Kérjük, azt az e-mail-címet add meg, amellyel fizettél: ebből látjuk, hogy a rendelés a tiéd. Erre a címre küldjük az átvételi elismervényt, a dátummal és az időponttal.',
    order: 'Rendelésszám',
    orderHint: 'Megtalálod a rendelésed visszaigazoló e-mailjében és a rendelési oldalon.',
    sending: 'Az elállásod küldése…',
    cancel: 'Mégse',
    back: 'Vissza a rendelésedhez',
    invalid: {
      name: 'Kérjük, add meg a neved.',
      email: 'Kérjük, érvényes e-mail-címet adj meg.',
      order: 'Kérjük, úgy add meg a rendelésszámot, ahogy az e-mailben szerepel.',
    },
    errors: {
      network: 'Nem sikerült elérni a SnapEyes szolgáltatást, ezért nem tudjuk, megérkezett-e az elállásod. Kérjük, ellenőrizd a kapcsolatodat, és próbáld újra: az ismételt küldés nem okoz gondot.',
      busy: `A rendszerünk most leterhelt, ezért az elállásodat nem tudtuk rögzíteni. Kérjük, próbáld újra egy kicsit később, vagy írd meg az elállásodat e-mailben: ${CONTACT_EMAIL}. Az e-mail ugyanolyan érvényes.`,
      unmatched: (when: string | null) => `A nyilatkozatodat ezekkel az adatokkal nem tudtuk egyetlen rendeléshez sem hozzárendelni. Megőriztük${when ? ` (beérkezett: ${when})` : ''}, és kézzel ellenőrizzük. Kérjük, ellenőrizd a rendelésszámot, és ha a rendelésed linkje nélkül jöttél, azt az e-mail-címet add meg, amellyel fizettél. Írhatsz nekünk ide is: ${CONTACT_EMAIL}.`,
      // api/_lib/withdraw.py 409 no_order: nothing was stored, so nothing here may say it was kept
      no_order: `Nem találtunk ilyen számú rendelést; semmit nem rögzítettünk. Ellenőrizd a számot, vagy írj nekünk: ${CONTACT_EMAIL}.`,
      not_paid: 'Ezt a rendelést soha nem fizették ki, így nincs szerződés, amelytől el lehetne állni. Nem történt terhelés.',
      invalid: 'Kérjük, ellenőrizd a neved és az e-mail-címed, és próbáld újra.',
      paused: `Online elállást most nem tudunk fogadni. Kérjük, írd meg az elállásodat e-mailben: ${CONTACT_EMAIL}. Az e-mail ugyanolyan érvényes.`,
      too_many: `Ehhez a rendeléshez ma már több elállási nyilatkozat is érkezett. Ha valami hiányzik, kérjük, írj nekünk: ${CONTACT_EMAIL}.`,
      failed: `Az elállásodat nem sikerült elküldeni. Kérjük, próbáld újra, vagy írd meg az elállásodat e-mailben: ${CONTACT_EMAIL}. Az e-mail ugyanolyan érvényes.`,
    },
    done: {
      effectiveTitle: 'Megkaptuk az elállásodat',
      lapsedTitle: 'Megkaptuk a nyilatkozatodat',
      checking: 'Most kézzel ellenőrizzük a rendelésedet, és e-mailben megírjuk az eredményt.',
      received: (when: string) => `Az elállásodat ekkor kaptuk meg: ${when}.`,
      effective: 'Elálltál a szerződéstől. A fájlodat nem készítjük el.',
      refund: (amount: string) => `A kifizetett összeget (${amount}) legkésőbb 14 napon belül visszatérítjük arra a fizetési módra, amellyel fizettél.`,
      refundNoAmount: 'A kifizetett összeget legkésőbb 14 napon belül visszatérítjük arra a fizetési módra, amellyel fizettél.',
      refundBy: (amount: string, date: string) => `A kifizetett összeget (${amount}) legkésőbb ${date} napjáig visszatérítjük arra a fizetési módra, amellyel fizettél. Ez neked semmilyen díjjal nem jár.`,
      settling: 'Amikor elálltál, a fizetésed még feldolgozás alatt állt. Ha megérkezik hozzánk, legkésőbb 14 napon belül teljes egészében visszatérítjük arra a fizetési módra, amellyel fizettél.',
      refundStarted: (amount: string) => `Elindítottuk a visszatérítést (${amount}) arra a fizetési módra, amellyel fizettél. A bankodtól függően néhány napig tarthat, mire megérkezik.`,
      lapsed: 'A fájlod elkészítése már megkezdődött. A rendeléskor hozzájárultál, hogy azonnal elkezdjük, és tudomásul vetted, hogy a kezdéssel elveszíted az elállási jogodat, így ez a jog már megszűnt. A rendelésed érvényben marad: a fájlodat a rendelési oldaladon találod.',
      lapsedPeriod: 'Ennek a rendelésnek a 14 napos elállási határideje már lejárt, így a nyilatkozatod beérkezésekor az elállási jogod már megszűnt.',
      lapsedHelp: 'A nyilatkozatodat ennek ellenére személyesen is megnézzük, és e-mailben válaszolunk. Hibás fájl esetén a jogszabályon alapuló jogaidat ez nem érinti.',
      mailSent: (email: string) => `Az átvételi elismervényt elküldtük erre a címre: ${email}.`,
      mailRedirected: 'Az átvételi elismervényt arra az e-mail-címre küldtük, amellyel fizettél.',
      mailLater: (email: string) => `Az átvételi elismervényt most nem tudtuk elküldeni ide: ${email}. Amint lehet, elküldjük. Az elállásod a fenti időponttól érvényes.`,
      mailFailed: (email: string) => `Az átvételi elismervényt nem tudtuk elküldeni ide: ${email}. Az elállásodat a fenti időponttal rögzítettük. Kérjük, ellenőrizd ezt a címet, vagy másolatért írj nekünk: ${CONTACT_EMAIL}.`,
    },
    withdrawn: {
      title: 'Ettől a rendeléstől elálltál',
      body: (when: string) => `Az elállásodat ekkor kaptuk meg: ${when}. Ehhez a rendeléshez semmi nem készül.`,
      bodyNoTime: 'Megkaptuk az elállásodat. Ehhez a rendeléshez semmi nem készül.',
    },
    unpaid: 'Ez a rendelés nincs kifizetve, így nincs szerződés, amelytől el lehetne állni. Nem történt terhelés.',
  },
  contact: {
    lead: 'Kérdésed van a rendelésedről?',
    write: (email: string) => `Írj nekünk: ${email}`,
    subject: (o: string) => `SnapEyes-rendelés: ${o}`,
  },
};

// src/order/copy.ts mbOf, dateOf and whenOf in Hungarian. The amount of a paid order is shown in its own currency by
// src/shared/markets.ts money(): a HUF order as "6 990 Ft", a EUR one as "19,97 €".

/** Megabytes with one decimal, Hungarian style ("12,4"). */
export const mbOfHu = (bytes: number) =>
  new Intl.NumberFormat('hu-HU', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(bytes / 1_000_000);

/** A day ("2026. október 13."), the date a refund is due by: the copy adds „napjáig”. */
export const dateOfHu = (unixSeconds: number) =>
  new Intl.DateTimeFormat('hu-HU', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(unixSeconds * 1000));

/** A moment with its time zone ("2026. szeptember 29. 13:15 EEST"): the withdrawal receipt names the date and time. */
export const whenOfHu = (unixSeconds: number) =>
  new Intl.DateTimeFormat('hu-HU', {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short',
  }).format(new Date(unixSeconds * 1000));
