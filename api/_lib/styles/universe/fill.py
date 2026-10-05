# -*- coding: utf-8 -*-
"""uni_fill: the enlarged-iris fill engine of the UNIVERSE family (brief 3.5.1 + the AD round of 2026-09-30). numpy + PIL only.

  uniform mode  the restored iris scaled by k_s about its own centre (pupil hidden behind the real iris: k_s * r_p <= 0.97 R,
                otherwise k_s is lowered to 0.97 R / r_p, not below 2.2, else the pupil zone is folded), mirrored radially beyond the limbus
  polar mode    slit / bar pupils, pets and tall canvases: canvas radius r in [R, 3R] maps to source rho = 0.55 + 0.40 min(1, (r - R) / 2R),
                angle kept (elliptical radius for bar irises); beyond 2.8 R the mapping breathes (rho folds between 0.55 and 0.95) instead of freezing
  resolution    magnification m = k_s R_canvas / R_src; above 2.5 a radially oriented anisotropic fibre noise (18 percent, finer cells) is added so a
                magnified fill never reads as planks or blocks
  darkening     FillStyle: the fill is placed in LINEAR light so that its mean L* in 1.0-1.5 R lands on clamp(0.27 L_ring + 2, 9, 16.5) (light eyes 12-16,
                dark brown 9-12, always >= 15 L* below the iris), chroma kept rich (C*/L* about 0.9-1.0), grey eyes get a cool 215-250 deg neutral
                (fill only), dark brown 30 percent copper; soft floor; dark well 0.55 -> 1.0 over 0.25 R
  blends        pair: OKLCH crossfade +-0.35 R about the perpendicular bisector (short hue arc, chroma 0.9 max(C1, C2)), ridge multiply 0.6 on the
                territory border; groups: Voronoi softmax sigma 0.30 R, every eye confined to 2.6-3.2 R, OKLCH blend, ridge 0.6
The source is always the restored iris pixels (never the composited artwork), so the hash test is untouched.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_fill.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np
from PIL import Image

from .common import C, smooth, luma, ramp_rgb, enlarge_band, EImgs, limb_L
from .engine import to_lin, to_disp

K_TARGET = 3.5
EXT_CAP = 1.3                # the extended source covers rho <= 1.3 (memory); farther pixels evaluate the same radial fold directly
K_MIN = 2.2
PUPIL_HIDE = 0.97
RESYNTH_M = 0.0              # fibre re-synthesis at EVERY size (the AD wanted it above m 2.5; switching it on with the magnification made the 1024 and the 4096
                             # picture different: design-only SSIM 0.98 instead of 0.997)
RESYNTH_AMP = 0.18           # AD: 18 percent (was 8)
WELL_MULT = 0.55             # AD: 0.42 -> 0.55 once the fill is darker
WELL_WIDTH = 0.25
GROUP_SIGMA = 0.36           # AD: 0.50 -> 0.30 R; 0.36 with wavy borders (a straight 0.30 R border read as a paper cut)
TERR_WAVE = 0.24            # borders meander: each territory distance gets +-0.24 R of low-frequency noise (correlation about 0.6 R)
TERR_CUT = (2.6, 0.6)        # a group eye's territory: full weight to 2.6 R, gone at 3.2 R (no mirror ghost)
RIDGE = 0.55                 # multiply on a territory border (Utah's warm / cold split)
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
GAMMA = 2.2

# ----------------------------------------------------------------------------- OKLab (display values with the pipeline's gamma 2.2)
_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]], np.float32)
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]], np.float32)
_M1i = np.linalg.inv(_M1).astype(np.float32)
_M2i = np.linalg.inv(_M2).astype(np.float32)


def to_oklab(disp):
    lin = np.power(np.maximum(disp, 0.0), GAMMA)
    lms = np.cbrt(lin @ _M1.T)
    return lms @ _M2.T


def from_oklab(lab):
    lms = lab @ _M2i.T
    lin = (lms * lms * lms) @ _M1i.T
    return np.power(np.clip(lin, 0.0, 1.0), 1.0 / GAMMA).astype(np.float32)


def blend_oklch(fills, ws, chroma_k=0.90):
    """Blend display-space fills with weights ws (each (h, w), normalised to sum 1). Where one weight is 1 the fill is returned untouched; in the
    mixing zone lightness mixes linearly, the hue turns along the SHORT arc (the mean of the chroma-weighted unit vectors) and the chroma is
    lifted toward chroma_k * max(C_k) (Lab mixing of two hues goes through grey mud). Returns (h, w, 3)."""
    n = len(fills)
    out = fills[0] * ws[0][..., None]
    for k in range(1, n):
        out = out + fills[k] * ws[k][..., None]
    wmax = ws[0]
    sq = ws[0] * ws[0]
    for k in range(1, n):
        wmax = np.maximum(wmax, ws[k])
        sq = sq + ws[k] * ws[k]
    zone = (1.0 - wmax) > 0.004
    if not zone.any():
        return out
    iy, ix = np.nonzero(zone)
    Lm = np.zeros(len(iy), np.float32)
    v = np.zeros((len(iy), 2), np.float32)
    Cmix = np.zeros(len(iy), np.float32)
    Cmax = np.zeros(len(iy), np.float32)
    wz = [w[iy, ix] for w in ws]
    labs = []
    for k in range(n):
        lab = to_oklab(fills[k][iy, ix])
        labs.append(lab)
        Ck = np.hypot(lab[:, 1], lab[:, 2])
        uk = lab[:, 1:] / np.maximum(Ck, 1e-4)[:, None]
        Lm += wz[k] * lab[:, 0]
        Cmix += wz[k] * Ck
        v += (wz[k] * (Ck + 0.012))[:, None] * uk
        Cmax = np.maximum(Cmax, np.where(wz[k] > 0.05, Ck, 0.0))
    b = np.clip((1.0 - sum(w * w for w in wz)) * 2.0, 0.0, 1.0)
    Cout = Cmix + b * np.maximum(chroma_k * Cmax - Cmix, 0.0)
    vn = np.hypot(v[:, 0], v[:, 1])
    # opposite hues: the vector sum collapses, the dominant eye's hue decides there
    kdom = np.zeros(len(iy), np.int64)
    best = np.full(len(iy), -1.0, np.float32)
    for k in range(n):
        m = wz[k] > best
        kdom[m] = k
        best = np.where(m, wz[k], best)
    lab_dom = np.stack(labs, 0)[kdom, np.arange(len(iy))]
    ud = lab_dom[:, 1:] / np.maximum(np.hypot(lab_dom[:, 1], lab_dom[:, 2]), 1e-4)[:, None]
    uvec = np.where((vn > 0.02)[:, None], v / np.maximum(vn, 1e-6)[:, None], ud)
    lab = np.stack([Lm, Cout * uvec[:, 0], Cout * uvec[:, 1]], 1)
    out[iy, ix] = from_oklab(lab)
    return out


# ----------------------------------------------------------------------------- per eye set-up
def pupil_rmax(src):
    pr = src.pup
    ang = pr["ang"] if "ang" in pr else (np.arange(len(pr["r_theta"])) + 0.5) * (2 * math.pi / len(pr["r_theta"]))
    px = pr["cx"] + pr["r_theta"] * np.cos(ang)
    py = pr["cy"] + pr["r_theta"] * np.sin(ang)
    return float(np.max(np.hypot(px, py)))


def _extended(src, rho_max, rho_c):
    """Extended source E: radial mirror beyond rho 0.985, the pupil zone (rho < rho_c) folded about rho_c when rho_c > 0. Two baked touches at
    SOURCE scale (so they cost nothing per band and cannot leave a seam): a fibre unsharp mask, and a local-contrast stretch (a dark iris has
    little structure to start with; the dark fill would read as a flat wash)."""
    key = ("pm", round(rho_max, 2), round(rho_c, 3))
    got = src._ext.get(key)
    if got is not None:
        return got
    M = int(math.ceil(2.0 * rho_max * src.R)) + 2
    M += M % 2
    ax = np.arange(M, dtype=np.float32) + 0.5 - M / 2.0
    dx, dy = ax[None, :], ax[:, None]
    rho = np.sqrt(dx * dx + dy * dy) / np.float32(src.R)
    a = np.float32(0.985)
    g = src.g
    E = np.zeros((M, M, 3), np.float32)
    t = src.tgt
    o = (M - t) // 2
    if o >= 0 and not rho_c:
        E[o:o + t, o:o + t] = g
    out = rho > (a if not rho_c else 0.0)
    if o < 0 or rho_c:
        out = np.ones(rho.shape, bool)
    iy, ix = np.nonzero(out)
    dxo = dx[0, ix]
    dyo = dy[iy, 0]
    r = rho[iy, ix]
    mm = np.mod(r, 2 * a)
    rho2 = np.where(mm <= a, mm, 2 * a - mm)
    if rho_c:
        rho2 = np.where(rho2 < rho_c, 2 * rho_c - rho2, rho2)
        rho2 = np.minimum(rho2, a)
    k = rho2 / np.maximum(r, 1e-6)
    sx = np.clip(dxo * k + src.tgt / 2.0 - 0.5, 0, src.tgt - 1.001)
    sy = np.clip(dyo * k + src.tgt / 2.0 - 0.5, 0, src.tgt - 1.001)
    x0 = np.floor(sx).astype(np.int32)
    y0 = np.floor(sy).astype(np.int32)
    fx, fy = (sx - x0)[:, None], (sy - y0)[:, None]
    E[iy, ix] = (g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x0 + 1] * fx * (1 - fy) + g[y0 + 1, x0] * (1 - fx) * fy
                 + g[y0 + 1, x0 + 1] * fx * fy).astype(np.float32)
    B = C.blur(E, 1.3)
    E = np.clip(E + 0.85 * (E - B), 0.0, 1.0).astype(np.float32)
    # local contrast about a 0.034 R_src mean (the old per-band blur of the fill, now at source scale: band independent)
    darkest = limb_L(src)
    c = float(np.clip((40.0 - darkest) / 14.0, 0.0, 1.0)) * 0.9 + 0.25
    Bm = C.blur(E, 0.034 * src.R)
    E = np.clip(Bm + (E - Bm) * (1.0 + c), 0.0, 1.0).astype(np.float32)
    src._ext[key] = (EImgs(E), M)
    return src._ext[key]


def territory_reach(scene, e):
    """Farthest distance (px) from eye e of a canvas pixel where its fill still carries weight (solo: the far corner; pair: up to the
    crossfade; groups: its Voronoi cell plus the blend margin). Sampled on a coarse grid."""
    gx = np.linspace(0, scene.W, 65, dtype=np.float32)
    gy = np.linspace(0, scene.H, 49, dtype=np.float32)
    x, y = gx[None, :], gy[:, None]
    d = np.sqrt((x - e.cx) ** 2 + (y - e.cy) ** 2)
    if scene.n == 1:
        return float(d.max())
    w = territory_w(scene, x, y, e.index)
    m = w > 5e-4
    return float(d[m].max()) + 0.3 * e.R if m.any() else 3.0 * e.R


def territory_w(scene, x, y, k, nz=None):
    """Weight of eye k at canvas points (x (1, w), y (h, 1)): pair = smooth crossfade about the bisector, groups = Voronoi softmax (sigma 0.36 R)
    with the territory cut at 2.6-3.2 R. nz: optional per-eye noise arrays 0..1 (the same shape as the points) that make the borders meander
    (pair: nz[0] only). Not normalised."""
    eyes = scene.eyes
    if scene.n == 2:
        a, b = eyes
        dx, dy = b.cx - a.cx, b.cy - a.cy
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        s = ((x - (a.cx + b.cx) / 2.0) * ux + (y - (a.cy + b.cy) / 2.0) * uy) / np.float32(0.5 * (a.R + b.R))
        if nz is not None:
            s = s + np.float32(TERR_WAVE * 0.8) * (2.0 * nz[0] - 1.0)
        wb = smooth((s + 0.35) / 0.70)
        return (1.0 - wb) if k == 0 else wb
    dd = []
    for j, o in enumerate(eyes):
        dj = np.sqrt((x - o.cx) ** 2 + (y - o.cy) ** 2) / np.float32(o.R)
        if nz is not None:
            dj = dj + np.float32(TERR_WAVE) * (2.0 * nz[j] - 1.0)
        dd.append(dj)
    dmin = dd[0]
    for q in dd[1:]:
        dmin = np.minimum(dmin, q)
    w = np.exp(-(dd[k] * dd[k] - dmin * dmin) / np.float32(2 * GROUP_SIGMA ** 2))
    c0 = np.maximum(TERR_CUT[0], dmin + 0.25)
    return w * (1.0 - smooth((dd[k] - c0) / TERR_CUT[1]))


def territory_noise(scene, y0, y1, f, hc, Wc):
    """Low-frequency noise 0..1 per eye on the coarse grid of rows y0..y1 (band independent: a NoiseGrid is a function of canvas position)."""
    from .engine import NoiseGrid
    cache = getattr(scene, "_terr_ng", None)
    if cache is None:
        cache = scene._terr_ng = {}
    need = 1 if scene.n == 2 else scene.n
    out = []
    for k in range(need):
        ng = cache.get(k)
        if ng is None:
            ng = cache[k] = NoiseGrid(scene, f"terr{k}", cells=5, octaves=3, gain=0.5)
        out.append(ng.band(y0, y0 + hc * f, out_w=Wc, out_h=hc))
    return out


def setup_eye(scene, e, k_target=K_TARGET, mode=None):
    """Choose the enlargement of one eye and prepare its extended source."""
    src = e.src
    rmax = pupil_rmax(src)
    cls = src.pup.get("cls", "round")
    pet = bool(scene.opts.get("pet")) or bool(getattr(e.iris, "is_pet", False))     # species known: pets are ALWAYS polar (brief 3.5.8)
    e.fill_mode = mode or ("polar" if (cls in ("slit", "bar") or pet) else "uniform")
    e.ellipse = scene.opts.get("ellipse") if e.fill_mode == "polar" else None
    e.rho_c = 0.0
    if e.fill_mode == "uniform":
        k = min(k_target, PUPIL_HIDE / max(rmax, 1e-3))
        if k < K_MIN:                     # a very wide pupil: keep 2.6 and fold the pupil zone into iris texture
            k = min(k_target, 2.6)
            e.rho_c = min(0.62, rmax * 1.06 + 0.015)
        e.k_s = k
        e.s = k * e.R / src.R
        reach = territory_reach(scene, e)
        rho_max = min(EXT_CAP, reach / (k * e.R) + 0.03)
        e.E, e.M = _extended(src, max(rho_max, 1.0), e.rho_c)           # beyond it the fold is evaluated on the fly (fold_far)
    else:
        e.k_s = 1.0
        e.s = 1.0
        e.E = e.M = None
    e.magnification = e.s
    e.style = None
    return e


# ----------------------------------------------------------------------------- fill of one eye on a band
def polar_rho(r, wall=False):
    """Source radius for a canvas radius r (units of R) in polar mode: 0.55 -> 0.95 over 1-3 R, then the source radius BREATHES between 0.95 and 0.55
    (period 2.4 R) instead of freezing: no flat plain and no visible switch arc on a tall canvas."""
    base = 0.55 + 0.40 * np.minimum(1.0, np.maximum(r - 1.0, 0.0) / 2.0)
    u = np.maximum(r - 3.0, 0.0) / 1.2                       # half periods beyond 3 R
    return np.where(r > 3.0, 0.55 + 0.40 * (0.5 + 0.5 * np.cos(np.pi * u)), base)


def polar_band(scene, e, y0, y1, f=1):
    src = e.src
    x, y = scene.band_xy(y0, y1, f)
    a = float(getattr(e, "ellipse", None) or 1.0)           # D17: the iris of a horse is a true oval rx : ry = a, the radial frame follows it
    dx = (x - e.cx) / np.float32(a)
    dy = y - e.cy
    r = np.sqrt(dx * dx + dy * dy) / np.float32(e.R)
    th = np.arctan2(np.broadcast_to(dy, r.shape), np.broadcast_to(dx, r.shape))
    rho = polar_rho(r)
    sx = src.R + rho * src.R * np.cos(th) - 0.5
    sy = src.R + rho * src.R * np.sin(th) - 0.5
    sx = np.clip(sx, 0, src.tgt - 1.001)
    sy = np.clip(sy, 0, src.tgt - 1.001)
    x0 = np.floor(sx).astype(np.int32)
    y0_ = np.floor(sy).astype(np.int32)
    fx, fy = (sx - x0)[..., None], (sy - y0_)[..., None]
    g = src.g
    out = (g[y0_, x0] * (1 - fx) * (1 - fy) + g[y0_, x0 + 1] * fx * (1 - fy) + g[y0_ + 1, x0] * (1 - fx) * fy + g[y0_ + 1, x0 + 1] * fx * fy)
    return out.astype(np.float32)


def fold_far(scene, e, out, y0, y1, f, cols=None, rows=None):
    """Pixels farther than the extended source reaches: the very same radial mirror fold (angle kept, rho folded about 0.985 and, when the
    pupil zone is folded, about rho_c) evaluated per pixel straight from the source. Writes into out in place."""
    src = e.src
    x, y = scene.band_xy(y0, y1, f)
    dx = x - e.cx
    dy = y - e.cy
    rpx = np.sqrt(dx * dx + dy * dy)
    edge = (e.M / 2.0 - 2.0) * e.s
    m = rpx > edge
    if cols is not None or rows is not None:
        mm = np.zeros(m.shape, bool)
        mm[(rows[0] if rows else 0):(rows[1] if rows else m.shape[0]), (cols[0] if cols else 0):(cols[1] if cols else m.shape[1])] = True
        m &= mm
    if not m.any():
        return out
    dxm = np.broadcast_to(dx, m.shape)[m]
    dym = np.broadcast_to(dy, m.shape)[m]
    rho = rpx[m] / np.float32(e.k_s * e.R)
    a = np.float32(0.985)
    mm_ = np.mod(rho, 2 * a)
    rho2 = np.where(mm_ <= a, mm_, 2 * a - mm_)
    if e.rho_c:
        rho2 = np.where(rho2 < e.rho_c, 2 * e.rho_c - rho2, rho2)
        rho2 = np.minimum(rho2, a)
    k = rho2 / np.maximum(rho, 1e-6)
    sx = np.clip(dxm * k / np.float32(e.k_s * e.R) * src.R + src.tgt / 2.0 - 0.5, 0, src.tgt - 1.001)
    sy = np.clip(dym * k / np.float32(e.k_s * e.R) * src.R + src.tgt / 2.0 - 0.5, 0, src.tgt - 1.001)
    x0 = np.floor(sx).astype(np.int32)
    y0_ = np.floor(sy).astype(np.int32)
    fx, fy = (sx - x0)[:, None], (sy - y0_)[:, None]
    g = src.g
    col = (g[y0_, x0] * (1 - fx) * (1 - fy) + g[y0_, x0 + 1] * fx * (1 - fy) + g[y0_ + 1, x0] * (1 - fx) * fy + g[y0_ + 1, x0 + 1] * fx * fy)
    out[m] = col
    return out


def eye_band(scene, e, y0, y1, f=1):
    if e.fill_mode == "polar":
        return polar_band(scene, e, y0, y1, f)
    hc, Wc = scene.grid(y0, y1, f)
    y0c = y0 // f
    out = enlarge_band(e.E, e.M, e.cx / f, e.cy / f, e.s / f, y0c, y0c + hc, Wc)
    out = fold_far(scene, e, out, y0, y1, f)
    if scene.n == 1 and scene.layout.aspect == "9:19.5":
        out = _wall_blend(scene, e, out, y0, y1, f)
    return out


def _wall_blend(scene, e, out, y0, y1, f):
    """AD D12: on the tall wallpaper the uniform enlargement ends at rho 0.985 (r = 3.45 R) in a dark ring (the limbal band mirrored), a visible disc edge. Beyond 2.8 R
    the fill is blended over 0.8 R into the polar mapping whose rho breathes between 0.95 and 0.55 (no ring, no frozen plain)."""
    x, y = scene.band_xy(y0, y1, f)
    r = np.sqrt((x - e.cx) ** 2 + (y - e.cy) ** 2) / np.float32(e.R)
    m = smooth((r - 2.8) / 0.8)
    if not (m > 0).any():
        return out
    P = polar_band(scene, e, y0, y1, f)
    return out * (1.0 - m)[..., None] + P * m[..., None]


def _eye_band_cols(scene, e, y0, y1, f, c0, c1):
    """eye_band restricted to coarse columns c0..c1 (same pixels as the full band)."""
    if e.fill_mode == "polar":
        return polar_band(scene, e, y0, y1, f)[:, c0:c1]
    hc, Wc = scene.grid(y0, y1, f)
    y0c = y0 // f
    out = enlarge_band(e.E, e.M, e.cx / f - c0, e.cy / f, e.s / f, y0c, y0c + hc, c1 - c0)
    full = np.zeros((hc, Wc, 3), np.float32)
    full[:, c0:c1] = out
    fold_far(scene, e, full, y0, y1, f, cols=(c0, c1))
    return full[:, c0:c1]


# ----------------------------------------------------------------------------- fibre re-synthesis
class FibreNoise:
    """Radially oriented anisotropic noise 0..1 as a function of (r / R, angle): angular cells N_TH round the circle, radial cells of
    0.09 R (two octaves) plus a fine octave (0.045 R, 3x the angular cells) that breaks up the magnified fibres. Bilinear from small periodic
    grids, so it is the same picture at any canvas size."""
    N_TH = 1800
    RC = 0.09
    R_MAX = 5.0

    def __init__(self, rnd):
        nr = int(self.R_MAX / self.RC) + 3
        self.g = rnd.uniform((nr, self.N_TH)).astype(np.float32)
        self.g2 = rnd.uniform((nr // 2 + 3, self.N_TH // 6)).astype(np.float32)
        self.g3 = rnd.uniform((2 * nr, self.N_TH * 3)).astype(np.float32)

    def sample(self, r, th):
        u = (r / self.RC).astype(np.float32)
        v = ((th + math.pi) * (self.N_TH / (2 * math.pi))).astype(np.float32)
        out = _bil2d(self.g, u, v, wrap_v=True)
        u2 = (r / (2 * self.RC)).astype(np.float32)
        v2 = ((th + math.pi) * (self.N_TH / 6 / (2 * math.pi))).astype(np.float32)
        out2 = _bil2d(self.g2, u2, v2, wrap_v=True)
        u3 = (r / (0.5 * self.RC)).astype(np.float32)
        v3 = ((th + math.pi) * (3 * self.N_TH / (2 * math.pi))).astype(np.float32)
        out3 = _bil2d(self.g3, u3, v3, wrap_v=True)
        return 0.40 * out + 0.25 * out2 + 0.35 * out3


def _bil2d(g, u, v, wrap_v=False):
    nr, nc = g.shape
    u = np.clip(u, 0, nr - 1.001)
    i0 = np.floor(u).astype(np.int32)
    fu = u - i0
    j0f = np.floor(v)
    fv = v - j0f
    j0 = (j0f.astype(np.int32)) % nc
    j1 = (j0 + 1) % nc
    return (g[i0, j0] * (1 - fu) * (1 - fv) + g[i0, j1] * (1 - fu) * fv + g[i0 + 1, j0] * fu * (1 - fv) + g[i0 + 1, j1] * fu * fv)


def fibre_noise_field(e, x, y, stride=2, origin=(0, 0)):
    """The radial fibre noise of eye e at canvas points (x (1, w), y (h, 1)) -> (h, w), 0..1. It is a smooth function of (r / R, angle), so it is evaluated on
    every second point of the GLOBAL coarse grid (origin = the global (row, column) index of the first point: the decimation phase is then the same whatever
    band or rectangle asks) and brought back by linear interpolation: a quarter of the cost, and the picture does not depend on the band layout."""
    h, w = y.shape[0], x.shape[1]
    if min(h, w) < 48:
        stride = 1
    if stride == 1:
        dx, dy = x - e.cx, y - e.cy
        r = np.sqrt(dx * dx + dy * dy) / np.float32(e.R)
        th = np.arctan2(np.broadcast_to(dy, r.shape), np.broadcast_to(dx, r.shape))
        return e.fibre_noise.sample(r, th)
    off_r = (-origin[0]) % stride
    off_c = (-origin[1]) % stride
    xs, ys = x[:, off_c::stride], y[off_r::stride, :]
    dx, dy = xs - e.cx, ys - e.cy
    r = np.sqrt(dx * dx + dy * dy) / np.float32(e.R)
    th = np.arctan2(np.broadcast_to(dy, r.shape), np.broadcast_to(dx, r.shape))
    nd = e.fibre_noise.sample(r, th)
    nr, nc = nd.shape
    ur = np.clip((np.arange(h, dtype=np.float32) - off_r) / stride, 0, nr - 1)
    uc = np.clip((np.arange(w, dtype=np.float32) - off_c) / stride, 0, nc - 1)
    i0 = np.minimum(ur.astype(np.int32), max(nr - 2, 0))
    j0 = np.minimum(uc.astype(np.int32), max(nc - 2, 0))
    fr = (ur - i0)[:, None]
    fc = (uc - j0)[None, :]
    i1 = np.minimum(i0 + 1, nr - 1)
    j1 = np.minimum(j0 + 1, nc - 1)
    top = nd[i0][:, j0] * (1 - fc) + nd[i0][:, j1] * fc
    bot = nd[i1][:, j0] * (1 - fc) + nd[i1][:, j1] * fc
    return (top * (1 - fr) + bot * fr).astype(np.float32)


def resynth(scene, e, fill, y0, y1, f=1, amp=RESYNTH_AMP):
    """Multiply the fill by 1 + amp (2 n - 1) with n the radial noise round eye e. Noise of mean 0.5 and a standard deviation of about 0.15: a +-18 percent
    peak, mostly +-5 percent."""
    x, y = scene.band_xy(y0, y1, f)
    n = fibre_noise_field(e, x, y, origin=(y0 // f, 0))
    fill *= (1.0 + amp * (2.0 * n - 1.0))[..., None]
    return fill


# ----------------------------------------------------------------------------- the darkening (FillStyle)
COPPER_C = None


def _lin(x):
    return np.power(np.maximum(x, 0.0), GAMMA)


def _disp(x):
    return np.power(np.maximum(x, 0.0), np.float32(1.0 / GAMMA))


def _Lstar(Y):
    Y = np.maximum(Y, 0.0)
    return np.where(Y > 0.008856, 116.0 * np.cbrt(Y) - 16.0, 903.3 * Y)


def _Ystar(L):
    return np.where(L > 8.0, ((L + 16.0) / 116.0) ** 3, L / 903.3)


class FillStyle:
    """Per-eye darkening of the enlarged iris, display -> display. Everything is in linear light: luminance scaled to the target, the chromaticity
    (lin / Y) pushed out by `sat`, optionally pulled toward a cool neutral (grey eyes) or copper (dark brown), then a soft floor, the profile
    (a little darker outward) and the dark well (multiply in display space, as the brief says)."""

    def __init__(self, src, e_fill_k):
        self.src = src
        cls = src.cls
        st = src.stats
        L_ring, C_ring = float(st["L"]), float(st["C"])
        self.cls = cls
        self.target = float(np.clip(0.27 * L_ring + 2.0, 9.0, 16.5))
        self.sat = 1.30
        self.gamma_c = 1.22                     # a power on the linear luminance: +22 percent log contrast, so the fibres of the dark fill read
        self.hue_pull = 0.25 if C_ring >= 22.0 else 0.50      # the chromaticity is pulled toward the eye's own mean: no olive blotches on a blue eye
        self.cool = 0.0
        self.cool_gain = 1.0
        self.copper = 0.0
        if cls == "dark_brown":
            self.copper, self.sat = 0.30, 1.55
            self.target = float(np.clip(0.27 * L_ring + 0.8, 7.5, 10.0))
        elif cls == "grey" or C_ring < 12.0:
            self.cool = 0.60 if cls == "grey" else 0.50
            self.sat = 1.10
        self.floor_L = 6.0 + 1.5 * float(np.clip((34.0 - L_ring) / 12.0, 0.0, 1.0))
        self.well = WELL_MULT if L_ring >= 34.0 else float(np.clip(WELL_MULT * (L_ring / 34.0) ** 1.2, 0.30, WELL_MULT))
        self.k0 = 1.0
        self.ref = None
        self._cool_vec = None
        self._cu_vec = None

    # -- colour vectors (luminance 1)
    @staticmethod
    def _unit_lum(c):
        c = np.maximum(np.asarray(c, np.float32), 1e-4)
        return c / float(c @ LUMA)

    def cool_vec(self):
        if self._cool_vec is None:
            rgb = C.from_lch(16.0, 8.0, 236.0).astype(np.float32)
            v = self._unit_lum(_lin(rgb))
            self._cool_vec = self._unit_lum(np.maximum(1.0 + (v - 1.0) * self.cool_gain, 0.02))
        return self._cool_vec

    def ring_vec(self):
        if getattr(self, "_ring_vec", None) is None:
            self._ring_vec = self._unit_lum(_lin(np.asarray(self.src.iris.ring).mean(0)))
        return self._ring_vec

    def copper_vec(self):
        if self._cu_vec is None:
            self._cu_vec = self._unit_lum(_lin(C.rgb01("#8A4A1F")))
        return self._cu_vec

    def chroma_vec(self, lin, Y):
        c = lin / np.maximum(Y, 1e-5)[..., None]
        c = c * (1.0 - self.hue_pull) + self.ring_vec()[None, None, :] * self.hue_pull
        c = np.maximum(1.0 + (c - 1.0) * self.sat, 0.02)
        if self.copper > 0:
            c = c * (1 - self.copper) + self.copper_vec()[None, None, :] * self.copper
        if self.cool > 0:
            c = c * (1 - self.cool) + self.cool_vec()[None, None, :] * self.cool
        c = c / np.maximum(c @ LUMA, 1e-4)[..., None]
        return c

    def floor_vec(self):
        """Linear colour of the soft floor: the eye's own mean ring colour at floor_L."""
        ring = np.asarray(self.src.iris.ring).mean(0)
        c = self._unit_lum(_lin(ring))
        if self.cool > 0:
            c = c * (1 - self.cool) + self.cool_vec() * self.cool
        return (c * float(_Ystar(self.floor_L))).astype(np.float32)

    def apply(self, Fd, rn):
        """Fd display (h, w, 3) enlarged iris, rn (h, w) distance to the nearest iris centre in R: returns the finished fill in display space."""
        lin = _lin(Fd)
        Y = lin @ LUMA
        c = self.chroma_vec(lin, Y)
        prof = 1.0 - 0.30 * smooth((rn - 1.0) / 1.8)
        Yo = np.power(np.maximum(Y, 1e-6) / 0.05, self.gamma_c) * 0.05 * np.float32(self.k0) * prof
        out = c * Yo[..., None]
        fl = self.floor_vec()
        Yf = float(fl @ LUMA)
        out = out + fl[None, None, :] * np.exp(-Yo / np.float32(0.8 * Yf))[..., None]
        d = _disp(out)
        e = np.maximum(rn - 1.0, 0.0)
        well = 1.0 - (1.0 - self.well) * (1.0 - smooth(e / WELL_WIDTH))
        d *= well[..., None]
        return d

    def _zone_samples(self, e):
        """Display colours of the source where the fill of 1.0-1.5 R comes from (angles x radii), and their nearest-iris distance rn."""
        src = e.src
        th = (np.arange(48) + 0.5) * (2 * math.pi / 48)
        rn = np.linspace(1.0, 1.5, 6)
        RN, TH = np.meshgrid(rn, th)
        if e.fill_mode == "polar":
            rho = polar_rho(RN)
        else:
            rho = RN / max(e.k_s, 1e-3)
            if e.rho_c:
                rho = np.where(rho < e.rho_c, 2 * e.rho_c - rho, rho)
        rho = np.minimum(rho, 0.985)
        sx = np.clip(src.R + rho * src.R * np.cos(TH) - 0.5, 0, src.tgt - 1.001)
        sy = np.clip(src.R + rho * src.R * np.sin(TH) - 0.5, 0, src.tgt - 1.001)
        x0 = np.floor(sx).astype(np.int32)
        y0 = np.floor(sy).astype(np.int32)
        fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
        g = src.g
        col = g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x0 + 1] * fx * (1 - fy) + g[y0 + 1, x0] * (1 - fx) * fy + g[y0 + 1, x0 + 1] * fx * fy
        return col.reshape(-1, 1, 3).astype(np.float32), RN.reshape(-1, 1).astype(np.float32)

    def _measure(self, col, rn):
        d = self.apply(col, rn)
        Ls, Cc, hh = C.lch(np.clip(d, 0, 1).reshape(-1, 3))
        return float(Ls.mean()), float(Cc.mean())

    def _fit_k0(self, col, rn, lo=0.01, hi=3.0):
        for _ in range(16):
            mid = math.sqrt(lo * hi)
            self.k0 = mid
            L, _ = self._measure(col, rn)
            if L < self.target:
                lo = mid
            else:
                hi = mid
        self.k0 = math.sqrt(lo * hi)
        return self.k0

    def calibrate(self, e):
        """Set k0 (and, if the colour is too pale, the chroma push) so that the FINISHED fill (floor, well and all) has a mean L* of `target` in
        1.0-1.5 R: measured on the real pipeline function over a sample of the source zone that feeds that ring (angles x radii). A wide pupil
        makes the near zone black: the reference for the luminance is then at least 0.62 of the iris body's L* (a natural socket, never a boost
        into mud). Chroma: C*/L* >= 0.9 for coloured eyes (Utah's fill is 1.0), and C* about 7 (6-9) for the cool grey fill."""
        col, rn = self._zone_samples(e)
        src = e.src
        Y = luma(_lin(src.g))
        mb = (src.rho > 0.43) & (src.rho < 0.80)
        body_L = float(_Lstar(np.float32(Y[mb].mean())))
        Ls_near = float(C.lch(np.clip(col, 0, 1).reshape(-1, 3))[0].mean())
        if Ls_near < 0.62 * body_L:                                   # a black pupil zone: lift the samples to the body-referenced socket
            lift = float(_Ystar(np.float32(0.62 * body_L))) / max(float(luma(_lin(col)).mean()), 1e-4)
            col = _disp(_lin(col) * np.float32(min(lift, 40.0)))
        if self.cool > 0:
            for m in (1.0, 1.7, 2.6, 3.8, 5.5):
                self.cool_gain = m
                self._cool_vec = None
                self._fit_k0(col, rn)
                L, Cm = self._measure(col, rn)
                if Cm >= 6.5:
                    break
        else:
            for sat in (self.sat, self.sat + 0.3, self.sat + 0.65, self.sat + 1.05, self.sat + 1.5):
                self.sat = sat
                self._fit_k0(col, rn)
                L, Cm = self._measure(col, rn)
                if Cm / max(L, 1e-3) >= 0.98:              # the image measures about 0.06 lower (accent, vignette, upsampling)
                    break
        self.measured = (L, Cm)
        return self.k0


def fill_style(e):
    """The FillStyle of an eye, calibrated once per (source, enlargement) and cached on the source: a second render of the same eye, at any canvas size,
    reuses it (the calibration looks at the source zone in R units, not at pixels)."""
    if getattr(e, "style", None) is None:
        key = ("style", round(float(e.k_s), 3), e.fill_mode, round(float(e.rho_c), 3))
        cache = e.src._ext
        st = cache.get(key)
        if st is None:
            st = FillStyle(e.src, e.k_s)
            st.calibrate(e)
            cache[key] = st
        e.style = st
    return e.style


def eye_fill_dark(scene, e, y0, y1, f, rn_e):
    """The finished (darkened, re-synthesised) fill of ONE eye on a band, display space, (hc, Wc, 3)."""
    F = eye_band(scene, e, y0, y1, f)
    if e.fibre_noise is not None:
        resynth(scene, e, F, y0, y1, f)
    return fill_style(e).apply(F, rn_e)


def territory_weights(scene, dd_raw, nz):
    """Weights of every eye from the per-eye distance fields dd_raw (hc, Wc, in R): a pair crossfades about the perpendicular bisector over +-0.35 R, a
    group is a Voronoi softmax (sigma 0.36 R) with the territory cut at 2.6-3.2 R; the borders meander with the per-eye noise nz (TERR_WAVE)."""
    n = scene.n
    if n == 2:
        a, b = scene.eyes
        x, y = scene._bandxy
        dx, dy = b.cx - a.cx, b.cy - a.cy
        d = math.hypot(dx, dy)
        ux, uy = dx / d, dy / d
        sdist = ((x - (a.cx + b.cx) / 2.0) * ux + (y - (a.cy + b.cy) / 2.0) * uy) / np.float32(0.5 * (a.R + b.R))
        sdist = sdist + np.float32(TERR_WAVE * 0.8) * (2.0 * nz[0] - 1.0)
        wb = np.broadcast_to(smooth((sdist + 0.35) / 0.70), dd_raw[0].shape).astype(np.float32)
        return [1.0 - wb, wb]
    dd = [dd_raw[k] + np.float32(TERR_WAVE) * (2.0 * nz[k] - 1.0) for k in range(n)]
    dmin = dd[0]
    for q in dd[1:]:
        dmin = np.minimum(dmin, q)
    c0 = np.maximum(TERR_CUT[0], dmin + 0.25)
    ws = []
    for k in range(n):
        w = np.exp(-(dd[k] * dd[k] - dmin * dmin) / np.float32(2 * GROUP_SIGMA ** 2)) * (1.0 - smooth((dd[k] - c0) / TERR_CUT[1]))
        ws.append(w.astype(np.float32))
    return ws


def fill_band(scene, y0, y1, f=1):
    """The finished fill of the (coarse) grid of rows y0..y1, display space (hc, Wc, 3), with its nearest-iris distance rn (hc, Wc): one eye
    alone; a pair crossfaded about the perpendicular bisector over +-0.35 R in OKLCH; groups by a Voronoi softmax (sigma 0.36 R, each territory
    cut at 2.6-3.2 R, wavy borders); on a territory border a dark ridge (multiply 0.55). Each eye is darkened BEFORE the blend with its own
    target, so a light and a dark eye keep their own depth. Every distance field is computed once per band."""
    eyes = scene.eyes
    x, y = scene.band_xy(y0, y1, f)
    scene._bandxy = (x, y)
    hc, Wc = scene.grid(y0, y1, f)
    dd_raw = [np.broadcast_to(np.sqrt((x - e.cx) ** 2 + (y - e.cy) ** 2) / np.float32(e.R), (hc, Wc)) for e in eyes]
    rn = dd_raw[0]
    kk = np.zeros((hc, Wc), np.int8)
    for k in range(1, scene.n):
        m = dd_raw[k] < rn
        kk[m] = k
        rn = np.where(m, dd_raw[k], rn)
    if scene.n == 1:
        return eye_fill_dark(scene, eyes[0], y0, y1, f, rn), rn
    nz = territory_noise(scene, y0, y1, f, hc, Wc)
    ws = territory_weights(scene, dd_raw, nz)
    tot = ws[0].copy()
    for w in ws[1:]:
        tot = tot + w
    if float(tot.min()) < 1e-6:                               # far corner out of every territory: the nearest eye takes it
        for k in range(scene.n):
            ws[k] = np.where(tot < 1e-6, (kk == k).astype(np.float32), ws[k])
        tot = ws[0].copy()
        for w in ws[1:]:
            tot = tot + w
    ws = [w / tot for w in ws]
    fills, wsu = [], []
    for k in range(scene.n):
        w = ws[k]
        act = w > 1e-3
        if not act.any():
            continue
        rows = np.nonzero(act.any(1))[0]
        cols = np.nonzero(act.any(0))[0]
        r0, r1, c0, c1 = int(rows[0]), int(rows[-1]) + 1, int(cols[0]), int(cols[-1]) + 1
        fills.append(_eye_fill_dark_rect(scene, eyes[k], y0, y1, f, dd_raw[k], r0, r1, c0, c1, hc, Wc))
        wsu.append(w)
    out = blend_oklch(fills, wsu) if len(fills) > 1 else fills[0]
    if len(fills) > 1:
        # territory ridge: 1 - (1 - RIDGE) q^1.6 with q = second / first weight (1 on the border, small within 0.2 R of it)
        srt = np.sort(np.stack(wsu, 0), 0)
        q = srt[-2] / np.maximum(srt[-1], 1e-6)
        out *= (1.0 - (1.0 - RIDGE) * np.power(q, 1.6))[..., None]
    return out, rn


def _eye_band_rect(scene, e, y0, y1, f, r0, r1, c0, c1, hc, Wc):
    """eye_band restricted to the coarse rectangle rows r0..r1, columns c0..c1 of the band (same pixels as the full band), returned as that rectangle."""
    if e.fill_mode == "polar":
        return polar_band(scene, e, y0, y1, f)[r0:r1, c0:c1]
    y0c = y0 // f
    out = enlarge_band(e.E, e.M, e.cx / f - c0, e.cy / f, e.s / f, y0c + r0, y0c + r1, c1 - c0)
    full = np.zeros((hc, Wc, 3), np.float32)
    full[r0:r1, c0:c1] = out
    fold_far(scene, e, full, y0, y1, f, cols=(c0, c1), rows=(r0, r1))
    return full[r0:r1, c0:c1]


def _eye_fill_dark_rect(scene, e, y0, y1, f, d_k, r0, r1, c0, c1, hc, Wc):
    """The finished fill of one eye on the rectangle of the band where its weight matters (zeros elsewhere)."""
    part = _eye_band_rect(scene, e, y0, y1, f, r0, r1, c0, c1, hc, Wc)
    if e.fibre_noise is not None:
        x, y = scene.band_xy(y0, y1, f)
        n = fibre_noise_field(e, x[:, c0:c1], y[r0:r1], origin=(y0 // f + r0, c0))
        part = part * (1.0 + RESYNTH_AMP * (2.0 * n - 1.0))[..., None]
    F = np.zeros((hc, Wc, 3), np.float32)
    F[r0:r1, c0:c1] = fill_style(e).apply(part, d_k[r0:r1, c0:c1])
    return F
