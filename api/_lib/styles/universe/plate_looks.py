# -*- coding: utf-8 -*-
"""uni_plate_looks: the three single-eye UNIVERSE looks that use a generated plate (AD round 2c): Deep Field (P-UV-DUST), Vortex (P-DN-SPIRAL),
Starfield (P-UV-MILKY). numpy + PIL only; the plates are mono luminance images tinted here by the eye's own colours.

  Deep Field  the Echo fill at 0.45 x, a luminous dust plate (void hidden behind the iris) gradient-mapped in the eye's hue with warm knots, dark
              lanes, stars; NO wedge streaks (the AD read them as sun rays and as 'Echo plus rays')
  Vortex      Echo fill under a P-DN-SPIRAL plate with a crisp circular void registered to 1.10 R on the iris centre, the eye's own band turned into an
              accretion ring (luminance equalised round the circle, x1.15, bloom 0.04 R at 20 percent, computed once on a window so nothing is blurred
              per band), recess shadow, stars and a few diffraction stars. Yellow eyes are clamped (no acid lime), grey eyes go warm-neutral silver
  Starfield   blue-black sky, the Milky Way plate with a photographic palette (eye hue in the lanes and the body, warm core), luminance ceiling 0.9,
              contrast x1.15, dark well 0.75, stars; the crisp plate stars are band-limited at a scale that does not depend on the canvas size
Every band is computed on a halo (see uni_engine.render_bands) so no blur, resize or upsample ever sees a band edge.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_plate_looks.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports, no fall back to a picture without the plate); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.
# WP8B (step B) moved the seed, the plates version of every pick and the pair's fallback and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import math

import numpy as np
from PIL import Image

from .common import C, smooth, luma, ramp_rgb
from . import engine as EN
from .engine import SplatList
from . import fill as FL
from . import matter as MT
from . import plates as PL
from . import looks as LK
from . import flakes as FK

COPPER5 = ("#1A0C05", "#3B1C0C", "#8A4A1F", "#C98545", "#F0C48C")
SILVER5 = ("#0B0D10", "#2A2E33", "#6E7680", "#B8C0C8", "#EEF2F5")


def dominant(src):
    st = src.stats
    return float(st["h"]), float(st["C"]), float(st["L"])


def _ramp(cols, t):
    cu = np.array([C.rgb01(h) for h in cols], np.float32)
    pos = t * 4.0
    i = np.minimum(pos.astype(np.int32), 3)
    f = (pos - i)[:, None]
    return cu[i] * (1 - f) + cu[i + 1] * f


def _is_neutral(src):
    return src.cls == "grey" or float(src.stats["C"]) < 14.0


def plate_lut(src, kind, N=256):
    """Gradient map luminance -> colour, from the eye's own hues. kind 'vortex' / 'dust': dust lanes near black, body in the dominant hue (chroma the
    eye's own, a little richer, clamped: no acid lime for hues 95-115), knots in the secondary hue H2 lifted. kind 'milky': a photographic Milky
    Way (see milky_lut). dark_brown uses the copper ramp, grey and very pale eyes a warm-neutral silver ramp (no khaki). Returns (N, 3) 0..1."""
    t = np.linspace(0, 1, N).astype(np.float32)
    if kind == "milky":
        return milky_lut(src, N)
    h0, C0, L0 = dominant(src)
    h2, c2 = src.h2
    if abs(c2 - 18.0) < 1e-6:
        h2, c2 = 80.0, 30.0
    cls = src.cls
    Lb = np.where(t < 0.12, 2.0 + 6.0 * (t / 0.12), 8.0 + 47.0 * np.clip((t - 0.12) / 0.62, 0, 1) ** 0.9)
    Lb = np.where(t > 0.74, 55.0 + 27.0 * np.clip((t - 0.74) / 0.26, 0, 1), Lb)
    k_w = smooth((t - 0.76) / 0.22) * 0.85
    Cd = min(max(C0 * 1.25, 15.0), 52.0)
    if 92.0 <= h0 <= 118.0:
        Cd = min(Cd, 38.0)                                # yellow-green eyes: rich, never acid lime
    Cb = Cd * np.clip(0.30 + 1.1 * np.sqrt(t), 0, 1.15) * (1 - 0.35 * k_w)
    Ck = min(max(c2 * 1.1, 20.0), 34.0)
    hue = np.degrees(np.angle(np.exp(1j * np.radians(h0)) * (1 - k_w) + np.exp(1j * np.radians(h2)) * k_w)) % 360.0
    Cc = Cb * (1 - k_w) + Ck * k_w
    rgb = C.from_lch(Lb, Cc, hue).astype(np.float32)
    if cls == "dark_brown":
        rgb = _ramp(COPPER5, t)
    elif _is_neutral(src):
        rgb = _ramp(SILVER5, t)
        rgb = np.minimum(rgb * (0.78 + 0.2 * t[:, None]) * np.array([1.035, 1.0, 0.955], np.float32), 1.0)
    return np.clip(rgb, 0, 1)


def milky_lut(src, N=256):
    """A photographic Milky Way: lanes dark with the eye's hue at 25 percent chroma, a near-neutral body that takes the eye's hue (chroma 8-16), a warm
    core from H2 (gold by default). EyeArt sells its coloured Milky Way as a best seller: a photographic palette is allowed here (AD C8 / D8)."""
    t = np.linspace(0, 1, N).astype(np.float32)
    h0, C0, L0 = dominant(src)
    h2, c2 = src.h2
    if abs(c2 - 18.0) < 1e-6:
        h2, c2 = 76.0, 26.0
    cls = src.cls
    Lb = np.where(t < 0.10, 1.5 + 6.0 * (t / 0.10), 7.5 + 50.0 * np.clip((t - 0.10) / 0.62, 0, 1) ** 0.9)
    Lb = np.where(t > 0.72, 57.5 + 34.0 * np.clip((t - 0.72) / 0.28, 0, 1), Lb)
    k_w = smooth((t - 0.70) / 0.26) * 0.9
    lane = 1.0 - smooth(t / 0.14)
    Cbody = 8.0 + 8.0 * smooth((t - 0.10) / 0.5)
    Cbody = Cbody * (1.0 - lane) + min(C0 * 0.25, 10.0) * lane
    Ck = min(max(c2 * 0.9, 18.0), 30.0)
    hue = np.degrees(np.angle(np.exp(1j * np.radians(h0)) * (1 - k_w) + np.exp(1j * np.radians(h2)) * k_w)) % 360.0
    Cc = Cbody * (1 - k_w) + Ck * k_w
    rgb = C.from_lch(Lb, Cc, hue).astype(np.float32)
    if cls == "dark_brown":
        rgb = 0.55 * _ramp(COPPER5, t) + 0.45 * rgb
    elif _is_neutral(src):
        rgb = _ramp(SILVER5, t) * np.array([0.98, 1.0, 1.04], np.float32)
        rgb = np.minimum(rgb * (0.85 + 0.15 * t[:, None]), 1.0)
    return np.clip(rgb, 0, 1)


def plate_t(p, body=0.72, knee=0.88):
    """Plate luminance -> LUT position: the body of the plate stays in the dominant hue (t <= 0.72), only the brightest knots reach the secondary hue."""
    return body * np.minimum(p / knee, 1.0) ** 1.05 + (1.0 - body) * 0.8 * smooth((p - 0.90) / 0.10)


def lut_apply(lut, t):
    idx = np.clip(t * (len(lut) - 1), 0, len(lut) - 1)
    i0 = np.minimum(idx.astype(np.int32), len(lut) - 2)
    f = (idx - i0)[..., None]
    return lut[i0] * (1 - f) + lut[i0 + 1] * f


def diffraction_stars(scene, n, tag="dstars", max_arm=0.010, lift_t=0.95):
    rnd = scene.rand(tag)
    xs = rnd.uniform(n, 0.05, 0.95) * scene.W
    ys = rnd.uniform(n, 0.05, 0.95) * scene.H
    arm = rnd.uniform(n, 0.4, 1.0) * max_arm * scene.S
    amp = rnd.uniform(n, 0.35, 0.9)
    col = ramp_rgb(scene.eyes[0].src, np.full(n, lift_t, np.float32), Lmax=97.0, gain=0.25)
    return xs, ys, arm, amp, col


def _sparkle_fn(stars):
    xs, ys, arm, amp, col = stars

    def fn(scene, cv, y0, y1):
        pad = float(arm.max()) * 1.2 + 3
        m = (ys > y0 - pad) & (ys < y1 + pad)
        if m.any():
            C.sparkles(cv, xs[m], ys[m] - y0, arm[m], col[m], amp[m], core=0.9)
    return fn


def _dark_fill(scene, y0, y1, lum_k):
    f = scene.f
    Fd, rn, e, kk = LK._fill_dark(scene, y0, y1, lum_k=lum_k)
    return Fd, rn, e


# =============================================================================== Deep Field
class DeepField:
    NAME = "deepfield"

    def halo_rows(self, scene):
        return 6 * scene.f + 2

    def prepare(self, scene):
        LK._prepare_eyes(scene, 2.6)
        e = scene.eyes[0]
        src = e.src
        rnd = scene.rand("deep")
        self.wind = LK._wind(scene)
        self.stars = MT.star_field(scene, 190)
        self.dstars = diffraction_stars(scene, 5 + int(rnd.uniform() * 4), max_arm=0.008)
        # the dust plate: the void (radius r0 x 1.06 S, the plate is never enlarged more than x1.1) hides behind the iris, the bright filaments start at the rim
        self.lut = plate_lut(src, "dust")
        pick = PL.pick_deep(rnd, scene.pv)
        pcx, pcy, r0 = PL.void_of(pick)
        r_void = r0 * 1.10 * scene.S
        self.plate = PL.Placed(pick, scene.W, scene.H, e.cx, e.cy, r_void_px=r_void, mirror=rnd.uniform() < 0.5, grid_f=scene.f)
        scene.info["plate"] = self.plate.info
        self.flakes = FK.fibre_flakes(scene, 0, 70, reach=1.3, taper=0.6, lift=LK._flake_lift(e), alpha=(0.7, 0.9), tag="dflakes", jets=(8, 12))
        LK._text_cull(scene, self.stars, self.flakes)
        self.layers = ([("fnc", self.dust_fn, "screen")] if self.plate is not None else []) + [("sprites", self.flakes, "over"), ("splat", self.stars, "screen"),
                                                                                           ("fn", _sparkle_fn(self.dstars), None)]

    def base(self, scene, cv, y0, y1):
        f = scene.f
        Fd, rn, e = _dark_fill(scene, y0, y1, 0.45)
        acc = LK._accent_layer(scene, y0, y1, f, "deep/accent", 1.0)
        Fd = 1.0 - (1.0 - Fd) * (1.0 - 0.14 * np.minimum(acc, 1.0))
        Fd *= LK._vignette_field(scene, y0, y1, f, 0.50)
        cv += scene.up(Fd, f, y0, y1)

    def dust_fn(self, scene, lay, y0, y1, f):
        p = self.plate.band(y0, y1, f)
        x, y = scene.band_xy(y0, y1, f)
        e0 = scene.eyes[0]
        r = np.sqrt((x - e0.cx) ** 2 + (y - e0.cy) ** 2) / np.float32(e0.R)
        q = np.clip(p / 0.85, 0, 1)
        q = q * q * (1.45 - 0.45 * q)                   # deeper dust lanes, brighter filaments
        col = lut_apply(self.lut, plate_t(q, body=0.74, knee=0.90))
        rim = smooth((r - 0.98) / 0.22)                 # the plate fades in just outside the limb (it is hidden under the iris anyway)
        lay += col * (np.minimum(1.0, q * 1.6) * 1.15 * rim)[..., None]


# =============================================================================== Vortex
class Vortex:
    NAME = "vortex"

    def halo_rows(self, scene):
        return 6 * scene.f + 2

    def prepare(self, scene):
        LK._prepare_eyes(scene, 3.0)
        e = scene.eyes[0]
        src = e.src
        rnd = scene.rand("vortex")
        self.lut = plate_lut(src, "vortex")
        pick = PL.pick_vortex(rnd, scene.pv)
        pcx, pcy, r0 = PL.void_of(pick)
        r_void = min(1.10 * e.R, 1.08 * r0 * scene.S)       # void registered to 1.10 R on the iris centre (crisp, circular plates only), never enlarged more than x1.1
        self.plate = PL.Placed(pick, scene.W, scene.H, e.cx, e.cy, r_void_px=r_void, mirror=rnd.uniform() < 0.5, grid_f=scene.f)
        self.r_void_n = r_void / e.R                       # the plate's crisp void edge, in R: the plate fades in over 0.08 R beyond it (a visible void edge is a hard fail)
        scene.info["plate"] = self.plate.info
        self.stars = MT.star_field(scene, 1200, sig_range=(0.0005, 0.0011))
        self.dstars = diffraction_stars(scene, 15 + int(rnd.uniform() * 6))
        self.twirl_sign = 1.0 if rnd.uniform() < 0.5 else -1.0
        self._build_ring(scene)
        LK._text_cull(scene, self.stars)
        self.layers = ([("fnc", self.plate_fn, "screen")] if self.plate is not None else []) + [("fnc", self.ring_fn, "screen"), ("splat", self.stars, "screen"),
                                                                                           ("fn", _sparkle_fn(self.dstars), None)]

    def _build_ring(self, scene):
        """The accretion ring from the eye's own band 0.86-0.98 R, turned into 1.00-1.30 R (twirl 40 deg x u^1.3), on a square WINDOW of the coarse
        grid built once (so the bloom blur never sees a band edge). Luminance equalised round the circle (the lopsided bright crescent of round 2b
        came from the eye's own bright and dark sectors), x 1.15, bloom 0.04 R at 20 percent, a little cross-flow blur and 8 percent noise."""
        e0 = scene.eyes[0]
        src = e0.src
        f = scene.f
        R = e0.R
        reach = 1.50
        I0 = max(int(math.floor((e0.cx - reach * R) / f)), 0)
        J0 = max(int(math.floor((e0.cy - reach * R) / f)), 0)
        I1 = min(int(math.ceil((e0.cx + reach * R) / f)), int(math.ceil(scene.W / f)))
        J1 = min(int(math.ceil((e0.cy + reach * R) / f)), int(math.ceil(scene.H / f)))
        X = ((np.arange(I0, I1, dtype=np.float32) + 0.5) * f)[None, :]
        Y = ((np.arange(J0, J1, dtype=np.float32) + 0.5) * f)[:, None]
        dx, dy = X - e0.cx, Y - e0.cy
        r = np.sqrt(dx * dx + dy * dy) / np.float32(R)
        th = np.arctan2(np.broadcast_to(dy, r.shape), np.broadcast_to(dx, r.shape))
        m = (r > 0.985) & (r < 1.45)
        rr = r[m]
        thm = th[m]
        u = np.clip((rr - 1.02) / 0.26, 0, 1)
        thm = thm - np.radians(40.0) * (u ** 1.3) * self.twirl_sign
        rho = 0.86 + 0.12 * u
        sx = np.clip(src.R + rho * src.R * np.cos(thm) - 0.5, 0, src.tgt - 1.001)
        sy = np.clip(src.R + rho * src.R * np.sin(thm) - 0.5, 0, src.tgt - 1.001)
        x0 = np.floor(sx).astype(np.int64)
        y0 = np.floor(sy).astype(np.int64)
        fx, fy = (sx - x0)[:, None], (sy - y0)[:, None]
        g = src.g
        col = g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x0 + 1] * fx * (1 - fy) + g[y0 + 1, x0] * (1 - fx) * fy + g[y0 + 1, x0 + 1] * fx * fy
        Ls, Cc, hh = C.lch(col)
        # luminance equalisation: divide by the angular mean luminance of the source band, (partly: 70 percent)
        nb = 72
        bi = np.minimum(((thm % (2 * math.pi)) * (nb / (2 * math.pi))).astype(np.int64), nb - 1)
        mean_L = np.bincount(bi, weights=Ls, minlength=nb) / np.maximum(np.bincount(bi, minlength=nb), 1)
        k = np.ones(9) / 9.0
        pad = np.concatenate([mean_L[-4:], mean_L, mean_L[:4]])
        mean_L = np.convolve(pad, k, "valid")
        Lref = float(mean_L.mean())
        fac = np.clip(Lref / np.maximum(mean_L[bi], 1.0), 0.45, 2.4)            # full equalisation: the ring is as bright on one side as on the other
        Lo = np.clip((Ls * fac * 1.25 + 10.0) * 1.15, 0, 84)
        Co = np.minimum(Cc * 1.6 + 6.0, 70.0)
        hue_lime = (hh > 92) & (hh < 120)
        Co = np.where(hue_lime, np.minimum(Co, 38.0), Co)
        if src.cls == "grey" or float(src.stats["C"]) < 14.0:
            Co = np.minimum(Co, 10.0)
        rgb = C.from_lch(Lo, Co, hh).astype(np.float32)
        a = smooth((rr - 0.985) / 0.03) * (0.25 + 0.75 * np.exp(-(rr - 1.02) / 0.12)) * (1.0 - smooth((rr - 1.22) / 0.20))
        ring = np.zeros(r.shape + (3,), np.float32)
        ring[m] = rgb * a[:, None]
        sg = 0.75 * scene.S / 1024.0 / f
        if sg > 0.3:
            ring = C.blur(ring, sg)
        nz = C.value_noise2d(ring.shape[1], ring.shape[0], 140, scene.rand("vortex/ringnoise"))
        ring *= (1.0 + 0.08 * (2.0 * nz - 1.0) * 1.6)[..., None].astype(np.float32)        # 8 percent noise kills the vinyl streaks
        bloom = C.blur(ring, 0.04 * R / f) * 0.20
        self.ring_win = (I0, J0, (ring + bloom).astype(np.float32))

    def base(self, scene, cv, y0, y1):
        f = scene.f
        Fd, rn, e = _dark_fill(scene, y0, y1, 0.55)
        Fd *= LK._vignette_field(scene, y0, y1, f, 0.40)
        cv += scene.up(Fd, f, y0, y1)

    def plate_fn(self, scene, lay, y0, y1, f):
        e0 = scene.eyes[0]
        p = self.plate.band(y0, y1, f)
        col = lut_apply(self.lut, plate_t(p))
        x, y = scene.band_xy(y0, y1, f)
        r = np.sqrt((x - e0.cx) ** 2 + (y - e0.cy) ** 2) / np.float32(e0.R)
        rec = 1.0 - 0.55 * (1.0 - smooth((r - 1.0) / 0.10))        # recess shadow: multiply 0.45 at the limb, gone at 1.10 R
        fv = smooth((r - self.r_void_n) / 0.09)                    # fade-in beyond the plate's void edge: no visible edge
        lay += col * (np.minimum(1.0, p * 2.2) * rec * fv)[..., None]

    def ring_fn(self, scene, lay, y0, y1, f):
        I0, J0, arr = self.ring_win
        hc, Wc = lay.shape[:2]
        j_lo = y0 // f
        ja, jb = max(J0, j_lo), min(J0 + arr.shape[0], j_lo + hc)
        ia, ib = max(I0, 0), min(I0 + arr.shape[1], Wc)
        if ja >= jb or ia >= ib:
            return
        lay[ja - j_lo:jb - j_lo, ia:ib] += arr[ja - J0:jb - J0, ia - I0:ib - I0]


# =============================================================================== Starfield
class Starfield:
    NAME = "starfield"

    def halo_rows(self, scene):
        return int(math.ceil(10.0 * scene.S / 1024.0)) + 8 * scene.f

    def prepare(self, scene):
        e = scene.eyes[0]
        src = e.src
        e.fill_mode = "none"
        e.fibre_noise = None
        e.k_s, e.s, e.magnification = 1.0, 1.0, 1.0
        rnd = scene.rand("starfield")
        entry, mirror, rot, tgt = PL.milky_choice(rnd, 32.0, 12.0, scene.pv)
        rot = float(np.clip(rot, -5.0, 5.0))
        scale = 1.10 * scene.S / 1024.0              # x1.10 the canvas: the plate covers the canvas through its rotation, never enlarged more than x1.1
        cx = scene.W / 2.0 + (rnd.uniform() - 0.5) * 0.02 * scene.S
        cy = scene.H / 2.0 + (rnd.uniform() - 0.5) * 0.02 * scene.S
        self.plate = PL.Placed(entry, scene.W, scene.H, cx, cy, scale=scale, angle_deg=rot, mirror=mirror, centre=(0.5, 0.5))
        scene.info["plate"] = self.plate.info
        self.lut = plate_lut(src, "milky")
        self.star_col = ramp_rgb(src, np.full((1,), 0.93, np.float32), Lmax=96.0, gain=0.3)[0]
        self.stars = MT.star_field(scene, 900 + int(rnd.uniform() * 500), sig_range=(0.0005, 0.0012), bright=(0.08, 0.95))
        self.dstars = diffraction_stars(scene, 9 + int(rnd.uniform() * 6), max_arm=0.010)
        LK._text_cull(scene, self.stars)
        self._hi = None
        self.layers = [("fn", self.hi_fn, None), ("splat", self.stars, "screen"), ("fn", _sparkle_fn(self.dstars), None)]

    def base(self, scene, cv, y0, y1):
        """Sky gradient + the gradient-mapped Milky Way band (soft knee, ceiling 0.9, contrast x1.15), the well round the iris (1.0-1.25 R multiply 0.75)
        and the vignette, all on the coarse grid; the crisp plate stars (its high frequencies) are added after by hi_fn."""
        f = scene.f
        hc, Wc = scene.grid(y0, y1, f)
        yy = (y0 + (np.arange(hc, dtype=np.float32) + 0.5) * f) / scene.H
        top, bot = C.rgb01("#03040A"), C.rgb01("#070A12")
        sky = np.broadcast_to(top[None, None, :] * (1 - yy)[:, None, None] + bot[None, None, :] * yy[:, None, None], (hc, Wc, 3))
        p = self.plate.band(y0, y1, 1) if self.plate is not None else np.zeros((y1 - y0, scene.W), np.float32)
        pc = C.box_reduce(p, f) if f > 1 else p
        pc = pc[:hc, :Wc]
        if pc.shape[0] < hc or pc.shape[1] < Wc:
            pc = np.pad(pc, ((0, hc - pc.shape[0]), (0, Wc - pc.shape[1])), mode="edge")
        lo_c = C.blur(pc, 0.6 * scene.S / 1024.0 / f + 0.3)
        t = 0.97 * (1.0 - np.exp(-2.5 * lo_c))                     # soft curve: the core keeps its dust lanes instead of clipping flat
        t = np.clip(t, 0.0, 1.0) ** (1.0 / 1.15) * 1.0             # contrast x1.15 on the brights
        t = np.where(t > 0.5, 0.5 + (t - 0.5) * 1.15, t)
        body = 0.95 * np.tanh(lut_apply(self.lut, np.clip(t, 0, 1)) / 0.95)
        Fd = 1.0 - (1.0 - sky) * (1.0 - 0.97 * body)              # screen
        rn, e, kk = scene.band_fields(y0, y1, f)
        Fd = Fd * (1.0 - 0.25 * (1.0 - smooth(np.maximum(e, 0.0) / 0.25)))[..., None]      # well 0.75 over 0.25 R (AD)
        Fd = Fd * LK._vignette_field(scene, y0, y1, f, 0.45)
        cv += scene.up(Fd, f, y0, y1)
        lo = scene.up(lo_c, f, y0, y1)
        hi = C.blur(np.maximum(p - lo, 0.0), 0.65 * scene.S / 1024.0)        # band-limited to the same scale at every size: the two plate LODs carry different star detail
        self._hi = hi * scene.up(np.broadcast_to(LK._vignette_field(scene, y0, y1, f, 0.45)[..., 0], (hc, Wc)), f, y0, y1)

    def hi_fn(self, scene, cv, y0, y1):
        hi = self._hi
        C.screen(cv, self.star_col[None, None, :] * np.minimum(hi * 1.4, 0.9)[..., None], 1.0)
