# -*- coding: utf-8 -*-
"""fx.collision_comp: the overlap compositor (BRIEF_V3_FINAL 1.1, 1.3, 1.7.3), ported from the scratch prototype. numpy only.

What it does
- iris_tile(): a graded disc as a float tile with the owner's feather F3 (alpha 1 up to 0.985 R, smoothstep to 0 at 1.015 R;
  colour beyond 0.985 R is the rim colour carried outward along the radius). Inside r <= 0.985 R the tile IS the graded pixels
  (byte for byte).
- Compositor: merges the tiles in the scene's order. Iris j over the accumulated layer X with a per-pixel weight w
  ("X in front"):  out = X (1 - (1 - w) a_j) + B_j (1 - w a_X),  a = a_X + a_j - a_X a_j.  w = 1 is plain "X over B", w = 0 is
  "B over X". A per-pixel OCCUPANT map (which iris is front-most at a pixel) picks the rule that applies where three irises
  meet, so the small triple regions of a brick are exact, never a 50/50 mix. Weave rule: w = smoothstep(-bw, +bw, t) with t the
  signed distance from the axis of the pair (+v side = A in front): the only mixed pixels are the seam band E1 (a convex mix
  of two real iris pixels, total width 2 bw = 0.08 R).
- The thin dark edge (1.3.4): inside the FRONT iris (zone B multiply), Zone C on the BACK iris (D8, soft shadow, alpha <= 0.45
  in the brief preset), fading out toward the axis; crumble variant for kiss / trio / family (strength x0.35, 30 % holes, zone
  C x0.6); edge_mode 'hairline' for dark eyes (1.3.5).
- pure_masks(): the analytic set M_k of pixels that must equal the graded iris (test T1); zone_c_masks(): the strips.
Work happens in windows around the lenses (never on whole tiles), in row bands, so a 4096 render stays inside the memory budget.
"""
from __future__ import annotations

# PORT of work package WP7A (step A): collision_comp.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (imports, a bounded cache); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math
from dataclasses import dataclass, field
import numpy as np

from .. import core as C
from . import seam_plan as SP

F3_IN, F3_OUT = 0.985, 1.015          # feather (share of R)
FADE_T0, FADE_T1 = 0.02, 0.14         # the edge fades out toward the axis (share of R)
WIN_PAD = 0.075                       # window around a lens: strips reach 0.05 R past a limb
BAND_ROWS = 320


def smooth(x0, x1, x):
    t = np.clip((x - x0) / (x1 - x0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def blend_w(tp, hw, beta=0.0):
    """Weight of iris A in the seam band: smoothstep over [-hw, hw] (compact support, exactly 0 and 1 outside), a share `beta` of it replaced by the
    linear ramp (a wider 10-90 % transition for the same mixed area; at beta 0.3 the slope at the band edge is 0.3 of the ramp slope: no visible kink)."""
    x = np.clip((tp + hw) / (2.0 * hw), 0.0, 1.0)
    return (1.0 - beta) * x * x * (3.0 - 2.0 * x) + beta * x


# ----------------------------------------------------------------------------- edge presets
PRESETS = {
    # brief 1.3.4 / 1.1: inside multiply 0.45 at the limb (zone B), Zone C alpha 0.45 decaying 0.015 R, cut at 0.05 R.
    "brief": dict(a_in=0.55, r0=0.965, zc_a=0.45, zc_l=0.015, zc_cut=0.05, zc_plateau=0.0),
    # calibrated on the owner's H10 (measured along the front limb): black valley 0.02-0.03 R wide, back iris recovers by 0.05 R.
    # Stronger than the brief's caps (needs the owner's word: D8 strength).
    "ref": dict(a_in=0.78, r0=0.955, zc_a=0.96, zc_l=0.0, zc_cut=0.050, zc_plateau=0.014),
}


@dataclass
class Cfg:
    """Switches of the compositor. band: seam half width in R (D13: 0.04 default; 0.01 = 'hard seam, 0.02 R feather').
    zone_c: D8 on/off. preset: 'brief' | 'ref'. hair_alpha: hairline mode alpha. hole_share: crumble holes (30 %)."""
    band: float = 0.04
    zone_c: bool = True
    preset: str = "brief"
    edge_scale: float = 1.0
    crumble_in: float = 0.35
    crumble_zc: float = 0.60
    hole_share: float = 0.30
    hair_alpha: float = 0.70          # round 2c (AD D): hairline mode of dark-eye pairs lighter and a little wider, so the S of a brown pair reads
    hair_w: float = 0.012
    seed: int = 1
    # round 2c seam (D13): 'band' = the brief's straight band (half width `band`), 'hard' = 0.02 R feather, 'soft_s' = the AD's wandering S seam
    seam: str = "plan"
    seam_hw: float = 0.060            # soft_s half width of the blend (R); the noise shift below adds up to seam_fine * hw on either side
    seam_wave: float = 0.108          # a slow S wave along the lens (wavelength 0.62 R, seeded phase) under the noise: the seam is never straight
    seam_amp: float = 0.07           # wander amplitude (R), wavelength seam_lam (R): the seam follows the fibres, never a ruler
    seam_lam: float = 0.35
    seam_bend: float = 0.0           # share of the lens half height the seam bends toward the limbs at both ends (the S flows into the limbs)
    seam_fine: float = 0.25
    seam_fibre: tuple = (0.20, 0.030)   # noise scales (R) of the fibre-scale shift: long along the axis (the fibres run along it near the axis), thin across
    erode: bool = True                # crumble contacts: the front iris's limb over the back iris is eroded (AD E): amplitude 0.012-0.030 R, wavelength 0.02-0.06 R, 30 % holes
    erode_amp: tuple = (0.012, 0.030)
    taper_sq: bool = True             # limb edge strength smoothstep(0, 0.16 R, |t|)^2 (round 2c) instead of smoothstep(0.02, 0.14)
    # DG1 rung 1: seam='plan' = the smooth contrast-adaptive seam of seam_plan.py (one SeamPlan per weave rule in `plans`, {rule index: plan})
    plans: object = None
    blend: str = "oklab"              # 'oklab' = the crossfade mixes the two irises' pixels in OKLab, 'srgb' = the round 2c mix of the encoded values
    pad: float = 1.01                 # E1 mask half width over the blend half width (the blend is exactly 0 or 1 outside |tp| >= hw)
    beta: float = 0.70                # share of the linear ramp in the blend profile (blend_w); DG1 judge: 0.70 with the support budget of seam_plan (SUPPORT_BUDGET)
    dp_sigma: float = 0.025           # blend 'oklab_dp': scale (R) that splits colour and tone from detail
    dp_rho: float = 0.40              # blend 'oklab_dp': the detail layer switches over w = 0.5 +- dp_rho

    @property
    def p(self):
        return PRESETS[self.preset]


def zone_c_profile(u, cfg):
    """Shadow strength (0..1) on the back iris at distance u >= -0.015 (R) outside the front limb."""
    p = cfg.p
    u = np.maximum(u, 0.0)
    if p["zc_plateau"] > 0:
        s = p["zc_a"] * (1.0 - smooth(p["zc_plateau"], p["zc_cut"], u))
    else:
        cut = p["zc_cut"]
        e0 = math.exp(-cut / p["zc_l"])
        s = p["zc_a"] * np.maximum(np.exp(-u / p["zc_l"]) - e0, 0.0) / (1.0 - e0)
    return s


# ----------------------------------------------------------------------------- hash noise (resolution independent)
def _h2(ix, iy, seed):
    h = ix.astype(np.int64) * 374761393 + iy.astype(np.int64) * 668265263 + (int(seed) & 0xFFFFFFFF) * 2246822519
    h = (h & 0xFFFFFFFF).astype(np.uint32)
    h = (h ^ (h >> np.uint32(13))) * np.uint32(1274126177)
    h = h ^ (h >> np.uint32(16))
    return (h.astype(np.float32)) * np.float32(1.0 / 4294967296.0)


def value_noise(x, y, seed):
    """Smooth 2-D value noise 0..1 at lattice coordinates (x, y) (floats, unit cell)."""
    ix = np.floor(x)
    iy = np.floor(y)
    fx = (x - ix).astype(np.float32)
    fy = (y - iy).astype(np.float32)
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = _h2(ix, iy, seed)
    b = _h2(ix + 1, iy, seed)
    c = _h2(ix, iy + 1, seed)
    d = _h2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def _noise1(x, seed):
    """Smooth 1-D value noise 0..1 at lattice coordinate x."""
    return value_noise(x, np.zeros_like(x) + 0.37, seed)


def seam_field(cfg, rule, ta, tb, xs, ys, ri, fine=True):
    """Signed position of a pixel relative to the seam of a WEAVE lens and the half width of the blend: returns (tp, hw) with
    tp = t - C(s) (+ the fibre-scale shift when fine), t the distance from the axis of the pair (R_a units, +v side = A in front), C(s) the seam line,
    s the position along the axis from the lens centre.  w(A in front) = smoothstep(-hw, hw, tp).
    'band' / 'hard': C = 0, hw = cfg.band (the brief's straight seam). 'soft_s': C = low-frequency wander (amp, lam) + an odd S bend that carries the seam
    into the two limbs, hw modulated 0.85-1.15, plus a fibre-scale shift of the threshold (anisotropic: long along the axis)."""
    Ra = ta.R
    vx, vy = rule.uy, -rule.ux
    t = ((xs - ta.cx) * vx + (ys - ta.cy) * vy) / np.float32(Ra)
    if cfg.seam == "plan":
        plan = (cfg.plans or {}).get(ri)
        if plan is None:                                           # no plan was made for this rule: the straight band of the brief with the references' softness
            plan = cfg.plans_fallback = getattr(cfg, "plans_fallback", None) or SP.straight_plan(rule.d / ta.R, hw=0.06)
        mx, my = 0.5 * (ta.cx + tb.cx), 0.5 * (ta.cy + tb.cy)
        s = ((xs - mx) * rule.ux + (ys - my) * rule.uy) / np.float32(Ra)
        Cc, hw = plan.eval(s)
        return t - Cc, hw
    if cfg.seam != "soft_s":
        return t, np.float32(cfg.band)
    mx, my = 0.5 * (ta.cx + tb.cx), 0.5 * (ta.cy + tb.cy)
    s = ((xs - mx) * rule.ux + (ys - my) * rule.uy) / np.float32(Ra)
    dd = rule.d / Ra
    L = max(1.0 - dd / 2.0 * (Ra + tb.R) / Ra * 0.0 - dd / 2.0, 1e-3)              # lens half width (R, equal irises: 1 - d / 2)
    sd = cfg.seed * 131 + ri * 17
    wander = cfg.seam_amp * (0.80 * (2.0 * _noise1(s / cfg.seam_lam + 3.7, sd) - 1.0) + 0.20 * (2.0 * value_noise(s / (0.70 * cfg.seam_lam) + 8.3, t / (0.45 * cfg.seam_lam) + 1.3, sd + 3) - 1.0))
    # the S bend: odd in s, zero in the middle third, carries the seam to the lens boundary at both ends
    ttop = np.sqrt(np.maximum(1.0 - (np.abs(s) + dd / 2.0) ** 2, 0.0))
    sg = np.clip(s / L, -1.0, 1.0)
    g = np.sign(sg) * smooth(0.30, 1.0, np.abs(sg)) ** 1.25
    ph = 6.2831853 * ((cfg.seed * 0.6180339 + ri * 0.37) % 1.0)
    ph2 = 6.2831853 * ((cfg.seed * 0.7548777 + ri * 0.53) % 1.0)
    jit = 0.018 * (2.0 * _noise1(s / 0.12 + 5.1, sd + 17) - 1.0)           # fibre-scale irregularity: no ruler-straight (even tilted) run
    # the seam leaves the pupil of one eye and arrives at the pupil of the other at about the height of the pupils (the owner's H10 / H11): the wander is
    # full in the middle of the lens and relaxes to 40 % toward both ends, where the limbs meet it
    taper = 1.0 - 0.60 * smooth(0.40, 1.0, np.abs(sg))
    C = taper * (wander + jit + cfg.seam_wave * np.sin(3.3 * sg + ph) + 0.25 * cfg.seam_wave * np.sin(6.0 * sg + ph2)) + 0.026 * (0.5 + 0.5 * taper) * np.sin(15.0 * sg + ph + 2.1) + cfg.seam_bend * ttop * g
    hw = cfg.seam_hw * (0.85 + 0.30 * _noise1(s / 0.55 + 9.1, sd + 5))
    tp = t - C
    if fine:
        nf = (2.0 * value_noise(s / cfg.seam_fibre[0] + 21.0, t / cfg.seam_fibre[1] + 5.0, sd + 11) - 1.0) * 0.75 + (2.0 * value_noise(s / 0.05 + 7.0, t / 0.012 + 1.0, sd + 23) - 1.0) * 0.25
        tp = tp + cfg.seam_fine * hw * nf
    return tp, hw


def ragged_field(xr, yr, seed, share=0.30):
    """1 where the edge is broken (holes 0.006-0.02 R, about `share` of the arc), smooth 0..1 elsewhere. xr, yr: pixel coordinates in
    units of R."""
    n = 0.62 * value_noise(xr / 0.020, yr / 0.020, seed) + 0.38 * value_noise(xr / 0.008 + 17.0, yr / 0.008 + 31.0, seed + 7)
    thr = _RAG_THR.get(round(share, 3))
    if thr is None:
        g = np.arange(200000, dtype=np.float32)
        rr = 0.62 * value_noise(g * 0.0137, g * 0.0091 + 3, 99) + 0.38 * value_noise(g * 0.0311 + 17.0, g * 0.0219 + 31.0, 106)
        thr = float(np.quantile(rr, 1.0 - share))
        _RAG_THR.put(round(share, 3), thr)
    return smooth(thr - 0.03, thr + 0.03, n)


_RAG_THR = C.BoundedCache(8)


class Tile:
    __slots__ = ("k", "rgb", "a", "x0", "y0", "cx", "cy", "R", "T", "rim")


def iris_tile(disc, k=0):
    """Float tile of a placed fx.core.Disc: rgb (T, T, 3) float32 0..255 (NOT premultiplied), a (T, T) float32 (F3), the tile's
    integer top-left (x0, y0) on the canvas, and the exact (cx, cy, R) of the disc."""
    g = disc.g
    t = g.shape[0]
    R = t / 2.0
    pad = int(math.ceil(0.04 * R)) + 1
    T = t + 2 * pad
    rgb = np.zeros((T, T, 3), np.float32)
    rgb[pad:pad + t, pad:pad + t] = g
    ax = (np.arange(T, dtype=np.float32) + 0.5 - T / 2.0)
    rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / np.float32(R)
    ring = (rr > F3_IN) & (rr < 1.06)
    if ring.any():
        ys, xs = np.nonzero(ring)
        r = rr[ys, xs]
        k_ = np.float32(F3_IN) / r
        sx = np.clip((xs + 0.5 - T / 2.0) * k_ + T / 2.0 - 0.5 - pad, 0, t - 1.001)
        sy = np.clip((ys + 0.5 - T / 2.0) * k_ + T / 2.0 - 0.5 - pad, 0, t - 1.001)
        x0 = np.floor(sx).astype(np.int64)
        y0 = np.floor(sy).astype(np.int64)
        fx = (sx - x0)[:, None]
        fy = (sy - y0)[:, None]
        gg = g.astype(np.float32)
        col = (gg[y0, x0] * (1 - fx) * (1 - fy) + gg[y0, x0 + 1] * fx * (1 - fy) + gg[y0 + 1, x0] * (1 - fx) * fy
               + gg[y0 + 1, x0 + 1] * fx * fy)
        rgb[ys, xs] = col
    a = 1.0 - smooth(F3_IN, F3_OUT, rr)
    tl = Tile()
    tl.k, tl.rgb, tl.a, tl.T = k, rgb, a.astype(np.float32), T
    tl.x0, tl.y0 = disc.x0 - pad, disc.y0 - pad
    tl.cx, tl.cy, tl.R = disc.cx, disc.cy, disc.R
    return tl


def _tile_view(tile, x0, y0, x1, y1):
    """(rgb, a) of a tile on the canvas window [x0, x1) x [y0, y1) (zero outside the tile)."""
    h, w = y1 - y0, x1 - x0
    rgb = np.zeros((h, w, 3), np.float32)
    a = np.zeros((h, w), np.float32)
    xa, ya = max(x0, tile.x0), max(y0, tile.y0)
    xb, yb = min(x1, tile.x0 + tile.T), min(y1, tile.y0 + tile.T)
    if xa < xb and ya < yb:
        rgb[ya - y0:yb - y0, xa - x0:xb - x0] = tile.rgb[ya - tile.y0:yb - tile.y0, xa - tile.x0:xb - tile.x0]
        a[ya - y0:yb - y0, xa - x0:xb - x0] = tile.a[ya - tile.y0:yb - tile.y0, xa - tile.x0:xb - tile.x0]
    return rgb, a


class Compositor:
    """scene: collision_layouts.Scene with every rule's mode decided ('weave', 'front_a', 'front_b'), tiles: list of Tile.
    edge_modes: {rule_index: 'dark' | 'hairline'}; hair_cols: {iris: (3,) colour 0..255} for hairline mode; pupils: {iris: callable(xs, ys, dil)
    -> bool array of the dilated pupil on canvas pixels (xs row vector, ys column vector)}."""

    def __init__(self, scene, tiles, cfg=None, edge_modes=None, hair_cols=None, pupils=None):
        self.sc = scene
        self.tiles = tiles
        self.cfg = cfg or Cfg()
        self.edge_modes = edge_modes or {}
        self.hair_cols = hair_cols or {}
        self.pupils = pupils or {}
        x0 = min(t.x0 for t in tiles)
        y0 = min(t.y0 for t in tiles)
        x1 = max(t.x0 + t.T for t in tiles)
        y1 = max(t.y0 + t.T for t in tiles)
        self.box = (x0, y0, x1, y1)
        self.P = np.zeros((y1 - y0, x1 - x0, 3), np.float32)       # premultiplied colour 0..255
        self.A = np.zeros((y1 - y0, x1 - x0), np.float32)
        self.occ = np.full((y1 - y0, x1 - x0), -1, np.int8)         # front-most iris per pixel
        self.done = False

    # -- geometry of one rule on a window ---------------------------------------------------------
    def _terms(self, rule, xs, ys):
        ta, tb = self.tiles[rule.a], self.tiles[rule.b]
        ra = np.sqrt((xs - ta.cx) ** 2 + (ys - ta.cy) ** 2) / np.float32(ta.R)
        rb = np.sqrt((xs - tb.cx) ** 2 + (ys - tb.cy) ** 2) / np.float32(tb.R)
        vx, vy = rule.uy, -rule.ux
        t = ((xs - ta.cx) * vx + (ys - ta.cy) * vy) / np.float32(ta.R)
        return ta, tb, ra, rb, t

    def _window(self, rule):
        ta, tb = self.tiles[rule.a], self.tiles[rule.b]
        ra_, rb_ = ta.R * (1 + WIN_PAD), tb.R * (1 + WIN_PAD)
        # bbox of disc a (dilated) intersect disc b (dilated)
        pts = None
        from .scenes import circle_intersections
        ci, cj = (ta.cx, ta.cy), (tb.cx, tb.cy)
        d = math.hypot(cj[0] - ci[0], cj[1] - ci[1])
        if d >= ra_ + rb_:
            return None
        # conservative: box of the intersection of the two bounding squares
        x0 = max(ci[0] - ra_, cj[0] - rb_)
        x1 = min(ci[0] + ra_, cj[0] + rb_)
        y0 = max(ci[1] - ra_, cj[1] - rb_)
        y1 = min(ci[1] + ra_, cj[1] + rb_)
        # tighten along the axis: the lens sits between the limbs
        return int(math.floor(x0)), int(math.floor(y0)), int(math.ceil(x1)), int(math.ceil(y1))

    def _front_w(self, rule, k, t):
        """Weight that iris k (a member of rule) is in FRONT at signed distance t (R_a units); for a weave t is (tp, hw) of seam_field."""
        if rule.mode == "weave":
            tp, hw = t
            wa = blend_w(tp, hw, self.cfg.beta) if self.cfg.seam == "plan" else smooth(-hw, hw, tp)
            return wa if k == rule.a else 1.0 - wa
        if rule.mode == "front_a":
            return np.full_like(t, 1.0 if k == rule.a else 0.0)
        return np.full_like(t, 1.0 if k == rule.b else 0.0)

    def _fades(self, rule, t, ta, tb, xs, ys, ri):
        cfg = self.cfg
        if rule.mode == "weave":
            tp0 = t[0]
            if cfg.taper_sq and cfg.seam in ("soft_s", "plan"):
                ga = smooth(0.0, 0.16, tp0) ** 2
                gb = smooth(0.0, 0.16, -tp0) ** 2
            else:
                ga = smooth(FADE_T0, FADE_T1, tp0)
                gb = smooth(FADE_T0, FADE_T1, -tp0)
            zca, zcb = ga, gb
            k_in = 1.0
            k_zc = 1.0
        else:
            d = math.hypot(tb.cx - ta.cx, tb.cy - ta.cy) / ta.R
            h = math.sqrt(max(1.0 - (d / 2.0) ** 2, 0.0))
            taper = 1.0 - 0.55 * smooth(h - 0.12, h, np.abs(t))
            one = taper if rule.mode == "front_a" else 0.0 * taper
            other = taper if rule.mode == "front_b" else 0.0 * taper
            ga, gb = one, other
            k_in, k_zc = (cfg.crumble_in if rule.crumble else 1.0), (cfg.crumble_zc if rule.crumble else 1.0)
            if rule.crumble:
                xr = (xs - ta.cx) / ta.R
                yr = (ys - ta.cy) / ta.R
                hole = 1.0 - ragged_field(xr, yr, cfg.seed * 31 + ri, cfg.hole_share)
                ga = ga * hole
                gb = gb * hole
            zca, zcb = one, other
        return ga, gb, zca, zcb, k_in, k_zc

    # -- multipliers (colour multipliers for the pixels of A and B, hairline coverage) ------------
    def _edge(self, rule, ri, xs, ys):
        ta, tb, ra, rb, t = self._terms(rule, xs, ys)
        cfg = self.cfg
        p = cfg.p
        if rule.mode == "weave":
            tp, hw = seam_field(cfg, rule, ta, tb, xs, ys, ri, fine=True)
            tp0, _ = seam_field(cfg, rule, ta, tb, xs, ys, ri, fine=False)
            t = (tp, hw, tp0)
            ga, gb, zca, zcb, k_in, k_zc = self._fades(rule, (tp0, hw), ta, tb, xs, ys, ri)
            t = (tp, hw)
        else:
            ga, gb, zca, zcb, k_in, k_zc = self._fades(rule, t, ta, tb, xs, ys, ri)
        s = cfg.edge_scale
        ins_b = 1.0 - smooth(0.96, 1.0, rb)
        ins_a = 1.0 - smooth(0.96, 1.0, ra)
        mode = self.edge_modes.get(ri, "dark")
        ua = ra - 1.0
        ub = rb - 1.0
        if mode == "dark":
            in_a = 1.0 - p["a_in"] * s * k_in * smooth(p["r0"], 1.004, ra) * ga * ins_b
            in_b = 1.0 - p["a_in"] * s * k_in * smooth(p["r0"], 1.004, rb) * gb * ins_a
            hair_a = hair_b = None
            kz = 1.0
        else:
            in_a = np.ones_like(ra)
            in_b = np.ones_like(rb)
            kz = 0.5
            wl = cfg.hair_w / 2.0
            hair_a = np.exp(-0.5 * ((ra - 1.0) / wl) ** 2) * ga * ins_b
            hair_b = np.exp(-0.5 * ((rb - 1.0) / wl) ** 2) * gb * ins_a
        if cfg.zone_c:
            cut = p["zc_cut"] + 0.004
            sh_b = zone_c_profile(ua, cfg) * ((ua > -F3_IN + 0.0) & (ua <= cut)) * zca * kz * k_zc * s
            sh_a = zone_c_profile(ub, cfg) * ((ub > -F3_IN + 0.0) & (ub <= cut)) * zcb * kz * k_zc * s
            # strip only on the back iris' own pixels outside the front limb's feather core; never inside the pupil dilated 0.01 R
            for kk, sh in ((rule.b, sh_b), (rule.a, sh_a)):
                pf = self.pupils.get(kk)
                if pf is not None:
                    sh *= (~pf(xs, ys, 0.01)).astype(np.float32)
            mul_on_b = 1.0 - np.minimum(sh_b, 0.98)
            mul_on_a = 1.0 - np.minimum(sh_a, 0.98)
        else:
            mul_on_b = mul_on_a = 1.0
        return in_a * mul_on_a, in_b * mul_on_b, hair_a, hair_b, ta, tb, ra, rb, t

    # -- the merge --------------------------------------------------------------------------------
    def compose(self):
        sc = self.sc
        bx0, by0, _, _ = self.box
        for j, partners in sc.order:
            tj = self.tiles[j]
            roi = (tj.x0, tj.y0, tj.x0 + tj.T, tj.y0 + tj.T)
            sl = (slice(roi[1] - by0, roi[3] - by0), slice(roi[0] - bx0, roi[2] - bx0))
            Xp0 = self.P[sl]
            AX0 = self.A[sl]
            Bp0 = tj.rgb * tj.a[..., None]
            aB0 = tj.a
            occ0 = self.occ[sl]
            # the plain merge (X over B) everywhere; the lens windows are recomputed below with ALL partners' rules at once
            newP = Xp0 + Bp0 * (1.0 - AX0)[..., None]
            newA = AX0 + aB0 - AX0 * aB0
            newocc = np.where((aB0 > 0.01) & (occ0 < 0), np.int8(j), occ0).astype(np.int8)
            wins = []
            for (k, ri) in partners:
                win = self._window(sc.rules[ri])
                if win is not None:
                    wins.append(win)
            if wins:
                wx0 = max(min(w[0] for w in wins), roi[0])
                wy0 = max(min(w[1] for w in wins), roi[1])
                wx1 = min(max(w[2] for w in wins), roi[2])
                wy1 = min(max(w[3] for w in wins), roi[3])
                if wx0 < wx1 and wy0 < wy1:
                    step_rows = (wy1 - wy0) if self.cfg.blend == "oklab_dp" else BAND_ROWS          # the detail split needs the whole band in one window
                    for r0 in range(wy0, wy1, step_rows):
                        r1 = min(wy1, r0 + step_rows)
                        self._merge_window(j, tj, partners, (wx0, r0, wx1, r1), Xp0, AX0, occ0, newP, newA, newocc, roi)
            self.P[sl] = newP
            self.A[sl] = newA
            self.occ[sl] = newocc
        self.done = True
        return self.P, self.A

    def _erosion(self, ri, xs, ys, rf, rbk, ftile):
        """Erosion field (0 = keep, 1 = gone) of the FRONT iris's limb where it lies over the back iris (crumble contacts, AD review E): the edge recedes by
        0.012-0.030 R through value noise of wavelength 0.02-0.06 R, and about 30 % of the arc is broken deeper (holes). Only pixels inside the back
        iris's disc; the back iris pixels that show through were hidden (excluded from the hash test) - never a visible zone A pixel."""
        cfg = self.cfg
        xr = (xs - ftile.cx) / np.float32(ftile.R)
        yr = (ys - ftile.cy) / np.float32(ftile.R)
        sd = cfg.seed * 37 + ri * 11
        n1 = value_noise(xr / 0.055, yr / 0.055, sd)
        n2 = value_noise(xr / 0.020 + 13.0, yr / 0.020 + 7.0, sd + 9)
        hole = 1.0 - ragged_field(xr, yr, sd + 3, cfg.hole_share)
        a0, a1 = cfg.erode_amp
        amp = a0 + (a1 - a0) * n1
        depth = amp * (0.30 * n2 + 0.70 * hole) + 0.004 * n2
        er = smooth(1.0 - depth - 0.0025, 1.0 - depth + 0.0025, rf)
        inside_back = 1.0 - smooth(0.985, 1.0, rbk)
        return (er * inside_back).astype(np.float32)

    def _merge_window(self, j, tj, partners, win, Xp0, AX0, occ0, newP, newA, newocc, roi):
        wx0, wy0, wx1, wy1 = win
        ys_ = slice(wy0 - roi[1], wy1 - roi[1])
        xs_ = slice(wx0 - roi[0], wx1 - roi[0])
        xs = (np.arange(wx0, wx1, dtype=np.float32) + np.float32(0.5))[None, :]
        ys = (np.arange(wy0, wy1, dtype=np.float32) + np.float32(0.5))[:, None]
        Xp = Xp0[ys_, xs_]
        AX = AX0[ys_, xs_]
        occ = occ0[ys_, xs_]
        Bv = _tile_view(tj, wx0, wy0, wx1, wy1)
        Bp_rgb, aB = Bv[0] * Bv[1][..., None], Bv[1]
        # DG1 review fix (brief 1.1 rule 6, "pupils are never covered"): inside the pupil of an iris dilated by 0.01 R no other iris contributes. The overlap solver keeps the
        # partner's limb 0.015 R from the pupil rim and the partner's feather F3 reaches 0.015 R past its limb, so a pupil dilated by 0.01 R can touch the feather ring (alpha up to
        # 0.26): 18 of the 441 pairs of the corpus changed 1 to 12 pupil pixels by 2/255 (round 2c: 6/255). The feather ring is hidden over the dilated pupil, nothing else changes.
        protj = None
        pj_ = self.pupils.get(j)
        if pj_ is not None:
            protj = pj_(xs, ys, 0.01)
            if protj.any():
                keep = (~protj).astype(np.float32)
                Xp = Xp * keep[..., None]
                AX = AX * keep
            else:
                protj = None
        for (k_, _ri) in partners:
            pk_ = self.pupils.get(k_)
            if pk_ is not None:
                protk = pk_(xs, ys, 0.01)
                if protk.any():
                    keep = (~protk).astype(np.float32)
                    Bp_rgb = Bp_rgb * keep[..., None]
                    aB = aB * keep
        mult_x = None
        mult_b = None
        front_sum = np.zeros(AX.shape, np.float32)          # weight that j is in front of the occupant, summed over the partners
        hairs = []
        erB = erX = None
        cfg_erode = self.cfg.erode
        for (k, ri) in partners:
            rule = self.sc.rules[ri]
            mx_a, mx_b, ha, hb, ta, tb, ra, rb, t = self._edge(rule, ri, xs, ys)
            if k == rule.a:
                mxk, mbj, hk, hj, rk = mx_a, mx_b, ha, hb, ra
            else:
                mxk, mbj, hk, hj, rk = mx_b, mx_a, hb, ha, rb
            wj = self._front_w(rule, j, t)
            present = ((occ == k) | ((occ < 0) & (AX > 0.0) & (rk < 1.03))).astype(np.float32)
            if rule.crumble and cfg_erode and rule.mode in ("front_a", "front_b"):
                f_is_a = rule.mode == "front_a"
                er = self._erosion(ri, xs, ys, ra if f_is_a else rb, rb if f_is_a else ra, ta if f_is_a else tb)
                if (rule.a if f_is_a else rule.b) == j:
                    erB = (1.0 - er) if erB is None else erB * (1.0 - er)
                else:
                    fx_ = 1.0 - er * present
                    erX = fx_ if erX is None else erX * fx_
            front_sum += present * wj
            one = np.float32(1.0)
            mx_eff = one - present * (one - mxk)          # X's edge terms of this rule only where X's occupant is the partner iris k
            mult_x = mx_eff if mult_x is None else mult_x * mx_eff
            mult_b = mbj if mult_b is None else mult_b * mbj
            if hk is not None:
                hairs.append((k, hk, j, hj))
        if erB is not None:
            Bp_rgb = Bp_rgb * erB[..., None]
            aB = aB * erB
        if erX is not None:
            Xp = Xp * erX[..., None]
            AX = AX * erX
        wX = np.clip(1.0 - front_sum, 0.0, 1.0)
        Xm = Xp * mult_x[..., None]
        Bm = Bp_rgb * mult_b[..., None]
        wx = 1.0 - (1.0 - wX) * aB
        wb = 1.0 - wX * AX
        out = Xm * wx[..., None] + Bm * wb[..., None]
        if self.cfg.blend in ("oklab", "oklab_dp"):
            self._blend_band(out, Xm, Bm, wX, AX, aB, tj)
        aout = AX + aB - AX * aB
        front_j = ((1.0 - wX) > 0.5) & (aB > 0.5) & (AX > 0.01)
        o = newocc[ys_, xs_]
        o_new = np.where(front_j, np.int8(j), o)
        if protj is not None:
            o_new = np.where(protj & (aB > 0.5), np.int8(j), o_new)          # the dilated pupil of j shows j (DG1 review fix above)
        if erX is not None:
            o_new = np.where((erX < 0.5) & (aB > 0.5), np.int8(j), o_new)          # pixels of the eroded front iris now show the iris behind it
        for (k, hk, jj, hj) in hairs:                      # a hairline is drawn only where its iris is the one shown
            out = self._hairline(out, aout, k, hk * (o_new == k), jj, None if hj is None else hj * (o_new == jj))
        newP[ys_, xs_] = out
        newA[ys_, xs_] = aout
        newocc[ys_, xs_] = o_new

    def _blend_band(self, out, Xm, Bm, wX, AX, aB, tj):
        """The crossfade of a weave band, in place on `out`. 'oklab': the two irises' pixels mixed in OKLab with weight wX (perceptually even, no muddy mid
        tones). 'oklab_dp' (detail preserving): the low frequencies (colour and tone, sigma `dp_sigma` R) are mixed with the wide weight wX, the detail layer
        (fibres) with a steeper weight, so the band keeps its fibres instead of a milky double exposure. Only where both irises are opaque."""
        cfg = self.cfg
        both = (AX > 0.999) & (aB > 0.999)
        bandm = (wX > 0.0) & (wX < 1.0) & both
        if not bandm.any():
            return
        if cfg.blend == "oklab":
            w_ = wX[bandm][:, None]
            lab = SP.srgb_to_oklab(Xm[bandm]) * w_ + SP.srgb_to_oklab(Bm[bandm]) * (1.0 - w_)
            out[bandm] = SP.oklab_to_srgb255(lab)
            return
        sig = cfg.dp_sigma * tj.R
        halo = int(math.ceil(3.0 * sig)) + 2
        yy, xx = np.nonzero(bandm)
        h, w = bandm.shape
        ya, yb = max(0, yy.min() - halo), min(h, yy.max() + 1 + halo)
        xa, xb = max(0, xx.min() - halo), min(w, xx.max() + 1 + halo)
        sub = (slice(ya, yb), slice(xa, xb))
        m = both[sub].astype(np.float32)
        labX = SP.srgb_to_oklab(Xm[sub])
        labB = SP.srgb_to_oklab(Bm[sub])

        def lf(lab):
            num = SP.blur2(lab * m[..., None], sig)
            den = np.maximum(SP.blur2(m, sig), 1e-4)
            return num / den[..., None]
        lfX, lfB = lf(labX), lf(labB)
        wl = wX[sub][..., None]
        rho = cfg.dp_rho
        wh = SP.smooth(0.5 - rho, 0.5 + rho, wX[sub])[..., None]
        lab = (wl * lfX + (1.0 - wl) * lfB) + (wh * (labX - lfX) + (1.0 - wh) * (labB - lfB))
        bm = bandm[sub]
        res = out[sub]
        res[bm] = SP.oklab_to_srgb255(lab[bm])
        out[sub] = res

    def _hairline(self, out, aout, k, hk, j, hj):
        for idx, cov in ((k, hk), (j, hj)):
            if cov is None:
                continue
            col = self.hair_cols.get(idx)
            if col is None:
                continue
            a = (self.cfg.hair_alpha * np.clip(cov, 0, 1) * aout).astype(np.float32)[..., None]
            out = out * (1.0 - a) + a * np.asarray(col, np.float32)[None, None, :]
        return out

    def paste(self, img8):
        """out = P + canvas (1 - A) over the compositor's box, written into img8 (uint8 (H, W, 3)) in place."""
        H, W = img8.shape[:2]
        x0, y0, x1, y1 = self.box
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        step = max(16, (1 << 21) // max(xb - xa, 1))
        for r0 in range(ya, yb, step):
            r1 = min(yb, r0 + step)
            reg = img8[r0:r1, xa:xb].astype(np.float32)
            a = self.A[r0 - y0:r1 - y0, xa - x0:xb - x0]
            reg *= (1.0 - a)[..., None]
            reg += self.P[r0 - y0:r1 - y0, xa - x0:xb - x0]
            np.rint(reg, out=reg)
            np.clip(reg, 0, 255, out=reg)
            img8[r0:r1, xa:xb] = reg.astype(np.uint8)
        return img8

    def visible_share(self):
        """Visible share of every iris: pixels where it is front-most inside its own disc (r <= 1) over its disc area."""
        out = []
        bx0, by0, _, _ = self.box
        for k, tk in enumerate(self.tiles):
            sl = (slice(tk.y0 - by0, tk.y0 - by0 + tk.T), slice(tk.x0 - bx0, tk.x0 - bx0 + tk.T))
            occ = self.occ[sl]
            ax = (np.arange(tk.T, dtype=np.float32) + 0.5 - tk.T / 2.0)
            inside = (ax[None, :] ** 2 + ax[:, None] ** 2) <= tk.R ** 2
            out.append(float(((occ == k) & inside).sum()) / float(inside.sum()))
        return out


# ----------------------------------------------------------------------------- analytic masks (test T1)
def pure_masks(scene, tiles, cfg, band_pad=1.08, pupil_fns=None):
    """M_k for every iris in ITS TILE coordinates: pixels of zone A (r <= 0.95 R) that must be identical to the graded disc.
    Excluded: the seam band inside a weave lens (E1), every pixel of a covered iris inside the front iris's disc (hidden), and the
    Zone C strip on the back iris (within 0.05 R + feather of the front limb). Pixels of the FRONT iris are always pure.
    The seam is the SAME function the compositor uses (seam_field, fibre-scale shift included), padded by band_pad.
    Returns (masks, info) where info holds the E1 and Zone C pixel shares."""
    masks, info = [], {"e1": [], "zc": []}
    strip = 1.0 + cfg.p["zc_cut"] + 0.012
    for k, tk in enumerate(tiles):
        xs = (np.arange(tk.x0, tk.x0 + tk.T, dtype=np.float32) + 0.5)[None, :]
        ys = (np.arange(tk.y0, tk.y0 + tk.T, dtype=np.float32) + 0.5)[:, None]
        rk = np.sqrt((xs - tk.cx) ** 2 + (ys - tk.cy) ** 2) / tk.R
        m0 = rk <= 0.95
        m = m0.copy()
        e1 = np.zeros_like(m)
        zc = np.zeros_like(m)
        for ri, rule in enumerate(scene.rules):
            if k not in (rule.a, rule.b):
                continue
            p = rule.b if k == rule.a else rule.a
            tp_ = tiles[p]
            rp = np.sqrt((xs - tp_.cx) ** 2 + (ys - tp_.cy) ** 2) / tp_.R
            ta = tiles[rule.a]
            in_lens = rp <= F3_OUT + 0.001                          # inside the partner's disc including its feather (alpha > 0): never a pure pixel
            pupd = pupil_fns[k](xs, ys, 0.01) if (pupil_fns is not None and pupil_fns.get(k) is not None) else None
            if pupd is not None:
                in_lens = in_lens & ~pupd                          # DG1 review fix: the pupil dilated by 0.01 R is pure by construction (Compositor._merge_window hides the partner's feather there)
            near_strip = (rp <= strip) & ~in_lens
            if pupd is not None:
                near_strip = near_strip & ~pupd          # Zone C never touches the pupil dilated by 0.01 R
            if rule.mode == "weave":
                tp, hw = seam_field(cfg, rule, ta, tiles[rule.b], xs, ys, ri, fine=True)
                bwp = hw * (cfg.pad if cfg.seam == "plan" else band_pad)
                front_side = (tp > bwp) if k == rule.a else (tp < -bwp)
                seam = np.abs(tp) <= bwp
                bad_lens = in_lens & ~front_side
                e1 |= (in_lens & seam) & m0
                zc |= (near_strip & ~front_side & ~seam) & m0
                bad = bad_lens | (near_strip & ~front_side)
            else:
                k_front = (rule.mode == "front_a") == (k == rule.a)
                if k_front:
                    bad = np.zeros_like(m)
                else:
                    bad = in_lens | near_strip
                    zc |= near_strip & m0
            m &= ~bad
        masks.append(m)
        info["e1"].append(float(e1.sum()) / float(m0.sum()))
        info["zc"].append(float(zc.sum()) / float(m0.sum()))
    return masks, info
