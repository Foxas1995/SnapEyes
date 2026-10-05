# -*- coding: utf-8 -*-
"""reveal_clean: what the Reveal does to the restored layer's SOURCE before it is resampled (ported from the scratch prototype's
designs/presentation_clean.py, work package WP9). numpy and Pillow only.

One function per job, every one a server side step of reveal.reveal_params() and every one baked into the image the page receives (the
watermarked display copy on /try), so the page needs no extra arithmetic:

  pupil_info(restored, kind)     centre, radius and SHAPE CLASS of the restored pupil: round (the engine's circle detector, human eyes), slit or
                                 bar (a dark-blob detector, animals; pets are out of scope for release 1: kind is always "human"); the cut goes
                                 through this centre.
  crush_pupil(restored, info)    the restored pupil to pure black, its own shape kept: luma x 0.12, chroma 0, feathered over the pupil's rim.
  lid_mask(restored, lid=None)   eyelid skin inside the restored disc: the pink skin wedges the colour rule finds (and any lid line /api/analyze
                                 supplies: it supplies none today). Returns a soft mask (1 = lid) and the share of the disc it covers; the masked
                                 pixels are hidden (black), never altered.
  apply_lid(restored, mask)      the restored image with the lid hidden.
  colour_drift(crop, restored)   dE00 between the median colour of the photo's iris band and the restored one: above 8 the cut is withheld.

Module rule of the v3 work: every module starts with the __future__ import (Vercel's default Python is 3.12)."""
from __future__ import annotations

import math
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

PAD = 1.12
R_FRAC = 1.0 / (2.0 * PAD)
WORK = 256                               # the side the detectors work at

# ---- pupil
PUPIL_CRUSH_LUMA = 0.12                  # AD 2: luma x 0.12, chroma 0 inside 0.88 r_p ...
PUPIL_CRUSH_IN, PUPIL_CRUSH_OUT = 0.88, 1.00    # ... feathered to 1.00 r_p
PUPIL_OFF_MAX = 0.40                     # a pupil this far off centre (iris radii) is a mis-detection, not an eye
PUPIL_TIGHT_Q = (0.25, 0.16, 0.09)        # blob levels: core + this share of the way to the iris body, tried in turn
ROUND_MIN = 0.72                         # minor / major axis of a round pupil at least this
BLOB_AREA_MIN, BLOB_AREA_MAX = 0.004, 0.55      # share of the iris disc

# ---- lid (the AD rule: a* more than 9 above the disc median and a* above 8, sigma 6 px at 1024)
LID_DA = 9.0
LID_A_MIN = 8.0
LID_SIGMA = 6.0 / 1024.0                 # of the image side
LID_LAMBDA = 0.7                         # a cap pixel without lid evidence costs this much (a candidate pixel earns 1)
LID_TMIN, LID_TMAX = 0.45, 0.97          # the lid's margin lies between these distances from the centre (R)
LID_SCORE_MIN = 0.012                    # net evidence of an accepted lid, as a share of the disc
LID_PURITY_MIN = 0.50                    # share of the cap that shows the evidence
LID_AREA_MIN = 0.03                      # an accepted cap covers at least this share of the disc
LID_FEATHER = 0.03                       # R, along the lid's edge
LID_GROW = 0.022                         # R, the lash shadow and the margin line the colour evidence misses
LID_PUPIL_KEEP = 1.10                    # never inside this many pupil radii, never inside 0.30 R

# ---- colour drift
DRIFT_BAND = (0.50, 0.88)
DRIFT_WARN, DRIFT_FAIL = 6.0, 8.0


def _grids(N, R_frac=R_FRAC):
    R = R_frac * N
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    ax = (xx + 0.5 - N / 2.0) / R
    ay = (yy + 0.5 - N / 2.0) / R
    return ax, ay, np.hypot(ax, ay)


def _lum(a):
    a = a.astype(np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def _blur_img(a, sig):
    """Gaussian blur of a float32 2-D array (separable, edge replicated): numpy only, deterministic."""
    a = np.asarray(a, np.float32)
    if sig < 0.25:
        return a
    n = max(1, int(math.ceil(3.0 * sig)))
    x = np.arange(-n, n + 1, dtype=np.float32)
    k = np.exp(-0.5 * (x / sig) ** 2)
    k /= k.sum()
    p = np.pad(a, ((0, 0), (n, n)), mode="edge")
    o = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(len(k)))
    p = np.pad(o, ((n, n), (0, 0)), mode="edge")
    return sum(k[i] * p[i:i + a.shape[0]] for i in range(len(k))).astype(np.float32)


def _erode(m, k):
    im = Image.fromarray((m * 255).astype(np.uint8))
    for _ in range(int(k)):
        im = im.filter(ImageFilter.MinFilter(3))
    return np.asarray(im) > 127


def _dilate(m, k):
    im = Image.fromarray((m * 255).astype(np.uint8))
    for _ in range(int(k)):
        im = im.filter(ImageFilter.MaxFilter(3))
    return np.asarray(im) > 127


def _label(mask):
    """4-connected components of a boolean 2-D array: (labels int32, sizes list with sizes[0] = 0)."""
    lab = np.zeros(mask.shape, np.int32)
    sizes = [0]
    H, W = mask.shape
    n = 0
    for y, x in np.argwhere(mask):
        if lab[y, x]:
            continue
        n += 1
        q = deque([(y, x)])
        lab[y, x] = n
        c = 0
        while q:
            cy, cx = q.popleft()
            c += 1
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = n
                    q.append((ny, nx))
        sizes.append(c)
    return lab, sizes


def _fill_holes(m):
    """Fill the holes of a boolean mask (a catch-light inside a pupil): flood the background from the border."""
    H, W = m.shape
    bg = np.zeros((H, W), bool)
    q = deque()
    for y in range(H):
        for x in (0, W - 1):
            if not m[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    for x in range(W):
        for y in (0, H - 1):
            if not m[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and not m[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                q.append((ny, nx))
    return ~bg


def _small(im, N=WORK):
    im = im if isinstance(im, Image.Image) else Image.fromarray(im)
    return np.asarray(im.convert("RGB").resize((N, N), Image.LANCZOS))


# ----------------------------------------------------------------------------- pupil
def _seed_blob(m, lum, rr, N):
    """The component of the boolean mask m that holds the darkest pixel of the picture's centre (r < 0.40 R), when it does not run
    out to the rim (a lid's shadow does); None otherwise. Grown by flood fill from that one pixel, so a thin curved slit is one
    blob and an arc of shadow that only touches it is not picked up unless the level is that loose."""
    cen = np.where(rr < 0.40, lum, np.float32(1e9))
    y0, x0 = np.unravel_index(int(np.argmin(cen)), cen.shape)
    if not m[y0, x0]:
        return None
    H, W = m.shape
    seen = np.zeros((H, W), bool)
    q = deque([(y0, x0)])
    seen[y0, x0] = True
    pts = []
    while q:
        cy, cx = q.popleft()
        pts.append((cy, cx))
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            ny, nx = cy + dy, cx + dx
            if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    if len(pts) < 10:
        return None
    ys, xs = np.array(pts).T
    if float(rr[ys, xs].max()) > 0.86:
        return None
    return seen


def pupil_blob(restored, N=WORK):
    """The restored pupil as a dark blob: dict(cx, cy, rho, a, b, angle, cls, mask, area) or None. cx, cy in iris radii from the
    restored square's centre (right, down); a, b the half axes in iris radii (major, minor); angle of the major axis in
    degrees from the x axis (0 = horizontal bar, 90 = vertical slit); cls round | slit | bar; mask a boolean N x N
    array (holes filled). Works on any pupil shape: the dark core of the picture's centre, grown a quarter of the way to the
    iris body (a tighter level when a lid's shadow is attached), the most compact central component."""
    rgb = _small(restored, N)
    lum = _blur_img(_lum(rgb), 0.7)
    ax, ay, rr = _grids(N)
    disc = float((rr <= 1.0).sum())
    ring = (rr > 0.45) & (rr < 0.88)
    if ring.sum() < 50:
        return None
    ref = float(np.percentile(lum[ring], 60))
    core = float(np.percentile(lum[rr < 0.40], 3.0))   # a pupil is central: its darkest pixels set the level, not a lid's shadow
    if ref - core < 14.0:                              # no pupil contrast to read (an almost black iris)
        return None
    blob = None
    for q in PUPIL_TIGHT_Q:
        thr = min(core + q * (ref - core), 0.65 * ref)
        m = (lum < thr) & (rr < 0.93)
        blob = _seed_blob(m, lum, rr, N)
        if blob is not None:
            break
    if blob is None:
        return None
    blob = _fill_holes(_dilate(_erode(_dilate(blob, 2), 2), 0))      # close small gaps (a reflection on the slit)
    blob &= rr < 0.95
    area = float(blob.sum()) / disc
    if not (BLOB_AREA_MIN <= area <= BLOB_AREA_MAX):
        return None
    ys, xs = np.nonzero(blob)
    X, Y = ax[ys, xs], ay[ys, xs]
    cx, cy = float(X.mean()), float(Y.mean())
    cov = np.cov(np.vstack([X - cx, Y - cy]))
    w, v = np.linalg.eigh(cov)
    w = np.maximum(w, 1e-9)
    a, b = 2.0 * math.sqrt(float(w[1])), 2.0 * math.sqrt(float(w[0]))      # half axes of the equivalent ellipse
    ang = math.degrees(math.atan2(float(v[1, 1]), float(v[0, 1]))) % 180.0
    if b / a >= ROUND_MIN:
        cls = "round"
    elif 55.0 <= ang <= 125.0:
        cls = "slit"
    elif ang <= 35.0 or ang >= 145.0:
        cls = "bar"
    else:
        cls = "slit"                                 # a tilted slit (cats hold their heads at angles)
    rho = math.sqrt(area)                             # radius of the disc of the same area, in iris radii (disc area = pi R^2)
    return dict(cx=cx, cy=cy, rho=float(rho), a=float(a), b=float(b), angle=float(ang), cls=cls, mask=blob, area=area)


def pupil_info(restored, kind="human", circle=None):
    """{"cx", "cy", "rho", "cls", "a", "b", "angle", "mask"?}: the restored pupil. kind "human": the repo's circle detector
    first (proven on the calibration set), the blob detector when that finds nothing; kind "pet": the blob detector first (slit
    and bar pupils are not discs), the circle detector when it finds nothing. Nothing found: centre (0, 0), cls None."""
    def from_circle():
        if circle is None:
            return None
        pc = circle(restored)
        if pc is None:
            return None
        cx, cy, rho = float(pc[0]), float(pc[1]), float(pc[2])
        if math.hypot(cx, cy) > 0.25:
            return None
        return dict(cx=cx, cy=cy, rho=rho, a=rho, b=rho, angle=0.0, cls="round", mask=None, area=math.pi * rho * rho / math.pi)

    def from_blob():
        try:
            bl = pupil_blob(restored)
        except Exception:  # noqa: a broken restoration must never break the page
            return None
        if bl is None or math.hypot(bl["cx"], bl["cy"]) > PUPIL_OFF_MAX:
            return None
        return bl

    order = (from_blob, from_circle) if kind == "pet" else (from_circle, from_blob)
    for f in order:
        r = f()
        if r is not None:
            return r
    return dict(cx=0.0, cy=0.0, rho=None, a=None, b=None, angle=0.0, cls=None, mask=None, area=0.0)


def pupil_weight(info, N):
    """Soft crush weight of the pupil on an N x N grid of the restored square (1 inside, 0 outside, feathered over the
    pupil's rim): the AD's 0.88 to 1.00 r_p ramp for a round pupil, the blob (eroded one step, blurred) for a slit or bar."""
    if info is None or info.get("cls") is None or not info.get("rho"):
        return np.zeros((N, N), np.float32)
    ax, ay, rr = _grids(N)
    if info["cls"] == "round" or info.get("mask") is None:
        d = np.hypot(ax - info["cx"], ay - info["cy"]) / max(info["rho"], 1e-4)
        t = np.clip((d - PUPIL_CRUSH_IN) / (PUPIL_CRUSH_OUT - PUPIL_CRUSH_IN), 0.0, 1.0)
        return (1.0 - t * t * (3.0 - 2.0 * t)).astype(np.float32)
    m = info["mask"].astype(np.float32)
    if m.shape[0] != N:
        m = np.asarray(Image.fromarray(m, "F").resize((N, N), Image.BILINEAR), np.float32)
    k = max(1.0, 0.012 * N)
    w = _blur_img(m, k)
    return np.clip((w - 0.20) / 0.60, 0.0, 1.0).astype(np.float32)


def crush_pupil(restored, info, luma=PUPIL_CRUSH_LUMA):
    """The restored image with its pupil crushed to pure black (luma x 0.12, chroma 0, feathered): PIL RGB, same size.
    The pupil's shape is whatever `info` says it is. No pupil found: the image unchanged."""
    im = restored.convert("RGB")
    if info is None or not info.get("rho"):
        return im
    N = im.size[0]
    w = pupil_weight(info, N)
    if not w.any():
        return im
    a = np.asarray(im).astype(np.float32)
    g = (_lum(a) * luma)[..., None]
    out = a * (1.0 - w[..., None]) + g * w[..., None]
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


# ----------------------------------------------------------------------------- eyelids
def _lab_a_b(rgb):
    """CIELAB a*, b* (D65) of an sRGB uint8 array: float32, numpy only."""
    c = rgb.astype(np.float32) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    X = 0.4124564 * c[..., 0] + 0.3575761 * c[..., 1] + 0.1804375 * c[..., 2]
    Y = 0.2126729 * c[..., 0] + 0.7151522 * c[..., 1] + 0.0721750 * c[..., 2]
    Z = 0.0193339 * c[..., 0] + 0.1191920 * c[..., 1] + 0.9503041 * c[..., 2]
    f = lambda t: np.where(t > 216.0 / 24389.0, np.cbrt(t), (24389.0 / 27.0 * t + 16.0) / 116.0)
    fx, fy, fz = f(X / 0.95047), f(Y), f(Z / 1.08883)
    return (116.0 * fy - 16.0).astype(np.float32), (500.0 * (fx - fy)).astype(np.float32), (200.0 * (fy - fz)).astype(np.float32)


def lid_from_geometry(geom, N):
    """A lid mask (float32 N x N, 1 = lid) from lid lines in the repo's /api/analyze format: [(side, xk, bk)], side "top" or
    "bottom", the lid the part of the disc on the rim side of the curve y(x) = interp(x, xk, bk) in iris radii from the centre
    (x right, y down; for the bottom lid y is measured upwards)."""
    ax, ay, rr = _grids(N)
    m = np.zeros((N, N), bool)
    xs = ax[0]
    for side, xk, bk in (geom or []):
        yb = np.interp(xs, np.asarray(xk, np.float32), np.asarray(bk, np.float32))[None, :]
        m |= (ay < yb) if side == "top" else (-ay < yb)
    return m.astype(np.float32)


def _soften(m, N, feather=LID_FEATHER, grow=LID_GROW):
    """The lid blob grown by `grow` R and feathered outward by `feather` R: a soft 0..1 mask, 1 on the hidden side."""
    R = R_FRAC * N
    g = _dilate(m > 0.5, max(1, int(round(grow * R)))) if grow > 0 else (m > 0.5)
    soft = _blur_img(g.astype(np.float32), max(0.8, feather * R / 2.0))
    return np.clip(np.maximum(soft * 2.0, g.astype(np.float32)), 0.0, 1.0)


def _best_cap(cand, allow, rr, ax, ay, lam=LID_LAMBDA, dphi=3.0, exclude=None):
    """The straight chord whose outer cap holds the most lid evidence: maximise sum over the cap of (+1 for a candidate pixel,
    -lam for any other), the cap reaching the rim (chord distance t from 0.45 R out to 0.97 R), covering at least 1 % of the disc.
    Returns (score, phi_deg, t, purity, area) or None. exclude: directions (degrees) already taken: a second lid must lie 90 degrees away.
    Every angle is one weighted histogram of the projected pixels, so the whole search is 120 bincounts at 256 px."""
    m = allow & (rr > 0.30)
    if not m.any():
        return None
    wgt = np.where(cand, 1.0, -lam).astype(np.float32)
    mc = cand.astype(np.float32)
    n_m = float(m.sum())
    best = None
    k0, k1 = int((LID_TMIN + 1.0) / 0.01), int((LID_TMAX + 1.0) / 0.01)
    for phi in np.arange(0.0, 360.0, dphi):
        if exclude is not None and any(abs((phi - e + 180.0) % 360.0 - 180.0) < 90.0 for e in exclude):
            continue
        s = ax * math.cos(math.radians(phi)) + ay * math.sin(math.radians(phi))
        bi = np.clip(((s + 1.0) / 0.01).astype(np.int64), 0, 199)
        tot = np.bincount(bi[m], weights=wgt[m], minlength=200)
        cnt = np.bincount(bi[m], weights=mc[m], minlength=200)
        ar = np.bincount(bi[m], minlength=200).astype(np.float64)
        cs = np.cumsum(tot[::-1])[::-1]
        cc = np.cumsum(cnt[::-1])[::-1]
        ca = np.cumsum(ar[::-1])[::-1]
        ok = ca[k0:k1] >= 0.01 * n_m
        if not ok.any():
            continue
        sc = np.where(ok, cs[k0:k1], -1e18)
        k = int(np.argmax(sc)) + k0
        if best is None or sc[k - k0] > best[0]:
            best = (float(sc[k - k0]), float(phi), k * 0.01 - 1.0, float(cc[k] / max(ca[k], 1.0)), float(ca[k] / n_m))
    return best


def lid_mask(restored, lid=None, pupil=None, N=WORK):
    """(soft float32 N x N, share of the disc 0..1, info): the eyelid inside the restored disc, hidden.
    lid: lid lines from /api/analyze (lid_from_geometry format) or None; they are hidden as given. The colour evidence (AD rule:
    blurred a* more than 9 above the disc median and above 8: pink or sepia skin) does not draw the mask itself, it only
    chooses it: the straight chord whose cap holds the most evidence is the lid's margin (a colour blob alone is ragged, and
    a lid is one clean edge). Accepted only when the cap is pure enough (PURITY_MIN) and its net evidence is at least 1.2 % of the
    disc (a lid-free eye has no chord with a positive score at all; the 10 calibration eyes: lids d04, d05, w08 found, 7 lid-free
    eyes untouched). A second lid 90 degrees or more away is searched the same way. Deterministic, 0.06 s at 256."""
    ax, ay, rr = _grids(N)
    disc = float((rr <= 1.0).sum())
    info = dict(colour=0.0, given=0.0, caps=[])
    hard = np.zeros((N, N), bool)
    if lid:
        g = lid_from_geometry(lid, N) > 0.5
        hard |= g
        info["given"] = float((g & (rr <= 1.0)).sum()) / disc
    rgb = _small(restored, N)
    _l, a, _b = _lab_a_b(rgb)
    sa = _blur_img(a, LID_SIGMA * N)
    med = float(np.median(sa[(rr > 0.30) & (rr < 0.95)]))
    cand = (sa - med > LID_DA) & (sa > LID_A_MIN) & (rr < 0.985)
    allow = rr <= 1.0
    taken = []
    for _ in range(2):
        best = _best_cap(cand, allow & ~hard, rr, ax, ay, exclude=taken if taken else None)
        if best is None:
            break
        score, phi, t, purity, area = best
        if score < LID_SCORE_MIN * disc or purity < LID_PURITY_MIN or area < LID_AREA_MIN:
            break
        s = ax * math.cos(math.radians(phi)) + ay * math.sin(math.radians(phi))
        cap = (s > t) & (rr <= 1.02)
        hard |= cap
        taken.append(phi)
        info["caps"].append(dict(phi=round(phi, 1), t=round(t, 3), purity=round(purity, 2), area=round(area, 3), score=round(score / disc, 3)))
    info["colour"] = float((hard & (rr <= 1.0)).sum()) / disc - info["given"]
    keep = rr > 0.30
    if pupil is not None and pupil.get("rho"):
        keep &= np.hypot(ax - pupil["cx"], ay - pupil["cy"]) > LID_PUPIL_KEEP * pupil["rho"]
    hard &= keep
    if not hard.any():
        return np.zeros((N, N), np.float32), 0.0, info
    soft = (_soften(hard, N) * keep).astype(np.float32)
    share = float((soft > 0.5)[rr <= 1.0].sum()) / disc
    return soft, share, info


def apply_lid(restored, mask):
    """The restored image with the lid hidden (multiplied by 1 - mask, black where the lid was): PIL RGB, same size. The mask
    (any size) is resampled bilinearly; pixels outside it are untouched, byte for byte."""
    im = restored.convert("RGB")
    if mask is None or not np.any(mask):
        return im
    N = im.size[0]
    m = mask
    if m.shape[0] != N:
        m = np.asarray(Image.fromarray(m.astype(np.float32), "F").resize((N, N), Image.BILINEAR), np.float32)
    a = np.asarray(im).astype(np.float32)
    out = a * (1.0 - np.clip(m, 0.0, 1.0))[..., None]
    changed = m > 1e-4
    res = np.asarray(im).copy()
    res[changed] = np.clip(out[changed] + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(res)


# ----------------------------------------------------------------------------- colour drift
def _de00(l1, l2):
    """CIEDE2000 of two Lab triples (Sharma's reference implementation, kL = kC = kH = 1)."""
    L1, a1, b1 = l1
    L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = 0.5 * (C1 + C2)
    G = 0.5 * (1.0 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25.0 ** 7)))
    a1p, a2p = (1.0 + G) * a1, (1.0 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360.0
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    else:
        dhp = h2p - h1p
        dhp = dhp - 360.0 if dhp > 180 else (dhp + 360.0 if dhp < -180 else dhp)
    dHp = 2.0 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2.0))
    Lbp, Cbp = 0.5 * (L1 + L2), 0.5 * (C1p + C2p)
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = 0.5 * (h1p + h2p)
    else:
        hbp = 0.5 * (h1p + h2p + (360.0 if h1p + h2p < 360 else -360.0))
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30)) + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6)) - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dth = 30.0 * math.exp(-(((hbp - 275.0) / 25.0) ** 2))
    Rc = 2.0 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25.0 ** 7))
    Sl = 1.0 + 0.015 * (Lbp - 50.0) ** 2 / math.sqrt(20.0 + (Lbp - 50.0) ** 2)
    Sc, Sh = 1.0 + 0.045 * Cbp, 1.0 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2.0 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh))


def colour_drift(crop, restored, lid=None, N=WORK):
    """(dE00, info): the colour the restoration shows against the colour the photo shows, each the median CIELAB of the iris band
    0.50-0.88 R of the same square (the restored image is a rigid copy of the crop), specular pixels (L* over 90 in either) and the lid
    mask left out. The half-and-half Reveal puts these two colours side by side: above 8 the cut looks like two different
    eyes (AD 4: fail above 8, warn above 6)."""
    ax, ay, rr = _grids(N)
    band = (rr >= DRIFT_BAND[0]) & (rr <= DRIFT_BAND[1])
    ra, rb = _small(restored, N), _small(crop, N)

    def lab3(rgb):
        c = rgb.astype(np.float32) / 255.0
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        X = 0.4124564 * c[..., 0] + 0.3575761 * c[..., 1] + 0.1804375 * c[..., 2]
        Y = 0.2126729 * c[..., 0] + 0.7151522 * c[..., 1] + 0.0721750 * c[..., 2]
        Z = 0.0193339 * c[..., 0] + 0.1191920 * c[..., 1] + 0.9503041 * c[..., 2]
        f = lambda t: np.where(t > 216.0 / 24389.0, np.cbrt(t), (24389.0 / 27.0 * t + 16.0) / 116.0)
        fx, fy, fz = f(X / 0.95047), f(Y), f(Z / 1.08883)
        return np.stack([116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)], -1)

    la, lb = lab3(ra), lab3(rb)
    ok = band & (la[..., 0] < 90.0) & (lb[..., 0] < 90.0)
    if lid is not None and np.any(lid):
        m = lid
        if m.shape[0] != N:
            m = np.asarray(Image.fromarray(m.astype(np.float32), "F").resize((N, N), Image.BILINEAR), np.float32)
        ok &= m < 0.05
    if ok.sum() < 200:
        return 0.0, dict(n=int(ok.sum()))
    ma = [float(np.median(la[..., i][ok])) for i in range(3)]
    mb = [float(np.median(lb[..., i][ok])) for i in range(3)]
    d = _de00(mb, ma)
    return float(d), dict(photo=[round(v, 1) for v in mb], restored=[round(v, 1) for v in ma], n=int(ok.sum()))
