# -*- coding: utf-8 -*-
"""WP3 of the v3 engine work: the eye profile, the restoration gate, eye_id and seal v2. Test I4 (seal and profile: version 1 and 2,
tamper, expiry, the size of eight eyes, profile determinism, the gate table of the 29 calibration restorations) and IE2 (the style
package imports no engine and is light), plus the places the profile now travels: /api/enhance (reply, events, the time guard),
/api/compose (eyes[]), the order draft and the master's eye record.
No network and no image model (the model is a stub), no real eye in the repository: the eyes here are procedural (synth_eye); the 29
real restorations of the calibration set are read only from a folder named by an environment variable, and only reported:
    SNAPEYES_CALIB       folder with <name>_2_enhanced.jpg (the calibration restorations)
    SNAPEYES_GATE_TABLE  gate_table.json of the calibration run (lid and fill results, the table of the plan)
Without them those checks are skipped, and their lines are LOCAL lines, not PASS lines, so the PASS count is the same everywhere.
    python test_gate_seal.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as the entry v3gate (SNAPEYES_REPO names the checkout)."""
import ast
import base64
import copy
import hashlib
import hmac
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zlib

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
TMP = os.path.join(HERE, "wp3_tmp")
CALIB = os.environ.get("SNAPEYES_CALIB") or ""
GATE_TABLE = os.environ.get("SNAPEYES_GATE_TABLE") or ""
SP = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP, "wave-pv", "tests") if SP else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []
LOCAL = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def local(name, ok, detail=""):
    """A check that needs the real calibration set: reported, not counted among the PASS lines (a failure still fails the run)."""
    LOCAL.append(bool(ok))
    print(("LOCAL ok   " if ok else "FAIL LOCAL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_CALIB", "SNAPEYES_GATE_TABLE"):
            os.environ.pop(k)
if os.path.isdir(TMP):
    shutil.rmtree(TMP, ignore_errors=True)
os.makedirs(TMP)
sys.path.insert(0, HARNESS)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store_gate")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])          # the payments harness' synthetic keys and ticket secret, a local store folder
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
sys.path.insert(0, API)
import numpy as np  # noqa: E402
import requests  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import catalogue as CAT  # noqa: E402
from _lib import store  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402
from _lib.styles import gate as GATE  # noqa: E402
from _lib.styles import pupil as PUP  # noqa: E402
from _lib.styles import palette as PAL  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
MODULES = ["eye", "gate", "pupil", "palette"]


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


# ============================================================================================ a procedural iris
def _circ_noise(rng, n, sigma):
    v = rng.normal(size=n)
    h = int(4 * sigma)
    k = np.exp(-0.5 * (np.arange(-h, h + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.convolve(np.r_[v[-h:], v, v[:h]], k, "valid")
    return out / (out.std() + 1e-9)


BASE_RGB = {"own": (92, 128, 158), "dark_brown": (66, 38, 18), "grey": (126, 129, 133)}
PUPIL_AXES = {"round": (0.27, 0.27), "slit": (0.15, 0.42), "bar": (0.46, 0.16)}


def synth_eye(kind="own", pupil="round", lid=False, seed=1, side=1024, pad=1.12):
    """A procedural restored iris on black (a square, the iris disc of radius side / (2 pad)): radial fibres, a bright collarette, a
    darker limbus, a flat dark pupil (round, slit or bar), optionally a dark lash band across the top. Deterministic in its arguments."""
    rng = np.random.default_rng(seed)
    R = side / (2.0 * pad)
    ax = np.arange(side, dtype=np.float32) + 0.5 - side / 2.0
    X, Y = np.meshgrid(ax, ax)
    r = np.hypot(X, Y) / np.float32(R)
    th = np.arctan2(Y, X)
    idx = ((th + np.pi) / (2 * np.pi) * 720.0).astype(np.int64) % 720
    f1, f2, f3 = _circ_noise(rng, 720, 2.0), _circ_noise(rng, 720, 6.0), _circ_noise(rng, 720, 18.0)
    fib = 0.5 * f1[idx] + 0.35 * f2[idx] + 0.25 * f3[idx]
    radial = 1.0 + 0.35 * np.exp(-((r - 0.45) / 0.14) ** 2) - 0.45 * np.clip((r - 0.90) / 0.10, 0, 1)
    lum = radial * (1.0 + 0.10 * fib * (0.4 + 0.6 * np.clip(r, 0, 1)))
    col = np.array(BASE_RGB[kind], np.float32)[None, None, :] * lum[..., None]
    pa, pb = PUPIL_AXES[pupil]
    e = np.hypot(X / (pa * R), Y / (pb * R))
    soft = np.clip((e - 1.0) / 0.06, 0, 1)
    col = col * soft[..., None] + np.array((6, 6, 7), np.float32)[None, None, :] * (1 - soft[..., None])
    if lid:
        ang = np.degrees(th)
        band = (ang > -135.0) & (ang < -45.0) & (r > 0.70)
        col = np.where(band[..., None], col * 0.15 + np.array((20, 16, 14), np.float32), col)
    alpha = np.clip((1.0 - r) / 0.03, 0, 1)[..., None]
    return Image.fromarray(np.clip(col * alpha, 0, 255).astype(np.uint8))


def jpeg(im, q=93):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, subsampling=0)
    return buf.getvalue()


# ============================================================================================ 1. the package is light (IE2)
section("1. the style package is light (IE2) and the modules follow the module rules")
code = ("import sys, time\nsys.path.insert(0, %r)\nt0 = time.perf_counter()\nimport _lib.styles\ndt = time.perf_counter() - t0\n"
        "print(dt, sorted(m for m in sys.modules if m.startswith('_lib.styles.')))\n" % API)
r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
dt_s, mods_s = r.stdout.strip().split(" ", 1) if r.returncode == 0 and r.stdout.strip() else ("99", "[]")
check("import _lib.styles takes at most 150 ms in a fresh interpreter", float(dt_s) <= 0.15, (dt_s, r.stderr[-300:]))
check("... and leaves every engine family out of sys.modules",
      not any(f"_lib.styles.{f}" in mods_s for f in ("singles", "collision", "universe")), mods_s)
code2 = ("import sys\nsys.path.insert(0, %r)\nimport _lib.styles.eye, _lib.styles.gate, _lib.styles.pupil, _lib.styles.palette, _lib.preview\n"
         "print(sorted(m for m in sys.modules if m.startswith('_lib.styles.')))\n" % API)
r2 = subprocess.run([sys.executable, "-c", code2], capture_output=True, text=True, timeout=120, env=dict(os.environ, SNAPEYES_TICKET_SECRET="x" * 32))
check("the profile modules and preview.py load no engine family either",
      r2.returncode == 0 and not any(f"_lib.styles.{f}" in r2.stdout for f in ("singles", "collision", "universe")), (r2.stdout, r2.stderr[-300:]))
srcs = {m: read(f"api/_lib/styles/{m}.py") for m in MODULES}
check("every module starts with the __future__ import after its docstring (Vercel's default Python is 3.12)",
      all(isinstance(ast.parse(s).body[0], ast.Expr) and isinstance(ast.parse(s).body[1], ast.ImportFrom)
          and ast.parse(s).body[1].module == "__future__" for s in srcs.values()))


def imports_of(src):
    """(level, module, names) of every import in a module."""
    out = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.ImportFrom):
            out.append((n.level, n.module or "", [a.name for a in n.names]))
        elif isinstance(n, ast.Import):
            out += [(0, a.name, []) for a in n.names]
    return out


STD_OK = {"__future__", "math", "numpy", "PIL", "collections", "hashlib", "io", "json", "re", "threading", "time", "zlib"}
bad_imp = []
for m_, s_ in srcs.items():
    for level, mod, names in imports_of(s_):
        if level == 0 and mod.split(".")[0] in STD_OK:
            continue
        if level == 2 and mod == "" and names == ["iris"]:
            continue                                         # from .. import iris as L: the legacy engine
        if level == 1 and mod == "" and all(n in MODULES for n in names):
            continue                                         # from . import gate, palette, pupil
        bad_imp.append((m_, level, mod, names))
check("they import only the standard library, numpy, Pillow, the legacy engine (iris) and each other (no scipy, skimage, psutil, requests, no engine)",
      not bad_imp, bad_imp)
check("no dash (en or em) and no non-ASCII character in the new modules", all(all(ord(c) < 128 for c in s) and not re.search(DASH, s) for s in srcs.values()))
check("they write no file and read none (no builtin open(), no os, no pathlib, no subprocess; Image.open of bytes in memory is not a file)",
      not any(re.search(r"(?<![\w.])open\(|\bimport os\b|\bpathlib\b|\bsubprocess\b", s) for s in srcs.values()))

# ============================================================================================ 2. identity
section("2. eye_id")
data = os.urandom(5000)
check("eye_id is the first 16 hex digits of the sha256 of the preview bytes, the same formula in preview.py, eye.py and the draft's sha256",
      EYE.eye_id_of(data) == P.eye_id_of(data) == hashlib.sha256(data).hexdigest()[:16] and len(EYE.eye_id_of(data)) == 16)
check("is_eye_id accepts 16 lower case hex digits only",
      EYE.is_eye_id("0123456789abcdef") and not any(EYE.is_eye_id(x) for x in ("0123456789ABCDEF", "0123456789abcde", "0123456789abcdef0", "xyz", None, 5, "")))
check("the seal's profile size cap equals the profile module's (8192 bytes)", P.PROFILE_MAX == EYE.MAX_PROFILE_BYTES == 8192)

# ============================================================================================ 3. the profile of procedural eyes
section("3. the profile: classes, pupils, gates (procedural eyes)")
EYES = {}
for key, args in {"own": ("own", "round", False), "brown": ("dark_brown", "round", False), "grey": ("grey", "round", False),
                  "slit": ("own", "slit", False), "bar": ("own", "bar", False), "own_lid": ("own", "round", True),
                  "grey_lid": ("grey", "round", True), "brown_slit": ("dark_brown", "slit", False)}.items():
    im = synth_eye(*args, seed=7)
    raw = jpeg(im)
    t_cpu = time.process_time()
    prof = EYE.profile_of_bytes(raw)
    EYES[key] = {"raw": raw, "prof": prof, "cpu": time.process_time() - t_cpu, "im": im}
p_own, p_brown, p_grey = EYES["own"]["prof"], EYES["brown"]["prof"], EYES["grey"]["prof"]
check("colour class: a blue-grey eye is own, a dark warm one dark_brown, a neutral one grey",
      [p_own.cls, p_brown.cls, p_grey.cls] == ["own", "dark_brown", "grey"], [p.cls for p in (p_own, p_brown, p_grey)])
check("pupil class: round, slit and bar pupils are told apart", [EYES[k]["prof"].pupil_cls for k in ("own", "slit", "bar")] == ["round", "slit", "bar"])
def walk(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)
    else:
        yield x


check("the record is whole numbers only (no float anywhere, no decimal point in its bytes), the version is 1, the eye id is the preview's",
      not any(isinstance(v, float) for v in walk(p_own.rec)) and b"." not in EYE.canonical_json(p_own.rec) and p_own.rec["v"] == 1
      and p_own.eye_id == EYE.eye_id_of(EYES["own"]["raw"]))
check("a clean procedural eye passes both gate rules, an eye with a lash band across the top fails the lid rule (own and grey)",
      all(EYES[k]["prof"].gate(r)["ok"] is True for k in ("own", "brown", "grey", "slit", "bar") for r in ("lid", "fill"))
      and all(EYES[k]["prof"].gate("lid")["ok"] is False and EYES[k]["prof"].gate("fill")["ok"] is False for k in ("own_lid", "grey_lid")),
      {k: (EYES[k]["prof"].gate("lid")["ok"], EYES[k]["prof"].gate("fill")["ok"]) for k in EYES})
g = EYES["own_lid"]["prof"].gate("lid")
check("the gate result has one schema: ok, rule, values (the numbers), why (reason codes that exist)",
      set(g) == {"ok", "rule", "values", "why"} and g["rule"] == "lid" and g["why"] and all(c in GATE.WHY["lid"] for c in g["why"])
      and set(g["values"]) == {"lid70", "lid88", "outlier_bins", "maxdev70"}, g)
gf = EYES["own_lid"]["prof"].gate("fill")
check("... for the fill rule too", set(gf) == {"ok", "rule", "values", "why"} and gf["rule"] == "fill" and set(gf["values"]) == {"run18", "n_step", "catch"}
      and all(c in GATE.WHY["fill"] for c in gf["why"]) and bool(gf["why"]) == (gf["ok"] is False), gf)
check("a profile measured with the lid rule only says unknown (ok None) for the fill rule, and the combination is unknown too",
      (lambda p: p.gate("fill")["ok"] is None and p.gate("lid+fill")["ok"] is None and p.gate("lid")["ok"] is True
       and "fill" not in p.rec["gate"])(EYE.profile_of_bytes(EYES["own"]["raw"], rules=("lid",))))
check("lid+fill: ok when both pass, False when one fails (values per rule)",
      EYES["own"]["prof"].gate("lid+fill")["ok"] is True and EYES["own_lid"]["prof"].gate("lid+fill")["ok"] is False
      and set(EYES["own"]["prof"].gate("lid+fill")["values"]) == {"lid", "fill"})
try:
    p_own.gate("zzz")
    bad_rule = False
except ValueError:
    bad_rule = True
check("an unknown gate rule name is a ValueError, never a silent pass", bad_rule)
pub = p_own.public()
check("public(): eye_id, version, class, ease, pupil class, the gate's ok per rule (reason codes only for a failure); about 0.4 KB",
      set(pub) == {"eye_id", "v", "cls", "ease", "pupil", "gate"} and pub["gate"]["lid"] == {"ok": True} and pub["pupil"] == {"cls": "round"}
      and len(json.dumps(pub)) < 400 and EYES["own_lid"]["prof"].public()["gate"]["lid"]["ok"] is False
      and EYES["own_lid"]["prof"].public()["gate"]["lid"]["why"], (pub, len(json.dumps(pub))))
check("the profile's wire form is at most 8192 bytes for every procedural eye (about 1 to 1.8 KB)",
      all(len(EYES[k]["prof"].to_wire()) <= EYE.MAX_PROFILE_BYTES for k in EYES) and max(len(EYES[k]["prof"].to_wire()) for k in EYES) < 3000,
      {k: len(EYES[k]["prof"].to_wire()) for k in EYES})
cpu_best = min(EYES[k]["cpu"] for k in EYES)
check("measuring a profile (both gate rules) takes at most 3 s of CPU per eye locally (the best of eight, CPU time)", cpu_best <= 3.0, cpu_best)
print("   profile CPU seconds per eye:", {k: round(EYES[k]["cpu"], 2) for k in EYES}, flush=True)

# ---- the profile read back: ring, stats, pupil, h2
ei = EYE.EyeInput(EYES["own"]["raw"])
m_ring, m_stats = ei.ring, ei.stats
check("the sealed ring is the measured ring at 8 bit precision (at most half a level off) and has 360 bins of 3 floats",
      p_own.ring.shape == (360, 3) and p_own.ring.dtype == np.float32 and float(np.abs(p_own.ring * 255.0 - m_ring * 255.0).max()) <= 0.5001)
check("the stored statistics are colour_stats of the unrounded ring (hundredths, tenths)",
      p_own.stats["class"] == m_stats["class"] and abs(p_own.stats["L"] - m_stats["L"]) < 0.0051 and abs(p_own.stats["C"] - m_stats["C"]) < 0.0051
      and abs(p_own.stats["h"] - m_stats["h"]) < 0.051 and np.abs(np.asarray(p_own.stats["mean_rgb"]) - np.asarray(m_stats["mean_rgb"])).max() < 0.051)
pup_m, pup_s = ei.pupil, p_own.pupil
check("the sealed pupil gives the same mask and reach as the measured one (within a thousandth of R)",
      abs(PUP.reach(pup_s, (1.0, 0.0)) - PUP.reach(pup_m, (1.0, 0.0))) < 0.002 and abs(PUP.reach(pup_s, (0.0, -1.0)) - PUP.reach(pup_m, (0.0, -1.0))) < 0.002
      and float((PUP.mask(pup_s, 256, 120.0) != PUP.mask(pup_m, 256, 120.0)).mean()) < 0.002 and pup_s["cls"] == pup_m["cls"] == "round")
rgb, how, hue = p_own.h2
check("the secondary hue is stored as numbers and rebuilt as the design code returns it (rgb 0..1, how, hue)",
      rgb.shape == (3,) and 0.0 <= float(rgb.min()) and float(rgb.max()) <= 1.0 and how in ("collarette", "analogous") and 0.0 <= hue < 360.0)

# ---- an eye with an attached profile answers from it
ep = EYE.EyeInput(EYES["own"]["raw"], profile=p_own)
check("an EyeInput with a profile answers ring, class, stats and pupil from it, without grading",
      ep.cls == "own" and ep.ring is p_own.ring and ep.stats["class"] == "own" and ep.pupil is p_own.pupil and not ep._grades and ep.eye_id == p_own.eye_id)
try:
    EYE.EyeInput(EYES["own"]["raw"], eye_id="f" * 16, profile=p_own)
    mism = False
except EYE.ProfileError:
    mism = True
check("a profile that belongs to another eye is refused", mism)
check("an EyeInput built from bytes takes its id from them, from pixels when it has no bytes, and a bad id is refused",
      ei.eye_id == EYE.eye_id_of(EYES["own"]["raw"]) and EYE.EyeInput(EYES["own"]["im"]).eye_id == EYE._pixel_id(EYES["own"]["im"])
      and EYE.EyeInput(EYES["own"]["im"], eye_id="a" * 16).eye_id == "a" * 16)
check("max_side shrinks a larger source (a 2400 px square to 2048 by default, to 4096 for a master); a non-square image is cropped square; pad is clamped",
      EYE.EyeInput(Image.new("RGB", (2400, 2400), (9, 9, 9))).src.size == (2048, 2048)
      and EYE.EyeInput(Image.new("RGB", (2400, 2400), (9, 9, 9)), max_side=4096).src.size == (2400, 2400)
      and EYE.EyeInput(Image.new("RGB", (300, 200), (9, 9, 9))).src.size == (200, 200)
      and EYE.EyeInput(EYES["own"]["im"], pad=9).pad == 2.0 and EYE.EyeInput(EYES["own"]["im"], pad=0.2).pad == 1.0
      and EYE.EyeInput(EYES["own"]["im"], pad="x").pad == EYE.PAD)
check("the grade cache is bounded by bytes and keeps the size asked for last",
      (lambda e: (e.graded(256), e.graded(512), e.graded(1024), True)[-1] and 1024 in e._grades and sum(a.nbytes for a in e._grades.values())
       <= EYE.GRADE_CACHE_BYTES + e._grades[1024].nbytes)(EYE.EyeInput(EYES["own"]["raw"])))

# ---- the profile of a degenerate image does not raise
flat = EYE.EyeInput(Image.new("RGB", (1024, 1024), (0, 0, 0)), eye_id="1" * 16)
try:
    pf = flat.compute_profile()
    flat_ok = pf.cls in EYE.CLASSES
except Exception as e:  # noqa
    flat_ok = repr(e)
check("a black square (no iris at all) gives a profile, not an exception", flat_ok is True, flat_ok)

# ============================================================================================ 4. determinism (4 fresh processes)
section("4. the profile is a function of the preview bytes")
child = r'''
import io, os, sys, hashlib, json, random
sys.path.insert(0, {api!r})
os.environ["SNAPEYES_TICKET_SECRET"] = "x" * 32
raw = open({raw!r}, "rb").read()
from _lib.styles import eye as EYE
p = EYE.profile_of_bytes(raw)
print(hashlib.sha256(EYE.canonical_json(p.rec)).hexdigest(), len(EYE.canonical_json(p.rec)))
'''
raw_path = os.path.join(TMP, "own.jpg")
with open(raw_path, "wb") as f:
    f.write(EYES["own"]["raw"])
digests = []
for seedh in ("0", "1", "4242", "random"):
    rr = subprocess.run([sys.executable, "-c", child.format(api=API, raw=raw_path)], capture_output=True, text=True, timeout=300,
                        env=dict(os.environ, PYTHONHASHSEED=seedh))
    digests.append(rr.stdout.strip() if rr.returncode == 0 else "ERR " + rr.stderr[-200:])
mine = hashlib.sha256(EYE.canonical_json(p_own.rec)).hexdigest() + " " + str(len(EYE.canonical_json(p_own.rec)))
check("four fresh interpreters (other hash seeds) measure the very same profile bytes as this one", all(d == mine for d in digests), (digests, mine))
check("measuring the same bytes twice in one process gives the same record, and a memoised call returns the one object",
      EYE.profile_of_bytes(EYES["own"]["raw"]).rec == p_own.rec and EYE.profile_of_bytes(EYES["own"]["raw"], memo=True) is EYE.profile_of_bytes(EYES["own"]["raw"], memo=True))
check("the measurement does not depend on the encoder of the bytes: another JPEG quality is another eye id (never silently the same)",
      EYE.profile_of_bytes(jpeg(EYES["own"]["im"], 80)).eye_id != p_own.eye_id)

# ============================================================================================ 5. the record is validated
section("5. the record: validation, wire form")
rec0 = p_own.rec


def mutated(fn):
    r_ = copy.deepcopy(rec0)
    fn(r_)
    return r_


MUT = {
    "an extra field": lambda r_: r_.update(extra=1),
    "a missing field": lambda r_: r_.pop("gate"),
    "version 2": lambda r_: r_.update(v=2),
    "an upper case eye id": lambda r_: r_.update(eye_id=r_["eye_id"].upper()),
    "a short eye id": lambda r_: r_.update(eye_id=r_["eye_id"][:15]),
    "an unknown class": lambda r_: r_.update(cls="blue"),
    "a ring of 1079 numbers": lambda r_: r_["ring"].pop(),
    "a ring level of 256": lambda r_: r_["ring"].__setitem__(5, 256),
    "a ring level that is a float": lambda r_: r_["ring"].__setitem__(5, 1.5),
    "a ring level that is a bool": lambda r_: r_["ring"].__setitem__(5, True),
    "a pupil reach of 179 numbers": lambda r_: r_["pupil"]["reach"].pop(),
    "an unknown pupil class": lambda r_: r_["pupil"].update(cls="oval"),
    "a negative lightness": lambda r_: r_["stats"].update(L=-1),
    "an unknown h2 kind": lambda r_: r_["h2"].update(how="x"),
    "an unknown gate rule": lambda r_: r_["gate"].update(zzz=r_["gate"]["lid"]),
    "an ok gate with a reason": lambda r_: r_["gate"]["lid"].update(why=["lid_deviation"]),
    "a failed gate without a reason": lambda r_: r_["gate"]["lid"].update(ok=False),
    "a reason code that does not exist": lambda r_: r_["gate"]["lid"].update(ok=False, why=["nope"]),
    "a gate value that is not whole": lambda r_: r_["gate"]["lid"]["values"].update(lid70=1.5),
    "an extra gate value": lambda r_: r_["gate"]["lid"]["values"].update(extra=1),
    "a pad below 1.0": lambda r_: r_.update(pad=999),
    "a not-a-dict record": None,
}
refused = {}
for name, fn in MUT.items():
    try:
        EYE.validate(copy.deepcopy(rec0) if fn is None else mutated(fn)) if fn is not None else EYE.validate([1, 2])
        refused[name] = False
    except EYE.ProfileError:
        refused[name] = True
check("validate refuses each of 22 malformed records (fields, version, id, class, ring, pupil, stats, h2, gate)", all(refused.values()),
      [k for k, v in refused.items() if not v])
check("validate accepts every procedural eye's own record", all(EYE.validate(EYES[k]["prof"].rec) is EYES[k]["prof"].rec for k in EYES))
wire = p_own.to_wire()
check("wire form round trip: the profile read back has the same record", EYE.EyeProfile.from_wire(wire).rec == rec0)
check("the wire form is zlib of the canonical JSON (sorted keys, no spaces)", zlib.decompress(wire) == EYE.canonical_json(rec0)
      and json.loads(zlib.decompress(wire)) == rec0)
worst = copy.deepcopy(rec0)
rng_w = np.random.default_rng(5)
worst["ring"] = [int(v) for v in rng_w.integers(0, 256, 1080)]
worst["pupil"]["reach"] = [int(v) for v in rng_w.integers(0, 1000, 180)]
check("even a profile of random numbers (nothing for zlib to find) fits the 8192 byte cap", len(EYE.EyeProfile(worst).to_wire()) <= EYE.MAX_PROFILE_BYTES,
      len(EYE.EyeProfile(worst).to_wire()))


def wire_refused(blob):
    try:
        EYE.EyeProfile.from_wire(blob)
        return False
    except EYE.ProfileError:
        return True


bomb = zlib.compress(b"0" * 6_000_000, 9)
check("from_wire refuses: nothing, too large, not zlib, a zlib bomb (small packed, large unpacked), trailing bytes, not JSON, a wrong schema",
      all(wire_refused(x) for x in (b"", b"x" * 9000, b"not zlib at all", bomb, wire + b"tail", zlib.compress(b"nonsense"),
                                    zlib.compress(b'{"v":1}'), zlib.compress(b"[1,2,3]"))) and len(bomb) < EYE.MAX_PROFILE_BYTES, len(bomb))
check("from_wire refuses what is not bytes", all(wire_refused(x) for x in (None, "abc", 5, [])))

# ============================================================================================ 6. the gate module on its own
section("6. the gate: the stored form, the set-level result")
res_l = {"ok": False, "rule": "lid", "values": {"lid70": 3, "lid88": 1, "outlier_bins": 12, "maxdev70": 12.25}, "why": ["lid_sectors_inner"]}
sf = GATE.store_form(res_l)
check("store_form keeps whole numbers (maxdev70 in tenths as the design code printed it, catch in ten thousandths) and read_form inverts it",
      sf == {"ok": False, "why": ["lid_sectors_inner"], "values": {"lid70": 3, "lid88": 1, "outlier_bins": 12, "maxdev70_x10": 122}}
      and GATE.read_form("lid", sf)["values"]["maxdev70"] == 12.2
      and GATE.store_form({"ok": True, "rule": "fill", "values": {"run18": 10, "n_step": 46, "catch": 0.0123}, "why": []})["values"]
      == {"run18": 10, "n_step": 46, "catch_x1e4": 123}, sf)
check("valid_form accepts what store_form makes and refuses the other shapes",
      GATE.valid_form("lid", sf) and not GATE.valid_form("fill", sf) and not GATE.valid_form("lid", dict(sf, ok=True))
      and not GATE.valid_form("lid", dict(sf, extra=1)) and not GATE.valid_form("lid", {"ok": True, "why": [], "values": {}})
      and not GATE.valid_form("zzz", sf) and not GATE.valid_form("lid", None))
unk = {"cls": "own"}
check("gate() of a record without a gate section is unknown for every rule (a hard style then says reseal)",
      GATE.gate(unk, "lid")["ok"] is None and GATE.gate(unk, "fill")["ok"] is None and GATE.gate({}, "lid+fill")["ok"] is None)
sr = GATE.set_result([p_own, EYES["own_lid"]["prof"], None], "lid")
check("set_result: the first failing eye names the reason, a failure beats an unknown eye, all passing is True, an unknown eye alone is None",
      sr["ok"] is False and sr["first"]["eye"] == 2 and sr["first"]["why"] in GATE.WHY["lid"] and sr["eyes"] == 3
      and GATE.set_result([p_own, p_brown], "lid")["ok"] is True and GATE.set_result([p_own, None], "lid")["ok"] is None
      and GATE.set_result([None], "lid")["first"] is None and GATE.set_result([p_own, EYES["grey_lid"]["prof"]], "lid+fill")["first"]["eye"] == 2)
check("the design code's rule is the rule: every failing lid result carries a reason and every passing one carries none",
      all(bool(EYES[k]["prof"].gate("lid")["why"]) == (EYES[k]["prof"].gate("lid")["ok"] is False) for k in EYES))
spike = np.pad(np.ones((1, 1), np.float32), 10)
bl = GATE.blur_small(spike, 1.5)
check("blur_small is the design code's blur for sigma 1.5: it keeps the sum, is symmetric and peaks at the centre",
      abs(float(bl.sum()) - 1.0) < 1e-4 and np.allclose(bl, bl.T, atol=1e-7) and np.allclose(bl, bl[::-1, ::-1], atol=1e-7)
      and bl[10, 10] == bl.max() and bl[10, 10] > bl[10, 14])
try:
    GATE.blur_small(np.zeros((8, 8), np.float32), 5.0)
    wide_refused = False
except ValueError:
    wide_refused = True
check("... and a wide blur is a ValueError (the gate never asks for one)", wide_refused)

# ============================================================================================ 7. seal v1 and v2 (I4)
section("7. the seal: version 1 and 2, tamper, expiry, size")
D = os.urandom(200_000)
EID = EYE.eye_id_of(D)
v1o, v1c = P.seal(D), P.seal(D, kind=P.KIND_COMPOSE)
pf_blue = EYES["own"]["prof"]
# a v2 order seal is made for the bytes of a preview whose id is the hash of those very bytes
raw_own = EYES["own"]["raw"]
v2o = P.seal(raw_own, eye_id=pf_blue.eye_id, profile=pf_blue)
v2c = P.seal(os.urandom(50_000), kind=P.KIND_COMPOSE, eye_id=pf_blue.eye_id, profile=pf_blue)
raw_b = base64.b64decode(v1o)
check("a seal without an id is the version 1 envelope, byte for byte as before (54 bytes of envelope, version byte 1)",
      raw_b[0] == 1 and len(raw_b) == len(D) + 54 and P.VERSION == 1 and P.VERSION_V2 == 2)
check("a version 1 order seal opens: eye_id is the hash of its own bytes, no profile (the gate is unknown)",
      (lambda pl, m: pl == D and m == {"v": 1, "kind": P.KIND_ORDER, "eye_id": EID, "profile": None})(*P.unseal_full(v1o)))
check("a version 1 compose copy opens: no id (its bytes are not the preview's), no profile",
      (lambda pl, m: pl == D and m == {"v": 1, "kind": P.KIND_COMPOSE, "eye_id": None, "profile": None})(*P.unseal_full(v1c)))
pl2, m2 = P.unseal_full(v2o)
check("a version 2 order seal carries the id and the profile in its authenticated header and opens to the same bytes",
      pl2 == raw_own and m2["v"] == 2 and m2["kind"] == P.KIND_ORDER and m2["eye_id"] == pf_blue.eye_id and m2["profile"].rec == pf_blue.rec
      and P.unseal(v2o) == raw_own and base64.b64decode(v2o)[0] == 2, m2)
pl2c, m2c = P.unseal_full(v2c)
check("a version 2 compose copy carries the same id and profile (the id is the order copy's, not the copy's own hash)",
      m2c["kind"] == P.KIND_COMPOSE and m2c["eye_id"] == pf_blue.eye_id and m2c["profile"].rec == pf_blue.rec and EYE.eye_id_of(pl2c) != m2c["eye_id"])
m3 = P.unseal_full(P.seal(raw_own, eye_id=pf_blue.eye_id))[1]
check("a version 2 seal without a profile says so (profile None, the id kept)", m3["v"] == 2 and m3["profile"] is None and m3["eye_id"] == pf_blue.eye_id)
check("two seals of one eye differ (a fresh nonce) and carry the same id and profile",
      P.seal(raw_own, eye_id=pf_blue.eye_id, profile=pf_blue) != v2o and P.unseal_full(P.seal(raw_own, eye_id=pf_blue.eye_id, profile=pf_blue))[1]["profile"].rec == pf_blue.rec)


def refusal_of(s, **kw):
    try:
        P.unseal_full(s, **kw)
    except P.SealExpired:
        return "expired"
    except P.SealError:
        return "seal"
    except Exception as e:  # noqa
        return "wrong " + repr(e)
    return None


def flipped(s, at):
    r_ = bytearray(base64.b64decode(s))
    r_[at] ^= 1
    return b64(bytes(r_))


nb = len(base64.b64decode(v2o))
head_n = P.HEAD_BYTES
plen = int.from_bytes(base64.b64decode(v2o)[head_n + 8:head_n + 10], "big")
spots = {"the version byte": 0, "the kind byte": 1, "the expiry": 3, "the nonce": 12, "the eye id": head_n + 3, "the profile length": head_n + 9,
         "the profile": head_n + 10 + plen // 2, "the ciphertext": head_n + 10 + plen + 100, "the tag": nb - 1}
check("a changed byte anywhere in a version 2 seal (version, kind, expiry, nonce, id, profile length, profile, ciphertext, tag) is refused",
      all(refusal_of(flipped(v2o, at)) == "seal" for at in spots.values()), {k: refusal_of(flipped(v2o, at)) for k, at in spots.items()})
check("truncation, a wrong key, an empty string and a non-string are refused for version 2 as for version 1",
      refusal_of(v2o[:60]) == "seal" and refusal_of("") == "seal" and refusal_of(None) == "seal" and refusal_of(7) == "seal"
      and refusal_of(v2o + "AAAA") == "seal")
expired = P.seal(raw_own, ttl=-1, eye_id=pf_blue.eye_id, profile=pf_blue)
check("an expired version 2 seal is refused as expired, a changed one as invalid (the tag is checked first)",
      refusal_of(expired) == "expired" and refusal_of(flipped(expired, head_n + 20)) == "seal")
check("kinds: a version 2 compose copy is refused where only an order's preview is taken; relabelling it as an order is refused by the tag",
      refusal_of(v2c, kinds=(P.KIND_ORDER,)) == "seal" and P.unseal_full(v2o, kinds=(P.KIND_ORDER,))[1]["v"] == 2
      and refusal_of(flipped(v2c, 1), kinds=(P.KIND_ORDER,)) == "seal")
check("an order seal whose id is not the hash of its bytes is refused on opening (the id of an order seal is checked against its plaintext)",
      refusal_of(P.seal(raw_own, eye_id="0123456789abcdef")) == "seal" and refusal_of(P.seal(raw_own, eye_id=EYE.eye_id_of(raw_own))) is None)
other = EYES["grey"]["prof"]
mix = P.seal(raw_own, eye_id=pf_blue.eye_id, profile=other.to_wire())
check("a seal whose profile belongs to another eye is refused by unseal_full (the profile is checked against the id) while unseal still returns the bytes",
      refusal_of(mix) == "seal" and P.unseal(mix) == raw_own)
body_fn = P._keys


def forge(body):
    """A blob with a valid tag over any body (the server's own key, for the tests of what a valid tag still must not carry)."""
    k_enc, k_mac = body_fn()
    return b64(body + hmac.digest(k_mac, body, "sha256"))


def v2_body(profile_bytes, plen_override=None, eid=None, data=raw_own, kind=P.KIND_ORDER):
    k_enc, _ = body_fn()
    nonce = os.urandom(16)
    n = len(profile_bytes) if plen_override is None else plen_override
    head = bytes([2, kind]) + (int(time.time()) + 3600).to_bytes(4, "big") + nonce + bytes.fromhex(eid or EYE.eye_id_of(data)) + n.to_bytes(2, "big")
    return head + profile_bytes + P._xor(k_enc, nonce, data)


check("a valid tag does not excuse a profile longer than 8192 bytes, a length that runs past the blob, or a profile that is not a profile",
      refusal_of(forge(v2_body(b"x" * 8193))) == "seal" and refusal_of(forge(v2_body(b"x" * 50, plen_override=60000))) == "seal"
      and refusal_of(forge(v2_body(zlib.compress(b"nonsense")))) == "seal" and refusal_of(forge(v2_body(b"\x00" * 20))) == "seal"
      and P.unseal(forge(v2_body(b"\x00" * 20))) == raw_own, "")
try:
    P.seal(raw_own, eye_id=pf_blue.eye_id, profile=b"x" * 8193)
    big_ok = False
except ValueError:
    big_ok = True
try:
    P.seal(raw_own, eye_id="not-an-id")
    badid_ok = False
except ValueError:
    badid_ok = True
try:
    P.seal(raw_own, profile=b"abc")
    noid_ok = False
except ValueError:
    noid_ok = True
try:
    P.seal(raw_own, eye_id="f" * 16, profile=pf_blue)
    other_ok = False
except ValueError:
    other_ok = True
check("seal() refuses a profile over 8192 bytes, a bad id, wire bytes without an id, and a profile of another eye than the id", big_ok and badid_ok and noid_ok and other_ok)
cap_blob = P.seal(os.urandom(1_200_000), eye_id="a" * 16, profile=os.urandom(8192))
check("the largest order preview (1.6 million characters of base64) with the largest profile still fits the seal's 1.7 million limit",
      len(cap_blob) <= P.SEALED_B64_MAX, (len(cap_blob), P.SEALED_B64_MAX))
t0 = time.time()
P.unseal_full(P.seal(raw_own, eye_id=pf_blue.eye_id, profile=pf_blue))
check("seal + unseal_full of a preview with its profile under 0.5 s", time.time() - t0 < 0.5, time.time() - t0)
# eight eyes: the compose request holds one compose copy per eye
eight = []
for i in range(8):
    imx = synth_eye(("own", "dark_brown", "grey")[i % 3], "round", False, seed=20 + i)
    rawx = jpeg(imx)
    pfx = EYE.profile_of_bytes(rawx) if i < 3 else EYE.EyeProfile(dict(copy.deepcopy(EYES["own"]["prof"].rec), eye_id=EYE.eye_id_of(rawx)))
    out = P.protect(imx, rawx, profile=pfx)
    eight.append((out, pfx, rawx))
c560 = [o["sealed_sizes"]["560"] for o, _, _ in eight]
check("eight eyes: the eight 560 px compose copies with their profiles stay far under compose's 4.4 MB request limit, each blob under the seal limit",
      sum(map(len, c560)) < 2_000_000 and all(len(o["sealed"]) <= P.SEALED_B64_MAX for o, _, _ in eight), sum(map(len, c560)))
check("the profile adds at most 11 KB (base64) to a seal", all(len(o["sealed"]) - len(P.seal(r_, eye_id=p.eye_id)) <= 11_000 for o, p, r_ in eight))
o0, p0, r0 = eight[0]
check("protect(): all three seals of an eye carry the same id (the order bytes') and the same profile; the display copy carries neither",
      all(P.unseal_full(x)[1]["eye_id"] == p0.eye_id and P.unseal_full(x)[1]["profile"].rec == p0.rec for x in (o0["sealed"], *o0["sealed_sizes"].values()))
      and P.unseal(o0["sealed"]) == r0 and P.is_display(base64.b64decode(o0["image"])) and p0.eye_id.encode() not in base64.b64decode(o0["image"]))
o_np = P.protect(EYES["own"]["im"], raw_own)
check("protect() without a profile still seals the id: version 2, no profile, the display copy as before",
      all(P.unseal_full(x)[1]["eye_id"] == EYE.eye_id_of(raw_own) and P.unseal_full(x)[1]["profile"] is None for x in (o_np["sealed"], *o_np["sealed_sizes"].values()))
      and set(o_np) == {"image", "sealed", "sealed_sizes"})
try:
    P.protect(EYES["own"]["im"], raw_own, profile=EYES["grey"]["prof"])
    prot_other = False
except ValueError:
    prot_other = True
check("protect() refuses a profile of another eye", prot_other)

# ============================================================================================ 8. /api/enhance, /api/compose in process
section("8. /api/enhance and /api/compose with the profile (the image model is a stub)")
spec = importlib.util.spec_from_file_location("enhance", os.path.join(API, "enhance.py"))
ENH = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ENH)
spec = importlib.util.spec_from_file_location("compose", os.path.join(API, "compose.py"))
CMP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CMP)
H.MODS["enhance"], H.MODS["compose"] = ENH, CMP
MODEL = []


def fake_gemini_image(prompt, im, size=None, thinking=None, model=None):
    MODEL.append(1)
    return im.filter(ImageFilter.UnsharpMask(2, 60, 2))


L.gemini_image = fake_gemini_image
EVENTS = []
_real_record = E.record


def spy_record(kind, **fields):
    EVENTS.append((kind, dict(fields)))
    return False


E.record = spy_record
PUBLIC = os.path.join(REPO, "public", "assets")
CROP_RAW = open(os.path.join(PUBLIC, "sample_eye_blue_before.jpg"), "rb").read()
SAMPLE_RAW = open(os.path.join(PUBLIC, "sample_eye_blue_restored.jpg"), "rb").read()
TICKET = L.mint_ticket("work")
t0 = time.process_time()
out_e = ENH.enhance({"crop": b64(CROP_RAW), "mode": "artistic", "pad": 1.12, "ticket": TICKET, "lang": "en"})
cpu_enh = time.process_time() - t0
pl_e, me_e = P.unseal_full(out_e["sealed"])
check("enhance: the reply carries profile (public part) beside image, sealed and sealed_sizes; the old fields are all still there",
      out_e["ok"] is True and {"image", "sealed", "sealed_sizes", "fidelity", "used_sr", "fallback", "seconds", "qa", "mode"} <= set(out_e)
      and set(out_e["profile"]) == {"eye_id", "v", "cls", "ease", "pupil", "gate"} and out_e["profile"]["eye_id"] == EYE.eye_id_of(pl_e), out_e.get("profile"))
check("enhance: the profile was measured on the clean preview bytes (what the seal holds), sealed into all three blobs, equal to a fresh measurement",
      me_e["profile"] is not None and me_e["profile"].rec == EYE.profile_of_bytes(pl_e, pad=1.12).rec
      and all(P.unseal_full(v)[1]["profile"].rec == me_e["profile"].rec for v in out_e["sealed_sizes"].values())
      and out_e["profile"] == me_e["profile"].public())
check("enhance: the event carries codes and numbers only, all allowed by events.FIELDS (gate, reason, cls, pupil, profile_ms)",
      (lambda ev: ev is not None and {"gate", "reason", "cls", "pupil", "profile_ms"} <= set(ev[1]) and set(E.build("enhance", ev[1])) >= {"gate", "cls", "pupil", "profile_ms"}
       and all(isinstance(ev[1][k], str) for k in ("gate", "reason", "cls", "pupil")))(next((e for e in EVENTS if e[0] == "enhance"), None)), EVENTS[-1:])
EVENTS.clear()
# the time guard: too little time left: the seals carry the id alone and the reply says unknown
_real_left = L.time_left
L.time_left = lambda default=L.BUDGET: 3.0
try:
    out_g = ENH.enhance({"crop": b64(CROP_RAW), "mode": "artistic", "pad": 1.12, "ticket": TICKET})
finally:
    L.time_left = _real_left
m_g = P.unseal_full(out_g["sealed"])[1]
ev_g = next((e for e in EVENTS if e[0] == "enhance"), (None, {}))[1]
check("enhance: with less than 6 s left the profile is not measured: the reply says unknown, the seals carry the id and no profile, the event says gate unknown",
      out_g["profile"].get("unknown") is True and out_g["profile"]["eye_id"] == m_g["eye_id"] and m_g["profile"] is None and m_g["v"] == 2
      and ev_g.get("gate") == "unknown" and "profile_ms" not in ev_g and out_g["ok"] is True, (out_g.get("profile"), ev_g))
EVENTS.clear()
_real_pob = EYE.profile_of_bytes


def boom(*a, **k):
    raise RuntimeError("synthetic failure of the measurement")


EYE.profile_of_bytes = boom
try:
    out_f = ENH.enhance({"crop": b64(CROP_RAW), "mode": "artistic", "pad": 1.12, "ticket": TICKET})
finally:
    EYE.profile_of_bytes = _real_pob
check("enhance: a measurement that fails never costs the preview (200 with the display copy and the seals, profile unknown)",
      out_f["ok"] is True and out_f["profile"].get("unknown") is True and P.unseal(out_f["sealed"]) and P.is_display(base64.b64decode(out_f["image"])))
EVENTS.clear()
calls = len(MODEL)
out_s = ENH.enhance({"sample": True, "image": b64(SAMPLE_RAW), "lang": "en"})
out_s2 = ENH.enhance({"sample": True, "image": b64(SAMPLE_RAW), "lang": "en"})
check("enhance: the sample eye's seals carry its profile too (no model call), measured once per instance",
      len(MODEL) == calls and P.unseal_full(out_s["sealed"])[1]["profile"] is not None and out_s["profile"]["cls"] in EYE.CLASSES
      and P.unseal_full(out_s["sealed"])[1]["profile"].rec == P.unseal_full(out_s2["sealed"])[1]["profile"].rec == EYE.profile_of_bytes(SAMPLE_RAW, memo=True).rec)
print(f"   enhance CPU seconds with the stub model: {cpu_enh:.1f} (the profile part is 1 to 2)", flush=True)

# compose with the sealed copies
sealed3 = [out_e["sealed_sizes"]["768"], out_s["sealed_sizes"]["768"], out_e["sealed_sizes"]["768"]]
r_c = CMP.compose({"sealed": sealed3, "style": "celestial_gold", "layout": "triangle", "names": "", "pad": 1.12, "lang": "en"})
check("compose: the reply gains eyes[] (eye, eye_id, cls, pupil, gate per rule) from the sealed profiles; the old fields are unchanged",
      {"ok", "style", "layout", "layouts", "format", "count", "width", "height", "image", "styles", "qa"} <= set(r_c) and len(r_c["eyes"]) == 3
      and r_c["eyes"][0]["eye_id"] == out_e["profile"]["eye_id"] and r_c["eyes"][1]["eye_id"] == out_s["profile"]["eye_id"]
      and r_c["eyes"][0]["gate"] == {"lid": out_e["profile"]["gate"]["lid"]["ok"], "fill": out_e["profile"]["gate"]["fill"]["ok"]}
      and r_c["eyes"][0]["cls"] == out_e["profile"]["cls"] and [e["eye"] for e in r_c["eyes"]] == [1, 2, 3], r_c.get("eyes"))
ev_c = next((e for e in EVENTS if e[0] == "compose"), (None, {}))[1]
check("compose: the event carries the set-level gate (ok, or the first failing eye's reason code, or unknown), a code E.build keeps",
      ev_c.get("gate") in ("ok", "unknown") or ev_c.get("gate") in GATE.WHY["lid"] and E.build("compose", ev_c).get("gate") == ev_c.get("gate"), ev_c)
EVENTS.clear()
r_old = CMP.compose({"irises": [b64(pl_e)], "style": "celestial_gold", "pad": 1.12, "lang": "en"})
r_new = CMP.compose({"sealed": [out_e["sealed"]], "style": "celestial_gold", "pad": 1.12, "lang": "en"})
check("compose: an old page's plain iris gives the same artwork as the sealed one, with unknown gates and no eye id (old page unchanged)",
      r_old["image"] == r_new["image"] and r_old["eyes"] == [{"eye": 1, "eye_id": None, "cls": None, "pupil": None, "gate": {"lid": None, "fill": None}}]
      and next(e for e in EVENTS if e[0] == "compose")[1]["gate"] == "unknown", r_old["eyes"])
lid_seal = P.protect(EYES["own_lid"]["im"], EYES["own_lid"]["raw"], profile=EYES["own_lid"]["prof"])
EVENTS.clear()
r_l = CMP.compose({"sealed": [out_e["sealed_sizes"]["560"], lid_seal["sealed_sizes"]["560"]], "style": "celestial_gold", "layout": "duo", "pad": 1.12})
check("compose: a set with an eye that fails the lid rule reports that eye and the reason code at set level",
      r_l["eyes"][1]["gate"]["lid"] is False and next(e for e in EVENTS if e[0] == "compose")[1]["gate"] in GATE.WHY["lid"], (r_l["eyes"], EVENTS[-1:]))
v1_sz = P.seal(P.unseal(out_e["sealed_sizes"]["768"]), kind=P.KIND_COMPOSE)
EVENTS.clear()
r_v1 = CMP.compose({"sealed": [v1_sz], "style": "celestial_gold", "pad": 1.12})
check("compose: a version 1 seal (a page loaded before the deploy) still composes; its gate is unknown",
      r_v1["ok"] and r_v1["eyes"][0]["gate"] == {"lid": None, "fill": None} and r_v1["eyes"][0]["eye_id"] is None
      and next(e for e in EVENTS if e[0] == "compose")[1]["gate"] == "unknown")
E.record = _real_record

# the event vocabulary
section("9. events: the fields and the counts")
ev = E.build("enhance", {"gate": "lid", "reason": "lid_ring_outliers", "cls": "grey", "pupil": "round", "profile_ms": 1234, "mode": "faithful"})
check("events.build keeps the enhance profile fields and drops what is not a code (a space, an @, a number where a code belongs)",
      ev["gate"] == "lid" and ev["cls"] == "grey" and ev["profile_ms"] == 1234
      and "gate" not in E.build("enhance", {"gate": "has space"}) and "cls" not in E.build("enhance", {"cls": "a@b"}) and "reason" not in E.build("enhance", {"reason": 5}))
agg = E.empty()
for e_ in ({"gate": "ok", "cls": "own", "pupil": "round", "reason": "none", "profile_ms": 1000}, {"gate": "lid", "cls": "grey", "pupil": "round", "reason": "lid_ring_outliers", "profile_ms": 3000},
           {"gate": "unknown", "reason": "none"}, {"gate": "ok", "cls": "own", "pupil": "slit", "reason": "none", "profile_ms": 2000}):
    E.add(agg, E.build("enhance", dict(e_, mode="faithful")))
E.add(agg, E.build("compose", {"style": "supernova", "eyes": 2, "gate": "lid_deviation"}))
E.add(agg, E.build("compose", {"style": "supernova", "eyes": 1}))
check("the daily counts: gate per eye, reason (not 'none'), class, pupil, compose gate; the profile time joins the averages",
      agg["enhance_gate"] == {"ok": 2, "lid": 1, "unknown": 1} and agg["enhance_reason"] == {"lid_ring_outliers": 1}
      and agg["enhance_class"] == {"own": 2, "grey": 1} and agg["enhance_pupil"] == {"round": 2, "slit": 1}
      and agg["compose_gate"] == {"lid_deviation": 1} and agg["ms"]["profile"] == [6000, 3], {k: agg[k] for k in agg if "gate" in k or "enhance_" in k})
mrg = E.merge(agg, agg)
check("merge adds the new tables like the old ones", mrg["enhance_gate"] == {"ok": 4, "lid": 2, "unknown": 2} and mrg["ms"]["profile"] == [12000, 6])

# ============================================================================================ 10. the order draft and the master's record
section("10. the order draft stores the id and the sealed profile; the master's record carries the id")


def post(path, body):
    r_ = requests.post(BASE + path, data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=180)
    try:
        return r_.status_code, r_.json()
    except ValueError:
        return r_.status_code, {"raw": r_.text[:200]}


def rec_of(order, eye):
    with open(os.path.join(STORE, "orders", order, "draft", f"eye_{eye}.json"), encoding="utf-8") as f:
        return json.load(f)


def draft(eye=1, order=None, k=None, **kw):
    b = {"action": "draft", "eye": eye, "crop": b64(CROP_RAW), "pad": 1.12, "lang": "en", "ref": f"eye-{eye}",
         "ticket": H.fresh_ticket() if order is None else TICKET}
    if order:
        b.update(order=order, k=k)
    b.update(kw)
    return post("/api/order", b)


c, jd = draft(sealed=out_e["sealed"])
O1, K1 = jd.get("order"), jd.get("k")
e1 = rec_of(O1, 1) if c == 200 else {}
check("draft with a sealed preview: the eye record gains eye_id (the preview's sha256 prefix) and the sealed profile, exactly the one the seal carried",
      c == 200 and e1.get("eye_id") == e1["preview"]["sha256"][:16] == me_e["eye_id"] and e1.get("profile") == me_e["profile"].rec and EYE.validate(e1["profile"]), (c, jd))
c, jd2 = draft(2, O1, K1, sealed=out_g["sealed"])
e2 = rec_of(O1, 2) if c == 200 else {}
check("draft with a seal whose profile was not measured: the id is stored, no profile (the gate is unknown)",
      c == 200 and e2.get("eye_id") == P.unseal_full(out_g["sealed"])[1]["eye_id"] and "profile" not in e2, (c, jd2, e2))
c, jd3 = draft(3, O1, K1, sealed=P.seal(pl_e))
e3 = rec_of(O1, 3) if c == 200 else {}
check("draft with a version 1 seal (a preview sealed before the deploy): the id is the hash of the bytes, no profile",
      c == 200 and e3.get("eye_id") == EYE.eye_id_of(pl_e) and "profile" not in e3, (c, jd3))
c, jd4 = draft(4, O1, K1, preview=b64(pl_e))
e4 = rec_of(O1, 4) if c == 200 else {}
check("draft with an old page's plain preview: the id is the hash of the bytes, no profile (old page unchanged)",
      c == 200 and e4.get("eye_id") == EYE.eye_id_of(pl_e) and "profile" not in e4, (c, jd4))
c, jd5 = draft(5, O1, K1, sealed=out_e["sealed_sizes"]["768"])
check("a compose copy is still refused as an order's preview, and a forged profile in a seal never reaches a draft (tag first)",
      c == 400 and jd5.get("reason") == "preview_invalid" and draft(5, O1, K1, sealed=flipped(out_e["sealed"], head_n + 30))[1].get("reason") == "preview_invalid")
c, ja = post("/api/order", {"action": "arrange", "order": O1, "k": K1, "slots": [2, 1]})
check("arrange moves the eye records with their profile (slot 1 and 2 swap, the profile follows its eye)",
      c == 200 and rec_of(O1, 1)["eye_id"] == e2["eye_id"] and "profile" not in rec_of(O1, 1) and rec_of(O1, 2).get("profile") == me_e["profile"].rec, (c, ja))

# master_eye: the id of the preview, and the record
ME = H.MODS["order"].ME
check("master_eye reads the id of the preview it is given: sealed (it wins), plain, a data URL, none",
      ME._preview_eye_id(None, out_e["sealed"]) == me_e["eye_id"] and ME._preview_eye_id(b64(pl_e), None) == me_e["eye_id"]
      and ME._preview_eye_id("data:image/jpeg;base64," + b64(pl_e), None) == me_e["eye_id"] and ME._preview_eye_id("not an image", out_e["sealed"]) == me_e["eye_id"]
      and ME._preview_eye_id(None, None) is None and ME._preview_eye_id("%%%", None) is None and ME._preview_eye_id(None, "garbage") is None)
LAB = "lab-20261005-profile1"
_real_4k = ME._render_4k
pv_im = Image.open(io.BytesIO(pl_e)).convert("RGB")


def fake_4k(base, order, eye, prompt=None):
    return pv_im.resize((4096, 4096), Image.LANCZOS), 1, {"prompt": 0, "output": 0}


ME._render_4k = fake_4k
try:
    r_me = ME.master_eye({"crop": b64(CROP_RAW), "sealed": out_e["sealed"], "pad": 1.12, "order": LAB, "eye": 1,
                          "ticket": L.mint_ticket(store.unlock_kind(LAB))})
    me_rec = store.get_json(f"orders/{LAB}/eye_1.json")
finally:
    ME._render_4k = _real_4k
check("the master's eye record carries eye_id: the preview's id, next to preview_sha (the approved preview and the master share one id)",
      r_me["ok"] and me_rec.get("eye_id") == me_e["eye_id"] and me_rec.get("preview_sha") and me_rec["input"] == "preview", me_rec)

# ============================================================================================ 11. the other readers still work
section("11. nothing else changed")
check("no module of the new package writes a file, no secret is in the new files (no key, no token, no ticket value)",
      not any(re.search(r"(sk_live|sk_test|whsec_|AIza|re_[A-Za-z0-9]{12})", s) for s in srcs.values()))
check("the registry, the catalogue and the gate agree on the rule names: every gate_rules value of the engine literal is a rule the gate module has",
      {e["gate_rules"] for e in CAT.ENGINE.values()} <= set(GATE.RULES))
check("the catalogue reads the profile's fields as they are stored: _problem needs gate{rule}{ok}, pupil{cls}, cls (a hard style on a failed gate says gate, a bar pupil bar_pupil, unknown reseal)",
      (lambda rec: CAT._problem("duo.collision_infinity", [rec]) is None)(EYES["own"]["prof"].rec)
      and CAT._problem("duo.collision_infinity", [EYES["own_lid"]["prof"].rec]) == "gate"
      and CAT._problem("duo.collision_infinity", [EYES["bar"]["prof"].rec]) == "bar_pupil"
      and CAT._problem("duo.collision_infinity", [{"cls": "own"}]) == "reseal"
      and CAT._problem("solo.universe", [EYES["own_lid"]["prof"].rec]) == "gate" and CAT._problem("solo.universe", [EYES["own"]["prof"].rec]) is None
      and CAT.set_class([p_own.rec, p_grey.rec]) == "grey" and CAT.set_class([p_own.rec, p_brown.rec]) == "dark_brown" and CAT.set_class([p_own.rec]) == "own")

# ============================================================================================ 12. the real calibration set (local only)
section("12. the calibration set (local only: SNAPEYES_CALIB and SNAPEYES_GATE_TABLE)")
if CALIB and GATE_TABLE and os.path.isdir(CALIB) and os.path.isfile(GATE_TABLE):
    table = json.load(open(GATE_TABLE, encoding="utf-8"))
    mism, n_seen, ts = [], 0, []
    for row in table:
        fp = os.path.join(CALIB, row["eye"] + "_2_enhanced.jpg")
        if not os.path.isfile(fp):
            continue
        n_seen += 1
        rawc = open(fp, "rb").read()
        t0 = time.process_time()
        pc = EYE.profile_of_bytes(rawc)
        ts.append(time.process_time() - t0)
        gl, gfv = pc.gate("lid"), pc.gate("fill")
        want_l = dict(re.findall(r"(\w+)=([-\d.]+)", row["cx"]))
        want_f = dict(re.findall(r"(\w+)=([-\d.]+)", row["uni"]))
        got_l = {"lid70": gl["values"]["lid70"], "lid88": gl["values"]["lid88"], "ob": gl["values"]["outlier_bins"], "md": gl["values"]["maxdev70"]}
        got_f = {"run18": gfv["values"]["run18"], "step": gfv["values"]["n_step"], "catch": gfv["values"]["catch"]}
        okl = gl["ok"] == row["cx_ok"] and all(abs(float(want_l[k]) - v) < 1e-6 for k, v in got_l.items())
        okf = gfv["ok"] == row["uni_ok"] and all(abs(float(want_f[k]) - v) < 1e-6 for k, v in got_f.items())
        if not (okl and okf and pc.cls == row["cls"] and EYE.is_eye_id(pc.eye_id)):
            mism.append((row["eye"], okl, okf, pc.cls, row["cls"]))
    local(f"gate table reproduced on {n_seen} real restorations: lid and fill pass or fail and every value equal to 1e-6, class equal", n_seen >= 29 and not mism, mism)
    npass = (sum(1 for r_ in table if r_["cx_ok"]), sum(1 for r_ in table if r_["uni_ok"]), sum(1 for r_ in table if r_["cx_ok"] and r_["uni_ok"]))
    local(f"the table says lid passes {npass[0]}, fill {npass[1]}, both {npass[2]} (the plan's 19, 19, 17)", npass == (19, 19, 17), npass)
    local(f"profile CPU per real eye: median {sorted(ts)[len(ts) // 2]:.2f} s, worst {max(ts):.2f} s (at most 3 s)", max(ts) <= 3.0, max(ts))
else:
    print("   (skipped: SNAPEYES_CALIB and SNAPEYES_GATE_TABLE are not set)", flush=True)

# ------------------------------------------------------------------
shutil.rmtree(TMP, ignore_errors=True)
ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed" + (f"   (+ {len(LOCAL)} local checks)" if LOCAL else ""))
sys.exit(0 if ok == len(RESULTS) and all(LOCAL) else 1)
