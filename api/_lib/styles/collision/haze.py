# -*- coding: utf-8 -*-
"""cx_haze: the photographed powder haze of the collision designs (BRIEF_V3_FINAL 3.1 layer 2, round 2c AD fix A5 + B).

One P-SN-CLOUD plate per iris (a real photograph of powder with a void registered to the limb, `black` 45 or 60, the strong side pointing away
from the partner), used as LUMINANCE only, gradient-mapped through the eye's own colours per angle, masked to the rim (smoothstep(0.75 R,
0.35 R, e) plus a denser rim band smoothstep(0.45 R, 0.08 R, e)), luminance capped, added under the irises. Never the same plate twice.
numpy + PIL only (the plate loader is the plate library's registry, offline tooling of the plate run).
"""
from __future__ import annotations

# PORT of work package WP7A (step A): cx_haze.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (imports, the cloud plates come from the plate loader); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.
# WP7B (step B) moved the seed and the place of the pixel decisions and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import math

import numpy as np

from .. import core as C
from .. import plates as _PLATES


def registry():
    """The plate loader (api/_lib/styles/plates.py): the pick and the placement of the plate workflow's registry, read only, on the baked library."""
    return _PLATES


def _ss(x0, x1, x):
    t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _brief_angle(dx, dy):
    """Screen vector (y down) -> the brief's degrees (0 = 3 o'clock, counter-clockwise positive)."""
    return (-math.degrees(math.atan2(dy, dx))) % 360.0


def cloud_haze(cv, geo, pals, rnd, prm, W, H, mask_fn=None, seed_tag="haze"):
    """Adds the cloud-plate haze of every iris into the float canvas cv. prm: cloud (alpha, default 0.30), cloud_cap (luminance cap 0.55),
    cloud_rim (extra rim band strength 0.40), cloud_reach (0.75). Returns an info dict (plate ids)."""
    alpha = prm.get("cloud", 0.0)
    info = dict(n=0, ids=[])
    if alpha <= 0:
        return info
    R = registry()
    cap = prm.get("cloud_cap", 0.55)
    rim = prm.get("cloud_rim", 0.40)
    reach = prm.get("cloud_reach", 0.75)
    cen = geo.c.mean(0)
    used = []
    order = list(range(geo.n))
    for k in order:
        # strong side: away from the partner (pair) or from the centroid (groups)
        if geo.n == 2:
            o = geo.c[1 - k]
            vx, vy = geo.c[k][0] - o[0], geo.c[k][1] - o[1]
        else:
            vx, vy = geo.c[k][0] - cen[0], geo.c[k][1] - cen[1]
            if math.hypot(vx, vy) < 1e-3:
                vx, vy = 0.0, -1.0
        want = _brief_angle(vx, vy) + (rnd.uniform() - 0.5) * 50.0
        seed = int(rnd.uniform() * 2 ** 31)
        classes = prm.get("cloud_black", ("45", "60"))
        try:
            if not isinstance(classes, (tuple, list)):
                raise R.NoPlate("no plate classes to filter by")
            pk = R.pick("P-SN-CLOUD", seed, want, exclude=tuple(used), max_rotation=45.0, black=list(classes), pv=prm.get("pv"))
        except R.NoPlate:
            pk = R.pick("P-SN-CLOUD", seed, want, exclude=tuple(used), max_rotation=90.0, pv=prm.get("pv"))
        used.append(pk.plate.id)
        Rk = float(geo.R[k])
        cx, cy = float(geo.c[k][0]), float(geo.c[k][1])
        r_sc = 1.0
        vr = pk.plate.void[2] if pk.plate.void else 0.22
        need = Rk / (vr * 4096.0)
        if need > 1.09:
            r_sc = 1.09 / need                              # a 4K plate enlarged at most x1.09: the void hides under the iris, the ring starts a little inside
        lum, pinfo = pk.place(W, H, cx, cy, Rk, strict=False, r_scale=1.0)
        lum = lum.astype(np.float32)
        yy, xx = np.ogrid[:H, :W]
        # bounding box of the plate's useful area: (1 + reach) R around the iris
        ext = int(Rk * (1.0 + reach + 0.15))
        x0, x1 = max(0, int(cx) - ext), min(W, int(cx) + ext)
        y0, y1 = max(0, int(cy) - ext), min(H, int(cy) + ext)
        sub = lum[y0:y1, x0:x1]
        gx = (np.arange(x0, x1, dtype=np.float32) + 0.5 - cx)[None, :]
        gy = (np.arange(y0, y1, dtype=np.float32) + 0.5 - cy)[:, None]
        rr = np.sqrt(gx * gx + gy * gy) / Rk
        e = rr - 1.0
        radial = _ss(reach, 0.35 * reach / 0.75, e) + rim * _ss(0.45, 0.08, e)
        radial = radial * _ss(0.0, 0.05, e)
        flo = prm.get("cloud_floor", 0.0)
        sub2 = np.maximum(sub - flo, 0.0) / max(1.0 - flo, 1e-3)
        sub2 = sub2 ** prm.get("cloud_gamma", 1.0)
        L = np.minimum(sub2 * radial, cap + 0.25 * rim * _ss(0.45, 0.08, e))
        L = np.maximum(L - prm.get("cloud_black", 0.020) / max(alpha, 1e-3), 0.0)          # a black point: the faint tails of the haze do not lift the pure black
        if mask_fn is not None:
            L = L * mask_fn(gx + cx, gy + cy)
        th = np.arctan2(gy, gx)
        idx = C.angle_index(th)
        lut = _haze_lut(pals[k])
        col = lut[idx]
        cv[y0:y1, x0:x1] += (L * alpha)[..., None] * col
        info["n"] += 1
        info["ids"].append(pk.plate.id)
    return info


def _haze_lut(pal):
    """(LUT_N, 3) colour of the haze per ring angle: the chip palette lifted, slightly richer than the chips (the plate luminance carries the
    highlights)."""
    from .. import core as CC
    n = CC.LUT_N
    phi = (np.arange(n) + 0.5) * (2 * math.pi / n)
    u = np.full(n, 0.35)
    v = np.full(n, 0.55)
    w = np.full(n, 0.5)
    c = pal.chips2(phi, u, v, w)
    return c.astype(np.float32)
