# -*- coding: utf-8 -*-
"""Records the golden hashes of the universe family on THIS repository's code (work package WP8B: the seed from the eyes' ids and the plan's seed key, decision
C9 step B).

The step A goldens were recorded on the scratch prototype (record_goldens_universe.py) and prove that the port is verbatim. Step B changed the seed (the bytes of
the irises, the look and the layout key are out of it; the eyes' ids and the plan's seed key are in), the per eye seeds (derived from it) and the plates version
every pick takes, which no scratch code has, so the new goldens can only be recorded here, on purpose, once, and reviewed (diff_goldens_universe.py):

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder>                          (only for the pictures that draw from a 4K plate: they are put into a local store first)
    set SNAPEYES_CALIB=<the folder of the calibration restorations>       (only for --real)
    python scripts/styles_tests/record_goldens_universe_repo.py [--sizes 512 1024 2048 4096] [--looks echo vortex ...] [--only KEYPART ...] [--fresh]
    python scripts/styles_tests/record_goldens_universe_repo.py --real

It runs universe_cases.cases() on synthetic irises (synth_iris) through api/_lib/styles/universe.render (the seed made from the eyes' ids, which the Iris class
defaults to the first 16 hex digits of the sha256 of the bytes it was made from, and the default seed key of the look) and writes data/universe_goldens.json: the
hash of every picture, the seeds and the facts of its choices. The step A recording is kept as it was in data/stepA/ and test_goldens_universe.py replays it too,
with the old seed (opts seed_mode legacy): that replay is byte for byte equal, which proves that the seed and the plates version are the ONLY things step B
changed. The golden is exact for this machine class and these pins (numpy 2.4.4, Pillow 12.2.0).
No image model, no network: a local store holds the 4K plates the pictures need (read from the scratch tree, sha256 equal to the registry's).

Every picture is drawn from a FRESH Iris (the step A recording shared one per eye between cases, as the scratch recorder did). The family caches the extended source of an
eye on the Iris under a key rounded to a hundredth of the radius it was asked for, and the first caller's array size wins: an eye that was drawn in another look first can have an
extension two pixels larger, and 11 pixels of a pair differ by one level (found by WP8B: `echo.blue_round+dark_brown_round.4:5.512` after a Vortex of the same eye). A request draws
on fresh Iris objects, so a golden made the same way does not depend on the order the cases ran in.
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

TMP = tempfile.mkdtemp(prefix="snapeyes_rec8b_")
os.environ.update({"STORE_LOCAL_DIR": os.path.join(TMP, "store"), "STYLE_PLATE_CACHE": os.path.join(TMP, "cache"), "PYTHONIOENCODING": "utf-8"})
for _k in list(os.environ):
    if _k.startswith("GEMINI"):
        os.environ.pop(_k)                                      # no image model, ever
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
os.makedirs(os.environ["STORE_LOCAL_DIR"], exist_ok=True)

import numpy as np  # noqa: E402
import PIL  # noqa: E402
import synth_iris as SI  # noqa: E402
import universe_cases as UC  # noqa: E402
from _lib import store  # noqa: E402
from _lib.styles import core as C  # noqa: E402
from _lib.styles import plates as PL  # noqa: E402
from _lib.styles import universe as U  # noqa: E402
from _lib.styles.universe import plates as UPL  # noqa: E402

DATA = os.path.join(HERE, "data")
Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or ""


def sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()       # a checkout with CRLF line ends hashes as the repository's LF


def write(path, out):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")


def machine():
    return {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}


def stock_plate(plate_id):
    """Put one 4K plate into the local store from the scratch tree (sha256 checked against the registry): what the pictures that draw from a 4K plate need."""
    if not Y3:
        sys.exit(f"the picture needs the 4K plate {plate_id}: set SNAPEYES_SCRATCH_Y3 (the wave-y3 folder) so that it can be put into the local store")
    import upload_plates as UP
    from _lib import plates_registry as REG
    table = REG.PLATES_REGISTRY["plates"]
    y2 = os.path.join(os.path.dirname(os.path.abspath(Y3)), "wave-y2", "plates")
    rows = UP.plan({plate_id: table[plate_id]}, {table[plate_id]["family"]}, UP.sources(y2, Y3))
    tot = UP.run(rows, store, True, out=lambda m: None)
    if tot["bad_source"] or tot["wrong"]:
        sys.exit(f"the 4K plate {plate_id} could not be stocked: {tot}")
    PL.clear_memory()
    UPL._IMG.clear()


def render(look, irises, size, aspect, names, date, opts):
    for _ in range(6):                                          # a plate that is not in the local store yet is stocked from the scratch tree, then the picture is drawn again
        try:
            return U.render(look, irises, size, aspect, names, date, opts, want_scene=True)
        except PL.PlateUnavailable as e:
            stock_plate(e.plate_id)
    raise RuntimeError("more plates than a picture can need")


def record_real():
    calib = os.environ.get("SNAPEYES_CALIB") or sys.exit("SNAPEYES_CALIB is not set (the folder of the calibration restorations)")
    fixtures = {}
    for n in UC.REAL_EYES:
        with open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb") as f:
            fixtures[n] = f.read()
    out = {"cases": {}}
    for c in UC.real_cases():
        rec = UC.render_case(render, C.Iris, fixtures, c)               # a fresh Iris per picture (see the module text: a shared one carries state from picture to picture)
        out["cases"][c["key"]] = rec
        print(f"{c['key']:60s} {rec['sha'][:12]}  {rec['cls']}", flush=True)
    out["about"] = ("SHA-256 of the RGB bytes of the real calibration eyes drawn by api/_lib/styles/universe (step B: the seed from the eyes' ids, WP8B): hashes only. "
                    "The step A recording (scratch code) is in data/stepA/.")
    out["step"] = "B"
    out["machine"] = machine()
    out["eye_files"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    out["stepA_file_sha256"] = sha_file(os.path.join(DATA, "stepA", "universe_goldens_real.json"))
    write(os.path.join(DATA, "universe_goldens_real.json"), out)
    print(f"recorded {len(out['cases'])} real-eye cases")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=[512, 1024, 2048, 4096])
    ap.add_argument("--looks", nargs="*", default=list(UC.LOOKS))
    ap.add_argument("--only", nargs="*", default=None, help="record only the cases whose key contains one of these texts")
    ap.add_argument("--real", action="store_true", help="record the real calibration eyes instead (data/universe_goldens_real.json: hashes only)")
    ap.add_argument("--fresh", action="store_true", help="start from an empty file (the default merges into the existing one)")
    a = ap.parse_args()
    try:
        if a.real:
            return record_real()
        fixtures = {n: SI.png_bytes(n) for n in UC.FIXTURE_BASE}
        dst = os.path.join(DATA, "universe_goldens.json")
        out = {"cases": {}}
        if os.path.exists(dst) and not a.fresh:
            with open(dst, encoding="utf-8") as f:
                out = json.load(f)
        todo = [c for c in UC.cases() if c["size"] in a.sizes and c["look"] in a.looks and (a.only is None or any(t in c["key"] for t in a.only))]
        t_all = time.time()
        for i, c in enumerate(todo, 1):
            t0 = time.time()
            rec = UC.render_case(render, C.Iris, fixtures, c)               # a fresh Iris per picture (see the module text)
            out["cases"][c["key"]] = rec
            pl = {k: rec["facts"][k]["lod"] for k in ("plate", "accent_plate") if k in rec["facts"]}
            print(f"[{i}/{len(todo)}] {c['key']:64s} {rec['sha'][:12]}  {time.time() - t0:6.1f} s  {pl or ''}", flush=True)
        out["about"] = ("SHA-256 of the RGB bytes of universe_cases.cases() rendered on api/_lib/styles/universe (step B of the seed change, WP8B: the seed from the eyes' ids "
                        "and the default seed key of the look, the per eye seeds derived from it, the plates version in every pick), synthetic irises of synth_iris. "
                        "The step A recording (the scratch code, the prototype's seed) is kept in data/stepA/ and replayed with the old seed.")
        out["step"] = "B"
        out["machine"] = machine()
        out["fixtures"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
        out["stepA_file_sha256"] = sha_file(os.path.join(DATA, "stepA", "universe_goldens.json"))
        write(dst, out)
        print(f"recorded {len(todo)} cases ({len(out['cases'])} in the file) to {dst} in {time.time() - t_all:.0f} s")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
