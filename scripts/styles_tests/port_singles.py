# -*- coding: utf-8 -*-
"""Makes the ported files of the singles family from the SCRATCH prototype by a listed set of edits, and nothing else (work package WP5A,
step A: "move first, merge later"). The committed files api/_lib/styles/singles/*.py and api/_lib/styles/matter.py ARE the output of this tool:

    set SNAPEYES_SCRATCH_Y3=<the wave-y3 folder of the scratch tree>
    python scripts/styles_tests/port_singles.py            # writes the files
    python scripts/styles_tests/port_singles.py --check    # compares them with what the edits make of the scratch (exit 1 on a difference)

test_goldens_singles.py runs the check when the scratch tree is there (a LOCAL line), so "the port is the scratch with these edits" is a
proven sentence and not a claim, next to the pixel goldens that prove the same from the other side. Every edit is a substring replacement that must
match exactly the number of times it says, or a cut of whole lines between two markers; a scratch file that moved makes the tool stop.

Two sets of edits, applied in this order: PORTS (step A, WP5A: the port) and STEP_B (WP5B: the seed, below; the one reviewed change of what a
picture is made from). With the STEP_B edits taken out the files are the step A port and replay the prototype's pictures byte for byte.

What the step A edits are, in four kinds (each file's header comment repeats the kinds that touch it):
  imports     the scratch paths and sys.path lines go; the engine core, layouts, text, plates and atlases are the repo modules; the thread-count
              environment lines at import go (run time rule of the plan: set them where the entry points are, not in a module)
  plates      `registry` (the plate workflow's module, which drags in the generation tooling) is api/_lib/styles/plates.py, which has the same surface;
              the two atlases are read through api/_lib/styles/atlas.py (checked against the registry's sha256), not from a scratch data folder
  caches      a module level dict keyed by the eye becomes a BoundedCache (a warm instance renders for hours)
  text        the three lines of customer text drawing live in api/_lib/styles/text.py (the verbatim drawer, with the font check and the line limit)
plus: the style ids of the registry are not written in a docstring (the style check refuses a literal id outside the registry), `from __future__ import annotations` after the docstring (Vercel's default Python is 3.12), and Celestial Gold is the owner-approved variant A
(wave-cg2/A/cg_a.py), not designs/singles_gold.py.
"""
from __future__ import annotations

import argparse
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("SNAPEYES_REPO") or os.path.dirname(os.path.dirname(HERE))      # the checkout (a suite runs from a prepared copy of this folder)
STYLES = os.path.join(ROOT, "api", "_lib", "styles")


def sub(old, new, count=1):
    return ("sub", old, new, count)


def cut(start, end, new=""):
    """Whole lines from the first line that starts with `start` up to (not including) the next line that starts with `end`."""
    return ("cut", start, end, new)


# (scratch file relative to wave-y3, destination relative to api/_lib/styles, header words, edits)
PORTS = [
    ("designs/singles_kit.py", "singles/kit.py", "imports, plates, caches, text; the legacy feather option is gone", [
        sub("(scratch prototype, NOT repo code)", "(ported from the scratch prototype)"),
        cut("import os", "L = C.L", "import math\nimport time\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .. import core as C\nfrom .. import layouts as LY\n"
            "from .. import plates as RG\nfrom ..text import draw_names, NAME_WARM, NAME_GOLD\n\n"),
        cut("SP = os.path.dirname(ROOT)", "F3_SPAN = "),
        cut("NAME_WARM = ", "WALL_NAME_Y = "),
        cut("def load_eye(name_or_path):", "# ----------------------------------------------------------------------------- geometry of a single",
            'def load_eye(eye):\n    """An Iris from an Iris or from the bytes of a restored iris square (a function reads what the request carried: a path is never opened)."""\n'
            '    if isinstance(eye, C.Iris):\n        return eye\n    if isinstance(eye, (bytes, bytearray)):\n        return C.Iris(bytes(eye))\n'
            '    raise TypeError("an eye is an Iris or the bytes of an image")\n\n\n'),
        sub("_H2 = {}\n", "_H2 = C.BoundedCache(64)\n"),
        sub("    key = iris.digest\n    if key in _H2:\n        return _H2[key]\n", "    key = iris.digest\n    got = _H2.get(key)\n    if got is not None:\n        return got\n"),
        sub("    _H2[key] = (rgb, how, h2)\n    return _H2[key]\n", "    return _H2.put(key, (rgb, how, h2))\n"),
        sub("    from PIL import ImageOps\n    if PLATE_TOOLS not in sys.path:\n        sys.path.insert(0, PLATE_TOOLS)\n    import registry as RG\n",
            "    from PIL import ImageOps\n"),
        cut("# ----------------------------------------------------------------------------- text", "# ----------------------------------------------------------------------------- memory discipline"),
        sub('    span = 0.0197 if (opts or {}).get("feather") == "legacy" else None          # D19: F3 (default) or the round 1 0.012 R feather\n',
            "    span = None                                                  # the F3 feather (the round 1 feather option is gone)\n"),
    ]),
    ("designs/singles_matter.py", "matter.py", "imports, the chips atlas read through atlas.py", [
        sub("(scratch prototype, NOT repo code)", "(ported from the scratch prototype)"),
        cut("import os, sys, math", "TWO_PI = ", "import math\n\nimport numpy as np\nfrom PIL import Image\n\nfrom . import atlas as AT\nfrom . import core as C\nfrom .singles import kit as K\n\n"),
        cut("_ATLAS = None", "# ----------------------------------------------------------------------------- emission (R units)",
            'def atlas():\n    """The chip atlas (api/_lib/styles/atlas.py: read once per process, checked against the registry\'s sha256)."""\n    return AT.chips()\n\n\n'
            'def _mip(side):\n    """The chip atlas reduced by a box filter to `side` x `side` (128, 64, 32, 16): (lum, mask) float32 (n, side, side). Built once."""\n'
            '    return AT.chips().mip(side)\n\n\n'),
    ]),
    ("designs/singles_powder.py", "singles/powder.py", "imports, plates", [
        sub(" (solo.powder)", ""),
        cut("import os, sys, math", "TWO_PI = ", "import math\nimport hashlib\n\nimport numpy as np\n\nfrom .. import core as C\nfrom .. import matter as M\nfrom .. import plates as RG\nfrom . import kit as K\n\n"),
        sub("_REG = None\n", ""),
        cut("def registry():", "def _angdiff(a, b):", "def registry():\n    return RG\n\n\n"),
        sub("import hashlib\n\n\ndef _hash(", "def _hash("),
    ]),
    ("designs/singles_splash.py", "singles/splash.py", "imports, plates, the drops atlas read through atlas.py", [
        sub(" (solo.splash)", ""),
        cut("import os, sys, math, hashlib", "TWO_PI = ", "import math\nimport hashlib\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .. import atlas as AT\nfrom .. import core as C\nfrom .. import plates as RG\nfrom . import kit as K\n\n"),
        sub("_REG = None\nSP = {", "SP = {"),
        cut("def registry():", "def _hash(seed, *parts):", "def registry():\n    return RG\n\n\n"),
        sub("_DROPS = None\n\n\ndef droplet_images", "def droplet_images"),
        sub('    global _DROPS\n    if _DROPS is None:\n        z = np.load(os.path.join(HERE, "data", "drops_atlas.npz"))\n        _DROPS = z["rgb"]\n    N = len(_DROPS)\n',
            "    drops = AT.drops()\n    N = len(drops)\n"),
        sub("        a = _DROPS[i].astype(np.float32) / 255.0\n", "        a = drops[i].astype(np.float32) / 255.0\n"),
    ]),
    ("designs/singles_elements.py", "singles/elements.py", "imports, plates", [
        sub(" (solo.elements)", ""),
        cut("import os, sys, math", "TWO_PI = ", "import math\n\nimport numpy as np\nfrom PIL import ImageFilter\n\nfrom .. import core as C\nfrom .. import matter as M\nfrom . import kit as K\nfrom . import splash as SS\n\n"),
    ]),
    ("designs/singles_radiance.py", "singles/radiance.py", "imports, a bounded cache", [
        sub(" (solo.radiance)", ""),
        cut("import os", "TWO_PI = ", "import math\n\nimport numpy as np\nfrom PIL import Image\n\nfrom .. import core as C\n\n"),
        sub("_INFO = {}\n", "_INFO = C.BoundedCache(64)\n"),
        sub("    key = iris.digest\n    if key in _INFO:\n        return _INFO[key]\n", "    key = iris.digest\n    got = _INFO.get(key)\n    if got is not None:\n        return got\n"),
        sub("    _INFO[key] = info\n    return info\n", "    return _INFO.put(key, info)\n"),
        sub("    from designs import singles_kit as _K\n", "    from . import kit as _K\n"),
    ]),
]
# Celestial Gold is the file of the approved variant A, not designs/singles_gold.py
GOLD = ("../wave-cg2/A/cg_a.py", "singles/gold.py", "imports; the approved variant A (wave-cg2/A/cg_a.py), its effect is named fx_gold", [
    sub("(wave-cg2, builder A, scratch prototype, NOT repo code)", "(ported from the scratch prototype of the design round wave-cg2)"),
    cut("import os, sys, math", "TWO_PI = ", "import math\n\nimport numpy as np\n\nfrom .. import core as C\nfrom .. import matter as M\nfrom . import kit as K\n\n"),
    sub("def fx_gold_a(cv, ctx):", "def fx_gold(cv, ctx):"),
])


# WP5B, step B: the seed is made from the eye ids and the plan's seed key (api/_lib/styles/seeds.py), not from the bytes of the iris; the plates version
# of the spec reaches every plate pick; the liquid of a splash can be fixed by the plan. Nothing else. Keyed by the destination file.
STEP_B = {
    "singles/kit.py": [
        sub('''    cx, cy, R), irises, seed, opts, rand(tag, eye), grid(), count(). The effect draws into the float canvas only."""

    def __init__(self, frame, d, iris, style, opts=None):
''', '''    cx, cy, R), irises, seed, pv, frozen, opts, rand(tag, eye), grid(), count(). The effect draws into the float canvas only.
    seed: the seed of the artwork (api/_lib/styles/seeds.py: the eye ids and the plan's seed key, WP5B); pv: the plates version a plate pick takes;
    frozen: the choices the plan fixed before the render (the liquid of a splash), which an effect reads before it measures the eye."""

    def __init__(self, frame, d, iris, style, opts=None, seed=None, pv=None, frozen=None):
'''),
        sub("        self.seed = C.seed_for(iris.raw, 0, style, frame.key)\n",
            '        if seed is None:\n            raise ValueError("an effect context needs the seed of its artwork (api/_lib/styles/seeds.py)")\n'
            "        self.seed = int(seed)\n        self.pv = pv\n        self.frozen = dict(frozen or {})\n"),
        sub("                  whiten=C.WHITEN, opts=None, times=None, limb=None):\n", "                  whiten=C.WHITEN, opts=None, times=None, limb=None, seed=None, pv=None, frozen=None):\n"),
        sub("    ctx = MCtx(frame, d, iris, design, opts)\n", "    ctx = MCtx(frame, d, iris, design, opts, seed=seed, pv=pv, frozen=frozen)\n"),
    ],
    "singles/powder.py": [
        sub('def pick_cloud(seed, allowed, maxrot=10.0, black=("30", "45", "60")):', 'def pick_cloud(seed, allowed, maxrot=10.0, black=("30", "45", "60"), pv=None):'),
        sub('''    bands (deg CCW from 3 o'clock). Only plates that can be placed at R = 0.24 S without an upscale beyond x1.1 at 4096 (void >= 0.437)."""
''', '''    bands (deg CCW from 3 o'clock). Only plates that can be placed at R = 0.24 S without an upscale beyond x1.1 at 4096 (void >= 0.437).
    pv: the plates version of the spec (a plate that arrived later is not a candidate; None is the current version)."""
'''),
        sub('    for p in R.plates("P-SN-CLOUD", black=list(black)):', '    for p in R.plates("P-SN-CLOUD", pv, black=list(black)):'),
        sub("    pk = pick_cloud(ctx.seed, allowed)\n", "    pk = pick_cloud(ctx.seed, allowed, pv=ctx.pv)\n"),
    ],
    "singles/splash.py": [
        sub('''def liquid_for(iris):
    """The liquid family of one eye by class and hue (brief 3.7.1)."""
    st = iris.stats
    if st["class"] == "dark_brown":''', '''def liquid_for(iris):
    """The liquid family of one eye by class and hue (brief 3.7.1)."""
    return liquid_from_stats(iris.stats)


def liquid_from_stats(st):
    """liquid_for() of the numbers alone: st is the eye's colour_stats (class, h, C), measured on the iris or read from its sealed profile (the plan
    fixes the liquid from the profile, so that the preview and the master draw the plate the plan names)."""
    if st["class"] == "dark_brown":'''),
        sub('''    liquid = ctx.opts.get("liquid") or liquid_for(iris)
    rnd = ctx.rand("splash")
    wanted = opts["wind_lo"] + (opts["wind_hi"] - opts["wind_lo"]) * float(rnd.uniform())
    pk = reg.pick("P-SP-CROWN", ctx.seed, wanted_strong_angle=wanted, max_rotation=30.0, liquid=liquid)
''', '''    liquid = ctx.opts.get("liquid") or ctx.frozen.get("liquid") or liquid_for(iris)
    wanted, pk = crown_pick(ctx.seed, liquid, ctx.pv, opts)
'''),
        sub('''def fx_splash(cv, ctx):''', '''def crown_pick(seed, liquid, pv=None, opts=None):
    """(the screen angle the crown's tall side is wanted at, the Pick): the crown plate of one splash, from the artwork's seed, the liquid and the
    plates version of the spec. No pixels: resolve() calls it to name the plate before the render, and the render calls it to draw."""
    o = dict(SP)
    o.update(opts or {})
    wanted = o["wind_lo"] + (o["wind_hi"] - o["wind_lo"]) * float(C.Rand(seed, "splash").uniform())
    return wanted, registry().pick("P-SP-CROWN", seed, wanted_strong_angle=wanted, max_rotation=30.0, liquid=liquid, pv=pv)


def fx_splash(cv, ctx):'''),
    ],
    "singles/elements.py": [
        sub("max_rotation=25.0, exclude=v3_exclude(reg))", "max_rotation=25.0, exclude=v3_exclude(reg), pv=ctx.pv)"),
        sub("max_rotation=35.0, liquid=liquid)", "max_rotation=35.0, liquid=liquid, pv=ctx.pv)"),
    ],
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


def _with_future(text, words, src, step_b=False):
    """After the module docstring: the future import and a note of what the file is."""
    tree = ast.parse(text)
    end = tree.body[0].end_lineno
    lines = text.split("\n")
    note = (f"# PORT of work package WP5A (step A): {src} of the scratch prototype, verbatim but for the edits scripts/styles_tests/port_singles.py lists\n"
            f"# ({words}); test_goldens_singles.py replays the edits on the scratch and the pixels of the scratch's own pictures."
            + ("\n# WP5B (step B) changed the seed and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py." if step_b else ""))
    return "\n".join(lines[:end] + ["from __future__ import annotations", ""] + note.split("\n") + [""] + lines[end:])


def build(y3):
    """{destination relative to api/_lib/styles: the text of the ported file}."""
    out = {}
    for src, dst, words, edits in PORTS + [GOLD]:
        path = os.path.normpath(os.path.join(y3, src if not src.startswith("..") else src))
        if src.startswith("../"):
            path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(y3)), src[3:]))
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read().replace("\r\n", "\n")
        text = _apply(_apply(text, edits, src), STEP_B.get(dst, []), src + " (step B)")
        out[dst] = _with_future(text, words, os.path.basename(src), bool(STEP_B.get(dst)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or sys.exit("SNAPEYES_SCRATCH_Y3 is not set (the wave-y3 folder of the scratch tree)")
    made = build(y3)
    bad = 0
    for dst, text in sorted(made.items()):
        path = os.path.join(STYLES, *dst.split("/"))
        if a.check:
            with open(path, encoding="utf-8", newline="") as f:
                have = f.read().replace("\r\n", "\n")
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
