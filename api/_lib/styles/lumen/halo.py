# -*- coding: utf-8 -*-
"""HALO (the light family, calm): the iris backlit. A soft bloom of the eye's own colour round the limb (pale at the rim, the eye's colour in the middle,
its deep tone in the tail), a faint optical ring further out, a breath of mist and of lopsidedness (one side has a little more light behind it) and a
deep tonal ground that is the eye's own dark shade, never pure grey. No ray, no particle, no line: the quietest of the looks, a Clean Iris with light behind it.

Drawn on the reduced grid (core.Grid, 512 cells on the long side at every size) and brought up in 256 row bands, so a 4096 master is the preview drawn
finer (the same numbers on the same grid) and no full size float layer exists. Only the hairline of the rim is drawn at full resolution, on its own
annulus.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from . import common as CM

F32 = np.float32
TWO_PI = 2.0 * math.pi
HP = {
    "len": (0.034, 0.17, 0.60),         # e-fold lengths of the bloom in R: a bright close rim, the body, a long tail
    "amp": (0.42, 0.60, 0.20),          # their weights
    "moat": 0.80,                       # the light at the limb is pulled down to this share and recovers by 1.08 R: the iris does not sit IN the glow
    "mist": 0.50,                       # depth of the mist on the body and the tail (0 none)
    "mist_cells": 3.0,                  # cells of the mist across the short side
    "ring": (1.70, 0.100, 0.040),       # the optical ring: radius (R), sigma (R), weight
    "ground": (0.36, 0.035),            # the tonal ground: centre and corner shares of the eye's deep tone
    "hair": (1.034, 0.0040, 0.10),      # the rim light: radius, sigma (R), weight
    "level": 1.30,                      # the light level that maps a bloom to the hot end of the ramp
    "white": 0.36,                      # how far the hot end of the ramp goes toward warm white (the rim stays coloured)
    "lobe": 0.10,                       # the lopsidedness of the bloom (0 none): one side of the iris has a little more light behind it
    "grain": 0.014,                     # the tooth of a photographic print on the glow (std of the noise at v = 1, display units; 0 none)
}


def fx_halo(cv, ctx):
    o = dict(HP)
    o.update(ctx.opts.get("halo", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    stp = CM.stops(iris, white=o["white"])
    f = CM.grid_factor(W, H)                              # the grid is 512 cells on the long side at every size: the master is the preview drawn finer
    g = C.Grid(W, H, f)
    # ---- the tonal ground: the eye's own deep tone, brightest behind the iris, nearly black in the corners (no fade: it is the paper, not matter)
    CM.screen_grid(cv, CM.ground_grid(g, d.cx, d.cy, CM.tone(stp, o["ground"][0]), CM.tone(stp, o["ground"][1])), f, "add")
    # ---- the bloom
    gx0, gy0, gx1, gy1 = g.box(d.cx, d.cy, 2.9 * R)
    rho, th = g.polar(d.cx, d.cy, R, 1.0, (gx0, gy0, gx1, gy1))
    e = np.maximum(rho - 1.0, 0.0)
    rise = CM.smooth((rho - 0.985) / 0.03)
    l1, l2, l3 = o["len"]
    a1, a2, a3 = o["amp"]
    nz = CM.smooth_noise(g.w, g.h, o["mist_cells"], ctx.rand("halo_mist"), 3, 0.55)[gy0:gy1, gx0:gx1]
    mist = (1.0 + o["mist"] * (nz - 0.5) * 2.0).astype(F32)
    I = (a1 * np.exp(-e / l1)).astype(F32) + (a2 * np.exp(-e / l2) + a3 * np.exp(-e / l3)).astype(F32) * mist
    # a breath of asymmetry: the light behind the iris is a little stronger on one side (a seeded lobe), so the bloom is never a perfect circle
    pr = ctx.rand("halo_lobe").uniform(2) * TWO_PI
    I = I * (1.0 + o["lobe"] * (np.cos(th - pr[0]) + 0.45 * np.cos(2.0 * th - pr[1]))).astype(F32)
    # the optical ring: a faint circle of the same colour, wider than the bloom, broken a little by the mist
    r0, rs, rw = o["ring"]
    I = I + (rw * np.exp(-0.5 * ((rho - r0) / rs) ** 2)).astype(F32) * (0.55 + 0.45 * mist)
    I = I * rise * (o["moat"] + (1.0 - o["moat"]) * CM.smooth((rho - 1.0) / 0.075)).astype(F32)
    lvl = np.clip(I / o["level"], 0.0, 1.0) ** 0.85
    light = np.zeros((g.h, g.w, 3), F32)
    light[gy0:gy1, gx0:gx1] = CM.ramp3(stp, th, lvl) * I[..., None]
    CM.screen_grid(cv, light, f, "screen", CM.fades_for(ctx))
    del light
    # ---- the rim light, a hairline at full resolution on its own annulus (never thinner than a pixel; the energy is kept)
    hr, hs, hw = o["hair"]
    s_px = max(hs, 0.45 / R)
    for ra, rb, x0, x1, rr, tt, m in CM.annulus(ctx, d, hr - 6.0 * s_px, hr + 6.0 * s_px):
        ln = (hw * (hs / s_px) * np.exp(-0.5 * ((rr[m] - hr) / s_px) ** 2)).astype(F32)
        col = CM.ramp3(stp, tt[m], np.full(ln.shape, 0.85, F32)) * ln[:, None]
        reg = cv[ra:rb, x0:x1]
        reg[m] += col
    if o["grain"]:
        CM.grain(cv, ctx.rand("halo_grain"), o["grain"])
    ctx.log["halo"] = {"class": iris.cls, "mid_rgb": [round(float(v), 3) for v in CM.mean_colour(stp, 1)], "factor": f}
