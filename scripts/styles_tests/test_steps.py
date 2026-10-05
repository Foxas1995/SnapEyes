# -*- coding: utf-8 -*-
"""WP6a of the v3 engine work: the master plan of a paid order, its steps and the state machine that runs them (api/_lib/styles/steps.py), the two
process guards (guard.py), the one duration constant (duration.py) and every place they reach: api/order.py compose_order (one step per call,
artwork {done, of, step}), api/_lib/maker.py (the chain, the watchdog, PROBE_HOPS), api/master_compose.py, the admin actions order_steps, rerun_step
and lab_steps, the clean-up of the style folder and the master events. Tests I11, I12, I19 and IE3 to IE6, IE8 (the part after payment), IE9 (the
class drift hold) and IE12 of the plan.

  1.  the one duration constant (IE12): vercel.json, every derived number at 60 s and at other durations, the build check and its refusals
  2.  the plan: make_plan, plan8 (what it hashes and what it does not), capacity, the break-even factors, PROBE_HOPS from the longest chain
  3.  the customer's words: the paid file draws what the preview draws
  4.  the guards (IE6): the memory budget and the one-heavy-render-at-a-time semaphore, released after an exception; the resident size meter
  5.  the state machine (IE3, IE5, IE8, IE9) on scripted executors: kills at every seam, storage errors, refusals, the third kill, two callers,
      deterministic refusals, plate faults, identical exceptions, engine_skew, the digest, rerun and recompose, the memory of twelve renders
  6.  a paid order of the LEGACY engine through the chain: one art step, the same artwork file as before (master_compose's own digest)
  7.  a paid order of a v3 style through the chain, the page's compose, the status progress, a plan of several steps and eight eyes
  8.  holds after payment: too big, engine_skew, class drift, plates, killed and identical failures: review.json, one note, no other style
  9.  the watchdog (IE4): a step that is killed is retaken with no page open
 10.  the admin: order_steps, rerun_step, recompose under the claims, lab_steps; the clean-up of the style folder; the master events
 11.  ENGINE_V against the recorded goldens, the files of the work

No network, no image model (every master is a procedural iris or a scripted stand in), no real eye. Run by suites/run_main.sh as v3steps.
    python test_steps.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest.mock as mock

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
SP_DIR = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP_DIR, "wave-pv", "tests") if SP_DIR else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")
NODE = shutil.which("node") or "node"

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3steps_")
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])          # synthetic Stripe and Resend keys, the ticket secret, a local store folder
os.environ["STYLE_PLATE_CACHE"] = os.path.join(TMP, "cache")
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
os.environ["SNAPEYES_SELF_BASE"] = BASE                 # the server's self-calls go to this very process
sys.path.insert(0, API)
import numpy as np  # noqa: E402
import requests  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import store  # noqa: E402
from _lib import pay  # noqa: E402
from _lib import maker as M  # noqa: E402
from _lib import cleanup as C  # noqa: E402
from _lib import duration as DU  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import ops  # noqa: E402
import _lib.styles as ST  # noqa: E402
from _lib.styles import steps as SP  # noqa: E402
from _lib.styles import guard as GD  # noqa: E402
from _lib.styles import costs as CO  # noqa: E402
from _lib.styles import plates as PL  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
ORDER_MOD = H.MODS["order"]
ME, MC = ORDER_MOD.ME, ORDER_MOD.MC
LAB_ORDER = "lab-261005-v3steps01"
PACK = json.load(open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
H.Fake.legal = dict(PACK, making_start="after_confirmation")      # the texts say the server starts an order right after its confirmation
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


def local(path):
    return os.path.join(STORE, *path.split("/"))


def exists(path):
    return os.path.exists(local(path))


def rj(path):
    try:
        with open(local(path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def wj(path, obj):
    os.makedirs(os.path.dirname(local(path)), exist_ok=True)
    with open(local(path), "w", encoding="utf-8") as f:
        json.dump(obj, f)


def wait_for(cond, timeout=60.0, step=0.2):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = cond()
        if v:
            return v
        time.sleep(step)
    return cond()


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=180)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path):
    r = requests.get(BASE + path, timeout=180)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def hook(obj):
    body, sig = H.signed_event(obj, "checkout.session.completed")
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=180)
    return r.status_code, r.json()


class Show:
    """A style made orderable for the length of a block (the ceilings are the registry's: a test may not raise one for good)."""
    def __init__(self, style, stage="live"):
        self.style, self.stage = style, stage

    def __enter__(self):
        self.old = CT.STYLES[self.style]["stage"]
        CT.STYLES[self.style]["stage"] = self.stage

    def __exit__(self, *a):
        CT.STYLES[self.style]["stage"] = self.old


def draft(eye, order=None, k=None, seed=1, lang="en"):
    b = {"action": "draft", "eye": eye, "crop": H.jpeg_b64(256, seed * 10 + eye), "preview": H.jpeg_b64(256, seed * 10 + eye + 5),
         "pad": 1.12, "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work"), "lang": lang, "ref": f"e{eye}"}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def new_order(eyes=1, style="studio_black", email="kunde@example.com", pay_it=True, lang="en", layout=None):
    c, j = draft(1, lang=lang)
    assert c == 200, (c, j)
    o, k = j["order"], j["k"]
    for i in range(2, eyes + 1):
        c, j = draft(i, o, k, lang=lang)
        assert c == 200, (c, j)
    body = {"order": o, "k": k, "eyes": eyes, "style": style, "names": "Ona", "title": "", "lang": lang, "consent_digital": True}
    if layout:
        body["layout"] = layout
    c, j = post("/api/checkout", body)
    assert c == 200, (c, j)
    sid = rj(f"orders/{o}/order.json")["checkout"]["session_id"]
    if pay_it:
        c, j = hook(H.pay_session(sid, email=email))
        assert c == 200, (c, j)
    return o, k, sid


def mails(to, subject_start=None, since=0):
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [to] and (subject_start is None or m["subject"].startswith(subject_start))]


def stopped(o, why=None):
    b = rj(f"orders/{o}/advance.json")
    return isinstance(b, dict) and b.get("state") == "stopped" and (why is None or b.get("why") == why) and b


READY_EN = "Your SnapEyes artwork is ready"
NOTES = lambda since: [m for m, _ in H.Fake.emails[since:] if m["to"] == ["info@snapeyes.com"]]


# ---------------------------------------------------------------------------- stand-ins for the image model's masters
_MASTERS = {}


def master_jpeg(kind="blue", pupil="round", side=4096, seed=11):
    key = (kind, pupil, side, seed)
    if key not in _MASTERS:
        b = io.BytesIO()
        SI.make(kind=kind, pupil=pupil, seed=seed, side=side).convert("RGB").save(b, "JPEG", quality=95)
        _MASTERS[key] = b.getvalue()
    return _MASTERS[key]


MODE = {"side": 4096, "kind": "blue", "delay": 0.0}
RENDERS = []
LOCK = threading.Lock()


def fake_master_eye(body):
    """master_eye's contract without the model: the stored master is a procedural iris (a 4096 px one for the single styles), its record carries the
    preview's eye id as the real one does; the real slot claim is kept so that a double render would show."""
    order, eye = body["order"], body["eye"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    folder = f"orders/{order}"
    key = f"{folder}/eye_{eye}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False, "key": key}
    lock = ME._claim(folder, eye)
    try:
        if store.exists(key):
            return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False, "key": key}
        time.sleep(MODE["delay"])
        data = master_jpeg(MODE["kind"], "round", MODE["side"], 10 + eye)
        with LOCK:
            RENDERS.append((order, eye))
        store.put(key, data, "image/jpeg", upsert=False)
        draft = store.get_json(f"{folder}/draft/eye_{eye}.json")            # the real master_eye records the id of the preview it was made from: the draft's own
        eid = draft.get("eye_id") if isinstance(draft, dict) and isinstance(draft.get("eye_id"), str) else f"{eye:02x}" * 8
        store.put(f"{folder}/eye_{eye}.json", store.json_bytes({"order": order, "eye": eye, "eye_id": eid, "qa": {"ok": True}, "bytes": len(data), "pad": 1.12,
                                                              "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}), "application/json", upsert=True)
        return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False, "key": key}
    finally:
        ME._release(lock)


LEGACY_COMPOSES = []


def fake_legacy_compose(body):
    """The legacy master compose, scripted (the real one is 20 s of CPU): it keeps its digest rule, so a changed input makes another file."""
    order = body["order"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    recs = {k: store.get_json(k[:-4] + ".json") for k in body["keys"]}
    ident = dict({k: body[k] for k in ("keys", "style", "layout", "names", "title")}, size=4096, eyes=[MC._identity(recs[k]) for k in body["keys"]])
    digest = hashlib.sha256(json.dumps(ident, sort_keys=True, ensure_ascii=True).encode()).hexdigest()[:16]
    key = f"orders/{order}/artwork_{digest}.jpg"
    if not store.exists(key):
        with LOCK:
            LEGACY_COMPOSES.append(order)
        store.put(key, b"artwork " + digest.encode(), "image/jpeg", upsert=True)
    return {"ok": True, "url": store.signed_url(key, 604800), "key": key, "width": 4096, "height": 2600, "bytes": 24, "style": body["style"],
            "layout": body["layout"], "count": len(body["keys"]), "existing": False, "needs_review": False}


ME.master_eye = fake_master_eye
REAL_MC = MC.master_compose


# ============================================================================================ 1. the one duration constant
section("1. the one duration constant (IE12)")
vj = json.load(open(os.path.join(REPO, "vercel.json"), encoding="utf-8"))
check("vercel.json: every function entry has the maxDuration that api/_lib/duration.py names (the build check holds them equal)",
      len({v["maxDuration"] for v in vj["functions"].values()}) == 1 and vj["functions"]["api/order.py"]["maxDuration"] == DU.DURATION_S, vj["functions"]["api/order.py"])
x60 = DU.derive(60)
check("at 60 s the derived numbers are the ones the code always had: work 52, lease 75, claims 75, fresh 100, wait 40, spare 4, clean-up lock 120",
      (x60["budget"], x60["lease_stale"], x60["compose_stale"], x60["fresh"], x60["wait_max"], x60["spare"], x60["cleanup_stale"], x60["function_seconds"])
      == (52.0, 75.0, 75.0, 100.0, 40.0, 4.0, 120.0, 60.0), x60)
check("every module reads them from the one constant: iris.BUDGET, maker (FUNCTION_SECONDS, SPARE, LEASE_STALE, FRESH, WAIT_MAX), order.COMPOSE_STALE, "
      "master_eye.LOCK_STALE, cleanup.LOCK_STALE, costs.WORK_BUDGET_S, steps.LOCK_STALE",
      (L.BUDGET, M.FUNCTION_SECONDS, M.SPARE, M.LEASE_STALE, M.FRESH, M.WAIT_MAX, ORDER_MOD.COMPOSE_STALE, ME.LOCK_STALE, C.LOCK_STALE, CO.WORK_BUDGET_S, SP.LOCK_STALE)
      == (DU.BUDGET_S, DU.FUNCTION_SECONDS, DU.SPARE_S, DU.LEASE_STALE_S, DU.FRESH_S, DU.WAIT_MAX_S, DU.COMPOSE_STALE_S, DU.LEASE_STALE_S, DU.CLEANUP_STALE_S,
          DU.BUDGET_S, DU.LEASE_STALE_S), (L.BUDGET, M.LEASE_STALE, ORDER_MOD.COMPOSE_STALE, ME.LOCK_STALE, C.LOCK_STALE))
rules = {d: DU.problems(d) for d in (60, 90, 120, 300, 800)}
check("the lease rule holds at every duration from 60 to 800 s: a lease outlives its holder by the margin, the watchdog fires after the lease has aged out, "
      "each relay waits no longer than the longest wait, a relay can still ask for the next step",
      all(not v for v in rules.values()), rules)
check("a duration below 60 s breaks the watchdog's two relays, and the check says so (a function that short is a different design)",
      any("watchdog" in p or "outside" in p for p in DU.problems(30)), DU.problems(30))
x300 = DU.derive(300)
check("a longer function lengthens every lease with it (300 s: work 292, lease 315, fresh 340): the old 75 s lease would have let a second caller take over a live render",
      (x300["budget"], x300["lease_stale"], x300["fresh"]) == (292.0, 315.0, 340.0) and x300["lease_stale"] > 300, x300)
wd = (DU.WATCHDOG_FIRST_S, DU.WATCHDOG_THEN_S)
check("the watchdog's two relays wait out the lease (40 + 40 s against a 75 s lease) and no longer than the 48 h promise's first 120 s",
      sum(wd) >= DU.LEASE_STALE_S and sum(wd) < 120 and all(w <= DU.WAIT_MAX_S for w in wd), wd)

# the build check, on a tiny tree (the handlers' names, vercel.json, duration.py): the refusals and the control
NODE_CHECK = os.path.join(TMP, "dur_check.mjs")
open(NODE_CHECK, "w", encoding="utf-8").write("""import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const repo = process.argv[2];
const { checkFunctions } = await import(pathToFileURL(join(repo, 'scripts', 'check_styles.mjs')).href);
const out = {};
for (const root of process.argv.slice(3)) { const p = []; try { checkFunctions(root, p); } catch (e) { p.push('THROWN: ' + e.message); } out[root] = p; }
console.log(JSON.stringify(out));
""")


def tiny_tree(name, vj_edit=None, dur_text=None):
    root = os.path.join(TMP, name)
    os.makedirs(os.path.join(root, "api", "_lib"))
    for h in vj["functions"]:
        open(os.path.join(root, h), "w").write("")
    d = json.loads(json.dumps(vj))
    if vj_edit:
        vj_edit(d)
    json.dump(d, open(os.path.join(root, "vercel.json"), "w"))
    text = read("api/_lib/duration.py") if dur_text is None else dur_text
    open(os.path.join(root, "api", "_lib", "duration.py"), "w", encoding="utf-8", newline="").write(text)
    return root


trees = {"ok": tiny_tree("d_ok"),
         "vj300": tiny_tree("d_vj", lambda d: d["functions"]["api/order.py"].update({"maxDuration": 300})),
         "all300": tiny_tree("d_all", lambda d: [f.update({"maxDuration": 300}) for f in d["functions"].values()]),
         "py300": tiny_tree("d_py", dur_text=re.sub(r"^DURATION_S = 60", "DURATION_S = 300", read("api/_lib/duration.py"), flags=re.M)),
         "noconst": tiny_tree("d_none", dur_text="X = 1\n")}
rc = subprocess.run([NODE, NODE_CHECK, REPO] + list(trees.values()), capture_output=True, text=True, encoding="utf-8", timeout=120)
try:
    got = json.loads(rc.stdout.strip().splitlines()[-1])
except Exception:  # noqa: BLE001
    got = None
check("the build check ran on the tiny trees", got is not None, (rc.returncode, rc.stderr[-400:], rc.stdout[-300:]))
if got:
    probs = {k: [p for p in got[v] if "duration" in p.lower() or "DURATION" in p] for k, v in trees.items()}
    check("check_styles item 13: a tree whose maxDuration equals DURATION_S passes (no duration problem)", probs["ok"] == [], got[trees["ok"]][:3])
    check("check_styles item 13 refuses one function with another maxDuration than DURATION_S", any("api/order.py" in p and "DURATION_S 60" in p for p in probs["vj300"]), probs["vj300"])
    check("check_styles item 13 refuses every function longer than DURATION_S (all at 300, the constant at 60): the constant must change with the limit",
          len(probs["all300"]) >= 11 and all("300" in p for p in probs["all300"]), probs["all300"][:2])
    check("check_styles item 13 refuses a DURATION_S raised alone (the constant at 300, vercel.json at 60)", len(probs["py300"]) >= 11, probs["py300"][:2])
    check("check_styles item 13 refuses a duration.py without the constant", any("cannot be read" in p for p in probs["noconst"]), probs["noconst"])

# ============================================================================================ 2. the plan
section("2. the plan: make_plan, plan8, capacity, the chain's length")
eyes1 = [{"eye_id": "ab" * 8, "profile": None}]
p_clean = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, eyes1)
p_leg = SP.make_plan({"style": "studio_black", "eyes": 2, "layout": "galaxy"}, [{"eye_id": "01" * 8}, {"eye_id": "02" * 8}])
check("a plan of a style of the v3 engine: the design used, the canvas, the seed key, one art step for every eye, its need and memory from the cost table, plan8",
      p_clean["family"] == "singles" and p_clean["design_used"] == "clean" and p_clean["canvas"] == "1:1" and p_clean["engine_v"] == ST.ENGINE_V
      and [s["name"] for s in p_clean["steps"]] == ["art"] and p_clean["steps"][0]["eyes"] == [1] and p_clean["steps"][0]["need_s"] > 10
      and isinstance(p_clean["steps"][0]["est_mb"], int) and re.fullmatch(r"[0-9a-f]{8}", p_clean["plan8"]) and p_clean["seed_key"]["design_used"] == "clean"
      and p_clean["reg"] == CT.registry_hash() and p_clean["pv"] == CT.PLATES_VERSION and p_clean["eye_ids"] == ["ab" * 8], p_clean)
check("a plan of a style of the legacy engine: family legacy, the style is the design, no engine version, no cost row but the legacy need (31.9 s at the factor 1.6 for eight eyes)",
      p_leg["family"] == "legacy" and p_leg["design_used"] == "studio_black" and p_leg["engine_v"] == 0 and p_leg["cost_key"] is None
      and p_leg["steps"][0]["need_s"] == CO.legacy_need(2) and CO.legacy_need(8) == 31.9 and p_leg["steps"][0]["est_mb"] is None, p_leg)
check("valid_plan accepts a made plan and refuses a plan of another version, an unknown style, no steps",
      SP.valid_plan(p_clean) and not SP.valid_plan(dict(p_clean, v=2)) and not SP.valid_plan(dict(p_clean, style="nope")) and not SP.valid_plan(dict(p_clean, steps=[]))
      and not SP.valid_plan({}), "")
base8 = p_clean["plan8"]
with mock.patch.object(CT, "registry_hash", lambda: "ffffffffffff"):
    p_reg = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, eyes1)
with mock.patch.dict(os.environ, {"STYLE_SLOW_CPU": "2.5"}):
    p_slow = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, eyes1)
p_names = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single", "names": "Anna;Max", "date": "12 May"}, eyes1)
p_later = dict(p_clean, created_at=1)
check("plan8 does NOT change with the registry hash (provenance only), the slow factor (an estimate), the time of creation or the customer's words (no names in a seed)",
      p_reg["plan8"] == base8 and p_slow["plan8"] == base8 and p_slow["steps"][0]["need_s"] != p_clean["steps"][0]["need_s"] and p_names["plan8"] == base8
      and SP.plan8(p_later) == base8 and p_reg["reg"] == "ffffffffffff", (base8, p_reg["plan8"], p_slow["plan8"], p_names["plan8"]))
p_eye = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, [{"eye_id": "cd" * 8}])
p_other = SP.make_plan({"style": "solo.gold", "eyes": 1, "layout": "single"}, eyes1)
p_look = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single", "opts": {"look": "x"}}, eyes1)
check("plan8 changes with the eyes' ids, the style and an option the buyer chose", len({base8, p_eye["plan8"], p_other["plan8"], p_look["plan8"]}) == 4,
      (base8, p_eye["plan8"], p_other["plan8"], p_look["plan8"]))
key_a = SP.artwork_key("261005-keytest01", p_clean, 0)
key_b = SP.artwork_key("261005-keytest01", p_clean, 1)
with mock.patch.object(CT, "registry_hash", lambda: "eeeeeeeeeeee"), mock.patch.dict(CT.STYLES["solo.gold"], {"stage": "preview"}):
    key_c = SP.artwork_key("261005-keytest01", dict(p_clean, reg="eeeeeeeeeeee"), 0)
check("the artwork's file name is sha256(plan8, rerun) and nothing else: an unrelated registry edit and a new registry hash leave it, a rerun changes it",
      key_a == key_c and key_a != key_b and re.fullmatch(r"orders/261005-keytest01/artwork_[0-9a-f]{16}\.jpg", key_a)
      and key_a[:-4].endswith(hashlib.sha256(json.dumps({"plan8": base8, "rerun": 0}, sort_keys=True).encode()).hexdigest()[:16]), (key_a, key_b, key_c))
caps = {f: SP.capacity(SP.make_plan({"style": "solo.powder", "eyes": 1, "layout": "single"}, eyes1), f) for f in (1.6, 3.5, 3.7, 6.0)}
check("capacity of a Powder Burst master flips where the cost table says (break-even factor 3.62): fits at 1.6 and 3.5, never at 3.7 and 6.0 (why time)",
      caps[1.6]["ok"] and caps[3.5]["ok"] and not caps[3.7]["ok"] and caps[3.7]["why"] == "time" and caps[6.0]["why"] == "time"
      and abs(CO.break_even_factor("singles.powder", 1) - 3.62) < 0.02, {k: (v["ok"], v["need_s"]) for k, v in caps.items()})
with mock.patch.object(CO, "MEM_BUDGET_MB", 300):
    cap_mem = SP.capacity(p_clean)
check("capacity says memory when the estimate passes the memory budget (here a 300 MB budget), and no_cost for a design the table has no row for",
      cap_mem["why"] == "memory" and not cap_mem["ok"] and SP.capacity(dict(p_clean, cost_key="nope.none"))["why"] == "no_cost", (cap_mem, ""))
check("the plan says it would like to be cut when its need passes the step budget (WP6b's trigger): not for Clean, yes for Trio at a slow factor of 2.5",
      not p_clean["steps"][0]["split_wanted"] and SP.capacity(dict(p_clean, cost_key="collision.trio", eyes=3, work_side=4096), 2.5)["need_s"] > CO.STYLE_STEP_BUDGET, "")
check("the longest planned chain is 10 hops (eight eyes, one art step, the ready email: the same chain as before the plan) and PROBE_HOPS is that plus 4, capped by MAX_HOPS",
      SP.longest_chain() == 10 and M.PROBE_HOPS == min(M.MAX_HOPS, 10 + 4) == 14, (SP.longest_chain(), M.PROBE_HOPS))
sid_p = "duo.kiss_collision"
saved = CT.ENGINE[sid_p]["steps"]
CT.ENGINE[sid_p]["steps"] = {"2": ["prep", "prep", "art"]}
try:
    chain_with_plan = SP.longest_chain()
finally:
    CT.ENGINE[sid_p]["steps"] = saved
check("a plan of more steps lengthens the chain the probe must cover (steps joined for two eyes: 2 + 3 + 1 = 6 is still under 10; for eight eyes 8 + 3 + 1 = 12)",
      chain_with_plan == 10, chain_with_plan)
CT.ENGINE["grp.collision"]["steps"], saved8 = {"8": ["prep", "prep", "art"]}, CT.ENGINE["grp.collision"]["steps"]
try:
    chain8 = SP.longest_chain()
finally:
    CT.ENGINE["grp.collision"]["steps"] = saved8
check("... and PROBE_HOPS follows: a three step plan for eight eyes makes the longest chain 12 and the probe 16", chain8 == 12 and min(M.MAX_HOPS, chain8 + 4) == 16, chain8)
check("the registry hash did not move while the test edited and restored an entry (the literal is the test's own copy in this process)", CT.registry_hash() == "7b1b4069399b", CT.registry_hash())

# ============================================================================================ 3. the words
section("3. the customer's words: the paid file draws what the preview draws")
CMP = H.MODS.get("compose")
if CMP is None:
    import importlib.util
    sp = importlib.util.spec_from_file_location("compose_for_words", os.path.join(API, "compose.py"))
    CMP = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(CMP)
samples = ["Anna;Max", "Ona", ["Rūta", "Šarūnas", "Ąžuolas"], "Zoltán;Éva;Őrs;Űrmenet", "", None, 12, {"a": 1}, "A" * 400, ["x" * 30] * 9, "Mia\nTom", "Žemaitė ; Pétur;",
           "emoji \U0001F600 here", ["ok", 3, None]]
dates = ["12 May 2026", "12;05;2026", "", None, "x" * 50, "2026-10-05\n", 7, "Šv. Kalėdos"]
check("master_words cuts and cleans the names and the date exactly as the preview does (api/compose.py _engine_text and _engine_date, 60 and 20 characters): "
      f"{len(samples)} names and {len(dates)} dates, in Lithuanian, Hungarian and German letters, lists, numbers, a letter the font lacks",
      all(SP.master_words({"names": s, "date": d})[0] == CMP._engine_text(s, 60) and SP.master_words({"names": s, "date": d})[1] == CMP._engine_date(d, 20)
          for s in samples for d in dates), [(s, SP.master_words({"names": s})[0], CMP._engine_text(s, 60)) for s in samples
                                              if SP.master_words({"names": s})[0] != CMP._engine_text(s, 60)])
check("words_sha changes with a changed line and ignores what the drawer would not draw", SP.words_sha({"names": "Anna"}) != SP.words_sha({"names": "Anne"})
      and SP.words_sha({"names": "Anna"}) == SP.words_sha({"names": " Anna "}) and SP.words_sha({}) == SP.words_sha({"names": ""}), "")

# ============================================================================================ 4. the guards
section("4. the guards (IE6): the memory budget, the one heavy render at a time, the meter")
GD.reset()
with mock.patch.object(GD, "WAIT_S", 0.3):
    with GD.slot(est_mb=900, est_s=20, budget_mb=1434, wait=0.3):
        st1 = GD.state()
        t0 = time.time()
        try:
            with GD.slot(est_mb=900, est_s=1.0, budget_mb=1434, wait=0.3):      # a light render: only the memory can refuse it
                e_mem = None
        except GD.Busy as e:
            e_mem = e
        waited = time.time() - t0
        try:
            with GD.slot(est_mb=100, est_s=20, budget_mb=1434, wait=0.2):
                e_cpu = None
        except GD.Busy as e:
            e_cpu = e
        with GD.slot(est_mb=100, est_s=1.0, budget_mb=1434, wait=0.2):
            light = GD.state()
check("two 4K renders never share an instance: a second of 900 MB (even a light one) waits and is then refused (Busy, memory) while the first holds 900 of 1434 MB",
      st1["mb"] == 900 and st1["heavy"] == 1 and isinstance(e_mem, GD.Busy) and e_mem.kind == "memory" and waited >= 0.25, (st1, e_mem, waited))
check("a second heavy render is refused for the CPU even when its memory fits (Busy, cpu), a light one (under 3 s) goes beside the heavy one",
      isinstance(e_cpu, GD.Busy) and e_cpu.kind == "cpu" and light["running"] == 2 and light["heavy"] == 1, (e_cpu, light))
check("every slot is released when the block ends", GD.state() == {"mb": 0.0, "heavy": 0, "running": 0}, GD.state())
check("a refusal says when the room should be there (Busy.eta_s): what the holder that frees it first still has by its own estimate, 20 s less the time already used (the CPU's and "
      "the memory's refusal alike)", all(isinstance(x, GD.Busy) and isinstance(x.eta_s, float) and 18.0 <= x.eta_s <= 20.0 for x in (e_mem, e_cpu)), (e_mem and e_mem.eta_s, e_cpu and e_cpu.eta_s))
GD.reset()
with GD.slot(est_mb=100, est_s=None, wait=0.2):                      # a holder that declared no estimate (unknown counts as heavy)
    try:
        with GD.slot(est_mb=100, est_s=20, wait=0.2):
            e_unknown = None
    except GD.Busy as e:
        e_unknown = e
with GD.slot(est_mb=100, est_s=0.1, heavy_s=0.05):                   # a holder past its own estimate
    time.sleep(0.3)
    try:
        with GD.slot(est_mb=100, est_s=20, wait=0.1):
            e_late = None
    except GD.Busy as e:
        e_late = e
check("a holder that declared no estimate gives no eta (None); a holder past its estimate gives 0.0 (never negative); the holder's record goes with its slot (nothing is left behind)",
      isinstance(e_unknown, GD.Busy) and e_unknown.eta_s is None and isinstance(e_late, GD.Busy) and e_late.eta_s == 0.0 and not GD._HOLDERS and GD.state() == {"mb": 0.0, "heavy": 0, "running": 0},
      (e_unknown and e_unknown.eta_s, e_late and e_late.eta_s, GD._HOLDERS))
try:
    with GD.slot(est_mb=500, est_s=30):
        raise RuntimeError("the render broke")
except RuntimeError:
    pass
check("both guards are released when the render raises", GD.state() == {"mb": 0.0, "heavy": 0, "running": 0}, GD.state())
t_w = []
GD.reset()
holder_in, holder_go = threading.Event(), threading.Event()


def holder():
    with GD.slot(est_mb=800, est_s=20, budget_mb=1434):
        holder_in.set()
        holder_go.wait(10)


th = threading.Thread(target=holder)
th.start()
holder_in.wait(5)
threading.Timer(0.3, holder_go.set).start()
t0 = time.time()
with GD.slot(est_mb=800, est_s=20, budget_mb=1434, wait=3.0):
    t_w.append(time.time() - t0)
th.join()
check("a render that waits gets its place as soon as the first one lets go (within the wait), it is not refused", 0.2 < t_w[0] < 2.0, t_w)
GD.reset()
with GD.slot(est_mb=5000, est_s=20, budget_mb=1434, wait=0.2):
    alone = GD.state()
check("a render larger than the whole budget is let in when nothing else runs (assess() refuses such a plan long before: a guard that can never be satisfied is a deadlock)",
      alone["running"] == 1, alone)
GD.reset()
t0 = time.time()
try:
    with GD.slot(est_mb=10, est_s=20, left=1.5, wait=2.0):
        pass
    ok_left = True
except GD.Busy:
    ok_left = False
check("the wait never takes more than the invocation has left minus one second (here 1.5 s left: it waits at most 0.5 s, and a free guard needs no wait at all)", ok_left, "")
rss0, hwm0 = GD.memory_now()
w = GD.MemWatch().start()
big = np.ones((70_000_000,), np.uint8) + 1
time.sleep(0.35)
m1 = w.stop()
del big
check("the meter reports the INCREASE of the resident size over a step (VmRSS: about +67 MB for a 70 MB array) and the instance's own high-water mark beside it",
      m1["peak_mb"] is not None and 40 <= m1["peak_mb"] <= 200 and m1["hwm_mb"] is not None and m1["hwm_mb"] >= m1["peak_mb"], (rss0, hwm0, m1))


# ============================================================================================ 5. the state machine on scripted executors
section("5. the state machine (IE3, IE5, IE8, IE9): kills at every seam, refusals, plate faults, identical exceptions, the digest, rerun and recompose")
import contextlib  # noqa: E402

EVENTS = []
_real_record = E.record


def spy_record(kind, **fields):
    EVENTS.append((kind, dict(fields)))
    return False


E.record = spy_record
N_ORDER = [0]
DELIVERED = []


def fresh_order(prefix="st"):
    N_ORDER[0] += 1
    return f"261005-{prefix}{N_ORDER[0]:06d}"


SPEC1 = {"eyes": 1, "style": "solo.clean", "layout": "single", "names": "Ona", "title": ""}


def mkctx(order, spec=None, finish=True, arm=None, arrival_left=None, rec=None, legacy=None):
    spec = dict(spec or SPEC1)

    def fin(r):
        d = {"key": r["key"], "needs_review": bool(r.get("needs_review")), "created_at": int(time.time())}
        DELIVERED.append((order, r["key"]))
        store.put(f"orders/{order}/delivery.json", store.json_bytes(d), "application/json", upsert=True)
        return d
    return SP.Ctx(order, spec, rec=rec, by="test", finish=fin if finish else None, arm=arm, arrival_left=arrival_left, legacy=legacy)


class Exe:
    """A scripted executor of the art step. script: what each call does ("ok", "storage", "exc", "exc2", "plate", "review"); block: an event the call waits
    for (two callers); it records its calls and what it was handed."""
    def __init__(self, script=None, block=None):
        self.script, self.calls, self.block, self.entered = list(script or []), 0, block, threading.Event()

    def __call__(self, ctx, plan, step, rerun):
        self.calls += 1
        self.entered.set()
        if self.block is not None:
            self.block.wait(30)
        act = self.script.pop(0) if self.script else "ok"
        if act == "storage":
            raise store.StorageError("put: HTTP 500 stand-in")
        if act == "exc":
            raise RuntimeError("the very same failure")
        if act == "exc2":
            raise ValueError("another failure")
        if act == "plate":
            raise PL.PlateUnavailable("P-SN-CLOUD__stand_in", "missing")
        key = SP.artwork_key(ctx.order, plan, rerun)
        data = b"J" * 100 + str(self.calls).encode()
        store.put(key, data, "image/jpeg", upsert=True)
        store.put(key[:-4] + ".json", store.json_bytes({"bytes": len(data), "needs_review": act == "review", "rerun": int(rerun)}), "application/json", upsert=True)
        res = {"key": key, "width": 8, "height": 8, "bytes": len(data), "style": plan["style"], "layout": plan["layout"], "count": plan["eyes"],
               "existing": False, "needs_review": act == "review", "url": "https://example.test/u"}
        recs = [store.get_json(k[:-4] + ".json") for k in SP._eye_keys(ctx, step)]
        return SP.Out(res, [{"path": key, "bytes": len(data), "sha12": SP._sha12(data)}], inputs=SP._inputs(ctx, plan, recs))


def steps_of(order, name="art"):
    return {"plan": rj(f"orders/{order}/style/plan.json"), "done": rj(f"orders/{order}/style/done_{name}.json"), "try": rj(f"orders/{order}/style/try_{name}.json"),
            "lock": exists(f"orders/{order}/style/{name}.lock"), "rerun": rj(f"orders/{order}/style/rerun.json")}


def raises(fn, exc):
    try:
        fn()
    except exc as e:
        return e
    except BaseException as e:  # noqa: BLE001
        return repr(e)
    return None


def hold_of(fn):
    e = raises(fn, SP.Hold)
    return e.reason if isinstance(e, SP.Hold) else e


# a normal run: the plan is made and stored, the step runs once, the records are written, the claim and `open` are cleared
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    got = SP.advance(mkctx(o))
s = steps_of(o)
check("a first call makes the plan (plan.json, upsert=False), runs the art step once, writes done_art.json LAST and try_art.json, hands the artwork to finish, and ends clear: "
      "no claim left, nothing open, no kill",
      got["final"] and got["ran"] == ["art"] and exe.calls == 1 and s["plan"]["plan8"] == got["plan8"] and s["done"]["step"] == "art" and s["done"]["result"]["key"] == got["artwork"]["key"]
      and not s["lock"] and s["try"]["open"] is False and s["try"]["kills"] == 0 and s["try"]["attempts"] == 1 and exists(f"orders/{o}/delivery.json")
      and DELIVERED[-1] == (o, got["artwork"]["key"]) and got["delivery"]["key"] == got["artwork"]["key"] and exists(f"{SP.INDEX}/{o}.json"), (s, got))
check("the done record has the numbers the admin shows: wall time, CPU, the planned need and memory, the inputs, who made it, when",
      all(k in s["done"] for k in ("ms", "cpu_s", "peak_mb", "hwm_mb", "need_s", "est_mb", "inputs", "by", "at", "outputs", "attempt")) and s["done"]["by"] == "test"
      and s["done"]["need_s"] == s["plan"]["steps"][0]["need_s"], s["done"])
ev = [f for k, f in EVENTS if k == "master" and f.get("order") == o]
check("the step wrote its master event: step art, part 1 of 1, the time, the style, the design, the planned need, the memory increase and the instance's high-water mark",
      len(ev) == 1 and ev[0]["step"] == "art" and ev[0]["part"] == 1 and ev[0]["of"] == 1 and ev[0]["style"] == "solo.clean" and ev[0]["design"] == "clean"
      and isinstance(ev[0]["ms"], int) and ev[0]["need_s"] == s["done"]["need_s"] and "peak_mb" in ev[0] and "hwm_mb" in ev[0] and ev[0]["kills"] == 0, ev)
n_deliv = len(DELIVERED)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    again = SP.advance(mkctx(o))
check("a call after the step is done renders nothing (the done record and its output are trusted) and gives the same file",
      again["final"] and again["ran"] == [] and exe.calls == 1 and again["artwork"]["key"] == got["artwork"]["key"] and again["artwork"]["existing"] is True, again)

# kill AFTER the claim: the next call finds `open` still set, counts ONE kill and goes on
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    SP.create_plan(mkctx(o))
    wj(f"orders/{o}/style/art.lock", {"t": time.time() - 200, "id": "dead"})
    wj(f"orders/{o}/style/try_art.json", {"kills": 0, "open": True, "attempts": 1, "plate": 0, "errors": [], "watchdog": 1})
    got = SP.advance(mkctx(o))
s = steps_of(o)
check("a kill after the claim (a stale claim and a try record still open): the next call takes the claim over, counts exactly one kill, renders, clears `open`",
      got["final"] and exe.calls == 1 and s["try"]["kills"] == 1 and s["try"]["open"] is False and s["try"]["attempts"] == 2 and not s["lock"], s["try"])
# the THIRD kill holds, and renders nothing
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    SP.create_plan(mkctx(o))
    wj(f"orders/{o}/style/art.lock", {"t": time.time() - 200, "id": "dead"})
    wj(f"orders/{o}/style/try_art.json", {"kills": 2, "open": True, "attempts": 3, "plate": 0, "errors": [], "watchdog": 2})
    why = hold_of(lambda: SP.advance(mkctx(o)))
s = steps_of(o)
check("the third kill holds the order (style_step_failed): nothing is rendered, no done record, the count is 3 and nothing is left open",
      why == "style_step_failed" and exe.calls == 0 and s["done"] is None and s["try"]["kills"] == 3 and s["try"]["open"] is False, (why, s["try"]))
hold_ev = [f for k, f in EVENTS if k == "master" and f.get("order") == o and f.get("hold")]
check("... and the hold is an event (master, hold style_step_failed): the admin counts holds by code", len(hold_ev) == 1 and hold_ev[0]["hold"] == "style_step_failed", hold_ev)

# kill BETWEEN the done record and delivery.json: the next call writes the delivery and renders nothing
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    first = SP.advance(mkctx(o, finish=False))
    gap = not exists(f"orders/{o}/delivery.json") and steps_of(o)["done"] is not None
    n_before = len(DELIVERED)
    second = SP.advance(mkctx(o))
check("a kill between the done record and delivery.json (the artwork and its done record exist, the delivery does not): the next call writes delivery.json "
      "without rendering again",
      gap and exe.calls == 1 and second["ran"] == [] and len(DELIVERED) == n_before + 1 and DELIVERED[-1] == (o, first["artwork"]["key"])
      and exists(f"orders/{o}/delivery.json"), (gap, exe.calls, second["ran"]))
# the artwork's object gone from storage while the done record stays: the step is drawn again, never trusted
store.delete(first["artwork"]["key"])
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    third = SP.advance(mkctx(o, finish=False))
check("a done record whose output is not in storage is not trusted: the step runs again (readers trust only a done record whose object exists)",
      exe.calls == 2 and third["ran"] == ["art"] and store.exists(third["artwork"]["key"]), (exe.calls, third["ran"]))
# a kill between the output and the done record: the stored output is reused, only the done record is written
o = fresh_order()
exe1, exe2 = Exe(), Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe1}):
    one = SP.advance(mkctx(o, finish=False))
os.remove(local(f"orders/{o}/style/done_art.json"))
os.remove(local(f"orders/{o}/style/try_art.json"))
with mock.patch.dict(SP.EXECUTORS, {"art": exe2}):
    two = SP.advance(mkctx(o, finish=False))
check("a kill between the output and the done record: the step runs again (the executor of a real engine reuses the stored artwork); the new done record names the same file",
      two["ran"] == ["art"] and two["artwork"]["key"] == one["artwork"]["key"] and steps_of(o)["done"] is not None, (two["ran"], one["artwork"]["key"], two["artwork"]["key"]))

# a storage error AFTER the claim never counts; a refusal BEFORE the claim never counts
o = fresh_order()
exe = Exe(["storage", "ok"])
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    e1 = raises(lambda: SP.advance(mkctx(o)), store.StorageError)
    s1 = steps_of(o)
    got = SP.advance(mkctx(o))
check("a storage error after the claim is not a kill, not an error signature, not a plate fault: nothing counted, `open` cleared, the claim released; the next call makes it",
      isinstance(e1, store.StorageError) and s1["try"]["kills"] == 0 and s1["try"]["errors"] == [] and s1["try"]["plate"] == 0 and s1["try"]["open"] is False and not s1["lock"]
      and got["final"] and steps_of(o)["try"]["kills"] == 0, (e1, s1))
o = fresh_order()
exe = Exe()
SP.create_plan(mkctx(o))
holder_in, holder_go = threading.Event(), threading.Event()


def hold_slot():
    with GD.slot(est_mb=500, est_s=30):
        holder_in.set()
        holder_go.wait(20)


th = threading.Thread(target=hold_slot)
th.start()
holder_in.wait(5)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), mock.patch.object(GD, "WAIT_S", 0.3):
    e_busy = raises(lambda: SP.advance(mkctx(o)), store.Answer)
holder_go.set()
th.join()
check("a refusal before the claim (the guards are full) is 503 room_retry (asked again after the holder's remaining 30 s estimate) and counts nothing: no try record, no claim, the executor never ran",
      isinstance(e_busy, store.Answer) and e_busy.status == 503 and e_busy.body["reason"] == "room_retry" and 28 <= e_busy.body["retry_after"] <= 30 and e_busy.body["room"] == "cpu" and exe.calls == 0
      and not exists(f"orders/{o}/style/try_art.json") and not exists(f"orders/{o}/style/art.lock"), (e_busy, exe.calls))
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), mock.patch.object(L, "time_left", lambda default=L.BUDGET: 6.0):
    e_time = raises(lambda: SP.advance(mkctx(o, arrival_left=20.0)), store.Answer)
check("a refusal with little time left on an invocation that had already used its time is still BUSY (503 busy_retry), not a hold: nothing counted, nothing claimed",
      isinstance(e_time, store.Answer) and e_time.body["reason"] == "busy_retry" and exe.calls == 0 and not exists(f"orders/{o}/style/try_art.json")
      and not exists(f"orders/{o}/style/art.lock"), e_time)

# IE5: deterministic refusals: a plan that can never fit is a HOLD with no busy hop
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), mock.patch.dict(os.environ, {"STYLE_SLOW_CPU": "6"}):
    why = hold_of(lambda: SP.advance(mkctx(o, dict(SPEC1, style="solo.powder"))))
check("IE5: a plan whose need passes the work budget at the slow factor in force (Powder Burst at 6.0) is held style_step_too_big, before any guard, claim or record: "
      "the executor never ran, no try record, no claim",
      why == "style_step_too_big" and exe.calls == 0 and not exists(f"orders/{o}/style/try_art.json") and not exists(f"orders/{o}/style/art.lock"), (why, exe.calls))
o = fresh_order()
with mock.patch.dict(SP.EXECUTORS, {"art": Exe()}), mock.patch.object(CO, "MEM_BUDGET_MB", 300):
    why_mem = hold_of(lambda: SP.advance(mkctx(o)))
check("IE5: a plan whose memory estimate passes the memory budget is held the same way", why_mem == "style_step_too_big", why_mem)
o = fresh_order()
with mock.patch.dict(SP.EXECUTORS, {"art": Exe()}), mock.patch.object(L, "time_left", lambda default=L.BUDGET: 6.0):
    why_fresh = hold_of(lambda: SP.advance(mkctx(o, arrival_left=52.0)))
check("IE5: a FRESH invocation (all its time on arrival) that still cannot fit the step is a configuration error: held, not retried as busy", why_fresh == "style_step_too_big", why_fresh)
o2 = fresh_order()
cost_gap = SP.make_plan(SPEC1, [None])
cost_gap = dict(cost_gap, cost_key="singles.nonesuch", plan8="00000000")
SP.create_plan(mkctx(o2))
store.put(f"orders/{o2}/style/plan.json", store.json_bytes(dict(cost_gap, created_at=1)), "application/json", upsert=True)
with mock.patch.dict(SP.EXECUTORS, {"art": Exe()}):
    why_cost = hold_of(lambda: SP.advance(mkctx(o2)))
check("a plan whose design has no row in the cost table is held style_not_priced after payment (a style the table cannot price is not made blind)", why_cost == "style_not_priced", why_cost)

# no room (the guards are full): 503 room_retry whose retry_after is the holder's remaining estimate between ROOM_MIN_S and ROOM_MAX_S, and the chain waits that long
room_bounds = [(eta, SP._room(GD.Busy("cpu", "", eta)).retry_after) for eta in (None, float("nan"), 0.0, 0.2, 5.0, 16.3, 28.0, 500.0)]
check("the back-off of a refusal for room: the holder's remaining estimate rounded up, never under ROOM_MIN_S (5 s) nor over ROOM_MAX_S (the longest back-off of a chain, 40 s), "
      "ROOM_DEFAULT_S (10 s) when the holder declared none or the number is nonsense",
      [r for _, r in room_bounds] == [10, 10, 5, 5, 5, 17, 28, 40] and (SP.ROOM_MIN_S, SP.ROOM_MAX_S, SP.ROOM_DEFAULT_S) == (5, DU.WAIT_MAX_S, 10), room_bounds)
a_room = SP._room(GD.Busy("memory", "", 16.3))
d_room = M._answer(a_room)
d_room0 = M._answer(store.Answer(503, "room_retry", "x", True))
check("the chain answers a refusal for room with a pause of that length and counts ONE busy hop (decision next, delay 17, counts, room_retry); an answer with no retry_after still pauses "
      "(10 s), and the answer names the guard that refused",
      a_room.status == 503 and a_room.body["reason"] == "room_retry" and a_room.body["retry"] is True and a_room.body["retry_after"] == 17 and a_room.body["room"] == "memory"
      and d_room == ("next", 17, True, "room_retry") and d_room0 == ("next", 10, True, "room_retry"), (a_room.body, d_room, d_room0))

# plate faults (IE8, after payment) and identical exceptions
o = fresh_order()
exe = Exe(["plate", "plate"])
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    e_p1 = raises(lambda: SP.advance(mkctx(o)), store.Answer)
    t1 = steps_of(o)["try"]
    decision = M._answer(e_p1) if isinstance(e_p1, store.Answer) else None
    why_p2 = hold_of(lambda: SP.advance(mkctx(o)))
t2 = steps_of(o)["try"]
check("IE8: the first plate fault is counted in try_art.json (kind plate) and answered 503 plate_retry; the chain waits and does NOT count a busy hop; the second plate fault holds "
      "the order (plate_unavailable), the plate named",
      isinstance(e_p1, store.Answer) and e_p1.body["reason"] == "plate_retry" and t1["plate"] == 1 and decision is not None and decision[0] == "next" and decision[2] is False
      and decision[3] == "plate_retry" and why_p2 == "plate_unavailable" and t2["plate"] == 2 and t2["plate_id"] == "P-SN-CLOUD__stand_in" and t2["open"] is False
      and not exists(f"orders/{o}/style/done_art.json"), (e_p1, decision, why_p2, t2))
o = fresh_order()
exe = Exe(["exc", "exc"])
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    e_x1 = raises(lambda: SP.advance(mkctx(o)), RuntimeError)
    tx1 = steps_of(o)["try"]
    why_x2 = hold_of(lambda: SP.advance(mkctx(o)))
check("a deterministic exception is raised as it is the first time (the chain's own error note, one more retry) and noted by its signature; the SECOND identical one holds the order "
      "(style_step_failed)", isinstance(e_x1, RuntimeError) and len(tx1["errors"]) == 1 and tx1["open"] is False and why_x2 == "style_step_failed", (e_x1, tx1, why_x2))
o = fresh_order()
exe = Exe(["exc", "exc2", "ok"])
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    raises(lambda: SP.advance(mkctx(o)), RuntimeError)
    raises(lambda: SP.advance(mkctx(o)), ValueError)
    got = SP.advance(mkctx(o))
check("two DIFFERENT exceptions do not hold (only an identical repeat is deterministic): the third call, healthy, makes the artwork", got["final"] and exe.calls == 3, exe.calls)

# engine_skew
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    SP.create_plan(mkctx(o))
    with mock.patch.object(SP, "ENGINE_V", ST.ENGINE_V + 1):
        why_skew = hold_of(lambda: SP.advance(mkctx(o)))
    got_ok = SP.advance(mkctx(o))
check("ENGINE_V: a plan made under another engine version holds the order (engine_skew) and renders nothing; under its own version it runs",
      why_skew == "engine_skew" and got_ok["final"] and exe.calls == 1, (why_skew, exe.calls))
o = fresh_order()
leg_plan = SP.make_plan({"style": "studio_black", "eyes": 1, "layout": "galaxy"}, [None])
check("a legacy plan carries no engine version and is never held for skew", leg_plan["engine_v"] == 0 and SP.check_skew(leg_plan) is None, leg_plan["engine_v"])

# an unrelated registry edit leaves the digest of an unfinished order alone
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    plan_before = SP.create_plan(mkctx(o))
    key_before = SP.artwork_key(o, plan_before, 0)
    with mock.patch.object(CT, "registry_hash", lambda: "aaaaaaaaaaaa"), mock.patch.dict(CT.STYLES["solo.gold"], {"stage": "preview", "name": "Renamed"}):
        got = SP.advance(mkctx(o))
check("IE3: an unrelated registry edit between payment and master (a stage, a name, a new registry hash) leaves the artwork's digest and file name unchanged",
      got["artwork"]["key"] == key_before and got["plan8"] == plan_before["plan8"], (key_before, got["artwork"]["key"]))

# two callers at once: 409 rendering for the second, one render, the second then finds it done
o = fresh_order()
release = threading.Event()
exe = Exe(block=release)
res_a = {}


def caller_a():
    try:
        res_a["got"] = SP.advance(mkctx(o))
    except BaseException as e:  # noqa: BLE001
        res_a["err"] = e


with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    ta = threading.Thread(target=caller_a)
    ta.start()
    exe.entered.wait(10)
    e_roll = raises(lambda: SP.advance(mkctx(o)), store.Answer)          # in this process the guard answers first: room_retry
    with mock.patch.object(GD, "slot", lambda **kw: contextlib.nullcontext()):
        e_claim = raises(lambda: SP.advance(mkctx(o)), store.Answer)     # another process: the claim answers 409 rendering
    lock_up = exists(f"orders/{o}/style/art.lock")
    release.set()
    ta.join(30)
    done_b = SP.advance(mkctx(o))
check("two callers at once: in one process the guard turns the second away (503 room_retry), in another process the claim does (409 rendering, retry_after); "
      "exactly one render happens and the second caller then finds it done",
      isinstance(e_roll, store.Answer) and e_roll.body["reason"] == "room_retry" and isinstance(e_claim, store.Answer) and e_claim.status == 409
      and e_claim.body["reason"] == "rendering" and e_claim.body.get("retry_after", 0) >= 5 and lock_up and "got" in res_a and exe.calls == 1
      and done_b["ran"] == [] and done_b["artwork"]["key"] == res_a["got"]["artwork"]["key"], (e_roll, e_claim, res_a, exe.calls))

# rerun and recompose of a v3 plan
o = fresh_order()
exe = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe}):
    f0 = SP.advance(mkctx(o))
    same = SP.advance(mkctx(o, finish=False), "recompose")
    wj(f"orders/{o}/eye_1.json", {"created": "2026-10-06T00:00:00Z", "bytes": 5, "eye_id": "ab" * 8})        # an eye was re-rendered (a new master)
    new = SP.advance(mkctx(o, finish=False), "recompose")
    again_new = SP.advance(mkctx(o, finish=False), "recompose")
    forced = SP.advance(mkctx(o, finish=False), "rerun")
s = steps_of(o)
check("recompose: the same file when no input changed (nothing rendered); a NEW file beside it when a master was re-rendered (the digest is salted with the rerun count, the delivered file "
      "is never deleted); asked again with nothing new it is the same new file; rerun draws again whatever changed",
      same["artwork"]["key"] == f0["artwork"]["key"] and same["ran"] == [] and new["ran"] == ["art"] and new["artwork"]["key"] != f0["artwork"]["key"]
      and again_new["ran"] == [] and again_new["artwork"]["key"] == new["artwork"]["key"] and forced["ran"] == ["art"] and forced["artwork"]["key"] not in (f0["artwork"]["key"], new["artwork"]["key"])
      and store.exists(f0["artwork"]["key"]) and s["rerun"]["n"] == 2 and exists(f"orders/{o}/style/done_art_r1.json") and exists(f"orders/{o}/style/try_art_r2.json"), (s["rerun"], f0["artwork"]["key"], new["artwork"]["key"]))
o = fresh_order()
leg = []


def fake_leg(body):
    leg.append(body["style"])
    return fake_legacy_compose(body)


with mock.patch.dict(os.environ, {"X": "1"}):
    lctx = mkctx(o, {"eyes": 1, "style": "studio_black", "layout": "galaxy", "names": "Ona", "title": ""}, legacy=fake_leg)
    store.put(f"orders/{o}/eye_1.jpg", b"x", "image/jpeg", upsert=True)
    store.put(f"orders/{o}/eye_1.json", store.json_bytes({"created": "c", "bytes": 1}), "application/json", upsert=True)
    l1 = SP.advance(lctx)
    l2 = SP.advance(mkctx(o, {"eyes": 1, "style": "studio_black", "layout": "galaxy", "names": "Ona", "title": ""}, legacy=fake_leg, finish=False), "recompose")
    e_rr = raises(lambda: SP.advance(mkctx(o, {"eyes": 1, "style": "studio_black", "layout": "galaxy", "names": "Ona", "title": ""}, legacy=fake_leg, finish=False), "rerun"), store.Answer)
check("a legacy order: one art step through the same runner, its file is the legacy composer's own digest; recompose asks that composer again (it answers the same file when nothing changed); "
      "rerun is refused (409 rerun_not_available): a salted digest would not exist for it",
      l1["final"] and l1["artwork"]["key"] == l2["artwork"]["key"] and len(leg) == 2 and isinstance(e_rr, store.Answer) and e_rr.body["reason"] == "rerun_not_available"
      and steps_of(o)["plan"]["family"] == "legacy", (l1["artwork"]["key"], l2["artwork"]["key"], leg, e_rr))

# eight eyes: a plan the stand in family draws; the memory of twelve renders in one process
class FakeFam:
    """A stand in for an engine family that is not built yet (collision): its resolve and preview, a transient allocation per render."""
    junk_mb = 0
    sizes = []
    selfcheck = None

    @staticmethod
    def resolve(spec, profiles=None):
        e = CT.engine_for(spec["style"], spec["eyes"])
        return {"family": "collision", "style": spec["style"], "design_used": e["design"], "fallback": None, "layout": spec["layout"], "canvas": "3:2", "clean": False,
                "seed_key": {"style": spec["style"], "pv": CT.PLATES_VERSION}, "seed_from": "eye_id", "plates": None, "steps": ["art"]}

    @staticmethod
    def preview(eyes, spec, size=1024, check=False, watermark=False):
        if FakeFam.junk_mb:
            junk = np.ones((FakeFam.junk_mb * 1048576,), np.uint8) + 1
            del junk
        FakeFam.sizes.append((len(eyes), [e.src.size for e in eyes][:1]))
        img = Image.new("RGB", (192, 128), (30 + len(eyes), 40, 50))
        return ST.Preview(img=img, discs=[(10, 10, 5)], graded=[np.zeros((16, 16, 3), np.uint8) + 100 for _ in eyes], design=CT.engine_for(spec["style"], spec["eyes"])["design"],
                          fmt="3:2", size=size, seed=777, cls="own", log={"eyes": len(eyes)}, times={"total": 0.01}, selfcheck=FakeFam.selfcheck)


FakeFam.__name__ = "_lib.styles.collision"
sys.modules["_lib.styles.collision"] = FakeFam
CT.ENGINES_BUILT_EXTRA.add("collision")


def small_masters(order, n, side=256):
    for i in range(1, n + 1):
        b = io.BytesIO()
        SI.make(kind="blue", seed=20 + i, side=side).convert("RGB").save(b, "JPEG", quality=92)
        store.put(f"orders/{order}/eye_{i}.jpg", b.getvalue(), "image/jpeg", upsert=True)
        store.put(f"orders/{order}/eye_{i}.json", store.json_bytes({"created": f"t{i}", "bytes": len(b.getvalue()), "eye_id": f"{i:02x}" * 8}), "application/json", upsert=True)


o8 = fresh_order("e8")
small_masters(o8, 8)
spec8 = {"eyes": 8, "style": "grp.collision", "layout": "ring", "names": "", "title": ""}
t0 = time.time()
g8 = SP.advance(mkctx(o8, spec8))
p8 = steps_of(o8)["plan"]
check("an 8 eye synthetic plan (the stand in family): one art step for eight eyes, work side 2048 (the registry's cap for families), the need from the cost table "
      f"({p8['steps'][0]['need_s']} s of {CO.WORK_BUDGET_S:.0f}), eight masters loaded, one artwork",
      g8["final"] and p8["steps"][0]["eyes"] == list(range(1, 9)) and p8["work_side"] == 2048 and p8["design_used"] == "family" and FakeFam.sizes[-1][0] == 8
      and p8["steps"][0]["need_s"] < CO.WORK_BUDGET_S and g8["artwork"]["count"] == 8 and g8["artwork"]["style"] == "grp.collision", (p8, FakeFam.sizes[-1:]))
FakeFam.junk_mb = 150
o12 = fresh_order("m12")
small_masters(o12, 2)
spec12 = {"eyes": 2, "style": "duo.kiss_collision", "layout": "pair", "names": "", "title": ""}
growth = []
for i in range(12):
    ctx12 = mkctx(o12, spec12, finish=False)
    SP.advance(ctx12, "rerun" if i else "next")
    if i == 2:
        base_rss, _ = GD.memory_now()
    if i == 11:
        end_rss, _ = GD.memory_now()
FakeFam.junk_mb = 0
check("IE6: twelve renders of different digests in one process (150 MB of transient memory each): the resident size after the third grows by at most 60 MB by the twelfth "
      "(a failed or finished render drops its arrays; both guards are free)",
      base_rss is None or end_rss - base_rss <= 60, (base_rss, end_rss))
check("... and the guards are free again after all of them", GD.state() == {"mb": 0.0, "heavy": 0, "running": 0}, GD.state())

# a failed self check or a measured colour failure stores the artwork and holds it for the owner's look (needs_review), as a check always did; a colour check that
# merely could not measure is no verdict
o_sc = fresh_order("sc")
small_masters(o_sc, 2)
FakeFam.selfcheck = {"ok": False, "checks": {"t1": {"ok": False, "bad": 3}}, "ms": 1}
got_sc = SP.advance(mkctx(o_sc, spec12, finish=False))
FakeFam.selfcheck = None
art_sc = rj(got_sc["artwork"]["key"][:-4] + ".json")
check("a self check that failed (T1 here) stores the artwork with needs_review and the numbers of the check in its record: held for the owner's look, never delivered silently",
      got_sc["artwork"]["needs_review"] is True and art_sc["needs_review"] is True and art_sc["selfcheck"]["ok"] is False and art_sc["selfcheck"]["checks"]["t1"]["bad"] == 3, art_sc)
o_qa = fresh_order("qa")
small_masters(o_qa, 2)
with mock.patch.object(L, "colour_qa", lambda *a, **k: {"ok": False, "pupil_neutral": False, "ring_de00": None}):
    got_qa = SP.advance(mkctx(o_qa, spec12, finish=False))
o_qn = fresh_order("qn")
small_masters(o_qn, 2)
with mock.patch.object(L, "colour_qa", lambda *a, **k: {"ok": False, "pupil_neutral": None, "ring_de00": None}):
    got_qn = SP.advance(mkctx(o_qn, spec12, finish=False))
check("a measured colour failure (the pupil core is not neutral) holds the artwork for review; a colour check that could not measure anything (no verdict) does not, as master_compose never counted it",
      got_qa["artwork"]["needs_review"] is True and got_qn["artwork"]["needs_review"] is False, (got_qa["artwork"]["needs_review"], got_qn["artwork"]["needs_review"]))
o_er = fresh_order("er")
small_masters(o_er, 2)
wj(f"orders/{o_er}/eye_1.json", {"created": "t1", "bytes": 5, "eye_id": "01" * 8, "qa": {"ok": False}})        # an eye master that failed its own colour check
got_er = SP.advance(mkctx(o_er, spec12, finish=False))
check("an eye master that failed its own check (needs_review in its record) holds the artwork made from it, as master_compose did", got_er["artwork"]["needs_review"] is True, got_er["artwork"])

# two orders at once: the second is turned away (503 busy_retry) while the first draws, then makes its own artwork
oA, oB = fresh_order("ta"), fresh_order("tb")
release2 = threading.Event()
exA, exB = Exe(block=release2), Exe()
route = lambda ctx, plan, step, rerun: (exA if ctx.order == oA else exB)(ctx, plan, step, rerun)
res_ab = {}


def caller_ab():
    try:
        res_ab["a"] = SP.advance(mkctx(oA))
    except BaseException as e:  # noqa: BLE001
        res_ab["err"] = e


with mock.patch.dict(SP.EXECUTORS, {"art": route}), mock.patch.object(GD, "WAIT_S", 0.3):
    tab = threading.Thread(target=caller_ab)
    tab.start()
    exA.entered.wait(10)
    e_b1 = raises(lambda: SP.advance(mkctx(oB)), store.Answer)
    release2.set()
    tab.join(30)
    got_b = SP.advance(mkctx(oB))
check("I11: two orders at once on one instance: the second order's step is turned away with 503 room_retry while the first draws (one heavy render at a time), nothing of it is counted, "
      "and it makes its own artwork as soon as the first has let go; the two artworks are two files",
      isinstance(e_b1, store.Answer) and e_b1.body["reason"] == "room_retry" and "a" in res_ab and exA.calls == 1 and exB.calls == 1
      and got_b["artwork"]["key"] != res_ab["a"]["artwork"]["key"] and steps_of(oB)["try"]["kills"] == 0, (e_b1, res_ab, exA.calls, exB.calls))

# the 4K plates a plan will draw from (the family that knows them before the render: the seed from eye_id, WP5B and the families after it)
from _lib.styles import plates as PLT  # noqa: E402
ids4k = [i for i in PLT.ids("P-SN-CLOUD") if PLT.record(i)["k4"]][:2]
real_resolve = ST.resolve
with mock.patch.object(ST, "resolve", lambda spec, profiles=None: dict(real_resolve(spec, profiles), plates=ids4k)):
    p_pl = SP.make_plan({"style": "solo.powder", "eyes": 1, "layout": "single"}, eyes1)
p_nopl = SP.make_plan({"style": "solo.powder", "eyes": 1, "layout": "single"}, [{"eye_id": None, "profile": None}])
check("a plan that knows its plates carries plates_needed (id, family, storage path, sha256 and size of every 4K file: checkout verifies each exists before the customer pays) and the plates "
      "are part of plan8; a plan whose eye has no id cannot make the seed, so it does not know them yet and has none, and the family is named in plate_families",
      p_pl["plates"] == ids4k and p_pl["plates_needed"] == PLT.needed(ids4k) and len(ids4k) == 2 and all(re.fullmatch(r"[0-9a-f]{64}", x["sha256"]) and x["path"].startswith("plates/v1/")
                                                                                                    for x in p_pl["plates_needed"]) and p_pl["plan8"] != p_nopl["plan8"]
      and p_nopl["plates"] is None and "plates_needed" not in p_nopl and p_nopl["plate_families"] == ["P-SN-CLOUD"], (p_pl.get("plates_needed"), p_nopl["plate_families"]))

# step B of the seed change (WP5B): the plan carries the seed, the plates and what it freezes, from the eye ids and the sealed profile
from _lib.styles import seeds as SD  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402
IDA, IDB = "0123456789abcdef", "fedcba9876543210"
p_a = SP.make_plan({"style": "solo.powder", "eyes": 1, "layout": "single"}, [{"eye_id": IDA, "profile": None}])
p_a2 = SP.make_plan({"style": "solo.powder", "eyes": 1, "layout": "single"}, [{"eye_id": IDA, "profile": None}])
p_b = SP.make_plan({"style": "solo.powder", "eyes": 1, "layout": "single"}, [{"eye_id": IDB, "profile": None}])
check("a plan of Powder Burst made from an eye id knows its seed (sha256 of the eye id and the seed key, seeds.py), its one cloud plate and the 4K plate it needs; the same eye gives the same plan "
      "(plan8 too), another eye another seed and another plan8; nothing but the eye and the style decides it",
      p_a["seed"] == str(SD.seed_for_key([IDA], p_a["seed_key"])) and p_a["seed_from"] == "eye_id" and len(p_a["plates"]) == 1 and p_a["plates"][0].startswith("P-SN-CLOUD")
      and p_a["plates_needed"] == PLT.needed(p_a["plates"]) and p_a["frozen"] == {} and p_a["plan8"] == p_a2["plan8"] and p_a["plan8"] != p_b["plan8"] and p_a["seed"] != p_b["seed"]
      and p_a["eye_ids"] == [IDA], (p_a["seed"], p_a["plates"], p_b["plates"]))
prof_blue = EYE.profile_of_bytes(SI.png_bytes("blue_round"), rules=("lid",))
p_s = SP.make_plan({"style": "solo.splash", "eyes": 1, "layout": "single"}, [{"eye_id": prof_blue.eye_id, "profile": prof_blue.rec}])
p_s0 = SP.make_plan({"style": "solo.splash", "eyes": 1, "layout": "single"}, [{"eye_id": prof_blue.eye_id, "profile": None}])
check("a plan of a Splash made from the eye id and the draft's sealed profile freezes the liquid, names its crown plate and the 4K file it needs (and the frozen liquid is part of plan8); with no profile "
      "it knows its seed but not its plate: plates None, nothing frozen, no plates_needed, the family named in plate_families",
      p_s["frozen"].get("liquid") and len(p_s["plates"]) == 1 and PLT.record(p_s["plates"][0])["variables"]["liquid"] == p_s["frozen"]["liquid"] and p_s["plates_needed"] == PLT.needed(p_s["plates"])
      and p_s0["plates"] is None and p_s0["frozen"] == {} and "plates_needed" not in p_s0 and p_s0["seed"] == p_s["seed"] and p_s0["plate_families"] == ["P-SP-CROWN"]
      and p_s0["plan8"] != p_s["plan8"], (p_s["frozen"], p_s["plates"], p_s0["plates"]))
p_clean0 = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, [{"eye_id": IDA, "profile": None}])
p_leg0 = SP.make_plan({"style": "studio_black", "eyes": 1, "layout": "single"}, [{"eye_id": IDA, "profile": None}])
check("a style that draws no plate has its seed and no plate to name (plates None: no plates_needed); a plan of the legacy engine has none of it (it is drawn by the old composer)",
      p_clean0["seed"] == str(SD.seed_for_key([IDA], p_clean0["seed_key"])) and p_clean0["plates"] is None and p_clean0["frozen"] == {} and "plates_needed" not in p_clean0
      and "seed" not in p_leg0 and "frozen" not in p_leg0, (p_clean0["plates"], p_leg0.get("seed")))
with mock.patch.object(ST, "resolve", side_effect=PLT.NoPlate("no plate for P-SN-CLOUD {}")):
    e_np = raises(lambda: SP.make_plan({"style": "solo.powder", "eyes": 1, "layout": "single"}, [{"eye_id": IDA, "profile": None}]), SP.Hold)
check("a plate library with no plate for the style at the plan's version is a hold (no_engine), not a crash at checkout", isinstance(e_np, SP.Hold) and e_np.reason == "no_engine", e_np)


class FakePv:
    def __init__(self, seed, plates):
        self.seed, self.log = seed, {"plates": plates}


e_s = raises(lambda: SP._check_drawn(p_a, FakePv(1, p_a["plates"])), SP.Hold)
e_p = raises(lambda: SP._check_drawn(p_a, FakePv(int(p_a["seed"]), ["P-SN-CLOUD__other"])), SP.Hold)
check("the picture is checked against the plan before anything is stored: the drawn seed and plates equal the plan's (nothing raised), another seed or other plates is a hold picture_drift, and a plan "
      "that names no plates is not checked for them (a splash with no profile, an old plan)",
      SP._check_drawn(p_a, FakePv(int(p_a["seed"]), p_a["plates"])) is None and isinstance(e_s, SP.Hold) and e_s.reason == "picture_drift" and isinstance(e_p, SP.Hold) and e_p.reason == "picture_drift"
      and SP._check_drawn(p_s0, FakePv(int(p_s0["seed"]), ["P-SP-CROWN__x"])) is None and SP._check_drawn({}, FakePv(5, [])) is None, (e_s, e_p))
check("the two new holds have their words for the owner's reminder (why it waits, what to do)", all(SP.hold_text(r, "261005-x") for r in ("eye_changed", "picture_drift")), "")


# ============================================================================================ 6. a paid order of the legacy engine through the chain
section("6. a paid order of the LEGACY engine through the chain (I3): one art step, the composer's own digest")
SPEC_STYLES = {}
MODE.update(side=256, kind="blue", delay=0.0)
MC.master_compose = fake_legacy_compose
n0 = len(H.Fake.emails)
o6, k6, sid6 = new_order(2, "studio_black", "leo@example.com")
done6 = wait_for(lambda: stopped(o6, "ready"), 60)
s6 = steps_of(o6)
dl6 = rj(f"orders/{o6}/delivery.json") or {}
check("a legacy order made by the server: ready, one 'ready' email, the plan is a legacy plan with one art step, its done record names the delivered file, the composer ran once",
      bool(done6) and s6["plan"]["family"] == "legacy" and [x["name"] for x in s6["plan"]["steps"]] == ["art"] and s6["done"]["result"]["key"] == dl6.get("key")
      and LEGACY_COMPOSES.count(o6) == 1 and len(mails("leo@example.com", READY_EN, n0)) == 1 and s6["try"]["kills"] == 0 and s6["try"]["open"] is False,
      (done6, s6["plan"] and s6["plan"]["family"], dl6, LEGACY_COMPOSES))
check("delivery.json of a legacy order is what it always was: no plan8, no design (the file's own digest names it); no claim is left on the folder",
      "plan8" not in dl6 and "design_used" not in dl6 and sorted(dl6) == ["bytes", "count", "created", "created_at", "height", "key", "layout", "needs_review", "style", "width"]
      and not exists(f"orders/{o6}/compose.lock") and not exists(f"orders/{o6}/style/art.lock") and not exists(f"orders/{o6}/advance.lock"), (sorted(dl6)))
c, j = get(f"/api/order?o={o6}&k={k6}")
check("the order page opened afterwards: ready with a download, no artwork progress block", c == 200 and j["state"] == "ready" and j.get("download", {}).get("url") and "artwork" not in j, j)

MC.master_compose = REAL_MC
MODE.update(side=4096)
t0 = time.time()
o6b, k6b, _ = new_order(1, "studio_black", "ria@example.com")
done6b = wait_for(lambda: stopped(o6b, "ready"), 240)
dl6b = rj(f"orders/{o6b}/delivery.json") or {}
rec_eye = rj(f"orders/{o6b}/eye_1.json")
paid6b = rj(f"orders/{o6b}/paid.json")["spec"]
ident = {"keys": [f"orders/{o6b}/eye_1.jpg"], "style": paid6b["style"], "layout": paid6b["layout"], "names": paid6b["names"], "title": paid6b["title"], "size": 4096,
         "eyes": [MC._identity(rec_eye)]}
want = f"orders/{o6b}/artwork_{hashlib.sha256(json.dumps(ident, sort_keys=True, ensure_ascii=True).encode()).hexdigest()[:16]}.jpg"
again_real = REAL_MC({"order": o6b, "ticket": L.mint_ticket(store.unlock_kind(o6b), 300), "keys": ident["keys"], "style": ident["style"], "layout": ident["layout"],
                      "names": ident["names"], "title": ident["title"]}) if done6b else {}
check("I3: the REAL legacy composer through the step runner: the delivered file is exactly the one the old digest rule names (sha256 of keys, style, layout, names, title, size and "
      "each master's identity), and asking the composer again answers the same stored file",
      bool(done6b) and dl6b.get("key") == want and again_real.get("key") == want and again_real.get("existing") is True and dl6b.get("width") == 4096
      and steps_of(o6b)["done"]["result"]["key"] == want, (done6b, dl6b.get("key"), want, again_real.get("key")))
MC.master_compose = fake_legacy_compose

# ============================================================================================ 7. a paid order of a v3 style
section("7. a paid order of a v3 style through the chain, the page's compose, the status progress, a plan of several steps, eight eyes")
MODE.update(side=4096, kind="blue", delay=0.0)
n0 = len(H.Fake.emails)
seen_server = []
with Show("solo.clean"):
    o7, k7, sid7 = new_order(1, "solo.clean", "vera@example.com")
t_start = time.time()
while time.time() - t_start < 120 and not stopped(o7):
    c, j = get(f"/api/order?o={o7}&k={k7}")
    if c == 200 and isinstance(j.get("server"), dict) and j["server"].get("step") == "compose":
        seen_server.append((j["server"].get("part"), j["server"].get("of"), j.get("artwork")))
    time.sleep(0.4)
done7 = stopped(o7, "ready")
s7 = steps_of(o7)
dl7 = rj(f"orders/{o7}/delivery.json") or {}
art7 = rj(dl7.get("key", "x/x")[:-4] + ".json") or {} if dl7 else {}
check("a style of the v3 engine, paid and made by the server: ready, one ready email, plan and done records, the artwork is named by sha256(plan8, rerun), delivery.json names the design and the plan",
      bool(done7) and s7["plan"]["family"] == "singles" and s7["plan"]["design_used"] == "clean" and dl7.get("design_used") == "clean" and dl7.get("plan8") == s7["plan"]["plan8"]
      and dl7["key"] == SP.artwork_key(o7, s7["plan"], 0) and s7["done"]["result"]["key"] == dl7["key"] and len(mails("vera@example.com", READY_EN, n0)) == 1
      and s7["try"]["kills"] == 0 and not s7["lock"] and not exists(f"orders/{o7}/compose.lock"), (done7, dl7, s7["plan"] and s7["plan"]["plan8"]))
im = Image.open(local(dl7["key"])) if dl7 else None
check("the file is one JPEG, 4096 x 4096, 4:4:4 (no chroma subsampling), with the sRGB profile embedded: the stored format of every deliverable",
      im is not None and im.format == "JPEG" and im.size == (4096, 4096) and __import__("PIL.JpegImagePlugin", fromlist=["x"]).get_sampling(im) == 0 and bool(im.info.get("icc_profile")), im and (im.format, im.size))
rec_parts = [("selfcheck ok", (art7.get("selfcheck") or {}).get("ok") is True), ("pupil neutral", ((art7.get("qa") or {}).get("eyes") or [{}])[0].get("pupil_neutral") is True),
             ("seed text", isinstance(art7.get("seed"), str)), ("plan8", art7.get("plan8") == s7["plan"]["plan8"]), ("engine_v", art7.get("engine_v") == ST.ENGINE_V),
             ("reg", bool(re.fullmatch(r"[0-9a-f]{12}", str(art7.get("reg"))))), ("design", art7.get("design_used") == "clean"), ("times", "times" in art7),
             ("not held", art7.get("needs_review") is False), ("inputs", isinstance(art7.get("inputs"), dict)), ("rerun 0", art7.get("rerun") == 0),
             ("seed is the plan's", s7["plan"].get("seed") is not None and art7.get("seed") == s7["plan"]["seed"]
              and s7["plan"]["seed"] == str(SD.seed_for_key(s7["plan"]["eye_ids"], s7["plan"]["seed_key"])))]
check("its record holds what the owner reads: the colour check per eye, the self checks (T1 to T12 ok), the seed as text, the plan and engine versions, the registry hash, "
      "the times, the drift, the inputs and the design", all(ok for _, ok in rec_parts), [n for n, ok in rec_parts if not ok])
check("while the server composed, the status told the page which step ran: step compose, part 1 of 1, and the artwork progress",
      any(p == 1 and o_ == 1 for p, o_, a in seen_server), seen_server[:4])
ev7 = [f for k, f in EVENTS if k == "master" and f.get("order") == o7 and f.get("step") == "art"]
check("the real engine's step event: step art, 4096 px time and CPU, a memory increase of the right order (a 4096 px master takes hundreds of MB), the plan's need above the real time",
      len(ev7) == 1 and ev7[0]["ms"] > 500 and (ev7[0].get("peak_mb") is None or ev7[0]["peak_mb"] > 100) and ev7[0]["need_s"] > ev7[0]["ms"] / 1000.0, ev7)
d7 = s7["done"]
check("its done record says what the 4096 px step really took against what the cost table planned (VE1's numbers for this machine)",
      d7["ms"] > 500 and d7["need_s"] > 10 and d7["est_mb"] > 300 and d7["by"] == "server" and d7["drift"] == [None], {k: d7[k] for k in ("ms", "cpu_s", "peak_mb", "hwm_mb", "need_s", "est_mb", "by", "drift")})

# the page's own compose (page mode: the texts say the page starts it), and the status progress before anything is made
H.Fake.legal = PACK
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
M._KICKED.clear()
MODE.update(side=256)
with Show("solo.clean"):
    o7p, k7p, sid7p = new_order(1, "solo.clean", "pia@example.com")
time.sleep(1.0)
c, j = get(f"/api/order?o={o7p}&k={k7p}")
check("a paid order nobody has started: state paid, and the status carries the artwork's progress, 0 of 1, next step art", c == 200 and j["state"] == "paid"
      and j.get("artwork") == {"done": 0, "of": 1, "step": "art"}, j)
c, j = post("/api/order", {"action": "make", "order": o7p, "k": k7p, "eye": 1})
c2, j2 = get(f"/api/order?o={o7p}&k={k7p}")
check("... after the eye is made and before the artwork: still 0 of 1", c == 200 and j2.get("artwork") == {"done": 0, "of": 1, "step": "art"} and j2["state"] == "making", (c, j2))
wait_for(lambda: stopped(o7p, "ready"), 90)          # (the page's make asked the server to go on with the rest: let it finish before the next test)
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)

# a plan of two steps: the page's compose answers 'making' with the progress, the chain goes on without a busy count
class Prep:
    def __init__(self):
        self.calls = 0

    def __call__(self, ctx, plan, step, rerun):
        self.calls += 1
        time.sleep(0.5)
        store.put(SP.path(ctx.order, "prep_1.json"), b"{}", "application/json", upsert=True)
        return SP.Out({"key": None}, [{"path": SP.path(ctx.order, "prep_1.json"), "bytes": 2, "sha12": None}], inputs={})


def two_step_plan(order_spec_style="solo.clean"):
    plan = SP.make_plan({"style": order_spec_style, "eyes": 1, "layout": "single"}, [None])
    plan["steps"] = [{"name": "prep", "kind": "prep", "eyes": [1], "need_s": 5.0, "est_mb": 100}, {"name": "art", "kind": "art", "eyes": [1], "need_s": 10.0, "est_mb": 200}]
    plan["plan8"] = SP.plan8(plan)
    return dict(plan, created_at=int(time.time()))


prep, exe = Prep(), Exe()
seen_parts = []
with mock.patch.dict(SP.EXECUTORS, {"prep": prep, "art": exe}):
    with Show("solo.clean"):
        o7s, k7s, sid7s = new_order(1, "solo.clean", "sam@example.com", pay_it=False)
    wj(f"orders/{o7s}/style/plan.json", two_step_plan())
    M.MAX_BUSY, keep_busy = 0, M.MAX_BUSY
    n0 = len(H.Fake.emails)
    hook(H.pay_session(sid7s, email="sam@example.com"))
    t_start = time.time()
    while time.time() - t_start < 60 and not stopped(o7s):
        b = rj(f"orders/{o7s}/advance.json") or {}
        if b.get("state") == "working" and b.get("step") == "compose":
            seen_parts.append((b.get("part"), b.get("of")))
        time.sleep(0.1)
    M.MAX_BUSY = keep_busy
done7s = stopped(o7s, "ready")
s7s = steps_of(o7s)
check("a plan of two steps made by the server: both done records, the artwork delivered after the second, the chain asked for the second step WITHOUT a busy count (MAX_BUSY was 0), "
      "advance.json named the steps (part 1 of 2, part 2 of 2), one ready email",
      bool(done7s) and exists(f"orders/{o7s}/style/done_prep.json") and exists(f"orders/{o7s}/style/done_art.json") and prep.calls == 1 and exe.calls == 1
      and (1, 2) in seen_parts and (2, 2) in seen_parts and len(mails("sam@example.com", READY_EN, n0)) == 1 and exists(f"orders/{o7s}/delivery.json"), (done7s, seen_parts, prep.calls, exe.calls))

# withdrawn in the middle of the chain: the order is withdrawn while step 1 of 2 draws; the chain stops at its next hop, the second step is never drawn, no email goes
class PrepWithdrawn(Prep):
    def __call__(self, ctx, plan, step, rerun):
        out = Prep.__call__(self, ctx, plan, step, rerun)
        store.put(f"orders/{ctx.order}/withdrawn.json", b"{}", "application/json", upsert=True)
        return out


prep, exe = PrepWithdrawn(), Exe()
with mock.patch.dict(SP.EXECUTORS, {"prep": prep, "art": exe}):
    with Show("solo.clean"):
        o7w, k7w, sid7w = new_order(1, "solo.clean", "wanda@example.com", pay_it=False)
    wj(f"orders/{o7w}/style/plan.json", two_step_plan())
    n0 = len(H.Fake.emails)
    hook(H.pay_session(sid7w, email="wanda@example.com"))
    done7w = wait_for(lambda: stopped(o7w), 60)
time.sleep(1.0)
check("an order withdrawn while step 1 of 2 draws: the chain stops with why withdrawn at its next hop, step 1 is done and recorded, step 2 is never drawn (no done record, no claim left), "
      "no delivery.json and no ready email",
      bool(done7w) and done7w.get("why") == "withdrawn" and prep.calls == 1 and exe.calls == 0 and exists(f"orders/{o7w}/style/done_prep.json")
      and not exists(f"orders/{o7w}/style/done_art.json") and not exists(f"orders/{o7w}/delivery.json") and not mails("wanda@example.com", READY_EN, n0), (done7w, prep.calls, exe.calls))
H.Fake.legal = PACK
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
M._KICKED.clear()
prep, exe = Prep(), Exe()
keep_base = os.environ.pop("SNAPEYES_SELF_BASE")          # no server making here: the page drives alone, as on a deployment whose self-calls are off
try:
    with mock.patch.dict(SP.EXECUTORS, {"prep": prep, "art": exe}):
        with Show("solo.clean"):
            o7q, k7q, sid7q = new_order(1, "solo.clean", "quin@example.com", pay_it=True)
        wj(f"orders/{o7q}/style/plan.json", two_step_plan())
        post("/api/order", {"action": "make", "order": o7q, "k": k7q, "eye": 1})
        c1, r1 = post("/api/order", {"action": "compose", "order": o7q, "k": k7q})
        c2, r2 = post("/api/order", {"action": "compose", "order": o7q, "k": k7q})
finally:
    os.environ["SNAPEYES_SELF_BASE"] = keep_base
check("the page's compose of a two step plan: the first call answers 200 state making with artwork {done 1, of 2, step art} (no download), the second is ready with the download",
      c1 == 200 and r1["state"] == "making" and r1["artwork"] == {"done": 1, "of": 2, "step": "art"} and "download" not in r1 and c2 == 200 and r2["state"] == "ready"
      and r2.get("download", {}).get("url"), (c1, r1, c2, r2))
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)

# eight eyes through the chain
MODE.update(side=256)
n0 = len(H.Fake.emails)
with Show("grp.collision"):
    CT.STYLES["grp.collision"]["stage_by_eyes"], saved_sbe = {}, CT.STYLES["grp.collision"]["stage_by_eyes"]
    o8c, k8c, sid8c = new_order(8, "grp.collision", "oskar@example.com", layout="ring")
    CT.STYLES["grp.collision"]["stage_by_eyes"] = saved_sbe
done8c = wait_for(lambda: stopped(o8c, "ready"), 120)
s8c = steps_of(o8c)
b8 = rj(f"orders/{o8c}/advance.json") or {}
check("eight eyes (the stand in family) through the server's own chain: ready, each eye made once, ONE art step for all eight (the chain is eight eyes, one compose, the mail: not longer than "
      "before the plan), one ready email",
      bool(done8c) and sorted(e for x, e in RENDERS if x == o8c) == list(range(1, 9)) and s8c["plan"]["steps"][0]["eyes"] == list(range(1, 9)) and s8c["done"]["result"]["count"] == 8
      and b8.get("hop", 99) <= SP.longest_chain() and len(mails("oskar@example.com", READY_EN, n0)) == 1, (done8c, b8, s8c["done"]))

# two paid orders at once on one warm instance, the first holds the heavy slot for longer than ten of the second's immediate retries would last (the review of WP6a):
# the second one's step is turned away for room, asked again after a back-off (not at once), and the order is made when the first has let go: no busy stop, no owner note
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
MODE.update(side=256, kind="blue", delay=0.0)
HOLD_S = 8.0
slow_for, slow_in, room_log = {}, threading.Event(), []


class SlowFirst(Exe):
    """The art step of the order named in slow_for draws for HOLD_S seconds inside the guard's slot, as a real 4096 px master does."""
    def __call__(self, ctx, plan, step, rerun):
        if ctx.order == slow_for.get("a"):
            slow_in.set()
            time.sleep(HOLD_S)
        return Exe.__call__(self, ctx, plan, step, rerun)


def spy_room(e):
    a = real_room(e)
    room_log.append((time.time(), a.retry_after, a.body.get("room")))
    return a


real_room = SP._room
exe = SlowFirst()
n_notes0 = len(H.Fake.emails)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), mock.patch.object(GD, "WAIT_S", 0.3), mock.patch.object(SP, "ROOM_MIN_S", 1), mock.patch.object(SP, "ROOM_MAX_S", 2),         mock.patch.object(SP, "_room", spy_room):
    with Show("solo.clean"):
        o7a, k7a, sid7a = new_order(1, "solo.clean", "ada@example.com", pay_it=False)
        o7b, k7b, sid7b = new_order(1, "solo.clean", "bea@example.com", pay_it=False)
    slow_for["a"] = o7a
    t_two = time.time()
    hook(H.pay_session(sid7a, email="ada@example.com"))
    slow_in.wait(30)
    hook(H.pay_session(sid7b, email="bea@example.com"))
    res7a = wait_for(lambda: stopped(o7a), 120)
    res7b = wait_for(lambda: stopped(o7b), 120)
    took_two = time.time() - t_two
gaps = [round(b[0] - a[0], 2) for a, b in zip(room_log, room_log[1:])]
notes_two = [m["subject"] for m in NOTES(n_notes0)]
check("two paid orders at once on one warm instance, the first draws for 8 s: the second's step is turned away for room (cpu) at least twice and asked again after a back-off of 1 to 2 s each "
      "(the patched bounds), never at once (the gaps between its refusals are at least 1 s); it is made when the first has let go and BOTH orders are ready, one email each",
      len(room_log) >= 2 and all(r[2] == "cpu" and 1 <= r[1] <= 2 for r in room_log) and all(g >= 0.9 for g in gaps) and bool(res7a) and res7a.get("why") == "ready"
      and bool(res7b) and res7b.get("why") == "ready" and took_two >= HOLD_S - 1.5 and len(mails("ada@example.com", READY_EN, n_notes0)) == 1
      and len(mails("bea@example.com", READY_EN, n_notes0)) == 1, (res7a, res7b, room_log, gaps, round(took_two, 1)))
check("... and nothing about it reaches the owner as a failure: no 'busy' note, no hold, no kill counted, the second order's own steps (the eye, the artwork) made once each",
      not any("busy" in s for s in notes_two) and not exists(f"orders/{o7b}/review.json") and steps_of(o7b)["try"]["kills"] == 0 and exe.calls == 2
      and sorted(e for x, e in RENDERS if x == o7b) == [1], (notes_two, exe.calls))
M._KICKED.clear()

# ============================================================================================ 8. holds after payment
section("8. holds after payment (IE5, IE8, IE9, IE3): review.json, one note, never another style")
CT.ENGINES_BUILT_EXTRA.add("collision")


def held(o, reason, n0, fresh_exe=None):
    rv = rj(f"orders/{o}/review.json") or {}
    notes = [m for m in NOTES(n0) if "needs a look" in m["subject"] and o in m["subject"]]
    arts = [p for p in os.listdir(local(f"orders/{o}")) if p.startswith("artwork_")]
    c, j = post("/api/order", {"action": "compose", "order": o, "k": pay.access_key(o)})
    return (rv.get("reason") == reason and len(notes) == 1 and not arts and not exists(f"orders/{o}/delivery.json") and c == 409 and j.get("reason") == "in_review"
            and not exists(f"orders/{o}/compose.lock") and not exists(f"orders/{o}/style/art.lock")), (rv, len(notes), arts, c, j.get("reason"))


MODE.update(side=256)
# (a) a plan that can never fit
exe = Exe()
n0 = len(H.Fake.emails)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), mock.patch.dict(os.environ, {"STYLE_SLOW_CPU": "6"}), Show("solo.powder"):
    o8a, k8a, sid8a = new_order(1, "solo.powder", "hold-a@example.com")
    done8a = wait_for(lambda: stopped(o8a, "review"), 60)
ok, d = held(o8a, "style_step_too_big", n0)
b = rj(f"orders/{o8a}/advance.json") or {}
check("IE5: a paid order whose plan can never fit (Powder Burst at the slow factor 6.0) is held style_step_too_big with ZERO busy hops (the chain made the eye, tried the artwork once, stopped "
      "'review'): review.json, ONE owner note naming the design, the factor and the need, no artwork, no other style, the executor never ran",
      bool(done8a) and ok and exe.calls == 0 and b.get("hop") == 1 and "6.0" in [m for m in NOTES(n0) if "needs a look" in m["subject"]][0]["text"]
      and "solo.powder" in [m for m in NOTES(n0) if "needs a look" in m["subject"]][0]["text"], (done8a, d, b))
hold_ev = [f for k, f in EVENTS if k == "master" and f.get("order") == o8a and f.get("hold")]
check("... and the hold is an event with its code", len(hold_ev) == 1 and hold_ev[0]["hold"] == "style_step_too_big" and hold_ev[0]["style"] == "solo.powder", hold_ev)
rt = C._review_todo(o8a, {"reason": "style_step_too_big", "t": 1})
check("the daily run's reminder knows the hold: it says why in words and what to do (the factor, the memory setting, the duration limit)",
      "never finish in one call" in rt[0] and "STYLE_SLOW_CPU" in rt[1] and "clear-review" in rt[1], rt)
# (b) engine_skew: a plan made under another engine version
exe = Exe()
n0 = len(H.Fake.emails)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), Show("solo.clean"):
    o8b, k8b, sid8b = new_order(1, "solo.clean", "hold-b@example.com", pay_it=False)
    pl = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, [None])
    pl = dict(pl, engine_v=ST.ENGINE_V + 5, created_at=int(time.time()))
    wj(f"orders/{o8b}/style/plan.json", pl)
    hook(H.pay_session(sid8b, email="hold-b@example.com"))
    done8b = wait_for(lambda: stopped(o8b, "review"), 60)
ok, d = held(o8b, "engine_skew", n0)
check("a deploy between payment and master (the plan was made under another ENGINE_V): held engine_skew, one note, nothing rendered, no other style", bool(done8b) and ok and exe.calls == 0, (done8b, d))
# (b2) the master was made from another preview than the plan was frozen on
n0 = len(H.Fake.emails)
with Show("solo.clean"):
    o8e, k8e, sid8e = new_order(1, "solo.clean", "hold-e@example.com", pay_it=False)
    pl = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, [{"eye_id": "cd" * 8, "profile": None}])
    wj(f"orders/{o8e}/style/plan.json", dict(pl, created_at=int(time.time())))
    hook(H.pay_session(sid8e, email="hold-e@example.com"))
    done8e = wait_for(lambda: stopped(o8e, "review"), 60)
ok, d = held(o8e, "eye_changed", n0)
check("an eye master made from another preview than the one the plan was frozen on (its eye id is not the plan's): held eye_changed, one note, nothing drawn (the seed would not be the approved one)",
      bool(done8e) and ok and not exists(f"orders/{o8e}/style/done_art.json"), (done8e, d))
# (b3) the real engine draws a picture the plan does not name (a plan whose seed is not the one its eyes make): never delivered
n0 = len(H.Fake.emails)
with Show("solo.clean"):
    o8f, k8f, sid8f = new_order(1, "solo.clean", "hold-f@example.com", pay_it=False)
    dr = rj(f"orders/{o8f}/draft/eye_1.json")
    pl = SP.make_plan({"style": "solo.clean", "eyes": 1, "layout": "single"}, [{"eye_id": dr["eye_id"], "profile": None}])
    wj(f"orders/{o8f}/style/plan.json", dict(pl, seed="12345", created_at=int(time.time())))
    hook(H.pay_session(sid8f, email="hold-f@example.com"))
    done8f = wait_for(lambda: stopped(o8f, "review"), 90)
ok, d = held(o8f, "picture_drift", n0)
check("a picture drawn from another seed than the plan names (a plan changed by hand, or code that changed without a new ENGINE_V) is held picture_drift AFTER the render and before anything is stored: "
      "one note, no artwork file, no delivery", bool(done8f) and ok, (done8f, d))
# (c) class drift: the master's colour class is not the preview's
n0 = len(H.Fake.emails)
MODE.update(side=4096)
with Show("solo.clean"):
    o8c2, k8c2, sid8c2 = new_order(1, "solo.clean", "hold-c@example.com", pay_it=False)
    dr = rj(f"orders/{o8c2}/draft/eye_1.json")
    dr["profile"] = {"v": 1, "cls": "grey", "stats": {"L": 5000, "C": 100, "h": 1000, "rgb": [1300, 1300, 1300]}}
    wj(f"orders/{o8c2}/draft/eye_1.json", dr)
    hook(H.pay_session(sid8c2, email="hold-c@example.com"))
    done8c2 = wait_for(lambda: stopped(o8c2, "review"), 90)
ok, d = held(o8c2, "class_changed", n0)
check("IE9: the sealed profile says grey and the 4096 px master measures another colour class: held class_changed BEFORE anything is drawn (never another palette), one note naming the eye, no artwork",
      bool(done8c2) and ok and "colour class" in [m for m in NOTES(n0) if "needs a look" in m["subject"]][0]["text"], (done8c2, d))
# the same order with a profile that agrees: the picture is made and the drift is recorded
n0 = len(H.Fake.emails)
with Show("solo.clean"):
    o8d, k8d, sid8d = new_order(1, "solo.clean", "hold-d@example.com", pay_it=False)
    dr = rj(f"orders/{o8d}/draft/eye_1.json")
    dr["profile"] = {"v": 1, "cls": "own", "pad": 1130, "stats": {"L": 5000, "C": 3000, "h": 2300, "rgb": [900, 1200, 1500]}}
    wj(f"orders/{o8d}/draft/eye_1.json", dr)
    hook(H.pay_session(sid8d, email="hold-d@example.com"))
    done8d = wait_for(lambda: stopped(o8d, "ready"), 120)
dd = (steps_of(o8d)["done"] or {}).get("drift") or [None]
check("... and with a profile of the same class the picture is made, and the drift is a number in the done record, in the artwork's record and in the event (the class pair, the ring colour's distance in levels)",
      bool(done8d) and isinstance(dd[0], dict) and dd[0]["cls"] == ["own", "own"] and isinstance(dd[0]["d_rgb"], (int, float))
      and any(f.get("order") == o8d and isinstance(f.get("d_rgb"), (int, float)) for k, f in EVENTS if k == "master")
      and dd[0].get("d_pad") == 0.01, dd)
MODE.update(side=256)
# (d) the plate fault: the first is a busy answer that does not count, the second holds
exe = Exe(["plate", "plate"])
n0 = len(H.Fake.emails)
keep = (SP.PLATE_RETRY_S, M.MAX_BUSY)
SP.PLATE_RETRY_S, M.MAX_BUSY = 5, 0
try:
    with mock.patch.dict(SP.EXECUTORS, {"art": exe}), Show("solo.clean"):
        o8e, k8e, sid8e = new_order(1, "solo.clean", "hold-e@example.com")
        done8e = wait_for(lambda: stopped(o8e, "review"), 60)
finally:
    SP.PLATE_RETRY_S, M.MAX_BUSY = keep
ok, d = held(o8e, "plate_unavailable", n0)
check("IE8: a missing plate after payment: the chain waited out the first fault WITHOUT a busy hop (MAX_BUSY was 0: a counted busy would have stopped it), the second held the order "
      "(plate_unavailable, the plate named in the try record), one note, no other plate was drawn",
      bool(done8e) and ok and exe.calls == 2 and steps_of(o8e)["try"]["plate"] == 2 and steps_of(o8e)["try"]["plate_id"] == "P-SN-CLOUD__stand_in", (done8e, d, exe.calls))
# (e) the third kill
exe = Exe()
n0 = len(H.Fake.emails)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), Show("solo.clean"):
    o8f, k8f, sid8f = new_order(1, "solo.clean", "hold-f@example.com", pay_it=False)
    wj(f"orders/{o8f}/style/try_art.json", {"kills": 2, "open": True, "attempts": 3, "plate": 0, "errors": [], "watchdog": 2})
    wj(f"orders/{o8f}/style/art.lock", {"t": time.time() - 300, "id": "dead"})
    hook(H.pay_session(sid8f, email="hold-f@example.com"))
    done8f = wait_for(lambda: stopped(o8f, "review"), 60)
ok, d = held(o8f, "style_step_failed", n0)
check("a step killed three times is held style_step_failed after payment: one note, nothing rendered", bool(done8f) and ok and exe.calls == 0 and steps_of(o8f)["try"]["kills"] == 3, (done8f, d))
# (f) an identical exception twice
exe = Exe(["exc", "exc"])
n0 = len(H.Fake.emails)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), Show("solo.clean"):
    o8g, k8g, sid8g = new_order(1, "solo.clean", "hold-g@example.com")
    first = wait_for(lambda: stopped(o8g, "error"), 60)
    err_notes = [m for m in NOTES(n0) if "could not be finished automatically" in m["subject"] and o8g in m["subject"]]
    M.kick(o8g, why="test")
    done8g = wait_for(lambda: stopped(o8g, "review"), 60)
ok, d = held(o8g, "style_step_failed", n0)
check("an exception raised twice by the same step: the first is the chain's own 'could not be finished' note and a stop (the page or the daily run tries once more), the second holds the order "
      "(style_step_failed): one note each, nothing made",
      bool(first) and len(err_notes) == 1 and bool(done8g) and ok and exe.calls == 2, (first, len(err_notes), done8g, d))
# the checks that tell a person to look first (a master that needs review) still deliver the artwork held, as before
exe = Exe(["review"])
n0 = len(H.Fake.emails)
with mock.patch.dict(SP.EXECUTORS, {"art": exe}), Show("solo.clean"):
    o8h, k8h, sid8h = new_order(1, "solo.clean", "hold-h@example.com")
    done8h = wait_for(lambda: stopped(o8h, "review"), 60)
dl8h = rj(f"orders/{o8h}/delivery.json") or {}
check("an artwork a check flags (needs_review) is stored and held for the owner's release, as it always was: delivery.json says needs_review, NO ready email, the index note stays",
      bool(done8h) and dl8h.get("needs_review") is True and not mails("hold-h@example.com", READY_EN, n0) and exists(f"cleanup/making/{o8h}.json"), (done8h, dl8h))

# ============================================================================================ 9. the watchdog
section("9. the watchdog (IE4): a step that is killed is retaken with no page open")
KILL_TL = threading.local()
ARMED = []


class SimKill(BaseException):
    """What a function killed by the platform looks like from inside this process: nothing after it runs, so no claim is released."""


class KillOnce(Exe):
    def __call__(self, ctx, plan, step, rerun):
        if self.calls == 0:
            self.calls += 1
            KILL_TL.dying = True
            raise SimKill()
        return super().__call__(ctx, plan, step, rerun)


def skip_if_dying(real):
    def wrapper(*a, **kw):
        if getattr(KILL_TL, "dying", False):
            return None
        return real(*a, **kw)
    return wrapper


real_arm = M.arm_watchdog


def counting_arm(order, hop=1):
    ARMED.append(order)
    return real_arm(order, hop)


exe = KillOnce()
n0 = len(H.Fake.emails)
t_arm = time.time()
patches = [mock.patch.object(SP, "LOCK_STALE", 3.0), mock.patch.object(ORDER_MOD, "COMPOSE_STALE", 3.0), mock.patch.object(M, "LEASE_STALE", 3.0),
           mock.patch.object(DU, "WATCHDOG_FIRST_S", 2), mock.patch.object(DU, "WATCHDOG_THEN_S", 2), mock.patch.object(M, "arm_watchdog", counting_arm),
           mock.patch.object(SP, "_release", skip_if_dying(SP._release)), mock.patch.object(SP, "_try_close", skip_if_dying(SP._try_close)),
           mock.patch.object(ORDER_MOD, "_compose_release", skip_if_dying(ORDER_MOD._compose_release)), mock.patch.object(M, "drop_lease", skip_if_dying(M.drop_lease)),
           mock.patch.dict(SP.EXECUTORS, {"art": exe})]
for p_ in patches:
    p_.start()
try:
    with Show("solo.clean"):
        o9, k9, sid9 = new_order(1, "solo.clean", "wanda@example.com")        # paid by the webhook: the server's own chain, no page is open at any time
    done9 = wait_for(lambda: stopped(o9, "ready"), 90)
    t_ready = time.time() - t_arm
finally:
    for p_ in reversed(patches):
        p_.stop()
s9 = steps_of(o9)
arts9 = [p for p in os.listdir(local(f"orders/{o9}")) if p.startswith("artwork_") and p.endswith(".jpg")]
check("IE4: the step was killed after its claim (no claim released, `open` left set, the advance lease left) and nobody asked for it again: the watchdog's relay hops waited out the claim "
      "and retook it, counted ONE kill, made the artwork ONCE and the order is ready, all within 120 s with no page open",
      bool(done9) and t_ready < 120 and s9["try"]["kills"] == 1 and exe.calls == 2 and len(arts9) == 1 and len(mails("wanda@example.com", READY_EN, n0)) == 1 and exists(f"orders/{o9}/delivery.json"),
      (done9, round(t_ready, 1), s9["try"], exe.calls, arts9))
check("the watchdog was armed at most twice for the step (once for the killed attempt, once for the retaken one) and the retaken step's own relays found a ready order and left",
      0 < len(ARMED) <= SP.WATCHDOG_MAX and (s9["try"]["watchdog"] <= SP.WATCHDOG_MAX), (ARMED, s9["try"]))
wd_first, wd_then = DU.derive(60)["watchdog_first"], DU.derive(60)["watchdog_then"]
check("with the real 60 s duration the two relays wait 40 and 40 s (80 s against the 75 s claim), so a killed step is retaken about 80 s after it began plus one step: inside the 120 s of the card",
      (wd_first, wd_then) == (40.0, 40.0) and wd_first + wd_then >= 75, (wd_first, wd_then))


# ============================================================================================ 10. the admin, the clean-up, the events
section("10. the admin: order_steps, rerun_step, recompose under the claims, lab_steps; the clean-up of the style folder; the master events")
WHO = {"kind": "admin"}
MODE.update(side=4096, kind="blue", delay=0.0)
os7 = ops.a_order_steps({"order": o7}, WHO)
st7 = steps_of(o7)
check("order_steps: the plan, every step with its done and try record, the rerun count, the claims, the capacity at the factor in force, the registry hash, the engine version, "
      "the eyes' ids and the artwork's own record",
      os7["ok"] and os7["plan"]["plan8"] == st7["plan"]["plan8"] and os7["steps"][0]["done"]["ms"] == st7["done"]["ms"] and os7["steps"][0]["try"]["kills"] == 0
      and os7["progress"] == {"done": 1, "of": 1, "step": None} and os7["rerun"] == 0 and os7["capacity"]["ok"] is True and os7["engine_v"] == ST.ENGINE_V
      and os7["locks"] == {"compose": None, "art": None} and os7["artwork"]["selfcheck"]["ok"] is True and re.fullmatch(r"[0-9a-f]{12}", os7["registry_hash"])
      and os7["eyes"] and os7["eyes"][0]["eye"] == 1 and os7["factor"] == CO.slow_factor(), {k: os7.get(k) for k in ("progress", "rerun", "locks", "capacity")})
no_plan = ops.a_order_steps({"order": "261005-noplan0001"}, WHO)
check("... an order with no records at all gives a plan of null and an empty step list, never an error", no_plan["plan"] is None and no_plan["steps"] == [] and no_plan["progress"]["of"] == 1, no_plan)
rr = ops.ACTIONS["recompose"]({"order": o7}, WHO)
check("recompose with nothing changed answers the same file and draws nothing (the claims are taken and released)",
      rr["result"] == "same" and rr["changed"] is False and rr["delivery"]["key"] == dl7["key"] and rr["ran"] == [] and not exists(f"orders/{o7}/compose.lock") and not exists(f"orders/{o7}/style/art.lock"), rr)
t0 = time.time()
rn = ops.ACTIONS["rerun_step"]({"order": o7, "step": "art"}, WHO)
dl7b = rj(f"orders/{o7}/delivery.json")
check("rerun_step draws the artwork again: a NEW file beside the delivered one (the digest is salted with the rerun count), the old file is NOT deleted (a link already mailed keeps working), "
      "the new one becomes the order's delivery by the admin, the rerun count is 1",
      rn["result"] == "rerun" and rn["changed"] and dl7b["key"] != dl7["key"] and store.exists(dl7["key"]) and store.exists(dl7b["key"]) and dl7b["by"] == "admin"
      and dl7b["key"] == SP.artwork_key(o7, st7["plan"], 1) and steps_of(o7)["rerun"]["n"] == 1 and exists(f"orders/{o7}/style/done_art_r1.json"), (rn, dl7b))
audit_names = [r["name"] for r in store.list_all(f"ops/audit/{time.strftime('%Y-%m-%d', time.gmtime())}") if not r["folder"]]
entries = [rj(f"ops/audit/{time.strftime('%Y-%m-%d', time.gmtime())}/{n}") for n in audit_names]
check("both admin actions are audited (rerun_step with its plan8, recompose), by the audit log of the panel", any(e and e.get("action") == "rerun_step" and e.get("order") == o7 and e.get("ok") for e in entries)
      and any(e and e.get("action") == "recompose" and e.get("order") == o7 for e in entries), [(e or {}).get("action") for e in entries][-6:])
# the claims: a live claim of the chain turns the admin away, nothing is doubled
wj(f"orders/{o7}/compose.lock", {"t": time.time(), "id": "someone"})
e_c = raises(lambda: ops.ACTIONS["recompose"]({"order": o7}, WHO), store.Answer)
os.remove(local(f"orders/{o7}/compose.lock"))
wj(f"orders/{o7}/eye_1.json", dict(rj(f"orders/{o7}/eye_1.json"), created="2026-10-07T00:00:00Z"))          # a master re-rendered: the recompose has work
wj(f"orders/{o7}/style/art.lock", {"t": time.time(), "id": "someone"})
e_a = raises(lambda: ops.ACTIONS["recompose"]({"order": o7}, WHO), store.Answer)
os.remove(local(f"orders/{o7}/style/art.lock"))
check("IE3: the admin's recompose takes the order's compose claim and the step's own: a live compose claim and a live step claim are each answered 409 rendering, and the delivered file is untouched",
      isinstance(e_c, store.Answer) and e_c.body["reason"] == "rendering" and isinstance(e_a, store.Answer) and e_a.body["reason"] == "rendering"
      and (rj(f"orders/{o7}/delivery.json") or {}).get("key") == dl7b["key"], (e_c, e_a))
e_leg = raises(lambda: ops.ACTIONS["rerun_step"]({"order": o6, "step": "art"}, WHO), store.Answer)
leg_re = ops.ACTIONS["recompose"]({"order": o6}, WHO)
check("a legacy order: recompose asks the legacy composer again (the same file when nothing changed); rerun_step is refused (409 rerun_not_available)",
      isinstance(e_leg, store.Answer) and e_leg.body["reason"] == "rerun_not_available" and leg_re["result"] == "same", (e_leg, leg_re.get("result")))

# after the clean-up of the style folder (14 days after delivery) an admin recompose must not point the delivery back at an older file
MODE.update(side=256)
exe_c = Exe()
with mock.patch.dict(SP.EXECUTORS, {"art": exe_c}), Show("solo.clean"):
    o10, k10, sid10 = new_order(1, "solo.clean", "cleo@example.com")
    done10 = wait_for(lambda: stopped(o10, "ready"), 60)
    rn10 = ops.ACTIONS["rerun_step"]({"order": o10, "step": "art"}, WHO)
    key10 = rj(f"orders/{o10}/delivery.json")["key"]
    gone10 = pay.folder_files(f"orders/{o10}/style")
    store.delete_many(gone10)                                    # what the daily clean-up does once the delivery is old enough
    rc10 = ops.ACTIONS["recompose"]({"order": o10}, WHO)
check("after the clean-up removed the style folder, an admin recompose of an order that was rerun does NOT point the delivery back at the first file: the rerun count comes back from the "
      "delivered artwork's own record, the same plan makes the same file, nothing is drawn",
      bool(done10) and rn10["result"] == "rerun" and len(gone10) >= 5 and rc10["result"] == "same" and rc10["delivery"]["key"] == key10 and rj(f"orders/{o10}/delivery.json")["key"] == key10
      and exe_c.calls == 3 and rj(f"orders/{o10}/style/rerun.json")["n"] == 1 and rj(f"orders/{o10}/style/rerun.json")["by"] == "restore", (rn10.get("result"), rc10.get("result"), exe_c.calls, key10))
# (the scripted executor has no reuse path, so it is called a third time; the real engine's executor reuses the stored artwork: the next check)
MODE.update(side=4096)

# lab_steps
store.put(f"orders/{LAB_ORDER}/eye_1.jpg", master_jpeg("blue", "round", 4096, 11), "image/jpeg", upsert=True)
store.put(f"orders/{LAB_ORDER}/eye_1.json", store.json_bytes({"order": LAB_ORDER, "eye": 1, "created": "2026-10-05T00:00:00Z", "bytes": 1, "eye_id": "ab" * 8}), "application/json", upsert=True)
dry = ops.ACTIONS["lab_steps"]({"order": LAB_ORDER, "style": "solo.clean", "dry": True}, WHO)
check("lab_steps dry: the plan and the capacity at the factor in force, nothing is drawn (no artwork in the folder)",
      dry["result"] == "dry" and dry["plan"]["style"] == "solo.clean" and dry["capacity"]["ok"] and not any(p.startswith("artwork_") for p in os.listdir(local(f"orders/{LAB_ORDER}"))), dry)
lr = ops.ACTIONS["lab_steps"]({"order": LAB_ORDER, "style": "solo.clean", "names": "Anna;Max", "date": "12 May 2026"}, WHO)
check("lab_steps: the master of a v3 style on the stored 4096 px eye through the same plan, guards, claim and executor: the artwork (4096 x 4096, a signed link), the steps with their time, "
      "CPU and memory increase, the capacity, nothing paid and no image model",
      lr["result"] == "made" and lr["artwork"]["width"] == 4096 and lr["artwork"]["url"] and lr["steps"][0]["done"]["by"] == "lab" and lr["steps"][0]["done"]["ms"] > 500
      and lr["capacity"]["ok"] and lr["plan"]["style"] == "solo.clean" and store.exists(lr["artwork"]["key"]) and lr["artwork"]["needs_review"] is False, {k: lr.get(k) for k in ("result", "capacity")})
lr2 = ops.ACTIONS["lab_steps"]({"order": LAB_ORDER, "style": "solo.clean", "names": "Anna;Max", "date": "12 May 2026"}, WHO)
lr3 = ops.ACTIONS["lab_steps"]({"order": LAB_ORDER, "style": "solo.clean", "names": "Anna;Max", "date": "12 May 2026", "fresh": True}, WHO)
check("asked again it is the same file (nothing drawn); fresh draws again beside it with the rerun count 1", lr2["result"] == "same" and lr2["artwork"]["key"] == lr["artwork"]["key"]
      and lr3["result"] == "made" and lr3["artwork"]["key"] != lr["artwork"]["key"] and lr3["rerun"] == 1 and store.exists(lr["artwork"]["key"]), (lr2["result"], lr3["result"], lr3.get("rerun")))
os.remove(local(f"orders/{LAB_ORDER}/style/done_art_r1.json"))                      # (the rerun's done record: a kill between its output and its done record)
t_re = time.time()
lr_re = ops.ACTIONS["lab_steps"]({"order": LAB_ORDER, "style": "solo.clean", "names": "Anna;Max", "date": "12 May 2026"}, WHO)
check("the real engine reuses a stored artwork whose done record is missing (a kill between the output and the done record): the same file, nothing drawn (seconds, not a render), the done "
      "record written again", lr_re["artwork"]["key"] == lr3["artwork"]["key"] and lr_re["result"] == "same" and time.time() - t_re < 4.0 and exists(f"orders/{LAB_ORDER}/style/done_art_r1.json"),
      (lr_re["result"], round(time.time() - t_re, 1)))
dry2 = ops.ACTIONS["lab_steps"]({"order": LAB_ORDER, "style": "solo.gold", "dry": True}, WHO)
check("a lab order's style folder belongs to the lab: another style starts again from nothing (the old plan and records are gone, the old artworks stay)",
      dry2["plan"]["style"] == "solo.gold" and not exists(f"orders/{LAB_ORDER}/style/done_art.json") and not exists(f"orders/{LAB_ORDER}/style/rerun.json") and store.exists(lr["artwork"]["key"]), dry2["plan"]["style"])
bad_calls = {
    "not a lab order": {"order": o7, "style": "solo.clean"},
    "a legacy style": {"order": LAB_ORDER, "style": "studio_black"},
    "an unknown style": {"order": LAB_ORDER, "style": "nonesuch"},
    "more eyes than stored": {"order": LAB_ORDER, "style": "solo.clean", "n": 2},
    "a layout the style does not take": {"order": LAB_ORDER, "style": "solo.clean", "layout": "ring"},
}
refused = {k: raises(lambda b=b: ops.a_lab_steps(b, WHO), L.ClientError) for k, b in bad_calls.items()}
check("lab_steps refuses: " + ", ".join(bad_calls), all(isinstance(v, L.ClientError) for v in refused.values()), refused)
with mock.patch.dict(os.environ, {"STYLE_SLOW_CPU": "6"}):
    e_hold = raises(lambda: ops.ACTIONS["lab_steps"]({"order": LAB_ORDER, "style": "solo.powder"}, WHO), store.Answer)
check("lab_steps of a plan that can never fit answers 409 step_held naming the hold (and is audited as a failure), never a render", isinstance(e_hold, store.Answer)
      and e_hold.status == 409 and e_hold.body["reason"] == "step_held" and e_hold.body["hold"] == "style_step_too_big", e_hold)
st_ok = ops.ACTIONS["order_steps"]({"order": LAB_ORDER}, WHO)
check("order_steps reads a lab order's plan too (the page's step table)", st_ok["plan"] is not None and st_ok["plan"]["style"] == "solo.powder", st_ok.get("plan") and st_ok["plan"]["style"])

# master_compose of a v3 style (the lab's endpoint): the same step runner, the owner's sentence on a hold
MODE.update(side=4096)
LAB2 = "lab-261005-v3steps02"
store.put(f"orders/{LAB2}/eye_1.jpg", master_jpeg("blue", "round", 4096, 11), "image/jpeg", upsert=True)
store.put(f"orders/{LAB2}/eye_1.json", store.json_bytes({"order": LAB2, "eye": 1, "created": "c", "bytes": 1, "eye_id": "cd" * 8}), "application/json", upsert=True)
mcb = {"order": LAB2, "ticket": L.mint_ticket(store.unlock_kind(LAB2), 300), "keys": [f"orders/{LAB2}/eye_1.jpg"], "style": "solo.clean", "layout": "single", "names": "Ona", "title": ""}
r_mc = REAL_MC(mcb)
r_mc2 = REAL_MC(dict(mcb, ticket=L.mint_ticket(store.unlock_kind(LAB2), 300)))
with mock.patch.dict(os.environ, {"STYLE_SLOW_CPU": "6"}):
    e_mc = raises(lambda: REAL_MC(dict(mcb, style="solo.powder", ticket=L.mint_ticket(store.unlock_kind(LAB2), 300))), store.Answer)
check("master_compose of a style of the v3 engine (the lab's endpoint, which refused it until the plan existed): the same step runner, a 4096 px artwork, the same file the second time, "
      "and on a plan that can never fit 409 step_held",
      r_mc["ok"] and r_mc["width"] == 4096 and r_mc["design_used"] == "clean" and r_mc2["existing"] is True and r_mc2["key"] == r_mc["key"] and isinstance(e_mc, store.Answer)
      and e_mc.body["reason"] == "step_held" and exists(f"orders/{LAB2}/style/plan.json"), (r_mc.get("key"), e_mc))
check("master_compose still answers 400 for a style that is not renderable (an id that takes no one-eye order)",
      isinstance(raises(lambda: REAL_MC(dict(mcb, style="duo.kiss_collision", ticket=L.mint_ticket(store.unlock_kind(LAB2), 300))), L.ClientError), L.ClientError), "")
check("step_need: the legacy figure for a legacy style, the cost table's for a v3 style, None where the table has no row",
      MC.step_need("studio_black", 1) == CO.legacy_need(1) == 21.8 and 20 < MC.step_need("solo.powder", 1) < 30
      and MC.step_need("solo.powder", 1) == round(CO.step_need("singles.powder", 1, side=4096), 3), (MC.step_need("solo.powder", 1),))
with mock.patch.object(CT, "engine_for", lambda s, n: {"module": "singles", "design": "nonesuch", "work_side": 4096, "clean": 0}):
    no_row = MC.step_need("solo.powder", 1)
check("... and None where the cost table has no row for the design", no_row is None, no_row)
# a request for another style than the order's plan is a hold, never the other style's artwork
mcb2 = dict(mcb, ticket=L.mint_ticket(store.unlock_kind(o7), 300), order=o7, keys=[f"orders/{o7}/eye_1.jpg"], style="solo.gold")
e_plan = raises(lambda: REAL_MC(mcb2), store.Answer)
check("a request to master_compose for another style than the order's own plan (a paid order's plan is the one the order was made under) is 409 step_held (plan_mismatch), never the artwork of the other style",
      isinstance(e_plan, store.Answer) and e_plan.body["reason"] == "step_held" and e_plan.body["hold"] == "plan_mismatch", e_plan)

# the clean-up of the style folder
DAY = 86400
seen_say = []
mk_style = lambda o, delivered_days=None, deleted=False, extra=True: (
    store.put(f"orders/{o}/style/plan.json", b"{}", "application/json", upsert=True), store.put(f"orders/{o}/style/done_art.json", b"{}", "application/json", upsert=True),
    store.put(f"orders/{o}/order.json", b"{}", "application/json", upsert=True),
    store.put(f"{SP.INDEX}/{o}.json", b"{}", "application/json", upsert=True),
    delivered_days is not None and store.put(f"orders/{o}/delivery.json", store.json_bytes({"key": "x", "created_at": int(time.time() - delivered_days * DAY)}), "application/json", upsert=True),
    deleted and store.put(f"orders/{o}/deleted.json", b"{}", "application/json", upsert=True))
oc_old, oc_new, oc_none, oc_gone = "260915-clean00001", "260915-clean00002", "260915-clean00003", "260915-clean00004"
mk_style(oc_old, 15)
mk_style(oc_new, 3)
mk_style(oc_none)
mk_style(oc_gone, 1, deleted=True)
dry_res = C._styles(False, 0.0, seen_say.append)
check("the clean-up's dry run of the style folders changes nothing", exists(f"orders/{oc_old}/style/plan.json") and exists(f"{SP.INDEX}/{oc_old}.json") and dry_res["folders"] == 1, dry_res)
res = C._styles(True, 0.0, seen_say.append)
check("the clean-up removes the style folder of an order delivered 14 days ago or more (and its marker), keeps an order delivered 3 days ago and one never delivered (held or making), and drops "
      "the folder and marker of an order whose files are gone",
      not exists(f"orders/{oc_old}/style/plan.json") and not exists(f"{SP.INDEX}/{oc_old}.json") and exists(f"orders/{oc_new}/style/plan.json") and exists(f"{SP.INDEX}/{oc_new}.json")
      and exists(f"orders/{oc_none}/style/plan.json") and not exists(f"orders/{oc_gone}/style/plan.json") and not exists(f"{SP.INDEX}/{oc_gone}.json") and exists(f"orders/{oc_old}/order.json")
      and res["kept"] >= 2 and res["gone"] >= 1, res)
oc_young = f"{time.strftime('%y%m%d', time.gmtime())}-clean00005"
mk_style(oc_young, 20)           # (its delivery says 20 days ago, which an order made today cannot have: the id says it is too young to look at)
res_y = C._styles(True, 0.0, seen_say.append)
check("an order made after the cut-off is skipped by its id without a read (it cannot have been delivered before it was made): its folder and marker stay",
      exists(f"orders/{oc_young}/style/plan.json") and exists(f"{SP.INDEX}/{oc_young}.json") and res_y["kept"] >= 1, res_y)
run_res = C.run(yes=True, lock=False)
check("the daily run includes the step (res['style']) after the other deletions", isinstance(run_res.get("style"), dict) and {"orders", "kept", "gone"} <= set(run_res["style"]), run_res.get("style"))

# the events
ev = E.build("master", dict(step="art", part=1, of=2, ms=1234, order="261005-abcd1234", count=1, style="solo.powder", design="powder", peak_mb=720, hwm_mb=950, need_s=26.1, cpu_s=11.2,
                            kills=1, d_rgb=2.5, hold="style_step_too_big", needs_review=False, existing=False, bogus="x", name="Anna"))
check("the master event keeps the new fields (part, of, need_s, cpu_s, peak_mb, hwm_mb, kills, design, d_rgb, hold) and drops what is not on the list: a name, an unknown field",
      all(ev.get(k) is not None for k in ("part", "of", "need_s", "cpu_s", "peak_mb", "hwm_mb", "kills", "design", "d_rgb", "hold")) and "bogus" not in ev and "name" not in ev
      and ev["hold"] == "style_step_too_big" and ev["lab"] is False, ev)
bad_code = E.build("master", dict(step="art", hold="not a code!", design="Has Space"))
check("a hold or design that is not a short lower case code is dropped, never stored", "hold" not in bad_code and "design" not in bad_code, bad_code)
agg = E.summarize([ev, dict(ev, hold=None, peak_mb=800, need_s=30.0), dict(ev, hold=None, existing=True), dict(ev, hold="engine_skew"),
                   {"kind": "master", "step": "compose", "existing": False, "ms": 5}])
check("the daily counts: art steps made (not the reused ones), by style, holds by code, the average memory and planned time as [sum, count], the review flag; the legacy compose count is its own",
      agg["master_art"] == 1 and agg["master_art_style"] == {"solo.powder": 1} and agg["master_hold"] == {"style_step_too_big": 1, "engine_skew": 1} and agg["master_existing"] == 1
      and agg["ms"]["art_peak_mb"] == [800, 1] and agg["ms"]["art_need_s"] == [30.0, 1] and agg["master_compose"] == 1, {k: agg[k] for k in ("master_art", "master_hold", "ms")})
merged = E.merge(agg, agg)
check("the counts merge (numbers add, tables add)", merged["master_art"] == 2 and merged["master_hold"]["engine_skew"] == 2 and merged["ms"]["art_peak_mb"] == [1600, 2], merged["master_art"])

# scripts/order_admin.py status prints the plan
env = dict(os.environ)
rs = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "order_admin.py"), "status", o7], capture_output=True, text=True, env=env, encoding="utf-8", timeout=120)
check("order_admin.py status prints the plan: its identity, the design, the engine and registry versions, the capacity, every step with its planned and real time and memory, the kills, the rerun count",
      rs.returncode == 0 and f"plan      {st7['plan']['plan8']}" in rs.stdout and "design clean" in rs.stdout and "capacity  fits one call" in rs.stdout and "step      art" in rs.stdout
      and "kills 0" in rs.stdout and "rerun     2" in rs.stdout, (rs.returncode, rs.stdout[-1200:], rs.stderr[-300:]))

# ============================================================================================ 11. ENGINE_V and the files of the work
section("11. ENGINE_V against the recorded goldens, the files of the work")
rec_path = os.path.join(HERE, "data", "engine_v.json")
recd = json.load(open(rec_path, encoding="utf-8"))
norm = lambda b: b.replace(b"\r\n", b"\n")
now_hashes = {n: hashlib.sha256(norm(open(os.path.join(HERE, "data", n), "rb").read())).hexdigest() for n in sorted(recd["goldens"])}
check("ENGINE_V is the version the goldens were recorded under: data/engine_v.json names the version and the hash of every golden file; if a golden file changed, raise ENGINE_V "
      "and record the new hashes (python scripts/styles_tests/test_steps.py --record-engine-v) together with the reviewed diff",
      recd["engine_v"] == ST.ENGINE_V and now_hashes == recd["goldens"], {n: (now_hashes[n][:10], recd["goldens"][n][:10]) for n in now_hashes if now_hashes[n] != recd["goldens"][n]})
check("every golden data file of the work is on that list (a new golden file must join it)",
      sorted(recd["goldens"]) == sorted(n for n in os.listdir(os.path.join(HERE, "data")) if n.endswith(".json") and n != "engine_v.json"), sorted(os.listdir(os.path.join(HERE, "data"))))
NEW_FILES = ["api/_lib/duration.py", "api/_lib/styles/steps.py", "api/_lib/styles/guard.py"]
changed = NEW_FILES + ["api/order.py", "api/_lib/maker.py", "api/master_compose.py", "api/master_eye.py", "api/_lib/ops.py", "api/_lib/cleanup.py", "api/_lib/events.py",
                       "api/_lib/styles/costs.py", "scripts/order_admin.py", "scripts/check_styles.mjs", "src/admin/StepTable.tsx", "src/admin/LabSteps.tsx",
                       "src/admin/OrderDetail.tsx", "src/admin/Lab.tsx", "src/admin/api.ts", "src/admin/format.ts", "src/order/OrderApp.tsx", "src/order/driver.ts",
                       "src/order/api.ts", "src/order/copy.ts", "src/order/copy.lt.ts", "src/order/copy.hu.ts", "scripts/styles_tests/test_steps.py"]
check("no en or em dash and no raw invisible or bidirectional character in any file the work added or changed",
      not any(re.search(DASH, read(f)) or re.search("[\u200b-\u200f\u2028-\u202e\u2060-\u2064\ufeff]", read(f)) for f in changed), [f for f in changed if re.search(DASH, read(f))])
check("every new module has the __future__ import and parses as Python 3.12 (Vercel's default)",
      all(re.search(r"^from __future__ import annotations\r?$", read(f), re.M) and __import__("ast").parse(read(f), feature_version=(3, 12)) for f in NEW_FILES), "")
code = ("import sys; sys.path.insert(0, %r); import _lib.styles.steps, _lib.styles.guard, _lib.duration; "
        "bad = [m for m in sys.modules if m.startswith('_lib.styles.') and m.split('.')[2] in ('singles','collision','universe','core','matter','plates','atlas','layouts','eye','gate','pupil','palette','text','selfcheck')]; "
        "print(bad)") % API
imp = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
check("importing steps, guard and duration loads no engine and no foundation module (a function that only reads a plan or a status pays nothing for an engine)",
      imp.returncode == 0 and imp.stdout.strip() == "[]", (imp.stdout, imp.stderr[-300:]))
src_steps = read("api/_lib/styles/steps.py") + read("api/_lib/styles/guard.py") + read("api/_lib/duration.py")
check("the new modules hold no secret name, no Windows or scratch path and no written price",
      not re.search(r"GEMINI_API_KEY|SERVICE_KEY|C:\\\\|wave-y3|wave-g|SNAPEYES_TICKET_SECRET|os\.environ\[", src_steps), re.findall(r"GEMINI_API_KEY|SERVICE_KEY|C:\\\\|wave-y3", src_steps))
check("the style suites refuse to run with a model key variable set (I21): the process under test holds none", not any(k.startswith("GEMINI") for k in os.environ), [k for k in os.environ if k.startswith("GEMINI")])

if "--record-engine-v" in sys.argv:
    out = {"engine_v": ST.ENGINE_V, "goldens": now_hashes}
    json.dump(out, open(rec_path, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("recorded", rec_path)


print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
