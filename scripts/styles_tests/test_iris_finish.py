# -*- coding: utf-8 -*-
"""The iris finish of the v3 engine (api/_lib/styles/core.py finish_iris, the owner's choice of 2026-10-27: "dabar geriau", "manau daug geriau", and no
highlight dots in the pupil). Every style of every family draws its iris from Iris.graded, and graded is the studio grade with this finish on top, so the
golden suites pin the engine with the finish OFF (they set core.IRIS_FINISH = False) and this suite guards the finish itself:

  1. the parameters the owner approved (no gloss), and the switch: a constant, on
  2. the finish on the graded disc of three synthetic eyes: outside the disc nothing changes, inside it does, the iris is clearer (more local contrast),
     the limbal band is darker than before, the pupil no lighter; deterministic, a fresh Iris of the same bytes gives the same bytes
  3. a master: a disc above FIN_R_CAP is finished on a reduced copy and the change brought up; it is within a level or so of finishing at full size,
     costs less, and reduced to the preview's size it is the preview's finish drawn finer
No network, no image model, no real eye in the repository (the eyes are procedural: synth_iris).
    python test_iris_finish.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure. Run by suites/run_main.sh as v3finish."""
import hashlib
import os
import sys
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
sys.path.insert(0, API)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from _lib import iris as L  # noqa: E402
from _lib.styles import core as C  # noqa: E402
import synth_iris as SI  # noqa: E402

EYES = ("blue_round", "dark_brown_round", "grey_round")

# ============================================================================================ 1. the parameters and the switch
section("1. the parameters and the switch")
check("the finish is on", C.IRIS_FINISH is True)
check("the owner's parameters: no gloss in the pupil (\"no dots inside like the competitor\"), a dark limbal ring from 0.78 R, a deeper pupil",
      C.FIN["gloss"] == 0.0 and C.FIN["limb"] == (0.78, 0.60) and C.FIN["pupil_dark"] == 0.85 and C.FIN["dehaze"] == 0.55, C.FIN)
src_core = open(os.path.join(API, "_lib", "styles", "core.py"), encoding="utf-8").read()
check("the switch is a constant of the module (IRIS_FINISH = True), never read from the environment: a deployment cannot lose the finish; only the golden suites set it False on the module",
      "\nIRIS_FINISH = True " in src_core and "import os" not in src_core and "environ" not in src_core)

# ============================================================================================ 2. the finish on the graded disc
section("2. the finish on the graded disc")
Sd = 1024
R = max(8, int(round(Sd * L.STUDIO_FILL))) / 2.0
ax = np.arange(Sd, dtype=np.float64) + 0.5 - Sd / 2.0
rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / R
outside, inside = rr > 1.0, rr <= 1.0
body, limb, pupil = (rr > 0.40) & (rr < 0.75), (rr > 0.90) & (rr < 0.98), rr < 0.15


def lap_std(a, m):
    g = a.astype(np.float64).mean(axis=2)
    lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap[m[1:-1, 1:-1]].std())


C.IRIS_FINISH = False
rows = {}
for n in EYES:
    raw = SI.png_bytes(n)
    ir0 = C.Iris(raw, n)
    g0 = ir0.graded(Sd)
    pup0 = C.PUP.analyse(C._tight(ir0.graded(C.REF_SIDE))[0])      # the pupil graded() hands the finish (IRIS_FINISH is off here: the plain grade)
    g1 = C.finish_iris(g0, pupil=pup0)
    g2 = C.finish_iris(np.array(g0), pupil=pup0)
    rows[n] = (g0, g1, g2)
C.IRIS_FINISH = True
check("outside the disc not one pixel changes (the styles draw their own ground there)",
      all(np.array_equal(g0[outside], g1[outside]) for g0, g1, _ in rows.values()))
check("inside the disc the finish changes the iris (it is not a no-op)",
      all(float(np.abs(g1[inside].astype(int) - g0[inside].astype(int)).mean()) > 3.0 for g0, g1, _ in rows.values()),
      {n: round(float(np.abs(g1[inside].astype(int) - g0[inside].astype(int)).mean()), 2) for n, (g0, g1, _) in rows.items()})
check("the iris is clearer: the fibres' local contrast in the body rises by at least a third on every eye",
      all(lap_std(g1, body) >= 1.33 * lap_std(g0, body) for g0, g1, _ in rows.values()),
      {n: (round(lap_std(g0, body), 2), round(lap_std(g1, body), 2)) for n, (g0, g1, _) in rows.items()})
check("the limbal band (0.90 to 0.98 R) is darker than the grade left it, and the pupil no lighter",
      all(g1[limb].mean() < 0.85 * g0[limb].mean() and g1[pupil].mean() <= g0[pupil].mean() + 0.5 for g0, g1, _ in rows.values()),
      {n: (round(float(g0[limb].mean()), 1), round(float(g1[limb].mean()), 1), round(float(g0[pupil].mean()), 1), round(float(g1[pupil].mean()), 1))
       for n, (g0, g1, _) in rows.items()})
check("the finish returns a new uint8 frame of the same shape and leaves its input as it was",
      all(g1.dtype == np.uint8 and g1.shape == g0.shape and g1 is not g0 for g0, g1, _ in rows.values()))
check("deterministic: the same frame twice gives the same bytes", all(np.array_equal(g1, g2) for _, g1, g2 in rows.values()))
h = [hashlib.sha256(np.ascontiguousarray(C.Iris(SI.png_bytes("blue_round"), f"x{i}").graded(Sd)).tobytes()).hexdigest() for i in range(2)]
check("graded() is the grade with the finish: a fresh Iris of the same bytes gives the same bytes, and they are the finished frame",
      h[0] == h[1] and h[0] == hashlib.sha256(np.ascontiguousarray(rows["blue_round"][1]).tobytes()).hexdigest())
g0b = rows["blue_round"][0]
huge = {"found": True, "cx": 0.0, "cy": 0.0, "r_theta": np.full(64, 0.6, np.float32), "rp": 0.6, "cls": "round", "aspect": 1.0}
with_p = C._finish(g0b, pupil=huge).astype(np.int16)
no_p = C._finish(g0b, fin={"pupil_dark": 0.0}, pupil=huge).astype(np.int16)
bright = (g0b.astype(np.float32).mean(axis=2) > 90) & (rr < 0.6)
check("the pupil darkening follows the engine's pupil and touches only what is dark already: with a pupil read far too large (0.6 R), no iris pixel brighter than 90 "
      "is darkened (a lab master of 2026-10-28 had fibres blackened inside an overestimated disc)",
      bright.sum() > 1000 and int(np.abs(with_p[bright] - no_p[bright]).max()) <= 1, (int(bright.sum()), int(np.abs(with_p[bright] - no_p[bright]).max())))
tiny = np.zeros((40, 40, 3), np.uint8)
check("a thumbnail (a disc under 24 px of radius) is returned as it is", C.finish_iris(tiny) is tiny)

# ============================================================================================ 2b. measurements read the grade WITHOUT the finish
section("2b. measurements read the grade without the finish (the sealed profile is measured so: a master's class and pupil must compare with it)")
from _lib.styles import eye as EY  # noqa: E402
from _lib.styles import pupil as PUP  # noqa: E402
from _lib.styles import steps as STEPS  # noqa: E402
meas = {}
for n in EYES + ("grey_lid",):
    raw = SI.png_bytes(n)
    ir = C.Iris(raw, n)
    plain = np.ascontiguousarray(np.asarray(C.grade_disc(ir.src, C.REF_SIDE, ir.ease)))
    prof = EY.EyeInput(raw, eye_id=ir.eye_id).compute_profile(rules=())
    meas[n] = (np.array_equal(ir.ring, C.ring_colours(plain)), ir.cls, prof.cls,
               STEPS._pupil_measure(ir)["cls"] == PUP.analyse(C._tight(plain)[0])["cls"])
check("the ring colours of an eye are measured on the grade alone (the finish's vibrance would move them)", all(v[0] for v in meas.values()), meas)
check("the colour class an Iris draws with is the sealed profile's for every eye, the grey eye with lid shadow included (with the finish it read as own: class_changed)",
      all(v[1] == v[2] for v in meas.values()), meas)
check("the master's pupil measure (steps._pupil_measure) is taken on the grade alone, as the profile's", all(v[3] for v in meas.values()), meas)
check("graded(finish=False) is the plain grade and graded() the finished one, cached apart",
      np.array_equal(C.Iris(SI.png_bytes("blue_round"), "q").graded(Sd, finish=False), rows["blue_round"][0])
      and np.array_equal(C.Iris(SI.png_bytes("blue_round"), "q").graded(Sd), rows["blue_round"][1]))

# ============================================================================================ 3. a master
section("3. a master (a disc above FIN_R_CAP)")
C.IRIS_FINISH = False
big = C.Iris(SI.png_bytes("blue_round", side=2048), "m", max_side=4096).graded(3000)
C.IRIS_FINISH = True
t0 = time.perf_counter()
fast = C.finish_iris(big)
t_fast = time.perf_counter() - t0
t0 = time.perf_counter()
full = C._finish(big)
t_full = time.perf_counter() - t0
d = np.abs(fast.astype(np.int16) - full.astype(np.int16))
check(f"the reduced finish of a 3000 px frame is the full size finish within a level or so (mean under 1.5, 99th percentile under 8 levels of 255)",
      float(d.mean()) < 1.5 and float(np.percentile(d, 99)) < 8, (round(float(d.mean()), 2), float(np.percentile(d, 99))))
check("it costs less than the full size finish", t_fast < t_full, (round(t_fast, 2), round(t_full, 2)))
Rb = max(8, int(round(3000 * L.STUDIO_FILL))) / 2.0
axb = np.arange(3000, dtype=np.float64) + 0.5 - 1500.0
check("outside the master's disc not one pixel changes", np.array_equal(fast[np.sqrt(axb[None, :] ** 2 + axb[:, None] ** 2) > Rb],
                                                                         big[np.sqrt(axb[None, :] ** 2 + axb[:, None] ** 2) > Rb]))
small = np.asarray(Image.fromarray(fast).resize((Sd, Sd), Image.LANCZOS)).astype(np.int16)
C.IRIS_FINISH = False
prev = C.finish_iris(C.Iris(SI.png_bytes("blue_round", side=2048), "p", max_side=4096).graded(Sd)).astype(np.int16)
C.IRIS_FINISH = True
dm = float(np.abs(small[inside] - prev[inside]).mean())
check("the master reduced to 1024 px is the 1024 px preview's finish drawn finer (mean difference inside the disc under 6 levels)", dm < 6.0, round(dm, 2))

from _lib.styles import costs as CO  # noqa: E402
base = CO.step_need("singles.clean", 1, factor=1.0)
_keep = CO.FINISH_S_PER_EYE
CO.FINISH_S_PER_EYE = 0.0
plain = CO.step_need("singles.clean", 1, factor=1.0)
plain8 = CO.step_need("collision.family", 8, factor=1.0)
CO.FINISH_S_PER_EYE = _keep
check("a master's plan counts the finish: 1.5 s per eye in the table's units (2.4 s at the slow factor 1.6), inside the factor like the decode",
      CO.FINISH_S_PER_EYE == 1.5 and abs(base - plain - 1.5) < 1e-9 and abs(CO.step_need("collision.family", 8, factor=1.0) - plain8 - 12.0) < 1e-9, (base, plain))

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
