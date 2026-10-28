# -*- coding: utf-8 -*-
"""AURORA (the light family; redrawn 2026-10-28 after the owner's verdict on the old look, "a blurry blue cloud with a hard dark rim, a sticker on fog"):
curtains of northern light rise from the limb, with fine ray structure, the iris's own colour at the foot and its partner hue at the tips, on black.

The iris stays whole (the engine pastes it last, byte for byte inside 0.974 R, with the family's F3 feather at the limb) and keeps no dark limbal ring of
the finish (DESIGN_FIN, as Powder Burst): the curtains start just under the feather, so the iris's edge runs straight into their light and no dark seam,
no ring and no plate separates the two. Round it, two curtains (AP["curtains"]):

  the curtain   a luminous sheet standing on the limb: fine rays (a table of 1600 Gaussian rays round the circle, 0.0012 to 0.0045 rad wide), a diffuse
                share under them, a sharp bright foot with a white hot touch, an e-fold height that changes round the circle (low harmonics, taller where
                the curtain is brighter), brighter and taller toward 12 o'clock ("lift"); the rays lean as they climb, so the curtain flows round the iris
                instead of bursting out of it; its colour runs from the eye's own light colour at each angle (common.stops) to the partner hue at the tips
  the veil      the partner coloured upper aurora: taller, softer (a larger diffuse share, a soft foot: a sharp one drew an arc), dimmer

Every curtain is drawn from 1-D tables round the circle (16384 samples) and a polar evaluation on a grid of at most 1536 cells on the long side (a
1024 preview: factor 1; a 4096 master: factor 3); the ray table is filtered to the grid's pixel (its angular footprint at 1.3 R), so a 480 px tile
does not alias and a master is the preview drawn finer. Every random number is drawn before any pixel work and none depends on the canvas size.
Lengths are in R (the iris radius) or S. The light dies out between 0.37 and 0.51 S from the centre: dark corners, never a lit square.
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
N = 16384                               # samples of every 1-D table round the circle

AP = {
    "base": {                           # one curtain (lengths in R, angles in compass degrees: 0 = 12 o'clock, clockwise); "curtains" override
        "k": 1.0,                           # strength
        "arc": None,                        # (centre, half width, taper): the curtain stands on this arc only (None: all round)
        "lift": (0.0, 0.0, 0.0),            # (height gain, light gain, centre): taller and brighter toward this compass angle
        "foot": 0.004,                      # the foot beyond the limb (negative: under the feather, so the iris's edge runs into the light)
        "h": 0.30,                          # the e-fold height
        "hvar": (0.45, 2),                  # the height's change round the circle: share and lowest harmonic
        "htie": 0.3,                        # the bright stretches stand taller (share of the height that follows them)
        "rag": 0.20,                        # the rays' lengths differ by this share
        "lean": 0.0,                        # the rays lean as they climb (radians per R; + clockwise)
        "rays": (1400, 0.0018, 0.0060),     # count, sigma min and max (radians)
        "rc": 1.0,                          # the rays' contrast (power of the ray table)
        "fill": 0.45,                       # the diffuse share under the rays
        "ps": 0.85,                         # the partner's share at the tips
        "pt": 0.9,                          # the partner takes over at this share of the height
        "rw": 0.012,                        # the sharp lower edge
        "pw": 1.15,                         # the profile's power
        "edge": 0.6,                        # extra light at the lower border (the bright foot of a curtain)
        "hot": 0.25,                        # white hot share at the foot
        "haze": 0.10,                       # the soft glow of the curtain
        "env": (0.45, 4),                   # the amplitude round the circle: the lowest level, the noise's base cells
        "bright": (16, 1.5, 0.30),          # the bright stretches along the curtain: base cells, power, floor
    },
    "curtains": (
        {"foot": -0.015, "k": 2.8, "lean": 0.42, "fill": 0.42, "rag": 0.1, "htie": 0.6, "hvar": (0.4, 3), "bright": (8, 1.8, 0.15), "h": 0.30,
         "edge": 1.0, "rays": (1600, 0.0012, 0.0045), "rc": 1.4, "pt": 1.1, "ps": 0.8, "lift": (0.6, 0.3, 0.0)},
        {"foot": -0.015, "rw": 0.08, "k": 0.8, "lean": 0.42, "fill": 0.75, "rag": 0.1, "hvar": (0.4, 3), "bright": (8, 1.5, 0.2), "h": 0.58,
         "edge": 0.0, "hot": 0.0, "rays": (900, 0.0018, 0.007), "ps": 1.0, "pt": 0.35, "lift": (0.7, 0.35, 0.0)},
    ),
    "turn": 90.0,                       # degrees the partner hue is turned from the eye's hue
    "turn2": 28.0,                      # the partner's second hue, a further turn (the tips change colour slowly round the circle)
    "own_hot": 0.20,                    # the foot colour: the eye's mid colour with this share of its hot colour
    "fade": (0.37, 0.51),               # the light dies out between these distances from the centre of the iris (shares of S)
    "grid": 1536,                       # cells of the grid on the long side at most (a 1024 preview: factor 1; a 4096 master: factor 3)
    "stars": (110, 170),
    "rim": (0.55, 0.985, 0.03),         # the curtains' foot light laid over the limb's feather after the paste (zone B only): strength, from (R),
                                        # ramp (R): where a curtain is bright the iris's dark limbal edge does not stand between it and its light
    "grain": 0.0,                       # no print grain: the light stays clean on the black (and a master saves 2.4 s)
}


def partner_colour(iris, stp, turn):
    """The partner light colour of the eye: its mid colour turned toward violet (cool eyes), rose (warm ones) or cyan (greens), same lightness."""
    h = float(iris.stats["h"])
    Lm, Cm, hm = C.lch(CM.mean_colour(stp, 1))
    if 95.0 <= h <= 175.0:
        dh = turn * 0.9
    elif 175.0 < h < 345.0:
        dh = turn
    else:
        dh = -turn * 0.9
    c = float(np.clip(Cm * 1.25, 28.0, 66.0))
    return C.from_lch(float(Lm) - 2.0, c, (float(hm) + dh) % 360.0).astype(F32)


def _circ_blur(tab, sigma):
    """Circular Gaussian blur of a periodic table (sigma in samples), by FFT."""
    if sigma <= 0.05:
        return np.asarray(tab, F32)
    n = len(tab)
    k = np.fft.rfftfreq(n) * n
    g = np.exp(-0.5 * (TWO_PI * k * sigma / n) ** 2)
    return np.fft.irfft(np.fft.rfft(np.asarray(tab, np.float64)) * g, n).astype(F32)


def _norm(v):
    v = np.asarray(v, np.float64)
    return (v - v.min()) / max(float(v.max() - v.min()), 1e-9)


def _rays(rnd, n, s0, s1):
    """The ray tables of a curtain: (intensity, length) round the circle, N samples. n rays at random angles, widths (log uniform s0..s1 radians),
    brightness and lengths."""
    a = rnd.uniform(n) * TWO_PI
    sg = np.exp(np.log(s0) + (np.log(s1) - np.log(s0)) * rnd.uniform(n))
    b = 0.20 + 0.80 * rnd.uniform(n) ** 1.5
    ln = rnd.uniform(n)
    p = a * (N / TWO_PI)
    ss = sg * (N / TWO_PI)
    w = int(math.ceil(3.0 * ss.max()))
    off = np.arange(-w, w + 1)
    c = np.rint(p).astype(np.int64)
    idx = ((c[:, None] + off[None, :]) % N).ravel()
    val = b[:, None] * np.exp(-0.5 * ((c[:, None] + off[None, :] - p[:, None]) / ss[:, None]) ** 2)
    ti = np.bincount(idx, val.ravel(), N)
    tl = np.bincount(idx, (val * ln[:, None]).ravel(), N)
    tl = np.where(ti > 1e-6, tl / np.maximum(ti, 1e-6), 0.5)
    ti /= max(float(np.quantile(ti, 0.99)), 1e-6)
    return ti.astype(F32), tl.astype(F32)


def _harm(rnd, m):
    """A smooth periodic wave of the lowest harmonic m round the circle (N samples, about -1..1)."""
    ph = rnd.uniform(3) * TWO_PI
    t = np.arange(N) * (TWO_PI / N)
    return 0.5 * np.sin(m * t + ph[0]) + 0.32 * np.sin((m + 1) * t + ph[1]) + 0.18 * np.sin((m + 3) * t + ph[2])


def _curtain(rnd, c):
    """Every draw of one curtain, then its 1-D tables round the circle (screen angle 0 = 3 o'clock, clockwise): the light A, the foot, the height,
    the rays (ti), their lengths (tl) and their smooth share (sm)."""
    hw = _harm(rnd, int(c["hvar"][1]))
    ti, tl = _rays(rnd, int(c["rays"][0]), float(c["rays"][1]), float(c["rays"][2]))
    if c["rc"] != 1.0:
        ti = (np.minimum(ti, 1.6) ** c["rc"]).astype(F32)
    env = _norm(C.periodic_fbm1d(N, rnd, 3, int(c["env"][1]), 0.55))
    br = _norm(C.periodic_fbm1d(N, rnd, 3, int(c["bright"][0]), 0.55))
    t = np.arange(N) * (TWO_PI / N)
    cp = (np.degrees(t) + 90.0) % 360.0
    b = c["bright"][2] + (1.0 - c["bright"][2]) * br ** c["bright"][1]
    A = (c["env"][0] + (1.0 - c["env"][0]) * env) * b
    if c["arc"] is not None:
        mid, half, tap = c["arc"]
        dd = np.abs((cp - mid + 180.0) % 360.0 - 180.0)
        A = A * CM.smooth((half - dd) / max(tap, 1e-3))
    foot = np.full(N, float(c["foot"]))
    h = c["h"] * np.maximum(1.0 + c["hvar"][0] * hw, 0.25) * (1.0 - c["htie"] + c["htie"] * 1.6 * b)
    if c["lift"][0] or c["lift"][1]:
        q = 0.5 + 0.5 * np.cos(np.radians(cp - c["lift"][2]))
        h = h * (1.0 + c["lift"][0] * q)
        A = A * (1.0 + c["lift"][1] * q)
    sm = _circ_blur(ti, 0.03 * N / TWO_PI)
    sm = sm / max(float(sm.max()), 1e-6)
    return {"A": A.astype(F32), "foot": foot.astype(F32), "h": h.astype(F32), "ti": ti, "tl": tl, "sm": sm.astype(F32)}


def _idx(th):
    p = (th % F32(TWO_PI)) * F32(N / TWO_PI)
    i0 = np.floor(p).astype(np.int32)
    w = (p - i0).astype(F32)
    i0 %= N
    return i0, (i0 + 1) % N, w


def _lk(tab, ix):
    i0, i1, w = ix
    return tab[i0] * (F32(1.0) - w) + tab[i1] * w


def _rim_post(ctx, d, tabs, own_lut, rim):
    """The foot light of the curtains standing on the limb, screened over the outer feather of the pasted iris (from rim[1] R, full by rim[1] + rim[2]
    R, gone by 1.04 R): zone B only, the iris inside 0.974 R stays byte for byte its graded disc."""
    k, r0, rr = rim
    n = own_lut.shape[0]
    foot = np.zeros(N, F32)
    for c, t, ti in tabs:
        if c["foot"] <= 0.005:
            foot += F32(c["k"]) * t["A"] * (F32(c["fill"]) * t["sm"] + F32(1.0 - c["fill"]) * ti) * F32(1.0 + c["edge"])
    col = (own_lut * np.minimum(foot[::N // n], F32(1.2))[:, None] * F32(k)).astype(F32)
    W, H, R = ctx.W, ctx.H, d.R

    def apply(img8):
        reach = 1.04 * R
        x0, y0 = max(0, int(d.cx - reach)), max(0, int(d.cy - reach))
        x1, y1 = min(W, int(math.ceil(d.cx + reach)) + 1), min(H, int(math.ceil(d.cy + reach)) + 1)
        for a in range(y0, y1, 256):
            b = min(y1, a + 256)
            rho, th = C.polar(W, H, d.cx, d.cy, R, 1.0, (x0, a, x1, b))
            w = CM.smooth((rho - F32(r0)) / F32(rr)) * (F32(1.0) - CM.smooth((rho - F32(1.0)) / F32(0.04)))
            sel = w > 0
            if not sel.any():
                continue
            lt = np.minimum(col[C.angle_index(th[sel], n)] * w[sel][:, None], F32(0.92))
            reg = img8[a:b, x0:x1]
            v = reg[sel].astype(F32) / F32(255.0)
            v = F32(1.0) - (F32(1.0) - v) * (F32(1.0) - lt)
            reg[sel] = np.clip(np.rint(v * F32(255.0)), 0, 255).astype(np.uint8)
    return apply


def fx_aurora(cv, ctx):
    o = dict(AP)
    o.update(ctx.opts.get("aurora", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    stp = CM.stops(iris, white=0.30)
    part_c = partner_colour(iris, stp, float(o["turn"]))
    part2_c = partner_colour(iris, stp, float(o["turn"]) + float(o["turn2"]))
    # every random draw first (none depends on the canvas): a master is its preview drawn finer
    rnd = ctx.rand("aurora")
    curt = []
    for c0 in o["curtains"]:
        c = dict(o["base"])
        c.update(c0)
        curt.append((c, _curtain(rnd, c)))
    pc = _norm(C.periodic_fbm1d(4096, rnd, 2, 3, 0.5)).astype(F32)
    rs = ctx.rand("aurora_stars")
    ns = int(o["stars"][0] + (o["stars"][1] - o["stars"][0]) * float(rs.uniform()))
    sx, sy = rs.uniform(ns) * W, rs.uniform(ns) * H
    sa = 0.05 + 0.20 * rs.uniform(ns) ** 2.2
    sz = (0.0004 + 0.0005 * rs.uniform(ns)) * S
    cool = C.mix(C.rgb01("#DCE6FF")[None, :], C.rgb01("#FFF2E2")[None, :], rs.uniform(ns)[:, None])
    # ---- colours round the circle: the eye's own light colour at each angle, the partner drifting between two hues
    own_lut = C.palette_lut(stp[1] * (1.0 - o["own_hot"]) + stp[2] * o["own_hot"], 4096)
    hot_lut = C.palette_lut(stp[2], 4096)
    part_lut = (part_c[None, :] * (1.0 - pc[:, None]) + part2_c[None, :] * pc[:, None]).astype(F32)
    fade = CM.fades_for(ctx)
    f = CM.grid_factor(W, H, o["grid"])
    g = C.Grid(W, H, f)
    fa, fb = float(o["fade"][0]) * S / R, float(o["fade"][1]) * S / R
    gx0, gy0, gx1, gy1 = g.box(d.cx, d.cy, fb * R)
    # the rays filtered to the grid's pixel (their angular footprint at 1.3 R): a 480 tile does not alias, a master is the preview drawn finer
    fp = (f / (1.3 * R)) * (N / TWO_PI)
    tabs = [(c, t, _circ_blur(t["ti"], 0.42 * fp)) for c, t in curt]
    light = np.zeros((g.h, g.w, 3), F32)
    for ga in range(gy0, gy1, 128):
        gb = min(gy1, ga + 128)
        rho, th = g.polar(d.cx, d.cy, R, 1.0, (gx0, ga, gx1, gb))
        rho, th = rho.astype(F32), th.astype(F32)
        Lo = np.zeros(rho.shape, F32)
        Lp = np.zeros(rho.shape, F32)
        Lw = np.zeros(rho.shape, F32)
        ix0 = _idx(th)
        lim = CM.smooth((rho - F32(0.985)) / F32(0.03))
        for c, t, ti in tabs:
            A = _lk(t["A"], ix0)
            ft = _lk(t["foot"], ix0)
            hh = _lk(t["h"], ix0)
            e = rho - F32(1.0) - ft
            ep = np.maximum(e, F32(0.0))
            ix = _idx(th + F32(c["lean"]) * ep) if c["lean"] else ix0
            ray = _lk(ti, ix)
            ln = _lk(t["tl"], ix)
            sm = _lk(t["sm"], ix)
            he = np.maximum(hh * (F32(1.0 - c["rag"]) + F32(c["rag"] * 1.6) * ln), F32(0.02))
            prof = np.exp(-(ep / he) ** F32(c["pw"]))
            rise = CM.smooth(e / F32(c["rw"]))
            body = F32(c["fill"]) * sm + F32(1.0 - c["fill"]) * ray
            I = F32(c["k"]) * A * rise * prof * body * (F32(1.0) + F32(c["edge"]) * np.exp(-ep / F32(0.035)))
            if c["haze"] > 0:
                down = np.exp(np.minimum(e, F32(0.0)) / F32(0.02))
                I += F32(c["k"] * c["haze"]) * A * sm * down * lim * np.exp(-ep / (F32(1.8) * hh))
            s = F32(c["ps"]) * CM.smooth(ep / np.maximum(F32(c["pt"]) * hh, F32(0.02)))
            Lo += I * (F32(1.0) - s)
            Lp += I * s
            if c["hot"] > 0:
                Lw += I * F32(c["hot"]) * np.exp(-ep / F32(0.03))
        edge = (F32(1.0) - CM.smooth((rho - F32(fa)) / F32(fb - fa))) * (rho > F32(0.97))
        ci = C.angle_index(th, 4096)
        lt = (Lo * edge)[..., None] * own_lut[ci]
        lt += (Lp * edge)[..., None] * part_lut[ci]
        lt += (Lw * edge)[..., None] * hot_lut[ci]
        light[ga:gb, gx0:gx1] = lt
    CM.screen_grid(cv, light, f, "screen", fade)
    del light
    if o["rim"][0] > 0:
        ctx.post.append(_rim_post(ctx, d, tabs, own_lut, o["rim"]))
    keep = np.hypot(sx - d.cx, sy - d.cy) > 2.0 * R
    layer = ParticleLayer()
    layer.splat(sx[keep], sy[keep], sz[keep], cool[keep], sa[keep], min_sigma=0.5)
    layer.flush(cv, fades=(lambda vv, r0: K.wall_fade(vv, ctx, y0=r0), lambda vv, r0: K.text_fade(vv, ctx, y0=r0)))
    if o["grain"]:
        CM.grain(cv, ctx.rand("aurora_grain"), o["grain"])
    ctx.log["aurora"] = {"class": iris.cls, "partner_rgb": [round(float(v), 3) for v in part_c], "factor": f}
