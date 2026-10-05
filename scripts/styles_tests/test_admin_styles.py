# -*- coding: utf-8 -*-
"""WP13a of the v3 engine work: the owner's switch of the style catalogue and the events behind the Stiliai page of the admin panel. Tests I16 (every event
field whitelisted and a code, an override above the ceiling refused, `live` refused without L1 and without L0 or its written waiver, one audit entry per
change, the Lithuanian sentences), IE11 (a storage error fails closed at checkout, the public catalogue lists only preview and live ids, the cache is 30 s)
and I22 for the admin side (the funnel numbers equal a replay of the recorded events, the opening line is one function).

  1. the read path: no override, an override that lowers, one above the ceiling that is ignored, an entry that is not a stage, a file that is not ours, a storage
     that fails (closed: strict raises, the pages get the ceiling capped at preview), no storage at all, the 30 s cache and the 5 s memory of a failure
  2. the public catalogue and the tile list follow the switch
  3. the action styles_override: the refusals, the ticks, the waiver, a range of eye counts, restore, the revision, the confirmation, the price test
  4. the default effective stage (the cutover's hook): a v3 style is held at preview until the owner's tick
  5. the orders in flight when a style is taken back (finish or hold)
  6. the audit log of the switch and the limits
  7. over HTTP: the admin key, 503 storage_busy at checkout when the switch cannot be read
Review fixes of WP13a (the second pass): L0 is a score with the bar and the scorer's name or the written waiver (3b), a hold that stops half way is reported and can be
finished (5b), the single flight and the request's own lack of time in the read path (1d), audit_written and the retention of the style audit log (7b), the numbers the
card names (8f).
No network, no image model, no real eye in the repository.
    python test_admin_styles.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3admin."""
import atexit
import contextlib
import json
import os
import re
import shutil
import sys
import tempfile
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
SP = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP, "wave-pv", "tests") if SP else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:700]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


def info(text):
    print("   " + text, flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3admin_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)       # a green, a red and a crashed run leave nothing in the temp directory (suites/README.md, Adding a suite, rule 4)
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ["SNAPEYES_ADMIN_SECRET"] = "wp13a-admin-secret-for-tests-0123456789abcdef0123"
os.environ["CRON_SECRET"] = "wp13a-cron-secret-for-tests-0123456789"        # the events are stored only while the daily clean-up can delete them
sys.path.insert(0, API)
import importlib.util  # noqa: E402
import requests  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import stage_overrides as SO  # noqa: E402
from _lib import store, pay, ops, abtest  # noqa: E402
from _lib import events as E  # noqa: E402

for name in ("admin",):
    spec_m = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
    mod = importlib.util.module_from_spec(spec_m)
    spec_m.loader.exec_module(mod)
    H.MODS[name] = mod
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
WHO = {"kind": "admin-v1", "exp": int(time.time()) + 3600}
LEGACY = list(CT.legacy_ids())
REAL_GET, REAL_PUT = store.get, store.put
REAL_NOW = SO._now


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def raised(fn):
    try:
        fn()
    except Exception as e:  # noqa
        return e
    return None


def reset():
    """No override, no audit entry, an empty cache, the real clock."""
    shutil.rmtree(os.path.join(STORE, "ops", "styles"), ignore_errors=True)
    SO._now = REAL_NOW
    store.get = REAL_GET
    SO.invalidate()


def act(action, **body):
    return ops.ACTIONS[action](dict(body), WHO)


def refused(action, status=None, reason=None, **body):
    """The Answer (or ClientError) the action raised, as (kind, status, reason), or None when it did not refuse."""
    try:
        act(action, **body)
    except store.Answer as a:
        return ("answer", a.status, a.body.get("reason"), a.body)
    except L.ClientError as e:
        return ("client", 400, "bad_request", {"error": str(e)})
    return None


def says(r, status, reason):
    return bool(r) and r[1] == status and r[2] == reason


class Clock:
    """The cache's clock, moved by hand."""
    def __init__(self):
        self.t = 1000.0

    def __enter__(self):
        SO._now = lambda: self.t
        SO.invalidate()
        return self

    def __exit__(self, *a):
        SO._now = REAL_NOW
        SO.invalidate()


class CountingStore:
    """store.get counted (and, when `fail` is set, failing) for the path of the overrides only."""
    def __init__(self, fail=None):
        self.calls, self.fail = 0, fail

    def __enter__(self):
        def get(path, *a, **k):
            if path == SO.PATH:
                self.calls += 1
                if self.fail:
                    raise self.fail
            return REAL_GET(path, *a, **k)
        store.get = get
        return self

    def __exit__(self, *a):
        store.get = REAL_GET


def write_object(obj, invalidate=True):
    path = os.path.join(STORE, "ops", "styles", "overrides.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(obj if isinstance(obj, str) else json.dumps(obj))
    if invalidate:
        SO.invalidate()


def ov(**styles):
    return {"v": 1, "rev": 3, "styles": {sid: {"stage_by_eyes": st} for sid, st in styles.items()}}


# ============================================================================================ 1. the read path
section("1. the read path of the owner's switch")
reset()
check("no file: every effective stage is the ceiling, the legacy ids are orderable (strict and not strict)",
      all(CT.stage_of(i, 2) == "live" and CT.orderable(i, 2) and CT.orderable(i, 2, strict=False) for i in LEGACY)
      and CT.stage_of("solo.powder", 1) == "lab" and CT.orderable_ids(3) == tuple(LEGACY))
check("the default source is the store's: catalogue._override_source is catalogue._store_source", CT._override_source is CT._store_source)
write_object(ov(celestial_gold={"1": "preview", "2": "lab"}))
check("an override lowers: celestial_gold is preview for one eye and lab for two, live for three; orderable and previewable follow it",
      CT.stage_of("celestial_gold", 1) == "preview" and CT.stage_of("celestial_gold", 2) == "lab" and CT.stage_of("celestial_gold", 3) == "live"
      and not CT.orderable("celestial_gold", 1) and not CT.orderable("celestial_gold", 2) and CT.orderable("celestial_gold", 3)
      and CT.previewable("celestial_gold", 1) and not CT.previewable("celestial_gold", 2) and CT.previewable("celestial_gold", 2, admin=True))
check("the other legacy ids are untouched, and a style without a record has none",
      all(CT.stage_of(i, 1) == "live" for i in LEGACY if i != "celestial_gold") and SO.source("studio_black", 1) is None)
write_object(ov(**{"solo.powder": {"1": "preview"}, "celestial_gold": {"1": "live"}}))
check("an override above the ceiling lowers nothing and raises nothing: solo.powder (lab) stays lab; live over a live ceiling is live",
      CT.stage_of("solo.powder", 1) == "lab" and not CT.previewable("solo.powder", 1) and CT.stage_of("celestial_gold", 1) == "live")
write_object(ov(celestial_gold={"1": "banana", "2": "preview"}))
check("an entry that is not a stage reads as lab (closed, never open); the next one still reads",
      CT.stage_of("celestial_gold", 1) == "lab" and CT.stage_of("celestial_gold", 2) == "preview" and CT.stage_of("celestial_gold", 3) == "live")
write_object({"v": 1, "rev": 1, "styles": {"no.such_style": {"stage_by_eyes": {"1": "lab"}}, "studio_black": {"stage_by_eyes": {"9": "lab", "x": "lab"}}}})
check("an id the registry does not know and a count that is not 1 to 8 are dropped",
      CT.stage_of("studio_black", 1) == "live" and "no.such_style" not in SO.load()["styles"] and "studio_black" not in SO.load()["styles"])

section("1b. failing closed: a file that is not ours, a storage that fails, no storage at all")
for label, content in (("not JSON", "{not json"), ("another version", json.dumps({"v": 2, "styles": {}})), ("not an object", "[1, 2]")):
    write_object(content)
    e = raised(lambda: CT.orderable("celestial_gold", 1))
    e2 = raised(lambda: CT.orderable_ids(3))
    check(f"a file that is {label}: strict (orderable, orderable_ids) raises a StorageError, the checkout would answer 503 storage_busy",
          isinstance(e, store.StorageError) and isinstance(e2, store.StorageError) and isinstance(e, SO.StageStoreError), (e, e2))
    check(f"... and the page-facing stage is the ceiling capped at preview, never live (a legacy id live becomes preview, a lab id stays lab), {label}",
          CT.stage_of("celestial_gold", 1) == "preview" and CT.stage_of("solo.powder", 1) == "lab" and CT.stage_of("celestial_gold", 3, strict=False) == "preview"
          and not CT.orderable("celestial_gold", 1, strict=False) and CT.orderable_max_eyes() == 0 and CT.pick_for(2) is None)
reset()
with CountingStore(fail=store.StorageError("injected: storage down")) as cs:
    e = raised(lambda: CT.orderable("celestial_gold", 3))
    check("a storage that fails: strict raises, the page-facing stage is capped at preview",
          isinstance(e, store.StorageError) and CT.stage_of("celestial_gold", 3) == "preview" and CT.stage_of("studio_black", 1) == "preview")
    check("the public catalogue and the tile list are served from the fallback (everything preview, nothing buyable, no pick), they do not raise",
          all(all(v == "preview" for v in c["stages"].values()) for c in CT.public_catalogue() if c["id"] in LEGACY)
          and CT.tile_list(1)["pick"] is None and all(t["stage"] == "preview" for t in CT.tile_list(1)["tiles"] if t["legacy"]))
    check("the failure of one refresh costs one storage call, not one per question: three hundred questions, the calls are one",
          cs.calls == 1, cs.calls)
reset()
with Clock() as clock, CountingStore(fail=store.StorageError("injected")) as cs:
    raised(lambda: CT.orderable("celestial_gold", 3))
    clock.t += 4.0
    raised(lambda: CT.orderable("celestial_gold", 3))
    check("a failure is remembered for 5 seconds (no new call after 4 s)", cs.calls == 1, cs.calls)
    clock.t += 1.5
    raised(lambda: CT.orderable("celestial_gold", 3))
    check("... and the storage is asked again after that", cs.calls == 2, cs.calls)
reset()
with CountingStore(fail=store.StorageError("injected")):
    first = CT.stage_of("celestial_gold", 3)
with CountingStore():
    SO.invalidate()
    check("a storage that comes back is read at once (the failure is not stuck): live again", CT.stage_of("celestial_gold", 3) == "live" and CT.orderable("celestial_gold", 3))
reset()
saved_env = os.environ.pop("STORE_LOCAL_DIR")
try:
    check("a deployment with no storage at all has no override and no error: the ceiling, strict and not",
          CT.stage_of("celestial_gold", 3) == "live" and CT.orderable("celestial_gold", 3) and not store.configured())
finally:
    os.environ["STORE_LOCAL_DIR"] = saved_env
reset()
check("set_override_source(None) is 'no overrides' and the default source can be put back",
      (lambda: (CT.set_override_source(None), CT.stage_of("studio_black", 1) == "live")[1])() and (CT.set_override_source(CT._store_source), CT._override_source is CT._store_source)[1])

section("1d. the read path: one read for a stampede, and a request's own lack of time is not the storage's failure")
import threading  # noqa: E402
reset()
calls_ = {"n": 0}


def slow_get(path, *a, **k):
    if path == SO.PATH:
        calls_["n"] += 1
        time.sleep(0.2)
    return REAL_GET(path, *a, **k)


store.get = slow_get
SO.invalidate()
ths = [threading.Thread(target=lambda: CT.stage_of("celestial_gold", 1)) for _ in range(40)]
for t_ in ths:
    t_.start()
for t_ in ths:
    t_.join()
store.get = REAL_GET
check("40 concurrent first questions on a cold instance are ONE storage read (the others wait for it and use its answer)", calls_["n"] == 1, calls_)
reset()
real_tl = store.time_left
store.time_left = lambda *a, **k: 1.0
try:
    with CountingStore() as cs:
        e1 = raised(lambda: SO.load())
        e2 = raised(lambda: CT.orderable("celestial_gold", 1))
        n_out = cs.calls
finally:
    store.time_left = real_tl
check("a request that has no time left raises StageStoreError (strict callers answer 503) and starts no storage call",
      isinstance(e1, SO.StageStoreError) and "out of time" in str(e1) and isinstance(e2, SO.StageStoreError) and n_out == 0, (e1, e2, n_out))
check("... and it is NOT remembered as the storage's failure: the next request, with time, reads at once and gets the object (no 5 second closed door for everyone)",
      SO._CACHE["err"] is None and CT.orderable("celestial_gold", 1) and CT.stage_of("celestial_gold", 1) == "live")
reset()

section("1c. the cache is 30 seconds")
reset()
write_object(ov(celestial_gold={"1": "preview"}))
with Clock() as clock, CountingStore() as cs:
    for _ in range(150):
        CT.stage_of("celestial_gold", 1)
        CT.tiles_for(2)
        CT.public_catalogue()
    check("many questions in one request cost one storage read", cs.calls == 1, cs.calls)
    clock.t += 29.0
    CT.stage_of("celestial_gold", 1)
    check("29 seconds later it is still the same reading", cs.calls == 1, cs.calls)
    write_object(ov(celestial_gold={"1": "lab"}), invalidate=False)          # another instance's change: this one's cache is not told
    check("another instance's change is not seen before the 30 seconds are over (the old reading is still in this one)", CT.stage_of("celestial_gold", 1) == "preview")
    clock.t += 1.5
    check("... and is seen after them", CT.stage_of("celestial_gold", 1) == "lab" and cs.calls == 2, cs.calls)
reset()
check("TTL_S is 30 and ERR_TTL_S is 5", SO.TTL_S == 30.0 and SO.ERR_TTL_S == 5.0)

# ============================================================================================ 2. the public catalogue
section("2. the public catalogue and the tile list follow the switch")
reset()
pub = {c["id"]: c for c in CT.public_catalogue()}
check("the public catalogue lists only ids that are preview or live somewhere: the six legacy ids today, no lab id and no planned id",
      set(pub) == set(LEGACY) and all(set(c["stages"].values()) <= {"preview", "live"} for c in pub.values()))
check("it carries no engine fact (no plates, no gate rules, no engine module)", all(set(c) == {"id", "name", "slug", "group", "eyes", "stages"} for c in pub.values()))
write_object(ov(celestial_gold={"1": "preview", "2": "lab", "3": "lab", "4": "lab", "5": "lab", "6": "lab", "7": "lab", "8": "lab"}))
pub = {c["id"]: c for c in CT.public_catalogue()}
check("an override that takes a style back to lab removes those counts from the list; preview shows as preview",
      pub["celestial_gold"]["stages"] == {"1": "preview"} and pub["studio_black"]["stages"]["1"] == "live")
write_object(ov(**{i: {str(n): "lab" for n in range(1, 9)} for i in LEGACY}))
check("a style taken back to lab everywhere leaves the list; with nothing left the catalogue is empty and nothing can be bought",
      CT.public_catalogue() == [] and CT.orderable_max_eyes() == 0 and CT.pick_for(1) is None and CT.orderable_ids(1) == ())
reset()

# ============================================================================================ 3. the action
section("3. styles_override: the refusals, the ticks, the waiver, ranges, restore, the revision, the confirmation, the price test")
reset()
r = act("styles_catalogue")
check("styles_catalogue: every id of the registry with its ranges, the checks L0 to L11, the revision and the limits, nothing drawn from a guess",
      r["ok"] and [s["id"] for s in r["styles"]] == list(CT.ids()) and r["checks"] == [f"L{i}" for i in range(12)] and r["rev"] == 0
      and r["limits"] == SO.LIMITS_DEFAULT and r["default_effective"] is None and r["price_test"] == [], r.get("rev"))
gold = next(s for s in r["styles"] if s["id"] == "celestial_gold")
check("a legacy id is one range per count group that reads the same: live for one to eight eyes, orderable, switchable, with nothing ticked",
      len(gold["ranges"]) == 1 and gold["ranges"][0]["eyes"] == [1, 8] and gold["ranges"][0]["effective"] == "live" and gold["ranges"][0]["orderable"]
      and gold["ranges"][0]["switchable"] and gold["ranges"][0]["checklist"] == {} and gold["ranges"][0]["missing_for_live"] == ["L1", "L0"])
powder = next(s for s in r["styles"] if s["id"] == "solo.powder")
planned = next(s for s in r["styles"] if CT.ceiling(s["id"], s["eyes"][0]) == "planned")
check("a lab id shows ceiling lab and is not orderable; a planned id is not switchable",
      powder["ranges"][0]["ceiling"] == "lab" and not powder["ranges"][0]["orderable"] and not planned["ranges"][0]["switchable"])

check("a stage change without the confirmation is a 400 and changes nothing",
      says(refused("styles_override", style="celestial_gold", eyes=1, stage="preview"), 400, "bad_request") and SO.load(force=True)["rev"] == 0)
check("an unknown style, eye counts outside the style's range, a malformed range and an unknown stage are 400",
      all(says(refused("styles_override", confirm=True, **b), 400, "bad_request") for b in (
          {"style": "nope", "eyes": 1, "stage": "lab"}, {"style": "solo.powder", "eyes": 2, "stage": "lab"}, {"style": "celestial_gold", "eyes": "9-10", "stage": "lab"},
          {"style": "celestial_gold", "eyes": "x", "stage": "lab"}, {"style": "celestial_gold", "eyes": 1, "stage": "retired"},
          {"style": "celestial_gold", "eyes": True, "stage": "lab"}, {"style": "celestial_gold", "eyes": 1, "stage": "lab", "tick": {"L12": True}},
          {"style": "celestial_gold", "eyes": 1, "stage": "lab", "reason_kind": "bad"}, {"style": "celestial_gold", "eyes": 1})))
x = refused("styles_override", style="solo.powder", eyes=1, stage="preview", confirm=True)
check("an override above the ceiling is refused: 409 above_ceiling, the ceiling named per count", says(x, 409, "above_ceiling") and x[3]["ceiling"] == {"1": "lab"}, x)
x = refused("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
check("... and live over a lab ceiling is refused for the ceiling first (the ticks do not matter)", says(x, 409, "above_ceiling"), x)
x = refused("styles_override", style=planned["id"], eyes=planned["eyes"][0], stage="lab", confirm=True)
check("a planned style cannot be switched: 409 not_switchable", says(x, 409, "not_switchable"), x)
check("nothing of that was written: still no object, revision 0", SO.load(force=True)["rev"] == 0 and not os.path.isfile(os.path.join(STORE, "ops", "styles", "overrides.json")))

res = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason="Soon again", reason_kind="soon", confirm=True)
check("lowering a live style to preview: changed, revision 1, effective preview for one eye, ceiling live, nothing held (the reason is not quality)",
      res["ok"] and res["result"] == "changed" and res["rev"] == 1 and res["effective"] == {"1": "preview"} and res["ceiling"] == {"1": "live"}
      and res["in_flight"] == "finish" and res["held"] is None, res)
check("it is in force at once on this instance: stage_of, orderable, previewable", CT.stage_of("celestial_gold", 1) == "preview" and not CT.orderable("celestial_gold", 1)
      and CT.orderable("celestial_gold", 2))
rec = SO.load()["styles"]["celestial_gold"]
check("the record keeps who, when, why and the kind; the object is the one file ops/styles/overrides.json",
      rec["by"] == "admin-v1" and rec["reason"] == "Soon again" and rec["reason_kind"] == "soon" and rec["stage_by_eyes"] == {"1": "preview"}
      and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", rec["at"]) and os.path.isfile(os.path.join(STORE, "ops", "styles", "overrides.json")), rec)
view = res["view"]
check("the reply carries the style's view: two ranges now (one eye preview, two to eight live)",
      [(g["eyes"], g["override"], g["effective"]) for g in view["ranges"]] == [([1, 1], "preview", "preview"), ([2, 8], None, "live")], view["ranges"])

res = act("styles_override", style="celestial_gold", eyes=1, stage="preview", confirm=True)
check("the same change again is 'same': no revision, no new entry", res["result"] == "same" and res["rev"] == 1 and SO.load(force=True)["rev"] == 1)
res = act("styles_override", style="celestial_gold", eyes="2-3", stage="lab", reason="capacity", reason_kind="capacity", confirm=True)
check("a range of eye counts: 2-3 is lab for both, the others untouched; capacity is not a quality reason, so nothing is held",
      res["after"] == {"2": "lab", "3": "lab"} and CT.stage_of("celestial_gold", 2) == "lab" and CT.stage_of("celestial_gold", 3) == "lab" and CT.stage_of("celestial_gold", 4) == "live"
      and res["in_flight"] == "finish" and res["held"] is None)
res = act("styles_override", style="celestial_gold", eyes=[1, 2, 3], stage="restore", confirm=True)
check("restore removes the override: back to the ceiling (live) for 1 to 3 eyes, and the record is gone",
      res["result"] == "changed" and all(CT.stage_of("celestial_gold", n) == "live" for n in (1, 2, 3)) and "celestial_gold" not in SO.load()["styles"], res)

SO.invalidate()
cur = SO.load(force=True)["rev"]
x = refused("styles_override", style="celestial_gold", eyes=1, stage="lab", confirm=True, rev=cur + 5)
check("a revision that is not the one on the disk is 409 stale_view (a second tab), and nothing is written", says(x, 409, "stale_view") and x[3]["rev"] == cur
      and SO.load(force=True)["rev"] == cur and CT.stage_of("celestial_gold", 1) == "live")
res = act("styles_override", style="celestial_gold", eyes=1, stage="lab", confirm=True, rev=cur)
check("the right revision is accepted", res["result"] == "changed" and res["rev"] == cur + 1)
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)

# a lab id made orderable through a ceiling patched for the length of the block (the ceilings are the registry's: a test may not raise one for good)
@contextlib.contextmanager
def ceiling(sid, stage, by_eyes=None, built=("singles",)):
    old = (CT.STYLES[sid]["stage"], dict(CT.STYLES[sid]["stage_by_eyes"]))
    CT.STYLES[sid]["stage"] = stage
    CT.STYLES[sid]["stage_by_eyes"] = dict(by_eyes or {})
    added = set(built) - CT.ENGINES_BUILT_EXTRA
    CT.ENGINES_BUILT_EXTRA.update(built)
    try:
        yield
    finally:
        CT.STYLES[sid]["stage"], CT.STYLES[sid]["stage_by_eyes"] = old
        CT.ENGINES_BUILT_EXTRA.difference_update(added)


PASS_L0 = {"L0": {"mean": 4.02, "min_axis": 3.84, "by": "Art Director"}}          # an independent score above the bar, with the scorer's name

reset()
with ceiling("solo.powder", "live"):
    x = refused("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
    check("live without any tick is refused: 409 needs_ticks naming L1 and L0", says(x, 409, "needs_ticks") and x[3]["missing"] == {"1": ["L1", "L0"]}, x)
    r1 = act("styles_override", style="solo.powder", eyes=1, tick={"L1": True})
    check("a tick alone needs no confirmation, changes no stage, and is dated and attributed",
          r1["result"] == "ticked" and r1["ticked"] == ["L1@1"] and SO.load()["styles"]["solo.powder"]["checklist"]["1"]["L1"]["by"] == "admin-v1"
          and re.fullmatch(r"\d{4}-\d\d-\d\dT.*Z", SO.load()["styles"]["solo.powder"]["checklist"]["1"]["L1"]["ticked_at"]) and SO.source("solo.powder", 1) is None, r1)
    x = refused("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
    check("L1 alone is not enough: L0 (the independent score) or the owner's written waiver is needed too", says(x, 409, "needs_ticks") and x[3]["missing"] == {"1": ["L0"]}, x)
    x = refused("styles_override", style="solo.powder", eyes=1, waiver={"text": "short"})
    check("a waiver is the owner's own words (at least 8 characters): a short one is a 400", says(x, 400, "bad_request"), x)
    r2 = act("styles_override", style="solo.powder", eyes=1, waiver={"text": "Splash and Powder scored together, I accept 3.96 for now"})
    check("the waiver is stored with its date and the key's kind, and it counts for L0",
          r2["waiver"] == "set" and SO.load()["styles"]["solo.powder"]["waiver"]["1"]["text"].startswith("Splash and Powder") and SO.load()["styles"]["solo.powder"]["waiver"]["1"]["by"] == "admin-v1"
          and SO.can_live(SO.load()["styles"]["solo.powder"], 1))
    r3 = act("styles_override", style="solo.powder", eyes=1, stage="live", reason="owner's tick", confirm=True)
    check("with L1 and the waiver the owner makes it live: effective live, orderable (its engine is built and its ceiling is live in this block)",
          r3["result"] == "changed" and r3["effective"] == {"1": "live"} and CT.stage_of("solo.powder", 1) == "live" and CT.orderable("solo.powder", 1), r3)
    r4 = act("styles_override", style="solo.powder", eyes=1, waiver=False)
    check("the waiver can be taken back; live stays as it was set (nothing re-checks a flip that was made), but the next flip would be refused",
          r4["waiver"] == "removed" and "1" not in SO.load()["styles"]["solo.powder"]["waiver"] and CT.stage_of("solo.powder", 1) == "live"
          and SO.missing_for_live(SO.load()["styles"]["solo.powder"], 1) == ["L0"])
    r5 = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": 4.02, "min_axis": 3.84, "by": "Art Director"}})
    sc = SO.load()["styles"]["solo.powder"]["checklist"]["1"]["L0"]
    check("L0 can be ticked with the independent score and the scorer's name; that is the evidence kept in the override file",
          sc["score"] == {"mean": 4.02, "min_axis": 3.84} and sc["director"] == "Art Director" and SO.can_live(SO.load()["styles"]["solo.powder"], 1) and r5["ticked"] == ["L0@1"], sc)
    r5b = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": 4.10, "min_axis": 3.90, "by": "Art Director"}})
    r5c = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": 4.10, "min_axis": 3.90, "by": "Art Director"}})
    check("the evidence of a tick can be corrected (the new score is kept, the tick stays), and the same evidence again is no change",
          r5b["result"] == "ticked" and SO.load()["styles"]["solo.powder"]["checklist"]["1"]["L0"]["score"] == {"mean": 4.1, "min_axis": 3.9} and r5c["result"] == "same")
    r6 = act("styles_override", style="solo.powder", eyes=1, tick={"L1": False})
    check("a tick can be taken back: L1 is gone and so is the right to a new flip to live", "L1" not in SO.load()["styles"]["solo.powder"]["checklist"]["1"]
          and r6["unticked"] == ["L1@1"] and SO.missing_for_live(SO.load()["styles"]["solo.powder"], 1) == ["L1"])
    x = refused("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
    check("so live is refused again", says(x, 409, "needs_ticks"), x)
    act("styles_override", style="solo.powder", eyes=1, stage="restore", confirm=True)
    check("restore puts it at the ceiling (live in this block): ticks are kept", CT.stage_of("solo.powder", 1) == "live" and "L0" in SO.load()["styles"]["solo.powder"]["checklist"]["1"])
section("3b. L0 is the independent score with its bar and the scorer's name, or the owner's written waiver (spec 1.6.1): a failing score never unlocks live")
reset()
with ceiling("solo.powder", "live"):
    act("styles_override", style="solo.powder", eyes=1, tick={"L1": True})

    def live_try():
        return refused("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)

    def l0_of(r):
        return r["l0"]["1"]

    x = refused("styles_override", style="solo.powder", eyes=1, tick={"L0": True})
    check("L0 has no bare tick: a tick of L0 is a 400 that says to send the score or the waiver (and a tick of false is still allowed, below)",
          says(x, 400, "bad_request") and "evidence" in x[3]["error"] and "waiver" in x[3]["error"], x)
    x0 = refused("styles_override", style="solo.powder", eyes=1, evidence={"L0": {}})
    check("an empty score is a 400 as well (it would make a mark that says nothing)", says(x0, 400, "bad_request"), x0)
    r = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": 1.0, "min_axis": 0.5, "by": "Art Director"}})
    x = live_try()
    check("a failing score (mean 1.0, axis 0.5) is RECORDED and shown with the scorer's name, and does not unlock live: 409 needs_ticks, L0 missing, its state below_bar",
          l0_of(r) == "below_bar" and SO.load()["styles"]["solo.powder"]["checklist"]["1"]["L0"]["score"] == {"mean": 1.0, "min_axis": 0.5}
          and says(x, 409, "needs_ticks") and x[3]["missing"] == {"1": ["L0"]} and x[3]["l0"] == {"1": "below_bar"} and not SO.can_live(SO.load()["styles"]["solo.powder"], 1)
          and SO.source("solo.powder", 1) is None, (r.get("l0"), x))
    got = []
    for mean, axis, want in ((3.96, 3.8, "pass"), (3.959, 3.8, "below_bar"), (3.96, 3.79, "below_bar"), (5, 5, "pass"), (3.99, 3.2, "below_bar"), (3.0, 4.5, "below_bar")):
        rr = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": mean, "min_axis": axis, "by": "Art Director"}})
        got.append((mean, axis, l0_of(rr), want, SO.can_live(SO.load()["styles"]["solo.powder"], 1) == (want == "pass")))
    check("the bar is exact: mean at least 3.96 AND no axis under 3.8 (3.96 and 3.8 pass, 3.959 or 3.79 do not, a high mean does not buy a low axis)", all(g[2] == g[3] and g[4] for g in got), got)
    rr = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": 4.3}})
    check("one number can be corrected without sending the other again (the old axis 4.5 stays: mean 4.3 and axis 4.5 pass)",
          l0_of(rr) == "pass" and SO.load()["styles"]["solo.powder"]["checklist"]["1"]["L0"]["score"] == {"mean": 4.3, "min_axis": 4.5})
    rr = act("styles_override", style="solo.powder", eyes=1, tick={"L0": False})
    check("an L0 mark can be taken back with a tick of false", "L0" not in SO.load()["styles"]["solo.powder"]["checklist"]["1"] and l0_of(rr) is None and rr["unticked"] == ["L0@1"])
    rr = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": 4.2, "min_axis": 4.0}})
    x = live_try()
    check("a score without the scorer's name is incomplete (the independence is the point of L0): recorded, state incomplete, live refused",
          l0_of(rr) == "incomplete" and says(x, 409, "needs_ticks") and x[3]["l0"] == {"1": "incomplete"}, (rr.get("l0"), x))
    rr = act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"by": "Art Director"}})
    check("... and with the name added to the same mark it passes", l0_of(rr) == "pass" and SO.can_live(SO.load()["styles"]["solo.powder"], 1))
    act("styles_override", style="solo.powder", eyes=1, evidence={"L0": {"mean": 3.1, "min_axis": 2.9}})
    act("styles_override", style="solo.powder", eyes=1, waiver={"text": "I looked at the real masters myself and accept this one"})
    cat = act("styles_catalogue", style="solo.powder")
    rg = cat["styles"][0]["ranges"][0]
    check("below the bar only the written waiver counts: the score stays recorded and shown, the state is waiver, live is allowed; the catalogue carries the bar and the state",
          cat["l0_bar"] == {"mean": 3.96, "min_axis": 3.8} and rg["l0"] == "waiver" and rg["checklist"]["L0"]["score"] == {"mean": 3.1, "min_axis": 2.9} and rg["missing_for_live"] == []
          and rg["waiver"]["text"].startswith("I looked"), rg)
    r = act("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
    e = SO.audit_read(limit=1)[0]
    check("with the waiver the owner makes it live, and the audit entry keeps where L0 stood (waiver) beside the ticks", r["result"] == "changed" and r["l0"] == {"1": "waiver"} and e["l0"] == {"1": "waiver"}, e.get("l0"))
    act("styles_override", style="solo.powder", eyes=1, waiver=False)
    check("take the waiver back and the failing score is what stands: below_bar, live is refused again", SO.l0_state(SO.load()["styles"]["solo.powder"], 1) == "below_bar")
    check("a stored mark with no score at all (a hand-edited file, or the old shape) does not count: incomplete",
          SO.l0_state({"checklist": {"1": {"L0": {"ticked_at": "2026-10-05T00:00:00Z", "by": "admin-v1"}}}}, 1) == "incomplete"
          and SO.missing_for_live({"checklist": {"1": {"L1": {"ticked_at": "x", "by": "y"}, "L0": {"ticked_at": "x", "by": "y"}}}}, 1) == ["L0"])
reset()
with ceiling("grp.collision", "live", built=("collision",)):
    act("styles_override", style="grp.collision", eyes="3-4", tick={"L1": True}, evidence=PASS_L0)
    act("styles_override", style="grp.collision", eyes=4, evidence={"L0": {"mean": 3.5}})
    st = act("styles_catalogue", style="grp.collision")["styles"][0]
    check("a count whose score was corrected is a range of its own (the ticks were made together, so equal times; the evidence differs), and the range says where its L0 stands",
          [(g["eyes"], g["l0"]) for g in st["ranges"]] == [([3, 3], "pass"), ([4, 4], "below_bar"), ([5, 8], None)], [(g["eyes"], g["l0"]) for g in st["ranges"]])
reset()
with ceiling("solo.powder", "live", built=()):
    reset()
    old_built = dict(CT._BUILT)
    CT._BUILT["singles"] = False                          # this deployment has no singles engine
    try:
        act("styles_override", style="solo.powder", eyes=1, tick={"L1": True}, evidence=PASS_L0)
        x = refused("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
    finally:
        CT._BUILT.clear()
        CT._BUILT.update(old_built)
    check("a style whose engine is not in this deployment cannot be made live, ticks or not: 409 no_engine", says(x, 409, "no_engine"), x)
reset()
with ceiling("grp.collision", "lab", {"3": "live", "4-8": "preview"}, built=("collision",)):
    act("styles_override", style="grp.collision", eyes=3, tick={"L1": True}, evidence=PASS_L0)
    x = refused("styles_override", style="grp.collision", eyes="3-5", stage="live", confirm=True)
    check("the ticks are per eye count: the Trio's ticks do not make four and five eyes live (and 4 to 8 are over their ceiling anyway)",
          x and x[1] == 409 and x[2] in ("above_ceiling", "needs_ticks"), x)
    r = act("styles_override", style="grp.collision", eyes=3, stage="live", confirm=True)
    check("three eyes, with their own ticks, are live", r["effective"] == {"3": "live"} and CT.orderable("grp.collision", 3) and not CT.orderable("grp.collision", 4))
    st = act("styles_catalogue", style="grp.collision")["styles"][0]
    check("the view groups the counts: 3 live with its ticks, 4 to 8 preview without",
          [(g["eyes"], g["effective"], sorted(g["checklist"])) for g in st["ranges"]] == [([3, 3], "live", ["L0", "L1"]), ([4, 8], "preview", [])], st["ranges"])
reset()

# ============================================================================================ 4. the default effective stage
section("4. the default effective stage: a v3 style is held at preview until the owner's tick (the hook of the cutover)")
reset()
with ceiling("solo.powder", "live"):
    CT.EFFECTIVE_DEFAULT = "preview"
    try:
        check("with the default at preview a v3 style whose ceiling is live is preview (not orderable, previewable); the legacy ids are not held to it",
              CT.stage_of("solo.powder", 1) == "preview" and not CT.orderable("solo.powder", 1) and CT.previewable("solo.powder", 1)
              and all(CT.stage_of(i, 3) == "live" and CT.orderable(i, 3) for i in LEGACY))
        act("styles_override", style="solo.powder", eyes=1, tick={"L1": True}, evidence=PASS_L0)
        check("ticks alone do not open it", CT.stage_of("solo.powder", 1) == "preview" and not CT.orderable("solo.powder", 1))
        cat = act("styles_catalogue", style="solo.powder")
        check("the catalogue says so: default_effective preview, the range is preview with a live ceiling, and live is within reach (nothing missing)",
              cat["default_effective"] == "preview" and cat["styles"][0]["ranges"][0]["effective"] == "preview" and cat["styles"][0]["ranges"][0]["ceiling"] == "live"
              and cat["styles"][0]["ranges"][0]["missing_for_live"] == [], cat["styles"][0]["ranges"])
        r = act("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
        check("the owner's flip makes it live: effective live, orderable; before was preview", r["effective"] == {"1": "live"} and CT.orderable("solo.powder", 1), r)
        r = act("styles_override", style="solo.powder", eyes=1, stage="restore", confirm=True)
        check("restore gives the DEFAULT (preview) and not the ceiling: only an explicit, ticked live is orderable", r["effective"] == {"1": "preview"}
              and CT.stage_of("solo.powder", 1) == "preview")
        r = act("styles_override", style="solo.powder", eyes=1, stage="lab", confirm=True)
        check("the owner can still take it lower than the default", r["effective"] == {"1": "lab"} and CT.stage_of("solo.powder", 1) == "lab")
        SO.invalidate()
        with CountingStore(fail=store.StorageError("injected")):
            check("when the switch cannot be read the page-facing stage is the ceiling capped at preview (the owner's lab cannot be read: preview is the most a guess may say), and the strict one raises",
                  CT.stage_of("solo.powder", 1) == "preview" and isinstance(raised(lambda: CT.orderable("solo.powder", 1)), store.StorageError))
    finally:
        CT.EFFECTIVE_DEFAULT = None
reset()
check("EFFECTIVE_DEFAULT is None today: nothing about a style's stage changes before the cutover sets it", CT.EFFECTIVE_DEFAULT is None
      and all(CT.stage_of(i, n) == CT.ceiling(i, n) for i in CT.ids() for n in range(1, 9)))

# ============================================================================================ 5. the orders in flight
section("5. taking a style back: the paid orders in flight finish or are held for the owner's look (decision DE1)")
reset()
DAY = time.strftime("%y%m%d")


def put_json(path, obj):
    full = os.path.join(STORE, *path.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def make_order(suffix, style, eyes, paid=True, delivery=False, review=False, withdrawn=False):
    o = f"{DAY}-{suffix}"
    put_json(f"orders/{o}/order.json", {"created_at": int(time.time()) - 600, "key_sha": "x" * 16})
    if paid:
        put_json(f"orders/{o}/paid.json", {"paid": True, "livemode": True, "paid_at": int(time.time()) - 300, "amount_total": 1997, "currency": "eur",
                                           "spec": {"style": style, "eyes": eyes, "layout": "single", "market": "eu", "lang": "en"}})
        put_json(f"orders/{o}/mail_delivery.json", {"state": "sent"})
    if delivery:
        put_json(f"orders/{o}/delivery.json", {"ok": True})
    if review:
        put_json(f"orders/{o}/review.json", {"reason": "other", "t": 1})
    if withdrawn:
        put_json(f"orders/{o}/withdrawn.json", {"t": 1})
    return o


oa = make_order("aaaa0001", "celestial_gold", 1)                       # in flight, the style and the count that are taken back
ob = make_order("aaaa0002", "celestial_gold", 2)                       # another eye count
oc = make_order("aaaa0003", "studio_black", 1)                         # another style
od = make_order("aaaa0004", "celestial_gold", 1, delivery=True)        # ready
oe = make_order("aaaa0005", "celestial_gold", 1, review=True)          # held already
of_ = make_order("aaaa0006", "celestial_gold", 1, paid=False)          # not paid
og = make_order("aaaa0007", "celestial_gold", 1, withdrawn=True)       # withdrawn
oh = make_order("aaaa0008", "celestial_gold", 1)                       # a second one in flight


def review_of(o):
    path = os.path.join(STORE, "orders", o, "review.json")
    return json.load(open(path, encoding="utf-8")) if os.path.isfile(path) else None


r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason="the cloud plates look dull", reason_kind="quality", confirm=True)
check("a quality rollback of a style that was orderable defaults to HOLD: the two orders in flight of that style and count are held, nobody else",
      r["in_flight"] == "hold" and r["held"]["count"] == 2 and sorted(r["held"]["orders"]) == sorted([oa, oh]), r["held"])
check("they carry review.json with the reason style_rolled_back (the hold every other hold uses); the other orders were not touched",
      review_of(oa)["reason"] == "style_rolled_back" and review_of(oh)["reason"] == "style_rolled_back" and review_of(ob) is None and review_of(oc) is None
      and review_of(od) is None and review_of(oe)["reason"] == "other" and review_of(of_) is None and review_of(og) is None)
check("the owner's reminder of a held order says why and what to do (steps.hold_text), the daily clean-up's index has them",
      all(os.path.isfile(os.path.join(STORE, "cleanup", "review", f"{o}.json")) for o in (oa, oh))
      and (lambda t: t and "style_rolled_back" not in t[0] and "admin page" in t[0])(__import__("_lib.styles.steps", fromlist=["x"]).hold_text("style_rolled_back", oa)))
check("the audit entry records what he chose and how many were held", (lambda e: e["in_flight"] == "hold" and e["held"]["count"] == 2 and e["reason_kind"] == "quality")(SO.audit_read(limit=1)[0]))
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
og2 = make_order("aaaa0009", "celestial_gold", 1)
r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason="capacity", reason_kind="capacity", confirm=True)
check("a capacity rollback defaults to FINISH: nothing is held, the order made since is untouched", r["in_flight"] == "finish" and r["held"] is None and review_of(og2) is None)
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="capacity", in_flight="hold", confirm=True)
check("the owner can choose against the default: hold for a capacity reason holds the order that is in flight and was not held yet",
      r["in_flight"] == "hold" and r["held"]["orders"] == [og2] and review_of(og2)["reason"] == "style_rolled_back", r["held"])
r = act("styles_override", style="celestial_gold", eyes=1, stage="lab", reason_kind="quality", confirm=True)
check("lowering a style that is not orderable any more asks nothing about orders (preview to lab: in_flight None, nothing held)", r["in_flight"] is None and r["held"] is None)
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
r = act("styles_override", style="celestial_gold", eyes=1, stage="lab", reason_kind="quality", in_flight="finish", confirm=True)
check("finish is honoured for a quality reason too", r["in_flight"] == "finish" and r["held"] is None)
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
r = act("styles_override", style="celestial_gold", eyes=1, tick={"L3": True})
check("a tick is not a rollback: nothing asked, nothing held", r["in_flight"] is None and r["held"] is None)
check("an invalid in_flight is a 400", says(refused("styles_override", style="celestial_gold", eyes=1, stage="lab", in_flight="burn", confirm=True), 400, "bad_request"))
shutil.rmtree(os.path.join(STORE, "orders"), ignore_errors=True)
shutil.rmtree(os.path.join(STORE, "cleanup"), ignore_errors=True)
reset()

section("5b. a hold that stops half way is reported as that, never as done, and the same request again finishes it")
import unittest.mock as mock  # noqa: E402
REAL_LIST = store.list_all
oa2 = make_order("bbbb0001", "celestial_gold", 1)


def fail_orders(folder, *a, **k):
    if folder == "orders":
        raise store.StorageError("list orders: HTTP 503")
    return REAL_LIST(folder, *a, **k)


store.list_all = fail_orders
try:
    r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", reason="plates", confirm=True)
finally:
    store.list_all = REAL_LIST
e = SO.audit_read(limit=1)
check("a storage error while the orders are listed does not undo or hide the change: the action answers (no 503), the override is saved, and held says error and incomplete with 0 held",
      r["result"] == "changed" and CT.stage_of("celestial_gold", 1) == "preview" and r["held"]["error"] == "StorageError" and r["held"]["incomplete"] is True and r["held"]["count"] == 0
      and review_of(oa2) is None and r["in_flight"] == "hold"
      and any("held 0 incomplete" in (g.get("detail") or "") for g in ops.a_audit({}, WHO)["entries"]), r.get("held"))
check("... and its audit entry IS written, with the same facts (it records the change and that the hold did not happen)",
      e and e[0]["style"] == "celestial_gold" and e[0]["held"]["incomplete"] is True and e[0]["held"]["error"] == "StorageError" and e[0]["in_flight"] == "hold" and r["audit_written"] is True, e)
r2 = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", confirm=True)
check("the same request again WITHOUT in_flight changes nothing and holds nothing (result same: the default is not a standing order)", r2["result"] == "same" and r2["held"] is None and review_of(oa2) is None)
r3 = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", in_flight="hold", confirm=True)
e = SO.audit_read(limit=1)[0]
check("the same request again WITH in_flight hold finishes it: result same (the stage is unchanged), the order in flight is held now, and the retry has its own audit entry (kind hold)",
      r3["result"] == "same" and r3["in_flight"] == "hold" and r3["held"]["orders"] == [oa2] and r3["held"]["incomplete"] is False and review_of(oa2)["reason"] == "style_rolled_back"
      and e["kind"] == "hold" and e["held"]["orders"] == [oa2] and e["style"] == "celestial_gold" and r3["audit_written"] is True, (r3.get("held"), e))
r4 = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", in_flight="hold", confirm=True)
check("and once more is harmless: nothing left to hold, 0 held, the order already held is left alone, complete", r4["held"]["count"] == 0 and r4["held"]["incomplete"] is False
      and review_of(oa2)["reason"] == "style_rolled_back")
check("a hold entry is not a flip of the catalogue (the price test's page lists flips only)", abtest.catalogue_changes(SO.audit_read(limit=20), "xk_test") == [])
r5 = act("styles_override", style="celestial_gold", eyes=1, tick={"L3": True}, in_flight="hold")
check("a tick with in_flight hold holds nothing (no stage was asked for)", r5["held"] is None and r5["result"] == "ticked")
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
r6 = act("styles_override", style="celestial_gold", eyes=1, stage="restore", in_flight="hold", confirm=True)
check("a style that is live is never held by the retry (the stage is the ceiling: same, nothing asked, nothing held)", r6["result"] == "same" and r6["held"] is None and r6["in_flight"] is None)
reset()
shutil.rmtree(os.path.join(STORE, "orders"), ignore_errors=True)
shutil.rmtree(os.path.join(STORE, "cleanup"), ignore_errors=True)

ob2 = make_order("bbbb0002", "celestial_gold", 1)
real_put_ = store.put


def put_fail(path, *a, **k):
    if path.endswith("review.json"):
        raise store.StorageError("put review: HTTP 500")
    return real_put_(path, *a, **k)


store.put = put_fail
try:
    r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", confirm=True)
finally:
    store.put = real_put_
e = SO.audit_read(limit=1)[0]
check("an order whose review.json could not be stored is NOT counted as held (pay.mark_review never raises, so the hold reads it back): 0 held, the order named in failed, incomplete, no review.json",
      r["held"]["count"] == 0 and r["held"]["failed"] == [ob2] and r["held"]["incomplete"] is True and review_of(ob2) is None and e["held"]["failed"] == [ob2], r["held"])
r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", in_flight="hold", confirm=True)
check("... and the same request again, with the storage back, holds it for real: 1 held, read back, complete", r["held"]["count"] == 1 and r["held"]["orders"] == [ob2] and r["held"]["incomplete"] is False
      and review_of(ob2)["reason"] == "style_rolled_back")
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
reset()
shutil.rmtree(os.path.join(STORE, "orders"), ignore_errors=True)
shutil.rmtree(os.path.join(STORE, "cleanup"), ignore_errors=True)

oc2, od2 = make_order("bbbb0003", "celestial_gold", 1), make_order("bbbb0004", "celestial_gold", 1)
real_row = ops.order_row


def row_fail(o, *a, **k):
    if o == oc2:
        raise store.StorageError("read order: HTTP 500")
    return real_row(o, *a, **k)


ops.order_row = row_fail
try:
    r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", confirm=True)
finally:
    ops.order_row = real_row
check("an order record that cannot be read is counted as unread (not skipped in silence): the readable one is held, the other is not, and the reply says incomplete",
      r["held"]["orders"] == [od2] and r["held"]["unread"] == 1 and r["held"]["incomplete"] is True and review_of(oc2) is None and review_of(od2) is not None, r["held"])
r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", in_flight="hold", confirm=True)
check("... and the same request again holds the one that was unread", r["held"]["orders"] == [oc2] and r["held"]["unread"] == 0 and review_of(oc2) is not None)
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
reset()
shutil.rmtree(os.path.join(STORE, "orders"), ignore_errors=True)
shutil.rmtree(os.path.join(STORE, "cleanup"), ignore_errors=True)

# a hold that runs short of time says so
oe2 = make_order("bbbb0005", "celestial_gold", 1)
with mock.patch.object(L, "time_left", lambda default=L.BUDGET: 7.0):
    r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="quality", confirm=True)
check("a hold that has no time left to list the orders says more and incomplete (nothing is held, nothing is claimed)", r["held"]["more"] is True and r["held"]["incomplete"] is True and r["held"]["count"] == 0
      and review_of(oe2) is None, r["held"])
act("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)
reset()
shutil.rmtree(os.path.join(STORE, "orders"), ignore_errors=True)
shutil.rmtree(os.path.join(STORE, "cleanup"), ignore_errors=True)

# ============================================================================================ 6. a running price test
section("6. a running price test: the flip needs the owner's acknowledgement, and is written into the test's page")
reset()
real_running = ops._running_price_tests
ops._running_price_tests = lambda: ["xk_test"]
try:
    x = refused("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="soon", confirm=True)
    check("a flip that changes what can be ordered while a test runs is refused until he says he has read the line: 409 price_test_running with the keys",
          says(x, 409, "price_test_running") and x[3]["keys"] == ["xk_test"] and CT.stage_of("celestial_gold", 1) == "live", x)
    r = act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="soon", price_test_seen=True, confirm=True)
    check("with price_test_seen it goes through: the owner decides, the server does not block", r["result"] == "changed" and r["price_test"] == ["xk_test"] and CT.stage_of("celestial_gold", 1) == "preview")
    e = SO.audit_read(limit=1)[0]
    check("the audit entry names the test that was running and that he had read the line", e["price_test"] == ["xk_test"] and e["price_test_seen"] is True)
    r = act("styles_override", style="celestial_gold", eyes=1, stage="lab", confirm=True)
    check("preview to lab changes nothing that can be ordered: no acknowledgement needed, no test named", r["price_test"] == [] and r["result"] == "changed")
    r = act("styles_override", style="celestial_gold", eyes=1, tick={"L2": True})
    check("a tick needs none either", r["result"] == "ticked")
    ch = abtest.catalogue_changes(SO.audit_read(limit=20), "xk_test")
    check("abtest.catalogue_changes shows the test's page the flip that was made inside its window (and not another test's)",
          len(ch) == 1 and ch[0]["style"] == "celestial_gold" and ch[0]["before"] == {"1": "live"} and ch[0]["after"] == {"1": "preview"} and abtest.catalogue_changes(SO.audit_read(limit=20), "other") == [])
    view = abtest.admin_view(lambda n: [], audit=[], catalogue=SO.audit_read(limit=20))
    check("and the experiments' view carries a `catalogue` list on every card (empty when nothing changed), nothing else of the view changed shape",
          view["ok"] and all(isinstance(x_.get("catalogue"), list) for x_ in view["experiments"]))
finally:
    ops._running_price_tests = real_running
check("with no test running _running_price_tests is empty (the real one)", real_running() == [])
reset()
real_rk = abtest.running_keys


def rk_fail(*a, **k):
    raise store.StorageError("experiments state: HTTP 500")


abtest.running_keys = rk_fail
try:
    rev_before = SO.load(force=True)["rev"]
    e = raised(lambda: act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="other", confirm=True))
    state_e = (SO.load(force=True)["rev"], CT.stage_of("celestial_gold", 1), SO.audit_read(limit=5))
    e2 = raised(lambda: act("styles_override", style="celestial_gold", eyes=1, tick={"L3": True}))
finally:
    abtest.running_keys = real_rk
check("when the price tests cannot be looked up a flip that changes what can be ordered is NOT let through without the acknowledgement: the error is raised (503), nothing is saved, nothing is logged",
      isinstance(e, store.StorageError) and state_e == (rev_before, "live", []), (e, state_e))
check("... a tick changes nothing that can be ordered and does not need the lookup", e2 is None and SO.load(force=True)["rev"] == rev_before + 1)
reset()

# ============================================================================================ 7. the audit log and the limits
section("7. the audit log of the switch and the limits of the attention card")
reset()
act("styles_override", style="celestial_gold", eyes="1-2", stage="preview", reason="Soon again", reason_kind="soon", confirm=True)
act("styles_override", style="supernova", eyes=1, stage="lab", reason="plates", reason_kind="quality", in_flight="finish", confirm=True)
au = act("styles_audit")
check("styles_audit: the entries newest first, each with who, what, why, the override and the effective stage before and after, the ceiling, the revision, the numbers",
      au["ok"] and [e["style"] for e in au["entries"]] == ["supernova", "celestial_gold"] and all(e["kind"] == "override" and e["by"] == "admin-v1" and e["rev"] >= 1 for e in au["entries"])
      and au["entries"][1]["eyes"] == [1, 2] and au["entries"][1]["effective_before"] == {"1": "live", "2": "live"} and au["entries"][1]["effective_after"] == {"1": "preview", "2": "preview"}
      and au["entries"][1]["ceiling"] == {"1": "live", "2": "live"} and au["entries"][1]["reason"] == "Soon again" and au["entries"][1]["in_flight"] == "finish"
      and isinstance(au["entries"][1]["numbers"], dict) and set(au["entries"][1]["numbers"]) == {"1", "2"}, au["entries"][:1])
check("the numbers of an entry are the set-level numbers at that moment with n (no sets yet: n 0, rates None, a line only for two or more eyes)",
      au["entries"][1]["numbers"]["1"] == {"n": 0, "first_pass": None, "with_retake": None, "unknown": 0, "line_ok": None, "why": [], "partial": False}
      and au["entries"][1]["numbers"]["2"]["line_ok"] is False and "n_low" in au["entries"][1]["numbers"]["2"]["why"], au["entries"][1]["numbers"])
check("the filter by style and the limit", [e["style"] for e in act("styles_audit", style="supernova")["entries"]] == ["supernova"] and len(act("styles_audit", limit=1)["entries"]) == 1
      and says(refused("styles_audit", style="nope"), 400, "bad_request"))
SO.audit_put({"kind": "override", "by": "admin-v1", "style": "studio_black", "eyes": [1], "stage": "lab", "rev": 0}, now=time.time() - 3 * 86400)
old_entries = SO.audit_read(limit=50)
check("the audit log is read day by day from the days that have entries, newest first, across days (an entry of three days ago is the last)",
      old_entries[-1]["style"] == "studio_black" and [e["t"] for e in old_entries] == sorted((e["t"] for e in old_entries), reverse=True) and len(old_entries) == 3
      and len(SO.audit_read(limit=50, days=1)) == 2, [e["style"] for e in old_entries])
generic = ops.a_audit({}, WHO)["entries"]
check("the generic admin audit has one short line per change as well (action styles_override, the style and the new stage in its detail)",
      [e for e in generic if e["action"] == "styles_override" and e["ok"] and "celestial_gold" in (e.get("detail") or "")] != [])
x = refused("styles_override", style="solo.powder", eyes=1, stage="preview", confirm=True)
generic = ops.a_audit({}, WHO)["entries"]
check("a refusal is in the generic log too, with its reason code", any(e["action"] == "styles_override" and e["ok"] is False and e["result"] == "above_ceiling" for e in generic))
check("an audit entry holds no e-mail address even when the reason has one",
      (lambda: (act("styles_override", style="supernova", eyes=1, stage="restore", reason="write to a@b.example", reason_kind="other", confirm=True), "a@b.example" not in json.dumps(SO.audit_read(limit=3)))[1])())
real_put2 = store.put


def audit_fail(path, *a, **k):
    if path.startswith(SO.AUDIT_DIR + "/"):
        raise store.StorageError("put audit: HTTP 500")
    return real_put2(path, *a, **k)


store.put = audit_fail
try:
    ra_ = act("styles_override", style="supernova", eyes=1, stage="preview", reason_kind="soon", confirm=True)
finally:
    store.put = real_put2
check("a log line that could not be stored does not undo the change and is not hidden: the reply says audit_written false (and true when it was written)",
      ra_["result"] == "changed" and ra_["audit_written"] is False and CT.stage_of("supernova", 1) == "preview"
      and act("styles_override", style="supernova", eyes=1, stage="restore", confirm=True)["audit_written"] is True)
import inspect  # noqa: E402
from _lib import cleanup as CL  # noqa: E402
SO.audit_put({"kind": "override", "by": "admin-v1", "style": "studio_black", "eyes": [1], "stage": "lab", "held": {"count": 1, "orders": ["260101-abcd1234"]}, "rev": 0}, now=time.time() - 800 * 86400)
n_before = len(SO.audit_read(limit=100, days=2000))
res_ = CL._audit(True, 0, lambda m: None, top=CL.STYLE_AUDIT_TOP)
left_ = SO.audit_read(limit=100, days=2000)
check("the style audit log has a retention rule like ops/audit (it names the order numbers a hold caught): an entry older than 24 months is deleted by the clean-up, the others stay",
      CL.STYLE_AUDIT_TOP == SO.AUDIT_DIR and res_["files"] == 1 and len(left_) == n_before - 1 and all(x["style"] != "studio_black" or x["t"] > time.time() - 700 * 86400 for x in left_)
      and len(left_) >= 3, (res_, n_before, len(left_)))
check("... and the daily run calls it (the step is wired into cleanup.run, with its own counts)", "top=STYLE_AUDIT_TOP" in inspect.getsource(CL.run) and 'res["style_audit"]' in inspect.getsource(CL.run))
lim = act("styles_catalogue")
rev0 = lim["rev"]
check("styles_limits needs the confirmation, a share from 0 to 1 and min_n a whole number; an unknown key is a 400",
      all(says(refused("styles_limits", **b), 400, "bad_request") for b in ({"limits": {"error_rate": 0.1}}, {"limits": {"error_rate": 3}, "confirm": True},
                                                                      {"limits": {"min_n": 1.5}, "confirm": True}, {"limits": {"nope": 1}, "confirm": True}, {"limits": {}, "confirm": True},
                                                                      {"confirm": True})))
r = act("styles_limits", limits={"error_rate": 0.2, "min_n": 5}, confirm=True, rev=rev0)
check("limits are set with the same object and revision, and are in the audit log", r["limits"]["error_rate"] == 0.2 and r["limits"]["min_n"] == 5 and r["limits"]["review_rate"] == 0.10
      and r["rev"] == rev0 + 1 and act("styles_audit", limit=1)["entries"][0]["kind"] == "limits" and act("styles_catalogue")["limits"]["min_n"] == 5)
check("a limits change with an old revision is 409 stale_view", says(refused("styles_limits", limits={"min_n": 9}, confirm=True, rev=rev0), 409, "stale_view"))
check("the overrides survive a limits change and the limits survive an override change",
      CT.stage_of("celestial_gold", 1) == "preview" and (lambda: (act("styles_override", style="celestial_gold", eyes=3, stage="lab", confirm=True), SO.load()["limits"]["min_n"] == 5)[1])())
reset()

# ============================================================================================ 8. the events
section("8. the events: every field whitelisted and a code, the set-level funnel against a replay, again, the slices, the spread of the times, the demand")
import ast  # noqa: E402
import random  # noqa: E402
import unittest.mock as mock  # noqa: E402
from _lib import style_stats as SS  # noqa: E402
spec_c = importlib.util.spec_from_file_location("compose", os.path.join(API, "compose.py"))
CMP = importlib.util.module_from_spec(spec_c)
spec_c.loader.exec_module(CMP)


def record_calls():
    """Every E.record, E.record_many and E.error call of api/ whose kind is a literal: (file, kind, keyword names, has a ** splat)."""
    out = []
    for root, _dirs, files in os.walk(API):
        if "__pycache__" in root or os.sep + "_assets" in root:
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            tree = ast.parse(read(path))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("record", "record_many") and node.args
                        and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    out.append((os.path.relpath(path, API), node.args[0].value, [k.arg for k in node.keywords if k.arg], any(k.arg is None for k in node.keywords)))
    return out


calls = record_calls()
bad_kind = [c for c in calls if c[1] not in E.FIELDS]
bad_field = [(c[0], c[1], k) for c in calls if c[1] in E.FIELDS for k in c[2] if not k.startswith("_") and k not in E.FIELDS[c[1]] and k != "ms"]
check("every E.record call of api/ names a kind that events.FIELDS has (the scan found " + str(len(calls)) + " calls)", calls and not bad_kind, bad_kind)
check("... and every keyword it passes is a field of that kind (a field outside FIELDS would be dropped silently: the scan makes it loud)", not bad_field, bad_field)
req = CMP._request({"style": "solo.gold", "again": True, "retake": 2, "lang": "lt", "market": "eu"})
ef = CMP._event_fields(req, "solo.gold", 1, "single", "1:1", 1024, "ok", True, "solo.gold", "echo", "kiss", clean=False, tile=True, cls="own")
sent = []
with mock.patch.object(E, "record", lambda kind, **f: sent.append((kind, f)) or True):
    CMP._set_event(req, 2, [], "duo.kiss_collision")
    CMP._help({"action": "help", "route": "soon", "style": "solo.radiance", "eyes": 1, "lang": "lt"})
    CMP._help({"action": "help", "route": "manual", "eyes": 2, "why": "lid_sectors_outer", "lang": "de"})
names = [("compose", ef)] + sent
check("the fields the compose handler builds as a dict (a picture's, a set's, the help beacon's) are all fields of their kind, again and market and lang among them",
      all(set(f) <= set(E.FIELDS[k]) | {"_wait"} for k, f in names) and ef["again"] is True and ef["market"] == "eu" and ef["lang"] == "lt"
      and [k for k, _ in sent] == ["compose", "help", "help"] and sent[0][1]["again"] is True and sent[1][1]["style"] == "solo.radiance" and sent[1][1]["route"] == "soon"
      and "style" not in sent[2][1], names)
with mock.patch.object(E, "record", lambda kind, **f: sent.append((kind, f)) or True):
    CMP._help({"action": "help", "route": "soon", "style": "no such id", "eyes": 99, "lang": "xx"})
    e1 = raised(lambda: CMP._help({"action": "help", "route": "blocked", "style": "solo.radiance"}))
check("an unknown style in a soon click is counted as unknown, the eye count and the language are bounded, and a customer cannot send the server's own route (blocked is a 400)",
      sent[-1][1]["style"] == "unknown" and sent[-1][1]["eyes"] == 1 and sent[-1][1]["lang"] == "en" and isinstance(e1, L.ClientError), (sent[-1], e1))
hostile = {"c": ["A B", "a@b.co", "x" * 80, "UPPER", "", 5, True, "a b", "-x"], "n": ["5", True, float("inf"), float("nan"), 10 ** 12, None], "b": ["true", 1, None, "yes"]}
leaks = []
for kind, spec_f in E.FIELDS.items():
    for field, typ in spec_f.items():
        if typ == "o":
            continue
        for v in hostile[typ]:
            if field in E.build(kind, {field: v}):
                leaks.append((kind, field, v))
check("codes only: no field of any kind keeps a value of the wrong type, a code with a space, an at sign or an upper case letter, a number that is not finite (the field is dropped)", not leaks, leaks[:5])
check("the new fields are in the whitelist: compose again, help style; and the price test's and the master's are unchanged in kind",
      E.FIELDS["compose"]["again"] == "b" and E.FIELDS["help"]["style"] == "c" and set(E.FIELDS) == {"analyze", "deglare", "enhance", "compose", "master", "error", "help", "checkout", "exp"})

section("8b. the set-level funnel equals a replay of the recorded events; again; the slices")
rng = random.Random(13)
evs = []
for i in range(120):
    f = {"tiles": 0, "eyes": rng.choice([1, 2, 2, 3]), "gate": rng.choice(["ok", "ok", "ok", "lid_sectors_outer", "lid_ring_outliers", "unknown"]),
         "cls": rng.choice(["own", "dark_brown", "grey"]), "retake": rng.choice([0, 0, 0, 1, 2]), "lang": rng.choice(["en", "lt", "de"])}
    if rng.random() < 0.6:
        f["market"] = rng.choice(["eu", "au"])
    if rng.random() < 0.3:
        f["again"] = True
    evs.append(E.build("compose", f))
agg = E.summarize(evs)


def replay(pred=lambda e: True, cls=False):
    rows = {}
    for e in evs:
        if not pred(e) or e.get("again"):
            continue
        key = (e["eyes"], e["cls"]) if cls else e["eyes"]
        row = rows.setdefault(key, {"first": 0, "first_pass": 0, "unknown": 0, "r1": 0, "r1_pass": 0, "r2": 0, "r2_pass": 0})
        r = min(2, e["retake"])
        if e["gate"] == "unknown":
            row["unknown"] += 1
        elif r == 0:
            row["first"] += 1
            row["first_pass"] += e["gate"] == "ok"
        else:
            row[f"r{r}"] += 1
            row[f"r{r}_pass"] += e["gate"] == "ok"
    return rows


def from_report(rows, cls=False):
    return {((r["eyes"], r["cls"]) if cls else r["eyes"]): {"first": r["first"], "first_pass": r["first_pass"], "unknown": r["unknown"], "r1": r["retake1"], "r1_pass": r["retake1_pass"],
                                                           "r2": r["retake2"], "r2_pass": r["retake2_pass"]} for r in rows}


check("the funnel of the summary equals a replay of the events, set by set (first photo, pass, unknown, one retake, two or more), with n",
      from_report(SS.funnel(SS.table(agg, "compose_funnel"))) == replay(), (from_report(SS.funnel(SS.table(agg, "compose_funnel"))), replay()))
check("... and by the set's colour class", from_report(SS.funnel(SS.table(agg, "compose_funnel_cls"), by_class=True), cls=True) == replay(cls=True))
check("a request with again is not a new set: the funnel's first-photo total is the events without again, and the same events with the flag off count more",
      sum(r["first"] + r["unknown"] for r in SS.funnel(SS.table(agg, "compose_funnel"))) < sum(1 for e in evs if e["retake"] == 0)
      and sum(1 for e in evs if e.get("again")) > 10)
for sl, pred in (("market:au", lambda e: e.get("market") == "au"), ("market:eu", lambda e: e.get("market") == "eu"), ("lang:lt", lambda e: e["lang"] == "lt"),
                 ("lang:de", lambda e: e["lang"] == "de")):
    check(f"the slice {sl} equals the replay of the events that carry it (a filter needs no raw event)", from_report(SS.funnel(SS.table(agg, "compose_funnel", sl))) == replay(pred))
def total(rows):
    return sum(r["first"] + r["unknown"] + r["retake1"] + r["retake2"] for r in rows)


check("an event without a market is in the base funnel and in no market slice (the two market slices together hold less than the whole)",
      total(SS.funnel(SS.table(agg, "compose_funnel"))) > sum(total(SS.funnel(SS.table(agg, "compose_funnel", s_))) for s_ in ("market:au", "market:eu"))
      and sum(1 for e in evs if not e.get("market") and not e.get("again")) > 0)
check("merging two days adds the tables and the slices", (lambda m: SS.table(m, "compose_funnel", "market:au") == {k: 2 * v for k, v in SS.table(agg, "compose_funnel", "market:au").items()}
                                                         and SS.table(m, "compose_funnel") == {k: 2 * v for k, v in SS.table(agg, "compose_funnel").items()})(E.merge(agg, agg)))
check("the funnel by colour class is not sliced (class by language by market is too many cells for a day's counts)", not [k for k in agg["compose_slice"] if "|compose_funnel_cls|" in k])
def day_of(valid):
    """6000 compose events: the combinations a real day can hold (a style asked only for eye counts it takes) or, for the stress test, every combination at all."""
    day = E.empty()
    rng2 = random.Random(7)
    ids = [i for i in CT.ids() if CT.STYLES[i]["tile_order"]]
    for _ in range(6000):
        sid = rng2.choice(ids)
        lo, hi = CT.eyes_range(sid)
        f = {"style": sid, "eyes": rng2.randint(lo, hi) if valid else rng2.randint(1, 8), "stage": rng2.choice(["preview", "live"]), "size": rng2.choice([480, 1024]),
             "tile": rng2.random() < 0.7, "tiles": rng2.randint(0, 6),
             "gate": rng2.choice(["ok", "unknown", "lid_sectors_outer", "lid_ring_outliers", "lid_sectors_inner", "fill_dark", "fill_edge", "fill_low"]),
             "retake": rng2.randint(0, 3), "lang": rng2.choice(["en", "de", "lt", "hu"]), "market": rng2.choice(["eu", "au", "hu", "lt", "us"]), "cls": rng2.choice(["own", "dark_brown", "grey"]),
             "ms": rng2.randint(100, 80000), "pick": rng2.random() < 0.3, "fallback": rng2.choice(["kiss", "stack_contrast", "none", "kiss"])}
        E.add(day, E.build("compose", f))
    return day


real_day, stress_day = day_of(True), day_of(False)
kb_real, kb_stress = len(json.dumps(real_day)) / 1024, len(json.dumps(stress_day)) / 1024
check("a day of 6000 compose events with the combinations a real day can hold (every language, market, gate code and retake) is a few hundred KB at most, and the stress test with EVERY combination "
      "(a style asked for eye counts it does not take) stays under the 2 MB a stored day is read back with", kb_real < 300 and kb_stress < 1024 and E.ROLLUP_MAX_BYTES == 2 << 20, (round(kb_real), round(kb_stress)))
check("the demand for a live style is in the day's table but not in a slice (only the styles that are Soon are filtered by language and market)",
      any("|live|" in k for k in real_day["compose_demand"]) and not any("|compose_demand|" in k and "|live|" in k for k in real_day["compose_slice"])
      and any("|compose_demand|" in k and "|preview|" in k for k in real_day["compose_slice"]))
rowsf = {r["eyes"]: r for r in SS.funnel(SS.table(agg, "compose_funnel"))}
check("rate_retake is (first pass + the failed sets that passed after one retake, at most the failed ones) over the first-photo sets, and never above 1",
      all(r["first"] == 0 or abs(r["rate_retake"] - (r["first_pass"] + min(r["first"] - r["first_pass"], r["retake1_pass"])) / r["first"]) < 1e-4 and r["rate_retake"] <= 1
          for r in rowsf.values()) and rowsf[2]["rate_first"] == round(rowsf[2]["first_pass"] / rowsf[2]["first"], 4))
check("one eye has no opening line (a set of one eye always has an advisory style); two or more have one", rowsf[1]["line"] is None and rowsf[2]["line"] is not None and rowsf[3]["line"] is not None)

section("8c. the opening line (spec 1.6.2 rule 2) is one function")
base = {"eyes": 2, "first": 40, "first_pass": 26, "rate_first": 0.65, "rate_retake": 0.95}
check("green when n is 30 or more, the first photo passes 50 percent or more and 75 percent or more with one retake", SS.opening_line(base)["ok"] and SS.opening_line(base)["why"] == [])
check("red with each reason named: too few sets (n_low), the first photo (first_low), the retake (retake_low); all three can hold at once",
      SS.opening_line(dict(base, first=29))["why"] == ["n_low"] and SS.opening_line(dict(base, rate_first=0.49))["why"] == ["first_low"]
      and SS.opening_line(dict(base, rate_retake=0.74))["why"] == ["retake_low"] and SS.opening_line(dict(base, first=3, rate_first=0.1, rate_retake=0.2))["why"] == ["n_low", "first_low", "retake_low"]
      and SS.opening_line(dict(base, rate_first=None, rate_retake=None))["ok"] is False)
check("the thresholds are the spec's: 30 sets, 0.50, 0.75", (SS.OPEN_MIN_SETS, SS.OPEN_FIRST, SS.OPEN_RETAKE) == (30, 0.5, 0.75)
      and SS.opening_line(dict(base, first=30, rate_first=0.5, rate_retake=0.75))["ok"])
fn_ = SS.flip_numbers([agg], [1, 2, 3, 8])
check("flip_numbers (what the audit entry keeps) is the funnel's own numbers for the counts asked, and zeros with no rates for a count with no set",
      fn_["2"] == {"n": rowsf[2]["first"], "first_pass": rowsf[2]["rate_first"], "with_retake": rowsf[2]["rate_retake"], "unknown": rowsf[2]["unknown"],
                   "line_ok": rowsf[2]["line"]["ok"], "why": rowsf[2]["line"]["why"]} and fn_["8"]["n"] == 0 and fn_["8"]["first_pass"] is None and fn_["1"]["line_ok"] is None)

section("8d. the spread of the render times, the demand for a style that cannot be bought yet, errors, review, fallbacks, the gate per style, the attention card")
check("the buckets: 250 ms is the first, one above a bound is the next, above the last bound is the open bucket",
      (E.hist_bucket(0), E.hist_bucket(250), E.hist_bucket(251), E.hist_bucket(64000), E.hist_bucket(64001)) == (0, 0, 1, len(E.HIST_MS) - 1, len(E.HIST_MS)))
hist_evs = [E.build("compose", {"style": "solo.gold", "eyes": 1, "ms": 400, "stage": "live", "size": 1024, "pick": True}) for _ in range(50)] + \
           [E.build("compose", {"style": "solo.gold", "eyes": 1, "ms": 1800, "stage": "live", "size": 1024, "pick": False}) for _ in range(45)] + \
           [E.build("compose", {"style": "solo.gold", "eyes": 1, "ms": 70000, "stage": "live", "size": 1024, "pick": False}) for _ in range(5)] + \
           [E.build("compose", {"style": "solo.gold", "eyes": 1, "ms": 300, "tile": True, "tiles": 2, "stage": "live", "size": 480}),
            E.build("compose", {"style": "solo.powder", "eyes": 1, "ms": 800, "tile": True, "stage": "preview", "size": 480})] + \
           [E.build("master", {"step": "art", "style": "solo.gold", "count": 1, "ms": 9000, "need_s": 26, "peak_mb": 480}) for _ in range(3)] + \
           [E.build("master", {"step": "art", "style": "solo.gold", "count": 1, "ms": 11000, "need_s": 26, "peak_mb": 500, "needs_review": True})]
a2 = E.summarize(hist_evs)
trow = {(r["what"], r["style"], r["eyes"]): r for r in SS.times(a2)}
check("the histogram gives p50 and p95 as the upper bound of their bucket, and says how many are above the last bound: 100 previews, 50 at 400 ms, 45 at 1800, 5 at 70000",
      trow[("compose", "solo.gold", 1)]["n"] == 100 and trow[("compose", "solo.gold", 1)]["p50_ms"] == 500 and trow[("compose", "solo.gold", 1)]["p95_ms"] == 2000
      and trow[("compose", "solo.gold", 1)]["over"] == 5 and SS.percentile({len(E.HIST_MS): 3}, 0.5) is None and SS.percentile({}, 0.5) is None, trow[("compose", "solo.gold", 1)])
check("tiles and masters have their own rows (a tile is not a preview, the artwork's step is art with the style and the eye count of its plan)",
      trow[("tile", "solo.gold", 1)]["n"] == 1 and trow[("tile", "solo.powder", 1)]["p50_ms"] == 1000 and trow[("art", "solo.gold", 1)]["n"] == 4 and trow[("art", "solo.gold", 1)]["p95_ms"] == 12000)
check("times merge across days and a day with no histogram (an old rollup) merges as it did", E.merge(a2, {"events": 1})["ms_hist"] == a2["ms_hist"]
      and E.merge(a2, a2)["ms_hist"]["compose|solo.gold|1|1"] == 100)
rv = SS.review_by_style(a2)
check("review by style: one artwork of four made for solo.gold was held for a look", rv == [{"style": "solo.gold", "name": CT.name_of("solo.gold"), "review": 1, "made": 4, "rate": 0.25}], rv)
dem_evs = [E.build("compose", {"style": "solo.radiance", "eyes": 1, "stage": "preview", "tile": True, "tiles": 1, "market": "eu", "lang": "en"}) for _ in range(4)] + \
          [E.build("compose", {"style": "solo.radiance", "eyes": 1, "stage": "preview", "size": 1024, "market": "eu", "lang": "en"}) for _ in range(2)] + \
          [E.build("compose", {"style": "solo.radiance", "eyes": 1, "stage": "preview", "size": 1024, "market": "au", "lang": "en"})] + \
          [E.build("help", {"route": "soon", "style": "solo.radiance", "eyes": 1, "lang": "en"}) for _ in range(3)] + [E.build("help", {"route": "blocked", "style": "solo.radiance", "eyes": 1})] + \
          [E.build("help", {"route": "manual", "eyes": 2, "why": "lid_ring_outliers", "lang": "de"})] + \
          [E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "live", "size": 1024, "pick": True, "market": "eu"}),
           E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "live", "size": 1024, "pick": False, "market": "au"})]
a3 = E.summarize(dem_evs)
d3 = {(r["style"], r["eyes"], r["stage"]): r for r in SS.demand(a3)}
check("the demand for a Soon style: tiles looked at, large previews made, clicks on its buy button and checkouts refused, by style and eye count; the manual route is not demand",
      d3[("solo.radiance", 1, "preview")]["tiles"] == 4 and d3[("solo.radiance", 1, "preview")]["large"] == 3 and d3[("solo.radiance", 1, "preview")]["soon"] == 3
      and d3[("solo.radiance", 1, "preview")]["blocked"] == 1 and a3["help_route"] == {"soon": 3, "blocked": 1, "manual": 1} and a3["help_why"] == {"lid_ring_outliers": 1}, d3)
d_au = {(r["style"], r["eyes"], r["stage"]): r for r in SS.demand(a3, "market:au")}
check("the demand of a market is the slice's own (the clicks carry no market, so they are not in a slice)",
      d_au[("solo.radiance", 1, "preview")]["large"] == 1 and d_au[("solo.radiance", 1, "preview")]["tiles"] == 0
      and all(r["soon"] == 0 and r["blocked"] == 0 for r in d_au.values()), d_au)
check("chosen against recommended counts previews that say whether they were the pick (two of solo.gold: one the pick, one not); the slice has its own",
      SS.chosen(a3) == {"pick": 1, "other": 1, "share": 0.5} and SS.chosen(a3, "market:au") == {"pick": 0, "other": 1, "share": 0.0}, (SS.chosen(a3), SS.chosen(a3, "market:au")))
Box = type("Box", (), {"status": 409, "path": "/api/checkout"})
sent.clear()
with mock.patch.object(E, "record", lambda kind, **f: sent.append((kind, f)) or True):
    E.answer(Box(), {"reason": "style_unavailable", "style": "solo.radiance", "eyes": 1, "why": "stage"})
    E.answer(Box(), {"reason": "rendering"})
    E.answer(Box(), {"reason": "in_review"})
    E.answer(Box(), {"reason": "style_unavailable"})
check("a checkout that refused a style that cannot be bought (409 style_unavailable) is demand: a help event with route blocked, the style, the eye count and the why; no other 409 writes anything",
      sent == [("help", {"route": "blocked", "style": "solo.radiance", "eyes": 1, "why": "stage", "_wait": 0.5}), ("help", {"route": "blocked", "style": None, "eyes": None, "why": None, "_wait": 0.5})], sent)
check("... and what it writes passes the whitelist (the style is a code, the eye count a number; a reply that names neither is counted as blocked for unknown)",
      E.build("help", {"route": "blocked", "style": "solo.radiance", "eyes": 1, "why": "stage"}).get("style") == "solo.radiance" and "style" not in E.build("help", {"route": "blocked", "style": None}))
fb_evs = [E.build("compose", {"style": "duo.collision_infinity", "eyes": 2, "stage": "preview", "size": 1024, "fallback": "stack_contrast"}) for _ in range(3)] + \
         [E.build("compose", {"style": "duo.collision_infinity", "eyes": 2, "stage": "preview", "size": 1024}) for _ in range(9)] + \
         [E.build("error", {"endpoint": "compose", "class": "500", "reason": "x", "status": 500, "style": "solo.gold"}) for _ in range(2)] + \
         [E.build("enhance", {"gate": g, "cls": "own", "pupil": "round"}) for g in ["ok"] * 5 + ["lid"] * 3 + ["fill"] * 1 + ["both"] * 1 + ["unknown"] * 2]
a4 = E.summarize(fb_evs)
fbr = SS.fallbacks(a4)
check("the stack's share per pair design: 3 of 12 pictures of Collision Infinity fell back to the stacked lens", fbr == [{"style": "duo.collision_infinity", "name": CT.name_of("duo.collision_infinity"),
                                                                                                                         "fallback": "stack_contrast", "count": 3, "of": 12, "share": 0.25}], fbr)
gbs = {r["style"]: r for r in SS.gate_by_style(a4)}
check("the gate per style is measured per eye at enhance under each style's own rule: the lid rule fails lid and both (4 of 10 known eyes), the fill rule fill and both (2 of 10); styles with no gate have no row",
      gbs["duo.kiss_collision"]["failed"] == 4 and gbs["duo.kiss_collision"]["seen"] == 10 and gbs["duo.kiss_collision"]["rate"] == 0.4 and gbs["solo.universe"]["failed"] == 2
      and gbs["solo.clean"]["policy"] == "advisory" and "studio_black" not in gbs and gbs["solo.clean"]["rule"] == CT.ENGINE["solo.clean"]["gate_rules"], gbs.get("solo.clean"))
att = SS.attention(a4, {"min_n": 2, "error_rate": 0.05, "review_rate": 0.1, "gate_fail_rate": 0.35}, {"styles": True, "plates_4k": False})
check("the attention card: the errors of solo.gold (2 asks of 2), the gate of the lid-rule styles (0.4 over 0.35), a failing health boolean; a limit with too few events behind it is silent",
      any(a["kind"] == "error" and a["style"] == "solo.gold" for a in att) and any(a["kind"] == "gate" and a["style"] == "duo.kiss_collision" for a in att)
      and {"kind": "health", "key": "plates_4k"} in att and not any(a["kind"] == "gate" and a["style"] == "solo.universe" for a in att)
      and SS.attention(a4, {"min_n": 500, "error_rate": 0.05, "review_rate": 0.1, "gate_fail_rate": 0.35}, None) == [], att)
check("a hold of an order for a style step is on the card with its code", SS.attention(E.summarize([E.build("master", {"step": "art", "hold": "style_step_too_big", "style": "solo.gold"})]), {"min_n": 0}, None)
      == [{"kind": "hold", "code": "style_step_too_big", "n": 1}])
check("report() has every part the page shows, and says which tables a filter does not slice",
      set(SS.report(agg)) >= {"requests", "funnel", "funnel_by_class", "opening", "demand", "chosen", "previews", "fallbacks", "times", "errors", "review", "gate", "holds", "help", "reveal", "attention", "filter"}
      and "gate" in SS.report(agg, sl="lang:lt")["filter"]["whole"] and SS.report(agg, sl="lang:lt")["filter"]["slice"] == "lang:lt")
check("one filter at a time", isinstance(raised(lambda: SS.parse_slice("eu", "lt")), ValueError) and SS.parse_slice("au") == "market:au" and SS.parse_slice(None, "lt") == "lang:lt" and SS.parse_slice() is None)

section("8e. styles_stats over the stored events (a real day of them)")
reset()
shutil.rmtree(os.path.join(STORE, "ops", "events"), ignore_errors=True)
shutil.rmtree(os.path.join(STORE, "ops", "daily"), ignore_errors=True)
for i in range(40):
    ok_ = i < 26
    E.record("compose", tiles=0, eyes=2, gate="ok" if ok_ else "lid_sectors_outer", cls="own", retake=0, lang="lt" if i % 2 else "en", **({"market": "au"} if i % 4 == 0 else {}))
for i in range(20):
    E.record("compose", tiles=0, eyes=2, gate="ok" if i < 12 else "lid_sectors_outer", cls="own", retake=1, lang="en")
for i in range(5):
    E.record("compose", tiles=0, eyes=2, gate="ok", cls="own", retake=0, lang="en", again=True)
for i in range(35):
    E.record("compose", tiles=0, eyes=3, gate="ok" if i < 10 else "lid_ring_outliers", cls="grey", retake=0, lang="en")
for i in range(5):
    E.record("compose", tiles=0, eyes=4, gate="ok", cls="own", retake=0, lang="en")
E.record("compose", style="solo.gold", eyes=1, stage="live", size=1024, pick=True, ms=900, lang="en", tiles=1)
E.record("help", route="soon", style="solo.radiance", eyes=1, lang="en")
st = act("styles_stats", days=1)
fr = {r["eyes"]: r for r in st["funnel"]}
check("styles_stats reads the day's events and gives the funnel with n: two eyes 40 first-photo sets of which 26 passed, 12 of the 14 failed ones passed after one retake (5 repeated requests left out)",
      st["ok"] and fr[2]["first"] == 40 and fr[2]["first_pass"] == 26 and fr[2]["rate_first"] == 0.65 and fr[2]["retake1"] == 20 and fr[2]["retake1_pass"] == 12 and fr[2]["rate_retake"] == 0.95, fr.get(2))
check("the opening lines: two eyes green (40 sets, 65 and 95 percent), three eyes red on the first photo and the retake, four eyes red for n",
      st["opening"]["2"]["ok"] is True and st["opening"]["3"]["ok"] is False and st["opening"]["3"]["why"] == ["first_low", "retake_low"] and st["opening"]["4"]["why"][0] == "n_low"
      and "1" not in st["opening"], st["opening"])
check("by colour class: the grey sets of three eyes are their own row", [(r["eyes"], r["cls"], r["first"], r["first_pass"]) for r in st["funnel_by_class"] if r["eyes"] == 3] == [(3, "grey", 35, 10)])
check("requests: the sum of compose_tiles (the sets that drew nothing are in it)", st["requests"]["total"] == 40 + 20 + 5 + 35 + 5 + 1 and st["requests"]["drew_nothing"] == 105, st["requests"])
au_ = act("styles_stats", days=1, market="au")
check("the market filter is the slice: ten of the forty first photos came from the Australian market", {r["eyes"]: r["first"] for r in au_["funnel"]} == {2: 10} and au_["market"] == "au" and "gate" in au_["filter"]["whole"])
lt_ = act("styles_stats", days=1, lang="lt")
check("the language filter likewise: twenty of them were Lithuanian", {r["eyes"]: r["first"] for r in lt_["funnel"]} == {2: 20})
check("a filter that is not a market or a language, and two filters at once, are 400",
      all(says(refused("styles_stats", **b), 400, "bad_request") for b in ({"market": "moon"}, {"lang": "xx"}, {"market": "au", "lang": "lt"}, {"market": 5})))
check("the demand for the style that was Soon (solo.radiance, one click) and the one picture of solo.gold with its time and estimate are in the reply",
      any(r["style"] == "solo.radiance" and r["soon"] == 1 for r in st["demand"]) and any(r["what"] == "compose" and r["style"] == "solo.gold" and r["p50_ms"] == 1000 for r in st["times"])
      and st["limits"] == SO.LIMITS_DEFAULT and st["memory"]["peak_mb_is"] == "vmrss_increase_over_the_step" and st["recording"] is True, st["times"])
check("the old stats action does not carry the two big tables (compose_slice, ms_hist), and everything else of it is as it was", (lambda d: all("compose_slice" not in x["counts"] and "ms_hist" not in x["counts"] for x in d["days"])
                                                                                                         and all("compose_funnel" in x["counts"] for x in d["days"]))(ops.a_stats({"days": 1}, WHO)))
ra = act("styles_override", style="celestial_gold", eyes=2, stage="preview", reason_kind="soon", confirm=True)
ea = SO.audit_read(limit=1)[0]
check("the audit entry of a change keeps the funnel of that count at that moment: the same numbers the page showed (n 40, 65 percent, 95 percent, green)",
      ea["numbers"]["2"] == {"n": 40, "first_pass": 0.65, "with_retake": 0.95, "unknown": 0, "line_ok": True, "why": [], "partial": False}, ea["numbers"])
act("styles_override", style="celestial_gold", eyes=2, stage="restore", confirm=True)
for stg_, gate_, n_ in (("start", "ok", 6), ("start", "lid_sectors_outer", 2), ("start", "unknown", 1), ("paid", "ok", 3), ("paid", "lid_sectors_outer", 1)):
    for _ in range(n_):
        E.record("checkout", stage=stg_, style="solo.gold", eyes=1, gate=gate_, lang="en", market="eu")
for _ in range(20):
    E.record("compose", style="solo.gold", eyes=1, stage="live", size=1024, pick=True, ms=800, lang="en")
st3 = act("styles_stats", days=1)
cv = {(r["style"], r["eyes"]): r for r in st3["conversion"]["rows"]}
check("the checkout events written through the real recorder reach the numbers: the funnel of solo.gold after the preview, 20 large previews, 9 sessions started, 4 paid",
      st3["conversion"]["recorded"] is True and cv[("solo.gold", 1)]["previews"] == 21 and cv[("solo.gold", 1)]["started"] == 9 and cv[("solo.gold", 1)]["paid"] == 4, st3["conversion"])
reset()
shutil.rmtree(os.path.join(STORE, "ops", "events"), ignore_errors=True)

section("8f. the numbers the card and PR 6.1 name: chosen against recommended by eye class, qa_ok false by style, busy_retry, the funnel after the preview, ordered after failure")
ev_ = []
for cls_, pick_n, other_n in (("grey", 2, 3), ("own", 4, 1)):
    ev_ += [E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "live", "size": 1024, "pick": True, "cls": cls_}) for _ in range(pick_n)]
    ev_ += [E.build("compose", {"style": "solo.powder", "eyes": 1, "stage": "preview", "size": 1024, "pick": False, "cls": cls_}) for _ in range(other_n)]
ev_ += [E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "live", "size": 1024, "qa_ok": False}) for _ in range(2)]
ev_ += [E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "live", "size": 480, "tile": True, "tiles": 1, "qa_ok": False})]
ev_ += [E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "live", "size": 480, "tile": True, "tiles": 1, "qa_ok": True})]
ev_ += [E.build("error", {"endpoint": "compose", "class": "503", "reason": "busy_retry", "status": 503, "style": "solo.gold"}) for _ in range(2)]
ev_ += [E.build("error", {"endpoint": "master_compose", "class": "503", "reason": "busy_retry", "status": 503})]
ev_ += [E.build("error", {"endpoint": "compose", "class": "500", "reason": "x", "status": 500, "style": "solo.gold"})]
a8 = E.summarize(ev_)
cb = {r["cls"]: r for r in SS.chosen_by_class(a8)}
check("chosen against recommended by the set's eye class: grey 2 of 5 followed the pick, own 4 of 5 (a tile of a batch is not a choice, a preview of an unknown class is in no row)",
      cb["grey"] == {"cls": "grey", "pick": 2, "other": 3, "n": 5, "share": 0.4} and cb["own"] == {"cls": "own", "pick": 4, "other": 1, "n": 5, "share": 0.8} and set(cb) == {"grey", "own"}, cb)
qa = {r["style"]: r for r in SS.qa_by_style(a8)}
check("qa_ok false by style: 3 pictures of solo.gold failed their own colour check over the 10 it made (8 previews and 2 tiles); a style with none has no row",
      qa["solo.gold"]["qa_fail"] == 3 and qa["solo.gold"]["of"] == 10 and qa["solo.gold"]["rate"] == 0.3 and "solo.powder" not in qa, qa)
br = SS.busy_retry(a8)
check("busy_retry by endpoint and style: 2 on compose for solo.gold, 1 on master_compose that named no style; a 500 is not a busy_retry",
      [(r["endpoint"], r["style"], r["count"]) for r in br] == [("compose", "solo.gold", 2), ("master_compose", "unknown", 1)] and br[1]["name"] is None, br)
ck_ = []
for stg_, gate_, n_ in (("start", "ok", 6), ("start", "lid_sectors_outer", 2), ("start", "unknown", 1), ("paid", "ok", 3), ("paid", "lid_sectors_outer", 1)):
    ck_ += [E.build("checkout", {"stage": stg_, "style": "solo.gold", "eyes": 1, "gate": gate_, "lang": "en", "market": "eu"}) for _ in range(n_)]
ck_ += [E.build("checkout", {"stage": "start", "style": "duo.kiss_collision", "eyes": 2, "gate": "lid_ring_outliers"}), E.build("checkout", {"stage": "bogus", "style": "solo.gold", "eyes": 1})]
ck_ += [E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "live", "size": 1024}) for _ in range(20)] + [E.build("compose", {"style": "solo.gold", "eyes": 1, "stage": "preview", "size": 1024})]
a9 = E.summarize(ck_)
cv = SS.conversion(a9)
row = {(r["style"], r["eyes"]): r for r in cv["rows"]}
check("the funnel after the preview by style and eye count, with n: 20 large previews while live (the one while Soon is not a chance to buy), 9 started, 4 paid; the rates are None where the denominator is 0",
      cv["recorded"] is True and row[("solo.gold", 1)] == {"style": "solo.gold", "name": CT.name_of("solo.gold"), "eyes": 1, "previews": 20, "started": 9, "paid": 4, "rate_started": 0.45, "rate_paid": 0.4444}
      and row[("duo.kiss_collision", 2)]["previews"] == 0 and row[("duo.kiss_collision", 2)]["rate_started"] is None and row[("duo.kiss_collision", 2)]["rate_paid"] == 0.0, cv)
check("an event whose stage is not start or paid counts nowhere, and with no checkout event at all the funnel says it was not recorded",
      sum(r["started"] + r["paid"] for r in cv["rows"]) == 9 + 4 + 1 and SS.conversion(E.empty()) == {"recorded": False, "rows": []})
oaf = {r["eyes"]: r for r in SS.ordered_after_failure(a9)}
check("ordered after failure per eye count: of 9 solo.gold starts 2 were on a failing set (an unknown gate is not a failure), of 4 paid 1, share 0.25, by the failing eye's code",
      oaf[1] == {"eyes": 1, "started": 9, "paid": 4, "started_failed": 2, "paid_failed": 1, "by_code": {"lid_sectors_outer": 1}, "share_paid_failed": 0.25}
      and oaf[2]["started_failed"] == 1 and oaf[2]["paid"] == 0 and oaf[2]["share_paid_failed"] is None, oaf)
rp = SS.report(a8)
check("report() carries them, and says which tables a filter does not slice", set(rp) >= {"chosen_by_class", "conversion", "after_failure", "busy_retry", "qa"}
      and {"chosen_by_class", "conversion", "after_failure", "busy_retry", "qa"} <= set(rp["filter"]["whole"]))
E._SEEN["all"] = [time.time()] * E.RATE["all"][0]               # the per-instance ceiling is reached
allowed = (E._allow("compose", time.time(), None), E._allow("checkout", time.time(), "start"), E._allow("checkout", time.time(), "paid"))
E._SEEN["all"] = []
check("a paid checkout event follows a real payment and is not lost to a flood of other events (the ceiling holds back the rest)", allowed == (False, False, True), allowed)
check("the checkout kind is whitelisted: stage, style, eyes, gate, lang and market only, no order id and no amount", set(E.FIELDS["checkout"]) == {"stage", "style", "eyes", "gate", "lang", "market"}
      and E.CHECKOUT_STAGES == ("start", "paid") and "order" not in E.FIELDS["checkout"] and "amount" not in E.FIELDS["checkout"])
check("the new tables merge across days (numbers add) and an old day without them merges as before",
      E.merge(a9, a9)["checkout_funnel"]["solo.gold|1|start|ok"] == 12 and E.merge(a8, {"events": 1})["compose_chosen_cls"] == a8["compose_chosen_cls"])
reset()
shutil.rmtree(os.path.join(STORE, "ops", "events"), ignore_errors=True)

# ============================================================================================ 9. the sentences
section("9. the Lithuanian sentences of the admin page for the new reasons and actions")
fmt = read(os.path.join(REPO, "src", "admin", "format.ts")).replace(chr(13) + chr(10), chr(10))
NEW_REASONS = ("above_ceiling", "not_switchable", "needs_ticks", "no_engine", "stale_view", "price_test_running")
LT_LETTERS_ALL = "A-Za-z" + "".join(chr(c) for c in (0x104, 0x10c, 0x118, 0x116, 0x12e, 0x160, 0x172, 0x16a, 0x17d, 0x105, 0x10d, 0x119, 0x117, 0x12f, 0x161, 0x173, 0x16b, 0x17e))
sent_lt = {}
for code in NEW_REASONS:
    m = re.search(r"^  " + code + r": '([^']*)',$", fmt, re.M)
    sent_lt[code] = m.group(1) if m else None
check("every reason code the new actions raise has a Lithuanian sentence in REASON_LT", all(sent_lt.values()), sent_lt)
LOWER_JUS = re.compile(r"(^|[^" + LT_LETTERS_ALL + r"])(" + "|".join(["j" + chr(0x16b) + "s", "j" + chr(0x16b) + "s" + chr(0x173), "jums", "jus", "jumis"]) + r")(?![" + LT_LETTERS_ALL + r"])", re.U)
FLAGGED = re.compile(r"(^|[^" + LT_LETTERS_ALL + r"])(matosi|matyt" + chr(0x173) + "si|mat" + chr(0x117) + "si|pilnai|priklausomai nuo|Gerb\\.)(?![" + LT_LETTERS_ALL + r"])", re.I | re.U)
check("they pass the typography and wording rules of the text check: no dash, no double space, no space before a full stop, no straight double quote, no lower case 'jus' form, no flagged wording, no English word",
      all(not re.search(DASH, t) and "  " not in t and " ." not in t and '"' not in t and not LOWER_JUS.search(t) and not FLAGGED.search(t)
          and not re.search(r"\b(live|ceiling|stage|override|tick|the|and|style|price|test|admin)\b", t) for t in sent_lt.values() if t), sent_lt)
check("the actions have their labels in ACTION_LT and the results of the audit lines are worded", "styles_override: '" in fmt and "styles_limits: '" in fmt
      and all(f"{c}: '" in fmt for c in ("changed", "ticked", "above_ceiling", "needs_ticks", "stale_view")))

# ============================================================================================ 10. over HTTP
section("10. over HTTP: the admin key, and a checkout that fails closed when the switch cannot be read")
KEY = ops.mint_admin_key(3600)
ops.FAIL_SLEEP = 0.0                                  # a refused key is slowed by 0.8 s each: not in this suite


def http_admin(action, key=KEY, **body):
    h = {"x-real-ip": "203.0.113.9"}
    if key:
        h["Authorization"] = "Bearer " + key
    r = requests.post(BASE + "/api/admin", json=dict(body, action=action), headers=h, timeout=60)
    return r.status_code, r.json()


for a_ in ("styles_catalogue", "styles_override", "styles_audit", "styles_stats", "styles_limits"):
    c, j = http_admin(a_, key=None, style="celestial_gold", eyes=1, stage="lab", confirm=True)
    check(f"{a_} without an admin key is 403 and changes nothing", c == 403 and j.get("reason") == "admin_denied", (c, j))
check("an expired or foreign key is 403 as well", http_admin("styles_catalogue", key="admin-v1.1000000000.0123456789abcdef0123456789abcdef")[0] == 403)
c, j = http_admin("styles_catalogue")
check("with the key the catalogue answers", c == 200 and j["ok"] and len(j["styles"]) == len(CT.ids()), (c, str(j)[:200]))
c, j = http_admin("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="soon", confirm=True)
check("a change over HTTP: 200, in force on this instance", c == 200 and j["result"] == "changed" and CT.stage_of("celestial_gold", 1) == "preview", (c, j))
c, j = http_admin("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
check("a refusal is a 409 with its reason code and its facts", c == 409 and j["reason"] == "above_ceiling" and j["ceiling"] == {"1": "lab"}, (c, j))
c, j = http_admin("styles_override", style="nope", eyes=1, stage="live", confirm=True)
check("a malformed request is a 400 with a sentence", c == 400 and j["ok"] is False and j.get("error"), (c, j))
with CountingStore(fail=store.StorageError("injected: storage down")):
    SO.invalidate()
    c, j = http_admin("styles_override", style="celestial_gold", eyes=1, stage="lab", confirm=True)
    check("when the switch cannot be read a change is a 503 storage_busy (never a guess)", c == 503 and j["reason"] == "storage_busy", (c, j))
    c, j = http_admin("styles_catalogue")
    check("and so is the catalogue of the switch", c == 503 and j["reason"] == "storage_busy", (c, j))
reset()
http_admin("styles_override", style="celestial_gold", eyes=1, stage="restore", confirm=True)

CROP, PREV = H.jpeg_b64(512, 1), H.jpeg_b64(1024, 2)


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def new_order():
    c, j = post("/api/order", {"action": "draft", "eye": 1, "crop": CROP, "preview": PREV, "pad": 1.12, "ticket": H.fresh_ticket(), "lang": "en", "ref": "eye-1"})
    assert c == 200, (c, j)
    return j["order"], j["k"]


def checkout(order, k, style="celestial_gold", eyes=1):
    return post("/api/checkout", {"order": order, "k": k, "eyes": eyes, "style": style, "names": "", "title": "", "lang": "en", "consent_digital": True})


o1, k1 = new_order()
creates0 = len(H.Fake.creates)
SO.invalidate()
with CountingStore(fail=store.StorageError("injected: storage down")):
    c, j = checkout(o1, k1)
check("IE11: a checkout when the owner's switch cannot be read fails closed: 503 storage_busy, retry true, no Stripe session, nothing recorded in the order",
      c == 503 and j.get("reason") == "storage_busy" and j.get("retry") is True and len(H.Fake.creates) == creates0
      and "checkout" not in json.load(open(os.path.join(STORE, "orders", o1, "order.json"), encoding="utf-8")), (c, j))
with CountingStore(fail=store.StorageError("injected: storage down")):
    r_ = requests.get(BASE + "/api/checkout", timeout=60)
check("... while GET /api/checkout (the page's price list) does not depend on it", r_.status_code == 200 and r_.json()["open"] is True)
SO.invalidate()
c, j = checkout(o1, k1)
check("with the switch readable the same checkout opens a Stripe session (the default path is not changed)", c == 200 and j["ok"] and len(H.Fake.creates) == creates0 + 1, (c, j))
act("styles_override", style="celestial_gold", eyes=1, stage="preview", reason_kind="soon", confirm=True)
o2, k2 = new_order()
c, j = checkout(o2, k2)
# WP12 (spec 2.9): a known style that cannot be ordered now is a 409 style_unavailable (why stage), not the old 400 that listed the ids; nothing else changed
check("a style the owner took back to preview is refused at checkout (409 style_unavailable, why stage: not one of the styles that can be ordered now), no session",
      c == 409 and j.get("reason") == "style_unavailable" and j.get("why") == "stage" and j.get("style") == "celestial_gold" and len(H.Fake.creates) == creates0 + 1, (c, j))
c, j = checkout(o2, k2, style="supernova")
check("another style of the same eye count still opens one", c == 200 and len(H.Fake.creates) == creates0 + 2, (c, j))
reset()

# ============================================================================================ 12. the laboratory of a group
section("12. the laboratory of a group: the contact sheet of every style for 1 to 8 eyes, with the gate readout")
import base64 as _b64  # noqa: E402
import io as _io  # noqa: E402
import synth_iris as SI  # noqa: E402
from PIL import Image  # noqa: E402
import _lib.styles as ST  # noqa: E402


def eye_b64(name):
    return _b64.b64encode(SI.jpeg_bytes(name)).decode("ascii")


def bar_b64():
    b = _io.BytesIO()
    SI.make(kind="blue", pupil="bar", seed=5).save(b, "JPEG", quality=92, subsampling=0)
    return _b64.b64encode(b.getvalue()).decode("ascii")


def decode(t):
    return Image.open(_io.BytesIO(_b64.b64decode(t["image"])))


reset()
marks = []
with mock.patch.object(ST, "watermarked", lambda *a, **k: marks.append(1) or (_ for _ in ()).throw(AssertionError("the lab draws no watermark"))):
    g2 = act("styles_lab", eyes=[eye_b64("blue_round"), eye_b64("dark_brown_round")], size=480)
want2 = [i for i in CT.previewable_ids(2, admin=True) if not CT.is_legacy(i)]
cmp_recs = [{"cls": e["cls"], "pupil": {"cls": e["pupil"]}, "gate": {r: {"ok": v["ok"]} for r, v in e["gate"].items()}} for e in g2["eyes"]]
tl2 = {t["id"]: t for t in g2["tiles"]}
check("a pair: one tile for every style of two eyes the admin may preview (laboratory and held ones included, the legacy six left out), in the registry's order, none watermarked",
      g2["ok"] and g2["group"] == 2 and g2["size"] == 480 and [t["id"] for t in g2["tiles"]] == want2 and len(want2) >= 3 and not marks and g2["partial"] is False, (list(tl2), want2))
check("each tile is drawn: a JPEG of 480 px on its long side, with its layout, canvas, design, the self check and the time; the stage and the ceiling are the registry's (laboratory today)",
      all(t["available"] and decode(t).size[0] <= 480 and max(decode(t).size) == 480 and t["layout"] and t["canvas"] and t["design_used"] and t["selfcheck"] is not None and t["ms"] >= 0
          and t["stage"] == t["ceiling"] == "lab" for t in g2["tiles"]), [(t["id"], t["why"], t.get("error")) for t in g2["tiles"]])
check("the eyes' gate readout: class, pupil and both rule sets with their values; clean eyes pass both",
      [e["eye"] for e in g2["eyes"]] == [1, 2] and g2["eyes"][0]["cls"] in ("own", "dark_brown", "grey") and g2["eyes"][1]["cls"] == "dark_brown" and g2["eyes"][0]["pupil"] == "round"
      and all(set(e["gate"]) == {"lid", "fill"} and all(v and v["ok"] is True and "values" in v for v in e["gate"].values()) for e in g2["eyes"]), g2["eyes"])
check("the recommended tile is the catalogue's own answer for these eyes (a live style: the legacy six are still the ones that can be bought), never a laboratory one; the call stored and audited nothing",
      g2["pick"] == CT.pick_for(2, cmp_recs) and CT.stage_of(g2["pick"], 2) == "live" and not os.path.isdir(os.path.join(STORE, "ops", "styles")), g2["pick"])
g2b = act("styles_lab", eyes=[eye_b64("blue_round"), eye_b64("dark_brown_round")], size=480, styles=["duo.kiss_collision"])
check("one style asked for: one tile, and the same picture as in the sheet (a tile does not depend on the others)",
      [t["id"] for t in g2b["tiles"]] == ["duo.kiss_collision"] and g2b["tiles"][0]["image"] == tl2["duo.kiss_collision"]["image"])
gf = act("styles_lab", eyes=[eye_b64("blue_lid"), eye_b64("blue_round")], size=480, styles=["duo.kiss_collision", "solo.clean"][:1])
tk = gf["tiles"][0]
check("a failing eye does not withhold the tile in the lab: the picture is drawn, why says gate, and the readout shows which rule failed on which eye",
      tk["available"] and tk["image"] and tk["why"] == "gate" and gf["eyes"][0]["gate"]["lid"]["ok"] is False and gf["eyes"][0]["gate"]["lid"]["why"] and gf["eyes"][1]["gate"]["lid"]["ok"] is True, (tk["why"], gf["eyes"][0]["gate"]))
gb = act("styles_lab", eyes=[bar_b64(), eye_b64("blue_round")], size=480)
bars = {t["id"]: t for t in gb["tiles"]}
check("a horizontal bar pupil: the collision family refuses it, so those tiles carry why bar_pupil and no picture (the readout says the pupil is a bar); the other families are drawn",
      all(t["why"] == "bar_pupil" and t["image"] is None and t["available"] is False for i, t in bars.items() if CT.engine_for(i, 2)["module"] == "collision")
      and gb["eyes"][0]["pupil"] == "bar" and any(t["available"] for t in gb["tiles"] if CT.engine_for(t["id"], 2)["module"] == "universe"), [(i, t["why"]) for i, t in bars.items()])
g1 = act("styles_lab", eyes=[eye_b64("green_round")], size=480, styles=["solo.universe", "solo.elements"])
check("one eye is a group too, and a held style (Elements) is on the sheet; a style with looks is one tile per look (Universe: echo, vortex, deepfield, starfield)",
      [(t["id"], t["look"]) for t in g1["tiles"]] == [("solo.universe", "echo"), ("solo.universe", "vortex"), ("solo.universe", "deepfield"), ("solo.universe", "starfield"), ("solo.elements", None)]
      and all(t["available"] and t["image"] for t in g1["tiles"]), [(t["id"], t["look"], t["why"]) for t in g1["tiles"]])
bad = [dict(eyes=[eye_b64("blue_round")] * 9), dict(eyes=[]), dict(eyes="x"), dict(eyes=[5]), dict(eyes=[eye_b64("blue_round")], size=2048), dict(eyes=[eye_b64("blue_round")], size=True),
       dict(eyes=[eye_b64("blue_round")], styles=["celestial_gold"]), dict(eyes=[eye_b64("blue_round")], styles=["nope"]), dict(eyes=[eye_b64("blue_round")], styles=["solo.gold", "solo.gold"]),
       dict(eyes=[eye_b64("blue_round")], styles="solo.gold"), dict(eyes=["!!!not base64!!!"]), dict(eyes=[eye_b64("blue_round")], order="lab-260101-abcd1234"),
       dict(order="lab-260101-abcd1234", ns=[0]), dict(order="studio", ns=[1]), dict(order="lab-260101-abcd1234", ns=[1, 1]), dict(ns=[1]), dict(eyes=[eye_b64("blue_round")], opts={"bad": 1})]
refusals = [(i, refused("styles_lab", **b)) for i, b in enumerate(bad)]
check("a malformed group request is a 400 that says so (nine eyes, none, the wrong kind, a size that is not offered, a legacy or unknown style, a style twice, text that is no image, "
      "both forms, a bad order or count, a bad option)", all(r and r[1] == 400 for _i, r in refusals), [(i, r) for i, r in refusals if not (r and r[1] == 400)])
for nm, name in (("1", "blue_round"), ("2", "dark_brown_round")):
    full = os.path.join(STORE, "orders", "lab-260101-abcd1234", f"eye_{nm}.jpg")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(SI.jpeg_bytes(name))
    put_json(f"orders/lab-260101-abcd1234/eye_{nm}.json", {"eye_id": ("ab" * 7) + nm * 2})
go = act("styles_lab", order="lab-260101-abcd1234", ns=[1, 2], size=480, styles=["duo.kiss_collision"])
check("the eyes of a lab test order (the stored masters, shrunk to the preview's size): the tile is drawn and the eye ids are the stored records' ones",
      go["ok"] and go["tiles"][0]["available"] and [e["eye_id"] for e in go["eyes"]] == [("ab" * 7) + "11", ("ab" * 7) + "22"], go["eyes"])
x = refused("styles_lab", order="lab-260101-abcd9999", ns=[1])
check("a lab order without that eye is a 400", x and x[1] == 400)
with mock.patch.object(L, "time_left", lambda default=L.BUDGET: 5.0):
    gp = act("styles_lab", eyes=[eye_b64("blue_round"), eye_b64("dark_brown_round")], size=480)
check("a call that runs short of time stops drawing: the tiles are not made, say no_time, and the reply says partial (the eyes' readout is still there)",
      gp["partial"] is True and all(t["why"] == "no_time" and t["image"] is None for t in gp["tiles"]) and len(gp["eyes"]) == 2, [(t["id"], t["why"]) for t in gp["tiles"]])
check("the single-eye lab is untouched: a style, an eye and a size give the old reply (image, view, facts), and without a style the menu lists the group sizes too",
      act("styles_lab", style="solo.clean", eye=eye_b64("blue_round"), size=480)["style"] == "solo.clean" and act("styles_lab")["group_sizes"] == [480, 1024])
c, j = http_admin("styles_lab", key=None, eyes=[eye_b64("blue_round")])
check("the group lab is an admin action: without the key it is 403 and draws nothing", c == 403)
c, j = http_admin("styles_lab", eyes=[eye_b64("blue_round")], size=480, styles=["solo.clean"])
check("over HTTP with the key the reply is one JSON of the tiles", c == 200 and j["ok"] and j["tiles"][0]["id"] == "solo.clean" and j["tiles"][0]["image"], (c, str(j)[:200]))
reset()
shutil.rmtree(os.path.join(STORE, "orders"), ignore_errors=True)

# ============================================================================================ 11. hygiene
section("11. what the package adds holds no dash, no written price, no secret")
mine = ["api/_lib/stage_overrides.py", "api/_lib/style_stats.py", "api/_lib/catalogue.py", "api/_lib/events.py", "api/_lib/ops.py", "api/_lib/abtest.py", "api/compose.py", "api/_lib/cleanup.py",
        "scripts/styles_tests/test_admin_styles.py"]
INVIS = "[" + "".join(chr(c) for lo, hi in ((0x200b, 0x200f), (0x2028, 0x202e), (0x2060, 0x2064), (0xfeff, 0xfeff)) for c in range(lo, hi + 1)) + "]"
texts = {f: read(os.path.join(REPO, f)) for f in mine if os.path.isfile(os.path.join(REPO, f))}
check("no en or em dash and no invisible character in any file of the package", not [f for f, t in texts.items() if re.search(DASH, t) or re.search(INVIS, t)])
PRICE = re.compile(r"\d+[.,]\d\d\s?(EUR|eur|A\$|Ft)|A\$\s?\d|\d\s?Ft\b")
MODS_NEW = ("api/_lib/stage_overrides.py", "api/_lib/style_stats.py")
check("no written price (a decimal amount with a currency, A$, Ft) in any new file", not [f for f in MODS_NEW + ("scripts/styles_tests/test_admin_styles.py",) if PRICE.search(texts.get(f, ""))])
check("no secret: no key-looking token in the new modules", not [f for f in MODS_NEW if re.search(r"(sk_(live|test)_|whsec_|re_[A-Za-z0-9]{8})", texts.get(f, ""))])
check("the new modules start with the __future__ import (Python 3.12) and import no engine and no numpy",
      all(re.search(r"^from __future__ import annotations$", texts[f].replace(chr(13), ""), re.M) for f in MODS_NEW)
      and not any(re.search(r"^(import|from) (numpy|PIL)|from \.styles|import styles", texts[f], re.M) for f in MODS_NEW))

passed = sum(RESULTS)
print(f"\n{passed} of {len(RESULTS)} passed", flush=True)
sys.exit(0 if passed == len(RESULTS) else 1)
