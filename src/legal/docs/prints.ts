// Prints of the artwork (api/_lib/prints.py, src/shared/prints.ts) in the legal texts of the EU edition (and of the Hungarian edition, which
// shares the EU texts): the terms get a section "prints" (the products and prices from api/_lib/print_offer.py, the shipping per country from
// api/_lib/print_rates.py, the delivery countries, the delivery time, the manufacturer as the General Product Safety Regulation (EU) 2023/988
// asks, no right of withdrawal under Art. 16(c) Directive 2011/83/EU, damage in transit and the legal guarantee; since 2026-11-21 it says that
// a print is ordered from the order page AFTER the artwork is delivered, as a contract of its own), and three of their sentences
// change (the product, the delivery costs, withdrawal and defects point to it); the privacy policy names the print partner as a recipient of
// the name and the delivery address (a section "prints", a line in the list of services, a line on how long they are kept); the withdrawal
// page says that a print has no right of withdrawal (a section "prints"). The Australian and the US editions are made from the texts before
// this (their markets sell no prints) and keep saying that no print is sold.
// A sentence that is changed here and is not found in the text any more stops the build (swap), so a later edit of the terms cannot leave
// a print sentence pointing at nothing. Every price and every country comes from the three tables: a change of a price or of the rate table is
// a change of the terms (the pack the confirmation e-mail quotes is built from the same pages).
// Not reviewed by a lawyer.
import type { Block, EditionDocs, LegalDoc, LegalSection } from '../types';
import type { Lang } from '../../shared/lang';
import { patchDoc } from '../patch';
import { eur, MAIL } from '../facts';
import { PRINT_TIMES, countriesByName, countryName, printCountries, printLabel, printProducts, printShipping } from '../../shared/prints';

const PRODUCER = 'Picanova GmbH (merchOne), Eupener Straße 67, 50933 Köln';
const PRODUCER_MAIL = '[support@merchone.com](mailto:support@merchone.com)';

// The times of the terms' delivery paragraph: ONE sentence pair per language, its numbers from api/_lib/print_times.py (the one place: production per kind,
// delivery per country), never typed here. {fast}: the kinds merchOne makes fastest (a canvas, a poster), {slow}: every other print; {lt0} to {lt1}: Lithuania,
// Latvia and Estonia (one time for the three), {fi0} to {fi1}: Finland, {de0} to {de1}: Germany; every other country has no published time and is said in
// words. suites/ts/prints.test.ts holds that the table still fits these words (which kinds are fast, which countries have a time, the Baltic three equal).
const TIMES: Record<Lang, string> = {
  en: 'Production takes about {fast} business days for a canvas or a poster and about {slow} business days for every other print. Delivery then usually takes {lt0} to {lt1} working days to Lithuania, Latvia and Estonia, {fi0} to {fi1} to Finland and {de0} to {de1} to Germany; to the other countries of the European Union the parcel is usually on its way for about a week.',
  de: 'Die Produktion dauert bei einer Leinwand oder einem Poster etwa {fast} Werktage, bei jedem anderen Druck etwa {slow} Werktage. Die Zustellung dauert danach meist {lt0} bis {lt1} Werktage nach Litauen, Lettland und Estland, {fi0} bis {fi1} nach Finnland und {de0} bis {de1} innerhalb Deutschlands; in die anderen Länder der Europäischen Union ist die Sendung meist etwa eine Woche unterwegs.',
  lt: 'Drobės ir plakato gamyba trunka apie {fast} darbo dienas, kiekvieno kito spaudinio apie {slow} darbo dienas. Po to pristatymas į Lietuvą, Latviją ir Estiją paprastai trunka nuo {lt0} iki {lt1} darbo dienų, į Suomiją nuo {fi0} iki {fi1}, į Vokietiją nuo {de0} iki {de1}; į kitas Europos Sąjungos šalis siunta paprastai keliauja apie savaitę.',
  hu: 'A gyártás vászonkép és poszter esetén körülbelül {fast} munkanap, minden más nyomat esetén körülbelül {slow} munkanap. A kézbesítés ezután Litvániába, Lettországba és Észtországba általában {lt0} és {lt1} munkanap között tart, Finnországba {fi0} és {fi1}, Németországba {de0} és {de1} munkanap között; az Európai Unió többi országába a csomag általában körülbelül egy hétig van úton.',
  hr: 'Izrada platna ili postera traje oko {fast} radna dana, a svakog drugog ispisa oko {slow} radna dana. Dostava zatim obično traje {lt0} do {lt1} radnih dana u Litvu, Latviju i Estoniju, {fi0} do {fi1} u Finsku i {de0} do {de1} u Njemačku; u ostale zemlje Europske unije pošiljka obično putuje oko tjedan dana.',
  fi: 'Canvastaulun ja julisteen tuotanto kestää noin {fast} arkipäivää, kaikkien muiden tulosteiden noin {slow} arkipäivää. Toimitus kestää sen jälkeen yleensä {lt0}-{lt1} arkipäivää Liettuaan, Latviaan ja Viroon, {fi0}-{fi1} Suomeen ja {de0}-{de1} Saksaan; muihin Euroopan unionin maihin lähetys on yleensä matkalla noin viikon.',
  et: 'Lõuendi ja plakati tootmine võtab umbes {fast} tööpäeva, iga muu trükitud pildi tootmine umbes {slow} tööpäeva. Kohaletoimetamine võtab seejärel tavaliselt {lt0} kuni {lt1} tööpäeva Leetu, Lätti ja Eestisse, {fi0} kuni {fi1} Soome ja {de0} kuni {de1} Saksamaale; teistesse Euroopa Liidu riikidesse on saadetis tavaliselt teel umbes nädala.',
  lv: 'Audekla un plakāta ražošana aizņem apmēram {fast} darba dienas, katras citas izdrukas ražošana apmēram {slow} darba dienas. Piegāde pēc tam parasti aizņem {lt0} līdz {lt1} darba dienas uz Lietuvu, Latviju un Igauniju, {fi0} līdz {fi1} uz Somiju un {de0} līdz {de1} uz Vāciju; uz pārējām Eiropas Savienības valstīm sūtījums parasti ir ceļā apmēram nedēļu.',
};
/** The sentences of the times in a language, with the numbers of the table. */
export function timesText(lang: Lang): string {
  const t = PRINT_TIMES;
  const days = Object.values(t.production);
  const n: Record<string, number> = { fast: Math.min(...days), slow: Math.max(...days), lt0: t.transit.LT[0], lt1: t.transit.LT[1], fi0: t.transit.FI[0], fi1: t.transit.FI[1], de0: t.transit.DE[0], de1: t.transit.DE[1] };
  return TIMES[lang].replace(/\{([a-z0-9]+)\}/g, (_m, k: string) => String(n[k]));
}

interface Words {
  title: string;
  intro: string;
  pricesNote: string;
  countries: string;
  delivery: string;
  maker: string;
  withdrawal: string;
  damage: string;
  // the sentences of the shared sections that change: [the old words, the new words]
  product: [string, string];
  noDelivery: [string, string];
  // the same sentence in the Hungarian edition's price section (forints): no print is sold in forints
  hufNote: string;
  withdrawalRef: string;
  defectsRef: string;
  // "{price} for the {name}" inside a country's line, where a print's shipping differs from the country's usual one
  except: (name: string, price: string) => string;
  // the privacy policy
  privTitle: string;
  priv: string[];
  privService: string;
  privRetention: string;
  // the withdrawal page
  wdTitle: string;
  wd: string;
}

const W: Record<Lang, Words> = {
  en: {
    title: 'Prints',
    intro: 'On orders in euros, we can offer a print of your artwork once it is delivered: a physical copy of the very file you received, made to order. You order it on your order page, as a contract of its own beside the one for your digital file; your digital file is the same with or without it. Prints and their prices:',
    pricesNote: 'These are final prices in euros; we are not registered for VAT, so no VAT is charged. The shipping of a print is added for its delivery country and shown before you pay and on the payment page. Per print it is:',
    countries: 'We ship prints only to these countries of the European Union. The delivery address must be in the country you choose before you pay; you enter it on the payment page.',
    delivery: `**Delivery.** We send your print to production as soon as you have ordered it; your file is ready by then (see [Delivery](#delivery)). ${timesText('en')} The parcel is tracked, and we email you the tracking link when it ships. At the latest, your print is delivered within 30 days of the contract.`,
    maker: `**Manufacturer.** Your print is made for us by our print partner, the manufacturer of the product: ${PRODUCER}, Germany, ${PRODUCER_MAIL}. The seller is SnapEyes (see [Who you contract with](#parties)): please write to us with any question about your print. An artwork that is not square is centred on the square print, and its background is continued to the edges. Colours on paper, on canvas or behind acrylic glass can look slightly different from your screen.`,
    withdrawal: '**No right of withdrawal for prints.** A print is made to your specifications from your personal artwork, so the right of withdrawal does not apply to it (Article 16(c) of Directive 2011/83/EU). Before you pay, we ask you to confirm that you know this. A print is ordered after your file is delivered, as a contract of its own; it changes nothing in the contract for your file.',
    damage: `**Damage in transit and defects.** Please check your print when it arrives. If it is damaged in transit or faulty, for example a printing error, a crack or a dent, please write to ${MAIL} within 7 days of delivery if you can, with your order number, a photo of the damage, a photo of the whole print and, if possible, of the packaging: our print partner takes claims within that time, so we can then have it replaced fastest. We have a damaged or faulty print made again and sent to you free of charge or, if that is not possible, refund it. Your statutory rights for goods that do not conform to the contract, including the legal guarantee of two years from delivery, apply in full: reporting a defect later does not take them away.`,
    product: ['The artwork is delivered only as a digital file, by download. We do not sell prints, frames or any other physical product.', 'The artwork is delivered as a digital file, by download. On orders in euros you can order a print of it afterwards, from your order page: see [Prints](#prints).'],
    noDelivery: ['There are no delivery costs.', 'There are no delivery costs for the digital file; for a print, see [Prints](#prints).'],
    hufNote: 'There are no delivery costs. A print can be added only to an order in euros (see [Prints](#prints)).',
    withdrawalRef: 'The right of withdrawal does not apply to prints: see [Prints](#prints).',
    defectsRef: 'For prints, see [Prints](#prints).',
    except: (name, price) => `${price} for the ${name}`,
    privTitle: 'When you order a print',
    priv: [
      "If you order a print of your artwork, Stripe's payment page for the print asks for your name and delivery address. We receive them from Stripe with your payment and keep them with your order.",
      `To make and send the print, we pass your name and delivery address, with the order number and the print file made from your artwork, to our print partner ${PRODUCER}, Germany. It produces the print in the EU and hands it to a parcel service, which receives your name and address for the delivery. Picanova processes these data on our behalf. We do not give it your email address: we send you the tracking link ourselves.`,
      'Legal basis: the contract with you (Art. 6(1)(b) GDPR). Your name and delivery address stay with your order record for as long as that record is kept (see [How long we keep your data](#retention)); the print file is deleted with the other files of your order.',
    ],
    privService: 'Picanova GmbH (merchOne): production and shipping of prints, with the data named in [When you order a print](#prints).',
    privRetention: 'For an order with a print, the order record also holds your name, your delivery address and the tracking number of the parcel.',
    wdTitle: 'Prints',
    wd: 'The right of withdrawal does not apply to a print of your artwork: a print is made to your specifications from your personal artwork (Article 16(c) of Directive 2011/83/EU). You order a print from your order page after your file is delivered, as a contract of its own; before you pay, we ask you to confirm that you know this. Your rights if a print arrives damaged or faulty are not affected: see our [Terms of sale](doc:terms#prints).',
  },
  de: {
    title: 'Drucke',
    intro: 'Bei Bestellungen in Euro können wir Ihnen einen Druck Ihres Kunstwerks anbieten, sobald es geliefert ist: ein physisches Exemplar genau der Datei, die Sie erhalten haben, nach Ihrer Bestellung angefertigt. Sie bestellen ihn auf Ihrer Bestellseite, als eigenen Vertrag neben dem über Ihre digitale Datei; Ihre digitale Datei ist mit oder ohne Druck dieselbe. Drucke und ihre Preise:',
    pricesNote: 'Das sind Endpreise in Euro; wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet. Die Versandkosten eines Drucks richten sich nach dem Lieferland und werden vor der Zahlung und auf der Zahlungsseite angezeigt. Sie betragen je Druck:',
    countries: 'Wir liefern Drucke nur in diese Länder der Europäischen Union. Die Lieferadresse muss in dem Land liegen, das Sie vor der Zahlung wählen; Sie geben sie auf der Zahlungsseite ein.',
    delivery: `**Lieferung.** Wir geben Ihren Druck in die Produktion, sobald Sie ihn bestellt haben; Ihre Datei ist dann bereits fertig (siehe [Lieferung](#delivery)). ${timesText('de')} Die Sendung ist verfolgbar, und wir senden Ihnen den Link zur Sendungsverfolgung, sobald sie versandt ist. Spätestens wird Ihr Druck innerhalb von 30 Tagen nach Vertragsschluss geliefert.`,
    maker: `**Hersteller.** Ihr Druck wird für uns von unserem Druckpartner hergestellt, dem Hersteller des Produkts: ${PRODUCER}, Deutschland, ${PRODUCER_MAIL}. Verkäufer ist SnapEyes (siehe [Ihr Vertragspartner](#parties)): Bei Fragen zu Ihrem Druck schreiben Sie bitte uns. Ein Kunstwerk, das nicht quadratisch ist, wird mittig auf den quadratischen Druck gesetzt, und sein Hintergrund wird bis zum Rand fortgeführt. Farben auf Papier, auf Leinwand oder hinter Acrylglas können leicht von Ihrem Bildschirm abweichen.`,
    withdrawal: '**Kein Widerrufsrecht für Drucke.** Ein Druck wird nach Ihren Vorgaben aus Ihrem persönlichen Kunstwerk angefertigt, daher besteht für ihn kein Widerrufsrecht (Artikel 16 Buchstabe c der Richtlinie 2011/83/EU). Vor der Zahlung bitten wir Sie zu bestätigen, dass Ihnen das bekannt ist. Einen Druck bestellen Sie, nachdem Ihre Datei geliefert ist, als eigenen Vertrag; am Vertrag über Ihre Datei ändert er nichts.',
    damage: `**Transportschäden und Mängel.** Bitte prüfen Sie Ihren Druck, wenn er ankommt. Ist er auf dem Transport beschädigt worden oder fehlerhaft, zum Beispiel durch einen Druckfehler, einen Riss oder eine Delle, schreiben Sie bitte möglichst innerhalb von 7 Tagen nach der Zustellung an ${MAIL}, mit Ihrer Bestellnummer, einem Foto des Schadens, einem Foto des ganzen Drucks und, wenn möglich, der Verpackung: Unser Druckpartner nimmt Reklamationen innerhalb dieser Frist an, so können wir ihn am schnellsten ersetzen lassen. Einen beschädigten oder fehlerhaften Druck lassen wir kostenlos neu anfertigen und Ihnen zusenden oder erstatten ihn, wenn das nicht möglich ist. Ihre gesetzlichen Rechte bei mangelhafter Ware, einschließlich der gesetzlichen Gewährleistung von zwei Jahren ab Lieferung, gelten uneingeschränkt: Eine spätere Meldung lässt sie nicht entfallen.`,
    product: ['Das Kunstwerk wird ausschließlich als digitale Datei zum Download geliefert. Drucke, Rahmen oder andere physische Produkte verkaufen wir nicht.', 'Das Kunstwerk wird als digitale Datei zum Download geliefert. Bei Bestellungen in Euro können Sie danach auf Ihrer Bestellseite einen Druck davon bestellen: siehe [Drucke](#prints).'],
    noDelivery: ['Versandkosten fallen nicht an.', 'Für die digitale Datei fallen keine Versandkosten an; zu Drucken siehe [Drucke](#prints).'],
    hufNote: 'Versandkosten fallen nicht an. Ein Druck kann nur zu einer Bestellung in Euro hinzugefügt werden (siehe [Drucke](#prints)).',
    withdrawalRef: 'Für Drucke besteht kein Widerrufsrecht: siehe [Drucke](#prints).',
    defectsRef: 'Zu Drucken siehe [Drucke](#prints).',
    except: (name, price) => `${price} für ${name}`,
    privTitle: 'Wenn Sie einen Druck bestellen',
    priv: [
      'Bestellen Sie einen Druck Ihres Kunstwerks, fragt die Zahlungsseite von Stripe für den Druck nach Ihrem Namen und Ihrer Lieferadresse. Wir erhalten sie mit Ihrer Zahlung von Stripe und bewahren sie bei Ihrer Bestellung auf.',
      `Um den Druck herzustellen und zu versenden, geben wir Ihren Namen und Ihre Lieferadresse mit der Bestellnummer und der aus Ihrem Kunstwerk erstellten Druckdatei an unseren Druckpartner ${PRODUCER}, Deutschland, weiter. Er stellt den Druck in der EU her und übergibt ihn einem Paketdienst, der dafür Ihren Namen und Ihre Adresse erhält. Picanova verarbeitet diese Daten in unserem Auftrag. Ihre E-Mail-Adresse geben wir nicht weiter: Den Link zur Sendungsverfolgung senden wir Ihnen selbst.`,
      'Rechtsgrundlage: der Vertrag mit Ihnen (Art. 6 Abs. 1 lit. b DSGVO). Ihr Name und Ihre Lieferadresse bleiben so lange bei Ihrem Bestelldatensatz, wie er aufbewahrt wird (siehe [Wie lange wir Ihre Daten speichern](#retention)); die Druckdatei wird mit den anderen Dateien Ihrer Bestellung gelöscht.',
    ],
    privService: 'Picanova GmbH (merchOne): Herstellung und Versand von Drucken, mit den unter [Wenn Sie einen Druck bestellen](#prints) genannten Daten.',
    privRetention: 'Bei einer Bestellung mit Druck enthält der Bestelldatensatz auch Ihren Namen, Ihre Lieferadresse und die Sendungsnummer des Pakets.',
    wdTitle: 'Drucke',
    wd: 'Für einen Druck Ihres Kunstwerks besteht kein Widerrufsrecht: Ein Druck wird nach Ihren Vorgaben aus Ihrem persönlichen Kunstwerk angefertigt (Artikel 16 Buchstabe c der Richtlinie 2011/83/EU). Einen Druck bestellen Sie auf Ihrer Bestellseite, nachdem Ihre Datei geliefert ist, als eigenen Vertrag; vor der Zahlung bitten wir Sie zu bestätigen, dass Ihnen das bekannt ist. Ihre Rechte, wenn ein Druck beschädigt oder fehlerhaft ankommt, bleiben unberührt: siehe unsere [AGB](doc:terms#prints).',
  },
  lt: {
    title: 'Spaudiniai',
    intro: 'Užsakymams eurais, kai Jūsų kūrinys pateiktas, galime pasiūlyti jo spaudinį: fizinę būtent to failo, kurį gavote, kopiją, pagamintą pagal užsakymą. Jį užsisakote savo užsakymo puslapyje, kaip atskirą sutartį šalia sutarties dėl Jūsų skaitmeninio failo; Jūsų skaitmeninis failas su spaudiniu ar be jo yra tas pats. Spaudiniai ir jų kainos:',
    pricesNote: 'Tai galutinės kainos eurais; nesame PVM mokėtojai, todėl PVM netaikomas. Spaudinio siuntimo kaina priklauso nuo pristatymo šalies ir parodoma prieš mokant bei mokėjimo puslapyje. Vienam spaudiniui ji yra:',
    countries: 'Spaudinius siunčiame tik į šias Europos Sąjungos šalis. Pristatymo adresas turi būti šalyje, kurią pasirenkate prieš mokėdami; jį įvedate mokėjimo puslapyje.',
    delivery: `**Pristatymas.** Spaudinį perduodame gaminti, kai tik jį užsisakote; Jūsų failas tuo metu jau būna paruoštas (žr. [Pristatymas](#delivery)). ${timesText('lt')} Siuntą galima sekti, o kai spaudinys išsiunčiamas, el. paštu atsiunčiame siuntos sekimo nuorodą. Vėliausiai spaudinys pristatomas per 30 dienų nuo sutarties sudarymo.`,
    maker: `**Gamintojas.** Spaudinį mums gamina mūsų spaudos partneris, gaminio gamintojas: ${PRODUCER}, Vokietija, ${PRODUCER_MAIL}. Pardavėjas yra SnapEyes (žr. [Su kuo sudarote sutartį](#parties)): visais klausimais dėl spaudinio rašykite mums. Ne kvadratinis kūrinys dedamas kvadratinio spaudinio centre, o jo fonas pratęsiamas iki kraštų. Spalvos ant popieriaus, drobės ar po akriliniu stiklu gali šiek tiek skirtis nuo matomų ekrane.`,
    withdrawal: '**Spaudiniams teisė atsisakyti sutarties netaikoma.** Spaudinys gaminamas pagal Jūsų nurodymus iš Jūsų asmeninio kūrinio, todėl teisė atsisakyti sutarties jam netaikoma (Direktyvos 2011/83/ES 16 straipsnio c punktas). Prieš mokėjimą paprašome patvirtinti, kad tai žinote. Spaudinį užsisakote po to, kai Jūsų failas pateiktas, kaip atskirą sutartį; sutarties dėl Jūsų failo ji nekeičia.',
    damage: `**Pažeidimai pervežant ir trūkumai.** Gavę spaudinį, jį patikrinkite. Jei jis sugadintas pervežant arba turi trūkumų, pavyzdžiui, spaudos klaidą, įtrūkimą ar įlenkimą, jei galite, per 7 dienas nuo pristatymo parašykite adresu ${MAIL}, nurodykite užsakymo numerį ir pridėkite pažeidimo nuotrauką, viso spaudinio nuotrauką ir, jei įmanoma, pakuotės nuotrauką: mūsų spaudos partneris pretenzijas priima per šį laiką, todėl tada greičiausiai pasirūpinsime pakeitimu. Sugadintą ar trūkumų turintį spaudinį nemokamai pagaminsime iš naujo ir atsiųsime arba, jei tai neįmanoma, grąžinsime už jį sumokėtus pinigus. Jūsų įstatyminės teisės dėl sutarties neatitinkančių prekių, įskaitant dvejų metų nuo pristatymo įstatyminę garantiją, galioja visa apimtimi: vėlesnis pranešimas apie trūkumą jų neatima.`,
    product: ['Kūrinys pateikiamas tik kaip skaitmeninis failas, jį atsisiunčiant. Spaudinių, rėmelių ar kitų fizinių produktų neparduodame.', 'Kūrinys pateikiamas kaip skaitmeninis failas, jį atsisiunčiant. Užsakymams eurais vėliau savo užsakymo puslapyje galite užsisakyti jo spaudinį: žr. [Spaudiniai](#prints).'],
    noDelivery: ['Pristatymo išlaidų nėra.', 'Skaitmeninio failo pristatymo išlaidų nėra; apie spaudinius žr. [Spaudiniai](#prints).'],
    hufNote: 'Pristatymo išlaidų nėra. Spaudinį galima pridėti tik prie užsakymo eurais (žr. [Spaudiniai](#prints)).',
    withdrawalRef: 'Spaudiniams teisė atsisakyti sutarties netaikoma: žr. [Spaudiniai](#prints).',
    defectsRef: 'Dėl spaudinių žr. [Spaudiniai](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Kai užsisakote spaudinį',
    priv: [
      'Jei užsisakote savo kūrinio spaudinį, Stripe mokėjimo puslapyje, kuriame mokate už spaudinį, prašoma nurodyti Jūsų vardą, pavardę ir pristatymo adresą. Juos kartu su mokėjimu gauname iš Stripe ir saugome su Jūsų užsakymu.',
      `Kad spaudinį pagamintume ir išsiųstume, Jūsų vardą, pavardę ir pristatymo adresą kartu su užsakymo numeriu ir iš Jūsų kūrinio paruoštu spaudos failu perduodame mūsų spaudos partneriui ${PRODUCER}, Vokietija. Jis pagamina spaudinį ES ir perduoda jį siuntų tarnybai, kuri pristatymui gauna Jūsų vardą, pavardę ir adresą. Picanova šiuos duomenis tvarko mūsų vardu. Jūsų el. pašto adreso jam neperduodame: siuntos sekimo nuorodą atsiunčiame patys.`,
      'Teisinis pagrindas: sutartis su Jumis (BDAR 6 straipsnio 1 dalies b punktas). Jūsų vardas, pavardė ir pristatymo adresas saugomi su Jūsų užsakymo įrašu tol, kol saugomas šis įrašas (žr. [Kiek laiko saugome Jūsų duomenis](#retention)); spaudos failas ištrinamas kartu su kitais užsakymo failais.',
    ],
    privService: 'Picanova GmbH (merchOne): spaudinių gamyba ir siuntimas, su skyriuje [Kai užsisakote spaudinį](#prints) nurodytais duomenimis.',
    privRetention: 'Jei užsakyme yra spaudinys, užsakymo įraše taip pat saugomas Jūsų vardas, pavardė, pristatymo adresas ir siuntos sekimo numeris.',
    wdTitle: 'Spaudiniai',
    wd: 'Jūsų kūrinio spaudiniui teisė atsisakyti sutarties netaikoma: spaudinys gaminamas pagal Jūsų nurodymus iš Jūsų asmeninio kūrinio (Direktyvos 2011/83/ES 16 straipsnio c punktas). Spaudinį užsisakote savo užsakymo puslapyje po to, kai Jūsų failas pateiktas, kaip atskirą sutartį; prieš mokėjimą paprašome patvirtinti, kad tai žinote. Jūsų teisės, jei spaudinys atkeliauja sugadintas ar su trūkumais, nesumažėja: žr. mūsų [pardavimo sąlygas](doc:terms#prints).',
  },
  hu: {
    title: 'Nyomatok',
    intro: 'Euróban leadott megrendelés esetén, miután az alkotását megkapta, felkínálhatjuk annak nyomatát: pontosan annak a fájlnak a megrendelésre készült fizikai példányát, amelyet Ön megkapott. A nyomatot a rendelési oldalán rendelheti meg, külön szerződésként a digitális fájljára vonatkozó szerződés mellett; a digitális fájlja nyomattal vagy anélkül ugyanaz. A nyomatok és áraik:',
    pricesNote: 'Ezek euróban értendő végső árak; nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel. A nyomat szállítási díja a szállítási országtól függ, és a fizetés előtt, valamint a fizetési oldalon látható. Nyomatonként:',
    countries: 'Nyomatot csak az Európai Unió alábbi országaiba szállítunk. A szállítási címnek abban az országban kell lennie, amelyet a fizetés előtt kiválaszt; a címet a fizetési oldalon adja meg.',
    delivery: `**Szállítás.** A nyomatot azonnal gyártásba adjuk, amint megrendelte; a fájlja ekkor már elkészült (lásd [Teljesítés](#delivery)). ${timesText('hu')} A csomag nyomon követhető, és a feladáskor e-mailben elküldjük a csomagkövetési linket. A nyomatot legkésőbb a szerződéskötéstől számított 30 napon belül kézbesítjük.`,
    maker: `**Gyártó.** A nyomatot nyomdai partnerünk, a termék gyártója készíti nekünk: ${PRODUCER}, Németország, ${PRODUCER_MAIL}. Az eladó a SnapEyes (lásd [Kivel köt szerződést](#parties)): a nyomattal kapcsolatos kérdéseivel nekünk írjon. A nem négyzet alakú alkotást a négyzetes nyomat közepére helyezzük, és a hátterét a széléig folytatjuk. A színek papíron, vásznon vagy akrilüveg mögött kissé eltérhetnek a képernyőn látottól.`,
    withdrawal: '**A nyomatokra nem vonatkozik az elállási jog.** A nyomat az Ön utasításai szerint, az Ön személyes alkotásából készül, ezért arra az elállási jog nem vonatkozik (a 2011/83/EU irányelv 16. cikkének c) pontja). Fizetés előtt megkérjük, hogy erősítse meg: tudomásul vette ezt. A nyomatot azután rendelheti meg, hogy a fájlját megkapta, külön szerződésként; ez a fájljára vonatkozó szerződésen nem változtat.',
    damage: `**Szállítási sérülés és hibák.** Kérjük, nézze meg a nyomatot, amikor megérkezik. Ha szállítás közben megsérült vagy hibás, például nyomdai hiba, repedés vagy horpadás miatt, lehetőleg a kézbesítéstől számított 7 napon belül írjon a(z) ${MAIL} címre a rendelésszámmal, egy fotóval a sérülésről, egy fotóval a teljes nyomatról és, ha lehet, a csomagolásról: nyomdai partnerünk ezen az időn belül fogadja be a reklamációt, így tudjuk a leggyorsabban kicseréltetni. A sérült vagy hibás nyomatot díjmentesen újra elkészíttetjük és elküldjük, vagy ha ez nem lehetséges, visszatérítjük az árát. A szerződésnek nem megfelelő termékre vonatkozó törvényes jogai, köztük a kézbesítéstől számított kétéves kellékszavatosság, teljes körűen megilletik: a későbbi bejelentés ezeket nem szünteti meg.`,
    product: ['Az alkotást kizárólag digitális fájlként, letöltéssel szolgáltatjuk. Nyomatot, keretet vagy más fizikai terméket nem árusítunk.', 'Az alkotást digitális fájlként, letöltéssel szolgáltatjuk. Euróban leadott megrendelés esetén utána a rendelési oldalán nyomatot is rendelhet belőle: lásd [Nyomatok](#prints).'],
    noDelivery: ['Szállítási költség nincs.', 'A digitális fájlnak nincs szállítási költsége; a nyomatokról lásd [Nyomatok](#prints).'],
    hufNote: 'Szállítási költség nincs. Nyomatot csak euróban leadott megrendeléshez lehet rendelni (lásd [Nyomatok](#prints)).',
    withdrawalRef: 'A nyomatokra az elállási jog nem vonatkozik: lásd [Nyomatok](#prints).',
    defectsRef: 'A nyomatokról lásd [Nyomatok](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Ha nyomatot rendel',
    priv: [
      'Ha megrendeli az alkotása nyomatát, a Stripe fizetési oldala a nyomat kifizetésekor elkéri a nevét és a szállítási címét. Ezeket a fizetéssel együtt a Stripe-tól kapjuk meg, és a megrendelésével együtt őrizzük.',
      `A nyomat elkészítéséhez és elküldéséhez a nevét és a szállítási címét a rendelésszámmal és az alkotásából készült nyomdai fájllal együtt átadjuk nyomdai partnerünknek: ${PRODUCER}, Németország. A partner az EU-ban elkészíti a nyomatot, és átadja egy csomagszállítónak, amely a kézbesítéshez megkapja a nevét és a címét. A Picanova ezeket az adatokat a megbízásunkból kezeli. Az e-mail-címét nem adjuk át neki: a csomagkövetési linket mi magunk küldjük el.`,
      'Jogalap: az Önnel kötött szerződés (GDPR 6. cikk (1) bekezdés b) pont). A nevét és a szállítási címét a rendelési nyilvántartással együtt addig őrizzük, ameddig azt megőrizzük (lásd [Meddig őrizzük az adatait](#retention)); a nyomdai fájlt a megrendelés többi fájljával együtt töröljük.',
    ],
    privService: 'Picanova GmbH (merchOne): nyomatok gyártása és szállítása, a [Ha nyomatot rendel](#prints) részben megnevezett adatokkal.',
    privRetention: 'Nyomatot tartalmazó megrendelésnél a rendelési nyilvántartás a nevét, a szállítási címét és a csomag követési számát is tartalmazza.',
    wdTitle: 'Nyomatok',
    wd: 'Az alkotása nyomatára az elállási jog nem vonatkozik: a nyomat az Ön utasításai szerint, az Ön személyes alkotásából készül (a 2011/83/EU irányelv 16. cikkének c) pontja). A nyomatot a rendelési oldalán rendelheti meg, miután a fájlját megkapta, külön szerződésként; fizetés előtt megkérjük, hogy erősítse meg: tudomásul vette ezt. Ez nem érinti a jogait, ha a nyomat sérülten vagy hibásan érkezik: lásd az [ÁSZF-et](doc:terms#prints).',
  },
  hr: {
    title: 'Ispisi',
    intro: 'Uz narudžbe u eurima, nakon što vam je umjetničko djelo isporučeno, možemo vam ponuditi njegov ispis: fizički primjerak upravo one datoteke koju ste dobili, izrađen po narudžbi. Naručujete ga na stranici svoje narudžbe, kao zaseban ugovor uz ugovor o vašoj digitalnoj datoteci; vaša digitalna datoteka ista je s ispisom ili bez njega. Ispisi i njihove cijene:',
    pricesNote: 'To su konačne cijene u eurima; nismo obveznik PDV-a, stoga se PDV ne obračunava. Dostava ispisa naplaćuje se prema zemlji dostave i prikazuje se prije plaćanja i na stranici za plaćanje. Po ispisu iznosi:',
    countries: 'Ispise šaljemo samo u ove zemlje Europske unije. Adresa za dostavu mora biti u zemlji koju odaberete prije plaćanja; unosite je na stranici za plaćanje.',
    delivery: `**Dostava.** Vaš ispis predajemo u izradu čim ga naručite; vaša je datoteka tada već gotova (pogledajte [Isporuka](#delivery)). ${timesText('hr')} Pošiljka se može pratiti, a kad je pošaljemo, e-poštom vam šaljemo poveznicu za praćenje. Ispis vam isporučujemo najkasnije u roku od 30 dana od sklapanja ugovora.`,
    maker: `**Proizvođač.** Vaš ispis za nas izrađuje naš partner za ispis, proizvođač proizvoda: ${PRODUCER}, Njemačka, ${PRODUCER_MAIL}. Prodavatelj je SnapEyes (pogledajte [S kim sklapate ugovor](#parties)): sa svim pitanjima o ispisu obratite se nama. Umjetničko djelo koje nije kvadratno postavlja se u sredinu kvadratnog ispisa, a njegova se pozadina nastavlja do rubova. Boje na papiru, platnu ili iza akrilnog stakla mogu se malo razlikovati od onih na zaslonu.`,
    withdrawal: '**Za ispise nema prava na jednostrani raskid ugovora.** Ispis se izrađuje prema vašim zahtjevima iz vašeg osobnog umjetničkog djela, pa se pravo na jednostrani raskid ugovora na njega ne primjenjuje (članak 16. točka (c) Direktive 2011/83/EU). Prije plaćanja molimo vas da potvrdite da to znate. Ispis naručujete nakon što vam je datoteka isporučena, kao zaseban ugovor; on ne mijenja ugovor o vašoj datoteci.',
    damage: `**Oštećenja u prijevozu i nedostaci.** Pregledajte ispis kad stigne. Ako je oštećen u prijevozu ili neispravan, primjerice zbog pogreške u ispisu, pukotine ili udubljenja, ako možete, pišite nam u roku od 7 dana od dostave na ${MAIL} s brojem narudžbe, fotografijom oštećenja, fotografijom cijelog ispisa i, ako je moguće, ambalaže: naš partner za ispis prima reklamacije u tom roku, pa ga tada najbrže možemo zamijeniti. Oštećen ili neispravan ispis besplatno ćemo ponovno izraditi i poslati vam ili, ako to nije moguće, vratiti njegov iznos. Vaša zakonska prava za robu koja nije u skladu s ugovorom, uključujući zakonsko jamstvo od dvije godine od dostave, vrijede u cijelosti: kasnija prijava ih ne ukida.`,
    product: ['Umjetničko djelo isporučuje se samo kao digitalna datoteka, preuzimanjem. Ne prodajemo otiske, okvire ni bilo kakve druge fizičke proizvode.', 'Umjetničko djelo isporučuje se kao digitalna datoteka, preuzimanjem. Uz narudžbu u eurima naknadno, na stranici svoje narudžbe, možete naručiti i njegov ispis: pogledajte [Ispisi](#prints).'],
    noDelivery: ['Troškova isporuke nema.', 'Za digitalnu datoteku nema troškova isporuke; za ispise pogledajte [Ispisi](#prints).'],
    hufNote: 'Troškova isporuke nema. Ispis se može dodati samo narudžbi u eurima (pogledajte [Ispisi](#prints)).',
    withdrawalRef: 'Pravo na jednostrani raskid ugovora ne primjenjuje se na ispise: pogledajte [Ispisi](#prints).',
    defectsRef: 'Za ispise pogledajte [Ispisi](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Kad naručite ispis',
    priv: [
      'Ako naručite ispis svojeg umjetničkog djela, Stripeova stranica za plaćanje ispisa traži vaše ime i adresu za dostavu. Primamo ih od Stripea s vašim plaćanjem i čuvamo ih uz vašu narudžbu.',
      `Kako bismo izradili i poslali ispis, vaše ime i adresu za dostavu, s brojem narudžbe i datotekom za ispis izrađenom iz vašeg umjetničkog djela, prosljeđujemo našem partneru za ispis ${PRODUCER}, Njemačka. On izrađuje ispis u EU-u i predaje ga dostavnoj službi, koja za dostavu dobiva vaše ime i adresu. Picanova te podatke obrađuje u naše ime. Vašu adresu e-pošte ne prosljeđujemo: poveznicu za praćenje šaljemo vam sami.`,
      'Pravna osnova: ugovor s vama (članak 6. stavak 1. točka (b) OUZP-a). Vaše ime i adresa za dostavu ostaju uz zapis o vašoj narudžbi dok god se on čuva (pogledajte [Koliko dugo čuvamo vaše podatke](#retention)); datoteka za ispis briše se s ostalim datotekama vaše narudžbe.',
    ],
    privService: 'Picanova GmbH (merchOne): izrada i slanje ispisa, s podacima navedenima u odjeljku [Kad naručite ispis](#prints).',
    privRetention: 'Za narudžbu s ispisom zapis o narudžbi sadržava i vaše ime, adresu za dostavu i broj za praćenje pošiljke.',
    wdTitle: 'Ispisi',
    wd: 'Za ispis vašeg umjetničkog djela nema prava na jednostrani raskid ugovora: ispis se izrađuje prema vašim zahtjevima iz vašeg osobnog umjetničkog djela (članak 16. točka (c) Direktive 2011/83/EU). Ispis naručujete na stranici svoje narudžbe nakon što vam je datoteka isporučena, kao zaseban ugovor; prije plaćanja molimo vas da potvrdite da to znate. To ne utječe na vaša prava ako ispis stigne oštećen ili neispravan: pogledajte naše [Opće uvjete prodaje](doc:terms#prints).',
  },
  fi: {
    title: 'Tulosteet',
    intro: 'Euromääräisissä tilauksissa voimme tarjota teille tulosteen taideteoksestanne sen jälkeen, kun se on toimitettu: fyysisen kappaleen juuri siitä tiedostosta, jonka saitte, tehtynä tilauksenne mukaan. Tilaatte sen tilaussivultanne omana sopimuksenaan digitaalista tiedostoanne koskevan sopimuksen rinnalla; digitaalinen tiedostonne pysyy samana, tilasittepa tulosteen tai ette. Tulosteet ja niiden hinnat:',
    pricesNote: 'Nämä ovat lopullisia hintoja euroina; emme ole arvonlisäverovelvollisia, joten arvonlisäveroa ei peritä. Tulosteen toimituskulut lisätään toimitusmaan mukaan, ja ne näytetään ennen maksamista ja maksusivulla. Tulostetta kohden ne ovat:',
    countries: 'Lähetämme tulosteita vain näihin Euroopan unionin maihin. Toimitusosoitteen on oltava maassa, jonka valitsette ennen maksamista; annatte osoitteen maksusivulla.',
    delivery: `**Toimitus.** Lähetämme tulosteenne tuotantoon heti, kun olette tilanneet sen; tiedostonne on silloin jo valmis (katsokaa [Toimitus](#delivery)). ${timesText('fi')} Lähetystä voi seurata, ja lähetämme seurantalinkin sähköpostiinne, kun tuloste lähtee matkaan. Tulosteenne toimitetaan viimeistään 30 päivän kuluessa sopimuksen tekemisestä.`,
    maker: `**Valmistaja.** Tulosteenne tekee meille tulostuskumppanimme, tuotteen valmistaja: ${PRODUCER}, Saksa, ${PRODUCER_MAIL}. Myyjä on SnapEyes (katsokaa [Sopimuskumppaninne](#parties)): kirjoittakaa meille kaikissa tulostettanne koskevissa kysymyksissä. Taideteos, joka ei ole neliön muotoinen, keskitetään neliön muotoiselle tulosteelle, ja sen taustaa jatketaan reunoihin asti. Värit paperilla, canvaksella tai akryylilasin takana voivat näyttää hieman erilaisilta kuin näytöllänne.`,
    withdrawal: '**Tulosteilla ei ole peruuttamisoikeutta.** Tuloste tehdään vaatimustenne mukaisesti henkilökohtaisesta taideteoksestanne, joten peruuttamisoikeutta ei sovelleta siihen (direktiivin 2011/83/EU 16 artiklan c alakohta). Ennen maksamista pyydämme teitä vahvistamaan, että tiedätte tämän. Tuloste tilataan sen jälkeen, kun tiedostonne on toimitettu, omana sopimuksenaan; se ei muuta tiedostoanne koskevaa sopimusta.',
    damage: `**Kuljetusvauriot ja virheet.** Tarkistakaa tulosteenne, kun se saapuu. Jos se on vahingoittunut kuljetuksessa tai siinä on virhe, esimerkiksi tulostusvirhe, halkeama tai lommo, kirjoittakaa mahdollisuuksien mukaan 7 päivän kuluessa toimituksesta osoitteeseen ${MAIL} ja liittäkää mukaan tilausnumeronne, kuva vauriosta, kuva koko tulosteesta ja mahdollisuuksien mukaan pakkauksesta: tulostuskumppanimme ottaa reklamaatioita vastaan tuon ajan kuluessa, joten saamme tulosteen silloin vaihdettua nopeimmin. Teetämme vahingoittuneen tai virheellisen tulosteen uudelleen ja lähetämme sen teille maksutta tai, jos se ei ole mahdollista, palautamme sen hinnan. Lakisääteiset oikeutenne, jotka koskevat sopimuksen vastaisia tavaroita, myös kahden vuoden lakisääteinen virhevastuu toimituksesta lukien, ovat voimassa täysimääräisinä: virheestä myöhemmin ilmoittaminen ei vie niitä teiltä.`,
    product: ['Taideteos toimitetaan vain digitaalisena tiedostona, lataamalla. Emme myy tulosteita, kehyksiä emmekä muita fyysisiä tuotteita.', 'Taideteos toimitetaan digitaalisena tiedostona, lataamalla. Euromääräisissä tilauksissa voitte tilata siitä jälkeenpäin tilaussivultanne myös tulosteen: katsokaa [Tulosteet](#prints).'],
    noDelivery: ['Toimituskuluja ei ole.', 'Digitaalisesta tiedostosta ei peritä toimituskuluja; tulosteen osalta katsokaa [Tulosteet](#prints).'],
    hufNote: 'Toimituskuluja ei ole. Tulosteen voi lisätä vain euromääräiseen tilaukseen (katsokaa [Tulosteet](#prints)).',
    withdrawalRef: 'Peruuttamisoikeutta ei sovelleta tulosteisiin: katsokaa [Tulosteet](#prints).',
    defectsRef: 'Tulosteiden osalta katsokaa [Tulosteet](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Kun tilaatte tulosteen',
    priv: [
      'Jos tilaatte tulosteen taideteoksestanne, Stripen maksusivu pyytää tulostetta maksettaessa nimenne ja toimitusosoitteenne. Saamme ne Stripeltä maksunne mukana ja säilytämme niitä tilauksenne yhteydessä.',
      `Tulosteen tekemistä ja lähettämistä varten välitämme nimenne ja toimitusosoitteenne sekä tilausnumeron ja taideteoksestanne tehdyn tulostustiedoston tulostuskumppanillemme ${PRODUCER}, Saksa. Se valmistaa tulosteen EU:ssa ja luovuttaa sen pakettipalvelulle, joka saa nimenne ja osoitteenne toimitusta varten. Picanova käsittelee näitä tietoja meidän lukuumme. Emme anna sille sähköpostiosoitettanne: lähetämme seurantalinkin teille itse.`,
      'Oikeusperuste: sopimus kanssanne (tietosuoja-asetuksen 6 artiklan 1 kohdan b alakohta). Nimenne ja toimitusosoitteenne säilyvät tilaustietueenne yhteydessä niin kauan kuin tuota tietuetta säilytetään (katsokaa [Kuinka kauan säilytämme tietojanne](#retention)); tulostustiedosto poistetaan tilauksenne muiden tiedostojen mukana.',
    ],
    privService: 'Picanova GmbH (merchOne): tulosteiden valmistus ja lähettäminen kohdassa [Kun tilaatte tulosteen](#prints) mainituin tiedoin.',
    privRetention: 'Kun tilaukseen kuuluu tuloste, tilaustietueessa ovat myös nimenne, toimitusosoitteenne ja lähetyksen seurantanumero.',
    wdTitle: 'Tulosteet',
    wd: 'Peruuttamisoikeutta ei sovelleta taideteoksestanne tehtyyn tulosteeseen: tuloste tehdään vaatimustenne mukaisesti henkilökohtaisesta taideteoksestanne (direktiivin 2011/83/EU 16 artiklan c alakohta). Tilaatte tulosteen tilaussivultanne sen jälkeen, kun tiedostonne on toimitettu, omana sopimuksenaan; ennen maksamista pyydämme teitä vahvistamaan, että tiedätte tämän. Tämä ei vaikuta oikeuksiinne, jos tuloste saapuu vahingoittuneena tai virheellisenä: katsokaa [myyntiehtojamme](doc:terms#prints).',
  },
  et: {
    title: 'Trükitud pildid',
    intro: 'Eurodes tehtavate tellimuste puhul saame pärast kunstiteose üleandmist pakkuda teile selle trükitud pilti: füüsilist koopiat täpselt sellest failist, mille saite, valmistatuna tellimuse järgi. Tellite selle oma tellimuse lehelt eraldi lepinguna teie digitaalse faili lepingu kõrval; teie digitaalne fail on sama nii sellega kui ka ilma. Trükitud pildid ja nende hinnad:',
    pricesNote: 'Need on lõpphinnad eurodes; me ei ole käibemaksukohustuslane, seega käibemaksu ei arvestata. Trükitud pildi tarnekulu lisandub vastavalt tarneriigile ning seda näidatakse enne maksmist ja makselehel. Ühe trükitud pildi kohta on see:',
    countries: 'Saadame trükitud pilte ainult nendesse Euroopa Liidu riikidesse. Tarneaadress peab asuma riigis, mille valite enne maksmist; aadressi sisestate makselehel.',
    delivery: `**Tarne.** Saadame teie trükitud pildi tootmisse kohe, kui olete selle tellinud; teie fail on selleks ajaks juba valmis (vt [Üleandmine](#delivery)). ${timesText('et')} Saadetis on jälgitav ja kui see teele läheb, saadame teile e-kirjaga jälgimislingi. Teie trükitud pilt toimetatakse kohale hiljemalt 30 päeva jooksul lepingu sõlmimisest.`,
    maker: `**Tootja.** Teie trükitud pildi valmistab meile meie trükipartner, toote tootja: ${PRODUCER}, Saksamaa, ${PRODUCER_MAIL}. Müüja on SnapEyes (vt [Kellega te lepingu sõlmite](#parties)): palun kirjutage meile kõigi oma trükitud pilti puudutavate küsimustega. Kunstiteos, mis ei ole ruudukujuline, paigutatakse ruudukujulise trükitud pildi keskele ja selle tausta jätkatakse servadeni. Värvid paberil, lõuendil või akrüülklaasi taga võivad paista veidi teistsugused kui teie ekraanil.`,
    withdrawal: '**Trükitud piltide puhul taganemisõigust ei ole.** Trükitud pilt valmistatakse teie esitatud nõuete järgi teie isiklikust kunstiteosest, seega taganemisõigus selle suhtes ei kehti (direktiivi 2011/83/EL artikli 16 punkt c). Enne maksmist palume teil kinnitada, et olete sellest teadlik. Trükitud pilt tellitakse pärast teie faili üleandmist eraldi lepinguna; see ei muuda teie faili lepingut.',
    damage: `**Transpordikahjustused ja puudused.** Palun kontrollige oma trükitud pilti, kui see saabub. Kui see on transpordil kahjustada saanud või puudusega, näiteks trükiviga, mõra või mõlk, kirjutage palun võimaluse korral 7 päeva jooksul pärast kättesaamist aadressile ${MAIL} ning lisage oma tellimuse number, foto kahjustusest, foto kogu trükitud pildist ja võimaluse korral pakendist: meie trükipartner võtab pretensioone vastu selle aja jooksul, nii et saame selle siis kõige kiiremini välja vahetada. Laseme kahjustatud või puudusega trükitud pildi tasuta uuesti valmistada ja teile saata või kui see ei ole võimalik, tagastame selle hinna. Teie seadusest tulenevad õigused lepingutingimustele mittevastava kauba korral, sealhulgas seadusest tulenev kaheaastane vastutus alates kättetoimetamisest, kehtivad täies ulatuses: puudusest hilisem teatamine neid ära ei võta.`,
    product: ['Kunstiteos antakse üle ainult digitaalse failina, allalaadimise teel. Me ei müü trükitud pilte, raame ega muid füüsilisi tooteid.', 'Kunstiteos antakse üle digitaalse failina, allalaadimise teel. Eurodes tehtavate tellimuste puhul saate hiljem oma tellimuse lehelt tellida ka selle trükitud pildi: vt [Trükitud pildid](#prints).'],
    noDelivery: ['Kättetoimetamiskulusid ei ole.', 'Digitaalse faili puhul kättetoimetamiskulusid ei ole; trükitud pildi kohta vt [Trükitud pildid](#prints).'],
    hufNote: 'Kättetoimetamiskulusid ei ole. Trükitud pildi saab lisada ainult eurodes tehtavale tellimusele (vt [Trükitud pildid](#prints)).',
    withdrawalRef: 'Trükitud piltide suhtes taganemisõigus ei kehti: vt [Trükitud pildid](#prints).',
    defectsRef: 'Trükitud piltide kohta vt [Trükitud pildid](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Kui tellite trükitud pildi',
    priv: [
      'Kui tellite oma kunstiteosest trükitud pildi, küsib Stripe’i makseleht trükitud pildi eest maksmisel teie nime ja tarneaadressi. Saame need Stripe’ilt koos teie maksega ja säilitame neid teie tellimuse juures.',
      `Trükitud pildi valmistamiseks ja saatmiseks edastame teie nime ja tarneaadressi koos tellimuse numbri ja teie kunstiteosest tehtud trükifailiga meie trükipartnerile ${PRODUCER}, Saksamaa. Ta valmistab trükitud pildi ELis ja annab selle üle pakiveoteenusele, mis saab kohaletoimetamiseks teie nime ja aadressi. Picanova töötleb neid andmeid meie nimel. Me ei anna talle teie e-posti aadressi: jälgimislingi saadame teile ise.`,
      'Õiguslik alus: teiega sõlmitud leping (IKÜMi artikli 6 lõike 1 punkt b). Teie nimi ja tarneaadress jäävad teie tellimuse kirje juurde seni, kuni seda kirjet säilitatakse (vt [Kui kaua me teie andmeid säilitame](#retention)); trükifail kustutatakse koos teie tellimuse teiste failidega.',
    ],
    privService: 'Picanova GmbH (merchOne): trükitud piltide valmistamine ja saatmine, andmetega, mida on nimetatud jaotises [Kui tellite trükitud pildi](#prints).',
    privRetention: 'Trükitud pildiga tellimuse puhul sisaldab tellimuse kirje ka teie nime, tarneaadressi ja saadetise jälgimisnumbrit.',
    wdTitle: 'Trükitud pildid',
    wd: 'Teie kunstiteose trükitud pildi suhtes taganemisõigus ei kehti: trükitud pilt valmistatakse teie esitatud nõuete järgi teie isiklikust kunstiteosest (direktiivi 2011/83/EL artikli 16 punkt c). Tellite trükitud pildi oma tellimuse lehelt pärast teie faili üleandmist eraldi lepinguna; enne maksmist palume teil kinnitada, et olete sellest teadlik. See ei mõjuta teie õigusi juhul, kui trükitud pilt saabub kahjustatuna või puudusega: vt meie [Müügitingimusi](doc:terms#prints).',
  },
  lv: {
    title: 'Izdrukas',
    intro: 'Pasūtījumiem eiro pēc mākslas darba piegādes varam jums piedāvāt tā izdruku: fizisku tieši tā faila kopiju, ko saņēmāt, izgatavotu pēc pasūtījuma. To pasūtāt savā pasūtījuma lapā kā atsevišķu līgumu līdzās līgumam par jūsu digitālo failu; jūsu digitālais fails ir tāds pats gan ar to, gan bez tās. Izdrukas un to cenas:',
    pricesNote: 'Tās ir galīgās cenas eiro; mēs neesam reģistrēti kā PVN maksātāji, tāpēc PVN netiek piemērots. Izdrukas piegādes maksa tiek pieskaitīta atbilstoši piegādes valstij un parādīta pirms maksāšanas un maksājuma lapā. Par vienu izdruku tā ir:',
    countries: 'Izdrukas sūtām tikai uz šīm Eiropas Savienības valstīm. Piegādes adresei jābūt valstī, ko izvēlaties pirms maksāšanas; adresi ievadāt maksājuma lapā.',
    delivery: `**Piegāde.** Jūsu izdruku nododam ražošanā, tiklīdz tā ir pasūtīta; jūsu fails tad jau ir gatavs (skatiet [Piegāde](#delivery)). ${timesText('lv')} Sūtījums ir izsekojams, un, kad tas ir izsūtīts, nosūtām jums e-pastā izsekošanas saiti. Vēlākais 30 dienu laikā no līguma noslēgšanas jūsu izdruka tiek piegādāta.`,
    maker: `**Ražotājs.** Jūsu izdruku mums izgatavo mūsu drukas partneris, produkta ražotājs: ${PRODUCER}, Vācija, ${PRODUCER_MAIL}. Pārdevējs ir SnapEyes (skatiet [Ar ko jūs slēdzat līgumu](#parties)): ar jebkuru jautājumu par savu izdruku, lūdzu, rakstiet mums. Mākslas darbs, kas nav kvadrātveida, tiek novietots kvadrātveida izdrukas centrā, un tā fons tiek turpināts līdz malām. Krāsas uz papīra, uz audekla vai aiz akrila stikla var izskatīties nedaudz citādas nekā jūsu ekrānā.`,
    withdrawal: '**Izdrukām nav atteikuma tiesību.** Izdruka tiek izgatavota pēc jūsu specifikācijām no jūsu personīgā mākslas darba, tāpēc atteikuma tiesības uz to neattiecas (Direktīvas 2011/83/ES 16. panta c) punkts). Pirms maksāšanas lūdzam jūs apliecināt, ka to zināt. Izdruka tiek pasūtīta pēc jūsu faila piegādes kā atsevišķs līgums; līgumu par jūsu failu tā nemaina.',
    damage: `**Bojājumi pārvadāšanas laikā un trūkumi.** Lūdzu, pārbaudiet izdruku, kad tā pienāk. Ja tā ir bojāta pārvadāšanas laikā vai ar trūkumiem, piemēram, drukas kļūda, plaisa vai iedobums, lūdzu, ja iespējams, 7 dienu laikā pēc piegādes rakstiet uz ${MAIL}, norādot pasūtījuma numuru un pievienojot bojājuma fotogrāfiju, visas izdrukas fotogrāfiju un, ja iespējams, iepakojuma fotogrāfiju: mūsu drukas partneris pretenzijas pieņem šajā laikā, tāpēc tad varam to nomainīt visātrāk. Bojātu izdruku vai izdruku ar trūkumiem liekam izgatavot vēlreiz un nosūtām jums bez maksas vai, ja tas nav iespējams, atmaksājam tās cenu. Jūsu likumīgās tiesības attiecībā uz precēm, kas neatbilst līgumam, tostarp likumā noteiktā divu gadu garantija no piegādes, ir spēkā pilnībā: vēlāka ziņošana par trūkumu tās neatņem.`,
    product: ['Mākslas darbs tiek piegādāts tikai kā digitāls fails, lejupielādējot. Mēs nepārdodam izdrukas, rāmjus vai citus fiziskus produktus.', 'Mākslas darbs tiek piegādāts kā digitāls fails, lejupielādējot. Pasūtījumiem eiro vēlāk savā pasūtījuma lapā varat pasūtīt arī tā izdruku: skatiet [Izdrukas](#prints).'],
    noDelivery: ['Piegādes izmaksu nav.', 'Digitālajam failam piegādes izmaksu nav; par izdruku skatiet [Izdrukas](#prints).'],
    hufNote: 'Piegādes izmaksu nav. Izdruku var pievienot tikai pasūtījumam eiro (skatiet [Izdrukas](#prints)).',
    withdrawalRef: 'Uz izdrukām atteikuma tiesības neattiecas: skatiet [Izdrukas](#prints).',
    defectsRef: 'Par izdrukām skatiet [Izdrukas](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Kad pasūtāt izdruku',
    priv: [
      'Ja pasūtāt sava mākslas darba izdruku, Stripe maksājuma lapa, kurā maksājat par izdruku, prasa jūsu vārdu, uzvārdu un piegādes adresi. Mēs tos saņemam no Stripe kopā ar jūsu maksājumu un glabājam kopā ar jūsu pasūtījumu.',
      `Lai izgatavotu un nosūtītu izdruku, jūsu vārdu, uzvārdu un piegādes adresi kopā ar pasūtījuma numuru un no jūsu mākslas darba izveidoto drukas failu nododam mūsu drukas partnerim ${PRODUCER}, Vācija. Tas izgatavo izdruku ES un nodod to paku piegādes dienestam, kas piegādei saņem jūsu vārdu, uzvārdu un adresi. Picanova apstrādā šos datus mūsu vārdā. Jūsu e-pasta adresi tam nedodam: izsekošanas saiti jums nosūtām paši.`,
      'Juridiskais pamats: līgums ar jums (VDAR 6. panta 1. punkta b) apakšpunkts). Jūsu vārds, uzvārds un piegādes adrese paliek kopā ar jūsu pasūtījuma ierakstu tik ilgi, kamēr šis ieraksts tiek glabāts (skatiet [Cik ilgi glabājam jūsu datus](#retention)); drukas fails tiek dzēsts kopā ar pārējiem jūsu pasūtījuma failiem.',
    ],
    privService: 'Picanova GmbH (merchOne): izdruku izgatavošana un nosūtīšana, ar datiem, kas minēti sadaļā [Kad pasūtāt izdruku](#prints).',
    privRetention: 'Pasūtījumam ar izdruku pasūtījuma ierakstā ir arī jūsu vārds, uzvārds, piegādes adrese un sūtījuma izsekošanas numurs.',
    wdTitle: 'Izdrukas',
    wd: 'Uz jūsu mākslas darba izdruku atteikuma tiesības neattiecas: izdruka tiek izgatavota pēc jūsu specifikācijām no jūsu personīgā mākslas darba (Direktīvas 2011/83/ES 16. panta c) punkts). Izdruku pasūtāt savā pasūtījuma lapā pēc jūsu faila piegādes kā atsevišķu līgumu; pirms maksāšanas lūdzam jūs apliecināt, ka to zināt. Tas neietekmē jūsu tiesības, ja izdruka pienāk bojāta vai ar trūkumiem: skatiet mūsu [Pārdošanas noteikumus](doc:terms#prints).',
  },
};

/** The section with this string replaced; the build stops when the old words are not in it (an edit of the terms must not leave a print
 *  sentence pointing at nothing). */
function swap(s: LegalSection, from: string, to: string): LegalSection {
  let hit = false;
  const blocks = s.blocks.map((b) => {
    if (typeof b === 'string' && b.includes(from)) {
      hit = true;
      return b.replace(from, to);
    }
    return b;
  });
  if (!hit) throw new Error(`prints in the legal texts: "${from}" not found in section ${s.id}`);
  return { ...s, blocks };
}

const add = (...more: Block[]) => (s: LegalSection): LegalSection => ({ ...s, blocks: [...s.blocks, ...more] });

const productName = (kind: Parameters<typeof printLabel>[0], cm: number, lang: Lang) => printLabel(kind, cm, lang);

/** The products and their prices, from api/_lib/print_offer.py. */
function productRows(lang: Lang): Array<[string, string]> {
  return printProducts().map((p) => [productName(p.kind, p.cm, lang), eur(p.price, lang)]);
}

/** The shipping per country (api/_lib/print_rates.py, with VAT and rounded up as the checkout does), grouped by the usual price of a country:
 *  one row per price, its countries by name, and a country where one print ships at another price says so ("Germany (6,99 € for the ...)").
 *  2026-11-24: prints that ship on a tariff of their own (they differ from the most common one in more than FEW countries: the metal print and the
 *  canvas of 60 cm) are left out of those rows and get rows of their own after them, one per price: "13,49 €: <their names>: <the countries>".
 *  Without that, every country's entry would repeat their names. The facts are the same; no word is added. */
const FEW = 3;
export function shippingRows(lang: Lang): Array<[string, string]> {
  const all = printProducts();
  const ccs = printCountries();
  const tariff = (id: string) => ccs.map((cc) => printShipping(cc, id) ?? 0);
  // the prints by their tariff (the same price in every country); the tariff most prints share is the usual one
  const byTariff = new Map<string, typeof all>();
  for (const p of all) byTariff.set(tariff(p.id).join(), [...(byTariff.get(tariff(p.id).join()) ?? []), p]);
  const sets = [...byTariff.values()].sort((a, b) => b.length - a.length);
  const usualTariff = tariff(sets[0][0].id);
  const far = sets.slice(1).filter((g) => tariff(g[0].id).filter((v, i) => v !== usualTariff[i]).length > FEW);
  const prods = all.filter((p) => !far.some((g) => g.includes(p)));
  const groups = new Map<number, string[]>();
  for (const cc of countriesByName(lang, printCountries())) {
    const prices = prods.map((p) => printShipping(cc, p.id) ?? 0);
    const count = new Map<number, number>();
    for (const v of prices) count.set(v, (count.get(v) ?? 0) + 1);
    const usual = [...count.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0])[0][0];
    const odd = prods.flatMap((p, i) => (prices[i] !== usual ? [W[lang].except(productName(p.kind, p.cm, lang), eur(prices[i], lang))] : []));
    const label = countryName(cc, lang) + (odd.length ? ` (${odd.join('; ')})` : '');
    groups.set(usual, [...(groups.get(usual) ?? []), label]);
  }
  const rows: Array<[string, string]> = [...groups.entries()].sort((a, b) => a[0] - b[0]).map(([price, names]) => [eur(price, lang), names.join(', ')]);
  for (const g of far) {
    const names = g.map((p) => productName(p.kind, p.cm, lang)).join(', ');
    const own = new Map<number, string[]>();
    for (const cc of countriesByName(lang, ccs)) {
      const v = printShipping(cc, g[0].id) ?? 0;
      own.set(v, [...(own.get(v) ?? []), countryName(cc, lang)]);
    }
    for (const [price, list] of [...own.entries()].sort((a, b) => a[0] - b[0])) rows.push([eur(price, lang), `${names}: ${list.join(', ')}`]);
  }
  return rows;
}

/** The terms' section "prints". */
function printsSection(lang: Lang): LegalSection {
  const w = W[lang];
  return {
    id: 'prints',
    title: w.title,
    blocks: [w.intro, { dl: productRows(lang) }, w.pricesNote, { dl: shippingRows(lang) }, w.countries, w.delivery, w.maker, w.withdrawal, w.damage],
  };
}

/** The terms of one language with the prints (the EU edition and the Hungarian one). */
export function withPrintsTerms(doc: LegalDoc, lang: Lang): LegalDoc {
  const w = W[lang];
  return patchDoc(doc, {
    replace: {
      product: (s) => swap(s, w.product[0], w.product[1]),
      // the Hungarian edition's price section (in forints) sells no print: it says that a print is only added to an order in euros
      prices: (s) => (s.blocks.some((b) => typeof b === 'string' && b.includes(w.noDelivery[0]) && /\(Ft\)|forint/i.test(b))
        ? swap(s, w.noDelivery[0], w.hufNote) : swap(s, w.noDelivery[0], w.noDelivery[1])),
      withdrawal: add(w.withdrawalRef),
      defects: add(w.defectsRef),
    },
    after: { delivery: [printsSection(lang)] },
  });
}

/** The privacy policy of one language with the print partner: the section "prints" after "orders", a line in the list of services and one
 *  about how long the name and the address are kept. */
export function withPrintsPrivacy(doc: LegalDoc, lang: Lang): LegalDoc {
  const w = W[lang];
  return patchDoc(doc, {
    replace: {
      services: (s) => {
        let hit = false;
        const blocks = s.blocks.map((b) => {
          if (!hit && typeof b === 'object' && 'ul' in b) {
            hit = true;
            return { ul: [...b.ul, w.privService] };
          }
          return b;
        });
        if (!hit) throw new Error(`prints in the privacy policy (${lang}): no list in "services"`);
        return { ...s, blocks };
      },
      retention: add(w.privRetention),
    },
    after: { orders: [{ id: 'prints', title: w.privTitle, blocks: w.priv }] },
  });
}

/** The withdrawal page of one language with its section "prints" (after "expiry"). */
export function withPrintsWithdrawal(doc: LegalDoc, lang: Lang): LegalDoc {
  const w = W[lang];
  return patchDoc(doc, { after: { expiry: [{ id: 'prints', title: w.wdTitle, blocks: [w.wd] }] } });
}

/** An edition's texts of one page, each language patched. */
export function patchEdition(docs: EditionDocs, fn: (d: LegalDoc, l: Lang) => LegalDoc): EditionDocs {
  return Object.fromEntries(Object.entries(docs).map(([l, d]) => [l, d ? fn(d, l as Lang) : d])) as EditionDocs;
}
