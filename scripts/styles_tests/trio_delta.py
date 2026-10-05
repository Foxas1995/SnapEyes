# -*- coding: utf-8 -*-
"""The Trio delta check (WP7B, decision 34 of the specification): Family Colours with three eyes drawn from three 4096 px masters, once from the full source and once
from a smaller working copy of each, and what changes.

    python scripts/styles_tests/trio_delta.py master1.jpg master2.jpg master3.jpg [--sides 3072 2560 2048]

A local diagnostic (real masters are never in the repository: the wave-o live-test masters of the design round, or any three 4096 px restorations). numpy and the
engine only. For each side it prints the CPU seconds of the render, the colour difference (CIEDE2000 mean, 99th percentile, largest), the SSIM of the luma, the
share of pixels that differ by more than two levels, where those pixels lie (inside the irises, on the limb, outside) and the energy of the finest detail inside
the irises against the full source (a Laplacian of the luma: 1.0 is as sharp), and whether the plan's choices (the frozen decisions) and the seed are the same.

What it found on the three masters of the design round (this machine, numpy 2.4.4, Pillow 12.2.0; suites/baseline.md section 15): the choices and the seed
are the same at every side, so the delta is not a different design; 97 percent of the pixels that differ lie INSIDE the irises, the matter and the ground differ
by 0.005 levels; the tone is the same (the mean luma inside the irises differs by 0.001 level); the detail at two pixels and coarser has the same energy (1.006);
only the finest detail, at the pixel scale, differs: a 2048 px copy keeps 87 percent of its energy, a 3072 px copy 102 percent, a 2560 px copy 97 percent with
more aliasing than either. The copy is shrunk to the iris's drawn size by LANCZOS in two steps instead of one, and a ratio of 2.0 (a copy of 2048 px) is the
gentlest of the non integer ones. A 3072 px copy draws the full source's picture (mean 0.085) and costs the same time; only 2048 px saves time (14 s of CPU
against 18). The owner's design boards were drawn from a 2048 px copy, so a 2048 px working copy is the picture he approved.
"""
from __future__ import annotations

import argparse
import gc
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "api"))
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402


def luma(a):
    return (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]).astype(np.float64)


def box(x, win):
    """Mean over a win x win window (edge pixels use what is there), by cumulative sums."""
    p = win // 2
    c = np.cumsum(np.cumsum(np.pad(x, ((p + 1, p), (p + 1, p)), mode="edge"), 0), 1)
    return (c[win:, win:] - c[:-win, win:] - c[win:, :-win] + c[:-win, :-win]) / float(win * win)


def ssim(a, b, win=7):
    x, y = luma(a), luma(b)
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mx, my = box(x, win), box(y, win)
    sxx, syy, sxy = box(x * x, win) - mx * mx, box(y * y, win) - my * my, box(x * y, win) - mx * my
    return float((((2 * mx * my + c1) * (2 * sxy + c2)) / ((mx * mx + my * my + c1) * (sxx + syy + c2))).mean())


def laplacian_energy(l, mask):
    lap = (np.roll(l, 1, 0) + np.roll(l, -1, 0) + np.roll(l, 1, 1) + np.roll(l, -1, 1) - 4.0 * l)
    return float(lap[mask].var())


def de00(L, a, b, band=256, stride=2):
    s, n, mx, hist = 0.0, 0, 0.0, np.zeros(4000, np.int64)
    for y in range(0, a.shape[0], band * stride):
        d = L.ciede2000(L.srgb_to_lab(a[y:y + band].reshape(-1, 3)), L.srgb_to_lab(b[y:y + band].reshape(-1, 3)))
        s += float(d.sum())
        n += d.size
        mx = max(mx, float(d.max()))
        hist += np.bincount(np.minimum((d * 100).astype(np.int64), 3999), minlength=4000)
    cum = np.cumsum(hist) / n
    return {"mean": round(s / n, 3), "p99": float(np.searchsorted(cum, 0.99) / 100), "max": round(mx, 1)}


def render(raws, side):
    from _lib.styles import collision as CX
    from _lib.styles import core as C
    eyes = [C.Iris(r, f"m{i}", max_side=side) for i, r in enumerate(raws)]
    t0 = time.process_time()
    pv = CX.preview(eyes, {"style": "grp.collision", "eyes": 3, "layout": "trio"}, size=4096)
    cpu = time.process_time() - t0
    img = np.asarray(pv.img.convert("RGB")).copy()
    out = {"cpu": round(cpu, 1), "frozen": pv.log.get("frozen"), "seed": pv.seed, "discs": list(pv.discs)}
    del eyes, pv
    gc.collect()
    return img, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("masters", nargs=3, help="three 4096 px restorations (JPEG or PNG)")
    ap.add_argument("--sides", type=int, nargs="*", default=[3072, 2560, 2048])
    a = ap.parse_args()
    from _lib.styles import core as C
    L = C.L
    raws = [open(p, "rb").read() for p in a.masters]
    full, rf = render(raws, 4096)
    H, W = full.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    rho = [np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) / R for (cx, cy, R) in rf["discs"]]
    inside = np.zeros((H, W), bool)
    ring = np.zeros((H, W), bool)
    deep = np.zeros((H, W), bool)
    for r in rho:
        inside |= r <= 0.95
        ring |= (r > 0.95) & (r <= 1.06)
        deep |= r <= 0.90
    lf = luma(full)
    ef = laplacian_energy(lf, deep)
    print(f"4096 px source: cpu {rf['cpu']} s; choices {rf['frozen']}; seed {rf['seed']}", flush=True)
    for side in a.sides:
        img, r = render(raws, side)
        diff = np.abs(full.astype(np.int16) - img.astype(np.int16)).max(-1)
        over = diff > 2
        where = {k: round(float(over[m].sum() / max(over.sum(), 1)) * 100, 1) for k, m in (("inside", inside), ("limb", ring), ("outside", ~inside & ~ring))}
        print(f"{side} px copy: cpu {r['cpu']} s; de00 {de00(L, full, img)}; ssim {ssim(full, img):.4f}; over 2 levels {over.mean() * 100:.2f} %; where {where}; "
              f"finest detail energy {laplacian_energy(luma(img), deep) / ef:.3f}; same choices {r['frozen'] == rf['frozen']}, same seed {r['seed'] == rf['seed']}", flush=True)
        del img, diff, over
        gc.collect()


if __name__ == "__main__":
    main()
