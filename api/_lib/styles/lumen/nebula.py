# -*- coding: utf-8 -*-
"""NEBULA (the light family): the iris as the bright heart of a nebula. The eye's own colour glows warm at its limb and in the gas nearest to
it; further out the clouds turn to the eye's partner colour (teal blue round a brown eye, violet round a blue one, purple round a green one: the
warm and cool pair of an astronomer's picture, or the eye's own second colour when its collarette has one); soft dark dust lanes cross the clouds and
their edges facing the iris are lit; a cluster of young stars sits round the iris and a field of stars of every magnitude and temperature fills the sky.

The gas is domain warped fBm with an exponential stretch (bright cores, smooth dark gaps, as a stretched astrophotograph) and ridged filaments, on a
grid of at most 1536 cells on the long side (the 1024 preview at full resolution, a 4096 master on a 1366 grid: the same pattern drawn finer); the
noise textures are padded so that a warped lookup never runs off their edge. A master draws two finer octaves of the gas and of the filaments that the
preview cannot hold (common.fbm_master: an octave whose cells span 8 px or more at the master's size and fewer at 1024), so the gas is clumpy and
fibrous at 100 percent instead of a smooth blur, and the preview is unchanged. The dust is a third warped field that darkens the gas and dims the stars
behind it. Every disc of the context gets its own cavity and its own colours, so a pair or a family is the same code: the composition, the dust and the
glow are drawn one band of grid rows at a time (the temporaries of a master stay a band in size). The iris is not touched: the canvas is drawn first
and the iris is pasted over it.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..matter import ParticleLayer
from ..singles import kit as K
from . import common as CM

F32 = np.float32
NP = {
    "grid": 1536,                 # cells of the gas grid on the long side at most (a 4096 master: a 1366 grid, factor 3)
    "warp": 0.085,                # the domain warp, share of S
    "cells": (1.45, 3.4, 2.3),    # first octave cells across the padded grid: gas, filaments, dust
    "expo": 2.0,                  # the exponential stretch of the gas density (bright cores, dark gaps)
    "gas": 1.05,                  # strength of the gas
    "fil": 0.85,                  # how much the filaments add to the gas
    "illum": (0.30, 1.55, 0.95),  # the light of the iris on the gas: floor, strength at the limb, e-fold (R)
    "dust": (1.7, 0.56, 0.26),    # optical depth of the dust lanes, the field level where they start, their softness
    "rim": 0.22,                  # the lit edges of the dust facing the iris
    "glow": (0.60, 0.055, 0.50, 0.40),  # the light behind the iris: close strength, close e-fold (R), body strength, body e-fold (R)
    "partner": 1.45,              # the self light of the partner gas (it is not lit by the iris: it glows by itself, dimmer)
    "cavity": 0.30,               # the gas rises over this distance from the limb (R)
    "stars": (5200, (0.0, 8.0)),  # field stars per S^2 and their magnitudes
    "cluster": (90, 0.55),        # stars of the young cluster round the iris, and its e-fold distance beyond the limb (R)
    "sparkle": 16,                # the brightest stars that carry four short spikes
    "ground": (0.070, 0.016),     # the faint sky: centre and corner shares of the partner colour
    "extra": ((2, 1.3), (2, 1.3)),  # the finer octaves only a master draws (count, the gain of each over the octave before): the gas, the filaments
    "grain": 0.010,
}
BAND = 128                        # grid rows a band of the composition holds


def colours(iris):
    """The nebula's colours of one eye: own (warm glow and the inner gas), partner (the outer clouds), hot (the lit dust edges)."""
    h, c, fam = CM.eye_hue(iris)
    stp = CM.stops(iris, white=0.32)
    ph, how = CM.partner_hue(iris)
    own = CM.own_colour(iris, 66.0, 36.0, 62.0, 1.9)
    if 80.0 <= ph <= 112.0:                               # an olive or yellow partner turns toward gold (never a muddy olive cloud)
        ph -= 14.0
    part = CM.lch_rgb(52.0, 60.0 if fam != "grey" else 52.0, ph)
    hot = (0.50 * CM.mean_colour(stp, 2) + 0.30 * own + 0.20).astype(F32)
    return {"stops": stp, "own": own, "partner": part, "hot": hot, "partner_hue": round(float(ph), 1), "how": how, "family": fam}


def _fields(gw, gh, f, S, o, ctx):
    """The four noise fields of the gas on the whole grid (a warped lookup reads its neighbours): the gas density with its exponential stretch, the
    ridged filaments, the dust field and the slow field that sets where the partner colour takes over."""
    pad = CM.pad_of(gw, gh, 0.10)
    amp = F32(o["warp"] * S / f)
    wx = CM.fbm(gw, gh, 1.8, ctx.rand("nebula_wx"), 4, 0.5) - F32(0.5)
    wy = CM.fbm(gw, gh, 1.8, ctx.rand("nebula_wy"), 4, 0.5) - F32(0.5)
    cg, cf, cd = o["cells"]
    xg, xf = o["extra"]
    gas = CM.warp_pad(CM.stretch01(CM.fbm_master(gw + 2 * pad, gh + 2 * pad, cg, ctx.rand("nebula_g"), 7, 0.56, S, xg[0], xg[1], 0.10), 0.01, 0.995),
                      pad, wx, wy, amp, gw, gh)
    ex = F32(o["expo"])
    gas *= ex
    np.exp(gas, out=gas)
    gas -= F32(1.0)
    gas *= F32(1.0 / (math.exp(float(ex)) - 1.0))
    fil = CM.ridge(CM.warp_pad(CM.stretch01(CM.fbm_master(gw + 2 * pad, gh + 2 * pad, cf, ctx.rand("nebula_f"), 5, 0.55, S, xf[0], xf[1], 0.10)),
                               pad, wx, wy, amp * F32(0.75), gw, gh), 3.0)
    # the dust: soft clouds of a warped field, few fine octaves (soft lanes, never crumbs)
    dust_f = CM.warp_pad(CM.stretch01(CM.fbm_pad(gw, gh, pad, cd, ctx.rand("nebula_d"), 6, 0.52)), pad, -wy, wx, amp * F32(1.2), gw, gh)
    del wx, wy
    q = CM.smooth((CM.stretch01(CM.fbm(gw, gh, 1.0, ctx.rand("nebula_q"), 3, 0.5)) - F32(0.28)) / F32(0.50))
    return gas, fil, dust_f, q


def fx_nebula(cv, ctx):
    o = dict(NP)
    o.update(ctx.opts.get("nebula", {}))
    discs, irises = ctx.discs, ctx.irises
    W, H, S = ctx.W, ctx.H, ctx.S
    cols = [colours(ir) for ir in irises]
    f = CM.grid_factor(W, H, o["grid"])
    g = C.Grid(W, H, f)
    gw, gh = g.w, g.h
    x, y = CM.grid_xy(g)
    gas, fil, dust_f, q = _fields(gw, gh, f, S, o, ctx)
    th0 = float(ctx.rand("nebula_side").uniform() * CM.TWO_PI)
    i0, i1, il = o["illum"]
    kd, d0, ds = o["dust"]
    gk, gl, bk, bl = o["glow"]
    g0, g1 = o["ground"]
    trans = np.empty((gh, gw), F32)                                     # the dust in front of the stars, read again below
    light = np.empty((gh, gw, 3), F32)
    # ---- the composition, the dust and the glow, one band of grid rows at a time (every term below is pointwise but the dust's lit edge, which reads
    # the whole dust field): the temporaries of a 4096 px master stay a band in size
    for r0 in range(0, gh, BAND):
        r1 = min(gh, r0 + BAND)
        yb = y[r0:r1]
        # where each eye's light reaches: the distance to the nearest disc (its own R units) and a soft share per disc (a pair blends its colours)
        rho_l, th_l = [], []
        for d in discs:
            r_, t_ = CM.polar_of(x, yb, d)
            rho_l.append(r_)
            th_l.append(t_)
        rho = rho_l[0].copy()
        for r_ in rho_l[1:]:
            np.minimum(rho, r_, out=rho)
        if len(discs) > 1:
            wts = [np.exp(-(r_ - rho) * F32(2.2)) for r_ in rho_l]
            tot = sum(wts)
            wts = [w_ / tot for w_ in wts]
        else:
            wts = [np.ones_like(rho)]

        def mixc(key):
            out = np.zeros(rho.shape + (3,), F32)
            for w_, c_ in zip(wts, cols):
                out += w_[..., None] * c_[key][None, None, :]
            return out
        gas_b, fil_b, dust_b, q_b = gas[r0:r1], fil[r0:r1], dust_f[r0:r1], q[r0:r1]
        # a cleared cavity round each iris, the gas brightest round it and fading toward the corners, one side of the sky denser
        cav = F32(0.45) + F32(0.55) * CM.smooth((rho - F32(1.0)) / F32(o["cavity"]))
        side = F32(1.0) + F32(0.30) * np.cos(th_l[0] - F32(th0))
        illum = (F32(i0) + F32(i1) * np.exp(-(rho - F32(1.0)) / F32(il)) * side).astype(F32)   # the iris lights the gas round it
        env = (cav * illum).astype(F32)
        inner = np.exp(-(rho - F32(1.0)) / F32(0.45))                   # the own colour rules near the iris, the partner further out
        w_part = np.clip(F32(0.55) + F32(0.60) * q_b - F32(1.20) * inner, 0.0, 1.0)
        dens = (F32(o["gas"]) * gas_b * (F32(0.50) + F32(o["fil"]) * fil_b)).astype(F32)
        l_own = dens * env * (F32(1.0) - w_part)                        # the own gas: lit by the iris
        l_par = dens * cav * F32(o["partner"]) * (F32(0.75) + F32(0.25) * side) * w_part * (F32(0.55) + F32(0.45) * np.exp(-(rho - F32(1.0)) / F32(2.2)))
        # the dust: soft lanes that darken the gas, their edges facing the iris lit (sampled a little toward the nearest disc)
        dd = CM.smooth((dust_b - F32(d0)) / F32(ds)) ** F32(1.4)
        ncx = np.full(rho.shape, discs[0].cx, F32)                      # the centre and radius of the nearest disc at every grid pixel
        ncy = np.full(rho.shape, discs[0].cy, F32)
        nR = np.full(rho.shape, discs[0].R, F32)
        for k_, d in enumerate(discs[1:], 1):
            m_ = rho_l[k_] <= rho
            ncx[m_], ncy[m_], nR[m_] = d.cx, d.cy, d.R
        dist = np.maximum(rho * nR, F32(1e-3))
        step = F32(0.05) * nR / F32(f)
        xs = np.arange(gw, dtype=F32)[None, :] - (x - ncx) / dist * step
        ys = np.arange(r0, r1, dtype=F32)[:, None] - (yb - ncy) / dist * step
        dd_in = CM.smooth((CM.bilerp(dust_f, xs, ys) - F32(d0)) / F32(ds)) ** F32(1.4)
        rim = (np.clip(dd - dd_in, 0.0, 1.0) * F32(o["rim"]) * env * (F32(0.35) + F32(1.2) * gas_b)).astype(F32)
        tau = F32(kd) * dd * CM.smooth((rho - F32(1.10)) / F32(0.40))
        trans[r0:r1] = np.exp(-tau)
        # the warm glow at each limb, in the ring's own colour at each angle, broken a little by the gas
        glow = np.zeros(rho.shape + (3,), F32)
        brk = F32(0.55) + F32(0.9) * np.sqrt(gas_b)
        for k_, d in enumerate(discs):
            r_, t_ = rho_l[k_], th_l[k_]
            e = np.maximum(r_ - F32(1.0), F32(0.0))
            I = (F32(gk) * np.exp(-e / F32(gl)) * (F32(0.75) + F32(0.25) * brk) + F32(bk) * np.exp(-e / F32(bl)) * brk) * CM.smooth((r_ - F32(0.985)) / F32(0.03))
            lvl = np.clip(I / F32(0.75), 0.0, 1.0)
            glow += CM.ramp3(cols[k_]["stops"], t_, lvl) * I[..., None]
        # the light of the band: gas (own and partner) over the faint sky, through the dust, the lit dust edges, the glow
        lb = mixc("own") * l_own[..., None]
        lb += mixc("partner") * l_par[..., None]
        lb += CM.ground_grid(g, discs[0].cx, discs[0].cy, cols[0]["partner"] * F32(g0), cols[0]["partner"] * F32(g1), rows=(r0, r1))
        lb *= trans[r0:r1][..., None]
        lb += rim[..., None] * mixc("hot")
        lb += glow
        light[r0:r1] = lb
    del gas, fil, dust_f, q
    fade_soft = lambda band, r0: (K.wall_fade(band, ctx, y0=r0), K.text_fade(band, ctx, y0=r0))   # noqa: E731  the gas runs to the canvas edge
    CM.screen_grid(cv, light, f, "add", fade_soft)
    del light
    # ---- stars: the field (dimmed by the dust in front of them), the young cluster round the iris, spikes on the brightest
    def trans_at(px, py):
        gi = np.clip((np.asarray(py) / f).astype(np.int64), 0, gh - 1)
        gj = np.clip((np.asarray(px) / f).astype(np.int64), 0, gw - 1)
        return trans[gi, gj]
    layer = ParticleLayer()
    dens, mags = o["stars"]
    fx_, fy_, ff_, fc_ = CM.starfield(ctx, layer, ctx.rand("nebula_stars"), dens, mags, sigma_S=0.00042, peak=1.5, avoid=CM.avoid_discs(discs, 1.0),
                                      trans=trans_at, eps=0.05)
    rs = ctx.rand("nebula_cluster")
    n_c, efold = o["cluster"]
    cx_, cy_, cf_, cc_ = [], [], [], []
    for d in discs:
        n = int(n_c)
        e = rs.exponential(n, efold) + 0.05
        t = rs.uniform(n) * CM.TWO_PI
        px = d.cx + (1.0 + e) * d.R * np.cos(t)
        py = d.cy + (1.0 + e) * d.R * np.sin(t)
        mag = CM.magnitudes(rs, n, 0.0, 6.0, 0.42)
        fl = CM.stretch_flux(10.0 ** (-0.4 * mag), 0.04) * trans_at(px, py)
        col_ = CM.star_colour(8000.0 + 7000.0 * rs.uniform(n))
        cx_.append(px), cy_.append(py), cf_.append(fl), cc_.append(col_)
    cx_, cy_, cf_, cc_ = np.concatenate(cx_), np.concatenate(cy_), np.concatenate(cf_), np.concatenate(cc_)
    layer.splat(cx_, cy_, 0.00036 * S, cc_, (1.5 * cf_).astype(F32), min_sigma=0.5)
    layer.splat(cx_, cy_, 0.0012 * S, cc_, (0.10 * cf_ ** 2).astype(F32), min_sigma=0.5)
    layer.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0)))
    nsp = int(o["sparkle"])
    oc = np.argsort(-cf_)[:max(2, nsp // 4)]
    bx = np.concatenate([fx_[:nsp], cx_[oc]])
    by = np.concatenate([fy_[:nsp], cy_[oc]])
    bf = np.concatenate([ff_[:nsp], cf_[oc]])
    bc = np.concatenate([fc_[:nsp], cc_[oc]])
    CM.spikes(cv, ctx, bx, by, 0.006 + 0.024 * np.clip(bf, 0, 1) ** 2, bc, 0.55 * np.clip(bf, 0.25, 1.0), angle=0.0)
    del trans
    if o["grain"]:
        CM.grain(cv, ctx.rand("nebula_grain"), o["grain"])
    ctx.log["nebula"] = {"factor": f, "partner_hue": [c_["partner_hue"] for c_ in cols], "how": [c_["how"] for c_ in cols], "family": [c_["family"] for c_ in cols]}
