# -*- coding: utf-8 -*-
"""cx_fill: the UNIVERSE background of the collision designs (BRIEF_V3_FINAL 3.5.1, 3.5.6, 3.5.7), numpy only.

The customer's own restored iris, enlarged about its own centre (k_s about 3, mirrored beyond rho = 1), darkened, sunk into a dark well
round the union outline, sprinkled with fibre flakes cut from the SAME iris's band and a few stars, vignetted. Pairs: each half is that
person's own iris enlarged, crossfaded over +-0.35 R about the perpendicular bisector. Groups: Voronoi blend, sigma 0.5 R (a 0.6 R wide
crossfade at d = 1.65 R). Nothing is repainted: the fill copies restored iris pixels only.
The result is a float canvas (display space) that the collision matter and the compositor then sit on.
"""
from __future__ import annotations

# PORT of work package WP7A (step A): cx_fill.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (imports); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math

import numpy as np

from .. import core as C
from . import powder as PW
from . import raster as RS

BAND_ROWS = 256
COPPER = np.array([0.54, 0.29, 0.12], np.float32)
STEEL = np.array([0.43, 0.46, 0.50], np.float32)


def _smooth(x0, x1, x):
    t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _sample(src, xs, ys):
    """Bilinear sample of src (h, w, 3) float32 at float coordinates (any broadcast shape): four row gathers on the flattened source."""
    h, w = src.shape[:2]
    flat = src.reshape(-1, 3)
    x = np.clip(xs, 0, w - 1.001)
    y = np.clip(ys, 0, h - 1.001)
    x0 = x.astype(np.int32)
    y0 = y.astype(np.int32)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    i00 = y0 * w + x0
    a = flat[i00]
    b = flat[i00 + 1]
    c = flat[i00 + w]
    d = flat[i00 + w + 1]
    top = a + (b - a) * fx
    bot = c + (d - c) * fx
    return top + (bot - top) * fy


def _tri(rho):
    return 1.0 - np.abs(1.0 - np.mod(rho, 2.0))


def enlarge(src, cx, cy, R, ks, x, y):
    """Enlarged iris colours at canvas pixel centres x (1, W), y (h, 1): the source pixel at normalised radius rho = r / (ks R) mirrored at
    every integer, angle kept. src: the restored iris square (float32 0..1, disc radius C.R_FRAC of its side)."""
    S0 = src.shape[0]
    Rs = C.R_FRAC * S0
    dx = x - cx
    dy = y - cy
    r = np.sqrt(dx * dx + dy * dy)
    rho = _tri(r / (ks * R))
    ux = dx / np.maximum(r, 1e-6)
    uy = dy / np.maximum(r, 1e-6)
    return _sample(src, S0 / 2.0 + ux * rho * Rs, S0 / 2.0 + uy * rho * Rs)


def _patch_fn_factory(discs, kk, sx, sy, lift):
    def patch_fn(i, w, h, rot_):
        dsc = discs[kk[i]]
        g = dsc.g
        cx0, cy0 = int(round(sx[i] - dsc.x0)), int(round(sy[i] - dsc.y0))
        x0_, y0_ = cx0 - w // 2, cy0 - h // 2
        xa, ya, xb, yb = max(0, x0_), max(0, y0_), min(g.shape[1], x0_ + w), min(g.shape[0], y0_ + h)
        out = np.zeros((h, w, 3), np.float32)
        if xa < xb and ya < yb:
            out[ya - y0_:yb - y0_, xa - x0_:xb - x0_] = g[ya:yb, xa:xb].astype(np.float32) / 255.0
        return np.clip(out * lift, 0, 1.4)
    return patch_fn


BASE_LONG = 576                 # the soft base of the universe fill is computed at this long side and upsampled: 4096 == 1024 and the cost is bounded


def _resize_f(a, W, H):
    """Bicubic resize of a float (h, w, 3) image to W x H (PIL mode F per channel), never negative."""
    from PIL import Image
    if a.shape[1] == W and a.shape[0] == H:
        return a
    out = np.empty((H, W, a.shape[2]), np.float32)
    for c in range(a.shape[2]):
        out[..., c] = np.asarray(Image.fromarray(np.ascontiguousarray(a[..., c]), "F").resize((W, H), Image.BICUBIC), np.float32)
    np.maximum(out, 0.0, out=out)
    return out


def add_resized(cv, soft):
    """cv (H, W, 3) += soft (h, w, 3) bicubic-resized to W x H, one channel at a time (a full-size temporary of three channels would add 200 MB at 4096)."""
    from PIL import Image
    H, W = cv.shape[:2]
    for c in range(3):
        ch = soft[..., c]
        if ch.shape != (H, W):
            ch = np.asarray(Image.fromarray(np.ascontiguousarray(ch), "F").resize((W, H), Image.BICUBIC), np.float32)
        cv[..., c] += np.maximum(ch, 0.0)


def _base_fill(sc_b, geo_b, irises, classes, prm, scale):
    """The soft universe base on the canonical geometry scaled by `scale` (px of the base grid): the enlarged own iris per person, darkened, class mixes,
    Voronoi / crossfade blend, dark well, vignette. Round 2c fixes (AD: posterised green and navy halos in the grey fills): the hue of near black is
    noise, so the darkest values are desaturated and lifted with a NEUTRAL pedestal tinted by the eye (never renormalised to a saturated colour), the
    floor is applied after the well, and the far field is softened (defocus) so the enlarged fibres do not read as fur."""
    n = len(irises)
    Wb, Hb = max(8, int(round(sc_b.W * scale))), max(8, int(round(sc_b.H * scale)))
    cx, cy, Rk = geo_b.c[:, 0] * scale, geo_b.c[:, 1] * scale, geo_b.R * scale
    Rm = float(Rk.mean())
    srcs = [np.asarray(ir.src, np.float32) / 255.0 for ir in irises]
    corner = max(math.hypot(px - cx[k], py - cy[k]) for k in range(n) for px in (0, Wb) for py in (0, Hb)) / Rm
    ks = float(prm.get("ks", np.clip(corner * 1.03, 3.0, 3.6)))
    cv = np.empty((Hb, Wb, 3), np.float32)
    sigma = 0.50
    rcorner = math.hypot(Wb / 2.0, Hb / 2.0)
    x = (np.arange(Wb, dtype=np.float32) + 0.5)[None, :]
    if n == 2:
        r0 = sc_b.rules[0]
        ux, uy = r0.ux, r0.uy
        mx, my = (cx[0] + cx[1]) / 2, (cy[0] + cy[1]) / 2
    db_idx = [k for k, c in enumerate(classes) if c == "dark_brown"]
    gr_idx = [k for k, c in enumerate(classes) if c == "grey"]
    ped_k = []
    for ir in irises:
        mc = np.asarray(ir.stats["mean_rgb"], np.float32) / 255.0
        mc = mc / max(float(mc.max()), 1e-3)
        ped_k.append((0.45 * mc + 0.55 * float(mc.mean())).astype(np.float32))
    rn_all = np.empty((Hb, Wb), np.float32)
    for y0 in range(0, Hb, BAND_ROWS):
        y1 = min(Hb, y0 + BAND_ROWS)
        y = (np.arange(y0, y1, dtype=np.float32) + 0.5)[:, None]
        dist = [np.sqrt((x - cx[k]) ** 2 + (y - cy[k]) ** 2) / Rk[k] for k in range(n)]
        if n == 2:
            s_ = ((x - mx) * ux + (y - my) * uy) / Rm
            wA = 1.0 - _smooth(-0.35, 0.35, s_)
            ws = [wA, 1.0 - wA]
            cols = []
            for k in range(2):                      # each person's enlarged iris only where its weight is not zero (about half of the canvas)
                nzc = np.nonzero((ws[k] > 1e-4).any(0))[0]
                c_ = np.zeros((y1 - y0, Wb, 3), np.float32)
                if len(nzc):
                    c0_, c1_ = int(nzc[0]), int(nzc[-1]) + 1
                    c_[:, c0_:c1_] = enlarge(srcs[k], cx[k], cy[k], Rk[k], ks, x[:, c0_:c1_], y)
                cols.append(c_)
        else:
            cols = [enlarge(srcs[k], cx[k], cy[k], Rk[k], ks, x, y) for k in range(n)]
            dn = [d * Rk[k] / Rm for k, d in enumerate(dist)]
            dmin = np.min(np.stack(dn), 0)
            ws = [np.exp(-(d * d - dmin * dmin) / (2 * sigma * sigma)) for d in dn]
            tot = sum(ws)
            ws = [w_ / tot for w_ in ws]
        F = sum(w_[..., None] * c_ for w_, c_ in zip(ws, cols))
        rn = np.min(np.stack(dist), 0)
        rn_all[y0:y1] = rn
        f = 0.64 - 0.30 * _smooth(1.0, 2.8, rn)
        F = F * f[..., None]
        if db_idx:
            cw = sum(ws[k] for k in db_idx)
            F = F * (1 - 0.30 * cw[..., None]) + 0.30 * cw[..., None] * COPPER * (f * 1.4)[..., None]
        if gr_idx:
            cw = sum(ws[k] for k in gr_idx)
            F = F * (1 - 0.25 * cw[..., None]) + 0.25 * cw[..., None] * STEEL * (f * 1.3)[..., None] + 0.03 * cw[..., None]
        m = F.max(-1, keepdims=True)
        lum = (F * np.array([0.299, 0.587, 0.114], np.float32)).sum(-1, keepdims=True)
        F = lum + (F - lum) * (0.30 + 0.70 * _smooth(0.015, 0.14, m))           # the hue of near black is noise: desaturate it
        ped = sum(ws[k][..., None] * ped_k[k] for k in range(n))
        floor = 0.13 + (0.06 * sum(ws[k] for k in db_idx)[..., None] if db_idx else 0.0)          # L* 14 (dark brown 22): never black
        F = np.maximum(F, ped * floor)
        e = None
        for k in range(n):
            ek = dist[k] - 1.0
            e = ek if e is None else np.minimum(e, ek)
        well = 0.42 + 0.58 * _smooth(0.0, 0.30, e)
        rc = np.sqrt((x - Wb / 2.0) ** 2 + (y - Hb / 2.0) ** 2) / rcorner
        vig = 1.0 - 0.45 * rc * rc
        out = F * (well * vig)[..., None]
        cv[y0:y1] = np.maximum(out, ped * 0.085)
    # far-field defocus: the enlarged fibres beyond about 1.2 R soften (fur -> nebula)
    soft = C.blur(cv, prm.get("far_blur", 0.10) * Rm, clip_negative=True)
    wt = (0.85 * _smooth(1.15, 2.6, rn_all))[..., None]
    cv = cv * (1.0 - wt) + soft * wt
    return cv, dict(ks=ks, corner_R=corner, base=(Wb, Hb))


def fill(sc, geo, irises, pals, discs, rnd, prm=None, base=None):
    """Universe canvas float32 (H, W, 3) in display space and an info dict. prm: ks, flakes (per artwork), stars (per S^2), far_blur (R).
    base = (scene, geo) of the canonical 1024 geometry (collision.render passes it): the soft base is computed ONCE on that geometry at BASE_LONG px and
    upsampled, so the 4096 master carries the very same fill as the preview; flakes and stars are drawn at full resolution."""
    prm = prm or {}
    W, H, S = sc.W, sc.H, sc.S
    n = len(irises)
    cx, cy, Rk, Rm = geo.c[:, 0], geo.c[:, 1], geo.R, geo.Rm
    classes = [ir.cls for ir in irises]
    sc_b, geo_b = base if base is not None else (sc, geo)
    scale = min(1.0, BASE_LONG / float(max(sc_b.W, sc_b.H)))
    cv0, info = _base_fill(sc_b, geo_b, irises, classes, prm, scale)
    cv = _resize_f(cv0, W, H)
    del cv0
    # fibre flakes: chips of the SAME iris's band, radial +-25 deg, curled, density exp(-e / 0.7 R) from e = 0.05 R (round 2c: shorter and fatter, dimmer:
    # the thin bright slivers read as hair)
    nfl = int(prm.get("flakes", 70 * n if n == 2 else min(260, 44 * n)))
    if nfl > 0:
        per = max(1, nfl // n)
        allp = PW.Particles()
        for k in range(n):
            th = rnd.uniform(per, 0, 2 * math.pi)
            e = np.minimum(0.05 + rnd.exponential(per, 0.6), 1.5)
            rr = Rk[k] * (1.0 + e)
            dp = rnd.uniform(per, 0.06, 0.15) * (1.0 + 0.7 * e)
            allp.add(x=cx[k] + rr * np.cos(th), y=cy[k] + rr * np.sin(th), d=dp * Rk[k], k=np.full(per, k), phi=th, e=e, cls=np.full(per, 2),
                     u=rnd.uniform(per), v=rnd.uniform(per), w=rnd.uniform(per))
        d = allp.cat()
        keep = ~geo.inside_any(d["x"], d["y"], 1.0) & (d["x"] > 0) & (d["x"] < W) & (d["y"] > 0) & (d["y"] < H)
        for kk_ in d:
            d[kk_] = d[kk_][keep]
        m = len(d["x"])
        kk = d["k"].astype(int)
        seeds = (rnd.uniform(m) * 1e9).astype(np.int64)
        asp = rnd.uniform(m, 0.10, 0.20)
        rot = d["phi"] + rnd.uniform(m, -math.radians(25), math.radians(25))
        curl = rnd.uniform(m, -0.20, 0.20)
        sx = np.zeros(m)
        sy = np.zeros(m)
        for i in range(m):
            dsc = discs[kk[i]]
            rho = 0.70 + 0.25 * rnd.uniform()
            ph = d["phi"][i] + 0.4 * (rnd.uniform() - 0.5)
            sx[i] = dsc.cx + rho * dsc.R * math.cos(ph)
            sy[i] = dsc.cy + rho * dsc.R * math.sin(ph)
        tint = np.zeros((m, 3), np.float32)
        for k in range(n):
            sel = kk == k
            if sel.any():
                tint[sel] = pals[k].chips2(d["phi"][sel], np.full(int(sel.sum()), 0.35), np.full(int(sel.sum()), 0.5), np.full(int(sel.sum()), 0.5))
        gain = rnd.uniform(m, 0.22, 0.50) * 0.75 * PW._depth(d["e"] * 0.7)
        RS.chunk_stamps(cv, None, d["x"], d["y"], np.maximum(d["d"] * 1.0, 3.0), rot, np.zeros(m, np.int64), _patch_fn_factory(discs, kk, sx, sy, 1.5),
                        tint, gain, 0.0, None, np.ones(m, bool), asp, seeds, curl)
        info["flakes"] = m
    # stars
    ns = int(prm.get("stars", 75) * (W * H) / float(S * S))
    if ns > 0:
        sxs = rnd.uniform(ns, 0, W)
        sys_ = rnd.uniform(ns, 0, H)
        ok = ~geo.inside_any(sxs, sys_, 1.02)
        sxs, sys_ = sxs[ok], sys_[ok]
        m = len(sxs)
        e_, kk_ = geo.e_field(sxs, sys_)
        cols = np.zeros((m, 3), np.float32)
        for k in range(n):
            sel = kk_ == k
            if sel.any():
                c = pals[k].chips2(np.full(int(sel.sum()), 0.0), np.full(int(sel.sum()), 0.9), np.full(int(sel.sum()), 0.3), np.full(int(sel.sum()), 0.5))
                cols[sel] = 0.65 * c + 0.35
        size = rnd.uniform(m, 0.0008, 0.0015) * S
        gain = 0.22 + 1.1 * rnd.uniform(m) ** 4
        RS.gauss_stamps(cv, sxs, sys_, size, cols, gain)
        info["stars"] = m
    return cv, info
