# -*- coding: utf-8 -*-
"""styles.ensemble.spiral: GALAXY DUO and GALAXY FAMILY, the light family's Spiral Galaxy (lumen/galaxy.py, live since 2026-10-30) round two to eight WHOLE
irises. A laboratory look of 2026-11-01 (branch fx-cosmic): boards for the owner, no registry style yet.

  galaxy_duo     the two irises as the double core of one barred spiral galaxy: they sit at the two ends of a short bar of light, and each sends out one arm
                 of its own colours (a two armed logarithmic spiral whose arms rise from the irises); a warm glow round each limb meets in the gap
  galaxy_family  the family as one galaxy: a warm core of light in the middle, the irises evenly on a ring round it (an inclined ring, an ellipse, on the
                 wide canvases), one arm per person that winds out of the core, through that person's iris and on beyond it, in that person's colours

Every piece is the single look's: the eye's own two colours per angle (galaxy._eye_pair: the outer band and the collarette, lifted to light), the arm profile
(a logarithmic spiral of a fixed pitch, a power of a cosine), clumps and dust lanes from value noise in the unwound coordinates, stars accepted where the arm
is, knots on the crests, a field of stars and a few spike stars. What changes is the frame: the galaxy has its own centre (between the two irises, or the
family's core), its own unit (the iris radius R), an inclination (the wide canvases see the disc tilted, an ellipse) and one arm per eye, each arm in the
colours of its own eye (von Mises weights on the arm phase).

The irises stay whole: the light is drawn into the float canvas only and every iris is pasted last (base.render), byte for byte inside 0.974 R, with the
finish of the single look (no dark limbal ring, the edge mode: no glass rim). No light starts inside 1.0 R of an iris that is not covered by it; the stars start
at 1.03 R, the spike stars beyond 1.25 R. Every length is in R, every count independent of the canvas, every random number drawn before any filter: a
4096 px master is the 1024 px preview drawn finer.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from .. import matter as M
from ..collision import scenes as CS
from ..lumen import common as CM
from ..lumen import galaxy as G
from ..singles import kit as K
from .base import Plan

F32 = np.float32
TWO_PI = 2.0 * math.pi
FIN = {"limb": (0.78, 0.0), "edge": 0.985}          # the single look's iris finish (lumen DESIGN_FIN["galaxy"])

GD = {                       # Galaxy Duo
    "gap": 0.42,             # limb to limb (R)
    "r": 0.185,              # the iris radius, share of S (3:2)
    "q": 0.78,               # the inclination on the wide canvases: the disc's minor axis over its major axis
    "pitch": 16.0,
    "sharp": 3.0,
    "reach": 3.7,            # the galaxy's radius from its centre (R)
    "disc": 1.0,             # the disc's e-fold length (R) beyond the irises
    "arm_light": 1.4,
    "inter": 0.07,
    "bulge": ((0.12, 0.16), (0.38, 0.20)),
    "bar": (0.34, 0.16),     # the bar between the irises: half width (R), light
    "lane": (0.50, 0.90, 4.0),
    "clump_cells": 30.0,
    "clump": (0.05, 1.6, 2.2),
    "iso": 0.45,
    "stars": (260000, 0.0012, 3.0),
    "star_floor": 0.06,
    "star_pow": 2.0,
    "star_mag": 3.0,
    "knots": (420, 0.0040, 1.6),
    "field": 110.0,
    "bright": (6, 0.030),
}
GF = {                       # Galaxy Family
    "gap": 0.30,             # between neighbours on the ring (R)
    "core_free": 0.80,       # free radius of the core: from the centre to the nearest limb (R)
    "halo": 1.05,            # room beyond the ring for the arms (R)
    "q": {"3:2": 0.64, "5:4": 0.80, "1:1": 1.0, "4:5": 1.0},
    "pitch": 27.0,
    "sharp": 2.6,
    "reach": 1.55,           # the galaxy's radius as a multiple of the ring radius
    "disc": 0.55,            # the disc's e-fold length as a share of the ring radius
    "arm_light": 1.0,
    "inter": 0.06,
    "core": ((0.10, 0.55), (0.30, 0.22)),   # the core glow: (e-fold as a share of the ring radius, light) twice
    "bulge": ((0.10, 0.12), (0.30, 0.14)),
    "lane": (0.50, 0.85, 4.0),
    "clump_cells": 30.0,
    "clump": (0.05, 1.6, 2.2),
    "iso": 0.45,
    "stars": (190000, 0.0012, 3.0),
    "star_floor": 0.06,
    "star_pow": 2.0,
    "star_mag": 3.0,
    "knots": (500, 0.0040, 1.6),
    "field": 110.0,
    "bright": (6, 0.030),
}


# ----------------------------------------------------------------------------- plans
def _axis(fmt):
    return {"3:2": 0.0, "5:4": 0.0, "1:1": 0.0, "4:5": 90.0, "9:19.5": 90.0}.get(fmt, 0.0)


def plan_galaxy_duo(n, fmt, o):
    """Two irises on the galaxy's major axis (horizontal on the wide canvases, vertical on the tall ones), `gap` R apart, the bar's centre at the canvas'."""
    W, H = CS.canvas_size(fmt, 1024)
    S = min(W, H)
    p = dict(GD)
    p.update(o.get("galaxy_duo") or {})
    gap = float(p["gap"])
    ax = math.radians(_axis(fmt))
    u = (math.cos(ax), math.sin(ax))
    R = float(p["r"]) * S * (1.0 if fmt in ("3:2", "5:4") else 0.92)
    cx, cy = W / 2.0, H / 2.0
    off = R * (1.0 + gap / 2.0)
    q = float(p["q"]) if fmt in ("3:2", "5:4", "9:19.5", "4:5") else 1.0
    return Plan(fmt, [(cx - u[0] * off, cy - u[1] * off, R), (cx + u[0] * off, cy + u[1] * off, R)],
                {"centre": (cx, cy), "rot": math.degrees(ax), "q": q, "gap": gap})


def family_fmt(n):
    return "1:1" if n >= 5 else "3:2"


def plan_galaxy_family(n, fmt, o):
    """n irises evenly on a ring round the galaxy's core (in the galaxy's plane; an ellipse on the canvas when the disc is inclined): neighbours at least
    `gap` R apart, the core at least `core_free` R from every limb, the arms' room `halo` R beyond the ring."""
    W, H = CS.canvas_size(fmt, 1024)
    p = dict(GF)
    p.update(o.get("galaxy_family") or {})
    qd = p["q"]
    q = float(qd.get(fmt, 1.0)) if isinstance(qd, dict) else float(qd)
    gap = min(float(p["gap"]), {7: 0.30, 8: 0.16}.get(n, 9.0))           # seven and eight eyes: closer, so each stays 22 percent of the width (T18)
    start = -90.0 if n % 2 == 1 else -90.0 + 180.0 / n
    th = [math.radians(start + 360.0 * i / n) for i in range(n)]
    unit = [(math.cos(t), q * math.sin(t)) for t in th]
    dmin = min(math.hypot(unit[i][0] - unit[(i + 1) % n][0], unit[i][1] - unit[(i + 1) % n][1]) for i in range(n))
    if n >= 3:
        dmin = min(dmin, min(math.hypot(unit[i][0] - unit[j][0], unit[i][1] - unit[j][1]) for i in range(n) for j in range(i + 1, n)))
    near = min(math.hypot(x, y) for x, y in unit)
    rho = max((2.0 + gap) / dmin, (1.0 + float(p["core_free"])) / near)
    pts = [(rho * x, rho * y) for x, y in unit]
    halo = min(float(p["halo"]), {3: 0.50, 4: 0.90, 5: 0.80, 6: 0.70, 7: 0.0, 8: 0.0}.get(n, 9.0))   # the bigger families give the arms' room to the irises (T18: D >= 0.22 W)
    xs0, xs1 = min(x for x, _ in pts) - 1.0 - halo, max(x for x, _ in pts) + 1.0 + halo
    ys0, ys1 = min(y for _, y in pts) - 1.0 - halo * q, max(y for _, y in pts) + 1.0 + halo * q
    r = min(0.97 * W / (xs1 - xs0), 0.96 * H / (ys1 - ys0), ring_fit(pts, W, H))
    ox, oy = W / 2.0 - (xs0 + xs1) / 2.0 * r, H / 2.0 - (ys0 + ys1) / 2.0 * r
    return Plan(fmt, [(ox + x * r, oy + y * r, r) for x, y in pts], {"centre": (ox, oy), "rot": 0.0, "q": q, "rho_r": rho})


def ring_fit(pts, W, H, margin=0.056):
    """The largest iris radius (px) at which the irises of a ring (centres pts in R) keep `margin` S from every canvas edge (T8: 0.05 S, with room for
    the caption's shrink)."""
    S = min(W, H)
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    return min((W - 2.0 * margin * S) / (max(xs) - min(xs) + 2.0), (H - 2.0 * margin * S) / (max(ys) - min(ys) + 2.0))


# ----------------------------------------------------------------------------- the frame of the galaxy
class _Shim:
    """What galaxy._eye_pair reads: one disc, one iris."""

    def __init__(self, d, iris):
        self.discs, self.irises = [d], [iris]


class Frame:
    """The galaxy's plane: centre (canvas px), unit U (px, the iris radius), inclination q, rotation rot (deg). to_plane maps canvas offsets to (rho, th)."""

    def __init__(self, cx, cy, U, q, rot):
        self.cx, self.cy, self.U, self.q = float(cx), float(cy), float(U), float(q)
        self.c, self.s = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def plane(self, X, Y):
        dx, dy = np.asarray(X, np.float64) - self.cx, np.asarray(Y, np.float64) - self.cy
        gx = (dx * self.c + dy * self.s) / self.U
        gy = (-dx * self.s + dy * self.c) / (self.U * self.q)
        return gx, gy

    def canvas(self, rho, th):
        gx, gy = rho * np.cos(th), rho * np.sin(th) * self.q
        return self.cx + (gx * self.c - gy * self.s) * self.U, self.cy + (gx * self.s + gy * self.c) * self.U


def _field(rnd, L, n, cells, gain):
    """galaxy._Field stretched once by its own 2 and 98 percent quantiles (the single look stretches each lookup; here the light is drawn in bands, and a
    stretch of the texture itself is the same for every band and every canvas size)."""
    fl = G._Field(rnd, L=L, n=n, cells=cells, octaves=4, gain=gain)
    fl.a = CM.stretch01(fl.a, 0.02, 0.98, sample=2)
    return fl


def _weights(th, lnr, k, crests, kappa):
    """(m, ...) von Mises weights of each arm at the points (th, ln rho): which eye's arm a point belongs to."""
    w = np.stack([np.exp(kappa * (np.cos(th - k * lnr - c) - 1.0)) for c in crests]).astype(F32)
    w /= np.maximum(w.sum(0, keepdims=True), F32(1e-6))
    return w


def _galaxy(cv, ctx, o, fr, rho0, crests, inner_r, kind):
    """The galaxy round the irises. fr: its Frame; rho0: the radius (R) where the arms pass through the iris centres; crests: the angles of the irises in the
    galaxy's plane (one arm each, evenly spaced); inner_r: where the arms begin (R); kind: "duo" (a bulge round each iris and a bar between) or "family" (a
    core of light in the middle)."""
    ds, irs = ctx.discs, ctx.irises
    m = len(crests)
    W, H, S = ctx.W, ctx.H, ctx.S
    R = float(ds[0].R)
    rnd = ctx.rand("spiral")
    pairs = [G._eye_pair(_Shim(d, ir)) for d, ir in zip(ds, irs)]
    stps = [CM.stops(ir) for ir in irs]
    k = 1.0 / math.tan(math.radians(o["pitch"]))
    kappa = 1.6 * m
    reach = float(o["reach"])
    L_d = float(o["disc"])
    near_k = float(o.get("near_k", 1.0))
    # ---- every draw first
    ns, sig_s, b_s = o["stars"]
    nk, sig_k, b_k = o["knots"]
    ns, nk = int(ns), int(nk)
    u_r, u_t, u_a, u_m, u_j = rnd.uniform(ns), rnd.uniform(ns) * TWO_PI, rnd.uniform(ns), rnd.uniform(ns), rnd.normal(ns, 0.0, 1.0)
    k_r, k_t, k_a, k_s = rnd.uniform(nk * 6), rnd.uniform(nk * 6) * TWO_PI, rnd.uniform(nk * 6), rnd.uniform(nk * 6)
    b_u, b_v, b_m = rnd.uniform(16), rnd.uniform(16), rnd.uniform(16)
    Lf = reach + 0.6
    nf = int(min(1536, max(512, round(150.0 * Lf))))                     # 75 grid px per R, as the single look's field (512 over 6.8 R)
    clumps = _field(ctx.rand("spiral_clumps"), Lf, nf, o["clump_cells"] * Lf / 3.4, 0.55)
    lanes = _field(ctx.rand("spiral_lanes"), Lf, nf, o["clump_cells"] * 1.6 * Lf / 3.4, 0.6)
    Li = 1.7 * reach + 0.8                                                  # the knots that do not follow the spiral: read at 1.7 x, so a field that wide
    iso = _field(ctx.rand("spiral_iso"), Li, int(min(2048, max(512, round(150.0 * Li / 1.7)))), o["clump_cells"] * Li / 3.4 / 1.7, 0.55)

    def arm_of(rho, th):
        lnr = np.log(np.maximum(rho, 1e-3) / rho0)
        psi = m * (th - k * lnr - crests[0])
        return (0.5 + 0.5 * np.cos(psi)) ** o["sharp"], psi, lnr

    def envelope(rho, e_near=None):
        """The disc's light: e-fold L_d from inner_r (the family's core) or, for the duo, from the nearest limb (e_near, R), so the arms are brightest
        where they leave their irises; nothing beyond the galaxy's reach."""
        if e_near is None:
            e = np.maximum(rho - inner_r, 0.0)
        elif kind == "duo":
            e = np.maximum(e_near, 0.0)
        else:                                                   # the family: bright at the core and again where each arm passes its iris
            e = np.minimum(np.maximum(rho - inner_r, 0.0), np.maximum(e_near, 0.0) * near_k)
        return (np.exp(-e / L_d) * (1.0 - CM.smooth((rho - reach * 0.75) / (reach * 0.35)))).astype(F32)

    def near_limb(X, Y):
        return np.min(np.stack([np.hypot(X - d.cx, Y - d.cy) / R - 1.0 for d in ds]), 0)

    def rise(rho):
        return CM.smooth((rho - inner_r) / (0.35 if kind == "duo" else 0.5 * inner_r + 1e-3)).astype(F32)

    # ---- the soft light on the grid (1024 cells on the long side)
    f = max(1, int(round(max(W, H) / 1024.0)))
    g = C.Grid(W, H, f)
    light = np.zeros((g.h, g.w, 3), F32)
    xg, yg = CM.grid_xy(g)
    for r0 in range(0, g.h, 128):
        r1 = min(g.h, r0 + 128)
        X = np.broadcast_to(xg, (r1 - r0, g.w))
        Y = np.broadcast_to(yg[r0:r1], (r1 - r0, g.w))
        gx, gy = fr.plane(X, Y)
        rho = np.sqrt(gx * gx + gy * gy).astype(F32)
        th = np.arctan2(gy, gx).astype(F32)
        if not (rho < reach + 0.3).any():
            continue
        arm, psi, lnr = arm_of(rho, th)
        tu = th - k * np.log(np.maximum(rho, 1e-3))
        ux, uy = rho * np.cos(tu) * 0.85, rho * np.sin(tu) * 0.85
        cl = clumps.at(ux, uy)
        if o["iso"] > 0:
            ci = iso.at(rho * np.cos(th) * 1.7 + 0.31, rho * np.sin(th) * 1.7 - 0.27)
            cl = cl * (1.0 - o["iso"]) + ci * o["iso"]
        ln = lanes.at(ux, uy)
        lag, depth, lsharp = o["lane"]
        lane = (0.5 + 0.5 * np.cos(psi + lag)) ** lsharp * CM.smooth((ln - 0.25) / 0.4)
        env = envelope(rho, near_limb(X, Y))
        c0_, c1_, cp_ = o["clump"]
        I = o["arm_light"] * arm * env * (c0_ + c1_ * cl ** cp_) * rise(rho) + o["inter"] * env
        I = I * (1.0 - depth * lane * CM.smooth((rho - inner_r - 0.08) / 0.15))
        w = _weights(th, lnr, k, crests, kappa)
        col = np.zeros(rho.shape + (3,), F32)
        hot = np.zeros(rho.shape + (3,), F32)
        bul = np.zeros(rho.shape + (3,), F32)
        (l1, b1), (l2, b2) = o["bulge"]
        for j, d in enumerate(ds):
            a_j = np.arctan2(Y - d.cy, X - d.cx)
            oc = G._at_angle(pairs[j][0], a_j)
            col += oc * w[j][..., None]
            e_j = np.maximum(np.hypot(X - d.cx, Y - d.cy) / R - 1.0, 0.0)
            hc = G._at_angle(stps[j][2], a_j)
            hot += hc * w[j][..., None]
            bul += hc * (b1 * np.exp(-e_j / l1)).astype(F32)[..., None] + oc * (b2 * np.exp(-e_j / l2)).astype(F32)[..., None]
        band = col * I[..., None] + bul
        if kind == "duo":
            hw, bl = o["bar"]
            along = np.clip(gx / rho0 * 0.5 + 0.5, 0.0, 1.0)[..., None]       # 0 at the first iris, 1 at the second
            bc = G._at_angle(stps[0][2], np.zeros(1))[0] * (1.0 - along) + G._at_angle(stps[1][2], np.full(1, math.pi))[0] * along
            bar = bl * np.exp(-(gy / hw) ** 2) * (1.0 - CM.smooth((np.abs(gx) - rho0) / 0.6))
            band += bc * bar.astype(F32)[..., None]
        else:
            (c1, cb1), (c2, cb2) = o["core"]
            rr = float(rho0)
            warm = np.array([1.0, 0.93, 0.80], F32)
            mh = np.mean([st[2].mean(0) for st in stps], 0).astype(F32)            # the family's mean hot colour: the very core is everyone's
            sc = (1.0 - CM.smooth((rho - 0.10 * rr) / (0.30 * rr))).astype(F32)[..., None]
            hot = hot * (1.0 - sc) + mh * sc
            band += (warm * 0.5 + hot * 0.5) * (cb1 * np.exp(-rho / (c1 * rr))).astype(F32)[..., None]
            band += hot * (cb2 * np.exp(-rho / (c2 * rr))).astype(F32)[..., None]
        light[r0:r1] = band
    CM.screen_grid(cv, light, f, "screen", CM.fades_for(ctx))
    del light
    # ---- stars along the arms, knots on the crests, a field of stars, a few spike stars
    rr = inner_r * 0.8 + (reach - inner_r * 0.8) * u_r ** 1.25
    a_s, _psi, lnr_s = arm_of(rr, u_t)
    sx, sy = fr.canvas(rr, u_t + u_j * 0.02 / np.maximum(rr, 0.3))
    acc = u_a < (o["star_floor"] + (1.0 - o["star_floor"]) * a_s ** o["star_pow"]) * envelope(rr, near_limb(sx, sy)) * np.maximum(rise(rr), 0.15)
    ws = _weights(u_t, lnr_s, k, crests, kappa)
    owner = np.argmax(ws, 0)
    cs = np.zeros((ns, 3), F32)
    for j, d in enumerate(ds):
        sel = owner == j
        cs[sel] = G._at_angle(stps[j][2], np.arctan2(sy[sel] - d.cy, sx[sel] - d.cx))
    white = np.array([1.0, 0.97, 0.92], F32)
    scol = (cs * (0.5 + 0.5 * u_m[:, None]) + white * (0.5 - 0.5 * u_m[:, None])).astype(F32)
    mag = 0.18 + 0.82 * (u_m ** o["star_mag"])
    clear = np.ones(ns, bool)
    for d in ds:
        clear &= np.hypot(sx - d.cx, sy - d.cy) > 1.03 * R
    acc &= clear
    layer = M.ParticleLayer()
    layer.splat(sx[acc], sy[acc], sig_s * R, scol[acc], (b_s * mag[acc]).astype(F32), min_sigma=0.5)
    kr = inner_r + (reach * 0.8 - inner_r) * k_r
    a_k, _pk, lnr_k = arm_of(kr, k_t)
    kx, ky = fr.canvas(kr, k_t)
    kacc = k_a < a_k ** 2 * envelope(kr, near_limb(kx, ky))
    for d in ds:
        kacc &= np.hypot(kx - d.cx, ky - d.cy) > 1.15 * R
    wk = _weights(k_t, lnr_k, k, crests, kappa)
    ok = np.argmax(wk, 0)
    kc = np.zeros((len(k_t), 3), F32)
    for j, d in enumerate(ds):
        sel_j = ok == j
        kc[sel_j] = G._at_angle(pairs[j][1], np.arctan2(ky[sel_j] - d.cy, kx[sel_j] - d.cx))
    ksz = sig_k * (0.5 + 1.0 * k_s)
    sel = np.nonzero(kacc)[0][:nk]
    layer.splat(kx[sel], ky[sel], ksz[sel] * R, kc[sel], (b_k * (0.4 + 0.6 * k_s[sel])).astype(F32), min_sigma=0.5)
    layer.splat(kx[sel], ky[sel], ksz[sel] * R * 0.3, np.ones((len(sel), 3), F32), (b_k * 0.8 * k_s[sel]).astype(F32), min_sigma=0.5)
    CM.starfield(ctx, layer, ctx.rand("spiral_field"), o["field"], mags=(1.0, 7.5), avoid=CM.avoid_discs(ds, 1.05))
    fades = (lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0))
    layer.flush(cv, fades=fades)
    nb, arm_b = o["bright"]
    if nb > 0:
        bx, by = b_u[:int(nb)] * W, b_v[:int(nb)] * H
        far = np.ones(int(nb), bool)
        for d in ds:
            far &= np.hypot(bx - d.cx, by - d.cy) > 1.25 * R
        near_j = np.argmin(np.stack([np.hypot(bx - d.cx, by - d.cy) for d in ds]), 0)
        bc = np.stack([np.array([1.0, 0.96, 0.9], F32) * 0.5 + G._at_angle(stps[near_j[i]][2], np.array([math.atan2(by[i] - ds[near_j[i]].cy, bx[i] - ds[near_j[i]].cx)]))[0] * 0.5
                       for i in range(int(nb))]).astype(F32)
        bm = 0.5 + 0.5 * b_m[:int(nb)]
        layer2 = M.ParticleLayer()
        layer2.splat(bx[far], by[far], 0.0016 * S, bc[far], (2.0 * bm[far]).astype(F32), min_sigma=0.5)
        layer2.flush(cv, fades=fades)
        CM.spikes(cv, ctx, bx[far], by[far], arm_b * bm[far], bc[far], 0.9 * bm[far], width_S=0.0005, angle=0.3)
    ctx.log["spiral"] = {"kind": kind, "arms": m, "stars": int(acc.sum()), "knots": int(len(sel)), "grid": [g.w, g.h]}


def fx_galaxy_duo(cv, ctx):
    o = dict(GD)
    o.update(ctx.opts.get("galaxy_duo") or {})
    info = ctx.plan.info
    cx, cy = info["centre"]
    ds = ctx.discs
    R = float(ds[0].R)
    fr = Frame(cx * ctx.k, cy * ctx.k, R, info["q"], info["rot"])
    gxy = [fr.plane(d.cx, d.cy) for d in ds]
    rho0 = float(np.mean([math.hypot(float(x), float(y)) for x, y in gxy]))
    crests = [math.atan2(float(y), float(x)) for x, y in gxy]                # the first iris at pi, the second at 0
    _galaxy(cv, ctx, o, fr, rho0, crests, rho0, "duo")


def fx_galaxy_family(cv, ctx):
    o = dict(GF)
    o.update(ctx.opts.get("galaxy_family") or {})
    info = ctx.plan.info
    cx, cy = info["centre"]
    ds = ctx.discs
    R = float(ds[0].R)
    fr = Frame(cx * ctx.k, cy * ctx.k, R, info["q"], info["rot"])
    gxy = [fr.plane(d.cx, d.cy) for d in ds]
    rho0 = float(np.mean([math.hypot(float(x), float(y)) for x, y in gxy]))
    crests = [math.atan2(float(y), float(x)) for x, y in gxy]
    o["reach"] = float(o["reach"]) * rho0
    o["disc"] = float(o["disc"]) * rho0
    _galaxy(cv, ctx, o, fr, rho0, crests, 0.18 * rho0, "family")


DUO_CANVASES = ("3:2", "5:4", "1:1", "4:5", "9:19.5")
FAMILY_CANVASES = ("3:2", "1:1", "5:4", "4:5")
GALAXY_DUO = {"n": (2, 2), "fmt": lambda n: "3:2", "canvases": DUO_CANVASES, "plan": plan_galaxy_duo, "fx": fx_galaxy_duo, "bg": "#000000",
              "group": "duo", "fin": FIN}
GALAXY_FAMILY = {"n": (3, 8), "fmt": family_fmt, "canvases": FAMILY_CANVASES, "plan": plan_galaxy_family, "fx": fx_galaxy_family, "bg": "#000000",
                 "group": "grp", "fin": FIN}
