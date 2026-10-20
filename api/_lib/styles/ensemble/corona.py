# -*- coding: utf-8 -*-
"""styles.ensemble.corona: the even corona of ONE disc, the owner-approved Celestial Gold single's own arithmetic (singles/gold.py fx_gold, its corona section)
drawn round one iris of a picture that holds several: Family Orbit's hub. Ported from the laboratory of the pairs and families round (proto_pf/celestial.py
corona and gold_opts, 2026-10-20) without a change; the laboratory's gold pair and gold family looks are NOT here (the owner shelved them).

The corona is SAMPLED FROM the iris (its rim band) and drawn outside it, into the float canvas, before the iris is pasted: nothing touches an iris."""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..singles import gold as G
from ..singles import kit as K

F32 = np.float32
TWO_PI = 2.0 * math.pi


def gold_opts(ctx):
    """The Celestial Gold single's constants (singles/gold.py GP), with the look's own overrides (ctx.opts["gold"], the laboratory's)."""
    o = dict(G.GP)
    o.update(ctx.opts.get("gold", {}))
    return o


def corona(cv, ctx, d, iris, rnd, opts, strength=1.0, partners=(), soften=0.0):
    """Adds the even corona of one disc into cv (radius only: one amplitude, one colour from the rim band, an angular texture of harmonics 72 and above) and
    returns the colour of its corona (3,) 0..1. fx_gold's own arithmetic; the differences are `strength`, that nothing else is drawn and `partners` / `soften`: the
    directions (rad, screen) of neighbouring irises and how far (0..1) the ray texture is flattened within about 26 degrees of them."""
    W, H, R = ctx.W, ctx.H, d.R
    g = G.GILD.get(iris.cls, 0.55)
    if iris.cls == "own" and 170.0 <= iris.stats["h"] <= 280.0:
        g = max(g, 0.65)
    NA, NRS = 4096, 24
    ths = (np.arange(NA) + 0.5) * (TWO_PI / NA)
    rhos = np.linspace(0.86, 0.98, NRS)
    Pm = K.sample_disc(d, rhos[None, :] * np.ones((NA, 1)), ths[:, None] * np.ones((1, NRS))).mean(axis=1)
    med = np.median(Pm, axis=0).astype(np.float32)
    own = C.boost(med * 1.15, 1.3, 1.3)
    gm = G.gold_ramp(np.float32(0.62))
    own = C.mix(own, gm * (float(own.mean()) / max(float(gm.mean()), 1e-6)), float(opts["warm"]))

    def tex_noise():
        a_ = 0
        for lo, hi, w in opts["bands"]:
            a_ = a_ + float(w) * G.band_noise(NA, rnd, lo, hi)
        return (a_ / max(float(np.std(a_)), 1e-9)).astype(np.float32)
    lutA, lutB = np.ascontiguousarray(tex_noise()), np.ascontiguousarray(tex_noise())
    c0 = 1.0 + float(opts["gap"])
    col_lut, Ib = G._radial_colour_lut(opts, g, own)
    NL = len(Ib)
    umax = 1.25
    s_a, s_l = float(opts["s_amp"]), float(opts["s_len"])
    tap0, tapL = float(opts["taper"][0]), float(opts["taper"][1])
    morph = float(opts["morph"])
    fl, fl_soft = float(opts["floor"]), float(opts["floor_soft"])
    reach = 1.56 * R
    x0, y0 = max(0, int(d.cx - reach)), max(0, int(d.cy - reach))
    x1, y1 = min(W, int(d.cx + reach) + 2), min(H, int(d.cy + reach) + 2)
    fo_hi, fo_w = opts["fade_out"]
    for r0 in range(y0, y1, 128):
        r1 = min(y1, r0 + 128)
        rho, th = C.polar(W, H, d.cx, d.cy, R, 1.0, (x0, r0, x1, r1))
        m = (rho >= c0 - 0.03) & (rho < 1.56)
        if not m.any():
            continue
        rh = rho[m]
        x = rh - F32(c0)
        tf = (th[m] % TWO_PI) * (NA / TWO_PI) - 0.5
        ti = np.floor(tf).astype(np.int32)
        tw = (tf - ti).astype(np.float32)
        i0, i1 = ti % NA, (ti + 1) % NA
        na = lutA[i0] * (1 - tw) + lutA[i1] * tw
        if morph > 0:
            nb = lutB[i0] * (1 - tw) + lutB[i1] * tw
            ph = morph * (rh - 1.0)
            ne = na * np.cos(ph).astype(np.float32) + nb * np.sin(ph).astype(np.float32)
        else:
            ne = na
        tp = F32(tap0) + F32(1.0 - tap0) * np.exp(-np.maximum(x, 0.0) * F32(1.0 / tapL)) if tap0 < 1.0 else 1.0
        if partners and soften > 0:
            tg = np.ones(rh.shape, np.float32)
            for pa_ in partners:
                dd = np.abs((th[m] - pa_ + math.pi) % TWO_PI - math.pi)
                tg = np.minimum(tg, (1.0 - soften * np.exp(-0.5 * (dd / 0.45) ** 2)).astype(np.float32))
            ne = ne * tg
        m0 = F32(1.0) + F32(s_a) * ne * tp
        ma = F32(0.5) * (m0 + F32(fl) + np.sqrt((m0 - F32(fl)) ** 2 + F32(fl_soft))) if fl_soft > 0 else np.maximum(m0, F32(fl))
        lm = np.maximum(F32(1.0) + F32(s_l) * ne, F32(0.45))
        u = np.maximum(x, 0.0) / lm
        f = np.clip(u * F32((NL - 1) / umax), 0.0, NL - 1.001)
        fi = f.astype(np.int32)
        ff = (f - fi)[:, None]
        colr = col_lut[fi] * (1 - ff) + col_lut[fi + 1] * ff
        onset = C.smoothstep((x + 0.010) / 0.014)
        outer = C.smoothstep((fo_hi - rh) / fo_w)
        cor_v = colr * (ma * onset * outer)[:, None]
        rim = np.exp(-0.5 * ((rh - (c0 + 0.002)) / 0.0045) ** 2) * F32(opts["rim_amp"])
        Ibm = G.gold_ramp(np.minimum(rim * 1.4, 1.0))
        cor_v += rim[:, None] * (Ibm * F32(0.55 + 0.35 * g) + own[None, :] * F32(0.45 * (1.0 - g)))
        bl = np.exp(-np.maximum(x, 0.0) / 0.22) * F32(opts["bloom"]) * C.smoothstep((x + 0.02) / 0.04) * outer
        cor_v += bl[:, None] * G.gold_ramp(np.float32(0.75))[None, :]
        cor = np.zeros((r1 - r0, x1 - x0, 3), np.float32)
        cor[m] = cor_v * F32(strength)
        cv[r0:r1, x0:x1] += cor
    return own
