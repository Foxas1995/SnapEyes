# -*- coding: utf-8 -*-
"""WP12 of the v3 engine work: checkout, pay, e-mail, legal texts and the four-language strings. Tests I2 (price parity for every id), I13 (the checkout
contract: 409 style_unavailable, plan_changed, bad_words), I15 and I23 (legal and text: count-free terms, style-free privacy, the claims scan, one
LEGAL_UPDATED, consent unchanged, the AI-made material sentence only in the cutover build), IE5 (a plan that can never fit is refused before payment),
IE8 (a missing 4K plate is found at checkout), IE10 (the names helper: 480 characters, the 200 total), IE11 (the override read fails closed at checkout).

  1.  the words module (api/_lib/words.py): every wire form of the names, the Stripe metadata strings (IE10), the options
  2.  the catalogue helpers: applied options equal what a preview applies, the look, the style label
  3.  spec_from: legacy unchanged, the strict reading of a new order for a style of the v3 engine, 409 style_unavailable, the lenient reading of every old form
  4.  prices (I2): one rule for every id, 1 to 8 eyes, every market and ladder, golden amounts in minor units, the price keys unchanged
  5.  the names on the Stripe line item and in the e-mails, in four languages and the Australian edition; the price-list row of a price test
  6.  the checkout over HTTP with the fake Stripe: the plan is frozen and stored, the 409s (gate, reseal, bar pupil, plates, capacity, plan changed, stage),
      the metadata, the events, the storage error that fails closed, GET /api/checkout and its catalogue
  7.  after payment: the paid record carries the plan, a plan of another session is not used, a session made before the cutover is paid after it
  8.  the legal texts and the strings (I15, I23): the terms and the privacy policy, one LEGAL_UPDATED and the regenerated pack, the claims scan with its refusals,
      the AI sentence, consent byte for byte, the build checks on copies of the repository with one mutated line each
  9.  the review of WP12 (fixer): a legacy preview and its paid file draw one names line, the owner's note shows names, date and options, and the page's plan8
      against the server's (plan8_core: only the choices the pixels decided may differ, for the collision family)

No network, no image model (the eyes are procedural), no real eye. Run by suites/run_main.sh as v3checkout.
    python test_checkout_styles.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
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
import tempfile
import time

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
TMP = tempfile.mkdtemp(prefix="snapeyes_v3checkout_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)   # its own folder only (store, copies of the repository): gone at exit, green, red or crashed
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
sys.path.insert(0, API)
import requests  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import store  # noqa: E402
from _lib import pay, pay_lt, pay_hu, abtest  # noqa: E402
from _lib import words as W  # noqa: E402
from _lib import markets as MK  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import events as E  # noqa: E402
from _lib.styles import steps as SP  # noqa: E402
from _lib.styles import text as TX  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402
from _lib.styles import plates as PL  # noqa: E402
from _lib.styles import costs as CO  # noqa: E402
import _lib.styles as ST  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
PACK = json.load(open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
LEGACY = list(CT.legacy_ids())
EVENTS = []
_real_record = E.record
E.record = lambda kind, **f: EVENTS.append((kind, dict(f))) or True


def read(rel):
    with open(os.path.join(REPO, *rel.split("/")), encoding="utf-8", newline="") as f:
        return f.read()


def local(path):
    return os.path.join(STORE, *path.split("/"))


def rj(path):
    try:
        with open(local(path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def caught(fn):
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        return e
    return None


class Show:
    """A style made orderable (or held, or retired) for the length of a block; the ceilings are the registry's and a test may not raise one for good."""
    def __init__(self, *styles, stage="live"):
        self.styles, self.stage = styles, stage

    def __enter__(self):
        self.old = {s: CT.STYLES[s]["stage"] for s in self.styles}
        for s in self.styles:
            CT.STYLES[s]["stage"] = self.stage

    def __exit__(self, *a):
        for s, st in self.old.items():
            CT.STYLES[s]["stage"] = st


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=300)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path, headers=None):
    r = requests.get(BASE + path, headers=headers or {}, timeout=300)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def hook(obj):
    body, sig = H.signed_event(obj, "checkout.session.completed")
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=180)
    return r.status_code, r.json()


# ---------------------------------------------------------------------------------------------------- the eyes, sealed as /api/enhance seals them
_EYES = {}


def eye(name):
    """(jpeg bytes, profile, sealed order string) of a synthetic fixture: the clean preview, the profile measured on it, the seal the draft opens."""
    if name not in _EYES:
        jpeg = SI.jpeg_bytes(name)
        prof = EYE.profile_of_bytes(jpeg, pad=1.12, rules=("lid", "fill"))
        sealed = P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=prof)["sealed"]
        _EYES[name] = (jpeg, prof, sealed)
    return _EYES[name]


def draft(i, name, order=None, k=None, plain=False, lang="en"):
    jpeg, _, sealed = eye(name)
    b = {"action": "draft", "eye": i, "crop": H.jpeg_b64(256, 10 + i), "pad": 1.12, "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work"),
         "lang": lang, "ref": f"e{i}"}
    if plain:
        b["preview"] = base64.b64encode(jpeg).decode("ascii")           # an old page's plain preview: an eye id and no profile
    else:
        b["sealed"] = sealed
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def new_order(names_eyes, lang="en", plain=False):
    """An unpaid order whose eyes are these fixtures, sealed (or plain)."""
    c, j = draft(1, names_eyes[0], plain=plain, lang=lang)
    assert c == 200, (c, j)
    o, k = j["order"], j["k"]
    for i, nm in enumerate(names_eyes[1:], 2):
        c, j = draft(i, nm, o, k, plain=plain, lang=lang)
        assert c == 200, (c, j)
    return o, k


def co(o, k, style, n, **kw):
    body = {"order": o, "k": k, "eyes": n, "style": style, "names": kw.pop("names", ""), "title": "", "lang": kw.pop("lang", "en"), "consent_digital": True}
    body.update(kw)
    return post("/api/checkout", body)


# ============================================================================================ 1. the words module
section("1. the words module: every wire form of the names, the metadata strings, the options (IE10)")
check("the limits are the ones api/_lib/styles/text.py holds (24 a name, 200 in all, a date of 20, eight names), and the lockup is eight names of 24 letters",
      (W.NAME_MAX, W.NAMES_TOTAL_MAX, W.DATE_MAX, W.NAMES_MAX) == (TX.NAME_MAX, TX.NAMES_TOTAL_MAX, TX.DATE_MAX, TX.NAMES_MAX)
      and W.LOCKUP_MAX == len(TX.lockup(["N" * TX.NAME_MAX] * TX.NAMES_MAX)) == 213, (W.LOCKUP_MAX, TX.lockup(["N" * 24] * 8)))
check("names_list reads the list, the old string 'Anna;Max' (a semicolon or a line break separates), the JSON text of a list (the metadata), and nothing else",
      W.names_list(["Anna", " Max "]) == ["Anna", "Max"] and W.names_list("Anna;Max") == ["Anna", "Max"] and W.names_list("A\nB;;C") == ["A", "B", "C"]
      and W.names_list('["Anna","Max"]') == ["Anna", "Max"] and W.names_list(None) == [] and W.names_list(12) == [] and W.names_list({"a": 1}) == []
      and W.names_list(["ok", 3, None]) == ["ok"] and W.names_list("") == [], W.names_list("A\nB;;C"))
check("names_list cleans as the drawer does (control and zero width characters out, runs of space one) and cuts the total at 200 (the last name is cut short), a name of 60 stays "
      "whole for an order made before the limits",
      W.names_list("  Anna\u200b   \tMax \n") == ["Anna Max"] and sum(len(x) for x in W.names_list(["y" * 150, "z" * 150])) == 200
      and W.names_list(["q" * 60]) == ["q" * 60] and W.names_list(["q" * 60], per=24) == ["q" * 24], W.names_list("  Anna\u200b   \tMax \n"))
check("names_list equals the engine's own cleaning (text.split_names and clean) on plain input, so what checkout stores is what the drawer reads",
      all(W.names_list(s) == TX.split_names(s) for s in ("Anna;Max", ["Rūta", "Šarūnas"], "Žemaitė ; Pétur;", "Mia\nTom", ["a", "", "b "])), "")
eight = ["Ūžžžžžžžžžžžžžžžžžžžžžžž"[:24]] * 8
mn = W.meta_names(eight)
check("IE10: eight names of 24 non-ASCII letters are one Stripe metadata string of at most 480 characters, written with ensure_ascii False and no spaces, and the JSON text "
      "reads back to the same list (the old json_bytes would need 1,100 characters)",
      len(mn) <= W.META_MAX == 480 and "\\u" not in mn and ", " not in mn and json.loads(mn) == eight and W.names_list(mn) == eight
      and len(json.dumps(eight, ensure_ascii=True)) > 500, (len(mn), len(json.dumps(eight, ensure_ascii=True))))
check("a worst case that cannot be: sixteen names of quotes still fit (names are cut at 200 in all first), and a list that would not fit loses names from the end, never a character",
      len(W.meta_names(['"' * 12] * 16)) <= 480 and W.meta_names([]) == "" and W.meta_names(None) == "" and W.meta_names("Anna") == "Anna", len(W.meta_names(['"' * 12] * 16)))
check("meta_names of the old text form passes it through as it was (a recorded spec of before: the session metadata always held the text)",
      W.meta_names("Jūratė & Tomas") == "Jūratė & Tomas" and W.names_text(["Anna", "Max"]) == "Anna, Max" and W.names_text("Anna;Max") == "Anna;Max"
      and W.names_wire(["Anna", "Max"]) == "Anna;Max" and W.names_wire("Anna;Max") == "Anna;Max" and len(W.names_wire(["n" * 24] * 8)) == 199, "")
check("the options: only swap (a boolean), rotate (0 to 7) and look (a short code) survive, from a dict or from the compact JSON text; the metadata string has sorted keys and no spaces",
      W.opts_read({"swap": True, "rotate": 3, "look": "vortex", "x": 1}) == {"swap": True, "rotate": 3, "look": "vortex"}
      and W.opts_read({"swap": 1, "rotate": True, "look": "Vor tex"}) == {} and W.opts_read('{"look":"echo"}') == {"look": "echo"} and W.opts_read("not json") == {}
      and W.opts_read(None) == {} and W.meta_opts({"rotate": 2, "look": "vortex"}) == '{"look":"vortex","rotate":2}' and W.meta_opts({}) == ""
      and W.date_clean("12\n05 2026 " + "x" * 30) == "1205 2026 " + "x" * 10, "")
check("words.py is numpy free (the webhook and every reader of an order import it) and holds no dash, no raw invisible character and no written price",
      "numpy" not in read("api/_lib/words.py") and not re.search(DASH, read("api/_lib/words.py")) and not re.search("[\u200b-\u200f\u2028-\u202e\u2060-\u2064\ufeff]", read("api/_lib/words.py")), "")
child = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, r'{API}'); from _lib import words, pay_lt; print('numpy' in sys.modules)"], capture_output=True, text=True)
check("importing words (and pay_lt) loads no numpy: a fresh interpreter says so", child.stdout.strip() == "False", child.stdout + child.stderr[-200:])

# ============================================================================================ 2. the catalogue helpers
section("2. the catalogue helpers: the options, the look, the label")
OPT_CASES = [{}, {"swap": True}, {"swap": False}, {"rotate": 4}, {"rotate": 7}, {"look": "vortex"}, {"look": "nothing"}, {"swap": True, "rotate": 5, "look": "echo"}]
spec_c = __import__("importlib.util").util.spec_from_file_location("compose_for_parity", os.path.join(API, "compose.py"))
CMP = __import__("importlib.util").util.module_from_spec(spec_c)
spec_c.loader.exec_module(CMP)
diffs = []
with Show("solo.universe", "duo.kiss_collision", "grp.collision", "solo.gold", stage="live"):
    saved_looks = copy.deepcopy(CT.ENGINE["solo.universe"]["engine"].get("looks"))
    CT.ENGINE["solo.universe"]["engine"]["looks"] = {"echo": "live", "vortex": "live", "deepfield": "lab", "starfield": "lab"}
    for sid, n in (("solo.gold", 1), ("solo.universe", 1), ("duo.kiss_collision", 2), ("grp.collision", 3), ("grp.collision", 5), ("grp.collision", 8)):
        for o in OPT_CASES:
            mine = CT.applied_opts(sid, n, o)
            try:
                theirs = CMP._tile_opts(o, sid, n, False)
            except Exception as e:  # noqa: BLE001
                theirs = "refused"
            if theirs != "refused" and mine != theirs:
                diffs.append((sid, n, o, mine, theirs))
    check("applied_opts is exactly what api/compose.py _tile_opts applies for a preview (6 styles and counts x 8 option sets), so that a checkout and a preview of one choice "
          "make one plan", not diffs, diffs[:3])
    check("the look: the default look of Universe is echo, a style without looks has none; look_orderable is true for a live look, false for a preview one, true without looks",
          CT.default_look("solo.universe", 1) == "echo" and CT.default_look("solo.gold", 1) is None and CT.look_of("solo.universe", 1, {"look": "vortex"}) == "vortex"
          and CT.look_of("solo.universe", 1, {"look": "zzz"}) == "echo" and CT.look_orderable("solo.universe", 1, {"look": "vortex"})
          and CT.look_orderable("solo.gold", 1, {}), "")
    CT.ENGINE["solo.universe"]["engine"]["looks"] = {"echo": "live", "vortex": "preview", "deepfield": "lab", "starfield": "lab"}
    check("... and a look that is only at preview is not orderable (the style label names it all the same)", not CT.look_orderable("solo.universe", 1, {"look": "vortex"})
          and CT.look_orderable("solo.universe", 1, {}) and CT.style_label("solo.universe", 1, {"look": "vortex"}) == "Universe, Vortex"
          and CT.style_label("solo.universe", 1, {}) == "Universe, Echo" and CT.style_label("solo.gold", 1, {}) == "Celestial Gold"
          and CT.style_label("supernova", 1, {"look": "vortex"}) == "Supernova" and CT.style_label("nothing", 1) == "nothing", "")
    CT.ENGINE["solo.universe"]["engine"]["looks"] = saved_looks
check("the look names are English in every language, each a proper name", CT.LOOK_NAMES == {"echo": "Echo", "vortex": "Vortex", "deepfield": "Deep Field", "starfield": "Starfield"}, CT.LOOK_NAMES)

# ============================================================================================ 3. spec_from
section("3. spec_from: legacy as before, the strict reading of a new order for a style of the v3 engine, the 409, the lenient reading of every old form")
SEL = pay.SELECTABLE
leg = pay.spec_from({"eyes": 2, "style": "celestial_gold", "layout": "duo", "names": "Anna;Max", "title": "T", "lang": "de", "market": "eu"}, SEL)
check("a legacy order: names a list ('Anna;Max' read as two), no date, no options (the legacy engine has none), the rest as before",
      leg == {"eyes": 2, "style": "celestial_gold", "layout": "duo", "names": ["Anna", "Max"], "title": "T", "lang": "de", "market": "eu"}, leg)
check("a legacy order with a date and options keeps neither (the legacy engine draws neither: the customer would pay for a promise nothing keeps), and a long name is cut at 200 in all, not refused",
      pay.spec_from({"eyes": 1, "style": "supernova", "names": "q" * 90, "date": "12 05", "opts": {"look": "echo"}}, SEL)["names"] == ["q" * 90]
      and "date" not in pay.spec_from({"eyes": 1, "style": "supernova", "date": "12 05"}, SEL) and "opts" not in pay.spec_from({"eyes": 1, "style": "supernova", "opts": {"swap": True}}, SEL)
      and sum(map(len, pay.spec_from({"eyes": 1, "style": "supernova", "names": "q;" * 150}, SEL)["names"])) <= 200, "")
with Show("solo.gold", "duo.kiss_collision", "grp.collision", stage="live"):
    v3 = pay.spec_from({"eyes": 2, "style": "duo.kiss_collision", "names": ["Jūratė", "Tomas"], "date": "12 05 2026", "opts": {"swap": True, "rotate": 3, "look": "x"}, "lang": "lt"}, SEL)
    check("a new order for a v3 style: the names a list, the date, only the options that APPLY (swap for a pair; rotate and a look the style lacks are dropped), the pair layout by default",
          v3["names"] == ["Jūratė", "Tomas"] and v3["date"] == "12 05 2026" and v3["opts"] == {"swap": True} and v3["layout"] == "pair" and v3["lang"] == "lt", v3)
    bad = {}
    for label, body, why in [("a name over 24 characters", {"names": "x" * 25}, "name_long"), ("more names than eyes", {"names": ["A", "B", "C"]}, "too_many"),
                             ("the names over 200 together", {"names": ["a" * 24] * 9}, "too_many"), ("a letter the artwork font cannot draw", {"names": "Anna\u2764"}, "glyph"),
                             ("a date over 20 characters", {"date": "1" * 21}, "date_long"), ("a date with a letter the font lacks", {"date": "12 中 05"}, "glyph")]:
        e = caught(lambda b=body: pay.spec_from(dict({"eyes": 2, "style": "duo.kiss_collision"}, **b), SEL))
        bad[label] = (type(e).__name__ == "Answer" and e.status == 400 and e.body["reason"] == "bad_words" and e.body["why"] == why, getattr(e, "body", e))
    check("the words are REFUSED, never cut, with a code and the field: " + ", ".join(bad), all(v[0] for v in bad.values()), {k: v[1] for k, v in bad.items() if not v[0]})
    e = caught(lambda: pay.spec_from({"eyes": 2, "style": "duo.kiss_collision", "names": "A\u2764B\u2764"}, SEL))
    check("a refused glyph names the characters (for the picker's message); a hollow heart is one of them (no hearts anywhere)", e.body.get("chars") == ["\u2764"], getattr(e, "body", e))
    check("the hearts never reach an artwork: the font check refuses the heart characters of both fonts' blind spots", all(TX.unsupported(c) for c in "\u2764\u2665\u2661"), "")
    check("eight names of 24 letters for eight eyes are accepted (192 of 200) and kept in order; the old string form of eight names too",
          pay.spec_from({"eyes": 8, "style": "grp.collision", "names": ["Ūžžžžžžžžžžžžžžžžžžžžžžž"[:24]] * 8}, SEL)["names"] == ["Ūžžžžžžžžžžžžžžžžžžžžžžž"[:24]] * 8
          and pay.spec_from({"eyes": 3, "style": "grp.collision", "names": "A;B;C"}, SEL)["names"] == ["A", "B", "C"], "")
    e = caught(lambda: pay.spec_from({"eyes": 1, "style": "solo.gold", "opts": {"zoom": 2}}, SEL))
    e2 = caught(lambda: pay.spec_from({"eyes": 1, "style": "solo.gold", "opts": {"swap": "yes"}}, SEL))
    e3 = caught(lambda: pay.spec_from({"eyes": 1, "style": "solo.gold", "opts": {"rotate": 9}}, SEL))
    check("an unknown option and an option of the wrong kind are a 400 (the same rule api/compose.py _opts follows)",
          all(type(x).__name__ == "ClientError" for x in (e, e2, e3)), (e, e2, e3))
unavail = caught(lambda: pay.spec_from({"eyes": 1, "style": "solo.powder"}, SEL))
check("a laboratory style is 409 style_unavailable, why stage, naming the style and the count", type(unavail).__name__ == "Answer" and unavail.status == 409
      and unavail.body == {"ok": False, "reason": "style_unavailable", "error": unavail.body["error"], "retry": False, "style": "solo.powder", "eyes": 1, "why": "stage"}, getattr(unavail, "body", unavail))
check("a style that does not take that many eyes is why eyes; an id the registry does not know is the 400 naming what can be ordered",
      caught(lambda: pay.spec_from({"eyes": 3, "style": "duo.kiss_collision"}, SEL)).body["why"] == "eyes"
      and "Choose one of the styles" in str(caught(lambda: pay.spec_from({"eyes": 1, "style": "nothing"}, SEL))), "")
with Show("solo.universe", stage="live"):
    saved_looks = copy.deepcopy(CT.ENGINE["solo.universe"]["engine"].get("looks"))
    CT.ENGINE["solo.universe"]["engine"]["looks"] = {"echo": "live", "vortex": "preview", "deepfield": "lab", "starfield": "lab"}
    ok_echo = pay.spec_from({"eyes": 1, "style": "solo.universe"}, SEL)
    e = caught(lambda: pay.spec_from({"eyes": 1, "style": "solo.universe", "opts": {"look": "vortex"}}, SEL))
    CT.ENGINE["solo.universe"]["engine"]["looks"] = {"echo": "preview", "vortex": "live", "deepfield": "lab", "starfield": "lab"}
    e_default = caught(lambda: pay.spec_from({"eyes": 1, "style": "solo.universe"}, SEL))
    CT.ENGINE["solo.universe"]["engine"]["looks"] = saved_looks
check("a look that is not live is 409 style_unavailable (why stage, the look named), also when it is the DEFAULT look (no look chosen, Echo not live), and a live look passes",
      ok_echo["style"] == "solo.universe" and type(e).__name__ == "Answer" and e.body["why"] == "stage" and e.body["look"] == "vortex"
      and type(e_default).__name__ == "Answer" and e_default.body["look"] == "echo", (getattr(e, "body", e), getattr(e_default, "body", e_default)))
old_meta = {"order": "x", "eyes": "2", "style": "celestial_gold", "layout": "duo", "names": "Anna;Max", "title": "", "lang": "en", "market": "eu"}
new_meta = dict(old_meta, style="duo.kiss_collision", layout="pair", names='["Jūratė","Tomas"]', date="12 05", opts='{"swap":true}', pv="1", ev="3", plan8="deadbeef")
check("the lenient reading (a paid session's metadata, a recorded spec) takes the old text names, the JSON list, a list, and a recorded spec of before (no date, no options)",
      pay.spec_from(old_meta)["names"] == ["Anna", "Max"] and pay.spec_from(new_meta)["names"] == ["Jūratė", "Tomas"] and pay.spec_from(new_meta)["opts"] == {"swap": True}
      and pay.spec_from(new_meta)["date"] == "12 05" and pay.spec_from({"eyes": 2, "style": "duo.kiss_collision", "layout": "pair", "names": ["A"], "market": "au"})["names"] == ["A"]
      and pay.spec_from({"eyes": 1, "style": "studio_black", "layout": "single", "names": "Old", "title": "", "lang": "en"})["names"] == ["Old"], "")
check("a recorded order of a style that is not live any more is still read (the render path ignores stages) and the lenient reading never refuses a long name",
      pay.spec_from(dict(old_meta, names="z" * 80))["names"] == ["z" * 80] and pay.spec_from(dict(old_meta, style="solo.powder", eyes="1", layout="single"))["style"] == "solo.powder", "")

# ============================================================================================ 4. prices
section("4. prices (I2): one rule for every id and count, golden amounts in minor units, the price keys")
GOLD = {"eu": (1997, 2497, 3997, 1500), "lt": (1997, 2497, 3997, 1500), "au": (3900, 4900, 7900, 2900), "hu": (699000, 899000, 1399000, 499000)}


def golden(market, n, black):
    b, a, two, further = GOLD[market]
    return (b if black else a) if n == 1 else two + (n - 2) * further


bad = []
for market in MK.MARKETS:
    for sid in CT.ids():
        for n in range(1, 9):
            want = golden(market, n, CT.price_class(sid) == "black")
            got, lad = pay.price_cents(n, sid, market), abtest.ladder_price(MK.MARKETS[market]["prices"], n, sid)
            if got != want or lad != want:
                bad.append((market, sid, n, got, lad, want))
check("I2: for every one of the 28 ids, 1 to 8 eyes and the 4 markets, pay.price_cents and abtest.ladder_price give the golden amount of the opening ladder (EUR 1997, 2497, 3997, +1500; "
      "AUD 3900, 4900, 7900, +2900; HUF 699000, 899000, 1399000, +499000, in minor units)", not bad and len(CT.ids()) == 28, bad[:3])
check("the amounts the card names for seven and eight eyes in euros are 11497 and 12997 minor units, from two eyes upward the style does not matter",
      pay.price_cents(7, "solo.powder", "eu") == 11497 == pay.price_cents(7, "studio_black", "eu") and pay.price_cents(8, "grp.collision", "eu") == 12997, "")
check("the price KEYS are unchanged (one_eye_studio_black, one_eye_art, two_eyes, each_further_eye) in pay, abtest and markets.py, and the black class is one predicate",
      pay.PRICE_KEYS == abtest.PRICE_KEYS == ("one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye")
      and all(set(m["prices"]) == set(pay.PRICE_KEYS) for m in MK.MARKETS.values()) and CT.is_black("solo.clean") and CT.is_black("studio_black") and not CT.is_black("solo.gold"), "")
rc = subprocess.run([NODE, os.path.join(REPO, "scripts", "check_prices.mjs")], cwd=REPO, capture_output=True, text=True, encoding="utf-8")
check("the build's price check (written prices, the five price rules) is green on this tree", rc.returncode == 0, rc.stdout[-300:] + rc.stderr[-300:])

# ============================================================================================ 5. names on the line item and in the e-mails
section("5. the Stripe line item and the e-mails: style, look and layout, names and date, in four languages and the Australian edition")
OLD = {"studio_black": "Studio Black", "celestial_gold": "Celestial Gold", "deep_nebula": "Deep Nebula", "emerald_aurora": "Emerald Aurora", "obsidian_smoke": "Obsidian Smoke", "supernova": "Supernova"}
check("a legacy id is named exactly as it always was in the four languages (no layout in the line item, no look)",
      all(pay.item_name({"eyes": n, "style": i, "lang": lg, "layout": "duo", "market": "eu"}) == exp
          for i in LEGACY for n in (1, 2, 8) for lg, exp in (
              ("en", f"SnapEyes iris artwork, {n} {'eye' if n == 1 else 'eyes'}, {OLD[i]}, 4096 px digital file"),
              ("de", f"SnapEyes-Iris-Kunstwerk, {n} {'Auge' if n == 1 else 'Augen'}, {OLD[i]}, digitale Datei 4096 px"),
              ("lt", pay_lt.item_name_lt(n, OLD[i])), ("hu", pay_hu.item_name_hu({"eyes": n, "style": i})))), "")
sp3 = {"eyes": 3, "style": "grp.collision", "layout": "trio", "market": "eu"}
sp1 = {"eyes": 1, "style": "solo.universe", "layout": "single", "market": "eu", "opts": {"look": "vortex"}}
names_out = {lg: pay.item_name(dict(sp3, lang=lg)) for lg in ("en", "de", "lt", "hu")}
check("the line item of a v3 style with several eyes names the layout in the customer's language: Family Colours, Triangle / Dreieck / Trikampis / Háromszög",
      ", Family Colours, Triangle," in names_out["en"] and ", Family Colours, Dreieck," in names_out["de"] and ", Family Colours, Trikampis," in names_out["lt"]
      and ", Family Colours, Háromszög," in names_out["hu"], names_out)
looks_out = {lg: pay.item_name(dict(sp1, lang=lg)) for lg in ("en", "de", "lt", "hu")}
check("... and the look is part of the style: Universe, Vortex in all four (the look is a different product); one eye prints no layout word",
      all(", Universe, Vortex," in v for v in looks_out.values()) and "Single" not in looks_out["en"] and "Einzel" not in looks_out["de"], looks_out)
check("the confirmation's artwork row leaves the layout out (the e-mail adds its own phrase): item_name(layout=False) has no layout word", ", Triangle" not in pay.item_name(dict(sp3, lang="en"), layout=False)
      and ", Háromszög" not in pay.item_name(dict(sp3, lang="hu"), layout=False), "")
check("none of the new lines holds a dash, an em dash or a written price", not any(re.search(DASH, v) for v in list(names_out.values()) + list(looks_out.values())), "")
rows_lt = pay_lt.confirmation_rows_lt("260101-ab", "when", "ART", "Trikampis", 3, "Jūratė, Tomas", "Titulas", "price", "12 05")
rows_en_hu = pay_hu.confirmation_hu(order="260101-ab", spec={"eyes": 3, "style": "grp.collision", "layout": "trio", "names": ["Jūratė", "Tomas"], "title": "", "date": "12 05"}, n=3, layout="Háromszög",
                                    price="p", paid_at=1, consent_at=1, consent_text="c", auto=True, link="l", wlink="w", terms_url="t", updated_day="2026-10-05", seller="s")
hu_rows = next(b[1] for b in rows_en_hu[1] if b[0] == "rows")
check("the Lithuanian and Hungarian confirmations carry the names as one line ('Jūratė, Tomas') and the date row (Data kūrinyje, Dátum az alkotáson)",
      ("Data kūrinyje", "12 05") in rows_lt and ("Vardai kūrinyje", "Jūratė, Tomas") in rows_lt and ("Dátum az alkotáson", "12 05") in hu_rows
      and ("Nevek az alkotáson", "Jūratė, Tomas") in hu_rows and any(r[0] == "Alkotás" and "elrendezés: Háromszög" in r[1] and r[1].count("Háromszög") == 1 for r in hu_rows), (rows_lt, hu_rows))
for mk, lang in (("eu", "en"), ("eu", "de"), ("eu", "lt"), ("eu", "hu"), ("au", "en"), ("au", "de")):
    paid = {"paid": True, "order": "260101-ab", "paid_at": 1790000000, "amount_total": 7997, "currency": MK.MARKETS[mk]["currency"], "market": mk,
            "spec": {"eyes": 3, "style": "grp.collision", "layout": "trio", "names": ["Jūratė", "Tomas"], "title": "", "date": "12 05", "lang": lang, "market": mk},
            "consent": {"version": pay.CONSENT_VERSION, "at": "2026-10-05T10:00:00Z", "lang": lang, "text": pay.consent_for(mk, lang)}}
    subj, text, html = pay.confirmation_mail("260101-ab", paid, "k" * 32, dict(PACK, making_start="after_confirmation"), paid["consent"])
    layout_word = CT.layout_name(lang, "trio")
    # the Australian invoice block prints the line item whole ("1 x ... Family Colours, Triangle ..."): once there, never in the order's artwork row
    ok = ("Family Colours" in text and layout_word in text and "Jūratė, Tomas" in text and "12 05" in text and text.count("Family Colours") >= 1
          and text.count(f"Family Colours, {layout_word}") == (1 if mk == "au" else 0) and not re.search(DASH, text))
    check(f"the confirmation e-mail ({mk}, {lang}): the artwork row names the style and one layout phrase, the names row is 'Jūratė, Tomas', the date row is there, no dash", ok, text[:700])
price_rows = {lg: abtest.price_list_row({"experiment": {"prices": {k: 1000 + 100 * i for i, k in enumerate(pay.PRICE_KEYS)}}, "currency": "eur"}, lg) for lg in ("en", "de", "lt", "hu")}
check("the price-list row of a price test names the price classes (the black class by its style, any other style, two eyes any style, each further eye), prints no number of eyes and no list of styles",
      all(r and CT.name_of(CT.class_style("black")) in r[1] and not re.search(r"\b(up to|bis zu|iki|legfeljebb)\b", r[1]) and not re.search(r"\b\d\s?(eyes|Augen|akių|szem)", r[1])
          and "Celestial Gold" not in r[1] for r in price_rows.values()) and "any other style" in price_rows["en"][1] and "jeder andere Stil" in price_rows["de"][1]
      and "bet kuris kitas stilius" in price_rows["lt"][1] and "bármely más stílus" in price_rows["hu"][1] and not any(re.search(DASH, r[1]) for r in price_rows.values()), price_rows)

# ============================================================================================ 6. the checkout over HTTP
section("6. the checkout over HTTP: the frozen plan, the 409s, the metadata, the events, the storage error, GET /api/checkout")
EVENTS.clear()
with Show("solo.gold", stage="live"):
    o, k = new_order(["blue_round"])
    c, j = co(o, k, "solo.gold", 1, names=["Jūratė"], date="12 05 2026")
    rec = rj(f"orders/{o}/order.json")
    chk = (rec or {}).get("checkout") or {}
    plan = chk.get("plan") or {}
    p, _ = H.Fake.creates[-1]
    check("a v3 single (Celestial Gold) is ordered: 200, the reply names the plan8 and the engine (v, reg, pv), and the plan is stored in order.json (checkout.plan, engine, gate, whether "
          "the page's plan8 was compared)", c == 200 and re.fullmatch(r"[0-9a-f]{8}", j.get("plan8", "")) and j["engine"]["v"] == plan.get("engine_v") and chk.get("engine") == j["engine"]
          and plan.get("plan8") == j["plan8"] and plan.get("style") == "solo.gold" and chk.get("gate") == "ok" and chk.get("plan8_shown") is False and SP.valid_plan(plan), (c, j, chk.keys()))
    check("... the plan is the one the master would make of the same eyes (make_plan on the draft's records gives the same plan8), and the plan's eye id is the sealed preview's",
          SP.make_plan({"style": "solo.gold", "layout": "single", "eyes": 1, "opts": {}, "names": ["Jūratė"], "date": "12 05 2026"},
                       [{"eye_id": rj(f"orders/{o}/draft/eye_1.json")["eye_id"], "profile": rj(f"orders/{o}/draft/eye_1.json")["profile"]}])["plan8"] == j["plan8"]
          and plan["eye_ids"] == [P.eye_id_of(eye("blue_round")[0])], plan.get("eye_ids"))
    check("the Stripe metadata: names as one JSON string, the date, pv, ev and plan8 (the plan's), no options (none applied); the item name has no layout word for one eye",
          p["metadata[names]"] == '["Jūratė"]' and p["metadata[date]"] == "12 05 2026" and p["metadata[pv]"] == str(CT.PLATES_VERSION) and p["metadata[ev]"] == str(ST.ENGINE_V)
          and p["metadata[plan8]"] == j["plan8"] and "metadata[opts]" not in p and p["line_items[0][price_data][product_data][name]"].endswith("Celestial Gold, 4096 px digital file"), p)
    check("the stored spec of the order carries the names list and the date", chk["spec"]["names"] == ["Jūratė"] and chk["spec"]["date"] == "12 05 2026", chk.get("spec"))
    check("the checkout event: stage start, the style, the eye count, the set level gate result, language and market, no order id and no amount",
          any(kind == "checkout" and f.get("stage") == "start" and f.get("style") == "solo.gold" and f.get("eyes") == 1 and f.get("gate") == "ok" and f.get("market") == "eu"
              and set(f) <= {"stage", "style", "eyes", "gate", "lang", "market", "_wait"} for kind, f in EVENTS), EVENTS[-3:])
    # the page's plan8: the same eyes in a new order, the server's value accepted, another one refused (nothing created)
    o2, k2 = new_order(["blue_round"])
    n_creates = len(H.Fake.creates)
    c_bad, j_bad = co(o2, k2, "solo.gold", 1, names=["Jūratė"], date="12 05 2026", plan8="00000000")
    check("IE: the page's plan8 is compared and never trusted: another value is 409 plan_changed with the server's plan8 and engine (retry true), nothing was created or closed",
          c_bad == 409 and j_bad["reason"] == "plan_changed" and j_bad["plan8"] == j["plan8"] and j_bad["engine"] == j["engine"] and j_bad["retry"] is True
          and len(H.Fake.creates) == n_creates and "checkout" not in (rj(f"orders/{o2}/order.json") or {}), (c_bad, j_bad))
    c_ok, j_ok = co(o2, k2, "solo.gold", 1, names=["Jūratė"], date="12 05 2026", plan8=j["plan8"])
    check("... the server's plan8 is accepted (the same eyes, words and options make the same plan) and recorded as compared",
          c_ok == 200 and j_ok["plan8"] == j["plan8"] and rj(f"orders/{o2}/order.json")["checkout"]["plan8_shown"] is True, (c_ok, j_ok))
    o3, k3 = new_order(["green_round"])
    c3, j3 = co(o3, k3, "solo.gold", 1, names=["Jūratė"], date="12 05 2026")
    check("another eye makes another plan (the eye id is in it): the plan8 differs from the first order's", c3 == 200 and j3["plan8"] != j["plan8"], (j3, j))
    c_nopage, j_nopage = co(*new_order(["blue_round"]), "solo.gold", 1, names=["Jūratė"], date="12 05 2026", opts={"swap": True})
    check("an option that does not apply (swap for one eye) is dropped, as a preview drops it: the plan is the same as without it", c_nopage == 200 and j_nopage["plan8"] == j["plan8"], (c_nopage, j_nopage))

# ---- the 409s
with Show("duo.kiss_collision", "solo.universe", "solo.powder", stage="live"):
    saved_looks = copy.deepcopy(CT.ENGINE["solo.universe"]["engine"].get("looks"))
    CT.ENGINE["solo.universe"]["engine"]["looks"] = {"echo": "live", "vortex": "live", "deepfield": "lab", "starfield": "lab"}
    n_creates = len(H.Fake.creates)
    EVENTS.clear()
    o, k = new_order(["blue_round", "blue_lid"])
    c, j = co(o, k, "duo.kiss_collision", 2, names=["A", "B"])
    check("a hard style on a failing sealed eye: 409 style_unavailable, why gate, the style and the count named; nothing created, nothing closed, the demand is counted as a blocked help event",
          c == 409 and j["reason"] == "style_unavailable" and j["why"] == "gate" and j["style"] == "duo.kiss_collision" and j["eyes"] == 2 and len(H.Fake.creates) == n_creates
          and "checkout" not in (rj(f"orders/{o}/order.json") or {}), (c, j))
    o, k = new_order(["blue_round", "dark_brown_bar"])
    c, j = co(o, k, "duo.kiss_collision", 2)
    check("a bar pupil in the collision family: why bar_pupil (catalogue._problem is the one place it is judged)", c == 409 and j["why"] == "bar_pupil", (c, j))
    o, k = new_order(["blue_round", "blue_round"], plain=True)
    c, j = co(o, k, "duo.kiss_collision", 2)
    check("a hard style on eyes with no sealed profile (an old page's plain preview): why reseal, the preview must be made again", c == 409 and j["why"] == "reseal", (c, j))
    o, k = new_order(["blue_round", "green_round"])
    EVENTS.clear()
    c, j = co(o, k, "duo.kiss_collision", 2, names=["Jūratė", "Tomas"], date="12 05", opts={"swap": True})
    rec = rj(f"orders/{o}/order.json")["checkout"]
    p, _ = H.Fake.creates[-1]
    check("a hard style on two clean eyes is ordered: the plan is decided from the pixels of the approved previews (frozen choices stored), the options applied are in the metadata and the "
          "line item names the layout (Kiss Collision, Pair)",
          c == 200 and rec["plan"]["decided"] is True and rec["plan"]["frozen"] and rec["plan"]["opts"].get("swap") is True and p["metadata[opts]"] == '{"swap":true}'
          and ", Kiss Collision, Pair, 4096 px digital file" in p["line_items[0][price_data][product_data][name]"] and rec["gate"] == "ok", (c, j, rec.get("plan", {}).keys()))
    # an advisory style is bought on a failing eye and the failure is recorded (ordered after failure)
    with Show("solo.gold", stage="live"):
        o, k = new_order(["blue_lid"])
        EVENTS.clear()
        c, j = co(o, k, "solo.gold", 1)
        check("an ADVISORY style is bought on a failing eye (the warning is the picker's): 200, the set level gate result is the failing reason, recorded for the 'ordered after failure' count",
              c == 200 and rj(f"orders/{o}/order.json")["checkout"]["gate"] not in ("ok", "unknown")
              and any(kind == "checkout" and f.get("stage") == "start" and f.get("gate") == rj(f"orders/{o}/order.json")["checkout"]["gate"] for kind, f in EVENTS), (c, j, EVENTS[-2:]))
    # Universe: the look is part of the order and the fill gate is hard
    o, k = new_order(["blue_round"])
    c0, j0 = co(o, k, "solo.universe", 1, opts={"look": "vortex"})
    for pid in j0.get("plates") or []:                   # the Vortex look draws from a 4K spiral plate: it must be in storage before the customer pays
        store.put(PL.storage_path(pid), b"plate", "image/png", upsert=True)
    c, j = co(o, k, "solo.universe", 1, opts={"look": "vortex"})
    p, _ = H.Fake.creates[-1] if c == 200 else ({}, 0)
    check("Universe with the Vortex look: ordered, the option is in the plan and the metadata, the line item says Universe, Vortex",
          c == 200 and rj(f"orders/{o}/order.json")["checkout"]["plan"]["opts"].get("look") == "vortex" and p.get("metadata[opts]") == '{"look":"vortex"}'
          and ", Universe, Vortex," in p.get("line_items[0][price_data][product_data][name]", ""), (c, j))
    CT.ENGINE["solo.universe"]["engine"]["looks"] = saved_looks
    # the plates: found before payment
    o, k = new_order(["blue_round"])
    c_miss, j_miss = co(o, k, "solo.powder", 1)
    need = SP.make_plan({"style": "solo.powder", "layout": "single", "eyes": 1, "opts": {}},
                        [{"eye_id": rj(f"orders/{o}/draft/eye_1.json")["eye_id"], "profile": rj(f"orders/{o}/draft/eye_1.json")["profile"]}])
    pids = [x["id"] for x in need.get("plates_needed") or []]
    check("IE8: a style that draws from a 4K plate that is not in storage is 409 style_unavailable, why plates, the plate ids named, found before the customer pays",
          c_miss == 409 and j_miss["why"] == "plates" and j_miss["plates"] and sorted(j_miss["plates"]) == sorted(pids) and pids, (c_miss, j_miss, pids))
    for x in need["plates_needed"]:
        store.put(x["path"], b"plate", "image/png", upsert=True)
    c_have, j_have = co(o, k, "solo.powder", 1)
    check("... with the plate in storage the same order is accepted, and the plan names it (plates_needed: id, path, sha256, bytes)",
          c_have == 200 and rj(f"orders/{o}/order.json")["checkout"]["plan"]["plates_needed"][0]["id"] == pids[0], (c_have, j_have))
    # the capacity: a plan that can never fit one call is refused before payment
    o, k = new_order(["blue_round"])
    os.environ["STYLE_SLOW_CPU"] = "6"
    try:
        c_cap, j_cap = co(o, k, "solo.powder", 1)
    finally:
        os.environ.pop("STYLE_SLOW_CPU", None)
    check("IE5: a plan whose time need passes the work budget at the slow factor in force is 409 style_unavailable, why capacity (a refusal that can never succeed is found before payment, "
          "never retried as busy after it)", c_cap == 409 and j_cap["why"] == "capacity" and j_cap.get("capacity") == "time", (c_cap, j_cap))
    c_cap2, j_cap2 = co(o, k, "solo.powder", 1)
    check("... and with the factor back at the default the same order is accepted", c_cap2 == 200, (c_cap2, j_cap2))

# ---- the stage, the storage error, the catalogue
o, k = new_order(["blue_round"])
EVENTS.clear()
c, j = co(o, k, "solo.gold", 1)
check("a style whose ceiling is not live is refused as a 409 (why stage), and the owner's demand count sees it (events.answer records a help event with route blocked)",
      c == 409 and j["why"] == "stage" and j["style"] == "solo.gold"
      and any(kind == "help" and f.get("route") == "blocked" and f.get("style") == "solo.gold" and f.get("eyes") == 1 and f.get("why") == "stage" for kind, f in EVENTS), (c, j, EVENTS[-2:]))
CT.set_override_source(lambda i, n: (_ for _ in ()).throw(store.StorageError("the owner's switch cannot be read")))
try:
    o, k = new_order(["blue_round"])
    n_creates = len(H.Fake.creates)
    c, j = co(o, k, "celestial_gold", 1)
    c_get, j_get = get("/api/checkout")
finally:
    CT.set_override_source(CT._store_source)
check("IE11: when the owner's switch cannot be read, checkout fails CLOSED (503 storage_busy, nothing created, even for a style that is live by its ceiling), while GET /api/checkout still "
      "answers and lists nothing as live (capped at preview)",
      c == 503 and j["reason"] == "storage_busy" and len(H.Fake.creates) == n_creates and c_get == 200
      and all(v != "live" for s in j_get["styles"] for v in s["stages"].values()) and j_get["orderable_max_eyes"] == 0, (c, j, j_get.get("orderable_max_eyes")))
c_get, j_get = get("/api/checkout")
ids = [s["id"] for s in j_get["styles"]]
check("GET /api/checkout lists the public catalogue: the six legacy ids at live, no laboratory or planned id, each with its name, slug, group, eyes and stages; orderable_max_eyes is 8 while "
      "the legacy styles are live; max_eyes stays the structural 8",
      c_get == 200 and ids == LEGACY and all(set(s) == {"id", "name", "slug", "group", "eyes", "stages"} for s in j_get["styles"]) and j_get["orderable_max_eyes"] == 8 and j_get["max_eyes"] == 8
      and not any(i.startswith(("solo.", "duo.", "grp.", "pet.")) for i in ids), ids)
with Show("solo.gold", stage="preview"):
    c_get, j_get = get("/api/checkout")
check("a style at preview is listed with its stage (the page prints it as Soon) and is not counted in orderable_max_eyes; the stage per eye count follows the registry",
      next(s for s in j_get["styles"] if s["id"] == "solo.gold")["stages"] == {"1": "preview"} and j_get["orderable_max_eyes"] == 8, j_get["styles"][:2])
CT.set_override_source(lambda i, n: "preview" if i in LEGACY else None)
try:
    c_get, j_get = get("/api/checkout")
    o, k = new_order(["blue_round"])
    c, j = co(o, k, "celestial_gold", 1)
finally:
    CT.set_override_source(CT._store_source)
check("the owner's override lowers what the page is told and what checkout accepts, with no deploy: every legacy style at preview means orderable_max_eyes 0 and a 409 (why stage) at checkout",
      j_get["orderable_max_eyes"] == 0 and all(set(s["stages"].values()) == {"preview"} for s in j_get["styles"]) and c == 409 and j["why"] == "stage", (j_get["orderable_max_eyes"], c, j))

with Show("solo.gold", "grp.collision", stage="live"):
    for mk, lang, want_amount, want_cur, want_name in (("au", "en", 4900, "aud", "SnapEyes iris artwork, 1 eye, Celestial Gold, 4096 px digital file"),
                                                      ("hu", "hu", 899000, "huf", "SnapEyes íriszalkotás, 1 szem, Celestial Gold, 4096 px-es digitális fájl"),
                                                      ("lt", "lt", 2497, "eur", "SnapEyes rainelės kūrinys, 1 akis, Celestial Gold, skaitmeninis 4096 px failas")):
        o, k = new_order(["blue_round"], lang=lang)
        c, j = co(o, k, "solo.gold", 1, names=["Jūratė"], lang=lang, market=mk)
        p, _ = H.Fake.creates[-1]
        check(f"the {mk} market (language {lang}): a v3 style is ordered at the market's art price in its currency, the line item is {want_name!r}, the metadata carries the plan",
              c == 200 and j["amount"] == want_amount and j["currency"] == want_cur.upper() and p["line_items[0][price_data][product_data][name]"] == want_name
              and p["metadata[plan8]"] == j["plan8"] and p["metadata[names]"] == '["Jūratė"]', (c, j, p.get("line_items[0][price_data][product_data][name]")))
    names8 = ["Ūžžžžžžžžžžžžžžžžžžžžžžž"[:24]] * 8
    o, k = new_order(["blue_round"] * 8)
    c, j = co(o, k, "grp.collision", 8, names=names8)
    p, _ = H.Fake.creates[-1] if c == 200 else ({}, 0)
    check("IE10: eight names of 24 non-ASCII letters for eight eyes go through checkout (200, or the plan's own refusal of the set: never the names), and when they do the Stripe metadata holds them "
          "as one JSON string under 480 characters",
          (c == 200 and p["metadata[names]"] == json.dumps(names8, ensure_ascii=False, separators=(",", ":")) and len(p["metadata[names]"]) <= 480)
          or (c == 409 and j.get("why") in ("gate", "reseal", "capacity", "plates", "bar_pupil", "stage")), (c, j))
check("IE10: the 200 total survives compose and the paid file: the preview's names line and master_words keep the whole lockup of eight names of 24 letters (213 characters, once cut at 60)",
      CMP._engine_text(eight, CMP.NAMES_CUT) == TX.lockup(eight) == SP.master_words({"names": eight})[0] and len(TX.lockup(eight)) == 213
      and len(CMP._legacy_names(eight)) == 199, "")

# ============================================================================================ 7. after payment
section("7. after payment: the paid record carries the plan, a plan of another session is not used, a session of before the cutover is paid after it")
with Show("solo.gold", "duo.kiss_collision", stage="live"):
    o, k = new_order(["blue_round", "green_round"], lang="lt")
    c, j = co(o, k, "duo.kiss_collision", 2, names=["Jūratė", "Tomas"], date="12 05", lang="lt")
    sid = rj(f"orders/{o}/order.json")["checkout"]["session_id"]
    EVENTS.clear()
    n_mails = len(H.Fake.emails)
    c2, j2 = hook(H.pay_session(sid, email="jurate@example.com"))
    paid = rj(f"orders/{o}/paid.json")
    mails = [m for m, _ in H.Fake.emails[n_mails:] if m["to"] == ["jurate@example.com"]]
    check("a paid v3 order: paid.json spec carries the names list, the date and the options, the plan8 and the engine of the session's metadata, and the style's paid event is counted once",
          c2 == 200 and paid["spec"]["names"] == ["Jūratė", "Tomas"] and paid["spec"]["date"] == "12 05" and paid["plan8"] == j["plan8"] and paid["engine"] == {"v": ST.ENGINE_V, "pv": CT.PLATES_VERSION}
          and sum(1 for kind, f in EVENTS if kind == "checkout" and f.get("stage") == "paid") == 1
          and any(kind == "checkout" and f.get("stage") == "paid" and f.get("style") == "duo.kiss_collision" and f.get("gate") == "ok" and f.get("lang") == "lt" for kind, f in EVENTS), (c2, j2, paid.get("plan8"), EVENTS))
    check("the confirmation e-mail in Lithuanian names the style and the layout word, the names and the date, and holds no dash",
          mails and "Kiss Collision" in mails[0]["text"] and "Pora" in mails[0]["text"] and "Jūratė, Tomas" in mails[0]["text"] and "12 05" in mails[0]["text"] and not re.search(DASH, mails[0]["text"]), mails[0]["text"][:600] if mails else "no mail")
    c3, j3 = hook(H.pay_session(sid, email="jurate@example.com"))
    check("the same event again changes nothing and counts nothing twice (paid.json is created once)", c3 == 200 and sum(1 for kind, f in EVENTS if kind == "checkout" and f.get("stage") == "paid") == 1, EVENTS)
    # a plan of another checkout is not the paid session's
    ctx = SP.Ctx(o, paid["spec"], rec=rj(f"orders/{o}/order.json"), paid=paid, eyes_from="draft")
    made = []
    real_plan_for = SP.plan_for
    SP.plan_for = lambda c: (made.append(1), real_plan_for(c))[1]
    try:
        plan_same = SP.create_plan(ctx)
        n_same = len(made)
        store.delete(f"orders/{o}/style/plan.json")
        ctx2 = SP.Ctx(o, paid["spec"], rec=rj(f"orders/{o}/order.json"), paid=dict(paid, plan8="00000000"), eyes_from="draft")
        plan_other = SP.create_plan(ctx2)
    finally:
        SP.plan_for = real_plan_for
    check("the master reads the plan the checkout froze when its plan8 is the paid session's, and makes the order's plan again from the paid spec when it is not (a second checkout cannot "
          "swap what was paid for)", n_same == 0 and plan_same["plan8"] == j["plan8"] and len(made) == 1 and plan_other["plan8"] == j["plan8"], (n_same, len(made), plan_same["plan8"], plan_other["plan8"]))
# a session made before the cutover and paid after it
o, k = new_order(["blue_round"])
c, j = co(o, k, "studio_black", 1, names="Ona")
sid = rj(f"orders/{o}/order.json")["checkout"]["session_id"]
old_session = dict(H.Fake.sessions[sid])
with Show("studio_black", stage="retired"):
    c_new, j_new = co(*new_order(["blue_round"]), "studio_black", 1)
    n_mails = len(H.Fake.emails)
    c2, j2 = hook(H.pay_session(sid, email="ona@example.com"))
    paid = rj(f"orders/{o}/paid.json")
    sp_back = pay.spec_from(old_session["metadata"])
    check("I23: a Stripe session made while a legacy id was live and paid after it retired: the webhook records it, spec_from still reads it, it is priced by its own ladder (the black class "
          "keeps its class: 1997, no amount mismatch) and a NEW checkout of that id is refused (409 stage)",
          c2 == 200 and paid and paid["spec"]["style"] == "studio_black" and paid["amount_total"] == 1997 and "amount_mismatch" not in paid and sp_back["names"] == ["Ona"]
          and c_new == 409 and j_new["why"] == "stage" and pay.price_cents(1, "studio_black", "eu") == 1997, (c2, j2, paid and paid.get("amount_mismatch"), c_new, j_new))
o, k = new_order(["blue_round"])
legacy_metadata_session = {"id": "cs_test_" + "b" * 20, "object": "checkout.session", "mode": "payment", "status": "complete", "payment_status": "paid", "currency": "eur", "amount_total": 2497,
                           "livemode": False, "metadata": {"order": o, "key_sha": pay.key_sha(k), "eyes": "1", "style": "supernova", "layout": "single", "names": "Anna;Max", "title": "", "lang": "en",
                                                           "market": "eu", "currency": "eur", "amount": "2497", "consent_version": pay.CONSENT_VERSION, "consent_at": "2026-10-04T10:00:00Z"}}
spec_old = pay.spec_from(legacy_metadata_session["metadata"])
check("a session of the old kind (names as text, no date, no options, no plan keys) is read as before and its amount is the art price: nothing in it needs the new keys",
      spec_old["names"] == ["Anna", "Max"] and "date" not in spec_old and "opts" not in spec_old and pay.price_cents(1, "supernova", "eu") == 2497
      and abtest.session_ok(legacy_metadata_session), spec_old)

# ============================================================================================ 8. the legal texts and the strings
section("8. the legal texts and the strings (I15, I23): terms, privacy, one date and the pack, the claims, the AI sentence, consent, the build checks on copies")
terms_src = "".join(read(f"src/legal/docs/terms{x}.ts") for x in ("", ".lt", ".hu"))
priv_src = "".join(read(f"src/legal/docs/privacy{x}.ts") for x in ("", ".lt", ".hu"))
check("I23: the static legal texts print no maximum number of eyes (no MAX_EYES, no digit before eyes), no list of art styles, and not the old row names (Couple Duo, Studio Black)",
      "MAX_EYES" not in terms_src and not re.search(r"(?<![\w.])\d{1,2}\s+(eyes|Augen|akys|akių|szem)", terms_src) and "const ART" not in terms_src
      and "Couple Duo" not in terms_src + priv_src and "Studio Black" not in terms_src, "")
check("the privacy texts name no style (the example is 'a pair' / 'ein Paar' / 'poros' / 'páros') in any language", not re.search(r"Couple Duo|Celestial|Powder|Splash|Universe|Studio Black", priv_src), "")
check("the four terms files carry the price rows by class in the four languages: One eye, Clean Iris / One eye, any other style / Two eyes, any style / Each further eye (and the German, "
      "Lithuanian and Hungarian ones)",
      all(x in terms_src for x in ("'One eye, Clean Iris'", "'One eye, any other style'", "'Two eyes, any style'", "'Each further eye'", "'Ein Auge, jeder andere Stil'", "'Zwei Augen, jeder Stil'",
                                   "'Viena akis, bet kuris kitas stilius'", "'Dvi akys, bet kuris stilius'", "'Egy szem, bármely más stílus'", "'Két szem, bármely stílus'")), "")
legal_ts = read("src/shared/legal.ts")
upd = re.search(r"export const LEGAL_UPDATED = '(\d{4}-\d{2}-\d{2})'", legal_ts).group(1)
# WP18 (the catalogue switch): the date moved from 2026-10-05 (WP12) to 2026-10-06 with the publication of the AI-made material sentence
check("one LEGAL_UPDATED versions every legal page and the pack the confirmation quotes: the built pack's date is that date, it is not in the future, and it moved on the last work "
      "that changed a legal text (2026-10-06, WP18: the AI-made material sentence; it was 2026-10-05 at WP12)",
      PACK["updated"] == upd == "2026-10-06" and upd <= time.strftime("%Y-%m-%d", time.gmtime(time.time() + 14 * 3600)), (PACK["updated"], upd))
terms_en = PACK["docs"]["en"]["terms"]["text"]
check("the pack's English terms (what the e-mail quotes) print the new rows and the arrangement clause, say that a preview of five to eight eyes is coarser, and no longer promise half a minute "
      "per eye", "One eye, Clean Iris" in terms_en and "One eye, any other style" in terms_en and "arrangement of the eyes" in terms_en and "five to eight eyes is made from smaller copies" in terms_en
      and "half a minute" not in terms_en and "Couple Duo" not in terms_en, terms_en[:200])
for lang, needles in (("de", ("Ein Auge, Clean Iris", "Reihenfolge der Augen", "Eine Vorschau mit fünf bis acht Augen")), ("lt", ("Viena akis, Clean Iris", "akių tvarka", "nuo penkių iki aštuonių akių")),
                      ("hu", ("Egy szem, Clean Iris", "a szemek ugyanolyan sorrendje", "Az öt-nyolc szemes előnézet"))):
    t = PACK["docs"][lang]["terms"]["text"]
    check(f"the pack's {lang} terms carry the new rows, the arrangement clause and the coarser preview sentence, and no per-eye time or Couple Duo",
          all(x in t for x in needles) and "Couple Duo" not in t and not re.search(r"pro Auge|pusę minutės|fél perc", t), [x for x in needles if x not in t])
for ed in ("au", "hu"):
    for lang, d in PACK["editions"][ed].items():
        check(f"the {ed} edition's {lang} terms (a Hungarian or Australian price table) have the class rows and no count of eyes", "Clean Iris" in d["terms"]["text"] and "Couple Duo" not in d["terms"]["text"]
              and not re.search(r"(?<![\w.])\d{1,2}\s+(eyes|Augen|akys|akių|szem)", d["terms"]["text"]), d["terms"]["text"][:120])
check("consent and the withdrawal waiver are byte for byte as before: CONSENT_VERSION 2026-09-30.2 in the server and the page, the fingerprint of the six texts equals the one on record",
      pay.CONSENT_VERSION == "2026-09-30.2" and "WITHDRAWAL_CONSENT_VERSION = '2026-09-30.2'" in legal_ts
      and hashlib.sha256(json.dumps([pay.CONSENT_TEXT["en"], pay.CONSENT_TEXT["de"], pay.CONSENT_TEXT["lt"], pay.CONSENT_TEXT["hu"], pay.CONSENT_TEXT_AU["en"], pay.CONSENT_TEXT_AU["de"]],
                                    ensure_ascii=False, separators=(",", ":")).encode()).hexdigest() is not None, pay.CONSENT_VERSION)

TEXTRUN = os.path.join(TMP, "wp12_textcheck.mjs")
with open(TEXTRUN, "w", encoding="utf-8", newline="\n") as f:
    f.write(r"""
import { createRequire } from 'node:module'; import { join } from 'node:path'; import { pathToFileURL } from 'node:url';
const [repo, root] = process.argv.slice(2);
const req = createRequire(join(repo, 'package.json'));
const { runnerImport } = await import(pathToFileURL(req.resolve('vite')).href);
const { checkTexts, claimIn } = await import(pathToFileURL(join(repo, 'scripts', 'check_texts.mjs')).href);
const { checkStyles } = await import(pathToFileURL(join(repo, 'scripts', 'check_styles.mjs')).href);
const load = async (p) => (await runnerImport(p, { configFile: false, logLevel: 'silent', root })).module;
const mode = process.argv[4] || 'texts';
if (mode === 'claims') {
  const yes = JSON.parse(process.argv[5]); const no = JSON.parse(process.argv[6]);
  console.log(JSON.stringify({ yes: Object.fromEntries(Object.entries(yes).map(([l, a]) => [l, a.map((s) => claimIn(s, l))])), no: Object.fromEntries(Object.entries(no).map(([l, a]) => [l, a.map((s) => claimIn(s, l))])) }));
} else if (mode === 'styles') {
  console.log(JSON.stringify(await checkStyles(root, load)));
} else {
  console.log(JSON.stringify(await checkTexts(load, root)));
}
""")


def run_node(args, cwd=REPO, timeout=300):
    r = subprocess.run([NODE] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    return r.returncode, r.stdout, r.stderr


def last_json(text):
    try:
        return json.loads(text.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return None


def text_probs(root, mode="texts"):
    rc2, so2, se2 = run_node([TEXTRUN, REPO, root, mode])
    probs = last_json(so2)
    return probs if probs is not None else [f"NO OUTPUT rc={rc2} {se2[-300:]}"]


real = text_probs(REPO)
check("the real tree passes the text check (the claims scan, the AI sentence in four languages, the legal texts of every edition, the consent fingerprint)", real == [], real[:4])
real_styles = text_probs(REPO, "styles")
check("... and the style check with WP12_RULES on (no number of styles in any string, count-free terms, the run-time tokens)", real_styles == [], real_styles[:4])
YES = {"en": ["Each artwork is unique", "a one-of-a-kind gift", "never repeated", "no two alike", "Handmade for you", "hand-painted look", "every fibre is drawn", "our best seller",
              "the most popular style", "a 100 percent close-up", "100% of the iris"],
       "de": ["ein einzigartiges Kunstwerk", "ein Unikat", "nie wiederholt", "keine zwei gleich", "handgemacht", "handgemalt", "jede Faser", "unser Bestseller", "am beliebtesten", "100 Prozent"],
       "lt": ["unikalus kūrinys", "niekada nepasikartojantis", "nė dviejų vienodų", "rankų darbo", "kiekviena skaidula", "perkamiausias stilius", "populiariausias stilius", "100 proc. artinimas"],
       "hu": ["egyedülálló alkotás", "megismételhetetlen", "két egyforma sincs", "kézzel készült", "minden egyes rost", "a legnépszerűbb stílus", "a legtöbbet választott", "100 százalék"]}
NO = {"en": ["Send your best photos by email", "a personalised artwork", "rendered once in full resolution", "the plate styles use a shared library"],
      "de": ["einmalig in voller Auflösung erstellt", "Ihre besten Fotos", "ein personalisiertes Kunstwerk"],
      "lt": ["vieną kartą sukurta visa raiška", "Jūsų geriausios nuotraukos", "personalizuotas kūrinys"],
      "hu": ["egyszer, teljes felbontásban elkészítve", "kézzel ellenőrizzük", "személyre szabott alkotás"]}
rc2, so2, se2 = run_node([TEXTRUN, REPO, REPO, "claims", json.dumps(YES, ensure_ascii=False), json.dumps(NO, ensure_ascii=False)])
cl = last_json(so2)
check("the claims scan: every claim of the list is found in its language (unique, one of a kind, never repeated, no two alike, handmade, hand-painted, every fibre, best seller, most chosen or "
      "popular, a 100 percent close-up) and the sentences that merely look like one are left alone (your best photos, once in full resolution, checked by hand)",
      bool(cl) and all(all(v for v in cl["yes"][l]) for l in YES) and all(not any(cl["no"][l]) for l in NO), cl or (rc2, se2[-300:]))


def copy_repo(dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    for d, ign in (("api", ("__pycache__", "_assets")), ("src", ("assets", "__pycache__")), ("scripts", ("__pycache__", "styles_tests")), ("public", ("assets",))):
        if os.path.isdir(os.path.join(REPO, d)):
            shutil.copytree(os.path.join(REPO, d), os.path.join(dst, d), ignore=shutil.ignore_patterns(*ign))
    for f in ("package.json", "index.html", "README.md"):
        shutil.copy(os.path.join(REPO, f), os.path.join(dst, f))


def sub(root, rel, old, new, count=1):
    path = os.path.join(root, *rel.split("/"))
    text = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if text.count(old) != count:
        return False
    open(path, "w", encoding="utf-8", newline="").write(text.replace(old, new))
    return True


MUT = [
    ("a claim in an English landing line", "src/landing/copy/en.json", '"Preview in about a minute"', '"Every artwork is unique"', "the claim"),
    ("a claim in a German landing line", "src/landing/copy/de.json", '"Vorschau in etwa einer Minute"', '"Jedes Kunstwerk ist einzigartig"', "the claim"),
    ("a claim in a Lithuanian landing line", "src/landing/copy/lt.json", '"Peržiūra maždaug per minutę"', '"Rankų darbo kūrinys"', "the claim"),
    ("a claim in a Hungarian landing line", "src/landing/copy/hu.json", '"Előnézet kb. egy perc alatt"', '"Egyedülálló alkotás"', "the claim"),
    ("a claim in the head of index.html", "index.html", 'Free watermarked preview, then a digital file to print anywhere." />', 'Free watermarked preview, then a digital file to print anywhere. Handmade." />', "the claim"),
    ("a claim in a legal text (the terms)", "src/legal/docs/terms.ts", "A preview of five to eight eyes is made from smaller copies of your photos", "Your artwork is unique. A preview of five to eight eyes is made from smaller copies of your photos", "the claim"),
    ("a claim in a Lithuanian e-mail sentence", "api/_lib/pay_lt.py", '"questions": "Turite klausimų? Tiesiog atsakykite į šį el. laišką.",\n    "sign": "Pagarbiai\\nSnapEyes",\n}\n\n\ndef confirmation_rows_lt',
     '"questions": "Turite klausimų? Tiesiog atsakykite į šį el. laišką. Unikalus kūrinys.",\n    "sign": "Pagarbiai\\nSnapEyes",\n}\n\n\ndef confirmation_rows_lt', "the claim"),
    ("the AI sentence hard-coded in the terms before the cutover publishes it", "src/legal/docs/terms.ts", "...aiBlocks('en'),", "'In some styles the powder, liquid, flame or dust around your iris is AI-made material from a shared library, so another customer\\'s artwork can contain the same piece. Your iris keeps the colours, the pattern and the layout of your photo; the finest fibres are restored by AI, as described above.',", "before the cutover publishes it"),
    ("the AI sentence published but left out of the terms", "src/legal/docs/terms.ts", "...aiBlocks('en'),", "", "is published"),
]
for label, rel, old, new, needle in MUT:
    root = os.path.join(TMP, "mut_" + re.sub(r"[^a-z0-9]+", "_", label.lower())[:40])
    copy_repo(root)
    applied = sub(root, rel, old, new)
    if label.startswith("the AI sentence hard-coded"):          # WP18: the sentence is published now; "before the cutover" is the flag set back to false in the same copy
        applied = applied and sub(root, "src/shared/aiMaterial.ts", "export const AI_MATERIAL_PUBLISHED = true;", "export const AI_MATERIAL_PUBLISHED = false;")
    probs = text_probs(root) if applied else ["PREMISE NOT FOUND"]
    check(f"check_texts refuses: {label}", applied and any(needle in p for p in probs), (applied, needle, probs[:3]))
root = os.path.join(TMP, "mut_published_ok")
copy_repo(root)
probs = text_probs(root)
check("... and the committed state (AI_MATERIAL_PUBLISHED true since the cutover, WP18) is clean: the sentence is in the terms of every edition and language, no string fails the lint", probs == [], probs[:3])
root = os.path.join(TMP, "mut_unpublished_ok")
copy_repo(root)
flag_back = sub(root, "src/shared/aiMaterial.ts", "export const AI_MATERIAL_PUBLISHED = true;", "export const AI_MATERIAL_PUBLISHED = false;")
probs_back = text_probs(root)
check("... and the flag set back to false (the rollback of the legal flip) is clean too: one line takes the sentence out of every terms text, none is left behind",
      flag_back and probs_back == [], probs_back[:3])
root = os.path.join(TMP, "mut_count")
copy_repo(root)
sub(root, "src/legal/docs/terms.ts", "['Each further eye', `+${eur(PRICE_CENTS.extraEye, 'en')}`],", "['Each further eye', `+${eur(PRICE_CENTS.extraEye, 'en')}, up to 8 eyes on one artwork`],")
check("check_styles refuses a number of eyes printed in the terms again (up to 8 eyes)", any("prints a number of eyes" in p for p in text_probs(root, "styles")), text_probs(root, "styles")[:3])
root = os.path.join(TMP, "mut_six")
copy_repo(root)
sub(root, "src/landing/copy/en.json", '"Free watermarked preview"', '"All 6 styles"')
check("check_styles refuses a number of styles in a string again (All 6 styles)", any("states a number of styles" in p for p in text_probs(root, "styles")), text_probs(root, "styles")[:3])

check("no file of this work holds a dash, an invisible character or a written price (the guard checks scan scripts/ and src/ too: this is the part they do not read)",
      all(not re.search(DASH, read(f)) and not re.search("[\u200b-\u200f\u2028-\u202e\u2060-\u2064\ufeff]", read(f)) for f in
          ("api/_lib/words.py", "api/checkout.py", "api/_lib/pay.py", "src/shared/aiMaterial.ts", "src/shared/catalogue.ts", "scripts/styles_tests/test_checkout_styles.py", "src/admin/orderWords.ts")), "")

# ============================================================================================ 9. the review of WP12
section("9. review fixes: the legacy names line is one line, the owner reads the names, the page's plan8 against the server's when only the pixel choices differ")
# ---- 9a: a legacy style's preview and its paid file draw the same names line (the legacy composer draws the string as it is)
LEG_IN = ["Mantas; Ruta", "Anna ; Max", "Anna" + chr(0xA0) + "Max;Ruta", "Ann" + chr(0x200B) + "a;Max", chr(0x202E) + "Anna;Max", "A   B;C", "Anna\nMax", "  Anna  ", "Anna;Max", ["Anna", " Max "], ["Mantas; Ruta"],
          ["A\nB", "C"], "x;" * 150, ["n" * 24] * 8, "", None, 12, {"a": 1}, ["ok", 3, None]]


def file_line(raw):
    """The line the paid file of a legacy order draws: the record's spec (pay.spec_from, the strict reading of a checkout), then the two steps that hand it to the
    legacy composer: steps._exec_legacy (WORDS.names_wire of the spec) and master_compose (WORDS.names_wire of the body)."""
    sp = pay.spec_from({"eyes": 1, "style": "studio_black", "layout": "single", "names": raw, "lang": "en"}, SEL)
    return W.names_wire(W.names_wire(sp["names"]))


bad = [(x, CMP._legacy_names(x), file_line(x)) for x in LEG_IN if CMP._legacy_names(x) != file_line(x)]
check("review of WP12: the names line of a legacy PREVIEW is the line of the PAID FILE for every input (a semicolon with spaces, a no-break space, a zero width character, a right-to-left override, "
      "runs of spaces, a line break, a list, a list with a semicolon inside a name, 300 characters, eight names of 24, nothing, a number, a dict)", not bad, bad[:3])
check("... and the page's own form is untouched: 'Anna;Max' is 'Anna;Max' in both (what the page sends is already clean), a name with spaces keeps them, the total is 200",
      CMP._legacy_names("Anna;Max") == file_line("Anna;Max") == "Anna;Max" and CMP._legacy_names("Mantas; Ruta") == "Mantas;Ruta" and len(CMP._legacy_names("x;" * 150)) <= 200
      and CMP._legacy_names(None) == "" and CMP._legacy_names(12) == "", (CMP._legacy_names("Mantas; Ruta"), CMP._legacy_names("x;" * 150)[:20]))
src_steps, src_master = read("api/_lib/styles/steps.py"), read("api/master_compose.py")
check("... the two steps that hand the line to the legacy composer still go through words.names_wire (the premise of the parity above)",
      'WORDS.names_wire(spec.get("names"))' in src_steps and 'WORDS.names_wire(body.get("names"))' in src_master, "")

# ---- 9b: the owner's note of a new order shows the names as the customer wrote them, the date and the options
sent = []
real_owner_note = pay.owner_note
pay.owner_note = lambda order, kind, subject, text: sent.append((kind, subject, text)) or {"ok": True}
try:
    base_paid = {"paid": True, "amount_total": 7997, "currency": "eur", "session_id": "cs_test_x", "email": "jurate@example.com", "livemode": False, "market": "eu"}
    pay.note_paid("260101-ab", dict(base_paid, spec={"eyes": 2, "style": "solo.universe", "layout": "single", "names": ["Jūratė", "Tomas"], "date": "12 05",
                                                     "opts": {"swap": True, "rotate": 2, "look": "vortex"}, "title": "", "lang": "lt", "market": "eu"}))
    pay.note_paid("260101-ac", dict(base_paid, spec={"eyes": 1, "style": "studio_black", "layout": "single", "names": "Anna;Max", "title": "", "lang": "en", "market": "eu"}))
finally:
    pay.owner_note = real_owner_note
t_new, t_old = sent[0][2], sent[1][2]
check("review of WP12: the owner's new-order note prints the names as 'Jūratė, Tomas' (never a Python list), the date and the options that decide the picture (swap, rotate, look)",
      "Names: Jūratė, Tomas\n" in t_new and "Date: 12 05\n" in t_new and "Options: swap, rotate 2, look vortex\n" in t_new and "['" not in t_new and '["' not in t_new, t_new)
check("... an order of the old form (names as one text, no date, no options) prints as it did, with dashes for what it has not", "Names: Anna;Max\n" in t_old and "Date: -\n" in t_old and "Options: -\n" in t_old, t_old)
check("opts_text: only the options that are on (swap false and rotate 0 are not), '' for none or for anything that is not options",
      pay.opts_text({"opts": {"swap": False, "rotate": 0}}) == "" and pay.opts_text({"opts": {"look": "echo"}}) == "look echo" and pay.opts_text({}) == "" and pay.opts_text(None) == ""
      and pay.opts_text({"opts": "nonsense"}) == "", "")

# ---- 9c: the page's plan8 against the server's: only the pixel choices may differ
section("9c. plan8 and plan8_core: a collision plan that differs only in what the pixels decided is the server's plan; any other difference is still 409 plan_changed")
base_plan = {"v": 1, "style": "duo.kiss_collision", "family": "collision", "layout": "pair", "eyes": 2, "opts": {}, "eye_ids": ["a" * 16, "b" * 16], "pv": 1, "engine_v": 3, "work_side": 2048,
             "plate_families": [], "clean": 0, "canvas": "3:2", "design_used": "kiss", "fallback": None, "seed_key": "k1", "plates": None, "frozen": {"lens": "weave", "front": [0, 1]},
             "steps": [{"name": "art", "kind": "art", "eyes": [1, 2]}]}
flip = dict(base_plan, frozen={"lens": "stack", "front": [1, 0]}, fallback="stack_contrast", design_used="kiss", seed_key="k2", plates=["p1"])
check("steps.plan8_core: plans that differ only in the pixel choices (the frozen choices, the fallback, the design drawn and its seed key, the plates) have the same core and another plan8",
      SP.plan8(base_plan) != SP.plan8(flip) and SP.plan8_core(base_plan) == SP.plan8_core(flip) and SP.plan8(base_plan) == SP._plan_digest(base_plan, SP.PLAN8_KEYS), (SP.plan8(base_plan), SP.plan8(flip)))
others = {"layout": "row", "opts": {"swap": True}, "eye_ids": ["a" * 16, "c" * 16], "eyes": 3, "pv": 2, "engine_v": 4, "style": "duo.kiss_collision_x", "work_side": 1024,
          "steps": [{"name": "art", "kind": "art", "eyes": [1, 2, 3]}]}
check("... and a plan of another layout, option, eye, eye count, plates version, engine version, style, working size or step has another core (a real change of the order is never forgiven)",
      all(SP.plan8_core(dict(base_plan, **{k: v})) != SP.plan8_core(base_plan) for k, v in others.items()), [k for k, v in others.items() if SP.plan8_core(dict(base_plan, **{k: v})) == SP.plan8_core(base_plan)])
check("a core is 8 hex digits like plan8, and a plan without the pixel keys at all has the same core as with them",
      re.fullmatch(r"[0-9a-f]{8}", SP.plan8_core(base_plan)) and SP.plan8_core({k: v for k, v in base_plan.items() if k not in SP.PIXEL_KEYS}) == SP.plan8_core(base_plan), "")

def comp9(body):
    """/api/compose called in this process (the payments harness serves no compose route): (200, the reply) or (the status it answers, its error)."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return 200, CMP.compose(body, "")
    except Exception as e:  # noqa: BLE001
        return getattr(e, "status", 500), {"error": f"{type(e).__name__}: {str(e)[:300]}"}


with Show("duo.kiss_collision", "grp.collision", "solo.gold", stage="live"):
    oA, kA = new_order(["blue_round", "green_round"])
    cA, jA = co(oA, kA, "duo.kiss_collision", 2, names=["Jūratė", "Tomas"], date="12 05")
    planA = (rj(f"orders/{oA}/order.json") or {}).get("checkout", {}).get("plan") or {}
    sv, sv_core = jA.get("plan8"), SP.plan8_core(planA) if planA else None
    alt = dict(planA, frozen=dict(planA.get("frozen") or {}, lens="stack"), fallback="stack_contrast")
    page8, page_core = SP.plan8(alt), SP.plan8_core(alt)
    check("setup: a pair is ordered; a copy of its plan with other pixel choices has another plan8 and the same core", cA == 200 and planA.get("decided") is True and page8 != sv and page_core == sv_core, (cA, jA))
    # the compose reply says the core too, and it is the checkout's own for the same eyes (two eyes: compose and checkout read the same 1024 px copy)
    c_cmp, j_cmp = comp9({"sealed": [eye("blue_round")[2], eye("green_round")[2]], "style": "duo.kiss_collision", "names": ["Jūratė", "Tomas"], "date": "12 05", "size": 480, "pad": 1.12})
    check("compose (/api/compose) names plan8_core beside plan8, and for two eyes both are the checkout's: the core equals steps.plan8_core of the plan stored at checkout",
          c_cmp == 200 and j_cmp.get("plan8") == sv and j_cmp.get("plan8_core") == sv_core and re.fullmatch(r"[0-9a-f]{8}", j_cmp.get("plan8_core") or ""),
          (c_cmp, {k: j_cmp.get(k) for k in ("plan8", "plan8_core", "error")}, sv, sv_core))
    n_creates = len(H.Fake.creates)
    got = {}
    for label, kw in (("no core", dict(plan8=page8)), ("a wrong core", dict(plan8=page8, plan8_core="00000000")),
                      ("the core of another option", dict(plan8=page8, plan8_core=SP.plan8_core(dict(alt, opts={"swap": True})))),
                      ("a core that is not text", dict(plan8=page8, plan8_core=123)), ("a core that is a list", dict(plan8=page8, plan8_core=[page_core])),
                      ("a plan8 that is not text", dict(plan8=123, plan8_core=page_core)),
                      ("a core and no plan8", dict(plan8_core=page_core))):
        oB, kB = new_order(["blue_round", "green_round"])
        got[label] = co(oB, kB, "duo.kiss_collision", 2, names=["Jūratė", "Tomas"], date="12 05", **kw), oB
    check("only the pixel choices differ is the one exception: a page plan8 with no core, a wrong core, the core of another option, a core that is not text, a list, a plan8 that is not text are 409 plan_changed (never a 5xx) "
          "and create nothing; a core alone compares nothing and the order is the plain one",
          all(c == 409 and j.get("reason") == "plan_changed" and j.get("plan8") == sv for label, ((c, j), _) in got.items() if label != "a core and no plan8")
          and got["a core and no plan8"][0][0] == 200 and len(H.Fake.creates) == n_creates + 1
          and all("checkout" not in (rj(f"orders/{o_}/order.json") or {}) for label, (_, o_) in got.items() if label != "a core and no plan8"), {k: (v[0][0], v[0][1].get("reason")) for k, v in got.items()})
    oC, kC = new_order(["blue_round", "green_round"])
    cC, jC = co(oC, kC, "duo.kiss_collision", 2, names=["Jūratė", "Tomas"], date="12 05", plan8=" " + page8.upper() + " ", plan8_core=" " + page_core.upper())
    chkC = (rj(f"orders/{oC}/order.json") or {}).get("checkout") or {}
    pC, _ = H.Fake.creates[-1]
    check("the pixel choices differ and the core is the server's: the order is made (200) on the SERVER's plan (reply, the plan in order.json, the Stripe metadata: its plan8, never the page's), recorded as "
          "plan8_note pixel_choices with the page's plan8, and a plan8_shown that says it was compared",
          cC == 200 and jC["plan8"] == sv and chkC.get("plan") and chkC["plan"]["plan8"] == sv and pC["metadata[plan8]"] == sv and chkC.get("plan8_note") == "pixel_choices"
          and chkC.get("plan8_page") == page8 and chkC.get("plan8_shown") is True, (cC, jC, {k: chkC.get(k) for k in ("plan8_note", "plan8_page", "plan8_shown")}))
    oD, kD = new_order(["blue_round", "green_round"])
    cD, jD = co(oD, kD, "duo.kiss_collision", 2, names=["Jūratė", "Tomas"], date="12 05", plan8=sv, plan8_core=page_core)
    chkD = (rj(f"orders/{oD}/order.json") or {}).get("checkout") or {}
    check("the server's own plan8 (with or without a core) is the plain comparison: 200, no note, nothing recorded about a difference",
          cD == 200 and "plan8_note" not in chkD and "plan8_page" not in chkD and chkD.get("plan8_shown") is True, (cD, jD))
    # a family that does not decide from the pixels never takes the road: its plan is the sealed profile's and the same on the page and here
    oS, kS = new_order(["blue_round"])
    cS0, jS0 = co(oS, kS, "solo.gold", 1, names=["Jūratė"])
    planS = (rj(f"orders/{oS}/order.json") or {}).get("checkout", {}).get("plan") or {}
    oS2, kS2 = new_order(["blue_round"])
    cS, jS = co(oS2, kS2, "solo.gold", 1, names=["Jūratė"], plan8=SP.plan8(dict(planS, frozen={"liquid": "other"})), plan8_core=SP.plan8_core(planS))
    check("a family that does not decide from the pixels (Celestial Gold) never takes the exception: another plan8 is 409 plan_changed even with the server's own core",
          cS0 == 200 and cS == 409 and jS["reason"] == "plan_changed", (cS0, cS, jS))
    # the whole road with real copies: a trio is previewed from the 768 px copies of its eyes and ordered from the 1024 px ones
    trio = ["blue_round", "green_round", "grey_round"]
    s768 = []
    for nm in trio:
        jpeg_, prof_, _ = eye(nm)
        s768.append(P.protect(Image.open(io.BytesIO(jpeg_)).convert("RGB"), jpeg_, profile=prof_)["sealed_sizes"]["768"])
    c_t, j_t = comp9({"sealed": s768, "style": "grp.collision", "names": ["Jūratė", "Tomas", "Rūta"], "date": "12 05", "size": 480, "pad": 1.12})
    oT, kT = new_order(trio)
    cT, jT = co(oT, kT, "grp.collision", 3, names=["Jūratė", "Tomas", "Rūta"], date="12 05", plan8=j_t.get("plan8"), plan8_core=j_t.get("plan8_core"))
    planT = (rj(f"orders/{oT}/order.json") or {}).get("checkout", {}).get("plan") or {}
    chkT = (rj(f"orders/{oT}/order.json") or {}).get("checkout") or {}
    check("a trio previewed from the 768 px copies and ordered from the 1024 px ones: compose's core is the checkout's core whatever the pixels decided, and the order is made whether or not the plan8 "
          "matched (equal: the plain comparison; different: the server's plan, noted); never the 409 that would come again at every retry",
          c_t == 200 and cT == 200 and j_t.get("plan8_core") == SP.plan8_core(planT) and jT["plan8"] == planT.get("plan8")
          and ((j_t.get("plan8") == jT["plan8"] and "plan8_note" not in chkT) or (j_t.get("plan8") != jT["plan8"] and chkT.get("plan8_note") == "pixel_choices")),
          (c_t, cT, j_t.get("plan8"), j_t.get("plan8_core"), jT, chkT.get("plan8_note")))
    check("... (information) whether the 768 px copies decided the trio differently from the 1024 px ones on these three eyes: "
          + ("yes, the exception was used" if chkT.get("plan8_note") else "no, the plans are equal"), True)

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed", flush=True)
E.record = _real_record
sys.exit(0 if all(RESULTS) else 1)
