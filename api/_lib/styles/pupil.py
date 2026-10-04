# -*- coding: utf-8 -*-
"""Pupil shape of a restored (graded) iris, numpy only. Ported verbatim from the design code's cx_pupil.py (byte identical to
uni_pupil.py: one copy here). analyse(), mask() and reach() are unchanged; to_record() and from_record() are new: the pupil as the
sealed eye profile carries it (whole numbers, thousandths of R).

The restoration already flattens the pupil to a neutral dark hole, so a ray cast from the pupil centroid finds its
edge. Result in units of the iris radius R:
  centre  (px, py)  offset of the pupil centre from the iris centre (screen x right, y down)
  r_theta (n_ang,)  pupil edge distance from that centre per screen angle (clockwise, 0 = 3 o'clock)
  rp                area-equivalent radius, reach(u) = support function of the pupil along a unit vector u
  cls               'round' | 'slit' | 'bar' (brief 1.4) from the bounding-box aspect

Module rule: every module of the v3 work starts with the __future__ import (Vercel's default Python is 3.12)."""
from __future__ import annotations

import math

import numpy as np

N_ANG = 180
CLASSES = ("round", "slit", "bar")
SCALE = 1000                      # the record keeps thousandths of R


def _luma(g):
    g = g.astype(np.float32)
    return 0.299 * g[..., 0] + 0.587 * g[..., 1] + 0.114 * g[..., 2]


def _bilinear(a, x, y):
    h, w = a.shape
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy
            + a[y0 + 1, x0 + 1] * fx * fy)


def _circ_median(v, k=7):
    n = len(v)
    pad = np.concatenate([v[-(k // 2):], v, v[:k // 2]])
    win = np.stack([pad[i:i + n] for i in range(k)], 0)
    return np.median(win, 0)


def analyse(g, n_ang=N_ANG):
    """g: the tight graded disc square (uint8 (t, t, 3), t = 2R px). Returns a dict (see module doc)."""
    t = g.shape[0]
    R = t / 2.0
    L = _luma(g)
    ax = (np.arange(t, dtype=np.float32) + 0.5 - R) / R
    rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)
    band = (rr > 0.45) & (rr < 0.90)
    med = float(np.median(L[band])) if band.any() else 60.0
    thr = float(np.clip(0.42 * med, 12.0, 46.0))
    dark = (L < thr) & (rr < 0.60)
    if dark.sum() < 20:
        # no dark hole found: a round pupil of the typical size at the centre
        return {"cx": 0.0, "cy": 0.0, "r_theta": np.full(n_ang, 0.27, np.float32), "rp": 0.27, "cls": "round", "thr": thr,
                "found": False, "aspect": 1.0}
    ys, xs = np.nonzero(dark)
    cx = float(xs.mean()) + 0.5
    cy = float(ys.mean()) + 0.5
    # smooth luminance a little so grain does not stop a ray
    Ls = L.copy()
    Ls = (Ls + np.roll(Ls, 1, 0) + np.roll(Ls, -1, 0) + np.roll(Ls, 1, 1) + np.roll(Ls, -1, 1)) / 5.0
    ang = (np.arange(n_ang) + 0.5) * (2 * math.pi / n_ang)
    steps = np.arange(0.0, 0.70 * R, 0.5)
    X = cx + np.cos(ang)[:, None] * steps[None, :]
    Y = cy + np.sin(ang)[:, None] * steps[None, :]
    prof = _bilinear(Ls, X, Y)
    bright = prof > thr
    r_edge = np.empty(n_ang)
    for i in range(n_ang):
        b = bright[i]
        # first run of >= 3 consecutive bright samples
        run = b[:-2] & b[1:-1] & b[2:]
        idx = np.nonzero(run)[0]
        r_edge[i] = steps[idx[0]] if len(idx) else steps[-1]
    r_edge = _circ_median(r_edge, 9)
    k = np.exp(-0.5 * (np.arange(-4, 5) / 1.8) ** 2)
    k /= k.sum()
    pad = np.concatenate([r_edge[-4:], r_edge, r_edge[:4]])
    r_edge = np.convolve(pad, k, "valid")
    r_theta = (r_edge / R).astype(np.float32)
    # extent along the axes -> class
    px = r_theta * np.cos(ang)
    py = r_theta * np.sin(ang)
    wid = float(px.max() - px.min())
    hei = float(py.max() - py.min())
    aspect = hei / max(wid, 1e-6)
    cls = "slit" if aspect >= 1.35 else ("bar" if aspect <= 0.70 else "round")
    area = 0.5 * float(np.sum(r_theta ** 2)) * (2 * math.pi / n_ang)
    rp = math.sqrt(area / math.pi)
    return {"cx": (cx - R) / R, "cy": (cy - R) / R, "r_theta": r_theta, "rp": float(rp), "cls": cls, "thr": thr,
            "found": True, "aspect": float(aspect), "ang": ang}


def mask(pup, tile_px, R_px, dil=0.0):
    """Boolean pupil mask on a tile_px square tile whose centre is the iris centre (R_px = iris radius in px), the
    pupil dilated by dil (units of R)."""
    n = tile_px
    ax = (np.arange(n, dtype=np.float32) + 0.5 - n / 2.0) / R_px
    dx = ax[None, :] - pup["cx"]
    dy = ax[:, None] - pup["cy"]
    r = np.sqrt(dx * dx + dy * dy)
    th = np.arctan2(dy, dx) % (2 * math.pi)
    rt = pup["r_theta"]
    m = len(rt)
    f = th * (m / (2 * math.pi)) - 0.5
    i0 = np.floor(f).astype(np.int64)
    w = f - i0
    edge = rt[i0 % m] * (1 - w) + rt[(i0 + 1) % m] * w
    return r <= edge + dil


def reach(pup, u):
    """Support function of the pupil along the unit vector u = (ux, uy) (screen x right, y down), in units of R,
    measured from the IRIS centre (includes the pupil's own offset)."""
    ang = pup["ang"] if "ang" in pup else (np.arange(len(pup["r_theta"])) + 0.5) * (2 * math.pi / len(pup["r_theta"]))
    px = pup["cx"] + pup["r_theta"] * np.cos(ang)
    py = pup["cy"] + pup["r_theta"] * np.sin(ang)
    return float(np.max(px * u[0] + py * u[1]))


# ----------------------------------------------------------------------------- the sealed form (whole numbers)
def to_record(pup):
    """The pupil as the eye profile stores it: {cls, aspect, rp, cx, cy, found, reach}, every number a whole number of
    thousandths of R (reach: the pupil edge distance per angle, N_ANG entries, what mask() and reach() are made from)."""
    r = np.asarray(pup["r_theta"], np.float64)
    # the aspect is capped at 100 for the record (a pupil edge of zero width would give 10^6; the class is decided before)
    return {"cls": str(pup["cls"]), "aspect": int(round(min(float(pup["aspect"]), 100.0) * SCALE)), "rp": int(round(float(pup["rp"]) * SCALE)),
            "cx": int(round(float(pup["cx"]) * SCALE)), "cy": int(round(float(pup["cy"]) * SCALE)), "found": 1 if pup["found"] else 0,
            "reach": [int(round(float(v) * SCALE)) for v in r]}


def from_record(rec):
    """The dict analyse() returns (cx, cy, r_theta, rp, cls, aspect, found, ang), rebuilt from a record. Values are the
    record's thousandths, so a profile read back from a seal draws what the sealed numbers say."""
    reach_ = rec["reach"]
    n = len(reach_)
    return {"cx": rec["cx"] / SCALE, "cy": rec["cy"] / SCALE, "r_theta": np.asarray(reach_, np.float32) / np.float32(SCALE),
            "rp": rec["rp"] / SCALE, "cls": rec["cls"], "found": bool(rec["found"]), "aspect": rec["aspect"] / SCALE,
            "ang": (np.arange(n) + 0.5) * (2 * math.pi / n)}
