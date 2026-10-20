# -*- coding: utf-8 -*-
"""SPARKS (the light family, dramatic): sparks and soft lights lifting off the limb on a wind, as if the iris were a coal. Hundreds of small
sparks with comet tails (hot white heads that cool to the eye's own colour and then to its deep tone), thousands of glints, a few large out of focus
lights (bokeh) in front, and a warm bloom on the limb; denser and longer on the wind side, a quiet, dark lee. The colour of every spark is the eye's
own at the angle it left the limb (kit.ramp_stops logic through common.stops: copper for dark browns, a tinted silver for grey eyes), so a blue eye
throws blue sparks and a brown one amber ones. Particles only: no plate, no atlas, no cloud (that is Powder Burst).

Where the matter goes is matter.Emission (the prototype's own angular density with a wind, jets and an envelope), drawn through matter.ParticleLayer
(Gaussian stamps and comet streaks, banded, never a full size layer). All sizes are in R and S units and the counts do not depend on the canvas, so a
4096 master is the preview drawn finer. The iris is not touched: nothing is drawn inside 1.02 R and the disc is pasted over everything.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from .. import matter as M
from ..singles import kit as K
from . import common as CM

F32 = np.float32
TWO_PI = 2.0 * math.pi
SP = {
    "wind": (-70.0, -35.0),             # the wind's direction, a seeded angle in this range (deg, 0 = 3 o'clock, clockwise: negative is up)
    "sparks": 430, "glints": 1700, "bokeh": 38,
    "ground": (0.12, 0.012),            # the tonal ground, centre and corner shares of the eye's deep tone
    "bloom": (0.30, 0.070, 0.07),       # the limb's warm bloom: strength, e-fold (R), the wide body
    "len": (0.008, 0.078),              # streak length range in S
    "start": 0.020,                     # nothing is drawn nearer than this (R) to the limb
}


def fx_sparks(cv, ctx):
    o = dict(SP)
    o.update(ctx.opts.get("sparks", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    stp = CM.stops(iris, white=0.55)
    rnd = ctx.rand("sparks")
    wind = math.radians(o["wind"][0] + (o["wind"][1] - o["wind"][0]) * float(ctx.rand("sparks_wind").uniform()))
    wv = np.array([math.cos(wind), math.sin(wind)])
    fade = CM.fades_for(ctx)
    # ---- the tonal ground and the bloom of the limb, warmer on the wind side
    f = CM.grid_factor(W, H)
    g = C.Grid(W, H, f)
    CM.screen_grid(cv, CM.ground_grid(g, d.cx, d.cy, CM.tone(stp, o["ground"][0]), CM.tone(stp, o["ground"][1])), f, "add")      # the paper: no fade
    gx0, gy0, gx1, gy1 = g.box(d.cx, d.cy, 2.6 * R)
    rho, th = g.polar(d.cx, d.cy, R, 1.0, (gx0, gy0, gx1, gy1))
    e = np.maximum(rho - 1.0, 0.0)
    bk, bl, bw = o["bloom"]
    wside = 0.62 + 0.38 * np.maximum(np.cos(th - wind), -0.3)
    I = (bk * np.exp(-e / bl) + bw * np.exp(-e / 0.40)) * CM.smooth((rho - 0.985) / 0.03) * (0.5 + 0.5 * CM.smooth((rho - 1.0) / 0.08)) * wside
    lvl = np.clip(I / 0.9, 0.0, 1.0)
    glow = np.zeros((g.h, g.w, 3), F32)
    glow[gy0:gy1, gx0:gx1] = CM.ramp3(stp, th, lvl) * I[..., None]
    CM.screen_grid(cv, glow, f, "screen", fade)
    del glow
    # ---- where matter goes: the prototype's emission (wind, jets, lobes, an envelope)
    emis = M.Emission(ctx.rand("sparks_emis"), wind, b=1.15, n_jets=5, jet_share=0.22, lobes=3, lobe_amp=0.30, halo=1.0, plume=2.0, stretch=(0.85, 1.10))
    layer = M.ParticleLayer()
    start = float(o["start"])

    def place(n, l1, l2, tail, cap):
        t_, e_ = emis.sample(rnd, n, l1, l2, tail, cap=cap, over=4.0, min_e=start)
        m = len(t_)
        curl = rnd.normal(m, 0.0, 0.05) * (0.3 + e_)                               # a lateral wander that grows with the distance
        px = d.cx + (1.0 + e_) * R * np.cos(t_) + R * curl * (-np.sin(t_)) + wv[0] * 0.18 * R * e_
        py = d.cy + (1.0 + e_) * R * np.sin(t_) + R * curl * np.cos(t_) + wv[1] * 0.18 * R * e_
        return t_, e_, px, py

    # ---- 1. the sparks: comet streaks with hot heads
    t_, e_, px, py = place(int(o["sparks"]), 0.32, 0.85, 0.28, 1.0)
    m = len(t_)
    u = rnd.uniform(m)
    a = 0.14 + 0.86 * u ** 2.4
    a *= 1.0 + 1.1 * (rnd.uniform(m) < 0.025)                                       # a few heroes
    lvl = np.clip(0.15 + 0.85 * u ** 1.3 - 0.35 * np.clip(e_ / 2.0, 0, 1), 0.0, 1.0)
    col = CM.ramp3(stp, t_, lvl)
    vx = np.cos(t_) * 0.28 + wv[0] * 1.00
    vy = np.sin(t_) * 0.28 + wv[1] * 1.00
    nrm = np.hypot(vx, vy)
    vx, vy = vx / nrm, vy / nrm
    jit = rnd.normal(m, 0.0, 0.14)
    cj, sj = np.cos(jit), np.sin(jit)
    dx, dy = vx * cj - vy * sj, vx * sj + vy * cj
    ln_ = (o["len"][0] + (o["len"][1] - o["len"][0]) * (0.25 + 0.75 * u ** 1.2) * (0.6 + 0.4 * np.clip(e_ / 1.2, 0, 1))) * S
    cls_ = rnd.uniform(m)                                                          # three sizes of spark: many fine, some medium, a few bold
    for lo_, hi_, sg_, lk_ in ((0.0, 0.66, 0.00060, 0.85), (0.66, 0.92, 0.00115, 1.0), (0.92, 1.01, 0.00200, 1.25)):
        k_ = (cls_ >= lo_) & (cls_ < hi_)
        if k_.any():
            M.streaks(layer, px[k_], py[k_], dx[k_], dy[k_], ln_[k_] * lk_, col[k_], a[k_] * 0.9, sigma_px=sg_ * S)
    # ---- 2. the glints: tiny points, many, dim, everywhere the wind carries them
    t2, e2, px2, py2 = place(int(o["glints"]), 0.45, 1.1, 0.35, 1.0)
    m2 = len(t2)
    u2 = rnd.uniform(m2)
    a2 = 0.10 + 0.55 * u2 ** 2.6
    lv2 = np.clip(0.10 + 0.80 * u2 ** 1.4 - 0.2 * np.clip(e2 / 2.0, 0, 1), 0.0, 1.0)
    col2 = CM.ramp3(stp, t2, lv2)
    sg2 = (0.00045 + 0.00075 * rnd.uniform(m2) ** 2.0) * S
    layer.splat(px2, py2, sg2, col2, a2, min_sigma=0.5)
    layer.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0)))
    # ---- 3. the bokeh: large out of focus lights in front, additive, soft, a brighter rim
    nb = int(o["bokeh"])
    tb, eb, pxb, pyb = place(nb, 0.55, 1.2, 0.4, 1.0)
    mb = len(tb)
    rad = (0.012 + 0.040 * rnd.uniform(mb) ** 1.6) * S
    ab = 0.045 + 0.150 * rnd.uniform(mb) ** 1.8
    cb = CM.ramp3(stp, tb, np.clip(0.28 + 0.4 * rnd.uniform(mb), 0, 1))
    Hh, Ww = cv.shape[:2]
    for k in range(mb):
        r = float(rad[k])
        m_ = int(r * 1.35) + 3
        x0, y0 = int(round(pxb[k])) - m_, int(round(pyb[k])) - m_
        xa, ya, xb_, yb_ = max(0, x0), max(0, y0), min(Ww, x0 + 2 * m_ + 1), min(Hh, y0 + 2 * m_ + 1)
        if xa >= xb_ or ya >= yb_:
            continue
        gx = (np.arange(xa, xb_, dtype=F32) + F32(0.5 - pxb[k]))[None, :]
        gy = (np.arange(ya, yb_, dtype=F32) + F32(0.5 - pyb[k]))[:, None]
        rr = np.sqrt(gx * gx + gy * gy)
        soft = max(1.0, 0.16 * r)
        disc = np.clip((r - rr) / soft + 0.5, 0.0, 1.0)
        prof = 0.72 + 0.28 * CM.smooth((rr / r - 0.55) / 0.45)
        al = (disc * prof * F32(ab[k])).astype(F32)
        reg = cv[ya:yb_, xa:xb_]
        reg += al[..., None] * cb[k][None, None, :] * (1.0 - 0.0)
    ctx.log["sparks"] = {"class": iris.cls, "wind_deg": round(math.degrees(wind), 1), "n": [m, m2, mb]}
