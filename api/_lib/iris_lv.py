"""Latvian ("lv") strings of api/_lib/iris.py: the preview watermark and the engine's error sentences in run() (the twin
of iris_hr.py).

WATERMARK_TEXT_LV  WATERMARK_TEXT["lv"] = (tile, badge). "PRIEKŠSKATĪJUMS" is the site's word for the preview,
                   "ŪDENSZĪME" for the watermark; the badge is a polite call to order the full size ("PASŪTIET PILNĀ
                   IZMĒRĀ"), like the English "UNLOCK FULL SIZE". Measured with the engine's own font and sizing
                   (PlusJakartaSans.ttf Bold at 0.016 u, the pill the text plus 0.044 u):
                     badge pill 509 px on the 1024 px square (German 592, Croatian 491, English 411); every canvas
                     scales the same way, so it stays about 14 % narrower than the German badge everywhere;
                     the tile is the site's address alone (iris.py WATERMARK_TILE), the same in every language.
                   Plus Jakarta Sans has every Latvian letter (Ā, Č, Ē, Ģ, Ī, Ķ, Ļ, Ņ, Š, Ū, Ž and the small ones,
                   checked with fontTools), so nothing falls back to a box. While a deployment takes no orders it still
                   says "pasūtiet", as the English and German badges do.
ERRORS_LV          the sentences run() sends for its refusals (iris.py RUN_ERRORS["lv"]).
page_lang() and run() keep "lv" for a request whose body says "lang": "lv" (once PAGE_LANGS has it).

The style titles on the artwork ("THE UNIVERSE WITHIN", ...) and the signature line ARTWORK_FOOTER stay English: they
are the brand's; no Latvian version is proposed.
"""

# The tile is the site's address alone in every language since 2026-10-20 (iris.py WATERMARK_TILE).
WATERMARK_TEXT_LV = ("SnapEyes.com", "PRIEKŠSKATĪJUMS AR ŪDENSZĪMI  ·  PASŪTIET PILNĀ IZMĒRĀ")
# The badge while ordering is closed (iris.py WATERMARK_SOON): "free preview", then "orders soon" ("FREE PREVIEW  ·
# ORDERING OPENS SOON"). Pill 441 px on the 1024 px square (German 518), so narrower than the German badge everywhere.
WATERMARK_SOON_LV = "BEZMAKSAS PRIEKŠSKATĪJUMS  ·  PASŪTĪJUMI DRĪZ"

ERRORS_LV = {
    # PermissionError that is an UnlockError: a download link that expired or belongs to another order
    "unlock": ("Šīs lejupielādes saites derīgums ir beidzies, vai arī tā nepieder šim pasūtījumam. Lūdzu, atveriet saiti "
               "no sava pasūtījuma vēlreiz vai rakstiet uz info@snapeyes.com."),
    # any other PermissionError: the photo's work ticket expired
    "session": "Šīs sesijas laiks ir beidzies. Lūdzu, nofotografējiet savu aci vēlreiz.",
    # ValueError: an image that cannot be read
    "unreadable": "Šo attēlu neizdevās nolasīt. Mēģiniet ar citu fotogrāfiju.",
    # ModelBusy
    "busy": "Mūsu studija pašlaik ir ļoti aizņemta. Lūdzu, mēģiniet vēlreiz pēc minūtes.",
    # ModelDenied: the model refused our key
    "denied": "Mūsu studija uz brīdi ir slēgta. Lūdzu, mēģiniet vēlreiz vēlāk.",
    # anything else
    "failed": "Mūsu pusē kaut kas nogāja greizi. Lūdzu, mēģiniet vēlreiz.",
    "limit": ("No šī savienojuma ir sasniegts šodienas bezmaksas priekšskatījumu limits ({n} dienā). Jaunus varēsiet "
              "izveidot rīt. Jau izveidotos priekšskatījumus joprojām varat pasūtīt. Jautājumi? Rakstiet uz "
              "info@snapeyes.com."),
}
