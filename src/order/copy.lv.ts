// Latvian ("lv") copy for /order: every key of src/order/copy.ts `en`, in the same structure. Polite plural "jūs",
// lowercase inside sentences, and the words of /try and the landing page (mākslas darbs, priekšskatījums, acs, fails).
// Eyes are ordinals ("2. acs"), as on /try (src/shared/lv.ts says why). The page words every server answer itself from
// its reason code, as in English.
// The right of withdrawal is „atteikuma tiesības”, as the Latvian text of Directive 2011/83/EU has it; the online
// withdrawal function's two button labels are src/shared/legal.ts WITHDRAWAL_ONLINE.lv (Art. 11a of the Directive in
// its Latvian text: „Atteikties no līguma”, „Apstiprināt atteikumu”). The statement follows the model withdrawal form
// („Atteikuma veidlapas paraugs”, Annex I(B) of the Directive: „paziņoju, ka ... atteikties no manis noslēgtā ...
// līguma”) and must stay word for word the same as api/_lib/withdraw_lv.py STATEMENT_LV. A cancel button here is
// "Atcelt", never "Atteikties": that word is the Directive's word for withdrawing.
import type { OrderCopy } from './copy';
import { CONTACT_EMAIL } from '../landing/config';
import { acis, dateLv, lvForm, mbLv, whenLv } from '../shared/lv';

export const lv: OrderCopy = {
  lang: 'lv',
  meta: {
    title: 'Jūsu pasūtījums | SnapEyes',
    description: 'Jūsu SnapEyes pasūtījums: šeit tiek veidots jūsu varavīksnenes mākslas darbs, un šeit to varat lejupielādēt.',
  },
  switchLabel: 'Valoda',
  tag: 'Pasūtījums',
  title: 'Jūsu pasūtījums',
  orderNo: (o: string) => `Pasūtījums ${o}`,
  loading: 'Atveram jūsu pasūtījumu…',
  summary: {
    eyes: (n: number) => acis(n),
    paid: (amount: string) => `Samaksāts: ${amount}`,
    inscription: (s: string) => `Uzraksts: ${s}`,
  },
  unpaid: {
    title: 'Vēl nav samaksāts',
    body: 'Par šo pasūtījumu maksājumu vēl neesam saņēmuši.',
    confirming: 'Pārbaudām jūsu maksājumu pie Stripe…',
    expired: 'Šis pasūtījums netika apmaksāts 24 stundu laikā, tāpēc to vairs nevar apmaksāt. Par to nekas nav iekasēts.',
    hint: 'Ja tikko samaksājāt, pārbaudiet vēlreiz pēc brīža. Citādi varat atgriezties studijā un pasūtīt tur.',
    check: 'Pārbaudīt vēlreiz',
    studio: 'Atpakaļ uz studiju',
  },
  pending: {
    title: 'Jūsu maksājums tiek apstiprināts',
    body: 'Jūsu maksāšanas veida apstiprināšana aizņem nedaudz vairāk laika. Tiklīdz maksājums būs apstiprināts, sāksim veidot jūsu mākslas darbu. Šī lapa pati pārbauda vēlreiz.',
    // paid, but the order confirmation email (it confirms the withdrawal waiver) has not gone out yet: nothing is made
    mailTitle: 'Maksājums saņemts',
    mailBody: 'Jūsu maksājums ir apstiprināts. Nosūtām jums pasūtījuma apstiprinājumu e-pastā un uzreiz pēc tam sākam veidot jūsu mākslas darbu. Šī lapa pati pārbauda vēlreiz.',
  },
  making: {
    title: 'Veidojam jūsu mākslas darbu',
    lead: 'Jūsu fails tiek veidots 4096 px izmērā tieši no priekšskatījumiem, ko apstiprinājāt. Tas aizņem apmēram 30 sekundes katrai acij.',
    keepOpen: 'Lūdzu, atstājiet šo lapu atvērtu, līdz lejupielāde ir gatava.',
    closeEmail: 'Ja to aizvērsiet, atveriet saiti savā e-pastā, lai turpinātu.',
    closeNoEmail: 'Ja to aizvērsiet, atveriet šo lapu vēlreiz tajā pašā adresē, lai turpinātu.',
    // the server makes the order by itself (api/_lib/maker.py): the page may be closed
    serverOn: 'Jūsu mākslas darbu veidojam savā pusē, tāpēc šo lapu varat aizvērt.',
    serverEmail: 'Kad tas būs gatavs, nosūtīsim jums e-pastu.',
    serverNoEmail: 'Vēlāk atveriet šo lapu vēlreiz tajā pašā adresē, lai to lejupielādētu.',
    eye: (i: number) => `${i}. acs`,
    done: 'Gatava',
    working: 'Tiek veidota…',
    waiting: 'Gaida',
    composing: 'Saliekam jūsu mākslas darbu…',
    part: (k: number, of: number) => `Saliekam jūsu mākslas darbu (${k} no ${of})…`,
    progress: (done: number, n: number) => `Gatavs: ${done} no ${n} ${lvForm(n, 'acs', 'acīm', 'acīm')}`,
    elapsed: (s: number) => `${s} s`,
  },
  wait: {
    busy: (s: number) => `Studija pašlaik ir aizņemta. Mēģināsim vēlreiz pēc ${s} s…`,
    network: (s: number) => `Savienojums pārtrūka. Mēģināsim vēlreiz pēc ${s} s…`,
    rendering: (s: number) => `Šī acs jau tiek veidota. Pārbaudīsim vēlreiz pēc ${s} s…`,
    confirming: (s: number) => `Pārbaudīsim vēlreiz pēc ${s} s…`,
  },
  review: {
    title: 'Pārbaudām jūsu mākslas darbu',
    body: 'Pirms nodošanas jūsu mākslas darbu pārbaudām arī paši un pēc tam jums rakstām e-pastā. Jums nekas nav jādara.',
  },
  ready: {
    title: 'Jūsu mākslas darbs ir gatavs',
    download: 'Lejupielādēt pilna izmēra failu',
    open: 'Atvērt attēlu',
    alt: 'Jūsu SnapEyes mākslas darbs',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} MB`,
    link: 'Lejupielādes saite ir derīga 7 dienas. Lai saņemtu jaunu saiti, šo lapu varat atvērt vēlreiz jebkurā laikā: jūsu failu glabājam 12 mēnešus.',
    email: 'Saite uz šo lapu ir arī jūsu e-pastā.',
    bookmark: 'Saglabājiet šīs lapas adresi: ar to jūs piekļūstat savam failam.',
  },
  // the order's print (api/_lib/prints.py order_view): preparing, sent (in production), shipped (with its tracking link), canceled
  print: {
    title: 'Jūsu izdruka',
    preparing: 'Nodosim to ražošanā, tiklīdz jūsu fails būs gatavs.',
    // the same once the file is delivered already (a print bought after the artwork): it goes to production at once
    preparingNow: 'Tieši tagad nododam to ražošanā.',
    sent: 'Ražošanā. Kad to izsūtīsim, e-pastā nosūtīsim jums izsekošanas saiti.',
    shipped: 'Ceļā pie jums.',
    canceled: 'Šī izdruka ir atcelta. Rakstiet mums, ja jums ir jautājumi.',
    track: 'Izsekot sūtījumu',
  },
  // a print of the artwork, offered under a delivered artwork that has none (./PrintOffer.tsx; api/_lib/prints.py addon_offer, addon_buy and
  // addon_status): the card, the picker's words (src/try/PrintPick.tsx) and the way back from Stripe's payment page
  offer: {
    title: 'Jūsu mākslas darbs kā izdruka',
    lead: 'Šo mākslas darbu varam jums arī izdrukāt: aiz akrila stikla, uz spīdīga metāla, uz audekla, kā plakātu vai kā akrila bloku. Katru izdruku izgatavojam pēc pasūtījuma un nosūtām jums. Tas ir atsevišķs pasūtījums; jūsu fails paliek tāds, kāds tas ir.',
    product: 'Izdruka',
    choose: 'Izvēlieties izdruku',
    option: (name: string, price: string) => `${name}, ${price}`,
    country: 'Piegādes valsts',
    pick: 'Izvēlieties valsti',
    shipping: 'Piegāde',
    arrives: 'Sūtījums ir izsekojams.',
    mockAlt: (name: string) => `${name}: jūsu mākslas darba priekšskatījums`,
    total: 'Kopā',
    opening: 'Atveram maksājuma lapu…',
    consentMissing: 'Atzīmējiet rūtiņu par savu izdruku.',
    countryMissing: 'Izvēlieties savas izdrukas piegādes valsti.',
    footnote: 'Šī ir galīgā cena: neesam reģistrēti kā PVN maksātāji, tāpēc PVN netiek pieskaitīts. Piegādes adresi ievadīsiet maksājuma lapā.',
    changed: 'Izdrukas cena tikko mainījās. Apskatiet to vēlreiz un pēc tam nospiediet pogu.',
    unavailable: 'Izdrukas pašlaik nevar pasūtīt. Lūdzu, mēģiniet vēlāk.',
    cancelled: 'Jūs atgriezāties nesamaksājot, tāpēc nekas nav ieturēts. Izdruku šeit varat pasūtīt jebkurā laikā.',
    checking: 'Apstiprinām jūsu maksājumu par izdruku…',
    slow: 'Jūsu maksājuma apstiprināšana aizņem nedaudz vairāk laika. Jums nekas nav jādara: izdruka parādīsies šeit, tiklīdz maksājums būs apstiprināts, un apstiprinājumu nosūtīsim e-pastā.',
    processing: 'Jūsu maksājuma veida apstiprināšanai vajag nedaudz vairāk laika. Izdruku pasūtīsim, tiklīdz maksājums būs apstiprināts.',
    expired: 'Šī maksājuma lapa bija beigusies, tāpēc nekas nav ieturēts. Izdruku varat pasūtīt vēlreiz zemāk.',
    extra: 'Šim pasūtījumam jau bija izdruka, tāpēc šis otrais maksājums nebija vajadzīgs. Mēs to atmaksāsim. Rakstiet mums, ja tā vietā vēlējāties otru izdruku.',
    done: 'Paldies, jūsu izdruka ir pasūtīta.',
    doneEmail: 'Apstiprinājums jau ir ceļā pie jums e-pastā.',
  },
  deleted: {
    title: 'Faili ir dzēsti',
    body: `Šī pasūtījuma faili ir dzēsti. Rakstiet uz ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Kaut kas nogāja greizi',
    bad_link: `Šī pasūtījuma saite nav derīga. Atveriet saiti no sava e-pasta vēlreiz vai rakstiet uz ${CONTACT_EMAIL}.`,
    missing: `Šai lapai vajag pilnu saiti no jūsu e-pasta vai no maksājuma lapas. Ja nevarat to atrast, rakstiet uz ${CONTACT_EMAIL}.`,
    network: 'Neizdevās sasniegt SnapEyes. Pārbaudiet interneta savienojumu un mēģiniet vēlreiz.',
    busy: 'Studija pašlaik ir ļoti aizņemta. Mēģiniet vēlreiz pēc dažām minūtēm.',
    failed: `Mūsu pusē kaut kas nogāja greizi. Mēģiniet vēlreiz. Ja tas atkārtojas, rakstiet uz ${CONTACT_EMAIL} un norādiet pasūtījuma numuru.`,
    retry: 'Mēģināt vēlreiz',
  },
  // The online withdrawal function (Art. 11a Directive 2011/83/EU as amended by Directive (EU) 2023/2673): a button with
  // the statutory words, a short statement form (name, contract, email for the receipt) and a second button with the
  // statutory words that sends it (./WithdrawPanel.tsx).
  withdraw: {
    heading: 'Atteikšanās no līguma',
    lead: 'Pasūtot jūs piekritāt, ka jūsu failu sākam veidot uzreiz. Kamēr neesam sākuši, šeit varat atteikties no šī līguma. Tiklīdz veidošana ir sākta, jūsu atteikuma tiesības ir beigušās.',
    acl: 'Šīs ir atteikuma tiesības saskaņā ar ES patērētāju tiesībām gadījumam, ja pārdomājat. Tās neietekmē jūsu tiesības saskaņā ar Austrālijas patērētāju tiesību likumu (Australian Consumer Law): ja jūsu fails ir ar trūkumiem vai neatbilst aprakstam, rakstiet mums un norādiet pasūtījuma numuru.',
    us: 'Šīs ir atteikuma tiesības saskaņā ar ES patērētāju tiesībām gadījumam, ja pārdomājat. Tās neietekmē jūsu tiesības, ja fails ir ar trūkumiem: ja jūsu fails ir ar trūkumiem vai neatbilst aprakstam, rakstiet mums un norādiet pasūtījuma numuru.',
    info: 'Atteikuma tiesības',
    formLead: (confirm: string) => `Pārbaudiet savus datus. Ar pogu „${confirm}” jūs nosūtāt mums šo paziņojumu:`,
    // identical to api/_lib/withdraw_lv.py STATEMENT_LV ({order} there)
    statement: (o: string) => `Ar šo paziņoju, ka atsakos no manis noslēgtā līguma par šāda digitālā satura piegādi: SnapEyes mākslas darbs, pasūtījums ${o}.`,
    statementNoOrder: 'Ar šo paziņoju, ka atsakos no manis noslēgtā līguma par šāda digitālā satura piegādi: SnapEyes mākslas darbs, zemāk norādītais pasūtījums.',
    name: 'Jūsu vārds un uzvārds',
    email: 'E-pasta adrese apstiprinājumam',
    emailHint: 'Uz šo adresi nosūtīsim apstiprinājumu par saņemšanu ar datumu un laiku.',
    emailHintNoLink: 'Norādiet e-pasta adresi, ar kuru maksājāt: pēc tās redzam, ka pasūtījums ir jūsu. Uz šo adresi nosūtīsim apstiprinājumu par saņemšanu ar datumu un laiku.',
    order: 'Pasūtījuma numurs',
    orderHint: 'Tas ir pasūtījuma apstiprinājuma e-pastā un pasūtījuma lapā.',
    sending: 'Nosūtām jūsu paziņojumu par atteikumu…',
    cancel: 'Atcelt',
    back: 'Atpakaļ pie jūsu pasūtījuma',
    invalid: {
      name: 'Ievadiet savu vārdu un uzvārdu.',
      email: 'Ievadiet derīgu e-pasta adresi.',
      order: 'Ievadiet pasūtījuma numuru tā, kā tas norādīts e-pastā.',
    },
    errors: {
      network: 'Neizdevās sasniegt SnapEyes, tāpēc nezinām, vai jūsu atteikums ir saņemts. Pārbaudiet savienojumu un mēģiniet vēlreiz: atkārtota nosūtīšana nekaitē.',
      busy: `Mūsu sistēma pašlaik ir aizņemta, tāpēc jūsu atteikumu neizdevās reģistrēt. Mēģiniet vēlreiz pēc brīža vai nosūtiet atteikumu uz ${CONTACT_EMAIL}: e-pasts ir tikpat derīgs.`,
      unmatched: (when: string | null) => `Jūsu paziņojumu ar šiem datiem nevarējām sasaistīt ne ar vienu pasūtījumu. Esam to saglabājuši${when ? ` (saņemts ${when})` : ''} un pārbaudīsim paši. Pārbaudiet pasūtījuma numuru un, ja atnācāt bez saites uz savu pasūtījumu, norādiet e-pasta adresi, ar kuru maksājāt. Varat arī rakstīt uz ${CONTACT_EMAIL}.`,
      // api/_lib/withdraw.py 409 no_order: nothing was stored, so nothing here may say it was kept
      no_order: `Pasūtījumu ar šādu numuru neatradām; nekas nav reģistrēts. Pārbaudiet numuru vai rakstiet uz ${CONTACT_EMAIL}.`,
      not_paid: 'Šis pasūtījums nekad nav apmaksāts, tāpēc nav līguma, no kura atteikties. Nekas nav iekasēts.',
      invalid: 'Pārbaudiet savu vārdu un e-pasta adresi un mēģiniet vēlreiz.',
      paused: `Pašlaik nevaram pieņemt atteikumus tiešsaistē. Nosūtiet atteikumu uz ${CONTACT_EMAIL}: e-pasts ir tikpat derīgs.`,
      too_many: `Par šo pasūtījumu šodien jau esam saņēmuši vairākus paziņojumus par atteikumu. Ja kaut kā trūkst, rakstiet uz ${CONTACT_EMAIL}.`,
      failed: `Jūsu atteikumu neizdevās nosūtīt. Mēģiniet vēlreiz vai nosūtiet atteikumu uz ${CONTACT_EMAIL}: e-pasts ir tikpat derīgs.`,
    },
    done: {
      effectiveTitle: 'Jūsu atteikums ir saņemts',
      lapsedTitle: 'Jūsu paziņojums ir saņemts',
      checking: 'Tagad pārbaudīsim jūsu pasūtījumu paši un rezultātu nosūtīsim jums e-pastā.',
      received: (when: string) => `Jūsu atteikumu saņēmām ${when}.`,
      effective: 'Atteikums no līguma ir spēkā. Jūsu failu neveidosim.',
      refund: (amount: string) => `Samaksāto summu (${amount}) atmaksāsim ar to pašu maksāšanas līdzekli, ar kuru maksājāt, ne vēlāk kā 14 dienu laikā.`,
      refundNoAmount: 'Samaksāto summu atmaksāsim ar to pašu maksāšanas līdzekli, ar kuru maksājāt, ne vēlāk kā 14 dienu laikā.',
      // date: "28.10.2026." (dateOfLv), its final dot is part of the date, so a comma follows it, never a full stop
      refundBy: (amount: string, date: string) => `Samaksāto summu (${amount}) atmaksāsim ne vēlāk kā ${date}, izmantojot to pašu maksāšanas līdzekli, ar kuru maksājāt. Par to jums nekas nav jāmaksā.`,
      settling: 'Kad atteicāties no līguma, jūsu maksājums vēl tika apstrādāts. Ja tas mūs sasniegs, atmaksāsim to pilnībā ar to pašu maksāšanas līdzekli, ar kuru maksājāt, ne vēlāk kā 14 dienu laikā.',
      refundStarted: (amount: string) => `Summas (${amount}) atmaksa uz maksāšanas līdzekli, ar kuru maksājāt, ir sākta. Atkarībā no jūsu bankas var paiet dažas dienas, līdz tā pienāk.`,
      lapsed: 'Jūsu faila veidošana jau bija sākta. Pasūtot jūs piekritāt, ka sākam uzreiz, un apliecinājāt, ka zaudējat atteikuma tiesības, tiklīdz esam sākuši, tāpēc šīs tiesības jau bija beigušās. Jūsu pasūtījums paliek spēkā: failu atradīsiet savā pasūtījuma lapā.',
      lapsedPeriod: '14 dienu atteikuma termiņš šim pasūtījumam jau bija beidzies, tāpēc jūsu atteikuma tiesības bija beigušās, kad saņēmām jūsu paziņojumu.',
      lapsedHelp: 'Jūsu paziņojumu tomēr izskatīsim personīgi un atbildēsim jums e-pastā. Tas neietekmē jūsu likumīgās tiesības, ja failam ir trūkumi.',
      mailSent: (email: string) => `Apstiprinājums par saņemšanu ir nosūtīts uz ${email}.`,
      mailRedirected: 'Apstiprinājums par saņemšanu ir nosūtīts uz e-pasta adresi, ar kuru maksājāt.',
      mailLater: (email: string) => `Apstiprinājumu par saņemšanu pašlaik neizdevās nosūtīt uz ${email}. Nosūtīsim to, tiklīdz varēsim. Jūsu atteikums ir spēkā no augstāk norādītā laika.`,
      mailFailed: (email: string) => `Apstiprinājumu par saņemšanu neizdevās nosūtīt uz ${email}. Jūsu atteikums ir reģistrēts ar augstāk norādīto laiku. Pārbaudiet šo adresi vai rakstiet uz ${CONTACT_EMAIL}, lai saņemtu kopiju.`,
    },
    withdrawn: {
      title: 'Atteikums no šī pasūtījuma līguma ir spēkā',
      body: (when: string) => `Jūsu atteikumu saņēmām ${when}. Šim pasūtījumam nekas netiek veidots.`,
      bodyNoTime: 'Jūsu atteikumu esam saņēmuši. Šim pasūtījumam nekas netiek veidots.',
    },
    unpaid: 'Šis pasūtījums nav apmaksāts, tāpēc nav līguma, no kura atteikties. Nekas nav iekasēts.',
  },
  contact: {
    lead: 'Jautājumi par pasūtījumu?',
    write: (email: string) => `Rakstiet uz ${email}`,
    subject: (o: string) => `SnapEyes pasūtījums ${o}`,
  },
};

// The helpers of src/order/copy.ts for 'lv'. The amount of a paid order is shown in its own currency by
// src/shared/markets.ts money() ("24,97 €").
/** mbOf(bytes, 'lv'): "4,2" */
export const mbOfLv = (bytes: number) => mbLv(bytes);
/** dateOf(unixSeconds, 'lv'): "13.10.2026." (the date a refund is due by: "ne vēlāk kā ...") */
export const dateOfLv = (unixSeconds: number) => dateLv(unixSeconds);
/** whenOf(unixSeconds, 'lv'): "29.09.2026. plkst. 13:15 (EEST)" (the withdrawal receipt names date and time) */
export const whenOfLv = (unixSeconds: number) => whenLv(unixSeconds);
