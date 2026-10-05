# -*- coding: utf-8 -*-
"""The reviewed diff of the seed change (WP5B, decision C9 step B): what moved between the step A recording (data/stepA/, the scratch prototype's own
pictures, the prototype's seed) and the step B recording (data/singles_goldens.json, the seed from the eye id), case by case, and by how much.

    python scripts/styles_tests/diff_goldens.py                  the table of the two recordings: hashes, seeds, plate picks
    python scripts/styles_tests/diff_goldens.py --pixels         also renders the 1024 px cases twice (the old seed, the new one) and measures what
                                                                 differs in the picture: nothing may differ on the iris, the matter does
    python scripts/styles_tests/diff_goldens.py --pixels --real  the same on the real calibration eyes (SNAPEYES_CALIB; numbers only, no image is written)

The review questions it answers: (1) which designs moved (every one but Clean Iris, whose seed only dithered pure black); (2) which plate each plate
style draws now (a different plate is the visible change of Powder Burst and Splash); (3) is the iris untouched (T1: the pixels inside 0.95 R, zone A, are the
graded iris byte for byte, old and new alike); (4) how much of the rest of the picture moved. No image model, no network.
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
import singles_cases as SC  # noqa: E402

DATA = os.path.join(HERE, "data")


def load(*parts):
    with open(os.path.join(DATA, *parts), encoding="utf-8") as f:
        return json.load(f)


def plate_of(facts):
    out = []
    for k in ("powder", "splash", "elements"):
        v = facts.get(k) or {}
        for f in ("plate", "flame_plate", "water_plate"):
            if f in v:
                out.append(v[f].split("__", 1)[1] if "__" in v[f] else v[f])
    return " + ".join(out) or "-"


def table(old, new, keys):
    print(f"{'case':44s} {'sha old':>9s} {'sha new':>9s}  plates old -> new")
    for k in keys:
        o, n = old[k], new[k]
        po, pn = plate_of(o["facts"]), plate_of(n["facts"])
        mark = "same " if o["sha"] == n["sha"] else "moved"
        print(f"{k:44s} {o['sha'][:8]:>9s} {n['sha'][:8]:>9s}  {mark}  {po} -> {pn}" if po != "-" else f"{k:44s} {o['sha'][:8]:>9s} {n['sha'][:8]:>9s}  {mark}")


def pixels(old_new, label):
    """old_new: [(case, img_old, img_new, disc)]: per design the share of pixels that moved outside the iris and what moved on it."""
    rows = {}
    for c, a, b, d in old_new:
        a, b = np.asarray(a).astype(np.int16), np.asarray(b).astype(np.int16)
        yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
        rho = np.hypot(xx + 0.5 - d[0], yy + 0.5 - d[1]) / d[2]
        inside = rho <= 0.95
        diff = np.abs(a - b).max(-1)
        rows.setdefault(c["design"], []).append((int(diff[inside].max()), float((diff[~inside] > 8).mean()), float(diff[~inside].mean())))
    print(f"\n{label}: per design, over the cases: largest difference on the iris (zone A: 0.95 R and in; the limb veil of Powder Burst is zone B), share of the other pixels that moved by more than 8 levels, their mean change")
    for design in SC.DESIGNS:
        r = rows.get(design)
        if r:
            print(f"  {design:9s} iris max diff {max(x[0] for x in r)}   moved >8: {min(x[1] for x in r) * 100:5.1f} to {max(x[1] for x in r) * 100:5.1f} %   mean change {min(x[2] for x in r):.2f} to {max(x[2] for x in r):.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pixels", action="store_true")
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    if a.real:
        old, new = load("stepA", "singles_goldens_real.json")["cases"], load("singles_goldens_real.json")["cases"]
    else:
        old, new = load("stepA", "singles_goldens.json")["cases"], load("singles_goldens.json")["cases"]
    keys = sorted(new, key=lambda k: (SC.DESIGNS.index(k.split(".")[0]), k))
    assert set(old) == set(new), "the two recordings do not hold the same cases"
    moved = [k for k in keys if old[k]["sha"] != new[k]["sha"]]
    by = {d: [k for k in keys if k.startswith(d + ".")] for d in SC.DESIGNS}
    print(f"{len(moved)} of {len(keys)} pictures moved; unchanged: {sorted({k.split('.')[0] for k in keys if k not in moved})}")
    for d in SC.DESIGNS:
        print(f"  {d:9s} {sum(1 for k in by[d] if k in moved):2d} of {len(by[d]):2d} moved")
    table(old, new, [k for k in keys if (".1024" in k and ".text" not in k)])
    if a.pixels:
        import synth_iris as SI
        from _lib.styles import core as C
        from _lib.styles import singles as S
        if a.real:
            calib = os.environ.get("SNAPEYES_CALIB") or sys.exit("SNAPEYES_CALIB is not set")
            fx = {n: open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb").read() for n in SC.REAL_EYES}
            cases = [c for c in SC.real_cases()]
        else:
            fx = {n: SI.png_bytes(n) for n in SC.FIXTURE_BASE}
            cases = [c for c in SC.cases() if c["size"] == 1024]
        irises, out = {}, []
        for c in cases:
            if c["eye"] not in irises:
                irises[c["eye"]] = C.Iris(fx[c["eye"]], c["eye"])
            ir = irises[c["eye"]]
            ra = S.render(c["design"], ir, c["fmt"], c["size"], c["names"], c["date"], opts={"seed_mode": "legacy"})
            rb = S.render(c["design"], ir, c["fmt"], c["size"], c["names"], c["date"])
            out.append((c, ra.img, rb.img, (ra.d.cx, ra.d.cy, ra.d.R)))
        pixels(out, "real calibration eyes at 1024 px" if a.real else "synthetic eyes at 1024 px")


if __name__ == "__main__":
    main()
