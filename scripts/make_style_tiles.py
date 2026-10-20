# -*- coding: utf-8 -*-
"""Makes the tile images of the styles shown to customers: public/assets/atelier/style-<slug>-480.webp and -800.webp, one pair of files per style
at stage preview or live (api/_lib/styles_registry.py; scripts/check_styles.mjs item 8 refuses the build when one is missing).

    python scripts/make_style_tiles.py --eyes <folder> [--out public/assets/atelier] [--only slug ...] [--list]

Every picture is made by the engine of this repository (api/_lib/styles, the same code the free preview and the paid file run), clean (no watermark: the
page labels an example as an example), from the restored irises of the owner's own eye and of two photos he has confirmed the right to publish on the
page (the eye files are NOT in the repository and never enter it: --eyes names the folder that holds them). Nothing here calls an image model or reads a key.

The eyes (file names in <folder>): own215120_2_enhanced.jpg (the owner's own eye), drv_w03_2_enhanced.jpg (brown) and drv_w04_2_enhanced.jpg (yellow green),
and for the ensemble family (2026-10-20) two more of the photos the owner holds the rights to publish (scripts/landing_assets_provenance.json, LICENCIJOS.csv w06 and
w09): drv_w06_2_enhanced.jpg (dark brown) and drv_w09_2_enhanced.jpg (violet brown). The ensemble tiles keep the owner's sample rule of 2026-10-20 for every public
picture: no eye whose eyelid skin or lashes show above the iris (drv_w03 has pink lid skin at the top, drv_d01 lashes: neither is in an ensemble tile) and no set with
one pupil far bigger than the others. A command reads only the eyes of the tiles it makes.
  one eye          the owner's own eye
  Kiss Collision   own eye and the brown one
  Infinity pairs   own eye and the yellow green one (the high contrast pair that shows the smooth seam)
  Family Colours   all three, the Trio
  Clean Duo        own eye and the yellow green one; Radiance Duo: own eye and the dark brown one
  Family Orbit, Light Circle, Radiance Family: four eyes (own, yellow green, dark brown, violet brown; Family Orbit has the owner's own eye in the middle)
  the other looks of the ensemble family (Nebula and Supernova as a pair and a family): no row of SETS, the family's defaults (the pair on the own eye and the
                   dark brown one, the family on the four eyes): their slugs carry the word of a legacy id, which this script may not write
The size of a picture is the long side of the family's default canvas at 1024 px (a preview), reduced with LANCZOS to 800 and 480 px; WEBP quality 80 and 78.
The same command run again on the same code and the same eyes gives the same files (the seed comes from the eye ids, which are hashes of the files).

Rules that hold for the files this makes: they carry no text but the customer's own words (none are given), no hearts, and one picture per style.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "api"))
sys.dont_write_bytecode = True

EYES = {"own": "own215120_2_enhanced.jpg", "brown": "drv_w03_2_enhanced.jpg", "yellow": "drv_w04_2_enhanced.jpg", "dark": "drv_w06_2_enhanced.jpg",
        "violet": "drv_w09_2_enhanced.jpg"}
# tile slug -> the eyes it is shown on, in the order of the canvas (keyed by slug, the file name part of the tile images: the registry holds the ids)
SETS = {
    "clean-iris": ("own",),
    "powder-burst": ("own",),
    "universe": ("own",),
    "splash": ("own",),
    "celestial-gold": ("own",),
    "radiance": ("own",),
    "kiss-collision": ("own", "brown"),
    "collision-infinity": ("own", "yellow"),
    "clean-infinity": ("own", "yellow"),
    "family-colours": ("own", "yellow", "brown"),
    "clean-duo": ("own", "yellow"),
    "radiance-duo": ("own", "dark"),
    "family-orbit": ("own", "yellow", "dark", "violet"),
    "light-circle": ("own", "yellow", "dark", "violet"),
    "radiance-family": ("own", "yellow", "dark", "violet"),
}
ONE_EYE = ("own",)          # a style of one eye that SETS does not name is shown on the owner's own eye, as every style of one eye is
ENSEMBLE_PAIR = ("own", "dark")                          # a pair of the ensemble family that SETS does not name
ENSEMBLE_GROUP = ("own", "yellow", "dark", "violet")     # a family of the ensemble family that SETS does not name
WIDTHS = ((800, 80), (480, 78))
SIDE = 1024
NO_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_KEY")


def eye_set(style_id, C):
    """The eyes a style's tile is shown on: its row of SETS, else the owner's own eye for a style of one eye and the ensemble family's defaults for its pairs
    and families (None: any other style of more eyes needs its row)."""
    keys = SETS.get(C.slug_of(style_id))
    if keys is None and C.eyes_range(style_id) == (1, 1):
        keys = ONE_EYE
    if keys is None and ((C.ENGINE.get(style_id) or {}).get("engine") or {}).get("module") == "ensemble":
        keys = ENSEMBLE_PAIR if C.eyes_range(style_id) == (2, 2) else ENSEMBLE_GROUP
    return keys


def shown_styles():
    """The ids at preview or live for some eye count, in registry order: the styles that need tile images (a legacy id of the same slug shares the file)."""
    from _lib import catalogue as C
    out = []
    for i, d in C.STYLES.items():
        if any(C.ceiling(i, n) in ("preview", "live") for n in range(d["eyes"][0], d["eyes"][1] + 1)):
            out.append(i)
    return out


def load_eyes(folder, keys=None):
    raws = {}
    for key, name in EYES.items():
        if keys is not None and key not in keys:
            continue
        p = os.path.join(folder, name)
        if not os.path.isfile(p):
            sys.exit(f"make_style_tiles: {p} is missing: --eyes names the folder with {', '.join(EYES[k] for k in (keys or EYES))}")
        with open(p, "rb") as f:
            raws[key] = f.read()
    return raws


def make_one(style_id, raws, ST, C, SCORE):
    keys = eye_set(style_id, C)
    n = len(keys)
    eyes = []
    for k in keys:
        raw = raws[k]
        eyes.append(SCORE.Iris(raw, f"tile_{k}", max_side=min(2048, C.work_side(style_id, n) or 2048), eye_id=hashlib.sha256(raw).hexdigest()[:16]))
    layout = C.default_layout(style_id, n)
    spec = {"style": style_id, "layout": layout, "eyes": n, "canvas": None, "names": [], "date": "", "family_name": "", "opts": {},
            "eye_ids": [e.eye_id for e in eyes], "profiles": [None] * n, "lang": "en"}
    pv = ST.preview(eyes, spec, size=SIDE, watermark=False)
    return pv.img.convert("RGB"), pv


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--eyes", help="the folder that holds the restored eyes (never in the repository)")
    ap.add_argument("--out", default=os.path.join(REPO, "public", "assets", "atelier"))
    ap.add_argument("--only", nargs="*", help="slugs to make (default: every style shown to customers)")
    ap.add_argument("--list", action="store_true", help="print the styles that need tile images and stop")
    a = ap.parse_args(argv)
    for k in NO_KEYS:
        os.environ.pop(k, None)
    from _lib import catalogue as C
    shown = shown_styles()
    if a.list:
        for i in shown:
            print(i, C.slug_of(i), "->", "+".join(eye_set(i, C) or ("?",)))
        return 0
    missing = [C.slug_of(i) for i in shown if eye_set(i, C) is None]
    if missing:
        sys.exit(f"make_style_tiles: no eye set for {', '.join(missing)}: add the slug to SETS")
    if not a.eyes:
        sys.exit("make_style_tiles: --eyes <folder> is required")
    from PIL import Image
    from _lib import styles as ST
    from _lib.styles import core as SCORE
    todo = [i for i in shown if not a.only or C.slug_of(i) in a.only]
    raws = load_eyes(a.eyes, {k for i in todo for k in eye_set(i, C)})
    os.makedirs(a.out, exist_ok=True)
    for i in shown:
        slug = C.slug_of(i)
        if a.only and slug not in a.only:
            continue
        img, pv = make_one(i, raws, ST, C, SCORE)
        for w, q in WIDTHS:
            im = img if img.size[0] == w else img.resize((w, round(img.size[1] * w / img.size[0])), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=q, method=6)
            path = os.path.join(a.out, f"style-{slug}-{w}.webp")
            with open(path, "wb") as f:
                f.write(buf.getvalue())
            print(f"{i:24s} {os.path.basename(path):40s} {im.size[0]}x{im.size[1]} {len(buf.getvalue()):7d} bytes  design {pv.design}  seed {pv.seed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
