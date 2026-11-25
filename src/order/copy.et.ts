// Estonian ("et") copy for /order: every key of src/order/copy.ts `en`, in the same structure. Informal singular "sina",
// and the words of /try and the landing page (kunstiteos, eelvaade, silm, fail). Eyes are numbered after the noun
// ("silm 2"), as on /try (src/shared/et.ts). The page words every server answer itself from its reason code, as in
// English.
// The right of withdrawal is „taganemisõigus“ and to withdraw is „lepingust taganema“ (Võlaõigusseadus § 56, the
// Estonian text of Directive 2011/83/EU); the online withdrawal function's two button labels are src/shared/legal.ts
// WITHDRAWAL_ONLINE.et (Võlaõigusseadus § 56⁴ lg 1 and 3, which transposes Art. 11a of the Directive: „Taganen
// lepingust“, „Kinnitan taganemise“). The statement follows the model withdrawal form („taganemisavalduse tüüpvorm“,
// justiitsministri 17.12.2013 määrus nr 41, lisa 1; Annex I(B) of the Directive) and must stay word for word the same
// as api/_lib/withdraw_et.py STATEMENT_ET. Never "tagane" or "taganemine" for a button that only closes the form:
// that button says „Katkesta“.
import type { OrderCopy } from './copy';
import { CONTACT_EMAIL } from '../landing/config';
import { dateEt, mbEt, silmad, whenEt } from '../shared/et';

export const et: OrderCopy = {
  lang: 'et',
  meta: {
    title: 'Sinu tellimus | SnapEyes',
    description: 'Sinu SnapEyesi tellimus: siin valmib sinu iirisekunstiteos ja siit saad selle alla laadida.',
  },
  switchLabel: 'Keel',
  tag: 'Tellimus',
  title: 'Sinu tellimus',
  orderNo: (o: string) => `Tellimus ${o}`,
  loading: 'Avame sinu tellimust…',
  summary: {
    eyes: (n: number) => silmad(n),
    paid: (amount: string) => `Makstud: ${amount}`,
    inscription: (s: string) => `Tekst: ${s}`,
  },
  unpaid: {
    title: 'Veel maksmata',
    body: 'Me ei ole selle tellimuse eest makset saanud.',
    confirming: 'Kontrollime sinu makset Stripe’is…',
    expired: 'Selle tellimuse eest ei makstud 24 tunni jooksul, seega ei saa selle eest enam maksta. Selle eest ei võetud raha.',
    hint: 'Kui maksid äsja, kontrolli hetke pärast uuesti. Muul juhul võid minna tagasi stuudiosse ja tellida sealt.',
    check: 'Kontrolli uuesti',
    studio: 'Tagasi stuudiosse',
  },
  pending: {
    title: 'Sinu makset kinnitatakse',
    body: 'Sinu makseviisi kinnitamine võtab veidi kauem aega. Alustame sinu kunstiteosega kohe, kui makse on kinnitatud. See leht kontrollib ise uuesti.',
    // paid, but the order confirmation email (it confirms the withdrawal waiver) has not gone out yet: nothing is made
    mailTitle: 'Makse on laekunud',
    mailBody: 'Sinu makse on kinnitatud. Saadame sulle e-kirjaga tellimuse kinnituse ja alustame kohe pärast seda sinu kunstiteosega. See leht kontrollib ise uuesti.',
  },
  making: {
    title: 'Valmistame sinu kunstiteost',
    lead: 'Sinu fail valmib suuruses 4096 px täpselt nende eelvaadete põhjal, mille heaks kiitsid. See võtab umbes 30 sekundit silma kohta.',
    keepOpen: 'Palun hoia see leht avatuna, kuni allalaadimine on valmis.',
    closeEmail: 'Kui sulged selle, ava jätkamiseks oma e-kirjas olev link.',
    closeNoEmail: 'Kui sulged selle, ava jätkamiseks see leht uuesti samal aadressil.',
    // the server makes the order by itself (api/_lib/maker.py): the page may be closed
    serverOn: 'Valmistame sinu kunstiteost enda juures, seega võid selle lehe sulgeda.',
    serverEmail: 'Saadame sulle e-kirja, kui see on valmis.',
    serverNoEmail: 'Allalaadimiseks ava see leht hiljem uuesti samal aadressil.',
    eye: (i: number) => `Silm ${i}`,
    done: 'Valmis',
    working: 'Töös…',
    waiting: 'Ootel',
    composing: 'Paneme sinu kunstiteost kokku…',
    part: (k: number, of: number) => `Paneme sinu kunstiteost kokku (${k}/${of})…`,
    // a count with a slash needs no noun form: "Silmi valmis: 2/3"
    progress: (done: number, n: number) => `Silmi valmis: ${done}/${n}`,
    elapsed: (s: number) => `${s} s`,
  },
  wait: {
    busy: (s: number) => `Stuudio on praegu hõivatud. Proovime uuesti ${s} s pärast…`,
    network: (s: number) => `Ühendus katkes. Proovime uuesti ${s} s pärast…`,
    rendering: (s: number) => `See silm on juba valmimas. Kontrollime uuesti ${s} s pärast…`,
    confirming: (s: number) => `Kontrollime uuesti ${s} s pärast…`,
  },
  review: {
    title: 'Kontrollime sinu kunstiteost',
    body: 'Kontrollime sinu kunstiteose enne üleandmist käsitsi üle ja saadame sulle e-kirja. Sa ei pea midagi tegema.',
  },
  ready: {
    title: 'Sinu kunstiteos on valmis',
    download: 'Laadi alla täissuuruses fail',
    open: 'Ava pilt',
    alt: 'Sinu SnapEyesi kunstiteos',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} MB`,
    link: 'Allalaadimislink kehtib 7 päeva. Uue lingi saamiseks ava see leht igal ajal uuesti: säilitame sinu faili 12 kuud.',
    email: 'Selle lehe link on ka sinu e-kirjas.',
    bookmark: 'Hoia selle lehe aadress alles: selle kaudu pääsed oma faili juurde.',
  },
  // the order's print (api/_lib/prints.py order_view): preparing, sent (in production), shipped (with its tracking link), canceled
  print: {
    title: 'Sinu trükitud pilt',
    preparing: 'Saadame selle tootmisse kohe, kui sinu fail on valmis.',
    // the same once the file is delivered already (a print bought after the artwork): it goes to production at once
    preparingNow: 'Saadame selle praegu tootmisse.',
    sent: 'Tootmises. Kui see teele läheb, saadame sulle e-kirjaga jälgimislingi.',
    shipped: 'Teel sinu juurde.',
    canceled: 'See trükitud pilt tühistati. Kui sul on küsimusi, kirjuta meile.',
    track: 'Jälgi saadetist',
  },
  // a print of the artwork, offered under a delivered artwork that has none (./PrintOffer.tsx; api/_lib/prints.py addon_offer, addon_buy and
  // addon_status): the card, the picker's words (src/try/PrintPick.tsx) and the way back from Stripe's payment page
  offer: {
    title: 'Sinu kunstiteos trükitud pildina',
    lead: 'Saame selle kunstiteose sulle ka välja trükkida: akrüülklaasi taha, läikivale metallile, lõuendile, plakatina või akrüülplokina. Samuti võtmehoidjana. Iga trükitud pilt valmistatakse sinu tellimuse järgi ja saadetakse sulle. See on eraldi tellimus; sinu fail jääb selliseks, nagu see on.',
    product: 'Trükitud pilt',
    choose: 'Vali trükitud pilt',
    option: (name: string, price: string) => `${name}, ${price}`,
    country: 'Tarneriik',
    pick: 'Vali riik',
    shipping: 'Tarne',
    arrives: 'Saadetis on jälgitav.',
    mockAlt: (name: string) => `${name}: sinu kunstiteose eelvaade`,
    total: 'Kokku',
    opening: 'Avame makselehte…',
    consentMissing: 'Palun märgi oma trükitud pildi kohta käiv kast.',
    countryMissing: 'Palun vali oma trükitud pildi tarneriik.',
    footnote: 'See on lõpphind: me ei ole käibemaksukohustuslane, seega käibemaksu ei lisandu. Tarneaadressi sisestad makselehel.',
    changed: 'Trükitud pildi hind muutus äsja. Palun vaata see uuesti üle ja vajuta siis nuppu.',
    unavailable: 'Trükitud pilte ei saa praegu tellida. Palun proovi hiljem uuesti.',
    cancelled: 'Tulid tagasi ilma maksmata, seega midagi ei võetud. Trükitud pildi saad siit tellida millal tahes.',
    checking: 'Kinnitame sinu makset trükitud pildi eest…',
    slow: 'Sinu makse kinnitamine võtab veidi kauem aega. Sa ei pea midagi tegema: sinu trükitud pilt ilmub siia kohe, kui makse on kinnitatud, ja kinnituse saadame sulle e-kirjaga.',
    processing: 'Sinu makseviisi kinnitamine võtab veidi kauem aega. Tellime sinu trükitud pildi kohe, kui makse on kinnitatud.',
    expired: 'See makseleht oli aegunud, seega midagi ei võetud. Trükitud pildi saad allpool uuesti tellida.',
    extra: 'Sellel tellimusel oli juba trükitud pilt, seega seda teist makset ei olnud vaja. Tagastame selle. Kirjuta meile, kui soovisid hoopis teist trükitud pilti.',
    done: 'Aitäh, sinu trükitud pilt on tellitud.',
    doneEmail: 'Kinnitus on e-kirjaga teel sinu juurde.',
  },
  deleted: {
    title: 'Failid on kustutatud',
    body: `Selle tellimuse failid on kustutatud. Kirjuta aadressile ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Midagi läks valesti',
    bad_link: `See tellimuse link ei kehti. Palun ava oma e-kirjas olev link uuesti või kirjuta aadressile ${CONTACT_EMAIL}.`,
    missing: `See leht vajab täielikku linki sinu e-kirjast või makselehelt. Kui sa seda ei leia, kirjuta aadressile ${CONTACT_EMAIL}.`,
    network: 'Me ei saanud SnapEyesiga ühendust. Palun kontrolli internetiühendust ja proovi uuesti.',
    busy: 'Stuudio on praegu väga hõivatud. Palun proovi mõne minuti pärast uuesti.',
    failed: `Meie poolel läks midagi valesti. Palun proovi uuesti. Kui see kordub, kirjuta aadressile ${CONTACT_EMAIL} ja lisa oma tellimuse number.`,
    retry: 'Proovi uuesti',
  },
  // The online withdrawal function (Art. 11a Directive 2011/83/EU as amended by Directive (EU) 2023/2673): a button with
  // the statutory words, a short statement form (name, contract, email for the receipt) and a second button with the
  // statutory words that sends it (./WithdrawPanel.tsx).
  withdraw: {
    heading: 'Lepingust taganemine',
    lead: 'Tellimisel nõustusid, et hakkame sinu faili kohe valmistama. Kuni me ei ole alustanud, saad sellest lepingust siin taganeda. Kui valmistamine on alanud, on sinu taganemisõigus lõppenud.',
    leadOpen: 'Sellest lepingust saad siin taganeda 14 päeva jooksul pärast tellimust, isegi kui oled oma faili juba kätte saanud, ja saad tagasi kogu makstud summa.',
    acl: 'See on ELi tarbijaõigusest tulenev taganemisõigus juhuks, kui muudad meelt. See ei mõjuta sinu õigusi Austraalia tarbijaõiguse (Australian Consumer Law) alusel: kui sinu fail on vigane või ei vasta kirjeldusele, kirjuta meile ja lisa oma tellimuse number.',
    us: 'See on ELi tarbijaõigusest tulenev taganemisõigus juhuks, kui muudad meelt. See ei mõjuta sinu õigusi juhul, kui fail on vigane: kui sinu fail on vigane või ei vasta kirjeldusele, kirjuta meile ja lisa oma tellimuse number.',
    info: 'Taganemisõigus',
    formLead: (confirm: string) => `Palun kontrolli oma andmeid. Nupuga „${confirm}“ saadad meile selle avalduse:`,
    // identical to api/_lib/withdraw_et.py STATEMENT_ET ({order} there)
    statement: (o: string) => `Käesolevaga taganen lepingust, mille esemeks on järgmise digitaalse sisu üleandmine: SnapEyesi kunstiteos, tellimus ${o}.`,
    statementNoOrder: 'Käesolevaga taganen lepingust, mille esemeks on järgmise digitaalse sisu üleandmine: SnapEyesi kunstiteos, allpool nimetatud tellimus.',
    name: 'Sinu nimi',
    email: 'E-posti aadress kinnituse jaoks',
    emailHint: 'Saadame kättesaamise kinnituse koos kuupäeva ja kellaajaga sellele aadressile.',
    emailHintNoLink: 'Palun kasuta e-posti aadressi, millega maksid: see näitab meile, et tellimus on sinu oma. Saadame kättesaamise kinnituse koos kuupäeva ja kellaajaga sellele aadressile.',
    order: 'Tellimuse number',
    orderHint: 'Leiad selle tellimuse kinnituskirjast ja tellimuse lehelt.',
    sending: 'Saadame sinu taganemisavaldust…',
    cancel: 'Katkesta',
    back: 'Tagasi sinu tellimuse juurde',
    invalid: {
      name: 'Palun sisesta oma nimi.',
      email: 'Palun sisesta kehtiv e-posti aadress.',
      order: 'Palun sisesta tellimuse number nii, nagu see on sinu e-kirjas.',
    },
    errors: {
      network: 'Me ei saanud SnapEyesiga ühendust, seega ei tea me, kas sinu taganemisavaldus jõudis kohale. Palun kontrolli ühendust ja proovi uuesti: uuesti saatmine ei tee kahju.',
      busy: `Meie süsteem on praegu hõivatud, seega ei saanud sinu taganemisavaldust salvestada. Palun proovi hetke pärast uuesti või saada oma taganemisavaldus aadressile ${CONTACT_EMAIL}: e-kiri kehtib samamoodi.`,
      unmatched: (when: string | null) => `Me ei saanud sinu avaldust nende andmete põhjal ühegi tellimusega kokku viia. Jätsime selle alles${when ? ` (kätte saadud ${when})` : ''} ja kontrollime selle käsitsi üle. Palun kontrolli tellimuse numbrit ja kui tulid ilma oma tellimuse lingita, kasuta e-posti aadressi, millega maksid. Võid kirjutada ka aadressile ${CONTACT_EMAIL}.`,
      // api/_lib/withdraw.py 409 no_order: nothing was stored, so nothing here may say it was kept
      no_order: `Me ei leidnud selle numbriga tellimust; midagi ei salvestatud. Kontrolli numbrit või kirjuta aadressile ${CONTACT_EMAIL}.`,
      not_paid: 'Selle tellimuse eest ei ole kunagi makstud, seega ei ole lepingut, millest taganeda. Raha ei võetud.',
      invalid: 'Palun kontrolli oma nime ja e-posti aadressi ning proovi uuesti.',
      paused: `Me ei saa praegu veebis taganemisavaldusi vastu võtta. Palun saada oma taganemisavaldus aadressile ${CONTACT_EMAIL}: e-kiri kehtib samamoodi.`,
      too_many: `Oleme selle tellimuse kohta täna juba mitu taganemisavaldust saanud. Kui midagi on puudu, kirjuta palun aadressile ${CONTACT_EMAIL}.`,
      failed: `Sinu taganemisavaldust ei õnnestunud saata. Palun proovi uuesti või saada oma taganemisavaldus aadressile ${CONTACT_EMAIL}: e-kiri kehtib samamoodi.`,
    },
    done: {
      effectiveTitle: 'Sinu taganemisavaldus on kätte saadud',
      lapsedTitle: 'Sinu avaldus on kätte saadud',
      checking: 'Kontrollime nüüd sinu tellimuse käsitsi üle ja saadame sulle tulemuse e-kirjaga.',
      received: (when: string) => `Saime sinu taganemisavalduse kätte ${when}.`,
      effective: 'Oled lepingust taganenud. Me ei valmista sinu faili.',
      refund: (amount: string) => `Tagastame sinu makstud summa (${amount}) samale makseviisile, mida kasutasid, hiljemalt 14 päeva jooksul.`,
      refundNoAmount: 'Tagastame sinu makstud summa samale makseviisile, mida kasutasid, hiljemalt 14 päeva jooksul.',
      // date: "28.10.2026" (dateOfEt)
      refundBy: (amount: string, date: string) => `Tagastame sinu makstud summa (${amount}) samale makseviisile, mida kasutasid, hiljemalt ${date}. Sa ei maksa selle eest mingeid tasusid.`,
      settling: 'Kui sa lepingust taganesid, oli sinu makse veel töötlemisel. Kui see meieni jõuab, tagastame selle täies ulatuses samale makseviisile, mida kasutasid, hiljemalt 14 päeva jooksul.',
      refundStarted: (amount: string) => `Summa ${amount} tagastamine sinu kasutatud makseviisile on algatatud. Sõltuvalt sinu pangast võib selle laekumine võtta mõne päeva.`,
      lapsed: 'Sinu faili valmistamine oli juba alanud. Tellimisel nõustusid, et alustame kohe, ja kinnitasid, et kaotad taganemisõiguse, kui oleme alustanud, seega oli see õigus juba lõppenud. Sinu tellimus jääb kehtima: faili leiad oma tellimuse lehelt.',
      lapsedPeriod: 'Selle tellimuse 14-päevane taganemistähtaeg oli juba lõppenud, seega oli sinu taganemisõigus avalduse saabumise ajaks lõppenud.',
      lapsedHelp: 'Vaatame sinu avalduse siiski isiklikult üle ja vastame sulle e-kirjaga. See ei mõjuta sinu seadusest tulenevaid õigusi puudusega faili korral.',
      mailSent: (email: string) => `Kättesaamise kinnitus on teel aadressile ${email}.`,
      mailRedirected: 'Kättesaamise kinnitus on teel e-posti aadressile, millega maksid.',
      mailLater: (email: string) => `Me ei saanud kättesaamise kinnitust praegu aadressile ${email} saata. Saadame selle niipea, kui saame. Sinu taganemine kehtib ülal näidatud ajast.`,
      mailFailed: (email: string) => `Me ei saanud kättesaamise kinnitust aadressile ${email} saata. Sinu taganemine on kirja pandud ülal näidatud ajaga. Palun kontrolli seda aadressi või kirjuta koopia saamiseks aadressile ${CONTACT_EMAIL}.`,
    },
    withdrawn: {
      title: 'Sellest tellimusest on taganetud',
      body: (when: string) => `Sinu taganemisavaldus saadi kätte ${when}. Selle tellimuse jaoks ei valmistata midagi.`,
      bodyNoTime: 'Sinu taganemisavaldus on kätte saadud. Selle tellimuse jaoks ei valmistata midagi.',
    },
    unpaid: 'Selle tellimuse eest ei ole makstud, seega ei ole lepingut, millest taganeda. Raha ei võetud.',
  },
  contact: {
    lead: 'Küsimusi tellimuse kohta?',
    write: (email: string) => `Kirjuta aadressile ${email}`,
    subject: (o: string) => `SnapEyesi tellimus ${o}`,
  },
};

// The helpers of src/order/copy.ts for 'et'. The amount of a paid order is shown in its own currency by
// src/shared/markets.ts money() ("24,97 €").
/** mbOf(bytes, 'et'): "4,2" */
export const mbOfEt = (bytes: number) => mbEt(bytes);
/** dateOf(unixSeconds, 'et'): "13.10.2026" (the date a refund is due by: "hiljemalt ...") */
export const dateOfEt = (unixSeconds: number) => dateEt(unixSeconds);
/** whenOf(unixSeconds, 'et'): "29.09.2026 kell 13:15 (EEST)" (the withdrawal receipt names date and time) */
export const whenOfEt = (unixSeconds: number) => whenEt(unixSeconds);
