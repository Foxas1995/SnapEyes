# -*- coding: utf-8 -*-
"""The payment methods of a Stripe Checkout Session by the visitor's country (api/_lib/pay.py payment_methods, visitor_country, create_checkout_session;
the owner's decision of 2026-11-25, "as on TaleInTune"): the card and Link everywhere, Revolut Pay in the EEA and the UK, each local method only in its own
country and in a currency it takes; a method Stripe refuses never breaks the checkout. The artwork, the voucher and the print add-on use it.

No network (Stripe is the harness's stub; the refusals are a fake sender here). Run by suites/run_main.sh as v3paym (the world before the catalogue switch).
    python test_paymethods.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import io
import json
import os
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


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "STORE_", "MERCHONE_", "META_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_WORLD"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3paym_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
import harness as H  # noqa: E402

stub = H.start_stub()
H.setup_env(os.path.join(TMP, "store"), stub.server_address[1])
os.environ["STYLE_PLATE_CACHE"] = os.path.join(TMP, "cache")
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"
sys.path.insert(0, API)
import requests  # noqa: E402
from PIL import Image  # noqa: E402
import synth_iris as SI  # noqa: E402
from _lib import catalogue as CT  # noqa: E402
from _lib import pay  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402

H.Fake.legal = dict(json.load(open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8")), making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
STYLE = next((s for s in CT.legacy_ids() if not CT.is_black(s)), None)


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=300)
    return r.status_code, r.json()


def methods(p):
    return [v for k, v in sorted(((k, v) for k, v in p.items() if k.startswith("payment_method_types[")), key=lambda x: int(x[0][21:-1]))]


# ---- 1. the lists
PM = pay.payment_methods
check("Lithuania, Latvia, Estonia, Germany: the card, Link and Revolut Pay", all(PM(c, "eur") == ["card", "link", "revolut_pay"] for c in ("LT", "LV", "EE", "DE")))
check("each local method in its own country only: EPS Austria, Bancontact Belgium, MB WAY Portugal, Satispay Italy, MobilePay Finland; Klarna in Portugal, Spain, the Netherlands and Finland",
      PM("AT", "eur")[3:] == ["eps"] and PM("BE", "eur")[3:] == ["bancontact"] and PM("PT", "eur")[3:] == ["mb_way", "klarna"] and PM("IT", "eur")[3:] == ["satispay"]
      and PM("FI", "eur")[3:] == ["mobilepay", "klarna"] and PM("ES", "eur")[3:] == ["klarna"] and PM("NL", "eur")[3:] == ["klarna"] and "eps" not in PM("DE", "eur"))
check("a method only in a currency it takes: BLIK is PLN only, so a Polish buyer in euros gets none; Hungary in forints the card and Link", PM("PL", "eur") == ["card", "link", "revolut_pay"]
      and PM("PL", "pln")[-1] == "blik" and PM("HU", "huf") == ["card", "link"])
check("outside the EEA and the UK and an unknown country: the card and Link; never anything Korean or Pix", PM("US", "usd") == PM("AU", "aud") == PM(None, "eur") == ["card", "link"]
      and not any(m in json.dumps([PM(c, "eur") for c in pay.EEA_GB]) for m in ("kakao", "naver", "payco", "samsung", "pix", "kr_card")))

# ---- 2. a refusal never breaks the checkout
SENT, ANSWERS = [], []
_real = pay._stripe


class R:
    def __init__(self, code, body):
        self.status_code, self._b = code, body

    def json(self):
        return self._b


def fake(method, path, params=None, idem=None, timeout=15.0):
    SENT.append((idem, [v for k, v in params if k.startswith("payment_method_types[")]))
    return ANSWERS.pop(0)


pay._stripe = fake
ANSWERS[:] = [R(400, {"error": {"type": "invalid_request_error", "param": "payment_method_types", "message": "The payment method type \"mobilepay\" is invalid."}}),
              R(200, {"id": "cs_test_x", "url": "https://x"})]
buf = io.StringIO()
import contextlib  # noqa: E402
with contextlib.redirect_stdout(buf):
    r = pay.create_checkout_session([("mode", "payment")], "idem1", "test", PM("FI", "eur"))
check("Stripe refuses a method: asked again with the card and Link (a new idempotency key), and it is logged", r.status_code == 200 and SENT[0][1] == PM("FI", "eur")
      and SENT[1] == ("idem1-pm1", ["card", "link"]) and "refused the payment methods" in buf.getvalue(), (SENT, buf.getvalue()))
SENT.clear()
ANSWERS[:] = [R(400, {"error": {"param": "payment_method_types[1]", "message": "x"}}), R(400, {"error": {"param": "payment_method_types[0]", "message": "x"}}), R(200, {})]
with contextlib.redirect_stdout(io.StringIO()):
    r = pay.create_checkout_session([], "idem2", "test", PM("AT", "eur"))
check("... and when even the card and Link are refused, with Stripe's own choice (no payment_method_types)", r.status_code == 200 and [s[1] for s in SENT] == [PM("AT", "eur"), ["card", "link"], []], SENT)
SENT.clear()
ANSWERS[:] = [R(400, {"error": {"param": "line_items", "message": "bad"}})]
r = pay.create_checkout_session([], "idem3", "test", PM("AT", "eur"))
check("another refusal is returned as it came (asked once)", r.status_code == 400 and len(SENT) == 1)
pay._stripe = _real

# ---- 3. the sessions
jpeg = SI.jpeg_bytes("blue_round")
sealed = P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=EYE.profile_of_bytes(jpeg, pad=1.12, rules=("lid", "fill")))["sealed"]


def order():
    c, j = post("/api/order", {"action": "draft", "eye": 1, "crop": H.jpeg_b64(256, 3), "pad": 1.12, "ticket": H.fresh_ticket(), "lang": "en", "ref": "e1", "sealed": sealed})
    return j["order"], j["k"]


o, k = order()
n = len(H.Fake.creates)
c, j = post("/api/checkout", {"order": o, "k": k, "eyes": 1, "style": STYLE, "names": "", "title": "", "lang": "en", "consent_digital": True}, {"X-Vercel-Ip-Country": "PT"})
p = H.Fake.creates[-1][0] if len(H.Fake.creates) > n else {}
check("the artwork's session of a visitor in Portugal: the card, Link, Revolut Pay, MB WAY and Klarna", c == 200 and methods(p) == ["card", "link", "revolut_pay", "mb_way", "klarna"], (c, j, methods(p)))
o, k = order()
c, j = post("/api/checkout", {"order": o, "k": k, "eyes": 1, "style": STYLE, "names": "", "title": "", "lang": "en", "consent_digital": True})
check("no country header on the euro market: the card and Link only", c == 200 and methods(H.Fake.creates[-1][0]) == ["card", "link"], methods(H.Fake.creates[-1][0]))
o, k = order()
c, j = post("/api/checkout", {"order": o, "k": k, "eyes": 1, "style": STYLE, "names": "", "title": "", "lang": "en", "consent_digital": True, "market": "lt"})
check("no header, the Lithuanian market: its country, the card, Link and Revolut Pay", c == 200 and methods(H.Fake.creates[-1][0]) == ["card", "link", "revolut_pay"], methods(H.Fake.creates[-1][0]))
c, j = post("/api/checkout", {"gift": {"kind": "one"}, "market": "eu", "lang": "en"}, {"X-Vercel-Ip-Country": "AT"})
check("a gift voucher's session from Austria: the card, Link, Revolut Pay and EPS", c == 200 and methods(H.Fake.creates[-1][0]) == ["card", "link", "revolut_pay", "eps"], methods(H.Fake.creates[-1][0]))
src = open(os.path.join(API, "_lib", "prints.py"), encoding="utf-8").read()
check("the print bought later asks for its session the same way (prints.addon_buy)", "pay.create_checkout_session(params, f\"snapeyes-print-" in src and "pay.payment_methods(pay.visitor_country(market), currency)" in src)

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
