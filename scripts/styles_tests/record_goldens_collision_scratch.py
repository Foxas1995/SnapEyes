# -*- coding: utf-8 -*-
"""Records the golden hashes of the collision family on the SCRATCH prototype (the DG1 snapshot of the collision code, which the owner-approved seam was made
with). Run once, in the scratch tree, never by the suites:

    set SNAPEYES_SCRATCH_DG1=<the wave-dg1/final folder of the scratch tree>
    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/make_collision_scratch_tree.py <a new folder>          # once
    set SNAPEYES_COLLISION_REC=<that folder>
    python scripts/styles_tests/record_goldens_collision_scratch.py [--sizes 512 1024 4096] [--designs infinity kiss ...] [--real]

It imports fx.core and designs.collision from the recording tree (a copy of the DG1 snapshot with the plate library of the design round next to it: the
DG1 folder itself holds no plates_cx, so a render there draws no JET plate and the notch jets fall back to the parametric fan; the boards the owner
approved had the plates, and the port reads them), runs collision_cases.cases() on synthetic irises (synth_iris) with the production switches and merges
the result into data/collision_goldens.json: the hash of every picture, the facts of its choices, the machine and the hashes of the scratch sources it ran.
test_goldens_collision.py replays the same cases on api/_lib/styles/collision and compares. A golden is exact for this machine class and these pins
(numpy 2.4.4, Pillow 12.2.0: the sine and exponential of float32 take other SIMD paths on other CPUs): a mismatch on another machine means recording again
on the scratch code there, never changing the port.

ONE exception to "the scratch's own plates": the baked plate library retouched two JET plates (a scale bar and a legend of the generator were painted into
the raw files: scripts/bake_plates_registry.py, RETOUCH). The recording takes every plate whose baked fit differs from the scratch's fit (and so its 1K
luminance) from the baked library: exactly those two, and says so. Every other plate is read from the scratch's own raw and LOD files, which is the proof
that the port's plate adapter (api/_lib/styles/collision/jetplates.py) picks, fits and places like the prototype.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))
REC = os.environ.get("SNAPEYES_COLLISION_REC") or sys.exit("SNAPEYES_COLLISION_REC is not set (the recording tree made by make_collision_scratch_tree.py)")
Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
SCRATCH = os.path.dirname(os.path.abspath(Y3))
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, HERE)
sys.path.insert(0, REC)
sys.path.insert(0, os.path.join(REC, "designs"))

import numpy as np  # noqa: E402
import PIL  # noqa: E402
from PIL import Image  # noqa: E402
import collision_cases as CC  # noqa: E402
from fx import core as C  # noqa: E402
import collision as CO  # noqa: E402
import cx_haze as HZ  # noqa: E402
import cx_plates as PL  # noqa: E402

HZ.PLATE_TOOLS = os.path.join(SCRATCH, "wave-y2", "plates", "tools")


def baked_registry():
    """The baked plate library as data (api/_lib/plates_registry.py is a literal: loaded by path, under another name, so that the scratch core's own _lib
    import is left alone)."""
    path = os.path.join(REPO, "api", "_lib", "plates_registry.py")
    spec = importlib.util.spec_from_file_location("baked_plates_registry", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PLATES_REGISTRY["plates"]


def patch_retouched():
    """Take the plates whose baked fit differs from the scratch's from the baked library (see the module text). Returns the list of their ids."""
    baked = baked_registry()
    fits = json.load(open(os.path.join(REC, "plates_cx", "fits.json"), encoding="utf-8"))
    changed = {}
    for pid, rec in baked.items():
        if rec["family"] not in ("P-CX-JET", "P-CX-RIVER") or not rec["usable"] or pid not in fits:
            continue
        s, b = fits[pid], rec["fit"]
        if any(abs(float(s[k]) - float(b[k])) > 1e-9 for k in b if k in s and isinstance(b[k], (int, float)) and not isinstance(b[k], bool)):
            changed[pid] = rec
    lum = {}
    orig_registry, orig_lum = PL.registry, PL._plate_lum

    def registry(fam):
        out = orig_registry(fam)
        for i, p in enumerate(out):
            rec = changed.get(p["key"])
            if rec is not None:
                out[i] = dict(p, **{k: v for k, v in rec["fit"].items() if k in p})
        return out

    def plate_lum(p, need_side):
        rec = changed.get(p["key"])
        if rec is not None and need_side <= 1024 * PL.MAX_UPSCALE:
            if p["key"] not in lum:
                f = os.path.join(REPO, "api", "_assets", "plates", rec["family"], rec["k1"]["file"])
                lum[p["key"]] = np.asarray(Image.open(f).convert("L"), np.float32) / 255.0
            return lum[p["key"]]
        return orig_lum(p, need_side)
    PL.registry, PL._plate_lum = registry, plate_lum
    return sorted(changed)


def scratch_render(design, eyes, fmt, size, names, date, bg, clean, opts, layout):
    o = dict(CC.PRODUCTION)
    o.update(opts)
    return CO.render(design, eyes, fmt=fmt, size=size, names=names or None, date=date or None, bg=bg, clean=clean, opts=o, layout=layout)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def machine():
    return {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}


def record_real(only=None):
    """The real-eye goldens: the owner's restorations of the calibration set (SNAPEYES_CALIB, or wave-g/live/out), 1024 px. Hashes only."""
    calib = os.environ.get("SNAPEYES_CALIB") or os.path.join(SCRATCH, "wave-g", "live", "out")
    fixtures = {}
    for n in CC.REAL_EYES:
        with open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb") as f:
            fixtures[n] = f.read()
    irises, out = {}, {"cases": {}}
    for c in CC.real_cases():
        rec = CC.render_case(scratch_render, C.Iris, fixtures, c, irises)
        out["cases"][c["key"]] = rec
        print(f"{c['key']:52s} {rec['sha'][:12]}  {rec['facts'].get('design_used')}", flush=True)
    out["about"] = "SHA-256 of the RGB bytes of the real calibration eyes drawn by the scratch collision code (DG1 snapshot, production switches) at 1024 px: hashes only"
    out["machine"] = machine()
    out["eye_files"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    dst = os.path.join(HERE, "data", "collision_goldens_real.json")
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"recorded {len(out['cases'])} real-eye cases to {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=[512, 1024, 4096])
    ap.add_argument("--designs", nargs="*", default=["infinity", "kiss", "trio", "family", "chain"])
    ap.add_argument("--real", action="store_true", help="record the real calibration eyes instead (data/collision_goldens_real.json: hashes only)")
    ap.add_argument("--keys", nargs="*", help="only these case keys")
    a = ap.parse_args()
    retouched = patch_retouched()
    print("plates taken from the baked library (retouched):", retouched, flush=True)
    if a.real:
        return record_real()
    fixtures = {n: CC.fixture_bytes(n) for n in CC.fixture_names()}
    dst = os.path.join(HERE, "data", "collision_goldens.json")
    out = {"cases": {}}
    if os.path.exists(dst):
        with open(dst, encoding="utf-8") as f:
            out = json.load(f)
    todo = [c for c in CC.cases() if c["size"] in a.sizes and c["design"] in a.designs and (not a.keys or c["key"] in a.keys)]
    irises = {}
    t_all = time.time()
    for i, c in enumerate(todo, 1):
        t0 = time.time()
        rec = CC.render_case(scratch_render, C.Iris, fixtures, c, irises)
        out["cases"][c["key"]] = rec
        print(f"[{i}/{len(todo)}] {c['key']:56s} {rec['sha'][:12]}  {time.time() - t0:6.1f} s", flush=True)
        if c["size"] >= 2048:
            irises.clear()                                                  # a 4096 grade is large: let go of it before the next
    out["about"] = ("SHA-256 of the RGB bytes of collision_cases.cases() rendered on the scratch collision code (the DG1 snapshot: designs/collision.py with "
                    "fx/collision_comp.py, seam_plan.py, lens_mode.py; the JET, RIVER and cloud plates of the design round), synthetic irises of synth_iris, "
                    "the production switches")
    out["machine"] = machine()
    out["fixtures"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    out["retouched_plates"] = retouched
    out["scratch_sources"] = {n: sha(os.path.join(REC, p)) for n, p in (
        ("core", "fx/core.py"), ("collision", "designs/collision.py"), ("kit", "designs/cx_kit.py"), ("powder", "designs/cx_powder.py"), ("raster", "designs/cx_raster.py"),
        ("extra", "designs/cx_extra.py"), ("fill", "designs/cx_fill.py"), ("haze", "designs/cx_haze.py"), ("plates", "designs/cx_plates.py"),
        ("scenes", "fx/collision_layouts.py"), ("compositor", "fx/collision_comp.py"), ("seam_plan", "fx/seam_plan.py"), ("lens_mode", "fx/lens_mode.py"))}
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"recorded {len(todo)} cases ({len(out['cases'])} in the file) to {dst} in {time.time() - t_all:.0f} s")


if __name__ == "__main__":
    main()
