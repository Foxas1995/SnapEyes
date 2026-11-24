# -*- coding: utf-8 -*-
"""The words of the prints in every language of the site: the name of each kind of print and the name of every country a print ships to.
One table for the server (the Stripe line item, the e-mails: api/_lib/prints.py) and the pages (src/shared/prints.ts imports this file as
text and parses the PRINT_NAMES literal below as JSON: the checkout's country list, the order page, the terms' list of delivery countries).
The build refuses a kind of api/_lib/print_offer.py or a country of api/_lib/print_rates.py without its words in all five languages, and a
dash in any of them (scripts/check_prices.mjs, scripts/check_texts.mjs).

Rules for the literal: plain JSON (double quotes, no trailing commas, no comments inside it), nothing after it in this file.
  kinds      {kind: {en, de, lt, hu, hr, fi, et, lv}}: the name of the product, without its size (the size is written "30 × 30 cm" next to it;
             the keyring has none)
  about      {kind: {the eight languages}}: one line that says what the thing is, shown where a print is chosen (src/try/PrintPick.tsx). Facts
             only, as merchOne makes them (2026-11-24): acrylic = a photo print behind 3 mm of acrylic glass with the hanger set; metal = the
             gloss finish with the hanger set; canvas = on its 2 cm wooden stretcher frame with the hanger set, ready to hang, WITHOUT an outer
             frame (the owner: as canvases are sold in Lithuania; no floating frame anywhere); poster = paper, no frame; block = 2.5 cm of
             clear acrylic that STANDS by itself on a shelf or a desk (it is not hung and has no hanger); keyring = rectangular
  times      {language: {made, way, way_other}}: the words of the times of api/_lib/print_times.py (the numbers are there, never here): made
             = the production time of a print ({n} business days), way = its time on the way to a country merchOne publishes one for ({country},
             {a} to {b} working days), way_other = every other country (about a week, no number). The country stands in brackets, in its own
             form, so no language has to bend it. Shown under the print a customer chooses and said in the confirmation e-mails
  countries  {ISO code: {en, de, lt, hu, hr}}: the country names (the EU member states)"""
PRINT_NAMES = {
    "kinds": {
        "acrylic": {"en": "Acrylic glass print", "de": "Acrylglasbild", "lt": "Paveikslas po akriliniu stiklu", "hu": "Akrilüveg kép", "hr": "Slika na akrilnom staklu", "fi": "Akryylilasitaulu", "et": "Pilt akrüülklaasil", "lv": "Izdruka uz akrila stikla"},
        "metal": {"en": "Glossy metal print", "de": "Metalldruck, glänzend", "lt": "Blizgus metalas", "hu": "Fényes fémnyomat", "hr": "Sjajni ispis na metalu", "fi": "Kiiltävä metallitaulu", "et": "Läikiv metallpilt", "lv": "Spīdīga izdruka uz metāla"},
        "canvas": {"en": "Canvas on a wooden stretcher frame", "de": "Leinwand auf Holzkeilrahmen", "lt": "Drobė ant medinio porėmio", "hu": "Vászonkép fa vakrámán", "hr": "Platno na drvenom podokviru", "fi": "Canvastaulu puisella kiilakehyksellä", "et": "Lõuend puidust alusraamil", "lv": "Audekls uz koka apakšrāmja"},
        "poster": {"en": "Poster", "de": "Poster", "lt": "Plakatas", "hu": "Poszter", "hr": "Poster", "fi": "Juliste", "et": "Plakat", "lv": "Plakāts"},
        "block": {"en": "Acrylic block", "de": "Acrylblock", "lt": "Akrilo blokas", "hu": "Akrilblokk", "hr": "Akrilni blok", "fi": "Akryylilohko", "et": "Akrüülplokk", "lv": "Akrila bloks"},
        "keyring": {"en": "Keyring", "de": "Schlüsselanhänger", "lt": "Raktų pakabukas", "hu": "Kulcstartó", "hr": "Privjesak za ključeve", "fi": "Avaimenperä", "et": "Võtmehoidja", "lv": "Atslēgu piekariņš"}
    },
    "about": {
        "acrylic": {"en": "A photo print behind 3 mm of acrylic glass, with a hanger set: ready to hang.", "de": "Ein Fotodruck hinter 3 mm Acrylglas, mit Aufhängeset: fertig zum Aufhängen.", "lt": "Nuotraukos atspaudas po 3 mm akriliniu stiklu, su pakabinimo rinkiniu: paruoštas kabinti.", "hu": "Fotónyomat 3 mm-es akrilüveg mögött, akasztókészlettel: felakasztásra kész.", "hr": "Fotoispis iza akrilnog stakla od 3 mm, s kompletom za vješanje: spreman za vješanje.", "fi": "Valokuvatuloste 3 mm:n akryylilasin takana, ripustussarjan kanssa: valmis ripustettavaksi.", "et": "Fototrükk 3 mm akrüülklaasi taga, riputuskomplektiga: valmis seinale riputamiseks.", "lv": "Fotoizdruka aiz 3 mm akrila stikla, ar piekāršanas komplektu: gatava piekāršanai."},
        "metal": {"en": "A glossy print on a metal plate, with a hanger set: ready to hang.", "de": "Ein glänzender Druck auf einer Metallplatte, mit Aufhängeset: fertig zum Aufhängen.", "lt": "Blizgus atspaudas ant metalo plokštės, su pakabinimo rinkiniu: paruoštas kabinti.", "hu": "Fényes nyomat fémlemezen, akasztókészlettel: felakasztásra kész.", "hr": "Sjajan ispis na metalnoj ploči, s kompletom za vješanje: spreman za vješanje.", "fi": "Kiiltävä tuloste metallilevyllä, ripustussarjan kanssa: valmis ripustettavaksi.", "et": "Läikiv trükk metallplaadil, riputuskomplektiga: valmis seinale riputamiseks.", "lv": "Spīdīga izdruka uz metāla plāksnes, ar piekāršanas komplektu: gatava piekāršanai."},
        "canvas": {"en": "Canvas on a 2 cm wooden stretcher frame, ready to hang, without an outer frame.", "de": "Leinwand auf einem 2 cm starken Holzkeilrahmen, fertig zum Aufhängen, ohne äußeren Rahmen.", "lt": "Drobė ant 2 cm medinio porėmio, paruošta kabinti, be išorinio rėmo.", "hu": "Vászonkép 2 cm-es fa vakrámán, felakasztásra kész, külső keret nélkül.", "hr": "Platno na drvenom podokviru od 2 cm, spremno za vješanje, bez vanjskog okvira.", "fi": "Canvastaulu 2 cm:n puisella kiilakehyksellä, valmis ripustettavaksi, ilman ulkokehystä.", "et": "Lõuend 2 cm puidust alusraamil, valmis seinale riputamiseks, ilma välisraamita.", "lv": "Audekls uz 2 cm koka apakšrāmja, gatavs piekāršanai, bez ārējā rāmja."},
        "poster": {"en": "A print on paper, without a frame.", "de": "Ein Druck auf Papier, ohne Rahmen.", "lt": "Atspaudas ant popieriaus, be rėmo.", "hu": "Nyomat papíron, keret nélkül.", "hr": "Ispis na papiru, bez okvira.", "fi": "Tuloste paperilla, ilman kehystä.", "et": "Trükk paberil, ilma raamita.", "lv": "Izdruka uz papīra, bez rāmja."},
        "block": {"en": "A clear acrylic block, 2.5 cm thick. It stands by itself on a shelf or desk.", "de": "Ein klarer Acrylblock, 2,5 cm dick. Er steht von selbst auf einem Regal oder Schreibtisch.", "lt": "Skaidraus akrilo blokas, 2,5 cm storio. Pats stovi ant lentynos ar stalo.", "hu": "Átlátszó akrilblokk, 2,5 cm vastag. Magától megáll a polcon vagy az asztalon.", "hr": "Prozirni akrilni blok, debeo 2,5 cm. Sam stoji na polici ili stolu.", "fi": "Kirkas akryylilohko, 2,5 cm paksu. Se pysyy pystyssä ilman tukea hyllyllä tai pöydällä.", "et": "Läbipaistev akrüülplokk, 2,5 cm paks. Seisab ise riiulil või laual.", "lv": "Caurspīdīgs akrila bloks, 2,5 cm biezs. Pats stāv uz plaukta vai galda."},
        "keyring": {"en": "A rectangular keyring with your artwork.", "de": "Ein rechteckiger Schlüsselanhänger mit Ihrem Kunstwerk.", "lt": "Stačiakampis raktų pakabukas su Jūsų kūriniu.", "hu": "Téglalap alakú kulcstartó az alkotásoddal.", "hr": "Pravokutni privjesak za ključeve s vašim djelom.", "fi": "Suorakulmainen avaimenperä, jossa on taideteoksesi.", "et": "Ristkülikukujuline võtmehoidja sinu kunstiteosega.", "lv": "Taisnstūra atslēgu piekariņš ar jūsu mākslas darbu."}
    },
    "times": {
        "en": {"made": "Production: about {n} business days.", "way": "Delivery ({country}): then usually {a} to {b} working days.", "way_other": "Delivery ({country}): then usually about a week."},
        "de": {"made": "Produktion: etwa {n} Werktage.", "way": "Zustellung ({country}): danach meist {a} bis {b} Werktage.", "way_other": "Zustellung ({country}): danach meist etwa eine Woche."},
        "lt": {"made": "Gamyba: apie {n} darbo dienas.", "way": "Pristatymas ({country}): po to paprastai nuo {a} iki {b} darbo dienų.", "way_other": "Pristatymas ({country}): po to paprastai apie savaitę."},
        "hu": {"made": "Gyártás: körülbelül {n} munkanap.", "way": "Kézbesítés ({country}): ezután általában {a} és {b} munkanap között.", "way_other": "Kézbesítés ({country}): ezután általában körülbelül egy hét."},
        "hr": {"made": "Izrada: oko {n} radna dana.", "way": "Dostava ({country}): zatim obično {a} do {b} radnih dana.", "way_other": "Dostava ({country}): zatim obično oko tjedan dana."},
        "fi": {"made": "Tuotanto: noin {n} arkipäivää.", "way": "Toimitus ({country}): sen jälkeen yleensä {a}-{b} arkipäivää.", "way_other": "Toimitus ({country}): sen jälkeen yleensä noin viikko."},
        "et": {"made": "Tootmine: umbes {n} tööpäeva.", "way": "Tarne ({country}): seejärel tavaliselt {a} kuni {b} tööpäeva.", "way_other": "Tarne ({country}): seejärel tavaliselt umbes nädal."},
        "lv": {"made": "Ražošana: apmēram {n} darba dienas.", "way": "Piegāde ({country}): pēc tam parasti {a} līdz {b} darba dienas.", "way_other": "Piegāde ({country}): pēc tam parasti apmēram nedēļa."}
    },
    "countries": {
        "AT": {"en": "Austria", "de": "Österreich", "lt": "Austrija", "hu": "Ausztria", "hr": "Austrija", "fi": "Itävalta", "et": "Austria", "lv": "Austrija"},
        "BE": {"en": "Belgium", "de": "Belgien", "lt": "Belgija", "hu": "Belgium", "hr": "Belgija", "fi": "Belgia", "et": "Belgia", "lv": "Beļģija"},
        "BG": {"en": "Bulgaria", "de": "Bulgarien", "lt": "Bulgarija", "hu": "Bulgária", "hr": "Bugarska", "fi": "Bulgaria", "et": "Bulgaaria", "lv": "Bulgārija"},
        "HR": {"en": "Croatia", "de": "Kroatien", "lt": "Kroatija", "hu": "Horvátország", "hr": "Hrvatska", "fi": "Kroatia", "et": "Horvaatia", "lv": "Horvātija"},
        "CY": {"en": "Cyprus", "de": "Zypern", "lt": "Kipras", "hu": "Ciprus", "hr": "Cipar", "fi": "Kypros", "et": "Küpros", "lv": "Kipra"},
        "CZ": {"en": "Czechia", "de": "Tschechien", "lt": "Čekija", "hu": "Csehország", "hr": "Češka", "fi": "Tšekki", "et": "Tšehhi", "lv": "Čehija"},
        "DK": {"en": "Denmark", "de": "Dänemark", "lt": "Danija", "hu": "Dánia", "hr": "Danska", "fi": "Tanska", "et": "Taani", "lv": "Dānija"},
        "EE": {"en": "Estonia", "de": "Estland", "lt": "Estija", "hu": "Észtország", "hr": "Estonija", "fi": "Viro", "et": "Eesti", "lv": "Igaunija"},
        "FI": {"en": "Finland", "de": "Finnland", "lt": "Suomija", "hu": "Finnország", "hr": "Finska", "fi": "Suomi", "et": "Soome", "lv": "Somija"},
        "FR": {"en": "France", "de": "Frankreich", "lt": "Prancūzija", "hu": "Franciaország", "hr": "Francuska", "fi": "Ranska", "et": "Prantsusmaa", "lv": "Francija"},
        "DE": {"en": "Germany", "de": "Deutschland", "lt": "Vokietija", "hu": "Németország", "hr": "Njemačka", "fi": "Saksa", "et": "Saksamaa", "lv": "Vācija"},
        "GR": {"en": "Greece", "de": "Griechenland", "lt": "Graikija", "hu": "Görögország", "hr": "Grčka", "fi": "Kreikka", "et": "Kreeka", "lv": "Grieķija"},
        "HU": {"en": "Hungary", "de": "Ungarn", "lt": "Vengrija", "hu": "Magyarország", "hr": "Mađarska", "fi": "Unkari", "et": "Ungari", "lv": "Ungārija"},
        "IE": {"en": "Ireland", "de": "Irland", "lt": "Airija", "hu": "Írország", "hr": "Irska", "fi": "Irlanti", "et": "Iirimaa", "lv": "Īrija"},
        "IT": {"en": "Italy", "de": "Italien", "lt": "Italija", "hu": "Olaszország", "hr": "Italija", "fi": "Italia", "et": "Itaalia", "lv": "Itālija"},
        "LV": {"en": "Latvia", "de": "Lettland", "lt": "Latvija", "hu": "Lettország", "hr": "Latvija", "fi": "Latvia", "et": "Läti", "lv": "Latvija"},
        "LT": {"en": "Lithuania", "de": "Litauen", "lt": "Lietuva", "hu": "Litvánia", "hr": "Litva", "fi": "Liettua", "et": "Leedu", "lv": "Lietuva"},
        "LU": {"en": "Luxembourg", "de": "Luxemburg", "lt": "Liuksemburgas", "hu": "Luxemburg", "hr": "Luksemburg", "fi": "Luxemburg", "et": "Luksemburg", "lv": "Luksemburga"},
        "MT": {"en": "Malta", "de": "Malta", "lt": "Malta", "hu": "Málta", "hr": "Malta", "fi": "Malta", "et": "Malta", "lv": "Malta"},
        "NL": {"en": "Netherlands", "de": "Niederlande", "lt": "Nyderlandai", "hu": "Hollandia", "hr": "Nizozemska", "fi": "Alankomaat", "et": "Holland", "lv": "Nīderlande"},
        "PL": {"en": "Poland", "de": "Polen", "lt": "Lenkija", "hu": "Lengyelország", "hr": "Poljska", "fi": "Puola", "et": "Poola", "lv": "Polija"},
        "PT": {"en": "Portugal", "de": "Portugal", "lt": "Portugalija", "hu": "Portugália", "hr": "Portugal", "fi": "Portugali", "et": "Portugal", "lv": "Portugāle"},
        "RO": {"en": "Romania", "de": "Rumänien", "lt": "Rumunija", "hu": "Románia", "hr": "Rumunjska", "fi": "Romania", "et": "Rumeenia", "lv": "Rumānija"},
        "SK": {"en": "Slovakia", "de": "Slowakei", "lt": "Slovakija", "hu": "Szlovákia", "hr": "Slovačka", "fi": "Slovakia", "et": "Slovakkia", "lv": "Slovākija"},
        "SI": {"en": "Slovenia", "de": "Slowenien", "lt": "Slovėnija", "hu": "Szlovénia", "hr": "Slovenija", "fi": "Slovenia", "et": "Sloveenia", "lv": "Slovēnija"},
        "ES": {"en": "Spain", "de": "Spanien", "lt": "Ispanija", "hu": "Spanyolország", "hr": "Španjolska", "fi": "Espanja", "et": "Hispaania", "lv": "Spānija"},
        "SE": {"en": "Sweden", "de": "Schweden", "lt": "Švedija", "hu": "Svédország", "hr": "Švedska", "fi": "Ruotsi", "et": "Rootsi", "lv": "Zviedrija"}
    }
}
