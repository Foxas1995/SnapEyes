// Lithuanian /order copy: the twin of `en` in src/order/copy.ts, same keys, same order, same function signatures. Polite
// "Jūs" (capitalised in every form) and the words of /try and the landing page (kūrinys, peržiūra, akis, failas).
// The online withdrawal function's two button labels are src/shared/legal.ts WITHDRAWAL_ONLINE.lt (the words of CK
// 6.228(10) straipsnio 11 ir 13 dalys), which the legal pages quote.
import type { OrderCopy } from './copy';
import { CONTACT_EMAIL } from '../landing/config';
import { akys, dateLt, mbLt, whenLt } from '../shared/lt';

export const lt: OrderCopy = {
  lang: 'lt',
  meta: {
    title: 'Jūsų užsakymas | SnapEyes',
    description: 'Jūsų SnapEyes užsakymas: čia sukuriamas Jūsų rainelės kūrinys ir čia jį galite atsisiųsti.',
  },
  switchLabel: 'Kalba',
  tag: 'Private Atelier · užsakymas',
  title: 'Jūsų užsakymas',
  orderNo: (o: string) => `Užsakymas ${o}`,
  loading: 'Atidarome Jūsų užsakymą…',
  summary: {
    eyes: (n: number) => akys(n),
    paid: (amount: string) => `Sumokėta ${amount}`,
    inscription: (s: string) => `Užrašas: ${s}`,
  },
  layouts: {
    single: 'Viena akis', duo: 'Greta', fusion: 'Susiliejimas', triangle: 'Trikampis', row: 'Vienoje eilėje', grid: 'Tinklelis', galaxy: 'Galaktika',
  },
  unpaid: {
    title: 'Dar neapmokėta',
    body: 'Šio užsakymo apmokėjimo dar negavome.',
    confirming: 'Tikriname Jūsų mokėjimą per Stripe…',
    expired: 'Šis užsakymas nebuvo apmokėtas per 24 valandas, todėl jo apmokėti nebegalima. Pinigai už jį nenuskaityti.',
    hint: 'Jei ką tik sumokėjote, po akimirkos patikrinkite dar kartą. Kitu atveju galite grįžti į studiją ir užsisakyti iš ten.',
    check: 'Patikrinti dar kartą',
    studio: 'Grįžti į studiją',
  },
  pending: {
    title: 'Jūsų mokėjimas tvirtinamas',
    body: 'Jūsų pasirinkto mokėjimo būdo patvirtinimas užtrunka šiek tiek ilgiau. Jūsų kūrinį pradėsime kurti, kai tik mokėjimas bus patvirtintas. Šis puslapis pats patikrins dar kartą.',
    // paid, but the order confirmation email (it confirms the withdrawal waiver) has not gone out yet: nothing is made
    mailTitle: 'Mokėjimas gautas',
    mailBody: 'Jūsų mokėjimas patvirtintas. Siunčiame užsakymo patvirtinimą el. paštu ir iškart po to pradėsime kurti Jūsų kūrinį. Šis puslapis pats patikrins dar kartą.',
  },
  making: {
    title: 'Kuriame Jūsų kūrinį',
    lead: 'Jūsų failas kuriamas 4096 px dydžio būtent iš tų peržiūrų, kurias patvirtinote. Tai užtrunka maždaug 30 sekundžių vienai akiai.',
    keepOpen: 'Neuždarykite šio puslapio, kol failas bus paruoštas atsisiųsti.',
    closeEmail: 'Jei jį uždarysite, atidarykite nuorodą iš savo el. laiško ir tęskite.',
    closeNoEmail: 'Jei jį uždarysite, vėl atidarykite šį puslapį tuo pačiu adresu ir tęskite.',
    // the server makes the order by itself (api/_lib/maker.py): the page may be closed
    serverOn: 'Jūsų kūrinį kuriame savo pusėje, todėl šį puslapį galite uždaryti.',
    serverEmail: 'Kai jis bus paruoštas, parašysime Jums el. laišką.',
    serverNoEmail: 'Vėliau vėl atidarykite šį puslapį tuo pačiu adresu ir atsisiųskite kūrinį.',
    eye: (i: number) => `Akis ${i}`,
    done: 'Paruošta',
    working: 'Kuriama…',
    waiting: 'Laukia',
    composing: 'Komponuojame Jūsų kūrinį…',
    progress: (done: number, n: number) => `Paruošta akių: ${done} iš ${n}`,
    elapsed: (s: number) => `${s} s`,
  },
  wait: {
    busy: (s: number) => `Studija šiuo metu užimta. Bandysime dar kartą po ${s} s…`,
    network: (s: number) => `Ryšys nutrūko. Bandysime dar kartą po ${s} s…`,
    rendering: (s: number) => `Ši akis jau kuriama. Dar kartą patikrinsime po ${s} s…`,
    confirming: (s: number) => `Dar kartą patikrinsime po ${s} s…`,
  },
  review: {
    title: 'Tikriname Jūsų kūrinį',
    body: 'Prieš pristatydami Jūsų kūrinį, jį asmeniškai tikriname; kai baigsime, parašysime Jums el. laišką. Jums nieko daryti nereikia.',
  },
  ready: {
    title: 'Jūsų kūrinys paruoštas',
    download: 'Atsisiųsti viso dydžio failą',
    open: 'Atidaryti vaizdą',
    alt: 'Jūsų SnapEyes kūrinys',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} MB`,
    link: 'Atsisiuntimo nuoroda galioja 7 dienas. Šį puslapį bet kada galite atidaryti dar kartą ir gauti naują nuorodą: Jūsų failą saugome 12 mėnesių.',
    email: 'Šio puslapio nuoroda yra ir Jūsų el. laiške.',
    bookmark: 'Išsaugokite šio puslapio adresą: tai Jūsų prieiga prie failo.',
  },
  deleted: {
    title: 'Failai ištrinti',
    body: `Šio užsakymo failai ištrinti. Parašykite mums adresu ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Kažkas nepavyko',
    bad_link: `Ši užsakymo nuoroda negalioja. Dar kartą atidarykite nuorodą iš savo el. laiško arba parašykite mums adresu ${CONTACT_EMAIL}.`,
    missing: `Šiam puslapiui reikia visos nuorodos iš Jūsų el. laiško arba mokėjimo puslapio. Jei jos nerandate, parašykite mums adresu ${CONTACT_EMAIL}.`,
    network: 'Nepavyko susisiekti su SnapEyes. Patikrinkite interneto ryšį ir bandykite dar kartą.',
    busy: 'Studija šiuo metu labai užimta. Bandykite dar kartą po kelių minučių.',
    failed: `Mūsų pusėje kažkas nepavyko. Bandykite dar kartą. Jei tai pasikartos, parašykite mums adresu ${CONTACT_EMAIL} ir nurodykite užsakymo numerį.`,
    retry: 'Bandyti dar kartą',
  },
  // The online withdrawal function (CK 6.228(10) straipsnio 11-15 dalys; Art. 11a Directive 2011/83/EU): a button with
  // the statutory words, a short statement form (name, contract, email for the receipt) and a second button with the
  // statutory words that sends it (./WithdrawPanel.tsx).
  withdraw: {
    heading: 'Atsisakyti sutarties',
    lead: 'Užsakymo metu sutikote, kad Jūsų failą pradėtume kurti iš karto. Kol dar nepradėjome, šios sutarties galite atsisakyti čia. Kai tik kūrimas pradėtas, Jūsų teisė atsisakyti sutarties baigiasi.',
    acl: 'Tai teisė atsisakyti sutarties pagal ES vartotojų teisės aktus, kai apsigalvojate. Ji nedaro įtakos Jūsų teisėms pagal Australijos vartotojų įstatymą (Australian Consumer Law): jei Jūsų failas turi trūkumų arba neatitinka aprašymo, parašykite mums nurodydami užsakymo numerį.',
    info: 'Teisė atsisakyti sutarties',
    formLead: (confirm: string) => `Patikrinkite savo duomenis. Mygtuku „${confirm}“ išsiųsite mums šį pareiškimą:`,
    // identical to api/_lib/withdraw_lt.py STATEMENT_LT ({order} there)
    statement: (o: string) => `Pranešu, kad atsisakau sutarties, kurią sudariau dėl šio skaitmeninio turinio teikimo: SnapEyes kūrinys, užsakymas ${o}.`,
    statementNoOrder: 'Pranešu, kad atsisakau sutarties, kurią sudariau dėl šio skaitmeninio turinio teikimo: SnapEyes kūrinys, užsakymas, nurodytas toliau.',
    name: 'Jūsų vardas ir pavardė',
    email: 'El. pašto adresas patvirtinimui',
    emailHint: 'Šiuo adresu išsiųsime gavimo patvirtinimą su data ir laiku.',
    emailHintNoLink: 'Įveskite el. pašto adresą, kurį nurodėte mokėdami: pagal jį matysime, kad užsakymas Jūsų. Šiuo adresu išsiųsime gavimo patvirtinimą su data ir laiku.',
    order: 'Užsakymo numeris',
    orderHint: 'Jį rasite užsakymo patvirtinimo el. laiške ir užsakymo puslapyje.',
    sending: 'Siunčiame Jūsų pareiškimą…',
    cancel: 'Atšaukti',
    back: 'Grįžti į užsakymą',
    invalid: {
      name: 'Įveskite savo vardą ir pavardę.',
      email: 'Įveskite galiojantį el. pašto adresą.',
      order: 'Įveskite užsakymo numerį taip, kaip jis nurodytas el. laiške.',
    },
    errors: {
      network: 'Nepavyko susisiekti su SnapEyes, todėl nežinome, ar Jūsų pareiškimas mus pasiekė. Patikrinkite ryšį ir bandykite dar kartą: pakartotinis siuntimas nepakenks.',
      busy: `Mūsų sistema šiuo metu užimta, todėl Jūsų pareiškimo užregistruoti nepavyko. Po akimirkos bandykite dar kartą arba atsiųskite pareiškimą adresu ${CONTACT_EMAIL}: el. laiškas galioja lygiai taip pat.`,
      unmatched: (when: string | null) => `Pagal šiuos duomenis Jūsų pareiškimo nepavyko susieti su užsakymu. Jį išsaugojome${when ? ` (gautas ${when})` : ''} ir patikrinsime rankiniu būdu. Patikrinkite užsakymo numerį ir, jei atėjote ne per savo užsakymo nuorodą, įveskite el. pašto adresą, kurį nurodėte mokėdami. Taip pat galite parašyti mums adresu ${CONTACT_EMAIL}.`,
      // api/_lib/withdraw.py 409 no_order: nothing was stored, so nothing here may say it was kept
      no_order: `Užsakymo su šiuo numeriu neradome, todėl nieko neužregistravome. Patikrinkite numerį arba parašykite mums adresu ${CONTACT_EMAIL}.`,
      not_paid: 'Šis užsakymas nebuvo apmokėtas, todėl nėra sutarties, kurios būtų galima atsisakyti. Pinigai nenuskaityti.',
      invalid: 'Patikrinkite savo vardą, pavardę ir el. pašto adresą ir bandykite dar kartą.',
      paused: `Šiuo metu negalime priimti pareiškimų internetu. Atsiųskite pareiškimą adresu ${CONTACT_EMAIL}: el. laiškas galioja lygiai taip pat.`,
      too_many: `Šiandien dėl šio užsakymo jau gavome kelis pareiškimus apie sutarties atsisakymą. Jei ko nors trūksta, parašykite mums adresu ${CONTACT_EMAIL}.`,
      failed: `Jūsų pareiškimo išsiųsti nepavyko. Bandykite dar kartą arba atsiųskite pareiškimą adresu ${CONTACT_EMAIL}: el. laiškas galioja lygiai taip pat.`,
    },
    done: {
      effectiveTitle: 'Jūsų pareiškimas apie sutarties atsisakymą gautas',
      lapsedTitle: 'Jūsų pareiškimas gautas',
      checking: 'Dabar patikrinsime Jūsų užsakymą rankiniu būdu ir rezultatą atsiųsime el. paštu.',
      received: (when: string) => `Jūsų pareiškimą apie sutarties atsisakymą gavome ${when}.`,
      effective: 'Sutarties atsisakyta. Jūsų failo nekursime.',
      refund: (amount: string) => `Sumokėtą sumą (${amount}) grąžinsime tuo pačiu mokėjimo būdu, kuriuo mokėjote, ne vėliau kaip per 14 dienų.`,
      refundNoAmount: 'Sumokėtą sumą grąžinsime tuo pačiu mokėjimo būdu, kuriuo mokėjote, ne vėliau kaip per 14 dienų.',
      refundBy: (amount: string, date: string) => `Sumokėtą sumą (${amount}) ne vėliau kaip iki ${date} grąžinsime tuo pačiu mokėjimo būdu, kuriuo mokėjote. Jokių mokesčių už tai nemokėsite.`,
      settling: 'Kai atsisakėte sutarties, Jūsų mokėjimas dar buvo apdorojamas. Jei jis mus pasieks, visą sumą grąžinsime tuo pačiu mokėjimo būdu, kuriuo mokėjote, ne vėliau kaip per 14 dienų.',
      refundStarted: (amount: string) => `Pradėjome grąžinti sumą (${amount}) tuo pačiu mokėjimo būdu, kuriuo mokėjote. Pinigai gali ateiti per kelias dienas, tai priklauso nuo Jūsų banko.`,
      lapsed: 'Jūsų failo kūrimas jau buvo pradėtas. Užsakymo metu sutikote, kad pradėtume iš karto, ir pripažinote, kad pradėjus kurti netenkate teisės atsisakyti sutarties, todėl ši teisė jau buvo pasibaigusi. Jūsų užsakymas lieka galioti: failą rasite savo užsakymo puslapyje.',
      lapsedPeriod: 'Šio užsakymo 14 dienų sutarties atsisakymo terminas jau buvo pasibaigęs, todėl, kai gavome Jūsų pareiškimą, teisė atsisakyti sutarties jau buvo pasibaigusi.',
      lapsedHelp: 'Jūsų pareiškimą vis tiek asmeniškai peržiūrėsime ir atsakysime el. paštu. Tai neturi įtakos Jūsų įstatymų numatytoms teisėms, jei failas turi trūkumų.',
      mailSent: (email: string) => `Gavimo patvirtinimas išsiųstas adresu ${email}.`,
      mailRedirected: 'Gavimo patvirtinimas išsiųstas el. pašto adresu, kurį nurodėte apmokėjimo metu.',
      mailLater: (email: string) => `Šiuo metu nepavyko išsiųsti gavimo patvirtinimo adresu ${email}. Išsiųsime jį, kai tik bus įmanoma. Jūsų sutarties atsisakymas galioja nuo aukščiau nurodyto laiko.`,
      mailFailed: (email: string) => `Nepavyko išsiųsti gavimo patvirtinimo adresu ${email}. Jūsų sutarties atsisakymas užregistruotas nuo aukščiau nurodyto laiko. Patikrinkite šį adresą arba, jei norite kopijos, parašykite mums adresu ${CONTACT_EMAIL}.`,
    },
    withdrawn: {
      title: 'Šio užsakymo sutarties atsisakyta',
      body: (when: string) => `Jūsų pareiškimą apie sutarties atsisakymą gavome ${when}. Pagal šį užsakymą nieko nekuriama.`,
      bodyNoTime: 'Jūsų pareiškimą apie sutarties atsisakymą gavome. Pagal šį užsakymą nieko nekuriama.',
    },
    unpaid: 'Šis užsakymas neapmokėtas, todėl nėra sutarties, kurios būtų galima atsisakyti. Pinigai nenuskaityti.',
  },
  contact: {
    lead: 'Klausimų dėl užsakymo?',
    write: (email: string) => `Rašykite adresu ${email}`,
    subject: (o: string) => `SnapEyes užsakymas ${o}`,
  },
};

// The helpers of src/order/copy.ts for 'lt'.
/** mbOf(bytes, 'lt'): "4,2" */
export const mbOfLt = (bytes: number) => mbLt(bytes);
/** dateOf(unixSeconds, 'lt'): "2026 m. spalio 13 d." (the date a refund is due by: "ne vėliau kaip iki ...") */
export const dateOfLt = (unixSeconds: number) => dateLt(unixSeconds);
/** whenOf(unixSeconds, 'lt'): "2026 m. rugsėjo 29 d. 13:15 (GMT+3)" (the withdrawal receipt names date and time) */
export const whenOfLt = (unixSeconds: number) => whenLt(unixSeconds);
