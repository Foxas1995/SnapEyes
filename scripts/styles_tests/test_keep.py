# -*- coding: utf-8 -*-
"""The kept copies of the free preview (the owner's decision of 2026-11-26, api/_lib/keep.py): every photo sent to /api/analyze with its outcome, the crop and
the clean restoration of /api/enhance, the large preview of /api/compose, 30 days, for the owner's admin page "Peržiūros". Suite v3keep.

  1. the module: the switch (on unless off, 0, false, no; off without the daily clean-up), the visit folder (the page's visit, a ticket's hash, else its own),
     the photo's size, the paths, never raises (a store that refuses, a picture that cannot be made), nothing when little time is left, the ceilings
     (per instance and day, per visit, the deployment's visits of a day)
  2. over HTTP: an accepted photo and a refused one (with the reason), the restoration's before and after, the large preview; the visit groups them; the
     events say kept; the AI-made sample eye, the owner's lab (nokeep), a robot and a batch of tiles keep nothing; no IP address, user agent, cookie or
     ticket in what is kept
  3. the daily clean-up: kept/<day> folders older than 30 days go with everything in them, younger ones stay; the clean-up's run calls it
  4. the admin page: the view of a day (the visits, their steps, the outcome and the codes, signed links), the deletion of a visit (the confirmation typed,
     audited without a link or a picture), the key is needed; health says keep
No network, no image model (scripted), no real eye. Run by suites/run_main.sh as v3keep.
    python test_keep.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import base64
import importlib.util
import io
import json
import os
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
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_WORLD"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3keep_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ["CRON_SECRET"] = "keep-cron-secret-for-tests-0123456789abcdef"        # kept only while the daily clean-up can delete
os.environ["SNAPEYES_ADMIN_SECRET"] = "keep-admin-secret-for-tests-0123456789abcdef0123"
os.environ["STYLE_PLATE_CACHE"] = os.path.join(TMP, "cache")
sys.path.insert(0, API)
import requests  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import keep as KP  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import store, ops  # noqa: E402
from _lib import catalogue as CT  # noqa: E402

for name in ("analyze", "enhance", "compose", "admin"):
    spec_m = importlib.util.spec_from_file_location(name, os.path.join(API, name + ".py"))
    mod = importlib.util.module_from_spec(spec_m)
    spec_m.loader.exec_module(mod)
    H.MODS[name] = mod
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
E.WAIT = 10.0
KP.WAIT = 10.0                   # a slow disk must not make a check flaky: the steps wait for their writes as long as they need here
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
HEADERS = {"Content-Type": "application/json", "User-Agent": UA, "X-Forwarded-For": "203.0.113.77", "X-Real-IP": "203.0.113.77",
           "Cookie": "_fbp=fb.1.1790000000.123456789", "X-Vercel-Ip-Country": "LT"}
EVENTS = []
_real_record = E.record


def spy_record(kind, **fields):
    EVENTS.append((kind, dict(fields)))
    return _real_record(kind, **fields)


E.record = spy_record
for m in ("analyze", "enhance", "compose"):
    H.MODS[m].E.record = spy_record


def post(path, body, headers=None):
    r = requests.post(BASE + path, data=json.dumps(body), headers=headers or HEADERS, timeout=300)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def b64(im, q=92):
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=q)
    return base64.b64encode(buf.getvalue()).decode()


def kept_files():
    root = os.path.join(STORE, "kept")
    out = []
    for r, _d, fs in os.walk(root):
        for f in fs:
            if not f.endswith(".part"):
                out.append(os.path.relpath(os.path.join(r, f), STORE).replace(os.sep, "/"))
    return sorted(out)


def last_event(kind):
    return next((f for k, f in reversed(EVENTS) if k == kind), {})


def wipe():
    shutil.rmtree(os.path.join(STORE, "kept"), ignore_errors=True)
    with KP._LOCK:
        KP._COUNT.update(day="", items=0, visits={}, full_day="", full_t=0.0, full=False)


# ============================================================================================ 1. the module
section("1. the module: the switch, the visit, the photo, the paths, never raises, time, ceilings")
states = {}
for v in ("off", "0", "false", "no", "OFF", "on", "1", ""):
    os.environ["SNAPEYES_KEEP"] = v
    states[v] = KP.on()
os.environ.pop("SNAPEYES_KEEP")
cron = os.environ.pop("CRON_SECRET")
no_cron = KP.on()
os.environ["CRON_SECRET"] = cron
check("the switch SNAPEYES_KEEP: off, 0, false, no (any case) turn it off, anything else leaves it on; without CRON_SECRET (no daily clean-up to delete) it is off",
      states == {"off": False, "0": False, "false": False, "no": False, "OFF": False, "on": True, "1": True, "": True} and no_cron is False and KP.on() is True, (states, no_cron))
v1 = KP.visit_of({"visit": "lz1abc-0a1b2c3d4e"})
v2 = KP.visit_of({"ticket": "work.1790000000.0123456789abcdef.0123456789abcdef0123456789abcdef"})
v3 = KP.visit_of({"visit": "../../etc", "ticket": None})
check("the visit folder: the page's visit as it is (v-), else a hash of the work ticket (t-, the ticket itself never), else one of its own (r-); a visit that is not one is ignored",
      v1 == "v-lz1abc-0a1b2c3d4e" and v2.startswith("t-") and len(v2) == 18 and "0123456789abcdef" not in v2 and v3.startswith("r-")
      and KP.visit_of({"ticket": "work.1790000000.0123456789abcdef.0123456789abcdef0123456789abcdef"}) == v2, (v1, v2, v3))
big = Image.new("RGB", (4000, 3000), (120, 90, 60))
pj = KP.photo_jpeg(big)
small = Image.open(io.BytesIO(pj))
check("the kept photo is at most 1280 px on its long side, a JPEG without metadata, the photo's proportions", small.size == (1280, 960) and pj[:2] == b"\xff\xd8"
      and "exif" not in small.info, small.size)
wipe()
k = KP.begin("analyze", {"visit": "lz1abc-0a1b2c3d4e"})
k.image("photo", lambda: pj)
code = k.done({"outcome": "refused", "reason": "too_blurry"})
files = kept_files()
day = time.strftime("%Y-%m-%d", time.gmtime())
check("one picture and its JSON under kept/<UTC day>/<visit>/<HHMMSS>-<step>-<rand>[-<picture>].(jpg|json); the code is ok",
      code == "ok" and len(files) == 2 and all(f.startswith(f"kept/{day}/v-lz1abc-0a1b2c3d4e/") for f in files)
      and any(f.endswith("-analyze-" + f.split("-analyze-")[1].split("-")[0] + "-photo.jpg") for f in files if "-photo" in f)
      and all(KP._FILE.fullmatch(f.rsplit("/", 1)[1]) for f in files), (code, files))
real_put = store.put


def refusing_put(*a, **kw):
    raise store.StorageError("refused")


store.put = refusing_put
k = KP.begin("analyze", {"visit": "lz1abc-0a1b2c3d4f"})
k.image("photo", lambda: pj)
fail_code = k.done({"outcome": "accepted"})
store.put = real_put
k = KP.begin("analyze", {"visit": "lz1abc-0a1b2c3d50"})
k.image("photo", lambda: (_ for _ in ()).throw(RuntimeError("cannot make it")))
bad_code = k.done({"outcome": "accepted"})
check("never raises: a store that refuses gives the code fail; a picture that cannot be made the code fail; nothing reaches the caller",
      fail_code == "fail" and bad_code == "fail", (fail_code, bad_code))
real_left = L.time_left
L.time_left = lambda default=L.BUDGET: KP.MIN_LEFT - 1.0
k = KP.begin("enhance", {"visit": "lz1abc-0a1b2c3d51"})
k.image("before", lambda: pj)
time_code = k.done({"outcome": "restored"})
L.time_left = real_left
check("little time left (under MIN_LEFT): nothing is started and the code says time", time_code == "time" and not any("0a1b2c3d51" in f for f in kept_files()), time_code)
os.environ["SNAPEYES_KEEP"] = "off"
off_code = KP.begin("compose", {"visit": "lz1abc-0a1b2c3d52"}).done({})
os.environ.pop("SNAPEYES_KEEP")
nk_code = KP.begin("compose", {"visit": "lz1abc-0a1b2c3d52", "nokeep": True}).done({})
check("the switch off: code off; a request that says nokeep (the owner's laboratory): code skip; nothing written for either",
      off_code == "off" and nk_code == "skip" and not any("0a1b2c3d52" in f for f in kept_files()), (off_code, nk_code))
wipe()
real_item, real_visit_max, real_day_max = KP.ITEM_DAY_MAX, KP.VISIT_ITEMS_MAX, KP.VISIT_DAY_MAX
KP.VISIT_ITEMS_MAX = 2
codes = []
for i in range(3):
    k = KP.begin("analyze", {"visit": "lz1abc-ceiling001"})
    k.image("photo", lambda: pj)
    codes.append(k.done({"outcome": "accepted"}))
KP.VISIT_ITEMS_MAX = real_visit_max
KP.ITEM_DAY_MAX = len(kept_files()) // 2
k = KP.begin("analyze", {"visit": "lz1abc-ceiling002"})
k.image("photo", lambda: pj)
day_code = k.done({"outcome": "accepted"})
KP.ITEM_DAY_MAX = real_item
check("the ceilings of an instance: a visit keeps at most VISIT_ITEMS_MAX pictures, the instance ITEM_DAY_MAX a day; past them the code is full and nothing is written",
      codes == ["ok", "ok", "full"] and day_code == "full" and len([f for f in kept_files() if f.endswith(".jpg")]) == 2, (codes, day_code, kept_files()))
wipe()
for i in range(3):
    os.makedirs(os.path.join(STORE, "kept", day, f"v-lz1abc-other{i:05d}"), exist_ok=True)
KP.VISIT_DAY_MAX = 3
k = KP.begin("analyze", {"visit": "lz1abc-ceiling003"})
k.image("photo", lambda: pj)
full_code = k.done({"outcome": "accepted"})
KP.VISIT_DAY_MAX = real_day_max
check("the deployment's ceiling of visits a day (counted from the day's folder in the writer thread): reached, nothing is written and the code is full",
      full_code == "full" and not any("ceiling003" in f and f.endswith(".jpg") for f in kept_files()), (full_code, kept_files()))
wipe()

# ============================================================================================ 2. over HTTP
section("2. over HTTP: analyze, enhance and compose keep their pictures in the tab's visit; what is never kept")
EYE = SI.make("blue", seed=5)
PHOTO = b64(Image.open(os.path.join(REPO, "public", "assets", "sample_eye_blue_1789706902835.jpg")).convert("RGB"), 90)
real_json, real_img = L.gemini_json, L.gemini_image
VISION = {"found": True, "iris_box": [226, 225, 786, 785], "pupil_box": [425, 424, 587, 586], "glare_boxes": [], "sharpness": "sharp",
          "iris_occluded_by_eyelids_percent": 2}
L.gemini_json = lambda model, prompt, img: dict(VISION)
L.gemini_image = lambda prompt, im, size=None, thinking=None, model=None: EYE.copy()
VISIT = "lz9xyz-k3m4n5p6q7"
c1, a1 = post("/api/analyze", {"image": PHOTO, "origWidth": 1024, "origHeight": 1024, "lang": "lt", "market": "lt", "visit": VISIT,
                               "camp": "fb|paid|spring|lt-a1|ad7"})
ev_a1 = last_event("analyze")
L.gemini_json = lambda model, prompt, img: {"found": False}
c2, a2 = post("/api/analyze", {"image": PHOTO, "origWidth": 1024, "origHeight": 1024, "lang": "lt", "visit": VISIT})
ev_a2 = last_event("analyze")
L.gemini_json = lambda model, prompt, img: dict(VISION)
files = kept_files()
metas = {}
for f in files:
    if f.endswith(".json"):
        with open(os.path.join(STORE, *f.split("/")), encoding="utf-8") as fh:
            metas[f] = json.load(fh)
outs = sorted((m.get("outcome"), m.get("reason")) for m in metas.values())
check("analyze: the photo of an accepted shot and of a refused one (no eye found) are kept with their outcome beside them, in the visit's folder; the events say kept ok",
      c1 == 200 and a1.get("ticket") and c2 == 200 and a2.get("reason") == "no_eye" and outs == [("accepted", None), ("refused", "no_eye")]
      and len([f for f in files if f.endswith("-photo.jpg")]) == 2 and all(f"/v-{VISIT}/" in f for f in files)
      and ev_a1.get("kept") == "ok" and ev_a2.get("kept") == "ok", (c1, c2, outs, files, ev_a1.get("kept"), ev_a2.get("kept")))
acc = next(m for m in metas.values() if m.get("outcome") == "accepted")
check("the accepted photo's JSON: the step, the time, the verdict, the detail, the iris size, the source, and the context of the events (campaign, device class, browser, "
      "language, market, country)", acc.get("step") == "analyze" and acc.get("iso", "").endswith("Z") and acc.get("verdict") in ("good", "ok", "weak")
      and isinstance(acc.get("detail"), (int, float)) and acc.get("diameter_px") and acc["ctx"].get("src") == "fb" and acc["ctx"].get("cnt") == "ad7"
      and acc["ctx"].get("dev") == "ios" and acc["ctx"].get("br") == "safari" and acc["ctx"].get("lang") == "lt" and acc["ctx"].get("cc") == "lt", acc)
c3, e3 = post("/api/enhance", {"crop": b64(EYE.resize((1024, 1024)), 95), "mode": "artistic", "pad": 1.12, "ticket": a1["ticket"], "lang": "lt", "visit": VISIT})
ev_e = last_event("enhance")
files = kept_files()
befores, afters = [f for f in files if f.endswith("-before.jpg")], [f for f in files if f.endswith("-after.jpg")]
clean = P.unseal_full(e3["sealed"])[0] if c3 == 200 else b""
after_bytes = open(os.path.join(STORE, *afters[0].split("/")), "rb").read() if afters else b""
check("enhance: the crop as it arrived (before) and the clean 1024 px restoration as made (after: the very bytes of the sealed preview, not the watermarked display copy), "
      "beside them the outcome and the gate; the event says kept ok", c3 == 200 and len(befores) == 1 and len(afters) == 1 and after_bytes == clean
      and after_bytes != base64.b64decode(e3["image"]) and ev_e.get("kept") == "ok" and all(f"/v-{VISIT}/" in f for f in befores + afters), (c3, befores, afters, ev_e.get("kept")))
c4, comp = post("/api/compose", {"sealed": [e3["sealed"]], "lang": "lt", "visit": VISIT, "styles": []})
style = next((t["id"] for t in comp.get("tiles") or [] if t.get("available")), None)
n_before = len(kept_files())
c5, comp1 = post("/api/compose", {"sealed": [e3["sealed"]], "style": style, "lang": "lt", "visit": VISIT}) if style else (0, {})
ev_c = last_event("compose")
arts = [f for f in kept_files() if f.endswith("-art.jpg")]
art_bytes = open(os.path.join(STORE, *arts[0].split("/")), "rb").read() if arts else b""
check("compose: the large preview (1024 px, one style) is kept as the visitor gets it (watermarked), with the style beside it; the tile list keeps nothing",
      c4 == 200 and c5 == 200 and len(arts) == 1 and art_bytes == base64.b64decode(comp1["image"]) and ev_c.get("kept") == "ok"
      and len(kept_files()) == n_before + 2, (c4, c5, style, arts, ev_c.get("kept")))
n_before = len(kept_files())
c6, batch = post("/api/compose", {"sealed": [e3["sealed"]], "styles": [style], "lang": "lt", "visit": VISIT})
c7, lab = post("/api/compose", {"sealed": [e3["sealed"]], "style": style, "lang": "lt", "visit": VISIT, "nokeep": True})
c8, small_pv = post("/api/compose", {"sealed": [e3["sealed"]], "style": style, "size": 480, "lang": "lt", "visit": VISIT})
check("a batch of picker tiles, the owner's laboratory (nokeep) and a small preview keep nothing", c6 == 200 and c7 == 200 and c8 == 200 and len(kept_files()) == n_before,
      (c6, c7, c8, len(kept_files()) - n_before))
sample_file = open(os.path.join(REPO, "public", "assets", "sample_eye_blue_restored.jpg"), "rb").read()
cs, es = post("/api/enhance", {"sample": True, "image": base64.b64encode(sample_file).decode(), "lang": "lt", "visit": VISIT})
n_before = len(kept_files())
c9, sc = post("/api/compose", {"sealed": [es.get("sealed")], "style": style, "lang": "lt", "visit": VISIT}) if cs == 200 else (0, {})
check("the AI-made sample eye: its prepared restoration and a preview of it keep nothing (the compose event says sample)", cs == 200 and c9 == 200
      and len(kept_files()) == n_before and last_event("compose").get("kept") == "sample", (cs, c9, last_event("compose").get("kept")))
bot = dict(HEADERS, **{"User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"})
n_before = len(kept_files())
cb, ab = post("/api/analyze", {"image": PHOTO, "origWidth": 1024, "origHeight": 1024, "lang": "lt", "visit": VISIT}, bot)
check("a robot's photo is not kept (the event says robot)", cb == 200 and len(kept_files()) == n_before and last_event("analyze").get("kept") == "robot", (cb, last_event("analyze").get("kept")))
blob = "".join(open(os.path.join(STORE, *f.split("/")), encoding="utf-8").read() for f in kept_files() if f.endswith(".json"))
check("nothing personal in what is kept: no IP address, no user agent, no cookie, no ticket, no email", "203.0.113.77" not in blob and "Mozilla" not in blob
      and "iPhone OS" not in blob and "_fbp" not in blob and "fb.1." not in blob and a1["ticket"] not in blob and "@" not in blob, blob[:400])
c10, a10 = post("/api/analyze", {"image": PHOTO, "origWidth": 1024, "origHeight": 1024, "lang": "lt"})
c11, e11 = post("/api/enhance", {"crop": b64(EYE.resize((1024, 1024)), 95), "mode": "artistic", "pad": 1.12, "ticket": a10.get("ticket"), "lang": "lt"})
tdirs = sorted({f.split("/")[2] for f in kept_files() if f.split("/")[2].startswith("t-")})
check("a page without a visit (one of before this release): its analysis and restoration are grouped by a hash of the work ticket", c10 == 200 and c11 == 200
      and len(tdirs) == 1 and len([f for f in kept_files() if f"/{tdirs[0]}/" in f and f.endswith(".jpg")]) == 2, tdirs)
L.gemini_json, L.gemini_image = real_json, real_img

# ============================================================================================ 3. the daily clean-up
section("3. the daily clean-up: 30 days")
old_day = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 31 * 86400))
edge_day = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 29 * 86400))
for d in (old_day, edge_day):
    store.put(f"kept/{d}/v-old-visit000/120000-analyze-abcdef-photo.jpg", b"\xff\xd8x", "image/jpeg", upsert=True)
    store.put(f"kept/{d}/v-old-visit000/120000-analyze-abcdef.json", b"{}", "application/json", upsert=True)
res = KP.purge()
left = kept_files()
check("kept/<day> folders older than 30 days go with everything in them; a day 29 days old and today's stay", res.get("days") == 1 and res.get("files") == 2
      and not any(f"kept/{old_day}/" in f for f in left) and any(f"kept/{edge_day}/" in f for f in left) and any(f"kept/{day}/" in f for f in left), (res, left[:5]))
dry = KP.purge(days_kept=1, yes=False)
check("a dry run deletes nothing", len(kept_files()) == len(left) and dry.get("files", 0) >= 2, dry)
src = open(os.path.join(API, "_lib", "cleanup.py"), encoding="utf-8").read()
check("the clean-up's run calls the purge with 30 days (keep.KEEP_DAYS) on every run", "keep.purge(keep.KEEP_DAYS, yes, stop_left, say)" in src and KP.KEEP_DAYS == 30)

# ============================================================================================ 4. the admin page
section("4. the admin page Peržiūros and the deletion of a visit; health")


def admin(action, key=True, **body):
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization"] = f"Bearer {ops.mint_admin_key(3600)}"
    r = requests.post(BASE + "/api/admin", data=json.dumps(dict(body, action=action)), headers=h, timeout=120)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


ca, va = admin("kept", day=day)
vis = next((v for v in va.get("visits") or [] if v["visit"] == f"v-{VISIT}"), {})
steps = [s["step"] for s in vis.get("steps") or []]
pics = [p for s in vis.get("steps") or [] for p in s["pictures"]]
check("the view of a day: the days, the visits with their steps in time order (analyze, analyze, enhance, compose), the outcome and codes of each, and a signed link per picture",
      ca == 200 and day in va.get("days", []) and va.get("day") == day and va.get("keep_days") == 30 and steps[:3] == ["analyze", "analyze", "enhance"] and "compose" in steps
      and sorted(set(pics)) == ["after", "art", "before", "photo"] and all(isinstance(u, str) and "expires=" in u for s in vis["steps"] for u in s["pictures"].values())
      and any((s.get("meta") or {}).get("reason") == "no_eye" for s in vis["steps"]), (ca, steps, pics, va.get("days")))
cn, jn = admin("kept", key=False, day=day)
check("without the admin key: refused", cn in (401, 403), (cn, jn))
cd1, jd1 = admin("kept_delete", day=day, visit=f"v-{VISIT}", confirm="no")
cd2, jd2 = admin("kept_delete", day=day, visit=f"v-{VISIT}", confirm=f"v-{VISIT}")
gone = not any(f"/v-{VISIT}/" in f for f in kept_files())
audit_files = [os.path.join(r, f) for r, _d, fs in os.walk(os.path.join(STORE, "ops", "audit")) for f in fs]
audit_blob = "".join(open(p, encoding="utf-8").read() for p in audit_files)
check("deleting a visit needs its name typed; then every file of it goes, and the audit log says kept_delete with the day and the number of files, no link and no picture name",
      cd1 == 400 and cd2 == 200 and jd2.get("result") == "deleted" and jd2.get("deleted", 0) == 9 and gone and '"kept_delete"' in audit_blob
      and "expires=" not in audit_blob and "-photo.jpg" not in audit_blob and VISIT not in audit_blob, (cd1, cd2, jd2, gone, audit_blob[-300:]))
ch = requests.get(BASE + "/api/health", timeout=60)
check("health says keep: true here (the switch on, a store and the daily clean-up)", ch.status_code == 200 and ch.json().get("keep") is True, ch.text[:300])

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
