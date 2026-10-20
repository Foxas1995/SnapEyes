# -*- coding: utf-8 -*-
"""styles.ensemble.pieces: the small drawing pieces the ensemble looks share (hairlines, star dust, auras, the black gap, sparkles), ported from the laboratory of the
pairs and families round (proto_pf/pieces.py, 2026-10-20) without a change to what they draw. All of them draw into the float canvas BEFORE the irises are
pasted; sizes are in R and S units, so a 4096 px master is exactly the 1024 px preview scaled (T9); every random number comes from the picture's own seed
(ctx.rand). numpy and PIL only, no plate, no model, nothing that is not already in the engine's kit."""
from __future__ import annotations

import math

import numpy as np

from .. import core as C
from ..singles import gold as G

TWO_PI = 2.0 * math.pi
F32 = np.float32
gold_ramp = G.gold_ramp
GOLD_LINE = "#E8C27A"
GOLD_HOT = "#FFF2D4"


def smooth(x):
    return C.smoothstep(x)


def own_colour(iris, lift=1.30, sat=1.30, toward=None, t=0.0):
    """The eye's own colour for a halo or a thread: the median of its ring colours (the ring is measured on the canonical grade), lifted a little, optionally
    warmed toward `toward` (rgb 0..1) by t. (3,) float32 0..1."""
    ring = np.asarray(iris.ring, np.float32)
    med = np.median(ring, axis=0).astype(np.float32)
    col = C.boost(med * 1.15, lift, sat)
    if toward is not None and t:
        col = C.mix(col, np.asarray(toward, np.float32), float(t))
    return np.clip(col, 0.0, 1.0).astype(np.float32)


def rho_to_discs(xs, ys, discs):
    """The smallest distance (in R of the disc it is nearest to) of each point to the discs: points (n,) -> (n,) float32."""
    out = np.full(len(xs), 1e9, np.float32)
    for d in discs:
        out = np.minimum(out, (np.hypot(xs - d.cx, ys - d.cy) / d.R).astype(np.float32))
    return out


def moat(xs, ys, discs, inner=1.0, width=0.08):
    """0 inside `inner` R of any disc, rising smoothly to 1 over `width` R: a thread that stops short of an iris and leaves it a black moat. xs, ys: any
    broadcastable arrays."""
    xs, ys = np.broadcast_arrays(np.asarray(xs, np.float32), np.asarray(ys, np.float32))
    out = np.full(xs.shape, 1e9, np.float32)
    for d in discs:
        out = np.minimum(out, (np.hypot(xs - d.cx, ys - d.cy) / d.R).astype(np.float32))
    return smooth((out - inner) / width)


def _put(view, light, mode):
    """Light into a view of the canvas, in place: 'screen' (1 - (1 - a)(1 - b): a hairline over a bright corona never burns out) or 'add'."""
    if mode == "screen":
        np.clip(light, 0.0, 1.0, out=light)
        view[...] = 1.0 - (1.0 - view) * (1.0 - light)
    else:
        view += light


def ring_line(cv, cx, cy, r, sigma, rgb, peak, a0=None, a1=None, weight=None, glow=0.0, glow_scale=6.0, mode="screen"):
    """A circular hairline (centre cx, cy, radius r px, Gaussian across it of sigma px) added straight into the canvas, row by row inside the annulus only: the
    arc from angle a0 to a1 (rad, screen, clockwise from 3 o'clock; both None: the whole circle), `weight(xs, y)` a per pixel factor (a moat, an edge fade).
    glow > 0 repeats it wider (glow_scale x sigma) and fainter (glow x peak)."""
    H, W = cv.shape[:2]
    sg = max(float(sigma), 0.5)
    amp = float(peak) * min(1.0, float(sigma) / sg)
    col = np.asarray(rgb, np.float32)
    rw = 4.0 * sg + 1.5
    ro, ri = r + rw, max(r - rw, 0.0)
    y0, y1 = max(0, int(cy - ro)), min(H, int(cy + ro) + 2)
    for y in range(y0, y1):
        dy = (y + 0.5) - cy
        if abs(dy) >= ro:
            continue
        xo = math.sqrt(ro * ro - dy * dy)
        xi = math.sqrt(ri * ri - dy * dy) if abs(dy) < ri else -1.0
        spans = ((cx - xo, cx + xo),) if xi < 0 else ((cx - xo, cx - xi), (cx + xi, cx + xo))
        for (xa, xb) in spans:
            ia, ib = max(0, int(math.ceil(xa - 0.5))), min(W, int(math.floor(xb - 0.5)) + 1)
            if ib <= ia:
                continue
            xs = np.arange(ia, ib, dtype=np.float32) + 0.5
            d = np.hypot(xs - np.float32(cx), np.float32(dy)) - np.float32(r)
            a = np.exp(-0.5 * (d / np.float32(sg)) ** 2) * np.float32(amp)
            if a0 is not None:
                th = np.arctan2(np.float32(dy), xs - np.float32(cx)) % np.float32(TWO_PI)
                lo, hi = a0 % TWO_PI, a1 % TWO_PI
                inside = (th >= lo) & (th <= hi) if lo <= hi else (th >= lo) | (th <= hi)
                a = a * inside
            if weight is not None:
                a = a * np.asarray(weight(xs, y + 0.5), np.float32)
            _put(cv[y, ia:ib], a[:, None] * col[None, :], mode)
    if glow:
        ring_line(cv, cx, cy, r, sg * glow_scale, rgb, float(peak) * float(glow), a0, a1, weight, 0.0, mode=mode)


def seg_line(cv, x0, y0, x1, y1, sigma, rgb, peak, weight=None, glow=0.0, glow_scale=7.0, along=None, mode="screen"):
    """A straight hairline from (x0, y0) to (x1, y1) (px), Gaussian across it, added straight into the canvas inside its own bounding box; `weight(xs, ys)` a
    factor per pixel (xs, ys broadcast arrays), `along(t)` a factor along the line (t 0..1)."""
    H, W = cv.shape[:2]
    sg = max(float(sigma), 0.5)
    amp = float(peak) * min(1.0, float(sigma) / sg)
    rw = 4.0 * sg + 1.5
    xa, xb = max(0, int(min(x0, x1) - rw)), min(W, int(max(x0, x1) + rw) + 2)
    ya, yb = max(0, int(min(y0, y1) - rw)), min(H, int(max(y0, y1) + rw) + 2)
    if xb <= xa or yb <= ya:
        return
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    xs = (np.arange(xa, xb, dtype=np.float32) + 0.5)[None, :]
    ys = (np.arange(ya, yb, dtype=np.float32) + 0.5)[:, None]
    t = ((xs - np.float32(x0)) * np.float32(ux) + (ys - np.float32(y0)) * np.float32(uy))
    d = (-(xs - np.float32(x0)) * np.float32(uy) + (ys - np.float32(y0)) * np.float32(ux))
    tc = np.clip(t, 0.0, L)
    dist = np.sqrt(d * d + (t - tc) ** 2)                                    # distance to the SEGMENT (round caps)
    a = np.exp(-0.5 * (dist / np.float32(sg)) ** 2) * np.float32(amp)
    if along is not None:
        a = a * np.asarray(along(tc / np.float32(L)), np.float32)
    if weight is not None:
        a = a * np.asarray(weight(xs, ys), np.float32)
    _put(cv[ya:yb, xa:xb], a[..., None] * np.asarray(rgb, np.float32)[None, None, :], mode)
    if glow:
        seg_line(cv, x0, y0, x1, y1, sg * glow_scale, rgb, float(peak) * float(glow), weight, 0.0, along=along, mode=mode)


def star_field(layer, ctx, rnd, n_range, discs, avoid=1.5, y_range=None, cool=("#D9E2FF", "#FFF4E4"), size=(0.0004, 0.0006), alpha=(0.06, 0.19)):
    """Sparse stars (the celestial gold single's own recipe) at uniform positions, none within `avoid` R of an iris, scaled by the canvas area so that a 3:2
    canvas carries 1.5 x the stars of a square. y_range (y0, y1) as shares of H."""
    W, H, S = ctx.W, ctx.H, ctx.S
    area = (W * H) / float(S * S)
    ns = int((n_range[0] + (n_range[1] - n_range[0]) * float(rnd.uniform())) * area)
    sx, sy = rnd.uniform(ns) * W, rnd.uniform(ns) * H
    sa = alpha[0] + (alpha[1] - alpha[0]) * rnd.uniform(ns) ** 2.0
    sz = (size[0] + size[1] * rnd.uniform(ns)) * S
    col = C.mix(C.rgb01(cool[0])[None, :], C.rgb01(cool[1])[None, :], rnd.uniform(ns)[:, None])
    keep = rho_to_discs(sx, sy, discs) > avoid
    if y_range is not None:
        keep &= (sy >= y_range[0] * H) & (sy <= y_range[1] * H)
    layer.splat(sx[keep], sy[keep], sz[keep], col[keep], sa[keep], min_sigma=0.5)
    return sx[keep], sy[keep], sa[keep], col[keep]


def gold_dust(layer, ctx, rnd, n_range, centres, r_range=(1.30, 2.20), discs=None, orbit_share=0.0, orbit_r=1.39, avoid=1.28, amp=0.9):
    """Gold dust round each centre (cx, cy, R): the celestial gold single's dust (1.30 to 2.20 R, sizes 0.0004 to 0.0014 S, a gold ramp colour), with
    orbit_share of it hugging the orbit of radius orbit_r R. n_range is the count for ONE centre; none within `avoid` R of a disc."""
    S = ctx.S
    discs = discs if discs is not None else ctx.discs
    for (cx, cy, R) in centres:
        nd = int(n_range[0] + (n_range[1] - n_range[0]) * float(rnd.uniform()))
        n_orb = int(round(orbit_share * nd))
        t_ = rnd.uniform(n_orb) * TWO_PI
        ox, oy = cx + orbit_r * R * np.cos(t_), cy + orbit_r * R * np.sin(t_)
        off = rnd.normal(n_orb, 0.0, 0.045) * R
        ox, oy = ox + np.cos(t_) * off, oy + np.sin(t_) * off
        r_ = r_range[0] + (r_range[1] - r_range[0]) * rnd.uniform(nd - n_orb) ** 0.8
        a_ = rnd.uniform(nd - n_orb) * TWO_PI
        dx = np.concatenate([ox, cx + r_ * R * np.cos(a_)])
        dy = np.concatenate([oy, cy + r_ * R * np.sin(a_)])
        lv = rnd.uniform(nd)
        dcol = gold_ramp(0.55 + 0.45 * lv)
        dsz = (0.0004 + 0.0010 * rnd.uniform(nd) ** 2.0) * S
        dam = 0.25 + 0.75 * rnd.uniform(nd) ** 2.2
        far = rho_to_discs(dx, dy, discs) > avoid
        layer.splat(dx[far], dy[far], dsz[far], dcol[far], dam[far] * amp, min_sigma=0.5)


def limb_brightness(d):
    """The mean display value (0..1) of the graded iris's limb band (0.90 to 0.98 R)."""
    g = d.g
    t = g.shape[0]
    ax = (np.arange(t, dtype=np.float32) + 0.5) - t / 2.0
    rho = np.hypot(ax[None, :], ax[:, None]) / np.float32(d.R)
    m = (rho > 0.90) & (rho < 0.98)
    return float(g[m].mean()) / 255.0


def aura(cv, d, rgb, amp, e_fold, reach=2.6, power=1.0, limb_share=0.45, cap=0.20):
    """A soft glow of one colour round a disc, added to the canvas: amp x exp(-(rho - 1) / e_fold) from the limb to `reach` R, zero inside the limb (the
    iris is pasted over it anyway). The personal colour of a person in the picture: an aura, never a recolouring of the iris. limb_share caps the glow at that
    share of the limb's own brightness (a dark iris gets a dim aura, so that its edge still reads against it: T10, T11) and `cap` (a pale iris never gets a white
    ring); None leaves amp as it is."""
    H, W = cv.shape[:2]
    if limb_share is not None:
        amp = min(float(amp), float(limb_share) * limb_brightness(d))
    if cap is not None:
        amp = min(float(amp), float(cap))
    x0, y0_ = max(0, int(d.cx - reach * d.R)), max(0, int(d.cy - reach * d.R))
    x1, y1_ = min(W, int(d.cx + reach * d.R) + 2), min(H, int(d.cy + reach * d.R) + 2)
    for r0 in range(y0_, y1_, 256):
        r1 = min(y1_, r0 + 256)
        rho, _ = C.polar(W, H, d.cx, d.cy, d.R, 1.0, (x0, r0, x1, r1))
        x = np.maximum(rho - 1.0, 0.0)
        f = np.exp(-(x / e_fold) ** power) * smooth((rho - 0.97) / 0.06) * (1.0 - smooth((rho - reach) / 0.35))
        cv[r0:r1, x0:x1] += (f * F32(amp))[..., None].astype(np.float32) * np.asarray(rgb, np.float32)


def eclipse_gap(cv, d, width=0.034):
    """The black eclipse gap of Celestial Gold: the canvas multiplied by 0.05 from the limb to 1 + width R with soft edges (drawn before the iris paste)."""
    H, W = cv.shape[:2]
    x0, y0 = max(0, int(d.cx - 1.12 * d.R)), max(0, int(d.cy - 1.12 * d.R))
    x1, y1 = min(W, int(d.cx + 1.12 * d.R) + 2), min(H, int(d.cy + 1.12 * d.R) + 2)
    rho, _ = C.polar(W, H, d.cx, d.cy, d.R, 1.0, (x0, y0, x1, y1))
    gap = 1.0 - 0.95 * (smooth((rho - 0.985) / 0.02) * (1.0 - smooth((rho - (1.0 + width - 0.01)) / 0.02)))
    cv[y0:y1, x0:x1] *= gap[..., None].astype(np.float32)


def sparkle(cv, x, y, arm_px, rgb, amp, width_px, angle=0.0, core=0.35):
    """One 4-point star added into the canvas (core.sparkles on a small window, so a 4096 px canvas costs a few ms)."""
    H, W = cv.shape[:2]
    gw = int(arm_px + 4 * max(width_px, 0.6)) + 2
    wx0, wy0 = max(0, int(x) - gw), max(0, int(y) - gw)
    wx1, wy1 = min(W, int(x) + gw + 1), min(H, int(y) + gw + 1)
    if wx1 <= wx0 or wy1 <= wy0:
        return
    lay = np.zeros((wy1 - wy0, wx1 - wx0, 3), np.float32)
    C.sparkles(lay, [x - wx0], [y - wy0], arm_px, np.asarray(rgb, np.float32), amp, width=width_px, angle=angle, core=core)
    C.screen(cv[wy0:wy1, wx0:wx1], lay)
