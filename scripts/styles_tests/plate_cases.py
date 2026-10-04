# -*- coding: utf-8 -*-
"""The plate pick cases, written once and run twice (as core_cases.py is): record_plate_picks.py runs them on the plate workflow's REGISTRY of the
design rounds (registry.py of the scratch tree, the code the approved boards picked their plates with) and writes the results into
data/plate_picks.json; test_plates.py runs the same function on api/_lib/styles/plates.py and compares. The port is the loader half of that registry;
the pick is min(candidates, key=sha256(seed | family | plate id)), so any plate that a different candidate set (a v2 flame, a soft spiral) let in
would change a result here.

run_cases(M) -> {case: json text}.  M: a module with plates(), pick(), pick_n() and Plate.place(): the scratch registry or styles.plates.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

CLOUD_WHERE = [{}, {"black": ["30", "45", "60"]}, {"black": ["45", "60"]}]
LIQUIDS = ["water_clear", "cognac", "whisky_amber", "tea_olive", "water_teal"]
SEEDS = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55, "seed", "a|b", 12345678901234]


def one(pk):
    return [pk.plate.id, round(pk.rotation_deg, 6), bool(pk.mirror), bool(pk.weak_direction)]


def run_cases(M):
    out = {}
    rows = []
    for w in CLOUD_WHERE:
        for seed in SEEDS:
            for wanted, maxrot in ((None, 45.0), (30.0, 45.0), (90.0, 10.0), (200.0, 45.0), (310.0, 90.0)):
                rows.append(one(M.pick("P-SN-CLOUD", seed, wanted, max_rotation=maxrot, **w)))
    out["cloud.picks"] = json.dumps(rows)
    out["cloud.count"] = str(len(M.plates("P-SN-CLOUD")))
    out["cloud.black45"] = json.dumps([p.id for p in M.plates("P-SN-CLOUD", black="45")])
    out["cloud.exclude"] = json.dumps([one(M.pick("P-SN-CLOUD", s, 60.0, exclude=[M.pick("P-SN-CLOUD", s, 60.0).plate.id], max_rotation=45.0)) for s in SEEDS[:6]])
    rows = []
    for liquid in LIQUIDS:
        for seed in SEEDS[:8]:
            for wanted, maxrot in ((50.0, 30.0), (120.0, 35.0), (None, 30.0)):
                rows.append(one(M.pick("P-SP-CROWN", seed, wanted, max_rotation=maxrot, liquid=liquid)))
    out["crown.picks"] = json.dumps(rows)
    out["crown.count"] = str(len(M.plates("P-SP-CROWN")))
    flame_ex = [p.id for p in M.plates("P-EL-FLAME") if "__v3__" not in p.id]      # the prototype's v3_exclude: empty on the port (the v2 flames are not usable)
    rows = []
    for seed in SEEDS[:10]:
        for wanted in (64.0, 116.0, 88.0):
            rows.append(one(M.pick("P-EL-FLAME", seed, wanted, max_rotation=25.0, exclude=flame_ex)))
    out["flame.picks"] = json.dumps(rows)
    out["flame.count"] = str(len([p for p in M.plates("P-EL-FLAME") if "__v3__" in p.id]))
    out["pick_n.cloud5"] = json.dumps([one(p) for p in M.pick_n("P-SN-CLOUD", 99, 5, [10.0, 100.0, 190.0, 280.0, 350.0], max_rotation=45.0)])
    out["pick_n.crown3"] = json.dumps([one(p) for p in M.pick_n("P-SP-CROWN", "s", 3, None, liquid="cognac")])
    # a placed 1K plate: the registered float image, bit for bit
    for tag, pk in (("cloud", M.pick("P-SN-CLOUD", 7, 60.0)), ("cloud.mirror", M.pick("P-SN-CLOUD", 3, 200.0, max_rotation=90.0)),
                    ("crown", M.pick("P-SP-CROWN", 5, 90.0, max_rotation=30.0, liquid="cognac")), ("flame", M.pick("P-EL-FLAME", 2, 88.0, max_rotation=40.0, exclude=flame_ex))):
        arr, info = pk.place(512, 512, 256.0, 256.0, 110.0, lod="1k", strict=False)
        out[f"place.{tag}"] = hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest() + ":" + json.dumps([pk.plate.id, round(info["scale"], 9), info["lod"], info["src_px"]])
    return out
