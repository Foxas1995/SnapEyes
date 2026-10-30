# -*- coding: utf-8 -*-
"""SPIRAL GALAXY (the light family since 2026-10-30; the owner's pick of the laboratory boards of 2026-10-28, variant A "three arms (recommended)": three
arms, knots, spike stars). The iris is the bright core of a face-on spiral galaxy. Three arms wind out of a warm glow round the limb (logarithmic spirals of
a fixed pitch), each made of the eye's own colour at its angle: a soft band of light, clumps of stars along it, a few bright knots of the collarette's colour
(where the stars are born), a dark lane of dust on its inner edge; a faint disc between the arms, a sparse field of stars beyond and a few foreground stars
with diffraction spikes.

The iris stays whole (the engine pastes it last, byte for byte inside 0.974 R, with the family's F3 feather at the limb); every light here is drawn OUTSIDE
the limb (the arms rise from 1.0 R, the stars start at 1.03 R, the knots at 1.15 R, the spike stars further than 1.25 R), on black.

The soft light is drawn on a grid of 1024 cells on the long side (a 4096 px master: the same numbers on a quarter size grid, brought up in bands), the
stars and knots as Gaussian stamps sized in R; every random number is drawn before any filter, so a 4096 px master is the 1024 px preview drawn finer.
The parameters in GP are the laboratory's (lumen lab galaxy.py of 2026-10-28, commit 43010bd) unchanged.
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
GP = {
    "arms": 3,
    "pitch": 19.0,              # the arms' pitch angle (deg)
    "sharp": 2.6,               # the arm profile's power (higher: narrower arms)
    "disc": (0.80, 1.00),       # the disc's e-fold length (R) and its rise (R) beyond the limb
    "arm_light": 1.1,           # the arms' soft light
    "inter": 0.08,              # the light between the arms
    "bulge": ((0.12, 0.16), (0.35, 0.20)),   # the core glow: (e-fold R, light) twice (the eye's hot colour, then its own colour)
    "lane": (0.50, 0.95, 4.0),  # the dust lane: phase lag (rad of the arm phase), depth, sharpness
    "clump_cells": 30.0,        # clumps along the arms
    "clump": (0.05, 1.6, 2.2),  # the arms' clumps: floor, gain, power
    "stars": (120000, 0.0012, 3.0),   # arm stars: count, sigma (R), light
    "star_floor": 0.06,         # share of the arm stars between the arms
    "star_pow": 2.0,            # how tightly the stars keep to the arms
    "star_mag": 3.0,            # the spread of the arm stars' brightness (higher: fewer bright ones)
    "knots": (300, 0.0040, 1.6),      # star forming knots: count, sigma (R), light
    "field": 110.0,             # field stars per S^2
    "reach": 2.8,               # the galaxy's radius (R)
    "iso": 0.45,                # share of the arms' clumps that are knots rather than streaks along the spiral
    "bright": (5, 0.030),       # foreground stars with diffraction spikes: count, arm (S)
}


# ----------------------------------------------------------------------------- the eye's own two colours per angle (the laboratory's kit)
def _lift(rgb, L_=66.0, cmin=18.0, cmax=58.0, k=1.5, dL=0.0, spread=0.35):
    """The eye's own colours (n, 3) 0..1 lifted to light: their hue, the chroma raised k times inside cmin..cmax, the lightness pulled toward L_ (a share
    `spread` of each colour's own difference kept, so light and dark fibres stay apart)."""
    rgb = np.clip(np.asarray(rgb, F32), 1e-4, 1.0)
    Ls, Cs, hs = C.lch(rgb)
    Ls = np.asarray(Ls, np.float64)
    Lm = float(np.median(Ls))
    Lo = L_ + dL + spread * (Ls - Lm)
    Co = np.clip(np.asarray(Cs, np.float64) * k, cmin, cmax)
    return np.clip(C.from_lch(Lo, Co, hs), 0.0, 1.0).astype(F32)


def _circ_smooth(a, sigma):
    n = a.shape[0]
    taps = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-taps, taps + 1) / float(sigma)) ** 2)
    k /= k.sum()
    out = np.zeros_like(a)
    for i, w in enumerate(k):
        out += F32(w) * np.roll(a, i - taps, axis=0)
    return out


def _eye_pair(ctx, n_ang=360):
    """(outer (n_ang, 3), inner (n_ang, 3), how): the eye's own two colours per angle, both lifted to light. outer: the outer band (0.80 to 0.96 R) smoothed
    round the circle; inner: the collarette (0.36 to 0.52 R) when it differs from the outer band, else the outer band itself turned lighter and warmer."""
    d = ctx.discs[0]
    iris = ctx.irises[0]
    th = (np.arange(n_ang) + 0.5) / n_ang * TWO_PI
    acc_o = np.zeros((n_ang, 3), F32)
    acc_i = np.zeros((n_ang, 3), F32)
    for rs in np.linspace(0.80, 0.96, 6):
        acc_o += K.sample_disc(d, np.full(n_ang, rs), th).reshape(n_ang, 3).astype(F32)
    for rs in np.linspace(0.36, 0.52, 6):
        acc_i += K.sample_disc(d, np.full(n_ang, rs), th).reshape(n_ang, 3).astype(F32)
    acc_o /= 6.0
    acc_i /= 6.0
    acc_o = _circ_smooth(acc_o, 6)
    acc_i = _circ_smooth(acc_i, 10)
    stp = CM.stops(iris)
    outer = 0.5 * _lift(acc_o, 64.0) + 0.5 * stp[1]
    try:
        _rgb, how, _h2 = K.secondary_hue(iris)
    except Exception:  # noqa: BLE001  a synthetic eye without a usable collarette
        how = "analogous"
    if how == "collarette":
        inner = _lift(acc_i, 72.0, 22.0, 60.0, 1.6)
    else:
        inner = (0.6 * stp[2] + 0.4 * stp[1]).astype(F32)
    return outer.astype(F32), inner.astype(F32), how


def _at_angle(tab, th):
    """A per angle table (n, 3) read at angles th (radians), linear between bins."""
    n = tab.shape[0]
    u = (np.asarray(th, np.float64) % TWO_PI) / TWO_PI * n - 0.5
    i0 = np.floor(u).astype(np.int64)
    w = (u - i0).astype(F32)[..., None]
    return tab[i0 % n] * (1.0 - w) + tab[(i0 + 1) % n] * w


class _Field:
    """A smooth 2-D field over the square [-L, L]^2 (R units round the iris centre) on an n x n grid: value noise fBm made once, read anywhere by bilinear
    lookup. The grid does not depend on the canvas, so every size reads the same numbers."""

    def __init__(self, rnd, L=3.2, n=384, cells=6.0, octaves=4, gain=0.5):
        self.L, self.n = float(L), int(n)
        self.a = CM.fbm(self.n, self.n, cells, rnd, octaves, gain).astype(F32)

    def at(self, x, y):
        s = (self.n - 1) / (2.0 * self.L)
        i = (np.asarray(x, np.float64) + self.L) * s
        j = (np.asarray(y, np.float64) + self.L) * s
        return CM.bilerp(self.a, i.astype(F32), j.astype(F32))


# ----------------------------------------------------------------------------- the look
def _arm(rho, th, o, phase0):
    """The arm profile 0..1 at (rho, th) and the arm phase (radians, 0 on an arm's crest)."""
    m = int(o["arms"])
    k = 1.0 / math.tan(math.radians(o["pitch"]))
    psi = m * (th - k * np.log(np.maximum(rho, 1e-3)) - phase0)
    a = (0.5 + 0.5 * np.cos(psi)) ** o["sharp"]
    return a, psi


def fx_galaxy(cv, ctx):
    o = dict(GP)
    o.update(ctx.opts.get("galaxy", {}))
    d = ctx.discs[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, float(d.R)
    rnd = ctx.rand("galaxy")
    phase0 = float(rnd.uniform(1)[0]) * TWO_PI
    outer, inner, how = _eye_pair(ctx)
    stp = CM.stops(ctx.irises[0])
    # ---- every draw first
    ns, sig_s, b_s = o["stars"]
    nk, sig_k, b_k = o["knots"]
    reach = o["reach"]
    u_r = rnd.uniform(int(ns))
    u_t = rnd.uniform(int(ns)) * TWO_PI
    u_a = rnd.uniform(int(ns))
    u_m = rnd.uniform(int(ns))
    u_j = rnd.normal(int(ns), 0.0, 1.0)
    k_r = rnd.uniform(int(nk) * 6)
    k_t = rnd.uniform(int(nk) * 6) * TWO_PI
    k_a = rnd.uniform(int(nk) * 6)
    k_s = rnd.uniform(int(nk) * 6)
    b_u, b_v, b_m = rnd.uniform(16), rnd.uniform(16), rnd.uniform(16)
    clumps = _Field(ctx.rand("galaxy_clumps"), L=3.4, n=512, cells=o["clump_cells"], octaves=4, gain=0.55)
    lanes = _Field(ctx.rand("galaxy_lanes"), L=3.4, n=512, cells=o["clump_cells"] * 1.6, octaves=4, gain=0.6)
    # ---- the soft light on the grid
    f = max(1, int(round(max(W, H) / 1024.0)))
    g = C.Grid(W, H, f)
    light = np.zeros((g.h, g.w, 3), F32)
    gx0, gy0, gx1, gy1 = g.box(d.cx, d.cy, (reach + 0.3) * R)
    rho, th = g.polar(d.cx, d.cy, R, 1.0, (gx0, gy0, gx1, gy1))
    e = np.maximum(rho - 1.0, 0.0)
    L_d, _rise = o["disc"]
    disc = (np.exp(-e / L_d) * (1.0 - CM.smooth((rho - reach * 0.75) / (reach * 0.35)))).astype(F32)
    arm, psi = _arm(rho, th, o, phase0)
    # the unwound coordinates: a point's position turned back along the spiral, so the clumps lie along the arms
    kk = 1.0 / math.tan(math.radians(o["pitch"]))
    tu = th - kk * np.log(np.maximum(rho, 1e-3))
    ux, uy = rho * np.cos(tu) * 0.85, rho * np.sin(tu) * 0.85
    cl = CM.stretch01(clumps.at(ux, uy), 0.02, 0.98)
    if o["iso"] > 0:                                             # knots that do not follow the spiral (star clouds, not streaks)
        ci = CM.stretch01(clumps.at(rho * np.cos(th) * 1.7 + 0.31, rho * np.sin(th) * 1.7 - 0.27), 0.02, 0.98)
        cl = cl * (1.0 - o["iso"]) + ci * o["iso"]
    ln = CM.stretch01(lanes.at(ux, uy), 0.02, 0.98)
    lag, depth, lsharp = o["lane"]
    lane = (0.5 + 0.5 * np.cos(psi + lag)) ** lsharp * CM.smooth((ln - 0.25) / 0.4)
    armrise = CM.smooth((rho - 1.0) / 0.25)
    c0_, c1_, cp_ = o["clump"]
    I_arm = o["arm_light"] * arm * disc * (c0_ + c1_ * cl ** cp_) * armrise
    I_int = o["inter"] * disc
    I = (I_arm + I_int) * (1.0 - depth * lane * CM.smooth((rho - 1.08) / 0.15))
    col = _at_angle(outer, th)
    light[gy0:gy1, gx0:gx1] = col * I[..., None]
    # the core: a warm glow of the eye's own hot colour round the limb
    hot = _at_angle(stp[2], th)
    (l1, b1), (l2, b2) = o["bulge"]
    light[gy0:gy1, gx0:gx1] += hot * (b1 * np.exp(-e / l1)).astype(F32)[..., None] + _at_angle(outer, th) * (b2 * np.exp(-e / l2)).astype(F32)[..., None]
    del rho, th, e, disc, arm, psi, tu, ux, uy, cl, ln, lane, I, col, hot
    CM.screen_grid(cv, light, f, "screen", CM.fades_for(ctx))
    del light
    # ---- stars along the arms (accepted where the arm is), knots on the arm crests, a field of stars
    rr = 1.03 + (reach - 1.03) * u_r ** 1.35
    a_s, _ = _arm(rr, u_t, o, phase0)
    disc_s = np.exp(-(rr - 1.0) / L_d)
    acc = u_a < (o["star_floor"] + (1.0 - o["star_floor"]) * a_s ** o["star_pow"]) * disc_s
    jit = u_j * 0.02
    sx = d.cx + rr * R * np.cos(u_t + jit / rr)
    sy = d.cy + rr * R * np.sin(u_t + jit / rr)
    cs = _at_angle(stp[2], u_t)
    white = np.array([1.0, 0.97, 0.92], F32)
    scol = (cs * (0.5 + 0.5 * u_m[:, None]) + white * (0.5 - 0.5 * u_m[:, None])).astype(F32)
    mag = 0.18 + 0.82 * (u_m ** o["star_mag"])
    layer = M.ParticleLayer()
    layer.splat(sx[acc], sy[acc], sig_s * R, scol[acc], (b_s * mag[acc]).astype(F32), min_sigma=0.5)
    kr = 1.15 + (reach * 0.8 - 1.15) * k_r
    a_k, _ = _arm(kr, k_t, o, phase0)
    kacc = (k_a < a_k ** 2 * np.exp(-(kr - 1.0) / L_d))
    kx = d.cx + kr * R * np.cos(k_t)
    ky = d.cy + kr * R * np.sin(k_t)
    kc = _at_angle(inner, k_t)
    ksz = sig_k * (0.5 + 1.0 * k_s)
    sel = np.nonzero(kacc)[0][: int(nk)]
    layer.splat(kx[sel], ky[sel], ksz[sel] * R, kc[sel], (b_k * (0.4 + 0.6 * k_s[sel])).astype(F32), min_sigma=0.5)
    layer.splat(kx[sel], ky[sel], ksz[sel] * R * 0.3, np.ones((len(sel), 3), F32), (b_k * 0.8 * k_s[sel]).astype(F32), min_sigma=0.5)
    CM.starfield(ctx, layer, ctx.rand("galaxy_field"), o["field"], mags=(1.0, 7.5), avoid=CM.avoid_discs([d], 1.05))
    nb, arm_b = o["bright"]
    fades = (lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0))
    layer.flush(cv, fades=fades)
    if nb > 0:
        # the cores of the spike stars take the same fades as every other star (the laboratory drew them unfaded: none in the customer's words, the
        # wallpaper's lock screen zones or the canvas edge); their spikes keep out of those places by themselves (common.spikes)
        bx = b_u[: int(nb)] * W
        by = b_v[: int(nb)] * H
        far = np.hypot(bx - d.cx, by - d.cy) > 1.25 * R
        bc = np.array([1.0, 0.96, 0.9], F32) * 0.5 + _at_angle(stp[2], np.arctan2(by - d.cy, bx - d.cx)) * 0.5
        bm = 0.5 + 0.5 * b_m[: int(nb)]
        layer2 = M.ParticleLayer()
        layer2.splat(bx[far], by[far], 0.0016 * S, bc[far], (2.0 * bm[far]).astype(F32), min_sigma=0.5)
        layer2.flush(cv, fades=fades)
        CM.spikes(cv, ctx, bx[far], by[far], arm_b * bm[far], bc[far], 0.9 * bm[far], width_S=0.0005, angle=0.3)
    ctx.log["galaxy"] = {"stars": int(acc.sum()), "knots": int(len(sel)), "how": how, "grid": [g.w, g.h]}
