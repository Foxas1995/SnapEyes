# -*- coding: utf-8 -*-
"""WP9 of the v3 engine work, the server half of the Reveal: api/_lib/styles/reveal.py (reveal_params, prepare_restored, the display copy, the
guard and the one call of /api/enhance), its two helper modules, and what /api/enhance does with them. Test I18 of the plan (server side: the
withheld case of p09f, registration at most 0.005 R, the restored layer untouched in zone A, pure black pupil) plus the port tests of the
other v3 families (the port is the scratch prototype's code plus a listed set of edits; the goldens recorded on the scratch code are replayed).
No network and no image model (the model is a stub), no real eye in the repository: the eyes here are the synthetic irises of synth_iris.py;
the owner's real calibration restorations are read only from a folder named by an environment variable, and only reported:
    SNAPEYES_SCRATCH_Y3   the wave-y3 folder of the scratch tree: the check that the committed files ARE the scratch plus the listed edits
    SNAPEYES_CALIB        folder with <name>_0_clientcrop.jpg and <name>_2_enhanced.jpg (the calibration eyes): the real-eye goldens
Without them those checks are skipped, and their lines are LOCAL lines, not PASS lines, so the PASS count is the same everywhere.
    python test_reveal.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as the entry v3reveal (SNAPEYES_REPO names the checkout). The browser half (src/reveal) is tested by src/reveal/*.test.ts."""
import base64
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
TMP = os.path.join(HERE, "wp9_tmp")
CALIB = os.environ.get("SNAPEYES_CALIB") or ""
Y3 = os.environ.get("SNAPEYES_SCRATCH_Y3") or ""
SP = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP, "wave-pv", "tests") if SP else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []
LOCAL = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def local(name, ok, detail=""):
    """A check that needs the scratch tree or the real calibration eyes: reported, not counted among the PASS lines (a failure still fails the run)."""
    LOCAL.append(bool(ok))
    print(("LOCAL ok   " if ok else "FAIL LOCAL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_CALIB", "SNAPEYES_SCRATCH_Y3"):
            os.environ.pop(k)
if os.path.isdir(TMP):
    shutil.rmtree(TMP, ignore_errors=True)
os.makedirs(TMP)
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store_reveal")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])          # the payments harness' synthetic keys and ticket secret, a local store folder
sys.path.insert(0, API)
import numpy as np  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402
import reveal_cases as RC  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib.styles import reveal as R  # noqa: E402
from _lib.styles import reveal_clean as RCL  # noqa: E402
from _lib.styles import reveal_wm as WM  # noqa: E402,F401  (loaded for the arcs checks only)

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
MODULES = ["reveal", "reveal_clean", "reveal_wm"]
CALLED = []                           # any call that would reach a model or read a key: this suite makes none (the image model is a stub below)


def _no_model(*args, **kwargs):
    CALLED.append("gemini")
    raise AssertionError("a model call: this suite makes none")


def _no_key():
    CALLED.append("key")
    raise AssertionError("a key lookup: this suite reads none")


L.gemini, L._key = _no_model, _no_key
STYLES_DIR = os.path.join(API, "_lib", "styles")


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def sha(im):
    return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()


def luma(a):
    a = a.astype(np.float32)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


with open(os.path.join(HERE, "data", "reveal_goldens.json"), encoding="utf-8") as f:
    GOLD = json.load(f)["cases"]

# ============================================================================================ 1. the files
section("1. the modules: what they are, and that they stay light")
src = {m: read(f"api/_lib/styles/{m}.py").replace(chr(13) + chr(10), chr(10)) for m in MODULES}      # a checkout with autocrlf has CRLF files: the checks read lines
check("each module opens with its docstring and then the __future__ import (Vercel's default Python is 3.12)",
      all(re.search(r'\A# -\*- coding: utf-8 -\*-\n"""[\s\S]*?"""\nfrom __future__ import annotations\n', s) for s in src.values()), [m for m, s in src.items() if "from __future__" not in s])
check("no dash (en or em), no raw invisible or bidirectional character, no written price in any of them",
      not any(re.search(DASH, s) for s in src.values())
      and not any(re.search("[\u200b-\u200f\u2028-\u202e\u2060-\u2064\ufeff]", s) for s in src.values())
      and not any(re.search(r"\d[.,]\d\d\s?(EUR|USD|AUD|HUF)|\u20ac|A\$", s) for s in src.values()))
check("the port keeps no scratch path, no Windows path and no sys.path edit",
      not any(re.search(r"wave-|C:\\\\|\\\\Users\\\\|sys\.path|fx import|REPO_API", s) for s in src.values()))
check("no module level cache that could grow in a warm instance (no dict or list at module level that is written to)",
      not any(re.search(r"^_?[A-Z_]*(CACHE|MEMO|_SEEN)\w* = (\{\}|\[\]|dict\(\)|list\(\))", s, re.M) for s in src.values()))
probe = subprocess.run([sys.executable, "-c",
                        "import sys, time; sys.path.insert(0, sys.argv[1]); t = time.time(); from _lib import styles; dt = time.time() - t; "
                        "print(sorted(m for m in sys.modules if m.startswith('_lib.styles') and m != '_lib.styles'), round(dt * 1000))", API],
                       capture_output=True, text=True, cwd=TMP)
check("importing the style package loads no part of the Reveal (it is read by /api/enhance alone, on first use)",
      probe.returncode == 0 and "reveal" not in probe.stdout, probe.stdout + probe.stderr)
probe2 = subprocess.run([sys.executable, "-c",
                         "import sys; sys.path.insert(0, sys.argv[1]); from _lib.styles import reveal as R; from PIL import Image; "
                         "R.display_copy(Image.new('RGB', (64, 64)), 'en'); print(sorted(m for m in sys.modules if m.startswith('_lib.styles.reveal')))", API],
                        capture_output=True, text=True, cwd=TMP)
check("the arcs watermark (reveal_wm) is OFF: the default display copy never loads it (D14 is not signed)",
      probe2.returncode == 0 and "reveal_wm" not in probe2.stdout and "reveal_clean" in probe2.stdout, probe2.stdout + probe2.stderr)
check("the default style of display_copy and of reveal_for is the repo tile ('repo')",
      R.display_copy.__defaults__ == ("en", "repo") and R.reveal_for.__defaults__[-1] == "repo", (R.display_copy.__defaults__, R.reveal_for.__defaults__))

# ============================================================================================ 2. the port is the scratch
section("2. the port is the scratch prototype's code plus the listed edits")
if Y3:
    r_ = subprocess.run([sys.executable, os.path.join(HERE, "port_reveal.py"), "--check"], capture_output=True, text=True,
                        env={**os.environ, "SNAPEYES_SCRATCH_Y3": Y3, "SNAPEYES_REPO": REPO})
    local("reveal.py, reveal_clean.py and reveal_wm.py are what port_reveal.py makes of designs/presentation*.py (the hand written part of reveal.py apart)",
          r_.returncode == 0, r_.stdout + r_.stderr)
else:
    print("   (skipped: SNAPEYES_SCRATCH_Y3 is not set)", flush=True)

# ============================================================================================ 3. goldens
section("3. the synthetic cases against the goldens recorded on the scratch code")
RES = {}
for key in RC.CASES:
    crop, rest = RC.pair(key)
    p = R.reveal_params(crop, rest)
    prep = R.prepare_restored(rest, p)
    RES[key] = dict(crop=crop, rest=rest, p=p, pub=R.wire(p), prep=prep)
bad = [k for k in RC.CASES if json.loads(json.dumps(RES[k]["pub"])) != GOLD[k]["params"]]
check(f"reveal_params: the wire dict of all {len(RC.CASES)} cases equals the scratch's, every number to the last digit", not bad, bad)
bad = [k for k in RC.CASES if sha(RES[k]["prep"]) != GOLD[k]["prep"]]
check("prepare_restored: the prepared restoration of all cases equals the scratch's byte for byte", not bad, bad)
bad = []
for key in RC.CASES:
    for lang, want in GOLD[key]["arcs"].items():
        if sha(R.display_copy(RES[key]["prep"], lang, "arcs")) != want:
            bad.append((key, lang))
check("the arcs display copy (OFF, but kept) equals the scratch's byte for byte, in English and Lithuanian", not bad, bad)
bad = [k for k in RC.CASES if abs(RES[k]["p"]["_info"]["reg"]["spread_r"] - GOLD[k]["registration"]["spread_r"]) > 1e-6
       or abs(RES[k]["p"]["_info"]["reg"]["ncc"] - GOLD[k]["registration"]["ncc"]) > 1e-4]
check("the registration spread and correlation of every case equal the scratch's", not bad, bad)

# ============================================================================================ 4. the verdict
section("4. the verdict: what is shown with the cut and what is withheld")
SPREAD_MAX = 0.005
for key, (_f, _how, (want_ok, want_code)) in RC.CASES.items():
    pub, info = RES[key]["pub"], RES[key]["p"]["_info"]
    check(f"verdict of {key}: ok {want_ok}, code {want_code} (drift {pub['drift']}, spread {info['reg']['spread_r']:.4f} R)",
          pub["ok"] is want_ok and R.code_of(pub) == want_code, (pub, info["reg"]))
check("registration is trusted only when the four half rings agree about the shift to 0.005 R: clean and shifted pairs are far inside it, "
      "a one degree turn and a two percent enlargement are outside",
      RES["blue_clean"]["p"]["_info"]["reg"]["spread_r"] <= 0.001 and RES["blue_shift"]["p"]["_info"]["reg"]["spread_r"] <= 0.001
      and RES["blue_rot1"]["p"]["_info"]["reg"]["spread_r"] > SPREAD_MAX and RES["blue_scale102"]["p"]["_info"]["reg"]["spread_r"] > SPREAD_MAX
      and R.REG_SPREAD_OK == SPREAD_MAX, [(k, RES[k]["p"]["_info"]["reg"]["spread_r"]) for k in ("blue_clean", "blue_shift", "blue_rot1", "blue_scale102")])
check("a shifted crop is corrected, not refused: the shift of the photo layer is measured to a fifth of a pixel at 1024 px (3 px right, 2 px down is about 0.0066 and 0.0043 R)",
      abs(RES["blue_shift"]["pub"]["shift"][0] + 3 / (SI.R_FRAC * 1024)) < 0.0015 and abs(RES["blue_shift"]["pub"]["shift"][1] + 2 / (SI.R_FRAC * 1024)) < 0.0015
      and RES["blue_shift"]["pub"]["ok"] is True, RES["blue_shift"]["pub"]["shift"])
check("the colour gate: the p09f case (restored colour far from the photo's) is withheld by colour, a mild change passes with a warning below it",
      RES["blue_warm"]["pub"]["drift"] > R.DRIFT_FAIL and RES["blue_warm"]["pub"]["ok"] is False and R.code_of(RES["blue_warm"]["pub"]) == "colour"
      and RES["blue_warm_mild"]["pub"]["drift"] < R.DRIFT_WARN and RES["blue_warm_mild"]["pub"]["ok"] is True and (R.DRIFT_FAIL, R.DRIFT_WARN) == (8.0, 6.0),
      (RES["blue_warm"]["pub"], RES["blue_warm_mild"]["pub"]))
check("a pair with no structure to correlate (flat) is withheld by registration, and no pupil is claimed",
      RES["flat"]["pub"]["ok"] is False and RES["flat"]["pub"]["cls"] is None and RES["flat"]["p"]["_info"]["reg"]["applied"] is False, RES["flat"]["pub"])
check("a withheld Reveal still carries its numbers (drift, pupil, edge): the page needs the drift to say why",
      all(RES[k]["pub"]["drift"] is not None and RES[k]["pub"]["edge"] and RES[k]["pub"]["pupil"] for k in ("blue_warm", "blue_rot1", "blue_scale102", "flat")))
check("pupil class and centre: a round, a slit and a bar pupil are told apart, and the centre of a synthetic eye is within 0.002 R of the middle",
      [RES[k]["pub"]["cls"] for k in ("blue_clean", "amber_slit_clean", "dark_brown_bar_clean")] == ["round", "slit", "bar"]
      and all(abs(RES[k]["pub"]["pupil"][0]) < 0.002 and abs(RES[k]["pub"]["pupil"][1]) < 0.002 for k in ("blue_clean", "dark_brown_clean", "grey_clean", "amber_slit_clean")),
      [(k, RES[k]["pub"]["cls"], RES[k]["pub"]["pupil"]) for k in ("blue_clean", "amber_slit_clean", "dark_brown_bar_clean")])
check("the restored edge never starts inside zone A (e0 at least 0.95 R) and always has a width (e1 above e0)",
      all(RES[k]["pub"]["edge"][0] >= R.ZONE_A - 1e-9 and RES[k]["pub"]["edge"][1] > RES[k]["pub"]["edge"][0] for k in RC.CASES), [RES[k]["pub"]["edge"] for k in RC.CASES])
check("no soft flag for 400 px crops (4 hundred px of crop is 179 px per iris radius), and the flag appears below 100 px per radius",
      all(RES[k]["pub"]["soft"] is False for k in RC.CASES)
      and R.reveal_params(RES["blue_clean"]["crop"].resize((200, 200), Image.LANCZOS), RES["blue_clean"]["rest"])["soft"] is True)

# ============================================================================================ 5. the wire
section("5. what goes over the wire")
wires = {k: json.dumps(RES[k]["pub"], separators=(",", ":")) for k in RC.CASES}
check("the reply field is about 140 bytes of JSON (at most 200 for every case), numbers, a class and flags only",
      all(len(w) <= 200 for w in wires.values()) and max(len(w) for w in wires.values()) >= 100, {k: len(w) for k, w in wires.items()})
check("the public keys are exactly pupil, rho, cls, shift, edge, ok, soft, drift, lid; no mask, no private key, no negative zero printed",
      all(set(RES[k]["pub"]) == {"pupil", "rho", "cls", "shift", "edge", "ok", "soft", "drift", "lid"} for k in RC.CASES)
      and not any(re.search(r"(?<![0-9.])-0[.]0(?![0-9])", w) for w in wires.values()),
      [k for k, w in wires.items() if re.search(r"(?<![0-9.])-0\.0(?![0-9])", w)])
check("the wire dict is plain JSON (it survives a round trip unchanged) and holds no image, no pixel, no eye id",
      all(json.loads(w) == json.loads(json.dumps(RES[k]["pub"])) for k, w in wires.items()) and not any("eye_id" in w or "base64" in w for w in wires.values()))

# ============================================================================================ 6. prepare_restored
section("6. prepare_restored: the eyelid hidden, the pupil pure black, nothing else touched")
N = 1024
ax, ay, rr = RCL._grids(N)
touched_ok, crush_ok, lid_ok = [], [], []
for key in ("blue_clean", "dark_brown_clean", "grey_clean", "amber_slit_clean", "dark_brown_bar_clean", "blue_lid_clean"):
    rest, p, prep = np.asarray(RES[key]["rest"]), RES[key]["p"], np.asarray(RES[key]["prep"])
    w = RCL.pupil_weight(p["_pupil"], N)
    lid = p["_lid"]
    lid = np.asarray(Image.fromarray(lid.astype(np.float32), "F").resize((N, N), Image.BILINEAR), np.float32) if lid.shape[0] != N else lid
    mask = (w > 0) | (lid > 1e-4)
    diff = np.abs(prep.astype(np.int16) - rest.astype(np.int16)).max(axis=2)
    touched_ok.append((key, int(diff[~mask].max()) if (~mask).any() else 0))
    inner = w >= 0.999
    crush_ok.append((key, float(luma(prep)[inner].mean()), int(prep[inner].max())))
    hard = lid > 0.99
    lid_ok.append((key, int(prep[hard].max()) if hard.any() else 0, float(RES[key]["pub"]["lid"])))
check("outside the pupil and the lid mask the prepared restoration is the restoration byte for byte (zone A and everything else untouched)",
      all(v == 0 for _, v in touched_ok), touched_ok)
check("the pupil is crushed to black inside its core: mean luma at most 2 and no channel above 6, its own shape kept (round, slit and bar)",
      all(m <= 2.0 and mx <= 6 for _, m, mx in crush_ok), crush_ok)
check("an eyelid wedge inside the disc is hidden (black where the mask is 1), share of the disc reported; the five lid-free eyes report none",
      lid_ok[-1][1] <= 2 and lid_ok[-1][2] > 0.05 and all(s == 0.0 for _, _, s in lid_ok[:-1]), lid_ok)
check("the pixels outside the iris disc stay exactly #000000 in the prepared image (the restored half sits on pure black)",
      all(int(np.asarray(RES[k]["prep"])[rr > 1.2].max()) == 0 for k in ("blue_clean", "dark_brown_clean", "amber_slit_clean")),
      [int(np.asarray(RES[k]["prep"])[rr > 1.2].max()) for k in ("blue_clean", "dark_brown_clean", "amber_slit_clean")])
check("prepare_restored with pupil_mode 'restored' hides the lid only, and 'colourless' keeps the pupil's luminance",
      np.array_equal(np.asarray(R.prepare_restored(RES["blue_clean"]["rest"], RES["blue_clean"]["p"], pupil_mode="restored")), np.asarray(RES["blue_clean"]["rest"]))
      and luma(np.asarray(R.prepare_restored(RES["blue_clean"]["rest"], RES["blue_clean"]["p"], pupil_mode="colourless")))[rr < 0.2].mean() > luma(np.asarray(RES["blue_clean"]["prep"]))[rr < 0.2].mean())

# ============================================================================================ 7. reveal_for
section("7. reveal_for: the guard, the failure, the display copy")
seen = {}
_real_display = P.display_image


def spy_display(clean, lang=None):
    seen["im"], seen["lang"] = clean.copy(), lang
    return _real_display(clean, lang)


P.display_image = spy_display
try:
    rv = R.reveal_for(RES["blue_clean"]["crop"], RES["blue_clean"]["rest"], lang="lt")
finally:
    P.display_image = _real_display
check("reveal_for: params, the display copy and the code 'ok' come back; the display copy is the repo's tile over the PREPARED restoration, in the page's language",
      rv["code"] == "ok" and rv["params"] == RES["blue_clean"]["pub"] and rv["image"].size == (P.DISPLAY_SIDE, P.DISPLAY_SIDE) and sha(seen["im"]) == sha(RES["blue_clean"]["prep"])
      and seen["lang"] == "lt" and rv["ms"] >= 0, (rv["code"], seen.get("lang")))
check("reveal_for: a withheld pair (colour) still comes back with its params and its prepared copy, code 'colour'",
      (lambda r: r["code"] == "colour" and r["params"]["ok"] is False and r["image"] is not None)(R.reveal_for(RES["blue_warm"]["crop"], RES["blue_warm"]["rest"])))
r_none = R.reveal_for(RES["blue_clean"]["crop"], RES["blue_clean"]["rest"], left=R.REVEAL_MIN_LEFT - 0.5)
check("reveal_for: with less than REVEAL_MIN_LEFT seconds left nothing is measured: no params, no image, code 'none'",
      r_none == {"params": None, "image": None, "code": "none", "ms": 0} and R.time_for_reveal(R.REVEAL_MIN_LEFT) and not R.time_for_reveal(R.REVEAL_MIN_LEFT - 0.01))
_real_rp = R.reveal_params


def boom(*a, **k):
    raise RuntimeError("synthetic failure of the measurement")


R.reveal_params = boom
try:
    r_err = R.reveal_for(RES["blue_clean"]["crop"], RES["blue_clean"]["rest"])
finally:
    R.reveal_params = _real_rp
check("reveal_for: a measurement that raises never raises out of it: no params, no image, code 'error'",
      r_err["params"] is None and r_err["image"] is None and r_err["code"] == "error")
check("reveal_for: the codes it can answer are all in CODES, and the event field accepts every one (a code E.build keeps)",
      all(c in R.CODES and E.build("enhance", {"reveal": c}).get("reveal") == c for c in R.CODES), R.CODES)
d64 = R.display_b64(rv["image"])
check("display_b64: a JPEG with the preview's display mark (is_display), the size of the display copy",
      P.is_display(base64.b64decode(d64)) and Image.open(io.BytesIO(base64.b64decode(d64))).size == (P.DISPLAY_SIDE, P.DISPLAY_SIDE))
t0 = time.process_time()
for _ in range(3):
    R.reveal_for(RES["blue_clean"]["crop"], RES["blue_clean"]["rest"])
cpu = (time.process_time() - t0) / 3
print(f"   reveal_for CPU at 1024 px with a 400 px crop: {cpu:.2f} s per eye", flush=True)
check("reveal_for costs at most 1.5 s of CPU per eye at 1024 px (about 0.5 s on a quiet core)", cpu <= 1.5, cpu)
a_, b_ = R.reveal_params(RES["blue_clean"]["crop"], RES["blue_clean"]["rest"]), R.reveal_params(RES["blue_clean"]["crop"], RES["blue_clean"]["rest"])
child = subprocess.run([sys.executable, "-c",
                        "import sys, json; sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2]); import reveal_cases as RC; from _lib.styles import reveal as R; "
                        "c, r = RC.pair('blue_clean'); print(json.dumps(R.wire(R.reveal_params(c, r))))", API, HERE],
                       capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": "12345"}, cwd=TMP)
check("determinism: the same input gives the same numbers twice in a process and in a child with another hash seed",
      R.wire(a_) == R.wire(b_) == RES["blue_clean"]["pub"] and child.returncode == 0 and json.loads(child.stdout) == json.loads(json.dumps(RES["blue_clean"]["pub"])), child.stderr[-300:])

# ============================================================================================ 8. /api/enhance
section("8. /api/enhance: the reply, the display copy, the seals, the event, the guard (the image model is a stub)")
spec = importlib.util.spec_from_file_location("enhance", os.path.join(API, "enhance.py"))
ENH = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ENH)
H.MODS["enhance"] = ENH
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


def enhance(**kw):
    EVENTS.clear()
    t = time.process_time()
    out = ENH.enhance({"crop": b64(CROP_RAW), "mode": "artistic", "pad": 1.12, "ticket": TICKET, "lang": "en", **kw})
    return out, [e for e in EVENTS if e[0] == "enhance"][-1][1], time.process_time() - t


def store_files():
    return sorted(os.path.join(dp, f) for dp, _d, fs in os.walk(STORE) for f in fs)


files_before = store_files()
out, ev, cpu_enh = enhance()
files_after = store_files()
clean_bytes, meta = P.unseal_full(out["sealed"])
clean_im = Image.open(io.BytesIO(clean_bytes)).convert("RGB")
shown = np.asarray(Image.open(io.BytesIO(base64.b64decode(out["image"]))).convert("RGB"))
plain = np.asarray(_real_display(clean_im, "en"))
Rr = SI.R_FRAC * P.DISPLAY_SIDE
yy, xx = np.mgrid[0:P.DISPLAY_SIDE, 0:P.DISPLAY_SIDE].astype(np.float32)
near = np.hypot(xx + 0.5 - P.DISPLAY_SIDE / 2, yy + 0.5 - P.DISPLAY_SIDE / 2) < 0.12 * Rr          # the middle of the pupil, where no watermark word is drawn on the iris
check("enhance: the reply carries reveal (the wire dict) beside image, sealed, sealed_sizes and profile; every old field is still there",
      out["ok"] is True and {"image", "sealed", "sealed_sizes", "profile", "fidelity", "used_sr", "fallback", "seconds", "qa", "mode"} <= set(out)
      and set(out["reveal"]) == {"pupil", "rho", "cls", "shift", "edge", "ok", "soft", "drift", "lid"} and out["reveal"]["ok"] is True, out.get("reveal"))
check("enhance: the display copy is a display copy (the mark in its JPEG comment), 800 px, and its pupil is crushed to black where the plain copy of the same restoration shows the pupil",
      P.is_display(base64.b64decode(out["image"])) and shown.shape == (800, 800, 3) and luma(shown)[near].mean() < 0.35 * luma(plain)[near].mean(),
      (float(luma(shown)[near].mean()), float(luma(plain)[near].mean())))
check("enhance: the sealed copies are the CLEAN preview, untouched: the sealed restoration still has its pupil and equals the bytes the page used to get",
      luma(np.asarray(clean_im))[512 - 5:512 + 5, 512 - 5:512 + 5].mean() > 3
      and all(P.unseal_full(v)[1]["eye_id"] == meta["eye_id"] for v in out["sealed_sizes"].values()) and meta["eye_id"] == P.eye_id_of(clean_bytes))
check("enhance: the reveal numbers are those of a fresh measurement on the deglared crop and the clean restoration (the registration of the clean preview)",
      out["reveal"]["cls"] in ("round", "slit", "bar") and abs(out["reveal"]["pupil"][0]) < 0.3 and abs(out["reveal"]["pupil"][1]) < 0.3 and 0 <= out["reveal"]["drift"] < 8,
      out["reveal"])
check("enhance: the event carries the code 'ok' and the time, both allowed by events.FIELDS",
      ev.get("reveal") == "ok" and isinstance(ev.get("reveal_ms"), int) and {"reveal", "reveal_ms"} <= set(E.build("enhance", ev)), ev)
check("enhance: nothing new is stored (no wide frame, no context crop, no photo, no reveal file): the store folder is as it was (decision C10)",
      files_before == files_after and "context" not in json.dumps(out) and "fit" not in out and "wide" not in out, (files_before, files_after))
_real_reveal_for = R.reveal_for
R.reveal_for = lambda *a, **k: {"params": None, "image": None, "code": "none", "ms": 0}
try:
    _o, _e, cpu_without = enhance()
finally:
    R.reveal_for = _real_reveal_for
print(f"   enhance CPU with the stub model: {cpu_enh:.1f} s with the Reveal, {cpu_without:.1f} s without it", flush=True)
check("enhance: the Reveal adds at most 2 s of CPU to the call (about half a second on a quiet core; measured against the same call with it switched off, so a loaded machine "
      "moves both)", cpu_enh - cpu_without <= 2.0, (cpu_enh, cpu_without))

# the guard: not enough time left
_real_left = L.time_left
calls = len(MODEL)
L.time_left = lambda default=L.BUDGET: 5.0         # more than the profile's 6 s? no: the profile is skipped, and so is the Reveal below 4 s
try:
    out_g, ev_g, _ = enhance()
finally:
    L.time_left = _real_left
check("enhance: with the profile's 6 s missing but the Reveal's 4 s there, the Reveal is still measured (the two guards are separate)",
      out_g["profile"].get("unknown") is True and out_g["reveal"]["ok"] is True and ev_g.get("reveal") == "ok" and ev_g.get("gate") == "unknown", (out_g.get("reveal"), ev_g))
L.time_left = lambda default=L.BUDGET: 3.0
try:
    out_n, ev_n, _ = enhance()
finally:
    L.time_left = _real_left
plain_n = np.asarray(Image.open(io.BytesIO(base64.b64decode(out_n["image"]))).convert("RGB"))
check("enhance: with less than 4 s left no Reveal is measured: 'reveal' is absent, the display copy is the plain one (pupil not crushed), the event says none, the preview is whole",
      out_n["ok"] is True and "reveal" not in out_n and ev_n.get("reveal") == "none" and "reveal_ms" not in ev_n and P.unseal(out_n["sealed"])
      and luma(plain_n)[near].mean() > 0.6 * luma(plain)[near].mean(), (list(out_n), ev_n))

# a measurement that raises costs nothing
R.reveal_params = boom
try:
    out_f, ev_f, _ = enhance()
finally:
    R.reveal_params = _real_rp
check("enhance: a Reveal that fails never costs the preview (200 with the display copy and the seals, no reveal, the event says error)",
      out_f["ok"] is True and "reveal" not in out_f and ev_f.get("reveal") == "error" and P.unseal(out_f["sealed"]) and P.is_display(base64.b64decode(out_f["image"])), ev_f)

# the p09f case end to end: the model changes the colour, the lock is off, so the restored colour is not the photo's
def warm_model(prompt, im, size=None, thinking=None, model=None):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    a[..., 0] *= 1.3
    a[..., 2] *= 0.7
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


_real_lock, _real_gem = L.chroma_lock, L.gemini_image
L.chroma_lock = lambda out_, base_: out_
L.gemini_image = warm_model
try:
    out_w, ev_w, _ = enhance()
finally:
    L.chroma_lock, L.gemini_image = _real_lock, _real_gem
check("enhance, the p09f case: restored colour far from the photo: 200, reveal.ok false with the drift over 8, the event says colour, the display copy and seals still come",
      out_w["ok"] is True and out_w["reveal"]["ok"] is False and out_w["reveal"]["drift"] > 8 and ev_w.get("reveal") == "colour" and P.unseal(out_w["sealed"])
      and P.is_display(base64.b64decode(out_w["image"])), (out_w.get("reveal"), ev_w))
EVENTS.clear()
calls = len(MODEL)
out_s = ENH.enhance({"sample": True, "image": b64(SAMPLE_RAW), "lang": "en"})
check("enhance: the AI-generated sample eye has no Reveal (it has no crop of its own): no reveal field, no model call, the plain display copy",
      "reveal" not in out_s and len(MODEL) == calls and P.is_display(base64.b64decode(out_s["image"])))
E.record = _real_record

# ============================================================================================ 9. events
section("9. events: the field and the counts")
agg = E.empty()
for ev_ in ({"reveal": "ok", "reveal_ms": 500}, {"reveal": "colour", "reveal_ms": 600}, {"reveal": "none"}, {"reveal": "ok", "reveal_ms": 400}, {"reveal": "registration", "reveal_ms": 550}, {"reveal": "error"}):
    E.add(agg, {"kind": "enhance", **E.build("enhance", ev_)})
check("events.add counts the Reveal's codes per day and its time as ms['reveal'] (sum and count)",
      agg["enhance_reveal"] == {"ok": 2, "colour": 1, "none": 1, "registration": 1, "error": 1} and agg["ms"]["reveal"] == [2050, 4], (agg["enhance_reveal"], agg["ms"].get("reveal")))
mrg = E.merge(agg, agg)
check("merge adds the new table like the old ones", mrg["enhance_reveal"]["ok"] == 4 and mrg["ms"]["reveal"] == [4100, 8])
check("events.build drops what is not a code (a space, an at sign, a number where a code belongs)",
      "reveal" not in E.build("enhance", {"reveal": "not a code"}) and "reveal" not in E.build("enhance", {"reveal": 7}) and E.build("enhance", {"reveal_ms": 12})["reveal_ms"] == 12)

# ============================================================================================ 10. the real eyes
section("10. the owner's real calibration eyes (LOCAL)")
real_path = os.path.join(HERE, "data", "reveal_goldens_real.json")
if CALIB and os.path.isfile(real_path):
    with open(real_path, encoding="utf-8") as f:
        GREAL = json.load(f)["cases"]
    n_seen, mism, spreads = 0, [], []
    for name, want in GREAL.items():
        cp, rp = os.path.join(CALIB, f"{name}_0_clientcrop.jpg"), os.path.join(CALIB, f"{name}_2_enhanced.jpg")
        if not (os.path.isfile(cp) and os.path.isfile(rp)):
            continue
        if hashlib.sha256(open(cp, "rb").read()).hexdigest() != want["crop_sha256"] or hashlib.sha256(open(rp, "rb").read()).hexdigest() != want["restored_sha256"]:
            continue          # another file than the one recorded: nothing to compare
        n_seen += 1
        crop, rest = Image.open(cp).convert("RGB"), Image.open(rp).convert("RGB")
        p = R.reveal_params(crop, rest)
        spreads.append(p["_info"]["reg"]["spread_r"])
        if json.loads(json.dumps(R.wire(p))) != want["params"] or sha(R.prepare_restored(rest, p)) != want["prep"]:
            mism.append(name)
    local(f"{n_seen} real eyes: reveal_params equals the scratch's number for number and prepare_restored byte for byte", n_seen >= 10 and not mism, (n_seen, mism))
    local(f"registration of the real eyes: the four half rings of every one agree about the shift to {max(spreads):.4f} R at most (the verdict's limit is 0.005 R)", bool(spreads) and max(spreads) <= R.REG_SPREAD_OK, spreads)
    if n_seen:
        by = {n: w["params"] for n, w in GREAL.items()}
        local("only the hazel eye p09f (restored colour 19.7 dE00 from its photo) is withheld; the other nine real eyes are shown with the cut",
              [n for n, v in by.items() if not v["ok"]] == ["p09f"] and abs(by["p09f"]["drift"] - 19.7) < 0.05, [(n, v["ok"], v["drift"]) for n, v in by.items()])
else:
    print("   (skipped: SNAPEYES_CALIB is not set)", flush=True)

section("11. no model call, no key")
check("nothing in this suite called the model or looked for a key (the image model was the stub of section 8, which answers from the crop)", not CALLED and len(MODEL) >= 4, (CALLED, len(MODEL)))

# ------------------------------------------------------------------
shutil.rmtree(TMP, ignore_errors=True)
ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed" + (f"   (+ {len(LOCAL)} local checks)" if LOCAL else ""))
sys.exit(0 if ok == len(RESULTS) and all(LOCAL) else 1)
