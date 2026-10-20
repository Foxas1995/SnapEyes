# -*- coding: utf-8 -*-
"""styles.ensemble: the pairs and families of WHOLE irises. Two to eight restored irises that never touch or overlap (every iris keeps 100 percent of itself:
no seam, no weave, no front iris, nothing hidden), each in a light of its own, on one dark ground. The family of the owner's chosen pair and family looks of
2026-10-20 (the laboratory round proto_pf, branch v3-proto-pf: he called Clean Duo, Radiance Duo, Family Orbit, Radiance Family and Light Circle "really
quite good"; Endless Duo did not please him and the gold looks stay shelved):

  clean_duo        Clean Duo         two irises on pure black wrapped by one thin infinity thread (gold; "thread": "tint" turns each side toward its eye's colour)
  radiance_duo     Radiance Duo      two ray bursts of the eyes' own colours that cross in the gap (singles/radiance.py), a star where they meet
  orbit            Family Orbit      the first eye of the canvas order larger in the middle in the gold corona, the others on a ring round it (the customer chooses
                                     the hub: the order of the eyes, or rotate)
  light_circle     Light Circle      the irises evenly on a circle round one small light, a white star in a thin aureole
  radiance_family  Radiance Family   every eye sends its own short rays, one shared key light, a soft territory per eye

Every picture follows the artwork charter by construction (base.py): the matter is drawn into the float canvas, the irises are pasted LAST, byte for byte;
nothing is drawn over an iris or a pupil (checks.py measures T1, T2, T6 on every render it is asked to and on every master).

The contract of api/_lib/styles/__init__.py, for this family:
    resolve(spec, profiles, eyes=None)   the plan: the design, the layout, the canvas, the geometry at 1024 px, the seed key and (with the eye ids) the seed. The two
                                         Radiance looks decide one thing from the PIXELS (which eye takes the next palette variant when two drawn colours are
                                         closer than 10 dE00): with the eyes the plan makes that choice and freezes it (frozen {"pal": [...]}, decided True), the
                                         preview and the master obey it; without them decided is False for those two (the render decides, as the preview did)
    preview(eyes, spec, size, check=False)    one style on its eyes, a Preview (clean: styles.watermarked() makes the free preview)
    tiles(eyes, styles, spec, size)           several styles of one eye count on one eye preparation
and render(design, eyes, ...), the entry of the golden suite and the laboratory.

The seed (seeds.py) is made from the eyes' ids in canvas order and the plan's seed key: the style, the design, the ground, no clean flag, the layout id, the
buyer's options in their canonical form (effective_opts: swap for a pair, rotate for a group, modulo the number of eyes) and the plates version (no plate is
read: pv only keeps the key's shape). Not in it: the names, the date, the canvas, the size, the pixels. Names and date are the customer's own words, one line
drawn by text.draw_names under the irises (the artwork moves up 0.03 S and shrinks to 0.94 to make room, the singles' rule).
"""
from __future__ import annotations

from ... import catalogue as CT
from .. import core as SCORE
from .. import seeds as SD
from .. import text as TX
from . import base as B

DESIGNS = ("clean_duo", "radiance_duo", "orbit", "light_circle", "radiance_family")
PAIR_DESIGNS = ("clean_duo", "radiance_duo")
GROUP_DESIGNS = ("orbit", "light_circle", "radiance_family")
SIZES = (64, 4096)
NAMES_MAX = 8
_LOOKS = {}


def looks():
    """{design: the look's entry}: n (min, max eyes), fmt (the default canvas for n eyes), canvases, plan, fx, bg, group, decide (the Radiance looks)."""
    if not _LOOKS:
        from . import clean_duo, light_circle, orbit, radiance_duo, radiance_family
        _LOOKS.update({"clean_duo": clean_duo.LOOK, "radiance_duo": radiance_duo.LOOK, "orbit": orbit.LOOK, "light_circle": light_circle.LOOK,
                       "radiance_family": radiance_family.LOOK})
    return _LOOKS


# ----------------------------------------------------------------------------- what a spec names
def _setup(spec):
    """(engine entry, design, layout, canvas) of the spec, or ValueError for a style that is not a style of this family. The canvas is the one the spec names when
    the registry lists it and the look has a scene on it, else the look's own default for the eye count (the paid file's canvas)."""
    style, n = spec.get("style"), spec.get("eyes", 2)
    e = CT.engine_for(style, n)
    if e is None or e.get("module") != "ensemble":
        raise ValueError(f"{style!r} with {n!r} eyes is not a style of the ensemble family")
    design = e["design"]
    lk = looks()[design]
    layout = spec.get("layout") or CT.default_layout(style, n)
    if layout not in CT.layouts_for(style, n):
        raise ValueError(f"{style!r} with {n} eyes has no layout {layout!r}")
    fmt = spec.get("canvas") or spec.get("format")
    if fmt not in e["canvases"] or fmt not in lk["canvases"]:
        fmt = lk["fmt"](n)
    return e, design, layout, fmt


def default_canvas(design, n):
    """The canvas a design of n eyes is drawn on when the spec names none (the paid file is this canvas at 4096 px on its long side)."""
    return looks()[design]["fmt"](n)


def _opts3(spec):
    return spec.get("opts") if isinstance(spec.get("opts"), dict) else {}


def _pv(spec):
    pv = spec.get("pv")
    return pv if isinstance(pv, int) and not isinstance(pv, bool) and pv >= 0 else CT.PLATES_VERSION


def effective_opts(design, opts, n):
    """The buyer's options in the form that DECIDES the picture, which is the form the seed key holds (one choice, one seed, however a caller spells it): swap is
    True only for a pair that is swapped (the two irises change places); rotate is the shift of the places of a group, modulo the number of eyes, 0 being the
    default (Family Orbit: which eye is the hub); look means nothing here. {} and {swap: False}, {rotate: 0} and {rotate: n} are one seed each."""
    o = opts if isinstance(opts, dict) else {}
    rot = o.get("rotate")
    swap = True if (design in PAIR_DESIGNS and o.get("swap") is True) else None
    rotate = ((rot % n) or None) if (design in GROUP_DESIGNS and isinstance(rot, int) and not isinstance(rot, bool) and 0 <= rot <= 7 and n >= 3) else None
    return {"swap": swap, "rotate": rotate, "look": None}


def canvas_order(items, design, eff):
    """The eyes (or their ids, or their profiles) in the order of the canvas: a swapped pair reversed, a group shifted by rotate (the eye at `rotate` first: the
    hub of Family Orbit)."""
    items = list(items)
    if design in PAIR_DESIGNS and eff.get("swap"):
        return items[::-1]
    r = eff.get("rotate") or 0
    return items[r:] + items[:r] if r else items


def seed_key(style, design, layout, opts=None, pv=None, n=2):
    """The plan's seed key of an ensemble artwork (seeds.py names its fields). The options are in their canonical form (effective_opts)."""
    return {"style": style, "design_used": design, "bg": "dark", "clean": False, "layout": layout, "opts": effective_opts(design, opts, n),
            "pv": CT.PLATES_VERSION if pv is None else int(pv)}


def _style_of(design, n):
    """The registry id of the style a design draws with n eyes (render() is called with the design alone)."""
    for sid in CT.ids():
        eng = CT.engine_for(sid, n) if CT.ENGINE[sid]["engine"] else None
        if eng is not None and eng.get("module") == "ensemble" and eng.get("design") == design:
            return sid
    raise KeyError(design)


def default_key(design, n, layout=None, pv=None):
    """The seed key of a render that was given none (the golden suite, the laboratory): the design's own style, its default layout, no options."""
    style = _style_of(design, n)
    return seed_key(style, design, layout or CT.default_layout(style, n), None, pv, n)


def _eyes(eyes):
    out = []
    for e in eyes:
        if isinstance(e, SCORE.Iris):
            out.append(e)
        elif isinstance(e, (bytes, bytearray)):
            out.append(SCORE.Iris(bytes(e)))
        else:
            raise TypeError("an eye is an Iris or the bytes of an image")
    return out


def _words(spec):
    """(names line, date line) as the singles draw them: the names joined into one lockup line (a list from the page, or the master's own lockup line), the
    date cleaned."""
    return TX.lockup(spec.get("names")), TX.clean(spec.get("date"))


# ----------------------------------------------------------------------------- the laboratory's and the golden suite's entry
def render(design, eyes, fmt=None, size=1024, names="", date="", opts=None, key=None, frozen=None):
    """One ensemble artwork. eyes: Iris objects or the bytes of restored squares, IN CANVAS ORDER (the hub of Family Orbit first). fmt: a canvas the look has a scene on
    (None: its default for the eye count). size: the long side in px (1024 a preview, 4096 a master). names: the customer's names (a list or one lockup line) and
    date. opts: the look's options (the laboratory's: "thread": "tint" for Clean Duo, the moat and the cap of the Radiance looks). key: the plan's seed key
    (default: default_key). frozen: what the plan fixed (the palette variants of a Radiance look). Returns base.Result."""
    if design not in DESIGNS:
        raise KeyError(design)
    lk = looks()[design]
    irises = _eyes(eyes)
    n = len(irises)
    if not lk["n"][0] <= n <= lk["n"][1]:
        raise ValueError(f"{design} takes {lk['n'][0]} to {lk['n'][1]} eyes, not {n}")
    fmt = fmt or lk["fmt"](n)
    if fmt not in lk["canvases"]:
        raise ValueError(f"{design} has no scene on the {fmt!r} canvas (its canvases are {', '.join(lk['canvases'])})")
    if not SIZES[0] <= int(size) <= SIZES[1]:
        raise ValueError(f"a canvas of {size} px (from {SIZES[0]} to {SIZES[1]})")
    key = key if key is not None else default_key(design, n)
    line = TX.lockup(names) if not isinstance(names, str) else TX.lockup(TX.split_names(names))
    return B.render(lk, design, irises, fmt, int(size), line, TX.clean(date), opts=opts, key=SD.clean_key(key), frozen=frozen)


# ----------------------------------------------------------------------------- the contract
def _profile_id(p):
    return p.get("eye_id") if isinstance(p, dict) else getattr(p, "eye_id", None)


def _eye_ids(spec, profiles, n):
    ids = spec.get("eye_ids")
    if not isinstance(ids, (list, tuple)):
        ids = [_profile_id(p) for p in (profiles or [])]
    ids = list(ids)[:n]
    return ids if len(ids) == n and all(SD.is_eye_id(i) for i in ids) else []


def resolve(spec, profiles=None, eyes=None):
    """The plan of a style. Without the eyes: the design, the layout, the canvas, the geometry of the discs at 1024 px (as shares of the short side S), the seed key
    and, when the eye ids are known (spec["eye_ids"], else the ids of the sealed profiles), the seed; decided is True for the looks that decide nothing from the
    pixels and False for the two Radiance looks. With the eyes (Iris objects or the bytes of restored squares, in the order of the spec) a Radiance look's palette
    choice is made on them and frozen ({"pal": [...]}, decided True): the preview and the master then draw that choice whatever another copy of the eyes would
    decide. profiles: the sealed profiles of the eyes (an EyeProfile, its record dict or None)."""
    e, design, layout, fmt = _setup(spec)
    n = spec.get("eyes", 2)
    lk = looks()[design]
    eff = effective_opts(design, _opts3(spec), n)
    key = seed_key(spec["style"], design, layout, _opts3(spec), _pv(spec), n)
    ids = _eye_ids(spec, profiles, n)
    seed = SD.seed_for_key(canvas_order(ids, design, eff), key) if ids else None
    frozen, decided = {}, True
    if "decide" in lk:
        if eyes is not None:
            irs = canvas_order(_eyes(eyes), design, eff)
            if len(irs) != n:
                raise ValueError(f"{spec.get('style')!r} draws exactly {n} eyes")
            frozen = lk["decide"](irs)
        else:
            decided = False
    names, date = _words(spec)
    plan = lk["plan"](n, fmt, {})
    if names or date:
        plan = B.with_text(plan)
    S = float(plan.S)
    slots = [{"cx": round(cx / S, 5), "cy": round(cy / S, 5), "R": round(R / S, 5)} for cx, cy, R in plan.discs]
    return {"family": "ensemble", "style": spec["style"], "design_used": design, "fallback": None, "layout": layout, "canvas": fmt, "clean": False,
            "size_ratio": [plan.W, plan.H], "geometry": {"slots": slots}, "seed_key": key, "seed_from": "eye_id", "eye_ids": ids,
            "seed": None if seed is None else str(seed), "frozen": frozen, "decided": decided, "plates": [], "steps": ["art"]}


def preview(eyes, spec, size=1024, check=False):
    """One style on its eyes. eyes: a list of Iris (or the bytes of restored squares), in the order of the spec (a swapped pair or a rotated group is put in canvas
    order here). Returns a styles.Preview whose img is the CLEAN render (the dispatcher's watermark=True, or styles.watermarked, makes the free preview); check=True
    adds the report of checks.selfcheck. spec["frozen"], the plan's record of the palette choice of a Radiance look (the master: the stored plan's), is obeyed;
    without it the render decides from these eyes (Preview.log["frozen"] says what was drawn). The words, the canvas and the size are not part of the seed."""
    from .. import Preview
    from . import checks as CK
    e, design, layout, fmt = _setup(spec)
    n = spec.get("eyes", 2)
    if not isinstance(eyes, (list, tuple)) or len(eyes) != n:
        raise ValueError(f"{spec.get('style')!r} draws exactly {n} eyes")
    eff = effective_opts(design, _opts3(spec), n)
    irs = canvas_order(_eyes(eyes), design, eff)
    key = seed_key(spec["style"], design, layout, _opts3(spec), _pv(spec), n)
    fz = spec.get("frozen") if isinstance(spec.get("frozen"), dict) and spec.get("frozen") else None
    names, date = _words(spec)
    eo = spec.get("engine_opts") if isinstance(spec.get("engine_opts"), dict) else None
    r = B.render(looks()[design], design, irs, fmt, int(size), names, date, opts=eo, key=key, frozen=fz)
    graded = [d.iris.graded(d.Sd) for d in r.discs]
    rep = CK.selfcheck(r, [spec["style"], design, layout]) if check else None
    log = dict(r.ctx.log)
    log.update(design_used=design, fallback=None, plates=[], frozen=r.frozen, layout=layout)
    return Preview(img=r.img, discs=[(d.cx, d.cy, d.R) for d in r.discs], graded=graded, design=design, fmt=fmt, size=int(size), seed=r.seed,
                   cls=[ir.cls for ir in irs], log=log, times=r.times, text_log=r.text_log, selfcheck=rep, ctx=None, frame=r.plan)


def tiles(eyes, styles, spec, size=480):
    """{style id: Preview} of several styles of this family on one eye preparation: the Iris objects are shared, so each eye's ring, class and grades are measured
    once. A tile takes the default layout and canvas of its own style and decides its own choices from these eyes. An exception of one tile is not caught here:
    the caller that serves a batch decides."""
    return {s: preview(eyes, dict(spec, style=s, layout=None, canvas=None, frozen=None), size) for s in styles}
