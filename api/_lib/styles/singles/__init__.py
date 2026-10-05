# -*- coding: utf-8 -*-
"""styles.singles: the single-eye family of the v3 engine. Six designs, one eye each, drawn from the restored iris with the matter of the design
around it (the iris itself is pasted last, byte for byte, and is never touched):

  clean     Clean Iris       the restored iris alone on pure black, names small and optional
  powder    Powder Burst     dust, not smoke: a cloud plate mapped through the eye's own colours, grains, dust and iris chips in the wind
  splash    Splash           a photographed liquid crown, the liquid chosen by the colour of the eye
  elements  Elements         fire on the warmer half of the rim, water on the cooler half (held: the laboratory only)
  radiance  Radiance         thin rays of the eye's own colour from the limbus inside a dark moat
  gold      Celestial Gold   the owner-approved variant A: a black eclipse gap, an even corona of the rim's own gold, a hairline orbit

This is work package WP5, step A: the prototype's designs ported verbatim (kit.py, powder.py, splash.py, elements.py, radiance.py, gold.py here and
the primitives in api/_lib/styles/matter.py; scripts/styles_tests/port_singles.py lists every edit), with the seed formula of the prototype kept:
a picture is a function of the bytes of the iris it was made from, the design, the canvas and the size, and nothing else. The golden hashes of the
prototype's own pictures are replayed on this port by scripts/styles_tests/test_goldens_singles.py. Step B (after the master plan work) re-seeds
from eye_id and re-records them with a reviewed diff.

The contract of api/_lib/styles/__init__.py, for this family:
    resolve(spec, profiles)        the plan of a style that needs no pixels: canvas, geometry, seed key, steps
    preview(eyes, spec, size, check=False)    one style on one eye, a Preview (clean: styles.watermarked() makes the free preview)
    tiles(eyes, styles, spec, size)           several styles on one eye preparation
and the prototype's own entry, render(design, eye, fmt, size, names, date, opts), which the golden suite calls.

An eye is a styles.core.Iris (or the bytes of a restored square: kit.load_eye). Nothing here reads a path, a key or the network; the plates come from
styles.plates (the bundle at 1K, private storage at 4K), the two atlases from styles.atlas. Names and date are the customer's own words (text.py).
"""
from __future__ import annotations

from ... import catalogue as CT
from .. import text as TX
from . import kit as K

DESIGNS = ("powder", "splash", "elements", "radiance", "gold", "clean")      # the prototype's NAMES
FORMATS = ("1:1", "4:5", "9:19.5")                                            # the canvases (the engine entry of the registry lists the same)
T4_RANGES = {"powder": (0.45, 0.65), "elements": (0.55, 0.75)}                # T4, the black share of the picture: the other designs are measured, not bounded
SIZES = (64, 4096)                                                            # the long side a render may ask for


def _design(name):
    """{fx: the effect function (None for Clean), bg: the canvas ground, limb: the zone B darkening, if the design has one}. A design module is
    imported on first use (each pulls in its own plates and atlases)."""
    if name == "clean":
        return {"fx": None, "bg": "#000000"}
    if name == "powder":
        from . import powder as m
        return {"fx": m.fx_powder, "bg": "#07080A", "limb": {"mult": 0.55, "r0": 0.955}}
    if name == "splash":
        from . import splash as m
        return {"fx": m.fx_splash, "bg": "#050505"}
    if name == "elements":
        from . import elements as m
        return {"fx": m.fx_elements, "bg": "#050505"}
    if name == "radiance":
        from . import radiance as m
        return {"fx": m.fx_radiance, "bg": "#050508"}
    if name == "gold":
        from . import gold as m
        return {"fx": m.fx_gold, "bg": "#0B0D14"}
    raise KeyError(name)


def render(design, eye, fmt="1:1", size=1024, names="", date="", opts=None, times=None, name_colour=None):
    """One single artwork (the prototype's entry). eye: an Iris or the bytes of a restored iris square. size: the long side in px (1024 a
    preview, 4096 a master). names: the customer's names (a list, the old "Anna;Max" string or one line) and date, drawn small under the iris
    when given. Returns a kit.Result: .img (PIL), .d (the placed disc), .ctx.log (the design's facts), .log (the text drawn), .times, .info."""
    if design not in DESIGNS:
        raise KeyError(design)
    if fmt not in FORMATS:
        raise ValueError(f"no canvas {fmt!r} (the canvases are {', '.join(FORMATS)})")
    if not SIZES[0] <= int(size) <= SIZES[1]:
        raise ValueError(f"a canvas of {size} px (from {SIZES[0]} to {SIZES[1]})")
    iris = K.load_eye(eye)
    spec = _design(design)
    return K.render_single(spec["fx"], iris, design, fmt, int(size), TX.lockup(names), TX.clean(date), bg=spec["bg"], opts=opts, times=times,
                           name_colour=name_colour, limb=spec.get("limb"))


# ----------------------------------------------------------------------------- the contract
def _engine(spec):
    """(engine entry, design, canvas) of the spec, or ValueError for a style that is not a single-eye style of this family."""
    style, n = spec.get("style"), spec.get("eyes", 1)
    e = CT.engine_for(style, n)
    if e is None or e.get("module") != "singles":
        raise ValueError(f"{style!r} with {n!r} eyes is not a style of the singles family")
    fmt = spec.get("canvas") or spec.get("format")
    return e, e["design"], (fmt if fmt in e["canvases"] else e["canvases"][0])


def resolve(spec, profiles=None):
    """The plan of a style that needs no pixels (at most a few milliseconds): the design, the canvas, where the iris sits at 1024 px, and the key a
    seed is made of. The plates a plate style will draw from depend on the seed, and the seed is still the prototype's (the bytes of the iris), so
    they are not in the plan yet: plates is None until step B seeds from eye_id, which a profile carries. profiles are not read yet either."""
    e, design, fmt = _engine(spec)
    has_text = bool(TX.lockup(spec.get("names")) or TX.clean(spec.get("date")))
    fr = K.frame_for(design, fmt, 1024, has_text)
    opts = spec.get("opts") if isinstance(spec.get("opts"), dict) else {}
    return {"family": "singles", "style": spec["style"], "design_used": design, "fallback": None, "layout": "single", "canvas": fmt,
            "clean": bool(e.get("clean")), "size_ratio": [fr.W, fr.H], "iris_at_1024": {"cx": round(fr.cx, 3), "cy": round(fr.cy, 3), "R": round(fr.R, 3)},
            "seed_key": {"style": spec["style"], "design_used": design, "bg": "dark", "clean": bool(e.get("clean")), "layout": "single",
                         "opts": {k: opts.get(k) for k in ("swap", "rotate", "look")}, "pv": CT.PLATES_VERSION},
            "seed_from": "iris_bytes", "plates": None, "steps": ["art"]}


def preview(eyes, spec, size=1024, check=False):
    """One style on one eye. eyes: a list of one Iris (or the bytes of a restored square). Returns a styles.Preview whose img is the CLEAN render:
    the dispatcher's watermark=True (or styles.watermarked) makes the free preview. check=True adds the selfcheck report (T1, T6, T7, T12 and T4
    where the design has a range) to .selfcheck."""
    from .. import Preview
    if not isinstance(eyes, (list, tuple)) or len(eyes) != 1:
        raise ValueError("the singles family draws exactly one eye")
    e, design, fmt = _engine(spec)
    names, date = TX.lockup(spec.get("names")), TX.clean(spec.get("date"))
    r = render(design, eyes[0], fmt, size, names, date, opts=spec.get("engine_opts"))
    d = r.d
    pv = Preview(img=r.img, discs=[(d.cx, d.cy, d.R)], graded=[d.iris.graded(d.Sd)], design=design, fmt=fmt, size=int(size), seed=r.info["seed"], cls=r.info["class"],
                 log=r.ctx.log, times=r.times, text_log=r.log, ctx=r.ctx, frame=r.frame)
    if check:
        import numpy as np
        from .. import selfcheck as SC
        pv.selfcheck = SC.run(np.asarray(r.img), [d], text_log=r.log, customer=[names, date], ids=[spec["style"], design, "single"],
                              black_range=T4_RANGES.get(design))
    return pv


def tiles(eyes, styles, spec, size=480):
    """{style id: Preview} of several styles of this family on one eye: the Iris is shared, so its ring, class and statistics are measured once
    (a grade is per design, as its disc differs). An exception of one tile is not caught here: the caller that serves a batch decides."""
    return {s: preview(eyes, dict(spec, style=s), size) for s in styles}
