// Croatian ("hr") copy for /order: every key of src/order/copy.ts `en`, in the same structure. Polite plural "vi",
// lowercase inside sentences, and the words of /try and the landing page (umjetničko djelo, pregled, oko, datoteka).
// Eyes are ordinals ("2. oko"), as on /try (src/shared/hr.ts says why). The page words every server answer itself from
// its reason code, as in English.
// The right of withdrawal is Zakon o zaštiti potrošača's „pravo na jednostrani raskid ugovora“ (Directive 2011/83/EU,
// whose Croatian text says „pravo odustajanja“); the online withdrawal function's two button labels are
// src/shared/legal.ts WITHDRAWAL_ONLINE.hr (Art. 11a of the Directive: „odustati od ugovora“, „potvrditi odustajanje“
// or an equivalent unambiguous wording). The statement follows the model withdrawal form („Obrazac za jednostrani
// raskid ugovora“, Annex I(B) of the Directive) and must stay word for word the same as api/_lib/withdraw_hr.py
// STATEMENT_HR. Never "odustanite" for a cancel button here: that word is the Directive's word for withdrawing.
import type { OrderCopy } from './copy';
import { CONTACT_EMAIL } from '../landing/config';
import { dateHr, hrForm, mbHr, oci, whenHr } from '../shared/hr';

export const hr: OrderCopy = {
  lang: 'hr',
  meta: {
    title: 'Vaša narudžba | SnapEyes',
    description: 'Vaša SnapEyes narudžba: ovdje se izrađuje vaše umjetničko djelo od šarenice i ovdje ga možete preuzeti.',
  },
  switchLabel: 'Jezik',
  tag: 'Narudžba',
  title: 'Vaša narudžba',
  orderNo: (o: string) => `Narudžba ${o}`,
  loading: 'Otvaramo vašu narudžbu…',
  summary: {
    eyes: (n: number) => oci(n),
    paid: (amount: string) => `Plaćeno: ${amount}`,
    inscription: (s: string) => `Natpis: ${s}`,
  },
  unpaid: {
    title: 'Još nije plaćeno',
    body: 'Za ovu narudžbu još nismo primili uplatu.',
    confirming: 'Provjeravamo vaše plaćanje kod Stripea…',
    expired: 'Ova narudžba nije plaćena u roku od 24 sata, pa se više ne može platiti. Za nju ništa nije naplaćeno.',
    hint: 'Ako ste upravo platili, provjerite ponovno za trenutak. U suprotnom se možete vratiti u studio i ondje naručiti.',
    check: 'Provjerite ponovno',
    studio: 'Natrag u studio',
  },
  pending: {
    title: 'Vaše se plaćanje potvrđuje',
    body: 'Potvrda vašeg načina plaćanja traje malo dulje. Čim plaćanje bude potvrđeno, počinjemo s vašim umjetničkim djelom. Ova stranica sama provjerava ponovno.',
    // paid, but the order confirmation email (it confirms the withdrawal waiver) has not gone out yet: nothing is made
    mailTitle: 'Uplata je primljena',
    mailBody: 'Vaše je plaćanje potvrđeno. Šaljemo vam potvrdu narudžbe e-poštom i odmah nakon toga počinjemo s vašim umjetničkim djelom. Ova stranica sama provjerava ponovno.',
  },
  making: {
    title: 'Izrađujemo vaše umjetničko djelo',
    lead: 'Vaša se datoteka izrađuje u veličini od 4096 px, točno iz pregleda koje ste odobrili. To traje otprilike 30 sekundi po oku.',
    keepOpen: 'Ostavite ovu stranicu otvorenom dok preuzimanje ne bude spremno.',
    closeEmail: 'Ako je zatvorite, otvorite poveznicu iz svoje e-poruke da biste nastavili.',
    closeNoEmail: 'Ako je zatvorite, ponovno otvorite ovu stranicu na istoj adresi da biste nastavili.',
    // the server makes the order by itself (api/_lib/maker.py): the page may be closed
    serverOn: 'Vaše umjetničko djelo izrađujemo kod sebe, pa ovu stranicu možete zatvoriti.',
    serverEmail: 'Javit ćemo vam se e-poštom kad bude gotovo.',
    serverNoEmail: 'Kasnije ponovno otvorite ovu stranicu na istoj adresi da biste ga preuzeli.',
    eye: (i: number) => `${i}. oko`,
    done: 'Gotovo',
    working: 'U izradi…',
    waiting: 'Čeka',
    composing: 'Slažemo vaše umjetničko djelo…',
    part: (k: number, of: number) => `Slažemo vaše umjetničko djelo (${k} od ${of})…`,
    progress: (done: number, n: number) => `Gotovo: ${done} od ${n} ${hrForm(n, 'oka', 'oka', 'očiju')}`,
    elapsed: (s: number) => `${s} s`,
  },
  wait: {
    busy: (s: number) => `Studio je trenutačno zauzet. Ponovni pokušaj za ${s} s…`,
    network: (s: number) => `Veza je prekinuta. Ponovni pokušaj za ${s} s…`,
    rendering: (s: number) => `Ovo se oko već izrađuje. Ponovna provjera za ${s} s…`,
    confirming: (s: number) => `Ponovna provjera za ${s} s…`,
  },
  review: {
    title: 'Provjeravamo vaše umjetničko djelo',
    body: 'Vaše umjetničko djelo prije isporuke provjeravamo i ručno, a zatim vam pišemo e-poštom. Vi ne morate ništa poduzimati.',
  },
  ready: {
    title: 'Vaše je umjetničko djelo gotovo',
    download: 'Preuzmite datoteku pune veličine',
    open: 'Otvorite sliku',
    alt: 'Vaše SnapEyes umjetničko djelo',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} MB`,
    link: 'Poveznica za preuzimanje vrijedi 7 dana. Za novu poveznicu ovu stranicu možete ponovno otvoriti u bilo kojem trenutku: vašu datoteku čuvamo 12 mjeseci.',
    email: 'Poveznica na ovu stranicu nalazi se i u vašoj e-poruci.',
    bookmark: 'Sačuvajte adresu ove stranice: preko nje pristupate svojoj datoteci.',
  },
  deleted: {
    title: 'Datoteke su izbrisane',
    body: `Datoteke ove narudžbe su izbrisane. Pišite nam na ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Nešto je pošlo po zlu',
    bad_link: `Ova poveznica za narudžbu nije valjana. Ponovno otvorite poveznicu iz svoje e-poruke ili nam pišite na ${CONTACT_EMAIL}.`,
    missing: `Za ovu stranicu potrebna je cijela poveznica iz vaše e-poruke ili sa stranice za plaćanje. Ako je ne možete pronaći, pišite nam na ${CONTACT_EMAIL}.`,
    network: 'Nismo uspjeli doći do SnapEyesa. Provjerite internetsku vezu i pokušajte ponovno.',
    busy: 'Studio je trenutačno vrlo zauzet. Pokušajte ponovno za nekoliko minuta.',
    failed: `Kod nas je nešto pošlo po zlu. Pokušajte ponovno. Ako se to ponovi, pišite nam na ${CONTACT_EMAIL} i navedite broj narudžbe.`,
    retry: 'Pokušajte ponovno',
  },
  // The online withdrawal function (Art. 11a Directive 2011/83/EU as amended by Directive (EU) 2023/2673): a button with
  // the statutory words, a short statement form (name, contract, email for the receipt) and a second button with the
  // statutory words that sends it (./WithdrawPanel.tsx).
  withdraw: {
    heading: 'Jednostrani raskid ugovora',
    lead: 'Pri narudžbi ste pristali da odmah počnemo izrađivati vašu datoteku. Dok još nismo počeli, ovaj ugovor ovdje možete jednostrano raskinuti. Čim izrada započne, vaše pravo na jednostrani raskid ugovora prestaje.',
    acl: 'Ovo je pravo na jednostrani raskid ugovora prema potrošačkom pravu EU-a, za slučaj da se predomislite. Ono ne utječe na vaša prava prema australskom zakonu o zaštiti potrošača (Australian Consumer Law): ako je vaša datoteka neispravna ili ne odgovara opisu, pišite nam i navedite broj narudžbe.',
    info: 'Pravo na jednostrani raskid ugovora',
    formLead: (confirm: string) => `Provjerite svoje podatke. Gumbom „${confirm}“ šaljete nam ovu izjavu:`,
    // identical to api/_lib/withdraw_hr.py STATEMENT_HR ({order} there)
    statement: (o: string) => `Ovime izjavljujem da jednostrano raskidam ugovor o isporuci sljedećeg digitalnog sadržaja: umjetničko djelo SnapEyes, narudžba ${o}.`,
    statementNoOrder: 'Ovime izjavljujem da jednostrano raskidam ugovor o isporuci sljedećeg digitalnog sadržaja: umjetničko djelo SnapEyes, narudžba navedena u nastavku.',
    name: 'Vaše ime i prezime',
    email: 'Adresa e-pošte za potvrdu',
    emailHint: 'Na ovu adresu šaljemo potvrdu o primitku, s datumom i vremenom.',
    emailHintNoLink: 'Upišite adresu e-pošte kojom ste platili: po njoj vidimo da je narudžba vaša. Na ovu adresu šaljemo potvrdu o primitku, s datumom i vremenom.',
    order: 'Broj narudžbe',
    orderHint: 'Naći ćete ga u e-poruci s potvrdom narudžbe i na stranici narudžbe.',
    sending: 'Šaljemo vašu izjavu o raskidu…',
    cancel: 'Otkažite',
    back: 'Natrag na vašu narudžbu',
    invalid: {
      name: 'Upišite svoje ime i prezime.',
      email: 'Upišite valjanu adresu e-pošte.',
      order: 'Upišite broj narudžbe onako kako je naveden u e-poruci.',
    },
    errors: {
      network: 'Nismo uspjeli doći do SnapEyesa, pa ne znamo je li vaša izjava o raskidu stigla. Provjerite vezu i pokušajte ponovno: ponovno slanje ne šteti.',
      busy: `Naš je sustav trenutačno zauzet, pa vašu izjavu o raskidu nismo mogli zabilježiti. Pokušajte ponovno za trenutak ili nam izjavu o raskidu pošaljite na ${CONTACT_EMAIL}: e-poruka jednako vrijedi.`,
      unmatched: (when: string | null) => `Vašu izjavu s ovim podacima nismo mogli povezati ni s jednom narudžbom. Sačuvali smo je${when ? ` (primljena ${when})` : ''} i provjerit ćemo je ručno. Provjerite broj narudžbe i, ako niste došli preko poveznice na svoju narudžbu, upišite adresu e-pošte kojom ste platili. Možete nam pisati i na ${CONTACT_EMAIL}.`,
      // api/_lib/withdraw.py 409 no_order: nothing was stored, so nothing here may say it was kept
      no_order: `Narudžbu s tim brojem nismo pronašli; ništa nije zabilježeno. Provjerite broj ili nam pišite na ${CONTACT_EMAIL}.`,
      not_paid: 'Ova narudžba nikad nije plaćena, pa nema ugovora koji biste mogli raskinuti. Ništa nije naplaćeno.',
      invalid: 'Provjerite svoje ime i adresu e-pošte i pokušajte ponovno.',
      paused: `Izjave o raskidu trenutačno ne možemo primati putem interneta. Pošaljite nam izjavu o raskidu na ${CONTACT_EMAIL}: e-poruka jednako vrijedi.`,
      too_many: `Za ovu smo narudžbu danas već primili nekoliko izjava o jednostranom raskidu ugovora. Ako nešto nedostaje, pišite nam na ${CONTACT_EMAIL}.`,
      failed: `Vašu izjavu o raskidu nije bilo moguće poslati. Pokušajte ponovno ili nam izjavu o raskidu pošaljite na ${CONTACT_EMAIL}: e-poruka jednako vrijedi.`,
    },
    done: {
      effectiveTitle: 'Primili smo vašu izjavu o raskidu ugovora',
      lapsedTitle: 'Primili smo vašu izjavu',
      checking: 'Sada ćemo ručno provjeriti vašu narudžbu i rezultat vam poslati e-poštom.',
      received: (when: string) => `Vašu izjavu o raskidu primili smo ${when}.`,
      effective: 'Ugovor je raskinut. Vašu datoteku nećemo izraditi.',
      refund: (amount: string) => `Plaćeni iznos (${amount}) vratit ćemo vam na način plaćanja kojim ste platili, najkasnije u roku od 14 dana.`,
      refundNoAmount: 'Plaćeni iznos vratit ćemo vam na način plaćanja kojim ste platili, najkasnije u roku od 14 dana.',
      // date: "28. 10. 2026." (dateOfHr), its final dot is part of the date
      refundBy: (amount: string, date: string) => `Plaćeni iznos (${amount}) vratit ćemo vam najkasnije do ${date}, na način plaćanja kojim ste platili. Za to ne plaćate nikakve naknade.`,
      settling: 'Kad ste raskinuli ugovor, vaše se plaćanje još obrađivalo. Ako stigne do nas, vratit ćemo vam ga u cijelosti na način plaćanja kojim ste platili, najkasnije u roku od 14 dana.',
      refundStarted: (amount: string) => `Povrat iznosa (${amount}) na način plaćanja kojim ste platili je pokrenut. Ovisno o vašoj banci, može proći nekoliko dana dok stigne.`,
      lapsed: 'Izrada vaše datoteke već je bila započela. Pri narudžbi ste pristali da počnemo odmah i potvrdili da početkom izrade gubite pravo na jednostrani raskid ugovora, pa je to pravo već prestalo. Vaša narudžba ostaje na snazi: datoteku ćete pronaći na stranici svoje narudžbe.',
      lapsedPeriod: 'Rok od 14 dana za jednostrani raskid ugovora za ovu narudžbu već je bio istekao, pa je vaše pravo na jednostrani raskid prestalo prije nego što je vaša izjava stigla.',
      lapsedHelp: 'Vašu ćemo izjavu svejedno osobno pogledati i odgovoriti vam e-poštom. To ne utječe na vaša zakonska prava u slučaju neispravne datoteke.',
      mailSent: (email: string) => `Potvrda o primitku poslana je na ${email}.`,
      mailRedirected: 'Potvrda o primitku poslana je na adresu e-pošte kojom ste platili.',
      mailLater: (email: string) => `Potvrdu o primitku trenutačno nismo mogli poslati na ${email}. Poslat ćemo je čim bude moguće. Vaš raskid vrijedi od gore navedenog vremena.`,
      mailFailed: (email: string) => `Potvrdu o primitku nismo mogli poslati na ${email}. Vaš je raskid zabilježen s gore navedenim vremenom. Provjerite tu adresu ili nam za kopiju pišite na ${CONTACT_EMAIL}.`,
    },
    withdrawn: {
      title: 'Ugovor za ovu narudžbu jednostrano je raskinut',
      body: (when: string) => `Vašu izjavu o raskidu primili smo ${when}. Za ovu se narudžbu ništa ne izrađuje.`,
      bodyNoTime: 'Primili smo vašu izjavu o raskidu. Za ovu se narudžbu ništa ne izrađuje.',
    },
    unpaid: 'Ova narudžba nije plaćena, pa nema ugovora koji biste mogli raskinuti. Ništa nije naplaćeno.',
  },
  contact: {
    lead: 'Imate pitanja o narudžbi?',
    write: (email: string) => `Pišite nam na ${email}`,
    subject: (o: string) => `SnapEyes narudžba ${o}`,
  },
};

// The helpers of src/order/copy.ts for 'hr'. The amount of a paid order is shown in its own currency by
// src/shared/markets.ts money() ("24,97 €").
/** mbOf(bytes, 'hr'): "4,2" */
export const mbOfHr = (bytes: number) => mbHr(bytes);
/** dateOf(unixSeconds, 'hr'): "13. 10. 2026." (the date a refund is due by: "najkasnije do ...") */
export const dateOfHr = (unixSeconds: number) => dateHr(unixSeconds);
/** whenOf(unixSeconds, 'hr'): "29. 9. 2026. u 13:15 (CEST)" (the withdrawal receipt names date and time) */
export const whenOfHr = (unixSeconds: number) => whenHr(unixSeconds);
