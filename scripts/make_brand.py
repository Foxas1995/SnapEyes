# -*- coding: utf-8 -*-
"""The SnapEyes logo on the site: the owner's own design (the eye on the right with a gold aperture iris, the gold and black swooshes, the
script name "SnapEyes"), approved by him on 2026-10-22 and supplied by him as a 4096 px master. Nothing is redrawn: every file here is cut,
recoloured or scaled from his master.

    assets/brand/snapeyes-logo-master.png   his logo, transparent (the white taken away by colour-to-alpha), 2400 px wide
    assets/brand/iris.json                  where the iris is in that file (centre, pupil, gold ring, black ring), for the icons and the dark version

The page is dark (#07090e), so the site shows the DARK version: his black strokes, black lid lines, lashes and the black "Eyes" turn a warm
cream (#efe6d2); the gold is untouched; inside the iris nothing changes (the pupil stays black inside its gold ring, the catch-light white).

    python scripts/make_brand.py            writes public/brand (the header, footer and 404 logos, WebP and PNG, 1x 2x 3x) and the icons
                                            (public/favicon.ico 16 32 48, favicon-16/32/48.png, apple-touch-icon.png 180, icon-192.png, icon-512.png)
    python scripts/make_brand.py --check    draws everything again and compares it with the committed files

The cut itself (his JPEG -> the transparent master) is made once, outside the repository: a small noise floor near white (the JPEG's
white reads 251 to 255), alpha only where the artwork meets the background, relative to the stroke's own ink, then the colours
unmultiplied from white; the only white kept is the catch-light (scratchpad wave-logo/final_logo_work/build/cut.py)."""
import io, json, os, sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "assets", "brand", "snapeyes-logo-master.png")
IRIS = os.path.join(ROOT, "assets", "brand", "iris.json")
PUBLIC = os.path.join(ROOT, "public")
BRAND = os.path.join(PUBLIC, "brand")
CREAM = (239, 230, 210)          # #efe6d2
LIGHT_GOLD = (233, 212, 161)     # #e9d4a1, the other dark option the owner can compare
DARK = (7, 9, 14)                # #07090e, the page

# the files the site uses (height in CSS px, densities)
FULL_HEIGHTS = {"h56": 56, "h96": 96}       # the full logo: the header from 768 px up (56) and the footer and the 404 page (96)
EYE_HEIGHTS = {"h34": 34}                   # the eye with a short swoosh: the header under 768 px (shown 28 to 34 px tall)
DENSITIES = (1, 2, 3)


def load():
    m = Image.open(MASTER).convert("RGBA")
    with open(IRIS, encoding="utf-8") as f:
        iris = json.load(f)
    return m, iris


def recolour(img, iris, target=CREAM):
    """The dark version: every neutral dark pixel (his black ink: low chroma, dark) moves to the target colour, in proportion to how black
    it is; gold (chromatic) stays; inside the iris's gold ring nothing changes."""
    a = np.asarray(img).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3:]
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    w = np.clip((70.0 - chroma) / 45.0, 0, 1) * np.clip((175.0 - lum) / 95.0, 0, 1)
    h, wd = w.shape
    yy, xx = np.ogrid[:h, :wd]
    inside = (yy - iris["cy"]) ** 2 + (xx - iris["cx"]) ** 2 < (iris["gold_r"] + 2) ** 2
    w[inside] = 0.0
    out = rgb * (1 - w[..., None]) + np.array(target, dtype=np.float32) * w[..., None]
    return Image.fromarray(np.dstack([out, al]).round().clip(0, 255).astype(np.uint8), "RGBA")


def scaled(img, width=None, height=None):
    """High quality scaling with premultiplied alpha (no dark or light fringe at the edges)."""
    if width is None:
        width = round(img.width * height / img.height)
    if height is None:
        height = round(img.height * width / img.width)
    return img.convert("RGBa").resize((width, height), Image.LANCZOS).convert("RGBA")


def eye_crop(img, iris):
    """The eye with a short swoosh: the eye, its lashes and the strokes that enter it, faded out to the left (the name stays out)."""
    s = img.width / 3827.0                       # the crop was chosen on the 3827 px cut
    box = (round(2000 * s), round(110 * s), img.width, round(1180 * s))
    c = img.crop(box)
    a = np.asarray(c).astype(np.float32)
    fade = np.clip((np.arange(c.width) - 0) / (350 * s), 0, 1) ** 1.4
    a[..., 3] *= fade[None, :]
    return Image.fromarray(a.round().astype(np.uint8), "RGBA")


def iris_disc(img, iris, px, bg=None, fill=1.0):
    """The iris alone (the gold aperture, the black pupil, the catch-light, its black ring) in a px square; fill = the share of the square
    the black ring's diameter takes; bg None = transparent."""
    r = iris["black_r"] + 1.5
    box = (round(iris["cx"] - r), round(iris["cy"] - r), round(iris["cx"] + r), round(iris["cy"] + r))
    c = img.crop(box)
    # a round mask (anti-aliased by supersampling)
    n = c.width
    yy, xx = np.ogrid[:n, :n]
    d = np.sqrt((yy - (iris["cy"] - box[1])) ** 2 + (xx - (iris["cx"] - box[0])) ** 2)
    m = np.clip(r - d, 0, 1)
    a = np.asarray(c).astype(np.float32)
    a[..., 3] = np.maximum(a[..., 3], 0) * m
    # inside the ring the iris is opaque (the white of the eye around it is not part of the icon)
    a[..., 3] = np.where(d < r - 1, np.maximum(a[..., 3], 255 * (d < iris["black_r"] - 2)), a[..., 3])
    disc = Image.fromarray(a.round().clip(0, 255).astype(np.uint8), "RGBA")
    inner = max(1, round(px * fill))
    disc = scaled(disc, inner, inner)
    out = Image.new("RGBA", (px, px), (0, 0, 0, 0) if bg is None else bg + (255,))
    out.alpha_composite(disc, ((px - inner) // 2, (px - inner) // 2))
    return out


def webp_bytes(img):
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=88, method=6, alpha_quality=95)
    return buf.getvalue()


def png_bytes(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def ico_bytes(images):
    """An ICO of PNG images, each drawn at its own size."""
    import struct
    blobs = [(im.size[0], png_bytes(im)) for im in images]
    out = struct.pack("<HHH", 0, 1, len(blobs))
    offset = 6 + 16 * len(blobs)
    entries, data = b"", b""
    for size, blob in blobs:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(blob), offset + len(data))
        data += blob
    return out + entries + data


def site_files():
    """{relative path under public: bytes} for everything the site uses."""
    m, iris = load()
    dark = recolour(m, iris)
    eye = eye_crop(dark, iris)
    files = {}
    for name, hgt in FULL_HEIGHTS.items():
        for k in DENSITIES:
            im = scaled(dark, height=hgt * k)
            suffix = "" if k == 1 else f"@{k}x"
            files[f"brand/logo-dark-{name}{suffix}.webp"] = webp_bytes(im)
            files[f"brand/logo-dark-{name}{suffix}.png"] = png_bytes(im)
    for name, hgt in EYE_HEIGHTS.items():
        for k in DENSITIES:
            im = scaled(eye, height=hgt * k)
            suffix = "" if k == 1 else f"@{k}x"
            files[f"brand/eye-dark-{name}{suffix}.webp"] = webp_bytes(im)
            files[f"brand/eye-dark-{name}{suffix}.png"] = png_bytes(im)
    icons = {px: iris_disc(m, iris, px, None, 1.0) for px in (16, 32, 48)}
    files["favicon.ico"] = ico_bytes([icons[16], icons[32], icons[48]])
    for px, im in icons.items():
        files[f"favicon-{px}.png"] = png_bytes(im)
    files["apple-touch-icon.png"] = png_bytes(iris_disc(m, iris, 180, DARK, 0.80))
    files["icon-192.png"] = png_bytes(iris_disc(m, iris, 192, DARK, 0.80))
    files["icon-512.png"] = png_bytes(iris_disc(m, iris, 512, DARK, 0.80))
    return files


def sizes():
    """The pixel sizes of the site's logo files at 1x (the components' width and height attributes)."""
    m, iris = load()
    eye = eye_crop(m, iris)
    out = {}
    for name, hgt in FULL_HEIGHTS.items():
        out[f"logo-{name}"] = (round(m.width * hgt / m.height), hgt)
    for name, hgt in EYE_HEIGHTS.items():
        out[f"eye-{name}"] = (round(eye.width * hgt / eye.height), hgt)
    return out


def main(argv):
    files = site_files()
    if "--check" in argv:
        bad = []
        for rel, data in files.items():
            p = os.path.join(PUBLIC, rel)
            if not os.path.exists(p):
                bad.append(f"{rel} is missing")
                continue
            if rel.endswith(".webp"):
                continue      # the WebP encoder is not byte stable across Pillow builds: its PNG twin is compared instead
            if open(p, "rb").read() != data:
                bad.append(f"{rel} differs from what assets/brand makes of it")
        for b in bad:
            print("FAIL", b)
        print("brand files: " + ("FAILED" if bad else f"ok ({len(files)} files)"))
        return 1 if bad else 0
    os.makedirs(BRAND, exist_ok=True)
    total = 0
    for rel, data in files.items():
        with open(os.path.join(PUBLIC, rel), "wb") as f:
            f.write(data)
        total += len(data)
    print(f"wrote {len(files)} files, {total} bytes; sizes at 1x: {sizes()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
