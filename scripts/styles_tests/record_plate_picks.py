# -*- coding: utf-8 -*-
"""Records the plate picks of the plate workflow's REGISTRY (the scratch tree's wave-y2/plates/tools/registry.py) with plate_cases.run_cases.
Run once in the scratch tree, never by the suites:

    set SNAPEYES_SCRATCH_PLATES=<the wave-y2/plates folder of the scratch tree>
    python scripts/styles_tests/record_plate_picks.py

Writes data/plate_picks.json. test_plates.py replays the same cases on api/_lib/styles/plates.py (the baked registry and the bundled 1K files).
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLATES = os.environ.get("SNAPEYES_SCRATCH_PLATES") or sys.exit("SNAPEYES_SCRATCH_PLATES is not set (the wave-y2/plates folder of the scratch tree)")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PLATES, "tools"))

import registry as R  # noqa: E402
import plate_cases as PC  # noqa: E402

cases = PC.run_cases(R)
dst = os.path.join(HERE, "data", "plate_picks.json")
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8", newline="\n") as f:
    json.dump({"about": "results of plate_cases.run_cases on the plate workflow's registry.py (pick, pick_n, plates, Plate.place at the 1K LOD)",
               "cases": cases}, f, indent=1, sort_keys=True)
    f.write("\n")
print(f"recorded {len(cases)} cases to {dst}")
