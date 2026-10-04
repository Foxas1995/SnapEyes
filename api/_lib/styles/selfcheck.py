# -*- coding: utf-8 -*-
"""styles.selfcheck: the cheap checks of the design brief that run on every delivered artwork (about 0.3 s at 4096 px) and are written into
artwork_<digest>.json for the owner's order page. A failure sets needs_review on the delivery (the existing mechanism): the owner releases the
order, recomposes it or re-renders an eye. None of them draws; each takes the finished 8-bit canvas and the facts the engine already holds.

  T1  iris integrity     every pixel of the visible inner zone (zone A: radius up to 0.95 R, minus the masks an overlap style publishes) of every iris
                         equals the graded disc it was drawn from: largest absolute difference at most 1 of 255. The product's promise ("your iris
                         is your iris") in a number. The disc is pasted last and an effect never sees it, so for the singles this is 0
  T2  pupil clearance    the pupil mask grown by 0.01 R lies entirely inside the iris's visible region and outside every strip an overlap style
                         draws over an iris (the contact edge): not one pixel of a pupil is ever covered. A square structuring element: stricter
                         than a disc, never looser
  T3  visible share      the visible area of each iris against the floor of its style (an overlap hides part of an iris: Kiss at least 93 percent,
                         Collision Infinity 87, Family Colours 82, Clean Family 97, chain interior 80 and ends 90, singles 100)
  T4  black share        the share of pixels with luma under 12/255 (the brief's literal 3/255 cannot be met by its own backgrounds, #07080A and
                         #040406 have luma 4 to 8, so the verdict uses 12, as the design round did; the literal 3 is reported beside it) inside the
                         range of the style (Powder Burst 45 to 65 percent, Elements 55 to 75, Clean 100 percent outside the iris)
  T6  matter on iris     the number of visible zone A pixels that are not the iris's own (the same measurement as T1, counted): 0
  T7  text               the draw log (api/_lib/styles/text.py) holds only what the customer typed: names, a date, a family name; never a style
                         name, a brand, a slogan or a placeholder
  T12 no hearts          no heart glyph in any drawn string and no heart word in any id, slug or layout the render used (the registry check covers
                         the ids at build time; this is the run-time half)

The checks are functions of arrays and lists: an engine passes what it has (the discs, the masks of its compositor) and gets back a small JSON
dict. run() makes the whole report; every key of it is a number, a boolean or a short list (it travels in the artwork record).
"""
from __future__ import annotations

import re
import time

import numpy as np

TOL = 1                          # T1: the largest allowed difference, of 255
ZONE_A = 0.95                    # radius of the inner zone, share of R
PUPIL_GROW = 0.01                # T2: the pupil mask grown by this share of R
BLACK_THR = 12                   # T4
BLACK_LITERAL = 3
CHUNK_ROWS = 256                 # rows per slice: the temporaries of a 4096 px check stay a few MB

# the heart glyphs: the white and black hearts, the heavy and ornamental hearts, the coloured and the anatomical heart emoji
HEART_CHARS = frozenset(chr(c) for c in (0x2661, 0x2665, 0x2763, 0x2764, 0x2765, 0x2766, 0x2767, *range(0x1F493, 0x1F4A0), 0x1F5A4, 0x1F90D,
                                         0x1F90E, 0x1F9E1, 0x1FA75, 0x1FA76, 0x1FA77, 0x1FAC0))
HEART_WORDS = frozenset(("heart", "hearts", "love", "loves", "valentine", "valentines", "cupid"))
TEXT_KINDS = frozenset(("names", "date", "family"))


# ----------------------------------------------------------------------------- masks
def zone_mask(disc, zone=ZONE_A):
    """Boolean (t, t): the pixels of the disc's tight square inside radius zone x R (disc.R, in px, is exact)."""
    t = disc.g.shape[0]
    ax = (np.arange(t, dtype=np.float64) + 0.5) - t / 2.0
    ax2 = ax * ax
    return (ax2[None, :] + ax2[:, None]) <= (zone * disc.R) ** 2


def _window(img8, disc):
    """(rows of the canvas, columns, the matching slices of the disc's tight square), or None when the disc is off the canvas."""
    H, W = img8.shape[:2]
    t = disc.g.shape[0]
    xa, ya = max(0, disc.x0), max(0, disc.y0)
    xb, yb = min(W, disc.x0 + t), min(H, disc.y0 + t)
    if xa >= xb or ya >= yb:
        return None
    return (ya, yb, xa, xb), (ya - disc.y0, yb - disc.y0, xa - disc.x0, xb - disc.x0)


# ----------------------------------------------------------------------------- T1 and T6
def iris_pixels(img8, disc, mask=None, zone=ZONE_A, tol=TOL):
    """Compare the canvas with the graded disc over the visible inner zone: {max_abs_diff, bad (pixels differing by more than tol), checked}.
    mask: a boolean (t, t) of the pixels to compare (an overlap style's published mask M_k); default: the whole zone A."""
    win = _window(img8, disc)
    m = zone_mask(disc, zone) if mask is None else np.asarray(mask, bool)
    if win is None:
        return {"max_abs_diff": 0, "bad": 0, "checked": 0}
    (ya, yb, xa, xb), (ga, gb, ca, cb) = win
    mx, bad, n = 0, 0, 0
    for r0 in range(ga, gb, CHUNK_ROWS):
        r1 = min(gb, r0 + CHUNK_ROWS)
        sel = m[r0:r1, ca:cb]
        if not sel.any():
            continue
        out = img8[ya + (r0 - ga):ya + (r1 - ga), xa:xb]
        ref = disc.g[r0:r1, ca:cb]
        d = (np.maximum(out, ref) - np.minimum(out, ref)).max(-1)[sel]          # |a - b| of two uint8 without leaving uint8
        mx = max(mx, int(d.max()))
        bad += int((d > tol).sum())
        n += int(d.size)
    return {"max_abs_diff": mx, "bad": bad, "checked": n}


def t1_iris_integrity(img8, discs, masks=None, zone=ZONE_A, tol=TOL):
    """T1 over every iris: ok when no visible zone A pixel differs from its graded disc by more than tol."""
    per = [iris_pixels(img8, d, None if masks is None else masks[i], zone, tol) for i, d in enumerate(discs)]
    return {"ok": all(p["bad"] == 0 for p in per), "max_abs_diff": max((p["max_abs_diff"] for p in per), default=0),
            "checked": sum(p["checked"] for p in per), "bad": sum(p["bad"] for p in per)}


def t6_matter_on_iris(img8, discs, masks=None, zone=ZONE_A, tol=TOL):
    """T6: the count of visible zone A pixels that are not the iris's own: 0. (T1's measurement, counted.)"""
    r = t1_iris_integrity(img8, discs, masks, zone, tol)
    return {"ok": r["bad"] == 0, "count": r["bad"]}


# ----------------------------------------------------------------------------- T2
def dilate(mask, r):
    """The boolean mask grown by r px with a square structuring element (separable running maximum: r shifted views per axis)."""
    r = int(np.ceil(r))
    if r <= 0:
        return np.asarray(mask, bool).copy()
    m = np.asarray(mask, bool)
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (r, r)
        p = np.pad(m, pad, mode="constant")
        n = m.shape[axis]
        out = np.zeros_like(m)
        for i in range(2 * r + 1):
            sl = [slice(None), slice(None)]
            sl[axis] = slice(i, i + n)
            out |= p[tuple(sl)]
        m = out
    return m


def t2_pupil_clearance(pupil_masks, visible_masks, strips=None, radii=None, grow=PUPIL_GROW):
    """T2: for every iris the pupil mask grown by grow x R must lie inside its visible mask and outside every strip (the masks an overlap style
    draws over an iris). Masks are boolean arrays of one canvas-sized or tile-sized frame each; radii the iris radii in px. Returns
    {ok, violations (pixels), per_iris}."""
    per = []
    for i, pm in enumerate(pupil_masks):
        r = (grow * float(radii[i])) if radii is not None else 1.0
        g = dilate(pm, r)
        v = np.asarray(visible_masks[i], bool)
        bad = int((g & ~v).sum())
        if strips is not None and strips[i] is not None:
            bad += int((g & np.asarray(strips[i], bool)).sum())
        per.append(bad)
    return {"ok": all(b == 0 for b in per), "violations": sum(per), "per_iris": per}


# ----------------------------------------------------------------------------- T3, T4
def t3_visible_share(visible_masks, disc_masks, floors):
    """T3: per iris the visible share of its disc (visible pixels over disc pixels), against the style's floor (one number or one per iris)."""
    fl = [float(floors)] * len(visible_masks) if np.isscalar(floors) else [float(x) for x in floors]
    shares = []
    for v, d in zip(visible_masks, disc_masks):
        n = int(np.asarray(d, bool).sum())
        shares.append(round(float((np.asarray(v, bool) & np.asarray(d, bool)).sum()) / n, 4) if n else 1.0)
    return {"ok": all(s + 1e-9 >= f for s, f in zip(shares, fl)), "shares": shares, "floors": fl}


def black_shares(img8, thresholds=(BLACK_THR,)):
    """Shares of pixels whose luma is below each threshold / 255 (luma 0.299, 0.587, 0.114 in float32, row slices, one pass)."""
    a = np.asarray(img8)
    H = a.shape[0]
    low = [0] * len(thresholds)
    for r0 in range(0, H, CHUNK_ROWS):
        s = a[r0:r0 + CHUNK_ROWS].astype(np.float32)
        y = s[..., 0] * 0.299 + s[..., 1] * 0.587 + s[..., 2] * 0.114
        for k, thr in enumerate(thresholds):
            low[k] += int((y < thr).sum())
    n = float(a.shape[0] * a.shape[1])
    return [v / n for v in low]


def black_share(img8, thr=BLACK_THR):
    """Share of pixels whose luma is below thr / 255."""
    return black_shares(img8, (thr,))[0]


def t4_black_share(img8, lo, hi, thr=BLACK_THR):
    s, lit = black_shares(img8, (thr, BLACK_LITERAL))
    return {"ok": lo <= s <= hi, "share": round(s, 4), "range": [lo, hi], "literal3": round(lit, 4)}


# ----------------------------------------------------------------------------- T7, T12
def t7_text(log, customer):
    """T7: every entry of the draw log is the customer's own string (as typed, cleaned) and of a known kind. customer: the strings the customer
    typed (names, date, family name) and the lockup of the names; an empty log is fine (no text asked)."""
    allowed = {str(c).strip() for c in customer if str(c).strip()}
    foreign = [e.get("text") for e in (log or []) if e.get("kind") not in TEXT_KINDS or str(e.get("text", "")).strip() not in allowed]
    return {"ok": not foreign, "drawn": len(log or []), "foreign": foreign[:5]}


def t12_no_hearts(strings=(), ids=()):
    """T12: no heart glyph in a drawn string and no heart word in an id, slug or layout name that the render used."""
    glyphs = sorted({ch for s in strings for ch in str(s) if ch in HEART_CHARS})
    words = sorted({w for i in ids for w in re.split(r"[^a-z]+", str(i).lower()) if w in HEART_WORDS})
    return {"ok": not glyphs and not words, "glyphs": [f"U+{ord(c):04X}" for c in glyphs], "words": words}


# ----------------------------------------------------------------------------- the report
def run(img8, discs, text_log=(), customer=(), ids=(), black_range=None, masks=None, pupils=None, visible=None, strips=None, disc_masks=None,
        share_floor=1.0, zone=ZONE_A, tol=TOL):
    """The whole report: {ok, checks: {t1, t6, t7, t12 [, t2, t3, t4]}, ms}. t2 and t3 run when the engine passes the masks of its compositor
    (pupils, visible, strips, disc_masks); t4 when it passes the range of its style (black_range = (lo, hi)). A single iris engine passes the
    discs, the text log and the customer's strings."""
    t0 = time.perf_counter()
    t1 = t1_iris_integrity(img8, discs, masks, zone, tol)                       # T6 is the same measurement, counted: made once
    checks = {"t1": t1, "t6": {"ok": t1["bad"] == 0, "count": t1["bad"]},
              "t7": t7_text(text_log, customer), "t12": t12_no_hearts([e.get("text", "") for e in (text_log or [])], ids)}
    if pupils is not None and visible is not None:
        checks["t2"] = t2_pupil_clearance(pupils, visible, strips, [d.R for d in discs])
    if visible is not None and disc_masks is not None:
        checks["t3"] = t3_visible_share(visible, disc_masks, share_floor)
    if black_range is not None:
        checks["t4"] = t4_black_share(img8, black_range[0], black_range[1])
    return {"ok": all(c["ok"] for c in checks.values()), "checks": checks, "ms": int(round((time.perf_counter() - t0) * 1000))}
