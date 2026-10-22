# -*- coding: utf-8 -*-
"""The share cards of the landing page (the og:image of /?lang=de, /?lang=lt and /?lang=hu).

The English card, public/assets/atelier/og-founder-eye.jpg (1200 x 630, the founder's own iris on the left, the brand and the
words on the right, a caption under the eye), was made by hand. A German, Lithuanian or Hungarian visitor who shares the page
used to get that card with English words on it. This script makes the other three from the English card: the eye (the left half and
everything that is not text) is the English card's own pixels, only the words are drawn again, in the site's own fonts
(public/assets/atelier/fonts: Cinzel for the brand and the headline, Plus Jakarta Sans for the rest) with the sizes, weights, tracking
and places that were measured on the English card (the parity check below proves the geometry: the English card, drawn again by
this very code, differs from the committed one by a mean of a few grey levels in the text areas).

The words are the page's own: the headline is the landing's hero title of the language (src/landing/copy/<lang>.json hero.title,
without its full stop), the line under it the first line of hero.micro, the brand line is the brand (SnapEyes, Private Atelier, the
same in every language); only the caption under the eye is new text (src/landing/shell/share.json, with the alt text of the image).

    python scripts/make_og_cards.py              write og-founder-eye-de.jpg, -lt.jpg and -hu.jpg next to the English card
    python scripts/make_og_cards.py --check      draw them again and compare with the committed files (what check:langheads runs)
    python scripts/make_og_cards.py --parity     draw the English card again and compare it with the committed one

Needs Pillow and fontTools (with brotli, to read the woff2 fonts). Each card stays under 150 kB (the check says so)."""
import io, json, os, sys, tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATELIER = os.path.join(ROOT, "public", "assets", "atelier")
COPY = os.path.join(ROOT, "src", "landing", "copy")
SHARE = os.path.join(ROOT, "src", "landing", "shell", "share.json")
LANGS = ("de", "lt", "hu")
MAX_BYTES = 150_000
QUALITY = 88

# What the English card holds, measured on it (see the module text): the pen origin, the baseline, the font, the size, the weight and the
# tracking (in em) of each block, and its colour. The right column starts at x 640; the caption is centred under the eye (x 319).
GOLD = (245, 197, 66)
BRAND = dict(font="cinzel-var", size=58, wght=700, track=0.12, x=640.0, base=205, fill=(247, 197, 72))
TAG = dict(font="plus-jakarta-sans-var", size=17, wght=600, track=0.36, x=642.0, base=250, fill=(172, 172, 178))
RULE = dict(x0=642, x1=722, y0=292, y1=293, fill=GOLD)
HEAD = dict(font="cinzel-var", size=38, wght=600, track=0.0, x=639.5, base=356, pitch=52, fill=(240, 243, 250), max_width=520)
SUB = dict(font="plus-jakarta-sans-var", size=21, wght=400, track=0.0, x=641.5, gap=62, fill=(165, 165, 169))   # gap: from the last headline baseline
CAP = dict(font="plus-jakarta-sans-var", size=20, wght=500, track=0.0, cx=319.0, base=588, fill=(224, 224, 228))
EN_CARD = dict(headline=["Precision Iris Art", "from Your Smartphone"], sub="Free watermarked preview",
               caption="Mantas, founder - photographed at home with a phone")   # the English card's own words (a spaced hyphen: the card is not a text of the site)
CLEAR = [(600, 120, 1200, 520), (0, 556, 700, 612)]    # the areas of the English card that hold words: painted black before the new words go on (the card's background is black)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Fonts:
    """The two site fonts as TrueType files in a throw-away folder (Pillow cannot read woff2), one FreeTypeFont per size and weight."""
    def __init__(self):
        self.dir = tempfile.TemporaryDirectory(prefix="og_fonts_")
        self.cache = {}

    def get(self, name, size, wght):
        key = (name, size, wght)
        if key not in self.cache:
            ttf = os.path.join(self.dir.name, name + ".ttf")
            if not os.path.exists(ttf):
                t = TTFont(os.path.join(ATELIER, "fonts", name + ".woff2"))
                t.flavor = None
                t.save(ttf)
            f = ImageFont.truetype(ttf, size)
            f.set_variation_by_axes([wght])
            self.cache[key] = f
        return self.cache[key]

    def close(self):
        self.cache.clear()
        self.dir.cleanup()


def width(text, font, track):
    return sum(font.getlength(ch) + track for ch in text) - (track if text else 0)


def put(img, text, font, x, base, track, fill):
    """The text on the card with its pen origin at x and its baseline at base, letter by letter when it is tracked."""
    d = ImageDraw.Draw(img)
    if not track:
        d.text((x, base), text, font=font, fill=fill, anchor="ls")
        return
    for ch in text:
        d.text((x, base), ch, font=font, fill=fill, anchor="ls")
        x += font.getlength(ch) + track


def wrap(text, font, limit):
    """The fewest lines of at most limit pixels (a single longer word stays on its line), broken where the longest line is shortest:
    "Ihre echte Iris, / als Kunstwerk", not "Ihre echte Iris, als / Kunstwerk"."""
    ws = text.split()
    lines, cur = [], ""
    for word in ws:
        trial = (cur + " " + word).strip()
        if cur and width(trial, font, 0) > limit:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines = lines + [cur] if cur else lines
    n = len(lines)
    best = None
    def split(i, left, acc):
        nonlocal best
        if left == 1:
            parts = acc + [" ".join(ws[i:])]
            w = max(width(p, font, 0) for p in parts)
            if w <= limit and (best is None or w < best[0]):
                best = (w, parts)
            return
        for j in range(i + 1, len(ws) - left + 2):
            split(j, left - 1, acc + [" ".join(ws[i:j])])
    if n > 1:
        split(0, n, [])
    return best[1] if best else lines


def card(base_card, fonts, headline, sub, caption):
    """The English card with its words painted out and the given ones drawn in. headline: a list of lines, or a string that is wrapped."""
    img = base_card.copy()
    d = ImageDraw.Draw(img)
    for box in CLEAR:
        d.rectangle(box, fill=(0, 0, 0))
    hf = fonts.get(HEAD["font"], HEAD["size"], HEAD["wght"])
    lines = headline if isinstance(headline, list) else wrap(headline, hf, HEAD["max_width"])
    if len(lines) > 3:
        raise SystemExit(f"the headline needs {len(lines)} lines: {lines}")
    lift = (len(lines) - 2) * HEAD["pitch"] / 2          # the block keeps its optical centre when the headline has another number of lines
    shift = lambda y: round(y - lift)
    bf = fonts.get(BRAND["font"], BRAND["size"], BRAND["wght"])
    put(img, "SNAPEYES", bf, BRAND["x"], shift(BRAND["base"]), BRAND["track"] * BRAND["size"], BRAND["fill"])
    # no brand line under SNAPEYES since 2026-10-22: the owner asked what "Private Atelier" means; the site and the cards say SnapEyes alone
    d.rectangle((RULE["x0"], shift(RULE["y0"]), RULE["x1"], shift(RULE["y1"])), fill=RULE["fill"])
    base = HEAD["base"]
    for i, line in enumerate(lines):
        put(img, line, hf, HEAD["x"], shift(base + i * HEAD["pitch"]), 0, HEAD["fill"])
    sf = fonts.get(SUB["font"], SUB["size"], SUB["wght"])
    put(img, sub, sf, SUB["x"], shift(base + (len(lines) - 1) * HEAD["pitch"] + SUB["gap"]), 0, SUB["fill"])
    cf = fonts.get(CAP["font"], CAP["size"], CAP["wght"])
    put(img, caption, cf, CAP["cx"] - width(caption, cf, 0) / 2, CAP["base"], 0, CAP["fill"])
    return img


def words(lang):
    """The card's words of a language: the page's own hero title and first micro line, and the caption of share.json."""
    copy = read_json(os.path.join(COPY, lang + ".json"))
    return dict(headline=copy["hero"]["title"].rstrip(". "), sub=copy["hero"]["micro"][0], caption=read_json(SHARE)[lang]["caption"])


def encode(img):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True, subsampling=0)
    return buf.getvalue()


def text_diff(a, b):
    """Mean absolute grey-level difference of two cards inside the text areas, after a blur of 1.5 px (a letter drawn half a pixel
    from where Chrome drew it is the same letter; a wrong size, weight, tracking or place is not)."""
    x = np.asarray(a.convert("L").filter(ImageFilter.GaussianBlur(1.5))).astype(float)
    y = np.asarray(b.convert("L").filter(ImageFilter.GaussianBlur(1.5))).astype(float)
    return max(float(np.abs(x[y0:y1, x0:x1] - y[y0:y1, x0:x1]).mean()) for (x0, y0, x1, y1) in CLEAR)


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")      # the words are Lithuanian and Hungarian: a Windows console is not UTF-8 by itself
    mode = "--check" if "--check" in argv else "--parity" if "--parity" in argv else "--write"
    en_path = os.path.join(ATELIER, "og-founder-eye.jpg")
    base = Image.open(en_path).convert("RGB")
    assert base.size == (1200, 630), base.size
    fonts = Fonts()
    problems = []
    try:
        if mode == "--parity":
            again = card(base, fonts, EN_CARD["headline"], EN_CARD["sub"], EN_CARD["caption"])
            d = text_diff(again, base)
            print(f"English card drawn again: mean grey difference in the text areas {d:.2f} (a text area of the original against the same area redrawn)")
            again.save(os.path.join(os.environ.get("OG_OUT", tempfile.gettempdir()), "og_en_redrawn.jpg"), quality=90)
            return 0 if d < 3.0 else 1
        if mode == "--write":
            # the English card is drawn again from itself with the same words and without the brand line (the area is painted out by CLEAR)
            en = encode(card(base, fonts, EN_CARD["headline"], EN_CARD["sub"], EN_CARD["caption"]))
            with open(en_path, "wb") as f:
                f.write(en)
            print(f"{os.path.basename(en_path)}: {len(en)} bytes  (English, drawn again without the brand line)")
            base = Image.open(en_path).convert("RGB")     # the other cards are drawn from the card as it is now on disk, as --check draws them
        for lang in LANGS:
            w = words(lang)
            img = card(base, fonts, w["headline"], w["sub"], w["caption"])
            data = encode(img)
            path = os.path.join(ATELIER, f"og-founder-eye-{lang}.jpg")
            if mode == "--write":
                with open(path, "wb") as f:
                    f.write(data)
                print(f"{os.path.basename(path)}: {len(data)} bytes  {w['headline']!r} / {w['sub']!r} / {w['caption']!r}")
                continue
            if not os.path.exists(path):
                problems.append(f"{os.path.basename(path)} is missing (python scripts/make_og_cards.py)")
                continue
            have = Image.open(path).convert("RGB")
            if have.size != (1200, 630):
                problems.append(f"{os.path.basename(path)}: {have.size[0]}x{have.size[1]}, not 1200x630")
            if os.path.getsize(path) > MAX_BYTES:
                problems.append(f"{os.path.basename(path)}: {os.path.getsize(path)} bytes, over {MAX_BYTES}")
            x = np.asarray(have).astype(float)
            y = np.asarray(Image.open(io.BytesIO(data)).convert("RGB")).astype(float)
            if x.shape != y.shape or float(np.abs(x - y).mean()) > 0.6:
                problems.append(f"{os.path.basename(path)} is not what share.json and the copy make of it (mean difference {float(np.abs(x - y).mean()):.2f}): run python scripts/make_og_cards.py")
        for p in problems:
            print("FAIL", p)
        if mode == "--check":
            print("og cards: " + ("FAILED" if problems else "ok (3 cards, 1200x630, under 150 kB, the words of the page)"))
        return 1 if problems else 0
    finally:
        fonts.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
