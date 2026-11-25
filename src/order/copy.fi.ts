// Finnish ("fi") copy for /order: every key of src/order/copy.ts `en`, in the same structure. Informal singular "sinä",
// and the words of /try and the landing page (taideteos, esikatselu, silmä, tiedosto). Eyes are "silmä 2", as on /try
// (src/shared/fi.ts). The page words every server answer itself from its reason code, as in English.
// The right of withdrawal is "peruuttamisoikeus" (Directive 2011/83/EU in its official Finnish text, and
// kuluttajansuojalaki 6 luku), the withdrawal period "peruuttamisaika", the statement "peruuttamisilmoitus", the
// acknowledgement of receipt "vastaanottoilmoitus" (Art. 11a(4)). The online withdrawal function's two button labels are
// src/shared/legal.ts WITHDRAWAL_ONLINE.fi (Art. 11a of the Directive: "Peruuta sopimus tästä", "Vahvista peruuttaminen").
// The statement follows the model withdrawal form ("Malliperuuttamislomake", Annex I(B) of the Directive: "Ilmoitan,
// että haluan peruuttaa tekemäni sopimuksen, joka koskee ...") and must stay word for word the same as
// api/_lib/withdraw_fi.py STATEMENT_FI. Never "Peruuta" for a cancel button here: that word is the Directive's word
// for withdrawing, so the form's cancel button says "Keskeytä".
import type { OrderCopy } from './copy';
import { CONTACT_EMAIL } from '../landing/config';
import { dateFi, fiForm, mbFi, silmat, whenFi } from '../shared/fi';

export const fi: OrderCopy = {
  lang: 'fi',
  meta: {
    title: 'Tilauksesi | SnapEyes',
    description: 'SnapEyes-tilauksesi: iiristaideteoksesi tehdään täällä, ja täältä voit ladata sen.',
  },
  switchLabel: 'Kieli',
  tag: 'Tilaus',
  title: 'Tilauksesi',
  orderNo: (o: string) => `Tilaus ${o}`,
  loading: 'Avaamme tilaustasi…',
  summary: {
    eyes: (n: number) => silmat(n),
    paid: (amount: string) => `Maksettu ${amount}`,
    inscription: (s: string) => `Teksti: ${s}`,
  },
  unpaid: {
    title: 'Ei vielä maksettu',
    body: 'Emme ole saaneet maksua tästä tilauksesta.',
    confirming: 'Tarkistamme maksuasi Stripeltä…',
    expired: 'Tätä tilausta ei maksettu 24 tunnin kuluessa, joten sitä ei voi enää maksaa. Siitä ei veloitettu mitään.',
    hint: 'Jos maksoit juuri äsken, tarkista hetken kuluttua uudelleen. Muussa tapauksessa voit palata studioon ja tilata sieltä.',
    check: 'Tarkista uudelleen',
    studio: 'Takaisin studioon',
  },
  pending: {
    title: 'Maksuasi vahvistetaan',
    body: 'Maksutapasi vahvistaminen kestää hieman kauemmin. Aloitamme taideteoksesi heti, kun maksu on vahvistettu. Tämä sivu tarkistaa tilanteen itse uudelleen.',
    // paid, but the order confirmation email (it confirms the withdrawal waiver) has not gone out yet: nothing is made
    mailTitle: 'Maksu vastaanotettu',
    mailBody: 'Maksusi on vahvistettu. Lähetämme tilausvahvistuksen sähköpostiisi ja aloitamme taideteoksesi heti sen jälkeen. Tämä sivu tarkistaa tilanteen itse uudelleen.',
  },
  making: {
    title: 'Teemme taideteostasi',
    lead: 'Tiedostosi tehdään 4096 px:n koossa täsmälleen hyväksymistäsi esikatseluista. Tämä kestää noin 30 sekuntia silmää kohden.',
    keepOpen: 'Pidä tämä sivu auki, kunnes latauksesi on valmis.',
    closeEmail: 'Jos suljet sen, jatka avaamalla sähköpostissasi oleva linkki.',
    closeNoEmail: 'Jos suljet sen, jatka avaamalla tämä sivu uudelleen samasta osoitteesta.',
    // the server makes the order by itself (api/_lib/maker.py): the page may be closed
    serverOn: 'Teemme taideteostasi meidän päässämme, joten voit sulkea tämän sivun.',
    serverEmail: 'Lähetämme sinulle sähköpostia, kun se on valmis.',
    serverNoEmail: 'Avaa tämä sivu myöhemmin uudelleen samasta osoitteesta, niin voit ladata sen.',
    eye: (i: number) => `Silmä ${i}`,
    done: 'Valmis',
    working: 'Työn alla…',
    waiting: 'Odottaa',
    composing: 'Koostamme taideteostasi…',
    part: (k: number, of: number) => `Koostamme taideteostasi (${k}/${of})…`,
    progress: (done: number, n: number) => `${done}/${n} ${fiForm(n, 'silmä', 'silmää')} valmiina`,
    elapsed: (s: number) => `${s} s`,
  },
  wait: {
    busy: (s: number) => `Studiossa on juuri nyt ruuhkaa. Yritämme uudelleen ${s} s:n kuluttua…`,
    network: (s: number) => `Yhteys katkesi. Yritämme uudelleen ${s} s:n kuluttua…`,
    rendering: (s: number) => `Tätä silmää tehdään jo. Tarkistamme uudelleen ${s} s:n kuluttua…`,
    confirming: (s: number) => `Tarkistamme uudelleen ${s} s:n kuluttua…`,
  },
  review: {
    title: 'Tarkistamme taideteostasi',
    body: 'Tarkistamme taideteoksesi käsin ennen toimitusta ja lähetämme sinulle sähköpostia. Sinun ei tarvitse tehdä mitään.',
  },
  ready: {
    title: 'Taideteoksesi on valmis',
    download: 'Lataa täysikokoinen tiedosto',
    open: 'Avaa kuva',
    alt: 'SnapEyes-taideteoksesi',
    details: (w: number, h: number, mb: string) => `JPEG, ${w} × ${h} px, ${mb} Mt`,
    link: 'Latauslinkki on voimassa 7 päivää. Saat uuden linkin avaamalla tämän sivun uudelleen milloin tahansa: säilytämme tiedostoasi 12 kuukautta.',
    email: 'Linkki tälle sivulle on myös sähköpostissasi.',
    bookmark: 'Pidä tämän sivun osoite tallessa: sen kautta pääset tiedostoosi.',
  },
  // the order's print (api/_lib/prints.py order_view): preparing, sent (in production), shipped (with its tracking link), canceled
  print: {
    title: 'Tulosteesi',
    preparing: 'Lähetämme sen tuotantoon heti, kun tiedostosi on valmis.',
    // the same once the file is delivered already (a print bought after the artwork): it goes to production at once
    preparingNow: 'Lähetämme sen nyt tuotantoon.',
    sent: 'Tuotannossa. Lähetämme seurantalinkin sähköpostiisi, kun tuloste lähtee matkaan.',
    shipped: 'Matkalla luoksesi.',
    canceled: 'Tämä tuloste peruttiin. Kirjoita meille, jos sinulla on kysyttävää.',
    track: 'Seuraa lähetystä',
  },
  // a print of the artwork, offered under a delivered artwork that has none (./PrintOffer.tsx; api/_lib/prints.py addon_offer, addon_buy and
  // addon_status): the card, the picker's words (src/try/PrintPick.tsx) and the way back from Stripe's payment page
  offer: {
    title: 'Taideteoksesi tulosteena',
    lead: 'Voimme myös tulostaa tämän taideteoksen sinulle: akryylilasin taakse, kiiltävälle metallille, canvakselle, julisteeksi tai akryylilohkoksi. Myös avaimenperäksi. Jokainen tuloste tehdään tilauksesi mukaan ja lähetetään sinulle. Se on erillinen tilaus; tiedostosi pysyy ennallaan.',
    product: 'Tuloste',
    choose: 'Valitse tuloste',
    option: (name: string, price: string) => `${name}, ${price}`,
    country: 'Toimitusmaa',
    pick: 'Valitse maa',
    shipping: 'Toimitus',
    arrives: 'Lähetystä voi seurata.',
    mockAlt: (name: string) => `${name}: esikatselu taideteoksestasi`,
    total: 'Yhteensä',
    opening: 'Avaamme maksusivua…',
    consentMissing: 'Rastita tulostettasi koskeva ruutu.',
    countryMissing: 'Valitse tulosteesi toimitusmaa.',
    footnote: 'Tämä on lopullinen hinta: emme ole arvonlisäverovelvollisia, joten arvonlisäveroa ei lisätä. Annat toimitusosoitteen maksusivulla.',
    changed: 'Tulosteen hinta muuttui juuri äsken. Tarkista se uudelleen ja paina sitten painiketta.',
    unavailable: 'Tulosteita ei voi tilata juuri nyt. Yritä myöhemmin uudelleen.',
    cancelled: 'Palasit maksamatta, joten mitään ei veloitettu. Voit tilata tulosteen täältä milloin tahansa.',
    checking: 'Vahvistamme tulosteesi maksua…',
    slow: 'Maksusi vahvistaminen kestää hieman kauemmin. Sinun ei tarvitse tehdä mitään: tulosteesi näkyy täällä, kun maksu on vahvistettu, ja lähetämme vahvistuksen sähköpostiisi.',
    processing: 'Maksutapasi vahvistaminen kestää hieman kauemmin. Tilaamme tulosteesi heti, kun maksu on vahvistettu.',
    expired: 'Tuo maksusivu oli vanhentunut, joten mitään ei veloitettu. Voit tilata tulosteen uudelleen alta.',
    extra: 'Tässä tilauksessa oli jo tuloste, joten tätä toista maksua ei tarvittu. Palautamme sen. Kirjoita meille, jos halusit sen sijaan toisen tulosteen.',
    done: 'Kiitos, tulosteesi on tilattu.',
    doneEmail: 'Vahvistus on matkalla sähköpostiisi.',
  },
  deleted: {
    title: 'Tiedostot poistettu',
    body: `Tämän tilauksen tiedostot on poistettu. Kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
  },
  errors: {
    title: 'Jokin meni vikaan',
    bad_link: `Tämä tilauslinkki ei kelpaa. Avaa sähköpostissasi oleva linkki uudelleen tai kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
    missing: `Tämä sivu tarvitsee koko linkin, joka on sähköpostissasi tai maksusivulla. Jos et löydä sitä, kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
    network: 'Emme saaneet yhteyttä SnapEyesiin. Tarkista verkkoyhteytesi ja yritä uudelleen.',
    busy: 'Studiossa on juuri nyt paljon ruuhkaa. Yritä muutaman minuutin kuluttua uudelleen.',
    failed: `Meidän päässämme meni jokin vikaan. Yritä uudelleen. Jos sama toistuu, kirjoita osoitteeseen ${CONTACT_EMAIL} ja kerro tilausnumerosi.`,
    retry: 'Yritä uudelleen',
  },
  // The online withdrawal function (Art. 11a Directive 2011/83/EU as amended by Directive (EU) 2023/2673): a button with
  // the statutory words, a short statement form (name, contract, email for the receipt) and a second button with the
  // statutory words that sends it (./WithdrawPanel.tsx).
  withdraw: {
    heading: 'Sopimuksen peruuttaminen',
    lead: 'Tilatessasi hyväksyit, että alamme tehdä tiedostoasi heti. Niin kauan kuin emme ole aloittaneet, voit peruuttaa tämän sopimuksen tässä. Kun tekeminen on alkanut, peruuttamisoikeutesi on päättynyt.',
    acl: 'Tämä on EU:n kuluttajalainsäädännön mukainen peruuttamisoikeus siltä varalta, että muutat mielesi. Se ei vaikuta Australian kuluttajalain (Australian Consumer Law) mukaisiin oikeuksiisi: jos tiedostossasi on virhe tai se ei vastaa kuvausta, kirjoita meille ja kerro tilausnumerosi.',
    us: 'Tämä on EU:n kuluttajalainsäädännön mukainen peruuttamisoikeus siltä varalta, että muutat mielesi. Se ei vaikuta oikeuksiisi, jos tiedostossasi on virhe: jos tiedostossasi on virhe tai se ei vastaa kuvausta, kirjoita meille ja kerro tilausnumerosi.',
    info: 'Peruuttamisoikeus',
    formLead: (confirm: string) => `Tarkista tietosi. Painikkeella ”${confirm}” lähetät meille tämän ilmoituksen:`,
    // identical to api/_lib/withdraw_fi.py STATEMENT_FI ({order} there)
    statement: (o: string) => `Ilmoitan, että haluan peruuttaa tekemäni sopimuksen, joka koskee seuraavan digitaalisen sisällön toimittamista: SnapEyes-taideteos, tilaus ${o}.`,
    statementNoOrder: 'Ilmoitan, että haluan peruuttaa tekemäni sopimuksen, joka koskee seuraavan digitaalisen sisällön toimittamista: SnapEyes-taideteos, alla mainittu tilaus.',
    name: 'Nimesi',
    email: 'Sähköpostiosoite vahvistusta varten',
    emailHint: 'Lähetämme vastaanottoilmoituksen päivämäärineen ja kellonaikoineen tähän osoitteeseen.',
    emailHintNoLink: 'Käytä sähköpostiosoitetta, jolla maksoit: siitä näemme, että tilaus on sinun. Lähetämme vastaanottoilmoituksen päivämäärineen ja kellonaikoineen tähän osoitteeseen.',
    order: 'Tilausnumero',
    orderHint: 'Löydät sen tilausvahvistuksesta ja tilaussivulta.',
    sending: 'Lähetämme peruuttamisilmoitustasi…',
    cancel: 'Keskeytä',
    back: 'Takaisin tilaukseesi',
    invalid: {
      name: 'Kirjoita nimesi.',
      email: 'Kirjoita kelvollinen sähköpostiosoite.',
      order: 'Kirjoita tilausnumerosi sellaisena kuin se on sähköpostissasi.',
    },
    errors: {
      network: 'Emme saaneet yhteyttä SnapEyesiin, joten emme tiedä, tuliko peruuttamisilmoituksesi perille. Tarkista yhteytesi ja yritä uudelleen: uudelleen lähettämisestä ei ole haittaa.',
      busy: `Järjestelmässämme on juuri nyt ruuhkaa, joten peruuttamisilmoitustasi ei voitu kirjata. Yritä hetken kuluttua uudelleen tai lähetä peruuttamisilmoituksesi osoitteeseen ${CONTACT_EMAIL}: sähköposti on yhtä pätevä.`,
      unmatched: (when: string | null) => `Emme voineet yhdistää ilmoitustasi näillä tiedoilla mihinkään tilaukseen. Olemme säilyttäneet sen${when ? ` (vastaanotettu ${when})` : ''} ja tarkistamme sen käsin. Tarkista tilausnumero, ja jos tulit ilman tilauksesi linkkiä, käytä sähköpostiosoitetta, jolla maksoit. Voit myös kirjoittaa osoitteeseen ${CONTACT_EMAIL}.`,
      // api/_lib/withdraw.py 409 no_order: nothing was stored, so nothing here may say it was kept
      no_order: `Emme löytäneet tilausta tällä numerolla; mitään ei kirjattu. Tarkista numero tai kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
      not_paid: 'Tätä tilausta ei koskaan maksettu, joten peruutettavaa sopimusta ei ole. Mitään ei veloitettu.',
      invalid: 'Tarkista nimesi ja sähköpostiosoitteesi ja yritä uudelleen.',
      paused: `Emme voi juuri nyt ottaa peruuttamisilmoituksia vastaan verkossa. Lähetä peruuttamisilmoituksesi osoitteeseen ${CONTACT_EMAIL}: sähköposti on yhtä pätevä.`,
      too_many: `Olemme tänään saaneet tästä tilauksesta jo useita peruuttamisilmoituksia. Jos jotain puuttuu, kirjoita osoitteeseen ${CONTACT_EMAIL}.`,
      failed: `Peruuttamisilmoitustasi ei voitu lähettää. Yritä uudelleen tai lähetä peruuttamisilmoituksesi osoitteeseen ${CONTACT_EMAIL}: sähköposti on yhtä pätevä.`,
    },
    done: {
      effectiveTitle: 'Peruuttamisilmoituksesi on vastaanotettu',
      lapsedTitle: 'Ilmoituksesi on vastaanotettu',
      checking: 'Tarkistamme nyt tilauksesi käsin ja lähetämme tuloksen sähköpostiisi.',
      received: (when: string) => `Vastaanotimme peruuttamisilmoituksesi ${when}.`,
      effective: 'Sopimuksesi on peruutettu. Emme tee tiedostoasi.',
      refund: (amount: string) => `Palautamme maksamasi summan (${amount}) käyttämällesi maksutavalle viimeistään 14 päivän kuluessa.`,
      refundNoAmount: 'Palautamme maksamasi summan käyttämällesi maksutavalle viimeistään 14 päivän kuluessa.',
      // date: "28.10.2026" (dateOfFi), without a final dot
      refundBy: (amount: string, date: string) => `Palautamme maksamasi summan (${amount}) käyttämällesi maksutavalle viimeistään ${date}. Sinulle ei tule tästä kuluja.`,
      settling: 'Maksuasi käsiteltiin vielä, kun peruutit sopimuksen. Jos se saapuu meille, palautamme sen kokonaan käyttämällesi maksutavalle viimeistään 14 päivän kuluessa.',
      refundStarted: (amount: string) => `Summan ${amount} palautus käyttämällesi maksutavalle on aloitettu. Pankistasi riippuen sen saapuminen voi kestää muutaman päivän.`,
      lapsed: 'Tiedostosi tekeminen oli jo alkanut. Tilatessasi hyväksyit, että aloitamme heti, ja vahvistit, että menetät peruuttamisoikeutesi, kun olemme aloittaneet, joten oikeus oli jo päättynyt. Tilauksesi pysyy voimassa: löydät tiedostosi tilaussivultasi.',
      lapsedPeriod: 'Tämän tilauksen 14 päivän peruuttamisaika oli jo päättynyt, joten peruuttamisoikeutesi oli päättynyt, kun ilmoituksesi saapui.',
      lapsedHelp: 'Katsomme ilmoituksesi silti henkilökohtaisesti ja vastaamme sinulle sähköpostitse. Tämä ei vaikuta lakisääteisiin oikeuksiisi, jos tiedostossa on virhe.',
      mailSent: (email: string) => `Vastaanottoilmoitus on matkalla osoitteeseen ${email}.`,
      mailRedirected: 'Vastaanottoilmoitus on matkalla sähköpostiosoitteeseen, jolla maksoit.',
      mailLater: (email: string) => `Emme voineet juuri nyt lähettää vastaanottoilmoitusta osoitteeseen ${email}. Lähetämme sen heti, kun voimme. Peruutuksesi on voimassa yllä mainitusta ajankohdasta alkaen.`,
      mailFailed: (email: string) => `Emme voineet lähettää vastaanottoilmoitusta osoitteeseen ${email}. Peruutuksesi on kirjattu yllä mainitulla ajankohdalla. Tarkista osoite tai pyydä kopio kirjoittamalla osoitteeseen ${CONTACT_EMAIL}.`,
    },
    withdrawn: {
      title: 'Tämän tilauksen sopimus on peruutettu',
      body: (when: string) => `Peruuttamisilmoituksesi vastaanotettiin ${when}. Tälle tilaukselle ei tehdä mitään.`,
      bodyNoTime: 'Peruuttamisilmoituksesi on vastaanotettu. Tälle tilaukselle ei tehdä mitään.',
    },
    unpaid: 'Tätä tilausta ei ole maksettu, joten peruutettavaa sopimusta ei ole. Mitään ei veloitettu.',
  },
  contact: {
    lead: 'Kysyttävää tilauksestasi?',
    write: (email: string) => `Kirjoita osoitteeseen ${email}`,
    subject: (o: string) => `SnapEyes-tilaus ${o}`,
  },
};

// The helpers of src/order/copy.ts for 'fi'. The amount of a paid order is shown in its own currency by
// src/shared/markets.ts money() ("24,97 €").
/** mbOf(bytes, 'fi'): "4,2" */
export const mbOfFi = (bytes: number) => mbFi(bytes);
/** dateOf(unixSeconds, 'fi'): "13.10.2026" (the date a refund is due by: "viimeistään ...") */
export const dateOfFi = (unixSeconds: number) => dateFi(unixSeconds);
/** whenOf(unixSeconds, 'fi'): "29.9.2026 klo 13.15 (UTC+3)" (the withdrawal receipt names date and time) */
export const whenOfFi = (unixSeconds: number) => whenFi(unixSeconds);
