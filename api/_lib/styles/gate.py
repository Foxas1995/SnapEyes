# -*- coding: utf-8 -*-
"""The restoration gate: two calibrated rule sets behind one result schema {ok, rule, values, why}.

An eye whose restored iris still carries an eyelid, a lash or skin cannot be repaired by a design (an effect never recolours or
repaints an iris), and the larger the iris is drawn the more it shows; the restoration has to remove them, so a style that
multiplies them refuses such an eye. The two rule sets are ported unchanged from the design code (no re-tuning: a loosened
threshold would sell the defect it exists to stop); the registry picks the rule set per style (styles_engine.py gate_rules) and
the consequence (styles_registry.py gate: none, advisory, hard).

  lid   the collision rule (cx_kit.gate): sectors (10 deg) of the annuli 0.70-0.88 R and 0.88-0.98 R whose mean L* deviates more
        than 16 from the median sector (a lash band or a lid margin is darker or brighter than any iris sector), the ring-colour
        outlier bins (the eye profile's ring measurement re-fills bins more than dE00 20 from the ring's median: a lid band),
        and the largest single deviation. Measured on the canonical 256 grade (R units, resolution independent), 0.19 to 0.34 s.
        Fails when lid70 >= 3 or lid88 >= 4 or outlier_bins >= 40 or (outlier_bins >= 20 and lid70 + lid88 >= 2) or
        (maxdev70 >= 22 and lid70 >= 2).
  fill  the universe rule (uni_gate.gate): run18, the longest circular run (degrees) of angular sectors whose median colour in the
        band 0.80-0.96 R is more than dE 18 (Lab) from the median sector (an eyelid, a lash line or a fur fringe is one long run,
        a crypt or a sector of pigment is short); n_step, the angular bins (of 180) whose luminance steps by more than 25 L* inside
        0.04 R somewhere in 0.66-0.93 R (a lid margin or a lash is a hard edge INSIDE the iris); catch, the share of the disc
        (percent) that is very bright and neutral (L* > 92, C* < 12) inside 0.93 R (a window or phone reflection). Measured on
        the graded frame the universe fill is cut from (1024 px, 0.9 to 1.7 s): the rule was calibrated there, not on the 256
        grade. Fails on R1 run18 >= 12 and n_step >= 55, R2 run18 >= 60, R3 n_step >= 120 or R4 catch >= 0.02.
Honest limit (design notes): thresholds fitted on 21 fixtures and checked on 29 restorations; it is a screen that sends an eye back
to the restoration, not a replacement for fixing it there.
Added detectors of the lid rule (DG6 step 2a, 2026-10-13; PREPARED, OFF BY DEFAULT: the switch SNAPEYES_GATE2 is read once at import by the engine module (iris.GATE2_ON, because this
package reads no environment); off, 0, false and no switch it off, and so does leaving it unset; nothing about what passes changes until the owner turns it on). Three more ways for the
lid rule to fail, run beside the five arms above on the same 256 grade. Each one compares a part of the eye with the eye's OWN median colour or window, so deep furrows and a lighter
or darker natural rim, which run all round the iris, are no deviation.
  lid_colour_wedge     75 or more of the 360 degrees of the annulus 0.70-0.88 R have a colour (median of 8 rings, mean of 5 degrees) more than
                       dE00 12 from the annulus's median colour. The colour arm above needs dE00 20 and 40 bins of 0.70-0.92 R: a pink or
                       blue-grey wedge of the same lightness as the iris passes it.
  lid_lash_lines       the share of the pixels of 0.84-0.99 R that are thin dark lines (black top-hat of L*, a 7 px square, deeper than 10) in
                       the worst 15 degree window is 0.22 or more above the median window: a lash band is a local excess of thin dark lines, the
                       furrows of a dark iris are everywhere, so the median window is as dense as the worst one.
  lid_ring_structure   the mean squared radial component of the L* gradient (an edge that runs ROUND the iris: a lid margin, a lash line, a sclera
                       or skin patch; iris fibres run along R and have none) in the worst 15 degree window is 21 or more above the median window.
The codes are appended to the lid rule's why list; the sealed form, its four values and every seal keep their shape (valid_form accepts the three
codes whether the switch is on or not, so a seal made with it on survives a switch off). No threshold of the five arms moves. The three thresholds were set on
161 looked-at restorations (DG6 step 2a): about 10 percent beyond the largest value of the clean and natural eyes that pass today. They are a first
calibration, not a measured rate: the owner's own labels are what should confirm them before the switch is turned on.

The functions take the tight graded disc square (uint8 (t, t, 3): the disc of a graded frame without its black margin) so that
this module needs no eye object. The result's values are the numbers the design code printed (maxdev70 to 0.1, catch to 0.0001);
the profile stores them as whole numbers (store_form) so that its bytes do not depend on float formatting. The decision (ok, why)
is made on the unrounded numbers and stored with them: it is never recomputed from the rounded ones.

Module rule: every module of the v3 work starts with the __future__ import (Vercel's default Python is 3.12)."""
from __future__ import annotations

import math

import numpy as np

from .. import iris as L
from . import palette as PAL

RULES = ("lid", "fill")
# the lid rule
LID_ANNULI = ((0.70, 0.88), (0.88, 0.98))
LID_DEV = 16.0
LID70_MAX, LID88_MAX, OUTLIER_MAX = 3, 4, 40
# the fill rule
R1_RUN, R1_STEP, R2_RUN, R3_STEP, R4_CATCH = 12, 55, 60, 120, 0.02

WHY = {
    "lid": ("lid_sectors_inner", "lid_sectors_outer", "lid_ring_outliers", "lid_outliers_and_sectors", "lid_deviation",
            "lid_colour_wedge", "lid_lash_lines", "lid_ring_structure"),      # the last three: the added detectors (SNAPEYES_GATE2)
    "fill": ("fill_lid_margin", "fill_rim_sector", "fill_hard_edges", "fill_catchlight"),
}
VALUE_KEYS = {
    "lid": ("lid70", "lid88", "outlier_bins", "maxdev70_x10"),        # stored: maxdev70 in tenths
    "fill": ("run18", "n_step", "catch_x1e4"),                         # stored: catch in ten thousandths
}


# ----------------------------------------------------------------------------- the small Gaussian blur of the design code
BLUR_WORK_SIGMA = 2.0


def _gauss_kernel(sigma):
    r = max(1, int(math.ceil(3.0 * sigma)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1, dtype=np.float64) / sigma) ** 2)
    return (k / k.sum()).astype(np.float32)


def _conv_axis(a, k, axis):
    """Symmetric 1-D convolution along axis (reflect edges): the centre tap, then each pair of mirrored taps summed
    before one multiply, all in place on float32."""
    r = (len(k) - 1) // 2
    n = a.shape[axis]
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r, r)
    p = np.pad(a, pad, mode="reflect" if n > r else "edge")
    sl = [slice(None)] * a.ndim

    def part(i):
        sl[axis] = slice(i, i + n)
        return p[tuple(sl)]

    out = part(r) * k[r]
    tmp = np.empty_like(out)
    for i in range(r):
        np.add(part(i), part(2 * r - i), out=tmp)
        tmp *= k[i]
        out += tmp
    return out


def blur_small(a, sigma):
    """fx.core.blur for the small sigmas the gate uses (the full-resolution branch of the design code's blur: a sigma under
    2 * BLUR_WORK_SIGMA is never computed on a reduced grid)."""
    a = np.asarray(a, np.float32)
    if sigma <= 0:
        return a.copy()
    if sigma / 2.0 >= BLUR_WORK_SIGMA:
        raise ValueError("blur_small is for sigma under 4 px")
    if sigma < 0.25:
        return a.copy()
    k = _gauss_kernel(sigma)
    return _conv_axis(_conv_axis(a, k, 0), k, 1)


# ----------------------------------------------------------------------------- the added lid detectors (SNAPEYES_GATE2, off by default; the switch is iris.GATE2_ON)
G2_WEDGE_BAND, G2_WEDGE_RINGS, G2_WEDGE_SMOOTH, G2_WEDGE_DE, G2_WEDGE_MIN = (0.70, 0.88), 8, 5, 12.0, 75    # annulus, rings, degrees averaged, dE00, degrees
G2_LINE_BAND, G2_LINE_DEPTH, G2_LINE_REACH, G2_LINE_EXCESS = (0.84, 0.99), 10.0, 3, 0.22                    # annulus, L* depth, half width of the square (px), share
G2_EDGE_EXCESS = 21.0                                                                                       # mean squared radial gradient over the median window
G2_WINDOW = 15                                                                                              # degrees: the window of the two excess measures
_G2_GEO, _G2_POLAR = {}, {}


def _g2_geo(t):
    """(rr, phi, deg) of a t x t grid, as gate.lid draws it: rr in R units, deg the whole degree of the angle (0 to the right, clockwise)."""
    g = _G2_GEO.get(t)
    if g is None:
        if len(_G2_GEO) >= 4:
            _G2_GEO.clear()
        R = t / 2.0
        ax = np.arange(t) + 0.5 - R
        dx, dy = ax[None, :] + np.zeros((t, 1)), ax[:, None] + np.zeros((1, t))
        phi = np.arctan2(dy, dx)
        g = (np.sqrt(dx * dx + dy * dy) / R, phi, (np.degrees(phi) % 360.0).astype(np.int64) % 360)
        _G2_GEO[t] = g
    return g


def _g2_polar(img, t, r0, r1, n):
    """Bilinear samples of img (t, t, c) on n rings from r0 to r1 R at the middle of each of the 360 degrees: (n, 360, c) float64."""
    key = (t, r0, r1, n)
    m = _G2_POLAR.get(key)
    if m is None:
        if len(_G2_POLAR) >= 6:
            _G2_POLAR.clear()
        R = t / 2.0
        th = np.radians(np.arange(360) + 0.5)
        rs = np.linspace(r0, r1, n)
        X = R + np.outer(rs, np.cos(th)) * R - 0.5
        Y = R + np.outer(rs, np.sin(th)) * R - 0.5
        x0, y0 = np.clip(np.floor(X).astype(np.int64), 0, t - 2), np.clip(np.floor(Y).astype(np.int64), 0, t - 2)
        m = (x0, y0, (X - x0)[..., None], (Y - y0)[..., None])
        _G2_POLAR[key] = m
    x0, y0, fx, fy = m
    return img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy


def _g2_circ_mean(a, k):
    """Moving mean of k (odd) neighbours round the circle, along axis 0."""
    p = k // 2
    c = np.cumsum(np.concatenate([np.zeros((1,) + a.shape[1:]), a[-p:], a, a[:p]], 0), 0)
    return (c[k:] - c[:-k]) / k


def _g2_extreme(a, k, fn):
    """Running maximum or minimum over 2k + 1 pixels along both axes (a square window), edges repeated."""
    for ax in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[ax] = (k, k)
        p = np.pad(a, pad, mode="edge")
        n = a.shape[ax]
        out = None
        for i in range(2 * k + 1):
            v = p[i:i + n] if ax == 0 else p[:, i:i + n]
            out = v if out is None else fn(out, v)
        a = out
    return a


def lid_extra_why(wedge_deg, line_excess, edge_excess):
    """The reason codes of the three added detectors for their three numbers (the decision of lid_extra, on the unrounded numbers)."""
    why = []
    if wedge_deg >= G2_WEDGE_MIN:
        why.append("lid_colour_wedge")
    if line_excess >= G2_LINE_EXCESS:
        why.append("lid_lash_lines")
    if edge_excess >= G2_EDGE_EXCESS:
        why.append("lid_ring_structure")
    return why


def lid_extra(sq):
    """The three added detectors on the tight graded disc square (uint8 (t, t, 3)): {values {wedge_deg, line_excess, edge_excess}, why [codes]}.
    Pure numpy, deterministic, about 0.03 s at 241 px. The decision is made on the unrounded numbers."""
    t = sq.shape[0]
    rr, phi, deg = _g2_geo(t)
    lab = L.srgb_to_lab(sq.astype(np.float64))
    # the colour wedge: the colour of each degree of the annulus against the annulus's own median colour
    med = np.median(_g2_polar(lab, t, G2_WEDGE_BAND[0], G2_WEDGE_BAND[1], G2_WEDGE_RINGS), axis=0)
    sm = _g2_circ_mean(med, G2_WEDGE_SMOOTH)
    de = L.ciede2000(sm, np.broadcast_to(np.median(sm, axis=0), sm.shape))
    wedge = int((de > G2_WEDGE_DE).sum())
    # thin dark lines and round-the-iris edges of the outer annulus, in 15 degree windows against the eye's own median window
    p = np.pad(lab[..., 0], 1, mode="edge")
    p = (p[:, :-2] + 2.0 * p[:, 1:-1] + p[:, 2:]) / 4.0
    Ls = (p[:-2] + 2.0 * p[1:-1] + p[2:]) / 4.0                    # L* with a 3 x 3 binomial blur, edges repeated
    m = (rr > G2_LINE_BAND[0]) & (rr < G2_LINE_BAND[1])
    cnt = np.maximum(np.bincount(deg[m], minlength=360), 1)
    th = _g2_extreme(_g2_extreme(Ls, G2_LINE_REACH, np.maximum), G2_LINE_REACH, np.minimum) - Ls          # black top-hat: narrow dark lines and dots
    pl = _g2_circ_mean(np.bincount(deg[m & (th > G2_LINE_DEPTH)], minlength=360) / cnt, G2_WINDOW)
    line_excess = float(pl.max() - np.median(pl))
    p = np.pad(Ls, 1, mode="edge")
    gr = (p[1:-1, 2:] - p[1:-1, :-2]) / 2.0 * np.cos(phi) + (p[2:, 1:-1] - p[:-2, 1:-1]) / 2.0 * np.sin(phi)    # the radial component of the gradient
    pe = _g2_circ_mean(np.bincount(deg[m], weights=(gr * gr)[m], minlength=360) / cnt, G2_WINDOW)
    edge_excess = float(pe.max() - np.median(pe))
    return {"values": {"wedge_deg": wedge, "line_excess": line_excess, "edge_excess": edge_excess}, "why": lid_extra_why(wedge, line_excess, edge_excess)}


# ----------------------------------------------------------------------------- the lid rule
def lid(sq, outlier_bins):
    """The collision rule on the canonical 256 grade. sq: the tight graded disc square; outlier_bins: the number of ring bins the
    ring-colour measurement re-filled (eye.ring_colours info). Returns {ok, rule, values {lid70, lid88, outlier_bins, maxdev70},
    why [codes], raw {maxdev70 unrounded}}."""
    t = sq.shape[0]
    R = t / 2.0
    ax = np.arange(t) + 0.5 - R
    rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / R
    th = np.degrees(np.arctan2(ax[:, None] + 0 * ax[None, :], ax[None, :] + 0 * ax[:, None])) % 360.0
    rgb = sq.astype(np.float32) / 255.0
    res = []
    for (r0, r1) in LID_ANNULI:
        m = (rr > r0) & (rr < r1)
        Lv = PAL.lch(rgb[m])[0]
        b = (th[m]).astype(int) // 10
        cnt = np.maximum(np.bincount(b, minlength=36), 1)
        Lm = np.bincount(b, weights=Lv, minlength=36) / cnt
        dev = np.abs(Lm - np.median(Lm))
        res.append((float(dev.max()), int((dev > LID_DEV).sum())))
    ob = int(outlier_bins)
    lid70, lid88, md = res[0][1], res[1][1], res[0][0]
    why = []
    if lid70 >= LID70_MAX:
        why.append("lid_sectors_inner")
    if lid88 >= LID88_MAX:
        why.append("lid_sectors_outer")
    if ob >= OUTLIER_MAX:
        why.append("lid_ring_outliers")
    if ob >= 20 and lid70 + lid88 >= 2 and ob < OUTLIER_MAX:
        why.append("lid_outliers_and_sectors")
    if md >= 22.0 and lid70 >= 2:
        why.append("lid_deviation")
    bad = lid70 >= 3 or lid88 >= 4 or ob >= 40 or (ob >= 20 and lid70 + lid88 >= 2) or (md >= 22.0 and lid70 >= 2)
    if bad != bool(why):                                 # the code list and the design code's condition are one rule
        raise AssertionError("gate lid: the reason codes disagree with the rule")
    res = {"ok": not bad, "rule": "lid", "values": {"lid70": lid70, "lid88": lid88, "outlier_bins": ob, "maxdev70": round(md, 1)},
           "why": why, "raw": {"maxdev70": md}}
    if L.GATE2_ON:                                       # the added detectors (module text): more reason codes, the sealed values stay the four above
        extra = lid_extra(sq)
        res["raw"]["gate2"] = extra["values"]
        if extra["why"]:
            res["ok"], res["why"] = False, why + extra["why"]
    return res


# ----------------------------------------------------------------------------- the fill rule
def fill_features(sq):
    """The three measurements of the universe rule on the 1024 graded disc. sq: the tight graded disc square (uint8)."""
    tgt = sq.shape[0]
    R = tgt / 2.0
    g = sq.astype(np.float32) / 255.0
    ax = (np.arange(tgt, dtype=np.float32) + 0.5 - R) / np.float32(R)
    rho_ = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2)
    theta = np.arctan2(np.broadcast_to(ax[:, None], rho_.shape), np.broadcast_to(ax[None, :], rho_.shape))
    lab = L.srgb_to_lab((g * 255.0).reshape(-1, 3).astype(np.float32)).reshape(g.shape)
    th = (np.degrees(theta) % 360.0).astype(np.int32) % 360
    band = (rho_ > 0.80) & (rho_ < 0.96)
    b = th[band]
    med = np.zeros((360, 3))
    for ch in range(3):
        v = lab[..., ch][band]
        order = np.argsort(b, kind="stable")
        bs, vs = b[order], v[order]
        starts = np.searchsorted(bs, np.arange(360), "left")
        ends = np.searchsorted(bs, np.arange(360), "right")
        for a in range(360):
            seg = vs[starts[a]:ends[a]]
            med[a, ch] = np.median(seg) if len(seg) else np.nan
    x = np.arange(360)
    for ch in range(3):
        ok = ~np.isnan(med[:, ch])
        med[:, ch] = np.interp(x, x[ok], med[ok, ch], period=360)
    k = np.ones(5) / 5.0
    sm = np.stack([np.convolve(np.r_[med[-2:, c], med[:, c], med[:2, c]], k, "valid") for c in range(3)], 1)
    de = np.sqrt(((sm - np.median(sm, 0)) ** 2).sum(1))
    flag = np.r_[de > 18, de > 18]
    run, best = 0, 0
    for v in flag:
        run = run + 1 if v else 0
        best = max(best, min(run, 360))
    # radial steps
    Y = np.power(g, 2.2) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    Ls = np.where(Y > 0.008856, 116.0 * np.cbrt(Y) - 16.0, 903.3 * Y).astype(np.float32)
    Ls = blur_small(Ls, 1.5)
    nA, nR = 180, 70
    ang = (np.arange(nA) + 0.5) * 2 * np.pi / nA
    rho = np.linspace(0.60, 0.99, nR)
    X = np.clip(R + np.outer(np.cos(ang), rho) * R, 0, tgt - 1.001)
    Y_ = np.clip(R + np.outer(np.sin(ang), rho) * R, 0, tgt - 1.001)
    prof = Ls[Y_.astype(int), X.astype(int)]
    w = 7
    step = np.abs(prof[:, w:] - prof[:, :-w])
    rpos = rho[:-w]
    sel = (rpos > 0.66) & (rpos < 0.93)
    n_step = int((step[:, sel].max(1) > 25.0).sum())
    Cc = np.hypot(lab[..., 1], lab[..., 2])
    catch = 100.0 * float(((rho_ < 0.93) & (lab[..., 0] > 92.0) & (Cc < 12.0)).sum()) / float((rho_ < 0.95).sum())
    return {"run18": int(best), "n_step": n_step, "catch": round(catch, 4)}


def fill(sq):
    """The universe rule on the 1024 graded disc: {ok, rule, values {run18, n_step, catch}, why [codes]}."""
    f = fill_features(sq)
    why = []
    if f["run18"] >= R1_RUN and f["n_step"] >= R1_STEP:
        why.append("fill_lid_margin")
    if f["run18"] >= R2_RUN:
        why.append("fill_rim_sector")
    if f["n_step"] >= R3_STEP:
        why.append("fill_hard_edges")
    if f["catch"] >= R4_CATCH:
        why.append("fill_catchlight")
    return {"ok": not why, "rule": "fill", "values": dict(f), "why": why}


# ----------------------------------------------------------------------------- the sealed form and the one result schema
def store_form(res):
    """A rule's result as the profile stores it: {ok, why, values} with whole numbers only (VALUE_KEYS)."""
    v = res["values"]
    if res["rule"] == "lid":
        vals = {"lid70": int(v["lid70"]), "lid88": int(v["lid88"]), "outlier_bins": int(v["outlier_bins"]),
                "maxdev70_x10": int(round(round(float(v["maxdev70"]), 1) * 10))}
    else:
        vals = {"run18": int(v["run18"]), "n_step": int(v["n_step"]), "catch_x1e4": int(round(round(float(v["catch"]), 4) * 10000))}
    return {"ok": bool(res["ok"]), "why": [str(c) for c in res["why"]], "values": vals}


def read_form(rule, stored):
    """store_form()'s inverse: {ok, rule, values, why} with the numbers the design code printed."""
    v = stored["values"]
    if rule == "lid":
        vals = {"lid70": v["lid70"], "lid88": v["lid88"], "outlier_bins": v["outlier_bins"], "maxdev70": v["maxdev70_x10"] / 10.0}
    else:
        vals = {"run18": v["run18"], "n_step": v["n_step"], "catch": v["catch_x1e4"] / 10000.0}
    return {"ok": bool(stored["ok"]), "rule": rule, "values": vals, "why": list(stored["why"])}


def valid_form(rule, stored):
    """Is `stored` a well-formed store_form() of this rule? (the profile validator)"""
    if rule not in RULES or not isinstance(stored, dict) or set(stored) != {"ok", "why", "values"}:
        return False
    if not isinstance(stored["ok"], bool) or not isinstance(stored["why"], list) or not isinstance(stored["values"], dict):
        return False
    if any(not isinstance(c, str) or c not in WHY[rule] for c in stored["why"]):
        return False
    if stored["ok"] == bool(stored["why"]):               # ok is exactly "no reason"
        return False
    v = stored["values"]
    if set(v) != set(VALUE_KEYS[rule]):
        return False
    return all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 10_000_000 for x in v.values())


def gate(profile, rules="lid"):
    """The gate result of an eye profile for a rule set: {ok, rule, values, why}. profile: an eye.EyeProfile, or its record dict.
    A rule the profile does not carry is unknown: ok None (a hard style then refuses with why "reseal", the picker asks for
    the preview again). rules: "lid", "fill" or both ("lid+fill": ok when every one passes, False when one fails, else None)."""
    rec = profile.rec if hasattr(profile, "rec") else profile
    gates = rec.get("gate") if isinstance(rec, dict) and isinstance(rec.get("gate"), dict) else {}
    names = [r for r in str(rules).split("+") if r]
    if not names or any(r not in RULES for r in names):
        raise ValueError("unknown gate rule")
    parts = [read_form(r, gates[r]) if isinstance(gates.get(r), dict) else {"ok": None, "rule": r, "values": {}, "why": []}
             for r in names]
    if len(parts) == 1:
        return parts[0]
    oks = [p["ok"] for p in parts]
    ok = False if any(o is False for o in oks) else (None if any(o is None for o in oks) else True)
    return {"ok": ok, "rule": "+".join(names), "values": {p["rule"]: p["values"] for p in parts},
            "why": [c for p in parts for c in p["why"]]}


def set_result(profiles, rules="lid"):
    """The set-level result of the eyes of one request: {ok, eyes, first} with ok True (every eye passes), False (an eye fails),
    or None (no failure but an eye without a sealed value: unknown), first = {eye (1-based), why} of the first failing eye. An
    eye without a profile is an unknown one."""
    first, unknown = None, False
    for i, p in enumerate(profiles, 1):
        g = gate(p, rules) if p is not None else {"ok": None, "why": []}
        if g["ok"] is False and first is None:
            first = {"eye": i, "why": (g["why"] or ["gate"])[0]}
        elif g["ok"] is None:
            unknown = True
    return {"ok": False if first else (None if unknown else True), "eyes": len(profiles), "first": first}


def severity(profile):
    """How far past the gate an eye is, from the numbers its profile stores: 0.0 when every rule passes. A rule that fails costs its worst
    arm (a number over the threshold it crossed: 1.0 is on the line) and at least 1.0; a rule that passes costs nothing. The arms are
    those of lid() and fill(): lid70 / 3, lid88 / 4, outlier_bins / 40, outlier_bins / 20 with (lid70 + lid88) / 2, maxdev70 / 22 with
    lid70 / 2; run18 / 12 with n_step / 55, run18 / 60, n_step / 120, catch / 0.02. An arm of two conditions fires only when both are
    met, so it counts as the smaller of its two ratios. /api/enhance compares two restorations of one eye with it; no rule changes."""
    total = 0.0
    for rule in RULES:
        g = gate(profile, rule)
        if g["ok"] is not False:
            continue
        v = g["values"]
        if rule == "lid":
            arms = (v["lid70"] / LID70_MAX, v["lid88"] / LID88_MAX, v["outlier_bins"] / OUTLIER_MAX,
                    min(v["outlier_bins"] / 20.0, (v["lid70"] + v["lid88"]) / 2.0), min(v["maxdev70"] / 22.0, v["lid70"] / 2.0))
        else:
            arms = (min(v["run18"] / R1_RUN, v["n_step"] / R1_STEP), v["run18"] / R2_RUN, v["n_step"] / R3_STEP, v["catch"] / R4_CATCH)
        total += max(1.0, *arms)
    return round(total, 3)
