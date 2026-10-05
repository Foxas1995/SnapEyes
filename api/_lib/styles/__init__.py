# -*- coding: utf-8 -*-
"""api/_lib/styles: the v3 style engine package. The shared foundation (core, layouts, text, plates, atlas, costs, selfcheck) lives in
this package; each engine family is a sub package of its own (singles, collision, universe) that lands in its own work package.

THIS FILE IMPORTS NO ENGINE AND NO FOUNDATION MODULE. enhance, checkout, analyze and the webhook import the package for the profile
and the plan only, so an engine (numpy and Pillow heavy, plates, atlases) is loaded lazily, per family, on first use, and
catalogue.engine_built() asks importlib for api/_lib/styles/<family> without importing the family (importing the package runs
this file: keep it light, test IE2 holds it to a few milliseconds and to an empty sys.modules of engines).

The contract an engine family implements (a family is the sub package api/_lib/styles/<family>; each function takes the spec of
api/_lib/catalogue.py and answers for the design the catalogue names):
    resolve(spec, profiles, eyes=None) -> Plan   no render: layout, design used, fallback, canvas, contact distances, seed key, plates needed; with the eyes
                                             (the families that take them: wants_eyes) also the choices that depend on the pixels, frozen (WP7B)
    preview(eyes, spec, size=1024, watermark=False) -> Preview     one style, one canvas
    tiles(eyes, styles, spec, size=480) -> dict                    several styles on one eye preparation
and the master plan's two (api/_lib/styles/steps.py: the plan record, the steps and the state machine that runs them, the guards in guard.py):
    plan_steps(plan) -> [step]                                     the steps of a plan: one "art" step by default
    run_step(ctx, plan, step, k, rerun, after) -> {out, done}      one step through the state machine (claim, try record, guards, done record)
This module only dispatches: it finds the family the catalogue names for the style and the eye count, loads it, and calls it. A family
that is not in the repository raises EngineNotBuilt (never an ImportError that reads like a bug): the catalogue already refuses to
route to such a style (catalogue.engine_built), this is the second wall.

Preview is what a family's preview() answers (below); watermarked() is the one place a preview gets its watermark, the words of the free
preview that make a picture of a customer's iris not the product (an engine never draws it: the paid file has none). Outside the discs the
engine reports it is the legacy engine's own watermark (api/_lib/iris.py, a tile anchored to the canvas and the badge); on each disc it is
the iris-anchored overlay (api/_lib/preview.py watermark: the same words, angle and phase in the disc's own frame in every view of the iris,
work package WP10).

Module rule of the v3 work: every module starts with the __future__ import below (Vercel's default Python is 3.12).
"""
from __future__ import annotations

import importlib

ENGINE_FAMILIES = ("singles", "collision", "universe")      # the engine packages; legacy styles never come through here

# The version of the engine's PICTURES. It changes if and only if a golden changes (scripts/styles_tests/data/engine_v.json records it with the
# hashes of the golden files and v3steps compares them): a plan records the version it was made under and the master step holds an order whose
# plan was made under another one (engine_skew: a deploy between payment and master must never draw a picture the preview did not show).
ENGINE_V = 4          # 1: step A (the prototype's seed, from the bytes of the iris); 2: step B of the seed change for the singles (WP5B: from the eye ids and the plan's
                      # seed key); 3: step B for the collision family (WP7B: the same seed, the names out of it, the pixel decisions made once and frozen in the plan);
                      # 4: step B for the universe family (WP8B: the same seed, the per eye seeds derived from it, the plates version in every pick, the pair's fallback frozen)


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
               (discs may carry a fourth number: the rotation of the iris in degrees, counter clockwise, where a layout turns it)
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


def watermarked(pv, lang=None, note=None, n_eyes=None):
    """The free-preview picture of a Preview: its clean img with the preview watermark (a faint rotated tile of words over the whole picture,
    anchored to the canvas and scaled to at most 1.33 times the disc diameter as the legacy multi-eye preview does, the badge at the top, and on
    every iris disc the words 3.5 times as strong, anchored to the IRIS: api/_lib/preview.py watermark). note: one short line under the badge for
    a picture that draws no caption of its own (the AI-generated sample's label). n_eyes: the irises the picture holds (default: one studio graded
    frame per eye, which every family reports in pv.graded): a family that reports fewer discs than that gets the whole canvas marked at the iris
    strength, never the faint canvas tile alone (preview.watermark). Returns a new PIL image; the Preview is not changed."""
    from .. import preview as P
    if n_eyes is None and isinstance(pv.graded, (list, tuple)) and pv.graded:
        n_eyes = len(pv.graded)
    return P.watermark(pv.img, WATERMARK_ACCENT, list(pv.discs or ()), lang=lang, note=note, n_eyes=n_eyes)


def _engine_of(spec):
    from .. import catalogue as C                 # cheap (reads two literals); imported here so that importing the package stays light
    style, n = spec.get("style"), spec.get("eyes")
    e = C.engine_for(style, n)
    if e is None:
        raise EngineNotBuilt(f"no engine for style {style!r} with {n!r} eyes")
    if e["module"] == "legacy":
        raise EngineNotBuilt("a legacy style is drawn by the legacy engine (api/_lib/iris.py), not by the style package")
    return e


def wants_eyes(spec):
    """Does the family of this style make its plan from the eyes' pixels as well (resolve(spec, profiles, eyes))? The collision family does: which iris
    is in front, whether a contact is a hairline and the woven or stacked lens of a pair depend on the luminance and the colour of the irises, which a
    sealed profile does not hold. Read from the signature of the family's resolve, never learnt by a TypeError."""
    import inspect
    try:
        return "eyes" in inspect.signature(family(_engine_of(spec)["module"]).resolve).parameters
    except EngineNotBuilt:
        return False


def resolve(spec, profiles, eyes=None):
    """The plan of a style (no render): the family's resolve(spec, profiles). eyes: the eyes as Iris objects, for a family that takes them (wants_eyes): its
    plan is then the whole plan, with the choices that depend on the pixels; a family that does not take them ignores the argument."""
    fam = family(_engine_of(spec)["module"])
    if eyes is not None and wants_eyes(spec):
        return fam.resolve(spec, profiles, eyes=eyes)
    return fam.resolve(spec, profiles)


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


def tiles(eyes, styles, spec, size=480, per_style=None):
    """{style id: Preview} of several styles on ONE eye preparation: the eye objects (their grade caches, ring, class and statistics) are shared by
    every tile, so the preparation is paid once. A family renders the styles that are its own (its tiles()); styles of different families are
    split by family and rendered one family after the other on the same eyes. per_style: {style: {spec key: value}}, what differs from spec for a
    style (its layout, its canvas, its options): a family then draws those styles one by one (its preview()) on the same eyes. The answer is in the
    order the styles were asked for, each Preview clean (watermarked() makes the free tile from it). A tile does not depend on the other tiles of
    the call (test IE7)."""
    per_style = per_style or {}
    groups = {}
    for s in styles:
        groups.setdefault(_engine_of(dict(spec, style=s, **per_style.get(s, {})))["module"], []).append(s)
    made = {}
    for module, ids in groups.items():
        fam = family(module)
        if any(per_style.get(s) for s in ids):
            made.update({s: fam.preview(eyes, dict(spec, style=s, frozen=None, **per_style.get(s, {})), size=size) for s in ids})
        else:
            made.update(fam.tiles(eyes, ids, spec, size=size))
    return {s: made[s] for s in styles}
