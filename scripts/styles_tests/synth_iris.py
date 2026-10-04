# -*- coding: utf-8 -*-
"""A synthetic iris generator: the committed fixtures of the v3 style suites. A real eye is biometric data and the calibration
restorations are the owner's and his volunteers' (never committed); these irises are procedural, so a test can run anywhere and nothing
in the repository is a person.

make(kind, pupil, lid, lash, seed, side) returns an RGB image of the shape the engines receive: a square with the restored iris disc on
black (the disc radius is the site's own share of the square, iris.iris_radius_frac(1.12)), a limbal ring, radial fibres (angular noise
drawn in polar space, smooth along the radius), a collarette, a few crypts, and a pupil that is round, a vertical slit or a horizontal bar.
  kind   blue | green | amber | dark_brown | grey      the three colour classes of the engine (own, dark_brown, grey) in five eyes
  pupil  round | slit | bar
  lid    True: a wedge of eyelid skin across the upper rim (a hard failure of the restoration gate)
  lash   True: a fan of dark lash lines across the rim (the other hard failure)
Everything is drawn from numpy's PCG64 uniform doubles (never normal or gamma, whose streams numpy may change) and rounded to 8 bit, so a
fixture is the same picture on every machine of one class (the sine and exponential of float32 differ in the last bit between CPU
paths, which can flip a level in a few pixels: the suites that hash a fixture say so).

FIXTURES is the standard set: eight clean eyes and four failures. png_bytes(name) is what the tests hand to the engine (lossless, so a
fixture's bytes do not depend on a JPEG encoder); jpeg_bytes(name) is the same picture as the preview the site stores.
"""
from __future__ import annotations

import io
import math

import numpy as np
from PIL import Image

R_FRAC = 0.4464285714285714       # iris.iris_radius_frac(1.12): the disc radius as a share of the square

# base colour of the mid ring, the inner (pupil side) and the outer (limbus side) tint, RGB 0..255
PALETTES = {
    "blue": ((86, 128, 168), (150, 150, 120), (46, 78, 112)),
    "green": ((96, 132, 78), (156, 140, 82), (52, 82, 52)),
    "amber": ((168, 118, 52), (196, 150, 72), (104, 66, 30)),
    "dark_brown": ((74, 44, 24), (104, 66, 34), (34, 20, 12)),
    "grey": ((132, 138, 144), (156, 156, 150), (84, 90, 98)),
}
PUPILS = ("round", "slit", "bar")

FIXTURES = {
    "blue_round": dict(kind="blue", pupil="round", seed=11),
    "green_round": dict(kind="green", pupil="round", seed=12),
    "amber_slit": dict(kind="amber", pupil="slit", seed=13),
    "dark_brown_round": dict(kind="dark_brown", pupil="round", seed=14),
    "dark_brown_bar": dict(kind="dark_brown", pupil="bar", seed=15),
    "grey_round": dict(kind="grey", pupil="round", seed=16),
    "blue_slit": dict(kind="blue", pupil="slit", seed=17),
    "green_bar": dict(kind="green", pupil="bar", seed=18),
    "blue_lid": dict(kind="blue", pupil="round", lid=True, seed=21),
    "dark_brown_lid": dict(kind="dark_brown", pupil="round", lid=True, seed=22),
    "grey_lash": dict(kind="grey", pupil="round", lash=True, seed=23),
    "grey_lid": dict(kind="grey", pupil="round", lid=True, seed=24),
}
CLEAN = [n for n, d in FIXTURES.items() if not (d.get("lid") or d.get("lash"))]
FAILING = [n for n, d in FIXTURES.items() if d.get("lid") or d.get("lash")]


def _smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _box_blur(a, k, axis):
    """Circular (axis 0) or reflecting (axis 1) running mean of width k, by cumulative sums."""
    if k <= 1:
        return a
    r = k // 2
    if axis == 0:
        p = np.concatenate([a[-r:], a, a[:r]], 0)
    else:
        p = np.concatenate([a[:, r:0:-1], a, a[:, -2:-r - 2:-1]], 1)
    c = np.cumsum(p, axis=axis, dtype=np.float64)
    if axis == 0:
        c = np.concatenate([np.zeros((1, a.shape[1])), c], 0)
        return ((c[k:k + a.shape[0]] - c[:a.shape[0]]) / k).astype(np.float32)
    c = np.concatenate([np.zeros((a.shape[0], 1)), c], 1)
    return ((c[:, k:k + a.shape[1]] - c[:, :a.shape[1]]) / k).astype(np.float32)


def _polar_noise(rng, n_ang, n_rad, ang_blur, rad_blur):
    """Uniform noise in polar space (angle x radius), smoothed little along the angle and much along the radius: radial streaks."""
    a = rng.random((n_ang, n_rad)).astype(np.float32)
    a = _box_blur(_box_blur(a, ang_blur, 0), rad_blur, 1)
    a = _box_blur(_box_blur(a, ang_blur, 0), rad_blur, 1)
    lo, hi = float(a.min()), float(a.max())
    return (a - lo) / max(hi - lo, 1e-6)


def _sample_polar(field, th, rho, rho_max=1.0):
    """Bilinear lookup of a polar field (angle rows over 0..2 pi, radius columns over 0..rho_max) at pixel angles and radii."""
    n_ang, n_rad = field.shape
    u = (th % (2.0 * math.pi)) / (2.0 * math.pi) * n_ang
    v = np.clip(rho / rho_max, 0.0, 1.0) * (n_rad - 1)
    i0 = np.floor(u).astype(np.int64) % n_ang
    i1 = (i0 + 1) % n_ang
    j0 = np.minimum(np.floor(v).astype(np.int64), n_rad - 2)
    fu = (u - np.floor(u)).astype(np.float32)
    fv = (v - j0).astype(np.float32)
    return (field[i0, j0] * (1 - fu) * (1 - fv) + field[i1, j0] * fu * (1 - fv) + field[i0, j0 + 1] * (1 - fu) * fv
            + field[i1, j0 + 1] * fu * fv)


def make(kind="blue", pupil="round", lid=False, lash=False, seed=1, side=1024):
    """One synthetic restored iris: RGB uint8 image, side x side, the disc on black."""
    if kind not in PALETTES or pupil not in PUPILS:
        raise ValueError(f"kind is one of {sorted(PALETTES)}, pupil one of {PUPILS}")
    rng = np.random.default_rng(int(seed))
    N = int(side)
    Ri = R_FRAC * N
    ax = (np.arange(N, dtype=np.float32) + 0.5 - N / 2.0)
    X, Y = np.meshgrid(ax, ax)
    rho = np.sqrt(X * X + Y * Y) / np.float32(Ri)
    th = np.arctan2(Y, X)
    mid, inner, outer = (np.asarray(c, np.float32) for c in PALETTES[kind])

    # colour ramp along the radius: inner tint at the pupil edge, mid ring, outer tint toward the limbus
    t_in = _smooth01((0.55 - rho) / 0.35)[..., None]
    t_out = _smooth01((rho - 0.62) / 0.34)[..., None]
    col = mid * (1 - t_in - t_out) + inner * t_in + outer * t_out

    # radial fibres: two noise scales (fine and coarse), the fine one stronger toward the middle of the ring
    fine = _sample_polar(_polar_noise(rng, 720, 96, 3, 9), th, rho)
    coarse = _sample_polar(_polar_noise(rng, 180, 48, 5, 13), th, rho)
    fib = 1.0 + 0.30 * (fine - 0.5) * 2.0 + 0.16 * (coarse - 0.5) * 2.0
    col = col * fib[..., None]

    # collarette (the wavy ring near the pupil), a few crypts (dark soft blobs), the limbal ring (a dark rim)
    wob = 0.012 * np.cos(7.0 * th + rng.random() * 6.28) + 0.008 * np.cos(13.0 * th + rng.random() * 6.28)
    coll = np.exp(-0.5 * ((rho - 0.46 - wob) / 0.035) ** 2)
    col = col * (1.0 + 0.16 * coll[..., None])
    for _ in range(5):
        a, r, w = rng.random() * 6.2832, 0.55 + 0.30 * rng.random(), 0.03 + 0.03 * rng.random()
        d2 = (rho * np.cos(th - a) - r) ** 2 + (rho * np.sin(th - a)) ** 2
        col = col * (1.0 - 0.28 * np.exp(-0.5 * d2 / (w * w))[..., None])
    limb = 1.0 - 0.45 * _smooth01((rho - 0.90) / 0.10)
    col = col * limb[..., None]

    # the pupil: round (r = 0.27), a vertical slit or a horizontal bar, soft edge 0.012
    if pupil == "round":
        e = np.sqrt((X / (0.27 * Ri)) ** 2 + (Y / (0.27 * Ri)) ** 2)
    elif pupil == "slit":
        e = np.sqrt((X / (0.085 * Ri)) ** 2 + (Y / (0.42 * Ri)) ** 2)
    else:
        e = np.sqrt((X / (0.44 * Ri)) ** 2 + (Y / (0.11 * Ri)) ** 2)
    pup = _smooth01((e - 1.0) / 0.05 + 0.5)
    col = col * pup[..., None] + np.asarray((7, 7, 9), np.float32) * (1 - pup[..., None])

    # failures of the restoration: an eyelid wedge across the upper rim, or a fan of lashes
    if lid:
        a0, a1 = -2.75, -0.40                                    # screen angles (y down): the upper rim, about 135 degrees
        within = _smooth01((th - a0) / 0.06) * _smooth01((a1 - th) / 0.06)
        edge = 0.58 + 0.07 * np.cos(5.0 * th)
        w = within * _smooth01((rho - edge) / 0.03)
        skin = np.asarray((205, 158, 132), np.float32) * (1.0 + 0.05 * (fine - 0.5)[..., None])
        col = col * (1 - w[..., None]) + skin * w[..., None]
        lashes = w * _smooth01((rho - 0.955) / 0.02)
        col = col * (1 - 0.8 * lashes[..., None]) + np.asarray((22, 14, 12), np.float32) * 0.8 * lashes[..., None]
    if lash:
        for k in range(26):
            a = -2.6 + 0.075 * k + 0.02 * rng.random()
            d = np.abs(np.sin(th - a)) * rho
            w = np.exp(-0.5 * (d / 0.012) ** 2) * _smooth01((rho - 0.58) / 0.05) * (np.cos(th - a) > 0)
            col = col * (1 - 0.92 * w[..., None]) + np.asarray((18, 12, 10), np.float32) * 0.92 * w[..., None]

    # the disc on black: alpha 1 inside the limbus, a soft 0.012 edge
    alpha = _smooth01((1.0 - rho) / 0.012)
    out = col * alpha[..., None]
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), "RGB")


def make_named(name, side=1024):
    return make(side=side, **FIXTURES[name])


def png_bytes(name, side=1024):
    b = io.BytesIO()
    make_named(name, side).save(b, "PNG", compress_level=3)
    return b.getvalue()


def png_bytes_of(**kw):
    """The PNG bytes of make(**kw): an eye that is not one of the standard fixtures (a leak test needs many different ones)."""
    b = io.BytesIO()
    make(**kw).save(b, "PNG", compress_level=3)
    return b.getvalue()


def jpeg_bytes(name, side=1024, quality=92):
    b = io.BytesIO()
    make_named(name, side).save(b, "JPEG", quality=quality, subsampling=0)
    return b.getvalue()
