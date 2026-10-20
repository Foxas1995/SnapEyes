# -*- coding: utf-8 -*-
"""styles.ensemble.base: the renderer every look of the ensemble family shares (the pairs and families of whole irises: Clean Duo, Radiance Duo, Family Orbit,
Light Circle, Radiance Family). Ported from the laboratory of the pairs and families round of 2026-10-20 (proto_pf/base.py, branch v3-proto-pf), with the
production seed (the plan's seed key and the eyes' ids, api/_lib/styles/seeds.py), the plan's frozen choices and the customer's words.

The pipeline is the singles' own (singles/kit.py render_single) widened from one disc to several, and nothing else:
  plan (the geometry of a look at the canonical 1024 px, pure arithmetic) -> every iris graded and snapped at the size it is drawn at (K.place_iris: the declared
  finish at masters, the F3 feather) -> float canvas -> the look's effect draws matter into the float canvas only (it never sees an iris) -> tone map -> dither ->
  every iris pasted LAST (K.paste_iris), byte for byte inside 0.974 R -> the customer's names and date (text.draw_names, the only words) -> Result.
So the artwork charter holds by construction: an iris is never repainted, blurred or recoloured, and nothing is drawn over a pupil (T1, T2, T6 are measured by
checks.selfcheck on every render the caller asks it of, and on every master).

PREVIEW == MASTER: the geometry is laid out at 1024 px and a larger render scales that geometry (the canvases are exact multiples of the 1024 one, as
collision.scenes.canvas_size makes them); the seed is made from the eyes' ids and the plan's seed key, never from the size, the canvas, the words or the pixels.
"""
from __future__ import annotations

import time

import numpy as np
from PIL import Image

from .. import core as C
from .. import seeds as SD
from .. import text as TX
from ..collision import scenes as CS
from ..singles import kit as K

REF = 1024
WALL = "9:19.5"


class Plan:
    """The geometry of one picture at the canonical 1024 px: fmt, W, H (the 1024 canvas), discs [(cx, cy, R)] in canvas order, info (whatever else the
    look needs to draw, in 1024 px units or as shares), n."""

    def __init__(self, fmt, discs, info=None):
        self.fmt = fmt
        self.W, self.H = CS.canvas_size(fmt, REF)
        self.S = min(self.W, self.H)
        self.discs = [tuple(float(v) for v in d) for d in discs]
        self.info = dict(info or {})
        self.n = len(self.discs)


def fit_points(pts, box, max_d=None, prefer=None):
    """Unit-diameter centres pts [(x, y)] -> (D px, [(cx, cy)]): the largest D at which the arrangement (each disc a unit diameter) fits box
    (x0, y0, x1, y1), capped at max_d, centred on prefer or on the box centre."""
    x0, y0, x1, y1 = box
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w, h = max(xs) - min(xs) + 1.0, max(ys) - min(ys) + 1.0
    D = min((x1 - x0) / w, (y1 - y0) / h)
    if max_d is not None:
        D = min(D, max_d)
    mx, my = (max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0
    bx, by = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    if prefer is not None:
        hw, hh = w * D / 2.0, h * D / 2.0
        bx = min(max(prefer[0], x0 + hw), x1 - hw) if x1 - x0 >= 2 * hw else bx
        by = min(max(prefer[1], y0 + hh), y1 - hh) if y1 - y0 >= 2 * hh else by
    return D, [(bx + (px - mx) * D, by + (py - my) * D) for px, py in pts]


def snap_ref(cx, cy, R):
    """The whole-pixel geometry a disc requested at (cx, cy, R) gets at 1024 px (K._snap: place_disc's own arithmetic, no grading)."""
    return K._snap(cx, cy, R)


TEXT_SHRINK = 0.94           # with the customer's names or date the artwork moves up 0.03 S and shrinks to 0.94 (the singles' and the collision family's own rule)
TEXT_LIFT = 0.03
TEXT_Y = 0.93                # the baseline of the lockup, share of H


def with_text(plan):
    """The plan made room for a caption: every disc moves about the canvas centre by 0.94 and up by 0.03 S (and a look's own points with it)."""
    W, H, S = plan.W, plan.H, plan.S

    def tx(x):
        return W / 2.0 + TEXT_SHRINK * (x - W / 2.0)

    def ty(y):
        return H / 2.0 + TEXT_SHRINK * (y - H / 2.0) - TEXT_LIFT * S
    info = dict(plan.info)
    if "centre" in info:
        info["centre"] = (tx(info["centre"][0]), ty(info["centre"][1]))
    return Plan(plan.fmt, [(tx(x), ty(y), TEXT_SHRINK * r) for x, y, r in plan.discs], info)


class _TF:
    """A frame as text.draw_names reads it."""

    def __init__(self, W, H, S):
        self.W, self.H, self.S, self.text_y = W, H, S, TEXT_Y * H


class _F:
    """A frame as K.place_iris reads it: a circle."""
    __slots__ = ("cx", "cy", "R")

    def __init__(self, cx, cy, R):
        self.cx, self.cy, self.R = cx, cy, R


def text_box(W, H, S):
    """The caption's box (the singles' rule, kit.frame_for): matter is thinned under it (kit.text_fade)."""
    y = TEXT_Y * H
    bw = 0.62 * W
    return (W / 2.0 - bw / 2.0, y - 0.045 * S, W / 2.0 + bw / 2.0, y + 0.03 * S)


class PCtx:
    """What an effect receives (a duck-typed K.MCtx for several discs): W, H, S, wall, stretch, discs (the placed core Discs with exact cx, cy, R), irises,
    seed, opts, frozen, rand(tag, eye), log, text_box. The effect draws into the float canvas only."""

    def __init__(self, design, fmt, W, H, discs, irises, opts, seed, plan, k, frozen=None, has_text=False):
        self.design = design
        self.fmt = fmt
        self.W, self.H, self.S = W, H, min(W, H)
        self.wall = fmt == WALL
        self.discs = discs
        self.irises = irises
        self.opts = dict(opts or {})
        self.seed = int(seed)
        self.plan = plan
        self.k = k                                   # canvas px per 1024 px of the plan
        self.frozen = dict(frozen or {})
        self.stretch = 1.0
        self.text_box = text_box(W, H, self.S) if has_text else None
        self.caption_accent = None
        self.post = []
        self.log = {}
        self.eye_seeds = [self.seed] * len(discs)

    def rand(self, tag, eye=None):
        return C.Rand(self.seed, tag if eye is None else f"{tag}#{int(eye)}")

    def count(self, density):
        return C.particle_count(density, self.W, self.H)

    def fade_caption(self, light, floor=0.25):
        return light


class Result:
    __slots__ = ("img", "img8", "discs", "d3s", "ctx", "plan", "info", "times", "design", "fmt", "size", "text_log", "customer", "seed", "frozen")


def render(spec, design, eyes, fmt, size, names="", date="", opts=None, key=None, frozen=None):
    """One picture of a look. spec: the look's entry (looks.LOOKS[design]); eyes: Iris objects in canvas order; fmt: a canvas the look has a scene on; size: the
    long side in px (1024 a preview, 4096 a master); names: the lockup line of the customer's names; date: the date line; opts: the look's options (the
    laboratory's); key: the plan's seed key (seeds.py); frozen: the choices the plan fixed (a look reads ctx.frozen; a look that decides something itself
    records it in ctx.log["frozen"]). Returns Result (img PIL, img8, discs, d3s, ctx, plan, times, text_log)."""
    t0 = time.perf_counter()
    irises = list(eyes)
    n = len(irises)
    o = dict(opts or {})
    names, date = TX.clean(names), TX.clean(date)
    plan = spec["plan"](n, fmt, o)
    has_text = bool(names or date)
    if has_text:
        plan = with_text(plan)
    W, H = CS.canvas_size(fmt, int(size))
    k = W / float(plan.W)
    g0 = sum(ir.grade_seconds for ir in irises)
    discs, d3s = [], []
    for i, (ir, (cx, cy, R)) in enumerate(zip(irises, plan.discs)):
        sx, sy, sR = snap_ref(cx, cy, R)
        f = _F(sx * k, sy * k, sR * k) if int(size) != REF else _F(sx, sy, sR)
        d, d3 = K.place_iris(ir, f, None, sharpen=o.get("sharpen", True), limb=o.get("limb"))
        d.index = d3.index = i
        discs.append(d)
        d3s.append(d3)
        ir.ring
    t1 = time.perf_counter()
    seed = SD.seed_for_key([ir.eye_id for ir in irises], key)
    ctx = PCtx(design, fmt, W, H, discs, irises, o, seed, plan, k, frozen=frozen, has_text=has_text)
    cv = C.canvas(W, H, spec.get("bg", "#040507"))
    spec["fx"](cv, ctx)
    t2 = time.perf_counter()
    K.tone_map_bands(cv, o.get("knee", C.KNEE), o.get("whiten", C.WHITEN))
    img8 = C.dither_quantize(cv, ctx.seed)
    del cv
    for d3 in d3s:
        K.paste_iris(img8, d3)
    for f_ in ctx.post:
        f_(img8)
    img = Image.fromarray(img8)
    t3 = time.perf_counter()
    text_log = TX.draw_names(img, _TF(W, H, min(W, H)), names, date, spec.get("name_colour", TX.NAME_WARM)) if has_text else []
    if text_log:
        img8 = np.asarray(img).copy()
    t4 = time.perf_counter()
    r = Result()
    r.img, r.img8, r.discs, r.d3s, r.ctx, r.plan, r.design, r.fmt, r.size = img, img8, discs, d3s, ctx, plan, design, fmt, int(size)
    r.text_log = text_log
    r.customer = [s for s in (names, date) if s]
    r.seed = seed
    r.frozen = dict(ctx.log.get("frozen") or ctx.frozen or {})
    g = sum(ir.grade_seconds for ir in irises) - g0
    r.times = {"grade": round(g, 3), "place": round(t1 - t0 - g, 3), "effect": round(t2 - t1, 3), "finish": round(t3 - t2, 3), "text": round(t4 - t3, 3),
               "total": round(t4 - t0, 3), "render_without_grade": round(t4 - t0 - g, 3)}
    r.info = {"design": design, "fmt": fmt, "size": int(size), "n": n, "seed": seed, "classes": [ir.cls for ir in irises], "log": ctx.log}
    return r
