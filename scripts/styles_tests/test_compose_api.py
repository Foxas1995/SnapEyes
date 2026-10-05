# -*- coding: utf-8 -*-
"""WP10 of the v3 engine work: the compose API v3 (api/compose.py): tiles, pick, plan, reply. Tests I13 (the API contract: request and reply, errors,
the batch cost guard, the limits at eight eyes, the names as a list and as the old string), I14 (preview protection: every tile watermarked on every disc
at display strength, the overlay anchored to the iris, the aligned median attack, sealed copies only, unlock unmintable, a customer never gets a larger
preview or a laboratory style), I22 (the recommended tile is never one that cannot be bought, its reason line belongs to the final pick), IE7 (a tile
does not depend on the other tiles of its call, a 480 px tile agrees with the 1024 px preview), IE6 (the heavy render slot and the daily ceiling of
tiles) and the events the API writes.

  1. the module: its files, its words in four languages, nothing that must not be in it
  2. the request and its errors (400, 422 and their codes), the legacy requests (I3)
  3. the tiles, the pick and its reason line, the gate states of a tile (I22)
  4. a batch: one call, the order of the tiles, a tile alone against the tile in a batch (IE7), the cost guard, the slot, the daily ceiling
  5. the replies: fields, plan8, design_used and fallback, the sizes at eight eyes, the names as a list and as a string
  6. multi eye plumbing on a stand in family (layout, options, names, eye ids, work side): the real families land in their own work packages
  7. the watermark (I14): every tile on every disc, outside the discs the legacy one, the overlay anchored to the iris, the aligned median attack
  8. a tile against the preview (IE7): the matter outside the iris agrees (SSIM)
  9. the laboratory flag (lab and an admin key), unlock, the help beacon, the events
 10. over HTTP: the statuses, Retry-After, the language of a refusal, the legacy page's request unchanged
No network, no image model, no real eye in the repository (synthetic irises: synth_iris).
    python test_compose_api.py   prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as v3compose."""
import ast
import base64
import contextlib
import importlib.util
import io
import itertools
import json
import math
import os
import re
import sys
import tempfile
import threading
import time
import unittest.mock as mock

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
TMP = tempfile.mkdtemp(prefix="snapeyes_v3compose_")
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

STORE = os.path.join(TMP, "store")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])                       # the payments harness' synthetic keys and ticket secret, a local store folder
os.environ["SNAPEYES_ADMIN_SECRET"] = "wp10-admin-secret-for-tests-0123456789abcdef0123"
os.environ["STYLE_PLATE_CACHE"] = os.path.join(TMP, "cache")
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
sys.path.insert(0, API)
import numpy as np  # noqa: E402
import requests  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib import store  # noqa: E402
from _lib import ops  # noqa: E402
import _lib.styles as ST  # noqa: E402
from _lib.styles import core as C, eye as EYE, costs as CO, guard as GD, steps as SPS, gate as GATE  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
INVISIBLE = "[" + "".join(chr(c) for lo, hi in ((0x200b, 0x200f), (0x2028, 0x202e), (0x2060, 0x2064), (0xfeff, 0xfeff)) for c in range(lo, hi + 1)) + "]"
MIDDLE_DOT = chr(0xb7)
LT_LETTERS = "".join(chr(c) for c in (0x105, 0x10d, 0x119, 0x117, 0x12f, 0x161, 0x173, 0x16b, 0x17e))      # the Lithuanian letters the artwork font draws
spec_c = importlib.util.spec_from_file_location("compose", os.path.join(API, "compose.py"))
CMP = importlib.util.module_from_spec(spec_c)
spec_c.loader.exec_module(CMP)
H.MODS["compose"] = CMP
SINGLES = ("solo.clean", "solo.powder", "solo.splash", "solo.radiance", "solo.gold")      # the single styles that have a tile slot (Elements has none)
LEGACY = list(CT.legacy_ids())
EVENTS = []
_real_record, _real_many = E.record, E.record_many
E.record = lambda kind, **f: EVENTS.append((kind, dict(f))) or False
E.record_many = lambda kind, rows, **k: ([EVENTS.append((kind, dict(r))) for r in rows], len(rows))[1]


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def b64(raw):
    return base64.b64encode(raw).decode("ascii")


def raised(fn):
    try:
        fn()
    except Exception as e:  # noqa
        return e
    return None


class Show:
    """A style made visible, held or retired for the length of a block (the ceilings are the registry's: a test may not raise one for good)."""
    def __init__(self, *styles, stage="preview"):
        self.styles, self.stage = styles, stage

    def __enter__(self):
        self.old = {s: CT.STYLES[s]["stage"] for s in self.styles}
        for s in self.styles:
            CT.STYLES[s]["stage"] = self.stage

    def __exit__(self, *a):
        for s, st in self.old.items():
            CT.STYLES[s]["stage"] = st


# ------------------------------------------------------------------------------------------ the eyes: sealed as /api/enhance seals them
_EYES = {}


def eye(name):
    """(jpeg bytes, profile, the reply of preview.protect) of a synthetic fixture: the clean bytes, the profile measured on them, the three seals."""
    if name not in _EYES:
        jpeg = SI.jpeg_bytes(name)
        prof = EYE.profile_of_bytes(jpeg, pad=1.12)
        _EYES[name] = (jpeg, prof, P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=prof))
    return _EYES[name]


def sealed(name, side=None):
    p = eye(name)[2]
    return p["sealed"] if side is None else p["sealed_sizes"][str(side)]


def comp(body, bearer=""):
    with contextlib.redirect_stdout(io.StringIO()):
        return CMP.compose(body, bearer)


def img_of(reply_or_tile):
    return Image.open(io.BytesIO(base64.b64decode(reply_or_tile["image"]))).convert("RGB")


def img_of(reply_or_tile):
    return Image.open(io.BytesIO(base64.b64decode(reply_or_tile["image"]))).convert("RGB")


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=300)
    try:
        return r.status_code, r.json(), r
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}, r


def tile_of(reply, style):
    return next(t for t in reply["tiles"] if t["id"] == style)


# ============================================================================================ 1. the module
section("1. the module: its files, its words, what must not be in it")
SRC = read(os.path.join(API, "compose.py"))
ast.parse(SRC, feature_version=(3, 12))
check("api/compose.py parses as Python 3.12 (Vercel's default) and carries no dash, no invisible character and no written price",
      not re.search(DASH, SRC) and not re.search(INVISIBLE, SRC)
      and not re.search(r"\d[.,]\d{2}\s*(EUR|" + chr(0x20ac) + r")|A\$\d|\d\s?Ft\b", SRC))
check("every refusal has its sentence in the four languages (en, de, lt, hu), different in each, with no dash",
      {"stage", "eyes", "gate", "reseal", "bar_pupil", "too_many_styles", "busy_retry", "tiles_paused"} <= set(CMP.WORDS)
      and all(set(CMP.WORDS[k]) == {"en", "de", "lt", "hu"} and len({CMP.WORDS[k][lg] for lg in CMP.WORDS[k]}) == 4
              and all(not re.search(DASH, CMP.WORDS[k][lg]) for lg in CMP.WORDS[k]) for k in CMP.WORDS), sorted(CMP.WORDS))
check("the admin module is imported on use only (never at the top of compose.py) and the lab flag is read as the boolean true",
      not re.search(r"^(import|from)\s.*\bops\b", SRC, re.M) and "ops.check_admin_key" in SRC and 'body.get("lab") is True' in SRC)
child = ("import sys, importlib.util as u; sys.path.insert(0, r'%s'); s = u.spec_from_file_location('compose', r'%s'); m = u.module_from_spec(s); s.loader.exec_module(m); "
         "print(sorted(k for k in sys.modules if k.startswith('_lib.styles.') and k.split('.')[2] in ('singles', 'collision', 'universe')))") % (API, os.path.join(API, "compose.py"))
mods_loaded = os.popen(f'"{sys.executable}" -c "{child}"').read().strip()
check("importing compose.py loads no engine family (singles, collision and universe load on first use)", mods_loaded == "[]", mods_loaded)

# ============================================================================================ 2. the request and its errors
section("2. the request: errors and codes, the legacy requests")
S1 = [sealed("blue_round")]
S1_560 = sealed("blue_round", 560)
e400 = {}
with Show(*SINGLES):
    for label, body in (("a style that is not the registry's", {"style": "nope"}), ("style and styles together", {"style": "solo.gold", "styles": ["solo.powder"]}),
                        ("a size of 700", {"style": "solo.gold", "size": 700}), ("a size of 2048", {"style": "solo.gold", "size": 2048}),
                        ("a size as text", {"style": "solo.gold", "size": "1024"}), ("a size as a boolean", {"style": "solo.gold", "size": True}),
                        ("a size of 4096 in a batch", {"styles": ["solo.gold"], "size": 4096}),
                        ("an unknown option", {"style": "solo.gold", "opts": {"colour": "red"}}), ("opts that is a list", {"style": "solo.gold", "opts": ["swap"]}),
                        ("swap that is a number", {"style": "solo.gold", "opts": {"swap": 1}}), ("rotate out of range", {"style": "solo.gold", "opts": {"rotate": 9}}),
                        ("a look with a space", {"style": "solo.gold", "opts": {"look": "a b"}}), ("a layout the style does not take", {"style": "solo.gold", "layout": "ring"}),
                        ("a layout that is a number", {"style": "solo.gold", "layout": 5}), ("a style that is a number", {"style": 5}),
                        ("styles that is not a list", {"styles": "solo.gold"}), ("styles with a number in it", {"styles": ["solo.gold", 3]}),
                        ("the same style twice", {"styles": ["solo.gold", "solo.gold"]}), ("no eyes", {"style": "solo.gold", "sealed": []}),
                        ("nine eyes", {"style": "solo.gold", "sealed": [S1_560] * 9})):
        e400[label] = raised(lambda b=body: comp(dict({"sealed": S1}, **b)))
check("a request that is not one is a 400 (a ClientError): " + ", ".join(e400),
      all(isinstance(e, L.ClientError) for e in e400.values()), {k: type(v).__name__ for k, v in e400.items() if not isinstance(v, L.ClientError)})
check("the 400 sentences say what is wrong and carry nothing the caller sent (a style, an option, a layout)",
      not any("nope" in str(e) or "colour" in str(e) or "ring" in str(e) for e in e400.values()))
e_lab = {}
good_key = ops.mint_admin_key(600)
with Show("solo.gold", stage="lab"):
    for label, body, bearer in (("a laboratory style", {"style": "solo.gold"}, ""), ("with lab true and no key", {"style": "solo.gold", "lab": True}, ""),
                                ("with lab true and a wrong key", {"style": "solo.gold", "lab": True}, "admin-v1.1999999999.0123456789abcdef0123456789abcdef"),
                                ("with lab true and a work ticket for a key", {"style": "solo.gold", "lab": True}, L.mint_ticket("work")),
                                ("with lab false and a good key", {"style": "solo.gold", "lab": False}, good_key), ("with a good key and no flag", {"style": "solo.gold"}, good_key),
                                ("a planned style", {"style": "pet.solo"}, ""), ("a planned style, lab true, a good key", {"style": "pet.solo", "lab": True}, good_key),
                                ("a laboratory style inside a batch", {"styles": ["solo.gold"], "lab": True}, "")):
        e_lab[label] = raised(lambda b=body, br=bearer: comp(dict({"sealed": S1}, **b), br))
check("a laboratory or planned style from a customer is 422 style_unavailable (why stage, no retry), with or without a lab flag and with a wrong, a missing or a foreign key: " + "; ".join(e_lab),
      all(getattr(e, "status", None) == 422 and e.body["reason"] == "style_unavailable" and e.body["why"] == "stage" and e.body["retry"] is False for e in e_lab.values()),
      {k: (getattr(v, "status", None), getattr(v, "body", v)) for k, v in e_lab.items() if getattr(v, "status", None) != 422})
with Show(*LEGACY, stage="retired"):
    e_ret = raised(lambda: comp({"sealed": S1, "style": "supernova"}))
    e_ret2 = raised(lambda: comp({"sealed": S1, "styles": ["supernova"]}))
check("a retired style is 422 style_unavailable too (it renders for an order already paid, never as a free preview), one style and in a batch",
      all(getattr(e, "status", None) == 422 and e.body["why"] == "stage" for e in (e_ret, e_ret2)))
with Show("solo.gold"):
    e_eyes = raised(lambda: comp({"sealed": [S1_560] * 2, "style": "solo.gold"}))
    e_eyes_b = raised(lambda: comp({"sealed": [S1_560] * 2, "styles": ["solo.gold"]}))
check("a style that does not take the number of eyes is 422 style_unavailable (why eyes), asked alone or in a batch; the body names the style and carries the sentence",
      all(getattr(e, "status", None) == 422 and e.body["why"] == "eyes" and e.body["style"] == "solo.gold" for e in (e_eyes, e_eyes_b)) and e_eyes.body["error"] == CMP.WORDS["eyes"]["en"], (e_eyes, e_eyes_b))
check("an unknown style, a style not for these eyes and a held style are different answers: 400, 422 eyes, 422 stage",
      isinstance(e400["a style that is not the registry's"], L.ClientError) and e_eyes.body["why"] == "eyes" and e_lab["a laboratory style"].body["why"] == "stage")

r_plain = comp({"irises": [b64(eye("blue_round")[0])], "style": "supernova", "pad": 1.12, "names": "Anna;Max", "lang": "en"})
r_one = comp({"iris": b64(eye("blue_round")[0]), "style": "supernova", "pad": 1.12, "names": "Anna;Max"})
r_sealed = comp({"sealed": S1, "style": "supernova", "pad": 1.12, "names": "Anna;Max"})
r_list = comp({"sealed": S1, "style": "supernova", "pad": 1.12, "names": ["Anna", "Max"]})
r_default = comp({"sealed": S1, "pad": 1.12})
im_direct = L.compose_multi([L.b64_to_pil(b64(eye("blue_round")[0]))], style="supernova", names="Anna;Max", watermark=True, r_frac=L.iris_radius_frac(1.12), size=1024,
                            layout="single", fmt="artwork")
check("a legacy request (plain irises, the one eye form, a sealed iris) is accepted and draws exactly what the legacy engine draws: the same bytes as compose_multi (I3)",
      r_plain["image"] == r_one["image"] == r_sealed["image"] == L.pil_to_b64(im_direct, "JPEG", 90))
check("the new wire form of the names (a list) gives the legacy preview of the old string, and a request with no style at all gets the default style",
      r_list["image"] == r_sealed["image"] and r_default["style"] == CT.DEFAULT_STYLE)
OLD_FIELDS = {"ok", "style", "layout", "layouts", "format", "count", "width", "height", "image", "styles", "qa", "eyes"}
NEW_FIELDS = {"tiles", "pick", "size", "opts", "design_used", "fallback", "plan8", "engine", "selfcheck", "timing"}
check("the reply keeps every field of the old reply with the old values and adds the new ones",
      OLD_FIELDS <= set(r_sealed) and NEW_FIELDS <= set(r_sealed) and r_sealed["styles"] == list(CT.previewable_ids(1)) and r_sealed["layouts"] == ["single"]
      and r_sealed["size"] == 1024 and r_sealed["width"] == 1024 and r_sealed["format"] == "artwork" and r_sealed["count"] == 1, sorted(r_sealed))
r_480 = comp({"sealed": S1, "style": "supernova", "size": 480})
check("a legacy style at size 480 is made at 480 px by the legacy engine (a tile of a legacy style); size is the long side", r_480["width"] == r_480["height"] == 480 and r_480["size"] == 480)
e_body = raised(lambda: comp({"irises": ["A" * (CMP.MAX_TOTAL_B64 + 10)], "style": "supernova"}))
e_seal = raised(lambda: comp({"sealed": [S1[0][:-4] + "AAAA"], "style": "supernova"}))
check("a body past MAX_TOTAL_B64 is a 400 ('too large together') and a seal that does not verify is a 400 with the preview sentence; neither reaches an engine",
      isinstance(e_body, L.ClientError) and "too large" in str(e_body) and isinstance(e_seal, L.ClientError) and str(e_seal) == P.refusal(P.SealError()), (e_body, e_seal))

# ============================================================================================ 3. the tiles, the pick, its reason line, the gate states
section("3. the tile list: the pick, its reason, what is held back and why (I22)")
with Show(*SINGLES):
    t_only = comp({"sealed": S1, "styles": []})
    with mock.patch.object(ST, "preview", side_effect=AssertionError("rendered")), mock.patch.object(ST, "tiles", side_effect=AssertionError("rendered")):
        t_free = comp({"sealed": S1, "styles": []})
check("an empty list of styles answers the tile list alone: no image, and nothing is drawn (the page's first call costs no pixel)",
      t_only["batch"] is True and all("image" not in t for t in t_free["tiles"]) and t_free["pick"] is not None and "timing" in t_free
      and {"solo.powder", "solo.gold", "solo.radiance", "solo.clean"} <= {t["id"] for t in t_free["tiles"]})
KEYS_ROW = {"id", "name", "slug", "group", "legacy", "stage", "available", "why", "layouts", "eyes", "price_class", "looks", "pick"}
check("a tile carries id, name, slug, group, stage, available, why, layouts, eyes, price class, looks and pick; exactly one tile is the pick and it is the first",
      all(KEYS_ROW <= set(t) for t in t_free["tiles"]) and sum(t["pick"] for t in t_free["tiles"]) == 1 and t_free["tiles"][0]["pick"] is True
      and t_free["tiles"][0]["id"] == t_free["pick"]["id"])
GOOD = {"cls": "own", "gate": {"lid": {"ok": True}, "fill": {"ok": True}}}


def tile_list(n, recs, stages=None, admin=False):
    """CT.tile_list with some styles at a stage for the length of the call."""
    with Show(*[s for s, st in (stages or {}).items() if st == "live"], stage="live"), Show(*[s for s, st in (stages or {}).items() if st == "preview"], stage="preview"):
        return CT.tile_list(n, recs, admin)


LIVE3 = {"solo.powder": "live", "solo.gold": "live", "solo.radiance": "live"}
p_own, p_brown, p_grey = (tile_list(1, [dict(GOOD, cls=c)], LIVE3) for c in ("own", "dark_brown", "grey"))
p_grey_soon = tile_list(1, [dict(GOOD, cls="grey")], dict(LIVE3, **{"solo.radiance": "preview"}))
check("the pick is the first buyable tile whose pick table lists the colour class, with the key of its reason line (own colours: Powder Burst, dark brown: Celestial Gold, grey: Radiance while it is live)",
      (p_own["pick"], p_own["reason"]) == ("solo.powder", "reason.solo_powder.own") and (p_brown["pick"], p_brown["reason"]) == ("solo.gold", "reason.solo_gold.dark_brown")
      and (p_grey["pick"], p_grey["reason"]) == ("solo.radiance", "reason.solo_radiance.grey"))
check("a tile that is only Soon (preview) is never the pick, and the reason line follows the FINAL pick: grey eyes with Radiance still Soon get another pick and no reason line",
      p_grey_soon["pick"] != "solo.radiance" and p_grey_soon["reason"] is None and any(t["id"] == "solo.radiance" and t["stage"] == "preview" and not t["pick"] for t in p_grey_soon["tiles"]),
      (p_grey_soon["pick"], p_grey_soon["reason"]))
FILL_FAIL = {"cls": "own", "gate": {"lid": {"ok": True}, "fill": {"ok": False, "why": ["fill_lid_margin"]}}}
CT.ENGINES_BUILT_EXTRA.add("universe")                      # the family may or may not be in the repository yet: the tile list reads the catalogue, not the family
p_hard = tile_list(1, [FILL_FAIL], {"solo.universe": "live", "solo.powder": "live", "solo.gold": "live"})
CT.ENGINES_BUILT_EXTRA.discard("universe")
d_hard = {t["id"]: t for t in p_hard["tiles"]}
check("a style whose hard gate rule failed is shown with why gate and is never the pick; an advisory style on the same eye stays available (I22)",
      d_hard["solo.universe"]["available"] is False and d_hard["solo.universe"]["why"] == "gate" and d_hard["solo.powder"]["available"] and p_hard["pick"] != "solo.universe",
      (p_hard["pick"], d_hard["solo.universe"]))
with Show(*LEGACY, stage="retired"):
    p_nothing = CT.tile_list(1, [GOOD])
check("when nothing can be bought the pick is null and so is its reason (the page then shows what it shows for a group with nothing to order)",
      p_nothing["pick"] is None and p_nothing["reason"] is None and CMP._pick_reply(p_nothing) is None)
v1_sz = P.seal(P.unseal(S1_560), kind=P.KIND_COMPOSE)
CT.ENGINES_BUILT_EXTRA.add("collision")
PAIR = ("duo.kiss_collision", "duo.collision_infinity", "duo.clean")
with Show(*PAIR):
    t_ok = {t["id"]: t for t in comp({"sealed": [S1_560, sealed("green_round", 560)], "styles": []})["tiles"]}
    t_lid = {t["id"]: t for t in comp({"sealed": [S1_560, sealed("blue_lid", 560)], "styles": []})["tiles"]}
    t_bar = {t["id"]: t for t in comp({"sealed": [S1_560, sealed("dark_brown_bar", 560)], "styles": []})["tiles"]}
    t_v1 = {t["id"]: t for t in comp({"sealed": [v1_sz, sealed("green_round", 560)], "styles": []})["tiles"]}
    e_gate = raised(lambda: comp({"sealed": [S1_560, sealed("blue_lid", 560)], "style": "duo.kiss_collision"}))
    e_reseal = raised(lambda: comp({"sealed": [v1_sz, sealed("green_round", 560)], "style": "duo.kiss_collision"}))
CT.ENGINES_BUILT_EXTRA.discard("collision")
r_lidreply = comp({"sealed": [S1_560, sealed("blue_lid", 560)], "styles": []})
check("an eye that fails a gate rule carries the reason codes of the failing rules in the reply's eyes (why), for the retake state; an eye that passes carries no why",
      "why" not in r_lidreply["eyes"][0] and r_lidreply["eyes"][1]["gate"]["lid"] is False and r_lidreply["eyes"][1]["why"]
      and all(c in GATE.WHY["lid"] + GATE.WHY["fill"] for c in r_lidreply["eyes"][1]["why"]), r_lidreply["eyes"])
check("pair tiles: both eyes clean: every pair style available and Soon (stage preview); an eye that fails the lid rule greys them all (why gate); a bar pupil refuses every pair design (why bar_pupil: the engine refuses Kiss too)",
      all(t_ok[i]["available"] and t_ok[i]["stage"] == "preview" for i in PAIR) and all(t_lid[i]["available"] is False and t_lid[i]["why"] == "gate" for i in PAIR)
      and all(t_bar[i]["available"] is False and t_bar[i]["why"] == "bar_pupil" for i in PAIR), {k: (v["available"], v["why"]) for k, v in t_bar.items()})
check("a version 1 seal (no sealed gate value) holds the hard styles back with why reseal, never a guess", all(t_v1[i]["available"] is False and t_v1[i]["why"] == "reseal" for i in PAIR))
check("one style asked for eyes that cannot take it is 422 style_unavailable with the tile's own why (gate, reseal): the state a batch reports as a tile",
      getattr(e_gate, "status", None) == 422 and e_gate.body["why"] == "gate" and e_reseal.body["why"] == "reseal" and e_gate.body["style"] == "duo.kiss_collision", (e_gate, e_reseal))
# WP10 review: the collision engine refuses a bar pupil in EVERY design (it raises NotOffered), but the tile list named the infinity designs only: Kiss, the Trio, the
# Family and the Chain showed a tile that could not be drawn. Every style of the family, at every eye count it takes, says bar_pupil for a set with a bar on any eye.
RND_P, BAR_P = dict(GOOD, pupil={"cls": "round"}), dict(GOOD, pupil={"cls": "bar"})
bar_rows = {}
for style_b, counts_b in (("duo.collision_infinity", (2,)), ("duo.clean", (2,)), ("duo.kiss_collision", (2,)), ("grp.collision", (3, 4, 5, 6, 7, 8)), ("grp.chain", (3, 4, 5, 6))):
    for n_b in counts_b:
        bar_rows[(style_b, n_b)] = tuple(CT.why_unavailable(style_b, n_b, recs_b, admin=True)
                                         for recs_b in ([RND_P] * (n_b - 1) + [BAR_P], [BAR_P] + [RND_P] * (n_b - 1), [RND_P] * n_b))
check("a bar pupil on any eye of the set refuses every design of the collision family at every eye count it takes (Infinity, Clean Infinity, Kiss, the Trio, the Family of four to eight, the Chain): why bar_pupil, "
      "on the first eye or the last; round pupils leave them available",
      all(v == ("bar_pupil", "bar_pupil", None) for v in bar_rows.values()) and len(bar_rows) == 13, {k: v for k, v in bar_rows.items() if v != ("bar_pupil", "bar_pupil", None)})
A_B3 = sealed("blue_round", 560)
with Show("grp.collision"):
    t_bar3 = {t["id"]: t for t in comp({"sealed": [A_B3, sealed("green_round", 560), sealed("dark_brown_bar", 560)], "styles": []})["tiles"]}
    t_bar4 = {t["id"]: t for t in comp({"sealed": [sealed("dark_brown_bar", 560), A_B3, sealed("green_round", 560), A_B3], "styles": []})["tiles"]}
    t_rnd3 = {t["id"]: t for t in comp({"sealed": [A_B3, sealed("green_round", 560), A_B3], "styles": []})["tiles"]}
check("through the endpoint: the Family Colours tile of three eyes (the Trio) and of four (the Family) with a bar pupil among the eyes says why bar_pupil, and is available for round ones",
      t_bar3["grp.collision"]["available"] is False and t_bar3["grp.collision"]["why"] == "bar_pupil" and t_bar4["grp.collision"]["available"] is False
      and t_bar4["grp.collision"]["why"] == "bar_pupil" and t_rnd3["grp.collision"]["available"] is True, (t_bar3["grp.collision"], t_bar4["grp.collision"]))
with Show("duo.kiss_collision"):
    e_bar_one = raised(lambda: comp({"sealed": [S1_560, sealed("dark_brown_bar", 560)], "style": "duo.kiss_collision"}))
check("Kiss asked alone for a pair with a bar pupil is 422 style_unavailable with why bar_pupil and the sentence of the pupil, as a tile of a batch would say it",
      getattr(e_bar_one, "status", None) == 422 and e_bar_one.body["why"] == "bar_pupil" and e_bar_one.body["error"] == CMP.WORDS["bar_pupil"]["en"], getattr(e_bar_one, "body", e_bar_one))


# ============================================================================================ 4. a batch
section("4. a batch: one call, the tile order, a tile alone against the tile in a batch (IE7), the cost guard, the slot, the daily ceiling")
SIX = list(SINGLES) + ["celestial_gold"]                  # five styles of the engine and one legacy tile: six tiles in one call
with Show(*SINGLES):
    t0 = time.time()
    r_b = comp({"sealed": S1, "styles": SIX, "pad": 1.12})
    t_six = time.time() - t0
need_six = CMP._need(SIX, 1, 480)[0]
info(f"six tiles in one call: {t_six:.1f} s here, the plan's estimate at the slow factor {CO.slow_factor()}: {need_six:.1f} s (SP: 7.8 s warm at x1.6)")
ids_b = [t["id"] for t in r_b["tiles"]]
check("a batch makes the tiles asked for at 480 px in one call, in the server's order (the pick first, then the tile order); the tiles not asked for carry no image",
      r_b["batch"] is True and r_b["size"] == 480 and ids_b[0] == r_b["pick"]["id"] and all((t["id"] in SIX) == ("image" in t) for t in r_b["tiles"])
      and all(img_of(t).size == (480, 480) and t["width"] == t["height"] == 480 for t in r_b["tiles"] if "image" in t) and sum(1 for t in r_b["tiles"] if "image" in t) == 6, ids_b)
SP_SIX_TILES_S = 7.8             # SPIKE 3.2: six single tiles in one call, warm, at the slow factor 1.6 (a real instance); this machine is a quiet core's equal or faster, and shared with other work
check("six tiles in one call take no more than the spike's figure for six single tiles on a real instance (7.8 s warm at x1.6): a wall time here, on a machine that is not slower than the baseline and is often shared; "
      "the plan's own estimate for the batch (the cost table at the slow factor, printed above) is what the guard uses",
      t_six <= SP_SIX_TILES_S and r_b["timing"]["total_ms"] / 1000.0 <= SP_SIX_TILES_S, (t_six, need_six))
alone = {}
with Show(*SINGLES):
    for s in SINGLES:
        alone[s] = tile_of(comp({"sealed": S1, "styles": [s]}), s)["image"]
    bad_pairs = []
    for x, y in itertools.permutations(SINGLES, 2):
        if tile_of(comp({"sealed": S1, "styles": [y, x]}), x)["image"] != alone[x]:
            bad_pairs.append((x, y))
check("a tile does not depend on the others of its call: the bytes of tile X alone are the bytes of X in any batch with any other style, before or after it, for every pair of the five styles (IE7), and in the batch of six",
      not bad_pairs and all(tile_of(r_b, s)["image"] == alone[s] for s in SINGLES), bad_pairs[:4])
iris_s = C.Iris(P.unseal(S1[0]), "x", max_side=2048, eye_id=P.unseal_full(S1[0])[1]["eye_id"])
meta_s = P.unseal_full(S1[0])[1]
direct_ok, direct_bad = True, []
with Show(*SINGLES):
    for s in SINGLES:
        req_s = CMP._request({"styles": [s], "lang": "en"})
        spec_s = CMP._spec(s, 1, [C.Iris(P.unseal(S1[0]), "y", max_side=2048, eye_id=meta_s["eye_id"])], [meta_s], req_s, "1:1", "single", {})
        direct = ST.watermarked(ST.preview([C.Iris(P.unseal(S1[0]), "y", max_side=2048, eye_id=meta_s["eye_id"])], spec_s, size=480), "en")
        if L.pil_to_b64(direct, "JPEG", 90) != alone[s]:
            direct_bad.append(s)
check("... and the tile in a batch is the picture a fresh eye and a plain preview() make of the same spec at 480 px (the batch is only the same work done once)", not direct_bad, direct_bad)
with mock.patch.object(CO, "slow_factor", lambda: 30.0), Show(*SINGLES):
    e_cost = raised(lambda: comp({"sealed": S1, "styles": list(SINGLES)}))
    k_fit = e_cost.body["max"] if getattr(e_cost, "status", None) == 422 else None
    r_fit = comp({"sealed": S1, "styles": list(SINGLES)[:k_fit]}) if k_fit else None
check("a batch whose estimate passes 40 s is refused before a pixel is drawn: 422 too_many_styles with max, the number of styles that still fit, and that many pass the guard",
      getattr(e_cost, "status", None) == 422 and e_cost.body["reason"] == "too_many_styles" and isinstance(k_fit, int) and 0 < k_fit < 5 and r_fit is not None and r_fit["batch"] is True
      and e_cost.body["error"] == CMP.WORDS["too_many_styles"]["en"], getattr(e_cost, "body", e_cost))
e_eight = raised(lambda: comp({"sealed": S1, "styles": ["solo.%d" % i for i in range(CMP.TILES_MAX + 1)]}))
check("more than TILES_MAX styles in one list is 422 too_many_styles {max: TILES_MAX} (before any style is looked at)",
      getattr(e_eight, "status", None) == 422 and e_eight.body["max"] == CMP.TILES_MAX, e_eight)
# the heavy render slot: one at a time per instance (IE6), the wait counts, the answer is 503 busy_retry with a back-off
ready, release = threading.Event(), threading.Event()


def holder(est_mb, est_s):
    with GD.slot(est_mb=est_mb, est_s=est_s, wait=0):
        ready.set()
        release.wait(60)


def with_holder(est_mb, est_s, fn):
    ready.clear()
    release.clear()
    th = threading.Thread(target=holder, args=(est_mb, est_s), daemon=True)
    th.start()
    ready.wait(10)
    try:
        return fn()
    finally:
        release.set()
        th.join(10)


with Show(*SINGLES), mock.patch.object(GD, "WAIT_S", 0.2):
    e_cpu = with_holder(100, 60.0, lambda: raised(lambda: comp({"sealed": S1, "styles": list(SINGLES)})))
    e_mem = with_holder(1400, 1.0, lambda: raised(lambda: comp({"sealed": S1, "styles": ["solo.clean"]})))
    with mock.patch.object(CMP, "_need", lambda *a, **k: (5.0, 300.0)):
        e_one = with_holder(100, 60.0, lambda: raised(lambda: comp({"sealed": S1, "style": "solo.gold"})))
    r_after = comp({"sealed": S1, "styles": ["solo.clean"]})
check("while another heavy render holds the CPU slot of the instance, a batch waits the guard's wait and then is 503 busy_retry (retry true, a back-off of 2 to 20 s from the holder's own estimate); so is a request for memory that does not fit; so is one heavy preview",
      all(getattr(e, "status", None) == 503 and e.body["reason"] == "busy_retry" and e.body["retry"] is True and 2 <= e.body["retry_after"] <= 20 for e in (e_cpu, e_mem, e_one))
      and e_cpu.body["error"] == CMP.WORDS["busy_retry"]["en"], [getattr(e, "body", e) for e in (e_cpu, e_mem, e_one)])
check("... and once the holder is done the same request is made; the guard holds nothing afterwards", r_after["batch"] and GD.state() == {"mb": 0.0, "heavy": 0, "running": 0}, GD.state())
with Show(*SINGLES), mock.patch.object(ST, "tiles", side_effect=RuntimeError("boom")):
    e_boom = raised(lambda: comp({"sealed": S1, "styles": ["solo.clean", "solo.gold"]}))
check("a render that raises gives the slot back (both guards are released in a finally): the error is the render's own and the guard is empty",
      isinstance(e_boom, RuntimeError) and GD.state() == {"mb": 0.0, "heavy": 0, "running": 0}, (e_boom, GD.state()))
with Show(*SINGLES), mock.patch.object(L, "time_left", lambda default=L.BUDGET: 2.0), mock.patch.object(ST, "tiles", side_effect=AssertionError("rendered")), \
        mock.patch.object(ST, "preview", side_effect=AssertionError("rendered")):
    e_late = [raised(lambda: comp({"sealed": S1, "styles": list(SINGLES)})), raised(lambda: comp({"sealed": S1, "style": "solo.powder"}))]
check("with too little time left in the call neither a batch nor one preview is started: 503 busy_retry before any work", all(getattr(e, "status", None) == 503 and e.body["reason"] == "busy_retry" for e in e_late), e_late)
os.environ["SNAPEYES_TILES_DAY_MAX"] = "3"
CMP._DAY.update(day="", tiles=0)
with Show(*SINGLES):
    r_d1 = comp({"sealed": S1, "styles": ["solo.clean", "solo.gold"]})
    e_day = raised(lambda: comp({"sealed": S1, "styles": ["solo.clean", "solo.gold"]}))
    r_d2 = comp({"sealed": S1, "style": "solo.gold"})
    r_d3 = comp({"sealed": S1, "styles": ["solo.clean"]})
    e_day2 = raised(lambda: comp({"sealed": S1, "styles": ["solo.clean"]}))
    r_none = comp({"sealed": S1, "styles": []})
del os.environ["SNAPEYES_TILES_DAY_MAX"]
check("this instance's daily ceiling of tiles: a batch that does not fit is 503 tiles_paused (retry true, a back-off of 60 s to 1 hour: the time to 00:00 UTC), nothing is charged for it; one preview and the tile list are not tiles",
      r_d1["batch"] and getattr(e_day, "status", None) == 503 and e_day.body["reason"] == "tiles_paused" and e_day.body["retry"] is True and 60 <= e_day.body["retry_after"] <= 3600
      and e_day.body["error"] == CMP.WORDS["tiles_paused"]["en"] and r_d2["ok"] and r_d3["batch"] and getattr(e_day2, "status", None) == 503 and r_none["batch"] and CMP._DAY["tiles"] == 3, (CMP._DAY, getattr(e_day, "body", e_day)))
check("the ceiling counts a day: a new UTC day starts again from zero", (lambda: (CMP._DAY.update(day="1999-01-01"), CMP._tiles_room(1))[1])() is True and CMP._DAY["day"] != "1999-01-01")

# ============================================================================================ 5. the replies
section("5. the replies: fields, plan8, design_used and fallback, the sizes at eight eyes, the names")
with Show("solo.gold", "solo.powder"):
    r1 = comp({"sealed": S1, "style": "solo.gold", "names": ["Anna", "Max"], "date": "2026", "lang": "en"})
    r1b = comp({"sealed": S1, "style": "solo.gold", "names": "Anna;Max", "date": "2026", "lang": "en"})
    r1c = comp({"sealed": S1, "style": "solo.gold", "names": "Completely different", "date": "1999"})
    r1d = comp({"sealed": [sealed("green_round")], "style": "solo.gold", "names": ["Anna", "Max"], "date": "2026"})
    r1w = comp({"sealed": S1, "style": "solo.gold", "format": "wallpaper"})
    r1_again = comp({"sealed": S1, "style": "solo.gold", "names": ["Anna", "Max"], "date": "2026", "lang": "en"})
eid = P.unseal_full(S1[0])[1]["eye_id"]
plan_ref = SPS.make_plan({"style": "solo.gold", "layout": "single", "eyes": 1, "opts": {}}, [{"eye_id": eid, "profile": eye("blue_round")[1].rec}])
check("a style of the engine: the reply holds the old fields, the canvas, the design drawn, the fallback (none for a single eye), the plan's identity, the engine facts, the self checks and the times",
      OLD_FIELDS <= set(r1) and NEW_FIELDS <= set(r1) and r1["canvas"] == "1:1" and r1["design_used"] == "gold" and r1["fallback"] is None and r1["opts"] == {}
      and r1["engine"] == {"v": ST.ENGINE_V, "reg": CT.registry_hash(), "pv": CT.PLATES_VERSION} and r1["selfcheck"] == {"ok": True, "failed": []}
      and {"eyes_ms", "render_ms", "total_ms"} <= set(r1["timing"]) and r1["size"] == 1024 and r1["width"] == r1["height"] == 1024, {k: r1[k] for k in r1 if k not in ("image", "tiles", "qa")})
check("plan8 is the plan's identity as the master plan makes it (steps.make_plan of the same style, layout, options and the draft's eye id and profile): checkout can recompute it and compare",
      r1["plan8"] == plan_ref["plan8"] and re.fullmatch(r"[0-9a-f]{8}", r1["plan8"]), (r1["plan8"], plan_ref["plan8"]))
check("plan8 is not moved by the customer's words or the canvas (a typo in a name never changes the plan) and is moved by the eye; the same request gives the same bytes",
      r1["plan8"] == r1c["plan8"] == r1w["plan8"] != r1d["plan8"] and r1_again["image"] == r1["image"] and r1_again["plan8"] == r1["plan8"], (r1["plan8"], r1d["plan8"]))
check("the names as a list and as the old string give the same preview (a v3 style), and the date is one line as typed", r1["image"] == r1b["image"] and r1["image"] != r1c["image"])
check("format wallpaper is the phone canvas for a style of the engine (canvas 9:19.5, taller than wide)", r1w["canvas"] == "9:19.5" and r1w["format"] == "wallpaper" and r1w["height"] > r1w["width"])
names8 = [(LT_LETTERS * 3)[:24] for _ in range(8)]
check("eight names of 24 letters (Lithuanian letters among them) are cut as the preview cuts them (60 characters of lockup, each letter the font can draw) and every name stays a name",
      all(len(n) <= 24 for n in names8) and len((" " + MIDDLE_DOT + " ").join(CMP._engine_names(names8))) <= CMP.NAMES_CUT and len(CMP._engine_names(names8)) >= 2 and CMP._engine_names("Anna;Max") == ["Anna", "Max"]
      and CMP._engine_names(None) == [] and CMP._engine_names(5) == [] and CMP._engine_names([1, "A"]) == ["A"], CMP._engine_names(names8))
eight = [sealed(n, 560) for n in ("blue_round", "green_round", "amber_slit", "dark_brown_round", "grey_round", "blue_slit", "green_bar", "dark_brown_bar")]
body8 = {"sealed": eight, "style": "supernova", "layout": "galaxy", "pad": 1.12, "names": names8}
r8 = comp(body8)
b8 = comp({"sealed": eight, "styles": ["supernova", "celestial_gold"], "pad": 1.12, "names": names8})
req_kb, rep_kb, bat_kb = len(json.dumps(body8)) / 1024.0, len(json.dumps(r8)) / 1024.0, len(json.dumps(b8)) / 1024.0
info(f"eight eyes: request {req_kb:.0f} KB (limit {CMP.MAX_TOTAL_B64 // 1024} KB), one preview reply {rep_kb:.0f} KB, a batch of two tiles {bat_kb:.0f} KB (limit 4500 KB)")
check("eight eyes: the request (eight sealed 560 px copies with their profiles) is under MAX_TOTAL_B64, the reply of one preview and of a batch of tiles under the platform's 4.5 MB, the sealed copies carry the eight profiles",
      len(json.dumps(body8)) < CMP.MAX_TOTAL_B64 and len(json.dumps(r8)) < 4_400_000 and len(json.dumps(b8)) < 4_400_000 and r8["count"] == 8 and len(r8["eyes"]) == 8
      and all(e["eye_id"] and e["cls"] for e in r8["eyes"]) and b8["batch"] and all(t["width"] == t["height"] or t["width"] > 0 for t in b8["tiles"] if "image" in t), (req_kb, rep_kb, bat_kb))
check("the old string of names, a list of names and no names all reach the eight eye legacy preview", comp(dict(body8, names="Anna;Max;Lina"))["count"] == 8 and comp(dict(body8, names=["A", "B"]))["count"] == 8 and comp(dict(body8, names=None))["count"] == 8)


# ============================================================================================ 6. multi eye plumbing on a stand in family
section("6. several eyes: what compose hands a family (a stand in for the collision family, which lands in its own package)")


class Pairs:
    """A stand in for an engine family that is not in this repository yet: records what it is asked and draws a flat picture with one disc per eye."""
    calls = []

    @staticmethod
    def resolve(spec, profiles=None):
        e = CT.engine_for(spec["style"], spec["eyes"])
        return {"family": "collision", "style": spec["style"], "design_used": e["design"], "fallback": "kiss" if (spec.get("opts") or {}).get("swap") else None,
                "layout": spec["layout"], "canvas": spec.get("canvas") or e["canvases"][0], "clean": False, "seed_key": {"style": spec["style"], "pv": CT.PLATES_VERSION},
                "seed_from": "eye_id", "plates": None, "steps": ["art"]}

    @staticmethod
    def preview(eyes, spec, size=1024, check=False, watermark=False):
        Pairs.calls.append(("preview", spec["style"], dict(spec), [e.max_side for e in eyes], size, bool(check)))
        return Pairs._draw(eyes, spec, size)

    @staticmethod
    def _draw(eyes, spec, size):
        n = len(eyes)
        W, H = size, int(size * 2 / 3)
        img = Image.new("RGB", (W, H), (30, 40, 50))
        discs = [(W * (i + 1) / (n + 1), H / 2.0, H * 0.3 if n < 4 else H * 0.15) for i in range(n)]
        return ST.Preview(img=img, discs=discs, graded=[np.zeros((16, 16, 3), np.uint8) + 100 for _ in eyes], design=CT.engine_for(spec["style"], spec["eyes"])["design"],
                          fmt=spec.get("canvas") or CT.engine_for(spec["style"], spec["eyes"])["canvases"][0], size=size, seed=1, cls="own", log={}, times={"total": 0.01},
                          selfcheck={"ok": True, "checks": {}})

    @staticmethod
    def tiles(eyes, styles, spec, size=480):
        Pairs.calls.append(("tiles", tuple(styles), dict(spec), size))
        return {s: Pairs._draw(eyes, dict(spec, style=s), size) for s in styles}


Pairs.__name__ = "_lib.styles.collision"
sys.modules["_lib.styles.collision"] = Pairs
CT.ENGINES_BUILT_EXTRA.add("collision")
A2, B2 = sealed("blue_round", 560), sealed("green_round", 560)
ids2 = [P.unseal_full(A2)[1]["eye_id"], P.unseal_full(B2)[1]["eye_id"]]
EVENTS.clear()
with Show(*PAIR, "grp.collision"):
    Pairs.calls.clear()
    r_p = comp({"sealed": [A2, B2], "style": "duo.kiss_collision", "layout": "pair", "opts": {"swap": True, "rotate": 2, "look": "echo"}, "names": ["Anna", "Max"],
                "date": "12 May 2026", "family_name": "Smith", "retake": 1, "lang": "en"})
    spec_p = Pairs.calls[0][2]
    max_side_p = Pairs.calls[0][3]
check("two eyes: the engine gets the spec of the contract: style, layout, count, no canvas of its own when none was asked (the family draws its default, as the master plan does), names as a LIST, date, family name, only the options that apply (swap for two eyes), the eyes' ids and their sealed profiles",
      spec_p["style"] == "duo.kiss_collision" and spec_p["layout"] == "pair" and spec_p["eyes"] == 2 and spec_p["canvas"] is None and r_p["canvas"] == "3:2" and spec_p["names"] == ["Anna", "Max"]
      and spec_p["date"] == "12 May 2026" and spec_p["family_name"] == "Smith" and spec_p["opts"] == {"swap": True} and spec_p["eye_ids"] == ids2
      and len(spec_p["profiles"]) == 2 and all(getattr(p, "cls", None) for p in spec_p["profiles"]), spec_p)
check("... the eyes it draws from are the working copies the registry allows (a pair: 2048 px at most) and the preview asked the family for the self checks at 1024 px",
      max_side_p == [2048, 2048] and Pairs.calls[0][5] is True)
check("the reply names the design the plan says and the fallback the plan says, the options that were applied, the layout, both eyes; plan8 is the master plan's for these eyes and options",
      r_p["design_used"] == "kiss" and r_p["fallback"] == "kiss" and r_p["opts"] == {"swap": True} and r_p["layout"] == "pair" and r_p["count"] == 2 and len(r_p["eyes"]) == 2
      and r_p["plan8"] == SPS.make_plan({"style": "duo.kiss_collision", "layout": "pair", "eyes": 2, "opts": {"swap": True}},
                                         [{"eye_id": ids2[0], "profile": P.unseal_full(A2)[1]["profile"].rec}, {"eye_id": ids2[1], "profile": P.unseal_full(B2)[1]["profile"].rec}])["plan8"], r_p)
ev_p = next(e[1] for e in EVENTS if e[0] == "compose")
check("the compose event of that preview: style, eyes, layout, size, stage (the style is Soon: preview), the set gate, the retake counter, the page's language, the fallback; tiles 1 (the request is counted once)",
      ev_p["style"] == "duo.kiss_collision" and ev_p["eyes"] == 2 and ev_p["layout"] == "pair" and ev_p["size"] == 1024 and ev_p["stage"] == "preview" and ev_p["gate"] == "ok"
      and ev_p["retake"] == 1 and ev_p["lang"] == "en" and ev_p["fallback"] == "kiss" and ev_p["tiles"] == 1 and ev_p["pick"] is False and "tile" not in ev_p, ev_p)
with Show("grp.collision"):
    Pairs.calls.clear()
    r_3 = comp({"sealed": [A2, B2, A2], "style": "grp.collision", "opts": {"swap": True, "rotate": 4}})
check("three eyes: rotate applies (taken modulo the number of eyes: 4 of 3 is 1) and swap does not (it is for two); the trio is the design the registry names for three eyes",
      Pairs.calls[0][2]["opts"] == {"rotate": 1} and r_3["opts"] == {"rotate": 1} and r_3["design_used"] == "trio" and r_3["count"] == 3, (Pairs.calls[0][2]["opts"], r_3["opts"]))
e_lay = raised(lambda: comp({"sealed": [A2, B2], "style": "duo.kiss_collision", "layout": "ring"}))
with Show(*PAIR):
    e_lay2 = raised(lambda: comp({"sealed": [A2, B2], "style": "duo.kiss_collision", "layout": "ring"}))
check("a layout the style does not take for this number of eyes is a 400, a layout it takes is accepted", isinstance(e_lay2, L.ClientError) and getattr(e_lay, "status", None) == 422)
# a batch of pair styles: the same spec for all: the family's tiles(); a layout only one of them takes: its own spec, drawn one by one
EVENTS.clear()
with Show(*PAIR):
    Pairs.calls.clear()
    b_p = comp({"sealed": [A2, B2], "styles": ["duo.kiss_collision", "duo.collision_infinity"], "names": ["Anna", "Max"]})
    same_calls = list(Pairs.calls)
    old_layouts = CT.STYLES["duo.clean"]["layouts"]
    CT.STYLES["duo.clean"]["layouts"] = {"2": ["pair", "diag"]}
    try:
        Pairs.calls.clear()
        b_d = comp({"sealed": [A2, B2], "styles": ["duo.kiss_collision", "duo.clean"], "layout": "diag"})
        diff_calls = list(Pairs.calls)
    finally:
        CT.STYLES["duo.clean"]["layouts"] = old_layouts
check("a batch of styles with one spec goes to the family's tiles() once (one eye preparation); each tile reports its layout, canvas, design, fallback and plan8 and the tiles are all at 480 px",
      [c[0] for c in same_calls] == ["tiles"] and same_calls[0][1] == ("duo.kiss_collision", "duo.collision_infinity") and same_calls[0][3] == 480
      and all(t["width"] == 480 and t["layout"] == "pair" and t["canvas"] == "3:2" and t["design_used"] in ("kiss", "infinity") and re.fullmatch(r"[0-9a-f]{8}", t["plan8"]) for t in b_p["tiles"] if "image" in t), same_calls)
check("... and when the styles differ in what they are asked (a layout only one takes: the others keep their default), the family draws them one by one on the same eyes, each with its own spec",
      sorted(c[0] for c in diff_calls) == ["preview", "preview"] and {c[1]: c[2]["layout"] for c in diff_calls} == {"duo.kiss_collision": "pair", "duo.clean": "diag"}, [(c[0], c[1]) for c in diff_calls])
ev_b = [e[1] for e in EVENTS if e[0] == "compose"]
check("the events of a batch: one per tile, each flagged tile with its style, stage, eyes and gate; the request is counted once (only the first carries tiles, the number of tiles made); a tile has its own time",
      len(ev_b) == 4 and all(e.get("tile") is True for e in ev_b) and [e.get("tiles") for e in ev_b] == [2, None, 2, None] and all(e["eyes"] == 2 and e["stage"] == "preview" and e["gate"] == "ok" for e in ev_b)
      and all(set(E.build("compose", e)) >= {"style", "eyes", "tile", "stage", "gate", "size", "lang"} for e in ev_b), ev_b[:2])
sys.modules.pop("_lib.styles.collision", None)
CT.ENGINES_BUILT_EXTRA.discard("collision")

# ============================================================================================ 6b. what the engine refuses, a render's own bug, what the ceiling counts
section("6b. the engine's own refusal of a bar pupil the profile did not show (the real collision family), a TypeError inside a render, a daily ceiling that counts pictures")
real_recs = CMP._recs


def lying_recs(metas):
    """The sealed profiles as they would be if the page's measurement had called a bar pupil round (the engine measures the pixels again)."""
    return [dict(r, pupil={"cls": "round"}) if r else r for r in real_recs(metas)]


BAR_PAIR = [S1_560, sealed("dark_brown_bar", 560)]
KISS_PICK = {"stage": "live", "pick": ["own", "dark_brown", "grey"]}            # Kiss as the recommended tile of a pair, to see the pick follow a refusal
EVENTS.clear()
CMP._DAY.update(day=CMP._utc_day(), tiles=0)
with mock.patch.dict(CT.STYLES["duo.kiss_collision"], KISS_PICK), mock.patch.object(CMP, "_recs", lying_recs):
    cat_before = CT.tile_list(2, lying_recs([P.unseal_full(s)[1] for s in BAR_PAIR]))
    e_eng1 = raised(lambda: comp({"sealed": BAR_PAIR, "style": "duo.kiss_collision"}))
    day_after_one = CMP._DAY["tiles"]
    r_eng = comp({"sealed": BAR_PAIR, "styles": ["duo.kiss_collision", "supernova"]})
    ev_eng = [e[1] for e in EVENTS if e[0] == "compose"]
rows_eng = {t["id"]: t for t in r_eng["tiles"]}
info(f"Kiss was the pick before the engine looked: {cat_before['pick']}; after: {r_eng['pick']}; the day's count {CMP._DAY['tiles']} (one legacy tile made, the refused Kiss tile charged back)")
check("one style whose engine refuses a bar pupil that the sealed profile did not show is 422 style_unavailable (why bar_pupil, the style, the pupil sentence), not a 400 'unreadable image'; one preview is not a tile",
      getattr(e_eng1, "status", None) == 422 and e_eng1.body["why"] == "bar_pupil" and e_eng1.body["style"] == "duo.kiss_collision" and e_eng1.body["error"] == CMP.WORDS["bar_pupil"]["en"]
      and day_after_one == 0, getattr(e_eng1, "body", e_eng1))
check("in a batch the refused style is a tile that says so (available false, why bar_pupil, no image, not the pick) and the other tile of the batch is still made",
      r_eng["batch"] is True and rows_eng["duo.kiss_collision"]["available"] is False and rows_eng["duo.kiss_collision"]["why"] == "bar_pupil" and "image" not in rows_eng["duo.kiss_collision"]
      and rows_eng["duo.kiss_collision"]["pick"] is False and "image" in rows_eng["supernova"] and rows_eng["supernova"]["width"] == 480, rows_eng["duo.kiss_collision"])
pick_after = r_eng["pick"]
flags_after = [t["id"] for t in r_eng["tiles"] if t["pick"]]
check("the recommended tile follows the refusal: Kiss was the pick of the profile's tile list; after the engine refused it the pick is another tile the customer can buy, or none, and the refused tile is never it; "
      "at most one tile is flagged, it is the pick and it is the first",
      cat_before["pick"] == "duo.kiss_collision" and "duo.kiss_collision" not in flags_after and (flags_after == [] if pick_after is None else
                                                                                                     (flags_after == [pick_after["id"]] and r_eng["tiles"][0]["id"] == pick_after["id"] and rows_eng[pick_after["id"]]["available"])),
      (cat_before["pick"], pick_after, flags_after))
check("the ceiling keeps what was drawn: the batch asked for two tiles, one was refused by the engine and one made, the day's count is 1; the events are one tile (the made one)",
      CMP._DAY["tiles"] == 1 and len(ev_eng) == 1 and ev_eng[0]["style"] == "supernova" and ev_eng[0]["tiles"] == 1, (CMP._DAY, ev_eng))
# a TypeError inside a render is the render's bug: seen as such, and the picture is not drawn a second time
with Show("solo.gold"), mock.patch.object(ST, "preview", side_effect=TypeError("a bug inside a render")) as m_te:
    e_te = raised(lambda: comp({"sealed": S1, "style": "solo.gold"}))


class FamCheck:
    preview = staticmethod(lambda eyes, spec, size=1024, check=False: None)


class FamPlain:
    preview = staticmethod(lambda eyes, spec, size=1024: None)


class FamKw:
    preview = staticmethod(lambda eyes, spec, size=1024, **kw: None)


def takes(fam):
    with mock.patch.object(ST, "family", lambda name: fam):
        return CMP._takes_check("solo.gold", 1)


check("a TypeError raised inside a family's render is not swallowed and is not answered by drawing the picture again: it is the render's own error and preview() was called once",
      isinstance(e_te, TypeError) and m_te.call_count == 1, (e_te, m_te.call_count))
check("whether a family takes the check keyword is read from its signature: a check parameter or any keywords yes, a preview with neither no; the three real families all take it",
      takes(FamCheck) is True and takes(FamKw) is True and takes(FamPlain) is False
      and all(CMP._takes_check(s, n_) is True for s, n_ in (("solo.gold", 1), ("duo.kiss_collision", 2), ("solo.universe", 1))), (takes(FamCheck), takes(FamKw), takes(FamPlain)))
# the daily ceiling counts the pictures made, not the requests tried
CMP._DAY.update(day=CMP._utc_day(), tiles=0)
with Show(*SINGLES), mock.patch.object(GD, "WAIT_S", 0.2):
    e_busy = with_holder(100, 60.0, lambda: raised(lambda: comp({"sealed": S1, "styles": list(SINGLES)})))
n_busy = CMP._DAY["tiles"]
with Show(*SINGLES), mock.patch.object(ST, "tiles", side_effect=RuntimeError("boom")):
    e_fail = raised(lambda: comp({"sealed": S1, "styles": ["solo.clean", "solo.gold"]}))
n_fail = CMP._DAY["tiles"]
with Show(*SINGLES):
    r_two = comp({"sealed": S1, "styles": ["solo.clean", "solo.gold"]})
n_two = CMP._DAY["tiles"]
CMP._tiles_refund(5, "1999-01-01")
check("a batch that was answered 503 busy_retry or that failed before a tile was drawn costs the day's ceiling nothing (it used to charge the whole batch first): 0 and 0; a batch that is made costs its tiles: 2",
      getattr(e_busy, "status", None) == 503 and e_busy.body["reason"] == "busy_retry" and n_busy == 0 and isinstance(e_fail, RuntimeError) and n_fail == 0 and r_two["batch"] and n_two == 2
      and CMP._DAY["tiles"] == 2 and GD.state() == {"mb": 0.0, "heavy": 0, "running": 0}, (n_busy, n_fail, n_two, CMP._DAY))

# ============================================================================================ 7. the watermark
section("7. the watermark: every tile on every disc, outside the discs the legacy one, the overlay anchored to the iris, the aligned median attack (I14)")
ACCENT = ST.WATERMARK_ACCENT
SIDE = 256
YY, XX = np.mgrid[0:SIDE, 0:SIDE]
RHO = np.hypot(XX + 0.5 - SIDE / 2.0, YY + 0.5 - SIDE / 2.0) / (SIDE / 2.0)
MASK = (RHO > 0.2) & (RHO < 0.85)


def canon(img, disc, side=SIDE):
    """The iris in its own frame: the square of the disc resampled to side x side."""
    cx, cy, r = disc[:3]
    return np.asarray(img.convert("RGB").resize((side, side), Image.LANCZOS, box=(cx - r, cy - r, cx + r, cy + r)), np.float32)


def contrast(a, b):
    return float(np.abs(a - b).mean(axis=2)[MASK].mean())


iris_g = C.Iris(P.unseal(S1[0]), "g", max_side=2048, eye_id=meta_s["eye_id"])
clean_pv, spec_for = {}, {}
with Show(*SINGLES):
    for s in SINGLES:
        spec_for[s] = CMP._spec(s, 1, [iris_g], [meta_s], CMP._request({"styles": [s], "lang": "en"}), "1:1", "single", {})
        clean_pv[s] = ST.preview([iris_g], spec_for[s], size=480)
    pv_gold_1024 = ST.preview([iris_g], spec_for["solo.gold"], size=1024)
    pv_powder_45 = ST.preview([iris_g], dict(spec_for["solo.powder"], canvas="4:5"), size=480)
    pv_gold_wall = ST.preview([iris_g], dict(spec_for["solo.gold"], canvas="9:19.5"), size=480)
# every tile of the batch, on the disc: changed pixels against the clean render, at the strength of the display copy
clean_iris_pil = Image.open(io.BytesIO(eye("blue_round")[0])).convert("RGB")
disp = P.display_image(clean_iris_pil, "en")
disp_clean = clean_iris_pil.resize((800, 800), Image.LANCZOS)
disp_disc = (400.0, 400.0, 800 * L.iris_radius_frac(1.12))
disp_strength = contrast(canon(disp, disp_disc), canon(disp_clean, disp_disc))


def ring_share(new, ref, disc, lo=0.35, hi=0.95):
    H_, W_ = new.shape[:2]
    yy, xx = np.mgrid[0:H_, 0:W_]
    d = np.hypot(xx + 0.5 - disc[0], yy + 0.5 - disc[1])
    ring = (d > lo * disc[2]) & (d < hi * disc[2])
    return float((np.abs(new.astype(np.int16) - ref.astype(np.int16)).max(axis=2)[ring] > 40).mean())


rows7 = []
for s in SINGLES:
    wm_t = np.asarray(img_of(tile_of(r_b, s)), np.int16)                      # what the endpoint answered (a JPEG)
    cl_t = np.asarray(clean_pv[s].img, np.int16)
    d_t = clean_pv[s].discs[0]
    st_t = contrast(canon(ST.watermarked(clean_pv[s], "en"), d_t), canon(clean_pv[s].img, d_t))          # the overlay's strength, without the JPEG's noise
    rows7.append((s, round(ring_share(wm_t, cl_t, d_t) * 100, 1), round(st_t / disp_strength, 2)))
info("tile, % of the iris ring changed by more than 40 levels, overlay strength against the display copy's: " + str(rows7))
check("every tile of the batch is marked on its iris disc: more than 2 percent of the iris ring changed by more than 40 levels against the clean render, and the overlay is at the strength of the display copy (between 0.6 and 1.6 times)",
      all(sh > 2.0 and 0.6 <= rel <= 1.6 for _, sh, rel in rows7), rows7)
# many discs at once: a canvas with four discs, each one marked
canvas4 = Image.new("RGB", (800, 500), (24, 28, 36))
for i in range(4):
    canvas4.paste(clean_iris_pil.resize((160, 160), Image.LANCZOS), (30 + i * 190, 170))
discs4 = [(110.0 + 190 * i, 250.0, 75.0) for i in range(4)]
wm4 = P.watermark(canvas4, ACCENT, discs4, lang="en")
check("on a canvas with four discs every disc is marked (each: more than 2 percent of its ring changed by more than 40 levels), the badge is drawn once at the top",
      all(ring_share(np.asarray(wm4), np.asarray(canvas4), d) > 0.02 for d in discs4) and wm4.size == canvas4.size)
# outside the discs it is the legacy tile and badge, pixel for pixel
dia = 2.0 * 75.0
legacy4 = L._watermark(canvas4, ACCENT, 500, tile_u=min(500.0, L.WM_DISC * dia), lang="en")
yy4, xx4 = np.mgrid[0:500, 0:800]
near = np.zeros((500, 800), bool)
for cx, cy, r in discs4:
    near |= np.hypot(xx4 + 0.5 - cx, yy4 + 0.5 - cy) <= r + 6
a4, b4 = np.asarray(wm4, np.int16), np.asarray(legacy4, np.int16)
check("outside the iris discs (and their 6 px rim) the preview is pixel for pixel the legacy watermark (the canvas tile and the badge), and on the discs it is not",
      int((np.abs(a4 - b4).max(axis=2)[~near] > 0).sum()) == 0 and int((np.abs(a4 - b4).max(axis=2)[near] > 40).sum()) > 500, (int((np.abs(a4 - b4).max(axis=2)[~near] > 0).sum()), int((np.abs(a4 - b4).max(axis=2)[near] > 40).sum())))
nodisc = P.watermark(canvas4, ACCENT, [], lang="en")
check("with no disc at all it is the legacy watermark whole, and a note (the sample's label) is drawn under the badge exactly as the legacy drawing does it",
      np.array_equal(np.asarray(nodisc), np.asarray(L._watermark(canvas4, ACCENT, 500, tile_u=500.0, lang="en")))
      and np.array_equal(np.asarray(P.watermark(canvas4, ACCENT, [], lang="en", note="ai sample")), np.asarray(L._watermark(canvas4, ACCENT, 500, tile_u=500.0, note="ai sample", lang="en"))))


# the overlay is anchored to the iris: the same words, angle and phase in the disc's frame, whatever the view's size, place or sub-pixel centre
def ncc(a, b):
    a, b = a[MASK] - a[MASK].mean(), b[MASK] - b[MASK].mean()
    return float((a * b).sum() / math.sqrt(float((a * a).sum() * (b * b).sum()) + 1e-9))


def overlay_view(cx, cy, r, rot=0.0, text=None):
    text = text or L.WATERMARK_TEXT["en"][0]
    h = int(math.ceil(1.15 * r)) + 2
    box = (int(math.floor(cx - h)), int(math.floor(cy - h)), int(math.ceil(cx + h)), int(math.ceil(cy + h)))
    a = P.anchored_alpha(text, cx, cy, r, box, rot)
    full = np.zeros((int(cy + 2 * r), int(cx + 2 * r)), np.float32)
    full[box[1]:box[3], box[0]:box[2]] = a
    return canon(Image.fromarray(np.clip(full * 255, 0, 255).astype(np.uint8)).convert("RGB"), (cx, cy, r))[..., 0]


v_a, v_b, v_c = overlay_view(300.0, 250.0, 140.0), overlay_view(215.5, 190.25, 96.5), overlay_view(480.3, 411.7, 330.2)
check("the overlay of three views of different radius, place and sub-pixel centre is the same picture in the disc's own frame (normalised correlation at least 0.95 between every two)",
      min(ncc(v_a, v_b), ncc(v_a, v_c), ncc(v_b, v_c)) >= 0.95 and v_a[MASK].std() > 5, (ncc(v_a, v_b), ncc(v_a, v_c), ncc(v_b, v_c)))
v_rot = overlay_view(300.0, 250.0, 140.0, rot=30.0)
rot_ref = np.asarray(Image.fromarray(v_a.astype(np.uint8)).rotate(30.0, resample=Image.BICUBIC), np.float32)
check("a disc that carries its rotation turns the overlay with the iris: in the iris's frame it is the same overlay (a view turned by 30 degrees equals the unturned one turned by 30 degrees)",
      ncc(v_rot, rot_ref) >= 0.9 and ncc(v_rot, v_a) < 0.9, (ncc(v_rot, rot_ref), ncc(v_rot, v_a)))
v_de = overlay_view(300.0, 250.0, 140.0, text=L.WATERMARK_TEXT["de"][0])
check("the words are the page's language's (the German overlay is another picture than the English one, the tile's first word being the same) and the canonical overlays kept are at most four",
      ncc(v_a, v_de) < 0.97 and len(P._CANON) <= 4, (ncc(v_a, v_de), len(P._CANON)))
# the aligned median attack: every view of one eye the page can obtain, aligned on the disc, per pixel median
views_new, clean_views = [], []
for s in SINGLES:
    d = clean_pv[s].discs[0]
    views_new.append(canon(ST.watermarked(clean_pv[s], "en"), d))
    clean_views.append(canon(clean_pv[s].img, d))
for pvx in (pv_powder_45, pv_gold_wall, pv_gold_1024):
    d = pvx.discs[0]
    views_new.append(canon(ST.watermarked(pvx, "en"), d))
    clean_views.append(canon(pvx.img, d))
views_new.append(canon(disp, disp_disc))
clean_views.append(canon(disp_clean, disp_disc))


def old_display(clean, lang="en"):
    """The display copy as it was before the overlay was anchored to the iris: the tile across the whole square at 3.5 times its strength."""
    side = 800
    im = clean.convert("RGB").resize((side, side), Image.LANCZOS)
    alpha = L._watermark_layer(side, side, side * 1.0, L.WATERMARK_TEXT[lang][0]).getchannel("A").point(lambda v: min(255, int(round(v * L.WATERMARK_IRIS))))
    out = im.convert("RGBA")
    zero = Image.new("L", (side, side), 0)
    shade = Image.new("L", (side, side), 0)
    shade.paste(alpha.point(lambda v: int(round(v * L.WATERMARK_IRIS_SHADOW))), (1, 1))
    out = Image.alpha_composite(out, Image.merge("RGBA", (zero, zero, zero, shade.filter(P.ImageFilter.GaussianBlur(1.0)))))
    white = Image.new("L", (side, side), 255)
    return Image.alpha_composite(out, Image.merge("RGBA", (white, white, white, alpha))).convert("RGB")


views_old = []
for s in SINGLES:
    pvx = clean_pv[s]
    views_old.append(canon(L._watermark(pvx.img, ACCENT, 480, tile_u=min(480.0, L.WM_DISC * 2 * pvx.discs[0][2]), lang="en", discs=list(pvx.discs)), pvx.discs[0]))
for pvx in (pv_powder_45, pv_gold_wall, pv_gold_1024):
    u_ = min(pvx.img.size)
    views_old.append(canon(L._watermark(pvx.img, ACCENT, u_, tile_u=min(float(u_), L.WM_DISC * 2 * pvx.discs[0][2]), lang="en", discs=list(pvx.discs)), pvx.discs[0]))
views_old.append(canon(old_display(clean_iris_pil), disp_disc))


def attack(views, cleans):
    single = float(np.mean([contrast(v, c) for v, c in zip(views, cleans)]))
    left = contrast(np.median(np.stack(views), axis=0), np.median(np.stack(cleans), axis=0))
    return left / max(single, 1e-6), single


ratio_new, single_new = attack(views_new, clean_views)
ratio_old, single_old = attack(views_old, clean_views)
info(f"aligned median over {len(views_new)} views of one iris: the overlay that survives is {ratio_new * 100:.0f} percent of a single view's (single view {single_new:.1f} levels); "
     f"with the canvas anchored overlay of before WP10: {ratio_old * 100:.0f} percent ({single_old:.1f} levels)")
check("the aligned median attack (five tiles, two more canvases, the 1024 px preview and the 800 px display copy of one eye, aligned on the disc, per pixel median): the overlay that is left is at least 60 percent of a single view's",
      ratio_new >= 0.6, (ratio_new, single_new))
check("... and the attack is real: the same views with the overlay the way it was drawn before (anchored to the canvas) leave less of it than the iris-anchored one does", ratio_old < ratio_new, (ratio_old, ratio_new))

# WP10 review: a family that reports fewer discs than it has eyes (an engine bug, never the customer's doing) used to fall back silently to the faint canvas tile, which has no
# 3.5 times strength on the iris. Now the whole canvas is marked at the iris strength.
pv_g = clean_pv["solo.gold"]


def share40(a, b):
    return float((np.abs(np.asarray(a, np.int16) - np.asarray(b, np.int16)).max(axis=2) > 40).mean())


def cells40(a, b):
    d = np.abs(np.asarray(a, np.int16) - np.asarray(b, np.int16)).max(axis=2) > 40
    h_, w_ = d.shape
    return [float(d[j * h_ // 2:(j + 1) * h_ // 2, i * w_ // 3:(i + 1) * w_ // 3].mean()) for j in range(2) for i in range(3)]


bug_pvs = {"no disc at all": ST.Preview(img=pv_g.img, discs=[], graded=pv_g.graded, fmt=pv_g.fmt, size=pv_g.size),
           "one disc for two eyes": ST.Preview(img=pv_g.img, discs=list(pv_g.discs), graded=list(pv_g.graded) * 2, fmt=pv_g.fmt, size=pv_g.size),
           "a disc of five pixels": ST.Preview(img=pv_g.img, discs=[(40.0, 40.0, 5.0)], graded=pv_g.graded, fmt=pv_g.fmt, size=pv_g.size),
           "a disc that is not a number": ST.Preview(img=pv_g.img, discs=[(float("nan"), 10.0, 100.0)], graded=pv_g.graded, fmt=pv_g.fmt, size=pv_g.size)}
with contextlib.redirect_stdout(io.StringIO()):
    wm_bug = {k: ST.watermarked(v, "en") for k, v in bug_pvs.items()}
faint = P.watermark(pv_g.img, ACCENT, [], lang="en")
rows_bug = {k: (round(share40(v, pv_g.img) * 100, 1), round(min(cells40(v, pv_g.img)) * 100, 1)) for k, v in wm_bug.items()}
info(f"a family that reports too few discs: % of the canvas changed by more than 40 levels (and the weakest sixth): {rows_bug}; the faint canvas tile alone: {share40(faint, pv_g.img) * 100:.1f}")
check("a Preview with fewer markable discs than eyes (none, one for two, a disc of five pixels, a disc that is not a number) is marked over the whole canvas at the iris strength: at least 2 percent of every sixth of the canvas "
      "changed by more than 40 levels, three times the faint canvas tile's share or more",
      all(c >= 1.5 and s >= 2.0 and s >= 3 * share40(faint, pv_g.img) * 100 for s, c in rows_bug.values()), rows_bug)
check("a picture whose discs are all there is marked as before, byte for byte (the guard changes nothing for a family that reports one disc per eye), with the eye count given or taken from the graded frames; "
      "a Preview that says nothing of its eyes (no graded frame) is not checked and keeps the legacy mark when it has no disc",
      np.array_equal(np.asarray(ST.watermarked(pv_g, "en")), np.asarray(P.watermark(pv_g.img, ACCENT, list(pv_g.discs), lang="en")))
      and np.array_equal(np.asarray(ST.watermarked(pv_g, "en", n_eyes=1)), np.asarray(ST.watermarked(pv_g, "en")))
      and np.array_equal(np.asarray(ST.watermarked(ST.Preview(img=pv_g.img, discs=[]), "en")), np.asarray(faint)))
pv_g1024 = ST.Preview(img=pv_gold_1024.img, discs=[], graded=pv_gold_1024.graded, fmt=pv_gold_1024.fmt, size=1024, design="gold", log={}, times={"total": 0.0})
with Show("solo.gold"), mock.patch.object(ST, "preview", lambda eyes, spec, size=1024, **kw: pv_g1024):
    r_nodisc = comp({"sealed": S1, "style": "solo.gold"})
check("through the endpoint: a family that reports no disc still answers a picture that is marked over its whole canvas (compose hands the number of eyes to the watermark)",
      share40(img_of(r_nodisc), pv_gold_1024.img) >= 0.02 and min(cells40(img_of(r_nodisc), pv_gold_1024.img)) >= 0.015, (share40(img_of(r_nodisc), pv_gold_1024.img), cells40(img_of(r_nodisc), pv_gold_1024.img)))


# ============================================================================================ 8. a tile against the preview
section("8. a tile against the preview (IE7): the matter and the background outside the iris agree after resizing")


def _conv(a, k, axis):
    n = a.shape[axis] - len(k) + 1
    out = 0
    for i, w in enumerate(k):
        out = out + w * (a[i:i + n] if axis == 0 else a[:, i:i + n])
    return out


def ssim_map(a, b):
    """The structural similarity of two grey pictures (float, 0 to 255): an 11 x 11 Gaussian window of 1.5, the usual constants; the map of the valid part."""
    k = np.exp(-0.5 * (np.arange(-5, 6) / 1.5) ** 2)
    k /= k.sum()

    def g(x):
        return _conv(_conv(x, k, 0), k, 1)
    mu_a, mu_b = g(a), g(b)
    saa, sbb, sab = g(a * a) - mu_a ** 2, g(b * b) - mu_b ** 2, g(a * b) - mu_a * mu_b
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return ((2 * mu_a * mu_b + c1) * (2 * sab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (saa + sbb + c2))


def matter_ssim(pv_big, pv_small, low_pass=0.0):
    """Mean SSIM of the 1024 px preview resized to the tile's size against the tile, over the pixels outside 1.15 R of the iris (the matter and the
    background); low_pass: a Gaussian blur of that many pixels laid on both first (0: none)."""
    small = pv_small.img.convert("L")
    big = pv_big.img.convert("L").resize(small.size, Image.LANCZOS)
    if low_pass:
        small, big = (x.filter(P.ImageFilter.GaussianBlur(low_pass)) for x in (small, big))
    a, b = np.asarray(big, np.float64), np.asarray(small, np.float64)
    m = ssim_map(a, b)
    H_, W_ = a.shape
    yy, xx = np.mgrid[5:H_ - 5, 5:W_ - 5]
    cx, cy, r = pv_small.discs[0]
    out = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) > 1.15 * r
    return float(m[out].mean())


rows8 = []
with Show(*SINGLES):
    for s in SINGLES:
        big = ST.preview([iris_g], spec_for[s], size=1024)
        rows8.append((s, round(matter_ssim(big, clean_pv[s]), 4), round(matter_ssim(big, clean_pv[s], 1.5), 4)))
info("SSIM of a 480 px tile against the 1024 px preview resized, outside 1.15 R, as (style, pixel level, after a 1.5 px low pass): " + str(rows8))
check("a 480 px tile agrees with the 1024 px preview of the same style and eye: the matter and the background outside 1.15 R, the preview resized to the tile's size, have an SSIM of at least 0.97 "
      "after a 1.5 px low pass on both (IE7; the grain and the dust of one or two pixels are drawn at the size asked for, not resampled, so the raw pixel level figure, printed above, is lower for Powder Burst)",
      all(v >= 0.97 for _, _, v in rows8), rows8)
check("... and at the pixel level no style is far off either: the raw SSIM is at least 0.85 for all five", all(v >= 0.85 for _, v, _ in rows8), rows8)
iris_pairs = [(clean_pv[s].discs[0][2] / 480.0) for s in SINGLES]
big_gold = ST.preview([iris_g], spec_for["solo.gold"], size=1024)
check("the iris of the tile is the iris of the preview: inside the disc (0.85 R) the tile and the resized preview differ by less than 3 levels on average (the same graded disc, T1, at two sizes)",
      float(np.abs(canon(clean_pv["solo.gold"].img, clean_pv["solo.gold"].discs[0]) - canon(big_gold.img, big_gold.discs[0])).mean(axis=2)[MASK].mean()) < 3.0)

# ============================================================================================ 9. lab, unlock, help, events
section("9. the laboratory flag, unlock, the help beacon, the events")
EVENTS.clear()
with Show("solo.gold", stage="lab"):
    r_lab = comp({"sealed": S1, "style": "solo.gold", "lab": True}, good_key)
    b_lab = comp({"sealed": S1, "styles": ["solo.elements", "solo.gold"], "lab": True}, good_key)
    e_nolab = raised(lambda: comp({"sealed": S1, "style": "solo.gold", "lab": True}, ""))
    lab_tiles = {t["id"]: t for t in b_lab["tiles"]}
    clean_gold = ST.preview([iris_g], spec_for["solo.gold"], size=1024)
check("the owner's admin key with lab true gets the laboratory styles: a held style drawn alone and in a batch (Elements has no tile slot of its own and still gets its tile), each tile at stage lab; no key, no lab",
      r_lab["style"] == "solo.gold" and r_lab["ok"] and "image" in lab_tiles["solo.elements"] and "image" in lab_tiles["solo.gold"] and lab_tiles["solo.elements"]["stage"] == "lab"
      and lab_tiles["solo.gold"]["stage"] == "lab" and getattr(e_nolab, "status", None) == 422)
check("... and what the laboratory draws is a preview too: watermarked on the iris (no endpoint hands out a clean iris, a laboratory flag or not), and the admin's own looks are no compose event",
      ring_share(np.asarray(img_of(r_lab), np.int16), np.asarray(clean_gold.img, np.int16), clean_gold.discs[0]) > 0.02 and not [e for e in EVENTS if e[0] == "compose"], EVENTS[:2])
mint_sites = [(os.path.relpath(p, REPO), n) for p in (os.path.join(d, f) for d, _, fs in os.walk(API) for f in fs if f.endswith(".py"))
              for n, line in enumerate(read(p).splitlines(), 1) if re.search(r"mint_ticket\(\s*[\"']unlock[\"']|mint_ticket\(\s*kind\s*=\s*[\"']unlock[\"']", line)]
check("the plain unlock ticket (the one that removes the watermark of a preview) is minted by nothing in api/: only scripts/mint_unlock.py, by hand, makes one", not mint_sites, mint_sites)
tkt = L.mint_ticket("unlock")
with Show("solo.gold"):
    r_unl = comp({"sealed": S1, "style": "solo.gold", "unlock": tkt, "names": "", "date": ""})
    r_unl_bad = comp({"sealed": S1, "style": "solo.gold", "unlock": L.mint_ticket("work"), "names": "", "date": ""})
    b_unl = comp({"sealed": S1, "styles": ["solo.gold"], "unlock": tkt})
    r_nounl = comp({"sealed": S1, "style": "solo.gold", "names": "", "date": ""})
check("a valid unlock ticket (which nothing mints) is the clean render of ONE style; a ticket of another kind and no ticket leave the watermark; a batch never takes it: its tiles are the watermarked ones",
      r_unl["image"] != r_nounl["image"] and r_unl_bad["image"] == r_nounl["image"] and tile_of(b_unl, "solo.gold")["image"] == alone["solo.gold"]
      and ring_share(np.asarray(img_of(r_unl), np.int16), np.asarray(clean_gold.img, np.int16), clean_gold.discs[0]) < 0.005)
# the help beacon
EVENTS.clear()
h_ok = comp({"action": "help", "route": "manual", "eyes": 3, "why": "lid_ring_outliers", "lang": "de"})
h_bad = raised(lambda: comp({"action": "help", "route": "other"}))
h_odd = comp({"action": "help", "route": "manual", "eyes": 99, "why": "a b@c", "lang": "xx"})
check("the help beacon counts a click on the manual route (route manual, the eye count, the reason code the retake state showed, the language) and nothing else; a route that is not manual is a 400; a hostile reason becomes unknown",
      h_ok["ok"] is True and h_ok["counted"] is True and h_odd["counted"] is True and isinstance(h_bad, L.ClientError), (h_ok, h_bad))
helps = [e[1] for e in EVENTS if e[0] == "help"]
check("... the events it wrote hold codes and numbers only (E.build keeps every field), and no image, no text a person typed",
      len(helps) == 2 and helps[0]["route"] == "manual" and helps[0]["eyes"] == 3 and helps[0]["why"] == "lid_ring_outliers" and helps[0]["lang"] == "de"
      and helps[1]["why"] == "unknown" and helps[1]["eyes"] == 1 and helps[1]["lang"] == "en" and set(E.build("help", helps[0])) >= {"route", "eyes", "why", "lang"}, helps)
check("the event whitelist: the compose, help and error events keep their new fields as codes, numbers and booleans and drop anything else (a space, an @, a text where a number belongs)",
      set(E.build("compose", {"style": "solo.powder", "eyes": 2, "tile": True, "tiles": 6, "size": 480, "look": "echo", "pick": False, "fallback": "stack_contrast", "stage": "preview",
                              "retake": 1, "lang": "lt", "market": "eu", "gate": "ok"})) >= {"tile", "tiles", "size", "look", "pick", "fallback", "stage", "retake", "lang", "market", "gate"}
      and "stage" not in E.build("compose", {"stage": "has space"}) and "size" not in E.build("compose", {"size": "480"}) and "pick" not in E.build("compose", {"pick": "yes"})
      and E.build("error", {"endpoint": "compose", "class": "503", "reason": "busy_retry", "style": "solo.gold"}).get("style") == "solo.gold" and "style" not in E.build("error", {"style": "a@b"})
      and E.build("help", {"route": "manual", "eyes": 2, "why": "x"})["kind"] == "help")
agg = E.empty()
for ev_ in ({"style": "solo.radiance", "eyes": 1, "tile": True, "tiles": 2, "size": 480, "stage": "preview", "gate": "ok", "retake": 0, "lang": "en", "ms": 90},
            {"style": "solo.gold", "eyes": 1, "tile": True, "size": 480, "stage": "live", "gate": "ok", "ms": 70},
            {"style": "solo.radiance", "eyes": 1, "size": 1024, "stage": "preview", "gate": "lid_deviation", "pick": False, "retake": 1, "lang": "lt", "tiles": 1, "ms": 1500},
            {"style": "solo.gold", "eyes": 1, "size": 1024, "stage": "live", "gate": "ok", "pick": True, "retake": 3, "lang": "en", "tiles": 1, "fallback": "kiss", "look": "echo", "ms": 1200},
            {"style": "supernova", "eyes": 2, "format": "artwork", "gate": "ok"}):
    E.add(agg, E.build("compose", ev_))
E.add(agg, E.build("help", {"route": "manual", "eyes": 2, "why": "lid_ring_outliers"}))
E.add(agg, E.build("error", {"endpoint": "compose", "class": "503", "reason": "busy_retry", "style": "solo.gold"}))
check("the daily counts: tiles are counted apart from previews (compose_style, compose_eyes are the previews as before), a request once (the event that carries tiles), demand by style, eyes, stage and kind, the set gate funnel by eye count, gate and retakes, chosen against recommended",
      agg["compose_style"] == {"solo.radiance": 1, "solo.gold": 1, "supernova": 1} and agg["compose_tile_style"] == {"solo.radiance": 1, "solo.gold": 1} and agg["compose_eyes"] == {"1": 2, "2": 1}
      and agg["compose_demand"] == {"solo.radiance|1|preview|tile": 1, "solo.gold|1|live|tile": 1, "solo.radiance|1|preview|large": 1, "solo.gold|1|live|large": 1}
      and agg["compose_funnel"] == {"1|ok|0": 1, "1|lid_deviation|1": 1, "1|ok|2": 1, "2|ok|0": 1} and agg["compose_chosen"] == {"other": 1, "pick": 1}
      and agg["compose_gate"] == {"ok": 3, "lid_deviation": 1} and agg["compose_size"] == {"480": 2, "1024": 2} and agg["compose_tiles"] == {"2": 1, "1": 2}
      and agg["compose_lang"] == {"en": 2, "lt": 1} and agg["compose_fallback"] == {"solo.gold|kiss": 1} and agg["compose_look"] == {"solo.gold|echo": 1}
      and agg["help_route"] == {"manual": 1} and agg["help_why"] == {"lid_ring_outliers": 1} and agg["help_eyes"] == {"2": 1} and agg["error_style"] == {"solo.gold": 1}
      and agg["ms"]["compose_tile"] == [160, 2] and agg["ms"]["compose"] == [2700, 2], {k: v for k, v in agg.items() if k.startswith(("compose", "help", "error_style"))})
mg = E.merge(agg, agg)
check("merge adds the new tables like the old ones", mg["compose_demand"]["solo.gold|1|live|tile"] == 2 and mg["compose_funnel"]["1|ok|2"] == 2 and mg["help_route"] == {"manual": 2})
# record_many and the help ceiling, against the real writer (a local store, the clean-up said to run)
E.record, E.record_many = _real_record, _real_many
os.environ["CRON_SECRET"] = "wp10-cron-secret-0123456789"
day_dir = os.path.join(STORE, "ops", "events", time.strftime("%Y-%m-%d", time.gmtime()))
before_n = len(os.listdir(day_dir)) if os.path.isdir(day_dir) else 0
n_written = E.record_many("compose", [{"style": "solo.gold", "eyes": 1, "tile": True, "stage": "live", "size": 480, "tiles": 3}, {"style": "solo.powder", "eyes": 1, "tile": True, "stage": "preview", "size": 480},
                                      {"style": "solo.clean", "eyes": 1, "tile": True, "stage": "preview", "size": 480}])
files = sorted(os.listdir(day_dir))[before_n:] if os.path.isdir(day_dir) else []
evs = [json.load(open(os.path.join(day_dir, f), encoding="utf-8")) for f in files]
check("record_many writes the events of a batch together: all three are stored, each one with its own fields (codes and numbers), and the count it returns is the number written",
      n_written == 3 and len(evs) == 3 and {e["style"] for e in evs} == {"solo.gold", "solo.powder", "solo.clean"} and all(e["kind"] == "compose" and e["tile"] is True for e in evs)
      and sum(1 for e in evs if e.get("tiles") == 3) == 1, (n_written, evs[:1]))
E._SEEN["help"], E._SEEN["help_day"], E._SEEN["help_today"] = [], "", 0
allowed = [E._allow("help", time.time()) for _ in range(E.RATE["help"][0] + 5)]
E._SEEN["help"] = []
check("the help beacon has a small budget of its own (it needs no order): past it the events are refused, and the ordinary events' budget is untouched",
      allowed.count(True) == E.RATE["help"][0] and E._allow("compose", time.time()) is True)
os.environ.pop("CRON_SECRET", None)
E.record = lambda kind, **f: EVENTS.append((kind, dict(f))) or False
E.record_many = lambda kind, rows, **k: ([EVENTS.append((kind, dict(r))) for r in rows], len(rows))[1]

# ============================================================================================ 10. over HTTP
section("10. over HTTP: the statuses, Retry-After, the language of a refusal, the legacy page's request")
c, j, r = post("/api/compose", {"sealed": S1, "style": "supernova", "pad": 1.12, "names": "Anna;Max", "lang": "en", "title": ""})
check("the legacy page's own request (sealed, style, names, pad, lang) over HTTP: 200 and the old reply with its image", c == 200 and OLD_FIELDS <= set(j) and j["image"] == r_sealed["image"], (c, str(j)[:200]))
c, j, r = post("/api/compose", {"sealed": S1, "style": "solo.gold", "lang": "de"})
check("a held style over HTTP: 422 style_unavailable with the sentence in the page's language (German here), no Retry-After", c == 422 and j["reason"] == "style_unavailable" and j["why"] == "stage"
      and j["error"] == CMP.WORDS["stage"]["de"] and "Retry-After" not in r.headers, (c, j))
for lg in ("lt", "hu"):
    c_, j_, _ = post("/api/compose", {"sealed": S1, "style": "solo.gold", "lang": lg})
    check(f"... and in {lg}", c_ == 422 and j_["error"] == CMP.WORDS["stage"][lg])
c, j, r = post("/api/compose", {"sealed": S1, "style": "supernova", "size": 700})
check("a size that is not 1024 or 480 over HTTP: 400 with the sentence", c == 400 and j["ok"] is False and "480" in j["error"], (c, j))
c, j, r = post("/api/compose", {"sealed": S1, "style": "nope"})
check("a style that is not the registry's over HTTP: 400", c == 400 and j["error"] == "Unknown style.", (c, j))
with Show(*SINGLES), mock.patch.object(GD, "WAIT_S", 0.2):
    c503, j503, r503 = with_holder(100, 60.0, lambda: post("/api/compose", {"sealed": S1, "styles": list(SINGLES)}))
check("busy over HTTP: 503 busy_retry with retry true, the sentence, and the Retry-After header with the back-off in seconds",
      c503 == 503 and j503["reason"] == "busy_retry" and j503["retry"] is True and r503.headers.get("Retry-After") == str(j503["retry_after"]) and 2 <= j503["retry_after"] <= 20, (c503, j503, dict(r503.headers)))
os.environ["SNAPEYES_TILES_DAY_MAX"] = "1"
CMP._DAY.update(day="", tiles=0)
with Show(*SINGLES):
    c_a, _, _ = post("/api/compose", {"sealed": S1, "styles": ["solo.clean"]})
    c_b, j_b, r_b_ = post("/api/compose", {"sealed": S1, "styles": ["solo.clean"]})
del os.environ["SNAPEYES_TILES_DAY_MAX"]
check("the daily ceiling over HTTP: the second batch is 503 tiles_paused with a Retry-After of the time to midnight", c_a == 200 and c_b == 503 and j_b["reason"] == "tiles_paused" and 60 <= int(r_b_.headers.get("Retry-After")) <= 3600, (c_a, c_b, j_b))
with Show("solo.gold", stage="lab"):
    c_l, j_l, _ = post("/api/compose", {"sealed": S1, "style": "solo.gold", "lab": True}, {"Authorization": "Bearer " + good_key})
    c_w, j_w, _ = post("/api/compose", {"sealed": S1, "style": "solo.gold", "lab": True}, {"Authorization": "Bearer admin-v1.1999999999.0123456789abcdef0123456789abcdef"})
check("the lab flag over HTTP: the admin key in the Authorization header opens the laboratory (200), a wrong key does not (422)", c_l == 200 and j_l["style"] == "solo.gold" and c_w == 422, (c_l, c_w))
c, j, r = post("/api/compose", {"sealed": S1, "style": "supernova"}, {"Origin": "https://example.org"})
check("the origin gate is as it was: a foreign Origin is refused (403) before anything is looked at", c == 403, c)
check("a request that is not JSON is refused as before (415)", requests.post(BASE + "/api/compose", data="x", headers={"Content-Type": "text/plain"}, timeout=30).status_code == 415)

# ------------------------------------------------------------------------------------------
E.record, E.record_many = _real_record, _real_many
ok = sum(1 for x in RESULTS if x)
print(f"\n{ok} of {len(RESULTS)} passed", flush=True)
sys.exit(0 if ok == len(RESULTS) else 1)
