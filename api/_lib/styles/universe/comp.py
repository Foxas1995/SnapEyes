# -*- coding: utf-8 -*-
"""uni_comp: the overlap compositor of the UNIVERSE family (brief 1.1, 1.3, 1.7.3). numpy only.

Irises are the only pixels this module writes and it writes them LAST, from the F3 discs (straight float colour + alpha).
  S weave (pairs, chains):     A is in front on the +v side of the lens, B on the -v side (H10 / H11). The seam is a textured crossfade of two
                               REAL iris pixels (exception E1): AD default smoothstep +-0.08 R (25-75 percent width 0.09 R; the owner's H11 measures
                               0.13 R), perturbed by t' = t + 0.05 R fbm (correlation 0.18 R) so the fibres dissolve into each other; switch
                               seam_band: True = "h11" (default: two stage +-0.08 / +-0.20 R, the owner's H11 profile) | "ad" (+-0.08 R) | "brief" (+-0.04 R) | False (hard seam).
  crumble (groups, trio):      one iris in front (luminance rule + stacking solver, or the apex rule), ragged edge. The trio's base pair is a
                               crumble too (the owner's H24 has no weave there); switch trio_base="weave" restores the brief's weave.
  contact edge (1.3.4):        inside the front iris, AD profile mult(r) = 1 - 0.96 exp(-((1 - r/R) / 0.028)^2): rim L* <= 6, half-depth width about
                               0.045 R, the owner's H10 / H11 values (switch edge_profile="brief": 1 - 0.55 smoothstep(0.965, 1)); fading out toward
                               the axis (0.02-0.14 R); Zone C on the back iris (alpha 0.45 at the limb, e-fold 0.018 R, cut 0.05 R, never in the
                               pupil dilated by 0.01 R). Switch zone_c (D8): off = nothing is drawn on the back iris.
  hairline (1.3.5):            0.008 R line at r = 1.000 R in the eye's own ring colour lifted, alpha 0.55, Zone C at half strength.
Everything is in units of R, so 4096 is the 1024 picture.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_comp.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np

from .common import C, smooth, luma
from .. import pupil as PUP

EDGE_K = 0.55                   # brief profile: multiply drops to 0.45 at the front limb
EDGE_LO = 0.965                 # brief profile: start of the inside edge, units of R
EDGE_AMP = 0.96                 # AD profile: 1 - 0.96 exp(-((1 - r) / 0.028)^2)
EDGE_SIG = 0.028
EDGE_REACH = 0.075              # the AD edge is below 0.2 percent beyond this depth: every pixel deeper than 1 - EDGE_REACH is pure
ZC_ALPHA = 0.45
ZC_TAU = 0.018
ZC_CUT = 0.05
SEAM_HALF = 0.08                # AD seam: smoothstep half-width 0.08 R (total 0.16 R)
SEAM_NOISE = 0.06               # seam perturbation amplitude (R), correlation 0.18 R
SEAM_REACH = 0.45               # the widest stage of the H11 variant (+-0.20 R) plus the noise
SEAM_MODES = {True: "h11", False: "hard", "h11": "h11", "h11full": "h11full", "ad": "ad", "brief": "brief", "hard": "hard"}   # default True = the H11 two-stage crossfade
FADE_LO, FADE_HI = 0.02, 0.14   # edge strength ramp toward the axis
HAIR_W = 0.008
HAIR_ALPHA = 0.55
CRUMBLE_EDGE = 0.25
CRUMBLE_ZC = 0.60
HOLE_COVER = 0.30
DARK_L = 26.0                   # hairline mode when the back band L* is below this
PUPIL_DIL = 0.01


class Options:
    """The sign-off switches (brief 0.7). Defaults are the brief's."""

    def __init__(self, zone_c=True, seam_band=True, edge_mode="auto", crumble_holes=True, edge_scale=1.0, edge_profile="h11", seam_noise=True):
        self.zone_c = zone_c              # D8
        self.seam_band = seam_band        # D13: True (AD 0.16 R) | "brief" (0.08 R) | "h11" | False
        self.seam_mode = SEAM_MODES[seam_band]
        self.edge_mode = edge_mode        # 'auto' | 'dark' | 'hairline'
        self.crumble_holes = crumble_holes
        self.edge_scale = edge_scale
        self.edge_profile = edge_profile  # 'h11' (AD, default) | 'brief'
        self.seam_noise = seam_noise

    def tag(self):
        return ("zc" if self.zone_c else "nozc") + "_" + self.seam_mode


def seam_w(mode, t):
    """Weight of iris A in an S-weave lens at signed axis distance t (R units): smoothstep crossfades, see the module doc."""
    if mode == "hard":
        return (t > 0).astype(np.float32)
    if mode == "brief":
        return smooth((t + 0.04) / 0.08)
    if mode == "h11":
        return 0.5 * smooth((t + 0.08) / 0.16) + 0.5 * smooth((t + 0.20) / 0.40)           # the AD's two-stage formula (25-75 percent width 0.082 R)
    if mode == "h11full":
        return 0.5 * smooth((t + 0.12) / 0.24) + 0.5 * smooth((t + 0.30) / 0.60)           # the owner's H11 as measured: 25-75 percent 0.12 R, 10-90 percent 0.30 R
    return smooth((t + SEAM_HALF) / (2 * SEAM_HALF))


def value_noise_win(seed, xs, ys, R, origin, cpr):
    """Smooth value noise 0..1, cpr lattice cells per R, hashed from lattice coordinates relative to `origin` (R units: the same picture at
    1024 and 4096); evaluated on a stride of a third of a cell and brought back bilinearly."""
    cell_px = R / cpr
    st = max(1, int(cell_px / 3.0))
    xg = xs[:, ::st]
    yg = ys[::st, :]
    u = ((xg - origin[0]) / R * cpr).astype(np.float64)
    v = ((yg - origin[1]) / R * cpr).astype(np.float64)
    i0 = np.floor(u)
    j0 = np.floor(v)
    fu, fv = u - i0, v - j0
    fu = fu * fu * (3 - 2 * fu)
    fv = fv * fv * (3 - 2 * fv)
    shp = np.broadcast(u, v).shape
    i0 = np.broadcast_to(i0, shp).astype(np.int64)
    j0 = np.broadcast_to(j0, shp).astype(np.int64)
    n = (_hash01(i0, j0, seed) * (1 - fu) * (1 - fv) + _hash01(i0 + 1, j0, seed) * fu * (1 - fv)
         + _hash01(i0, j0 + 1, seed) * (1 - fu) * fv + _hash01(i0 + 1, j0 + 1, seed) * fu * fv).astype(np.float32)
    if st > 1:
        from PIL import Image
        n = np.asarray(Image.fromarray(np.ascontiguousarray(n), "F").resize((xs.shape[1], ys.shape[0]), Image.BILINEAR), np.float32)
    return n


class Tile:
    __slots__ = ("k", "rgb", "a", "x0", "y0", "cx", "cy", "R", "T", "pup", "pmask")


def make_tile(eye, k):
    d = eye.disc
    t = Tile()
    t.k = k
    t.rgb, t.a = d.rgb, d.alpha
    t.T = d.rgb.shape[0]
    t.x0, t.y0, t.cx, t.cy, t.R = d.x0, d.y0, d.cx, d.cy, d.R
    t.pup = eye.src.pup
    t.pmask = None
    return t


def _pupil_keep(tile):
    """float32 (T, T): 0 inside the pupil dilated by 0.01 R, 1 elsewhere (Zone C never touches the pupil)."""
    if tile.pmask is None:
        m = PUP.mask(tile.pup, tile.T, tile.R, PUPIL_DIL)
        tile.pmask = (~m).astype(np.float32)
    return tile.pmask


def _grid(x0, y0, w, h):
    xs = (np.arange(x0, x0 + w, dtype=np.float32) + np.float32(0.5))[None, :]
    ys = (np.arange(y0, y0 + h, dtype=np.float32) + np.float32(0.5))[:, None]
    return xs, ys


def _alpha_on(tile, x0, y0, w, h):
    """Tile alpha on the canvas window (x0, y0, w, h) (zero outside the tile)."""
    out = np.zeros((h, w), np.float32)
    xa, ya = max(x0, tile.x0), max(y0, tile.y0)
    xb, yb = min(x0 + w, tile.x0 + tile.T), min(y0 + h, tile.y0 + tile.T)
    if xa < xb and ya < yb:
        out[ya - y0:yb - y0, xa - x0:xb - x0] = tile.a[ya - tile.y0:yb - tile.y0, xa - tile.x0:xb - tile.x0]
    return out


def _sub_on(arr, tile, x0, y0, w, h, fill=1.0):
    """A tile-sized array (T, T[, c]) read on the window (canvas coords)."""
    shp = (h, w) + arr.shape[2:]
    out = np.full(shp, fill, np.float32)
    xa, ya = max(x0, tile.x0), max(y0, tile.y0)
    xb, yb = min(x0 + w, tile.x0 + tile.T), min(y0 + h, tile.y0 + tile.T)
    if xa < xb and ya < yb:
        out[ya - y0:yb - y0, xa - x0:xb - x0] = arr[ya - tile.y0:yb - tile.y0, xa - tile.x0:xb - tile.x0]
    return out


# ----------------------------------------------------------------------------- crumble holes
def _hash01(ix, iy, seed):
    """Integer hash of a lattice point -> float in [0, 1) (splitmix style, numpy uint64)."""
    with np.errstate(over="ignore"):
        h = (ix.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)) ^ (iy.astype(np.uint64) * np.uint64(0xC2B2AE3D27D4EB4F)) ^ np.uint64(seed)
        h ^= h >> np.uint64(33)
        h *= np.uint64(0xFF51AFD7ED558CCD)
        h ^= h >> np.uint64(33)
        h *= np.uint64(0xC4CEB9FE1A85EC53)
        h ^= h >> np.uint64(33)
    return (h >> np.uint64(11)).astype(np.float64) * (1.0 / float(1 << 53))


def hole_field(seed, xs, ys, R, origin, cover=HOLE_COVER):
    """1 = edge present, 0 = hole. Holes of about 0.006-0.02 R covering `cover` of the arc. A value noise on a lattice of 90 cells per R,
    hashed from the lattice coordinates relative to `origin` (the contact's midpoint) in R units: the same picture at 1024 and 4096.
    Evaluated on a stride of a third of a lattice cell and brought back with a bilinear resize (PIL)."""
    cpr = 90.0
    h, w = ys.shape[0], xs.shape[1]
    cell_px = R / cpr
    st = max(1, int(cell_px / 2.5))
    xg = xs[:, ::st]
    yg = ys[::st, :]
    u = ((xg - origin[0]) / R * cpr).astype(np.float64)
    v = ((yg - origin[1]) / R * cpr).astype(np.float64)
    i0 = np.floor(u)
    j0 = np.floor(v)
    fu, fv = u - i0, v - j0
    fu = fu * fu * (3 - 2 * fu)
    fv = fv * fv * (3 - 2 * fv)
    shp = np.broadcast(u, v).shape
    i0 = np.broadcast_to(i0, shp).astype(np.int64)
    j0 = np.broadcast_to(j0, shp).astype(np.int64)
    n = (_hash01(i0, j0, seed) * (1 - fu) * (1 - fv) + _hash01(i0 + 1, j0, seed) * fu * (1 - fv)
         + _hash01(i0, j0 + 1, seed) * (1 - fu) * fv + _hash01(i0 + 1, j0 + 1, seed) * fu * fv).astype(np.float32)
    if st > 1:
        from PIL import Image
        n = np.asarray(Image.fromarray(np.ascontiguousarray(n), "F").resize((xs.shape[1], ys.shape[0]), Image.BILINEAR), np.float32)
    thr = 0.5 + 0.10 * (0.30 / max(cover, 0.05))            # the bilinear value noise has mean 0.5 and sd about 0.2: a threshold of 0.60 covers 30 percent
    return (1.0 - smooth((n - thr) / 0.06)).astype(np.float32)


# ----------------------------------------------------------------------------- band luminance for the rules
def _Lstar_of_Y(Y):
    Y = np.clip(Y, 0, None)
    f = np.where(Y > 0.008856, np.cbrt(Y), 7.787 * Y + 16.0 / 116.0)
    return 116.0 * f - 16.0


def _band_table(src):
    """Per-degree mean linear luminance of the source iris band 0.60-0.95 R (cached on the Src)."""
    t = getattr(src, "_band_tab", None)
    if t is None:
        m = (src.rho > 0.60) & (src.rho < 0.95)
        Y = (np.power(src.g, 2.2) @ np.array([0.2126, 0.7152, 0.0722], np.float32))
        deg = (np.degrees(src.theta) % 360.0).astype(np.int32) % 360
        sums = np.bincount(deg[m], weights=Y[m], minlength=360)
        cnt = np.bincount(deg[m], minlength=360)
        t = (sums, cnt)
        src._band_tab = t
    return t


def seam_band_L(src, direction):
    """Mean L* of the seam-side band 0.60-0.95 R within +-60 deg of the seam direction (rule 1.3.2). src.g is display 0..1."""
    sums, cnt = _band_table(src)
    c = int(round(math.degrees(direction))) % 360
    idx = (np.arange(c - 60, c + 61) % 360)
    n = cnt[idx].sum()
    if n == 0:
        return 50.0
    Y = float(sums[idx].sum() / n)
    return float(_Lstar_of_Y(np.float32(Y)))


def decide_fronts(eyes, contacts, slots, max_back=2):
    """Stacking solver (T19). Crumble contacts without a decided front: the iris whose seam-side band has the higher L* is in
    front, ties (dL* < 3): the lower-left one; then contacts are flipped, weakest margin first, until no iris is the BACK one at
    more than max_back contacts. Deterministic. Returns the list of (contact, dL) it decided."""
    todo = []
    for ci, c in enumerate(contacts):
        if c.kind != "crumble" or c.front >= 0:
            continue
        a, b = c.a, c.b
        ang_ab = math.atan2(slots[b].cy - slots[a].cy, slots[b].cx - slots[a].cx)
        La = seam_band_L(eyes[a].src, ang_ab)
        Lb = seam_band_L(eyes[b].src, ang_ab + math.pi)
        dL = La - Lb
        if abs(dL) < 3.0:
            a_ll = (slots[a].cy, -slots[a].cx)
            b_ll = (slots[b].cy, -slots[b].cx)
            c.front = a if a_ll >= b_ll else b
            margin = abs(dL)
        else:
            c.front = a if dL > 0 else b
            margin = abs(dL)
        todo.append([ci, margin])
    n = len(eyes)

    def back_counts():
        cnt = [0] * n
        for c in contacts:
            if c.front >= 0:
                cnt[c.b if c.front == c.a else c.a] += 1
        return cnt

    for _ in range(200):
        cnt = back_counts()
        bad = [k for k in range(n) if cnt[k] > max_back]
        if not bad:
            break
        k = bad[0]
        cands = [(m, ci) for ci, m in todo if (contacts[ci].a == k or contacts[ci].b == k)
                 and (contacts[ci].b if contacts[ci].front == contacts[ci].a else contacts[ci].a) == k]
        cands.sort()
        flipped = False
        for m, ci in cands:
            c = contacts[ci]
            other = c.a if c.b == k else c.b
            if cnt[other] + 1 > max_back:
                continue
            c.front = k
            flipped = True
            break
        if not flipped:
            break
    return todo


# ----------------------------------------------------------------------------- hairline colour
def hair_colour(src, ang):
    ring = src.iris.ring
    col = C.ring_at(ring, ang)
    Ls, Cc, hh = C.lch(col)
    out = C.from_lch(np.full_like(Ls, 66.0), np.minimum(Cc * 1.1, 60.0), hh)
    return (out * 255.0).astype(np.float32)


# ----------------------------------------------------------------------------- the compositor
class Compositor:
    def __init__(self, eyes, layout, opts=None, rand=None):
        self.eyes = eyes
        self.lay = layout
        self.opts = opts or Options()
        self.rand = rand
        self.tiles = [make_tile(e, i) for i, e in enumerate(eyes)]
        x0 = min(t.x0 for t in self.tiles)
        y0 = min(t.y0 for t in self.tiles)
        x1 = max(t.x0 + t.T for t in self.tiles)
        y1 = max(t.y0 + t.T for t in self.tiles)
        self.box = (x0, y0, x1, y1)
        self.info = {"contacts": []}
        self.P = None
        self.A = None
        self._seam_seed = {}
        for i, c in enumerate(layout.contacts):
            self._seam_seed[id(c)] = int(rand(f"seam/{i}").uniform() * (2 ** 31)) if rand is not None else 12345

    # -- order of merging: irises that are back at most contacts first
    def _order(self):
        n = len(self.tiles)
        score = [0.0] * n
        for c in self.lay.contacts:
            if c.kind == "crumble" and c.front >= 0:
                score[c.front] += 1.0
                score[c.b if c.front == c.a else c.a] -= 1.0
        return sorted(range(n), key=lambda k: (score[k], k))

    def _edge_mode_for(self, c, ta, tb):
        """(mode_a, mode_b, L_a, L_b): 'dark' | 'hairline' for A's front arc and B's front arc of one contact: hairline when the median L* of
        the back iris band 0.02-0.12 R outside that front limb, on the side where the arc is drawn, is below 26 (1.3.5). A crumble contact
        has one arc (the front iris's); the other entry repeats it."""
        om = self.opts.edge_mode
        if om in ("dark", "hairline"):
            return om, om, None, None
        if c.kind == "weave":
            La = self._back_band_L(ta, tb, +1.0, ta, tb)
            Lb = self._back_band_L(tb, ta, -1.0, ta, tb)
        else:
            if c.front == ta.k:
                La = Lb = self._back_band_L(ta, tb, 0.0, ta, tb)
            else:
                La = Lb = self._back_band_L(tb, ta, 0.0, ta, tb)
        ma = "hairline" if La < DARK_L else "dark"
        mb = "hairline" if Lb < DARK_L else "dark"
        return ma, mb, La, Lb

    @staticmethod
    def _back_band_L(front, back, side, ta, tb):
        """Median L* of the back iris pixels 0.02-0.12 R outside the front limb (back iris r < 0.95); for a weave only on the side (sign of t
        relative to the axis A -> B, beyond 0.14 R) where that arc is drawn."""
        x0, y0 = int(max(back.x0, front.cx - 1.2 * front.R)), int(max(back.y0, front.cy - 1.2 * front.R))
        x1, y1 = int(min(back.x0 + back.T, front.cx + 1.2 * front.R)), int(min(back.y0 + back.T, front.cy + 1.2 * front.R))
        if x1 <= x0 or y1 <= y0:
            return 50.0
        xs, ys = _grid(x0, y0, x1 - x0, y1 - y0)
        rf = np.sqrt((xs - front.cx) ** 2 + (ys - front.cy) ** 2) / np.float32(front.R)
        rb = np.sqrt((xs - back.cx) ** 2 + (ys - back.cy) ** 2) / np.float32(back.R)
        m = (rf > 1.02) & (rf < 1.12) & (rb < 0.95)
        if side != 0.0:
            dx, dy = tb.cx - ta.cx, tb.cy - ta.cy
            d = math.hypot(dx, dy)
            t = ((xs - ta.cx) * (dy / d) + (ys - ta.cy) * (-dx / d)) / np.float32(ta.R)
            m &= (t * side) > 0.14
        if not m.any():
            return 50.0
        rgb = back.rgb[y0 - back.y0:y1 - back.y0, x0 - back.x0:x1 - back.x0][m] / 255.0
        Y = float(np.median((np.power(rgb, 2.2) @ np.array([0.2126, 0.7152, 0.0722], np.float32))))
        return float(_Lstar_of_Y(np.float32(Y)))

    # -- terms of one contact on a window
    def _terms(self, c, xs, ys, ta, tb):
        R = np.float32(ta.R)
        ra = np.sqrt((xs - ta.cx) ** 2 + (ys - ta.cy) ** 2) / np.float32(ta.R)
        rb = np.sqrt((xs - tb.cx) ** 2 + (ys - tb.cy) ** 2) / np.float32(tb.R)
        dx, dy = tb.cx - ta.cx, tb.cy - ta.cy
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        vx, vy = uy, -ux
        t = ((xs - ta.cx) * vx + (ys - ta.cy) * vy) / R
        if c.kind == "weave" and self.opts.seam_noise and self.opts.seam_mode != "hard":
            # AD: the seam is a textured crossfade, not a ruler: t' = t + 0.05 R fbm (correlation 0.18 R), a two-octave value noise hashed in R units
            org = ((ta.cx + tb.cx) / 2.0, (ta.cy + tb.cy) / 2.0)
            sd = self._seam_seed.get(id(c), 12345)
            n = 0.65 * value_noise_win(sd, xs, ys, ta.R, org, 5.56) + 0.35 * value_noise_win(sd + 77, xs, ys, ta.R, org, 11.1)
            t = t + np.float32(SEAM_NOISE) * (2.0 * n - 1.0)
        return ra, rb, t, d / ta.R

    def _front_weight(self, c, k, t):
        """Weight 'iris k (a or b of contact c) is in front' at signed distance t."""
        if c.kind == "weave":
            wa = seam_w(self.opts.seam_mode, t)
            return wa if k == c.a else 1.0 - wa
        return np.ones_like(t) if k == c.front else np.zeros_like(t)

    def _edge_terms(self, ci, c, xs, ys, ra, rb, t, dnorm, ta, tb, mode):
        """Multipliers (mult_a on iris a's colour, mult_b on b's) and the hairline coverages (hair_a, hair_b)."""
        o = self.opts
        es = o.edge_scale
        if c.kind == "weave":
            ga = smooth((t - FADE_LO) / (FADE_HI - FADE_LO))
            gb = smooth((-t - FADE_LO) / (FADE_HI - FADE_LO))
            s_in, s_zc = 1.0, 1.0
        else:
            h = math.sqrt(max(1.0 - (dnorm / 2.0) ** 2, 0.0))
            taper = 1.0 - 0.70 * smooth((np.abs(t) - (h - 0.10)) / 0.10)
            hole = 1.0
            if o.crumble_holes and self.rand is not None:
                seed = int(self.rand("holes/%d" % ci).uniform() * (2 ** 31))
                hole = hole_field(seed, xs, ys, ta.R, ((ta.cx + tb.cx) / 2.0, (ta.cy + tb.cy) / 2.0))
            g = taper * hole
            ga = g if c.front == c.a else np.zeros_like(t)
            gb = g if c.front == c.b else np.zeros_like(t)
            s_in, s_zc = CRUMBLE_EDGE, CRUMBLE_ZC
        ins_b = 1.0 - smooth((rb - 0.96) / 0.04)
        ins_a = 1.0 - smooth((ra - 0.96) / 0.04)
        h11 = o.edge_profile == "h11"

        def edge_in(rk):
            """Darkening strength 0..1 of the front iris's own rim at normalised radius rk (before the arc weights)."""
            if not h11:
                return EDGE_K * smooth((rk - EDGE_LO) / (1.0004 - EDGE_LO))
            u = np.maximum(1.0004 - rk, 0.0)
            return EDGE_AMP * np.exp(-(u / EDGE_SIG) ** 2) * (1.0 - smooth((u - (EDGE_REACH - 0.02)) / 0.02))
        ua = np.maximum(ra - 1.0, 0.0)
        ub = np.maximum(rb - 1.0, 0.0)
        cutmask_a = 1.0 - smooth((ua - (ZC_CUT - 0.01)) / 0.01)
        cutmask_b = 1.0 - smooth((ub - (ZC_CUT - 0.01)) / 0.01)
        mode_a, mode_b = mode
        zsa = (1.0 if mode_a == "dark" else 0.5) * s_zc * es
        zsb = (1.0 if mode_b == "dark" else 0.5) * s_zc * es
        wx0, wy0 = int(round(float(xs[0, 0]) - 0.5)), int(round(float(ys[0, 0]) - 0.5))
        ww, wh = xs.shape[1], ys.shape[0]
        pkeep_a = _sub_on(_pupil_keep(ta), ta, wx0, wy0, ww, wh)
        pkeep_b = _sub_on(_pupil_keep(tb), tb, wx0, wy0, ww, wh)
        # Zone C: on B beside A's front limb (weight ga), on A beside B's front limb (weight gb)
        if o.zone_c:
            out_a = smooth((ra - 0.995) / 0.01)            # Zone C lives OUTSIDE the front limb: never on the pixels a front iris covers (the broad seam makes them visible)
            out_b = smooth((rb - 0.995) / 0.01)
            zc_on_b = 1.0 - np.minimum(ZC_ALPHA * zsa * np.exp(-ua / ZC_TAU) * cutmask_a * ga * out_a, 0.95) * pkeep_b
            zc_on_a = 1.0 - np.minimum(ZC_ALPHA * zsb * np.exp(-ub / ZC_TAU) * cutmask_b * gb * out_b, 0.95) * pkeep_a
        else:
            zc_on_b = zc_on_a = 1.0
        sg = max(HAIR_W * 0.5 / 2.355 * ta.R, 0.5) / ta.R          # hairline sigma in R, floored at half a pixel
        amp = min(1.0, HAIR_W * 0.5 / 2.355 / sg) * (1.0 if c.kind == "weave" else 0.8)
        if mode_a == "dark":
            in_a = 1.0 - np.minimum(edge_in(ra) * s_in * es, 0.985) * ga * ins_b
            hair_a = None
        else:
            in_a = 1.0
            hair_a = np.exp(-0.5 * ((ra - 1.0) / sg) ** 2) * ga * ins_b * amp
        if mode_b == "dark":
            in_b = 1.0 - np.minimum(edge_in(rb) * s_in * es, 0.985) * gb * ins_a
            hair_b = None
        else:
            in_b = 1.0
            hair_b = np.exp(-0.5 * ((rb - 1.0) / sg) ** 2) * gb * ins_a * amp
        return in_a * zc_on_a, in_b * zc_on_b, hair_a, hair_b

    def _lens_win(self, c):
        """Canvas window (x0, y0, x1, y1) round the lens of contact c (+ the Zone C and seam reach), clipped to the compositor box."""
        ta, tb = self.tiles[c.a], self.tiles[c.b]
        R = min(ta.R, tb.R)
        dx, dy = tb.cx - ta.cx, tb.cy - ta.cy
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        hw = max((ta.R + tb.R - d) / 2.0, 0.0)
        hh = math.sqrt(max(R * R - (d / 2.0) ** 2, 0.0))
        ex = abs(ux) * hw + abs(uy) * hh
        ey = abs(uy) * hw + abs(ux) * hh
        pad = 0.22 * R + 3
        mx, my = (ta.cx + tb.cx) / 2.0, (ta.cy + tb.cy) / 2.0
        bx0, by0, bx1, by1 = self.box
        return (max(int(math.floor(mx - ex - pad)), bx0), max(int(math.floor(my - ey - pad)), by0),
                min(int(math.ceil(mx + ex + pad)) + 1, bx1), min(int(math.ceil(my + ey + pad)) + 1, by1))

    def _edge_pass(self, modes):
        """Per-iris multiplier tiles M_k (product over the contacts of k of that contact's multiplier for k) and the hairline coverages. Each
        multiplier acts on its own iris only and is computed once per contact on the window round its lens (everything else stays 1)."""
        contacts = self.lay.contacts
        self.mult = [np.ones((t.T, t.T), np.float32) for t in self.tiles]
        self.hair_items = []
        self._wins = {}
        for ci, c in enumerate(contacts):
            ta, tb = self.tiles[c.a], self.tiles[c.b]
            win = self._lens_win(c)
            self._wins[ci] = win
            x0, y0, x1, y1 = win
            if x1 <= x0 or y1 <= y0:
                continue
            xs, ys = _grid(x0, y0, x1 - x0, y1 - y0)
            ra, rb, t, dn = self._terms(c, xs, ys, ta, tb)
            ma, mb, ha, hb = self._edge_terms(ci, c, xs, ys, ra, rb, t, dn, ta, tb, modes[ci])
            for side, tile, m, hcov in ((c.a, ta, ma, ha), (c.b, tb, mb, hb)):
                m = np.broadcast_to(np.asarray(m, np.float32), (y1 - y0, x1 - x0))
                xa, ya = max(x0, tile.x0), max(y0, tile.y0)
                xb, yb = min(x1, tile.x0 + tile.T), min(y1, tile.y0 + tile.T)
                if xa < xb and ya < yb:
                    self.mult[side][ya - tile.y0:yb - tile.y0, xa - tile.x0:xb - tile.x0] *= m[ya - y0:yb - y0, xa - x0:xb - x0]
                if hcov is not None:
                    self.hair_items.append((side, win, np.broadcast_to(np.asarray(hcov, np.float32), (y1 - y0, x1 - x0))))

    def compose(self):
        x0, y0, x1, y1 = self.box
        h, w = y1 - y0, x1 - x0
        self.P = np.zeros((h, w, 3), np.float32)
        self.A = np.zeros((h, w), np.float32)
        contacts = self.lay.contacts
        by_pair = {}
        for ci, c in enumerate(contacts):
            by_pair.setdefault((c.a, c.b), (ci, c))
            by_pair.setdefault((c.b, c.a), (ci, c))
        modes = {}
        for ci, c in enumerate(contacts):
            ma, mb, La, Lb = self._edge_mode_for(c, self.tiles[c.a], self.tiles[c.b])
            modes[ci] = (ma, mb)
            em = ma if ma == mb else f"{ma}/{mb}"
            self.info["contacts"].append({"a": c.a, "b": c.b, "kind": c.kind, "front": c.front, "edge_mode": em,
                                          "back_L": None if La is None else (round(float(La), 1), round(float(Lb), 1))})
        self._edge_pass(modes)
        done = []
        for j in self._order():
            tj = self.tiles[j]
            sl = (slice(tj.y0 - y0, tj.y0 - y0 + tj.T), slice(tj.x0 - x0, tj.x0 - x0 + tj.T))
            Xp = self.P[sl]
            AX = self.A[sl]
            Bp = (tj.rgb * self.mult[j][..., None]) * tj.a[..., None]
            aB = tj.a
            partners = [(k, by_pair[(k, j)]) for k in done if (k, j) in by_pair]
            if partners:
                wnum = np.zeros(aB.shape, np.float32)
                wden = np.zeros(aB.shape, np.float32)
                for (k, (ci, c)) in partners:
                    tk = self.tiles[k]
                    ta, tb = self.tiles[c.a], self.tiles[c.b]
                    wx0, wy0, wx1, wy1 = self._wins[ci]
                    wx0, wy0 = max(wx0, tj.x0), max(wy0, tj.y0)
                    wx1, wy1 = min(wx1, tj.x0 + tj.T), min(wy1, tj.y0 + tj.T)
                    if wx1 <= wx0 or wy1 <= wy0:
                        continue
                    xs, ys = _grid(wx0, wy0, wx1 - wx0, wy1 - wy0)
                    ra, rb, t, dn = self._terms(c, xs, ys, ta, tb)
                    ak = _alpha_on(tk, wx0, wy0, wx1 - wx0, wy1 - wy0)
                    sub = (slice(wy0 - tj.y0, wy1 - tj.y0), slice(wx0 - tj.x0, wx1 - tj.x0))
                    m = ak * aB[sub]
                    wnum[sub] += m * self._front_weight(c, k, t)
                    wden[sub] += m
                wt = np.where(wden > 1e-6, wnum / np.maximum(wden, 1e-6), 1.0).astype(np.float32)
                wx = 1.0 - (1.0 - wt) * aB
                wb = 1.0 - wt * AX
                out = Xp * wx[..., None] + Bp * wb[..., None]
                aout = AX + aB - AX * aB
                self.P[sl] = out
                self.A[sl] = aout
            else:
                self.P[sl] = Xp + Bp * (1.0 - AX)[..., None]
                self.A[sl] = AX + aB - AX * aB
            done.append(j)
        self._hairlines()
        return self.P, self.A

    def _hairlines(self):
        """Dark eyes: the coloured hairline on the front arcs over the composite, only where that iris is the top one there."""
        bx0, by0, bx1, by1 = self.box
        for side, win, cov in self.hair_items:
            x0, y0, x1, y1 = win
            tl = self.tiles[side]
            xs, ys = _grid(x0, y0, x1 - x0, y1 - y0)
            vis = np.ones((y1 - y0, x1 - x0), np.float32)
            for c2 in self.lay.contacts:
                if side not in (c2.a, c2.b):
                    continue
                p = c2.b if side == c2.a else c2.a
                ta2, tb2 = self.tiles[c2.a], self.tiles[c2.b]
                ra, rb, t, dn = self._terms(c2, xs, ys, ta2, tb2)
                w_self = self._front_weight(c2, side, t)
                vis *= 1.0 - _alpha_on(self.tiles[p], x0, y0, x1 - x0, y1 - y0) * (1.0 - w_self)
            ang = np.arctan2(ys - tl.cy, xs - tl.cx)
            col = hair_colour(self.eyes[side].src, ang)
            sl = (slice(y0 - by0, y1 - by0), slice(x0 - bx0, x1 - bx0))
            Aout = self.A[sl]
            a = (HAIR_ALPHA * cov * vis * Aout)[..., None].astype(np.float32)
            self.P[sl] = self.P[sl] * (1.0 - a) + a * col * Aout[..., None]

    def paste(self, img8):
        H, W = img8.shape[:2]
        x0, y0, x1, y1 = self.box
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        step = max(16, (1 << 21) // max(xb - xa, 1))
        for r0 in range(ya, yb, step):
            r1 = min(yb, r0 + step)
            reg = img8[r0:r1, xa:xb].astype(np.float32)
            a = self.A[r0 - y0:r1 - y0, xa - x0:xb - x0]
            reg *= (1.0 - a)[..., None]
            reg += self.P[r0 - y0:r1 - y0, xa - x0:xb - x0]
            np.rint(reg, out=reg)
            np.clip(reg, 0, 255, out=reg)
            img8[r0:r1, xa:xb] = reg.astype(np.uint8)
        return img8


# ----------------------------------------------------------------------------- masks (test T1)
def front_weights(comp, k):
    """Per contact of iris k: (contact, partner tile, weight 'k is in front' (T, T) on k's tile window, partner radius map, t map). The weights come from
    the compositor's own terms (seam noise included), so the test measures exactly what was drawn."""
    tk = comp.tiles[k]
    xs, ys = _grid(tk.x0, tk.y0, tk.T, tk.T)
    out = []
    for c in comp.lay.contacts:
        if k not in (c.a, c.b):
            continue
        p = c.b if k == c.a else c.a
        tp = comp.tiles[p]
        ta, tb = comp.tiles[c.a], comp.tiles[c.b]
        ra, rb, t, dn = comp._terms(c, xs, ys, ta, tb)
        rp = rb if k == c.a else ra
        w = np.broadcast_to(comp._front_weight(c, k, t), rp.shape).astype(np.float32)
        out.append((c, tp, w, rp, t))
    return out


def pure_masks(comp, W, H):
    """M_k: boolean tile masks of the zone A pixels (r <= 0.95 R_k) that must equal the F3 disc's own colour: the iris itself, where no contact
    edge (the multiplier tile is 1), no Zone C strip and no seam blend touches it, and where it is not hidden by a partner. Pixels of the FRONT
    iris away from its contact arcs are pure everywhere; the mask of the back iris excludes what the front iris covers and its Zone C strip."""
    out = []
    for k, tk in enumerate(comp.tiles):
        xs, ys = _grid(tk.x0, tk.y0, tk.T, tk.T)
        rk = np.sqrt((xs - tk.cx) ** 2 + (ys - tk.cy) ** 2) / np.float32(tk.R)
        m = (rk <= 0.95) & (tk.a >= 0.999) & (comp.mult[k] >= 0.9995)
        strip = 1.0 + ZC_CUT + 0.01
        for (c, tp, w, rp, t) in front_weights(comp, k):
            in_reach = rp <= strip
            m &= ~(in_reach & (w < 1.0 - 1e-3))
        out.append(m)
    return out


def edge_zone_ok(comp):
    """Structure of everything that is NOT pure (mult < 1 inside zone A): it must be the front iris's own rim zone (r > 1 - EDGE_REACH) or the back
    iris's Zone C strip (<= 0.055 R outside a front limb). Returns the count of pixels that violate it."""
    bad = 0
    for k, tk in enumerate(comp.tiles):
        xs, ys = _grid(tk.x0, tk.y0, tk.T, tk.T)
        rk = np.sqrt((xs - tk.cx) ** 2 + (ys - tk.cy) ** 2) / np.float32(tk.R)
        touched = (rk <= 0.95) & (comp.mult[k] < 0.9995)
        ok = rk > 1.0 - EDGE_REACH
        for (c, tp, w, rp, t) in front_weights(comp, k):
            # Zone C strip on iris k beside the PARTNER's front limb: partner radius within 1.0 .. 1.06
            ok |= (rp > 0.995) & (rp < 1.0 + ZC_CUT + 0.01)
            # pixels the partner hides completely are not part of the picture
            ok |= (rp <= 1.0) & (w <= 1e-3)
        bad += int((touched & ~ok).sum())
    return bad


def blend_share(comp):
    """E1 per iris: share of the disc (r <= 1) that is a mix of two irises (0.001 < w < 0.999 on a pixel covered by both)."""
    res = []
    for k, tk in enumerate(comp.tiles):
        xs, ys = _grid(tk.x0, tk.y0, tk.T, tk.T)
        rk = np.sqrt((xs - tk.cx) ** 2 + (ys - tk.cy) ** 2) / np.float32(tk.R)
        area = float((rk <= 1.0).sum())
        mix = np.zeros(rk.shape, bool)
        for (c, tp, w, rp, t) in front_weights(comp, k):
            if c.kind == "weave":
                mix |= (rk <= 1.0) & (rp <= 1.0) & (w > 1e-3) & (w < 1.0 - 1e-3)
        res.append(float(mix.sum()) / area)
    return res
