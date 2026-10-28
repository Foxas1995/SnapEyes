# -*- coding: utf-8 -*-
"""SPARKS (the light family; embers since 2026-10-28, after the owner's word on the old look: streaks across the whole canvas, uneven and noisy, bokeh,
the iris pasted on; he wants the effect round the iris, compact, on black, and the iris untouched but for a few pixels at the limb).

The iris is a coal and its embers rise on a gentle wind. The iris stays whole (the engine pastes it last, byte for byte inside 0.974 R, with the family's
F3 feather at the limb; its own finish keeps a light limbal ring, DESIGN_FIN). Every ember is born AT the limb, at an angle drawn from a density a little
higher on the wind side, and flies along the streamlines of an air current that flows round the iris (the potential flow past a disc, a uniform wind plus
its doublet) with the lift of its own heat near the limb and a slow lateral wobble, so the embers born low stream round the sides and the plume rises over
the top: they move outward round the iris and never across it (a point of a path that would come nearer than 1.004 R is put back on that circle). An
ember is drawn as the last stretch of its own path (a short trail, motion blur) ending in a hot head: the trail cools from the deep tone of its colour to
the colour, the head goes toward white. Its colour is the iris's own at the angle it left (a point of the band 0.50 to 0.93 R, its saturation lifted a
little and brought to full brightness), so a blue green eye throws cyan and yellow embers and a brown one copper. Most embers are short and dim, a few
bright, a twentieth are heroes with three times the trail; the brightness fades with the distance flown. A dust of tiny glints smoulders on the limb, so
no dark seam separates the iris from its embers; no ring of light, no plate, no cloud, no bokeh.

Every length is in R (the iris radius), the counts do not depend on the canvas and every random number is drawn for all embers before anything that
depends on the canvas size (the colour an ember samples differs a little between a tile, the preview and the master; nothing is filtered on it), so a
4096 px master is the 1024 px preview drawn finer: the paths are the same in R, only the number of stamps along a trail follows its length in pixels.
"""
from __future__ import annotations

import math

import numpy as np

from .. import matter as M
from ..singles import kit as K

F32 = np.float32
TWO_PI = 2.0 * math.pi
SQ2PI = math.sqrt(2.0 * math.pi)
SP = {
    "n": 1150,                  # embers
    "wind": (-105.0, -75.0),    # the wind's direction, a seeded angle in this range (deg, 0 = 3 o'clock, clockwise: -90 is straight up)
    "bias": 0.35,               # birth density round the limb: 1 + bias x cos(angle - wind) (a little more on the wind side)
    "flight": (0.32, 1.3),      # the distance an ember has flown (R): a gamma of this mean and shape (most near the limb, a few far)
    "heat": (1.5, 0.18, 0.22),  # the lift off the limb: strength, e-fold (R) and the constant outward drift that widens the plume (over a wind of 1)
    "wobble": (0.10, 0.22),     # the lateral wobble of a path: amplitude (over the wind) and period (R)
    "steps": 48,                # the integration steps of a path (its length / steps each)
    "trail": (0.02, 0.09),      # the drawn trail (R): uniform in this range, never longer than the path
    "hero": (0.05, 3.2, 1.3),   # the share of hero embers, their trail and brightness factors
    "sigma": (0.0012, 0.0036),  # the trail's stroke sigma (R): most fine, a few bold (u^3)
    "light": (5.5, 3.0),        # the brightness of a trail and the exponent of its spread (most dim, a few bright)
    "fade": 2.2,                # brightness falls as exp(-flight / (mean flight x fade))
    "hot": 0.45,                # how far the hottest heads go toward white
    "head": (2.6, 0.8, 0.5),    # the head of a bright ember: sigma over the trail's, brightness, the share of embers that have one (the brightest)
    "bloom": (0.020, 0.02, 0.6),  # the soft light round the brighter heads: sigma (R), brightness, the share that has it
    "src": (0.50, 0.93),        # the band of the iris whose colours the embers take (R)
    "colour": (1.25, 0.30),     # the colour lift: saturation, the brightness floor before a colour is brought to full brightness
    "smoulder": (2600, 0.030, 1.2, 0.0012),   # the glints on the limb: count, mean distance (R), brightness, sigma (R)
    "start": 1.004,             # the limb the embers leave and never come nearer than (R)
}


def _own(col, sat, floor):
    """The iris's own colour as light: its saturation lifted, brought to full brightness (a dark sample stays darker, under the floor)."""
    m = col.mean(1, keepdims=True)
    c = np.clip(m + (col - m) * sat, 0.0, None)
    return np.clip(c / np.maximum(c.max(1, keepdims=True), floor), 0.0, 1.0).astype(F32)


def _angles(u, dens):
    """Angles of the circular density dens (bins round the circle) from the uniforms u, by its inverse distribution: no rejection, no extra draw."""
    nb = len(dens)
    cdf = np.concatenate([[0.0], np.cumsum(dens)])
    cdf /= cdf[-1]
    return np.interp(u, cdf, np.linspace(0.0, TWO_PI, nb + 1))


def _trails(layer, d, X, Y, prof, col, hot, sig, amp, mmax=480):
    """Stamps along every path (X, Y: (n, k) in R round the centre, tail first): <= 0.7 sigma apart, so they always join into a line, each carrying the
    line's brightness amp x prof over its own length (a trail is as bright at 1024 px as at 4096). The colour runs from the deep tone of col at the tail
    to col, the head toward white by hot."""
    R = float(d.R)
    n, k = X.shape
    if n == 0:
        return
    Lr = np.maximum(np.hypot(np.diff(X, axis=1), np.diff(Y, axis=1)).sum(1), 1e-6)
    sp = sig * R
    m = np.clip(np.ceil(Lr * R / (0.7 * np.maximum(sp, 0.5))), 2, mmax).astype(np.int64)
    m = (np.ceil(m / 8.0) * 8).astype(np.int64)                 # whole groups of eight, one vectorised pass per group
    deep = (col ** 1.5).astype(F32)
    for mv in np.unique(m):
        sel = np.nonzero(m == mv)[0]
        u = (np.arange(mv) + 0.5) / mv
        f = u * (k - 1)
        i0 = np.minimum(np.floor(f).astype(np.int64), k - 2)
        w = (f - i0)[None, :]
        xs = X[sel][:, i0] * (1 - w) + X[sel][:, i0 + 1] * w
        ys = Y[sel][:, i0] * (1 - w) + Y[sel][:, i0 + 1] * w
        pr = prof[sel][:, i0] * (1 - w) + prof[sel][:, i0 + 1] * w
        a = amp[sel][:, None] * pr * (Lr[sel] * R / mv)[:, None] / (sp[sel][:, None] * SQ2PI)
        t = u[None, :, None]
        hh = hot[sel][:, None, None] * t ** 3
        cc = (deep[sel][:, None, :] * (1 - t) + col[sel][:, None, :] * t) * (1 - hh) + hh
        layer.splat((d.cx + xs * R).ravel(), (d.cy + ys * R).ravel(), np.repeat(sp[sel], mv), cc.reshape(-1, 3).astype(F32), a.ravel(), min_sigma=0.5)


def fx_sparks(cv, ctx):
    o = dict(SP)
    o.update(ctx.opts.get("sparks", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    rnd = ctx.rand("sparks")
    n = int(o["n"])
    ns = int(o["smoulder"][0])
    fm, fk = o["flight"]
    # every draw of every ember and glint is made here, before anything that depends on the canvas size (see the module's note)
    u_th = rnd.uniform(n)
    u_src = rnd.uniform(n)
    flown = rnd.gamma(n, fk, fm / fk)
    u_tr = rnd.uniform(n)
    u_b = rnd.uniform(n)
    u_s = rnd.uniform(n)
    ph = rnd.uniform(n) * TWO_PI
    u_hero = rnd.uniform(n)
    s_th = rnd.uniform(ns)
    s_d = rnd.exponential(ns, o["smoulder"][1])
    s_b = rnd.uniform(ns)
    s_src = rnd.uniform(ns)
    w0, w1 = o["wind"]
    wind = math.radians(w0 + (w1 - w0) * float(ctx.rand("sparks_wind").uniform()))
    grid = (np.arange(4096) + 0.5) / 4096 * TWO_PI
    dens = 1.0 + o["bias"] * np.cos(grid - wind)
    th0 = _angles(u_th, dens)
    # ---- the colours: the iris's own at the angle of birth
    s0, s1 = o["src"]
    sat, floor = o["colour"]
    col = _own(K.sample_disc(d, s1 - (s1 - s0) * u_src ** 1.5, th0).reshape(n, 3).astype(F32), sat, floor)
    # ---- the flight: streamlines of the wind round the disc (complex potential U (z + 1/z) in the wind's frame), the heat's lift, the wobble
    start = float(o["start"])
    ew = complex(math.cos(wind), math.sin(wind))
    hk, hl, hd = o["heat"]
    wa, wp = o["wobble"]
    kk = int(o["steps"])
    s_tot = 0.01 + flown
    ds = s_tot / (kk - 1)
    x, y = start * np.cos(th0), start * np.sin(th0)
    Xs = np.empty((n, kk))
    Ys = np.empty((n, kk))
    Xs[:, 0], Ys[:, 0] = x, y
    for j in range(1, kk):
        z = (x + 1j * y) / ew
        v = 1.0 - 1.0 / (z * z)                                 # u - i v of the flow past the unit disc in the wind's frame
        V = (v.real - 1j * v.imag) * ew
        r = np.hypot(x, y)
        lift = hk * np.exp(-(r - 1.0) / hl) + hd
        ux, uy = V.real + lift * x / r, V.imag + lift * y / r
        nn = np.maximum(np.hypot(ux, uy), 1e-9)
        ux, uy = ux / nn, uy / nn
        s = ds * j
        wb = wa * np.sin(ph + s * TWO_PI / wp) * np.minimum(s / 0.08, 1.0)
        ux, uy = ux - uy * wb, uy + ux * wb
        x, y = x + ux * ds, y + uy * ds
        k_ = np.maximum(start / np.hypot(x, y), 1.0)              # never nearer than the limb it left
        x, y = x * k_, y * k_
        Xs[:, j], Ys[:, j] = x, y
    # ---- the drawn trail: the last stretch of the path
    hs, ht, ha = o["hero"]
    hero = u_hero < hs
    lo, hi = o["trail"]
    tr = (lo + (hi - lo) * u_tr) * np.where(hero, ht, 1.0)
    f0 = 1.0 - np.minimum(tr, s_tot) / s_tot
    t = np.linspace(0.0, 1.0, 14)[None, :]
    f = (f0[:, None] + (1.0 - f0[:, None]) * t) * (kk - 1)
    i0 = np.minimum(np.floor(f).astype(np.int64), kk - 2)
    w = f - i0
    rows = np.arange(n)[:, None]
    X = Xs[rows, i0] * (1 - w) + Xs[rows, i0 + 1] * w
    Y = Ys[rows, i0] * (1 - w) + Ys[rows, i0 + 1] * w
    del Xs, Ys
    lk, le = o["light"]
    amp = lk * (0.25 + 0.75 * u_b ** le) * np.where(hero, ha, 1.0) * np.exp(-flown / (fm * o["fade"]))
    hot = o["hot"] * u_b ** 1.5
    g0, g1 = o["sigma"]
    sig = g0 + (g1 - g0) * u_s ** 3.0
    layer = M.ParticleLayer()
    _trails(layer, d, X, Y, np.broadcast_to(t ** 1.3, X.shape), col, hot, sig, amp)
    # ---- the heads of the brighter embers and their soft light
    R = float(d.R)
    hx, hy = d.cx + X[:, -1] * R, d.cy + Y[:, -1] * R
    sh, ah, qh = o["head"]
    sel = u_b > 1.0 - qh
    if sel.any():
        layer.splat(hx[sel], hy[sel], sig[sel] * sh * R, (col[sel] * (1 - hot[sel, None]) + hot[sel, None]).astype(F32), amp[sel] * ah, min_sigma=0.5)
    sb, ab, qb = o["bloom"]
    sel = u_b > 1.0 - qb
    if ab > 0 and sel.any():
        layer.splat(hx[sel], hy[sel], sb * R, col[sel], amp[sel] * ab, min_sigma=0.5)
    # ---- the smouldering limb: tiny glints of the iris's colours right on it, a little more on the wind side
    if ns:
        sth = _angles(s_th, dens)
        scol = _own(K.sample_disc(d, s1 - (s1 - s0) * s_src ** 1.5, sth).reshape(ns, 3).astype(F32), sat, floor)
        sm = float(o["smoulder"][1])
        rr = (start + s_d) * R
        sa = o["smoulder"][2] * (0.3 + 0.7 * s_b ** 2) * np.exp(-s_d / (2.0 * sm))
        layer.splat(d.cx + rr * np.cos(sth), d.cy + rr * np.sin(sth), o["smoulder"][3] * R, scol, sa, min_sigma=0.5)
    layer.flush(cv, fades=(lambda v_, r0: K.wall_fade(v_, ctx, y0=r0), lambda v_, r0: K.text_fade(v_, ctx, y0=r0), lambda v_, r0: K.edge_fade(v_, ctx, y0=r0)))
    ctx.log["sparks"] = {"class": iris.cls, "wind_deg": round(math.degrees(wind), 1), "n": [n, int(hero.sum()), ns]}
