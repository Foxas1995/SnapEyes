# -*- coding: utf-8 -*-
"""DG6 step 2a (2026-10-13): the added detectors of the lid rule, prepared and OFF BY DEFAULT (api/_lib/styles/gate.py, the switch SNAPEYES_GATE2).
A restored eye whose lashes or skin the five arms of the lid rule let through is caught by three more measurements on the same 256 grade
(lid_colour_wedge, lid_lash_lines, lid_ring_structure; the module text of gate.py has the arithmetic). The owner has not approved any change of what passes,
so with the switch off every function, every record and every seal is what it was; this suite proves that, and what the detectors do when they are on.
No network, no image model, no real eye in the repository (the eyes are the procedural ones of synth_iris.py, plus a painted defect or a painted natural
feature on them); the measurements of the 161 looked-at real restorations are kept as numbers (section 5), not as pictures.
    section 1  off equals today: gate.lid against a verbatim copy of the function as it was, the reason codes, the stored form, the 12 synthetic profiles
               against the records saved from the code before this change
    section 2  the switch (iris.GATE2_ON, read once at import, BOM safe): 21 spellings, and a fresh interpreter with the variable set
    section 3  the detectors on painted synthetic eyes: clean eyes, subtle defects the five arms pass, natural features that must pass, a turned eye
    section 4  the gate with the switch on: reason codes, the sealed form, a profile round trip, a seal made on that is read off, events, severity
    section 5  the saved numbers of 161 looked-at restorations: the decision and the counts the calibration was made on
    section 6  the files
    python test_gate2.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
    SNAPEYES_CALIB             folder with <name>_2_enhanced.jpg (the 29 calibration restorations): LOCAL lines, not counted
Run by suites/run_main.sh as the entry v3gate2 (SNAPEYES_REPO names the checkout)."""
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import types

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
CALIB = os.environ.get("SNAPEYES_CALIB") or ""

RESULTS = []
LOCAL = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def local(name, ok, detail=""):
    """A line that needs the real calibration restorations: reported, not counted among the PASS lines (a failure still fails the run)."""
    LOCAL.append(bool(ok))
    print(("LOCAL ok   " if ok else "FAIL LOCAL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_CALIB"):
            os.environ.pop(k)
sys.path.insert(0, API)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402
from _lib.styles import gate as GATE  # noqa: E402
from _lib.styles import palette as PAL  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
INVISIBLE = "[" + "".join(chr(c) for a, b in ((0x200B, 0x2010), (0x2028, 0x202F), (0x2060, 0x2065), (0xFEFF, 0xFF00)) for c in range(a, b)) + "]"
NEW_CODES = ("lid_colour_wedge", "lid_lash_lines", "lid_ring_structure")


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


# ---- the lid rule as it was before this change (verbatim: api/_lib/styles/gate.py of origin/main 7e88348), the reference of "off equals today"
LID_ANNULI = ((0.70, 0.88), (0.88, 0.98))
LID_DEV = 16.0
LID70_MAX, LID88_MAX, OUTLIER_MAX = 3, 4, 40


def lid_ref(sq, outlier_bins):
    t = sq.shape[0]
    R = t / 2.0
    ax = np.arange(t) + 0.5 - R
    rr = np.sqrt(ax[None, :] ** 2 + ax[:, None] ** 2) / R
    th = np.degrees(np.arctan2(ax[:, None] + 0 * ax[None, :], ax[None, :] + 0 * ax[:, None])) % 360.0
    rgb = sq.astype(np.float32) / 255.0
    res = []
    for (r0, r1) in LID_ANNULI:
        m = (rr > r0) & (rr < r1)
        Lv = PAL.lch(rgb[m])[0]
        b = (th[m]).astype(int) // 10
        cnt = np.maximum(np.bincount(b, minlength=36), 1)
        Lm = np.bincount(b, weights=Lv, minlength=36) / cnt
        dev = np.abs(Lm - np.median(Lm))
        res.append((float(dev.max()), int((dev > LID_DEV).sum())))
    ob = int(outlier_bins)
    lid70, lid88, md = res[0][1], res[1][1], res[0][0]
    why = []
    if lid70 >= LID70_MAX:
        why.append("lid_sectors_inner")
    if lid88 >= LID88_MAX:
        why.append("lid_sectors_outer")
    if ob >= OUTLIER_MAX:
        why.append("lid_ring_outliers")
    if ob >= 20 and lid70 + lid88 >= 2 and ob < OUTLIER_MAX:
        why.append("lid_outliers_and_sectors")
    if md >= 22.0 and lid70 >= 2:
        why.append("lid_deviation")
    bad = lid70 >= 3 or lid88 >= 4 or ob >= 40 or (ob >= 20 and lid70 + lid88 >= 2) or (md >= 22.0 and lid70 >= 2)
    if bad != bool(why):
        raise AssertionError("gate lid: the reason codes disagree with the rule")
    return {"ok": not bad, "rule": "lid", "values": {"lid70": lid70, "lid88": lid88, "outlier_bins": ob, "maxdev70": round(md, 1)},
            "why": why, "raw": {"maxdev70": md}}


# ---- the profiles of the 12 synthetic fixtures made by the code BEFORE this change (stored forms of the two rules)
GOLDEN = json.loads('{"amber_slit":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":65,"outlier_bins":0},"why":[]}},"blue_lid":{"fill":{"ok":false,"values":{"catch_x1e4":0,"n_step":19,"run18":132},"why":["fill_rim_sector"]},"lid":{"ok":false,"values":{"lid70":0,"lid88":12,"maxdev70_x10":82,"outlier_bins":131},"why":["lid_sectors_outer","lid_ring_outliers"]}},"blue_round":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":98,"outlier_bins":0},"why":[]}},"blue_slit":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":46,"outlier_bins":0},"why":[]}},"dark_brown_bar":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":32,"outlier_bins":0},"why":[]}},"dark_brown_lid":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":30,"run18":0},"why":[]},"lid":{"ok":false,"values":{"lid70":14,"lid88":0,"maxdev70_x10":381,"outlier_bins":136},"why":["lid_sectors_inner","lid_ring_outliers","lid_deviation"]}},"dark_brown_round":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":42,"outlier_bins":0},"why":[]}},"green_bar":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":55,"outlier_bins":0},"why":[]}},"green_round":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":81,"outlier_bins":0},"why":[]}},"grey_lash":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":4},"why":[]},"lid":{"ok":false,"values":{"lid70":11,"lid88":3,"maxdev70_x10":278,"outlier_bins":48},"why":["lid_sectors_inner","lid_ring_outliers","lid_deviation"]}},"grey_lid":{"fill":{"ok":false,"values":{"catch_x1e4":0,"n_step":1,"run18":132},"why":["fill_rim_sector"]},"lid":{"ok":false,"values":{"lid70":0,"lid88":13,"maxdev70_x10":156,"outlier_bins":131},"why":["lid_sectors_outer","lid_ring_outliers"]}},"grey_round":{"fill":{"ok":true,"values":{"catch_x1e4":0,"n_step":0,"run18":0},"why":[]},"lid":{"ok":true,"values":{"lid70":0,"lid88":0,"maxdev70_x10":87,"outlier_bins":0},"why":[]}}}')

# ---- painted cases: a synthetic iris plus ONE painted feature (1024 px, the iris disc centred, as the engines receive it)
SIDE = 1024


def geom():
    R = SI.R_FRAC * SIDE
    ax = np.arange(SIDE) + 0.5 - SIDE / 2.0
    dx, dy = ax[None, :] + np.zeros((SIDE, 1)), ax[:, None] + np.zeros((1, SIDE))
    return np.hypot(dx, dy) / R, np.degrees(np.arctan2(dy, dx)) % 360.0, R


def blend(a, mask, colour, alpha):
    m = (mask * alpha)[..., None]
    return a * (1 - m) + np.asarray(colour, np.float64) * m


def paint(im, what):
    """The picture with one feature painted on it. Defects the five arms of the lid rule pass: lash_fan (18 thin dark curved lines over 55 degrees of the
    rim), pink_wedge and cyan_wedge (a tint over 100 and 90 degrees of the outer annulus, the fibres kept), lid_margin (a thin pale arc along the rim over
    90 degrees). Natural features that must pass: furrows (deep dark radial streaks all round), light_rim, dark_rim, hetero_centre (a recoloured inner
    zone) and concentric (the contraction furrows of the outer zone all round)."""
    a = np.asarray(im.convert("RGB"), np.float64)
    rr, th, R = geom()
    inside = rr < 1.0
    if what == "lash_fan":
        for k in range(18):
            ang = math.radians(243 + 3.2 * k)
            for s in np.linspace(0.78, 1.0, 120):
                curve = ang + 0.10 * (1.0 - s) * (1 if k % 2 else -1)
                xi, yi = int(SIDE / 2 + s * R * math.cos(curve)), int(SIDE / 2 + s * R * math.sin(curve))
                a[yi - 2:yi + 3, xi - 1:xi + 2] = (22, 18, 16)
    elif what == "pink_wedge":
        a = blend(a, ((th > 190) & (th < 290) & (rr > 0.66)) * inside, (176, 120, 118), 0.62)
    elif what == "cyan_wedge":
        a = blend(a, ((th > 20) & (th < 110) & (rr > 0.66)) * inside, (70, 170, 170), 0.6)
    elif what == "lid_margin":
        a = blend(a, ((th > 225) & (th < 315) & (rr > 0.90) & (rr < 0.955)) * inside, (222, 212, 206), 0.9)
    elif what == "furrows":
        a = blend(a, ((np.mod(th, 7.0) < 2.4) & (rr > 0.35)) * inside, (14, 10, 8), 0.55)
    elif what == "light_rim":
        a = blend(a, (rr > 0.90) * inside, (235, 225, 214), 0.35)
    elif what == "dark_rim":
        a = blend(a, (rr > 0.93) * inside, (12, 10, 10), 0.55)
    elif what == "hetero_centre":
        a = blend(a, (rr > 0.30) & (rr < 0.62), (196, 140, 60), 0.6)
    elif what == "concentric":
        a = blend(a, ((np.mod(rr * 40.0, 3.0) < 0.5) & (rr > 0.7)) * inside, (20, 14, 10), 0.35)
    else:
        raise ValueError(what)
    return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8))


def grade(im):
    """(sq, outlier_bins) of a picture as the profile measures it: the canonical 256 grade."""
    ei = EYE.EyeInput(im)
    fr = ei.graded(EYE.REF_SIDE)
    sq, _ = EYE.tight(fr)
    info = {}
    EYE.ring_colours(fr, info=info)
    return sq, info["outlier_bins"]


def jpeg(im):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=93)
    return buf.getvalue()


KINDS = ("blue", "green", "amber", "dark_brown", "grey")
BASE = {k: SI.make(k, "round", seed=31) for k in KINDS}
GRADED = {}            # (kind, what, turn) -> (sq, outlier_bins)


def graded(kind, what=None, turn=0):
    key = (kind, what, turn)
    if key not in GRADED:
        im = BASE[kind] if what is None else paint(BASE[kind], what)
        if turn:
            im = im.rotate(turn, resample=Image.BICUBIC, center=(SIDE / 2.0, SIDE / 2.0))
        GRADED[key] = grade(im)
    return GRADED[key]


# ============================================================================================ 1. off equals today
section("1. off equals today: the switch is off, and then nothing is different")
check("SNAPEYES_GATE2 is not set in this suite and the detectors are off (iris.GATE2_ON)", L.GATE2_ON is False and "SNAPEYES_GATE2" not in os.environ)
FIXED = {n: grade(SI.make_named(n)) for n in SI.FIXTURES}
real_extra = GATE.lid_extra


def _boom(*a, **k):
    raise AssertionError("lid_extra was called with the switch off")


GATE.lid_extra = _boom
try:
    same_fix = {n: GATE.lid(sq, ob) == lid_ref(sq, ob) for n, (sq, ob) in FIXED.items()}
    painted_off = {}
    for kind in ("blue", "grey", "amber"):
        for what in ("lash_fan", "pink_wedge", "lid_margin", "furrows", "light_rim"):
            sq, ob = graded(kind, what)
            painted_off[f"{kind}:{what}"] = GATE.lid(sq, ob) == lid_ref(sq, ob)
finally:
    GATE.lid_extra = real_extra
check("gate.lid with the switch off is, key for key and bit for bit, the function as it was, on the 12 synthetic fixtures (and lid_extra is never called)",
      all(same_fix.values()), [n for n, v in same_fix.items() if not v])
check("... and on 15 painted eyes (subtle defects and natural features, three colours)", all(painted_off.values()), [n for n, v in painted_off.items() if not v])
check("the off result has no trace of the detectors: raw holds maxdev70 only, the values are the four numbers, the reason codes are the five old ones",
      all(set(GATE.lid(sq, ob)["raw"]) == {"maxdev70"} and set(GATE.lid(sq, ob)["values"]) == {"lid70", "lid88", "outlier_bins", "maxdev70"}
          and all(c not in NEW_CODES for c in GATE.lid(sq, ob)["why"]) for sq, ob in FIXED.values()))
check("the reason code table keeps its five codes first (WHY[rule][0] is the same), the three new codes are appended; the fill codes, the rules and the value keys are untouched",
      GATE.WHY["lid"][:5] == ("lid_sectors_inner", "lid_sectors_outer", "lid_ring_outliers", "lid_outliers_and_sectors", "lid_deviation") and GATE.WHY["lid"][5:] == NEW_CODES
      and GATE.WHY["fill"] == ("fill_lid_margin", "fill_rim_sector", "fill_hard_edges", "fill_catchlight") and GATE.RULES == ("lid", "fill")
      and GATE.VALUE_KEYS == {"lid": ("lid70", "lid88", "outlier_bins", "maxdev70_x10"), "fill": ("run18", "n_step", "catch_x1e4")})
profiles = {n: EYE.profile_of_bytes(SI.png_bytes(n)) for n in SI.FIXTURES}
bad = {n: (p.rec["gate"]["lid"], GOLDEN[n]["lid"]) for n, p in profiles.items() if p.rec["gate"]["lid"] != GOLDEN[n]["lid"]}
check("the lid record of each of the 12 synthetic profiles, switch off, equals the record saved from the code before this change (ok, reason codes, whole numbers)", not bad, bad)
bad = {n: (p.rec["gate"]["fill"], GOLDEN[n]["fill"]) for n, p in profiles.items() if p.rec["gate"]["fill"] != GOLDEN[n]["fill"]}
check("... and the fill record, which this change does not touch", not bad, bad)
sf = GATE.store_form(GATE.lid(*FIXED["blue_lid"]))
check("store_form and valid_form read the old codes as before", GATE.valid_form("lid", sf) and sf["ok"] is False and all(c in GATE.WHY["lid"][:5] for c in sf["why"]), sf)
check("the profile of a synthetic eye is the same twice and after a switch on and off (no state is left behind)",
      (lambda a, b: a == b)(EYE.canonical_json(profiles["blue_round"].rec), EYE.canonical_json(EYE.profile_of_bytes(SI.png_bytes("blue_round")).rec)))

# ============================================================================================ 2. the switch
section("2. the switch SNAPEYES_GATE2 (read once at import, BOM safe)")
bom = chr(0xFEFF)
want = {None: False, "": False, " ": False, "off": False, "OFF": False, " off ": False, "0": False, "false": False, "False": False, "no": False, "NO": False,
        bom + "off": False, bom + "0": False, "on": True, "ON": True, "1": True, "yes": True, "true": True, bom + "on": True, " on ": True, "enabled": True}
iris_src = read("api/_lib/iris.py")
exprs = re.findall(r"^GATE2_ON = (.+)$", iris_src, re.M)
bad = {}
for val, exp in want.items():
    got = eval(exprs[0], {"os": types.SimpleNamespace(environ={} if val is None else {"SNAPEYES_GATE2": val})})    # the expression of iris.py itself, on a made environment
    if got is not exp:
        bad[repr(val)] = got
check("SNAPEYES_GATE2: unset, empty, blank, off, 0, false, no in any case, with spaces or a byte order mark are off; on, 1, yes, true (and any other word) are on (21 spellings of the expression in iris.py)",
      len(exprs) == 1 and not bad and len(want) == 21, (exprs, bad))
SWITCH_CODE = ("import sys\nsys.path.insert(0, %r)\nimport numpy as np\nfrom _lib import iris as L\nfrom _lib.styles import gate as G\n"
               "r = G.lid(np.full((241, 241, 3), 120, np.uint8), 0)\nprint(L.GATE2_ON, 'gate2' in r['raw'])\n" % API)
spawned = {}
for val in (None, "on", bom + "on", "off", bom + "off", "0"):
    env = {k: v for k, v in os.environ.items() if k != "SNAPEYES_GATE2"}
    if val is not None:
        env["SNAPEYES_GATE2"] = val
    r_ = subprocess.run([sys.executable, "-c", SWITCH_CODE], capture_output=True, text=True, timeout=180, env=env)
    spawned[repr(val)] = r_.stdout.strip() or r_.stderr[-200:]
check("in a fresh interpreter the variable decides: unset, off, 0 and a BOM before off leave the detectors off (iris.GATE2_ON False, gate.lid has no gate2 numbers), on and a BOM before on turn them on",
      spawned == {"None": "False False", "'on'": "True True", repr(bom + "on"): "True True", "'off'": "False False", repr(bom + "off"): "False False", "'0'": "False False"}, spawned)
srcs = {f: read(f"api/{f}") for f in ("enhance.py", "master_eye.py", "master_compose.py", "compose.py", "deglare.py", "analyze.py", "checkout.py", "order.py", "_lib/styles/eye.py", "_lib/styles/palette.py")}
gate_src = read("api/_lib/styles/gate.py")
check("the switch is read in one place only, api/_lib/iris.py (the style package reads no environment): no endpoint, master module or style module reads it, and gate.py only asks iris.GATE2_ON",
      all("SNAPEYES_GATE2" not in s for s in srcs.values()) and iris_src.count('os.environ.get("SNAPEYES_GATE2")') == 1 and re.search(r"\bos\.", gate_src) is None and "L.GATE2_ON" in gate_src, [k for k, s in srcs.items() if "SNAPEYES_GATE2" in s])
check("the detectors' three thresholds and windows are the numbers the module text states",
      (GATE.G2_WEDGE_MIN, GATE.G2_WEDGE_DE, GATE.G2_WEDGE_BAND, GATE.G2_WEDGE_RINGS, GATE.G2_WEDGE_SMOOTH) == (75, 12.0, (0.70, 0.88), 8, 5)
      and (GATE.G2_LINE_EXCESS, GATE.G2_LINE_DEPTH, GATE.G2_LINE_BAND, GATE.G2_LINE_REACH) == (0.22, 10.0, (0.84, 0.99), 3)
      and GATE.G2_EDGE_EXCESS == 21.0 and GATE.G2_WINDOW == 15)

# ============================================================================================ 3. the detectors on painted synthetic eyes
section("3. the detectors on painted synthetic eyes")


def extra(kind, what=None, turn=0):
    sq, ob = graded(kind, what, turn)
    return GATE.lid_extra(sq)


def old_ok(kind, what=None, turn=0):
    sq, ob = graded(kind, what, turn)
    return lid_ref(sq, ob)["ok"]


def fired(kind, what=None, turn=0):
    return set(extra(kind, what, turn)["why"])


clean = {n: GATE.lid_extra(FIXED[n][0]) for n in SI.CLEAN}
check("the 8 clean synthetic fixtures: no added code, and the numbers are far under the thresholds (wedge under 40 of 75 degrees, lines under 0.12 of 0.22, edges under 8 of 21)",
      all(not v["why"] and v["values"]["wedge_deg"] < 40 and v["values"]["line_excess"] < 0.12 and v["values"]["edge_excess"] < 8.0 for v in clean.values()), {n: v for n, v in clean.items() if v["why"]})
failing = {n: (lid_ref(*FIXED[n]), GATE.lid_extra(FIXED[n][0])) for n in SI.FAILING}
check("the 4 synthetic failing fixtures (a lid wedge, a lash fan) fail the old rule; the added detectors may add codes, never remove any", all(not r["ok"] for r, e in failing.values()))
check("the 5 clean colour classes of the painted base eye (seed 31): no added code", all(not fired(k) for k in KINDS), {k: fired(k) for k in KINDS})
lash = {k: (old_ok(k, "lash_fan"), fired(k, "lash_fan")) for k in ("blue", "green", "amber", "grey")}
check("a lash fan over 55 degrees of the rim (18 thin dark lines) on blue, green, amber and grey eyes passes the five old arms and fails lid_lash_lines",
      all(o and "lid_lash_lines" in f for o, f in lash.values()), lash)
pink = (old_ok("grey", "pink_wedge"), fired("grey", "pink_wedge"))
check("a pink tint over 100 degrees of a grey eye's rim passes the five old arms and fails lid_colour_wedge", pink[0] and "lid_colour_wedge" in pink[1], pink)
cyan = {k: fired(k, "cyan_wedge") for k in KINDS}
check("a cyan tint over 90 degrees fails lid_colour_wedge on all five colour classes (grey: the old arms pass it)", all("lid_colour_wedge" in f for f in cyan.values()) and old_ok("grey", "cyan_wedge"), cyan)
margin = {k: (old_ok(k, "lid_margin"), fired(k, "lid_margin")) for k in ("blue", "grey")}
check("a thin pale arc along the rim (a lid margin, 90 degrees) on a blue and on a grey eye passes the old arms and fails lid_ring_structure",
      all(o and "lid_ring_structure" in f for o, f in margin.values()), margin)
natural = {}
for what in ("furrows", "light_rim", "dark_rim", "hetero_centre", "concentric"):
    for kind in KINDS:
        natural[f"{kind}:{what}"] = (old_ok(kind, what), fired(kind, what))
check("natural features that run all round the eye or sit inside it (deep furrows, a lighter rim, a darker limbal ring, a recoloured inner zone, concentric furrows) on all five classes: 25 eyes, the old arms pass them and no added code fires",
      all(o and not f for o, f in natural.values()), {k: v for k, v in natural.items() if not (v[0] and not v[1])})
turned = {}
for what, kind in (("lash_fan", "blue"), ("pink_wedge", "grey"), ("furrows", "blue"), ("lash_fan", "grey")):
    for turn in (37, 211):
        turned[f"{kind}:{what}:{turn}"] = fired(kind, what, turn) == fired(kind, what)
check("the verdicts do not depend on where the defect sits: the same eyes turned by 37 and by 211 degrees give the same codes (a lash fan on two eyes, a pink wedge, furrows)", all(turned.values()), turned)
R_PX = SI.R_FRAC * SIDE
raw_edge = []
for turn in (0, 37, 90, 180, 211, 300):
    im = paint(BASE["grey"], "lid_margin")
    if turn:
        im = im.rotate(turn, resample=Image.BICUBIC, center=(SIDE / 2.0, SIDE / 2.0))
    box = tuple(int(round(SIDE / 2.0 + d * R_PX)) for d in (-1, -1, 1, 1))
    raw_edge.append(GATE.lid_extra(np.asarray(im.convert("RGB").crop(box).resize((241, 241), Image.LANCZOS)))["values"]["edge_excess"])
check("on the pictures themselves, before the studio grade, the ring structure of a pale arc is the same at 6 turns (within 5 percent; the grade's local contrast is what makes it stronger or weaker with the arc's position)",
      max(raw_edge) < 1.05 * min(raw_edge) and min(raw_edge) > 3 * GATE.G2_EDGE_EXCESS, raw_edge)
sq0, ob0 = graded("blue", "lash_fan")
t0 = time.perf_counter()
a1 = GATE.lid_extra(sq0)
dt = time.perf_counter() - t0
a2 = GATE.lid_extra(sq0.copy())
check("deterministic (the same numbers twice, bit for bit) and cheap (one call under 0.5 s; about 0.03 s on the development machine)", a1 == a2 and dt < 0.5, (a1, a2, dt))
check("the numbers are the documented ones: wedge_deg a whole number of degrees, 0 to 360; line_excess and edge_excess finite and not negative",
      all(isinstance(v["values"]["wedge_deg"], int) and 0 <= v["values"]["wedge_deg"] <= 360 and math.isfinite(v["values"]["line_excess"]) and v["values"]["line_excess"] >= 0
          and math.isfinite(v["values"]["edge_excess"]) and v["values"]["edge_excess"] >= 0 for v in list(clean.values()) + [a1]))

# ============================================================================================ 4. the gate with the switch on
section("4. the gate with the switch on: codes, sealed form, profile, seal, events")
L.GATE2_ON = True
try:
    on_fix = {n: GATE.lid(sq, ob) for n, (sq, ob) in FIXED.items()}
    r_lash = GATE.lid(*graded("blue", "lash_fan"))
    r_wedge = GATE.lid(*graded("grey", "pink_wedge"))
    r_edge = GATE.lid(*graded("blue", "lid_margin"))
    r_clean = GATE.lid(*graded("blue"))
    r_nat = [GATE.lid(*graded(k, "furrows")) for k in KINDS]
    r_off_ref = lid_ref(*graded("blue", "lash_fan"))
    on_painted_prof = EYE.EyeInput(jpeg(paint(BASE["blue"], "lash_fan"))).compute_profile(rules=("lid",))
    on_clean_prof = EYE.EyeInput(jpeg(BASE["blue"])).compute_profile(rules=("lid",))
finally:
    L.GATE2_ON = False
check("on: the 8 clean fixtures still pass and are the same result as off apart from the raw numbers of the detectors",
      all(on_fix[n]["ok"] is True and on_fix[n]["why"] == [] and on_fix[n]["values"] == lid_ref(*FIXED[n])["values"] for n in SI.CLEAN))
check("on: the 4 failing fixtures still fail with their old codes first (the added codes only follow)",
      all(on_fix[n]["ok"] is False and on_fix[n]["why"][:len(lid_ref(*FIXED[n])["why"])] == lid_ref(*FIXED[n])["why"] for n in SI.FAILING))
check("on: a lash fan the old arms pass now fails with exactly lid_lash_lines, and the four sealed values are the old numbers",
      r_lash["ok"] is False and r_lash["why"] == ["lid_lash_lines"] and r_lash["values"] == r_off_ref["values"] and r_off_ref["ok"] is True, r_lash)
check("on: a pink wedge on a grey eye fails with lid_colour_wedge and a pale lid margin on a blue eye with lid_ring_structure (the old arms pass both)",
      r_wedge["ok"] is False and "lid_colour_wedge" in r_wedge["why"] and r_edge["ok"] is False and "lid_ring_structure" in r_edge["why"], (r_wedge["why"], r_edge["why"]))
check("on: a clean eye and the five furrowed natural eyes pass, with the detectors' numbers in raw", r_clean["ok"] is True and all(r["ok"] is True and r["why"] == [] for r in r_nat)
      and set(r_clean["raw"]) == {"maxdev70", "gate2"} and set(r_clean["raw"]["gate2"]) == {"wedge_deg", "line_excess", "edge_excess"}, r_clean)
sf = GATE.store_form(r_lash)
check("the sealed form of a failure by an added code is valid, has the same keys as ever and no number of the detectors",
      GATE.valid_form("lid", sf) and set(sf) == {"ok", "why", "values"} and set(sf["values"]) == set(GATE.VALUE_KEYS["lid"]) and sf["why"] == ["lid_lash_lines"] and sf["ok"] is False, sf)
check("valid_form accepts each added code (and refuses an unknown one, and an ok record that carries one) whatever the switch says",
      all(GATE.valid_form("lid", {"ok": False, "why": [c], "values": sf["values"]}) for c in NEW_CODES) and not GATE.valid_form("lid", {"ok": False, "why": ["lid_nonsense"], "values": sf["values"]})
      and not GATE.valid_form("lid", {"ok": True, "why": ["lid_lash_lines"], "values": sf["values"]}) and not GATE.valid_form("fill", {"ok": False, "why": ["lid_lash_lines"], "values": {"run18": 0, "n_step": 0, "catch_x1e4": 0}}))
rec = on_painted_prof.rec
check("on: the profile of the painted eye carries the failure in its lid record; the profile validates and the clean eye's lid record is a pass",
      rec["gate"]["lid"]["ok"] is False and rec["gate"]["lid"]["why"] == ["lid_lash_lines"] and on_clean_prof.rec["gate"]["lid"]["ok"] is True, rec["gate"])
wire = on_painted_prof.to_wire()
back = EYE.EyeProfile.from_wire(wire)
check("a seal made with the switch on is read with it off: the wire round trip, the gate result, the public part and the set result keep the code",
      back.rec == rec and L.GATE2_ON is False and back.gate("lid")["ok"] is False and back.gate("lid")["why"] == ["lid_lash_lines"]
      and back.public()["gate"]["lid"] == {"ok": False, "why": ["lid_lash_lines"]} and GATE.set_result([on_clean_prof, back])["first"] == {"eye": 2, "why": "lid_lash_lines"}, back.public())
check("the same painted eye with the switch off passes (turning the switch on is the only thing that changes the verdict)",
      EYE.EyeInput(jpeg(paint(BASE["blue"], "lash_fan"))).compute_profile(rules=("lid",)).rec["gate"]["lid"]["ok"] is True)
sev = GATE.severity(back)
check("severity of an eye that fails only by an added code is the floor of a failing rule, 1.0 (the stored form has no number of the detectors to scale it), a passing eye 0.0",
      sev == 1.0 and GATE.severity(on_clean_prof) == 0.0, sev)
ev = E.build("enhance", {"gate": "lid", "reason": "lid_ring_structure", "cls": "grey", "pupil": "round", "profile_ms": 1234, "mode": "faithful"})
check("the events carry the added reason codes (the code pattern of events.py accepts them)", ev.get("reason") == "lid_ring_structure" and ev.get("gate") == "lid", ev)

# ============================================================================================ 5. the saved numbers of 161 looked-at restorations
section("5. the saved numbers of 161 looked-at real restorations (no picture): the decision and the counts of the calibration")
SAVED = """02.s1 N P g 27 0.1767 4.93
02.s2 N P g 38 0.1132 4.41
03.s1 N F o 52 0.2180 9.25
03.s2 N F o 33 0.2099 9.69
08.s1 N P o 66 0.1936 13.69
08.s2 N P o 29 0.1217 11.85
17.s1 N P d 2 0.1814 10.76
17.s2 N P d 0 0.0878 9.98
30.s1 N F d 69 0.1204 3.95
30.s2 N F d 73 0.1708 5.95
cm005.s1 N P o 44 0.1238 9.32
cm005.s2 N P o 58 0.0793 7.67
cm011.s1 N P d 13 0.0941 12.84
cm011.s2 N P d 8 0.1292 11.47
cm014.s1 N F d 58 0.1413 15.46
cm014.s2 N F o 65 0.2027 22.19
cs045.s1 N P o 36 0.1500 5.27
cs045.s2 N F o 34 0.1189 6.44
14.s1 N P o 26 0.1067 5.33
14.s2 N P o 10 0.0493 4.02
d01.s1 N P o 8 0.1323 8.82
d01.s2 N P o 5 0.1142 8.66
215208.s1 N P o 18 0.1121 8.21
cs003.s2 N P g 10 0.1725 7.59
11.s1 N P o 39 0.0927 6.62
215102.s2 N P o 25 0.1809 10.52
26.s1 N P o 60 0.1313 6.10
26.s2 N P o 61 0.0825 4.58
cm017.s1 N P o 51 0.1227 6.37
cs030.s1 N P o 58 0.1935 6.96
cs030.s2 N P o 57 0.1362 11.57
09.s2 C P o 51 0.1798 5.35
13.s1 C P d 55 0.0757 2.92
15.s2 C P o 8 0.0881 5.98
18.s1 C P o 0 0.0779 4.88
18.s2 C P o 4 0.1230 8.61
w04.s1 C P o 14 0.1794 11.36
w04.s2 C P o 6 0.1608 13.46
cm010.s1 C P d 4 0.0965 6.42
cm010.s2 C P d 2 0.0876 6.30
cm012.s1 C P g 0 0.1099 5.32
cm012.s2 C P g 0 0.1175 3.93
cm019.s1 C P o 23 0.1073 4.11
cm019.s2 C P o 35 0.1375 4.91
cm021.s1 C P o 27 0.0717 3.04
cm021.s2 C P o 47 0.1158 6.12
cm025.s1 C P g 39 0.1246 7.79
cm025.s2 C P g 43 0.1925 9.54
cm033.s1 C P o 0 0.0766 4.57
cm033.s2 C P o 1 0.0562 4.50
cm040.s1 C P o 38 0.1847 18.89
cm040.s2 C P o 20 0.1673 14.04
cs025.s1 C P o 10 0.1853 11.34
cs025.s2 C P o 8 0.2009 9.06
cs040.s1 C P o 50 0.0666 6.48
cs040.s2 C P o 43 0.1062 6.85
cs042.s1 C P o 16 0.0470 4.28
cs042.s2 C P o 42 0.0801 4.94
cs043.s1 C P o 13 0.1313 4.12
cs043.s2 C P o 19 0.0399 6.66
215120.s2 C P o 37 0.1947 8.95
22.s1 C P d 23 0.0098 5.62
28.s1 C P d 0 0.0653 3.86
07.s1 D1 P o 0 0.0585 5.70
07.s2 D1 P o 14 0.2109 34.15
09.s1 D1 F o 50 0.0649 12.82
11.s2 D2 F o 130 0.3963 20.33
15.s1 D2 F o 53 0.3317 22.27
20.s1 D2 P o 85 0.2280 20.66
29.s1 D2 P o 100 0.2665 25.07
29.s2 D2 P d 105 0.2659 26.34
cm013.s1 D2 F g 3 0.3927 22.30
cm013.s2 D2 F g 15 0.4079 28.05
cm030.s1 D2 F o 121 0.3091 10.47
cm030.s2 D2 F o 115 0.3007 9.31
cs024.s1 D2 F g 128 0.4149 40.47
cs037.s2 D2 P g 55 0.3390 10.64
cs044.s1 D2 F o 81 0.5078 69.62
cs044.s2 D2 P d 84 0.3502 37.70
cs085.s1 D2 P o 47 0.4032 67.71
cs099.s1 D2 F o 154 0.0512 4.07
cm022.s1 D2 F g 253 0.2137 36.42
cm022.s2 D2 F g 175 0.1894 46.25
13.s2 D1 P d 81 0.1345 13.32
16.s1 D2 P o 7 0.2211 21.46
16.s2 D1 P o 58 0.2682 27.66
20.s2 D2 F o 96 0.2357 9.03
215102.s1 D1 F o 119 0.1482 10.97
215120.s1 D1 P o 44 0.1324 7.00
215208.s2 D2 F o 74 0.1071 6.06
22.s2 D1 F d 74 0.0228 4.49
28.s2 D1 P d 2 0.0506 6.31
cm001.s1 D1 P o 14 0.0582 5.40
cm001.s2 D1 P o 24 0.0628 4.39
cm002.s1 D1 F o 80 0.1089 7.56
cm002.s2 D2 F o 151 0.1739 7.53
cm004.s1 D1 F o 45 0.1188 12.35
cm004.s2 D1 P o 64 0.1130 11.75
cm006.s1 D1 P o 9 0.1745 7.22
cm006.s2 D1 P o 25 0.1014 5.32
cm009.s1 D1 P g 45 0.1102 7.55
cm009.s2 D1 P g 6 0.0481 4.78
cm015.s1 D2 F o 65 0.1216 13.16
cm015.s2 D2 F o 61 0.1355 14.14
cm016.s1 D2 F o 206 0.1500 11.51
cm016.s2 D1 P o 86 0.0780 7.85
cm017.s2 D2 P g 0 0.0000 22.28
cm023.s1 D2 P o 124 0.1707 6.99
cm023.s2 D2 P o 124 0.2107 15.03
cm024.s1 D1 F o 64 0.1441 6.53
cm024.s2 D1 P o 10 0.1465 3.92
cs003.s1 D2 F g 52 0.1154 2.50
cs024.s2 D2 P g 182 0.1328 6.73
cs037.s1 D1 P g 16 0.0949 15.13
cs085.s2 D2 P o 51 0.1533 5.16
cs099.s2 D2 P o 124 0.1714 10.56
cs100.s1 D2 P g 12 0.1774 48.20
cs100.s2 D2 P g 6 0.2388 9.14
cs043.s1r D1 P o 45 0.0965 6.38
cs043.s2r D2 P o 69 0.0518 9.04
cal.amber14e C P o 46 0.0251 3.62
cal.drv_w04 C P o 6 0.1867 13.79
cal.drv_w09 C P o 66 0.1437 4.26
cal.lid06c C P o 47 0.0579 5.57
cal.lid19c C P d 1 0.0212 3.46
cal.lid19h C P d 5 0.0250 3.47
cal.p05i C P d 3 0.0799 6.53
cal.p08f C P o 0 0.0557 6.83
cal.p14j C P o 24 0.0579 3.53
cal.drv_d01 N P o 24 0.1174 14.57
cal.drv_w06 N P d 4 0.1345 7.13
cal.own215120 N P o 52 0.1764 6.07
cal.own215120h N P o 18 0.1602 5.96
cal.own215120j N P o 30 0.1735 11.20
cal.p09f N P o 27 0.1112 6.37
cal.p09g N P o 38 0.0594 12.50
cal.p09h N F o 43 0.1366 14.74
cal.p09i N P o 33 0.0734 11.56
cal.drv_d02 D2 F g 121 0.3529 50.16
cal.drv_d04 D2 F g 99 0.1443 8.67
cal.drv_d05 D2 F g 118 0.1034 12.49
cal.drv_w02 D2 F o 132 0.2937 46.88
cal.drv_w08 D2 F g 112 0.2178 13.56
cal.drv_w11 D2 F d 169 0.1358 6.58
cal.drv_w12 D2 F d 250 0.1901 30.64
cal.p11j D2 F o 211 0.5124 30.59
cal.drv_w03 D2 P o 12 0.1083 6.21
cal.drv_w10 D2 F o 69 0.0878 5.50
cal.lid19 D2 P d 4 0.0343 5.13
cal.lid19b D1 P d 0 0.0096 4.49
cal.own215120i D1 P o 46 0.1740 6.80
cal.p21e D2 P o 68 0.1136 7.01
cal.sample_cache D1 P o 52 0.1261 12.10
ms.cm004 C P o 23 0.1244 8.32
ms.cm010 C P d 1 0.0900 5.99
ms.cm012 C P g 0 0.1823 4.88
ms.cm040 C P o 11 0.1771 10.22
ms.cs025 C P o 0 0.1257 3.54
ms.d01 N P o 5 0.1046 12.42
ms.cm009 D1 P g 21 0.0955 6.27
ms.cm013 D2 P g 81 0.2952 50.34"""
rows = []
for line in SAVED.strip().splitlines():
    i, truth, old, cls, w, l, e = line.split()
    rows.append({"id": i, "truth": truth, "old_ok": old == "P", "cls": cls, "w": int(w), "l": float(l), "e": float(e)})
for r in rows:
    r["why"] = GATE.lid_extra_why(r["w"], r["l"], r["e"])
    r["new_ok"] = r["old_ok"] and not r["why"]
isD = lambda r: r["truth"] in ("D1", "D2")   # noqa: E731
check("the saved set is 161 restorations: 46 clean, 41 natural structure, 27 minor and 47 clear defects (the look of one reviewer, labels in the DG6 step 2a note)",
      (len(rows), sum(r["truth"] == "C" for r in rows), sum(r["truth"] == "N" for r in rows), sum(r["truth"] == "D1" for r in rows), sum(r["truth"] == "D2" for r in rows)) == (161, 46, 41, 27, 47))
tp_old, tp_new = sum(isD(r) and not r["old_ok"] for r in rows), sum(isD(r) and not r["new_ok"] for r in rows)
fp_old, fp_new = sum((not isD(r)) and not r["old_ok"] for r in rows), sum((not isD(r)) and not r["new_ok"] for r in rows)
check("the old rule alone fails 33 of the 74 defects and 8 of the 87 clean and natural eyes (recall 44.6 percent, precision 80.5 percent)", (tp_old, fp_old) == (33, 8), (tp_old, fp_old))
check("with the detectors the lid rule fails 52 of the 74 defects (42 of the 47 clear ones) and the same 8 of the 87 clean and natural eyes: no clean or natural eye newly rejected (recall 70.3 percent, precision 86.7 percent)",
      (tp_new, fp_new) == (52, 8) and sum(r["truth"] == "D2" and not r["new_ok"] for r in rows) == 42 and not [r["id"] for r in rows if (not isD(r)) and r["old_ok"] and not r["new_ok"]],
      (tp_new, fp_new))
check("of the 41 defects that pass today the detectors catch 19, of the 20 clear ones 15; the 5 clear ones they miss are cs085.s2, cs043.s2r, cal.drv_w03, cal.lid19 and cal.p21e",
      sum(isD(r) and r["old_ok"] and not r["new_ok"] for r in rows) == 19 and sum(r["truth"] == "D2" and r["old_ok"] and not r["new_ok"] for r in rows) == 15
      and sorted(r["id"] for r in rows if r["truth"] == "D2" and r["new_ok"]) == sorted(["cs085.s2", "cs043.s2r", "cal.drv_w03", "cal.lid19", "cal.p21e"]))
nat = [r for r in rows if r["truth"] in ("C", "N") and r["old_ok"]]
check("the 79 clean and natural eyes that pass today stay under all three thresholds: the largest wedge is 66 of 75 degrees, line excess 0.2009 of 0.22, edge excess 18.89 of 21",
      len(nat) == 79 and max(r["w"] for r in nat) == 66 and max(r["l"] for r in nat) == 0.2009 and max(r["e"] for r in nat) == 18.89 and not any(r["why"] for r in nat),
      (len(nat), max(r["w"] for r in nat), max(r["l"] for r in nat), max(r["e"] for r in nat)))
by_cls = {c: (sum(isD(r) and not r["old_ok"] for r in rows if r["cls"] == c), sum(isD(r) and not r["new_ok"] for r in rows if r["cls"] == c), sum(isD(r) for r in rows if r["cls"] == c)) for c in "odg"}
check("by colour class (defects failed today, with the detectors, of all): own 20, 30 of 45; dark brown 3, 6 of 9; grey 10, 16 of 20", by_cls == {"o": (20, 30, 45), "d": (3, 6, 9), "g": (10, 16, 20)}, by_cls)
near = sorted(r["id"] for r in rows if abs(r["w"] - GATE.G2_WEDGE_MIN) < 1 or abs(r["l"] - GATE.G2_LINE_EXCESS) < 0.003 or abs(r["e"] - GATE.G2_EDGE_EXCESS) < 0.3)
check("the decision of the saved rows does not hang on a rounding: only 03.s1 and cal.drv_w08 (the old rule fails both anyway) and the defect 16.s1 lie within 1 degree, 0.003 or 0.3 of a threshold, none of the 79 clean and natural eyes that pass today",
      near == ["03.s1", "16.s1", "cal.drv_w08"], near)
check("the saved rows name each reason code at least once (wedge, lines and ring structure all fire on real restorations)", all(any(c in r["why"] for r in rows) for c in NEW_CODES))

# ============================================================================================ 6. the files
section("6. the files")
changed = {rel: read(rel) for rel in ("api/_lib/styles/gate.py", "api/_lib/iris.py", "scripts/styles_tests/test_gate2.py", "suites/suites.list", "suites/baseline.json", "suites/baseline.md", "README.md")}
check("no dash (en or em) and no invisible or bidirectional character in the files this change touches",
      not any(re.search(DASH, s) for s in changed.values()) and not any(re.search(INVISIBLE, s) for s in changed.values()), [k for k, s in changed.items() if re.search(DASH, s)])
check("the module text of gate.py names the switch, the default and the three codes; the suite is in suites.list and in baseline.json",
      all(w in changed["api/_lib/styles/gate.py"] for w in ("SNAPEYES_GATE2", "OFF BY DEFAULT", "lid_colour_wedge", "lid_lash_lines", "lid_ring_structure"))
      and "v3gate2:scripts/styles_tests:test_gate2.py" in changed["suites/suites.list"] and '"v3gate2"' in changed["suites/baseline.json"])
check("gate.py imports what it imported before (math, numpy, the iris module and the palette: no os, the style package reads no environment); iris.py holds the switch",
      re.findall(r"^(?:import|from) .*$", changed["api/_lib/styles/gate.py"], re.M) == ["from __future__ import annotations", "import math", "import numpy as np", "from .. import iris as L", "from . import palette as PAL"]
      and "GATE2_ON" in read("api/_lib/iris.py"))

# ------------------------------------------------------------------ the real calibration restorations (LOCAL lines, only with SNAPEYES_CALIB)
if CALIB and os.path.isdir(CALIB):
    files = sorted(f for f in os.listdir(CALIB) if f.endswith("_2_enhanced.jpg"))
    got = {}
    for f in files:
        sq, ob = grade(Image.open(os.path.join(CALIB, f)))
        got[f[:-len("_2_enhanced.jpg")]] = (lid_ref(sq, ob)["ok"], GATE.lid_extra(sq)["why"])
    saved = {r["id"][len("cal."):]: r for r in rows if r["id"].startswith("cal.")}
    diff = {n: (got[n][1], saved[n]["why"]) for n in got if n in saved and sorted(got[n][1]) != sorted(saved[n]["why"])}
    local(f"the calibration restorations in {CALIB} ({len(got)} files): the detectors say what the saved numbers say", not diff, diff)
else:
    print("\n(no SNAPEYES_CALIB: the real calibration restorations are not read)")

ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed" + (f"   (+ {len(LOCAL)} LOCAL lines)" if LOCAL else ""))
sys.exit(0 if ok == len(RESULTS) and all(LOCAL) else 1)
