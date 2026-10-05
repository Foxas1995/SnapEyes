# -*- coding: utf-8 -*-
"""reveal: the server half of the clean-iris Reveal (work package WP9), ported from the scratch prototype's designs/presentation.py.

What /api/enhance hands the page next to the display copy, all measured on the CLEAN restoration and the deglared crop it was made from (the
display copy's watermark would disturb every measurement):
  reveal_params(crop, restored)   the small dict ("reveal", about 140 bytes): pupil centre and radius, the registration shift of the photo layer,
                                  the restored edge (alpha 1 up to e0 R, 0 from e1 R, e0 >= 0.95 so zone A is untouched), ok (registration
                                  trusted AND colour drift <= 8: False means the page shows the strip without the cut), soft, drift, lid
  public_params(p)                p without its private masks: exactly what goes over the wire
  prepare_restored(restored, p)   the restored image as the Reveal shows it: the eyelid skin hidden, the pupil crushed to pure black (its own
                                  shape kept), nothing else touched
  display_copy(restored)          the 800 px display copy with the preview watermark (api/_lib/preview.py display_image; style "repo", the
                                  default). The AD's arcs variant (reveal_wm.py) stays OFF until the owner signs D14: only style="arcs" reaches it
  reveal_for(crop, restored)      the one call of /api/enhance: the guard on the time left, the measurement, the prepared and watermarked copy,
                                  the codes of the event; never raises, never costs the preview

What is NOT here (decision C10): the wide frame, the 4:5 card, the strip and the context crop. The browser builds the customer's frame from the
photo it still holds (src/reveal/wideFrame.ts), keeps it in memory and never uploads it; no server code builds or stores one. Its arithmetic is
src/reveal/revealMath.ts, checked against vectors the prototype's Python wrote (src/reveal/vectors.json).

Nothing is written on the picture (the studio writes nothing on the artwork), nothing is drawn around the iris: no stroke, no glow. Deterministic,
no randomness, no model call. numpy and Pillow only.

Module rule of the v3 work: every module starts with the __future__ import (Vercel's default Python is 3.12)."""
from __future__ import annotations

import base64
import io
import math
import time

import numpy as np
from PIL import Image

from .. import iris as L
from . import reveal_clean as CL


PAD = 1.12                               # crop padding the site uses
R_FRAC = 1.0 / (2.0 * PAD)               # restored iris radius as a share of the restored square's side (0.4464)
RF = 0.335                               # frame iris radius / frame width (D = 0.67 W, the owner's example)
ZONE_A = 0.95                            # zone A ends here: nothing of the restored layer may change inside it (BRIEF 1.1)
F3_LO, F3_HI = 0.985, 1.015              # outer safety alpha of the restored layer: 1 up to 0.985 R, 0 at 1.015 R
EDGE_E1_MAX = 1.03                       # the softer edge variant never reaches further out than this
REG_TOL = 0.005                          # registration tolerance in R_f (about 1 px at 640 px)
REG_BAND = 0.06                          # band half width about the cut, in R_f
REG_NCC_MIN = 0.20                       # below this the gradient fields do not correlate: do not claim a registration
REG_SPREAD_OK = REG_TOL                  # the four half-annuli may disagree about the shift by this much (EN3)
SHIFT_MAX = 0.06                         # a larger measured shift is a mis-registration, not a correction
EDGE_TARGET = 0.034                      # the brief's 10-90 % width of the restored edge in R; zone B alone reaches about 0.02-0.03 (EN1)
EDGE_MIN_NATURAL = 0.030                 # natural edges at least this wide are left alone
SOFT_PX_PER_R = 100.0                    # fewer photo pixels than this per iris radius: the raw half looks soft (AD8)
DRIFT_FAIL, DRIFT_WARN = CL.DRIFT_FAIL, CL.DRIFT_WARN


def _clampf(x, lo, hi, default=None):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(x):
        return default
    return min(max(x, lo), hi)


def smoothstep01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


# ----------------------------------------------------------------------------- pupil
def _circle_detector(im):
    """The repo's round-pupil detector on a 512 px copy (None when it finds no clear round pupil)."""
    im = im if isinstance(im, Image.Image) else Image.fromarray(im)
    im = im.convert("RGB")
    if im.size[0] > 512:
        im = im.resize((512, 512), Image.LANCZOS)
    return L.pupil_circle(im, R_FRAC)


def pupil_info(restored, kind="human"):
    """The restored pupil: dict(cx, cy (iris radii from the centre, right / down), rho (radius, iris radii), cls round | slit |
    bar | None, a, b, angle, mask). kind "human": the repo's circle detector first; "pet": the dark-blob detector first (slit and
    bar pupils are not discs). Nothing found: centre (0, 0), cls None (the cut then goes through the iris centre)."""
    def circ(im):
        try:
            return _circle_detector(im)
        except Exception:  # noqa: a broken restoration must never break the page
            return None
    return CL.pupil_info(restored, kind, circ)


def pupil_centre(restored, kind="human"):
    """(px, py, rho): centre in iris radii from the frame centre (right, down) and radius in iris radii; (0, 0, None) when
    no pupil is found. One number pair the server hands to the page next to the display copy."""
    i = pupil_info(restored, kind)
    return i["cx"], i["cy"], i["rho"]


# ----------------------------------------------------------------------------- display copy (/try)
def display_copy(restored, lang="en", style="repo"):
    """The watermarked display copy /api/enhance hands the page instead of the clean restoration. style "repo": the repo's own
    preview.display_image (800 px square, the preview tile across the iris, read-only use). style "arcs": the AD's proposal (5), the
    same words on three arcs at 0.62-0.92 R with nothing inside 0.55 R (owner sign-off D14). Same frame as the clean
    restoration, so every number measured on the clean one applies unchanged."""
    if style == "arcs":
        from . import reveal_wm as WM
        return WM.display_copy_arcs(restored, lang)
    from .. import preview as PV
    return PV.display_image(restored.convert("RGB"), lang)


def _sample_lum(lum, xs, ys):
    """Bilinear samples of a 2-D array at float pixel-centre coordinates (x, y arrays)."""
    x = xs - 0.5
    y = ys - 0.5
    x0 = np.clip(np.floor(x).astype(int), 0, lum.shape[1] - 2)
    y0 = np.clip(np.floor(y).astype(int), 0, lum.shape[0] - 2)
    fx = np.clip(x - x0, 0, 1)
    fy = np.clip(y - y0, 0, 1)
    return (lum[y0, x0] * (1 - fx) * (1 - fy) + lum[y0, x0 + 1] * fx * (1 - fy)
            + lum[y0 + 1, x0] * (1 - fx) * fy + lum[y0 + 1, x0 + 1] * fx * fy)


def edge_profile(restored, rfrac=R_FRAC, rmin=0.84, rmax=1.08, n=241, angles=72):
    """Median radial luminance profile of the restored disc's rim over all angles: (rs in R, median). The restored
    disc's own edge (the enhance step's soft disk, 0.98-0.99 R) is what the eye sees; this measures it."""
    im = restored.convert("L")
    N = im.size[0]
    lum = np.asarray(im).astype(np.float32)
    R = rfrac * N
    rs = np.linspace(rmin, rmax, n)
    th = np.linspace(0, 2 * np.pi, angles, endpoint=False)
    xs = N / 2.0 + np.cos(th)[:, None] * rs[None, :] * R
    ys = N / 2.0 + np.sin(th)[:, None] * rs[None, :] * R
    return rs, np.median(_sample_lum(lum, xs, ys), axis=0)


def _width_1090(rs, prof, plateau):
    """(10-90 % width, 50 % radius) of a falling edge profile, linear interpolation; None if it never falls."""
    hi, lo = 0.9 * plateau, 0.1 * plateau
    ihi = np.where(prof >= hi)[0]
    ilo = np.where(prof <= lo)[0]
    if len(ihi) == 0 or len(ilo) == 0:
        return None
    a, b = int(ihi.max()), int(ilo.min())
    if b <= a:
        return None

    def cross(i0, i1, level):
        p0, p1 = float(prof[i0]), float(prof[i1])
        return float(rs[i0]) if p0 == p1 else float(rs[i0]) + (level - p0) / (p1 - p0) * float(rs[i1] - rs[i0])

    r90 = cross(a, min(a + 1, len(rs) - 1), hi)
    r10 = cross(max(b - 1, 0), b, lo)
    r50 = cross(a, b, 0.5 * plateau)
    return r10 - r90, r50


def restored_edge(restored, rfrac=R_FRAC, target=EDGE_TARGET, e0_min=ZONE_A):
    """The edge of the restored layer: (e0, e1, info). alpha = 1 up to e0 R, smoothstep to 0 at e1 R, and e0 is NEVER inside zone
    A (e0 >= e0_min = 0.95: EN1). A natural edge already wide enough is left alone (F3: 0.985 to 1.015, no visible change, the raw
    pixels already fade); a narrower one is widened, inward down to e0_min and outward up to 1.03 R, toward the 10-90 % width `target`
    of the product. Inside zone B the most the ramp can give is about 0.02-0.03 R (the natural cliff sits at 0.98 R): the brief's
    0.034 R target was measured with a ramp that started inside zone A. The soft A/B variant (owner sign-off D20) passes
    e0_min 0.90 and target 0.048: an explicit, published exception of at most 0.05 R inside zone A.
    Multiplication only: no stroke, no glow, nothing added."""
    rs, prof = edge_profile(restored, rfrac)
    base = float(np.median(prof[(rs > 0.80) & (rs < 0.95)]))
    none = dict(natural=None, final=None, wa=0.0)
    if base < 3.0:
        return F3_LO, F3_HI, none
    idx = np.where(prof >= 0.5 * base)[0]
    r_rough = float(rs[idx.max()]) if len(idx) else 0.98
    win = (rs >= r_rough - 0.045) & (rs <= r_rough - 0.012)
    plateau = float(np.median(prof[win])) if win.any() else base           # the rim level just inside the cliff
    if plateau < 3.0:
        return F3_LO, F3_HI, none
    m = _width_1090(rs, prof, plateau)
    if m is None:
        return F3_LO, F3_HI, none
    w_nat, r50 = m
    leave = EDGE_MIN_NATURAL if target <= EDGE_TARGET + 1e-9 else target
    if w_nat >= leave:
        return F3_LO, F3_HI, dict(natural=w_nat, final=w_nat, wa=0.0, r50=r50)
    best = None
    e0s = [ZONE_A] if e0_min >= ZONE_A - 1e-9 else list(np.arange(ZONE_A, e0_min - 1e-9, -0.005))
    for e0 in e0s:
        for e1 in np.linspace(e0 + 0.01, EDGE_E1_MAX, 161):
            a = 1.0 - smoothstep01((rs - e0) / (e1 - e0))
            f = _width_1090(rs, prof * a, plateau)
            if f is None:
                continue
            err = abs(f[0] - target) + 0.02 * (ZONE_A - e0)            # the nearer to zone B the better on a tie
            if best is None or err < best[0] - 1e-9:
                best = (err, float(e0), float(e1), float(f[0]))
    if best is None:
        return F3_LO, F3_HI, dict(natural=w_nat, final=w_nat, wa=0.0, r50=r50)
    return best[1], best[2], dict(natural=w_nat, final=best[3], wa=best[2] - best[1], r50=r50)


# ----------------------------------------------------------------------------- registration
def _lum(arr):
    a = arr.astype(np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def _gauss1d(sig):
    n = max(1, int(math.ceil(3 * sig)))
    x = np.arange(-n, n + 1, dtype=np.float32)
    k = np.exp(-0.5 * (x / max(sig, 1e-3)) ** 2)
    return k / k.sum()


def _blur(a, sig):
    if sig < 0.3:
        return a
    k = _gauss1d(sig)
    n = len(k) // 2
    p = np.pad(a, ((0, 0), (n, n)), mode="edge")
    o = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(len(k)))
    p = np.pad(o, ((n, n), (0, 0)), mode="edge")
    return sum(k[i] * p[i:i + a.shape[0]] for i in range(len(k)))


def _grad(lum, sig):
    b = _blur(lum, sig)
    gx = np.zeros_like(b)
    gy = np.zeros_like(b)
    gx[:, 1:-1] = 0.5 * (b[:, 2:] - b[:, :-2])
    gy[1:-1] = 0.5 * (b[2:] - b[:-2])
    return gx, gy


def _down(a, f):
    if f == 1:
        return a
    h, w = a.shape[0] // f * f, a.shape[1] // f * f
    return a[:h, :w].reshape(h // f, f, w // f, f, *a.shape[2:]).mean(axis=(1, 3))


def _xcorr_peak(fx1, fy1, fx2, fy2, m1, m2, search):
    """Cross-correlation of two vector fields by FFT: c[d] = sum a[x + d] . b[x]. Its peak d (within |d| <= search px,
    sub-pixel by a parabola) says the features of field 1 sit d away from those of field 2. Returns (dx, dy, ncc)."""
    n = fx1.shape[0]
    a_x, a_y = fx1 * m1, fy1 * m1
    b_x, b_y = fx2 * m2, fy2 * m2
    F = np.fft.rfft2
    corr = np.fft.irfft2(F(a_x) * np.conj(F(b_x)) + F(a_y) * np.conj(F(b_y)), s=(n, n))
    ea = math.sqrt(float((a_x ** 2 + a_y ** 2).sum()) * float((b_x ** 2 + b_y ** 2).sum())) + 1e-9
    corr = np.fft.fftshift(corr) / ea
    c = n // 2
    s = int(search)
    sub = corr[c - s:c + s + 1, c - s:c + s + 1]
    iy, ix = np.unravel_index(int(np.argmax(sub)), sub.shape)
    peak = float(sub[iy, ix])

    def para(v0, v1, v2):
        d = v0 - 2 * v1 + v2
        return 0.0 if abs(d) < 1e-12 else 0.5 * (v0 - v2) / d

    fx = para(sub[iy, ix - 1], sub[iy, ix], sub[iy, ix + 1]) if 0 < ix < 2 * s else 0.0
    fy = para(sub[iy - 1, ix], sub[iy, ix], sub[iy + 1, ix]) if 0 < iy < 2 * s else 0.0
    return (ix - s) + fx, (iy - s) + fy, peak


def _annulus(S, rf, lo, hi, cx, cy):
    d = np.sqrt(((np.arange(S) + 0.5 - cx) ** 2)[None, :] + ((np.arange(S) + 0.5 - cy) ** 2)[:, None]) / (rf * S)
    return ((d >= lo) & (d <= hi)).astype(np.float32)


def _central_square(a):
    """The central W x W square of a W x H array (W < H) so the registration works on any frame."""
    H, W = a.shape[:2]
    if H <= W:
        return a
    y0 = (H - W) // 2
    return a[y0:y0 + W]


def registration(P, Rr, rf=RF, cut=0.5, band=REG_BAND, sigma=0.012, fit_ring=(0.16, 0.90), work=512, search=0.10,
                 pupil=(0.0, 0.0)):
    """Measured registration of the photo layer P and the restored layer Rr (uint8 H x W x 3 on the same frame).
    ring_*: peak of the gradient-direction correlation on the whole annulus 0.16-0.90 R (well conditioned, the number
    the refit uses); band_*: the same restricted to the band +-`band` R_f about the cut (the T16 number, noisier: a
    small area of fibres a generative render has redrawn); off_*: the annulus WITHOUT the band. Offsets are (dx, dy) of
    the PHOTO's features relative to the restored ones, in frame px of P's size; *_offset_rf are hypot / R_f."""
    P, Rr = _central_square(P), _central_square(Rr)
    S = P.shape[0]
    f = max(1, S // work)
    w = S // f
    lp, lr = _down(_lum(P), f), _down(_lum(Rr), f)
    sg = sigma * rf * w
    gpx, gpy = _grad(lp, sg)
    grx, gry = _grad(lr, sg)
    ring = _annulus(w, rf, fit_ring[0], fit_ring[1], w / 2.0 - pupil[0] * rf * w, w / 2.0 - pupil[1] * rf * w)
    xs = (np.arange(w) + 0.5) / w
    bandm = (np.abs(xs - cut)[None, :] <= band * rf).astype(np.float32) * np.ones((w, 1), np.float32)
    srch = max(2, int(round(search * rf * w)))
    res = {}
    rpx = rf * S
    for name, m in (("ring", ring), ("band", ring * bandm), ("off", ring * (1.0 - bandm))):
        dx, dy, ncc = _xcorr_peak(gpx, gpy, grx, gry, m, m, srch)
        res[name + "_dx"], res[name + "_dy"], res[name + "_ncc"] = dx * f, dy * f, ncc
        res[name + "_offset_rf"] = math.hypot(dx * f, dy * f) / rpx
    return res


def _half_offsets(A, B, rfrac, work, ncc_min):
    """Translation estimates of four half-annuli (left, right, top, bottom) of the crop / restored pair, in iris radii:
    {name: (dx, dy, ncc)}. The restored render must be one rigid copy of the crop, so the halves agree; when they do not
    (a redrawn half, a rotated or scaled render) no single shift registers the two."""
    la, lb = _lum(A), _lum(B)
    sg = 0.012 * rfrac * work
    gax, gay = _grad(la, sg)
    gbx, gby = _grad(lb, sg)
    ring = _annulus(work, rfrac, 0.16, 0.90, work / 2.0, work / 2.0)
    t = (np.arange(work) + 0.5) / work
    masks = {"L": ring * (t < 0.5)[None, :], "R": ring * (t >= 0.5)[None, :],
             "T": ring * (t < 0.5)[:, None], "B": ring * (t >= 0.5)[:, None]}
    R = rfrac * work
    srch = max(2, int(round(0.10 * R)))
    out = {}
    for k, m in masks.items():
        dx, dy, ncc = _xcorr_peak(gax, gay, gbx, gby, m, m, srch)
        out[k] = (dx / R, dy / R, ncc)
    return out


def align_crop(crop, restored, work=256, rfrac=R_FRAC):
    """Server side registration in CROP space: the client (or deglared) crop and its restored iris are squares of the
    same frame, so no photo mapping is needed. Returns (shift_r, info): shift_r = the translation of the PHOTO layer
    in iris radii that puts it on the restored one (pass as photo_layer(shift_r=)); (0, 0) when the correlation is
    weak (ncc < REG_NCC_MIN) or the shift is implausible (> 0.06 R). work: the side the pair is compared at.
    info.spread_r: how far the four half-annuli disagree about that shift (a rigid copy gives 0 within noise);
    info.ok: the T16 verdict, the page may show the cut only when it is True: correlation at least REG_NCC_MIN, every half
    correlating, spread <= REG_SPREAD_OK (0.005 R: no part of the frame is more than about 1 px off at the hero's size)."""
    a = np.asarray(crop.convert("RGB").resize((work, work), Image.LANCZOS))
    b = np.asarray(restored.convert("RGB").resize((work, work), Image.LANCZOS))
    r = registration(a, b, rfrac, work=work)        # in crop space the iris radius is rfrac of the side
    R = rfrac * work
    dx, dy = -r["ring_dx"] / R, -r["ring_dy"] / R    # correction = minus the measured offset
    usable = r["ring_ncc"] >= REG_NCC_MIN and math.hypot(dx, dy) <= SHIFT_MAX
    sh = (float(dx), float(dy)) if usable else (0.0, 0.0)
    hv = _half_offsets(a, b, rfrac, work, REG_NCC_MIN)
    good = {k: v for k, v in hv.items() if v[2] >= REG_NCC_MIN * 0.5}
    spread = 0.0
    for p, q in (("L", "R"), ("T", "B")):
        if p in good and q in good:
            spread = max(spread, math.hypot(good[p][0] - good[q][0], good[p][1] - good[q][1]))
    ok = bool(usable and len(good) == 4 and spread <= REG_SPREAD_OK)
    return sh, dict(ncc=float(r["ring_ncc"]), measured_r=(float(-dx), float(-dy)), applied=bool(usable),
                    offset_r=float(math.hypot(dx, dy)), spread_r=float(spread), ok=ok)


# ----------------------------------------------------------------------------- server hand-off
def reveal_params(crop, restored, kind="human", lid=None, iris_aspect=1.0, lid_on=True):
    """The small dict the server hands to the page next to the display copy, all measured on the CLEAN restoration and the client
    crop (the display copy's watermark would disturb every one of the measurements):
      pupil [px, py] (iris radii, right / down), rho (pupil radius, iris radii), cls (round | slit | bar | None),
      shift [sx, sy] (translation of the photo layer, iris radii), edge [e0, e1] (alpha 1 up to e0 R, 0 from e1 R, e0 >= 0.95),
      ok (registration trusted AND colour drift <= 8: False = the page shows the strip without the cut, 4.5),
      soft (fewer than 100 photo px per iris radius: the page adds "move closer"), drift (dE00 photo vs restoration),
      lid (share of the disc hidden), ia (iris aspect of an oval eye, only when not 1).
    kind "pet": the pupil comes from the dark-blob detector. lid: lid lines from /api/analyze ([(side, xk, bk)]).
    The private keys (_pupil, _lid, _info) carry the masks prepare_restored() needs; public_params() drops them."""
    pi = pupil_info(restored, kind)
    sh, reg = align_crop(crop, restored)
    lid_soft, lid_share, lid_info = (CL.lid_mask(restored, lid, pi) if lid_on else (np.zeros((CL.WORK, CL.WORK), np.float32), 0.0, {}))
    drift, dinfo = CL.colour_drift(crop, restored, lid_soft if lid_share > 0 else None)
    ia = _clampf(iris_aspect, 1.0, 2.0, 1.0)
    e0, e1, einfo = restored_edge(restored) if ia <= 1.0001 else (F3_LO, F3_HI, dict(natural=None, final=None, wa=0.0))
    px_per_r = crop.size[0] * R_FRAC
    ok = bool(reg["ok"] and drift <= DRIFT_FAIL)
    out = dict(pupil=[round(pi["cx"], 4), round(pi["cy"], 4)], rho=None if not pi["rho"] else round(pi["rho"], 4), cls=pi["cls"],
               shift=[round(sh[0], 4), round(sh[1], 4)], edge=[round(e0, 4), round(e1, 4)], ok=ok,
               soft=bool(px_per_r < SOFT_PX_PER_R), drift=round(drift, 1), lid=round(lid_share, 4))
    if ia > 1.0001:
        out["ia"] = round(ia, 3)
    out["_pupil"] = pi
    out["_lid"] = lid_soft
    out["_info"] = dict(reg=reg, edge=einfo, drift=dinfo, lid=lid_info, px_per_r=px_per_r, reg_ok=bool(reg["ok"]), drift_warn=drift > DRIFT_WARN)
    return out


def public_params(p):
    """reveal_params without the private diagnostics: exactly what goes over the wire (about 140 bytes)."""
    return {k: v for k, v in p.items() if not k.startswith("_")}


def prepare_restored(restored, params, pupil_mode="crush", lid=True):
    """The restored image as the Reveal shows it (PIL RGB, same size): the lid hidden (black) and the pupil made pure black
    (luma x 0.12, chroma 0, its own shape kept), everything else byte for byte the restoration. pupil_mode: "crush" (default: the
    brief's pure black), "colourless" (the pupil keeps its luminance and loses its colour, what the studio grade does to the art),
    "restored" (as the restoration made it). The masks are params["_lid"], params["_pupil"]; both are also what the hash tests exclude."""
    im = restored.convert("RGB")
    if lid and params.get("_lid") is not None:
        im = CL.apply_lid(im, params["_lid"])
    info = params.get("_pupil")
    if pupil_mode == "crush":
        im = CL.crush_pupil(im, info)
    elif pupil_mode == "colourless":
        im = CL.crush_pupil(im, info, luma=1.0)
    return im


# ---- hand written below this line (scripts/styles_tests/port_reveal.py leaves it alone) --------------------
REVEAL_MIN_LEFT = 4.0        # seconds left in the invocation (after the profile) that /api/enhance asks of the Reveal's measurement: it is about 0.5 s of
                             # work on a quiet core (0.25 s for the parameters, 0.2 s for the prepared and watermarked copy), twice that on a slow one
PAD_TOL = 0.005              # the measurements above are made at the site's crop padding (PAD: R_FRAC, the pupil detector, the frame the page cuts); a request that says another
                             # padding (the body's "pad" is allowed anywhere in 1 to 2) gets no Reveal, and with it the plain display copy, never numbers measured on the wrong radius
CODES = ("ok", "colour", "registration", "none", "error")   # what the event says about one eye's Reveal (events.FIELDS["enhance"]["reveal"])


def time_for_reveal(left=None):
    """Is there time in this invocation to measure the Reveal (the guard of /api/enhance)? left: seconds, default L.time_left()."""
    return (L.time_left() if left is None else left) >= REVEAL_MIN_LEFT


def wire(p):
    """The public part of reveal_params as it goes over the wire: no private masks, and no negative zero (a measured offset of
    minus one ten thousandth rounds to -0.0, which JSON would print as "-0.0"). Every number is finite or this raises ValueError:
    one NaN in the reply would make the whole /api/enhance answer unparseable in the browser and lose the paid preview, so reveal_for
    turns it into "not measured" (the plain slider) instead."""
    out = {}
    for k, v in public_params(p).items():
        if isinstance(v, (list, tuple)):
            v = [x + 0.0 if isinstance(x, float) else x for x in v]
        elif isinstance(v, float):
            v = v + 0.0
        if any(isinstance(x, float) and not math.isfinite(x) for x in (v if isinstance(v, list) else [v])):
            raise ValueError("a Reveal number is not finite: " + k)
        out[k] = v
    return out


def standard_pad(pad):
    """True when `pad` (the crop padding a request says its crop was cut with) is the site's, within PAD_TOL: the one padding the Reveal is measured at.
    None means the site's padding. NaN, infinity and anything that is not a number are not standard (a comparison with NaN is never true)."""
    if pad is None:
        return True
    try:
        return abs(float(pad) - PAD) <= PAD_TOL
    except (TypeError, ValueError):
        return False


def shown_copy(prepared, lang, style="repo", pad=None):
    """The display copy of the prepared restoration, its watermark anchored to the iris disc of the padding the eye was cut with, exactly where the seals, the
    profile and every tile of this eye carry it (preview.display_image takes the padding and places the overlay on the disc). display_copy above is the
    prototype's own and knows no padding: the repo tile goes through here, the arcs variant (D14, off) through display_copy. pad is rounded to the thousandths
    the eye profile keeps, so a measured profile and this copy name the same disc."""
    if style != "repo":
        return display_copy(prepared, lang, style)
    from .. import preview as PV
    p = PAD if pad is None else int(round(float(pad) * 1000)) / 1000.0
    return PV.display_image(prepared.convert("RGB"), lang, p)


def code_of(pub):
    """The event code of a reveal_params reply: ok (the page shows the cut), colour (withheld: the restored colour drifted from the photo by
    more than DRIFT_FAIL), registration (withheld: the halves of the iris do not agree about one rigid shift, or the correlation is weak)."""
    if pub.get("ok"):
        return "ok"
    return "colour" if (pub.get("drift") or 0.0) > DRIFT_FAIL else "registration"


def display_b64(shown):
    """The display copy as /api/enhance sends it: JPEG at the preview's quality, carrying the preview's display mark in its comment (so the server can
    tell a display copy from a clean preview, preview.is_display), exactly as preview.display_b64 writes it."""
    from .. import preview as PV
    buf = io.BytesIO()
    shown.save(buf, "JPEG", quality=PV.DISPLAY_QUALITY, comment=PV.DISPLAY_MARK)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def reveal_for(crop, restored, lang=None, left=None, pad=None, style="repo"):
    """What /api/enhance does for the Reveal, in one call that never raises and never costs the preview.
    crop: the deglared crop this restoration was made from (the colour reference of enhance), restored: the clean restoration (PIL).
    pad: the crop padding the request says it cut with (None: the site's). The Reveal is measured at the site's padding only (standard_pad): any other
    padding is "not measured", and the display copy of a measured eye has its watermark on the disc of that padding (shown_copy).
    Returns {"params": the wire dict or None, "image": the display copy (PIL, the prepared restoration under the preview watermark) or
    None, "code": one of CODES, "ms": the time it took}. None for params and image means "not measured": the page then keeps the plain
    before and after slider and the display copy is the plain one (no eyelid hidden, no pupil crushed). A withheld Reveal (ok false)
    still comes back with its params and its prepared copy: the page shows the strip without the cut, and tells the customer why."""
    t0 = time.time()
    if not time_for_reveal(left) or not standard_pad(pad):
        return {"params": None, "image": None, "code": "none", "ms": 0}
    try:
        p = reveal_params(crop, restored)
        pub = wire(p)
        shown = shown_copy(prepare_restored(restored, p), lang or L.page_lang(), style, pad)
    except Exception as e:  # noqa: a broken measurement must never cost the customer's preview
        print("snapeyes reveal: not measured:", L._scrub(repr(e))[:200], flush=True)
        return {"params": None, "image": None, "code": "error", "ms": int((time.time() - t0) * 1000)}
    return {"params": pub, "image": shown, "code": code_of(pub), "ms": int((time.time() - t0) * 1000)}
