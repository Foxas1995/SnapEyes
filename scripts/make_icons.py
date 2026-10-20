# -*- coding: utf-8 -*-
"""The site's icons: the iris ring of the header (src/landing/Header.tsx LogoMark: a hairline ring, a ring, a filled centre, in the gold #f5c542) on the site's dark
(#07090e). public/favicon.svg is written by hand (it is the same three circles with heavier strokes, so that it still reads at 16 px); this script draws the same
geometry as PNG and ICO with Pillow (supersampled, no font and no other input), so the files can be made again:

    python scripts/make_icons.py        writes public/favicon.ico (16, 32, 48), apple-touch-icon.png (180), icon-192.png and icon-512.png

The geometry is the SVG's, in a 32 unit square: tile corner radius 7 (the touch icon and the two app icons are full-bleed squares: the system rounds them),
rings r 13 (stroke 2) and r 8 (stroke 2.4) and a centre r 3.2 up to 48 px (the tab icon); from 64 px up the header's own mark: the hairline ring r 15 (55 percent),
the ring r 9.5 (stroke 1.4) and the centre r 4, all at the centre (16, 16)."""
import io
import os
import struct

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public")
GOLD = (245, 197, 66)
DARK = (7, 9, 14)
SS = 8        # supersampling


def mark(px, tile, rounded):
    """The mark in a px square: the dark tile (rounded or full-bleed) and the rings, drawn at SS times the size and shrunk."""
    big = px * SS
    u = big / 32.0
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle((0, 0, big - 1, big - 1), radius=7 * u, fill=DARK + (255,))
    else:
        d.rectangle((0, 0, big, big), fill=DARK + (255,))
    k = tile             # the share of the tile the mark takes (full-bleed icons keep a margin for the rounded corners the system adds)
    c = 16 * u

    def ring(r, w, fill=None, alpha=255):
        r, w = r * k * u, w * k * u
        d.ellipse((c - r - w / 2, c - r - w / 2, c + r + w / 2, c + r + w / 2), outline=GOLD + (alpha,), width=max(1, int(round(w))))

    if px >= 64:      # the header's own mark: the hairline ring (55 percent), the ring, the centre
        ring(15, 1.0, alpha=140)
        ring(9.5, 1.4)
        r = 4.0 * k * u
    else:             # a tab icon: heavier strokes, or the rings are a grey smear at 16 px
        ring(13, 2.0)
        ring(8, 2.4)
        r = 3.2 * k * u
    d.ellipse((c - r, c - r, c + r, c + r), fill=GOLD + (255,))
    return img.resize((px, px), Image.LANCZOS)


def ico(images):
    """An ICO file of PNG-compressed images, each drawn at its own size (Pillow's own ICO writer shrinks one picture to the others, which blurs the 16 px one)."""
    blobs = []
    for im in images:
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        blobs.append((im.size[0], buf.getvalue()))
    out = struct.pack("<HHH", 0, 1, len(blobs))
    offset = 6 + 16 * len(blobs)
    for px, data in blobs:
        out += struct.pack("<BBBBHHII", px % 256, px % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return out + b"".join(d for _, d in blobs)


def main():
    os.makedirs(PUBLIC, exist_ok=True)
    with open(os.path.join(PUBLIC, "favicon.ico"), "wb") as f:
        f.write(ico([mark(s, 1.0, True) for s in (16, 32, 48)]))
    for name, px, k in (("apple-touch-icon.png", 180, 0.86), ("icon-192.png", 192, 0.86), ("icon-512.png", 512, 0.86)):
        mark(px, k, False).convert("RGB").save(os.path.join(PUBLIC, name), "PNG", optimize=True)
    for name in ("favicon.ico", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
        print(f"{name}: {os.path.getsize(os.path.join(PUBLIC, name))} bytes")


if __name__ == "__main__":
    main()
