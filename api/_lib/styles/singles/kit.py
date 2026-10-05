# -*- coding: utf-8 -*-
"""designs.singles_kit: the shared foundation of the v3 SINGLES family (ported from the scratch prototype).

What lives here (used by designs/singles.py and its helper modules):
  Frame / frame_for   canvas + iris geometry of a single (1:1, 4:5, 9:19.5 wallpaper, 3:2 ...), text lockup rules
  Disc3 / place_iris  the graded iris with the v3 feather F3 (10-90 % alpha width 0.031 R, natural limbal ring kept and
                      extended radially, so zone A (r <= 0.95 R) is byte-identical to fx.core's graded disc)
  paste_iris          the LAST pixel operation, exactly like fx.core.paste_iris_last but with F3
  draw_names          the ONLY text an artwork may carry: the customer's names and date (Cinzel caps), with a draw log
  MCtx                the context object the effect functions receive (W, H, S, discs, rand, opts ...)
  sample_disc         bilinear sample of the graded iris at polar positions (chips, limbus breakup, coronas)
  palette helpers     secondary hue, ramp stops (deep / mid / hot per ring angle), class fallbacks
Rules enforced: an effect only receives the float canvas (never the disc); the iris is pasted last; every random number
comes from fx.core.Rand (sha256 seeds); sizes in R and S units; numpy + PIL only.
"""
from __future__ import annotations

# PORT of work package WP5A (step A): singles_kit.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists
# (imports, plates, caches, text; the legacy feather option is gone); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures.
# WP5B (step B) changed the seed and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import math
import time

import numpy as np
from PIL import Image

from .. import core as C
from .. import layouts as LY
from .. import plates as RG
from ..text import draw_names, NAME_WARM, NAME_GOLD

L = C.L
TWO_PI = 2.0 * math.pi
F32 = np.float32
F3_SPAN = 0.052              # feather span in R, centred on the limb: 10-90 % alpha width = 0.608 x span = 0.0316 R
F3_INNER = 1.0 - F3_SPAN / 2.0
WALL_NAME_Y = 0.80           # wallpaper name baseline, share of H (clear of the lock-screen buttons and the home bar)


# ----------------------------------------------------------------------------- loading
def load_eye(eye):
    """An Iris from an Iris or from the bytes of a restored iris square (a function reads what the request carried: a path is never opened)."""
    if isinstance(eye, C.Iris):
        return eye
    if isinstance(eye, (bytes, bytearray)):
        return C.Iris(bytes(eye))
    raise TypeError("an eye is an Iris or the bytes of an image")


# ----------------------------------------------------------------------------- geometry of a single
# per design and format: iris radius as a share of S (S = the short side), centre y as a share of H
# brief 3.6 / 3.7 / 3.8 / 3.9 / 3.10 / 3.12 (v3 final).  "r" is R as a share of S (S = short side = W on a wallpaper: powder
# D 0.50-0.55 W -> R 0.26 W); "cy" is the centre y as a share of H.  The wallpaper centre sits at 0.40 H (safe zones 0.20 H top,
# 0.06 H foot).  4:5: R = 0.24 W, centre (0.5 W, 0.44 H) for powder, the same offsets for the others.
SPECS = {
    "powder":   {"r": {"1:1": 0.260, "4:5": 0.260, "9:19.5": 0.265}, "cy": {"1:1": 0.500, "4:5": 0.440, "9:19.5": 0.400}},
    "splash":   {"r": {"1:1": 0.250, "4:5": 0.250, "9:19.5": 0.255}, "cy": {"1:1": 0.520, "4:5": 0.460, "9:19.5": 0.400}},
    "elements": {"r": {"1:1": 0.250, "4:5": 0.250, "9:19.5": 0.255}, "cy": {"1:1": 0.520, "4:5": 0.460, "9:19.5": 0.400}},
    "gold":     {"r": {"1:1": 0.270, "4:5": 0.270, "9:19.5": 0.270}, "cy": {"1:1": 0.470, "4:5": 0.430, "9:19.5": 0.400}},
    "radiance": {"r": {"1:1": 0.305, "4:5": 0.305, "9:19.5": 0.290}, "cy": {"1:1": 0.500, "4:5": 0.440, "9:19.5": 0.400}},
    "clean":    {"r": {"1:1": 0.330, "4:5": 0.330, "9:19.5": 0.330}, "cy": {"1:1": 0.500, "4:5": 0.450, "9:19.5": 0.410}},
}
DEFAULT_R = 0.25


class Frame:
    """Everything geometric about one artwork: canvas, iris circle (requested), text lockup."""
    __slots__ = ("fmt", "W", "H", "S", "wall", "cx", "cy", "R", "has_text", "text_y", "text_box", "key", "design", "size",
                 "shrink")

    def __repr__(self):
        return f"Frame({self.design} {self.fmt} {self.W}x{self.H} c=({self.cx:.1f},{self.cy:.1f}) R={self.R:.1f})"


REF_SIZE = 1024


def _snap(cx, cy, R):
    """The whole-pixel geometry fx.core.place_disc gives a disc requested at (cx, cy, R): pure arithmetic, no grading."""
    Sd = max(8, int(round(2.0 * R / L.STUDIO_FILL)))
    tgt = max(8, int(round(Sd * L.STUDIO_FILL)))
    x0, y0 = int(round(cx - tgt / 2.0)), int(round(cy - tgt / 2.0))
    return x0 + tgt / 2.0, y0 + tgt / 2.0, tgt / 2.0


def frame_for(design, fmt="1:1", size=1024, has_text=False, _ref=False):
    """size = the LONG side in px (1024 preview, 4096 master). With text the artwork moves up 0.03 S (not on the
    wallpaper, whose names sit at 0.80 H) and the iris shrinks x 0.94 (brief 1.5.7).
    PREVIEW == MASTER: the geometry is laid out at 1024 and snapped there exactly as the preview does; a master scales that snapped geometry
    up (so every disc, plate and particle sits on the preview's own spot, and a 4096 file reduced to 1024 lines up with the preview)."""
    W, H = LY.canvas_size(fmt, size)
    S = min(W, H)
    sp = SPECS.get(design, {"r": {}, "cy": {}})
    rf = sp["r"].get(fmt, DEFAULT_R)
    cyf = sp["cy"].get(fmt, 0.5)
    wall = fmt == LY.WALL
    f = Frame()
    f.design, f.fmt, f.W, f.H, f.S, f.wall, f.size, f.has_text = design, fmt, W, H, S, wall, size, bool(has_text)
    f.shrink = 0.94 if has_text else 1.0
    f.cx = W / 2.0
    f.cy = cyf * H - (0.03 * S if (has_text and not wall) else 0.0)
    f.R = rf * S * f.shrink
    f.key = f"single/{fmt}"
    f.text_y = (WALL_NAME_Y * H) if wall else 0.93 * H
    if size == REF_SIZE or _ref:
        f.cx, f.cy, f.R = _snap(f.cx, f.cy, f.R)
    else:
        f1 = frame_for(design, fmt, REF_SIZE, has_text, _ref=True)
        f.cx, f.cy, f.R = f1.cx * (W / f1.W), f1.cy * (H / f1.H), f1.R * (size / float(REF_SIZE))
    if has_text:
        bw, bh = 0.62 * W, 0.075 * S
        f.text_box = (W / 2.0 - bw / 2.0, f.text_y - 0.045 * S, W / 2.0 + bw / 2.0, f.text_y + 0.03 * S)
    else:
        f.text_box = None
    return f


# ----------------------------------------------------------------------------- the iris with the F3 feather
class Disc3:
    """The graded iris with the v3 feather. d: the fx Disc (tight uint8 square g, exact cx, cy, R, integer x0, y0).
    rgb / alpha: padded (T, T) arrays; the paste is out = rgb * alpha + canvas * (1 - alpha) at integer position, so
    wherever alpha is 1 (r <= 0.974 R) the output pixel IS the graded pixel."""
    __slots__ = ("d", "pad", "x0", "y0", "rgb", "alpha", "cx", "cy", "R", "iris", "index", "T")


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def make_disc3(d, span=None):
    """Build the padded F3 disc from an fx Disc. span: feather span in R (default F3_SPAN; the legacy 0.012 R feather is span 0.0197)."""
    span = F3_SPAN if span is None else span
    inner = 1.0 - span / 2.0
    g = d.g
    tgt = g.shape[0]
    R = d.R
    pad = int(math.ceil(0.03 * R)) + 1
    T = tgt + 2 * pad
    ax = (np.arange(T, dtype=np.float64) - pad + 0.5) - tgt / 2.0
    dx, dy = ax[None, :], ax[:, None]
    r = np.hypot(dx, dy)
    rho = r / R
    alpha = 1.0 - _smooth((rho - inner) / span)
    rgb = np.zeros((T, T, 3), np.float32)
    inside = slice(pad, pad + tgt)
    rgb[inside, inside] = g
    # the ring beyond 0.984 R is sampled radially from 0.981 R (bilinear): the limbal ring continues to 1.03 R
    ext = rho > 0.984
    ext &= alpha > 0.0
    if ext.any():
        rr = np.maximum(r[ext], 1e-9)
        k = (0.981 * R) / rr
        x = np.broadcast_to(dx, r.shape)[ext] * k + tgt / 2.0 - 0.5
        y = np.broadcast_to(dy, r.shape)[ext] * k + tgt / 2.0 - 0.5
        x0 = np.floor(x).astype(np.int64)
        y0 = np.floor(y).astype(np.int64)
        wx = (x - x0).astype(np.float32)[:, None]
        wy = (y - y0).astype(np.float32)[:, None]
        x0 = np.clip(x0, 0, tgt - 2)
        y0 = np.clip(y0, 0, tgt - 2)
        gf = g.astype(np.float32)
        a = gf[y0, x0] * (1 - wx) + gf[y0, x0 + 1] * wx
        b = gf[y0 + 1, x0] * (1 - wx) + gf[y0 + 1, x0 + 1] * wx
        rgb[ext] = a * (1 - wy) + b * wy
    o = Disc3()
    o.d, o.pad, o.T = d, pad, T
    o.x0, o.y0 = d.x0 - pad, d.y0 - pad
    o.rgb, o.alpha = rgb, alpha.astype(np.float32)
    o.cx, o.cy, o.R, o.iris, o.index = d.cx, d.cy, d.R, d.iris, d.index
    return o


FINISH_SIGMA_R = 0.00094      # declared finishing of the graded disc (AD cross-design fix): unsharp sigma in R units ...
FINISH_AMOUNT = 0.35         # ... amount, applied inside r <= 0.925 R only (ramp to 0 at 0.965 R). At 1024 px the sigma is 0.25 px: skipped.
FINISH_MIN_SIGMA = 0.45      # px: below this the finishing is skipped (the 1024 preview and every tile are untouched)


def finish_grade(g, R, enable=True):
    """The declared resampling finish of the graded tight disc (uint8 square). The restoration is a 1024 px file, so a 2048 or 4096 master
    enlarges it about 1.9x and the fibres come out soft: a fixed unsharp mask (sigma 0.00094 R, amount 0.35, inside 0.925 R) gives them
    their edge back. Deterministic, the same function builds the T1 reference (singles_tests), it is part of 'identical resampling'."""
    sig = FINISH_SIGMA_R * R
    if not enable or sig < FINISH_MIN_SIGMA:
        return g
    tgt = g.shape[0]
    gf = g.astype(np.float32)
    bl = C.blur(gf, sig)
    ax = (np.arange(tgt, dtype=np.float32) + 0.5) - np.float32(tgt / 2.0)
    rho = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / np.float32(R)
    w = (1.0 - C.smoothstep((rho - 0.925) / 0.04)).astype(np.float32)
    out = gf + (gf - bl) * (np.float32(FINISH_AMOUNT) * w)[..., None]
    np.clip(out, 0.0, 255.0, out=out)
    return np.ascontiguousarray(np.rint(out).astype(np.uint8))


def apply_limb(d3, mult=0.55, r0=0.955):
    """Zone B darkening of the graded iris (brief 1.1 rule 4: zone B may be multiplied down to 0.45): the dark limbal edge of the owner's
    H10 / H11 and of Kremer's pieces. Multiplier 1 at r0, `mult` at the limb and beyond (the feathered outer ring). Never touches r <= r0 (zone A)."""
    T, pad, R = d3.T, d3.pad, d3.R
    tgt = d3.d.g.shape[0]
    ax = (np.arange(T, dtype=np.float64) - pad + 0.5) - tgt / 2.0
    rho = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / R
    k = (1.0 - (1.0 - mult) * _smooth((rho - r0) / (1.0 - r0))).astype(np.float32)
    d3.rgb = d3.rgb * k[..., None]
    return d3


def place_iris(iris, frame, span=None, sharpen=True, limb=None):
    """Grade + snap the iris to whole pixels near the frame's circle, finish it (declared unsharp at masters), then build the F3 disc
    (optionally with the zone B limb darkening of the design)."""
    d = C.place_disc(iris, frame.cx, frame.cy, frame.R, 0)
    d.g = finish_grade(d.g, d.R, sharpen)
    d3 = make_disc3(d, span)
    if limb:
        apply_limb(d3, **limb)
    return d, d3


def paste_iris(img8, d3):
    """The LAST pixel operation on the 8-bit canvas, in place."""
    H, W = img8.shape[:2]
    T = d3.T
    xa, ya = max(0, d3.x0), max(0, d3.y0)
    xb, yb = min(W, d3.x0 + T), min(H, d3.y0 + T)
    if xa >= xb or ya >= yb:
        return img8
    s = (slice(ya - d3.y0, yb - d3.y0), slice(xa - d3.x0, xb - d3.x0))
    a = d3.alpha[s][..., None]
    reg = img8[ya:yb, xa:xb].astype(np.float32)
    reg *= 1.0 - a
    reg += d3.rgb[s] * a
    np.rint(reg, out=reg)
    np.clip(reg, 0, 255, out=reg)
    img8[ya:yb, xa:xb] = reg.astype(np.uint8)
    return img8


def sample_disc(d, rho, theta, stretch=1.0):
    """Bilinear RGB (0..1 float32, shape rho.shape + (3,)) of the graded iris at polar positions round its centre:
    rho in units of R, theta in radians (screen: clockwise, y down). Positions outside the tight square clamp."""
    g = d.g
    tgt = g.shape[0]
    rho = np.asarray(rho, np.float64)
    th = np.asarray(theta, np.float64)
    x = tgt / 2.0 + rho * d.R * np.cos(th) - 0.5
    y = tgt / 2.0 + rho * d.R * np.sin(th) - 0.5
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    wx = (x - x0).astype(np.float32)[..., None]
    wy = (y - y0).astype(np.float32)[..., None]
    x0c = np.clip(x0, 0, tgt - 2)
    y0c = np.clip(y0, 0, tgt - 2)
    gf = g
    a = gf[y0c, x0c] * (1 - wx) + gf[y0c, x0c + 1] * wx
    b = gf[y0c + 1, x0c] * (1 - wx) + gf[y0c + 1, x0c + 1] * wx
    return ((a * (1 - wy) + b * wy) / 255.0).astype(np.float32)


def radial_compress_im(im, cx, cy, R, e0=0.25, k=0.5, tile=None, knee=0.06):
    """Compress a plate radially beyond the lip: a point at distance e (R units beyond the limb) is drawn at g(e): identity below e0, slope k
    above it, the corner rounded over +-knee R (so the piecewise-bilinear mesh below stays exact to about 1 px). Flame tongues and sparks the
    image model made too tall. im: PIL image (uint8, 'L' or 'RGB') registered on the canvas; returns a PIL image. MESH transform on
    tile x tile quads (tile = R / 16, at least 16 px), bicubic."""
    W, H = im.size
    tile = int(max(16, round(R / 16.0))) if tile is None else int(tile)
    eg = np.linspace(-1.0, 4.0, 5001)
    x = eg - e0
    soft = np.where(x <= -knee, 0.0, np.where(x >= knee, x, (x + knee) ** 2 / (4.0 * knee)))
    gd = eg - (1.0 - k) * soft                                     # destination e for a source e
    xs = np.array(list(range(0, W, tile)) + [W], np.float64)
    ys = np.array(list(range(0, H, tile)) + [H], np.float64)
    gx, gy = np.meshgrid(xs, ys)
    dx, dy = gx - cx, gy - cy
    r = np.hypot(dx, dy)
    rho = np.maximum(r / R, 1e-9)
    e_dst = rho - 1.0
    e_src = np.interp(e_dst, gd, eg)
    f = np.where(e_dst > -0.999, (1.0 + e_src) / rho, 1.0)
    sx, sy = cx + dx * f, cy + dy * f
    mesh = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            mesh.append(((int(xs[i]), int(ys[j]), int(xs[i + 1]), int(ys[j + 1])),
                         (sx[j, i], sy[j, i], sx[j + 1, i], sy[j + 1, i], sx[j + 1, i + 1], sy[j + 1, i + 1], sx[j, i + 1], sy[j, i + 1])))
    return im.transform((W, H), Image.MESH, mesh, resample=Image.BICUBIC)


def radial_warp_im(im, cx, cy, R, scale_fn, e0=0.12, knee=0.05, tile=None):
    """Stretch a plate radially beyond the lip by an ANGLE-DEPENDENT factor: a point at source distance e (R beyond the limb) is drawn at
    e0 + (e - e0) m(theta) (identity below e0, the corner rounded over +-knee R). scale_fn(theta) -> m (theta: screen radians, clockwise,
    y down). Used for the crown's uneven spike height. MESH transform (tile R/16), bicubic; m is smooth so the quads stay exact to about 1 px."""
    W, H = im.size
    tile = int(max(16, round(R / 9.0))) if tile is None else int(tile)
    xs = np.array(list(range(0, W, tile)) + [W], np.float64)
    ys = np.array(list(range(0, H, tile)) + [H], np.float64)
    gx, gy = np.meshgrid(xs, ys)
    dx, dy = gx - cx, gy - cy
    r = np.hypot(dx, dy)
    rho = np.maximum(r / R, 1e-9)
    th = np.arctan2(dy, dx)
    m = np.asarray(scale_fn(th), np.float64)
    e_dst = rho - 1.0

    def soft(x):
        return np.where(x <= -knee, 0.0, np.where(x >= knee, x, (x + knee) ** 2 / (4.0 * knee)))

    def dsoft(x):
        return np.where(x <= -knee, 0.0, np.where(x >= knee, 1.0, (x + knee) / (2.0 * knee)))
    e_src = e_dst.copy()
    for _ in range(8):                                               # invert e_dst = e_src - (1 - m) soft(e_src - e0) by Newton (f' >= m > 0)
        f = e_src - (1.0 - m) * soft(e_src - e0) - e_dst
        fp = 1.0 - (1.0 - m) * dsoft(e_src - e0)
        e_src = e_src - f / np.maximum(fp, 1e-3)
    f = np.where(e_dst > -0.999, (1.0 + e_src) / rho, 1.0)
    sx, sy = cx + dx * f, cy + dy * f
    mesh = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            mesh.append(((int(xs[i]), int(ys[j]), int(xs[i + 1]), int(ys[j + 1])),
                         (sx[j, i], sy[j, i], sx[j + 1, i], sy[j + 1, i], sx[j + 1, i + 1], sy[j + 1, i + 1], sx[j, i + 1], sy[j, i + 1])))
    return im.transform((W, H), Image.MESH, mesh, resample=Image.BICUBIC)


def radial_compress(arr, cx, cy, R, e0=0.25, k=0.5, tile=None):
    """radial_compress_im for a float32 0..1 array (kept for callers that hold arrays)."""
    mode = "L" if arr.ndim == 2 else "RGB"
    im = Image.fromarray((np.clip(arr, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), mode)
    return np.asarray(radial_compress_im(im, cx, cy, R, e0, k, tile), np.float32) / 255.0


# ----------------------------------------------------------------------------- colour helpers
LUMW = np.array([0.299, 0.587, 0.114], np.float32)


def lum(rgb):
    return np.asarray(rgb, np.float32) @ LUMW


_H2 = C.BoundedCache(64)


def secondary_hue(iris):
    """(rgb 0..1 accent colour, how) : H2 of the brief. The collarette median (0.35-0.55 R of the canonical grade) when it
    is more than dE00 12 from the ring median, else the analogous hue +25 deg of the ring. The returned colour is lifted
    to a light, clean accent (L* 80, C* limited), never a new hue family."""
    key = iris.digest
    got = _H2.get(key)
    if got is not None:
        return got
    fr = iris.graded(C.REF_SIDE)
    sq, tgt = C._tight(fr)
    R = tgt / 2.0
    ax = np.arange(tgt) + 0.5 - R
    rho = np.hypot(ax[None, :], ax[:, None]) / R
    m = (rho > 0.35) & (rho < 0.55)
    px = sq[m].astype(np.float64)
    lab = L.srgb_to_lab(px)
    med = np.median(lab, 0)
    ringm = iris.ring.mean(0).astype(np.float64)
    ring_lab = L.srgb_to_lab((ringm * 255.0)[None, :])[0]
    de = float(L.ciede2000(med[None, :], ring_lab[None, :])[0])
    Cc = float(np.hypot(med[1], med[2]))
    hh = float(np.degrees(np.arctan2(med[2], med[1])) % 360.0)
    st = iris.stats
    if de > 12.0 and Cc > 8.0:
        how = "collarette"
        h2 = hh
        c2 = min(max(Cc * 1.15, 20.0), 52.0)
    else:
        how = "analogous"
        h2 = (st["h"] + 25.0) % 360.0
        c2 = min(max(st["C"] * 1.1, 18.0), 50.0)
    rgb = C.from_lch(80.0, c2, h2).astype(np.float32)
    return _H2.put(key, (rgb, how, h2))


def soft_knee(Cc, knee=48.0, room=16.0):
    return np.where(Cc > knee, knee + room * np.tanh((Cc - knee) / room), Cc)


PLATINUM = np.stack([C.rgb01(h) for h in ("#2F4460", "#9FB6CF", "#F3F6FF")])
COPPER_DEEP = C.rgb01("#5A230E")
COPPER = {"lift": 1.8, "sat": 1.5, "toward": "#D98A3D", "t": 0.35}
WHITE_HOT = C.rgb01("#FFF4E0")


def colour_weights(iris, hue_deg=0.0):
    st = iris.stats
    Cm, hm = st["C"], (st["h"] + hue_deg) % 360.0
    dark = st["class"] == "dark_brown"
    w_grey = 0.0 if dark else float(_smooth((16.0 - Cm) / 8.0))
    w_ol = 0.0 if dark else float(_smooth((Cm - 20.0) / 10.0) * _smooth((hm - 87.0) / 8.0) * _smooth((133.0 - hm) / 8.0))
    return w_grey, w_ol, dark


def ramp_stops(iris, hue_deg=0.0):
    """(3, 360, 3) float32: deep, mid, hot colour per ring angle. deep = darker, richer, hue -10; mid = the boosted own ring
    (dark brown: copper, grey: platinum ice); hot = 55 % toward warm white. Olive and yellow eyes never turn sulfur."""
    w_grey, w_ol, dark = colour_weights(iris, hue_deg)
    mid = C.effect_palette(iris.ring, 1.45, 1.35, {"dark_brown": COPPER}, cls=iris.stats["class"], hue_deg=hue_deg)
    Ls, Cc, h = C.lch(mid)
    Ls = Ls - w_ol * np.maximum(Ls - 70.0, 0.0)
    Cs = soft_knee(Cc, 48.0 - 12.0 * w_ol)
    mid = C.from_lch(Ls, Cs, h)
    deep = C.from_lch(np.maximum(Ls - 28.0, 6.0), soft_knee(Cs * 1.0, 32.0, 8.0), h - 4.0 + 12.0 * w_ol)      # no red shadows in thin dust (copper eyes)
    hot = C.mix(C.from_lch(Ls, Cs, h - 15.0 * w_ol), WHITE_HOT[None, :], 0.55)
    if dark:
        deep = C.mix(deep, COPPER_DEEP[None, :], 0.6)
    st = np.stack([deep, mid, hot]).astype(np.float32)
    if w_grey > 0:
        st = st * (1.0 - w_grey) + PLATINUM[:, None, :] * w_grey
    return st.astype(np.float32)


# ----------------------------------------------------------------------------- memory discipline (row bands)
BAND = 256


def bands(H, step=BAND):
    for r0 in range(0, H, step):
        yield r0, min(H, r0 + step)


def fill_radial_bg(cv, cx, cy, radius, inner, outer, power=1.0):
    """cv[:] = fx.core.radial_bg(...) computed in row bands (no second full canvas)."""
    H, W = cv.shape[:2]
    a, b = C.rgb01(inner), C.rgb01(outer)
    x = (np.arange(W, dtype=np.float32) + np.float32(0.5 - cx))[None, :]
    for r0, r1 in bands(H):
        y = (np.arange(r0, r1, dtype=np.float32) + np.float32(0.5 - cy))[:, None]
        t = np.clip(np.sqrt(x * x + y * y) / np.float32(radius), 0, 1)
        t = (t * t * (3 - 2 * t)) ** power
        cv[r0:r1] = a[None, None, :] + (b - a)[None, None, :] * t[..., None]
    return cv


def tone_map_bands(cv, knee=C.KNEE, whiten=C.WHITEN):
    """fx.core.tone_map is pointwise: applying it per row band gives the same pixels with far fewer temporaries."""
    for r0, r1 in bands(cv.shape[0]):
        C.tone_map(cv[r0:r1], knee, whiten)
    return cv


def place_u8(pick, W, H, cx, cy, R, r_scale=1.0, edge_fade=0.05):
    """fx plate registration (registry.Plate.place) returning the PIL image (uint8, 'L' or 'RGB') instead of a float32 array: a 4096 RGB float
    plate is 200 MB and its conversion doubles that.  The resampling is ONE anti-aliased LANCZOS resize of the (mirrored, rotated) plate window
    onto the canvas (PIL `box`, sub-pixel exact), so a plate reduced to a 1024 preview and the same plate at a 4096 master are the same picture
    (the registry's bicubic affine aliased speckle and drops below 0.7 x: the SSIM of round 1). Registration is identical: the plate's fitted
    void circle lands on the circle (cx, cy, R x r_scale). Returns (PIL image, info)."""
    from PIL import ImageOps
    plate = pick.plate
    R_ = float(R) * float(r_scale)
    vcx, vcy, vr = plate.void
    chosen, sc = None, None
    for lod in ("1k", "4k"):
        side = plate.side(lod)
        s_l = R_ / (vr * side)
        if s_l <= RG.MAX_UPSCALE or lod == "4k":
            chosen, sc = lod, s_l
            break
    if sc > RG.MAX_UPSCALE + 1e-9:
        raise RG.ResolutionError(f"{plate.id}: void radius {R_:.0f} px needs x{sc:.2f} of the {chosen} plate")
    im = plate.image(chosen)
    side = im.size[0]
    cx_s, cy_s = vcx * side, vcy * side
    if pick.mirror:
        im = ImageOps.mirror(im)
        cx_s = side - cx_s
    if edge_fade and edge_fade > 0:
        a = np.array(im)                                              # uint8 copy; only the border strips are touched (same numbers as registry)
        ramp = np.clip(np.minimum(np.arange(side) + 0.5, side - np.arange(side) - 0.5) / (edge_fade * side), 0, 1)
        ramp = (ramp * ramp * (3 - 2 * ramp)).astype(np.float32)
        e = int(math.ceil(edge_fade * side)) + 1
        for rows in (slice(0, e), slice(side - e, side)):              # top and bottom strips: the whole row width
            m = ramp[rows, None] * ramp[None, :]
            a[rows] = (a[rows] * (m if a.ndim == 2 else m[..., None]) + 0.5).astype(np.uint8)
        for cols in (slice(0, e), slice(side - e, side)):              # left and right strips (rows between the strips)
            m = ramp[e:side - e, None] * ramp[None, cols]
            a[e:side - e, cols] = (a[e:side - e, cols] * (m if a.ndim == 2 else m[..., None]) + 0.5).astype(np.uint8)
        im = Image.fromarray(a)
    if abs(pick.rotation_deg) > 0.01:                                  # CCW on screen about the void centre, at plate resolution (no scale change)
        im = im.rotate(pick.rotation_deg, resample=Image.BICUBIC, center=(cx_s, cy_s), fillcolor=0 if im.mode == "L" else (0, 0, 0))
    # canvas rectangle the plate covers: x_out = cx + (x_plate - cx_s) * sc
    ox0 = max(0, int(math.ceil(cx + (0.0 - cx_s) * sc)))
    oy0 = max(0, int(math.ceil(cy + (0.0 - cy_s) * sc)))
    ox1 = min(int(W), int(math.floor(cx + (side - cx_s) * sc)))
    oy1 = min(int(H), int(math.floor(cy + (side - cy_s) * sc)))
    out = Image.new(im.mode, (int(W), int(H)), 0 if im.mode == "L" else (0, 0, 0))
    if ox1 > ox0 and oy1 > oy0:
        box = (cx_s + (ox0 - cx) / sc, cy_s + (oy0 - cy) / sc, cx_s + (ox1 - cx) / sc, cy_s + (oy1 - cy) / sc)
        box = (max(0.0, box[0]), max(0.0, box[1]), min(float(side), box[2]), min(float(side), box[3]))
        part = im.resize((ox1 - ox0, oy1 - oy0), Image.LANCZOS, box=box)
        out.paste(part, (ox0, oy0))
    return out, {"lod": chosen, "scale": sc, "upscale": max(1.0, sc), "src_px": side, "rotation_deg": pick.rotation_deg,
                 "mirror": bool(pick.mirror)}


def _rank1d(a, k, axis, fn):
    """Running min / max (fn = np.minimum / np.maximum) of window k along an axis of a 2-D array, edges replicated: k-1 shifted views, no O(k^2) filter."""
    r = k // 2
    n = a.shape[axis]
    pad = [(0, 0), (0, 0)]
    pad[axis] = (r, r)
    ap = np.pad(a, pad, mode="edge")
    sl = [slice(None), slice(None)]
    sl[axis] = slice(0, n)
    out = ap[tuple(sl)].copy()
    for i in range(1, k):
        sl[axis] = slice(i, i + n)
        fn(out, ap[tuple(sl)], out=out)
    return out


def opening_lum(im, S):
    """(L, opened): the 8-bit luminance of a plate image (PIL L / RGB) and its morphological opening (min then max over a square window of
    2 round(0.0008 S) + 1 px: 3 at 1024, 7 at 4096, the same physical size), as uint8 arrays. What the opening removes is the plate's speckle
    ((L - opened) / L of a pixel); a design thins it by scaling the pixel by 1 - speck x (1 - keep). Separable numpy passes (PIL's rank filter is
    O(k^2): 13 s at 4096)."""
    k = 2 * int(round(0.0008 * S)) + 1
    L8 = np.asarray(im if im.mode == "L" else im.convert("L"))
    op = _rank1d(_rank1d(L8, k, 1, np.minimum), k, 0, np.minimum)          # erosion
    op = _rank1d(_rank1d(op, k, 1, np.maximum), k, 0, np.maximum)           # dilation
    return L8, op


def speck_keep(a, L8, op8, r0, r1, keep):
    """Rows r0:r1 of a plate band a (h, W, 3) float 0..1 with its speckle scaled by keep (h, W): out = a x (1 - s (1 - keep)), s = the share of the
    pixel's luminance that the opening removed."""
    lb = L8[r0:r1].astype(np.float32)
    ob = op8[r0:r1].astype(np.float32)
    sp = np.clip((lb - ob) / np.maximum(lb, 1.0), 0.0, 1.0)
    return a * (1.0 - sp * (1.0 - keep))[..., None]


def opening(im, S):
    """The morphological opening of a plate image (PIL uint8 L / RGB): min then max filter with a kernel of 2 round(0.0008 S) + 1 px (3 at 1024, 7 at
    4096, the same physical size). What the opening removes is the plate's speckle (image - opening), which a design can thin out."""
    from PIL import ImageFilter
    k = 2 * int(round(0.0008 * S)) + 1
    return im.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))


def tophat_split(im, S):
    """(structure, specks) of a plate image (PIL uint8): structure = a morphological opening (min then max filter, kernel 2 round(0.0008 S) + 1 px:
    3 at 1024, 7 at 4096), specks = image - structure (what is smaller than the kernel: the plate's speckle). Both float32 0..1 arrays."""
    from PIL import ImageFilter
    k = 2 * int(round(0.0008 * S)) + 1
    op = im.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    a = np.asarray(im, np.float32) / 255.0
    b = np.asarray(op, np.float32) / 255.0
    return b, np.maximum(a - b, 0.0)


def u8_band(im, r0, r1):
    """float32 0..1 rows r0:r1 of a PIL uint8 image: (h, W) for 'L', (h, W, 3) for 'RGB'."""
    a = np.asarray(im.crop((0, r0, im.size[0], r1)), np.float32)
    a *= np.float32(1.0 / 255.0)
    return a


# ----------------------------------------------------------------------------- the effect context
class _Cap:
    mode = "none"
    top = 0.0


class _Lay:
    caption = _Cap()
    key = ""
    aspect = "1:1"


class MCtx:
    """What an effect function receives (a duck-typed fx.core.Ctx): W, H, S, wall, stretch, discs (fx Discs with exact
    cx, cy, R), irises, seed, pv, frozen, opts, rand(tag, eye), grid(), count(). The effect draws into the float canvas only.
    seed: the seed of the artwork (api/_lib/styles/seeds.py: the eye ids and the plan's seed key, WP5B); pv: the plates version a plate pick takes;
    frozen: the choices the plan fixed before the render (the liquid of a splash), which an effect reads before it measures the eye."""

    def __init__(self, frame, d, iris, style, opts=None, seed=None, pv=None, frozen=None):
        self.frame = frame
        self.W, self.H, self.S = frame.W, frame.H, frame.S
        self.wall = frame.wall
        self.discs = [d]
        self.irises = [iris]
        self.style = style
        self.opts = dict(opts or {})
        lay = _Lay()
        lay.aspect = frame.fmt
        lay.key = frame.key
        self.layout = lay
        if seed is None:
            raise ValueError("an effect context needs the seed of its artwork (api/_lib/styles/seeds.py)")
        self.seed = int(seed)
        self.pv = pv
        self.frozen = dict(frozen or {})
        self.eye_seeds = [self.seed]
        self.stretch = 1.0
        self.caption_accent = None
        self.text_box = frame.text_box
        self.post = []                      # callables(img8) run right AFTER the iris paste (zone B veils only, see rim_veil)
        self.log = {}                       # design facts for the tests and the boards (wind, plates, palettes ...)

    def rand(self, tag, eye=None):
        return C.Rand(self.seed, tag)

    def grid(self, feature_px, min_px=1.5, max_f=8):
        return C.Grid(self.W, self.H, C.work_factor(feature_px, min_px, max_f))

    def count(self, density):
        return C.particle_count(density, self.W, self.H)

    def fade_caption(self, light, floor=0.25):
        return light


def text_fade(arr, ctx, y0=0, x0=0, floor=0.15):
    """Matter density masked to <= 15 % inside the text box + 0.02 S (brief 1.5.7), soft edges 0.02 S. arr: (h, w[, 3]) window of the canvas
    whose first row / column are y0 / x0. No text -> untouched."""
    tb = ctx.text_box
    if tb is None:
        return arr
    S = ctx.S
    m = 0.02 * S
    soft = 0.02 * S
    h, w = arr.shape[:2]
    ys = np.arange(y0, y0 + h, dtype=np.float32) + np.float32(0.5)
    xs = np.arange(x0, x0 + w, dtype=np.float32) + np.float32(0.5)

    def box(v, lo, hi):
        a = (v - np.float32(lo - m - soft)) / np.float32(soft)
        b = (np.float32(hi + m + soft) - v) / np.float32(soft)
        return C.smoothstep(a) * C.smoothstep(b)
    vy = box(ys, tb[1], tb[3])
    hx = box(xs, tb[0], tb[2])
    if not (vy.any() and hx.any()):
        return arr
    k = (1.0 - (1.0 - floor) * vy[:, None] * hx[None, :]).astype(np.float32)
    arr *= (k[..., None] if arr.ndim == 3 else k)
    return arr


def edge_fade(arr, ctx, y0=0, x0=0, width=0.035):
    """Matter fades over the last `width` S toward the canvas edge (brief 3.0.4: an artwork must not look cropped). arr: (h, w[, 3]) window at row y0."""
    h, w = arr.shape[:2]
    W, H, S = ctx.W, ctx.H, ctx.S
    ys = np.arange(y0, y0 + h, dtype=np.float32) + np.float32(0.5)
    xs = np.arange(x0, x0 + w, dtype=np.float32) + np.float32(0.5)
    ex = C.smoothstep(np.minimum(xs, W - xs) / np.float32(width * S))
    ey = C.smoothstep(np.minimum(ys, H - ys) / np.float32(width * S))
    k = (ey[:, None] * ex[None, :]).astype(np.float32)
    arr *= (k[..., None] if arr.ndim == 3 else k)
    return arr


def wall_fade(light, ctx, top=0.35, y0=0):
    """Wallpaper only: matter above 0.20 H (the lock-screen clock) fades to `top` strength, below 0.94 H to 60 %.
    y0: the canvas row of light's first row when light is a window of the canvas."""
    if not ctx.wall:
        return light
    H = ctx.H
    y = (np.arange(H, dtype=np.float32) + 0.5) / np.float32(H)
    fz = (top + (1.0 - top) * C.smoothstep((y - 0.08) / 0.14)) * (1.0 - 0.4 * C.smoothstep((y - 0.86) / 0.10))
    fz = fz[y0:y0 + light.shape[0]]
    light *= (fz[:, None, None] if light.ndim == 3 else fz[:, None]).astype(np.float32)
    return light


# ----------------------------------------------------------------------------- the render pipeline
class Result:
    __slots__ = ("img", "frame", "d", "d3", "ctx", "log", "times", "img8_noText", "info")


def render_single(effect, iris, design, fmt="1:1", size=1024, names="", date="", bg=C.BG, name_colour=None, knee=C.KNEE,
                  whiten=C.WHITEN, opts=None, times=None, limb=None, seed=None, pv=None, frozen=None):
    """One artwork: frame -> place + grade the iris -> canvas (bg) -> effect(cv, ctx) -> tone map -> dither -> iris pasted
    LAST (F3) -> the customer's names. effect None draws nothing (Clean). Returns a Result."""
    t0 = time.perf_counter()
    has_text = bool((names or "").strip() or (date or "").strip())
    frame = frame_for(design, fmt, size, has_text)
    g0 = iris.grade_seconds
    span = None                                                  # the F3 feather (the round 1 feather option is gone)
    o_ = opts or {}
    lb = o_.get("limb", limb)
    d, d3 = place_iris(iris, frame, span, sharpen=o_.get("sharpen", True), limb=(lb if lb else None))
    iris.ring
    t1 = time.perf_counter()
    ctx = MCtx(frame, d, iris, design, opts, seed=seed, pv=pv, frozen=frozen)
    cv = C.canvas(frame.W, frame.H, bg)
    if effect is not None:
        effect(cv, ctx)
    t2 = time.perf_counter()
    tone_map_bands(cv, knee, whiten)
    img8 = C.dither_quantize(cv, ctx.seed)
    del cv
    paste_iris(img8, d3)
    for f in ctx.post:                      # zone B only (r >= 0.955 R), never zone A: the tests check it
        f(img8)
    t3 = time.perf_counter()
    img = Image.fromarray(img8)
    acc = name_colour or (NAME_GOLD if design == "gold" else NAME_WARM)
    log = draw_names(img, frame, names, date, acc)
    t4 = time.perf_counter()
    r = Result()
    r.img, r.frame, r.d, r.d3, r.ctx, r.log = img, frame, d, d3, ctx, log
    g = iris.grade_seconds - g0
    r.times = {"grade": round(g, 3), "place": round(t1 - t0 - g, 3), "effect": round(t2 - t1, 3), "finish": round(t3 - t2, 3),
               "text": round(t4 - t3, 3), "total": round(t4 - t0, 3), "render_without_grade": round(t4 - t0 - g, 3)}
    if times is not None:
        times.update(r.times)
    r.img8_noText = None
    r.info = {"design": design, "fmt": fmt, "size": size, "seed": ctx.seed, "class": iris.cls}
    return r
