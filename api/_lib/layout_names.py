# -*- coding: utf-8 -*-
"""The words for the layouts: THE ONE PLACE that says what a layout id is called in English, German, Lithuanian and Hungarian.
A layout is how the irises of an artwork are arranged (one eye, a pair, a triangle of three, a ring of seven, ...); the layout ids a
style takes for each number of eyes are in api/_lib/styles_registry.py (the "layouts" field), and this file names every one of them.
Nothing else keeps a table of layout words: not the e-mails (api/_lib/pay.py, pay_lt.py, pay_hu.py), not the picker (src/try), not
the order page (src/order), not the admin. The server asks api/_lib/catalogue.py layout_name(lang, id), the pages ask
src/shared/layouts.ts layoutName(lang, id), and both read this very file (the pages import it as text with Vite's ?raw and parse the
literal below as JSON, as src/shared/styles.ts does with the registry).

The build refuses to finish (scripts/check_styles.mjs, item 5) when the literal is not plain JSON, when a layout id has no word in one
of the four languages, when a style takes a layout this file does not name, when a word here belongs to no style, when the pages read
another table than this one, or when any other file of api/, src/ or scripts/ holds a table that names layouts again. The text check
(scripts/check_texts.mjs) reads these words too: no en or em dash in any of them, and no English or German word in a Lithuanian or
Hungarian one.

Rules for the literal (JSON inside Python): double quotes only, no trailing commas, no comments inside it, nothing after it in this
file. Unlike the style registry it holds the words in plain UTF-8 (the Lithuanian and Hungarian letters), exactly as pay_lt.py and
pay_hu.py do. Every entry has exactly the four languages en, de, lt and hu, each a short word or two with no spaces at either end.

Which ids are which. The legacy ids (single, duo, fusion, triangle, row, grid, galaxy) are what the six styles of today take and what
every order made so far carries: their words are the ones the e-mails and the order page have always printed and stay for ever, so
that an old order still reads the same. The v3 ids (pair, trio, diag, zigzag, cluster, brick, ring, flower, chain; single is shared)
are the arrangements of the new styles. The words of the v3 ids are drafts of the product work (PRODUCT.md 2.1, the integration
specification 5.4); `pair` has no draft there and is named by the work package that moved the tables here. Nothing in Lithuanian or
Hungarian has been read by a native speaker yet (README): every word of a v3 id is on that review list.
"""
LAYOUT_NAMES = {
    "single": {"en": "Single", "de": "Einzeln", "lt": "Viena akis", "hu": "Egy szem"},
    "pair": {"en": "Pair", "de": "Paar", "lt": "Pora", "hu": "Pár"},
    "trio": {"en": "Triangle", "de": "Dreieck", "lt": "Trikampis", "hu": "Háromszög"},
    "diag": {"en": "Diagonal", "de": "Diagonale", "lt": "Įstrižai", "hu": "Átlós"},
    "zigzag": {"en": "Zigzag", "de": "Zickzack", "lt": "Zigzagas", "hu": "Cikcakk"},
    "cluster": {"en": "Cluster", "de": "Gruppe", "lt": "Grupė", "hu": "Csoport"},
    "ring": {"en": "Ring", "de": "Ring", "lt": "Žiedas", "hu": "Gyűrű"},
    "brick": {"en": "Rows", "de": "Reihen", "lt": "Eilės", "hu": "Sorok"},
    "flower": {"en": "Flower", "de": "Blume", "lt": "Gėlė", "hu": "Virág"},
    "chain": {"en": "Chain", "de": "Kette", "lt": "Grandinė", "hu": "Lánc"},
    "duo": {"en": "Side by side", "de": "Nebeneinander", "lt": "Greta", "hu": "Egymás mellett"},
    "fusion": {"en": "Fusion", "de": "Fusion", "lt": "Susiliejimas", "hu": "Összeolvadás"},
    "triangle": {"en": "Triangle", "de": "Dreieck", "lt": "Trikampis", "hu": "Háromszög"},
    "row": {"en": "In a row", "de": "In einer Reihe", "lt": "Vienoje eilėje", "hu": "Egy sorban"},
    "grid": {"en": "Grid", "de": "Raster", "lt": "Tinklelis", "hu": "Rács"},
    "galaxy": {"en": "Galaxy", "de": "Galaxie", "lt": "Galaktika", "hu": "Galaxis"}
}
