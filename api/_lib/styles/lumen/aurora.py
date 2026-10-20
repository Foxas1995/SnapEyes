# -*- coding: utf-8 -*-
"""AURORA (the light family, dramatic): a crown of northern light round the iris. Two veils of soft curtains stand on the limb and rise outward like the
auroral oval seen from above: the rays are broad and feathered (never hairlines: that is Radiance), the height of the veil undulates with the angle (folds),
the rays lean a little as they climb, and the colour runs from the eye's own light colour at the foot to its partner hue at the tip (the eye's hue turned 90
degrees toward violet for cool eyes, 81 degrees toward rose for warm ones, toward cyan for greens); the partner share changes slowly round the circle, so one
side of the crown is bluer or warmer than the other. The crown dies out into a dark sky between 0.31 and 0.50 S from the centre of the iris (the laboratory's veils
ran to the canvas edge, so the picture read as a lit square with a frame: a crown of soft two coloured curtains with dark corners is also what tells it apart from
Radiance's thin rays out of a dark moat). The ground is the eye's own deep tone with a few tiny stars; a soft bloom of the eye's colour sits on the limb.

Drawn in polar coordinates round the disc on the reduced grid (1536 cells on the long side at most: the rays are feathered, a 4096 master is the preview drawn
on a grid three times coarser than its pixels) from 1-D tables of 8192 samples (the ray noise, periodic round the circle) and a few harmonics (the folds); brought
up in 256 row bands. The iris is not touched: the veils start at the limb (1.010 R) and the iris is pasted over everything. All sizes are in R and S units.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..matter import ParticleLayer
from ..singles import kit as K
from . import common as CM

F32 = np.float32
TWO_PI = 2.0 * math.pi
AP = {
    "veils": (                          # (height e-fold R, strength, lean R-deg per R, partner share, ray cells (periodic bases of the ray noise))
        (0.56, 1.25, 22.0, 0.85, (9, 36)),
        (1.00, 0.85, -14.0, 1.00, (5, 20)),
    ),
    "fold": 0.52,                       # how much the veils' height varies round the circle (0 none)
    "contrast": 2.6,                    # the rays' contrast (power of the 0..1 noise): visible curtains, never a smooth glow
    "ground": (0.10, 0.012),            # the tonal ground, centre and corner shares of the eye's deep tone
    "stars": (110, 170),
    "bloom": (0.26, 0.060, 0.05),       # soft bloom on the limb: strength, e-fold (R), weight of the wide body
    "turn": 90.0,                       # degrees the partner hue is turned from the eye's hue (the laboratory's 56: the tips now read as a second colour)
    "start": 0.010,                     # the veils start this far (R) outside the limb
    "fade": (0.31, 0.50),               # the veils die out between these distances from the centre of the iris (shares of S): a crown with a dark sky
                                        # round it, never a lit square with a frame at the canvas edge
    "grid": 1536,                       # cells of the veils' grid on the long side at most (a 4096 master: a 1366 grid, factor 3)
    "grain": 0.016,                     # the tooth of a photographic print on the light (std of the noise at v = 1, display units; 0 none)
}


def _noise1d(rnd, n, base, octaves, gain):
    v = C.periodic_fbm1d(n, rnd, octaves, base, gain).astype(np.float64)
    v = (v - v.min()) / max(float(v.max() - v.min()), 1e-9)
    return v.astype(F32)


def _lookup(tab, th):
    """Linear lookup of a periodic table (len n over 0..2 pi) at angles th (radians, any shape)."""
    n = len(tab)
    p = (np.asarray(th, F32) % F32(TWO_PI)) * F32(n / TWO_PI)
    i0 = np.floor(p).astype(np.int32)
    w = p - i0
    return tab[i0 % n] * (1.0 - w) + tab[(i0 + 1) % n] * w


def partner_colour(iris, stp, turn):
    """The partner light colour of the eye: its mid colour turned toward violet (cool eyes), orange (warm ones) or cyan (greens), same lightness."""
    h = float(iris.stats["h"])
    Lm, Cm, hm = C.lch(CM.mean_colour(stp, 1))
    if 95.0 <= h <= 175.0:
        dh = turn * 0.9                                   # greens turn toward cyan
    elif 175.0 < h < 345.0:
        dh = turn                                          # blues and greys toward violet
    else:
        dh = -turn * 0.9                                   # browns and ambers toward orange and rose
    c = float(np.clip(Cm * 1.25, 28.0, 66.0))
    return C.from_lch(float(Lm) - 2.0, c, (float(hm) + dh) % 360.0).astype(F32)


def fx_aurora(cv, ctx):
    o = dict(AP)
    o.update(ctx.opts.get("aurora", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    stp = CM.stops(iris, white=0.30)
    mid_c = CM.mean_colour(stp, 1)
    hot_c = CM.mean_colour(stp, 2)
    part_c = partner_colour(iris, stp, float(o["turn"]))
    rnd = ctx.rand("aurora")
    N = 8192
    veils = []
    for (hh, st, lean, pshare, cells) in o["veils"]:
        ray = 0.60 * _noise1d(rnd, N, cells[0], 3, 0.55) + 0.40 * _noise1d(rnd, N, cells[1], 3, 0.6)
        ray = np.clip((ray - 0.15) / 0.85, 0.0, 1.0) ** float(o["contrast"])
        ph = rnd.uniform(4) * TWO_PI
        veils.append({"hh": hh, "st": st, "lean": math.radians(lean), "ps": pshare, "ray": ray.astype(F32), "ph": ph})
    hue_ph = float(rnd.uniform() * TWO_PI)
    env = _noise1d(rnd, N, 4, 2, 0.5)
    fade = CM.fades_for(ctx)
    # ---- the tonal ground (the paper: no fade)
    fg = CM.grid_factor(W, H)
    gg = C.Grid(W, H, fg)
    CM.screen_grid(cv, CM.ground_grid(gg, d.cx, d.cy, CM.tone(stp, o["ground"][0]), CM.tone(stp, o["ground"][1])), fg, "add")
    # ---- the veils on the reduced grid
    f = CM.grid_factor(W, H, o["grid"])
    g = C.Grid(W, H, f)
    gx0, gy0, gx1, gy1 = g.box(d.cx, d.cy, 3.1 * R)
    light = np.zeros((g.h, g.w, 3), F32)
    fold = float(o["fold"])
    start = float(o["start"])
    fa, fb = float(o["fade"][0]) * S / R, float(o["fade"][1]) * S / R                  # the fade, in R units
    col_low = (hot_c * 0.18 + mid_c * 0.82)[None, None, :]
    for ga in range(gy0, gy1, 128):
        gb = min(gy1, ga + 128)
        rho, th = g.polar(d.cx, d.cy, R, 1.0, (gx0, ga, gx1, gb))
        rho, th = rho.astype(F32), th.astype(F32)
        edge = F32(1.0) - CM.smooth((rho - F32(fa)) / F32(fb - fa))                        # the crown fades out into a dark sky before the canvas edge
        out = (rho > 1.0 + start - 0.02)
        lt = np.zeros(rho.shape + (3,), F32)
        e_amp = (0.55 + 0.45 * _lookup(env, th)).astype(F32)
        # the partner share changes slowly round the circle: one side of the crown is bluer (or warmer) than the other
        pcirc = (0.5 + 0.5 * np.sin(th + hue_ph)).astype(F32)
        for v in veils:
            p = v["ph"]
            e = np.maximum(rho - F32(1.0 + start), F32(0.0))
            hgt = (v["hh"] * (1.0 + fold * (0.50 * np.sin(2.0 * th + p[0]) + 0.32 * np.sin(3.0 * th + p[1]) + 0.18 * np.sin(5.0 * th + p[2])))).astype(F32)
            ray = _lookup(v["ray"], th + F32(v["lean"]) * e)                                 # the rays lean as they climb
            rise = CM.smooth(e / F32(0.035))
            hh_ = np.maximum(hgt, F32(0.05))
            prof = np.exp(-(e / hh_) ** F32(1.15))
            body = F32(0.30) + F32(0.70) * ray * (F32(0.45) + F32(0.55) * CM.smooth(e / F32(0.12)))   # solid at the foot, broken into rays higher up
            I = v["st"] * rise * prof * body * e_amp * edge
            t = np.clip(e / (F32(1.7) * hh_), 0.0, 1.0)
            share = np.clip(v["ps"] * (F32(0.35) + F32(1.1) * pcirc) * (F32(0.25) + t) * F32(1.5), 0.0, 1.0)[..., None]
            col = col_low * (1.0 - share) + part_c[None, None, :] * share
            foot = np.exp(-e / F32(0.05))[..., None]
            col = col * (1.0 - 0.30 * foot) + hot_c[None, None, :] * (0.30 * foot)
            lt += (I[..., None] * col).astype(F32)
        lt *= out[..., None]
        light[ga:gb, gx0:gx1] = lt
    CM.screen_grid(cv, light, f, "screen", fade)
    del light
    # ---- a soft bloom on the limb (the 512 grid) and the stars
    gb_ = C.Grid(W, H, fg)
    bx0, by0, bx1, by1 = gb_.box(d.cx, d.cy, 2.4 * R)
    rho, th = gb_.polar(d.cx, d.cy, R, 1.0, (bx0, by0, bx1, by1))
    e = np.maximum(rho - 1.0, 0.0)
    bk, bl, bw = o["bloom"]
    I = (bk * np.exp(-e / bl) + bw * np.exp(-e / 0.45)) * CM.smooth((rho - 0.985) / 0.03) * (0.6 + 0.4 * CM.smooth((rho - 1.0) / 0.08))
    lvl = np.clip(I / 0.9, 0.0, 1.0)
    glow = np.zeros((gb_.h, gb_.w, 3), F32)
    glow[by0:by1, bx0:bx1] = CM.ramp3(stp, th, lvl) * I[..., None]
    CM.screen_grid(cv, glow, fg, "screen", fade)
    del glow
    rs = ctx.rand("aurora_stars")
    ns = int(o["stars"][0] + (o["stars"][1] - o["stars"][0]) * float(rs.uniform()))
    sx, sy = rs.uniform(ns) * W, rs.uniform(ns) * H
    keep = np.hypot(sx - d.cx, sy - d.cy) > 2.0 * R
    sa = 0.05 + 0.20 * rs.uniform(ns) ** 2.2
    sz = (0.0004 + 0.0005 * rs.uniform(ns)) * S
    cool = C.mix(C.rgb01("#DCE6FF")[None, :], C.rgb01("#FFF2E2")[None, :], rs.uniform(ns)[:, None])
    layer = ParticleLayer()
    layer.splat(sx[keep], sy[keep], sz[keep], cool[keep], sa[keep], min_sigma=0.5)
    layer.flush(cv, fades=(lambda vv, r0: K.wall_fade(vv, ctx, y0=r0), lambda vv, r0: K.text_fade(vv, ctx, y0=r0)))
    if o["grain"]:
        CM.grain(cv, ctx.rand("aurora_grain"), o["grain"])
    ctx.log["aurora"] = {"class": iris.cls, "partner_rgb": [round(float(v), 3) for v in part_c], "factor": f}
