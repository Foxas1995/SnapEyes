# -*- coding: utf-8 -*-
"""DUST (the light family; Powder Burst since 2026-10-28, the owner: "A variantas", after his references of 2026-10-27, where the explosion is the iris's
own colour turning into dust round it, compact, on black, and "more around the iris, not spoiling it; the iris itself touched by a few pixels at most").

The iris stays whole (the engine pastes it last, byte for byte inside 0.974 R, with the family's F3 feather at the limb). Round it, grains of its own colour:
each grain takes the colour of a point of the iris's outer band (0.80 to 0.98 R, at the grain's own angle) and lies outside the limb at a distance drawn from
a soft hump (most of them a fifth of R out, a few far), further in some directions than in others (a periodic noise round the circle), dimmer the further
it is. A small share lies right at the limb, dimmed, so that no dark seam separates the iris from its dust; no ring of light, no plate, no cloud. Three
sizes of grain (many fine, some medium, a few bold) and a faint glow of the same grains, so the dust reads as light and not as noise.

Every length is in R (the iris radius) or S, and the counts do not depend on the canvas: a 4096 px master is the 1024 px preview drawn finer.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from .. import matter as M
from ..singles import kit as K

F32 = np.float32
TWO_PI = 2.0 * math.pi
DP = {
    "n": 80000,                 # grains
    "src": (0.80, 0.98),        # the band of the iris whose colours the grains take (R)
    "start": 0.996,             # the grains start at the limb (R)
    "reach": 0.20,              # the mean distance beyond the start (R): a gamma hump of shape `shape`
    "shape": 2.2,
    "near": (0.12, 0.024, 0.5),  # share of the grains right at the limb, their mean distance (R) and their brightness: no dark seam, no ring
    "fade": 3.0,                # brightness falls as exp(-d / (reach x fade))
    "lobes": (0.55, 0.90),      # the reach per angle: base + amp x a periodic noise (some directions throw further)
    "jitter": 0.012,            # angular scatter (rad), growing with the distance
    "bright": 0.88,             # grain light over the iris colour it came from (the owner's board A)
    "sizes": ((0.72, 0.0013, 0.9), (0.95, 0.0030, 1.3), (1.01, 0.0055, 1.9)),   # (upper bound of the class draw, sigma in R, gain)
    "glow": (0.0, 0.040),       # the faint glow of the grains: weight, sigma in R (off: the owner's board was grains, not light)
}


def fx_dust(cv, ctx):
    o = dict(DP)
    o.update(ctx.opts.get("dust", {}))
    d = ctx.discs[0]
    R = float(d.R)
    rnd = ctx.rand("dust")
    n = int(o["n"])
    th = rnd.uniform(n) * TWO_PI
    u = rnd.uniform(n)
    s0, s1 = o["src"]
    rs = s1 - (s1 - s0) * u ** 2.2                                         # mostly from the outermost band
    col = K.sample_disc(d, rs, th).reshape(n, 3).astype(F32)
    k = float(o["shape"])
    share, near_mean, near_dim = o["near"]
    # every grain's draws are made for all n grains BEFORE the filter below: the colour a grain samples differs a little between a 480 px tile, the 1024 px
    # preview and the 4096 px master, so the filter keeps a different count at each size, and draws of the kept count would reshuffle every grain after the
    # first one dropped. Drawn first, a grain lies at the same place at every size and a master is its preview drawn finer
    g_ = rnd.gamma(n, k, o["reach"] / k)
    near_u = rnd.uniform(n)
    near_d = rnd.exponential(n, near_mean)
    jit_ = rnd.normal(n, 0.0, o["jitter"])
    b_u = rnd.uniform(n)
    cls = rnd.uniform(n)
    keep = col.mean(1) > 0.04                                              # no grain from a crypt or a lash shadow
    th, rs, col, g_, near_u, near_d, jit_, b_u, cls = (v[keep] for v in (th, rs, col, g_, near_u, near_d, jit_, b_u, cls))
    m = len(th)
    lob = C.periodic_fbm1d(2048, ctx.rand("dust_lobes"), 5, 4)
    reach_a = o["lobes"][0] + o["lobes"][1] * lob[(th / TWO_PI * 2048).astype(np.int64) % 2048]
    dist = g_ * reach_a * (0.4 + 0.9 * (rs - s0) / (s1 - s0))
    near = near_u < share
    dist = np.where(near, near_d, dist)
    rd = o["start"] + dist
    jit = jit_ * (0.3 + dist / o["reach"])
    a = th + jit
    px = d.cx + rd * R * np.cos(a)
    py = d.cy + rd * R * np.sin(a)
    fade = np.exp(-dist / (o["reach"] * o["fade"]))
    br = col * (o["bright"] * (0.55 + 0.9 * b_u) * fade * np.where(near, near_dim, 1.0))[:, None]
    br = np.clip(br, 0.0, 1.0).astype(F32)
    layer = M.ParticleLayer()
    lo = 0.0
    for hi, sig, gain in o["sizes"]:
        sel = (cls >= lo) & (cls < hi)
        lo = hi
        if sel.any():
            layer.splat(px[sel], py[sel], sig * R, br[sel], np.full(int(sel.sum()), gain * 0.5), min_sigma=0.5)
    gw, gs = o["glow"]
    if gw > 0:
        layer.splat(px[::7], py[::7], gs * R, br[::7], np.full(len(px[::7]), gw), min_sigma=0.5)
    layer.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0)))
    ctx.log["dust"] = {"n": int(m), "near": int(near.sum())}
