# -*- coding: utf-8 -*-
"""styles.universe: the UNIVERSE family of the v3 engine. The customer's own iris, enlarged and darkened to a fill, as the sky of the picture, with its own
matter (fibre flakes, grains, iris chips, stars) around the real iris; the iris itself is pasted last, byte for byte, and is never touched. Looks:

  echo       Universe (Echo)       the default and the only look of a pair or a group: the enlarged iris as a dark sky, flakes of the iris and dust round it
  vortex     Universe (Vortex)     one eye: a photographed spiral (P-DN-SPIRAL plate, a crisp circular void hidden behind the iris) and an accretion ring
                                   made of the eye's own limbus; a chip inside the Universe tile
  deepfield  Deep Field            one eye: luminous dust (P-UV-DUST plate) in the eye's own hue (held: the laboratory only)
  starfield  Starfield             one eye: a photographed Milky Way (P-UV-MILKY plate) in the eye's hue (held: the laboratory only)
and the pair (Universe Duo over the Collision Infinity geometry: an S weave of two real irises) and the group of three to six (over the Family Colours
layouts: crumble contacts, one iris in front), both held: the laboratory only. The registry says which look of which style is at which stage.

This is work package WP8, step A: the prototype's family ported verbatim (layout, common, engine, comp, fill, flakes, grains, matter, plates, looks and
plate_looks here; the restoration gate and the pupil are api/_lib/styles/gate.py and pupil.py; scripts/styles_tests/port_universe.py lists every
edit) and replayed against the prototype's own pictures byte for byte (scripts/styles_tests/test_goldens_universe.py). The seed is still the prototype's
(the bytes of the irises, the look and the layout: step B, WP8B, makes it from the eye ids and the plan's seed key like the singles got in WP5B), so
resolve() cannot name the plate a plate look will draw before the render yet: plates is None and seed_from says iris_bytes.

A picture is drawn in horizontal bands with a halo (engine.render_bands: every layer is a pure function of the canvas position, so a 4096 px master is
the 1024 px picture with more pixels and never holds more than a few 4096 x 512 float arrays), the soft content (fill, plates, haze) on a coarse grid
(1 up to 1536 px, 2 up to 2304, 3 above), the sprites at full resolution. The fill is cut from a graded copy of the eye of FILL_SD = 1024 px for one or two
eyes and 768 px for groups (common.py: the soft-by-design fill: a 2048 px copy costs about four times the set-up and the fill does not need it).

The contract of api/_lib/styles/__init__.py, for this family:
    resolve(spec, profiles)                   the plan of a style that needs no pixels: look, layout, canvas, the geometry of the layout at 1024 px (a pair's
                                              distance from the pupils of the sealed profiles, and the fallback to the Kiss distance), the seed key
    preview(eyes, spec, size, check=False)    one style on its eyes (one, two, or three to six), a Preview (clean: styles.watermarked() makes the free preview)
    tiles(eyes, styles, spec, size)           several styles of this family on one eye preparation (the Src of an eye is cached on the Iris)
and the prototype's own entry, render(look, irises, size, aspect, names, date, opts), which the golden suite calls.

An eye is a styles.core.Iris (or the bytes of a restored square). Nothing here reads a path, a key or the network; the plates come from styles.plates (the
bundle at 1K, private storage at 4K: a plate that is not there stops the render with PlateUnavailable, the master plan holds the order and the family never
draws a picture without it), the chip atlas from styles.atlas. Names and date are the customer's own words (text.py cleans them, engine.draw_names draws).
"""
from __future__ import annotations

from ... import catalogue as CT
from .. import seeds as SD
from .. import text as TX
from . import layout as LO

LOOKS = ("echo", "deepfield", "vortex", "starfield")          # the prototype's names; the registry's looks table lists the same
SOLO_LOOKS = ("deepfield", "vortex", "starfield")             # one eye only (Echo covers pairs and groups)
SIZES = (64, 4096)                                            # the long side a render may ask for
ENGINE_OPTS = ("zone_c", "seam_band", "edge_mode", "crumble_holes", "edge_scale", "edge_profile", "seam_noise", "seam_dust", "trio_base", "d_group",
               "d_override", "kiss", "k_s", "r_scale", "fill_only", "pet", "ellipse")        # the laboratory's switches (the owner's sign-offs): never a customer's
GROUP_LAYOUTS = {3: "trio", 4: "zigzag", 5: "brick5", 6: "brick6"}
JOIN_PAIR = " " + chr(0x221E) + " "           # how engine.draw_names joins the two names of a pair (the infinity sign) ...
JOIN_GROUP = " " + chr(0xB7) + " "          # ... and the names of a group (the middle dot)


def _core():
    from .. import core as C
    return C


def _iris(eye, name="eye"):
    """An Iris from an Iris or from the bytes of a restored iris square (a function reads what the request carried: a path is never opened)."""
    C = _core()
    if isinstance(eye, C.Iris):
        return eye
    if isinstance(eye, (bytes, bytearray)):
        return C.Iris(bytes(eye), name)
    raise TypeError("an eye is an Iris or the bytes of an image")


def render(look, irises, size=1024, aspect=None, names=None, date=None, opts=None, want_scene=False, times=None):
    """One artwork (the prototype's entry). look: echo, deepfield, vortex or starfield (the last three draw one eye). irises: a list of one to six Iris (or
    the bytes of restored squares). size: the long side in px (1024 a preview, 4096 a master). aspect: the canvas id of the layout (None: its default).
    names: the customer's names (a list of at most one per eye, or the old "Anna;Max" string) and date, drawn small under the irises when given.
    opts: the laboratory's switches (ENGINE_OPTS) and the buyer's rotate (the trio's roles) and swap (the seed). Returns the PIL image, or (image, scene)
    with want_scene (the scene holds the eyes, the layout, the seed and the facts of the render in scene.info)."""
    if look not in LOOKS:
        raise ValueError(f"unknown look {look!r}; have {LOOKS}")
    if not isinstance(irises, (list, tuple)) or not 1 <= len(irises) <= 6:
        raise ValueError("the universe family draws one to six eyes")
    if not SIZES[0] <= int(size) <= SIZES[1]:
        raise ValueError(f"a canvas of {size} px (from {SIZES[0]} to {SIZES[1]})")
    if look != "echo" and len(irises) != 1:
        raise ValueError("Deep Field, Vortex and Starfield are single-eye looks (Echo covers pairs and groups)")
    from . import looks as LK                     # looks first: it imports plate_looks at its end and plate_looks imports looks
    from . import engine as EN
    o = dict(opts or {})
    if date:
        o["date"] = date
    return EN.render(LK.LOOKS[look](), [_iris(e, f"eye{i + 1}") for i, e in enumerate(irises)], int(size), aspect, TX.split_names(names), o,
                     times=times, want_scene=want_scene)


# ----------------------------------------------------------------------------- the spec
def engine_layout(layout, n):
    """The prototype's layout name of a registry layout id for n eyes (a group: trio, zigzag, brick5, brick6, ring5, ring6), None for one or two eyes."""
    if n < 3:
        return None
    if layout in ("brick", "ring"):
        return f"{layout}{n}"
    return GROUP_LAYOUTS[n]


def _aspect_of(e, spec, n, lname):
    fmt = spec.get("canvas") or spec.get("format")
    if fmt in e["canvases"]:
        return fmt
    if n >= 3:
        return LO.GROUP_TABLE[lname][0]
    return e["canvases"][0]


def _engine(spec):
    """(engine entry, look, canvas id, the prototype's layout name or None) of the spec, or ValueError for a style that is not of this family or a look
    the style does not have for that number of eyes."""
    style, n = spec.get("style"), spec.get("eyes", 1)
    e = CT.engine_for(style, n)
    if e is None or e.get("module") != "universe":
        raise ValueError(f"{style!r} with {n!r} eyes is not a style of the universe family")
    o = spec.get("opts") if isinstance(spec.get("opts"), dict) else {}
    look = o.get("look") or e["design"]
    allowed = tuple(e.get("looks") or (e["design"],))
    if look not in LOOKS or look not in allowed or (look != "echo" and n != 1):
        raise ValueError(f"{look!r} is not a look of {style!r} with {n!r} eyes (looks: {', '.join(allowed)})")
    lname = engine_layout(spec.get("layout"), n)
    return e, look, _aspect_of(e, spec, n, lname), lname


def _names_of(value, n):
    """The names of a spec as the list the drawer reads, from any of the forms they arrive in: a list of texts (the new wire form, one per eye), the old string "Anna;Max",
    or the lockup line the master plan passes ("Anna, a middle dot, Max": api/_lib/styles/steps.py master_words). For one eye the names are ONE line (the lockup of what was given: the
    singles draw it whole), for a pair the drawer joins the first two with the infinity sign and for a group all of them with the middle dot."""
    if isinstance(value, str) and TX.LOCKUP_JOIN in value:
        value = value.split(TX.LOCKUP_JOIN)
    names = TX.split_names(value)
    return [TX.lockup(names)] if (n == 1 and names) else names


def _opts3(spec):
    o = spec.get("opts") if isinstance(spec.get("opts"), dict) else {}
    return {k: o.get(k) for k in SD.OPT_FIELDS}


def _pv(spec):
    pv = spec.get("pv")
    return pv if isinstance(pv, int) and not isinstance(pv, bool) and pv >= 0 else CT.PLATES_VERSION


def seed_key(style, look, layout="single", opts=None, pv=None):
    """The plan's seed key of a universe artwork (seeds.py names its fields): the registry id, the look it draws with, the ground (the universe fill is the
    picture's own, not the "universe" background of the collision family), no clean flag, the registry's layout id, the buyer's three options (swap, rotate,
    look) and the plates version (None: the current one)."""
    o = opts if isinstance(opts, dict) else {}
    return {"style": style, "design_used": look, "bg": "dark", "clean": False, "layout": layout, "opts": {k: o.get(k) for k in SD.OPT_FIELDS},
            "pv": CT.PLATES_VERSION if pv is None else int(pv)}


def _pupil_of(profile):
    """The pupil dict (pupil.analyse's shape) of a sealed profile (an EyeProfile or its record dict), or None."""
    if profile is None:
        return None
    try:
        if isinstance(profile, dict):
            from ..eye import EyeProfile
            profile = EyeProfile(profile)
        return profile.pupil
    except Exception:  # noqa: BLE001  a profile that cannot be read is no information (the render measures the pupils itself)
        return None


def _axis(aspect):
    """The unit vector from eye A to eye B of a pair on this canvas (engine.Scene: 0 degrees on the wide canvases, 35 on the square, 60 on the tall one)."""
    import math
    ang = {"1:1": math.radians(35.0), "4:5": math.radians(60.0)}.get(aspect, 0.0)
    return (math.cos(ang), -math.sin(ang))


def _layout_at_1024(n, look, aspect, lname, has_text, spec, profiles, o):
    """(Layout, how its geometry was known) at 1024 px: pure arithmetic of layout.py, no pixels. A pair's distance needs the reach of both pupils toward
    the partner: from the sealed profiles when both have one, else the layout's default reach (and the plan says so)."""
    if n == 1:
        return LO.solo(look, 1024, aspect, has_text, o.get("r_scale", 1.0)), "layout"
    if n == 2:
        pups = [_pupil_of(p) for p in (profiles or [])][:2]
        if len(pups) == 2 and None not in pups:
            from .. import pupil as PUP
            ua = _axis(aspect)
            ra, rb = PUP.reach(pups[0], ua), PUP.reach(pups[1], (-ua[0], -ua[1]))
            return LO.duo(1024, reach_a=ra, reach_b=rb, aspect=aspect, names=has_text, d_override=o.get("d_override"), kiss=o.get("kiss")), "profile"
        return LO.duo(1024, aspect=aspect, names=has_text, d_override=o.get("d_override"), kiss=o.get("kiss")), "default"
    opts = _opts3(spec)
    return LO.group(n, 1024, names=has_text, layout=lname, d=o.get("d_group", LO.GROUP_D), aspect=aspect, rotate=int(opts["rotate"] or 0),
                    trio_base=o.get("trio_base", "crumble")), "layout"


def resolve(spec, profiles=None):
    """The plan of a style that needs no pixels (a few milliseconds): the look, the registry's layout, the canvas, the geometry of the layout at 1024 px
    in units of the short side S (the centre and radius of every iris, the contacts with their kind and distance in R, so a 4096 px master is the same
    picture), the fallback of a pair whose pupils need more than the weave allows (the Kiss distance), and the key a seed is made of. profiles: the sealed
    profiles of the eyes (an EyeProfile, its record dict or None); a pair's distance is read from their pupils (geometry_from says "profile"), else from
    the layout's default reach ("default"). What the render measures itself (a pupil on a 1024 px graded frame, not on the 256 px grade the profile was
    made on) can move a pair's distance in the third decimal: the plan names the decisions, the render makes the pixels. plates is None: the plate a plate
    look draws depends on the seed, and the seed is still the prototype's (the bytes of the irises), so it is unknown before the render (WP8B)."""
    e, look, aspect, lname = _engine(spec)
    n = spec.get("eyes", 1)
    names = _names_of(spec.get("names"), n)
    has_text = bool(names or TX.clean(spec.get("date")))
    o = spec.get("engine_opts") if isinstance(spec.get("engine_opts"), dict) else {}
    lay, how = _layout_at_1024(n, look, aspect, lname, has_text, spec, profiles, o)
    S = float(lay.S)
    slots = [{"cx": round(s.cx / S, 5), "cy": round(s.cy / S, 5), "R": round(s.R / S, 5)} for s in lay.slots]
    contacts = [{"a": c.a, "b": c.b, "kind": c.kind, "d_R": round(c.d / lay.slots[c.a].R, 4)} for c in lay.contacts]
    fallback = "kiss" if lay.info.get("overlap_fallback") else None
    layout_id = spec.get("layout") or CT.default_layout(spec["style"], n)
    key = seed_key(spec["style"], look, layout_id, _opts3(spec), _pv(spec))
    return {"family": "universe", "style": spec["style"], "design_used": look, "fallback": fallback, "layout": layout_id, "canvas": aspect,
            "clean": False, "size_ratio": [lay.W, lay.H], "geometry": {"key": lay.key, "layout": lay.layout, "slots": slots, "contacts": contacts, "from": how,
                                                                       "d_units": lay.info.get("d_units"), "d_needed": lay.info.get("d_needed")},
            "seed_key": key, "seed_from": "iris_bytes", "eye_ids": [], "seed": None, "frozen": {}, "plates": None, "steps": ["art"]}


def _text_expected(names, date, n):
    """The strings the drawer draws for these words (engine.draw_names: upper case, joined by the family's rule, the letters the font lacks left out): what
    the T7 check lets a drawn line be."""
    def keep(s):
        return "".join(ch for ch in s if not TX.unsupported(ch))
    up = [s.upper() for s in names]
    if n == 1:
        line = up[0] if up else ""
    elif n == 2:
        line = JOIN_PAIR.join(up[:2]) if len(up) >= 2 else (up[0] if up else "")
    else:
        line = JOIN_GROUP.join(up)
    return [keep(line), keep(TX.clean(date).upper())]


def plates_used(info):
    """[plate id] a render drew from, read from its facts (the plate of the look, and the Echo wall's accent plate)."""
    out = []
    for k in ("plate", "accent_plate"):
        v = info.get(k) if isinstance(info, dict) else None
        if isinstance(v, dict) and isinstance(v.get("id"), str):
            out.append(v["id"])
    return out


def _log_of(scene, look):
    """The facts of a render that name something (small JSON-safe numbers and words): the look, the layout, the plates, the halo, the contacts."""
    info = scene.info
    log = {"look": look, "layout": scene.layout.key, "aspect": scene.layout.aspect, "plates": plates_used(info), "halo_rows": info.get("halo_rows"),
           "band_rows": info.get("band_rows"), "coarse": scene.f}
    for k in ("plate", "accent_plate", "notches", "contacts", "plate_fallback"):
        if k in info:
            log[k] = info[k]
    return log


def preview(eyes, spec, size=1024, check=False):
    """One style on its eyes: one (Echo, Vortex, Deep Field, Starfield), two (the pair: Echo) or three to six (the group: Echo). Returns a styles.Preview
    whose img is the CLEAN render (the dispatcher's watermark=True, or styles.watermarked, makes the free preview). check=True adds the selfcheck report
    (T1, T6, T7 and T12; for a pair or a group T1 reads the compositor's own masks of the pure iris pixels) to .selfcheck. spec["opts"]: the buyer's look
    (echo, vortex, ...), rotate (the trio's roles) and swap (a pair's two irises exchange places); spec["engine_opts"]: the laboratory's switches."""
    from .. import Preview
    import numpy as np
    e, look, aspect, lname = _engine(spec)
    n = spec.get("eyes", 1)
    if not isinstance(eyes, (list, tuple)) or len(eyes) != n:
        raise ValueError(f"the style draws {n} eye(s), {len(eyes) if isinstance(eyes, (list, tuple)) else 'no list of'} given")
    eo = dict(spec.get("engine_opts") or {})
    bad = sorted(set(eo) - set(ENGINE_OPTS))
    if bad:
        raise ValueError(f"unknown engine option(s) {', '.join(bad)} (the laboratory's switches: {', '.join(ENGINE_OPTS)})")
    opts3 = _opts3(spec)
    names = _names_of(spec.get("names"), n)
    date = TX.clean(spec.get("date"))
    irises = [_iris(x, f"eye{i + 1}") for i, x in enumerate(eyes)]
    if n == 2 and opts3["swap"]:
        irises = irises[::-1]
    o = dict(eo, swap=bool(opts3["swap"]), rotate=int(opts3["rotate"] or 0))
    if lname:
        o["layout"] = lname
    times = {}
    img, scene = render(look, irises, size, aspect, names, date, o, want_scene=True, times=times)
    discs = [e_.snap for e_ in scene.eyes]
    graded = [e_.iris.graded(e_.disc.Sd) for e_ in scene.eyes]
    text_log = [{"kind": k, "text": t} for k, t in scene.info.get("text", [])]
    cls = [e_.iris.cls for e_ in scene.eyes]
    pv = Preview(img=img, discs=[tuple(map(float, d)) for d in discs], graded=graded, design=look, fmt=aspect, size=int(size), seed=int(scene.seed),
                 cls=cls[0] if n == 1 else cls, log=_log_of(scene, look), times=times, text_log=text_log, ctx=scene, frame=scene.layout)
    if check:
        from .. import selfcheck as SC
        from . import comp as CO
        masks = None
        if n > 1 and scene.comp is not None:
            masks = CO.pure_masks(scene.comp, scene.W, scene.H)
        pv.selfcheck = SC.run(np.asarray(img), [e_.disc for e_ in scene.eyes], text_log=text_log, customer=_text_expected(names, date, n),
                              ids=[spec["style"], look, scene.layout.layout or "single"], masks=masks)
    return pv


def tiles(eyes, styles, spec, size=480):
    """{style id: Preview} of several styles of this family on the same eyes: an Iris caches its grades, its ring and the Src of the fill, so the work that
    does not depend on the style is done once. An exception of one tile is not caught here: the caller that serves a batch decides."""
    return {s: preview(eyes, dict(spec, style=s), size) for s in styles}
