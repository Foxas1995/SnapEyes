# -*- coding: utf-8 -*-
"""uni_matter: particles of the UNIVERSE family (brief 3.0, 3.5.1, 1.7.4-1.7.6). numpy + PIL only.

  fibre_flakes   quadratic-Bezier slivers cut from the SAME iris band 0.70-0.95 R (the owner's Echo flakes)
  star_field     1-2 px stars in the eye's own lifted palette
  outline_grains dust / grains round an iris outline (density 0.85 exp(-e/L1) + 0.15 exp(-e/L2))
  notch plumes   grains and iris-chips leaving a notch along the wedge bisector, colours by origin arc with the partner share
  ChipList       iris-chips: photographed chip silhouettes (P-SN-FLAKE atlas) filled with the eye's own colours, lit from the upper left
Every size is in R (iris radius) or S (short side): a 4096 render is the 1024 picture. Matter is drawn BEFORE the irises
and therefore never shows on a visible iris pixel (T6); the optional seam dust of D15 is a separate post layer.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_matter.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports, the chip atlas read through atlas.py); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np
from PIL import Image

from .. import atlas as AT
from .common import C, smooth, luma, ramp_rgb
from .engine import SplatList
from .grains import GrainList
from .flakes import fibre_flakes  # noqa: F401  (the flakes are sprites now, see flakes.py)

COPPER = np.array([C.rgb01(h) for h in ("#3B1C0C", "#8A4A1F", "#C98545", "#F0C48C")], np.float32)
SILVER = np.array([C.rgb01(h) for h in ("#2A2E33", "#6E7680", "#B8C0C8", "#EEF2F5")], np.float32)


_A8 = C.BoundedCache(1)


def atlas():
    """The chip atlas as the prototype's loader returned it: the uint8 planes lum and mask (n, 128, 128) and n. The file is the foundation's
    (api/_lib/styles/atlas.py: one copy, read once, checked against the registry's sha256); its float planes are v / 255, and v / 255 * 255 rounds back
    to the very byte (test_goldens_universe.py compares the planes with the file's own)."""
    got = _A8.get("atlas")
    if got is None:
        A = AT.chips()
        got = _A8.put("atlas", {"lum": np.rint(A.lum * np.float32(255.0)).astype(np.uint8), "mask": np.rint(A.mask * np.float32(255.0)).astype(np.uint8), "n": int(A.n)})
    return got


# ----------------------------------------------------------------------------- colours
def _ramp4(pal, t):
    t = np.clip(np.asarray(t, np.float32), 0, 1) * 3.0
    i = np.minimum(t.astype(np.int32), 2)
    f = (t - i)[..., None]
    return pal[i] * (1 - f) + pal[i + 1] * f


def chip_colour(src, phi, rnd, Lrange=(0.78, 0.94), chroma_k=0.85, cap=34.0):
    """Chip palette (1.5.2): the eye's ring colour at angle phi (screen radians) lifted to L 0.75-0.95, chroma x 0.85 (cap), dark_brown
    copper-to-cream and grey silver fallbacks (v2 table). Returns (n, 3) float 0..1."""
    phi = np.atleast_1d(phi)
    n = len(phi)
    col = C.ring_at(src.iris.ring, phi)
    Ls, Cc, hh = C.lch(col)
    L_out = 100.0 * rnd.uniform(n, *Lrange)
    C_out = np.minimum(Cc * chroma_k * 1.6, cap)
    out = C.from_lch(L_out, C_out, hh).astype(np.float32)
    cls = src.cls
    if cls == "dark_brown":
        t = rnd.uniform(n, 0.55, 1.0)
        out = _ramp4(COPPER, t).astype(np.float32) * 1.0
        out = np.minimum(out * 1.05, 1.0)
    elif cls == "grey":
        t = rnd.uniform(n, 0.55, 1.0)
        base = _ramp4(SILVER, t).astype(np.float32)
        out = np.minimum(base * 0.55 + out * 0.45, 1.0)
    return out


def haze_colour(src, phi, rnd):
    phi = np.atleast_1d(phi)
    n = len(phi)
    col = C.ring_at(src.iris.ring, phi)
    Ls, Cc, hh = C.lch(col)
    return C.from_lch(100.0 * rnd.uniform(n, 0.45, 0.65), np.minimum(Cc * 1.2, 40.0), hh).astype(np.float32)


def star_field(scene, density, tag="stars", sig_range=(0.0008, 0.0015), bright=(0.10, 0.95), sat=0.3, lift_t=0.92):
    rnd = scene.rand(tag)
    n = C.particle_count(density, scene.W, scene.H)
    xs = rnd.uniform(n) * scene.W
    ys = rnd.uniform(n) * scene.H
    b = bright[0] + (bright[1] - bright[0]) * rnd.uniform(n) ** 4.0
    sig = rnd.uniform(n, *sig_range) * scene.S
    e0 = scene.eyes[0]
    col = ramp_rgb(e0.src, np.full(n, lift_t, np.float32) + rnd.uniform(n, -0.06, 0.03).astype(np.float32), Lmax=96.0, gain=sat)
    sl = SplatList()
    sl.add(xs, ys, sig, col, b)
    return sl


# ----------------------------------------------------------------------------- iris chips
class ChipList:
    """Chip silhouettes from the atlas, filled with the eye's own colours, lit from the upper left. Items are added in canvas px
    and drawn (screen-added) into any band. A chip of 8 px or more also carries a patch of the eye's own fibre texture (band 0.82 R at the
    emission angle), so a larger chip shows real fibres (1.7.6)."""

    def __init__(self):
        self.items = []          # (x, y, size_px, angle_deg, rgb(3), sprite, alpha, blur_px, (src, sx, sy, scale) | None)
        self._cache = {}

    def add(self, xs, ys, size, ang, rgb, sprite, alpha, blur=0.0, srcs=None, phi=None, Rpx=None):
        n = len(xs)
        size = np.broadcast_to(np.asarray(size, np.float64), (n,))
        ang = np.broadcast_to(np.asarray(ang, np.float64), (n,))
        alpha = np.broadcast_to(np.asarray(alpha, np.float64), (n,))
        blur = np.broadcast_to(np.asarray(blur, np.float64), (n,))
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), (n, 3))
        for i in range(n):
            tex = None
            if srcs is not None:
                sr = srcs[i] if isinstance(srcs, (list, tuple)) else srcs
                ph = float(phi[i])
                tex = (sr, sr.R + 0.82 * sr.R * math.cos(ph), sr.R + 0.82 * sr.R * math.sin(ph), sr.R / float(Rpx))
            self.items.append((float(xs[i]), float(ys[i]), float(size[i]), float(ang[i]), rgb[i], int(sprite[i]), float(alpha[i]), float(blur[i]), tex))

    def cull(self, boxes):
        keep = []
        for it in self.items:
            ok = True
            for (a, b, c_, d) in boxes:
                if a <= it[0] <= c_ and b <= it[1] <= d:
                    ok = False
                    break
            if ok:
                keep.append(it)
        self.items = keep
        return self

    def __len__(self):
        return len(self.items)

    def _raster(self, sprite, n, ang, blur):
        key = (sprite, n, int(round(ang)) % 360, int(round(blur * 4)))
        r = self._cache.get(key)
        if r is None:
            A = atlas()
            m = Image.fromarray(A["mask"][sprite]).rotate(ang, resample=Image.BILINEAR)
            l = Image.fromarray(A["lum"][sprite]).rotate(ang, resample=Image.BILINEAR)
            m = m.resize((n, n), Image.LANCZOS if n < 128 else Image.BICUBIC)
            l = l.resize((n, n), Image.LANCZOS if n < 128 else Image.BICUBIC)
            mf = np.asarray(m, np.float32) / 255.0
            lf = np.asarray(l, np.float32) / 255.0
            if blur > 0.3:
                mf = C.blur(mf, blur)
                lf = C.blur(lf, blur)
            w = mf > 0.5
            l0 = float(lf[w].mean()) if w.any() else 0.7
            r = (mf, lf, l0)
            self._cache[key] = r
        return r

    @staticmethod
    def _patch(tex, n, ang):
        """Luminance texture factor (n, n) 0..~1.6 from the eye's own pixels round (sx, sy): the patch's luminance over its mean."""
        sr, sx, sy, sc = tex
        ax = (np.arange(n, dtype=np.float32) + 0.5 - n / 2.0) * np.float32(sc)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        X = sx + ax[None, :] * ca - ax[:, None] * sa
        Y = sy + ax[None, :] * sa + ax[:, None] * ca
        X = np.clip(X, 0, sr.tgt - 1.001)
        Y = np.clip(Y, 0, sr.tgt - 1.001)
        x0 = np.floor(X).astype(np.int32)
        y0 = np.floor(Y).astype(np.int32)
        fx, fy = (X - x0), (Y - y0)
        Yg = sr.Y
        v = Yg[y0, x0] * (1 - fx) * (1 - fy) + Yg[y0, x0 + 1] * fx * (1 - fy) + Yg[y0 + 1, x0] * (1 - fx) * fy + Yg[y0 + 1, x0 + 1] * fx * fy
        return np.clip(0.80 + 1.5 * (v / max(float(v.mean()), 1e-3) - 1.0), 0.45, 1.5).astype(np.float32)

    def draw(self, cv, y0, y1):
        h, W = cv.shape[:2]
        for (x, y, size, ang, rgb, sprite, alpha, blur, tex) in self.items:
            n = max(3, int(round(size)))
            half = n / 2.0 + 2 * blur
            if y + half < y0 or y - half > y1 or x + half < 0 or x - half > W:
                continue
            mf, lf, l0 = self._raster(sprite, n, ang, blur)
            ix, iy = int(round(x - n / 2.0)), int(round(y - n / 2.0))
            xa, ya = max(0, ix), max(y0, iy)
            xb, yb = min(W, ix + n), min(y1, iy + n)
            if xa >= xb or ya >= yb:
                continue
            m = mf[ya - iy:yb - iy, xa - ix:xb - ix]
            l = lf[ya - iy:yb - iy, xa - ix:xb - ix]
            shade = np.clip(0.60 + 1.7 * (l - l0), 0.16, 1.22)            # the photographed light on the chip, normalised about its own mean
            if tex is not None and n >= 8:
                shade = shade * self._patch(tex, n, ang)[ya - iy:yb - iy, xa - ix:xb - ix]
            cv[ya - y0:yb - y0, xa:xb] += (rgb[None, None, :] * shade[..., None]) * (m * alpha)[..., None]
        return cv


# ----------------------------------------------------------------------------- notches
class Notch:
    __slots__ = ("x", "y", "bx", "by", "i", "j", "weight", "kind", "side")


def circle_points(ci, ri, cj, rj):
    dx, dy = cj[0] - ci[0], cj[1] - ci[1]
    d = math.hypot(dx, dy)
    if d >= ri + rj or d <= abs(ri - rj) or d == 0:
        return None
    a = (ri * ri - rj * rj + d * d) / (2 * d)
    h = math.sqrt(max(ri * ri - a * a, 0.0))
    ux, uy = dx / d, dy / d
    vx, vy = uy, -ux
    mx, my = ci[0] + a * ux, ci[1] + a * uy
    return (mx + h * vx, my + h * vy), (mx - h * vx, my - h * vy)


def notch_list(eyes, contacts):
    """Outer notches (free ones weight 1.0, pocket ones 0.5, covered ones dropped) of every contact, with the wedge bisector
    (unit, pointing away from the union)."""
    cs = [(e.cx, e.cy) for e in eyes]
    Rs = [e.R for e in eyes]
    out = []
    for c in contacts:
        pts = circle_points(cs[c.a], Rs[c.a], cs[c.b], Rs[c.b])
        if pts is None:
            continue
        for sgn, p in zip((+1, -1), pts):
            covered = False
            for k in range(len(eyes)):
                if k in (c.a, c.b):
                    continue
                if math.hypot(p[0] - cs[k][0], p[1] - cs[k][1]) < 0.985 * Rs[k]:
                    covered = True
            if covered:
                continue
            nx = (p[0] - cs[c.a][0]) / Rs[c.a] + (p[0] - cs[c.b][0]) / Rs[c.b]
            ny = (p[1] - cs[c.a][1]) / Rs[c.a] + (p[1] - cs[c.b][1]) / Rs[c.b]
            nn = math.hypot(nx, ny) or 1.0
            bx, by = nx / nn, ny / nn
            w = 1.0
            for k in range(len(eyes)):
                if k in (c.a, c.b):
                    continue
                for step in (0.3, 0.6):
                    q = (p[0] + bx * step * Rs[c.a], p[1] + by * step * Rs[c.a])
                    if math.hypot(q[0] - cs[k][0], q[1] - cs[k][1]) < Rs[k]:
                        w = 0.5
            n = Notch()
            n.x, n.y, n.bx, n.by, n.i, n.j, n.weight, n.kind, n.side = p[0], p[1], bx, by, c.a, c.b, w, "outer", sgn
            out.append(n)
    return out


def _weibull(rnd, n, k=1.4, lam=0.55):
    u = rnd.uniform(n)
    return lam * (-np.log1p(-u * 0.9999)) ** (1.0 / k)


def edge_fade(xs, ys, W, H, S, width=0.04):
    d = np.minimum(np.minimum(xs, W - xs), np.minimum(ys, H - ys)) / (width * S)
    return smooth(d)


GRAIN_MED = 0.0050           # AD D5: grain DIAMETER median 1.0 % R (p90 1.6 %) -> radius median 0.5 % R, lognormal sigma 0.37
GRAIN_SIGMA = 0.37
DUST_R = (0.0012, 0.0040)    # dust radius (share of R): sub-pixel at 1024, small polygons at 4096
CHUNK_D = (0.016, 0.030)     # chunk DIAMETER share of R, capped at 3.0 % (AD D5)
CHUNK_CAP = 0.030


def grain_radii(rnd, n, R, is_dust):
    """Radius in px: dust U(0.12-0.40 % R), grains lognormal median 0.5 % R (sigma 0.37), clipped to 0.25-1.3 % R."""
    g = GRAIN_MED * np.exp(GRAIN_SIGMA * rnd.normal(n))
    g = np.clip(g, 0.0025, 0.013)
    d = rnd.uniform(n, *DUST_R)
    return np.where(is_dust, d, g) * R


def chunk_size(rnd, n, R, e):
    """Chip diameter in px: 1.6-3.0 % R growing a little outward, capped at 3.0 % R."""
    d = rnd.uniform(n, *CHUNK_D) * (1.0 + 0.5 * np.minimum(e, 1.0))
    return np.minimum(d, CHUNK_CAP) * R


def emit_notch(scene, nt, n_grain, n_chunk, phi_c_deg, r_d, r_m, splats, chips, tag, grain_amp=0.9,
               lightness=(0.80, 0.95), tail=0.01, limb_thin=True):
    """One notch plume: grains (dust x3) and iris-chips leave along the wedge bisector, distance Weibull (dense reach r_d, max r_m,
    e in R from the notch), colours by origin arc with the partner share p(s) = 0.05 + 0.35 exp(-(s / 0.25 R)^2). `splats` is a GrainList.
    Grain sizes follow the AD's H11 numbers (median diameter 1.0 % R), chunks are capped at 3.0 % R. Returns the number of particles."""
    rnd = scene.rand(f"plume/{tag}")
    ei, ej = scene.eyes[nt.i], scene.eyes[nt.j]
    R = 0.5 * (ei.R + ej.R)
    bis = math.atan2(nt.by, nt.bx)
    phi_c = math.radians(phi_c_deg)

    def points(n):
        side = rnd.uniform(n) < 0.5                     # True: emitted from iris i's arc, False: from j's
        a = rnd.uniform(n) * 0.35 * R
        a = np.where(rnd.uniform(n) < 0.5, a, a * 0.4)
        ox = np.empty(n)
        oy = np.empty(n)
        for which in (True, False):
            e = ei if which else ej
            o = ej if which else ei
            m = side == which
            if not m.any():
                continue
            ang0 = math.atan2(nt.y - e.cy, nt.x - e.cx)
            cand = []
            for sg in (+1, -1):
                ang = ang0 + sg * a[m] / e.R
                px = e.cx + e.R * np.cos(ang)
                py = e.cy + e.R * np.sin(ang)
                dist = np.hypot(px - o.cx, py - o.cy)
                cand.append((px, py, dist))
            use0 = cand[0][2] > cand[1][2]
            ox[m] = np.where(use0, cand[0][0], cand[1][0])
            oy[m] = np.where(use0, cand[0][1], cand[1][1])
        th = bis + np.clip(rnd.normal(n, 0.0, phi_c / 2.2), -phi_c, phi_c)
        ee = r_d * _weibull(rnd, n)
        tl = rnd.uniform(n) < tail
        ee = np.where(tl, r_d + rnd.uniform(n) * (1.0 - r_d), ee)
        ee = np.minimum(ee, r_m if not tail else 1.0)
        px = ox + np.cos(th) * ee * R
        py = oy + np.sin(th) * ee * R
        s_lat = a / R
        p_share = 0.05 + 0.35 * np.exp(-(s_lat / 0.25) ** 2)
        swap = rnd.uniform(n) < p_share
        origin = np.where(side, nt.i, nt.j)
        origin = np.where(swap, np.where(side, nt.j, nt.i), origin)
        phi_col = np.where(side, math.atan2(nt.y - ei.cy, nt.x - ei.cx), math.atan2(nt.y - ej.cy, nt.x - ej.cx))
        return px, py, ee, origin, phi_col

    n_g = int(round(n_grain * nt.weight))
    if n_g > 0:
        n_dust = n_g * 3
        n_all = n_g + n_dust
        px, py, ee, origin, phi_col = points(n_all)
        cols = np.zeros((n_all, 3), np.float32)
        for k in (nt.i, nt.j):
            m = origin == k
            if m.any():
                cols[m] = chip_colour(scene.eyes[k].src, phi_col[m], rnd, lightness)
        is_dust = np.arange(n_all) >= n_g
        rad = grain_radii(rnd, n_all, R, is_dust)
        amp = np.where(is_dust, rnd.uniform(n_all, 0.35, 0.8), rnd.uniform(n_all, 0.7, 1.0)) * grain_amp
        fade = edge_fade(px, py, scene.W, scene.H, scene.S)
        amp = amp * fade * np.exp(-0.25 * ee)
        splats.add_grains(rnd, px, py, rad, cols, amp)
    n_c = int(round(n_chunk * nt.weight))
    if n_c > 0 and chips is not None:
        px, py, ee, origin, phi_col = points(n_c)
        cols = np.zeros((n_c, 3), np.float32)
        for k in (nt.i, nt.j):
            m = origin == k
            if m.any():
                cols[m] = chip_colour(scene.eyes[k].src, phi_col[m], rnd, lightness)
        size = chunk_size(rnd, n_c, R, ee)
        fade = edge_fade(px, py, scene.W, scene.H, scene.S)
        chips.add(px, py, size, rnd.uniform(n_c) * 360.0, cols, rnd.integers(n_c, 0, atlas()["n"]), 0.95 * fade,
                  srcs=[scene.eyes[int(o)].src for o in origin], phi=phi_col, Rpx=R)
    return n_g * 4 + n_c


def union_exposed(scene, ei, angs, margin=0.0):
    """Boolean: the limb point of iris ei at screen angle angs is NOT inside another iris."""
    e = scene.eyes[ei]
    px = e.cx + e.R * np.cos(angs)
    py = e.cy + e.R * np.sin(angs)
    ok = np.ones(len(angs), bool)
    for k, o in enumerate(scene.eyes):
        if k == ei:
            continue
        ok &= np.hypot(px - o.cx, py - o.cy) > o.R * (1.0 + margin)
    return ok


DRAW_CAP = 32768


def outline_grains(scene, ei, lam, L1=0.18, L2=0.42, wind=None, b=0.25, tag="outline", dust_k=3, reach=0.95, amp_k=1.0,
                   lightness=(0.72, 0.92), limb_keep=0.75):
    """Grains (and dust x3) round the exposed outline of iris ei: lam grains per R of exposed outline, radial profile
    85 % exp(-e/L1) + 15 % exp(-e/L2), hard cut at reach, wind modulation 1 + b cos(theta - theta_w), a low-frequency angular noise
    of +-25 percent so the reach varies round the outline; AD D5: 25 percent of the DUST inside 0.15 R of the limb is thinned (no crust hugging
    the rim). Every random array is drawn at a fixed length and cut to the count. Returns a GrainList."""
    rnd = scene.rand(f"{tag}/{ei}")
    e = scene.eyes[ei]
    R = e.R
    nt = 4096
    angs = (np.arange(nt) + 0.5) * (2 * math.pi / nt)
    expo = union_exposed(scene, ei, angs)
    L_exp = float(expo.mean()) * 2 * math.pi
    n = int(round(lam * L_exp))
    gl = GrainList()
    if n <= 0:
        return gl
    n_all = min(n * (1 + dust_k), DRAW_CAP)
    k1 = rnd.uniform((3,)) * 2 * math.pi
    lobes = 1.0 + 0.25 * np.sin(3 * angs + k1[0]) + 0.15 * np.sin(5 * angs + k1[1])
    dens = expo.astype(np.float64) * lobes
    if wind is not None:
        dens = dens * (1.0 + b * np.cos(angs - wind))
    cdf = np.cumsum(dens)
    cdf /= cdf[-1]
    F = DRAW_CAP
    idx = np.minimum(np.searchsorted(cdf, rnd.uniform(F)[:n_all]), nt - 1)
    phi = angs[idx] + (rnd.uniform(F)[:n_all] - 0.5) * (2 * math.pi / nt)
    pick = rnd.uniform(F)[:n_all] < 0.85
    ee = np.where(pick, rnd.exponential(F, L1)[:n_all], rnd.exponential(F, L2)[:n_all])
    ee = np.minimum(ee, reach)
    xs = e.cx + (1.0 + ee) * R * np.cos(phi)
    ys = e.cy + (1.0 + ee) * R * np.sin(phi)
    u_col = rnd.uniform(F)[:n_all]
    cols = chip_colour_fixed(e.src, phi, u_col, lightness)
    is_dust = np.arange(n_all) >= n
    keep = ~(is_dust & (ee < 0.15) & (rnd.uniform(F)[:n_all] > limb_keep))
    rad = grain_radii(rnd, n_all, R, is_dust)
    amp = np.where(is_dust, 0.30 + 0.45 * rnd.uniform(F)[:n_all], 0.6 + 0.4 * rnd.uniform(F)[:n_all]) * amp_k
    fade = edge_fade(xs, ys, scene.W, scene.H, scene.S)
    amp = amp * fade * np.exp(-0.5 * ee)
    gl.add_grains(rnd, xs[keep], ys[keep], rad[keep], cols[keep], amp[keep])
    return gl


def chip_colour_fixed(src, phi, u, Lrange):
    """chip_colour with the lightness taken from a given uniform array (so the caller controls the stream)."""
    class _R:
        def __init__(self, u):
            self.u = u

        def uniform(self, n, lo=0.0, hi=1.0):
            return lo + (hi - lo) * self.u[:n]
    return chip_colour(src, phi, _R(u), Lrange)


def outline_chunks(scene, ei, n, chips, wind=None, b=0.25, tag="chunks", lightness=(0.78, 0.94), e_scale=0.3, alpha=0.95):
    """Iris-chips round the exposed outline: diameter 1.6-3.0 % R (capped at 3.0 %, AD D5), 60 percent of the old count."""
    rnd = scene.rand(f"{tag}/{ei}")
    e = scene.eyes[ei]
    R = e.R
    nt = 2048
    angs = (np.arange(nt) + 0.5) * (2 * math.pi / nt)
    dens = union_exposed(scene, ei, angs).astype(np.float64)
    if wind is not None:
        dens *= 1.0 + b * np.cos(angs - wind)
    cdf = np.cumsum(dens)
    cdf /= cdf[-1]
    n = int(round(n * 0.6))
    if n <= 0:
        return
    idx = np.minimum(np.searchsorted(cdf, rnd.uniform(n)), nt - 1)
    phi = angs[idx]
    ee = 0.04 + rnd.exponential(n, e_scale)
    ee = np.minimum(ee, 1.0)
    xs = e.cx + (1.0 + ee) * R * np.cos(phi)
    ys = e.cy + (1.0 + ee) * R * np.sin(phi)
    cols = chip_colour(e.src, phi, rnd, lightness)
    size = chunk_size(rnd, n, R, ee)
    fade = edge_fade(xs, ys, scene.W, scene.H, scene.S)
    chips.add(xs, ys, size, rnd.uniform(n) * 360.0, cols, rnd.integers(n, 0, atlas()["n"]), alpha * fade, srcs=e.src, phi=phi, Rpx=R)


def blobs(scene, ei, n, tag="blobs", e_lo=0.25, e_hi=0.9, wind=None):
    """Defocused blobs (4-6 % R, blur, alpha 0.40-0.50), lighter or darker than the local matter. Returns (light SplatList, dark list as
    negative-amp is not possible in a screen layer, so darker ones are just dimmer): one SplatList."""
    rnd = scene.rand(f"{tag}/{ei}")
    e = scene.eyes[ei]
    sl = SplatList()
    phi = rnd.uniform(n) * 2 * math.pi
    ee = rnd.uniform(n, e_lo, e_hi)
    xs = e.cx + (1.0 + ee) * e.R * np.cos(phi)
    ys = e.cy + (1.0 + ee) * e.R * np.sin(phi)
    cols = chip_colour(e.src, phi, rnd, (0.55, 0.80))
    sig = e.R * rnd.uniform(n, 0.04, 0.06) * 0.6
    amp = rnd.uniform(n, 0.10, 0.22)
    fade = edge_fade(xs, ys, scene.W, scene.H, scene.S)
    sl.add(xs, ys, sig, cols, amp * fade)
    return sl
