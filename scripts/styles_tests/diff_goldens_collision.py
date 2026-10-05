# -*- coding: utf-8 -*-
"""The reviewed diff of the seed change for the collision family (WP7B, decision C9 step B): what moved between the step A recording (data/stepA/, the scratch
prototype's own pictures, the prototype's seed) and the step B recording (data/collision_goldens.json, the seed from the eyes' ids), case by case, and by how much.

    python scripts/styles_tests/diff_goldens_collision.py                  the table of the two recordings: hashes, seeds, what each picture chose
    python scripts/styles_tests/diff_goldens_collision.py --pixels         also renders the 512 px cases twice (the old seed, the new one) and measures what differs
                                                                           in the picture: the irises (zone A) must not move, the matter does
    python scripts/styles_tests/diff_goldens_collision.py --pixels --real  the same on the real calibration eyes at 1024 px (SNAPEYES_CALIB; numbers only)

The review questions it answers: (1) which pictures moved (every one with matter: the seed only dithers the pure black of Clean Infinity's ground, so a Clean
Infinity moves a little and by a rounding of the dither only); (2) which plates each picture draws from now (the haze's cloud plates and the notch jets);
(3) are the choices that are NOT the seed's the same (the design drawn, the lens mode and its colour step, the fronts, the edge modes, the fallbacks: they
must be equal in every case); (4) is the iris untouched (T1: zone A is the graded iris byte for byte, old and new alike); (5) how much of the rest moved.
No image model, no network.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
import collision_cases as CC  # noqa: E402

DATA = os.path.join(HERE, "data")
CHOICES = ("design_used", "lens_mode", "lens_K", "overlap_fallback", "fallback", "rules", "d_over_R", "edge_modes", "gate_fail", "auto_hairline")


def load(*parts):
    with open(os.path.join(DATA, *parts), encoding="utf-8") as f:
        return json.load(f)


def table(old, new, keys):
    print(f"{'case':58s} {'sha old':>9s} {'sha new':>9s}  choices equal  plates")
    for k in keys:
        o, n = old[k], new[k]
        same = all(o["facts"].get(c) == n["facts"].get(c) for c in CHOICES)
        mark = "same " if o["sha"] == n["sha"] else "moved"
        plates = (len(o["facts"].get("cloud") or []), len(n["facts"].get("cloud") or []))
        print(f"{k:58s} {o['sha'][:8]:>9s} {n['sha'][:8]:>9s}  {mark}  {'yes' if same else 'NO '}  cloud {plates[0]} -> {plates[1]}  "
              f"{o['facts'].get('design_used')}/{n['facts'].get('design_used')}")


def pixels(rows, label):
    """rows: [(case, img_old, img_new, discs)]: per design the largest difference deep inside the irises (0.80 R and in, where no iris overlaps another, no seam
    band and no contact strip lies), the share of the other pixels that moved by more than 8 levels, their mean change."""
    out = {}
    for c, a, b, discs in rows:
        a, b = np.asarray(a).astype(np.int16), np.asarray(b).astype(np.int16)
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        inside = np.zeros(a.shape[:2], bool)
        for (cx, cy, R) in discs:
            inside |= np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) <= 0.80 * R
        for (cx, cy, R) in discs:                                     # where a second iris reaches in, the seam or the contact is drawn: not "deep inside"
            for (cx2, cy2, R2) in discs:
                if (cx2, cy2) != (cx, cy):
                    inside &= ~(np.hypot(xx + 0.5 - cx2, yy + 0.5 - cy2) <= 1.05 * R2)
        diff = np.abs(a - b).max(-1)
        out.setdefault(c["design"], []).append((int(diff[inside].max()) if inside.any() else 0, float((diff[~inside] > 8).mean()), float(diff[~inside].mean())))
    print(f"\n{label}: per design, over the cases: largest difference deep inside the irises, share of the other pixels that moved by more than 8 levels, their mean change")
    for design in CC_DESIGNS:
        r = out.get(design)
        if r:
            print(f"  {design:9s} iris max diff {max(x[0] for x in r)}   moved >8: {min(x[1] for x in r) * 100:5.1f} to {max(x[1] for x in r) * 100:5.1f} %   "
                  f"mean change {min(x[2] for x in r):.2f} to {max(x[2] for x in r):.2f}")


CC_DESIGNS = ("infinity", "kiss", "trio", "family", "chain")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pixels", action="store_true")
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    if a.real:
        old, new = load("stepA", "collision_goldens_real.json")["cases"], load("collision_goldens_real.json")["cases"]
    else:
        old, new = load("stepA", "collision_goldens.json")["cases"], load("collision_goldens.json")["cases"]
    assert set(old) == set(new), "the two recordings do not hold the same cases"
    keys = sorted(new, key=lambda k: (CC_DESIGNS.index(k.split(".")[0]), k))
    moved = [k for k in keys if old[k]["sha"] != new[k]["sha"]]
    changed = [k for k in keys if any(old[k]["facts"].get(c) != new[k]["facts"].get(c) for c in CHOICES)]
    print(f"{len(moved)} of {len(keys)} pictures moved; the choices that are not the seed's (design, lens mode, fronts, edge modes, fallbacks) differ in {len(changed)}: {changed}")
    for d in CC_DESIGNS:
        ks = [k for k in keys if k.split(".")[0] == d]
        print(f"  {d:9s} {sum(1 for k in ks if k in moved):2d} of {len(ks):2d} moved")
    table(old, new, [k for k in keys if ".1024" in k or a.real])
    if a.pixels:
        import synth_iris as SI  # noqa: F401
        from _lib.styles import core as C
        from _lib.styles import collision as CX
        if a.real:
            calib = os.environ.get("SNAPEYES_CALIB") or sys.exit("SNAPEYES_CALIB is not set")
            fx = {n: open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb").read() for n in CC.REAL_EYES}
            cases = list(CC.real_cases())
        else:
            fx = {n: CC.fixture_bytes(n) for n in CC.fixture_names()}
            cases = [c for c in CC.cases() if c["size"] == 512 and not c["opts"] and c["bg"] == "dark"]
        irises, out = {}, []
        for c in cases:
            for n in c["eyes"]:
                irises.setdefault(n, C.Iris(fx[n], n))
            eyes = [irises[n] for n in c["eyes"]]
            o = dict(CC.PRODUCTION)
            o.update(c["opts"])
            ra = CX.render(c["design"], eyes, c["fmt"], c["size"], c["names"], c["date"], c["bg"], c["clean"], dict(o, seed_mode="legacy"), c["layout"])
            rb = CX.render(c["design"], eyes, c["fmt"], c["size"], c["names"], c["date"], c["bg"], c["clean"], o, c["layout"])
            out.append((c, ra.img, rb.img, [(d.cx, d.cy, d.R) for d in rb.discs]))
        pixels(out, "real calibration eyes at 1024 px" if a.real else "synthetic eyes at 512 px")


if __name__ == "__main__":
    main()
