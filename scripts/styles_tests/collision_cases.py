# -*- coding: utf-8 -*-
"""The golden cases of the collision family, written once and run twice: record_goldens_collision_scratch.py runs them on the SCRATCH prototype (the DG1
snapshot of the collision code, wave-dg1/final, with the JET, RIVER and cloud plates of the design round) and writes the SHA-256 of every picture into
data/collision_goldens.json; test_goldens_collision.py runs the very same cases on the port (api/_lib/styles/collision) and compares. A port is verbatim
when every hash is equal. numpy, Pillow and the fixtures of synth_iris only.

A case is one picture: a design (infinity, kiss, trio, family, chain), a set of synthetic irises, a canvas, a size, the customer's words, a layout and
the prototype's switches. The matrix: every pair design on three pairs of different colour classes at 1024 px, the other canvases, the sizes 512, 1024 and
4096, the text lockup, the stack lens (forced), the laboratory's switches (the universe fill, the D15 seam dust, the woven base of the trio), the trio, every
layout of the family for four to eight eyes, and the chain. Both sides get the production switches (PRODUCTION: the contact edge of the owner's own
reference, which the prototype's render() does not default to; every other production value is the prototype's default) plus the case's own.

  render_case(render, Iris, fixtures, case, irises) -> {sha, w, h, seed, facts}
      render   render(design, eyes, fmt, size, names, date, bg, clean, opts, layout) -> a result with .img (PIL), .info, .seed
      Iris     the Iris class of the core module under test (fx.core.Iris or styles.core.Iris)
      fixtures {eye name: PNG bytes} from fixture_bytes
"""
from __future__ import annotations

import hashlib
import io
import json

import numpy as np

# the eyes: synthetic irises of synth_iris (five colours in the three colour classes of the engine, all round pupils, none a failure of the gate)
EYE_SPECS = {
    "blue": dict(kind="blue", pupil="round", seed=11),
    "green": dict(kind="green", pupil="round", seed=12),
    "brown": dict(kind="dark_brown", pupil="round", seed=14),
    "grey": dict(kind="grey", pupil="round", seed=16),
    "amber": dict(kind="amber", pupil="round", seed=31),
    "blue2": dict(kind="blue", pupil="round", seed=32),
    "green2": dict(kind="green", pupil="round", seed=33),
    "brown2": dict(kind="dark_brown", pupil="round", seed=34),
}
WIDE_PUPIL = "wide"                      # a blue iris whose pupil is 0.52 R wide: the placement rule falls back to the Kiss geometry
PRODUCTION = {"edge": "ref", "zone_c": True, "seam": "plan", "seam_dust": False, "lens_mode": "auto", "trio_base": "crumble"}
TEXT = {"names": ["Anna", "Max"], "date": "12 MAY 2026"}


def fixture_bytes(name):
    """The PNG bytes of one fixture eye."""
    import synth_iris as SI
    if name == WIDE_PUPIL:
        im = SI.make(kind="blue", pupil="round", seed=41)
        a = np.asarray(im, np.float32).copy()
        n = a.shape[0]
        ax = np.arange(n, dtype=np.float32) + 0.5 - n / 2.0
        r = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / np.float32(SI.R_FRAC * n)
        w = np.clip((0.52 - r) / 0.02 + 0.5, 0.0, 1.0)[..., None]
        a = a * (1 - w) + np.asarray((7, 7, 9), np.float32) * w
        from PIL import Image
        b = io.BytesIO()
        Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), "RGB").save(b, "PNG", compress_level=3)
        return b.getvalue()
    return SI.png_bytes_of(**EYE_SPECS[name])


def fixture_names():
    return sorted(EYE_SPECS) + [WIDE_PUPIL]


def case_key(design, eyes, fmt, size, clean=False, tag=""):
    return f"{design}{'.clean' if clean else ''}.{'+'.join(eyes)}.{fmt}.{size}" + (f".{tag}" if tag else "")


def _c(design, eyes, fmt, size, clean=False, names=None, date="", layout=None, bg="dark", opts=None, tag=""):
    if layout:
        tag = layout + ("." + tag if tag else "")
    if names or date:
        tag = (tag + "." if tag else "") + "text"
    return dict(key=case_key(design, eyes, fmt, size, clean, tag), design=design, eyes=list(eyes), fmt=fmt, size=size, clean=clean, names=list(names or []),
                date=date, layout=layout, bg=bg, opts=dict(opts or {}))


BB, BG, GA = ("blue", "brown"), ("blue", "green"), ("grey", "amber")


def cases():
    """The ordered list of cases."""
    out = []
    # the three pairs (a blue and a dark brown, a blue and a green, a grey and an amber) at 1024 px on the 3:2 canvas: every pair design
    for pair in (BB, BG, GA):
        out.append(_c("infinity", pair, "3:2", 1024))
        out.append(_c("infinity", pair, "3:2", 1024, clean=True))
        out.append(_c("kiss", pair, "3:2", 1024))
    # the sizes: 512 and 4096 px (the 4096 picture is the 1024 picture sample for sample: exact multiples of the canonical geometry)
    out.append(_c("infinity", BB, "3:2", 512))
    out.append(_c("infinity", BB, "3:2", 4096))
    out.append(_c("infinity", BG, "3:2", 4096, clean=True))
    out.append(_c("kiss", BB, "3:2", 4096))
    # the other canvases, at 512 px
    for fmt in ("5:4", "1:1", "4:5", "9:19.5"):
        out.append(_c("infinity", BG, fmt, 512))
    out.append(_c("infinity", GA, "1:1", 512, clean=True))
    out.append(_c("kiss", BB, "4:5", 512))
    out.append(_c("kiss", GA, "9:19.5", 512))
    # the customer's words
    out.append(_c("infinity", BB, "3:2", 1024, names=TEXT["names"], date=TEXT["date"]))
    out.append(_c("kiss", BG, "3:2", 1024, names=TEXT["names"]))
    out.append(_c("infinity", GA, "1:1", 512, clean=True, names=TEXT["names"], date=TEXT["date"]))
    # the stack lens (forced: no real pair needs it), the dark pair that draws a hairline contact, the wide pupil that falls back to the Kiss geometry
    out.append(_c("infinity", BB, "3:2", 1024, opts={"lens_mode": "stack"}, tag="stack"))
    out.append(_c("infinity", GA, "3:2", 512, clean=True, opts={"lens_mode": "stack"}, tag="stack"))
    out.append(_c("infinity", ("brown", "brown2"), "3:2", 1024))
    out.append(_c("infinity", (WIDE_PUPIL, "green"), "3:2", 1024))
    # the laboratory's switches: the universe fill, the D15 seam dust, the hard seam and the brief's own edge
    out.append(_c("kiss", BB, "3:2", 512, bg="universe", tag="universe"))
    out.append(_c("kiss", BB, "3:2", 512, opts={"seam_dust": True}, tag="dust"))
    out.append(_c("infinity", BG, "3:2", 512, opts={"seam": "hard"}, tag="hard"))
    out.append(_c("infinity", BG, "3:2", 512, opts={"edge": "brief"}, tag="brief"))
    # the trio (the owner's isosceles): the square canvas at 1024 and 4096 px, the other canvases, the cycled roles, the woven base pair, words
    tri = ("blue", "brown", "green")
    out.append(_c("trio", tri, "1:1", 1024))
    out.append(_c("trio", tri, "1:1", 4096))
    out.append(_c("trio", tri, "3:2", 512))
    out.append(_c("trio", tri, "9:19.5", 512))
    out.append(_c("trio", tri, "1:1", 512, opts={"rotate": 1}, tag="rot1"))
    out.append(_c("trio", tri, "1:1", 512, opts={"trio_base": "weave"}, tag="weave"))
    out.append(_c("trio", ("grey", "amber", "blue"), "1:1", 1024, names=["Anna", "Max", "Lina"], date=TEXT["date"]))
    # the family: every layout of four to eight eyes
    e4 = ("blue", "brown", "green", "grey")
    e5 = e4 + ("amber",)
    e6 = e5 + ("blue2",)
    e7 = e6 + ("green2",)
    e8 = e7 + ("brown2",)
    out.append(_c("family", e4, "3:2", 1024, layout="zigzag"))
    out.append(_c("family", e4, "3:2", 4096, layout="zigzag"))
    out.append(_c("family", e4, "1:1", 512, layout="cluster"))
    out.append(_c("family", e4, "1:1", 512, layout="ring"))
    out.append(_c("family", e4, "3:2", 512, layout="brick"))
    out.append(_c("family", e5, "3:2", 1024, layout="brick"))
    out.append(_c("family", e5, "1:1", 512, layout="flower"))
    out.append(_c("family", e5, "1:1", 512, layout="ring"))
    out.append(_c("family", e6, "3:2", 1024, layout="brick"))
    out.append(_c("family", e6, "1:1", 512, layout="ring"))
    out.append(_c("family", e6, "1:1", 512, layout="flower"))
    out.append(_c("family", e7, "1:1", 512, layout="ring"))
    out.append(_c("family", e7, "1:1", 512, layout="brick"))
    out.append(_c("family", e8, "1:1", 1024, layout="ring"))
    out.append(_c("family", e8, "1:1", 512, layout="brick"))
    out.append(_c("family", e8, "1:1", 512, layout="flower"))
    out.append(_c("family", e4, "3:2", 1024, layout="zigzag", names=["Anna", "Max", "Lina", "Joe"], date=TEXT["date"]))
    out.append(_c("family", tri, "3:2", 512, layout="diag"))
    # the chain
    out.append(_c("chain", tri, "3:2", 1024))
    out.append(_c("chain", e4, "3:2", 512))
    out.append(_c("chain", e5, "3:1", 1024))
    out.append(_c("chain", e6, "3:1", 512))
    out.append(_c("chain", tri, "9:19.5", 512))
    out.append(_c("chain", e4, "9:19.5", 512))
    return out


# the real calibration irises of the design round (never committed: SNAPEYES_CALIB names their folder; only the hashes of the pictures are): the eight pairs of
# the DG1 boards at 1024 px in both builds of the infinity, the Kiss on two of them, a trio, a family and a chain. Reported as LOCAL lines.
REAL_PAIRS = {
    "blue_yellow": ("own215120", "drv_w04"),
    "blue_brown": ("own215120", "p05i"),
    "brown_pair": ("p05i", "p08f"),
    "grey_hazel": ("drv_d01", "p09f"),
    "similar_blue": ("sample_cache", "own215120"),
    "similar_brown": ("drv_w09", "p21e"),
    "very_dark": ("lid19b", "drv_w06"),
    "hetero_blue_copper": ("sample_cache", "drv_w03"),
}
REAL_EYES = sorted({n for p in REAL_PAIRS.values() for n in p} | {"drv_w04", "p09f", "drv_d02", "drv_w06"})


def real_cases():
    out = []
    for name, pair in REAL_PAIRS.items():
        out.append(_c("infinity", pair, "3:2", 1024, tag=name))
        out.append(_c("infinity", pair, "3:2", 1024, clean=True, tag=name))
    for name in ("blue_brown", "grey_hazel"):
        out.append(_c("kiss", REAL_PAIRS[name], "3:2", 1024, tag=name))
    out.append(_c("trio", ("p08f", "own215120", "drv_w04"), "1:1", 1024, tag="real"))
    out.append(_c("family", ("own215120", "drv_w04", "p08f", "drv_d01"), "3:2", 1024, layout="zigzag", tag="real"))
    out.append(_c("chain", ("own215120", "drv_w04", "p08f"), "3:2", 1024, tag="real"))
    return out


def _facts(info):
    """The choices a render made that name something: the design drawn, the lens mode and its colour step, the fallbacks, the fronts, the edge modes, the
    plates the haze took. Compared exactly (strings and rounded numbers); apart from the picture hash they say WHAT differs when a hash does."""
    out = {"design_used": info.get("design_used"), "lens_mode": info.get("lens_mode_used"), "overlap_fallback": bool(info.get("overlap_fallback")),
           "fallback": info.get("fallback"), "rules": [list(r) for r in info.get("rules", [])], "n_particles": (info.get("counts") or {}).get("n"),
           "vis": [round(float(v), 4) for v in info.get("vis", [])], "d_over_R": [round(float(v), 4) for v in info.get("d_over_R", [])],
           "edge_modes": {str(k): v for k, v in sorted((info.get("edge_modes") or {}).items())}, "gate_fail": list(info.get("gate_fail", [])),
           "cloud": list((info.get("cloud") or {}).get("ids", []))}
    if info.get("lens_K") is not None:
        out["lens_K"] = round(float(info["lens_K"]), 2)
    if info.get("auto_hairline"):
        out["auto_hairline"] = [int(i) for i in info["auto_hairline"]]
    return json.loads(json.dumps(out, sort_keys=True))


def render_case(render, Iris, fixtures, case, irises=None):
    """Render one case and describe it. irises: an optional cache {eye name: Iris} (an Iris caches its grades and its ring)."""
    irises = {} if irises is None else irises
    for n in case["eyes"]:
        if n not in irises:
            irises[n] = Iris(fixtures[n], n)
    eyes = [irises[n] for n in case["eyes"]]
    r = render(case["design"], eyes, case["fmt"], case["size"], case["names"], case["date"], case["bg"], case["clean"], case["opts"], case["layout"])
    a = np.ascontiguousarray(np.asarray(r.img.convert("RGB")))
    return {"sha": hashlib.sha256(a.tobytes()).hexdigest(), "w": int(a.shape[1]), "h": int(a.shape[0]), "seed": int(r.seed), "facts": _facts(r.info)}
