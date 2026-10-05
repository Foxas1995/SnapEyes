# -*- coding: utf-8 -*-
"""WP5A and WP5B of the v3 engine work: the singles family (Clean Iris, Powder Burst, Splash, Elements, Radiance, Celestial Gold variant A) ported
verbatim into api/_lib/styles/singles (step A), then re-seeded once from the eye id (step B). Test I6 (goldens) for the family, the singles share of
I7 (T1, T4, T6, T7, T12) and the places the family is reached from: the style package's contract, /api/compose for a style a customer may see, and
the admin laboratory (styles_lab).

  1. the family in the repository: its files, the rules of every module, the registry and the family agree, no stage was raised
  2. the golden replay: the SHA-256 of the pictures this code makes (record_goldens_repo.py, step B: the seed from the eye id and the plan's seed key)
     for every design x three synthetic eye classes x 512, 1024 and 4096 px, the other two canvases and the text lockup; the plate picks and the seeds
     equal too; the replay can fail. And the STEP A recording (the scratch prototype's own pictures, data/stepA/) replayed with the old seed (opts
     seed_mode legacy): byte for byte equal, which proves that the seed is the ONLY thing step B changed. The 4096 px pictures of the three plate
     styles draw from 4K plates that live in private storage: they are replayed only with the scratch tree (LOCAL lines)
  3. the hard rules on every picture of the replay: the iris is the graded iris byte for byte (T1, T6), the text log holds the customer's words only
     (T7), no hearts (T12), the black share of Powder Burst and Elements (T4), Clean's ground is pure black, the veil of Powder Burst
  4. determinism, bounded caches, the guards of render()
  5. the contract (resolve, preview, tiles, the watermark) and plates that are missing (never another plate)
  6. /api/compose: a style a customer may see is drawn by the engine with the preview watermark; a laboratory style is not; the old styles are unchanged
  7. the admin laboratory: styles_lab behind the admin key
  8. the real calibration eyes (LOCAL: SNAPEYES_CALIB) and the port as the scratch plus its edits (LOCAL: SNAPEYES_SCRATCH_Y3)
  9. step B, the seed: made from the eye id and the plan's seed key and from nothing else, the plates a plan names are the plates the picture draws
     from, the plates version of the spec reaches every pick, what the plan freezes (the liquid of a splash) is what the preview and the master draw,
     the statistical rules (T1, T4, T6, T7, T12, the veil) hold over many seeds, the preview of /api/compose and the laboratory seed alike
No network, no image model, no real eye in the repository (the eyes are procedural: synth_iris). A golden is exact for this machine class and the pins
of requirements.txt; a mismatch elsewhere means recording again on the scratch code there, never changing the port.
    SNAPEYES_SCRATCH_Y3  the wave-y3 folder of the scratch tree (the 4K plates, the edit check); SNAPEYES_CALIB the calibration restorations' folder
    python test_goldens_singles.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3single."""
import ast
import base64
import gc
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
import unittest.mock as mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
FAMILY = os.path.join(API, "_lib", "styles", "singles")
STYLES = os.path.join(API, "_lib", "styles")
SCRATCH_Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or ""
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
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_SCRATCH_Y3", "SNAPEYES_CALIB"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3single_")
STORE = os.path.join(TMP, "store")
os.makedirs(STORE)
os.environ.update({"PYTHONIOENCODING": "utf-8", "SNAPEYES_TICKET_SECRET": "wp5a-ticket-secret-for-tests-0123456789abcdef",
                   "SNAPEYES_ADMIN_SECRET": "wp5a-admin-secret-for-tests-0123456789abcdef0123", "STORE_LOCAL_DIR": STORE,
                   "STYLE_PLATE_CACHE": os.path.join(TMP, "cache")})
sys.path.insert(0, API)
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import PIL  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402
import synth_iris as SI  # noqa: E402
import singles_cases as SC  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import store  # noqa: E402
import _lib.styles as ST  # noqa: E402
from _lib.styles import core as C, selfcheck as SCK, plates as PL, text as TX, costs as CO  # noqa: E402
from _lib.styles import seeds as SD, eye as EYE  # noqa: E402
from _lib.styles import singles as S  # noqa: E402
from _lib.styles.singles import kit as K  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
GOLD = json.load(open(os.path.join(HERE, "data", "singles_goldens.json"), encoding="utf-8"))
G = GOLD["cases"]
GOLD_A = json.load(open(os.path.join(HERE, "data", "stepA", "singles_goldens.json"), encoding="utf-8"))      # step A: the scratch prototype's own pictures
GA = GOLD_A["cases"]
MACHINE_SAME = GOLD["machine"]["numpy"] == np.__version__ and GOLD["machine"]["pillow"] == PIL.__version__
NOTE = "" if MACHINE_SAME else f" (numpy/Pillow differ from the recording {GOLD['machine']}: record again on the scratch code, do not change the port)"
FAMILY_FILES = sorted(f for f in os.listdir(FAMILY) if f.endswith(".py"))


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


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
SINGLES_STYLES = [i for i in CT.ids() if CT.ENGINE[i]["engine"] and CT.ENGINE[i]["engine"].get("module") == "singles"]
check("the family has its six designs, a module each (Clean Iris draws no effect), the primitives are styles/matter.py, and the style catalogue sees the family built",
      FAMILY_FILES == ["__init__.py", "elements.py", "gold.py", "kit.py", "powder.py", "radiance.py", "splash.py"] and os.path.isfile(os.path.join(STYLES, "matter.py"))
      and CT.engine_built("singles") and ST.family("singles").__name__ == "_lib.styles.singles" and len(SINGLES_STYLES) == 6, (FAMILY_FILES, SINGLES_STYLES))
mods = [os.path.join(FAMILY, f) for f in FAMILY_FILES] + [os.path.join(STYLES, "matter.py")]
src_all = "".join(read(m) for m in mods)
check("every module of the family has the __future__ import (Python 3.12 is Vercel's default) and parses as 3.12",
      all(re.search(r"^from __future__ import annotations\r?$", read(m), re.M) and ast.parse(read(m), feature_version=(3, 12)) for m in mods), [os.path.basename(m) for m in mods])
check("no module holds a dash, a Windows or scratch path, a studio tagline, a secret name, an environment line for threads or a path read at run time",
      not re.search(DASH, src_all) and not re.search(r"C:\\|wave-g|wave-y2|wave-y3|THE UNIVERSE WITHIN|PRECISE IRIS|GEMINI_API_KEY|SERVICE_KEY|OMP_NUM_THREADS|sys\.path", src_all),
      re.findall(r"C:\\|wave-g|wave-y2|wave-y3|GEMINI_API_KEY|OMP_NUM_THREADS|sys\.path", src_all)[:5])
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
check("no module of the family keeps an empty module level dict, list or set (a cache): the two caches that were keyed by the eye are BoundedCache(64), the atlases and plates are the foundation's",
      not any(empty_containers(m) for m in mods), {os.path.basename(m): empty_containers(m) for m in mods if empty_containers(m)})
check("importing a design reads no file of its own, opens no socket and writes nothing: no open(), no os.environ, no subprocess in any module of the family",
      not re.search(r"\bopen\(|os\.environ|subprocess|socket|np\.load|\.save\(", src_all), re.findall(r"\bopen\(|os\.environ|subprocess|socket|np\.load|\.save\(", src_all)[:5])
DESIGNS_IN_REGISTRY = sorted(CT.ENGINE[i]["engine"]["design"] for i in SINGLES_STYLES)
check("the registry's six single styles and the family agree: same designs, same canvases (the geometry table of the kit has a row per design and canvas)",
      DESIGNS_IN_REGISTRY == sorted(S.DESIGNS) and all(CT.ENGINE[i]["canvases"] == list(S.FORMATS) for i in SINGLES_STYLES)
      and set(K.SPECS) == set(S.DESIGNS) and all(set(K.SPECS[d]["r"]) == set(S.FORMATS) and set(K.SPECS[d]["cy"]) == set(S.FORMATS) for d in K.SPECS), (DESIGNS_IN_REGISTRY, K.SPECS.keys()))
PROTO_PICK = {"own": "powder", "dark_brown": "gold", "grey": "radiance"}      # the prototype's PICK table: the recommended design per colour class
check("the prototype's recommend and PICK are the registry's pick: own colours Powder Burst, dark brown Celestial Gold, grey Radiance (each with a reason key), and no other single style is picked",
      {c: [CT.ENGINE[i]["engine"]["design"] for i in SINGLES_STYLES if c in CT.STYLES[i]["pick"]] for c in PROTO_PICK} == {c: [d] for c, d in PROTO_PICK.items()}
      and all(CT.STYLES[i]["reason"].keys() == set(CT.STYLES[i]["pick"]) for i in SINGLES_STYLES if CT.STYLES[i]["pick"]) and not hasattr(S, "recommend") and not hasattr(S, "PICK"))
check("every cost row the family needs exists: a preview row and a master row for each of the six designs",
      all(CO.known(f"singles.{d}", 1) and 1 in CO.PREVIEW[f"singles.{d}"] for d in S.DESIGNS))
check("no stage was raised: every single style of the engine is still at the laboratory ceiling, so a customer can neither order nor preview one, and the admin can look at all six",
      all(CT.ceiling(i, 1) == "lab" and not CT.orderable(i, 1) and not CT.previewable(i, 1) and CT.previewable(i, 1, admin=True) for i in SINGLES_STYLES)
      and not any(t["id"] in SINGLES_STYLES for t in CT.tiles_for(1))
      and {t["id"] for t in CT.tiles_for(1, admin=True)} >= {i for i in SINGLES_STYLES if CT.STYLES[i]["tile_order"] > 0} and CT.STYLES["solo.elements"]["tile_order"] == 0,
      [(i, CT.ceiling(i, 1)) for i in SINGLES_STYLES])

# ============================================================================================ 2. the golden replay
section("2. the golden replay: this code's recorded pictures, and the step A recording with the old seed")
FIX = {n: SI.png_bytes(n) for n in SC.FIXTURE_BASE}
check("the three fixtures of the replay are the very bytes of the recording", all(hashlib.sha256(FIX[n]).hexdigest() == GOLD["fixtures"][n] for n in FIX),
      [n for n in FIX if hashlib.sha256(FIX[n]).hexdigest() != GOLD["fixtures"][n]])
print(f"   (recorded on {GOLD['machine']}; running on python {sys.version.split()[0]}, numpy {np.__version__}, Pillow {PIL.__version__})", flush=True)

LAST = {}
SEEN = {"t": [], "black": {}, "clean_out": [], "veil": []}
IRISES = {}


def port_render(design, eye, fmt, size, names, date):
    r = S.render(design, eye, fmt, size, names, date)
    LAST["r"] = r
    return r


def replay(cases, with_checks=True):
    """The cases rendered on the port: [(case, record, differences)]. For every picture the hard rules of section 3 are measured on the way."""
    out = []
    for c in cases:
        rec = SC.render_case(port_render, C.Iris, FIX, c, IRISES)
        g = G[c["key"]]
        diff = [k for k in ("sha", "seed", "facts", "w", "h", "cls") if rec[k] != g[k]]
        out.append((c, rec, diff))
        if with_checks:
            r = LAST["r"]
            img8 = np.asarray(r.img)
            rep = SCK.run(img8, [r.d], text_log=r.log, customer=[c["names"], c["date"]], ids=[c["design"], "single"])
            SEEN["t"].append((c["key"], rep["ok"], {k: v["ok"] for k, v in rep["checks"].items()}))
            if c["size"] == 1024 and not (c["names"] or c["date"]) and c["fmt"] == "1:1":
                SEEN["black"][(c["design"], c["eye"])] = SCK.black_share(img8)
                if c["design"] == "powder":
                    SEEN["veil"].append((r.ctx.log.get("veil_mean_alpha"), r.ctx.log.get("veil_max_alpha")))
            if c["design"] == "clean" and c["size"] == 1024 and not (c["names"] or c["date"]):
                rho = np.hypot(np.arange(img8.shape[1])[None, :] + 0.5 - r.d.cx, np.arange(img8.shape[0])[:, None] + 0.5 - r.d.cy) / r.d.R
                SEEN["clean_out"].append(int(img8[rho > 1.03].max()))
        if c["size"] >= 2048:
            IRISES.clear()
            gc.collect()
    return out


t0 = time.time()
ALL = SC.cases()
for size in (512, 1024):
    for design in S.DESIGNS:
        rows = replay([c for c in ALL if c["size"] == size and c["design"] == design and not (c["names"] or c["date"]) and c["fmt"] == "1:1"])
        bad = [(c["key"], d) for c, _, d in rows if d]
        check(f"{design} at {size} px: the three eye classes give the recorded pictures, seeds and plate picks, byte for byte", len(rows) == 3 and not bad, str(bad) + NOTE)
for design in S.DESIGNS:
    rows = replay([c for c in ALL if c["size"] == 512 and c["design"] == design and (c["names"] or c["date"])])
    bad = [(c["key"], d) for c, _, d in rows if d]
    check(f"{design}: the 4:5 canvas with names, the wallpaper with a date and the square with both (the frame shrinks and moves up with text) equal the recorded pictures", len(rows) == 3 and not bad, str(bad) + NOTE)
for design in ("clean", "radiance", "gold"):
    rows = replay([c for c in ALL if c["size"] == 4096 and c["design"] == design])
    bad = [(c["key"], d) for c, _, d in rows if d]
    check(f"{design} at 4096 px (a master): the three eye classes equal the recorded pictures, byte for byte", len(rows) == 3 and not bad, str(bad) + NOTE)
print(f"   (replayed in {time.time() - t0:.0f} s)", flush=True)


def legacy_render(design, eye, fmt, size, names, date):
    return S.render(design, eye, fmt, size, names, date, opts={"seed_mode": "legacy"})


def replay_legacy(cases):
    """The step A cases rendered with the seed of the prototype (the bytes of the iris): [(case, differences from the step A recording)]."""
    out = []
    for c in cases:
        rec = SC.render_case(legacy_render, C.Iris, FIX, c, IRISES)
        g = GA[c["key"]]
        out.append((c, [k for k in ("sha", "seed", "facts", "w", "h", "cls") if rec[k] != g[k]]))
        if c["size"] >= 2048:
            IRISES.clear()
            gc.collect()
    return out


t0 = time.time()
for label, cases_ in (("512 px (every design x three eyes, and the other two canvases with names and a date)", [c for c in ALL if c["size"] == 512]),
                      ("1024 px (every design x three eyes)", [c for c in ALL if c["size"] == 1024]),
                      ("4096 px (a master of Clean Iris, Radiance and Celestial Gold on the blue eye)", [c for c in ALL if c["size"] == 4096 and c["eye"] == "blue_round"
                                                                                                           and c["design"] in ("clean", "radiance", "gold")])):
    rows = replay_legacy(cases_)
    bad = [(c["key"], d) for c, d in rows if d]
    check(f"STEP A replay with the old seed (opts seed_mode legacy), {label}: {len(rows)} pictures equal the scratch prototype's, byte for byte, with their seeds and plate picks "
          "(the seed is the only thing step B changed)", len(rows) >= 3 and not bad, str(bad[:4]) + NOTE)
print(f"   (legacy replay in {time.time() - t0:.0f} s)", flush=True)
check("the step A recording is kept as it was (data/stepA: the scratch prototype's hashes, 72 cases and the 24 real-eye ones) and the new recording names it by its hash: the same 72 keys, and exactly the Clean Iris "
      "pictures kept their hashes (Clean Iris draws no matter, its seed only dithers pure black), every picture of the five other designs moved",
      set(GA) == set(G) and len(GA) == 72 and GOLD["step"] == "B"
      and GOLD["stepA_file_sha256"] == hashlib.sha256(open(os.path.join(HERE, "data", "stepA", "singles_goldens.json"), "rb").read().replace(b"\r\n", b"\n")).hexdigest()
      and all((G[k]["sha"] == GA[k]["sha"]) == k.startswith("clean.") for k in G) and json.load(open(os.path.join(HERE, "data", "singles_goldens_real.json"), encoding="utf-8"))["stepA_file_sha256"]
      == hashlib.sha256(open(os.path.join(HERE, "data", "stepA", "singles_goldens_real.json"), "rb").read().replace(b"\r\n", b"\n")).hexdigest(),
      [k for k in G if (G[k]["sha"] == GA[k]["sha"]) != k.startswith("clean.")][:5])
with mock.patch.object(K, "F3_SPAN", K.F3_SPAN * 1.02):
    moved = SC.render_case(port_render, C.Iris, FIX, [c for c in ALL if c["design"] == "clean" and c["size"] == 512][0], {})
check("the replay can fail: a two percent change of the iris feather moves the hash of Clean Iris", moved["sha"] != G["clean.blue_round.1:1.512"]["sha"])

# the 4096 px pictures of the plate styles: 4K plates from a local store made out of the scratch tree's own files
if SCRATCH_Y3 and os.path.isdir(SCRATCH_Y3):
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import upload_plates as UP  # noqa: E402
    from _lib import plates_registry as REG  # noqa: E402
    need = set()
    for k, v in G.items():
        if k.endswith(".4096"):
            for f in v["facts"].values():
                need |= {f[x] for x in ("plate", "flame_plate", "water_plate") if x in f}
    table = REG.PLATES_REGISTRY["plates"]
    y2 = os.path.join(os.path.dirname(os.path.abspath(SCRATCH_Y3)), "wave-y2", "plates")
    rows_ = UP.plan({i: table[i] for i in need}, {table[i]["family"] for i in need}, UP.sources(y2, SCRATCH_Y3))
    tot = UP.run(rows_, store, True, out=lambda m: None)
    local(f"the {len(need)} 4K plates the three plate styles pick at 4096 px are in a local store (read from the scratch tree, sha256 equal to the registry's)",
          tot["bad_source"] == 0 and tot["wrong"] == 0 and tot["uploaded"] + tot["present"] == len(need), tot)
    need_a = set()
    for k, v in GA.items():
        if k == "powder.blue_round.1:1.4096":
            for f in v["facts"].values():
                need_a |= {f[x] for x in ("plate", "flame_plate", "water_plate") if x in f}
    rows_a = UP.plan({i: table[i] for i in need_a}, {table[i]["family"] for i in need_a}, UP.sources(y2, SCRATCH_Y3))
    tot_a = UP.run(rows_a, store, True, out=lambda m: None)
    rows_l = replay_legacy([c for c in ALL if c["key"] == "powder.blue_round.1:1.4096"])
    local("Powder Burst at 4096 px on the blue eye with the old seed (4K plate through storage and the cache) equals the scratch prototype's picture of step A, byte for byte",
          tot_a["bad_source"] == 0 and tot_a["wrong"] == 0 and len(rows_l) == 1 and not rows_l[0][1], (tot_a, rows_l))
    PL.clear_memory()
    for design in ("powder", "splash", "elements"):
        rows = replay([c for c in ALL if c["size"] == 4096 and c["design"] == design])
        bad = [(c["key"], d) for c, _, d in rows if d]
        local(f"{design} at 4096 px (4K plates through storage, the cache and the sha256 check): the three eye classes equal the recorded pictures, byte for byte",
              len(rows) == 3 and not bad, str(bad) + NOTE)
        PL.clear_memory()
else:
    print("   (the 4096 px pictures of Powder Burst, Splash and Elements are replayed only with SNAPEYES_SCRATCH_Y3: their 4K plates are in private storage)", flush=True)

# ============================================================================================ 3. the hard rules
section("3. the hard rules on every picture of the replay (synthetic eyes)")
bad = [t for t in SEEN["t"] if not t[1]]
check(f"T1, T6, T7 and T12 on every one of the {len(SEEN['t'])} pictures: the iris is the graded iris byte for byte (zone A, largest difference 0), nothing of the matter lies on it, "
      "the text drawn is the customer's own words, no heart", len(SEEN["t"]) >= 60 and not bad, bad[:3])
check("T4: the black share of Powder Burst is inside 45 to 65 percent and Elements inside 55 to 75 on the three eyes (the numbers are the picture's own, 1024 px)",
      all(0.45 <= SEEN["black"][("powder", e)] <= 0.65 and 0.55 <= SEEN["black"][("elements", e)] <= 0.75 for e in SC.EYES),
      {k: round(v, 3) for k, v in SEEN["black"].items() if k[0] in ("powder", "elements")})
check("Clean Iris: every pixel more than 1.03 R from the iris is exactly black", SEEN["clean_out"] and max(SEEN["clean_out"]) == 0, SEEN["clean_out"])
check("Powder Burst's veil is a veil: mean alpha at most 0.10 and no pixel above 0.6 (zone B only, the wind side)",
      SEEN["veil"] and all(m is not None and m <= 0.10 and x <= 0.6 + 1e-6 for m, x in SEEN["veil"]), SEEN["veil"])
r_txt = S.render("gold", C.Iris(FIX["blue_round"], "x"), "1:1", 512, "Anna;Max", "12 May 2026")
check("the customer's words: the old string \"Anna;Max\" is drawn as one lockup line, the date as typed, and nothing else is ever drawn",
      [(e["kind"], e["text"]) for e in r_txt.log] == [("names", "Anna \u00b7 Max"), ("date", "12 May 2026")], r_txt.log)

# ============================================================================================ 4. determinism, caches, guards
section("4. determinism, bounded caches and the guards of render()")
a = SC.render_case(port_render, C.Iris, FIX, [c for c in ALL if c["design"] == "powder" and c["size"] == 512][0], {})
check("the same eye twice in one process gives the same picture; so does a fresh Iris of the same bytes", a["sha"] == G["powder.blue_round.1:1.512"]["sha"])
code = ("import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); import hashlib, numpy as np, synth_iris as SI; from _lib.styles import core as C, singles as S; "
        "r = S.render('splash', C.Iris(SI.png_bytes('grey_round'), 'g'), '1:1', 512); print(hashlib.sha256(np.ascontiguousarray(np.asarray(r.img)).tobytes()).hexdigest())") % (API, HERE)
env = dict(os.environ, PYTHONHASHSEED="12345")
pr = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300, env=env)
check("a fresh interpreter with another PYTHONHASHSEED draws the same picture (no hash(), no dict order, no clock in a seed)",
      pr.returncode == 0 and pr.stdout.strip() == G["splash.grey_round.1:1.512"]["sha"], (pr.stdout[-200:], pr.stderr[-300:]))
from _lib.styles.singles import radiance as RAD  # noqa: E402
RAD._INFO.clear()
K._H2.clear()
for n_ in ("blue_round", "dark_brown_round", "grey_round", "amber_slit", "green_round"):
    ir_ = C.Iris(SI.png_bytes(n_), n_)
    S.render("radiance", ir_, "1:1", 256)
    S.render("powder", ir_, "1:1", 256)
check("the two caches the prototype kept per eye (the secondary hue, the fibre facts) are BoundedCache(64), keep what was seen and hold the last 64 at most",
      isinstance(K._H2, C.BoundedCache) and isinstance(RAD._INFO, C.BoundedCache) and K._H2.maxsize == 64 and RAD._INFO.maxsize == 64 and len(K._H2) == 5 and len(RAD._INFO) >= 1
      and (lambda c: [c.put(i, i) for i in range(200)] and len(c) == 64)(C.BoundedCache(64)))
eye0 = C.Iris(FIX["blue_round"], "e")
check("render() refuses an unknown design, a canvas the family does not draw, a size outside 64 to 4096 and anything that is not an eye",
      raises(lambda: S.render("nope", eye0), KeyError) is not False and isinstance(raises(lambda: S.render("clean", eye0, "3:2"), ValueError), ValueError)
      and isinstance(raises(lambda: S.render("clean", eye0, size=8192), ValueError), ValueError) and isinstance(raises(lambda: S.render("clean", eye0, size=10), ValueError), ValueError)
      and isinstance(raises(lambda: S.render("clean", "a/path.jpg"), TypeError), TypeError) and isinstance(raises(lambda: K.load_eye(None), TypeError), TypeError))
check("the round 1 feather option (opts feather legacy) is gone: it changes nothing",
      S.render("clean", eye0, "1:1", 256, opts={"feather": "legacy"}).img.tobytes() == S.render("clean", eye0, "1:1", 256).img.tobytes())
check("an eye may be the bytes of a restored square (a function reads what the request carried, never a path): bytes and Iris give the same picture",
      S.render("clean", FIX["blue_round"], "1:1", 256).img.tobytes() == S.render("clean", eye0, "1:1", 256).img.tobytes())

# ============================================================================================ 5. the contract
section("5. the contract: resolve, preview, tiles, the watermark, a plate that is missing")
spec = {"style": "solo.powder", "layout": "single", "eyes": 1, "canvas": "1:1", "names": ["Anna", "Max"], "date": ""}
pl = ST.resolve(spec, [])
check("resolve answers the plan without a pixel: family, design, canvas, the iris at 1024 px, the seed key of the plan (registry id, design, background, clean flag, layout, options, plates version); "
      "with no eye known there is no seed and no plate (the seed is made from the eye id: step B)",
      pl["family"] == "singles" and pl["design_used"] == "powder" and pl["fallback"] is None and pl["canvas"] == "1:1" and pl["layout"] == "single"
      and set(pl["seed_key"]) == {"style", "design_used", "bg", "clean", "layout", "opts", "pv"} and pl["seed_key"]["pv"] == CT.PLATES_VERSION and pl["plates"] is None
      and pl["seed_from"] == "eye_id" and pl["seed"] is None and pl["eye_ids"] == [] and pl["frozen"] == {}
      and pl["steps"] == ["art"] and pl["iris_at_1024"]["R"] > 200 and ST.resolve(dict(spec, canvas="9:19.5"), None)["canvas"] == "9:19.5"
      and ST.resolve(dict(spec, canvas="bogus"), None)["canvas"] == "1:1", pl)
t0 = time.perf_counter()
ST.resolve(spec, [])
check("resolve takes a few milliseconds (at most 50)", (time.perf_counter() - t0) * 1000 < 50)
check("resolve refuses a style that is not of the family (a legacy id, another family's style)",
      isinstance(raises(lambda: ST.resolve({"style": CT.legacy_ids()[0], "eyes": 1}, []), ST.EngineNotBuilt), ST.EngineNotBuilt))
eye_a = C.Iris(FIX["dark_brown_round"], "a")
pv = ST.preview([eye_a], dict(spec, style="solo.gold", names="Anna", date="2026"), size=512, check=True)
check("preview: the clean render as a Preview (picture, disc, graded frame, design, canvas, size, seed, class, the design's facts, times, text log, the selfcheck report that passes)",
      pv.img.size == (512, 512) and pv.design == "gold" and pv.fmt == "1:1" and pv.size == 512 and pv.cls == "dark_brown" and len(pv.discs) == 1 and pv.discs[0][2] > 100
      and isinstance(pv.graded[0], np.ndarray) and pv.graded[0].shape[2] == 3 and pv.selfcheck["ok"] is True and set(pv.selfcheck["checks"]) >= {"t1", "t6", "t7", "t12"} and "gold" in pv.log
      and pv.times["total"] > 0 and [e["kind"] for e in pv.text_log] == ["names", "date"] and pv.width == 512, (pv.fmt, pv.size, pv.selfcheck))
pw = ST.preview([eye_a], dict(spec, style="solo.gold", names="", date=""), size=512, watermark=True)
pc_ = ST.preview([eye_a], dict(spec, style="solo.gold", names="", date=""), size=512)
d0 = pc_.discs[0]
yy, xx = np.mgrid[0:512, 0:512]
inside = np.hypot(xx + 0.5 - d0[0], yy + 0.5 - d0[1]) < 0.9 * d0[2]
diff_in = np.abs(np.asarray(pw.img).astype(int) - np.asarray(pc_.img).astype(int)).max(-1)[inside]
check("watermark=True returns the free preview: the words lie on the iris disc too (the clean render differs from it on the iris), while the clean render is the golden picture and the Preview of "
      "watermarked() is a copy (the clean one is not changed)", (diff_in > 8).mean() > 0.01 and pc_.img.tobytes() != pw.img.tobytes() and ST.watermarked(pc_).tobytes() == pw.img.tobytes()
      and S.render("gold", eye_a, "1:1", 512).img.tobytes() == pc_.img.tobytes(), float((diff_in > 8).mean()))
tl = ST.tiles([eye_a], ["solo.clean", "solo.radiance", "solo.gold"], dict(spec, names=""), size=480)
check("tiles: several styles of the family on one eye (one Iris, its ring and class measured once), a Preview each at the size asked",
      set(tl) == {"solo.clean", "solo.radiance", "solo.gold"} and all(t.img.size == (480, 480) for t in tl.values()) and tl["solo.gold"].design == "gold"
      and len({t.img.tobytes() for t in tl.values()}) == 3)
check("preview refuses a set of eyes (the family draws one) and a style that is not its own",
      isinstance(raises(lambda: ST.preview([eye_a, eye_a], spec), ValueError), ValueError) and isinstance(raises(lambda: ST.preview([eye_a], {"style": "duo.kiss_collision", "eyes": 2}), (ValueError, ST.EngineNotBuilt)), Exception))
# a plate styles' 1K plate comes from the bundle at a preview; the 4K plate comes from storage at a master and a missing one is never replaced by another
check("a preview draws its plate from the 1K file in the bundle (no storage, no cache); Powder Burst, Splash and Elements all name a plate of the registry",
      all(G[f"{d}.{e}.1:1.1024"]["facts"][d if d != "elements" else "elements"].get("lod", "1k") == "1k" for d in ("powder", "splash") for e in SC.EYES)
      and all(PL.known(G[f"splash.{e}.1:1.1024"]["facts"]["splash"]["plate"]) and PL.known(G[f"powder.{e}.1:1.1024"]["facts"]["powder"]["plate"]) for e in SC.EYES)
      and PL.known(G["elements.blue_round.1:1.1024"]["facts"]["elements"]["flame_plate"]))


class EmptyStore:
    """An empty private storage and an empty plate cache for the length of a block: what a deployment looks like before the 4K plates are uploaded."""
    def __enter__(self):
        PL.clear_memory()
        self.dir = tempfile.mkdtemp(prefix="empty_store_", dir=TMP)
        self.patch = mock.patch.dict(os.environ, {"STORE_LOCAL_DIR": os.path.join(self.dir, "store"), "STYLE_PLATE_CACHE": os.path.join(self.dir, "cache")})
        os.makedirs(os.path.join(self.dir, "store"))
        self.patch.start()

    def __exit__(self, *a):
        self.patch.stop()
        PL.clear_memory()


with EmptyStore():
    e_missing = raises(lambda: S.render("powder", C.Iris(FIX["blue_round"], "m", max_side=4096), "1:1", 4096), PL.PlateUnavailable)
check("a master of a plate style whose 4K plate is not in storage is PlateUnavailable(missing) naming the plate: the render stops, no other plate is drawn",
      isinstance(e_missing, PL.PlateUnavailable) and e_missing.why == "missing" and e_missing.plate_id.startswith("P-SN-CLOUD"), e_missing)
gc.collect()

# ============================================================================================ 6. /api/compose
section("6. /api/compose: a style a customer may see is drawn by the engine, a laboratory style is not")
import importlib.util  # noqa: E402
spec_ = importlib.util.spec_from_file_location("compose", os.path.join(API, "compose.py"))
CMP = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(CMP)
EVENTS = []
E.record = lambda kind, **f: EVENTS.append((kind, dict(f))) or False
jpeg = SI.jpeg_bytes("dark_brown_round")
im_j = Image.open(io.BytesIO(jpeg)).convert("RGB")
sealed = P.protect(im_j, jpeg)["sealed"]


class Show:
    """A style of the engine made visible to customers for the length of a block (the ceilings are the registry's, a test may not raise one for good)."""
    def __init__(self, style, stage="preview"):
        self.style, self.stage = style, stage

    def __enter__(self):
        self.old = CT.STYLES[self.style]["stage"]
        CT.STYLES[self.style]["stage"] = self.stage

    def __exit__(self, *a):
        CT.STYLES[self.style]["stage"] = self.old


ids_before = list(CT.previewable_ids(1))
check("before anything is raised the customer's list of styles for one eye holds the legacy six and no style of the engine",
      not any(i in ids_before for i in SINGLES_STYLES) and len(ids_before) == 6, ids_before)
try:
    CMP.compose({"sealed": [sealed], "style": "solo.gold", "pad": 1.12})
    e_lab = None
except Exception as e_:  # noqa
    e_lab = e_
# WP10 (compose API v3): the old check said that a laboratory style falls to the default style; the contract says 422 style_unavailable, and never a render
check("a laboratory style asked by a customer is not drawn by the engine: 422 style_unavailable (why stage), nothing is rendered; no compose event names it",
      getattr(e_lab, "status", None) == 422 and e_lab.body["reason"] == "style_unavailable" and e_lab.body["why"] == "stage"
      and all(e[1].get("style") != "solo.gold" for e in EVENTS), (e_lab, EVENTS[-1:]))
EVENTS.clear()
with Show("solo.gold"), mock.patch.object(L, "colour_qa", wraps=L.colour_qa) as qa_spy:
    r_g = CMP.compose({"sealed": [sealed], "style": "solo.gold", "pad": 1.12, "names": "Anna;Max", "date": "12 May 2026", "lang": "en"})
    ids_shown = list(CT.previewable_ids(1))
    rg2 = CMP.compose({"sealed": [sealed], "style": "solo.gold", "format": "wallpaper", "pad": 1.12})
    rg3 = CMP.compose({"sealed": [sealed], "style": "solo.gold", "format": "bogus", "pad": 1.12})
    try:
        CMP.compose({"sealed": [sealed], "style": "solo.gold", "layout": "ring", "pad": 1.12})
        e_ring = None
    except Exception as e_:  # noqa
        e_ring = e_
    ev_g = [e for e in EVENTS if e[0] == "compose"][0][1]
meta_ = P.unseal_full(sealed)[1]
exp_pv = ST.preview([C.Iris(jpeg, "compose", max_side=2048, eye_id=meta_["eye_id"])], {"style": "solo.gold", "layout": "single", "eyes": 1, "canvas": "1:1", "names": "Anna \u00b7 Max", "date": "12 May 2026"},
                    size=1024, watermark=True)
check("a style made visible is drawn by the engine: the reply has every field of a compose reply (and canvas), the picture is the engine's clean render with the preview watermark (equal to a render of the same bytes, "
      "names as one lockup, date as typed), the eye id and gate of the seal are in eyes[]",
      r_g["ok"] and r_g["style"] == "solo.gold" and r_g["layout"] == "single" and r_g["layouts"] == ["single"] and r_g["format"] == "artwork" and r_g["canvas"] == "1:1" and r_g["count"] == 1
      and (r_g["width"], r_g["height"]) == (1024, 1024) and r_g["image"] == L.pil_to_b64(exp_pv.img, "JPEG", 90) and "solo.gold" in r_g["styles"] and "solo.gold" in ids_shown
      and {"ok", "style", "layout", "layouts", "format", "count", "width", "height", "image", "styles", "qa", "eyes", "canvas"} <= set(r_g)
      and r_g["eyes"][0]["eye_id"] == meta_["eye_id"] and isinstance(r_g["qa"].get("ok"), bool), {k: r_g[k] for k in r_g if k not in ("image",)})
check("the picture a customer gets is a preview: it is not the clean picture (the words of the watermark lie over the whole canvas and on the iris), and the clean render of the same bytes is not what the reply holds",
      r_g["image"] != L.pil_to_b64(ST.preview([C.Iris(jpeg, "compose", max_side=2048, eye_id=meta_["eye_id"])], {"style": "solo.gold", "layout": "single", "eyes": 1, "canvas": "1:1", "names": "Anna \u00b7 Max", "date": "12 May 2026"}, size=1024).img, "JPEG", 90))
check("the format words of the legacy page read as canvases: wallpaper is the phone canvas (9:19.5), an unknown format falls back to the square artwork; a layout that is not the style's is a 400 (WP10: it fell back to the default before)",
      rg2["canvas"] == "9:19.5" and rg2["format"] == "wallpaper" and rg2["width"] < rg2["height"] and abs(rg2["height"] / rg2["width"] - 19.5 / 9) < 0.01
      and rg3["canvas"] == "1:1" and rg3["format"] == "artwork" and rg3["layout"] == "single" and isinstance(e_ring, L.ClientError))
check("the compose event names the style and the set's gate like every compose event, and the colour QA ran on the graded frame",
      ev_g.get("style") == "solo.gold" and ev_g.get("eyes") == 1 and ev_g.get("layout") == "single" and ev_g.get("format") == "artwork" and ev_g.get("clean") is False and "gate" in ev_g
      and E.build("compose", ev_g).get("style") == "solo.gold" and qa_spy.called, ev_g)
tkt = L.mint_ticket("unlock")
with Show("solo.gold"):
    r_clean = CMP.compose({"sealed": [sealed], "style": "solo.gold", "pad": 1.12, "unlock": tkt, "names": "Anna", "date": ""})
    r_noclean = CMP.compose({"sealed": [sealed], "style": "solo.gold", "pad": 1.12, "unlock": tkt + "x", "names": "Anna"})
exp_clean = ST.preview([C.Iris(jpeg, "compose", max_side=2048, eye_id=meta_["eye_id"])], {"style": "solo.gold", "layout": "single", "eyes": 1, "canvas": "1:1", "names": "Anna", "date": ""}, size=1024)
check("a valid unlock ticket gives the clean render and nothing else does (a ticket that is not valid leaves the watermark)",
      r_clean["image"] == L.pil_to_b64(exp_clean.img, "JPEG", 90) and r_noclean["image"] != r_clean["image"])
with Show("solo.gold"):
    r_plain = CMP.compose({"irises": [b64(jpeg)], "style": "solo.gold", "pad": 1.12, "names": "Anna;Max", "date": "12 May 2026"})
check("an old page's plain iris gives the same picture as the sealed one (the same bytes, the same seed), with unknown gates and no eye id",
      r_plain["image"] == r_g["image"] and r_plain["eyes"][0]["eye_id"] is None and r_plain["eyes"][0]["gate"] == {"lid": None, "fill": None})


def exif_jpeg(orientation, junk=None):
    """A landscape JPEG (the iris on the left of a wider black frame) with a camera orientation, as a phone writes it (junk: the bytes of a damaged EXIF block instead)."""
    wide = Image.new("RGB", (1200, 1024), (0, 0, 0))
    wide.paste(Image.open(io.BytesIO(SI.png_bytes("blue_round"))).convert("RGB"), (0, 0))
    ex = Image.Exif()
    ex[0x0112] = orientation
    bio = io.BytesIO()
    wide.save(bio, "JPEG", quality=92, exif=junk if junk is not None else ex.tobytes())
    return bio.getvalue()


raw_x = exif_jpeg(6)
sq_legacy = CMP._irises_full({"irises": [b64(raw_x)]})
eye_x = C.Iris(sq_legacy[2][0], "x", max_side=2048)
up_png = io.BytesIO()
ImageOps.exif_transpose(Image.open(io.BytesIO(raw_x))).convert("RGB").save(up_png, "PNG")
check("the engine reads an iris the way the legacy engine does: the camera orientation of the file is applied before the square is cut, so both cut the same square (an old page's plain "
      "iris: the engine's square equals the legacy one and equals the upright picture's); the seed is still the sha256 of the bytes as sent",
      np.array_equal(np.asarray(sq_legacy[0][0]), np.asarray(eye_x.src)) and np.array_equal(np.asarray(eye_x.src), np.asarray(C.Iris(up_png.getvalue()).src))
      and eye_x.src.size == (1024, 1024) and eye_x.digest == hashlib.sha256(raw_x).digest() and not np.array_equal(np.asarray(eye_x.src), np.asarray(C.Iris(exif_jpeg(1)).src)))
im_up = Image.open(io.BytesIO(jpeg)).convert("RGB")
check("a file with no orientation, orientation 1 or a damaged EXIF block is read as before: the pixels are the file's own (a damaged block never refuses a picture)",
      np.array_equal(np.asarray(C.Iris(jpeg).src), np.asarray(im_up.crop((0, 0, min(im_up.size), min(im_up.size)))))
      and C.Iris(exif_jpeg(1)).src.size == (1024, 1024) and C.Iris(exif_jpeg(1, junk=b"Exif\x00\x00MM\x00*\xff\xff\xff\xff\x00\x01")).src.size == (1024, 1024))
with Show("solo.clean"):
    r_exif = CMP.compose({"irises": [b64(raw_x)], "style": "solo.clean", "pad": 1.12})
    r_upright = CMP.compose({"irises": [b64(up_png.getvalue())], "style": "solo.clean", "pad": 1.12})
check("end to end, a phone photo with an orientation gives the picture of the same photo upright (Clean Iris has no seed to tell the two files apart)",
      r_exif["ok"] and r_exif["style"] == "solo.clean" and r_exif["image"] == r_upright["image"], (r_exif["style"], r_exif["image"] == r_upright["image"]))
t0 = time.time()
tx_big = CMP._engine_text("A" * 4_000_000, 60)
tx_parts = CMP._engine_text([f"N{i}" for i in range(300_000)], 60)
tx_date = CMP._engine_date("9" * 4_000_000, 20)
t_text = time.time() - t0
check("a customer's text is read from its first 1000 characters and 16 parts only: a 4 MB names field, a list of 300 000 names and a 4 MB date cost milliseconds (cleaned whole, one 4 MB "
      "field took 7.5 s of CPU of a public endpoint before the picture was drawn) and give the lines they gave",
      t_text < 1.5 and tx_big == "A" * 60 and tx_parts == " · ".join(f"N{i}" for i in range(16))[:60] and tx_date == "9" * 20, (round(t_text, 2), tx_big[:10], tx_parts[:20]))
check("names that are not text are no names (a number, a dict, None, a list of numbers: an empty line); a date is one line as typed, equal to what the paid file draws (TX.clean): a semicolon "
      "or a line break does not turn it into a lockup of several dates (a line break is a control character that the drawer's own clean() removes), and a letter the font lacks is left out of it as of the names",
      CMP._engine_text(12345) == "" and CMP._engine_text({"a": 1}) == "" and CMP._engine_text(None) == "" and CMP._engine_text([1, 2]) == "" and CMP._engine_text("Anna;Max") == "Anna · Max"
      and CMP._engine_text(["Anna", "Max"], 60) == "Anna · Max" and CMP._engine_date("12;05;2026", 20) == "12;05;2026" == TX.clean("12;05;2026")
      and CMP._engine_date("12\n05", 20) == TX.clean("12\n05") == "1205" and CMP._engine_date(5) == "" and CMP._engine_date(None) == "" and CMP._engine_date("12 中 May", 20) == "12 May")
with Show("solo.gold"):
    r_font = CMP.compose({"sealed": [sealed], "style": "solo.gold", "pad": 1.12, "names": "Anna \u4e2d\u6587 \u2665 Max"})
check("a letter the artwork font cannot draw is left out of a free preview (it would print as an empty box); a heart never reaches the picture",
      r_font["ok"] and CMP._engine_text("Anna \u4e2d\u6587 \u2665 Max") == "Anna Max" and CMP._engine_text("\u0105\u010d\u0119\u0117\u012f\u0161\u0173\u016b\u017e \u0151\u0171 \u00e4\u00f6\u00fc\u00df") != "", CMP._engine_text("Anna \u4e2d\u6587 \u2665 Max"))
two = [sealed] * 2
with Show("solo.gold"):
    e_two = raises(lambda: CMP.compose({"sealed": two, "style": "solo.gold", "pad": 1.12}), Exception)
# WP10 (compose API v3): the old check said that two eyes asked for a one-eye style fall back to a style that takes two; the contract says 422 style_unavailable (why eyes)
check("two eyes asked for a one-eye style are not drawn by it: 422 style_unavailable (why eyes), nothing is rendered",
      getattr(e_two, "status", None) == 422 and e_two.body["reason"] == "style_unavailable" and e_two.body["why"] == "eyes", e_two)
with Show("solo.gold"):
    r_legacy = CMP.compose({"sealed": [sealed], "style": "celestial_gold", "pad": 1.12})
check("a legacy style is still drawn by the legacy engine, with none of the engine's fields", r_legacy["style"] == "celestial_gold" and "canvas" not in r_legacy and r_legacy["format"] == "artwork")
with Show("solo.gold", "lab"):
    e_lab1 = raises(lambda: CMP.compose({"sealed": [sealed], "style": "solo.gold", "lab": True, "pad": 1.12}), Exception)
    e_lab2 = raises(lambda: CMP.compose({"sealed": [sealed], "style": "solo.gold", "lab": True, "pad": 1.12}, "admin-1.2.3"), Exception)
src_c = read(os.path.join(API, "compose.py"))
# WP10 (compose API v3): the old check said that compose never reads an authorization header, an admin key or a lab flag (WP5A: the lab was the admin page's own action
# until the compose work package gave compose the flag). Now the only way to the lab is lab true with a valid admin key, looked at through ops.check_admin_key, imported on use
check("compose.py reaches the laboratory only with lab true AND a valid admin key (ops.check_admin_key, imported on use, never at the top of the module): a customer, and a wrong key, get 422 style_unavailable",
      getattr(e_lab1, "status", None) == 422 and getattr(e_lab2, "status", None) == 422 and not re.search(r"^(import|from)\s.*\bops\b", src_c, re.M) and "ops.check_admin_key" in src_c, (e_lab1, e_lab2))
EVENTS.clear()
spec_m = importlib.util.spec_from_file_location("master_compose", os.path.join(API, "master_compose.py"))
MC = importlib.util.module_from_spec(spec_m)
spec_m.loader.exec_module(MC)
lab_order = "lab-260101-abcd1234"
tk_m = L.mint_ticket(store.unlock_kind(lab_order), 900)
mc_body = {"order": lab_order, "ticket": tk_m, "keys": [f"orders/{lab_order}/eye_1.jpg"], "layout": "single"}
e_v3 = raises(lambda: MC.master_compose(dict(mc_body, style="solo.powder")), store.Answer)
e_old = raises(lambda: MC.master_compose(dict(mc_body, style="celestial_gold")), L.ClientError)
check("master_compose makes a style of the v3 engine through the master plan's step runner (WP6a replaced its 400 for such a style: it must never draw one with the legacy engine, which "
      "would read an id it does not know as the default style, a silent substitution after payment): with no eye stored for the order it answers 409 eyes_not_ready, nothing is drawn, "
      "the legacy engine is not asked; a legacy id still passes the style check (it stops later: no eye is stored)",
      isinstance(e_v3, store.Answer) and e_v3.status == 409 and e_v3.body["reason"] == "eyes_not_ready" and isinstance(e_old, L.ClientError) and "not stored yet" in str(e_old), (e_v3, e_old))
check("the catalogue still says the engine styles are renderable for one eye (the laboratory and the master plan draw them) and for no other number of eyes",
      all(CT.renderable(i, 1) for i in SINGLES_STYLES) and not any(CT.renderable(i, 2) for i in SINGLES_STYLES))

# ============================================================================================ 7. the admin laboratory
section("7. the admin laboratory: styles_lab (no image model, nothing stored, behind the admin key)")
from _lib import ops  # noqa: E402
SAMPLE = open(os.path.join(REPO, "public", "assets", "sample_eye_blue_restored.jpg"), "rb").read()
lst = ops.a_styles_lab({}, "t")
lst_s = [r for r in lst["styles"] if r["module"] == "singles"]        # the list holds every one-eye style of every family built (the universe family joined it: its rows carry looks)
check("without a style styles_lab lists what the page builds its menu from: the six styles of the singles engine (and those of the other families built), with their stage, canvases, plates and the sizes",
      lst["ok"] and sorted(r["id"] for r in lst_s) == sorted(SINGLES_STYLES) and all(r["stage"] == "lab" and r["ceiling"] == "lab" and r["canvases"] == list(S.FORMATS) and r["looks"] == [] for r in lst_s)
      and lst["sizes"] == [480, 1024, 2048, 4096] and {r["name"] for r in lst["styles"]} >= {"Clean Iris", "Powder Burst", "Celestial Gold"}, lst)
ok_all = True
rows_ = []
for sid in SINGLES_STYLES:
    t0 = time.time()
    rr = ops.a_styles_lab({"style": sid, "eye": b64(SAMPLE), "size": 480, "names": "Anna;Max", "date": "2026"}, "t")
    rows_.append((sid, rr["selfcheck"]["ok"], round(time.time() - t0, 2)))
    ok_all = ok_all and rr["ok"] and rr["width"] == rr["height"] == 480 and rr["cls"] in ("own", "dark_brown", "grey") and isinstance(rr["image"], str) and rr["crop"] is None \
        and set(rr["selfcheck"]["checks"]) >= {"t1", "t6", "t7", "t12"} and rr["design"] == CT.ENGINE[sid]["engine"]["design"] and rr["plan"]["design_used"] == rr["design"] \
        and rr["times"]["total"] > 0 and isinstance(rr["estimate"]["need_s"], float)
check("styles_lab draws every style of the engine on the site's restored sample eye, whatever its stage: picture, class, seed, facts, plan, the self checks and the time, with the estimate of the cost table",
      ok_all, rows_)
check("the self checks of the laboratory are the ones that run on a delivered file: T1 iris untouched on all six (T4 is the black share: Elements may be outside its range on a real eye and says so)",
      all(ops.a_styles_lab({"style": sid, "eye": b64(SAMPLE), "size": 480}, "t")["selfcheck"]["checks"]["t1"]["ok"] for sid in SINGLES_STYLES))
big = ops.a_styles_lab({"style": "solo.clean", "eye": b64(SAMPLE), "size": 4096, "crop": [3000, 900]}, "t")
check("a 4096 px render comes back as a view of 1536 px and a window of 1280 px at 100 percent (a 4096 px JPEG would not fit the reply); the whole reply is far below 4.5 MB and the checks ran on the full size",
      big["width"] == big["height"] == 4096 and big["view"] == [1536, 1536] and big["crop"]["w"] == 1280 and big["crop"]["h"] == 1280 and big["crop"]["x"] == 3000 - 640 and big["crop"]["y"] == 900 - 640
      and len(json.dumps(big)) < 3_500_000 and big["selfcheck"]["checks"]["t1"]["ok"] and big["selfcheck"]["checks"]["t1"]["checked"] > 2_000_000 and big["estimate"]["ok"] is True and big["selfcheck"]["ms"] < 5000, (big["view"], len(json.dumps(big))))
refusals = []
for label, body in (("a legacy style", {"style": CT.legacy_ids()[0], "eye": b64(SAMPLE)}), ("an unknown style", {"style": "solo.nope", "eye": b64(SAMPLE)}),
                    ("a style that does not take one eye", {"style": "duo.kiss_collision", "eye": b64(SAMPLE)}), ("a size outside the four", {"style": "solo.clean", "eye": b64(SAMPLE), "size": 3000}),
                    ("a size as a boolean", {"style": "solo.clean", "eye": b64(SAMPLE), "size": True}), ("no eye", {"style": "solo.clean"}),
                    ("a text that is no image", {"style": "solo.clean", "eye": b64(b"not an image at all")}),
                    ("an order that is not a lab order", {"style": "solo.clean", "order": "order-20260101-abcd", "n": 1}),
                    ("an eye number out of range", {"style": "solo.clean", "order": "lab-260101-abcd1234", "n": 9}), ("a list as the style", {"style": ["solo.clean"], "eye": b64(SAMPLE)})):
    e_ = raises(lambda b=body: ops.a_styles_lab(b, "t"), L.ClientError)
    refusals.append((label, isinstance(e_, L.ClientError)))
check("styles_lab refuses with a 400 (ClientError): " + ", ".join(r[0] for r in refusals), all(r[1] for r in refusals), [r for r in refusals if not r[1]])
trunc_eye = SAMPLE[:len(SAMPLE) * 3 // 5]
flat_io = io.BytesIO()
Image.new("L", (7000, 6000), 40).save(flat_io, "JPEG", quality=50)
words = {}
for label, body in (("names over 256 characters", {"names": "A" * 300}), ("a date over 256 characters", {"date": "9" * 300}), ("names of 4 MB", {"names": "A" * 4_000_000}),
                    ("a letter the font cannot draw", {"names": "Anna 中文"}), ("names that are a number", {"names": 5}), ("17 names", {"names": [f"N{i}" for i in range(17)]}),
                    ("a date that is a list", {"date": ["2026"]}), ("a truncated JPEG", {"eye": b64(trunc_eye)}), ("a flat 42 megapixel file", {"eye": b64(flat_io.getvalue())})):
    e_ = raises(lambda b=dict({"style": "solo.clean", "eye": b64(SAMPLE), "size": 480}, **body): ops.a_styles_lab(b, "t"), L.ClientError)
    words[label] = str(e_) if isinstance(e_, L.ClientError) else "NOT A CLIENT ERROR: " + repr(e_)
check("styles_lab answers a 400 that says what is wrong (a ClientError: not the generic \"could not read that image\" of a ValueError, and not a 500): " + ", ".join(words),
      not any(v.startswith("NOT A CLIENT ERROR") for v in words.values()) and "256" in words["names over 256 characters"] and "date" in words["a date over 256 characters"]
      and "256" in words["names of 4 MB"] and "cannot draw" in words["a letter the font cannot draw"] and "names is text" in words["names that are a number"]
      and "16 texts" in words["17 names"] and "date is text" in words["a date that is a list"] and "too large" in words["a flat 42 megapixel file"]
      and "not a readable image" in words["a truncated JPEG"], words)
lt = ops.a_styles_lab({"style": "solo.clean", "eye": b64(SAMPLE), "size": 480, "names": "Ąžuolas;Čiurlionis", "date": "2026-05-12"}, "t")
check("styles_lab draws a Lithuanian name and a date, the names as one lockup line, and the text check of the report (T7) holds",
      lt["ok"] and lt["selfcheck"]["checks"]["t7"]["ok"], lt["selfcheck"]["checks"]["t7"])
nums = [ops._lab_number(v) for v in (float("nan"), float("inf"), -float("inf"), True, "1", None, 10 ** 400, 5, 2.5, -3)]
big_bad = ops.a_styles_lab({"style": "solo.clean", "eye": b64(SAMPLE), "size": 4096, "crop": [float("nan"), 10 ** 400]}, "t")
pl_ = big_bad["plan"]["iris_at_1024"]
want_x = int(min(max(4 * (pl_["cx"] + 0.72 * pl_["R"]) - 640, 0), 4096 - 1280))
want_y = int(min(max(4 * (pl_["cy"] - 0.72 * pl_["R"]) - 640, 0), 4096 - 1280))
check("a crop that is not a number (NaN, an infinity, an integer too large for a float) falls back to the default window and never fails the render",
      nums == [None, None, None, None, None, None, None, 5.0, 2.5, -3.0] and big_bad["ok"] and abs(big_bad["crop"]["x"] - want_x) <= 1 and abs(big_bad["crop"]["y"] - want_y) <= 1,
      (nums, big_bad["crop"]["x"], want_x, big_bad["crop"]["y"], want_y))
exif_lab = [ops.a_styles_lab({"style": "solo.clean", "eye": b64(x), "size": 480}, "t")["image"] for x in (raw_x, up_png.getvalue())]
check("the laboratory reads an iris as the site does: a phone photo with an orientation draws as the same photo upright", exif_lab[0] == exif_lab[1])
e_nostore = raises(lambda: ops.a_styles_lab({"style": "solo.clean", "order": "lab-260101-abcd1234", "n": 1}, "t"), L.ClientError)
store.put("orders/lab-260101-abcd1234/eye_1.jpg", SAMPLE, "image/jpeg", upsert=True)
by_order = ops.a_styles_lab({"style": "solo.clean", "order": "lab-260101-abcd1234", "n": 1, "size": 480}, "t")
check("a lab test order's stored eye is an eye (a real master without a new image model call); an order with no such eye is a 400",
      isinstance(e_nostore, L.ClientError) and by_order["ok"] and by_order["width"] == 480, e_nostore)
with EmptyStore():
    e_plate = raises(lambda: ops.a_styles_lab({"style": "solo.powder", "eye": b64(SAMPLE), "size": 4096}, "t"), store.Answer)
check("a 4096 px render of a plate style without its 4K plate in storage is 409 plate_unavailable naming the plate (the page says so), never a render with another plate",
      isinstance(e_plate, store.Answer) and e_plate.status == 409 and e_plate.body["reason"] == "plate_unavailable" and e_plate.body.get("why") == "missing", e_plate)
with mock.patch.object(CO, "assess", return_value={"need_s": 99.0, "est_mb": 9999, "ok": False, "why": "time"}):
    e_time = raises(lambda: ops.a_styles_lab({"style": "solo.radiance", "eye": b64(SAMPLE), "size": 4096}, "t"), L.ClientError)
check("a 4096 px render the cost table says cannot finish in the time or the memory of this function is refused before it starts, with the numbers", isinstance(e_time, L.ClientError) and "99.0" in str(e_time), e_time)


class Req:
    def __init__(self, token=None):
        self.headers = {"authorization": f"Bearer {token}"} if token else {}
        self.client_address = ("127.0.0.1", 1)


ops.FAIL_SLEEP = 0.0
e_auth = raises(lambda: ops.dispatch(Req(), {"action": "styles_lab", "style": "solo.clean", "eye": b64(SAMPLE), "size": 480}), store.Answer)
via_key = ops.dispatch(Req(ops.mint_admin_key(3600)), {"action": "styles_lab", "style": "solo.clean", "eye": b64(SAMPLE), "size": 480})
check("styles_lab is an admin action: without an admin key it is a 403 and draws nothing, with a valid one it answers; it is read only (not in the audit list of actions) and calls no image model",
      isinstance(e_auth, store.Answer) and e_auth.status == 403 and via_key["ok"] and "styles_lab" in ops.ACTIONS and ops.ACTIONS["styles_lab"] is ops.a_styles_lab
      and not any(k.startswith("GEMINI") for k in os.environ), e_auth)
tsx = read(os.path.join(REPO, "src", "admin", "StyleLab.tsx"))
labtsx = read(os.path.join(REPO, "src", "admin", "Lab.tsx"))
check("the admin page has the laboratory: StyleLab.tsx (menu from the server's list, the eye, size, names, the picture, the 100 percent window, the checks, the facts) is on the Laboratorija page, "
      "holds no literal style id, no dash and no call to the image model's endpoints",
      "<StyleLab call={call} lab={lab} />" in labtsx and "'styles_lab'" in tsx and "Piešti" in tsx and "selfcheck" in tsx and not re.search(r"\b(solo|duo|grp|pet)\.[a-z_]+\b", tsx) and not re.search(DASH, tsx)
      and "/api/enhance" not in tsx and "/api/master_eye" not in tsx)

# ============================================================================================ 9. step B: the seed
section("9. step B: the seed is made from the eye id and the plan's seed key and from nothing else")
EID_A, EID_B = "0123456789abcdef", "fedcba9876543210"
K_POW = S.seed_key("solo.powder", "powder")
s_pow = SD.seed_for_key([EID_A], K_POW)
code = ("import sys; sys.path.insert(0, %r); from _lib.styles import seeds as SD; import _lib.styles.singles as S; "
        "print(SD.seed_for_key(['0123456789abcdef'], S.seed_key('solo.powder', 'powder')))") % API
pr = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120, env=dict(os.environ, PYTHONHASHSEED="777"))
check("the seed is a 64 bit number made by sha256 of the eye ids and the seed key: the same in this process and in a fresh interpreter with another PYTHONHASHSEED, and pinned (a change of "
      "the formula is a change of every picture: it needs a new ENGINE_V)",
      s_pow == 8843487212479903757 and pr.returncode == 0 and pr.stdout.strip() == str(s_pow) and 0 <= s_pow < 2 ** 64, (s_pow, pr.stdout, pr.stderr[-200:]))
variants = {
    "another eye id": SD.seed_for_key([EID_B], K_POW), "two eyes": SD.seed_for_key([EID_A, EID_B], K_POW), "the eyes in the other order": SD.seed_for_key([EID_B, EID_A], K_POW),
    "another style id": SD.seed_for_key([EID_A], dict(K_POW, style="solo.splash")), "another design used": SD.seed_for_key([EID_A], dict(K_POW, design_used="stack")),
    "another ground": SD.seed_for_key([EID_A], dict(K_POW, bg="universe")), "the clean flag": SD.seed_for_key([EID_A], dict(K_POW, clean=True)),
    "another layout": SD.seed_for_key([EID_A], dict(K_POW, layout="pair")), "an option": SD.seed_for_key([EID_A], dict(K_POW, opts={"swap": 1, "rotate": None, "look": None})),
    "another plates version": SD.seed_for_key([EID_A], dict(K_POW, pv=K_POW["pv"] + 1))}
check("another eye id, a second eye, the eyes in another order, another style id, design used, ground, clean flag, layout, option or plates version each give another seed (and all are different)",
      s_pow not in variants.values() and len(set(variants.values())) == len(variants), variants)
check("an option left unset is the same as not mentioned (the key has all three options, None when unset), and a bool for the clean flag is read as a bool",
      SD.seed_for_key([EID_A], dict(K_POW, opts={})) == s_pow and SD.seed_for_key([EID_A], dict(K_POW, clean=0)) == s_pow)
refusals = {"no eyes": lambda: SD.seed_for_key([], K_POW), "an eye id that is not 16 hex digits": lambda: SD.seed_for_key(["xyz"], K_POW), "upper case hex": lambda: SD.seed_for_key(["0123456789ABCDEF"], K_POW),
            "an eye id that is a number": lambda: SD.seed_for_key([1234567890123456], K_POW), "eyes that are one text": lambda: SD.seed_for_key(EID_A, K_POW),
            "a key that is not a dict": lambda: SD.seed_for_key([EID_A], "powder"), "an unknown field": lambda: SD.seed_for_key([EID_A], dict(K_POW, names="Anna")),
            "a missing field": lambda: SD.seed_for_key([EID_A], {k: v for k, v in K_POW.items() if k != "pv"}), "a pv that is a bool": lambda: SD.seed_for_key([EID_A], dict(K_POW, pv=True)),
            "a negative pv": lambda: SD.seed_for_key([EID_A], dict(K_POW, pv=-1)), "an option that is not one of the three": lambda: SD.seed_for_key([EID_A], dict(K_POW, opts={"names": "x"})),
            "an option that is a list": lambda: SD.seed_for_key([EID_A], dict(K_POW, opts={"look": ["a"]})), "an empty style": lambda: SD.seed_for_key([EID_A], dict(K_POW, style=""))}
bad_ref = [k for k, f in refusals.items() if not isinstance(raises(f, ValueError), ValueError)]
check("seed_for_key refuses what is not a seed: " + ", ".join(refusals), not bad_ref, bad_ref)
check("the eye of an Iris made from bytes has the id of its bytes (the first 16 hex digits of their sha256: the id an order-kind seal of those bytes carries), a given id is kept, and render() "
      "refuses an eye whose id is not a valid one rather than seed a guess",
      C.Iris(FIX["blue_round"]).eye_id == hashlib.sha256(FIX["blue_round"]).hexdigest()[:16] == EYE.eye_id_of(FIX["blue_round"]) and C.Iris(FIX["blue_round"], eye_id=EID_A).eye_id == EID_A
      and isinstance(raises(lambda: S.render("clean", C.Iris(FIX["blue_round"], eye_id="not-an-id"), "1:1", 64), ValueError), ValueError))

# nothing but the eyes and the key is in the seed
eye_b = C.Iris(FIX["blue_round"], "b")
seeds_same = {(f, s, n, d): S.render("powder", eye_b, f, s, n, d).info["seed"] for f, s, n, d in (("1:1", 256, "", ""), ("1:1", 512, "Anna Max", "12 May 2026"), ("4:5", 256, "Anna", ""),
                                                                                              ("9:19.5", 256, "", "2026"))}
check("the seed does not depend on the names, the date, the canvas ratio or the size of the canvas: four renders of one eye (1:1, 4:5 and the wallpaper, 256 and 512 px, with and without "
      "names and a date) have one seed, so a typo in a name can never reshuffle the powder", len(set(seeds_same.values())) == 1 and next(iter(seeds_same.values())) == SD.seed_for_key([eye_b.eye_id], K_POW), seeds_same)
raw_b = FIX["blue_round"]
small = io.BytesIO()
Image.open(io.BytesIO(raw_b)).convert("RGB").resize((768, 768), Image.LANCZOS).save(small, "JPEG", quality=88)
eA, eB = C.Iris(raw_b, "a", eye_id=EID_A), C.Iris(small.getvalue(), "b", eye_id=EID_A)
rA, rB = S.render("powder", eA, "1:1", 256), S.render("powder", eB, "1:1", 256)
rC = S.render("powder", C.Iris(raw_b, "c", eye_id=EID_B), "1:1", 256)
check("the seed does not depend on the pixels or the bytes the eye arrives in: the 1024 px preview and a 768 px copy of the same eye (the same id) draw the same seed and the same plate, and "
      "the same pixels under another eye id draw another seed (the preview, the draft and the master of one eye all carry the eye id of the sealed preview)",
      rA.info["seed"] == rB.info["seed"] and rA.ctx.log["powder"]["plate"] == rB.ctx.log["powder"]["plate"] and rA.info["seed"] != rC.info["seed"] and eA.digest != eB.digest, (rA.info["seed"], rB.info["seed"], rC.info["seed"]))
r_leg = S.render("powder", eye_b, "1:1", 256, opts={"seed_mode": "legacy"})
check("the old seed is still one switch away for the laboratory's before and after look: opts seed_mode legacy seeds from the iris bytes, the design and the frame key (the prototype's formula), "
      "and the new seed is not that number", r_leg.info["seed"] == C.seed_for(FIX["blue_round"], 0, "powder", "single/1:1") != seeds_same[("1:1", 256, "", "")], r_leg.info["seed"])

# resolve names the seed and the plates, and the render draws what it names
PROF = {e: EYE.profile_of_bytes(FIX[e], rules=("lid",)) for e in SC.EYES}
IDS = {e: PROF[e].eye_id for e in SC.EYES}
rows, bad = [], []
for style, design in (("solo.powder", "powder"), ("solo.splash", "splash"), ("solo.clean", "clean"), ("solo.radiance", "radiance"), ("solo.gold", "gold")):
    for e in SC.EYES:
        for fmt in ("1:1", "9:19.5"):
            plan = ST.resolve({"style": style, "eyes": 1, "canvas": fmt}, [PROF[e]])
            pv_ = ST.preview([C.Iris(FIX[e], e)], {"style": style, "eyes": 1, "canvas": fmt, "profiles": [PROF[e]]}, size=256)
            rows.append((style, e, fmt, plan["plates"], pv_.log["plates"], plan["seed"], str(pv_.seed)))
            if not (plan["seed"] == str(pv_.seed) and plan["plates"] == pv_.log["plates"] and plan["eye_ids"] == [IDS[e]] and plan["plates"] is not None
                    and (len(plan["plates"]) == (1 if design in ("powder", "splash") else 0))):
                bad.append(rows[-1])
check("resolve names the seed and the plates before the render and the render draws exactly those: five styles x three eye classes x the square and the wallpaper (30 pictures at 256 px) "
      "have the plan's seed and the plan's plate (none, for the three styles that draw none)", len(rows) == 30 and not bad, bad[:3])
plan_rec = ST.resolve({"style": "solo.splash", "eyes": 1}, [PROF["blue_round"].rec])
plan_obj = ST.resolve({"style": "solo.splash", "eyes": 1}, [PROF["blue_round"]])
plan_ids = ST.resolve({"style": "solo.powder", "eyes": 1, "eye_ids": [IDS["blue_round"]]}, None)
plan_none = ST.resolve({"style": "solo.splash", "eyes": 1, "eye_ids": [IDS["blue_round"]]}, None)
plan_junk = ST.resolve({"style": "solo.splash", "eyes": 1, "eye_ids": [IDS["blue_round"]]}, [{"eye_id": IDS["blue_round"], "cls": "own"}])
plan_badid = ST.resolve({"style": "solo.powder", "eyes": 1, "eye_ids": ["short"]}, None)
check("resolve reads the eye from the record dict a draft keeps as from an EyeProfile; a powder needs only the eye id (spec eye_ids), a splash also the profile (its liquid): with no profile the "
      "plates stay unknown (None) and nothing is frozen, an unreadable profile is no profile, an id that is not 16 hex digits is no id",
      plan_rec == plan_obj and plan_rec["plates"] and plan_rec["frozen"].get("liquid") and plan_ids["plates"] and len(plan_ids["plates"]) == 1 and plan_ids["seed"] is not None
      and plan_none["plates"] is None and plan_none["frozen"] == {} and plan_none["seed"] is not None and plan_junk["plates"] is None and plan_junk["frozen"] == {}
      and plan_badid["seed"] is None and plan_badid["plates"] is None and plan_badid["eye_ids"] == [], (plan_rec["plates"], plan_none["plates"], plan_badid["eye_ids"]))
t0 = time.perf_counter()
for _ in range(20):
    ST.resolve({"style": "solo.splash", "eyes": 1}, [PROF["grey_round"].rec])
t_res = (time.perf_counter() - t0) / 20 * 1000
check("resolve with the eye, the seed, the pick of the plate and the frozen liquid takes a few milliseconds (at most 50)", t_res < 50, round(t_res, 1))
check("the plates a plan names are plates of the library a spec of its version may pick, with a 4K file for the two plate styles (checkout verifies those in storage)",
      all(PL.known(x) and PL.visible(PL.record(x), plan_rec["seed_key"]["pv"]) for x in plan_rec["plates"] + plan_ids["plates"]) and all(PL.record(x)["k4"] for x in plan_rec["plates"] + plan_ids["plates"]))


# what the plan freezes
class FakeProf:
    def __init__(self, cls, h, c):
        self.eye_id = EID_A
        self.stats = {"class": cls, "h": h, "C": c, "L": 50.0, "mean_rgb": [90.0, 90.0, 90.0]}


from _lib.styles.singles import splash as SPL  # noqa: E402
lq = {k: S.frozen_for("splash", FakeProf(*v)).get("liquid") for k, v in {"dark brown": ("dark_brown", 60.0, 30.0), "grey": ("grey", 200.0, 5.0), "teal (hue 177.9)": ("own", 177.9, 30.0),
                                                                          "clear (hue 178.0)": ("own", 178.0, 30.0), "olive": ("own", 120.0, 30.0), "amber": ("own", 60.0, 40.0)}.items()}
check("the liquid of a splash is fixed from the profile's numbers by the very function the render uses (class and hue thresholds of the brief): cognac, clear, teal below hue 178, clear above, tea olive, "
      "amber; a design that fixes nothing and a profile that is not known freeze nothing",
      lq == {"dark brown": "cognac", "grey": "water_clear", "teal (hue 177.9)": "water_teal", "clear (hue 178.0)": "water_clear", "olive": "tea_olive", "amber": "whisky_amber"}
      and S.frozen_for("powder", FakeProf("own", 60.0, 30.0)) == {} and S.frozen_for("splash", None) == {} and SPL.liquid_from_stats({"class": "own", "h": 120.0, "C": 30.0}) == "tea_olive", lq)
eye_s = C.Iris(FIX["blue_round"], "s")
own_liquid = SPL.liquid_for(eye_s)
pk_a = S.render("splash", eye_s, "1:1", 128)
pk_f = S.render("splash", eye_s, "1:1", 128, frozen={"liquid": "cognac"})
check("what the plan froze wins over what the eye measures: the same eye draws a crown plate of the frozen liquid (cognac) instead of its own, and the laboratory's liquid option still wins over both",
      pk_a.ctx.log["splash"]["liquid"] == own_liquid != "cognac" and pk_f.ctx.log["splash"]["liquid"] == "cognac"
      and PL.record(pk_f.ctx.log["splash"]["plate"])["variables"]["liquid"] == "cognac" and PL.record(pk_a.ctx.log["splash"]["plate"])["variables"]["liquid"] == own_liquid
      and S.render("splash", eye_s, "1:1", 128, opts={"liquid": "tea_olive"}, frozen={"liquid": "cognac"}).ctx.log["splash"]["liquid"] == "tea_olive", (own_liquid, pk_a.ctx.log["splash"]["liquid"]))
tl2 = ST.tiles([eye_s], ["solo.splash", "solo.powder"], {"style": "solo.splash", "eyes": 1, "frozen": {"liquid": "cognac"}, "profiles": [PROF["blue_round"]]}, size=128)
check("a batch of tiles takes the frozen choices of each style from the profiles and never the spec's own frozen (that belongs to one style): the splash tile ignores the cognac of the spec and "
      "draws the liquid the profile gives", tl2["solo.splash"].log["splash"]["liquid"] == plan_rec["frozen"]["liquid"] != "cognac" and tl2["solo.powder"].log["plates"] == [tl2["solo.powder"].log["powder"]["plate"]])

# the plates version of the spec reaches every pick
calls = []
real_plates = PL.plates
with mock.patch.object(PL, "plates", lambda family, pv=None, **kw: calls.append((family, pv)) or real_plates(family, pv, **kw)):
    ST.preview([C.Iris(FIX["blue_round"], "p")], {"style": "solo.powder", "eyes": 1, "pv": 1}, size=128)
    ST.preview([C.Iris(FIX["blue_round"], "p")], {"style": "solo.splash", "eyes": 1, "pv": 1}, size=128)
    ST.preview([C.Iris(FIX["blue_round"], "p")], {"style": "solo.elements", "eyes": 1, "pv": 1}, size=128)
    ST.resolve({"style": "solo.powder", "eyes": 1, "pv": 1, "eye_ids": [EID_A]}, None)
check("every plate pick of a render and of resolve is asked with the spec's plates version: the cloud, the crown and the flame are asked with pv 1, and the only call without one is Elements' list of "
      "plates to leave out (the v2 flames, which no version may pick)",
      {f for f, v in calls if v == 1} >= {"P-SN-CLOUD", "P-SP-CROWN", "P-EL-FLAME"} and [c for c in calls if c[1] != 1] == [("P-EL-FLAME", None)], calls)
POW = __import__("_lib.styles.singles.powder", fromlist=["x"])
allowed = POW.WIND_SETS["square"]
picked = {}
for sd_ in range(200):
    picked.setdefault(POW.pick_cloud(sd_, allowed, pv=CT.PLATES_VERSION).plate.id, sd_)
some_id, some_seed = next(iter(picked.items()))
rec_ = PL._TABLE[some_id]
old_since = rec_["since"]
try:
    rec_["since"] = CT.PLATES_VERSION + 1
    before = POW.pick_cloud(some_seed, allowed, pv=CT.PLATES_VERSION).plate.id
    after_v = POW.pick_cloud(some_seed, allowed, pv=CT.PLATES_VERSION + 1).plate.id
    never = {POW.pick_cloud(sd_, allowed, pv=CT.PLATES_VERSION).plate.id for sd_ in range(200)}
finally:
    rec_["since"] = old_since
check("a plate that arrives later never changes the pick of an older plates version: with a plate's `since` raised past the spec's pv it is picked by no seed of 200 (its seed used to pick it), and a "
      "spec of the newer version can pick it again", some_id not in never and before != some_id and after_v == some_id, (some_id, before, after_v))

# the statistical rules over many seeds (the seed re-rolled every plate, wind and particle: the rules are not a property of three lucky eyes)
SW_BAD, SW_BLACK, SW_VEIL = [], {"powder": [], "elements": []}, []
t0 = time.time()
sweep_eyes = {e: C.Iris(FIX[e], e) for e in SC.EYES}
for k_ in range(4):
    for e, ir_ in sweep_eyes.items():
        ir_.eye_id = hashlib.sha256(f"sweep|{k_}|{e}".encode()).hexdigest()[:16]
        for design in ("powder", "splash", "elements", "radiance", "gold"):
            r_ = S.render(design, ir_, "1:1", 512, "Anna", "")
            rep = SCK.run(np.asarray(r_.img), [r_.d], text_log=r_.log, customer=["Anna", ""], ids=[design, "single"])
            if not rep["ok"]:
                SW_BAD.append((design, e, k_, {kk: v["ok"] for kk, v in rep["checks"].items()}))
        for design in SW_BLACK:                                  # T4 is the picture's own at 1024 px, with no text (the golden checks measure it so)
            r_ = S.render(design, ir_, "1:1", 1024)
            SW_BLACK[design].append(SCK.black_share(np.asarray(r_.img)))
            if design == "powder":
                SW_VEIL.append((r_.ctx.log.get("veil_mean_alpha"), r_.ctx.log.get("veil_max_alpha")))
print(f"   (sweep in {time.time() - t0:.0f} s; black share at 1024 px: powder {min(SW_BLACK['powder']):.3f} to {max(SW_BLACK['powder']):.3f}, "
      f"elements {min(SW_BLACK['elements']):.3f} to {max(SW_BLACK['elements']):.3f}; veil mean alpha up to {max(m for m, _ in SW_VEIL):.3f})", flush=True)
check("T1, T6, T7 and T12 hold on 60 pictures of 5 designs x 3 eye classes x 4 other seeds (512 px with a name): the iris is the graded iris byte for byte whatever the seed",
      not SW_BAD, SW_BAD[:3])
check("T4 and the veil over those seeds, at 1024 px with no text: the black share of Powder Burst stays inside 45 to 65 percent and Elements inside 55 to 75 on all 12 pictures each, the veil's "
      "mean alpha is at most 0.10 and no pixel of it above 0.6",
      all(0.45 <= v <= 0.65 for v in SW_BLACK["powder"]) and all(0.55 <= v <= 0.75 for v in SW_BLACK["elements"]) and all(m <= 0.10 and x <= 0.6 + 1e-6 for m, x in SW_VEIL),
      (min(SW_BLACK["powder"]), max(SW_BLACK["powder"]), min(SW_BLACK["elements"]), max(SW_BLACK["elements"]), max(m for m, _ in SW_VEIL)))
picks_seen = {S.render("powder", C.Iris(FIX["blue_round"], "z", eye_id=hashlib.sha256(f"spread|{i}".encode()).hexdigest()[:16]), "1:1", 64).ctx.log["powder"]["plate"] for i in range(24)}
check("the new seed spreads the plate pick: 24 different eyes draw at least 6 different cloud plates (a seed that always picked the same plate would make every Powder Burst alike)", len(picks_seen) >= 6, len(picks_seen))

# the preview of /api/compose and the laboratory draw the plan's picture
prof_j = EYE.profile_of_bytes(jpeg, rules=("lid",))
sealed_p = P.protect(im_j, jpeg, profile=prof_j)["sealed"]
meta_p = P.unseal_full(sealed_p)[1]
with Show("solo.splash"), Show("solo.powder"):
    r_sp = CMP.compose({"sealed": [sealed_p], "style": "solo.splash", "pad": 1.12})
    r_pw = CMP.compose({"sealed": [sealed_p], "style": "solo.powder", "pad": 1.12})
    r_pl = CMP.compose({"sealed": [sealed], "style": "solo.splash", "pad": 1.12})
plan_p = ST.resolve({"style": "solo.splash", "eyes": 1, "eye_ids": [meta_p["eye_id"]]}, [meta_p["profile"]])
plan_w = ST.resolve({"style": "solo.powder", "eyes": 1, "eye_ids": [meta_p["eye_id"]]}, None)
exp_sp = ST.preview([C.Iris(jpeg, "compose", max_side=2048, eye_id=meta_p["eye_id"])], {"style": "solo.splash", "eyes": 1, "canvas": "1:1", "frozen": plan_p["frozen"]}, size=1024, watermark=True)
exp_pw = ST.preview([C.Iris(jpeg, "compose", max_side=2048, eye_id=meta_p["eye_id"])], {"style": "solo.powder", "eyes": 1, "canvas": "1:1"}, size=1024, watermark=True)
check("the preview a customer sees through /api/compose is the plan's picture: with a sealed profile the splash is drawn with the plan's frozen liquid and the powder from the seal's eye id, "
      "byte for byte what a master of the same plan would draw at this size (the plan's seed key, frozen choices and eye id)",
      r_sp["image"] == L.pil_to_b64(exp_sp.img, "JPEG", 90) and r_pw["image"] == L.pil_to_b64(exp_pw.img, "JPEG", 90) and r_sp["eyes"][0]["eye_id"] == meta_p["eye_id"]
      and str(exp_sp.seed) == plan_p["seed"] and exp_sp.log["plates"] == plan_p["plates"] and exp_pw.log["plates"] == plan_w["plates"], (plan_p["plates"], exp_sp.log["plates"]))
check("a sealed eye with no profile (a preview of the old kind, the gate unknown) is still drawn by the engine: the splash is drawn from what the render measures on the eye",
      r_pl["ok"] and r_pl["style"] == "solo.splash" and "canvas" in r_pl, r_pl.get("style"))
lab_new = ops.a_styles_lab({"style": "solo.powder", "eye": b64(jpeg), "size": 480}, "t")
lab_old = ops.a_styles_lab({"style": "solo.powder", "eye": b64(jpeg), "size": 480, "seed": "legacy"}, "t")
lab_same = ops.a_styles_lab({"style": "solo.powder", "eye": b64(jpeg), "size": 480, "seed": "eye_id"}, "t")
iris_l = C.Iris(jpeg, "lab", max_side=2048)
bad_seed = raises(lambda: ops.a_styles_lab({"style": "solo.powder", "eye": b64(jpeg), "size": 480, "seed": "random"}, "t"), L.ClientError)
check("the laboratory draws with the customer's seed by default (the eye's id is the hash of the image sent) and, when asked (seed legacy), with the old one for the owner's before and after look: "
      "two different pictures, the reply says which seed it used and the eye's id, the plan shows the seed and the plate, and any other value is a 400",
      lab_new["seed_mode"] == "eye_id" and lab_old["seed_mode"] == "legacy" and lab_new["image"] != lab_old["image"] and lab_new["image"] == lab_same["image"] and lab_new["eye_id"] == iris_l.eye_id
      and lab_new["seed"] == str(SD.seed_for_key([iris_l.eye_id], S.seed_key("solo.powder", "powder"))) and lab_new["plan"]["seed"] == lab_new["seed"] and lab_new["plan"]["plates"] == [lab_new["facts"]["powder"]["plate"]]
      and lab_old["seed"] == str(C.seed_for(jpeg, 0, "powder", "single/1:1")) and isinstance(bad_seed, L.ClientError), (lab_new["seed"], lab_old["seed"], bad_seed))
store.put("orders/lab-260101-abcd1234/eye_1.json", json.dumps({"eye_id": EID_B, "side": 4096}).encode(), "application/json", upsert=True)
by_order2 = ops.a_styles_lab({"style": "solo.powder", "order": "lab-260101-abcd1234", "n": 1, "size": 480}, "t")
check("a lab test order's eye takes the eye id of its stored record (the id of the preview the master was made from), so a style looked at on a real master has the seed of the order's picture",
      by_order2["eye_id"] == EID_B and by_order2["seed"] == str(SD.seed_for_key([EID_B], S.seed_key("solo.powder", "powder"))), (by_order2["eye_id"], by_order2["seed"]))
tsx2 = read(os.path.join(REPO, "src", "admin", "StyleLab.tsx"))
check("the admin page's laboratory has the switch: a Sėkla menu with the new seed and the old one for comparison, sent as seed, and the answer shows which was used",
      "Sėkla" in tsx2 and "'legacy'" in tsx2 and "seed," in tsx2 and "seed_mode" in tsx2 and not re.search(DASH, tsx2))

# ============================================================================================ 8. local only
section("8. the real calibration eyes and the port as the scratch plus its edits (local only)")
if CALIB and os.path.isdir(CALIB) and os.path.isfile(os.path.join(HERE, "data", "singles_goldens_real.json")):
    RG = json.load(open(os.path.join(HERE, "data", "singles_goldens_real.json"), encoding="utf-8"))
    fx = {}
    for n in SC.REAL_EYES:
        p_ = os.path.join(CALIB, f"{n}_2_enhanced.jpg")
        if os.path.isfile(p_):
            fx[n] = open(p_, "rb").read()
    same_files = {n: hashlib.sha256(b).hexdigest() == RG["eye_files"][n] for n, b in fx.items()}
    local(f"the {len(fx)} real eyes are the files of the recording (their hashes equal)", len(fx) == len(SC.REAL_EYES) and all(same_files.values()), same_files)
    RGA = json.load(open(os.path.join(HERE, "data", "stepA", "singles_goldens_real.json"), encoding="utf-8"))
    local("the step A recording of the real eyes (the scratch prototype's) was made from the very same eye files", RGA["eye_files"] == RG["eye_files"])
    irises = {}
    for design in S.DESIGNS:
        bad, bad_a = [], []
        for c in [c for c in SC.real_cases() if c["design"] == design]:
            rec = SC.render_case(lambda d, e, f, s, nm, dt: S.render(d, e, f, s, nm, dt), C.Iris, fx, c, irises)
            if rec["sha"] != RG["cases"][c["key"]]["sha"] or rec["facts"] != RG["cases"][c["key"]]["facts"]:
                bad.append(c["key"])
            rec_a = SC.render_case(legacy_render, C.Iris, fx, c, irises)
            if rec_a["sha"] != RGA["cases"][c["key"]]["sha"] or rec_a["facts"] != RGA["cases"][c["key"]]["facts"]:
                bad_a.append(c["key"])
        local(f"{design} on the four real eyes (own, own, dark brown, grey) at 1024 px equals the recorded pictures, byte for byte", not bad, str(bad) + NOTE)
        local(f"{design} on the four real eyes with the old seed equals the scratch prototype's pictures of step A, byte for byte", not bad_a, str(bad_a) + NOTE)
else:
    print("   (the real-eye goldens need SNAPEYES_CALIB, the folder of the calibration restorations)", flush=True)
if SCRATCH_Y3 and os.path.isdir(SCRATCH_Y3):
    pr = subprocess.run([sys.executable, os.path.join(HERE, "port_singles.py"), "--check"], capture_output=True, text=True, timeout=120,
                        env=dict(os.environ, SNAPEYES_SCRATCH_Y3=SCRATCH_Y3))
    local("the committed files of the family are what port_singles.py makes of the scratch files (the listed edits and nothing else)", pr.returncode == 0 and "DIFFERS" not in pr.stdout, pr.stdout[-400:] + pr.stderr[-300:])
else:
    print("   (the edit check needs SNAPEYES_SCRATCH_Y3, the wave-y3 folder of the scratch tree)", flush=True)

shutil.rmtree(TMP, ignore_errors=True)
ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed" + (f"   (+ {len(LOCAL)} local checks)" if LOCAL else ""))
sys.exit(0 if ok == len(RESULTS) and all(LOCAL) else 1)
