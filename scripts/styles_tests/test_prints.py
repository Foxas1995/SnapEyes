# -*- coding: utf-8 -*-
"""Prints of the artwork (api/_lib/prints.py, merchone.py, print_offer.py, print_rates.py, print_names.py): the offer, its switch, the checkout,
the payment, the confirmation e-mail, the order at the print partner, its webhook and the daily run, the admin actions, the pages' reading.

  1.  the tables and the rules: the shipping rule (VAT, rounded up to .49 or .99) and the margins, the same numbers as the build's check and the
      page's module (node), the print file's size for every SKU (the trim, the resolution between merchOne's minimum and PRINT_DPI), a 3:2
      artwork centred with its background continued
  2.  the switch: off by default (GET /api/checkout has no prints, a print is refused 409 print_unavailable), why (not_configured, off, market,
      product, country), the admin action with its confirmation and its revision, a switch that cannot be read is off
  3.  the checkout with a print: the Stripe parameters (the second line item, the address form for the one country, the shipping rate, the
      print's note above the pay button, the metadata), order.json's print with the print box's consent, the refusals (the box, the price shown);
      a checkout without a print is the same request as before prints existed
  4.  the payment: paid.json's print with the address Stripe collected, print.json and the index, the amount checked with the print, a price
      test's session with a print, an address in another country held for the owner; the confirmation e-mail's rows and section (en and lt)
  5.  the order at merchOne (a stub): not before the artwork is delivered or while it waits for the owner's look, the payload (external id, test
      order, the name and address, our e-mail, the billing, the SKU, the signed link of the print file), the print file's size, once only (a
      second step, a lost reply adopted from merchOne's refusal of the same external id), a refusal held as failed with the owner told and the
      admin's retry, a refunded or withdrawn order cancelled, merchOne not configured waits
  6.  the webhook and the daily run: the token, an event read back from merchOne, the shipping e-mail once with its tracking link, a lost
      webhook caught by the daily run, a cancellation at merchOne, the admin's cancel
  7.  the server's own making sends the print right after the ready e-mail (maker._step), the order page's status shows it, health says it
  8.  the legal texts: the terms, the privacy policy and the withdrawal page of the EU edition (every language) and the Hungarian edition's terms
      name the prints, the partner and the countries; the Australian and the US editions do not; the consent version and its print box

No network (merchOne and Stripe are local stubs), no image model, no real eye. Run by suites/run_main.sh as v3prints (in the world before the
catalogue switch: a legacy style is the vehicle of the checkout, as in the payment suites).
    python test_prints.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

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
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_", "MERCHONE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_WORLD"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3prints_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ["STYLE_PLATE_CACHE"] = os.path.join(TMP, "cache")


# ---------------------------------------------------------------------------------------------------- the merchOne stub
class MO:
    orders = {}            # id -> {payload, status, shipments}
    creates = []           # payloads, in order
    fail_create = []       # HTTP codes for the next create calls (500: busy; 422: a refusal)
    lose_reply = 0         # the next n creates are MADE but answered 503 (a reply lost on the way)
    gets = []
    deletes = []
    n = 31186000
    refuse_delete = False  # merchOne's 405 "Order cannot be cancelled" (the first seconds, or after its hold time)


USER, KEY = "stub-user-01", "stub-key-0123456789abcdef"


class MOHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj=None):
        data = b"" if obj is None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)

    def _ok(self):
        want = "Basic " + base64.b64encode(f"{USER}:{KEY}".encode()).decode()
        if self.headers.get("Authorization") != want:
            self._send(401, {"message": "Unauthorized"})
            return False
        return True

    def do_POST(self):
        n = int(self.headers.get("content-length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        if not self._ok():
            return
        path = urlsplit(self.path).path
        if path == "/api/v1/orders":
            MO.creates.append(body)
            if MO.fail_create:
                code = MO.fail_create.pop(0)
                return self._send(code, {"message": "The product sku is invalid.", "errors": {"items.0.product_sku": ["invalid"]}} if code == 422 else {"message": "busy"})
            for oid, o in MO.orders.items():
                if o["payload"].get("external_id") == body.get("external_id"):
                    msg = f"This store already has a previous order with an external ID {body.get('external_id')} ({oid}) in our system."
                    return self._send(422, {"message": msg, "errors": {"external_id": [msg]}})
            MO.n += 1
            oid = f"PPO{MO.n}T"
            MO.orders[oid] = {"payload": body, "status": "PROCESSING", "shipments": []}
            if MO.lose_reply:
                MO.lose_reply -= 1
                return self._send(503, {"message": "gateway"})
            return self._send(200, {"order_id": oid})
        if path == "/api/v1/shipment/rates":
            return self._send(200, {"data": [{"type": "tracked", "cost": 6.99, "currency": "EUR"}]})
        self._send(404, {"message": "no route"})

    def do_GET(self):
        if not self._ok():
            return
        path = urlsplit(self.path).path
        m = re.fullmatch(r"/api/beta/orders/([A-Z0-9]+)", path)
        if m:
            MO.gets.append(m.group(1))
            o = MO.orders.get(m.group(1))
            if not o:
                return self._send(404, {"message": "No order found"})
            return self._send(200, {"data": {"id": m.group(1), "external_id": o["payload"].get("external_id"), "is_test": True, "status": o["status"],
                                             "shipments": o["shipments"]}})
        self._send(404, {})

    def do_DELETE(self):
        if not self._ok():
            return
        m = re.fullmatch(r"/api/beta/orders/([A-Z0-9]+)", urlsplit(self.path).path)
        if MO.refuse_delete:
            return self._send(405, {"message": "Order cannot be cancelled"})
        if m and m.group(1) in MO.orders:
            MO.deletes.append(m.group(1))
            MO.orders[m.group(1)]["status"] = "CANCELLED"
            return self._send(204)
        self._send(422, {"message": "not cancellable"})


mo = ThreadingHTTPServer(("127.0.0.1", 0), MOHandler)
threading.Thread(target=mo.serve_forever, daemon=True).start()
MO_BASE = f"http://127.0.0.1:{mo.server_address[1]}"

api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
sys.path.insert(0, API)
import requests  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import iris as L  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import store  # noqa: E402
from _lib import pay, abtest  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import prints as PR  # noqa: E402
from _lib import merchone as MC  # noqa: E402
from _lib import ops  # noqa: E402
from _lib import maker  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
PACK = json.load(open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
WHO = {"kind": "admin-v1", "exp": int(time.time()) + 3600}
LEGACY = list(CT.legacy_ids())
STYLE = "solo.gold" if "solo.gold" in LEGACY else LEGACY[0]


def mo_env(on=True):
    for k in ("MERCHONE_API_USER", "MERCHONE_API_KEY", "MERCHONE_API_BASE", "MERCHONE_LIVE"):
        os.environ.pop(k, None)
    if on:
        os.environ.update(MERCHONE_API_USER=USER, MERCHONE_API_KEY=KEY, MERCHONE_API_BASE=MO_BASE)


def fresh_switch():
    PR._SW.update(v=None, t=0.0, failed=0.0)


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


def rj(path):
    try:
        with open(os.path.join(STORE, *path.split("/")), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def exists(path):
    return os.path.isfile(os.path.join(STORE, *path.split("/")))


_EYES = {}


def draft(name="blue_round", lang="en"):
    if name not in _EYES:
        jpeg = SI.jpeg_bytes(name)
        prof = EYE.profile_of_bytes(jpeg, pad=1.12, rules=("lid", "fill"))
        _EYES[name] = P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=prof)["sealed"]
    c, j = post("/api/order", {"action": "draft", "eye": 1, "crop": H.jpeg_b64(256, 11), "pad": 1.12, "ticket": H.fresh_ticket(), "lang": lang,
                               "ref": "e1", "sealed": _EYES[name]})
    assert c == 200, (c, j)
    return j["order"], j["k"]


def co(o, k, **kw):
    body = {"order": o, "k": k, "eyes": 1, "style": STYLE, "names": "", "title": "", "lang": kw.pop("lang", "en"), "consent_digital": True}
    body.update(kw)
    return post("/api/checkout", body)


def fix_total(sid):
    """The fake Stripe of the harness sums line item 0 only: a real session's amount_total is every line item and the shipping."""
    p = next(params for params, _h in reversed(H.Fake.creates) if params.get("client_reference_id") == H.Fake.sessions[sid]["metadata"]["order"])
    s = H.Fake.sessions[sid]
    tot = int(p["line_items[0][price_data][unit_amount]"]) + int(p.get("line_items[1][price_data][unit_amount]") or 0) \
        + int(p.get("shipping_options[0][shipping_rate_data][fixed_amount][amount]") or 0)
    s["amount_total"] = tot
    return p


def pay_with_address(sid, cc="LT", name="SnapEyes Test", email="kunde@example.com", old_api=False):
    s = H.pay_session(sid, email)
    sd = {"name": name, "address": {"line1": "Gedimino pr. 1", "line2": "", "city": "Vilnius", "postal_code": "01100", "state": "", "country": cc}}
    if old_api:
        s["shipping_details"] = sd
    else:
        s["collected_information"] = {"shipping_details": sd}
    return s


def webhook(obj):
    body, sig = H.signed_event(obj, "checkout.session.completed")
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=180)
    return r.status_code, r.json()


def deliver(order, side=2048, held=False, w=None, h=None):
    """A made artwork: the file and delivery.json, as compose_order writes them."""
    a = (np.random.default_rng(7).random(((h or side), (w or side), 3)) * 80).astype("uint8")
    b = io.BytesIO()
    Image.fromarray(a).save(b, "JPEG", quality=88)
    key = f"orders/{order}/artwork_test.jpg"
    store.put(key, b.getvalue(), "image/jpeg", upsert=True)
    store.put(f"orders/{order}/delivery.json", store.json_bytes({"key": key, "width": w or side, "height": h or side, "bytes": len(b.getvalue()),
                                                               "needs_review": held, "created_at": int(time.time())}), "application/json", upsert=True)
    return key


def paid_print_order(cc="LT", product="acrylic40", lang="en", mismatch_cc=None):
    o, k = draft(lang=lang)
    c, j = co(o, k, lang=lang, print={"product": product, "country": cc}, consent_print=True)
    assert c == 200, (c, j)
    sid = rj(f"orders/{o}/order.json")["checkout"]["session_id"]
    fix_total(sid)
    sess = pay_with_address(sid, cc=mismatch_cc or cc)
    c2, j2 = webhook(sess)
    assert c2 == 200, (c2, j2)
    return o, k, sid


# ============================================================================================ 1. the tables and the rules
section("1. the tables and the rules: shipping, margins, the print file")
check("the shipping rule: the cost with 19 % VAT rounded UP to the next .49 or .99 (3.99 to 4.99, 5.50 to 6.99, 6.99 to 8.49, 7.99 to 9.99)",
      [PR.ship_price(c) for c in (399, 550, 699, 799, 1, 49, 50)] == [499, 699, 849, 999, 49, 99, 99], [PR.ship_price(c) for c in (399, 550, 699, 799, 1, 49, 50)])
check("the offer: five prints at the owner's prices (59, 79, 129, 69, 35 EUR), every SKU in the rate table, prints offered on eu, lt and hr only"
      " - 1124: the final list of that day (the owner's decisions of 2026-11-24): eleven prints offered, the keyring twelfth in the list and not offered",
      [(p["id"], p["price"]) for p in PR.products()] == [("acrylic30", 5900), ("acrylic40", 7900), ("acrylic60", 12900), ("metal30", 5900), ("metal40", 7900),
                                                         ("metal60", 12900), ("canvas40", 4900), ("canvas60", 6900), ("poster50", 3500), ("block10", 3900),
                                                         ("block20", 7900), ("keyring", 2000)]      # 1125: the keyring is offered, at 20 EUR
      and [(p["id"], p["price"], p["on"]) for p in PR.products(offered=False)][11:] == [("keyring", 2000, 1)]
      and all(PR.sku_rec(p["sku"]) for p in PR.products()) and PR.markets() == ("eu", "lt", "hr"), PR.products())
check("the countries: the 27 member states of the EU, each with a rate for every print and a name in every language; no US, no GB",
      len(PR.countries()) == 27 and "US" not in PR.countries() and "GB" not in PR.countries()
      and all(PR.ship_cost(cc, p["sku"]) for cc in PR.countries() for p in PR.products())
      and all(PR.PRINT_NAMES["countries"][cc][l] for cc in PR.countries() for l in PR.LANGS), PR.countries())
mg = {p["id"]: min(PR.margin(p["id"], cc) for cc in PR.countries()) for p in PR.products()}
check("every print earns at least the margin floor in every country after merchOne's price and shipping with VAT and the payment fee",
      all(v >= PR.PRINT_OFFER["margin_floor"] for v in mg.values()), mg)
js = subprocess.run([NODE, "-e", (
    "import(require('url').pathToFileURL(process.argv[2]).href).then((m) => { const t = m.readPrints(process.argv[1]);"
    " const o = {}; for (const p of t.offer.products) for (const cc of Object.keys(t.rates.shipping)) o[p.id + cc] = [m.shipRule(t.rates.shipping[cc][p.sku], t.offer.vat_pct), m.marginRule(t.offer, t.rates, p.id, cc)];"
    " console.log(JSON.stringify(o)); })"), REPO, os.path.join(REPO, "scripts", "check_prints.mjs")], capture_output=True, text=True, timeout=120)
try:
    jsv = json.loads(js.stdout.strip().splitlines()[-1])
except (ValueError, IndexError):
    jsv = None
py = {p["id"] + cc: [PR.shipping(cc, p["id"]), PR.margin(p["id"], cc)] for p in PR.products(offered=False) for cc in PR.countries()}      # 1124: every product of the list, the keyring too (it is off)
check("the server's shipping and margins are the build check's (scripts/check_prints.mjs, the rules the page's module is held to) for every print and country",
      jsv == py, (js.stderr[-300:], None if jsv is None else [k for k in py if jsv.get(k) != py[k]][:5]))
geo = {p["sku"]: PR.file_geometry(p["sku"], 4096) for p in PR.products()}
s30, s60, cv, ps = geo["ACP0300301HP"], geo["ACP0600601HP"], geo["CVS0400401LMF2HC"], geo["PSD0500501"]      # 1124: the canvas without an outer frame
check("the print file of a 4096 px master: the design area at 200 dpi where the master allows (30 cm: 2362 px), at the master's own resolution for 60 cm "
      "(173 dpi, never under merchOne's 120), the trim around it (2.5 mm a side on acrylic: 2402 px), no trim on the canvas, 3 mm on the poster",
      s30 == (2402, 2362, 200) and s60[2] == 173 and s60[1] <= 4096 and s60[0] - s60[1] == 34 and cv == (3150, 3150, 200) and ps[0] - ps[1] == 48, geo)
check("a print file is never under merchOne's minimum print area", all(geo[s][1] >= PR.sku_rec(s)["design_px"][0] for s in geo), geo)
a = np.zeros((300, 450, 3), dtype=np.uint8)
a[:, :, 0] = 40
a[100:200, 200:250] = 250
raw = io.BytesIO()
Image.fromarray(a).save(raw, "PNG")
data, info = PR.make_print_file(raw.getvalue(), "PSD0500501")
pic = np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
check("a 3:2 artwork is centred on the square print file and its background is continued (the corners carry the artwork's ground, not black or white), "
      "nothing of it is cut",
      pic.shape[0] == pic.shape[1] == info["width"] and info["art"][0] == info["design"] and abs(int(pic[5, 5, 0]) - 40) < 12
      and abs(int(pic[pic.shape[0] // 2, pic.shape[1] // 2, 0]) - 250) < 20, (info, pic[5, 5], pic[pic.shape[0] // 2, pic.shape[1] // 2]))
# 2026-11-13: Finnish, Estonian and Latvian (languages, not markets: the prints stay on eu, lt and hr); a name for every print and every country in each of the eight
check("the product's name in the five languages, with its size (no-break spaces)"
      " - 1113: in the eight languages (Finnish, Estonian, Latvian), every print and every country named in each, the eight names of a print all different",
      PR.LANGS == ("en", "de", "lt", "hu", "hr", "fi", "et", "lv")
      and PR.product_name("acrylic40", "fi") == "Akryylilasitaulu 40\u00a0×\u00a040\u00a0cm" and PR.product_name("canvas40", "et").startswith("Lõuend puidust alusraamil")
      and PR.product_name("poster50", "lv") == "Plakāts 50\u00a0×\u00a050\u00a0cm" and PR.product_name("poster50", "fi").startswith("Juliste")
      and [PR.country_name("DE", l) for l in ("fi", "et", "lv")] == ["Saksa", "Saksamaa", "Vācija"]
      and [PR.country_name(cc, l) for cc, l in (("FI", "fi"), ("EE", "et"), ("LV", "lv"))] == ["Suomi", "Eesti", "Latvija"]
      and all(len({PR.product_name(pid, l) for l in PR.LANGS}) == 8 for pid in ("acrylic30", "acrylic40", "acrylic60", "canvas40"))
      and all(PR.product_name(p_["id"], l).endswith("\u00a0cm") and "\u00a0×\u00a0" in PR.product_name(p_["id"], l) for p_ in PR.products() if p_["cm"] for l in PR.LANGS)
      and all(isinstance(PR.country_name(cc, l), str) and PR.country_name(cc, l).strip() for cc in PR.countries() for l in PR.LANGS) and
      PR.product_name("acrylic40", "en") == "Acrylic glass print 40 × 40 cm" and PR.product_name("canvas40", "lt").startswith("Drobė ant medinio porėmio")
      and PR.product_name("poster50", "hu").startswith("Poszter") and PR.country_name("DE", "hr") == "Njemačka", [PR.product_name("acrylic40", l) for l in PR.LANGS])
src = "\n".join(open(os.path.join(API, "_lib", f), encoding="utf-8").read() for f in ("prints.py", "merchone.py", "print_offer.py", "print_names.py", "print_rates.py"))
check("the new server files hold no dash and no credential", not re.search(DASH, src) and USER not in src and "MERCHONE_API_KEY=" not in src, "")

# ============================================================================================ 2. the switch
section("2. the switch: off by default, why, the admin action")
mo_env(False)
fresh_switch()
c, info0 = get("/api/checkout")
check("GET /api/checkout says nothing of prints while they cannot be bought (no credentials): the reply is the one of before prints existed",
      c == 200 and "prints" not in info0 and "print" not in (info0.get("consent") or {}), sorted(info0))
o, k = draft()
c, j = co(o, k, print={"product": "acrylic40", "country": "LT"}, consent_print=True)
check("a print without merchOne configured: 409 print_unavailable, why not_configured, nothing created", c == 409 and j.get("reason") == "print_unavailable"
      and j.get("why") == "not_configured", (c, j))
mo_env(True)
fresh_switch()
c, j = co(o, k, print={"product": "acrylic40", "country": "LT"}, consent_print=True)
check("configured, but the owner's switch is off (the default): 409 print_unavailable, why off", c == 409 and j.get("why") == "off", (c, j))
check("the switch is off by default and the health booleans say so (merchone true, prints false, merchone_live false)",
      PR.switch_state(fresh=True).get("on") is False and get("/api/health")[1].get("merchone") is True and get("/api/health")[1].get("prints") is False
      and get("/api/health")[1].get("merchone_live") is False, get("/api/health")[1])
e = None
try:
    ops.ACTIONS["print_switch"]({"on": True}, WHO)
except store.Answer as x:
    e = x
check("the admin's switch needs its confirmation word (400 confirm_required) and audits the refusal", e is not None and e.body.get("reason") == "confirm_required", e)
r = ops.ACTIONS["print_switch"]({"on": True, "confirm": "spaudiniai", "rev": 0}, WHO)
fresh_switch()
check("the admin turns prints on: the switch is on, revision 1, by the admin key's kind, in the audit log",
      r["result"] == "on" and PR.switch_state(fresh=True)["on"] is True and r["switch"]["rev"] == 1 and r["switch"]["by"] == "admin-v1"
      and any(os.path.basename(f).endswith(".json") for d, _, fs in os.walk(os.path.join(STORE, "ops", "audit")) for f in fs), r)
e = None
try:
    ops.ACTIONS["print_switch"]({"on": False, "confirm": "spaudiniai", "rev": 0}, WHO)
except store.Answer as x:
    e = x
check("a second tab's change (the old revision) is a 409 stale_view, not a silent overwrite", e is not None and e.body.get("reason") == "stale_view", e)
fresh_switch()
c, info1 = get("/api/checkout")
pr = info1.get("prints") or {}
check("GET /api/checkout now offers the prints: the markets, the products with their prices and the shipping per country with VAT, and the print box's text",
      pr.get("on") is True and pr.get("markets") == ["eu", "lt", "hr"] and [p["id"] for p in pr.get("products") or []] == [p["id"] for p in PR.products()]
      and pr["products"][1]["ship"]["DE"] == 499 and pr["products"][2]["ship"]["DE"] == 699 and pr["products"][0]["ship"]["SE"] == 999
      and (info1.get("consent") or {}).get("print", {}).get("lt") == PR.PRINT_CONSENT_TEXT["lt"] and "sku" not in json.dumps(pr) and "cost" not in json.dumps(pr), pr)
for why, body, market in (("market", {"product": "acrylic40", "country": "AU"}, "au"), ("product", {"product": "mug", "country": "LT"}, "eu"),
                          ("country", {"product": "acrylic40", "country": "US"}, "eu"), ("country", {"product": "acrylic40", "country": "GB"}, "eu")):
    o2, k2 = draft()
    c, j = co(o2, k2, market=market, print=body, consent_print=True)
    check(f"a print refused with why {why} ({body['product']} to {body['country']}, market {market}): 409 print_unavailable", c == 409 and j.get("why") == why, (c, j))
o2, k2 = draft()
c, j = co(o2, k2, print={"product": "acrylic40", "country": "LT"})
check("a print without its box ticked: 400 print_consent_required", c == 400 and j.get("reason") == "print_consent_required", (c, j))
c, j = co(o2, k2, print={"product": "acrylic40", "country": "LT"}, consent_print=True, print_shown=1)
check("a page that showed another print price: 409 print_price_changed with the server's price and shipping (retry true)",
      c == 409 and j.get("reason") == "print_price_changed" and j.get("print") == {"product": "acrylic40", "country": "LT", "price": 7900, "ship": 849}, (c, j))
store_get = store.get_json


def broken(path, *a, **kw):
    if path == PR.SWITCH_PATH:
        raise store.StorageError("injected")
    return store_get(path, *a, **kw)


store.get_json = broken
fresh_switch()
off = PR.offer_problem()
store.get_json = store_get
fresh_switch()
check("a switch that cannot be read is OFF (fail closed), and the failure is remembered a few seconds", off == "off", off)

# ============================================================================================ 3. the checkout with a print
section("3. the checkout with a print: Stripe, order.json, a checkout without a print unchanged")
o, k = draft()
n0 = len(H.Fake.creates)
c, j = co(o, k)
plain = H.Fake.creates[-1][0] if len(H.Fake.creates) > n0 else {}
check("a checkout of the file alone is the request of before prints existed: one line item, no shipping, no address form, the file's note, no print metadata",
      c == 200 and "line_items[1][price_data][unit_amount]" not in plain and not any(x.startswith(("shipping_", "custom_text[shipping")) for x in plain)
      and not any("print" in x or "ship_" in x for x in plain if x.startswith("metadata[")) and plain.get("custom_text[submit][message]") == pay.SUBMIT_NOTE["en"]
      and "print" not in j and "total" not in j, sorted(plain))
o, k = draft(lang="lt")
c, j = co(o, k, lang="lt", print={"product": "acrylic60", "country": "DE"}, consent_print=True, print_shown=12900 + 699)
p = H.Fake.creates[-1][0]
check("with a print: the second line item at the print's price with its Lithuanian name and description, in euros",
      c == 200 and p["line_items[1][price_data][unit_amount]"] == "12900" and p["line_items[1][price_data][currency]"] == "eur"
      and p["line_items[1][price_data][product_data][name]"] == PR.product_name("acrylic60", "lt")
      and p["line_items[1][price_data][product_data][description]"] == PR.ITEM_DESC_PRINT["lt"], {k_: v for k_, v in p.items() if "line_items[1]" in k_})
check("Stripe collects the delivery address for that ONE country, adds one fixed shipping rate (the country's for that print: 6.99 to Germany for 60 cm) with a "
      "delivery estimate in business days, and its note names the country",
      p["shipping_address_collection[allowed_countries][0]"] == "DE" and "shipping_address_collection[allowed_countries][1]" not in p
      and p["shipping_options[0][shipping_rate_data][fixed_amount][amount]"] == "699" and p["shipping_options[0][shipping_rate_data][type]"] == "fixed_amount"
      and p["shipping_options[0][shipping_rate_data][delivery_estimate][maximum][unit]"] == "business_day"
      and "Vokietija" in p["shipping_options[0][shipping_rate_data][display_name]"] and "Vokietija" in p["custom_text[shipping_address][message]"], p)
check("the note above the pay button is the print's (it says a print is shipped and cannot be withdrawn from, and keeps the binding order sentence)",
      p["custom_text[submit][message]"] == PR.SUBMIT_NOTE_PRINT["lt"] and "prievole sumokėti" in p["custom_text[submit][message]"], p.get("custom_text[submit][message]"))
check("the metadata: the artwork's amount as before, and print, print_sku, print_amount, ship_amount, ship_cc, written by the server",
      p["metadata[amount]"] == str(j["amount"]) and p["metadata[print]"] == "acrylic60" and p["metadata[print_sku]"] == "ACP0600601HP"
      and p["metadata[print_amount]"] == "12900" and p["metadata[ship_amount]"] == "699" and p["metadata[ship_cc]"] == "DE", {k_: v for k_, v in p.items() if k_.startswith("metadata[")})
rec = rj(f"orders/{o}/order.json")
cp = (rec.get("checkout") or {}).get("print") or {}
check("order.json keeps the print with the print box the customer ticked (consent version 2026-10-28.3, time, Lithuanian text, fingerprint)"
      " - 1113: consent version 2026-11-13.1 (the Finnish, Estonian and Latvian boxes added; the Lithuanian text as it was)",
      cp.get("product") == "acrylic60" and cp.get("country") == "DE" and cp.get("ship") == 699 and cp["consent"]["version"] == pay.CONSENT_VERSION == "2026-11-13.1"
      and cp["consent"]["text"] == PR.PRINT_CONSENT_TEXT["lt"] and len(cp["consent"]["text_sha256"]) == 16, cp)
check("the reply names the print and the total Stripe charges (the artwork, the print, its shipping)",
      j.get("print") == {"product": "acrylic60", "country": "DE", "price": 12900, "ship": 699} and j.get("total") == j["amount"] + 12900 + 699, j)
# 2026-11-25 (the owner's decision): no consent box for the file but on the US market; the print box stays (a print made to order, another legal role)
check("the file has no consent box on this market since 2026-11-25 (the owner's decision): no waiver recorded, the plain fact of how the order was placed instead; "
      "the texts of the versions before are still read",
      "consent" not in rec["checkout"] and rec["checkout"]["placed"]["box"] is False and pay.consent_text("2026-10-28.2", "en") == pay.CONSENT_TEXT["en"]
      and pay.consent_text("2026-10-28.3", "en", "us") == pay.CONSENT_TEXT_US["en"], rec["checkout"])
# 2026-11-13: the same checkout in Finnish, Estonian and Latvian (a poster to the language's own country): Stripe's line, shipping and notes and the recorded print box
# are that language's, under the current consent version (the variables of the Lithuanian order above are used further down and stay untouched)
PAYDUTY = {"fi": "maksuvelvollisuus", "et": "maksekohustusega", "lv": "pienākumu maksāt"}
for l_, cc_ in (("fi", "FI"), ("et", "EE"), ("lv", "LV")):
    o_l, k_l = draft(lang=l_)
    ship_l = PR.shipping(cc_, "poster50")
    c_l, j_l = co(o_l, k_l, lang=l_, print={"product": "poster50", "country": cc_}, consent_print=True, print_shown=3500 + (ship_l or 0))
    p_l = H.Fake.creates[-1][0] if c_l == 200 else {}
    cp_l = ((rj(f"orders/{o_l}/order.json").get("checkout") or {}).get("print") or {}) if c_l == 200 else {}
    rec_l = (rj(f"orders/{o_l}/order.json").get("checkout") or {}) if c_l == 200 else {}
    check(f"... and a checkout with a print in {l_} (a poster to {cc_}): the line item's name and description, the shipping label and the address note with the country's name, and the "
          f"note above the pay button with the binding order sentence are in {l_}; order.json keeps the {l_} print box under consent version 2026-11-13.1 and, the file "
          f"having no consent box since 2026-11-25 (the owner's decision), no waiver",
          c_l == 200 and p_l.get("line_items[1][price_data][product_data][name]") == PR.product_name("poster50", l_) and p_l.get("line_items[1][price_data][unit_amount]") == "3500"
          and p_l.get("line_items[1][price_data][product_data][description]") == PR.ITEM_DESC_PRINT[l_]
          and p_l.get("shipping_address_collection[allowed_countries][0]") == cc_ and p_l.get("shipping_options[0][shipping_rate_data][fixed_amount][amount]") == str(ship_l)
          and p_l.get("shipping_options[0][shipping_rate_data][display_name]") == PR.SHIP_LABEL[l_].format(country=PR.country_name(cc_, l_))
          and p_l.get("custom_text[shipping_address][message]") == PR.SHIP_ADDRESS_NOTE[l_].format(country=PR.country_name(cc_, l_))
          and p_l.get("custom_text[submit][message]") == PR.SUBMIT_NOTE_PRINT[l_] and PAYDUTY[l_] in PR.SUBMIT_NOTE_PRINT[l_]
          and PR.SUBMIT_NOTE_PRINT[l_] not in [PR.SUBMIT_NOTE_PRINT[x] for x in PR.LANGS if x != l_] and PR.ITEM_DESC_PRINT[l_] not in [PR.ITEM_DESC_PRINT[x] for x in PR.LANGS if x != l_]
          and cp_l.get("product") == "poster50" and cp_l.get("country") == cc_ and cp_l.get("consent", {}).get("version") == "2026-11-13.1" and cp_l["consent"]["lang"] == l_
          and cp_l["consent"]["text"] == PR.PRINT_CONSENT_TEXT[l_] and cp_l["consent"]["text_sha256"] == hashlib.sha256(PR.PRINT_CONSENT_TEXT[l_].encode("utf-8")).hexdigest()[:16]
          and "consent" not in rec_l and rec_l.get("placed", {}).get("box") is False
          and j_l.get("print") == {"product": "poster50", "country": cc_, "price": 3500, "ship": ship_l},
          (c_l, j_l, {k_: v for k_, v in p_l.items() if "line_items[1]" in k_ or k_.startswith(("custom_text", "shipping_options[0][shipping_rate_data][display"))}, cp_l))

# ============================================================================================ 4. the payment and the confirmation
section("4. the payment: paid.json, print.json, the amount, the confirmation e-mail")
sid = rec["checkout"]["session_id"]
fix_total(sid)
H.Fake.emails.clear()
sess = pay_with_address(sid, cc="DE", name="Jonas Jonaitis")
c, j = webhook(sess)
paid = rj(f"orders/{o}/paid.json") or {}
pp = paid.get("print") or {}
check("the webhook records the paid order with its print: the product, the SKU, the price and shipping, the name and address Stripe collected, the print box",
      c == 200 and pp.get("product") == "acrylic60" and pp.get("sku") == "ACP0600601HP" and pp.get("price") == 12900 and pp.get("ship") == 699
      and pp.get("name") == "Jonas Jonaitis" and pp["address"]["city"] == "Vilnius" and pp["address"]["country"] == "DE" and not pp.get("mismatch")
      and pp["consent"]["text"] == PR.PRINT_CONSENT_TEXT["lt"], (c, j, pp))
check("the amount is checked with the print: no amount_mismatch for the artwork plus the print plus its shipping",
      paid.get("amount_total") == rec["checkout"]["amount"] + 12900 + 699 and "amount_mismatch" not in paid, paid.get("amount_mismatch"))
check("print.json is waiting (the artwork is not delivered yet) and the order is in the print index of the daily run",
      (rj(f"orders/{o}/print.json") or {}).get("state") == "waiting" and exists(f"cleanup/print/{o}.json"), rj(f"orders/{o}/print.json"))
mail = next((m for m, _i in H.Fake.emails if o in m.get("subject", "") and m.get("to") == ["kunde@example.com"]), None)
txt = (mail or {}).get("text", "")
check("the confirmation e-mail (Lithuanian) has the print's rows (the file, the print, the shipping with the country, the delivery address), the delivery row "
      "names the print, and its section: production and delivery time, the producer, damage within 7 days, the print box quoted",
      mail is not None and "Spaudinys" in txt and "Vokietija, 6,99" in txt and "Jonas Jonaitis, Gedimino pr. 1" in txt and "Picanova GmbH" in txt
      and "per 7 dienas" in txt and PR.PRINT_CONSENT_TEXT["lt"][:40] in txt and "Joks spaudinys" not in txt and not re.search(DASH, txt), txt[:1500])
check("the confirmation names the total in its price row (the artwork, the print, the shipping)", pay.price_text(paid["amount_total"], "lt", "eur") in txt, "")
o3, k3, sid3 = paid_print_order(cc="LT", product="poster50", lang="en")
mail3 = next((m for m, _i in reversed(H.Fake.emails) if o3 in m.get("subject", "") and m.get("to") == ["kunde@example.com"]), {})
t3 = mail3.get("text", "")
check("an English confirmation: the print rows, 'Your print', the print box, no sentence that says no print is shipped",
      "Poster 50 × 50 cm, €35.00" in t3 and "Your print" in t3 and "Lithuania, €8.49" in t3 and "no print and no" not in t3 and PR.PRINT_CONSENT_TEXT["en"] in t3, t3[:1200])
o4, k4, sid4 = paid_print_order(cc="LT", product="acrylic30", mismatch_cc="LV")
pj4 = rj(f"orders/{o4}/print.json") or {}
check("an address in another country than the priced one: recorded as mismatch, the print HELD for the owner and the owner told (the payment itself is recorded)",
      (rj(f"orders/{o4}/paid.json") or {}).get("print", {}).get("mismatch") == ["country"] and pj4.get("state") == "held"
      and any("is held" in m.get("subject", "") and o4 in m.get("subject", "") for m, _i in H.Fake.emails), pj4)
sess_old = dict(H.Fake.sessions[sid3])
sess_old.pop("collected_information", None)
sess_old["shipping_details"] = {"name": "A B", "address": {"line1": "x", "city": "y", "postal_code": "1", "country": "LT"}}
check("an older Stripe API version's shipping_details is read too", PR.paid_part(sess_old, rj(f"orders/{o3}/order.json"))["name"] == "A B", "")
meta = {"eyes": "1", "style": STYLE, "market": "eu", "amount": "2497", "print": "poster50", "print_amount": "3500", "ship_amount": "849"}
check("a price test's session check takes the print off before comparing with the ladder (abtest.print_extra), and a session without one is unchanged",
      abtest.print_extra(meta) == 4349 and abtest.print_extra({"amount": "1"}) == 0 and PR.extra_cents(meta) == 4349 and PR.extra_cents({}) == 0, "")

# ============================================================================================ 5. the order at merchOne
section("5. the order at merchOne: when, what, once")
rec, paid = rj(f"orders/{o}/order.json"), pay.get_paid(o)
MO.creates.clear()
r = PR.step(o, rec, paid)
check("not before the artwork is delivered: the step waits and merchOne is not asked", r == "wait" and not MO.creates, r)
deliver(o, held=True)
r = PR.step(o, rec, paid)
check("not while the delivered artwork waits for the owner's look (needs_review, not released)", r == "wait" and not MO.creates, r)
deliver(o)
r = PR.step(o, rec, paid)
cur = PR.record(o)
pl = MO.creates[-1] if MO.creates else {}
check("delivered: the print goes to merchOne once, state created, its id recorded", r == "created" and cur["state"] == "created" and cur["merchone_id"] in MO.orders
      and len(MO.creates) == 1, (r, cur))
check("the payload: external_id = our order id, a TEST order (MERCHONE_LIVE is off), tracked shipping, the SKU, quantity 1",
      pl.get("external_id") == o and pl.get("is_test") is True and pl.get("shipping_type") == "tracked" and pl["items"][0]["product_sku"] == "ACP0600601HP"
      and pl["items"][0]["quantity"] == 1 and pl["items"][0]["external_id"] == f"{o}-1", pl)
check("the delivery address: the customer's name split into first and last name, street, city, postcode and the country; OUR e-mail, never the customer's; our "
      "company as the billing address",
      pl["shipping"]["firstname"] == "Jonas" and pl["shipping"]["lastname"] == "Jonaitis" and pl["shipping"]["street_primary"] == "Gedimino pr. 1"
      and pl["shipping"]["postcode"] == "01100" and pl["shipping"]["country"] == "DE" and pl["shipping"]["email"] == pay.CONTACT
      and "kunde@example.com" not in json.dumps(pl) and pl["billing"]["company"] == "MB Portretizuokis", pl.get("shipping"))
f = cur.get("file") or {}
url = pl["items"][0]["file"]["front"]["url"]
check("the print file: stored beside the order, a signed link that expires (merchOne fetches it), its size the SKU's print file for this master",
      f.get("path") == f"orders/{o}/print_acrylic60.jpg" and exists(f["path"]) and "expires=" in url and f["width"] == PR.file_geometry("ACP0600601HP", 2048)[0]
      and Image.open(os.path.join(STORE, *f["path"].split("/"))).size == (f["width"], f["width"]), (f, url))
r2 = PR.step(o, rec, paid)
check("a second step (a Stripe retry, the page, the daily run) does nothing: done, no second order", r2 == "done" and len(MO.creates) == 1, (r2, len(MO.creates)))
check("pending() is false once it is sent (the server's chain stops asking)", PR.pending(o, paid) is False, "")
# a lost reply: merchOne made the order but the answer did not arrive; the next try adopts it from merchOne's own refusal of the same external id
o5, k5, _s5 = paid_print_order(cc="AT", product="canvas40")
deliver(o5)
rec5, paid5 = rj(f"orders/{o5}/order.json"), pay.get_paid(o5)
MO.creates.clear()
MO.lose_reply = 1
r1 = PR.step(o5, rec5, paid5)
st1 = PR.record(o5)
r2 = PR.step(o5, rec5, paid5)
st2 = PR.record(o5)
made = [oid for oid, v in MO.orders.items() if v["payload"]["external_id"] == o5]
check("a reply lost on the way: the print waits (transient), the next step asks again, merchOne refuses the same external id and names its order, which is "
      "ADOPTED: one merchOne order, never two",
      r1 == "transient" and st1["state"] == "waiting" and r2 == "created" and len(made) == 1 and st2["merchone_id"] == made[0] and len(MO.creates) == 2, (r1, r2, made, st2))
# a refusal: failed, the owner told, the admin retries
o6, k6, _s6 = paid_print_order(cc="FR", product="acrylic30")
deliver(o6)
rec6, paid6 = rj(f"orders/{o6}/order.json"), pay.get_paid(o6)
MO.fail_create = [422]
H.Fake.emails.clear()
r = PR.step(o6, rec6, paid6)
st = PR.record(o6)
check("merchOne refuses the order (422): failed with merchOne's sentence, the owner told; the daily run does not retry it by itself",
      r == "failed" and st["state"] == "failed" and "invalid" in (st.get("error") or "") and any("refused the print" in m.get("subject", "") for m, _i in H.Fake.emails)
      and PR.step(o6, rec6, paid6) == "failed", (r, st))
res = ops.ACTIONS["print_retry"]({"order": o6}, WHO)
check("the admin's retry sends it again: created", res["result"] == "created" and PR.record(o6)["state"] == "created", res)
# withdrawn, refunded, not configured
o7, k7, _s7 = paid_print_order(cc="IT", product="poster50")
deliver(o7)
store.put(f"orders/{o7}/refunded.json", store.json_bytes({"t": 1}), "application/json", upsert=True)
r = PR.step(o7, rj(f"orders/{o7}/order.json"), pay.get_paid(o7))
check("a refunded order's print is cancelled before anything is sent", r == "done" and PR.record(o7)["state"] == "canceled" and not exists(f"cleanup/print/{o7}.json"), PR.record(o7))
o8, k8, _s8 = paid_print_order(cc="ES", product="poster50")
deliver(o8)
mo_env(False)
r = PR.step(o8, rj(f"orders/{o8}/order.json"), pay.get_paid(o8))
mo_env(True)
check("merchOne not configured on the deployment: the print waits (not_configured, the owner told once), nothing lost", r == "wait"
      and PR.record(o8)["state"] == "waiting" and PR.record(o8)["error"] == "not_configured", PR.record(o8))

# ============================================================================================ 6. the webhook and the daily run
section("6. the webhook, the shipping e-mail, the daily run, the cancel")
oid = PR.record(o)["merchone_id"]
ev = {"type": "shipment_sent", "data": {"order": {"id": oid, "external_id": o, "status": "FULFILLED"}, "shipment": {"tracking_url": "https://evil.example/x"}}}
rr = requests.post(BASE + "/api/order?hook=merchone&token=wrong", data=json.dumps(ev), headers={"Content-Type": "application/json"}, timeout=60)
check("the webhook with a wrong token: 403, nothing read or changed", rr.status_code == 403 and PR.record(o)["state"] == "created", rr.text[:200])
MO.orders[oid]["status"] = "FULFILLED"
MO.orders[oid]["shipments"] = [{"tracking_number": "00340434161094042557", "tracking_url": "https://www.dhl.com/track?id=00340434161094042557",
                                "shipped_at": "2026-10-30T10:00:00Z", "shipping_method": {"code": "DHL", "name": "DHL Standard"}}]
H.Fake.emails.clear()
rr = requests.post(BASE + "/api/order?" + "hook=merchone&token=" + PR.hook_token(), data=json.dumps(ev), headers={"Content-Type": "application/json"}, timeout=60)
cur = PR.record(o)
check("the right token: the event's order is read back from merchOne, and ITS shipment (never the event's own link) is recorded: shipped, out of the index",
      rr.status_code == 200 and cur["state"] == "shipped" and cur["tracking"]["url"].startswith("https://www.dhl.com/") and not exists(f"cleanup/print/{o}.json"), (rr.text[:300], cur))
shipped = [m for m, _i in H.Fake.emails if m.get("subject") == PR.SHIPPED["lt"]["subject"]]
check("the customer gets the shipping e-mail once, in the order's language, with the tracking link and the 7 day request (no dash)",
      len(shipped) == 1 and "https://www.dhl.com/track" in shipped[0]["text"] and "per 7 dienas" in shipped[0]["text"] and shipped[0]["to"] == ["kunde@example.com"]
      and not re.search(DASH, shipped[0]["text"]), shipped)
rr = requests.post(BASE + "/api/order?hook=merchone&token=" + PR.hook_token(), data=json.dumps(ev), headers={"Content-Type": "application/json"}, timeout=60)
check("the same event again (merchOne retries): no second e-mail", rr.status_code == 200 and len([m for m, _i in H.Fake.emails if m.get("subject") == PR.SHIPPED["lt"]["subject"]]) == 1, rr.text[:200])
rr = requests.post(BASE + "/api/order?hook=merchone&token=" + PR.hook_token(), data=json.dumps({"type": "shipment_sent", "data": {"order": {"id": "PPO1T", "external_id": "nope-1234"}}}),
                   headers={"Content-Type": "application/json"}, timeout=60)
check("an event for an order of no print of ours: 200 and ignored", rr.status_code == 200 and rr.json().get("ignored"), rr.text[:200])
oid5 = PR.record(o5)["merchone_id"]
MO.orders[oid5]["shipments"] = [{"tracking_number": "123", "tracking_url": "https://tracking.dpd.de/x", "shipping_method": {"name": "DPD"}}]
PR._write(o5, PR.record(o5), is_test=False)      # as a live order: the daily run does not read a TEST order back (section 9)
d = PR.daily(True, 0.0, lambda s: None)
check("the daily run catches a shipment whose webhook was lost: the print read back, shipped, the e-mail sent", PR.record(o5)["state"] == "shipped" and d["shipped"] >= 1, d)
oid6 = PR.record(o6)["merchone_id"]
MO.refuse_delete = True
e = None
try:
    ops.ACTIONS["print_cancel"]({"order": o6, "confirm": o6}, WHO)
except store.Answer as x:
    e = x
MO.refuse_delete = False
check("merchOne refuses the cancel (its first seconds, or the order is in production after the hold time): 409 not_cancellable with its sentence, retry true, "
      "nothing recorded as cancelled", e is not None and e.status == 409 and e.body.get("reason") == "not_cancellable" and "cannot be cancelled" in e.body.get("error", "")
      and PR.record(o6)["state"] == "created", e and e.body)
res = ops.ACTIONS["print_cancel"]({"order": o6, "confirm": o6}, WHO)
check("the admin's cancel at merchOne (the order number typed): merchOne's DELETE, state canceled, out of the index",
      res["result"] == "canceled" and oid6 in MO.deletes and PR.record(o6)["state"] == "canceled" and not exists(f"cleanup/print/{o6}.json"), res)
st = ops.ACTIONS["print_status"]({}, WHO)
check("the admin page: the switch, merchOne configured, test orders, the webhook URL with its token, the offer with its margins, the open prints",
      st["switch"]["on"] is True and st["configured"] is True and st["live"] is False and PR.hook_token() in st["hook_url"]
      and len(st["offer"]) == 12 and all(x["margin_min"] >= PR.PRINT_OFFER["margin_floor"] for x in st["offer"] if x["on"])
      and [x["id"] for x in st["offer"] if not x["on"]] == [] and {x["id"]: x["margin_min"] for x in st["offer"]}["keyring"] == 1575 and any(r_["order"] == o8 for r_ in st["open"]), st["open"])
ov = ops.ACTIONS["order"]({"order": o}, WHO)
check("the admin's order detail has the print block (state, merchOne id, tracking, the file), no street address", (ov.get("print") or {}).get("state") == "shipped"
      and ov["print"]["merchone_id"] == oid and "Gedimino" not in json.dumps(ov["print"]), ov.get("print"))

# ============================================================================================ 7. the server's chain, the order page, health
section("7. the server's own making, the order page, health")
o9, k9, _s9 = paid_print_order(cc="PL", product="acrylic30")
deliver(o9)
rec9, paid9 = rj(f"orders/{o9}/order.json"), pay.get_paid(o9)
store.put(f"orders/{o9}/mail_delivery.json", store.json_bytes({"state": "sent", "making": "server"}), "application/json", upsert=True)
dec = maker._step(o9, rec9, paid9, 3, {"make_eye": None, "compose_order": None})
check("the server's step of a delivered order with a print sends it after the ready e-mail, then stops ready", dec == ("stop", "ready") and PR.record(o9)["state"] == "created", (dec, PR.record(o9)))
c, sj = get(f"/api/order?o={o}&k={pay.access_key(o)}")
check("the order page's status of a paid order with a print: product, country, shipped and the tracking link", c == 200 and sj.get("print", {}).get("state") == "shipped"
      and sj["print"]["tracking_url"].startswith("https://www.dhl.com/") and sj["print"]["product"] == "acrylic60", sj.get("print"))
c, sj9 = get(f"/api/order?o={o9}&k={pay.access_key(o9)}")
check("... and a sent one reads 'sent' with no link", sj9.get("print", {}).get("state") == "sent" and sj9["print"].get("tracking_url") is None, sj9.get("print"))
c, h = get("/api/health")
check("health: merchone true, prints true (switch on, configured), merchone_live false; MERCHONE_LIVE=1 makes it true", h.get("merchone") is True and h.get("prints") is True
      and h.get("merchone_live") is False and (os.environ.update(MERCHONE_LIVE="1") or MC.live()) is True, h)
os.environ.pop("MERCHONE_LIVE", None)
check("a log line never carries the merchOne key or user", USER not in pay.scrub(f"x {USER} {KEY}") and KEY not in pay.scrub(f"x {KEY}"), pay.scrub(f"x {USER} {KEY}"))

# ============================================================================================ 8. the legal texts
section("8. the legal texts: the editions with and without prints, the consent version")
docs = PACK.get("docs") or {}
ed = PACK.get("editions") or {}


def term_text(lang, edition=None):
    d = ((ed.get(edition) or {}).get(lang) if edition else docs.get(lang)) or {}
    return (d.get("terms") or {}).get("text", "")


en, lt_, hu_, hr_, de_ = (term_text(x) for x in ("en", "lt", "hu", "hr", "de"))
fi_, et_, lv_ = (term_text(x) for x in ("fi", "et", "lv"))      # 2026-11-13: the Finnish, Estonian and Latvian terms of the EU edition
check("the EU terms in every language name the prints with their prices, the shipping table, the delivery countries, the manufacturer and its address, "
      "Art. 16(c), the 7 days and the legal guarantee of two years"
      " - 1113: in Finnish, Estonian and Latvian too (the manufacturer and its address, Article 16(c) in each language's own words, the prices of all five prints, 7 and 30 days, two years, "
      "the 27 countries by their names in that language)"
      " - 1124: the prices of the eleven prints of now (59, 79, 129, 49, 69, 35 and 39 EUR) and the block, the metal and the canvas by their names in each of the "
      "eight languages; no text names a black or floating frame",
      all("Picanova GmbH" in t and "Eupener Straße 67" in t and "16" in t for t in (en, lt_, hu_, hr_, de_, fi_, et_, lv_)) and "€59.00" in en and "59,00 €" in de_
      and "Germany" in en and "Sweden" in en and "two years" in en and "7 days" in en and "Article 16(c)" in en and "30 days" in en
      and "16 artiklan c alakohta" in fi_ and "artikli 16 punkt c" in et_ and "16. panta c) punkts" in lv_
      and all(all(re.search(r"(?<!\d)%s,00\s*€" % eur_, t) for eur_ in (59, 79, 129, 49, 69, 35, 39, 20)) for t in (fi_, et_, lv_))
      and all(len(re.findall(r"(?<!\d)79,00\s*€", t)) == 3 for t in (de_, lt_, hu_, hr_, fi_, et_, lv_)) and en.count("€79.00") == 3 and en.count("€49.00") == 1
      and all(PR.product_name(pid_, l) in t for pid_ in ("block10", "block20", "metal30", "metal60", "canvas40", "canvas60")
              for l, t in (("en", en), ("de", de_), ("lt", lt_), ("hu", hu_), ("hr", hr_), ("fi", fi_), ("et", et_), ("lv", lv_)))
      and all(PR.PRINT_NAMES["kinds"]["keyring"][l] + ": " in t for l, t in (("en", en), ("de", de_), ("lt", lt_), ("fi", fi_)))      # 1125: the keyring's row
      and not re.search(r"floating frame|Schattenfuge|juodame rėme", en + de_ + lt_)
      and all(re.search(r"(?<!\d)7\s%s" % d_, t) and re.search(r"(?<!\d)30\s%s" % d_, t) for d_, t in (("päivä", fi_), ("päeva", et_), ("dien", lv_)))
      and "kahden vuoden" in fi_ and "kaheaastane" in et_ and re.search(r"divu gadu|divus gadus", lv_)
      and all(PR.country_name(cc, l) in t for l, t in (("fi", fi_), ("et", et_), ("lv", lv_)) for cc in PR.countries()),
      [(l, cc) for l, t in (("fi", fi_), ("et", et_), ("lv", lv_)) for cc in PR.countries() if PR.country_name(cc, l) not in t] or en[:300])
check("the EU terms no longer say that no print is sold, in any language", all(x not in t for t, x in ((en, "We do not sell prints"), (de_, "Drucke, Rahmen oder andere"),
      (lt_, "Spaudinių, rėmelių ar kitų"), (hu_, "Nyomatot, keretet vagy más"), (hr_, "Ne prodajemo otiske"))), "")
au, us_ = term_text("en", "au"), term_text("en", "us")
check("the Australian and the US editions sell no print and still say so (their markets offer none)", "We do not sell prints" in au and "We do not sell prints" in us_
      and "Picanova" not in au and "Picanova" not in us_, (au[:100], us_[:100]))
huhu = term_text("hu", "hu")
check("the Hungarian edition's terms (forints) carry the print section and say a print is added only to an order in euros", "Picanova" in huhu
      and "csak euróban" in huhu.lower() or "Nyomatot csak euróban" in huhu, huhu[:200])
priv = json.dumps(PACK)
check("the privacy policy of the EU edition names the print partner as a recipient of the name and the address (the pack carries it for every language)",
      all(("Picanova" in (((docs.get(l) or {}).get("privacy") or {}).get("text", "") or "Picanova")) for l in ("en",)) or "Picanova" in priv, "")
check("the consent version is 2026-10-28.3 on the server and the page, and the print box is the same words on both (the build's text check holds it)"
      " - 1113: the consent version is 2026-11-13.1 on both, and the print box of each of the eight languages is the same words on both, eight different texts",
      pay.CONSENT_VERSION == "2026-11-13.1" and "WITHDRAWAL_CONSENT_VERSION = '2026-11-13.1'" in open(os.path.join(REPO, "src", "shared", "legal.ts"), encoding="utf-8").read()
      and "2026-10-28.3'" not in open(os.path.join(REPO, "src", "shared", "legal.ts"), encoding="utf-8").read().split("WITHDRAWAL_CONSENT_VERSION = ")[1][:20]
      and set(PR.PRINT_CONSENT_TEXT) == set(PR.LANGS) == {"en", "de", "lt", "hu", "hr", "fi", "et", "lv"} and len(set(PR.PRINT_CONSENT_TEXT.values())) == 8
      and all(PR.PRINT_CONSENT_TEXT[l] in open(os.path.join(REPO, "src", "shared", "legal.ts"), encoding="utf-8").read() for l in PR.LANGS), "")
check("no dash in any print text the server sends (the e-mails, the Stripe notes, the consent)", not re.search(DASH, json.dumps([PR.CONF, PR.SHIPPED, PR.SUBMIT_NOTE_PRINT,
      PR.ITEM_DESC_PRINT, PR.PRINT_CONSENT_TEXT, PR.SHIP_LABEL, PR.SHIP_ADDRESS_NOTE], ensure_ascii=False)), "")


# ============================================================================================ 9. the review's fixes
section("9. the review of 2026-10-28: live payments, the line item, the daily run, the shipping e-mail, the lock, no step back, the refund")
# the artwork's own line item of a print order says nothing of "no print"
o20, k20 = draft()
c, j = co(o20, k20, print={"product": "poster50", "country": "LT"}, consent_print=True)
p20 = H.Fake.creates[-1][0]
o21, k21 = draft()
c2, j2 = co(o21, k21)
p21 = H.Fake.creates[-1][0]
check("a print order's own artwork line describes the file and the print line after it (never 'No print, no frame'); a file-only order keeps its description",
      c == 200 and p20["line_items[0][price_data][product_data][description]"] == PR.ITEM_DESC_FILE["en"] and "No print" not in PR.ITEM_DESC_FILE["en"]
      and c2 == 200 and p21["line_items[0][price_data][product_data][description]"] == pay.ITEM_DESC["en"]
      and all(PR.ITEM_DESC_FILE[l] for l in PR.LANGS), (p20.get("line_items[0][price_data][product_data][description]"), p21.get("line_items[0][price_data][product_data][description]")))
# a LIVE payment is never sent as a test order
o22, k22, _s22 = paid_print_order(cc="LT", product="acrylic30")
deliver(o22)
pd22 = rj(f"orders/{o22}/paid.json")
pd22["livemode"] = True
store.put(f"orders/{o22}/paid.json", store.json_bytes(pd22), "application/json", upsert=True)
MO.creates.clear()
H.Fake.emails.clear()
r = PR.step(o22, rj(f"orders/{o22}/order.json"), pay.get_paid(o22))
check("a LIVE payment while MERCHONE_LIVE is not set: the print is HELD (not_live), nothing goes to merchOne, the owner is told",
      r == "held" and not MO.creates and PR.record(o22)["state"] == "held" and PR.record(o22)["error"] == "not_live"
      and any("MERCHONE_LIVE" in m.get("subject", "") for m, _i in H.Fake.emails), (r, PR.record(o22)))
check("... and the daily run and the server's chain leave it (held is the owner's): no try, no test order", PR.step(o22, rj(f"orders/{o22}/order.json"), pay.get_paid(o22)) == "held"
      and not MO.creates, len(MO.creates))
os.environ["MERCHONE_LIVE"] = "1"
res = ops.ACTIONS["print_retry"]({"order": o22}, WHO)
live_pl = MO.creates[-1] if MO.creates else {}
os.environ.pop("MERCHONE_LIVE", None)
check("with MERCHONE_LIVE set the owner's retry sends it as a REAL order (is_test false)", res["result"] == "created" and live_pl.get("is_test") is False, (res, live_pl.get("is_test")))
real_prod = pay.on_production
pay.on_production = lambda: True
e = None
try:
    ops.ACTIONS["print_switch"]({"on": True, "confirm": "spaudiniai", "rev": PR.switch_state(fresh=True)["rev"]}, WHO)
except store.Answer as x:
    e = x
os.environ["MERCHONE_LIVE"] = "1"
r_ok = ops.ACTIONS["print_switch"]({"on": True, "confirm": "spaudiniai", "rev": PR.switch_state(fresh=True)["rev"]}, WHO)
os.environ.pop("MERCHONE_LIVE", None)
pay.on_production = real_prod
check("on production the switch refuses to turn prints on while MERCHONE_LIVE is not set (409 not_live), and turns them on once it is",
      e is not None and e.body.get("reason") == "not_live" and r_ok["result"] == "on", e and e.body)
# never a step back
cur_o = PR.record(o)
back = PR._write(o, dict(cur_o, state="created"), state="created", partner_status="FULFILLED")
check("a write from a stale copy never moves a shipped print back (created asked, shipped kept, the other fields written)",
      cur_o["state"] == "shipped" and back["state"] == "shipped" and PR.record(o)["state"] == "shipped" and PR.record(o)["partner_status"] == "FULFILLED", back.get("state"))
st22 = PR.record(o22)
PR._write(o22, dict(st22, state="waiting"), state="waiting")
check("... nor a created one back to waiting; the owner's retry (back) may restart a failed or held one", PR.record(o22)["state"] == "created", PR.record(o22)["state"])
# the lock: a stale one is never deleted, the next generation is taken
o23, k23, _s23 = paid_print_order(cc="LT", product="poster50")
store.put(f"orders/{o23}/print_0.lock", store.json_bytes({"t": time.time() - 3600, "id": "dead"}), "application/json", upsert=True)
c1 = PR._claim(o23, 0)
c2_ = PR._claim(o23, 0)
check("a stale lock is not deleted: the next generation's lock is created (only one taker can), and a second taker finds it fresh and leaves",
      c1 is not None and c1[2] == 1 and exists(f"orders/{o23}/print_0.lock") and c2_ is None, (c1, c2_))
PR._release(c1)
check("its release deletes only its own lock", not exists(f"orders/{o23}/print_1.lock") and exists(f"orders/{o23}/print_0.lock"), "")
deliver(o23)
r23 = PR.step(o23, rj(f"orders/{o23}/order.json"), pay.get_paid(o23))
check("the next try records the generation it took (lock_gen) and is created", r23 == "created" and PR.record(o23).get("lock_gen") in (0, 1), PR.record(o23))
# the shipping e-mail: a transient failure keeps the order in the index, the daily run sends it
oid23 = PR.record(o23)["merchone_id"]
MO.orders[oid23]["shipments"] = [{"tracking_number": "999", "tracking_url": "https://tracking.dpd.de/999", "shipping_method": {"name": "DPD"}}]
H.Fake.emails.clear()
H.Fake.fail_mail = [503]
PR.refresh(o23)
kept = exists(f"cleanup/print/{o23}.json")
d = PR.daily(True, 0.0, lambda s: None)
sent23 = [m for m, _i in H.Fake.emails if m.get("subject") == PR.SHIPPED["en"]["subject"]]
check("the shipping e-mail that failed for a moment: the print is shipped, the order stays indexed, the daily run sends the e-mail once and then lets it go",
      PR.record(o23)["state"] == "shipped" and kept and len(sent23) == 1 and not exists(f"cleanup/print/{o23}.json"), (kept, len(sent23), d))
# the daily run: what waits for the owner takes no turn, a test order is not read back, the oldest checked go first
for i in range(8):
    store.put(f"cleanup/print/261028-parked{i:010d}.json", store.json_bytes({"t": 1}), "application/json", upsert=True)
    store.put(f"orders/261028-parked{i:010d}/print.json", store.json_bytes({"state": "failed" if i % 2 else "held"}), "application/json", upsert=True)
o24, k24, _s24 = paid_print_order(cc="LT", product="poster50")
deliver(o24)
d = PR.daily(True, 0.0, lambda s: None)
check("eight held or failed prints in the index take no turn: a new print is sent in the same run (parked counted apart)",
      PR.record(o24)["state"] == "created" and d.get("parked", 0) >= 8 and d["sent"] >= 1, d)
chk24 = PR.record(o24).get("checked")
d2 = PR.daily(True, 0.0, lambda s: None)
check("the daily run records when it looked at a print (checked), so the next run takes the oldest first", isinstance(chk24, int), chk24)
check("a TEST order that merchOne has is not read back again and again: the next daily run lets it leave the index (never produced, never shipped)",
      not exists(f"cleanup/print/{o24}.json") and PR.record(o24)["state"] == "created", d2)
# comments: no unverified text in the owner's note
H.Fake.emails.clear()
ev = {"type": "order_commented", "data": {"comment": "SECRET-UNVERIFIED-TEXT http://evil.example", "order": {"id": oid23, "external_id": o23}}}
rr = requests.post(BASE + "/api/order?hook=merchone&token=" + PR.hook_token(), data=json.dumps(ev), headers={"Content-Type": "application/json"}, timeout=60)
note = [m for m, _i in H.Fake.emails if "commented" in m.get("subject", "")]
check("a merchOne comment: the owner is told where to read it, the event's own (unsigned) text is not passed on",
      rr.status_code == 200 and note and "SECRET-UNVERIFIED-TEXT" not in note[0]["text"] and "merchOne dashboard" in note[0]["text"], note[:1])
# the refund of an order with a print
o25, k25, _s25 = paid_print_order(cc="LT", product="poster50")
deliver(o25)
PR.step(o25, rj(f"orders/{o25}/order.json"), pay.get_paid(o25))
oid25 = PR.record(o25)["merchone_id"]
pr25 = ops._print_after_refund(o25, pay.get_paid(o25))
check("refunding an order with a print cancels the print at merchOne while it is cancellable", pr25 == {"result": "canceled"} and oid25 in MO.deletes
      and PR.record(o25)["state"] == "canceled", pr25)
pr_shipped = ops._print_after_refund(o23, pay.get_paid(o23))
MO.refuse_delete = True
o26, k26, _s26 = paid_print_order(cc="LT", product="poster50")
deliver(o26)
PR.step(o26, rj(f"orders/{o26}/order.json"), pay.get_paid(o26))
pr26 = ops._print_after_refund(o26, pay.get_paid(o26))
MO.refuse_delete = False
check("... and warns the owner when it cannot (shipped already, or in production at merchOne)", pr_shipped.get("result") == "shipped" and pr_shipped.get("warning")
      and pr26.get("result") == "not_canceled" and "merchOne" in pr26.get("warning", ""), (pr_shipped, pr26))
# a second paid session with a print: the owner's note says so
H.Fake.emails.clear()
pay.extra_payment(o25, pay.get_paid(o25), {"session_id": "cs_test_second", "amount_total": 9999, "currency": "eur", "livemode": False, "payment_intent": "pi_x",
                                          "email": None, "spec": {"eyes": 1, "style": STYLE}, "print": {"product": "poster50", "country": "LT"}})
xn = [m for m, _i in H.Fake.emails if "paid twice" in m.get("subject", "")]
check("a second paid session with a print: the owner's refund note names the print (nothing is sent to merchOne for it)",
      xn and "with a PRINT (poster50 to LT)" in xn[0]["text"], xn[:1])
# 2026-11-13 (the next consent version came: 2026-11-13.1 added the Finnish, Estonian and Latvian boxes): the first version, 2026-10-28.3, still quotes the five boxes it
# had, word for word (their fingerprint is the one of the texts as they were committed with 2026-10-28.3), and the current version the eight
FIVE_BOXES_1028 = "f979c4e9b0e1b4ba86676e130f7c449fe6abf6219c7f1f091df7ed445d520da9"      # sha256 of the JSON list of the en, de, lt, hu, hr print boxes of 2026-10-28.3
five_boxes = [(PR.PRINT_CONSENT_TEXTS.get("2026-10-28.3") or {}).get(l) for l in ("en", "de", "lt", "hu", "hr")]
check("the print box survives the next consent version: the current version maps to the current text, the first one is kept"
      " - 1113: the next version is here (2026-11-13.1, eight boxes); under 2026-10-28.3 the five boxes of that version are quoted byte for byte (the fingerprint on record) "
      "and are the same words under the new version",
      PR.PRINT_CONSENT_TEXTS[pay.CONSENT_VERSION] == PR.PRINT_CONSENT_TEXT and set(PR.PRINT_CONSENT_TEXTS) == {"2026-10-28.3", "2026-11-13.1"} and pay.CONSENT_VERSION == "2026-11-13.1"
      and hashlib.sha256(json.dumps(five_boxes, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest() == FIVE_BOXES_1028
      and all(PR.consent_text("2026-10-28.3", l) == PR.PRINT_CONSENT_TEXT[l] == PR.consent_text("2026-11-13.1", l) for l in ("en", "de", "lt", "hu", "hr"))
      and all(PR.consent_text("2026-11-13.1", l) == PR.PRINT_CONSENT_TEXT[l] for l in ("fi", "et", "lv"))
      and PR.consent_text(pay.CONSENT_VERSION, "lt") == PR.PRINT_CONSENT_TEXT["lt"] and PR.consent_text("2026-09-30.2", "lt") is None, sorted(PR.PRINT_CONSENT_TEXTS))
check("1113: an old version quotes exactly the boxes it had: 2026-10-28.3 has the five print boxes of its day and no Finnish, Estonian or Latvian one (they were first shown under "
      "2026-11-13.1), as pay.CONSENT_TEXTS keeps the waivers of 2026-10-28.3",
      set(PR.PRINT_CONSENT_TEXTS.get("2026-10-28.3") or {}) == {"en", "de", "lt", "hu", "hr"} == set(pay.CONSENT_TEXTS["2026-10-28.3"])
      and all(PR.consent_text("2026-10-28.3", l) is None for l in ("fi", "et", "lv")),
      (sorted(PR.PRINT_CONSENT_TEXTS.get("2026-10-28.3") or {}), {l: (PR.consent_text("2026-10-28.3", l) or "")[:40] for l in ("fi", "et", "lv")}))
# the print file of 60 cm without full-frame float arrays
import tracemalloc  # noqa: E402
a60 = (np.random.default_rng(3).random((4096, 4096, 3)) * 60).astype("uint8")
b60 = io.BytesIO()
Image.fromarray(a60).save(b60, "JPEG", quality=88)
del a60
tracemalloc.start()
d60, i60 = PR.make_print_file(b60.getvalue(), "ACP0600601HP")
peak = tracemalloc.get_traced_memory()[1]
tracemalloc.stop()
check("the 60 cm print file is made with the border strips only: the arrays' peak stays under 200 MB for a 4096 px master (no full-frame float copies)",
      peak < 200 * 2 ** 20 and i60["width"] == PR.file_geometry("ACP0600601HP", 4096)[0], f"{peak / 2 ** 20:.0f} MB")

# ============================================================================================ 10. a print bought after the artwork
section("10. the print offered AFTER the purchase (2026-11-21): who gets it, its own session, the paid record once, the merge, the refunds, the e-mails")
mo_env(True)
fresh_switch()
KICKS = []
real_kick = maker.kick
maker.kick = lambda order, *a, **kw: KICKS.append((order, kw.get("why"))) or "off"      # the self-call has no address in this run: what would be asked for is recorded
REFUNDS = []
real_stripe = pay._stripe


class _Refund:
    status_code = 200

    def __init__(self, p):
        self.p = p

    def json(self):
        return {"id": "re_test_" + hashlib.sha256(self.p.get("payment_intent", "").encode()).hexdigest()[:8], "object": "refund", "status": "succeeded",
                "amount": 1, "currency": "eur", "payment_intent": self.p.get("payment_intent")}


def stripe_with_refunds(method, path, params=None, idem=None, timeout=15.0):
    """The harness's fake Stripe has no refunds: the admin's refund call is answered here, every other call goes to the stub."""
    if path == "/v1/refunds":
        REFUNDS.append(dict(params))
        return _Refund(dict(params))
    return real_stripe(method, path, params, idem, timeout)


pay._stripe = stripe_with_refunds


def paid_file_order(lang="en", market=None, delivered=True):
    """A paid order of the file alone (the webhook recorded it), delivered unless asked otherwise."""
    o_, k_ = draft(lang=lang)
    c_, j_ = co(o_, k_, lang=lang, **({"market": market} if market else {}))
    assert c_ == 200, (c_, j_)
    sid_ = rj(f"orders/{o_}/order.json")["checkout"]["session_id"]
    c2_, j2_ = webhook(H.pay_session(sid_))
    assert c2_ == 200, (c2_, j2_)
    if delivered:
        deliver(o_)
    return o_, k_, sid_


def addon(o_, k_, product="poster50", cc="LT", lang="en", **kw):
    body = {"addon": {"order": o_, "key": k_}, "print": {"product": product, "country": cc}, "consent_print": True, "lang": lang}
    body.update(kw)
    return post("/api/checkout", body)


def addon_sid(o_):
    return (rj(f"orders/{o_}/print_checkout.json") or {}).get("session_id")


def raw(path):
    try:
        with open(os.path.join(STORE, *path.split("/")), "rb") as f_:
            return f_.read()
    except OSError:
        return None


def refund_mark(o_, pi_):
    return f"ops/refunds/{o_}/{hashlib.sha256(pi_.encode()).hexdigest()[:16]}.json"


# --- who gets the offer
oa, ka, sa = paid_file_order(lang="lt")
c, sj = get(f"/api/order?o={oa}&k={ka}")
po = sj.get("print_offer") or {}
check("the status of a paid, delivered order without a print carries the offer: euros, the five prints with the server's prices and the shipping per country, "
      "the print box in the eight languages; no SKU, no cost, and no print block - 1124: the six prints (the list is compared with the server's own)",
      c == 200 and sj.get("state") == "ready" and po.get("currency") == "EUR" and [p_["id"] for p_ in po.get("products") or []] == [p_["id"] for p_ in PR.products()]
      and {p_["id"]: p_ for p_ in po["products"]}["poster50"]["price"] == 3500 and {p_["id"]: p_ for p_ in po["products"]}["poster50"]["ship"]["LT"] == 849
      and po["products"][2]["ship"]["DE"] == 699 and len(po["products"][0]["ship"]) == 27 and len(po["products"]) == 12
      and po.get("consent") == PR.PRINT_CONSENT_TEXT and "sku" not in json.dumps(po) and "cost" not in json.dumps(po) and "print" not in sj, (c, sj.get("state"), po))
ob, kb, sb = paid_file_order(delivered=False)
c, sjb = get(f"/api/order?o={ob}&k={kb}")
c2, j2 = addon(ob, kb)
check("a paid order whose artwork is not delivered yet: no offer in its status, and its checkout is refused 409 print_not_offered, why not_ready, nothing created",
      "print_offer" not in sjb and c2 == 409 and j2.get("reason") == "print_not_offered" and j2.get("why") == "not_ready" and not exists(f"orders/{ob}/print_checkout.json"), (sjb.get("state"), c2, j2))
deliver(ob, held=True)
c2, j2 = addon(ob, kb)
c, sjb = get(f"/api/order?o={ob}&k={kb}")
store.put(f"orders/{ob}/release.json", store.json_bytes({"t": 1}), "application/json", upsert=True)
c3, sjb3 = get(f"/api/order?o={ob}&k={kb}")
check("an artwork that waits for the owner's look: why review, no offer; once released the offer is there",
      c2 == 409 and j2.get("why") == "review" and "print_offer" not in sjb and sjb3.get("state") == "ready" and "print_offer" in sjb3, (c2, j2, sjb.get("state"), sorted(sjb3)))
n_creates = len(H.Fake.creates)
for mark, why in (("withdrawn.json", "withdrawn"), ("deleted.json", "deleted"), ("expired.json", "deleted"), ("refunded.json", "refunded")):
    ox, kx, sx = paid_file_order()
    store.put(f"orders/{ox}/{mark}", store.json_bytes({"t": 1}), "application/json", upsert=True)
    cx, jx = addon(ox, kx)
    check(f"an order with {mark}: 409 print_not_offered, why {why}", cx == 409 and jx.get("reason") == "print_not_offered" and jx.get("why") == why
          and PR.addon_offer(ox, pay.get_paid(ox)) is None, (cx, jx))
ox, kx, sx = paid_file_order()
store.put(refund_mark(ox, pay.get_paid(ox)["payment_intent"]), store.json_bytes({"refund": "re_x"}), "application/json", upsert=True)
cx, jx = addon(ox, kx)
c, sjx = get(f"/api/order?o={ox}&k={kx}")
check("an order whose payment the admin refunded: why refunded, and its status has no offer", cx == 409 and jx.get("why") == "refunded" and "print_offer" not in sjx, (cx, jx))
ou, ku = draft()
cu, ju = addon(ou, ku)
cw, jw = addon(oa, "0" * 32)
check("an unpaid order: 409 print_not_offered, why not_paid; a wrong key: 403 bad_link (the order link is the authentication)",
      cu == 409 and ju.get("why") == "not_paid" and cw == 403 and jw.get("reason") == "bad_link", (cu, ju, cw, jw))
cp_, jp_ = addon(o24, k24)
check("an order that bought its print at the first checkout: why has_print, and its status has the print and no offer", cp_ == 409 and jp_.get("why") == "has_print"
      and "print_offer" not in get(f"/api/order?o={o24}&k={k24}")[1], (cp_, jp_))
om, km, sm = paid_file_order(market="au")
cm, jm = addon(om, km)
check("an order of a market that offers no prints (au): 409 print_unavailable, why market, no offer in its status",
      cm == 409 and jm.get("reason") == "print_unavailable" and jm.get("why") == "market" and "print_offer" not in get(f"/api/order?o={om}&k={km}")[1], (cm, jm))
sw = PR.set_switch(False, "test", PR.switch_state(fresh=True)["rev"])
fresh_switch()
c_off, j_off = addon(oa, ka)
s_off = get(f"/api/order?o={oa}&k={ka}")[1]
PR.set_switch(True, "test", sw["rev"])
fresh_switch()
mo_env(False)
c_nc, j_nc = addon(oa, ka)
s_nc = get(f"/api/order?o={oa}&k={ka}")[1]
mo_env(True)
fresh_switch()
check("the owner's switch off: 409 print_unavailable why off and no offer; merchOne not configured: why not_configured and no offer; the order's status is otherwise the same",
      c_off == 409 and j_off.get("why") == "off" and "print_offer" not in s_off and c_nc == 409 and j_nc.get("why") == "not_configured" and "print_offer" not in s_nc
      and {k_: v for k_, v in s_off.items() if k_ not in ("download", "ms")} == {k_: v for k_, v in sj.items() if k_ not in ("download", "print_offer", "ms")},
      (j_off, j_nc, sorted(s_off), sorted(sj)))
real_allowed = pay.test_orders_allowed
pay.test_orders_allowed = lambda: False
why_test = PR.addon_problem(oa, pay.get_paid(oa))
pay.test_orders_allowed = real_allowed
check("a payment that does not count here (a test payment where test orders are off): why test_payment", why_test == "test_payment", why_test)
c1, j1 = addon(oa, ka, consent_print=False)
c2, j2 = addon(oa, ka, product="mug")
c3, j3 = addon(oa, ka, cc="US")
c4, j4 = addon(oa, ka, print_shown=1)
c5, j5 = post("/api/checkout", {"addon": {"order": oa, "key": ka}, "consent_print": True, "lang": "lt"})
check("the request's own refusals: the box not ticked 400 print_consent_required, an unknown print why product, a country without prints why country, another price "
      "shown 409 print_price_changed with the server's numbers, no print 400; none of the refusals of this block created a session or a record",
      c1 == 400 and j1.get("reason") == "print_consent_required" and c2 == 409 and j2.get("why") == "product" and c3 == 409 and j3.get("why") == "country"
      and c4 == 409 and j4.get("reason") == "print_price_changed" and j4.get("print") == {"product": "poster50", "country": "LT", "price": 3500, "ship": 849}
      and c5 == 400 and not exists(f"orders/{oa}/print_checkout.json")
      and not [p_ for p_, _h in H.Fake.creates[n_creates:] if p_.get("metadata[kind]") == "print_addon"], (c1, j1, c2, j2, c3, j3, c4, j4, c5, j5))

# --- the session
order_before = raw(f"orders/{oa}/order.json")
paid_before = raw(f"orders/{oa}/paid.json")
exp0 = len(H.Fake.expires)
t_buy = int(time.time())
c, ja = addon(oa, ka, product="acrylic40", cc="DE", lang="lt", print_shown=7900 + 499)
p = H.Fake.creates[-1][0]
sid1 = addon_sid(oa)
check("the add-on checkout answers the Stripe page, the print and the total (the print and its shipping)",
      c == 200 and ja.get("url", "").startswith("https://") and ja.get("print") == {"product": "acrylic40", "country": "DE", "price": 7900, "ship": 499}
      and ja.get("total") == 8399 and ja.get("currency") == "EUR" and ja.get("order") == oa, (c, ja))
check("its Stripe session: the print is the ONLY line item (its price, its Lithuanian name and description, euros), the address form for that one country, one fixed "
      "shipping rate with a delivery estimate, the print's own note above the pay button with the binding order sentence, no discount",
      p.get("mode") == "payment" and p.get("line_items[0][price_data][unit_amount]") == "7900" and p.get("line_items[0][price_data][currency]") == "eur"
      and p.get("line_items[0][price_data][product_data][name]") == PR.product_name("acrylic40", "lt")
      and p.get("line_items[0][price_data][product_data][description]") == PR.ITEM_DESC_PRINT["lt"] and not any(x.startswith("line_items[1]") for x in p)
      and p.get("shipping_address_collection[allowed_countries][0]") == "DE" and "shipping_address_collection[allowed_countries][1]" not in p
      and p.get("shipping_options[0][shipping_rate_data][fixed_amount][amount]") == "499"
      and p.get("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][unit]") == "business_day"
      and p.get("custom_text[submit][message]") == PR.SUBMIT_NOTE_ADDON["lt"] and "prievole sumokėti" in PR.SUBMIT_NOTE_ADDON["lt"]
      and "Vokietija" in p.get("custom_text[shipping_address][message]", "") and not any(x.startswith("discounts") for x in p)
      and p.get("adaptive_pricing[enabled]") == "false", {k_: v for k_, v in p.items() if not k_.startswith("metadata[")})
check("it comes back to the order page with the session named (ps), Stripe's back link says print=cancelled, it lives an hour, and it names the order",
      p.get("success_url") == f"https://snapeyes.com/order?o={oa}&k={ka}&lang=lt&ps={{CHECKOUT_SESSION_ID}}"
      and p.get("cancel_url") == f"https://snapeyes.com/order?o={oa}&k={ka}&lang=lt&print=cancelled" and p.get("client_reference_id") == oa
      and 0 <= int(p.get("expires_at", 0)) - t_buy - PR.ADDON_TTL <= 30 and p.get("payment_intent_data[metadata][kind]") == "print_addon"
      and p.get("payment_intent_data[metadata][order]") == oa, (p.get("success_url"), p.get("cancel_url"), p.get("expires_at")))
meta_a = {k_[9:-1]: v for k_, v in p.items() if k_.startswith("metadata[")}
check("the metadata: kind print_addon, the order and the fingerprint of its key, print, print_sku, print_amount, ship_amount, ship_cc, lang, market, currency, "
      "consent_version, consent_at, and nothing of the artwork's (no eyes, style, amount, plan, voucher or experiment)",
      meta_a.get("kind") == "print_addon" and meta_a.get("order") == oa and meta_a.get("key_sha") == pay.key_sha(ka) and meta_a.get("print") == "acrylic40"
      and meta_a.get("print_sku") == "ACP0400401HP" and meta_a.get("print_amount") == "7900" and meta_a.get("ship_amount") == "499" and meta_a.get("ship_cc") == "DE"
      and meta_a.get("lang") == "lt" and meta_a.get("market") == "eu" and meta_a.get("currency") == "eur" and meta_a.get("consent_version") == pay.CONSENT_VERSION
      and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", meta_a.get("consent_at", ""))
      and set(meta_a) == {"kind", "order", "key_sha", "print", "print_sku", "print_amount", "ship_amount", "ship_cc", "lang", "market", "currency", "consent_version", "consent_at"}, meta_a)
pc = rj(f"orders/{oa}/print_checkout.json") or {}
check("print_checkout.json keeps the checkout: the session, the print, the print box the customer ticked (version, time, the Lithuanian text, its fingerprint); the "
      "order's own record and payment are untouched byte for byte, and no session of the artwork was closed",
      pc.get("session_id") == sid1 and pc.get("sessions") == [sid1] and pc.get("amount") == 8399 and pc.get("currency") == "eur" and pc.get("market") == "eu"
      and pc.get("lang") == "lt" and pc["print"]["product"] == "acrylic40" and pc["print"]["country"] == "DE" and pc["print"]["consent"]["version"] == pay.CONSENT_VERSION
      and pc["print"]["consent"]["text"] == PR.PRINT_CONSENT_TEXT["lt"]
      and pc["print"]["consent"]["text_sha256"] == hashlib.sha256(PR.PRINT_CONSENT_TEXT["lt"].encode("utf-8")).hexdigest()[:16]
      and raw(f"orders/{oa}/order.json") == order_before and raw(f"orders/{oa}/paid.json") == paid_before and len(H.Fake.expires) == exp0, pc)
c, st1 = get(f"/api/checkout?addon={sid1}&o={oa}&k={ka}")
cb, stb = get(f"/api/checkout?addon={sid1}&o={oa}&k={'0' * 32}")
cs, sts = get(f"/api/checkout?addon={sa}&o={oa}&k={ka}")
cg, stg = get(f"/api/checkout?addon=nonsense&o={oa}&k={ka}")
check("the order page's check of the session before it is paid: pending; a wrong key 403; the artwork's own session is not a print session (unknown); nonsense 400; "
      "nothing recorded", c == 200 and st1.get("state") == "pending" and cb == 403 and sts.get("state") == "unknown" and cg == 400
      and not exists(f"orders/{oa}/print_paid.json"), (st1, cb, sts, cg))
c, jb = addon(oa, ka, product="acrylic40", cc="DE", lang="lt")
sid2 = addon_sid(oa)
check("a second press (a double click, a second tab): the earlier session is expired at Stripe first, so only one can be paid; print_checkout.json names both",
      c == 200 and sid2 != sid1 and H.Fake.sessions[sid1]["status"] == "expired" and sid1 in H.Fake.expires[exp0:]
      and (rj(f"orders/{oa}/print_checkout.json") or {}).get("sessions") == [sid1, sid2], (c, jb, H.Fake.sessions[sid1]["status"]))
check("the expired one reads expired for the order page", get(f"/api/checkout?addon={sid1}&o={oa}&k={ka}")[1].get("state") == "expired", "")

# --- paid: the record once, the merge, the confirmation, the step
fix_total(sid2)
H.Fake.emails.clear()
KICKS.clear()
sess_a = pay_with_address(sid2, cc="DE", name="Ona Onaitė", email="spaudinys@example.com")
check("the artwork's own paths never take the add-on's session for the order's payment: session_matches refuses it and record_paid raises",
      pay.session_matches(sess_a, oa, rj(f"orders/{oa}/order.json")) is False and pay.session_ours(sess_a, oa, rj(f"orders/{oa}/order.json")) is True, "")
try:
    pay.record_paid(oa, rj(f"orders/{oa}/order.json"), sess_a, "test")
    raised = False
except pay.PayError:
    raised = True
check("... record_paid refuses it whoever asks (PayError), and no extra payment of the artwork was stored", raised
      and not [f_ for f_ in os.listdir(os.path.join(STORE, "orders", oa)) if f_.startswith("extra_payment_")], raised)
c, jw = webhook(sess_a)
pj = rj(f"orders/{oa}/print_paid.json") or {}
ppa = pj.get("print") or {}
check("the webhook records the print's payment apart: print_paid.json with the session, the payment, the amount (the print and its shipping), euros, the time, the "
      "buyer's e-mail and the print (product, SKU, price, shipping, the name and address Stripe collected, the print box), no mismatch",
      c == 200 and jw.get("print") is True and jw.get("state") == "new" and pj.get("paid") is True and pj.get("session_id") == sid2
      and pj.get("payment_intent") == sess_a["payment_intent"] and pj.get("amount_total") == 8399 and pj.get("currency") == "eur" and pj.get("livemode") is False
      and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", pj.get("at", "")) and pj.get("email") == "spaudinys@example.com" and pj.get("source") == "webhook"
      and ppa.get("product") == "acrylic40" and ppa.get("sku") == "ACP0400401HP" and ppa.get("price") == 7900 and ppa.get("ship") == 499 and ppa.get("country") == "DE"
      and ppa.get("name") == "Ona Onaitė" and ppa["address"]["country"] == "DE" and ppa["consent"]["text"] == PR.PRINT_CONSENT_TEXT["lt"] and "mismatch" not in ppa, (c, jw, pj))
paid_a = pay.get_paid(oa)
check("paid.json is not touched (byte for byte), and pay.get_paid merges the print in: print and print_addon {session_id, payment_intent, amount_total, at, livemode, "
      "email}; the record's own amount stays the artwork's",
      raw(f"orders/{oa}/paid.json") == paid_before and paid_a.get("print") == ppa and paid_a.get("print_addon") == {"session_id": sid2, "payment_intent": sess_a["payment_intent"],
      "amount_total": 8399, "at": pj["at"], "livemode": False, "email": "spaudinys@example.com"} and paid_a["amount_total"] == json.loads(paid_before)["amount_total"]
      and paid_a["session_id"] == sa, paid_a.get("print_addon"))
check("print.json is waiting, the order is in the print index, and the server's step for the print was asked for (the artwork is delivered: nobody else would ask)",
      (rj(f"orders/{oa}/print.json") or {}).get("state") == "waiting" and exists(f"cleanup/print/{oa}.json") and (oa, "print") in KICKS, (rj(f"orders/{oa}/print.json"), KICKS))
conf = [m for m, _i in H.Fake.emails if m.get("subject") == PR.ADDON_CONF["lt"]["subject"].format(order=oa)]
txt = conf[0]["text"] if conf else ""
check("the customer gets the print's own confirmation once, in the ORDER's language, to the address of that payment: the print, the shipping with the country, the "
      "delivery address, the total with the no VAT sentence, production right away, the producer, the 7 days, the print box quoted, the order page, the terms in full",
      len(conf) == 1 and conf[0]["to"] == ["spaudinys@example.com"] and PR.product_name("acrylic40", "lt") in txt and "Vokietija, 4,99" in txt
      and "Ona Onaitė, Gedimino pr. 1" in txt and pay.price_text(8399, "lt", "eur") in txt and "PVM" in txt and "iš karto" in txt and "Picanova GmbH" in txt
      and "per 7 dienas" in txt and PR.PRINT_CONSENT_TEXT["lt"] in txt and f"/order?o={oa}&k={ka}&lang=lt" in txt
      and PACK["docs"]["lt"]["terms"]["text"][:200] in txt and PACK["docs"]["lt"]["withdrawal"]["text"][:200] not in txt and not re.search(DASH, txt), txt[:1500])
note = [m for m, _i in H.Fake.emails if "a print for order" in m.get("subject", "") and oa in m.get("subject", "")]
check("the owner gets one note of the sale (the print, where it goes, the payment)", len(note) == 1 and "acrylic40 to DE" in note[0]["text"]
      and sess_a["payment_intent"] in note[0]["text"], note[:1])
paid_bytes = raw(f"orders/{oa}/print_paid.json")
c, jw2 = webhook(sess_a)
check("the same event again (Stripe retries): 200, state known, print_paid.json byte for byte the same, no second confirmation, no second note",
      c == 200 and jw2.get("state") == "known" and raw(f"orders/{oa}/print_paid.json") == paid_bytes
      and len([m for m, _i in H.Fake.emails if m.get("subject") == PR.ADDON_CONF["lt"]["subject"].format(order=oa)]) == 1
      and len([m for m, _i in H.Fake.emails if "a print for order" in m.get("subject", "")]) == 1, (c, jw2))
MO.creates.clear()
r = PR.step(oa, rj(f"orders/{oa}/order.json"), pay.get_paid(oa))
pl = MO.creates[-1] if MO.creates else {}
check("fulfilment is the code it was: the step sends the print to merchOne once (external id = the order, the SKU, the name and the address of the add-on's payment), "
      "a second step does nothing", r == "created" and len(MO.creates) == 1 and pl.get("external_id") == oa and pl["items"][0]["product_sku"] == "ACP0400401HP"
      and pl["shipping"]["lastname"] == "Onaitė" and pl["shipping"]["country"] == "DE" and pl.get("is_test") is True
      and PR.step(oa, rj(f"orders/{oa}/order.json"), pay.get_paid(oa)) == "done" and len(MO.creates) == 1, (r, pl))
c, stp = get(f"/api/checkout?addon={sid2}&o={oa}&k={ka}")
c2, sja = get(f"/api/order?o={oa}&k={ka}")
check("the order page's check of the recorded session: paid, with the print block; the order's status has the print (sent) and no offer any more",
      stp.get("state") == "paid" and (stp.get("print") or {}).get("state") == "sent" and stp["print"]["product"] == "acrylic40"
      and (sja.get("print") or {}).get("state") == "sent" and "print_offer" not in sja, (stp, sja.get("print")))
n_c = len(H.Fake.creates)
c, jn = addon(oa, ka)
check("a second print for an order that has one is refused: 409 print_not_offered, why has_print, no session is made",
      c == 409 and jn.get("reason") == "print_not_offered" and jn.get("why") == "has_print" and len(H.Fake.creates) == n_c, (c, jn))
oid_a = PR.record(oa)["merchone_id"]
MO.orders[oid_a]["shipments"] = [{"tracking_number": "777", "tracking_url": "https://tracking.dpd.de/777", "shipping_method": {"name": "DPD"}}]
H.Fake.emails.clear()
PR.refresh(oa)
ship_a = [m for m, _i in H.Fake.emails if m.get("subject") == PR.SHIPPED["lt"]["subject"]]
check("the shipping e-mail of an add-on print goes to the address of the payment that bought it, in the order's language",
      PR.record(oa)["state"] == "shipped" and len(ship_a) == 1 and ship_a[0]["to"] == ["spaudinys@example.com"], ship_a[:1])

# --- recorded by the order page's own check, in another language than the order's
oc, kc, sc = paid_file_order(lang="de")
c, jc = addon(oc, kc, product="canvas40", cc="AT", lang="lt")
sidc = addon_sid(oc)
pcr = H.Fake.creates[-1][0]
fix_total(sidc)
sess_c = pay_with_address(sidc, cc="AT", name="Max Muster")
sess_c["customer_details"] = {}          # Stripe gave no e-mail with this payment: the print's e-mails go to the order's address
H.Fake.emails.clear()
KICKS.clear()
c, stc = get(f"/api/checkout?addon={sidc}&o={oc}&k={kc}")
pjc = rj(f"orders/{oc}/print_paid.json") or {}
conf_c = [m for m, _i in H.Fake.emails if m.get("subject") == PR.ADDON_CONF["de"]["subject"].format(order=oc)]
check("the webhook has not arrived: the order page's check of the session records the payment itself (source order_page), answers paid with the print block (preparing) "
      "and asks for the step", c == 200 and stc.get("state") == "paid" and (stc.get("print") or {}).get("state") == "preparing" and pjc.get("source") == "order_page"
      and pjc.get("session_id") == sidc and (oc, "print") in KICKS, (stc, pjc.get("source"), KICKS))
check("the page was Lithuanian, the order is German: the Stripe page and the recorded box are Lithuanian, the confirmation is German and quotes the Lithuanian box "
      "as it was ticked; without an e-mail of its own on the payment it goes to the order's address",
      pcr.get("locale") == "lt" and pcr.get("custom_text[submit][message]") == PR.SUBMIT_NOTE_ADDON["lt"] and pjc["print"]["consent"]["lang"] == "lt"
      and len(conf_c) == 1 and "Ihr Druck" in conf_c[0]["text"] and "Österreich, 6,99" in conf_c[0]["text"] and PR.PRINT_CONSENT_TEXT["lt"] in conf_c[0]["text"]
      and "sofort in die Produktion" in conf_c[0]["text"] and conf_c[0]["to"] == ["kunde@example.com"], (pcr.get("locale"), conf_c[:1]))
bytes_c = raw(f"orders/{oc}/print_paid.json")
c, jwc = webhook(sess_c)
check("the late webhook finds it recorded: known, nothing rewritten, no second confirmation", c == 200 and jwc.get("state") == "known"
      and raw(f"orders/{oc}/print_paid.json") == bytes_c and len([m for m, _i in H.Fake.emails if m.get("subject") == PR.ADDON_CONF["de"]["subject"].format(order=oc)]) == 1, (c, jwc))

# --- the confirmation that cannot go out for a moment, a session that is not the order's
od, kd, sd = paid_file_order()
addon(od, kd)
sidd = addon_sid(od)
fix_total(sidd)
sess_d = pay_with_address(sidd, cc="LT")
H.Fake.emails.clear()
H.Fake.fail_mail = [503, 503]          # the owner's note, then the customer's confirmation
c, jd = webhook(sess_d)
recorded_d = exists(f"orders/{od}/print_paid.json")
c2, jd2 = webhook(sess_d)
conf_d = [m for m, _i in H.Fake.emails if m.get("subject") == PR.ADDON_CONF["en"]["subject"].format(order=od)]
check("the confirmation could not go out for a moment: the payment is recorded all the same and the webhook answers 503 so Stripe retries; the retry sends it, once",
      c == 503 and jd.get("reason") == "mail_retry" and recorded_d and c2 == 200 and jd2.get("state") == "known" and len(conf_d) == 1
      and f"{PR.product_name('poster50', 'en')}, €35.00" in conf_d[0]["text"] and "Lithuania, €8.49" in conf_d[0]["text"] and "right away" in conf_d[0]["text"], (c, jd, c2, jd2, len(conf_d)))
oe, ke, se = paid_file_order()
addon(oe, ke)
side = addon_sid(oe)
fix_total(side)
sess_e = dict(pay_with_address(side, cc="LT"))
forged = dict(sess_e, metadata=dict(sess_e["metadata"], key_sha="0" * 32))
unpaid = dict(sess_e, status="open", payment_status="unpaid")
c, jf = webhook(forged)
c2, ju2 = webhook(unpaid)
check("a print session whose key fingerprint is not the order's is ignored (nothing recorded); one that is not paid yet waits",
      c == 200 and jf.get("ignored") == "session does not match" and c2 == 200 and ju2.get("state") == "awaiting_payment" and not exists(f"orders/{oe}/print_paid.json"), (jf, ju2))

# --- an amount nobody priced
H.Fake.sessions[side]["amount_total"] += 100
H.Fake.emails.clear()
KICKS.clear()
MO.creates.clear()
c, jm = webhook(H.Fake.sessions[side])
pje = rj(f"orders/{oe}/print_paid.json") or {}
check("a paid amount other than the print and its shipping: recorded as it came with mismatch ['amount'], the print HELD for the owner (told), nothing asked of "
      "merchOne, by the step or by the owner's chain",
      c == 200 and pje.get("amount_total") == 3500 + 849 + 100 and pje["print"].get("mismatch") == ["amount"] and (rj(f"orders/{oe}/print.json") or {}).get("state") == "held"
      and any("is held" in m.get("subject", "") and oe in m.get("subject", "") for m, _i in H.Fake.emails) and (oe, "print") not in KICKS
      and PR.step(oe, rj(f"orders/{oe}/order.json"), pay.get_paid(oe)) == "held" and not MO.creates, (c, jm, pje.get("print", {}).get("mismatch"), KICKS))
held_e = next((m.get("text", "") for m, _i in H.Fake.emails if "is held" in m.get("subject", "") and oe in m.get("subject", "")), "")
H.Fake.emails.clear()
o_h, k_h, s_h = paid_print_order(cc="LT", product="acrylic30", mismatch_cc="LV")
held_first = next((m.get("text", "") for m, _i in H.Fake.emails if "is held" in m.get("subject", "") and o_h in m.get("subject", "")), "")
check("the held note of a print bought later sends the owner to the admin page's refund of that payment (named: the server sees it and cancels the print), not to "
      "the Stripe Dashboard; a print of the artwork's own checkout keeps the Dashboard (its money is a part of the order's payment)",
      "Spaudinio mokėjimas" in held_e and sess_e["payment_intent"] in held_e and "Do not refund it in the Stripe Dashboard" in held_e and "the amount paid" in held_e
      and "refund the print in the Stripe Dashboard." in held_first and "Spaudinio mokėjimas" not in held_first, (held_e, held_first))

# --- paid twice
og, kg, sg = paid_file_order()
addon(og, kg, product="poster50", cc="LT")
sg1 = addon_sid(og)
addon(og, kg, product="poster50", cc="LT")
sg2 = addon_sid(og)
H.Fake.sessions[sg1]["status"] = "open"          # as if the first tab's session had not been closed in time: both get paid
fix_total(sg1)
fix_total(sg2)
s2 = pay_with_address(sg2, cc="LT")
s1 = pay_with_address(sg1, cc="LT")
H.Fake.emails.clear()
c, jg2 = webhook(s2)
bytes_g = raw(f"orders/{og}/print_paid.json")
c1_, jg1 = webhook(s1)
xp = [f_ for f_ in os.listdir(os.path.join(STORE, "orders", og)) if f_.startswith("extra_payment_")]
xr = rj(f"orders/{og}/{xp[0]}") if xp else {}
twice = [m for m, _i in H.Fake.emails if "was paid twice" in m.get("subject", "") and og in m.get("subject", "")]
check("two add-on sessions of one order paid anyway: the first is the order's print, the second is stored as an extra payment (as pay.extra_payment does) and the "
      "owner told to refund it; print_paid.json is not rewritten",
      c == 200 and jg2.get("state") == "new" and c1_ == 200 and jg1.get("state") == "extra" and raw(f"orders/{og}/print_paid.json") == bytes_g and len(xp) == 1
      and xr.get("extra_payment") is True and xr.get("paid") is False and xr.get("kind") == "print_addon" and xr.get("session_id") == sg1
      and xr.get("first_session") == sg2 and xr.get("payment_intent") == s1["payment_intent"] and len(twice) == 1 and s1["payment_intent"] in twice[0]["text"], (jg2, jg1, xr))
c, jg3 = webhook(s1)
MO.creates.clear()
deliver(og)
rg = PR.step(og, rj(f"orders/{og}/order.json"), pay.get_paid(og))
check("... replayed: still one extra payment and one note; the print is made ONCE (one merchOne order); the order page's check of the second session says extra",
      jg3.get("state") == "extra" and len([f_ for f_ in os.listdir(os.path.join(STORE, "orders", og)) if f_.startswith("extra_payment_")]) == 1
      and len([m for m, _i in H.Fake.emails if "was paid twice" in m.get("subject", "")]) == 1 and rg == "created" and len(MO.creates) == 1
      and get(f"/api/checkout?addon={sg1}&o={og}&k={kg}")[1].get("state") == "extra", (jg3, rg, len(MO.creates)))
oh, kh, sh = paid_file_order()
addon(oh, kh)
sh1 = addon_sid(oh)
fix_total(sh1)
pay_with_address(sh1, cc="LT")
n_c = len(H.Fake.creates)
c, jh = addon(oh, kh)
check("a new checkout that finds the earlier add-on session paid records it (source checkout) and makes no second session: 409 print_not_offered, why has_print",
      c == 409 and jh.get("why") == "has_print" and (rj(f"orders/{oh}/print_paid.json") or {}).get("source") == "checkout" and len(H.Fake.creates) == n_c, (c, jh))
sess_x = dict(sess_e, id="cs_test_" + "f" * 24, metadata=dict(sess_e["metadata"], order=o24, key_sha=pay.key_sha(k24)), payment_intent="pi_test_addonx1")
c, jx2 = webhook(sess_x)
check("an add-on payment for an order that bought its print at the first checkout is an extra payment too: paid.json's own print stays the order's print",
      jx2.get("state") == "extra" and pay.get_paid(o24).get("print_addon") is None and not exists(f"orders/{o24}/print_paid.json")
      and any(f_.startswith("extra_payment_") for f_ in os.listdir(os.path.join(STORE, "orders", o24))), jx2)

# --- the refunds
oi, ki, si = paid_file_order()
addon(oi, ki, product="poster50", cc="LT")
sidi = addon_sid(oi)
fix_total(sidi)
sess_i = pay_with_address(sidi, cc="LT")
webhook(sess_i)
PR.step(oi, rj(f"orders/{oi}/order.json"), pay.get_paid(oi))
oid_i = PR.record(oi)["merchone_id"]
paid_i = pay.get_paid(oi)
ov = ops.ACTIONS["order"]({"order": oi}, WHO)
check("the admin's order detail lists the print's payment beside the order's (kind print, its own amount), and the print block says it was bought after the artwork",
      [(p_["kind"], p_["payment_intent"], p_["amount"]) for p_ in ov["payments"]] == [("order", paid_i["payment_intent"], paid_i["amount_total"]),
                                                                                     ("print", sess_i["payment_intent"], 3500 + 849)]
      and (ov.get("print") or {}).get("addon") is True and ov["print"]["state"] == "created", ov.get("payments"))
row = ops.order_row(oi)
check("the admin's order row: the amount is the artwork's, nothing of the print is taken off it (print_amount 0), the add-on's amount stands apart; a price test and "
      "the artwork's confirmation never count the add-on's print",
      row["amount"] == paid_i["amount_total"] and row["print_amount"] == 0 and row["print_addon"] == 3500 + 849 and row["print"]["product"] == "poster50"
      and abtest.paid_extra(paid_i) == 0 and abtest.paid_extra(pay.get_paid(o24)) == 3500 + 849
      and PR.amend_confirmation([("rows", [("a", "1"), ("b", "2"), ("c", "3")])], "en", paid_i) == [("rows", [("a", "1"), ("b", "2"), ("c", "3")])], row)
e = None
try:
    ops.ACTIONS["refund"]({"order": oi, "payment_intent": "pi_test_notmine01", "confirm": oi}, WHO)
except store.Answer as x:
    e = x
r_art = ops.ACTIONS["refund"]({"order": oi, "payment_intent": paid_i["payment_intent"], "confirm": oi}, WHO)
check("the artwork's payment refunded alone leaves the add-on's print alone: no print result, nothing cancelled at merchOne, the print still due and created; a "
      "payment that is not the order's is refused",
      e is not None and e.body.get("reason") == "unknown_payment" and r_art.get("result") == "succeeded" and "print" not in r_art and oid_i not in MO.deletes
      and PR.record(oi)["state"] == "created" and PR.due(oi, pay.get_paid(oi)) == "" and REFUNDS[-1].get("payment_intent") == paid_i["payment_intent"], (r_art, e and e.body))
r_pr = ops.ACTIONS["refund"]({"order": oi, "payment_intent": sess_i["payment_intent"], "confirm": oi}, WHO)
ov2 = ops.ACTIONS["order"]({"order": oi}, WHO)
check("the add-on's payment refunded cancels the print at merchOne, as refunding an order with a print does; both payments read refunded in the order detail",
      r_pr.get("print") == {"result": "canceled"} and oid_i in MO.deletes and PR.record(oi)["state"] == "canceled" and REFUNDS[-1].get("payment_intent") == sess_i["payment_intent"]
      and all(p_["refunded"] for p_ in ov2["payments"]), (r_pr, ov2.get("payments")))
oj, kj, sj_ = paid_file_order()
addon(oj, kj)
sidj = addon_sid(oj)
fix_total(sidj)
sess_j = pay_with_address(sidj, cc="LT")
webhook(sess_j)
store.put(f"orders/{oj}/refunded.json", store.json_bytes({"t": 1}), "application/json", upsert=True)
due_art = PR.due(oj, pay.get_paid(oj))
r_j = ops.ACTIONS["refund"]({"order": oj, "payment_intent": sess_j["payment_intent"], "confirm": oj}, WHO)
MO.creates.clear()
st_j = PR.step(oj, rj(f"orders/{oj}/order.json"), pay.get_paid(oj))
check("refunded.json marks the artwork's payment: an add-on print stays due; the add-on's payment refunded before the print was sent: not_sent, and the next step "
      "cancels it instead of sending it", due_art == "" and r_j.get("print") == {"result": "not_sent"} and PR.due(oj, pay.get_paid(oj)) == "refunded"
      and st_j == "done" and PR.record(oj)["state"] == "canceled" and not MO.creates, (due_art, r_j, st_j))

# --- what is kept
check("the add-on's checkout, its payment and its confirmation mark are kept with the accounting files when an order's files are erased",
      all(pay.kept_record(f"orders/x/{n_}") for n_ in ("print_checkout.json", "print_paid.json", "print_confirmation.json")) and not pay.kept_record("orders/x/print_poster50.jpg"), "")
gone, total_ = pay.erase_files(oc, "test", yes=True, out=lambda s: None)
check("... erased: print_paid.json, print_checkout.json and print_confirmation.json stay beside paid.json, the artwork goes",
      all(exists(f"orders/{oc}/{n_}") for n_ in ("paid.json", "print_paid.json", "print_checkout.json", "print_confirmation.json", "print.json"))
      and not exists(f"orders/{oc}/artwork_test.jpg") and PR.addon_problem(oc, pay.get_paid(oc)) == "has_print", (gone, total_))
check("merge_addon: a record with a print of its own keeps it; an add-on record that is not paid, or names no print, changes nothing",
      pay.merge_addon({"paid": True, "print": {"product": "a"}}, {"paid": True, "print": {"product": "b"}}) == {"paid": True, "print": {"product": "a"}}
      and pay.merge_addon({"paid": True}, {"paid": False, "print": {"product": "b"}}) == {"paid": True} and pay.merge_addon({"paid": True}, None) == {"paid": True}
      and pay.merge_addon({"paid": True}, {"paid": True, "print": {}}) == {"paid": True}, "")

# --- the "ready" e-mail
ol, kl, sl = paid_file_order(lang="lt")
paid_l = pay.get_paid(ol)
s_on, t_on, h_on = pay.ready_mail(ol, paid_l, kl, checked=False)
i_order, i_sec, i_q = t_on.find(f"Užsakymas: {ol}"), t_on.find(pay.READY_PRINT["lt"][0]), t_on.find("Turite klausimų?")
check("the ready e-mail of an order that can buy a print now has one short section after the order number: the heading and the sentence that the artwork can be "
      "ordered as a print from the order page, no price",
      pay.READY_PRINT["lt"][1] in t_on and 0 < i_order < i_sec < i_q and pay.READY_PRINT["lt"][0] in h_on and "€" not in pay.READY_PRINT["lt"][1]
      and not re.search(r"\d", pay.READY_PRINT["lt"][1]), t_on)
t_print = pay.ready_mail(o24, pay.get_paid(o24), k24, checked=False)[1]
t_released = pay.ready_mail(ob, pay.get_paid(ob), kb)[1]          # held, then released by the owner: eligible, and its e-mail (the release sends it) has the section
sw = PR.set_switch(False, "test", PR.switch_state(fresh=True)["rev"])
fresh_switch()
t_off = pay.ready_mail(ol, paid_l, kl, checked=False)[1]
PR.set_switch(True, "test", sw["rev"])
fresh_switch()
t_au = pay.ready_mail(om, pay.get_paid(om), km)[1]
t_ref = pay.ready_mail(ox, pay.get_paid(ox), kx)[1]
check("... and not the e-mail of an order that has a print, of one while the switch is off, of a market without prints, or of a refunded order: those are the e-mails "
      "they were", all(pay.READY_PRINT[l_][0] not in t_ for l_ in ("en", "lt") for t_ in (t_print, t_off, t_au, t_ref)) and pay.READY_PRINT["en"][0] in t_released, (t_off, t_au))
sections = {}
for l_ in PR.LANGS:
    sections[l_] = pay.ready_mail(ol, dict(paid_l, spec=dict(paid_l["spec"], lang=l_)), kl, checked=False, offer=True)[1]
plain_l = {l_: pay.ready_mail(ol, dict(paid_l, spec=dict(paid_l["spec"], lang=l_)), kl, checked=False, offer=False)[1] for l_ in PR.LANGS}
check("the section in the eight languages: each its own heading and sentence, no price, no digit, no dash; without it the e-mail is the same text less that section",
      set(pay.READY_PRINT) == set(PR.LANGS) and len({v for v in pay.READY_PRINT.values()}) == 8
      and all(pay.READY_PRINT[l_][0] in sections[l_] and pay.READY_PRINT[l_][1] in sections[l_] for l_ in PR.LANGS)
      and all(not re.search(r"[\d€]", " ".join(pay.READY_PRINT[l_])) and not re.search(DASH, " ".join(pay.READY_PRINT[l_])) for l_ in PR.LANGS)
      and all(sections[l_].replace(f"{pay.READY_PRINT[l_][0]}\n{pay.READY_PRINT[l_][1]}\n\n", "") == plain_l[l_] for l_ in PR.LANGS),
      [l_ for l_ in PR.LANGS if sections[l_].replace(f"{pay.READY_PRINT[l_][0]}\n{pay.READY_PRINT[l_][1]}\n\n", "") != plain_l[l_]])
H.Fake.emails.clear()
res_l = maker.ready_mail_once(ol, rj(f"orders/{ol}/order.json"), paid_l, False)
sent_l = [m for m, _i in H.Fake.emails if m.get("subject") == "Jūsų SnapEyes kūrinys paruoštas"]
check("the server's own ready e-mail (maker.ready_mail_once) carries it for an eligible order", res_l == "sent" and len(sent_l) == 1
      and pay.READY_PRINT["lt"][1] in sent_l[0]["text"], (res_l, sent_l[:1]))

# --- the add-on's confirmation in the eight languages
mails8 = {}
for l_ in PR.LANGS:
    mails8[l_] = PR.addon_mail(oi, dict(paid_i, spec=dict(paid_i["spec"], lang=l_)), ki, PACK, PACK["docs"][l_])
check("the add-on's confirmation in the eight languages: eight different subjects with the order number, the print's name, the country and the prices in that "
      "language, the producer, the order page, the terms of that language in full, no dash in our own words",
      len({mails8[l_][0] for l_ in PR.LANGS}) == 8 and all(oi in mails8[l_][0] for l_ in PR.LANGS)
      and all(PR.product_name("poster50", l_) in mails8[l_][1] and PR.country_name("LT", l_) in mails8[l_][1] and pay.price_text(3500 + 849, l_, "eur") in mails8[l_][1]
              and "Picanova GmbH" in mails8[l_][1] and f"/order?o={oi}&k={ki}&lang={l_}" in mails8[l_][1] and PACK["docs"][l_]["terms"]["text"][:200] in mails8[l_][1]
              and PR.ADDON_CONF[l_]["p1"].split("{time}")[0] in mails8[l_][1] and PR.time_text("poster50", "LT", l_) in mails8[l_][1] for l_ in PR.LANGS)
      and not re.search(DASH, json.dumps([PR.ADDON_CONF, PR.SUBMIT_NOTE_ADDON], ensure_ascii=False))
      and len(set(PR.SUBMIT_NOTE_ADDON.values())) == 8 and set(PR.SUBMIT_NOTE_ADDON) == set(PR.ADDON_CONF) == set(PR.LANGS),
      [l_ for l_ in PR.LANGS if PR.product_name("poster50", l_) not in mails8[l_][1] or pay.price_text(3500 + 849, l_, "eur") not in mails8[l_][1]])

# ============================================================================================ 11. the acrylic block
section("11. the acrylic block 20 x 20 cm (2026-11-24): a fourth kind, which stands on a shelf; the canvas at 79 EUR")
BLOCK_SKU = "ABS0200201"
bk, brec = PR.product("block20"), PR.sku_rec(BLOCK_SKU) or {}
check("the block in the tables: kind block, 20 cm, merchOne's SKU ABS0200201 (blueprint 18, a design area of 200 mm and a print file of 204 mm: 2 mm of trim a side), "
      "79 EUR as the canvas now; its name with its size in the eight languages, eight different names",
      bk == {"id": "block20", "kind": "block", "cm": 20, "sku": BLOCK_SKU, "price": 7900, "on": 1} and PR.product("canvas40")["price"] == 4900
      and brec.get("blueprint") == 18 and brec.get("design_mm") == [200.0, 200.0] and brec.get("file_mm") == [204.0, 204.0] and brec.get("trim_mm") == 2.0
      and PR.product_name("block20", "en") == "Acrylic block 20\u00a0×\u00a020\u00a0cm" and PR.product_name("block20", "lt") == "Akrilo blokas 20\u00a0×\u00a020\u00a0cm"
      and len({PR.product_name("block20", l_) for l_ in PR.LANGS}) == 8 and len({PR.PRINT_NAMES["kinds"]["block"][l_] for l_ in PR.LANGS}) == 8
      and not re.search(DASH, json.dumps(PR.PRINT_NAMES["kinds"], ensure_ascii=False)), (bk, brec, [PR.product_name("block20", l_) for l_ in PR.LANGS]))
bgeo = PR.file_geometry(BLOCK_SKU, 4096)
ab = np.zeros((300, 450, 3), dtype=np.uint8)
ab[:, :, 1] = 60
ab[100:200, 200:250] = 240
bb = io.BytesIO()
Image.fromarray(ab).save(bb, "PNG")
bdata, binfo = PR.make_print_file(bb.getvalue(), BLOCK_SKU)
bpic = np.asarray(Image.open(io.BytesIO(bdata)).convert("RGB"))
check("its print file: the design area at 200 dpi (1575 px for 200 mm) with the trim around it (1607 px), never under merchOne's minimum (567 px at 72 dpi); a 3:2 "
      "artwork is centred on the square and its ground continued to the edges",
      bgeo == (1607, 1575, 200) and bgeo[1] >= brec.get("design_px", [9999])[0] == 567 and brec.get("file_px") == [579, 579] and brec.get("dpi") == 72
      and bpic.shape[0] == bpic.shape[1] == binfo["width"] and binfo["art"][0] == binfo["design"] and abs(int(bpic[5, 5, 1]) - 60) < 12
      and abs(int(bpic[bpic.shape[0] // 2, bpic.shape[1] // 2, 1]) - 240) < 20, (bgeo, binfo))
mgb = {cc_: PR.margin("block20", cc_) for cc_ in PR.countries()}
mgc = {cc_: PR.margin("canvas40", cc_) for cc_ in PR.countries()}
check("what they earn after merchOne's price and shipping with VAT and the fee: the block at least the floor in every country (38.78 EUR to Lithuania, 38.96 to "
      "Germany), the canvas at 79 EUR 40.81 to Lithuania; the block ships at the price of the other small prints (4.99 to Germany, 8.49 to Lithuania)"
      " - 1124, the final list: the canvas without an outer frame at 49 EUR earns 26.85 EUR to Lithuania",
      min(mgb.values()) >= PR.PRINT_OFFER["margin_floor"] and mgb["LT"] == 3878 and mgb["DE"] == 3896 and mgc["LT"] == 2685 == min(mgc.values())
      and PR.shipping("DE", "block20") == 499 and PR.shipping("LT", "block20") == 849 and len([cc_ for cc_ in PR.countries() if PR.shipping(cc_, "block20")]) == 27,
      (min(mgb.values()), mgb["LT"], mgb["DE"], mgc["LT"], min(mgc.values())))
okb, kkb, _skb = paid_file_order(lang="lt")
c, sjb = get(f"/api/order?o={okb}&k={kkb}")
pob = (sjb.get("print_offer") or {}).get("products") or []
c, jbk = addon(okb, kkb, product="block20", cc="LT", lang="lt", print_shown=7900 + 849)
pbk = H.Fake.creates[-1][0]
check("the order page's offer names the block last (kind block, 20 cm, 79 EUR, its shipping per country), and a block bought after the artwork has a Stripe session "
      "of its own: the only line item, its Lithuanian name, 79 EUR, the shipping to Lithuania, the SKU in the metadata",
      # 1125: the keyring is the last one now; the block is found by its id
      [x["id"] for x in pob][-2:] == ["block20", "keyring"] and pob[-2]["kind"] == "block" and pob[-2]["cm"] == 20 and pob[-2]["price"] == 7900 and pob[-2]["ship"]["LT"] == 849
      and c == 200 and jbk.get("print") == {"product": "block20", "country": "LT", "price": 7900, "ship": 849} and jbk.get("total") == 8749
      and pbk.get("line_items[0][price_data][product_data][name]") == PR.product_name("block20", "lt") == "Akrilo blokas 20\u00a0×\u00a020\u00a0cm"
      and pbk.get("line_items[0][price_data][unit_amount]") == "7900" and not any(x.startswith("line_items[1]") for x in pbk)
      and pbk.get("shipping_options[0][shipping_rate_data][fixed_amount][amount]") == "849" and pbk.get("metadata[print]") == "block20"
      and pbk.get("metadata[print_sku]") == BLOCK_SKU and pbk.get("metadata[kind]") == "print_addon", (c, jbk, pob[-1:]))
sidbk = addon_sid(okb)
fix_total(sidbk)
H.Fake.emails.clear()
sess_bk = pay_with_address(sidbk, cc="LT", name="Ona Onaitė", email="blokas@example.com")
c, jwb = webhook(sess_bk)
paid_bk = pay.get_paid(okb)
MO.creates.clear()
rbk = PR.step(okb, rj(f"orders/{okb}/order.json"), paid_bk)
cur_bk = PR.record(okb) or {}
plb = MO.creates[-1] if MO.creates else {"items": [{}]}
fbk = cur_bk.get("file") or {}
conf_bk = [m for m, _i in H.Fake.emails if m.get("subject") == PR.ADDON_CONF["lt"]["subject"].format(order=okb)]
check("paid: the print is on record with the block's kind and size and no mismatch, the confirmation names it, and the step sends ONE order to merchOne with the "
      "block's SKU and a square print file of the SKU's size (print_block20.jpg), as for every other print",
      c == 200 and (paid_bk.get("print") or {}).get("product") == "block20" and paid_bk["print"].get("kind") == "block" and paid_bk["print"].get("cm") == 20
      and paid_bk["print"].get("sku") == BLOCK_SKU and "mismatch" not in paid_bk["print"] and (rj(f"orders/{okb}/print_paid.json") or {}).get("amount_total") == 8749
      and len(conf_bk) == 1 and PR.product_name("block20", "lt") in conf_bk[0]["text"]
      and rbk == "created" and cur_bk.get("state") == "created" and len(MO.creates) == 1 and plb["items"][0].get("product_sku") == BLOCK_SKU
      and plb["items"][0].get("quantity") == 1 and plb.get("shipping", {}).get("country") == "LT" and plb.get("is_test") is True
      and fbk.get("path") == f"orders/{okb}/print_block20.jpg" and exists(fbk.get("path") or "x") and fbk.get("width") == PR.file_geometry(BLOCK_SKU, 2048)[0] == 1607
      and Image.open(os.path.join(STORE, *fbk["path"].split("/"))).size == (1607, 1607), (c, jwb, rbk, cur_bk, plb.get("items")))
stb = get(f"/api/order?o={okb}&k={kkb}")[1]
check("the order page then shows the block as the order's print (its product, kind and size) and offers no second one",
      (stb.get("print") or {}).get("product") == "block20" and stb["print"].get("kind") == "block" and stb["print"].get("cm") == 20 and "print_offer" not in stb, stb.get("print"))

# ============================================================================================ 12. the final list of 2026-11-24
section("12. the final list (2026-11-24): the canvas without an outer frame, glossy metal, the small block, and the keyring that is ready and not offered")
check("the canvas is the unframed one (the SKUs without the black floating frame; merchOne's prices 17.30 and 26.38 EUR), 40 cm at 49 EUR and 60 cm at 69 EUR; its "
      "name in no language says black or floating, and its line says ready to hang and without an outer frame; no SKU with a floating frame is left in the rate table",
      [(PR.product(x)["sku"], PR.product(x)["price"], PR.sku_rec(PR.product(x)["sku"])["cost"]) for x in ("canvas40", "canvas60")]
      == [("CVS0400401LMF2HC", 4900, 1730), ("CVS0600601LMF2HC", 6900, 2638)]
      and PR.PRINT_NAMES["kinds"]["canvas"]["en"] == "Canvas on a wooden stretcher frame" and PR.PRINT_NAMES["kinds"]["canvas"]["lt"] == "Drobė ant medinio porėmio"
      and not re.search(r"black|floating|schwarz|Schattenfuge|juod|fekete|crn|must|meln", json.dumps([PR.PRINT_NAMES["kinds"]["canvas"], PR.PRINT_NAMES["about"]["canvas"]], ensure_ascii=False), re.I)
      and "ready to hang, without an outer frame" in PR.PRINT_NAMES["about"]["canvas"]["en"] and "be išorinio rėmo" in PR.PRINT_NAMES["about"]["canvas"]["lt"]
      and not any("BF" in s_ for s_ in PR.PRINT_RATES["skus"]) and len(PR.PRINT_RATES["skus"]) == 12, sorted(PR.PRINT_RATES["skus"]))
check("glossy metal 30, 40 and 60 cm at the prices of the acrylic (merchOne's blueprint 46, the SKUs with the hanger set), the small block of 10 cm at 39 EUR; every "
      "kind has a name and a line that says what it is in the eight languages, no dash in any",
      [(PR.product(x)["sku"], PR.product(x)["price"], PR.sku_rec(PR.product(x)["sku"])["blueprint"]) for x in ("metal30", "metal40", "metal60", "block10")]
      == [("ALP0300301HP", 5900, 46), ("ALP0400401HP", 7900, 46), ("ALP0600601HP", 12900, 46), ("ABS0100101", 3900, 18)]
      and PR.product_name("metal40", "lt") == "Blizgus metalas 40\u00a0×\u00a040\u00a0cm" and PR.product_name("metal40", "en").startswith("Glossy metal print 40")
      and set(PR.PRINT_NAMES["about"]) == set(PR.PRINT_NAMES["kinds"]) == {"acrylic", "metal", "canvas", "poster", "block", "keyring"}
      and all(len(PR.PRINT_NAMES["about"][k_][l_]) > 12 and PR.PRINT_NAMES["kinds"][k_][l_] for k_ in PR.PRINT_NAMES["about"] for l_ in PR.LANGS)
      and len({PR.PRINT_NAMES["about"][k_][l_] for k_ in PR.PRINT_NAMES["about"] for l_ in PR.LANGS}) == 48
      and not re.search(DASH, json.dumps([PR.PRINT_NAMES["kinds"], PR.PRINT_NAMES["about"]], ensure_ascii=False)), [PR.product_name("metal40", l_) for l_ in PR.LANGS])
mg12 = {p_["id"]: (min(PR.margin(p_["id"], cc_) for cc_ in PR.countries()), max(PR.margin(p_["id"], cc_) for cc_ in PR.countries())) for p_ in PR.products(offered=False)}
check("what each earns, least to most over the 27 countries (the build's own table): metal 39.70, 47.64 and 67.41 EUR at least, the canvas 26.85 and 35.44, the small "
      "block 22.68; the prints of 60 cm on metal and canvas ship dearer than the acrylic of 60 cm (13.49 EUR to Lithuania, 6.99 to Germany)",
      mg12["metal30"] == (3970, 4003) and mg12["metal40"] == (4764, 4797) and mg12["metal60"] == (6741, 6773) and mg12["canvas40"] == (2685, 2717)
      and mg12["canvas60"] == (3544, 3577) and mg12["block10"] == (2268, 2301) and mg12["block20"] == (3878, 3910) and mg12["poster50"] == (2581, 2614)
      and all(v[0] >= PR.PRINT_OFFER["margin_floor"] for k_, v in mg12.items() if k_ != "keyring")
      and [PR.shipping(cc_, "metal60") for cc_ in ("LT", "DE")] == [1349, 699] == [PR.shipping(cc_, "canvas60") for cc_ in ("LT", "DE")]
      and PR.shipping("LT", "acrylic60") == 849, mg12)
kb, kbi = PR.file_box("KRR0050041", 4096), PR.file_box("ALP0600601HP", 4096)
ak = np.zeros((400, 400, 3), dtype=np.uint8)
ak[:, :, 2] = 50
ak[150:250, 150:250] = 240
bk_ = io.BytesIO()
Image.fromarray(ak).save(bk_, "PNG")
kdata, kinfo = PR.make_print_file(bk_.getvalue(), "KRR0050041")
kpic = np.asarray(Image.open(io.BytesIO(kdata)).convert("RGB"))
check("the keyring: no size in its name in any language, a print area that is NOT square (56 x 76 mm: 441 x 598 px at 200 dpi, no trim), and a square artwork is "
      "centred on it whole, its own ground continued above and below; every square print keeps the geometry it had",
      PR.product("keyring") == PR.product("keyring", offered=False) == {"id": "keyring", "kind": "keyring", "cm": 0, "sku": "KRR0050041", "price": 2000, "on": 1}
      and all(PR.product_name("keyring", l_) == PR.PRINT_NAMES["kinds"]["keyring"][l_] for l_ in PR.LANGS) and PR.product_name("keyring", "lt") == "Raktų pakabukas"
      and PR.sku_rec("KRR0050041")["design_mm"] == [56.0, 76.0] and kb == ((441, 598), (441, 598), 200) and kbi == ((4121, 4121), (4087, 4087), 173)
      and PR.file_geometry("ALP0600601HP", 4096) == (4121, 4087, 173) and PR.file_geometry("CVS0600601LMF2HC", 4096) == (4087, 4087, 173)
      and PR.file_geometry("ABS0100101", 4096) == (819, 787, 200)
      # the artwork of this check is 400 px: at merchOne's least 133 dpi allows (never enlarged), its file is 293 x 398 px
      and PR.file_box("KRR0050041", 400) == ((293, 398), (293, 398), 133) and kpic.shape[:2] == (398, 293) and (kinfo["width"], kinfo["height"]) == (293, 398)
      and kinfo["art"] == [293, 293] and abs(int(kpic[4, 146, 2]) - 50) < 14 and abs(int(kpic[393, 146, 2]) - 50) < 14 and abs(int(kpic[199, 146, 2]) - 240) < 20, (kb, kinfo))
okk, kkk, _skk = paid_file_order(lang="lt")
pok = [x["id"] for x in ((get(f"/api/order?o={okk}&k={kkk}")[1].get("print_offer") or {}).get("products") or [])]
c, jkk = addon(okk, kkk, product="keyring", cc="LT", lang="lt")
pkk = H.Fake.creates[-1][0]
check("while the keyring is not offered (it earns 10.90 to 11.22 EUR, under the floor of 15 EUR: the owner decides), no page is told of it and nobody can buy it"
      " - 1125: the owner decided, the keyring is 20 EUR and offered. It earns 15.75 to 16.07 EUR, over the floor (the rule is as it was); the order page's offer "
      "lists twelve prints with it last, and its checkout is a session of its own with its name without a size, 20 EUR and its own shipping (8.49 to Lithuania)",
      mg12["keyring"] == (1575, 1607) and PR.PRINT_OFFER["margin_floor"] == 1500 and len(pok) == 12 and pok[-1] == "keyring" and c == 200
      and jkk.get("print") == {"product": "keyring", "country": "LT", "price": 2000, "ship": 849} and jkk.get("total") == 2849
      and pkk.get("line_items[0][price_data][product_data][name]") == "Raktų pakabukas" and pkk.get("line_items[0][price_data][unit_amount]") == "2000"
      and pkk.get("metadata[print_sku]") == "KRR0050041" and "keyring" in [x["id"] for x in (PR.public_info().get("products") or [])], (c, jkk, pok))
sidkk = addon_sid(okk)
fix_total(sidkk)
ckk, jwk = webhook(pay_with_address(sidkk, cc="LT", name="Ona Onaitė", email="pakabukas@example.com"))
paid_kk = pay.get_paid(okk)
MO.creates.clear()
rkk = PR.step(okk, rj(f"orders/{okk}/order.json"), paid_kk)
cur_kk = PR.record(okk) or {}
plk = MO.creates[-1] if MO.creates else {"items": [{}]}
fkk = cur_kk.get("file") or {}
check("a keyring bought and paid goes to merchOne as ONE order with its SKU and a print file of its own shape (56 x 76 mm: 441 x 598 px for the 2048 px artwork, "
      "the artwork whole in the middle), as every print does",
      ckk == 200 and (paid_kk.get("print") or {}).get("product") == "keyring" and paid_kk["print"].get("kind") == "keyring" and paid_kk["print"].get("cm") == 0
      and "mismatch" not in paid_kk["print"] and rkk == "created" and cur_kk.get("state") == "created" and len(MO.creates) == 1
      and plk["items"][0].get("product_sku") == "KRR0050041" and fkk.get("path") == f"orders/{okk}/print_keyring.jpg" and (fkk.get("width"), fkk.get("height")) == (441, 598)
      and Image.open(os.path.join(STORE, *fkk["path"].split("/"))).size == (441, 598) and fkk.get("art") == [441, 441], (ckk, rkk, cur_kk, plk.get("items")))
okm, kkm, _skm = paid_file_order(lang="en")
c, jkm = addon(okm, kkm, product="canvas60", cc="LT", lang="en", print_shown=6900 + 1349)
pkm = H.Fake.creates[-1][0]
check("a canvas of 60 cm bought after the artwork: its own session with its name (on a wooden stretcher frame, 60 x 60 cm), 69 EUR and its own shipping to Lithuania",
      c == 200 and jkm.get("print") == {"product": "canvas60", "country": "LT", "price": 6900, "ship": 1349} and jkm.get("total") == 8249
      and pkm.get("line_items[0][price_data][product_data][name]") == "Canvas on a wooden stretcher frame 60\u00a0×\u00a060\u00a0cm"
      and pkm.get("line_items[0][price_data][unit_amount]") == "6900" and pkm.get("shipping_options[0][shipping_rate_data][fixed_amount][amount]") == "1349"
      and pkm.get("metadata[print_sku]") == "CVS0600601LMF2HC", (c, jkm))

# ============================================================================================ 13. how long a print takes
section("13. how long a print takes (2026-11-24): per product and per country, from one table")
PT = PR.PRINT_TIMES
check("the table (api/_lib/print_times.py): a production time for every kind of the offer (canvas and poster 2 business days, every other 3), a delivery time for "
      "Lithuania, Latvia, Estonia (4 to 6 working days), Finland (5 to 8) and Germany (3 to 6), every one a country prints ship to; the constants of before are gone",
      set(PT["production"]) == set(PR.PRINT_NAMES["kinds"]) and {k_ for k_, v in PT["production"].items() if v == 2} == {"canvas", "poster"}
      and set(PT["production"].values()) == {2, 3} and PT["transit"] == {"LT": [4, 6], "LV": [4, 6], "EE": [4, 6], "FI": [5, 8], "DE": [3, 6]}
      and all(cc_ in PR.countries() for cc_ in PT["transit"]) and not hasattr(PR, "PROD_DAYS") and not hasattr(PR, "TRANSIT_DAYS")
      and [PR.production_days(x) for x in ("canvas40", "canvas60", "poster50", "acrylic30", "metal60", "block10", "keyring", "nothing")] == [2, 2, 2, 3, 3, 3, 3, 3]
      and PR.transit_days("LT") == (4, 6, True) and PR.transit_days("FI") == (5, 8, True) and PR.transit_days("SE")[2] is False and PR.transit_days(None)[2] is False, PT)
check("the sentence of a print's time in the eight languages: its production, then the delivery to its country in brackets with the published numbers, or 'about a "
      "week' without a number for a country that has none; no token left, no dash",
      PR.time_text("canvas40", "LT", "lt") == "Gamyba: apie 2 darbo dienas. Pristatymas (Lietuva): po to paprastai nuo 4 iki 6 darbo dienų."
      and PR.time_text("acrylic30", "SE", "en") == "Production: about 3 business days. Delivery (Sweden): then usually about a week."
      and PR.time_text("block20", "DE", "de") == "Produktion: etwa 3 Werktage. Zustellung (Deutschland): danach meist 3 bis 6 Werktage."
      and all(not re.search(r"[{}]", PR.time_text(p_["id"], cc_, l_)) and not re.search(DASH, PR.time_text(p_["id"], cc_, l_))
              and str(PR.production_days(p_["id"])) in PR.time_text(p_["id"], cc_, l_) and f"({PR.country_name(cc_, l_)})" in PR.time_text(p_["id"], cc_, l_)
              for p_ in PR.products(offered=False) for cc_ in ("LT", "FI", "DE", "SE", "HR") for l_ in PR.LANGS)
      and len({PR.time_text("poster50", "LT", l_) for l_ in PR.LANGS}) == 8, PR.time_text("canvas40", "LT", "lt"))
ot1, kt1 = draft(lang="lt")
c, jt1 = co(ot1, kt1, lang="lt", print={"product": "canvas40", "country": "LT"}, consent_print=True)
pt1 = H.Fake.creates[-1][0]
ot2, kt2, _st2 = paid_file_order(lang="en")
c2, jt2 = addon(ot2, kt2, product="acrylic60", cc="SE", lang="en")
pt2 = H.Fake.creates[-1][0]
est = lambda p_: (p_.get("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][value]"), p_.get("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]"))
check("Stripe's delivery estimate is the order's own: this print's production and this country's delivery (a canvas to Lithuania 6 to 8 business days; an acrylic "
      "print to Sweden, which has no published time, 3 and the general estimate)",
      c == 200 and est(pt1) == ("6", "8") and c2 == 200 and est(pt2) == (str(3 + PT["transit_other"][0]), str(3 + PT["transit_other"][1]))
      and pt1.get("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][unit]") == "business_day", (est(pt1), est(pt2)))
sidt = rj(f"orders/{ot1}/order.json")["checkout"]["session_id"]
fix_total(sidt)
H.Fake.emails.clear()
ct, jt = webhook(pay_with_address(sidt, cc="LT"))
conf_t = [m for m, _i in H.Fake.emails if ot1 in m.get("subject", "") or ot1 in m.get("text", "")]
txt_t = "\n".join(m.get("text", "") for m in conf_t)
check("the order confirmation of an order with a print says that print's own times (a canvas to Lithuania: production about 2 business days, delivery 4 to 6 working "
      "days) and not the sentence of before; the e-mails' paragraphs hold the slot {time} in every language",
      ct == 200 and PR.time_text("canvas40", "LT", "lt") in txt_t and "Gamyba trunka apie 3 darbo dienas, o pristatymas" not in txt_t and "nuo 2 iki 9" not in txt_t
      and all(t_[l_]["p1"].count("{time}") == 1 and t_[l_]["p1"].count("{producer}") == 1 and not re.search(r"\d", t_[l_]["p1"]) for t_ in (PR.CONF, PR.ADDON_CONF) for l_ in PR.LANGS),
      (ct, txt_t[:300]))
maker.kick = real_kick
pay._stripe = real_stripe

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
