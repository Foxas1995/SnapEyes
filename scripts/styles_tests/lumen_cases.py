# -*- coding: utf-8 -*-
"""The golden cases of the light family (api/_lib/styles/lumen: Nebula, Supernova, Halo, Sparks, Aurora, Iris Echo, Powder Burst), written once and run twice:
record_goldens_lumen.py renders them and writes the SHA-256 of every picture into data/lumen_goldens.json; test_lumen.py renders the very same cases and
compares. numpy, Pillow and the fixtures of synth_iris only (no real eye, no plate: the family reads none).

A case is one picture: a design, an eye (a synthetic iris of one of the three colour classes), a canvas, a size and optionally the customer's names and
date. The matrix: every design x every eye class at 512 and 1024 px on the square canvas, a 4096 px master of every design on the blue eye, and the other
two canvases and the text lockup at 512 px.

  render_case(render, Iris, fixtures, case, irises) -> {sha, w, h, cls, seed, facts}
      render   lumen.render(design, eye, fmt, size, names, date) -> a kit.Result
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

DESIGNS = ("nebula", "stardust", "halo", "sparks", "aurora", "echo", "dust")  # echo: Iris Echo, 2026-10-27; dust: Powder Burst, 2026-10-28
EYES = ("blue_round", "dark_brown_round", "grey_round")          # the three colour classes: own, dark_brown, grey
SIZES = (512, 1024)
MASTER = (4096, "blue_round")
TEXT = {"names": "Anna Max", "date": "12 MAY 2026"}
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
    for design in DESIGNS:
        size, eye = MASTER
        out.append(dict(key=case_key(design, eye, "1:1", size), design=design, eye=eye, fmt="1:1", size=size, names="", date=""))
    for design in DESIGNS:
        for eye, fmt, names, date in (("blue_round", "4:5", TEXT["names"], ""), ("grey_round", "9:19.5", "", TEXT["date"]),
                                      ("dark_brown_round", "1:1", TEXT["names"], TEXT["date"])):
            out.append(dict(key=case_key(design, eye, fmt, 512, names, date), design=design, eye=eye, fmt=fmt, size=512, names=names, date=date))
    return out


def _plain(v):
    """The facts of a look as plain JSON: strings, booleans, numbers rounded to 4 places, lists and dicts of them (arrays become lists)."""
    if isinstance(v, (str, bool)) or v is None:
        return v
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return round(float(v), 4)
    if isinstance(v, dict):
        return {str(k): _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, np.ndarray)):
        return [_plain(x) for x in list(v)]
    return str(v)


def facts(log):
    """What a render chose that names something (the factor of its grid, the partner hue, the wind, the counts), under the design's own key."""
    return {k: _plain(log[k]) for k in DESIGNS if k in log}


def render_case(render, Iris, fixtures, case, irises=None):
    """Render one case and describe it. irises: an optional cache {eye name: Iris} (an Iris caches its grades and its ring)."""
    irises = {} if irises is None else irises
    if case["eye"] not in irises:
        irises[case["eye"]] = Iris(fixtures[case["eye"]], case["eye"])
    r = render(case["design"], irises[case["eye"]], case["fmt"], case["size"], case["names"], case["date"])
    a = np.ascontiguousarray(np.asarray(r.img.convert("RGB")))
    return {"sha": hashlib.sha256(a.tobytes()).hexdigest(), "w": int(a.shape[1]), "h": int(a.shape[0]), "cls": irises[case["eye"]].cls,
            "seed": int(r.info["seed"]), "facts": json.loads(json.dumps(facts(r.ctx.log), sort_keys=True))}
