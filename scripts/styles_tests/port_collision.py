# -*- coding: utf-8 -*-
"""Makes the ported files of the collision family from the SCRATCH prototype by a listed set of edits, and nothing else (work package WP7A,
step A: "move first, merge later"). The committed files api/_lib/styles/collision/*.py ARE the output of this tool:

    set SNAPEYES_SCRATCH_DG1=<the wave-dg1/final folder of the scratch tree>
    python scripts/styles_tests/port_collision.py            # writes the files
    python scripts/styles_tests/port_collision.py --check    # compares them with what the edits make of the scratch (exit 1 on a difference)

The source is the DG1 snapshot (wave-dg1/final): the round 2c collision code of wave-y3 with the design gate DG1's smooth planned seam (seam_plan.py),
its automatic stack lens (lens_mode.py), the review fixes (a bar pupil is refused, the dilated pupil is never touched) and the owner's reading of the
seam budget E1 (the mixed share at most about 3 percent, the seam band at most 4 percent of an iris). SOURCES holds the sha256 of every source file:
the snapshot the goldens were recorded on. test_goldens_collision.py runs the check when the scratch tree is there (a LOCAL line), so "the port is
the scratch with these edits" is a proven sentence next to the pixel goldens that prove it from the other side.

Every edit is a substring replacement that must match exactly the number of times it says, or a cut of whole lines between two markers; a scratch
file that moved makes the tool stop. What the edits are, in five kinds (each file's header comment repeats the kinds that touch it):
  imports     the scratch paths and sys.path lines go; the engine core, palette and pupil are the repo modules (api/_lib/styles/core.py, palette.py,
              pupil.py: WP3 and WP4 ported cx_palette and cx_pupil once for every family, byte for byte the same code), the collision modules are the
              siblings of this package under their own names (collision.py is engine.py, cx_kit is kit.py, cx_plates is jetplates.py, ...)
  plates      the JET and RIVER plates are read from the baked plate registry (styles/plates.py, 1K files in the bundle) instead of being fitted and cut
              from raw 4K files at run time; the cloud plates of the haze come from the same loader (the plate workflow's registry is not in a function)
  caches      a module level dict keyed by the eye becomes a BoundedCache (a warm instance renders for hours)
  files       the loader of an eye by a calibration name, the atlas read from a path and the Windows memory meter are gone (the atlas comes through
              styles/atlas.py, checked against the registry's sha256)
  ids         the registry ids of the styles are not written in a docstring or tested by a string (the style check refuses a literal id outside the
              registry): the one place that keeps them is scenes.py, whose scene key is part of the prototype's seed (step A), allowed by name
plus `from __future__ import annotations` after the docstring (Vercel's default Python is 3.12).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))      # the checkout (a suite runs from a prepared copy of this folder)
DEST = os.path.join(ROOT, "api", "_lib", "styles", "collision")


def sub(old, new, count=1):
    return ("sub", old, new, count)


def cut(start, end, new=""):
    """Whole lines from the first line that starts with `start` up to (not including) the next line that starts with `end`."""
    return ("cut", start, end, new)


# (scratch file relative to wave-dg1/final, destination relative to api/_lib/styles/collision, header words, edits)
PORTS = [
    ("fx/lens_mode.py", "lens_mode.py", "no edit", []),
    ("fx/seam_plan.py", "seam_plan.py", "no edit", []),
    ("fx/collision_layouts.py", "scenes.py", "the prototype's scene key is kept (it is part of the step A seed)", [
        sub("scratch prototype.", "ported from the scratch prototype."),
    ]),
    ("fx/collision_comp.py", "compositor.py", "imports, a bounded cache", [
        sub("scratch prototype. numpy only.", "ported from the scratch prototype. numpy only."),
        sub("import numpy as np\nfrom . import seam_plan as SP\n", "import numpy as np\n\nfrom .. import core as C\nfrom . import seam_plan as SP\n"),
        sub("from .collision_layouts import circle_intersections", "from .scenes import circle_intersections"),
        sub("        _RAG_THR[round(share, 3)] = thr\n", "        _RAG_THR.put(round(share, 3), thr)\n"),
        sub("_RAG_THR = {}\n", "_RAG_THR = C.BoundedCache(8)\n"),
    ]),
    ("designs/cx_raster.py", "raster.py", "the atlas class that read a path is gone (styles/atlas.py)", [
        cut("class Atlas:", "def _bilinear(a, x, y):", "# the chip atlas is read through api/_lib/styles/atlas.py (checked against the registry's sha256), never from a path\n\n\n"),
    ]),
    ("designs/cx_powder.py", "powder.py", "imports, the JET and RIVER plates, a bounded cache", [
        cut("import math", "NB = 1440", "import math\n\nimport numpy as np\n\nfrom .. import core as C\nfrom . import raster as RS\n\n"),
        sub("    import cx_plates as PL\n", "    from . import jetplates as PL\n", 4),
        sub("_DITHER_TILES = {}\n", "_DITHER_TILES = C.BoundedCache(16)\n"),
        sub("        t = g.random((n, n)).astype(np.float32)\n        if len(_DITHER_TILES) > 16:\n            _DITHER_TILES.clear()\n        _DITHER_TILES[(seed, n)] = t\n",
            "        t = _DITHER_TILES.put((seed, n), g.random((n, n)).astype(np.float32))\n"),
    ]),
    ("designs/cx_extra.py", "extra.py", "imports", [
        cut("import math", "NB = PW.NB", "import math\n\nimport numpy as np\n\nfrom . import powder as PW\nfrom . import raster as RS\nfrom .compositor import value_noise, smooth\n\n"),
    ]),
    ("designs/cx_fill.py", "fill.py", "imports", [
        cut("import math", "BAND_ROWS = 256", "import math\n\nimport numpy as np\n\nfrom .. import core as C\nfrom . import powder as PW\nfrom . import raster as RS\n\n"),
    ]),
    ("designs/cx_haze.py", "haze.py", "imports, the cloud plates come from the plate loader", [
        cut("import os, sys, math", "def _ss(x0, x1, x):", "import math\n\nimport numpy as np\n\nfrom .. import core as C\nfrom .. import plates as _PLATES\n\n\n"
            "def registry():\n    \"\"\"The plate loader (api/_lib/styles/plates.py): the pick and the placement of the plate workflow's registry, read only, on the baked library.\"\"\"\n"
            "    return _PLATES\n\n\n"),
        sub("    from fx import core as CC\n", "    from .. import core as CC\n"),
    ]),
    ("designs/cx_plates.py", "jetplates.py", "the baked registry instead of the raw plates, a bounded cache", [
        cut("import os, json, math, glob", "FADE = 0.04", "import math\nimport threading\n\nimport numpy as np\n\nfrom .. import core as C\nfrom .. import plates as PL\n\n"),
        sub("MAX_UPSCALE = 1.1\n", "MAX_UPSCALE = 1.1\n\n_TL = threading.local()\n"),
        sub("        out.append(pl[order[j % len(order)]])\n    return out\n", "        out.append(pl[order[j % len(order)]])\n    drawn(out)\n    return out\n"),
        sub("_cache = {}\n", "_cache = C.BoundedCache(4)\n"),
        cut("def _lum(path, side=None):", "def qa(p):",
            'def registry(fam, pv=None):\n'
            '    """[Plate dicts] of the usable plates of a family (JET or RIVER) that a spec of plates version pv may pick, by id: the baked fit (what the\n'
            '    prototype fitted from the raw file once and cached in fits.json) and the key, which is the plate id."""\n'
            '    return [dict(PL.record(pid)["fit"], key=pid) for pid in sorted(PL.ids("P-CX-" + fam, pv))]\n\n\n'
            'def _plate_lum(p, need_side):\n'
            '    """Luminance (float32 0..1) of the plate at a side the placement needs, never enlarged more than MAX_UPSCALE from the file used: the bundled 1K\n'
            '    file when the placement needs at most 1.1 x 1024 px, the 4K file otherwise (the collision plates have none: a collision picture is drawn on\n'
            '    the canonical 1024 geometry, where no placement needs more, and PlateUnavailable says so if one ever did)."""\n'
            '    lod = "1k" if need_side <= 1024 * MAX_UPSCALE else "4k"\n'
            '    k = (p["key"], lod)\n'
            '    a = _cache.get(k)\n'
            '    if a is None:\n'
            '        im = PL.load_1k(p["key"]) if lod == "1k" else PL.fetch_4k(p["key"])\n'
            '        a = _cache.put(k, np.asarray(im.convert("L"), np.float32) / 255.0)\n'
            '    return a\n\n\n'),
        sub("def qa(p):", 'def trace(on=True):\n    """Start (on) or stop (off) collecting the ids of the plates picked on this thread; stopping returns them, in the order picked (the Preview\'s facts and the\n    admin\'s list of the plates a picture was drawn from). Records nothing else and changes no pixel."""\n    if on:\n        _TL.keys = []\n        return None\n    got = getattr(_TL, "keys", None)\n    _TL.keys = None\n    return got or []\n\n\ndef drawn(plates):\n    keys = getattr(_TL, "keys", None)\n    if keys is not None:\n        keys.extend(p["key"] for p in plates)\n\n\ndef qa(p):'),
    ]),
    ("designs/cx_kit.py", "kit.py", "imports, no calibration eye loader, no path atlas, bounded caches, no Windows meter", [
        sub("(scratch prototype)", "(ported from the scratch prototype)"),
        cut("import os, sys, ctypes, math, hashlib", "_PUP = {}",
            "import sys\n\nimport numpy as np\n\nfrom .. import atlas as AT\nfrom .. import core as C\nfrom .. import pupil as PUP\n\n\n"
            "def atlas():\n    \"\"\"The chip atlas (api/_lib/styles/atlas.py: read once per process, checked against the registry's sha256).\"\"\"\n    return AT.chips()\n\n\n"),
        sub("_PUP = {}\n", "_PUP = C.BoundedCache(64)\n"),
        sub("    if ir.digest not in _PUP:\n        fr = ir.graded(C.REF_SIDE)\n        sq, t = C._tight(fr)\n        _PUP[ir.digest] = PUP.analyse(sq)\n    return _PUP[ir.digest]\n",
            "    got = _PUP.get(ir.digest)\n    if got is None:\n        fr = ir.graded(C.REF_SIDE)\n        sq, t = C._tight(fr)\n        got = _PUP.put(ir.digest, PUP.analyse(sq))\n    return got\n"),
        cut("def peak_rss_mb():", "# ----------------------------------------------------------------------------- input gate",
            'def peak_rss_mb():\n'
            '    """The peak memory of the process in MB (the high-water mark of a warm instance), or None where the platform has no resource module. Only the\n'
            '    options that ask for a memory trace read it."""\n'
            '    try:\n'
            '        import resource\n'
            '        ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss\n'
            '        return round(ru / (1024.0 if sys.platform.startswith("linux") else 1048576.0))\n'
            '    except Exception:  # noqa: no meter on this platform\n'
            '        return None\n\n\n'),
        sub("_GATE = {}\n", "_GATE = C.BoundedCache(64)\n"),
        sub("    k = ir.digest\n    if k in _GATE:\n        return _GATE[k]\n", "    k = ir.digest\n    got = _GATE.get(k)\n    if got is not None:\n        return got\n"),
        sub("    _GATE[k] = out\n    return out\n", "    return _GATE.put(k, out)\n"),
    ]),
    ("designs/collision.py", "engine.py", "imports, a bounded cache, the style ids out of the text", [
        sub(" (scratch prototype, NOT repo code)", " (ported from the scratch prototype)"),
        sub(" (duo.collision_infinity)", ""),
        sub(" (duo.clean)", ""),
        sub(" (duo.kiss_collision)", ""),
        sub(" (grp.collision, N = 3)", " (N = 3)"),
        sub(" (grp.collision, N = 4-8)", " (N = 4-8)"),
        sub(" (grp.chain, N = 3-6)", " (N = 3-6)"),
        cut("import os, sys, math, time", "BG_DARK = ",
            "import math\nimport time\n\nimport numpy as np\nfrom PIL import Image, ImageDraw\n\nfrom .. import core as C\nfrom .. import palette as PAL\nfrom .. import pupil as PUPM\n"
            "from . import compositor as CC\nfrom . import extra as EX\nfrom . import fill as FL\nfrom . import haze as HZ\nfrom . import kit as K\nfrom . import lens_mode as LM\n"
            "from . import powder as PW\nfrom . import raster as RS\nfrom . import scenes as CL\nfrom . import seam_plan as SP\n\n"),
        sub("_LST = {}\n", "_LST = C.BoundedCache(32)\n"),
        sub("    k = iris.digest\n    if k not in _LST:\n", "    k = iris.digest\n    got = _LST.get(k)\n    if got is None:\n"),
        sub("        _LST[k] = (m, th, Ls)\n    return _LST[k]\n", "        got = _LST.put(k, (m, th, Ls))\n    return got\n"),
        sub('or sc.key.startswith("grp.chain") else', 'or str(sc.info.get("layout", "")).startswith("chain") else'),
        sub('info["not_offered"] = "bar pupil: use pet.clean (true ellipse), the collision family does not overlap horizontal bars"',
            'info["not_offered"] = "bar pupil: the collision family does not overlap horizontal bars"'),
    ]),
]

SOURCES = {          # sha256 of the DG1 snapshot (wave-dg1/final, line ends as LF) the goldens were recorded on
    "designs/collision.py": "63f5e236bf7e2234d0c88cc49916e8972be16265cfa0e85054a159d6302f15f4",
    "designs/cx_extra.py": "0d7ece0267e67de5adb65b01a30c0e334b7f6d9ac558be646632e3b48628648d",
    "designs/cx_fill.py": "a7bdbda034d74c57bc37b7dc33148454f9baa9064f0f3b23b5cf5587e0fad0d6",
    "designs/cx_haze.py": "11231c602d8f42f20e7ca1d30a804368f1ae8fb541bc669858efbbc44bc0de72",
    "designs/cx_kit.py": "d01ea17ea33f94e8d5b51508b42eb6af136d39d73b4aef475ff2b7d475622dd2",
    "designs/cx_plates.py": "e9c9a1e24b0af10f16dbe079cb70ad86f5473bdb243d15e30d1251db1f730651",
    "designs/cx_powder.py": "953fb1d0184b97844753891290d1daf2fb39a7da4ce7e409807eaf6bfb920b72",
    "designs/cx_raster.py": "861e19a903f86bf1b6c5821edffe7858a62827b5aeac124700fcac2e7bb53e32",
    "fx/collision_comp.py": "b36b8437da86419466d008923a314d6865df52c3b04c743dbc71a0168f0be47a",
    "fx/collision_layouts.py": "9e706c08af164bc000223d1581c78880ff7b9f2b5a248849f91e408eef1f4cd3",
    "fx/lens_mode.py": "ba1a17d205e7928ba4413b9cbd00b33653386635965ae8b889220b32d8f7c987",
    "fx/seam_plan.py": "34c3bf65104bd768ddb27242081fab8819f826f22b39be504be896778040818f",
}


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
    note = (f"# PORT of work package WP7A (step A): {src} of the DG1 snapshot of the scratch prototype, verbatim but for the edits\n"
            f"# scripts/styles_tests/port_collision.py lists ({words}); test_goldens_collision.py replays the edits on the scratch and the pixels of the\n"
            "# scratch's own pictures.")
    return "\n".join(lines[:end] + ["from __future__ import annotations", ""] + note.split("\n") + [""] + lines[end:])


def build(dg1):
    """{destination relative to api/_lib/styles/collision: the text of the ported file}, and {source: sha256 of the scratch file}."""
    out, shas = {}, {}
    for src, dst, words, edits in PORTS:
        path = os.path.normpath(os.path.join(dg1, src))
        with open(path, "rb") as f:
            raw = f.read()
        shas[src] = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
        text = raw.decode("utf-8").replace("\r\n", "\n")
        out[dst] = _with_future(_apply(text, edits, src), words, os.path.basename(src))
    return out, shas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sources", action="store_true", help="print the sha256 of every source file")
    a = ap.parse_args()
    dg1 = os.environ.get("SNAPEYES_SCRATCH_DG1") or sys.exit("SNAPEYES_SCRATCH_DG1 is not set (the wave-dg1/final folder of the scratch tree)")
    made, shas = build(dg1)
    if a.sources:
        for k, v in sorted(shas.items()):
            print(f'    "{k}": "{v}",')
        return
    bad = 0
    for dst, text in sorted(made.items()):
        path = os.path.join(DEST, *dst.split("/"))
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
    if a.check:
        want = {k: v for k, v in SOURCES.items()}
        if want and want != shas:
            bad += 1
            print("DIFFERS  the sha256 of the source files (the snapshot the goldens were recorded on)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
