# -*- coding: utf-8 -*-
"""Records the golden hashes of the collision family on THIS repository's code (work package WP7B: the seed from the eyes' ids and the plan freeze, decision
C9 step B and C8).

The step A goldens were recorded on the scratch prototype (record_goldens_collision_scratch.py) and prove that the port is verbatim. Step B changed the seed
(the names, the scene key and the bytes of the irises are out of it; the eyes' ids and the plan's seed key are in) and the place of the pixel decisions (one
pass on a copy of the canonical scene, which a plan can freeze), which no scratch code has, so the new goldens can only be recorded here, on purpose, once,
and reviewed (diff_goldens_collision.py):

    set SNAPEYES_CALIB=<the folder of the calibration restorations>       (only for --real)
    python scripts/styles_tests/record_goldens_collision_repo.py [--sizes 512 1024 4096] [--designs infinity kiss ...] [--fresh]
    python scripts/styles_tests/record_goldens_collision_repo.py --real

It runs collision_cases.cases() on synthetic irises (synth_iris) through api/_lib/styles/collision.render (the seed made from the eyes' ids, which the Iris
class defaults to the first 16 hex digits of the sha256 of the bytes it was made from, and the default seed key of the design) and writes
data/collision_goldens.json: the hash of every picture, the facts of its choices, the seed and the frozen decisions it made. The step A recording is kept as it
was in data/stepA/ and test_goldens_collision.py replays it too, with the old seed (opts seed_mode legacy): that replay is byte for byte equal, which proves
that the seed is the ONLY thing step B changed. The golden is exact for this machine class and these pins (numpy 2.4.4, Pillow 12.2.0).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)

TMP = tempfile.mkdtemp(prefix="snapeyes_rec7b_")
os.environ.update({"STORE_LOCAL_DIR": os.path.join(TMP, "store"), "STYLE_PLATE_CACHE": os.path.join(TMP, "cache"), "PYTHONIOENCODING": "utf-8"})
for _k in list(os.environ):
    if _k.startswith("GEMINI"):
        os.environ.pop(_k)                                      # no image model, ever
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.makedirs(os.environ["STORE_LOCAL_DIR"], exist_ok=True)

import numpy as np  # noqa: E402
import PIL  # noqa: E402
import collision_cases as CC  # noqa: E402
from _lib.styles import core as C  # noqa: E402
from _lib.styles import collision as CX  # noqa: E402

DATA = os.path.join(HERE, "data")


def sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()       # a checkout with CRLF line ends hashes as the repository's LF


def write(path, out):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")


def machine():
    return {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}


def render(design, eyes, fmt, size, names, date, bg, clean, opts, layout):
    o = dict(CC.PRODUCTION)
    o.update(opts)
    return CX.render(design, eyes, fmt, size, names, date, bg, clean, o, layout)


def record_real():
    calib = os.environ.get("SNAPEYES_CALIB") or sys.exit("SNAPEYES_CALIB is not set (the folder of the calibration restorations)")
    fixtures = {}
    for n in CC.REAL_EYES:
        with open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb") as f:
            fixtures[n] = f.read()
    irises, out = {}, {"cases": {}}
    for c in CC.real_cases():
        rec = CC.render_case(render, C.Iris, fixtures, c, irises, with_frozen=True)
        out["cases"][c["key"]] = rec
        print(f"{c['key']:52s} {rec['sha'][:12]}  {rec['facts'].get('design_used')}", flush=True)
    out["about"] = ("SHA-256 of the RGB bytes of the real calibration eyes drawn by api/_lib/styles/collision (step B: the seed from the eyes' ids, WP7B) at 1024 px: "
                    "hashes only. The step A recording (scratch code) is in data/stepA/.")
    out["step"] = "B"
    out["machine"] = machine()
    out["eye_files"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    out["stepA_file_sha256"] = sha_file(os.path.join(DATA, "stepA", "collision_goldens_real.json"))
    write(os.path.join(DATA, "collision_goldens_real.json"), out)
    print(f"recorded {len(out['cases'])} real-eye cases")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=[512, 1024, 4096])
    ap.add_argument("--designs", nargs="*", default=["infinity", "kiss", "trio", "family", "chain"])
    ap.add_argument("--real", action="store_true", help="record the real calibration eyes instead (data/collision_goldens_real.json: hashes only)")
    ap.add_argument("--fresh", action="store_true", help="start from an empty file (the default merges into the existing one)")
    a = ap.parse_args()
    try:
        if a.real:
            return record_real()
        fixtures = {n: CC.fixture_bytes(n) for n in CC.fixture_names()}
        dst = os.path.join(DATA, "collision_goldens.json")
        out = {"cases": {}}
        if os.path.exists(dst) and not a.fresh:
            with open(dst, encoding="utf-8") as f:
                out = json.load(f)
        todo = [c for c in CC.cases() if c["size"] in a.sizes and c["design"] in a.designs]
        irises, t_all = {}, time.time()
        for i, c in enumerate(todo, 1):
            t0 = time.time()
            rec = CC.render_case(render, C.Iris, fixtures, c, irises, with_frozen=True)
            out["cases"][c["key"]] = rec
            print(f"[{i}/{len(todo)}] {c['key']:56s} {rec['sha'][:12]}  {time.time() - t0:6.1f} s", flush=True)
            if c["size"] >= 2048:
                irises.clear()                                              # a 4096 grade is large: let go of it before the next
        out["about"] = ("SHA-256 of the RGB bytes of collision_cases.cases() rendered on api/_lib/styles/collision (step B of the seed change and the plan freeze, WP7B: "
                        "the seed from the eyes' ids and the default seed key of the design; the pixel decisions made once on a copy of the canonical scene and recorded in "
                        "frozen), synthetic irises of synth_iris, the production switches. The step A recording (the scratch code, the prototype's seed) is kept in "
                        "data/stepA/ and replayed with the old seed.")
        out["step"] = "B"
        out["machine"] = machine()
        out["fixtures"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
        out["retouched_plates"] = ["P-CX-JET__medium_left_b75__pro4K__t2", "P-CX-JET__wide_right_b75__pro4K__t1"]
        out["stepA_file_sha256"] = sha_file(os.path.join(DATA, "stepA", "collision_goldens.json"))
        write(dst, out)
        print(f"recorded {len(todo)} cases ({len(out['cases'])} in the file) to {dst} in {time.time() - t_all:.0f} s")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
