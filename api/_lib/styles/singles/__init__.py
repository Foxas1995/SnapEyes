# -*- coding: utf-8 -*-
"""styles.singles: the single-eye family of the v3 engine. Six designs, one eye each, drawn from the restored iris with the matter of the design
around it (the iris itself is pasted last, byte for byte, and is never touched):

  clean     Clean Iris       the restored iris alone on pure black, names small and optional
  powder    Powder Burst     dust, not smoke: a cloud plate mapped through the eye's own colours, grains, dust and iris chips in the wind
  splash    Splash           a photographed liquid crown, the liquid chosen by the colour of the eye
  elements  Elements         fire on the warmer half of the rim, water on the cooler half (held: the laboratory only)
  radiance  Radiance         thin rays of the eye's own colour from the limbus inside a dark moat
  gold      Celestial Gold   the owner-approved variant A: a black eclipse gap, an even corona of the rim's own gold, a hairline orbit

This is work package WP5: the prototype's designs ported verbatim (kit.py, powder.py, splash.py, elements.py, radiance.py, gold.py here and the
primitives in api/_lib/styles/matter.py; scripts/styles_tests/port_singles.py lists every edit). Step A kept the prototype's seed (the bytes of the
iris, the design and the canvas) and replayed the prototype's own pictures byte for byte. STEP B (WP5B, decision C9) changed the seed once and
nothing else: a picture is now a function of the iris pixels, of WHICH eye it shows (its eye_id, the id of the sealed profile) and of the plan's seed
key (api/_lib/styles/seeds.py: style, design, ground, clean flag, layout, options, plates version), and of nothing else: not the names, the date,
the canvas or its size, not the bytes the eye happens to arrive in. So the preview, the order's draft and the master of one eye seed alike, the
plates a plate style will pick are known before the render (resolve names them), and a plate added to the library later cannot change an older
order (every pick takes the spec's pv). The golden hashes were recorded again on this code (data/singles_goldens.json); the step A hashes are kept
(data/stepA/) and replayed with opts seed_mode "legacy", which seeds the old way: that this replay is byte for byte the step A recording is the proof
that the seed is the ONLY thing step B moved. The admin laboratory offers the same switch, so the owner can look at a board before and after.

The contract of api/_lib/styles/__init__.py, for this family:
    resolve(spec, profiles)        the plan of a style that needs no pixels: canvas, geometry, seed key, the seed and the plates (when the eye
                                   ids are known), what the plan freezes (the liquid of a splash)
    preview(eyes, spec, size, check=False)    one style on one eye, a Preview (clean: styles.watermarked() makes the free preview)
    tiles(eyes, styles, spec, size)           several styles on one eye preparation
and the prototype's own entry, render(design, eye, fmt, size, names, date, opts), which the golden suite calls.

An eye is a styles.core.Iris (or the bytes of a restored square: kit.load_eye). Nothing here reads a path, a key or the network; the plates come from
styles.plates (the bundle at 1K, private storage at 4K), the two atlases from styles.atlas. Names and date are the customer's own words (text.py).
"""
from __future__ import annotations

from ... import catalogue as CT
from .. import seeds as SD
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


def _style_of(design):
    """The registry id of the single style a design draws (the seed key names the style; render() is called with the design alone)."""
    for sid in CT.ids():
        eng = CT.ENGINE[sid]["engine"]
        if eng and eng.get("module") == "singles" and eng.get("design") == design:
            return sid
    raise KeyError(design)


def seed_key(style, design, clean=False, opts=None, pv=None):
    """The plan's seed key of a single artwork (seeds.py names its fields): the registry id, the design, the ground, the clean flag, the layout id,
    the three options the buyer may choose and the plates version (None: the current one)."""
    o = opts if isinstance(opts, dict) else {}
    return {"style": style, "design_used": design, "bg": "dark", "clean": bool(clean), "layout": "single",
            "opts": {k: o.get(k) for k in SD.OPT_FIELDS}, "pv": CT.PLATES_VERSION if pv is None else int(pv)}


def legacy_seed(iris, design, fmt):
    """The seed before WP5B (the prototype's: the bytes of the iris, the eye index 0, the design, the frame's key). Only for the laboratory's
    before and after switch and the replay of the step A goldens: never what a customer's picture is seeded with."""
    return K.C.seed_for(iris.raw, 0, design, f"single/{fmt}")


def render(design, eye, fmt="1:1", size=1024, names="", date="", opts=None, times=None, name_colour=None, key=None, frozen=None):
    """One single artwork (the prototype's entry). eye: an Iris or the bytes of a restored iris square. size: the long side in px (1024 a
    preview, 4096 a master). names: the customer's names (a list, the old "Anna;Max" string or one line) and date, drawn small under the iris
    when given. key: the plan's seed key (seed_key(); default: the design's own style, no options, the current plates version); the seed is
    made from it and from the eye's id (eye.eye_id). frozen: what the plan froze ({"liquid": ...}). opts is the effect options of the
    laboratory; opts["seed_mode"] == "legacy" seeds as before WP5B (legacy_seed). Returns a kit.Result: .img (PIL), .d (the placed disc),
    .ctx.log (the design's facts), .log (the text drawn), .times, .info."""
    if design not in DESIGNS:
        raise KeyError(design)
    if fmt not in FORMATS:
        raise ValueError(f"no canvas {fmt!r} (the canvases are {', '.join(FORMATS)})")
    if not SIZES[0] <= int(size) <= SIZES[1]:
        raise ValueError(f"a canvas of {size} px (from {SIZES[0]} to {SIZES[1]})")
    iris = K.load_eye(eye)
    spec = _design(design)
    key = key if key is not None else seed_key(_style_of(design), design)
    legacy = (opts or {}).get("seed_mode") == "legacy"
    seed = legacy_seed(iris, design, fmt) if legacy else SD.seed_for_key([iris.eye_id], key)
    return K.render_single(spec["fx"], iris, design, fmt, int(size), TX.lockup(names), TX.clean(date), bg=spec["bg"], opts=opts, times=times,
                           name_colour=name_colour, limb=spec.get("limb"), seed=seed, pv=key["pv"], frozen=frozen)


# ----------------------------------------------------------------------------- the contract
def _engine(spec):
    """(engine entry, design, canvas) of the spec, or ValueError for a style that is not a single-eye style of this family."""
    style, n = spec.get("style"), spec.get("eyes", 1)
    e = CT.engine_for(style, n)
    if e is None or e.get("module") != "singles":
        raise ValueError(f"{style!r} with {n!r} eyes is not a style of the singles family")
    fmt = spec.get("canvas") or spec.get("format")
    return e, e["design"], (fmt if fmt in e["canvases"] else e["canvases"][0])


def _pv(spec):
    """The plates version a spec asks for (the plan's pv; absent: the current one)."""
    pv = spec.get("pv")
    return pv if isinstance(pv, int) and not isinstance(pv, bool) and pv >= 0 else CT.PLATES_VERSION


def _opts3(spec):
    return spec.get("opts") if isinstance(spec.get("opts"), dict) else {}


def _profile_id(p):
    return p.get("eye_id") if isinstance(p, dict) else getattr(p, "eye_id", None)


def _eye_ids(spec, profiles):
    """[eye id] of the one eye of a single artwork, or [] when it is not known: spec["eye_ids"] (the order's own record), else the id of the sealed
    profile. An id that is not 16 hex digits is no id."""
    ids = spec.get("eye_ids")
    if not isinstance(ids, (list, tuple)):
        ids = [_profile_id(p) for p in (profiles or [])]
    ids = list(ids)[:1]
    return ids if len(ids) == 1 and SD.is_eye_id(ids[0]) else []


def _stats_of(profile):
    """colour_stats() ({class, L, C, h, mean_rgb}) of a sealed profile (an EyeProfile or the record dict a draft keeps), or None."""
    if profile is None:
        return None
    try:
        if isinstance(profile, dict):
            from ..eye import EyeProfile
            profile = EyeProfile(profile)
        return profile.stats
    except Exception:  # noqa: BLE001  a profile that cannot be read is no information (the render measures the eye itself)
        return None


def frozen_for(design, profile):
    """What the plan fixes before the render, from the eye's sealed profile: the liquid of a splash (the plate it picks is chosen by it, and a
    master measures the eye again at 4096 px: an eye on a hue threshold must not draw another liquid than the preview showed). {} when the design
    fixes nothing or the profile is not known (the render then measures the eye itself)."""
    if design != "splash":
        return {}
    st = _stats_of(profile)
    if st is None:
        return {}
    from . import splash as m
    return {"liquid": m.liquid_from_stats(st)}


def plates_for(design, seed, wall, pv, frozen):
    """[plate id] the picture of a design will draw from, no pixels (the same pick functions the render calls, so the plan and the picture cannot
    disagree): [] for a design with no plate, None when it cannot be known before the render (a splash without a frozen liquid; Elements, which
    reads the warmth of the ring and is a laboratory style)."""
    if design in ("clean", "radiance", "gold"):
        return []
    if design == "powder":
        from . import powder as m
        return [m.pick_cloud(seed, m.WIND_SETS["wall" if wall else "square"], pv=pv).plate.id]
    if design == "splash":
        liquid = (frozen or {}).get("liquid")
        if not liquid:
            return None
        from . import splash as m
        return [m.crown_pick(seed, liquid, pv)[1].plate.id]
    return None


def plates_used(log):
    """[plate id] a render drew from, read from the design's own facts."""
    out = []
    for k, fields in (("powder", ("plate",)), ("splash", ("plate",)), ("elements", ("flame_plate", "water_plate"))):
        v = log.get(k) if isinstance(log, dict) else None
        if isinstance(v, dict):
            out += [v[f] for f in fields if isinstance(v.get(f), str)]
    return out


def resolve(spec, profiles=None):
    """The plan of a style that needs no pixels (at most a few milliseconds): the design, the canvas, where the iris sits at 1024 px, the seed key
    and, when the eye is known (spec["eye_ids"], else the id of its sealed profile), the seed and the plate or plates the picture will draw from;
    what the plan freezes (the liquid of a splash, from the profile) is in frozen. Names, date and canvas size are not part of the seed, so the same
    answer holds for the preview, the draft and the master of an eye. profiles: the sealed profiles of the eyes (an EyeProfile, its record dict or
    None); plates is None where it cannot be known before the render (see plates_for)."""
    e, design, fmt = _engine(spec)
    has_text = bool(TX.lockup(spec.get("names")) or TX.clean(spec.get("date")))
    fr = K.frame_for(design, fmt, 1024, has_text)
    pv = _pv(spec)
    key = seed_key(spec["style"], design, e.get("clean"), _opts3(spec), pv)
    ids = _eye_ids(spec, profiles)
    prof = (profiles or [None])[0] if isinstance(profiles, (list, tuple)) else None
    frozen = frozen_for(design, prof)
    seed = SD.seed_for_key(ids, key) if ids else None
    plates = plates_for(design, seed, fr.wall, pv, frozen) if seed is not None else None
    return {"family": "singles", "style": spec["style"], "design_used": design, "fallback": None, "layout": "single", "canvas": fmt,
            "clean": bool(e.get("clean")), "size_ratio": [fr.W, fr.H], "iris_at_1024": {"cx": round(fr.cx, 3), "cy": round(fr.cy, 3), "R": round(fr.R, 3)},
            "seed_key": key, "seed_from": "eye_id", "eye_ids": ids, "seed": None if seed is None else str(seed), "frozen": frozen, "plates": plates,
            "steps": ["art"]}


def preview(eyes, spec, size=1024, check=False):
    """One style on one eye. eyes: a list of one Iris (or the bytes of a restored square). Returns a styles.Preview whose img is the CLEAN render:
    the dispatcher's watermark=True (or styles.watermarked) makes the free preview. check=True adds the selfcheck report (T1, T6, T7, T12 and T4
    where the design has a range) to .selfcheck. The seed is made from the eye's id and the seed key of the spec (style, options, pv). What the plan
    freezes is spec["frozen"] (the master: the stored plan's), or, when the spec carries the eyes' sealed profiles (spec["profiles"], the
    preview), what frozen_for makes of them: the same liquid in both. Preview.log["plates"] lists the plates the picture drew from."""
    from .. import Preview
    if not isinstance(eyes, (list, tuple)) or len(eyes) != 1:
        raise ValueError("the singles family draws exactly one eye")
    e, design, fmt = _engine(spec)
    names, date = TX.lockup(spec.get("names")), TX.clean(spec.get("date"))
    key = seed_key(spec["style"], design, e.get("clean"), _opts3(spec), _pv(spec))
    frozen = spec.get("frozen")
    if not isinstance(frozen, dict):
        profs = spec.get("profiles")
        frozen = frozen_for(design, profs[0] if isinstance(profs, (list, tuple)) and profs else None)
    r = render(design, eyes[0], fmt, size, names, date, opts=spec.get("engine_opts"), key=key, frozen=frozen)
    d = r.d
    log = r.ctx.log
    log["plates"] = plates_used(log)
    pv = Preview(img=r.img, discs=[(d.cx, d.cy, d.R)], graded=[d.iris.graded(d.Sd)], design=design, fmt=fmt, size=int(size), seed=r.info["seed"], cls=r.info["class"],
                 log=log, times=r.times, text_log=r.log, ctx=r.ctx, frame=r.frame)
    if check:
        import numpy as np
        from .. import selfcheck as SC
        pv.selfcheck = SC.run(np.asarray(r.img), [d], text_log=r.log, customer=[names, date], ids=[spec["style"], design, "single"],
                              black_range=T4_RANGES.get(design))
    return pv


def tiles(eyes, styles, spec, size=480):
    """{style id: Preview} of several styles of this family on one eye: the Iris is shared, so its ring, class and statistics are measured once
    (a grade is per design, as its disc differs). What a plan froze belongs to one style, so a tile takes the frozen choices of its own style from
    the sealed profiles of the spec (spec["profiles"]) and never the spec's own frozen. An exception of one tile is not caught here: the caller
    that serves a batch decides."""
    return {s: preview(eyes, dict(spec, style=s, frozen=None), size) for s in styles}
