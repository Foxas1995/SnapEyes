# -*- coding: utf-8 -*-
"""seam_plan: DG1 rung 1, the smooth contrast-adaptive seam of the S weave (Collision Infinity, Clean Infinity). numpy only at run time.

A pair's seam is planned ONCE per pair, in the lens frame (s along the axis from the lens centre, t across it, both in units of R, +t = the side
where iris A is in front), from the two irises as they lie in the lens on the canonical REF_SIDE grade. So the plan does not depend on the
render size (1024 == 4096) and has no random number in it (a pure function of the two irises and the geometry):

  1. contrast map K(s, c): CIEDE2000 between the smoothed A just above and the smoothed B just below a seam at height c (what the eye sees as the
     step of the crossfade), and a pattern energy term (a seam that cuts through strong structure shows);
  2. the seam line C(s) = a0 + a1 P1 + a2 P2 + a3 P3 (Legendre in x = s / L): a low order polynomial BY CONSTRUCTION (lateral extent and curvature are
     bounded), found by an exhaustive search over a small grid of coefficients for the minimum of  mean K + pupil attraction at the two ends +
     extent and curvature priors. It is a minimum-cost path with the curvature target built in, instead of a free path that is smoothed afterwards;
  3. the half width of the blend hw(s): narrow where the two irises are alike, wider where the step is large, then scaled down so that the share of each
     iris that is really mixed (0.02 < w < 0.98) stays inside the budget (D13: about 3 %).
"""
from __future__ import annotations

# PORT of work package WP7A (step A): seam_plan.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (no edit); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math
from dataclasses import dataclass, field
import numpy as np

HW_LO, HW_HI = 0.040, 0.095          # R: half width of the blend for the most alike / the most different pair of irises
K_LO, K_HI = 6.0, 24.0               # CIEDE2000 step across the seam that maps to HW_LO / HW_HI
MIX_BUDGET = 0.0295                  # share of each iris that may be mixed (0.02 < w < 0.98), D13 'about 3 percent'
SUPPORT_BUDGET = 0.0295              # DG1 judge: share of each iris (pi R^2) on which the blend is not exactly 0 or 1 (0 < w < 1): the strict reading of D13, so that no pixel
                                     # of an iris outside that share differs from the iris at all
BETA = 0.70                          # DG1 judge: share of the linear ramp in the blend profile; for the same support it gives a 10 to 90 percent width of 1.49 hw at 0.70 (smoothstep 1.22 hw, linear 1.60 hw)
EXT_MAX = 0.13                       # R, lateral extent of the seam line (references: 0.07 to 0.14)
DELTA = 0.06                         # R: the seam's two sides are sampled this far from the line
SIG = 0.03                           # R: smoothing of the colour maps


# ----------------------------------------------------------------------------- colour
def srgb_to_lin(c255):
    c = np.asarray(c255, np.float32) / np.float32(255.0)
    return np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92).astype(np.float32)


def lin_to_srgb255(lin):
    lin = np.clip(lin, 0.0, 1.0)
    c = np.where(lin > 0.0031308, 1.055 * np.power(lin, 1 / 2.4) - 0.055, 12.92 * lin)
    return (c * 255.0).astype(np.float32)


def srgb_to_oklab(c255):
    """sRGB 0..255 (..., 3) -> OKLab (L, a, b) float32."""
    lin = srgb_to_lin(c255)
    r, g, b = lin[..., 0], lin[..., 1], lin[..., 2]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], -1).astype(np.float32)


def oklab_to_srgb255(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = np.stack([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s], -1)
    return lin_to_srgb255(rgb)


def srgb_to_lab(c255):
    """sRGB 0..255 (..., 3) -> CIELAB (D65), float32 (same formulas as fx.core, numpy only)."""
    lin = srgb_to_lin(c255)
    x = 0.4124564 * lin[..., 0] + 0.3575761 * lin[..., 1] + 0.1804375 * lin[..., 2]
    y = 0.2126729 * lin[..., 0] + 0.7151522 * lin[..., 1] + 0.0721750 * lin[..., 2]
    z = 0.0193339 * lin[..., 0] + 0.1191920 * lin[..., 1] + 0.9503041 * lin[..., 2]
    x, z = x / 0.95047, z / 1.08883

    def f(v):
        return np.where(v > 0.008856, np.cbrt(v), 7.787 * v + 16.0 / 116.0)
    fx_, fy_, fz_ = f(x), f(y), f(z)
    return np.stack([116.0 * fy_ - 16.0, 500.0 * (fx_ - fy_), 200.0 * (fy_ - fz_)], -1).astype(np.float32)


def ciede2000(l1, l2):
    """CIEDE2000 (Sharma et al. 2005), numpy, arrays (..., 3) -> (...)."""
    L1, a1, b1 = [l1[..., i].astype(np.float64) for i in range(3)]
    L2, a2, b2 = [l2[..., i].astype(np.float64) for i in range(3)]
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cb = 0.5 * (C1 + C2)
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360.0
    dLp = L2 - L1
    dCp = C2p - C1p
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where((C1p * C2p) == 0, 0.0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh) / 2)
    Lbp = 0.5 * (L1 + L2)
    Cbp = 0.5 * (C1p + C2p)
    hs = h1p + h2p
    hbp = np.where(np.abs(h1p - h2p) <= 180, hs / 2, np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2))
    hbp = np.where((C1p * C2p) == 0, hs, hbp)
    T = 1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp)) + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63))
    dth = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))
    Sl = 1 + 0.015 * (Lbp - 50) ** 2 / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


# ----------------------------------------------------------------------------- small numpy helpers
def smooth(x0, x1, x):
    t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _gauss_kernel(sig_samples):
    r = max(1, int(math.ceil(3.0 * sig_samples)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / max(sig_samples, 1e-6)) ** 2)
    return (k / k.sum()).astype(np.float32), r


def blur_axis(a, sig_samples, axis):
    """Gaussian smoothing along one axis with edge replication."""
    if sig_samples <= 1e-6:
        return a
    k, r = _gauss_kernel(sig_samples)
    a = np.moveaxis(a, axis, 0)
    pad = np.concatenate([np.repeat(a[:1], r, 0), a, np.repeat(a[-1:], r, 0)], 0)
    out = np.zeros_like(a, dtype=np.float32)
    for i, w in enumerate(k):
        out += w * pad[i:i + a.shape[0]]
    return np.moveaxis(out, 0, axis)


def blur2(a, sig_samples):
    return blur_axis(blur_axis(a, sig_samples, 0), sig_samples, 1)


def sample_bilinear(img, R, px, py):
    """img: (n, n, 3) float32 tight disc square of radius R px; (px, py): offsets from the iris centre in R units (x right, y down). Returns (..., 3)."""
    n = img.shape[0]
    x = np.clip(px * R + R - 0.5, 0, n - 1.001)
    y = np.clip(py * R + R - 0.5, 0, n - 1.001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


# ----------------------------------------------------------------------------- the plan
@dataclass
class SeamPlan:
    """The seam of one weave lens in the lens frame. C(s) = sum a[k] P_k(x), x = s / L, clamped to |x| <= 1.15; hw(s) by linear interpolation of
    (s_k, hw_k). d: centre distance in R units, L = 1 - d / 2 the lens half width."""
    L: float
    a: tuple
    s_k: np.ndarray
    hw_k: np.ndarray
    info: dict = field(default_factory=dict)
    beta: float = 0.0

    def line(self, s):
        x = np.clip(s / np.float32(self.L), -1.15, 1.15)
        a0, a1, a2, a3 = self.a
        return (a0 + a1 * x + a2 * (1.5 * x * x - 0.5) + a3 * (2.5 * x * x * x - 1.5 * x)).astype(np.float32)

    def hw(self, s):
        return np.interp(s, self.s_k, self.hw_k).astype(np.float32)

    def eval(self, s):
        return self.line(s), self.hw(s)


def straight_plan(d_over_R, hw=0.085, lean=0.0):
    """A straight (optionally leaning) band of constant half width: the zero of the scale (brief's seam='band' with the references' softness)."""
    L = max(1.0 - d_over_R / 2.0, 1e-3)
    s_k = np.linspace(-1.3 * L, 1.3 * L, 9, dtype=np.float32)
    return SeamPlan(L, (0.0, lean, 0.0, 0.0), s_k, np.full(9, hw, np.float32), {"kind": "straight", "hw": hw})


def _canon(iris, C):
    sq, t = C._tight(iris.graded(C.REF_SIDE))
    return sq.astype(np.float32), t / 2.0


def lens_maps(ir_a, ir_b, d, ux, uy, C, ds=0.01, T=0.34):
    """Smoothed Lab maps of A and B on the lens grid (rows t = -T..T, columns s = -L..L, step ds R). Returns dict with s, t, labA, labB, valid, rgbA, rgbB."""
    L = 1.0 - d / 2.0
    vx, vy = uy, -ux
    s = np.arange(-L, L + 1e-9, ds, dtype=np.float32)
    t = np.arange(-T, T + 1e-9, ds, dtype=np.float32)
    S, Tt = np.meshgrid(s, t)
    pax = (S + d / 2.0) * ux + Tt * vx
    pay = (S + d / 2.0) * uy + Tt * vy
    pbx = (S - d / 2.0) * ux + Tt * vx
    pby = (S - d / 2.0) * uy + Tt * vy
    ia, Ra = _canon(ir_a, C)
    ib, Rb = _canon(ir_b, C)
    rgbA = sample_bilinear(ia, Ra, pax, pay)
    rgbB = sample_bilinear(ib, Rb, pbx, pby)
    valid = (np.hypot(pax, pay) <= 0.965) & (np.hypot(pbx, pby) <= 0.965)
    return dict(s=s, t=t, rgbA=rgbA, rgbB=rgbB, valid=valid, ds=ds, L=L)


def _cost_maps(m, sig=SIG, delta=DELTA):
    """K[j, i] = CIEDE2000 between smoothed A at t_j + delta and smoothed B at t_j - delta, column s_i; E[j, i] = pattern energy of A and B at the seam."""
    ds = m["ds"]
    rgbA, rgbB = m["rgbA"], m["rgbB"]
    sg = sig / ds
    labA = blur2(srgb_to_lab(rgbA), sg)
    labB = blur2(srgb_to_lab(rgbB), sg)
    k = int(round(delta / ds))
    nt, ns = labA.shape[:2]
    K = np.full((nt, ns), np.nan, np.float32)
    up = labA[2 * k:]
    dn = labB[:nt - 2 * k]
    K[k:nt - k] = ciede2000(up, dn)
    # pattern energy: local std of L* of the raw (unsmoothed) irises, 0.04 R window
    La, Lb = srgb_to_lab(rgbA)[..., 0], srgb_to_lab(rgbB)[..., 0]
    E = np.sqrt(np.maximum(blur2(La * La, 0.04 / ds) - blur2(La, 0.04 / ds) ** 2, 0) + np.maximum(blur2(Lb * Lb, 0.04 / ds) - blur2(Lb, 0.04 / ds) ** 2, 0)) * 0.5
    val = m["valid"]
    # a position counts only where both irises exist on both sides of it
    vv = np.zeros_like(val)
    vv[k:nt - k] = val[2 * k:] & val[:nt - 2 * k] & val[k:nt - k]
    K = np.where(vv, K, np.nan)
    return K, E.astype(np.float32), labA, labB


def _grid_candidates(ext_max=EXT_MAX):
    a0 = np.arange(-0.10, 0.0401, 0.01)
    a1 = np.arange(0.02, 0.0901, 0.01)
    a2 = np.arange(-0.02, 0.0401, 0.01)
    a3 = np.arange(-0.01, 0.0301, 0.01)
    g = np.stack(np.meshgrid(a0, a1, a2, a3, indexing="ij"), -1).reshape(-1, 4)
    x = np.linspace(-1.0, 1.0, 41)
    P = _legendre(x)
    Cc = g @ P                                                                                   # (N, nx)
    keep = (Cc.max(1) - Cc.min(1)) <= ext_max
    return g[keep], Cc[keep], x


def _legendre(x):
    return np.stack([np.ones_like(x), x, 1.5 * x * x - 0.5, 2.5 * x ** 3 - 1.5 * x], 0)


# the shape of the owner's seams (H10, H11, measured in MEASURE.md / SEAM_PATHS.png): low on the A-behind side at the end near iris A's pupil (about -0.08 R from the
# line of the centres), rising slowly and then more steeply toward the end where iris A's limb arc leaves the lens (+s), +0.03 R there: a gentle S of about 0.11 R end to end
# (the contact arcs then flow into the seam: lower-left B arc, seam, upper-right A arc). C(x) = -0.04 + 0.055 x + 0.015 x^2 in x = s / L.
SHAPE_A = (-0.035, 0.055, 0.010, 0.0)           # Legendre coefficients of that curve
SHAPE_W = 1500.0                               # ΔE00 per R^2 of mean squared departure from that shape (the colours must save more than this to move the seam)


def _path_cost(K, E, s, t, ds, cand, L, trim, xg):
    """Mean contrast K, mean pattern energy E and the number of valid samples along every candidate seam (rows of cand: Legendre coefficients), sampled at
    s = x * trim * L for the x in xg. K is nan where a side of the seam would leave the lens."""
    ns = len(s)
    xi = np.clip(np.round(xg * trim * L / ds).astype(int) + (ns - 1) // 2, 0, ns - 1)             # column of every sample position
    Cs = cand @ _legendre(xg * trim)                                                              # heights at the sampled s (x = s / L)
    jf = (Cs - t[0]) / ds
    j0 = np.clip(np.floor(jf).astype(int), 0, len(t) - 2)
    fr = np.clip(jf - j0, 0, 1)
    colK, colE = K[:, xi], E[:, xi]
    ar = np.arange(len(xi))[None, :]
    Kv = colK[j0, ar] * (1 - fr) + colK[j0 + 1, ar] * fr
    Ev = colE[j0, ar] * (1 - fr) + colE[j0 + 1, ar] * fr
    ok = np.isfinite(Kv)
    Kmean = np.where(ok.any(1), np.nanmean(np.where(ok, Kv, np.nan), 1), np.inf)
    return Kmean, Ev.mean(1), ok.sum(1)


def plan_seam(ir_a, ir_b, d_over_R, ux, uy, pup_a, pup_b, C, mode="plan", mix_budget=MIX_BUDGET, hw_lo=HW_LO, hw_hi=HW_HI, trim=0.92, shape=SHAPE_A, shape_w=SHAPE_W, beta=BETA, support_budget=SUPPORT_BUDGET):
    """The seam plan of a weave lens. ux, uy: unit vector A -> B on the canvas, d_over_R: centre distance in R. pup_a / pup_b: cx_pupil analysis dicts
    (offset of the pupil centre in R, screen axes; only reported). C: fx.core. mode 'plan' (searched around the owner's shape) or 'shape' (the shape itself, no search).
    Deterministic: no random number, no clock; a function of the two canonical (REF_SIDE) grades and the geometry."""
    d = float(d_over_R)
    L = max(1.0 - d / 2.0, 1e-3)
    vx, vy = uy, -ux
    m = lens_maps(ir_a, ir_b, d, ux, uy, C)
    K, E, labA, labB = _cost_maps(m)
    s, t, ds = m["s"], m["t"], m["ds"]
    ns = len(s)
    tA = float(pup_a["cx"] * vx + pup_a["cy"] * vy)
    tB = float(pup_b["cx"] * vx + pup_b["cy"] * vy)
    cand, Cc, xg = _grid_candidates()
    Kmean, Emean, nok = _path_cost(K, E, s, t, ds, cand, L, trim, xg)
    pa = np.asarray(shape, np.float64)
    dev = (cand - pa[None, :]) @ _legendre(xg)                                                    # departure from the owner's shape along the seam
    pen_shape = shape_w * (dev ** 2).mean(1)
    curv = np.abs(cand[:, 2] * 3.0 + cand[:, 3] * 7.5) / (L * L)                                  # about the largest |C''| (1 / R)
    pen_curv = 4.0 * curv ** 2
    J = Kmean + 0.25 * Emean + pen_shape + pen_curv
    J = np.where(nok < 0.8 * len(xg), np.inf, J)
    if mode == "shape" or not np.isfinite(J).any():
        best = int(np.argmin(((cand - pa[None, :]) ** 2).sum(1)))
    else:
        best = int(np.argmin(J))
    a = tuple(float(v) for v in cand[best])
    k_ref = _path_cost(K, E, s, t, ds, np.array([a, pa, [0.0, 0.0, 0.0, 0.0]]), L, trim, xg)[0]     # contrast along: the chosen seam, the owner's shape, the straight axis line
    # contrast along the chosen seam, smoothed along s -> half width
    sl = np.linspace(-trim * L, trim * L, 25)
    plan0 = SeamPlan(L, a, np.array([-1.3 * L, 1.3 * L], np.float32), np.array([0.08, 0.08], np.float32))
    cl = plan0.line(sl.astype(np.float32))
    jj = (cl - t[0]) / ds
    jlo = np.clip(np.floor(jj).astype(int), 0, len(t) - 2)
    ii = np.clip(np.round((sl - s[0]) / ds).astype(int), 0, ns - 1)
    kk = K[jlo, ii] * (1 - (jj - jlo)) + K[jlo + 1, ii] * (jj - jlo)
    fin = np.isfinite(kk)
    kk = np.where(fin, kk, np.mean(kk[fin]) if fin.any() else 10.0)
    spacing = 2.0 * trim * L / 24.0
    kks = blur_axis(kk.astype(np.float32)[:, None], 0.10 / spacing, 0)[:, 0]                      # smoothed along the seam over about 0.10 R
    hw_s = hw_lo + (hw_hi - hw_lo) * smooth(K_LO, K_HI, kks)
    s_k = np.concatenate([[-1.3 * L], sl, [1.3 * L]]).astype(np.float32)
    hw_k = np.concatenate([[hw_s[0]], hw_s, [hw_s[-1]]]).astype(np.float32)
    plan = SeamPlan(L, a, s_k, hw_k, beta=beta)
    # budgets: scale the half width down so that (a) the mixed share (0.02 < w < 0.98, inside the lens) is at most the mix budget (D13, about 3 percent) and
    # (b) the support of the blend (0 < w < 1, the pixels that differ from the pure irises at all) is at most the support budget; largest scale that holds both
    share = mixed_share(plan, d)
    supp = support_share(plan, d)
    scale = 1.0
    if share > mix_budget or supp > support_budget:
        lo_, hi_ = 0.2, 1.0
        for _ in range(30):
            mid = 0.5 * (lo_ + hi_)
            plan.hw_k = np.maximum(hw_k * mid, 0.5 * hw_lo).astype(np.float32)
            if mixed_share(plan, d) <= mix_budget and support_share(plan, d) <= support_budget:
                lo_ = mid
            else:
                hi_ = mid
        scale = lo_
        plan.hw_k = np.maximum(hw_k * scale, 0.5 * hw_lo).astype(np.float32)
        share = mixed_share(plan, d)
        supp = support_share(plan, d)
    plan.info = dict(kind=mode, L=L, tA=tA, tB=tB, K_mean=float(np.mean(kk)), K_chosen=float(k_ref[0]), K_shape=float(k_ref[1]), K_straight=float(k_ref[2]), hw_min=float(plan.hw_k.min()),
                     hw_max=float(plan.hw_k.max()), scale=scale, mixed_share=share, support_share=supp, coeffs=a, ext=float(Cc[best].max() - Cc[best].min()))
    return plan


def blend_w(tp, hw, beta):
    x = np.clip((tp + hw) / (2.0 * hw), 0.0, 1.0)
    return (1.0 - beta) * x * x * (3.0 - 2.0 * x) + beta * x


def mixed_share(plan, d, step=0.006):
    """Share of one iris's disc area that the blend mixes (0.02 < w < 0.98) inside the lens, on a fine grid in the lens frame (R^2 units over pi)."""
    L = max(1.0 - d / 2.0, 1e-3)
    s = np.arange(-L, L, step, dtype=np.float32) + step / 2
    t = np.arange(-0.5, 0.5, step, dtype=np.float32) + step / 2
    S, Tt = np.meshgrid(s, t)
    inside = (np.hypot(S + d / 2.0, Tt) <= 1.0) & (np.hypot(S - d / 2.0, Tt) <= 1.0)
    Cc, hw = plan.eval(S)
    w = blend_w(Tt - Cc, hw, plan.beta)
    mixed = inside & (w > 0.02) & (w < 0.98)
    return float(mixed.sum()) * step * step / math.pi


def support_share(plan, d, step=0.006):
    """Share of one iris's disc area on which the blend is neither exactly 0 nor exactly 1 (0 < w < 1) inside the lens: the support of the crossfade. The pixels outside it are
    pure pixels of one iris (what the T1 integrity test looks at)."""
    L = max(1.0 - d / 2.0, 1e-3)
    s = np.arange(-L, L, step, dtype=np.float32) + step / 2
    t = np.arange(-0.5, 0.5, step, dtype=np.float32) + step / 2
    S, Tt = np.meshgrid(s, t)
    inside = (np.hypot(S + d / 2.0, Tt) <= 1.0) & (np.hypot(S - d / 2.0, Tt) <= 1.0)
    Cc, hw = plan.eval(S)
    sup = inside & (np.abs(Tt - Cc) < hw)
    return float(sup.sum()) * step * step / math.pi
