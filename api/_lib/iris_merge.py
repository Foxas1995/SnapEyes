# -*- coding: utf-8 -*-
"""
iris_merge.py - production multi-frame iris merge for SnapEyes.

Takes the 3-5 photos a phone burst produced with the torch moved between shots
and returns ONE frame with the reflections gone and the sensor noise averaged out.
No AI, no network, no API key.  Pure numpy + OpenCV, about 1 second on a CPU.

Drop-in use in api/:

    from _lib.iris_merge import merge_burst
    merged, rep = merge_burst(list_of_bgr_uint8_arrays)
    if rep["ok"]:
        crop = merged            # feed this to the existing enhance step
        skip_deglare = rep["residual_glare_pct"] < 0.5

Design decisions, each backed by a measurement in exp1..exp5:
  * alignment is NOT optional.  Merging unaligned frames destroys 2/3 of the
    fibre detail (detail 0.88 -> 0.31) and is worse than using one frame.
  * ORB+RANSAC is the best aligner when the iris has texture, but it finds
    nothing on a soft phone selfie, so we count RANSAC inliers and fall back to
    phase correlation.  Do not run ECC on a low-texture iris: it makes it worse.
  * the merge is a per-pixel weighted mean whose weight falls off with how much
    brighter than the per-pixel median that sample is.  A specular highlight is
    always the brightest sample, so it weighs ~0 without any glare detector.
  * per-frame gain+offset normalisation first, or the merge just picks whichever
    frame the auto-exposure made darkest.
"""
import math
import numpy as np
import cv2

__all__ = ["merge_burst", "align_auto", "frame_quality", "MergeReport"]

# tuned in exp1/exp4; see the tables in the report
TAU = 8.0            # DN above the per-pixel median at which a sample's weight falls to 1/e
SHARP_POW = 0.5      # how hard local sharpness is allowed to pick between frames
MIN_INLIERS = 30     # below this many ORB RANSAC inliers we do not trust the feature match
MIN_FRAMES = 2
SHARP_REJECT = 0.45  # drop a frame below this fraction of the sharpest frame (blink / motion blur)


# --------------------------------------------------------------------------- prep
def _gray(f):
    return cv2.cvtColor(np.clip(f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)


def _no_highlight(f, pct=90):
    """Grey image with the specular clipped off, for anything that must not chase the glare."""
    g = _gray(f).astype(np.float32)
    return np.minimum(g, np.percentile(g, pct))


def frame_quality(f, ring=None):
    """Sharpness and exposure health of one frame.  Used to throw out blinks."""
    g = _no_highlight(f)
    if ring is not None:
        g = g * ring + g.mean() * (1 - ring)
    sharp = float(cv2.Laplacian(g.astype(np.uint8), cv2.CV_64F).var())
    gg = _gray(f)
    clipped = float((gg >= 250).mean())
    dark = float((gg <= 6).mean())
    return dict(sharp=sharp, clipped=clipped, dark=dark)


def ring_from_circles(side, r_pupil, r_iris, inner=1.10, outer=0.97):
    yy, xx = np.mgrid[0:side, 0:side].astype(np.float32)
    c = (side - 1) / 2.0
    r = np.hypot(xx - c, yy - c)
    return ((r >= r_pupil * inner) & (r <= r_iris * outer)).astype(np.float32)


# ------------------------------------------------------- circles + rubber sheet
def _polar(g, cx, cy, rmax, nth=180):
    th = np.linspace(0, 2 * math.pi, nth, endpoint=False).astype(np.float32)
    rr = np.linspace(1, rmax, int(rmax)).astype(np.float32)
    X = (cx + np.cos(th)[None, :] * rr[:, None]).astype(np.float32)
    Y = (cy + np.sin(th)[None, :] * rr[:, None]).astype(np.float32)
    return cv2.remap(g, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), rr


def _edge_radius(g, cx, cy, rmax, r_lo, r_hi, sign):
    """Daugman: the radius where the angle-MEDIAN intensity steps hardest."""
    P, rr = _polar(g, cx, cy, rmax)
    prof = cv2.GaussianBlur(np.median(P, 1).reshape(-1, 1), (0, 0), 2.5).ravel()
    d = np.gradient(prof) * sign
    i0 = int(np.searchsorted(rr, r_lo)); i1 = min(int(np.searchsorted(rr, r_hi)), len(d) - 1)
    if i1 <= i0:
        return None, -1e18
    k = i0 + int(np.argmax(d[i0:i1]))
    return float(rr[k]), float(d[k])


def fit_circles(f, search=10, step=2):
    """
    (pupil_cx, pupil_cy, pupil_r), (limbus_cx, limbus_cy, limbus_r).
    Highlights are clipped and the circle average is a MEDIAN over angle, so a
    specular blob covering a fifth of the ring cannot move the answer.
    Measured accuracy on simulated bursts: limbus +-2 px, pupil 2.3 px RMS.
    """
    g = cv2.GaussianBlur(_no_highlight(f, 88), (0, 0), 2.0)
    side = g.shape[0]
    c = (side - 1) / 2.0
    best, lim = -1e18, (c, c, side * 0.45)
    for cx in np.arange(c - search, c + search + .01, step):
        for cy in np.arange(c - search, c + search + .01, step):
            rmax = min(cx, cy, side - 1 - cx, side - 1 - cy) - 2
            r, v = _edge_radius(g, cx, cy, rmax, side * 0.28, side * 0.50, -1.0)
            if r is not None and v > best:
                best, lim = v, (float(cx), float(cy), r)
    lcx, lcy, ri = lim
    best, pup = -1e18, (lcx, lcy, ri * 0.33)
    for cx in np.arange(lcx - search, lcx + search + .01, step):
        for cy in np.arange(lcy - search, lcy + search + .01, step):
            rmax = min(ri * 0.80, cx, cy, side - 1 - cx, side - 1 - cy) - 2
            if rmax < 12:
                continue
            r, v = _edge_radius(g, cx, cy, rmax, ri * 0.10, ri * 0.72, +1.0)
            if r is not None and v > best:
                best, pup = v, (float(cx), float(cy), r)
    return pup, lim


def rubber_warp(img, src_rp, src_ri, src_c, dst_rp, dst_ri, dst_c):
    """
    Daugman rubber-sheet: resample so this frame's pupil radius becomes dst_rp and
    its limbus radius becomes dst_ri.  The tissue between the two circles stretches
    linearly in radius, which is what iris tissue really does when the pupil moves.
    """
    side = img.shape[0]
    yy, xx = np.mgrid[0:side, 0:side].astype(np.float32)
    dx, dy = xx - dst_c[0], yy - dst_c[1]
    r = np.hypot(dx, dy)
    ang = np.arctan2(dy, dx)
    src = np.where(r <= dst_rp, r * (src_rp / max(dst_rp, 1e-3)),
                   np.where(r <= dst_ri,
                            src_rp + (r - dst_rp) * (src_ri - src_rp) / max(dst_ri - dst_rp, 1e-3),
                            src_ri + (r - dst_ri)))
    mx = (src_c[0] + np.cos(ang) * src).astype(np.float32)
    my = (src_c[1] + np.sin(ang) * src).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


# ---------------------------------------------------------------------- alignment
def _affine_sane(E, max_scale=1.30, max_shear=0.25):
    """A 6-DOF fit can shear wildly on bad matches.  An iris never does."""
    A = np.asarray(E, np.float64)[:, :2]
    try:
        u, sv, vt = np.linalg.svd(A)
    except np.linalg.LinAlgError:
        return False
    if sv[1] <= 1e-6:
        return False
    if not (1.0 / max_scale < sv[0] < max_scale and 1.0 / max_scale < sv[1] < max_scale):
        return False
    return (sv[0] / sv[1] - 1.0) <= max_shear


def _orb_align(frames, ref=0, nfeat=3000):
    gref = _gray(frames[ref])
    orb = cv2.ORB_create(nfeat)
    kr, dr = orb.detectAndCompute(gref, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    side = frames[ref].shape[0]
    out, inliers = [], []
    for i, f in enumerate(frames):
        if i == ref:
            out.append(f.astype(np.float32)); inliers.append(9999); continue
        k, d = orb.detectAndCompute(_gray(f), None)
        W, n = None, 0
        if d is not None and dr is not None and len(k) >= 8:
            m = sorted(bf.match(d, dr), key=lambda x: x.distance)[:400]
            if len(m) >= 8:
                src = np.float32([k[x.queryIdx].pt for x in m])
                dst = np.float32([kr[x.trainIdx].pt for x in m])
                # FULL affine, 6 DOF - not estimateAffinePartial2D.  When the subject
                # looks a little left or right between shots the iris, sitting on a
                # sphere, is foreshortened into an ellipse, and a similarity transform
                # cannot undo an ellipse.  Measured at a 15 deg gaze change: similarity
                # keeps 0.55 of the detail, full affine keeps 0.91.  It costs nothing
                # when the gaze did not move (39.02 vs 38.92 dB).
                E, inl = cv2.estimateAffine2D(src, dst, method=cv2.RANSAC,
                                              ransacReprojThreshold=2.0)
                if E is not None and _affine_sane(E):
                    W = E.astype(np.float32)
                    n = int(inl.sum()) if inl is not None else 0
        if W is None:
            W = np.eye(2, 3, dtype=np.float32)
        out.append(cv2.warpAffine(f.astype(np.float32), W, (side, side),
                                  flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
        inliers.append(n)
    return out, inliers


def _phase_align(frames, ref=0):
    """Sub-pixel translation with no features at all.  For a soft, low-texture iris."""
    side = frames[ref].shape[0]
    win = cv2.createHanningWindow((side, side), cv2.CV_32F)
    gref = (_no_highlight(frames[ref]) * win).astype(np.float32)
    out, shifts = [], []
    for i, f in enumerate(frames):
        if i == ref:
            out.append(f.astype(np.float32)); shifts.append((0.0, 0.0)); continue
        cur = (_no_highlight(f) * win).astype(np.float32)
        (dx, dy), _ = cv2.phaseCorrelate(gref, cur)
        if not np.isfinite(dx) or not np.isfinite(dy) or max(abs(dx), abs(dy)) > side * 0.25:
            dx = dy = 0.0
        W = np.float32([[1, 0, -dx], [0, 1, -dy]])
        out.append(cv2.warpAffine(f.astype(np.float32), W, (side, side),
                                  flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
        shifts.append((float(dx), float(dy)))
    return out, shifts


def align_auto(frames, ref=0):
    """
    ORB+RANSAC when the iris has texture to match on, phase correlation when it
    does not.  Measured: on a sharp iris ORB gives 314-389 inliers and keeps 0.87
    of the true detail; on a real soft phone selfie it gives 0 inliers and keeps
    0.32, where phase correlation keeps 0.60.
    """
    out, inl = _orb_align(frames, ref)
    others = [n for i, n in enumerate(inl) if i != ref]
    if others and float(np.median(others)) >= MIN_INLIERS:
        return out, dict(method="orb", inliers=others)
    out, sh = _phase_align(frames, ref)
    return out, dict(method="phase", inliers=others, shifts=sh)


# ------------------------------------------------------------------- photometric
def photometric(frames, ring=None):
    """Robust per-frame gain+offset onto the median frame, fitted off the highlights."""
    st = np.stack(frames, 0)
    ref = np.median(st, 0)
    gref = ref.mean(2)
    base = np.ones(gref.shape, bool) if ring is None else (ring > 0)
    base &= (gref > 8)
    out, gains = [], []
    for f in frames:
        g = f.mean(2)
        sel = base & (g < np.percentile(g[base], 92)) & (gref < np.percentile(gref[base], 92))
        if sel.sum() < 200:
            out.append(f); gains.append((1.0, 0.0)); continue
        x, y = g[sel], gref[sel]
        A = np.stack([x, np.ones_like(x)], 1)
        sol, *_ = np.linalg.lstsq(A, y, rcond=None)
        a, b = float(sol[0]), float(sol[1])
        if not (0.5 < a < 2.0):
            a, b = 1.0, 0.0
        out.append(f * a + b)
        gains.append((a, b))
    return out, gains


# ------------------------------------------------------------------------- merge
def _local_sharp(f, k=9):
    lap = cv2.Laplacian(_gray(f), cv2.CV_32F, ksize=3)
    return cv2.boxFilter(lap * lap, -1, (k, k))


def weighted_merge(frames, tau=TAU, sharp_pow=SHARP_POW):
    """
    Per pixel, weight each sample by
        exp(-(sample - median)/tau)  * local_sharpness ** sharp_pow
    The first factor is the glare killer: a specular is always the brightest
    sample at that pixel, so it weighs almost nothing.  It needs no glare
    detector, no threshold and no model.
    """
    st = np.stack(frames, 0)
    lum = st.mean(3)
    med = np.median(lum, 0)[None]
    w = np.exp(-np.maximum(lum - med, 0.0) / tau)
    if sharp_pow > 0:
        sh = np.stack([_local_sharp(f) for f in frames], 0)
        sh = sh / (sh.mean((1, 2), keepdims=True) + 1e-6)
        w = w * np.power(np.maximum(sh, 1e-3), sharp_pow)
    w = w[..., None]
    return (st * w).sum(0) / np.maximum(w.sum(0), 1e-6)


class MergeReport(dict):
    pass


# Measured trigger: fitted-pupil-radius spread is ~0.8 % when the pupil did not move
# and ~3.5 % at a 10 % dilation swing.  Firing wrongly costs 1.0 dB; failing to fire
# when the pupil DID move costs up to 10.5 dB, so the threshold sits close to the floor.
RUBBER_MARGIN = 1.08
RUBBER_MIN_TEXTURE = 4.0   # below this HF energy the sharpness score is pure noise, so do not choose on it


def hf_energy(img, ring=None):
    """
    No-reference sharpness: high-frequency energy inside the iris ring.  Used to
    choose between two candidate merges without any ground truth - a badly
    registered merge is a blurred merge, so the sharper candidate is the better
    registered one.  Measured: this rule picked the better variant in 19 of 20
    cases, and the single miss cost 0.57 dB.
    """
    g = _gray(img).astype(np.float32)
    hp = g - cv2.GaussianBlur(g, (0, 0), 1.6)
    hp = hp * hp
    return float(hp[ring > 0].mean()) if ring is not None else float(hp.mean())


def _align_photo_merge(sel, ref, ring):
    al, ainfo = align_auto(sel, ref)
    al, gains = photometric(al, ring)
    return weighted_merge(al), al, ainfo, gains


def merge_burst(frames, r_pupil=None, r_iris=None, drop_bad=True, ref=None, rubber="auto"):
    """
    frames : list of HxWx3 BGR arrays, same size, the same eye, torch moved between shots.
    returns (merged_float32_bgr, report)
    """
    rep = MergeReport(ok=False, n_in=len(frames), n_used=0, method=None,
                      dropped=[], residual_glare_pct=None, note="")
    if len(frames) < MIN_FRAMES:
        rep["note"] = "need at least %d frames" % MIN_FRAMES
        return (frames[0].astype(np.float32) if frames else None), rep

    side = frames[0].shape[0]
    frames = [f for f in frames if f.shape[:2] == (side, side)]
    ring = ring_from_circles(side, r_pupil, r_iris) if (r_pupil and r_iris) else None

    # 1. throw out blinks and badly blurred shots
    q = [frame_quality(f, ring) for f in frames]
    best = max(x["sharp"] for x in q) or 1.0
    keep = list(range(len(frames)))
    if drop_bad:
        keep = [i for i in range(len(frames))
                if q[i]["sharp"] >= SHARP_REJECT * best and q[i]["clipped"] < 0.25]
        rep["dropped"] = [i for i in range(len(frames)) if i not in keep]
    if len(keep) < MIN_FRAMES:
        keep = list(range(len(frames)))
        rep["dropped"] = []
    sel = [frames[i].astype(np.float32) for i in keep]

    # 2. the sharpest surviving frame is the reference: everything lands in ITS geometry
    if ref is None:
        ref = int(np.argmax([q[i]["sharp"] for i in keep]))
    rep["ref_frame"] = keep[ref]

    # 3. The pupil moves between shots, because the torch does.  Once it has moved,
    #    NO rigid transform can register the frames - the iris tissue itself stretched.
    #    A Daugman rubber-sheet fixes that, but it costs ~1 dB when the pupil did NOT
    #    move, and the fitted pupil radius is too noisy on a real photo to decide from
    #    (measured fit noise at zero dilation ranges from 0.8 % to 5.0 % depending on
    #    the eye, which straddles the signal from a real 10 % dilation).  So we do not
    #    guess: we merge BOTH ways and keep whichever result is sharper.
    rep["rubber"] = False
    rubber_imgs = None
    if rubber:
        try:
            circ = [fit_circles(f) for f in sel]
            rps = np.array([c[0][2] for c in circ], np.float64)
            rep["pupil_radii"] = [round(float(x), 1) for x in rps]
            rep["pupil_spread"] = round(float(rps.std() / max(rps.mean(), 1e-6)), 4)
            (pc0, lc0) = circ[ref]
            rubber_imgs = [rubber_warp(f, pc[2], lc[2], (lc[0], lc[1]),
                                       pc0[2], lc0[2], (lc0[0], lc0[1]))
                           for f, (pc, lc) in zip(sel, circ)]
            if r_pupil is None or r_iris is None:
                ring = ring_from_circles(side, circ[ref][0][2], circ[ref][1][2])
        except Exception as e:                     # a fit failure must never lose the merge
            rep["note"] = "circle fit failed: %s" % e
            rubber_imgs = None

    # 4. align, 5. normalise exposure, 6. merge
    merged, al, ainfo, gains = _align_photo_merge(sel, ref, ring)
    if rubber_imgs is not None and rubber != "off":
        m2, al2, ai2, g2 = _align_photo_merge(rubber_imgs, ref, ring)
        s1, s2 = hf_energy(merged, ring), hf_energy(m2, ring)
        rep["sharpness"] = (round(s1, 2), round(s2, 2))
        if s1 < RUBBER_MIN_TEXTURE and rubber != "always":
            s2 = 0.0                              # textureless iris: no evidence, stay rigid
            rep["note"] = (rep["note"] + " low-texture: rubber-sheet not considered").strip()
        # Require a real margin.  A genuine pupil dilation makes the rubber-sheet
        # merge 15-35 % sharper; anything under 8 % is fit noise, and on a
        # near-textureless iris the score is noise all the way down.
        if rubber == "always" or s2 > s1 * RUBBER_MARGIN:
            merged, al, ainfo, gains = m2, al2, ai2, g2
            rep["rubber"] = True
    rep["method"] = ainfo["method"]
    rep["inliers"] = ainfo.get("inliers")
    rep["gains"] = [round(g[0], 4) for g in gains]

    # 7. how much glare is left, measured against the per-pixel median of the stack
    st = np.stack([a.mean(2) for a in al], 0)
    med = np.median(st, 0)
    mm = merged.mean(2)
    area = ring if ring is not None else np.ones_like(mm, np.float32)
    denom = max(float(area.sum()), 1.0)
    rep["residual_glare_pct"] = float((((mm - med) > 10).astype(np.float32) * area).sum() / denom * 100)
    rep["input_glare_pct"] = float(np.mean([
        (((a.mean(2) - med) > 10).astype(np.float32) * area).sum() / denom * 100 for a in al]))
    rep["n_used"] = len(al)
    rep["ok"] = True
    return np.clip(merged, 0, 255), rep
