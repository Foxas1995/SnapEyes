# -*- coding: utf-8 -*-
"""styles.ensemble.light_circle: LIGHT CIRCLE, the owner's old 2026-09-30 "Light Circle" (7 of 10 on his family board) in today's engine: three to eight WHOLE
irises of one size stand evenly on a circle round one small light, a white star in a thin aureole (the centre the owner approved on 2026-10-20); each person's
own colour is a faint aura. Calm: pure black ground, nothing else. The ring is as wide as the layout allows (neighbours 0.18 R apart, never fewer than 0.9 R of
free centre) and the aureole takes half of the free centre. Everything is drawn before the irises are pasted: nothing touches an iris or a pupil. No plate,
no model. Ported from the laboratory (proto_pf/lightcircle.py, 2026-10-20); the one change: with the customer's words the light moves with the irises (the
laboratory's caption rule moved the discs and left the light where it was)."""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..collision import scenes as CS
from . import pieces as P
from .base import Plan

F32 = np.float32
TWO_PI = 2.0 * math.pi


def plan_light_circle(n, fmt, o):
    W, H = CS.canvas_size(fmt, 1024)
    gap = float(o.get("gap", 0.18))
    # ring radius in iris radii: neighbours `gap` R apart, and at least 1.9 R (three eyes keep room for the light)
    rho = max((2.0 + gap) / (2.0 * math.sin(math.pi / n)), float(o.get("rho_min", 1.9)))
    start = -90.0 if n % 2 == 1 else -90.0 + 180.0 / n
    pts = [(rho * math.cos(math.radians(start + 360.0 * i / n)), rho * math.sin(math.radians(start + 360.0 * i / n))) for i in range(n)]
    xs0, xs1 = min(p[0] for p in pts) - 1.0, max(p[0] for p in pts) + 1.0
    ys0, ys1 = min(p[1] for p in pts) - 1.0, max(p[1] for p in pts) + 1.0
    halo = 0.35
    r = min(0.94 * W / (xs1 - xs0 + 2 * halo), 0.92 * H / (ys1 - ys0 + 2 * halo))
    ox, oy = W / 2.0 - (xs0 + xs1) / 2.0 * r, 0.5 * H - (ys0 + ys1) / 2.0 * r
    discs = [(ox + x * r, oy + y * r, r) for x, y in pts]
    return Plan(fmt, discs, {"rho_r": rho, "centre": (ox, oy), "r": r})


def default_fmt(n):
    return "1:1"


def fx_light_circle(cv, ctx):
    W, H, S = ctx.W, ctx.H, ctx.S
    ds = ctx.discs
    ox, oy = ctx.plan.info["centre"]
    ox, oy = ox * ctx.k, oy * ctx.k
    r = ds[0].R
    rho = math.hypot(ds[0].cx - ox, ds[0].cy - oy)
    cv[:] = C.rgb01(ctx.opts.get("ground", "#020203"))[None, None, :]
    cols = [P.own_colour(ir, 1.25, 1.35) for ir in ctx.irises]
    for d, c in zip(ds, cols):
        P.aura(cv, d, c, float(ctx.opts.get("aura", 0.16)), 0.14, reach=2.2)
    free = rho - r
    a = float(ctx.opts.get("aureole", 0.52)) * free                        # the aureole takes half of the free centre
    # the light: a soft disc of warm white inside the aureole, a hairline aureole, a four point star at the middle
    x0, y0, x1, y1 = int(max(0, ox - 1.4 * a)), int(max(0, oy - 1.4 * a)), int(min(W, ox + 1.4 * a)), int(min(H, oy + 1.4 * a))
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    rr = np.hypot(xx + 0.5 - ox, yy + 0.5 - oy) / a
    glow = np.exp(-(rr / 0.55) ** 2) * 0.55 + np.exp(-rr / 0.25) * 0.20
    glow *= 1.0 - P.smooth((rr - 0.96) / 0.08)
    cv[y0:y1, x0:x1] += glow[..., None] * C.rgb01("#FFEFD2")[None, None, :] * F32(0.62)
    sig = 0.0012 * S * 0.5 + 0.2
    P.ring_line(cv, ox, oy, a, sig, C.rgb01("#F2E3C6"), 0.62, glow=0.10)
    P.sparkle(cv, ox, oy, 0.62 * a, C.rgb01("#FFF8EA"), 0.95, 0.011 * a, core=0.70)
    P.sparkle(cv, ox, oy, 0.34 * a, C.rgb01("#FFF8EA"), 0.55, 0.011 * a, angle=math.radians(45.0), core=0.0)
    for d in ds:
        P.eclipse_gap(cv, d, 0.030)
    ctx.log["light_circle"] = {"n": len(ds), "rho_over_r": round(ctx.plan.info["rho_r"], 3), "aureole_over_r": round(a / r, 3)}


LOOK = {"n": (3, 8), "fmt": default_fmt, "canvases": ("1:1", "4:5"), "plan": plan_light_circle, "fx": fx_light_circle, "bg": "#020203", "group": "grp"}
