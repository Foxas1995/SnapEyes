# -*- coding: utf-8 -*-
"""styles.ensemble.radiance_duo: RADIANCE DUO, two whole irises side by side, each sending thin rays of its own colour from the limbus inside a dark moat; the two
lights cross in the gap (the second burst is the first one mirrored across the line between the irises) and a small four point star stands where they meet.
The ray engine is the Radiance single's (singles/radiance.py as it stands: build_field, sample_field, bloom_and_screen, palette, duo_palettes, the looks):
this module lays out the two discs, aims the lights, shares one key light, keeps each limb in its dark moat and draws the star. Nothing of an iris is
touched: the rays are drawn into the float canvas, the moat keeps the limb black, the iris is pasted last.

Ported from the laboratory of the pairs and families round (proto_pf/radiance_duo.py, 2026-10-20) with the round the owner asked for, and nothing else changed:
  the dark limb rule   a dark iris (the limb band of its graded disc under 0.34 in display value, a dark brown eye) keeps a wider and deeper moat (up to 0.20 R
                       wide, the light pulled down to 0.05 at the limb), so its limb reads against the ring outside it (T10 and T11 at 1024 and 320 px: the
                       laboratory's dark brown set read 1.3 L* at 320 px)
  the ray reach cap    the light fades out from 2.25 R to 2.85 R of its iris (singles/radiance.py's own cap, Look.cap: the longest hero rays no longer run
                       across the picture) and over the last 0.035 S toward the canvas edge (kit.edge_fade, the brief's own rule that an artwork must not look
                       cropped): the frame stays dark, T8b (the Radiance brief's own bound) is held on every render, the phone wallpaper included
  the plan freeze      when the two drawn colours are closer than 10 dE00 one eye takes its next palette variant (radiance.duo_palettes); which eye and
                       which variant is decided ONCE, at the plan (resolve with the eyes), and the master obeys it (frozen {"pal": [vA, vB]}), so a 4096 px
                       master of another copy of the eyes never draws another colour than the preview showed."""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..collision import scenes as CS
from ..singles import kit as K
from ..singles import radiance as RD
from . import pieces as P
from .base import Plan

F32 = np.float32
DARK_LIMB = (0.34, 0.16)          # a limb band under 0.34 (display value 0..1) is dark: fully so 0.16 below it
MOAT = 0.18                       # the light at the limb (the single's own moat) ...
MOAT_DARK = 0.05                  # ... and at a dark limb
MOAT_W = (0.08, 0.20)             # the moat's width in R: the single's, and a dark limb's
CAP = (2.85, 0.60)                # the reach of the light, Look.cap: full inside 2.25 R, none from 2.85 R
EDGE = 0.035                      # the light fades out over the last 0.035 S toward the canvas edge (kit.edge_fade, the brief's 3.0.4): the frame stays dark (T8b)


def plan_radiance_duo(n, fmt, o):
    W, H = CS.canvas_size(fmt, 1024)
    S = min(W, H)
    gap = float(o.get("gap", 0.34))
    wall = fmt == "9:19.5"
    ax = {"3:2": 0.0, "5:4": 0.0, "1:1": 30.0, "4:5": 60.0, "9:19.5": 90.0}.get(fmt, 0.0)
    a = math.radians(float(o.get("axis_deg", ax)))
    u = (math.cos(a), math.sin(a))
    reach = 1.15
    hx = (1.0 + gap / 2.0) * abs(u[0]) + reach
    hy = (1.0 + gap / 2.0) * abs(u[1]) + reach
    R = min(0.46 * W / hx, (0.36 if wall else 0.46) * H / hy)
    R = min(R, 0.27 * H if fmt in ("3:2", "5:4") else 0.5 * S)
    cx, cy = W / 2.0, (0.57 if wall else 0.5) * H
    off = R * (1.0 + gap / 2.0)
    return Plan(fmt, [(cx - u[0] * off, cy - u[1] * off, R), (cx + u[0] * off, cy + u[1] * off, R)], {"axis_deg": math.degrees(a), "gap": gap})


def default_fmt(n):
    return "3:2"


def _hue(p):
    return float(C.lch(np.asarray(p, np.float32).mean(0))[2])


def decide(irises):
    """What the plan freezes for two eyes in canvas order: {"pal": [vA, vB]}, the palette variant of each (0 its own colours; at most one of them moves, as
    radiance.duo_palettes decides)."""
    _pa, _pb, (mover, v) = RD.duo_palettes(irises[0], irises[1])
    pal = [0, 0]
    if mover is not None:
        pal[int(mover)] = int(v)
    return {"pal": pal}


def palettes(irises, frozen):
    """The two palettes for the variants the plan froze (radiance.duo_palettes' own arithmetic for the same decision: the eye that moves turns away from the
    hue of its partner's own palette)."""
    pal = list((frozen or {}).get("pal") or [0, 0])
    A, B = irises
    if pal[1]:
        pa = RD.palette(A)
        return pa, RD.palette(B, int(pal[1]), _hue(pa))
    if pal[0]:
        pb = RD.palette(B)
        return RD.palette(A, int(pal[0]), _hue(pb)), pb
    return RD.palette(A), RD.palette(B)


def dark_share(d):
    """How dark the limb of a placed disc is: 0 (a light limb) to 1 (a dark brown one), from the graded disc's own limb band (pieces.limb_brightness)."""
    lb = P.limb_brightness(d)
    return float(np.clip((DARK_LIMB[0] - lb) / DARK_LIMB[1], 0.0, 1.0))


def fx_radiance_duo(cv, ctx):
    W, H, S = ctx.W, ctx.H, ctx.S
    A, B = ctx.irises
    look = ctx.opts.get("look") or RD.Look(vignette=(0.78, 0.50, 0.80))
    cap = tuple(ctx.opts.get("cap", CAP)) if ctx.opts.get("cap", CAP) else None
    ctx.stretch = 1.0
    light = np.zeros((H, W, 3), np.float32)
    frozen = ctx.frozen if isinstance(ctx.frozen.get("pal"), list) else decide(ctx.irises)
    pa, pb = palettes(ctx.irises, frozen)
    pals = (pa, pb)
    key0 = (RD.key_angle(ctx.rand("radiance/key")), look.key)
    cross = bool(ctx.opts.get("cross", True))
    hole = ctx.opts.get("hole", (10.0, 40.0, 0.45))
    axis = math.atan2(ctx.discs[1].cy - ctx.discs[0].cy, ctx.discs[1].cx - ctx.discs[0].cx)
    mirror = bool(ctx.opts.get("mirror_lobes", True))
    lobe0, key0m = None, None
    for i, d in enumerate(ctx.discs):
        other = ctx.discs[1 - i]
        towards = math.atan2(other.cy - d.cy, other.cx - d.cx)
        if cross:
            # the lights CROSS: each iris's key light (the direction its longest, brightest rays face, hero rays within 70 deg of it) is the partner, +-20 deg,
            # and the dimmer sector toward the partner is off, so the two bursts overlap in the gap
            jit = math.radians(float(ctx.rand("radiance/cross", i).uniform(1, -20.0, 20.0)[0]))
            key, tw = (towards + jit, look.key), None
        else:
            key, tw = key0, towards
        lk = RD.Look(vignette=(0.78, 0.50, 0.80), cap=cap)
        if mirror and cross and i == 1:
            # the second burst is the first one reflected across the line between the two irises: the long rays leave both at mirrored angles (a balanced pair, not two
            # unrelated bursts); the single rays of each eye stay its own
            key = (math.pi + 2.0 * axis - key0m[0], look.key)
            lk.lobe_fn = lambda c, f=lobe0: f((math.pi + 2.0 * axis - np.asarray(c, np.float64)))
        else:
            lk.lobe_fn = RD.make_lobe_fn(ctx.rand("radiance/lobes", i), key)
            if i == 0:
                lobe0, key0m = lk.lobe_fn, key
        rho_max = min(RD.far_rho(d, W, H) + 0.05, cap[0] + 0.05) if cap else RD.far_rho(d, W, H) + 0.05
        fld = RD.build_field(d, pals[i], RD._rnd(ctx, i), lk, rho_max, towards=tw, key=key, whiten=RD._whiten_for(d.iris, lk), hole=hole)
        RD.sample_field(fld, light, ctx)
        del fld
    moat = float(ctx.opts.get("moat", MOAT))
    wins, darks = [], []
    for d in ctx.discs:
        dk = dark_share(d) if ctx.opts.get("dark_limb", True) else 0.0
        darks.append(round(dk, 3))
        floor = moat + (MOAT_DARK - moat) * dk
        width = MOAT_W[0] + (MOAT_W[1] - MOAT_W[0]) * dk
        reach = 1.0 + width + 0.08
        x0, y0 = max(0, int(d.cx - reach * d.R)), max(0, int(d.cy - reach * d.R))
        x1, y1 = min(W, int(d.cx + reach * d.R) + 2), min(H, int(d.cy + reach * d.R) + 2)
        rho, _ = C.polar(W, H, d.cx, d.cy, d.R, 1.0, (x0, y0, x1, y1))
        f = (floor + (1.0 - floor) * C.smoothstep((rho - 1.0) / width))[..., None].astype(np.float32)
        light[y0:y1, x0:x1] *= f
        wins.append((x0, y0, x1, y1, f))
    K.text_fade(light, ctx)

    def post_glow(lt):
        for (x0, y0, x1, y1, f) in wins:
            lt[y0:y1, x0:x1] *= f
        if ctx.opts.get("edge", EDGE):
            K.edge_fade(lt, ctx, width=float(ctx.opts.get("edge", EDGE)))
    RD.bloom_and_screen(cv, light, ctx, look, post_glow=post_glow)
    del light
    # the star where the two lights meet: a four point star at the middle of the gap, warm white
    d0, d1 = ctx.discs
    mx, my = (d0.cx + d1.cx) / 2.0, (d0.cy + d1.cy) / 2.0
    R = d0.R
    col = C.mix(C.rgb01(RD.WARM_WHITE)[None, :], (pa.mean(0) + pb.mean(0))[None, :] / 2.0, 0.25)[0]
    if ctx.opts.get("star", True):
        P.sparkle(cv, mx, my, 0.30 * R, col, 0.85, 0.0075 * R, angle=0.0, core=0.55)
        P.sparkle(cv, mx, my, 0.17 * R, col, 0.55, 0.0070 * R, angle=math.radians(45.0), core=0.0)
    ctx.log["frozen"] = {"pal": [int(v) for v in frozen["pal"]]}
    ctx.log["radiance_duo"] = {"modes": [RD.colour_mode(A), RD.colour_mode(B)], "pal": ctx.log["frozen"]["pal"], "dark": darks, "gap_limb_R": ctx.plan.info["gap"],
                               "cap": list(cap) if cap else None}


LOOK = {"n": (2, 2), "fmt": default_fmt, "canvases": ("3:2", "5:4", "1:1", "4:5", "9:19.5"), "plan": plan_radiance_duo, "fx": fx_radiance_duo, "bg": "#050508",
        "group": "duo", "decide": decide}
