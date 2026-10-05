# -*- coding: utf-8 -*-
"""uni_plates: runtime loader / placer of the mono plates of the UNIVERSE family (P-UV-DUST, P-UV-MILKY, P-DN-SPIRAL). numpy + PIL only.

A plate is a neutral (grey) luminance image that a look tints with the eye's own colours. Placement is one PIL affine transform per band
(bicubic, float), with a soft fade at the plate border, an optional rotation (screen degrees counter-clockwise), an optional mirror and a
registration of the plate's void circle onto a circle of the canvas. A plate is never enlarged more than x1.1 at the canvas size in use
(the 1k LOD serves up to 1.1 x 1024, otherwise the 4k file).
"""
from __future__ import annotations

# PORT of work package WP8A (step A): uni_plates.py of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists
# (imports, the plates from the foundation's library (bundle, storage, baked registry), a bounded cache); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.
# WP8B (step B) moved the seed, the plates version of every pick and the pair's fallback and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py.

import math

import numpy as np
from PIL import Image

from .. import core as C
from .. import plates as RG

MAX_UP = 1.1
FADE = 0.035

_IMG = C.BoundedCache(2)


# What the prototype's registry file listed in one order and the baked registry (sorted by id) lists in another: the spirals. The pick is an index into
# the candidate list, so the list keeps the prototype's order; a plate that is not named here (a later one) follows, sorted.
SPIRAL_ORDER = (
    "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v8__pro4K__t0",
    "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v11__pro4K__t0",
    "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v4__pro4K__t0_g50",
    "P-DN-SPIRAL__arms-three_sense-cw_wound-tight__v10__pro4K__t0",
    "P-DN-SPIRAL__arms-three_sense-cw_wound-tight__v10__pro4K__t2",
    "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v10__pro4K__t1",
    "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v10__pro4K__t0_g50",
    "P-DN-SPIRAL__arms-two_sense-ccw_wound-loose__v10__pro4K__t0",
    "P-DN-SPIRAL__arms-three_sense-ccw_wound-loose__v10__pro4K__t2",
    "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v10__pro4K__t0",
    "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v10__pro4K__t2",
    "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v12__pro4K__t0",
    "P-DN-SPIRAL__arms-two_sense-cw_wound-tight__v12__pro4K__t1",
    "P-DN-SPIRAL__arms-three_sense-ccw_wound-loose__v12__pro4K__t0",
    "P-DN-SPIRAL__arms-two_sense-cw_wound-loose__v12__pro4K__t0",
    "P-DN-SPIRAL__arms-two_sense-ccw_wound-tight__v12__pro4K__t1",
)


def _entry(pid):
    """A plate as the looks read it (the prototype's registry entry): id, family, void {cx, cy, r0} and the family's own fields (axis_deg of a Milky Way
    plate, ...). Built from the baked record: nothing is read from a folder, nothing is measured."""
    rec = RG.record(pid)
    e = {"id": pid, "family": rec["family"]}
    v = rec.get("void")
    if v:
        e["void"] = {"cx": v[0], "cy": v[1], "r0": v[2]}
    e.update(rec.get("extra") or {})
    return e


def plates(family, pv=None):
    """The usable plates of a family a spec of plates version pv may pick (None: the current version), in the prototype's order. NoPlate when there is
    none (the library has nothing at that version): the pick of a look is an index into this list."""
    ids = list(RG.ids(family, pv))
    if family == "P-DN-SPIRAL":
        rank = {pid: k for k, pid in enumerate(SPIRAL_ORDER)}
        ids.sort(key=lambda i: (rank.get(i, len(rank)), i))
    if not ids:
        raise RG.NoPlate(f"the plate library has no {family} plate at plates version {pv if pv is not None else 'current'}")
    return [_entry(i) for i in ids]


def _load(entry, lod):
    """PIL float image of a plate at 1k (the bundled LOD), 2k (a LANCZOS mip of the 4k file, built once) or 4k, with a soft border fade. The 4k file is
    fetched through api/_lib/styles/plates.py (cache, then private storage, sha256 checked): PlateUnavailable when it is not the plate the registry names."""
    key = (entry["id"], lod)
    im = _IMG.get(key)
    if im is None:
        if lod == "2k":
            raw = RG.fetch_4k(entry["id"]).convert("L").resize((2048, 2048), Image.LANCZOS)
        elif lod == "1k":
            raw = RG.load_1k(entry["id"]).convert("L")
        else:
            raw = RG.fetch_4k(entry["id"]).convert("L")
        a = np.asarray(raw, np.float32) / 255.0
        n = a.shape[0]
        ax = (np.arange(n, dtype=np.float32) + 0.5) / n
        edge = np.minimum(ax, 1.0 - ax) / FADE
        e = np.clip(edge, 0, 1)
        e = e * e * (3 - 2 * e)
        a = a * e[None, :] * e[:, None]
        im = _IMG.put(key, Image.fromarray(a, "F"))
    return im


def void_of(entry):
    v = entry.get("void")
    if v is None:
        return 0.5, 0.5, 0.25
    return v["cx"], v["cy"], v["r0"]


class Placed:
    """A plate registered on a canvas: void centre -> (cx, cy), void radius -> r_void_px (or, for band plates, scale given directly)."""

    def __init__(self, entry, W, H, cx, cy, r_void_px=None, scale=None, angle_deg=0.0, mirror=False, centre=None, grid_f=1):
        self.entry = entry
        pcx, pcy, r0 = void_of(entry)
        if centre is not None:
            pcx, pcy = centre
        px = 1024
        self.scale_c = (r_void_px / (r0 * px)) if scale is None else scale     # canvas px per 1k-plate px
        side_c = self.scale_c * px                     # plate side in canvas px
        side_g = side_c / float(grid_f)                # ... on the grid the look samples it on (coarse grids sample it at 1/f)
        self.lod = "1k" if side_g <= MAX_UP * 1024 else ("2k" if side_g <= MAX_UP * 2048 else "4k")
        nsrc = {"1k": 1024.0, "2k": 2048.0, "4k": 4096.0}[self.lod]
        self.upscale = side_g / nsrc
        self.im = _load(entry, self.lod)
        n = nsrc
        self.W, self.H = W, H
        self.cx, self.cy = cx, cy
        f = n / px                                    # source px per 1k px
        s = self.scale_c / f                          # canvas px per source px
        phi = math.radians(angle_deg)
        c, sn = math.cos(phi), math.sin(phi)
        mx = -1.0 if mirror else 1.0
        # inverse map canvas -> source: p = pc + Mx . Rot(-phi) . (q - c) / s
        a00, a01 = mx * c / s, mx * -sn / s
        a10, a11 = sn / s, c / s
        self.pc = (pcx * n, pcy * n)
        self.A = (a00, a01, a10, a11)
        self.info = {"id": entry["id"], "lod": self.lod, "upscale": round(self.upscale, 3), "angle": angle_deg, "mirror": mirror}

    def band(self, y0, y1, f=1):
        """The plate on canvas rows y0..y1 (float 0..1); with f > 1 on the coarse grid (hc, Wc) of those rows (y0 a multiple of f)."""
        a00, a01, a10, a11 = self.A
        pcx, pcy = self.pc
        h = y1 - y0
        hc = int(math.ceil(h / float(f)))
        Wc = int(math.ceil(self.W / float(f)))
        c0 = pcx - a00 * self.cx - a01 * (self.cy - y0)
        f0 = pcy - a10 * self.cx - a11 * (self.cy - y0)
        out = self.im.transform((Wc, hc), Image.AFFINE, (a00 * f, a01 * f, c0, a10 * f, a11 * f, f0), resample=Image.BICUBIC)
        return np.clip(np.asarray(out, np.float32), 0.0, 1.0)


def spiral_plates(min_r0=0.20, pv=None):
    """The crisp P-DN-SPIRAL plates (a flag of the baked registry: the prototype measured it on the 1k LOD at run time, the same measurement is
    baked offline, scripts/bake_plates_registry.py) whose void radius is at least min_r0, in the prototype's order. Four of the 16 curated spirals have
    a soft, lopsided void: they read as a displaced second disc behind the iris (AD C6) and are not usable in the registry."""
    out = [p for p in plates("P-DN-SPIRAL", pv) if p["void"]["r0"] >= min_r0]
    if not out:
        raise RG.NoPlate(f"the plate library has no crisp P-DN-SPIRAL plate with a void of {min_r0} or more")
    return out


# Gemini drew these three Milky Way plates in visible tiles (rectangular blocks of different sky brightness, clear at gamma 0.6 with the luminance x3):
# a plate with a straight-edged block is a hard fail (brief 6.4 'plate edge'), so they are vetoed here. Checked 2026-09-30 on the contact sheet.
MILKY_BLOCKED = ("P-UV-MILKY__band-high_stars-dense__v1__pro4K__t0", "P-UV-MILKY__band-high_stars-sparse__v1__pro4K__t0",
                 "P-UV-MILKY__band-high_stars-sparse__v1__pro4K__t1")


def milky_plates(pv=None):
    return [e for e in plates("P-UV-MILKY", pv) if e["id"] not in MILKY_BLOCKED]


def milky_choice(rnd, target_deg=32.0, jitter=12.0, pv=None):
    """(entry, mirror, rotation deg) so that the band axis lands within ~8 degrees of the seeded target (axes 25-45 deg or mirror)."""
    tgt = target_deg + (rnd.uniform() * 2 - 1) * jitter
    best = None
    for e in milky_plates(pv):
        for mir in (False, True):
            ax = e["axis_deg"] % 180.0
            if mir:
                ax = (180.0 - ax) % 180.0
            diff = ((tgt - ax + 90.0) % 180.0) - 90.0
            key = abs(diff)
            if best is None or key < best[0]:
                best = (key, e, mir, diff)
    _, e, mir, diff = best
    return e, mir, float(np.clip(diff, -8.0, 8.0)), tgt


DEEP_R0 = 0.185             # Deep Field picks among the DUST plates whose void is at least this large


def _pick(rnd, pl):
    return pl[int(rnd.uniform() * len(pl))]


def pick_wall(rnd, pv=None):
    """The DUST plate of the Echo wall canvas's accent (any of the usable ones at plates version pv; the first draw of rnd)."""
    return _pick(rnd, plates("P-UV-DUST", pv))


def pick_deep(rnd, pv=None):
    """The DUST plate of Deep Field (a void of DEEP_R0 or more; the next draw of rnd)."""
    pl = [p for p in plates("P-UV-DUST", pv) if p["void"]["r0"] >= DEEP_R0]
    if not pl:
        raise RG.NoPlate(f"the plate library has no P-UV-DUST plate with a void of {DEEP_R0} or more at plates version {pv if pv is not None else 'current'}")
    return _pick(rnd, pl)


def pick_vortex(rnd, pv=None):
    """The crisp SPIRAL plate of Vortex (the first draw of rnd)."""
    return _pick(rnd, spiral_plates(0.20, pv))
