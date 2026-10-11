# -*- coding: utf-8 -*-
"""A dark lash curtain over the iris with a lid margin behind it: read on the photo in /api/analyze and blocked with the
existing "eyelid" retake (wave-q3 lashes: test photos 29, 26 and 09).

Lashes, a lash line and the shadow of a lid can hang over a quarter of the iris with too little lid skin for the eyelid gate
(coverage.py) to read it (hand labels 25 to 28 percent of the iris hidden; the gate reads 7.2, 9.9 and 8.5 to 12.8 against its
line of 11.0). No fill can repair that: it would have to invent the iris under the curtain, and the studio model keeps such a
mass or repaints it as smeared fibres, at random from render to render. The honest answer is the retake the eyelid gate
already gives: the same reason, so the same EN/DE/LT/HU text, which already says to keep lashes and mascara out of the iris.

Two readings must both be there, and below them the photo is not touched (analyze adds nothing):
  1. measure(): the tone deficit in polar space. Each radius has a reference tone (the 60th percentile of its L* all round); a
     cell smoothed over 0.025 r x 4 degrees and more than DEFICIT L* under it is dark. A curtain is ONE big connected dark shape
     that hangs from the rim and reaches deep (r0 <= PRE_R0). numpy only, about 40 ms on a 256 px copy. It decides only whether
     the second reading is worth its 0.2 to 0.3 s.
  2. margin_cover(): the share of the disc that lies beyond the deepest lid margin lid_geometry accepted, read from its debug
     list BEFORE its LID_DEEP_STEP rule throws a weak deep margin away as "hanging lashes" (which is what 29 is). With
     BLOCK_COVER percent or more behind a margin it is lid plus lashes: no iris under it to repair it from.
Reach (judge re-run, 287 circles: the live circle and 6 moves of 2 to 10 percent of r, radius x 0.90 to 1.10, for 41 photos): 0 of 161
runs on the 23 photos labelled clean blocked (the owner's 4 eyes and both samples among them); 09 blocks on 5 of 7 circles, 26 on 6
of 7, 29 on 2 of 7 (lid_geometry does not always accept 29's deep margin). Of an independent set of 55 Commons eye photos the live
gates pass 42: two of them (cm021, cm023, the lid across the top of the iris) now block and no other does. The pre-read matters:
without it the cover alone reads 16.3 and 13.2 on two dark-iris photos (cm010, cm017) that have no dark shape.
SNAPEYES_LASHBLOCK=off (or 0/false/no) switches the block off. The repair of the curtains that can be repaired (11) is
lashfill.py, in /api/deglare; the two do not depend on each other.
"""
import os
import numpy as np
from PIL import Image
from . import iris as L

# the BOM strip is for values set from PowerShell
LB_ON = (os.environ.get("SNAPEYES_LASHBLOCK") or "on").strip().lstrip("\ufeff").lower() not in ("off", "0", "false", "no")

SIDE = 256                   # px: the crop is read on a copy this size
NR, NA = 76, 360             # polar grid: NR rows of 0.0125 iris radii from R0 outwards, 1 degree columns
R0, R1 = 0.05, 1.0
DR = (R1 - R0) / NR
ROW_LO, ROW_HI = 0.45, 0.93  # rows read (and never nearer the pupil than PUPIL_GAP)
PUPIL_GAP = 0.06
REF_Q = 60.0                 # a row's reference tone: this percentile of its L*
SMOOTH = (2, 4)              # box smoothing of the tone, rows and columns each way (0.025 r x 4 degrees)
L_SKY = 88.0                 # brighter than this is a reflection: not read
DEFICIT = 15.0               # L* under the row's reference that makes a smoothed pixel dark
RIM_ROOT = 0.80              # a dark shape must reach this radius to hang from the rim
PRE_R0 = 0.60                # the dark shape must reach in to this radius (a curtain hangs deep; the limbal crescent and a rim sliver do not)

# ---- geometry and sampling ------------------------------------------------------------------------------------------
_CACHE = {}

def _grid(side, pad):
    """bilinear sampling of a side x side square into the polar grid, as flat indices and weights (cached)"""
    key = (side, round(float(pad), 4))
    g = _CACHE.get(key)
    if g is None:
        R = side / (2.0 * pad)
        rr = R0 + (np.arange(NR) + 0.5) * DR
        th = np.radians((np.arange(NA) + 0.5) * 360.0 / NA)
        X = side / 2.0 + np.outer(rr, np.cos(th)) * R - 0.5
        Y = side / 2.0 + np.outer(rr, np.sin(th)) * R - 0.5
        x0 = np.clip(np.floor(X).astype(np.int64), 0, side - 2)
        y0 = np.clip(np.floor(Y).astype(np.int64), 0, side - 2)
        fx = np.clip(X - x0, 0, 1).astype(np.float32)
        fy = np.clip(Y - y0, 0, 1).astype(np.float32)
        g = (y0 * side + x0, fx, fy, rr)
        _CACHE[key] = g
    return g

def _sample(arr, pad):
    """arr side x side x 3 float32 -> (NR, NA, 3) polar, and the radii"""
    side = arr.shape[0]
    i0, fx, fy, rr = _grid(side, pad)
    flat = arr.reshape(-1, arr.shape[2])
    a, b, c, d = flat[i0], flat[i0 + 1], flat[i0 + side], flat[i0 + side + 1]
    fx, fy = fx[..., None], fy[..., None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy, rr

def polar_lab(im, pad):
    """(lab (NR, NA, 3), lit (NR, NA) bool, rr) of a square iris image. lit: not the black round the disc."""
    sm = im.convert("RGB")
    if sm.size[0] != SIDE or sm.size[1] != SIDE:
        sm = sm.resize((SIDE, SIDE), Image.BOX if sm.size[0] >= SIDE else Image.LANCZOS)
    rgb, rr = _sample(np.asarray(sm, np.float32), pad)
    return L.srgb_to_lab(rgb).astype(np.float32), rgb.sum(-1) > 12.0, rr

def _box_cols(a, k):
    """mean over 2k+1 columns, wrapping round the circle"""
    p = np.concatenate([a[:, -k:], a, a[:, :k]], 1)
    c = np.concatenate([np.zeros((a.shape[0], 1)), np.cumsum(p, 1, dtype=np.float64)], 1)
    return ((c[:, 2 * k + 1:] - c[:, :-(2 * k + 1)]) / (2 * k + 1)).astype(np.float32)

def _box_rows(a, k):
    p = np.pad(a, ((k, k), (0, 0)), mode="edge")
    c = np.concatenate([np.zeros((1, a.shape[1])), np.cumsum(p, 0, dtype=np.float64)], 0)
    return ((c[2 * k + 1:] - c[:-(2 * k + 1)]) / (2 * k + 1)).astype(np.float32)

def pupil_rho(lab, lit, rr):
    """the pupil's radius in iris radii, from the median tone of each radius (first radius where it climbs half way
    from the dark core to the iris), clamped to 0.05-0.5. Only used to keep the dark pupil edge out of the rows read."""
    Lm = np.array([np.median(lab[i, :, 0][lit[i]]) if lit[i].sum() > 40 else np.nan for i in range(len(rr))])
    ok = np.isfinite(Lm)
    if ok.sum() < 10:
        return 0.25
    Lm = np.interp(np.arange(len(rr)), np.nonzero(ok)[0], Lm[ok])
    core = float(np.min(Lm[rr < 0.30])) if (rr < 0.30).any() else float(Lm[0])
    iris = float(np.percentile(Lm[(rr > 0.45) & (rr < 0.95)], 90))
    if iris - core < 12.0:
        return 0.25
    up = np.nonzero(Lm > core + 0.5 * (iris - core))[0]
    return float(np.clip(rr[up[0]] if len(up) else 0.25, 0.05, 0.5))

def deficit(lab, lit, rr, pupil, q=REF_Q, lo=ROW_LO):
    """(D, rows, ref): D = the row's reference tone minus the smoothed tone (L*), positive = darker than the iris at
    that radius; rows = the radii read; ref = the reference per radius. None when a row has too little iris."""
    Lc = lab[..., 0]
    rows = (rr >= max(lo, pupil + PUPIL_GAP)) & (rr <= ROW_HI)
    ok = lit & (Lc > 3.0) & (Lc < L_SKY)
    ref = np.full(len(rr), np.nan, np.float32)
    for i in np.nonzero(rows)[0]:
        if ok[i].sum() >= 40:
            ref[i] = np.percentile(Lc[i][ok[i]], q)
    have = np.nonzero(np.isfinite(ref))[0]
    if len(have) < 4:
        return None
    ref = np.interp(np.arange(len(rr)), have, ref[have]).astype(np.float32)
    Ls = _box_rows(_box_cols(np.where(ok, Lc, ref[:, None]), SMOOTH[1]), SMOOTH[0])
    return (ref[:, None] - Ls).astype(np.float32), rows, ref

def _row_area(rr):
    """each row's share of the iris disc, per column (in %)"""
    return rr * DR * 2.0 / NA * 100.0

def components(mask, rr, rim=RIM_ROOT):
    """every 8-connected shape of mask (wrapping round the circle) that reaches radius rim, largest first, each
    {"area" (% of the disc), "a0" (degrees, where its arc starts), "span", "r0", "r1", "cells": pooled (row, col)}.
    Worked on a 2x2 pooled copy (a cell is set when two of its four are), so a shape's size costs nothing."""
    nr2, na2 = NR // 2, NA // 2
    m2 = mask[:nr2 * 2, :na2 * 2].reshape(nr2, 2, na2, 2).sum((1, 3)) >= 2
    if not m2.any():
        return []
    seen = np.zeros((nr2, na2), bool)
    w2 = _row_area(rr[:nr2 * 2].reshape(nr2, 2).mean(1)) * 4.0
    out = []
    for y, x in zip(*np.nonzero(m2)):
        if seen[y, x]:
            continue
        seen[y, x] = True
        stack, cells = [(y, x)], []
        while stack:
            cy, cx = stack.pop()
            cells.append((cy, cx))
            for dy in (-1, 0, 1):
                yy = cy + dy
                if yy < 0 or yy >= nr2:
                    continue
                for dx in (-1, 0, 1):
                    xx = (cx + dx) % na2
                    if m2[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        stack.append((yy, xx))
        cy_, cx_ = np.array([c[0] for c in cells]), np.array([c[1] for c in cells])
        rmax = float(rr[min(nr2 * 2 - 1, cy_.max() * 2 + 1)])
        if rmax < rim:
            continue
        cols = np.unique(cx_)
        gaps = np.diff(np.concatenate([cols, [cols[0] + na2]]))
        k = int(np.argmax(gaps))
        start = int(cols[(k + 1) % len(cols)])
        span = int(na2 - gaps[k] + 1)
        out.append(dict(area=float(w2[cy_].sum()), a0=float(start * 360.0 / na2), span=float(span * 360.0 / na2),
                        r0=float(rr[cy_.min() * 2]), r1=rmax, cells=cells))
    out.sort(key=lambda c: -c["area"])
    return out

def measure(im, pad, pupil=None, lab=None):
    """the dark shape reading of a square iris image (masked or not; the disc is what is read): {"area", "a0", "a1", "span",
    "centre", "r0", "r1", "pupil"}; area is the largest rim-rooted dark shape as % of the disc (0.0 when none), or None when
    the iris cannot be read. lab: the polar_lab tuple when the caller has it."""
    lab_, lit, rr = lab if lab is not None else polar_lab(im, pad)
    p = pupil_rho(lab_, lit, rr) if pupil is None else float(pupil)
    d = deficit(lab_, lit, rr, p)
    if d is None:
        return None
    D, rows, _ = d
    mask = (D > DEFICIT) & rows[:, None]
    comps = components(mask, rr)
    comp = comps[0] if comps else None
    out = dict(area=0.0, a0=None, a1=None, span=0.0, centre=None, r0=None, r1=None, pupil=round(p, 3))
    if comp is not None:
        out.update(area=comp["area"], a0=comp["a0"], a1=(comp["a0"] + comp["span"]) % 360.0, span=comp["span"],
                   r0=comp["r0"], r1=comp["r1"], centre=(comp["a0"] + comp["span"] / 2.0) % 360.0)
    return out

# ---- lid margins: where a curtain is lid and lashes, with no iris under it ----------------------------------------------
BLOCK_COVER = 13.0           # % of the disc behind the deepest accepted lid margin: block (analyze, reason "eyelid")
BLOCK_PRE = 4.0              # the measure() area (with r0 <= PRE_R0) that pays for the lid_geometry read in analyze (about 0.25 s)

def margin_cover(square, pad, pupil_r=None):
    """% of the iris disc that lies beyond the deepest lid margin lid_geometry accepted, per side the larger (0.0 when
    it accepted none). Read from lid_geometry's debug list, so a margin its LID_DEEP_STEP rule then throws away (a weak
    deep margin: lashes hanging over the iris, 29) still counts. square: the UNMASKED crop as the client cuts it (the
    rim test reads outside the circle); pupil_r: the analyze pupil as a share of the crop side."""
    r_frac = L.iris_radius_frac(pad)
    pr = (float(pupil_r) / r_frac) if pupil_r else None
    dbg = []
    L.lid_geometry(square, r_frac, None, dbg, pr, None)
    deepest = {}
    for d in dbg:
        if d.get("ok") and "c" in d and (d["side"] not in deepest or d["c"][0] > deepest[d["side"]][0]):
            deepest[d["side"]] = d["c"]
    if not deepest:
        return 0.0
    n = 160
    ax = (np.arange(n) - n / 2 + 0.5) / (r_frac * n)
    X, Y = np.meshgrid(ax, ax)
    disk = np.hypot(X, Y) < 1.0
    best = 0.0
    for side, c in deepest.items():
        yb = c[0] + c[1] * X + c[2] * X * X
        cov = (Y < yb) if side == "top" else (-Y < yb)
        best = max(best, 100.0 * float((cov & disk).sum()) / float(disk.sum()))
    return best

def square_of(im, cx, cy, r, pad=1.12):
    """the unmasked square the client cuts round the analyze circle (circular_crop without its mask)"""
    S = int(round(2 * r * pad))
    x0, y0 = int(round(cx - S / 2)), int(round(cy - S / 2))
    sq = Image.new("RGB", (S, S), (0, 0, 0))
    sq.paste(im, (-x0, -y0))
    return sq

def eyelid_block(im, cx, cy, r, pad, pupil_r, crop=None):
    """(block, info) for analyze: the lash-curtain check that comes after the eyelid gate. measure() on the masked crop
    (analyze's own circular_crop when given) decides whether lid_geometry is worth reading: a dark shape hanging from
    the rim and reaching deep (BLOCK_PRE, PRE_R0). The block needs BLOCK_COVER % of the disc behind an accepted margin."""
    if not LB_ON:
        return False, None
    m = measure(crop if crop is not None else L.mask_disk(square_of(im, cx, cy, r, pad), pad), pad)
    info = {"area": None if m is None else round(m["area"], 1), "cover": None}
    if m is None or m["area"] < BLOCK_PRE or (m["r0"] or 1.0) > PRE_R0:
        return False, info
    info["cover"] = round(margin_cover(square_of(im, cx, cy, r, pad), pad, pupil_r), 1)
    return info["cover"] >= BLOCK_COVER, info
