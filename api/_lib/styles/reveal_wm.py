# -*- coding: utf-8 -*-
"""reveal_wm: the display copy with the watermark on ARCS (the art director's proposal, owner sign-off D14 outstanding; ported from the scratch
prototype's designs/presentation_wm.py, work package WP9). OFF: reveal.display_copy uses the repo's own tile unless style="arcs" is asked for, and
nothing asks for it until D14 is signed.

The repo's display copy (preview.display_image) draws the preview tile across the WHOLE square at 3.5 x its artwork strength, so the words run over
the pupil and the iris centre. This one puts the same words on three concentric arcs between 0.62 R and 0.92 R of the iris, at about 0.045 R cap
height, opacity 0.17 over a soft dark copy, and draws nothing inside 0.55 R (pupil, collarette) or outside the disc. The words are the engine's
(iris.WATERMARK_TEXT, the page's language); the font is the engine's Plus Jakarta Sans Bold. numpy and Pillow only.

Module rule of the v3 work: every module starts with the __future__ import (Vercel's default Python is 3.12)."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .. import iris as L

R_FRAC = 1.0 / (2.0 * 1.12)
SIDE = 800                      # the repo's DISPLAY_SIDE
ARC_RADII = (0.655, 0.785, 0.915)   # in iris radii: three arcs between 0.62 R and 0.92 R (centre line; the text is 0.06 R high)
ARC_FONT = 0.062                # font size in iris radii (cap height about 0.045 R)
ARC_ALPHA = 0.17                # opacity of the words (AD: 0.14 to 0.18)
ARC_SHADOW = 0.45               # the soft dark copy, as a share of the words' opacity
ARC_PHASE = (0.0, 0.33, 0.66)   # each arc starts a third of a repeat later, so the words do not line up radially
INNER_CLEAR = 0.55              # nothing is drawn inside this many iris radii


def _font(px):
    return L._font("PlusJakartaSans.ttf", int(px), "Bold")


def _strip(words, length, height, fsz, phase):
    """A horizontal strip (RGBA alpha only, L mode) of `words` repeated along `length` px, starting `phase` of a repeat in."""
    img = Image.new("L", (int(length), int(height)), 0)
    d = ImageDraw.Draw(img)
    f = _font(fsz)
    unit = words + "   "
    uw = d.textlength(unit, font=f)
    n = int(math.ceil(length / uw)) + 2
    x = -phase * uw
    for _ in range(n):
        d.text((x, height / 2.0), unit, font=f, fill=255, anchor="lm")
        x += uw
    return img


def arcs_alpha(side, words):
    """Float32 alpha (side x side, 0..1) of the words on the three arcs, centred on the iris centre."""
    R = R_FRAC * side
    yy, xx = np.mgrid[0:side, 0:side].astype(np.float32)
    dx, dy = xx + 0.5 - side / 2.0, yy + 0.5 - side / 2.0
    d = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)                                # 0 = 3 o'clock, clockwise on screen (y down)
    out = np.zeros((side, side), np.float32)
    h = ARC_FONT * R * 1.9                                 # strip height
    for rc, ph in zip(ARC_RADII, ARC_PHASE):
        rpx = rc * R
        circ = 2.0 * math.pi * rpx
        strip = np.asarray(_strip(words, circ, h, ARC_FONT * R, ph), np.float32) / 255.0
        Hs, Ws = strip.shape
        # u: arc length clockwise from the 9 o'clock so the text reads left to right over the top; v: outward is up (row 0)
        u = ((th + math.pi) % (2.0 * math.pi)) * rpx
        v = (Hs / 2.0) - (d - rpx)
        band = (np.abs(d - rpx) <= Hs / 2.0 - 1.0)
        if not band.any():
            continue
        ui, vi = u[band], v[band]
        x0 = np.floor(ui - 0.5).astype(np.int64)
        y0 = np.floor(vi - 0.5).astype(np.int64)
        fx, fy = (ui - 0.5 - x0).astype(np.float32), (vi - 0.5 - y0).astype(np.float32)
        x0m, x1m = np.mod(x0, Ws), np.mod(x0 + 1, Ws)
        y0c, y1c = np.clip(y0, 0, Hs - 1), np.clip(y0 + 1, 0, Hs - 1)
        val = (strip[y0c, x0m] * (1 - fx) * (1 - fy) + strip[y0c, x1m] * fx * (1 - fy)
               + strip[y1c, x0m] * (1 - fx) * fy + strip[y1c, x1m] * fx * fy)
        out[band] = np.maximum(out[band], val)
    rr = d / R
    out *= (rr >= INNER_CLEAR).astype(np.float32)
    return out


def display_copy_arcs(clean, lang=None, side=SIDE, alpha=ARC_ALPHA):
    """The display copy (PIL RGB, side x side) with the words on three arcs; nothing inside 0.55 R of the iris centre."""
    im = clean.convert("RGB")
    if im.size != (side, side):
        im = im.resize((side, side), Image.LANCZOS)
    words = L.WATERMARK_TEXT.get(lang or "en", L.WATERMARK_TEXT["en"])[0]
    a = arcs_alpha(side, words)
    base = np.asarray(im).astype(np.float32)
    # the soft dark copy, 1 px down and right, blurred 1 px: keeps the words legible on a pale iris
    sh = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)), np.float32) / 255.0
    sh = np.roll(np.roll(sh, 1, 0), 1, 1) * (alpha * ARC_SHADOW / max(alpha, 1e-6)) * alpha
    out = base * (1.0 - sh[..., None])
    out = out * (1.0 - (a * alpha)[..., None]) + 255.0 * (a * alpha)[..., None]
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))
