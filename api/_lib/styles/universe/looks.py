# -*- coding: utf-8 -*-
"""uni_looks: the layers of the UNIVERSE looks (brief 3.5). Every look exposes NAME, prepare(scene), base(scene, cv, y0, y1),
layers = [('splat', SplatList, 'add'|'screen') | ('chips', ChipList, None) | ('fn', f(scene, cv, y0, y1), None)].

Echo (default, 1 / 2 / 3-6 eyes), Deep Field, Vortex, Starfield (1 eye).
Rules kept everywhere: the material is the customer's own iris (enlarged, darkened, angle-true) plus real plate dust where a look needs it;
one or two hues from the eye; no rainbow gas, no glow over an iris, no studio text. Irises are pasted LAST by the engine.
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_looks.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports, no fall back to a picture without the plate); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.
# WP8B (step B) moved the seed, the plates version of every pick and the pair's fallback and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import math

import numpy as np
from PIL import Image

from .common import C, L, smooth, luma, ramp_rgb, get_src
from . import engine as EN
from .engine import to_lin, to_disp, SplatList
from . import fill as FL
from . import matter as MT
from . import plates as PL
from . import flakes as FK
from .grains import GrainList
from .common import limb_L

WIND_SET = [0.0, 25.0, 50.0, 130.0, 155.0, 180.0]      # brief 3.1: theta_w in degrees, counter-clockwise from 3 o'clock


def _wind(scene, tag="wind"):
    """Screen-angle wind (radians, y down) from the allowed set, +-10 deg jitter, seeded; never toward the text box."""
    rnd = scene.rand(tag)
    k = int(rnd.uniform() * len(WIND_SET))
    a = math.radians(WIND_SET[k] + (rnd.uniform() * 20 - 10))
    return -a


def _floor_colour(scene, Lstar=14.0):
    rc = np.mean([np.asarray(e.iris.ring).mean(0) for e in scene.eyes], 0)
    Y = ((Lstar + 16.0) / 116.0) ** 3
    disp = Y ** (1 / 2.2)
    return (rc * (disp / max(float(luma(rc)), 1e-3))).astype(np.float32)


def _accent_layer(scene, y0, y1, f, tag="accent", sg_R=0.75):
    """Warm sector cloud in the secondary hue H2 (blur 0.35 R, alpha 0.10 applied by the caller): (hc, Wc, 3) on the coarse grid."""
    e0 = scene.eyes[0]
    hh, cc = e0.src.h2
    acc = C.from_lch(58.0, min(cc, 40.0), hh).astype(np.float32)
    ang = (scene.rand(tag).uniform(1)[0]) * 2 * math.pi
    gx = scene.cx_mean + math.cos(ang) * 1.6 * scene.R
    gy = scene.cy_mean + math.sin(ang) * 1.6 * scene.R
    x, y = scene.band_xy(y0, y1, f)
    sg = sg_R * scene.R
    w = np.exp(-0.5 * ((x - gx) ** 2 + (y - gy) ** 2) / np.float32(sg * sg))
    return w[..., None] * acc[None, None, :]


def _vignette_field(scene, y0, y1, f, k=0.45):
    x, y = scene.band_xy(y0, y1, f)
    rc = np.sqrt((x - scene.W / 2.0) ** 2 + (y - scene.H / 2.0) ** 2)
    rcorner = math.hypot(scene.W / 2.0, scene.H / 2.0)
    return (1.0 - k * (rc / rcorner) ** 2)[..., None]


def _well(scene, e, mult=0.42, width=0.30):
    """dark socket: multiply mult at the union outline rising to 1 over `width` R."""
    return 1.0 - (1.0 - mult) * (1.0 - smooth(np.maximum(e, 0.0) / width))


def _soft_floor(cv, floor):
    """Lift the blacks smoothly to the floor colour (L* 14, never black) without flattening the structure: out = v + f exp(-v / 0.8 f)."""
    f = floor[None, None, :].astype(np.float32)
    cv += f * np.exp(-cv / (0.8 * f))


def _limb_L_old(src):
    """Median L* of the source iris's limb ring 0.90-0.98 R (cached on the Src)."""
    v = getattr(src, "_limb_Lv", None)
    if v is None:
        m = (src.rho > 0.90) & (src.rho < 0.98)
        lin = np.power(src.g[m], 2.2)
        Y = float(np.median(lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)))
        v = float(116.0 * Y ** (1 / 3) - 16.0) if Y > 0.008856 else 903.3 * Y
        src._limb_Lv = v
    return v


def _text_cull(scene, *lists):
    if scene.layout.text_box:
        for sl in lists:
            if sl is None:
                continue
            if isinstance(sl, EN.SpriteList):
                sl.cull([scene.layout.text_box], scene.fs)
            else:
                sl.cull([scene.layout.text_box])


def _prepare_eyes(scene, k_target=FL.K_TARGET):
    for e in scene.eyes:
        FL.setup_eye(scene, e, k_target)
        if e.magnification > FL.RESYNTH_M:
            e.fibre_noise = FL.FibreNoise(scene.rand("fibre", e.index))
        else:
            e.fibre_noise = None


def _fill_dark(scene, y0, y1, lum_k=1.0):
    """The finished enlarged-iris fill of a band on the coarse grid, display space (darkened in linear light to the eye's own L* target with the
    soft floor and the dark well, blended in OKLCH for pairs and groups, fibre re-synthesis above m 2.5). Returns (Fd, rn, e, kk)."""
    f = scene.f
    Fd, rn = FL.fill_band(scene, y0, y1, f)
    if lum_k != 1.0:
        Fd = Fd * lum_k
    return Fd, rn, rn - 1.0, None


def _flake_lift(eye):
    """Luminance lift of a flake relative to its own iris: a dark iris must stay the brightest object (AD), a pale one can throw brighter chips."""
    return float(np.clip(0.72 + 0.008 * float(eye.src.stats["L"]), 0.88, 1.10))


def _wall(scene):
    return scene.layout.aspect == "9:19.5"


# =============================================================================== Echo
class Echo:
    NAME = "echo"

    def halo_rows(self, scene):
        return 6 * scene.f + 2

    def prepare(self, scene):
        _prepare_eyes(scene, scene.opts.get("k_s", FL.K_TARGET))
        n = scene.n
        S = scene.S
        wall = _wall(scene)
        self.wind = _wind(scene)
        total = 260 if n == 1 else (160 * 2 if n == 2 else int(min(380, 60 * n)))
        if wall:
            total = int(total * 1.7)
        per = max(1, total // n)
        self.flakes = EN.SpriteList()
        self.depth = EN.SpriteList()
        for i in range(n):
            if wall:
                fl = FK.fibre_flakes(scene, i, per, reach=3.5, taper=1.4, e_cap=3.5, growth=0.5, lift=_flake_lift(scene.eyes[i]))
            else:
                fl = FK.fibre_flakes(scene, i, per, reach=1.6, taper=0.55, lift=_flake_lift(scene.eyes[i]), lum_k=(1.12 if n == 2 else 1.0))
            self.flakes.items.extend(fl.items)
            fb = FK.fibre_flakes(scene, i, max(3, per // 16), reach=(3.0 if wall else 1.3), taper=(1.2 if wall else 0.6), e0=0.15, blur_R=0.045,
                                 size_k=1.7, alpha=(0.6, 0.8), tag="depth", jets=(6, 9), jet_share=0.3, e_cap=(3.0 if wall else 1.5))
            self.depth.items.extend(fb.items)
        self.stars = MT.star_field(scene, 80 if n == 1 else 75)
        self.matter = GrainList()
        self.chips = MT.ChipList()
        self._dust(scene)
        if n == 2:
            self._duo_matter(scene)
        elif n >= 3:
            self._group_matter(scene)
        _text_cull(scene, self.flakes, self.depth, self.stars, self.matter, self.chips)
        self.layers = [("sprites", self.flakes, "over"), ("sprites", self.depth, "over"), ("splat", self.matter, "screen"),
                       ("chips", self.chips, None), ("splat", self.stars, "screen")]
        if wall:
            self._wall_accent(scene)
        if scene.opts.get("fill_only"):                 # test hook (T14): the fill alone, no flakes, stars, dust or chips
            self.layers = []

    def _wall_accent(self, scene):
        """AD D12: the tall canvas gets a P-UV-DUST accent in the lower third (the fill alone leaves the lower half flat). A plate that cannot be had stops the render (PlateUnavailable, NoPlate): never an accent-less picture."""
        e = scene.eyes[0]
        rnd = scene.rand("echo/wall")
        pick = PL.pick_wall(rnd, scene.pv)
        side = 2.6 * scene.W                                      # plate side in canvas px; its void (radius r0 x side) stays BELOW the canvas bottom
        cy = 1.0 * scene.H + 0.02 * scene.H + 1.05 * float(pick["void"]["r0"]) * side
        self.accent_plate = PL.Placed(pick, scene.W, scene.H, scene.W * 0.5, cy, scale=side / 1024.0, mirror=rnd.uniform() < 0.5, angle_deg=rnd.uniform() * 360.0,
                                      centre=(0.5, 0.5), grid_f=scene.f)
        scene.info["accent_plate"] = self.accent_plate.info
        self.accent_lut = plate_lut(e.src, "milky")
        self.layers.append(("fnc", self._accent_fn, "screen"))

    def _accent_fn(self, scene, lay, y0, y1, f):
        p = self.accent_plate.band(y0, y1, f)
        x, y = scene.band_xy(y0, y1, f)
        e0 = scene.eyes[0]
        # lower third only: fade in from 0.62 H to 0.80 H, and keep away from the iris
        wy = smooth((y - 0.58 * scene.H) / (0.20 * scene.H)) * (1.0 - smooth((y - 0.84 * scene.H) / (0.14 * scene.H)))
        wx = np.ones_like(x)
        rr = np.sqrt((x - e0.cx) ** 2 + (y - e0.cy) ** 2) / e0.R
        wr = smooth((rr - 2.2) / 1.2)
        q = np.clip(p / 0.7, 0, 1)
        col = lut_apply(self.accent_lut, 0.62 * q)
        lay += col * (q * 0.30 * wy * wx * wr)[..., None]

    def _dust(self, scene):
        rnd = scene.rand("echo/dust")
        for i, e in enumerate(scene.eyes):
            n = int(950 / scene.n)
            reach = 3.4 if _wall(scene) else 2.2
            phi = rnd.uniform(n) * 2 * math.pi
            ee = 0.05 + rnd.exponential(n, 0.9 if not _wall(scene) else 1.6)
            ee = np.minimum(ee, reach)
            xs = e.cx + (1 + ee) * e.R * np.cos(phi)
            ys = e.cy + (1 + ee) * e.R * np.sin(phi)
            col = np.minimum(C.ring_at(e.iris.ring, phi) * 1.9, 1.0)
            amp = 0.05 + 0.32 * rnd.uniform(n) ** 3
            rad = rnd.uniform(n, 0.0006, 0.0013) * scene.S * 1.5
            self.matter.add_grains(rnd, xs, ys, rad, col, amp * 1.6)

    def _duo_matter(self, scene):
        """Universe Duo (3.5.6): matter at 40 percent of Collision Infinity: lambda 160, chunks 18 per eye (x 0.6, AD), blobs 4 per eye, jets with
        B_g 320 (the AD's H11 comparison: the jets read too faint at 1024), r_d 0.45 R, chips brighter (L 0.80-0.95)."""
        w = self.wind
        for i in range(2):
            self.matter.extend(MT.outline_grains(scene, i, 115, wind=w, tag="outline"))
            MT.outline_chunks(scene, i, 18, self.chips, wind=w, tag="chunks")
            self.matter.dust.parts.extend(MT.blobs(scene, i, 4).parts)
        for k, nt in enumerate(MT.notch_list(scene.eyes, scene.layout.contacts)):
            MT.emit_notch(scene, nt, 320, 7, 38.0, 0.45, 0.85, self.matter, self.chips, f"n{k}")

    def _group_matter(self, scene):
        w = self.wind
        for i in range(scene.n):
            self.matter.extend(MT.outline_grains(scene, i, 70, wind=w, tag="outline", amp_k=0.9))
            MT.outline_chunks(scene, i, 5, self.chips, wind=w, tag="chunks")
        nts = MT.notch_list(scene.eyes, scene.layout.contacts)
        for k, nt in enumerate(nts):
            MT.emit_notch(scene, nt, 180, 4, 42.0, 0.45, 0.85, self.matter, self.chips, f"n{k}")
        scene.info["notches"] = len(nts)

    def base(self, scene, cv, y0, y1):
        f = scene.f
        Fd, rn, e, kk = _fill_dark(scene, y0, y1)
        acc = _accent_layer(scene, y0, y1, f, "echo/accent")
        a_acc = 0.10 * float(np.clip(min(FL.fill_style(e_).target for e_ in scene.eyes) / 16.5, 0.45, 1.0))   # a dark fill gets a weaker accent (alpha 0.10 at most)
        Fd = 1.0 - (1.0 - Fd) * (1.0 - a_acc * np.minimum(acc, 1.0))         # screen
        Fd *= _vignette_field(scene, y0, y1, f, 0.40)
        cv += scene.up(Fd, f, y0, y1)


# =============================================================================== the plate looks live in uni_plate_looks
from .plate_looks import DeepField, Vortex, Starfield, plate_lut, lut_apply, plate_t, diffraction_stars, milky_lut   # noqa: E402,F401

LOOKS = {"echo": Echo, "deepfield": DeepField, "vortex": Vortex, "starfield": Starfield}
