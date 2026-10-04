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
This module only dispatches: it finds the family the catalogue names for the style and the eye count, loads it, and calls it. A family
that is not in the repository raises EngineNotBuilt (never an ImportError that reads like a bug): the catalogue already refuses to
route to such a style (catalogue.engine_built), this is the second wall.

Module rule of the v3 work: every module starts with the __future__ import below (Vercel's default Python is 3.12).
"""
from __future__ import annotations

import importlib

ENGINE_FAMILIES = ("singles", "collision", "universe")      # the engine packages; legacy styles never come through here


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


def preview(eyes, spec, size=1024, watermark=False):
    return family(_engine_of(spec)["module"]).preview(eyes, spec, size=size, watermark=watermark)


def tiles(eyes, styles, spec, size=480):
    """The tiles of several styles of one family on one eye preparation. Styles of different families are separate calls."""
    modules = {_engine_of(dict(spec, style=s))["module"] for s in styles}
    if len(modules) != 1:
        raise EngineNotBuilt("tiles() renders the styles of one engine family at a time")
    return family(modules.pop()).tiles(eyes, styles, spec, size=size)
