# -*- coding: utf-8 -*-
"""Offline tool (never in a function or a bundle: scripts/ is excluded): a contact sheet of the usable plates of one family, from the bundle.

    python scripts/plate_sheet.py P-CX-JET --out sheet.png [--cell 256] [--cols 5] [--gain 1]
    python scripts/plate_sheet.py P-CX-JET --out strips.png --strips 140 --gain 3     the bottom 140 rows of each plate, brightened, two to a row

Why it exists: the plates are generated pictures, and a generator sometimes draws a legend into one (a scale bar, a size key with "(mm)", a caption).
No pixel test finds that: every plate holds debris, specks and chips detached from the plume, so island, edge-run and component counts flag
nearly every plate (tried on all 169, 2026-10-05). The two JET plates that had one were found on a 256 px sheet, and the bake's RETOUCH table
(scripts/bake_plates_registry.py) holds the fix. Look at a sheet of every family you add to the library, and at the strips (the legends sit
near the bottom edge) with a gain of 3, before baking it; each plate is labelled with its position in the sorted order, and the ids are printed.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("family", help="a plate family, for example P-CX-JET")
    ap.add_argument("--out", required=True, help="the PNG to write (outside the repository)")
    ap.add_argument("--cell", type=int, default=256, help="the side of one plate on the sheet, px")
    ap.add_argument("--cols", type=int, default=5)
    ap.add_argument("--gain", type=float, default=1.0, help="a brightness factor, clipped at white (3 shows what is faint)")
    ap.add_argument("--strips", type=int, default=0, help="show only the bottom N rows (of 1024) of each plate, full width")
    a = ap.parse_args()
    from _lib import plates_registry as REG
    table = REG.PLATES_REGISTRY["plates"]
    ids = sorted(i for i, r in table.items() if r["family"] == a.family and r["usable"])
    if not ids:
        sys.exit(f"no usable plate in {a.family}")
    folder = os.path.join(ROOT, "api", "_assets", "plates", a.family)
    if a.strips:
        w = 2 * a.cell                                  # two strips side by side, at half the plate's own size
        h = max(8, a.strips * w // 1024)
    else:
        w = h = a.cell
    cols = 2 if a.strips else a.cols
    rows = (len(ids) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (40, 40, 40))
    draw = ImageDraw.Draw(sheet)
    for n, pid in enumerate(ids):
        im = Image.open(os.path.join(folder, table[pid]["k1"]["file"])).convert("RGB")
        if a.strips:
            im = im.crop((0, 1024 - a.strips, 1024, 1024))
        if a.gain != 1.0:
            im = Image.fromarray(np.clip(np.asarray(im, np.float32) * a.gain, 0, 255).astype(np.uint8))
        im = im.resize((w - 4, h - 4), Image.LANCZOS)
        x, y = (n % cols) * w, (n // cols) * h
        sheet.paste(im, (x + 2, y + 2))
        draw.text((x + 6, y + 6), str(n), fill=(255, 220, 90))
        print(n, pid)
    sheet.save(a.out)
    print(f"wrote {a.out}: {len(ids)} plates, {sheet.size[0]} x {sheet.size[1]} px")


if __name__ == "__main__":
    main()
