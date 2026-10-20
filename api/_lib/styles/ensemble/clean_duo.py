# -*- coding: utf-8 -*-
"""styles.ensemble.clean_duo: CLEAN DUO, the calm pair and the safest seller: two whole irises side by side on pure black, wrapped by ONE thin line that crosses
itself between them (an infinity drawn as two loops and the two short tangents that cross), a four point star on the crossing. Nothing else: no corona, no
powder, no dust, no stars. The irises never overlap (no seam, no weave, no front iris), so every colour pair is as good as every other.

The line is the belt of two pulleys: a circle of 1.10 R round each iris and the two internal common tangents of the two circles, which cross on the middle of the
line of centres. It is drawn before the irises are pasted and lies 0.10 R outside each limb; nothing is ever drawn over an iris or a pupil.

The thread is gold, as the owner saw it on the laboratory board of 2026-10-20 and liked it ("thread": "gold", the default). "thread": "tint" (the owner's
other option of the same day, shown beside it on the board, not the default) draws each loop and the half of each tangent next to it in gold turned 45 percent
toward that person's own eye colour (pieces.own_colour), so the line changes colour where it crosses, under the star. Ported from the laboratory
(proto_pf/clean_duo.py); the plan and the gold line are the laboratory's own."""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..collision import scenes as CS
from . import pieces as P
from .base import Plan

F32 = np.float32
GOLD = "#E6BE72"
TINT = 0.45                                  # how far the tinted thread turns toward the eye's own colour


def plan_clean_duo(n, fmt, o):
    W, H = CS.canvas_size(fmt, 1024)
    S = min(W, H)
    gap = float(o.get("gap", 0.34))
    rho = float(o.get("belt", 1.10))
    wall = fmt == "9:19.5"
    ax = {"3:2": 0.0, "5:4": 0.0, "1:1": 35.0, "4:5": 60.0, "9:19.5": 90.0}.get(fmt, 0.0)
    ax = float(o.get("axis_deg", ax))
    a = math.radians(ax)
    u = (math.cos(a), math.sin(a))
    c = 1.0 + gap / 2.0
    hx = c * abs(u[0]) + rho + 0.06
    hy = c * abs(u[1]) + rho + 0.06
    R = min(0.46 * W / hx, (0.36 if wall else 0.46) * H / hy)
    R = min(R, 0.30 * H if fmt in ("3:2", "5:4") else 0.5 * S)
    cx, cy = W / 2.0, (0.57 if wall else 0.5) * H
    off = R * c
    return Plan(fmt, [(cx - u[0] * off, cy - u[1] * off, R), (cx + u[0] * off, cy + u[1] * off, R)], {"axis_deg": ax, "gap": gap, "belt": rho, "c": c})


def thread_colours(ctx):
    """The colours of the line: (left, right) as rgb 0..1. Gold for both (the default), or each side gold turned toward its own eye's colour ("thread": "tint")."""
    gold = C.rgb01(ctx.opts.get("line", GOLD))
    if ctx.opts.get("thread", "gold") != "tint":
        return gold, gold
    t = float(ctx.opts.get("tint", TINT))
    out = []
    for ir in ctx.irises:
        own = P.own_colour(ir, 1.45, 1.40)
        # the tint keeps the gold line's brightness: the eye's colour sets the hue, the line its light
        lum = float(own @ np.array([0.299, 0.587, 0.114], np.float32))
        glum = float(gold @ np.array([0.299, 0.587, 0.114], np.float32))
        own = np.clip(own * (glum / max(lum, 1e-3)), 0.0, 1.0)
        out.append(np.clip(C.mix(gold, own, t), 0.0, 1.0).astype(np.float32))
    return out[0], out[1]


def fx_clean_duo(cv, ctx):
    W, H, S = ctx.W, ctx.H, ctx.S
    d0, d1 = ctx.discs
    R = d0.R
    info = ctx.plan.info
    cx, cy = (d0.cx + d1.cx) / 2.0, (d0.cy + d1.cy) / 2.0
    axis = math.atan2(d1.cy - d0.cy, d1.cx - d0.cx)
    c = math.hypot(d1.cx - d0.cx, d1.cy - d0.cy) / 2.0
    rho = float(info["belt"]) * R
    L = math.sqrt(c * c - rho * rho)
    th = math.asin(rho / c)
    ux, uy = math.cos(axis), math.sin(axis)

    def scr(x, y):
        return cx + x * ux - y * uy, cy + x * uy + y * ux
    cv[:] = C.rgb01(ctx.opts.get("ground", "#020203"))[None, None, :]
    left, right = thread_colours(ctx)
    sig = float(ctx.opts.get("stroke", 0.0014)) * S * 0.5
    peak = float(ctx.opts.get("peak", 0.88))
    # the two loops (the far side of each circle) and the two tangents that cross on the middle of the line of centres
    gam = math.atan2(L * math.sin(th), c - L * math.cos(th))                  # the tangent points sit at +-(pi - gam) on the right circle and at +-gam on the left one
    rx, ry = scr(c, 0.0)
    lx, ly = scr(-c, 0.0)
    P.ring_line(cv, rx, ry, rho, sig, right, peak, a0=axis + math.pi + gam, a1=axis + math.pi - gam, glow=0.10)
    P.ring_line(cv, lx, ly, rho, sig, left, peak, a0=axis + gam, a1=axis + 2.0 * math.pi - gam, glow=0.10)
    same = bool(np.allclose(left, right))
    for sgn in (1.0, -1.0):
        xa, ya = scr(L * math.cos(th), sgn * L * math.sin(th))
        xb, yb = scr(-L * math.cos(th), -sgn * L * math.sin(th))
        if same:
            P.seg_line(cv, xa, ya, xb, yb, sig, left, peak, glow=0.10)
        else:
            # each tangent in two halves that meet under the star: the half next to the right iris in its colour, the other in the left one's
            P.seg_line(cv, xa, ya, cx, cy, sig, right, peak, glow=0.10)
            P.seg_line(cv, cx, cy, xb, yb, sig, left, peak, glow=0.10)
    P.sparkle(cv, cx, cy, 0.30 * R, C.rgb01(P.GOLD_HOT), 0.85, 0.0055 * R, angle=math.radians(45.0), core=0.5)
    ctx.log["clean_duo"] = {"belt_over_R": info["belt"], "gap_limb_R": info["gap"], "tangent_len_R": round(2 * L / R, 3), "thread": ctx.opts.get("thread", "gold")}


def default_fmt(n):
    return "3:2"


LOOK = {"n": (2, 2), "fmt": default_fmt, "canvases": ("3:2", "5:4", "1:1", "4:5", "9:19.5"), "plan": plan_clean_duo, "fx": fx_clean_duo, "bg": "#020203",
        "group": "duo"}
