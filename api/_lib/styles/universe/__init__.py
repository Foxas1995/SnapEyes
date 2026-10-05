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

This is work package WP8: the prototype's family ported verbatim (step A: layout, common, engine, comp, fill, flakes, grains, matter, plates, looks and
plate_looks here; the restoration gate and the pupil are api/_lib/styles/gate.py and pupil.py; scripts/styles_tests/port_universe.py lists every
edit) and replayed against the prototype's own pictures byte for byte (scripts/styles_tests/test_goldens_universe.py), then changed ONCE on purpose (step B,
WP8B, decision C9): the seed is made from the eyes' ids and the plan's seed key (api/_lib/styles/seeds.py), as the singles got in WP5B and the collision family in
WP7B, so the preview, the order's draft and the master of one eye seed alike and a typo in a name, the canvas or the size reshuffle nothing; every plate pick takes
the plates version of the plan (the append-only rule); resolve() names the seed and the plate a look will draw (the plan's plates_needed: the 4K plates a Vortex or an
Echo wall master fetches); the pair's fallback (the Kiss distance or the weave) is fixed by the plan and a master whose pupils contradict it is refused
(DesignChanged). opts seed_mode "legacy" draws the step A pictures byte for byte: that replay is the proof that nothing else moved.

A picture is drawn in horizontal bands with a halo (engine.render_bands: every layer is a pure function of the canvas position, so a 4096 px master is
the 1024 px picture with more pixels and never holds more than a few 4096 x 512 float arrays), the soft content (fill, plates, haze) on a coarse grid
(1 up to 1536 px, 2 up to 2304, 3 above), the sprites at full resolution. The fill is cut from a graded copy of the eye of FILL_SD = 1024 px for one or two
eyes and 768 px for groups (common.py: the soft-by-design fill: a 2048 px copy costs about four times the set-up and the fill does not need it).

The contract of api/_lib/styles/__init__.py, for this family:
    resolve(spec, profiles)                   the plan of a style that needs no pixels: look, layout, canvas, the geometry of the layout at 1024 px (a pair's
                                              distance from the pupils of the sealed profiles, and the fallback to the Kiss distance, which it freezes), the
                                              seed key and, when the eyes' ids are known, the seed and the plates the picture will draw from
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
from . import plates as UPL

LOOKS = ("echo", "deepfield", "vortex", "starfield")          # the prototype's names; the registry's looks table lists the same
SOLO_LOOKS = ("deepfield", "vortex", "starfield")             # one eye only (Echo covers pairs and groups)
SIZES = (64, 4096)                                            # the long side a render may ask for
ENGINE_OPTS = ("zone_c", "seam_band", "edge_mode", "crumble_holes", "edge_scale", "edge_profile", "seam_noise", "seam_dust", "trio_base", "d_group",
               "d_override", "kiss", "k_s", "r_scale", "fill_only", "pet", "ellipse", "seed_mode")        # the laboratory's switches (the owner's sign-offs): never a customer's
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


def style_of(n):
    """The registry id of the style of this family that draws n eyes (read from the registry: one eye is the solo style with its four looks, two the pair, three to six the
    group); KeyError when none does."""
    for sid in CT.ids():
        e = CT.engine_for(sid, n) if CT.ENGINE[sid]["engine"] else None
        if e is not None and e.get("module") == "universe":
            return sid
    raise KeyError(n)


def registry_layout(lname, n):
    """The registry's layout id of the prototype's layout name (trio, zigzag, brick5, brick6, ring5, ring6, or None for the default) for n eyes."""
    if n == 1:
        return "single"
    if n == 2:
        return "pair"
    if not lname:
        return CT.default_layout(style_of(n), n)
    for lid in ("brick", "ring"):
        if lname.startswith(lid):
            return lid
    return lname


def default_key(look, n, lname=None, opts=None, pv=None):
    """The seed key of a render that was given none (the golden suite, the laboratory, a direct caller): the style that draws n eyes, the look, the layout of the
    prototype's name, the buyer's swap and rotate if the options carry them, and the current plates version. It is the key a preview makes of the same artwork."""
    return seed_key(style_of(n), look, registry_layout(lname, n), opts, pv)


def _checked_key(key, look):
    """A seed key as the engine takes it: the look drawn, the ground and the clean flag filled in (a universe artwork is always the look's own, on its own fill),
    every other field present and valid. ValueError for anything else, before anything is drawn."""
    if not isinstance(key, dict):
        raise ValueError("a seed key is a dict")
    return SD.clean_key(dict(key, design_used=look, bg="dark", clean=False))


def _checked_frozen(frozen):
    """What a plan froze, as the engine takes it: nothing, or {"fallback": None | "kiss"} (a pair's weave or Kiss distance). ValueError for anything else."""
    if frozen is None:
        return {}
    if not isinstance(frozen, dict) or set(frozen) - {"fallback"} or ("fallback" in frozen and frozen["fallback"] not in (None, "kiss")):
        raise ValueError("a frozen plan of the universe family holds only the pair's fallback: null (the weave) or 'kiss'")
    return dict(frozen)


def render(look, irises, size=1024, aspect=None, names=None, date=None, opts=None, want_scene=False, times=None, key=None, frozen=None):
    """One artwork (the prototype's entry). look: echo, deepfield, vortex or starfield (the last three draw one eye). irises: a list of one to six Iris (or
    the bytes of restored squares). size: the long side in px (1024 a preview, 4096 a master). aspect: the canvas id of the layout (None: its default).
    names: the customer's names (a list of at most one per eye, or the old "Anna;Max" string) and date, drawn small under the irises when given.
    opts: the laboratory's switches (ENGINE_OPTS) and the buyer's rotate (the trio's roles) and swap. Returns the PIL image, or (image, scene) with
    want_scene (the scene holds the eyes, the layout, the seed and the facts of the render in scene.info).
    WP8B (step B): key is the plan's seed key (seed_key(); default: default_key, the look's own style with the buyer's swap and rotate), from which and from the
    eyes' ids (irises[k].eye_id: an Iris made without one has the first 16 hex digits of the sha256 of its bytes) the seed is made; the names, the date, the
    canvas, the size and the pixels are not in it. opts seed_mode "legacy" seeds as before step B (the bytes of the irises, the look and the layout key).
    frozen: what the plan fixed before the render ({"fallback": None | "kiss"}: a pair's weave or Kiss distance): obeyed, and engine.DesignChanged when the
    pupils of these eyes contradict a weave."""
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
    if key is None and o.get("seed_mode") != "legacy":
        key = default_key(look, len(irises), o.get("layout"), o)
    elif key is not None:
        key = _checked_key(key, look)
    return EN.render(LK.LOOKS[look](), [_iris(e, f"eye{i + 1}") for i, e in enumerate(irises)], int(size), aspect, TX.split_names(names), o,
                     times=times, want_scene=want_scene, key=key, frozen=_checked_frozen(frozen))


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
    look) and the plates version (None: the current one). The options are written in their canonical form, so that one choice has one seed whatever way a caller
    spells it (WP8B): swap is true only for the pair that is swapped (it exchanges the two irises, and means nothing else), rotate is the trio's role shift modulo
    three (and nothing for any other layout), look is the look the buyer chose when it is not Echo, the default (the look drawn is in design_used already)."""
    o = opts if isinstance(opts, dict) else {}
    rot = o.get("rotate")
    rot = rot % 3 if (layout == "trio" and isinstance(rot, int) and not isinstance(rot, bool)) else 0
    kopts = {"swap": True if (layout == "pair" and o.get("swap")) else None, "rotate": rot or None, "look": look if look != "echo" else None}
    return {"style": style, "design_used": look, "bg": "dark", "clean": False, "layout": layout, "opts": kopts, "pv": CT.PLATES_VERSION if pv is None else int(pv)}


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


def _profile_id(p):
    return p.get("eye_id") if isinstance(p, dict) else getattr(p, "eye_id", None)


def _eye_ids(spec, profiles, n):
    """[eye id] of the n eyes in the order of the spec (the customer's order, before a pair's swap), or [] when they are not all known: spec["eye_ids"] (the
    order's own record), else the ids of the sealed profiles. An id that is not 16 hex digits is no id."""
    ids = spec.get("eye_ids")
    if not isinstance(ids, (list, tuple)):
        ids = [_profile_id(p) for p in (profiles or [])]
    ids = list(ids)[:n]
    return ids if len(ids) == n and all(SD.is_eye_id(i) for i in ids) else []


def plates_for(look, wall, seed, pv):
    """[plate id] the picture of a look draws from, from the seed and the plates version alone, no pixels (the very pick functions the looks call, and the very
    draws they make of the look's own random stream, so the plan and the picture cannot disagree; the test of the family replays it on every look): [] for a look
    that draws no plate (Echo off the wall canvas), the DUST plate of the accent for Echo on the wall canvas (9:19.5), and the one plate of Deep Field (its first draw
    is the number of diffraction stars), Vortex (a crisp spiral) and Starfield (the Milky Way whose band axis fits the seeded target). NoPlate when the library has
    none at that version."""
    from .. import core as C
    if look == "echo":
        return [UPL.pick_wall(C.Rand(seed, "echo/wall"), pv)["id"]] if wall else []
    if look == "deepfield":
        rnd = C.Rand(seed, "deep")
        rnd.uniform()
        return [UPL.pick_deep(rnd, pv)["id"]]
    if look == "vortex":
        return [UPL.pick_vortex(C.Rand(seed, "vortex"), pv)["id"]]
    return [UPL.milky_choice(C.Rand(seed, "starfield"), 32.0, 12.0, pv)[0]["id"]]


def _canvas_profiles(spec, profiles, n):
    """The sealed profiles in the order of the canvas: a pair's swap exchanges the two irises (preview() turns them), so the profile of the first iris of the canvas
    is the second the spec names."""
    profs = list(profiles or [])[:n]
    if n == 2 and _opts3(spec)["swap"]:
        profs = profs[::-1]
    return profs


def frozen_of(n, lay, how):
    """What the plan fixes from a layout built from the sealed profiles: for a pair whose pupils were both known (how "profile") the fallback, "kiss" (the pupils
    need more than the weave allows) or None (the weave); nothing otherwise (the render decides, as the preview did)."""
    return {"fallback": "kiss" if lay.info.get("overlap_fallback") else None} if (n == 2 and how == "profile") else {}


def frozen_for(spec, profiles):
    """What the plan freezes for a spec from the sealed profiles of its eyes (the spec's order): the pair's fallback, else {}. The master obeys it (a weave the
    pupils of the master's eyes no longer allow is DesignChanged: the order is held, never drawn another way); the preview of the same spec takes it from
    spec["profiles"], so the preview and the master draw the same."""
    e, look, aspect, lname = _engine(spec)
    n = spec.get("eyes", 1)
    if n != 2:
        return {}
    names = _names_of(spec.get("names"), n)
    o = spec.get("engine_opts") if isinstance(spec.get("engine_opts"), dict) else {}
    lay, how = _layout_at_1024(n, look, aspect, lname, bool(names or TX.clean(spec.get("date"))), spec, _canvas_profiles(spec, profiles, n), o)
    return frozen_of(n, lay, how)


def resolve(spec, profiles=None):
    """The plan of a style that needs no pixels (a few milliseconds): the look, the registry's layout, the canvas, the geometry of the layout at 1024 px
    in units of the short side S (the centre and radius of every iris, the contacts with their kind and distance in R, so a 4096 px master is the same
    picture), the fallback of a pair whose pupils need more than the weave allows (the Kiss distance), and the key a seed is made of. profiles: the sealed
    profiles of the eyes (an EyeProfile, its record dict or None); a pair's distance is read from their pupils (geometry_from says "profile"), else from
    the layout's default reach ("default"). What the render measures itself (a pupil on a 1024 px graded frame, not on the 256 px grade the profile was
    made on) can move a pair's distance in the third decimal: the plan names the decisions, the render makes the pixels.
    WP8B (step B): when the ids of the eyes are known (spec["eye_ids"], else the ids of the sealed profiles) the plan also holds the SEED (seeds.seed_for_key of the
    ids in canvas order and the seed key: the names, the date, the canvas, the size and the pixels are not in it) and the PLATES the picture will draw from (plates_for:
    the plan's plates_needed are the 4K plates a master of it fetches), so a plan, a preview and a master of one eye agree before anything is drawn. frozen holds the
    pair's fallback when both profiles carry a pupil; decided is False for a plan whose choices the render still decides from its own pixels (a pair without both
    pupils, and a group: which iris is in front at a contact and the hairline edges depend on the luminance of the irises, and the groups are a laboratory style)."""
    e, look, aspect, lname = _engine(spec)
    n = spec.get("eyes", 1)
    names = _names_of(spec.get("names"), n)
    has_text = bool(names or TX.clean(spec.get("date")))
    o = spec.get("engine_opts") if isinstance(spec.get("engine_opts"), dict) else {}
    opts3 = _opts3(spec)
    lay, how = _layout_at_1024(n, look, aspect, lname, has_text, spec, _canvas_profiles(spec, profiles, n), o)
    S = float(lay.S)
    slots = [{"cx": round(s.cx / S, 5), "cy": round(s.cy / S, 5), "R": round(s.R / S, 5)} for s in lay.slots]
    contacts = [{"a": c.a, "b": c.b, "kind": c.kind, "d_R": round(c.d / lay.slots[c.a].R, 4)} for c in lay.contacts]
    fallback = "kiss" if lay.info.get("overlap_fallback") else None
    layout_id = spec.get("layout") or CT.default_layout(spec["style"], n)
    pv = _pv(spec)
    key = seed_key(spec["style"], look, layout_id, opts3, pv)
    ids = _eye_ids(spec, profiles, n)
    seed = SD.seed_for_key(ids[::-1] if (n == 2 and opts3["swap"]) else ids, key) if ids else None
    plates = plates_for(look, n == 1 and aspect == "9:19.5", seed, pv) if seed is not None else None
    frozen = frozen_of(n, lay, how)
    return {"family": "universe", "style": spec["style"], "design_used": look, "fallback": fallback, "layout": layout_id, "canvas": aspect,
            "clean": False, "size_ratio": [lay.W, lay.H], "geometry": {"key": lay.key, "layout": lay.layout, "slots": slots, "contacts": contacts, "from": how,
                                                                       "d_units": lay.info.get("d_units"), "d_needed": lay.info.get("d_needed")},
            "seed_key": key, "seed_from": "eye_id", "eye_ids": ids, "seed": None if seed is None else str(seed), "frozen": frozen, "decided": n == 1 or bool(frozen),
            "plates": plates, "steps": ["art"]}


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
    """The facts of a render that name something (small JSON-safe numbers and words): the look, the layout, the plates, the halo, the contacts, and the fallback the
    render took (kiss: a pair whose pupils need more than the weave allows is drawn at the Kiss distance; the compose reply reports it as its fallback), and
    frozen: the choice a plan can fix as it was drawn (a pair's fallback; nothing for one eye or a group)."""
    info = scene.info
    fb = "kiss" if scene.layout.info.get("overlap_fallback") else None
    log = {"look": look, "layout": scene.layout.key, "aspect": scene.layout.aspect, "plates": plates_used(info), "halo_rows": info.get("halo_rows"),
           "band_rows": info.get("band_rows"), "coarse": scene.f, "fallback": fb, "frozen": {"fallback": fb} if scene.n == 2 else {}}
    for k in ("plate", "accent_plate", "notches", "contacts", "plate_fallback"):
        if k in info:
            log[k] = info[k]
    return log


def preview(eyes, spec, size=1024, check=False):
    """One style on its eyes: one (Echo, Vortex, Deep Field, Starfield), two (the pair: Echo) or three to six (the group: Echo). Returns a styles.Preview
    whose img is the CLEAN render (the dispatcher's watermark=True, or styles.watermarked, makes the free preview). check=True adds the selfcheck report
    (T1, T6, T7 and T12; for a pair or a group T1 reads the compositor's own masks of the pure iris pixels) to .selfcheck. spec["opts"]: the buyer's look
    (echo, vortex, ...), rotate (the trio's roles) and swap (a pair's two irises exchange places); spec["engine_opts"]: the laboratory's switches.
    WP8B (step B): the seed is made from the eyes' ids (Iris.eye_id: the sealed id; an Iris made without one has the hash of its bytes) and the seed key of the spec
    (style, look, layout, swap, rotate, look option, pv; the words, the canvas and the size are not part of it); spec["pv"] is the plates version every pick takes.
    What the plan froze is spec["frozen"] (the master: the stored plan's: a pair's fallback, obeyed or DesignChanged), or, for a pair whose spec carries the sealed
    profiles (spec["profiles"], the preview), what frozen_for makes of them: the same fallback in both. Preview.log["plates"] lists the plates the picture drew from."""
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
    key = seed_key(spec["style"], look, spec.get("layout") or CT.default_layout(spec["style"], n), opts3, _pv(spec))
    fz = spec.get("frozen") if isinstance(spec.get("frozen"), dict) and spec["frozen"] else None
    if fz is None and n == 2:
        fz = frozen_for(spec, spec.get("profiles")) or None
    times = {}
    img, scene = render(look, irises, size, aspect, names, date, o, want_scene=True, times=times, key=key, frozen=fz)
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
    return {s: preview(eyes, dict(spec, style=s, frozen=None), size) for s in styles}
