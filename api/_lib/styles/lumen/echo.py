# -*- coding: utf-8 -*-
"""IRIS ECHO (the light family, the owner's choice of 2026-10-27: "daryk B, vadink Iris Echo", then "less zoom, more luxurious, like the competitors"):
the iris in the middle of its own echo. The ground is the same graded iris drawn ZOOM times larger round the same centre, so its fibres radiate from
behind the iris like a tunnel; the echo keeps its fibres (local contrast at the crypts' scale), is pushed a little toward the eye's own deep tone, darkened,
and falls to near black in a deep vignette; a soft shadow lifts the iris off its echo. Nothing but the eye's own pixels: no plate, no noise, no colour that
is not the eye's.

Drawn on a grid of at most GRID cells on the long side (the echo is the iris enlarged ZOOM times, so it holds no finer detail than that grid) and brought
up to the canvas with one bicubic resize; a 4096 master is the preview drawn on a finer grid with the same numbers in R and S units.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from .. import core as C
from ..singles import kit as K

F32 = np.float32
GRID = 1536
EP = {
    "zoom": 2.4,                # the echo is the iris this many times larger
    "clarity": (0.0138, 0.60),  # local contrast of the echo: sigma in S, amount
    "sat": 1.10,                # colour of the echo
    "deep": 0.30,               # share of the echo pushed toward the eye's own deep tone (its median x 0.45, with the echo's own light)
    "dark": 0.72,               # the echo's level
    "vig": (0.15, 0.30, 1.30, 1.6),   # the vignette: floor, inner and outer radius (in half S), power
    "shadow": (1.06, 0.06, 0.55),     # the iris lifts off its echo: radius, softness (in R), depth
}


def fx_echo(cv, ctx):
    o = dict(EP)
    o.update(ctx.opts.get("echo", {}))
    d = ctx.discs[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    f = max(1.0, max(W, H) / float(GRID))
    gw, gh = max(8, int(round(W / f))), max(8, int(round(H / f)))
    fx, fy = W / float(gw), H / float(gh)
    xs = (np.arange(gw, dtype=np.float64) + 0.5) * fx - d.cx
    ys = (np.arange(gh, dtype=np.float64) + 0.5) * fy - d.cy
    X, Y = np.meshgrid(xs, ys)
    dist = np.hypot(X, Y)
    rho = dist / R
    th = np.arctan2(Y, X)
    echo = K.sample_disc(d, rho / o["zoom"], th)                          # 0..1, the graded iris enlarged round its own centre
    sig, amt = o["clarity"]
    bl = C.blur(echo, max(0.6, sig * S / f), clip_negative=False)
    echo = echo + F32(amt) * (echo - bl)
    m = echo.mean(axis=2, keepdims=True)
    echo = m + (echo - m) * F32(o["sat"])
    deep = np.median(echo.reshape(-1, 3), axis=0).astype(F32) * F32(0.45)
    lum = echo.mean(axis=2, keepdims=True)
    echo = echo * F32(1.0 - o["deep"]) + deep[None, None, :] * (lum / F32(max(float(lum.mean()), 1e-4))) * F32(o["deep"])
    echo *= F32(o["dark"])
    v0, vi, vo, vp = o["vig"]
    dn = (dist / (S / 2.0)).astype(F32)
    echo *= (F32(v0) + F32(1.0 - v0) * np.clip((vo - dn) / (vo - vi), 0.0, 1.0) ** F32(vp))[..., None]
    sr, ss, sd = o["shadow"]
    sh = (1.0 - C.smoothstep((rho - (sr - ss)) / (2.0 * ss))).astype(F32)
    echo *= (1.0 - F32(sd) * sh)[..., None]
    np.clip(echo, 0.0, 1.0, out=echo)
    if (gw, gh) != (W, H):
        up = np.empty((H, W, 3), F32)
        for c in range(3):
            up[..., c] = np.asarray(Image.fromarray(np.ascontiguousarray(echo[..., c]), "F").resize((W, H), Image.BICUBIC), F32)
        echo = up
    np.clip(echo, 0.0, 1.0, out=echo)
    cv[:] = echo
    ctx.log["echo"] = {"zoom": o["zoom"], "grid": [gw, gh], "deep_rgb": [round(float(v), 3) for v in deep]}
