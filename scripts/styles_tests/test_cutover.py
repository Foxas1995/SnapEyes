# -*- coding: utf-8 -*-
"""WP18 of the v3 engine work: the catalogue switch (the cutover), in the REAL world: no shim, the registry as it is committed.

What the cutover is. A reviewed change of DATA (section 4 of the specification): the ceilings of the release-1 styles are raised (singles and the Trio to live,
Radiance, the three pair designs and Family Colours from four eyes to preview), the six legacy ids are retired, the registry's EFFECTIVE_DEFAULT is "preview",
the AI-made material sentence and one new LEGAL_UPDATED enter the legal texts, and the styles that are shown to customers have tile images. NOTHING becomes
orderable by it: only the owner's recorded tick in the admin page (L1, then L0 or its waiver, then live) does that, and he can take a style back in the same page
with no deploy. This suite proves exactly that, end to end, and nothing about the machinery that earlier suites own.

  1. the release-1 table: every id at the ceiling the specification gives it, the looks of Universe, the legacy ids retired for 1 to 8 eyes
  2. the defaults: EFFECTIVE_DEFAULT in the registry file, in the catalogue and in the pages, DEFAULT_STYLE, what a page may assume before the server answers
     (buildStage, the landing's list, the fallback catalogue, the reading of a server catalogue) and the build's guard (check item 14) on registries that break it
  3. before the owner's tick nothing is orderable: no effective stage live, no maximum of eyes, no recommended tile, a checkout of every release-1 style is a 409,
     previews and tiles are drawn for every style at preview (free, "soon")
  4. the owner's tick: the admin action makes exactly the style he ticks orderable, over its ceiling it refuses, restore gives the default, a rollback needs no deploy and
     an order already paid still renders; a plate style is refused at checkout until its 4K plates are in storage (the runbook's order)
  5. the legacy ids after the cutover: retired (known, rendered for old orders, never offered), a Stripe session made while one was live and paid after is recorded and
     priced by its own ladder, a new checkout of one is refused, the legacy engine still has its own default style
  6. the tile images: both widths for every style shown, the right shape; (LOCAL) the committed files are what scripts/make_style_tiles.py makes of the eyes
  7. the texts: the AI-made material sentence is in every terms text of every edition and language and in the pack, one LEGAL_UPDATED, the consent version untouched
  8. health: the registry reads, the 4K plates of the visible styles are expected in storage, and the cutover itself changed no price

No network, no image model (the eyes are procedural), no real eye (the LOCAL lines read the owner's eyes through SNAPEYES_CALIB when it is set).
    python test_cutover.py     prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3cutover."""
import atexit
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
SP_DIR = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP_DIR, "wave-pv", "tests") if SP_DIR else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")
NODE = shutil.which("node") or "node"
CALIB = os.environ.get("SNAPEYES_CALIB") or ""

RESULTS = []
LOCAL = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


def local(name, ok, detail=""):
    LOCAL.append(bool(ok))
    print(("LOCAL ok   " if ok else "FAIL LOCAL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


if os.environ.get("SNAPEYES_WORLD"):
    sys.exit("v3cutover runs in the real world: SNAPEYES_WORLD must not be set (the shim of the older suites would put the catalogue back the way it was before the cutover)")
for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3cutover_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)       # its own folder only (the store): gone at exit, green, red or crashed
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])          # synthetic Stripe and Resend keys, the ticket secret, a local store folder
os.environ["STYLE_PLATE_CACHE"] = os.path.join(TMP, "cache")
sys.path.insert(0, API)
import requests  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import styles_registry as R  # noqa: E402
from _lib import styles_engine as X  # noqa: E402
from _lib import stage_overrides as SO  # noqa: E402
from _lib import store, pay, ops, abtest  # noqa: E402
from _lib import markets as MK  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402
from _lib.styles import plates as PL  # noqa: E402
import _lib.styles as ST  # noqa: E402

spec_c = importlib.util.spec_from_file_location("compose", os.path.join(API, "compose.py"))
CMP = importlib.util.module_from_spec(spec_c)
spec_c.loader.exec_module(CMP)
H.MODS["compose"] = CMP
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

PACK = json.load(open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
EVENTS = []
E.record = lambda kind, **f: EVENTS.append((kind, dict(f))) or True
E.record_many = lambda kind, rows, **k: ([EVENTS.append((kind, dict(r))) for r in rows], len(rows))[1]
WHO = {"kind": "admin-v1", "exp": int(time.time()) + 3600}
LEGACY = list(CT.legacy_ids())
V3 = [i for i in CT.ids() if i not in LEGACY]
DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


def local_path(path):
    return os.path.join(STORE, *path.split("/"))


def rj(path):
    try:
        with open(local_path(path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def raised(fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        return e
    return None


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=300)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path):
    r = requests.get(BASE + path, timeout=300)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def hook(obj):
    body, sig = H.signed_event(obj, "checkout.session.completed")
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=180)
    return r.status_code, r.json()


def act(action, **body):
    return ops.ACTIONS[action](dict(body), WHO)


def refused(action, **body):
    """(status, reason) of the answer the action raised, None when it did not refuse."""
    try:
        act(action, **body)
    except store.Answer as a:
        return (a.status, a.body.get("reason"))
    except L.ClientError:
        return (400, "bad_request")
    return None


def reset():
    """No override, no audit entry, an empty cache."""
    shutil.rmtree(os.path.join(STORE, "ops", "styles"), ignore_errors=True)
    SO.invalidate()


# ---------------------------------------------------------------------------------------------------- the eyes, sealed as /api/enhance seals them
_EYES = {}


def eye(name):
    if name not in _EYES:
        jpeg = SI.jpeg_bytes(name)
        prof = EYE.profile_of_bytes(jpeg, pad=1.12, rules=("lid", "fill"))
        _EYES[name] = (jpeg, prof, P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=prof))
    return _EYES[name]


def draft(i, name, order=None, k=None):
    b = {"action": "draft", "eye": i, "crop": H.jpeg_b64(256, 10 + i), "pad": 1.12, "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work"),
         "lang": "en", "ref": f"e{i}", "sealed": eye(name)[2]["sealed"]}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def new_order(names_eyes):
    c, j = draft(1, names_eyes[0])
    assert c == 200, (c, j)
    o, k = j["order"], j["k"]
    for i, nm in enumerate(names_eyes[1:], 2):
        c, j = draft(i, nm, o, k)
        assert c == 200, (c, j)
    return o, k


def co(o, k, style, n, **kw):
    body = {"order": o, "k": k, "eyes": n, "style": style, "names": kw.pop("names", ""), "title": "", "lang": kw.pop("lang", "en"), "consent_digital": True}
    body.update(kw)
    return post("/api/checkout", body)


def comp(body):
    with contextlib.redirect_stdout(io.StringIO()):
        return CMP.compose(body, "")


def run_probe(payload):
    r = subprocess.run([NODE, os.path.join(HERE, "cutover_probe.mjs")], cwd=REPO, input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8", timeout=300)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {"error": (r.returncode, r.stderr[-900:])}


PASS_L0 = {"L0": {"mean": 4.02, "min_axis": 3.84, "by": "Art Director"}}          # an independent score above the bar, with the scorer's name

# ============================================================================================ 1. the release-1 table
section("1. the release-1 catalogue: every id at the ceiling the specification gives it")
LIVE1 = ["solo.clean", "solo.powder", "solo.universe", "solo.splash", "solo.gold"]
PREVIEW = ["solo.radiance", "duo.kiss_collision", "duo.collision_infinity", "duo.clean"]
LAB = ["solo.elements", "duo.universe", "grp.chain", "grp.universe"]
PLANNED = ["duo.reflection", "duo.radiance", "duo.gold", "grp.reflection", "grp.radiance", "grp.clean", "pet.solo", "pet.clean"]


def ceilings(i):
    lo, hi = CT.eyes_range(i)
    return [CT.ceiling(i, n) for n in range(lo, hi + 1)]


check("every id of the registry is classified here once: 5 live, 4 preview, grp.collision, 4 laboratory, 8 planned, 6 legacy (28)",
      sorted(LIVE1 + PREVIEW + LAB + PLANNED + ["grp.collision"] + LEGACY) == sorted(CT.ids()) and len(CT.ids()) == 28, sorted(set(CT.ids()) - set(LIVE1 + PREVIEW + LAB + PLANNED + LEGACY)))
check("singles at live: Clean Iris, Powder Burst, Universe (Echo and Vortex), Splash and Celestial Gold are live for one eye (the owner's release-1 singles)",
      all(CT.ceiling(i, 1) == "live" for i in LIVE1) and [CT.name_of(i) for i in LIVE1] == ["Clean Iris", "Powder Burst", "Universe", "Splash", "Celestial Gold"], [CT.ceiling(i, 1) for i in LIVE1])
check("Family Colours: live for three eyes (the Trio, which opens alone: 1.6.3), preview for four to eight (Clean Family and DG4 come first)",
      [CT.ceiling("grp.collision", n) for n in range(3, 9)] == ["live", "preview", "preview", "preview", "preview", "preview"] and CT.ceiling("grp.collision", 2) is None)
check("Radiance and the three pair designs wait at preview (DG7, DG1 and the gate pass rule of two eyes are theirs), and every other design of the first release stays in the laboratory",
      all(set(ceilings(i)) == {"preview"} for i in PREVIEW) and all(set(ceilings(i)) == {"lab"} for i in LAB), {i: ceilings(i) for i in PREVIEW + LAB})
check("planned ids (the reserved designs, Clean Family and the two pet ids) have no engine and stay planned",
      all(set(ceilings(i)) == {"planned"} and not X.ENGINE[i]["engine"] for i in PLANNED), {i: ceilings(i) for i in PLANNED})
check("the six legacy ids are RETIRED for 1 to 8 eyes (a ceiling of retired is final), still known and still renderable by the legacy engine",
      all(set(ceilings(i)) == {"retired"} and len(ceilings(i)) == 8 and CT.known(i) and CT.is_legacy(i) and CT.renderable(i, n) for i in LEGACY for n in range(1, 9)), {i: set(ceilings(i)) for i in LEGACY})
looks = CT.engine_for("solo.universe", 1)["looks"]
check("Universe: Echo and Vortex are live looks, Deep Field and Starfield stay in the laboratory (a look is never above its style)",
      looks == {"echo": "live", "vortex": "live", "deepfield": "lab", "starfield": "lab"}, looks)
check("no style shown to customers is a heart, a pet or a study: the shown ids are exactly the ten of the landing's gate table (6 + 3 + the Family tile)",
      sorted(i for i in V3 if any(c in ("preview", "live") for c in ceilings(i))) == sorted(LIVE1 + PREVIEW + ["grp.collision"]) and len(LIVE1 + PREVIEW + ["grp.collision"]) == 10)
check("the price classes did not move: Clean Iris is the one style of the black class (the class the terms row names), the others are art, and the keys are unchanged",
      [i for i in V3 if CT.is_black(i) and CT.ceiling(i, CT.eyes_range(i)[0]) != "planned"] == ["solo.clean"] and tuple(pay.PRICE_KEYS) == ("one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye")
      and tuple(abtest.PRICE_KEYS) == tuple(pay.PRICE_KEYS), "")

# ============================================================================================ 2. the defaults
section("2. the defaults: the effective default of the registry, the default style, what a page may assume, the build's guard (check item 14)")
FILE_EFF = re.search(r'^EFFECTIVE_DEFAULT = "([a-z]*)"\s*$', read("api/_lib/styles_registry.py"), re.M)
FILE_DEF = re.search(r'^DEFAULT_STYLE = "([a-z][a-z0-9_.]*)"\s*$', read("api/_lib/styles_registry.py"), re.M)
check("EFFECTIVE_DEFAULT is one line of the registry file, 'preview', and the catalogue reads it: a ceiling raised in the file makes nothing orderable by itself",
      bool(FILE_EFF) and FILE_EFF.group(1) == "preview" == R.EFFECTIVE_DEFAULT == CT.EFFECTIVE_DEFAULT, (FILE_EFF and FILE_EFF.group(1), CT.EFFECTIVE_DEFAULT))
check("DEFAULT_STYLE is Powder Burst (a v3 style of one eye that customers can see: the registry names it for the grey-eye fallback), and the legacy engine keeps its own default",
      bool(FILE_DEF) and FILE_DEF.group(1) == "solo.powder" == CT.DEFAULT_STYLE and CT.ceiling(CT.DEFAULT_STYLE, 1) == "live"
      and L.LEGACY_DEFAULT == LEGACY[0] == "celestial_gold" and L.LEGACY_DEFAULT in L.STYLES and CT.DEFAULT_STYLE not in L.STYLES, (CT.DEFAULT_STYLE, L.LEGACY_DEFAULT))
check("the legacy engine still draws with no style named (its own default: the one it always drew), and an id it does not know falls back to it, not to a v3 id",
      L.compose.__defaults__ is not None and L.LEGACY_DEFAULT in L.compose.__defaults__ and L.LEGACY_DEFAULT in L.compose_multi.__defaults__, (L.compose.__defaults__, ))
CT.set_override_source(None)           # no owner's override at all: the literal and the default
try:
    eff = {(i, n): CT.stage_of(i, n) for i in CT.ids() for n in range(1, 9)}
finally:
    CT.set_override_source(CT._store_source)
check("with no tick, every style of the v3 engine is held at preview or lower: nothing is effectively live (the legacy ids are retired, which is not live either)",
      all(s != "live" for s in eff.values()) and all(eff[(i, 1)] == "preview" for i in LIVE1) and eff[("grp.collision", 3)] == "preview" and eff[("grp.collision", 4)] == "preview"
      and eff[("solo.radiance", 1)] == "preview" and eff[("solo.elements", 1)] == "lab" and eff[("studio_black", 1)] == "retired", {k: v for k, v in eff.items() if v == "live"})
probe = run_probe({"server": {"ok": True, "open": True, "orderable_max_eyes": 1, "styles": [
    {"id": "solo.clean", "name": "Clean Iris", "slug": "clean-iris", "group": "solo", "eyes": [1, 1], "stages": {"1": "live"}},
    {"id": "solo.powder", "name": "Powder Burst", "slug": "powder-burst", "group": "solo", "eyes": [1, 1], "stages": {"1": "preview"}}]},
    "mutations": [
        {"name": "the committed registry"},
        {"name": "the state before the cutover", "allV3": "lab", "allLegacy": "live", "effectiveDefault": "", "defaultStyle": "celestial_gold"},
        {"name": "a live ceiling and no default", "effectiveDefault": ""},
        {"name": "a default of live", "effectiveDefault": "live"},
        {"name": "a legacy id still live beside live v3 styles", "stages": {"studio_black": "live"}},
        {"name": "a legacy default style beside live v3 styles", "defaultStyle": "studio_black"},
        {"name": "a default of lab is allowed", "effectiveDefault": "lab"}]})
check("the page module reads the same registry: EFFECTIVE_DEFAULT and DEFAULT_STYLE as the file says (src/shared/styles.ts)",
      probe.get("effectiveDefault") == "preview" == probe.get("fileEffectiveDefault") and probe.get("defaultStyle") == CT.DEFAULT_STYLE, probe if "error" in probe else (probe.get("effectiveDefault"), probe.get("defaultStyle")))
bs = probe.get("buildStages", {})
check("buildStage (what a page may assume before the server answers) is the server's stage with no tick: the ceiling held at the default, for every id and 1 to 8 eyes",
      bool(bs) and all(bs[i][n - 1] == eff.get((i, n)) for i in CT.ids() for n in range(1, 9)), [(i, n) for i in bs for n in range(1, 9) if bs[i][n - 1] != eff.get((i, n))][:5])
check("the landing's gallery lists the five live one-eye styles of the v3 engine in tile order (a Soon style stays off the landing: spec 1.8 rule 1), never a legacy id",
      probe.get("landing") == ["solo.powder", "solo.universe", "solo.splash", "solo.gold", "solo.clean"], probe.get("landing"))
fb = probe.get("fallback") or {}
check("the fallback catalogue (before the server answers, and when it cannot): nothing orderable, no maximum, no list of art styles, no id for one eye",
      fb == {"max": 0, "styles": [], "one": [], "eyes": [], "by": {}}, fb)
sv = probe.get("server") or {}
check("a server catalogue is read as before and names the ids orderable for one eye: Clean Iris (live) yes, Powder Burst (preview) no; the art list is empty (the black class is named by its own row)",
      sv == {"max": 1, "styles": [], "one": ["solo.clean"], "eyes": [1], "by": {"solo.clean": [1]}}, sv)
g = {m["name"]: m["problems"] for m in probe.get("guard", [])}
check("the build's cutover guard (check item 14): the committed registry and the state before the cutover pass, a default of lab passes",
      g.get("the committed registry") == [] and g.get("the state before the cutover") == [] and g.get("a default of lab is allowed") == [], g)
check("... it refuses a live ceiling with no default, a default of live, a legacy id still live beside live v3 styles and a legacy default style, each with its own sentence",
      any("EFFECTIVE_DEFAULT" in p for p in g.get("a live ceiling and no default", [])) and any('"live"' in p and "must be" in p for p in g.get("a default of live", []))
      and any("still live beside live v3" in p for p in g.get("a legacy id still live beside live v3 styles", []))
      and any("legacy style and the v3 styles are live" in p for p in g.get("a legacy default style beside live v3 styles", [])), g)
r_build = subprocess.run([NODE, os.path.join(REPO, "scripts", "check_styles.mjs")], cwd=REPO, capture_output=True, text=True, encoding="utf-8", timeout=300)
check("the whole style check passes on the committed tree and prints the cutover's registry (5 preview, 5 live, 6 retired)",
      r_build.returncode == 0 and "5 preview, 5 live, 6 retired" in r_build.stdout, (r_build.returncode, r_build.stdout[-300:], r_build.stderr[-300:]))

# ============================================================================================ 3. before the owner's tick
section("3. before the owner's tick: nothing can be bought, everything can be looked at")
reset()
check("no style is orderable for any eye count (strict: the question the checkout asks), the orderable maximum is 0, and the recommended tile is none for every eye class and count",
      all(not CT.orderable_ids(n) for n in range(1, 9)) and CT.orderable_max_eyes() == 0
      and all(CT.pick_for(n, [{"cls": c}] * n) is None for n in range(1, 9) for c in ("own", "dark_brown", "grey")), CT.orderable_ids(1))
check("every release-1 style can be PREVIEWED (a customer sees the tile, the free preview, 'soon'), the laboratory and planned ones cannot, the legacy ones cannot any more",
      all(CT.previewable(i, 1) for i in LIVE1 + ["solo.radiance"]) and all(CT.previewable(i, 2) for i in ("duo.kiss_collision", "duo.collision_infinity", "duo.clean"))
      and all(CT.previewable("grp.collision", n) for n in range(3, 9)) and not any(CT.previewable(i, 1) for i in ("solo.elements",) + tuple(LEGACY))
      and not CT.previewable("grp.chain", 3) and not CT.previewable("grp.clean", 3), "")
check("the tiles: six for one eye (Powder Burst first, Clean Iris last), three for two eyes, one for three to eight, all at preview; none is the recommended tile",
      [t["id"] for t in CT.tiles_for(1)] == ["solo.powder", "solo.universe", "solo.splash", "solo.gold", "solo.radiance", "solo.clean"]
      and [t["id"] for t in CT.tiles_for(2)] == ["duo.kiss_collision", "duo.collision_infinity", "duo.clean"]
      and all([t["id"] for t in CT.tiles_for(n)] == ["grp.collision"] for n in range(3, 9))
      and all(t["stage"] == "preview" for n in range(1, 9) for t in CT.tiles_for(n)) and all(CT.tile_list(n)["pick"] is None for n in range(1, 9)), "")
check("the public catalogue (what a customer's page is told) lists the ten shown ids at preview only, with no held, planned or legacy id",
      sorted(c["id"] for c in CT.public_catalogue()) == sorted(LIVE1 + PREVIEW + ["grp.collision"]) and all(set(c["stages"].values()) == {"preview"} for c in CT.public_catalogue()), CT.public_catalogue()[:2])
c_cat, j_cat = get("/api/checkout")
ANS = {"before": j_cat}              # the answers the landing reads, kept for the check at the end of section 4 (the page's own functions through the probe)
check("GET /api/checkout over HTTP: the same catalogue (preview only) and orderable_max_eyes 0: the landing and the buy card print 'opens soon', never a price for a style that cannot be bought",
      c_cat == 200 and j_cat.get("orderable_max_eyes") == 0 and all(set(s["stages"].values()) == {"preview"} for s in j_cat["styles"]) and len(j_cat["styles"]) == 10, (c_cat, j_cat.get("orderable_max_eyes")))
S1 = [eye("blue_round")[2]["sealed"]]
t1 = comp({"sealed": S1, "styles": []})
check("the compose endpoint answers the tile list of one eye at preview with no pick and draws nothing; a preview of Powder Burst at 480 px is drawn (free) and its tile says preview",
      t1["pick"] is None and [t["id"] for t in t1["tiles"]] == ["solo.powder", "solo.universe", "solo.splash", "solo.gold", "solo.radiance", "solo.clean"] and all(t["stage"] == "preview" for t in t1["tiles"]), t1.get("pick"))
r_p = comp({"sealed": S1, "style": "solo.clean", "size": 480})
check("a free preview of a style that cannot be bought yet is drawn (labelled, watermarked, the same engine as the file): Clean Iris at 480 px", r_p["width"] == r_p["height"] == 480 and r_p["design_used"] and r_p["tiles"][0]["stage"] == "preview", {k: r_p.get(k) for k in ("width", "design_used")})
e_leg = raised(lambda: comp({"sealed": S1, "style": "studio_black"}))
e_lab = raised(lambda: comp({"sealed": S1, "style": "solo.elements"}))
check("a retired legacy id and a laboratory style are 422 style_unavailable (stage) for a customer: never a render",
      isinstance(e_leg, store.Answer) and e_leg.status == 422 and e_leg.body.get("why") == "stage" and isinstance(e_lab, store.Answer) and e_lab.status == 422 and e_lab.body.get("why") == "stage", (e_leg, e_lab))
no_session = len(H.Fake.creates)
o, k = new_order(["blue_round"])
res = {s: co(o, k, s, 1) for s in LIVE1}
check("a checkout of each of the five live-ceiling singles is 409 style_unavailable (why stage, the style named), and no Stripe session is created: the ceiling alone sells nothing",
      all(c == 409 and j["reason"] == "style_unavailable" and j["why"] == "stage" and j.get("style") == s for s, (c, j) in res.items()) and len(H.Fake.creates) == no_session, res)
o3, k3 = new_order(["blue_round", "green_round", "blue_round"])
c3, j3 = co(o3, k3, "grp.collision", 3)
o2, k2 = new_order(["blue_round", "green_round"])
c2, j2 = co(o2, k2, "duo.kiss_collision", 2)
check("the Trio (live ceiling) and a pair design (preview) are refused the same way before the tick: 409 stage, no session",
      (c3, j3.get("why")) == (409, "stage") and (c2, j2.get("why")) == (409, "stage") and len(H.Fake.creates) == no_session, (c3, j3, c2, j2))
c_leg, j_leg = co(*new_order(["blue_round"]), "celestial_gold", 1)
check("and a checkout of a legacy id is refused too (409 stage): the six retired ids are not offered",
      c_leg == 409 and j_leg.get("why") == "stage" and len(H.Fake.creates) == no_session, (c_leg, j_leg))
cat = act("styles_catalogue")
rows = {s["id"]: s for s in cat["styles"]}
check("the admin page sees it: default_effective is preview, each live-ceiling style is preview with its ceiling live and L1 and L0 still missing, and nothing has a tick yet",
      cat["default_effective"] == "preview" and all(rows[i]["ranges"][0]["ceiling"] == "live" and rows[i]["ranges"][0]["effective"] == "preview"
                                                    and sorted(rows[i]["ranges"][0]["missing_for_live"]) == ["L0", "L1"] for i in LIVE1), rows["solo.clean"]["ranges"])

# ============================================================================================ 4. the owner's tick
section("4. the owner's tick: his ticks and his switch make exactly one style orderable; over the ceiling it refuses; a rollback needs no deploy")
reset()
x = refused("styles_override", style="solo.clean", eyes=1, stage="live", confirm=True)
check("live without L1 and L0 is refused (409 needs_ticks), as it is for every style: the ceiling raised in the registry did not remove the owner's checklist", x == (409, "needs_ticks"), x)
act("styles_override", style="solo.clean", eyes=1, tick={"L1": True}, evidence=PASS_L0)
check("ticks alone open nothing: Clean Iris is still preview, still not orderable", CT.stage_of("solo.clean", 1) == "preview" and not CT.orderable("solo.clean", 1))
r = act("styles_override", style="solo.clean", eyes=1, stage="live", confirm=True)
check("the owner's flip makes Clean Iris live: effective live, orderable, in the catalogue GET, and ONLY it (Powder Burst, Gold, Universe, Splash are still preview)",
      r["effective"] == {"1": "live"} and CT.orderable("solo.clean", 1) and CT.orderable_ids(1) == ("solo.clean",) and CT.orderable_max_eyes() == 1
      and all(not CT.orderable(i, 1) for i in LIVE1 if i != "solo.clean"), r["effective"])
c_cat, j_cat = get("/api/checkout")
check("GET /api/checkout now lists Clean Iris live for one eye and the rest at preview, and orderable_max_eyes 1", c_cat == 200 and j_cat["orderable_max_eyes"] == 1
      and {s["id"]: s["stages"].get("1") for s in j_cat["styles"] if "1" in s["stages"]}["solo.clean"] == "live"
      and {s["id"]: s["stages"].get("1") for s in j_cat["styles"] if "1" in s["stages"]}["solo.powder"] == "preview", j_cat["styles"][:1])
ANS["clean"] = j_cat
t_now = CT.tile_list(1, [{"cls": "own"}])
check("the recommended tile is a style the customer can buy: Clean Iris is the only one, so it is the pick (the table is price blind: it reads class and stage); with two live it follows the class",
      t_now["pick"] == "solo.clean", t_now["pick"])
o, k = new_order(["blue_round"])
n_before = len(H.Fake.creates)
c, j = co(o, k, "solo.clean", 1, names="Ona")
sid = (rj(f"orders/{o}/order.json") or {}).get("checkout", {}).get("session_id")
amount = int(H.Fake.creates[-1][0]["line_items[0][price_data][unit_amount]"]) if len(H.Fake.creates) > n_before else None
check("a checkout of Clean Iris now creates a session at the black price of the market (the amount is the registry's black class, read from api/_lib/markets.py), the plan is frozen and stored, "
      "and the line item names the style", c == 200 and amount == MK.MARKETS["eu"]["prices"]["one_eye_studio_black"] and (rj(f"orders/{o}/order.json") or {}).get("checkout", {}).get("plan") is not None
      and "Clean Iris" in H.Fake.creates[-1][0].get("line_items[0][price_data][product_data][name]", ""), (c, j, amount))
over = {s: refused("styles_override", style=s, eyes=n, stage="live", confirm=True) for s, n in (("solo.radiance", 1), ("duo.kiss_collision", 2), ("duo.collision_infinity", 2), ("duo.clean", 2),
                                                                                              ("grp.collision", 4), ("grp.collision", 8), ("solo.elements", 1), ("grp.chain", 3), ("grp.clean", 3))}
check("above the ceiling the owner's switch refuses even with ticks: Radiance, Kiss Collision, Collision Infinity, Clean Infinity, Family Colours from four eyes, Elements, the chain and Clean Family "
      "cannot be made live without a reviewed change of the registry",
      all(v and v[0] == 409 and v[1] in ("above_ceiling", "needs_ticks", "not_switchable") for v in over.values()), over)
for s, n in (("solo.radiance", 1), ("duo.kiss_collision", 2), ("grp.collision", 4)):
    act("styles_override", style=s, eyes=n, tick={"L1": True}, evidence=PASS_L0)
over2 = {s: refused("styles_override", style=s, eyes=n, stage="live", confirm=True) for s, n in (("solo.radiance", 1), ("duo.kiss_collision", 2), ("grp.collision", 4))}
check("... ticked, they are still refused for the ceiling (above_ceiling): a tick is not a way over the ceiling", all(v == (409, "above_ceiling") for v in over2.values()) and not CT.orderable("solo.radiance", 1), over2)
x_leg = {s: refused("styles_override", style=s, eyes=1, stage="live", confirm=True) for s in LEGACY}
check("the six retired ids cannot be switched back on from the admin page (retired is final): refused, and still not orderable",
      all(v and v[0] in (400, 409) for v in x_leg.values()) and not any(CT.orderable(s, 1) for s in LEGACY), x_leg)
# the Trio: its own ticks, per eye count
act("styles_override", style="grp.collision", eyes=3, tick={"L1": True}, evidence=PASS_L0)
act("styles_override", style="grp.collision", eyes=3, stage="live", confirm=True)
check("Family Colours for three eyes (the Trio) is switchable on its own ticks, and four to eight stay preview: the opening is per eye count",
      CT.orderable("grp.collision", 3) and not CT.orderable("grp.collision", 4) and CT.orderable_max_eyes() == 3, (CT.stage_of("grp.collision", 3), CT.stage_of("grp.collision", 4)))
act("styles_override", style="grp.collision", eyes=3, stage="preview", confirm=True)
# a plate style: the order of the runbook (plates in storage first)
act("styles_override", style="solo.powder", eyes=1, tick={"L1": True}, evidence=PASS_L0)
act("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
o, k = new_order(["blue_round"])
c_pl, j_pl = co(o, k, "solo.powder", 1)
check("a plate style the owner has switched on is refused at checkout until its 4K plates are in storage (409 plates, the plate ids named): upload first, tick second (the runbook)",
      c_pl == 409 and j_pl.get("why") == "plates" and j_pl.get("plates"), (c_pl, j_pl))
for pid in j_pl.get("plates") or []:
    store.put(PL.storage_path(pid), b"plate", "image/png", upsert=True)
c_pl2, j_pl2 = co(o, k, "solo.powder", 1)
check("... with the plates in storage the same order is accepted", c_pl2 == 200, (c_pl2, j_pl2))
r = act("styles_override", style="solo.powder", eyes=1, stage="restore", confirm=True)
check("restore gives the DEFAULT, not the ceiling: Powder Burst is preview again (only an explicit, ticked live is orderable), the registry's default is what the page says",
      r["effective"] == {"1": "preview"} and not CT.orderable("solo.powder", 1) and act("styles_catalogue")["default_effective"] == "preview", r["effective"])
# the Universe looks
act("styles_override", style="solo.universe", eyes=1, tick={"L1": True}, evidence=PASS_L0)
act("styles_override", style="solo.universe", eyes=1, stage="live", confirm=True)
check("Universe live: Echo and Vortex are the looks a customer may buy (live), Deep Field and Starfield are never offered; an order for a held look is refused",
      CT.looks_for("solo.universe", 1) == {"echo": "live", "vortex": "live"} and CT.look_orderable("solo.universe", 1, {"look": "vortex"}) and CT.look_orderable("solo.universe", 1, {})
      and not CT.look_orderable("solo.universe", 1, {"look": "deepfield"}) and CT.looks_for("solo.universe", 1, admin=True)["deepfield"] == "lab", CT.looks_for("solo.universe", 1))
act("styles_override", style="solo.universe", eyes=1, stage="preview", confirm=True)
# the rollback
r = act("styles_override", style="solo.clean", eyes=1, stage="preview", confirm=True, reason="rolled back", reason_kind="quality", in_flight="finish")
o, k = new_order(["blue_round"])
c_rb, j_rb = co(o, k, "solo.clean", 1)
check("the rollback: Clean Iris back to preview in the admin page, with no deploy: not orderable, a new checkout is 409 stage, the catalogue GET lists it at preview again, the audit log has the entries",
      r["effective"] == {"1": "preview"} and not CT.orderable("solo.clean", 1) and (c_rb, j_rb.get("why")) == (409, "stage") and CT.orderable_max_eyes() == 0
      and len(act("styles_audit", limit=50)["entries"]) >= 6 and get("/api/checkout")[1]["orderable_max_eyes"] == 0, (r["effective"], c_rb, j_rb))
check("an order paid before the rollback still renders (the render path ignores stages): renderable, and the session of the earlier checkout is still readable by spec_from and priced",
      CT.renderable("solo.clean", 1) and pay.spec_from(H.Fake.sessions[sid]["metadata"])["style"] == "solo.clean" and pay.price_cents(1, "solo.clean", "eu") == amount, "")
ANS["after"] = get("/api/checkout")[1]
# what the landing makes of the server's answers (WP18 review: the deployment takes orders here, so "open" is true in every answer; the page must still say "opens soon" and print no price while
# nothing can be ordered, and print only the prices of what can). The page's own functions run through the probe on the answers this section collected.
act("styles_override", style="solo.powder", eyes=1, tick={"L1": True}, evidence=PASS_L0)
act("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
ANS["art_only"] = get("/api/checkout")[1]
act("styles_override", style="solo.powder", eyes=1, stage="preview", confirm=True)
act("styles_override", style="solo.clean", eyes=1, stage="live", confirm=True)
act("styles_override", style="solo.powder", eyes=1, stage="live", confirm=True)
ANS["both"] = get("/api/checkout")[1]
act("styles_override", style="solo.powder", eyes=1, stage="preview", confirm=True)
act("styles_override", style="solo.clean", eyes=1, stage="preview", confirm=True)
act("styles_override", style="grp.collision", eyes=3, tick={"L1": True}, evidence=PASS_L0)
act("styles_override", style="grp.collision", eyes=3, stage="live", confirm=True)
ANS["trio_only"] = get("/api/checkout")[1]
act("styles_override", style="grp.collision", eyes=3, stage="preview", confirm=True)
ANS["closed_again"] = get("/api/checkout")[1]
NAMES = ["before", "clean", "art_only", "both", "trio_only", "after", "closed_again"]
lp = run_probe({"answers": [ANS[n] for n in NAMES]})
LR = dict(zip(NAMES, lp.get("landingReading") or []))
EU = MK.MARKETS["eu"]["prices"]
check("the deployment takes orders in every answer of this section (open is true: Stripe, the e-mail and the legal texts are set up in this harness), so the cutover's closed state is the CATALOGUE's, not the keys'",
      all(ANS[n].get("open") is True for n in NAMES) and all(LR.get(n, {}).get("deploymentOpen") is True for n in NAMES), {n: ANS[n].get("open") for n in NAMES})
check("the landing before the owner's tick: ordering open and nothing ticked is NOT open for the page: no 'from' price in the hero, no price row in the one-eye card (the page says 'opens soon', what the checkout will say with 409)",
      all(LR.get("before", {}).get(k) == v for k, v in {"deploymentOpen": True, "open": False, "from": None, "rows": {"black": False, "art": False}, "max": 0, "several": 0, "eyes": [], "forSale": []}.items()), LR.get("before"))
check("... the same after a rollback and when the owner has taken everything back: closed again, no price",
      all(LR.get(n) == LR.get("before") for n in ("after", "closed_again")), (LR.get("after"), LR.get("closed_again")))
check("with Clean Iris ticked the page is open and prints only what can be bought: 'from' is the black price and only the black row (an art style is not orderable, so the art row stays off)",
      all(LR.get("clean", {}).get(k) == v for k, v in {"deploymentOpen": True, "open": True, "from": LR["clean"]["texts"]["black"], "rows": {"black": True, "art": False}, "max": 1, "several": 0, "eyes": [1], "forSale": ["clean"]}.items()), LR.get("clean"))
check("with Powder Burst ticked alone only the art row and the art price (the black class is not orderable); with both ticked 'from' is the lower of the two and both rows",
      all(LR.get("art_only", {}).get(k) == v for k, v in {"deploymentOpen": True, "open": True, "from": LR["art_only"]["texts"]["art"], "rows": {"black": False, "art": True}, "max": 1, "several": 0, "eyes": [1], "forSale": ["powder"]}.items())
      and all(LR.get("both", {}).get(k) == v for k, v in {"deploymentOpen": True, "open": True, "from": LR["both"]["texts"]["from"], "rows": {"black": True, "art": True}, "max": 1, "several": 0, "eyes": [1], "forSale": ["powder", "clean"]}.items())
      and LR["art_only"]["texts"]["art"] != LR["art_only"]["texts"]["black"], (LR.get("art_only"), LR.get("both")))
check("with only the Trio ticked the page is open (an order can be made) but prints no one-eye price (no style can be ordered for one eye) and no price for two eyes (the several-eyes row says 'free preview now': "
      "its ladder starts at two eyes and no pair design is orderable in release 1); the one tile that is for sale is the Trio's, its price is the price of three eyes",
      all(LR.get("trio_only", {}).get(k) == v for k, v in {"deploymentOpen": True, "open": True, "from": None, "rows": {"black": False, "art": False}, "max": 3, "several": 0, "eyes": [3], "forSale": ["fam_trio"]}.items()), LR.get("trio_only"))
land = {f: read(f"src/landing/{f}") for f in ("ordering.ts", "Hero.tsx", "PriceTable.tsx", "StyleGallery.tsx", "StyleTile.tsx", "tileState.ts", "heroPrice.ts")}
catalogue_ts = read("src/shared/catalogue.ts")
check("the landing's components use those functions and no longer print a price unconditionally: ordering.ts opens through ordersOpen and hands the page a sale catalogue (nothing while ordering is closed), the hero prints fromOf over the one-eye styles for sale (never the black price by itself), "
      "the price table prints a row by the classes for sale and the several-eyes row by severalMax (never cat.max), a tile prints a price only for a style the catalogue lists live for its number of eyes (liveFor), the combo card follows severalMax",
      "ordersOpen(v.open" in land["ordering.ts"] and "sale = saleCatalogue(v.open, catalogue)" in land["ordering.ts"] and "export function useSaleCatalogue" in land["ordering.ts"]
      and "return ordersOpen(deploymentOpen, c) ? c : NOTHING_FOR_SALE" in catalogue_ts
      and "heroPrice(" in land["Hero.tsx"] and "useSaleCatalogue" in land["Hero.tsx"] and "prices.fromOf(sale.one)" in land["heroPrice.ts"] and "one_eye_studio_black" not in land["Hero.tsx"] + land["heroPrice.ts"]
      and "classLive('black')" in land["PriceTable.tsx"] and "classLive('art')" in land["PriceTable.tsx"] and "severalMax(cat)" in land["PriceTable.tsx"] and "cat.max" not in land["PriceTable.tsx"]
      and "tileState(tile.id, sale)" in land["StyleTile.tsx"] and "liveFor(sale, style," in land["tileState.ts"] and "severalMax(" in land["StyleGallery.tsx"] and "useSaleCatalogue" in land["StyleGallery.tsx"], "")
reset()

# ============================================================================================ 5. the legacy ids after the cutover
section("5. the six legacy ids: retired, readable for the orders already made, never offered")
check("each legacy id: known, retired, not orderable, not previewable (customer or admin), renderable for an old order, still its own price class (black for one, art for the others)",
      all(CT.known(i) and CT.stage_of(i, 1) == "retired" and not CT.orderable(i, 1) and not CT.previewable(i, 1) and not CT.previewable(i, 1, admin=True) and CT.renderable(i, 1)
          for i in LEGACY) and CT.is_black("studio_black") and not any(CT.is_black(i) for i in LEGACY if i != "studio_black"), "")


class PreCutover:
    """The catalogue as a session of before the cutover saw it: the legacy ids live (in memory, for the length of a block)."""
    def __enter__(self):
        self.old = {i: CT.STYLES[i]["stage"] for i in LEGACY}
        for i in LEGACY:
            CT.STYLES[i]["stage"] = "live"

    def __exit__(self, *a):
        for i, s in self.old.items():
            CT.STYLES[i]["stage"] = s


sess = {}
with PreCutover():
    for style, nm in (("studio_black", "Ona"), ("supernova", "Jonas")):
        o_, k_ = new_order(["blue_round"])
        c_, j_ = co(o_, k_, style, 1, names=nm)
        sess[style] = (o_, k_, c_, (rj(f"orders/{o_}/order.json") or {}).get("checkout", {}).get("session_id"))
check("before the cutover a Stripe page was opened for Studio Black and for Supernova (both created: 200)", all(v[2] == 200 and v[3] for v in sess.values()), sess)
c_new, j_new = co(*new_order(["blue_round"]), "studio_black", 1)
check("after it a NEW checkout of Studio Black is refused (409 stage)", (c_new, j_new.get("why")) == (409, "stage"), (c_new, j_new))
paid = {}
for style, (o_, k_, c_, sid_) in sess.items():
    n_mails = len(H.Fake.emails)
    c2_, j2_ = hook(H.pay_session(sid_, email=f"{style}@example.com"))
    paid[style] = (c2_, rj(f"orders/{o_}/paid.json"), [m for m, _ in H.Fake.emails[n_mails:] if m["to"] == [f"{style}@example.com"]])
check("the two sessions are paid AFTER the cutover: the webhook records both, spec_from reads them, and each is priced by its own ladder (black for Studio Black, art for Supernova; no amount mismatch)",
      all(v[0] == 200 and v[1] for v in paid.values()) and paid["studio_black"][1]["amount_total"] == MK.MARKETS["eu"]["prices"]["one_eye_studio_black"]
      and paid["supernova"][1]["amount_total"] == MK.MARKETS["eu"]["prices"]["one_eye_art"] and not any("amount_mismatch" in v[1] for v in paid.values()), {s: (v[0], v[1] and v[1].get("amount_total")) for s, v in paid.items()})
check("the confirmation e-mails of those orders name the legacy style as the customer chose it (Studio Black, Supernova): the retired names are printed for the orders that are theirs",
      all(v[2] and name in v[2][0]["text"] for v, name in ((paid["studio_black"], "Studio Black"), (paid["supernova"], "Supernova"))), [bool(v[2]) for v in paid.values()])
check("a legacy order is made by the legacy engine through the master plan: its plan is one art step of the legacy module, and the legacy engine's styles are untouched",
      all(CT.engine_for(i, 1)["module"] == "legacy" and CT.engine_for(i, 3)["module"] == "legacy" for i in LEGACY) and tuple(L.STYLES) == tuple(LEGACY), "")

# ============================================================================================ 6. the tile images
section("6. the tile images of the styles shown to customers")
shown = [i for i in CT.ids() if any(CT.ceiling(i, n) in ("preview", "live") for n in range(CT.eyes_range(i)[0], CT.eyes_range(i)[1] + 1))]
dims = {}
for i in shown:
    for w in (480, 800):
        p = os.path.join(REPO, "public", "assets", "atelier", f"style-{CT.slug_of(i)}-{w}.webp")
        try:
            with Image.open(p) as im:
                dims[(i, w)] = (im.format, im.size, os.path.getsize(p))
        except OSError:
            dims[(i, w)] = None
check("every shown style has a WEBP tile at 480 and at 800 px wide, none missing (the build's item 8 says the same of the files)", len(shown) == 10 and all(v and v[0] == "WEBP" and v[1][0] == w for (i, w), v in dims.items()), {k: v for k, v in dims.items() if not v})
check("the shape: one eye and the Trio are square, a pair is 3:2 (the family's default canvas); none is over 150 kB, so the gallery stays light",
      all(dims[(i, w)][1][0] == dims[(i, w)][1][1] for i in shown if CT.eyes_range(i)[1] <= 1 or i == "grp.collision" for w in (480, 800))
      and all(abs(dims[(i, w)][1][1] / dims[(i, w)][1][0] - 2 / 3) < 0.01 for i in shown if i.startswith("duo.") for w in (480, 800))
      and all(v[2] < 150_000 for v in dims.values()), {k: v for k, v in dims.items() if v[2] >= 150_000})
tile_bytes = {k: open(os.path.join(REPO, "public", "assets", "atelier", f"style-{CT.slug_of(k[0])}-{k[1]}.webp"), "rb").read() for k in dims}
check("no two tiles are the same picture, and no tile is a copy of an image of the repository's legacy renders (the shared slug celestial-gold now shows the new Celestial Gold)",
      len({hashlib.sha256(b).hexdigest() for b in tile_bytes.values()}) == len(tile_bytes), "")
tool = read("scripts/make_style_tiles.py")
check("the tile tool is part of the repository and names no key and no image model; the eyes it reads are outside it (--eyes), and no eye file is in the repository",
      "--eyes" in tool and "GEMINI" in tool and "gemini(" not in tool.lower() and not any(f.lower().endswith(("_2_enhanced.jpg", "_0_clientcrop.jpg")) for _r, _d, fs in os.walk(os.path.join(REPO, "public")) for f in fs), "")
if CALIB and all(os.path.isfile(os.path.join(CALIB, f)) for f in ("own215120_2_enhanced.jpg", "drv_w03_2_enhanced.jpg", "drv_w04_2_enhanced.jpg")):
    out_dir = os.path.join(TMP, "tiles")
    r_t = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "make_style_tiles.py"), "--eyes", CALIB, "--out", out_dir], capture_output=True, text=True, encoding="utf-8", timeout=900)
    same = {k: open(os.path.join(out_dir, f"style-{CT.slug_of(k[0])}-{k[1]}.webp"), "rb").read() == b for k, b in tile_bytes.items()} if r_t.returncode == 0 else {}
    local("the committed tile images are byte for byte what scripts/make_style_tiles.py makes of the owner's eyes with this code (the seed comes from the eye ids)", r_t.returncode == 0 and all(same.values()) and len(same) == 20,
          (r_t.returncode, r_t.stderr[-300:], [k for k, v in same.items() if not v]))
else:
    print("   (skipped: SNAPEYES_CALIB does not name the folder with the owner's restored eyes)", flush=True)

# ============================================================================================ 7. the texts
section("7. the texts of the cutover: the AI-made material sentence, one date, the consent untouched")
ai_src = read("src/shared/aiMaterial.ts")
legal_src = read("src/shared/legal.ts")
terms_src = {x: read(f"src/legal/docs/terms{x}.ts") for x in ("", ".lt", ".hu")}
upd = re.search(r"export const LEGAL_UPDATED = '(\d{4}-\d\d-\d\d)';", legal_src)
check("the AI-made material sentence is PUBLISHED by this deploy (AI_MATERIAL_PUBLISHED is true) and the terms take it through aiBlocks in each of the four languages (en and de in terms.ts, lt, hu)",
      "export const AI_MATERIAL_PUBLISHED = true;" in ai_src and "...aiBlocks('en')" in terms_src[""] and "...aiBlocks('de')" in terms_src[""] and "...aiBlocks('lt')" in terms_src[".lt"]
      and "...aiBlocks('hu')" in terms_src[".hu"], [t.count("...aiBlocks(") for t in terms_src.values()])
# (a checkout of this repository has CRLF line ends on a machine with core.autocrlf, and read() keeps them: the pattern takes either)
SENT = {l: re.search(r"^  %s:\r?\n\s+['\"](.+)['\"],?\s*$" % l, ai_src, re.M) for l in ("en", "de", "lt", "hu")}
docs = PACK.get("docs", {})
check("the sentence is in the terms of the built pack (the one the confirmation e-mail quotes) in English, German, Lithuanian and Hungarian, and the pack's date is the new LEGAL_UPDATED",
      all(SENT[l] and SENT[l].group(1).replace("\\'", "'")[:60] in docs[l]["terms"]["text"] for l in ("en", "de", "lt", "hu")) and bool(upd) and PACK["updated"] == upd.group(1) == "2026-10-06", (upd and upd.group(1), PACK.get("updated")))
check("one LEGAL_UPDATED for every legal page moved with it (2026-10-06, the day of the switch) and is not in the future; the consent version and its texts are untouched (2026-09-30.2)",
      upd.group(1) <= time.strftime("%Y-%m-%d") and pay.CONSENT_VERSION == "2026-09-30.2", (upd and upd.group(1), pay.CONSENT_VERSION))
check("the texts hold no dash and no claim the claims scan refuses: the text check of the build is green on the whole tree (it is the one that runs inside the build and reads these files)",
      not re.search(DASH, ai_src) and not re.search(DASH, terms_src[""]), "")

# ============================================================================================ 8. health, prices
section("8. health: the registries read and the visible styles' 4K plates are expected in storage; the switch changed no price")
h0 = PL.health()
fams = PL.expected_families()
check("the registries read (health.styles true) and the visible styles now expect their 4K plates: CLOUD, CROWN, SPIRAL and DUST are expected (Radiance and the pair designs need none of their own)",
      h0["styles"] is True and {"P-SN-CLOUD", "P-SP-CROWN", "P-DN-SPIRAL", "P-UV-DUST"} <= set(fams), (h0, sorted(fams)))
check("with an empty storage plates_4k is false (the admin's attention card says so and the checkout answers 409 plates): the plates are uploaded BEFORE the owner ticks a plate style",
      h0["plates_4k"] is False or any(store.exists(PL.storage_path(p)) for p in sorted(PL.storage_ids([f for f in fams if PL._FAMILIES.get(f, {}).get("store4k")]))[:1]), h0)
sample = sorted(PL.storage_ids([f for f in fams if PL._FAMILIES.get(f, {}).get("store4k")]))[0]
store.put(PL.storage_path(sample), b"plate", "image/png", upsert=True)
check("... and with the sample plate stored it is true (the probe asks storage for one sample of the visible styles' plates)", PL.health()["plates_4k"] is True, PL.health())
gold = {m: {k: MK.MARKETS[m]["prices"][k] for k in MK.MARKETS[m]["prices"]} for m in MK.MARKETS}
check("the cutover changed no price: the ladders of every market are the keys' four numbers, and the price of every id for 1 to 8 eyes follows the class (black or art) then the ladder, both ways",
      all(pay.price_cents(n, i, m) == (gold[m]["one_eye_studio_black"] if CT.is_black(i) else gold[m]["one_eye_art"]) if n == 1 else pay.price_cents(n, i, m) == pay.price_cents(n, "solo.gold", m)
          for m in MK.MARKETS for i in CT.ids() for n in range(1, 9) if CT.in_range(i, n)), "")

ok = sum(RESULTS)
print(f"\n{ok} of {len(RESULTS)} passed" + (f"   (+ {len(LOCAL)} local checks)" if LOCAL else ""))
sys.exit(0 if ok == len(RESULTS) and all(LOCAL) else 1)
