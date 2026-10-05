# -*- coding: utf-8 -*-
"""Records the goldens of the Reveal's server half on the SCRATCH prototype (the code the owner-approved Reveal was made with). Run once, in the
scratch tree, never by the suites:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/record_reveal_goldens_scratch.py [--real]

It imports designs/presentation.py from that folder (which puts the repo engine of the main checkout on its path, as the prototype always did), runs
reveal_cases.CASES on it and writes data/reveal_goldens.json: for each case the public parameters (the wire dict), the SHA-256 of the prepared
restoration (the eyelid hidden, the pupil crushed: what the display copy is made from) and of the display copy with the watermark on ARCS (the
variant that stays off; its pixels depend on nothing but the engine's words and font, so it can be pinned: the repo tile's pixels belong to
preview.display_image, which another work package changes on purpose, so they are not pinned here). With --real: the owner's calibration eyes
(wave-g/live/out, or SNAPEYES_CALIB): the same, hashes and numbers only, into data/reveal_goldens_real.json; the eyes are never committed.
test_reveal.py replays the same cases on api/_lib/styles/reveal.py and compares. A golden is exact for this machine class and these pins (numpy
2.4.4, Pillow 12.2.0): a mismatch on another machine means recording again on the scratch code there, never changing the port.
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
from PIL import Image  # noqa: E402

import reveal_cases as RC  # noqa: E402
from designs import presentation as P  # noqa: E402

REAL_EYES = ["own215120", "drv_d01", "drv_w04", "drv_w02", "drv_w03", "p05i", "p09f", "drv_w08", "drv_d04", "drv_d05"]


def sha(im):
    return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()


def wire(p):
    """The wire dict as the repo writes it (no private masks, no negative zero), through JSON so that tuples are lists."""
    out = {}
    for k, v in P.public_params(p).items():
        if isinstance(v, (list, tuple)):
            v = [x + 0.0 if isinstance(x, float) else x for x in v]
        elif isinstance(v, float):
            v = v + 0.0
        out[k] = v
    return json.loads(json.dumps(out))


def record(crop, restored, lang_list=("en",)):
    p = P.reveal_params(crop, restored)
    prep = P.prepare_restored(restored, p)
    rec = {"params": wire(p), "prep": sha(prep), "arcs": {lang: sha(P.display_copy(prep, lang, "arcs")) for lang in lang_list}}
    reg = p["_info"]["reg"]
    rec["registration"] = {"spread_r": round(float(reg["spread_r"]), 6), "ncc": round(float(reg["ncc"]), 4), "applied": bool(reg["applied"])}
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    machine = {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "machine": platform.machine(), "system": platform.system()}
    if a.real:
        calib = os.environ.get("SNAPEYES_CALIB") or os.path.join(SCRATCH, "wave-g", "live", "out")
        out = {"cases": {}}
        for n in REAL_EYES:
            t = time.time()
            with open(os.path.join(calib, f"{n}_0_clientcrop.jpg"), "rb") as f:
                crop_bytes = f.read()
            with open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb") as f:
                rest_bytes = f.read()
            import io
            crop = Image.open(io.BytesIO(crop_bytes)).convert("RGB")
            rest = Image.open(io.BytesIO(rest_bytes)).convert("RGB")
            rec = record(crop, rest)
            rec["crop_sha256"] = hashlib.sha256(crop_bytes).hexdigest()
            rec["restored_sha256"] = hashlib.sha256(rest_bytes).hexdigest()
            out["cases"][n] = rec
            print(f"{n:12s} ok {rec['params']['ok']!s:5s} drift {rec['params']['drift']:5.1f} {time.time() - t:5.2f}s", flush=True)
        out["about"] = "Reveal server half on the real calibration eyes, scratch prototype: numbers and SHA-256 only, no image"
        out["machine"] = machine
        path = os.path.join(HERE, "data", "reveal_goldens_real.json")
    else:
        out = {"cases": {}}
        for key in RC.CASES:
            crop, rest = RC.pair(key)
            rec = record(crop, rest, ("en", "lt") if key == "blue_clean" else ("en",))
            out["cases"][key] = rec
            print(f"{key:22s} ok {rec['params']['ok']!s:5s} drift {rec['params']['drift']:5.1f} cls {rec['params']['cls']}", flush=True)
        out["about"] = "Reveal server half on the synthetic cases of reveal_cases.py, scratch prototype (designs/presentation.py)"
        out["machine"] = machine
        path = os.path.join(HERE, "data", "reveal_goldens.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print("wrote", path)


if __name__ == "__main__":
    main()
