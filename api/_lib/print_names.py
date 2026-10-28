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
        "acrylic": {"en": "Acrylic glass print", "de": "Acrylglasbild", "lt": "Paveikslas po akriliniu stiklu", "hu": "Akrilüveg kép", "hr": "Slika na akrilnom staklu"},
        "canvas": {"en": "Canvas in a black floating frame", "de": "Leinwand im schwarzen Schattenfugenrahmen", "lt": "Drobė juodame rėme", "hu": "Vászonkép fekete úsztatott keretben", "hr": "Platno u crnom lebdećem okviru"},
        "poster": {"en": "Poster", "de": "Poster", "lt": "Plakatas", "hu": "Poszter", "hr": "Poster"}
    },
    "countries": {
        "AT": {"en": "Austria", "de": "Österreich", "lt": "Austrija", "hu": "Ausztria", "hr": "Austrija"},
        "BE": {"en": "Belgium", "de": "Belgien", "lt": "Belgija", "hu": "Belgium", "hr": "Belgija"},
        "BG": {"en": "Bulgaria", "de": "Bulgarien", "lt": "Bulgarija", "hu": "Bulgária", "hr": "Bugarska"},
        "HR": {"en": "Croatia", "de": "Kroatien", "lt": "Kroatija", "hu": "Horvátország", "hr": "Hrvatska"},
        "CY": {"en": "Cyprus", "de": "Zypern", "lt": "Kipras", "hu": "Ciprus", "hr": "Cipar"},
        "CZ": {"en": "Czechia", "de": "Tschechien", "lt": "Čekija", "hu": "Csehország", "hr": "Češka"},
        "DK": {"en": "Denmark", "de": "Dänemark", "lt": "Danija", "hu": "Dánia", "hr": "Danska"},
        "EE": {"en": "Estonia", "de": "Estland", "lt": "Estija", "hu": "Észtország", "hr": "Estonija"},
        "FI": {"en": "Finland", "de": "Finnland", "lt": "Suomija", "hu": "Finnország", "hr": "Finska"},
        "FR": {"en": "France", "de": "Frankreich", "lt": "Prancūzija", "hu": "Franciaország", "hr": "Francuska"},
        "DE": {"en": "Germany", "de": "Deutschland", "lt": "Vokietija", "hu": "Németország", "hr": "Njemačka"},
        "GR": {"en": "Greece", "de": "Griechenland", "lt": "Graikija", "hu": "Görögország", "hr": "Grčka"},
        "HU": {"en": "Hungary", "de": "Ungarn", "lt": "Vengrija", "hu": "Magyarország", "hr": "Mađarska"},
        "IE": {"en": "Ireland", "de": "Irland", "lt": "Airija", "hu": "Írország", "hr": "Irska"},
        "IT": {"en": "Italy", "de": "Italien", "lt": "Italija", "hu": "Olaszország", "hr": "Italija"},
        "LV": {"en": "Latvia", "de": "Lettland", "lt": "Latvija", "hu": "Lettország", "hr": "Latvija"},
        "LT": {"en": "Lithuania", "de": "Litauen", "lt": "Lietuva", "hu": "Litvánia", "hr": "Litva"},
        "LU": {"en": "Luxembourg", "de": "Luxemburg", "lt": "Liuksemburgas", "hu": "Luxemburg", "hr": "Luksemburg"},
        "MT": {"en": "Malta", "de": "Malta", "lt": "Malta", "hu": "Málta", "hr": "Malta"},
        "NL": {"en": "Netherlands", "de": "Niederlande", "lt": "Nyderlandai", "hu": "Hollandia", "hr": "Nizozemska"},
        "PL": {"en": "Poland", "de": "Polen", "lt": "Lenkija", "hu": "Lengyelország", "hr": "Poljska"},
        "PT": {"en": "Portugal", "de": "Portugal", "lt": "Portugalija", "hu": "Portugália", "hr": "Portugal"},
        "RO": {"en": "Romania", "de": "Rumänien", "lt": "Rumunija", "hu": "Románia", "hr": "Rumunjska"},
        "SK": {"en": "Slovakia", "de": "Slowakei", "lt": "Slovakija", "hu": "Szlovákia", "hr": "Slovačka"},
        "SI": {"en": "Slovenia", "de": "Slowenien", "lt": "Slovėnija", "hu": "Szlovénia", "hr": "Slovenija"},
        "ES": {"en": "Spain", "de": "Spanien", "lt": "Ispanija", "hu": "Spanyolország", "hr": "Španjolska"},
        "SE": {"en": "Sweden", "de": "Schweden", "lt": "Švedija", "hu": "Svédország", "hr": "Švedska"}
    }
}
