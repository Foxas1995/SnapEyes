# -*- coding: utf-8 -*-
"""The words for the layouts: THE ONE PLACE that says what a layout id is called in English, German, Lithuanian and Hungarian.
A layout is how the irises of an artwork are arranged (one eye, a pair, a triangle of three, a ring of seven, ...); the layout ids a
style takes for each number of eyes are in api/_lib/styles_registry.py (the "layouts" field), and this file names every one of them.
Nothing else keeps a table of layout words: not the e-mails (api/_lib/pay.py, pay_lt.py, pay_hu.py), not the picker (src/try), not
the order page (src/order), not the admin. The server asks api/_lib/catalogue.py layout_name(lang, id), the pages ask
src/shared/layouts.ts layoutName(lang, id), and both read this very file (the pages import it as text with Vite's ?raw and parse the
literal below as JSON, as src/shared/styles.ts does with the registry).

The build refuses to finish (scripts/check_styles.mjs, item 5) when the literal is not plain JSON, when a layout id has no word in one
of the five languages, when a style takes a layout this file does not name, when a word here belongs to no style, when the pages read
another table than this one, or when any other file of api/, src/ or scripts/ holds a table that names layouts again. The text check
(scripts/check_texts.mjs) reads these words too: no en or em dash in any of them, and no English or German word in a Lithuanian or
Hungarian one.

Rules for the literal (JSON inside Python): double quotes only, no trailing commas, no comments inside it, nothing after it in this
file. Unlike the style registry it holds the words in plain UTF-8 (the Lithuanian and Hungarian letters), exactly as pay_lt.py and
pay_hu.py do. Every entry has exactly the five languages en, de, lt, hu and hr, each a short word or two with no spaces at either end.

Which ids are which. The legacy ids (single, duo, fusion, triangle, row, grid, galaxy) are what the six styles of today take and what
every order made so far carries: their words are the ones the e-mails and the order page have always printed and stay for ever, so
that an old order still reads the same. The v3 ids (pair, trio, diag, zigzag, cluster, brick, ring, flower, chain, orbit; single is shared)
are the arrangements of the new styles. The words of the v3 ids are drafts of the product work (PRODUCT.md 2.1, the integration
specification 5.4); `pair` has no draft there and is named by the work package that moved the tables here; `orbit` (Family Orbit: one eye in the
middle, the others round it) is named by the work of 2026-10-20 that brought the ensemble family. Nothing in Lithuanian or
Hungarian has been read by a native speaker yet (README): every word of a v3 id is on that review list.
"""
LAYOUT_NAMES = {
    "single": {"en": "Single", "de": "Einzeln", "lt": "Viena akis", "hu": "Egy szem", "hr": "Jedno oko", "fi": "Yksi silmä", "et": "Üks silm", "lv": "Viena acs"},
    "pair": {"en": "Pair", "de": "Paar", "lt": "Pora", "hu": "Pár", "hr": "Par", "fi": "Pari", "et": "Paar", "lv": "Pāris"},
    "trio": {"en": "Triangle", "de": "Dreieck", "lt": "Trikampis", "hu": "Háromszög", "hr": "Trokut", "fi": "Kolmio", "et": "Kolmnurk", "lv": "Trīsstūris"},
    "diag": {"en": "Diagonal", "de": "Diagonale", "lt": "Įstrižai", "hu": "Átlós", "hr": "Dijagonalno", "fi": "Vinottain", "et": "Diagonaalis", "lv": "Pa diagonāli"},
    "zigzag": {"en": "Zigzag", "de": "Zickzack", "lt": "Zigzagas", "hu": "Cikcakk", "hr": "Cik-cak", "fi": "Siksak", "et": "Siksak", "lv": "Zigzags"},
    "cluster": {"en": "Cluster", "de": "Gruppe", "lt": "Grupė", "hu": "Csoport", "hr": "Skupina", "fi": "Ryhmä", "et": "Kobar", "lv": "Grupa"},
    "ring": {"en": "Ring", "de": "Ring", "lt": "Žiedas", "hu": "Gyűrű", "hr": "Prsten", "fi": "Rengas", "et": "Rõngas", "lv": "Gredzens"},
    "brick": {"en": "Rows", "de": "Reihen", "lt": "Eilės", "hu": "Sorok", "hr": "Redovi", "fi": "Rivit", "et": "Read", "lv": "Rindas"},
    "flower": {"en": "Flower", "de": "Blume", "lt": "Gėlė", "hu": "Virág", "hr": "Cvijet", "fi": "Kukka", "et": "Lill", "lv": "Zieds"},
    "chain": {"en": "Chain", "de": "Kette", "lt": "Grandinė", "hu": "Lánc", "hr": "Lanac", "fi": "Ketju", "et": "Kett", "lv": "Ķēde"},
    "orbit": {"en": "Orbit", "de": "Umlaufbahn", "lt": "Orbita", "hu": "Pálya", "hr": "Orbita", "fi": "Kiertorata", "et": "Orbiit", "lv": "Orbīta"},
    "duo": {"en": "Side by side", "de": "Nebeneinander", "lt": "Greta", "hu": "Egymás mellett", "hr": "Jedno uz drugo", "fi": "Vierekkäin", "et": "Kõrvuti", "lv": "Blakus"},
    "fusion": {"en": "Fusion", "de": "Fusion", "lt": "Susiliejimas", "hu": "Összeolvadás", "hr": "Stapanje", "fi": "Fuusio", "et": "Sulandus", "lv": "Saplūšana"},
    "triangle": {"en": "Triangle", "de": "Dreieck", "lt": "Trikampis", "hu": "Háromszög", "hr": "Trokut", "fi": "Kolmio", "et": "Kolmnurk", "lv": "Trīsstūris"},
    "row": {"en": "In a row", "de": "In einer Reihe", "lt": "Vienoje eilėje", "hu": "Egy sorban", "hr": "U nizu", "fi": "Rivissä", "et": "Reas", "lv": "Vienā rindā"},
    "grid": {"en": "Grid", "de": "Raster", "lt": "Tinklelis", "hu": "Rács", "hr": "Mreža", "fi": "Ruudukko", "et": "Ruudustik", "lv": "Režģis"},
    "galaxy": {"en": "Galaxy", "de": "Galaxie", "lt": "Galaktika", "hu": "Galaxis", "hr": "Galaksija", "fi": "Galaksi", "et": "Galaktika", "lv": "Galaktika"}
}
