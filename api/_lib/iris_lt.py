"""The Lithuanian words of api/_lib/iris.py: WATERMARK_TEXT["lt"] = (tile, badge) and the five customer sentences of run()
(RUN_ERRORS["lt"]). page_lang() keeps "lt" for a request whose body says "lang": "lt".

Tile: "PERŽIŪRA" is the site's word for the preview. Badge: "PERŽIŪRA SU VANDENS ŽENKLU" (watermarked preview) and a
polite call to order the full-size file, "UŽSAKYKITE VISO DYDŽIO FAILĄ" ("viso dydžio", never "pilno dydžio", which
Lithuanian style guides flag). All capitals, as the English and German pairs; both engine fonts (PlusJakartaSans.ttf
and Cinzel.ttf, and the site's two woff2 files) have every Lithuanian letter (ą č ę ė į š ų ū ž, checked with
fontTools).

MEASURED with the engine's own fonts and sizes on the 6 distinct preview canvases /api/compose makes at 1024 px:
                                   Lithuanian        German            English
  badge text, 1024 px square       516.0 px          547.0 px          366.0 px
  badge pill, 1024 px square       561.1 of 1020     592.1 of 1020     411.1 of 1020
  badge pill, 473 x 1024 wallpaper 373.7 of 469      390.7 of 469      265.7 of 469   (the tightest canvas)
  tile text vs 716 px tile step    508.0 px (71 %)   542.0 px (76 %)   495.0 px (69 %)
  sample note pill, square         247.8 px          218.8 px          202.8 px
The German figures reproduce the ones iris.py's comment gives (592 px, 391 px, 542 against 716). The Lithuanian badge
and tile are narrower than the German ones on every canvas, so the pill keeps its words inside it everywhere (95 px to
spare on the wallpaper, German 78 px), and the tile rows keep their gap (at most 72 % of the step, German 76 %). A
shorter call to action that also fits everywhere: "UŽSAKYKITE VISĄ DYDĮ".
"""

WATERMARK_TEXT_LT = ("SNAPEYES.COM  ·  PERŽIŪRA", "PERŽIŪRA SU VANDENS ŽENKLU  ·  UŽSAKYKITE VISO DYDŽIO FAILĄ")

# The customer sentences of run(), which answer in the page's language once the body is parsed (iris.py RUN_ERRORS): the
# Lithuanian twin of each German/English pair, keyed by the exception it answers.
RUN_ERRORS_LT = {
    # PermissionError that is an UnlockError: a paid endpoint got no valid unlock ticket for this order
    "unlock": ("Ši atsisiuntimo nuoroda nebegalioja arba nepriklauso šiam užsakymui. Dar kartą atidarykite nuorodą iš "
               "savo užsakymo arba parašykite mums adresu info@snapeyes.com."),
    # any other PermissionError: the work ticket of the photo expired
    "session": "Ši sesija baigėsi. Nufotografuokite savo akį dar kartą.",
    # ValueError: the image could not be read
    "unreadable": "Nepavyko nuskaityti šio vaizdo. Pabandykite su kita nuotrauka.",
    # ModelBusy
    "busy": "Mūsų studija šiuo metu labai užimta. Po minutės bandykite dar kartą.",
    # ModelDenied: the model refused our key
    "denied": "Mūsų studija trumpam uždaryta. Bandykite dar kartą vėliau.",
    # anything else (500)
    "failed": "Mūsų pusėje kažkas nepavyko. Bandykite dar kartą.",
}

# Left in English on purpose, as the German pages leave them: the art styles' default title drawn in the artwork
# (STYLES[...]["title"], e.g. "THE UNIVERSE WITHIN") and the signature line ARTWORK_FOOTER "SNAPEYES  ·  PRECISION IRIS
# ART" (the brand's). Should the owner want them in Lithuanian, "VIDINĖ VISATA" (not the calque "VISATA VIDUJE", 342 px
# against the English title's 531 px, so it fits wherever the English one does) and "SNAPEYES  ·  PRECIZIŠKAS RAINELĖS
# MENAS" (286 px, English 213 px, inside 90 % of even the 473 px wallpaper) were measured with _caption's own fonts.
