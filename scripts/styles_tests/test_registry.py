# -*- coding: utf-8 -*-
"""WP1 of the v3 engine work: the style registry (api/_lib/styles_registry.py, styles_engine.py), the catalogue helpers
(api/_lib/catalogue.py), the one price-class predicate, the readers that moved onto them, and the build check
(scripts/check_styles.mjs). Tests I1 (registry and build checks, with a negative test per refusal), I2 (price parity), I3 (legacy
compatibility: the six legacy ids render the same bytes, old specs read), IE1 (the build-check hazards that apply here), IE2 (import
weight) and IE11 (the public catalogue lists only preview and live ids; the override math). Work package 2 added section 8 and the matching
refusals of section 5: the words for the layouts are one table (api/_lib/layout_names.py), with golden strings in four languages for the
legacy ids, the e-mails and the page code reading it, and the build and text checks refusing a second table or a bad word (I1, I15).
No network, no image model, no real eye: a synthetic iris, the engine functions and the compose handler called in-process, the real
check scripts run by Node on copies of the repository with one mutated line each.
    python test_registry.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as the entry v3reg (SNAPEYES_REPO names the checkout)."""
import ast
import atexit
import base64
import contextlib
import copy
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
TMP = os.path.join(HERE, "wp1_tmp")
NODE = shutil.which("node") or "node"

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
atexit.register(shutil.rmtree, TMP, ignore_errors=True)   # its own folder only (store, plate cache): gone at exit, green, red or crashed
os.environ.update({"SNAPEYES_TICKET_SECRET": "wp1-ticket-secret-for-tests-0123456789abcdef", "PYTHONIOENCODING": "utf-8"})
sys.path.insert(0, API)
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as C  # noqa: E402
from _lib import pay, pay_hu, abtest, markets as MK, experiments as XP  # noqa: E402
from _lib import styles_registry as R, styles_engine as X, layout_names as LN  # noqa: E402
import compose as COMPOSE  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
LEGACY = ["celestial_gold", "deep_nebula", "emerald_aurora", "obsidian_smoke", "supernova", "studio_black"]   # the order of iris.py
OLD_NAMES = {"studio_black": "Studio Black", "celestial_gold": "Celestial Gold", "deep_nebula": "Deep Nebula",
             "emerald_aurora": "Emerald Aurora", "obsidian_smoke": "Obsidian Smoke", "supernova": "Supernova"}
OLD_LAYOUTS = {1: ("single",), 2: ("duo", "fusion"), 3: ("triangle", "row"), 4: ("grid", "row"), 5: ("galaxy",), 6: ("galaxy",),
               7: ("galaxy",), 8: ("galaxy",)}
BRANDS = ["Clean Iris", "Powder Burst", "Universe", "Splash", "Celestial Gold", "Radiance", "Clean Infinity", "Clean Family",
          "Kiss Collision", "Collision Infinity", "Family Colours"]


def read(rel, repo=REPO):
    with open(os.path.join(repo, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


def run_node(args, cwd=REPO, timeout=300):
    r = subprocess.run([NODE] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def last_json(text):
    try:
        return json.loads(text.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return None


# ============================================================================================ 1. the registry itself
section("1. the registry: shape, ids, stages, hash")
pub_text = read("api/_lib/styles_registry.py")
eng_text = read("api/_lib/styles_engine.py")
pub_lit = json.loads(pub_text[pub_text.index("\nSTYLES = {") + len("\nSTYLES = "):])
eng_lit = json.loads(eng_text[eng_text.index("\nENGINE = {") + len("\nENGINE = "):])
check("the literal in each file is plain JSON and is what Python imports", pub_lit == R.STYLES and eng_lit == X.ENGINE)
check("both files are ASCII and hold no en or em dash", all(ord(ch) < 128 for ch in pub_text + eng_text) and not re.search(DASH, pub_text + eng_text))
check("28 ids: the 6 legacy ones live, 14 in the laboratory, 8 planned; nothing of v3 is above the laboratory",
      len(R.STYLES) == 28 and [i for i, d in R.STYLES.items() if d["legacy"] == 1] == LEGACY
      and all(R.STYLES[i]["stage"] == "live" for i in LEGACY)
      and sum(1 for d in R.STYLES.values() if d["stage"] == "lab") == 14 and sum(1 for d in R.STYLES.values() if d["stage"] == "planned") == 8,
      {d["stage"] for d in R.STYLES.values()})
check("the two literals have the same ids; a planned style has no engine, every other one has",
      set(R.STYLES) == set(X.ENGINE) and all((R.STYLES[i]["stage"] == "planned") == (not X.ENGINE[i]["engine"]) for i in R.STYLES))
check("the legacy ids are in the order api/_lib/iris.py STYLES has always had (iris asserts it at import)", list(L.STYLES) == LEGACY == list(C.legacy_ids()))
check("the legacy engine entries are module legacy, nothing else is", {i for i, e in X.ENGINE.items() if e["engine"].get("module") == "legacy"} == set(LEGACY))
check("the eleven brand names of the catalogue and the held ones are in the registry (English in every language)",
      all(any(d["name"] == b for d in R.STYLES.values()) for b in BRANDS)
      and {d["name"] for d in R.STYLES.values()} >= {"Elements", "Reflection", "Infinity Chain", "Radiance Duo", "Celestial Gold Duo"})
check("the names of the six legacy ids are the old STYLE_NAMES; pay and pay_hu read them from the registry",
      {i: C.name_of(i) for i in LEGACY} == OLD_NAMES and all(pay.STYLE_NAMES[i] == OLD_NAMES[i] and pay_hu.STYLE_NAMES[i] == OLD_NAMES[i] for i in LEGACY)
      and C.name_of("nothing") == "nothing")
check("price classes: studio_black is black and the other five legacy ids art; the v3 clean ids are black",
      [i for i in LEGACY if C.is_black(i)] == ["studio_black"] and C.price_class("solo.clean") == "black" and C.price_class("pet.clean") == "black"
      and C.price_class("solo.powder") == "art" and C.price_class("nothing") == "art" and C.price_class(None) == "art")
check("the owner's price keys are unchanged", pay.PRICE_KEYS == ("one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye")
      and all(set(m["prices"]) == set(pay.PRICE_KEYS) for m in MK.MARKETS.values()))
check("no heart and no pet symbol in any id, slug or name",
      not [w for d in R.STYLES.values() for w in re.split(r"[^a-z]+", (d["slug"] + " " + d["name"]).lower()) if w in ("heart", "hearts", "love", "cupid", "paw", "paws", "dog", "cat", "bone")])
check("slugs are unique, except that a legacy id and a v3 id of one name share one",
      len({d["slug"] for d in R.STYLES.values()}) == 27 and [i for i, d in R.STYLES.items() if d["slug"] == "celestial-gold"] == ["solo.gold", "celestial_gold"])
check("registry hash: 12 hex digits, the hash of the canonical ASCII text",
      re.fullmatch(r"[0-9a-f]{12}", C.registry_hash()) and C.registry_hash() == hashlib.sha256(C.canonical().encode("ascii")).hexdigest()[:12])
check("tile_order is unique per group among legacy ids and among v3 ids",
      len({(d["group"], d["legacy"], d["tile_order"]) for d in R.STYLES.values() if d["tile_order"]}) == sum(1 for d in R.STYLES.values() if d["tile_order"]))

# ============================================================================================ 2. the catalogue helpers
section("2. catalogue helpers on the real registry and on patched copies")


@contextlib.contextmanager
def patched(public=None, engine=None, built=(), override=None):
    """The catalogue with a modified deep copy of the registry (and the engine modules in `built` treated as present)."""
    old = (C.STYLES, C.ENGINE, set(C.ENGINES_BUILT_EXTRA), C._override_source)
    C.STYLES, C.ENGINE = copy.deepcopy(old[0]), copy.deepcopy(old[1])
    C.ENGINES_BUILT_EXTRA.update(built)
    C.set_override_source(override)
    try:
        if public:
            public(C.STYLES)
        if engine:
            engine(C.ENGINE)
        yield
    finally:
        C.STYLES, C.ENGINE = old[0], old[1]
        C.ENGINES_BUILT_EXTRA.clear()
        C.ENGINES_BUILT_EXTRA.update(old[2])
        C.set_override_source(old[3])


check("known: every id, and nothing else (not None, not a list, not a number)",
      all(C.known(i) for i in R.STYLES) and not any(C.known(x) for x in ("nothing", "", None, 3, ["solo.clean"], {"a": 1})))
check("stage_of of a legacy id is live for 1 to 8 eyes and None otherwise; orderable and previewable agree",
      all(C.stage_of(i, n) == "live" and C.orderable(i, n) and C.previewable(i, n) for i in LEGACY for n in range(1, 9))
      and all(C.stage_of(i, n) is None and not C.orderable(i, n) for i in LEGACY for n in (0, 9, True, "3", None)))
built_dirs = {m: os.path.isdir(os.path.join(API, "_lib", "styles", m)) for m in ("singles", "collision", "universe")}
check("engine_built: legacy always, a v3 family exactly when its folder api/_lib/styles/<family> exists",
      C.engine_built("legacy") and all(C.engine_built(m) == built_dirs[m] for m in built_dirs), built_dirs)
check("a laboratory or planned v3 id is never orderable and never previewable for a customer, whatever its engine",
      not any(C.orderable(i, n) or C.previewable(i, n) for i in R.STYLES if not R.STYLES[i]["legacy"] for n in range(1, 9)))
with patched(built=("singles",)):
    check("a laboratory style is previewable for the admin only, and only once its engine module is built",
          C.previewable("solo.powder", 1, admin=True) and not C.previewable("solo.powder", 1) and not C.orderable("solo.powder", 1)
          and C.previewable("solo.universe", 1, admin=True) == built_dirs["universe"])
check("without its engine module even the admin cannot preview a laboratory style",
      C.previewable("solo.powder", 1, admin=True) == built_dirs["singles"])
with patched(public=lambda s: s["grp.collision"].update(stage="lab", stage_by_eyes={"3": "live", "4-6": "preview"}), built=("collision",)):
    check("stage_by_eyes: the ceiling per eye range (3 live, 4 to 6 preview, 7 and 8 the style's own stage, lab)",
          [C.ceiling("grp.collision", n) for n in range(2, 9)] == [None, "live", "preview", "preview", "preview", "lab", "lab"]
          and C.orderable("grp.collision", 3) and not C.orderable("grp.collision", 4) and C.previewable("grp.collision", 5)
          and not C.previewable("grp.collision", 7) and C.previewable("grp.collision", 7, admin=True))
    check("the layouts, the design and the work_side of a style follow the eye count (trio and diag for 3, the family design for 4 to 8)",
          C.layouts_for("grp.collision", 3) == ("trio", "diag") and C.default_layout("grp.collision", 5) == "brick"
          and C.layouts_for("grp.collision", 2) == () and C.engine_for("grp.collision", 3)["design"] == "trio"
          and C.engine_for("grp.collision", 5)["design"] == "family" and C.engine_for("grp.collision", 5)["work_side"] == 2048
          and C.engine_for("grp.collision", 3)["work_side"] == 2048 and C.work_side("grp.collision", 8) == 2048  # WP7B: the trio is capped at 2048 px as the family is
          and C.work_side("grp.clean", 3) == 4096 and C.work_side("grp.clean", 5) == 2048)
RANK = {"planned": 0, "lab": 1, "preview": 2, "live": 3}
eff = {(c, o): C.effective_stage(c, o) for c in ("planned", "lab", "preview", "live", "retired") for o in (None, "planned", "lab", "preview", "live", "retired", "bogus")}
check("effective_stage = min(ceiling, override): an override can only lower, an unknown one is ignored, retired is final",
      all(v == (c if c == "retired" or o not in RANK else min((c, o), key=RANK.get)) for (c, o), v in eff.items())
      and eff[("preview", "live")] == "preview" and eff[("live", "lab")] == "lab" and eff[("retired", "live")] == "retired"
      and C.effective_stage(None, "live") is None, eff)
with patched(override=lambda i, n: "lab" if i == "studio_black" else ("preview" if i == "supernova" and n >= 3 else None)):
    check("stage_of reads the override: lowered where it says so, untouched elsewhere; orderable and previewable follow it",
          C.stage_of("studio_black", 1) == "lab" and not C.orderable("studio_black", 1) and C.previewable("studio_black", 1, admin=True)
          and not C.previewable("studio_black", 1) and C.stage_of("supernova", 2) == "live" and C.stage_of("supernova", 3) == "preview"
          and C.orderable("celestial_gold", 4) and not C.orderable("supernova", 4) and C.previewable("supernova", 4))
check("the override is gone after set_override_source(None): the effective stage is the ceiling", C.stage_of("studio_black", 1) == "live")
with patched(override=lambda i, n: "live"):
    check("an override above the ceiling lowers nothing and raises nothing", C.stage_of("solo.powder", 1) == "lab" and C.stage_of("studio_black", 2) == "live")
check("orderable_max_eyes is 8 and every eye count has the six legacy styles to order", C.orderable_max_eyes() == 8 and C.orderable_ids(3) == tuple(LEGACY))
with patched(public=lambda s: [s[i].update(stage_by_eyes={"4-8": "preview"}) for i in LEGACY]):
    check("orderable_max_eyes follows the stage per eye count: live up to 3 eyes, preview above (the buy card then says up to 3)",
          C.orderable_max_eyes() == 3 and C.orderable_ids(5) == () and C.previewable_ids(5) == tuple(LEGACY))
with patched(public=lambda s: [s[i].update(stage="retired") for i in LEGACY]):
    check("retired ids stay known and renderable, are neither orderable nor previewable, and then nothing can be bought",
          all(C.known(i) and C.renderable(i, 2) and not C.orderable(i, 2) and not C.previewable(i, 2, admin=True) for i in LEGACY)
          and C.orderable_max_eyes() == 0 and C.pick_for(1) is None and C.public_catalogue() == [])
check("renderable: the six legacy ids for every eye count and nothing of v3 until its engine folder exists",
      all(C.renderable(i, n) for i in LEGACY for n in (1, 8)) and C.renderable("solo.powder", 1) == built_dirs["singles"]
      and (C.renderable_ids(2) == tuple(LEGACY) or any(built_dirs.values())))
check("public_catalogue (what a customer's page may be told) lists the six legacy ids at live, no laboratory id, no planned id",
      [e["id"] for e in C.public_catalogue()] == LEGACY and all(set(e["stages"].values()) == {"live"} for e in C.public_catalogue()))


def scenario(s):
    for sid in ("solo.powder", "solo.gold", "solo.radiance", "solo.universe", "duo.kiss_collision", "duo.collision_infinity"):
        s[sid]["stage"] = "live"
    s["solo.elements"]["stage"] = "preview"
    s["solo.universe"].update(pick=["own"], reason={"own": "reason.solo_universe.own"}, tile_order=1)
    s["solo.powder"]["tile_order"] = 2


GATE_OK = {"lid": {"ok": True}, "fill": {"ok": True}}
with patched(public=scenario, built=("singles", "universe", "collision")):
    t1 = C.tiles_for(1)
    check("tiles_for(1): the live v3 tiles in tile order, then the legacy ones; a laboratory style is in the admin's list only",
          [t["id"] for t in t1] == ["solo.universe", "solo.powder", "solo.gold", "solo.radiance"] + ["studio_black", "celestial_gold", "deep_nebula", "emerald_aurora", "obsidian_smoke", "supernova"]
          and all(t["available"] and t["why"] is None for t in t1)
          and "solo.splash" not in [t["id"] for t in t1] and "solo.splash" in [t["id"] for t in C.tiles_for(1, admin=True)], [t["id"] for t in t1])
    check("pick_for: the first buyable tile whose pick lists the set's colour class (grey radiance, dark brown gold, own universe), else the default style",
          C.pick_for(1, [{"cls": "grey", "gate": GATE_OK}]) == "solo.radiance" and C.pick_for(1, [{"cls": "dark_brown", "gate": GATE_OK}]) == "solo.gold"
          and C.pick_for(1, [{"cls": "own", "gate": GATE_OK}]) == "solo.universe" and C.pick_for(1) == "solo.universe"
          and C.set_class([{"cls": "own"}, {"cls": "grey"}]) == "grey" and C.set_class([{"cls": "dark_brown"}, {"cls": "own"}]) == "dark_brown"
          and C.set_class(None) == "own" and C.set_class([]) == "own" and C.set_class("x") == "own")
    bad_fill = [{"cls": "own", "gate": {"lid": {"ok": True}, "fill": {"ok": False}}}]
    td = {x["id"]: x for x in C.tiles_for(1, bad_fill)}
    check("a hard style whose gate rule failed is greyed with the reason gate; advisory styles stay available",
          not td["solo.universe"]["available"] and td["solo.universe"]["why"] == "gate" and td["solo.powder"]["available"] and td["solo.gold"]["available"])
    check("a hard style on an eye without a sealed gate value is held back with the reason reseal (a version 1 seal)",
          {x["id"]: x["why"] for x in C.tiles_for(1, [{"cls": "own"}])}["solo.universe"] == "reseal")
    check("the recommended tile is never one the customer cannot buy: a gate-failed pick moves on to the next, and to the default at the end",
          C.pick_for(1, bad_fill) == "solo.powder" and C.pick_for(1, [{"cls": "own"}]) == "solo.powder")
    pairs = [{"cls": "own", "gate": GATE_OK, "pupil": {"cls": "bar"}}, {"cls": "own", "gate": GATE_OK, "pupil": {"cls": "round"}}]
    d2 = {x["id"]: x for x in C.tiles_for(2, pairs, admin=True)}
    # WP10 review fix: the collision engine raises NotOffered for a bar pupil in EVERY design (Kiss too), so every pair tile of it says bar_pupil; this check used to
    # say "Kiss does not" and so showed a Kiss tile that could not be drawn (the three tiles of the pair are the engine's, so the answer is the engine's)
    check("a bar pupil refuses every pair design of the collision family (bar_pupil: Infinity, Clean Infinity, Kiss); the pair tiles carry their layouts",
          not d2["duo.collision_infinity"]["available"] and d2["duo.collision_infinity"]["why"] == "bar_pupil"
          and not d2["duo.kiss_collision"]["available"] and d2["duo.kiss_collision"]["why"] == "bar_pupil"
          and d2["duo.kiss_collision"]["layouts"] == ["pair"] and C.pick_for(2, [{"cls": "own", "gate": GATE_OK}] * 2) == "duo.kiss_collision",
          {k: (v["available"], v["why"]) for k, v in d2.items()})
    check("public_catalogue lists only ids at preview or live (a laboratory or planned id never reaches a customer's page)",
          {e["id"] for e in C.public_catalogue()} == {"solo.powder", "solo.universe", "solo.gold", "solo.radiance", "duo.kiss_collision", "duo.collision_infinity", "solo.elements", *LEGACY}
          and all(set(e["stages"].values()) <= {"preview", "live"} for e in C.public_catalogue())
          and not any(e["id"] in ("duo.universe", "duo.reflection", "grp.collision", "pet.solo") for e in C.public_catalogue()))
with patched(public=lambda s: s["solo.powder"].update(stage="live"), built=("singles",)):
    check("engine_for: module, design, looks, clean, gate rules, plates, atlas, canvases, the default plan of one art step, fill and work sizes",
          C.engine_for("solo.powder", 1) == {"module": "singles", "design": "powder", "looks": {}, "clean": 0, "gate_rules": "lid", "plates": ["P-SN-CLOUD"],
                                             "atlas": ["chips"], "canvases": ["1:1", "4:5", "9:19.5"], "steps": ["art"], "fill_side": 0, "work_side": 4096}
          and C.engine_for("solo.powder", 2) is None and C.engine_for("duo.reflection", 2) is None and C.engine_for("nothing", 1) is None
          and C.engine_for("solo.universe", 1)["looks"]["vortex"] == "lab" and C.engine_for("duo.clean", 2)["clean"] == 1
          and C.gate_policy("solo.universe") == "hard" and C.gate_policy("solo.clean") == "advisory" and C.gate_policy("studio_black") == "none"
          and C.gate_policy("nothing") is None)
check("class_style: the first live style of a class (studio_black, celestial_gold)", C.class_style("black") == "studio_black" and C.class_style("art") == "celestial_gold")
with patched(public=lambda s: [s[i].update(stage="retired") for i in LEGACY]):
    check("class_style with every legacy style retired falls back to the first open or planned one of the class",
          C.class_style("black") == "solo.clean" and C.class_style("art") in R.STYLES)
check("legacy_layouts_table is the old LAYOUTS table and iris reads it (the first layout is the default)",
      C.legacy_layouts_table() == OLD_LAYOUTS and L.LAYOUTS == OLD_LAYOUTS and all(L.layouts_for(n) == OLD_LAYOUTS[n] for n in range(1, 9))
      and L.layouts_for(9) == () and L.multi_layout(2) == "duo" and L.multi_layout(8) == "galaxy" and L.MULTI_MAX == 8 == C.MAX_EYES)
check("the layouts of every legacy style through catalogue.layouts_for are the old table", all(C.layouts_for(i, n) == OLD_LAYOUTS[n] for i in LEGACY for n in range(1, 9)))
check("the bare print is exactly studio_black (the registry gives it no accent colour)", L.BARE_STYLES == {"studio_black"})

# ============================================================================================ 3. legacy compatibility (I3)
section("3. legacy compatibility: the six ids render the same bytes, old specs and requests are read as before")


def synth_iris(side=384, seed=1, hue=0):
    """A deterministic masked iris square: radial colour, angular fibres, a black pupil, black outside the limbus."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:side, 0:side].astype(np.float32)
    cx = cy = (side - 1) / 2
    r = np.hypot(xx - cx, yy - cy) / (side / 2)
    th = np.arctan2(yy - cy, xx - cx)
    fib = 0.5 + 0.5 * np.sin(th * 37 + rng.random() * 6) * np.sin(th * 11 + r * 9)
    noise = rng.random((side, side)).astype(np.float32)
    base = np.stack([0.30 + 0.5 * np.cos(r * 3 + hue), 0.25 + 0.4 * np.cos(r * 4 + hue + 1), 0.15 + 0.5 * r * (1 - r) * 4], axis=-1)
    img = base * (0.55 + 0.45 * fib[..., None]) * (0.85 + 0.15 * noise[..., None])
    img[r > 0.92] = 0
    img[r < 0.22] = 0
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


def b64(im):
    b = io.BytesIO()
    im.save(b, "JPEG", quality=92)
    return base64.b64encode(b.getvalue()).decode()


def h(im):
    return hashlib.sha256(np.asarray(im.convert("RGB")).tobytes()).hexdigest()[:20]


GOLDENS = {   # recorded on the base commit 90695da (before the registry) with these pins; the work tree gave the same bytes
    "engine celestial_gold 1 single": "3feb2cecea8c4fba70d7", "engine celestial_gold 2 duo": "a7ef0c15b50c4794d7b9",
    "engine celestial_gold 2 fusion": "965db0e2b87923d9808c", "engine celestial_gold 3 row": "c427eec587f4f70fad30",
    "engine celestial_gold 3 triangle": "1837ceebaef2546cf8c7", "engine celestial_gold 4 grid": "4cedec54527d3d9e60c3",
    "engine celestial_gold 4 row": "9fdd34747be0f73a9ecd", "engine celestial_gold 5 galaxy": "63e7a29e4d99ad50cbf7",
    "engine celestial_gold 8 galaxy": "11a6bb5d8eea663d5113", "engine deep_nebula 1 single": "03909f5fcb4be899697f",
    "engine deep_nebula 2 wallpaper": "08fdef5258b8c876fb05", "engine emerald_aurora 1 single": "8b537ab979f646d6a29e",
    "engine obsidian_smoke 1 single": "63a54731fe4ba79ffaa6", "engine studio_black 1 single": "3c8cde68e1493aaf9f04",
    "engine studio_black 2 duo": "8d60f13b523b652dc766", "engine supernova 1 single": "6280a98356566c03edbc",
    "handler celestial_gold 4 row": "224e76a0a87581765466", "handler celestial_gold 4 row fields": "a3b11c33bd15eee2ea56",
    "handler studio_black 1 None": "97731f4a5210e05efce0", "handler studio_black 1 None fields": "fa6946ee5111c6929c9e",
    "handler supernova 2 fusion": "57b2cedc3279eebb461c", "handler supernova 2 fusion fields": "84091a94180d6ee0d499",
}
IR = [synth_iris(seed=s, hue=s) for s in range(1, 9)]
NEW_REPLY_FIELDS = ("tiles", "pick", "size", "opts", "design_used", "fallback", "plan8", "plan8_core", "engine", "selfcheck", "timing")      # the compose API v3's additive fields (WP10; plan8_core: the review of WP12, the plan8 without the pixel choices)
got = {}
replies = {}
with contextlib.redirect_stdout(io.StringIO()):
    for style in L.STYLES:
        got[f"engine {style} 1 single"] = h(L.compose_multi(IR[:1], style=style, names="Anna", size=256))
    for n, layout in ((2, "duo"), (2, "fusion"), (3, "triangle"), (3, "row"), (4, "grid"), (4, "row"), (5, "galaxy"), (8, "galaxy")):
        got[f"engine celestial_gold {n} {layout}"] = h(L.compose_multi(IR[:n], style="celestial_gold", names="A & B", size=256, layout=layout))
    got["engine studio_black 2 duo"] = h(L.compose_multi(IR[:2], style="studio_black", size=256, layout="duo"))
    got["engine deep_nebula 2 wallpaper"] = h(L.compose_multi(IR[:2], style="deep_nebula", size=256, layout="fusion", fmt="wallpaper"))
    for style, n, layout in (("studio_black", 1, None), ("supernova", 2, "fusion"), ("celestial_gold", 4, "row")):
        body = {"irises": [b64(x) for x in IR[:n]], "style": style, "names": "Anna", "pad": 1.12}
        if layout:
            body["layout"] = layout
        rep = COMPOSE.compose(body)
        replies[(style, n)] = rep
        img = Image.open(io.BytesIO(base64.b64decode(rep["image"]))).convert("RGB")
        got[f"handler {style} {n} {layout}"] = h(img)
        got[f"handler {style} {n} {layout} fields"] = hashlib.sha256(
            json.dumps({k: v for k, v in rep.items() if k not in ("image", "qa", "eyes", *NEW_REPLY_FIELDS)}, sort_keys=True).encode()).hexdigest()[:20]   # "eyes": added by WP3, the NEW_REPLY_FIELDS by WP10 (compose API v3): additive (v3gate and v3compose check them); the old fields stay byte for byte
diff = {k: (got.get(k), v) for k, v in GOLDENS.items() if got.get(k) != v}
check("the six legacy ids render the same pixels as before the registry (22 results of the engine and of the compose handler)", not diff, diff)
rep = replies[("celestial_gold", 4)]
check("compose reply: styles is the six legacy ids in the old order, layouts the old table for the eye count, the layout as chosen",
      rep["styles"] == LEGACY and rep["layouts"] == ["grid", "row"] and rep["layout"] == "row" and replies[("studio_black", 1)]["layouts"] == ["single"]
      and replies[("supernova", 2)]["layout"] == "fusion" and rep["style"] == "celestial_gold" and rep["count"] == 4)
def _refusal(body):
    try:
        COMPOSE.compose(body)
    except Exception as e:  # noqa
        return e
    return None


with contextlib.redirect_stdout(io.StringIO()):
    e_bad = _refusal({"irises": [b64(IR[0])], "style": "solo.powder", "pad": 1.12})
    r_none = COMPOSE.compose({"irises": [b64(IR[0])], "pad": 1.12})
    e_lay = _refusal({"irises": [b64(IR[0]), b64(IR[1])], "style": "supernova", "layout": "grid", "pad": 1.12})
    e_unk = _refusal({"irises": [b64(IR[0])], "style": "nope", "pad": 1.12})
# WP10 (compose API v3): the old check said that a style that is not previewable falls back to the default style and an unknown layout to the first. The
# specification's contract says 422 style_unavailable for a style a customer may not have (a laboratory id), 400 for an id that is not the registry's and
# 400 for a layout the style does not take; a request with no style at all still gets the default style.
check("compose with a style a customer may not have (a laboratory id) is 422 style_unavailable, an unknown id and a layout the style does not take are 400, no style is the default style",
      getattr(e_bad, "status", None) == 422 and e_bad.body["reason"] == "style_unavailable" and e_bad.body["why"] == "stage"
      and isinstance(e_lay, L.ClientError) and isinstance(e_unk, L.ClientError) and r_none["style"] == "celestial_gold")
check("pay.item_name of the six legacy ids in English and German is the old sentence",
      all(pay.item_name({"eyes": n, "style": i, "lang": lg, "market": "eu"}) == exp
          for i in LEGACY for n in (1, 3) for lg, exp in (
              ("en", f"SnapEyes iris artwork, {n} {'eye' if n == 1 else 'eyes'}, {OLD_NAMES[i]}, 4096 px digital file"),
              ("de", f"SnapEyes-Iris-Kunstwerk, {n} {'Auge' if n == 1 else 'Augen'}, {OLD_NAMES[i]}, digitale Datei 4096 px"))))
check("the Lithuanian and Hungarian sentences carry the same brand name",
      all(OLD_NAMES[i] in pay.item_name({"eyes": 2, "style": i, "lang": lg, "market": "eu" if lg == "lt" else "hu"}) for i in LEGACY for lg in ("lt", "hu")))
SPEC = {"eyes": "2", "style": "supernova", "layout": "fusion", "names": "Anna;Max", "title": "T", "lang": "en", "market": "eu"}


class _Reply:
    status_code = 200

    def json(self):
        return {"id": "cs_test_" + "a" * 20, "url": "https://checkout.stripe.com/c/pay/x"}


def stripe_form_hash():
    """SHA-256 of the Stripe Checkout Session parameters pay.create_session builds for every legacy style x market x language x 1, 2, 3, 8 eyes."""
    captured, real = [], pay._stripe
    pay._stripe = lambda method, path, params=None, idem=None, timeout=None: (captured.append(sorted((k, v) for k, v in params)), _Reply())[1]
    out = {}
    lay = {1: "single", 2: "fusion", 3: "triangle", 8: "galaxy"}
    try:
        for market in pay.MARKETS:
            for lang in ("en", "de", "lt", "hu"):
                for style in LEGACY:
                    for n in (1, 2, 3, 8):
                        spec = {"eyes": n, "style": style, "layout": lay[n], "names": "Anna", "title": "T", "lang": pay.lang_for(market, lang), "market": market}
                        pay.create_session("260101-abcd", "k" * 40, spec, pay.price_cents(n, style, market), {"version": "2026-09-30.2", "at": "2026-01-01T00:00:00Z"}, 1900000000)
                        out[f"{market} {lang} {style} {n}"] = captured[-1]
    finally:
        pay._stripe = real
    return len(out), hashlib.sha256(json.dumps(out, sort_keys=True).encode("utf-8")).hexdigest()[:24]


check("the Stripe Checkout Session parameters of the six legacy ids (item name, amount, metadata: 384 combinations) are byte equal to those of 90695da",
      stripe_form_hash() == (384, "9d3e048ab360e89bac51819b"), stripe_form_hash())
ok_specs = [pay.spec_from(dict(SPEC, eyes=str(n), style=i, layout=OLD_LAYOUTS[n][-1]), pay.SELECTABLE) for i in LEGACY for n in range(1, 9)]
check("spec_from: every legacy id, 1 to 8 eyes and each layout is read at checkout exactly as before",
      len(ok_specs) == 48 and all(s["layout"] == OLD_LAYOUTS[s["eyes"]][-1] and s["style"] in LEGACY for s in ok_specs)
      and pay.spec_from(dict(SPEC, layout=""), pay.SELECTABLE)["layout"] == "duo" and pay.spec_from(dict(SPEC, layout=None), pay.SELECTABLE)["layout"] == "duo")


def refused(fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        return type(e).__name__ + ": " + str(e)
    return None


def caught(fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        return e
    return None


# WP12 (spec 2.9): a style the registry knows but that cannot be ordered is a 409 style_unavailable (why stage), not the old 400 that named the six ids; an id the
# registry does not know is still that 400 (the next check)
a409 = caught(lambda: pay.spec_from(dict(SPEC, style="duo.kiss_collision"), pay.SELECTABLE))   # a TWO-eye style (solo.powder with two eyes is why eyes)
check("a v3 id that is not live is refused at checkout as 409 style_unavailable (why stage), the body naming the style and the eye count",
      type(a409).__name__ == "Answer" and a409.status == 409 and a409.body["reason"] == "style_unavailable" and a409.body["why"] == "stage"
      and a409.body["style"] == "duo.kiss_collision" and a409.body["eyes"] == 2, a409)
msg = refused(lambda: pay.spec_from(dict(SPEC, style="nothing"), pay.SELECTABLE))
check("an id the registry does not know is the old 400, with the sentence naming the six ids", msg == "ClientError: Choose one of the styles: " + ", ".join(LEGACY) + ".", msg)
check("an unknown style, one that is not text, and a wrong layout are refused as before",
      all(refused(lambda s=s: pay.spec_from(dict(SPEC, style=s), pay.SELECTABLE)) for s in ("nothing", None, 3, ["supernova"], {}))
      and refused(lambda: pay.spec_from(dict(SPEC, layout="grid"), pay.SELECTABLE)) == "ClientError: 2 eyes can use: duo, fusion.")
with patched(override=lambda i, n: "lab" if i == "supernova" else None):
    check("spec_from refuses a legacy id at checkout only when its stage is not live, and still reads it for a paid order",
          refused(lambda: pay.spec_from(SPEC, pay.SELECTABLE)) is not None and pay.spec_from(SPEC)["style"] == "supernova"
          and pay.spec_from(dict(SPEC, style="deep_nebula"), pay.SELECTABLE)["style"] == "deep_nebula")
with patched(public=lambda s: s["supernova"].update(stage="retired")):
    check("a retired id is read from a paid session and refused for a new checkout",
          pay.spec_from(SPEC)["style"] == "supernova" and refused(lambda: pay.spec_from(SPEC, pay.SELECTABLE)) is not None)
check("a paid order is read for any style of the registry that takes its eye count and for no other",
      pay.spec_from(dict(SPEC, style="solo.powder", eyes="1", layout="single"))["style"] == "solo.powder"
      and refused(lambda: pay.spec_from(dict(SPEC, style="nothing"))) is not None
      and refused(lambda: pay.spec_from(dict(SPEC, style="solo.powder", eyes="2"))) is not None)


def built_for(n):
    """The v3 styles whose engine family is in the repository and that take n eyes (WP5A: the singles for one eye; WP7A: the collision family for two to
    eight eyes; a family that lands later joins by itself)."""
    return {i for i in C.ids() if C.ENGINE[i]["engine"] and C.ENGINE[i]["engine"]["module"] != "legacy" and C.engine_built(C.ENGINE[i]["engine"]["module"]) and C.in_range(i, n)}


check("the catalogue says what can be drawn: the six legacy ids for every eye count, and the styles of a v3 family that is in the repository for the eye counts "
      "they take (the singles for one eye, the collision family for two to eight; a paid order's artwork of such a style is made by the master plan's step runner, "
      "WP6a, test_steps.py)",
      all(set(C.renderable_ids(n)) == set(LEGACY) | built_for(n) and [i for i in C.renderable_ids(n) if C.is_legacy(i)] == LEGACY
          for n in range(1, 9)) and C.renderable_ids(9) == ())

# ============================================================================================ 4. price parity (I2)
section("4. price parity: five rules, every id, 1 to 8 eyes, 4 markets, every experiment ladder")
os.makedirs(TMP, exist_ok=True)
PROBE = os.path.join(TMP, "wp1_probe.mjs")
with open(PROBE, "w", encoding="utf-8", newline="\n") as f:
    f.write(r"""
import { createRequire } from 'node:module'; import { join } from 'node:path'; import { pathToFileURL } from 'node:url'; import { readFileSync } from 'node:fs';
const repo = process.argv[2];
const req = createRequire(join(repo, 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root: repo })).module;
const M = await load('./src/shared/markets.ts');
const S = await load('./src/shared/styles.ts');
const P = await import(pathToFileURL(join(repo, 'scripts', 'check_prices.mjs')).href);
const E = await import(pathToFileURL(join(repo, 'scripts', 'check_experiments.mjs')).href);
const reg = (await import(pathToFileURL(join(repo, 'scripts', 'styles_source.mjs')).href)).loadRegistry(repo).styles;
const mk = P.parseMarketsSource(readFileSync(join(repo, 'api/_lib/markets.py'), 'utf8')).markets;
const ex = E.parseExperimentsSource(readFileSync(join(repo, 'api/_lib/experiments.py'), 'utf8')).experiments;
const out = { table: [], ladders: [], styles: {} };
for (const id of Object.keys(reg)) {
  for (const m of Object.keys(mk)) for (let n = 1; n <= 8; n++) out.table.push([id, m, n, M.priceMinor(n, id, m), P.priceRule(mk, m, n, reg[id].price_class), E.ladderRule(mk[m].prices, n, reg[id].price_class)]);
  for (const [key, e] of Object.entries(ex)) for (const [name, v] of Object.entries(e.variants)) for (const [m, l] of Object.entries(v.prices)) for (let n = 1; n <= 8; n++)
    out.ladders.push([id, key, name, m, n, M.priceMinor(n, id, m, l), E.ladderRule(l, n, reg[id].price_class)]);
}
for (const id of Object.keys(reg)) {
  out.styles[id] = { ceil: [0,1,2,3,4,5,6,7,8,9].map((n) => S.ceilingStage(id, n)), layouts: [1,2,3,4,5,6,7,8,9].map((n) => [...S.layoutsFor(id, n)]), cls: S.priceClass(id), black: S.isBlack(id), name: S.styleName(id) };
}
out.styles['nothing'] = { cls: S.priceClass('nothing'), black: S.isBlack('nothing'), name: S.styleName('nothing') };
out.misc = { classBlack: S.classStyle('black'), classArt: S.classStyle('art'), def: S.DEFAULT_STYLE, legacy: [...S.LEGACY_IDS], picker: S.legacyStyles(), landing: S.landingStyles(), names: S.STYLE_NAMES, schema: S.STYLES_SCHEMA, pv: S.PLATES_VERSION };
console.log(JSON.stringify(out));
""")
rc, so, se = run_node([PROBE, REPO])
probe = last_json(so)
check("the node probe loads the site's price rule, the two restatements and styles.ts", probe is not None, (rc, se[-600:], so[-300:]))


def expected(sid, eyes, prices):
    if eyes <= 1:
        return prices["one_eye_studio_black"] if R.STYLES[sid]["price_class"] == "black" else prices["one_eye_art"]
    return prices["two_eyes"] + (eyes - 2) * prices["each_further_eye"]


bad = []
n_checked = 0
for sid in R.STYLES:
    for m in MK.MARKETS:
        for eyes in range(1, 9):
            pr = MK.MARKETS[m]["prices"]
            want = expected(sid, eyes, pr)
            n_checked += 1
            if not (pay.price_cents(eyes, sid, m) == abtest.ladder_price(pr, eyes, sid) == want):
                bad.append((sid, m, eyes, pay.price_cents(eyes, sid, m), abtest.ladder_price(pr, eyes, sid), want))
check("pay.price_cents and abtest.ladder_price equal the rule for every id (28) x 4 markets x 1 to 8 eyes", not bad and n_checked == 28 * 4 * 8, bad[:3])
lad = []
for key, e in XP.EXPERIMENTS.items():
    for name, v in e["variants"].items():
        for m, l in v["prices"].items():
            for sid in R.STYLES:
                for eyes in range(1, 9):
                    if abtest.ladder_price(l, eyes, sid) != expected(sid, eyes, l):
                        lad.append((key, name, m, sid, eyes))
check("abtest.ladder_price equals the rule on every ladder of every price experiment", not lad and XP.EXPERIMENTS, lad[:3])
if probe:
    tbad = [r for r in probe["table"] if not (r[3] == r[4] == r[5] == expected(r[0], r[2], MK.MARKETS[r[1]]["prices"]) == pay.price_cents(r[2], r[0], r[1]))]
    check("the site's priceMinor, check_prices priceRule and check_experiments ladderRule give the server's price for every id x market x 1 to 8 eyes",
          not tbad and len(probe["table"]) == 896, tbad[:3])
    lbad = [r for r in probe["ladders"] if not (r[5] == r[6] == expected(r[0], r[4], XP.EXPERIMENTS[r[1]]["variants"][r[2]]["prices"][r[3]]))]
    check("the same on every experiment ladder (priceMinor fed the ladder, as the server's answer feeds it)", not lbad and probe["ladders"], lbad[:3])
    sbad = []
    for sid in R.STYLES:
        ts = probe["styles"][sid]
        if (ts["ceil"] != [C.ceiling(sid, n) for n in range(0, 10)] or ts["layouts"] != [list(C.layouts_for(sid, n)) for n in range(1, 10)]
                or ts["cls"] != C.price_class(sid) or ts["black"] != C.is_black(sid) or ts["name"] != C.name_of(sid)):
            sbad.append(sid)
    check("src/shared/styles.ts reads the registry as catalogue.py does: ceiling per eye count, layouts, price class, name, for every id",
          not sbad and probe["styles"]["nothing"] == {"cls": "art", "black": False, "name": "nothing"}, sbad[:3])
    ms = probe["misc"]
    check("styles.ts: classStyle, DEFAULT_STYLE, the legacy list in engine order, the landing order by tile_order, the accents, schema and plates version",
          ms["classBlack"] == C.class_style("black") and ms["classArt"] == C.class_style("art") and ms["def"] == C.DEFAULT_STYLE
          and ms["legacy"] == LEGACY and [s["id"] for s in ms["landing"]] == ["studio_black", "celestial_gold", "deep_nebula", "emerald_aurora", "obsidian_smoke", "supernova"]
          and [s["id"] for s in ms["picker"]] == LEGACY and ms["picker"][0]["accent"] == [245, 197, 66] and ms["picker"][-1]["accent"] is None
          and all(s["accent"] == list(L.STYLES[s["id"]]["accent"]) for s in ms["picker"][:-1])
          and ms["schema"] == R.STYLES_SCHEMA and ms["pv"] == R.PLATES_VERSION and ms["names"] == C.names(), ms["picker"][:1])

# ============================================================================================ 5. the build check
section("5. scripts/check_styles.mjs: the repository passes, and each refusal is exact")
rc, so, se = run_node(["scripts/check_styles.mjs"])
check("npm run check:styles passes on the repository and prints the registry hash (item 11)", rc == 0 and "styles registry ok: 28 ids" in so, (rc, so, se[-500:]))
mh = re.search(r"registry hash ([0-9a-f]{12})", so)
check("the hash the build prints is the hash the server computes (node and Python make the same canonical text)",
      bool(mh) and mh.group(1) == C.registry_hash(), (mh and mh.group(1), C.registry_hash()))
rc, so, se = run_node(["scripts/check_prices.mjs"])
check("the price check passes on the repository (the registry's price classes feed it)", rc == 0 and "price check ok" in so, (so, se[-400:]))
rc, so, se = run_node(["scripts/check_texts.mjs"])
check("the text check passes on the repository (the brand names are in ENGLISH_OK)", rc == 0 and "text check ok" in so, (so, se[-400:]))

BASE = os.path.join(TMP, "base")
PROBLEMS = {}


def copy_repo(dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    for d, ign in (("api", ("__pycache__", "_assets")), ("src", ("assets", "__pycache__")), ("scripts", ("__pycache__", "styles_tests"))):
        shutil.copytree(os.path.join(REPO, d), os.path.join(dst, d), ignore=shutil.ignore_patterns(*ign))
    shutil.copy(os.path.join(REPO, "package.json"), os.path.join(dst, "package.json"))
    shutil.copy(os.path.join(REPO, "index.html"), os.path.join(dst, "index.html"))   # WP12: the text check lints the head of index.html


def sub(case, root, rel, old, new):
    """Replace old by new once in a copy's file; a premise that is not found exactly once fails the case for that reason."""
    path = os.path.join(root, *rel.split("/"))
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")
    if text.count(old) != 1:
        PROBLEMS.setdefault(case, []).append((rel, text.count(old), old[:80]))
        return
    text = text.replace(old, new)
    if crlf:
        text = text.replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def append(root, rel, text):
    with open(os.path.join(root, *rel.split("/")), "a", encoding="utf-8", newline="") as f:
        f.write(text)


def put(root, rel, text):
    os.makedirs(os.path.dirname(os.path.join(root, *rel.split("/"))), exist_ok=True)
    with open(os.path.join(root, *rel.split("/")), "w", encoding="utf-8", newline="") as f:
        f.write(text)


def mutate_literal(root, rel, name, fn):
    path = os.path.join(root, *rel.split("/"))
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    at = text.index(f"\n{name} = {{") + 1
    data = json.loads(text[at + len(name) + 3:])
    fn(data)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text[:at] + f"{name} = " + json.dumps(data, indent=1) + "\n")


def pub(fn):
    return lambda case, root: mutate_literal(root, "api/_lib/styles_registry.py", "STYLES", fn)


def eng(fn):
    return lambda case, root: mutate_literal(root, "api/_lib/styles_engine.py", "ENGINE", fn)


def names(fn):
    return lambda case, root: mutate_literal(root, "api/_lib/layout_names.py", "LAYOUT_NAMES", fn)


def reorder(s):
    first = s.pop("celestial_gold")
    s["celestial_gold"] = first      # moved behind the other legacy ids: the order of the legacy block changes


NEG_BATCH = [   # label, mutation(case, root), a sentence the check must say
    ("an unknown field in an entry", pub(lambda s: s["solo.powder"].update(colour="red")), 'style "solo.powder": its fields must be exactly'),
    ("a missing field in an entry", pub(lambda s: s["solo.powder"].pop("gate")), "missing gate"),
    ("eyes outside 1 to 8", pub(lambda s: s["solo.powder"].update(eyes=[0, 1])), "eyes must be [min, max] inside 1 to 8"),
    ("eyes up to 9", pub(lambda s: s["solo.powder"].update(eyes=[1, 9])), "eyes must be [min, max] inside 1 to 8"),
    ("a layouts key outside the eyes", pub(lambda s: s["solo.powder"]["layouts"].update({"3": ["trio"]})), 'layouts key "3" is not an eye count inside 1 to 1'),
    ("layouts that do not cover the eyes", pub(lambda s: s["solo.powder"]["layouts"].pop("1")), "layouts has nothing for 1 eyes"),
    ("a layout id outside the vocabulary", pub(lambda s: s["solo.powder"]["layouts"].update({"1": ["spiral"]})), 'layouts["1"] must be a list of distinct layout ids'),
    ("a stage that is not one of the five", pub(lambda s: s["solo.powder"].update(stage="ready")), "stage must be one of planned, lab, preview, live, retired"),
    ("stage_by_eyes outside the eyes", pub(lambda s: s["solo.powder"].update(stage_by_eyes={"2": "live"})), 'the range "2" is not inside the eyes 1 to 1'),
    ("stage_by_eyes ranges that overlap", pub(lambda s: s["grp.collision"].update(stage_by_eyes={"3-5": "lab", "5-8": "lab"})), "overlaps another range"),
    ("a planned style that has an engine", pub(lambda s: s["solo.powder"].update(stage="planned")), 'style "solo.powder": a planned style has no engine'),
    ("a live style without an engine", eng(lambda e: e["supernova"].update(engine={})), "a style at stage live needs an engine"),
    ("a look above its style", eng(lambda e: e["solo.universe"]["engine"]["looks"].update(echo="live")), 'the look "echo" is at stage live, above its style'),
    ("the legacy module on a v3 style", eng(lambda e: e["solo.powder"]["engine"].update(module="legacy")), "the module legacy belongs to the legacy styles"),
    ("null in the literal (not Python)", pub(lambda s: s["solo.powder"].update(name=None)), "null, true and false are not Python"),
    ("true in the literal (not Python)", pub(lambda s: s["solo.powder"].update(legacy=True)), "null, true and false are not Python"),
    ("a float in the literal", pub(lambda s: s["solo.powder"]["work_side"].update({"1": 2048.5})), "whole numbers only"),
    ("a name that is not ASCII", pub(lambda s: s["solo.powder"].update(name="Powder é")), "ASCII only"),
    ("two ids with one slug", pub(lambda s: s["solo.powder"].update(slug=s["solo.splash"]["slug"])), "is also the slug of"),
    ("a heart in a name", pub(lambda s: s["solo.powder"].update(name="Powder Heart")), 'holds the word "heart"'),
    ("a heart in a slug", pub(lambda s: s["solo.powder"].update(slug="love-powder")), 'holds the word "love"'),
    ("a pet symbol in a slug", pub(lambda s: s["solo.powder"].update(slug="dog-powder")), 'holds the pet symbol word "dog"'),
    ("gate none on a v3 style", pub(lambda s: s["solo.powder"].update(gate="none")), "gate none belongs to the legacy styles only"),
    ("an unknown gate", pub(lambda s: s["solo.powder"].update(gate="soft")), "gate must be one of none, advisory, hard"),
    ("a bad price class", pub(lambda s: s["solo.powder"].update(price_class="gold")), "price_class must be black or art"),
    ("work_side that leaves an eye count out", pub(lambda s: s["grp.collision"].update(work_side={"3": 4096})), "work_side must cover every eye count"),
    ("a work_side of 8192", pub(lambda s: s["solo.powder"].update(work_side={"1": 8192})), "must be a size from 512 to 4096"),
    ("a work_side for the legacy engine", pub(lambda s: s["celestial_gold"].update(work_side={"1": 2048})), "the legacy engine has its own limits"),
    ("two tiles with one tile_order", pub(lambda s: s["solo.splash"].update(tile_order=s["solo.powder"]["tile_order"])), "tile_order 1 is also"),
    ("a reason without its class", pub(lambda s: s["solo.powder"].update(reason={})), "reason must have a key for exactly the classes of pick"),
    ("an accent on a v3 style", pub(lambda s: s["solo.powder"].update(accent=[1, 2, 3])), "accent is for the legacy styles only"),
    ("legacy styles with different layouts",
     pub(lambda s: s["supernova"].update(layouts={"1": ["single"], "2": ["duo"], "3": ["row"], "4": ["row"], "5": ["galaxy"], "6": ["galaxy"], "7": ["galaxy"], "8": ["galaxy"]})),
     "the legacy styles must share one layout table"),
    ("an engine entry for an id the registry does not have", eng(lambda e: e.update({"solo.ghost": copy.deepcopy(e["solo.powder"])})),
     'an entry for "solo.ghost", which api/_lib/styles_registry.py does not have'),
    ("a style without an engine entry", eng(lambda e: e.pop("duo.gold")), 'no entry for the style "duo.gold"'),
    ("a fill_side of 4096", eng(lambda e: e["solo.universe"].update(fill_side=4096)), "fill_side must be 0 or a size up to 1536"),
    ("an unknown rule set", eng(lambda e: e["solo.powder"].update(gate_rules="eyelid")), "gate_rules must be one of lid, fill"),
    ("an unknown DEFAULT_STYLE", lambda c, r: sub(c, r, "api/_lib/styles_registry.py", 'DEFAULT_STYLE = "celestial_gold"', 'DEFAULT_STYLE = "solo.ghost"'),
     'DEFAULT_STYLE "solo.ghost" is not a style of the registry'),
    ("a v3 id that is not group.name", lambda c, r: sub(c, r, "api/_lib/styles_registry.py", '"solo.powder": {', '"powder": {'), 'style "powder": a v3 id is "'),
    ("a literal that is not JSON any more", lambda c, r: sub(c, r, "api/_lib/styles_registry.py", '"slug": "powder-burst",', '"slug": "powder-burst"'), "cannot be read as JSON"),
    ("a style id written in a Python file of api/", lambda c, r: append(r, "api/_lib/pay.py", '\nLEAK = "studio_black"\n'),
     'api/_lib/pay.py: writes the style id "studio_black" itself'),
    ("a v3 id written in a TypeScript file of src/", lambda c, r: append(r, "src/try/multi.ts", "\nexport const LEAK = 'solo.powder';\n"),
     'src/try/multi.ts: writes the style id "solo.powder" itself'),
    ("a style id written in a script", lambda c, r: put(r, "scripts/leak.mjs", "export const LEAK = 'deep_nebula';\n"), 'scripts/leak.mjs: writes the style id "deep_nebula" itself'),
    ("the engine table of iris.py in another order than the registry",
     lambda c, r: sub(c, r, "api/_lib/iris.py", '    "celestial_gold": {"bg": "bg_celestial_gold.jpg", "accent": (245, 197, 66), "title": "THE UNIVERSE WITHIN"},\n    "deep_nebula": {"bg": "bg_deep_nebula.jpg", "accent": (129, 140, 248), "title": "DEEP NEBULA"},',
                      '    "deep_nebula": {"bg": "bg_deep_nebula.jpg", "accent": (129, 140, 248), "title": "DEEP NEBULA"},\n    "celestial_gold": {"bg": "bg_celestial_gold.jpg", "accent": (245, 197, 66), "title": "THE UNIVERSE WITHIN"},'),
     "api/_lib/iris.py STYLES has the ids deep_nebula, celestial_gold"),
    ("the registry's legacy block in another order than iris.py", pub(reorder), "api/_lib/iris.py STYLES has the ids celestial_gold, deep_nebula"),
    ("an accent in iris.py that the registry does not have", lambda c, r: sub(c, r, "api/_lib/iris.py", '"accent": (245, 197, 66)', '"accent": (245, 197, 67)'),
     'api/_lib/iris.py STYLES "celestial_gold" accent is [245,197,67]'),
    ("a terms row of the black class that no longer names its style",
     lambda c, r: sub(c, r, "src/legal/docs/terms.ts", "['One eye, Clean Iris', eur(PRICE_CENTS.studioBlack, 'en')]", "['One eye, Pure Black', eur(PRICE_CENTS.studioBlack, 'en')]"),
     'the row "One eye, Pure Black" prices the black class, whose one member is "Clean Iris"'),
    ("a Lithuanian terms row that no longer names it",
     lambda c, r: sub(c, r, "src/legal/docs/terms.lt.ts", "['Viena akis, Clean Iris', eurLt(PRICE_CENTS.studioBlack)]", "['Viena akis, Juodas', eurLt(PRICE_CENTS.studioBlack)]"),
     'terms.lt.ts: the row "Viena akis, Juodas"'),
    # WP12: the terms name the black class's one v3 member (the legacy Studio Black retires at the cutover and is not named): a second v3 style of the class
    ("a second style in the black price class", pub(lambda s: s["solo.powder"].update(price_class="black")),
     "the black price class has 2 styles that are not legacy or planned (solo.clean, solo.powder)"),
    # work package 2: the words for the layouts
    ("a layout word missing in one language", names(lambda n: n["single"].pop("hu")), 'layout "single": it must have a word in exactly en, de, lt, hu'),
    ("a layout word in a fifth language", names(lambda n: n["single"].update(fr="Seul")), 'layout "single": it must have a word in exactly en, de, lt, hu'),
    ("an empty layout word", names(lambda n: n["duo"].update(lt="")), 'layout "duo": the lt word must be a short text'),
    ("a layout word with a space at its end", names(lambda n: n["duo"].update(de="Nebeneinander ")), 'layout "duo": the de word must be a short text'),
    ("a layout id that is not lower case", names(lambda n: n.update(Spiral=n["duo"])), 'layout "Spiral": a layout id is lower case letters'),
    ("a layout a style takes that has no words", names(lambda n: n.pop("pair")), 'layouts["2"] must be a list of distinct layout ids'),
    ("words for a layout no style takes", names(lambda n: n.update(spiral={"en": "Spiral", "de": "Spirale", "lt": "Spirale", "hu": "Spir\u00e1l"})),
     'has words for the layout "spiral", which no style of api/_lib/styles_registry.py takes'),
    ("a LAYOUT_NAMES literal that is not JSON any more", lambda c, r: sub(c, r, "api/_lib/layout_names.py", '"hu": "Galaxis"}\n}', '"hu": "Galaxis"},\n}'),
     "the LAYOUT_NAMES literal cannot be read as JSON"),
    ("a second layout table in a Python file", lambda c, r: append(r, "api/_lib/pay.py", '\nWORDS = {"single": "Single", "duo": "Side by side"}\n'),
     "api/_lib/pay.py: a table that names layouts again"),
    ("a second layout table in an order page dictionary", lambda c, r: append(r, "src/order/copy.ts", "\nexport const LAYOUTS_AGAIN = { single: 'Single', galaxy: 'Galaxy' };\n"),
     "src/order/copy.ts: a table that names layouts again"),
    ("a second layout table in a picker dictionary, in Lithuanian",
     lambda c, r: sub(c, r, "src/try/copy.lt.ts", "    retry: 'Bandyti dar kartą',\n", "    retry: 'Bandyti dar kartą',\n    layouts: { single: 'Viena akis', duo: 'Greta' },\n"),
     "src/try/copy.lt.ts: a table that names layouts again"),
]
roots = []
for i, (label, fn, needle) in enumerate(NEG_BATCH):
    root = os.path.join(TMP, f"case_{i:02d}")
    copy_repo(root)
    fn(label, root)
    roots.append(root)
control = os.path.join(TMP, "case_control")        # a price key and an asset name are not style ids
copy_repo(control)
put(control, "api/_lib/zz_probe.py", 'KEYS = ("one_eye_studio_black", "one_eye_art")\nF = "bg_studio_black.jpg"\n')
control2 = os.path.join(TMP, "case_control2")       # layout ids as keys with lower case values (a caption mode, a family) are not words
copy_repo(control2)
put(control2, "api/_lib/zz_probe2.py", 'CAPTION = {"single": "full", "duo": "full", "row": "names", "grid": "names"}\n')
untouched = os.path.join(TMP, "case_untouched")
copy_repo(untouched)
BATCH = os.path.join(TMP, "wp1_batch.mjs")
with open(BATCH, "w", encoding="utf-8", newline="\n") as f:
    f.write(r"""
import { join } from 'node:path'; import { pathToFileURL } from 'node:url';
const repo = process.argv[2];
const { checkStyles } = await import(pathToFileURL(join(repo, 'scripts', 'check_styles.mjs')).href);
const out = {};
for (const root of process.argv.slice(3)) { try { out[root] = await checkStyles(root); } catch (e) { out[root] = ['THROWN: ' + e.message]; } }
console.log(JSON.stringify(out));
""")
rc, so, se = run_node([BATCH, REPO] + roots + [control, control2, untouched])
batch = last_json(so)
check("the batch runner ran every copy of the repository", batch is not None and len(batch) == len(roots) + 3, (rc, se[-500:], so[-300:]))
if batch:
    check("a copy of the repository with nothing changed passes", batch[untouched] == [], batch[untouched])
    check("a price key (one_eye_studio_black) and a file name (bg_studio_black.jpg) are not style ids: the word boundary counts _ as a letter", batch[control] == [], batch[control])
    check("layout ids as keys with lower case values (a caption mode per family) are not a table of layout words", batch[control2] == [], batch[control2])
    for (label, fn, needle), root in zip(NEG_BATCH, roots):
        probs = batch[root]
        check(f"check_styles refuses: {label}", not PROBLEMS.get(label) and any(needle in p for p in probs), (PROBLEMS.get(label), needle, probs[:3]))

# --- the refusals that need the page code (styles.ts, markets.ts, the copy dictionaries): the check with Vite's module runner
LOADRUN = os.path.join(TMP, "wp1_loadcheck.mjs")
with open(LOADRUN, "w", encoding="utf-8", newline="\n") as f:
    f.write(r"""
import { createRequire } from 'node:module'; import { join } from 'node:path'; import { pathToFileURL } from 'node:url';
const [repo, root] = process.argv.slice(2);
const req = createRequire(join(repo, 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const { checkStyles } = await import(pathToFileURL(join(repo, 'scripts', 'check_styles.mjs')).href);
const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root })).module;
console.log(JSON.stringify(await checkStyles(root, load)));
""")


def with_load(label, mutate):
    root = os.path.join(TMP, "load_" + re.sub(r"[^a-z0-9]+", "_", label.lower())[:40])
    copy_repo(root)
    mutate(label, root)
    rc2, so2, se2 = run_node([LOADRUN, REPO, root])
    probs = last_json(so2)
    return probs if probs is not None else [f"NO OUTPUT rc={rc2} {se2[-300:]}"]


probs0 = with_load("untouched", lambda c, r: None)
check("with the page code loaded (styles.ts, markets.ts, the copy dictionaries) an untouched copy passes", probs0 == [], probs0[:4])
LT_LINE = "      supernova: 'Žvaigždžių dulkės raudonais ir oranžiniais tonais.',\n"
for label, mutate, needle in [
    ("a copy dictionary keyed by style id with an id that is not shown",
     lambda c, r: sub(c, r, "src/landing/copy.ts", "    desc: {\n      studio_black: 'Your iris alone, on pure black.',", "    desc: {\n      'solo.powder': 'x',\n      studio_black: 'Your iris alone, on pure black.',"),
     "landing.en.styles.desc is a dictionary keyed by style id with"),
    ("a copy dictionary that lacks a shown id in Lithuanian", lambda c, r: sub(c, r, "src/landing/copy.lt.ts", LT_LINE, ""),
     "landing.lt.styles.desc is a dictionary keyed by style id with"),
    ("layouts.ts that reads another LAYOUT_NAMES than the file holds",
     lambda c, r: sub(c, r, "src/shared/layouts.ts", "return JSON.parse(src.slice(at + 'LAYOUT_NAMES = '.length)) as Record<string, LayoutWords>;",
                      "return Object.fromEntries(Object.entries(JSON.parse(src.slice(at + 'LAYOUT_NAMES = '.length))).slice(1)) as Record<string, LayoutWords>;"),
     "src/shared/layouts.ts reads another LAYOUT_NAMES than api/_lib/layout_names.py holds"),
    ("styles.ts that reads another STYLES than the file holds",
     lambda c, r: sub(c, r, "src/shared/styles.ts", "styles: JSON.parse(src.slice(at + 'STYLES = '.length)) as Record<string, StyleDef>,",
                      "styles: Object.fromEntries(Object.entries(JSON.parse(src.slice(at + 'STYLES = '.length))).slice(1)) as Record<string, StyleDef>,"),
     "src/shared/styles.ts reads another STYLES than api/_lib/styles_registry.py holds"),
    ("a site price rule that does not use the price class",
     lambda c, r: sub(c, r, "src/shared/markets.ts", "isBlack(style) ? p.one_eye_studio_black : p.one_eye_art", "style === 'x' ? p.one_eye_studio_black : p.one_eye_art"),
     "priceMinor(1, studio_black, eu) = "),
]:
    probs = with_load(label, mutate)
    check(f"check_styles refuses: {label}", not PROBLEMS.get(label) and any(needle in p for p in probs), (PROBLEMS.get(label), needle, probs[:3]))

# --- the rules of items 4 and 7 that work package 12's texts meet: built, tested on synthetic files, and enforced on the real tree (WP12_RULES)
RULES = os.path.join(TMP, "wp1_rules.mjs")
with open(RULES, "w", encoding="utf-8", newline="\n") as f:
    f.write(r"""
import { join } from 'node:path'; import { pathToFileURL } from 'node:url'; import { mkdtempSync, mkdirSync, writeFileSync } from 'node:fs';
const repo = process.argv[2];
const M = await import(pathToFileURL(join(repo, 'scripts', 'check_styles.mjs')).href);
const S = await import(pathToFileURL(join(repo, 'scripts', 'styles_source.mjs')).href);
const styles = S.loadRegistry(repo).styles;
const res = { enforced: M.WP12_RULES };
const hit = (s) => M.NUMBER_OF_STYLES.test(s);
res.numberYes = ['six styles', 'All 6 styles', 'in allen sechs Stilen', 'Alle 6 Stile', 'Nemokama peržiūra 6 stiliais', 'Visi 6 stiliai', 'hat stílusban', '6 stílusban', 'in six styles. The watermarked', 'seven styles'].map(hit);
res.numberNo = ['any style', 'in the style you choose', 'Choose a style', 'One eye, any style', 'Two eyes (Couple Duo), jeder Stil', 'iki 8 akiu', 'Sechs Augen auf einem Kunstwerk'].map(hit);
let out = []; M.checkNumberOfStyles([['landing', { en: { a: { b: 'All 6 styles' } } }]], out); res.numberCheck = out;
out = []; M.checkRuntimeTokens({ en: { pricing: { artBackgroundNote: 'Celestial Gold, Deep Nebula' } }, de: { pricing: { artBackgroundNote: '{styles}', severalNote: 'Zwei bis acht Augen' } } }, out); res.tokens = out;
const dir = mkdtempSync(join(process.argv[3], 'wp1-terms-')); mkdirSync(join(dir, 'src/legal/docs'), { recursive: true });
writeFileSync(join(dir, 'src/legal/docs/terms.ts'), "const rows = [['One eye, Clean Iris', eur(PRICE_CENTS.studioBlack, 'en')], ['Each further eye', `+${eur(1, 'en')}, up to ${MAX_EYES} eyes on one artwork`], ['x', 'up to 8 eyes']];\n");
out = []; M.checkTerms(dir, styles, out, ['src/legal/docs/terms.ts'], true); res.termsOn = out;
out = []; M.checkTerms(dir, styles, out, ['src/legal/docs/terms.ts'], false); res.termsOff = out;
console.log(JSON.stringify(res));
""")
rc, so, se = run_node([RULES, REPO, TMP])                       # the probe's folder is made inside TMP, which the suite removes at exit
rules = last_json(so)
check("the rules of items 4 and 7 (WP12) are built: the number-of-styles pattern catches six, 6, sechs, 6 stiliais, stilus and spares 'any style'",
      bool(rules) and all(rules["numberYes"]) and not any(rules["numberNo"]) and len(rules["numberCheck"]) == 1 and "states a number of styles" in rules["numberCheck"][0],
      rules or (rc, se[-400:]))
check("... the run-time token rule flags a written list of art styles and a written number of eyes and accepts {styles}; the count-free terms rule flags the printed maximum "
      "(the constant and a digit before eyes) only when enforced; it IS enforced now (WP12_RULES)",
      bool(rules) and len(rules["tokens"]) == 2 and "landing.en.pricing.artBackgroundNote" in rules["tokens"][0] and "landing.de.pricing.severalNote" in rules["tokens"][1]
      and any("prints the maximum number of eyes" in p for p in rules["termsOn"]) and any('prints a number of eyes ("8 eyes")' in p for p in rules["termsOn"])
      and not any("number of eyes" in p for p in rules["termsOff"]) and rules["enforced"] is True, rules or (rc, se[-400:]))

# ============================================================================================ 6. build-check hazards (IE1) that apply to WP1
section("6. build-check hazards: a decimal price in a test file, a function without samples, a brand name equal in two languages")
PRICE_LEAK = "19" + "." + "97"
root = os.path.join(TMP, "ie1_price")
copy_repo(root)
put(root, "scripts/styles_tests/zz_leak.py", f"PRICE = '{PRICE_LEAK}'\n")
rc, so, se = run_node([os.path.join(root, "scripts", "check_prices.mjs")], cwd=root)
check("IE1: a decimal price in a test file under scripts/ is refused by the price check, with the file and the price",
      rc == 1 and "zz_leak.py: writes the price " + PRICE_LEAK in se, (rc, se[-300:]))
TEXTRUN = os.path.join(TMP, "wp1_textcheck.mjs")
with open(TEXTRUN, "w", encoding="utf-8", newline="\n") as f:
    f.write(r"""
import { createRequire } from 'node:module'; import { join } from 'node:path'; import { pathToFileURL } from 'node:url';
const [repo, root] = process.argv.slice(2);
const req = createRequire(join(repo, 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const { checkTexts } = await import(pathToFileURL(join(repo, 'scripts', 'check_texts.mjs')).href);
const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root })).module;
console.log(JSON.stringify(await checkTexts(load, root)));
""")


def text_probs(root):
    rc2, so2, se2 = run_node([TEXTRUN, REPO, root])
    probs = last_json(so2)
    return probs if probs is not None else [f"NO OUTPUT rc={rc2} {se2[-300:]}"]


def add_entry(root, line):
    """One more key before each `save:` of the four /try dictionaries (English and German in copy.ts, Lithuanian, Hungarian). The marker was `namesPlaceholder:`
    until WP11 replaced that one free line by the names form (src/try/Words.tsx); `save:` (result.save) is one key per dictionary as well."""
    for rel in ("src/try/copy.ts", "src/try/copy.lt.ts", "src/try/copy.hu.ts"):
        path = os.path.join(root, *rel.split("/"))
        text = open(path, encoding="utf-8", newline="").read()
        text, k = re.subn(r"^(\s*)save: ", lambda m: f"{m.group(1)}{line}\n{m.group(1)}save: ", text, flags=re.M)
        assert k >= 1, rel
        open(path, "w", encoding="utf-8", newline="").write(text)


root = os.path.join(TMP, "ie1_brand_ok")
copy_repo(root)
add_entry(root, "brandProbe: 'Kiss Collision',")
p = text_probs(root)
check("IE1: a brand name that is the same words in English and in Lithuanian or Hungarian passes, now that the names are in ENGLISH_OK", p == [], p[:3])
root = os.path.join(TMP, "ie1_brand_bad")
copy_repo(root)
add_entry(root, "brandProbe: 'Frost Collision',")
p = text_probs(root)
check("IE1: ... and an English name that is not listed is refused word for word, in both languages",
      sum("brandProbe" in x and "word for word the English or German text" in x for x in p) >= 2, p[:4])
root = os.path.join(TMP, "ie1_samples")
copy_repo(root)
add_entry(root, "probeFn: (n: number) => `${n}`,")
p = text_probs(root)
check("IE1: a function of a copy dictionary without a SAMPLES entry is refused",
      any("probeFn: no sample arguments in scripts/check_texts.mjs SAMPLES" in x for x in p), p[:3])

# ============================================================================================ 7. hygiene, import weight
section("7. hygiene: no dash, no secret, Python 3.12 syntax, a light import")
NEW_FILES = ["api/_lib/styles_registry.py", "api/_lib/styles_engine.py", "api/_lib/catalogue.py", "api/_lib/layout_names.py", "src/shared/styles.ts",
             "src/shared/layouts.ts", "scripts/styles_source.mjs",
             "scripts/check_styles.mjs", "scripts/check_styles.d.mts", "scripts/styles_tests/test_registry.py"]
check("the new files hold no en or em dash and no secret-looking value",
      all(not re.search(DASH, read(f)) and not re.search(r"(sk_" + "live|sk_" + "test_|whsec" + "_|re" + "_[A-Za-z0-9]{10})", read(f)) for f in NEW_FILES),
      [f for f in NEW_FILES if re.search(DASH, read(f))])
bad312 = []
for f in ("api/_lib/styles_registry.py", "api/_lib/styles_engine.py", "api/_lib/catalogue.py", "api/_lib/layout_names.py", "api/_lib/iris.py", "api/_lib/pay.py",
          "api/_lib/pay_lt.py", "api/_lib/pay_hu.py", "api/_lib/abtest.py", "api/compose.py", "api/master_compose.py", "scripts/test_flow.py"):
    try:
        ast.parse(read(f), feature_version=(3, 12))
    except SyntaxError as e:
        bad312.append((f, str(e)))
check("every Python file this package touched parses as Python 3.12", not bad312, bad312)
check("catalogue.py starts with the __future__ import (the module rule of the v3 work)",
      re.search(r'"""\r?\nfrom __future__ import annotations\r?\n', read("api/_lib/catalogue.py")) is not None)
times, mods = [], []
for _ in range(3):
    code = ("import time, sys; sys.path.insert(0, sys.argv[1]); t = time.perf_counter(); from _lib import catalogue; print(time.perf_counter() - t); "
            "print(sorted(m for m in sys.modules if m.startswith('_lib.')))")
    r = subprocess.run([sys.executable, "-c", code, API], capture_output=True, text=True, encoding="utf-8")
    lines = r.stdout.strip().splitlines()
    times.append(float(lines[0]))
    mods = json.loads(lines[1].replace("'", '"'))
check("IE2: importing the catalogue takes at most 150 ms and loads only the registry files and the layout words besides itself (no engine, no store, no network module)",
      min(times) <= 0.15 and mods == ["_lib.catalogue", "_lib.layout_names", "_lib.styles_engine", "_lib.styles_registry"], (times, mods))
imports = set(re.findall(r"^(?:import|from) ([\w.]+)", read("api/_lib/catalogue.py"), re.M))
check("the catalogue needs no new dependency: it imports the standard library and the registry files (and the layout words) only",
      imports <= {"__future__", "hashlib", "importlib.util", "json", "."} | {"."}, imports)

# ============================================================================================ 8. WP2: the words for the layouts (I1, I15)
section("8. WP2: the words for the layouts are one table: golden strings in four languages, the readers, the page code")
LN_TEXT = read("api/_lib/layout_names.py")
ln_lit = json.loads(LN_TEXT[LN_TEXT.index("\nLAYOUT_NAMES = {") + len("\nLAYOUT_NAMES = "):])
LANGS4 = ("en", "de", "lt", "hu")
OLD_WORDS = {   # the four tables of the e-mails and the eight dictionaries of the pages, as they stood on 1d58fbf: en, de, lt, hu
    "single": ("Single", "Einzeln", "Viena akis", "Egy szem"),
    "duo": ("Side by side", "Nebeneinander", "Greta", "Egymás mellett"),
    "fusion": ("Fusion", "Fusion", "Susiliejimas", "Összeolvadás"),
    "triangle": ("Triangle", "Dreieck", "Trikampis", "Háromszög"),
    "row": ("In a row", "In einer Reihe", "Vienoje eilėje", "Egy sorban"),
    "grid": ("Grid", "Raster", "Tinklelis", "Rács"),
    "galaxy": ("Galaxy", "Galaxie", "Galaktika", "Galaxis"),
}
SPEC_WORDS = {  # the draft words of the integration specification 5.4 (PRODUCT.md 2.1): en, de, lt, hu
    "trio": ("Triangle", "Dreieck", "Trikampis", "Háromszög"),
    "diag": ("Diagonal", "Diagonale", "Įstrižai", "Átlós"),
    "zigzag": ("Zigzag", "Zickzack", "Zigzagas", "Cikcakk"),
    "cluster": ("Cluster", "Gruppe", "Grupė", "Csoport"),
    "brick": ("Rows", "Reihen", "Eilės", "Sorok"),
    "ring": ("Ring", "Ring", "Žiedas", "Gyűrű"),
    "flower": ("Flower", "Blume", "Gėlė", "Virág"),
    "chain": ("Chain", "Kette", "Grandinė", "Lánc"),
}
taken_ids = {x for d in R.STYLES.values() for lst in d["layouts"].values() for x in lst}
check("layout_names.py: the literal is plain JSON and is what Python imports; UTF-8 words (not ASCII), no en or em dash",
      ln_lit == LN.LAYOUT_NAMES == C.LAYOUT_NAMES and any(ord(ch) > 127 for ch in LN_TEXT) and not re.search(DASH, LN_TEXT))
check("16 layout ids with exactly the four languages each, short words with no space at either end; the ids are exactly the layouts the registry's styles take",
      len(ln_lit) == 16 and set(ln_lit) == taken_ids and all(set(v) == set(LANGS4) and all(isinstance(w, str) and w == w.strip() and 0 < len(w) <= 40 for w in v.values()) for v in ln_lit.values())
      and C.layout_ids() == tuple(ln_lit), (sorted(set(ln_lit) ^ taken_ids), len(ln_lit)))
check("the words of the seven legacy layouts are the ones the e-mails and the pages always printed, 7 ids x 4 languages (28 strings)",
      all(C.layout_name(lg, i) == OLD_WORDS[i][k] for i in OLD_WORDS for k, lg in enumerate(LANGS4)) and len(OLD_WORDS) * 4 == 28,
      [(i, lg, C.layout_name(lg, i)) for i in OLD_WORDS for k, lg in enumerate(LANGS4) if C.layout_name(lg, i) != OLD_WORDS[i][k]])
check("the words of the v3 layouts are the drafts of the specification (trio, diag, zigzag, cluster, brick, ring, flower, chain), and pair has all four",
      all(C.layout_name(lg, i) == SPEC_WORDS[i][k] for i in SPEC_WORDS for k, lg in enumerate(LANGS4))
      and [C.layout_name(lg, "pair") for lg in LANGS4] == ["Pair", "Paar", "Pora", "Pár"])
check("layout_name: any other language reads English; an id with no word (or not text) gives the default, which is '' unless the caller passes one",
      C.layout_name("xx", "duo") == "Side by side" and C.layout_name(None, "grid") == "Grid" and C.layout_name(["de"], "grid") == "Grid"
      and C.layout_name("en", "spiral") == "" and C.layout_name("en", None) == "" and C.layout_name("en", 3) == "" and C.layout_name("en", ["duo"]) == ""
      and C.layout_name("lt", "spiral", "spiral") == "spiral" and C.layout_name("lt", "duo", "spiral") == "Greta")
check("no second table: pay.LAYOUT_NAMES, pay_lt.LAYOUT_NAMES_LT and pay_hu.LAYOUT_NAMES_HU are gone; the registry hash is about engine data, not words",
      not hasattr(pay, "LAYOUT_NAMES") and not hasattr(pay.pay_lt, "LAYOUT_NAMES_LT") and not hasattr(pay_hu, "LAYOUT_NAMES_HU")
      and "Nebeneinander" not in C.canonical())

# --- the e-mails: the confirmation prints the same layout words as before, in four languages (and nothing for one eye or an unknown layout)
PACK_PATH = os.path.join(REPO, "dist", "legal", "order-mail.json")
check("the built legal pack the confirmation mail needs is there (npm run build writes dist/legal/order-mail.json)", os.path.isfile(PACK_PATH), PACK_PATH)
MAIL_PHRASE = {"en": ", layout {w}", "de": ", Anordnung {w}", "lt": ", išdėstymas {w}", "hu": ", elrendezés: {w}"}
if os.path.isfile(PACK_PATH):
    with open(PACK_PATH, encoding="utf-8") as f:
        MPACK = json.load(f)
    consent = {"at": "2026-01-01T00:00:00Z", "text": "I agree."}

    def mail_text(lang, n, layout):
        market = "hu" if lang == "hu" else "eu"
        spec = {"eyes": n, "style": "supernova", "layout": layout, "names": "", "title": "", "lang": lang, "market": market}
        paid = {"spec": spec, "market": market, "paid_at": 1900000000, "amount_total": 5000, "currency": "huf" if market == "hu" else "eur"}
        return pay.confirmation_mail("260101-abcd", paid, "k" * 40, MPACK, consent)[1]

    def artwork_row(lang, n, layout):
        """The artwork row of the confirmation: the line that names the style (the item name, then the layout phrase when there is one)."""
        return next(x for x in mail_text(lang, n, layout).splitlines() if "Supernova" in x)

    bad_mail, n_mail = [], 0
    for layout, n in (("duo", 2), ("fusion", 2), ("triangle", 3), ("row", 3), ("row", 4), ("grid", 4), ("galaxy", 5), ("galaxy", 8)):
        for k, lg in enumerate(LANGS4):
            n_mail += 1
            if not artwork_row(lg, n, layout).endswith(MAIL_PHRASE[lg].format(w=OLD_WORDS[layout][k])):
                bad_mail.append((lg, n, layout))
    check("the confirmation e-mail ends its artwork row with the old layout word in en, de, lt and hu for every legacy layout it can carry (32 mails)",
          not bad_mail and n_mail == 32, bad_mail[:4])
    check("one eye: no layout phrase in the artwork row of any language, as before",
          all(MAIL_PHRASE[lg].split("{w}")[0] not in artwork_row(lg, 1, "single") for lg in LANGS4))
    check("a v3 layout is read by the same table (pair prints Pair, Paar, Pora, Pár) and an unknown layout prints no phrase instead of failing",
          all(artwork_row(lg, 2, "pair").endswith(MAIL_PHRASE[lg].format(w=w)) for lg, w in zip(LANGS4, ("Pair", "Paar", "Pora", "Pár")))
          and all(MAIL_PHRASE[lg].split("{w}")[0] not in artwork_row(lg, 2, "spiral") for lg in LANGS4))

# --- the page code: layoutName, the picker's label, the order page's word, the layouts of the picker, the canvas: through Vite's module runner
PROBE2 = os.path.join(TMP, "wp2_probe.mjs")
with open(PROBE2, "w", encoding="utf-8", newline="\n") as f:
    f.write(r"""
import { createRequire } from 'node:module'; import { join } from 'node:path'; import { pathToFileURL } from 'node:url';
const repo = process.argv[2];
const req = createRequire(join(repo, 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root: repo })).module;
const LY = await load('./src/shared/layouts.ts');
const S = await load('./src/shared/styles.ts');
const TC = await load('./src/try/copy.ts');
const OC = await load('./src/order/copy.ts');
const M = await load('./src/try/multi.ts');
const out = { names: LY.LAYOUT_NAMES, ids: LY.LAYOUT_IDS, langs: LY.LAYOUT_LANGS };
const ids = [...LY.LAYOUT_IDS, 'spiral', '__proto__', 'constructor', 'toString'];
out.lookup = {};
for (const lang of ['en', 'de', 'lt', 'hu', 'xx', '']) out.lookup[lang] = ids.map((id) => [LY.layoutName(lang, id), LY.layoutName(lang, id, 'raw:' + id), LY.isLayout(id)]);
out.label = {};
for (const lang of ['en', 'de', 'lt', 'hu']) { TC.setCopyLang(lang); out.label[lang] = [...LY.LAYOUT_IDS, 'spiral'].map((id) => TC.layoutLabel(id)); }
// no dictionary of /try or /order holds a layout table any more: no key "layouts", no object with two layout ids as keys
const hits = [];
const walk = (v, path) => {
  if (!v || typeof v !== 'object') return;
  const keys = Object.keys(v);
  if (keys.includes('layouts') || keys.filter((k) => LY.LAYOUT_IDS.includes(k)).length >= 2) hits.push(path);
  for (const k of keys) walk(v[k], path + '.' + k);
};
for (const [name, dict] of [['try', TC.COPY], ['order', OC.ORDER_COPY]]) for (const [lang, c] of Object.entries(dict)) walk(c, name + '.' + lang);
out.tables = hits;
out.layoutsFor = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => [[...M.layoutsFor(n)], [...S.legacyLayoutsFor(n)]]);
out.eff = [[2, 'fusion'], [2, 'grid'], [2, null], [9, 'x'], [3, 'row'], [4, 'row'], [8, 'galaxy'], [1, 'duo'], [2, 'pair']].map(([n, w]) => M.effectiveLayout(n, w));
out.canvas = [[1, 'single'], [2, 'duo'], [2, 'fusion'], [3, 'row'], [3, 'triangle'], [4, 'row'], [4, 'grid'], [5, 'galaxy'], [8, 'galaxy']].map(([n, l]) => M.canvasSize(n, l));
console.log(JSON.stringify(out));
""")
rc, so, se = run_node([PROBE2, REPO])
p2 = last_json(so)
check("the node probe loads layouts.ts, styles.ts, the /try and /order copy and multi.ts", p2 is not None, (rc, se[-600:], so[-300:]))
if p2:
    check("src/shared/layouts.ts reads the very table the server reads (16 ids x 4 languages), in the file's order", p2["names"] == C.LAYOUT_NAMES and p2["ids"] == list(C.layout_ids()) and p2["langs"] == list(LANGS4))
    ids_ = p2["ids"] + ["spiral", "__proto__", "constructor", "toString"]
    lk_bad = []
    for lg in ("en", "de", "lt", "hu", "xx", ""):
        for j, i in enumerate(ids_):
            word, raw, is_l = p2["lookup"][lg][j]
            want = C.layout_name(lg, i)
            if (word, raw, is_l) != (want, want or ("raw:" + i), i in C.LAYOUT_NAMES):
                lk_bad.append((lg, i, word, raw, is_l))
    check("layoutName(lang, id, fallback) is catalogue.layout_name: the same word for every id and language, English for another language, the fallback (never a prototype member) for no word",
          not lk_bad, lk_bad[:4])
    check("the picker's layoutLabel gives the old word in each of the four languages for the seven legacy layouts, the raw id for an unknown one",
          all(p2["label"][lg][p2["ids"].index(i)] == OLD_WORDS[i][k] for i in OLD_WORDS for k, lg in enumerate(LANGS4))
          and all(p2["label"][lg][-1] == "spiral" for lg in LANGS4))
    check("no dictionary of /try or /order holds a layout table any more (no key layouts, no object with two layout ids as keys)", p2["tables"] == [], p2["tables"][:4])
    check("the picker offers the same layouts as before for 0 to 9 eyes, from the registry's legacy table (multi.ts layoutsFor, styles.ts legacyLayoutsFor, iris.py LAYOUTS)",
          all(a == b == list(OLD_LAYOUTS.get(n, ())) for n, (a, b) in enumerate(p2["layoutsFor"])), p2["layoutsFor"][:3])
    check("effectiveLayout as before: the wanted layout when the count takes it, else the engine's default (or single when the count has none)",
          p2["eff"] == ["fusion", "duo", "duo", "single", "row", "row", "galaxy", "single", "duo"], p2["eff"])
    check("canvasSize as before for the legacy layouts (1024 x 1024, 3:2, 2:1, 21:9, 4:5)",
          p2["canvas"] == [{"w": 1024, "h": 1024}, {"w": 1024, "h": 683}, {"w": 1024, "h": 683}, {"w": 1024, "h": 512}, {"w": 819, "h": 1024},
                           {"w": 1024, "h": 439}, {"w": 819, "h": 1024}, {"w": 819, "h": 1024}, {"w": 819, "h": 1024}], p2["canvas"])
rc, so, se = run_node(["scripts/check_styles.mjs"])
check("the build log line says how many layouts are named in four languages", rc == 0 and "16 layouts named in en, de, lt, hu" in so, (rc, so, se[-300:]))

# --- the text check reads the layout words: a dash, an English word in Lithuanian, a German word in Hungarian
for label, case_fn, needle in [
    ("an en dash in an English layout word", lambda r: sub("t", r, "api/_lib/layout_names.py", '"en": "Side by side"', '"en": "Side' + chr(0x2013) + 'by side"'), "layout words.duo (en): an en or em dash"),
    ("an em dash in a German layout word", lambda r: sub("t", r, "api/_lib/layout_names.py", '"de": "Nebeneinander"', '"de": "Neben' + chr(0x2014) + 'einander"'), "layout words.duo (de): an en or em dash"),
    ("an English word in a Lithuanian layout word", lambda r: sub("t", r, "api/_lib/layout_names.py", '"lt": "Tinklelis"', '"lt": "Photo tinklelis"'), 'layout words.grid (lt): untranslated English "Photo"'),
    ("a German word in a Hungarian layout word", lambda r: sub("t", r, "api/_lib/layout_names.py", '"hu": "Rács"', '"hu": "Bitte rács"'), 'layout words.grid (hu): untranslated German "Bitte"'),
    ("a layout with an empty word in one language", lambda r: sub("t", r, "api/_lib/layout_names.py", '"hu": "Csoport"', '"hu": ""'), "layout words: \"cluster\" has no hu word"),
]:
    root = os.path.join(TMP, "wp2_text_" + re.sub(r"[^a-z0-9]+", "_", label.lower())[:36])
    copy_repo(root)
    case_fn(root)
    probs = text_probs(root)
    check(f"the text check refuses: {label}", not PROBLEMS.get("t") and any(needle in p for p in probs), (PROBLEMS.get("t"), needle, probs[:3]))
    PROBLEMS.pop("t", None)

fails = len([r for r in RESULTS if not r])
print(f"\n{len(RESULTS) - fails} of {len(RESULTS)} passed" + (f"; {fails} FAILED" if fails else ""))
sys.exit(1 if fails else 0)
