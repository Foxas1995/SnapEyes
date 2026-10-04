# -*- coding: utf-8 -*-
"""WP4 of the v3 engine work, the foundation every engine family is ported onto: api/_lib/styles/ core.py, layouts.py, text.py,
selfcheck.py, costs.py, the package's own lightness, and the synthetic iris generator the style suites use instead of real eyes.

  1. the package: importing _lib.styles imports no engine and no foundation module and is quick (IE2); a family that is not in the repository
     is EngineNotBuilt; every module starts with the __future__ import (Python 3.12 default, Eng review rule a) and parses as 3.12; no
     module level cache that can grow (a dict, list or set at module level), the baked tables aside (IE6's rule c)
  2. core.py is a verbatim port: the golden hashes of core_cases.run_cases were recorded on the SCRATCH prototype (the code the approved
     boards were made with; record_core_goldens.py) and are replayed here on the port: every primitive, the eye, its ring, class and grades, a
     placed disc, a small effect drawn with the primitives, the layouts, the customer's text; plus what the port changed (no studio words,
     no WORK_SIDE, max_side and eye_id) and BoundedCache
  3. text.py: limits, cleaning, the old "Anna;Max" string, the font check (every letter of the Lithuanian, Hungarian and German alphabets is
     drawn by the artwork font, a heart or a Chinese character is not), the drawers and their draw log
  4. the synthetic fixtures: deterministic, the three colour classes, three pupil shapes, clean eyes pass the calibrated gates and the lid and
     lash failures fail the lid rule (verdicts recorded on the scratch gates by record_synth_verdicts.py, the lid rule replayed here)
  5. selfcheck.py: T1 to T4, T6, T7, T12, with a negative case each, and the time at 4096 px
  6. costs.py: the planning spike's own numbers (step need, break-even factors, memory), a row for every style that has an engine, the
     environment overrides, the model's calibration against the spike's group figures
No network, no image model, no real eye. Run by suites/run_main.sh as v3core.
    python test_engine_core.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import time
import types

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
STYLES = os.path.join(API, "_lib", "styles")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
os.environ.update({"PYTHONIOENCODING": "utf-8", "SNAPEYES_TICKET_SECRET": "wp4-ticket-secret-for-tests-0123456789abcdef"})
sys.path.insert(0, API)
sys.path.insert(0, HERE)
import numpy as np  # noqa: E402
import PIL  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
import core_cases as CC  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
import _lib.styles as ST  # noqa: E402
from _lib.styles import core as C, layouts as LY, text as TX, selfcheck as SC, costs as CO  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
GOLD = json.load(open(os.path.join(HERE, "data", "core_goldens.json"), encoding="utf-8"))
VERDICTS = json.load(open(os.path.join(HERE, "data", "synth_verdicts.json"), encoding="utf-8"))["fixtures"]
MODULES = sorted(f for f in os.listdir(STYLES) if f.endswith(".py"))


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


# ============================================================================================ 1. the package
section("1. the package: light, lazy, rules of every module")
code = ("import sys, time; sys.path.insert(0, %r); t = time.perf_counter(); import _lib.styles as S; dt = (time.perf_counter() - t) * 1000; "
        "print(dt, sorted(m for m in sys.modules if m.startswith('_lib.styles.')), sorted(m for m in sys.modules if m in ('numpy', 'PIL', '_lib.iris')))" % API)
best = None
for _ in range(3):
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    m_ = re.match(r"(\S+) (\[.*?\]) (\[.*\])$", r.stdout.strip())
    ms, mods, heavy = m_.groups() if (r.returncode == 0 and m_) else ("999999", "?", "?")
    best = float(ms) if best is None else min(best, float(ms))
check("importing the package imports no module of it (no engine, no foundation), no numpy, no Pillow, no iris", mods == "[]" and heavy == "[]", (mods, heavy, r.stderr[-300:]))
check("... and takes at most 150 ms (best of three fresh interpreters; IE2)", best is not None and best <= 150.0, best)
built = [f for f in ST.ENGINE_FAMILIES if os.path.isdir(os.path.join(STYLES, f))]
unbuilt = [f for f in ST.ENGINE_FAMILIES if f not in built]
def raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    except Exception as e:  # noqa: BLE001
        return repr(e)
    return False
check("a family that is not in the repository is EngineNotBuilt, one that is imports; an unknown name is EngineNotBuilt",
      all(raises(lambda f=f: ST.family(f), ST.EngineNotBuilt) is True for f in unbuilt) and all(ST.family(f).__name__.endswith(f) for f in built)
      and raises(lambda: ST.family("legacy"), ST.EngineNotBuilt) is True, (built, unbuilt))
check("catalogue.engine_built agrees with the folders: a family is built exactly when api/_lib/styles/<family> exists",
      all(CT.engine_built(f) == (f in built) for f in ST.ENGINE_FAMILIES), (built, {f: CT.engine_built(f) for f in ST.ENGINE_FAMILIES}))
lab_unbuilt = next((s for s in CT.ids() if CT.ENGINE[s]["engine"] and CT.ENGINE[s]["engine"]["module"] in unbuilt), None)
if lab_unbuilt:
    n = CT.eyes_range(lab_unbuilt)[0]
    check("resolve, preview and tiles of a style whose family is not built are EngineNotBuilt (the second wall behind the catalogue)",
          all(raises(fn, ST.EngineNotBuilt) is True for fn in (lambda: ST.resolve({"style": lab_unbuilt, "eyes": n}, []),
                                                             lambda: ST.preview([], {"style": lab_unbuilt, "eyes": n}),
                                                             lambda: ST.tiles([], [lab_unbuilt], {"style": lab_unbuilt, "eyes": n}))), lab_unbuilt)
else:
    check("every engine family is built: the dispatch has no unbuilt family left to refuse", True)
check("a legacy style is refused by the style package (the legacy engine draws it)",
      raises(lambda: ST.resolve({"style": CT.legacy_ids()[0], "eyes": 1}, []), ST.EngineNotBuilt) is True)
check("every module of the package has the __future__ import (annotations) and parses as Python 3.12",
      all(re.search(r"^from __future__ import annotations\r?$", read(os.path.join(STYLES, m)), re.M) for m in MODULES)
      and all(ast.parse(read(os.path.join(STYLES, m)), feature_version=(3, 12)) for m in MODULES), MODULES)


def module_level_growers(path, allow=()):
    """Names assigned at module level to a dict, list or set (literal, comprehension or constructor): what could grow with the work done."""
    out = []
    for node in ast.parse(read(path)).body:
        targets = node.targets if isinstance(node, ast.Assign) else ([node.target] if isinstance(node, ast.AnnAssign) else [])
        v = getattr(node, "value", None)
        if v is None:
            continue
        bad = isinstance(v, (ast.Dict, ast.List, ast.Set, ast.DictComp, ast.ListComp, ast.SetComp)) or (
            isinstance(v, ast.Call) and getattr(v.func, "id", getattr(v.func, "attr", "")) in ("dict", "list", "set", "defaultdict", "OrderedDict", "deque"))
        if bad:
            out += [t.id for t in targets if isinstance(t, ast.Name) and t.id not in allow]
    return out
OWN = ["__init__.py", "core.py", "layouts.py", "text.py", "plates.py", "atlas.py", "costs.py", "selfcheck.py"]    # this package's; each later one adds its own checks
growers = {m: module_level_growers(os.path.join(STYLES, m), allow={"MASTER", "CAPPED", "PREVIEW", "ASPECTS", "N_RANGE", "DEFAULT_CAPTION", "_FAMILY_FN", "TEXT_KINDS"})
           for m in OWN}
check("no foundation module (core, layouts, text, plates, atlas, costs, selfcheck) keeps a module level dict, list or set that can grow (the baked cost "
      "table and the constant tables aside): caches are BoundedCache, so a warm instance cannot leak (rule c of the Eng review)", not any(growers.values()), {m: g for m, g in growers.items() if g})
src_all = "".join(read(os.path.join(STYLES, m)) for m in MODULES)
check("no module of the package holds a dash, a Windows or scratch path, a studio tagline or footer, or a secret name",
      not re.search(DASH, src_all) and not re.search(r"C:\\|wave-[a-z0-9]+|THE UNIVERSE WITHIN|PRECISE IRIS|GEMINI_API_KEY|SERVICE_KEY", src_all),
      re.findall(r"C:\\|wave-[a-z0-9]+|THE UNIVERSE WITHIN|PRECISE IRIS|GEMINI_API_KEY|SERVICE_KEY", src_all)[:5])
# A raw invisible or bidirectional character in source (a zero width space, a right to left override, a line separator, a byte order mark, a soft
# hyphen) cannot be read in review and can change what the line means (Trojan Source): the regex of text.clean names them by escape, never by glyph.
INVISIBLE = re.compile("[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f-\u009f\u00ad\u061c\u180e\u200b-\u200f\u2028-\u202e\u2060-\u206f\ufeff\ufff9-\ufffb]")
hid = [(m, [(i + 1, hex(ord(c))) for i, c in enumerate(read(os.path.join(STYLES, m))) if INVISIBLE.match(c)][:3]) for m in MODULES]
check("no module of the package holds a raw invisible, control or bidirectional character (text.clean writes its character class with escapes)",
      not any(h for _, h in hid), [x for x in hid if x[1]])

# ============================================================================================ 2. core: the golden replay
section("2. core, layouts, text: the golden hashes of the scratch prototype replayed on the port")
fixtures = {n: SI.png_bytes(n) for n in CC.IRIS_FIXTURES}
t0 = time.time()
cases = CC.run_cases(C, LY, TX.draw_names, fixtures)
print(f"   ({len(cases)} cases replayed in {time.time() - t0:.1f} s; recorded on {GOLD['machine']}; running on python "
      f"{sys.version.split()[0]}, numpy {np.__version__}, Pillow {PIL.__version__})", flush=True)
gold = GOLD["cases"]
machine_same = GOLD["machine"]["numpy"] == np.__version__ and GOLD["machine"]["pillow"] == PIL.__version__
check("the recorded cases and the replayed ones are the same cases", set(gold) == set(cases), sorted(set(gold) ^ set(cases))[:8])


def diff(prefix):
    return [k for k in sorted(gold) if k.startswith(prefix) and gold[k] != cases.get(k)]
note = "" if machine_same else f" (numpy/Pillow differ from the recording: {GOLD['machine']}: re-record on the scratch code, do not change the port)"
for label, prefix in [("the randomness: Rand streams, seed_for", "rand."), ("blur, box_reduce, upsample, Grid, polar, work_factor", ("blur", "box_reduce", "upsample", "grid.", "polar", "work_factor")),
                      ("tone map, dither, screen and add, fade, canvas and ground", ("tone_map", "dither", "screen_add", "fade_rows", "canvas", "radial_bg", "smoothstep")),
                      ("splat, sparkles, the three noises, the particle count", ("splat", "sparkles", "fbm", "value_noise", "particle_count")),
                      ("colour: stats and class, palettes, luts, ring_at, Lab and LCh, boost, mix, hue", ("colour", "effect_palette", "palette_lut", "angular_lut", "angle_index", "ring_at", "boost_mix", "lab_", "lch", "from_lch", "rgb01"))]:
    bad = [k for k in sorted(gold) if k.startswith(prefix) and gold[k] != cases.get(k)]
    n = len([k for k in gold if k.startswith(prefix)])
    check(f"core primitives equal the scratch ({n} cases): {label}", n > 0 and not bad, str(bad[:6]) + note)
for name in CC.IRIS_FIXTURES:
    bad = diff(name + ".")
    check(f"the eye {name}: ease, ring colours, class, grades at 256 and 640 px, a placed disc and a small effect drawn on it are equal to the scratch",
          not bad, str(bad) + note)
check("the seed of a design (design_seed over the four eyes) is equal to the scratch", gold["design_seed"] == cases["design_seed"] and not diff("seed_for"))
check(f"the layouts: all {gold['layouts.count']} cases of the five families (1 to 8 eyes, five canvases, three caption modes) give the scratch's slots and captions",
      not diff("layouts."), diff("layouts."))
check("the customer's text: names and date, names only, date only, a long line shrunk to fit, a landscape canvas: the pixels and the draw log equal the "
      "scratch drawer's", not diff("text."), diff("text."))
check("the four fixtures of the replay are the very bytes of the recording", all(__import__("hashlib").sha256(fixtures[n]).hexdigest() == GOLD["fixtures"][n] for n in fixtures),
      [n for n in fixtures if __import__("hashlib").sha256(fixtures[n]).hexdigest() != GOLD["fixtures"][n]])

import unittest.mock as mock  # noqa: E402
_erf0 = C._erf
with mock.patch.object(C, "_erf", lambda x: (_erf0(x) * np.float32(0.999)).astype(np.float32)), mock.patch.object(C, "SPLAT_CHUNK", 1 << 21):
    moved = CC.primitive_cases(C)
check("the replay can fail: a change of one thousandth in the error function of the splat moves the splat hash and not the unrelated ones",
      moved["splat"] != gold["splat"] and moved["rand.uniform"] == gold["rand.uniform"] and moved["blur.rgb.6.0"] == gold["blur.rgb.6.0"], (moved["splat"] == gold["splat"]))

section("2b. what the port changed, and nothing else")
check("core.py has no studio words and no orchestration: no TAGLINE, FOOTER, caption, watermark, render, Ctx, WORK_SIDE",
      not any(hasattr(C, n) for n in ("TAGLINE", "FOOTER", "caption", "watermark", "render", "Ctx", "WORK_SIDE", "REPO_API", "FONTS")), [n for n in ("TAGLINE", "FOOTER", "caption", "watermark", "render", "Ctx", "WORK_SIDE") if hasattr(C, n)])
core_tree = ast.parse(read(os.path.join(STYLES, "core.py")))
touches = []
for fn in ast.walk(core_tree):
    if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "open" and fn.name != "load_iris":
                touches.append((fn.name, "open"))
for n in ast.walk(core_tree):
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and (n.value.id, n.attr) in (("sys", "path"), ("os", "environ"), ("os", "path")):
        touches.append((n.value.id, n.attr))
    if isinstance(n, ast.Import) and any(a.name in ("os", "sys", "subprocess", "socket") for a in n.names):
        touches.append(("import", ast.dump(n)[:60]))
check("core.py imports no os, sys, subprocess or socket and opens a file only in load_iris (a path the caller names)", not touches, touches)
big = Image.new("RGB", (3000, 3000), (30, 40, 50))
bb = io.BytesIO()
big.save(bb, "PNG")
check("Iris(max_side): a 3000 px source is shrunk to 2048 by default, to the given cap otherwise, and never enlarged",
      C.Iris(bb.getvalue()).src.size == (2048, 2048) and C.Iris(bb.getvalue(), max_side=4096).src.size == (3000, 3000)
      and C.Iris(bb.getvalue(), max_side=512).src.size == (512, 512))
ir0 = C.Iris(fixtures["blue_round"], "x")
check("Iris.eye_id is the first 16 hex digits of the sha256 of its bytes unless a sealed id is passed in",
      ir0.eye_id == __import__("hashlib").sha256(fixtures["blue_round"]).hexdigest()[:16] and C.Iris(fixtures["blue_round"], eye_id="0123456789abcdef").eye_id == "0123456789abcdef")
bc = C.BoundedCache(2)
bc.put("a", 1)
bc.put("b", 2)
bc.get("a")
bc.put("c", 3)
check("BoundedCache: least recently used goes first, a read counts as use, the size is the bound, clear empties it",
      "b" not in bc and "a" in bc and "c" in bc and len(bc) == 2 and bc.get("zz", 7) == 7 and not (bc.clear() or len(bc)))
bc3 = C.BoundedCache(3)
for i in range(1000):
    bc3.put(i, bytes(10))
check("BoundedCache never holds more than its bound however much goes through it", len(bc3) == 3 and list(bc3._d) == [997, 998, 999])
import gc  # noqa: E402
import tracemalloc  # noqa: E402
tracemalloc.start()
grown = []
for k in range(12):
    ir_k = C.Iris(SI.png_bytes_of(kind=("blue", "green", "amber", "dark_brown", "grey")[k % 5], pupil=("round", "slit", "bar")[k % 3], seed=300 + k, side=384), f"leak{k}")
    d_k = C.place_disc(ir_k, 384.0, 384.0, 150.0, 0)
    CC.mini_render(C, ir_k, d_k)
    del ir_k, d_k
    gc.collect()
    grown.append(tracemalloc.get_traced_memory()[0])
tracemalloc.stop()
check("twelve different eyes through the core (grade, ring, disc, a small effect) in one process: the memory held after the third does not grow by more than 60 MiB "
      "(test IE6, the core's side: nothing keeps an eye alive)", (grown[-1] - grown[2]) / 1048576 < 60 and max(grown) / 1048576 < 200, [round(g / 1048576, 1) for g in grown])

# ============================================================================================ 3. text
section("3. the customer's words: limits, the font check, the drawers")
check("clean: NFC, control and zero width characters out, white space collapsed and trimmed; not a string is an empty string",
      TX.clean("  Anna\u200b   \tMax \n") == "Anna Max" and TX.clean("e\u0301") == "\u00e9" and TX.clean(None) == "" and TX.clean(5) == "")
check("split_names: a list, or the old wire string with semicolons or line breaks; empty names dropped; nothing cut",
      TX.split_names("Anna;Max") == ["Anna", "Max"] and TX.split_names(["Anna", " ", "Max "]) == ["Anna", "Max"] and TX.split_names("A\nB;;C") == ["A", "B", "C"]
      and TX.split_names(None) == [] and TX.split_names("x" * 300) == ["x" * 300])
check("normalise_names: the codes too_many, name_long, glyph, and None for a good set (eight names of 24 letters are 192 characters: the 200 total is a net "
      "under the other limits)",
      TX.normalise_names("Anna;Max", 2) == (["Anna", "Max"], None) and TX.normalise_names("A;B;C", 2)[1] == "too_many"
      and TX.normalise_names("x" * 25, 1)[1] == "name_long" and TX.normalise_names(["y" * 24] * 8 + ["z"], 8)[1] == "too_many"
      and TX.normalise_names(["y" * 24] * 8, 8) == (["y" * 24] * 8, None) and TX.normalise_names("Anna\u2764", 1)[1] == "glyph"
      and TX.normalise_names("", 1) == ([], None))
check("the limits are the plan's: 24 characters a name, 200 in all, a date of 20, a family name of 24, eight names", (TX.NAME_MAX, TX.NAMES_TOTAL_MAX, TX.DATE_MAX, TX.FAMILY_MAX, TX.NAMES_MAX) == (24, 200, 20, 24, 8))
check("lockup joins the names with a middle dot: Anna \u00b7 Max", TX.lockup(["Anna", "Max"]) == "Anna \u00b7 Max" and TX.lockup("Lina") == "Lina")
LT = "aąbcčdeęėfghiįyjklmnoprsštuųūvzž"
HU = "aábcdeéfghiíjklmnoóöőprstuúüűvzs"
DE = "abcdefghijklmnopqrstuvwxyzäöüß"
for name, alpha in (("Lithuanian", LT), ("Hungarian", HU), ("German", DE)):
    check(f"every letter of the {name} alphabet, in both cases, is drawn by the artwork font (no empty box in a delivered file)",
          TX.unsupported(alpha) == [] and TX.unsupported(alpha.upper()) == [], (TX.unsupported(alpha), TX.unsupported(alpha.upper())))
check("digits, the usual punctuation of a date or a name and the middle dot are drawn", TX.unsupported("12.05.2026 O'Neil-Smith & Anna, Max (2) \u00b7 No. 7") == [], TX.unsupported("12.05.2026 O'Neil-Smith & Anna, Max (2) \u00b7 No. 7"))
check("a heart, an emoji and a Chinese character are not drawn by the font and are named", set(TX.unsupported("Anna \u2764 \U0001F600 \u65e5")) == {"\u2764", "\U0001F600", "\u65e5"}, TX.unsupported("Anna \u2764 \U0001F600 \u65e5"))
check("the font's code point table is read from its cmap (Cinzel and Plus Jakarta Sans, both a few hundred letters), no dependency",
      300 < len(TX.font_cover("Cinzel.ttf")) < 600 and 600 < len(TX.font_cover("PlusJakartaSans.ttf")) < 2000 and ord("A") in TX.font_cover("Cinzel.ttf"), (len(TX.font_cover("Cinzel.ttf")), len(TX.font_cover("PlusJakartaSans.ttf"))))
fr = types.SimpleNamespace(W=1024, H=1024, S=1024, text_y=0.93 * 1024)
img = Image.new("RGB", (1024, 1024), (4, 4, 6))
log = TX.draw_names(img, fr, "Anna & Max", "2026", TX.NAME_WARM, [])
check("draw_names logs exactly what it drew: the names, then the date, with size and baseline; T7 accepts that log",
      [(e["kind"], e["text"]) for e in log] == [("names", "Anna & Max"), ("date", "2026")] and SC.t7_text(log, ["Anna & Max", "2026"])["ok"], log)
img2 = Image.new("RGB", (1024, 1024), (4, 4, 6))
check("with no names and no date nothing is drawn and the log is empty (the canvas is untouched)",
      TX.draw_names(img2, fr, "", "  ", TX.NAME_WARM, []) == [] and not np.asarray(img2).astype(int).__sub__(np.asarray(Image.new("RGB", (1024, 1024), (4, 4, 6)))).any())
img3 = Image.new("RGB", (1024, 1024), (4, 4, 6))
lg = TX.draw_line(img3, 512, 500, "Muller family", 1024, "family", log=[])
check("draw_line draws one centred line (the family name inside a ring) and logs it as kind family; an empty text draws nothing",
      lg[0]["kind"] == "family" and lg[0]["text"] == "Muller family" and np.asarray(img3).max() > 100 and TX.draw_line(img3, 512, 500, " ", 1024, log=[]) == [], lg)
words = TX.clean("A" * 40 + " " + "B" * 40)
img4 = Image.new("RGB", (1024, 1024), (4, 4, 6))
lg4 = TX.draw_names(img4, fr, words, "", TX.NAME_WARM, [])
arr4 = np.asarray(img4).max(-1)
cols = np.nonzero(arr4.max(0) > 60)[0]
check("a line that is too long is shrunk to 0.80 of the canvas width, never cut and never off the canvas", lg4[0]["px"] < TX._cap_font_px("Cinzel.ttf", "Regular", TX.CAP_H * 1024) and cols.min() >= 0.1 * 1024 - 2 and cols.max() <= 0.9 * 1024 + 2, (lg4, cols.min(), cols.max()))

# the drawers set a line character by character with a width measure of the whole prefix: quadratic, so the length of a line is bounded here too
longest = TX.lockup(["N" * TX.NAME_MAX] * TX.NAMES_MAX)
img5 = Image.new("RGB", (1024, 1024), (4, 4, 6))
t5 = time.time()
lg5 = TX.draw_names(img5, fr, longest, "12.05.2026", TX.NAME_WARM, [])
dt5 = time.time() - t5
check("the longest legal line (the lockup of eight names of 24 letters, 213 characters) is drawn, is under LINE_MAX, and takes seconds not minutes",
      len(longest) == 213 <= TX.LINE_MAX and [e["kind"] for e in lg5] == ["names", "date"] and dt5 < 10, (len(longest), dt5))
refused = []
for what, fn in (("names", lambda im: TX.draw_names(im, fr, "A" * (TX.LINE_MAX + 1), "", TX.NAME_WARM, [])),
                 ("date", lambda im: TX.draw_names(im, fr, "", "9" * (TX.LINE_MAX + 1), TX.NAME_WARM, [])),
                 ("line", lambda im: TX.draw_line(im, 512, 500, "B" * (TX.LINE_MAX + 1), 1024, log=[])),
                 ("names with a blank run", lambda im: TX.draw_names(im, fr, "A" * TX.LINE_MAX + " B", "", TX.NAME_WARM, []))):
    imx = Image.new("RGB", (1024, 1024), (4, 4, 6))
    t_ = time.time()
    try:
        fn(imx)
        refused.append((what, "drawn"))
    except TX.TextTooLong as e_:
        if not isinstance(e_, ValueError) or time.time() - t_ > 1.0 or np.asarray(imx).astype(int).__sub__(np.asarray(Image.new("RGB", (1024, 1024), (4, 4, 6)))).any():
            refused.append((what, "slow or touched the canvas"))
check("a line over LINE_MAX (256) characters is refused with TextTooLong (a ValueError) at once and before anything is drawn, whichever drawer or field; "
      "exactly LINE_MAX is drawn", not refused and TX.draw_names(Image.new("RGB", (256, 256)), types.SimpleNamespace(W=256, H=256, S=256, text_y=200.0), "A" * TX.LINE_MAX, "", TX.NAME_WARM, [])[0]["text"] == "A" * TX.LINE_MAX, refused)

# ============================================================================================ 4. the synthetic fixtures
section("4. the synthetic irises the style suites use: deterministic, three classes, three pupils, clean ones pass, failures fail")


def lid_gate(ir):
    """cx_kit.gate of the scratch prototype (the lid rule of collision, chain and family), 20 lines, run on the ported core."""
    info = {}
    C.ring_colours(ir, info=info)
    fr_ = ir.graded(C.REF_SIDE)
    sq, t = C._tight(fr_)
    R = t / 2.0
    ax = np.arange(t) + 0.5 - R
    rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / R
    th = np.degrees(np.arctan2(ax[:, None] + 0 * ax[None, :], ax[None, :] + 0 * ax[:, None])) % 360.0
    rgb = sq.astype(np.float32) / 255.0
    res = []
    for (r0, r1) in ((0.70, 0.88), (0.88, 0.98)):
        m = (rr > r0) & (rr < r1)
        Lv = C.lch(rgb[m])[0]
        b = (th[m]).astype(int) // 10
        cnt = np.maximum(np.bincount(b, minlength=36), 1)
        Lm = np.bincount(b, weights=Lv, minlength=36) / cnt
        dev = np.abs(Lm - np.median(Lm))
        res.append((float(dev.max()), int((dev > 16).sum())))
    ob = int(info.get("outlier_bins", 0))
    lid70, lid88, md = res[0][1], res[1][1], res[0][0]
    bad = lid70 >= 3 or lid88 >= 4 or ob >= 40 or (ob >= 20 and lid70 + lid88 >= 2) or (md >= 22.0 and lid70 >= 2)
    return dict(ok=not bad, lid70=lid70, lid88=lid88, outlier_bins=ob, maxdev70=round(md, 1))


raws = {n: SI.png_bytes(n) for n in SI.FIXTURES}
hs = lambda b: __import__("hashlib").sha256(b).hexdigest()
check("the generator makes the same bytes twice, and the 12 fixtures are the bytes of the recording", all(raws[n] == SI.png_bytes(n) for n in ("blue_round", "grey_lash")) and
      all(hs(raws[n]) == VERDICTS[n]["sha256"] for n in raws), [n for n in raws if hs(raws[n]) != VERDICTS[n]["sha256"]])
check("the set holds three colour classes (own, dark_brown, grey), three pupil shapes (round, slit, bar), eight clean eyes and four failures",
      {VERDICTS[n]["class"] for n in raws} == {"own", "dark_brown", "grey"} and {VERDICTS[n]["pupil"] for n in raws} == {"round", "slit", "bar"}
      and len(SI.CLEAN) == 8 and len(SI.FAILING) == 4, ({VERDICTS[n]["class"] for n in raws}, {VERDICTS[n]["pupil"] for n in raws}))
irs = {n: C.Iris(raws[n], n) for n in SI.FIXTURES}
check("the ported core reads each fixture's colour class as the scratch did (own, dark_brown, grey) and the stats are equal",
      all(irs[n].stats["class"] == VERDICTS[n]["class"] and irs[n].stats == VERDICTS[n]["stats"] for n in irs), {n: (irs[n].stats["class"], VERDICTS[n]["class"]) for n in irs if irs[n].stats["class"] != VERDICTS[n]["class"]})
replay = {n: lid_gate(irs[n]) for n in irs}
check("the lid rule replayed on the port gives the scratch gate's numbers for all 12 fixtures",
      all(replay[n]["ok"] == VERDICTS[n]["lid"]["ok"] and replay[n]["lid70"] == VERDICTS[n]["lid"]["lid70"] and replay[n]["lid88"] == VERDICTS[n]["lid"]["lid88"]
          and replay[n]["outlier_bins"] == VERDICTS[n]["lid"]["outlier_bins"] and abs(replay[n]["maxdev70"] - VERDICTS[n]["lid"]["maxdev70"]) < 0.051 for n in irs),
      {n: (replay[n], VERDICTS[n]["lid"]) for n in irs if replay[n]["ok"] != VERDICTS[n]["lid"]["ok"]})
from _lib.styles import eye as EYE  # noqa: E402  (work package 3: the eye profile and the gate of the repository)
profs = {n: EYE.profile_of_bytes(raws[n]) for n in irs}
check("the repository's own gate and profile (api/_lib/styles/eye.py, work package 3) say what the scratch gates said about all 12 fixtures: colour class, "
      "pupil class, the lid verdict and the fill verdict",
      all(profs[n].cls == VERDICTS[n]["class"] and profs[n].pupil_cls == VERDICTS[n]["pupil"] and profs[n].gate("lid")["ok"] is VERDICTS[n]["lid"]["ok"]
          and profs[n].gate("fill")["ok"] is VERDICTS[n]["fill"]["ok"] for n in irs),
      {n: (profs[n].cls, profs[n].pupil_cls, profs[n].gate("lid")["ok"], profs[n].gate("fill")["ok"]) for n in irs})
check("the two ports of the ring colours agree: core.ring_colours and eye.ring_colours give the same 360 colours on the graded 256 px frame of every fixture",
      all(np.array_equal(C.ring_colours(irs[n].graded(C.REF_SIDE)), EYE.ring_colours(irs[n].graded(C.REF_SIDE))) for n in ("blue_round", "dark_brown_bar", "grey_lid", "amber_slit")))
check("every clean fixture passes the lid rule (replayed) and the fill rule (recorded on the scratch gate)",
      all(replay[n]["ok"] and VERDICTS[n]["fill"]["ok"] for n in SI.CLEAN), [n for n in SI.CLEAN if not (replay[n]["ok"] and VERDICTS[n]["fill"]["ok"])])
check("every failing fixture (an eyelid wedge on blue, dark brown and grey, a fan of lashes on grey) fails the lid rule; the two on blue and grey also fail the fill rule",
      not any(replay[n]["ok"] for n in SI.FAILING) and not VERDICTS["blue_lid"]["fill"]["ok"] and not VERDICTS["grey_lid"]["fill"]["ok"], [n for n in SI.FAILING if replay[n]["ok"]])
check("the generator refuses an unknown colour or pupil; the jpeg of a fixture is the same picture the engine receives from the site",
      raises(lambda: SI.make(kind="purple"), ValueError) is True and raises(lambda: SI.make(pupil="square"), ValueError) is True
      and np.abs(np.asarray(Image.open(io.BytesIO(SI.jpeg_bytes("blue_round")))).astype(int) - np.asarray(Image.open(io.BytesIO(raws["blue_round"]))).astype(int)).mean() < 2.0)
sm = SI.make("amber", "round", side=256)
check("a fixture is a square disc on black at the site's own radius (the corners are black, the limbus is at 0.4464 of the side)",
      sm.size == (256, 256) and np.asarray(sm)[:6, :6].max() == 0 and np.asarray(sm)[128, 128 + int(0.4464 * 256) - 3].max() > 20 and np.asarray(sm)[128, 128 + int(0.4464 * 256) + 3].max() == 0)

# ============================================================================================ 5. selfcheck
section("5. selfcheck: T1 to T4, T6, T7, T12")
ir = irs["blue_round"]
dsc = C.place_disc(ir, 384.0, 384.0, 150.0, 0)
img8 = CC.mini_render(C, ir, dsc)
r1 = SC.t1_iris_integrity(img8, [dsc])
check("T1: a finished canvas (the iris pasted last) has zone A byte for byte the graded disc: largest difference 0 over every pixel of the zone",
      r1["ok"] and r1["max_abs_diff"] == 0 and r1["bad"] == 0 and r1["checked"] > 50000, r1)
bad8 = img8.copy()
cy, cx_ = int(dsc.cy), int(dsc.cx) + 60
bad8[cy, cx_] = (bad8[cy, cx_].astype(int) ^ 7).astype(np.uint8)
r1b = SC.t1_iris_integrity(bad8, [dsc])
check("T1 negative: one pixel of zone A changed by 7 is found (max difference 7, one bad pixel), and T6 counts it", not r1b["ok"] and r1b["max_abs_diff"] == 7 and r1b["bad"] == 1
      and SC.t6_matter_on_iris(bad8, [dsc]) == {"ok": False, "count": 1})
edge8 = img8.copy()
ex_, ey_ = int(dsc.cx + 0.985 * dsc.R), int(dsc.cy)
edge8[ey_, ex_] = (edge8[ey_, ex_].astype(int) ^ 7).astype(np.uint8)
check("T1 looks at zone A only: a change at 0.985 R (the rim's own soft zone) is not an iris failure", SC.t1_iris_integrity(edge8, [dsc])["ok"])
m = SC.zone_mask(dsc)
check("the zone A mask is the disc of 0.95 R about the exact centre (area within 0.2 percent of pi (0.95 R)^2)", abs(m.sum() / (np.pi * (0.95 * dsc.R) ** 2) - 1) < 0.002, m.sum())
half = np.zeros_like(m)
half[:, :m.shape[1] // 2] = True
rp = SC.iris_pixels(bad8, dsc, mask=m & half)
check("a published mask (an overlap style's M_k) limits the comparison to its pixels", rp["bad"] == 0 and rp["checked"] < m.sum() and SC.iris_pixels(bad8, dsc, mask=m & ~half)["bad"] == 1)
t4 = SC.t4_black_share(img8, 0.0, 1.0)
a32 = img8.astype(np.float32)
lum = a32[..., 0] * 0.299 + a32[..., 1] * 0.587 + a32[..., 2] * 0.114
check("T4: the black share is the share of luma under 12/255 (equal to the whole-array float32 formula), and the literal 3/255 is reported beside it",
      abs(t4["share"] - round(float((lum < 12).mean()), 4)) < 1e-9 and abs(t4["literal3"] - round(float((lum < 3).mean()), 4)) < 1e-9 and t4["literal3"] <= t4["share"], t4)
check("T4 ranges: inside passes, outside fails", SC.t4_black_share(img8, t4["share"] - 0.01, t4["share"] + 0.01)["ok"] and not SC.t4_black_share(img8, t4["share"] + 0.05, 1.0)["ok"])
pup = np.zeros((300, 300), bool)
yy, xx = np.mgrid[0:300, 0:300]
pup[(xx - 150) ** 2 + (yy - 150) ** 2 <= 40 ** 2] = True
vis = np.ones((300, 300), bool)
check("T2: a pupil with all its surroundings visible and no strip near it is clear", SC.t2_pupil_clearance([pup], [vis], None, [150.0])["ok"])
vis_hole = vis.copy()
vis_hole[150, 150 + 41] = False
strip = np.zeros((300, 300), bool)
strip[:, 150 + 42] = True
far = np.zeros((300, 300), bool)
far[:, 200] = True
check("T2 negative: a hidden pixel just outside the pupil (inside the 0.01 R margin) fails; so does a strip within the margin; a strip outside it passes",
      SC.t2_pupil_clearance([pup], [vis_hole], None, [150.0])["violations"] > 0 and SC.t2_pupil_clearance([pup], [vis], [strip], [150.0])["violations"] > 0
      and SC.t2_pupil_clearance([pup], [vis], [far], [150.0])["ok"])
disc_mask = np.zeros((300, 300), bool)
disc_mask[(xx - 150) ** 2 + (yy - 150) ** 2 <= 140 ** 2] = True
vis93 = disc_mask.copy()
vis93[:, 150 + 100:] = False
sh = SC.t3_visible_share([vis93], [disc_mask], 0.5)
check("T3: the visible share of an iris is visible pixels over disc pixels, against the style's floor (one number or one per iris)",
      sh["ok"] and 0.80 < sh["shares"][0] < 0.95 and not SC.t3_visible_share([vis93], [disc_mask], 0.95)["ok"] and SC.t3_visible_share([disc_mask], [disc_mask], [1.0])["shares"] == [1.0])
check("T7: the customer's own names and date pass; a style name, the studio's name or a slogan in the log fails, whatever its kind",
      SC.t7_text([{"kind": "names", "text": "Anna"}, {"kind": "date", "text": "2026"}], ["Anna", "2026"])["ok"] and SC.t7_text([], [])["ok"]
      and not SC.t7_text([{"kind": "names", "text": "SNAPEYES"}], ["Anna"])["ok"] and not SC.t7_text([{"kind": "title", "text": "Anna"}], ["Anna"])["ok"]
      and not SC.t7_text([{"kind": "names", "text": "Clean Iris"}], ["Anna"])["ok"])
check("T12: a heart glyph in a drawn string and a heart word in an id are named; an ordinary set is clean",
      SC.t12_no_hearts(["Anna \u2764"], ["solo.clean"])["glyphs"] == ["U+2764"] and SC.t12_no_hearts([], ["solo.heart_line"])["words"] == ["heart"]
      and SC.t12_no_hearts(["Anna", "Max"], ["solo.clean", "duo.kiss_collision"])["ok"])
rep = SC.run(img8, [dsc], text_log=log, customer=["Anna & Max", "2026"], ids=["solo.clean", "single"], black_range=(0.0, 1.0))
check("run(): one small JSON report with every check, ok overall, and the time it took", rep["ok"] and set(rep["checks"]) == {"t1", "t6", "t7", "t12", "t4"}
      and len(json.dumps(rep)) < 900 and isinstance(rep["ms"], int), rep)
rep_bad = SC.run(bad8, [dsc], text_log=[{"kind": "names", "text": "SNAPEYES"}], customer=[], ids=[])
check("run(): any failing check makes the report not ok and names which", not rep_bad["ok"] and not rep_bad["checks"]["t1"]["ok"] and not rep_bad["checks"]["t7"]["ok"] and rep_bad["checks"]["t12"]["ok"])
W_ = 4096
tgt = 3000
rg = np.random.default_rng(1)
big_disc = C.Disc()
big_disc.iris, big_disc.index, big_disc.Sd = None, 0, 3200
big_disc.g = rg.integers(0, 256, (tgt, tgt, 3), dtype=np.uint8)
big_disc.alpha = L.disk_alpha(tgt, tgt / 2.0, C.FEATHER).astype(np.float32)
big_disc.x0 = big_disc.y0 = 548
big_disc.cx = big_disc.cy = 548 + tgt / 2.0
big_disc.R = tgt / 2.0
canvas8 = np.zeros((W_, W_, 3), np.uint8)
C.paste_iris_last(canvas8, big_disc)
t0 = time.perf_counter()
repb = SC.run(canvas8, [big_disc], black_range=(0.0, 1.0))
dt = time.perf_counter() - t0
check(f"run() on a 4096 px canvas with a 3000 px iris takes {dt:.2f} s (the plan said about 0.3 s: bound 1.5 s here) and finds the iris intact",
      repb["ok"] and dt < 1.5 and repb["checks"]["t1"]["checked"] > 6_000_000, (dt, repb))
del canvas8, big_disc

# ============================================================================================ 6. costs
section("6. costs: the spike's numbers, a row for every engine style, the model")
SPEC_TABLE = {   # design, eyes: (need at 1.6, need at 2.0, break-even factor, uncapped peak MB): recomputed in the plan's section 10.3
    ("singles.powder", 1): (26.1, 31.2, 3.62), ("singles.splash", 1): (25.6, 30.6, 3.71), ("singles.radiance", 1): (21.2, 25.1, 4.77),
    ("singles.clean", 1): (16.4, 19.0, 6.90), ("collision.trio", 3): (32.3, 38.9, 2.80), ("collision.family", 8): (43.6, 52.5, 1.98),
    ("collision.family", 7): (41.1, 49.5, 2.12), ("universe.echo", 1): (25.6, 30.6, 3.71), ("universe.echo", 3): (43.7, 53.1, 1.95),
    ("universe.echo", 6): (46.3, 56.1, 1.83), ("universe.vortex", 1): (22.6, 26.8, 4.37), ("collision.infinity", 2): (20.4, 24.1, 5.08),
    ("collision.kiss", 2): (18.5, 21.7, 5.86), ("collision.family.universe", 8): (46.6, 56.3, 1.82)}
bad = []
for (k, n), (a16, a20, be) in SPEC_TABLE.items():
    got = (round(CO.step_need(k, n, factor=1.6), 1), round(CO.step_need(k, n, factor=2.0), 1), round(CO.break_even_factor(k, n), 2))
    if abs(got[0] - a16) > 0.06 or abs(got[1] - a20) > 0.06 or abs(got[2] - be) > 0.011:
        bad.append((k, n, got, (a16, a20, be)))
check(f"step_need at 1.6 and 2.0 and the break-even factor of the 52 s guard equal the plan's table 10.3 for {len(SPEC_TABLE)} designs", not bad, bad[:3])
check("every style with an engine has a row for every eye count and every look it takes (a style the table cannot price is not sold)",
      all(CO.known(CO.cost_key(CT.engine_for(s, n), look=lk if lk != CT.engine_for(s, n)["design"] else None), n)
          for s, e in CT.ENGINE.items() if e["engine"] and e["engine"]["module"] != "legacy"
          for n in range(CT.eyes_range(s)[0], CT.eyes_range(s)[1] + 1) for lk in (list(CT.engine_for(s, n)["looks"]) or [None])),
      "a style without a row")
check("the model: decode, encode, cold start, storage read and upload are in the formula (0.25 s a decoded eye, 0.17 s encode, 4.5, 0.31 a read, 0.8)",
      abs(CO.step_need("singles.clean", 1, factor=1.0) - ((6.3 + 0.25 + 0.17) + 4.5 + 0.31 + 0.8)) < 1e-9
      and abs(CO.step_need("collision.family", 8, factor=1.0) - ((20.2 + 0.25 * 8 + 0.17) + 4.5 + 0.31 * 8 + 0.8)) < 1e-9)
check("peak memory: the cold peak of the spike times the Linux allowance of 15 percent; the 2048 px copy of a pair, a family and the chain uses its own row",
      CO.est_mb("singles.powder", 1) == int(-(-729 * 1.15 // 1)) and CO.est_mb("collision.family", 8) == int(-(-1330 * 1.15 // 1))
      and CO.est_mb("collision.family", 8, side=2048) == int(-(-945 * 1.15 // 1)) and CO.est_mb("collision.infinity", 2, side=2048) < CO.est_mb("collision.infinity", 2))
check("a capped working copy is cheaper in time too (Family 8 on dark 16.8 s against 20.2), and a design without a capped row falls back to the uncapped figure",
      CO.cpu("collision.family", 8, 2048) == 16.8 and CO.cpu("collision.family", 8) == 20.2 and CO.cpu("singles.gold", 1, 2048) == CO.cpu("singles.gold", 1))
a = CO.assess("collision.family.universe", 8)
b = CO.assess("collision.family", 8, factor=2.1)
c_ = CO.assess("singles.clean", 1)
d_ = CO.assess("nothing.such", 1)
check("assess: a universe fill at eight eyes is refused for memory (2994 MB of a 1434 MB budget), a family at factor 2.1 for time (it can never finish), a clean "
      "iris is fine, an unknown design has no cost", a["why"] == "memory" and b["why"] == "time" and c_["ok"] and c_["why"] is None and d_["why"] == "no_cost" and not d_["ok"], (a, b, c_, d_))
check("the budgets: 1434 MB at the default 2048 MB function, a step over 40 s is cut into steps (WP6b), the work budget is 52 s",
      CO.MEM_BUDGET_MB == 1434 and CO.FUNCTION_MEM_MB == 2048 and CO.exceeds_step_budget(40.1) and not CO.exceeds_step_budget(40.0) and CO.WORK_BUDGET_S == 52.0)
check("the legacy engine has no row and a master smaller than 4096 px is refused rather than guessed",
      raises(lambda: CO.cost_key(CT.engine_for(CT.legacy_ids()[0], 1)), CO.NoCost) is True and raises(lambda: CO.step_need("singles.clean", 1, size=1024), CO.NoCost) is True
      and raises(lambda: CO.step_need("singles.clean", 2), CO.NoCost) is True)
sp = ["singles.powder", "singles.clean", "singles.gold", "singles.splash", "singles.radiance", "singles.elements"]
check("tiles_need: six single tiles on one eye preparation at 1024 px come to the spike's 4.9 s of a group call (within 5 percent); a preview of Powder on new eyes at 1.6 "
      "is the spike's 2.3 to 2.4 s; a second tile on the same eyes is cheaper than the first",
      abs(CO.tiles_need(sp, 1, size=1024, factor=1.0) / 4.9 - 1) < 0.05 and 2.25 <= CO.preview_need("singles.powder", 1, factor=1.6) <= 2.45
      and CO.preview_need("singles.powder", 1, factor=1.6, new_eyes=False) < CO.preview_need("singles.powder", 1, factor=1.6))
check("a 480 px tile costs less than a 1024 px one but never less than a fifth of the design time", CO.tiles_need(sp, 1, size=480, factor=1.6) < CO.tiles_need(sp, 1, size=1024, factor=1.6)
      and CO.tiles_need(sp, 1, size=480, factor=1.6) > 0.2 * CO.tiles_need(sp, 1, size=1024, factor=1.6))
code = ("import sys; sys.path.insert(0, %r); from _lib.styles import costs as K; print(round(K.step_need('singles.powder', 1), 2), K.MEM_BUDGET_MB, K.slow_factor())" % API)
env2 = dict(os.environ, STYLE_SLOW_CPU="2.0", STYLE_FUNCTION_MEM_MB="1024")
r2 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env2, timeout=120).stdout.split()
check("STYLE_SLOW_CPU and STYLE_FUNCTION_MEM_MB move the estimate and the memory budget (the factor from the probe, the memory from the project settings)",
      r2[:3] == ["31.25", "717", "2.0"], r2)
env3 = dict(os.environ, STYLE_SLOW_CPU="not a number", STYLE_FUNCTION_MEM_MB="12")
r3 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env3, timeout=120).stdout.split()
check("a bad setting falls back (factor 1.6) or is bounded (function memory at least 512 MB)", r3[0] == "26.12" and r3[1] == "358" and r3[2] == "1.6", r3)

fails = len([r for r in RESULTS if not r])
print(f"\n{len(RESULTS) - fails} of {len(RESULTS)} passed" + (f"; {fails} FAILED" if fails else ""))
sys.exit(1 if fails else 0)
