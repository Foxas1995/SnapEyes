# -*- coding: utf-8 -*-
"""STARDUST, the design of Supernova (the light family): the iris as a star that has just burst. Clumpy jets of stardust leave every angle of the
limb in the eye's own colour at that angle (the ring colours through the deep, mid and hot ramp: a blue eye bursts blue and teal, a brown one amber
and copper, a grey one silver), glowing haze along the jets, tens of thousands of glitter grains with a few sparkles, fine radial filaments, a faint
broken shock shell further out, a white hot rim at the limb and a quiet field of stars behind. All round, never on a wind (that is Sparks and Powder
Burst), denser in a few jets.

The haze is periodic polar fBm (core.fbm_polar: radial streaks, the same in every size) on a grid of at most 1536 cells on the long side; the grains,
filaments and sparkles are pixel integrated stamps (matter.ParticleLayer, drawn in bands), their counts per S^2, so a 4096 master is the preview
drawn finer (the haze of a master on a 1366 grid). The iris is not touched: nothing is drawn nearer than the limb and the iris is pasted over everything.
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
    "grid": 1536,
    "jets": (18, 0.55),           # jets round the limb and their share of the light (the rest is an even burst)
    "reach": (0.42, 0.95),        # e-fold length of the burst in R: between jets, in the strongest jet
    "haze": 0.85,                 # the glowing haze along the jets
    "grains": 42000,              # glitter grains per S^2
    "sparkles": 340,              # brighter grains per S^2
    "spiked": 14,                 # the brightest sparkles with four short spikes
    "filaments": 520,             # fine radial filaments per S^2
    "shell": (1.82, 0.030, 0.16), # the shock shell: radius (R), width (R), strength (broken: only where the burst is strong)
    "rim": (0.80, 0.030, 0.30, 0.16),  # the white hot rim and its glow: close strength, e-fold (R), body strength, e-fold (R)
    "stars": (1800, (0.0, 8.0)),
    "grain": 0.010,
}
BAND = 128                        # grid rows a band of the haze holds


def _jet_profile(rnd, n_jets, n=4096):
    """(n,) the burst's strength round the circle, 0..1: n_jets jets of random width and strength over a periodic fBm floor."""
    th = np.arange(n) * (TWO_PI / n)
    prof = 0.35 + 0.65 * C.periodic_fbm1d(n, rnd, 4, 7, 0.55).astype(np.float64)
    jets = np.zeros(n)
    centres = rnd.uniform(n_jets) * TWO_PI
    widths = np.radians(3.0 + 9.0 * rnd.uniform(n_jets) ** 1.5)
    strength = 0.35 + 0.65 * rnd.uniform(n_jets) ** 0.8
    for c, w, s in zip(centres, widths, strength):
        d = (th - c + math.pi) % TWO_PI - math.pi
        jets = np.maximum(jets, s * np.exp(-0.5 * (d / w) ** 2))
    return prof, jets


def _lut(tab, th):
    n = len(tab)
    p = (np.asarray(th, np.float64) % TWO_PI) * (n / TWO_PI)
    i0 = np.floor(p).astype(np.int64)
    w = p - i0
    return tab[i0 % n] * (1.0 - w) + tab[(i0 + 1) % n] * w


def fx_stardust(cv, ctx):
    o = dict(SP)
    o.update(ctx.opts.get("stardust", {}))
    discs, irises = ctx.discs, ctx.irises
    W, H, S = ctx.W, ctx.H, ctx.S
    fade = CM.fades_for(ctx)
    f = CM.grid_factor(W, H, o["grid"])
    g = C.Grid(W, H, f)
    x, y = CM.grid_xy(g)
    light = np.zeros((g.h, g.w, 3), F32)
    layer = M.ParticleLayer()
    n_jets, jet_share = o["jets"]
    r_lo, r_hi = o["reach"]
    logs = []
    for k_, (d, iris) in enumerate(zip(discs, irises)):
        R = d.R
        stp = CM.stops(iris, white=0.45)
        rnd = ctx.rand(f"stardust_{k_}")
        prof, jets = _jet_profile(rnd, int(n_jets))
        strength = (1.0 - jet_share) * prof + jet_share * jets * (0.6 + 0.4 * prof)       # 0..1 round the circle
        reach = r_lo + (r_hi - r_lo) * jets                                                  # the jets reach further
        # ---- the haze on the grid: polar streaks (fine in angle, long in radius), the jets' strength and reach, the ring's colour; one band of grid rows
        # at a time (every term is pointwise), so the temporaries of a 4096 px master stay a band in size
        n_ang, n_rad = 2048, 256
        streak = C.fbm_polar(n_ang, n_rad, ctx.rand(f"stardust_streak_{k_}"), 5, (40, 3), 0.62)
        clump = C.fbm_polar(n_ang, n_rad, ctx.rand(f"stardust_clump_{k_}"), 4, (10, 5), 0.55)
        rk, rl, bk, bl = o["rim"]
        sr, sw, sk = o["shell"]
        for r0 in range(0, g.h, BAND):
            r1 = min(g.h, r0 + BAND)
            rho, th = CM.polar_of(x, y[r0:r1], d)
            e = np.maximum(rho - F32(1.0), F32(0.0))
            ai = ((th % F32(TWO_PI)) * F32(n_ang / TWO_PI)).astype(np.int32) % n_ang
            ri = np.clip((np.log1p(e) / math.log(4.0) * (n_rad - 1)).astype(np.int32), 0, n_rad - 1)
            st = streak[ai, ri]
            cl = clump[ai, ri]
            del ai, ri
            s_th = _lut(strength, th).astype(F32)
            r_th = _lut(reach, th).astype(F32)
            prof_r = np.exp(-e / r_th) * CM.smooth((rho - F32(0.99)) / F32(0.04))
            tex = (F32(0.25) + F32(1.15) * CM.smooth((st - F32(0.40)) / F32(0.35))) * (F32(0.45) + F32(0.9) * cl)
            I = (F32(o["haze"]) * s_th * prof_r * tex).astype(F32)
            del st, cl, tex
            lvl = np.clip(I * F32(1.25) + F32(0.25) * np.exp(-e / F32(0.15)), 0.0, 1.0)
            # the white hot rim and its glow (the light of the burst itself)
            Ir = (F32(rk) * np.exp(-e / F32(rl)) + F32(bk) * np.exp(-e / F32(bl)) * (F32(0.5) + s_th)) * CM.smooth((rho - F32(0.985)) / F32(0.03))
            # the broken shock shell
            Is = F32(sk) * np.exp(-0.5 * ((rho - F32(sr)) / F32(sw)) ** 2) * np.clip(_lut(prof, th).astype(F32) * F32(1.6) - F32(0.75), 0.0, 1.0) ** 2
            # one colour lookup for the three lights: the level of each, weighted by its own light (the ramp is the dear part on a full grid)
            tot = I + Ir + Is
            lv = (lvl * I + np.clip(Ir * F32(1.4), 0.0, 1.0) * Ir + F32(0.75) * Is) / np.maximum(tot, F32(1e-6))
            light[r0:r1] += CM.ramp3(stp, th, lv) * tot[..., None]
            del tot, lv, rho, th, e, prof_r, I, Ir, Is, s_th, r_th, lvl
        del streak, clump
        # ---- the grains: positions drawn from the burst (angle by strength, distance by the reach at that angle)
        def burst(n, reach_k=1.0, min_e=0.012):
            m_ = int(n * 2.2)
            t = rnd.uniform(m_) * TWO_PI
            keep = rnd.uniform(m_) < _lut(strength, t) ** 1.25
            t = t[keep][:n]
            ee = rnd.exponential(len(t), 1.0) * _lut(reach, t) * reach_k + min_e
            jit = rnd.normal(len(t), 0.0, 0.010) * (0.4 + ee)                              # the grains wander a little off their ray
            px = d.cx + (1.0 + ee) * R * np.cos(t + jit)
            py = d.cy + (1.0 + ee) * R * np.sin(t + jit)
            return t, ee, px, py
        dens = (W * H) / float(S * S)
        t1, e1, px, py = burst(int(o["grains"] * dens))
        u = rnd.uniform(len(t1))
        lv = np.clip(0.20 + 0.75 * u ** 1.4 - 0.25 * np.clip(e1 / 1.6, 0, 1), 0.0, 1.0)
        col = CM.ramp3(stp, t1, lv)
        amp = (0.10 + 0.55 * u ** 3.0) * np.exp(-e1 / 2.2)
        layer.splat(px, py, (0.00024 + 0.00030 * rnd.uniform(len(t1)) ** 2) * S, col, amp.astype(F32), min_sigma=0.5)
        t2, e2, px2, py2 = burst(int(o["sparkles"] * dens), 1.1)
        u2 = rnd.uniform(len(t2))
        col2 = CM.ramp3(stp, t2, np.clip(0.55 + 0.45 * u2, 0, 1))
        amp2 = (0.45 + 1.1 * u2 ** 2.2) * np.exp(-e2 / 2.6)
        layer.splat(px2, py2, 0.00042 * S, col2, amp2.astype(F32), min_sigma=0.5)
        layer.splat(px2, py2, 0.0016 * S, col2, (0.05 * amp2).astype(F32), min_sigma=0.5)
        # ---- fine radial filaments: short streaks along the ray, bright heads outward
        t3, e3, px3, py3 = burst(int(o["filaments"] * dens), 0.9, 0.03)
        u3 = rnd.uniform(len(t3))
        dx, dy = np.cos(t3), np.sin(t3)
        ln = (0.010 + 0.050 * u3 ** 1.5) * S * (0.6 + 0.5 * np.clip(e3, 0, 1))
        col3 = CM.ramp3(stp, t3, np.clip(0.35 + 0.5 * u3, 0, 1))
        M.streaks(layer, px3, py3, dx, dy, ln, col3, (0.10 + 0.35 * u3 ** 2) * np.exp(-e3 / 2.0), sigma_px=0.00040 * S)
        nsp = int(o["spiked"])
        top = np.argsort(-amp2)[:nsp]
        logs.append({"class": iris.cls, "jets": int(n_jets), "grains": int(len(t1)), "sparkles": int(len(t2)), "filaments": int(len(t3)),
                     "spikes": (px2[top], py2[top], amp2[top], col2[top])})
    CM.screen_grid(cv, light, f, "screen", fade)
    del light
    # ---- stars behind (quiet: the burst is the picture) and the grains, filaments and sparkles in front
    star_layer = M.ParticleLayer()
    dens_s, mags = o["stars"]
    CM.starfield(ctx, star_layer, ctx.rand("stardust_stars"), dens_s, mags, sigma_S=0.00040, peak=1.1, avoid=CM.avoid_discs(discs, 1.0), eps=0.05)
    fades = (lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0))
    star_layer.flush(cv, fades=fades)
    layer.flush(cv, fades=fades)
    for lg in logs:
        sx, sy, sa, sc = lg.pop("spikes")
        CM.spikes(cv, ctx, sx, sy, 0.008 + 0.020 * np.clip(sa / 1.5, 0, 1), sc, 0.45 * np.clip(sa / 1.5, 0.3, 1.0), angle=math.radians(12.0))
    if o["grain"]:
        CM.grain(cv, ctx.rand("stardust_grain"), o["grain"])
    ctx.log["stardust"] = logs
