// Prints of the artwork (api/_lib/prints.py, src/shared/prints.ts) in the legal texts of the EU edition (and of the Hungarian edition, which
// shares the EU texts): the terms get a section "prints" (the products and prices from api/_lib/print_offer.py, the shipping per country from
// api/_lib/print_rates.py, the delivery countries, the delivery time, the manufacturer as the General Product Safety Regulation (EU) 2023/988
// asks, no right of withdrawal under Art. 16(c) Directive 2011/83/EU, damage in transit and the legal guarantee), and three of their sentences
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
import { countriesByName, countryName, kindName, printCountries, printProducts, printShipping, printSize } from '../../shared/prints';

const PRODUCER = 'Picanova GmbH (merchOne), Eupener Straße 67, 50933 Köln';
const PRODUCER_MAIL = '[support@merchone.com](mailto:support@merchone.com)';

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
    intro: 'On orders in euros, the checkout can offer a print of your artwork as an option: a physical copy of the very file you receive, made to order. Your digital file is the same with or without it. Prints and their prices:',
    pricesNote: 'These are final prices in euros; we are not registered for VAT, so no VAT is charged. The shipping of a print is added for its delivery country and shown before you pay and on the payment page. Per print it is:',
    countries: 'We ship prints only to these countries of the European Union. The delivery address must be in the country you choose before you pay; you enter it on the payment page.',
    delivery: '**Delivery.** We send your print to production as soon as your file is ready (see [Delivery](#delivery)). Production takes about 3 business days; delivery then usually takes 2 to 9 business days, depending on the country (for example 2 to 3 to Germany, 3 to 4 to Lithuania, 4 to 5 to Croatia, 5 to 6 to Hungary). The parcel is tracked, and we email you the tracking link when it ships. At the latest, your print is delivered within 30 days of the contract.',
    maker: `**Manufacturer.** Your print is made for us by our print partner, the manufacturer of the product: ${PRODUCER}, Germany, ${PRODUCER_MAIL}. The seller is SnapEyes (see [Who you contract with](#parties)): please write to us with any question about your print. An artwork that is not square is centred on the square print, and its background is continued to the edges. Colours on paper, on canvas or behind acrylic glass can look slightly different from your screen.`,
    withdrawal: '**No right of withdrawal for prints.** A print is made to your specifications from your personal artwork, so the right of withdrawal does not apply to it (Article 16(c) of Directive 2011/83/EU). Before you pay, we ask you to confirm that you know this. If you withdraw from the contract while your right of withdrawal for the file still lasts, we do not make the print either, and we refund it with the rest of your order.',
    damage: `**Damage in transit and defects.** Please check your print when it arrives. If it is damaged in transit or faulty, for example a printing error, a crack or a dent, please write to ${MAIL} within 7 days of delivery if you can, with your order number, a photo of the damage, a photo of the whole print and, if possible, of the packaging: our print partner takes claims within that time, so we can then have it replaced fastest. We have a damaged or faulty print made again and sent to you free of charge or, if that is not possible, refund it. Your statutory rights for goods that do not conform to the contract, including the legal guarantee of two years from delivery, apply in full: reporting a defect later does not take them away.`,
    product: ['The artwork is delivered only as a digital file, by download. We do not sell prints, frames or any other physical product.', 'The artwork is delivered as a digital file, by download. On orders in euros you can also order a print of it: see [Prints](#prints).'],
    noDelivery: ['There are no delivery costs.', 'There are no delivery costs for the digital file; for a print, see [Prints](#prints).'],
    hufNote: 'There are no delivery costs. A print can be added only to an order in euros (see [Prints](#prints)).',
    withdrawalRef: 'The right of withdrawal does not apply to prints: see [Prints](#prints).',
    defectsRef: 'For prints, see [Prints](#prints).',
    except: (name, price) => `${price} for the ${name}`,
    privTitle: 'When you order a print',
    priv: [
      "If you add a print to your order, Stripe's payment page also asks for your name and delivery address. We receive them from Stripe with your payment and keep them with your order.",
      `To make and send the print, we pass your name and delivery address, with the order number and the print file made from your artwork, to our print partner ${PRODUCER}, Germany. It produces the print in the EU and hands it to a parcel service, which receives your name and address for the delivery. Picanova processes these data on our behalf. We do not give it your email address: we send you the tracking link ourselves.`,
      'Legal basis: the contract with you (Art. 6(1)(b) GDPR). Your name and delivery address stay with your order record for as long as that record is kept (see [How long we keep your data](#retention)); the print file is deleted with the other files of your order.',
    ],
    privService: 'Picanova GmbH (merchOne): production and shipping of prints, with the data named in [When you order a print](#prints).',
    privRetention: 'For an order with a print, the order record also holds your name, your delivery address and the tracking number of the parcel.',
    wdTitle: 'Prints',
    wd: 'The right of withdrawal does not apply to a print of your artwork that you order with it: a print is made to your specifications from your personal artwork (Article 16(c) of Directive 2011/83/EU). If you withdraw from the contract while your right of withdrawal for the file lasts, we do not make the print either, and we refund it with the rest of your order. Your rights if a print arrives damaged or faulty are not affected: see our [Terms of sale](doc:terms#prints).',
  },
  de: {
    title: 'Drucke',
    intro: 'Bei Bestellungen in Euro kann die Kasse optional einen Druck Ihres Kunstwerks anbieten: ein physisches Exemplar genau der Datei, die Sie erhalten, nach Ihrer Bestellung angefertigt. Ihre digitale Datei ist mit oder ohne Druck dieselbe. Drucke und ihre Preise:',
    pricesNote: 'Das sind Endpreise in Euro; wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet. Die Versandkosten eines Drucks richten sich nach dem Lieferland und werden vor der Zahlung und auf der Zahlungsseite angezeigt. Sie betragen je Druck:',
    countries: 'Wir liefern Drucke nur in diese Länder der Europäischen Union. Die Lieferadresse muss in dem Land liegen, das Sie vor der Zahlung wählen; Sie geben sie auf der Zahlungsseite ein.',
    delivery: '**Lieferung.** Wir geben Ihren Druck in die Produktion, sobald Ihre Datei fertig ist (siehe [Lieferung](#delivery)). Die Produktion dauert etwa 3 Werktage; die Zustellung dauert danach je nach Land meist 2 bis 9 Werktage (zum Beispiel 2 bis 3 nach Deutschland, 3 bis 4 nach Litauen, 4 bis 5 nach Kroatien, 5 bis 6 nach Ungarn). Die Sendung ist verfolgbar, und wir senden Ihnen den Link zur Sendungsverfolgung, sobald sie versandt ist. Spätestens wird Ihr Druck innerhalb von 30 Tagen nach Vertragsschluss geliefert.',
    maker: `**Hersteller.** Ihr Druck wird für uns von unserem Druckpartner hergestellt, dem Hersteller des Produkts: ${PRODUCER}, Deutschland, ${PRODUCER_MAIL}. Verkäufer ist SnapEyes (siehe [Ihr Vertragspartner](#parties)): Bei Fragen zu Ihrem Druck schreiben Sie bitte uns. Ein Kunstwerk, das nicht quadratisch ist, wird mittig auf den quadratischen Druck gesetzt, und sein Hintergrund wird bis zum Rand fortgeführt. Farben auf Papier, auf Leinwand oder hinter Acrylglas können leicht von Ihrem Bildschirm abweichen.`,
    withdrawal: '**Kein Widerrufsrecht für Drucke.** Ein Druck wird nach Ihren Vorgaben aus Ihrem persönlichen Kunstwerk angefertigt, daher besteht für ihn kein Widerrufsrecht (Artikel 16 Buchstabe c der Richtlinie 2011/83/EU). Vor der Zahlung bitten wir Sie zu bestätigen, dass Ihnen das bekannt ist. Widerrufen Sie den Vertrag, solange Ihr Widerrufsrecht für die Datei noch besteht, fertigen wir auch den Druck nicht an und erstatten ihn mit dem Rest Ihrer Bestellung.',
    damage: `**Transportschäden und Mängel.** Bitte prüfen Sie Ihren Druck, wenn er ankommt. Ist er auf dem Transport beschädigt worden oder fehlerhaft, zum Beispiel durch einen Druckfehler, einen Riss oder eine Delle, schreiben Sie bitte möglichst innerhalb von 7 Tagen nach der Zustellung an ${MAIL}, mit Ihrer Bestellnummer, einem Foto des Schadens, einem Foto des ganzen Drucks und, wenn möglich, der Verpackung: Unser Druckpartner nimmt Reklamationen innerhalb dieser Frist an, so können wir ihn am schnellsten ersetzen lassen. Einen beschädigten oder fehlerhaften Druck lassen wir kostenlos neu anfertigen und Ihnen zusenden oder erstatten ihn, wenn das nicht möglich ist. Ihre gesetzlichen Rechte bei mangelhafter Ware, einschließlich der gesetzlichen Gewährleistung von zwei Jahren ab Lieferung, gelten uneingeschränkt: Eine spätere Meldung lässt sie nicht entfallen.`,
    product: ['Das Kunstwerk wird ausschließlich als digitale Datei zum Download geliefert. Drucke, Rahmen oder andere physische Produkte verkaufen wir nicht.', 'Das Kunstwerk wird als digitale Datei zum Download geliefert. Bei Bestellungen in Euro können Sie zusätzlich einen Druck davon bestellen: siehe [Drucke](#prints).'],
    noDelivery: ['Versandkosten fallen nicht an.', 'Für die digitale Datei fallen keine Versandkosten an; zu Drucken siehe [Drucke](#prints).'],
    hufNote: 'Versandkosten fallen nicht an. Ein Druck kann nur zu einer Bestellung in Euro hinzugefügt werden (siehe [Drucke](#prints)).',
    withdrawalRef: 'Für Drucke besteht kein Widerrufsrecht: siehe [Drucke](#prints).',
    defectsRef: 'Zu Drucken siehe [Drucke](#prints).',
    except: (name, price) => `${price} für ${name}`,
    privTitle: 'Wenn Sie einen Druck bestellen',
    priv: [
      'Fügen Sie Ihrer Bestellung einen Druck hinzu, fragt die Zahlungsseite von Stripe auch nach Ihrem Namen und Ihrer Lieferadresse. Wir erhalten sie mit Ihrer Zahlung von Stripe und bewahren sie bei Ihrer Bestellung auf.',
      `Um den Druck herzustellen und zu versenden, geben wir Ihren Namen und Ihre Lieferadresse mit der Bestellnummer und der aus Ihrem Kunstwerk erstellten Druckdatei an unseren Druckpartner ${PRODUCER}, Deutschland, weiter. Er stellt den Druck in der EU her und übergibt ihn einem Paketdienst, der dafür Ihren Namen und Ihre Adresse erhält. Picanova verarbeitet diese Daten in unserem Auftrag. Ihre E-Mail-Adresse geben wir nicht weiter: Den Link zur Sendungsverfolgung senden wir Ihnen selbst.`,
      'Rechtsgrundlage: der Vertrag mit Ihnen (Art. 6 Abs. 1 lit. b DSGVO). Ihr Name und Ihre Lieferadresse bleiben so lange bei Ihrem Bestelldatensatz, wie er aufbewahrt wird (siehe [Wie lange wir Ihre Daten speichern](#retention)); die Druckdatei wird mit den anderen Dateien Ihrer Bestellung gelöscht.',
    ],
    privService: 'Picanova GmbH (merchOne): Herstellung und Versand von Drucken, mit den unter [Wenn Sie einen Druck bestellen](#prints) genannten Daten.',
    privRetention: 'Bei einer Bestellung mit Druck enthält der Bestelldatensatz auch Ihren Namen, Ihre Lieferadresse und die Sendungsnummer des Pakets.',
    wdTitle: 'Drucke',
    wd: 'Für einen Druck Ihres Kunstwerks, den Sie mitbestellen, besteht kein Widerrufsrecht: Ein Druck wird nach Ihren Vorgaben aus Ihrem persönlichen Kunstwerk angefertigt (Artikel 16 Buchstabe c der Richtlinie 2011/83/EU). Widerrufen Sie den Vertrag, solange Ihr Widerrufsrecht für die Datei besteht, fertigen wir auch den Druck nicht an und erstatten ihn mit dem Rest Ihrer Bestellung. Ihre Rechte, wenn ein Druck beschädigt oder fehlerhaft ankommt, bleiben unberührt: siehe unsere [AGB](doc:terms#prints).',
  },
  lt: {
    title: 'Spaudiniai',
    intro: 'Užsakydami eurais, atsiskaitymo metu galite pasirinkti papildomą savo kūrinio spaudinį: fizinę būtent to failo, kurį gaunate, kopiją, pagamintą pagal užsakymą. Jūsų skaitmeninis failas su spaudiniu ar be jo yra tas pats. Spaudiniai ir jų kainos:',
    pricesNote: 'Tai galutinės kainos eurais; nesame PVM mokėtojai, todėl PVM netaikomas. Spaudinio siuntimo kaina priklauso nuo pristatymo šalies ir parodoma prieš mokant bei mokėjimo puslapyje. Vienam spaudiniui ji yra:',
    countries: 'Spaudinius siunčiame tik į šias Europos Sąjungos šalis. Pristatymo adresas turi būti šalyje, kurią pasirenkate prieš mokėdami; jį įvedate mokėjimo puslapyje.',
    delivery: '**Pristatymas.** Spaudinį perduodame gaminti, kai tik Jūsų failas būna paruoštas (žr. [Pristatymas](#delivery)). Gamyba trunka apie 3 darbo dienas, o pristatymas, atsižvelgiant į šalį, paprastai trunka nuo 2 iki 9 darbo dienų (pavyzdžiui, į Vokietiją nuo 2 iki 3, į Lietuvą nuo 3 iki 4, į Kroatiją nuo 4 iki 5, į Vengriją nuo 5 iki 6). Siuntą galima sekti, o kai spaudinys išsiunčiamas, el. paštu atsiunčiame siuntos sekimo nuorodą. Vėliausiai spaudinys pristatomas per 30 dienų nuo sutarties sudarymo.',
    maker: `**Gamintojas.** Spaudinį mums gamina mūsų spaudos partneris, gaminio gamintojas: ${PRODUCER}, Vokietija, ${PRODUCER_MAIL}. Pardavėjas yra SnapEyes (žr. [Su kuo sudarote sutartį](#parties)): visais klausimais dėl spaudinio rašykite mums. Ne kvadratinis kūrinys dedamas kvadratinio spaudinio centre, o jo fonas pratęsiamas iki kraštų. Spalvos ant popieriaus, drobės ar po akriliniu stiklu gali šiek tiek skirtis nuo matomų ekrane.`,
    withdrawal: '**Spaudiniams teisė atsisakyti sutarties netaikoma.** Spaudinys gaminamas pagal Jūsų nurodymus iš Jūsų asmeninio kūrinio, todėl teisė atsisakyti sutarties jam netaikoma (Direktyvos 2011/83/ES 16 straipsnio c punktas). Prieš mokėjimą paprašome patvirtinti, kad tai žinote. Jei atsisakote sutarties, kol Jūsų teisė atsisakyti sutarties dėl failo dar galioja, spaudinio taip pat negaminame ir grąžiname už jį sumokėtus pinigus kartu su likusia užsakymo dalimi.',
    damage: `**Pažeidimai pervežant ir trūkumai.** Gavę spaudinį, jį patikrinkite. Jei jis sugadintas pervežant arba turi trūkumų, pavyzdžiui, spaudos klaidą, įtrūkimą ar įlenkimą, jei galite, per 7 dienas nuo pristatymo parašykite adresu ${MAIL}, nurodykite užsakymo numerį ir pridėkite pažeidimo nuotrauką, viso spaudinio nuotrauką ir, jei įmanoma, pakuotės nuotrauką: mūsų spaudos partneris pretenzijas priima per šį laiką, todėl tada greičiausiai pasirūpinsime pakeitimu. Sugadintą ar trūkumų turintį spaudinį nemokamai pagaminsime iš naujo ir atsiųsime arba, jei tai neįmanoma, grąžinsime už jį sumokėtus pinigus. Jūsų įstatyminės teisės dėl sutarties neatitinkančių prekių, įskaitant dvejų metų nuo pristatymo įstatyminę garantiją, galioja visa apimtimi: vėlesnis pranešimas apie trūkumą jų neatima.`,
    product: ['Kūrinys pateikiamas tik kaip skaitmeninis failas, jį atsisiunčiant. Spaudinių, rėmelių ar kitų fizinių produktų neparduodame.', 'Kūrinys pateikiamas kaip skaitmeninis failas, jį atsisiunčiant. Užsakydami eurais, galite papildomai užsisakyti jo spaudinį: žr. [Spaudiniai](#prints).'],
    noDelivery: ['Pristatymo išlaidų nėra.', 'Skaitmeninio failo pristatymo išlaidų nėra; apie spaudinius žr. [Spaudiniai](#prints).'],
    hufNote: 'Pristatymo išlaidų nėra. Spaudinį galima pridėti tik prie užsakymo eurais (žr. [Spaudiniai](#prints)).',
    withdrawalRef: 'Spaudiniams teisė atsisakyti sutarties netaikoma: žr. [Spaudiniai](#prints).',
    defectsRef: 'Dėl spaudinių žr. [Spaudiniai](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Kai užsisakote spaudinį',
    priv: [
      'Jei prie užsakymo pridedate spaudinį, Stripe mokėjimo puslapyje taip pat prašoma nurodyti Jūsų vardą, pavardę ir pristatymo adresą. Juos kartu su mokėjimu gauname iš Stripe ir saugome su Jūsų užsakymu.',
      `Kad spaudinį pagamintume ir išsiųstume, Jūsų vardą, pavardę ir pristatymo adresą kartu su užsakymo numeriu ir iš Jūsų kūrinio paruoštu spaudos failu perduodame mūsų spaudos partneriui ${PRODUCER}, Vokietija. Jis pagamina spaudinį ES ir perduoda jį siuntų tarnybai, kuri pristatymui gauna Jūsų vardą, pavardę ir adresą. Picanova šiuos duomenis tvarko mūsų vardu. Jūsų el. pašto adreso jam neperduodame: siuntos sekimo nuorodą atsiunčiame patys.`,
      'Teisinis pagrindas: sutartis su Jumis (BDAR 6 straipsnio 1 dalies b punktas). Jūsų vardas, pavardė ir pristatymo adresas saugomi su Jūsų užsakymo įrašu tol, kol saugomas šis įrašas (žr. [Kiek laiko saugome Jūsų duomenis](#retention)); spaudos failas ištrinamas kartu su kitais užsakymo failais.',
    ],
    privService: 'Picanova GmbH (merchOne): spaudinių gamyba ir siuntimas, su skyriuje [Kai užsisakote spaudinį](#prints) nurodytais duomenimis.',
    privRetention: 'Jei užsakyme yra spaudinys, užsakymo įraše taip pat saugomas Jūsų vardas, pavardė, pristatymo adresas ir siuntos sekimo numeris.',
    wdTitle: 'Spaudiniai',
    wd: 'Kartu užsakytam Jūsų kūrinio spaudiniui teisė atsisakyti sutarties netaikoma: spaudinys gaminamas pagal Jūsų nurodymus iš Jūsų asmeninio kūrinio (Direktyvos 2011/83/ES 16 straipsnio c punktas). Jei atsisakote sutarties, kol Jūsų teisė atsisakyti sutarties dėl failo galioja, spaudinio taip pat negaminame ir grąžiname už jį sumokėtus pinigus kartu su likusia užsakymo dalimi. Jūsų teisės, jei spaudinys atkeliauja sugadintas ar su trūkumais, nesumažėja: žr. mūsų [pardavimo sąlygas](doc:terms#prints).',
  },
  hu: {
    title: 'Nyomatok',
    intro: 'Euróban leadott megrendeléshez a pénztár választhatóan felkínálhatja az alkotása nyomatát: pontosan annak a fájlnak a megrendelésre készült fizikai példányát, amelyet Ön megkap. A digitális fájlja nyomattal vagy anélkül ugyanaz. A nyomatok és áraik:',
    pricesNote: 'Ezek euróban értendő végső árak; nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel. A nyomat szállítási díja a szállítási országtól függ, és a fizetés előtt, valamint a fizetési oldalon látható. Nyomatonként:',
    countries: 'Nyomatot csak az Európai Unió alábbi országaiba szállítunk. A szállítási címnek abban az országban kell lennie, amelyet a fizetés előtt kiválaszt; a címet a fizetési oldalon adja meg.',
    delivery: '**Szállítás.** A nyomatot azonnal gyártásba adjuk, amint elkészült a fájlja (lásd [Teljesítés](#delivery)). A gyártás körülbelül 3 munkanap, a kézbesítés ezután országtól függően általában 2 és 9 munkanap között tart (például Németországba 2 vagy 3, Litvániába 3 vagy 4, Horvátországba 4 vagy 5, Magyarországra 5 vagy 6 munkanap). A csomag nyomon követhető, és a feladáskor e-mailben elküldjük a csomagkövetési linket. A nyomatot legkésőbb a szerződéskötéstől számított 30 napon belül kézbesítjük.',
    maker: `**Gyártó.** A nyomatot nyomdai partnerünk, a termék gyártója készíti nekünk: ${PRODUCER}, Németország, ${PRODUCER_MAIL}. Az eladó a SnapEyes (lásd [Kivel köt szerződést](#parties)): a nyomattal kapcsolatos kérdéseivel nekünk írjon. A nem négyzet alakú alkotást a négyzetes nyomat közepére helyezzük, és a hátterét a széléig folytatjuk. A színek papíron, vásznon vagy akrilüveg mögött kissé eltérhetnek a képernyőn látottól.`,
    withdrawal: '**A nyomatokra nem vonatkozik az elállási jog.** A nyomat az Ön utasításai szerint, az Ön személyes alkotásából készül, ezért arra az elállási jog nem vonatkozik (a 2011/83/EU irányelv 16. cikkének c) pontja). Fizetés előtt megkérjük, hogy erősítse meg: tudomásul vette ezt. Ha a szerződéstől addig áll el, amíg a fájlra vonatkozó elállási joga még fennáll, a nyomatot sem készítjük el, és az árát a megrendelés többi részével együtt visszatérítjük.',
    damage: `**Szállítási sérülés és hibák.** Kérjük, nézze meg a nyomatot, amikor megérkezik. Ha szállítás közben megsérült vagy hibás, például nyomdai hiba, repedés vagy horpadás miatt, lehetőleg a kézbesítéstől számított 7 napon belül írjon a(z) ${MAIL} címre a rendelésszámmal, egy fotóval a sérülésről, egy fotóval a teljes nyomatról és, ha lehet, a csomagolásról: nyomdai partnerünk ezen az időn belül fogadja be a reklamációt, így tudjuk a leggyorsabban kicseréltetni. A sérült vagy hibás nyomatot díjmentesen újra elkészíttetjük és elküldjük, vagy ha ez nem lehetséges, visszatérítjük az árát. A szerződésnek nem megfelelő termékre vonatkozó törvényes jogai, köztük a kézbesítéstől számított kétéves kellékszavatosság, teljes körűen megilletik: a későbbi bejelentés ezeket nem szünteti meg.`,
    product: ['Az alkotást kizárólag digitális fájlként, letöltéssel szolgáltatjuk. Nyomatot, keretet vagy más fizikai terméket nem árusítunk.', 'Az alkotást digitális fájlként, letöltéssel szolgáltatjuk. Euróban leadott megrendeléshez nyomatot is rendelhet belőle: lásd [Nyomatok](#prints).'],
    noDelivery: ['Szállítási költség nincs.', 'A digitális fájlnak nincs szállítási költsége; a nyomatokról lásd [Nyomatok](#prints).'],
    hufNote: 'Szállítási költség nincs. Nyomatot csak euróban leadott megrendeléshez lehet rendelni (lásd [Nyomatok](#prints)).',
    withdrawalRef: 'A nyomatokra az elállási jog nem vonatkozik: lásd [Nyomatok](#prints).',
    defectsRef: 'A nyomatokról lásd [Nyomatok](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Ha nyomatot rendel',
    priv: [
      'Ha nyomatot ad a megrendeléséhez, a Stripe fizetési oldala a nevét és a szállítási címét is elkéri. Ezeket a fizetéssel együtt a Stripe-tól kapjuk meg, és a megrendelésével együtt őrizzük.',
      `A nyomat elkészítéséhez és elküldéséhez a nevét és a szállítási címét a rendelésszámmal és az alkotásából készült nyomdai fájllal együtt átadjuk nyomdai partnerünknek: ${PRODUCER}, Németország. A partner az EU-ban elkészíti a nyomatot, és átadja egy csomagszállítónak, amely a kézbesítéshez megkapja a nevét és a címét. A Picanova ezeket az adatokat a megbízásunkból kezeli. Az e-mail-címét nem adjuk át neki: a csomagkövetési linket mi magunk küldjük el.`,
      'Jogalap: az Önnel kötött szerződés (GDPR 6. cikk (1) bekezdés b) pont). A nevét és a szállítási címét a rendelési nyilvántartással együtt addig őrizzük, ameddig azt megőrizzük (lásd [Meddig őrizzük az adatait](#retention)); a nyomdai fájlt a megrendelés többi fájljával együtt töröljük.',
    ],
    privService: 'Picanova GmbH (merchOne): nyomatok gyártása és szállítása, a [Ha nyomatot rendel](#prints) részben megnevezett adatokkal.',
    privRetention: 'Nyomatot tartalmazó megrendelésnél a rendelési nyilvántartás a nevét, a szállítási címét és a csomag követési számát is tartalmazza.',
    wdTitle: 'Nyomatok',
    wd: 'Az alkotásával együtt megrendelt nyomatra az elállási jog nem vonatkozik: a nyomat az Ön utasításai szerint, az Ön személyes alkotásából készül (a 2011/83/EU irányelv 16. cikkének c) pontja). Ha a szerződéstől addig áll el, amíg a fájlra vonatkozó elállási joga fennáll, a nyomatot sem készítjük el, és az árát a megrendelés többi részével együtt visszatérítjük. Ez nem érinti a jogait, ha a nyomat sérülten vagy hibásan érkezik: lásd az [ÁSZF-et](doc:terms#prints).',
  },
  hr: {
    title: 'Ispisi',
    intro: 'Uz narudžbe u eurima naplata može ponuditi ispis vašeg umjetničkog djela kao mogućnost: fizički primjerak upravo one datoteke koju dobivate, izrađen po narudžbi. Vaša digitalna datoteka ista je s ispisom ili bez njega. Ispisi i njihove cijene:',
    pricesNote: 'To su konačne cijene u eurima; nismo obveznik PDV-a, stoga se PDV ne obračunava. Dostava ispisa naplaćuje se prema zemlji dostave i prikazuje se prije plaćanja i na stranici za plaćanje. Po ispisu iznosi:',
    countries: 'Ispise šaljemo samo u ove zemlje Europske unije. Adresa za dostavu mora biti u zemlji koju odaberete prije plaćanja; unosite je na stranici za plaćanje.',
    delivery: '**Dostava.** Vaš ispis predajemo u izradu čim je vaša datoteka gotova (pogledajte [Isporuka](#delivery)). Izrada traje oko 3 radna dana, a dostava zatim obično 2 do 9 radnih dana, ovisno o zemlji (primjerice 2 do 3 u Njemačku, 3 do 4 u Litvu, 4 do 5 u Hrvatsku, 5 do 6 u Mađarsku). Pošiljka se može pratiti, a kad je pošaljemo, e-poštom vam šaljemo poveznicu za praćenje. Ispis vam isporučujemo najkasnije u roku od 30 dana od sklapanja ugovora.',
    maker: `**Proizvođač.** Vaš ispis za nas izrađuje naš partner za ispis, proizvođač proizvoda: ${PRODUCER}, Njemačka, ${PRODUCER_MAIL}. Prodavatelj je SnapEyes (pogledajte [S kim sklapate ugovor](#parties)): sa svim pitanjima o ispisu obratite se nama. Umjetničko djelo koje nije kvadratno postavlja se u sredinu kvadratnog ispisa, a njegova se pozadina nastavlja do rubova. Boje na papiru, platnu ili iza akrilnog stakla mogu se malo razlikovati od onih na zaslonu.`,
    withdrawal: '**Za ispise nema prava na jednostrani raskid ugovora.** Ispis se izrađuje prema vašim zahtjevima iz vašeg osobnog umjetničkog djela, pa se pravo na jednostrani raskid ugovora na njega ne primjenjuje (članak 16. točka (c) Direktive 2011/83/EU). Prije plaćanja molimo vas da potvrdite da to znate. Ako jednostrano raskinete ugovor dok vaše pravo na raskid za datoteku još traje, ni ispis ne izrađujemo, a njegov iznos vraćamo zajedno s ostatkom narudžbe.',
    damage: `**Oštećenja u prijevozu i nedostaci.** Pregledajte ispis kad stigne. Ako je oštećen u prijevozu ili neispravan, primjerice zbog pogreške u ispisu, pukotine ili udubljenja, ako možete, pišite nam u roku od 7 dana od dostave na ${MAIL} s brojem narudžbe, fotografijom oštećenja, fotografijom cijelog ispisa i, ako je moguće, ambalaže: naš partner za ispis prima reklamacije u tom roku, pa ga tada najbrže možemo zamijeniti. Oštećen ili neispravan ispis besplatno ćemo ponovno izraditi i poslati vam ili, ako to nije moguće, vratiti njegov iznos. Vaša zakonska prava za robu koja nije u skladu s ugovorom, uključujući zakonsko jamstvo od dvije godine od dostave, vrijede u cijelosti: kasnija prijava ih ne ukida.`,
    product: ['Umjetničko djelo isporučuje se samo kao digitalna datoteka, preuzimanjem. Ne prodajemo otiske, okvire ni bilo kakve druge fizičke proizvode.', 'Umjetničko djelo isporučuje se kao digitalna datoteka, preuzimanjem. Uz narudžbu u eurima možete naručiti i njegov ispis: pogledajte [Ispisi](#prints).'],
    noDelivery: ['Troškova isporuke nema.', 'Za digitalnu datoteku nema troškova isporuke; za ispise pogledajte [Ispisi](#prints).'],
    hufNote: 'Troškova isporuke nema. Ispis se može dodati samo narudžbi u eurima (pogledajte [Ispisi](#prints)).',
    withdrawalRef: 'Pravo na jednostrani raskid ugovora ne primjenjuje se na ispise: pogledajte [Ispisi](#prints).',
    defectsRef: 'Za ispise pogledajte [Ispisi](#prints).',
    except: (name, price) => `${name}: ${price}`,
    privTitle: 'Kad naručite ispis',
    priv: [
      'Ako narudžbi dodate ispis, Stripeova stranica za plaćanje traži i vaše ime i adresu za dostavu. Primamo ih od Stripea s vašim plaćanjem i čuvamo ih uz vašu narudžbu.',
      `Kako bismo izradili i poslali ispis, vaše ime i adresu za dostavu, s brojem narudžbe i datotekom za ispis izrađenom iz vašeg umjetničkog djela, prosljeđujemo našem partneru za ispis ${PRODUCER}, Njemačka. On izrađuje ispis u EU-u i predaje ga dostavnoj službi, koja za dostavu dobiva vaše ime i adresu. Picanova te podatke obrađuje u naše ime. Vašu adresu e-pošte ne prosljeđujemo: poveznicu za praćenje šaljemo vam sami.`,
      'Pravna osnova: ugovor s vama (članak 6. stavak 1. točka (b) OUZP-a). Vaše ime i adresa za dostavu ostaju uz zapis o vašoj narudžbi dok god se on čuva (pogledajte [Koliko dugo čuvamo vaše podatke](#retention)); datoteka za ispis briše se s ostalim datotekama vaše narudžbe.',
    ],
    privService: 'Picanova GmbH (merchOne): izrada i slanje ispisa, s podacima navedenima u odjeljku [Kad naručite ispis](#prints).',
    privRetention: 'Za narudžbu s ispisom zapis o narudžbi sadržava i vaše ime, adresu za dostavu i broj za praćenje pošiljke.',
    wdTitle: 'Ispisi',
    wd: 'Za ispis vašeg umjetničkog djela koji naručite uz njega nema prava na jednostrani raskid ugovora: ispis se izrađuje prema vašim zahtjevima iz vašeg osobnog umjetničkog djela (članak 16. točka (c) Direktive 2011/83/EU). Ako jednostrano raskinete ugovor dok vaše pravo na raskid za datoteku traje, ni ispis ne izrađujemo, a njegov iznos vraćamo zajedno s ostatkom narudžbe. To ne utječe na vaša prava ako ispis stigne oštećen ili neispravan: pogledajte naše [Opće uvjete prodaje](doc:terms#prints).',
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

const productName = (kind: Parameters<typeof kindName>[0], cm: number, lang: Lang) => `${kindName(kind, lang)} ${printSize(cm)}`;

/** The products and their prices, from api/_lib/print_offer.py. */
function productRows(lang: Lang): Array<[string, string]> {
  return printProducts().map((p) => [productName(p.kind, p.cm, lang), eur(p.price, lang)]);
}

/** The shipping per country (api/_lib/print_rates.py, with VAT and rounded up as the checkout does), grouped by the usual price of a country:
 *  one row per price, its countries by name, and a country where one print ships at another price says so ("Germany (6,99 € for the ...)"). */
export function shippingRows(lang: Lang): Array<[string, string]> {
  const prods = printProducts();
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
  return [...groups.entries()].sort((a, b) => a[0] - b[0]).map(([price, names]) => [eur(price, lang), names.join(', ')]);
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
