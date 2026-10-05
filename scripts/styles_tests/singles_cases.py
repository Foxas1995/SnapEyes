# -*- coding: utf-8 -*-
"""The golden cases of the singles family, written once and run twice: record_goldens_scratch.py runs them on the SCRATCH prototype
(wave-y3/designs/singles.py with Celestial Gold replaced by the owner-approved variant A, wave-cg2/A/cg_a.py: the code the approved boards were
made with) and writes the SHA-256 of every picture into data/singles_goldens.json; test_goldens_singles.py runs the very same cases on the port
(api/_lib/styles/singles) and compares. A port is verbatim when every hash is equal. numpy, Pillow and the fixtures of synth_iris only.

A case is one picture: a design, an eye (a synthetic iris of one of the three colour classes), a canvas format, a size and optionally the
customer's names and date. The standard matrix is every design x every eye class x the sizes 512, 1024 and 4096 on the square canvas (the
brief's default); the extra cases are the other two canvases and the text lockup, at 512 px.

  render_case(render, Iris, fixtures, case) -> {sha, w, h, cls, seed, facts}
      render   render(design, eye, fmt, size, names, date) -> a result with .img (PIL), .ctx.log, .info  (scratch singles.render or the port's)
      Iris     the Iris class of the core module under test (fx.core.Iris or styles.core.Iris)
      fixtures {eye name: PNG bytes} from synth_iris.png_bytes
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

DESIGNS = ("clean", "powder", "splash", "elements", "radiance", "gold")
EYES = ("blue_round", "dark_brown_round", "grey_round")          # the three colour classes: own, dark_brown, grey
SIZES = (512, 1024, 4096)
NEEDS_4K = frozenset(("powder", "splash", "elements"))           # at 4096 px these draw from a 4K plate, which is in private storage and not in the repo
TEXT = {"names": "Anna Max", "date": "12 MAY 2026"}                # one space: the port cleans a run of spaces (text.clean), the scratch drawer did not
FIXTURE_BASE = ("blue_round", "dark_brown_round", "grey_round")


def case_key(design, eye, fmt, size, names="", date=""):
    return f"{design}.{eye}.{fmt}.{size}" + (".text" if (names or date) else "")


def cases():
    """The ordered list of cases: dict(key, design, eye, fmt, size, names, date)."""
    out = []
    for size in SIZES:
        for design in DESIGNS:
            for eye in EYES:
                out.append(dict(key=case_key(design, eye, "1:1", size), design=design, eye=eye, fmt="1:1", size=size, names="", date=""))
    # the other two canvases and the text lockup, at 512 px: the frame (the iris shrinks 0.94 and moves up with text), the wallpaper's safe zones
    for design in DESIGNS:
        for eye, fmt, names, date in (("blue_round", "4:5", TEXT["names"], ""), ("grey_round", "9:19.5", "", TEXT["date"]),
                                      ("dark_brown_round", "1:1", TEXT["names"], TEXT["date"])):
            out.append(dict(key=case_key(design, eye, fmt, 512, names, date), design=design, eye=eye, fmt=fmt, size=512, names=names, date=date))
    return out


# the owner's own restorations of the calibration set (never committed: SNAPEYES_CALIB names their folder; only the hashes of the pictures are):
# one of each colour class and a second plain one, at 1024 px, every design: the real-eye goldens (G-real), reported as LOCAL lines
REAL_EYES = ("own215120", "drv_d01", "drv_w06", "drv_d02")


def real_cases():
    return [dict(key=case_key(d, e, "1:1", 1024), design=d, eye=e, fmt="1:1", size=1024, names="", date="") for e in REAL_EYES for d in DESIGNS]


def needs_4k(case):
    return case["size"] >= 2048 and case["design"] in NEEDS_4K


def _facts(log):
    """The choices a render made that name something: the plate ids, the liquid, the wind. Compared exactly (they are strings and the
    rounded numbers of a pick), apart from the picture hash they say WHAT differs when a hash does."""
    out = {}
    for k in ("powder", "splash", "elements", "radiance", "gold"):
        v = log.get(k)
        if isinstance(v, dict):
            row = {}
            for kk, vv in v.items():
                if isinstance(vv, (str, bool)) or vv is None:
                    row[kk] = vv
                elif isinstance(vv, (int, float)):
                    row[kk] = round(float(vv), 4)
            out[k] = row
    return out


def render_case(render, Iris, fixtures, case, irises=None):
    """Render one case and describe it. irises: an optional cache {eye name: Iris} (an Iris caches its grades and its ring)."""
    irises = {} if irises is None else irises
    if case["eye"] not in irises:
        irises[case["eye"]] = Iris(fixtures[case["eye"]], case["eye"])
    r = render(case["design"], irises[case["eye"]], case["fmt"], case["size"], case["names"], case["date"])
    a = np.ascontiguousarray(np.asarray(r.img.convert("RGB")))
    return {"sha": hashlib.sha256(a.tobytes()).hexdigest(), "w": int(a.shape[1]), "h": int(a.shape[0]), "cls": irises[case["eye"]].cls,
            "seed": int(r.info["seed"]), "facts": json.loads(json.dumps(_facts(r.ctx.log), sort_keys=True))}
