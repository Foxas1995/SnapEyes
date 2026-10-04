# -*- coding: utf-8 -*-
"""Records the golden hashes of the engine core on the SCRATCH prototype (the code the owner-approved boards were made with).
Run once, in the scratch tree, never by the suites:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/record_core_goldens.py

It imports fx.core, fx.layouts and designs.singles_kit from that folder (which puts the repo engine of the main checkout on its path,
as the prototype always did), runs core_cases.run_cases on synthetic irises (synth_iris), and writes data/core_goldens.json: the
hash of every case, with the machine it was made on. test_engine_core.py replays the same cases on api/_lib/styles/ and compares.
A golden is exact for this machine class and these pins (the sine and exponential of float32 take other SIMD paths on other CPUs):
a mismatch on another machine means recording again on the scratch code there, not changing the port.
"""
from __future__ import annotations

import json
import os
import platform
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
sys.path.insert(0, HERE)
sys.path.insert(0, Y3)
sys.path.insert(0, os.path.join(Y3, "designs"))

import numpy as np  # noqa: E402
import PIL  # noqa: E402
import core_cases as CC  # noqa: E402
import synth_iris as SI  # noqa: E402
from fx import core as C  # noqa: E402
from fx import layouts as LY  # noqa: E402
from designs import singles_kit as K  # noqa: E402

fixtures = {n: SI.png_bytes(n) for n in CC.IRIS_FIXTURES}
cases = CC.run_cases(C, LY, K.draw_names, fixtures)
out = {"about": "SHA-256 of the results of core_cases.run_cases on the scratch fx.core, fx.layouts and singles_kit.draw_names",
       "machine": {"python": platform.python_version(), "numpy": np.__version__, "pillow": PIL.__version__, "platform": platform.platform()},
       "fixtures": {n: __import__("hashlib").sha256(fixtures[n]).hexdigest() for n in fixtures},
       "cases": cases}
dst = os.path.join(HERE, "data", "core_goldens.json")
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, indent=1, sort_keys=True)
    f.write("\n")
print(f"recorded {len(cases)} cases to {dst}")
