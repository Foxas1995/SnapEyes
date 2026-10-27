# -*- coding: utf-8 -*-
"""styles.lumen: the LIGHT family of the v3 engine. Five looks of one eye that the owner chose on 2026-10-20 from the two laboratory rounds of that day
("taip, darom Nebula, Supernova, Halo, Sparks, Aurora"), each drawn round the restored iris, which is pasted last, byte for byte, and never touched:

  nebula    Nebula      the iris as the bright heart of a nebula: a glow of its own colour at the limb, clouds of its partner colour further out, soft dust
                        lanes with lit edges, a young cluster and a sky of stars of every magnitude and colour temperature
  stardust  Supernova   the iris as a star that has just burst: clumpy jets of stardust leave every angle of the limb in the eye's own colour at that
                        angle, glitter, fine radial filaments, a broken shock shell, a white hot rim, a quiet field of stars
  halo      Halo        the iris backlit in its own colour: a soft bloom, a faint optical ring, a breath of mist, a tonal ground of its own deep shade
  sparks    Sparks      sparks and soft lights lifting off the limb on a wind, as if the iris were a coal: comet streaks, glints and a few large lights
  aurora    Aurora      curtains of northern light standing on the limb, the eye's own colour at the foot and its partner hue at the tips
  echo      Iris Echo   the iris in the middle of its own echo: the same iris enlarged behind it, its fibres radiating like a tunnel (2026-10-27)

No plate, no atlas, no model call: every look is light drawn from noise fields, Gaussian stamps and the eye's own ring colours (common.py). The pipeline is
the singles family's (api/_lib/styles/singles/kit.py: grade and place the iris, the F3 feather, the effect on the float canvas, the tone map, the dither,
the iris pasted LAST, the customer's words) with this family's own geometry (GEOM), so a picture obeys the same rules as Radiance's: inside 0.974 R it IS
the graded disc (T1, T6), nothing is drawn over the pupil, the only words are the customer's (T7), no hearts (T12). A picture is a function of the iris
pixels, of WHICH eye it shows (its eye_id) and of the plan's seed key (api/_lib/styles/seeds.py), and of nothing else: the preview, the order's draft and
the master of one eye seed alike, and the 4096 px master is the 1024 px preview drawn finer (sizes in R and S units, reduced grids of a fixed cell count).

The contract of api/_lib/styles/__init__.py, for this family (the singles family's, with no plate and nothing frozen):
    resolve(spec, profiles)                   the plan of a style that needs no pixels: canvas, geometry, seed key, the seed when the eye ids are known
    preview(eyes, spec, size, check=False)    one style on one eye, a Preview (styles.watermarked() makes the free preview of it)
    tiles(eyes, styles, spec, size)           several styles on one eye preparation
and the family's own render(design, eye, fmt, size, names, date, opts), which the golden suite calls.

The registry gives every style of the family the gate policy advisory with the lid rule, as Radiance's: the looks draw light round the limb and nothing
over the iris, so an eye that fails the lid rule is warned, never refused (the registry's text ships in the landing's bundle, so the reason is written here).

The effects read their discs and irises as LISTS (ctx.discs, ctx.irises): Nebula and Supernova draw round several irises with the very same code, so the
pair and family styles take them over as they are (nebula.fx_nebula, stardust.fx_stardust on a context of their own). The lab id of Supernova is
"stardust": the registry's legacy id of the old Supernova is the word itself, which no file but the registry may write (scripts/check_styles.mjs item 3).
Module rule: __future__ import (Vercel's default Python is 3.12).
"""
from __future__ import annotations

import time

from PIL import Image

from ... import catalogue as CT
from .. import core as C
from .. import layouts as LY
from .. import seeds as SD
from .. import text as TX
from ..singles import kit as K

DESIGNS = ("nebula", "stardust", "halo", "sparks", "aurora", "echo")
FORMATS = ("1:1", "4:5", "9:19.5")                                            # the canvases (the engine entries of the registry list the same)
SIZES = (64, 4096)                                                            # the long side a render may ask for
BG = "#000000"                                                                # every look lays its own sky or tonal ground on pure black by adding light

# per design and canvas: the iris radius as a share of S (S = the short side) and the centre y as a share of H (kit.SPECS has the singles' table; this is
# the light family's, read by frame_for below). The geometry of the laboratory rounds, which the owner's boards showed.
GEOM = {
    "nebula":   {"r": {"1:1": 0.255, "4:5": 0.255, "9:19.5": 0.262}, "cy": {"1:1": 0.500, "4:5": 0.450, "9:19.5": 0.400}},
    "stardust": {"r": {"1:1": 0.262, "4:5": 0.262, "9:19.5": 0.262}, "cy": {"1:1": 0.500, "4:5": 0.450, "9:19.5": 0.400}},
    "halo":     {"r": {"1:1": 0.300, "4:5": 0.300, "9:19.5": 0.300}, "cy": {"1:1": 0.500, "4:5": 0.450, "9:19.5": 0.400}},
    "sparks":   {"r": {"1:1": 0.285, "4:5": 0.285, "9:19.5": 0.285}, "cy": {"1:1": 0.520, "4:5": 0.470, "9:19.5": 0.410}},
    "aurora":   {"r": {"1:1": 0.262, "4:5": 0.262, "9:19.5": 0.262}, "cy": {"1:1": 0.500, "4:5": 0.450, "9:19.5": 0.400}},
    "echo":     {"r": {"1:1": 0.330, "4:5": 0.330, "9:19.5": 0.300}, "cy": {"1:1": 0.500, "4:5": 0.470, "9:19.5": 0.420}},
}


def _design(name):
    """{fx: the effect function}: a design module is imported on first use (numpy heavy work only when a look is drawn)."""
    if name == "nebula":
        from . import nebula as m
        return {"fx": m.fx_nebula}
    if name == "stardust":
        from . import stardust as m
        return {"fx": m.fx_stardust}
    if name == "halo":
        from . import halo as m
        return {"fx": m.fx_halo}
    if name == "sparks":
        from . import sparks as m
        return {"fx": m.fx_sparks}
    if name == "aurora":
        from . import aurora as m
        return {"fx": m.fx_aurora}
    if name == "echo":
        from . import echo as m
        return {"fx": m.fx_echo}
    raise KeyError(name)


def _style_of(design):
    """The registry id of the style a design draws (the seed key names the style; render() is called with the design alone)."""
    for sid in CT.ids():
        eng = CT.ENGINE[sid]["engine"]
        if eng and eng.get("module") == "lumen" and eng.get("design") == design:
            return sid
    raise KeyError(design)


def seed_key(style, design, opts=None, pv=None):
    """The plan's seed key of an artwork of this family (seeds.py names its fields), the shape of the singles family's: the registry id, the design, the
    ground, the clean flag (never clean), the layout id, the three options the buyer may choose and the plates version (None: the current one)."""
    o = opts if isinstance(opts, dict) else {}
    return {"style": style, "design_used": design, "bg": "dark", "clean": False, "layout": "single",
            "opts": {k: o.get(k) for k in SD.OPT_FIELDS}, "pv": CT.PLATES_VERSION if pv is None else int(pv)}


# ----------------------------------------------------------------------------- the frame and the render (the singles pipeline with this family's geometry)
def frame_for(design, fmt="1:1", size=1024, has_text=False, _ref=False):
    """kit.frame_for with the geometry of this family (GEOM): size is the LONG side in px (1024 a preview, 4096 a master). With text the artwork moves up
    0.03 S (not on the wallpaper, whose names sit at 0.80 H) and the iris shrinks x 0.94. PREVIEW == MASTER: the geometry is laid out at 1024 and snapped
    there exactly as the preview does; a master scales that snapped geometry up, so a 4096 file reduced to 1024 lines up with the preview."""
    W, H = LY.canvas_size(fmt, size)
    S = min(W, H)
    sp = GEOM[design]
    rf = sp["r"].get(fmt, K.DEFAULT_R)
    cyf = sp["cy"].get(fmt, 0.5)
    wall = fmt == LY.WALL
    f = K.Frame()
    f.design, f.fmt, f.W, f.H, f.S, f.wall, f.size, f.has_text = design, fmt, W, H, S, wall, size, bool(has_text)
    f.shrink = 0.94 if has_text else 1.0
    f.cx = W / 2.0
    f.cy = cyf * H - (0.03 * S if (has_text and not wall) else 0.0)
    f.R = rf * S * f.shrink
    f.key = f"single/{fmt}"
    f.text_y = (K.WALL_NAME_Y * H) if wall else 0.93 * H
    if size == K.REF_SIZE or _ref:
        f.cx, f.cy, f.R = K._snap(f.cx, f.cy, f.R)
    else:
        f1 = frame_for(design, fmt, K.REF_SIZE, has_text, _ref=True)
        f.cx, f.cy, f.R = f1.cx * (W / f1.W), f1.cy * (H / f1.H), f1.R * (size / float(K.REF_SIZE))
    if has_text:
        bw = 0.62 * W
        f.text_box = (W / 2.0 - bw / 2.0, f.text_y - 0.045 * S, W / 2.0 + bw / 2.0, f.text_y + 0.03 * S)
    else:
        f.text_box = None
    return f


def render_single(effect, iris, design, fmt="1:1", size=1024, names="", date="", bg=BG, name_colour=None, opts=None, times=None, seed=None, pv=None):
    """One artwork: kit.render_single step for step (frame, grade and place the iris with the F3 feather, the float canvas, the effect, the tone map in
    bands, the dither, the iris pasted LAST, the customer's names), with this family's frame. effect None draws nothing (the effect free picture the
    suite compares the iris with). Returns a kit.Result."""
    t0 = time.perf_counter()
    has_text = bool((names or "").strip() or (date or "").strip())
    frame = frame_for(design, fmt, size, has_text)
    g0 = iris.grade_seconds
    o_ = opts or {}
    d, d3 = K.place_iris(iris, frame, None, sharpen=o_.get("sharpen", True), limb=None)
    iris.ring
    t1 = time.perf_counter()
    ctx = K.MCtx(frame, d, iris, design, opts, seed=seed, pv=pv, frozen=None)
    cv = C.canvas(frame.W, frame.H, bg)
    if effect is not None:
        effect(cv, ctx)
    t2 = time.perf_counter()
    K.tone_map_bands(cv)
    img8 = C.dither_quantize(cv, ctx.seed)
    del cv
    K.paste_iris(img8, d3)
    for f in ctx.post:                      # zone B only (r >= 0.955 R), never zone A (no look of this family has one today)
        f(img8)
    t3 = time.perf_counter()
    img = Image.fromarray(img8)
    log = TX.draw_names(img, frame, names, date, name_colour or TX.NAME_WARM)
    t4 = time.perf_counter()
    r = K.Result()
    r.img, r.frame, r.d, r.d3, r.ctx, r.log = img, frame, d, d3, ctx, log
    g = iris.grade_seconds - g0
    r.times = {"grade": round(g, 3), "place": round(t1 - t0 - g, 3), "effect": round(t2 - t1, 3), "finish": round(t3 - t2, 3),
               "text": round(t4 - t3, 3), "total": round(t4 - t0, 3), "render_without_grade": round(t4 - t0 - g, 3)}
    if times is not None:
        times.update(r.times)
    r.img8_noText = None
    r.info = {"design": design, "fmt": fmt, "size": size, "seed": ctx.seed, "class": iris.cls}
    return r


def render(design, eye, fmt="1:1", size=1024, names="", date="", opts=None, times=None, name_colour=None, key=None):
    """One artwork of this family. eye: an Iris or the bytes of a restored iris square. size: the long side in px (1024 a preview, 4096 a master). names: the
    customer's names (a list, the old "Anna;Max" string or one line) and date, drawn small under the iris when given. key: the plan's seed key (seed_key();
    default: the design's own style, no options, the current plates version); the seed is made from it and from the eye's id (eye.eye_id). opts: the effect
    options of the laboratory ({design: {parameter: value}}). Returns a kit.Result: .img (PIL), .d (the placed disc), .ctx.log (the look's facts), .log
    (the text drawn), .times, .info."""
    if design not in DESIGNS:
        raise KeyError(design)
    if fmt not in FORMATS:
        raise ValueError(f"no canvas {fmt!r} (the canvases are {', '.join(FORMATS)})")
    if not SIZES[0] <= int(size) <= SIZES[1]:
        raise ValueError(f"a canvas of {size} px (from {SIZES[0]} to {SIZES[1]})")
    iris = K.load_eye(eye)
    fx = _design(design)["fx"]
    key = key if key is not None else seed_key(_style_of(design), design)
    seed = SD.seed_for_key([iris.eye_id], key)
    return render_single(fx, iris, design, fmt, int(size), TX.lockup(names), TX.clean(date), bg=BG, name_colour=name_colour, opts=opts, times=times,
                         seed=seed, pv=key["pv"])


# ----------------------------------------------------------------------------- the contract
def _engine(spec):
    """(engine entry, design, canvas) of the spec, or ValueError for a style that is not a style of this family."""
    style, n = spec.get("style"), spec.get("eyes", 1)
    e = CT.engine_for(style, n)
    if e is None or e.get("module") != "lumen":
        raise ValueError(f"{style!r} with {n!r} eyes is not a style of the light family")
    fmt = spec.get("canvas") or spec.get("format")
    return e, e["design"], (fmt if fmt in e["canvases"] else e["canvases"][0])


def _pv(spec):
    """The plates version a spec asks for (the plan's pv; absent: the current one). No look of this family reads a plate: the version only seeds."""
    pv = spec.get("pv")
    return pv if isinstance(pv, int) and not isinstance(pv, bool) and pv >= 0 else CT.PLATES_VERSION


def _opts3(spec):
    return spec.get("opts") if isinstance(spec.get("opts"), dict) else {}


def _profile_id(p):
    return p.get("eye_id") if isinstance(p, dict) else getattr(p, "eye_id", None)


def _eye_ids(spec, profiles):
    """[eye id] of the one eye of an artwork, or [] when it is not known: spec["eye_ids"] (the order's own record), else the id of the sealed profile. An id
    that is not 16 hex digits is no id."""
    ids = spec.get("eye_ids")
    if not isinstance(ids, (list, tuple)):
        ids = [_profile_id(p) for p in (profiles or [])]
    ids = list(ids)[:1]
    return ids if len(ids) == 1 and SD.is_eye_id(ids[0]) else []


def resolve(spec, profiles=None):
    """The plan of a style that needs no pixels (a few milliseconds): the design, the canvas, where the iris sits at 1024 px, the seed key and, when the eye
    is known, the seed. No plate is ever drawn from (plates []) and nothing is frozen. Names, date and canvas size are not part of the seed, so the same answer
    holds for the preview, the draft and the master of an eye."""
    e, design, fmt = _engine(spec)
    has_text = bool(TX.lockup(spec.get("names")) or TX.clean(spec.get("date")))
    fr = frame_for(design, fmt, 1024, has_text)
    key = seed_key(spec["style"], design, _opts3(spec), _pv(spec))
    ids = _eye_ids(spec, profiles)
    seed = SD.seed_for_key(ids, key) if ids else None
    return {"family": "lumen", "style": spec["style"], "design_used": design, "fallback": None, "layout": "single", "canvas": fmt, "clean": False,
            "size_ratio": [fr.W, fr.H], "iris_at_1024": {"cx": round(fr.cx, 3), "cy": round(fr.cy, 3), "R": round(fr.R, 3)},
            "seed_key": key, "seed_from": "eye_id", "eye_ids": ids, "seed": None if seed is None else str(seed), "frozen": {}, "plates": [],
            "steps": ["art"]}


def preview(eyes, spec, size=1024, check=False):
    """One style on one eye. eyes: a list of one Iris (or the bytes of a restored square). Returns a styles.Preview whose img is the CLEAN render: the
    dispatcher's watermark=True (or styles.watermarked) makes the free preview. check=True adds the self check report (T1, T6, T7, T12) to .selfcheck, as
    the singles family does; the master step stores it with the artwork. Preview.log["plates"] is [] (this family reads no plate)."""
    from .. import Preview
    if not isinstance(eyes, (list, tuple)) or len(eyes) != 1:
        raise ValueError("the light family draws exactly one eye")
    e, design, fmt = _engine(spec)
    names, date = TX.lockup(spec.get("names")), TX.clean(spec.get("date"))
    key = seed_key(spec["style"], design, _opts3(spec), _pv(spec))
    r = render(design, eyes[0], fmt, size, names, date, opts=spec.get("engine_opts"), key=key)
    d = r.d
    log = r.ctx.log
    log["plates"] = []
    pv = Preview(img=r.img, discs=[(d.cx, d.cy, d.R)], graded=[d.iris.graded(d.Sd)], design=design, fmt=fmt, size=int(size), seed=r.info["seed"],
                 cls=r.info["class"], log=log, times=r.times, text_log=r.log, ctx=r.ctx, frame=r.frame)
    if check:
        import numpy as np
        from .. import selfcheck as SC
        pv.selfcheck = SC.run(np.asarray(r.img), [d], text_log=r.log, customer=[names, date], ids=[spec["style"], design, "single"])
    return pv


def tiles(eyes, styles, spec, size=480):
    """{style id: Preview} of several styles of this family on one eye: the Iris is shared, so its ring, class and statistics are measured once. An
    exception of one tile is not caught here: the caller that serves a batch decides."""
    return {s: preview(eyes, dict(spec, style=s, frozen=None), size) for s in styles}
