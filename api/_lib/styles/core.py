# -*- coding: utf-8 -*-
"""styles.core: the shared foundation every v3 engine is drawn with. A verbatim port of the scratch prototype fx/core.py (work
package WP4, "move first, merge later": the three engine families are ported onto this module as it stands, with golden hashes
recorded on the scratch code, and only then merged; scripts/styles_tests/test_engine_core.py replays those goldens).

What changed against the scratch file, and nothing else:
- the repo engine is imported as a sibling module (from .. import iris as L), not through a Windows path on sys.path;
- the studio's own words are gone (owner rule: the studio writes nothing on the artwork): no TAGLINE, no FOOTER, no caption(), and
  with them render(), Ctx and the watermark hook (the preview watermark is drawn by api/_lib/preview.py, never by an engine; the
  only text an artwork may carry is the customer's, api/_lib/styles/text.py);
- the process-wide WORK_SIDE is a parameter of the eye: Iris(raw, name, max_side=2048) (a preview 2048, a master 4096; the registry's
  work_side per layout caps it further), and an Iris can carry the eye_id of its sealed profile;
- BoundedCache: the one bounded cache the engines use in place of an unbounded module level dict (a warm instance renders for hours).
- Iris applies the camera orientation of the file's EXIF block before it crops the square, as iris.b64_to_pil does for the legacy engine (WP5A review: an old
  page's plain iris is read by both, and the two must cut the same square; the seed is still the bytes as sent, and a file with no orientation is untouched).

The rules this module enforces (the scratch test_fx.py proved them; they are the engines' contract):
- The customer's graded iris is pasted LAST (finish -> paste_iris_last). An effect only ever receives the float
  canvas, never the disc, so nothing it draws can cover, recolour or distort the iris. Inside the disc (alpha 1)
  the output pixels ARE the graded pixels, byte for byte, whatever the effect did.
- Effect colours come from the eye's own ring: ring_colours() = per-angle MEDIAN of the graded disc between
  0.70 R and 0.92 R, 360 bins, 25-tap circular Gaussian smoothing. They are measured once per eye on a canonical
  REF_SIDE grade, so a 1024 preview and its 4096 master get the very same colours and the same colour class.
- Colour class from the mean ring colour in CIELCh: dark_brown = L* < 30 and hue 30-95 deg; grey = C* < 10
  (and not dark_brown); else own. Each style passes its own fallback palette for the two special classes.
- float32 layers in display space 0..1 (values above 1 allowed until the tone map), soft shoulder tone map above
  0.8 on the max channel (hue kept, overexposed light whitens), +-0.5 LSB dither before 8 bit.
- Randomness: seed_for() = first 8 bytes of sha256(iris bytes, eye index, style, layout joined by NUL bytes), never
  Python hash(). Rand draws everything from PCG64 uniform doubles, so the stream does not depend on numpy's own
  gamma/normal code.
- Sizes in units of R (visible iris radius) and S (canvas short side); particle counts per S^2; blur sigmas in px
  derived from S; stamps pixel-integrated with energy kept, so a 4096 master downsized equals the 1024 preview.

Geometry conventions: pixel (i, j) covers [j, j+1) x [i, i+1), its centre is (j + 0.5, i + 0.5).
theta = atan2(dy, dx) with y pointing DOWN: 0 = 3 o'clock, angles grow CLOCKWISE on screen, -pi..pi.
ring bin k covers theta in [k, k+1) degrees (mod 360).
"""
from __future__ import annotations

import collections
import hashlib
import io
import math
import threading
import time

import numpy as np
from PIL import Image, ImageOps

from .. import iris as L

# ----------------------------------------------------------------------------- constants
PAD = 1.12                           # the crop padding the site uses (compose._pad default)
R_FRAC = L.iris_radius_frac(PAD)     # iris radius as a share of the input square
MAX_SIDE = 2048                      # the default working copy of an eye (the scratch WORK_SIDE: /api/compose shrinks a larger iris to this)
FEATHER = 0.012                      # the graded disc's own soft edge, in units of R (studio_grade step 5)
REF_SIDE = 256                       # canonical grade frame the ring colours are measured on (vs 512: median
                                     # dE00 0.16-0.39, max 0.96 on the calibration set, at about half the cost)
RING_BAND = (0.70, 0.92)             # ring colour band, share of R
RING_BINS = 360
RING_SMOOTH = 5.0                    # circular Gaussian sigma in bins (taps +-12 = 25 taps)
RING_OUTLIER = (0.50, 1.70)          # a bin darker than 0.50 x or brighter than 1.70 x the median bin luminance
                                     # (a lash, a lid shadow, a glare residue) is re-filled from its neighbours
RING_DE_MAX = 20.0                   # ...and so is a bin more than this dE00 from the ring's median colour (an eyelid
                                     # or lash band inside the disc: drv_w02 has 113 such bins, clean eyes max 17.6)
RING_BAD_MAX = 0.40                  # never re-fill more than this share of the ring
DARK_BROWN_L = 30.0
DARK_BROWN_HUE = (30.0, 95.0)
GREY_C = 10.0
KNEE = 0.8                           # tone map shoulder start (display 0..1)
WHITEN = 0.6                         # how far overexposed light drifts to white in the shoulder
BG = (4, 4, 6)                       # default near-black background (#040406)
LUT_N = 8192                         # angular lookup resolution (power of two) for per-pixel colour and profiles
TWO_PI = 2.0 * math.pi


class BoundedCache:
    """A small least-recently-used cache for what an engine keeps between calls (decoded plates, analysed pupils, atlases): a warm
    instance renders for hours, so no module level dict may grow with the number of eyes it has seen. maxsize 2 for anything that
    holds pixels, 64 for small records. get() returns the default for a missing key; put() evicts the oldest entry beyond maxsize."""

    def __init__(self, maxsize=2):
        self.maxsize = max(1, int(maxsize))
        self._d = collections.OrderedDict()
        self._lock = threading.Lock()

    def get(self, key, default=None):
        with self._lock:
            if key not in self._d:
                return default
            self._d.move_to_end(key)
            return self._d[key]

    def put(self, key, value):
        with self._lock:
            self._d[key] = value
            self._d.move_to_end(key)
            while len(self._d) > self.maxsize:
                self._d.popitem(last=False)
        return value

    def clear(self):
        with self._lock:
            self._d.clear()

    def __len__(self):
        return len(self._d)

    def __contains__(self, key):
        return key in self._d


# ----------------------------------------------------------------------------- iris loading and grading
class Iris:
    """One customer eye: the restored iris square exactly as /api/compose receives it.

    raw: the file bytes (the seed source; production uses the stored preview iris PNG bytes for preview AND master).
    graded(Sd): the studio grade in an Sd x Sd frame, via L._grade_disc (compose_multi's path; for a 1024 input and
    any disc up to 4096 it equals compose()'s own studio_grade call). Cached per Sd.
    ring / stats / cls: the eye's own ring colours and colour class (canonical REF_SIDE grade, cached).
    max_side: the working copy cap (a preview 2048, a master 4096): a larger source is shrunk to it on arrival."""

    def __init__(self, raw, name="", max_side=MAX_SIDE, eye_id=None):
        self.raw = bytes(raw)
        self.name = name
        self.digest = hashlib.sha256(self.raw).digest()
        # the id of the sealed profile this eye belongs to: the first 16 hex digits of the sha256 of the clean 1024 px preview
        # bytes. When the Iris is made from those very bytes it is the digest's own prefix; a master made from other bytes passes it in.
        self.eye_id = eye_id or self.digest.hex()[:16]
        self.max_side = int(max_side)
        im = Image.open(io.BytesIO(self.raw))
        try:
            im = ImageOps.exif_transpose(im)                   # as iris.b64_to_pil: an old page's plain iris may carry a camera orientation
        except Exception:                                      # (a damaged EXIF block is no reason to refuse the picture)
            pass
        im = im.convert("RGB")
        side = min(im.size)
        im = im.crop((0, 0, side, side))                       # as compose._irises
        if side > self.max_side:
            im = im.resize((self.max_side, self.max_side), Image.LANCZOS)
        self.src = im
        self._grades = {}
        self._ring = None
        self._stats = None
        self._ease = None
        self.grade_seconds = 0.0

    @property
    def ease(self):
        """studio_ease of the iris as it came in (what L._grade_disc measures on every call), measured once."""
        if self._ease is None:
            t0 = time.perf_counter()
            self._ease = L.studio_ease(self.src, R_FRAC)
            self.grade_seconds += time.perf_counter() - t0
        return self._ease

    def graded(self, Sd):
        Sd = int(Sd)
        g = self._grades.get(Sd)
        if g is None:
            ease = self.ease
            t0 = time.perf_counter()
            g = np.ascontiguousarray(np.asarray(grade_disc(self.src, Sd, ease)))
            self.grade_seconds += time.perf_counter() - t0
            self._grades[Sd] = g
        return g

    @property
    def ring(self):
        if self._ring is None:
            self._ring = ring_colours(self)
        return self._ring

    @property
    def stats(self):
        if self._stats is None:
            self._stats = colour_stats(self.ring)
        return self._stats

    @property
    def cls(self):
        return self.stats["class"]

    def __repr__(self):
        return f"Iris({self.name!r}, {self.src.size[0]} px, {self.digest.hex()[:8]})"


def grade_disc(src, Sd, ease=None):
    """L._grade_disc (compose_multi's grade, equal to compose()'s for a 1024 input) with the ease passed in, so
    it is measured once per eye instead of on every size. Same arithmetic line by line; test_fx checks the pixels
    against L._grade_disc itself."""
    src = src if src.mode == "RGB" else src.convert("RGB")
    ease = L.studio_ease(src, R_FRAC) if ease is None else ease
    target = max(8, int(round(Sd * L.STUDIO_FILL)))
    need = int(math.ceil(1.5 * target / (2.0 * R_FRAC * L.STUDIO_TRIM)))
    s = src if src.size[0] <= need else src.resize((need, need), Image.LANCZOS)
    return L.studio_grade(s, R_FRAC, out=Sd, local=L.STUDIO_LOCAL * ease, micro=L.STUDIO_MICRO * ease)


def load_iris(path, name=None, max_side=MAX_SIDE):
    """Iris from a file (the restored 1024 px disc on black, *_2_enhanced.jpg). Grading is lazy: a disc is graded at
    the size it is drawn at (Iris.graded / place_disc), the ring colours on the canonical REF_SIDE grade. For local boards and
    tests: a function never reads a path of its own choosing."""
    with open(path, "rb") as f:
        raw = f.read()
    base = str(path).replace("\\", "/").rsplit("/", 1)[-1]
    return Iris(raw, name or base.split("_2_enhanced")[0], max_side)


def _tight(frame):
    """The tight disc square of a graded frame: (square uint8, its side). studio_grade puts a target x target disc
    at offset (Sd - target) // 2 with target = round(Sd * STUDIO_FILL), black everywhere else."""
    Sd = frame.shape[0]
    tgt = max(8, int(round(Sd * L.STUDIO_FILL)))
    off = (Sd - tgt) // 2
    return frame[off:off + tgt, off:off + tgt], tgt


# ----------------------------------------------------------------------------- ring colours and colour class
def _circular_smooth(a, sigma=RING_SMOOTH, taps=12):
    k = np.exp(-0.5 * (np.arange(-taps, taps + 1) / sigma) ** 2)
    k /= k.sum()
    pad = np.concatenate([a[-taps:], a, a[:taps]], 0)
    return np.stack([np.convolve(pad[:, c], k, "valid") for c in range(a.shape[1])], 1)


def _fill_gaps_circular(a, bad):
    """Linear interpolation round the circle over the bins flagged bad."""
    n = len(a)
    good = np.nonzero(~bad)[0]
    if len(good) == 0:
        return a
    if len(good) == n:
        return a
    x = np.arange(n)
    out = a.copy()
    for c in range(a.shape[1]):
        out[:, c] = np.interp(x, good, a[good, c], period=n)
    return out


def ring_colours(iris, bins=RING_BINS, band=RING_BAND, smooth=RING_SMOOTH, info=None):
    """(bins, 3) float32 in 0..1: the eye's own colour per angle. Per-angle MEDIAN of the graded disc between
    band[0] R and band[1] R (exact per-channel medians via one sort), outlier bins (lash, lid shadow, glare
    residue: luminance outside RING_OUTLIER x the median bin) re-filled from their neighbours, then circular
    Gaussian smoothing (25 taps). iris: an Iris (measured on its canonical REF_SIDE grade) or a graded frame array.
    info: optional dict that receives {"outlier_bins": n}."""
    frame = iris.graded(REF_SIDE) if isinstance(iris, Iris) else np.asarray(iris)
    sq, tgt = _tight(frame)
    R = tgt / 2.0
    ax = np.arange(tgt, dtype=np.float64) + 0.5 - R
    dx, dy = ax[None, :], ax[:, None]
    rho = np.sqrt(dx * dx + dy * dy) / R
    th = np.degrees(np.arctan2(np.broadcast_to(dy, rho.shape), np.broadcast_to(dx, rho.shape))) % 360.0
    m = (rho > band[0]) & (rho < band[1])
    b = np.minimum((th[m] * (bins / 360.0)).astype(np.int64), bins - 1)
    cnt = np.bincount(b, minlength=bins)
    start = np.cumsum(cnt) - cnt
    lo_i = start + np.maximum(cnt - 1, 0) // 2
    hi_i = start + cnt // 2
    out = np.zeros((bins, 3), np.float64)
    for c in range(3):
        v = sq[..., c][m].astype(np.int64)
        s = np.sort(b * 256 + v)
        vals = s % 256
        med = 0.5 * (vals[np.minimum(lo_i, len(s) - 1)] + vals[np.minimum(hi_i, len(s) - 1)])
        out[:, c] = med
    empty = cnt == 0
    lum = out @ np.array([0.299, 0.587, 0.114])
    ref = np.median(lum[~empty]) if (~empty).any() else 0.0
    bad_l = (lum < RING_OUTLIER[0] * ref) | (lum > RING_OUTLIER[1] * ref)
    med = np.median(out[~empty], axis=0) if (~empty).any() else np.zeros(3)
    de = L.ciede2000(L.srgb_to_lab(out), L.srgb_to_lab(med[None, :]))
    bad = empty | bad_l | (de > RING_DE_MAX)
    if bad.mean() > RING_BAD_MAX:                         # never throw away most of the ring
        bad = empty | bad_l
        if bad.mean() > RING_BAD_MAX:
            bad = empty
    out = _fill_gaps_circular(out, bad)
    out = _circular_smooth(out, smooth)
    if info is not None:
        info["outlier_bins"] = int(bad.sum())
    return (out / 255.0).astype(np.float32)


def lab_to_srgb(lab):
    """CIELAB (D65) to sRGB 0..1 (inverse of L.srgb_to_lab), clipped."""
    lab = np.asarray(lab, np.float64)
    fy = (lab[..., 0] + 16.0) / 116.0
    fx = fy + lab[..., 1] / 500.0
    fz = fy - lab[..., 2] / 200.0
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f > 0.206893, f ** 3, (f - 16.0 / 116.0) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    M = np.array([[0.412453, 0.357580, 0.180423], [0.212671, 0.715160, 0.072169], [0.019334, 0.119193, 0.950227]])
    lin = xyz @ np.linalg.inv(M).T
    lin = np.clip(lin, 0.0, None)
    c = np.where(lin > 0.0031308, 1.055 * lin ** (1 / 2.4) - 0.055, 12.92 * lin)
    return np.clip(c, 0.0, 1.0)


def lch(rgb01):
    """sRGB 0..1 -> (L*, C*, h deg)."""
    lab = L.srgb_to_lab(np.asarray(rgb01, np.float64) * 255.0)
    return lab[..., 0], np.hypot(lab[..., 1], lab[..., 2]), np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360.0


def from_lch(Ls, C, h):
    hr = np.radians(h)
    return lab_to_srgb(np.stack([np.asarray(Ls, np.float64), C * np.cos(hr), C * np.sin(hr)], -1))


def colour_stats(ring):
    """Mean ring colour in CIELCh and the colour class ("dark_brown", "grey" or "own")."""
    mean = np.asarray(ring, np.float64).mean(0)
    Ls, C, h = (float(v) for v in lch(mean))
    if Ls < DARK_BROWN_L and DARK_BROWN_HUE[0] <= h <= DARK_BROWN_HUE[1]:
        cls = "dark_brown"
    elif C < GREY_C:
        cls = "grey"
    else:
        cls = "own"
    return {"class": cls, "L": round(Ls, 2), "C": round(C, 2), "h": round(h, 1),
            "mean_rgb": [round(float(v) * 255, 1) for v in mean]}


def colour_class(ring_or_iris):
    """'dark_brown' | 'grey' | 'own' (see colour_stats)."""
    ring = ring_or_iris.ring if isinstance(ring_or_iris, Iris) else ring_or_iris
    return colour_stats(ring)["class"]


# ----------------------------------------------------------------------------- palette helpers
def rgb01(c):
    """A colour as float32 RGB 0..1 from '#RRGGBB', a 0..255 tuple (any int in it or any value > 1) or 0..1 floats."""
    if isinstance(c, str):
        h = c.lstrip("#")
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0
    a = np.asarray(c, np.float32)
    if a.dtype.kind in "iu" or (isinstance(c, (tuple, list)) and any(isinstance(v, int) for v in c)) or a.max() > 1.0:
        return a / 255.0
    return a


def boost(c, lift=1.6, sat=1.5):
    """Brighter and richer version of a colour (or a (..., 3) palette), 0..1: grey + (c - grey) * sat, times lift.
    Clamped hue-preserving: a colour pushed past 1 is scaled down as a whole (not clipped per channel, which would
    shift its hue), a channel pushed below 0 is set to 0."""
    c = np.asarray(c, np.float32)
    g = c.mean(-1, keepdims=True)
    o = np.maximum((g + (c - g) * sat) * lift, 0.0)
    m = o.max(-1, keepdims=True)
    return (o / np.maximum(m, 1.0)).astype(np.float32)


def mix(a, b, t):
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    return (a * (1.0 - t) + b * t).astype(np.float32)


def hue_shift(c, deg):
    """Rotate hue in CIELCh by deg (the duo rule for two same-coloured eyes), same L* and C*."""
    Ls, C, h = lch(c)
    return from_lch(Ls, C, (h + deg) % 360.0).astype(np.float32)


def colour_distance(a, b):
    """CIEDE2000 between two 0..1 colours (mean ring colours for the duo rule)."""
    return float(L.ciede2000(L.srgb_to_lab(np.asarray(a) * 255.0), L.srgb_to_lab(np.asarray(b) * 255.0)))


def effect_palette(iris_or_ring, lift=1.6, sat=1.4, fallback=None, cls=None, hue_deg=0.0):
    """The per-angle effect palette (RING_BINS, 3) of one eye: boost(ring, lift, sat), then the style's fallback
    for the special classes. fallback maps class -> (colour, t) meaning mix t toward colour, or -> dict with
    optional lift, sat, toward, t (e.g. Supernova dark brown: {'lift': 1.8, 'sat': 1.5, 'toward': '#D98A3D',
    't': 0.35}). hue_deg rotates the palette (duo rule). Returns float32 0..1."""
    ring = iris_or_ring.ring if isinstance(iris_or_ring, Iris) else np.asarray(iris_or_ring, np.float32)
    cls = cls or colour_class(ring)
    spec = (fallback or {}).get(cls)
    if isinstance(spec, dict):
        lift, sat = spec.get("lift", lift), spec.get("sat", sat)
    p = boost(ring, lift, sat)
    if spec is not None:
        toward, t = (spec.get("toward"), spec.get("t", 0.0)) if isinstance(spec, dict) else spec
        if toward is not None and t:
            p = mix(p, rgb01(toward)[None, :], t)
    if hue_deg:
        p = hue_shift(p, hue_deg)
    return p.astype(np.float32)


def palette_lut(pal, n=LUT_N):
    """(n, 3) float32 circular lookup of a (bins, 3) palette, linearly interpolated between bin centres."""
    pal = np.asarray(pal, np.float32)
    bins = pal.shape[0]
    x = (np.arange(n) + 0.5) * (bins / n) - 0.5
    return np.stack([np.interp(x, np.arange(bins), pal[:, c], period=bins) for c in range(3)], 1).astype(np.float32)


def angle_index(theta, n=LUT_N):
    """Per-pixel index into a palette_lut (or angular_lut) for theta (radians, -pi..pi); n a power of two."""
    idx = (theta * np.float32(n / TWO_PI) + np.float32(n)).astype(np.int32)
    idx &= n - 1
    return idx


def angular_lut(prof, n=LUT_N):
    """(n,) float32 circular lookup of a 1-D angular profile of any length, linear between its samples (sample k at
    angle k / len * 360 deg)."""
    prof = np.asarray(prof, np.float64)
    m = len(prof)
    x = (np.arange(n) + 0.5) * (m / n)
    return np.interp(x, np.arange(m), prof, period=m).astype(np.float32)


def tint(intensity, lut, theta, out=None, k=1.0, idx=None):
    """intensity (H, W) x the palette colour at each pixel's angle -> (H, W, 3) float32 light (added into out when
    given). lut from palette_lut(); idx = angle_index(theta) when already computed."""
    col = lut[angle_index(theta, lut.shape[0]) if idx is None else idx]
    col *= (intensity if k == 1.0 else intensity * np.float32(k))[..., None]
    if out is None:
        return col
    out += col
    return out


def ring_at(pal, theta):
    """The palette colour at angle(s) theta (radians), linear between bin centres: (..., 3) float32."""
    theta = np.asarray(theta, np.float64)
    n = pal.shape[0]
    f = (theta * (n / TWO_PI)) % n - 0.5
    i0 = np.floor(f).astype(np.int64)
    w = (f - i0)[..., None]
    i0 %= n
    return (pal[i0] * (1 - w) + pal[(i0 + 1) % n] * w).astype(np.float32)


# ----------------------------------------------------------------------------- seeds and randomness
def seed_for(iris_bytes, eye_index, style, layout):
    """64-bit seed = first 8 bytes (big-endian) of sha256(iris_bytes + b'\\0' + str(eye_index) + b'\\0' + style +
    b'\\0' + layout), UTF-8. The same in every process (Python hash() is salted per process)."""
    h = hashlib.sha256()
    h.update(bytes(iris_bytes))
    h.update(b"\0" + str(int(eye_index)).encode() + b"\0" + str(style).encode("utf-8") + b"\0" + str(layout).encode("utf-8"))
    return int.from_bytes(h.digest()[:8], "big")


def design_seed(irises, style, layout):
    """The seed of a whole design (shared background stars, bridges): seed_for over the eyes' digests in canvas
    order, eye index -1."""
    return seed_for(b"".join(ir.digest for ir in irises), -1, style, layout)


def _sub_seed(seed, tag):
    return int.from_bytes(hashlib.sha256(int(seed).to_bytes(8, "big") + b"\0" + str(tag).encode("utf-8")).digest()[:16], "big")


class Rand:
    """Seeded random numbers for one purpose (tag) of one seed. Everything is derived from PCG64 uniform doubles
    (stable since numpy 1.17), so particles do not move when numpy's own gamma/normal/pareto code changes."""

    def __init__(self, seed, tag=""):
        self.g = np.random.Generator(np.random.PCG64(_sub_seed(seed, tag)))

    def uniform(self, n=None, lo=0.0, hi=1.0):
        return lo + (hi - lo) * self.g.random(n)

    def normal(self, n, mu=0.0, sigma=1.0):
        u = self.g.random((2, n))
        return mu + sigma * np.sqrt(-2.0 * np.log1p(-u[0])) * np.cos(TWO_PI * u[1])

    def exponential(self, n, scale=1.0):
        return -scale * np.log1p(-self.g.random(n))

    def pareto(self, n, a):
        """Lomax like numpy's pareto: (1 - u)^(-1/a) - 1."""
        return (1.0 - self.g.random(n)) ** (-1.0 / a) - 1.0

    def gamma(self, n, k, scale=1.0):
        """Wilson-Hilferty gamma (close for k >= 1, fine for visuals), from one normal per draw."""
        z = self.normal(n)
        c = 1.0 / (9.0 * k)
        return k * scale * np.maximum(1.0 - c + z * math.sqrt(c), 0.0) ** 3

    def integers(self, n, lo, hi):
        return lo + np.minimum((self.g.random(n) * (hi - lo)).astype(np.int64), hi - lo - 1)


def rng_for(seed, tag=""):
    return Rand(seed, tag)


# ----------------------------------------------------------------------------- float canvas helpers
def canvas(W, H, bg=BG):
    """(H, W, 3) float32 0..1 filled with bg."""
    c = np.empty((int(H), int(W), 3), np.float32)
    c[:] = rgb01(bg)
    return c


def radial_bg(W, H, cx, cy, radius, inner, outer, power=1.0):
    """(H, W, 3) float32: inner at (cx, cy) fading to outer at radius px (and beyond), smoothstep^power."""
    x = (np.arange(W, dtype=np.float32) + np.float32(0.5 - cx))[None, :]
    y = (np.arange(H, dtype=np.float32) + np.float32(0.5 - cy))[:, None]
    t = np.clip(np.sqrt(x * x + y * y) / np.float32(radius), 0, 1)
    t = (t * t * (3 - 2 * t)) ** power
    a, b = rgb01(inner), rgb01(outer)
    return (a[None, None, :] + (b - a)[None, None, :] * t[..., None]).astype(np.float32)


def _polar_from(dx, dy, R, stretch_y):
    """rho, theta from offsets. With stretch_y != 1 only the part BEYOND the rim is stretched (rho stays exact up
    to 1, so an effect still hugs the round disc): rho = 1 + (r / R - 1) * |(dx, dy / s)| / |(dx, dy)|, and theta is
    read in the stretched frame, so rays fan out like a vertically stretched picture."""
    dx, dy = np.broadcast_arrays(dx, dy)
    r = np.sqrt(dx * dx + dy * dy)
    rho = r / np.float32(R)
    if stretch_y == 1.0:
        return rho.astype(np.float32), np.arctan2(dy, dx).astype(np.float32)
    dys = dy / np.float32(stretch_y)
    q = np.sqrt(dx * dx + dys * dys) / np.maximum(r, np.float32(1e-6))
    out = rho > 1.0
    rho = np.where(out, np.float32(1.0) + (rho - np.float32(1.0)) * q, rho)
    return rho.astype(np.float32), np.arctan2(dys, dx).astype(np.float32)


def polar(W, H, cx, cy, R, stretch_y=1.0, box=None):
    """rho (distance in units of R) and theta (radians, 0 = 3 o'clock, clockwise on screen) of every pixel centre,
    float32 (H, W). box=(x0, y0, x1, y1) gives only that window. stretch_y > 1 stretches an effect vertically
    beyond the rim (the wallpaper's 1.15, see _polar_from)."""
    x0, y0, x1, y1 = box or (0, 0, W, H)
    dx = (np.arange(x0, x1, dtype=np.float32) + np.float32(0.5 - cx))[None, :]
    dy = (np.arange(y0, y1, dtype=np.float32) + np.float32(0.5 - cy))[:, None]
    return _polar_from(dx, dy, R, stretch_y)


def screen(base, light, k=1.0):
    """In place: base = 1 - (1 - base)(1 - k light). Light above 1 is allowed (the tone map rolls it off)."""
    t = 1.0 - base
    t *= light if k == 1.0 else light * np.float32(k)
    base += t
    return base


def add(base, light, k=1.0):
    """In place: base += k light."""
    if k == 1.0:
        base += light
    else:
        base += light * np.float32(k)
    return base


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


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


def _gauss_full(a, sigma):
    if sigma < 0.25:
        return a.copy()
    k = _gauss_kernel(sigma)
    return _conv_axis(_conv_axis(a, k, 0), k, 1)


BLUR_WORK_SIGMA = 2.0        # a wide blur is computed on a grid where its sigma is 2-4 px


def blur(a, sigma, clip_negative=True):
    """Separable Gaussian blur of an (H, W) or (H, W, C) float32 array, numpy only, sigma in px.

    A wide blur runs at reduced resolution: the image is box-reduced by f (a power of two, f >= 2 as soon as sigma
    >= 4, i.e. half resolution or less), blurred there with sigma' = sqrt(sigma^2 - f^2 / 12) / f in [2, 4) px
    (the box's own spread subtracted), and brought back with a bicubic resize (PIL mode F). So its cost does not
    grow with sigma, and because sigma is given in S units the 1024 and 4096 renders reduce to nearly the same
    small grid (their soft layers match). Edges reflect."""
    a = np.asarray(a, np.float32)
    if sigma <= 0:
        return a.copy()
    f = 1
    while sigma / (2 * f) >= BLUR_WORK_SIGMA:
        f *= 2
    if f == 1:
        return _gauss_full(a, sigma)
    red = box_reduce(a, f)
    s2 = math.sqrt(max(sigma * sigma - f * f / 12.0, 0.25 * f * f)) / f
    red = _gauss_full(red, s2)
    return upsample(red, a.shape[1], a.shape[0], f, clip_negative)


def box_reduce(a, f):
    """Mean of every f x f block (edge-padded to a multiple of f), per channel with PIL's float reduce."""
    if f == 1:
        return a
    H, W = a.shape[:2]
    Hp, Wp = -(-H // f) * f, -(-W // f) * f
    p = a if (Hp, Wp) == (H, W) else np.pad(a, [(0, Hp - H), (0, Wp - W)] + [(0, 0)] * (a.ndim - 2), mode="edge")
    if p.ndim == 2:
        return np.asarray(Image.fromarray(np.ascontiguousarray(p), "F").reduce(f), np.float32)
    out = np.empty((Hp // f, Wp // f, p.shape[2]), np.float32)
    for c in range(p.shape[2]):
        out[..., c] = np.asarray(Image.fromarray(np.ascontiguousarray(p[..., c]), "F").reduce(f), np.float32)
    return out


def upsample(a, W, H, f, clip_negative=True):
    """A reduced grid (block centres of f x f blocks) back to W x H px: bicubic per channel (PIL mode F), the
    block centre mapped to the block centre. f == 1 returns a itself."""
    if f == 1:
        return a
    h, w = a.shape[:2]
    if a.ndim == 2:
        out = np.array(np.asarray(Image.fromarray(np.ascontiguousarray(a), "F").resize((w * f, h * f), Image.BICUBIC),
                                  np.float32)[:H, :W])
    else:
        out = np.empty((H, W, a.shape[2]), np.float32)
        for c in range(a.shape[2]):
            out[..., c] = np.asarray(Image.fromarray(np.ascontiguousarray(a[..., c]), "F").resize((w * f, h * f), Image.BICUBIC),
                                     np.float32)[:H, :W]
    if clip_negative:                 # bicubic can undershoot next to a bright edge
        np.maximum(out, 0.0, out=out)
    return out


def work_factor(feature_px, min_px=1.5, max_f=8):
    """The coarsest power-of-two reduction (<= max_f) at which the finest feature of a soft layer (a blur sigma, a
    ring width, in full-resolution px) still spans min_px grid px. 1024 previews stay at 1; a 4096 master computes
    its soft light on a 2x-8x smaller grid and upsamples once, so it samples like the preview does."""
    f = 1
    while f * 2 <= max_f and feature_px / (f * 2) >= min_px:
        f *= 2
    return f


class Grid:
    """A sampling grid over a W x H canvas, reduced by f: grid pixel (i, j) stands for the f x f block centred at
    ((j + 0.5) f, (i + 0.5) f) in canvas px. Soft light is computed here and brought back once with up()."""

    def __init__(self, W, H, f=1):
        self.W, self.H, self.f = int(W), int(H), int(f)
        self.w, self.h = -(-self.W // self.f), -(-self.H // self.f)

    def zeros(self, c=3):
        return np.zeros((self.h, self.w, c) if c else (self.h, self.w), np.float32)

    def box(self, cx, cy, reach_px):
        """Grid window (x0, y0, x1, y1) covering reach_px (canvas px) round (cx, cy), clipped."""
        f = self.f
        return (max(0, int((cx - reach_px) // f)), max(0, int((cy - reach_px) // f)),
                min(self.w, int(math.ceil((cx + reach_px) / f)) + 1), min(self.h, int(math.ceil((cy + reach_px) / f)) + 1))

    def polar(self, cx, cy, R, stretch_y=1.0, box=None):
        """rho (units of R) and theta at the grid pixels' canvas positions; box in GRID pixels."""
        x0, y0, x1, y1 = box or (0, 0, self.w, self.h)
        f = np.float32(self.f)
        dx = ((np.arange(x0, x1, dtype=np.float32) + np.float32(0.5)) * f - np.float32(cx))[None, :]
        dy = ((np.arange(y0, y1, dtype=np.float32) + np.float32(0.5)) * f - np.float32(cy))[:, None]
        return _polar_from(dx, dy, R, stretch_y)

    def up(self, a, clip_negative=True):
        return upsample(a, self.W, self.H, self.f, clip_negative)


def tone_map(a, knee=KNEE, whiten=WHITEN):
    """In place soft shoulder: the max channel m above knee becomes knee + (1 - knee)(1 - exp(-(m - knee)/(1 - knee)))
    (slope 1 at the knee, never reaching 1), all channels scaled by the same factor (hue kept), then pulled toward
    white by whiten x (1 - factor) so strongly overexposed light turns white-hot instead of flat-saturated.
    Below the knee nothing changes. Negative values are set to 0."""
    np.maximum(a, 0.0, out=a)
    m = np.maximum(np.maximum(a[..., 0], a[..., 1]), a[..., 2])
    over = m > knee
    if over.any():
        mo = m[over]
        span = 1.0 - knee
        t = knee + span * (1.0 - np.exp(-(mo - knee) / span))
        s = (t / mo).astype(np.float32)
        sub = a[over] * s[:, None]
        if whiten:
            w = (whiten * (1.0 - s))[:, None]
            sub += (t[:, None].astype(np.float32) - sub) * w
        a[over] = sub
    return a


def dither_quantize(a, seed, tag="dither"):
    """float 0..1 -> uint8 with +-0.5 LSB uniform dither (floor(255 a + u), u in [0, 1)), seeded, in row bands."""
    H, W = a.shape[:2]
    out = np.empty(a.shape, np.uint8)
    rnd = Rand(seed, tag)
    step = max(8, (1 << 20) // max(W, 1))
    for r0 in range(0, H, step):
        r1 = min(H, r0 + step)
        v = a[r0:r1] * np.float32(255.0)
        v += rnd.g.random(v.shape, dtype=np.float32)
        np.floor(v, out=v)
        np.clip(v, 0, 255, out=v)
        out[r0:r1] = v.astype(np.uint8)
    return out


def fade_rows(light, y0, y1, floor=0.25):
    """In place: rows above y0 keep full strength, fading smoothly to floor at y1 and below (px)."""
    H = light.shape[0]
    y = np.arange(H, dtype=np.float32) + 0.5
    f = 1.0 - (1.0 - floor) * smoothstep((y - y0) / max(y1 - y0, 1.0))
    light *= f.astype(np.float32)[:, None, None] if light.ndim == 3 else f.astype(np.float32)[:, None]
    return light


# ----------------------------------------------------------------------------- noise (resolution independent)
def periodic_fbm1d(n, rnd, octaves=3, base=6, gain=0.55):
    """Periodic 1-D fBm with n samples round the circle, 0..1 float32 (cells counted round the circle, not in px)."""
    x = np.arange(n) * 1.0 / n
    acc = np.zeros(n)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cells = base * 2 ** o
        v = rnd.uniform(cells)
        # periodic Catmull-Rom
        t = x * cells
        i = np.floor(t).astype(int)
        f = t - i
        p0, p1, p2, p3 = v[(i - 1) % cells], v[i % cells], v[(i + 1) % cells], v[(i + 2) % cells]
        acc += amp * (p1 + 0.5 * f * (p2 - p0 + f * (2 * p0 - 5 * p1 + 4 * p2 - p3 + f * (3 * (p1 - p2) + p3 - p0))))
        tot += amp
        amp *= gain
    return np.clip(acc / tot, 0, 1).astype(np.float32)


def fbm_polar(n_ang, n_rad, rnd, octaves=5, base=(6, 3), gain=0.55):
    """Periodic-in-angle fBm on an (angle x radius) grid, float32 0..1 (tile 3x in angle, bicubic in mode F)."""
    acc = np.zeros((n_ang, n_rad), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        ca, cr = base[0] * 2 ** o, base[1] * 2 ** o
        g = rnd.uniform((ca, cr)).astype(np.float32)
        tiled = np.ascontiguousarray(np.concatenate([g, g, g], 0))
        up = np.asarray(Image.fromarray(tiled, "F").resize((n_rad, 3 * n_ang), Image.BICUBIC), np.float32)
        acc += amp * up[n_ang:2 * n_ang]
        tot += amp
        amp *= gain
    return np.clip(acc / tot, 0, 1)


def value_noise2d(W, H, cells, rnd):
    """Smooth 2-D value noise 0..1 at W x H px with `cells` cells across the SHORT side (so the same pattern at any
    resolution): a small random grid resized bicubic in mode F."""
    S = min(W, H)
    cw, ch = max(2, int(round(cells * W / S))) + 1, max(2, int(round(cells * H / S))) + 1
    g = rnd.uniform((ch, cw)).astype(np.float32)
    return np.clip(np.asarray(Image.fromarray(g, "F").resize((W, H), Image.BICUBIC), np.float32), 0, 1)


# ----------------------------------------------------------------------------- particles
def at_polar(disc, rho, theta, stretch_y=1.0):
    """Canvas px of points given in R units round a disc: rho (distance / R), theta (radians, screen clockwise).
    stretch_y stretches only the part beyond the rim, as polar() reads it."""
    rho = np.asarray(rho, np.float64)
    theta = np.asarray(theta, np.float64)
    c, s = np.cos(theta), np.sin(theta)
    if stretch_y != 1.0:
        k = 1.0 / np.sqrt(c * c + (s / stretch_y) ** 2)      # the stretch along this direction
        rho = np.where(rho > 1.0, 1.0 + (rho - 1.0) * k, rho)
    return disc.cx + rho * disc.R * c, disc.cy + rho * disc.R * s


def particle_count(density, W, H):
    """Particles for a density given per S^2 (S = short side): the same count at every resolution."""
    S = min(W, H)
    return int(round(density * (W * H) / float(S * S)))


def _erf(x):
    """Abramowitz-Stegun 7.1.26 (|error| < 1.5e-7), vectorised, float32 out."""
    s = np.sign(x)
    a = np.abs(x)
    t = 1.0 / (1.0 + 0.3275911 * a)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-a * a)
    return (s * y).astype(np.float32)


def _pix_gauss(c, s, r):
    """(n, 2r+1) pixel-integrated normalised Gaussians centred at c (px) with sigma s, starting at floor(c) - r."""
    i0 = np.floor(c).astype(np.int64) - r
    edges = i0[:, None] + np.arange(2 * r + 2)[None, :]
    z = (edges - c[:, None]) / (s[:, None] * math.sqrt(2.0))
    cdf = 0.5 * (1.0 + _erf(z))
    return np.diff(cdf, axis=1).astype(np.float32), i0


SPLAT_CHUNK = 1 << 21        # stamp pixels per scatter call (memory bound)


def splat(layer, xs, ys, sigma, rgb, amp=1.0, min_sigma=0.5):
    """Anti-aliased Gaussian stamps added into layer (H, W, 3) float32, in place.

    xs, ys: stamp centres in canvas px (floats). sigma: px (scalar or per stamp). rgb: (3,) or (n, 3) 0..1.
    amp: peak of the ideal Gaussian at the requested sigma (scalar or per stamp). Each pixel receives the Gaussian
    integrated over its own area, and the energy amp * 2 pi sigma^2 is kept when sigma is floored to min_sigma px,
    so a stamp sized in S units deposits the same light per area at 1024 and 4096 (a sub-pixel star is dimmer
    per pixel at 1024, exactly like the 4096 master downsized)."""
    H, W = layer.shape[:2]
    xs = np.atleast_1d(np.asarray(xs, np.float64))
    ys = np.atleast_1d(np.asarray(ys, np.float64))
    n = len(xs)
    if n == 0:
        return layer
    sig = np.broadcast_to(np.asarray(sigma, np.float64), (n,)).copy()
    energy = np.broadcast_to(np.asarray(amp, np.float64), (n,)) * 2.0 * math.pi * sig * sig
    s_eff = np.maximum(sig, min_sigma)
    col = np.broadcast_to(np.asarray(rgb, np.float32), (n, 3))
    rad = np.ceil(3.5 * s_eff + 1.0).astype(np.int64)
    flat = layer.reshape(-1, 3)
    for r in np.unique(rad):
        idx_r = np.nonzero(rad == r)[0]
        K = 2 * r + 1
        per = max(1, SPLAT_CHUNK // (K * K))
        for c0 in range(0, len(idx_r), per):
            ii = idx_r[c0:c0 + per]
            gx, ix0 = _pix_gauss(xs[ii], s_eff[ii], r)
            gy, iy0 = _pix_gauss(ys[ii], s_eff[ii], r)
            w = (gy[:, :, None] * gx[:, None, :]) * energy[ii].astype(np.float32)[:, None, None]
            px = ix0[:, None, None] + np.arange(K)[None, None, :]
            py = iy0[:, None, None] + np.arange(K)[None, :, None]
            ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
            ok = np.broadcast_to(ok, w.shape)
            fi = (np.broadcast_to(py, w.shape) * W + np.broadcast_to(px, w.shape))[ok]
            pi = np.broadcast_to(np.arange(len(ii))[:, None, None], w.shape)[ok]
            np.add.at(flat, fi, w[ok][:, None] * col[ii][pi])
    return layer


def sparkles(layer, xs, ys, arm, rgb, amp=1.0, width=None, angle=0.0, core=1.0, min_width=0.6):
    """4-point stars added into layer, in place. arm: arm length px (scalar or per star), width: arm sigma px
    (default arm / 14, floored to min_width with the brightness scaled down so thin arms keep their energy), angle:
    radians (scalar or per star; 0 = arms along x and y). Arms taper as (1 - |t| / arm)^2.5, plus a round core
    (sigma 1.4 width) of relative strength core."""
    H, W = layer.shape[:2]
    xs = np.atleast_1d(np.asarray(xs, np.float64))
    ys = np.atleast_1d(np.asarray(ys, np.float64))
    n = len(xs)
    if n == 0:
        return layer
    arm = np.broadcast_to(np.asarray(arm, np.float64), (n,))
    wid = np.broadcast_to(np.asarray(width if width is not None else arm / 14.0, np.float64), (n,))
    w_eff = np.maximum(wid, min_width)
    gain = np.broadcast_to(np.asarray(amp, np.float64), (n,)) * wid / w_eff
    ang = np.broadcast_to(np.asarray(angle, np.float64), (n,))
    col = np.broadcast_to(np.asarray(rgb, np.float32), (n, 3))
    for k in range(n):
        r = int(math.ceil(arm[k] + 3 * w_eff[k])) + 1
        cx, cy = xs[k], ys[k]
        x0, y0 = int(math.floor(cx)) - r, int(math.floor(cy)) - r
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + 2 * r + 1), min(H, y0 + 2 * r + 1)
        if xa >= xb or ya >= yb:
            continue
        dx = (np.arange(xa, xb, dtype=np.float32) + np.float32(0.5 - cx))[None, :]
        dy = (np.arange(ya, yb, dtype=np.float32) + np.float32(0.5 - cy))[:, None]
        ca, sa = np.float32(math.cos(ang[k])), np.float32(math.sin(ang[k]))
        u = dx * ca + dy * sa
        v = -dx * sa + dy * ca
        a2, wv = np.float32(arm[k]), np.float32(w_eff[k])
        arm_u = np.clip(1 - np.abs(u) / a2, 0, 1) ** 2.5 * np.exp(-0.5 * (v / wv) ** 2)
        arm_v = np.clip(1 - np.abs(v) / a2, 0, 1) ** 2.5 * np.exp(-0.5 * (u / wv) ** 2)
        val = np.maximum(arm_u, arm_v)
        if core:
            val = val + np.float32(core) * np.exp(-0.5 * (u * u + v * v) / (1.4 * wv) ** 2)
        layer[ya:yb, xa:xb] += (val * np.float32(gain[k]))[..., None] * col[k]
    return layer


# ----------------------------------------------------------------------------- the disc: placement and paste
class Disc:
    """A graded iris placed on a canvas. g: the tight disc square (uint8, premultiplied by its own soft edge),
    alpha: that edge (float32, 1 inside rho <= 1 - FEATHER), (x0, y0): its integer top-left on the canvas,
    (cx, cy, R): the EXACT centre and visible radius in canvas px every effect must use."""
    __slots__ = ("iris", "index", "g", "alpha", "x0", "y0", "cx", "cy", "R", "Sd")

    def __repr__(self):
        return f"Disc(#{self.index} {self.iris.name if self.iris else ''} c=({self.cx:.1f},{self.cy:.1f}) R={self.R:.1f})"


def place_disc(iris, cx, cy, R, index=0):
    """Grade iris for a visible radius of about R px and snap it to whole pixels near (cx, cy). The returned
    Disc's cx, cy, R are exact (effects use those, never the requested ones): R = target / 2 where
    target = round(Sd * STUDIO_FILL), Sd = round(2R / STUDIO_FILL), and the top-left is rounded to integers so
    the graded pixels are pasted unresampled."""
    Sd = max(8, int(round(2.0 * R / L.STUDIO_FILL)))
    frame = iris.graded(Sd)
    sq, tgt = _tight(frame)
    d = Disc()
    d.iris, d.index, d.Sd = iris, index, Sd
    d.g = np.ascontiguousarray(sq)
    d.alpha = L.disk_alpha(tgt, tgt / 2.0, FEATHER).astype(np.float32)
    d.x0, d.y0 = int(round(cx - tgt / 2.0)), int(round(cy - tgt / 2.0))
    d.cx, d.cy, d.R = d.x0 + tgt / 2.0, d.y0 + tgt / 2.0, tgt / 2.0
    return d


def paste_iris_last(img8, disc, centre=None, R=None):
    """Composite the graded disc over the finished 8-bit canvas, in place, as the LAST pixel operation:
    out = g + canvas * (1 - alpha) (premultiplied over: g already carries its own 0.012 R soft edge, so there is no
    dark fringe). Where alpha is 1 the output is g exactly, byte for byte. Also accepts (img8, iris, (cx, cy), R),
    which places the disc first. Returns the Disc."""
    if not isinstance(disc, Disc):
        disc = place_disc(disc, centre[0], centre[1], R)
    H, W = img8.shape[:2]
    t = disc.g.shape[0]
    xa, ya = max(0, disc.x0), max(0, disc.y0)
    xb, yb = min(W, disc.x0 + t), min(H, disc.y0 + t)
    if xa >= xb or ya >= yb:
        return disc
    gs = disc.g[ya - disc.y0:yb - disc.y0, xa - disc.x0:xb - disc.x0].astype(np.float32)
    a = disc.alpha[ya - disc.y0:yb - disc.y0, xa - disc.x0:xb - disc.x0][..., None]
    reg = img8[ya:yb, xa:xb].astype(np.float32)
    reg *= 1.0 - a
    reg += gs
    np.rint(reg, out=reg)
    np.clip(reg, 0, 255, out=reg)
    img8[ya:yb, xa:xb] = reg.astype(np.uint8)
    return disc


def finish(cv, discs, seed, knee=KNEE, whiten=WHITEN, paste=True):
    """The last steps, in this order: tone map (in place on cv), dither to 8 bit, paste every graded iris LAST.
    Returns the uint8 (H, W, 3) array. paste=False is for the effect-layer tests only."""
    tone_map(cv, knee, whiten)
    img8 = dither_quantize(cv, seed)
    if paste:
        for d in discs:
            paste_iris_last(img8, d)
    return img8
