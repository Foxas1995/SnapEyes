# -*- coding: utf-8 -*-
"""The reviewed diff of the seed change for the universe family (WP8B, decision C9 step B): what moved between the step A recording (data/stepA/, the scratch
prototype's own pictures, the prototype's seed) and the step B recording (data/universe_goldens.json, the seed from the eyes' ids), case by case, and by how much.

    python scripts/styles_tests/diff_goldens_universe.py                  the table of the two recordings: hashes, what each picture chose, the plates
    python scripts/styles_tests/diff_goldens_universe.py --pixels         also renders the 512 px cases twice (the old seed, the new one) and measures what differs
                                                                          in the picture: the irises (zone A) must not move, the matter does
    python scripts/styles_tests/diff_goldens_universe.py --pixels --real  the same on the real calibration eyes at 1024 px (SNAPEYES_CALIB; numbers only)

The review questions it answers: (1) which pictures moved (every one: the seed draws the matter, the grains, the stars, the flakes and the plate of every look); (2) which
plate each picture draws from now (the plate of a plate look, the Echo wall's accent); (3) are the choices that are NOT the seed's the same (the layout, the canvas, the
geometry of every iris, the contacts and their kind, the notches, the text, the work grid: they must be equal in every case); (4) is the iris untouched (T1: zone A is the
graded iris byte for byte, old and new alike); (5) how much of the rest moved. The picture's colour treatment does not depend on the seed. No image model, no network.
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
import universe_cases as UC  # noqa: E402

DATA = os.path.join(HERE, "data")
CHOICES = ("layout", "aspect", "f", "S", "wh", "halo_rows", "band_rows", "contacts", "notches", "text", "eye_geometry")
LOOKS = UC.LOOKS


def load(*parts):
    with open(os.path.join(DATA, *parts), encoding="utf-8") as f:
        return json.load(f)


def look_of(k):
    return k.split(".")[0]


def table(old, new, keys):
    print(f"{'case':66s} {'sha old':>9s} {'sha new':>9s}  choices  plates (old -> new)")
    for k in keys:
        o, n = old[k], new[k]
        same = all(o["facts"].get(c) == n["facts"].get(c) for c in CHOICES)
        mark = "same " if o["sha"] == n["sha"] else "moved"
        po = [o["facts"][x]["id"][-24:] for x in ("plate", "accent_plate") if x in o["facts"]]
        pn = [n["facts"][x]["id"][-24:] for x in ("plate", "accent_plate") if x in n["facts"]]
        print(f"{k:66s} {o['sha'][:8]:>9s} {n['sha'][:8]:>9s}  {mark} {'yes' if same else 'NO '}  {','.join(po) or '-'} -> {','.join(pn) or '-'}")


def pixels(rows, label):
    """rows: [(case, img_old, img_new, discs)]: per look the largest difference deep inside the irises (0.80 R and in, where no iris overlaps another, no seam band and no
    contact strip lies), the share of the other pixels that moved by more than 8 levels, their mean change."""
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
        key = c["look"] + ("" if len(c["eyes"]) == 1 else f" x{len(c['eyes'])}")
        out.setdefault(key, []).append((int(diff[inside].max()) if inside.any() else 0, float((diff[~inside] > 8).mean()), float(diff[~inside].mean())))
    print(f"\n{label}: per look, over the cases: largest difference deep inside the irises, share of the other pixels that moved by more than 8 levels, their mean change")
    for key in sorted(out):
        r = out[key]
        print(f"  {key:12s} iris max diff {max(x[0] for x in r)}   moved >8: {min(x[1] for x in r) * 100:5.1f} to {max(x[1] for x in r) * 100:5.1f} %   "
              f"mean change {min(x[2] for x in r):.2f} to {max(x[2] for x in r):.2f}   ({len(r)} pictures)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pixels", action="store_true")
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    if a.real:
        old, new = load("stepA", "universe_goldens_real.json")["cases"], load("universe_goldens_real.json")["cases"]
    else:
        old, new = load("stepA", "universe_goldens.json")["cases"], load("universe_goldens.json")["cases"]
    assert set(old) == set(new), "the two recordings do not hold the same cases"
    keys = sorted(new, key=lambda k: (LOOKS.index(look_of(k)), k))
    moved = [k for k in keys if old[k]["sha"] != new[k]["sha"]]
    changed = [k for k in keys if any(old[k]["facts"].get(c) != new[k]["facts"].get(c) for c in CHOICES)]
    print(f"{len(moved)} of {len(keys)} pictures moved; the choices that are not the seed's (layout, canvas, geometry, contacts, notches, text, work grid) differ in {len(changed)}: {changed}")
    for lk in LOOKS:
        ks = [k for k in keys if look_of(k) == lk]
        print(f"  {lk:10s} {sum(1 for k in ks if k in moved):2d} of {len(ks):2d} moved")
    plate_changed = [k for k in keys if [old[k]['facts'].get(x, {}).get('id') for x in ('plate', 'accent_plate')] != [new[k]['facts'].get(x, {}).get('id') for x in ('plate', 'accent_plate')]]
    with_plate = [k for k in keys if "plate" in new[k]["facts"] or "accent_plate" in new[k]["facts"]]
    print(f"the plate drawn from changed in {len(plate_changed)} of the {len(with_plate)} pictures that draw from one")
    table(old, new, [k for k in keys if ".1024" in k or a.real])
    if a.pixels:
        import synth_iris as SI  # noqa: F401
        from _lib.styles import core as C
        from _lib.styles import universe as U
        if a.real:
            calib = os.environ.get("SNAPEYES_CALIB") or sys.exit("SNAPEYES_CALIB is not set")
            fx = {n: open(os.path.join(calib, f"{n}_2_enhanced.jpg"), "rb").read() for n in UC.REAL_EYES}
            cases = list(UC.real_cases())
        else:
            fx = {n: SI.png_bytes(n) for n in UC.FIXTURE_BASE}
            cases = [c for c in UC.cases() if c["size"] == 512 and not c["opts"] and not c["names"] and not c["date"]]
        out = []
        for c in cases:
            # a fresh Iris for each picture (the family caches the extended source of an eye on the Iris: a shared one carries state from picture to picture, see baseline.md section 16)
            ra, sa = U.render(c["look"], [C.Iris(fx[n], n) for n in c["eyes"]], c["size"], c["aspect"], c["names"], c["date"], dict(c["opts"], seed_mode="legacy"), want_scene=True)
            rb, sb = U.render(c["look"], [C.Iris(fx[n], n) for n in c["eyes"]], c["size"], c["aspect"], c["names"], c["date"], dict(c["opts"]), want_scene=True)
            out.append((c, ra, rb, [tuple(e.snap) for e in sb.eyes]))
        pixels(out, "real calibration eyes at 1024 px" if a.real else "synthetic eyes at 512 px")


if __name__ == "__main__":
    main()
