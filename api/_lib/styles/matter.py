# -*- coding: utf-8 -*-
"""designs.singles_matter: the physical-matter primitives of the SINGLES designs (ported from the scratch prototype).

  atlas()            the chip atlas (345 photographed chips cut from the P-SN-FLAKE sheets, built offline by _build_atlas.py)
  grains()           angular polygon grains (3-5 vertices) with a specular edge on the upper-left facet
  dust()             sub-pixel to 2 px splats (energy conserving)
  streaks()          the fastest grains as short radial streaks
  chips()            iris-chips: an atlas silhouette filled with a patch of the SAME iris (band 0.70-0.95 R at the emission
                     angle, 60 %) and the gradient map (40 %), lit from the upper left, real fibres inside
  blobs() / fg_chunks()   defocused matter for depth
  limbus_breakup()   the iris's own band 0.92-0.99 R pushed outward 0.02-0.09 R through a noise mask with holes
  Emission           angular density (wind, jets, lobes) and radial density (85 % dense L1, 15 % tail L2) in R units

All positions are generated in R units with counts that do not depend on the canvas size; sizes are R fractions, so a 4096
master and its 1024 preview are the same picture. Nothing here ever draws on a visible iris pixel (r <= 1.0 R is masked).
"""
from __future__ import annotations

# PORT of work package WP5A (step A): singles_matter.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists
# (imports, the chips atlas read through atlas.py); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np
from PIL import Image

from . import atlas as AT
from . import core as C
from .singles import kit as K

TWO_PI = 2.0 * math.pi
F32 = np.float32
LIGHT = np.array([-0.55, -0.83], np.float64)          # key light toward the upper left (screen x right, y down)
LIGHT /= np.linalg.norm(LIGHT)

def atlas():
    """The chip atlas (api/_lib/styles/atlas.py: read once per process, checked against the registry's sha256)."""
    return AT.chips()


def _mip(side):
    """The chip atlas reduced by a box filter to `side` x `side` (128, 64, 32, 16): (lum, mask) float32 (n, side, side). Built once."""
    return AT.chips().mip(side)


# ----------------------------------------------------------------------------- emission (R units)
class Emission:
    """Where matter goes. theta in radians (screen: clockwise, y down), e = outward distance from the limb in R.
    wind: direction (screen rad), b: wind bias, m(theta) = 1 + b cos(theta - wind); n_jets +-10 deg jets carrying jet_share;
    a low-frequency lobe noise (3-5 lobes, +-25 %).
    Envelope (brief 3.6, 0.6 R3 / R13):  E(theta) = halo + plume * max(0, cos(theta - wind))^1.5   [R, beyond the limb],
    times the +-12 % reach noise. A particle at angle theta may not go beyond E(theta); the radial law of every particle is
    stretched on the wind side (scale_at) so the plume is denser and longer, not just cut."""

    def __init__(self, rnd, wind, b=0.25, n_jets=6, jet_share=0.20, lobes=4, lobe_amp=0.25, n=1440, halo=0.55, plume=0.45,
                 stretch=(0.85, 1.05)):
        self.n = n
        th = np.arange(n) * (TWO_PI / n)
        m = 1.0 + b * np.cos(th - wind)
        ph = rnd.uniform(lobes) * TWO_PI
        lobe = np.zeros(n)
        for kk, p in zip(range(2, 2 + lobes), ph):
            lobe += np.cos(kk * th + p) / lobes
        m = m * (1.0 + lobe_amp * lobe * 2.0)
        jets = np.zeros(n)
        jc = rnd.uniform(n_jets) * TWO_PI
        jc = np.where(rnd.uniform(n_jets) < 0.6, wind + rnd.normal(n_jets, 0.0, 0.9), jc)      # jets prefer the wind side
        jw = np.radians(rnd.uniform(n_jets, 4.0, 10.0))
        jm = rnd.uniform(n_jets, 0.5, 1.0)
        for c, w, a in zip(jc, jw, jm):
            dd = (th - c + math.pi) % TWO_PI - math.pi
            jets += a * np.exp(-0.5 * (dd / w) ** 2)
        jets /= max(jets.sum(), 1e-9)
        base = np.maximum(m, 0.05)
        base /= base.sum()
        self.pdf = (1.0 - jet_share) * base + jet_share * jets
        self.cdf = np.concatenate([[0.0], np.cumsum(self.pdf)])
        self.cdf /= self.cdf[-1]
        self.wind = wind
        self.reach = 1.0 + 0.12 * (C.periodic_fbm1d(n, rnd, 3, 4).astype(np.float64) * 2.0 - 1.0)     # +-12 % round the outline
        w = np.maximum(0.0, np.cos(th - wind)) ** 1.5
        self.w = w
        self.E = (halo + plume * w) * self.reach
        self.scale = stretch[0] + stretch[1] * w
        self.halo, self.plume = halo, plume
        # broken-ring mask: the dense grain ring hugging the limb is never a perfect circle (1 = matter, 0 = gap)
        nz = C.periodic_fbm1d(n, rnd, 4, 9).astype(np.float64)
        self.gap = 0.30 + 0.70 * C.smoothstep((nz - 0.22) / 0.40)

    def _at(self, arr, th):
        i = (np.floor(np.asarray(th) * (self.n / TWO_PI)).astype(np.int64)) % self.n
        return arr[i]

    def theta(self, rnd, n):
        u = rnd.uniform(n)
        return np.interp(u, self.cdf, np.arange(self.n + 1)) * (TWO_PI / self.n)

    def reach_at(self, th):
        return self._at(self.reach, th)

    def ring_at(self, th, e, width=0.30):
        """Multiplier 0.30..1 that breaks the ring near the limb (e in R): full strength beyond `width` R."""
        g = self._at(self.gap, th)
        u = np.clip(np.asarray(e) / width, 0.0, 1.0)
        u = u * u * (3.0 - 2.0 * u)
        return g + (1.0 - g) * u

    def E_at(self, th):
        """Allowed outward reach (R) at angle th."""
        return self._at(self.E, th)

    def scale_at(self, th):
        return self._at(self.scale, th)

    def strength_at(self, th):
        """pdf at th, normalised to its maximum (0..1)."""
        x = np.asarray(th) % TWO_PI
        v = np.interp(x, np.arange(self.n + 1) * (TWO_PI / self.n), np.concatenate([self.pdf, self.pdf[:1]]))
        return v / max(float(self.pdf.max()), 1e-12)

    def radial(self, rnd, n, l1=0.18, l2=0.42, tail=0.15, cut=0.95):
        """Outward distance e (R): 85 % dense exp(L1), 15 % tail exp(L2), hard cut at `cut`."""
        which = rnd.uniform(n) < tail
        e = np.where(which, rnd.exponential(n, l2), rnd.exponential(n, l1))
        return np.minimum(e, cut * 0.999)

    def sample(self, rnd, n, l1=0.18, l2=0.42, tail=0.15, cap=1.0, over=3.0, min_e=0.0):
        """n (theta, e) pairs: the angular pdf, the radial law stretched on the wind side, truncated at cap * E(theta)
        (rejection, so nothing piles up on the boundary). Returns fewer than n only if the envelope is impossibly tight."""
        out_t, out_e, have = [], [], 0
        for _ in range(6):
            m = int(max(n, 8) * over)
            th = self.theta(rnd, m)
            e = self.radial(rnd, m, l1, l2, tail, cut=50.0) * self.scale_at(th)
            ok = (e <= cap * self.E_at(th)) & (e >= min_e)
            out_t.append(th[ok])
            out_e.append(e[ok])
            have += int(ok.sum())
            if have >= n:
                break
        th, e = np.concatenate(out_t)[:n], np.concatenate(out_e)[:n]
        return th, e


class Fields:
    """Reduced-resolution masks: plate coupling (density follows the cloud), text box, canvas edge, wallpaper clock zone."""

    def __init__(self, ctx, lum=None, f=4, red=None):
        self.f = f
        self.W, self.H = ctx.W, ctx.H
        self.w, self.h = -(-ctx.W // f), -(-ctx.H // f)
        self.plate = None
        if red is None and lum is not None:
            red = C.box_reduce(np.ascontiguousarray(lum), f)
        if red is not None:
            self.plate = C.blur(np.ascontiguousarray(red, np.float32), 0.012 * ctx.S / f)
        self.S = ctx.S
        self.text_box = ctx.text_box
        self.wall = ctx.wall

    def accept(self, x, y, plate_gain=1.6, plate_floor=0.10, text=0.12, edge=0.04):
        """Acceptance probability (0..1) of a particle at canvas px (x, y)."""
        x = np.asarray(x)
        y = np.asarray(y)
        p = np.ones(x.shape, np.float64)
        if self.plate is not None:
            xi = np.clip((x / self.f).astype(np.int64), 0, self.w - 1)
            yi = np.clip((y / self.f).astype(np.int64), 0, self.h - 1)
            p = np.clip(plate_floor + plate_gain * self.plate[yi, xi], 0.0, 1.0)
        if self.text_box is not None and text < 1.0:
            x0, y0, x1, y1 = self.text_box
            m = 0.02 * self.S
            inside = (x > x0 - m) & (x < x1 + m) & (y > y0 - m) & (y < y1 + m)
            p = np.where(inside, p * text, p)
        if edge:
            e = edge * self.S
            p = p * C.smoothstep(np.minimum(np.minimum(x, self.W - x), np.minimum(y, self.H - y)) / e)
        if self.wall:
            p = p * (0.35 + 0.65 * C.smoothstep((y / self.H - 0.08) / 0.14))
        return p


# ----------------------------------------------------------------------------- small helpers
def polar_px(d, rho, th):
    """canvas px of polar points (rho in R, theta rad) round the disc."""
    return d.cx + rho * d.R * np.cos(th), d.cy + rho * d.R * np.sin(th)


def rgb_pal(stops, th, level):
    """Colour of ramp stops (3, 360, 3) at angles th with a level 0..1 (deep -> mid -> hot)."""
    deep, mid, hot = C.ring_at(stops[0], th), C.ring_at(stops[1], th), C.ring_at(stops[2], th)
    lv = np.asarray(level, np.float32)[..., None]
    a = np.clip(lv * 2.0, 0.0, 1.0)
    b = np.clip(lv * 2.0 - 1.0, 0.0, 1.0)
    return ((deep * (1 - a) + mid * a) * (1 - b) + hot * b).astype(np.float32)


def sample_tight(g, x, y):
    """Bilinear RGB 0..1 of the tight graded square g (uint8) at continuous tight coords (pixel centres at i + 0.5)."""
    tgt = g.shape[0]
    xf, yf = x - 0.5, y - 0.5
    x0 = np.floor(xf).astype(np.int64)
    y0 = np.floor(yf).astype(np.int64)
    wx = (xf - x0).astype(np.float32)[..., None]
    wy = (yf - y0).astype(np.float32)[..., None]
    x0c = np.clip(x0, 0, tgt - 2)
    y0c = np.clip(y0, 0, tgt - 2)
    a = g[y0c, x0c] * (1 - wx) + g[y0c, x0c + 1] * wx
    b = g[y0c + 1, x0c] * (1 - wx) + g[y0c + 1, x0c + 1] * wx
    return ((a * (1 - wy) + b * wy) / 255.0).astype(np.float32)


# ----------------------------------------------------------------------------- polygon grains
def grains(cv, xs, ys, rad, col, alpha, rnd, spec=0.55, ids=None, total=None, px_scale=None):
    """Angular polygon grains composited 'over' onto cv (H, W, 3) in place. xs, ys canvas px (sub-pixel), rad px (mean
    radius), col (n, 3) 0..1, alpha (n,). 3-5 vertices, facet shading from the upper-left key light, a bright specular
    edge on the facets that face it, 1 px anti-aliased edge (coverage x alpha keeps the energy of sub-pixel grains)."""
    H, W = cv.shape[:2]
    n = len(xs)
    if n == 0:
        return cv
    edge_px = float(max(H, W) / 1024.0 if px_scale is None else px_scale)      # the specular edge width (0.9 px at 1024) scales with the canvas: a master draws the preview's grain
    xs, ys = np.asarray(xs, np.float64), np.asarray(ys, np.float64)
    # every random attribute is drawn for ALL candidates (total) and then indexed by the grain's own candidate id, so a preview and a master
    # that differ in which borderline candidates are accepted still give every surviving grain the same shape and colour
    tot = n if ids is None else int(total)
    sel = slice(None) if ids is None else np.asarray(ids)
    nv = rnd.integers(tot, 3, 6)[sel]
    ph = (rnd.uniform(tot) * TWO_PI)[sel]
    jit = (rnd.uniform((tot, 5)) - 0.5)[sel]
    rv = (0.62 + 0.38 * rnd.uniform((tot, 5)))[sel]
    asp = np.exp(rnd.uniform(tot, -0.50, 0.50))[sel][:, None]                    # shards are not regular: aspect 0.6 .. 1.65
    tone = np.exp(rnd.uniform(tot, -0.28, 0.22))[sel]                             # grain-to-grain brightness (no two shards lit alike)
    ang = np.arange(5)[None, :] * (TWO_PI / nv[:, None]) + jit * (0.55 * TWO_PI / nv[:, None])
    valid = np.arange(5)[None, :] < nv[:, None]
    x0_ = np.cos(ang) * rv * asp
    y0_ = np.sin(ang) * rv / asp
    cph, sph = np.cos(ph)[:, None], np.sin(ph)[:, None]
    vx = np.where(valid, x0_ * cph - y0_ * sph, 0.0)
    vy = np.where(valid, x0_ * sph + y0_ * cph, 0.0)
    vx = np.where(valid, vx, vx[:, :1])
    vy = np.where(valid, vy, vy[:, :1])
    wx = np.roll(vx, -1, axis=1)
    wy = np.roll(vy, -1, axis=1)
    rows = np.arange(n)
    wx[rows, nv - 1] = vx[:, 0]                       # the closing edge of a k-gon: vertex k-1 -> vertex 0
    wy[rows, nv - 1] = vy[:, 0]
    ex, ey = wx - vx, wy - vy
    ln = np.hypot(ex, ey)
    ok_edge = valid & (ln > 1e-6)
    nx, ny = ey / np.maximum(ln, 1e-9), -ex / np.maximum(ln, 1e-9)
    flip = (nx * (vx + wx) + ny * (vy + wy)) < 0
    nx, ny = np.where(flip, -nx, nx).astype(np.float32), np.where(flip, -ny, ny).astype(np.float32)
    vx, vy = vx.astype(np.float32), vy.astype(np.float32)
    rad = np.maximum(np.asarray(rad, np.float64), 0.35)
    col = np.asarray(col, np.float32)
    alpha = np.broadcast_to(np.asarray(alpha, np.float32), (n,))
    Kb = np.ceil(rad).astype(np.int64)
    acc_fi, acc_a, acc_c = [], [], []                 # sparse accumulation: only the touched pixels (a full-canvas accumulator is 270 MB at 4K)
    for kb in np.unique(Kb):
        sel = np.nonzero(Kb == kb)[0]
        h = int(kb) + 1
        Kw = 2 * h + 1
        jo = np.arange(Kw) - h
        per = max(1, (1 << 18) // (Kw * Kw * 5))
        for c0 in range(0, len(sel), per):
            ii = sel[c0:c0 + per]
            gxi = np.floor(xs[ii]).astype(np.int64)[:, None] + jo[None, :]              # (m, Kw)
            gyi = np.floor(ys[ii]).astype(np.int64)[:, None] + jo[None, :]
            r_ = rad[ii].astype(np.float32)
            px = ((gxi + 0.5 - xs[ii][:, None]) / r_[:, None]).astype(np.float32)
            py = ((gyi + 0.5 - ys[ii][:, None]) / r_[:, None]).astype(np.float32)
            sd = -((px[:, None, :, None] - vx[ii][:, None, None, :]) * nx[ii][:, None, None, :]
                   + (py[:, :, None, None] - vy[ii][:, None, None, :]) * ny[ii][:, None, None, :])      # (m, Ky, Kx, 5)
            sd = np.where(ok_edge[ii][:, None, None, :], sd, np.float32(9.0))
            am = np.argmin(sd, axis=-1)
            dmin = np.take_along_axis(sd, am[..., None], -1)[..., 0] * r_[:, None, None]                  # px
            ss = 3 if kb <= 2 else (2 if kb <= 5 else 1)
            if ss > 1:                                   # area-exact coverage by ss x ss supersampling (a 2-6 px shard at 1024 must equal its 4096 twin reduced)
                cov = np.zeros(dmin.shape, np.float32)
                for oy in (np.arange(ss) + 0.5) / ss - 0.5:
                    for ox in (np.arange(ss) + 0.5) / ss - 0.5:
                        pxs = ((gxi + 0.5 + ox - xs[ii][:, None]) / r_[:, None]).astype(np.float32)
                        pys = ((gyi + 0.5 + oy - ys[ii][:, None]) / r_[:, None]).astype(np.float32)
                        sds = -((pxs[:, None, :, None] - vx[ii][:, None, None, :]) * nx[ii][:, None, None, :]
                                + (pys[:, :, None, None] - vy[ii][:, None, None, :]) * ny[ii][:, None, None, :])
                        sds = np.where(ok_edge[ii][:, None, None, :], sds, np.float32(9.0))
                        cov += (sds.min(-1) >= 0.0)
                cover = cov / np.float32(ss * ss)
            else:
                cover = np.clip(dmin + 0.5, 0.0, 1.0)
            nxg = np.take_along_axis(np.broadcast_to(nx[ii][:, None, None, :], sd.shape), am[..., None], -1)[..., 0]
            nyg = np.take_along_axis(np.broadcast_to(ny[ii][:, None, None, :], sd.shape), am[..., None], -1)[..., 0]
            fl = nxg * np.float32(LIGHT[0]) + nyg * np.float32(LIGHT[1])
            edge_w = np.clip(1.0 - dmin / np.maximum(0.30 * r_[:, None, None], 0.9 * edge_px), 0.0, 1.0)
            shade = 0.80 + 0.40 * np.clip(fl, -0.7, 1.0) + spec * 1.6 * edge_w * np.clip(fl - 0.15, 0.0, 1.0)
            inb = ((gxi >= 0) & (gxi < W))[:, None, :] & ((gyi >= 0) & (gyi < H))[:, :, None]
            a = cover * alpha[ii][:, None, None]
            good = inb & (a > 1e-4)
            fi = (gyi[:, :, None] * W + gxi[:, None, :])
            fi = np.broadcast_to(fi, a.shape)[good]
            aw = a[good].astype(np.float32)
            cc = np.broadcast_to(col[ii][:, None, None, :], a.shape + (3,))[good]
            acc_fi.append(fi)
            acc_a.append(aw)
            tone_g = np.broadcast_to(tone[ii][:, None, None], a.shape)[good].astype(np.float32)
            acc_c.append((cc * (shade[good].astype(np.float32) * tone_g * aw)[:, None]).astype(np.float32))
    if not acc_fi:
        return cv
    fi = np.concatenate(acc_fi)
    uniq, inv = np.unique(fi, return_inverse=True)
    A_a = np.bincount(inv, weights=np.concatenate(acc_a), minlength=len(uniq)).astype(np.float32)
    cw = np.concatenate(acc_c)
    A_rgb = np.stack([np.bincount(inv, weights=cw[:, c], minlength=len(uniq)) for c in range(3)], 1).astype(np.float32)
    hit = np.nonzero(A_a > 1e-5)[0]
    if len(hit):
        flat = cv.reshape(-1, 3)
        idx = uniq[hit]
        a = np.minimum(A_a[hit], 1.0)[:, None]
        mean = A_rgb[hit] / A_a[hit][:, None]
        flat[idx] = flat[idx] * (1.0 - a) + mean * a
    return cv


class ParticleLayer:
    """A light layer that never exists as a full canvas: splat() collects Gaussian stamps, flush() draws them band by band (256 rows
    + a 16 px margin, so stamps across a band edge stay whole) into a small layer, applies the per-band fades and screens the band into
    the canvas. Identical to splatting into a full layer and screening it, at a fraction of the memory (a 4096 RGB layer is 200 MB)."""

    def __init__(self):
        self.parts = []

    def splat(self, xs, ys, sigma, rgb, amp=1.0, min_sigma=0.5):
        n = len(np.atleast_1d(xs))
        if n == 0:
            return
        self.parts.append((np.atleast_1d(np.asarray(xs, np.float64)), np.atleast_1d(np.asarray(ys, np.float64)),
                           np.broadcast_to(np.asarray(sigma, np.float64), (n,)).copy(),
                           np.broadcast_to(np.asarray(rgb, np.float32), (n, 3)).copy(),
                           np.broadcast_to(np.asarray(amp, np.float64), (n,)).copy(), float(min_sigma)))

    def flush(self, cv, fades=(), step=256, margin=16, mode="screen"):
        if not self.parts:
            return cv
        H, W = cv.shape[:2]
        ms = sorted(set(p[5] for p in self.parts))
        xs = np.concatenate([p[0] for p in self.parts])
        ys = np.concatenate([p[1] for p in self.parts])
        sg = np.concatenate([p[2] for p in self.parts])
        rgb = np.concatenate([p[3] for p in self.parts])
        am = np.concatenate([p[4] for p in self.parts])
        mn = np.concatenate([np.full(len(p[0]), p[5]) for p in self.parts])
        order = np.argsort(ys, kind="stable")
        xs, ys, sg, rgb, am, mn = xs[order], ys[order], sg[order], rgb[order], am[order], mn[order]
        for r0 in range(0, H, step):
            r1 = min(H, r0 + step)
            lo = np.searchsorted(ys, r0 - margin)
            hi = np.searchsorted(ys, r1 + margin)
            if hi <= lo:
                continue
            ya, yb = max(0, r0 - margin), min(H, r1 + margin)
            layer = np.zeros((yb - ya, W, 3), np.float32)
            for m_ in ms:
                sel = np.nonzero(mn[lo:hi] == m_)[0] + lo
                if len(sel):
                    C.splat(layer, xs[sel], ys[sel] - ya, sg[sel], rgb[sel], am[sel], min_sigma=m_)
            view = layer[r0 - ya:r1 - ya]
            for f in fades:
                f(view, r0)
            if mode == "screen":
                C.screen(cv[r0:r1], view)
            else:
                cv[r0:r1] += view
        return cv


# ----------------------------------------------------------------------------- dust and streaks (light, screened)
def dust(light, xs, ys, sigma_px, col, amp):
    """Sub-pixel to 2 px Gaussian splats with the energy of the ideal stamp (fx.core.splat), added into light (a canvas layer or a ParticleLayer)."""
    light.splat(xs, ys, sigma_px, col, amp, min_sigma=0.2) if isinstance(light, ParticleLayer) else C.splat(light, xs, ys, sigma_px, col, amp, min_sigma=0.2)
    return light


def streaks(light, x0, y0, dx, dy, length_px, col, amp, sigma_px=0.55):
    """Short radial streaks: k points along (dx, dy), intensity falling to the tail (comet). sigma_px is the stroke width (give it in S units,
    0.00054 S, so a 4096 master draws the same streak as its 1024 preview); k follows length / sigma so the points always overlap into a line."""
    n = len(x0)
    if n == 0:
        return light
    L_ = np.asarray(length_px, np.float64)
    k = int(np.clip(math.ceil(float(L_.max()) / (0.9 * max(sigma_px, 0.5))), 8, 48))
    t = (np.arange(k) + 0.5) / k
    prof = (1.0 - t) ** 1.6
    prof = prof / prof.sum()
    xx = x0[:, None] - dx[:, None] * L_[:, None] * t[None, :]
    yy = y0[:, None] - dy[:, None] * L_[:, None] * t[None, :]
    aa = np.asarray(amp)[:, None] * prof[None, :] * k
    cc = np.repeat(np.asarray(col, np.float32), k, axis=0)
    if isinstance(light, ParticleLayer):
        light.splat(xx.ravel(), yy.ravel(), sigma_px, cc, aa.ravel(), min_sigma=0.5)
    else:
        C.splat(light, xx.ravel(), yy.ravel(), sigma_px, cc, aa.ravel(), min_sigma=0.5)
    return light


# ----------------------------------------------------------------------------- chips
def sprite_size(size_px):
    """Side (px) of the square canvas a chip of longest side size_px is drawn on (room for any rotation)."""
    return int(math.ceil(max(3.0, float(size_px)) * 1.43)) + 3


def _sprite(idx, size_px, rot_deg, fx=0.0, fy=0.0):
    """(lum, mask) float32 (n, n) of atlas sprite idx scaled so its longest side is size_px, rotated rot_deg about its centre, and placed with its
    centre at (n / 2 + fx, n / 2 + fy) pixels of the returned canvas: ONE affine resample from the smallest atlas mip that is at least as large as
    the chip (at most a 2x reduction), so a chip lands on its exact sub-pixel position (a 1024 preview and a 4096 master draw the same chip)."""
    n = sprite_size(size_px)
    side = 16
    for sd in (16, 32, 64, 128):
        side = sd
        if sd >= size_px:
            break
    lm, mk = _mip(side)
    im = Image.fromarray(np.stack([(lm[idx] * 255.0 + 0.5).astype(np.uint8), (mk[idx] * 255.0 + 0.5).astype(np.uint8),
                                   np.zeros((side, side), np.uint8)], -1), "RGB")
    k = max(float(size_px), 1.0) / side                                 # output px per mip px
    th = math.radians(rot_deg)
    cs, sn = math.cos(th), math.sin(th)
    ocx, ocy = n / 2.0 + fx, n / 2.0 + fy
    a, b = cs / k, sn / k
    d_, e_ = -sn / k, cs / k
    c = side / 2.0 - (a * ocx + b * ocy)
    f = side / 2.0 - (d_ * ocx + e_ * ocy)
    out = im.transform((n, n), Image.AFFINE, (a, b, c, d_, e_, f), resample=Image.BICUBIC)
    arr = np.asarray(out, np.float32) / 255.0
    return arr[..., 0], arr[..., 1]


def rgb_pal_const(stops, th, level):
    """rgb_pal for ONE angle th (scalar) and a level array of any shape: the three colours are looked up once."""
    deep = C.ring_at(stops[0], np.float64(th))
    mid = C.ring_at(stops[1], np.float64(th))
    hot = C.ring_at(stops[2], np.float64(th))
    lv = np.asarray(level, np.float32)[..., None]
    a = np.clip(lv * 2.0, 0.0, 1.0)
    b = np.clip(lv * 2.0 - 1.0, 0.0, 1.0)
    return ((deep * (1 - a) + mid * a) * (1 - b) + hot * b).astype(np.float32)


def chips(cv, d, xs, ys, size_px, th_emit, stops, rnd, alpha=0.95, blur_px=0.0, lift=1.0, rot_max=20.0, patch_share=0.72,
          rho_patch=(0.72, 0.92), dark=0.0, shade_lo=0.30, shade_gain=0.80, ids=None, total=None,
          dark_frac=0.0, dark_mult=0.45, trans_frac=0.0, trans_alpha=(0.50, 0.70), facet=0.0, hue_var=0.0):
    """Iris-chips composited 'over' onto cv in place. Each chip: an atlas silhouette (bright edge on the upper-left facet,
    the sprite's own shading), filled with a patch of the SAME iris (60 %, real fibres, taken at the emission angle from
    band 0.70-0.95 R) and the gradient map (40 %). dark > 0: the chips are darkened (out of focus, in front).
    Atlas indices are drawn without replacement, so a chip never repeats within a run."""
    H, W = cv.shape[:2]
    n = len(xs)
    if n == 0:
        return cv
    A = atlas()
    perm = np.argsort(rnd.uniform(A["n"]))
    tgt = d.g.shape[0]
    Rg = d.R
    tot = n if ids is None else int(total)
    sel = slice(None) if ids is None else np.asarray(ids)
    rot = rnd.uniform(tot, -rot_max, rot_max)[sel]
    rp = rnd.uniform(tot, rho_patch[0], rho_patch[1])[sel]
    ju = rnd.uniform(tot, -0.2, 0.2)[sel]
    u_dark = rnd.uniform(tot)[sel]                                       # per chip: dark (shadowed) / translucent / neither, drawn per candidate
    u_trans = rnd.uniform(tot)[sel]
    u_alpha = rnd.uniform(tot, trans_alpha[0], trans_alpha[1])[sel]
    u_tone = np.exp(rnd.uniform(tot, -0.22, 0.18))[sel]
    facet_ang = rnd.uniform(tot, -0.5, 0.5)[sel]
    aid = np.arange(n) if ids is None else np.asarray(ids)
    ali = np.broadcast_to(np.asarray(alpha, np.float32), (n,))
    for k in range(n):
        nsp = sprite_size(size_px[k])
        x0 = int(math.floor(xs[k] - nsp / 2.0))
        y0 = int(math.floor(ys[k] - nsp / 2.0))
        lum, msk = _sprite(int(perm[int(aid[k]) % len(perm)]), float(size_px[k]), float(rot[k]), xs[k] - nsp / 2.0 - x0, ys[k] - nsp / 2.0 - y0)
        h, w = lum.shape
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xa >= xb or ya >= yb:
            continue
        sx = slice(xa - x0, xb - x0)
        sy = slice(ya - y0, yb - y0)
        lm, mk = lum[sy, sx], msk[sy, sx]
        th = th_emit[k] + ju[k]
        pcx = tgt / 2.0 + rp[k] * Rg * math.cos(th)
        pcy = tgt / 2.0 + rp[k] * Rg * math.sin(th)
        gx = pcx + (np.arange(xa, xb) + 0.5 - xs[k])[None, :]
        gy = pcy + (np.arange(ya, yb) + 0.5 - ys[k])[:, None]
        patch = sample_tight(d.g, np.broadcast_to(gx, lm.shape), np.broadcast_to(gy, lm.shape))
        lmn = np.clip(lm / 0.85, 0.0, 1.0)
        pal = rgb_pal_const(stops, th_emit[k], np.clip(0.26 + 0.46 * lmn, 0, 1))
        base = patch_share * np.clip(patch * lift, 0, 1.4) + (1.0 - patch_share) * pal
        shade = (shade_lo + shade_gain * lmn ** 1.15)[..., None]
        if facet > 0:                                                    # one shade facet on the lower-right side (key light from the upper left)
            hh_, ww_ = lm.shape
            yy_ = (np.arange(ya, yb) + 0.5 - ys[k])[:, None] / max(h, 1)
            xx_ = (np.arange(xa, xb) + 0.5 - xs[k])[None, :] / max(w, 1)
            dd_ = 0.55 * xx_ + 0.83 * yy_ + float(facet_ang[k]) * 0.2
            shade = shade * (1.0 - facet * C.smoothstep((dd_ - 0.02) / 0.22))[..., None]
        colr = base * shade * float(u_tone[k])
        if dark:
            colr = colr * (1.0 - dark)
        if dark_frac > 0 and u_dark[k] < dark_frac:
            dk = rgb_pal_const(stops, th_emit[k], np.clip(0.18 + 0.30 * lmn, 0, 1))             # a shadowed chip keeps the eye's own hue
            colr = colr * dark_mult * 0.55 + dk * (0.40 * dark_mult / 0.45) * shade
        a = mk * ali[k]
        if trans_frac > 0 and u_trans[k] < trans_frac:
            a = a * float(u_alpha[k])
        if blur_px > 0:
            bp = int(math.ceil(3 * blur_px))
            th_, tw_ = lm.shape
            tile = np.zeros((th_ + 2 * bp, tw_ + 2 * bp, 4), np.float32)
            tile[bp:bp + th_, bp:bp + tw_, :3] = colr * a[..., None]
            tile[bp:bp + th_, bp:bp + tw_, 3] = a
            tile = C.blur(tile, blur_px)
            ya2, yb2, xa2, xb2 = max(0, ya - bp), min(H, yb + bp), max(0, xa - bp), min(W, xb + bp)
            oy, ox = ya2 - (ya - bp), xa2 - (xa - bp)
            t2 = tile[oy:oy + (yb2 - ya2), ox:ox + (xb2 - xa2)]
            reg = cv[ya2:yb2, xa2:xb2]
            reg *= (1.0 - t2[..., 3:4])
            reg += t2[..., :3]
        else:
            reg = cv[ya:yb, xa:xb]
            reg *= (1.0 - a[..., None])
            reg += colr * a[..., None]
    return cv


def blobs(cv, xs, ys, rad_px, col, alpha, blur_px):
    """Defocused matter: soft discs (radius rad_px, blurred blur_px), composited 'over'."""
    H, W = cv.shape[:2]
    for k in range(len(xs)):
        r = float(rad_px[k])
        bp = int(math.ceil(3 * blur_px)) + 1
        m = int(math.ceil(r)) + bp
        x0, y0 = int(round(xs[k])) - m, int(round(ys[k])) - m
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + 2 * m + 1), min(H, y0 + 2 * m + 1)
        if xa >= xb or ya >= yb:
            continue
        gx = (np.arange(xa, xb) + 0.5 - xs[k])[None, :]
        gy = (np.arange(ya, yb) + 0.5 - ys[k])[:, None]
        rr = np.sqrt(gx * gx + gy * gy)
        disc = np.clip((r - rr) / max(1.0, blur_px * 1.2) + 0.5, 0, 1).astype(np.float32)
        prof = (0.78 + 0.22 * C.smoothstep((rr / r - 0.5) / 0.5)).astype(np.float32)          # a brighter rim: bokeh
        a = disc * prof
        if blur_px > 0.6:
            a = C.blur(a, blur_px * 0.6)
        a = (a * float(alpha[k]))[..., None]
        reg = cv[ya:yb, xa:xb]
        reg *= (1.0 - a)
        reg += np.asarray(col[k], np.float32)[None, None, :] * a
    return cv


def rim_fragments(cv, d, n, emis, stops, rnd, e_scale=0.05, e_max=0.20, size=(0.006, 0.020), rho_src=(0.90, 0.985), alpha=0.95):
    """Fragments of the iris's own rim lifting off the limb: tiny angular grains (3-5 vertices) coloured with the iris pixels of the
    SAME angle (band 0.90-0.985 R), placed 0.01-0.20 R beyond the limb, denser and further on the wind side. Drawn BEFORE the paste
    (outside 1.0 R only)."""
    if n <= 0:
        return cv
    th = emis.theta(rnd, n * 2)
    e = 0.012 + rnd.exponential(len(th), e_scale) * (0.6 + 1.4 * emis.w[(th * emis.n / TWO_PI).astype(np.int64) % emis.n])
    ok = e < e_max
    th, e = th[ok][:n], e[ok][:n]
    m = len(th)
    px, py = polar_px(d, 1.0 + e, th)
    rs = rnd.uniform(m, rho_src[0], rho_src[1])
    cols = K.sample_disc(d, rs, th + rnd.uniform(m, -0.05, 0.05)) * 1.05
    sz = np.exp(math.log(size[0]) + (math.log(size[1]) - math.log(size[0])) * rnd.uniform(m) ** 1.4) * d.R
    grains(cv, px, py, sz / 2.0, np.minimum(cols, 1.2), alpha, rnd, spec=0.35)
    return cv


def sample_polar_tex(tex, tt, u):
    """Bilinear lookup of a polar texture tex (n_ang, n_rad): tt in 0..1 (angle share, periodic), u in 0..1 (radial share)."""
    na, nr = tex.shape
    x = (np.asarray(tt, np.float32) % 1.0) * na - 0.5
    y = np.clip(np.asarray(u, np.float32), 0.0, 1.0) * (nr - 1)
    x0 = np.floor(x).astype(np.int32)
    wx = (x - x0).astype(np.float32)
    y0 = np.minimum(np.floor(y).astype(np.int32), nr - 2)
    wy = (y - y0).astype(np.float32)
    xa, xb = x0 % na, (x0 + 1) % na
    a = tex[xa, y0] * (1 - wy) + tex[xa, y0 + 1] * wy
    b = tex[xb, y0] * (1 - wy) + tex[xb, y0 + 1] * wy
    return a * (1 - wx) + b * wx


# ----------------------------------------------------------------------------- limbus breakup
def limbus_breakup(cv, ctx, d, rnd, emis, strength=1.0, rho_max=1.11, lift=1.25, step=128, rho_min=1.0, arcs=None, thr0=0.22, thr1=0.72):
    """The iris's own band 0.92-0.99 R shown again at rho_min-rho_max R through a noise mask with holes: the rim looks as if
    it were turning into matter while the iris itself is untouched (drawn BEFORE the iris; only pixels outside rho_min). arcs: optional
    1-D angular weight (30 % of the circumference erodes, the rest stays crisp). Only the pixels of the ring are computed (index lists)."""
    W, H = ctx.W, ctx.H
    R = d.R
    reach = rho_max * R
    x0, y0 = max(0, int(d.cx - reach)), max(0, int(d.cy - reach))
    x1, y1 = min(W, int(d.cx + reach) + 2), min(H, int(d.cy + reach) + 2)
    n_ang, n_rad = 2048, 96
    tex = C.fbm_polar(n_ang, n_rad, rnd, octaves=4, base=(72, 4), gain=0.62)                    # holes 0.009-0.05 R
    low = C.fbm_polar(512, 24, rnd, octaves=3, base=(40, 3), gain=0.5)
    tmin, tmax = float(tex.min()), float(tex.max())
    dx = (np.arange(x0, x1, dtype=np.float32) + np.float32(0.5 - d.cx))[None, :]
    arcs_ext = None if arcs is None else np.concatenate([arcs, arcs[:1]]).astype(np.float32)
    for r0 in range(y0, y1, step):
        r1 = min(y1, r0 + step)
        dy = (np.arange(r0, r1, dtype=np.float32) + np.float32(0.5 - d.cy))[:, None]
        rho2 = (dx * dx + dy * dy) / np.float32(R * R)
        band = (rho2 > (rho_min - 0.005) ** 2) & (rho2 < rho_max ** 2)
        iy, ix = np.nonzero(band)
        if not len(iy):
            continue
        ddx = np.broadcast_to(dx, rho2.shape)[iy, ix]
        ddy = np.broadcast_to(dy, rho2.shape)[iy, ix]
        rho = np.sqrt(rho2[iy, ix])
        th = np.arctan2(ddy, ddx)
        u = np.clip((rho - rho_min) / (rho_max - rho_min), 0.0, 1.0)
        tt = (th % TWO_PI) / TWO_PI
        v = sample_polar_tex(tex, tt, u)
        lo = sample_polar_tex(low, tt, u)
        s_ang = 0.45 + 0.55 * emis.strength_at(th)
        thr = thr0 + thr1 * u ** 0.8 - 0.22 * (s_ang - 0.5) * strength
        v0 = (v - tmin) / max(tmax - tmin, 1e-6)
        alpha = C.smoothstep((v0 - thr) / 0.16) * (1.0 - C.smoothstep((u - 0.75) / 0.25))
        if arcs_ext is not None:
            alpha = alpha * np.interp(tt, np.arange(len(arcs_ext)) / (len(arcs_ext) - 1), arcs_ext).astype(np.float32)
        keep = alpha > 0.004
        if not keep.any():
            continue
        iy, ix, th, lo, alpha = iy[keep], ix[keep], th[keep], lo[keep], alpha[keep]
        rho_s = 0.99 - 0.07 * lo
        col = K.sample_disc(d, rho_s, th) * np.float32(lift)
        col = np.minimum(col, 1.2)
        a = (alpha * np.float32(0.96))[:, None].astype(np.float32)
        reg = cv[r0:r1, x0:x1]
        cur = reg[iy, ix]
        reg[iy, ix] = cur * (1.0 - a) + col * a
    return cv
