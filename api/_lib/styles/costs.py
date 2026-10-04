# -*- coding: utf-8 -*-
"""styles.costs: what a design costs, in seconds and megabytes, before any pixel is drawn. The planner, the checkout capacity check and the
step runner ask this module whether a step can finish inside the time that is left and fit the memory budget; nothing here draws.

The table is MEASURED, not guessed: quiet-core CPU seconds and peak memory of every design the planning spike rendered, at 1024 px
previews and at 4096 px masters made from real 4096 px eyes (baked by scripts/bake_costs.py from the spike's own tables, never rounded).
A Vercel call is modelled as the spike models it (SPIKE.md section 2.4):

    step_need = F x (cpu(design, eyes) + 0.25 s per eye of JPEG decode + 0.17 s of JPEG encode)
                + 4.5 s cold start + 0.31 s per eye of storage read + 0.8 s of upload, record and link

F is STYLE_SLOW_CPU (api/_lib/cpu_probe.py style_slow_cpu(): the environment, default 1.6, bounded 1.0 to 6.0; measured on the real
instance by the admin action cpu_probe). The cold start is charged to every call although a warm call has no such cost: a warm step is
over-estimated by 4.5 s on purpose. Decode and encode are inside the factor (they are CPU too).

A cost key names a design the way the catalogue does: module.design, with .clean for the clean variant and .universe for a design drawn over
a universe fill (cost_key(engine, bg)). A combination the spike did not measure has no row: cpu() raises NoCost, never a guess, and a
planner treats that as a configuration error (a style the table cannot price is not a style that may be sold).

Memory: peaks are the spike's cold peaks with uncapped 4096 px sources; est_mb() takes the 2048 px working copy row where the registry
caps the layout (pairs, families 4 to 8, chain: catalogue.work_side) and adds the plan's Linux allowance of 15 percent. MEM_BUDGET_MB is
70 percent of FUNCTION_MEM_MB (the project's function memory: 2048 until V4 reads the real setting, env STYLE_FUNCTION_MEM_MB).
"""
from __future__ import annotations

import os

from .. import cpu_probe

# ----------------------------------------------------------------------------- the model's constants
COLD_START_S = 4.5            # seconds outside the handler on a cold instance (SPIKE 2.1, measured on the live function)
DECODE_S_PER_EYE = 0.25       # JPEG decode of one 4096 px eye
ENCODE_S = 0.17               # JPEG q95 4:4:4 encode of the finished artwork
STORAGE_READ_S_PER_EYE = 0.31  # an eye read from private storage (estimate: 20 MB/s down, 0.15 s a call)
UPLOAD_S = 0.8                # the artwork upload, the record and the signed link
PREVIEW_DECODE_S_PER_EYE = 0.1
LINUX_ALLOWANCE = 1.15        # peaks were measured on Windows; the plan adds 15 percent for Linux
TILE_AREA_FLOOR = 0.22        # a 480 px tile costs at least this share of the design time of a 1024 px preview (480 squared over 1024 squared)
TILE_OVERHEAD_S = 0.2         # per tile of a batch: atlas and plate loads, the per-design grade the preparation does not share. Calibrated against
                              # the spike's group figures (SPIKE 3.2: six single tiles 4.9 s local in one call, four pair tiles 1.9, a Trio 1.8)

STYLE_STEP_BUDGET = 40.0      # seconds: the planner cuts a master into steps when one would need more (a larger duration limit raises it)
WORK_BUDGET_S = 52.0          # iris.BUDGET today; WP6a derives it from the one duration constant


def _env_float(name, default, lo, hi):
    try:
        v = float(os.environ.get(name, "").strip())
    except ValueError:
        return default
    return min(max(v, lo), hi) if v == v else default


FUNCTION_MEM_MB = int(_env_float("STYLE_FUNCTION_MEM_MB", 2048, 512, 10240))
MEM_BUDGET_FRACTION = 0.70
MEM_BUDGET_MB = int(round(FUNCTION_MEM_MB * MEM_BUDGET_FRACTION))     # 1434 at 2 GB


class NoCost(LookupError):
    """The table has no measured row for this design and eye count."""


# BEGIN BAKED (scripts/bake_costs.py)
# MASTER[key][eyes] = (cold cpu s, warm cpu s, cold peak MB, warm peak MB): a 4096 px master from 4096 px eyes, one thread, quiet core
MASTER = {
    "singles.powder": {1: (12.4, 11.2, 729, 931)},
    "singles.splash": {1: (12.1, 12.3, 801, 952)},
    "singles.elements": {1: (16.4, 15.8, 890, 1041)},
    "singles.radiance": {1: (9.3, 8.4, 900, 986)},
    "singles.gold": {1: (12.4, 12.1, 734, 816)},
    "singles.clean": {1: (6.3, 5.6, 620, 706)},
    "collision.infinity": {2: (8.4, 8.2, 645, 823)},
    "collision.infinity.clean": {2: (9.0, 8.1, 642, 810)},
    "collision.infinity.universe": {2: (8.8, 8.4, 895, 1122)},
    "collision.kiss": {2: (7.2, 6.8, 643, 811)},
    "collision.kiss.universe": {2: (8.0, 7.4, 896, 1121)},
    "collision.trio": {3: (15.4, 14.4, 929, 1228)},
    "collision.trio.universe": {3: (16.0, 16.4, 1263, 1576)},
    "collision.family": {4: (9.9, 9.2, 782, 1129), 5: (15.2, 14.5, 909, 1315), 6: (16.4, 15.8, 988, 1481), 7: (19.1, 18.5, 1258, 1827), 8: (20.2, 19.1, 1330, 1969)},
    "collision.family.universe": {6: (18.0, 16.9, 2015, 2554), 8: (22.1, 20.9, 2603, 3293)},
    "collision.chain": {3: (9.7, 9.2, 712, 992), 4: (10.1, 9.1, 772, 1115), 5: (10.2, 9.2, 716, 1104), 6: (11.1, 10.6, 800, 1257)},
    "universe.echo": {1: (12.1, 11.6, 635, 769), 2: (14.8, 13.8, 649, 861), 3: (22.5, 18.1, 1250, 1254), 4: (16.3, 15.9, 770, 1267), 5: (21.9, 21.0, 1069, 1515), 6: (22.8, 22.6, 1107, 1703)},
    "universe.vortex": {1: (10.2, 9.0, 526, 655)},
    "universe.deepfield": {1: (10.1, 9.4, 595, 735)},
    "universe.starfield": {1: (9.4, 8.2, 525, 697)},
}

# CAPPED[key][eyes] = (cpu s, peak MB) with the working copy of every eye cut to 2048 px: what the pairs, families and chain cost
CAPPED = {
    "collision.family": {6: (16.1, 701), 8: (16.8, 945)},
    "collision.family.universe": {6: (15.7, 759), 8: (19.0, 1012)},
    "collision.infinity": {2: (6.3, 547)},
    "collision.kiss": {2: (5.3, 546)},
    "collision.trio": {3: (11.5, 785)},
    "singles.clean": {1: (3.3, 567)},
    "singles.elements": {1: (14.8, 841)},
    "singles.powder": {1: (9.1, 681)},
    "singles.radiance": {1: (6.5, 852)},
    "universe.deepfield": {1: (8.0, 548)},
    "universe.echo": {1: (9.7, 587), 6: (21.3, 815)},
    "universe.vortex": {1: (8.1, 478)},
}

# PREVIEW[key][eyes] = (cold s, warm s with new eyes, warm s with the same eyes (the design alone), per-eye preparation s, peak MB):
# a 1024 px preview, quiet core
PREVIEW = {
    "singles.powder": {1: (1.72, 1.4, 0.88, 0.52, 236)},
    "singles.splash": {1: (1.16, 0.94, 0.51, 0.43, 182)},
    "singles.elements": {1: (1.51, 1.34, 0.83, 0.51, 188)},
    "singles.radiance": {1: (1.07, 0.89, 0.41, 0.48, 167)},
    "singles.gold": {1: (1.11, 0.95, 0.43, 0.52, 165)},
    "singles.clean": {1: (0.72, 0.58, 0.05, 0.53, 164)},
    "collision.infinity": {2: (1.3, 1.08, 0.33, 0.75, 245)},
    "collision.infinity.clean": {2: (0.98, 0.91, 0.11, 0.8, 175)},
    "collision.infinity.universe": {2: (1.37, 1.15, 0.46, 0.69, 242)},
    "collision.kiss": {2: (1.13, 0.92, 0.22, 0.7, 244)},
    "collision.kiss.universe": {2: (1.29, 1.1, 0.37, 0.73, 244)},
    "collision.trio": {3: (2.05, 1.79, 0.52, 1.27, 267)},
    "collision.trio.universe": {3: (2.48, 2.09, 0.86, 1.23, 302)},
    "collision.family": {4: (1.94, 1.57, 0.48, 1.09, 285), 5: (2.41, 2.12, 0.63, 1.49, 295), 6: (2.66, 2.39, 0.66, 1.73, 310), 7: (3.31, 3.0, 0.81, 2.19, 324), 8: (3.33, 3.03, 0.9, 2.13, 337)},
    "collision.family.universe": {6: (3.08, 2.74, 1.05, 1.69, 382), 8: (4.14, 3.91, 1.66, 2.25, 487)},
    "collision.chain": {3: (1.57, 1.24, 0.3, 0.94, 268), 4: (1.75, 1.42, 0.39, 1.03, 283), 5: (1.8, 1.64, 0.37, 1.27, 299), 6: (2.17, 2.02, 0.43, 1.59, 314)},
    "universe.echo": {1: (2.33, 2.07, 0.9, 1.17, 254), 2: (3.47, 3.21, 0.83, 2.38, 402), 3: (5.08, 4.64, 1.68, 2.96, 418), 4: (5.85, 5.2, 1.28, 3.92, 444), 5: (6.6, 6.32, 1.44, 4.88, 532), 6: (7.37, 7.2, 1.45, 5.75, 612)},
    "universe.vortex": {1: (2.69, 2.11, 0.81, 1.3, 281)},
    "universe.deepfield": {1: (2.22, 1.98, 0.73, 1.25, 280)},
    "universe.starfield": {1: (1.42, 1.24, 0.37, 0.87, 228)},
}
# END BAKED


# ----------------------------------------------------------------------------- keys
def cost_key(engine, bg="dark", look=None):
    """The cost key of a design from catalogue.engine_for(...): module.design, .clean for the clean variant, .universe for a design drawn over
    a universe fill (bg = "universe"). A universe look other than the default (vortex, deepfield, starfield: the chip of the tile) has a row of
    its own: pass look. legacy designs have no key (the legacy engine has its own estimate in master_compose)."""
    if not engine or engine.get("module") == "legacy":
        raise NoCost("the legacy engine has no row in this table")
    key = f"{engine['module']}.{look if (look and engine['module'] == 'universe') else engine['design']}"
    if engine.get("clean"):
        key += ".clean"
    if bg == "universe":
        key += ".universe"
    return key


def _row(table, key, n):
    rows = table.get(key)
    if not rows or n not in rows:
        raise NoCost(f"no measured row for {key} with {n} eyes")
    return rows[n]


def known(key, n):
    return key in MASTER and n in MASTER[key]


def slow_factor():
    return cpu_probe.style_slow_cpu()


# ----------------------------------------------------------------------------- the master
def cpu(key, n, side=4096):
    """Quiet-core CPU seconds of the master render alone. side: the working copy of an eye the layout allows (the registry's work_side):
    at 2048 or less the capped row is used where the spike measured one, else the uncapped row (an upper bound)."""
    if side and side <= 2048 and key in CAPPED and n in CAPPED[key]:
        return CAPPED[key][n][0]
    return _row(MASTER, key, n)[0]


def step_need(design, n, size=4096, factor=None, side=None):
    """Seconds a call needs to make the master (or the step) of n eyes of a design on the real instance: the formula in the module
    docstring. design: a cost key. size is the canvas's long side; the table is for 4096, a smaller canvas is refused rather than guessed
    (previews have preview_need). side: the eye working copy cap (None: 4096)."""
    if size < 4096:
        raise NoCost("step_need is for the 4096 px master; use preview_need for a preview")
    F = slow_factor() if factor is None else float(factor)
    c = cpu(design, n, side or 4096)
    return F * (c + DECODE_S_PER_EYE * n + ENCODE_S) + COLD_START_S + STORAGE_READ_S_PER_EYE * n + UPLOAD_S


def est_mb(design, n, size=4096, side=None):
    """Peak memory in MB of the master render on Linux: the cold peak of the table (the capped row where the layout caps the working
    copy) times the Linux allowance, rounded up."""
    if size < 4096:
        raise NoCost("est_mb is for the 4096 px master")
    if side and side <= 2048 and design in CAPPED and n in CAPPED[design]:
        peak = CAPPED[design][n][1]
    else:
        peak = _row(MASTER, design, n)[2]
    return int(-(-peak * LINUX_ALLOWANCE // 1))


def break_even_factor(design, n, budget=WORK_BUDGET_S, side=None):
    """The slow factor at which step_need reaches the budget: above it the step can never succeed (a configuration error, not busy)."""
    c = cpu(design, n, side or 4096)
    fixed = COLD_START_S + STORAGE_READ_S_PER_EYE * n + UPLOAD_S
    return (budget - fixed) / (c + DECODE_S_PER_EYE * n + ENCODE_S)


def assess(design, n, size=4096, side=None, factor=None, budget=WORK_BUDGET_S, mem_budget=None):
    """Can a step of this design run at all? {need_s, est_mb, ok, why}: why is None, "time" (the need passes the work budget at this factor:
    the step can never finish, a configuration error) or "memory" (the estimate passes the memory budget), "no_cost" when there is no row."""
    try:
        need, mb = step_need(design, n, size, factor, side), est_mb(design, n, size, side)
    except NoCost:
        return {"need_s": None, "est_mb": None, "ok": False, "why": "no_cost"}
    why = "time" if need > budget else ("memory" if mb > (MEM_BUDGET_MB if mem_budget is None else mem_budget) else None)
    return {"need_s": round(need, 2), "est_mb": mb, "ok": why is None, "why": why}


def exceeds_step_budget(need_s, budget=STYLE_STEP_BUDGET):
    """The planner's rule: a master that needs more than the step budget is cut into steps (WP6b); otherwise it is one art step."""
    return need_s > budget


# ----------------------------------------------------------------------------- previews and tiles
def preview_need(design, n, size=1024, factor=None, new_eyes=True):
    """Seconds of a warm preview of one design on the real instance: F x (warm render) + 0.1 s per eye of request decode. new_eyes False is
    the design alone on eyes already prepared (a second tile of the same call). size 1024 is the table; 480 scales the design part by the
    pixel count (floored at TILE_AREA_FLOOR), the preparation stays whole: an estimate the first live measurement replaces."""
    F = slow_factor() if factor is None else float(factor)
    _cold, warm_new, warm_same, prep, _mb = _row(PREVIEW, design, n)
    scale = 1.0 if size >= 1024 else max(TILE_AREA_FLOOR, (size / 1024.0) ** 2)
    render = warm_same * scale + (prep if new_eyes else 0.0)
    return F * render + PREVIEW_DECODE_S_PER_EYE * n


def tiles_need(designs, n, size=480, factor=None):
    """Seconds of one call that makes the tiles of several designs on one eye preparation: the preparation once, then each design alone.
    designs: cost keys. The compose handler refuses a call over 40 s (422 too_many_styles)."""
    F = slow_factor() if factor is None else float(factor)
    scale = 1.0 if size >= 1024 else max(TILE_AREA_FLOOR, (size / 1024.0) ** 2)
    prep = max((_row(PREVIEW, d, n)[3] for d in designs), default=0.0)
    return F * (prep + sum(_row(PREVIEW, d, n)[2] * scale + TILE_OVERHEAD_S for d in designs)) + PREVIEW_DECODE_S_PER_EYE * n
