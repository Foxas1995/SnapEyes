# -*- coding: utf-8 -*-
"""The Meta pixel's server half, the Conversions API (api/_lib/meta.py; the owner's decision of 2026-11-25), and its wiring (api/checkout.py, pay.py
record_paid and create_session, voucher.py buy and on_paid, prints.py addon_buy, addon_record and addon_status, api/health.py).

  1.  the unit: the dataset id (the constant, META_PIXEL_ID overrides it, empty or malformed switches it off), the token from the environment only,
      the event id (purchase_<session>, a voucher's hashed), the payload (SHA-256 of the trimmed lower-case e-mail as em and external_id, the
      hashed country, fbp, fbc, the IP and the user agent from the session's metadata, value and currency, the category, the page's path without
      its query, action_source website; nothing about the photo, the iris, the colour, the style, the names or an image), META_TEST_EVENT_CODE
  2.  purchase(): no token = no call (said once in the log), Stripe test mode = no call, a failure or a refusal = no exception and a log line
      without the token, the token in the POST body and never in the address
  3.  the checkout's half: no token = nothing collected (the Stripe session's metadata is what it was); with it, fbp, fbc, cip and cua in the
      metadata of the artwork's and the voucher's session (malformed values dropped)
  4.  the payment: the webhook of a live payment sends one Purchase with the same event id as the browser's (a replayed webhook sends none, a test
      payment none); a Meta that fails or hangs does not break or fail the payment; the voucher's Purchase with its hashed id and /gift
  5.  GET /api/health: meta_pixel and meta_capi
  6.  the print bought later: its record sends the Purchase once, and the order page's paid answer says what was paid (read in the code)

No network (Stripe and Resend are the harness's stub, Meta is a stub sender here), no image model. Run by suites/run_main.sh as v3meta (in the world
before the catalogue switch, as the payment suites).
    python test_meta.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(REPO, "api")
SP_DIR = os.environ.get("SNAPEYES_SP") or ""
HARNESS = next((d for d in (os.path.join(SP_DIR, "wave-pv", "tests") if SP_DIR else "", os.path.join(REPO, "suites", "tree", "wave-pv", "tests"))
                if d and os.path.isfile(os.path.join(d, "harness.py"))), None) or sys.exit("the payments harness (wave-pv/tests/harness.py) is not found")

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:900]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_", "MERCHONE_", "META_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_WORLD"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3meta_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

# coupons in the Stripe stub (a voucher's payment makes one: api/_lib/voucher.py _coupon)
_POST = H.StubHandler.do_POST


def _post(self):
    if self.path.split("?")[0] != "/v1/coupons":
        return _POST(self)
    self.rfile.read(int(self.headers.get("content-length") or 0))
    return self._send(200, {"id": "gift_coupon", "object": "coupon"})


H.StubHandler.do_POST = _post
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
os.environ["STYLE_PLATE_CACHE"] = os.path.join(TMP, "cache")
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
sys.path.insert(0, API)
import requests  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import meta as MC  # noqa: E402
from _lib import pay  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import voucher as V  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402

PACK = json.load(open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
LEGACY = list(CT.legacy_ids())
STYLE = next((s for s in LEGACY if not CT.is_black(s)), LEGACY[0])
TOKEN = "EAAtest" + "x" * 40
FBP = "fb.1.1764000000000.1234567890"
FBC = "fb.1.1764000000000.IwAR0abcdEFGH_ij-12"
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"

SENT = []
MODE = {"m": "ok"}


def fake_send(url, payload, timeout):
    SENT.append({"url": url, "payload": json.loads(json.dumps(payload)), "timeout": timeout})
    if MODE["m"] == "raise":
        raise requests.ConnectionError("graph.facebook.com is down")
    if MODE["m"] == "refuse":
        return 400, {"type": "OAuthException", "code": 190, "message": "Invalid OAuth access token."}
    return 200, None


MC._send = fake_send
LOG = []
_print = print


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
    return r.status_code, r.json()


def webhook(obj):
    body, sig = H.signed_event(obj, "checkout.session.completed")
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=180)
    return r.status_code, r.json()


def rj(path):
    try:
        with open(os.path.join(STORE, *path.split("/")), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


_EYE = {}


def draft():
    if "s" not in _EYE:
        jpeg = SI.jpeg_bytes("blue_round")
        prof = EYE.profile_of_bytes(jpeg, pad=1.12, rules=("lid", "fill"))
        _EYE["s"] = P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=prof)["sealed"]
    c, j = post("/api/order", {"action": "draft", "eye": 1, "crop": H.jpeg_b64(256, 11), "pad": 1.12, "ticket": H.fresh_ticket(), "lang": "en", "ref": "e1",
                               "sealed": _EYE["s"]})
    assert c == 200, (c, j)
    return j["order"], j["k"]


def checkout(o, k, extra=None, headers=None):
    body = {"order": o, "k": k, "eyes": 1, "style": STYLE, "names": "", "title": "", "lang": "en", "consent_digital": True}
    body.update(extra or {})
    return post("/api/checkout", body, headers)


def meta_of(sid):
    return dict(H.Fake.sessions[sid]["metadata"])


def sid_of(o):
    return rj(f"orders/{o}/order.json")["checkout"]["session_id"]


# ============================================================================================ 1. the unit
section("1. the dataset id, the token, the event id, the payload")
check("the dataset id is api/_lib/meta.py PIXEL_ID (1804549607500630) when META_PIXEL_ID is not set", MC.PIXEL_ID == "1804549607500630" and MC.pixel_id() == MC.PIXEL_ID)
os.environ["META_PIXEL_ID"] = " 123456789 "
a = MC.pixel_id()
os.environ["META_PIXEL_ID"] = ""
b = MC.pixel_id()
os.environ["META_PIXEL_ID"] = "12x45"
c_ = MC.pixel_id()
del os.environ["META_PIXEL_ID"]
check("META_PIXEL_ID overrides it (trimmed); an empty value switches the pixel off, a malformed one too", a == "123456789" and b == "" and c_ == "" and not MC.capi_on())
check("without META_CAPI_TOKEN the Conversions API is off; a malformed token counts as none", not MC.capi_on() and MC.token() == "")
os.environ["META_CAPI_TOKEN"] = "short"
check("... a token of five characters is malformed", MC.token() == "" and not MC.capi_on())
os.environ["META_CAPI_TOKEN"] = TOKEN
check("with a token and the dataset id it is on", MC.capi_on() and MC.token() == TOKEN)
check("the event id: purchase_<session> for the artwork and a print, purchase_ and 32 hex of SHA-256 of the session for a voucher (its session shows the code)",
      MC.event_id("cs_live_abc123", "artwork") == "purchase_cs_live_abc123" == MC.event_id("cs_live_abc123", "print")
      and MC.event_id("cs_live_abc123", "voucher") == "purchase_" + hashlib.sha256(b"cs_live_abc123").hexdigest()[:32])
SESS = {"id": "cs_live_abc123", "livemode": True, "metadata": {"fbp": FBP, "fbc": FBC, "cip": "203.0.113.7", "cua": UA, "style": "clean_iris", "names": "[\"Anna\"]",
                                                                "order": "ab12-cd34", "key_sha": "x" * 16}}
pl = MC.payload("artwork", SESS, "  Kunde@Example.COM ", 4999, "eur", "https://snapeyes.com/order?o=ab12-cd34&k=" + "0" * 32, country="LT", now=1764000000)
ev = pl["data"][0]
em = hashlib.sha256(b"kunde@example.com").hexdigest()
check("the payload: Purchase, its time, the event id, action_source website, the page's address without its query (never the order's key)",
      ev["event_name"] == "Purchase" and ev["event_time"] == 1764000000 and ev["event_id"] == "purchase_cs_live_abc123" and ev["action_source"] == "website"
      and ev["event_source_url"] == "https://snapeyes.com/order", ev)
check("user_data: SHA-256 of the trimmed lower-case e-mail as em and as external_id, the hashed country, fbp, fbc, the IP and the user agent as they came",
      ev["user_data"] == {"em": [em], "external_id": [em], "fbp": FBP, "fbc": FBC, "client_ip_address": "203.0.113.7", "client_user_agent": UA,
                          "country": [hashlib.sha256(b"lt").hexdigest()]}, ev["user_data"])
check("custom_data: value in the currency's unit, the currency in capitals, the category; nothing else", ev["custom_data"] == {"value": 49.99, "currency": "EUR", "content_category": "artwork"},
      ev["custom_data"])
blob = json.dumps(pl).lower()
check("nothing of the order, its style, the names, the key, the photo or an image is in the payload, and no plain e-mail; no token in it", not any(w in blob for w in (
    "clean_iris", "anna", "ab12-cd34", "key_sha", "image", "iris", "photo", "colour", "color", "kunde@", "0" * 32, TOKEN.lower())), blob[:300])
check("no test_event_code without META_TEST_EVENT_CODE", "test_event_code" not in pl)
os.environ["META_TEST_EVENT_CODE"] = "TEST12345"
check("META_TEST_EVENT_CODE adds test_event_code", MC.payload("artwork", SESS, "a@b.c", 1, "eur", "x").get("test_event_code") == "TEST12345")
del os.environ["META_TEST_EVENT_CODE"]
check("the country: Stripe's (customer_details.address.country), else the market's one country, else none",
      MC.country_of({"customer_details": {"address": {"country": "de"}}}, ["LT"]) == "DE" and MC.country_of({}, ["LT"]) == "LT" and MC.country_of({}, []) is None
      and MC.country_of({}, ["LT", "LV"]) is None)

# ============================================================================================ 2. purchase()
section("2. purchase(): what it sends and when it sends nothing")
SENT.clear()
r = MC.purchase("artwork", SESS, "kunde@example.com", 4999, "eur", "https://snapeyes.com/order", "LT")
s0 = SENT[0] if SENT else {}
check("a live payment with a token: one call to graph.facebook.com/<version>/<dataset id>/events, the token in the POST body, never in the address, a short timeout",
      r == "sent" and len(SENT) == 1 and s0["url"] == f"https://graph.facebook.com/{MC.API_VERSION}/1804549607500630/events" and TOKEN not in s0["url"]
      and s0["payload"].get("access_token") == TOKEN and 0 < s0["timeout"] <= MC.TIMEOUT, (r, s0.get("url"), s0.get("timeout")))
SENT.clear()
r = MC.purchase("artwork", dict(SESS, livemode=False), "kunde@example.com", 4999, "eur", "x")
check("a payment in Stripe's test mode: nothing is sent", r == "test" and not SENT, r)
os.environ.pop("META_CAPI_TOKEN")
MC._SAID["no_token"] = False
import contextlib  # noqa: E402
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    r1 = MC.purchase("artwork", SESS, "kunde@example.com", 4999, "eur", "x")
    r2 = MC.purchase("artwork", SESS, "kunde@example.com", 4999, "eur", "x")
check("no token: nothing is sent, and the log says so once per instance", r1 == r2 == "off" and not SENT and buf.getvalue().count("META_CAPI_TOKEN is not set") == 1, buf.getvalue())
os.environ["META_CAPI_TOKEN"] = TOKEN
for m, want in (("raise", "failed"), ("refuse", "refused")):
    MODE["m"] = m
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            r = MC.purchase("artwork", SESS, "kunde@example.com", 4999, "eur", "x")
        thrown = None
    except Exception as e:  # noqa
        thrown, r = e, None
    check(f"Meta {'down' if m == 'raise' else 'refusing'}: purchase() raises nothing ({want}) and logs a line without the token", thrown is None and r == want
          and TOKEN not in buf.getvalue() and "snapeyes meta:" in buf.getvalue(), (thrown, r, buf.getvalue()))
MODE["m"] = "ok"
check("an unknown category or no e-mail address: nothing sent", MC.purchase("eye", SESS, "a@b.c", 1, "eur", "x") == "failed"
      and MC.purchase("artwork", SESS, None, 1, "eur", "x") == "no_email")
check("the token never reaches a log line of the payments either (pay.scrub knows it)", TOKEN not in pay.scrub(f"call with {TOKEN}"))

# ============================================================================================ 3. the checkout's half
section("3. the checkout carries fbp, fbc, the IP and the user agent in the Stripe metadata, only with a token")
os.environ.pop("META_CAPI_TOKEN")
o, k = draft()
c, j = checkout(o, k, {"fbp": FBP, "fbc": FBC}, {"User-Agent": UA, "X-Real-IP": "203.0.113.7"})
m0 = meta_of(sid_of(o)) if c == 200 else {}
check("no token: the session's metadata has none of fbp, fbc, cip, cua (nothing is collected that nothing would send)", c == 200 and not set(m0) & set(MC.META_KEYS), (c, j, m0))
os.environ["META_CAPI_TOKEN"] = TOKEN
o, k = draft()
c, j = checkout(o, k, {"fbp": FBP, "fbc": FBC}, {"User-Agent": UA, "X-Real-IP": "203.0.113.7"})
sid_a = sid_of(o) if c == 200 else None
m1 = meta_of(sid_a) if sid_a else {}
check("with a token: fbp and fbc as the page sent them, cip (x-real-ip) and cua (the user agent) in the metadata",
      c == 200 and m1.get("fbp") == FBP and m1.get("fbc") == FBC and m1.get("cip") == "203.0.113.7" and m1.get("cua") == UA, (c, j, m1))
rec = rj(f"orders/{o}/order.json") or {}
check("... and nowhere in our own order record", not any(x in json.dumps(rec) for x in (FBP, FBC, "203.0.113.7", "iPhone OS")), "")
o2, k2 = draft()
c, j = checkout(o2, k2, {"fbp": "fb.1.x.<script>", "fbc": "javascript:alert(1)"}, {"User-Agent": "A\x01B", "X-Forwarded-For": "198.51.100.9, 10.0.0.1"})
m2 = meta_of(sid_of(o2)) if c == 200 else {}
check("malformed fbp and fbc are dropped; the first x-forwarded-for address is the IP; control characters leave the user agent", c == 200 and "fbp" not in m2 and "fbc" not in m2
      and m2.get("cip") == "198.51.100.9" and m2.get("cua") == "AB", m2)

# ============================================================================================ 4. the payment
section("4. the payment: one Purchase, the browser's event id, and the payment never fails for Meta")
SENT.clear()
s = H.pay_session(sid_a, "Kunde@Example.com")
s["livemode"] = True
c, j = webhook(s)
ev = SENT[0]["payload"]["data"][0] if SENT else {}
check("the webhook of a live payment records the order and sends ONE Purchase: purchase_<session>, the amount, the currency, the category artwork, /order",
      c == 200 and j.get("new") is True and len(SENT) == 1 and ev.get("event_id") == f"purchase_{sid_a}" and ev["custom_data"]["currency"] == "EUR"
      and ev["custom_data"]["value"] == s["amount_total"] / 100 and ev["custom_data"]["content_category"] == "artwork"
      and ev.get("event_source_url", "").endswith("/order") and ev["user_data"]["em"] == [em] and ev["user_data"]["fbp"] == FBP and ev["user_data"]["client_user_agent"] == UA,
      (c, j, ev))
c, j = webhook(s)
c2, j2 = get(f"/api/order?o={o}&k={k}&s={sid_a}")
check("a replayed webhook and the order page's own check send nothing more", c == 200 and len(SENT) == 1 and c2 == 200, (c, j, len(SENT)))
o3, k3 = draft()
checkout(o3, k3, {"fbp": FBP})
SENT.clear()
c, j = webhook(H.pay_session(sid_of(o3), "test@example.com"))
check("a payment in Stripe's test mode: answered as before (this deployment takes no test orders), nothing sent to Meta", c == 200 and not SENT, (c, j))
o4, k4 = draft()
checkout(o4, k4)
MODE["m"] = "raise"
SENT.clear()
s4 = H.pay_session(sid_of(o4), "down@example.com")
s4["livemode"] = True
c, j = webhook(s4)
MODE["m"] = "ok"
check("Meta down at the payment: the webhook still answers 200, the order is paid and its confirmation goes out", c == 200 and j.get("new") is True and len(SENT) == 1
      and (rj(f"orders/{o4}/paid.json") or {}).get("paid") is True and j.get("mail") in ("sent", "done"), (c, j))
# the voucher
SENT.clear()
c, j = post("/api/checkout", {"gift": {"kind": "one"}, "market": "lt", "lang": "lt", "fbp": FBP}, {"User-Agent": UA, "X-Real-IP": "203.0.113.8"})
vsid = next((x for x, v in H.Fake.sessions.items() if v["url"] == j.get("url")), None)
vm = meta_of(vsid) if vsid else {}
check("a gift voucher's session carries fbp, cip and cua too (with the token)", c == 200 and vm.get("fbp") == FBP and vm.get("cip") == "203.0.113.8" and vm.get("cua") == UA, (c, vm))
vs = H.pay_session(vsid, "pirkejas@example.com")
vs["livemode"] = True
c, j = webhook(vs)
ev = SENT[0]["payload"]["data"][0] if SENT else {}
check("the voucher's payment sends one Purchase: the hashed event id (never the session, which shows the code), category voucher, /gift, the voucher's value",
      c == 200 and len(SENT) == 1 and ev.get("event_id") == MC.event_id(vsid, "voucher") and vsid not in json.dumps(SENT[0]["payload"])
      and ev["custom_data"] == {"value": V.value_of("one", "lt") / 100, "currency": "EUR", "content_category": "voucher"} and ev["event_source_url"].endswith("/gift")
      and ev["user_data"]["country"] == [hashlib.sha256(b"lt").hexdigest()], (c, j, ev))
webhook(vs)
get(f"/api/checkout?gift={vsid}")
check("... once: a replayed webhook and the gift page send nothing more", len(SENT) == 1, len(SENT))

# ============================================================================================ 5. health
section("5. GET /api/health")
c, h = get("/api/health")
os.environ.pop("META_CAPI_TOKEN")
c2, h2 = get("/api/health")
os.environ["META_PIXEL_ID"] = ""
c3, h3 = get("/api/health")
os.environ.pop("META_PIXEL_ID")
check("meta_pixel and meta_capi are booleans: true and true with a token, true and false without, false and false with META_PIXEL_ID empty; no token in the answer",
      h.get("meta_pixel") is True and h.get("meta_capi") is True and h2.get("meta_pixel") is True and h2.get("meta_capi") is False
      and h3.get("meta_pixel") is False and h3.get("meta_capi") is False and TOKEN not in json.dumps(h), (h.get("meta_pixel"), h.get("meta_capi"), h2.get("meta_capi"), h3.get("meta_pixel")))

# ============================================================================================ 6. the print bought later
section("6. the print bought after the artwork")
src = open(os.path.join(API, "_lib", "prints.py"), encoding="utf-8").read()
rec_fn = src[src.index("def addon_record("):src.index("def addon_mail(")]
check("prints.addon_record sends the print's Purchase once, after print_paid.json was created (the StorageExists path returns before it)",
      rec_fn.index('store.put(_path(order, ADDON_PAID)') < rec_fn.index('MC.purchase("print", sess, email, amount, currency') and "return again(" in rec_fn.split("MC.purchase")[0])
check("prints.addon_buy puts the identifiers in the print's session metadata, and the paid answer of addon_status says the amount and currency",
      "meta.update(MC.checkout_meta(body))" in src[src.index("def addon_buy("):src.index("def _addon_extra(")] and src.count("**_paid_amount(pa)") == 2)
pay_src = open(os.path.join(API, "_lib", "pay.py"), encoding="utf-8").read()
rp = pay_src[pay_src.index("def record_paid("):pay_src.index("def extra_payment(")]
check("pay.record_paid sends the artwork's Purchase only for a new paid.json, and not for a payment that arrived after a withdrawal",
      rp.index("upsert=False)") < rp.index('meta.purchase("artwork"') and "else:" in rp.split('meta.purchase("artwork"')[0][-400:])
DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
check("the new server code holds no dash", not re.search(DASH, open(os.path.join(API, "_lib", "meta.py"), encoding="utf-8").read()))

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
