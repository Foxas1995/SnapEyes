# -*- coding: utf-8 -*-
"""Records what the SCRATCH gates and pupil analysis say about the synthetic fixtures of synth_iris.py (the calibrated rule sets
cx_kit.gate, the lid rule of collision, chain and family, and uni_gate.gate, the fill rule of Universe), with the hash of every
fixture. Run once in the scratch tree, never by the suites:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/record_synth_verdicts.py

Writes data/synth_verdicts.json. test_engine_core.py compares the fixtures it regenerates (hash), the class and the lid rule it replays
on the ported core (the rule is 20 lines of core functions: replayed verbatim there) with this record, and checks the acceptance of the
generator: every clean fixture passes both rule sets, every failing one fails the lid rule.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
sys.path.insert(0, HERE)
sys.path.insert(0, Y3)
sys.path.insert(0, os.path.join(Y3, "designs"))

import synth_iris as SI  # noqa: E402
from fx import core as C  # noqa: E402
import cx_kit as K  # noqa: E402
import cx_pupil as PUP  # noqa: E402
import uni_gate as UG  # noqa: E402

rows = {}
for name in SI.FIXTURES:
    raw = SI.png_bytes(name)
    ir = C.Iris(raw, name)
    g = K.gate(ir)
    u = UG.gate(ir)
    p = PUP.analyse(C._tight(ir.graded(C.REF_SIDE))[0])
    rows[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "class": ir.stats["class"], "stats": ir.stats,
                  "lid": {"ok": bool(g["ok"]), "lid70": g["lid70"], "lid88": g["lid88"], "outlier_bins": g["outlier_bins"], "maxdev70": g["maxdev70"]},
                  "fill": {"ok": bool(u["ok"]), "run18": u["run18"], "n_step": u["n_step"], "catch": u["catch"]},
                  "pupil": (p.get("cls") if isinstance(p, dict) else getattr(p, "cls", None))}
dst = os.path.join(HERE, "data", "synth_verdicts.json")
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"about": "verdicts of the scratch cx_kit.gate (lid rule), uni_gate.gate (fill rule) and cx_pupil.analyse on the synthetic fixtures",
               "fixtures": rows}, f, indent=1, sort_keys=True)
    f.write("\n")
print("recorded", len(rows), "fixtures to", dst)
