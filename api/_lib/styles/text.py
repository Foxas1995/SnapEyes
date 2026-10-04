# -*- coding: utf-8 -*-
"""styles.text: the customer's own words on an artwork, and nothing else. Owner rule: the studio writes nothing on the artwork; the
only text an artwork may carry is what the customer typed (names, a date, a family name), and every draw call is recorded in a log
that the run-time check T7 reads (selfcheck.t7_text): a style name, a brand, a slogan or a placeholder in that log fails the render.

What lives here
  limits and cleaning    NAME_MAX, NAMES_TOTAL_MAX, DATE_MAX, FAMILY_MAX; clean(), split_names() (a list, or the old string "Anna;Max"),
                         normalise_names(), lockup() (the names as one line: "ANNA · MAX · LINA")
  the font check         unsupported(text): the letters the artwork font cannot draw (a missing glyph would print as an empty box in a
                         delivered file), read from the font's own cmap table with no dependency; the page and checkout refuse such a name
  the drawers            draw_names(): the verbatim port of the singles drawer (names in Cinzel capitals, tracked 0.18 em, cap height
                         0.017 S; the date at 0.011 S, tracked 0.30 em, at 55 percent opacity), draw_line(): one centred tracked line (the
                         family name inside a ring of seven or eight eyes), both with the draw log

The collision and universe drawers (draw_names in collision.py and uni_engine.py) come with their engine packages; the three drawers are
merged here only in the clean-up package, under the goldens. A drawer is given a frame with W, H, S (canvas size and short side) and
text_y (the baseline of the first line, in px).
"""
from __future__ import annotations

import re
import struct
import unicodedata

from PIL import ImageDraw

from .. import iris as L
from . import core as C

NAME_MAX = 24            # characters in one name
NAMES_TOTAL_MAX = 200    # characters in all names of one order
DATE_MAX = 20
FAMILY_MAX = 24
NAMES_MAX = 8            # one name per eye
SEPARATOR = ";"          # the old wire form: one string, names joined by a semicolon

NAME_WARM = "#C9B8A0"
NAME_GOLD = "#C9A86A"
CAP_H = 0.017            # name cap height, share of S
DATE_H = 0.011
NAME_TRACK = 0.18        # em
DATE_TRACK = 0.30
LOCKUP_JOIN = " · "                 # middle dot, covered by both artwork fonts

_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202e\u2060-\u2064\ufeff]")
_SPACES = re.compile(r"\s+")


# ----------------------------------------------------------------------------- cleaning and limits
def clean(s):
    """One customer string as it is drawn: NFC, control and zero width characters out, runs of white space one space, trimmed."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFC", s)
    return _SPACES.sub(" ", _CONTROL.sub("", s)).strip()


def split_names(value):
    """The names of an order as a list: a list of strings, or the old wire string "Anna;Max" (a semicolon or a line break separates).
    Empty names are dropped; nothing is cut here (normalise_names checks the limits)."""
    if value is None:
        return []
    parts = value if isinstance(value, (list, tuple)) else re.split(r"[;\n]", str(value))
    return [n for n in (clean(p) for p in parts) if n]


def normalise_names(value, eyes=NAMES_MAX):
    """(names, problem): the cleaned list, and None or a code when it breaks a limit: too_many (more than the eyes or NAMES_MAX),
    name_long (a name over NAME_MAX characters), names_long (the total over NAMES_TOTAL_MAX), glyph (a letter the font cannot draw)."""
    names = split_names(value)
    if len(names) > min(int(eyes), NAMES_MAX):
        return names, "too_many"
    if any(len(n) > NAME_MAX for n in names):
        return names, "name_long"
    if sum(len(n) for n in names) > NAMES_TOTAL_MAX:
        return names, "names_long"
    if any(unsupported(n) for n in names):
        return names, "glyph"
    return names, None


def lockup(names):
    """The names as one line of the artwork: ANNA · MAX · LINA (upper case is the drawer's)."""
    return LOCKUP_JOIN.join(split_names(names))


# ----------------------------------------------------------------------------- what the font can draw
_COVER = C.BoundedCache(4)


def _cmap_codes(data):
    """The code points a TrueType font maps to a real glyph (not .notdef): the cmap table, subtable formats 4 and 12 (Windows Unicode
    and Unicode platform). Pure struct reading, no dependency."""
    num_tables = struct.unpack_from(">H", data, 4)[0]
    cmap = None
    for i in range(num_tables):
        tag, _chk, off, _ln = struct.unpack_from(">4sIII", data, 12 + 16 * i)
        if tag == b"cmap":
            cmap = off
            break
    if cmap is None:
        return frozenset()
    n_sub = struct.unpack_from(">H", data, cmap + 2)[0]
    best = None
    for i in range(n_sub):
        plat, enc, off = struct.unpack_from(">HHI", data, cmap + 4 + 8 * i)
        rank = {(3, 10): 3, (0, 4): 3, (0, 6): 3, (3, 1): 2, (0, 3): 2, (0, 0): 1, (0, 1): 1, (0, 2): 1}.get((plat, enc), 0)
        if rank and (best is None or rank > best[0]):
            best = (rank, cmap + off)
    if best is None:
        return frozenset()
    sub = best[1]
    fmt = struct.unpack_from(">H", data, sub)[0]
    codes = set()
    if fmt == 4:
        seg2 = struct.unpack_from(">H", data, sub + 6)[0]
        seg = seg2 // 2
        end_o, start_o = sub + 14, sub + 16 + seg2
        delta_o, range_o = start_o + seg2, start_o + 2 * seg2
        for s in range(seg):
            end = struct.unpack_from(">H", data, end_o + 2 * s)[0]
            start = struct.unpack_from(">H", data, start_o + 2 * s)[0]
            delta = struct.unpack_from(">h", data, delta_o + 2 * s)[0]
            ro = struct.unpack_from(">H", data, range_o + 2 * s)[0]
            for c in range(start, end + 1):
                if c == 0xFFFF:
                    continue
                if ro == 0:
                    g = (c + delta) & 0xFFFF
                else:
                    pos = range_o + 2 * s + ro + 2 * (c - start)
                    g = struct.unpack_from(">H", data, pos)[0] if pos + 2 <= len(data) else 0
                    g = (g + delta) & 0xFFFF if g else 0
                if g:
                    codes.add(c)
    elif fmt == 12:
        n_groups = struct.unpack_from(">I", data, sub + 12)[0]
        for g in range(n_groups):
            start, end, gid = struct.unpack_from(">III", data, sub + 16 + 12 * g)
            for c in range(start, end + 1):
                if gid + (c - start):
                    codes.add(c)
    return frozenset(codes)


def font_cover(name="Cinzel.ttf"):
    """The code points an artwork font draws (cached)."""
    got = _COVER.get(name)
    if got is None:
        import os
        with open(os.path.join(L.ASSETS, "fonts", name), "rb") as f:
            got = _COVER.put(name, _cmap_codes(f.read()))
    return got


def unsupported(text, font="Cinzel.ttf"):
    """The distinct characters of a customer string (as the drawer sets it: upper case) that the artwork font cannot draw, sorted.
    Spaces are always fine. [] means the string draws completely."""
    cover = font_cover(font)
    bad = {ch for ch in clean(text).upper() if not ch.isspace() and ord(ch) not in cover}
    return sorted(bad)


# ----------------------------------------------------------------------------- drawing
def _cap_font_px(font_name, weight, cap_px):
    f = L._font(font_name, 200, weight)
    b = f.getbbox("H")
    cap200 = b[3] - b[1]
    return max(4, int(round(200.0 * cap_px / max(cap200, 1))))


def _fit_width(d, text, font_name, weight, px, tracking, max_w):
    """px reduced until the tracked line fits max_w."""
    size = px
    while True:
        f = L._font(font_name, size, weight)
        w = d.textlength(text, font=f) + tracking * size * (len(text) - 1)
        if w <= max_w or size <= 5:
            return f, size, w
        size = max(5, min(size - 1, int(size * max_w / w)))


def _rgb(colour):
    return tuple(int(round(v)) for v in (C.rgb01(colour) * 255.0)) if isinstance(colour, str) else tuple(int(v) for v in colour)


def draw_names(img, frame, names="", date="", colour=NAME_WARM, log=None, iris_colour=None):
    """The customer's optional names (Cinzel caps, tracking 0.18 em, cap height 0.017 S) and date (0.011 S at tracking 0.3 em,
    55 % opacity), centred at the frame's baseline. Nothing else is ever drawn (test T7 reads the log). Returns the log."""
    log = [] if log is None else log
    names = clean(names)
    date = clean(date)
    if not names and not date:
        return log
    W, H, S = frame.W, frame.H, frame.S
    d = ImageDraw.Draw(img, "RGBA")
    col = _rgb(colour)
    max_w = 0.80 * W
    y = frame.text_y
    if names:
        txt = names.upper()
        px = _cap_font_px("Cinzel.ttf", "Regular", CAP_H * S)
        f, size, w = _fit_width(d, txt, "Cinzel.ttf", "Regular", px, NAME_TRACK, max_w)
        x = W / 2.0 - w / 2.0
        for i, ch in enumerate(txt):
            d.text((x, y), ch, font=f, fill=col + (255,), anchor="ls")
            x += d.textlength(txt[:i + 1], font=f) - d.textlength(txt[:i], font=f) + NAME_TRACK * size
        log.append({"kind": "names", "text": names, "px": size, "baseline": y})
        y += 0.030 * S + 0.0
    if date:
        txt = date.upper()
        px = _cap_font_px("Cinzel.ttf", "Regular", DATE_H * S)
        f, size, w = _fit_width(d, txt, "Cinzel.ttf", "Regular", px, DATE_TRACK, max_w)
        x = W / 2.0 - w / 2.0
        yy = y if names else frame.text_y
        for i, ch in enumerate(txt):
            d.text((x, yy), ch, font=f, fill=col + (int(255 * 0.55),), anchor="ls")
            x += d.textlength(txt[:i + 1], font=f) - d.textlength(txt[:i], font=f) + DATE_TRACK * size
        log.append({"kind": "date", "text": date, "px": size, "baseline": yy})
    return log


def draw_line(img, cx, baseline, text, S, kind="family", colour=NAME_WARM, max_w=None, cap=CAP_H, tracking=NAME_TRACK, log=None):
    """One centred, tracked line in Cinzel capitals at a baseline (the family name in the hollow of a ring of seven or eight eyes):
    cap height cap x S, shrunk until it fits max_w (default 0.80 of the canvas width). Returns the log."""
    log = [] if log is None else log
    text = clean(text)
    if not text:
        return log
    W = img.size[0]
    d = ImageDraw.Draw(img, "RGBA")
    col = _rgb(colour)
    txt = text.upper()
    px = _cap_font_px("Cinzel.ttf", "Regular", cap * S)
    f, size, w = _fit_width(d, txt, "Cinzel.ttf", "Regular", px, tracking, max_w if max_w else 0.80 * W)
    x = cx - w / 2.0
    for i, ch in enumerate(txt):
        d.text((x, baseline), ch, font=f, fill=col + (255,), anchor="ls")
        x += d.textlength(txt[:i + 1], font=f) - d.textlength(txt[:i], font=f) + tracking * size
    log.append({"kind": kind, "text": text, "px": size, "baseline": baseline})
    return log
