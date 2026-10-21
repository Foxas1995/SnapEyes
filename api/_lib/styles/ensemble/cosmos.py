# -*- coding: utf-8 -*-
"""styles.ensemble.cosmos: NEBULA DUO, NEBULA FAMILY, SUPERNOVA DUO and SUPERNOVA FAMILY, the owner's cosmos looks of 2026-10-20 (he liked the pair and family
sketches of the cosmos laboratory round, SP wave-cosmos sketch_pair_family.jpg), drawn round two to eight WHOLE irises.

This module only lays the discs out (the ensemble family's pair and family arrangements) and calls the light family's own effects over all of them, as they are:
  nebula_duo, nebula_family         lumen.nebula.fx_nebula(cv, ctx)       the irises as the bright hearts of one nebula: each eye's own colour glows warm at its
                                                                          limb, the clouds turn to the partner colours further out, dust lanes, a young cluster
  supernova_duo, supernova_family   lumen.stardust.fx_stardust(cv, ctx)   a burst of stardust in each eye's own colours at every angle of its limb, the broken
                                                                          shock shell, sparkles, a quiet field of stars
Those two functions are the ONLY entry points of the light family this module calls, and nothing of that family is changed or copied: the effects read
ctx.discs and ctx.irises as lists (api/_lib/styles/lumen/__init__.py says so), and the context of base.render gives them what they read (W, H, S, wall, discs,
irises, opts, rand, log, text_box; the kit's fades read the same). The single looks and these four draw with the very same code, so a change of the light
family moves them together (the single looks' goldens are v3lumen's, these four's are v3ensemble's: both are recorded again then).

Nothing of an iris is touched: the effects draw into the float canvas and every iris is pasted last (base.render), byte for byte inside 0.974 R."""
from __future__ import annotations

from ..collision import scenes as CS
from ..lumen import nebula as NB
from ..lumen import stardust as SDT
from .base import Plan, fit_points
from .radiance_duo import plan_radiance_duo
from .radiance_family import ROWS, hex_points

GAP_DUO = 0.12           # limb to limb gap of a pair in R (the laboratory's sketch: about 0.1 R, the two lights meet between the irises)
GAP_FAMILY = 0.18        # the gap of the hex arrangement of a family in iris diameters (the laboratory's sketch: one sky round all of them)
# The masters of the two cosmos families from six eyes (the family speed work of 2026-10-21). The light family's effects compute their soft fields on a
# grid of cells over the whole canvas for every disc (lumen.common.grid_factor: 3 px a cell at 4096), most of the time of a big family's master. From
# GRID_FROM eyes a master (a canvas of GRID_MASTER px and more) draws them on a coarser grid; the stars, grains, sparkles, filaments and young clusters
# stay full resolution, every particle count stays the laboratory's, and the preview (1024 px, one px a cell), three to five eyes and the pairs are
# untouched.
GRID_FROM = 6
GRID_MASTER = 2048
# Supernova Family: the haze of the bursts on 768 cells asked (5 px a cell at 4096, 820 cells): at eight eyes the 3 px cells took 8 of the 16 s of the
# effect, 768 cells take 3; side by side at 100 percent the two hazes are not told apart.
HAZE_GRID = 768
# Nebula Family: the gas, the filaments and the dust on the preview's own grid (lumen.nebula's "grid": 1024 cells, 4 px a cell at 4096): the gas reads
# slightly softer at 100 percent (SSIM 0.997 beyond the irises at eight eyes).
GAS_GRID = 1024


def plan_cosmos_duo(n, fmt, o):
    """Two irises side by side (one above the other on the phone wallpaper): the Radiance Duo arrangement with a smaller gap."""
    return plan_radiance_duo(n, fmt, dict(o, gap=float(o.get("gap", GAP_DUO))))


def plan_cosmos_family(n, fmt, o):
    """Three to eight irises in the hex rows of Radiance Family (six in three rows of two) with a smaller gap and margin: one sky round all of them."""
    W, H = CS.canvas_size(fmt, 1024)
    S = min(W, H)
    gap = float(o.get("gap", GAP_FAMILY))
    rows = ROWS[n]
    pts = hex_points(rows, 1.0 + gap)
    D = 0.2 * S
    for _ in range(3):
        m = 0.04 * S + 0.40 * D / 2.0
        D, cs = fit_points(pts, (m, m, W - m, H - m), 0.40 * S)
    return Plan(fmt, [(x, y, D / 2.0) for x, y in cs], {"gap": gap, "rows": rows})


def duo_fmt(n):
    return "3:2"


def family_fmt(n):
    return "1:1" if n >= 6 else "3:2"


def master_grid(ctx):
    """Does this picture draw the soft fields of its effect on the coarser grid of a big family's master (GRID_FROM eyes, a GRID_MASTER px canvas)?"""
    return len(ctx.discs) >= GRID_FROM and max(ctx.W, ctx.H) >= GRID_MASTER


def fx_nebula_group(cv, ctx):
    if master_grid(ctx):
        o = dict(ctx.opts.get("nebula") or {})
        o.setdefault("grid", GAS_GRID)                                    # an option the laboratory gives wins
        ctx.opts = dict(ctx.opts, nebula=o)
    NB.fx_nebula(cv, ctx)


def fx_supernova_group(cv, ctx):
    if master_grid(ctx):
        o = dict(ctx.opts.get("stardust") or {})
        o.setdefault("grid", HAZE_GRID)                                   # an option the laboratory gives wins
        ctx.opts = dict(ctx.opts, stardust=o)
    SDT.fx_stardust(cv, ctx)


DUO_CANVASES = ("3:2", "5:4", "1:1", "4:5", "9:19.5")
FAMILY_CANVASES = ("3:2", "1:1", "5:4", "4:5")
NEBULA_DUO = {"n": (2, 2), "fmt": duo_fmt, "canvases": DUO_CANVASES, "plan": plan_cosmos_duo, "fx": fx_nebula_group, "bg": "#000000", "group": "duo"}
NEBULA_FAMILY = {"n": (3, 8), "fmt": family_fmt, "canvases": FAMILY_CANVASES, "plan": plan_cosmos_family, "fx": fx_nebula_group, "bg": "#000000", "group": "grp"}
SUPERNOVA_DUO = {"n": (2, 2), "fmt": duo_fmt, "canvases": DUO_CANVASES, "plan": plan_cosmos_duo, "fx": fx_supernova_group, "bg": "#000000", "group": "duo"}
SUPERNOVA_FAMILY = {"n": (3, 8), "fmt": family_fmt, "canvases": FAMILY_CANVASES, "plan": plan_cosmos_family, "fx": fx_supernova_group, "bg": "#000000",
                    "group": "grp"}
