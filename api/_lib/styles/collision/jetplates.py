# -*- coding: utf-8 -*-
"""cx_plates: registry, fits and placement of the collision plates P-CX-JET (notch jets) and P-CX-RIVER (Kiss S band). numpy + PIL only.

Plates are photographs of powder made by Gemini (plates_cx/raw/<family>/*.png, monochrome white and grey); they are used as LUMINANCE only and
tinted with the colours of the irises on the two sides, so the photographic texture of real powder (clouds, chips, motion streaks) is under
the procedural iris-coloured chips. Fitted once per file and cached in plates_cx/fits.json:
  JET    source point (luminance-weighted centroid of the 4 % strip nearest the bottom edge), axis (principal axis of the luminance moments
         above it), half angle enclosing 90 % of the mass, reach90 (radius holding 60 % of the mass, the 'dense reach'), strong side
  RIVER  centre (luminance centroid), axis angle (principal axis), width at the centre (10-90 % profile), strong half
Placement rotates, scales and mirrors the plate so the source point sits on the notch and the axis on the bisector, with a soft border fade.
"""
from __future__ import annotations

# PORT of work package WP7A (step A): cx_plates.py of the DG1 snapshot of the scratch prototype, verbatim but for the edits
# scripts/styles_tests/port_collision.py lists (the baked registry instead of the raw plates, a bounded cache); test_goldens_collision.py replays the edits on the scratch and the pixels of the
# scratch's own pictures.

import math
import threading

import numpy as np

from .. import core as C
from .. import plates as PL

FADE = 0.04                                   # soft border, share of the plate side
MAX_UPSCALE = 1.1

_TL = threading.local()

_cache = C.BoundedCache(4)


def registry(fam, pv=None):
    """[Plate dicts] of the usable plates of a family (JET or RIVER) that a spec of plates version pv may pick, by id: the baked fit (what the
    prototype fitted from the raw file once and cached in fits.json) and the key, which is the plate id."""
    return [dict(PL.record(pid)["fit"], key=pid) for pid in sorted(PL.ids("P-CX-" + fam, pv))]


def _plate_lum(p, need_side):
    """Luminance (float32 0..1) of the plate at a side the placement needs, never enlarged more than MAX_UPSCALE from the file used: the bundled 1K
    file when the placement needs at most 1.1 x 1024 px, the 4K file otherwise (the collision plates have none: a collision picture is drawn on
    the canonical 1024 geometry, where no placement needs more, and PlateUnavailable says so if one ever did)."""
    lod = "1k" if need_side <= 1024 * MAX_UPSCALE else "4k"
    k = (p["key"], lod)
    a = _cache.get(k)
    if a is None:
        im = PL.load_1k(p["key"]) if lod == "1k" else PL.fetch_4k(p["key"])
        a = _cache.put(k, np.asarray(im.convert("L"), np.float32) / 255.0)
    return a


def trace(on=True):
    """Start (on) or stop (off) collecting the ids of the plates picked on this thread; stopping returns them, in the order picked (the Preview's facts and the
    admin's list of the plates a picture was drawn from). Records nothing else and changes no pixel."""
    if on:
        _TL.keys = []
        return None
    got = getattr(_TL, "keys", None)
    _TL.keys = None
    return got or []


def drawn(plates):
    keys = getattr(_TL, "keys", None)
    if keys is not None:
        keys.extend(p["key"] for p in plates)


def qa(p):
    """Accept rules (brief 5.4, adapted to what the flash and Pro plates showed): JET source y >= 0.85 H and x within 0.5 +- 0.12, half angle
    within 20-70 deg, black >= 55 %, axis within 25 deg of upward; RIVER axis 35 +- 20 deg or its mirror, centre width 0.12-0.40, black >= 50 %."""
    if p["fam"] == "JET":
        up = abs(((p["axis"] + math.pi / 2) + math.pi) % (2 * math.pi) - math.pi)
        return (p["sy"] >= 0.85 and abs(p["sx"] - 0.5) <= 0.12 and math.radians(18) <= p["half"] <= math.radians(75) and p["black"] >= 0.45
                and up < math.radians(28) and p.get("glare", 0) < 0.10)
    a = abs(math.degrees(p["axis"]) % 180)
    ok_axis = min(abs(a - 35), abs(a - 145)) <= 22
    return ok_axis and 0.10 <= p["width"] <= 0.62 and p["black"] >= 0.40         # corner glare is outside the used disc (limit 0.46 side)


def pick(fam, rnd, n, seed_tag=0, want_strong_left=None):
    """n distinct plates (no plate twice while unused ones remain), passing qa()."""
    pl = [p for p in registry(fam) if qa(p) and "pro4K" in p["key"]] or [p for p in registry(fam) if qa(p)]
    if not pl:
        return []
    idx = list(range(len(pl)))
    order = sorted(idx, key=lambda i: rnd.uniform())
    out = []
    for j in range(n):
        out.append(pl[order[j % len(order)]])
    drawn(out)
    return out


# ----------------------------------------------------------------------------- placement
def _sample_bilinear(a, xs, ys):
    h, w = a.shape
    x = np.clip(xs, 0, w - 1.001)
    y = np.clip(ys, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = (x - x0).astype(np.float32)
    fy = (y - y0).astype(np.float32)
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)


def place_jet(p, nx, ny, bis, reach_px, W, H, mirror=False, window_R=1.7, R_px=1.0, cone_scale=1.0, step=1, fade=None):
    """Luminance window of a jet plate: source point on (nx, ny), plate axis rotated onto the direction bis (rad, screen), scaled so the plate's
    60 %-mass radius equals reach_px. mirror flips the plate across its axis. Returns (window (h, w) float32, x0, y0) or None.
    window_R: window half size in units of R_px around the notch."""
    reach_plate = p["reach60"]                         # fraction of the plate side
    s = reach_px / max(reach_plate, 1e-3)              # canvas px per plate side
    need = int(s)
    L = _plate_lum(p, need)
    side = L.shape[0]
    rad = window_R * R_px
    x0, y0 = int(max(0, nx - rad)), int(max(0, ny - rad))
    x1, y1 = int(min(W, nx + rad)), int(min(H, ny + rad))
    if x1 <= x0 or y1 <= y0:
        return None
    nxg, nyg = -(-(x1 - x0) // step), -(-(y1 - y0) // step)
    gx = ((np.arange(nxg, dtype=np.float32) + 0.5) * step + (x0 - nx))[None, :]          # grid centres (step px cells)
    gy = ((np.arange(nyg, dtype=np.float32) + 0.5) * step + (y0 - ny))[:, None]
    # canvas offset -> plate offset (inverse of: rotate axis to bis, scale s, optional mirror)
    plate_axis = p["axis"]
    rot = bis - plate_axis                              # rotate the plate axis onto bis (both screen-clockwise angles)
    c, sn = math.cos(-rot), math.sin(-rot)
    ux = gx * c - gy * sn
    uy = gx * sn + gy * c                               # offset in the plate frame, canvas px, plate axis along plate_axis
    # decompose along the plate axis (a) and perpendicular (t) to mirror
    ca, sa = math.cos(plate_axis), math.sin(plate_axis)
    a = ux * ca + uy * sa
    t = -ux * sa + uy * ca
    if mirror:
        t = -t
    px = (a * ca - t * sa) / s * side + p["sx"] * side
    py = (a * sa + t * ca) / s * side + p["sy"] * side
    out = _sample_bilinear(L, px, py)
    inside = (px > 0) & (px < side - 1) & (py > 0) & (py < side - 1)
    fd = FADE if fade is None else fade
    fade = np.clip(np.minimum(np.minimum(px, side - px), np.minimum(py, side - py)) / (fd * side), 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    out = out * fade * inside
    return out.astype(np.float32), x0, y0, (a / max(R_px, 1e-6), t / max(R_px, 1e-6))


def place_river(p, cx, cy, axis_screen, width_px, W, H, mirror=False, window_R=2.6, R_px=1.0, limit=0.46, step=1):
    """Luminance window of a river plate centred on (cx, cy), band axis rotated onto axis_screen, scaled so the plate's centre width equals width_px."""
    s = width_px / max(p["width"], 1e-3)
    L = _plate_lum(p, int(s))
    side = L.shape[0]
    rad = window_R * R_px
    x0, y0 = int(max(0, cx - rad)), int(max(0, cy - rad))
    x1, y1 = int(min(W, cx + rad)), int(min(H, cy + rad))
    if x1 <= x0 or y1 <= y0:
        return None
    nxg, nyg = -(-(x1 - x0) // step), -(-(y1 - y0) // step)
    gx = ((np.arange(nxg, dtype=np.float32) + 0.5) * step + (x0 - cx))[None, :]
    gy = ((np.arange(nyg, dtype=np.float32) + 0.5) * step + (y0 - cy))[:, None]
    plate_axis = p["axis"]
    rot = axis_screen - plate_axis
    c, sn = math.cos(-rot), math.sin(-rot)
    ux = gx * c - gy * sn
    uy = gx * sn + gy * c
    ca, sa = math.cos(plate_axis), math.sin(plate_axis)
    a = ux * ca + uy * sa
    t = -ux * sa + uy * ca
    if mirror:
        t = -t
    px = (a * ca - t * sa) / s * side + p["cx"] * side
    py = (a * sa + t * ca) / s * side + p["cy"] * side
    out = _sample_bilinear(L, px, py)
    inside = (px > 0) & (px < side - 1) & (py > 0) & (py < side - 1)
    fade = np.clip(np.minimum(np.minimum(px, side - px), np.minimum(py, side - py)) / (FADE * side), 0, 1)
    fade = fade * fade * (3 - 2 * fade)
    # the plate is used inside a disc of `limit` x its side round the centre (plates carry corner glare outside it)
    dd = np.hypot(px / side - p["cx"], py / side - p["cy"])
    lim = np.clip((limit - dd) / (0.30 * limit), 0, 1)
    lim = lim * lim * (3 - 2 * lim)
    return (out * fade * inside * lim).astype(np.float32), x0, y0, (a / max(R_px, 1e-6), t / max(R_px, 1e-6))
