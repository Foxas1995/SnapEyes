# -*- coding: utf-8 -*-
"""One eye as a function sees it (EyeInput), and what is known about it (EyeProfile, eye_id).

The design code's Iris is split in two. EyeInput holds the restored iris square and answers for pixels: the studio grade at any
size (graded), and, from that grade, the ring colours, the colour class, the pupil. EyeProfile is the small, authentic record of
what was measured once, on the restored 1024 px preview, at /api/enhance: eye_id, ease, colour class, ring colours, pupil class
and reach, the secondary hue, the two gate results. It is sealed into the preview (api/_lib/preview.py, seal v2), stored with the
order draft and read by compose, checkout and the master, so a preview and the paid file draw the same picture from the same
facts, and a customer's page can neither invent nor edit them.

eye_id: the first 16 hex digits of the sha256 of the clean 1024 px preview JPEG bytes (the sealed KIND_ORDER plaintext; the order
draft stores the same value as preview.sha256[:16]). A seed is made from eye ids, never from the pixels it draws, because a 4096 px
master has other bytes than the preview it belongs to.

Profile record (JSON, whole numbers only, at most MAX_PROFILE_BYTES after zlib: the bytes of a profile do not depend on float
formatting). Fixed precision: ring in 8 bit steps (the colour class is decided on the unrounded ring and stored), pad, ease,
aspect and reach in thousandths, colour statistics in hundredths and tenths:
  v, eye_id, pad (thousandths), ease (thousandths), cls ("own" | "dark_brown" | "grey"),
  stats {L (hundredths), C (hundredths), h (tenths of a degree), rgb [3, tenths of a level]},
  ring [1080] (360 bins x R, G, B, 0..255), pupil {cls, aspect, rp, cx, cy, found, reach [180]} (styles/pupil.py),
  h2 {how, hue (thousandths of a degree), chroma (thousandths)}, gate {lid | fill: {ok, why [codes], values}} (styles/gate.py).
The ease is a record: a grade always measures its own ease from the pixels it is given (carrying the preview's ease into the master's
grade made the picture worse in the one real pair measured).

Module rule: every module of the v3 work starts with the __future__ import (Vercel's default Python is 3.12)."""
from __future__ import annotations

import collections
import hashlib
import io
import json
import math
import re
import threading
import time
import zlib

import numpy as np
from PIL import Image

from .. import iris as L
from . import gate as GATE
from . import palette as PAL
from . import pupil as PUP

PROFILE_V = 1
PAD = 1.12                           # the crop padding the site uses (compose._pad default)
MAX_SIDE = 2048                      # the default working copy of an eye: a larger source is shrunk to it on arrival
REF_SIDE = 256                       # canonical grade frame the ring, the pupil and the lid rule are measured on
FILL_SIDE = 1024                     # the graded frame the fill rule was calibrated on (the universe fill is cut from it)
RING_BAND = (0.70, 0.92)             # ring colour band, share of R
RING_BINS = 360
RING_SMOOTH = 5.0                    # circular Gaussian sigma in bins (taps +-12 = 25 taps)
RING_OUTLIER = (0.50, 1.70)          # a bin darker than 0.50 x or brighter than 1.70 x the median bin luminance is re-filled
RING_DE_MAX = 20.0                   # ...and so is a bin more than this dE00 from the ring's median colour
RING_BAD_MAX = 0.40                  # never re-fill more than this share of the ring
CLASSES = PAL.CLASSES
MAX_PROFILE_BYTES = 8192             # a profile after zlib
MAX_PROFILE_RAW = 24576              # ... and before it (a decompression cap)
PROFILE_MIN_LEFT = 6.0               # enhance computes the profile only with at least this many seconds left in the invocation
GRADE_CACHE_BYTES = 192 << 20        # graded frames one EyeInput keeps (least recently used first out)

_ID = re.compile(r"^[0-9a-f]{16}$")


class ProfileError(ValueError):
    """A profile record that is not well formed (or does not belong to its eye)."""


# ----------------------------------------------------------------------------- identity
def eye_id_of(data):
    """The eye id of the clean 1024 px preview JPEG bytes: the first 16 hex digits of their sha256."""
    return hashlib.sha256(bytes(data)).hexdigest()[:16]


def is_eye_id(s):
    return isinstance(s, str) and bool(_ID.fullmatch(s))


def _pixel_id(im):
    """An id for an eye that has no bytes (tests, laboratories): the sha256 of its RGB pixels. Never the id of a customer's eye."""
    return hashlib.sha256(b"pixels:" + im.convert("RGB").tobytes()).hexdigest()[:16]


# ----------------------------------------------------------------------------- grading and measuring (the design code, verbatim)
def tight(frame):
    """The tight disc square of a graded frame: (square uint8, its side). studio_grade puts a target x target disc
    at offset (Sd - target) // 2 with target = round(Sd * STUDIO_FILL), black everywhere else."""
    Sd = frame.shape[0]
    tgt = max(8, int(round(Sd * L.STUDIO_FILL)))
    off = (Sd - tgt) // 2
    return frame[off:off + tgt, off:off + tgt], tgt


def grade_disc(src, r_frac, Sd, ease=None):
    """L._grade_disc (compose_multi's grade, equal to compose()'s for a 1024 input) with the ease passed in, so it is measured once
    per eye instead of on every size. Same arithmetic line by line."""
    src = src if src.mode == "RGB" else src.convert("RGB")
    ease = L.studio_ease(src, r_frac) if ease is None else ease
    target = max(8, int(round(Sd * L.STUDIO_FILL)))
    need = int(math.ceil(1.5 * target / (2.0 * r_frac * L.STUDIO_TRIM)))
    s = src if src.size[0] <= need else src.resize((need, need), Image.LANCZOS)
    return L.studio_grade(s, r_frac, out=Sd, local=L.STUDIO_LOCAL * ease, micro=L.STUDIO_MICRO * ease)


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


def ring_colours(frame, bins=RING_BINS, band=RING_BAND, smooth=RING_SMOOTH, info=None):
    """(bins, 3) float32 in 0..1: the eye's own colour per angle. Per-angle MEDIAN of the graded disc between band[0] R and band[1] R
    (exact per-channel medians via one sort), outlier bins (lash, lid shadow, glare residue: luminance outside RING_OUTLIER x the
    median bin, or more than RING_DE_MAX dE00 from the ring's median colour) re-filled from their neighbours, then circular Gaussian
    smoothing (25 taps). frame: a graded frame (the canonical REF_SIDE grade). info: optional dict that receives
    {"outlier_bins": n}."""
    sq, tgt = tight(np.asarray(frame))
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


# ----------------------------------------------------------------------------- the profile record
def _is_int(x, lo, hi):
    return isinstance(x, int) and not isinstance(x, bool) and lo <= x <= hi


def _int_list(a, n, lo, hi):
    return isinstance(a, list) and len(a) == n and all(_is_int(x, lo, hi) for x in a)


def validate(rec):
    """Raise ProfileError unless rec is a well-formed profile record (see the module text). Returns rec."""
    def bad(why):
        raise ProfileError("eye profile: " + why)
    if not isinstance(rec, dict) or set(rec) != {"v", "eye_id", "pad", "ease", "cls", "stats", "ring", "pupil", "h2", "gate"}:
        bad("fields")
    if rec["v"] != PROFILE_V or isinstance(rec["v"], bool):
        bad("version")
    if not is_eye_id(rec["eye_id"]):
        bad("eye_id")
    if not _is_int(rec["pad"], 1000, 2000) or not _is_int(rec["ease"], 0, 1000):
        bad("pad or ease")
    if rec["cls"] not in CLASSES:
        bad("class")
    st = rec["stats"]
    if (not isinstance(st, dict) or set(st) != {"L", "C", "h", "rgb"} or not _is_int(st["L"], 0, 10000) or not _is_int(st["C"], 0, 30000)
            or not _is_int(st["h"], 0, 3600) or not _int_list(st["rgb"], 3, 0, 2550)):
        bad("stats")
    if not _int_list(rec["ring"], RING_BINS * 3, 0, 255):
        bad("ring")
    p = rec["pupil"]
    if (not isinstance(p, dict) or set(p) != {"cls", "aspect", "rp", "cx", "cy", "found", "reach"} or p["cls"] not in PUP.CLASSES
            or not _is_int(p["aspect"], 0, 100000) or not _is_int(p["rp"], 0, 2000) or not _is_int(p["cx"], -2000, 2000)
            or not _is_int(p["cy"], -2000, 2000) or p["found"] not in (0, 1) or isinstance(p["found"], bool)
            or not _int_list(p["reach"], PUP.N_ANG, 0, 2000)):
        bad("pupil")
    h = rec["h2"]
    if (not isinstance(h, dict) or set(h) != {"how", "hue", "chroma"} or h["how"] not in ("collarette", "analogous")
            or not _is_int(h["hue"], 0, 360000) or not _is_int(h["chroma"], 0, 200000)):
        bad("h2")
    g = rec["gate"]
    if not isinstance(g, dict) or not set(g) <= set(GATE.RULES) or any(not GATE.valid_form(r, g[r]) for r in g):
        bad("gate")
    return rec


def canonical_json(rec):
    """The bytes of a record: JSON with sorted keys and no spaces, ASCII, whole numbers only (deterministic)."""
    return json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


class EyeProfile:
    """What was measured once about one eye (see the module text). rec is the validated record (a dict); the helpers decode it."""

    def __init__(self, rec, check=True):
        self.rec = validate(rec) if check else rec
        self._ring = None
        self._pupil = None

    # -- the record's fields
    @property
    def eye_id(self):
        return self.rec["eye_id"]

    @property
    def cls(self):
        return self.rec["cls"]

    @property
    def pad(self):
        return self.rec["pad"] / 1000.0

    @property
    def ease(self):
        return self.rec["ease"] / 1000.0

    @property
    def ring(self):
        """(360, 3) float32 0..1: the ring colours at the stored 8 bit precision."""
        if self._ring is None:
            self._ring = np.asarray(self.rec["ring"], np.float32).reshape(RING_BINS, 3) / np.float32(255.0)
        return self._ring

    @property
    def stats(self):
        """colour_stats() of the eye as it was measured (class decided on the unrounded ring, the numbers stored in whole units)."""
        s = self.rec["stats"]
        return {"class": self.rec["cls"], "L": s["L"] / 100.0, "C": s["C"] / 100.0, "h": s["h"] / 10.0, "mean_rgb": [v / 10.0 for v in s["rgb"]]}

    @property
    def pupil(self):
        """The dict pupil.analyse() returns (cx, cy, r_theta, rp, cls, aspect, found, ang) at the stored precision."""
        if self._pupil is None:
            self._pupil = PUP.from_record(self.rec["pupil"])
        return self._pupil

    @property
    def pupil_cls(self):
        return self.rec["pupil"]["cls"]

    @property
    def h2(self):
        """(rgb 0..1 accent colour, how, hue deg): the secondary hue, as palette.secondary_hue() returns it."""
        h = self.rec["h2"]
        return PAL.secondary_rgb(h["hue"] / 1000.0, h["chroma"] / 1000.0), h["how"], h["hue"] / 1000.0

    # -- the gate
    def gate(self, rules="lid"):
        """The gate result for a rule set: {ok, rule, values, why}; ok None for a rule this profile does not carry."""
        return GATE.gate(self, rules)

    def public(self):
        """What /api/enhance tells the page (about 0.4 KB): eye_id, version, class, ease, pupil class, and the gate's ok (with the
        reason codes of a failure) per rule. The page ignores the numbers; the picker uses them from the server's tiles."""
        gates = {}
        for r in GATE.RULES:
            s = self.rec["gate"].get(r)
            gates[r] = {"ok": None} if s is None else ({"ok": True} if s["ok"] else {"ok": False, "why": list(s["why"])})
        return {"eye_id": self.eye_id, "v": PROFILE_V, "cls": self.cls, "ease": self.ease, "pupil": {"cls": self.pupil_cls}, "gate": gates}

    # -- the wire form (what a seal carries)
    def to_wire(self):
        """The record as a seal carries it: canonical JSON, zlib level 9. At most MAX_PROFILE_BYTES."""
        data = zlib.compress(canonical_json(self.rec), 9)
        if len(data) > MAX_PROFILE_BYTES:
            raise ProfileError("eye profile: too large for a seal")
        return data

    @classmethod
    def from_wire(cls, data):
        """The profile of wire bytes (ProfileError for anything that is not one: size, zlib, JSON or schema)."""
        if not isinstance(data, (bytes, bytearray)) or not data or len(data) > MAX_PROFILE_BYTES:
            raise ProfileError("eye profile: no data or too large")
        d = zlib.decompressobj()
        try:
            raw = d.decompress(bytes(data), MAX_PROFILE_RAW + 1)
        except zlib.error:
            raise ProfileError("eye profile: not zlib") from None
        if len(raw) > MAX_PROFILE_RAW or d.unconsumed_tail or not d.eof or d.unused_data:
            raise ProfileError("eye profile: not one complete stream within its size")
        try:
            rec = json.loads(raw.decode("ascii"))
        except (ValueError, UnicodeDecodeError):
            raise ProfileError("eye profile: not JSON") from None
        return cls(rec)

    def __repr__(self):
        return f"EyeProfile({self.eye_id}, {self.cls}, pupil {self.pupil_cls})"


# ----------------------------------------------------------------------------- the eye
class EyeInput:
    """One eye as a function sees it: the restored iris square (RGB, cropped square, shrunk to max_side), its eye_id, the crop padding
    the page used, and the sealed profile when there is one. The grade is the studio grade of the engine (L.studio_grade through
    grade_disc), graded(Sd) per size, cached with a byte budget. Attribute names follow the design code's Iris (raw, name, digest, src,
    ease, graded, ring, stats, cls), so engine code written for it takes either.
      image     PIL image or the encoded bytes of one (JPEG or PNG); raw is then the bytes (the seed source of the design code)
      eye_id    16 hex; default: the sha256 prefix of raw, or of the pixels when there are no bytes
      pad       the crop padding (1.0 to 2.0); the iris radius is 1 / (2 pad) of the square
      max_side  the working copy cap (a preview 2048, a master 4096; the registry's work_side caps it further)
      profile   an EyeProfile (what the seal carries); ring, class, pupil and gate are read from it, else measured from the pixels"""

    def __init__(self, image, eye_id=None, pad=PAD, max_side=MAX_SIDE, profile=None, raw=None, name=""):
        if isinstance(image, (bytes, bytearray)):
            raw = bytes(image)
            image = Image.open(io.BytesIO(raw))
        im = image.convert("RGB")
        side = min(im.size)
        im = im.crop((0, 0, side, side))                      # as compose._irises
        self.max_side = max(8, int(max_side))
        if side > self.max_side:
            im = im.resize((self.max_side, self.max_side), Image.LANCZOS)
        self.src = im
        self.raw = None if raw is None else bytes(raw)
        self.name = name
        try:
            p = float(pad)
        except (TypeError, ValueError):
            p = PAD
        self.pad = min(2.0, max(1.0, p)) if p == p else PAD
        self.r_frac = L.iris_radius_frac(self.pad)
        if eye_id is None:
            eye_id = profile.eye_id if profile is not None else (eye_id_of(self.raw) if self.raw is not None else _pixel_id(im))
        if not is_eye_id(eye_id):
            raise ProfileError("eye id: 16 hex digits")
        if profile is not None and profile.eye_id != eye_id:
            raise ProfileError("eye profile: it belongs to another eye")
        self.eye_id = eye_id
        self.profile = profile
        self.digest = hashlib.sha256(self.raw if self.raw is not None else b"eye-id:" + eye_id.encode("ascii")).digest()
        self._grades = collections.OrderedDict()
        self._lock = threading.Lock()
        self._ease = None
        self._measured = None
        self.grade_seconds = 0.0

    @property
    def ease(self):
        """studio_ease of the iris as it came in (what L._grade_disc measures on every call), measured once, from these pixels."""
        if self._ease is None:
            t0 = time.perf_counter()
            self._ease = L.studio_ease(self.src, self.r_frac)
            self.grade_seconds += time.perf_counter() - t0
        return self._ease

    def graded(self, Sd):
        Sd = int(Sd)
        with self._lock:
            g = self._grades.get(Sd)
            if g is not None:
                self._grades.move_to_end(Sd)
                return g
        ease = self.ease
        t0 = time.perf_counter()
        g = np.ascontiguousarray(np.asarray(grade_disc(self.src, self.r_frac, Sd, ease)))
        self.grade_seconds += time.perf_counter() - t0
        with self._lock:
            self._grades[Sd] = g
            self._grades.move_to_end(Sd)
            while len(self._grades) > 1 and sum(a.nbytes for a in self._grades.values()) > GRADE_CACHE_BYTES:
                self._grades.popitem(last=False)
        return g

    # -- measured from the pixels (the canonical REF_SIDE grade)
    def _measure(self):
        if self._measured is None:
            fr = self.graded(REF_SIDE)
            sq, _ = tight(fr)
            info = {}
            ring = ring_colours(fr, info=info)
            stats = PAL.colour_stats(ring)
            self._measured = {"sq": sq, "ring": ring, "stats": stats, "outliers": info["outlier_bins"], "pupil": None}
        return self._measured

    @property
    def ring(self):
        return self.profile.ring if self.profile is not None else self._measure()["ring"]

    @property
    def stats(self):
        return self.profile.stats if self.profile is not None else self._measure()["stats"]

    @property
    def cls(self):
        return self.stats["class"]

    @property
    def pupil(self):
        """The pupil analysis (pupil.analyse on the tight 256 grade), or the profile's stored one."""
        if self.profile is not None:
            return self.profile.pupil
        m = self._measure()
        if m["pupil"] is None:
            m["pupil"] = PUP.analyse(m["sq"])
        return m["pupil"]

    def compute_profile(self, rules=GATE.RULES):
        """Measure this eye and return its EyeProfile (not attached: assign .profile to use it). Always from the pixels, never
        from an attached profile. rules: the gate rule sets to run ("fill" costs 0.9 to 1.7 s, "lid" 0.2 to 0.3 s per eye)."""
        m = self._measure()
        sq, ring, stats = m["sq"], m["ring"], m["stats"]
        pup = PUP.analyse(sq)
        m["pupil"] = pup
        rgb, how, h2, c2 = PAL.secondary_hue(sq, ring, stats)
        gates = {}
        for r in GATE.RULES:
            if r not in rules:
                continue
            if r == "lid":
                gates[r] = GATE.store_form(GATE.lid(sq, m["outliers"]))
            else:
                sq_fill, _ = tight(self.graded(FILL_SIDE))
                gates[r] = GATE.store_form(GATE.fill(sq_fill))
        rec = {"v": PROFILE_V, "eye_id": self.eye_id, "pad": int(round(self.pad * 1000)), "ease": int(round(float(self.ease) * 1000)),
               "cls": stats["class"],
               "stats": {"L": int(round(stats["L"] * 100)), "C": int(round(stats["C"] * 100)), "h": int(round(stats["h"] * 10)),
                         "rgb": [int(round(v * 10)) for v in stats["mean_rgb"]]},
               "ring": [int(v) for v in np.rint(ring.astype(np.float64) * 255.0).astype(np.int64).reshape(-1)],
               "pupil": PUP.to_record(pup),
               "h2": {"how": how, "hue": int(round(h2 * 1000)), "chroma": int(round(c2 * 1000))},
               "gate": gates}
        return EyeProfile(rec)

    def ensure_profile(self, rules=GATE.RULES):
        """The attached profile, or the one measured now (and attached)."""
        if self.profile is None:
            self.profile = self.compute_profile(rules)
        return self.profile

    def __repr__(self):
        return f"EyeInput({self.name!r}, {self.src.size[0]} px, {self.eye_id})"


Iris = EyeInput                      # the name the design code and the engine ports use


# ----------------------------------------------------------------------------- the entry points of the functions
_MEMO = collections.OrderedDict()
_MEMO_LOCK = threading.Lock()
MEMO_SIZE = 4                        # profiles kept by profile_of_bytes(memo=True): small records, bounded


def profile_of_bytes(data, pad=PAD, rules=GATE.RULES, max_side=MAX_SIDE, memo=False):
    """The profile of a clean preview given as its JPEG (or PNG) bytes: decode, measure, return an EyeProfile whose eye_id is
    eye_id_of(data). memo: keep the result (at most MEMO_SIZE) for a file that is asked about again and again (the sample eye)."""
    data = bytes(data)
    key = (eye_id_of(data), int(round(float(pad) * 1000)), tuple(rules), int(max_side))
    if memo:
        with _MEMO_LOCK:
            hit = _MEMO.get(key)
            if hit is not None:
                _MEMO.move_to_end(key)
                return hit
    prof = EyeInput(data, eye_id=key[0], pad=pad, max_side=max_side).compute_profile(rules)
    if memo:
        with _MEMO_LOCK:
            _MEMO[key] = prof
            while len(_MEMO) > MEMO_SIZE:
                _MEMO.popitem(last=False)
    return prof


def time_for_profile(left=None):
    """Is there time in this invocation to measure a profile (the guard of /api/enhance)? left: seconds, default L.time_left()."""
    return (L.time_left() if left is None else left) >= PROFILE_MIN_LEFT
