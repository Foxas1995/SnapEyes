# -*- coding: utf-8 -*-
"""The words of the prints in every language of the site: the name of each kind of print and the name of every country a print ships to.
One table for the server (the Stripe line item, the e-mails: api/_lib/prints.py) and the pages (src/shared/prints.ts imports this file as
text and parses the PRINT_NAMES literal below as JSON: the checkout's country list, the order page, the terms' list of delivery countries).
The build refuses a kind of api/_lib/print_offer.py or a country of api/_lib/print_rates.py without its words in all five languages, and a
dash in any of them (scripts/check_prices.mjs, scripts/check_texts.mjs).

Rules for the literal: plain JSON (double quotes, no trailing commas, no comments inside it), nothing after it in this file.
  kinds      {kind: {en, de, lt, hu, hr}}: the name of the product, without its size (the size is written "30 × 30 cm" next to it)
  countries  {ISO code: {en, de, lt, hu, hr}}: the country names (the EU member states)"""
PRINT_NAMES = {
    "kinds": {
        "acrylic": {"en": "Acrylic glass print", "de": "Acrylglasbild", "lt": "Paveikslas po akriliniu stiklu", "hu": "Akrilüveg kép", "hr": "Slika na akrilnom staklu", "fi": "Akryylilasitaulu", "et": "Pilt akrüülklaasil", "lv": "Izdruka uz akrila stikla"},
        "canvas": {"en": "Canvas in a black floating frame", "de": "Leinwand im schwarzen Schattenfugenrahmen", "lt": "Drobė juodame rėme", "hu": "Vászonkép fekete úsztatott keretben", "hr": "Platno u crnom lebdećem okviru", "fi": "Canvastaulu mustassa leijukehyksessä", "et": "Lõuend mustas ujuvraamis", "lv": "Audekls melnā peldošajā rāmī"},
        "poster": {"en": "Poster", "de": "Poster", "lt": "Plakatas", "hu": "Poszter", "hr": "Poster", "fi": "Juliste", "et": "Plakat", "lv": "Plakāts"}
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
