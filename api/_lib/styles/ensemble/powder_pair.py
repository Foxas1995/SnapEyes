# -*- coding: utf-8 -*-
"""styles.ensemble.powder_pair: POWDER DUO and POWDER FAMILY, the light family's Powder Burst (lumen/dust.py, the owner's "A variantas" of 2026-10-28) round two
to eight WHOLE irises. A laboratory look of 2026-11-01 (branch fx-cosmic): boards for the owner, no registry style yet.

  powder_duo     two irises side by side, each turning into dust of its own colours round it (dust.py's grains, unchanged in size, colour and light); toward
                 the partner the dust is thrown further, so the two clouds meet in the gap and their grains mix there, blue among brown
  powder_family  three to eight irises on one ring, each in its own dust, thrown furthest toward the middle, where the family's grains meet and mix in one
                 shared cloud

Every grain is dust.py's: it takes the colour of a point of its iris's outer band (0.80 to 0.98 R, at its own angle), lies outside the limb at a distance from
a soft hump (further in some directions than in others: a periodic noise round the circle), dimmer the further it is, in three sizes; a share lies right at
the limb, dimmed, so no dark seam separates an iris from its dust. What is new is the throw toward the partner (or the family's centre): the reach of a grain
is multiplied by 1 + throw x (cos of its angle to that direction)^power (positive half only), and its fade stretched with it, so the far grains still read.
A grain that falls on another iris is dropped (it would be hidden under it anyway, but not under its feather).

The irises stay whole: the grains are drawn into the float canvas only and every iris is pasted last (base.render), byte for byte inside 0.974 R, with dust.py's
finish (no dark limbal ring, the edge mode: no glass rim). Every length in R, counts independent of the canvas, every random number drawn for all grains
before any filter: a 4096 px master is the 1024 px preview drawn finer.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from .. import matter as M
from ..collision import scenes as CS
from ..lumen import dust as D
from ..singles import kit as K
from .base import Plan
from .spiral import FIN, family_fmt, ring_fit

F32 = np.float32
TWO_PI = 2.0 * math.pi
PD = {                       # Powder Duo (dust.py's DP plus the throw)
    "gap": 0.60,             # limb to limb (R)
    "r": 0.245,              # the iris radius, share of S (3:2)
    "n": 110000,             # grains per iris (dust.py's 80000 and the stream toward the partner)
    "bright": 0.98,          # dust.py's 0.88, a touch lighter: the grains spread over a larger field
    "throw": (2.6, 1.6),     # toward the partner: reach x (1 + a cos^p)
    "fade_k": 0.8,           # how much of the throw also stretches the fade
    "stars": 0.0,            # field stars per S^2 (0: pure black, the owner's board A)
    "aim": (0.40, 0.45),     # share of the grains aimed at the partner, the spread of their angles (rad)
}
PF = dict(PD, throw=(2.2, 1.6), n=90000, aim=(0.34, 0.45), ring_gap=0.62, core_free=0.75)


def plan_powder_duo(n, fmt, o):
    W, H = CS.canvas_size(fmt, 1024)
    S = min(W, H)
    p = dict(PD)
    p.update(o.get("powder") or {})
    gap = float(p["gap"])
    vert = fmt in ("4:5", "9:19.5")
    R = float(p["r"]) * S * (1.0 if fmt in ("3:2", "5:4") else 0.80)
    cx, cy = W / 2.0, H / 2.0
    off = R * (1.0 + gap / 2.0)
    if vert:
        return Plan(fmt, [(cx, cy - off, R), (cx, cy + off, R)], {"centre": (cx, cy), "gap": gap})
    return Plan(fmt, [(cx - off, cy, R), (cx + off, cy, R)], {"centre": (cx, cy), "gap": gap})


def plan_powder_family(n, fmt, o):
    """n irises evenly on a ring (Light Circle's rule with this look's gaps), the dust's room round them."""
    W, H = CS.canvas_size(fmt, 1024)
    p = dict(PF)
    p.update(o.get("powder") or {})
    gap = min(float(p["ring_gap"]), {7: 0.30, 8: 0.16}.get(n, 9.0))      # seven and eight eyes: closer, so each stays 22 percent of the width (T18)
    rho = max((2.0 + gap) / (2.0 * math.sin(math.pi / n)), 1.0 + float(p["core_free"]))
    start = -90.0 if n % 2 == 1 else -90.0 + 180.0 / n
    pts = [(rho * math.cos(math.radians(start + 360.0 * i / n)), rho * math.sin(math.radians(start + 360.0 * i / n))) for i in range(n)]
    halo = 0.42
    xs0, xs1 = min(x for x, _ in pts) - 1.0 - halo, max(x for x, _ in pts) + 1.0 + halo
    ys0, ys1 = min(y for _, y in pts) - 1.0 - halo, max(y for _, y in pts) + 1.0 + halo
    r = min(0.97 * W / (xs1 - xs0), 0.97 * H / (ys1 - ys0)) if n < 7 else ring_fit(pts, W, H)   # seven and eight: only the T8 margin
    ox, oy = W / 2.0 - (xs0 + xs1) / 2.0 * r, H / 2.0 - (ys0 + ys1) / 2.0 * r
    return Plan(fmt, [(ox + x * r, oy + y * r, r) for x, y in pts], {"centre": (ox, oy), "rho_r": rho})


def _grains(d, rnd, lob_rnd, o, toward, others):
    """dust.py's grains round one disc, thrown further toward the angle `toward` (radians). Returns (px, py, br, cls)."""
    R = float(d.R)
    n = int(o["n"])
    th = rnd.uniform(n) * TWO_PI
    u = rnd.uniform(n)
    aim_u = rnd.uniform(n)
    aim_n = rnd.normal(n, 0.0, 1.0)
    share_a, sig_a = o["aim"]
    th = np.where(aim_u < share_a, (toward + sig_a * aim_n) % TWO_PI, th)       # a share of the grains leaves toward the partner: the stream that meets
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


def fx_powder(cv, ctx):
    o = dict(D.DP)
    o.update(PD if len(ctx.discs) == 2 else PF)
    o.update(ctx.opts.get("powder") or {})
    ds = ctx.discs
    cx, cy = ctx.plan.info["centre"]
    cx, cy = cx * ctx.k, cy * ctx.k
    layer = M.ParticleLayer()
    total = 0
    for i, d in enumerate(ds):
        if len(ds) == 2:
            e = ds[1 - i]
            toward = math.atan2(e.cy - d.cy, e.cx - d.cx)
        else:
            toward = math.atan2(cy - d.cy, cx - d.cx)
            ta, tp = o["throw"]
            o["throw"] = (PF["throw"][0] * max(1.0, (float(ctx.plan.info["rho_r"]) - 1.0) / 1.2), tp)   # a wider ring throws further: the dust meets in the middle
        px, py, br, cls = _grains(d, ctx.rand("powder", i), ctx.rand("powder_lobes", i), o, toward, [e for j, e in enumerate(ds) if j != i])
        total += len(px)
        lo = 0.0
        R = float(d.R)
        for hi, sig, gain in o["sizes"]:
            sel = (cls >= lo) & (cls < hi)
            lo = hi
            if sel.any():
                layer.splat(px[sel], py[sel], sig * R, br[sel], np.full(int(sel.sum()), gain * 0.5), min_sigma=0.5)
    if o.get("stars", 0.0) > 0:
        from ..lumen import common as CM
        CM.starfield(ctx, layer, ctx.rand("powder_field"), float(o["stars"]), mags=(2.0, 7.5), avoid=CM.avoid_discs(ds, 1.05))
    layer.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0)))
    ctx.log["powder"] = {"grains": int(total)}


DUO_CANVASES = ("3:2", "5:4", "1:1", "4:5", "9:19.5")
FAMILY_CANVASES = ("3:2", "1:1", "5:4", "4:5")
POWDER_DUO = {"n": (2, 2), "fmt": lambda n: "3:2", "canvases": DUO_CANVASES, "plan": plan_powder_duo, "fx": fx_powder, "bg": "#000000", "group": "duo",
              "fin": FIN}
POWDER_FAMILY = {"n": (3, 8), "fmt": family_fmt, "canvases": FAMILY_CANVASES, "plan": plan_powder_family, "fx": fx_powder, "bg": "#000000", "group": "grp",
                 "fin": FIN}
