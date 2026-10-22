"""The round thumbnails of the sphere and ring prototypes (src/lab/sphere/img), made from the artworks the site already publishes.

    python scripts/lab/sphere/make_thumbs.py            (from the repository root)

Every picture is an existing artwork of public/assets (the landing's art tiles and the style pictures of /try), nothing new is drawn:
  * a one-eye artwork (square) is used whole: the page clips it to a circle;
  * a pair or a family artwork (3:2) is set into the circle: its sides are trimmed a little, the strips above and below are filled
    with the artwork's own edge, stretched and darkened, so the circle has no hard line;
  * outside the circle the square is black (the page never shows it; it costs nothing to store).
Three widths: 160 and 240 px for the discs, 480 px for the one in front.
The selection follows the owner's rule for public samples (2026-10-20): no eye with eyelid skin or lashes over the iris, no very large pupil,
and in a pair or a family no pupil much larger than the others (so the grey example eye, pupil 0.42 of the iris, and the five and six eye
families with the red eye are not used).
"""
import ast
import glob
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ART = os.path.join(ROOT, 'public', 'assets', 'landing', 'art')
ATELIER = os.path.join(ROOT, 'public', 'assets', 'atelier')
OUT = os.path.join(ROOT, 'src', 'lab', 'sphere', 'img')
SIZES = {160: 72, 240: 74, 480: 80}   # width: WebP quality
WORK = 960


def art(name):
    """The 900 px file of a landing art tile (its name carries a content hash)."""
    hits = glob.glob(os.path.join(ART, f'{name}_900.*.webp'))
    if len(hits) != 1:
        sys.exit(f'art {name}: {hits}')
    return hits[0]


def registry():
    """The styles of api/_lib/styles_registry.py (the one place that writes style ids and slugs; read here, never written)."""
    path = os.path.join(ROOT, 'api', '_lib', 'styles_registry.py')
    for node in ast.parse(open(path, encoding='utf-8').read()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'STYLES':
            return ast.literal_eval(node.value)
    sys.exit('no STYLES in the registry')


STYLES = registry()


def atelier(name, group):
    """The 800 px picture of /try's style picker for the style of this name (style-<slug>-800.webp: the slug is the registry's)."""
    hits = [v['slug'] for v in STYLES.values() if v['name'] == name and v['group'] == group and v['stage'] != 'retired']
    if len(hits) != 1:
        sys.exit(f'atelier {name}: {hits}')
    return os.path.join(ATELIER, f'style-{hits[0]}-800.webp'), hits[0].replace('-', '_')


# id: (source, kind, fit): a wide picture shows `fit` of its width in the circle; a square one is scaled by `fit` (1: whole, the corners cut)
# (the yellow green and brown example eyes of Celestial Gold, the brown ones of Universe and Clean Iris and the second Collision Infinity pair are
# left out: 32 artworks fill the globe, and those add no new look)
ITEMS = {}
for design, eyes in (('radiance', 'own yg br'), ('powder', 'own yg br'), ('universe', 'own yg'), ('splash', 'own yg br'), ('clean', 'own yg'), ('gold', 'own')):
    for eye in eyes.split():
        ITEMS[f'{design}_{eye}'] = (art(f'{design}_{eye}'), 'square', 1.0)
# the five newer one-eye styles exist only as /try's pictures, in our own eye: <slug>_own like the landing's own-eye tiles
for name in ('Halo', 'Sparks', 'Aurora', 'Nebula', 'Supernova'):
    src, key = atelier(name, 'solo')
    ITEMS[f'{key}_own'] = (src, 'square', 1.0)
for name in ('duo_infinity_by', 'duo_clean_by', 'duo_thread_by', 'duo_radiance_bd'):
    ITEMS[name] = (art(name), 'wide', 1.0)
ITEMS['fam_radiance_4'] = (art('fam_radiance_4'), 'wide', 0.95)
ITEMS['fam_trio'] = (art('fam_trio'), 'square', 1.0)
ITEMS['fam_orbit_4'] = (art('fam_orbit_4'), 'square', 1.0)
ITEMS['fam_circle_4'] = (art('fam_circle_4'), 'square', 0.92)
for name, group, fit in (('Kiss Collision', 'duo', 1.0), ('Nebula Duo', 'duo', 1.0), ('Supernova Duo', 'duo', 1.0), ('Nebula Family', 'grp', 0.95), ('Supernova Family', 'grp', 0.95)):
    src, key = atelier(name, group)
    ITEMS[key] = (src, 'wide', fit)


def circle_mask(n, feather=0.0):
    m = Image.new('L', (n * 4, n * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, n * 4 - 1, n * 4 - 1), fill=255)
    m = m.resize((n, n), Image.LANCZOS)
    return m.filter(ImageFilter.GaussianBlur(feather)) if feather else m


def square(src, kind, side):
    im = Image.open(src).convert('RGB')
    w, h = im.size
    if kind == 'square':
        if side >= 1:
            return im.resize((WORK, WORK), Image.LANCZOS)
        inner = round(WORK * side)
        canvas = Image.new('RGB', (WORK, WORK), im.getpixel((2, 2)))
        canvas.paste(im.resize((inner, inner), Image.LANCZOS), ((WORK - inner) // 2, (WORK - inner) // 2))
        return canvas
    # a wide picture: the circle shows `side` of its width; the picture is scaled to that, centred, and the strips above and below are
    # its own top and bottom rows stretched, blurred and darkened, blended in with a soft edge
    scale = WORK / (w * side)
    pw, ph = round(w * scale), round(h * scale)
    pic = im.resize((pw, ph), Image.LANCZOS)
    left = (pw - WORK) // 2
    pic = pic.crop((left, 0, left + WORK, ph))
    top = (WORK - ph) // 2
    canvas = Image.new('RGB', (WORK, WORK), (0, 0, 0))
    if top > 0:
        band = max(8, ph // 10)
        up = pic.crop((0, 0, WORK, band)).resize((WORK, top + band), Image.BILINEAR).filter(ImageFilter.GaussianBlur(18))
        down = pic.crop((0, ph - band, WORK, ph)).resize((WORK, top + band), Image.BILINEAR).filter(ImageFilter.GaussianBlur(18))
        dark = lambda x: Image.eval(x, lambda v: int(v * 0.55))
        canvas.paste(dark(up), (0, 0))
        canvas.paste(dark(down), (0, WORK - top - band))
        # the picture over the fill with a soft top and bottom edge
        fade = Image.new('L', (WORK, ph), 255)
        d = ImageDraw.Draw(fade)
        ramp = max(6, ph // 9)
        for y in range(ramp):
            a = int(255 * (y + 1) / ramp)
            d.line([(0, y), (WORK, y)], fill=a)
            d.line([(0, ph - 1 - y), (WORK, ph - 1 - y)], fill=a)
        canvas.paste(pic, (0, top), fade)
    else:
        canvas.paste(pic, (0, top))
    return canvas


def finish(sq):
    """Black outside the circle, and a quiet darkening of the circle's outer rim (the page draws the bezel)."""
    n = sq.size[0]
    vign = Image.new('L', (n, n), 0)
    d = ImageDraw.Draw(vign)
    steps = 40
    for i in range(steps):
        r = n / 2 * (1 - 0.10 * i / steps)
        a = int(255 * (1 - (i + 1) / steps) * 0.35)
        d.ellipse((n / 2 - r, n / 2 - r, n / 2 + r, n / 2 + r), fill=a)
    black = Image.new('RGB', (n, n), (0, 0, 0))
    inner = Image.composite(black, sq, vign.filter(ImageFilter.GaussianBlur(n / 120)))
    return Image.composite(inner, black, circle_mask(n))


def main():
    os.makedirs(OUT, exist_ok=True)
    total = {k: 0 for k in SIZES}
    for key, (src, kind, side) in ITEMS.items():
        big = finish(square(src, kind, side))
        for px, q in SIZES.items():
            path = os.path.join(OUT, f'{key}-{px}.webp')
            big.resize((px, px), Image.LANCZOS).save(path, 'WEBP', quality=q, method=6)
            total[px] += os.path.getsize(path)
    print(f'{len(ITEMS)} artworks ->', ', '.join(f'{px}px {total[px] / 1024:.0f} KB' for px in SIZES))


if __name__ == '__main__':
    main()
