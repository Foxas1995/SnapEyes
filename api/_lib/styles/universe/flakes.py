# -*- coding: utf-8 -*-
"""uni_flakes: the fibre flakes of the UNIVERSE family as sprites of the eye's own texture (AD round D10). numpy + PIL only.

A flake is a real CHIP of the same iris: a pointed sliver (quadratic Bezier, aspect 1:6 to 1:14, curl +-25 deg, radial +-25 deg, length class
0.06 / 0.12 / 0.22 R with lognormal sigma 0.5, x (1 + 0.8 e/R)) filled with a strip of the eye's own band 0.70-0.95 R at the emission angle
(1:1 scale, fibres run along the flake), opaque (alpha 0.88-0.98), a 1 px anti-aliased edge, lit from the upper left (the shadow side x 0.6).
60 percent of the flakes leave along 20-28 jets, 40 percent are scattered; the density falls as exp(-e / 0.55 R) from e0 to `reach`.
Sprites live on the GLOBAL coarse grid (see uni_engine.SpriteList), so they are band independent.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_flakes.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np

from .common import C
from .engine import SpriteList

LIGHT = np.array([-0.6, -0.8], np.float32)          # screen direction TOWARD the key light (upper left), brief 1.5.6
FLAKE_CLASSES = (0.06, 0.12, 0.22)                  # AD D10
FLAKE_CLASS_P = (0.45, 0.40, 0.15)
FLAKE_PX_CAP = 680                                  # sprite tiles are at most this many coarse px per side


def edge_fade(xs, ys, W, H, S, width=0.04):
    d = np.minimum(np.minimum(xs, W - xs), np.minimum(ys, H - ys)) / (width * S)
    d = np.clip(d, 0.0, 1.0)
    return d * d * (3.0 - 2.0 * d)


def _detail(src):
    """The source with its fibres stretched x1.7 about a 3 px local mean (cached): a flake is a small piece, it needs crisper fibres than the whole iris."""
    d = getattr(src, "_flake_detail", None)
    if d is None:
        B = C.blur(src.g, 3.0)
        d = np.clip(B + (src.g - B) * 1.7, 0.0, 1.0).astype(np.float32)
        src._flake_detail = d
    return d


def fibre_flakes(scene, ei, count, reach=1.6, taper=0.55, e0=0.04, lift=1.0, alpha=(0.88, 0.98), tag="flakes", blur_R=0.0,
                 size_k=1.0, jets=(20, 28), jet_share=0.60, growth=0.8, e_cap=1.5, region=None, lum_k=1.0):
    """Returns a SpriteList. blur_R > 0 makes the defocused depth flakes (blur in R units). region = (angle_lo, angle_hi) screen radians to emit
    into only (the wallpaper's lower accent). lum_k scales the flake luminance (Universe Duo: brighter chips)."""
    eye = scene.eyes[ei]
    src, R = eye.src, eye.R
    f = scene.fs
    rnd = scene.rand(f"{tag}/{ei}")
    n = int(count)
    sl = SpriteList()
    if n <= 0:
        return sl
    nj = int(jets[0] + rnd.uniform() * (jets[1] - jets[0] + 1))
    ja = (np.arange(nj) + rnd.uniform(nj) * 0.8) * (2 * math.pi / nj)
    jw = rnd.uniform(nj, 0.4, 1.6)
    jcdf = np.cumsum(jw) / jw.sum()
    is_jet = rnd.uniform(n) < jet_share
    jsel = np.minimum(np.searchsorted(jcdf, rnd.uniform(n)), nj - 1)
    phi = np.where(is_jet, ja[jsel] + np.radians(rnd.normal(n, 0.0, 4.5)), rnd.uniform(n) * 2 * math.pi)
    if region is not None:
        phi = region[0] + (phi % (2 * math.pi)) / (2 * math.pi) * (region[1] - region[0])
    u = rnd.uniform(n)
    span = 1.0 - math.exp(-(reach - e0) / taper)
    e = e0 - taper * np.log1p(-u * span)
    cls = np.searchsorted(np.cumsum(FLAKE_CLASS_P), rnd.uniform(n)).clip(0, 2)
    Lg = R * np.asarray(FLAKE_CLASSES)[cls] * np.exp(rnd.normal(n, 0.0, 0.5)) * (1.0 + growth * np.minimum(e, e_cap)) * size_k
    Lg = np.clip(Lg, 0.03 * R, 0.55 * R)
    aspect = rnd.uniform(n, 6.0, 14.0)
    wd = Lg / aspect
    psi = phi + np.radians(rnd.uniform(n, -25.0, 25.0))
    curl = np.radians(rnd.uniform(n, -25.0, 25.0))
    al_f = rnd.uniform(n, alpha[0], alpha[1])
    flip = rnd.uniform(n) < 0.5
    span_r_all = np.minimum(Lg / R, 0.22)
    rho0 = 0.70 + rnd.uniform(n) * (0.95 - 0.70 - span_r_all)
    pcx = eye.cx + (1.0 + e) * R * np.cos(phi)
    pcy = eye.cy + (1.0 + e) * R * np.sin(phi)
    fade = edge_fade(pcx, pcy, scene.W, scene.H, scene.S)
    d_ = eye.disc                                   # the flake texture comes from the graded DISC at canvas scale (1:1: the chip is as crisp as the iris itself at 4096)
    g = d_.rgb / np.float32(255.0)
    Td = g.shape[0]
    tcx, tcy, Rd = d_.cx - d_.x0, d_.cy - d_.y0, d_.R
    M = 10
    s_ = np.linspace(0.0, 1.0, M)
    Wc_max, Hc_max = int(math.ceil(scene.W / f)), int(math.ceil(scene.H / f))
    # ---- geometry of every flake at once: a quadratic Bezier per flake sampled at M points, its coarse-grid bounding box
    dxv, dyv = np.cos(psi), np.sin(psi)
    pxn, pyn = -dyv, dxv
    cs = Lg * 0.5 * np.sin(curl)
    P0x, P0y = pcx - dxv * Lg / 2, pcy - dyv * Lg / 2
    P2x, P2y = pcx + dxv * Lg / 2, pcy + dyv * Lg / 2
    P1x, P1y = pcx + pxn * cs, pcy + pyn * cs
    S_ = s_[None, :]
    PX = (1 - S_) ** 2 * P0x[:, None] + 2 * S_ * (1 - S_) * P1x[:, None] + S_ * S_ * P2x[:, None]
    PY = (1 - S_) ** 2 * P0y[:, None] + 2 * S_ * (1 - S_) * P1y[:, None] + S_ * S_ * P2y[:, None]
    pad = wd * 0.8 + 1.5 * f + 3.0 * blur_R * R
    I0 = np.maximum(np.floor((PX.min(1) - pad) / f).astype(np.int64), 0)
    I1 = np.minimum(np.ceil((PX.max(1) + pad) / f).astype(np.int64) + 1, Wc_max)
    J0 = np.maximum(np.floor((PY.min(1) - pad) / f).astype(np.int64), 0)
    J1 = np.minimum(np.ceil((PY.max(1) + pad) / f).astype(np.int64) + 1, Hc_max)
    hh_t, ww_t = J1 - J0, I1 - I0
    valid = (fade >= 0.02) & (hh_t >= 2) & (ww_t >= 2) & (hh_t <= FLAKE_PX_CAP) & (ww_t <= FLAKE_PX_CAP)
    idx_all = np.nonzero(valid)[0]
    if len(idx_all) == 0:
        return sl
    Hb_all = ((hh_t[idx_all] + 7) // 8) * 8
    Wb_all = ((ww_t[idx_all] + 7) // 8) * 8
    keys = Hb_all * 4096 + Wb_all
    for key in np.unique(keys):
        members = idx_all[keys == key]
        Hb, Wb = int(key // 4096), int(key % 4096)
        per = max(1, 1_200_000 // (Hb * Wb * (M - 1)))
        for c0 in range(0, len(members), per):
            ib = members[c0:c0 + per]
            nb = len(ib)
            X4 = ((I0[ib][:, None] + np.arange(Wb)[None, :] + 0.5) * f).astype(np.float32)[:, None, :, None]
            Y4 = ((J0[ib][:, None] + np.arange(Hb)[None, :] + 0.5) * f).astype(np.float32)[:, :, None, None]
            ax = PX[ib, :-1].astype(np.float32)
            ay = PY[ib, :-1].astype(np.float32)
            ex = (PX[ib, 1:] - PX[ib, :-1]).astype(np.float32)
            ey = (PY[ib, 1:] - PY[ib, :-1]).astype(np.float32)
            el2 = np.maximum(ex * ex + ey * ey, 1e-9)
            qx = X4 - ax[:, None, None, :]
            qy = Y4 - ay[:, None, None, :]
            tt = np.clip((qx * ex[:, None, None, :] + qy * ey[:, None, None, :]) / el2[:, None, None, :], 0.0, 1.0)
            dxs = qx - tt * ex[:, None, None, :]
            dys = qy - tt * ey[:, None, None, :]
            d2 = dxs * dxs + dys * dys
            kb = np.argmin(d2, axis=3)
            kk = kb[..., None]
            dmin = np.sqrt(np.take_along_axis(d2, kk, 3)[..., 0])
            tk = np.take_along_axis(tt, kk, 3)[..., 0]
            ex_k = np.take_along_axis(np.broadcast_to(ex[:, None, None, :], d2.shape), kk, 3)[..., 0]
            ey_k = np.take_along_axis(np.broadcast_to(ey[:, None, None, :], d2.shape), kk, 3)[..., 0]
            dx_k = np.take_along_axis(dxs, kk, 3)[..., 0]
            dy_k = np.take_along_axis(dys, kk, 3)[..., 0]
            sp = (kb + tk) / (M - 1.0)
            v = dmin * np.where(ex_k * dy_k - ey_k * dx_k >= 0, 1.0, -1.0)
            wh = 0.5 * wd[ib][:, None, None] * np.maximum(np.sin(np.pi * sp) ** 0.7, 0.14)
            cov = np.clip(0.5 + (wh - dmin) / float(f), 0.0, 1.0)
            jj, ii = np.indices((Hb, Wb))
            inside_tile = (jj[None] < hh_t[ib][:, None, None]) & (ii[None] < ww_t[ib][:, None, None])
            m = (cov > 0.02) & inside_tile
            rgbp = np.zeros((nb, Hb, Wb, 3), np.float32)
            a_b = np.zeros((nb, Hb, Wb), np.float32)
            bi, ji, xi = np.nonzero(m)
            if len(bi):
                fl = ib[bi]
                ph = phi[fl]
                spm = sp[bi, ji, xi]
                rr = rho0[fl] + np.where(flip[fl], 1.0 - spm, spm) * span_r_all[fl]
                cross = v[bi, ji, xi] / R
                cph, sph = np.cos(ph), np.sin(ph)
                sx = np.clip(tcx + Rd * (rr * cph - cross * sph) - 0.5, 0, Td - 1.001)
                sy = np.clip(tcy + Rd * (rr * sph + cross * cph) - 0.5, 0, Td - 1.001)
                x0 = np.floor(sx).astype(np.int32)
                y0 = np.floor(sy).astype(np.int32)
                fx_, fy_ = (sx - x0)[:, None], (sy - y0)[:, None]
                cm = (g[y0, x0] * (1 - fx_) * (1 - fy_) + g[y0, x0 + 1] * fx_ * (1 - fy_) + g[y0 + 1, x0] * (1 - fx_) * fy_ + g[y0 + 1, x0 + 1] * fx_ * fy_)
                Ls, Cc, hh = C.lch(cm)
                Lo = np.clip(Ls * 1.12 * lift * lum_k + 4.0, 0, 90.0)
                Co = np.minimum(Cc * 1.45, 66.0)
                col = C.from_lch(Lo, Co, hh).astype(np.float32)
                tx, ty = ex_k[bi, ji, xi], ey_k[bi, ji, xi]
                tn = np.maximum(np.hypot(tx, ty), 1e-6)
                sg = np.where(v[bi, ji, xi] >= 0, 1.0, -1.0)
                lit = (-ty / tn) * sg * LIGHT[0] + (tx / tn) * sg * LIGHT[1]          # +1: this side of the flake faces the light
                edge = np.clip(np.abs(v[bi, ji, xi]) / np.maximum(wh[bi, ji, xi], 1e-3), 0.0, 1.0) ** 1.5
                shade = 1.0 + edge * np.where(lit > 0, 0.22 * lit, 0.40 * lit)        # shadow side down to x 0.6 at the very edge
                al = cov[bi, ji, xi] * al_f[fl] * fade[fl]
                a_b[bi, ji, xi] = al
                rgbp[bi, ji, xi] = np.clip(col * shade[:, None], 0, 1.4) * al[:, None]
            for q in range(nb):
                i = ib[q]
                h_, w_ = int(hh_t[i]), int(ww_t[i])
                rg_, a_ = rgbp[q, :h_, :w_].copy(), a_b[q, :h_, :w_].copy()            # (float32 here, stored as float16 by the SpriteList)
                if blur_R > 0:
                    sgm = blur_R * R / f
                    rg_ = C.blur(rg_, sgm)
                    a_ = np.clip(C.blur(a_, sgm), 0, 1)
                sl.add(int(I0[i]), int(J0[i]), rg_, a_)
    return sl
