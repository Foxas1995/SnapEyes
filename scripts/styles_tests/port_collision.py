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

Two sets of edits, applied in this order: PORTS (step A, WP7A: the port) and STEP_B (WP7B: the seed from the eyes' ids, the pixel decisions made once and
taken from the plan, the plates version, the fill source; below). With the STEP_B edits taken out the files are the step A port; with opts seed_mode
"legacy" the step B files draw the step A pictures byte for byte.
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

# WP7B, step B (decision C9, the plan freeze of C8): the seed is made from the eyes' ids and the plan's seed key (api/_lib/styles/seeds.py) and NOT from the
# bytes of the irises, the scene key and the customer's names; the discrete choices that depend on the pixels (the overlap fallback, the woven or stacked
# lens, the front order of the contacts, the hairline edges) are decided once on a copy of the canonical scene and can be taken from the plan instead
# (frozen); a plan-only run stops after them; the plates version of the spec reaches every plate pick; the universe fill reads a source of at most 1536 px.
# Nothing else. Keyed by the destination file. The legacy seed stays one option away (opts seed_mode "legacy"): that the replay of the step A recording
# with it is byte for byte equal is the proof that the seed and the decisions' place are the ONLY things step B moved.
STEP_B = {
    "engine.py": [
        sub("import math\nimport time\n\nimport numpy as np\n", "import copy\nimport math\nimport time\n\nimport numpy as np\n"),
        sub("from .. import pupil as PUPM\nfrom . import compositor as CC\n", "from .. import pupil as PUPM\nfrom .. import seeds as SD\nfrom . import compositor as CC\n"),
        sub("def place_disc_exact(iris, cx, cy, tgt, index=0):\n",
            'class DesignChanged(ValueError):\n'
            '    """The plan froze a choice that the eyes of this render contradict (the plan says Collision Infinity and the pupils now say the Kiss geometry, a front\n'
            '    order that does not fit the scene): never another picture than the approved one, so the caller holds the order. `why` names it."""\n\n'
            '    def __init__(self, msg, why="design_changed"):\n'
            '        super().__init__(msg)\n'
            '        self.why = why\n\n\n'
            'def place_disc_exact(iris, cx, cy, tgt, index=0):\n'),
        # the decisions that depend on pixels, factored out of render() (the same code, on a copy of the canonical scene, or the plan's choices)
        sub("# ----------------------------------------------------------------------------- main\ndef render(design, irises, fmt=None, size=1024, names=None, date=None, bg=\"dark\", clean=False, opts=None, layout=None):\n"
            "    \"\"\"One artwork. See the module docstring. Returns a Result.\"\"\"\n    o = dict(opts or {})\n",
            '# ----------------------------------------------------------------------------- decisions\n'
            'def decisions(sc_can, irises, design, design0, info, o, frozen):\n'
            '    """The discrete choices of one artwork that depend on the PIXELS of its irises, decided ONCE on a copy of the canonical (1024 px) scene, so that they are\n'
            '    the same at every size, or taken from the plan (frozen) when the plan fixed them before the render: which iris is in front at each contact the scene\n'
            '    leaves undecided (the brighter seam side; the stacking solver for the groups), whether a contact is drawn as a hairline (its back band is dark) and,\n'
            '    decided earlier in render() from the same irises, the overlap fallback of Collision Infinity and its woven or stacked lens. The master of an order is\n'
            '    made from ANOTHER image of the same eyes than its preview (a 4096 px render registered to the 1024 px restoration), whose band luminance can differ by\n'
            '    a fraction of a unit: a tie (a difference under 3) could go the other way, so the plan stores what the preview decided and the master obeys it.\n'
            '    design is the design drawn (a fallen back infinity is a kiss), design0 the one asked for. Returns {fronts: {rule index: mode}, pend: a scene rule was left\n'
            '    to decide (the merge order is built again), lens_stack, hairline: [rule index], info: facts to report, frozen: the plan\'s record of all of it}.\n'
            '    DesignChanged when a frozen choice does not fit this scene."""\n'
            '    s = copy.deepcopy(sc_can)\n'
            '    pend = [i for i, r in enumerate(s.rules) if r.mode == "stack"]\n'
            '    lens_stack = info.get("lens_mode_used") == "stack" and design == "infinity" and len(s.rules) == 1\n'
            '    facts, fronts = {}, {}\n'
            '    if "fronts" in frozen:\n'
            '        fz = frozen["fronts"]\n'
            '        ok = (isinstance(fz, dict) and all(isinstance(k, (str, int)) and str(k).isdigit() for k in fz) and all(v in ("front_a", "front_b") for v in fz.values())\n'
            '              and sorted(int(k) for k in fz) == sorted(pend + ([0] if lens_stack else [])))\n'
            '        if not ok:\n'
            '            raise DesignChanged("the plan\'s front order %r does not fit this scene (contacts left to decide: %r)" % (fz, pend))\n'
            '        fronts = {int(k): v for k, v in fz.items()}\n'
            '        for i, m in fronts.items():\n'
            '            s.rules[i].mode = m\n'
            '    else:\n'
            '        if pend:\n'
            '            if design == "kiss":\n'
            '                r = s.rules[0]\n'
            '                pa = math.atan2(r.uy, r.ux)\n'
            '                la, lb = band_lstar(irises[0], pa), band_lstar(irises[1], pa + math.pi)\n'
            '                r.mode = "front_b" if lb - la > 3.0 else "front_a"             # ties (and A brighter): A, the lower-left eye, in front\n'
            '                facts["front"] = r.mode\n'
            '            else:\n'
            '                cache = {}\n\n'
            '                def lstar(k, phi):\n'
            '                    key = (k, round(phi, 3))\n'
            '                    if key not in cache:\n'
            '                        cache[key] = band_lstar(irises[k], phi)\n'
            '                    return cache[key]\n'
            '                facts["stack"] = decide_fronts(s, lstar)\n'
            '            fronts = {i: s.rules[i].mode for i in pend}\n'
            '        if lens_stack:\n'
            '            # DG1 rung 2: the stack lens: one iris in front over the whole lens (brief 1.3.2: the one whose seam-side band is brighter, ties A), no weave, no seam\n'
            '            r = s.rules[0]\n'
            '            pa = math.atan2(r.uy, r.ux)\n'
            '            la, lb = band_lstar(irises[0], pa), band_lstar(irises[1], pa + math.pi)\n'
            '            r.mode = "front_b" if lb - la > 3.0 else "front_a"\n'
            '            facts["front"] = r.mode\n'
            '            fronts[0] = r.mode\n'
            '    nr = len(s.rules)\n'
            '    if "hairline" in frozen:\n'
            '        hz = frozen["hairline"]\n'
            '        if not (isinstance(hz, list) and all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < nr for i in hz)):\n'
            '            raise DesignChanged("the plan\'s hairline contacts %r do not fit this scene (%d contacts)" % (hz, nr))\n'
            '        natural = sorted(set(hz))\n'
            '    else:\n'
            '        natural = []\n'
            '        for ri, r in enumerate(s.rules):\n'
            '            pa = math.atan2(r.uy, r.ux)\n'
            '            la = band_lstar(irises[r.a], pa)\n'
            '            lb = band_lstar(irises[r.b], pa + math.pi)\n'
            '            back_L = min(la, lb) if r.mode == "weave" else (lb if r.mode == "front_a" else la)\n'
            '            if back_L < DARK_EDGE_L:\n'
            '                natural.append(ri)\n'
            '    out = {"fronts": {str(i): m for i, m in sorted(fronts.items())}, "hairline": natural}\n'
            '    if design0 == "infinity":\n'
            '        out["fallback"] = "overlap_fallback" if info.get("overlap_fallback") else None\n'
            '        if not info.get("overlap_fallback"):\n'
            '            out["lens"] = info.get("lens_mode_used")\n'
            '    return {"fronts": fronts, "pend": bool(pend), "lens_stack": bool(lens_stack), "hairline": list(range(nr)) if o.get("hairline") else natural, "info": facts, "frozen": out}\n\n\n'
            '# ----------------------------------------------------------------------------- main\n'
            'def render(design, irises, fmt=None, size=1024, names=None, date=None, bg="dark", clean=False, opts=None, layout=None, key=None, frozen=None, plan_only=False):\n'
            '    """One artwork. See the module docstring. Returns a Result. WP7B (step B): key is the plan\'s seed key (seeds.py: the style, the layout, the options and the\n'
            '    plates version; the design drawn, the ground and the clean flag are filled in here), from which and from the eyes\' ids (irises[k].eye_id) the seed is\n'
            '    made; opts seed_mode "legacy" seeds as before step B (the bytes of the irises, the design, the scene key and the names). frozen is what the plan fixed\n'
            '    before the render (decisions() names its fields: fallback, lens, fronts, hairline): taken from it instead of decided from these irises. plan_only stops\n'
            '    after those decisions and the seed (res.frozen, res.seed, res.info) and draws nothing: the plan pass."""\n'
            '    o = dict(opts or {})\n'
            '    frozen = dict(frozen or {})\n'
            '    design0 = design\n'),
        # the overlap fallback and the lens mode: from the plan when it names them
        sub("            d_over_R, raw, over = CL.solve_infinity_d(ra, rb)\n            info.update(d_raw=raw, reach=(ra, rb), overlap_fallback=bool(over))\n",
            "            d_over_R, raw, over = CL.solve_infinity_d(ra, rb)\n"
            "            if \"fallback\" in frozen:\n"
            "                if frozen[\"fallback\"] == \"overlap_fallback\":\n"
            "                    over = True                      # the plan drew the Kiss geometry for these pupils: so does every render of the order\n"
            "                elif over:\n"
            "                    raise DesignChanged(\"the plan draws the infinity overlap, but the pupils of these eyes reach %.3f R (the limit is the Kiss fallback)\" % raw)\n"
            "            info.update(d_raw=raw, reach=(ra, rb), overlap_fallback=bool(over))\n"),
        sub("            elif o.get(\"lens_mode\", \"auto\") in (\"auto\", \"stack\", \"weave\"):\n", "            elif (frozen.get(\"lens\") or o.get(\"lens_mode\", \"auto\")) in (\"auto\", \"stack\", \"weave\"):\n"),
        sub("                lens_used = LM.decide(pl0.info, o.get(\"lens_mode\", \"auto\"))\n", "                lens_used = LM.decide(pl0.info, frozen.get(\"lens\") or o.get(\"lens_mode\", \"auto\"))\n"),
        # the fronts, the lens stack's front and the hairline edges: decisions(), applied to the scene of this size
        sub('    # -- fronts and order ----------------------------------------------------------------------\n'
            '    if any(r.mode == "stack" for r in sc.rules):\n'
            '        if design == "kiss":\n'
            '            r = sc.rules[0]\n'
            '            pa = math.atan2(r.uy, r.ux)\n'
            '            la, lb = band_lstar(irises[0], pa), band_lstar(irises[1], pa + math.pi)\n'
            '            r.mode = "front_b" if lb - la > 3.0 else "front_a"             # ties (and A brighter): A, the lower-left eye, in front\n'
            '            info["front"] = r.mode\n'
            '        else:\n'
            '            cache = {}\n\n'
            '            def lstar(k, phi):\n'
            '                key = (k, round(phi, 3))\n'
            '                if key not in cache:\n'
            '                    cache[key] = band_lstar(irises[k], phi)\n'
            '                return cache[key]\n'
            '            info["stack"] = decide_fronts(sc, lstar)\n'
            '        rebuild_order(sc)\n'
            '    if info.get("lens_mode_used") == "stack" and design == "infinity" and len(sc.rules) == 1:\n'
            '        # DG1 rung 2: the stack lens: one iris in front over the whole lens (brief 1.3.2: the one whose seam-side band is brighter, ties A), no weave, no seam\n'
            '        r = sc.rules[0]\n'
            '        pa = math.atan2(r.uy, r.ux)\n'
            '        la, lb = band_lstar(irises[0], pa), band_lstar(irises[1], pa + math.pi)\n'
            '        r.mode = "front_b" if lb - la > 3.0 else "front_a"\n'
            '        r.crumble = False\n'
            '        info["front"] = r.mode\n'
            '    info["rules"] = [(r.a, r.b, r.mode) for r in sc.rules]\n',
            '    # -- fronts and order (WP7B: decided once on the canonical scene, or the plan\'s) ------------------\n'
            '    dec = decisions(sc_can, irises, design, design0, info, o, frozen)\n'
            '    for ri, mode in dec["fronts"].items():\n'
            '        sc.rules[ri].mode = mode\n'
            '    if dec["lens_stack"]:\n'
            '        sc.rules[0].crumble = False\n'
            '    if dec["pend"]:\n'
            '        rebuild_order(sc)\n'
            '    info.update(dec["info"])\n'
            '    info["rules"] = [(r.a, r.b, r.mode) for r in sc.rules]\n'),
        sub('    seed = C.design_seed(irises, STYLE + "." + design + "." + bg + (".clean" if clean else ""), sc.key + "/" + ",".join(names or []))\n    res.seed = seed\n',
            '    if o.get("seed_mode") == "legacy":\n'
            '        seed = C.design_seed(irises, STYLE + "." + design + "." + bg + (".clean" if clean else ""), sc.key + "/" + ",".join(names or []))\n'
            '    else:\n'
            '        if not isinstance(key, dict):\n'
            '            raise ValueError("a render needs the plan\'s seed key (seeds.py) or opts seed_mode legacy")\n'
            '        # names, date, canvas, size and pixels are NOT in the seed: a typo in a name must never reshuffle the powder, a preview and a master draw the same\n'
            '        seed = SD.seed_for_key([ir.eye_id for ir in irises], dict(key, design_used=info["design_used"], bg=bg, clean=bool(clean)))\n'
            '    res.seed = seed\n'
            '    res.frozen = dec["frozen"]\n'
            '    info["frozen"] = dec["frozen"]\n'
            '    if plan_only:\n'
            '        info["d_over_R"] = [round(r.d / sc.R[r.a], 4) for r in sc.rules]\n'
            '        res.img = res.img8 = res.comp = None\n'
            '        res.info, res.scene, res.discs, res.irises, res.opts = info, sc, discs, irises, o\n'
            '        return res\n'),
        sub('    edge_modes, hair_cols = {}, {}\n'
            '    for ri, r in enumerate(sc.rules):\n'
            '        pa = math.atan2(r.uy, r.ux)\n'
            '        la = band_lstar(irises[r.a], pa)\n'
            '        lb = band_lstar(irises[r.b], pa + math.pi)\n'
            '        back_L = min(la, lb) if r.mode == "weave" else (lb if r.mode == "front_a" else la)\n'
            '        if back_L < DARK_EDGE_L or o.get("hairline"):\n'
            '            edge_modes[ri] = "hairline"\n'
            '    for k in range(n):\n',
            '    edge_modes, hair_cols = {ri: "hairline" for ri in dec["hairline"]}, {}\n'
            '    for k in range(n):\n'),
        sub('        prm.update(o.get("prm", {}))\n', '        prm.update(o.get("prm", {}))\n        prm["pv"] = (key or {}).get("pv")                        # the plates version of the spec reaches the haze\'s plate pick\n'),
    ],
    "haze.py": [
        # the prototype caught every exception of the first pick: for the trio, the families and the chain, whose cloud_black is a NUMBER (a black point, not a list
        # of plate classes), list(0.03) raised a TypeError that the catch swallowed, so their haze has always been drawn from the wider pick without the colour filter.
        # That is the picture the owner approved, so it is written out here; a plate that is missing altogether (NoPlate twice) is no longer a picture without the haze
        sub('        try:\n            pk = R.pick("P-SN-CLOUD", seed, want, exclude=tuple(used), max_rotation=45.0, black=list(prm.get("cloud_black", ("45", "60"))))\n'
            '        except Exception:\n            try:\n                pk = R.pick("P-SN-CLOUD", seed, want, exclude=tuple(used), max_rotation=90.0)\n            except Exception:\n                continue\n',
            '        classes = prm.get("cloud_black", ("45", "60"))\n'
            '        try:\n'
            '            if not isinstance(classes, (tuple, list)):\n'
            '                raise R.NoPlate("no plate classes to filter by")\n'
            '            pk = R.pick("P-SN-CLOUD", seed, want, exclude=tuple(used), max_rotation=45.0, black=list(classes), pv=prm.get("pv"))\n'
            '        except R.NoPlate:\n'
            '            pk = R.pick("P-SN-CLOUD", seed, want, exclude=tuple(used), max_rotation=90.0, pv=prm.get("pv"))\n'),
    ],
    "jetplates.py": [
        sub("import math\nimport threading\n", "import contextlib\nimport math\nimport threading\n"),
        sub('    prototype fitted from the raw file once and cached in fits.json) and the key, which is the plate id."""\n    return [dict(PL.record(pid)["fit"], key=pid) for pid in sorted(PL.ids("P-CX-" + fam, pv))]\n',
            '    prototype fitted from the raw file once and cached in fits.json) and the key, which is the plate id. pv None: the plates version of plates_version() (the spec\'s,\n'
            '    set by the family\'s render for this thread), else the current one."""\n'
            '    pv = getattr(_TL, "pv", None) if pv is None else pv\n'
            '    return [dict(PL.record(pid)["fit"], key=pid) for pid in sorted(PL.ids("P-CX-" + fam, pv))]\n\n\n'
            '@contextlib.contextmanager\n'
            'def plates_version(pv):\n'
            '    """The plates version of the spec for the picks of this thread inside the block (a plate that arrived later is not a candidate: the plate registry is append-only)."""\n'
            '    old = getattr(_TL, "pv", None)\n'
            '    _TL.pv = pv\n'
            '    try:\n'
            '        yield\n'
            '    finally:\n'
            '        _TL.pv = old\n'),
    ],
    "fill.py": [
        sub("BAND_ROWS = 256\n", "BAND_ROWS = 256\nFILL_SIDE = 1536                # the soft base is computed on a 576 px grid: a source above this adds memory and no picture (WP7B; the prototype held every source whole)\nFILL_FLOAT_MB = 700.0           # the float32 copies of all the sources together may not pass this (the prototype held 1.73 GB for eight 4096 px eyes)\n"),
        sub("    srcs = [np.asarray(ir.src, np.float32) / 255.0 for ir in irises]\n",
            "    side = int(prm.get(\"fill_side\", FILL_SIDE))\n"
            "    srcs = [_fill_source(ir.src, side) for ir in irises]\n"
            "    mb = sum(s.nbytes for s in srcs) / 1048576.0\n"
            "    if mb > FILL_FLOAT_MB:\n"
            "        raise ValueError(f\"a universe fill of {n} eyes would hold {mb:.0f} MB of float copies (the limit is {FILL_FLOAT_MB:.0f} MB)\")\n"),
        sub("def _tri(rho):\n",
            "def _fill_source(im, side):\n"
            "    \"\"\"The restored iris (a square PIL image) as float32 0..1 for the soft base, shrunk to at most `side` px first (WP7B).\"\"\"\n"
            "    if im.size[0] > side:\n"
            "        from PIL import Image\n"
            "        im = im.resize((side, side), Image.LANCZOS)\n"
            "    return np.asarray(im, np.float32) / 255.0\n\n\n"
            "def _tri(rho):\n"),
    ],
}


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


def _with_future(text, words, src, step_b=False):
    """After the module docstring: the future import and a note of what the file is."""
    tree = ast.parse(text)
    end = tree.body[0].end_lineno
    lines = text.split("\n")
    note = (f"# PORT of work package WP7A (step A): {src} of the DG1 snapshot of the scratch prototype, verbatim but for the edits\n"
            f"# scripts/styles_tests/port_collision.py lists ({words}); test_goldens_collision.py replays the edits on the scratch and the pixels of the\n"
            "# scratch's own pictures."
            + ("\n# WP7B (step B) moved the seed and the place of the pixel decisions and nothing else (STEP_B of the same tool): see api/_lib/styles/seeds.py." if step_b else ""))
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
        text = _apply(_apply(text, edits, src), STEP_B.get(dst, []), src + " (step B)")
        out[dst] = _with_future(text, words, os.path.basename(src), bool(STEP_B.get(dst)))
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
