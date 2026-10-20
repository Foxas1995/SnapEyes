# -*- coding: utf-8 -*-
"""styles.ensemble.radiance_family: RADIANCE FAMILY, the owner's old 2026-09-30 "Radiance Family" (the recommended look of his family board, 7.5 of 10) in today's
engine: three to eight WHOLE irises, every one sending short thin rays of its own colour from the limbus inside the dark moat, one shared key light at half
strength (singles/radiance.FAMILY_KINDS, the rays capped at 2.2 R), each eye's rays kept to its own territory by a soft Voronoi weight (sample_field's wmap) so
that the neighbours' lights blend at the borders instead of piling up. The ray engine is singles/radiance.py as it stands; this module lays the discs out,
picks distinct palettes and builds the territories. Nothing touches an iris: the moat keeps every limb black, the iris is pasted last.

Ported from the laboratory of the pairs and families round (proto_pf/radiance_family.py, 2026-10-20). Three things are added, nothing else is changed: the dark
limb rule of Radiance Duo (radiance_duo.dark_share: a dark limb keeps a wider and deeper moat, so it reads at 320 px), Radiance Duo's fade of the light over the last
0.035 S toward the canvas edge (the frame stays dark: T8b) and the plan freeze of the palettes
(an eye whose drawn colours are within 10 dE00 of an earlier eye's takes its next variant: decided once, at the plan, {"pal": [v, ...]}, and obeyed by the
master)."""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..collision import scenes as CS
from ..singles import kit as K
from ..singles import radiance as RD
from .base import Plan, fit_points
from .radiance_duo import EDGE, MOAT_DARK, MOAT_W, dark_share

F32 = np.float32
# rows of the hex arrangement per eye count; six eyes take three rows of two (the rays need room, and a 3 + 3 brick on the 3:2 canvas is under the floor T18)
ROWS = {3: [1, 2], 4: [2, 2], 5: [2, 3], 6: [2, 2, 2], 7: [2, 3, 2], 8: [3, 2, 3]}


def hex_points(rows, d=1.0):
    """Unit-diameter centres of a hex packing with the given row counts (centre spacing d in diameters, rows 0.866 d apart): rows of equal count are
    shifted by half a step, rows of different count stagger by themselves."""
    pts = []
    for r, c in enumerate(rows):
        shift = 0.5 * d if (r % 2 == 1 and c == rows[r - 1]) else 0.0
        for j in range(c):
            pts.append(((j - (c - 1) / 2.0) * d + shift, (r - (len(rows) - 1) / 2.0) * d * math.sqrt(3.0) / 2.0))
    cx = (max(p[0] for p in pts) + min(p[0] for p in pts)) / 2.0
    return [(x - cx, y) for x, y in pts]


class Territory:
    """A soft Voronoi weight of disc i over the canvas, read by slices (what sample_field asks of a wmap): exp(-s d_i / R) over the sum of the same for every
    disc, d the distance to the disc's centre."""

    def __init__(self, discs, i, sharp=2.6):
        self.discs, self.i, self.sharp = discs, i, sharp

    def __getitem__(self, key):
        rs, cs = key
        ys = (np.arange(rs.start, rs.stop, dtype=np.float32) + 0.5)[:, None]
        xs = (np.arange(cs.start, cs.stop, dtype=np.float32) + 0.5)[None, :]
        ws = []
        for d in self.discs:
            ws.append(np.exp(-self.sharp * np.hypot(xs - d.cx, ys - d.cy) / d.R))
        tot = ws[0].copy()
        for w in ws[1:]:
            tot += w
        return (ws[self.i] / np.maximum(tot, 1e-12)).astype(np.float32)


def plan_radiance_family(n, fmt, o):
    W, H = CS.canvas_size(fmt, 1024)
    S = min(W, H)
    gap = float(o.get("gap", 0.30))
    rows = ROWS[n]
    pts = hex_points(rows, 1.0 + gap)
    D = 0.2 * S
    for _ in range(3):
        m = 0.04 * S + 0.45 * D / 2.0
        box = (m, m, W - m, H - m)
        D, cs = fit_points(pts, box, 0.40 * S)
    return Plan(fmt, [(x, y, D / 2.0) for x, y in cs], {"gap": gap, "rows": rows})


def default_fmt(n):
    return "1:1" if n >= 6 else "3:2"


def _distinct(p, pals):
    return all(C.colour_distance(p.mean(0), q.mean(0)) >= 10.0 for q in pals)


def decide(irises):
    """What the plan freezes: {"pal": [v, ...]}, the palette variant of each eye in canvas order (0 its own colours): an eye whose drawn colours are within
    10 dE00 of an earlier eye's takes its next variant, up to 3 (the laboratory's rule, radiance.palette's variants)."""
    pals, out = [], []
    for ir in irises:
        p, v = RD.palette(ir), 0
        for k in (1, 2, 3):
            if _distinct(p, pals):
                break
            p, v = RD.palette(ir, k, float(C.lch(pals[-1].mean(0))[2])), k
        pals.append(p)
        out.append(v)
    return {"pal": out}


def palettes(irises, frozen):
    """The palettes of the eyes for the variants the plan froze (decide's own arithmetic for the same decisions: a moved eye turns away from the hue of the
    eye drawn before it)."""
    pal = list((frozen or {}).get("pal") or [0] * len(irises))
    pals = []
    for ir, v in zip(irises, pal):
        pals.append(RD.palette(ir) if not v else RD.palette(ir, int(v), float(C.lch(pals[-1].mean(0))[2])))
    return pals


def fx_radiance_family(cv, ctx):
    W, H, S = ctx.W, ctx.H, ctx.S
    ds, irs = ctx.discs, ctx.irises
    n = len(ds)
    ctx.stretch = 1.0
    light = np.zeros((H, W, 3), np.float32)
    fz = ctx.frozen.get("pal")
    frozen = ctx.frozen if isinstance(fz, list) and len(fz) == n else decide(irs)
    pals = palettes(irs, frozen)
    key = (RD.key_angle(ctx.rand("radiance/key")), 0.5)
    cap = ctx.opts.get("cap", (2.2, 0.40))
    gain = float(ctx.opts.get("gain", 1.6))
    look = RD.Look(kinds=RD.FAMILY_KINDS, vignette=(0.80, 0.50, 0.70), cap=cap, key=0.5, spread=1.0, ray_gain=0.88 * gain)
    for i, d in enumerate(ds):
        lk = RD.Look(kinds=RD.FAMILY_KINDS, vignette=(0.80, 0.50, 0.70), cap=cap, key=0.5, spread=1.0, ray_gain=0.88 * gain)
        lk.lobe_fn = RD.make_lobe_fn(ctx.rand("radiance/lobes", i), key)
        fld = RD.build_field(d, pals[i], RD._rnd(ctx, i), lk, float(cap[0]) + 0.1, key=key, whiten=RD._whiten_for(d.iris, lk))
        RD.sample_field(fld, light, ctx, wmap=Territory(ds, i))
        del fld
    moat = float(ctx.opts.get("moat", 0.14))
    wins, darks = [], []
    for d in ds:
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
    ctx.log["frozen"] = {"pal": [int(v) for v in frozen["pal"]]}
    ctx.log["radiance_family"] = {"n": n, "modes": [RD.colour_mode(ir) for ir in irs], "pal": ctx.log["frozen"]["pal"], "dark": darks}


LOOK = {"n": (3, 8), "fmt": default_fmt, "canvases": ("3:2", "1:1", "5:4", "4:5"), "plan": plan_radiance_family, "fx": fx_radiance_family, "bg": "#050508",
        "group": "grp", "decide": decide}
