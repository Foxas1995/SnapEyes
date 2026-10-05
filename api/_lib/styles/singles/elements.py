# -*- coding: utf-8 -*-
"""designs.singles_elements: ELEMENTS, brief 3.12 (scratch prototype), round 2c.

A split rim: FIRE on the warmer half of the ring, WATER on the cooler half, a vertical cut through the pupil that exists only in the
matter layers (the iris is never cut). Never a full crown, so it does not duplicate Splash.
  assignment  the half of the ring (0.70-0.92 R, 180 deg each side) with the higher warmth (Lab b*, ties: higher L*; grey eyes C* < 10:
              left half, seeded flip) carries FIRE. Never recolours the iris.
  fire half   a P-EL-FLAME v3 plate (sharp real flames, 1/8000 s, deep orange), gradient-mapped through a fire ramp by its own luminance
              (deep red-brown > deep orange #C4471B > orange > amber > cream: nothing clipped to white, no pink, no cyan fringe), sharpened,
              radially compressed x0.70 and tapered to 0.12 of that toward the cut (AD: an angular taper, not a planar fade), masked to the
              half; procedural embers (lengths x0.6-2.5, 30 % bent by the wind, no cyan tip), e <= 1.0 R
  water half  a P-SP-CROWN plate (water_clear with a cool tint of the eye, water_teal for blue-green) compressed to a LOW crown (spikes <= 0.3 R)
              with 5-7 lobes, tapered toward the cut, its speckle thinned; a droplet band on the lip and droplets to 2.0 R; two hairline ripple
              arcs in 3-5 segments with random gaps (alpha 0.05-0.25, r 1.25-1.7 R)
  seam        a 0.14 R gap of pure black between the materials at the top and the bottom of the cut (0.10 R in the brief, 0.14 R where the
              matter tapers); no third material (no steam)
Hard rules: nothing on a visible iris pixel r <= 0.95 R (paste last); colours physical (flame) or the liquid's own (crown) with hue
shifts <= 15 deg; seeds from sha256; sizes in R and S; numpy + PIL only.
"""
from __future__ import annotations

# PORT of work package WP5A (step A): singles_elements.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists
# (imports, plates); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np
from PIL import ImageFilter

from .. import core as C
from .. import matter as M
from . import kit as K
from . import splash as SS

TWO_PI = 2.0 * math.pi
F32 = np.float32
EP = {
    "gap": 0.14,                 # R, pure black seam between the two materials (0.10 R in the brief; 0.14 R where the matter tapers)
    "fire_gain": 1.0,
    "water_gain": 1.0,
    "embers": 110,
    "drops": 24,
    "lip_drops": 16,             # the droplet band on the water lip
    "flame_m": 0.75,             # radial compression of the flames (AD: x0.75, tips at e about 0.6 R -> <= 0.45 R)
    "crown_m": 0.55,             # radial compression of the water crown (spikes <= 0.3 R)
    "taper_deg": 35.0,           # the matter shrinks toward the cut over this angle
    "taper_floor": 0.12,         # ... to this share of its height at the cut (a 0.05 R lick)
    "ripples": (1.36, 1.62),
    "ripple_alpha": (0.22, 0.12),
    "hue_max": 15.0,
    "flip": None,                # None: by warmth; True / False forces fire on the left / right (the buyer's swap)
    "sharpen": 0.75,             # unsharp on the flame plate (percent / 100)
    "flame_map": 0.40,           # share of the fire ramp in the flame colour (the rest is the plate's own cleaned colour)
    "speck_gain": 1.0,
}
RIPPLE_GAIN = 2.5
FIRE_STOPS = ((0.00, "#000000"), (0.05, "#260903"), (0.20, "#7E230C"), (0.40, "#C4471B"), (0.60, "#EC7A24"), (0.78, "#F8A63F"),
              (0.92, "#FFCF73"), (1.00, "#FFE9B8"))
EMBER_STOPS = ("#D9601F", "#F29A3A", "#FFC966")


def v3_exclude(reg):
    """Every registered P-EL-FLAME plate that is not a v3 keeper (the v2 plates were soft glows clipped to white)."""
    return [p.id for p in reg.plates("P-EL-FLAME") if "__v3__" not in p.id]


def warmth_halves(iris):
    """(warm_left, info): which half of the ring (left = screen x < centre) is warmer. Lab b* per angle bin of the eye's own ring
    (bins 0.70-0.92 R, 360, bin k = k deg clockwise from 3 o'clock), left half = bins 90..269."""
    ring = np.asarray(iris.ring, np.float64) * 255.0
    lab = C.L.srgb_to_lab(ring)
    b = lab[:, 2]
    Ls = lab[:, 0]
    left = np.arange(90, 270)
    right = np.concatenate([np.arange(270, 360), np.arange(0, 90)])
    bl, br = float(b[left].mean()), float(b[right].mean())
    ll, lr = float(Ls[left].mean()), float(Ls[right].mean())
    chroma = iris.stats["C"]
    info = {"b_left": round(bl, 2), "b_right": round(br, 2), "L_left": round(ll, 2), "L_right": round(lr, 2), "tie": False}
    if chroma < 10.0:                       # grey eyes: left half unless the seeded flip says otherwise
        info["tie"] = True
        return True, info
    if abs(bl - br) < 0.75:                 # a tie on b*: the lighter half burns
        info["tie"] = True
        return ll >= lr, info
    return bl > br, info


def _seam_alpha(th, rho, side, gap, phases, soft=0.26):
    """(h, W) alpha of one half by ANGLE: 0 inside the pure-black gap (0.14 R wide on the vertical cut through the top and the bottom), rising over
    `soft` rad (15 deg) with a ragged edge (a few sines in rho, seeded): the matter ends like a flame ends, not at a vertical plate edge.
    th: screen angle (atan2(dy, dx), y down); side: +1 right half, -1 left half. The ragged edge is evaluated only in the transition strip."""
    sd = side * (math.pi / 2.0 - np.abs(th))                               # > 0 inside the half, radians from the cut
    sd = sd - 0.5 * gap / np.maximum(rho, 1.0)                              # the gap, as an angle at this radius
    out = (sd > 0.0).astype(np.float32)
    strip = np.abs(sd) < soft + 0.17
    if strip.any():
        rr = rho[strip]
        jit = 0.07 * np.sin(9.0 * rr + phases[0]) + 0.05 * np.sin(23.0 * rr + phases[1]) + 0.03 * np.sin(51.0 * rr + phases[2])
        # the ragged edge may only recede from the gap, never reach into it: the nominal gap (sd < 0) stays pure black
        out[strip] = C.smoothstep((sd[strip] + jit) / soft) * C.smoothstep(sd[strip] / 0.03)
    return out


def _taper_fn(base, taper_deg, floor, lobes=None):
    """scale_fn(theta) for K.radial_warp_im: base x (floor + (1 - floor) smoothstep(angular distance from the cut / taper)); the cut runs through
    the top and the bottom of the circle (theta = -+90 deg on screen). lobes: (n, phase, amp) adds n low lobes."""
    td = math.radians(taper_deg)

    def f(th):
        dist = np.abs(np.abs(th) - math.pi / 2.0)
        t = C.smoothstep(dist / td)
        m = base * (floor + (1.0 - floor) * t)
        if lobes is not None:
            n, ph, amp = lobes
            m = m * (1.0 + amp * np.cos(n * (th - ph)))
        return m
    return f


def fire_lut(hue_delta=0.0, n=256):
    """(n, 3) float32 fire ramp indexed by plate luminance 0..1, optionally hue shifted (LCh sense) by a few degrees."""
    xs = np.array([s[0] for s in FIRE_STOPS])
    cols = np.stack([C.rgb01(s[1]) for s in FIRE_STOPS])
    t = np.linspace(0.0, 1.0, n)
    lut = np.stack([np.interp(t, xs, cols[:, c]) for c in range(3)], 1).astype(np.float32)
    if abs(hue_delta) > 0.01:
        lut = SS.hue_shift_plate(lut[None, :, :], np.full(C.LUT_N, float(hue_delta), np.float32), np.zeros((1, n), np.float32))[0]
    return lut


def _flame_band(rgb, lut, mix=0.40):
    """rgb (h, W, 3) 0..1 of the (sharpened) flame plate -> physical flame colour, no clipped white, no pink, no cyan fringe:
    mix x the fire ramp by luminance + (1 - mix) x the plate's own colour cleaned (orange order R >= G >= B, blue removed, whites pulled toward the
    ramp). The v3 plates are already deep orange with small yellow cores; the ramp only guards the extremes."""
    w3 = np.array([0.299, 0.587, 0.114], np.float32)
    y = rgb @ w3
    idx = np.clip(y * 255.0 + 0.5, 0, 255).astype(np.int32)
    ramp = lut[idx]
    r = rgb[..., 0]
    g = np.minimum(rgb[..., 1], r)
    b = np.minimum(rgb[..., 2], 0.72 * g)
    own = np.stack([r, g, b], -1)
    white = C.smoothstep((b - 0.45) / 0.35)[..., None]              # near-white cores go to the ramp's cream
    col = own * (1.0 - mix) + ramp * mix
    col = col * (1.0 - white) + ramp * white
    return np.clip(col, 0.0, 1.0)


def _curve_embers(light, px, py, dirx, diry, length, bend, col, amp, sigma_px):
    """Bent comet streaks: k points along p0 - dir L t + bend L t^2 (t 0 -> 1, the head at p0), intensity falling to the tail."""
    n = len(px)
    if n == 0:
        return
    k = int(np.clip(math.ceil(float(np.max(length)) / (0.9 * max(sigma_px, 0.5))), 8, 40))
    t = (np.arange(k) + 0.5) / k
    prof = (1.0 - t) ** 1.6
    prof = prof / prof.sum()
    nx, ny = -diry, dirx                                               # the normal bends the tail sideways
    xx = px[:, None] - dirx[:, None] * length[:, None] * t[None, :] + nx[:, None] * bend[:, None] * length[:, None] * t[None, :] ** 2
    yy = py[:, None] - diry[:, None] * length[:, None] * t[None, :] + ny[:, None] * bend[:, None] * length[:, None] * t[None, :] ** 2
    aa = np.asarray(amp)[:, None] * prof[None, :] * k
    cc = np.repeat(np.asarray(col, np.float32), k, axis=0)
    light.splat(xx.ravel(), yy.ravel(), sigma_px, cc, aa.ravel(), min_sigma=0.5)


def _ripple_arcs(cv, ctx, d, side, rgb, alphas, radii, gap):
    """Two hairline arcs on the water half, each in 3-5 segments with random gaps (alpha 0.05-0.25 per segment, tapering at the ends)."""
    R, S = d.R, ctx.S
    for k, (r_, a_) in enumerate(zip(radii, alphas)):
        rnd = ctx.rand(f"ripple{k}")
        sigma = 0.0007 * S
        centre = 0.0 if side > 0 else math.pi                   # screen angle of the half's axis (0 = right, pi = left)
        margin = math.asin(min(0.99, (gap / 2.0 + 0.10) / r_))
        half = math.pi / 2.0 - margin
        nseg = int(rnd.integers(1, 3, 6)[0])                     # 3-5 segments
        cuts = np.sort(rnd.uniform(nseg - 1)) if nseg > 1 else np.array([])
        edges = np.concatenate([[0.0], cuts, [1.0]])
        for s_i in range(nseg):
            u0, u1 = edges[s_i], edges[s_i + 1]
            gapw = 0.06 + 0.06 * float(rnd.uniform())
            u0, u1 = u0 + gapw / 2.0, u1 - gapw / 2.0
            if u1 - u0 < 0.03:
                continue
            al = float(rnd.uniform(1, 0.05, 0.25)[0]) * (a_ / 0.22)
            ang0 = centre - half + 2.0 * half * u0
            ang1 = centre - half + 2.0 * half * u1
            length = (ang1 - ang0) * r_ * R
            n = int(np.clip(length / max(0.35 * max(sigma, 0.5), 0.2), 40, 60000))
            u = (np.arange(n) + 0.5) / n
            th = ang0 + (ang1 - ang0) * u
            wob = 1.0 + 0.006 * (C.periodic_fbm1d(512, rnd, 3, base=7)[np.minimum((u * 511).astype(np.int64), 511)] * 2 - 1)
            ends = C.smoothstep(u / 0.18) * C.smoothstep((1 - u) / 0.18)
            px = d.cx + r_ * R * wob * np.cos(th)
            py = d.cy + r_ * R * wob * np.sin(th)
            col = np.asarray(rgb, np.float32)
            amp = al * ends * (0.35 * max(sigma, 0.5)) / (math.sqrt(2 * math.pi) * max(sigma, 0.5)) * RIPPLE_GAIN
            tb = ctx.text_box
            if tb is not None:                                     # no hairline through the customer's text (+ the 0.02 S margin)
                m_ = 0.02 * S
                amp = amp * (1.0 - ((px > tb[0] - m_) & (px < tb[2] + m_) & (py > tb[1] - m_) & (py < tb[3] + m_)))
            C.splat(cv, px, py, sigma, col, amp, min_sigma=0.5)


def fx_elements(cv, ctx):
    opts = dict(EP)
    opts.update(ctx.opts.get("elements", {}))
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    reg = SS.registry()
    rnd = ctx.rand("elements")
    warm_left, winfo = warmth_halves(iris)
    if winfo["tie"] and iris.stats["C"] < 10.0 and rnd.uniform() < 0.5:
        warm_left = not warm_left                            # grey eyes: the seeded flip
    if opts["flip"] is not None:
        warm_left = bool(opts["flip"])
    fire_side = -1.0 if warm_left else 1.0                    # sign of x on the fire half
    water_side = -fire_side
    K.fill_radial_bg(cv, d.cx, d.cy, 1.8 * R, "#101012", "#040405")
    h2rgb, h2how, h2deg = K.secondary_hue(iris)
    w3 = np.array([0.299, 0.587, 0.114], np.float32)
    fade = (lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0), lambda v, r0: K.edge_fade(v, ctx, y0=r0))
    gap = opts["gap"]
    # ---------------------------------------------------------------- fire half
    want_fire = 90.0 + (26.0 if warm_left else -26.0) + float(rnd.uniform(1, -8.0, 8.0)[0])
    pkf = reg.pick("P-EL-FLAME", ctx.seed, wanted_strong_angle=want_fire, max_rotation=25.0, exclude=v3_exclude(reg))
    rs_f = min(0.985, 1.045 * pkf.plate.void_diam * 4096.0 / (2.0 * 0.255 * 4096.0))
    flame_im, finfo = K.place_u8(pkf, W, H, d.cx, d.cy, R, r_scale=rs_f, edge_fade=0.05)
    ph, _ = SS._plate_hue(np.asarray(flame_im)[::4, ::4].astype(np.float32) / 255.0)
    dh = ((h2deg - ph + 180.0) % 360.0) - 180.0
    # flames are physical colours: they lean toward H2 only when H2 is an analogous (warm-side) hue, never the long way round the wheel
    delta = float(np.clip(dh, -opts["hue_max"], opts["hue_max"])) if abs(dh) <= 70.0 else 0.0
    lut = fire_lut(delta)
    # sharpen (the plate is a soft macro at 100 %), compress radially and taper toward the cut
    if opts["sharpen"] > 0:
        flame_im = flame_im.filter(ImageFilter.UnsharpMask(radius=max(0.8, 0.0012 * S), percent=int(round(100 * opts["sharpen"])), threshold=1))
    flame_im = K.radial_warp_im(flame_im, d.cx, d.cy, R, _taper_fn(opts["flame_m"], opts["taper_deg"], opts["taper_floor"]), e0=0.05)
    ph_ = ctx.rand("seam").uniform(6) * TWO_PI
    for r0, r1 in K.bands(H):
        rho, th_ = C.polar(W, H, d.cx, d.cy, R, 1.0, (0, r0, W, r1))
        fl = _flame_band(K.u8_band(flame_im, r0, r1), lut, opts["flame_map"])
        moat = 0.25 + 0.75 * C.smoothstep((rho - 1.0) / 0.035)
        fl *= moat[..., None] * _seam_alpha(th_, rho, fire_side, gap, ph_[:3])[..., None]
        for f_ in fade:
            f_(fl, r0)
        cv[r0:r1] += fl * F32(opts["fire_gain"])
    del flame_im
    # embers: rising comet streaks on the fire half (lengths x0.6-2.5, 30 % bent by the wind, colours from the ember ramp, no cyan)
    light = M.ParticleLayer()
    re_ = ctx.rand("embers")
    ne = int(opts["embers"])
    pal = np.stack([C.rgb01(c) for c in EMBER_STOPS]).astype(np.float32)
    cand = ne * 8
    ang_c = -math.pi / 2.0 - math.radians(32.0) * (1.0 if warm_left else -1.0)  # screen angle (y down): left -> -122 deg
    thc = ang_c + re_.normal(cand, 0.0, 0.85)
    e = 0.12 + re_.exponential(cand, 0.30)
    ok = e <= 1.0
    px = d.cx + (1.0 + e) * R * np.cos(thc)
    py = d.cy + (1.0 + e) * R * np.sin(thc)
    ok &= (px - d.cx) * fire_side > (gap / 2.0 + 0.04) * R
    idx = np.nonzero(ok)[0][:ne]
    if len(idx):
        px, py = px[idx], py[idx]
        m_ = len(idx)
        cls = re_.integers(m_, 0, 3)
        cols = pal[cls]
        drift = 0.25 + 0.20 * re_.uniform(m_)
        vx = (-0.35 if warm_left else 0.35) * drift
        vy = -np.ones(m_)
        nv = np.hypot(vx, vy)
        dirx, diry = vx / nv, vy / nv
        L_ = np.exp(re_.uniform(m_, math.log(0.6), math.log(2.5))) * 0.022 * R
        bend = np.where(re_.uniform(m_) < 0.30, re_.uniform(m_, -0.6, 0.6), 0.0)
        amp = np.array([0.40, 0.70, 1.05])[cls] * (0.6 + 0.4 * re_.uniform(m_))
        _curve_embers(light, px, py, dirx, diry, L_, bend, cols, amp * 0.85, sigma_px=0.0005 * S)
        sg = (0.0020 + 0.0028 * re_.uniform(m_)) * R
        light.splat(px, py, sg, cols, amp * 1.4, min_sigma=0.5)
    light.flush(cv, fades=fade, mode="add")                  # additive: a screen over an already bright flame (base > 1) would tint the spark cyan
    del light
    # ---------------------------------------------------------------- water half
    liquid = ctx.opts.get("water_liquid") or ("water_teal" if (iris.stats["class"] == "own" and 160.0 <= iris.stats["h"] < 178.0) else "water_clear")
    want_w = 90.0 + (-58.0 if warm_left else 58.0) + float(rnd.uniform(1, -8.0, 8.0)[0])      # tall spikes AWAY from the water half
    pkw = reg.pick("P-SP-CROWN", ctx.seed, wanted_strong_angle=want_w, max_rotation=35.0, liquid=liquid)
    rs_w = min(0.975, 1.045 * pkw.plate.void_diam * 4096.0 / (2.0 * 0.255 * 4096.0))
    crown_im, winfo2 = K.place_u8(pkw, W, H, d.cx, d.cy, R, r_scale=rs_w, edge_fade=0.05)
    rl = ctx.rand("lobes")
    nlobe = int(rl.integers(1, 5, 8)[0])                                                       # 5-7 low lobes
    lobes = (nlobe, float(rl.uniform()) * TWO_PI, 0.28)
    crown_im = K.radial_warp_im(crown_im, d.cx, d.cy, R, _taper_fn(opts["crown_m"], opts["taper_deg"], opts["taper_floor"], lobes), e0=0.02)
    L8, op8 = K.opening_lum(crown_im, S)
    n_th = C.periodic_fbm1d(512, ctx.rand("specknoise"), 3, base=5)
    ph2, _ = SS._plate_hue(np.asarray(crown_im)[::4, ::4].astype(np.float32) / 255.0)
    hr, _cr = SS._ring_hue_lut(iris)
    dd_ = ((hr - ph2 + 180.0) % 360.0) - 180.0
    dl = np.where(np.abs(dd_) <= 90.0, np.clip(dd_, -opts["hue_max"], opts["hue_max"]), 0.0)
    if iris.stats["class"] == "grey" or iris.stats["C"] < 13.0:
        dl = dl * 0.0
    dl_lut = C.angular_lut(dl)
    tint = SS.crown_tint(iris) if (liquid == "water_clear" and iris.stats["class"] != "dark_brown") else np.ones(3, np.float32)
    for r0, r1 in K.bands(H):
        rho, th = C.polar(W, H, d.cx, d.cy, R, 1.0, (0, r0, W, r1))
        e = rho - 1.0
        a = K.u8_band(crown_im, r0, r1)
        thm = (th % TWO_PI) / TWO_PI
        nz = n_th[np.minimum((thm * 512).astype(np.int32), 511)]
        wsp = np.exp(-e / 0.8) * C.smoothstep((e - 0.12) / 0.10) * (1.0 - C.smoothstep((e - 1.5) / 0.25)) * (0.25 + 0.75 * nz) * opts["speck_gain"]
        lipk = 1.0 - C.smoothstep((e - 0.10) / 0.04)                      # the lip's own texture (e < 0.10 R, tapered toward the seam) is never opened: no square blocks
        wsp = lipk + (1.0 - lipk) * wsp
        liq_in = K.speck_keep(a, L8, op8, r0, r1, wsp.astype(np.float32))
        cr = SS.hue_shift_plate(liq_in, dl_lut, th)
        if liquid == "water_clear":
            cr = cr * tint[None, None, :]
        lum = cr @ w3
        sp = C.smoothstep((lum - 0.80) / 0.15)[..., None]
        cr = cr * (1.0 - sp) + lum[..., None] * sp
        cr *= _seam_alpha(th, rho, water_side, gap, ph_[3:6])[..., None]
        for f_ in fade:
            f_(cr, r0)
        cv[r0:r1] += cr * F32(opts["water_gain"])
    del crown_im, L8, op8
    # droplets: a band on the lip (small beads just off the liquid) and free droplets out to 2.0 R
    nd, nl_ = int(opts["drops"]), int(opts["lip_drops"])
    rdr = ctx.rand("wdrops")
    sprites = SS.droplet_images(ctx.seed, (nd + nl_) * 3)
    used_free, used_lip = 0, 0
    ax = 0.0 if water_side > 0 else math.pi
    for im in sprites:
        if used_free >= nd and used_lip >= nl_:
            break
        lip = used_lip < nl_ and (used_free >= nd or rdr.uniform() < nl_ / float(nd + nl_))
        if lip:
            r = 1.04 + 0.16 * rdr.uniform() ** 1.2
            a = ax + (rdr.uniform() * 2.0 - 1.0) * math.radians(78.0)
            size = (0.010 + 0.020 * rdr.uniform()) * R * 2.0
        else:
            r = 1.10 + 0.90 * rdr.uniform() ** 1.3
            a = ax + rdr.normal(1, 0.0, 0.85)[0]
            size = (0.02 + 0.04 * rdr.uniform()) * R * 2.0
        x, y = d.cx + r * R * math.cos(a), d.cy + r * R * math.sin(a)
        if (x - d.cx) * water_side < (gap / 2.0 + 0.04) * R or SS.in_text_box(ctx, x, y, size):
            continue
        if SS.blit_sprite(cv, im, x, y, size, 0.85):
            if lip:
                used_lip += 1
            else:
                used_free += 1
    # ripples: hairline arcs in a cool white leaning to the eye's own colour
    lift = C.from_lch(88.0, 8.0, float(np.median(SS._ring_hue_lut(iris)[0]))).astype(np.float32)
    _ripple_arcs(cv, ctx, d, water_side, lift, opts["ripple_alpha"], opts["ripples"], gap)
    ctx.log["elements"] = {"fire_left": bool(warm_left), "warmth": winfo, "flame_plate": pkf.plate.id, "flame_strong": pkf.strong_angle,
                           "flame_hue_delta": delta, "water_plate": pkw.plate.id, "liquid": liquid, "drops": used_free, "lip_drops": used_lip,
                           "flame_lod": finfo["lod"], "flame_upscale": finfo["upscale"], "flame_r_scale": rs_f, "crown_lod": winfo2["lod"],
                           "crown_upscale": winfo2["upscale"], "gap": gap, "lobes": nlobe}
