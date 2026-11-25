# -*- coding: utf-8 -*-
"""The Lens look of Universe (2026-11-25, the owner chose the direction and its variant A, with a black pupil and no highlight): ONE look for one eye, in the genre of
a macro photograph. The customer's iris is the sharp disc in the middle; behind it the SAME iris, magnified about twice and softly out of focus, falls to
black towards the corners, with a soft dark ring between the two; the pupil is a deep matte black, smaller when the photo's was wide.

  the disc        the studio grade of the restored iris WITHOUT the iris finish (core.FIN: its vibrance pushes a blue green eye to cyan, its micro contrast
                  reads over processed at this size), with a gentle local contrast on luminance only (the hue and the colour ratios are the eye's own), a
                  soft dark limbal falloff and a soft round edge
  the pupil       a deep matte black disc on the remapped pupil (no highlight, no sheen: the owner), with a faint shadow on the iris round it
  the remap       a rubber sheet from the measured pupil edge to the limbus: when the photographed pupil is wider than PUPIL_TARGET of the iris (a phone in
                  dim light), the ring is remapped radially so that the customer's own texture reaches in to a pupil of that size, as a real iris does in
                  bright light (smooth and monotone, a little more stretch near the pupil; nothing synthesised: every pixel is sampled from the iris). The
                  inner edge is a smooth closed curve fitted to the engine's own pupil measurement (pupil.analyse), so a ragged or off-centre pupil of a
                  restoration never leaves a lumpy inner ring, and the remapped pupil is round and centred
  the background  the same remapped iris, magnified MAG times about the disc's centre, defocused by a disc (lens) kernel whose radius grows with the
                  distance from the disc, darkened, a little less saturated, vignetted to black at the corners, with a soft dark ring hugging the disc
  the lids        an eyelid, lash line or skin inside the disc is found per degree by the fill gate's own measurement (gate.fill_features: the median colour
                  of the band 0.80-0.96 R per degree against the median degree, more than dE 18), traced inward, and filled from the customer's own
                  neighbouring iris angles (a mirror walk over the clean degrees on both sides, crossfaded in the middle): ALWAYS in the background (a lid
                  is never magnified behind the disc), in the disc only when it is small (LID_DISC_MAX_DEG, LID_DISC_MAX_DEPTH); a larger one stays in the
                  disc as photographed, and the picker does not recommend the look for that eye (catalogue.lid_heavy)

The family rule "the iris is pasted last, byte for byte" holds in its form (the disc below is pasted last by core.paste_iris_last, and the self check T1 holds
it to the pixel), but the disc is this look's own drawing of the iris, not the graded iris: the exception the coordinator signed off for this look on
2026-11-25 (the owner approved the picture that needs it), recorded in api/_lib/styles/universe/__init__.py and core.py where the rule is written.

Every length is in units of the disc's R or of the canvas's short side S, so a 4096 px master is the 1024 px preview drawn finer: the background is worked
on a grid of at most BG_GRID px on the long side (the same grid for the preview and the master), the disc at the canvas's own resolution. numpy and PIL only.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from .common import C, L, smooth
from .. import pupil as PUP

NAME = "lens"
SOLO_R = 0.32                 # the disc's radius as a share of the short side (the references: a disc of 0.62 to 0.68 S)
MAG = 2.1                     # the background iris against the disc (the owner's variant A: about 2x)
BLUR_IN = 0.0035              # lens blur radius just outside the disc, share of S ...
BLUR_OUT = 0.016              # ... and at the corners (variant A: light enough that crypts and fibres stay readable)
BLUR_LEVELS = 6               # the radii the spatially varying blur is blended from
BG_GAIN = 0.50                # the background's brightness against the disc's own pixels
BG_DESAT = 0.15               # a little less colour behind than in front
BG_REF = 0.32                 # a disc whose body is darker than this (mean luminance) gets its background lifted ...
BG_LIFT_MAX = 1.7             # ... by at most this (a dark brown eye would leave the background almost black)
VIG_START = 0.38              # vignette: from this share of the half diagonal ...
VIG_POWER = 1.6               # ... to black at the corners
HALO = 0.88                   # depth of the dark ring round the disc
HALO_W = 0.14                 # its width, share of R
LIMB = 0.48                   # the disc's limbal falloff: this much darker at the edge ...
LIMB_FROM = 0.80              # ... from this share of R
EDGE = 0.025                  # the disc's soft edge, share of R (a little softer than the prototype's 0.018: the owner's note)
MICRO = ((0.0045, 0.35), (0.020, 0.22))      # luminance-only local contrast: (sigma in R, amount)
DEHAZE = 0.25                 # share of the veil (the 6th percentile of the body's luminance) taken away
PUPIL_TARGET = 0.30           # the remapped pupil's radius, share of R (= of the diameter)
REMAP_BIAS = 0.30             # 0: a uniform radial stretch; more: more stretch near the pupil, the outer ring almost untouched
PUPIL_BLACK = 0.004           # the pupil's level (display 0..1): deep matte black, the dither keeps it from banding
PUPIL_SHADOW = 0.30           # the faint shadow on the iris right round the pupil ...
PUPIL_SHADOW_W = 0.05         # ... its width, share of R
PUPIL_FOURIER = 6             # the inner edge: a closed curve of this many harmonics fitted to the measured pupil edge
BG_GRID = 512                 # the background's working grid, px on the long side: the same grid for a 512 px tile, the 1024 px preview and the 4096 px master
BG_SRC = 512                  # the graded frame the background and the lid measurement are sampled from (the magnified iris is 1.4 of its pixels on the grid)
LID_DE = 18.0                 # the fill gate's per degree threshold (gate.fill_features: dE in Lab of the band 0.80-0.96 R from the median degree)
LID_TRACE_DE = 14.0           # a lid degree is traced inward while its colour is this far from the iris's own colour at that radius
LID_EDGE = 19.0               # the margin detector: an L* drop outward over 0.06 R this much stronger than the iris's sides have at that radius ...
LID_EDGE_RUN = 40             # ... along at least this many degrees of a lid's arc, at a radius that moves smoothly (2026-11-25, on the 512 px grade of the 16
                              # restorations of the boards: 18 / 35 also took the lower collarette of the grey green eye; 19 / 40 only the three lidded eyes. A
                              # thin margin on a small set: a first calibration, to be checked on the owner's labels as the gate's were)
LID_MIN_RUN = 4               # degrees: a shorter run is a crypt or a fleck, not a lid
LID_MERGE = 3                 # degrees: runs this close are one lid
LID_MARGIN_DEG = 3            # every lid run grows by this on both sides ...
LID_MARGIN_RHO = 0.04         # ... and this much deeper (a lash tip, the lid's own shadow)
LID_ARCS = ((-90.0, 75.0), (90.0, 60.0))     # (centre, half width) in screen degrees, y down: the upper and the lower lid; a run centred elsewhere is the iris's own
LID_DISC_MAX_DEG = 50         # the disc is filled when every lid run is at most this wide ...
LID_DISC_MAX_DEPTH = 0.30     # ... and reaches at most this deep from the limbus (share of R); else the disc keeps it as photographed
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


# ----------------------------------------------------------------------------- sampling
def _bicubic_w(t):
    """Keys (a = -0.5) weights of the four taps for fractional offsets t."""
    t = t.astype(np.float32)
    t2, t3 = t * t, t * t * t
    return (-0.5 * t3 + t2 - 0.5 * t, 1.5 * t3 - 2.5 * t2 + 1.0, -1.5 * t3 + 2.0 * t2 + 0.5 * t, 0.5 * t3 - 0.5 * t2)


def sample(img, x, y, cubic=True):
    """img (H, W, 3) uint8 or float32 sampled at continuous array coordinates (x, y: pixel centres at integers), edges clamped. Bicubic (Keys) or bilinear."""
    H, W = img.shape[:2]
    x = np.asarray(x, np.float32)
    y = np.asarray(y, np.float32)
    x0 = np.floor(x)
    y0 = np.floor(y)
    fx, fy = x - x0, y - y0
    x0 = x0.astype(np.int64)
    y0 = y0.astype(np.int64)
    out = np.zeros(x.shape + (3,), np.float32)
    if not cubic:
        for dy, wy in ((0, 1 - fy), (1, fy)):
            yy = np.clip(y0 + dy, 0, H - 1)
            for dx, wx in ((0, 1 - fx), (1, fx)):
                xx = np.clip(x0 + dx, 0, W - 1)
                out += img[yy, xx].astype(np.float32) * (wy * wx)[..., None]
        return out
    wxs, wys = _bicubic_w(fx), _bicubic_w(fy)
    for j in range(4):
        yy = np.clip(y0 + (j - 1), 0, H - 1)
        row = np.zeros(x.shape + (3,), np.float32)
        for i in range(4):
            xx = np.clip(x0 + (i - 1), 0, W - 1)
            row += img[yy, xx].astype(np.float32) * wxs[i][..., None]
        out += row * wys[j][..., None]
    return out


# ----------------------------------------------------------------------------- the pupil's inner edge
def _circ_median(v, k):
    n = len(v)
    p = k // 2
    pad = np.concatenate([v[-p:], v, v[:p]])
    return np.median(np.stack([pad[i:i + n] for i in range(k)], 0), 0)


def pupil_envelope(pu, sq, reach=0.75, gap=0.07):
    """The measured edge widened to the pupil-black blobs that hang on it (a restoration can leave the pupil ragged: black islands just outside its round edge,
    separated by a thin bright gap): along each ray of pupil.analyse, from its edge outward, the last radius that is as dark as the pupil (its own threshold) before
    a bright stretch longer than `gap` R, up to `reach` R. sq: the tight canonical grade pupil.analyse read. An edge with no such blob is returned as it was."""
    rt = np.asarray(pu["r_theta"], np.float64)
    if not pu.get("found"):
        return rt
    t = sq.shape[0]
    R = t / 2.0
    lum = sq.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    n = len(rt)
    ang = (np.arange(n) + 0.5) * (2 * math.pi / n)
    steps = np.arange(0.0, reach, 0.5 / R)
    cx, cy = R + pu["cx"] * R, R + pu["cy"] * R
    X = np.clip(cx + np.outer(np.cos(ang), steps) * R - 0.5, 0, t - 1)
    Y = np.clip(cy + np.outer(np.sin(ang), steps) * R - 0.5, 0, t - 1)
    prof = lum[np.rint(Y).astype(np.int64), np.rint(X).astype(np.int64)]       # (n, steps)
    dark = prof < min(0.6 * float(pu.get("thr", 30.0)), 18.0)                 # as black as a pupil (a restoration's blob), not a dark crypt or ruff
    out = rt.copy()
    g = int(round(gap / (0.5 / R)))
    for i in range(n):
        k = int(np.searchsorted(steps, rt[i]))
        last, run = rt[i], 0
        while k < len(steps):
            if dark[i, k]:
                last, run = steps[k], 0
            else:
                run += 1
                if run > g:
                    break
            k += 1
        out[i] = max(rt[i], last)
    return out


def pupil_curve(pu, sq=None, k=PUPIL_FOURIER):
    """The inner edge as a smooth closed curve: pupil.analyse's edge per angle (from its centroid, share of R), widened to the black blobs that hang on it
    (pupil_envelope, when the grade is given: a ragged pupil's islands go into the pupil, not into the iris ring) and spread over 12 degrees, a circular median
    of 9 against a spike, then the first k harmonics of a least squares Fourier fit, never inside the measured edge, clipped to 0.06 .. 0.80 R. Returns (cx, cy,
    coefficients (a0, a1, b1, ...), rp: the area radius)."""
    rt = np.asarray(pu["r_theta"], np.float64)
    n = len(rt)
    ang = (np.arange(n) + 0.5) * (2 * math.pi / n)
    if sq is not None:
        env = pupil_envelope(pu, sq)
        ext = env - rt
        isle = np.zeros(n, bool)
        for s, m in _runs(ext > 0.03):
            if m >= 5:                                                         # an island of pupil black at least 10 degrees wide (a black crypt is narrower)
                isle[[(s + j) % n for j in range(m)]] = True
        ragged = bool(isle.any() and float(np.mean(isle)) < 0.5)              # islands on part of the edge (all round it is the pupil's own soft edge)
        if ragged:
            env = np.where(isle, env, rt)
            env = np.maximum.reduce([np.roll(env, j) for j in range(-9, 10)])
            rt = np.maximum(rt, env)
    else:
        ragged = False
    r = _circ_median(rt, 9)
    cols = [np.ones(n)]
    for h in range(1, k + 1):
        cols += [np.cos(h * ang), np.sin(h * ang)]
    A = np.stack(cols, 1)
    coef, *_ = np.linalg.lstsq(A, r, rcond=None)
    under = float(np.max(r - A @ coef))
    if under > 0:
        coef[0] += min(under, 0.10 if ragged else 0.03)      # the curve does not cut into what was measured as pupil (no black left in the ring)
    fit = np.clip(A @ coef, 0.06, 0.80)
    rp = math.sqrt(float(np.mean(fit ** 2)))
    return float(pu["cx"]), float(pu["cy"]), coef.astype(np.float64), rp


def curve_at(coef, th):
    """The fitted edge (share of R) at screen angles th."""
    out = np.full(np.shape(th), coef[0], np.float32)
    k = (len(coef) - 1) // 2
    for h in range(1, k + 1):
        out += np.float32(coef[2 * h - 1]) * np.cos(h * th) + np.float32(coef[2 * h]) * np.sin(h * th)
    return np.clip(out, 0.06, 0.80)


# ----------------------------------------------------------------------------- the lids
def _circ_mean(a, k):
    """Moving mean of k (odd) degrees round the circle, along axis 0."""
    p = k // 2
    c = np.cumsum(np.concatenate([np.zeros((1,) + a.shape[1:]), a[-p:], a, a[:p]], 0), 0)
    return (c[k:] - c[:-k]) / k


def _runs(flag):
    """[(start, length)] of the circular runs of True (a run may wrap past 359)."""
    n = len(flag)
    if flag.all():
        return [(0, n)]
    if not flag.any():
        return []
    s = int(np.argmin(flag))                       # start the walk on a False
    out, i = [], 0
    while i < n:
        j = (s + i) % n
        if flag[j]:
            k = 0
            while k < n and flag[(j + k) % n]:
                k += 1
            out.append((j, k))
            i += k
        else:
            i += 1
    return out


def _in_arcs(deg):
    """Is the screen degree (0 at 3 o'clock, clockwise, y down) inside the upper or the lower lid's arc."""
    c = (np.asarray(deg, np.float64) + 180.0) % 360.0 - 180.0
    return np.any([np.abs((c - a + 180.0) % 360.0 - 180.0) <= hw for a, hw in LID_ARCS], axis=0)


def lid_map(sq):
    """The lids of a tight graded disc square (uint8 (t, t, 3), the grade without the iris finish): {inner: (360,) the radius (share of R) from which a degree is
    lid out to the limbus (1.0: no lid), runs: [(start degree, length)], max_run, max_depth, disc_fill (small enough to fill in the disc too)}.
    The measurement is the gates' (gate.fill_features and gate.lid: the colour and the L* of a degree's band at the limbus against the iris's own), with the
    reference taken where a lid never sits (iris.LOCK_SIDES: the two side sectors, -40..40 and 140..220 degrees; a lid covering a third of the ring moves the median
    degree the fill gate compares with): a degree of the upper or the lower arc is lid when its outer band (0.84-0.98 R) is more than LID_DE (Lab) from the sides'
    colour at the same radius and the difference is anchored at the limbus (the outer band differs more than the iris at 0.50-0.62 R: a lid comes in from the
    rim, a sector of pigment runs to the pupil). Runs shorter than LID_MIN_RUN are crypts; each kept degree is traced inward."""
    t = sq.shape[0]
    R = t / 2.0
    rhos = np.linspace(0.42, 0.985, 58)
    th = (np.arange(360) + 0.5) * (2 * math.pi / 360.0)
    X = R + np.outer(rhos, np.cos(th)) * R - 0.5
    Y = R + np.outer(rhos, np.sin(th)) * R - 0.5
    lab = L.srgb_to_lab(sample(sq, X, Y, cubic=False))                         # (58, 360, 3)
    degs = np.arange(360)
    side = (degs < 40) | (degs >= 320) | ((degs >= 140) & (degs < 220))
    ref = np.median(lab[:, side], axis=1)                                      # the iris's own colour per ring, where no lid sits
    dev = np.sqrt(((lab - ref[:, None, :]) ** 2).sum(-1))                      # (58, 360)
    dev = _circ_mean(dev.T, 5).T
    dev = (np.r_[dev[:1], dev[:-1]] + dev + np.r_[dev[1:], dev[-1:]]) / 3.0
    side_dev = float(np.median(dev[:, side]))                                  # how much the iris itself varies (a busy iris is not a lid)
    outer = dev[(rhos > 0.84) & (rhos < 0.98)].mean(0)
    mid = dev[(rhos > 0.50) & (rhos < 0.62)].mean(0)
    arcs = _in_arcs(degs + 0.5)
    flag = (outer > LID_DE + side_dev) & (outer > mid + 6.0) & arcs
    # the second detector: a lid margin with its lash line is a hard edge INSIDE the iris (the fill gate's n_step: L* steps by more than 25 inside 0.04 R),
    # darker outward, at a radius that runs smoothly along the degrees (a crypt or a fleck is a step at a random radius), and the iris's sides do not have it
    Ls = _circ_mean(lab[..., 0].T, 5).T                                        # (58, 360)
    h = 3                                                                      # rings: 0.03 R each side
    step = Ls[:-2 * h] - Ls[2 * h:]                                            # inner minus outer: positive where it gets darker outward
    rs = rhos[h:-h]
    zone = (rs > 0.45) & (rs < 0.93)
    stz = np.where(zone[:, None], step, -1e9)
    k_e = np.argmax(stz, 0)
    s_e = stz[k_e, degs]
    r_e = rs[k_e]
    side_step = np.median(step[:, side], axis=1)                               # the same step on the iris's sides, per radius
    edge = (s_e > LID_EDGE + side_step[k_e]) & arcs
    for s, n in _runs(~edge):
        if n <= LID_MERGE:
            edge[[(s + k) % 360 for k in range(n)]] = True
    edge_inner = np.ones(360, np.float32)
    for s, n in _runs(edge):
        if n < LID_EDGE_RUN:
            continue
        idx = [(s + k) % 360 for k in range(n)]
        rr = r_e[idx]
        if np.mean(np.abs(np.diff(rr)) < 0.04) < 0.7:                          # the edge's radius jumps about: crypts, not one margin
            continue
        sm = _circ_mean(rr[:, None], 5)[:, 0] if n >= 5 else rr
        edge_inner[idx] = np.clip(sm - 0.02, 0.30, 1.0)
    for s, n in _runs(~flag):
        if n <= LID_MERGE and _in_arcs(s + n / 2.0):
            flag[[(s + k) % 360 for k in range(n)]] = True
    keep = np.zeros(360, bool)
    for s, n in _runs(flag):
        if n >= LID_MIN_RUN:
            keep[[(s + k) % 360 for k in range(n)]] = True
    inner = np.ones(360, np.float32)
    if not keep.any() and not (edge_inner < 0.999).any():
        return {"inner": inner, "runs": [], "max_run": 0, "max_depth": 0.0, "bg_inner": inner.copy(), "bg_runs": [], "disc_fill": True, "flag_deg": int(flag.sum())}
    for d in np.nonzero(keep)[0]:
        k = len(rhos) - 1
        gap = 0
        last = k
        while k >= 0:
            if dev[k, d] > LID_TRACE_DE + 0.5 * side_dev:
                last, gap = k, 0
            else:
                gap += 1
                if gap > 2:
                    break
            k -= 1
        inner[d] = rhos[last]
    inner = np.minimum(inner, edge_inner)
    keep = keep | (edge_inner < 0.999)
    # a lid is one smooth shape: the deepest of its neighbours, then a mean; grown by the margins
    grown = keep.copy()
    for s, n in _runs(keep):
        for k in range(-LID_MARGIN_DEG, n + LID_MARGIN_DEG):
            grown[(s + k) % 360] = True
    mn = np.minimum.reduce([np.roll(inner, k) for k in range(-4, 5)])
    inner = np.where(grown, np.clip(_circ_mean(mn[:, None], 5)[:, 0] - LID_MARGIN_RHO, 0.30, 1.0), 1.0).astype(np.float32)
    runs = _runs(grown)
    max_run = max(n for _, n in runs)
    max_depth = float(1.0 - inner.min())
    # the background takes the WHOLE arc of a lid that was found in it (a detector sees the lid's strongest part; the background is soft, so a generous fill
    # costs nothing there, and a lid must never be magnified behind the disc), as deep as the deepest part found, shallower over the arc's last 12 degrees
    bg_inner = np.ones(360, np.float32)
    for a, hw in LID_ARCS:
        d = (degs + 0.5 - (a % 360.0) + 180.0) % 360.0 - 180.0
        sel = np.abs(d) <= hw
        hit = sel & (inner < 0.999)
        if hit.any():
            depth = float(1.0 - inner[hit].min())
            taper = smooth((hw - np.abs(d)) / 12.0)
            bg_inner = np.where(sel, np.minimum(bg_inner, 1.0 - depth * taper), bg_inner).astype(np.float32)
    bg_inner = np.minimum(bg_inner, inner)
    return {"inner": inner, "runs": runs, "max_run": int(max_run), "max_depth": round(max_depth, 3), "bg_inner": bg_inner, "bg_runs": _runs(bg_inner < 0.999),
            "disc_fill": bool(max_run <= LID_DISC_MAX_DEG and max_depth <= LID_DISC_MAX_DEPTH), "flag_deg": int(flag.sum())}


def lid_donors(inner, runs):
    """For every degree (3600 tenths) the two donor angles (radians) and the crossfade weight of the second: a lid degree takes the iris of the clean degrees
    met by walking out of its run on each side, mirrored (the first clean degree past the edge for the degree at the edge, then on), so both halves of a lid
    are its own neighbours turned over; the two meet in the middle of the run with a crossfade. A clean degree is its own donor."""
    lid = inner < 0.999
    clean = np.nonzero(~lid)[0]
    n10 = 3600
    deg = (np.arange(n10) + 0.5) / 10.0
    dl = deg.copy()
    dr = deg.copy()
    w = np.zeros(n10, np.float32)
    if not lid.any() or len(clean) == 0:
        return np.radians(dl).astype(np.float32), np.radians(dr).astype(np.float32), w
    nc = len(clean)
    for s, n in runs:
        # the clean degree before the run and the one after it, by their index in `clean`
        before = (s - 1) % 360
        after = (s + n) % 360
        ib = int(np.searchsorted(clean, before)) % nc
        ia = int(np.searchsorted(clean, after)) % nc
        for k10 in range(n * 10):
            d10 = (s * 10 + k10) % n10
            u = (k10 + 0.5) / 10.0                                             # degrees into the run
            # mirror walk: u degrees into the run is u degrees out of it, over the clean degrees only (fractions kept)
            kb, fb = int(u), u - int(u)
            ka, fa = int(n - u), (n - u) - int(n - u)
            left = clean[(ib - kb) % nc] + 0.5 - fb
            right = clean[(ia + ka) % nc] + 0.5 + fa
            dl[d10] = left % 360.0
            dr[d10] = right % 360.0
            w[d10] = float(smooth((u / n - 0.35) / 0.30))                      # the left donors for the first part, the right for the last, crossfaded
    return np.radians(dl).astype(np.float32), np.radians(dr).astype(np.float32), w


# ----------------------------------------------------------------------------- the rubber sheet
class Sheet:
    """The map from the drawn iris (round centred pupil of radius p_out, share of R) to the restored one: (rho, theta) -> (X, Y) in units of the source disc's R
    from its centre. Lids: where lid (the per degree inner radius, 1.0 none) applies, the angle is taken from the donors."""

    def __init__(self, pu, lm=None, remap=True, target=PUPIL_TARGET, bias=REMAP_BIAS, sq=None):
        self.cx, self.cy, self.coef, self.p_meas = pupil_curve(pu, sq)
        self.found = bool(pu.get("found"))
        # a slit or a bar (an animal's) is drawn as photographed: no rubber sheet (it would make it round), the pupil black follows its own curve
        self.round = pu.get("cls", "round") == "round"
        self.p_out = min(self.p_meas, target) if (remap and self.found and self.round) else self.p_meas
        self.bias = float(bias) if (remap and self.found and self.round and self.p_meas > self.p_out + 1e-3) else 0.0
        self.lids = {}
        if lm is not None and lm["runs"]:
            self.lids["disc"] = (lm["inner"], lid_donors(lm["inner"], lm["runs"]))
        if lm is not None and lm.get("bg_runs"):
            self.lids["bg"] = (lm["bg_inner"], lid_donors(lm["bg_inner"], lm["bg_runs"]))

    def pupil_ratio(self, DX, DY):
        """Where the drawn pupil is: the distance from its centre over its edge (1 on the edge), for the canvas offsets DX, DY in units of R."""
        if self.round:
            return np.sqrt(DX * DX + DY * DY) / np.float32(self.p_out)
        px, py = DX - np.float32(self.cx), DY - np.float32(self.cy)
        return np.sqrt(px * px + py * py) / curve_at(self.coef, np.arctan2(py, px))

    def _source(self, rho, th):
        if not self.round:
            return (rho * np.cos(th)).astype(np.float32), (rho * np.sin(th)).astype(np.float32), rho
        pin = curve_at(self.coef, th)
        ux, uy = np.cos(th), np.sin(th)
        bx, by = np.float32(self.cx) + pin * ux, np.float32(self.cy) + pin * uy
        ox, oy = np.float32(0.992) * ux, np.float32(0.992) * uy
        t = (rho - np.float32(self.p_out)) / np.float32(1.0 - self.p_out)
        b = np.float32(self.bias)
        f = np.where(t >= 0, (1 - b) * t + b * t * t, (1 - b) * t).astype(np.float32)
        return bx + f * (ox - bx), by + f * (oy - by), f

    def map(self, rho, th, lids=None):
        """[(X, Y, weight)]: one source point, or three (the point and its two lid donors) whose weights sum to 1. lids: None, "disc" (the lids as found) or
        "bg" (the whole arc of a lid found)."""
        X, Y, f = self._source(rho, th)
        if lids not in self.lids:
            return [(X, Y, None)]
        inner_deg, (dl, dr, wr) = self.lids[lids]
        idx = (((th % (2 * math.pi)) * (1800.0 / math.pi)).astype(np.int64)) % 3600
        inner = inner_deg[(idx // 10) % 360]
        # the lid's share of this pixel: from just inside the lid's inner radius out (measured on the source radius, f, so the remap does not move it)
        src_rho = np.sqrt(X * X + Y * Y)
        m = smooth((src_rho - (inner - 0.05)) / 0.05) * (inner < 0.999)
        if not m.any():
            return [(X, Y, None)]
        XL, YL, _ = self._source(rho, dl[idx])
        XR, YR, _ = self._source(rho, dr[idx])
        w2 = wr[idx]
        return [(X, Y, 1.0 - m), (XL, YL, m * (1.0 - w2)), (XR, YR, m * w2)]


def _sample_sheet(frame, pts, cubic):
    """frame: a graded frame (Sd square, the disc centred, STUDIO_FILL of it); pts from Sheet.map. Returns float32 (..., 3) 0..255."""
    Sd = frame.shape[0]
    tgt = max(8, int(round(Sd * L.STUDIO_FILL)))
    off = (Sd - tgt) // 2
    Rg = tgt / 2.0
    cg = off + Rg
    out = None
    for X, Y, w in pts:
        v = sample(frame, cg + X * Rg - 0.5, cg + Y * Rg - 0.5, cubic)
        v = v if w is None else v * w[..., None]
        out = v if out is None else out + v
    return out


# ----------------------------------------------------------------------------- the disc
def _blur2(a, sigma):
    return C.blur(a, sigma, clip_negative=False)


def build_disc(iris, cx, cy, R, sheet, lids_in_disc, seed, index=0):
    """The Lens disc as a core.Disc (g premultiplied uint8, alpha, its top left, the exact centre and R): the remapped iris (bicubic from the grade WITHOUT the
    finish, at the disc's own size), dehaze and local contrast on luminance only, the limbal falloff, the pupil's faint shadow, the matte black pupil, the
    soft edge; dithered to 8 bit. Rows in chunks, so a 4096 px master holds a few rows of floats at a time."""
    Sd = max(8, int(round(2.0 * R / L.STUDIO_FILL)))
    frame = iris.graded(Sd, finish=False)
    t = int(math.ceil(2.0 * R * (1.0 + EDGE * 1.5))) + 4
    t += t % 2
    x0, y0 = int(round(cx - t / 2.0)), int(round(cy - t / 2.0))
    ccx, ccy = x0 + t / 2.0, y0 + t / 2.0                      # the exact centre of the square (snapped): the disc is drawn round it
    ax = (np.arange(t, dtype=np.float32) + np.float32(0.5) - np.float32(t / 2.0)) / np.float32(R)
    rgb = np.zeros((t, t, 3), np.float32)
    rows = max(64, (1 << 20) // t)
    for r0 in range(0, t, rows):
        r1 = min(t, r0 + rows)
        DX = np.broadcast_to(ax[None, :], (r1 - r0, t))
        DY = np.broadcast_to(ax[r0:r1, None], (r1 - r0, t))
        rho = np.sqrt(DX * DX + DY * DY)
        th = np.arctan2(DY, DX)
        sel = rho <= 1.0 + 3 * EDGE
        pts = sheet.map(rho, th, lids="disc" if lids_in_disc else None)
        v = _sample_sheet(frame, pts, True) / 255.0
        rgb[r0:r1] = np.where(sel[..., None], v, 0.0)
    del frame
    rho = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)
    # dehaze and local contrast on luminance only (hue and the colour ratios are the eye's own: no vibrance, no cyan)
    Y0 = rgb @ LUMA
    body = (rho > max(sheet.p_out + 0.08, 0.35)) & (rho < 0.95)
    st = max(1, int(t // 512))
    veil = float(np.percentile(Y0[::st, ::st][body[::st, ::st]], 6)) if body.any() else 0.0
    k = DEHAZE * veil
    rgb -= np.float32(k)
    rgb *= np.float32(1.0 / max(1e-3, 1.0 - k))
    np.maximum(rgb, 0.0, out=rgb)
    Yl = rgb @ LUMA
    Y2 = Yl.copy()
    for sig, amt in MICRO:
        Y2 += np.float32(amt) * (Yl - _blur2(Yl, max(0.6, sig * R)))
    ratio = np.clip(Y2, 0.0, 1.2) / np.maximum(Yl, np.float32(1e-3))
    ratio = np.where(Yl < 1e-3, np.float32(1.0), ratio)
    rgb *= ratio[..., None]
    ybody = float(np.mean(Y2[::st, ::st][body[::st, ::st]])) if body.any() else 0.3
    del Y0, Yl, Y2, ratio
    # the limbal falloff and the pupil's faint shadow on the iris
    p = sheet.p_out
    pr = sheet.pupil_ratio(ax[None, :], ax[:, None])                          # 1 on the drawn pupil's edge
    gain = 1.0 - np.float32(LIMB) * smooth((rho - LIMB_FROM) / (1.0 - LIMB_FROM)) ** 1.3
    gain *= 1.0 - np.float32(PUPIL_SHADOW) * np.exp(-np.clip((pr - 1.0) * np.float32(p), 0.0, None) ** 2 / np.float32(2 * PUPIL_SHADOW_W ** 2))
    rgb *= gain[..., None]
    # the pupil: deep matte black, no highlight (the owner), its edge the iris's own ruff blending in
    pa = 1.0 - smooth((pr - 0.92) / 0.10)
    if not sheet.round:
        pa = np.zeros_like(pa)                                                 # a slit or a bar keeps the restoration's own dark pupil, its tips as sharp as they are
    rgb = rgb * (1.0 - pa[..., None]) + np.float32(PUPIL_BLACK) * pa[..., None]
    alpha = (1.0 - smooth((rho - (1.0 - EDGE)) / (2.0 * EDGE))).astype(np.float32)
    rgb *= alpha[..., None]
    v = np.clip(rgb, 0.0, 1.0) * np.float32(255.0)
    rnd = C.Rand(seed, f"lens/disc{index}")
    v += rnd.g.random(v.shape, dtype=np.float32) - np.float32(0.5)
    g = np.clip(np.rint(v), 0, 255).astype(np.uint8)
    d = C.Disc()
    d.iris, d.index, d.Sd, d.master_map = iris, index, Sd, False
    d.g = g
    d.alpha = alpha
    d.x0, d.y0 = x0, y0
    d.cx, d.cy, d.R = ccx, ccy, float(R)
    return d, ybody


# ----------------------------------------------------------------------------- the background
def _disc_kernel(r):
    n = int(math.ceil(r))
    ax = np.arange(-n, n + 1, dtype=np.float32)
    dd = np.sqrt(ax[None] ** 2 + ax[:, None] ** 2)
    k = np.clip(r + 0.5 - dd, 0.0, 1.0)
    return k / k.sum()


def lens_blur(img, rad):
    """A spatially varying lens blur: the image blurred by disc kernels of BLUR_LEVELS radii (geometric), blended per pixel by the wanted radius rad (px). One FFT of
    the image (edges reflected by the largest radius), one product and one inverse per radius."""
    rmin = max(0.6, float(rad.min()))
    rmax = max(float(rad.max()), rmin * 1.01)
    radii = np.geomspace(rmin, rmax, BLUR_LEVELS)
    lr = np.log(np.clip(rad, rmin, radii[-1]))
    lg = np.log(radii)
    idx = np.clip(np.searchsorted(lg, lr) - 1, 0, BLUR_LEVELS - 2)
    w = ((lr - lg[idx]) / (lg[idx + 1] - lg[idx])).astype(np.float32)
    h, wd = img.shape[:2]
    kr = int(math.ceil(radii[-1])) + 1
    p = np.pad(img, ((kr, kr), (kr, kr), (0, 0)), mode="reflect")
    H, W = p.shape[:2]
    F = [np.fft.rfft2(p[..., c]) for c in range(3)]
    out = np.zeros_like(img)
    prev = None
    for i, r in enumerate(radii):
        kern = _disc_kernel(r)
        k = kern.shape[0] // 2
        K = np.zeros((H, W), np.float32)
        K[:kern.shape[0], :kern.shape[1]] = kern
        FK = np.fft.rfft2(np.roll(K, (-k, -k), (0, 1)))
        cur = np.stack([np.fft.irfft2(F[c] * FK, s=(H, W))[kr:kr + h, kr:kr + wd] for c in range(3)], -1).astype(np.float32)
        if prev is not None:
            sel = (idx == i - 1)
            out += np.where(sel[..., None], prev * (1 - w)[..., None] + cur * w[..., None], np.float32(0.0))
        prev = cur
    return out


def build_background(iris, sheet, W, H, cx, cy, R, ybody):
    """The background on its grid (gh, gw, 3) float32 display space and the grid factor fb (canvas px per grid px): the remapped iris with every lid filled,
    magnified MAG about the disc's centre, defocused (lens), darkened, a little less colourful, vignetted to black, with the dark ring round the disc."""
    fb = max(1, int(math.ceil(max(W, H) / float(BG_GRID))))
    gw, gh = int(math.ceil(W / fb)), int(math.ceil(H / fb))
    S = min(W, H)
    src = iris.graded(BG_SRC, finish=False)
    xs = (np.arange(gw, dtype=np.float32) + 0.5) * fb
    ys = (np.arange(gh, dtype=np.float32) + 0.5) * fb
    dx = (xs[None, :] - np.float32(cx)) / np.float32(MAG * R)
    dy = (ys[:, None] - np.float32(cy)) / np.float32(MAG * R)
    DX, DY = np.broadcast_to(dx, (gh, gw)), np.broadcast_to(dy, (gh, gw))
    brho = np.sqrt(DX * DX + DY * DY)
    bth = np.arctan2(DY, DX)
    pts = sheet.map(np.minimum(brho, np.float32(0.995)), bth, lids="bg")
    bg = _sample_sheet(src, pts, False) / 255.0
    del src
    bg *= (1.0 - smooth((brho - 0.97) / 0.10))[..., None]                   # past the magnified limbus: to black
    lum = bg @ LUMA
    bg = bg * np.float32(1 - BG_DESAT) + lum[..., None] * np.float32(BG_DESAT)
    # the lens blur grows from the disc's edge to the corners
    rpx = np.sqrt((xs[None, :] - np.float32(cx)) ** 2 + (ys[:, None] - np.float32(cy)) ** 2)          # canvas px
    far = max(math.hypot(cx, cy), math.hypot(W - cx, cy), math.hypot(cx, H - cy), math.hypot(W - cx, H - cy))
    u = np.clip((rpx - R) / max(far - R, 1.0), 0.0, 1.0)
    rad = (np.float32(BLUR_IN) + np.float32(BLUR_OUT - BLUR_IN) * u ** 1.1) * np.float32(S / fb)
    bg = lens_blur(bg.astype(np.float32), rad.astype(np.float32))
    # darken, vignette (from the canvas's centre, black at its corners) and the dark ring round the disc
    rc = np.sqrt((xs[None, :] - W / 2.0) ** 2 + (ys[:, None] - H / 2.0) ** 2) / np.float32(math.hypot(W / 2.0, H / 2.0))
    vig = (1.0 - smooth((rc - VIG_START) / (1.0 - VIG_START))) ** VIG_POWER
    halo = 1.0 - np.float32(HALO) * np.exp(-np.clip(rpx - R, 0.0, None) ** 2 / np.float32(2 * (HALO_W * R) ** 2))
    lift = float(np.clip((BG_REF / max(1e-3, ybody)) ** 0.5, 1.0, BG_LIFT_MAX))
    bg = np.clip(bg, 0.0, None) * (np.float32(BG_GAIN * lift) * vig * halo)[..., None]
    return bg.astype(np.float32), fb


# ----------------------------------------------------------------------------- the look, as the band renderer calls it
class Lens:
    NAME = NAME

    def halo_rows(self, scene):
        return 4 * scene.f + 2

    def prepare(self, scene):
        e = scene.eyes[0]
        ir = e.iris
        ref_sq = C._tight(ir.graded(C.REF_SIDE, finish=False))[0]
        pu = PUP.analyse(ref_sq)
        lm = lid_map(C._tight(ir.graded(BG_SRC, finish=False))[0])
        if scene.opts.get("lens_lids", True) is False:                         # the laboratory's before picture: no lid filled anywhere
            lm = dict(lm, inner=np.ones(360, np.float32), runs=[], bg_inner=np.ones(360, np.float32), bg_runs=[], disc_fill=True)
        remap = scene.opts.get("lens_remap", True) is not False
        self.sheet = Sheet(pu, lm, remap=remap, sq=ref_sq)
        disc_fill = (bool(lm["disc_fill"]) or scene.opts.get("lens_disc_lids") == "force") and scene.opts.get("lens_disc_lids", True) is not False   # force: the laboratory's look at a large one
        d, ybody = build_disc(ir, e.cx, e.cy, e.R, self.sheet, disc_fill and bool(lm["runs"]), scene.seed, 0)
        e.disc = d
        e.snap = (d.cx, d.cy, d.R)
        e.fill_mode, e.k_s = "lens", float(MAG)                                # what the golden suite's facts read of an eye (looks.py's fill sets them for Echo)
        self.bg, self.fb = build_background(ir, self.sheet, scene.W, scene.H, d.cx, d.cy, d.R, ybody)
        scene.info["lens"] = {"p_measured": round(self.sheet.p_meas, 3), "p_drawn": round(self.sheet.p_out, 3), "remap": self.sheet.bias > 0, "pupil_round": self.sheet.round,
                              "lid_runs": [[int(s), int(n)] for s, n in lm["runs"]], "lid_max_run": lm["max_run"], "lid_max_depth": lm["max_depth"],
                              "lid_bg_runs": [[int(s), int(n)] for s, n in lm["bg_runs"]],
                              "lid_in_disc": "filled" if (disc_fill and lm["runs"]) else ("kept" if lm["runs"] else "none"), "bg_grid": self.fb}
        self.layers = []

    def base(self, scene, cv, y0, y1):
        from .engine import resize_band
        cv += resize_band(self.bg, y0, y1, scene.W, scene.H, self.fb) if self.fb > 1 else self.bg[y0:y1, :scene.W]


LOOKS = {"lens": Lens}
