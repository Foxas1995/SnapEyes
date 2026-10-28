"""Croatian ("hr") strings of api/_lib/iris.py: the preview watermark and the engine's error sentences in run() (the twin
of iris_hu.py).

WATERMARK_TEXT_HR  WATERMARK_TEXT["hr"] = (tile, badge). "PREGLED" is the site's word for the preview, "VODENI ŽIG" for
                   the watermark; the badge is a polite call to order the full size ("NARUČITE PUNU VELIČINU"), like the
                   English "UNLOCK FULL SIZE". Measured with the engine's own font and sizing (PlusJakartaSans.ttf Bold at
                   0.016 u, the pill the text plus 0.044 u):
                     badge pill 491 px on the 1024 px square (German 592, English 411); every canvas scales the same
                     way, so it stays about 17 % narrower than the German badge everywhere (about 324 of the 469 px on
                     the 473 px wallpaper, German 391);
                     the tile is the site's address alone (iris.py WATERMARK_TILE), the same in every language.
                   Plus Jakarta Sans has every Croatian letter (Č, Ć, Ž, Š, Đ and the small ones, checked with
                   fontTools), so nothing falls back to a box. While a deployment takes no orders it still says
                   "naručite", as the English and German badges do. A longer measured alternative, closest to the German:
                   "PREGLED S VODENIM ŽIGOM  ·  NARUČITE DATOTEKU U PUNOJ VELIČINI" (599 px pill on the square: wider
                   than the German one, so not used).
ERRORS_HR          the sentences run() sends for its refusals (iris.py RUN_ERRORS["hr"]).
page_lang() and run() keep "hr" for a request whose body says "lang": "hr" (once PAGE_LANGS has it).

The style titles on the artwork ("THE UNIVERSE WITHIN", ...) and the signature line ARTWORK_FOOTER stay English: they
are the brand's; no Croatian version is proposed.
"""

# The tile is the site's address alone in every language since 2026-10-20 (iris.py WATERMARK_TILE).
WATERMARK_TEXT_HR = ("SnapEyes.com", "PREGLED S VODENIM ŽIGOM  ·  NARUČITE PUNU VELIČINU")
# The badge while ordering is closed (iris.py WATERMARK_SOON): "free preview", then "orders start soon" ("FREE PREVIEW  ·
# ORDERING OPENS SOON"). Pill 445 px on the 1024 px square (German 518), so narrower than the German badge everywhere.
# Written without a native reader.
WATERMARK_SOON_HR = "BESPLATNI PREGLED  ·  NARUČIVANJE USKORO"

ERRORS_HR = {
    # PermissionError that is an UnlockError: a download link that expired or belongs to another order
    "unlock": ("Ova poveznica za preuzimanje je istekla ili ne pripada ovoj narudžbi. Molimo ponovno otvorite poveznicu "
               "iz svoje narudžbe ili nam pišite na info@snapeyes.com."),
    # any other PermissionError: the photo's work ticket expired
    "session": "Ova je sesija istekla. Molimo ponovno fotografirajte svoje oko.",
    # ValueError: an image that cannot be read
    "unreadable": "Ovu sliku nismo mogli učitati. Pokušajte s drugom fotografijom.",
    # ModelBusy
    "busy": "Naš je studio trenutačno vrlo zauzet. Molimo pokušajte ponovno za minutu.",
    # ModelDenied: the model refused our key
    "denied": "Naš je studio na trenutak zatvoren. Molimo pokušajte ponovno kasnije.",
    # anything else
    "failed": "Nešto je pošlo po zlu kod nas. Molimo pokušajte ponovno.",
}
