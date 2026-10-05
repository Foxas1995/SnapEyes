# -*- coding: utf-8 -*-
"""uni_engine: the band renderer of the UNIVERSE family (scratch prototype). numpy + PIL only.

A universe artwork is drawn in horizontal bands (rows y0..y1 of the canvas) so a 4096 px master never holds more than a
few 4096 x band_h float arrays (peak memory budget 900 MB). Every layer is a pure function of the canvas position (or a
splat list rasterised with energy-conserving stamps), so the result does not depend on the band height and a 4096
render is the 1024 picture with more pixels.

Pipeline:  scene (layout, F3 discs, per-eye source) -> for each band: base layers -> splat layers -> post layers ->
tone map -> dither -> uint8 band;  then the irises are pasted LAST (solo plain, pair S weave, group single front);
then the customer's names (the only text).
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_engine.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports, ASCII escapes for the two glyphs of the names line); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.
# WP8B (step B) moved the seed, the plates version of every pick and the pair's fallback and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import math
import time

import numpy as np
from PIL import Image, ImageDraw

from .common import (C, L, smooth, luma, get_src, f3_disc, enlarge_band, ramp_rgb, peak_rss_mb, FILL_SD)
from . import layout as LO
from . import comp as CO
from .. import pupil as PUP
from .. import seeds as SD

BAND_PX = 2 * 1024 * 1024    # pixels per band (a 4096 px master never holds more than a few 4096 x 512 float arrays)
WORK_MAX = 1200          # smooth layers are computed on a grid whose long side is at most this many px
GAMMA = 2.2


def to_lin(x):
    return np.power(np.maximum(x, 0.0), GAMMA, dtype=np.float32) if x.dtype == np.float32 else np.power(np.maximum(x, 0.0), GAMMA)


def to_disp(x):
    return np.power(np.maximum(x, 0.0), np.float32(1.0 / GAMMA))


class DesignChanged(ValueError):
    """The plan froze a choice that the eyes of this render contradict (the plan says the weave of a pair and the pupils now say the Kiss geometry): never another
    picture than the approved one, so the caller holds the order. `why` names it."""

    def __init__(self, msg, why="design_changed"):
        super().__init__(msg)
        self.why = why


# ----------------------------------------------------------------------------- eyes and scene
class Eye:
    pass


class Scene:
    def __init__(self, look, irises, size, aspect=None, names=None, opts=None, key=None, frozen=None):
        self.look = look
        self.irises = list(irises)
        self.n = len(irises)
        self.opts = dict(opts or {})
        self.pv = key.get("pv") if isinstance(key, dict) else None          # the plates version of the plan: every plate pick takes it
        self.frozen = dict(frozen or {})                                  # what the plan fixed before the render (the pair's fallback)
        self.names = [n for n in (names or []) if n]
        self.date = self.opts.get("date")
        self.has_text = bool(self.names or self.date)
        srcs = [get_src(ir, len(irises)) for ir in irises]
        aspect = aspect or self.opts.get("aspect")
        if self.n == 1:
            lay = LO.solo(look, size, aspect or "1:1", self.has_text, self.opts.get("r_scale", 1.0))
        elif self.n == 2:
            ua = (1.0, 0.0)
            ang = 0.0
            asp = aspect or "3:2"
            if asp == "1:1":
                ang = math.radians(35.0)
            elif asp == "4:5":
                ang = math.radians(60.0)
            ua = (math.cos(ang), -math.sin(ang))
            ra = PUP.reach(srcs[0].pup, ua)
            rb = PUP.reach(srcs[1].pup, (-ua[0], -ua[1]))
            lay = LO.duo(size, reach_a=ra, reach_b=rb, aspect=asp, names=self.has_text,
                         d_override=self.opts.get("d_override"), kiss=self.opts.get("kiss"))
            if "fallback" in self.frozen and self.opts.get("kiss") is None:
                # what the plan fixed before the render is obeyed (the master is ANOTHER image of the same eyes: its pupils, measured on its own 1024 px grade, can
                # sit on the other side of the limit than the sealed profile's): the Kiss distance is forced, a weave the pupils no longer allow is refused
                want, got = self.frozen["fallback"] == "kiss", bool(lay.info.get("overlap_fallback"))
                if want and not got:
                    lay = LO.duo(size, reach_a=ra, reach_b=rb, aspect=asp, names=self.has_text, d_override=self.opts.get("d_override"), kiss=True)
                elif got and not want:
                    raise DesignChanged("the plan draws the weave, but the pupils of these eyes need %.3f R (the limit is the Kiss fallback)" % lay.info["d_needed"])
        elif 3 <= self.n <= 6:
            lay = LO.group(self.n, size, names=self.has_text, layout=self.opts.get("layout"), d=self.opts.get("d_group", LO.GROUP_D),
                           aspect=aspect, rotate=self.opts.get("rotate", 0), trio_base=self.opts.get("trio_base", "crumble"))
        else:
            raise ValueError("universe supports 1-6 eyes")
        LO.check(lay)
        self.layout = lay
        self.W, self.H, self.S = lay.W, lay.H, lay.S
        self.size = size
        self.scale = self.S / 1024.0
        self.eyes = []
        for i, (ir, sl) in enumerate(zip(irises, lay.slots)):
            e = Eye()
            e.iris, e.src, e.index = ir, srcs[i], i
            d = f3_disc(ir, sl.cx, sl.cy, sl.R, i)
            e.disc = d
            e.cx, e.cy, e.R = float(sl.cx), float(sl.cy), float(sl.R)      # the IDEAL geometry drives matter, fill and fields (the same picture at every canvas size);
            e.snap = (d.cx, d.cy, d.R)                                       # the disc is snapped to whole pixels: only the compositor reads that
            self.eyes.append(e)
        if self.opts.get("seed_mode") == "legacy":
            # the seed before step B (WP8B): the bytes of the irises, the look and the layout key; the laboratory's before and after look and the replay of step A
            self.seed = C.design_seed(irises, look, lay.key + f"/r{self.opts.get('rotate', 0)}/s{int(bool(self.opts.get('swap', False)))}")      # names and date never change the picture (1.7.8)
            self.eye_seeds = [C.seed_for(ir.raw, i, look, lay.key) for i, ir in enumerate(irises)]
        else:
            if not isinstance(key, dict):
                raise ValueError("a render needs the plan's seed key (seeds.py) or opts seed_mode legacy")
            # names, date, canvas, size and pixels are NOT in the seed: a typo in a name must never reshuffle the matter, a preview and a master draw the same
            self.seed = SD.seed_for_key([ir.eye_id for ir in irises], key)
            self.eye_seeds = [SD.eye_seed(self.seed, i) for i in range(self.n)]
        R0 = float(np.mean([e.R for e in self.eyes]))
        self.R = R0
        self.cxs = np.array([e.cx for e in self.eyes], np.float32)
        self.cys = np.array([e.cy for e in self.eyes], np.float32)
        self.Rs = np.array([e.R for e in self.eyes], np.float32)
        self.cx_mean, self.cy_mean = float(self.cxs.mean()), float(self.cys.mean())
        self.band_rows = int(max(128, min(self.H, (BAND_PX // max(self.W, 1)) // 8 * 8)))     # 2 Mpx bands: the whole canvas at 1024, 512 rows at 4096 (multiple of 8)
        self.wf = max(1, int(math.ceil(max(self.W, self.H) / float(WORK_MAX))))   # work-grid factor of smooth layers
        self.f = 1 if self.S <= 1536 else (2 if self.S <= 2304 else 3)   # coarse factor of the SOFT content (fill, plates, haze): a 4096 master is worked at 1365
        self.fs = 1                                   # sprites (flakes, chips) are drawn at full resolution: crisp edges at every size
        self.times = {}
        self.info = {}

    def rand(self, tag, eye=None):
        return C.Rand(self.seed if eye is None else self.eye_seeds[eye], tag)

    # -- geometry helpers for a band
    def grid(self, y0, y1, f=1):
        """(rows, cols) of the coarse grid covering canvas rows y0..y1 (y0 a multiple of f)."""
        return int(math.ceil((y1 - y0) / float(f))), int(math.ceil(self.W / float(f)))

    def band_xy(self, y0, y1, f=1):
        """Pixel-centre coordinates (canvas px) of the coarse grid of rows y0..y1: x (1, Wc), y (hc, 1)."""
        hc, Wc = self.grid(y0, y1, f)
        x = ((np.arange(Wc, dtype=np.float32) + np.float32(0.5)) * np.float32(f))[None, :]
        y = (np.float32(y0) + (np.arange(hc, dtype=np.float32) + np.float32(0.5)) * np.float32(f))[:, None]
        return x, y

    def band_fields(self, y0, y1, f=1):
        """rn: distance to the nearest iris centre in units of that iris's R; e: distance outside the union outline in units
        of R (negative inside), both (hc, Wc) float32; k: index of the nearest iris (by rn)."""
        x, y = self.band_xy(y0, y1, f)
        hc, Wc = self.grid(y0, y1, f)
        rn = None
        kk = np.zeros((hc, Wc), np.int8)
        for k in range(self.n):
            r = np.sqrt((x - self.cxs[k]) ** 2 + (y - self.cys[k]) ** 2) / self.Rs[k]
            if rn is None:
                rn = r
            else:
                m = r < rn
                kk[m] = k
                rn = np.where(m, r, rn)
        return rn, rn - 1.0, kk

    def up(self, a, f, y0, y1):
        """A coarse-grid array (hc, Wc[, 3]) brought back to the canvas rows y0..y1 (h, W[, 3]): bicubic, block centres to block centres."""
        if f == 1:
            return a
        h = y1 - y0
        hc, Wc = a.shape[:2]
        if a.ndim == 2:
            im = Image.fromarray(np.ascontiguousarray(a, np.float32), "F").resize((Wc * f, hc * f), Image.BICUBIC)
            return np.asarray(im, np.float32)[:h, :self.W]
        out = np.empty((h, self.W, a.shape[2]), np.float32)
        for k in range(a.shape[2]):
            im = Image.fromarray(np.ascontiguousarray(a[..., k], np.float32), "F").resize((Wc * f, hc * f), Image.BICUBIC)
            out[..., k] = np.asarray(im, np.float32)[:h, :self.W]
        return out


# ----------------------------------------------------------------------------- coarse noise, evaluated per band
class NoiseGrid:
    """Value noise 0..1 that is the same picture at any canvas size: `cells` cells across the SHORT side of the canvas, evaluated
    on any band with a PIL bicubic resize of a small random grid (mode F). Several octaves = fbm."""

    def __init__(self, scene, seed_tag, cells=6, octaves=4, gain=0.55, lac=2.0, rnd=None):
        self.W, self.H, self.S = scene.W, scene.H, scene.S
        rnd = rnd or scene.rand("noise/" + seed_tag)
        self.grids = []
        self.weights = []
        amp = 1.0
        for o in range(octaves):
            c = cells * (lac ** o)
            gw = int(math.ceil(c * self.W / self.S)) + 4
            gh = int(math.ceil(c * self.H / self.S)) + 4
            g = rnd.uniform((gh, gw)).astype(np.float32)
            self.grids.append((g, c))
            self.weights.append(amp)
            amp *= gain
        self.total = sum(self.weights)

    def band(self, y0, y1, out_w=None, out_h=None, x0=0, x1=None):
        """fbm 0..1 for canvas rows y0..y1 (columns x0..x1) sampled at out_w x out_h px (default 1:1)."""
        x1 = self.W if x1 is None else x1
        out_w = out_w or (x1 - x0)
        out_h = out_h or (y1 - y0)
        acc = np.zeros((out_h, out_w), np.float32)
        for (g, c), wgt in zip(self.grids, self.weights):
            gh, gw = g.shape
            k = c / self.S                     # grid cells per canvas px; grid cell i centre at (i + 0.5 - 2) cells from canvas origin
            left = x0 * k + 2.0
            right = x1 * k + 2.0
            top = y0 * k + 2.0
            bottom = y1 * k + 2.0
            im = Image.fromarray(g, "F").resize((out_w, out_h), Image.BICUBIC, box=(left, top, right, bottom))
            acc += np.asarray(im, np.float32) * np.float32(wgt)
        return np.clip(acc / self.total, 0.0, 1.0)


def gauss_blur_small(a, sigma):
    return C.blur(a, sigma)


SPLAT_Q = 0.0                 # px: stamps get sigma_eff = sqrt(sigma^2 + Q^2) (energy kept): the raster blur every canvas size shares


# ----------------------------------------------------------------------------- fast splat (bincount instead of ufunc.at)
def fast_splat(layer, xs, ys, sigma, rgb, amp=1.0, min_sigma=0.5):
    """fx.core.splat with the scatter done by np.bincount (several times faster than np.add.at): anti-aliased pixel-integrated Gaussian
    stamps, energy kept when sigma is floored to min_sigma. layer (H, W, 3) float32 in place."""
    H, W = layer.shape[:2]
    xs = np.atleast_1d(np.asarray(xs, np.float64))
    ys = np.atleast_1d(np.asarray(ys, np.float64))
    n = len(xs)
    if n == 0:
        return layer
    sig = np.broadcast_to(np.asarray(sigma, np.float64), (n,)).copy()
    energy = np.broadcast_to(np.asarray(amp, np.float64), (n,)) * 2.0 * math.pi * sig * sig
    s_eff = np.sqrt(sig * sig + SPLAT_Q * SPLAT_Q) if SPLAT_Q > 0 else np.maximum(sig, min_sigma)
    col = np.broadcast_to(np.asarray(rgb, np.float32), (n, 3))
    rad = np.ceil(3.5 * s_eff + 1.0).astype(np.int64)
    npx = H * W
    fis, wws, ccs = [], [], []
    for r in np.unique(rad):
        idx_r = np.nonzero(rad == r)[0]
        K = 2 * r + 1
        per = max(1, C.SPLAT_CHUNK // (K * K))
        for c0 in range(0, len(idx_r), per):
            ii = idx_r[c0:c0 + per]
            gx, ix0 = C._pix_gauss(xs[ii], s_eff[ii], r)
            gy, iy0 = C._pix_gauss(ys[ii], s_eff[ii], r)
            w = (gy[:, :, None] * gx[:, None, :]) * energy[ii].astype(np.float32)[:, None, None]
            px = ix0[:, None, None] + np.arange(K)[None, None, :]
            py = iy0[:, None, None] + np.arange(K)[None, :, None]
            ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
            ok = np.broadcast_to(ok, w.shape)
            fis.append((np.broadcast_to(py, w.shape) * W + np.broadcast_to(px, w.shape))[ok])
            pi = np.broadcast_to(np.arange(len(ii))[:, None, None], w.shape)[ok]
            wws.append(w[ok])
            ccs.append(col[ii][pi])
    if not fis:
        return layer
    fi = np.concatenate(fis)
    ww = np.concatenate(wws)
    cc = np.concatenate(ccs)
    acc = np.empty((3, npx), np.float32)
    for ch in range(3):
        acc[ch] = np.bincount(fi, weights=ww * cc[:, ch], minlength=npx)
    layer += acc.T.reshape(H, W, 3).astype(np.float32)
    return layer


# ----------------------------------------------------------------------------- splat lists (particles), drawn per band
class SplatList:
    def __init__(self):
        self.parts = []
        self._done = None

    def add(self, xs, ys, sig, rgb, amp):
        n = len(xs)
        if n == 0:
            return
        self.parts.append((np.asarray(xs, np.float64), np.asarray(ys, np.float64),
                           np.broadcast_to(np.asarray(sig, np.float64), (n,)).copy(),
                           np.broadcast_to(np.asarray(rgb, np.float32), (n, 3)).copy(),
                           np.broadcast_to(np.asarray(amp, np.float64), (n,)).copy()))
        self._done = None

    def cull(self, boxes):
        """Remove every stamp centred inside any (x0, y0, x1, y1) box (text box, cropped areas)."""
        self._finalize()
        xs, ys, sig, rgb, amp = self._done
        keep = np.ones(len(xs), bool)
        for (a, b, c_, d) in boxes:
            keep &= ~((xs >= a) & (xs <= c_) & (ys >= b) & (ys <= d))
        order = np.nonzero(keep)[0]
        self._done = tuple(v[order] for v in self._done)
        return self

    def _finalize(self):
        if self._done is None:
            if not self.parts:
                z = np.zeros(0)
                self._done = (z, z, z, np.zeros((0, 3), np.float32), z)
                return
            xs = np.concatenate([p[0] for p in self.parts])
            ys = np.concatenate([p[1] for p in self.parts])
            sg = np.concatenate([p[2] for p in self.parts])
            rg = np.concatenate([p[3] for p in self.parts])
            am = np.concatenate([p[4] for p in self.parts])
            o = np.argsort(ys, kind="stable")
            self._done = (xs[o], ys[o], sg[o], rg[o], am[o])

    def __len__(self):
        self._finalize()
        return len(self._done[0])

    def draw(self, layer, y0, y1, min_sigma=0.5, f=1):
        """Stamp everything that reaches canvas rows y0..y1 into layer (in place). With f > 1 the layer is the coarse grid (hc, Wc, 3) of
        those rows: positions and sigmas are divided by f (energy kept)."""
        self._finalize()
        xs, ys, sg, rg, am = self._done
        if len(xs) == 0:
            return layer
        margin = 3.5 * max(float(sg.max()), min_sigma * f) + 2.0 * f
        lo = np.searchsorted(ys, y0 - margin, "left")
        hi = np.searchsorted(ys, y1 + margin, "right")
        if hi <= lo:
            return layer
        if f == 1:
            fast_splat(layer, xs[lo:hi], ys[lo:hi] - y0, sg[lo:hi], rg[lo:hi], am[lo:hi], min_sigma=min_sigma)
        else:
            fast_splat(layer, xs[lo:hi] / f, (ys[lo:hi] - y0) / f, sg[lo:hi] / f, rg[lo:hi], am[lo:hi], min_sigma=min_sigma)
        return layer


# ----------------------------------------------------------------------------- upsampling of work-grid layers
def resize_band(a, y0, y1, W, H, f):
    """a: array on the work grid ((H/f) x (W/f), optional channel axis) covering the whole canvas; returns canvas rows y0..y1
    (h, W[, c]) via bicubic PIL resize with a source box, block centres mapped to block centres."""
    h = y1 - y0
    if f == 1:
        return a[y0:y1]
    gh, gw = a.shape[:2]
    box = (0.0, y0 / f, W / f, y1 / f)
    if a.ndim == 2:
        im = Image.fromarray(np.ascontiguousarray(a), "F").resize((W, h), Image.BICUBIC, box=box)
        return np.asarray(im, np.float32)
    out = np.empty((h, W, a.shape[2]), np.float32)
    for k in range(a.shape[2]):
        im = Image.fromarray(np.ascontiguousarray(a[..., k]), "F").resize((W, h), Image.BICUBIC, box=box)
        out[..., k] = np.asarray(im, np.float32)
    return out


# ----------------------------------------------------------------------------- sprites (hard-edged chips drawn OVER the fill)
class SpriteList:
    """Small RGBA tiles (premultiplied colour + alpha) on the GLOBAL coarse grid of the canvas (cell (I, J) centred at ((I + .5) f, (J + .5) f)
    canvas px). A sprite is a pure function of its own position, so the picture does not depend on the band height and a sprite that
    crosses a band edge is drawn, clipped, in both bands. Drawn 'over' (alpha composite), not added: a chip of the iris hides the fill under it."""

    def __init__(self):
        self.items = []            # (I0, J0, rgb (h, w, 3) premultiplied, a (h, w))
        self._sorted = False

    def add(self, I0, J0, rgb, a):
        self.items.append((int(I0), int(J0), np.asarray(rgb, np.float16), np.asarray(a, np.float16)))      # float16: 360 flakes at 4096 would hold 130 MB in float32
        self._sorted = False

    def __len__(self):
        return len(self.items)

    def cull(self, boxes, f):
        """Drop sprites whose centre lies in any canvas box (x0, y0, x1, y1)."""
        keep = []
        for it in self.items:
            I0, J0, rgb, a = it
            cx = (I0 + a.shape[1] / 2.0) * f
            cy = (J0 + a.shape[0] / 2.0) * f
            if any(x0 <= cx <= x1 and y0 <= cy <= y1 for (x0, y0, x1, y1) in boxes):
                continue
            keep.append(it)
        self.items = keep
        self._sorted = False
        return self

    def draw(self, lay, alay, y0, y1, f):
        """Composite every sprite that reaches canvas rows y0..y1 into the coarse layers lay (hc, Wc, 3) premultiplied and alay (hc, Wc)."""
        if not self.items:
            return
        if not self._sorted:
            self.items.sort(key=lambda it: (it[1], it[0]))
            self._sorted = True
        hc, Wc = lay.shape[:2]
        j_lo = y0 // f
        for (I0, J0, rgb, a) in self.items:
            h, w = a.shape
            ja, jb = max(J0, j_lo), min(J0 + h, j_lo + hc)
            ia, ib = max(I0, 0), min(I0 + w, Wc)
            if ja >= jb or ia >= ib:
                continue
            sa = a[ja - J0:jb - J0, ia - I0:ib - I0].astype(np.float32)
            sr = rgb[ja - J0:jb - J0, ia - I0:ib - I0].astype(np.float32)
            dst = lay[ja - j_lo:jb - j_lo, ia:ib]
            da = alay[ja - j_lo:jb - j_lo, ia:ib]
            dst *= (1.0 - sa)[..., None]
            dst += sr
            da *= (1.0 - sa)
            da += sa


# ----------------------------------------------------------------------------- the render loop
def render_bands(scene, look):
    """look.base(scene, cv, y0, y1) draws the fill / background, look.layers = ordered [('splat', SplatList, mode) | ('splatc', SplatList, mode) |
    ('splatb', (SplatList, sigma_R), mode) | ('sprites', SpriteList, 'over') | ('chips', ChipList, None) | ('fnc', f, mode) | ('fn', f, None)].
    Every band is computed on rows [y0 - halo, y1 + halo] (halo = look.halo_rows(scene), a multiple of the coarse factor) and cropped, so a
    blur, a resize or a coarse-grid upsample never sees the band edge (no row steps at band multiples). Per-layer wall times land in
    scene.times['layers']."""
    W, H = scene.W, scene.H
    img8 = np.empty((H, W, 3), np.uint8)
    t0 = time.perf_counter()
    lt = {}
    f = scene.f
    halo = int(getattr(look, "halo_rows", lambda sc: 4 * f + 2)(scene))
    f2 = 2 * f                                            # bands start on a multiple of 2 f: the strided evaluation of the fibre noise then has the same phase in every band
    halo = int(math.ceil(halo / float(f2))) * f2
    scene.info["halo_rows"] = halo
    scene.info["band_rows"] = scene.band_rows

    def tick(name, t):
        lt[name] = lt.get(name, 0.0) + (time.perf_counter() - t)

    for y0 in range(0, H, scene.band_rows):
        y1 = min(H, y0 + scene.band_rows)
        ya = (max(0, y0 - halo) // f2) * f2
        yb = min(H, y1 + halo)
        cv = np.zeros((yb - ya, W, 3), np.float32)
        t = time.perf_counter()
        look.base(scene, cv, ya, yb)
        tick("base", t)
        for li, (kind, obj, mode) in enumerate(look.layers):
            t = time.perf_counter()
            nm = f"{li}:{kind}" + (f":{getattr(obj, '__name__', '')}" if kind == "fn" else "")
            if kind == "chips":
                obj.draw(cv, ya, yb)
            elif kind in ("splatb", "splatc"):
                # coarse / blurred splat layer: obj = SplatList (splatc) or (SplatList, sigma in R units) (splatb)
                sl, sig_R = obj if kind == "splatb" else (obj, 0.0)
                sig = sig_R * scene.R / f
                pad = int(math.ceil(3.0 * sig)) + 1 if sig > 0 else 0
                pa, pb = max(0, ya - pad * f), min(scene.H, yb + pad * f)
                pa = (pa // f) * f
                hc, Wc = scene.grid(pa, pb, f)
                lay = np.zeros((hc, Wc, 3), np.float32)
                sl.draw(lay, pa, pb, f=f)
                if sig > 0.4:
                    lay = C.blur(lay, sig)
                lay = scene.up(lay, f, pa, pb)[ya - pa:yb - pa]
                if mode == "add":
                    cv += lay
                else:
                    C.screen(cv, lay)
            elif kind == "sprites":
                fs = scene.fs
                hc, Wc = scene.grid(ya, yb, fs)
                lay = np.zeros((hc, Wc, 3), np.float32)
                al = np.zeros((hc, Wc), np.float32)
                obj.draw(lay, al, ya, yb, fs)
                lay = scene.up(lay, fs, ya, yb)
                al = np.clip(scene.up(al, fs, ya, yb), 0.0, 1.0)
                cv *= (1.0 - al)[..., None]
                cv += lay
            elif kind == "splat":
                lay = np.zeros_like(cv)
                obj.draw(lay, ya, yb)
                if mode == "add":
                    cv += lay
                else:
                    C.screen(cv, lay)
            elif kind == "fnc":
                hc, Wc = scene.grid(ya, yb, f)
                lay = np.zeros((hc, Wc, 3), np.float32)
                obj(scene, lay, ya, yb, f)
                lay = scene.up(lay, f, ya, yb)
                if mode == "add":
                    cv += lay
                else:
                    C.screen(cv, lay)
            else:
                obj(scene, cv, ya, yb)
            tick(nm, t)
        t = time.perf_counter()
        cv = cv[y0 - ya:y1 - ya]
        C.tone_map(cv)
        img8[y0:y1] = C.dither_quantize(cv, scene.seed, tag=f"dither/{y0}")
        tick("tone+dither", t)
    scene.times["bands"] = round(time.perf_counter() - t0, 3)
    scene.times["layers"] = {k: round(v, 2) for k, v in lt.items()}
    return img8


def release_bands_memory(scene, look):
    """Everything the band loop needed and the compositor does not (flake sprites, grains, chips, plates, the extended sources of the fill) is
    dropped before the irises are composed: the peak of a 4096 px master with six eyes was in the compositor, on top of the band leftovers.
    Above 1536 px the extended sources are also dropped from the eye's cache (a 4K master is rendered once)."""
    import gc
    look.layers = []
    for name in ("flakes", "depth", "matter", "chips", "stars", "plate", "accent_plate", "_hi", "ring_win"):
        if hasattr(look, name):
            setattr(look, name, None)
    for e in scene.eyes:
        e.E = None
        if scene.S > 1536:
            src = e.src
            for k in [k for k in src._ext if isinstance(k, tuple) and k and k[0] == "pm"]:
                del src._ext[k]
    gc.collect()


def paste_irises(scene, img8):
    """Irises last. Solo: plain paste of the F3 disc. Pairs and groups: the overlap compositor (S weave / apex / single front, contact
    edges, Zone C, hairline), then the optional seam dust of D15."""
    t0 = time.perf_counter()
    eyes = scene.eyes
    info = scene.info
    lay = scene.layout
    if scene.n == 1:
        C.paste_iris_last(img8, eyes[0].disc)
        scene.comp = None
    else:
        opts = CO.Options(zone_c=scene.opts.get("zone_c", True), seam_band=scene.opts.get("seam_band", True),
                          edge_mode=scene.opts.get("edge_mode", "auto"), crumble_holes=scene.opts.get("crumble_holes", True),
                          edge_scale=scene.opts.get("edge_scale", 1.0), edge_profile=scene.opts.get("edge_profile", "h11"),
                          seam_noise=scene.opts.get("seam_noise", True))
        CO.decide_fronts(eyes, lay.contacts, eyes)
        comp = CO.Compositor(eyes, lay, opts, rand=lambda tag: scene.rand(tag))
        comp.compose()
        comp.paste(img8)
        scene.comp = comp
        info["contacts"] = comp.info["contacts"]
        if scene.opts.get("seam_dust"):
            from . import matter as MT
            seam_dust(scene, img8, comp)
    scene.times["irises"] = round(time.perf_counter() - t0, 3)


def seam_dust(scene, img8, comp):
    """D15 (default OFF): H24's grit lying on the neighbouring visible iris. Chips and grains at most 0.12 R outside the front limb on
    the BACK iris along the visible front arc, alpha <= 0.6, own-colour of the front iris. Drawn after the irises: it is the one
    documented exception to 'nothing on a visible iris pixel' and only exists behind the switch."""
    from . import matter as MT
    rnd = scene.rand("seamdust")
    eyes = scene.eyes
    for ci, c in enumerate(scene.layout.contacts):
        if c.front < 0 and c.kind != "weave":
            continue
        fronts = [c.front if c.kind != "weave" else c.a, c.b] if c.kind != "weave" else [c.a, c.b]
        pairs = [(c.front, c.b if c.front == c.a else c.a)] if c.kind != "weave" else [(c.a, c.b), (c.b, c.a)]
        for f, b in pairs:
            ef, eb = eyes[f], eyes[b]
            R = ef.R
            n = 260
            # points on the front limb inside the back disc
            ang0 = math.atan2(eb.cy - ef.cy, eb.cx - ef.cx)
            half = math.acos(min(1.0, (c.d / R) / 2.0)) if c.d < 2 * R else 0.5
            a = ang0 + (rnd.uniform(n) * 2 - 1) * half * 0.92
            u = rnd.exponential(n, 0.05) + 0.004
            u = np.minimum(u, 0.12)
            xs = ef.cx + (1.0 + u) * R * np.cos(a)
            ys = ef.cy + (1.0 + u) * R * np.sin(a)
            inb = np.hypot(xs - eb.cx, ys - eb.cy) < 0.95 * eb.R
            if c.kind == "weave":
                # only on the side where f is in front
                dx, dy = eyes[c.b].cx - eyes[c.a].cx, eyes[c.b].cy - eyes[c.a].cy
                d = math.hypot(dx, dy)
                vx, vy = dy / d, -dx / d
                t = ((xs - eyes[c.a].cx) * vx + (ys - eyes[c.a].cy) * vy) / R
                inb &= (t > 0.08) if f == c.a else (t < -0.08)
            if not inb.any():
                continue
            xs, ys, a, u = xs[inb], ys[inb], a[inb], u[inb]
            cols = MT.chip_colour(ef.src, a, rnd, (0.80, 0.95))
            sig = rnd.uniform(len(xs), 0.006, 0.02) * R / 2.0
            amp = np.minimum(rnd.uniform(len(xs), 0.4, 0.9) * (1.0 - u / 0.14), 0.6)
            x0, y0 = int(max(0, min(xs.min(), ys.min()) - 6)), 0
            y0 = int(max(0, ys.min() - 8)); y1 = int(min(scene.H, ys.max() + 8))
            x0 = int(max(0, xs.min() - 8)); x1 = int(min(scene.W, xs.max() + 8))
            lay = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
            C.splat(lay, xs - x0, ys - y0, np.maximum(sig, 0.4), cols, amp)
            reg = img8[y0:y1, x0:x1].astype(np.float32) / 255.0
            reg = 1.0 - (1.0 - reg) * (1.0 - np.clip(lay, 0, 0.6))
            img8[y0:y1, x0:x1] = np.clip(np.rint(reg * 255.0), 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------- the customer's names (the only text)
def draw_names(scene, img):
    """1.5.7: Cinzel caps, tracking +0.18 em, cap height 0.017 S (single) / 0.02 W (couple) / 0.012-0.016 S (groups), date 0.011 S
    at tracking +0.3 em and 55 percent opacity, colour #C9B8A0. Couple: ANNA & MAX or ANNA + infinity + MAX; groups: one line
    with middle dots. Draws on the PIL image and returns the text draw log (test T7)."""
    log = []
    if not scene.has_text:
        return log
    BANNED_GLYPHS = set("\u2665\u2764\u2661\u2763\u2766\u2767\U0001F493\U0001F494\U0001F495\U0001F496\U0001F497\U0001F498\U0001F499\U0001F49A\U0001F49B\U0001F49C\U0001F49D\U0001F49E\U0001F49F\U0001F5A4\U0001F90D\U0001F90E")
    d = ImageDraw.Draw(img, "RGBA")
    W, H, S = scene.W, scene.H, scene.S
    n = scene.n
    names = [s.upper() for s in scene.names]
    if n == 1:
        text = names[0] if names else ""
        base, cap = (0.88 * H if H > 1.5 * W else 0.93 * S), 0.017 * S
    elif n == 2:
        text = (" \u221e ".join(names[:2])) if len(names) >= 2 else (names[0] if names else "")
        base, cap = 0.90 * H, 0.02 * W
    else:
        text = " \u00b7 ".join(names)
        base, cap = (0.955 * S if W == H else 0.94 * H), (0.016 if n <= 4 else 0.013) * S
    col = (0xC9, 0xB8, 0xA0)
    size = max(8, int(round(cap / 0.70)))            # Cinzel cap height ~ 0.70 em
    max_w = 0.8 * W
    tr = 0.18
    f = L._font("Cinzel.ttf", size, "Bold")
    _nd = f.getmask("\uE000")
    _nd_sig = (_nd.size, bytes(_nd))

    def clean(s):
        """Drop every character the font has no glyph for (it would be drawn as a tofu box) and every banned symbol glyph (the brief bans that symbol in any form)."""
        out = []
        for ch in s:
            if ch in BANNED_GLYPHS:
                continue
            if not ch.isspace() and ch != "\u221e":
                m = f.getmask(ch)
                if (m.size, bytes(m)) == _nd_sig:
                    continue
            out.append(ch)
        return "".join(out)

    text = clean(text)

    def width(s, f, size):
        return d.textlength(s, font=f) + tr * size * (len(s) - 1)

    while text and width(text, f, size) > max_w and size > 8:
        size = int(size * 0.94)
        f = L._font("Cinzel.ttf", size, "Bold")
    y = base
    if text:
        x = W / 2.0 - width(text, f, size) / 2.0
        for i, ch in enumerate(text):
            g = ch
            if ch == "\u221e" and d.textlength(ch, font=f) < 1:      # glyph missing: fall back to the sans font for that glyph
                g = ch
            d.text((x, y), g, font=f, fill=col + (235,), anchor="ls")
            x += d.textlength(text[:i + 1], font=f) - d.textlength(text[:i], font=f) + tr * size
        log.append(("names", text))
    if scene.date:
        fs = max(7, int(round(0.011 * S / 0.70)))
        fd = L._font("Cinzel.ttf", fs, "Regular")
        s = clean(str(scene.date).upper())
        tw = d.textlength(s, font=fd) + 0.3 * fs * (len(s) - 1)
        x = W / 2.0 - tw / 2.0
        yy = y + 0.032 * S
        for i, ch in enumerate(s):
            d.text((x, yy), ch, font=fd, fill=col + (140,), anchor="ls")
            x += d.textlength(s[:i + 1], font=fd) - d.textlength(s[:i], font=fd) + 0.3 * fs
        log.append(("date", s))
    return log


# ----------------------------------------------------------------------------- drivers
def render(look, irises, size=1024, aspect=None, names=None, opts=None, times=None, want_scene=False, key=None, frozen=None):
    t_all = time.perf_counter()
    scene = Scene(look.NAME, irises, size, aspect, names, opts, key=key, frozen=frozen)
    scene.times["setup"] = round(time.perf_counter() - t_all, 3)
    t0 = time.perf_counter()
    look.prepare(scene)
    scene.times["prepare"] = round(time.perf_counter() - t0, 3)
    img8 = render_bands(scene, look)
    release_bands_memory(scene, look)
    paste_irises(scene, img8)
    img = Image.fromarray(img8)
    scene.info["text"] = draw_names(scene, img)
    scene.times["total"] = round(time.perf_counter() - t_all, 3)
    scene.info["rss_mb"] = peak_rss_mb()
    if times is not None:
        times.update(scene.times)
    return (img, scene) if want_scene else img
