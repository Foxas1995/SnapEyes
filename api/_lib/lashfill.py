# -*- coding: utf-8 -*-
"""Dark lash curtains over the iris: measured on the deglared crop, repaired from the iris itself only where measured.

A curtain is lash shadow, lash fringe or a lash line lying on the iris disk in the photo. No lid skin shows, so the
eyelid gate (coverage.py, L.lid_mask) does not see it, and /api/enhance takes a defined dark mass for iris structure
(it keeps it) and a soft one for fibres to paint over, at random between two renders of one input (wave-q3 lashes).

Gate (scan). In a 70 degree window at the top or the bottom of the disk, the mid ring (LF_RING, iris radii) is darker
than the rest of the disk at the same radius (the far arc: all but the window and 30 degrees round it). A curtain hangs
into the iris, so it is dark deep in the ring; lid shade, a lash cap and a dark upper iris are darkest at the rim and
fade inwards. Armed when at least LF_ARM_SHARE of the ring's cells are LF_D L* darker AND their mean deficit is at
least LF_ARM_MEAN. Calibrated on the 43 saved analyze crops of wave-q3 (lashes, builder A): the 23 frames labelled clean
(the owner's 4 eyes and both samples among them) never arm it, at the crop as it is or with the circle moved 4-8 %,
scaled 0.85-1.15 and the pupil 0.7-1.4 x (0 of 437 runs); the real curtains 11 and 29 do, and so do the lid frames
the eyelid gate already stops. A crop the gate does not arm comes back as the very same object (byte identical); its
cost is one 256 px luma read (about 0.03-0.05 s).

Mask (curtain_mask), armed crops only, inside LF_REACH degrees of the window: thin dark lines (black top-hat, LF_BH, with
their fading tails, LF_WEAK) and very dark pixels (LF_T_HI below the far arc's tone at that radius), closed, nothing else:
the iris between the strokes, however shaded, is left as the photo has it.
Fill (curtain_fill): the lid path of /api/deglare (mirror_prefill with LID_EXTRA_DONORS, composite, lid_composite with
the fibre band of single donors) at LF_FILL_SIDE, laid back through the mask's soft edge: the pixels come from the same
person's iris at the same radius, never from the model. Three guards leave the crop as it was: the fill's lid_drift
above LF_DRIFT_MAX, a second mask pass that still finds more than LF_RESID of the strokes (a half repaired curtain is
worse than the photo), and a mask that no honest fill can cover (below).

Verdicts (info["verdict"], also the reply's "curtain"): None quiet gate (no "curtain" key at all); "fill" repaired;
"skip_lid" the lid fill already ran (lid_pct > 0); "small" (mask under LF_MIN of the disk); "too_big": the mask is wider
than LF_CAP[0] of the disk, or its angular runs wider than LF_WIDE (no clean iris beside them) cover more than LF_CAP[1],
or the lid gate's discarded margin (L.lid_geometry, LID_DEEP_STEP: hanging lashes) covers LF_COVER of the disk: a fill
would be another sector's iris, so the crop is left alone and the photo is a retake candidate (the "eyelid" reason);
"partial" and "no_donor" the two guards above; "error" (never stops the restoration).
"""
import os
import time
import warnings
import numpy as np
from PIL import Image, ImageFilter
from . import iris as L

# SNAPEYES_CURTAIN=off (or 0/false/no) switches the whole stage off without a deploy (the BOM strip is for values set from PowerShell)
LF_ON = (os.environ.get("SNAPEYES_CURTAIN") or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no")
# gate
LF_SIDE = 256              # the gate reads a copy this size
LF_NR, LF_NT = 48, 240     # polar grid of the gate: radial bins over LF_R, angular bins of 1.5 degrees
LF_R = (0.25, 0.985)       # iris radii
LF_WIN = 70.0              # window width, degrees
LF_STEP = 15               # window centres every this many degrees (top 225..315, bottom 45..135)
LF_RING = (0.50, 0.70)     # the ring the gate reads, iris radii: the curtain hangs into it, rim shade does not
LF_D = 15.0                # a cell this many L* darker than the far arc at its radius is dark
LF_ARM_SHARE = 0.75        # armed when this share of the window's ring cells is dark...
LF_ARM_MEAN = 24.0         # ...and their mean deficit (L*) is at least this
LF_FAR_PAD = 30.0          # the far arc leaves out the window and this many degrees round it
# mask
LF_REACH = 75.0            # the mask looks this far either side of the armed window's centre, degrees
LF_BH = 14.0               # a thin dark line: black top-hat (closing with a 9 px element at 256 px) above this...
LF_BH_D = 5.0              # ...where the pixel is also at least this much darker than the far arc at its radius
LF_WEAK = (8.0, 10.0)      # the tail of a thin stroke: top-hat and deficit (L*); taken when it touches a strong pixel
LF_GROW = 3                # ...up to this many px (at 256) from it
LF_T_HI = 28.0             # a very dark pixel: this many L* darker than the far arc at its radius
LF_R_MASK = (0.30, 0.97)   # the mask stays in this part of the disk (and outside the pupil + 0.04)
LF_CLOSE = 2               # the mask is closed by this many px at 256, then grown by one
LF_WIDE = 25.0             # a masked run wider than this (degrees at one radius) has no clean iris beside it...
LF_CAP = (20.0, 3.0)       # ...too_big when the mask passes the first share of the disk (%), or the wide runs the second
LF_MIN = 1.5               # a mask smaller than this share of the disk (%) is not worth a fill ("small")
LF_COVER = 12.0            # a lid margin / lash line across the iris this wide (% of the disk) is beyond repair
LF_MARGIN_GRID = 81
# fill
LF_FILL_SIDE = 384         # the lid path runs on a copy this size (the fill is smooth, the model redraws the fibres); 448: +0.7 s, same fidelity
LF_DRIFT_SIDE = 256        # lid_drift (medians of radius bands) is read on copies this size
LF_DRIFT_MAX = 12.0        # the fill's lid_drift (colour moved from the iris round it, dE76) above this: not applied
LF_RESID = 0.35            # a fill that leaves more than this share of the mask's strokes in place is partial
LF_SOFT = 2.0              # mask feather, px at 512 (as the lid mask: 2 x blur radius)


def _lstar256(crop, side=LF_SIDE):
    """L* of the crop at side px, and the max channel (black = outside the photo)."""
    im = crop.convert("RGB")
    im = im.resize((side, side), Image.BOX if im.size[0] >= side else Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255.0
    lin = np.where(a > 0.04045, ((a + 0.055) / 1.055) ** 2.4, a / 12.92)
    y = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    f = np.where(y > 0.008856, np.cbrt(y), 7.787 * y + 16 / 116.0)
    return (116 * f - 16).astype(np.float32), a.max(-1)


_POLAR = {}


def _polar_index(side, pad):
    key = (side, round(pad, 4))
    if key not in _POLAR:
        R = side / (2.0 * pad)
        rr = np.linspace(LF_R[0], LF_R[1], LF_NR)
        th = (np.arange(LF_NT) + 0.5) * 360.0 / LF_NT
        X = side / 2.0 + rr[:, None] * R * np.cos(np.radians(th))[None, :] - 0.5
        Y = side / 2.0 + rr[:, None] * R * np.sin(np.radians(th))[None, :] - 0.5
        x0 = np.clip(np.floor(X).astype(np.int32), 0, side - 2)
        y0 = np.clip(np.floor(Y).astype(np.int32), 0, side - 2)
        fx, fy = (X - x0).astype(np.float32), (Y - y0).astype(np.float32)
        _POLAR.clear() if len(_POLAR) > 8 else None
        _POLAR[key] = (rr.astype(np.float32), th.astype(np.float32), x0, y0, fx, fy)
    return _POLAR[key]


def _sample(A, idx):
    _, _, x0, y0, fx, fy = idx
    return (A[y0, x0] * (1 - fx) * (1 - fy) + A[y0, x0 + 1] * fx * (1 - fy)
            + A[y0 + 1, x0] * (1 - fx) * fy + A[y0 + 1, x0 + 1] * fx * fy)


def _windows():
    return ((("top", c) for c in range(225, 316, LF_STEP)), (("bottom", c) for c in range(45, 136, LF_STEP)))


def _ref_profile(Lp, valid, far):
    """Median of the far arc per radial bin (NaN where fewer than 10 cells), interpolated over the gaps."""
    m = valid & far[None, :]
    cnt = m.sum(1)
    Lm = np.where(m, Lp, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        ref = np.nanmedian(Lm, axis=1)
    ok = cnt >= 10
    if not ok.any():
        return None
    idx = np.arange(Lp.shape[0])
    return np.interp(idx, idx[ok], ref[ok]).astype(np.float32)


def scan(crop, pad, pupil_rho):
    """The gate's reading of a deglared crop: the best top and the best bottom window.
    Returns {"top": w, "bottom": w, "armed": w or None} with w = dict(side, c, share, mean, n) (None where a window
    has too few cells)."""
    Ls, mx = _lstar256(crop)
    idx = _polar_index(Ls.shape[0], pad)
    rr, th = idx[0], idx[1]
    Lp, mp = _sample(Ls, idx), _sample(mx, idx)
    lo = max(0.45, (pupil_rho or 0.25) + 0.06)
    valid = (Lp < 86.0) & (mp > 0.05) & (rr[:, None] > lo) & (rr[:, None] < 0.92)
    ring = valid & (rr[:, None] >= LF_RING[0]) & (rr[:, None] < LF_RING[1])
    best = {"top": None, "bottom": None}
    for gen in _windows():
        for side, c in gen:
            w = ((th - (c - LF_WIN / 2)) % 360.0) <= LF_WIN
            far = ~(((th - (c - LF_WIN / 2 - LF_FAR_PAD)) % 360.0) <= LF_WIN + 2 * LF_FAR_PAD)
            ref = _ref_profile(Lp, valid, far)
            if ref is None:
                continue
            s = ring & w[None, :]
            n = int(s.sum())
            if n < 15:
                continue
            d = (ref[:, None] - Lp)[s]
            r = dict(side=side, c=c, share=float((d > LF_D).mean()), mean=float(d.mean()), n=n)
            if best[side] is None or r["share"] > best[side]["share"]:
                best[side] = r
    armed = None
    for side in ("top", "bottom"):
        w = best[side]
        if w and w["share"] >= LF_ARM_SHARE and w["mean"] >= LF_ARM_MEAN:
            if armed is None or w["share"] > armed["share"]:
                armed = w
    best["armed"] = armed
    return best




_CART = {}


def _cart_grid(side, pad):
    key = (side, round(pad, 4))
    if key not in _CART:
        ax = np.arange(side) + 0.5 - side / 2.0
        X, Y = np.meshgrid(ax, ax)
        R = side / (2.0 * pad)
        _CART.clear() if len(_CART) > 8 else None
        _CART[key] = (np.hypot(X, Y) / R, (np.degrees(np.arctan2(Y, X)) + 360.0) % 360.0)
    return _CART[key]


def _blackhat(Lu, r):
    """closing(Lu, (2r+1)^2) - Lu, from running max / min along both axes (thin dark strokes stand out)."""
    def run(a, fn):
        for ax in (0, 1):
            n = a.shape[ax]
            p = np.pad(a, [(r, r) if x == ax else (0, 0) for x in (0, 1)], mode="edge")
            acc = np.take(p, np.arange(0, n), axis=ax).copy()
            for s in range(1, 2 * r + 1):
                fn(acc, np.take(p, np.arange(s, s + n), axis=ax), out=acc)
            a = acc
        return a
    return run(run(Lu, np.maximum), np.minimum) - Lu


def _wide_share(m, rho, ang, nt=360):
    """Share of the disk covered by masked cells that sit in an angular run wider than LF_WIDE at their radius."""
    nb = 40
    rb = np.clip((rho / 1.0 * nb).astype(np.int32), 0, nb - 1)
    ab = np.clip((ang / (360.0 / nt)).astype(np.int32), 0, nt - 1)
    grid = np.zeros((nb, nt), np.float32)
    np.add.at(grid, (rb[m], ab[m]), 1.0)
    cnt = np.zeros((nb, nt), np.float32)
    np.add.at(cnt, (rb[rho < 1.0], ab[rho < 1.0]), 1.0)
    frac = grid / np.maximum(cnt, 1.0)
    on = frac > 0.5
    wide = np.zeros((nb, nt), bool)
    need = int(round(LF_WIDE / (360.0 / nt)))
    for i in range(nb):
        row = on[i]
        if not row.any():
            continue
        if row.all():
            wide[i] = True
            continue
        s = int(np.argmin(row))                     # start the scan at a clear cell, runs wrap round
        rot = np.roll(row, -s)
        j = 0
        while j < nt:
            if rot[j]:
                k = j
                while k < nt and rot[k]:
                    k += 1
                if k - j >= need:
                    wide[i, (np.arange(j, k) + s) % nt] = True
                j = k
            else:
                j += 1
    wm = wide[rb, ab] & m
    return 100.0 * float(wm.sum()) / max(1.0, float((rho < 1.0).sum()))


def curtain_mask(crop, pad, pupil_rho, armed):
    """The pixels to repair, on the 256 px grid: bool array (LF_SIDE x LF_SIDE) and a dict of measures.
    Thin dark lines (lash shadow, lashes) and very dark pixels inside the armed window's arc, nothing else: the
    iris between them, however shaded, is left as the photo has it."""
    Ls, mx = _lstar256(crop)
    side = Ls.shape[0]
    idx = _polar_index(side, pad)
    rr, th = idx[0], idx[1]
    Lp, mp = _sample(Ls, idx), _sample(mx, idx)
    lo = max(0.45, (pupil_rho or 0.25) + 0.06)
    valid = (Lp < 86.0) & (mp > 0.05) & (rr[:, None] > lo) & (rr[:, None] < 0.92)
    c = armed["c"]
    far = ~(((th - (c - LF_WIN / 2 - LF_FAR_PAD)) % 360.0) <= LF_WIN + 2 * LF_FAR_PAD)
    ref = _ref_profile(Lp, valid, far)
    rho, ang = _cart_grid(side, pad)
    inreg = np.abs((ang - c + 180.0) % 360.0 - 180.0) <= LF_REACH
    d = np.interp(rho, rr, ref) - Ls
    ok = (rho > max(LF_R_MASK[0], (pupil_rho or 0.25) + 0.04)) & (rho < LF_R_MASK[1]) & (mx > 0.05) & (Ls < 86.0)
    bh = _blackhat(Ls, 4)
    m = ok & inreg & (((bh >= LF_BH) & (d >= LF_BH_D)) | (d >= LF_T_HI))
    weak = ok & inreg & (bh >= LF_WEAK[0]) & (d >= LF_WEAK[1])
    g = m.copy()
    for _ in range(LF_GROW):                 # hysteresis: a stroke's fading tail joins its strong part
        g = (np.asarray(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0) & weak | m
    m = g
    mi = Image.fromarray((m * 255).astype(np.uint8))
    if LF_CLOSE:
        mi = mi.filter(ImageFilter.MaxFilter(2 * LF_CLOSE + 1)).filter(ImageFilter.MinFilter(2 * LF_CLOSE + 1))
    mi = mi.filter(ImageFilter.MaxFilter(3))
    m = (np.asarray(mi) > 0) & ok & inreg
    disc = rho < 1.0
    info = dict(mask_pct=100.0 * float(m.sum()) / max(1.0, float(disc.sum())), wide_pct=_wide_share(m, rho, ang))
    return m, info




def _soft_masks(m256, side):
    """Hard (uint8 0/255) and feathered (float32 0..1) masks at `side` from the 256 px mask."""
    hard = np.asarray(Image.fromarray((m256 * 255).astype(np.uint8)).resize((side, side), Image.BILINEAR))
    hard = (hard > 127).astype(np.uint8) * 255
    hb = (hard > 0).astype(np.float32)
    soft = np.clip(2.0 * L._blur_f(hb, LF_SOFT * side / 512.0), 0.0, 1.0)
    return hard, np.maximum(soft, hb).astype(np.float32)


def curtain_fill(crop, m256, r_px, prho):
    """The lid path over the curtain mask. Returns (new crop or None, lid_drift). None: the guard refused (no clean
    iris at the same radius to borrow from). Pixels outside the soft mask come back as they were."""
    S = crop.size[0]
    side = min(S, LF_FILL_SIDE)
    small = crop if side == S else crop.resize((side, side), Image.BOX)
    k = side / float(S)
    hard, feather = _soft_masks(m256, side)
    filled = L.mirror_prefill(small, feather, L.LID_EXTRA_DONORS)
    base = L.composite(small, filled, feather)
    ds = min(side, LF_DRIFT_SIDE)
    if ds < side:
        dk = ds / float(side)
        sm = lambda im: im.resize((ds, ds), Image.BOX)
        hd = np.asarray(Image.fromarray(hard).resize((ds, ds), Image.NEAREST))
        drift = L.lid_drift(sm(small), sm(base), hd, np.zeros((ds, ds), np.uint8), r_px * k * dk)
    else:
        drift = L.lid_drift(small, base, hard, np.zeros((side, side), np.uint8), r_px * k)
    if drift > LF_DRIFT_MAX:
        return None, drift
    out = L.lid_composite(small, filled, hard, feather, r_px * k, prho, glare_hard=None)
    if side == S:
        return out, drift
    a_big = _soft_masks(m256, S)[1][..., None]
    up = lambda im: np.asarray(im.resize((S, S), Image.BICUBIC), np.float32)
    o, s0 = up(out), up(small)
    c = np.asarray(crop.convert("RGB"), np.float32)
    res = c + (1.0 - a_big) * (o - s0) + a_big * (o - c)
    return Image.fromarray(np.clip(res + 0.5, 0, 255).astype(np.uint8)), drift




def margin_cover(raw, r_frac, pupil_rho, glare_hard=None):
    """The share (%) of the iris disk beyond the deepest lid margin lid_geometry accepted, per side (max of both).
    lid_geometry then drops a weak deep margin (LID_DEEP_STEP: hanging lashes) and returns no lid, so this is how a
    lash line that the lid gate discarded is still counted. raw: the unmasked square."""
    dbg = []
    L.lid_geometry(raw, r_frac, glare_hard, dbg, pupil_rho)
    g = np.linspace(-1.0, 1.0, LF_MARGIN_GRID)
    X, Y = np.meshgrid(g, g)
    disc = X * X + Y * Y < 1.0
    best = 0.0
    for dd in dbg:
        if dd.get("ok") is not True or "c" not in dd:
            continue
        c0, c1, c2 = (float(v) for v in dd["c"])
        yb = c0 + c1 * X + c2 * X * X
        best = max(best, 100.0 * float(((Y < yb) & disc).sum()) / float(disc.sum()))
    return best


def _fix(crop, pad, pupil_rho, lid_pct, raw, glare_hard, info):
    sc = scan(crop, pad, pupil_rho)
    armed = sc["armed"]
    if armed is None:
        return crop, None
    info.update(side=armed["side"], c=armed["c"], share=round(armed["share"], 3), mean=round(armed["mean"], 1))
    if lid_pct and lid_pct > 0:
        info["verdict"] = "skip_lid"
        return crop, info
    m, mi = curtain_mask(crop, pad, pupil_rho, armed)
    info.update(mask_pct=round(mi["mask_pct"], 2), wide_pct=round(mi["wide_pct"], 2))
    if mi["mask_pct"] < LF_MIN:
        info["verdict"] = "small"
        return crop, info
    if mi["mask_pct"] > LF_CAP[0] or mi["wide_pct"] > LF_CAP[1]:
        info["verdict"] = "too_big"
        return crop, info
    if raw is not None:
        info["cover"] = round(margin_cover(raw, L.iris_radius_frac(pad), pupil_rho, glare_hard), 1)
        if info["cover"] >= LF_COVER:
            info["verdict"] = "too_big"
            return crop, info
    out, drift = curtain_fill(crop, m, L.iris_radius_frac(pad) * crop.size[0], pupil_rho)
    info["drift"] = round(float(drift), 1)
    if out is None:
        info["verdict"] = "no_donor"
        return crop, info
    m2, mi2 = curtain_mask(out, pad, pupil_rho, armed)
    info["resid"] = round(mi2["mask_pct"] / max(mi["mask_pct"], 1e-6), 2)
    if info["resid"] > LF_RESID:          # a half repaired curtain is worse than the photo as it is
        info["verdict"] = "partial"
        return crop, info
    info["verdict"] = "fill"
    return out, info


def curtain_fix(crop, pad, pupil_rho, lid_pct=0.0, raw=None, glare_hard=None):
    """The whole stage, for /api/deglare: (crop, info). Quiet gate: the very same crop object and info None. Otherwise
    info = dict(verdict, side, c, share, mean, mask_pct, wide_pct, cover, drift, resid, secs); see the module text.
    lid_pct: the lid fill's share of the disk (above 0 the lid path already ran); raw: the unmasked square and
    glare_hard the glare mask, as /api/deglare has them (they let lid_geometry's discarded margin count as a lash line)."""
    if pupil_rho is None or not LF_ON:
        return crop, None
    t0 = time.perf_counter()
    info = dict(verdict=None)
    try:
        out, info = _fix(crop, pad, pupil_rho, lid_pct, raw, glare_hard, info)
    except Exception as e:                   # an optional repair never stops the restoration
        return crop, dict(verdict="error", error=type(e).__name__)
    if info is not None:
        info["secs"] = round(time.perf_counter() - t0, 2)
    return out, info
