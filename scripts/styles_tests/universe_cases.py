# -*- coding: utf-8 -*-
"""The golden cases of the universe family, written once and run twice: record_goldens_universe.py runs them on the SCRATCH prototype
(wave-y3/designs/universe.py: the code the approved boards were made with) and writes the SHA-256 of every picture into
data/universe_goldens.json; test_goldens_universe.py runs the very same cases on the port (api/_lib/styles/universe) and compares. A port is
verbatim when every hash is equal. numpy, Pillow and the fixtures of synth_iris only.

A case is one picture: a look, one to six eyes (synthetic irises: the three colour classes, the slit and the bar pupil), a canvas, a size and
optionally the customer's names and date and the laboratory's switches. The matrix:
  solo     every look x the three colour classes x 512 and 1024 px on the square canvas (the brief's default); Echo also at 4096 px, the master
  canvases the other two single canvases (4:5, the wall 9:19.5) for Echo and for a plate look, and the wall at 1024 px (its accent plate is a 2k LOD of
           a 4K file, which is in private storage and not in the repo)
  text     the names and the date under one eye, and a name with a Lithuanian letter
  pair     Echo over the Collision Infinity geometry on 3:2, 1:1, 4:5 and 5:4, the Kiss distance (forced), the widest pupils, names, the
           laboratory's switches (no zone C, the narrow seam)
  group    Echo for three to six eyes: the trio, the zigzag, the bricks and the rings, the trio rotated and with the weave at its base, names

  render_case(render, Iris, fixtures, case) -> {sha, w, h, cls, seed, eye_seeds, facts}
      render   render(look, irises, size, aspect, names, date, opts) -> (image, scene)   (scratch universe.render or the port's, with want_scene)
      Iris     the Iris class of the core module under test (fx.core.Iris or styles.core.Iris)
      fixtures {eye name: PNG bytes} from synth_iris.png_bytes
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

LOOKS = ("echo", "deepfield", "vortex", "starfield")
EYES = ("blue_round", "dark_brown_round", "grey_round")          # the three colour classes: own, dark_brown, grey
SIZES = (512, 1024)
MULTI = ("blue_round", "green_round", "amber_slit", "dark_brown_round", "grey_round", "blue_slit")       # the first n eyes of a group
FIXTURE_BASE = tuple(sorted(set(EYES) | set(MULTI) | {"dark_brown_bar", "green_bar"}))
PLATE_LOOKS = frozenset(("deepfield", "vortex", "starfield"))
TEXT = {"names": ["Anna", "Max"], "date": "12 MAY 2026"}


def case_key(look, eyes, aspect, size, names=(), date="", tag=""):
    return f"{look}.{'+'.join(eyes)}.{aspect or 'auto'}.{size}" + (".text" if (names or date) else "") + (f".{tag}" if tag else "")


def _c(look, eyes, aspect, size, names=(), date="", opts=None, tag=""):
    return dict(key=case_key(look, eyes, aspect, size, names, date, tag), look=look, eyes=list(eyes), aspect=aspect, size=size, names=list(names), date=date,
                opts=dict(opts or {}))


def cases():
    """The ordered list of cases: dict(key, look, eyes, aspect, size, names, date, opts)."""
    out = []
    for size in SIZES:
        for look in LOOKS:
            for eye in EYES:
                out.append(_c(look, [eye], "1:1", size))
    for eye in EYES:                                                                    # the master
        out.append(_c("echo", [eye], "1:1", 4096))
    for look in ("vortex", "deepfield", "starfield"):                                    # the plate looks as masters: 2k and 4k LODs of 4K plates (LOCAL)
        out.append(_c(look, ["blue_round"], "1:1", 4096))
    # the other two single canvases (the wall's accent plate at 512 px is a 1K LOD: no 4K file is read)
    for look, eye, asp in (("echo", "blue_round", "4:5"), ("echo", "grey_round", "9:19.5"), ("vortex", "dark_brown_round", "4:5"),
                           ("starfield", "blue_round", "9:19.5"), ("deepfield", "grey_round", "4:5"), ("echo", "dark_brown_round", "9:19.5")):
        out.append(_c(look, [eye], asp, 512))
    out.append(_c("echo", ["blue_round"], "9:19.5", 1024))                                # the wall at 1024: a 2k LOD of a 4K plate (LOCAL)
    # polar fill (a slit or bar pupil, a pet) and the laboratory's one-eye switches
    out.append(_c("echo", ["blue_round"], "1:1", 2048))                                 # the coarse factor 2
    out.append(_c("echo", ["dark_brown_bar"], "1:1", 512))
    out.append(_c("echo", ["amber_slit"], "1:1", 512))
    out.append(_c("echo", ["blue_round"], "1:1", 512, opts={"pet": True}, tag="pet"))      # the pet flag is the laboratory's: render() gets it as the opts key
    out.append(_c("echo", ["blue_round"], "1:1", 512, opts={"fill_only": True}, tag="fillonly"))
    # the customer's words
    out.append(_c("echo", ["blue_round"], "1:1", 512, names=TEXT["names"][:1], date=TEXT["date"]))
    out.append(_c("echo", ["grey_round"], "1:1", 512, names=["Gabriel" + chr(0x117)]))
    out.append(_c("vortex", ["dark_brown_round"], "1:1", 512, names=TEXT["names"][:1]))
    # pairs: Echo over the Collision Infinity geometry (A in front on one side of the lens, B on the other)
    for asp in ("3:2", "1:1", "4:5", "5:4"):
        out.append(_c("echo", ["blue_round", "dark_brown_round"], asp, 512))
    out.append(_c("echo", ["blue_round", "grey_round"], "3:2", 512))
    out.append(_c("echo", ["blue_round", "dark_brown_round"], "3:2", 1024))
    out.append(_c("echo", ["blue_round", "dark_brown_round"], "3:2", 4096))              # a pair as a master: the coarse factor 3
    out.append(_c("echo", ["dark_brown_bar", "green_bar"], "3:2", 512))                  # the widest pupils of the fixtures (a bar along the axis): the weave at nearly its longest
    out.append(_c("echo", ["blue_round", "dark_brown_round"], "3:2", 512, opts={"kiss": True}, tag="kiss"))      # the Kiss distance (1.70 R, a crumble), forced as the laboratory does
    out.append(_c("echo", ["amber_slit", "blue_slit"], "3:2", 512))
    out.append(_c("echo", ["blue_round", "dark_brown_round"], "3:2", 512, names=TEXT["names"], date=TEXT["date"]))
    out.append(_c("echo", ["blue_round", "dark_brown_round"], "3:2", 512, opts={"zone_c": False}, tag="nozc"))
    out.append(_c("echo", ["blue_round", "grey_round"], "3:2", 512, opts={"seam_band": "ad"}, tag="seamad"))
    out.append(_c("echo", ["blue_round", "dark_brown_round"], "3:2", 512, opts={"swap": True}, tag="swap"))
    # groups of three to six
    for n, lname, asp in ((3, None, None), (4, None, None), (5, None, None), (6, None, None), (5, "ring5", None), (6, "ring6", None)):
        o = {"layout": lname} if lname else {}
        out.append(_c("echo", MULTI[:n], asp, 512, opts=o, tag=lname or ""))
    out.append(_c("echo", MULTI[:3], None, 1024))
    out.append(_c("echo", MULTI[:6], None, 1024))
    out.append(_c("echo", MULTI[:3], None, 2048))                                       # the coarse factor 2 (a canvas between 1536 and 2304 px)
    out.append(_c("echo", MULTI[:3], None, 512, opts={"rotate": 1}, tag="rot1"))
    out.append(_c("echo", MULTI[:3], None, 512, opts={"trio_base": "weave"}, tag="weave"))
    out.append(_c("echo", MULTI[:4], "3:2", 512, names=TEXT["names"] + ["Lina", "Jonas"]))
    return out


# the owner's own restorations of the calibration set (never committed: SNAPEYES_CALIB names their folder; only the hashes of the pictures are): one of
# each colour class and a second plain one, every look at 1024 px, a pair and a trio at 512 px: the real-eye goldens (G-real), reported as LOCAL lines
REAL_EYES = ("own215120", "drv_d01", "drv_w06", "drv_d02")


def real_cases():
    out = [_c(look, [e], "1:1", 1024) for e in REAL_EYES for look in LOOKS]
    out.append(_c("echo", list(REAL_EYES[:2]), "3:2", 512))
    out.append(_c("echo", list(REAL_EYES[:3]), None, 512))
    return out


def needs_4k(case, lods=None):
    """Does this picture draw from a 4K plate (private storage, not the repo)? True for a plate look at the master size and for a plate whose LOD
    the recording named 2k or 4k (lods: the plate facts of the recording)."""
    if lods:
        return any(v in ("2k", "4k") for v in lods)
    return case["size"] >= 2048 and case["look"] in PLATE_LOOKS


def _round(v, nd=4):
    if isinstance(v, (bool, str)) or v is None:
        return v
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return round(float(v), nd)
    if isinstance(v, dict):
        return {str(k): _round(x, nd) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_round(x, nd) for x in v]
    if isinstance(v, np.ndarray):
        return [_round(x, nd) for x in v.tolist()]
    return str(v)


def facts_of(scene):
    """What a render chose that names something, read from the scene (the same attributes in the prototype and in the port). Compared exactly: apart from
    the picture hash they say WHAT differs when a hash does."""
    info = scene.info
    out = {"layout": scene.layout.key, "aspect": scene.layout.aspect, "f": scene.f, "S": int(scene.S), "wh": [int(scene.W), int(scene.H)],
           "halo_rows": info.get("halo_rows"), "band_rows": info.get("band_rows")}
    for k in ("plate", "accent_plate"):
        if isinstance(info.get(k), dict):
            out[k] = {kk: info[k].get(kk) for kk in ("id", "lod", "upscale", "angle", "mirror")}
    out["plate_fallback"] = info.get("plate_fallback")
    out["contacts"] = info.get("contacts")
    out["notches"] = info.get("notches")
    out["text"] = [list(t) for t in info.get("text", [])]
    out["eye_geometry"] = [[round(float(e.cx), 3), round(float(e.cy), 3), round(float(e.R), 3), e.fill_mode, round(float(e.k_s), 4)] for e in scene.eyes]
    return json.loads(json.dumps(_round(out), sort_keys=True))


def render_case(render, Iris, fixtures, case, irises=None):
    """Render one case and describe it. irises: an optional cache {eye name: Iris} (an Iris caches its grades, its ring and the source of its fill)."""
    irises = {} if irises is None else irises
    eyes = []
    for n in case["eyes"]:
        if case["opts"].get("pet"):                       # a pet is flagged on the Iris object itself: never a shared one
            eyes.append(Iris(fixtures[n], n))
            eyes[-1].is_pet = True
            continue
        if n not in irises:
            irises[n] = Iris(fixtures[n], n)
        eyes.append(irises[n])
    img, scene = render(case["look"], eyes, case["size"], case["aspect"], case["names"], case["date"], dict(case["opts"]))
    a = np.ascontiguousarray(np.asarray(img.convert("RGB")))
    return {"sha": hashlib.sha256(a.tobytes()).hexdigest(), "w": int(a.shape[1]), "h": int(a.shape[0]), "cls": [e.cls for e in eyes],
            "seed": int(scene.seed), "eye_seeds": [int(s) for s in scene.eye_seeds], "facts": facts_of(scene)}
