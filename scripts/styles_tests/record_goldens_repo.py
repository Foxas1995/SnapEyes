# -*- coding: utf-8 -*-
"""Records the golden hashes of the singles family on THIS repository's code (work package WP5B: the seed change, decision C9 step B).

The step A goldens were recorded on the scratch prototype (record_goldens_scratch.py) and prove that the port is verbatim. Step B changed the seed,
which no scratch code has, so the new goldens can only be recorded here, on purpose, once, and reviewed:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>        (only for the 4096 px pictures of the plate styles: their 4K plates)
    set SNAPEYES_CALIB=<the folder of the calibration restorations>         (only for --real)
    python scripts/styles_tests/record_goldens_repo.py [--sizes 512 1024 4096] [--designs powder gold ...] [--fresh]
    python scripts/styles_tests/record_goldens_repo.py --real

It runs singles_cases.cases() on synthetic irises (synth_iris) through api/_lib/styles/singles (the seed made from the eye id and the plan's seed key,
seeds.py) and writes data/singles_goldens.json: the hash of every picture, the plate picks, the seed. The step A recording is kept as it was in
data/stepA/ and test_goldens_singles.py replays it too, with the old seed (opts seed_mode "legacy"): that replay is byte for byte equal, which proves
that the seed is the ONLY thing step B changed. The golden is exact for this machine class and these pins (numpy 2.4.4, Pillow 12.2.0).

The 4K plates a 4096 px picture of a plate style draws from live in private storage; for the recording they are copied from the scratch tree's own
plate folders into a local store folder (scripts/upload_plates.py, sha256 checked against the plate registry), exactly as the suite's LOCAL lines do.
Memory: a 4096 px render peaks near 900 MB; the cases run one after the other in one process.
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

TMP = tempfile.mkdtemp(prefix="snapeyes_rec5b_")
os.environ.update({"STORE_LOCAL_DIR": os.path.join(TMP, "store"), "STYLE_PLATE_CACHE": os.path.join(TMP, "cache"), "PYTHONIOENCODING": "utf-8"})
for _k in list(os.environ):
    if _k.startswith("GEMINI"):
        os.environ.pop(_k)                                      # no image model, ever
os.makedirs(os.environ["STORE_LOCAL_DIR"], exist_ok=True)

import numpy as np  # noqa: E402
import PIL  # noqa: E402
import synth_iris as SI  # noqa: E402
import singles_cases as SC  # noqa: E402
from _lib import store  # noqa: E402
from _lib.styles import core as C  # noqa: E402
from _lib.styles import plates as PL  # noqa: E402
from _lib.styles import singles as S  # noqa: E402

DATA = os.path.join(HERE, "data")


def sha_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"
", b"
")).hexdigest()       # a checkout with CRLF line ends hashes as the repository's LF


def render(d, e, f, s, n, dt):
    return S.render(d, e, f, s, n, dt)


def write(path, out):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")


def machine():
    return {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()}


def load_4k_plates(ids):
    """The 4K files of these plates into the local store, from the scratch tree (the plate workflow's folders), sha256 checked."""
    y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set: the 4K plates of the plate styles come from the scratch tree")
    import upload_plates as UP
    from _lib import plates_registry as REG
    table = REG.PLATES_REGISTRY["plates"]
    y2 = os.path.join(os.path.dirname(os.path.abspath(y3)), "wave-y2", "plates")
    rows = UP.plan({i: table[i] for i in ids}, {table[i]["family"] for i in ids}, UP.sources(y2, y3))
    tot = UP.run(rows, store, True, out=lambda m: None)
    if tot["bad_source"] or tot["wrong"] or tot["uploaded"] + tot["present"] != len(ids):
        sys.exit(f"the 4K plates are not all there: {tot}")
    print(f"   {len(ids)} 4K plates in the local store", flush=True)


def record_real(fresh):
    calib = os.environ.get("SNAPEYES_CALIB") or sys.exit("SNAPEYES_CALIB is not set (the folder of the calibration restorations)")
    fixtures = {}
    for n in SC.REAL_EYES:
        with open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb") as f:
            fixtures[n] = f.read()
    irises, out = {}, {"cases": {}}
    for c in SC.real_cases():
        rec = SC.render_case(render, C.Iris, fixtures, c, irises)
        out["cases"][c["key"]] = rec
        print(f"{c['key']:40s} {rec['sha'][:12]}  {rec['cls']}", flush=True)
    out["about"] = ("SHA-256 of the RGB bytes of the real calibration eyes drawn by api/_lib/styles/singles (step B: the seed from the eye id, WP5B; "
                    "Celestial Gold = variant A) at 1024 px: hashes only. The step A recording (scratch code) is in data/stepA/.")
    out["step"] = "B"
    out["machine"] = machine()
    out["eye_files"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
    out["stepA_file_sha256"] = sha_file(os.path.join(DATA, "stepA", "singles_goldens_real.json"))
    write(os.path.join(DATA, "singles_goldens_real.json"), out)
    print(f"recorded {len(out['cases'])} real-eye cases")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="*", default=list(SC.SIZES))
    ap.add_argument("--designs", nargs="*", default=list(SC.DESIGNS))
    ap.add_argument("--real", action="store_true", help="record the real calibration eyes instead (data/singles_goldens_real.json: hashes only)")
    ap.add_argument("--fresh", action="store_true", help="start from an empty file (the default merges into the existing one)")
    a = ap.parse_args()
    try:
        if a.real:
            return record_real(a.fresh)
        fixtures = {n: SI.png_bytes(n) for n in SC.FIXTURE_BASE}
        dst = os.path.join(DATA, "singles_goldens.json")
        out = {"cases": {}}
        if os.path.exists(dst) and not a.fresh:
            with open(dst, encoding="utf-8") as f:
                out = json.load(f)
        todo = [c for c in SC.cases() if c["size"] in a.sizes and c["design"] in a.designs]
        # the 4K plates the 4096 px pictures of the plate styles draw from: the plate a picture picks does not depend on its size, so they are the
        # ones its 1024 px twin picked (recorded first: the sizes run smallest first)
        irises, t_all = {}, time.time()
        planned = False
        for i, c in enumerate(todo, 1):
            if SC.needs_4k(c) and not planned:
                twins = [out["cases"].get(SC.case_key(x["design"], x["eye"], "1:1", 1024)) for x in todo if SC.needs_4k(x)]
                if not all(twins):
                    sys.exit("record the 512 and 1024 px cases first: the 4096 px ones read the plates their 1024 px twins picked")
                need = set()
                for tw in twins:
                    for v in tw["facts"].values():
                        need |= {v[x] for x in ("plate", "flame_plate", "water_plate") if x in v}
                load_4k_plates(sorted(need))
                planned = True
            t0 = time.time()
            rec = SC.render_case(render, C.Iris, fixtures, c, irises)
            if SC.needs_4k(c):
                twin = out["cases"][SC.case_key(c["design"], c["eye"], "1:1", 1024)]
                pick = lambda r: {k: {f: v[f] for f in ("plate", "flame_plate", "water_plate", "liquid") if f in v} for k, v in r["facts"].items()}
                if pick(rec) != pick(twin) or rec["seed"] != twin["seed"]:
                    sys.exit(f"{c['key']}: the 4096 px picture drew another seed or other plates than its 1024 px twin: {pick(rec)} / {pick(twin)}")
            out["cases"][c["key"]] = rec
            print(f"[{i}/{len(todo)}] {c['key']:44s} {rec['sha'][:12]}  {time.time() - t0:6.1f} s", flush=True)
            if c["size"] >= 2048:
                irises.clear()
                PL.clear_memory()
        out["about"] = ("SHA-256 of the RGB bytes of singles_cases.cases() rendered on api/_lib/styles/singles (step B of the seed change, WP5B: the seed from the "
                        "eye id and the plan's seed key; Celestial Gold = variant A), synthetic irises of synth_iris. The step A recording (scratch code, "
                        "the prototype's seed) is kept in data/stepA/ and replayed with the old seed.")
        out["step"] = "B"
        out["machine"] = machine()
        out["fixtures"] = {n: hashlib.sha256(fixtures[n]).hexdigest() for n in fixtures}
        out["stepA_file_sha256"] = sha_file(os.path.join(DATA, "stepA", "singles_goldens.json"))
        write(dst, out)
        print(f"recorded {len(todo)} cases ({len(out['cases'])} in the file) to {dst} in {time.time() - t_all:.0f} s")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
