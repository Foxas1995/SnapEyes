# -*- coding: utf-8 -*-
"""HALO (the light family; a corona since 2026-10-28, after the owner's "more around the iris, not spoiling it; the iris itself touched by a few pixels at
most" and his reference board, where an eclipse corona of fine streamers stands round an untouched iris). The iris is the moon of a total eclipse and its
own colours are the corona.

The iris stays whole: the engine pastes it last, byte for byte inside 0.974 R, with the family's F3 feather at the limb, and its finish keeps only a light
limbal shade (DESIGN_FIN in __init__.py), the dark edge of the moon. Round it, on pure black, a corona of thousands of fine radial streamers: each angle takes
the colour of the iris's own outer band at that angle (0.84 to 0.965 R, the brightest four of six samples, so no crypt and no lash shadow), lifted toward a
light of the same hue, and a touch of warm white close to the limb. The light falls with the distance as rho^-p, as a real corona does: steeply in the quiet
sectors, slowly in a few broad lobes where the streamers reach further; three families of streamers (many fine short ones, fewer middle ones, a few long
ones) fall at their own rates, bundles of them are brighter and longer than their neighbours, and they bend a little with the distance. A smooth inner
corona, textured by the same fine streamers, closes the gaps right at the limb, so no dark seam and no ring of light separate the iris from its corona.
A faint field of stars lies beyond. No plate, no tonal ground, no rim line.

Every length is in R, every count is fixed (the angular tables have HP["n"] samples whatever the canvas): the light is a function of (rho, theta) evaluated
at every pixel in row bands, and the tables are only blurred by half a pixel's angular footprint at the limb, so a 4096 px master is its 1024 px preview
drawn finer (the same streamers at the same angles) and no full size float layer exists beside the canvas.
"""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from .. import matter as M
from ..singles import kit as K
from . import common as CM

F32 = np.float32
TWO_PI = 2.0 * math.pi
LUMW = np.array([0.299, 0.587, 0.114], np.float64)
HP = {
    "n": 8192,                          # samples of every angular table round the circle (fixed: the same tables at every size)
    "src": (0.84, 0.965),               # the band of the iris whose colours the corona takes (R)
    "anchor": 0.25,                     # share of the band's mean colour in every angle's colour (one stray hue does not take over a sector)
    "col_sigma": 0.010,                 # angular blur of the colour table (rad)
    "lift": (0.40, 0.55, 1.15),         # the light's colour: luminance target, share of the lift toward it, saturation
    "rays": ((3600, 0.0006, 0.0022), (900, 0.0012, 0.0045), (50, 0.0020, 0.0060)),   # the streamer families: count, Gaussian half width lo, hi (rad)
    "weights": (0.62, 0.31, 0.07),      # their shares of the streamers' light at the limb
    "fall": (5.0, 11.0),                # the light falls as rho^-p: p in the lobes, p in the quiet sectors
    "fall_d": (2.5, 0.5, -0.5),         # each family falls this much faster (negative: further); multiples of a half are cheapest
    "lobes": 4,                         # cells of the broad lobes round the circle
    "clump": (22, 0.35, 2.5),           # bundles: cells round the circle, depth of their strength, how much further a bright bundle reaches (in p)
    "bend": 0.06,                       # the streamers bend by this many radians per R of distance, toward the lobes' own drift
    "inner": (0.45, 5.0, 0.6),          # the smooth inner corona: share of the light at the limb, its extra fall (in p), how much the fine streamers texture it
    "white": 0.22,                      # the corona turns this much toward warm white where its inner part is strong (it fades with it)
    "gain": 1.25,                       # the light at the limb over the lifted colour
    "reach": 2.9,                       # the window of the corona (R)
    "stars": (2600, (0.0, 8.0), 1.1),   # field stars per S^2, their magnitudes, the core of the brightest (0 stars: none)
}
WARM = (1.0, 0.96, 0.88)


def _circ_blur(a, sigma):
    """Circular Gaussian blur of a table (n,) or (n, c), sigma in radians, exact (by FFT)."""
    a = np.asarray(a, np.float64)
    m = np.arange(a.shape[0] // 2 + 1, dtype=np.float64)
    k = np.exp(-0.5 * (m * float(sigma)) ** 2)
    f = np.fft.rfft(a, axis=0)
    f *= k[:, None] if a.ndim == 2 else k
    return np.fft.irfft(f, n=a.shape[0], axis=0)


def band_colours(d, n, src):
    """(n, 3) float64: the iris's own colour per angle in its outer band, the mean of the brightest four of six samples across the band."""
    th = (np.arange(n) + 0.5) * (TWO_PI / n)
    rs = np.linspace(src[0], src[1], 6)
    cols = K.sample_disc(d, np.broadcast_to(rs[None, :], (n, 6)), np.broadcast_to(th[:, None], (n, 6))).astype(np.float64)
    order = np.argsort(cols @ LUMW, axis=1)[:, 2:]
    return np.take_along_axis(cols, order[..., None], 1).mean(1)


def lift(col, target, share, sat):
    """A colour per angle made light: its luminance moved toward target by share (in log), its saturation scaled by sat (hue kept)."""
    lum = np.maximum(col @ LUMW, 0.02)
    out = col * ((target / lum) ** share)[:, None]
    l2 = out @ LUMW
    return np.clip(l2[:, None] + (out - l2[:, None]) * sat, 0.0, None)


def ray_table(rnd, n, count, w0, w1):
    """(n,) of mean 1: count streamers at random angles, Gaussian across, half widths log uniform in w0..w1 (rad), strengths from a steep draw. All the
    numbers are drawn before anything is computed from them."""
    c = rnd.uniform(count) * TWO_PI
    w = w0 * (w1 / w0) ** rnd.uniform(count)
    s = 0.15 + 0.85 * rnd.uniform(count) ** 2.0
    binw = TWO_PI / n
    k = int(math.ceil(4.0 * w1 / binw)) + 1
    j = np.floor(c / binw).astype(np.int64)[:, None] + np.arange(-k, k + 1)[None, :]
    v = s[:, None] * np.exp(-0.5 * ((j * binw - c[:, None]) / w[:, None]) ** 2)
    tab = np.bincount((j % n).ravel(), weights=v.ravel(), minlength=n)
    return tab / max(tab.mean(), 1e-12)


def _rpow(inv, sq, rho, x):
    """rho^-x from 1 / rho and its square root: products when x is a multiple of a half (the usual case), the power otherwise."""
    m = int(round(2.0 * x))
    if abs(2.0 * x - m) > 1e-9:
        return np.power(rho, F32(-x))
    k, half = divmod(abs(m), 2)
    base = inv if m > 0 else rho
    out = None
    for _ in range(k):
        out = base if out is None else out * base
    if half:
        h = sq if m > 0 else F32(1.0) / sq
        out = h if out is None else out * h
    return np.ones_like(inv) if out is None else out


def _norm01(a):
    a = np.asarray(a, np.float64)
    return (a - a.min()) / max(float(a.max() - a.min()), 1e-12)


def fx_halo(cv, ctx):
    o = dict(HP)
    o.update(ctx.opts.get("halo", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    R = float(d.R)
    n = int(o["n"])
    # ---- the tables (every random draw first, at a fixed size)
    lob = _norm01(C.periodic_fbm1d(n, ctx.rand("halo_lobes"), 3, int(o["lobes"]), 0.55))
    ccells, cdep, cdp = o["clump"]
    cl = _norm01(C.periodic_fbm1d(n, ctx.rand("halo_clump"), 3, int(ccells), 0.6))
    rnd = ctx.rand("halo_rays")
    raw_rays = [ray_table(rnd, n, int(cnt), w0, w1) for cnt, w0, w1 in o["rays"]]
    # ---- the eye's own colour per angle
    raw = band_colours(d, n, o["src"])
    an = float(o["anchor"])
    raw = raw * (1.0 - an) + raw.mean(0)[None, :] * an
    col = lift(np.clip(_circ_blur(raw, o["col_sigma"]), 0.0, None), *o["lift"])
    # ---- the streamers blurred by half a pixel's angular footprint at the limb: a preview draws them as a reduced master would show them; the bundles'
    # strength rides on the streamers (it bends with them)
    aa = 0.45 / R
    rw = 1.0 - cdep + 2.0 * cdep * cl
    w = o["weights"]
    iw, ifd, itex = o["inner"]
    rays = [(_circ_blur(t, aa) * rw * (wk * (1.0 - iw))).astype(F32) for t, wk in zip(raw_rays, w)]
    tex = (iw * (1.0 - itex) + iw * itex * _circ_blur(raw_rays[0], aa)).astype(F32)       # the inner corona, textured by the fine streamers
    p_lo, p_hi = o["fall"]
    fall_p = p_hi - (p_hi - p_lo) * lob                                  # rho^-p of the inner corona per angle ...
    fall_i = (fall_p + ifd).astype(F32)
    fall_r = (fall_p - cdp * (cl - 0.5)).astype(F32)                     # ... and of the streamers, further in a bright bundle
    drift = (float(o["bend"]) * (lob - 0.5)).astype(F32)                 # the bend per R of distance
    lob_k = (0.8 + 0.4 * lob) * float(o["gain"])                         # the lobes' strength and the gain, carried by the colour
    colk = [np.ascontiguousarray((col[:, c] * lob_k).astype(F32)) for c in range(3)]
    wh = float(o["white"])
    lumk = ((col @ LUMW) / 0.85 * lob_k * wh).astype(F32)
    fd = [float(v) for v in o["fall_d"]]
    k_n = F32(n / TWO_PI)
    fades = CM.fades_for(ctx)
    x0, y0, x1, y1 = CM.window(ctx, d, o["reach"])
    r_in = 0.965 * R                                                     # nothing is drawn inside 0.965 R (the iris covers it): those columns are skipped

    def light(xa, xb, ra, rb):
        """(rb - ra, xb - xa, 3) light of a block of the canvas."""
        xs = (np.arange(xa, xb, dtype=F32) + F32(0.5) - F32(d.cx))[None, :]
        ys = (np.arange(ra, rb, dtype=F32) + F32(0.5) - F32(d.cy))[:, None]
        rho = np.sqrt(xs * xs + ys * ys) * F32(1.0 / R)
        th = np.arctan2(ys, xs)
        i0 = np.floor(th * k_n).astype(np.int64) % n                     # nearest bin: the tables are finer than a master's pixel at the limb
        rc = np.maximum(rho, F32(1.0))
        lr = np.log(rc)
        th += drift[i0] * (rc - F32(1.0))
        i1 = np.floor(th * k_n).astype(np.int64) % n
        del th
        inv = F32(1.0) / rc
        sq = np.sqrt(inv)
        e_in = np.exp(-fall_i[i0] * lr)                                 # the inner corona's fall
        s = rays[0][i1] * _rpow(inv, sq, rc, fd[0])
        s += rays[1][i1] * _rpow(inv, sq, rc, fd[1])
        s += rays[2][i1] * _rpow(inv, sq, rc, fd[2])
        s *= np.exp(-fall_r[i0] * lr)
        s += tex[i1] * e_in
        s *= CM.smooth((rho - F32(0.975)) / F32(0.03))
        e_in *= lumk[i0]                                                 # warm white where the inner corona is strong
        out = np.empty(rho.shape + (3,), F32)
        for c in range(3):
            v = colk[c][i0]
            v += WARM[c] * e_in
            v *= s
            out[..., c] = v
        return out

    for ra, rb in CM.band_rows(y0, y1, 128):
        band = np.zeros((rb - ra, ctx.W, 3), F32)
        dy = max(abs(ra + 0.5 - d.cy), abs(rb - 0.5 - d.cy))            # the band's row farthest from the centre: its chord of the inner disc is the shortest
        hw = math.sqrt(r_in * r_in - dy * dy) if dy < r_in else 0.0
        xa, xb = int(math.ceil(d.cx - hw)), int(math.floor(d.cx + hw))
        if xb - xa > 2:
            band[:, x0:xa] = light(x0, xa, ra, rb)
            band[:, xb:x1] = light(xb, x1, ra, rb)
        else:
            band[:, x0:x1] = light(x0, x1, ra, rb)
        fades(band, ra)
        cv[ra:rb] += band
    # ---- a faint field of stars beyond the corona
    ns, mags, peak = o["stars"]
    if ns:
        layer = M.ParticleLayer()
        CM.starfield(ctx, layer, ctx.rand("halo_stars"), float(ns), tuple(mags), sigma_S=0.00036, peak=float(peak), avoid=CM.avoid_discs(ctx.discs, 1.25),
                     sat=0.8)
        layer.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0)))
    ctx.log["halo"] = {"class": iris.cls, "mid_rgb": [round(float(v), 3) for v in col.mean(0)], "rays": [int(r[0]) for r in o["rays"]]}
