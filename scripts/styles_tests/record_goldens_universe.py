# -*- coding: utf-8 -*-
"""Records the golden hashes of the universe family on the SCRATCH prototype (the code the approved boards were made with). Run once, in the scratch
tree, never by the suites:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/record_goldens_universe.py [--sizes 512 1024 4096] [--looks vortex ...] [--only KEYPART ...] [--real]

It imports fx.core and designs.universe from that folder (which puts the repo engine of the main checkout on its path, as the prototype always did),
runs universe_cases.cases() on synthetic irises (synth_iris) and writes data/universe_goldens.json: the hash of every picture, the facts of its
render (the plate picks, the layout, the contacts), the machine and the hashes of the scratch sources it ran. test_goldens_universe.py replays the same
cases on api/_lib/styles/universe and compares. This is the STEP A recording: the prototype's own pictures, seeded the prototype's way (the bytes of the
irises). WP8B changes the seed and records its own file (the engine record, data/engine_v.json, holds the hashes of these until then).

A golden is exact for this machine class and these pins (numpy 2.4.4, Pillow 12.2.0: the sine and exponential of float32 take other SIMD paths on other
CPUs, and Pillow's resampling and fonts move): a mismatch on another machine means recording again on the scratch code there, never changing the port.
Memory: a 4096 px render peaks near 700 MB; the cases run one after the other in one process.

--real records the owner's calibration eyes (SNAPEYES_CALIB, the folder of the *_2_enhanced.jpg restorations) instead: Echo, Vortex, Deep Field and
Starfield on four eyes at 1024 px, a pair and a trio at 512 px: hashes only (data/universe_goldens_real.json); the eyes are never committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
SCRATCH = os.path.dirname(os.path.abspath(Y3))
sys.path.insert(0, HERE)
sys.path.insert(0, Y3)

import numpy as np  # noqa: E402
import PIL  # noqa: E402
import synth_iris as SI  # noqa: E402
import universe_cases as UC  # noqa: E402
from fx import core as C  # noqa: E402
from designs import universe as U  # noqa: E402

SOURCES = ("fx/core.py", "designs/universe.py", "designs/uni_layout.py", "designs/uni_common.py", "designs/uni_engine.py", "designs/uni_comp.py",
           "designs/uni_fill.py", "designs/uni_flakes.py", "designs/uni_grains.py", "designs/uni_matter.py", "designs/uni_plates.py", "designs/uni_looks.py",
           "designs/uni_plate_looks.py", "designs/uni_pupil.py", "designs/uni_gate.py")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def scratch_render(look, irises, size, aspect, names, date, opts):
    return U.render(look, irises, size, aspect, names, date, opts, want_scene=True)


def record_real():
    """The real-eye goldens: the owner's restorations of the calibration set, hashes only."""
    calib = os.environ.get("SNAPEYES_CALIB") or os.path.join(SCRATCH, "wave-g", "live", "out")
    names = UC.REAL_EYES
    fixtures = {}
    for n in names:
        with open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb") as f:
            fixtures[n] = f.read()
    irises, out = {}, {"cases": {}}
    for c in UC.real_cases():
        rec = UC.render_case(scratch_render, C.Iris, fixtures, c, irises)
        out["cases"][c["key"]] = rec
        print(f"{c['key']:60s} {rec['sha'][:12]}  {rec['cls']}", flush=True)
    out["about"] = "SHA-256 of the RGB bytes of the real calibration eyes drawn by the scratch universe family: hashes only"
    out["machine"] = {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}
    out["eye_files"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    dst = os.path.join(HERE, "data", "universe_goldens_real.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"recorded {len(out['cases'])} real-eye cases to {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=[512, 1024, 2048, 4096])
    ap.add_argument("--looks", nargs="*", default=list(UC.LOOKS))
    ap.add_argument("--only", nargs="*", default=None, help="record only the cases whose key contains one of these texts")
    ap.add_argument("--real", action="store_true", help="record the real calibration eyes instead (data/universe_goldens_real.json: hashes only)")
    a = ap.parse_args()
    if a.real:
        return record_real()
    fixtures = {n: SI.png_bytes(n) for n in UC.FIXTURE_BASE}
    dst = os.path.join(HERE, "data", "universe_goldens.json")
    out = {"cases": {}}
    if os.path.exists(dst):
        with open(dst, encoding="utf-8") as f:
            out = json.load(f)
    todo = [c for c in UC.cases() if c["size"] in a.sizes and c["look"] in a.looks and (a.only is None or any(t in c["key"] for t in a.only))]
    irises = {}
    t_all = time.time()
    for i, c in enumerate(todo, 1):
        t0 = time.time()
        rec = UC.render_case(scratch_render, C.Iris, fixtures, c, irises)
        out["cases"][c["key"]] = rec
        pl = {k: rec["facts"][k]["lod"] for k in ("plate", "accent_plate") if k in rec["facts"]}
        print(f"[{i}/{len(todo)}] {c['key']:64s} {rec['sha'][:12]}  {time.time() - t0:6.1f} s  {pl or ''}", flush=True)
        if c["size"] >= 2048:
            irises.clear()                                                  # a 4096 grade is large: let go of it before the next
    out["about"] = ("SHA-256 of the RGB bytes of universe_cases.cases() rendered on the scratch designs/universe.py (fx.core, uni_*), synthetic irises of synth_iris; "
                    "step A: the prototype's own seed")
    out["machine"] = {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}
    out["fixtures"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    out["scratch_sources"] = {p: sha(os.path.join(Y3, p)) for p in SOURCES}
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"recorded {len(todo)} cases ({len(out['cases'])} in the file) to {dst} in {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
