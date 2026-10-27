# -*- coding: utf-8 -*-
"""Records the golden pictures of the light family (api/_lib/styles/lumen) into data/lumen_goldens.json: the SHA-256 of the RGB pixels of every case
of lumen_cases.py, its size, colour class, seed and facts, the fixtures' hashes and the machine (numpy and Pillow versions). test_lumen.py replays them.

    python scripts/styles_tests/record_goldens_lumen.py [--check]     (SNAPEYES_REPO: the checkout; default the one this file lives in)

A golden is exact for one machine class and the pins of requirements.txt. Recording again is a reviewed change: a new picture of a look needs the
owner's eye on its board first, and data/engine_v.json then records the new hash of this file (python scripts/styles_tests/test_steps.py --record-engine-v)."""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "api"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import PIL  # noqa: E402
import synth_iris as SI  # noqa: E402
import lumen_cases as LC  # noqa: E402
from _lib.styles import core as C  # noqa: E402
from _lib.styles import lumen as LU  # noqa: E402
C.IRIS_FINISH = False   # 2026-10-27: the goldens pin the engine UNDER the iris finish (test_lumen.py replays them so; test_iris_finish.py checks the finish)

OUT = os.path.join(HERE, "data", "lumen_goldens.json")


def main(argv):
    fixtures = {n: SI.png_bytes(n) for n in LC.FIXTURE_BASE}
    irises = {}
    rec = {}
    for c in LC.cases():
        rec[c["key"]] = LC.render_case(LU.render, C.Iris, fixtures, c, irises)
        if c["size"] >= 2048:
            irises.clear()
        print(c["key"], rec[c["key"]]["sha"][:12], flush=True)
    out = {"family": "lumen", "machine": {"numpy": np.__version__, "pillow": PIL.__version__},
           "fixtures": {n: hashlib.sha256(b).hexdigest() for n, b in fixtures.items()}, "cases": rec}
    if "--check" in argv:
        old = json.load(open(OUT, encoding="utf-8"))
        bad = [k for k in rec if old["cases"].get(k) != rec[k]]
        print("differ:", bad)
        return 1 if bad else 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print("recorded", OUT, len(rec), "cases")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
