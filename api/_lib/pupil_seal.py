# -*- coding: utf-8 -*-
"""The last look at the pupil of the model's render (api/enhance.py): two repairs, each behind its own measurement, numpy and PIL only.
The image model draws the pupil at random. Nearly every render is right and comes back from here as the very same object (the graded
final is then byte-identical); the two defects below are the ones the colour lock and the pupil lock cannot reach.
Kill switches (read once at import, BOM-safe like SNAPEYES_DEGLARE_MODEL; off, 0, false or no): SNAPEYES_PUPIL=off switches every
repair of this round off (this module and api/_lib/pupilgeo.py), SNAPEYES_PUPIL_HALO and SNAPEYES_PUPIL_ZONE switch these two.

1. HALO (seal). A smooth, flat, lit annulus round a pupil the model drew too small (test photo 13: a grey ring 0.06 iris
   radii wide that the colour lock turned into a red ring; 25: a white glow out to the real pupil edge). pupil_lock misses it
   (it wants iris painted ALL round the photo's pupil), _pupil_rim re-colours pixels only, and the grade flattens only inside
   the radius it measures. Estimator: the render's own pupil circle (pupil_circle), then in 24 sectors the annulus just
   outside its edge (HALO_NEAR) is a halo sector when it is lit (median luma at least the larger of HALO_LIT_MIN and HALO_LIT of
   the iris beyond it, HALO_FAR) AND far smoother than that iris (fibre-band std under HALO_SMOOTH of its). Gate: the share of
   the measured sectors that are halo (halo_frac) at least HALO_MIN on at least HALO_SECTORS sectors, and, when the photo has
   a pupil circle, the render's pupil smaller than the photo's by PHOTO_SMALLER. Repair: each sector's halo ends where
   its radial profile ends (the fibre-band std reaches HALO_FIBRE, the luma falls under 0.6 of the plateau, or, where the halo
   is HALO_BRIGHT times brighter than the iris beyond it, at the step down the model drew at the real pupil edge); the glow
   ends on one circle, which is fitted (it need not share the black disk's centre), so a sector with a narrower halo, or
   none, is sealed to that circle; the band is taken to the pupil's own tone (never above HALO_TONE_MAX, never brighter than
   it was) over a soft edge. No fibre texture beyond the halo is touched, nothing is painted that the render did not have.

2. ZONE (seal). On a photo that is almost black (test photo 17: luma 5 to 8 round the pupil) chroma_lock multiplies noise
   chroma by the model's lift and lays a colourless blue-grey zone over a brown iris (the raw render is clean). A near-black
   photo is not evidence of colour. Estimator: the median luma of the model's input over the zone (ZONE) under ZONE_SRC_MAX,
   and the zone's (a*, b*) shift from the raw render, less the same shift on the outer ring, at least ZONE_EXCESS.
   Repair: the zone takes the chroma of the iris ring beyond it (the colour the photo does carry), blended out over ZONE_FADE; luma untouched.

The measurement costs 0.04 to 0.05 s on a render that passes both gates, 0.13 to 0.15 s where one repairs (idle machine, 1024 px).
Any failure returns the render as it came.

Not handled here: lobes of the room reflected inside a pupil the fill disc missed, and the white crescent of the reflected
window beside it (test photo 25, about one render in five); a pupil drawn larger than the photo's; a genuine catchlight (the
grade flattens them all by design)."""
import os, math, json
import numpy as np
from PIL import Image
from . import iris as L


def _on(*names):
    """True unless one of these environment variables says off, 0, false or no (read once at import; the BOM strip is for
    values set from PowerShell)."""
    return all((os.environ.get(n) or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no") for n in names)


HALO_ON = _on("SNAPEYES_PUPIL", "SNAPEYES_PUPIL_HALO")
ZONE_ON = _on("SNAPEYES_PUPIL", "SNAPEYES_PUPIL_ZONE")

NS = 24                      # sectors round the pupil
HALO_NEAR = (0.004, 0.055)   # the annulus that is tested, iris radii outside the render's pupil edge
HALO_FAR = (0.10, 0.26)      # the iris beyond it, the reference
HALO_LIT = 0.85              # a halo sector is at least this share of the iris beyond it (and HALO_LIT_MIN grey levels)...
HALO_LIT_MIN = 25.0
HALO_SMOOTH = 0.45           # ...with a fibre-band std under this share of that iris's
HALO_MIN = 0.40              # the gate: share of the measured sectors that carry a halo (13: 0.67, 25: 0.71; every other render 0.29 or less:
                             # 119 replays, 215 renders of 36 independent photos, 703 saved renders of earlier rounds)
HALO_SECTORS = 16            # and at least this many of the 24 sectors had enough pixels to be measured
PHOTO_SMALLER = 0.03         # a photo circle, when there is one, must be larger than the render's pupil by this much
STEP = 0.004                 # radial bin of the repair's profile (iris radii)
MAXW = 0.14                  # widest halo that is repaired
HALO_FIBRE = 3.0             # grey levels at 1024 px: a band whose fibre-band std reaches this is fibre, not glow
                             # (halo 1.4 to 2.4 on 13, fibres 5 to 17)
HALO_STEP_MARGIN = 0.004     # the step's own blur: the band runs this far past the bin where the luma has fallen
HALO_BRIGHT = 1.6            # only where the halo is at least this much brighter than the iris beyond it
HALO_OFFSET = 0.06           # the glow's circle may lie this far (iris radii) off the black disk's centre
HALO_TONE_MAX = 30.0         # the pupil tone the halo is taken to (as pupil_lock: never lighter than this)
HALO_FEATHER = 0.006         # soft edge of the sealed disk (iris radii, 3 px at 1024)
PHOTO_CAP = 0.04             # the sealed pupil is at most this much wider (radius) than the photo's when it has one

ZONE = (0.01, 0.25)          # the zone round the pupil that the colour lock may have tinted (iris radii outside its edge)
ZONE_OUTER = (0.70, 0.88)    # the outer ring it is compared with, iris radii from the frame centre
ZONE_SRC_MAX = 12.0          # photo luma in the zone under which its colour is not evidence (17: 5.6 to 7.8, every other test frame 19.2 or more;
                             # 36 Commons photos, lowest reading of each: cm011 4.0, cm010 5.6, cs003 7.0, every other 17 or more)
ZONE_EXCESS = 10.0           # shift of the zone's (a*, b*) from the raw render, less the outer ring's (17: 11.8 to 18.5; cm011, four fresh
                             # renders: 12.8 to 28.4; the dark cm010 and cs003, whose renders have no zone, stay under it)
ZONE_IN = 0.02               # the repair starts this far inside the pupil edge (the lock leaves a thin cyan outline on the boundary itself)
ZONE_FULL = 0.22             # the repair is full up to this far outside the pupil edge...
ZONE_FADE = 0.14             # ...and gone this much further out


def _polar(im, pc, reach, r_frac, f):
    """The window of the render round the pupil circle, every f-th pixel (BOX): luma, fibre band, distance from the
    circle centre d and sector (iris radii, 24 sectors), the radius from the frame centre rc."""
    S = im.size[0]; R = r_frac * S
    cx, cy, rho, edge = pc
    x0, y0 = S / 2 + cx * R, S / 2 + cy * R
    e = (edge + reach) * R
    c0, r0 = max(0, int(x0 - e) - 1), max(0, int(y0 - e) - 1)
    c1, r1 = min(S, int(math.ceil(x0 + e)) + 2), min(S, int(math.ceil(y0 + e)) + 2)
    w, h = (c1 - c0) // f * f, (r1 - r0) // f * f
    blk = im.crop((c0, r0, c0 + w, r0 + h))
    if f > 1:
        blk = blk.resize((w // f, h // f), Image.BOX)
    rgb = np.asarray(blk)
    Y = L._lum3(rgb.astype(np.float32))[..., 0]
    hp = Y - L._blur_f(Y, max(1.0, 3.0 * S / 1024.0 / f))
    xs = (c0 + (np.arange(w // f) + 0.5) * f - S / 2) / R
    ys = (r0 + (np.arange(h // f) + 0.5) * f - S / 2) / R
    X, Yc = xs[None, :] - cx, ys[:, None] - cy
    d = np.sqrt(X * X + Yc * Yc)
    th = np.arctan2(Yc, X)
    sec = ((th + math.pi) / (2 * math.pi) * NS).astype(np.int32) % NS
    rc = np.sqrt(xs[None, :] ** 2 + ys[:, None] ** 2)
    return {"Y": Y, "hp": hp, "d": d, "th": th, "sec": sec, "rc": rc, "rgb": rgb, "box": (c0, r0, w, h), "f": f}


def _sector_stats(P, edge, lo, hi):
    """Per sector: pixel count, median luma and fibre-band std of the annulus edge + lo .. edge + hi (inside 0.95 of the iris)."""
    m = (P["d"] >= edge + lo) & (P["d"] < edge + hi) & (P["rc"] < 0.95)
    s, y, h = P["sec"][m], P["Y"][m], P["hp"][m]
    n = np.bincount(s, minlength=NS).astype(np.float64)
    nn = np.maximum(n, 1.0)
    m1, m2 = np.bincount(s, weights=h, minlength=NS) / nn, np.bincount(s, weights=h * h, minlength=NS) / nn
    sd = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    o = np.argsort(s, kind="stable")
    ys = y[o]
    cut = np.searchsorted(s[o], np.arange(NS + 1))
    med = np.full(NS, np.nan)
    for k in range(NS):
        if cut[k + 1] > cut[k]:
            med[k] = float(np.median(ys[cut[k]:cut[k + 1]]))
    return n, med, sd


def halo_measure(P, edge):
    """(halo_frac, flags, yB): the share of the measured sectors that carry a smooth lit annulus, the per sector
    flags and the median luma of the iris beyond. halo_frac None when fewer than HALO_SECTORS sectors can be measured."""
    nA, yA, sA = _sector_stats(P, edge, *HALO_NEAR)
    nB, yB, sB = _sector_stats(P, edge, *HALO_FAR)
    ok = (nA >= 10) & (nB >= 20)
    flag = ok & (yA >= np.maximum(HALO_LIT_MIN, HALO_LIT * yB)) & (sA < HALO_SMOOTH * np.maximum(sB, 1.0))
    if ok.sum() < HALO_SECTORS:
        return None, flag, yB
    return float(flag[ok].sum() / ok.sum()), flag, yB


def _profile(out, pc, r_frac):
    """Full resolution radial profile of the halo zone: per sector and STEP bin the median luma and the fibre-band std,
    plus the window's pixels (for the repair)."""
    edge = pc[3]
    P = _polar(out, pc, MAXW + 0.03, r_frac, 1)
    nb = int(round(MAXW / STEP))
    m = (P["d"] >= edge) & (P["d"] < edge + MAXW) & (P["rc"] < 0.95)
    key = P["sec"][m] * nb + np.floor((P["d"][m] - edge) / STEP).astype(np.int32)
    y, h = P["Y"][m], P["hp"][m]
    n = np.bincount(key, minlength=NS * nb).astype(np.float64)
    nn = np.maximum(n, 1.0)
    m1, m2 = np.bincount(key, weights=h, minlength=NS * nb) / nn, np.bincount(key, weights=h * h, minlength=NS * nb) / nn
    sd = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    o = np.argsort(key, kind="stable")
    ys = y[o]
    cut = np.searchsorted(key[o], np.arange(NS * nb + 1))
    med = np.full(NS * nb, np.nan)
    for k in range(NS * nb):
        if cut[k + 1] - cut[k] >= 4:
            med[k] = float(np.median(ys[cut[k]:cut[k + 1]]))
    return P, med.reshape(NS, nb), sd.reshape(NS, nb)


def _halo_widths(med, sd, flag, yB):
    """Per sector the width of its halo (iris radii from the pupil edge), NaN for a sector without one, and whether the
    halo was a bright glow. Two kinds, both measured on the sector's radial profile (bins of STEP):
    a glow: the band just outside the pupil is at least HALO_BRIGHT times the iris beyond it (25: the model drew a white
    rim out to the real pupil edge, 100 to 200 against 30). It ends at the step down the model drew there, the first bin
    after its peak that has fallen to half the peak (and to 1.15 of the iris), whatever its fibre-band std: a steep ramp
    has std 3 to 7 and is still glow. A sector that is not flagged counts too (the glow can be gradual and textured).
    a plateau: a flagged sector with no glow (13: grey 54 against an iris of 50 to 70). It is walked out from the edge
    while it stays smooth (fibre-band std under HALO_FIBRE) and lit (0.6 of its plateau)."""
    nb = med.shape[1]
    w = np.full(NS, np.nan)
    glow = np.zeros(NS, bool)
    for s in range(NS):
        plateau = float(np.nanmedian(med[s, 2:10])) if np.isfinite(med[s, 2:10]).any() else float("nan")
        if not plateau == plateau:
            continue
        if plateau >= HALO_BRIGHT * max(float(yB[s]), 1.0):
            row = np.nan_to_num(med[s], nan=0.0)
            kp = 2 + int(np.argmax(row[2:]))
            peak = float(row[kp])
            lim = max(0.5 * peak, 1.15 * float(yB[s]))
            j = kp
            while j < nb and med[s, j] == med[s, j] and med[s, j] > lim:
                j += 1
            if j < nb and med[s, j] == med[s, j]:               # a step was found, not the end of the window
                w[s] = j * STEP + HALO_STEP_MARGIN
                glow[s] = True
            continue
        if not flag[s]:
            continue
        k = 2
        while k < nb:
            ya, ta = med[s, k], sd[s, k]
            if ya != ya or ta >= HALO_FIBRE or ya < 0.6 * plateau:
                break
            k += 1
        w[s] = k * STEP
    return w, glow


def _halo_repair(out, pc, r_frac, flag, yB, photo=None):
    """(image, info) with the halo taken into the pupil, or (out, info) when the widths say there is nothing to do."""
    cx, cy, rho, edge = pc
    P, med, sd = _profile(out, pc, r_frac)
    w, glow = _halo_widths(med, sd, flag, yB)
    have = w == w
    if have.sum() < 3:
        return out, {"why": "no widths"}
    wmed = float(np.median(w[have]))
    wf = np.where(have, np.maximum(w, wmed), wmed)              # concentric: no sector keeps less than the median halo
    how = "median"
    fit = L._pupil_fit(np.where(have, edge + w, np.nan))       # the glow ends on the model's real pupil circle, which
    if fit is not None and fit[4] <= L.PUPIL_LOCK_FIT and math.hypot(fit[0], fit[1]) <= HALO_OFFSET:   # need not share the black disk's centre
        t = (np.arange(NS) + 0.5) / NS * 2 * math.pi - math.pi
        ux, uy = np.cos(t), np.sin(t)
        rr = fit[0] * ux + fit[1] * uy + np.sqrt(np.maximum(fit[2] ** 2 - (fit[0] * uy - fit[1] * ux) ** 2, 0.0))
        wfit = rr - edge
        if np.all(wfit > 0.0):
            wf = np.where(have, np.maximum(w, wfit), wfit)
            how = "circle"
    wf = np.minimum(wf, MAXW)
    if photo is not None:                                        # and no wider than the photo's pupil plus PHOTO_CAP
        wf = np.minimum(wf, max(photo[2] + PHOTO_CAP - edge, STEP))
    o = edge + (np.roll(wf, 1) + 2 * wf + np.roll(wf, -1)) / 4.0   # the outer radius of the sealed disk per sector
    t = (P["th"] + math.pi) / (2 * math.pi) * NS - 0.5
    k0 = np.floor(t).astype(np.int32)
    fr = t - k0
    k0 %= NS
    k1 = (k0 + 1) % NS
    r_out = o[k0] * (1 - fr) + o[k1] * fr
    d = P["d"]
    a = np.clip((r_out + HALO_FEATHER / 2 - d) / HALO_FEATHER, 0.0, 1.0)
    a = 0.5 - 0.5 * np.cos(a * math.pi)
    a = np.where(d <= edge, 1.0, a)
    inner = d < 0.7 * edge
    tone = float(np.percentile(P["Y"][inner], 20)) if inner.any() else 3.0
    tone = min(tone, HALO_TONE_MAX)
    c0, r0, w_, h_ = P["box"]
    blk = np.asarray(out.convert("RGB").crop((c0, r0, c0 + w_, r0 + h_))).astype(np.float32)
    new = np.clip(blk + a[..., None] * (np.minimum(blk, tone) - blk) + 0.5, 0, 255).astype(np.uint8)
    res = out.convert("RGB")
    res.paste(Image.fromarray(new), (c0, r0))
    return res, {"how": how, "halo_width_med": round(wmed, 3), "halo_sectors": int(have.sum()), "tone": round(tone, 1),
                 "new_rho": round(float(np.mean(o)), 3), "old_edge": round(float(edge), 3)}


def _lab_med(a, m, step=7):
    lab = L.srgb_to_lab(a[m][::step])
    return float(np.median(lab[:, 1])), float(np.median(lab[:, 2]))


def zone_measure(out, raw, base, pc, r_frac, P):
    """(src_luma, excess) of the zone, or None when it cannot be measured. src_luma is read first and alone decides
    whether the colour work is done at all (almost every photo is lit: 19 or more against 12)."""
    S = out.size[0]; f = P["f"]
    c0, r0, w, h = P["box"]
    edge = pc[3]
    Z = (P["d"] >= edge + ZONE[0]) & (P["d"] < edge + ZONE[1]) & (P["rc"] < 0.90)
    if Z.sum() < 200:
        return None
    blk = base.crop((c0, r0, c0 + w, r0 + h))
    if f > 1:
        blk = blk.resize((w // f, h // f), Image.BOX)
    src = float(np.median(L._lum3(np.asarray(blk).astype(np.float32))[..., 0][Z]))
    if src >= ZONE_SRC_MAX or raw is None:
        return src, None
    # the same zone (window) and outer ring (the whole frame, every 3rd pixel) at full size, (a*, b*) of the render
    # against the model's raw render
    if raw.size != out.size:
        raw = raw.resize(out.size, Image.LANCZOS)
    cx, cy = pc[0], pc[1]
    R = r_frac * S
    xs = (np.arange(c0, c0 + w) + 0.5 - S / 2) / R
    ys = (np.arange(r0, r0 + h) + 0.5 - S / 2) / R
    d = np.sqrt((xs[None, :] - cx) ** 2 + (ys[:, None] - cy) ** 2)
    rc = np.sqrt(xs[None, :] ** 2 + ys[:, None] ** 2)
    Zf = (d >= edge + ZONE[0]) & (d < edge + ZONE[1]) & (rc < 0.90)
    g = np.arange(1, S, 3)
    gx = (g + 0.5 - S / 2) / R
    Of = (np.sqrt(gx[None, :] ** 2 + gx[:, None] ** 2) > ZONE_OUTER[0]) & (np.sqrt(gx[None, :] ** 2 + gx[:, None] ** 2) < ZONE_OUTER[1])
    if Zf.sum() < 200 or Of.sum() < 200:
        return src, None
    ao = np.asarray(out.convert("RGB"))
    ar = np.asarray(raw.convert("RGB"))
    zr, zl = _lab_med(ar[r0:r0 + h, c0:c0 + w], Zf), _lab_med(ao[r0:r0 + h, c0:c0 + w], Zf)
    orr, ol = _lab_med(ar[1::3, 1::3], Of, 1), _lab_med(ao[1::3, 1::3], Of, 1)
    excess = math.hypot(zl[0] - zr[0], zl[1] - zr[1]) - math.hypot(ol[0] - orr[0], ol[1] - orr[1])
    return src, excess


def _zone_repair(out, pc, r_frac):
    """The zone takes the chroma (Cb, Cr) of the iris ring beyond it, blended out over ZONE_FADE."""
    S = out.size[0]; R = r_frac * S
    cx, cy, rho, edge = pc
    P = _polar(out, pc, ZONE[1] + ZONE_FADE + 0.02, r_frac, 1)
    c0, r0, w, h = P["box"]
    d, rc = P["d"], P["rc"]
    ref = (rc > ZONE_OUTER[0]) & (rc < ZONE_OUTER[1]) & (d > edge + ZONE[1] + ZONE_FADE)
    if ref.sum() < 200:
        # the window does not reach the outer ring: read it over the whole frame (rare, a pupil near the rim)
        full = np.asarray(out.convert("YCbCr")).astype(np.float32)
        xs = (np.arange(S) + 0.5 - S / 2) / R
        rcf = np.sqrt(xs[None, :] ** 2 + xs[:, None] ** 2)
        m = (rcf > ZONE_OUTER[0]) & (rcf < ZONE_OUTER[1])
        cb_ref, cr_ref = float(np.median(full[..., 1][m])), float(np.median(full[..., 2][m]))
    else:
        ycc = np.asarray(out.convert("YCbCr").crop((c0, r0, c0 + w, r0 + h))).astype(np.float32)
        cb_ref, cr_ref = float(np.median(ycc[..., 1][ref])), float(np.median(ycc[..., 2][ref]))
    wgt = np.clip((edge + ZONE_FULL + ZONE_FADE - d) / ZONE_FADE, 0.0, 1.0)
    wgt = 0.5 - 0.5 * np.cos(wgt * math.pi)
    wgt = np.where((d > edge - ZONE_IN) & (rc < 0.92), wgt, 0.0)
    ycc = np.asarray(out.convert("YCbCr").crop((c0, r0, c0 + w, r0 + h))).astype(np.float32)
    cb = ycc[..., 1] + (cb_ref - ycc[..., 1]) * wgt
    cr = ycc[..., 2] + (cr_ref - ycc[..., 2]) * wgt
    new = Image.merge("YCbCr", tuple(Image.fromarray(np.clip(p + 0.5, 0, 255).astype(np.uint8)) for p in (ycc[..., 0], cb, cr))).convert("RGB")
    old = np.asarray(out.convert("RGB").crop((c0, r0, c0 + w, r0 + h)))
    blk = np.where((wgt > 0)[..., None], np.asarray(new), old)
    res = out.convert("RGB")
    res.paste(Image.fromarray(blk.astype(np.uint8)), (c0, r0))
    return res, {"cb_ref": round(cb_ref - 128, 1), "cr_ref": round(cr_ref - 128, 1)}


def seal(out, raw, base, r_frac=None, info=None):
    """The render with its halo and its colour zone repaired when (and only when) they are measured; else the same
    object. out: the render after chroma_lock and pupil_lock, at WORK px; raw: the model's render before chroma_lock
    (None: no zone check); base: the image the model was given. info, a dict, is filled with the measurements."""
    info = {} if info is None else info
    try:
        if not (HALO_ON or ZONE_ON):
            return out
        r_frac = r_frac or L.iris_radius_frac()
        if out.size != (L.WORK, L.WORK):
            return out
        pc = L.pupil_circle(L._lock_lum(out), r_frac)
        if pc is None:
            info["why"] = "no pupil circle"
            return out
        info["pupil"] = [round(pc[0], 3), round(pc[1], 3), round(pc[2], 3), round(pc[3], 3)]
        P = _polar(out, pc, HALO_FAR[1] + 0.01, r_frac, 2)
        frac, flag, yB = halo_measure(P, pc[3]) if HALO_ON else (None, None, None)
        info["halo_frac"] = None if frac is None else round(frac, 3)
        zm = zone_measure(out, raw, base, pc, r_frac, P) if ZONE_ON else None
        if zm is not None:
            info["zone_src"] = round(zm[0], 1)
            info["zone_excess"] = None if zm[1] is None else round(zm[1], 1)
        res = out
        photo = None
        if frac is not None and frac >= HALO_MIN:
            photo = L.pupil_circle(L._lock_lum(base), r_frac)
            info["photo_circle"] = None if photo is None else [round(v, 3) for v in photo]
            if photo is not None and not photo[2] - pc[2] >= PHOTO_SMALLER:
                info["halo_vetoed"] = "render pupil is not smaller than the photo's"
            else:
                res, hi = _halo_repair(res, pc, r_frac, flag, yB, photo)
                info["halo"] = hi
        if zm is not None and zm[1] is not None and zm[0] < ZONE_SRC_MAX and zm[1] >= ZONE_EXCESS:
            res, zi = _zone_repair(res, pc, r_frac)
            info["zone"] = zi
        if res is not out:
            print("snapeyes pupil seal " + json.dumps(info), flush=True)
        return res
    except Exception as e:
        print("snapeyes pupil seal skipped: " + repr(e)[:200], flush=True)
        return out
