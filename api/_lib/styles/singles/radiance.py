# -*- coding: utf-8 -*-
"""designs.singles_radiance: RADIANCE ported from round 1 (wave-y designs/radiance.py, single eye only) on the fx core copy.
Deltas of v3 (brief 3.9): no title, style name or brand line; names per 1.5.7 (kit); a dark moat 1.00-1.06 R so rays never touch the iris;
F3 feather (kit); R 0.305 S. The original docstring follows.

designs.radiance: the RADIANCE family on fx (scratch prototype, NOT repo code). Version 2 (after the art
director's and the engineer's reviews; v1 is kept as designs/_radiance_v1.py).

  Radiance          1 eye, the launch default       1:1 (also 9:19.5 wallpaper)
  Radiance Duo      2 eyes side by side, one line   3:2, their lights meet in a small 4-point star between them
  Radiance Family   3-8 eyes                         1:1 (4:5 for 7-8), short rays per eye, one shared key light

Entry point:  render(eyes, names="", fmt=None, size=None, design=None, ...) -> PIL.Image
  eyes   list of paths or fx.core.Iris objects (the restored 1024 px iris discs /api/compose receives)
  fmt    None (the design's own canvas), "1:1", "3:2", "4:5", "9:19.5", or "tile" (the picker tile, 320 px)
  design None picks by eye count: 1 radiance, 2 radiance_duo, 3-8 radiance_family

THE LIGHT MODEL (one disc). Everything a disc emits is a sum of separable terms, angular profile x radial profile,
assembled in polar space (angle x radius) and sampled once per canvas pixel:
  - ~1100 seeded Gaussian beams in four kinds: fine filaments, streaks, soft shafts and five long hero rays. Each
    beam has its own length, falloff shape and colour (the eye's ring colour at that angle, jittered, whitened by a
    random amount). Beam centres follow a seeded streamer density (fBm, cubed, so 3-5 bundles with quiet dark gaps).
  - A KEY LIGHT per artwork: a seeded direction in the upper half (-150..-30 deg); beams facing it are 2.6x brighter
    and ~1.6x longer than the far side, and the hero rays all sit within 70 deg of it. So no two artworks share the
    same light shape. The family shares one key light (half strength).
  - The rim is thin: rays start at the limbus, a short corona (18%, e-fold 0.014 R, 90% following the streamers and
    the key) and the 1.02 R hairline (16%, champagne white, 75% following them) break into bright and dark arcs (an
    eclipse "diamond ring"), so the 4096 master shows filaments growing out of the limbus, not a neon lip.
  - Colour (radiance palette): the eye's own ring colour, then in LCh a chroma cap (58, 48 for pure yellows), yellows
    turned 10 deg toward gold, lightness capped at 90. Dark brown -> champagne gold. Grey -> steel blue in the
    iris's own cool hue (cool fibres present) or clean silver (truly neutral). A low-chroma khaki ring (C* < 16,
    hue 60-135) never paints khaki: steel if it has cool fibres, silver otherwise.
Beams are summed in the Fourier domain (a Gaussian beam has a closed-form angular spectrum) and every radius gets its
own angular anti-aliasing filter matched to the pixel footprint there, so there are no beads and no moire at any
resolution. Bloom: 4 tiers (0.005, 0.022, 0.08, 0.12 S).

PREVIEW == MASTER. Sizes are in R and S. A master (size != 1024) lays itself out at 1024 first and snaps the discs
exactly as the preview does (pure arithmetic, no grading), then scales that geometry up, so every disc sits on the
preview's own sub-pixel spot: fine rays match to the pixel. No draft change is needed.

Hard rules kept (tests in designs/test_radiance.py): the graded iris is pasted LAST by fx.core.finish; effect colours
come only from the eye's own pixels (ring colours, and for grey / khaki eyes the hue of its own fibres) with the
Radiance fallbacks; float32 layers, fx tone map + dither; every random number from fx.core.Rand (sha256 seeds); sizes
in R and S units; numpy + PIL only; no AI calls, no plates.
"""
from __future__ import annotations

# PORT of work package WP5A (step A): singles_radiance.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists
# (imports, a bounded cache); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures.

import math

import numpy as np
from PIL import Image

from .. import core as C

TWO_PI = 2.0 * math.pi
PREVIEW_SIZE = 1024

# ----------------------------------------------------------------------------- palettes
CHAMPAGNE = "#EDD3A6"             # dark brown fallback target (champagne gold)
ROSE_GOLD = "#EBC2A2"             # second dark brown in a duo
PALE_GOLD = "#E8D9A4"
SILVER = "#E1E5EA"                # neutral silver (a hair cool)
WARM_SILVER = "#EAE3D7"           # second silver in a duo
WARM_WHITE = "#FFF4E0"
LIFT, SAT = 1.7, 1.4
KHAKI = (16.0, 60.0, 135.0)       # ring C* below, hue inside: low-chroma khaki
COOL_HUE = (180.0, 300.0)
COOL_SHARE = 0.25                 # share of chromatic (C* > 4) fibre pixels with a cool hue that makes an eye "steel"
_INFO = C.BoundedCache(64)


def _fibre_info(iris):
    """Colour facts of the eye's own fibres (canonical REF_SIDE grade, 0.45-0.90 R): the share of chromatic
    pixels with a cool hue, and that cool cluster's median hue and chroma. Cached per eye."""
    key = iris.digest
    got = _INFO.get(key)
    if got is not None:
        return got
    fr = iris.graded(C.REF_SIDE)
    sq, tgt = C._tight(fr)
    R = tgt / 2.0
    ax = np.arange(tgt) + 0.5 - R
    rho = np.hypot(ax[None, :], ax[:, None]) / R
    m = (rho > 0.45) & (rho < 0.90)
    lab = C.L.srgb_to_lab(sq[m].astype(np.float64))
    Cc = np.hypot(lab[:, 1], lab[:, 2])
    h = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360.0
    chrom = Cc > 4.0
    cool = chrom & (h > COOL_HUE[0]) & (h < COOL_HUE[1])
    info = {"cool_share": float(cool.sum() / max(chrom.sum(), 1)), "chroma_share": float(chrom.mean()),
            "cool_h": None, "cool_C": 0.0}
    if cool.sum() > 50:
        a, b = np.median(lab[cool, 1]), np.median(lab[cool, 2])
        info["cool_h"] = float(np.degrees(np.arctan2(b, a)) % 360.0)
        info["cool_C"] = float(np.hypot(a, b))
    return _INFO.put(key, info)


def colour_mode(iris):
    """'own' | 'champagne' | 'steel' | 'silver' and why: the Radiance colour rule for one eye."""
    cls = iris.cls
    if cls == "dark_brown":
        return "champagne"
    st = iris.stats
    khaki = cls == "own" and st["C"] < KHAKI[0] and KHAKI[1] <= st["h"] <= KHAKI[2]
    if cls == "grey" or khaki:
        fi = _fibre_info(iris)
        return "steel" if (fi["cool_share"] >= COOL_SHARE and fi["cool_h"] is not None) else "silver"
    return "own"


def _style_lch(p):
    """The Radiance colour discipline in CIELCh: yellows (hue 95-125) turn 10 deg toward gold (smooth ramps, the
    mapping stays monotone), chroma capped at 58 (48 for the pure yellows 90-120 after the turn), L* at 90."""
    Ls, Cc, h = C.lch(np.clip(p, 0.0, 1.0))
    w = C.smoothstep((h - 75.0) / 20.0) * (1.0 - C.smoothstep((h - 125.0) / 20.0))
    h2 = (h - 10.0 * w) % 360.0
    cap = 58.0 - 10.0 * (C.smoothstep((h2 - 82.0) / 8.0) * (1.0 - C.smoothstep((h2 - 120.0) / 8.0)))
    return C.from_lch(np.minimum(Ls, 90.0), np.minimum(Cc, cap), h2).astype(np.float32)


def _tinted(target, ring, lift=1.6, sat=1.3):
    """A clean one-colour palette: target (0..1) with the ring's own per-angle brightness (sqrt, 0.82-1.15)."""
    b = C.boost(ring, lift, sat)
    lum = b @ np.array([0.299, 0.587, 0.114], np.float32)
    mod = np.clip(np.sqrt(lum / max(float(lum.mean()), 1e-6)), 0.82, 1.15)
    p = np.asarray(target, np.float32)[None, :] * mod[:, None]
    return (p / np.maximum(p.max(-1, keepdims=True), 1.0)).astype(np.float32)


def _steel(iris, dh=0.0):
    fi = _fibre_info(iris)
    c = 14.0 + 4.0 * float(np.clip((fi["cool_C"] - 4.0) / 6.0, 0.0, 1.0))
    return C.from_lch(86.0, c, (fi["cool_h"] + dh) % 360.0).astype(np.float32)


def palette(iris, variant=0, away=None):
    """The eye's Radiance colours (360, 3) float32 0..1. variant > 0: the same eye made distinct from its partner
    in a duo: an own-coloured eye turns 16 / 28 / 40 deg in hue AWAY from the partner's hue (away, deg); a fallback
    eye takes its next fallback target (champagne -> pale gold -> rose gold -> warm silver, steel -> warm silver,
    silver -> warm silver -> steel)."""
    mode = colour_mode(iris)
    ring = iris.ring
    if mode == "champagne":
        target, t = ((CHAMPAGNE, 0.45), (PALE_GOLD, 0.70), (ROSE_GOLD, 0.70), (WARM_SILVER, 0.75))[min(variant, 3)]
        return _style_lch(C.mix(C.boost(ring, 1.55, 1.2), C.rgb01(target)[None, :], t))
    if mode == "steel":
        t = (_steel(iris), C.rgb01(WARM_SILVER), _steel(iris, 40.0))[min(variant, 2)]
        return _tinted(t, ring)
    if mode == "silver":
        t = (C.rgb01(SILVER), C.rgb01(WARM_SILVER), C.from_lch(86.0, 14.0, 255.0).astype(np.float32))[min(variant, 2)]
        return _tinted(t, ring)
    p = _style_lch(C.boost(ring, LIFT, SAT))
    if variant:
        own_h = float(C.lch(p.mean(0))[2])
        sign = 1.0 if away is None or ((own_h - away + 180.0) % 360.0 - 180.0) >= 0 else -1.0
        p = C.hue_shift(p, sign * (16.0, 28.0, 40.0)[min(variant, 3) - 1])
    return p


def duo_palettes(A, B):
    """Both eyes' colours. When the DRAWN colours are closer than 10 dE00, one eye takes its next variant (up to 3):
    a fallback eye moves before an own-coloured one (its colour is not its own anyway), else B moves.
    Returns (palette A, palette B, (index of the eye that moved or None, variant))."""
    pa, pb = palette(A), palette(B)
    if C.colour_distance(pa.mean(0), pb.mean(0)) >= 10.0:
        return pa, pb, (None, 0)
    move_a = colour_mode(A) != "own" and colour_mode(B) == "own"
    mover, fixed = (A, pb) if move_a else (B, pa)
    away = float(C.lch(fixed.mean(0))[2])
    for v in (1, 2, 3):
        pm = palette(mover, v, away)
        if C.colour_distance(pm.mean(0), fixed.mean(0)) >= 10.0:
            break
    return (pm, pb, (0, v)) if move_a else (pa, pm, (1, v))


def title_colour(pals):
    """Name colour: the brightest effect colour (over all eyes) mixed 60% toward #F2E6C9."""
    p = np.concatenate([np.asarray(q, np.float32) for q in pals], 0)
    lum = p @ np.array([0.299, 0.587, 0.114], np.float32)
    return C.mix(p[int(np.argmax(lum))], C.rgb01("#F2E6C9"), 0.6)


# ----------------------------------------------------------------------------- the ray field
# beam kinds: count, angular sigma deg (lo, hi, power), e-fold length in R (median, log sd), peak (lo, hi, power),
# whitening (lo, hi), rod-shaped share, colour jitter deg
SOLO_KINDS = (
    ("filament", 560, (0.045, 0.22, 2.6), (0.22, 0.55), (0.20, 0.95, 2.4), (0.00, 0.28), 0.35, 10.0),
    ("streak", 105, (0.10, 0.38, 1.8), (0.44, 0.45), (0.18, 0.60, 1.6), (0.00, 0.18), 0.45, 14.0),
    ("shaft", 24, (0.8, 2.6, 1.0), (0.55, 0.30), (0.07, 0.16, 1.0), (0.00, 0.10), 0.20, 6.0),
    ("hero", 8, (0.08, 0.20, 1.0), (1.00, 0.22), (1.00, 1.50, 1.0), (0.15, 0.35), 0.00, 4.0),
)
# AD round 2c: the length of a ray follows 3 lobes (L(theta) = 0.35 + 0.9 lobe^1.5 R visible), per kind factor, lognormal spread
LEN_KIND = {"filament": 0.88, "streak": 1.0, "shaft": 0.9, "hero": 1.35}
VIS_TO_EFOLD = 2.4                   # a ray is visible to about 2.4 e-folds
HERO_HUE = 12.0                      # deg toward H2 (the analogous accent of the ring hue)
# Radiance Family: fewer, shorter rays, capped at rho 2.2
FAMILY_KINDS = (
    ("filament", 560, (0.035, 0.10, 1.6), (0.22, 0.50), (0.20, 0.90, 2.4), (0.00, 0.28), 0.35, 10.0),
    ("streak", 110, (0.12, 0.40, 1.4), (0.36, 0.45), (0.16, 0.55, 1.6), (0.00, 0.18), 0.45, 14.0),
    ("shaft", 18, (0.9, 2.8, 1.0), (0.50, 0.30), (0.07, 0.15, 1.0), (0.00, 0.10), 0.20, 6.0),
    ("hero", 5, (0.05, 0.11, 1.0), (0.80, 0.20), (0.55, 0.85, 1.0), (0.15, 0.35), 0.00, 4.0),
)
L0, LQ, KL = 0.05, 1.30, 15          # length classes: 0.05 R x 1.3^k, k = 0..14 (0.05 .. 1.97 R)
RHO0 = 0.985                          # the field starts under the disc's own soft edge (alpha 1 inside 0.988)
NR = 288                              # radial samples, sqrt-spaced (finest at the rim)
AA_PX = 0.42                          # angular anti-aliasing sigma, canvas px at each radius
BAND_ROWS = 192                       # sampling band height (memory bound at 4096)
NT_OVER = 2.0                         # angular samples per harmonic kept
TILTS = (-3.0, -1.5, 1.5, 3.0)         # lean of the leaning rays, deg per R
TILT_CLS = 1000
KEY_RANGE = (-150.0, -30.0)           # key light direction, deg (screen: -90 = 12 o'clock)
KEY_HERO = 70.0                       # hero rays within this many deg of the key


def _smooth_size(x, lo=512):
    """The smallest even 5-smooth number >= x (fast FFT length), at least lo."""
    x = max(int(math.ceil(x)), lo)
    best = 1 << int(math.ceil(math.log2(x)))
    p2 = 2
    while p2 < best:
        p3 = p2
        while p3 < best:
            p5 = p3
            while p5 < best:
                if p5 >= x:
                    best = p5
                p5 *= 5
            p3 *= 3
        p2 *= 2
    return best


class Look:
    """The knobs of one design's light (all in R units or display intensity)."""

    def __init__(self, **kw):
        self.kinds = SOLO_KINDS
        self.ray_gain = 0.88
        self.vignette = (0.85, 0.50, 0.62)             # light fades by up to 62% toward the corners
        self.rise = (1.06, 0.08)                     # AD: rays fade in over 1.06-1.14 R (they no longer start at the moat)
        self.corona = (0.18, 0.014, 0.22, 0.26)      # core amp, e-fold; inner glow amp, e-fold (thin: no neon lip)
        self.corona_rise = (0.986, 0.014)
        self.corona_mod = 0.90                       # share of the corona that follows the streamers (and key)
        self.hair = (1.02, 0.010, 0.16)              # hairline radius, sigma, strength
        self.hair_mod = 0.75                         # share of the hairline that follows the streamers (and key)
        self.hair_min_px = 0.55
        self.whiten = (0.22, 0.06)                   # radial whitening near the rim: amount, e-fold
        self.aa_px = AA_PX
        self.cap = None                              # (rho, soft) reach cap for Radiance Family
        self.spread = 1.0                            # rays thin out as rho^-spread
        self.key = 1.0                               # key light strength (family 0.5)
        self.tilt_share = 0.05                       # share of filaments and streaks that lean
        self.bloom = ((0.005, 0.45), (0.022, 0.40), (0.08, 0.20), (0.12, 0.10))   # (sigma in S, weight)
        self.__dict__.update(kw)


class Field:
    """The polar light image of one disc: P (NR, NT, 3) float32 at rho_r = RHO0 + (r du)^2, theta_t = 2 pi t / NT."""
    __slots__ = ("P", "NT", "du", "rho_max", "disc")


CLUMP = (0.12, 2.2, 3.0, 0.55)        # ray density = floor + gain fbm^power (streamers); brightness envelope share


def _clump(rnd, n=4096):
    """Periodic angular density (streamers: where rays bundle) and a slow brightness envelope, both from fBm."""
    f = C.periodic_fbm1d(n, rnd, 4, 5, 0.6).astype(np.float64)
    f = (f - f.min()) / max(f.max() - f.min(), 1e-9)
    dens = CLUMP[0] + CLUMP[1] * f ** CLUMP[2]
    env = C.periodic_fbm1d(n, rnd, 3, 3, 0.5).astype(np.float64)
    env = (env - env.min()) / max(env.max() - env.min(), 1e-9)
    return dens, (1.0 - CLUMP[3]) + CLUMP[3] * env


def _angles(u, dens):
    """Inverse-CDF sampling of angles (rad) from a periodic density on len(dens) cells."""
    n = len(dens)
    cdf = np.concatenate([[0.0], np.cumsum(dens)])
    cdf /= cdf[-1]
    return np.interp(u, cdf, np.arange(n + 1)) * (TWO_PI / n)


def _wrapdeg(a):
    return np.abs((np.asarray(a) + math.pi) % TWO_PI - math.pi) * (180.0 / math.pi)


def make_lobe_fn(rnd, key=None, n=3):
    """lobe(theta) in 0..1: n lobes with a flat top (half width 14-22 deg) and smooth sides (12-20 deg) at seeded angles, one of them near the key light; the
    rays' visible length is 0.35 + 0.9 lobe^1.5 R (AD: about 30 % of the rays reach 0.9 R or more, about 40 % stay within 0.3 R, never a uniform fan;
    measured on the 33 restored eyes: 27 % and 33 %, sd 0.08 - 0.12)."""
    cs = rnd.uniform(n) * TWO_PI
    if key is not None:
        cs[0] = key[0] + math.radians(float(rnd.uniform(1, -25.0, 25.0)[0]))
    w = np.radians(rnd.uniform(n, 14.0, 22.0))
    t = np.radians(rnd.uniform(n, 12.0, 20.0))
    am = rnd.uniform(n, 0.80, 1.0)
    am[0] = 1.0

    def f(c):
        c = np.asarray(c, np.float64)
        out = np.zeros(c.shape)
        for ck, wk, tk, ak in zip(cs, w, t, am):
            dd = np.abs((c - ck + math.pi) % TWO_PI - math.pi)
            x = np.clip((dd - wk) / tk, 0.0, 1.0)
            out = np.maximum(out, ak * (1.0 - x * x * (3.0 - 2.0 * x)))
        return out
    return f


def key_angle(rnd):
    """The artwork's key light direction (rad), seeded, in the upper half of the frame."""
    return math.radians(KEY_RANGE[0] + (KEY_RANGE[1] - KEY_RANGE[0]) * float(rnd.uniform()))


def _beams(rnd, kinds, pal, key=None, towards=None, lobe_fn=None):
    """All beams of one disc: centre angle c (rad), sigma (rad), peak a, length L (R), rod flag, colour (n, 3).
    key = (angle, strength): beams facing it are up to 2.6x brighter and 1.6x longer, heroes sit within 70 deg.
    towards: the partner's direction in a duo; beams facing it are 0.6x as long."""
    out = {k: [] for k in ("c", "s", "a", "L", "rod", "col", "kind")}
    dens, env = _clump(rnd["clump"])
    ne = len(env)
    for ki, (name, n, sd, ln, am, hot, rod_share, jit) in enumerate(kinds):
        r = rnd[name]
        u = r.uniform(n)
        if name == "hero" and key is not None:
            c = key[0] + math.radians(KEY_HERO) * (2.0 * u - 1.0)
        elif name == "shaft":
            c = u * TWO_PI
        else:
            c = _angles(u, dens)
        c = c % TWO_PI
        s = np.radians(sd[0] + (sd[1] - sd[0]) * r.uniform(n) ** sd[2])
        if lobe_fn is not None and name != "shaft":
            vis = (0.35 + 0.90 * lobe_fn(c) ** 1.5) * LEN_KIND[name] * np.exp(0.26 * r.normal(n))
            L = vis / VIS_TO_EFOLD
        elif lobe_fn is not None:
            L = ln[0] * np.exp(ln[1] * r.normal(n))
        else:
            L = ln[0] * np.exp(ln[1] * r.normal(n))
        a = am[0] + (am[1] - am[0]) * r.uniform(n) ** am[2]
        a = a * env[(c * (ne / TWO_PI)).astype(int) % ne]
        if key is not None and key[1]:
            k3 = ((1.0 + np.cos(c - key[0])) / 2.0) ** 3
            a = a * (1.0 + key[1] * (0.55 + 0.90 * k3 - 1.0))
            L = L * (1.0 + key[1] * (0.85 + 0.50 * k3 - 1.0))
        if towards is not None:
            L = L * (0.6 + 0.4 * C.smoothstep((_wrapdeg(c - towards) - 10.0) / 40.0))
        h = hot[0] + (hot[1] - hot[0]) * r.uniform(n) ** 2
        rod = r.uniform(n) < rod_share
        col = C.ring_at(pal, c + np.radians(jit) * r.normal(n))
        if name == "hero" and lobe_fn is not None:                     # the hero rays turn 12 deg toward H2 (brighter, a touch warmer or cooler)
            Lh, Ch, hh = C.lch(col)
            col = C.from_lch(Lh, Ch, hh + HERO_HUE).astype(np.float32)
        m = col.max(-1, keepdims=True)
        col = col + (m - col) * h[:, None].astype(np.float32)          # whiter, not brighter
        for k, v in zip(("c", "s", "a", "L", "rod", "col", "kind"), (c, s, a, L, rod, col, np.full(n, ki))):
            out[k].append(v)
    return {k: np.concatenate(v, 0) for k, v in out.items()}


def _smooth_spectrum(f, M, NT):
    """X_m (m < M) of a smooth periodic profile sampled at len(f) points (theta_j = 2 pi j / n): NT x rfft / n."""
    n = f.shape[0]
    F = np.fft.rfft(np.asarray(f, np.float64), axis=0) / n
    X = np.zeros((M,) + f.shape[1:], np.complex64)
    k = min(M, F.shape[0] - 1)
    X[:k] = F[:k] * NT
    return X


def build_field(disc, pal, rnd, look, rho_max, towards=None, key=None, whiten=None, hole=(10.0, 40.0, 0.45)):
    """The polar light image of one disc (see the module doc). towards: the angle (rad) of a partner disc (duo):
    light there is weighted hole[2] + (1 - hole[2]) smoothstep((|dtheta| - hole[0]) / hole[1]), so the two lights
    still meet between the discs. key: (angle rad, strength). whiten overrides look.whiten (dark brown: 0.12)."""
    R = float(disc.R)
    NT = _smooth_size(NT_OVER * 2.6 * R / look.aa_px)
    M = NT // 2
    rho_max = float(max(rho_max, 1.2))
    du = math.sqrt(rho_max - RHO0) / (NR - 1)
    rho = (RHO0 + (np.arange(NR) * du) ** 2).astype(np.float64)
    x = np.maximum(rho - 1.0, 0.0)
    rise = C.smoothstep((rho - look.rise[0]) / look.rise[1])
    capf = np.ones_like(rho) if not look.cap else C.smoothstep((look.cap[0] - rho) / look.cap[1])
    spread = np.maximum(rho, 1.0) ** -look.spread
    m = np.arange(M, dtype=np.float64)

    b = _beams(rnd, look.kinds, pal, key=key, towards=towards, lobe_fn=getattr(look, "lobe_fn", None))
    kL = np.clip(np.rint(np.log(b["L"] / L0) / math.log(LQ)), 0, KL - 1).astype(int)
    cls = kL * 2 + b["rod"].astype(int)
    # a few filaments and streaks lean (TILTS deg per R), so not every ray points exactly at the pupil centre: each
    # lean group is one more column whose radial profile carries the phase exp(-i m k (rho - 1))
    nb = len(cls)
    tr = rnd["tilt"]
    lean = (tr.uniform(nb) < look.tilt_share) & (b["kind"] <= 1)
    grp = np.minimum((tr.uniform(nb) * len(TILTS)).astype(int), len(TILTS) - 1)
    cls = np.where(lean, TILT_CLS + grp, cls)
    A, D = [], []
    order = np.argsort(cls, kind="stable")
    cls = cls[order]
    ampl = (b["a"] * b["s"] / math.sqrt(TWO_PI) * NT * look.ray_gain)[order]
    colw = (b["col"][order] * ampl[:, None]).astype(np.float32)
    c32 = b["c"][order].astype(np.float32)
    s2 = (0.5 * b["s"][order] ** 2).astype(np.float32)
    ks, starts = np.unique(cls, return_index=True)
    ends = list(starts[1:]) + [len(cls)]
    Are = np.empty((M, len(ks), 3), np.float32)
    Aim = np.empty((M, len(ks), 3), np.float32)
    for m0 in range(0, M, 2048):
        mm = np.arange(m0, min(M, m0 + 2048), dtype=np.float32)[:, None]
        ph = mm * c32[None, :]
        g = np.exp(-(mm * mm) * s2[None, :])
        cs = np.cos(ph)
        cs *= g
        sn = np.sin(ph, out=ph)
        sn *= g
        for j, (a0, a1) in enumerate(zip(starts, ends)):
            Are[m0:m0 + len(mm), j] = cs[:, a0:a1] @ colw[a0:a1]
            Aim[m0:m0 + len(mm), j] = -(sn[:, a0:a1] @ colw[a0:a1])
    Ab = Are + 1j * Aim
    A = [Ab[:, j].astype(np.complex64) for j in range(len(ks)) if ks[j] < TILT_CLS]
    lean_cols = []                                   # (angular spectrum (M, 3), radial x phase (M, NR))
    Lb = b["L"][order]
    for j, k in enumerate(ks):
        if k >= TILT_CLS:
            Lg = float(np.median(Lb[starts[j]:ends[j]]))
            dg = (np.exp(-x / Lg) * rise * capf * spread).astype(np.float32)
            kk = math.radians(TILTS[k - TILT_CLS])
            ph = np.outer(m, kk * x).astype(np.float32)
            lean_cols.append((Ab[:, j].astype(np.complex64), (np.cos(ph) - 1j * np.sin(ph)).astype(np.complex64) * dg[None, :]))
            del ph
            continue
        Lk = L0 * LQ ** (k // 2)
        d = np.exp(-(x / (1.2 * Lk)) ** 1.8) if k % 2 else np.exp(-x / Lk)
        D.append(d * rise * capf * spread)
    # corona (follows the streamers) and the hairline (breaks into arcs with them), both smooth in angle
    ns = 2048
    th_s = np.arange(ns) * (TWO_PI / ns)
    pal_s = C.ring_at(pal, th_s).astype(np.float64)
    dens = np.zeros(ns)
    j = np.rint(b["c"] / TWO_PI * ns).astype(int) % ns
    np.add.at(dens, j, b["a"] * b["s"])
    kern = np.exp(-0.5 * (np.minimum(np.arange(ns), ns - np.arange(ns)) / (ns * 3.5 / 360.0)) ** 2)
    dens = np.real(np.fft.ifft(np.fft.fft(dens) * np.fft.fft(kern / kern.sum())))
    dens = dens / max(dens.max(), 1e-9)
    cm = look.corona_mod
    A.append(_smooth_spectrum(pal_s * ((1.0 - cm) + cm * dens)[:, None], M, NT))
    crise = C.smoothstep((rho - look.corona_rise[0]) / look.corona_rise[1])
    D.append(crise * capf * (look.corona[0] * np.exp(-x / look.corona[1]) + look.corona[2] * np.exp(-x / look.corona[3])))
    if look.hair and look.hair[2]:
        at, sg, st = look.hair
        s_eff = max(sg, look.hair_min_px / R)
        wob = ((1.0 - look.hair_mod) + look.hair_mod * dens) * (0.85 + 0.15 * C.periodic_fbm1d(ns, rnd["hair"], 3, 5))
        hot = pal_s + (C.rgb01(WARM_WHITE).astype(np.float64)[None, :] - pal_s) * 0.5
        A.append(_smooth_spectrum(hot * wob[:, None], M, NT))
        D.append(st * (sg / s_eff) * np.exp(-0.5 * ((rho - at) / s_eff) ** 2) * capf)
    A = np.stack(A, 1)                                           # (M, K, 3)
    D = np.stack(D, 0).astype(np.complex64)                      # (K, NR)
    arc = 1.0 / (R * np.maximum(rho, 1.0))
    G = np.exp(-0.5 * np.outer(m * m, (look.aa_px * arc) ** 2)).astype(np.float32)   # (M, NR) angular AA
    wh = look.whiten if whiten is None else whiten
    w = (wh[0] * np.exp(-x / wh[1])).astype(np.float32)
    ang = None
    if towards is not None:
        th_t = np.arange(NT + 1) * (TWO_PI / NT)
        ang = (hole[2] + (1.0 - hole[2]) * C.smoothstep((_wrapdeg(th_t - towards) - hole[0]) / hole[1])).astype(np.float32)
    P = np.empty((NR, NT + 1, 3), np.float32)
    X = np.zeros((M + 1, NR), np.complex64)
    for c in range(3):
        X[:M] = A[:, :, c] @ D
        for Ag, DEg in lean_cols:
            X[:M] += Ag[:, c][:, None] * DEg
        X[:M] *= G
        P[:, :NT, c] = np.fft.irfft(X, n=NT, axis=0).T
    P[:, NT] = P[:, 0]
    np.maximum(P, 0.0, out=P)
    mx = np.maximum(np.maximum(P[..., 0], P[..., 1]), P[..., 2])
    mx *= w[:, None]
    for c in range(3):
        pc = P[..., c]
        pc *= (1.0 - w)[:, None]
        pc += mx
        if ang is not None:
            pc *= ang[None, :]
    P[-1] = 0.0
    f = Field()
    f.P, f.NT, f.du, f.rho_max, f.disc = P, NT, du, rho_max, disc
    return f


def sample_field(field, light, ctx, wmap=None):
    """Bilinear lookup of the polar image at every canvas pixel within reach (row bands), added into light (H, W, 3),
    each pixel weighted by wmap (H, W) when given (the family's territories)."""
    d = field.disc
    NT, du = field.NT, field.du
    nr = field.P.shape[0]
    stride = NT + 1
    flat = field.P.reshape(-1, 3)
    reach = field.rho_max * d.R * ctx.stretch
    x0, y0 = max(0, int(d.cx - reach)), max(0, int(d.cy - reach))
    x1, y1 = min(ctx.W, int(math.ceil(d.cx + reach)) + 1), min(ctx.H, int(math.ceil(d.cy + reach)) + 1)
    inv_du = np.float32(1.0 / du)
    inv_R = np.float32(1.0 / d.R)
    kt = np.float32(NT / TWO_PI)
    band = int(min(BAND_ROWS, max(16, reach / 6)))
    for r0 in range(y0, y1, band):
        r1 = min(y1, r0 + band)
        dy0 = max(0.0, max(r0 - d.cy, d.cy - r1))
        half = math.sqrt(max(reach * reach - dy0 * dy0, 0.0)) if ctx.stretch == 1.0 else reach
        xa, xb = max(x0, int(d.cx - half)), min(x1, int(math.ceil(d.cx + half)) + 1)
        if xa >= xb:
            continue
        if ctx.stretch == 1.0:
            dx = (np.arange(xa, xb, dtype=np.float32) + np.float32(0.5 - d.cx))[None, :]
            dy = (np.arange(r0, r1, dtype=np.float32) + np.float32(0.5 - d.cy))[:, None]
            th = np.arctan2(dy, dx)
            u = dx * dx + dy * dy
            np.sqrt(u, out=u)
            u *= inv_R
        else:
            u, th = C.polar(ctx.W, ctx.H, d.cx, d.cy, d.R, ctx.stretch, (xa, r0, xb, r1))
        u -= np.float32(RHO0)
        np.maximum(u, 0.0, out=u)
        np.sqrt(u, out=u)
        u *= inv_du
        np.minimum(u, np.float32(nr - 1.001), out=u)
        ri = u.astype(np.int32)
        u -= ri
        th *= kt
        th += np.float32(NT) * (th < 0)
        ti = th.astype(np.int32)
        np.minimum(ti, NT - 1, out=ti)
        th -= ti
        ri *= stride
        ri += ti
        idx = ri.ravel()
        wt = th.reshape(-1, 1)
        wr = u.reshape(-1, 1)
        a = np.take(flat, idx, axis=0)
        b = np.take(flat, idx + 1, axis=0)
        b -= a
        b *= wt
        a += b
        idx += stride
        c = np.take(flat, idx, axis=0)
        np.take(flat, idx + 1, axis=0, out=b)
        b -= c
        b *= wt
        c += b
        c -= a
        c *= wr
        a += c
        if wmap is not None:
            a *= wmap[r0:r1, xa:xb].reshape(-1, 1)
        light[r0:r1, xa:xb] += a.reshape(r1 - r0, xb - xa, 3)
    return light


def far_rho(disc, W, H):
    """Distance from the disc centre to the farthest canvas corner, in R."""
    return max(math.hypot(x - disc.cx, y - disc.cy) for x in (0, W) for y in (0, H)) / disc.R


def _band_dim(light, ctx, y_c, half, floor):
    """In place: light dimmed to floor round the row y_c (a Gaussian band of sigma half px), for a caption line."""
    y = np.arange(ctx.H, dtype=np.float32) + 0.5
    f = 1.0 - (1.0 - floor) * np.exp(-0.5 * ((y - y_c) / half) ** 2)
    light *= f.astype(np.float32)[:, None, None]


def _vignette(light, ctx, e0, span, depth):
    """In place: the light fades by depth toward the corners (e = distance from the canvas centre over the half
    sides: 1 at the edge middles, 1.41 at the corners; full strength inside e0, depth reached at e0 + span)."""
    ex = ((np.arange(ctx.W, dtype=np.float32) + 0.5) / np.float32(ctx.W / 2.0) - 1.0) ** 2
    ey = ((np.arange(ctx.H, dtype=np.float32) + 0.5) / np.float32(ctx.H / 2.0) - 1.0) ** 2
    for r0 in range(0, ctx.H, 512):
        r1 = min(ctx.H, r0 + 512)
        e = np.sqrt(ey[r0:r1, None] + ex[None, :])
        v = 1.0 - np.float32(depth) * C.smoothstep((e - np.float32(e0)) / np.float32(span)).astype(np.float32)
        light[r0:r1] *= v[..., None]


def _upsample_rows(a, W, H, f, r0, r1):
    """Rows r0:r1 of C.upsample(a, W, H, f) (bicubic, PIL mode F, clipped at 0) computed from a source window 2 source rows wider than the band, so
    the band equals the full upsample (the window edge effects are cropped away)."""
    h, w = a.shape[:2]
    ra, rb = max(0, r0 - 2 * f), min(h * f, r1 + 2 * f)
    im = Image.fromarray(a, "F").resize((w * f, rb - ra), Image.BICUBIC, box=(0.0, ra / float(f), float(w), rb / float(f)))
    out = np.asarray(im, np.float32)[r0 - ra:r1 - ra, :W]
    return np.maximum(out, 0.0)


def bloom_and_screen(cv, light, ctx, look, post_glow=None):
    """light + glow (blurred copies at look.bloom sigmas, on one reduced grid) -> faded under the caption ->
    screened onto cv."""
    s_min = min(s for s, _ in look.bloom) * ctx.S
    f = 1
    while s_min / (2 * f) >= 2.0 and f < 32:
        f *= 2
    red = C.box_reduce(light, f)
    glow = np.zeros_like(red)
    for s, wgt in look.bloom:
        glow += C.blur(red, s * ctx.S / f) * np.float32(wgt)
    if f > 1:
        for c in range(3):                                   # one channel and one 512-row band at a time: a full upsample is 200 MB of temporaries at 4096
            gc = np.ascontiguousarray(glow[..., c])
            for r0 in range(0, ctx.H, 512):
                r1 = min(ctx.H, r0 + 512)
                light[r0:r1, :, c] += _upsample_rows(gc, ctx.W, ctx.H, f, r0, r1)
    else:
        light += glow
    del glow, red
    if post_glow is not None:
        post_glow(light)
    if look.vignette:
        _vignette(light, ctx, *look.vignette)
    if ctx.wall:
        y = (np.arange(ctx.H, dtype=np.float32) + 0.5) / np.float32(ctx.H)
        # the lock-screen clock (top fifth): 35%; the dock and home bar (bottom 15%): 70%
        fz = (0.35 + 0.65 * C.smoothstep((y - 0.04) / 0.18)) * (1.0 - 0.30 * C.smoothstep((y - 0.85) / 0.15))
        light *= fz.astype(np.float32)[:, None, None]
        if ctx.opts.get("wall_name_y"):
            _band_dim(light, ctx, ctx.opts["wall_name_y"], 0.022 * ctx.H, 0.45)
    for r0 in range(0, ctx.H, 256):
        C.screen(cv[r0:r0 + 256], light[r0:r0 + 256])


# ----------------------------------------------------------------------------- effects: effect(cv, ctx)
def _rnd(ctx, eye):
    return {k: ctx.rand("radiance/" + k, eye) for k in ("filament", "streak", "shaft", "hero", "hair", "clump", "tilt")}


def _lobes(ctx, eye, key):
    return make_lobe_fn(ctx.rand("radiance/lobes", eye), key)


def _whiten_for(iris, look):
    return (0.12, look.whiten[1]) if colour_mode(iris) == "champagne" else None


def fx_radiance(cv, ctx):
    """Single Radiance: thin own-colour rays from the limbus (round 1 engine) with the v3 moat."""
    look = ctx.opts.get("look") or Look(vignette=(0.78, 0.50, 0.80))            # v3: the outer 0.02 S stays under 3 % mean luminance (T8)
    ctx.stretch = 1.15 if ctx.wall else 1.0
    light = np.zeros((ctx.H, ctx.W, 3), np.float32)
    d = ctx.discs[0]
    pal = palette(d.iris)
    key = (key_angle(ctx.rand("radiance/key", d.index)), look.key)
    if getattr(look, "lobe_fn", None) is None and ctx.opts.get("radiance", {}).get("lobes", True):
        look.lobe_fn = _lobes(ctx, d.index, key)
    fld = build_field(d, pal, _rnd(ctx, d.index), look, far_rho(d, ctx.W, ctx.H) + 0.05, key=key, whiten=_whiten_for(d.iris, look))
    sample_field(fld, light, ctx)
    del fld
    # v3 moat: the light is pulled down to MOAT at the limb and recovers by 1.10 R (rays start after a hair of dark); applied to the rays
    # and again after the bloom, so the glow of the rays never fills the dark ring
    rs = ctx.opts.get("radiance", {})
    moat = float(rs.get("moat", 0.18))
    x0, y0 = max(0, int(d.cx - 1.16 * d.R)), max(0, int(d.cy - 1.16 * d.R))
    x1, y1 = min(ctx.W, int(d.cx + 1.16 * d.R) + 2), min(ctx.H, int(d.cy + 1.16 * d.R) + 2)
    rho, _ = C.polar(ctx.W, ctx.H, d.cx, d.cy, d.R, 1.0, (x0, y0, x1, y1))
    f = (moat + (1.0 - moat) * C.smoothstep((rho - 1.0) / 0.08))[..., None].astype(np.float32)
    light[y0:y1, x0:x1] *= f
    from . import kit as _K
    _K.text_fade(light, ctx)

    def post_glow(lt):
        lt[y0:y1, x0:x1] *= f
    bloom_and_screen(cv, light, ctx, look, post_glow=post_glow)
    ctx.log["radiance"] = {"mode": colour_mode(d.iris), "moat": moat}
