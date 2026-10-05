# -*- coding: utf-8 -*-
"""WP7A of the v3 engine work: the collision family (Kiss Collision, Clean Infinity, Collision Infinity, Family Colours with the trio, Infinity Chain)
ported verbatim into api/_lib/styles/collision (step A), with the design gate DG1's smooth planned seam. Test I6 (goldens) for the family, the collision
share of I7 (T1, T2, T3, T4, T6, T7, T10, T12, T13, T18, T19 of the brief) and the places the family is reached from: the style package's contract and
the master plan.

  1. the family in the repository: its files, the rules of every module, the registry and the family agree, no stage was raised
  2. the golden replay: the SHA-256 of the pictures the scratch prototype (the DG1 snapshot) made, for every pair design on three pairs, the canvases, the
     sizes 512, 1024 and 4096, the words, the stack lens, the laboratory switches, the trio, every layout of the family for four to eight eyes and the
     chain (data/collision_goldens.json): the port draws them byte for byte, with the same fronts, edge modes, fallbacks and plates; the replay can fail
  3. the hard rules on every picture of the replay: the iris is the graded iris byte for byte outside the seam band and the contact strips (T1, T6), the
     pupil is untouched (T2), the visible share keeps its floor (T3), the words are the customer's (T7), no hearts (T12), the iris size floor and the
     stacking rule (T18, T19)
  4. the seam of DG1: smooth by construction, the owner's budget E1 (the mixed share at most about 3 percent, the seam band at most 4 percent of an
     iris), the plan is the same at every size, the stack lens is automatic above K 62 and forced it passes T1, T2, T3, a bar pupil is refused
  5. the tests of the brief (T4, T6 flood, T7, T10, T12, T13, T18, T19) on the port
  6. determinism, bounded caches, the guards of render(), the plates (the JET and RIVER plates the prototype fitted are the baked ones, none needs a 4K file)
  7. the contract (resolve, preview, tiles, the watermark) and the master plan end to end
  8. the real calibration eyes (LOCAL: SNAPEYES_CALIB) and the port as the scratch plus its edits (LOCAL: SNAPEYES_SCRATCH_DG1)
No network, no image model, no real eye in the repository (the eyes are procedural: synth_iris). A golden is exact for this machine class and the pins of
requirements.txt; a mismatch elsewhere means recording again on the scratch code there, never changing the port.
    SNAPEYES_SCRATCH_DG1  the wave-dg1/final folder of the scratch tree (the edit check); SNAPEYES_CALIB the calibration restorations' folder
    python test_goldens_collision.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3coll."""
import ast
import gc
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest.mock as mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
FAMILY = os.path.join(API, "_lib", "styles", "collision")
STYLES = os.path.join(API, "_lib", "styles")
SCRATCH_DG1 = os.environ.get("SNAPEYES_SCRATCH_DG1") or ""
CALIB = os.environ.get("SNAPEYES_CALIB") or ""

RESULTS = []
LOCAL = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def local(name, ok, detail=""):
    """A check that needs the scratch tree or the real calibration eyes: reported, not counted among the PASS lines (a failure still fails the run)."""
    LOCAL.append(bool(ok))
    print(("LOCAL ok   " if ok else "FAIL LOCAL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_SCRATCH_Y3", "SNAPEYES_SCRATCH_DG1", "SNAPEYES_CALIB"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3coll_")
STORE = os.path.join(TMP, "store")
os.makedirs(STORE)
os.environ.update({"PYTHONIOENCODING": "utf-8", "SNAPEYES_TICKET_SECRET": "wp7a-ticket-secret-for-tests-0123456789abcdef",
                   "SNAPEYES_ADMIN_SECRET": "wp7a-admin-secret-for-tests-0123456789abcdef0123", "STORE_LOCAL_DIR": STORE,
                   "STYLE_PLATE_CACHE": os.path.join(TMP, "cache")})
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, API)
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import PIL  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
import collision_cases as CC  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import store  # noqa: E402
import _lib.styles as ST  # noqa: E402
from _lib.styles import core as C, selfcheck as SCK, plates as PL, text as TX, costs as CO, seeds as SD, eye as EYE, pupil as PUPM, steps as STP  # noqa: E402
from _lib.styles import collision as CX  # noqa: E402
from _lib.styles.collision import engine as E, scenes as CL, compositor as CMP, seam_plan as SP, lens_mode as LM, kit as K, jetplates as JP  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
GOLD = json.load(open(os.path.join(HERE, "data", "collision_goldens.json"), encoding="utf-8"))
G = GOLD["cases"]
MACHINE_SAME = GOLD["machine"]["numpy"] == np.__version__ and GOLD["machine"]["pillow"] == PIL.__version__
NOTE = "" if MACHINE_SAME else f" (numpy/Pillow differ from the recording {GOLD['machine']}: record again on the scratch code, do not change the port)"
FAMILY_FILES = sorted(f for f in os.listdir(FAMILY) if f.endswith(".py"))
COLLISION_STYLES = [i for i in CT.ids() if CT.ENGINE[i]["engine"] and CT.ENGINE[i]["engine"].get("module") == "collision"]


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def raises(fn, exc):
    try:
        fn()
    except exc as e:
        return e
    except Exception as e:  # noqa: BLE001
        return repr(e)
    return False


# ============================================================================================ 1. the family in the repository
section("1. the family in the repository")
check("the family has its modules (the prototype's collision.py is engine.py; the compositor, the scenes, the seam plan and the lens mode are its own; the powder, the "
      "raster, the extras, the fill, the haze, the kit and the JET and RIVER plates), and the style catalogue sees the family built",
      FAMILY_FILES == ["__init__.py", "compositor.py", "engine.py", "extra.py", "fill.py", "haze.py", "jetplates.py", "kit.py", "lens_mode.py", "powder.py", "raster.py",
                       "scenes.py", "seam_plan.py"]
      and CT.engine_built("collision") and ST.family("collision").__name__ == "_lib.styles.collision" and len(COLLISION_STYLES) == 5, (FAMILY_FILES, COLLISION_STYLES))
mods = [os.path.join(FAMILY, f) for f in FAMILY_FILES]
src_all = "".join(read(m) for m in mods)
check("every module of the family has the __future__ import (Python 3.12 is Vercel's default) and parses as 3.12",
      all(re.search(r"^from __future__ import annotations\r?$", read(m), re.M) and ast.parse(read(m), feature_version=(3, 12)) for m in mods), [os.path.basename(m) for m in mods])
check("no module holds a dash, a Windows or scratch path, a secret name, an environment line for threads, a sys.path line or a studio tagline",
      not re.search(DASH, src_all) and not re.search(r"C:\\|wave-g|wave-y2|wave-y3|wave-dg1|GEMINI_API_KEY|SERVICE_KEY|OMP_NUM_THREADS|sys\.path|THE UNIVERSE WITHIN|PRECISE IRIS", src_all),
      re.findall(r"C:\\|wave-g|wave-y2|wave-y3|wave-dg1|GEMINI_API_KEY|OMP_NUM_THREADS|sys\.path", src_all)[:5])
INVISIBLE = re.compile("[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u00ad\u061c\u180e\u200b-\u200f\u2028-\u202e\u2060-\u206f\ufeff\ufff9-\ufffb]")
check("no module holds a raw invisible, control or bidirectional character", not any(INVISIBLE.search(read(m)) for m in mods))


def empty_containers(path):
    """Names assigned at module level to an EMPTY dict, list or set: the signature of a cache that grows with the eyes seen."""
    out = []
    for node in ast.parse(read(path)).body:
        v = getattr(node, "value", None)
        empty = (isinstance(v, ast.Dict) and not v.keys) or (isinstance(v, (ast.List, ast.Set)) and not v.elts) or \
            (isinstance(v, ast.Call) and getattr(v.func, "id", "") in ("dict", "list", "set", "defaultdict", "OrderedDict") and not v.args)
        if empty:
            out += [t.id for t in (node.targets if isinstance(node, ast.Assign) else [node.target]) if isinstance(t, ast.Name)]
    return out


check("no module of the family keeps an empty module level dict, list or set (a cache): the caches that were keyed by the eye or the plate are BoundedCache (the scratch "
      "kept _PUP, _GATE, _LST, _cache, _DITHER_TILES and _RAG_THR as plain dicts)",
      not any(empty_containers(m) for m in mods), {os.path.basename(m): empty_containers(m) for m in mods if empty_containers(m)})
check("importing the family reads no file of its own, opens no socket and writes nothing: no open(), no os.environ, no subprocess, no np.load in any module of the family",
      not re.search(r"\bopen\(|os\.environ|subprocess|socket|np\.load|\.save\(", src_all), re.findall(r"\bopen\(|os\.environ|subprocess|socket|np\.load|\.save\(", src_all)[:5])
bad_layouts = []
for sid in COLLISION_STYLES:
    lo, hi = CT.eyes_range(sid)
    for n in range(lo, hi + 1):
        for lay in CT.layouts_for(sid, n):
            try:
                e, design, layout, fmt, clean = CX._setup({"style": sid, "eyes": n, "layout": lay})
                if design == "infinity" or design == "kiss":
                    sc = CL.pair_scene(fmt, 256, 1.3, False, False, "clean" if clean else design)
                elif design == "trio":
                    sc = CL.trio_scene(fmt, 256)
                elif design == "family":
                    sc = CL.family_scene(n, lay, fmt, 256)
                else:
                    sc = CL.chain_scene(n, fmt, 256)
                CL.check(sc)
                if sc.n != n or fmt not in e["canvases"]:
                    bad_layouts.append((sid, n, lay, fmt))
            except Exception as ex:  # noqa: BLE001
                bad_layouts.append((sid, n, lay, repr(ex)[:80]))
check("the registry and the family agree: every style, eye count and layout the registry lists for the five collision styles builds a scene on its default canvas with every iris "
      "inside it, and the default canvas is one the registry lists", not bad_layouts, bad_layouts[:5])
check("the registry's design names are the family's: infinity, kiss, trio, family, chain (Clean Infinity is the infinity design with the clean flag)",
      sorted({CT.engine_for(i, n)["design"] for i in COLLISION_STYLES for n in range(CT.eyes_range(i)[0], CT.eyes_range(i)[1] + 1)}) == sorted(CX.DESIGNS)
      and CT.engine_for("duo.clean", 2)["clean"] == 1 and CT.engine_for("duo.collision_infinity", 2)["clean"] == 0)
cost_rows = {}
for sid in COLLISION_STYLES:
    for n in range(CT.eyes_range(sid)[0], CT.eyes_range(sid)[1] + 1):
        eng = CT.engine_for(sid, n)
        cost_rows[(sid, n)] = CO.assess(CO.cost_key(eng, "dark", None), n, size=4096, side=CT.work_side(sid, n), factor=1.6)
check("every cost row the family needs exists (a master row and a preview row for each design and eye count), and every release 1 style fits one call at the slow factor 1.6: "
      "only Family Colours with seven eyes (outside release 1, 1447 MB against the 1434 MB budget) does not", all(r["need_s"] is not None for r in cost_rows.values())
      and [k for k, r in cost_rows.items() if not r["ok"]] == [("grp.collision", 7)], [(k, r["ok"], r["why"]) for k, r in cost_rows.items() if not r["ok"]])
check("no stage was raised: every collision style of the engine is still at the laboratory ceiling, so a customer can neither order nor preview one, and the admin can look at all five",
      all(CT.ceiling(i, n) == "lab" and not CT.orderable(i, n) and not CT.previewable(i, n) and CT.previewable(i, n, admin=True)
          for i in COLLISION_STYLES for n in range(CT.eyes_range(i)[0], CT.eyes_range(i)[1] + 1)), [(i, CT.ceiling(i, 2)) for i in COLLISION_STYLES])
check("the family is the only place that writes the scene keys: they are the registry's ids, part of the prototype's seed in step A, and scripts/check_styles.mjs allows exactly that file",
      "api/_lib/styles/collision/scenes.py" in read(os.path.join(REPO, "scripts", "check_styles.mjs")) and re.search(r"duo\.clean|grp\.chain", read(os.path.join(FAMILY, "scenes.py")))
      and not any(re.search(r"\b(solo|duo|grp)\.[a-z_]+", read(os.path.join(FAMILY, f))) for f in FAMILY_FILES if f not in ("scenes.py",)))

# ============================================================================================ 2. the golden replay
section("2. the golden replay: the scratch prototype's pictures (the DG1 snapshot) against this code")
FIX = {n: CC.fixture_bytes(n) for n in CC.fixture_names()}
check("the fixtures of the replay are the very bytes of the recording", all(hashlib.sha256(FIX[n]).hexdigest() == GOLD["fixtures"][n] for n in FIX),
      [n for n in FIX if hashlib.sha256(FIX[n]).hexdigest() != GOLD["fixtures"][n]])
print(f"   (recorded on {GOLD['machine']}; running on python {sys.version.split()[0]}, numpy {np.__version__}, Pillow {PIL.__version__})", flush=True)
check("the recording used the plates the owner's boards had: exactly the two retouched JET plates were taken from the baked library (their fits differ from the raw files'), "
      "every other plate from the prototype's own raw and 1K files", GOLD["retouched_plates"] == ["P-CX-JET__medium_left_b75__pro4K__t2", "P-CX-JET__wide_right_b75__pro4K__t1"], GOLD["retouched_plates"])

LAST = {}
SEEN = {"t": [], "plans": {}, "black": {}, "k": {}}
IRISES = {}


def port_render(design, eyes, fmt, size, names, date, bg, clean, opts, layout):
    r = CX.render(design, eyes, fmt, size, names, date, bg, clean, opts, layout)
    LAST["r"] = r
    return r


def replay(cases, with_checks=True):
    """The cases rendered on the port: [(case, record, differences)]. For every picture of 1024 px and less the hard rules of section 3 are measured on the way."""
    out = []
    for c in cases:
        rec = CC.render_case(port_render, C.Iris, FIX, c, IRISES)
        g = G[c["key"]]
        diff = [k for k in ("sha", "seed", "facts", "w", "h") if rec[k] != g[k]]
        out.append((c, rec, diff))
        r = LAST["r"]
        plans = list((r.cfg.plans or {}).values())
        if plans:
            SEEN["plans"][c["key"]] = (list(plans[0].a), [round(float(v), 6) for v in plans[0].hw_k], round(plans[0].info["K_chosen"], 3))
        if with_checks and c["size"] <= 1024:
            rep = CX.selfcheck(r, c["design"], [c["key"].split(".")[0], r.info.get("design_used", c["design"]), c["layout"] or "x"], c["names"], c["date"])
            SEEN["t"].append((c["key"], rep["ok"], {k: v["ok"] for k, v in rep["checks"].items()}, rep))
        if c["size"] >= 2048:
            IRISES.clear()
            gc.collect()
    return out


t0 = time.time()
ALL = CC.cases()
GROUPS = [
    ("infinity", "the three pairs at 1024 px on 3:2 (a blue and a dark brown, a blue and a green, a grey and an amber)", lambda c: c["design"] == "infinity" and not c["clean"] and c["size"] == 1024
        and c["fmt"] == "3:2" and not c["opts"] and not c["names"] and c["eyes"] in (list(CC.BB), list(CC.BG), list(CC.GA)), 3),
    ("clean infinity", "the three pairs at 1024 px", lambda c: c["design"] == "infinity" and c["clean"] and c["size"] == 1024 and c["fmt"] == "3:2" and not c["names"], 3),
    ("kiss", "the three pairs at 1024 px", lambda c: c["design"] == "kiss" and c["size"] == 1024 and c["fmt"] == "3:2" and not c["names"], 3),
]
for name, what, sel, n_want in GROUPS:
    rows = replay([c for c in ALL if sel(c)])
    bad = [(c["key"], d) for c, _, d in rows if d]
    check(f"{name}: {what} give the recorded pictures, seeds, fronts, edge modes and plates, byte for byte", len(rows) == n_want and not bad, str(bad) + NOTE)
rest = [c for c in ALL if not any(sel(c) for _, _, sel, _ in GROUPS) and c["size"] < 4096]
for design in CX.DESIGNS:
    rows = replay([c for c in rest if c["design"] == design])
    bad = [(c["key"], d) for c, _, d in rows if d]
    check(f"{design}: the other {len(rows)} cases (the other canvases, sizes, words, layouts and switches) equal the recorded pictures, byte for byte", rows and not bad, str(bad[:4]) + NOTE)
big = [c for c in ALL if c["size"] == 4096]
rows = replay(big)
bad = [(c["key"], d) for c, _, d in rows if d]
check(f"{len(big)} masters at 4096 px (a pair in the three builds, the trio, a family of four) equal the recorded pictures, byte for byte (the 4096 picture is the 1024 picture "
      "sample for sample)", len(rows) == len(big) and not bad, str(bad) + NOTE)
print(f"   (replayed in {time.time() - t0:.0f} s, {len(ALL)} cases)", flush=True)
check("the recording holds exactly the cases of the list and no other", sorted(G) == sorted(c["key"] for c in ALL), sorted(set(G) ^ {c["key"] for c in ALL})[:5])
with mock.patch.dict(CMP.PRESETS["ref"], {"a_in": 0.70}):
    moved = CC.render_case(port_render, C.Iris, FIX, [c for c in ALL if c["key"] == "infinity.blue+green.3:2.1024"][0], {})
check("the replay can fail: a change of the strength of the contact edge moves the hash of a pair", moved["sha"] != G["infinity.blue+green.3:2.1024"]["sha"])
check("the production switches of the family are what the recording passed: the contact edge of the owner's reference and the prototype's own defaults for everything else",
      CX.PRODUCTION == CC.PRODUCTION and CX.PRODUCTION["edge"] == "ref" and CX.PRODUCTION["zone_c"] is True and CX.PRODUCTION["seam"] == "plan" and CX.PRODUCTION["seam_dust"] is False,
      CX.PRODUCTION)

# ============================================================================================ 3. the hard rules
section("3. the hard rules on every picture of the replay (synthetic eyes)")
FLOWER6 = "family.blue+brown+green+grey+amber+blue2.1:1.512.flower"          # the known defect of the layouts (below)
CASE = {c["key"]: c for c in ALL}
DEFAULT_LAYOUT = {4: "zigzag", 5: "brick", 6: "brick", 7: "ring", 8: "ring"}      # what family_scene draws when the spec names no layout
T3_ONLY = [t for t in SEEN["t"] if not t[1] and "dust" not in t[0] and t[0] != FLOWER6 and {k for k, v in t[2].items() if not v} == {"t3"}]
KNOWN_T3 = [t for t in T3_ONLY if (CASE[t[0]]["design"] == "family" and CASE[t[0]]["layout"] != DEFAULT_LAYOUT[len(CASE[t[0]]["eyes"])])
            or (CASE[t[0]]["design"] == "chain" and all(s + 0.015 >= f for s, f in zip(t[3]["checks"]["t3"]["shares"], t[3]["checks"]["t3"]["floors"])))]
bad = [(t[0], {k: v for k, v in t[2].items() if not v}) for t in SEEN["t"] if not t[1] and "dust" not in t[0] and t[0] != FLOWER6 and t not in KNOWN_T3]
check(f"T1, T2, T3, T6, T7, T12, T18 and T19 on the {len(SEEN['t']) - 1 - len(KNOWN_T3)} pictures of 1024 px and less that are not one of the {len(KNOWN_T3) + 1} known misses below: the iris is "
      "the graded iris byte for byte outside the seam band and the contact strips, the pupil grown by 0.01 R is untouched, every iris keeps its visible share, nothing of the matter lies "
      "on an iris, the words are the customer's, no hearts, the iris size floor and the stacking rule hold", len(SEEN["t"]) >= 50 and not bad, bad[:4])
check("the known T3 misses (the visible share floor, found by this check on synthetic eyes and left as the prototype has it): only Family Colours in a layout that is not the default of its "
      "eye count (a brick of four eyes 0.76 and a flower of eight 0.77 against 0.82: the brief tested the defaults only) and the end irises of a chain by half a point or so (0.895 "
      "against 0.90 with the planned seam leaning toward the first eye); the pairs, the trio and the default layouts of the family all keep their floors, and the self check would hold such "
      "an order for review",
      KNOWN_T3 and len(T3_ONLY) == len(KNOWN_T3) and all(CASE[t[0]]["design"] in ("family", "chain") for t in KNOWN_T3)
      and all(t[3]["checks"]["t3"]["ok"] for t in SEEN["t"] if CASE[t[0]]["design"] in ("infinity", "kiss", "trio")),
      [(t[0], t[3]["checks"]["t3"]["shares"], t[3]["checks"]["t3"]["floors"]) for t in T3_ONLY if t not in KNOWN_T3])
print("   known T3 misses: " + "; ".join(f"{t[0]} {min(t[3]['checks']['t3']['shares']):.3f}" for t in KNOWN_T3), flush=True)
fl6 = [t for t in SEEN["t"] if t[0] == FLOWER6]
check("the one known defect of the layouts, found by this check and left as the prototype has it (step A is verbatim): Family Colours as a flower of SIX eyes puts the five petals 1.94 R apart, "
      "which is no contact (the rule is below 1.90 R) and still an overlap of 0.06 R, so the later petal's rim covers the earlier one's zone A over a few pixels (T1 and T6 fail on at most "
      "a hundred pixels at 0.94 to 0.95 R; every other check holds). The self check finds it, and a paid order of it would be held for review. WP7B (the layouts) or the families' design gate "
      "must fix it, or the picker must not offer that layout",
      len(fl6) == 1 and not fl6[0][1] and not fl6[0][2]["t1"] and not fl6[0][2]["t6"] and all(v for k, v in fl6[0][2].items() if k not in ("t1", "t6"))
      and 0 < fl6[0][3]["checks"]["t1"]["bad"] < 100, [(t[0], t[2], t[3]["checks"]["t1"]) for t in fl6])
dust = [t for t in SEEN["t"] if "dust" in t[0]]
check("the D15 seam dust (a laboratory switch, off in production) lies on the back iris by design: the check excludes the pixels it touched, and everything else holds",
      len(dust) == 1 and dust[0][1], [t[2] for t in dust])
t1 = [t[3]["checks"]["t1"] for t in SEEN["t"] if t[0] != FLOWER6]
check("T1 in numbers: the largest difference of a pure zone A pixel from the graded iris is 0 on every picture, with five million pixels or more checked in all",
      all(x["max_abs_diff"] == 0 and x["bad"] == 0 for x in t1) and sum(x["checked"] for x in t1) > 5_000_000, (max(x["max_abs_diff"] for x in t1), sum(x["checked"] for x in t1)))
t3 = {t[0]: t[3]["checks"]["t3"] for t in SEEN["t"]}
check("T3 in numbers (the brief's definition: inside 0.985 R): the visible shares of the pairs are 87 percent and more in the woven build and 93 percent and more in the Kiss",
      all(min(v["shares"]) >= 0.87 - 0.004 for k, v in t3.items() if k.startswith(("infinity", "clean"))) and all(min(v["shares"]) >= 0.93 - 0.004 for k, v in t3.items() if k.startswith("kiss")),
      {k: min(v["shares"]) for k, v in t3.items() if k.startswith(("infinity", "clean", "kiss"))})
check("the report of the check is small and JSON safe (it travels in the artwork record): under 6 KB for every picture",
      all(len(json.dumps(t[3])) < 6000 for t in SEEN["t"]), max(len(json.dumps(t[3])) for t in SEEN["t"]))

# ============================================================================================ 4. the seam of DG1
section("4. the seam of DG1: smooth, inside the owner's budget E1, the same at every size, with the stack lens as the safety net")
weave = [k for k in SEEN["plans"] if k.startswith(("infinity", "clean")) and "stack" not in k and ".1:1." not in "" and G[k]["facts"]["lens_mode"] == "weave"]
facts_w = {t[0]: t[3]["checks"]["seam"] for t in SEEN["t"] if t[3]["checks"]["seam"].get("weave")}
check(f"the owner's budget E1 on every woven pair of the replay ({len(facts_w)}): the pixels that are really mixed (0.02 < w < 0.98) are at most about 3 percent of an iris, the seam "
      "band (the blend's support as the integrity test pads it) at most 4 percent",
      len(facts_w) >= 20 and all(f["ok"] and f["mixed"] <= 0.03 and f["support"] <= 0.03 and f["e1"] <= 0.04 for f in facts_w.values()),
      {k: v for k, v in facts_w.items() if not v["ok"]})
print(f"   (mixed {max(f['mixed'] for f in facts_w.values()):.4f}, support {max(f['support'] for f in facts_w.values()):.4f}, band {max(f['e1'] for f in facts_w.values()):.4f}, "
      f"limits 0.03 / 0.03 / 0.04)", flush=True)


def tortuosity(plan, n=400):
    """Length of the planned seam line over its chord, over the stretch of the lens the blend uses (0.92 of its half width): 1.000 is a straight line."""
    s = np.linspace(-0.92 * plan.L, 0.92 * plan.L, n).astype(np.float32)
    c = plan.line(s).astype(np.float64)
    return float(np.hypot(np.diff(s.astype(np.float64)), np.diff(c)).sum() / np.hypot(s[-1] - s[0], c[-1] - c[0])), float(c.max() - c.min())


tw = []
for key, c in ((k, [c for c in ALL if c["key"] == k][0]) for k in ("infinity.blue+brown.3:2.1024", "infinity.blue+green.3:2.1024", "infinity.grey+amber.3:2.1024")):
    rr = CX.render(c["design"], [C.Iris(FIX[n], n) for n in c["eyes"]], c["fmt"], 512)
    pl = list(rr.cfg.plans.values())[0]
    tw.append((key, tortuosity(pl), pl.info["K_chosen"], pl.info["hw_min"], pl.info["hw_max"]))
two_ = [C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b")]
check("names are part of the step A seed (the prototype's: the scene key and the names): the same eyes with other names draw another seed, which step B (WP7B) takes out; "
      "the eyes' own bytes, the design and the background change it too",
      CX.render("infinity", two_, "3:2", 128, ["Anna", "Max"]).seed != CX.render("infinity", two_, "3:2", 128, ["Ana", "Max"]).seed
      and CX.render("infinity", two_, "3:2", 128, ["Anna", "Max"]).seed == CX.render("infinity", two_, "3:2", 128, ["Anna", "Max"]).seed
      and CX.render("infinity", two_, "3:2", 128).seed != CX.render("kiss", two_, "3:2", 128).seed)
check("the seam is a smooth planned curve, not a torn one: its length over its chord is under 1.02 (the round 2c seam wandered to 1.38 to 1.72, the owner's own references measure 1.03 to "
      "1.22) and it leans at most 0.13 R from end to end", all(t[1][0] < 1.02 and t[1][1] <= SP.EXT_MAX + 1e-6 for t in tw), tw)
check("the blend's half width is inside the planner's bounds (0.040 R for the most alike pair, 0.095 R for the most different, scaled down to the owner's budget, never below half of 0.040)",
      all(0.5 * SP.HW_LO - 1e-6 <= t[3] and t[4] <= SP.HW_HI + 1e-6 for t in tw), [(t[0], t[3], t[4]) for t in tw])
p_a, p_b = SEEN["plans"]["infinity.blue+brown.3:2.512"], SEEN["plans"]["infinity.blue+brown.3:2.4096"]
p_c = SEEN["plans"]["infinity.blue+brown.3:2.1024"]
check("the plan is the same at every size: the seam of the pair at 512, 1024 and 4096 px has the same coefficients, the same half widths and the same colour step (a function of the "
      "canonical grade and the geometry, no random number)", p_a == p_b == p_c, (p_a[0], p_b[0], p_c[0]))
c_a = SP.plan_seam(C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b"), 1.3, 1.0, 0.0, K.pupil(C.Iris(FIX["blue"], "a")), K.pupil(C.Iris(FIX["brown"], "b")), C)
c_b = SP.plan_seam(C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b"), 1.3, 1.0, 0.0, K.pupil(C.Iris(FIX["blue"], "a")), K.pupil(C.Iris(FIX["brown"], "b")), C)
check("planning twice gives the identical plan (deterministic: no clock, no random number)", c_a.a == c_b.a and np.array_equal(c_a.hw_k, c_b.hw_k) and c_a.info["K_chosen"] == c_b.info["K_chosen"])
check("the rule of the safety net: a pair is drawn in STACK mode when the colour step across its planned seam is above K 62, and woven otherwise (the net fires on none of the three "
      "synthetic pairs, as on none of the 441 pairs of the 23 gate-passing eyes of the design round)",
      LM.K_STACK == 62.0 and LM.decide({"K_chosen": 61.99}) == "weave" and LM.decide({"K_chosen": 62.01}) == "stack" and LM.decide({"K_chosen": 99}, "weave") == "weave"
      and LM.decide({"K_chosen": 1}, "stack") == "stack" and all(G[k]["facts"]["lens_mode"] == "weave" and G[k]["facts"]["lens_K"] < LM.K_STACK
                                                                for k in G if k.startswith("infinity.") and "stack" not in k and G[k]["facts"]["lens_mode"] is not None), "")
check("the stack lens sits at least 1.57 R apart and at most at the Kiss distance (so that the back iris keeps its 87 percent), and a stack is recorded: design_used stack, fallback "
      "stack_contrast, one iris in front, no weave, no seam plan",
      LM.stack_distance(1.30) == 1.57 and LM.stack_distance(1.65) == 1.65 and LM.stack_distance(1.90) == 1.70
      and all(G[k]["facts"]["design_used"] == "stack" and G[k]["facts"]["fallback"] == "stack_contrast" and G[k]["facts"]["rules"][0][2] in ("front_a", "front_b")
              and abs(G[k]["facts"]["d_over_R"][0] - 1.57) < 0.02 and k not in SEEN["plans"] for k in G if k.endswith(".stack")), [G[k]["facts"] for k in G if k.endswith(".stack")])
stk = [t for t in SEEN["t"] if t[0].endswith(".stack")]
check("forced, the stack lens passes the integrity test, the pupil test and the visible share floor of 87 percent (T1, T2, T3), and has no seam to measure",
      len(stk) == 2 and all(t[1] and t[2]["t1"] and t[2]["t2"] and t[2]["t3"] and t[3]["checks"]["seam"] == {"ok": True, "weave": False} for t in stk), [(t[0], t[2]) for t in stk])
a_, b_ = C.Iris(FIX["green_bar" if "green_bar" in FIX else "blue"], "a"), None
bar = C.Iris(SI.png_bytes("dark_brown_bar"), "bar")
blue = C.Iris(FIX["blue"], "blue")
ex1 = raises(lambda: CX.render("infinity", [bar, blue], "3:2", 256), E.NotOffered)
ex2 = raises(lambda: CX.render("infinity", [blue, bar], "3:2", 256), E.NotOffered)
ex3 = raises(lambda: CX.render("kiss", [blue, bar], "3:2", 256), E.NotOffered)
check("a bar pupil (a horse, a goat) is refused in every design and order, with the reason bar_pupil: the caller answers available false and no picture is made (D17, C9)",
      all(isinstance(x, E.NotOffered) and x.why == "bar_pupil" for x in (ex1, ex2, ex3)), (ex1, ex2, ex3))
kept = CX.render("infinity", [bar, blue], "3:2", 256, opts={"allow_bar": True})
check("... unless a board asks for the flag only (opts allow_bar): the picture is made and info says not_offered", "bar pupil" in kept.info.get("not_offered", ""), kept.info.get("not_offered"))

# ============================================================================================ 5. the tests of the brief
section("5. the tests of the brief on the port")
dark_k = {t[0]: t[3]["checks"]["t4"] for t in SEEN["t"] if t[0].split(".")[0] in ("infinity", "kiss", "trio", "family", "chain") and t[0].endswith(".1024")}
clean_pairs = [c for c in ALL if c["clean"] and c["size"] == 1024 and c["fmt"] == "3:2"]
outside = []
for c in clean_pairs:
    r = CX.render(c["design"], [C.Iris(FIX[n], n) for n in c["eyes"]], c["fmt"], 1024, None, None, "dark", True, None, None)
    img8 = np.asarray(r.img)
    mask = np.ones(img8.shape[:2], bool)
    yy, xx = np.ogrid[:img8.shape[0], :img8.shape[1]]
    for d in r.discs:
        mask &= ((xx - d.cx) ** 2 + (yy - d.cy) ** 2) > (1.03 * d.R) ** 2
    outside.append(float((np.asarray(r.img.convert("L"))[mask] < 3).mean()) if False else float(((img8[mask].astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)) < 3.0).mean()))
check("T4 for Clean Infinity: everything outside the irises is pure black (at least 99.9 percent of the pixels more than 1.03 R from an iris have luma under 3)",
      outside and all(o >= 0.999 for o in outside), outside)
print("   T4 measured (the black share, luma under 12, and the brief's range): " + ", ".join(
    f"{k.split('.')[0]} {v['share']:.2f}{'' if v['in_range'] is None else (' ok' if v['in_range'] else ' OUT')}" for k, v in sorted(dark_k.items())), flush=True)
fl = CX.render("infinity", [C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b")], "3:2", 512, opts={"flood": 5.0})
rep_fl = CX.selfcheck(fl, "infinity", ["x", "infinity", "pair"], [], "")
white = float((np.asarray(fl.img.convert("L")) > 240).mean())
check("T6, no matter on an iris: the whole effect layer flooded with +5 of light turns the background white and still leaves every pure zone A pixel the graded iris",
      white > 0.5 and rep_fl["checks"]["t1"]["bad"] == 0 and rep_fl["checks"]["t6"]["ok"], (white, rep_fl["checks"]["t1"]))
words = CX.render("infinity", [C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b")], "3:2", 256, ["Anna", "Max"], "12 MAY 2026")
words3 = CX.render("family", [C.Iris(FIX[n], n) for n in ("blue", "brown", "green")], "3:2", 256, ["Anna", "Max", "Lina"], None, "dark", False, None, "diag")
words_kiss = CX.render("kiss", [C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b")], "3:2", 256, ["Anna", "Max"], None)
none_ = CX.render("infinity", [C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b")], "3:2", 256)
check("T7, the only text is the customer's: none by default; names drawn in capitals joined by an infinity sign for the infinity designs, an ampersand for a Kiss and a middle dot for "
      "groups; the date as typed; nothing else, in the log or in the source",
      none_.info["text"] == [] and words.info["text"] == ["ANNA \u221e MAX", "12 MAY 2026"] and words_kiss.info["text"] == ["ANNA & MAX"] and words3.info["text"] == ["ANNA \u00b7 MAX \u00b7 LINA"]
      and not re.search(r"SNAPEYES|SUPERNOVA|THE UNIVERSE WITHIN|PRECISION IRIS ART", src_all), (none_.info["text"], words.info["text"], words_kiss.info["text"], words3.info["text"]))
rep_w = CX.selfcheck(words, "infinity", ["x", "infinity", "pair"], ["Anna", "Max"], "12 MAY 2026")
check("... and the check reads the draw log: the names and the date pass T7, a line that is not the customer's would not",
      rep_w["checks"]["t7"]["ok"] and rep_w["checks"]["t7"]["drawn"] == 2 and not SCK.t7_text([{"kind": "names", "text": "THE STUDIO", "px": 9, "baseline": 1}],
                                                                                           CX.customer_strings(["Anna"], ""))["ok"], rep_w["checks"]["t7"])
dk = {k: G[k]["facts"] for k in G if k == "infinity.brown+brown2.3:2.1024"}
check("T10, the contact edge reads: a pair whose back iris is dark (two dark browns) falls back to the hairline contact (edge mode hairline, the back band L* under 26), and the "
      "pairs with light irises keep the dark edge", dk["infinity.brown+brown2.3:2.1024"]["edge_modes"] == {"0": "hairline"}
      and G["infinity.blue+green.3:2.1024"]["facts"]["edge_modes"] == {}, (dk, G["infinity.blue+green.3:2.1024"]["facts"]["edge_modes"]))
check("T10, the hairline retry still fires: with the brief's own edge preset a contact whose edge does not read at 320 px (a step of L* under 8 against the back iris) is drawn again in "
      "hairline mode (info auto_hairline), as the recording says and the replay of that picture reproduced",
      G["infinity.blue+green.3:2.512.brief"]["facts"].get("auto_hairline") == [0] and G["infinity.blue+green.3:2.512.brief"]["facts"]["edge_modes"] == {"0": "hairline"}, G["infinity.blue+green.3:2.512.brief"]["facts"])
hearts = re.compile("heart|love|valentine|cupid", re.I)
check("T12, no hearts: no id, slug, layout id or layout name of the collision styles holds the word, and nothing the render draws does",
      not any(hearts.search(x) for i in COLLISION_STYLES for x in (i, CT.slug_of(i), CT.name_of(i), *[l for n in range(CT.eyes_range(i)[0], CT.eyes_range(i)[1] + 1) for l in CT.layouts_for(i, n)]))
      and not hearts.search(src_all.replace("heart", "") if False else re.sub(r"(?i)hearth", "", src_all)) and all(t[2]["t12"] for t in SEEN["t"]), "")
a_, b_ = C.Iris(FIX["blue"], "a"), C.Iris(FIX["green"], "b")
d1 = CX.render("infinity", [a_, b_], "3:2", 512).info["d_over_R"]
d2 = CX.render("infinity", [a_, b_], "3:2", 512).info["d_over_R"]
orig_pupil = K.pupil


def wide_pupil(ir):
    p = dict(orig_pupil(ir))
    p["r_theta"] = np.full_like(p["r_theta"], 0.52)
    p["cx"], p["cy"], p["rp"] = 0.0, 0.0, 0.52
    return p


with mock.patch.object(K, "pupil", wide_pupil):
    rf = CX.render("infinity", [a_, b_], "3:2", 512)
check("T13, the overlap solver: the distance is deterministic; a pupil that reaches beyond 0.47 R makes Collision Infinity fall back to the Kiss geometry (design kiss, overlap_fallback "
      "logged, d 1.70 R); and the same fallback from the pixels of a wide pupil (the fixture) is in the recording",
      d1 == d2 and rf.info.get("overlap_fallback") is True and rf.info["design_used"] == "kiss" and abs(rf.info["d_over_R"][0] - CL.D_KISS) < 0.02
      and G["infinity.wide+green.3:2.1024"]["facts"]["design_used"] == "kiss" and G["infinity.wide+green.3:2.1024"]["facts"]["overlap_fallback"] is True, (d1, d2, rf.info.get("d_raw")))
rows18 = []
for n in range(3, 9):
    sc = CL.family_scene(n, None, None, 1024)
    rows18.append(CL.dfloor_ok(sc))
for n, fmt in ((3, "3:2"), (4, "3:2"), (4, "3:1"), (5, "3:1"), (6, "3:1")):
    rows18.append(CL.dfloor_ok(CL.chain_scene(n, fmt, 1024)))
for fmt in ("3:2", "5:4", "1:1", "4:5", "9:19.5"):
    rows18.append(CL.dfloor_ok(CL.pair_scene(fmt, 1024, 1.3, False, False, "infinity")))
check("T18, the iris size floor: every default layout has an iris of at least 22 percent of the canvas width (the 3:1 chain at least 0.60 of its height)", all(rows18) and len(rows18) == 16, rows18)
rng = np.random.default_rng(7)
bad19, n19 = [], 0
for n, lay in ((4, "zigzag"), (4, "cluster"), (5, "brick"), (6, "brick"), (7, "brick"), (7, "flower"), (8, "brick"), (5, "flower"), (6, "flower")):
    for trial in range(23):
        Ls = rng.uniform(15, 85, size=n)
        sc1, sc2 = CL.family_scene(n, lay, None, 512), CL.family_scene(n, lay, None, 512)
        E.decide_fronts(sc1, lambda k, phi, Ls=Ls: float(Ls[k]))
        E.decide_fronts(sc2, lambda k, phi, Ls=Ls: float(Ls[k]))
        cnt = E.back_counts(sc1)
        n19 += 1
        if (max(cnt.values()) if cnt else 0) > 2 or [r.mode for r in sc1.rules] != [r.mode for r in sc2.rules]:
            bad19.append((n, lay, trial))
check(f"T19, the stacking solver: {n19} random colour sets on the zigzag, cluster, brick and flower layouts of four to eight eyes: no iris is the back one at more than two contacts, and the "
      "answer is deterministic", n19 >= 200 and not bad19, bad19[:5])

# ============================================================================================ 6. determinism, caches, guards, plates
section("6. determinism, bounded caches, the guards of render() and the plates")
a = CC.render_case(port_render, C.Iris, FIX, [c for c in ALL if c["key"] == "kiss.blue+brown.3:2.1024"][0], {})
check("the same eyes twice in one process give the same picture; so does a fresh Iris of the same bytes", a["sha"] == G["kiss.blue+brown.3:2.1024"]["sha"])
code = ("import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); import hashlib, numpy as np, collision_cases as CC; from _lib.styles import core as C, collision as CX; "
        "fx = {n: CC.fixture_bytes(n) for n in ('blue', 'brown', 'green')}; "
        "r = CX.render('infinity', [C.Iris(fx['blue'], 'a'), C.Iris(fx['green'], 'b')], '3:2', 512, ['Anna', 'Max']); "
        "t = CX.render('trio', [C.Iris(fx[n], n) for n in ('blue', 'brown', 'green')], '1:1', 512); "
        "print(hashlib.sha256(np.ascontiguousarray(np.asarray(r.img)).tobytes()).hexdigest(), hashlib.sha256(np.ascontiguousarray(np.asarray(t.img)).tobytes()).hexdigest())") % (API, HERE)
hs = []
for seed in ("0", "987"):
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=dict(os.environ, PYTHONHASHSEED=seed), timeout=300)
    hs.append(p.stdout.split())
here1 = CC.render_case(port_render, C.Iris, FIX, dict(CC.cases()[0], design="infinity", eyes=["blue", "green"], fmt="3:2", size=512, names=["Anna", "Max"], date="", clean=False,
                                                      layout=None, bg="dark", opts={}), {})
check("two fresh processes with different hash seeds draw the identical pair and trio (equal to this process's picture of the pair)",
      len(hs) == 2 and len(hs[0]) == 2 and hs[0] == hs[1] and hs[0][0] == here1["sha"], (hs, here1["sha"][:12]))
eyes_many = [C.Iris(SI.png_bytes_of(kind="blue", pupil="round", seed=100 + i, side=192), f"m{i}") for i in range(70)]
for ir in eyes_many:
    K.pupil(ir)
    E.band_lstar(ir, 0.0)
for ir in eyes_many[:66]:
    K.gate(ir)
check("the caches are bounded: after 70 different eyes the pupil cache holds at most 64, the gate cache 64 and the iris band cache 32 (the scratch kept every eye it had seen)",
      len(K._PUP) <= 64 and len(K._GATE) <= 64 and len(E._LST) <= 32 and len(JP._cache) <= 4 and len(CMP._RAG_THR) <= 8, (len(K._PUP), len(K._GATE), len(E._LST)))
two = [C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b")]
check("the guards of render(): an unknown design, the wrong number of eyes for a design, an unknown canvas or background and a size outside 64 to 4096 are refused before anything is drawn",
      raises(lambda: CX.render("bond", two), KeyError) is not False and isinstance(raises(lambda: CX.render("trio", two), ValueError), ValueError)
      and isinstance(raises(lambda: CX.render("chain", two), ValueError), ValueError) and isinstance(raises(lambda: CX.render("infinity", two, "7:3"), ValueError), ValueError)
      and isinstance(raises(lambda: CX.render("infinity", two, "3:2", 63), ValueError), ValueError) and isinstance(raises(lambda: CX.render("infinity", two, "3:2", 4097), ValueError), ValueError)
      and isinstance(raises(lambda: CX.render("infinity", two, "3:2", 256, bg="space"), ValueError), ValueError) and isinstance(raises(lambda: CX.render("kiss", [two[0]]), ValueError), ValueError),
      "")
check("the customer's words are cleaned before they are drawn: the old string \"Anna;Max\" and the lockup line \"Anna \u00b7 Max\" are two names, a letter the artwork font cannot draw is left out, "
      "a name is cut at 24 letters, there are at most eight names and the date at 20 characters",
      CX._words("Anna;Max") == ["Anna", "Max"] and CX._words("Anna \u00b7 Max") == ["Anna", "Max"] and CX._words(["Ana\u4e2d", "x" * 40]) == ["Ana", "x" * 24]
      and len(CX._words([str(i) for i in range(12)])) == 8 and CX._words(None) == [] and CX._words(5) == [] and CX._date("12   MAY\u200b 2026 and some more words") == "12 MAY 2026 and some",
      (CX._words("Anna;Max"), CX._date("12   MAY\u200b 2026 and some more words")))
JET_USED = JP.registry("JET")
RIV_USED = JP.registry("RIVER")
check("the JET and RIVER plates of the prototype are the baked library's: 19 JET and 16 RIVER plates pass the accept rules and are the whole usable set (the prototype's pick list), "
      "sorted by id as the prototype's glob was, and every one has a 1K file in the bundle", len(JET_USED) == 19 and len(RIV_USED) == 16 and all(JP.qa(p) for p in JET_USED + RIV_USED)
      and [p["key"] for p in JET_USED] == sorted(p["key"] for p in JET_USED) and all("pro4K" in p["key"] for p in JET_USED + RIV_USED)
      and all(os.path.isfile(PL.bundle_path(p["key"])) for p in JET_USED + RIV_USED), (len(JET_USED), len(RIV_USED)))
widths = [p["width"] for p in RIV_USED]
reach = [p["reach60"] for p in JET_USED]
check("no collision picture decodes a 4K plate: the largest side a placement needs (a Kiss river 0.75 R wide on the largest 5:4 canvas, a jet scaled up to twice its reach on the "
      "largest iris) is below the 1126 px that the 1K file serves, and a 4K request answers PlateUnavailable (the collision plates have no 4K file)",
      0.75 * 0.27 * 819 / min(widths) < 1024 * JP.MAX_UPSCALE and 2.0 * 0.85 * 0.27 * 819 / min(reach) < 1024 * JP.MAX_UPSCALE
      and isinstance(raises(lambda: JP._plate_lum(JET_USED[0], 4000), PL.PlateUnavailable), PL.PlateUnavailable), (0.75 * 0.27 * 819 / min(widths), 2.0 * 0.85 * 0.27 * 819 / min(reach)))
for nm in ("a plate that is not there", "a plate with the wrong size"):
    pass
with mock.patch.object(PL, "bundle_path", lambda pid: os.path.join(TMP, "nowhere", "x.png")):
    PL.clear_memory()
    JP._cache.clear()
    miss = raises(lambda: JP._plate_lum(JET_USED[0], 500), PL.PlateUnavailable)
PL.clear_memory()
JP._cache.clear()
check("a plate that is missing from the bundle is PlateUnavailable with the plate's id (the step holds the order for the owner: never another plate)",
      isinstance(miss, PL.PlateUnavailable) and miss.plate_id == JET_USED[0]["key"] and miss.why == "missing", miss)

# ============================================================================================ 7. the contract and the master plan
section("7. the contract (resolve, preview, tiles, the watermark) and the master plan")
spec_pair = {"style": "duo.kiss_collision", "eyes": 2, "layout": "pair", "names": ["Anna", "Max"]}
eyes2 = [C.Iris(FIX["blue"], "a"), C.Iris(FIX["brown"], "b")]
pv = ST.preview(eyes2, dict(spec_pair, names=None), size=512, check=True)
check("preview(): a Preview of the family with the clean picture, one disc per iris, the graded frames the colour check reads, the design and canvas drawn, the prototype's seed, the colour "
      "class of each eye, the plates the haze took and a self check that passed",
      pv.img.size == (512, 341) and len(pv.discs) == 2 and len(pv.graded) == 2 and pv.design == "kiss" and pv.fmt == "3:2" and pv.size == 512 and isinstance(pv.seed, int)
      and pv.cls == ["own", "dark_brown"] and pv.log["plates"] and pv.log["design_used"] == "kiss" and pv.selfcheck["ok"] is True and pv.selfcheck["checks"]["t3"]["ok"], (pv.log, pv.cls))
wm = ST.watermarked(pv)
check("the free preview is the clean picture with the preview watermark laid on the discs the family reports: the same size, a different picture, the clean one unchanged",
      wm.size == pv.img.size and np.asarray(wm).tobytes() != np.asarray(pv.img).tobytes())
tl = ST.tiles(eyes2, ["duo.kiss_collision", "duo.clean", "duo.collision_infinity"], {"eyes": 2, "names": None}, 256)
alone = {s: ST.preview(eyes2, {"style": s, "eyes": 2, "names": None}, size=256) for s in tl}
check("tiles(): several styles of one eye count on one eye preparation; the bytes of a tile are the same alone and in the batch (the shared Iris caches only its grades)",
      list(tl) == ["duo.kiss_collision", "duo.clean", "duo.collision_infinity"] and all(np.asarray(tl[s].img).tobytes() == np.asarray(alone[s].img).tobytes() for s in tl)
      and tl["duo.clean"].design == "infinity" and tl["duo.kiss_collision"].design == "kiss", {s: tl[s].design for s in tl})
check("a style that is not of the family, a layout the style does not take and the wrong number of eyes are refused",
      isinstance(raises(lambda: ST.preview(eyes2, {"style": "solo.powder", "eyes": 2}, size=64), (ValueError, ST.EngineNotBuilt)), (ValueError, ST.EngineNotBuilt))
      and isinstance(raises(lambda: CX.preview(eyes2, {"style": "duo.clean", "eyes": 2, "layout": "ring"}, 64), ValueError), ValueError)
      and isinstance(raises(lambda: CX.preview(eyes2[:1], {"style": "duo.clean", "eyes": 2}, 64), ValueError), ValueError), "")
prof2 = [EYE.profile_of_bytes(FIX[n], rules=("lid",)) for n in ("blue", "green")]
pw = EYE.profile_of_bytes(FIX["wide"], rules=("lid",))
rv = CX.resolve({"style": "duo.collision_infinity", "eyes": 2, "layout": "pair"}, prof2)
rvw = CX.resolve({"style": "duo.collision_infinity", "eyes": 2, "layout": "pair"}, [pw, prof2[1]])
rvc = CX.resolve({"style": "duo.clean", "eyes": 2, "layout": "pair", "eye_ids": [p.eye_id for p in prof2]}, [p.rec for p in prof2])
check("resolve() needs no pixel: the design, the canvas, the layout and the seed key of a pair; a wide pupil in the sealed profile turns Collision Infinity into the Kiss geometry "
      "(design_used kiss, fallback overlap_fallback) exactly as the render does it; the eye ids come from the spec or the profiles; the seed and the plates are not known "
      "(step A seeds from the bytes of the eyes)",
      rv["design_used"] == "infinity" and rv["fallback"] is None and rv["canvas"] == "3:2" and rv["layout"] == "pair" and rv["size_ratio"] == [1024, 683] and rv["family"] == "collision"
      and rvw["design_used"] == "kiss" and rvw["fallback"] == "overlap_fallback" and rvw["d_over_R"] == CL.D_KISS and rvc["clean"] is True and rvc["eye_ids"] == [p.eye_id for p in prof2]
      and rv["seed"] is None and rv["plates"] is None and rv["seed_from"] == "iris_bytes" and rv["steps"] == ["art"] and rv["seed_key"]["design_used"] == "infinity"
      and rv["seed_key"]["layout"] == "pair" and SD.clean_key(rv["seed_key"]) == rv["seed_key"], (rv, rvw))
check("... and what resolve() says is what the render drew: the three pairs and the wide pupil are the same design, the same canvas and the same size as the recording",
      all(G[k]["facts"]["design_used"] == CX.resolve({"style": "duo.collision_infinity", "eyes": 2}, [EYE.profile_of_bytes(FIX[n], rules=("lid",)) for n in ks])["design_used"]
          for k, ks in (("infinity.blue+green.3:2.1024", ("blue", "green")), ("infinity.wide+green.3:2.1024", ("wide", "green")))), "")
every = {}
for sid in COLLISION_STYLES:
    for n in range(CT.eyes_range(sid)[0], CT.eyes_range(sid)[1] + 1):
        for lay in CT.layouts_for(sid, n):
            rr_ = CX.resolve({"style": sid, "eyes": n, "layout": lay}, None)
            every[(sid, n, lay)] = rr_
check("resolve() answers for every style, eye count and layout of the registry: a design the family draws, a canvas the registry lists, the layout asked, a plan the master can freeze",
      all(v["design_used"] in CX.DESIGNS and v["canvas"] in CT.ENGINE[k[0]]["canvases"] and v["layout"] == k[2] and SD.clean_key(v["seed_key"]) for k, v in every.items()) and len(every) == 25,
      [(k, v["canvas"]) for k, v in every.items() if v["canvas"] not in CT.ENGINE[k[0]]["canvases"]][:3])
check("the plan of a pair, a trio, a family of eight and a chain through the master plan (steps.make_plan): the family, the design drawn, the canvas, the work side the registry caps the "
      "masters at (2048 for a pair, a family and a chain, 4096 for the trio), one art step and a cost the work budget allows",
      all((lambda p: p["family"] == "collision" and p["design_used"] == d and p["work_side"] == w and len(p["steps"]) == 1 and p["steps"][0]["need_s"] < CO.WORK_BUDGET_S)(
          STP.make_plan({"style": s, "eyes": n, "layout": lay}, [{"eye_id": f"{i:016x}", "profile": None} for i in range(1, n + 1)]))
          for s, n, lay, d, w in (("duo.kiss_collision", 2, "pair", "kiss", 2048), ("duo.collision_infinity", 2, "pair", "infinity", 2048), ("grp.collision", 3, "trio", "trio", 4096),
                                  ("grp.collision", 8, "ring", "family", 2048), ("grp.chain", 4, "chain", "chain", 2048))), "")

# a lab order end to end: two small masters, the master plan's art step, the family at 4096 px
order = "261005-wp7a000001"
for i, nm in ((1, "blue"), (2, "brown")):
    im = Image.open(io.BytesIO(FIX[nm])).convert("RGB").resize((512, 512), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=92)
    store.put(f"orders/{order}/eye_{i}.jpg", b.getvalue(), "image/jpeg", upsert=True)
    store.put(f"orders/{order}/eye_{i}.json", store.json_bytes({"created": f"t{i}", "bytes": len(b.getvalue()), "eye_id": f"{i:02x}" * 8}), "application/json", upsert=True)
DELIVERED = []


def fin(r):
    d = {"key": r["key"], "needs_review": bool(r.get("needs_review")), "created_at": int(time.time())}
    DELIVERED.append(r["key"])
    store.put(f"orders/{order}/delivery.json", store.json_bytes(d), "application/json", upsert=True)
    return d


t0 = time.time()
ctx = STP.Ctx(order, {"eyes": 2, "style": "duo.kiss_collision", "layout": "pair", "names": "Anna \u00b7 Max", "title": ""}, by="test", finish=fin)
got = STP.advance(ctx)
art = got["artwork"]
rec_ = json.load(open(os.path.join(STORE, "orders", order, art["key"].split("/")[-1][:-4] + ".json"), encoding="utf-8"))
jpg = Image.open(os.path.join(STORE, "orders", order, art["key"].split("/")[-1]))
check("a master of Kiss Collision through the master plan from two stored 4096 class masters (here 512 px): one art step, the family drew it at 4096 px on the 3:2 canvas, JPEG, the "
      "colour check and the self check are in the record, the names are the lockup the order carries, nothing is held",
      got["final"] and jpg.size == (4096, 2732) and rec_["design_used"] == "kiss" and rec_["selfcheck"]["ok"] is True and rec_["qa"]["ok"] is True and not art["needs_review"]
      and rec_["canvas"] == "3:2" and rec_["facts"]["plates"] and DELIVERED == [art["key"]] and rec_["width"] == 4096, (art, rec_.get("selfcheck")))
print(f"   (the master took {time.time() - t0:.0f} s)", flush=True)
STP.advance(STP.Ctx(order, {"eyes": 2, "style": "duo.kiss_collision", "layout": "pair", "names": "Anna \u00b7 Max", "title": ""}, by="test", finish=fin), "rerun")
del jpg
gc.collect()

# ============================================================================================ 8. real eyes and the scratch tree (LOCAL)
section("8. LOCAL: the real calibration eyes and the port as the scratch plus its edits")
if CALIB and os.path.isdir(CALIB) and os.path.exists(os.path.join(HERE, "data", "collision_goldens_real.json")):
    REAL = json.load(open(os.path.join(HERE, "data", "collision_goldens_real.json"), encoding="utf-8"))
    fx_real = {n: open(os.path.join(CALIB, f"{n}_2_enhanced.jpg"), "rb").read() for n in CC.REAL_EYES}
    local("the real calibration files are the very files of the recording", all(hashlib.sha256(fx_real[n]).hexdigest() == REAL["eye_files"][n] for n in fx_real),
          [n for n in fx_real if hashlib.sha256(fx_real[n]).hexdigest() != REAL["eye_files"][n]])
    irs, bad_r, reps = {}, [], {}
    for c in CC.real_cases():
        rec = CC.render_case(port_render, C.Iris, fx_real, c, irs)
        if any(rec[k] != REAL["cases"][c["key"]][k] for k in ("sha", "seed", "facts", "w", "h")):
            bad_r.append(c["key"])
        r = LAST["r"]
        reps[c["key"]] = CX.selfcheck(r, c["design"], [c["design"], r.info.get("design_used", c["design"]), "x"], [], "")
    local(f"{len(REAL['cases'])} real-eye pictures (the eight pairs of the DG1 boards in both builds of the infinity, two Kiss, a trio, a family of four, a chain) equal the scratch's, "
          "byte for byte", not bad_r and len(REAL["cases"]) == len(CC.real_cases()), bad_r)
    seam = {k: v["checks"]["seam"] for k, v in reps.items() if v["checks"]["seam"].get("weave")}
    pairs_ = [s for k, s in seam.items() if k.startswith("infinity.")]
    print(f"   (real pairs, {len(pairs_)} woven: mixed at most {max(s['mixed'] for s in pairs_):.4f}, support {max(s['support'] for s in pairs_):.4f}, seam band "
          f"{max(s['e1'] for s in pairs_):.4f}; largest K {max(s['K'] for s in pairs_):.1f}; limits 0.03, 0.03, 0.04, 62)", flush=True)
    local("on the real pairs the owner's budget E1 holds (mixed at most 3 percent, band at most 4), the stack lens fires on none (K under 62: the largest of the eight is 46.8) and every "
          "check of the self check passes (T1, T2, T3, T6, T7, T12, T18, T19), the T3 floors with the 0.4 point margin the prototype's own test allowed",
          all(s["ok"] and (s["mode"] == "weave" and s["K"] < 62 if k.startswith("infinity.") else True) for k, s in seam.items()) and len(seam) >= 16 and all(v["ok"] for v in reps.values()),
          {k: (v["ok"], {c: x["ok"] for c, x in v["checks"].items() if not x["ok"]}) for k, v in reps.items() if not v["ok"]})
    ks = {k: round(v["K"], 1) for k, v in seam.items() if k.startswith("infinity.") and not k.startswith("infinity.clean")}
    local("the colour steps K of the eight board pairs are the design round's (blue with brown 46.8, blue with yellow 29.9, a blue with copper 33.2 ...)",
          abs(ks["infinity.own215120+p05i.3:2.1024.blue_brown"] - 46.8) < 0.2 and abs(ks["infinity.own215120+drv_w04.3:2.1024.blue_yellow"] - 29.9) < 0.2, ks)
    T4R = {k: v["checks"]["t4"] for k, v in reps.items()}
    off = {k: (v["share"], v["range"]) for k, v in T4R.items() if v["in_range"] is False}
    local("T4 on the real eyes: the black share of the dark designs is inside the brief's range (Collision Infinity 55 to 70 percent, Kiss 60 to 75, trio 50 to 65, family 50 to 65) "
          "or within three points of it (the check measures it and does not bound it: the very dark pair is 0.3 point over, the family of four 1.8)",
          all(lo - 0.03 <= v["share"] <= hi + 0.03 for v in T4R.values() if v["in_range"] is not None for lo, hi in [v["range"]]) and len(off) <= 3, off)
    irs.clear()
else:
    print("   (the real calibration eyes are used only with SNAPEYES_CALIB; their hashes are in data/collision_goldens_real.json)", flush=True)
if SCRATCH_DG1 and os.path.isdir(SCRATCH_DG1):
    p = subprocess.run([sys.executable, os.path.join(HERE, "port_collision.py"), "--check"], capture_output=True, text=True, timeout=120,
                       env=dict(os.environ, SNAPEYES_REPO=REPO, SNAPEYES_SCRATCH_DG1=SCRATCH_DG1))
    local("the committed files of the family are exactly what the listed edits make of the scratch snapshot (port_collision.py --check: 12 files the same, and the source hashes are the "
          "snapshot's)", p.returncode == 0 and p.stdout.count("same ") == 12 and "DIFFERS" not in p.stdout, (p.stdout[-600:], p.stderr[-300:]))
else:
    print("   (the edit check runs only with SNAPEYES_SCRATCH_DG1)", flush=True)

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed" + (f", {len(LOCAL)} local lines" if LOCAL else ""))
sys.exit(0 if all(RESULTS) and all(LOCAL) else 1)
