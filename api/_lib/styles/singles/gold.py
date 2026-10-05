# -*- coding: utf-8 -*-
"""cg_a: CELESTIAL GOLD V2, design A "EVEN CORONA" (ported from the scratch prototype of the design round wave-cg2).

Drop-in for designs.singles_gold.fx_gold:  fx_gold_a(cv, ctx)  (same signature, same ctx, same kit and fx core, numpy + PIL only).

The idea of the brief is kept (navy sky, a black eclipse gap, a golden corona made of the eye's own rim, a hairline gold orbit, stars and dust),
but the light is one rotationally even halo, like an eclipse corona seen evenly all round the eye:
  * the corona is a function of the RADIUS only: one amplitude, one e-fold length, ONE gold colour per eye (the circular median of the rim band,
    warmed toward gold by the gild factor), the ramp position fixed by the radius. The rim luminance no longer drives amplitude or length.
  * fine organic ray texture, built ONLY from angular harmonics of 72 and above (wavelengths shorter than one 5 degree sector), so it adds a hair
    of variance to the sector means but no wedge. The texture modulates brightness (and the ray length a little), never the colour.
  * the eclipse gap has a constant width, the hairline orbit is a concentric circle with constant alpha, the glint and the lower right bokeh
    discs are gone (an optional pair of tiny opposite sparkles is off by default).
  * stars and dust stay (stars beyond 1.5 R, gold dust 1.30 to 2.20 R, 40 % near the orbit): they are sparse and move the sector means by 0.
Hard rules kept: the corona is sampled FROM the iris and never drawn over it, nothing touches the pixels inside the disc (the kit pastes the iris
last), seeds from sha256 (ctx.rand), sizes in R and S units so 1024 == 4096, nothing is written on the artwork.
"""
from __future__ import annotations

# PORT of work package WP5A (step A): cg_a.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists
# (imports; the approved variant A (wave-cg2/A/cg_a.py), its effect is named fx_gold); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np

from .. import core as C
from .. import matter as M
from . import kit as K

TWO_PI = 2.0 * math.pi
F32 = np.float32
GILD = {"own": 0.55, "dark_brown": 0.85, "grey": 0.65}          # as the live design
RAMP = ("#3A2408", "#8C5A1C", "#D9A441", "#F6E3B0")
GP = {
    "gap": 0.034,                  # constant eclipse gap width (R), not tied to anything
    "gain": 1.2,                   # radial amplitude of the corona at its inner edge (before the soft clip)
    "split": 0.45,                 # share of the amplitude in the short inner exponential
    "L1": 0.028, "L2": 0.105,      # the two e-fold lengths (R): a bright close fringe and a soft outer glow
    "fade_out": (1.42, 0.18),      # the corona is zero from 1.42 R, full strength below 1.24 R
    "soft_clip": 1.6,
    "bands": ((126, 162, 1.0), (198, 234, 0.75), (270, 306, 0.3), (90, 330, 1.2)),     # texture harmonics (cycles per revolution) and weights: rays 2.9 to 1.2 degrees wide,
                                                                       # all far above 72 and each band sits around a multiple of 72, where a 5 degree sector
                                                                       # mean cancels the most (measured on shifted sector grids too)
    "s_amp": 0.58,                 # texture depth on the brightness: light x (1 + s n), n unit std
    "s_len": 0.12,                 # texture depth on the ray length
    "taper": (0.25, 0.09),         # the ray contrast falls from 1 at the gap to this share over this many R: rays near the limb, a soft glow further out
    "morph": 0.9,                  # the ray pattern drifts along the radius by this many radians per R (two independent noises crossfaded)
    "floor": 0.25, "floor_soft": 0.025,   # lower bound of the ray brightness factor, and the softness of the smooth max that applies it
    "rim_amp": 0.70,
    "bloom": 0.05,
    "orbit": {"r": 1.39, "alpha": 0.40, "stroke": 0.0012, "col": "#E8C27A"},
    "warm": 0.45,                  # the eye colour of the corona is warmed this far toward gold
    "stars": (120, 180), "dust": (150, 300),
    "pair": False,                 # an optional pair of tiny opposite sparkles on the orbit
    "tex_src": "noise",
}


# ----------------------------------------------------------------------------- helpers
def gold_ramp(t):
    """(..., 3) gold gradient map of t in 0..1: #3A2408 > #8C5A1C > #D9A441 > #F6E3B0."""
    cols = np.stack([C.rgb01(c) for c in RAMP])
    t = np.clip(t, 0.0, 1.0) * (len(cols) - 1)
    i = np.minimum(np.asarray(t).astype(np.int32), len(cols) - 2)
    f = (t - i)[..., None]
    return (cols[i] * (1 - f) + cols[i + 1] * f).astype(np.float32)


def band_noise(n, rnd, k_lo, k_hi, edge=0.12):
    """Seeded periodic noise of n samples, unit std, with power only in the harmonics k_lo..k_hi (raised cosine edges of `edge` x band width)."""
    z = rnd.normal(n)
    F = np.fft.rfft(z)
    k = np.arange(len(F), dtype=np.float64)
    w_ = max(2.0, edge * (k_hi - k_lo))
    up = np.clip((k - (k_lo - w_ / 2)) / w_, 0, 1)
    dn = np.clip(((k_hi + w_ / 2) - k) / w_, 0, 1)
    win = (0.5 - 0.5 * np.cos(np.pi * up)) * (0.5 - 0.5 * np.cos(np.pi * dn))
    y = np.fft.irfft(F * win, n)
    return (y / max(float(y.std()), 1e-9)).astype(np.float32)


def band_pass(a, k_lo, k_hi, edge=0.12):
    """Circular band pass of a periodic 1-D signal (harmonics k_lo..k_hi), returns the filtered signal."""
    n = len(a)
    F = np.fft.rfft(a - a.mean())
    k = np.arange(len(F), dtype=np.float64)
    w_ = max(2.0, edge * (k_hi - k_lo))
    up = np.clip((k - (k_lo - w_ / 2)) / w_, 0, 1)
    dn = np.clip(((k_hi + w_ / 2) - k) / w_, 0, 1)
    win = (0.5 - 0.5 * np.cos(np.pi * up)) * (0.5 - 0.5 * np.cos(np.pi * dn))
    return np.fft.irfft(F * win, n)


def flatten_log(n, s, win, iters=3):
    """Remove from the texture n (unit std, log-normal depth s: e = exp(s n)) every slow swell of the light: n is corrected by the log of its own running mean
    over `win` samples (one 5 degree sector) so that the mean of e over ANY window of that width is 1 (the texture keeps its fine structure and loses
    its clumps). Circular, deterministic, a few FFT passes."""
    N = len(n)
    kern = np.zeros(N)
    kern[:win] = 1.0 / win
    kern = np.roll(kern, -(win // 2))
    Fk = np.fft.rfft(kern)
    x = n.astype(np.float64).copy()
    for _ in range(iters):
        e = np.exp(s * x)
        mean = np.fft.irfft(np.fft.rfft(e) * Fk, N)
        x = x - np.log(mean) / s
    return x.astype(np.float32)


def circ_window_mean(a, width):
    """Circular running mean of a 1-D periodic signal over `width` samples (cosine window)."""
    n = len(a)
    kk = 0.5 * (1.0 + np.cos(np.linspace(-math.pi, math.pi, 2 * int(width) + 1)))
    kk = kk / kk.sum()
    kern = np.zeros(n)
    kern[:len(kk)] = kk
    kern = np.roll(kern, -int(width))
    return np.real(np.fft.ifft(np.fft.fft(a) * np.fft.fft(kern)))


def _radial_colour_lut(opts, g, own, n=4096, umax=1.25):
    """(n, 3) light colour of a ray as a function of u = (rho - c0) / length modulation: one gold colour per eye, the ramp position set by the
    radius (through the radial profile), never by the angle. Also returns the profile itself (n,)."""
    u = np.linspace(0.0, umax, n)
    Ib = opts["gain"] * (opts["split"] * np.exp(-u / opts["L1"]) + (1.0 - opts["split"]) * np.exp(-u / opts["L2"]))
    if opts["soft_clip"]:
        over = np.maximum(Ib - 0.6, 0.0)
        Ib = np.minimum(Ib, 0.6) + 0.45 * (1.0 - np.exp(-over / 0.45))
    Ib = Ib.astype(np.float32)
    gold = gold_ramp(np.minimum(Ib * 1.05, 1.0))
    col = own[None, :] * (Ib * F32(1.0 - g) * F32(1.15))[:, None] + gold * (F32(g) * np.minimum(Ib * 2.2, 1.0))[:, None]
    return col.astype(np.float32), Ib


# ----------------------------------------------------------------------------- the effect
def fx_gold(cv, ctx):
    opts = dict(GP)
    opts.update(ctx.opts.get("gold", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    g = GILD.get(iris.cls, 0.55)
    if iris.cls == "own" and 170.0 <= iris.stats["h"] <= 280.0:
        g = max(g, 0.65)
    rnd = ctx.rand("gold_a")
    # ---- navy gradient (as the live design)
    K.fill_radial_bg(cv, d.cx, d.cy, 0.95 * max(W, H), "#0B0D14", "#040507", power=0.9)
    # ---- the eye: the rim band 0.86-0.98 R, sampled at NA angles. Its circular MEDIAN colour is the one colour of the corona (warmed by the gild factor);
    # its fine structure (band passed, evenly normalised) can be the source of the ray texture. Nothing else of the rim reaches the corona.
    NA, NRS = 4096, 24
    ths = (np.arange(NA) + 0.5) * (TWO_PI / NA)
    rhos = np.linspace(0.86, 0.98, NRS)
    P = K.sample_disc(d, rhos[None, :] * np.ones((NA, 1)), ths[:, None] * np.ones((1, NRS)))        # (NA, NRS, 3)
    Pm = P.mean(axis=1)
    med = np.median(Pm, axis=0).astype(np.float32)                                                  # one colour per eye
    own = C.boost(med * 1.15, 1.3, 1.3)
    gm = gold_ramp(np.float32(0.62))
    own = C.mix(own, gm * (float(own.mean()) / max(float(gm.mean()), 1e-6)), float(opts["warm"]))
    # ---- the texture (angular only, harmonics tex_lo..tex_hi), unit std
    def tex_noise():
        a_ = 0
        for lo, hi, w in opts["bands"]:
            a_ = a_ + float(w) * band_noise(NA, rnd, lo, hi)
        return (a_ / max(float(np.std(a_)), 1e-9)).astype(np.float32)
    n1 = tex_noise()
    n2 = tex_noise()
    if opts["tex_src"] == "rim":
        lum = Pm @ np.array([0.299, 0.587, 0.114], np.float32)
        bp = band_pass(lum.astype(np.float64), 126, 306)
        env = np.sqrt(circ_window_mean(bp * bp, NA / 360.0 * 30.0) + 0.15 * float(np.mean(bp * bp)))
        r1 = band_pass(bp / env, 126, 306)
        r1 = (r1 / max(float(r1.std()), 1e-9)).astype(np.float32)
        n1 = (0.80 * r1 + 0.60 * n1).astype(np.float32)
        n1 /= max(float(n1.std()), 1e-9)
    # ---- radial profile -> colour lookup (function of the radius only)
    c0 = 1.0 + float(opts["gap"])
    col_lut, Ib = _radial_colour_lut(opts, g, own)
    NL = len(Ib)
    umax = 1.25
    lutA, lutB = np.ascontiguousarray(n1), np.ascontiguousarray(n2)
    # the radial extras: the thin bright inner edge (the eclipse "diamond ring", even) and a faint diffuse bloom, colour from the radius only
    gold_bloom = gold_ramp(np.float32(0.75))
    s_a, s_l = float(opts["s_amp"]), float(opts["s_len"])
    tap0, tapL = float(opts["taper"][0]), float(opts["taper"][1])
    morph = float(opts["morph"])
    fl, fl_soft = float(opts["floor"]), float(opts["floor_soft"])
    reach = 1.56 * R
    x0, y0 = max(0, int(d.cx - reach)), max(0, int(d.cy - reach))
    x1, y1 = min(W, int(d.cx + reach) + 2), min(H, int(d.cy + reach) + 2)
    fo_hi, fo_w = opts["fade_out"]
    for r0 in range(y0, y1, 128):
        r1 = min(y1, r0 + 128)
        rho, th = C.polar(W, H, d.cx, d.cy, R, 1.0, (x0, r0, x1, r1))
        m = (rho >= c0 - 0.03) & (rho < 1.56)
        if not m.any():
            continue
        rh = rho[m]
        x = rh - F32(c0)
        tf = (th[m] % TWO_PI) * (NA / TWO_PI) - 0.5
        ti = np.floor(tf).astype(np.int32)
        tw = (tf - ti).astype(np.float32)
        i0, i1 = ti % NA, (ti + 1) % NA
        na = lutA[i0] * (1 - tw) + lutA[i1] * tw
        if morph > 0:
            nb = lutB[i0] * (1 - tw) + lutB[i1] * tw
            ph = morph * (rh - 1.0)
            ne = na * np.cos(ph).astype(np.float32) + nb * np.sin(ph).astype(np.float32)
        else:
            ne = na
        tp = F32(tap0) + F32(1.0 - tap0) * np.exp(-np.maximum(x, 0.0) * F32(1.0 / tapL)) if tap0 < 1.0 else 1.0
        m0 = F32(1.0) + F32(s_a) * ne * tp
        if fl_soft > 0:
            ma = F32(0.5) * (m0 + F32(fl) + np.sqrt((m0 - F32(fl)) ** 2 + F32(fl_soft)))     # smooth max(m0, fl): no hard black ticks
        else:
            ma = np.maximum(m0, F32(fl))
        lm = np.maximum(F32(1.0) + F32(s_l) * ne, F32(0.45))
        u = np.maximum(x, 0.0) / lm
        f = np.clip(u * F32((NL - 1) / umax), 0.0, NL - 1.001)
        fi = f.astype(np.int32)
        ff = (f - fi)[:, None]
        colr = col_lut[fi] * (1 - ff) + col_lut[fi + 1] * ff
        onset = C.smoothstep((x + 0.010) / 0.014)
        outer = C.smoothstep((fo_hi - rh) / fo_w)
        cor_v = colr * (ma * onset * outer)[:, None]
        # the inner edge line and the diffuse bloom: radial only
        rim = np.exp(-0.5 * ((rh - (c0 + 0.002)) / 0.0045) ** 2) * F32(opts["rim_amp"])
        Ibm = gold_ramp(np.minimum(rim * 1.4, 1.0))
        cor_v += rim[:, None] * (Ibm * F32(0.55 + 0.35 * g) + own[None, :] * F32(0.45 * (1.0 - g)))
        bl = np.exp(-np.maximum(x, 0.0) / 0.22) * F32(opts["bloom"]) * C.smoothstep((x + 0.02) / 0.04) * outer
        cor_v += bl[:, None] * gold_bloom[None, :]
        cor = np.zeros((r1 - r0, x1 - x0, 3), np.float32)
        cor[m] = cor_v
        K.wall_fade(cor, ctx, y0=r0)
        K.text_fade(cor, ctx, y0=r0, x0=x0)
        cv[r0:r1, x0:x1] += cor
    # ---- stars, dust (as the live design), the concentric orbit
    rs = ctx.rand("stars")
    ns = int(opts["stars"][0] + (opts["stars"][1] - opts["stars"][0]) * float(rs.uniform()))
    sx, sy = rs.uniform(ns) * W, rs.uniform(ns) * H
    keep = np.hypot(sx - d.cx, sy - d.cy) > 1.5 * R
    sa = 0.06 + 0.19 * rs.uniform(ns) ** 2.0
    sz = (0.0004 + 0.0006 * rs.uniform(ns)) * S
    cool = C.mix(C.rgb01("#D9E2FF")[None, :], C.rgb01("#FFF4E4")[None, :], rs.uniform(ns)[:, None])
    layer = M.ParticleLayer()
    layer.splat(sx[keep], sy[keep], sz[keep], cool[keep], sa[keep], min_sigma=0.5)
    o = opts["orbit"]
    ro = o["r"] * R

    def orbit_pt(t):
        return d.cx + ro * np.cos(t), d.cy + ro * np.sin(t)

    rd = ctx.rand("dust")
    nd = int(opts["dust"][0] + (opts["dust"][1] - opts["dust"][0]) * float(rd.uniform()))
    n_orb = int(round(0.4 * nd))
    t_ = rd.uniform(n_orb) * TWO_PI
    ox, oy = orbit_pt(t_)
    off = rd.normal(n_orb, 0.0, 0.045) * R
    nrm = np.hypot(ox - d.cx, oy - d.cy)
    ox, oy = ox + (ox - d.cx) / nrm * off, oy + (oy - d.cy) / nrm * off
    r_ = 1.30 + (2.20 - 1.30) * rd.uniform(nd - n_orb) ** 0.8
    a_ = rd.uniform(nd - n_orb) * TWO_PI
    dx = np.concatenate([ox, d.cx + r_ * R * np.cos(a_)])
    dy = np.concatenate([oy, d.cy + r_ * R * np.sin(a_)])
    lv = rd.uniform(nd)
    dcol = gold_ramp(0.55 + 0.45 * lv)
    dsz = (0.0004 + 0.0010 * rd.uniform(nd) ** 2.0) * S
    dam = 0.25 + 0.75 * rd.uniform(nd) ** 2.2
    far = np.hypot(dx - d.cx, dy - d.cy) > 1.28 * R
    layer.splat(dx[far], dy[far], dsz[far], dcol[far], dam[far] * 0.9, min_sigma=0.5)
    # hairline orbit: a centred circle, constant alpha all round
    n_pts = int(2 * math.pi * o["r"] * R / 0.4)
    tt = (np.arange(n_pts) + 0.5) / n_pts * TWO_PI
    px, py = orbit_pt(tt)
    sig = o["stroke"] * S * 0.5
    sp = 0.4
    amp_pt = float(o["alpha"]) * sp / (math.sqrt(2 * math.pi) * max(sig, 0.5))
    layer.splat(px, py, sig, C.rgb01(o["col"]), amp_pt * 1.8, min_sigma=0.5)
    layer.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0)))
    del layer
    # ---- optional: ONE pair of tiny opposite sparkles on the orbit (equal, symmetric), off by default
    if opts["pair"]:
        th0 = math.radians(25.0 + 10.0 * float(rnd.uniform()))
        hot = C.rgb01("#FFF2D4")
        for k_ in range(2):
            gx, gy = orbit_pt(np.array([th0 + k_ * math.pi]))
            gw = int(0.12 * R)
            wx0, wy0 = max(0, int(gx[0]) - gw), max(0, int(gy[0]) - gw)
            wx1, wy1 = min(W, int(gx[0]) + gw + 1), min(H, int(gy[0]) + gw + 1)
            lay2 = np.zeros((wy1 - wy0, wx1 - wx0, 3), np.float32)
            lx, ly = gx - wx0, gy - wy0
            C.sparkles(lay2, lx, ly, 0.06 * R, hot, 0.35, width=0.0030 * R, angle=math.radians(45.0), core=0.0)
            C.splat(lay2, lx, ly, 0.0036 * S, hot, 0.45, min_sigma=0.6)
            K.wall_fade(lay2, ctx, y0=wy0)
            C.screen(cv[wy0:wy1, wx0:wx1], lay2)
    # ---- the black gap (eclipse): constant width, multiply 0.05 from the limb to 1 + gap, soft outer edge, drawn before the iris paste
    x0, y0 = max(0, int(d.cx - 1.12 * R)), max(0, int(d.cy - 1.12 * R))
    x1, y1 = min(W, int(d.cx + 1.12 * R) + 2), min(H, int(d.cy + 1.12 * R) + 2)
    rho, th = C.polar(W, H, d.cx, d.cy, R, 1.0, (x0, y0, x1, y1))
    gw_ = float(opts["gap"])
    gap = 1.0 - 0.95 * (C.smoothstep((rho - 0.985) / 0.02) * (1.0 - C.smoothstep((rho - (1.0 + gw_ - 0.01)) / 0.02)))
    cv[y0:y1, x0:x1] *= gap[..., None].astype(np.float32)
    ctx.log["gold"] = {"gild": g, "class": iris.cls, "design": "A even corona", "gap": gw_, "gap_min": gw_, "gap_max": gw_,
                       "own_rgb": [float(v) for v in own], "orbit_r": o["r"], "tex_src": opts["tex_src"]}
