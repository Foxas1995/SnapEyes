// The words of the gift voucher page (/gift, ./GiftApp.tsx; api/_lib/voucher.py) in the five languages of the site. Plain words, short sentences: the
// page is read on a phone by someone buying a present. The Hungarian page speaks to the visitor with "te", as /try does.
import type { Lang } from '../shared/lang';

export type GiftKind = 'one' | 'two';

export interface GiftCopy {
  meta: { title: string; description: string };
  switchLabel: string;
  tag: string;
  title: string;
  lead: string;
  choose: string;
  kinds: Record<GiftKind, { name: string; note: string; alt: string }>;
  stepsTitle: string;
  steps: [string, string, string];
  rules: string;
  buy: (price: string) => string;
  next: string;
  accept: [string, string, string];
  euroOnly: string;
  closed: string;
  cancelled: string;
  waiting: string;
  slow: string;
  expired: string;
  unknown: string;
  errors: { network: string; busy: string; failed: string };
  ready: {
    title: string;
    rows: { code: string; value: string; for: string; until: string };
    mailed: string;
    copy: string;
    copied: string;
    print: string;
    again: string;
  };
  card: { heading: string; line: string; how: string; until: (day: string) => string };
  contact: string;
}

const en: GiftCopy = {
  meta: {
    title: 'Gift voucher | SnapEyes',
    description: 'Give someone an artwork of their own iris. Buy a SnapEyes gift voucher now; they photograph their eye with their phone later.',
  },
  switchLabel: 'Language',
  tag: 'Gift voucher',
  title: 'Give an artwork of their own eye',
  lead: 'You buy the voucher now. The person you give it to photographs their eye with their phone later, chooses a style and gets their artwork.',
  choose: 'Choose the voucher',
  kinds: {
    one: { name: 'One eye', note: 'An artwork of one eye, any style', alt: 'An artwork of one eye' },
    two: { name: 'Two eyes', note: 'An artwork of two eyes, for a couple or two people', alt: 'An artwork of two eyes' },
  },
  stepsTitle: 'How it works',
  steps: [
    'You pay and get the code by email.',
    'You give the code: print the card or send it.',
    'They photograph their eye on snapeyes.com and enter the code at checkout.',
  ],
  rules: 'Valid for 12 months, for one order. If the artwork costs less, the rest is not paid out. You can withdraw from an unused voucher within 14 days.',
  buy: (price) => `Buy the voucher · ${price}`,
  next: "Next is Stripe's secure payment page. There you enter your email; we send the code to it.",
  accept: ['By buying you accept our ', 'terms of sale', '.'],
  euroOnly: 'Gift vouchers are sold and used in euros.',
  closed: 'Gift vouchers will be on sale soon.',
  cancelled: 'Payment cancelled. Nothing was charged.',
  waiting: 'Confirming your payment',
  slow: 'Your payment is still being confirmed. The code will come by email, or reload this page in a minute.',
  expired: 'This payment page has expired. Nothing was charged.',
  unknown: 'We could not find this voucher payment. If you were charged, please write to info@snapeyes.com.',
  errors: {
    network: 'We could not reach SnapEyes. Please check your internet connection and try again.',
    busy: 'The payment service did not answer. Please try again in a moment.',
    failed: 'We could not open the payment page. Please try again, or write to info@snapeyes.com.',
  },
  ready: {
    title: 'Your gift voucher',
    rows: { code: 'Code', value: 'Value', for: 'For', until: 'Valid until' },
    mailed: 'We also sent the code to your email.',
    copy: 'Copy the code',
    copied: 'Copied',
    print: 'Print the card',
    again: 'Buy another voucher',
  },
  card: {
    heading: 'Gift voucher',
    line: 'An artwork of your own eye',
    how: 'Open snapeyes.com on your phone, photograph your eye, choose a style and enter this code at checkout.',
    until: (day) => `Valid until ${day}`,
  },
  contact: 'Questions? Write to',
};

const de: GiftCopy = {
  meta: {
    title: 'Geschenkgutschein | SnapEyes',
    description: 'Schenken Sie ein Kunstwerk aus der eigenen Iris. Kaufen Sie jetzt einen SnapEyes-Geschenkgutschein; das Auge wird später mit dem Smartphone fotografiert.',
  },
  switchLabel: 'Sprache',
  tag: 'Geschenkgutschein',
  title: 'Schenken Sie ein Kunstwerk aus dem eigenen Auge',
  lead: 'Sie kaufen den Gutschein jetzt. Die beschenkte Person fotografiert später ihr Auge mit dem Smartphone, wählt einen Stil und erhält ihr Kunstwerk.',
  choose: 'Wählen Sie den Gutschein',
  kinds: {
    one: { name: 'Ein Auge', note: 'Ein Kunstwerk mit einem Auge, jeder Stil', alt: 'Ein Kunstwerk mit einem Auge' },
    two: { name: 'Zwei Augen', note: 'Ein Kunstwerk mit zwei Augen, für ein Paar oder zwei Personen', alt: 'Ein Kunstwerk mit zwei Augen' },
  },
  stepsTitle: 'So funktioniert es',
  steps: [
    'Sie bezahlen und erhalten den Code per E-Mail.',
    'Sie verschenken den Code: Drucken Sie die Karte aus oder senden Sie ihn weiter.',
    'Die beschenkte Person fotografiert ihr Auge auf snapeyes.com und gibt den Code an der Kasse ein.',
  ],
  rules: 'Gültig 12 Monate, für eine Bestellung. Kostet das Kunstwerk weniger, wird der Rest nicht ausgezahlt. Einen unbenutzten Gutschein können Sie innerhalb von 14 Tagen widerrufen.',
  buy: (price) => `Gutschein kaufen · ${price}`,
  next: 'Als Nächstes öffnet sich die sichere Zahlungsseite von Stripe. Dort geben Sie Ihre E-Mail-Adresse ein; dorthin senden wir den Code.',
  accept: ['Mit dem Kauf akzeptieren Sie unsere ', 'AGB', '.'],
  euroOnly: 'Geschenkgutscheine werden in Euro verkauft und eingelöst.',
  closed: 'Geschenkgutscheine gibt es bald.',
  cancelled: 'Zahlung abgebrochen. Es wurde nichts berechnet.',
  waiting: 'Ihre Zahlung wird bestätigt',
  slow: 'Ihre Zahlung wird noch bestätigt. Der Code kommt per E-Mail, oder laden Sie diese Seite in einer Minute neu.',
  expired: 'Diese Zahlungsseite ist abgelaufen. Es wurde nichts berechnet.',
  unknown: 'Wir konnten diese Gutscheinzahlung nicht finden. Wurde Ihnen etwas berechnet, schreiben Sie bitte an info@snapeyes.com.',
  errors: {
    network: 'Wir konnten SnapEyes nicht erreichen. Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es noch einmal.',
    busy: 'Der Zahlungsdienst hat nicht geantwortet. Bitte versuchen Sie es gleich noch einmal.',
    failed: 'Wir konnten die Zahlungsseite nicht öffnen. Bitte versuchen Sie es noch einmal oder schreiben Sie an info@snapeyes.com.',
  },
  ready: {
    title: 'Ihr Geschenkgutschein',
    rows: { code: 'Code', value: 'Wert', for: 'Für', until: 'Gültig bis' },
    mailed: 'Den Code haben wir Ihnen auch per E-Mail gesendet.',
    copy: 'Code kopieren',
    copied: 'Kopiert',
    print: 'Karte drucken',
    again: 'Noch einen Gutschein kaufen',
  },
  card: {
    heading: 'Geschenkgutschein',
    line: 'Ein Kunstwerk aus Ihrem eigenen Auge',
    how: 'Öffnen Sie snapeyes.com auf dem Smartphone, fotografieren Sie Ihr Auge, wählen Sie einen Stil und geben Sie diesen Code an der Kasse ein.',
    until: (day) => `Gültig bis ${day}`,
  },
  contact: 'Fragen? Schreiben Sie an',
};

const lt: GiftCopy = {
  meta: {
    title: 'Dovanų kuponas | SnapEyes',
    description: 'Padovanokite kūrinį iš žmogaus akies rainelės. Nupirkite SnapEyes dovanų kuponą dabar, o apdovanotas žmogus akį vėliau nusifotografuos telefonu pats.',
  },
  switchLabel: 'Kalba',
  tag: 'Dovanų kuponas',
  title: 'Padovanokite kūrinį iš artimo žmogaus akies',
  lead: 'Kuponą perkate dabar. Apdovanotas žmogus vėliau pats nusifotografuoja akį telefonu, pasirenka stilių ir gauna savo kūrinį.',
  choose: 'Pasirinkite kuponą',
  kinds: {
    one: { name: 'Viena akis', note: 'Vienos akies kūrinys, bet kuris stilius', alt: 'Vienos akies kūrinys' },
    two: { name: 'Dvi akys', note: 'Dviejų akių kūrinys, porai arba dviem žmonėms', alt: 'Dviejų akių kūrinys' },
  },
  stepsTitle: 'Kaip tai veikia',
  steps: [
    'Sumokate ir gaunate kodą el. paštu.',
    'Padovanojate kodą: atsispausdinkite kortelę arba persiųskite.',
    'Apdovanotas žmogus nusifotografuoja akį snapeyes.com ir kasoje įveda kodą.',
  ],
  rules: 'Galioja 12 mėnesių, vienam užsakymui. Jei kūrinys kainuoja mažiau, likutis negrąžinamas. Nepanaudoto kupono galite atsisakyti per 14 dienų.',
  buy: (price) => `Pirkti kuponą · ${price}`,
  next: 'Toliau atsidarys saugus Stripe mokėjimo puslapis. Ten įvesite el. paštą; juo atsiųsime kodą.',
  accept: ['Pirkdami sutinkate su mūsų ', 'pardavimo sąlygomis', '.'],
  euroOnly: 'Dovanų kuponai parduodami ir naudojami eurais.',
  closed: 'Dovanų kuponus pardavinėsime netrukus.',
  cancelled: 'Mokėjimas atšauktas. Nieko nenuskaičiavome.',
  waiting: 'Tvirtiname Jūsų mokėjimą',
  slow: 'Jūsų mokėjimas dar tvirtinamas. Kodą atsiųsime el. paštu, arba po minutės perkraukite šį puslapį.',
  expired: 'Šio mokėjimo puslapio galiojimas baigėsi. Nieko nenuskaičiavome.',
  unknown: 'Šio kupono mokėjimo neradome. Jei pinigai buvo nuskaičiuoti, parašykite info@snapeyes.com.',
  errors: {
    network: 'Nepavyko susisiekti su SnapEyes. Patikrinkite interneto ryšį ir bandykite dar kartą.',
    busy: 'Mokėjimų paslauga neatsakė. Po akimirkos bandykite dar kartą.',
    failed: 'Nepavyko atidaryti mokėjimo puslapio. Bandykite dar kartą arba parašykite info@snapeyes.com.',
  },
  ready: {
    title: 'Jūsų dovanų kuponas',
    rows: { code: 'Kodas', value: 'Vertė', for: 'Kam', until: 'Galioja iki' },
    mailed: 'Kodą atsiuntėme ir el. paštu.',
    copy: 'Kopijuoti kodą',
    copied: 'Nukopijuota',
    print: 'Spausdinti kortelę',
    again: 'Pirkti dar vieną kuponą',
  },
  card: {
    heading: 'Dovanų kuponas',
    line: 'Kūrinys iš Jūsų akies',
    how: 'Telefone atsidarykite snapeyes.com, nusifotografuokite akį, pasirinkite stilių ir kasoje įveskite šį kodą.',
    until: (day) => `Galioja iki ${day}`,
  },
  contact: 'Klausimai? Rašykite',
};

const hu: GiftCopy = {
  meta: {
    title: 'Ajándékutalvány | SnapEyes',
    description: 'Ajándékozz alkotást a saját íriszéből. Vásárolj most SnapEyes ajándékutalványt; a szemét később a telefonjával fotózza le.',
  },
  switchLabel: 'Nyelv',
  tag: 'Ajándékutalvány',
  title: 'Ajándékozz alkotást a saját szeméből',
  lead: 'Az utalványt most veszed meg. A megajándékozott később lefotózza a szemét a telefonjával, stílust választ, és megkapja az alkotását.',
  choose: 'Válaszd ki az utalványt',
  kinds: {
    one: { name: 'Egy szem', note: 'Alkotás egy szemről, bármilyen stílusban', alt: 'Alkotás egy szemről' },
    two: { name: 'Két szem', note: 'Alkotás két szemről, párnak vagy két embernek', alt: 'Alkotás két szemről' },
  },
  stepsTitle: 'Így működik',
  steps: [
    'Fizetsz, és e-mailben megkapod a kódot.',
    'Odaadod a kódot: nyomtasd ki a kártyát, vagy küldd el.',
    'A megajándékozott a snapeyes.com oldalon lefotózza a szemét, és a pénztárnál beírja a kódot.',
  ],
  rules: '12 hónapig érvényes, egy rendeléshez. Ha az alkotás kevesebbe kerül, a maradékot nem fizetjük ki. A fel nem használt utalványtól 14 napon belül elállhatsz.',
  buy: (price) => `Utalvány megvásárlása · ${price}`,
  next: 'Ezután megnyílik a Stripe biztonságos fizetési oldala. Ott megadod az e-mail-címedet; oda küldjük a kódot.',
  accept: ['A vásárlással elfogadod az ', 'általános szerződési feltételeinket', '.'],
  euroOnly: 'Az ajándékutalványokat euróban árusítjuk és euróban lehet beváltani.',
  closed: 'Az ajándékutalványok hamarosan megvásárolhatók.',
  cancelled: 'A fizetés megszakadt. Nem vontunk le semmit.',
  waiting: 'A fizetésed visszaigazolása',
  slow: 'A fizetésed visszaigazolása még folyamatban van. A kódot e-mailben küldjük, vagy egy perc múlva töltsd újra ezt az oldalt.',
  expired: 'Ez a fizetési oldal lejárt. Nem vontunk le semmit.',
  unknown: 'Nem találjuk ezt az utalványfizetést. Ha levontak tőled pénzt, írj az info@snapeyes.com címre.',
  errors: {
    network: 'Nem értük el a SnapEyes-t. Ellenőrizd az internetkapcsolatot, és próbáld újra.',
    busy: 'A fizetési szolgáltatás nem válaszolt. Próbáld újra egy kicsit később.',
    failed: 'Nem sikerült megnyitni a fizetési oldalt. Próbáld újra, vagy írj az info@snapeyes.com címre.',
  },
  ready: {
    title: 'Az ajándékutalványod',
    rows: { code: 'Kód', value: 'Érték', for: 'Mire', until: 'Érvényes' },
    mailed: 'A kódot e-mailben is elküldtük.',
    copy: 'Kód másolása',
    copied: 'Másolva',
    print: 'Kártya nyomtatása',
    again: 'Még egy utalvány vásárlása',
  },
  card: {
    heading: 'Ajándékutalvány',
    line: 'Alkotás a saját szemedből',
    how: 'Nyisd meg a snapeyes.com oldalt a telefonodon, fotózd le a szemed, válassz stílust, és a pénztárnál írd be ezt a kódot.',
    until: (day) => `Érvényes: ${day}`,
  },
  contact: 'Kérdésed van? Írj ide:',
};

const hr: GiftCopy = {
  meta: {
    title: 'Poklon-bon | SnapEyes',
    description: 'Darujte umjetničku sliku vlastite šarenice. Kupite SnapEyes poklon-bon sada; oko se kasnije fotografira mobitelom.',
  },
  switchLabel: 'Jezik',
  tag: 'Poklon-bon',
  title: 'Darujte umjetničku sliku vlastitog oka',
  lead: 'Bon kupujete sada. Osoba kojoj ga darujete kasnije fotografira svoje oko mobitelom, odabere stil i dobije svoju sliku.',
  choose: 'Odaberite bon',
  kinds: {
    one: { name: 'Jedno oko', note: 'Umjetnička slika jednog oka, bilo koji stil', alt: 'Umjetnička slika jednog oka' },
    two: { name: 'Dva oka', note: 'Umjetnička slika dvaju očiju, za par ili dvije osobe', alt: 'Umjetnička slika dvaju očiju' },
  },
  stepsTitle: 'Kako funkcionira',
  steps: [
    'Platite i dobijete kod e-poštom.',
    'Darujete kod: ispišite karticu ili ga proslijedite.',
    'Osoba fotografira svoje oko na snapeyes.com i upiše kod na blagajni.',
  ],
  rules: 'Vrijedi 12 mjeseci, za jednu narudžbu. Ako slika košta manje, ostatak se ne isplaćuje. Ugovor o neiskorištenom bonu možete jednostrano raskinuti u roku od 14 dana.',
  buy: (price) => `Kupi bon · ${price}`,
  next: 'Zatim se otvara Stripeova sigurna stranica za plaćanje. Ondje upisujete adresu e-pošte; na nju šaljemo kod.',
  accept: ['Kupnjom prihvaćate naše ', 'uvjete prodaje', '.'],
  euroOnly: 'Poklon-bonovi se prodaju i koriste u eurima.',
  closed: 'Poklon-bonovi uskoro će biti u prodaji.',
  cancelled: 'Plaćanje je otkazano. Ništa nije naplaćeno.',
  waiting: 'Potvrđujemo vaše plaćanje',
  slow: 'Vaše se plaćanje još potvrđuje. Kod će stići e-poštom, ili za minutu ponovno učitajte ovu stranicu.',
  expired: 'Ova je stranica za plaćanje istekla. Ništa nije naplaćeno.',
  unknown: 'Ne možemo pronaći ovo plaćanje bona. Ako vam je naplaćeno, pišite na info@snapeyes.com.',
  errors: {
    network: 'Ne možemo dosegnuti SnapEyes. Provjerite internetsku vezu i pokušajte ponovno.',
    busy: 'Usluga plaćanja nije odgovorila. Pokušajte ponovno za trenutak.',
    failed: 'Nismo mogli otvoriti stranicu za plaćanje. Pokušajte ponovno ili pišite na info@snapeyes.com.',
  },
  ready: {
    title: 'Vaš poklon-bon',
    rows: { code: 'Kod', value: 'Vrijednost', for: 'Za', until: 'Vrijedi do' },
    mailed: 'Kod smo vam poslali i e-poštom.',
    copy: 'Kopiraj kod',
    copied: 'Kopirano',
    print: 'Ispiši karticu',
    again: 'Kupi još jedan bon',
  },
  card: {
    heading: 'Poklon-bon',
    line: 'Umjetnička slika vašeg oka',
    how: 'Otvorite snapeyes.com na mobitelu, fotografirajte svoje oko, odaberite stil i upišite ovaj kod na blagajni.',
    until: (day) => `Vrijedi do ${day}`,
  },
  contact: 'Pitanja? Pišite na',
};

export const GIFT_COPY: Record<Lang, GiftCopy> = { en, de, lt, hu, hr };
