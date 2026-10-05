# -*- coding: utf-8 -*-
"""cx_raster: stamping of photographed-looking matter into the float canvas (numpy only).

All sizes arrive in canvas px but were derived from R units, so a 4096 render is the 1024 picture with more pixels:
  * dust (< 1.6 px): energy-conserving Gaussians (fx.core.splat logic, own faster scatter)
  * grains: convex polygons of 3-5 sides, anti-aliased by signed distance, facet lighting from the upper left, a bright edge on
    the lit facet, a soft dark facet on the far side (angular ceramic / mineral grit, never a round dot)
  * chunks: silhouettes from the flake-sheet atlas (real photographed shards) rotated and scaled, coloured with a patch of the
    SAME iris's band (real fibres) mixed with a lit palette colour
  * defocused blobs, streaks, foreground chunks
Everything is added into the canvas (float32 display space, screened later by the tone map).
"""
from __future__ import annotations

# PORT of work package WP7A (step A): cx_raster.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (the atlas class that read a path is gone (styles/atlas.py)); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math
import numpy as np

LIGHT = np.array([-0.55, -0.83], np.float32)      # key light from the upper left (screen y down)
LIGHT /= np.linalg.norm(LIGHT)
CHUNK = 1 << 21


def _erf(x):
    s = np.sign(x)
    a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-a * a)
    return (s * y).astype(np.float32)


def _scatter(layer, fy, fx, vals):
    """layer (H, W, 3) += vals at rows fy, cols fx (flat lists)."""
    H, W = layer.shape[:2]
    np.add.at(layer.reshape(-1, 3), fy * W + fx, vals)


# ----------------------------------------------------------------------------- dust: Gaussians, pixel integrated
def gauss_stamps(layer, xs, ys, sigma, rgb, gain):
    """Anti-aliased Gaussian stamps. sigma: px per stamp; gain: peak of the ideal Gaussian at the requested sigma (per stamp). Energy
    gain * 2 pi sigma^2 is kept when sigma is floored at 0.55 px (a sub-pixel speck is dimmer per pixel, like the master downsized)."""
    n = len(xs)
    if n == 0:
        return
    H, W = layer.shape[:2]
    sig = np.asarray(sigma, np.float64) * np.ones(n)
    energy = np.asarray(gain, np.float64) * np.ones(n) * 2.0 * math.pi * sig * sig
    s_eff = np.maximum(sig, 0.2)
    rad = np.ceil(3.0 * s_eff + 0.5).astype(np.int64)
    col = np.asarray(rgb, np.float32)
    if col.ndim == 1:
        col = np.broadcast_to(col, (n, 3))
    for r in np.unique(rad):
        ii = np.nonzero(rad == r)[0]
        K = 2 * r + 1
        per = max(1, CHUNK // (K * K))
        for c0 in range(0, len(ii), per):
            jj = ii[c0:c0 + per]
            x = xs[jj]
            y = ys[jj]
            i0x = np.floor(x).astype(np.int64) - r
            i0y = np.floor(y).astype(np.int64) - r
            ex = (i0x[:, None] + np.arange(K + 1)[None, :] - x[:, None]) / (s_eff[jj][:, None] * math.sqrt(2.0))
            ey = (i0y[:, None] + np.arange(K + 1)[None, :] - y[:, None]) / (s_eff[jj][:, None] * math.sqrt(2.0))
            gx = np.diff(0.5 * (1.0 + _erf(ex)), axis=1)
            gy = np.diff(0.5 * (1.0 + _erf(ey)), axis=1)
            w = (gy[:, :, None] * gx[:, None, :]) * energy[jj].astype(np.float32)[:, None, None]
            px = i0x[:, None, None] + np.arange(K)[None, None, :]
            py = i0y[:, None, None] + np.arange(K)[None, :, None]
            ok = (px >= 0) & (px < W) & (py >= 0) & (py < H) & (w > 1e-5)
            wb = np.broadcast_to(ok, w.shape)
            fy = np.broadcast_to(py, w.shape)[wb]
            fx = np.broadcast_to(px, w.shape)[wb]
            pi = np.broadcast_to(np.arange(len(jj))[:, None, None], w.shape)[wb]
            _scatter(layer, fy, fx, w[wb][:, None] * col[jj][pi])


# ----------------------------------------------------------------------------- grains: convex polygons
def poly_stamps(layer, xs, ys, rad_px, rot, aspect, nv, rgb, gain, rnd_seed=1, rnd_arr=None):
    """Anti-aliased convex polygons with 3-5 sides and facet lighting. rad_px: circumradius px; rot: rad; aspect: 0.4..1
    (length : width across the local v axis); nv: sides (3..5) per grain; rgb: (n, 3) base colour; gain: brightness per grain."""
    n = len(xs)
    if n == 0:
        return
    H, W = layer.shape[:2]
    g = np.random.Generator(np.random.PCG64(rnd_seed))
    nv = np.asarray(nv, np.float32) * np.ones(n, np.float32)
    aspect = np.asarray(aspect, np.float32) * np.ones(n, np.float32)
    rot = np.asarray(rot, np.float32) * np.ones(n, np.float32)
    if rnd_arr is not None:                                   # per-particle random numbers: the same grain looks the same at any resolution
        jitter = np.asarray(rnd_arr[:, :5], np.float32)
        apo = (0.86 + 0.14 * np.asarray(rnd_arr[:, 5:10], np.float32)).astype(np.float32)
    else:
        jitter = g.random((n, 5)).astype(np.float32)
        apo = (0.86 + 0.14 * g.random((n, 5))).astype(np.float32)       # apothem factors
    step = (2 * math.pi / nv).astype(np.float32)
    idx5 = np.arange(5, dtype=np.float32)[None, :]
    ang = idx5 * step[:, None] + (jitter - 0.5) * 0.9 * step[:, None]
    valid = idx5 < nv[:, None]
    hap = np.where(valid, apo, np.float32(1e4))
    nx_l = np.cos(ang)
    ny_l = np.sin(ang)
    cr, sr = np.cos(rot).astype(np.float32), np.sin(rot).astype(np.float32)
    nwx = nx_l * cr[:, None] - ny_l * sr[:, None]
    nwy = nx_l * sr[:, None] + ny_l * cr[:, None]
    lit = nwx * LIGHT[0] + nwy * LIGHT[1]
    R = (np.maximum(np.asarray(rad_px, np.float32), 0.3) * np.ones(n, np.float32)).astype(np.float32)
    rk = np.ceil(R * 2.0 + 2.0).astype(np.int64)          # a triangle's vertices reach 2x its apothem: the window must hold them at every resolution
    col = np.asarray(rgb, np.float32)
    gn = np.asarray(gain, np.float32) * np.ones(n, np.float32)
    for r in np.unique(rk):
        ii = np.nonzero(rk == r)[0]
        K = 2 * r + 1
        per = max(1, CHUNK // (K * K * 4))
        for c0 in range(0, len(ii), per):
            jj = ii[c0:c0 + per]
            m = len(jj)
            x = xs[jj].astype(np.float32)
            y = ys[jj].astype(np.float32)
            i0x = np.floor(x).astype(np.int64) - r
            i0y = np.floor(y).astype(np.int64) - r
            dx = (i0x[:, None, None] + np.arange(K)[None, None, :] + 0.5 - x[:, None, None]).astype(np.float32)
            dy = (i0y[:, None, None] + np.arange(K)[None, :, None] + 0.5 - y[:, None, None]).astype(np.float32)
            dx = np.broadcast_to(dx, (m, K, K))
            dy = np.broadcast_to(dy, (m, K, K))
            u = dx * cr[jj][:, None, None] + dy * sr[jj][:, None, None]
            v = (-dx * sr[jj][:, None, None] + dy * cr[jj][:, None, None]) / aspect[jj][:, None, None]
            rho_c = (0.22 * R[jj])[:, None, None]                     # corner rounding radius, relative to the grain
            pos2 = np.zeros((m, K, K), np.float32)
            smax = np.full((m, K, K), -1e9, np.float32)
            lit_star = np.zeros((m, K, K), np.float32)
            for i in range(5):
                s_i = u * nx_l[jj, i][:, None, None] + v * ny_l[jj, i][:, None, None] - (hap[jj, i] * R[jj])[:, None, None] + rho_c
                better = s_i > smax
                smax = np.where(better, s_i, smax)
                lit_star = np.where(better, lit[jj, i][:, None, None], lit_star)
                pos2 += np.maximum(s_i, 0.0) ** 2
            sdf = np.sqrt(pos2) + np.minimum(smax, 0.0) - rho_c          # rounded convex polygon: exact distance inside, round corners outside
            cov = np.clip(0.5 - (sdf + 0.042 / R[jj][:, None, None]) / 1.0, 0.0, 1.0)       # the 1 px ramp adds 0.083 pi px^2 to any shape: shrink it back (area kept at every resolution)
            depth = np.clip(-sdf / (0.55 * R[jj][:, None, None]), 0.0, 3.0)
            edge = np.exp(-depth * 2.2)
            grain = 1.0 + 0.11 * np.sin(u * (37.0 / R[jj][:, None, None]) + 6.0 * nx_l[jj, 0][:, None, None]) * np.sin(v * (29.0 / R[jj][:, None, None]) + 4.0 * ny_l[jj, 1][:, None, None])   # matte mineral grain
            shade = (0.90 + 0.09 * lit_star + 0.15 * np.maximum(lit_star, 0.0) ** 3 * edge - 0.05 * (1.0 - edge) * np.maximum(-lit_star, 0)) * grain
            val = cov * np.maximum(shade, 0.15) * gn[jj][:, None, None]
            px = i0x[:, None, None] + np.arange(K)[None, None, :]
            py = i0y[:, None, None] + np.arange(K)[None, :, None]
            ok = (np.broadcast_to(px, val.shape) >= 0) & (np.broadcast_to(px, val.shape) < W) & (np.broadcast_to(py, val.shape) >= 0) & \
                 (np.broadcast_to(py, val.shape) < H) & (val > 1e-4)
            fy = np.broadcast_to(py, val.shape)[ok]
            fx = np.broadcast_to(px, val.shape)[ok]
            pi = np.broadcast_to(np.arange(m)[:, None, None], val.shape)[ok]
            _scatter(layer, fy, fx, val[ok][:, None] * col[jj][pi])


# ----------------------------------------------------------------------------- chunks: atlas silhouettes with iris-band fibres
# the chip atlas is read through api/_lib/styles/atlas.py (checked against the registry's sha256), never from a path


def _bilinear(a, x, y):
    h, w = a.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = (x - x0)
    fy = (y - y0)
    if a.ndim == 3:
        fx = fx[..., None]
        fy = fy[..., None]
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)


def chunk_stamps(layer, atlas, xs, ys, size_px, rot, sprite_idx, patch_fn, tint, gain, defocus_px=0.0, flip=None, iris_mode=None, aspect=None, seeds=None, curl=None):
    """size_px: chunk diameter px. patch_fn(i, K, rot) -> (K, K, 3) float 0..1 patch of the iris band (or None). tint: (n, 3) palette
    colour of the chip. The chip colour = 0.55 patch (lifted, real fibres) + 0.45 palette, shaded by the sprite luminance."""
    n = len(xs)
    H, W = layer.shape[:2]
    for i in range(n):
        sz = float(size_px[i])
        r = int(math.ceil(sz * 0.72 + 2 + defocus_px * 2))
        K = 2 * r + 1
        x, y = float(xs[i]), float(ys[i])
        i0x, i0y = int(math.floor(x)) - r, int(math.floor(y)) - r
        xa, ya, xb, yb = max(0, i0x), max(0, i0y), min(W, i0x + K), min(H, i0y + K)
        if xa >= xb or ya >= yb:
            continue
        gx = (np.arange(xa, xb, dtype=np.float32) + 0.5 - x)[None, :]
        gy = (np.arange(ya, yb, dtype=np.float32) + 0.5 - y)[:, None]
        c, s = math.cos(rot[i]), math.sin(rot[i])
        u = (gx * c + gy * s) / sz            # -0.5..0.5 across the chip (sprite frame)
        v = (-gx * s + gy * c) / sz
        if flip is not None and flip[i]:
            u = -u
        sx = (u + 0.5) * 120 + 4.0            # atlas is 128 px with the shard fitted to about 128; keep a 4 px margin
        sy = (v + 0.5) * 120 + 4.0
        k = int(sprite_idx[i]) % (atlas.n if atlas is not None else 1)
        is_iris = iris_mode is not None and bool(iris_mode[i])
        if is_iris:
            if curl is not None:
                v = v - float(curl[i]) * u * u * 2.0               # a bent sliver (fibre flake): the centre line is a parabola
            asp = float(aspect[i]) if aspect is not None else 0.7
            th = np.arctan2(v, u * asp + 1e-9)
            rs = np.sqrt((u / 0.5) ** 2 + (v / (0.5 * asp)) ** 2)
            g_ = np.random.Generator(np.random.PCG64(int(seeds[i]) if seeds is not None else i))
            ph = g_.random(4) * 6.283
            edge = 1.0 + 0.14 * np.sin(2 * th + ph[0]) + 0.10 * np.sin(3 * th + ph[1]) + 0.07 * np.sin(5 * th + ph[2])
            mk = np.clip((edge - rs) * 0.5 * sz + 0.5, 0.0, 1.0).astype(np.float32)
            mk = mk * (0.88 + 0.12 * np.sin(4 * th + ph[3]) ** 2)
        else:
            mk = _bilinear(atlas.mask[k], sx, sy)
            mk = np.where((sx >= 0) & (sx <= 127) & (sy >= 0) & (sy <= 127), mk, 0.0)
        if defocus_px > 0:
            mk = _soft(mk, defocus_px)
        if is_iris:
            # a soft dome: lit from the upper left, plus the fibres of the patch
            nx_, ny_ = u * 2.0, v * 2.0 / max(asp, 0.3)
            lx = c * LIGHT[0] + s * LIGHT[1]
            ly = -s * LIGHT[0] + c * LIGHT[1]
            shade = np.clip(1.0 + 0.30 * (-(nx_ * lx + ny_ * ly)) * (np.clip(rs, 0, 1)), 0.55, 1.4)
        else:
            lum = _bilinear(atlas.lum[k], sx, sy)
            mval = atlas.mask[k] > 0.5
            mean = float(atlas.lum[k][mval].mean()) if mval.any() else 0.5
            shade = np.clip(lum / max(mean, 1e-3), 0.2, 2.2)
        patch = patch_fn(i, xb - xa, yb - ya, rot[i]) if patch_fn is not None else None
        t = np.asarray(tint[i], np.float32)
        if patch is not None:
            colr = 0.45 * patch + 0.55 * t[None, None, :]
        else:
            colr = np.broadcast_to(t, (yb - ya, xb - xa, 3))
        val = (mk * (0.42 + 0.48 * shade) * float(gain[i]))[..., None] * colr
        layer[ya:yb, xa:xb] += val.astype(np.float32)


def _soft(a, sigma_px):
    """Small separable Gaussian blur of a tiny 2-D window."""
    r = max(1, int(math.ceil(3 * sigma_px)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_px) ** 2)
    k = (k / k.sum()).astype(np.float32)
    p = np.pad(a, ((r, r), (0, 0)), mode="edge")
    a = sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))
    p = np.pad(a, ((0, 0), (r, r)), mode="edge")
    a = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
    return a


# ----------------------------------------------------------------------------- streaks and soft blobs
def streak_stamps(layer, xs, ys, length_px, width_px, ang, rgb, gain):
    """Motion streaks: anisotropic Gaussians along ang (rad), sigma_u = length / 2.6, sigma_v = width."""
    n = len(xs)
    H, W = layer.shape[:2]
    for i in range(n):
        su = max(float(length_px[i]) / 2.6, 0.6)
        sv = max(float(width_px[i]), 0.55)
        r = int(math.ceil(3 * su)) + 1
        x, y = float(xs[i]), float(ys[i])
        xa, ya, xb, yb = max(0, int(x) - r), max(0, int(y) - r), min(W, int(x) + r + 1), min(H, int(y) + r + 1)
        if xa >= xb or ya >= yb:
            continue
        gx = (np.arange(xa, xb, dtype=np.float32) + 0.5 - x)[None, :]
        gy = (np.arange(ya, yb, dtype=np.float32) + 0.5 - y)[:, None]
        c, s = math.cos(ang[i]), math.sin(ang[i])
        u = gx * c + gy * s
        v = -gx * s + gy * c
        g = np.exp(-0.5 * (u / su) ** 2 - 0.5 * (v / sv) ** 2)
        norm = sv / max(float(width_px[i]), 0.55)
        layer[ya:yb, xa:xb] += (g * float(gain[i]) * norm)[..., None] * np.asarray(rgb[i], np.float32)


# ----------------------------------------------------------------------------- chips v2 (round 2c): small irregular convex chips
def chip_polys(layer, xs, ys, size_px, rot, aspect, nv, rgb, gain, rt, facet=None):
    """Small chips as rounded CONVEX polygons (round 2c AD fix: 5-8 vertices, corner rounding 15 % of the size, aspect at most 2.2 : 1, flat
    opaque colour, NO regular texture inside). Geometry comes from R units (size_px is the equivalent diameter in canvas px) plus a per-chip
    table rt (n, >= 12) drawn before any culling, so a chip looks the same at 1024 and 4096; coverage is the signed-distance ramp of the exact
    rounded polygon (box-filter coverage, no pre-baked bitmap, nothing tiled).
    xs, ys: centres px; size_px: equivalent diameter px; rot: rad; aspect: length : width (>= 1, <= 2.2); nv: 5..8; rgb (n, 3): chip colour
    (already lit by its own luminance factor); gain (n,): opacity-like multiplier; facet (n,) bool: a thin lit edge (15 % of the chips)."""
    n = len(xs)
    if n == 0:
        return
    H, W = layer.shape[:2]
    size = np.maximum(np.asarray(size_px, np.float32), 0.35)
    nvv = np.asarray(nv, np.int64)
    asp = np.clip(np.asarray(aspect, np.float32), 1.0, 2.2)
    rot = np.asarray(rot, np.float32)
    rgbf = np.asarray(rgb, np.float32)
    gn = np.asarray(gain, np.float32) * np.ones(n, np.float32)
    # circumradius so the polygon holds the area of a disc of diameter `size`; semi axes a (along rot) and b (across)
    Rc = 0.5 * size * np.sqrt(2.0 * math.pi / (nvv * np.sin(2.0 * math.pi / nvv))) * 1.02
    a_ax = Rc * np.sqrt(asp)
    b_ax = Rc / np.sqrt(asp)
    MAXV = 8
    idx = np.arange(MAXV, dtype=np.float32)[None, :]
    step = (2.0 * math.pi / nvv).astype(np.float32)[:, None]
    jit = (np.asarray(rt[:, 0:MAXV], np.float32) - 0.5) * 0.62
    ang = (idx + jit) * step + np.asarray(rt[:, 8:9], np.float32) * 2.0 * math.pi
    valid = idx < nvv[:, None]
    hap = 0.80 + 0.20 * np.asarray(rt[:, 9:9 + MAXV] if rt.shape[1] >= 9 + MAXV else np.roll(rt[:, 0:MAXV], 3, axis=1), np.float32)
    hap = np.where(valid, hap, np.float32(1e4))
    nlx, nly = np.cos(ang), np.sin(ang)
    lit_dir = np.asarray(LIGHT, np.float32)
    cr, sr = np.cos(rot), np.sin(rot)
    # lit-ness of every edge normal in the world frame (for the facet edge)
    nwx = nlx * cr[:, None] - nly * sr[:, None]
    nwy = nlx * sr[:, None] + nly * cr[:, None]
    lit = nwx * lit_dir[0] + nwy * lit_dir[1]
    rk = np.ceil(np.maximum(a_ax, b_ax) * 1.3 + 2.0).astype(np.int64)
    for r in np.unique(rk):
        ii = np.nonzero(rk == r)[0]
        K = 2 * int(r) + 1
        per = max(1, CHUNK // (K * K * 3))
        for c0 in range(0, len(ii), per):
            jj = ii[c0:c0 + per]
            m = len(jj)
            x = np.asarray(xs[jj], np.float32)
            y = np.asarray(ys[jj], np.float32)
            i0x = np.floor(x).astype(np.int64) - int(r)
            i0y = np.floor(y).astype(np.int64) - int(r)
            dx = (i0x[:, None, None] + np.arange(K)[None, None, :] + 0.5 - x[:, None, None]).astype(np.float32)
            dy = (i0y[:, None, None] + np.arange(K)[None, :, None] + 0.5 - y[:, None, None]).astype(np.float32)
            dx = np.broadcast_to(dx, (m, K, K))
            dy = np.broadcast_to(dy, (m, K, K))
            u = (dx * cr[jj][:, None, None] + dy * sr[jj][:, None, None]) / a_ax[jj][:, None, None]       # unit-disc frame (a, b scaled out)
            v = (-dx * sr[jj][:, None, None] + dy * cr[jj][:, None, None]) / b_ax[jj][:, None, None]
            rho_c = 0.15 * np.float32(1.0)
            pos2 = np.zeros((m, K, K), np.float32)
            smax = np.full((m, K, K), -1e9, np.float32)
            lit_star = np.zeros((m, K, K), np.float32)
            for i in range(MAXV):
                vmask = valid[jj, i]
                if not vmask.any():
                    continue
                s_i = u * nlx[jj, i][:, None, None] + v * nly[jj, i][:, None, None] - (hap[jj, i][:, None, None] - rho_c)
                s_i = np.where(vmask[:, None, None], s_i, np.float32(-1e4))
                better = s_i > smax
                smax = np.where(better, s_i, smax)
                lit_star = np.where(better, lit[jj, i][:, None, None], lit_star)
                pos2 += np.maximum(s_i, 0.0) ** 2
            sdf_u = np.sqrt(pos2) + np.minimum(smax, 0.0) - rho_c                    # rounded convex polygon distance in the unit frame
            sdf = sdf_u * (0.5 * (a_ax[jj] + b_ax[jj]))[:, None, None]
            cov = np.clip(0.5 - (sdf - 0.04), 0.0, 1.0)
            val = cov * gn[jj][:, None, None]
            px = i0x[:, None, None] + np.arange(K)[None, None, :]
            py = i0y[:, None, None] + np.arange(K)[None, :, None]
            col = np.broadcast_to(rgbf[jj][:, None, None, :], (m, K, K, 3))
            # a flat chip lit from the upper left: its lit side a little brighter, its shadow side darker (no texture)
            proj = (dx * lit_dir[0] + dy * lit_dir[1]) / np.maximum(Rc[jj], 0.5)[:, None, None]
            col = col * (1.0 + 0.20 * np.clip(proj, -1.0, 1.0))[..., None]
            if facet is not None and facet[jj].any():
                fm = np.asarray(facet[jj], np.float32)[:, None, None]
                depth = np.clip(-sdf / (0.45 * np.maximum(Rc[jj], 0.5)[:, None, None]), 0.0, 3.0)
                hl = fm * 0.55 * np.maximum(lit_star, 0.0) ** 2 * np.exp(-depth * 2.6)
                col = col + hl[..., None] * (1.0 - col) * 0.8
            col = np.minimum(col, 0.80)                   # below the tone-map knee (0.8): the shoulder is non-linear, so a chip brighter than it would
                                                          # lose energy differently at 1024 and 4096 (box-reduced) and T9 would drop
            okm = (np.broadcast_to(px, val.shape) >= 0) & (np.broadcast_to(px, val.shape) < W) & (np.broadcast_to(py, val.shape) >= 0) & \
                  (np.broadcast_to(py, val.shape) < H) & (val > 1e-4)
            fy = np.broadcast_to(py, val.shape)[okm]
            fx = np.broadcast_to(px, val.shape)[okm]
            _scatter(layer, fy, fx, val[okm][:, None] * col[okm])
