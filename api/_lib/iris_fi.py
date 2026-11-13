"""Finnish ("fi") strings of api/_lib/iris.py: the preview watermark and the engine's error sentences in run() (the twin
of iris_hr.py).

WATERMARK_TEXT_FI  WATERMARK_TEXT["fi"] = (tile, badge). "ESIKATSELU" is the site's word for the preview, "VESILEIMA" for
                   the watermark; the badge is a call to order the full size ("TILAA TÄYSI KOKO"), like the English
                   "UNLOCK FULL SIZE". Measured with the engine's own font and sizing (PlusJakartaSans.ttf Bold at
                   0.016 u, the pill the text plus 0.044 u):
                     badge pill 421 px on the 1024 px square (German 592, English 411, Croatian 491); every canvas
                     scales the same way, so it stays about 29 % narrower than the German badge everywhere;
                     the tile is the site's address alone (iris.py WATERMARK_TILE), the same in every language.
                   Plus Jakarta Sans has every Finnish letter (Ä, Ö, Å and the small ones, checked with fontTools), so
                   nothing falls back to a box. While a deployment takes no orders the badge is WATERMARK_SOON_FI. A
                   longer measured alternative, closest to the German: "ESIKATSELU VESILEIMALLA  ·  TILAA TÄYSIKOKOINEN
                   TIEDOSTO" (541 px pill on the square), not used: the short one says the same.
ERRORS_FI          the sentences run() sends for its refusals (iris.py RUN_ERRORS["fi"]), informal "sinä" as the page.
page_lang() and run() keep "fi" for a request whose body says "lang": "fi" (once PAGE_LANGS has it).

The style titles on the artwork ("THE UNIVERSE WITHIN", ...) and the signature line ARTWORK_FOOTER stay English: they
are the brand's; no Finnish version is proposed.
"""

# The tile is the site's address alone in every language since 2026-10-20 (iris.py WATERMARK_TILE).
WATERMARK_TEXT_FI = ("SnapEyes.com", "ESIKATSELU VESILEIMALLA  ·  TILAA TÄYSI KOKO")
# The badge while ordering is closed (iris.py WATERMARK_SOON): "free preview", then "ordering opens soon" ("FREE PREVIEW  ·
# ORDERING OPENS SOON"), the words of the landing's notice. Pill 450 px on the 1024 px square (German 518), so narrower
# than the German badge everywhere.
WATERMARK_SOON_FI = "ILMAINEN ESIKATSELU  ·  TILAAMINEN AVAUTUU PIAN"

ERRORS_FI = {
    # PermissionError that is an UnlockError: a download link that expired or belongs to another order
    "unlock": ("Tämä latauslinkki on vanhentunut tai ei kuulu tähän tilaukseen. Avaa tilauksesi linkki uudelleen tai "
               "kirjoita osoitteeseen info@snapeyes.com."),
    # any other PermissionError: the photo's work ticket expired
    "session": "Tämä istunto on vanhentunut. Ota kuva silmästäsi uudelleen.",
    # ValueError: an image that cannot be read
    "unreadable": "Emme pystyneet lukemaan tätä kuvaa. Kokeile toista kuvaa.",
    # ModelBusy
    "busy": "Studiossamme on juuri nyt paljon ruuhkaa. Yritä minuutin kuluttua uudelleen.",
    # ModelDenied: the model refused our key
    "denied": "Studiomme on hetken suljettu. Yritä myöhemmin uudelleen.",
    # anything else
    "failed": "Meidän päässämme meni jokin vikaan. Yritä uudelleen.",
    "limit": ("Tältä yhteydeltä on käytetty tämän päivän ilmaisten esikatselujen raja ({n} päivässä). Voit tehdä lisää "
              "huomenna. Jo tekemäsi esikatselut voit edelleen tilata. Kysyttävää? Kirjoita osoitteeseen "
              "info@snapeyes.com."),
}
