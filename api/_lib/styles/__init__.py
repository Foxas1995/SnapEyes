# -*- coding: utf-8 -*-
"""api/_lib/styles: the v3 style engine package. The shared foundation (core, layouts, text, plates, atlas, costs, selfcheck) lives in
this package; each engine family is a sub package of its own (singles, collision, universe) that lands in its own work package.

THIS FILE IMPORTS NO ENGINE AND NO FOUNDATION MODULE. enhance, checkout, analyze and the webhook import the package for the profile
and the plan only, so an engine (numpy and Pillow heavy, plates, atlases) is loaded lazily, per family, on first use, and
catalogue.engine_built() asks importlib for api/_lib/styles/<family> without importing the family (importing the package runs
this file: keep it light, test IE2 holds it to a few milliseconds and to an empty sys.modules of engines).

The contract an engine family implements (a family is the sub package api/_lib/styles/<family>; each function takes the spec of
api/_lib/catalogue.py and answers for the design the catalogue names):
    resolve(spec, profiles) -> Plan          no pixels: layout, design used, fallback, canvas, contact distances, seed key, plates needed
    preview(eyes, spec, size=1024, watermark=False) -> Preview     one style, one canvas
    tiles(eyes, styles, spec, size=480) -> dict                    several styles on one eye preparation
and the master plan's two (api/_lib/styles/steps.py: the plan record, the steps and the state machine that runs them, the guards in guard.py):
    plan_steps(plan) -> [step]                                     the steps of a plan: one "art" step by default
    run_step(ctx, plan, step, k, rerun, after) -> {out, done}      one step through the state machine (claim, try record, guards, done record)
This module only dispatches: it finds the family the catalogue names for the style and the eye count, loads it, and calls it. A family
that is not in the repository raises EngineNotBuilt (never an ImportError that reads like a bug): the catalogue already refuses to
route to such a style (catalogue.engine_built), this is the second wall.

Preview is what a family's preview() answers (below); watermarked() is the one place a preview gets its watermark, the words of the free
preview that make a picture of a customer's iris not the product (an engine never draws it: the paid file has none). It is the legacy
engine's own watermark (api/_lib/iris.py) laid on the picture with the discs the engine reports; the iris-anchored version of the compose
work package replaces it here, in one place.

Module rule of the v3 work: every module starts with the __future__ import below (Vercel's default Python is 3.12).
"""
from __future__ import annotations

import importlib

ENGINE_FAMILIES = ("singles", "collision", "universe")      # the engine packages; legacy styles never come through here

# The version of the engine's PICTURES. It changes if and only if a golden changes (scripts/styles_tests/data/engine_v.json records it with the
# hashes of the golden files and v3steps compares them): a plan records the version it was made under and the master step holds an order whose
# plan was made under another one (engine_skew: a deploy between payment and master must never draw a picture the preview did not show).
ENGINE_V = 1


class EngineNotBuilt(LookupError):
    """The style names an engine family that is not in the repository (a laboratory or planned id before its package landed)."""


def family(name):
    """The engine package api/_lib/styles/<name>, imported on first use. EngineNotBuilt when it is not there."""
    if name not in ENGINE_FAMILIES:
        raise EngineNotBuilt(f"{name!r} is not an engine family of the style package")
    try:
        return importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as e:
        if e.name == f"{__name__}.{name}":
            raise EngineNotBuilt(f"the engine family {name!r} is not in the repository") from None
        raise


class Preview:
    """What preview() answers for one style on one canvas.
    img        the picture, a PIL RGB image (the clean render: watermarked() makes the free preview from it)
    discs      [(cx, cy, r)] the visible iris discs in canvas pixels (pixel centres at +0.5), for the watermark and the checks
    graded     [uint8 array] the studio-graded frame of each iris (the legacy engine keeps it as an image: Image.fromarray gives iris.colour_qa its input)
    design, fmt, size, seed, cls    what was drawn: the design id of its family, the canvas, the long side, the seed, the eye colour class
    log        the engine's own facts (the plates it picked, the wind, the palette mode): small JSON-safe numbers and words
    times      seconds per stage (grade, place, effect, finish, text, total)
    text_log   what the text drawer drew (selfcheck T7 reads it); selfcheck the report of selfcheck.run when asked for, else None
    """
    __slots__ = ("img", "discs", "graded", "design", "fmt", "size", "seed", "cls", "log", "times", "text_log", "selfcheck", "ctx", "frame")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    @property
    def width(self):
        return self.img.size[0]

    @property
    def height(self):
        return self.img.size[1]


WATERMARK_ACCENT = (245, 197, 66)       # the badge's colour on a free preview of a style that has no accent of its own (the site's gold)


def watermarked(pv, lang=None):
    """The free-preview picture of a Preview: its clean img with the preview watermark (a faint rotated tile of words over the whole picture,
    drawn 3.5 times as strong on every iris disc, and the badge at the top). The tile is scaled to at most 1.33 times the disc diameter, as the
    legacy multi-eye preview does. Returns a new PIL image; the Preview is not changed."""
    from .. import iris as L
    u = min(pv.img.size)
    dia = max(2.0 * d[2] for d in pv.discs) if pv.discs else float(u)
    return L._watermark(pv.img.copy(), WATERMARK_ACCENT, u, tile_u=min(float(u), L.WM_DISC * dia), lang=lang, discs=list(pv.discs))


def _engine_of(spec):
    from .. import catalogue as C                 # cheap (reads two literals); imported here so that importing the package stays light
    style, n = spec.get("style"), spec.get("eyes")
    e = C.engine_for(style, n)
    if e is None:
        raise EngineNotBuilt(f"no engine for style {style!r} with {n!r} eyes")
    if e["module"] == "legacy":
        raise EngineNotBuilt("a legacy style is drawn by the legacy engine (api/_lib/iris.py), not by the style package")
    return e


def resolve(spec, profiles):
    return family(_engine_of(spec)["module"]).resolve(spec, profiles)


def preview(eyes, spec, size=1024, watermark=False, **kw):
    """One style, one canvas: a Preview (clean). watermark=True returns it with img replaced by the watermarked picture; kw go to the family
    (check=True: run the selfcheck report; the admin laboratory asks for it)."""
    pv = family(_engine_of(spec)["module"]).preview(eyes, spec, size=size, **kw)
    if watermark:
        pv.img = watermarked(pv)
    return pv


def plan_steps(plan, factor=None):
    """The steps of a master plan (api/_lib/styles/steps.py; imported here on use, so this package stays light)."""
    from . import steps
    return steps.plan_steps(plan, factor)


def run_step(ctx, plan, step, k=1, rerun=0, after=None):
    """One step of a master plan through its state machine (api/_lib/styles/steps.py run_step)."""
    from . import steps
    return steps.run_step(ctx, plan, step, k, rerun, after)


def tiles(eyes, styles, spec, size=480):
    """The tiles of several styles of one family on one eye preparation. Styles of different families are separate calls."""
    modules = {_engine_of(dict(spec, style=s))["module"] for s in styles}
    if len(modules) != 1:
        raise EngineNotBuilt("tiles() renders the styles of one engine family at a time")
    return family(modules.pop()).tiles(eyes, styles, spec, size=size)
