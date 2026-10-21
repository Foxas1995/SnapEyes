# -*- coding: utf-8 -*-
"""lumen.common: what the five looks of the light family share. The colour of an eye (deep, mid and hot per ring angle, the eye's own glow colour and its
partner hue), reduced grids and banded light layers, resolution independent noise (fBm, ridges, domain warping), a star field with a real looking spread
of magnitudes and colour temperatures, diffraction spikes, grain.

One copy of the two laboratory rounds of 2026-10-20 (the five looks of one eye and the cosmos round), which each repeated the colour and grid helpers. The
rules of a single eye hold for every piece here: an effect draws into the float canvas only and never sees the disc, the iris is pasted LAST by the family's
render (so inside r <= 0.974 R the picture IS the graded disc), sizes are in R and S units so a 4096 px master is its 1024 px preview drawn finer, every
random number comes from core.Rand (sha256 seeds), numpy and Pillow only. An effect reads its discs and irises as LISTS (ctx.discs, ctx.irises), so the
looks that the pair and family styles take over (Nebula and Supernova) draw round several irises with the same code.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from .. import core as C
from ..singles import kit as K

F32 = np.float32
TWO_PI = 2.0 * math.pi
WHITE_HOT = C.rgb01("#FFF4E0")
LUMW = np.array([0.299, 0.587, 0.114], F32)


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def wrap180(a):
    return (np.asarray(a, np.float64) + 180.0) % 360.0 - 180.0


def luma(a):
    return np.asarray(a, F32) @ LUMW


# ----------------------------------------------------------------------------- the colour of an eye
def _smooth_lab(ring, sigma_bins):
    """The ring (360, 3) as smoothed (L, a, b) per angle: smoothing the Lab components (never the hue itself) keeps a hue average honest."""
    Ls, Cs, hs = C.lch(ring)
    a = Cs * np.cos(np.radians(hs))
    b = Cs * np.sin(np.radians(hs))
    m = np.stack([Ls, a, b], 1)
    m = C._circular_smooth(m, sigma_bins, int(3 * sigma_bins))
    Lm, am, bm = m[:, 0], m[:, 1], m[:, 2]
    return Lm, np.hypot(am, bm), np.degrees(np.arctan2(bm, am)) % 360.0


def hue_cap(h, cap=56.0, yellow=44.0):
    """Chroma ceiling by hue: yellows and olives (hue 85 to 125) never get the full ceiling, they turn sulfur first."""
    w = smooth((np.asarray(h) - 80.0) / 8.0) * (1.0 - smooth((np.asarray(h) - 128.0) / 8.0))
    return cap - (cap - yellow) * w


def stops(iris, sigma=9.0, white=0.5):
    """(3, 360, 3) float32: deep, mid and hot colour per ring angle. The eye's own ring colour lifted to a light clean accent (mid, L* 58 to 78), a darker
    richer partner (deep) and a warm white partner (hot). Dark brown eyes take the studio's copper ramp (kit.ramp_stops, the one of Powder Burst and Celestial
    Gold). A grey or very dark eye keeps ITS hue at a modest chroma (a tinted silver): the hue is the mean ring hue, the per angle hue only where the ring has
    chroma enough to be trusted. Yellows and olives turn 12 degrees toward gold and a touch darker (never sulfur)."""
    st = iris.stats
    if st["class"] == "dark_brown":
        return K.ramp_stops(iris)
    ring = iris.ring
    Ls, Cs, hs = _smooth_lab(ring, sigma)
    Lm, Cm, hm = st["L"], st["C"], st["h"]
    wC = smooth((Cs - 3.0) / 7.0)
    h = (hm + wrap180(hs - hm) * wC) % 360.0
    w_ol = smooth((h - 85.0) / 8.0) * (1.0 - smooth((h - 133.0) / 8.0)) * float(smooth((Cm - 12.0) / 8.0))
    h = (h - 12.0 * w_ol) % 360.0
    c_key = np.clip(2.0 * Cs + 6.0, 15.0, hue_cap(h))
    L_mid = 69.0 + 9.0 * np.clip((Ls - Lm) / 12.0, -1.0, 1.0) - 6.0 * w_ol
    mid = C.from_lch(L_mid, c_key, h).astype(F32)
    deep = C.from_lch(np.maximum(L_mid - 31.0, 8.0), np.minimum(c_key * 0.95, 40.0), h - 4.0).astype(F32)
    hot = C.mix(C.from_lch(L_mid + 9.0, c_key * 0.75, h), WHITE_HOT[None, :], white)
    return np.stack([deep, mid, hot]).astype(F32)


def mean_colour(stp, which=1):
    """The circular mean of one stop (0 deep, 1 mid, 2 hot) of stops(): one colour (3,) float32."""
    return stp[which].mean(0).astype(F32)


def ramp3(stp, th, level):
    """deep -> mid -> hot at angle(s) th (radians) for a light level 0..1 (the Powder Burst mapping): (..., 3) float32."""
    if stp[0].shape[0] == stp[1].shape[0] == stp[2].shape[0]:
        deep, mid, hot = C.ring_at_stack((stp[0], stp[1], stp[2]), th)          # the same bins and weights for the three: ring_at to the bit
    else:
        deep, mid, hot = C.ring_at(stp[0], th), C.ring_at(stp[1], th), C.ring_at(stp[2], th)
    lv = np.asarray(level, F32)[..., None]
    a = np.clip(lv * 2.0, 0.0, 1.0)
    b = np.clip(lv * 2.0 - 1.0, 0.0, 1.0)
    return ((deep * (1 - a) + mid * a) * (1 - b) + hot * b).astype(F32)


def tone(stp, k, which=0):
    """A tonal ground colour: the eye's own deep (or mid) colour at the fraction k of its brightness (3,) float32."""
    return (mean_colour(stp, which) * F32(k)).astype(F32)


def lch_rgb(L_, c, h):
    return C.from_lch(float(L_), float(c), float(h) % 360.0).astype(F32)


def eye_hue(iris):
    """(hue deg, chroma, family) of the eye: 'grey' (no hue to speak of, chroma under 4.5), 'warm' (dark brown, very dark, amber, brown, hazel under
    hue 90), 'olive' (hue 90 to 115), 'green' (115 to 175), 'cool' (blue and grey blue, 175 to 330). A very dark eye (L* under 26) is warm whatever
    its hue reads: its few coloured pixels are brown."""
    st = iris.stats
    h, c = float(st["h"]), float(st["C"])
    if st["class"] == "dark_brown":
        return h, c, "warm"
    if c < 4.5:
        return h, c, "grey"
    if float(st["L"]) < 26.0:
        return h, c, "warm"
    if 90.0 <= h < 115.0:
        return h, c, "olive"
    if 115.0 <= h <= 175.0:
        return h, c, "green"
    if 175.0 < h < 330.0:
        return h, c, "cool"
    return h, c, "warm"


def own_colour(iris, L_=64.0, cmin=26.0, cmax=58.0, k=1.6):
    """The eye's own light colour for a cosmic glow: its hue at a lifted chroma (a grey or a pale eye still glows in its own hue; a truly neutral one
    takes a steel blue), copper amber for dark and very dark eyes."""
    h, c, fam = eye_hue(iris)
    if fam == "warm" and (iris.stats["class"] == "dark_brown" or float(iris.stats["L"]) < 26.0):
        return lch_rgb(L_ - 6.0, 52.0, 56.0)
    if fam == "grey":
        return lch_rgb(L_ + 4.0, 15.0, 225.0)
    return lch_rgb(L_, float(np.clip(c * k, cmin, cmax)), h)


def partner_hue(iris):
    """The partner hue of the eye (deg) and how it was chosen. The eye's own second colour when it has one (the collarette, kit.secondary_hue: a
    blue eye with an amber ring round the pupil takes amber), else a turn of the eye's hue that astronomers' pictures use with it: cool eyes toward
    violet, greens toward teal, warm eyes toward teal blue (the warm and cool pair of a nebula)."""
    h, c, fam = eye_hue(iris)
    try:
        _rgb, how, h2 = K.secondary_hue(iris)
    except Exception:  # noqa: BLE001  a synthetic eye without a usable collarette
        how, h2 = "analogous", (h + 25.0) % 360.0
    if how == "collarette" and abs(float(wrap180(h2 - h))) >= 35.0:
        return float(h2), "collarette"
    if fam == "cool":
        return (h + 62.0) % 360.0, "turn"              # blue toward violet
    if fam == "green":
        return (h + 160.0) % 360.0, "turn"             # green and purple
    if fam == "olive":
        return (h + 185.0) % 360.0, "turn"             # olive and violet
    if fam == "grey":
        return 262.0, "turn"                           # a grey eye: a cool blue violet
    return 218.0, "turn"                               # warm eyes: teal blue (the classic warm and cool nebula)


# ----------------------------------------------------------------------------- grids and banded light layers
def grid_factor(W, H, cells=512):
    """The reduction factor that gives a grid of `cells` on the long side (at most 8): the same grid at 1024 and at 4096 px, so a master is its preview
    drawn finer."""
    return int(min(8, max(1, round(max(W, H) / float(cells)))))


def band_rows(y0, y1, step=128):
    for r0 in range(y0, y1, step):
        yield r0, min(y1, r0 + step)


def window(ctx, d, reach_r):
    """(x0, y0, x1, y1): the canvas window within reach_r x R of the disc centre."""
    r = reach_r * d.R
    return (max(0, int(d.cx - r)), max(0, int(d.cy - r)), min(ctx.W, int(math.ceil(d.cx + r)) + 1), min(ctx.H, int(math.ceil(d.cy + r)) + 1))


def up_rows(a, W, H, f, r0, r1):
    """Rows r0:r1 of the bicubic upsampling of one 2-D reduced array a (clipped at 0), made from a window of a only."""
    h, w = a.shape[:2]
    if f == 1:
        return np.maximum(np.asarray(a[r0:r1, :W], F32), 0.0)
    ra, rb = max(0, r0 - 2 * f), min(h * f, r1 + 2 * f)
    ga, gb = max(0, ra // f - 3), min(h, -(-rb // f) + 3)           # the grid rows the window needs (a margin of 3 for the bicubic support)
    src = np.ascontiguousarray(a[ga:gb], F32)
    im = Image.fromarray(src, "F").resize((w * f, rb - ra), Image.BICUBIC, box=(0.0, ra / float(f) - ga, float(w), rb / float(f) - ga))
    return np.maximum(np.asarray(im, F32)[r0 - ra:r1 - ra, :W], 0.0)


def screen_grid(cv, light, f, mode="screen", fade=None, k=1.0):
    """light: a reduced grid (gh, gw, 3) covering the WHOLE canvas at the factor f. Upsample it band by band and screen (or add) it into cv; mode "mul"
    multiplies cv by the upsampled light (a transmission layer). fade(band, r0): an optional in place multiplier of the upsampled band (text boxes, the
    wallpaper zones, the canvas edge)."""
    H, W = cv.shape[:2]
    planes = [np.ascontiguousarray(light[..., c]) for c in range(3)]
    for r0 in range(0, H, 256):
        r1 = min(H, r0 + 256)
        band = np.empty((r1 - r0, W, 3), F32)
        for c in range(3):
            band[..., c] = up_rows(planes[c], W, H, f, r0, r1)
        if fade is not None:
            fade(band, r0)
        if k != 1.0:
            band *= F32(k)
        if mode == "screen":
            C.screen(cv[r0:r1], band)
        elif mode == "mul":
            cv[r0:r1] *= band
        else:
            cv[r0:r1] += band
    return cv


def fades_for(ctx):
    """The fades every full canvas layer of light takes: the customer's text box, the wallpaper's lock screen zones and the canvas edge (kit.text_fade,
    kit.wall_fade, kit.edge_fade: light fades over the last 0.035 S, so an artwork never looks cropped). The ground, the paper, takes none."""
    def fade(band, r0):
        K.wall_fade(band, ctx, y0=r0)
        K.text_fade(band, ctx, y0=r0)
        K.edge_fade(band, ctx, y0=r0)
    return fade


def ground_grid(g, cx, cy, inner, outer, reach=0.95, power=0.9, rows=None):
    """kit.fill_radial_bg on the reduced grid g (core.Grid): (g.h, g.w, 3) float32, `inner` at (cx, cy) to `outer` at reach x the long side. rows: (r0, r1),
    only those grid rows (a band)."""
    r0, r1 = (0, g.h) if rows is None else rows
    x = ((np.arange(g.w, dtype=F32) + F32(0.5)) * F32(g.f) - F32(cx))[None, :]
    y = ((np.arange(r0, r1, dtype=F32) + F32(0.5)) * F32(g.f) - F32(cy))[:, None]
    t = np.clip(np.sqrt(x * x + y * y) / F32(reach * max(g.W, g.H)), 0.0, 1.0)
    t = (t * t * (3.0 - 2.0 * t)) ** F32(power)
    a, b = np.asarray(inner, F32), np.asarray(outer, F32)
    return (a[None, None, :] + (b - a)[None, None, :] * t[..., None]).astype(F32)


def grain(cv, rnd, amp=0.012, step=256):
    """Luminance grain on the canvas, in place, band by band: triangular noise (the sum of two uniform draws) with a standard deviation of amp x sqrt(v), v the
    brightest channel, so the blacks stay black and a glow gets the tooth of a photographic print. Drawn before the iris is pasted: the iris is never grained."""
    H, W = cv.shape[:2]
    k0 = F32(amp / 0.408)
    for r0 in range(0, H, step):
        r1 = min(H, r0 + step)
        n = rnd.g.random((r1 - r0, W), dtype=F32) + rnd.g.random((r1 - r0, W), dtype=F32) - F32(1.0)
        v = np.clip(cv[r0:r1].max(-1), 0.0, 1.0)
        n *= k0 * np.sqrt(v)
        cv[r0:r1] += n[..., None]
    return cv


def grid_xy(g):
    """Canvas px of the grid pixels' centres: (x (1, gw), y (gh, 1)) float32."""
    f = F32(g.f)
    x = ((np.arange(g.w, dtype=F32) + F32(0.5)) * f)[None, :]
    y = ((np.arange(g.h, dtype=F32) + F32(0.5)) * f)[:, None]
    return x, y


def polar_of(x, y, d):
    """rho (R units) and theta (radians, screen clockwise) of canvas positions round a disc."""
    dx, dy = x - F32(d.cx), y - F32(d.cy)
    return (np.sqrt(dx * dx + dy * dy) / F32(d.R)).astype(F32), np.arctan2(dy, dx).astype(F32)


def annulus(ctx, d, r_lo, r_hi, step=128):
    """Bands of the canvas that hold the annulus r_lo..r_hi (R units) round the disc: yields (ra, rb, x0, x1, rho, theta, mask) for each band, rho and theta
    float32 over the window of the band, mask the pixels inside the annulus (the expensive terms are then computed on those pixels only)."""
    x0, y0, x1, y1 = window(ctx, d, r_hi + 0.02)
    for ra, rb in band_rows(y0, y1, step):
        rho, th = C.polar(ctx.W, ctx.H, d.cx, d.cy, d.R, 1.0, (x0, ra, x1, rb))
        m = (rho >= r_lo) & (rho <= r_hi)
        if m.any():
            yield ra, rb, x0, x1, rho, th, m


# ----------------------------------------------------------------------------- noise (the same pattern at any grid size)
def smooth_noise(gw, gh, cells, rnd, octaves=3, gain=0.55):
    """Seeded smooth 2-D noise 0..1 on a gw x gh grid with `cells` cells across the short side (the same pattern at any grid size), fBm of octaves."""
    acc = np.zeros((gh, gw), F32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        acc += F32(amp) * C.value_noise2d(gw, gh, cells * (2 ** o), rnd)
        tot += amp
        amp *= gain
    return np.clip(acc / tot, 0.0, 1.0)


def fbm(gw, gh, cells, rnd, octaves=5, gain=0.55, lac=2.0):
    """Seeded smooth fBm 0..1 on a gw x gh grid, `cells` value noise cells across the SHORT side for the first octave (core.value_noise2d)."""
    acc = np.zeros((gh, gw), F32)
    amp, tot = 1.0, 0.0
    c = float(cells)
    for _ in range(octaves):
        acc += F32(amp) * C.value_noise2d(gw, gh, c, rnd)
        tot += amp
        amp *= gain
        c *= lac
    acc *= F32(1.0 / tot)
    return acc


def fbm_master(gw, gh, cells, rnd, octaves, gain, S, extra=0, gain_extra=None, pad_share=0.0, min_px=8.0, ref=1024):
    """fbm with up to `extra` finer octaves that only a master draws: an extra octave is added where its cell spans at least min_px canvas pixels at this
    size and fewer at the reference size (the 1024 px preview), so the preview is the plain fbm and a master its own finer self (the finer octaves average out
    when it is reduced). The extra octaves take their own gain (gain_extra) after the last base octave's amplitude; the base octaves keep the plain fbm's
    weights (the sum is not renormalized by them: the callers stretch the field by its quantiles). pad_share: the padding of the grid as a share of its short
    side (the cells are counted across the padded grid)."""
    acc = fbm(gw, gh, cells, rnd, octaves, gain)
    if extra <= 0:
        return acc
    g2 = gain if gain_extra is None else gain_extra
    tot = sum(gain ** o for o in range(octaves))
    amp = gain ** (octaves - 1) / tot
    span = (1.0 + 2.0 * pad_share) * float(S)
    for o in range(octaves, octaves + int(extra)):
        amp *= g2
        c = float(cells) * 2.0 ** o
        px, px_ref = span / c, (1.0 + 2.0 * pad_share) * float(ref) / c
        n = C.value_noise2d(gw, gh, c, rnd)                          # drawn whether or not it is used: the numbers after it do not depend on the size
        if px >= min_px and px_ref < min_px:
            acc += F32(amp) * (n - F32(0.5))
    return acc


def stretch01(a, lo=0.02, hi=0.98, sample=8):
    """Rescale an fBm field so that its lo and hi quantiles (on a subsample) map to 0 and 1, clipped: fBm sums crowd round 0.5."""
    s = np.asarray(a[::sample, ::sample], F32).ravel()
    q0, q1 = np.quantile(s, [lo, hi])
    out = (a - F32(q0)) * F32(1.0 / max(float(q1 - q0), 1e-6))
    np.clip(out, 0.0, 1.0, out=out)
    return out


def ridge(a, p=2.0):
    """Ridged noise: 1 at the middle of the range, thin bright lines where the field crosses 0.5."""
    return np.clip(1.0 - np.abs(2.0 * a - 1.0), 0.0, 1.0) ** F32(p)


def bilerp(tex, x, y):
    """Bilinear sample of a 2-D float32 texture at float positions (x, y) in texture pixels (clamped)."""
    h, w = tex.shape
    x = np.clip(x, 0.0, w - 1.001).astype(F32)
    y = np.clip(y, 0.0, h - 1.001).astype(F32)
    x0 = x.astype(np.int32)
    y0 = y.astype(np.int32)
    fx = x - x0
    fy = y - y0
    t = tex.ravel()
    i = y0 * w + x0
    a = t[i]
    b = t[i + 1]
    top = a + (b - a) * fx
    c = t[i + w]
    e = t[i + w + 1]
    bot = c + (e - c) * fx
    return top + (bot - top) * fy


def bilerp_banded(tex, X, Y, step=256):
    """bilerp over full coordinate arrays X, Y (same shape, 2-D), 256 rows at a time: the ten temporaries of a lookup stay a band in size."""
    out = np.empty(X.shape, F32)
    for r0 in range(0, X.shape[0], step):
        out[r0:r0 + step] = bilerp(tex, X[r0:r0 + step], Y[r0:r0 + step])
    return out


def pad_of(gw, gh, share=0.12):
    """The margin (grid px) of a padded noise texture: a share of the grid's short side, so the pattern does not depend on the grid's size."""
    return int(math.ceil(share * min(gw, gh)))


def fbm_pad(gw, gh, pad, cells, rnd, octaves=5, gain=0.55):
    """fbm on the grid grown by pad on every side (gh + 2 pad, gw + 2 pad): a warped lookup never runs off its edge."""
    return fbm(gw + 2 * pad, gh + 2 * pad, cells, rnd, octaves, gain)


def warp_pad(tex, pad, wx, wy, amp_px, gw, gh):
    """A padded texture sampled at the grid's own pixels moved by (amp wx, amp wy): (gh, gw) float32, 256 rows at a time (small temporaries)."""
    out = np.empty((gh, gw), F32)
    xr = np.arange(gw, dtype=F32)[None, :] + F32(pad)
    for r0 in range(0, gh, 256):
        r1 = min(gh, r0 + 256)
        xs = xr + F32(amp_px) * wx[r0:r1]
        ys = np.arange(r0, r1, dtype=F32)[:, None] + F32(pad) + F32(amp_px) * wy[r0:r1]
        out[r0:r1] = bilerp(tex, xs, ys)
    return out


# ----------------------------------------------------------------------------- stars
# colour temperatures of stars (K) and their display colours: the blackbody of each temperature in sRGB, a little richer (a star field looks white with
# a spread of warm and cool points, never a rainbow)
_TEMPS = np.array([2800, 3500, 4200, 5000, 5800, 6800, 8000, 10000, 14000], np.float64)
_TCOL = np.array([[1.00, 0.62, 0.38], [1.00, 0.72, 0.50], [1.00, 0.82, 0.64], [1.00, 0.89, 0.78], [1.00, 0.95, 0.89],
                  [0.97, 0.96, 1.00], [0.86, 0.90, 1.00], [0.76, 0.84, 1.00], [0.66, 0.77, 1.00]], np.float32)


def star_colour(temp):
    t = np.asarray(temp, np.float64)
    out = np.stack([np.interp(t, _TEMPS, _TCOL[:, c]) for c in range(3)], -1)
    return out.astype(F32)


def star_temps(rnd, n):
    """Temperatures of n field stars: mostly 4000 to 6500 K, a tail of red dwarfs and giants, a few hot blue stars."""
    u = rnd.uniform(n)
    base = 3200.0 + 3800.0 * rnd.uniform(n) ** 0.85
    hot = u > 0.86
    base = np.where(hot, 7000.0 + 7000.0 * rnd.uniform(n) ** 1.4, base)
    red = u < 0.10
    base = np.where(red, 2800.0 + 900.0 * rnd.uniform(n), base)
    return base


def magnitudes(rnd, n, m0, m1, slope=0.55):
    """n magnitudes in m0..m1 with N(<m) growing as 10^(slope m): many faint stars, few bright ones (slope 0.6 is the sky's own)."""
    a, b = 10.0 ** (slope * m0), 10.0 ** (slope * m1)
    return np.log10(a + (b - a) * rnd.uniform(n)) / slope


def stretch_flux(flux, eps=0.03):
    """The astrophotographer's asinh stretch of a linear star flux (1 for the brightest): faint stars stay visible points, bright ones do not burn
    out the picture. asinh(F / eps) / asinh(1 / eps)."""
    return np.arcsinh(np.asarray(flux, np.float64) / eps) / math.asinh(1.0 / eps)


def starfield(ctx, layer, rnd, density, mags=(0.0, 7.0), sigma_S=0.00034, peak=1.6, avoid=None, density_map=None, trans=None, sat=0.85,
              tint=None, tint_k=0.0, eps=0.03):
    """Field stars into a matter.ParticleLayer. density: stars per S^2; peak: the core of a magnitude m0 star (display units, the tone map rolls it off);
    a star of magnitude m has the asinh stretch of 10^(-0.4 (m - m0)) of it (stretch_flux); the PSF is sigma_S S wide (sub pixel at 1024: the stamp
    keeps its energy, so the preview is the master reduced). avoid(x, y) -> bool: stars that are not drawn (behind the iris). density_map(x, y) -> 0..1:
    the stars are thinned where it is low (the clumpy sky). trans(x, y) -> 0..1: dust in front of the stars. Returns (x, y, flux, colour) of the drawn
    stars, brightest first (flux after the stretch)."""
    W, H, S = ctx.W, ctx.H, ctx.S
    n = int(round(density * (W * H) / float(S * S)))
    if n <= 0:
        return np.zeros(0), np.zeros(0), np.zeros(0), np.zeros((0, 3), F32)
    over = 2 if density_map is not None else 1
    x = rnd.uniform(n * over) * W
    y = rnd.uniform(n * over) * H
    if density_map is not None:
        keep = rnd.uniform(n * over) < np.clip(density_map(x, y), 0.0, 1.0)
        x, y = x[keep][:n], y[keep][:n]
    m = len(x)
    mag = magnitudes(rnd, m, mags[0], mags[1])
    flux = stretch_flux(10.0 ** (-0.4 * (mag - mags[0])), eps)
    col = star_colour(star_temps(rnd, m))
    g = col.mean(-1, keepdims=True)
    col = (g + (col - g) * F32(sat)).astype(F32)
    if tint is not None and tint_k > 0:
        col = (col * F32(1.0 - tint_k) + np.asarray(tint, F32)[None, :] * F32(tint_k) * (col.mean(-1, keepdims=True) / max(float(np.mean(tint)), 1e-3))).astype(F32)
    if trans is not None:
        flux = flux * np.clip(trans(x, y), 0.0, 1.0)
    if avoid is not None:
        ok = ~avoid(x, y)
        x, y, flux, col = x[ok], y[ok], flux[ok], col[ok]
    sig = sigma_S * S
    layer.splat(x, y, sig, col, F32(peak) * flux.astype(F32), min_sigma=0.5)
    # a broad faint halo round the brighter stars (the glow of a lens and of the air): the eye reads a bright star as larger
    b = flux > 0.45
    if b.any():
        layer.splat(x[b], y[b], 3.0 * sig, col[b], F32(0.07 * peak) * (flux[b] ** 3).astype(F32), min_sigma=0.5)
    order = np.argsort(-flux)
    return x[order], y[order], flux[order], col[order]


def spikes(cv, ctx, xs, ys, arm_S, col, amp, width_S=0.00042, angle=None):
    """Diffraction spikes (4 arms) on a few bright stars, drawn into the float canvas; none inside the customer's text box or near the canvas edge."""
    if len(xs) == 0:
        return
    W, H, S = ctx.W, ctx.H, ctx.S
    keep = (xs > 0.04 * S) & (xs < W - 0.04 * S) & (ys > 0.04 * S) & (ys < H - 0.04 * S)
    tb = ctx.text_box
    if tb is not None:
        keep &= ~((xs > tb[0] - 0.05 * S) & (xs < tb[2] + 0.05 * S) & (ys > tb[1] - 0.05 * S) & (ys < tb[3] + 0.05 * S))
    if ctx.wall:
        keep &= ys > 0.22 * H
    if not keep.any():
        return
    arm = np.asarray(arm_S, np.float64) * S
    arm = np.broadcast_to(arm, xs.shape)[keep]
    a = np.broadcast_to(np.asarray(amp, np.float64), xs.shape)[keep]
    c = np.broadcast_to(np.asarray(col, F32), (len(xs), 3))[keep]
    ang = 0.0 if angle is None else angle
    C.sparkles(cv, xs[keep], ys[keep], arm, c, a, width=width_S * S, angle=ang, core=0.0, min_width=0.55)


def avoid_discs(discs, k=1.0):
    """A test for star positions hidden behind the irises (inside k x R of any disc)."""
    def f(x, y):
        out = np.zeros(len(x), bool)
        for d in discs:
            out |= np.hypot(x - d.cx, y - d.cy) < k * d.R
        return out
    return f
