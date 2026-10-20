# -*- coding: utf-8 -*-
"""styles.ensemble.checks: the run-time checks of a ensemble picture (preview(check=True), and every master: the master step asks for them). They are the engine's
own self check (selfcheck.run: T1 iris integrity, T6 matter on iris, T7 text, T12 no hearts) plus the checks of the design brief that apply to looks whose
irises never overlap, measured the way the laboratory of 2026-10-20 measured them (proto_pf/checks.py):

  T1, T6   every pixel of zone A (r <= 0.95 R) of every iris is the graded disc, 0 of 255 (the product's promise, AC-5: the iris is never repainted or blurred)
  T2       the pupil grown by 0.01 R is untouched: the same pixel comparison over the pupil mask (pupil.analyse of the graded disc), 0 violations
  T3       the visible share of every iris: 100 percent (no two discs overlap; the least limb to limb gap is reported in R)
  T4       the black share of the picture (luma under 12/255), reported, not bounded (it varies with the look and the eyes)
  T7, T12  only the customer's words are drawn; no heart word in the style, design or layout
  T8       format safety: every iris and a margin of 0.05 S inside the canvas; on the phone wallpaper (9:19.5) inside the clock fifth and the foot
  T8b      the outer 0.02 S of the canvas stays under 3 percent mean luminance (the Radiance brief's own rule): BOUNDED for the two Radiance looks, reported for
           the others (the navy ground of Family Orbit reads about 4 percent, as the owner-approved Celestial Gold single's does)
  T18      the iris size floor: a diameter of at least 22 percent of the canvas width
  T19      the stacking rule: no contacts at all (no iris is behind another)
  edge     the limb read (T10 / T11 of the suites, reported here): |median L* of the limb band (0.90 to 0.98 R) - median L* of the ring just outside it
           (1.04 to 1.14 R, pixels within 1.15 R of another iris left out)| at 1024 px and at a 320 px tile
and, for two renders of the same picture (the golden suite and the owner's boards), T9: the master against the preview (t9_scale)."""
from __future__ import annotations

import math
import time

import numpy as np
from PIL import Image

from ... import iris as L
from .. import core as C
from .. import pupil as PUPM
from .. import selfcheck as SC

T8B_LIMIT = 0.03
T8B_BOUNDED = ("radiance_duo", "radiance_family")
FLOOR = 0.22


def gaps(discs):
    """The least limb to limb gap between two discs, in R of the smaller (positive: no overlap), and the number of contacts (a gap under 0.02 R)."""
    best, contacts = 1e9, 0
    for i in range(len(discs)):
        for j in range(i + 1, len(discs)):
            a, b = discs[i], discs[j]
            g = (math.hypot(a.cx - b.cx, a.cy - b.cy) - a.R - b.R) / min(a.R, b.R)
            best = min(best, g)
            contacts += g < 0.02
    return best, contacts


def _lstar(rgb8):
    return L.srgb_to_lab(rgb8.reshape(-1, 3).astype(np.float32))[:, 0].reshape(rgb8.shape[:2])


def edge_delta(img8, discs, scale=1.0):
    """For every iris |median L*(0.90..0.98 R) - median L*(1.04..1.14 R)| (the ring outside leaves out every pixel within 1.15 R of another iris), on the
    picture shrunk by `scale`: the list, one per iris (None where too few pixels are left)."""
    im = img8
    if scale != 1.0:
        h, w = im.shape[:2]
        im = np.asarray(Image.fromarray(im).resize((max(8, int(round(w * scale))), max(8, int(round(h * scale)))), Image.LANCZOS))
    out = []
    for k, d in enumerate(discs):
        cx, cy, R = d.cx * scale, d.cy * scale, d.R * scale
        r1 = int(1.16 * R) + 2
        x0, y0 = max(0, int(cx) - r1), max(0, int(cy) - r1)
        x1, y1 = min(im.shape[1], int(cx) + r1 + 1), min(im.shape[0], int(cy) + r1 + 1)
        sub = im[y0:y1, x0:x1]
        Lc = _lstar(sub)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        rho = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) / R
        near_other = np.zeros(rho.shape, bool)
        for j, e in enumerate(discs):
            if j != k:
                near_other |= np.hypot(xx + 0.5 - e.cx * scale, yy + 0.5 - e.cy * scale) <= 1.15 * e.R * scale
        a = Lc[(rho > 0.90) & (rho < 0.98)]
        b = Lc[(rho > 1.04) & (rho < 1.14) & ~near_other]
        if len(a) < 8 or len(b) < 8:
            out.append(None)
            continue
        out.append(round(float(abs(np.median(a) - np.median(b))), 1))
    return out


def frame_luma(img8, S):
    """The mean luminance (0..1) of the outer 0.02 S of the canvas (T8b)."""
    fw = max(2, int(round(0.02 * S)))
    luma = img8.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    fr = np.concatenate([luma[:fw].ravel(), luma[-fw:].ravel(), luma[fw:-fw, :fw].ravel(), luma[fw:-fw, -fw:].ravel()])
    return float(fr.mean()) / 255.0


def selfcheck(r, ids, edge=True):
    """The report of one base.Result: {ok, checks: {t1, t2, t3, t4, t6, t7, t8, t8b, t12, t18, t19, edge}, ms}; ok = every bounded check passes (T4, the edge
    numbers and T8b of a look that is not a Radiance look are reported). ids: the style, the design and the layout (T12)."""
    t0 = time.perf_counter()
    img8, discs, ctx = r.img8, r.discs, r.ctx
    H, W = img8.shape[:2]
    S = min(W, H)
    tl = [{"kind": e["kind"], "text": e["text"], "px": e["px"], "baseline": e["baseline"]} for e in (r.text_log or [])]
    rep = SC.run(img8, discs, text_log=tl, customer=list(r.customer or []), ids=list(ids))
    ch = rep["checks"]
    bad, per = 0, []
    for d in discs:
        t = d.g.shape[0]
        m = PUPM.mask(PUPM.analyse(d.g), t, d.R, dil=0.01)
        p = SC.iris_pixels(img8, d, mask=m)
        per.append(p["bad"])
        bad += p["bad"]
    ch["t2"] = {"ok": bad == 0, "violations": bad, "per_iris": per}
    gap, contacts = gaps(discs)
    ch["t3"] = {"ok": gap >= 0.0, "shares": [1.0] * len(discs), "min_gap_R": round(gap, 3), "floor": 1.0}
    share, lit = SC.black_shares(img8, (SC.BLACK_THR, SC.BLACK_LITERAL))
    ch["t4"] = {"ok": True, "share": round(share, 4), "literal3": round(lit, 4), "bounded": False}
    bad8 = []
    mg = 0.05 * S
    for k, d in enumerate(discs):
        if not (d.cx - d.R >= mg and d.cx + d.R <= W - mg and d.cy - d.R >= mg and d.cy + d.R <= H - mg):
            bad8.append(f"iris {k} outside the 0.05 S margin")
        if ctx.wall and (d.cy - d.R < 0.20 * H or d.cy + d.R > 0.94 * H):
            bad8.append(f"iris {k} outside the wallpaper safe zone")
    ch["t8"] = {"ok": not bad8, "bad": bad8}
    fl = frame_luma(img8, S)
    bounded8b = r.design in T8B_BOUNDED
    ch["t8b"] = {"ok": fl <= T8B_LIMIT or not bounded8b, "frame_luma": round(fl, 4), "limit": T8B_LIMIT, "bounded": bounded8b}
    dmin = 2.0 * min(d.R for d in discs)
    ch["t18"] = {"ok": dmin >= FLOOR * W - 1, "d_share_of_W": round(dmin / W, 4), "floor": FLOOR}
    ch["t19"] = {"ok": contacts == 0, "contacts": int(contacts)}
    if edge:
        e1024 = edge_delta(img8, discs, 1024.0 / max(W, H))
        e320 = edge_delta(img8, discs, 320.0 / max(W, H))
        ch["edge"] = {"ok": True, "bounded": False, "min_1024": min((v for v in e1024 if v is not None), default=None),
                      "min_320": min((v for v in e320 if v is not None), default=None), "per_iris_1024": e1024, "per_iris_320": e320}
    rep["ok"] = all(c["ok"] for c in ch.values())
    rep["checks"] = ch
    rep["ms"] = int(round((time.perf_counter() - t0) * 1000))
    return rep


# ----------------------------------------------------------------------------- T9: the master against the preview
def _dE(a, b):
    la = L.srgb_to_lab(a.reshape(-1, 3).astype(np.float32)[::3])
    lb = L.srgb_to_lab(b.reshape(-1, 3).astype(np.float32)[::3])
    de = L.ciede2000(la, lb)
    return float(de.mean()), float(np.percentile(de, 99))


def ssim_map(x, y, sigma=1.5):
    """The structural similarity map of two luma planes (0..255 float32): Gaussian windows of `sigma` px (core.blur), K1 0.01, K2 0.03, numpy only."""
    c1, c2 = (0.01 * 255.0) ** 2, (0.03 * 255.0) ** 2
    x = np.ascontiguousarray(x, np.float32)
    y = np.ascontiguousarray(y, np.float32)
    mx, my = C.blur(x, sigma, clip_negative=False), C.blur(y, sigma, clip_negative=False)
    sxx = C.blur(x * x, sigma, clip_negative=False) - mx * mx
    syy = C.blur(y * y, sigma, clip_negative=False) - my * my
    sxy = C.blur(x * y, sigma, clip_negative=False) - mx * my
    return ((2.0 * mx * my + c1) * (2.0 * sxy + c2)) / ((mx * mx + my * my + c1) * (sxx + syy + c2))


def t9_scale(small_img8, small_discs, big_img8):
    """T9 on two renders of the same picture (the 1024 px preview and the 4096 px master): the design (everything beyond 1.15 R of an iris) of the master
    shrunk to the preview's size against the preview, SSIM at least 0.95, mean dE00 at most 1.5, p99 at most 10; inside the irises (r <= 0.95 R) the mean dE00
    at most 3.0 (T9b). discs: (cx, cy, R) of the preview's irises."""
    a = small_img8
    h, w = a.shape[:2]
    bd = np.asarray(Image.fromarray(big_img8).resize((w, h), Image.LANCZOS))
    la = (a.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32))
    lb = (bd.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32))
    smap = ssim_map(la, lb)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    far = np.ones((h, w), bool)
    inside = np.zeros((h, w), bool)
    for (cx, cy, R) in small_discs:
        rr = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
        far &= rr > 1.15 * R
        inside |= rr <= 0.95 * R
    s_design = float(smap[far].mean())
    de_m, de_p = _dE(a[far], bd[far])
    de_in = _dE(a[inside], bd[inside])[0]
    ok = s_design >= 0.95 and de_m <= 1.5 and de_p <= 10.0 and de_in <= 3.0
    return {"ok": bool(ok), "ssim_design": round(s_design, 4), "dE_mean_design": round(de_m, 2), "dE_p99_design": round(de_p, 2), "dE_iris_T9b": round(de_in, 2)}
