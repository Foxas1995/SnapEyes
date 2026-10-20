# -*- coding: utf-8 -*-
"""styles.ensemble.orbit: FAMILY ORBIT, a gift for ONE person: three to eight WHOLE irises that never overlap, the first eye of the canvas order larger in the
middle (the hub: mum, grandma, the new baby; the customer chooses which eye it is), the others on a ring round it, an orbit hairline that runs behind the ring
irises, the hub in the gold corona of the owner-approved Celestial Gold single, each person's own colour as a faint aura. Square (1:1) or 4:5.

Ported from the laboratory of the pairs and families round (proto_pf/family.py, the orbit, 2026-10-20) without a change to what it draws. Pieces of the engine
it reuses: corona.corona (singles/gold.py's corona of one disc), matter.ParticleLayer, the sparkles. The threads and the orbit are drawn BEFORE the irises are
pasted, so they lie under every iris: nothing is ever drawn over an iris or a pupil."""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from .. import matter as M
from ..collision import scenes as CS
from ..singles import kit as K
from . import corona as CR
from . import pieces as P
from .base import Plan

F32 = np.float32
TWO_PI = 2.0 * math.pi
KAPPA = {3: 1.45, 4: 1.40, 5: 1.40, 6: 1.32, 7: 1.22, 8: 1.20}       # the hub's radius over the ring's (a smaller hub for a larger family)


def plan_orbit(n, fmt, o):
    W, H = CS.canvas_size(fmt, 1024)
    m = n - 1
    kappa = float(o.get("kappa", KAPPA[n]))
    gap = float(o.get("gap", 0.16))                      # the least gap between neighbours on the ring, in ring radii
    rho_min = kappa + 1.0 + float(o.get("hub_gap", 0.55 if m <= 4 else 0.42))
    rho = max(rho_min, (2.0 + gap) / (2.0 * math.sin(math.pi / m)) if m >= 3 else 0.0)
    a0 = {2: -135.0, 3: -90.0, 4: -135.0, 5: -90.0, 6: -120.0, 7: -90.0}.get(m, -90.0)
    a0 = float(o.get("start_deg", a0))
    ring = [(rho * math.cos(math.radians(a0 + 360.0 * i / m)), rho * math.sin(math.radians(a0 + 360.0 * i / m))) for i in range(m)]
    xs0 = [-kappa] + [x - 1.0 for x, _ in ring]
    xs1 = [kappa] + [x + 1.0 for x, _ in ring]
    ys0 = [-kappa] + [y - 1.0 for _, y in ring]
    ys1 = [kappa] + [y + 1.0 for _, y in ring]
    halo = float(o.get("halo", 0.45))                      # room for the corona of the hub and the auras, in ring radii
    bw, bh = max(xs1) - min(xs0) + 2 * halo, max(ys1) - min(ys0) + 2 * halo
    r = min(0.94 * W / bw, 0.92 * H / bh)
    cxm, cym = (max(xs1) + min(xs0)) / 2.0, (max(ys1) + min(ys0)) / 2.0
    ox, oy = W / 2.0 - cxm * r, 0.5 * H - cym * r
    discs = [(ox, oy, kappa * r)] + [(ox + x * r, oy + y * r, r) for x, y in ring]
    return Plan(fmt, discs, {"rho_r": rho, "r": r, "kappa": kappa, "m": m})


def default_fmt(n):
    return "1:1"


def fx_orbit(cv, ctx):
    W, H, S = ctx.W, ctx.H, ctx.S
    o = CR.gold_opts(ctx)
    hub, ring = ctx.discs[0], ctx.discs[1:]
    K.fill_radial_bg(cv, hub.cx, hub.cy, 0.95 * max(W, H), "#0B0D14", "#040507", power=0.9)
    cols = [P.own_colour(ir, 1.25, 1.35, P.gold_ramp(np.float32(0.62)), 0.25) for ir in ctx.irises]
    # the personal colour of every person, a faint aura (the hub's is the widest)
    P.aura(cv, hub, cols[0], 0.20, 0.20, reach=3.0)
    for d, c in zip(ring, cols[1:]):
        P.aura(cv, d, c, float(ctx.opts.get("aura", 0.22)), 0.13, reach=2.4)
    # the hub in its corona: the owner-approved gold, one iris, the eclipse
    CR.corona(cv, ctx, hub, ctx.irises[0], ctx.rand("gold_a", 0), o, strength=float(ctx.opts.get("corona", 0.95)))
    # the orbit: one hairline circle round the hub through the centres of the ring, drawn behind the ring irises and stopped 0.05 R short of each
    rho = math.hypot(ring[0].cx - hub.cx, ring[0].cy - hub.cy)
    sig = 0.0012 * S * 0.5

    def w_moat(xs, y):
        return P.moat(xs, y, ring, inner=1.06, width=0.10)
    P.ring_line(cv, hub.cx, hub.cy, rho, sig, C.rgb01("#F0E2C4"), 0.62, weight=w_moat, glow=0.10)

    def w_edge(xs, y):
        return w_moat(xs, y) * np.clip((0.5 * W - np.abs(xs - W / 2.0)) / (0.04 * W), 0.0, 1.0) * np.clip((0.5 * H - abs(y - H / 2.0)) / (0.04 * H), 0.0, 1.0)
    # a second orbit, fainter and wider, for depth, and the faint inner one round the hub's corona
    for fr, pk in ((rho + ring[0].R * 1.9, 0.20), (hub.R * 1.62, 0.16)):
        P.ring_line(cv, hub.cx, hub.cy, fr, sig, C.rgb01("#E2D2B0"), pk, weight=w_edge)
    layer = M.ParticleLayer()
    P.star_field(layer, ctx, ctx.rand("stars"), (130, 200), ctx.discs, avoid=1.35)
    P.gold_dust(layer, ctx, ctx.rand("dust"), (150, 260), [(hub.cx, hub.cy, hub.R)], discs=ctx.discs, orbit_share=0.0, avoid=1.30)
    layer.flush(cv)
    del layer
    # a four point star halfway between every two neighbours on the ring (the moons)
    hot = C.rgb01(P.GOLD_HOT)
    m = len(ring)
    ang = [math.atan2(d.cy - hub.cy, d.cx - hub.cx) for d in ring]
    for i in range(m):
        a_mid = ang[i] + ((ang[(i + 1) % m] - ang[i]) % TWO_PI) / 2.0
        P.sparkle(cv, hub.cx + rho * math.cos(a_mid), hub.cy + rho * math.sin(a_mid), 0.34 * ring[0].R, hot, 0.62, 0.0050 * ring[0].R, angle=math.radians(45.0), core=0.40)
    P.eclipse_gap(cv, hub, o["gap"])
    for d in ring:
        P.eclipse_gap(cv, d, 0.030)
    ctx.log["orbit"] = {"n": len(ctx.discs), "rho_over_r": round(ctx.plan.info["rho_r"], 3), "hub_over_ring": ctx.plan.info["kappa"]}


LOOK = {"n": (3, 8), "fmt": default_fmt, "canvases": ("1:1", "4:5"), "plan": plan_orbit, "fx": fx_orbit, "bg": "#0B0D14", "group": "grp", "name_colour": "#C9A86A"}
