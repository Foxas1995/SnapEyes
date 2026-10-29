# -*- coding: utf-8 -*-
"""The shape of the delivered pupil (api/_lib/iris.py pupil_shape and the check "pupil_shape" of preview_qa, 2026-10-28). The lab order
lab-261027-9c1f1d48 showed the owner's 215102 with a pupil drawn as a square black blob with an arm and black spots round it: the photo's wide
pupil is lit grey by a room mirrored on the cornea with the photographer's dark silhouette in it, the restoration drew that silhouette as the
pupil, and pupil_lock left it (the silhouette's arm reaches the photo's pupil edge, so its PUPIL_LOCK_EVEN rule reads a circle off the pupil).
Its master was held only because its colour check failed; a master of the same kind with a right colour would have shipped. Now preview_qa
measures the delivered pupil's solidity and fails "pupil_shape" below PREVIEW_QA_SHAPE, so store.needs_review holds it for the owner.

  1. round, slit and bar pupils, with and without a lid or lashes (the twelve synthetic eyes): solidity at least 0.99, the check passes
  2. a pupil painted as the lab order's blob (a square with an arm, a bay and black spots beside it): solidity under the limit, the check
     fails, ok is false, the record needs review, and it is no render check (render_ok and score are the clean picture's)
  3. a picture with no dark centre: no reading and no failure; a fault inside the measure costs nothing but the reading
  4. the master's size: a 4096 px copy reads as its 1024 px preview
  LOCAL (not counted; with SNAPEYES_FIXTURES or suites/private/fixtures): the owner's four restorations, 215102 failing and the other three passing.
No network, no image model.
    python test_pupil_shape.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure. Run by suites/run_main.sh as v3pupil."""
import os
import sys
from unittest import mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def local(name, ok, detail=""):
    print(("LOCAL PASS " if ok else "LOCAL FAIL ") + name + ("" if ok else f"   <- {str(detail)[:400]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_FIXTURES"):
            os.environ.pop(k)
sys.path.insert(0, API)
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from _lib import iris as L  # noqa: E402
from _lib import store  # noqa: E402
import synth_iris as SI  # noqa: E402

R_FRAC = L.iris_radius_frac(1.12)

# ============================================================================================ 1. right pupils
section("1. round, slit and bar pupils, lids and lashes: one convex dark disc")
shapes = {n: L.pupil_shape(SI.make_named(n), R_FRAC) for n in SI.FIXTURES}
check("every synthetic eye's pupil is read (a dark centre with a clear iris round it)", all(v is not None for v in shapes.values()), shapes)
check("solidity at least 0.99 on all twelve (round, slit, bar, lid, lashes)", all(v and v["solidity"] >= 0.99 for v in shapes.values()), shapes)
check("the limit is 0.97, below every right pupil and above the two defects measured (0.933 and 0.938)", L.PREVIEW_QA_SHAPE == 0.97)
check("the area-equivalent radius follows the drawn pupil: a round one of 0.27 R reads 0.25 to 0.29",
      all(0.25 <= shapes[n]["rp"] <= 0.29 for n in ("blue_round", "green_round", "grey_round")), shapes)
clean = SI.make_named("blue_round")
q_clean = L.preview_qa("suite clean", clean, clean, r_frac=R_FRAC)
check("preview_qa of a right pupil: the reading is in the record, nothing fails, ok", q_clean["pupil_shape"] is not None and q_clean["pupil_shape"] >= 0.99
      and q_clean["fail"] == [] and q_clean["ok"] is True, q_clean)

# ============================================================================================ 2. the blob
section("2. the lab order's blob: a square with an arm and a bay, black spots beside it")


def blob(base):
    """base with its pupil painted over as 215102's restoration drew it (sizes in iris radii, from the lab order's preview)."""
    im = base.copy()
    d = ImageDraw.Draw(im)
    n = im.size[0]
    R = R_FRAC * n
    c = n / 2.0

    def box(x0, y0, x1, y1):
        d.rectangle((c + x0 * R, c + y0 * R, c + x1 * R, c + y1 * R), fill=(4, 4, 6))

    def disc(x, y, r):
        d.ellipse((c + (x - r) * R, c + (y - r) * R, c + (x + r) * R, c + (y + r) * R), fill=(4, 4, 6))
    box(-0.36, -0.30, 0.16, 0.34)            # the square body
    box(0.16, -0.30, 0.40, -0.04)            # its upper right block, and below it a bay of iris
    box(0.16, 0.02, 0.60, 0.06)              # the arm to the right
    for x, y, r in ((0.30, 0.22, 0.07), (0.24, 0.31, 0.05), (0.42, 0.26, 0.05), (0.12, -0.42, 0.035), (0.38, -0.38, 0.03)):
        disc(x, y, r)                        # the spots, two of them joined to the body
    return im


bad = blob(clean)
s_bad = L.pupil_shape(bad, R_FRAC)
check("the blob reads under the limit", s_bad is not None and s_bad["solidity"] < L.PREVIEW_QA_SHAPE, s_bad)
q_bad = L.preview_qa("suite blob", bad, bad, r_frac=R_FRAC)
check("preview_qa fails pupil_shape and only that, and ok is false", q_bad["fail"] == ["pupil_shape"] and q_bad["ok"] is False, q_bad)
check("it is no render check: render_ok stays true and the score is the clean picture's (a second render of the same preview has the same pupil)",
      q_bad["render_ok"] is True and q_bad["score"] == q_clean["score"], (q_bad["render_ok"], q_bad["score"], q_clean["score"]))
check("the eye's record with this preview_qa needs a person's review before it ships (store.needs_review), the clean one does not",
      store.needs_review({"qa": {"ok": True}, "preview": q_bad}) is True and store.needs_review({"qa": {"ok": True}, "preview": q_clean}) is False)
check("pupil_shape is not one of PREVIEW_RENDER_CHECKS (master_eye's re-render rule reads render_ok)", "pupil_shape" not in L.PREVIEW_RENDER_CHECKS)

# ============================================================================================ 3. nothing to read, a fault
section("3. no dark centre, and a fault inside the measure")
flat = Image.new("RGB", (1024, 1024), (120, 110, 90))
check("a picture with no dark centre gives no reading", L.pupil_shape(flat, R_FRAC) is None)
q_flat = L.preview_qa("suite flat", flat, flat, r_frac=R_FRAC)
check("...and preview_qa records None and fails nothing for it", q_flat["pupil_shape"] is None and "pupil_shape" not in q_flat["fail"], q_flat)
with mock.patch.object(L, "pupil_shape", side_effect=RuntimeError("boom")):
    q_err = L.preview_qa("suite fault", clean, clean, r_frac=R_FRAC)
check("a fault inside pupil_shape leaves the reading None and the rest of the QA as it was (no qa_error)",
      q_err["pupil_shape"] is None and q_err["ok"] is True and q_err["fail"] == [], q_err)

# ============================================================================================ 4. the master's size
section("4. a 4096 px master reads as its preview")
big_clean = clean.resize((4096, 4096), Image.BICUBIC)
big_bad = bad.resize((4096, 4096), Image.BICUBIC)
s_bc, s_bb = L.pupil_shape(big_clean, R_FRAC), L.pupil_shape(big_bad, R_FRAC)
check("the 4096 px copies read within 0.01 of the 1024 px ones, on the same side of the limit",
      abs(s_bc["solidity"] - shapes["blue_round"]["solidity"]) <= 0.01 and abs(s_bb["solidity"] - s_bad["solidity"]) <= 0.01
      and s_bb["solidity"] < L.PREVIEW_QA_SHAPE <= s_bc["solidity"], (s_bc, s_bb, s_bad))

# ============================================================================================ LOCAL: the owner's own restorations
SP = os.environ.get("SNAPEYES_SP") or ""
FIX = os.environ.get("SNAPEYES_FIXTURES") or os.path.join(REPO, "suites", "private", "fixtures")
if os.path.isfile(os.path.join(FIX, "enhanced_founder_215102.jpg")):
    section("LOCAL: the owner's restorations (private fixtures, not counted)")
    for name, want_fail in (("founder_215102", True), ("founder_215120", False), ("founder_215208", False), ("sample_ai", False)):
        s = L.pupil_shape(Image.open(os.path.join(FIX, f"enhanced_{name}.jpg")).convert("RGB"), R_FRAC)
        local(f"{name}: {'fails' if want_fail else 'passes'} the shape check", s is not None and (s["solidity"] < L.PREVIEW_QA_SHAPE) == want_fail, s)

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
