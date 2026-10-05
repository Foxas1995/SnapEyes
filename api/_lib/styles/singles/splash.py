# -*- coding: utf-8 -*-
"""designs.singles_splash: SPLASH, brief 3.7.1 (scratch prototype).

A photographed liquid crown (P-SP-CROWN keeper, the liquid chosen by the eye's class and hue) registered so that its liquid lip
lands on the limb (0.97-1.05 R), the tallest spikes turned toward 60-120 deg, the liquid's hue leaning to the eye's own colour by at most
15 deg (per ring angle), speculars kept neutral white, the lip and the drops near the iris leaning to the secondary hue H2, plus 6-12
extra droplet sprites (P-SP-DROPS) at 1.3-1.8 R.  The iris is pasted last with the F3 feather, so the lip meets it under a soft edge
(zone B, D1) and the iris never looks like a sticker on a template.
Liquids:  blue / grey -> water_clear, blue-green -> water_teal, green / olive -> tea_olive, amber / light brown / hazel-gold -> whisky_amber,
dark brown -> cognac.
Hard rules: no pixel of a visible iris with r <= 0.95 R is touched (paste last); colours from the plate's own physical colour shifted <= 15 deg
toward C(theta); seeds from sha256; sizes in R and S; numpy + PIL only.
"""
from __future__ import annotations

# PORT of work package WP5A (step A): singles_splash.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists
# (imports, plates, the drops atlas read through atlas.py); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures.
# WP5B (step B) changed the seed and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import math
import hashlib

import numpy as np
from PIL import Image

from .. import atlas as AT
from .. import core as C
from .. import plates as RG
from . import kit as K

TWO_PI = 2.0 * math.pi
F32 = np.float32
SP = {
    "lip_scale": 0.975,        # the plate's void circle lands at 0.975 R: the lip's inner edge sits under the iris's F3 feather
    "hue_max": 15.0,           # deg
    "h2_lean": 0.22,           # share of the near-lip liquid pulled toward H2
    "drops": 9,                # extra droplet sprites (6-12)
    "wind_lo": 62.0, "wind_hi": 118.0,
    "gain": 1.0,
    "spike_warp": 0.30,        # AD: spike height m(theta) = 1 + 0.30 cos(theta - wind) on the short side (x0.70) ...
    "spike_tall": 0.08,        # ... and x1.20 on the tall side (x1.35 put the tips of the tall spikes on the canvas edge at 1:1)
    "cut_spikes": 2,           # AD: 15-20 % of the short side's spikes dropped (two sectors)
    "speck_gain": 0.85,
}


def registry():
    return RG


def _hash(seed, *parts):
    return int.from_bytes(hashlib.sha256(("|".join([str(seed)] + [str(p) for p in parts])).encode()).digest()[:8], "big")


def liquid_for(iris):
    """The liquid family of one eye by class and hue (brief 3.7.1)."""
    return liquid_from_stats(iris.stats)


def liquid_from_stats(st):
    """liquid_for() of the numbers alone: st is the eye's colour_stats (class, h, C), measured on the iris or read from its sealed profile (the plan
    fixes the liquid from the profile, so that the preview and the master draw the plate the plan names)."""
    if st["class"] == "dark_brown":
        return "cognac"
    h, c = st["h"], st["C"]
    if st["class"] == "grey" or c < 13.0:
        return "water_clear"
    if 245.0 <= h <= 300.0 or h < 5.0 and False:
        return "water_clear"
    if 160.0 <= h < 245.0:
        return "water_teal" if h < 178.0 else "water_clear"       # AD: a blue-grey eye (hue 178-245, own215120 is 191) gets clear water with a cool tint, not teal
    if 100.0 <= h < 160.0:
        return "tea_olive"
    return "whisky_amber"


def hue_shift_plate(rgb, delta_deg_lut, th, strength=1.0):
    """Rotate the chroma of an RGB plate (H, W, 3) 0..1 by delta(theta) degrees (per pixel angle, LUT over the ring bins), in YIQ. Only the
    pixels that carry light (max channel > 0.004) are computed: most of a plate is black."""
    out = np.zeros_like(rgb)
    m = rgb.max(-1) > 0.004
    if not m.any():
        return out
    px = rgb[m]
    idx = C.angle_index(th[m])
    delta = -np.radians(delta_deg_lut[idx]).astype(np.float32) * F32(strength)      # YIQ rotates red -> magenta; LCh hue runs red -> yellow
    r, g, b = px[:, 0], px[:, 1], px[:, 2]
    Y = 0.299 * r + 0.587 * g + 0.114 * b
    I = 0.5959 * r - 0.2746 * g - 0.3213 * b
    Q = 0.2115 * r - 0.5227 * g + 0.3112 * b
    cs, sn = np.cos(delta), np.sin(delta)
    I2 = I * cs - Q * sn
    Q2 = I * sn + Q * cs
    o = np.empty_like(px)
    o[:, 0] = Y + 0.9563 * I2 + 0.6210 * Q2
    o[:, 1] = Y - 0.2721 * I2 - 0.6474 * Q2
    o[:, 2] = Y - 1.1070 * I2 + 1.7046 * Q2
    np.clip(o, 0.0, 1.0, out=o)
    out[m] = o
    return out


def _plate_hue(rgb_small):
    """Mean hue (deg, LCh) of the coloured part of a plate."""
    a = rgb_small.reshape(-1, 3)
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    m = (lum > 0.10) & (lum < 0.80)
    if m.sum() < 100:
        return 0.0, 0.0
    lab = C.L.srgb_to_lab(a[m][::7].astype(np.float64) * 255.0)
    return float(np.degrees(np.arctan2(lab[:, 2].mean(), lab[:, 1].mean())) % 360.0), float(np.hypot(lab[:, 1].mean(), lab[:, 2].mean()))


def _ring_hue_lut(iris):
    """(360,) hue of the eye's own ring colour per angle (deg, LCh) in the fx convention (bin k = k deg clockwise)."""
    ring = iris.ring
    _, cc, h = C.lch(ring)
    return np.asarray(h, np.float64), np.asarray(cc, np.float64)


def in_text_box(ctx, x, y, pad=0.0):
    """True when the canvas point (x, y) lies inside the customer's text box (+ the brief's 0.02 S margin + pad): sprites are not placed there (matter density <= 15 % inside it)."""
    tb = getattr(ctx, "text_box", None)
    if tb is None:
        return False
    m = 0.02 * ctx.S + pad
    return (tb[0] - m) < x < (tb[2] + m) and (tb[1] - m) < y < (tb[3] + m)


def blit_sprite(cv, im, x, y, size_px, gain=0.9):
    """Add an RGB sprite (float 0..1, on black) of longest side size_px centred at canvas (x, y) into cv (screen-like add). The sprite is reduced to
    its size by an anti-aliased LANCZOS resize and then placed with a sub-pixel affine shift (bicubic, scale corrected to the exact size), so a droplet sits
    on its exact position at every canvas size: a 1024 preview and a 4096 master draw the same drop (integer placement was the main p99 dE00 of round 2c)."""
    H, W = cv.shape[:2]
    h_, w_ = im.shape[:2]
    k = size_px / max(h_, w_)
    nh, nw = max(3, int(round(h_ * k))), max(3, int(round(w_ * k)))
    u8 = (np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8)
    small = Image.fromarray(u8).resize((nw, nh), Image.LANCZOS)
    ow, oh = nw + 4, nh + 4
    x0, y0 = int(math.floor(x - ow / 2.0)), int(math.floor(y - oh / 2.0))
    fx, fy = x - ow / 2.0 - x0, y - oh / 2.0 - y0
    sx, sy = (w_ * k) / nw, (h_ * k) / nh                        # exact size / resized size (close to 1)
    a, e_ = 1.0 / sx, 1.0 / sy
    c = nw / 2.0 - (ow / 2.0 + fx) * a
    f = nh / 2.0 - (oh / 2.0 + fy) * e_
    out = np.asarray(small.transform((ow, oh), Image.AFFINE, (a, 0.0, c, 0.0, e_, f), resample=Image.BICUBIC), np.float32) / 255.0
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + ow), min(H, y0 + oh)
    if xa >= xb or ya >= yb:
        return False
    cv[ya:yb, xa:xb] += out[ya - y0:yb - y0, xa - x0:xb - x0] * F32(gain)
    return True


def droplet_images(seed, n):
    """n droplet sprites (float32 RGB 0..1 on black, cropped) from the offline atlas of the P-SP-DROPS sheets (139 sprites, 128 px), in a
    deterministic sha256 order: no plate decode and no component labelling at render time."""
    drops = AT.drops()
    N = len(drops)
    order = sorted(range(N), key=lambda i: _hash(seed, "drop", i))[:n]
    out = []
    for i in order:
        a = drops[i].astype(np.float32) / 255.0
        m = a.max(-1) > 0.03
        ys, xs = np.nonzero(m)
        out.append(a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else a)
    return out


def crown_tint(iris):
    """(3,) multiplier of a CLEAR-water plate for a coloured eye: 35 % of the eye's own ring colour (luminance-normalised), so the water of a
    blue-grey eye is a cool clear, not the neutral grey of the plate and not the teal of a green eye. A colourless eye gets 1."""
    if iris.stats["class"] == "grey" or iris.stats["C"] < 13.0:
        return np.ones(3, np.float32)
    med = np.median(np.asarray(iris.ring, np.float32), axis=0)
    lum = float(med @ np.array([0.299, 0.587, 0.114], np.float32))
    c = med / max(lum, 1e-3)
    return (0.65 + 0.35 * c).astype(np.float32)


def crown_pick(seed, liquid, pv=None, opts=None):
    """(the screen angle the crown's tall side is wanted at, the Pick): the crown plate of one splash, from the artwork's seed, the liquid and the
    plates version of the spec. No pixels: resolve() calls it to name the plate before the render, and the render calls it to draw."""
    o = dict(SP)
    o.update(opts or {})
    wanted = o["wind_lo"] + (o["wind_hi"] - o["wind_lo"]) * float(C.Rand(seed, "splash").uniform())
    return wanted, registry().pick("P-SP-CROWN", seed, wanted_strong_angle=wanted, max_rotation=30.0, liquid=liquid, pv=pv)


def fx_splash(cv, ctx):
    opts = dict(SP)
    opts.update(ctx.opts.get("splash", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    reg = registry()
    liquid = ctx.opts.get("liquid") or ctx.frozen.get("liquid") or liquid_for(iris)
    wanted, pk = crown_pick(ctx.seed, liquid, ctx.pv, opts)
    # background: #050505 with a 3 % radial lift inside 1.6 R
    K.fill_radial_bg(cv, d.cx, d.cy, 1.6 * R, "#0B0B0C", "#050505")
    lip = min(opts["lip_scale"], 1.045 * pk.plate.void_diam * 4096.0 / (2.0 * 0.255 * 4096.0))       # plate upscale at 4096 <= x1.045 (AD: x1.05)
    plate_im, pinfo = K.place_u8(pk, W, H, d.cx, d.cy, R, r_scale=lip, edge_fade=0.05)
    # uneven crown (AD: a near-perfect ring of equal spikes is the preset tell): the spike height follows m(theta) = 1 + a cos(theta - wind),
    # tall side x(1 + a), short side x(1 - a); a few spikes of the short side are dropped
    wind = -math.radians(wanted)                                        # screen angle (clockwise, y down) of the tall side
    amp = float(opts["spike_warp"])
    amp_t = float(opts["spike_tall"])
    if amp > 0:
        plate_im = K.radial_warp_im(plate_im, d.cx, d.cy, R, lambda th: 1.0 + np.where(np.cos(th - wind) > 0, amp_t, amp) * np.cos(th - wind), e0=0.14)
    rs_ = ctx.rand("spikes")
    n_cut = 0 if opts["cut_spikes"] <= 0 else int(opts["cut_spikes"])
    cuts = []
    for k in range(n_cut):
        c = wind + math.pi + float(rs_.uniform(1, -0.85, 0.85)[0]) + (k - (n_cut - 1) / 2.0) * 0.55
        cuts.append((c, math.radians(float(rs_.uniform(1, 5.0, 8.0)[0]))))
    # specks: the plate's own speckle is kept but thinned: density x exp(-e / 0.8 R), none within 0.15 R of the lip, none beyond 1.9 R,
    # clustered by a low-frequency angular noise (AD: a uniform speck field reads as a starfield)
    L8, op8 = K.opening_lum(plate_im, S)
    n_th = C.periodic_fbm1d(512, ctx.rand("specknoise"), 3, base=5)
    # hue: rotate the liquid's chroma toward the eye's own hue at each ring angle, at most hue_max
    small = np.asarray(plate_im)[::4, ::4].astype(np.float32) / 255.0
    ph, pc = _plate_hue(small)
    hr, cr = _ring_hue_lut(iris)
    delta = ((hr - ph + 180.0) % 360.0) - 180.0
    delta = np.where(np.abs(delta) <= 90.0, np.clip(delta, -opts["hue_max"], opts["hue_max"]), 0.0)
    if iris.stats["class"] == "grey" or iris.stats["C"] < 13.0:
        delta = delta * 0.0                                  # a colourless eye keeps a colourless liquid
    delta_lut = C.angular_lut(delta)
    h2, h2how, _ = K.secondary_hue(iris)
    h2a = np.asarray(h2, np.float32)
    tint = crown_tint(iris) if liquid == "water_clear" else np.ones(3, np.float32)
    w3 = np.array([0.299, 0.587, 0.114], np.float32)
    for r0, r1 in K.bands(H):                                # row bands: a 4096 RGB plate is 200 MB, its temporaries 4x that
        rho, th = C.polar(W, H, d.cx, d.cy, R, 1.0, (0, r0, W, r1))
        e = rho - 1.0
        a = K.u8_band(plate_im, r0, r1)
        thm = (th % TWO_PI) / TWO_PI
        nz = n_th[np.minimum((thm * 512).astype(np.int32), 511)]
        wsp = np.exp(-e / 0.8) * C.smoothstep((e - 0.15) / 0.10) * (1.0 - C.smoothstep((e - 1.65) / 0.25)) * (0.25 + 0.75 * nz) * opts["speck_gain"]
        lipk = 1.0 - C.smoothstep((e - 0.10) / 0.04)                      # the lip's own texture (e < 0.10 R) is never opened: its fine lines are the liquid, not speckle
        wsp = lipk + (1.0 - lipk) * wsp
        liq_in = K.speck_keep(a, L8, op8, r0, r1, wsp.astype(np.float32))
        for c_, hw_ in cuts:                                   # dropped spikes of the short side (beyond the lip only)
            dth = np.abs((th - c_ + math.pi) % TWO_PI - math.pi)
            k_ = C.smoothstep((dth - hw_ * 0.6) / (hw_ * 0.5)) + (1.0 - C.smoothstep((e - 0.10) / 0.06))
            liq_in = liq_in * np.minimum(k_, 1.0)[..., None].astype(np.float32)
        liq = hue_shift_plate(liq_in, delta_lut, th)
        if liquid == "water_clear":
            liq = liq * tint[None, None, :]
        # near-lip and near-drop leaning to H2 (analogous accent): a soft mix in the first 0.35 R
        lean = opts["h2_lean"] * (1.0 - C.smoothstep((rho - 1.0) / 0.35))
        lum = liq @ w3
        tinted = liq * (0.55 + 0.45 * h2a[None, None, :] / max(float(h2a.max()), 1e-3))
        liq = liq * (1.0 - lean[..., None]) + tinted * lean[..., None]
        # speculars stay neutral white
        sp = C.smoothstep((lum - 0.80) / 0.15)[..., None]
        liq = liq * (1.0 - sp) + lum[..., None] * sp
        K.wall_fade(liq, ctx, y0=r0)
        K.text_fade(liq, ctx, y0=r0)
        K.edge_fade(liq, ctx, y0=r0)
        cv[r0:r1] += liq * F32(opts["gain"])
    del plate_im, L8, op8
    # extra droplets: 6-12 sprites at 1.3-1.8 R, biased to the wind side
    nd = int(opts["drops"])
    if nd:
        sprites = droplet_images(ctx.seed, nd * 3)
        rd = ctx.rand("drops")
        used = 0
        for im in sprites:
            if used >= nd:
                break
            th_ = wind + rd.normal(1, 0.0, 1.0)[0]
            rr = 1.30 + 0.50 * rd.uniform()
            size = (0.02 + 0.04 * rd.uniform()) * R * 2.0
            sx_, sy_ = d.cx + rr * R * math.cos(th_), d.cy + rr * R * math.sin(th_)
            if in_text_box(ctx, sx_, sy_, size):
                continue
            if blit_sprite(cv, im, sx_, sy_, size):
                used += 1
    ctx.log["splash"] = {"liquid": liquid, "plate": pk.plate.id, "strong": pk.strong_angle, "rot": pk.rotation_deg, "mirror": pk.mirror,
                         "lod": pinfo["lod"], "upscale": pinfo["upscale"], "hue_delta_max": float(np.abs(delta).max()),
                         "warp": amp, "cut_spikes": len(cuts)}
