# -*- coding: utf-8 -*-
"""designs.singles_powder: POWDER BURST, brief 3.6 with the tight envelope of 0.6 R3 / R13 (scratch prototype).

Dust, not smoke: a fine mist of the eye's own colours with crisp grains and iris-chips riding in it, asymmetric wind, restraint.

  envelope   E(theta) = 0.55 R + 0.45 R max(0, cos(theta - wind))^1.5 beyond the limb, +-12 % reach noise; a halo all round and one
             plume to e = 1.0 R on the wind side. Every layer (haze, grains, dust, chips) is confined to it.
  haze       a P-SN-CLOUD plate (void = the limb, strong side on the wind), gradient-mapped through the eye's own colours per angle,
             thinned to a mist (gamma, alpha), cut by the envelope with an organic (noise-warped) outline
  matter     polygon grains, sub-pixel dust, streaks, iris-chips (real fibres of the SAME iris), defocused blobs
  rim        the iris's own band 0.92-0.99 R shown again just outside the limb (limbus breakup, before the paste) and a fine veil of
             grit over zone B (rim_veil, after the paste, r >= 0.955 R, mean alpha <= 0.30, max 0.6: brief 1.1 rule 4 / D1)
AD round 2c fixes: dark limbal edge (zone B multiplied down at the limb + a black moat under the feather) instead of a pale bezel; the veil on the wind half
only (mean alpha <= 0.10); a visible limbus breakup (iris-rim chips peeling off 30 % of the circumference); plume plate alpha 0.30 with a radial mask and a
hue-locked gradient map (no clay-grey); tail L2 0.30 R / 10 %; streaks few, coloured, jittered +-25 deg, lognormal width, wind half; chips 30 % dark, 20 %
translucent, a lower-right shade facet; R 0.26 S with the plume capped at e 0.85 R.
Hard rules: nothing is ever drawn on a visible pixel with r <= 0.95 R (the iris is pasted last, the veil starts at 0.955 R);
colours from the eye's own ring colours per angle (fallbacks: copper for dark brown, platinum for grey); float layers, soft tone
map, dither; seeds from sha256; sizes in R and S; numpy + PIL only.
"""
from __future__ import annotations

# PORT of work package WP5A (step A): singles_powder.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists
# (imports, plates); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math
import hashlib

import numpy as np

from .. import core as C
from .. import matter as M
from .. import plates as RG
from . import kit as K

TWO_PI = 2.0 * math.pi
F32 = np.float32

# tunables (the art director's knobs; the contract is the measured profile in the tests)
P = {
    "halo": 0.52, "plume": 0.33,              # envelope (R beyond the limb): halo 0.55 R all round, one plume to e = 0.85 R (R is 0.26 S now)
    "b": 0.30,                                # wind bias of the angular density
    "haze_alpha": 0.30, "haze_gamma": 2.6, "haze_scale": 2.0, "haze_fall": 0.95, "haze_r0": 0.45, "haze_r1": 0.80,
    "dust_amp": 1.5, "chip_lo": 0.45, "chip_gain": 0.85, "chip_lift": 1.15, "chip_share": 0.72,   # the mist from the plate
    "lambda": 830,                            # grains per R of circumference (brief start value 600)
    "dust": 3.8,                              # dust count = dust x grains
    "l2": 0.30, "tail": 0.10,                 # radial law: 90 % dense (L1 0.18 R), 10 % tail (L2 0.30 R)
    "chunks": 75,                             # iris-chips (brief start value 60)
    "chip_dark": 0.30, "chip_trans": 0.20, "chip_facet": 0.45,
    "streaks": 36,
    "blobs": 4,
    "fg": 3,
    "limb_chips": 220,                        # the limbus breakup: chips of the iris's own rim peeling off (AD: 250-350 at 1024, too dense by eye: 220)
    "rim_frags": 450,
    "moat": 0.10,                             # canvas multiplier under the feathered limb (a dark edge instead of a pale bezel)
    "veil": True,                             # rim_veil (D1)
    "veil_mean": 0.09,
}
MOAT_IN, MOAT_W = 1.012, 0.034               # R: the moat is full up to MOAT_IN and is gone at MOAT_IN + MOAT_W


def registry():
    return RG


def _angdiff(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def _hash(seed, *parts):
    return int.from_bytes(hashlib.sha256(("|".join([str(seed)] + [str(p) for p in parts])).encode()).digest()[:8], "big")


WIND_SETS = {
    "square": ((20.0, 160.0), (200.0, 250.0)),        # never straight down into the text
    "wall": ((40.0, 140.0),),
}
MIN_VOID = 0.40        # R is 0.26 S now: a plate with a smaller void than 0.473 is placed with r_scale < 1 (its void hides under the iris) so the 4096 upscale stays <= x1.1


R_MAX_4K = 0.265 * 4096.0


def plate_scale(p, r_max=R_MAX_4K):
    """r_scale (<= 1) that keeps the plate's upscale at 4096 within x1.045 (the AD's x1.05 limit; the brief allows x1.1) for the largest R the design uses."""
    need = 1.045 * p.void_diam * 4096.0 / (2.0 * r_max)
    return float(min(1.0, need))


def pick_cloud(seed, allowed, maxrot=10.0, black=("30", "45", "60")):
    """One P-SN-CLOUD keeper whose strong side (after an optional mirror and a small rotation) lands in one of the allowed screen-angle
    bands (deg CCW from 3 o'clock). Only plates that can be placed at R = 0.24 S without an upscale beyond x1.1 at 4096 (void >= 0.437)."""
    R = registry()
    rnd = C.Rand(seed, "cloudpick")
    cands = []
    for p in R.plates("P-SN-CLOUD", black=list(black)):
        if p.strength < R.WEAK_STRENGTH or p.strong_angle is None or (p.void_diam or 0) < MIN_VOID:
            continue
        for mir in (False, True):
            a = 180.0 - p.strong_angle if mir else p.strong_angle
            for lo, hi in allowed:
                mid, half = (lo + hi) / 2.0, (hi - lo) / 2.0
                if abs(_angdiff(a, mid)) <= half + maxrot:
                    cands.append((p, mir, a, lo, hi))
    if not cands:
        raise RuntimeError("no cloud plate for the allowed winds")
    p, mir, a, lo, hi = min(cands, key=lambda c: _hash(seed, c[0].id, c[1]))
    rot = float(rnd.uniform() * 2.0 - 1.0) * maxrot
    mid, half = (lo + hi) / 2.0, (hi - lo) / 2.0
    fin = a + rot
    if abs(_angdiff(fin, mid)) > half:
        fin = mid + math.copysign(half, _angdiff(fin, mid))
        rot = _angdiff(fin, a)
    return R.Pick(p, rot, mir, False, "")


def haze_stops(iris, stops, h2deg):
    """The gradient map of the plate haze, hue-locked: (deep, mid, hot) per ring angle, plus the per-angle weight of the secondary hue.
    hot = the eye's own colour lifted (L +16, chroma x 0.9, floor 0.6 x the ring chroma) with only 14 % white: never the clay-grey of a
    near-white mixed into a mid-tone, and H2 only where it is within 15-40 deg of the ring hue."""
    deep, mid = stops[0], stops[1]
    Lm, Cm, hm = C.lch(mid)
    Cring = np.asarray(C.lch(iris.ring)[1], np.float64)
    Lh = np.minimum(np.asarray(Lm, np.float64) + 16.0, 90.0)
    Ch = np.maximum(np.asarray(Cm, np.float64) * 0.9, 0.6 * Cring)
    hot = C.from_lch(Lh, Ch, hm)
    hot = C.mix(hot, np.ones_like(hot), 0.14)
    dh = np.abs(((np.asarray(hm, np.float64) - h2deg) + 180.0) % 360.0 - 180.0)
    h2w = 1.0 - C.smoothstep((dh - 8.0) / 14.0)
    return np.stack([deep, mid, hot]).astype(np.float32), h2w.astype(np.float32)


def tint_band(lum, th, ctx, stops, h2, n_noise, h2w, deep_floor=0.30, eps=0.003):
    """Gradient-map a band of a mono plate (h, W) through the eye's own colours: black -> deep -> mid -> hot by plate luminance, per ring angle
    (th: the band's pixel angles), the hottest cores partly taking the secondary hue H2 where it is a neighbour of the ring hue (h2w) in
    irregular patches (n_noise: the band's 0..1 noise). Only the pixels that carry haze (lum > eps) are coloured: most of the canvas is black."""
    out = np.zeros(lum.shape + (3,), np.float32)
    m = lum > eps
    if not m.any():
        return out
    t = np.clip(lum[m], 0.0, 1.0)
    idx = C.angle_index(th[m])
    lutD, lutM, lutH = C.palette_lut(stops[0]), C.palette_lut(stops[1]), C.palette_lut(stops[2])
    deep, mid, hot = lutD[idx], lutM[idx], lutH[idx]
    lutW = C.angular_lut(h2w)
    w2 = (C.smoothstep((n_noise[m] - 0.55) / 0.25) * 0.4 * lutW[idx]).astype(np.float32)[:, None]
    h2 = np.asarray(h2, np.float32)
    hot = hot * (1 - w2) + (hot * 0.6 + h2 * 0.4) * w2

    def seg(a, b):
        return C.smoothstep((t - a) / (b - a))[:, None]
    col = deep * 0.45
    s = seg(0.0, deep_floor)
    col = col * (1 - s) + deep * s
    s = seg(deep_floor, 0.70)
    col = col * (1 - s) + mid * s
    s = seg(0.68, 0.95)
    col = col * (1 - s) + hot * s
    out[m] = col * seg(0.0, 0.10)
    return out


def _bg(cv, ctx, d):
    K.fill_radial_bg(cv, d.cx, d.cy, 1.0 * ctx.S, "#0D0E12", "#050507")


def limb_moat(cv, ctx, d, floor=0.10):
    """A dark moat under the feathered limb: the canvas is multiplied by `floor` up to MOAT_IN R and back to 1 at MOAT_IN + MOAT_W R, so the F3
    feather fades into black (the dark edge of the owner's H10 / H11) instead of over grit (the pale bezel of the first round)."""
    W, H = ctx.W, ctx.H
    R = d.R
    reach = (MOAT_IN + MOAT_W + 0.01) * R
    x0, x1 = max(0, int(d.cx - reach)), min(W, int(d.cx + reach) + 2)
    y0, y1 = max(0, int(d.cy - reach)), min(H, int(d.cy + reach) + 2)
    dx = (np.arange(x0, x1, dtype=np.float32) + np.float32(0.5 - d.cx))[None, :]
    for r0 in range(y0, y1, 256):
        r1 = min(y1, r0 + 256)
        dy = (np.arange(r0, r1, dtype=np.float32) + np.float32(0.5 - d.cy))[:, None]
        rho = np.sqrt(dx * dx + dy * dy) / np.float32(R)
        k = floor + (1.0 - floor) * C.smoothstep((rho - MOAT_IN) / MOAT_W)
        cv[r0:r1, x0:x1] *= k[..., None].astype(np.float32)
    return cv


def rim_veil_post(ctx, d, stops, emis, seed, mean_alpha=0.09):
    """rim_veil (D1): a fine veil of grit over zone B only (0.955 R <= r <= 1.0 R), drawn after the paste, on the WIND half only. Coverage follows
    the emission strength, alpha <= 0.6, and the band's mean alpha is scaled to `mean_alpha` (AD: <= 0.10; the brief allows 0.30)."""
    W, H = ctx.W, ctx.H
    R = d.R
    rnd = C.Rand(seed, "veil")
    n_ang, n_rad = 4096, 48
    tex = C.fbm_polar(n_ang, n_rad, rnd, octaves=2, base=(520, 7), gain=0.55)             # grit: grains 2-4 px at 1024 (a band would be a flat stripe)
    tex = (tex - tex.min()) / max(float(tex.max() - tex.min()), 1e-6)
    tex2 = C.fbm_polar(n_ang, n_rad, rnd, octaves=2, base=(260, 5), gain=0.55)            # grain colour: deep to hot
    tex2 = (tex2 - tex2.min()) / max(float(tex2.max() - tex2.min()), 1e-6)
    pre = 1.02 * R
    wind = emis.wind

    def apply(img8):
        x0, y0 = max(0, int(d.cx - pre)), max(0, int(d.cy - pre))
        x1, y1 = min(W, int(d.cx + pre) + 2), min(H, int(d.cy + pre) + 2)
        dx = (np.arange(x0, x1, dtype=np.float32) + np.float32(0.5 - d.cx))[None, :]
        dy = (np.arange(y0, y1, dtype=np.float32) + np.float32(0.5 - d.cy))[:, None]
        rho2 = (dx * dx + dy * dy) / np.float32(R * R)
        band = (rho2 >= 0.955 ** 2) & (rho2 <= 1.0)
        iy, ix = np.nonzero(band)
        if not len(iy):
            return
        rho = np.sqrt(rho2[iy, ix])
        th = np.arctan2(np.broadcast_to(dy, rho2.shape)[iy, ix], np.broadcast_to(dx, rho2.shape)[iy, ix])
        u = np.clip((rho - 0.955) / 0.045, 0.0, 1.0)
        tt = (th % TWO_PI) / TWO_PI
        v = M.sample_polar_tex(tex, tt, u)
        wh = C.smoothstep((np.cos(th - wind) + 0.15) / 0.7)              # the wind half only
        thr = 0.74 - 0.12 * u ** 1.2                                      # about 25-30 % of the band carries a grain
        a = C.smoothstep((v - thr) / 0.06) * (0.30 + 0.40 * u ** 1.5) * wh * (1.0 - C.smoothstep((rho - 0.985) / 0.015))
        lv = M.sample_polar_tex(tex2, tt, u)
        cur = float(a.mean())
        if cur > 1e-6:
            a = a * (mean_alpha / cur)
        a = np.minimum(a, 0.6).astype(np.float32)
        lv = lv[:, None]
        col = C.ring_at(stops[0], th) * (1.0 - lv) + C.ring_at(stops[2], th) * lv * np.float32(0.9)            # grains from the eye's deep to hot colour, not a flat mint
        col = np.minimum(col * np.float32(1.05), 1.0)
        sub = img8[y0:y1, x0:x1]
        cur8 = sub[iy, ix].astype(np.float32)
        aa = a[:, None]
        sub[iy, ix] = np.clip(np.rint(cur8 * (1.0 - aa) + col * 255.0 * aa), 0, 255).astype(np.uint8)
        ctx.log["veil_mean_alpha"] = float(a.mean())
        ctx.log["veil_max_alpha"] = float(a.max())
    return apply


PRESETS = {
    "dust": {},                                                                                   # the default: dust, not smoke
    "cloud": {"haze_alpha": 0.80, "haze_gamma": 2.6, "haze_r0": 0.70, "haze_r1": 1.0, "lambda": 600, "dust": 3.0, "chunks": 60,
              "l2": 0.42, "tail": 0.15, "plume": 0.45},                                           # the brief's starting values: a heavier, longer plume
}


def fx_powder(cv, ctx):
    opts = dict(P)
    po = dict(ctx.opts.get("powder", {}))
    opts.update(PRESETS[po.pop("preset", "dust")])
    opts.update(po)
    d = ctx.discs[0]
    iris = ctx.irises[0]
    W, H, S, R = ctx.W, ctx.H, ctx.S, d.R
    stops = K.ramp_stops(iris)
    h2, h2how, h2deg = K.secondary_hue(iris)
    hstops, h2w = haze_stops(iris, stops, h2deg)
    reg = registry()
    _bg(cv, ctx, d)
    # ---- wind and plate
    allowed = WIND_SETS["wall" if ctx.wall else "square"]
    pk = pick_cloud(ctx.seed, allowed)
    wind_deg = pk.strong_angle
    wind = -math.radians(wind_deg)
    emis = M.Emission(ctx.rand("emis"), wind, b=opts["b"], halo=opts["halo"], plume=opts["plume"])
    l2, tail = opts["l2"], opts["tail"]
    # ---- haze: the plate, thinned, tinted, cut by the envelope with a noise-warped outline (row bands: no full-canvas temporaries)
    rs = plate_scale(pk.plate)
    lum_im, pinfo = K.place_u8(pk, W, H, d.cx, d.cy, d.R, r_scale=rs, edge_fade=0.07)      # one anti-aliased resample: the same haze at every size
    wobn = C.value_noise2d(W, H, 7, ctx.rand("wob"))
    hn = C.value_noise2d(W, H, 5, ctx.rand("h2"))
    ang_x = np.arange(emis.n + 1) * (TWO_PI / emis.n)
    E_ext, gap_ext = np.concatenate([emis.E, emis.E[:1]]), np.concatenate([emis.gap, emis.gap[:1]])
    dens = []
    fq = max(1, int(round(S / 256.0)))                     # the acceptance field is always a 256-px grid of the short side: a master accepts the preview's grains
    for r0, r1 in K.bands(H):
        rho, th = C.polar(W, H, d.cx, d.cy, R, 1.0, (0, r0, W, r1))
        e = rho - 1.0
        thm = th % TWO_PI
        E = np.interp(thm, ang_x, E_ext).astype(np.float32)
        Ew = E * (1.0 + 0.30 * (wobn[r0:r1] * 2.0 - 1.0)).astype(np.float32)
        g = C.smoothstep((Ew - e) / (opts["haze_fall"] * Ew))
        rm = 1.0 - C.smoothstep((e - opts["haze_r0"]) / max(opts["haze_r1"] - opts["haze_r0"], 1e-3))     # AD: the plume plate is masked by e
        moat = 0.50 + 0.50 * C.smoothstep(e / 0.07)
        gap = np.interp(thm, ang_x, gap_ext).astype(np.float32)
        u = np.clip(e / 0.30, 0.0, 1.0)
        ringm = gap + (1.0 - gap) * (u * u * (3.0 - 2.0 * u))
        lum_b = K.u8_band(lum_im, r0, r1)
        hz = (np.clip(lum_b, 0, 1) ** opts["haze_gamma"]) * opts["haze_scale"] * g * rm * moat * ringm
        K.text_fade(hz, ctx, y0=r0)
        tl = tint_band(hz, th, ctx, hstops, h2, hn[r0:r1], h2w)
        K.wall_fade(tl, ctx, y0=r0)
        C.screen(cv[r0:r1], tl, opts["haze_alpha"])
        dens.append(C.box_reduce(np.ascontiguousarray(lum_b * (hz > 0.01)), fq))
    del wobn, hn, lum_im
    fields = M.Fields(ctx, red=np.concatenate(dens, 0), f=fq)
    del dens
    ctx.log["powder"] = {"plate": pk.plate.id, "wind_deg": wind_deg, "rot": pk.rotation_deg, "mirror": pk.mirror, "lod": pinfo["lod"],
                         "upscale": pinfo["upscale"], "r_scale": rs, "h2": h2how}
    ctx.opts["plate"] = ctx.log["powder"]
    # ---- matter: grains, dust, streaks (light, screened), all inside the envelope
    light = M.ParticleLayer()
    rg = ctx.rand("grain")
    Ng = int(round(opts["lambda"] * TWO_PI))
    th, e = emis.sample(rg, int(Ng * 2.2), l2=l2, tail=tail)
    mc = len(th)
    px, py = M.polar_px(d, 1.0 + e, th)
    u_keep = rg.uniform(mc)                                   # all attributes are drawn per CANDIDATE, then filtered: a preview and a master that
    lvl_all = 0.22 + 0.74 * rg.uniform(mc) ** 1.5             # accept a few borderline candidates differently still agree on every other grain
    lean_all = rg.uniform(mc) < 0.12
    gs_all = np.exp(math.log(0.008) + (math.log(0.023) - math.log(0.008)) * rg.uniform(mc)) * R
    keep = u_keep < fields.accept(px, py, plate_gain=1.6, plate_floor=0.16) * emis.ring_at(th, e, 0.22)
    sel = np.nonzero(keep)[0][:Ng]
    gcol = M.rgb_pal(stops, th[sel], lvl_all[sel])
    gcol = np.where(lean_all[sel][:, None], gcol * 0.5 + np.asarray(h2, np.float32) * 0.5, gcol)
    M.grains(cv, px[sel], py[sel], gs_all[sel] / 2.0, gcol, 0.92, ctx.rand("grainpoly"), ids=sel, total=mc)
    rd = ctx.rand("dust")
    Nd = int(round(Ng * opts["dust"]))
    th, e = emis.sample(rd, int(Nd * 2.2), l1=0.20, l2=l2 + 0.04, tail=tail)
    mc = len(th)
    px, py = M.polar_px(d, 1.0 + e, th)
    u_keep = rd.uniform(mc)
    lv_all = 0.30 + 0.62 * rd.uniform(mc) ** 1.3
    sig_all = (0.0026 + 0.0046 * rd.uniform(mc) ** 2.2) * R * 0.5
    amp_all = (0.12 + 1.5 * rd.uniform(mc) ** 3.4) * opts["dust_amp"]
    keep = u_keep < fields.accept(px, py, plate_gain=1.4, plate_floor=0.10) * emis.ring_at(th, e, 0.22)
    sel = np.nonzero(keep)[0][:Nd]
    M.dust(light, px[sel], py[sel], sig_all[sel], M.rgb_pal(stops, th[sel], lv_all[sel]), amp_all[sel])
    # streaks: few, coloured (not white), jittered +-25 deg off the radial, lognormal width 0.5-2.5 px at 1024, wind half only
    rsk = ctx.rand("streak")
    ns = int(opts["streaks"])
    th, e = emis.sample(rsk, ns * 4, min_e=0.30, l1=0.30, l2=0.5, tail=0.3)
    mc = len(th)
    px, py = M.polar_px(d, 1.0 + e, th)
    u_keep = rsk.uniform(mc)
    len_all = (0.04 + 0.10 * rsk.uniform(mc) ** 1.4) * R
    amp_all = 0.16 + 0.26 * rsk.uniform(mc)
    jit_all = np.radians(rsk.uniform(mc, -25.0, 25.0))
    wid_all = np.exp(rsk.uniform(mc, math.log(0.5), math.log(2.5))) / 1024.0 * S
    lvl_sk = 0.46 + 0.22 * rsk.uniform(mc)
    wind_half = np.cos(th - wind) > -0.15
    keep = (u_keep < fields.accept(px, py, plate_gain=1.2, plate_floor=0.04)) & wind_half
    sel = np.nonzero(keep)[0][:ns]
    if len(sel):
        ang = th[sel] + jit_all[sel]
        cols = M.rgb_pal(stops, th[sel], lvl_sk[sel])
        wpx = wid_all[sel] / S * 1024.0
        for lo, hi in ((0.0, 1.2), (1.2, 1.9), (1.9, 9.0)):
            gm = (wpx >= lo) & (wpx < hi)
            if not gm.any():
                continue
            g = sel[gm]
            M.streaks(light, px[g], py[g], np.cos(ang[gm]), np.sin(ang[gm]), len_all[g], cols[gm], amp_all[g], sigma_px=float(np.median(wid_all[g])))
    light.flush(cv, fades=(lambda v, r0: K.wall_fade(v, ctx, y0=r0), lambda v, r0: K.text_fade(v, ctx, y0=r0)))
    del light
    # ---- the dark moat under the feather (a dark limbal edge, not a pale bezel)
    limb_moat(cv, ctx, d, opts["moat"])
    # ---- the limbus turning into powder (outside the moat, before the paste): 30 % of the circumference erodes, the rest stays crisp
    rl = ctx.rand("limbchips")
    nz = C.periodic_fbm1d(1024, rl, 4, base=5)
    arcs = C.smoothstep((nz - 0.50) / 0.12).astype(np.float64)                      # about 30 % of the circumference
    arcs_w = 0.06 + 0.94 * arcs
    M.limbus_breakup(cv, ctx, d, ctx.rand("breakup"), emis, strength=1.0, rho_min=1.03, rho_max=1.10, lift=0.95,
                     arcs=arcs_w.astype(np.float32), thr0=0.48, thr1=0.40)
    M.rim_fragments(cv, d, int(opts["rim_frags"]), emis, stops, ctx.rand("rimfrag"), e_scale=0.05, e_max=0.16)
    # limb chips: real pieces of the iris's own rim (0.90-0.985 R) peeling off the eroding arcs, darkened where they turn away
    nl = int(opts["limb_chips"])
    if nl:
        th = emis.theta(rl, nl * 8)
        ok = rl.uniform(len(th)) < (0.05 + 0.95 * arcs[(th * 1024.0 / TWO_PI).astype(np.int64) % 1024])
        th = th[ok][:nl]
        mc = len(th)
        e = 0.040 + rl.exponential(mc, 0.040) * (0.6 + 1.4 * emis.w[(th * emis.n / TWO_PI).astype(np.int64) % emis.n])
        sz = (0.010 + 0.030 * rl.uniform(mc) ** 1.8) * R
        e = np.minimum(e, 0.16)
        e = np.maximum(e, 0.034 + sz / (2.0 * R))
        px, py = M.polar_px(d, 1.0 + e, th)
        M.chips(cv, d, px, py, sz * 2.0, th, stops, rl, rho_patch=(0.90, 0.985), patch_share=0.88, lift=1.0, shade_lo=0.42, shade_gain=0.75,
                dark_frac=0.30, dark_mult=0.55, facet=0.35)
    # ---- chips
    rc = ctx.rand("chips")
    nc = int(opts["chunks"])
    th, e = emis.sample(rc, nc * 3, l1=0.26, l2=0.50, tail=0.12, min_e=0.06)
    mc = len(th)
    u_keep = rc.uniform(mc)
    sz_all = (0.025 + 0.035 * rc.uniform(mc) ** 1.3) * R * (1.0 + 1.2 * e)
    e = np.maximum(e, sz_all / (2.0 * R) + 0.012)
    px, py = M.polar_px(d, 1.0 + e, th)
    keep = u_keep < fields.accept(px, py, plate_gain=1.2, plate_floor=0.10)
    sel = np.nonzero(keep)[0][:nc]
    M.chips(cv, d, px[sel], py[sel], sz_all[sel], th[sel], stops, rc, lift=opts["chip_lift"], patch_share=opts["chip_share"],
            shade_lo=opts["chip_lo"], shade_gain=opts["chip_gain"], ids=sel, total=mc, dark_frac=opts["chip_dark"], dark_mult=0.45,
            trans_frac=opts["chip_trans"], facet=opts["chip_facet"])
    # ---- defocused debris (the brief's blobs, drawn as out-of-focus chips: a shard in front of the lens, not a disc) and foreground chunks
    rb = ctx.rand("blobs")
    nb = int(opts["blobs"])
    th, e = emis.sample(rb, nb * 6, min_e=0.30, l1=0.30, l2=0.5, tail=0.3)
    px, py = M.polar_px(d, 1.0 + e, th)
    ok = np.nonzero(fields.accept(px, py, plate_gain=2.0, plate_floor=0.0) > 0.45)[0][:nb]
    if len(ok):
        sz = (0.055 + 0.030 * rb.uniform(len(ok))) * R * 2.0
        M.chips(cv, d, px[ok], py[ok], sz, th[ok], stops, rb, alpha=0.20 + 0.08 * rb.uniform(len(ok)), blur_px=0.03 * R, lift=0.9, dark=0.12)
    rf = ctx.rand("fgchunk")
    nf = int(opts["fg"])
    th, e = emis.sample(rf, nf * 6, min_e=0.35, l1=0.4, l2=0.6, tail=0.3)
    px, py = M.polar_px(d, 1.0 + e, th)
    ok = np.nonzero(fields.accept(px, py, plate_gain=0.0, plate_floor=1.0, edge=0.10) > 0.9)[0][:nf]
    if len(ok):
        sz = (0.08 + 0.04 * rf.uniform(len(ok))) * R
        M.chips(cv, d, px[ok], py[ok], sz, th[ok], stops, rf, alpha=0.45 + 0.05 * rf.uniform(len(ok)), blur_px=0.04 * R, dark=0.25)
    if opts["veil"]:
        ctx.post.append(rim_veil_post(ctx, d, stops, emis, ctx.seed, opts["veil_mean"]))
