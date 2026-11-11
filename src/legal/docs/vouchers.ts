// Gift vouchers (api/_lib/voucher.py, the gift page src/gift) in the legal texts of the EU edition: the terms get a section "vouchers" after
// "prices" (what a voucher is, its two kinds and their prices, 12 months, one order, no cash, the rest not paid out, the contract and the
// right of withdrawal of an unused voucher) and one sentence in "prices"; the privacy policy a section "vouchers" after "orders" (the buyer's
// email address only at Stripe and in the email, no address in our record, the code derived and not stored) and a line on how long the
// record is kept; the withdrawal page a section "vouchers" after "expiry". Vouchers are sold and redeemed in euros only: the Australian, the
// US and the Hungarian (forint) terms are made without them; the Hungarian edition shares the EU privacy policy and withdrawal page, whose
// sections say "in euros".
// The prices are the standard euro prices of a one-eye artwork in any style other than Clean Iris and of a two-eye artwork (src/legal/facts.ts
// PRICE_CENTS, from api/_lib/markets.py), as api/_lib/voucher.py value_of takes them.
// Not reviewed by a lawyer.
import type { Block, LegalDoc, LegalSection } from '../types';
import type { Lang } from '../../shared/lang';
import { patchDoc } from '../patch';
import { eur, MAIL, PRICE_CENTS } from '../facts';

interface Words {
  title: string;
  intro: string;
  rows: [string, string];
  rules: string;
  contract: string;
  withdrawal: string;
  pricesRef: string;
  // the same place in the Hungarian edition's price section (forints): vouchers do not pay for an order in forints
  hufRef: string;
  // the Hungarian edition's voucher table: its terms print no euro price list (scripts/check_texts.mjs checkPack), and a voucher is bought under the EU edition
  hufPrice: string;
  privTitle: string;
  priv: string[];
  privRetention: [string, string];
  wdTitle: string;
  wd: string;
}

const W: Record<Lang, Words> = {
  en: {
    title: 'Gift vouchers',
    intro: 'You can buy a gift voucher for someone else on our [gift page](/gift): a code for one order on snapeyes.com in euros. The person who has the code photographs their own eye, chooses a style, sees the free preview and enters the code at checkout. Vouchers and their prices:',
    rows: ['Voucher for an artwork of one eye, any style', 'Voucher for an artwork of two eyes, any style'],
    rules: 'A voucher is valid for 12 months from its purchase (the last day is in the email with the code) and can be used once, for one order in euros. If the order costs less than the voucher, the rest is not paid out and cannot be used later; if it costs more, the difference is paid on the payment page. A voucher cannot be exchanged for cash. Anyone who has the code can use it, so please keep it safe.',
    contract: 'You pay for a voucher in advance through our payment provider Stripe. The contract for the voucher is concluded when your payment is confirmed: we then show the code on the page you return to and email it to you, with these terms and the withdrawal information as text. An order paid with a voucher is a contract of its own between us and the person who places it, under these terms.',
    withdrawal: `You can withdraw from the purchase of a voucher within 14 days of the purchase, without giving any reason, as long as the voucher has not been used: write to ${MAIL} with the voucher code (you may use the model form on our page [Right of withdrawal](doc:withdrawal)). We refund the full price within 14 days, with the same payment method, and cancel the code. For an order paid with a voucher, the right of withdrawal of that order applies (see [Right of withdrawal](#withdrawal)).`,
    pricesRef: 'A gift voucher can pay for an order in part or in full: see [Gift vouchers](#vouchers).',
    hufRef: 'Gift vouchers are sold and used in euros only, so they cannot pay for an order in forints: see [Gift vouchers](#vouchers).',
    hufPrice: 'sold in euros on our gift page',
    privTitle: 'Gift vouchers',
    priv: [
      'When you buy a gift voucher, you enter your email address on the payment page of Stripe. We use it only to send you the voucher code, these details and our terms. Our own record of the voucher holds no email address: its kind, its value, the dates, the last four characters of the code and the Stripe payment session, through which we can find the payment and your email address at Stripe, for example if you withdraw. The code itself is not stored: our server derives it from the payment with a secret key. At Stripe we create a single-use discount for the code, which names the payment session and the kind of voucher.',
      'The person who uses the voucher orders like any other customer (see [When you order](#orders)). We do not tell the buyer anything about that order.',
      'Legal basis: the contract with you (Art. 6(1)(b) GDPR); for accounting records, our legal obligations (Art. 6(1)(c) GDPR).',
    ],
    privRetention: ['Gift vouchers', 'The record of a voucher (without an email address) is kept like an order record; the email with the code as described for emails.'],
    wdTitle: 'Gift vouchers',
    wd: `**Gift vouchers** (sold in euros) can be withdrawn within 14 days of their purchase, as long as the voucher has not been used. The period starts on the day you buy the voucher. Please write to us (${MAIL}) with the voucher code; you may use the model form below. We refund the full price and cancel the code. The online withdrawal function is for orders of artworks; for a voucher, please write to us. An order paid with a voucher has the right of withdrawal described above.`,
  },
  de: {
    title: 'Geschenkgutscheine',
    intro: 'Auf unserer [Geschenkseite](/gift) können Sie einen Geschenkgutschein für eine andere Person kaufen: einen Code für eine Bestellung auf snapeyes.com in Euro. Wer den Code hat, fotografiert das eigene Auge, wählt einen Stil, sieht die kostenlose Vorschau und gibt den Code an der Kasse ein. Gutscheine und ihre Preise:',
    rows: ['Gutschein für ein Kunstwerk mit einem Auge, jeder Stil', 'Gutschein für ein Kunstwerk mit zwei Augen, jeder Stil'],
    rules: 'Ein Gutschein gilt 12 Monate ab dem Kauf (der letzte Tag steht in der E-Mail mit dem Code) und kann einmal eingelöst werden, für eine Bestellung in Euro. Kostet die Bestellung weniger als der Gutschein, wird der Rest nicht ausgezahlt und verfällt; kostet sie mehr, wird die Differenz auf der Zahlungsseite bezahlt. Ein Gutschein kann nicht in Geld umgetauscht werden. Wer den Code hat, kann ihn einlösen; bitte bewahren Sie ihn sicher auf.',
    contract: 'Sie bezahlen einen Gutschein im Voraus über unseren Zahlungsdienstleister Stripe. Der Vertrag über den Gutschein kommt zustande, wenn Ihre Zahlung bestätigt ist: Wir zeigen den Code dann auf der Seite, auf die Sie zurückkehren, und senden ihn Ihnen per E-Mail, mit diesen AGB und der Widerrufsbelehrung als Text. Eine mit einem Gutschein bezahlte Bestellung ist ein eigener Vertrag zwischen uns und der Person, die sie aufgibt, nach diesen AGB.',
    withdrawal: `Sie können den Kauf eines Gutscheins innerhalb von 14 Tagen ab dem Kauf ohne Angabe von Gründen widerrufen, solange der Gutschein nicht eingelöst ist: Schreiben Sie an ${MAIL} mit dem Gutscheincode (Sie können das Muster-Widerrufsformular auf unserer Seite [Widerrufsbelehrung](doc:withdrawal) verwenden). Wir erstatten den vollen Preis innerhalb von 14 Tagen über dasselbe Zahlungsmittel und sperren den Code. Für eine mit einem Gutschein bezahlte Bestellung gilt das Widerrufsrecht dieser Bestellung (siehe [Widerrufsrecht](#withdrawal)).`,
    pricesRef: 'Ein Geschenkgutschein kann eine Bestellung ganz oder teilweise bezahlen: siehe [Geschenkgutscheine](#vouchers).',
    hufRef: 'Geschenkgutscheine werden nur in Euro verkauft und eingelöst und können daher keine Bestellung in Forint bezahlen: siehe [Geschenkgutscheine](#vouchers).',
    hufPrice: 'in Euro auf unserer Geschenkseite erhältlich',
    privTitle: 'Geschenkgutscheine',
    priv: [
      'Wenn Sie einen Geschenkgutschein kaufen, geben Sie Ihre E-Mail-Adresse auf der Zahlungsseite von Stripe ein. Wir verwenden sie nur, um Ihnen den Gutscheincode, diese Angaben und unsere AGB zu senden. Unser eigener Datensatz des Gutscheins enthält keine E-Mail-Adresse: seine Art, seinen Wert, die Daten, die letzten vier Zeichen des Codes und die Stripe-Zahlungssitzung, über die wir die Zahlung und Ihre E-Mail-Adresse bei Stripe finden können, zum Beispiel wenn Sie widerrufen. Der Code selbst wird nicht gespeichert: Unser Server leitet ihn mit einem geheimen Schlüssel aus der Zahlung ab. Bei Stripe legen wir für den Code einen einmal nutzbaren Rabatt an, der die Zahlungssitzung und die Art des Gutscheins nennt.',
      'Die Person, die den Gutschein einlöst, bestellt wie jeder andere Kunde (siehe [Wenn Sie bestellen](#orders)). Wir teilen dem Käufer nichts über diese Bestellung mit.',
      'Rechtsgrundlage: der Vertrag mit Ihnen (Art. 6 Abs. 1 lit. b DSGVO); für Buchhaltungsunterlagen unsere rechtlichen Pflichten (Art. 6 Abs. 1 lit. c DSGVO).',
    ],
    privRetention: ['Geschenkgutscheine', 'Der Datensatz eines Gutscheins (ohne E-Mail-Adresse) wird wie ein Bestelldatensatz aufbewahrt; die E-Mail mit dem Code wie bei E-Mails beschrieben.'],
    wdTitle: 'Geschenkgutscheine',
    wd: `**Geschenkgutscheine** (in Euro verkauft) können innerhalb von 14 Tagen ab dem Kauf widerrufen werden, solange der Gutschein nicht eingelöst ist. Die Frist beginnt mit dem Tag, an dem Sie den Gutschein kaufen. Bitte schreiben Sie uns (${MAIL}) mit dem Gutscheincode; Sie können das Muster-Widerrufsformular unten verwenden. Wir erstatten den vollen Preis und sperren den Code. Die Online-Widerrufsfunktion ist für Bestellungen von Kunstwerken; für einen Gutschein schreiben Sie uns bitte. Für eine mit einem Gutschein bezahlte Bestellung gilt das oben beschriebene Widerrufsrecht.`,
  },
  lt: {
    title: 'Dovanų kuponai',
    intro: 'Mūsų [dovanų puslapyje](/gift) galite nupirkti dovanų kuponą kitam žmogui: kodą vienam užsakymui snapeyes.com eurais. Kodą turintis žmogus nusifotografuoja savo akį, pasirenka stilių, pamato nemokamą peržiūrą ir kasoje įveda kodą. Kuponai ir jų kainos:',
    rows: ['Kuponas vienos akies kūriniui, bet kuris stilius', 'Kuponas dviejų akių kūriniui, bet kuris stilius'],
    rules: 'Kuponas galioja 12 mėnesių nuo pirkimo (paskutinė diena nurodyta el. laiške su kodu) ir gali būti panaudotas vieną kartą, vienam užsakymui eurais. Jei užsakymas kainuoja mažiau nei kuponas, likutis negrąžinamas ir vėliau nepanaudojamas; jei daugiau, skirtumas sumokamas mokėjimo puslapyje. Kupono negalima iškeisti į pinigus. Kodu gali pasinaudoti bet kas, kas jį turi, todėl jį saugokite.',
    contract: 'Už kuponą mokate iš anksto per mūsų mokėjimo paslaugų teikėją Stripe. Kupono sutartis sudaroma, kai patvirtinamas Jūsų mokėjimas: tada kodą parodome puslapyje, į kurį grįžtate, ir atsiunčiame el. paštu kartu su šiomis sąlygomis ir informacija apie teisę atsisakyti sutarties. Kuponu apmokėtas užsakymas yra atskira sutartis tarp mūsų ir jį pateikusio žmogaus pagal šias sąlygas.',
    withdrawal: `Kupono pirkimo galite atsisakyti per 14 dienų nuo pirkimo, nenurodydami priežasties, jei kuponas dar nepanaudotas: parašykite ${MAIL} ir nurodykite kupono kodą (galite naudoti pavyzdinę formą puslapyje [Teisė atsisakyti sutarties](doc:withdrawal)). Visą kainą grąžinsime per 14 dienų tuo pačiu mokėjimo būdu, o kodą panaikinsime. Kuponu apmokėtam užsakymui taikoma to užsakymo teisė atsisakyti sutarties (žr. [Teisė atsisakyti sutarties](#withdrawal)).`,
    pricesRef: 'Dovanų kuponu galima apmokėti visą užsakymą arba jo dalį: žr. [Dovanų kuponai](#vouchers).',
    hufRef: 'Dovanų kuponai parduodami ir naudojami tik eurais, todėl jais negalima apmokėti užsakymo forintais: žr. [Dovanų kuponai](#vouchers).',
    hufPrice: 'parduodamas eurais mūsų dovanų puslapyje',
    privTitle: 'Dovanų kuponai',
    priv: [
      'Pirkdami dovanų kuponą, savo el. pašto adresą įvedate Stripe mokėjimo puslapyje. Jį naudojame tik tam, kad atsiųstume Jums kupono kodą, šią informaciją ir mūsų sąlygas. Mūsų pačių kupono įraše el. pašto adreso nėra: tik kupono rūšis, vertė, datos, paskutiniai keturi kodo simboliai ir Stripe mokėjimo sesija, per kurią Stripe sistemoje galime rasti mokėjimą ir Jūsų el. pašto adresą, pavyzdžiui, jei atsisakote sutarties. Pats kodas nesaugomas: mūsų serveris jį išveda iš mokėjimo slaptu raktu. Stripe sistemoje kodui sukuriame vienkartinę nuolaidą, kurioje nurodyta mokėjimo sesija ir kupono rūšis.',
      'Kuponą panaudojęs žmogus užsako kaip ir bet kuris kitas klientas (žr. [Kai užsisakote](#orders)). Pirkėjui apie tą užsakymą nieko nepranešame.',
      'Teisinis pagrindas: sutartis su Jumis (BDAR 6 straipsnio 1 dalies b punktas); apskaitos dokumentams: mūsų teisinės prievolės (BDAR 6 straipsnio 1 dalies c punktas).',
    ],
    privRetention: ['Dovanų kuponai', 'Kupono įrašas (be el. pašto adreso) saugomas kaip užsakymo įrašas; el. laiškas su kodu, kaip aprašyta el. laiškams.'],
    wdTitle: 'Dovanų kuponai',
    wd: `**Dovanų kuponų** (parduodamų eurais) pirkimo galima atsisakyti per 14 dienų nuo pirkimo, jei kuponas dar nepanaudotas. Terminas pradedamas skaičiuoti nuo kupono pirkimo dienos. Parašykite mums (${MAIL}) ir nurodykite kupono kodą; galite naudoti toliau pateiktą pavyzdinę formą. Visą kainą grąžinsime, o kodą panaikinsime. Internetinė sutarties atsisakymo funkcija skirta kūrinių užsakymams; dėl kupono parašykite mums. Kuponu apmokėtam užsakymui taikoma pirmiau aprašyta teisė atsisakyti sutarties.`,
  },
  hu: {
    title: 'Ajándékutalványok',
    intro: 'Az [ajándékoldalunkon](/gift) ajándékutalványt vásárolhat valaki másnak: egy kódot egy euróban fizetett rendeléshez a snapeyes.com oldalon. Akinél a kód van, lefotózza a saját szemét, stílust választ, megnézi az ingyenes előnézetet, és a pénztárnál beírja a kódot. Az utalványok és áraik:',
    rows: ['Utalvány egy szemről készült alkotásra, bármilyen stílusban', 'Utalvány két szemről készült alkotásra, bármilyen stílusban'],
    rules: 'Az utalvány a vásárlástól számított 12 hónapig érvényes (az utolsó nap a kódot tartalmazó e-mailben szerepel), és egyszer, egy euróban fizetett rendeléshez használható fel. Ha a rendelés kevesebbe kerül, mint az utalvány, a maradékot nem fizetjük ki, és később sem használható fel; ha többe kerül, a különbözetet a fizetési oldalon kell kifizetni. Az utalvány nem váltható pénzre. Bárki felhasználhatja, akinél a kód van, ezért kérjük, őrizze meg biztonságban.',
    contract: 'Az utalványt előre fizeti ki a fizetési szolgáltatónkon, a Stripe-on keresztül. Az utalványra vonatkozó szerződés a fizetés visszaigazolásával jön létre: ekkor a kódot megmutatjuk azon az oldalon, ahová visszatér, és e-mailben is elküldjük, ezekkel a feltételekkel és az elállási tájékoztatóval együtt, szövegként. Az utalvánnyal fizetett rendelés külön szerződés köztünk és a rendelést leadó személy között, ezen feltételek szerint.',
    withdrawal: `Az utalvány vásárlásától a vásárlástól számított 14 napon belül indokolás nélkül elállhat, amíg az utalványt nem használták fel: írjon a(z) ${MAIL} címre az utalvány kódjával (használhatja az [Elállási tájékoztató](doc:withdrawal) oldalon található elállási nyilatkozatmintát). A teljes árat 14 napon belül, ugyanazzal a fizetési móddal visszatérítjük, a kódot pedig érvénytelenítjük. Az utalvánnyal fizetett rendelésre az adott rendelés elállási joga vonatkozik (lásd [Elállási jog](#withdrawal)).`,
    pricesRef: 'Egy ajándékutalvány a rendelés egészét vagy egy részét kifizetheti: lásd [Ajándékutalványok](#vouchers).',
    hufRef: 'Az ajándékutalványokat csak euróban árusítjuk és váltjuk be, ezért forintban fizetett rendeléshez nem használhatók: lásd [Ajándékutalványok](#vouchers).',
    hufPrice: 'euróban kapható az ajándékoldalunkon',
    privTitle: 'Ajándékutalványok',
    priv: [
      'Ajándékutalvány vásárlásakor az e-mail-címét a Stripe fizetési oldalán adja meg. Csak arra használjuk, hogy elküldjük Önnek az utalvány kódját, ezeket az adatokat és a feltételeinket. Az utalványról vezetett saját nyilvántartásunk nem tartalmaz e-mail-címet: csak az utalvány fajtáját, értékét, a dátumokat, a kód utolsó négy karakterét és a Stripe fizetési munkamenetet, amelyen keresztül a Stripe-nál megtaláljuk a fizetést és az e-mail-címét, például ha eláll. Magát a kódot nem tároljuk: a szerverünk titkos kulccsal állítja elő a fizetésből. A Stripe-nál a kódhoz egyszer használható kedvezményt hozunk létre, amely megnevezi a fizetési munkamenetet és az utalvány fajtáját.',
      'Aki az utalványt felhasználja, ugyanúgy rendel, mint bármely más vásárló (lásd [Rendelés esetén](#orders)). A vásárlónak semmit sem közlünk erről a rendelésről.',
      'Jogalap: az Önnel kötött szerződés (GDPR 6. cikk (1) bekezdés b) pont); a számviteli nyilvántartásokhoz jogi kötelezettségeink (GDPR 6. cikk (1) bekezdés c) pont).',
    ],
    privRetention: ['Ajándékutalványok', 'Az utalvány nyilvántartását (e-mail-cím nélkül) a rendelési nyilvántartással azonos módon őrizzük; a kódot tartalmazó e-mailt az e-maileknél leírtak szerint.'],
    wdTitle: 'Ajándékutalványok',
    wd: `Az **ajándékutalványok** (euróban értékesítve) vásárlásától a vásárlástól számított 14 napon belül el lehet állni, amíg az utalványt nem használták fel. A határidő az utalvány megvásárlásának napján kezdődik. Kérjük, írjon nekünk (${MAIL}) az utalvány kódjával; használhatja az alábbi nyilatkozatmintát. A teljes árat visszatérítjük, a kódot pedig érvénytelenítjük. Az online elállási funkció az alkotások rendeléseire szolgál; utalvány esetén kérjük, írjon nekünk. Az utalvánnyal fizetett rendelésre a fent leírt elállási jog vonatkozik.`,
  },
  hr: {
    title: 'Poklon-bonovi',
    intro: 'Na našoj [stranici za poklone](/gift) možete kupiti poklon-bon za drugu osobu: kod za jednu narudžbu na snapeyes.com u eurima. Osoba koja ima kod fotografira svoje oko, odabere stil, pogleda besplatni pregled i upiše kod na blagajni. Bonovi i njihove cijene:',
    rows: ['Bon za umjetničku sliku jednog oka, bilo koji stil', 'Bon za umjetničku sliku dvaju očiju, bilo koji stil'],
    rules: 'Bon vrijedi 12 mjeseci od kupnje (posljednji dan naveden je u e-poruci s kodom) i može se iskoristiti jednom, za jednu narudžbu u eurima. Ako narudžba košta manje od bona, ostatak se ne isplaćuje i ne može se kasnije iskoristiti; ako košta više, razlika se plaća na stranici za plaćanje. Bon se ne može zamijeniti za novac. Svatko tko ima kod može ga iskoristiti, zato ga čuvajte.',
    contract: 'Bon plaćate unaprijed putem našeg pružatelja platnih usluga Stripe. Ugovor o bonu sklapa se kada je vaše plaćanje potvrđeno: tada vam kod prikazujemo na stranici na koju se vratite i šaljemo ga e-poštom, zajedno s ovim uvjetima i informacijama o pravu na jednostrani raskid ugovora, kao tekst. Narudžba plaćena bonom poseban je ugovor između nas i osobe koja je predaje, prema ovim uvjetima.',
    withdrawal: `Ugovor o kupnji bona možete jednostrano raskinuti u roku od 14 dana od kupnje, bez navođenja razloga, dok bon nije iskorišten: pišite na ${MAIL} i navedite kod bona (možete upotrijebiti obrazac za jednostrani raskid na našoj stranici [Pravo na jednostrani raskid ugovora](doc:withdrawal)). Cijeli iznos vratit ćemo u roku od 14 dana istim načinom plaćanja, a kod ćemo poništiti. Za narudžbu plaćenu bonom vrijedi pravo na jednostrani raskid te narudžbe (vidi [Pravo na jednostrani raskid ugovora](#withdrawal)).`,
    pricesRef: 'Poklon-bon može platiti cijelu narudžbu ili njezin dio: vidi [Poklon-bonovi](#vouchers).',
    hufRef: 'Poklon-bonovi se prodaju i koriste samo u eurima, pa se njima ne može platiti narudžba u forintama: vidi [Poklon-bonovi](#vouchers).',
    hufPrice: 'prodaje se u eurima na našoj stranici za poklone',
    privTitle: 'Poklon-bonovi',
    priv: [
      'Kada kupujete poklon-bon, svoju adresu e-pošte upisujete na Stripeovoj stranici za plaćanje. Koristimo je samo da vam pošaljemo kod bona, ove podatke i naše uvjete. Naš vlastiti zapis o bonu ne sadrži adresu e-pošte: samo vrstu bona, vrijednost, datume, posljednja četiri znaka koda i Stripeovu sesiju plaćanja, preko koje u Stripeu možemo pronaći plaćanje i vašu adresu e-pošte, na primjer ako jednostrano raskinete ugovor. Sam kod ne pohranjujemo: naš poslužitelj izvodi ga iz plaćanja tajnim ključem. U Stripeu za kod stvaramo jednokratni popust koji navodi sesiju plaćanja i vrstu bona.',
      'Osoba koja iskoristi bon naručuje kao i svaki drugi kupac (vidi [Kada naručujete](#orders)). Kupcu ne javljamo ništa o toj narudžbi.',
      'Pravna osnova: ugovor s vama (članak 6. stavak 1. točka (b) GDPR-a); za računovodstvene evidencije naše zakonske obveze (članak 6. stavak 1. točka (c) GDPR-a).',
    ],
    privRetention: ['Poklon-bonovi', 'Zapis o bonu (bez adrese e-pošte) čuva se kao zapis o narudžbi; e-poruka s kodom kako je opisano za e-poruke.'],
    wdTitle: 'Poklon-bonovi',
    wd: `Ugovor o kupnji **poklon-bonova** (prodanih u eurima) može se jednostrano raskinuti u roku od 14 dana od kupnje dok bon nije iskorišten. Rok počinje teći od dana kupnje bona. Pišite nam (${MAIL}) i navedite kod bona; možete upotrijebiti obrazac u nastavku. Vratit ćemo cijeli iznos i poništiti kod. Mrežna funkcija za jednostrani raskid namijenjena je narudžbama umjetničkih slika; za bon nam pišite. Za narudžbu plaćenu bonom vrijedi gore opisano pravo na jednostrani raskid ugovora.`,
  },
};

const add = (...more: Block[]) => (s: LegalSection): LegalSection => ({ ...s, blocks: [...s.blocks, ...more] });

/** The terms' section "vouchers" (huf: the Hungarian edition's, without the euro prices). */
function vouchersSection(lang: Lang, huf = false): LegalSection {
  const w = W[lang];
  const price = (cents: number) => (huf ? w.hufPrice : eur(cents, lang));
  return {
    id: 'vouchers',
    title: w.title,
    blocks: [w.intro, { dl: [[w.rows[0], price(PRICE_CENTS.artBackground)], [w.rows[1], price(PRICE_CENTS.coupleDuo)]] }, w.rules, w.contract, w.withdrawal],
  };
}

/** The terms of one language with the gift vouchers: the EU edition, and the Hungarian one (whose price section in forints says that a voucher is euros only). */
export function withVoucherTerms(doc: LegalDoc, lang: Lang): LegalDoc {
  const w = W[lang];
  const prices = doc.sections.find((s) => s.id === 'prices');
  const huf = !!prices && prices.blocks.some((b) => typeof b === 'string' && /\(Ft\)|forint/i.test(b));
  return patchDoc(doc, { replace: { prices: add(huf ? w.hufRef : w.pricesRef) }, after: { prices: [vouchersSection(lang, huf)] } });
}

/** The EU privacy policy of one language with the gift vouchers: the section after "orders" and a row in "retention" (before its last row, the emails). */
export function withVoucherPrivacy(doc: LegalDoc, lang: Lang): LegalDoc {
  const w = W[lang];
  return patchDoc(doc, {
    replace: {
      retention: (s) => {
        let hit = false;
        const blocks = s.blocks.map((b) => {
          if (!hit && typeof b === 'object' && 'dl' in b) {
            hit = true;
            return { dl: [...b.dl.slice(0, -1), w.privRetention, ...b.dl.slice(-1)] };
          }
          return b;
        });
        if (!hit) throw new Error(`gift vouchers in the privacy policy (${lang}): no table in "retention"`);
        return { ...s, blocks };
      },
    },
    after: { orders: [{ id: 'vouchers', title: w.privTitle, blocks: w.priv }] },
  });
}

/** The EU withdrawal page of one language with its section "vouchers" (after "expiry"). */
export function withVoucherWithdrawal(doc: LegalDoc, lang: Lang): LegalDoc {
  const w = W[lang];
  return patchDoc(doc, { after: { expiry: [{ id: 'vouchers', title: w.wdTitle, blocks: [w.wd] }] } });
}
