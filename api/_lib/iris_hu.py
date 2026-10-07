"""Hungarian ("hu") strings of api/_lib/iris.py: the preview watermark and the engine's error sentences in run().

WATERMARK_TEXT_HU  WATERMARK_TEXT["hu"] = (tile, badge). Measured on every canvas /api/compose makes for a preview
                   (1024 px on the longest side: the square, every multi-eye layout as artwork and as the 473 x 1024
                   wallpaper), with the engine's own fonts and sizing:
                     badge pill 481 px on the 1024 px square (German 592, English 411); on the 473 px wallpaper
                     311 px of the 469 px room (German 391, English 266), 158 px to spare;
                     tile text 520 px against the 716 px tile step (German 542, English 495);
                     the sample-eye note "MI ÁLTAL GENERÁLT MINTA" fits every canvas too.
                   Plus Jakarta Sans has every Hungarian letter (Ő, Ű, É, Á, Í checked with fontTools), so nothing falls
                   back to a box. The badge is a call to action in the "te" form, like the English "UNLOCK FULL SIZE".
                   While a deployment takes no orders it still says "rendeld meg", as the English and German badges do.
                   Shorter measured alternatives that also fit everywhere: "VÍZJELES ELŐNÉZET  ·  TELJES MÉRET
                   RENDELÉSRE" (437 px pill on the square) and, closest to the German, "ELŐNÉZET VÍZJELLEL  ·  A TELJES
                   MÉRETŰ FÁJL MEGVÁSÁRLÁSA" (538 px pill).
ERRORS_HU          the sentences run() sends for its five refusals (iris.py RUN_ERRORS["hu"]).
page_lang() and run() keep "hu" for a request whose body says "lang": "hu".

The style titles on the artwork ("THE UNIVERSE WITHIN", ...) and the signature line ARTWORK_FOOTER stay English: they
are the brand's; no Hungarian version is proposed.
"""

WATERMARK_TEXT_HU = ("SNAPEYES.COM  ·  ELŐNÉZET", "VÍZJELES ELŐNÉZET  ·  RENDELD MEG TELJES MÉRETBEN")

ERRORS_HU = {
    # PermissionError that is an UnlockError: a download link that expired or belongs to another order
    "unlock": ("Ez a letöltési link lejárt, vagy nem ehhez a rendeléshez tartozik. Kérjük, nyisd meg újra a "
               "rendelésedben kapott linket, vagy írj nekünk: info@snapeyes.com."),
    # any other PermissionError: the photo's work ticket expired
    "session": "Ez a munkamenet lejárt. Kérjük, fotózd le újra a szemed.",
    # ValueError: an image that cannot be read
    "unreadable": "Ezt a képet nem tudtuk beolvasni. Kérjük, próbáld egy másik fotóval.",
    # ModelBusy
    "busy": "A stúdiónk most nagyon leterhelt. Kérjük, próbáld újra egy perc múlva.",
    # ModelDenied: the model refused our key
    "denied": "A stúdiónk egy időre zárva van. Kérjük, próbáld újra később.",
    # anything else
    "failed": "Hiba történt nálunk. Kérjük, próbáld újra.",
}
