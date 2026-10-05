# -*- coding: utf-8 -*-
"""cx_extra: limbus breakup, foreground chunks and the D15 seam dust of the collision designs (numpy only)."""
from __future__ import annotations

# PORT of work package WP7A (step A): cx_extra.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (imports); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math

import numpy as np

from . import powder as PW
from . import raster as RS
from .compositor import value_noise, smooth

NB = PW.NB


def breakup(cv, geo, discs, rnd, prm, seed):
    """Limbus breakup on the OUTER arcs (brief 3.1 layer 6): pixels of the iris's own band 0.92-0.99 R pushed outward 0.02-0.04 R through a
    noise mask with holes, strength 0.4, off within 0.3 R of a notch. Added into cv (under the irises): the torn fringe beyond the F3 edge."""
    H, W = cv.shape[:2]
    n_done = 0
    for k in range(geo.n):
        dsc = discs[k]
        R = geo.R[k]
        rad = int(math.ceil(R * 1.07)) + 2
        x0, y0 = int(max(0, dsc.cx - rad)), int(max(0, dsc.cy - rad))
        x1, y1 = int(min(W, dsc.cx + rad)), int(min(H, dsc.cy + rad))
        if x1 <= x0 or y1 <= y0:
            continue
        gx = (np.arange(x0, x1, dtype=np.float32) + 0.5 - dsc.cx)[None, :]
        gy = (np.arange(y0, y1, dtype=np.float32) + 0.5 - dsc.cy)[:, None]
        r = np.sqrt(gx * gx + gy * gy) / R
        ring = (r > 0.995) & (r < 1.07)
        if not ring.any():
            continue
        ys, xs = np.nonzero(ring)
        rr = r[ys, xs]
        th = np.arctan2(gy[ys, 0], gx[0, xs])
        b = np.minimum(((th % (2 * math.pi)) * (NB / (2 * math.pi))).astype(np.int64), NB - 1)
        ok = geo.exposed[k][b] & (geo.notch_arc[k][b] > 0.30)
        ys, xs, rr, th = ys[ok], xs[ok], rr[ok], th[ok]
        if len(ys) == 0:
            continue
        fib = value_noise(th / 0.011, np.full(len(th), 3.0), seed + 13 * k)
        fib2 = value_noise(th / 0.004 + 9.0, np.full(len(th), 7.0), seed + 29 * k)
        lens = 0.008 + 0.034 * (0.6 * fib + 0.4 * value_noise(th / 0.05, np.full(len(th), 11.0), seed + 41 * k))
        hole = smooth(0.30, 0.52, 0.65 * fib2 + 0.35 * value_noise(th / 0.02, np.full(len(th), 5.0), seed + 53 * k))
        a = smooth(lens, 0.15 * lens, rr - 0.995) * hole * prm.get("breakup", 0.40)
        tsz = dsc.g.shape[0]
        Rg = tsz / 2.0
        sx = np.clip(Rg + 0.955 * Rg * np.cos(th), 0, tsz - 1.001)
        sy = np.clip(Rg + 0.955 * Rg * np.sin(th), 0, tsz - 1.001)
        xi, yi = np.floor(sx).astype(np.int64), np.floor(sy).astype(np.int64)
        fx, fy = (sx - xi)[:, None], (sy - yi)[:, None]
        g = dsc.g.astype(np.float32) / 255.0
        col = g[yi, xi] * (1 - fx) * (1 - fy) + g[yi, xi + 1] * fx * (1 - fy) + g[yi + 1, xi] * (1 - fx) * fy + g[yi + 1, xi + 1] * fx * fy
        cv[y0 + ys, x0 + xs] += (col * 1.05 * a[:, None]).astype(np.float32)
        n_done += len(ys)
    return n_done


def fg_chunks(geo, rnd, prm, theta_w):
    """2-4 foreground chunks per artwork (8-11 % R, blur 0.04 R, alpha about 0.4) at e >= 0.35 R, never over an iris."""
    P = PW.Particles()
    lo, hi = prm.get("fg", (2, 3))
    n = int(lo + rnd.uniform() * (hi - lo + 0.999))
    for i in range(n):
        k = int(rnd.uniform() * geo.n)
        if geo.arc_R[k] < 0.3:
            continue
        f, _ = PW._angdens(geo, k, rnd, prm, theta_w[k], jets=False)
        ui, th = PW._sample_theta(f, rnd, 1)
        e = rnd.uniform(None, 0.35, 0.70)
        rr = geo.R[k] * (1.0 + e)
        P.add(x=np.array([geo.c[k][0] + rr * math.cos(th[0])]), y=np.array([geo.c[k][1] + rr * math.sin(th[0])]),
              d=np.array([rnd.uniform(None, 8.0, 11.0) / 100.0 * geo.R[k]]), k=np.array([k]), src=5, phi=th, e=np.array([e]), cls=np.array([4]),
              u=np.array([rnd.uniform()]), v=np.array([rnd.uniform()]), w=np.array([rnd.uniform()]))
    return P


def seam_dust(geo, pals, rnd, W, H, prm, discs=None):
    """D15 (owner sign-off, default OFF), RESTRAINED (round 2c, AD F): the grit of the owner's H24 lying on the neighbouring iris, but only what a real
    crumbling edge would shed - chips of the FRONT iris's OWN zone-B colours (the real band pixels at the emission angle, slightly darkened: no lifted
    palette, no white facet, no glow), at most 0.012 R across, within 0.08 R of the front limb, alpha <= 0.35, about 25 per R of visible lens arc,
    on the back iris only. Returns (P, A, mask): P premultiplied colour (H, W, 3) 0..255, A alpha (H, W) 0..1 (img8 = P + img8 (1 - A)), mask bool of the
    touched pixels (excluded from the hash test with the flag on)."""
    P = np.zeros((H, W, 3), np.float32)
    A3 = np.zeros((H, W, 3), np.float32)
    xs_all, ys_all, d_all, k_all, phi_all = [], [], [], [], []
    for ri, r in enumerate(geo.sc.rules):
        if r.mode not in ("front_a", "front_b"):
            continue
        f, b = (r.a, r.b) if r.mode == "front_a" else (r.b, r.a)
        arc = 0.0
        nprobe = 1440
        thp = (np.arange(nprobe) + 0.5) * (2 * math.pi / nprobe)
        pxp = geo.c[f][0] + geo.R[f] * 1.004 * np.cos(thp)
        pyp = geo.c[f][1] + geo.R[f] * 1.004 * np.sin(thp)
        vis = np.hypot(pxp - geo.c[b][0], pyp - geo.c[b][1]) < geo.R[b] * 0.985
        for j in range(geo.n):
            if j not in (f, b):
                vis &= np.hypot(pxp - geo.c[j][0], pyp - geo.c[j][1]) > geo.R[j] * 1.0
        arc = float(vis.sum()) / nprobe * 2 * math.pi
        nmax = int(prm.get("seam_dust_per_R", 25) * arc)
        if nmax <= 0:
            continue
        idx = np.nonzero(vis)[0]
        th = thp[idx[np.minimum((rnd.uniform(nmax) * len(idx)).astype(int), len(idx) - 1)]]
        u = np.minimum(0.004 - 0.030 * np.log(np.maximum(rnd.uniform(nmax), 1e-6)), 0.08)
        rr = geo.R[f] * (1.0 + u)
        x = geo.c[f][0] + rr * np.cos(th)
        y = geo.c[f][1] + rr * np.sin(th)
        keep = np.hypot(x - geo.c[b][0], y - geo.c[b][1]) < geo.R[b] * 0.985
        for j in range(geo.n):
            if j not in (f, b):
                keep &= np.hypot(x - geo.c[j][0], y - geo.c[j][1]) > geo.R[j] * 1.0
        x, y, th = x[keep], y[keep], th[keep]
        m = len(x)
        if m == 0:
            continue
        xs_all.append(x)
        ys_all.append(y)
        k_all.append(np.full(m, f))
        phi_all.append(th)
        d_all.append(np.exp(np.log(0.0025) + rnd.uniform(m) * (np.log(0.012) - np.log(0.0025))) * geo.R[f] * 2.0)
    if not xs_all:
        return P, A3[..., 0], np.zeros((H, W), bool)
    x, y, k, phi, dd = (np.concatenate(v) for v in (xs_all, ys_all, k_all, phi_all, d_all))
    m = len(x)
    rgb = np.zeros((m, 3), np.float32)
    for kk in range(geo.n):
        sel = k == kk
        if not sel.any():
            continue
        if discs is not None:
            dsc = discs[kk]
            t = dsc.g.shape[0]
            Rg = t / 2.0
            sx = np.clip(Rg + 0.93 * Rg * np.cos(phi[sel]), 0, t - 1.001)
            sy = np.clip(Rg + 0.93 * Rg * np.sin(phi[sel]), 0, t - 1.001)
            xi, yi = np.floor(sx).astype(np.int64), np.floor(sy).astype(np.int64)
            fx, fy = (sx - xi)[:, None], (sy - yi)[:, None]
            gg = dsc.g.astype(np.float32) / 255.0
            col = gg[yi, xi] * (1 - fx) * (1 - fy) + gg[yi, xi + 1] * fx * (1 - fy) + gg[yi + 1, xi] * (1 - fx) * fy + gg[yi + 1, xi + 1] * fx * fy
            rgb[sel] = np.clip(col * (0.80 + 0.35 * rnd.uniform(int(sel.sum()))[:, None]), 0, 1)
        else:
            ns = int(sel.sum())
            rgb[sel] = pals[kk].chips2(phi[sel], 0.05 + 0.30 * rnd.uniform(ns), rnd.uniform(ns), rnd.uniform(ns)) * 0.6
    alpha = 0.35 * (0.45 + 0.55 * rnd.uniform(m))
    Rm = geo.Rm
    big = dd >= 0.0074 * Rm
    nb = int(big.sum())
    white = np.ones((m, 3), np.float32)
    if nb:
        rt = rnd.uniform((nb, 20))
        nv = 5 + np.minimum((rt[:, 3] * 4).astype(np.int64), 3)
        asp = 1.0 + 1.0 * rt[:, 2] ** 1.5
        rot = rt[:, 1] * 2 * math.pi
        RS.chip_polys(P, x[big], y[big], dd[big], rot, asp, nv, rgb[big] * 255.0 * alpha[big][:, None], 1.0, rt, None)
        RS.chip_polys(A3, x[big], y[big], dd[big], rot, asp, nv, white[big], alpha[big], rt, None)
    sm = ~big
    RS.gauss_stamps(P, x[sm], y[sm], np.maximum(dd[sm], 0.0016 * Rm) * 0.34, rgb[sm] * 255.0, alpha[sm] * 1.25)
    RS.gauss_stamps(A3, x[sm], y[sm], np.maximum(dd[sm], 0.0016 * Rm) * 0.34, white[sm], alpha[sm] * 1.25)
    A = np.clip(A3[..., 0], 0.0, 0.35)
    P = np.minimum(P, 255.0 * A[..., None])
    mask = (A > 2e-3)
    return P, A, mask


def matter_mask(sc, boxes):
    """Brief 3.0.4: matter fades over the last 0.04 S toward the canvas edge (an artwork must not look cropped) and is <= 15 % inside the text
    box + 0.02 S. Returns f(x, y) -> float32 factor for arrays of canvas coordinates of any shape."""
    W, H, S = sc.W, sc.H, sc.S

    def f(x, y):
        x = np.asarray(x, np.float32)
        y = np.asarray(y, np.float32)
        de = np.minimum(np.minimum(x, W - x), np.minimum(y, H - y))
        m = smooth(0.0, 0.04 * S, de)
        for (x0, y0, x1, y1) in boxes:
            dx = np.maximum(np.maximum(x0 - x, x - x1), 0.0)
            dy = np.maximum(np.maximum(y0 - y, y - y1), 0.0)
            m = m * (0.15 + 0.85 * smooth(0.0, 0.02 * S, np.hypot(dx, dy)))
        return m.astype(np.float32)
    return f
