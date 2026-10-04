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
    "lid": ("lid_sectors_inner", "lid_sectors_outer", "lid_ring_outliers", "lid_outliers_and_sectors", "lid_deviation"),
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
    return {"ok": not bad, "rule": "lid", "values": {"lid70": lid70, "lid88": lid88, "outlier_bins": ob, "maxdev70": round(md, 1)},
            "why": why, "raw": {"maxdev70": md}}


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
