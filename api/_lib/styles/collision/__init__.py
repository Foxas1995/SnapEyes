# -*- coding: utf-8 -*-
"""styles.collision: the overlapping-irises family of the v3 engine. Pairs, trios, families and chains: two or more restored irises that touch or
overlap, with the matter of the design around the union (the irises themselves are composited by one compositor, and a pixel of an iris that is
not in a seam band or a contact strip IS the graded iris, byte for byte).

  infinity   Collision Infinity   two irises overlap like an infinity sign: a smooth planned S seam between them (DG1: no torn edge), a thin dark edge,
                                  powder in each eye's colours; clean=1 is Clean Infinity (no matter, pure black). A pair whose colour step across the
                                  seam is too large (K above lens_mode.K_STACK) is drawn in STACK mode: one iris in front, no weave
                                  (design_used "stack", fallback "stack_contrast"); a pair with a wide pupil falls back to the Kiss geometry
                                  (design_used "kiss", fallback "overlap_fallback")
  kiss       Kiss Collision       d 1.70 R on a diagonal, one iris in front, a crumbling contact, a burst of powder through the contact
  trio       Family Colours, 3    the measured isosceles of the owner's reference (base 1.53 R, flanks 1.71 R), crumbling contacts
  family     Family Colours, 4-8  zigzag, brick, ring, flower, cluster (a diagonal of three is the same engine), crumbling contacts, d 1.65 R
  chain      Infinity Chain       an S weave on every link of a chain of three to six, d 1.40 R (held: the laboratory only)

This is work package WP7A, STEP A of the family: the prototype's code ported verbatim (engine.py is collision.py, compositor.py, scenes.py,
seam_plan.py, lens_mode.py, powder.py, haze.py, raster.py, extra.py, fill.py, kit.py, jetplates.py; scripts/styles_tests/port_collision.py lists every
edit and the golden suite replays the prototype's own pictures). The source is the DG1 snapshot of the design rounds' collision code: round 2c plus the smooth seam. The
seed is still the prototype's (the bytes of the irises, the design, the background, the scene key and the NAMES: step B of this family, WP7B, takes
the names out and seeds from the eye ids and the plan's seed key as the singles do since WP5B). So are the plan freeze (resolve() here says what can be
known without a pixel, and nothing more) and the work_side per layout.

The contract of api/_lib/styles/__init__.py, for this family:
    resolve(spec, profiles)        the plan of a style as far as no pixel is needed: design, fallback by the pupils, layout, canvas, the seed key
    preview(eyes, spec, size, check=False)    one style on its eyes, a Preview (clean: styles.watermarked() makes the free preview)
    tiles(eyes, styles, spec, size)           several styles of one eye count on one eye preparation
and the prototype's own entry, render(design, eyes, fmt, size, names, date, bg, clean, opts, layout), which the golden suite calls.

An eye is a styles.core.Iris (or the bytes of a restored square). Nothing here reads a path, a key or the network; the JET, RIVER and cloud plates come
from styles.plates (the 1K files of the bundle: a collision picture is drawn on the canonical 1024 geometry and decodes no 4K plate), the chip atlas from
styles.atlas. Names and date are the customer's own words (styles.text).

The owner's sign-offs are production constants (PRODUCTION): the soft shadow of the front iris on the back one (D8, zone_c), the contact edge of his own
reference (edge "ref": the black valley of H10), the smooth planned seam, no seam dust (D15), the crumbling base pair of the trio (D3), the Kiss depth of
15 percent and 17.5 percent in the families (D18: scenes.D_KISS, D_FAMILY). The seam budget E1 is the owner's reading: the pixels that are neither one
iris nor the other (the mixed share) are at most about 3 percent of an iris and the seam band (the support of the blend, padded for the check) at
most 4 percent. engine_opts (the admin laboratory only) overrides them for a board.
"""
from __future__ import annotations

import re
import time

import numpy as np

from ... import catalogue as CT
from .. import core as C
from .. import pupil as PUPM
from .. import seeds as SD
from .. import text as TX
from . import compositor as CC
from . import engine as E
from . import jetplates as JP
from . import scenes as CL

DESIGNS = ("infinity", "kiss", "trio", "family", "chain")                  # the prototype's NAMES
SIZES = (64, 4096)                                                          # the long side a render may ask for
NAMES_MAX = 8
E1_BAND_MAX = 0.04                                                          # the owner's budget: the seam band (support of the blend, as T1 pads it) per iris
MIX_MAX = 0.03                                                              # ... and the pixels that are really mixed (0.02 < w < 0.98): about 3 percent
PRODUCTION = {"edge": "ref", "zone_c": True, "seam": "plan", "seam_dust": False, "lens_mode": "auto", "trio_base": "crumble"}
OPT_KEYS = frozenset(("edge", "zone_c", "seam", "seam_dust", "kiss_d", "hairline", "plates", "breakup", "rotate", "trio_base", "lens_mode", "plan_mode", "beta",
                      "support_budget", "strict_gate", "allow_bar", "exact_scale", "auto_hairline", "mem", "prm", "fill", "keep_cv", "flood", "seam_hw",
                      "seam_amp", "seam_lam", "seam_bend", "seam_fine", "seam_wave", "blend", "pad", "dp_sigma", "dp_rho"))
T3_TOL = 0.004                                                              # the visible share is measured on pixels: a margin of 0.4 point
T3_ZONE = 0.985                                                             # ... inside this share of R (the brief's definition: the feather of the disc is not the iris)
SEPARATORS = (" ∞ ", " & ", " · ")                               # what layout_text puts between names (an infinity, an ampersand, a middle dot)
ASSET_RANGE = {"infinity": (0.55, 0.70), "kiss": (0.60, 0.75), "trio": (0.50, 0.65), "family": (0.50, 0.65), "chain": (0.55, 0.70)}       # T4 of the brief

LOCKUP = TX.LOCKUP_JOIN
Result = E.Result
NotOffered = E.NotOffered


# ----------------------------------------------------------------------------- the words
def _words(value):
    """The customer's names as a list: a list of strings, the old wire string "Anna;Max" or the lockup line "Anna · Max"; cleaned, a letter the artwork
    font cannot draw left out, at most NAMES_MAX names of NAME_MAX letters."""
    if isinstance(value, (list, tuple)):
        parts = [v[:TX.LINE_MAX] for v in value[:NAMES_MAX * 2] if isinstance(v, str)]
    elif isinstance(value, str):
        parts = [p for chunk in value[:1000].split(LOCKUP) for p in re.split(r"[;\n]", chunk)]
    else:
        return []
    out = []
    for p in TX.split_names(parts):
        p = TX.clean("".join(ch for ch in p if not TX.unsupported(ch)))
        if p:
            out.append(p[:TX.NAME_MAX])
    return out[:NAMES_MAX]


def _date(value):
    if not isinstance(value, str):
        return ""
    return TX.clean("".join(ch for ch in value[:1000] if not TX.unsupported(ch)))[:TX.DATE_MAX]


# ----------------------------------------------------------------------------- what a spec names
def default_canvas(design, n, layout=None):
    """The canvas a design is drawn on when the spec names none: the prototype's own default per design and layout (the paid file is this canvas at
    4096 px on its long side)."""
    if design in ("infinity", "kiss"):
        return "3:2"
    if design == "trio":
        return "1:1"
    if design == "chain":
        return "3:2" if n <= 4 else "3:1"
    lay = layout or {3: "diag", 4: "zigzag", 5: "brick", 6: "brick", 7: "ring", 8: "ring"}[n]
    fmt = {"zigzag": "3:2", "brick": "3:2", "diag": "3:2", "ring": "1:1", "flower": "1:1", "cluster": "1:1"}[lay]
    return "1:1" if (lay == "brick" and n >= 7) else fmt


def _scene_of(design, n, layout, fmt, clean=False):
    """The scene the engine builds for a design with n eyes in a layout on a canvas (the canonical 1024 px, no words): the prototype's own constructors,
    with the arguments engine.render gives them. Raises what the constructor raises for a canvas it has no constants for (a KeyError of the eye count,
    a ValueError)."""
    if design in ("infinity", "kiss"):
        return CL.pair_scene(fmt, 1024, 1.3, False, False, "clean" if clean else design)
    if design == "trio":
        return CL.trio_scene(fmt, 1024, False, False)
    if design == "family":
        return CL.family_scene(n, layout, fmt, 1024, False, False)
    if design == "chain":
        return CL.chain_scene(n, fmt, 1024, False, False)
    raise ValueError(design)


def builds_on(design, n, layout, fmt, clean=False):
    """True when the family has the constants to build this design with n eyes in this layout on this canvas, and the scene it builds is on that canvas
    (the brick of seven and eight eyes is always the square one, whatever canvas is asked). The registry lists the canvases of a style, not of an eye
    count: a chain draws 3:1 for four to six links, 3:2 and the phone column for three and four, and asked for the others the scene constructor used to
    raise a KeyError (a request the registry itself advertises answered with a 500)."""
    if fmt not in CL.ASPECTS:
        return False
    try:
        return _scene_of(design, n, layout, fmt, clean).fmt == fmt
    except (KeyError, ValueError, IndexError, AssertionError):
        return False


def draws_on(design, n, layout, fmt, clean=False):
    """True when the family offers this canvas for this design, eye count and layout: it builds (builds_on) and the iris keeps the brief's size floor
    T18 (a diameter of at least 22 percent of the canvas width, 0.60 of the height of the 3:1 panorama) with no words. The brief tested the default
    canvas of each layout; a ring of five to eight or a flower on the 3:2 canvas is below the floor, and a request for it is drawn on the layout's
    default canvas instead of a picture that its own hard check refuses."""
    if fmt not in CL.ASPECTS:
        return False
    try:
        sc = _scene_of(design, n, layout, fmt, clean)
        return sc.fmt == fmt and bool(CL.dfloor_ok(sc))
    except (KeyError, ValueError, IndexError, AssertionError):
        return False


def canvases_for(style, n, layout=None):
    """The canvases of the registry's list on which the family draws this style with n eyes in a layout (the registry's order; the layout's own default
    canvas is `default_canvas`). A canvas the registry lists for the style but not for this eye count or layout is not in the answer: _setup draws the
    default canvas in its place."""
    e = CT.engine_for(style, n)
    if e is None or e.get("module") != "collision":
        raise ValueError(f"{style!r} with {n!r} eyes is not a style of the collision family")
    design = e["design"]
    layout = layout or CT.default_layout(style, n)
    if layout not in CT.layouts_for(style, n):
        raise ValueError(f"{style!r} with {n} eyes has no layout {layout!r}")
    if design == "trio" and layout == "diag":
        design = "family"
    return [c for c in e["canvases"] if draws_on(design, n, layout, c, bool(e.get("clean")))]


def _setup(spec):
    """(engine entry, design, layout, canvas, clean) of the spec, or ValueError for a style that is not a style of this family. design is the
    prototype's name of what is drawn: the registry names trio for three eyes, and a diagonal of three is the family engine. The canvas is the one the
    spec names when the registry lists it and the family draws this design, eye count and layout on it (draws_on), else the layout's own default."""
    style, n = spec.get("style"), spec.get("eyes", 2)
    e = CT.engine_for(style, n)
    if e is None or e.get("module") != "collision":
        raise ValueError(f"{style!r} with {n!r} eyes is not a style of the collision family")
    design = e["design"]
    layout = spec.get("layout") or CT.default_layout(style, n)
    if layout not in CT.layouts_for(style, n):
        raise ValueError(f"{style!r} with {n} eyes has no layout {layout!r}")
    if design == "trio" and layout == "diag":
        design = "family"
    fmt = spec.get("canvas") or spec.get("format")
    if fmt not in e["canvases"] or not draws_on(design, n, layout, fmt, bool(e.get("clean"))):
        fmt = default_canvas(design, n, layout if design == "family" else None)
    return e, design, layout, fmt, bool(e.get("clean"))


def _pv(spec):
    pv = spec.get("pv")
    return pv if isinstance(pv, int) and not isinstance(pv, bool) and pv >= 0 else CT.PLATES_VERSION


def _opts3(spec):
    return spec.get("opts") if isinstance(spec.get("opts"), dict) else {}


def seed_key(style, design, layout, clean=False, bg="dark", opts=None, pv=None):
    """The plan's seed key of a collision artwork (seeds.py names its fields). Step A draws with the prototype's seed; the key is what step B seeds
    from and what makes two plans that draw differently differ (plan8)."""
    o = opts if isinstance(opts, dict) else {}
    return {"style": style, "design_used": design, "bg": bg, "clean": bool(clean), "layout": layout, "opts": {k: o.get(k) for k in SD.OPT_FIELDS},
            "pv": CT.PLATES_VERSION if pv is None else int(pv)}


def _engine_opts(spec, design):
    """The options of one render: the production constants, the buyer's rotate (trio), then the laboratory's engine_opts."""
    o = dict(PRODUCTION)
    rot = _opts3(spec).get("rotate")
    if design == "trio" and isinstance(rot, int) and not isinstance(rot, bool) and 0 <= rot <= 2:
        o["rotate"] = rot
    eo = spec.get("engine_opts")
    if isinstance(eo, dict):
        o.update({k: v for k, v in eo.items() if k in OPT_KEYS})
    return o


def _eyes(eyes):
    out = []
    for e in eyes:
        if isinstance(e, C.Iris):
            out.append(e)
        elif isinstance(e, (bytes, bytearray)):
            out.append(C.Iris(bytes(e)))
        else:
            raise TypeError("an eye is an Iris or the bytes of an image")
    return out


# ----------------------------------------------------------------------------- the prototype's entry
def render(design, eyes, fmt=None, size=1024, names=None, date=None, bg="dark", clean=False, opts=None, layout=None):
    """One collision artwork (the prototype's entry, with guards). eyes: Iris objects or the bytes of restored squares, in canvas order (A first). size:
    the long side in px (1024 a preview, 4096 a master). names: a list (the old "Anna;Max" string and the lockup line are accepted) and date: drawn
    small under the irises when given. opts: the prototype's switches for the owner's sign-offs and the laboratory (see PRODUCTION and OPT_KEYS; a key
    that is not named is ignored as the prototype ignored it). Returns engine.Result: .img (PIL), .img8, .info (the facts of the render: timings,
    geometry, lens mode, shares), .scene, .tiles, .discs, .comp, .cfg, .pups, .text_layout. Raises engine.NotOffered for a bar pupil."""
    if design not in DESIGNS:
        raise KeyError(design)
    irises = _eyes(eyes)
    n = len(irises)
    if (design in ("infinity", "kiss") and n != 2) or (design == "trio" and n != 3) or (design == "family" and not 3 <= n <= 8) or (design == "chain" and not 3 <= n <= 6):
        raise ValueError(f"{design} does not take {n} eyes")
    if bg not in ("dark", "universe"):
        raise ValueError(f"no background {bg!r}")
    if fmt is not None and fmt not in CL.ASPECTS:
        raise ValueError(f"no canvas {fmt!r} (the canvases are {', '.join(CL.ASPECTS)})")
    if fmt is not None:
        try:
            _scene_of(design, n, layout, fmt, bool(clean))
        except KeyError:                                 # the scene constructors have constants per eye count and canvas: a missing one is a canvas this design has no scene on
            raise ValueError(f"{design} with {n} eyes has no scene on the {fmt!r} canvas") from None
    if not SIZES[0] <= int(size) <= SIZES[1]:
        raise ValueError(f"a canvas of {size} px (from {SIZES[0]} to {SIZES[1]})")
    if bg == "universe":
        # the fill converts every source to float32 (cx_fill: 1.73 GB at 8 full-size eyes): refuse what cannot fit, a laboratory board only
        mb = sum(ir.src.size[0] ** 2 * 12 for ir in irises) / 1048576.0
        if mb > 700.0:
            raise ValueError(f"a universe fill of {n} eyes of up to {max(ir.src.size[0] for ir in irises)} px would hold {mb:.0f} MB of float copies")
    o = dict(PRODUCTION)
    o.update(opts or {})
    JP.trace(True)
    try:
        r = E.render(design, irises, fmt=fmt, size=int(size), names=_words(names) or None, date=_date(date) or None, bg=bg, clean=bool(clean), opts=o, layout=layout)
    finally:
        picked = JP.trace(False)
    r.picked = picked                                    # the JET and RIVER plates the render picked, in order (the haze's cloud plates are in info)
    return r


# ----------------------------------------------------------------------------- the checks
def t3_floors(design_used, sc, o):
    """The visible share every iris must keep (T3 of the brief): Kiss 93 percent, Collision Infinity (and its stack) 87, the trio's apex whole and its
    bases 80 (crumbling base pair, D3) or 84 (woven), Family Colours 82, a chain's interior 80 and its ends 90."""
    n = sc.n
    if design_used == "kiss":
        return [0.93] * n
    if design_used in ("infinity", "stack"):
        return [0.87] * n
    if design_used == "trio":
        ap = sc.info["apex"]
        return [1.0 if k == ap else (0.84 if o.get("trio_base") == "weave" else 0.80) for k in range(n)]
    if design_used == "family":
        return [0.82] * n
    return [0.90 if k in (0, n - 1) else 0.80 for k in range(n)]


def visible_shares(r, zone=None):
    """The visible share of every iris by the brief's definition (T3): the pixels of its disc inside `zone` x R (0.985: the F3 feather of the disc is
    not part of the iris) where it is the front-most iris, over the pixels of that disc."""
    zone = T3_ZONE if zone is None else zone
    comp = r.comp
    bx0, by0 = comp.box[0], comp.box[1]
    out = []
    for k, tk in enumerate(r.tiles):
        sl = (slice(tk.y0 - by0, tk.y0 - by0 + tk.T), slice(tk.x0 - bx0, tk.x0 - bx0 + tk.T))
        ax = np.arange(tk.T, dtype=np.float32) + 0.5 - tk.T / 2.0
        inside = (ax[None, :] ** 2 + ax[:, None] ** 2) <= (zone * tk.R) ** 2
        out.append(float(((comp.occ[sl] == k) & inside).sum()) / float(inside.sum()))
    return out


def text_log(r):
    """The draw log of a render in the shape selfcheck.t7_text reads: one entry per line the engine drew."""
    return [{"kind": kind, "text": str(t).strip(), "px": int(size), "baseline": round(float(base), 1)} for (t, size, tr, x0, base, w, kind) in (r.text_layout or [])]


def customer_strings(names, date):
    """The strings T7 allows an artwork to carry: the customer's names joined as the engine joins them (the three separators) and the date."""
    out = [date] if date else []
    if names:
        out += [sep.join(n.upper() for n in names) for sep in SEPARATORS] + list(names)
    return out


def selfcheck(r, design, spec_ids, names, date):
    """The report of the run-time checks for a collision render (selfcheck.run with the masks of the compositor, plus T2, T3, T4 as measured, T18 and
    T19). T1 and T6: every pixel of an iris's zone A that is in no seam band and no contact strip is the graded iris (the compositor publishes the
    analytic masks, pure_masks). T2: the pupil grown by 0.01 R is untouched. T3: the visible share against the floor of the design. T4: the black
    share is measured and compared with the brief's range, not bounded (it varies with the eye; the suite bounds it on the board eyes). T18 / T19:
    the iris size floor of the layout and the stacking rule (no iris the back one at more than two contacts)."""
    from .. import selfcheck as SC
    t0 = time.perf_counter()
    img8 = r.img8
    masks, minfo = CC.pure_masks(r.scene, r.tiles, r.cfg, pupil_fns=r.comp.pupils)
    crops = []
    for d, tl, m in zip(r.discs, r.tiles, masks):
        t = d.g.shape[0]
        ox, oy = d.x0 - tl.x0, d.y0 - tl.y0
        crops.append(m[oy:oy + t, ox:ox + t])
    del masks
    sdm = getattr(r, "seam_dust_mask", None)
    if sdm is not None:                                  # the D15 dust (a laboratory switch, off in production) lies on the back iris by design
        for k, d in enumerate(r.discs):
            t = d.g.shape[0]
            crops[k] = crops[k] & ~sdm[d.y0:d.y0 + t, d.x0:d.x0 + t]
    rep = SC.run(img8, r.discs, text_log=text_log(r), customer=customer_strings(names, date), ids=list(spec_ids), masks=crops)
    del crops
    bad, per = 0, []
    for d, fn in zip(r.discs, (r.comp.pupils[k] for k in range(len(r.discs)))):
        t = d.g.shape[0]
        xs = (np.arange(d.x0, d.x0 + t, dtype=np.float32) + 0.5)[None, :]
        ys = (np.arange(d.y0, d.y0 + t, dtype=np.float32) + 0.5)[:, None]
        p = SC.iris_pixels(img8, d, mask=fn(xs, ys, 0.01))
        per.append(p["bad"])
        bad += p["bad"]
    rep["checks"]["t2"] = {"ok": bad == 0, "violations": bad, "per_iris": per}
    used = r.info.get("design_used", design)
    floors = t3_floors(used, r.scene, r.opts)
    shares = [round(v, 4) for v in visible_shares(r)]
    rep["checks"]["t3"] = {"ok": all(s + T3_TOL >= f for s, f in zip(shares, floors)), "shares": shares, "floors": floors, "zone": T3_ZONE}
    lo_hi = ASSET_RANGE.get("infinity" if used == "stack" else used)
    share, lit = SC.black_shares(img8, (SC.BLACK_THR, SC.BLACK_LITERAL))
    in_range = None if (r.info.get("clean") or r.info.get("bg") != "dark" or lo_hi is None) else bool(lo_hi[0] <= share <= lo_hi[1])
    rep["checks"]["t4"] = {"ok": True, "share": round(share, 4), "range": list(lo_hi) if lo_hi else None, "in_range": in_range, "literal3": round(lit, 4),
                           "bounded": False}
    rep["checks"]["t18"] = {"ok": bool(CL.dfloor_ok(r.scene)), "d_floor": 0.22}
    counts = E.back_counts(r.scene)
    rep["checks"]["t19"] = {"ok": max(counts.values(), default=0) <= 2, "back_counts": {str(k): v for k, v in sorted(counts.items())}}
    rep["checks"]["seam"] = seam_facts(r, minfo)
    rep["ok"] = all(c["ok"] for c in rep["checks"].values())
    rep["ms"] = int(round((time.perf_counter() - t0) * 1000))
    return rep


def seam_facts(r, minfo=None):
    """The owner's budget E1 for the seam, as numbers: the share of each iris the seam band covers (T1's padded mask, per weave lens of the iris) and
    the planned plan's mixed share and support (seam_plan: 0.02 < w < 0.98 and 0 < w < 1), against E1_BAND_MAX and MIX_MAX. ok when no weave is drawn."""
    plans = [p for p in ((r.cfg.plans or {}).values())]
    if not plans:
        return {"ok": True, "weave": False}
    mixed = max(p.info.get("mixed_share", 0.0) for p in plans)
    supp = max(p.info.get("support_share", 0.0) for p in plans)
    e1 = None
    if minfo is not None:
        sc = r.scene
        nw = [max(1, sum(1 for q in sc.rules if q.mode == "weave" and k in (q.a, q.b))) for k in range(sc.n)]
        e1 = max(e / w for e, w in zip(minfo["e1"], nw))
    return {"ok": bool(mixed <= MIX_MAX + 1e-6 and supp <= MIX_MAX + 1e-6 and (e1 is None or e1 <= E1_BAND_MAX + 1e-6)), "weave": True,
            "mixed": round(float(mixed), 4), "support": round(float(supp), 4), "e1": None if e1 is None else round(float(e1), 4),
            "limits": {"mixed": MIX_MAX, "e1": E1_BAND_MAX}, "K": r.info.get("lens_K"), "mode": r.info.get("lens_mode_used")}


# ----------------------------------------------------------------------------- the contract
def _pupil_of(p):
    """The pupil dict of one eye's sealed profile (an EyeProfile or its record), or None."""
    if p is None:
        return None
    try:
        if hasattr(p, "pupil"):
            return p.pupil
        rec = p.get("pupil") if isinstance(p, dict) else None
        return PUPM.from_record(rec) if isinstance(rec, dict) and "reach" in rec else None
    except Exception:  # noqa: a profile that cannot be read is no information (the render measures the eye itself)
        return None


def _profile_id(p):
    return p.get("eye_id") if isinstance(p, dict) else getattr(p, "eye_id", None)


def _eye_ids(spec, profiles, n):
    ids = spec.get("eye_ids")
    if not isinstance(ids, (list, tuple)):
        ids = [_profile_id(p) for p in (profiles or [])]
    ids = list(ids)[:n]
    return ids if len(ids) == n and all(SD.is_eye_id(i) for i in ids) else []


def resolve(spec, profiles=None):
    """The plan of a style as far as no pixel is needed: the design, the layout, the canvas, the seed key and, for a pair, the placement rule applied to
    the pupils of the sealed profiles (a wide pupil turns Collision Infinity into the Kiss geometry: design_used kiss, fallback overlap_fallback). What
    needs the pixels of the irises, the colour step across the seam (stack mode) and the seed, is None here: step A seeds from the bytes of the eyes, and
    the plan freeze of WP7B decides the lens mode once, on the preview's canonical grade, and records it. profiles: the sealed profiles of the eyes (an
    EyeProfile, its record dict or None)."""
    e, design, layout, fmt, clean = _setup(spec)
    n = spec.get("eyes", 2)
    has_text = bool(_words(spec.get("names")) or _date(spec.get("date")))
    design_used, fallback, d_over_R = design, None, None
    pups = [_pupil_of(p) for p in (profiles or [])]
    if design in ("infinity", "kiss"):
        kind = "clean" if clean else design
        sc = CL.pair_scene(fmt, 1024, 1.3, has_text, False, kind)
        u = (sc.rules[0].ux, sc.rules[0].uy)
        if design == "kiss":
            d_over_R = CL.D_KISS
        elif len(pups) == 2 and all(p is not None for p in pups):
            d_over_R, raw, over = CL.solve_infinity_d(PUPM.reach(pups[0], u), PUPM.reach(pups[1], (-u[0], -u[1])))
            if over:
                design_used, fallback, d_over_R = "kiss", "overlap_fallback", CL.D_KISS
    key = seed_key(spec["style"], design_used, layout, clean, "dark", _opts3(spec), _pv(spec))
    W, H = CL.canvas_size(fmt, 1024)
    return {"family": "collision", "style": spec["style"], "design_used": design_used, "fallback": fallback, "layout": layout, "canvas": fmt, "clean": clean,
            "size_ratio": [W, H], "d_over_R": None if d_over_R is None else round(float(d_over_R), 4), "lens_mode": None, "seed_key": key,
            "seed_from": "iris_bytes", "eye_ids": _eye_ids(spec, profiles, n), "seed": None, "frozen": {}, "plates": None, "steps": ["art"]}


def _log(r, used):
    """The facts of a render a Preview carries (small, JSON safe after steps._plain)."""
    i = r.info
    keep = ("design", "bg", "clean", "n", "gate_fail", "pupil_classes", "d_raw", "overlap_fallback", "lens_mode_used", "lens_K", "stack_d", "front", "rules",
            "d_over_R", "wind_deg", "counts", "edge_modes", "auto_hairline", "edge_delta_320", "breakup_px", "plan_s", "vis", "chain_d_need")
    log = {k: i[k] for k in keep if k in i}
    log["design_used"] = used
    log["fallback"] = i.get("fallback") or ("overlap_fallback" if i.get("overlap_fallback") else None)
    cloud = i.get("cloud") or {}
    plates = list(cloud.get("ids") or []) + [str(k) for k in (getattr(r, "picked", None) or [])]
    pinfo = i.get("plates") or {}
    for kind in ("jets", "river"):
        plates += [str(k) for k in (pinfo.get(kind) or {}).get("keys", [])]
    log["plates"] = list(dict.fromkeys(plates))
    return log


def preview(eyes, spec, size=1024, check=False):
    """One style on its eyes. eyes: a list of Iris (or the bytes of restored squares), in canvas order. Returns a styles.Preview whose img is the CLEAN
    render: the dispatcher's watermark=True (or styles.watermarked) makes the free preview. check=True adds the selfcheck report. The seed is the
    prototype's (step A): the bytes of the eyes, the design, the scene and the names."""
    from .. import Preview
    e, design, layout, fmt, clean = _setup(spec)
    n = spec.get("eyes", 2)
    if not isinstance(eyes, (list, tuple)) or len(eyes) != n:
        raise ValueError(f"{spec.get('style')!r} draws exactly {n} eyes")
    names, date = _words(spec.get("names")), _date(spec.get("date"))
    o = _engine_opts(spec, design)
    if _opts3(spec).get("swap") is True and n == 2:
        eyes = list(eyes)[::-1]
    r = render(design, eyes, fmt, size, names, date, "dark", clean, o, layout if design == "family" else None)
    used = r.info.get("design_used", design)
    graded = [d.iris.graded(d.Sd) for d in r.discs]
    r.comp.P = r.comp.A = None                           # the premultiplied layers only paste the irises; the checks read the front-most map and the geometry
    for tk in r.tiles:
        tk.rgb = tk.a = None                              # ... and the tiles' pixels are not read by pure_masks either (a 4096 px iris tile is 87 MB of float32)
    rep = selfcheck(r, design, [spec["style"], used, layout], names, date) if check else None
    out = Preview(img=r.img, discs=[(d.cx, d.cy, d.R) for d in r.discs], graded=graded, design=used, fmt=fmt, size=int(size), seed=r.seed,
                  cls=[ir.cls for ir in r.irises], log=_log(r, used), times=r.info.get("times"), text_log=text_log(r), selfcheck=rep, ctx=None, frame=r.scene)
    return out


def tiles(eyes, styles, spec, size=480):
    """{style id: Preview} of several styles of this family on one eye preparation: the Iris objects are shared, so each eye's ring, class, pupil and
    grades are measured once. A tile takes the default layout and canvas of its own style. An exception of one tile is not caught here: the caller that
    serves a batch decides."""
    return {s: preview(eyes, dict(spec, style=s, layout=None, canvas=None), size) for s in styles}
