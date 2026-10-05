# -*- coding: utf-8 -*-
"""Makes the ported files of the universe family from the SCRATCH prototype by a listed set of edits, and nothing else (work package WP8A, step A:
"move first, merge later"). The committed files api/_lib/styles/universe/{layout,common,engine,comp,fill,flakes,grains,matter,plates,looks,
plate_looks}.py ARE the output of this tool (api/_lib/styles/universe/__init__.py, the family's contract, is written by hand):

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/port_universe.py            # writes the files
    python scripts/styles_tests/port_universe.py --check    # compares them with what the edits make of the scratch (exit 1 on a difference)

test_goldens_universe.py runs the check when the scratch tree is there (a LOCAL line), so "the port is the scratch with these edits" is a proven
sentence and not a claim, next to the pixel goldens that prove the same from the other side. Every edit is a substring replacement that must match
exactly the number of times it says, or a cut of whole lines between two markers; a scratch file that moved makes the tool stop.

The scratch files and where they went (the card of WP8 lists 14 files; two of them are not ported because the foundation already has them):
    universe.py        the family's entry render()          -> __init__.py (by hand: the contract of api/_lib/styles/__init__.py around render())
    uni_gate.py        the restoration gate, rule "fill"     -> api/_lib/styles/gate.py (WP3: calibrated rule sets, one schema)
    uni_pupil.py       byte identical to cx_pupil            -> api/_lib/styles/pupil.py (WP3)
    uni_layout, uni_common, uni_engine, uni_comp, uni_fill, uni_flakes, uni_grains, uni_matter, uni_plates, uni_looks, uni_plate_looks -> this tool

What the edits are, in five kinds (each file's header comment repeats the kinds that touch it):
  imports     the scratch paths and sys.path lines go; the engine core, the pupil and the atlas are the repo modules; the family's own modules are
              package relative
  plates      uni_plates.py read a folder of the plate workflow; here the plates come from api/_lib/styles/plates.py (the bundle at 1K, private
              storage at 4K, the baked registry: the crisp spirals are a flag of the registry and not measured at run time, the order of the
              prototype's list is kept because the pick is an index into it); a plate that cannot be had stops the render with PlateUnavailable
              (the master plan holds the order), where the prototype fell back to a picture without the plate: a silent substitution is exactly
              what the plan forbids
  atlas       the chip atlas is read through atlas.py (checked against the registry's sha256), as the uint8 planes the prototype loaded
  caches      the module level dict of decoded plates is a BoundedCache(2)
  text        no raw non ASCII character in a source file (the infinity sign and the middle dot of the names line are written as escapes)
plus: `from __future__ import annotations` after the docstring (Vercel's default Python is 3.12), and the psutil memory meter reads guard.memory_now().
"""
from __future__ import annotations

import argparse
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))      # the checkout (a suite runs from a prepared copy of this folder)
FAMILY = os.path.join(ROOT, "api", "_lib", "styles", "universe")

INF, DOT = chr(0x221E), chr(0xB7)          # the two glyphs of the names line (written as escapes in the ported source)


def sub(old, new, count=1):
    return ("sub", old, new, count)


def cut(start, end, new=""):
    """Whole lines from the first line that starts with `start` up to (not including) the next line that starts with `end`."""
    return ("cut", start, end, new)


# the order of the prototype's registry file (wave-y2/plates/plates.json) for the spirals: the pick is an index into the list of candidates, so the list
# keeps the prototype's order (the baked registry is sorted by id, which is another order); DUST and MILKY were sorted by id in the prototype already
SPIRAL_ORDER = [
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
]

_PLATES_NEW = '''import math

import numpy as np
from PIL import Image

from .. import core as C
from .. import plates as RG

'''

_PLATES_LOADER = '''# What the prototype's registry file listed in one order and the baked registry (sorted by id) lists in another: the spirals. The pick is an index into
# the candidate list, so the list keeps the prototype's order; a plate that is not named here (a later one) follows, sorted.
SPIRAL_ORDER = %SPIRAL_ORDER%


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


'''.replace("%SPIRAL_ORDER%", "(\n" + "".join(f'    "{i}",\n' for i in SPIRAL_ORDER) + ")")

# the three plate looks and the Echo wall accent chose a plate inside try / except Exception and drew a picture without it when anything failed:
# a silent substitution, which the master plan forbids (a missing, short or wrong plate holds the order). The blocks below lose the try.
_DEEP_OLD = '''        try:
            pl = [p for p in PL.plates("P-UV-DUST") if p["void"]["r0"] >= 0.185]
            pick = pl[int(rnd.uniform() * len(pl))]
            pcx, pcy, r0 = PL.void_of(pick)
            r_void = r0 * 1.10 * scene.S
            self.plate = PL.Placed(pick, scene.W, scene.H, e.cx, e.cy, r_void_px=r_void, mirror=rnd.uniform() < 0.5, grid_f=scene.f)
            scene.info["plate"] = self.plate.info
        except Exception as ex:                      # a missing, empty or corrupt plate never stops an order: the look falls back to the fill, flakes and stars
            self.plate = None
            scene.info["plate_fallback"] = f"{type(ex).__name__}: {ex}"[:120]
'''
_DEEP_NEW = '''        pl = [p for p in PL.plates("P-UV-DUST") if p["void"]["r0"] >= 0.185]
        pick = pl[int(rnd.uniform() * len(pl))]
        pcx, pcy, r0 = PL.void_of(pick)
        r_void = r0 * 1.10 * scene.S
        self.plate = PL.Placed(pick, scene.W, scene.H, e.cx, e.cy, r_void_px=r_void, mirror=rnd.uniform() < 0.5, grid_f=scene.f)
        scene.info["plate"] = self.plate.info
'''
_VORTEX_OLD = '''        try:
            pl = PL.spiral_plates(0.20)
            pick = pl[int(rnd.uniform() * len(pl))]
            pcx, pcy, r0 = PL.void_of(pick)
            r_void = min(1.10 * e.R, 1.08 * r0 * scene.S)       # void registered to 1.10 R on the iris centre (crisp, circular plates only), never enlarged more than x1.1
            self.plate = PL.Placed(pick, scene.W, scene.H, e.cx, e.cy, r_void_px=r_void, mirror=rnd.uniform() < 0.5, grid_f=scene.f)
            self.r_void_n = r_void / e.R                       # the plate's crisp void edge, in R: the plate fades in over 0.08 R beyond it (a visible void edge is a hard fail)
            scene.info["plate"] = self.plate.info
        except Exception as ex:
            self.plate = None
            scene.info["plate_fallback"] = f"{type(ex).__name__}: {ex}"[:120]
'''
_VORTEX_NEW = '''        pl = PL.spiral_plates(0.20)
        pick = pl[int(rnd.uniform() * len(pl))]
        pcx, pcy, r0 = PL.void_of(pick)
        r_void = min(1.10 * e.R, 1.08 * r0 * scene.S)       # void registered to 1.10 R on the iris centre (crisp, circular plates only), never enlarged more than x1.1
        self.plate = PL.Placed(pick, scene.W, scene.H, e.cx, e.cy, r_void_px=r_void, mirror=rnd.uniform() < 0.5, grid_f=scene.f)
        self.r_void_n = r_void / e.R                       # the plate's crisp void edge, in R: the plate fades in over 0.08 R beyond it (a visible void edge is a hard fail)
        scene.info["plate"] = self.plate.info
'''
_STAR_OLD = '''        try:
            entry, mirror, rot, tgt = PL.milky_choice(rnd, 32.0, 12.0)
            rot = float(np.clip(rot, -5.0, 5.0))
            scale = 1.10 * scene.S / 1024.0              # x1.10 the canvas: the plate covers the canvas through its rotation, never enlarged more than x1.1
            cx = scene.W / 2.0 + (rnd.uniform() - 0.5) * 0.02 * scene.S
            cy = scene.H / 2.0 + (rnd.uniform() - 0.5) * 0.02 * scene.S
            self.plate = PL.Placed(entry, scene.W, scene.H, cx, cy, scale=scale, angle_deg=rot, mirror=mirror, centre=(0.5, 0.5))
            scene.info["plate"] = self.plate.info
        except Exception as ex:                      # no plate: a blue-black sky with stars only
            self.plate = None
            scene.info["plate_fallback"] = f"{type(ex).__name__}: {ex}"[:120]
'''
_STAR_NEW = '''        entry, mirror, rot, tgt = PL.milky_choice(rnd, 32.0, 12.0)
        rot = float(np.clip(rot, -5.0, 5.0))
        scale = 1.10 * scene.S / 1024.0              # x1.10 the canvas: the plate covers the canvas through its rotation, never enlarged more than x1.1
        cx = scene.W / 2.0 + (rnd.uniform() - 0.5) * 0.02 * scene.S
        cy = scene.H / 2.0 + (rnd.uniform() - 0.5) * 0.02 * scene.S
        self.plate = PL.Placed(entry, scene.W, scene.H, cx, cy, scale=scale, angle_deg=rot, mirror=mirror, centre=(0.5, 0.5))
        scene.info["plate"] = self.plate.info
'''
_WALL_OLD = '''        try:
            pl = PL.plates("P-UV-DUST")
            pick = pl[int(rnd.uniform() * len(pl))]
            side = 2.6 * scene.W                                      # plate side in canvas px; its void (radius r0 x side) stays BELOW the canvas bottom
            cy = 1.0 * scene.H + 0.02 * scene.H + 1.05 * float(pick["void"]["r0"]) * side
            self.accent_plate = PL.Placed(pick, scene.W, scene.H, scene.W * 0.5, cy, scale=side / 1024.0, mirror=rnd.uniform() < 0.5, angle_deg=rnd.uniform() * 360.0,
                                          centre=(0.5, 0.5), grid_f=scene.f)
            scene.info["accent_plate"] = self.accent_plate.info
        except Exception as ex:
            scene.info["plate_fallback"] = f"{type(ex).__name__}: {ex}"[:120]
            return
'''
_WALL_NEW = '''        pl = PL.plates("P-UV-DUST")
        pick = pl[int(rnd.uniform() * len(pl))]
        side = 2.6 * scene.W                                      # plate side in canvas px; its void (radius r0 x side) stays BELOW the canvas bottom
        cy = 1.0 * scene.H + 0.02 * scene.H + 1.05 * float(pick["void"]["r0"]) * side
        self.accent_plate = PL.Placed(pick, scene.W, scene.H, scene.W * 0.5, cy, scale=side / 1024.0, mirror=rnd.uniform() < 0.5, angle_deg=rnd.uniform() * 360.0,
                                      centre=(0.5, 0.5), grid_f=scene.f)
        scene.info["accent_plate"] = self.accent_plate.info
'''

_ATLAS_NEW = '''_A8 = C.BoundedCache(1)


def atlas():
    """The chip atlas as the prototype's loader returned it: the uint8 planes lum and mask (n, 128, 128) and n. The file is the foundation's
    (api/_lib/styles/atlas.py: one copy, read once, checked against the registry's sha256); its float planes are v / 255, and v / 255 * 255 rounds back
    to the very byte (test_goldens_universe.py compares the planes with the file's own)."""
    got = _A8.get("atlas")
    if got is None:
        A = AT.chips()
        got = _A8.put("atlas", {"lum": np.rint(A.lum * np.float32(255.0)).astype(np.uint8), "mask": np.rint(A.mask * np.float32(255.0)).astype(np.uint8), "n": int(A.n)})
    return got


'''

# (scratch file relative to wave-y3, destination relative to api/_lib/styles/universe, header words, edits)
PORTS = [
    ("designs/uni_layout.py", "layout.py", "no code changed", []),
    ("designs/uni_common.py", "common.py", "imports; the memory meter is guard.memory_now()", [
        cut("import os, sys, math, time, hashlib", "FILL_SD = ", "import math\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .. import core as C\nfrom .. import pupil as PUP\n\nL = C.L\n\n"),
        sub('''def peak_rss_mb():
    try:
        import psutil
        p = psutil.Process()
        mi = p.memory_info()
        return round(getattr(mi, "peak_wset", mi.rss) / 2 ** 20)
    except Exception:
        return None
''', '''def peak_rss_mb():
    """The high-water mark of this process's resident memory in MB, or None where the platform says nothing (api/_lib/styles/guard.py reads it: /proc on
    Linux, psapi on Windows; psutil is not a dependency)."""
    try:
        from .. import guard
        hwm = guard.memory_now()[1]
        return None if hwm is None else round(hwm)
    except Exception:
        return None
'''),
    ]),
    ("designs/uni_engine.py", "engine.py", "imports, ASCII escapes for the two glyphs of the names line", [
        cut("import math, time, hashlib", "BAND_PX = ",
            "import math\nimport time\n\nimport numpy as np\nfrom PIL import Image, ImageDraw\n\nfrom .common import (C, L, smooth, luma, get_src, f3_disc, enlarge_band, ramp_rgb, peak_rss_mb, FILL_SD)\n"
            "from . import layout as LO\nfrom . import comp as CO\nfrom .. import pupil as PUP\n\n"),
        sub("from designs import uni_matter as MT\n", "from . import matter as MT\n", 2),
        sub('text = (" ' + INF + ' ".join(names[:2]))', 'text = (" \\u221e ".join(names[:2]))'),
        sub('text = " ' + DOT + ' ".join(names)', 'text = " \\u00b7 ".join(names)'),
        sub('if ch == "' + INF + '" and', 'if ch == "\\u221e" and'),
    ]),
    ("designs/uni_comp.py", "comp.py", "imports", [
        cut("import math", "EDGE_K = ", "import math\n\nimport numpy as np\n\nfrom .common import C, smooth, luma\nfrom .. import pupil as PUP\n\n"),
    ]),
    ("designs/uni_fill.py", "fill.py", "imports", [
        cut("import math", "K_TARGET = ", "import math\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .common import C, smooth, luma, ramp_rgb, enlarge_band, EImgs, limb_L\nfrom .engine import to_lin, to_disp\n\n"),
        sub("    from designs.uni_engine import NoiseGrid\n", "    from .engine import NoiseGrid\n"),
    ]),
    ("designs/uni_flakes.py", "flakes.py", "imports", [
        cut("import math", "LIGHT = ", "import math\n\nimport numpy as np\n\nfrom .common import C\nfrom .engine import SpriteList\n\n"),
    ]),
    ("designs/uni_grains.py", "grains.py", "imports", [
        cut("import math", "POLY_MIN_PX = ", "import math\n\nimport numpy as np\n\nfrom .engine import SplatList\n\n"),
    ]),
    ("designs/uni_matter.py", "matter.py", "imports, the chip atlas read through atlas.py", [
        cut("import os, math", "COPPER = ", "import math\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .. import atlas as AT\nfrom .common import C, smooth, luma, ramp_rgb\n"
            "from .engine import SplatList\nfrom .grains import GrainList\nfrom .flakes import fibre_flakes  # noqa: F401  (the flakes are sprites now, see flakes.py)\n\n"),
        cut("def atlas():", "# ----------------------------------------------------------------------------- colours", _ATLAS_NEW),
    ]),
    ("designs/uni_plates.py", "plates.py", "imports, the plates from the foundation's library (bundle, storage, baked registry), a bounded cache", [
        cut("import os, json, math", "MAX_UP = ", _PLATES_NEW),
        sub("_REG = {}\n_IMG = {}\n", "_IMG = C.BoundedCache(2)\n"),
        cut("def registry(which=", "def void_of(entry):", _PLATES_LOADER),
        cut("_SPIRAL_OK = None", "# Gemini drew these three Milky Way plates", '''def spiral_plates(min_r0=0.20):
    """The crisp P-DN-SPIRAL plates (a flag of the baked registry: the prototype measured it on the 1k LOD at run time, the same measurement is
    baked offline, scripts/bake_plates_registry.py) whose void radius is at least min_r0, in the prototype's order. Four of the 16 curated spirals have
    a soft, lopsided void: they read as a displaced second disc behind the iris (AD C6) and are not usable in the registry."""
    out = [p for p in plates("P-DN-SPIRAL") if p["void"]["r0"] >= min_r0]
    if not out:
        raise RG.NoPlate(f"the plate library has no crisp P-DN-SPIRAL plate with a void of {min_r0} or more")
    return out


'''),
    ]),
    ("designs/uni_looks.py", "looks.py", "imports, no fall back to a picture without the plate", [
        cut("import math", "WIND_SET = ",
            "import math\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .common import C, L, smooth, luma, ramp_rgb, get_src\nfrom . import engine as EN\n"
            "from .engine import to_lin, to_disp, SplatList\nfrom . import fill as FL\nfrom . import matter as MT\nfrom . import plates as PL\nfrom . import flakes as FK\n"
            "from .grains import GrainList\nfrom .common import limb_L\n\n"),
        sub("from designs.uni_plate_looks import DeepField,", "from .plate_looks import DeepField,"),
        sub(_WALL_OLD, _WALL_NEW),
    ]),
    ("designs/uni_plate_looks.py", "plate_looks.py", "imports, no fall back to a picture without the plate", [
        cut("import math", "COPPER5 = ",
            "import math\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .common import C, smooth, luma, ramp_rgb\nfrom . import engine as EN\nfrom .engine import SplatList\n"
            "from . import fill as FL\nfrom . import matter as MT\nfrom . import plates as PL\nfrom . import looks as LK\nfrom . import flakes as FK\n\n"),
        sub(_DEEP_OLD, _DEEP_NEW),
        sub(_VORTEX_OLD, _VORTEX_NEW),
        sub(_STAR_OLD, _STAR_NEW),
    ]),
]


def _apply(text, edits, name):
    for e in edits:
        if e[0] == "sub":
            _, old, new, count = e
            n = text.count(old)
            if n != count:
                raise SystemExit(f"{name}: expected {count} of {old[:70]!r}, found {n}")
            text = text.replace(old, new)
        else:
            _, start, end, new = e
            lines = text.split("\n")
            i = next((k for k, ln in enumerate(lines) if ln.startswith(start)), None)
            if i is None:
                raise SystemExit(f"{name}: no line starts with {start[:70]!r}")
            j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith(end)), None)
            if j is None:
                raise SystemExit(f"{name}: no line starts with {end[:70]!r} after {start[:40]!r}")
            put = new.split("\n")[:-1] if new.endswith("\n") else ([new] if new else [])
            text = "\n".join(lines[:i] + put + lines[j:])
    return text


def _with_future(text, words, src):
    """After the module docstring: the future import and a note of what the file is."""
    tree = ast.parse(text)
    end = tree.body[0].end_lineno
    lines = text.split("\n")
    note = (f"# PORT of work package WP8A (step A): {src} of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_universe.py lists\n"
            f"# ({words}); test_goldens_universe.py replays the edits on the scratch and the pixels of the scratch's own pictures.")
    return "\n".join(lines[:end] + ["from __future__ import annotations", ""] + note.split("\n") + [""] + lines[end:])


def build(y3):
    """{destination relative to api/_lib/styles/universe: the text of the ported file}."""
    out = {}
    for src, dst, words, edits in PORTS:
        with open(os.path.join(y3, src), encoding="utf-8", newline="") as f:
            text = f.read().replace("\r\n", "\n")
        text = _apply(text, edits, src)
        out[dst] = _with_future(text, words, os.path.basename(src))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
    made = build(y3)
    bad = 0
    for dst, text in sorted(made.items()):
        path = os.path.join(FAMILY, *dst.split("/"))
        if a.check:
            try:
                with open(path, encoding="utf-8", newline="") as f:
                    have = f.read().replace("\r\n", "\n")
            except OSError:
                have = None
            if have != text:
                bad += 1
                print(f"DIFFERS  {dst}")
            else:
                print(f"same     {dst}")
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print(f"wrote    {dst} ({len(text)} bytes)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
