# -*- coding: utf-8 -*-
"""uni_grains: hard-edged angular grains and energy-conserving dust (AD round D5). numpy only.

The AD measured our dust as soft Gaussian discs 2.3x larger than the owner's H11 grains (the 'bokeh glitter' hard fail). A GrainList holds two
kinds of particle:
  dust    sub-pixel: a Gaussian stamp with its energy kept (uni_engine.SplatList)
  grains  every particle whose radius reaches POLY_MIN_PX (1.2 px): a convex polygon of 3-5 vertices, anti-aliased with the analytic edge distance
          (alpha edge <= 1 px, no halo), a bevel facing the key light (upper left x 1.4 on the lit facet, x 0.6 on the shadow facet)
Sizes are given in px at the render size (the callers compute them from R), so a grain of 1.0 percent R is the same picture at 1024 and 4096: at 1024
it is a two-pixel point, at 4096 a real polygon.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_grains.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np

from .engine import SplatList

POLY_MIN_PX = 1.2
LIGHT = np.array([-0.6, -0.8], np.float32)
MAXK = 49


class GrainList:
    def __init__(self):
        self.dust = SplatList()
        self._p = []               # list of dicts of arrays
        self._poly = None

    # -- building
    def add_dust(self, xs, ys, sig, rgb, amp):
        self.dust.add(xs, ys, sig, rgb, amp)

    def add_grains(self, rnd, xs, ys, rad, rgb, amp, min_sigma=0.45):
        """Particles of circumradius `rad` px. Those below POLY_MIN_PX become dust (energy of a disc of that radius: amp * pi rad^2), the others
        polygons. rnd supplies the vertex jitter (drawn at a fixed length, so a count that moves by one does not decorrelate the picture)."""
        xs = np.asarray(xs, np.float64)
        ys = np.asarray(ys, np.float64)
        rad = np.asarray(rad, np.float64)
        n = len(xs)
        if n == 0:
            return
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), (n, 3))
        amp = np.broadcast_to(np.asarray(amp, np.float64), (n,))
        poly = rad >= POLY_MIN_PX
        small = ~poly
        if small.any():
            r = rad[small]
            sig = np.maximum(r / 2.0, 0.25)
            # disc of radius r and level amp has energy amp pi r^2; a gaussian of sigma s and peak a has a 2 pi s^2
            a = amp[small] * (math.pi * r * r) / (2.0 * math.pi * sig * sig)
            self.dust.add(xs[small], ys[small], sig, rgb[small], a)
        if poly.any():
            m = int(poly.sum())
            u = rnd.uniform((n, 12))[poly]              # drawn for EVERY particle (n), then cut: the random stream never depends on which grains are big enough at this size
            nv = np.where(u[:, 0] < 0.25, 3, np.where(u[:, 0] < 0.75, 4, 5))
            self._p.append({"x": xs[poly], "y": ys[poly], "r": rad[poly], "rot": u[:, 1] * 2 * math.pi, "nv": nv,
                            "ja": u[:, 2:7] - 0.5, "jr": u[:, 7:12], "rgb": rgb[poly], "amp": amp[poly]})
            self._poly = None

    def extend(self, other):
        self.dust.parts.extend(other.dust.parts)
        self.dust._done = None
        self._p.extend(other._p)
        self._poly = None
        return self

    def cull(self, boxes):
        self.dust.cull(boxes)
        self._finalize()
        if self._poly is not None and len(self._poly["x"]):
            keep = np.ones(len(self._poly["x"]), bool)
            for (a, b, c_, d) in boxes:
                keep &= ~((self._poly["x"] >= a) & (self._poly["x"] <= c_) & (self._poly["y"] >= b) & (self._poly["y"] <= d))
            self._poly = {k: v[keep] for k, v in self._poly.items()}
            self._p = [self._poly]
        return self

    def __len__(self):
        self._finalize()
        return len(self.dust) + (0 if self._poly is None else len(self._poly["x"]))

    def n_poly(self):
        self._finalize()
        return 0 if self._poly is None else len(self._poly["x"])

    def _finalize(self):
        if self._poly is None and self._p:
            self._poly = {k: np.concatenate([p[k] for p in self._p], 0) for k in self._p[0]}
            o = np.argsort(self._poly["y"], kind="stable")
            self._poly = {k: v[o] for k, v in self._poly.items()}
            self._p = [self._poly]

    # -- drawing (a 'splat' layer: obj.draw(layer, y0, y1), screen-added by the engine)
    def draw(self, layer, y0, y1, min_sigma=0.5, f=1):
        self.dust.draw(layer, y0, y1, min_sigma=min_sigma, f=f)
        self._finalize()
        P = self._poly
        if P is None or not len(P["x"]):
            return layer
        ys = P["y"]
        margin = float(P["r"].max()) + 2.0
        lo = int(np.searchsorted(ys, y0 - margin, "left"))
        hi = int(np.searchsorted(ys, y1 + margin, "right"))
        if hi <= lo:
            return layer
        raster_polys(layer, P, lo, hi, y0)
        return layer


def raster_polys(layer, P, lo, hi, y0):
    """Rasterise grains lo..hi of the store P into layer (rows start at canvas row y0), additive."""
    H, W = layer.shape[:2]
    idx = np.arange(lo, hi)
    rad = P["r"][idx]
    K = (2 * np.ceil(rad).astype(np.int64) + 3)
    K = np.minimum(K, MAXK)
    npx = H * W
    acc = None
    fis, vals = [], []
    for k in np.unique(K):
        sel = idx[K == k]
        per = max(1, (1 << 20) // (int(k) * int(k) * 5))
        for c0 in range(0, len(sel), per):
            ii = sel[c0:c0 + per]
            m = len(ii)
            xc = P["x"][ii][:, None, None]
            yc = P["y"][ii][:, None, None] - y0
            r = P["r"][ii]
            nv = P["nv"][ii]
            # vertices (m, 5): convex-ish polygon; unused vertices repeat vertex 0 (a zero-length edge is ignored)
            j = np.arange(5)[None, :]
            a = P["rot"][ii][:, None] + (j + 0.45 * P["ja"][ii]) * (2 * math.pi / nv[:, None])
            rr = r[:, None] * (0.80 + 0.20 * P["jr"][ii])
            vx = rr * np.cos(a)
            vy = rr * np.sin(a)
            used = j < nv[:, None]
            vx = np.where(used, vx, vx[:, :1])
            vy = np.where(used, vy, vy[:, :1])
            # edge j: vertex j -> vertex (j + 1) mod nv
            nxt = np.where(j + 1 < nv[:, None], j + 1, 0)
            nxt = np.where(used, nxt, 0)
            ex = np.take_along_axis(vx, nxt, 1) - vx
            ey = np.take_along_axis(vy, nxt, 1) - vy
            el = np.hypot(ex, ey)
            valid = used & (el > 1e-6)
            nx = np.where(valid, ey / np.maximum(el, 1e-9), 0.0)
            ny = np.where(valid, -ex / np.maximum(el, 1e-9), 0.0)
            off = nx * vx + ny * vy                                   # n . v_j
            # sample grid: integer patch round the grain centre
            kk = int(k)
            px0 = np.floor(P["x"][ii]).astype(np.int64) - kk // 2
            py0 = np.floor(P["y"][ii] - y0).astype(np.int64) - kk // 2
            gx = px0[:, None] + np.arange(kk)[None, :]                # (m, K)
            gy = py0[:, None] + np.arange(kk)[None, :]
            ux = (gx + 0.5)[:, None, :] - xc                          # (m, 1, K) offset from the centre
            uy = (gy + 0.5)[:, :, None] - yc                          # (m, K, 1)
            d = (nx[:, None, None, :] * ux[..., None] + ny[:, None, None, :] * uy[..., None]) - off[:, None, None, :]
            d = np.where(valid[:, None, None, :], d, -1e9)
            sd = d.max(-1)
            jb = d.argmax(-1)
            cov = np.clip(0.5 - sd, 0.0, 1.0)
            # bevel: the facet the pixel belongs to, lit from the upper left
            fnx = np.take_along_axis(nx, jb.reshape(m, -1), 1).reshape(jb.shape)
            fny = np.take_along_axis(ny, jb.reshape(m, -1), 1).reshape(jb.shape)
            lit = fnx * LIGHT[0] + fny * LIGHT[1]
            bev = np.clip(1.0 - (-sd) / np.maximum(0.55 * r[:, None, None], 0.9), 0.0, 1.0)
            shade = 0.95 + bev * np.where(lit > 0, 0.45 * lit, 0.40 * lit)
            # energy: a polygon of circumradius r covers 1.05 / 1.62 / 1.93 r^2 (3, 4, 5 vertices, vertex radii 0.8-1.0 r) where the sub-pixel dust stamp of the same
            # particle carries pi r^2: the gain makes a grain the same amount of light at 4096 as the dust point it becomes at 1024
            gain = (math.pi / np.array([1.0, 1.0, 1.0, 1.05, 1.62, 1.93], np.float32))[nv]
            w = cov * shade * (P["amp"][ii] * gain)[:, None, None]
            ok = (cov > 1e-3) & (gx[:, None, :] >= 0) & (gx[:, None, :] < W) & (gy[:, :, None] >= 0) & (gy[:, :, None] < H)
            if not ok.any():
                continue
            fi = (np.broadcast_to(gy[:, :, None], cov.shape) * W + np.broadcast_to(gx[:, None, :], cov.shape))[ok]
            pi = np.broadcast_to(np.arange(m)[:, None, None], cov.shape)[ok]
            fis.append(fi)
            vals.append(P["rgb"][ii][pi] * w[ok][:, None])
    if not fis:
        return layer
    fi = np.concatenate(fis)
    va = np.concatenate(vals)
    out = np.empty((3, npx), np.float32)
    for ch in range(3):
        out[ch] = np.bincount(fi, weights=va[:, ch], minlength=npx)
    layer += out.T.reshape(H, W, 3)
    return layer
