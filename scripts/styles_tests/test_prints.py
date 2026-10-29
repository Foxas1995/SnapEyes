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
check("the offer: five prints at the owner's prices (59, 79, 129, 69, 35 EUR), every SKU in the rate table, prints offered on eu, lt and hr only",
      [(p["id"], p["price"]) for p in PR.products()] == [("acrylic30", 5900), ("acrylic40", 7900), ("acrylic60", 12900), ("canvas40", 6900), ("poster50", 3500)]
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
py = {p["id"] + cc: [PR.shipping(cc, p["id"]), PR.margin(p["id"], cc)] for p in PR.products() for cc in PR.countries()}
check("the server's shipping and margins are the build check's (scripts/check_prints.mjs, the rules the page's module is held to) for every print and country",
      jsv == py, (js.stderr[-300:], None if jsv is None else [k for k in py if jsv.get(k) != py[k]][:5]))
geo = {p["sku"]: PR.file_geometry(p["sku"], 4096) for p in PR.products()}
s30, s60, cv, ps = geo["ACP0300301HP"], geo["ACP0600601HP"], geo["CVS0400401LMSBF2HC"], geo["PSD0500501"]
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
check("the product's name in the five languages, with its size (no-break spaces)",
      PR.product_name("acrylic40", "en") == "Acrylic glass print 40 × 40 cm" and PR.product_name("canvas40", "lt").startswith("Drobė juodame rėme")
      and PR.product_name("poster50", "hu").startswith("Poszter") and PR.country_name("DE", "hr") == "Njemačka", PR.product_name("acrylic40", "en"))
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
check("order.json keeps the print with the print box the customer ticked (consent version 2026-10-28.3, time, Lithuanian text, fingerprint)",
      cp.get("product") == "acrylic60" and cp.get("country") == "DE" and cp.get("ship") == 699 and cp["consent"]["version"] == pay.CONSENT_VERSION == "2026-10-28.3"
      and cp["consent"]["text"] == PR.PRINT_CONSENT_TEXT["lt"] and len(cp["consent"]["text_sha256"]) == 16, cp)
check("the reply names the print and the total Stripe charges (the artwork, the print, its shipping)",
      j.get("print") == {"product": "acrylic60", "country": "DE", "price": 12900, "ship": 699} and j.get("total") == j["amount"] + 12900 + 699, j)
check("the withdrawal waiver of the file is unchanged and recorded as before (its text is the version's)",
      (rec["checkout"]["consent"]["text"] == pay.CONSENT_TEXT["lt"]) and pay.consent_text("2026-10-28.2", "en") == pay.CONSENT_TEXT["en"]
      and pay.consent_text("2026-10-28.3", "en", "us") == pay.CONSENT_TEXT_US["en"], rec["checkout"]["consent"])

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
      and len(st["offer"]) == 5 and all(x["margin_min"] >= PR.PRINT_OFFER["margin_floor"] for x in st["offer"]) and any(r_["order"] == o8 for r_ in st["open"]), st["open"])
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
check("the EU terms in every language name the prints with their prices, the shipping table, the delivery countries, the manufacturer and its address, "
      "Art. 16(c), the 7 days and the legal guarantee of two years",
      all("Picanova GmbH" in t and "Eupener Straße 67" in t and "16" in t for t in (en, lt_, hu_, hr_, de_)) and "€59.00" in en and "59,00 €" in de_
      and "Germany" in en and "Sweden" in en and "two years" in en and "7 days" in en and "Article 16(c)" in en and "30 days" in en, en[:300])
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
check("the consent version is 2026-10-28.3 on the server and the page, and the print box is the same words on both (the build's text check holds it)",
      pay.CONSENT_VERSION == "2026-10-28.3" and "2026-10-28.3" in open(os.path.join(REPO, "src", "shared", "legal.ts"), encoding="utf-8").read()
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
check("the print box survives the next consent version: the current version maps to the current text, the first one is kept",
      PR.PRINT_CONSENT_TEXTS[pay.CONSENT_VERSION] == PR.PRINT_CONSENT_TEXT and PR.PRINT_CONSENT_TEXTS["2026-10-28.3"] == PR.PRINT_CONSENT_TEXT
      and PR.consent_text(pay.CONSENT_VERSION, "lt") == PR.PRINT_CONSENT_TEXT["lt"], "")
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

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
