# -*- coding: utf-8 -*-
"""The ensemble family of the v3 engine (2026-10-20): the pairs and families of WHOLE irises the owner chose from the laboratory round of the same day (Clean Duo,
Radiance Duo, Family Orbit, Light Circle, Radiance Family) in api/_lib/styles/ensemble, at stage preview. The goldens of the family, the checks of the brief on every
golden picture, the master against the preview, the contract and the master plan.

  1. the family in the repository: its files and the rules of every module, the registry's five entries (stage preview, gate hard, the art price class, the
     working copy, the layouts and their words), the engine table, the family's place in the style package; nothing of it can be bought before the owner's tick
  2. the golden replay: the pictures this code makes, recorded on purpose once (data/ensemble_goldens.json; record again with --record after a reviewed change of a
     picture, together with ENGINE_V and data/engine_v.json), for every look on several sets of synthetic eyes, the canvases, the sizes 512, 1024 and 4096, the
     customer's words, the swapped pair, the rotated group, the tinted thread and a forced frozen palette
  3. the artwork charter and the brief on every picture of the replay: every iris is the graded iris byte for byte (T1, T6), the pupil is untouched (T2), every iris
     whole and no contact (T3, T19), only the customer's words (T7), no hearts (T12), the format margin and the iris size floor (T8, T18), the frame under 3 percent for
     the two Radiance looks (T8b) and the limb read of the ensemble looks (the edge numbers, at 1024 and at a 320 px tile)
  4. T9: the 4096 px master against the 1024 px preview of the same picture (the design SSIM, the colour differences of the design and of the irises)
  5. the contract: resolve (the plan without the eyes and with them), preview, tiles, the watermark; the seed from the eyes' ids and the seed key and nothing else;
     the buyer's options in one canonical form (swap for a pair, rotate for a group: the hub of Family Orbit); the palette choice of the two Radiance looks frozen at
     the plan and obeyed by the master
  6. the master plan: steps.make_plan of every style and eye count (the family, the cost key, the capacity at the slow factor, the steps), and a 4096 px master made the
     way the master step makes it draws the plan's seed and frozen choices (steps._check_drawn)
No network, no image model, no real eye (the eyes are procedural: synth_iris). A golden is exact for this machine class and the pins of requirements.txt.
    python test_goldens_ensemble.py [--record]   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3ensemble."""
import ast
import atexit
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
FAMILY = os.path.join(API, "_lib", "styles", "ensemble")
GOLDEN = os.path.join(HERE, "data", "ensemble_goldens.json")
RECORD = "--record" in sys.argv

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


T_START = time.time()


def section(title):
    print(f"\n== {title}   [{time.time() - T_START:.0f} s since the start]", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3ensemble_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)   # its own folder only: gone at exit, green, red or crashed
os.environ.update({"PYTHONIOENCODING": "utf-8", "STORE_LOCAL_DIR": os.path.join(TMP, "store"), "STYLE_PLATE_CACHE": os.path.join(TMP, "cache")})
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
sys.path.insert(0, API)
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
import collision_cases as CCS  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
import _lib.styles as ST  # noqa: E402
from _lib.styles import core as C, costs as CO, seeds as SD, steps as STP, text as TX  # noqa: E402
from _lib.styles import ensemble as HL  # noqa: E402
from _lib.styles.ensemble import base as HB, checks as HCK  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
STYLES = {"duo.clean_duo": "clean_duo", "duo.radiance": "radiance_duo", "grp.orbit": "orbit", "grp.light_circle": "light_circle", "grp.radiance": "radiance_family"}


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


# ============================================================================================ 1. the family in the repository
section("1. the family in the repository, the registry, the engine table")
mods = sorted(f for f in os.listdir(FAMILY) if f.endswith(".py"))
check("the package holds the contract, the renderer, the pieces, the checks and one module per look",
      mods == sorted(["__init__.py", "base.py", "pieces.py", "corona.py", "checks.py", "clean_duo.py", "radiance_duo.py", "orbit.py", "light_circle.py", "radiance_family.py"]), mods)
srcs = {m: read(os.path.join("api", "_lib", "styles", "ensemble", m)) for m in mods}
check("every module starts with the __future__ import and parses as Python 3.12 (Vercel's default)",
      all(re.search(r"^from __future__ import annotations\r?$", s, re.M) and ast.parse(s, feature_version=(3, 12)) for s in srcs.values()), "")
check("no en or em dash, no raw invisible or bidirectional character in any module of the family",
      not any(re.search(DASH, s) or re.search("[​-‏ -‮⁠-⁤﻿]", s) for s in srcs.values()), [m for m, s in srcs.items() if re.search(DASH, s)])
imports = set()
for m, s in srcs.items():
    for node in ast.walk(ast.parse(s)):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            imports.add(node.module.split(".")[0])
check("numpy, Pillow and the standard library only (no network, no model, no environment, no file path): the family reads nothing but the eyes it is given",
      imports <= {"__future__", "math", "time", "numpy", "PIL"} and not any(re.search(r"os\.environ|open\(|requests|urllib|gemini", s, re.I) for s in srcs.values()), (imports, ))
check("the family is one of the style package's engine families, and the catalogue sees it built (without importing it)",
      "ensemble" in ST.ENGINE_FAMILIES and CT.engine_built("ensemble"), ST.ENGINE_FAMILIES)
code = ("import sys; sys.path.insert(0, %r); import _lib.styles, _lib.catalogue; print(sorted(m for m in sys.modules if m.startswith('_lib.styles.')))") % API
imp = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
check("importing the style package and the catalogue loads no engine family (the ensemble family is loaded on first use, like the others)",
      imp.returncode == 0 and imp.stdout.strip() == "[]", (imp.stdout[-300:], imp.stderr[-300:]))
reg = {sid: CT.STYLES[sid] for sid in STYLES}
eng = {sid: CT.ENGINE[sid] for sid in STYLES}
check("the registry has the five styles at stage preview (drawn in /try, never orderable until the owner's tick), in the art price class, with the HARD gate and the lid rule",
      all(d["stage"] == "preview" and d["stage_by_eyes"] == {} and d["price_class"] == "art" and d["gate"] == "hard" and d["legacy"] == 0 for d in reg.values())
      and all(e["gate_rules"] == "lid" and e["plates"] == [] and e["atlas"] == [] for e in eng.values()), {s: (d["stage"], d["gate"]) for s, d in reg.items()})
check("their engine is the ensemble family with the design of each look; the names are the owner's (Clean Duo, Radiance Duo, Family Orbit, Light Circle, Radiance Family)",
      all(eng[s]["engine"] == {"module": "ensemble", "design": STYLES[s]} for s in STYLES)
      and [reg[s]["name"] for s in STYLES] == ["Clean Duo", "Radiance Duo", "Family Orbit", "Light Circle", "Radiance Family"], {s: eng[s]["engine"] for s in STYLES})
check("the pairs take two eyes in the layout pair, the families three to eight (Family Orbit the new layout orbit, Light Circle the ring, Radiance Family the triangle, the "
      "zigzag and the rows), and every layout has its word in the four languages",
      reg["duo.clean_duo"]["eyes"] == [2, 2] and reg["duo.radiance"]["layouts"] == {"2": ["pair"]} and reg["duo.clean_duo"]["layouts"] == {"2": ["pair"]}
      and all(reg[s]["eyes"] == [3, 8] for s in ("grp.orbit", "grp.light_circle", "grp.radiance"))
      and all(reg["grp.orbit"]["layouts"][str(n)] == ["orbit"] and reg["grp.light_circle"]["layouts"][str(n)] == ["ring"] for n in range(3, 9))
      and reg["grp.radiance"]["layouts"] == {"3": ["trio"], "4": ["zigzag"], "5": ["brick"], "6": ["brick"], "7": ["brick"], "8": ["brick"]}
      and sorted(CT.LAYOUT_NAMES["orbit"]) == ["de", "en", "hu", "lt"] and CT.layout_name("lt", "orbit") == "Orbita", reg["grp.radiance"]["layouts"])
check("a working copy of 2048 px for every eye count (the master reads each eye at most 2048 px wide, as the pairs and Family Colours do), and a place in the picker's order",
      all(CT.work_side(s, n) == 2048 for s in STYLES for n in range(reg[s]["eyes"][0], reg[s]["eyes"][1] + 1))
      and sorted(reg[s]["tile_order"] for s in ("duo.clean_duo", "duo.radiance")) == [4, 5] and sorted(reg[s]["tile_order"] for s in ("grp.orbit", "grp.light_circle", "grp.radiance")) == [3, 4, 5],
      {s: reg[s]["tile_order"] for s in STYLES})
CT.set_override_source(lambda sid, n: None)
check("with no tick of the owner every new style is at preview for every eye count it takes: previewable for a customer, renderable, and orderable for no one",
      all(CT.stage_of(s, n) == "preview" and CT.previewable(s, n) and CT.renderable(s, n) and not CT.orderable(s, n, strict=False)
          for s in STYLES for n in range(reg[s]["eyes"][0], reg[s]["eyes"][1] + 1)), "")
check("the canvases the registry lists are canvases each look draws, its default first where the default does not depend on the eye count",
      all(set(eng[s]["canvases"]) <= set(HL.looks()[STYLES[s]]["canvases"]) for s in STYLES)
      and eng["duo.clean_duo"]["canvases"][0] == "3:2" and eng["grp.orbit"]["canvases"][0] == "1:1", {s: eng[s]["canvases"] for s in STYLES})
check("no heart and no pet word in an id, a slug, a name or a layout of the family (T12, the owner's rule)",
      not any(w in re.split(r"[^a-z]+", f"{s} {reg[s]['slug']} {reg[s]['name']} {' '.join(sum(reg[s]['layouts'].values(), []))}".lower())
              for s in STYLES for w in ("heart", "hearts", "love", "valentine", "cupid", "paw", "cat", "dog")), "")
check("the existing pairs and families are not this family and did not move: Clean Infinity, Collision Infinity, Kiss Collision and Family Colours keep the collision engine",
      all(CT.ENGINE[s]["engine"]["module"] == "collision" for s in ("duo.clean", "duo.collision_infinity", "duo.kiss_collision", "grp.collision"))
      and CT.STYLES["grp.collision"]["tile_order"] == 1 and CT.STYLES["duo.kiss_collision"]["tile_order"] == 1, "")

# ============================================================================================ 2. the golden replay
section("2. the golden replay")
EYES = {n: CCS.fixture_bytes(n) for n in ("blue", "green", "brown", "grey", "amber", "blue2", "green2", "brown2")}
EYE_IDS = {n: hashlib.sha256(b).hexdigest()[:16] for n, b in EYES.items()}
BIG = {}


def eyes_of(names, big=False):
    """Iris objects: the 1024 px fixtures (a preview), or the same eyes drawn at 2048 px carrying the 1024 px fixture's id (a master: another image of the same eye)."""
    out = []
    for n in names:
        if big:
            if n not in BIG:
                b = io.BytesIO()
                SI.make(side=2048, **CCS.EYE_SPECS[n]).save(b, "PNG", compress_level=3)
                BIG[n] = b.getvalue()
            out.append(C.Iris(BIG[n], f"big_{n}", max_side=2048, eye_id=EYE_IDS[n]))
        else:
            out.append(C.Iris(EYES[n], n, max_side=2048))
    return out


TXT = {"names": ["Anna", "Max", "Lina"], "date": "12 MAY 2026"}
P1, P2, P3 = ("blue", "brown"), ("green", "grey"), ("amber", "blue2")
F8 = ("blue", "brown", "green", "grey", "amber", "blue2", "green2", "brown2")


def case(style, eyes, fmt=None, size=1024, text=False, opts=None, eo=None, frozen=None, tag=""):
    key = f"{style}.{'+'.join(eyes)}.{fmt or 'default'}.{size}" + (".text" if text else "") + (f".{tag}" if tag else "")
    return {"key": key, "style": style, "eyes": list(eyes), "fmt": fmt, "size": size, "text": text, "opts": dict(opts or {}), "eo": dict(eo or {}), "frozen": frozen}


def cases():
    out = []
    for s in ("duo.clean_duo", "duo.radiance"):
        for p in (P1, P2, P3):
            out.append(case(s, p))
        out.append(case(s, P1, "4:5", 512))
        out.append(case(s, P2, "9:19.5", 512))
        out.append(case(s, P1, "5:4", 512))
        out.append(case(s, P1, text=True))
        out.append(case(s, P1, opts={"swap": True}, tag="swap"))
        out.append(case(s, P1, size=4096))
    out.append(case("duo.clean_duo", P1, eo={"thread": "tint"}, tag="tint"))
    out.append(case("duo.radiance", ("brown", "brown2"), tag="dark"))
    out.append(case("duo.radiance", ("blue", "blue2"), tag="near"))
    out.append(case("duo.radiance", ("blue", "blue2"), frozen={"pal": [0, 2]}, tag="frozen"))
    for s in ("grp.orbit", "grp.light_circle", "grp.radiance"):
        for n in (3, 4, 5, 8):
            out.append(case(s, F8[:n]))
        out.append(case(s, F8[:5], text=True))
        out.append(case(s, F8[:4], opts={"rotate": 2}, tag="rot2"))
        out.append(case(s, F8[:5], size=4096))
    out.append(case("grp.orbit", F8[:5], "4:5", 512))
    out.append(case("grp.light_circle", F8[:6], "4:5", 512))
    out.append(case("grp.radiance", F8[:6]))
    out.append(case("grp.radiance", F8[:5], "1:1", 512))
    return out


def spec_of(c):
    n = len(c["eyes"])
    return {"style": c["style"], "eyes": n, "layout": None, "canvas": c["fmt"], "names": TXT["names"][:n] if c["text"] else None,
            "date": TXT["date"] if c["text"] else "", "opts": c["opts"], "engine_opts": c["eo"] or None, "frozen": c["frozen"]}


def run_case(c):
    eyes = eyes_of(c["eyes"], big=c["size"] > 2048)
    pv = ST.preview(eyes, spec_of(c), size=c["size"], watermark=False, check=True)
    a = np.asarray(pv.img)
    return pv, a, hashlib.sha256(a.tobytes() + repr(a.shape).encode()).hexdigest()


CASES = cases()
gold = {} if RECORD else json.load(open(GOLDEN, encoding="utf-8"))["cases"]
got, PVS = {}, {}
for c in CASES:
    t0 = time.time()
    pv, a, sha = run_case(c)
    got[c["key"]] = {"sha": sha, "w": pv.img.size[0], "h": pv.img.size[1], "seed": str(pv.seed), "design": pv.design, "fmt": pv.fmt,
                     "frozen": pv.log.get("frozen") or {}, "discs": [[round(float(v), 2) for v in d] for d in pv.discs]}
    PVS[c["key"]] = (c, pv, a)
    print(f"   {c['key']}: {time.time() - t0:.1f} s", flush=True)
if RECORD:
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
    with open(GOLDEN, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"note": "the pictures of the ensemble family (api/_lib/styles/ensemble) on the synthetic eyes of synth_iris, recorded by test_goldens_ensemble.py --record: "
                           "sha256 of the decoded pixels and their shape, the seed, the design, the canvas, the frozen choices and the discs of every case. Exact for "
                           "this machine class and the pins of requirements.txt", "engine_v": ST.ENGINE_V, "cases": got}, f, indent=1, sort_keys=True)
    print("recorded", GOLDEN, len(got), "cases")
    gold = got
check(f"the replay has every recorded case ({len(CASES)} pictures: the five looks, the canvases, 512, 1024 and 4096 px, the words, the swapped pair, the rotated group, "
      "the tinted thread, the dark pair, a near pair whose palettes move, a forced frozen palette)", sorted(gold) == sorted(got), sorted(set(gold) ^ set(got))[:6])
diff = [k for k in got if k in gold and got[k]["sha"] != gold[k]["sha"]]
check("every picture is byte for byte its golden (decoded pixels): the family draws what was recorded and reviewed", not diff, diff[:8])
check("and so are their seeds, designs, canvases, frozen choices and the places of the irises",
      all(got[k][f] == gold[k][f] for k in got if k in gold for f in ("seed", "design", "fmt", "frozen", "discs", "w", "h")),
      [k for k in got if k in gold and any(got[k][f] != gold[k][f] for f in ("seed", "design", "fmt", "frozen", "discs"))][:6])

# ============================================================================================ 3. the charter and the brief on every picture
section("3. the artwork charter and the checks of the brief on every picture of the replay")
reps = {k: pv.selfcheck for k, (c, pv, a) in PVS.items()}
check("T1 and T6: every pixel of zone A (r <= 0.95 R) of every iris of every picture is its graded disc, 0 of 255 (the iris is never repainted, blurred or recoloured)",
      all(r["checks"]["t1"]["ok"] and r["checks"]["t1"]["bad"] == 0 and r["checks"]["t1"]["max_abs_diff"] == 0 and r["checks"]["t6"]["count"] == 0 for r in reps.values()),
      [k for k, r in reps.items() if r["checks"]["t1"]["bad"] or r["checks"]["t1"]["max_abs_diff"]][:5])
check("T2: nothing over a pupil (the pupil grown by 0.01 R is the graded disc, 0 violations on every iris)",
      all(r["checks"]["t2"]["violations"] == 0 for r in reps.values()), [k for k, r in reps.items() if r["checks"]["t2"]["violations"]][:5])
check("T3 and T19: every iris whole (no two irises touch: the least limb to limb gap is positive) and no contact anywhere",
      all(r["checks"]["t3"]["ok"] and r["checks"]["t3"]["min_gap_R"] > 0.1 and r["checks"]["t19"]["contacts"] == 0 for r in reps.values()),
      {k: r["checks"]["t3"]["min_gap_R"] for k, r in reps.items() if r["checks"]["t3"]["min_gap_R"] <= 0.1})
check("T7 and T12: only the customer's words are drawn (the lockup of the names and the date, by text.draw_names) and no heart anywhere",
      all(r["checks"]["t7"]["ok"] and r["checks"]["t12"]["ok"] for r in reps.values())
      and all(r["checks"]["t7"]["drawn"] == (2 if PVS[k][0]["text"] else 0) for k, r in reps.items()), [k for k, r in reps.items() if not r["checks"]["t7"]["ok"]][:5])
check("T8 and T18: every iris inside a margin of 0.05 S (on the phone wallpaper inside the clock fifth and the foot) and at least 22 percent of the canvas width",
      all(r["checks"]["t8"]["ok"] and r["checks"]["t18"]["ok"] for r in reps.values()), {k: (r["checks"]["t8"], r["checks"]["t18"]) for k, r in reps.items() if not (r["checks"]["t8"]["ok"] and r["checks"]["t18"]["ok"])})
check("T8b: the outer 0.02 S of every Radiance picture stays under 3 percent of white (the Radiance brief's bound; the light fades out by 2.85 R and over the last 0.035 S)",
      all(r["checks"]["t8b"]["frame_luma"] <= 0.03 for k, r in reps.items() if PVS[k][0]["style"] in ("duo.radiance", "grp.radiance"))
      and all(r["checks"]["t8b"]["bounded"] == (PVS[k][0]["style"] in ("duo.radiance", "grp.radiance")) for k, r in reps.items()),
      {k: r["checks"]["t8b"]["frame_luma"] for k, r in reps.items() if r["checks"]["t8b"]["bounded"] and r["checks"]["t8b"]["frame_luma"] > 0.03})
check("every report is ok (every bounded check of every picture passes)", all(r["ok"] for r in reps.values()), [k for k, r in reps.items() if not r["ok"]][:6])
edge = {k: (r["checks"]["edge"]["min_1024"], r["checks"]["edge"]["min_320"]) for k, r in reps.items() if PVS[k][1].size <= 1024}
check("the limb reads: every iris of Clean Duo, Radiance Duo, Family Orbit and Light Circle at least 6 L* from the ring outside it at 1024 px and at a 320 px tile (the "
      "laboratory's bar; the synthetic eyes have a dark limbal ring of their own, the owner's real sets read 7 to 38), the dark brown pair of Radiance Duo included (its dark "
      "limb keeps the deeper moat)",
      all(v[0] >= 6.0 and v[1] >= 6.0 for k, v in edge.items() if PVS[k][0]["style"] != "grp.radiance"),
      {k: v for k, v in edge.items() if PVS[k][0]["style"] != "grp.radiance" and not (v[0] >= 6.0 and v[1] >= 6.0)})
rf = {k: v for k, v in edge.items() if PVS[k][0]["style"] == "grp.radiance"}
check("Radiance Family reads at least 4 L* at the limb everywhere (its short rays run all round each iris: the laboratory's 4 to 5.7 is the known weak point, reported "
      "on the owner's board)", all(v[1] >= 4.0 for v in rf.values()), rf)
print("   (edge, least of each picture at 1024 / 320 px: " + ", ".join(f"{k.split('.')[1]}.{len(PVS[k][0]['eyes'])} {v[0]}/{v[1]}" for k, v in list(edge.items())[:60]) + ")")

# ============================================================================================ 4. T9: the master against the preview
section("4. T9: the 4096 px master against the 1024 px preview of the same picture")
t9 = {}
for k, (c, pv, a) in PVS.items():
    if c["size"] != 4096:
        continue
    k1 = k.replace(".4096", ".1024")
    _c1, pv1, a1 = PVS[k1]
    t9[k] = HCK.t9_scale(a1, pv1.discs, a)
check("T9: every 4096 px master is its 1024 px preview made larger: the design SSIM at least 0.95 (several eyes), its mean dE00 at most 1.5 and p99 at most 10, the "
      "irises' own mean dE00 at most 3.0 (T9b); the seed and the frozen choices are the preview's", len(t9) == 5 and all(v["ok"] for v in t9.values())
      and all(PVS[k][1].seed == PVS[k.replace(".4096", ".1024")][1].seed and PVS[k][1].log.get("frozen") == PVS[k.replace(".4096", ".1024")][1].log.get("frozen") for k in t9), t9)
print("   " + "; ".join(f"{k.split('.')[1]}: ssim {v['ssim_design']}, dE {v['dE_mean_design']}/{v['dE_p99_design']}, iris {v['dE_iris_T9b']}" for k, v in t9.items()))

# ============================================================================================ 5. the contract
section("5. the contract: resolve, preview, tiles, the watermark, the seed, the options, the frozen palette")
CT.set_override_source(lambda sid, n: None)
check("the family takes the eyes at the plan (the two Radiance looks freeze their palette choice there): styles.wants_eyes is True for its styles",
      all(ST.wants_eyes({"style": s, "eyes": CT.eyes_range(s)[0]}) for s in STYLES), "")
ids2 = [EYE_IDS[n] for n in P1]
pl = ST.resolve({"style": "duo.clean_duo", "eyes": 2, "layout": None, "opts": {}, "eye_ids": ids2}, [None, None])
pv_c = PVS["duo.clean_duo.blue+brown.default.1024"][1]
check("resolve of a pair: the family, the design, the layout, the default canvas, the geometry at 1024 px, the seed key and the seed from the eye ids, which is the "
      "preview's own seed; nothing to decide from the pixels (decided, frozen empty), no plate",
      pl["family"] == "ensemble" and pl["design_used"] == "clean_duo" and pl["layout"] == "pair" and pl["canvas"] == "3:2" and pl["decided"] is True and pl["frozen"] == {}
      and pl["plates"] == [] and pl["seed"] == str(pv_c.seed) and len(pl["geometry"]["slots"]) == 2 and pl["seed_key"]["design_used"] == "clean_duo", pl)
pr0 = ST.resolve({"style": "duo.radiance", "eyes": 2, "layout": None, "opts": {}, "eye_ids": [EYE_IDS["blue"], EYE_IDS["blue2"]]}, [None, None])
pr1 = ST.resolve({"style": "duo.radiance", "eyes": 2, "layout": None, "opts": {}, "eye_ids": [EYE_IDS["blue"], EYE_IDS["blue2"]]}, [None, None],
                 eyes=eyes_of(("blue", "blue2")))
pv_n = PVS["duo.radiance.blue+blue2.default.1024.near"][1]
check("Radiance Duo: without the eyes the plan cannot know the palette choice (decided False); with them it decides it (two blues within 10 dE00: one of them takes "
      "its next variant) and the preview of the same eyes draws exactly that choice",
      pr0["decided"] is False and pr0["frozen"] == {} and pr1["decided"] is True and isinstance(pr1["frozen"].get("pal"), list) and sum(pr1["frozen"]["pal"]) > 0
      and pv_n.log["frozen"] == pr1["frozen"], (pr0["frozen"], pr1["frozen"], pv_n.log.get("frozen")))
pv_f = PVS["duo.radiance.blue+blue2.default.1024.frozen"][1]
check("a frozen palette is obeyed even where these eyes would choose otherwise (the master of another copy of the eyes draws the plan's choice): another picture, "
      "the same seed", pv_f.log["frozen"] == {"pal": [0, 2]} and pv_f.seed == pv_n.seed and PVS["duo.radiance.blue+blue2.default.1024.frozen"][2].tobytes() != PVS["duo.radiance.blue+blue2.default.1024.near"][2].tobytes(),
      (pv_f.log.get("frozen"), pv_n.log.get("frozen")))
fam_eyes = F8[:5]
rf0 = ST.resolve({"style": "grp.radiance", "eyes": 5, "layout": None, "opts": {}, "eye_ids": [EYE_IDS[n] for n in fam_eyes]}, [None] * 5, eyes=eyes_of(fam_eyes))
check("Radiance Family: the plan with the eyes freezes one palette variant per eye in canvas order, and the preview draws it",
      rf0["decided"] is True and len(rf0["frozen"]["pal"]) == 5 and PVS["grp.radiance.blue+brown+green+grey+amber.default.1024"][1].log["frozen"] == rf0["frozen"], rf0["frozen"])
ef = HL.effective_opts
check("the buyer's options in one canonical form (one choice, one seed): swap only for a pair, rotate only for a group and modulo the number of eyes, 0 is the default, the look means nothing here",
      ef("clean_duo", {"swap": True}, 2) == {"swap": True, "rotate": None, "look": None} and ef("clean_duo", {"swap": False}, 2) == ef("clean_duo", {}, 2)
      and ef("clean_duo", {"rotate": 1}, 2)["rotate"] is None and ef("orbit", {"rotate": 5}, 5)["rotate"] is None and ef("orbit", {"rotate": 6}, 5)["rotate"] == 1
      and ef("orbit", {"swap": True}, 4)["swap"] is None and ef("light_circle", {"rotate": 0}, 3) == ef("light_circle", {}, 3) and ef("orbit", {"look": "echo"}, 3)["look"] is None, "")
a_plain, a_swap = PVS["duo.clean_duo.blue+brown.default.1024"][1], PVS["duo.clean_duo.blue+brown.default.1024.swap"][1]
check("a swapped pair draws the two irises the other way round (the first disc shows the second eye) and has its own seed",
      a_plain.graded[0].shape == a_swap.graded[1].shape and np.array_equal(a_plain.graded[0], a_swap.graded[1]) and a_plain.seed != a_swap.seed, "")
o_plain, o_rot = PVS["grp.orbit.blue+brown+green+grey.default.1024"][1], PVS["grp.orbit.blue+brown+green+grey.default.1024.rot2"][1]
check("Family Orbit: the first eye of the canvas order is the hub (the largest disc in the middle) and rotate 2 makes the third eye the hub (the customer chooses the hub "
      "by the order of the eyes or by rotate)", o_plain.discs[0][2] > 1.15 * o_plain.discs[1][2] and o_rot.discs[0][2] > 1.15 * o_rot.discs[1][2]
      and o_plain.seed != o_rot.seed, (o_plain.discs[:2], o_rot.discs[:2]))
g_hub = o_rot.graded[0]
check("the hub of the rotated orbit IS the third eye (green), graded byte for byte, and the unrotated hub is the first (blue)",
      np.array_equal(eyes_of(("green",))[0].graded(g_hub.shape[0]), g_hub) and np.array_equal(eyes_of(("blue",))[0].graded(o_plain.graded[0].shape[0]), o_plain.graded[0]), "")
t_plain, t_txt = PVS["grp.light_circle.blue+brown+green+grey+amber.default.1024"][1], PVS["grp.light_circle.blue+brown+green+grey+amber.default.1024.text"][1]
check("the customer's words: one lockup line of the names and the date under the irises (text.draw_names), the artwork moved up and shrunk to 0.94 to make room, the "
      "same seed (the words are not in it)", [e["kind"] for e in t_txt.text_log] == ["names", "date"] and t_txt.text_log[0]["text"] == TX.lockup(TXT["names"][:5])
      and t_txt.seed == t_plain.seed and abs(t_txt.discs[0][2] / t_plain.discs[0][2] - 0.94) < 0.01, t_txt.text_log)
eyes5 = eyes_of(F8[:5])
tl = HL.tiles(eyes5, ["grp.orbit", "grp.light_circle", "grp.radiance"], {"style": "grp.orbit", "eyes": 5, "opts": {}}, size=480)
alone = HL.preview(eyes_of(F8[:5]), {"style": "grp.light_circle", "eyes": 5, "opts": {}}, size=480)
check("tiles: several styles on one eye preparation, each the picture its own preview makes (a tile does not depend on the other tiles of the call)",
      list(tl) == ["grp.orbit", "grp.light_circle", "grp.radiance"] and np.array_equal(np.asarray(tl["grp.light_circle"].img), np.asarray(alone.img)), "")
wm = ST.watermarked(PVS["grp.orbit.blue+brown+green.default.1024"][1])
check("the free preview: styles.watermarked marks every iris of a ensemble picture (one studio graded frame per eye) and leaves the clean picture as it was",
      wm.size == PVS["grp.orbit.blue+brown+green.default.1024"][1].img.size and np.asarray(wm).tobytes() != PVS["grp.orbit.blue+brown+green.default.1024"][2].tobytes(), "")
try:
    HL.preview(eyes_of(P1), {"style": "grp.orbit", "eyes": 2, "opts": {}})
    bad = False
except ValueError:
    bad = True
try:
    HL.render("orbit", eyes_of(P1))
    bad2 = False
except ValueError:
    bad2 = True
try:
    HL.render("clean_duo", eyes_of(P1), fmt="3:1")
    bad3 = False
except ValueError:
    bad3 = True
check("the guards: a style of another eye count, a look given too few eyes, a canvas the look has no scene on are refused before anything is drawn", bad and bad2 and bad3, (bad, bad2, bad3))

# ============================================================================================ 6. the master plan
section("6. the master plan: the plan of every style and eye count, the capacity, a master made the master step's way")
caps = {}
for s, d in STYLES.items():
    lo, hi = CT.eyes_range(s)
    for n in range(lo, hi + 1):
        names = (F8 * 2)[:n]
        ev = [{"eye_id": EYE_IDS[x], "profile": None} for x in names]
        p = STP.make_plan({"style": s, "layout": None, "eyes": n, "opts": {}}, ev, irises=eyes_of(names), factor=1.6)
        caps[(s, n)] = p
check("steps.make_plan of every style and eye count: the ensemble family, the engine version, the design, the cost key ensemble.<design>, one art step, the seed from the eye ids, "
      "decided (with the eyes), and a plan8", all(p["family"] == "ensemble" and p["engine_v"] == ST.ENGINE_V and p["design_used"] == STYLES[s] and p["cost_key"] == f"ensemble.{STYLES[s]}"
                                                   and len(p["steps"]) == 1 and p["steps"][0]["kind"] == "art" and p["seed"] and p["decided"] is True and re.fullmatch(r"[0-9a-f]{8}", p["plan8"])
                                                   for (s, n), p in caps.items()), [(k, p.get("cost_key"), p.get("decided")) for k, p in caps.items()][:4])
check("the cost table has a measured row of every style and eye count (masters at 4096 px from the 2048 px working copy, and the 1024 px previews): no plan of the family is "
      "unpriced", all(CO.known(f"ensemble.{d}", n) and n in CO.CAPPED[f"ensemble.{d}"] and n in CO.PREVIEW[f"ensemble.{d}"] for s, d in STYLES.items()
                      for n in range(CT.eyes_range(s)[0], CT.eyes_range(s)[1] + 1)), "")
fits = {f"{s}/{n}": STP.capacity(p, 1.6) for (s, n), p in caps.items()}
OVER = ["grp.orbit/7", "grp.orbit/8", "grp.radiance/7", "grp.radiance/8"]
check("at the default slow factor (1.6) every plan of the family fits one call's work and memory budgets but four: Family Orbit and Radiance Family at seven and eight eyes "
      "need 53 to 65 s of the 52 s (measured: checkout answers capacity for them, never a held order). PINNED, so that a change of the table or of the budget is seen",
      sorted(k for k, v in fits.items() if not v["ok"]) == OVER and all(fits[k]["why"] == "time" for k in OVER) and all(v["est_mb"] < CO.MEM_BUDGET_MB for v in fits.values()),
      {k: (v["need_s"], v["est_mb"], v["why"]) for k, v in fits.items() if not v["ok"]})
print("   (need s at factor 1.6: " + ", ".join(f"{k} {v['need_s']}" for k, v in fits.items()) + ")")
plan = caps[("duo.radiance", 2)]
mspec = {"style": plan["style"], "layout": plan["layout"], "eyes": 2, "canvas": plan.get("canvas"), "names": "", "date": "", "opts": plan.get("opts"),
         "pv": plan.get("pv"), "frozen": plan.get("frozen") or None}
pvm = ST.preview(eyes_of((F8 * 2)[:2], big=True), mspec, size=4096, watermark=False, check=True)
try:
    STP._check_drawn(plan, pvm)
    drawn_ok = True
except STP.Hold as h:
    drawn_ok = h.reason
check("a 4096 px master made the master step's way (eyes of another size carrying the plan's ids, the plan's frozen choices) draws the plan's seed, design and frozen "
      "palette: steps._check_drawn holds no picture_drift, and its self check is ok", drawn_ok is True and pvm.selfcheck["ok"] and str(pvm.seed) == plan["seed"], (drawn_ok, plan.get("frozen")))
plan_bad = dict(plan, frozen={"pal": [3, 0]})
try:
    STP._check_drawn(plan_bad, pvm)
    held = False
except STP.Hold as h:
    held = h.reason == "picture_drift"
check("a picture that drew other frozen choices than its plan names is never delivered (picture_drift: the ensemble family is checked like the collision and universe families)", held, "")

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed   [{time.time() - T_START:.0f} s]")
sys.exit(0 if all(RESULTS) else 1)
