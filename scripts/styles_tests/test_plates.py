# -*- coding: utf-8 -*-
"""WP4 of the v3 engine work, the plate library, the bundle and storage (test I5, IE8, IE6 for the plate side, the bundle checks 8 to 10 and 12).

  1. the baked registry (api/_lib/plates_registry.py): sound, one version with the style registry, every usable plate's 1K file is in api/_assets/plates
     with the recorded size and sha256, nothing rides in unlisted, the two atlases are the files the registry names, the 4K files are the ones storage
     will hold; the engines' own pick replayed on the port gives the picks of the prototype's registry for 14 groups of cases
  2. the loader is read only: nothing at import or render writes under api/ (an audit hook blocks it in a child process); no fitting, no scan of a
     plate folder at run time
  3. append only: a plate added later never changes the pick of an older plates version, a retired plate still answers an old version and never a new
     one (IE8); a plate that is not usable is never picked
  4. the 4K plate: from storage with the sha256 and size checked, a missing, short or wrong object is PlateUnavailable and never another plate; the cache
     is written atomically (eight threads and two processes racing for one plate), capped with the least recently used out, used when storage is down,
     skipped when /tmp cannot be written; the decoded caches stay at two (the leak side of IE6)
  5. the atlases, the health probe (two booleans), the admin action plates_status
  6. scripts/upload_plates.py: a dry run writes nothing, a run uploads, a second run finds everything present, a wrong object is never overwritten, a
     source that is not the registry's file is refused
  7. the bundle checks: the real tree passes check_styles (items 8, 9, 10, 12) and each refusal is proved on a small copy of the tree with one change
No network, no image model, no real eye, no key: a local store folder and synthetic plates. Run by suites/run_main.sh as v3plates.
    python test_plates.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tracemalloc
import unittest.mock as mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
TMP = os.path.join(HERE, "wp4_tmp")
NODE = shutil.which("node") or "node"

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
if os.path.isdir(TMP):
    shutil.rmtree(TMP, ignore_errors=True)
os.makedirs(TMP)
atexit.register(shutil.rmtree, TMP, ignore_errors=True)   # its own folder only (store, plate cache): gone at exit, green, red or crashed
STORE = os.path.join(TMP, "store")
CACHE = os.path.join(TMP, "cache")
os.environ.update({"PYTHONIOENCODING": "utf-8", "SNAPEYES_TICKET_SECRET": "wp4-ticket-secret-for-tests-0123456789abcdef", "STYLE_PLATE_CACHE": CACHE,
                   "PYTHONDONTWRITEBYTECODE": "1"})
sys.path.insert(0, API)
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import plate_cases as PC  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import plates_registry as REG  # noqa: E402
from _lib import styles_registry as SR  # noqa: E402
from _lib import store  # noqa: E402
from _lib.styles import plates as P, atlas as A, core as C  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
TABLE = REG.PLATES_REGISTRY["plates"]
FAMS = REG.PLATES_REGISTRY["families"]
USABLE = {i: r for i, r in TABLE.items() if r["usable"]}
GOLD = json.load(open(os.path.join(HERE, "data", "plate_picks.json"), encoding="utf-8"))["cases"]


def read(rel, repo=REPO):
    with open(os.path.join(repo, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def raises(fn, exc):
    try:
        fn()
    except exc as e:
        return e
    except Exception as e:  # noqa: BLE001
        return repr(e)
    return False


@contextlib.contextmanager
def local_store(path=STORE):
    os.makedirs(path, exist_ok=True)
    with mock.patch.dict(os.environ, {"STORE_LOCAL_DIR": path}):
        yield


# ============================================================================================ 1. the baked registry
section("1. the baked library: sound, one version, the bundle is exactly it")
text = read("api/_lib/plates_registry.py")
lit = json.loads(text[text.index("\nPLATES_REGISTRY = ") + len("\nPLATES_REGISTRY = "):])
check("the registry is JSON inside Python (the literal ends the file and is what Python imports), ASCII, no dash, three constants of one line each",
      lit == REG.PLATES_REGISTRY and all(ord(c) < 128 for c in text) and not re.search(DASH, text)
      and all(re.search(rf"^{n} = ", text, re.M) for n in ("PLATES_REGISTRY_SCHEMA", "PLATES_VERSION", "DEPENDENCIES_MIB")))
check("the library has the version the style registry names, and the dependencies it was sized with are recorded (an estimate until V1)",
      REG.PLATES_VERSION == SR.PLATES_VERSION == CT.PLATES_VERSION and REG.PLATES_REGISTRY_SCHEMA == 1 and 100 <= REG.DEPENDENCIES_MIB < 235)
by_fam = {}
for i, r in TABLE.items():
    by_fam.setdefault(r["family"], []).append(r)
check("eight families, 221 plates, 169 usable: CLOUD 47, CROWN 60, FLAME 6 of 14 (the v3 flames), SPIRAL 10 of 16 (the crisp ones), DUST 7, MILKY 4 of 7 "
      "(three vetoed), JET 19 of 42 and RIVER 16 of 28 (the accept rules)",
      len(TABLE) == 221 and len(USABLE) == 169 and {f: (len(v), sum(x["usable"] for x in v)) for f, v in by_fam.items()} == {
          "P-SN-CLOUD": (47, 47), "P-SP-CROWN": (60, 60), "P-EL-FLAME": (14, 6), "P-DN-SPIRAL": (16, 10), "P-UV-DUST": (7, 7), "P-UV-MILKY": (7, 4),
          "P-CX-JET": (42, 19), "P-CX-RIVER": (28, 16)}, {f: (len(v), sum(x["usable"] for x in v)) for f, v in by_fam.items()})
engine_fams = {f for e in CT.ENGINE.values() for f in e["plates"]}
engine_atl = {a for e in CT.ENGINE.values() for a in e["atlas"]}
check("every plate family and atlas an engine entry of the style registry names is in the library", engine_fams <= set(FAMS) and engine_atl <= set(REG.PLATES_REGISTRY["atlas"]) and set(FAMS) >= engine_fams, (engine_fams - set(FAMS), engine_atl))
bundle = os.path.join(API, "_assets", "plates")
on_disk = {os.path.relpath(os.path.join(r, f), bundle).replace("\\", "/") for r, _d, fs in os.walk(bundle) for f in fs}
named = {f"{r['family']}/{r['k1']['file']}" for r in USABLE.values()}
check("the bundle holds exactly the 169 usable plates' 1K files and nothing else (no plate rides in unlisted, none is missing)", on_disk == named and len(named) == 169, (sorted(on_disk ^ named)[:4]))
bad = [i for i, r in USABLE.items() if os.path.getsize(os.path.join(bundle, r["family"], r["k1"]["file"])) != r["k1"]["bytes"]
       or sha(os.path.join(bundle, r["family"], r["k1"]["file"])) != r["k1"]["sha256"]]
check("every bundled 1K file has the size and the sha256 the registry records", not bad, bad[:3])
check("the 1K files are 1024 px, mono plates open as L and colour plates as RGB (the registry's mono flag is right)",
      all(Image.open(os.path.join(bundle, r["family"], r["k1"]["file"])).size == (1024, 1024) for r in list(USABLE.values())[::9])
      and all(P.load_1k(i).mode == ("L" if r["mono"] else "RGB") for i, r in list(USABLE.items())[::23]))
atl = REG.PLATES_REGISTRY["atlas"]
check("the two atlases are the files the registry names (chips md5 06de0f96 like the four copies of the prototype, 3806278 bytes; drops 3371063 bytes)",
      all(sha(os.path.join(API, "_assets", "atlas", a["file"])) == a["sha256"] and os.path.getsize(os.path.join(API, "_assets", "atlas", a["file"])) == a["bytes"] for a in atl.values())
      and hashlib.md5(open(os.path.join(API, "_assets", "atlas", "chips.npz"), "rb").read()).hexdigest().startswith("06de0f96") and atl["chips"]["bytes"] == 3806278 and atl["drops"]["bytes"] == 3371063)
k4 = {i: r for i, r in USABLE.items() if r["k4"]}
check("4K files: only in the families that keep them in storage, at most 16 MiB each, a valid store path each (segments of at most 80 characters), "
      "ids that start with their family", all(FAMS[r["family"]]["store4k"] and r["k4"]["bytes"] <= 16 << 20 and r["k4"]["px"] == 4096 and re.fullmatch(r"[0-9a-f]{64}", r["k4"]["sha256"]) for r in k4.values())
      and all(store._check_path(P.storage_path(i)) for i in k4) and all(i.startswith(r["family"] + "__") for i, r in TABLE.items()), [i for i in k4 if not FAMS[k4[i]["family"]]["store4k"]][:2])
rel1 = sum(r["k4"]["bytes"] for r in k4.values() if FAMS[r["family"]]["release1"]) / 1048576
check("what the first release must upload (CLOUD for Powder Burst, CROWN for Splash, SPIRAL for Vortex, DUST for the accent plate of Universe Echo on its tall canvas) is 413 MiB: "
      "the size V6 reads against the storage plan; the laboratory families (FLAME, MILKY) are not in it",
      405 < rel1 < 420 and {r["family"] for r in k4.values() if FAMS[r["family"]]["release1"]} == {"P-SN-CLOUD", "P-SP-CROWN", "P-DN-SPIRAL", "P-UV-DUST"}
      and not FAMS["P-EL-FLAME"]["release1"] and not FAMS["P-UV-MILKY"]["release1"], rel1)
check("a plate that is not usable keeps its record and ships no file; a plate without a void is never offered to place()", all(not r["k1"] and not r["k4"] for r in TABLE.values() if not r["usable"])
      and all("void" in r for r in USABLE.values() if r["family"] in ("P-SN-CLOUD", "P-SP-CROWN", "P-EL-FLAME", "P-DN-SPIRAL")))
check("the fits of the collision plates are full precision (the prototype read them unrounded): JET axis of the first plate", TABLE["P-CX-JET__medium_left_b60__flash1K__t0"]["fit"]["axis"] == -1.7105220328572195)

# the plates' pixels are what the registry says they are, and what they show is the plate and nothing else (no legend, no scale bar)
sys.path.insert(0, os.path.join(REPO, "scripts"))
import bake_plates_registry as BK  # noqa: E402


def lum_of(pid):
    r = TABLE[pid]
    return np.asarray(Image.open(os.path.join(bundle, r["family"], r["k1"]["file"])).convert("L"), np.float32) / 255.0


def fit_gap(pid, L):
    """The largest difference between the registry's fit of a collision plate and the fit of the pixels L (the fit functions of the design rounds)."""
    f = TABLE[pid]["fit"]
    new = BK.fit_jet(L) if TABLE[pid]["family"] == "P-CX-JET" else BK.fit_river(L)
    return max(abs(float(v) - float(f[k])) for k, v in new.items() if k != "fam")


gaps = {i: fit_gap(i, lum_of(i)) for i, r in USABLE.items() if r["family"] in ("P-CX-JET", "P-CX-RIVER")}
check("the fit of every collision plate (19 JET, 16 RIVER) is the fit of the pixels it ships, to 1e-9 (fit_jet and fit_river of the design rounds): a plate "
      "whose picture is changed after it was fitted would put the source point and the axis off its notch", len(gaps) == 35 and max(gaps.values()) < 1e-9, sorted(gaps.items(), key=lambda t: -t[1])[:3])
check("the retouched plates are the two the generator drew a legend on (a scale bar pair, three particle size icons with '(mm)'): each is registered, usable, "
      "and in the bundle", set(BK.RETOUCH) == {"P-CX-JET__medium_left_b75__pro4K__t2", "P-CX-JET__wide_right_b75__pro4K__t1"} and all(USABLE.get(i) for i in BK.RETOUCH)
      and all(TABLE[i]["family"] == "P-CX-JET" for i in BK.RETOUCH))
dirty = []
for pid, rects in BK.RETOUCH.items():
    Lr = lum_of(pid)
    for x0, y0, x1, y1 in rects:
        frame = np.zeros(Lr.shape, bool)
        frame[y0 - 1:y1 + 1, x0 - 1:x1 + 1] = True
        frame[y0:y1, x0:x1] = False
        if not (0 <= x0 < x1 <= 1024 and 1 <= y0 < y1 <= 1023 and x0 >= 1 and x1 <= 1023) or Lr[y0:y1, x0:x1].max() != 0 or Lr[frame].max() > 8 / 255:
            dirty.append((pid[-24:], (x0, y0, x1, y1), float(Lr[y0:y1, x0:x1].max()), float(Lr[frame].max())))
check("each retouch rectangle is inside the plate, black in the shipped file, and cut clean (the pixel frame around it is at most 8 of 255): no trace of the "
      "legend is left and no edge shows", not dirty, dirty)
# the proofs that these checks can fail: draw a scale bar and a "(mm)" style mark back into a retouched plate
lp = lum_of("P-CX-JET__wide_right_b75__pro4K__t1")
lp[996:1010, 790:830] = 0.38
check("a legend drawn back into the plate: its rectangle is no longer black, and the fit of the new pixels is not the registry's (sx moves by more than 0.001, the "
      "state the original plate was in: its source point was 1.8 percent of the width off)",
      lp[928:1018, 786:1010].max() > 0 and fit_gap("P-CX-JET__wide_right_b75__pro4K__t1", lp) > 0.001, fit_gap("P-CX-JET__wide_right_b75__pro4K__t1", lp))
check("the retouched plates still pass the collision accept rules, and the bake refuses a retouched plate that would not",
      all(BK.cx_qa(TABLE[i]["fit"]) for i in BK.RETOUCH) and "fails the collision accept rules after it" in read("scripts/bake_plates_registry.py"))
sheet_png, strip_png = os.path.join(TMP, "sheet.png"), os.path.join(TMP, "strips.png")
sh1 = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "plate_sheet.py"), "P-CX-JET", "--out", sheet_png, "--cell", "64", "--cols", "5"], capture_output=True, text=True, timeout=120)
sh2 = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "plate_sheet.py"), "P-CX-JET", "--out", strip_png, "--cell", "128", "--strips", "140", "--gain", "3"], capture_output=True, text=True, timeout=120)
check("scripts/plate_sheet.py (the curation tool: look at a sheet and at the brightened bottom strips of a family before baking it) makes a 5 x 4 sheet of the 19 JET "
      "plates and a strip sheet, and names every plate id", sh1.returncode == 0 and sh2.returncode == 0 and Image.open(sheet_png).size == (320, 256) and Image.open(strip_png).size == (512, 10 * 35)
      and sh1.stdout.count("P-CX-JET__") == 19 and "no usable plate" in subprocess.run([sys.executable, os.path.join(REPO, "scripts", "plate_sheet.py"), "P-NO-NONE", "--out", sheet_png], capture_output=True, text=True).stderr,
      (sh1.stderr[-300:], sh2.stderr[-300:], sh1.stdout[-200:]))
mine = PC.run_cases(P)
check("the pick of the prototype's registry replayed on the port: CLOUD with and without the black filter, with excludes, CROWN by liquid, FLAME, pick_n, "
      "and four placed 1K plates bit for bit (14 groups of cases, 100s of picks)", mine == GOLD, [k for k in GOLD if GOLD[k] != mine.get(k)][:5])

# ============================================================================================ 2. read only, no run time fitting
section("2. read only: nothing under api/ is written at import or render; no fitting, no scan")
child = r'''
import sys, os
API = sys.argv[1]
STORE = sys.argv[2]
root = os.path.normcase(os.path.abspath(API))
def hook(event, args):
    if event == "open":
        path, mode, flags = args
        if not isinstance(path, (str, bytes, os.PathLike)): return
        p = os.path.normcase(os.path.abspath(os.fsdecode(path)))
        write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        if write and p.startswith(root):
            raise RuntimeError("WRITE under api: " + p)
    elif event in ("os.rename", "os.remove", "os.mkdir", "os.rmdir", "shutil.copyfile", "shutil.move", "os.truncate", "os.chmod", "os.utime"):
        for a in args:
            if isinstance(a, (str, bytes, os.PathLike)) and os.path.normcase(os.path.abspath(os.fsdecode(a))).startswith(root):
                raise RuntimeError(event + " under api: " + str(a))
sys.addaudithook(hook)
sys.path.insert(0, API)
os.environ["STORE_LOCAL_DIR"] = STORE
from _lib.styles import core, layouts, text, plates, atlas, costs, selfcheck
import _lib.styles as S
pk = plates.pick("P-SN-CLOUD", 7, 60.0)
arr, info = pk.place(512, 512, 256.0, 256.0, 110.0, lod="1k", strict=False)
pk2 = plates.pick("P-SP-CROWN", 5, 90.0, max_rotation=30.0, liquid="cognac")
pk2.plate.image("1k")
atlas.chips(); atlas.drops()
plates.health(); plates.bundle_status(); plates.storage_status(["P-EL-FLAME"])
print("OK", info["lod"])
'''
cp = subprocess.run([sys.executable, "-c", child, API, STORE], capture_output=True, text=True, timeout=300)
check("import, pick, place, 1K and atlas loads, the status probes: no open for writing, rename, remove, mkdir or copy under api/ (audit hook in a child process)",
      cp.returncode == 0 and "OK" in cp.stdout, (cp.stdout[-200:], cp.stderr[-500:]))
src_plates = read("api/_lib/styles/plates.py") + read("api/_lib/styles/atlas.py")
check("no glob, walk or scandir and no fit (linalg, eigh, moments) in the loader; the one directory listing is the cache folder's (_evict)",
      not re.search(r"\bglob\b|os\.walk|scandir|linalg|\beigh\b|_fit\b", src_plates) and len(re.findall(r"os\.listdir", src_plates)) == 1
      and re.search(r"def _evict\(.*?os\.listdir", src_plates, re.S) is not None)
import ast  # noqa: E402
calls = {getattr(n.func, "id", "") for n in ast.walk(ast.parse(read("api/_lib/styles/plates.py"))) if isinstance(n, ast.Call)}
check("the pick is the prototype's rule: min over sha256(seed | family | plate id), never Python's salted hash()", "def _seed_int" in src_plates and "hashlib.sha256" in src_plates and "hash" not in calls)

# ============================================================================================ 3. append only (IE8)
section("3. append only: since, until and the plates version of a spec")
base_pick = P.pick("P-SN-CLOUD", 12345, 60.0)
pid0 = base_pick.plate.id
newrec = dict(TABLE[pid0], since=2, until=0)
many = {f"P-SN-CLOUD__strong-up_black-45__v9__pro4K__t{i}": dict(TABLE[pid0], since=2) for i in range(1, 60)}
with mock.patch.dict(P._TABLE, many):
    same_v1 = [P.pick("P-SN-CLOUD", s, 60.0, pv=1).plate.id for s in range(40)]
    v2_ids = {P.pick("P-SN-CLOUD", s, 60.0, pv=2).plate.id for s in range(40)}
base_ids = [P.pick("P-SN-CLOUD", s, 60.0, pv=1).plate.id for s in range(40)]
check("a plate added in version 2 never changes a pick of version 1 (59 plates added: 40 seeds, the same plate each)", same_v1 == base_ids and not any("__v9__" in i for i in same_v1))
check("... and version 2 does pick the new plates (the library did change for them)", any("__v9__" in i for i in v2_ids), sorted(v2_ids)[:3])
retired = {pid0: dict(TABLE[pid0], until=2)}
with mock.patch.dict(P._TABLE, retired):
    old = P.pick("P-SN-CLOUD", 12345, 60.0, pv=1).plate.id
    new = {P.pick("P-SN-CLOUD", s, 60.0, pv=2).plate.id for s in range(60)}
check("a retired plate (until 2) still answers version 1 with the same pick and is never picked by version 2", old == pid0 and pid0 not in new, (old, pid0))
with mock.patch.dict(P._TABLE, {pid0: dict(TABLE[pid0], usable=0)}):
    nz = {P.pick("P-SN-CLOUD", s, 60.0).plate.id for s in range(120)}
check("a plate that is not usable is never picked, at any version", pid0 not in nz and pid0 in {P.pick("P-SN-CLOUD", s, 60.0).plate.id for s in range(120)})
check("the visible window: since inclusive, until exclusive, usable required; the default is the library's version",
      P.visible(dict(TABLE[pid0], since=2), 1) is False and P.visible(dict(TABLE[pid0], since=2), 2) is True and P.visible(dict(TABLE[pid0], until=2), 2) is False
      and P.visible(dict(TABLE[pid0], until=2), 1) is True and P.visible(TABLE[pid0]) is True and P.families(1) == P.families())
check("nothing matches: NoPlate; the plates of a family are listed best score first with the id as the tie break", raises(lambda: P.pick("P-SN-CLOUD", 1, black="nope"), P.NoPlate) is not False
      and [p.id for p in P.plates("P-SN-CLOUD")] == sorted([p.id for p in P.plates("P-SN-CLOUD")], key=lambda i: (-(TABLE[i]["score"] or 0), i)))

# ============================================================================================ 4. the 4K plate
section("4. the 4K plate: storage, the cache, the missing and the wrong plate")
SYN_ID = next(i for i, r in k4.items() if r["family"] == "P-SP-CROWN")
png = io.BytesIO()
Image.fromarray(np.random.default_rng(3).integers(0, 255, (96, 96, 3), dtype=np.uint8)).save(png, "WEBP", lossless=True)
SYN = png.getvalue()
syn_rec = dict(TABLE[SYN_ID], k4={"file": "syn.webp", "bytes": len(SYN), "sha256": hashlib.sha256(SYN).hexdigest(), "px": 4096})
SYN_PATH = "plates/v1/P-SP-CROWN/syn.webp"


def stored(data, path=SYN_PATH):
    p = os.path.join(STORE, *path.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(data)


def clean_state():
    P.clear_memory()
    shutil.rmtree(CACHE, ignore_errors=True)
    shutil.rmtree(STORE, ignore_errors=True)
    os.makedirs(STORE)


with local_store(), mock.patch.dict(P._TABLE, {SYN_ID: syn_rec}):
    clean_state()
    e = raises(lambda: P.fetch_4k(SYN_ID), P.PlateUnavailable)
    check("a 4K plate that is not in storage is PlateUnavailable(missing) and names the plate; nothing else is returned in its place",
          isinstance(e, P.PlateUnavailable) and e.why == "missing" and e.plate_id == SYN_ID and SYN_ID in str(e), e)
    stored(SYN[:-5])
    P.clear_memory()
    e = raises(lambda: P.fetch_4k(SYN_ID), P.PlateUnavailable)
    check("a short object is PlateUnavailable(size)", isinstance(e, P.PlateUnavailable) and e.why == "size", e)
    bad_obj = bytearray(SYN)
    bad_obj[40] ^= 1
    stored(bytes(bad_obj))
    P.clear_memory()
    e = raises(lambda: P.fetch_4k(SYN_ID), P.PlateUnavailable)
    check("an object of the right size and the wrong bytes is PlateUnavailable(sha256), and no file of it reaches the cache", isinstance(e, P.PlateUnavailable) and e.why == "sha256"
          and not (os.path.isdir(CACHE) and os.listdir(CACHE)), (e, os.listdir(CACHE) if os.path.isdir(CACHE) else None))
    stored(SYN)
    P.clear_memory()
    im = P.fetch_4k(SYN_ID)
    check("the right object is decoded (RGB for a colour plate), cached under its hash, and the decoded plate is kept in memory",
          im.mode == "RGB" and im.size == (96, 96) and os.listdir(CACHE) == [syn_rec["k4"]["sha256"][:12] + ".webp"] and P.fetch_4k(SYN_ID) is im)
    P.clear_memory()
    with mock.patch.object(store, "get", side_effect=AssertionError("storage must not be asked")):
        im2 = P.fetch_4k(SYN_ID)
    check("with the plate in the cache, storage is not asked (a warm instance, or a storage that is down for a moment)", im2.size == (96, 96))
    shutil.rmtree(STORE)
    os.makedirs(STORE)
    P.clear_memory()
    check("... and a cache file of the wrong size is not trusted: the plate is fetched again (and is now missing)",
          (open(os.path.join(CACHE, os.listdir(CACHE)[0]), "ab").write(b"x") or True) and raises(lambda: P.fetch_4k(SYN_ID), P.PlateUnavailable) is not False)
    # a cache file of the right size and the wrong bytes (a disk fault, an edit) is not drawn from either: the object is fetched again and the cache healed
    clean_state()
    stored(SYN)
    P.clear_memory()
    P.fetch_4k(SYN_ID)
    cfile = os.path.join(CACHE, os.listdir(CACHE)[0])
    dmg = bytearray(open(cfile, "rb").read())
    dmg[40] ^= 1
    open(cfile, "wb").write(bytes(dmg))
    P.clear_memory()
    try:
        im4 = P.fetch_4k(SYN_ID)
    except Exception as ex_:  # noqa: BLE001  (a damaged file that was decoded raises here: the check below then fails instead of the suite)
        im4 = ex_
    healed = open(cfile, "rb").read() == SYN
    shutil.rmtree(STORE)
    os.makedirs(STORE)
    open(cfile, "wb").write(bytes(dmg))
    P.clear_memory()
    e = raises(lambda: P.fetch_4k(SYN_ID), P.PlateUnavailable)
    check("a cache file of the right size and the wrong bytes is not trusted (the hit is checked by sha256 too): the object is fetched again and the cache file is "
          "healed; with the object gone as well the plate is PlateUnavailable and the damaged file is never decoded", healed and getattr(im4, "size", None) == (96, 96)
          and isinstance(e, P.PlateUnavailable) and e.why == "missing", (healed, e))
    e = raises(lambda: P.fetch_4k(next(i for i, r in USABLE.items() if not r["k4"])), P.PlateUnavailable)
    check("a plate the registry holds no 4K file of is PlateUnavailable(no_4k): a master never invents one", isinstance(e, P.PlateUnavailable) and e.why == "no_4k", e)
    # two writers: eight threads and two processes race for one uncached plate
    clean_state()
    stored(SYN)
    outs, errs = [], []

    def worker():
        try:
            outs.append(P._read_4k(SYN_ID, syn_rec))
        except Exception as ex:  # noqa: BLE001
            errs.append(repr(ex))
    ths = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in ths]
    [t.join() for t in ths]
    pcode = ("import sys, os; sys.path.insert(0, %r); os.environ['STORE_LOCAL_DIR'] = %r; os.environ['STYLE_PLATE_CACHE'] = %r; "
             "from _lib.styles import plates as P; rec = dict(P._TABLE[%r], k4=%r); d = P._read_4k(%r, rec); import hashlib; print(hashlib.sha256(d).hexdigest())") % (
        API, STORE, CACHE, SYN_ID, syn_rec["k4"], SYN_ID)
    procs = [subprocess.Popen([sys.executable, "-c", pcode], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    pouts = [p.communicate(timeout=120) for p in procs]
    left = sorted(os.listdir(CACHE))
    check("eight threads and two processes racing for one uncached plate all get the right bytes, no .part file is left, one file is in the cache (atomic write)",
          not errs and all(o == SYN for o in outs) and len(outs) == 8 and all(o[0].strip() == hashlib.sha256(SYN).hexdigest() for o in pouts)
          and left == [syn_rec["k4"]["sha256"][:12] + ".webp"], (errs, [o[1][-200:] for o in pouts], left))
    # the cap: the least recently used out, the file just written stays
    shutil.rmtree(CACHE)
    os.makedirs(CACHE)
    now = time.time()
    for k in range(5):
        fp = os.path.join(CACHE, f"f{k}.png")
        open(fp, "wb").write(b"z" * (3 << 20))
        os.utime(fp, (now - 100 + k * 10, now - 100 + k * 10))
    open(os.path.join(CACHE, "g.part"), "wb").write(b"p" * 10)
    P._evict(os.path.join(CACHE, "f0.png"), 8 << 20)
    left = sorted(os.listdir(CACHE))
    check("the cache cap (8 MiB here, 256 MiB by default): the least recently used files go first, the one just written stays even if it is the oldest, .part files are left alone",
          left == ["f0.png", "f4.png", "g.part"], left)
    with mock.patch.dict(os.environ, {"STYLE_PLATE_CACHE_MB": "1"}):
        cap_small = P._cache_cap()
    with mock.patch.dict(os.environ, {"STYLE_PLATE_CACHE_MB": "999999"}):
        cap_big = P._cache_cap()
    check("the cap comes from the environment, bounded (8 MiB to 4 GiB), 256 MiB by default", P._cache_cap() == 256 << 20 and cap_small == 8 << 20 and cap_big == 4096 << 20)
    with mock.patch.dict(os.environ, {"STYLE_PLATE_CACHE": ""}):
        import tempfile
        check("without STYLE_PLATE_CACHE the cache is /tmp/snapeyes_plates (the temp folder of the system)", P.cache_dir() == os.path.join(tempfile.gettempdir(), "snapeyes_plates"))
    # a /tmp that cannot be written
    clean_state()
    stored(SYN)
    blocker = os.path.join(TMP, "notadir")
    open(blocker, "w").write("x")
    with mock.patch.dict(os.environ, {"STYLE_PLATE_CACHE": os.path.join(blocker, "sub")}):
        P.clear_memory()
        im3 = P.fetch_4k(SYN_ID)
    check("a cache folder that cannot be made (read only or full /tmp) costs the cache, not the plate", im3.size == (96, 96))
    # needed(), missing_in_storage()
    clean_state()
    ids2 = [SYN_ID, next(i for i, r in k4.items() if r["family"] == "P-SN-CLOUD")]
    stored(SYN)
    nd = P.needed(ids2 + [next(i for i, r in USABLE.items() if not r["k4"])])
    check("needed() lists the 4K plates a plan will fetch (id, path, sha256, bytes) and leaves out a plate without one; missing_in_storage() asks the object itself",
          [n["id"] for n in nd] == ids2 and nd[0]["path"] == SYN_PATH and nd[0]["sha256"] == syn_rec["k4"]["sha256"] and P.missing_in_storage(ids2) == [ids2[1]], (nd, P.missing_in_storage(ids2)))
    # bounded decoded caches (the leak side of IE6)
    P.clear_memory()
    tracemalloc.start()
    m0 = tracemalloc.get_traced_memory()[0]
    for i in list(USABLE)[:60]:
        P.load_1k(i)
    grown = (tracemalloc.get_traced_memory()[0] - m0) / 1048576
    tracemalloc.stop()
    check("60 different 1K plates through load_1k keep two decoded in memory and the growth under 12 MiB (the caches are bounded)", len(P._IMG1) == 2 and grown < 12, (len(P._IMG1), grown))
    check("the decoded 4K cache holds two at most", (lambda c: [c.put(i, i) for i in range(9)] and len(c) == 2)(P._IMG4.__class__(2)) and P._IMG4.maxsize == 2 and P._IMG1.maxsize == 2)

# ============================================================================================ 5. atlas, health, admin action
section("5. the atlases, the health probe, the admin action plates_status")
A.clear()
ch = A.chips()
check("the chips atlas: 345 sprites of 128 px, lum and mask as float32 0..1, a meta table; mips of 64, 32 and 16 px by box reduction; readable as a dict too",
      ch.n == 345 and ch.lum.shape == (345, 128, 128) and ch.lum.dtype == np.float32 and 0 <= ch.lum.min() and ch.lum.max() <= 1 and ch.mask.shape == ch.lum.shape
      and ch.mip(64)[0].shape == (345, 64, 64) and ch.mip(16)[1].shape == (345, 16, 16) and np.allclose(ch.mip(64)[0][0, 0, 0], ch.lum[0, :2, :2].mean())
      and ch["n"] == 345 and ch["lum"] is ch.lum and ch.meta.shape[0] == 345)
check("the droplet atlas: 139 sprites of 128 px, uint8 RGB; each atlas is loaded once per process (the same object twice) and clear() lets go", A.drops().shape == (139, 128, 128, 3)
      and A.drops().dtype == np.uint8 and A.chips() is ch and A.drops() is A.drops() and (A.clear() or A._CHIPS is None and A._DROPS is None))
with mock.patch.dict(A._INFO, {"chips": dict(A._INFO["chips"], sha256="0" * 64)}):
    check("an atlas that is not the file the registry names is AtlasUnavailable (nothing is drawn with another)", raises(lambda: A._load("chips"), A.AtlasUnavailable) is not False)
with mock.patch.dict(A._INFO, {"drops": dict(A._INFO["drops"], file="nothere.npz")}):
    check("an atlas missing from the bundle (a function that excludes it) is AtlasUnavailable, not an OSError", raises(lambda: A._load("drops"), A.AtlasUnavailable) is not False)
check("status(): both atlases present", A.status() == {"ok": True, "atlases": {"chips": {"present": True, "bytes": 3806278}, "drops": {"present": True, "bytes": 3371063}}})
bs = P.bundle_status(deep=True)
check("bundle_status(deep): every usable plate present with its size and hash, per family", bs["ok"] and bs["missing"] == [] and sum(f["present"] for f in bs["families"].values()) == 169
      and bs["families"]["P-SN-CLOUD"]["usable"] == 47)
with mock.patch.dict(P._TABLE, {next(iter(USABLE)): dict(next(iter(USABLE.values())), k1=dict(next(iter(USABLE.values()))["k1"], bytes=1))}):
    bs2 = P.bundle_status()
check("... and a wrong size is reported by name (the status is a probe, never a raise)", not bs2["ok"] and len(bs2["missing"]) == 1)
check("no style that customers can see fetches a plate yet: nothing is expected of the bundle or of storage", P.expected_families() == set() and P.health() == {"styles": True, "plates_4k": True})
store_boom = mock.Mock(side_effect=AssertionError("no request while nothing is expected"))
fake_store = mock.Mock(configured=store_boom, exists=store_boom)
check("health() makes no storage request while nothing is expected (the public endpoint stays cheap)", P.health(store=fake_store) == {"styles": True, "plates_4k": True} and not store_boom.called)
with local_store(), mock.patch.object(P, "expected_families", return_value={"P-EL-FLAME"}):
    clean_state()
    h0 = P.health()
    flame = next(iter(P.storage_ids(["P-EL-FLAME"])))
    nm = P.storage_path(sorted(P.storage_ids(["P-EL-FLAME"]))[0])
    stored(b"x", nm)
    h1 = P.health()
check("health(): with a visible style that fetches FLAME plates, plates_4k is false while the sample is not in storage and true once it is (one existence request)",
      h0 == {"styles": True, "plates_4k": False} and h1 == {"styles": True, "plates_4k": True}, (h0, h1))
with mock.patch.object(P, "expected_families", return_value={"P-EL-FLAME"}):
    check("health(): storage not configured is false for plates_4k, and a broken storage never raises", P.health()["plates_4k"] is False
          and P.health(store=mock.Mock(configured=lambda: True, exists=mock.Mock(side_effect=RuntimeError("boom"))))["plates_4k"] is False)
with mock.patch.dict(P._FAMILIES, {}, clear=False), mock.patch.dict(CT.ENGINE, {"solo.powder": dict(CT.ENGINE["solo.powder"], plates=["P-XX-NONE"])}):
    check("health(): a style registry that names a plate family the library does not have is styles false", P.health()["styles"] is False)
import health as HEALTH  # noqa: E402
cap = {}
with mock.patch.object(L, "send_json", lambda req, code, info: cap.update(code=code, info=info)):
    HEALTH.handle(mock.Mock())
check("GET /api/health carries styles and plates_4k as booleans beside the old fields, and nothing else changed shape (booleans, a commit, a model name)",
      cap["code"] == 200 and cap["info"]["styles"] is True and cap["info"]["plates_4k"] is True and {"ok", "commit", "gemini_key", "stripe", "ordering", "legal", "sr_model"} <= set(cap["info"]),
      cap)
from _lib import ops  # noqa: E402
st = ops.ACTIONS["plates_status"]({}, "admin")
check("the admin action plates_status: the bundle, the atlases, the registry's hash and versions, the function's memory figures; ok; nothing stored is read",
      st["ok"] and st["bundle"]["ok"] and st["atlas"]["ok"] and st["registry"]["styles_hash"] == CT.registry_hash() and st["registry"]["usable"] == 169
      and st["registry"]["plates_version"] == st["registry"]["library_version"] == 1 and "storage" not in st and st["function"]["memory_budget_mb"] == 1434, st)
with local_store():
    clean_state()
    st2 = ops.ACTIONS["plates_status"]({"storage": True, "families": ["P-EL-FLAME"]}, "admin")
    st3 = ops.ACTIONS["plates_status"]({"storage": True}, "admin")
check("plates_status with storage: asks for the named families (default the first release's), names what is missing, and is not ok then", not st2["ok"] and len(st2["storage"]["missing"]) == 6
      and st2["storage"]["checked"] == 6 and not st3["ok"] and st3["storage"]["checked"] == len([1 for r in k4.values() if FAMS[r["family"]]["release1"]]), (st2["storage"], st3["storage"]["checked"]))
check("plates_status refuses a family that is not one (400 through L.ClientError) and is read only: it is not in the audited actions",
      raises(lambda: ops.ACTIONS["plates_status"]({"storage": True, "families": ["P-ZZ-NOPE"]}, "admin"), L.ClientError) is not False
      and "plates_status" in ops.ACTIONS and ops.ACTIONS["plates_status"].__name__ == "a_plates_status")

# ============================================================================================ 6. upload_plates.py
section("6. scripts/upload_plates.py: dry run, upload, idempotence, a wrong object, a bad source")
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("upload_plates", os.path.join(REPO, "scripts", "upload_plates.py"))
UP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(UP)
SRC = os.path.join(TMP, "src")
fam_dir = os.path.join(SRC, "plates_4k", "P-SN-CLOUD")
os.makedirs(fam_dir)
files = {}
for k in range(3):
    data = bytes(np.random.default_rng(10 + k).integers(0, 255, 5000 + k, dtype=np.uint8))
    name = f"P-SN-CLOUD__syn{k}.png"
    open(os.path.join(fam_dir, name), "wb").write(data)
    files[name] = data
mini = {f"P-SN-CLOUD__syn{k}": {"family": "P-SN-CLOUD", "usable": 1, "k4": {"file": f"P-SN-CLOUD__syn{k}.png", "bytes": len(files[f"P-SN-CLOUD__syn{k}.png"]),
                                                                       "sha256": hashlib.sha256(files[f"P-SN-CLOUD__syn{k}.png"]).hexdigest(), "px": 4096}} for k in range(3)}
mini["P-SN-CLOUD__nofile"] = {"family": "P-SN-CLOUD", "usable": 1, "k4": {"file": "nofile.png", "bytes": 10, "sha256": "0" * 64, "px": 4096}}
mini["P-SN-CLOUD__noK4"] = {"family": "P-SN-CLOUD", "usable": 1, "k4": {}}
mini["P-SP-CROWN__other"] = {"family": "P-SP-CROWN", "usable": 1, "k4": {"file": "o.webp", "bytes": 1, "sha256": "1" * 64, "px": 4096}}
lines = []
with local_store(os.path.join(TMP, "store_up")):
    rows = UP.plan(mini, {"P-SN-CLOUD"}, UP.sources(SRC, ""))
    check("plan(): the plates with a 4K file in the families asked for (not another family, not one without a 4K file); a plate whose source file is not found says no_source",
          [r["id"] for r in rows] == ["P-SN-CLOUD__nofile", "P-SN-CLOUD__syn0", "P-SN-CLOUD__syn1", "P-SN-CLOUD__syn2"] and rows[0]["why"] == "no_source" and all(r["why"] is None for r in rows[1:]), rows)
    good = [r for r in rows if not r["why"]]
    t0 = UP.run(good, store, yes=False, out=lines.append)
    check("a dry run writes nothing and counts what it would upload", t0["would"] == 3 and t0["uploaded"] == 0 and not os.path.exists(os.path.join(TMP, "store_up", "plates")), t0)
    t1 = UP.run(good, store, yes=True, out=lines.append)
    check("a run uploads every plate under plates/v1/<family>/<file>, byte for byte", t1["uploaded"] == 3 and all(store.get(r["path"]) == files[r["path"].rsplit("/", 1)[-1]] for r in good), t1)
    t2 = UP.run(good, store, yes=True, out=lines.append)
    check("a second run finds everything present and uploads nothing (idempotent)", t2["present"] == 3 and t2["uploaded"] == 0 and t2["wrong"] == 0, t2)
    os.remove(os.path.join(TMP, "store_up", "plates", "v1", "P-SN-CLOUD", "P-SN-CLOUD__syn1.png"))
    open(os.path.join(TMP, "store_up", "plates", "v1", "P-SN-CLOUD", "P-SN-CLOUD__syn1.png"), "wb").write(b"not the plate")
    t3 = UP.run(good, store, yes=True, out=lines.append)
    check("a stored object that is not the registry's file is reported WRONG and left as it is (upsert is off: a person looks at it)",
          t3["wrong"] == 1 and t3["present"] == 2 and store.get(good[1]["path"]) == b"not the plate" and any("WRONG" in l for l in lines), t3)
    bad_src = dict(mini["P-SN-CLOUD__syn2"], k4=dict(mini["P-SN-CLOUD__syn2"]["k4"], sha256="2" * 64))
    rows2 = UP.plan({"x": dict(bad_src)}, {"P-SN-CLOUD"}, UP.sources(SRC, ""))
    rows3 = UP.plan({"y": dict(mini["P-SN-CLOUD__syn2"], k4=dict(mini["P-SN-CLOUD__syn2"]["k4"], bytes=3))}, {"P-SN-CLOUD"}, UP.sources(SRC, ""))
    check("a source file that is not the file the registry names (wrong hash, wrong size) is refused before anything is sent", [r["why"] for r in rows2 + rows3] == ["sha256", "size"]
          and UP.run(rows2 + rows3, store, yes=True, out=lines.append)["bad_source"] == 2)
cli = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "upload_plates.py"), "--local-dir", os.path.join(TMP, "store_cli")], capture_output=True, text=True, timeout=120)
cli2 = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "upload_plates.py"), "--families", "P-CX-JET", "--local-dir", os.path.join(TMP, "store_cli")], capture_output=True, text=True, timeout=120)
cli3 = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "upload_plates.py"), "--release1", "--y2", os.path.join(TMP, "none"), "--local-dir", os.path.join(TMP, "store_cli")], capture_output=True, text=True, timeout=300)
check("the command line names the families (nothing is chosen by default), refuses a family without 4K files, and with no source folder reports every plate and exits 1; "
      "the dry run's last line says nothing was written", cli.returncode != 0 and "name the families" in (cli.stdout + cli.stderr) and cli2.returncode != 0 and "P-CX-JET" in (cli2.stdout + cli2.stderr)
      and cli3.returncode == 1 and "109 plates" in cli3.stdout and "dry run: nothing was written" in cli3.stdout and not os.path.exists(os.path.join(TMP, "store_cli", "plates")), (cli3.stdout[-400:], cli3.stderr[-300:]))
check("the script never reads or prints a key: it names no environment variable of the store", not re.search(r"SERVICE_KEY|GEMINI|os\.environ\.get|getenv", read("scripts/upload_plates.py")))

# ============================================================================================ 7. the bundle checks
section("7. check_styles items 8 to 10 and 12: the real tree passes, each refusal is proved on a small copy with one change")
rc = subprocess.run([NODE, "scripts/check_styles.mjs"], cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=300)
check("the real tree passes check_styles and the build log says what the library weighs (221 plates, 169 usable) and what a function would hold",
      rc.returncode == 0 and "plates ok: 221 plates, 169 usable" in rc.stdout and re.search(r"a rendering function \d+\.\d MiB and any other \d+\.\d MiB of 235", rc.stdout), (rc.stdout[-400:], rc.stderr[-400:]))
vj = json.loads(read("vercel.json"))
handlers = sorted(f[:-3] for f in os.listdir(API) if re.fullmatch(r"[^_.][^/]*\.py", f) and os.path.isfile(os.path.join(API, f)))
check("vercel.json: eleven entries, one per function of api/, no glob, one maxDuration, the plates and atlases excluded for the seven that never render and kept for compose, "
      "master_compose, order and admin; suites/** stays in every entry (the WP0 rule)",
      sorted(k[4:-3] for k in vj["functions"]) == handlers and len(handlers) == 11 and len({v["maxDuration"] for v in vj["functions"].values()}) == 1
      and all(("api/_assets/plates/**" in v["excludeFiles"]) == (k[4:-3] not in ("admin", "compose", "master_compose", "order")) for k, v in vj["functions"].items())
      and all("suites/**" in v["excludeFiles"] for v in vj["functions"].values()), list(vj["functions"]))
rep = subprocess.run([NODE, "scripts/bundle_report.mjs", "--json"], cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=300)
rj = json.loads(rep.stdout)
byname = {r["name"]: r for r in rj["rows"]}
check("bundle_report reads the new entries: the four rendering functions carry the plates (37.0 MiB) and the atlases (6.8 MiB), the other seven neither, every estimate is under the 235 MiB tripwire",
      all("api/_assets/plates" in byname[n]["api_mib"] and 36 < byname[n]["api_mib"]["api/_assets/plates"] < 38 for n in ("admin", "compose", "master_compose", "order"))
      and all("api/_assets/plates" not in byname[n]["api_mib"] for n in ("analyze", "checkout", "deglare", "enhance", "health", "master_eye", "stripe_webhook"))
      and all(r["estimate_mib"]["high"] < 235 for r in rj["rows"]) and rj["problems"] == [], [(r["name"], r["estimate_mib"]) for r in rj["rows"]][:2])


def make_tree(dst):
    """A small deployment tree: the real api (code, no assets), a synthetic plate library (three plates, two atlases, tiny files with true hashes), the tile images
    of every style the copied registry shows to customers (preview or live) as empty files, the real vercel.json and a deny list that holds the hash of one image
    the tree does not have. WP18: the styles are read from the registry FILE that was copied (the literal), not from the module in this process, which the pre-cutover
    world of this suite has put back the way it was before the switch."""
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    for d, ign in (("api", ("__pycache__", "_assets")), ("src", ("assets", "__pycache__")), ("scripts", ("__pycache__", "styles_tests"))):
        shutil.copytree(os.path.join(REPO, d), os.path.join(dst, d), ignore=shutil.ignore_patterns(*ign))
    for f in ("package.json", "vercel.json"):
        shutil.copy(os.path.join(REPO, f), os.path.join(dst, f))
    for rel in ("api/_assets/fonts",):
        shutil.copytree(os.path.join(REPO, *rel.split("/")), os.path.join(dst, *rel.split("/")))
    atel = os.path.join(dst, "public", "assets", "atelier")
    os.makedirs(atel)
    reg_text = open(os.path.join(dst, "api", "_lib", "styles_registry.py"), encoding="utf-8").read()
    for d in json.loads(reg_text[reg_text.index("\nSTYLES = {") + len("\nSTYLES = "):]).values():
        if any(s in ("preview", "live") for s in [d["stage"], *d["stage_by_eyes"].values()]):
            for w in (480, 800):
                open(os.path.join(atel, f"style-{d['slug']}-{w}.webp"), "wb").write(b"")
    plates, files_ = {}, []
    rng = np.random.default_rng(1)
    # WP18: every plate family a style shown to customers reads has a plate in the small tree (Universe reads SPIRAL, DUST and MILKY, the pair designs JET and RIVER)
    for fam, n, ext, mono in (("P-SN-CLOUD", 2, "webp", 1), ("P-SP-CROWN", 1, "webp", 0), ("P-CX-JET", 1, "png", 1), ("P-CX-RIVER", 1, "png", 1),
                              ("P-DN-SPIRAL", 1, "webp", 1), ("P-UV-DUST", 1, "webp", 1), ("P-UV-MILKY", 1, "webp", 1)):
        d = os.path.join(dst, "api", "_assets", "plates", fam)
        os.makedirs(d)
        for k in range(n):
            buf = io.BytesIO()
            Image.fromarray(rng.integers(0, 255, (32, 32), dtype=np.uint8) if mono else rng.integers(0, 255, (32, 32, 3), dtype=np.uint8)).save(buf, "WEBP" if ext == "webp" else "PNG")
            data = buf.getvalue()
            pid = f"{fam}__mini{k}"
            open(os.path.join(d, pid + "." + ext), "wb").write(data)
            rec = {"family": fam, "since": 1, "until": 0, "usable": 1, "mono": mono, "kind": "radial", "variables": {}, "score": 1.0,
                   "k1": {"file": pid + "." + ext, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "px": 1024}, "k4": {}}
            if fam not in ("P-CX-JET", "P-CX-RIVER") and k == 0:
                rec["k4"] = {"file": pid + "4k." + ext, "bytes": 1000, "sha256": "a" * 64, "px": 4096}
            plates[pid] = rec
    plates["P-SN-CLOUD__gone"] = {"family": "P-SN-CLOUD", "since": 1, "until": 0, "usable": 0, "mono": 1, "kind": "radial", "variables": {}, "score": 0.0, "k1": {}, "k4": {}}
    atlas = {}
    os.makedirs(os.path.join(dst, "api", "_assets", "atlas"))
    for key in ("chips", "drops"):
        buf = io.BytesIO()
        np.savez(buf, a=np.arange(10))
        open(os.path.join(dst, "api", "_assets", "atlas", key + ".npz"), "wb").write(buf.getvalue())
        atlas[key] = {"file": key + ".npz", "bytes": len(buf.getvalue()), "sha256": hashlib.sha256(buf.getvalue()).hexdigest()}
    lit_ = {"atlas": atlas, "families": REG.PLATES_REGISTRY["families"], "plates": plates}
    open(os.path.join(dst, "api", "_lib", "plates_registry.py"), "w", encoding="utf-8", newline="\n").write(
        "PLATES_REGISTRY_SCHEMA = 1\nPLATES_VERSION = 1\nDEPENDENCIES_MIB = 126\nPLATES_REGISTRY = " + json.dumps(lit_, indent=1, sort_keys=True) + "\n")
    os.makedirs(os.path.join(dst, "pics"))
    open(os.path.join(dst, "pics", "fine.png"), "wb").write(b"\x89PNG fine")
    deny = {hashlib.sha256(b"\x89PNG a reference work").hexdigest(): "wave-y3/ref/H10.png", hashlib.sha256(b"\x89PNG a calibration iris").hexdigest(): "wave-g/live/out/x_2_enhanced.jpg"}
    open(os.path.join(dst, "scripts", "hygiene_denylist.json"), "w").write(json.dumps({"sha256": deny}))
    return dst


def sub_file(root, rel, old, new):
    path = os.path.join(root, *rel.split("/"))
    t = open(path, encoding="utf-8", newline="").read()
    assert t.count(old) == 1, (rel, old[:60], t.count(old))
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new))


def sub_first(root, rel, old, new):
    path = os.path.join(root, *rel.split("/"))
    t = open(path, encoding="utf-8", newline="").read()
    assert old in t, (rel, old[:60])
    open(path, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))


def edit_registry(root, fn):
    p = os.path.join(root, "api", "_lib", "plates_registry.py")
    t = open(p, encoding="utf-8").read()
    i = t.index("PLATES_REGISTRY = ") + len("PLATES_REGISTRY = ")
    lit_ = json.loads(t[i:])
    fn(lit_)
    open(p, "w", encoding="utf-8", newline="\n").write(t[:i] + json.dumps(lit_, indent=1, sort_keys=True) + "\n")


def add_file(root, rel, data=b"x"):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(data)


def flip_byte(root, rel):
    p = os.path.join(root, *rel.split("/"))
    b = bytearray(open(p, "rb").read())
    b[len(b) // 2] ^= 1
    open(p, "wb").write(bytes(b))


def vj_edit(fn):
    def go(root):
        p = os.path.join(root, "vercel.json")
        d = json.load(open(p, encoding="utf-8"))
        fn(d)
        open(p, "w", encoding="utf-8").write(json.dumps(d, indent=2))
    return go


cases = [
    ("a plate's 1K file missing from the bundle", lambda r: os.remove(os.path.join(r, "api", "_assets", "plates", "P-SN-CLOUD", "P-SN-CLOUD__mini0.webp")), "the plate \"P-SN-CLOUD__mini0\" is in the registry and its 1K file is not in the bundle"),
    ("a plate's 1K file with one byte changed", lambda r: flip_byte(r, "api/_assets/plates/P-SN-CLOUD/P-SN-CLOUD__mini1.webp"), "not the file the registry names (sha256 differs)"),
    ("a plate's 1K file of another size", lambda r: add_file(r, "api/_assets/plates/P-SN-CLOUD/P-SN-CLOUD__mini1.webp", b"short"), "bytes, the registry says"),
    ("a file in the plate bundle that no plate names", lambda r: add_file(r, "api/_assets/plates/P-SN-CLOUD/stray.webp"), "a file in the plate bundle that no usable plate"),
    ("an atlas file replaced", lambda r: add_file(r, "api/_assets/atlas/chips.npz", b"other"), "not the file the registry names"),
    ("an atlas missing", lambda r: os.remove(os.path.join(r, "api", "_assets", "atlas", "drops.npz")), "the atlas \"drops\" is in the registry and its file is not in the bundle"),
    ("an unlisted file in the atlas folder", lambda r: add_file(r, "api/_assets/atlas/extra.npz"), "a file in the atlas bundle that"),
    ("the library's version not the registry's", lambda r: sub_file(r, "api/_lib/plates_registry.py", "PLATES_VERSION = 1", "PLATES_VERSION = 2"), "PLATES_VERSION 2 is not the registry's 1"),
    ("a plate of a family the library does not have", lambda r: edit_registry(r, lambda L_: L_["plates"].update({"P-ZZ-NONE__x": dict(L_["plates"]["P-SN-CLOUD__gone"], family="P-ZZ-NONE")})), "the family \"P-ZZ-NONE\" is not in families"),
    ("a plate with a field the schema does not know", lambda r: edit_registry(r, lambda L_: L_["plates"]["P-SN-CLOUD__mini0"].update({"surprise": 1})), "unknown surprise"),
    ("a plate that is not usable but ships a file entry", lambda r: edit_registry(r, lambda L_: L_["plates"]["P-SN-CLOUD__gone"].update({"k1": {"file": "x", "bytes": 1, "sha256": "b" * 64, "px": 1024}})), "ships no file"),
    ("a 4K file larger than 16 MiB", lambda r: edit_registry(r, lambda L_: L_["plates"]["P-SN-CLOUD__mini0"]["k4"].update({"bytes": 17 << 20})), "a 4K file is {file, bytes up to 16 MiB"),
    ("a plate retired before it arrived (until not after since)", lambda r: edit_registry(r, lambda L_: L_["plates"]["P-SN-CLOUD__mini0"].update({"until": 1})), "until must be 0"),
    ("a null in the library (not Python)", lambda r: edit_registry(r, lambda L_: L_["plates"]["P-SN-CLOUD__mini0"].update({"score": None})), "null, true and false are not Python"),
    ("a non ASCII word in the library", lambda r: edit_registry(r, lambda L_: L_["plates"]["P-SN-CLOUD__mini0"]["variables"].update({"x": "café"})), "ASCII only"),
    ("an engine entry that names a plate family the library lacks", lambda r: sub_file(r, "api/_lib/styles_engine.py", '"plates": ["P-SN-CLOUD"],', '"plates": ["P-SN-NOPE"],'), "reads the plate family \"P-SN-NOPE\""),
    ("an engine entry that names an atlas that is not one (item 1 of the engine literal)", lambda r: sub_first(r, "api/_lib/styles_engine.py", '"atlas": ["drops"],', '"atlas": ["drops", "nope"],'), "atlas must list chips, drops"),
    ("a style shown to customers without a tile image", lambda r: os.remove(os.path.join(r, "public", "assets", "atelier", "style-powder-burst-800.webp")), "style-powder-burst-800.webp: the style \"solo.powder\" is shown to customers and has no tile image at 800 px"),
    ("the Python packages recorded at 234 MiB (over the budget with the files of api/)", lambda r: (sub_file(r, "api/_lib/plates_registry.py", "DEPENDENCIES_MIB = 126", "DEPENDENCIES_MIB = 234"), add_file(r, "api/_assets/pad.bin", b"\0" * (2 << 20))), "over the 235 MiB budget"),
    ("a dependency size of zero", lambda r: sub_file(r, "api/_lib/plates_registry.py", "DEPENDENCIES_MIB = 126", "DEPENDENCIES_MIB = 0"), "DEPENDENCIES_MIB 0 must be"),
    ("vercel.json: a function without its own entry", vj_edit(lambda d: d["functions"].pop("api/enhance.py")), "no functions entry for api/enhance.py"),
    ("vercel.json: a catch-all glob", vj_edit(lambda d: d["functions"].update({"api/**/*.py": {"maxDuration": 60, "excludeFiles": "{}"}})), "the functions pattern \"api/**/*.py\" is a glob"),
    ("vercel.json: an entry for a function that is not there", vj_edit(lambda d: d["functions"].update({"api/ghost.py": dict(d["functions"]["api/enhance.py"])})), "names no function of api/"),
    ("vercel.json: the plates still in the bundle of health", vj_edit(lambda d: d["functions"]["api/health.py"].update({"excludeFiles": d["functions"]["api/compose.py"]["excludeFiles"]})), "api/health.py: excludeFiles must be the base list and the plates and atlases"),
    ("vercel.json: the plates excluded from compose", vj_edit(lambda d: d["functions"]["api/compose.py"].update({"excludeFiles": d["functions"]["api/health.py"]["excludeFiles"]})), "api/compose.py: excludeFiles must be the base list"),
    ("vercel.json: suites/** gone from an entry", vj_edit(lambda d: d["functions"]["api/order.py"].update({"excludeFiles": d["functions"]["api/order.py"]["excludeFiles"].replace("suites/**,", "")})), "api/order.py: excludeFiles must be"),
    ("vercel.json: another maxDuration", vj_edit(lambda d: d["functions"]["api/analyze.py"].update({"maxDuration": 300})), "do not share one maxDuration"),
    ("vercel.json: includeFiles puts the plates back into a function that never renders", vj_edit(lambda d: d["functions"]["api/analyze.py"].update({"includeFiles": "api/_assets/plates/**"})), "api/analyze.py: includeFiles puts files back"),
    ("vercel.json: a key the check does not read (memory)", vj_edit(lambda d: d["functions"]["api/compose.py"].update({"memory": 3008})), "api/compose.py: the key \"memory\" is not one this check reads"),
    ("vercel.json: not JSON", lambda r: open(os.path.join(r, "vercel.json"), "w").write("{"), "vercel.json: cannot be read as JSON"),
    ("a repository image that is byte for byte a reference work", lambda r: add_file(r, "public/assets/h10.png", b"\x89PNG a reference work"), "public/assets/h10.png: is byte for byte \"wave-y3/ref/H10.png\""),
    ("a calibration iris under another name and folder", lambda r: add_file(r, "src/landing/eye.png", b"\x89PNG a calibration iris"), "src/landing/eye.png: is byte for byte \"wave-g/live/out/x_2_enhanced.jpg\""),
    ("no deny list", lambda r: os.remove(os.path.join(r, "scripts", "hygiene_denylist.json")), "hygiene_denylist.json: cannot be read"),
    ("a deny list that holds a hash and no label", lambda r: open(os.path.join(r, "scripts", "hygiene_denylist.json"), "w").write(json.dumps({"sha256": ["abc"]})), "sha256 must map sha256 hashes to labels"),
]
roots = []
BATCH = os.path.join(TMP, "batch.mjs")
open(BATCH, "w", encoding="utf-8").write("""import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const repo = process.argv[2];
const { checkStyles } = await import(pathToFileURL(join(repo, 'scripts', 'check_styles.mjs')).href);
const out = {};
for (const root of process.argv.slice(3)) { try { out[root] = await checkStyles(root); } catch (e) { out[root] = ['THROWN: ' + e.message]; } }
console.log(JSON.stringify(out));
""")
untouched = make_tree(os.path.join(TMP, "t_untouched"))
for i, (label, fn, needle) in enumerate(cases):
    root = make_tree(os.path.join(TMP, f"t_{i:02d}"))
    fn(root)
    roots.append(root)
rc2 = subprocess.run([NODE, BATCH, REPO, untouched] + roots, capture_output=True, text=True, encoding="utf-8", timeout=900)
try:
    batch = json.loads(rc2.stdout.strip().splitlines()[-1])
except Exception:  # noqa: BLE001
    batch = None
check("the batch runner ran every copy of the small tree", batch is not None and len(batch) == len(roots) + 1, (rc2.returncode, rc2.stderr[-500:], rc2.stdout[-300:]))
if batch:
    check("an untouched small tree (synthetic plates and atlases with their true hashes, the tile images, the real vercel.json, a deny list) passes every item", batch[untouched] == [], batch[untouched][:4])
    for (label, _fn, needle), root in zip(cases, roots):
        probs = batch[root]
        check(f"check_styles refuses: {label}", any(needle in p for p in probs), (needle, probs[:3]))
bare = os.path.join(TMP, "t_bare")
shutil.copytree(untouched, bare)
os.remove(os.path.join(bare, "vercel.json"))
shutil.rmtree(os.path.join(bare, "api", "_assets"))
rc3 = subprocess.run([NODE, BATCH, REPO, bare], capture_output=True, text=True, encoding="utf-8", timeout=300)
check("a copy without vercel.json is not a deployment tree: items 8, 9, 10 and 12 are skipped there (the registry suite's mutation copies carry no plates and no vercel.json)",
      json.loads(rc3.stdout.strip().splitlines()[-1])[bare] == [], rc3.stdout[-300:])

fails = len([r for r in RESULTS if not r])
print(f"\n{len(RESULTS) - fails} of {len(RESULTS)} passed" + (f"; {fails} FAILED" if fails else ""))
sys.exit(1 if fails else 0)
