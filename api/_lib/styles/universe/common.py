# -*- coding: utf-8 -*-
"""uni_common: shared pieces of the UNIVERSE family (scratch prototype, NOT repo code). numpy + PIL only.

  Src          per-eye source prepared once: graded disc (float), polar-mirror EXTENSION E for enlargement, pupil,
               gradient ramp built from the eye's own pixels, secondary hue H2, colour class. Cached on the Iris.
  f3_disc()    a fx.core.Disc with the brief's F3 feather (alpha 1 for r <= 0.985 R, smoothstep to 0 at 1.015 R)
  enlarge()    banded affine (scale about the iris centre) sampling of E, PIL bicubic in mode F: fast, no scipy
  ramp_rgb()   gradient map luminance -> the eye's own colours
Everything is sized in R (iris radius) or S (canvas short side), so 1024 and 4096 are one picture.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_common.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports; the memory meter is guard.memory_now()); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np
from PIL import Image

from .. import core as C
from .. import pupil as PUP

L = C.L

FILL_SD = 1024                       # graded frame the fill is sampled from (R_src about 481 px); groups of 3+ use GROUP_FILL_SD (the fill is enlarged x3.5 anyway, and a 6-eye 4K master spends 0.6 s per eye grading it)
GROUP_FILL_SD = 768
F3_LO, F3_HI = 0.985, 1.015          # brief 1.5.1
RHO_EDGE = 0.985                     # extension mirrors at this normalised radius (the disc's own edge is soft)
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def luma(a):
    return a[..., 0] * LUMA[0] + a[..., 1] * LUMA[1] + a[..., 2] * LUMA[2]


# ----------------------------------------------------------------------------- the F3 disc
class UDisc(C.Disc):
    """fx.core.Disc plus the straight float colour of the tile (0..255, with the F3 skirt) for the overlap compositor."""
    __slots__ = ("rgb", "pup")


def f3_disc(iris, cx, cy, R, index=0):
    """core.place_disc, then the F3 feather: the colour beyond 0.99 R is the radial clamp of the colour at 0.99 R (nothing
    invented: the limbal ring's own dark edge continues), alpha follows F3. Pixels with r <= 0.985 R are the graded
    pixels byte for byte (the old alpha is exactly 1 there). The array is padded so the F3 skirt (to 1.015 R) fits."""
    d0 = C.place_disc(iris, cx, cy, R, index)
    t = d0.g.shape[0]
    Rp = t / 2.0
    pad = int(math.ceil(0.02 * Rp)) + 1
    T = t + 2 * pad
    a_old = np.asarray(d0.alpha, np.float32)
    g = d0.g.astype(np.float32)
    ax = np.arange(T, dtype=np.float32) + 0.5 - T / 2.0
    dx, dy = ax[None, :], ax[:, None]
    rho = np.sqrt(dx * dx + dy * dy) / np.float32(Rp)
    out = np.zeros((T, T, 3), np.float32)
    inside = rho <= 0.99
    # colour u = g / alpha_old for the unpadded grid (reliable while alpha_old >= 0.3, i.e. rho <= 0.996)
    u = g / np.maximum(a_old, 0.3)[..., None]
    out[pad:pad + t, pad:pad + t] = np.where((rho[pad:pad + t, pad:pad + t] <= 0.99)[..., None], u, 0.0)
    ring = ~inside
    if ring.any():
        yy, xx = np.nonzero(ring)
        px = (xx + 0.5 - T / 2.0).astype(np.float32)
        py = (yy + 0.5 - T / 2.0).astype(np.float32)
        r = np.sqrt(px * px + py * py)
        k = np.float32(0.99 * Rp) / np.maximum(r, 1e-3)
        sx = px * k + t / 2.0 - 0.5          # array coords in the unpadded frame (pixel centres at integers)
        sy = py * k + t / 2.0 - 0.5
        x0 = np.clip(np.floor(sx).astype(np.int64), 0, t - 2)
        y0 = np.clip(np.floor(sy).astype(np.int64), 0, t - 2)
        fx, fy = (sx - x0)[:, None], (sy - y0)[:, None]
        col = (u[y0, x0] * (1 - fx) * (1 - fy) + u[y0, x0 + 1] * fx * (1 - fy) + u[y0 + 1, x0] * (1 - fx) * fy
               + u[y0 + 1, x0 + 1] * fx * fy)
        out[yy, xx] = col
    alpha = 1.0 - smooth((rho - F3_LO) / (F3_HI - F3_LO))
    alpha = alpha.astype(np.float32)
    gp = out * alpha[..., None]
    g8 = np.clip(np.rint(gp), 0, 255).astype(np.uint8)
    # byte-exact original pixels wherever the old alpha was 1
    core_ok = (rho[pad:pad + t, pad:pad + t] <= 0.985)
    sub = g8[pad:pad + t, pad:pad + t]
    sub[core_ok] = d0.g[core_ok]
    d = UDisc()
    d.pup = None
    d.iris, d.index, d.Sd = iris, index, d0.Sd
    d.g = np.ascontiguousarray(g8)
    d.rgb = out                                   # straight (not premultiplied) float colour 0..255 incl. the F3 skirt
    d.alpha = alpha
    d.x0, d.y0 = d0.x0 - pad, d0.y0 - pad
    d.cx, d.cy, d.R = d0.cx, d0.cy, d0.R
    return d


# ----------------------------------------------------------------------------- per-eye source
class Src:
    """The eye as material. g: graded disc float32 0..1 (tgt, tgt, 3) at FILL_SD; R: its radius px."""

    def __init__(self, iris, fill_sd=None):
        self.iris = iris
        fr = iris.graded(fill_sd or FILL_SD)
        sq, tgt = C._tight(fr)
        self.tgt = tgt
        self.R = tgt / 2.0
        self.g = (sq.astype(np.float32) / 255.0)
        ax = (np.arange(tgt, dtype=np.float32) + 0.5 - self.R) / np.float32(self.R)
        self.rho = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)
        self.theta = np.arctan2(np.broadcast_to(ax[:, None], self.rho.shape), np.broadcast_to(ax[None, :], self.rho.shape))
        self.Y = luma(self.g)
        self.pup = PUP.analyse(sq)                       # dict: rp (units of R), cls, cx, cy
        self.r_p = float(self.pup["rp"])
        self.cls = iris.cls
        self.stats = iris.stats
        self._ext = {}
        self._ramp = None
        self._h2 = None

    # -- extension E: the disc, mirrored radially beyond RHO_EDGE, out to rho_max
    def extended(self, rho_max):
        key = round(rho_max, 2)
        e = self._ext.get(key)
        if e is not None:
            return e
        M = int(math.ceil(2.0 * rho_max * self.R)) + 2
        M += M % 2
        ax = np.arange(M, dtype=np.float32) + 0.5 - M / 2.0
        dx, dy = ax[None, :], ax[:, None]
        r = np.sqrt(dx * dx + dy * dy)
        rho = r / np.float32(self.R)
        a = np.float32(RHO_EDGE)
        m = np.mod(rho, 2 * a)
        rho2 = np.where(m <= a, m, 2 * a - m)
        k = rho2 / np.maximum(rho, 1e-6)
        sx = dx * k + self.tgt / 2.0 - 0.5
        sy = dy * k + self.tgt / 2.0 - 0.5
        sx = np.clip(sx, 0, self.tgt - 1.001)
        sy = np.clip(sy, 0, self.tgt - 1.001)
        x0 = np.floor(sx).astype(np.int32)
        y0 = np.floor(sy).astype(np.int32)
        fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
        g = self.g
        E = (g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x0 + 1] * fx * (1 - fy) + g[y0 + 1, x0] * (1 - fx) * fy
             + g[y0 + 1, x0 + 1] * fx * fy).astype(np.float32)
        self._ext[key] = (E, M)
        return self._ext[key]

    # -- gradient ramp from the eye's own pixels, luminance quantiles -> (L*, C*, h)
    @property
    def ramp(self):
        if self._ramp is None:
            m = (self.rho > 0.38) & (self.rho < 0.92)
            px = self.g[m]
            Y = luma(px)
            o = np.argsort(Y)
            px = px[o]
            K = 48
            edges = np.linspace(0, len(px), K + 1).astype(np.int64)
            cols = np.stack([px[edges[i]:edges[i + 1]].mean(0) for i in range(K)], 0)
            Ls, Cc, hh = C.lch(cols)
            # smooth the hue circularly and the rest linearly
            def sm(v, circ=False):
                k = np.array([1, 2, 3, 2, 1], np.float32)
                k /= k.sum()
                if circ:
                    z = np.exp(1j * np.radians(v))
                    p = np.concatenate([np.repeat(z[:1], 2), z, np.repeat(z[-1:], 2)])
                    return np.degrees(np.angle(np.convolve(p, k, "valid"))) % 360.0
                p = np.concatenate([np.repeat(v[:1], 2), v, np.repeat(v[-1:], 2)])
                return np.convolve(p, k, "valid")
            self._ramp = (sm(Ls), sm(Cc), sm(hh, True))
        return self._ramp

    @property
    def h2(self):
        """(hue deg, chroma) of the secondary hue: the ring colour bins farthest in hue from the mean, chroma-weighted;
        if none is 35+ deg away, the warm complement at low chroma."""
        if self._h2 is None:
            ring = self.iris.ring
            Ls, Cc, hh = C.lch(ring)
            h0 = self.stats["h"]
            dh = (hh - h0 + 180.0) % 360.0 - 180.0
            w = Cc * (np.abs(dh) > 35.0)
            if w.sum() > 0.08 * Cc.sum() and Cc.max() > 12.0:
                z = (w * np.exp(1j * np.radians(hh))).sum()
                self._h2 = (float(np.degrees(np.angle(z)) % 360.0), float(min(60.0, np.average(Cc, weights=w + 1e-6) * 1.2)))
            else:
                dw = (55.0 - h0 + 180.0) % 360.0 - 180.0
                self._h2 = ((55.0 if abs(dw) > 40 else (h0 + 160.0) % 360.0), 18.0)
        return self._h2

    def ring_at(self, theta):
        return C.ring_at(self.iris.ring, theta)


def ramp_rgb(src, t, Lmin=2.0, Lmax=92.0, gamma=1.0, gain=1.0, cmax=95.0):
    """Gradient map: t in 0..1 (any shape) -> sRGB 0..1 (..., 3), the eye's own hue and chroma per luminance quantile,
    lightness set by t (L* = Lmin + (Lmax - Lmin) t^gamma), chroma x gain, capped."""
    Lq, Cq, hq = src.ramp
    K = len(Lq)
    t = np.clip(np.asarray(t, np.float32), 0.0, 1.0)
    pos = t * (K - 1)
    i0 = np.minimum(pos.astype(np.int32), K - 2)
    f = pos - i0
    Cc = (Cq[i0] * (1 - f) + Cq[i0 + 1] * f) * gain
    # hue: interpolate on the circle
    z0, z1 = np.exp(1j * np.radians(hq[i0])), np.exp(1j * np.radians(hq[i0 + 1]))
    h = np.degrees(np.angle(z0 * (1 - f) + z1 * f))
    Ls = Lmin + (Lmax - Lmin) * np.power(t, gamma)
    # chroma is limited near black and white so the colour stays in gamut
    Cc = np.minimum(Cc, cmax) * np.clip(np.minimum(Ls / 22.0, (104.0 - Ls) / 26.0), 0.0, 1.0)
    return C.from_lch(Ls, Cc, h % 360.0).astype(np.float32)


def limb_L(src):
    """Median L* of the source iris's limb ring 0.90-0.98 R (cached on the Src)."""
    v = getattr(src, "_limb_Lv", None)
    if v is None:
        m = (src.rho > 0.90) & (src.rho < 0.98)
        lin = np.power(src.g[m], 2.2)
        Y = float(np.median(lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)))
        v = float(116.0 * Y ** (1 / 3) - 16.0) if Y > 0.008856 else 903.3 * Y
        src._limb_Lv = v
    return v


def get_src(iris, n_eyes=1):
    """The per-eye source, cached on the Iris per frame size (1024 for one or two eyes, 768 for groups)."""
    sd = FILL_SD if n_eyes <= 2 else GROUP_FILL_SD
    d = getattr(iris, "_uni_srcs", None)
    if d is None:
        d = iris._uni_srcs = {}
    s = d.get(sd)
    if s is None:
        s = Src(iris, sd)
        d[sd] = s
    return s


# ----------------------------------------------------------------------------- banded affine enlargement
class EImgs:
    """An extended source held as three PIL float images (what the affine transform needs); .array() rebuilds the (M, M, 3) float array."""

    def __init__(self, arr):
        self.imgs = [Image.fromarray(np.ascontiguousarray(arr[..., c]), "F") for c in range(3)]

    def array(self):
        return np.stack([np.asarray(im, np.float32) for im in self.imgs], -1)


def _channel_images(E):
    return E.imgs if isinstance(E, EImgs) else EImgs(E).imgs


def enlarge_band(E, M, cx, cy, s, y0, y1, W):
    """Rows y0..y1 of the canvas sampled from the extended source E (M x M x 3, centre at (M/2, M/2) in continuous coords)
    scaled by s canvas px per source px about the canvas point (cx, cy). PIL bicubic, mode F per channel."""
    h = y1 - y0
    a = 1.0 / s
    c0 = M / 2.0 - cx / s
    f0 = M / 2.0 - (cy - y0) / s
    out = np.empty((h, W, 3), np.float32)
    coeffs = (a, 0.0, c0, 0.0, a, f0)
    for k, im in enumerate(_channel_images(E)):
        o = im.transform((W, h), Image.AFFINE, coeffs, resample=Image.BICUBIC)
        out[..., k] = np.asarray(o, np.float32)
    np.clip(out, 0.0, 1.0, out=out)
    return out


def hex_to_rgb(h):
    return C.rgb01(h)


def peak_rss_mb():
    """The high-water mark of this process's resident memory in MB, or None where the platform says nothing (api/_lib/styles/guard.py reads it: /proc on
    Linux, psapi on Windows; psutil is not a dependency)."""
    try:
        from .. import guard
        hwm = guard.memory_now()[1]
        return None if hwm is None else round(hwm)
    except Exception:
        return None
