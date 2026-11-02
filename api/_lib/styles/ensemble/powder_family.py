# -*- coding: utf-8 -*-
"""styles.ensemble.powder_family: POWDER FAMILY, the light family's Powder Burst (lumen/dust.py, the owner's "A variantas" of 2026-10-28) round three to eight WHOLE
irises on one ring, the owner's pick of the boards of 2026-11-01 ("not bad"; the pair of that round was dropped): every iris turns into dust of its own colours,
thrown furthest toward the middle, where the family's grains meet and mix in one shared cloud.

Every grain is dust.py's: it takes the colour of a point of its iris's outer band (0.80 to 0.98 R, at its own angle), lies outside the limb at a distance from
a soft hump (further in some directions than in others: a periodic noise round the circle), dimmer the further it is, in three sizes; a share lies right at
the limb, dimmed, so no dark seam separates an iris from its dust. What is new is the throw toward the family's centre: a share of the grains leaves in that
direction, the reach of a grain is multiplied by 1 + throw x (cos of its angle to it)^power (positive half only), and its fade stretched with it, so the far grains
still read. A wider ring throws further. A grain that falls on another iris is dropped (it would be hidden under it anyway, but not under its feather).

The irises stay whole: the grains are drawn into the float canvas only and every iris is pasted last (base.render), byte for byte inside 0.974 R, with dust.py's
finish (no dark limbal ring, the edge mode: no glass rim). Every length in R, counts independent of the canvas, every random number drawn for all grains
before any filter: a 4096 px master is the 1024 px preview drawn finer.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from .. import matter as M
from ..lumen import dust as D
from ..singles import kit as K
from .base import Plan
from .spiral import FIN, family_fmt, ring_layout

F32 = np.float32
TWO_PI = 2.0 * math.pi
PF = {
    "n": 90000,              # grains per iris (dust.py's 80000 and the stream toward the middle)
    "bright": 0.98,          # dust.py's 0.88, a touch lighter: the grains spread over a larger field
    "throw": (2.2, 1.6),     # toward the family's centre: reach x (1 + a cos^p); a is scaled up on a wider ring
    "fade_k": 1.1,           # how much of the throw also stretches the fade
    "aim": (0.34, 0.45),     # share of the grains aimed at the centre, the spread of their angles (rad)
    "ring_gap": 0.62,        # between neighbours on the ring (R)
    "core_free": 0.75,       # free radius of the middle: from the centre to the nearest limb (R)
}


def plan_powder_family(n, fmt, o):
    """n irises evenly on a ring (Light Circle's rule with this look's gaps), the dust's room round them; from five eyes the wide canvases lay the ring flatter."""
    p = dict(PF)
    p.update(o.get("powder") or {})
    gap = min(float(p["ring_gap"]), {7: 0.30, 8: 0.16}.get(n, 9.0))      # seven and eight eyes: closer, so each stays 22 percent of the width (T18)
    q = {"3:2": 0.72, "5:4": 0.86}.get(fmt, 1.0) if n >= 5 else 1.0
    cs, r, centre, rho = ring_layout(n, fmt, gap, float(p["core_free"]), 0.42, q)
    return Plan(fmt, [(x, y, r) for x, y in cs], {"centre": centre, "rho_r": rho})


def _grains(d, rnd, lob_rnd, o, toward, others):
    """dust.py's grains round one disc, thrown further toward the angle `toward` (radians). Returns (px, py, br, cls)."""
    R = float(d.R)
    n = int(o["n"])
    th = rnd.uniform(n) * TWO_PI
    u = rnd.uniform(n)
    aim_u = rnd.uniform(n)
    aim_n = rnd.normal(n, 0.0, 1.0)
    share_a, sig_a = o["aim"]
    th = np.where(aim_u < share_a, (toward + sig_a * aim_n) % TWO_PI, th)       # a share of the grains leaves toward the middle: the stream that meets
    s0, s1 = o["src"]
    rs = s1 - (s1 - s0) * u ** 2.2
    col = K.sample_disc(d, rs, th).reshape(n, 3).astype(F32)
    k = float(o["shape"])
    share, near_mean, near_dim = o["near"]
    g_ = rnd.gamma(n, k, o["reach"] / k)
    near_u = rnd.uniform(n)
    near_d = rnd.exponential(n, near_mean)
    jit_ = rnd.normal(n, 0.0, o["jitter"])
    b_u = rnd.uniform(n)
    cls = rnd.uniform(n)
    keep = col.mean(1) > 0.04
    th, rs, col, g_, near_u, near_d, jit_, b_u, cls = (v[keep] for v in (th, rs, col, g_, near_u, near_d, jit_, b_u, cls))
    lob = C.periodic_fbm1d(2048, lob_rnd, 5, 4)
    reach_a = o["lobes"][0] + o["lobes"][1] * lob[(th / TWO_PI * 2048).astype(np.int64) % 2048]
    ta, tp = o["throw"]
    c = np.maximum(np.cos(th - toward), 0.0) ** tp
    thr = 1.0 + ta * c
    dist = g_ * reach_a * thr * (0.4 + 0.9 * (rs - s0) / (s1 - s0))
    near = near_u < share
    dist = np.where(near, near_d, dist)
    rd = o["start"] + dist
    jit = jit_ * (0.3 + dist / o["reach"])
    a = th + jit
    px = d.cx + rd * R * np.cos(a)
    py = d.cy + rd * R * np.sin(a)
    fade = np.exp(-dist / (o["reach"] * o["fade"] * (1.0 + float(o["fade_k"]) * (thr - 1.0))))
    br = col * (o["bright"] * (0.55 + 0.9 * b_u) * fade * np.where(near, near_dim, 1.0))[:, None]
    br = np.clip(br, 0.0, 1.0).astype(F32)
    ok = np.ones(len(px), bool)
    for e in others:
        ok &= np.hypot(px - e.cx, py - e.cy) > 0.99 * float(e.R)
    return px[ok], py[ok], br[ok], cls[ok]


def fx_powder_family(cv, ctx):
    o = dict(D.DP)
    o.update(PF)
    o.update(ctx.opts.get("powder") or {})
    ds = ctx.discs
    cx, cy = ctx.plan.info["centre"]
    cx, cy = cx * ctx.k, cy * ctx.k
    ta, tp = o["throw"]
    o["throw"] = (ta * max(1.0, (float(ctx.plan.info["rho_r"]) - 1.0) / 0.85), tp)      # a wider ring throws further: the dust meets in the middle
    layer = M.ParticleLayer()
    total = 0
    for i, d in enumerate(ds):
        toward = math.atan2(cy - d.cy, cx - d.cx)
        px, py, br, cls = _grains(d, ctx.rand("powder", i), ctx.rand("powder_lobes", i), o, toward, [e for j, e in enumerate(ds) if j != i])
        total += len(px)
        lo = 0.0
        R = float(d.R)
        for hi, sig, gain in o["sizes"]:
            sel = (cls >= lo) & (cls < hi)
            lo = hi
            if sel.any():
                layer.splat(px[sel], py[sel], sig * R, br[sel], np.full(int(sel.sum()), gain * 0.5), min_sigma=0.5)
    layer.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0)))
    ctx.log["powder"] = {"grains": int(total)}


FAMILY_CANVASES = ("3:2", "1:1", "5:4", "4:5")
POWDER_FAMILY = {"n": (3, 8), "fmt": family_fmt, "canvases": FAMILY_CANVASES, "plan": plan_powder_family, "fx": fx_powder_family, "bg": "#000000", "group": "grp",
                 "fin": FIN}
