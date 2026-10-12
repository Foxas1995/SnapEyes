# -*- coding: utf-8 -*-
"""The conditional second restoration of /api/enhance (2026-10-12): when the first restoration fails the lid rule of the gate and the invocation has
the time, the model is asked once more and the better of the two restorations is kept (api/enhance.py, api/_lib/styles/gate.py severity, the events).
No network and no image model (the model is a stub that answers from a script), no real eye (the irises are the synthetic ones of synth_iris.py):
    section 1  gate.severity: the arithmetic on hand-made records, and on the 12 synthetic irises (0.0 exactly when every rule passes)
    section 2  the decision, with the second restoration scripted: which one is kept, the margin, the rule a pass may not lose, the time guard,
               a second call that fails or cannot be measured
    section 3  /api/enhance end to end with the real gate: a failing first and a passing second (kept), both failing (the better kept), a passing
               first (one call, the same bytes as before), the switch off, too little time, the reply field, the event line
    section 4  the switch SNAPEYES_RETRY2 (read once at import, BOM safe) and the files
    python test_retry2.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as the entry v3retry2 (SNAPEYES_REPO names the checkout)."""
import atexit
import base64
import copy
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
TMP = os.path.join(HERE, "retry2_tmp")
SP = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP, "wave-pv", "tests") if SP else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
if os.path.isdir(TMP):
    shutil.rmtree(TMP, ignore_errors=True)
os.makedirs(TMP)
atexit.register(shutil.rmtree, TMP, ignore_errors=True)   # its own folder only: gone at exit, green, red or crashed
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(os.path.join(TMP, "store_retry2"), stub.server_address[1])          # the payments harness' synthetic keys and ticket secret, a local store folder
sys.path.insert(0, API)
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402
from _lib.styles import gate as GATE  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
INVISIBLE = "[" + "".join(chr(c) for a, b in ((0x200B, 0x2010), (0x2028, 0x202F), (0x2060, 0x2065), (0xFEFF, 0xFF00)) for c in range(a, b)) + "]"   # zero width, direction and line separator characters, the byte order mark
CALLED = []                           # any call that would reach a model or read a key: this suite makes none (the image model is the script below)


def _no_model(*args, **kwargs):
    CALLED.append("gemini")
    raise AssertionError("a model call: this suite makes none")


def _no_key():
    CALLED.append("key")
    raise AssertionError("a key lookup: this suite reads none")


L.gemini, L._key = _no_model, _no_key


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def b64(im, fmt="PNG"):
    buf = io.BytesIO()
    im.save(buf, fmt)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def jpeg(im):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=93)
    return buf.getvalue()


# ============================================================================================ 1. gate.severity
section("1. gate.severity: how far past the gate an eye is")
BASE_REC = EYE.profile_of_bytes(jpeg(SI.make("blue", seed=5)), pad=1.12).rec


def form(rule, ok, **v):
    """A stored gate result of a rule: ok, one valid reason code when it fails, the stored values (zero unless given)."""
    keys = GATE.VALUE_KEYS[rule]
    return {"ok": ok, "why": [] if ok else [GATE.WHY[rule][0]], "values": {k: int(v.get(k, 0)) for k in keys}}


def crafted(lid=None, fill=None, drop=()):
    """The profile of the blue iris with its gate results replaced (a hand-made record that validates)."""
    rec = copy.deepcopy(BASE_REC)
    rec["gate"] = {"lid": form("lid", True), "fill": form("fill", True)}
    if lid is not None:
        rec["gate"]["lid"] = form("lid", False, **lid)
    if fill is not None:
        rec["gate"]["fill"] = form("fill", False, **fill)
    for r in drop:
        rec["gate"].pop(r)
    return EYE.EyeProfile(rec)


cases = [
    ("every rule passes", crafted(), 0.0),
    ("a rule not carried costs nothing", crafted(drop=("fill",)), 0.0),
    ("lid70 on the line (3 of 3)", crafted(lid={"lid70": 3}), 1.0),
    ("lid70 6 is twice the line", crafted(lid={"lid70": 6}), 2.0),
    ("lid88 8 is twice the line of 4", crafted(lid={"lid88": 8}), 2.0),
    ("80 outlier bins are twice the 40", crafted(lid={"outlier_bins": 80}), 2.0),
    ("20 outlier bins with 2 flagged sectors: the pair arm sits on the line, the bins alone are at 0.5", crafted(lid={"outlier_bins": 20, "lid70": 1, "lid88": 1}), 1.0),
    ("30 outlier bins with 2 sectors: the pair arm is the smaller of 1.5 and 1.0", crafted(lid={"outlier_bins": 30, "lid70": 1, "lid88": 1}), 1.0),
    ("maxdev 44 with 2 inner sectors: the pair arm is the smaller of 2.0 and 1.0", crafted(lid={"maxdev70_x10": 440, "lid70": 2}), 1.0),
    ("a failing rule costs at least 1.0 even when its stored numbers read under the line", crafted(lid={"maxdev70_x10": 219, "lid70": 2}), 1.0),
    ("fill run18 120 is twice the 60", crafted(fill={"run18": 120}), 2.0),
    ("fill n_step 240 is twice the 120", crafted(fill={"n_step": 240}), 2.0),
    ("fill catch 0.04 is twice the 0.02", crafted(fill={"catch_x1e4": 400}), 2.0),
    ("fill run18 24 with n_step 110: the pair arm is 2.0 (the others 0.4 and 0.92)", crafted(fill={"run18": 24, "n_step": 110}), 2.0),
    ("both rules fail: the two costs add", crafted(lid={"lid70": 6}, fill={"run18": 120}), 4.0),
]
for name, prof, want in cases:
    got = GATE.severity(prof)
    check(f"severity: {name} = {want}", abs(got - want) < 1e-9, got)

FIXTURE_SEV = {}
for name, spec in SI.FIXTURES.items():
    p = EYE.profile_of_bytes(jpeg(SI.make(**spec)), pad=1.12)
    FIXTURE_SEV[name] = (GATE.severity(p), [p.gate(r)["ok"] for r in GATE.RULES])
check("severity of the 8 clean synthetic irises is exactly 0.0 and they pass both rules",
      all(FIXTURE_SEV[n][0] == 0.0 and all(FIXTURE_SEV[n][1]) for n in SI.CLEAN), {n: FIXTURE_SEV[n] for n in SI.CLEAN})
check("severity of the 4 failing synthetic irises is at least 1.0 and they fail the lid rule",
      all(FIXTURE_SEV[n][0] >= 1.0 and FIXTURE_SEV[n][1][0] is False for n in SI.FAILING), {n: FIXTURE_SEV[n] for n in SI.FAILING})
check("severity is 0.0 exactly when no rule fails, on all 12 (it is a number about the gate's own verdict, never a second opinion)",
      all((FIXTURE_SEV[n][0] == 0.0) == all(FIXTURE_SEV[n][1]) for n in SI.FIXTURES))

# ============================================================================================ 2. the decision
section("2. the decision: which restoration is kept (the second restoration is scripted)")
spec = importlib.util.spec_from_file_location("enhance", os.path.join(API, "enhance.py"))
ENH = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ENH)
BLUE = SI.make("blue", seed=5)
IM = Image.new("RGB", (8, 8))
DRAWS = []


def draw_of(prof, ms=7):
    return ENH.Draw(IM, b"clean", prof, ms, 0.99, False, {"ok": True})


def decide(first_prof, second, left=40.0):
    """_retry with the second draw scripted: second is a Draw, None (an unmeasured one) or an exception to raise. (the Draw kept, the note, the draws made)"""
    DRAWS.clear()
    first = draw_of(first_prof)

    def fake_draw(*a):
        DRAWS.append(a)
        if isinstance(second, Exception):
            raise second
        return second

    real_draw, real_left = ENH._draw, L.time_left
    ENH._draw, L.time_left = fake_draw, (lambda default=L.BUDGET: left)
    try:
        kept, note = ENH._retry(first, "artistic", IM, IM, 0.4464, 1.12)
    finally:
        ENH._draw, L.time_left = real_draw, real_left
    return kept is first, kept, note, len(DRAWS)


LID2 = crafted(lid={"lid70": 6})                                # severity 2.0, fails lid
first_kept, _, note, n = decide(LID2, draw_of(crafted()))
check("a failing first and a passing second: the second is kept (code kept2, severities 2.0 and 0.0)",
      not first_kept and note["code"] == "kept2" and note["sev1"] == 2.0 and note["sev2"] == 0.0 and note["gate1"] == "lid" and n == 1, note)
first_kept, _, note, n = decide(LID2, draw_of(crafted(lid={"lid70": 4})))
check("both fail and the second is clearly less severe (1.333 against 2.0, at most 0.8 of it): the second is kept", not first_kept and note["code"] == "kept2", note)
first_kept, _, note, n = decide(LID2, draw_of(crafted(lid={"lid70": 5})))
check("both fail and the second is lower but not clearly (1.667 against 2.0, over 0.8 of it): the first stays", first_kept and note["code"] == "kept1" and note["sev2"] == 1.667, note)
first_kept, _, note, n = decide(LID2, draw_of(crafted(lid={"lid70": 9})))
check("both fail and the second is worse: the first stays", first_kept and note["code"] == "kept1", note)
first_kept, _, note, n = decide(LID2, draw_of(crafted(lid={"lid70": 6})))
check("both fail and they are equal: the first stays (otherwise the first)", first_kept and note["code"] == "kept1", note)
first_kept, _, note, n = decide(LID2, draw_of(crafted(fill={"run18": 70})))
check("the second passes the lid rule but fails the fill rule the first passed (1.167 against 2.0): the first stays, a rule that passed is never lost",
      first_kept and note["code"] == "kept1" and note["sev2"] == 1.167, note)
first_kept, _, note, n = decide(crafted(lid={"lid70": 6}, fill={"run18": 120}), draw_of(crafted(fill={"run18": 90})))
check("the first fails both rules (4.0), the second only the fill rule (1.5): the second is kept (it fails nothing the first passed)", not first_kept and note["code"] == "kept2" and note["gate1"] == "both", note)
first_kept, _, note, n = decide(LID2, L.ModelBusy("busy"))
check("the second call fails (the model is busy): the first is kept, code error, nothing is raised", first_kept and note["code"] == "error" and n == 1 and "sev2" not in note, note)
first_kept, _, note, n = decide(LID2, RuntimeError("image model returned no image"))
check("the second call returns no image: the first is kept, code error", first_kept and note["code"] == "error", note)
first_kept, _, note, n = decide(LID2, draw_of(None))
check("the second restoration cannot be measured (no profile): it cannot be judged, the first is kept, code error", first_kept and note["code"] == "error" and n == 1, note)
first_kept, _, note, n = decide(LID2, draw_of(crafted()), left=ENH.RETRY_MIN_LEFT - 0.1)
check("less than RETRY_MIN_LEFT seconds left: no second call, code time", first_kept and note["code"] == "time" and n == 0 and note["sev1"] == 2.0, (note, n))
first_kept, _, note, n = decide(LID2, draw_of(crafted()), left=ENH.RETRY_MIN_LEFT)
check("exactly RETRY_MIN_LEFT seconds left: the second call is made", not first_kept and note["code"] == "kept2" and n == 1, (note, n))
check("RETRY_MIN_LEFT leaves room: more than the profile's and the Reveal's guards together, less than the 52 s budget minus a slow first draw (p90 of an enhance 17 s)",
      EYE.PROFILE_MIN_LEFT + 4.0 < ENH.RETRY_MIN_LEFT <= L.BUDGET - 17.0, (ENH.RETRY_MIN_LEFT, L.BUDGET))
check("the trigger is the lid rule by default (RETRY_RULES) and the margin is a share of the first severity", ENH.RETRY_RULES == ("lid",) and 0.0 < ENH.RETRY_CLEAR < 1.0, (ENH.RETRY_RULES, ENH.RETRY_CLEAR))

# ============================================================================================ 3. /api/enhance end to end
section("3. /api/enhance with the real gate (the image model is a script)")
SCRIPT, MODEL, REQUESTS, LAST_REQUESTS = [], [], [], []


def scripted_model(prompt, im, size=None, thinking=None, model=None):
    REQUESTS.append((prompt, hash(im.tobytes()), size, thinking, model))
    MODEL.append(1)
    item = SCRIPT[min(len(MODEL) - 1, len(SCRIPT) - 1)]
    if isinstance(item, Exception):
        raise item
    return item.copy()


L.gemini_image = scripted_model
EVENTS = []
_real_record = E.record


def spy_record(kind, **fields):
    EVENTS.append((kind, dict(fields)))
    return False


E.record = spy_record
CLEAN_A, LID_A, LASH_A = SI.make("blue", seed=5), SI.make("blue", seed=5, lid=True), SI.make("blue", seed=5, lash=True)


def run(*script, crop=BLUE, mode="artistic", on=True, left=None, **kw):
    """One /api/enhance call with the model answering from the script: (reply, the enhance event, model calls)."""
    SCRIPT[:] = list(script)
    MODEL.clear()
    REQUESTS.clear()
    EVENTS.clear()
    real_on, real_left = ENH.RETRY_ON, L.time_left
    ENH.RETRY_ON = on
    if left is not None:
        L.time_left = lambda default=L.BUDGET: left
    try:
        out = ENH.enhance({"crop": b64(crop), "mode": mode, "pad": 1.12, "ticket": L.mint_ticket("work"), "lang": "en", **kw})
    finally:
        ENH.RETRY_ON, L.time_left = real_on, real_left
    LAST_REQUESTS[:] = REQUESTS
    return out, [e for e in EVENTS if e[0] == "enhance"][-1][1], len(MODEL)


def clean_of(out):
    return P.unseal_full(out["sealed"])[0]


def gates(out):
    return {r: out["profile"]["gate"][r]["ok"] for r in GATE.RULES}


# a passing first restoration
pass_out, pass_ev, pass_calls = run(CLEAN_A, LID_A)
check("a passing first restoration: one model call, no retry field in the reply, none in the event", pass_calls == 1 and "retry" not in pass_out
      and not any(k in pass_ev for k in ("retry", "gate1", "sev1", "sev2", "retry_ms")), (pass_calls, list(pass_out), pass_ev))
check("a passing first restoration: both rules pass in the sealed profile", gates(pass_out) == {"lid": True, "fill": True}, gates(pass_out))
pass_off, pass_off_ev, pass_off_calls = run(CLEAN_A, LID_A, on=False)
check("a passing eye comes back byte for byte as with the switch off: the sealed clean JPEG, the display copy, the profile, the Reveal, the colour QA, the event",
      clean_of(pass_out) == clean_of(pass_off) and pass_out["image"] == pass_off["image"] and pass_out["profile"] == pass_off["profile"]
      and pass_out["reveal"] == pass_off["reveal"] and pass_out["qa"] == pass_off["qa"] and pass_out["fidelity"] == pass_off["fidelity"]
      and set(pass_out) == set(pass_off) and {k: v for k, v in pass_ev.items() if k not in ("profile_ms", "reveal_ms")} == {k: v for k, v in pass_off_ev.items() if k not in ("profile_ms", "reveal_ms")}
      and pass_off_calls == 1, (set(pass_out) ^ set(pass_off), pass_ev, pass_off_ev))
many = {}
for name in ("blue_round", "grey_round", "dark_brown_round", "green_bar"):
    fx = SI.make(**SI.FIXTURES[name])
    o, e, c = run(fx, LID_A, crop=fx)
    many[name] = (c, "retry" in o, gates(o))
check("passing eyes never make a second call: blue, grey, dark brown and green irises each take one call and carry no retry field",
      all(c == 1 and not r and all(g.values()) for c, r, g in many.values()), many)

# a failing first and a passing second
ret_out, ret_ev, ret_calls = run(LID_A, CLEAN_A)
ret_requests = list(LAST_REQUESTS)
only_out, only_ev, _ = run(CLEAN_A)
first_out, first_ev, first_calls = run(LID_A, CLEAN_A, on=False)
check("a failing first and a passing second: two model calls, the second kept (ran, kept second, code kept2)",
      ret_calls == 2 and ret_out["retry"]["ran"] is True and ret_out["retry"]["kept"] == "second" and ret_out["retry"]["code"] == "kept2", (ret_calls, ret_out.get("retry")))
check("the kept restoration is the second, whole: the sealed clean JPEG, the display copy, the eye id and the profile are those of the passing image alone",
      clean_of(ret_out) == clean_of(only_out) and ret_out["image"] == only_out["image"] and ret_out["profile"] == only_out["profile"]
      and P.unseal_full(ret_out["sealed"])[1]["eye_id"] == ret_out["profile"]["eye_id"] == P.eye_id_of(clean_of(ret_out)), ret_out["profile"])
check("the sealed profile of the kept restoration passes both rules and is the one measured on its own bytes",
      gates(ret_out) == {"lid": True, "fill": True}
      and P.unseal_full(ret_out["sealed"])[1]["profile"].rec == EYE.profile_of_bytes(clean_of(ret_out), pad=1.12).rec, gates(ret_out))
check("the first restoration alone (the switch off) fails both rules; the retry turned that into a pass of both",
      first_calls == 1 and gates(first_out) == {"lid": False, "fill": False} and gates(ret_out) == {"lid": True, "fill": True}, (gates(first_out), gates(ret_out)))
check("the two requests of a retry are equal (prompt, the pixels of the crop, size, thinking, model; no seed is sent): the draws differ only because the model samples afresh",
      len(ret_requests) == 2 and ret_requests[0] == ret_requests[1], ret_requests)
r = ret_out["retry"]
check("the reply field carries codes and numbers only: ran, kept, code, gate1, sev1, sev2, ms (booleans, short codes, numbers); nothing else",
      set(r) == {"ran", "kept", "code", "gate1", "sev1", "sev2", "ms"} and isinstance(r["ran"], bool) and r["kept"] in ("first", "second") and r["gate1"] == "both"
      and r["sev1"] > 1.0 and r["sev2"] == 0.0 and isinstance(r["ms"], int) and r["ms"] >= 0 and "AIza" not in json.dumps(r) and "secret" not in json.dumps(r).lower(), r)
check("the event line: retry kept2, the first gate code, the two severities and the time of the second", ret_ev.get("retry") == "kept2" and ret_ev.get("gate1") == "both"
      and ret_ev.get("sev1") == r["sev1"] and ret_ev.get("sev2") == 0.0 and ret_ev.get("retry_ms") == r["ms"], ret_ev)
check("the event's gate, class and pupil describe the restoration that was kept (a pass), not the first", ret_ev.get("gate") == "ok" and ret_ev.get("reason") == "none", ret_ev)
built = E.build("enhance", ret_ev)
check("events.build keeps all five new fields of the line and nothing else is added",
      all(k in built for k in ("retry", "gate1", "sev1", "sev2", "retry_ms")) and built["retry"] == "kept2" and built["gate1"] == "both", built)
check("events.build drops a retry that is not a code, a severity that is not a number", "retry" not in E.build("enhance", {"retry": "not a code"}) and "sev1" not in E.build("enhance", {"sev1": "2"})
      and "retry" not in E.build("enhance", {"retry": 7}) and E.build("enhance", {"sev1": 1.5, "retry_ms": 12})["retry_ms"] == 12)
check("the seconds of the reply cover the second draw (they are the whole call's, and the retry's own time is inside them)", ret_out["seconds"] + 0.1 >= ret_out["retry"]["ms"] / 1000.0,
      (ret_out["seconds"], ret_out["retry"]["ms"]))

# the switch off
check("the switch off: a failing first makes one call, carries no retry field and no retry in the event, and fails the gate as the first restoration does",
      first_calls == 1 and "retry" not in first_out and not any(k in first_ev for k in ("retry", "gate1", "sev1", "sev2", "retry_ms")) and first_ev.get("gate") == "both", (first_ev, list(first_out)))

# both fail
b1_out, b1_ev, b1_calls = run(LID_A, LASH_A)
check("both fail and the second is clearly less severe (the lash fan fails the lid rule only, the lid wedge fails both): the second is kept",
      b1_calls == 2 and b1_out["retry"]["code"] == "kept2" and b1_out["retry"]["sev2"] <= ENH.RETRY_CLEAR * b1_out["retry"]["sev1"] and gates(b1_out) == {"lid": False, "fill": True}, (b1_out["retry"], gates(b1_out)))
b2_out, b2_ev, b2_calls = run(LASH_A, LID_A)
check("both fail and the second is worse and fails the fill rule the first passed: the first is kept, code kept1, the reply says ran and kept first",
      b2_calls == 2 and b2_out["retry"]["code"] == "kept1" and b2_out["retry"]["ran"] is True and b2_out["retry"]["kept"] == "first" and gates(b2_out) == {"lid": False, "fill": True}
      and b2_ev.get("retry") == "kept1", (b2_out["retry"], gates(b2_out)))
only_lash, _, _ = run(LASH_A)
check("kept1: the sealed restoration is the first one, whole", clean_of(b2_out) == clean_of(only_lash) and b2_out["profile"] == only_lash["profile"])

# time
SHORT = ENH.RETRY_MIN_LEFT - 0.1
t_out, t_ev, t_calls = run(LID_A, CLEAN_A, left=SHORT)
check("too little time (just under RETRY_MIN_LEFT): one model call, the first restoration, the reply says ran false and why (time)",
      t_calls == 1 and t_out["retry"]["ran"] is False and t_out["retry"]["code"] == "time" and t_out["retry"]["kept"] == "first" and "sev2" not in t_out["retry"]
      and gates(t_out) == {"lid": False, "fill": False}, (t_calls, t_out.get("retry")))
check("too little time: the reply is the first restoration alone, as with the switch off (the same bytes, profile, colour QA and Reveal)",
      clean_of(t_out) == clean_of(first_out) and t_out["profile"] == first_out["profile"] and t_out["qa"] == first_out["qa"] and t_out["reveal"] == first_out["reveal"])
check("too little time: the event says retry time with the first gate code and severity, and no second severity or time", t_ev.get("retry") == "time" and t_ev.get("gate1") == "both"
      and t_ev.get("sev1") > 1.0 and t_ev.get("sev2") is None and t_ev.get("retry_ms") is None and not any(k in E.build("enhance", t_ev) for k in ("sev2", "retry_ms")), t_ev)
edge_out, _, edge_calls = run(LID_A, CLEAN_A, left=ENH.RETRY_MIN_LEFT)
check("exactly RETRY_MIN_LEFT seconds left: the retry runs", edge_calls == 2 and edge_out["retry"]["code"] == "kept2", edge_out.get("retry"))
tiny_out, tiny_ev, tiny_calls = run(LID_A, CLEAN_A, left=3.0)
check("almost no time left (3 s): no second call, the preview comes whole with its seals (the profile is not measured: the gate is unknown, nothing is retried)",
      tiny_calls == 1 and "retry" not in tiny_out and tiny_out["ok"] is True and P.unseal(tiny_out["sealed"]) and tiny_out["profile"].get("unknown") is True and tiny_ev.get("gate") == "unknown", (tiny_calls, tiny_ev))

# a second call that fails
e_out, e_ev, e_calls = run(LID_A, L.ModelBusy("busy"))
check("the second call fails (the model is busy): 200 with the first restoration, ran false, code error, the event says error; the preview is not lost",
      e_calls == 2 and e_out["ok"] is True and e_out["retry"]["ran"] is False and e_out["retry"]["code"] == "error" and e_out["retry"]["kept"] == "first" and e_ev.get("retry") == "error"
      and clean_of(e_out) == clean_of(first_out) and P.is_display(base64.b64decode(e_out["image"])), (e_calls, e_out.get("retry")))
real_tfp = EYE.time_for_profile
calls_tfp = []


def second_has_no_time(left=None):
    calls_tfp.append(1)
    return len(calls_tfp) == 1


EYE.time_for_profile = second_has_no_time
try:
    u_out, u_ev, u_calls = run(LID_A, CLEAN_A)
finally:
    EYE.time_for_profile = real_tfp
check("the second restoration has no time left to be measured: it cannot be judged, the first is kept, code error",
      u_calls == 2 and u_out["retry"]["code"] == "error" and clean_of(u_out) == clean_of(first_out), u_out.get("retry"))

# faithful mode goes through the same steps
f_out, f_ev, f_calls = run(LID_A, CLEAN_A, mode="faithful")
check("the faithful mode takes the same path: a failing first and a passing second are two calls and the second is kept; the model is asked with thinking high both times",
      f_calls == 2 and f_out["retry"]["code"] == "kept2" and f_out["fallback"] is False and [q[3] for q in REQUESTS] == ["high", "high"], (f_out.get("retry"), REQUESTS))

# the trigger: which rules ask for a second restoration (RETRY_RULES); _draw is scripted here, so no model and no gate measurement run
def scripted_draws(rules, *profs):
    """enhance() with _draw scripted (the blue iris with the given profiles, one per call): (the reply, the number of restorations made)."""
    seq = [ENH.Draw(CLEAN_A, jpeg(CLEAN_A), p, 5, 0.99, False, {"ok": True}) for p in profs]
    made = []

    def fake(*a):
        made.append(1)
        return seq[min(len(made) - 1, len(seq) - 1)]

    real_draw, real_rules = ENH._draw, ENH.RETRY_RULES
    ENH._draw, ENH.RETRY_RULES = fake, rules
    try:
        out = ENH.enhance({"crop": b64(BLUE), "mode": "artistic", "pad": 1.12, "ticket": L.mint_ticket("work"), "lang": "en"})
    finally:
        ENH._draw, ENH.RETRY_RULES = real_draw, real_rules
    return out, len(made)


trig = {}
for rules in (("lid",), ("fill",), ("lid", "fill")):
    trig[rules] = (scripted_draws(rules, crafted(lid={"lid70": 6}), crafted())[1], scripted_draws(rules, crafted(fill={"run18": 120}), crafted())[1],
                   scripted_draws(rules, crafted(), crafted(lid={"lid70": 6}))[1])
check("RETRY_RULES decides which failure asks for a second restoration: (restorations made for a lid failure, a fill failure, a pass) = (2, 1, 1) for lid, (1, 2, 1) for fill, (2, 2, 1) for both",
      trig == {("lid",): (2, 1, 1), ("fill",): (1, 2, 1), ("lid", "fill"): (2, 2, 1)}, trig)
o_fill, n_fill = scripted_draws(("lid", "fill"), crafted(fill={"run18": 120}), crafted())
check("a fill failure under both rules: the second restoration is kept, the note says gate1 fill", n_fill == 2 and o_fill["retry"]["code"] == "kept2" and o_fill["retry"]["gate1"] == "fill", o_fill.get("retry"))
o_none, n_none = scripted_draws(("lid",), None, crafted())
check("a first restoration without a profile (no time to measure it) is never retried: its gate is unknown", n_none == 1 and "retry" not in o_none and o_none["profile"].get("unknown") is True, n_none)

# the events and the counts
agg = E.empty()
for ev_ in ({"retry": "kept2", "gate1": "lid", "sev1": 2.0, "sev2": 0.0, "retry_ms": 14000}, {"retry": "kept1", "gate1": "both", "sev1": 4.0, "sev2": 3.5, "retry_ms": 16000},
            {"retry": "time", "gate1": "lid", "sev1": 2.0}, {"retry": "error", "gate1": "lid", "sev1": 2.0, "retry_ms": 9000}, {"gate": "ok"}):
    E.add(agg, {"kind": "enhance", **E.build("enhance", ev_)})
check("events.add counts the codes per day and the time of the second restoration as ms['retry'] (sum and count)",
      agg["enhance_retry"] == {"kept2": 1, "kept1": 1, "time": 1, "error": 1} and agg["ms"]["retry"] == [39000, 3], (agg["enhance_retry"], agg["ms"].get("retry")))
check("events.add counts a second image call whenever the second restoration was made (retry_ms is there): 5 events, 2 without a second call and 3 with: 8 image calls",
      agg["gemini"]["image_1k"] == 8, agg["gemini"])
mrg = E.merge(agg, agg)
check("merge adds the new table like the old ones", mrg["enhance_retry"]["kept2"] == 2 and mrg["ms"]["retry"] == [78000, 6] and mrg["gemini"]["image_1k"] == 16)

# ============================================================================================ 4. the switch and the files
section("4. the switch SNAPEYES_RETRY2 (read once at import, BOM safe) and the files")
bom = chr(0xFEFF)
want = {None: True, "": True, "on": True, "ON": True, "1": True, "yes": True, "true": True, "off": False, "OFF": False, " off ": False, "0": False, "false": False, "False": False,
        "no": False, "NO": False, bom + "off": False, bom + "0": False, bom + "on": True}
bad = {}
for val, exp in want.items():
    if val is None:
        os.environ.pop("SNAPEYES_RETRY2", None)
    else:
        os.environ["SNAPEYES_RETRY2"] = val
    sp = importlib.util.spec_from_file_location("enhance_switch", os.path.join(API, "enhance.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    if m.RETRY_ON is not exp:
        bad[repr(val)] = m.RETRY_ON
os.environ.pop("SNAPEYES_RETRY2", None)
check("SNAPEYES_RETRY2: unset, empty, on, 1, yes, true are on; off, 0, false, no in any case, with spaces or a byte order mark are off (18 spellings)", not bad, bad)
check("the switch is read in one place only, api/enhance.py: the paid master chain and the other endpoints do not read it",
      sum("SNAPEYES_RETRY2" in read(f"api/{f}") for f in ("enhance.py", "master_eye.py", "master_compose.py", "compose.py", "deglare.py", "analyze.py", "checkout.py", "order.py", "_lib/iris.py")) == 1
      and "SNAPEYES_RETRY2" in read("api/enhance.py"))
changed = {rel: read(rel) for rel in ("api/enhance.py", "api/_lib/styles/gate.py", "api/_lib/events.py", "scripts/styles_tests/test_retry2.py")}
check("no dash (en or em) and no invisible or bidirectional character in the files this change touches",
      not any(re.search(DASH, s) for s in changed.values()) and not any(re.search(INVISIBLE, s) for s in changed.values()),
      [k for k, s in changed.items() if re.search(DASH, s)])
check("the paid master chain is untouched: master_eye.py and iris.py make no use of the gate's severity", all("severity(" not in read(f"api/{f}") for f in ("master_eye.py", "_lib/iris.py")))
check("nothing in this suite called the model or looked for a key (the image model was the script of section 3)", not CALLED and len(MODEL) >= 1, CALLED)
E.record = _real_record

# ------------------------------------------------------------------
ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed")
sys.exit(0 if ok == len(RESULTS) else 1)
