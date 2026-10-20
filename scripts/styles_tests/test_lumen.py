# -*- coding: utf-8 -*-
"""The light family of the v3 engine (api/_lib/styles/lumen): the five looks of one eye the owner chose on 2026-10-20 (Supernova, Nebula, Sparks, Halo,
Aurora), registered as styles at stage preview (shown in /try and its picker, not orderable), drawn by the real engine path. The family's own guard:

  1. the family in the repository: its files, the rules of every module, the registry and the engine table agree with it, the stages, the gate policy, the
     cost rows, the catalogue (previewable, never orderable, the picker's order), and the singles family untouched
  2. the golden replay: the SHA-256 of the pictures this code makes (record_goldens_lumen.py) for every look x three synthetic eye classes at 512 and
     1024 px, a 4096 px master of every look, the other two canvases and the text lockup; seeds and facts equal too; the replay can fail
  3. the artwork charter on every look x five eyes (blue, green, dark brown, grey, an amber eye with a slit pupil) at 512 px: the iris rectangle is byte for
     byte the picture WITHOUT the effect layer and the graded disc (T1, T6: 0), the pupil grown by 0.01 R is clear (T2), the visible share is 1 (T3), the
     text log is empty (T7), no hearts (T12), the iris is at least 22 percent of the canvas width (T18), the black share is measured (T4); and with the
     customer's words (T7) and on the two other canvases
  4. determinism and the seed: the same eye twice gives the same bytes, another eye another picture, the seed is the eye id and the plan's seed key and
     nothing else (not the names, not the canvas size), a 4096 px master reduced to 1024 is the 1024 px preview drawn finer
  5. the contract and the engine path: resolve, preview (watermark), tiles, the dispatcher, the plan of the master (make_plan, the cost key, capacity at the
     slow factor), the master's own call (a 4096 px preview with the self check) and the guards of render()
  6. /api/compose: a batch of tiles for one eye holds the five (480 px, the engine's pictures with the preview watermark), a single preview of each at
     1024 px; an eye that fails the lid rule keeps them (advisory) while the hard styles are held; the admin laboratory draws them
  7. several irises: Nebula and Supernova draw round two irises on one canvas with the same code (the pair and family styles take them over)
  8. the words and the pictures of the pages: the four languages of the picker's line for each look, the tile images
No network, no image model, no real eye in the repository (the eyes are procedural: synth_iris).
    python test_lumen.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure. Run by suites/run_main.sh as v3lumen."""
import ast
import atexit
import base64
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import unittest.mock as mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
FAMILY = os.path.join(API, "_lib", "styles", "lumen")
SINGLES = os.path.join(API, "_lib", "styles", "singles")
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3lumen_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
STORE = os.path.join(TMP, "store")
os.makedirs(STORE)
os.environ.update({"PYTHONIOENCODING": "utf-8", "SNAPEYES_TICKET_SECRET": "lumen-ticket-secret-for-tests-0123456789abcdef",
                   "SNAPEYES_ADMIN_SECRET": "lumen-admin-secret-for-tests-0123456789abcdef0123", "STORE_LOCAL_DIR": STORE,
                   "STYLE_PLATE_CACHE": os.path.join(TMP, "cache")})
sys.path.insert(0, API)
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import PIL  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
import lumen_cases as LC  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
import _lib.styles as ST  # noqa: E402
from _lib.styles import core as C, selfcheck as SCK, pupil as PU, seeds as SD, costs as CO, eye as EYE, steps as STP  # noqa: E402
from _lib.styles import lumen as LU  # noqa: E402
from _lib.styles.singles import kit as K  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
LUMEN = {"solo.supernova": "stardust", "solo.nebula": "nebula", "solo.sparks": "sparks", "solo.halo": "halo", "solo.aurora": "aurora"}
NAMES = {"solo.supernova": "Supernova", "solo.nebula": "Nebula", "solo.sparks": "Sparks", "solo.halo": "Halo", "solo.aurora": "Aurora"}
SLUGS = {"solo.supernova": "supernova", "solo.nebula": "nebula", "solo.sparks": "sparks", "solo.halo": "halo", "solo.aurora": "aurora"}
SIX = ["solo.clean", "solo.powder", "solo.universe", "solo.splash", "solo.gold", "solo.radiance"]
GOLD = json.load(open(os.path.join(HERE, "data", "lumen_goldens.json"), encoding="utf-8"))
G = GOLD["cases"]
MACHINE_SAME = GOLD["machine"]["numpy"] == np.__version__ and GOLD["machine"]["pillow"] == PIL.__version__
NOTE = "" if MACHINE_SAME else f" (numpy/Pillow differ from the recording {GOLD['machine']}: record again with record_goldens_lumen.py on this machine class)"


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
FILES = sorted(f for f in os.listdir(FAMILY) if f.endswith(".py"))
check("the family has its files: the contract, the shared pieces and one module per look", FILES == ["__init__.py", "aurora.py", "common.py", "halo.py", "nebula.py", "sparks.py", "stardust.py"], FILES)
mods = [os.path.join(FAMILY, f) for f in FILES]
src_all = "".join(read(m) for m in mods)
check("every module has the __future__ import (Python 3.12 is Vercel's default) and parses as 3.12",
      all(re.search(r"^from __future__ import annotations\r?$", read(m), re.M) and ast.parse(read(m), feature_version=(3, 12)) for m in mods), FILES)
check("no module holds a dash, a Windows or scratch path, a secret name, a thread setting or a path read at run time",
      not re.search(DASH, src_all) and not re.search(r"C:\\|scratchpad|AppData|wave-[a-z0-9]+|GEMINI_API_KEY|SERVICE_KEY|OMP_NUM_THREADS|sys\.path", src_all),
      re.findall(r"C:\\|scratchpad|wave-[a-z0-9]+|GEMINI_API_KEY|OMP_NUM_THREADS|sys\.path", src_all)[:5])
INVISIBLE = re.compile("[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u00ad\u061c\u180e\u200b-\u200f\u2028-\u202e\u2060-\u206f\ufeff\ufff9-\ufffb]")
check("no module holds a raw invisible, control or bidirectional character", not any(INVISIBLE.search(read(m)) for m in mods))


def growers(path):
    """Names assigned at module level to a dict, list or set that could grow with the work done (a cache keyed by the eye); the constant tables of the
    looks (their parameters, the geometry) are allowed by name."""
    out = []
    for node in ast.parse(read(path)).body:
        targets = node.targets if isinstance(node, ast.Assign) else ([node.target] if isinstance(node, ast.AnnAssign) else [])
        v = getattr(node, "value", None)
        if v is None:
            continue
        if isinstance(v, (ast.Dict, ast.List, ast.Set, ast.DictComp, ast.ListComp, ast.SetComp)) or (
                isinstance(v, ast.Call) and getattr(v.func, "id", getattr(v.func, "attr", "")) in ("dict", "list", "set", "defaultdict", "OrderedDict", "deque")):
            out += [t.id for t in targets if isinstance(t, ast.Name) and t.id not in ("NP", "SP", "HP", "AP", "GEOM")]
    return out


check("no module keeps a module level dict, list or set that can grow (the looks' parameter tables and the geometry aside): a warm instance cannot leak",
      not any(growers(m) for m in mods), {os.path.basename(m): growers(m) for m in mods if growers(m)})
check("importing a look reads no file, opens no socket, writes nothing and calls no model: no open(), os.environ, subprocess, socket, plate, atlas or chip",
      not re.search(r"\bopen\(|os\.environ|subprocess|socket|np\.load|\.save\(|plates\.|atlas\(|\.chips\(|gemini|urlopen|requests", src_all, re.I),
      re.findall(r"\bopen\(|os\.environ|subprocess|socket|np\.load|\.save\(|plates\.|atlas\(|gemini", src_all, re.I)[:5])
ID_RE = re.compile(r"(?<![\w.])(" + "|".join(re.escape(i) for i in CT.ids()) + r")(?![\w])")
check("no module writes a style id of the registry (the legacy id of the old Supernova among them: the design of the new one is 'stardust')",
      not ID_RE.search(src_all), ID_RE.findall(src_all)[:5])
LUMEN_IDS = [i for i in CT.ids() if (CT.ENGINE[i]["engine"] or {}).get("module") == "lumen"]
check("the registry names exactly the five styles of the family, each with its design, in the picker's order 7 to 11 after the six singles of release 1",
      {i: CT.ENGINE[i]["engine"]["design"] for i in LUMEN_IDS} == LUMEN and [CT.STYLES[i]["tile_order"] for i in LUMEN_IDS] == [7, 8, 9, 10, 11]
      and sorted(LU.DESIGNS) == sorted(LUMEN.values()), {i: CT.ENGINE[i]["engine"] for i in LUMEN_IDS})
check("each is a style of one eye of the solo group: its name, its slug (Supernova shares the old legacy Supernova's, which the registry allows for one name), "
      "one layout, the art price class, no accent, no pick (the recommended tile stays the release 1 table), a 4096 px working copy",
      all(CT.STYLES[i]["name"] == NAMES[i] and CT.STYLES[i]["slug"] == SLUGS[i] and CT.STYLES[i]["group"] == "solo" and CT.STYLES[i]["eyes"] == [1, 1]
          and CT.STYLES[i]["layouts"] == {"1": ["single"]} and CT.STYLES[i]["legacy"] == 0 and CT.STYLES[i]["price_class"] == "art" and CT.STYLES[i]["pick"] == []
          and CT.STYLES[i]["reason"] == {} and CT.STYLES[i]["accent"] == [] and CT.STYLES[i]["work_side"] == {"1": 4096} for i in LUMEN_IDS)
      and CT.STYLES["supernova"]["slug"] == "supernova" and CT.STYLES["supernova"]["name"] == "Supernova", "")
check("the stage is preview (a ceiling: the admin page can lower it, never raise it; raising it is a reviewed change of the registry) and the gate policy is "
      "advisory with the lid rule, as Radiance's: a failing eye warns, it is never refused for these looks",
      all(CT.STYLES[i]["stage"] == "preview" and CT.STYLES[i]["stage_by_eyes"] == {} and CT.STYLES[i]["gate"] == "advisory" and CT.ENGINE[i]["gate_rules"] == "lid"
          for i in LUMEN_IDS) and CT.STYLES["solo.radiance"]["gate"] == "advisory", "")
check("the engine entries: the family lumen, the three canvases of the family (the square first), no plate, no atlas, one art step, no fill",
      all(CT.ENGINE[i]["canvases"] == list(LU.FORMATS) and CT.ENGINE[i]["plates"] == [] and CT.ENGINE[i]["atlas"] == [] and CT.ENGINE[i]["steps"] == {}
          and CT.ENGINE[i]["fill_side"] == 0 and CT.ENGINE[i]["design_by_eyes"] == {} for i in LUMEN_IDS), "")
check("the family is an engine family of the style package: listed, built, and the dispatch loads it", "lumen" in ST.ENGINE_FAMILIES and CT.engine_built("lumen")
      and ST.family("lumen").__name__ == "_lib.styles.lumen")
check("the geometry has a row per look and canvas, and every iris is at least 22 percent of the canvas width (T18 read for a single, with and without words)",
      set(LU.GEOM) == set(LU.DESIGNS) and all(set(LU.GEOM[d]["r"]) == set(LU.FORMATS) == set(LU.GEOM[d]["cy"]) for d in LU.GEOM)
      and all(2 * LU.frame_for(d, f, 1024, t).R / LU.frame_for(d, f, 1024, t).W >= 0.22 for d in LU.DESIGNS for f in LU.FORMATS for t in (False, True)), "")
check("every cost row the family needs exists: a master row and a preview row of one eye for each look (a style the table cannot price is never sold)",
      all(CO.known(f"lumen.{d}", 1) and 1 in CO.PREVIEW[f"lumen.{d}"] for d in LU.DESIGNS) and all(CO.cost_key(CT.engine_for(i, 1)) == f"lumen.{LUMEN[i]}" for i in LUMEN_IDS))
check("the catalogue: a customer may preview each (and the admin), nobody can order one, and the picker lists them after the six of release 1, in their order; "
      "none is the recommended tile",
      all(CT.previewable(i, 1) and CT.previewable(i, 1, admin=True) and not CT.orderable(i, 1, strict=False) and CT.stage_of(i, 1) == "preview" for i in LUMEN_IDS)
      and [t["id"] for t in CT.tiles_for(1)][-5:] == LUMEN_IDS and all(CT.why_unavailable(i, 1) is None for i in LUMEN_IDS)
      and CT.tile_list(1)["pick"] not in LUMEN_IDS and not any(CT.previewable(i, 2) for i in LUMEN_IDS), [t["id"] for t in CT.tiles_for(1)])
SINGLES_FILES = sorted(f for f in os.listdir(SINGLES) if f.endswith(".py"))
check("the singles family is untouched: its seven files and its six registry styles (the light family is a family of its own, so the singles goldens are the old ones)",
      SINGLES_FILES == ["__init__.py", "elements.py", "gold.py", "kit.py", "powder.py", "radiance.py", "splash.py"]
      and sorted(i for i in CT.ids() if (CT.ENGINE[i]["engine"] or {}).get("module") == "singles") == sorted(SIX[:2] + SIX[3:] + ["solo.elements"]), SINGLES_FILES)

# ============================================================================================ 2. the golden replay
section("2. the golden replay")
FIX = {n: SI.png_bytes(n) for n in LC.FIXTURE_BASE}
check("the three fixtures of the replay are the very bytes of the recording", all(hashlib.sha256(FIX[n]).hexdigest() == GOLD["fixtures"][n] for n in FIX))
print(f"   (recorded on {GOLD['machine']}; running on numpy {np.__version__}, Pillow {PIL.__version__})", flush=True)
ALL = LC.cases()
check("the recording holds every case of lumen_cases.py and nothing else (50: 5 looks x 3 eyes x 2 sizes, 5 masters, 15 with words or another canvas)",
      sorted(G) == sorted(c["key"] for c in ALL) and len(G) == 50, sorted(set(G) ^ {c["key"] for c in ALL})[:5])
IRISES = {}
t0 = time.time()


def rec_case(c):
    out = LC.render_case(LU.render, C.Iris, FIX, c, IRISES)
    if c["size"] >= 2048:
        IRISES.clear()
    return out


for design in LU.DESIGNS:
    for size in (512, 1024):
        rows = [(c, rec_case(c)) for c in ALL if c["design"] == design and c["size"] == size and c["fmt"] == "1:1" and not (c["names"] or c["date"])]
        bad = [(c["key"], [k for k in ("sha", "seed", "facts", "w", "h", "cls") if r[k] != G[c["key"]][k]]) for c, r in rows]
        bad = [b for b in bad if b[1]]
        check(f"{design} at {size} px: the three eye classes give the recorded pictures, seeds and facts, byte for byte", len(rows) == 3 and not bad, str(bad) + NOTE)
    rows = [(c, rec_case(c)) for c in ALL if c["design"] == design and c["size"] == 512 and (c["names"] or c["date"])]
    bad = [(c["key"], [k for k in ("sha", "seed", "facts", "w", "h", "cls") if r[k] != G[c["key"]][k]]) for c, r in rows]
    bad = [b for b in bad if b[1]]
    check(f"{design}: the 4:5 canvas with names, the wallpaper with a date and the square with both equal the recorded pictures", len(rows) == 3 and not bad, str(bad) + NOTE)
    rows = [(c, rec_case(c)) for c in ALL if c["design"] == design and c["size"] == 4096]
    bad = [(c["key"], [k for k in ("sha", "seed", "facts", "w", "h", "cls") if r[k] != G[c["key"]][k]]) for c, r in rows]
    bad = [b for b in bad if b[1]]
    check(f"{design} at 4096 px (a master) equals the recorded picture, byte for byte", len(rows) == 1 and not bad, str(bad) + NOTE)
print(f"   (replayed in {time.time() - t0:.0f} s)", flush=True)
c0 = [c for c in ALL if c["design"] == "halo" and c["size"] == 512][0]
with mock.patch.object(K, "F3_SPAN", K.F3_SPAN * 1.02):
    moved = LC.render_case(LU.render, C.Iris, FIX, c0, {})
check("the replay can fail: a two percent change of the iris feather moves the hash of Halo", moved["sha"] != G[c0["key"]]["sha"])

# ============================================================================================ 3. the artwork charter
section("3. the artwork charter on every look x five eyes at 512 px, with words and on the other canvases")
EYES = ("blue_round", "green_round", "dark_brown_round", "grey_round", "amber_slit")
IR = {n: C.Iris(SI.png_bytes(n), n) for n in EYES}


def effect_free(design, iris, fmt, size, names="", date="", style=None):
    """The same frame and seed without the effect layer: what the picture is with the look taken away."""
    key = LU.seed_key(style or LU._style_of(design), design)
    from _lib.styles import text as TX
    return LU.render_single(None, iris, design, fmt, size, TX.lockup(names), TX.clean(date), seed=SD.seed_for_key([iris.eye_id], key), pv=key["pv"])


def charter(r, rc, customer=("", "")):
    a = np.asarray(r.img.convert("RGB"))
    c = np.asarray(rc.img.convert("RGB"))
    d = r.d
    t = d.g.shape[0]
    ax = (np.arange(t) + 0.5) - t / 2.0
    rho = np.hypot(ax[None, :], ax[:, None]) / d.R
    wa = a[d.y0:d.y0 + t, d.x0:d.x0 + t].astype(np.int16)
    wc = c[d.y0:d.y0 + t, d.x0:d.x0 + t].astype(np.int16)
    diff = np.abs(wa - wc).max(-1)
    gd = np.abs(wa - d.g.astype(np.int16)).max(-1)
    full = rho <= 0.974
    rep = SCK.run(a, [d], text_log=r.log, customer=list(customer), ids=["solo", r.info["design"], "single"])
    pm = PU.mask(PU.analyse(d.g), t, d.R, 0.0)
    vis = SCK.zone_mask(d, 0.95)
    t2 = SCK.t2_pupil_clearance([pm], [vis], None, [d.R])
    grown = SCK.dilate(pm, int(np.ceil(0.01 * d.R))) & vis
    share = float(((gd <= 1) & vis).sum()) / float(vis.sum())
    return {"identical": int((diff[full] > 0).sum()) == 0, "graded": int((gd[full] > 0).sum()) == 0, "t1": rep["checks"]["t1"]["ok"] and rep["checks"]["t1"]["max_abs_diff"] == 0,
            "t6": rep["checks"]["t6"]["count"] == 0, "t12": rep["checks"]["t12"]["ok"], "t7": rep["checks"]["t7"]["ok"] and (customer != ("", "") or rep["checks"]["t7"]["drawn"] == 0),
            "t2": t2["ok"] and int((diff[grown] > 0).sum()) == 0, "t3": share >= 1.0, "t18": 2 * d.R / a.shape[1] >= 0.22}, SCK.black_share(a)


bad, blacks = {}, {}
for design in LU.DESIGNS:
    for n in EYES:
        res, bl = charter(LU.render(design, IR[n], "1:1", 512), effect_free(design, IR[n], "1:1", 512))
        blacks[(design, n)] = round(bl, 3)
        for k, v in res.items():
            if not v:
                bad.setdefault(k, []).append(f"{design}.{n}")
for k, label in (("identical", "the iris rectangle (alpha 1, r <= 0.974 R) is byte for byte the picture without the effect layer"),
                 ("graded", "the iris rectangle is byte for byte the graded disc of the eye"), ("t1", "T1: the iris is the graded disc (0 of 255)"),
                 ("t6", "T6: no matter on the iris (0 pixels)"), ("t2", "T2: the pupil grown by 0.01 R is clear and identical to the effect free picture"),
                 ("t3", "T3: the visible share of the disc is 1.0"), ("t7", "T7: the text log is empty when no text is asked"), ("t12", "T12: no hearts"),
                 ("t18", "T18: the iris is at least 22 percent of the canvas width")):
    check(f"{label}: {len(LU.DESIGNS)} looks x {len(EYES)} eyes", k not in bad, bad.get(k))
print("   T4, the black share (luma under 12) per look, measured and not bounded (as Radiance's): " +
      ", ".join(f"{d} {min(v for (dd, _), v in blacks.items() if dd == d)} to {max(v for (dd, _), v in blacks.items() if dd == d)}" for d in LU.DESIGNS), flush=True)
check("T4 measured: every look leaves a dark ground (black share at least 0.03) and none is a black picture (at most 0.80)", all(0.03 <= v <= 0.80 for v in blacks.values()), blacks)
ok_w, why_w = True, []
for design in LU.DESIGNS:
    res, _ = charter(LU.render(design, IR["blue_round"], "1:1", 512, "Anna Max", "12 MAY 2026"), effect_free(design, IR["blue_round"], "1:1", 512, "Anna Max", "12 MAY 2026"),
                     ("Anna Max", "12 MAY 2026"))
    if not all(res.values()):
        ok_w = False
        why_w.append((design, res))
check("with the customer's name and date: T1, T6, T7 (only the customer's words are drawn), T12 and the identical iris hold for every look", ok_w, why_w)
ok_c, why_c = True, []
for design in LU.DESIGNS:
    for fmt in ("4:5", "9:19.5"):
        r = LU.render(design, IR["grey_round"], fmt, 256)
        res, _ = charter(r, effect_free(design, IR["grey_round"], fmt, 256))
        if not (res["identical"] and res["graded"] and res["t1"] and res["t6"] and res["t18"]) or r.img.size != (r.frame.W, r.frame.H):
            ok_c = False
            why_c.append((design, fmt, res))
check("on the 4:5 canvas and the phone wallpaper (9:19.5) every look draws with the iris identical, at least 22 percent of the width", ok_c, why_c)

# ============================================================================================ 4. determinism and the seed
section("4. determinism, the seed and the size")
for design in LU.DESIGNS:
    a = hashlib.sha256(np.asarray(LU.render(design, IR["blue_round"], "1:1", 256).img).tobytes()).hexdigest()
    b = hashlib.sha256(np.asarray(LU.render(design, IR["blue_round"], "1:1", 256).img).tobytes()).hexdigest()
    c2 = hashlib.sha256(np.asarray(LU.render(design, IR["green_round"], "1:1", 256).img).tobytes()).hexdigest()
    check(f"{design}: the same eye twice is the same bytes, another eye another picture", a == b and a != c2)
key_n = LU.seed_key("solo.nebula", "nebula")
check("the seed is the eye id and the plan's seed key (the style, the design, the options, the plates version): the same at 512 and at 4096 px, with or without names, "
      "and another style key or another eye gives another seed",
      LU.render("nebula", IR["blue_round"], "1:1", 256).info["seed"] == LU.render("nebula", IR["blue_round"], "4:5", 512, "Anna", "1 May").info["seed"]
      == SD.seed_for_key([IR["blue_round"].eye_id], key_n)
      and SD.seed_for_key([IR["blue_round"].eye_id], dict(key_n, style="solo.halo")) != SD.seed_for_key([IR["blue_round"].eye_id], key_n)
      and LU.render("nebula", IR["green_round"], "1:1", 256).info["seed"] != SD.seed_for_key([IR["blue_round"].eye_id], key_n))
for design in LU.DESIGNS:
    big = LU.render(design, IR["dark_brown_round"], "1:1", 1024).img.convert("RGB").resize((256, 256), Image.BOX)
    small = LU.render(design, IR["dark_brown_round"], "1:1", 256).img.convert("RGB")
    md = float(np.abs(np.asarray(big, np.float32) - np.asarray(small, np.float32)).mean())
    check(f"{design}: a 1024 px picture reduced to 256 px is the 256 px picture (mean difference {md:.2f} of 255, under 9): a master is its preview drawn finer", md < 9.0, md)

# ============================================================================================ 5. the contract and the engine path
section("5. the contract, the plan of the master, the master's own call, the guards")
eye_id = IR["blue_round"].eye_id
for sid, design in LUMEN.items():
    rp = ST.resolve({"style": sid, "eyes": 1, "eye_ids": [eye_id]}, [None])
    pv = ST.preview([IR["blue_round"]], {"style": sid, "eyes": 1}, size=512, check=True)
    ok = (rp["family"] == "lumen" and rp["design_used"] == design and rp["canvas"] == "1:1" and rp["plates"] == [] and rp["frozen"] == {} and rp["layout"] == "single"
          and rp["seed"] == str(SD.seed_for_key([eye_id], LU.seed_key(sid, design))) and rp["seed_key"]["style"] == sid
          and pv.design == design and str(pv.seed) == rp["seed"] and pv.log["plates"] == [] and pv.selfcheck["ok"] and pv.discs and len(pv.graded) == 1
          and np.array_equal(np.asarray(pv.img), np.asarray(LU.render(design, IR["blue_round"], "1:1", 512, key=LU.seed_key(sid, design)).img)))
    check(f"{sid}: resolve names the family, the design, the canvas and the seed of the picture; preview draws it with the run-time self check passing", ok,
          (rp.get("family"), rp.get("design_used"), pv.selfcheck))
r_none = ST.resolve({"style": "solo.halo", "eyes": 1}, [None])
check("resolve without an eye id knows no seed (the plan freezes the eye id; never a seed of another eye)", r_none["seed"] is None and r_none["eye_ids"] == [])
pv_w = ST.preview([IR["grey_round"]], {"style": "solo.sparks", "eyes": 1}, size=512, watermark=True)
pv_c = ST.preview([IR["grey_round"]], {"style": "solo.sparks", "eyes": 1}, size=512)
check("the dispatcher's watermark makes the free preview of a look (not the clean picture; the clean one is the family's render)",
      not np.array_equal(np.asarray(pv_w.img), np.asarray(pv_c.img)) and pv_w.img.size == pv_c.img.size)
tl = ST.tiles([IR["grey_round"]], list(LUMEN), {"eyes": 1, "names": [], "date": ""}, size=480)
check("tiles: the five looks on one eye preparation, each the picture its own preview makes", list(tl) == list(LUMEN)
      and all(np.array_equal(np.asarray(tl[s].img), np.asarray(ST.preview([IR["grey_round"]], {"style": s, "eyes": 1}, size=480).img)) for s in ("solo.halo", "solo.aurora")))
plans = {}
for sid, design in LUMEN.items():
    plans[sid] = STP.make_plan({"style": sid, "layout": "single", "eyes": 1, "opts": {}}, [{"eye_id": eye_id, "profile": None}], factor=1.6)
cap = {s: STP.capacity(p, 1.6) for s, p in plans.items()}
check("the master's plan of each: the family lumen, the design, one art step, the cost key of the table, the capacity fits one call at the default slow factor (time and memory), "
      "the engine version and the registry hash recorded",
      all(p["family"] == "lumen" and p["design_used"] == LUMEN[s] and p["cost_key"] == f"lumen.{LUMEN[s]}" and [x["kind"] for x in p["steps"]] == ["art"]
          and cap[s]["ok"] and cap[s]["why"] is None and p["engine_v"] == ST.ENGINE_V and p["reg"] == CT.registry_hash() and p["plates"] is None for s, p in plans.items()),
      {s: (c["ok"], c["need_s"], c["est_mb"]) for s, c in cap.items()})
print("   the master estimates at the slow factor 1.6: " + ", ".join(f"{NAMES[s]} {c['need_s']} s / {c['est_mb']} MB" for s, c in cap.items()), flush=True)
check("the plan is stable: made twice for the same eye it is the same plan (plan8), and another eye makes another one",
      all(STP.make_plan({"style": s, "layout": "single", "eyes": 1, "opts": {}}, [{"eye_id": eye_id, "profile": None}], factor=1.6)["plan8"] == p["plan8"] for s, p in plans.items())
      and STP.make_plan({"style": "solo.nebula", "layout": "single", "eyes": 1, "opts": {}}, [{"eye_id": IR["green_round"].eye_id, "profile": None}], factor=1.6)["plan8"] != plans["solo.nebula"]["plan8"])
big_eye = C.Iris(SI.png_bytes("blue_round", side=2048), "m", max_side=4096, eye_id=eye_id)
t_m = time.time()
pv_m = ST.preview([big_eye], {"style": "solo.nebula", "layout": "single", "eyes": 1, "canvas": plans["solo.nebula"]["canvas"], "names": [], "date": "",
                              "opts": {}, "pv": plans["solo.nebula"]["pv"], "frozen": None}, size=4096, watermark=False, check=True)
t_m = time.time() - t_m
check(f"the master's own call (the step runner's: a 4096 px preview, clean, with the self check) draws the planned seed and passes the self check ({t_m:.1f} s here)",
      pv_m.img.size == (4096, 4096) and pv_m.selfcheck["ok"] and str(pv_m.seed) == plans["solo.nebula"]["seed"] and pv_m.selfcheck["checks"]["t1"]["max_abs_diff"] == 0,
      (pv_m.selfcheck, pv_m.seed, plans["solo.nebula"]["seed"]))
check("the guards of render(): an unknown design is a KeyError, a canvas the family does not draw and a size out of range are ValueErrors; preview takes one eye and a style of its own family only",
      raises(lambda: LU.render("nope", IR["blue_round"]), KeyError) is not False and isinstance(raises(lambda: LU.render("halo", IR["blue_round"], "3:2", 256), ValueError), ValueError)
      and isinstance(raises(lambda: LU.render("halo", IR["blue_round"], "1:1", 5000), ValueError), ValueError)
      and isinstance(raises(lambda: LU.render("halo", IR["blue_round"], "1:1", 32), ValueError), ValueError)
      and isinstance(raises(lambda: LU.preview([IR["blue_round"]] * 2, {"style": "solo.halo", "eyes": 1}), ValueError), ValueError)
      and isinstance(raises(lambda: LU.preview([IR["blue_round"]], {"style": "solo.radiance", "eyes": 1}), ValueError), ValueError))

# ============================================================================================ 6. /api/compose and the laboratory
section("6. /api/compose: the tiles and the previews of the looks; the gate; the admin laboratory")
spec_ = importlib.util.spec_from_file_location("compose", os.path.join(API, "compose.py"))
CMP = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(CMP)
EVENTS = []
E.record = lambda kind, **f: EVENTS.append((kind, dict(f))) or False


def sealed_of(name):
    jpeg = SI.jpeg_bytes(name)
    prof = EYE.profile_of_bytes(jpeg, pad=1.12)
    return jpeg, prof, P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=prof)["sealed"]


jpeg_b, prof_b, sealed_b = sealed_of("blue_round")
r_list = CMP.compose({"sealed": [sealed_b], "styles": [], "pad": 1.12})
tiles_ = {t["id"]: t for t in r_list["tiles"]}
check("the tile list of one eye holds the five looks at preview, available, with the advisory policy and the lid rule, after the six of release 1 (none is the pick)",
      all(i in tiles_ and tiles_[i]["stage"] == "preview" and tiles_[i]["available"] and tiles_[i]["gate"] == "advisory" and tiles_[i]["rule"] == "lid"
          and tiles_[i]["name"] == NAMES[i] and tiles_[i]["slug"] == SLUGS[i] and not tiles_[i]["pick"] for i in LUMEN)
      and [t["id"] for t in r_list["tiles"] if t["id"] in LUMEN] == list(LUMEN), [(t["id"], t["stage"], t["available"]) for t in r_list["tiles"]])
meta_b = P.unseal_full(sealed_b)[1]
r_b = CMP.compose({"sealed": [sealed_b], "styles": ["solo.supernova", "solo.nebula"], "pad": 1.12})
r_b2 = CMP.compose({"sealed": [sealed_b], "styles": ["solo.sparks", "solo.halo", "solo.aurora"], "pad": 1.12})
got = {t["id"]: t for t in r_b["tiles"] + r_b2["tiles"] if t.get("image")}
exp_t = {s: L.pil_to_b64(ST.preview([C.Iris(jpeg_b, "compose", max_side=2048, eye_id=meta_b["eye_id"])], {"style": s, "layout": "single", "eyes": 1, "canvas": "1:1",
                                                                                                              "names": "", "date": ""}, size=480, watermark=True).img, "JPEG", 90)
         for s in LUMEN}
check("a batch of tiles draws each look at 480 px through the engine: the picture is the engine's preview of the sealed eye with the preview watermark, as every tile",
      sorted(got) == sorted(LUMEN) and all((got[s]["width"], got[s]["height"]) == (480, 480) and got[s]["design_used"] == LUMEN[s] for s in LUMEN)
      and all(got[s]["image"] == exp_t[s] for s in LUMEN), {s: (got.get(s, {}).get("width"), got.get(s, {}).get("image") == exp_t[s]) for s in LUMEN})
r_one = {s: CMP.compose({"sealed": [sealed_b], "style": s, "pad": 1.12, "lang": "en"}) for s in ("solo.halo", "solo.supernova")}
check("a single preview of a look is the 1024 px picture of the engine with the watermark, its plan8 and canvas, and the compose event names the style",
      all(r["ok"] and r["style"] == s and (r["width"], r["height"]) == (1024, 1024) and r["design_used"] == LUMEN[s] and r["canvas"] == "1:1" and len(r["plan8"]) >= 8
          and r["engine"] == {"v": ST.ENGINE_V, "reg": CT.registry_hash(), "pv": CT.PLATES_VERSION} for s, r in r_one.items())
      and any(e[0] == "compose" and e[1].get("style") == "solo.halo" for e in EVENTS), {s: (r.get("style"), r.get("width")) for s, r in r_one.items()})
check("the single preview's plan8 is the plan the master would make of the same eye (checkout compares the two)",
      r_one["solo.halo"]["plan8"] == STP.make_plan({"style": "solo.halo", "layout": "single", "eyes": 1, "opts": {}}, [{"eye_id": meta_b["eye_id"], "profile": None}])["plan8"],
      (r_one["solo.halo"]["plan8"],))
jpeg_l, prof_l, sealed_l = sealed_of("blue_lid")
r_lid = CMP.compose({"sealed": [sealed_l], "styles": [], "pad": 1.12})
t_lid = {t["id"]: t for t in r_lid["tiles"]}
check("an eye that fails the lid rule (the gate's verdict, sealed with its profile): the five looks stay available (advisory: a warning, never a refusal) while the hard "
      "styles Clean Iris and Celestial Gold are held back with why gate",
      prof_l.rec["gate"]["lid"]["ok"] is False and all(t_lid[i]["available"] and t_lid[i]["why"] is None for i in LUMEN)
      and not t_lid["solo.clean"]["available"] and t_lid["solo.clean"]["why"] == "gate" and not t_lid["solo.gold"]["available"], {i: (t_lid[i]["available"], t_lid[i]["why"]) for i in t_lid})
from _lib import ops  # noqa: E402
lst = ops.a_styles_lab({}, "t")
rows_l = {r["id"]: r for r in lst["styles"] if r["module"] == "lumen"}
lab_one = ops.a_styles_lab({"style": "solo.aurora", "eye": base64.b64encode(SI.png_bytes("grey_round")).decode("ascii"), "size": 480}, "t")
check("the admin laboratory lists the five looks with their stage, ceiling, canvases and no plate, and draws one with the self check",
      sorted(rows_l) == sorted(LUMEN) and all(r["ceiling"] == "preview" and r["canvases"] == list(LU.FORMATS) and r["plates"] == [] for r in rows_l.values())
      and lab_one["ok"] and lab_one["selfcheck"]["checks"]["t1"]["ok"], {k: v for k, v in lab_one.items() if k not in ("image",)} if isinstance(lab_one, dict) else lab_one)

# ============================================================================================ 7. several irises
section("7. several irises: Nebula and Supernova draw round two irises on one canvas with the same code")


def group_canvas(fx, irises, centres, R_share, W, H, key_style):
    """A canvas of several irises the way a pair or family style would make it (the discs placed, the effect drawn ONCE over all of them, every iris
    pasted last with the F3 feather): the effect module is the family's own, unchanged."""
    S_ = min(W, H)
    ds, d3s = [], []
    for k_, (ir, (fx_, fy_)) in enumerate(zip(irises, centres)):
        d = C.place_disc(ir, fx_ * W, fy_ * H, R_share * S_, k_)
        d.g = K.finish_grade(d.g, d.R, True)
        ds.append(d)
        d3s.append(K.make_disc3(d))

    class Fr:
        pass
    fr = Fr()
    fr.W, fr.H, fr.S, fr.wall, fr.fmt, fr.key, fr.text_box = W, H, S_, False, "3:2", "test/group", None
    ctx = K.MCtx(fr, ds[0], irises[0], "group", None, seed=SD.seed_for_key([ir.eye_id for ir in irises], LU.seed_key(key_style, "group")), pv=1)
    ctx.discs, ctx.irises = ds, irises
    cv = C.canvas(W, H, "#000000")
    fx(cv, ctx)
    K.tone_map_bands(cv)
    img8 = C.dither_quantize(cv, ctx.seed)
    for d3 in d3s:
        K.paste_iris(img8, d3)
    return img8, ds, ctx


from _lib.styles.lumen import nebula as NB, stardust as SDU  # noqa: E402
for name, fx in (("Nebula", NB.fx_nebula), ("Supernova", SDU.fx_stardust)):
    img8, ds, ctx_g = group_canvas(fx, [IR["blue_round"], IR["dark_brown_round"]], [(0.32, 0.5), (0.68, 0.5)], 0.20, 720, 480, "solo.nebula")
    t1 = SCK.t1_iris_integrity(img8, ds)
    lit = [float(img8[int(d.cy - 1.25 * d.R), int(d.cx)].mean()) for d in ds]
    check(f"{name}: a pair on one canvas keeps both irises byte for byte their graded discs (T1 max {t1['max_abs_diff']}), and light is drawn round each of them",
          t1["ok"] and t1["max_abs_diff"] == 0 and all(v > 1.0 for v in lit), (t1, lit))
nb_log = group_canvas(NB.fx_nebula, [IR["blue_round"], IR["green_round"], IR["grey_round"]], [(0.2, 0.5), (0.5, 0.5), (0.8, 0.5)], 0.14, 900, 450, "solo.nebula")[2].log
check("Nebula takes each eye's own colours round its own disc (one partner hue per eye of a family of three)", len(nb_log["nebula"]["partner_hue"]) == 3, nb_log)

# ============================================================================================ 8. the words and the pictures of the pages
section("8. the words of the picker and the tile images")
copies = {"en": read(os.path.join(REPO, "src", "try", "copy.ts")), "lt": read(os.path.join(REPO, "src", "try", "copy.lt.ts")),
          "hu": read(os.path.join(REPO, "src", "try", "copy.hu.ts"))}
keys = [f"line.{i.replace('.', '_')}" for i in LUMEN]
lines = {lang: {k: re.findall(r"'" + re.escape(k) + r"':\s*'([^']+)'", src) for k in keys} for lang, src in copies.items()}
check("the picker's one line of each look is in English and German (copy.ts: two dictionaries), Lithuanian and Hungarian, one sentence each, no dash",
      all(len(lines["en"][k]) == 2 for k in keys) and all(len(lines[l][k]) == 1 for l in ("lt", "hu") for k in keys)
      and not any(re.search(DASH, s) for l in lines.values() for v in l.values() for s in v)
      and all(0 < len(s) <= 70 for l in lines.values() for v in l.values() for s in v), lines)
for sid in LUMEN:
    paths = [os.path.join(REPO, "public", "assets", "atelier", f"style-{SLUGS[sid]}-{w}.webp") for w in (480, 800)]
    dims = []
    for p_, w in zip(paths, (480, 800)):
        try:
            with Image.open(p_) as im:
                dims.append((im.format, im.size, os.path.getsize(p_)))
        except OSError:
            dims.append(None)
    check(f"{NAMES[sid]}: its tile images exist at 480 and 800 px, square WEBP files under 150 kB (scripts/make_style_tiles.py on the owner's own eye)",
          all(d_ and d_[0] == "WEBP" and d_[1] == (w, w) and d_[2] < 150_000 for d_, w in zip(dims, (480, 800))), dims)

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
