"""Estonian ("et") strings of api/_lib/iris.py: the preview watermark and the engine's error sentences in run() (the twin
of iris_hr.py).

WATERMARK_TEXT_ET  WATERMARK_TEXT["et"] = (tile, badge). "EELVAADE" is the site's word for the preview, "VESIMÄRGIGA" says
                   it carries a watermark; the badge is a call to order the full-size file ("TELLI TÄISSUURUSES FAIL"),
                   like the English "UNLOCK FULL SIZE", in the informal singular of the Estonian page. Measured with the
                   engine's own font and sizing (PlusJakartaSans.ttf Bold at 0.016 u, the pill the text plus 0.044 u):
                     badge pill 463 px on the 1024 px square (German 592, Croatian 491, English 411); every canvas scales
                     the same way, so it stays about 22 % narrower than the German badge everywhere;
                     the tile is the site's address alone (iris.py WATERMARK_TILE), the same in every language.
                   Plus Jakarta Sans has every Estonian letter (Ä, Ö, Ü, Õ, Š, Ž and the small ones, checked with
                   fontTools), so nothing falls back to a box. While a deployment takes no orders it still says
                   "telli", as the English and German badges do. A shorter measured alternative: "VESIMÄRGIGA EELVAADE
                   ·  TELLI TÄISSUURUS" (406 px pill on the square), not used because it does not name the file.
ERRORS_ET          the sentences run() sends for its refusals (iris.py RUN_ERRORS["et"]).
page_lang() and run() keep "et" for a request whose body says "lang": "et" (once PAGE_LANGS has it).

The style titles on the artwork ("THE UNIVERSE WITHIN", ...) and the signature line ARTWORK_FOOTER stay English: they
are the brand's; no Estonian version is proposed.
"""

# The tile is the site's address alone in every language since 2026-10-20 (iris.py WATERMARK_TILE).
WATERMARK_TEXT_ET = ("SnapEyes.com", "VESIMÄRGIGA EELVAADE  ·  TELLI TÄISSUURUSES FAIL")
# The badge while ordering is closed (iris.py WATERMARK_SOON): "free preview", then "ordering opens soon" ("FREE PREVIEW  ·
# ORDERING OPENS SOON"), the words of the landing's notice. Pill 414 px on the 1024 px square (German 518), so narrower
# than the German badge everywhere.
WATERMARK_SOON_ET = "TASUTA EELVAADE  ·  TELLIMINE AVANEB PEAGI"

ERRORS_ET = {
    # PermissionError that is an UnlockError: a download link that expired or belongs to another order
    "unlock": ("See allalaadimislink on aegunud või ei kuulu selle tellimuse juurde. Palun ava oma tellimuses olev link "
               "uuesti või kirjuta aadressile info@snapeyes.com."),
    # any other PermissionError: the photo's work ticket expired
    "session": "See seanss on aegunud. Palun tee foto uuesti.",
    # ValueError: an image that cannot be read
    "unreadable": "Me ei saanud seda pilti lugeda. Proovi teise fotoga.",
    # ModelBusy
    "busy": "Meie stuudio on praegu väga hõivatud. Palun proovi minuti pärast uuesti.",
    # ModelDenied: the model refused our key
    "denied": "Meie stuudio on hetkeks suletud. Palun proovi hiljem uuesti.",
    # anything else
    "failed": "Meie poolel läks midagi valesti. Palun proovi uuesti.",
    "limit": ("Sellest ühendusest on tänane tasuta eelvaadete piir täis ({n} päevas). Homme saad teha uusi. Juba tehtud "
              "eelvaateid saad endiselt tellida. Küsimusi? Kirjuta aadressile info@snapeyes.com."),
}
