# -*- coding: utf-8 -*-
"""Records the golden hashes of the singles family on the SCRATCH prototype (the code the owner-approved boards were made with). Run once, in
the scratch tree, never by the suites:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/record_goldens_scratch.py [--sizes 512 1024 4096] [--designs powder gold ...] [--family singles]

It imports fx.core and designs.singles from that folder (which puts the repo engine of the main checkout on its path, as the prototype always
did), swaps Celestial Gold for the owner-approved variant A (wave-cg2/A/cg_a.py next to it: the old design is not what ships), runs
singles_cases.cases() on synthetic irises (synth_iris) and merges the result into data/singles_goldens.json: the hash of every picture, the
facts of its plate picks, the machine and the hashes of the scratch sources it ran. test_goldens_singles.py replays the same cases on
api/_lib/styles/singles and compares. A golden is exact for this machine class and these pins (numpy 2.4.4, Pillow 12.2.0: the sine and
exponential of float32 take other SIMD paths on other CPUs, and Pillow's resampling and fonts move): a mismatch on another machine means
recording again on the scratch code there, never changing the port.

The 4096 px pictures of the plate styles (Powder Burst, Splash, Elements) are drawn from the 4K plates of the plate workflow, which the scratch
registry reads from wave-y2. Memory: a 4096 px render peaks near 900 MB; the cases run one after the other in one process.
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
import singles_cases as SC  # noqa: E402
from fx import core as C  # noqa: E402
from designs import singles as S  # noqa: E402
from designs import singles_kit as K  # noqa: E402
from designs import singles_matter as _M  # noqa: E402,F401  (imported now, from wave-y3: cg_a.py puts wave-cg2/base first on the path)

CG_A = os.path.join(SCRATCH, "wave-cg2", "A", "cg_a.py")


def load_gold_a():
    """The effect function of Celestial Gold variant A, imported from its file. wave-cg2/A/cg_a.py puts its own copy of the core on the path first;
    fx.core and designs.singles_kit are already imported from wave-y3 here (the copy is byte identical but for a path), so those are used."""
    import importlib.util
    for name in S.NAMES:
        if name != "gold":
            S._load(name)                                                   # every other design is imported from wave-y3 before cg_a.py touches the path
    base = os.path.join(SCRATCH, "wave-cg2", "base")
    spec = importlib.util.spec_from_file_location("cg_a", CG_A)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path[:] = [p for p in sys.path if os.path.normpath(p) != os.path.normpath(base)]
    return mod.fx_gold_a


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def record_real():
    """The real-eye goldens: the owner's restorations of the calibration set (wave-g/live/out, or SNAPEYES_CALIB), 1024 px, every design. The
    eyes are never committed; the file holds the hash of each eye file and of each picture, nothing that shows an iris."""
    calib = os.environ.get("SNAPEYES_CALIB") or os.path.join(SCRATCH, "wave-g", "live", "out")
    fixtures = {}
    for n in SC.REAL_EYES:
        with open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb") as f:
            fixtures[n] = f.read()
    irises, out = {}, {"cases": {}}
    for c in SC.real_cases():
        rec = SC.render_case(lambda d, e, f, s, nm, dt: S.render(d, e, f, s, nm, dt), C.Iris, fixtures, c, irises)
        out["cases"][c["key"]] = rec
        print(f"{c['key']:40s} {rec['sha'][:12]}  {rec['cls']}", flush=True)
    out["about"] = "SHA-256 of the RGB bytes of the real calibration eyes drawn by the scratch designs (Celestial Gold = variant A) at 1024 px: hashes only"
    out["machine"] = {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}
    out["eye_files"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    dst = os.path.join(HERE, "data", "singles_goldens_real.json")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"recorded {len(out['cases'])} real-eye cases to {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="singles", choices=["singles"])
    ap.add_argument("--sizes", type=int, nargs="*", default=list(SC.SIZES))
    ap.add_argument("--designs", nargs="*", default=list(SC.DESIGNS))
    ap.add_argument("--real", action="store_true", help="record the real calibration eyes instead (data/singles_goldens_real.json: hashes only)")
    a = ap.parse_args()
    S.DESIGNS["gold"] = {"fx": load_gold_a(), "bg": "#0B0D14"}            # the variant that ships: _load("gold") finds it ready
    if a.real:
        return record_real()
    fixtures = {n: SI.png_bytes(n) for n in SC.FIXTURE_BASE}
    dst = os.path.join(HERE, "data", "singles_goldens.json")
    out = {"cases": {}}
    if os.path.exists(dst):
        with open(dst, encoding="utf-8") as f:
            out = json.load(f)
    todo = [c for c in SC.cases() if c["size"] in a.sizes and c["design"] in a.designs]
    irises = {}
    t_all = time.time()
    for i, c in enumerate(todo, 1):
        t0 = time.time()
        rec = SC.render_case(lambda d, e, f, s, n, dt: S.render(d, e, f, s, n, dt), C.Iris, fixtures, c, irises)
        out["cases"][c["key"]] = rec
        print(f"[{i}/{len(todo)}] {c['key']:44s} {rec['sha'][:12]}  {time.time() - t0:6.1f} s", flush=True)
        if c["size"] >= 2048:
            irises.clear()                                                  # a 4096 grade is large: let go of it before the next
    out["about"] = ("SHA-256 of the RGB bytes of singles_cases.cases() rendered on the scratch designs/singles.py (fx.core, singles_kit, the six "
                    "designs; Celestial Gold = variant A, wave-cg2/A/cg_a.py), synthetic irises of synth_iris")
    out["machine"] = {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}
    out["fixtures"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    out["scratch_sources"] = {n: sha(os.path.join(Y3, p)) for n, p in (
        ("core", "fx/core.py"), ("layouts", "fx/layouts.py"), ("kit", "designs/singles_kit.py"), ("matter", "designs/singles_matter.py"),
        ("singles", "designs/singles.py"), ("powder", "designs/singles_powder.py"), ("splash", "designs/singles_splash.py"),
        ("elements", "designs/singles_elements.py"), ("radiance", "designs/singles_radiance.py"))}
    out["scratch_sources"]["gold_a"] = sha(CG_A)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"recorded {len(todo)} cases ({len(out['cases'])} in the file) to {dst} in {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
