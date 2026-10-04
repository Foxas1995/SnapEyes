# -*- coding: utf-8 -*-
"""Colour of an eye: the colour class, the effect palettes, the secondary hue. numpy only.

Ported verbatim from the design code: the colour helpers of fx/core.py (lch, colour_stats, colour_class, boost, mix, effect_palette,
palette_lut and the angular lookups), cx_palette.py (OKLab, Pal, pair_hues: the powder colours of one iris) and secondary_hue() of
singles_kit.py (H2 of the brief). Nothing here knows an iris object: functions take the ring (360 x 3 float32, 0..1) or anything
with a .ring, .cls and .stats (an eye.EyeInput does), so the profile module and the engines share one copy.

Colour class from the mean ring colour in CIELCh: dark_brown = L* < 30 and hue 30-95 deg; grey = C* < 10 (and not dark_brown);
else own. Each style passes its own fallback palette for the two special classes.

Module rule: every module of the v3 work starts with the __future__ import (Vercel's default Python is 3.12)."""
from __future__ import annotations

import math

import numpy as np

from .. import iris as L

DARK_BROWN_L = 30.0
DARK_BROWN_HUE = (30.0, 95.0)
GREY_C = 10.0
LUT_N = 8192                         # angular lookup resolution (power of two) for per-pixel colour and profiles
TWO_PI = 2.0 * math.pi
CLASSES = ("own", "dark_brown", "grey")


# ----------------------------------------------------------------------------- colour space
def lab_to_srgb(lab):
    """CIELAB (D65) to sRGB 0..1 (inverse of L.srgb_to_lab), clipped."""
    lab = np.asarray(lab, np.float64)
    fy = (lab[..., 0] + 16.0) / 116.0
    fx = fy + lab[..., 1] / 500.0
    fz = fy - lab[..., 2] / 200.0
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f > 0.206893, f ** 3, (f - 16.0 / 116.0) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    M = np.array([[0.412453, 0.357580, 0.180423], [0.212671, 0.715160, 0.072169], [0.019334, 0.119193, 0.950227]])
    lin = xyz @ np.linalg.inv(M).T
    lin = np.clip(lin, 0.0, None)
    c = np.where(lin > 0.0031308, 1.055 * lin ** (1 / 2.4) - 0.055, 12.92 * lin)
    return np.clip(c, 0.0, 1.0)


def lch(rgb01_):
    """sRGB 0..1 -> (L*, C*, h deg)."""
    lab = L.srgb_to_lab(np.asarray(rgb01_, np.float64) * 255.0)
    return lab[..., 0], np.hypot(lab[..., 1], lab[..., 2]), np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360.0


def from_lch(Ls, C, h):
    hr = np.radians(h)
    return lab_to_srgb(np.stack([np.asarray(Ls, np.float64), C * np.cos(hr), C * np.sin(hr)], -1))


def colour_stats(ring):
    """Mean ring colour in CIELCh and the colour class ("dark_brown", "grey" or "own")."""
    mean = np.asarray(ring, np.float64).mean(0)
    Ls, C, h = (float(v) for v in lch(mean))
    if Ls < DARK_BROWN_L and DARK_BROWN_HUE[0] <= h <= DARK_BROWN_HUE[1]:
        cls = "dark_brown"
    elif C < GREY_C:
        cls = "grey"
    else:
        cls = "own"
    return {"class": cls, "L": round(Ls, 2), "C": round(C, 2), "h": round(h, 1),
            "mean_rgb": [round(float(v) * 255, 1) for v in mean]}


def colour_class(ring_or_eye):
    """'dark_brown' | 'grey' | 'own' (see colour_stats). Takes a ring or anything with a .ring."""
    ring = getattr(ring_or_eye, "ring", ring_or_eye)
    return colour_stats(ring)["class"]


# ----------------------------------------------------------------------------- palette helpers
def rgb01(c):
    """A colour as float32 RGB 0..1 from '#RRGGBB', a 0..255 tuple (any int in it or any value > 1) or 0..1 floats."""
    if isinstance(c, str):
        h = c.lstrip("#")
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0
    a = np.asarray(c, np.float32)
    if a.dtype.kind in "iu" or (isinstance(c, (tuple, list)) and any(isinstance(v, int) for v in c)) or a.max() > 1.0:
        return a / 255.0
    return a


def boost(c, lift=1.6, sat=1.5):
    """Brighter and richer version of a colour (or a (..., 3) palette), 0..1: grey + (c - grey) * sat, times lift.
    Clamped hue-preserving: a colour pushed past 1 is scaled down as a whole (not clipped per channel, which would
    shift its hue), a channel pushed below 0 is set to 0."""
    c = np.asarray(c, np.float32)
    g = c.mean(-1, keepdims=True)
    o = np.maximum((g + (c - g) * sat) * lift, 0.0)
    m = o.max(-1, keepdims=True)
    return (o / np.maximum(m, 1.0)).astype(np.float32)


def mix(a, b, t):
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    return (a * (1.0 - t) + b * t).astype(np.float32)


def hue_shift(c, deg):
    """Rotate hue in CIELCh by deg (the duo rule for two same-coloured eyes), same L* and C*."""
    Ls, C, h = lch(c)
    return from_lch(Ls, C, (h + deg) % 360.0).astype(np.float32)


def colour_distance(a, b):
    """CIEDE2000 between two 0..1 colours (mean ring colours for the duo rule)."""
    return float(L.ciede2000(L.srgb_to_lab(np.asarray(a) * 255.0), L.srgb_to_lab(np.asarray(b) * 255.0)))


def effect_palette(eye_or_ring, lift=1.6, sat=1.4, fallback=None, cls=None, hue_deg=0.0):
    """The per-angle effect palette (RING_BINS, 3) of one eye: boost(ring, lift, sat), then the style's fallback
    for the special classes. fallback maps class -> (colour, t) meaning mix t toward colour, or -> dict with
    optional lift, sat, toward, t (e.g. Supernova dark brown: {'lift': 1.8, 'sat': 1.5, 'toward': '#D98A3D',
    't': 0.35}). hue_deg rotates the palette (duo rule). Returns float32 0..1."""
    ring = np.asarray(getattr(eye_or_ring, "ring", eye_or_ring), np.float32)
    cls = cls or colour_class(ring)
    spec = (fallback or {}).get(cls)
    if isinstance(spec, dict):
        lift, sat = spec.get("lift", lift), spec.get("sat", sat)
    p = boost(ring, lift, sat)
    if spec is not None:
        toward, t = (spec.get("toward"), spec.get("t", 0.0)) if isinstance(spec, dict) else spec
        if toward is not None and t:
            p = mix(p, rgb01(toward)[None, :], t)
    if hue_deg:
        p = hue_shift(p, hue_deg)
    return p.astype(np.float32)


def palette_lut(pal, n=LUT_N):
    """(n, 3) float32 circular lookup of a (bins, 3) palette, linearly interpolated between bin centres."""
    pal = np.asarray(pal, np.float32)
    bins = pal.shape[0]
    x = (np.arange(n) + 0.5) * (bins / n) - 0.5
    return np.stack([np.interp(x, np.arange(bins), pal[:, c], period=bins) for c in range(3)], 1).astype(np.float32)


def angle_index(theta, n=LUT_N):
    """Per-pixel index into a palette_lut (or angular_lut) for theta (radians, -pi..pi); n a power of two."""
    idx = (theta * np.float32(n / TWO_PI) + np.float32(n)).astype(np.int32)
    idx &= n - 1
    return idx


def angular_lut(prof, n=LUT_N):
    """(n,) float32 circular lookup of a 1-D angular profile of any length, linear between its samples (sample k at
    angle k / len * 360 deg)."""
    prof = np.asarray(prof, np.float64)
    m = len(prof)
    x = (np.arange(n) + 0.5) * (m / n)
    return np.interp(x, np.arange(m), prof, period=m).astype(np.float32)


def tint(intensity, lut, theta, out=None, k=1.0, idx=None):
    """intensity (H, W) x the palette colour at each pixel's angle -> (H, W, 3) float32 light (added into out when
    given). lut from palette_lut(); idx = angle_index(theta) when already computed."""
    col = lut[angle_index(theta, lut.shape[0]) if idx is None else idx]
    col *= (intensity if k == 1.0 else intensity * np.float32(k))[..., None]
    if out is None:
        return col
    out += col
    return out


def ring_at(pal, theta):
    """The palette colour at angle(s) theta (radians), linear between bin centres: (..., 3) float32."""
    theta = np.asarray(theta, np.float64)
    n = pal.shape[0]
    f = (theta * (n / TWO_PI)) % n - 0.5
    i0 = np.floor(f).astype(np.int64)
    w = (f - i0)[..., None]
    i0 %= n
    return (pal[i0] * (1 - w) + pal[(i0 + 1) % n] * w).astype(np.float32)


# ----------------------------------------------------------------------------- OKLab (numpy)
_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
_M1I = np.linalg.inv(_M1)
_M2I = np.linalg.inv(_M2)


def srgb_to_oklch(rgb):
    rgb = np.asarray(rgb, np.float64)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    lms = np.cbrt(lin @ _M1.T)
    lab = lms @ _M2.T
    return lab[..., 0], np.hypot(lab[..., 1], lab[..., 2]), np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360.0


def oklch_to_srgb(L_, Cc, h, gamut_steps=8):
    """OKLCH -> sRGB 0..1, chroma reduced (not clipped) until the colour fits the gamut."""
    L_ = np.asarray(L_, np.float64)
    Cc = np.asarray(Cc, np.float64) * np.ones_like(L_)
    hr = np.radians(h) * np.ones_like(L_)
    scale = np.ones_like(L_)
    out = None
    for it in range(gamut_steps):
        a = Cc * scale * np.cos(hr)
        b = Cc * scale * np.sin(hr)
        lab = np.stack([L_, a, b], -1)
        lms = (lab @ _M2I.T) ** 3
        lin = lms @ _M1I.T
        bad = (lin.min(-1) < -0.0005) | (lin.max(-1) > 1.0005)
        out = lin
        if not bad.any():
            break
        scale = np.where(bad, scale * 0.86, scale)
    lin = np.clip(out, 0.0, 1.0)
    return np.where(lin > 0.0031308, 1.055 * np.maximum(lin, 1e-9) ** (1 / 2.4) - 0.055, 12.92 * lin).astype(np.float32)


COPPER = ["#3B1C0C", "#8A4A1F", "#C98545", "#F0C48C"]
SILVER = ["#2A2E33", "#6E7680", "#B8C0C8", "#EEF2F5"]


def _lab_of_hex(hexes):
    rgb = np.stack([rgb01(h) for h in hexes]).astype(np.float64)
    L_, Cc, h = lch(rgb)
    lab = np.stack([L_, Cc * np.cos(np.radians(h)), Cc * np.sin(np.radians(h))], -1)
    return lab


_COPPER_LAB = _lab_of_hex(COPPER)
_SILVER_LAB = _lab_of_hex(SILVER)


def _ramp(lab, s):
    """Piecewise linear position s in 0..1 along a 4-stop Lab ramp -> (n, 3) Lab."""
    s = np.clip(s, 0.0, 1.0) * (len(lab) - 1)
    i0 = np.minimum(np.floor(s).astype(np.int64), len(lab) - 2)
    f = (s - i0)[:, None]
    return lab[i0] * (1 - f) + lab[i0 + 1] * f


def _lab_to_rgb(lab):
    return lab_to_srgb(lab).astype(np.float32)


class Pal:
    """Colour source of one iris (cx_palette.Pal). hue_deg rotates the effect hue (same-class neighbours). Takes anything with
    .ring (360 x 3, 0..1), .cls and .stats (the colour_stats dict)."""

    def __init__(self, eye, hue_deg=0.0):
        ring = np.asarray(eye.ring, np.float32)
        self.cls = eye.cls
        L_, Cc, h = lch(ring)
        self.L = np.asarray(L_, np.float64)
        self.C = np.asarray(Cc, np.float64)
        self.h = (np.asarray(h, np.float64) + hue_deg) % 360.0
        self.ring = ring
        st = eye.stats
        self.mL, self.mC, self.mh = st["L"], st["C"], (st["h"] + hue_deg) % 360.0
        self.hue_deg = hue_deg
        okL, okC, okh = srgb_to_oklch(ring)
        self.ok_L, self.ok_C, self.ok_h = np.asarray(okL), np.asarray(okC), (np.asarray(okh) + hue_deg) % 360.0
        self.ok_mC = float(np.mean(self.ok_C))

    def _bin(self, phi):
        return (np.floor(np.degrees(phi) % 360.0).astype(np.int64)) % 360

    def chips(self, phi, u, v, w=None):
        """(n, 3) float32 sRGB 0..1 of lit chips. phi: emission angle (radians, screen clockwise), u, v: uniform 0..1 draws
        (lightness, chroma), w: another uniform for hue jitter."""
        n = len(phi)
        b = self._bin(phi)
        L0, C0, h0 = self.L[b], self.C[b], self.h[b]
        if w is None:
            w = np.full(n, 0.5)
        if self.cls == "dark_brown":
            s = 0.30 + 0.70 * u ** 0.75
            lab = _ramp(_COPPER_LAB, s)
            # keep a little of the local ring hue: chips off a copper rim differ by angle
            Lc = lab[:, 0]
            Cc = np.hypot(lab[:, 1], lab[:, 2])
            hh = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) + self.hue_deg + 0.35 * ((h0 - self.mh + 180.0) % 360.0 - 180.0) + 8.0 * (w - 0.5)
            Cc = Cc * (0.85 + 0.30 * v)
            lab = np.stack([Lc, Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))], -1)
            return _lab_to_rgb(lab)
        if self.cls == "grey":
            s = 0.45 + 0.55 * u ** 0.8
            lab = _ramp(_SILVER_LAB, s)
            Lc = lab[:, 0]
            tint_c = np.minimum(C0, 16.0) * 0.30 * (0.6 + 0.8 * v)
            a = lab[:, 1] + tint_c * np.cos(np.radians(h0))
            b_ = lab[:, 2] + tint_c * np.sin(np.radians(h0))
            return _lab_to_rgb(np.stack([Lc, a, b_], -1))
        # own colours: OKLCH, hue and chroma of the ring at this angle, lightness 0.50-0.92 (brighter chips are rarer), chroma kept
        # (a lit chip of a warm iris is ochre or orange, never pastel pink)
        L0, C0, h0 = self.ok_L[b], self.ok_C[b], self.ok_h[b]
        Lc = np.clip(L0 + 0.08 + 0.20 * u ** 1.3, 0.54, 0.90)
        keep = np.clip(1.10 - 0.55 * (Lc - 0.54) / 0.36, 0.5, 1.10)
        Cc = np.minimum(np.maximum(C0, 0.5 * self.ok_mC) * keep * 1.25 * (0.85 + 0.30 * v), 0.17)
        hh = h0 + 6.0 * (w - 0.5) * 2.0 + self.hue_deg * 0.0
        return oklch_to_srgb(Lc, Cc, hh)

    def chips2(self, phi, u, v, w=None):
        """Round 2c chip colours (AD fixes A6): lit powder of the eye's OWN ring colour at the emission angle, OKLCH lightness 0.64-0.88 (cap
        0.88: no near-white glass), chroma floor C* about 14 in the ring hue (0.055), pure white at most 6 % of the chips (the highlight facet
        is added by the rasteriser), dark brown = copper ramp with 15 % deep dim copper, grey = silver ramp capped at L about 84 with a tint of
        the local ring hue. (n, 3) float32 sRGB 0..1. The per-chip luminance factor 0.35-1.0 is applied by the rasteriser."""
        n = len(phi)
        b = self._bin(phi)
        if w is None:
            w = np.full(n, 0.5)
        L0, C0, h0 = self.L[b], self.C[b], self.h[b]
        if self.cls == "dark_brown":
            s_ = 0.22 + 0.72 * u ** 0.8
            deep = v < 0.15                                   # 15 % deep copper (dim) chips
            s_ = np.where(deep, 0.12 + 0.18 * w, s_)
            lab = _ramp(_COPPER_LAB, s_)
            Lc = lab[:, 0]
            Cc = np.hypot(lab[:, 1], lab[:, 2])
            hh = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) + self.hue_deg + 0.35 * ((h0 - self.mh + 180.0) % 360.0 - 180.0) + 8.0 * (w - 0.5)
            Cc = Cc * (0.90 + 0.25 * v)
            lab = np.stack([Lc, Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))], -1)
            return _lab_to_rgb(lab)
        if self.cls == "grey":
            s_ = 0.40 + 0.46 * u ** 0.9                      # stops at 0.86 of the ramp: silver, never the near-white end
            lab = _ramp(_SILVER_LAB, s_)
            Lc = lab[:, 0]
            tint_c = np.clip(C0, 9.0, 17.0) * 0.60 * (0.7 + 0.6 * v)
            a = lab[:, 1] + tint_c * np.cos(np.radians(h0))
            b_ = lab[:, 2] + tint_c * np.sin(np.radians(h0))
            return _lab_to_rgb(np.stack([Lc, a, b_], -1))
        L0o, C0o, h0o = self.ok_L[b], self.ok_C[b], self.ok_h[b]
        Lc = np.clip(L0o + 0.08 + 0.18 * u ** 1.3, 0.60, 0.88)
        keep = np.clip(1.10 - 0.50 * (Lc - 0.60) / 0.28, 0.55, 1.10)
        Cc = np.clip(np.maximum(C0o, 0.55 * self.ok_mC) * keep * 1.40 * (0.85 + 0.30 * v), 0.060, 0.150)
        hh = h0o + 10.0 * (w - 0.5)
        return oklch_to_srgb(Lc, Cc, hh)

    def haze(self, phi, u, v):
        """Darker, richer haze colours (L 45-65, chroma x1.2, brief 1.5.2 haze palette)."""
        b = self._bin(phi)
        C0, h0 = self.C[b], self.h[b]
        if self.cls == "dark_brown":
            lab = _ramp(_COPPER_LAB, 0.35 + 0.35 * u)
            return _lab_to_rgb(lab)
        if self.cls == "grey":
            lab = _ramp(_SILVER_LAB, 0.35 + 0.35 * u)
            return _lab_to_rgb(lab)
        Lc = 45.0 + 20.0 * u
        Cc = np.clip(C0 * 1.2 * (0.85 + 0.3 * v), 8.0, 70.0)
        lab = np.stack([Lc, Cc * np.cos(np.radians(h0)), Cc * np.sin(np.radians(h0))], -1)
        return _lab_to_rgb(lab)

    def at(self, phi):
        """The ring colour at angle phi (0..1 RGB)."""
        return ring_at(self.ring, phi)


def pair_hues(eyes):
    """Hue rotations (deg) for a set of eyes: a second eye of the same class and near colour rotates 12-20 deg
    (v2 rule); returns a list of floats."""
    out = []
    means = []
    for e in eyes:
        means.append(np.asarray(e.stats["mean_rgb"], np.float64) / 255.0)
    for i, e in enumerate(eyes):
        rot = 0.0
        for j in range(i):
            if e.cls == eyes[j].cls:
                de = colour_distance(means[i], means[j])
                if de < 10.0:
                    rot = 20.0 if (i % 2) else -20.0
        out.append(rot)
    return out


# ----------------------------------------------------------------------------- the secondary hue (H2 of the brief)
def secondary_hue(sq, ring, stats):
    """(rgb 0..1 accent colour, how, hue deg, chroma): H2 of the brief. The design code's secondary_hue returns the first three; the
    chroma is added so that the profile can store the accent as numbers. The collarette median (0.35-0.55 R of the canonical grade)
    when it is more than dE00 12 from the ring median, else the analogous hue +25 deg of the ring. The returned colour is lifted
    to a light, clean accent (L* 80, C* limited), never a new hue family. sq: the tight graded disc square (uint8, the canonical
    256 grade), ring: the eye's ring colours, stats: colour_stats(ring)."""
    tgt = sq.shape[0]
    R = tgt / 2.0
    ax = np.arange(tgt) + 0.5 - R
    rho = np.hypot(ax[None, :], ax[:, None]) / R
    m = (rho > 0.35) & (rho < 0.55)
    px = sq[m].astype(np.float64)
    lab = L.srgb_to_lab(px)
    med = np.median(lab, 0)
    ringm = np.asarray(ring).mean(0).astype(np.float64)
    ring_lab = L.srgb_to_lab((ringm * 255.0)[None, :])[0]
    de = float(L.ciede2000(med[None, :], ring_lab[None, :])[0])
    Cc = float(np.hypot(med[1], med[2]))
    hh = float(np.degrees(np.arctan2(med[2], med[1])) % 360.0)
    if de > 12.0 and Cc > 8.0:
        how = "collarette"
        h2 = hh
        c2 = min(max(Cc * 1.15, 20.0), 52.0)
    else:
        how = "analogous"
        h2 = (stats["h"] + 25.0) % 360.0
        c2 = min(max(stats["C"] * 1.1, 18.0), 50.0)
    return from_lch(80.0, c2, h2).astype(np.float32), how, h2, c2


def secondary_rgb(hue, chroma):
    """The accent colour of a secondary hue (hue deg, chroma): L* 80, as secondary_hue() returns it (float32 0..1)."""
    return from_lch(80.0, chroma, hue).astype(np.float32)
