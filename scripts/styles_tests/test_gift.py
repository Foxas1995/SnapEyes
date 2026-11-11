# -*- coding: utf-8 -*-
"""Gift vouchers (api/_lib/voucher.py, api/checkout.py, api/stripe_webhook.py, pay.py; the gift page src/gift; the checkout's field src/try/GiftField.tsx;
the legal texts src/legal/docs/vouchers.ts).

  1.  the code: derived from the session with the secret (the same every time), 12 characters without 0, O, 1 and I, read with spaces, dashes and in
      lower case, a one-way coupon id; the markets (eu, lt, hr) and the values (the standard one-eye art and two-eye prices)
  2.  buying: POST /api/checkout {gift}: the Stripe session (mode payment, euros, the value, the metadata, the success and cancel pages of /gift, the
      language), refusals (an unknown kind, a market that is not in euros of the EU edition)
  3.  paid: the webhook makes the coupon (amount_off, currency, one redemption, the last day), the record (no email address), the buyer's email with the
      code and the legal texts, the owner's note, each once (a replayed webhook, the success page); a busy email is retried; a session paid at
      another amount is refused and the owner told; GET /api/checkout?gift=: ready with the code, pending, expired, unknown
  4.  checking a code: GET /api/checkout?voucher=: valid with its value; format, unknown, currency
  5.  redeeming: the order's checkout with the code (discounts[0][coupon], the metadata, no payment_intent_data when it pays for everything), a no-cost
      payment (no_payment_required, amount 0) is an order paid in full: paid.json's voucher, no amount mismatch, the confirmation's price row; the code
      cannot be used twice (409 voucher_invalid used, nothing created); a voucher that pays part of a larger order; a cheaper order (the rest not paid out)
  6.  pay.session_paid: a no-cost session only with amount 0
  7.  the legal texts: the EU terms (every language) with the section and its prices, the Hungarian edition's terms without euro prices, the Australian and
      the US ones without vouchers; the privacy policy and the withdrawal page; the server files hold no dash

No network (Stripe and Resend are the harness's stub, with coupons added here), no image model. Run by suites/run_main.sh as v3gift (in the world before the
catalogue switch: a legacy style is the vehicle of the checkout, as in the payment suites).
    python test_gift.py       prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure"""
import atexit
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
from urllib.parse import urlsplit, parse_qs

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
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_", "STORE_", "MERCHONE_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP", "SNAPEYES_WORLD"):
            os.environ.pop(k)
TMP = tempfile.mkdtemp(prefix="snapeyes_v3gift_")
atexit.register(shutil.rmtree, TMP, ignore_errors=True)
STORE = os.path.join(TMP, "store")
sys.path.insert(0, HARNESS)
sys.path.insert(0, HERE)
os.environ["PYTHONIOENCODING"] = "utf-8"
import harness as H  # noqa: E402

# ---------------------------------------------------------------------------------------------------- coupons in the Stripe stub
COUPONS = {}
COUPON_CREATES = []
_POST, _GET = H.StubHandler.do_POST, H.StubHandler.do_GET


def _post(self):
    path = urlsplit(self.path).path
    if path != "/v1/coupons":
        return _POST(self)
    raw = self.rfile.read(int(self.headers.get("content-length") or 0))
    p = {k: v[0] for k, v in parse_qs(raw.decode("utf-8"), keep_blank_values=True).items()}
    COUPON_CREATES.append((p, dict(self.headers)))
    cid = p.get("id")
    if cid in COUPONS:
        return self._send(400, {"error": {"type": "invalid_request_error", "code": "resource_already_exists", "message": "Coupon already exists."}})
    cp = {"id": cid, "object": "coupon", "amount_off": int(p["amount_off"]), "currency": p["currency"], "duration": p.get("duration"),
          "max_redemptions": int(p["max_redemptions"]), "redeem_by": int(p["redeem_by"]), "times_redeemed": 0, "valid": True, "name": p.get("name"),
          "metadata": {k[9:-1]: v for k, v in p.items() if k.startswith("metadata[")}}
    COUPONS[cid] = cp
    return self._send(200, cp)


def _get(self):
    path = urlsplit(self.path).path
    if not path.startswith("/v1/coupons/"):
        return _GET(self)
    cp = COUPONS.get(path.rsplit("/", 1)[1])
    return self._send(200, cp) if cp else self._send(404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}})


H.StubHandler.do_POST, H.StubHandler.do_GET = _post, _get
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
from _lib import pay  # noqa: E402
from _lib import preview as P  # noqa: E402
from _lib import voucher as V  # noqa: E402
from _lib.styles import eye as EYE  # noqa: E402

DASH = "[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]"
PACK = json.load(open(os.path.join(REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
H.Fake.legal = dict(PACK, making_start="after_confirmation")
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
LEGACY = list(CT.legacy_ids())
STYLE = next((s for s in LEGACY if not CT.is_black(s)), LEGACY[0])
BLACK = next((s for s in LEGACY if CT.is_black(s)), None)


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=300)
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


def webhook(obj):
    body, sig = H.signed_event(obj, "checkout.session.completed")
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=180)
    return r.status_code, r.json()


def params_of(sid):
    want = H.Fake.sessions[sid]
    for p, _h in reversed(H.Fake.creates):
        meta = {k[9:-1]: v for k, v in p.items() if k.startswith("metadata[")}
        if meta == want["metadata"] and p.get("client_reference_id") is not None:
            return p
    return None


def complete(sid, email="kunde@example.com"):
    """Stripe completes a session: a coupon in its discounts is taken off the total (and counted once); a total of 0 is a no-cost session."""
    s = H.Fake.sessions[sid]
    p = params_of(sid)
    base = int(p["line_items[0][price_data][unit_amount]"])
    cid = p.get("discounts[0][coupon]")
    off = 0
    if cid:
        cp = COUPONS[cid]
        assert cp["valid"] and cp["times_redeemed"] < cp["max_redemptions"], cp
        off = min(cp["amount_off"], base)
        cp["times_redeemed"] += 1
        cp["valid"] = cp["times_redeemed"] < cp["max_redemptions"]
        s["discounts"] = [{"coupon": cid}]
    total = base - off
    s.update(status="complete", amount_total=total, total_details={"amount_discount": off, "amount_shipping": 0, "amount_tax": 0},
             customer_details={"email": email}, payment_status="paid" if total else "no_payment_required",
             payment_intent=("pi_test_" + os.urandom(6).hex()) if total else None)
    return s


_EYES = {}


def draft(name="blue_round", lang="en", n=1):
    if name not in _EYES:
        jpeg = SI.jpeg_bytes(name)
        prof = EYE.profile_of_bytes(jpeg, pad=1.12, rules=("lid", "fill"))
        _EYES[name] = P.protect(Image.open(io.BytesIO(jpeg)).convert("RGB"), jpeg, profile=prof)["sealed"]
    o = k = None
    for i in range(1, n + 1):
        body = {"action": "draft", "eye": i, "crop": H.jpeg_b64(256, 10 + i), "pad": 1.12, "ticket": H.fresh_ticket(), "lang": lang, "ref": f"e{i}",
                "sealed": _EYES[name]}
        if o:
            body.update(order=o, k=k)
        c, j = post("/api/order", body)
        assert c == 200, (c, j)
        o, k = j["order"], j["k"]
    return o, k


def co(o, k, eyes=1, style=None, **kw):
    body = {"order": o, "k": k, "eyes": eyes, "style": style or STYLE, "names": "", "title": "", "lang": kw.pop("lang", "en"), "consent_digital": True}
    body.update(kw)
    return post("/api/checkout", body)


def buy_voucher(kind="one", market="lt", lang="lt", email="pirkejas@example.com"):
    c, j = post("/api/checkout", {"gift": {"kind": kind}, "market": market, "lang": lang})
    assert c == 200, (c, j)
    sid = next(s for s, x in H.Fake.sessions.items() if x["url"] == j["url"])
    sess = H.pay_session(sid, email)
    c2, j2 = webhook(sess)
    assert c2 == 200, (c2, j2)
    return sid, V.code_for(sid)


# ============================================================================================ 1. the code
section("1. the code, the markets and the values")
c1, c2 = V.code_for("cs_test_" + "a" * 24), V.code_for("cs_test_" + "a" * 24)
c3 = V.code_for("cs_test_" + "b" * 24)
check("the code of a session is the same every time and another session's is another; 12 characters of the alphabet without 0, O, 1 and I",
      c1 == c2 and c1 != c3 and len(c1) == 12 and all(ch in V.ALPHABET for ch in c1) and not set("01OI") & set(V.ALPHABET), (c1, c3))
check("a typed code is read with dashes, spaces and in lower case; a code with 0, O, 1 or I, or of another length, is not a code",
      V.normal(f" {V.shown(c1).lower()} ") == c1 and V.normal(c1[:4] + " " + c1[4:]) == c1 and V.normal("ABCD-EFGH-JKL") is None
      and V.normal("ABCD-EFGH-JKL0") is None and V.normal("ABCD-EFGH-JKLO") is None and V.normal(None) is None and V.normal("x" * 50) is None, V.shown(c1))
check("the coupon id is a one-way hash of the code (gift_ and 24 hex), not the code", re.fullmatch(r"gift_[0-9a-f]{24}", V.coupon_id(c1)) is not None
      and c1.lower() not in V.coupon_id(c1), V.coupon_id(c1))
check("vouchers are sold in the euro markets of the EU edition only (eu, lt, hr), at the standard one-eye art and two-eye prices",
      V.markets() == ("eu", "lt", "hr") and V.value_of("one", "lt") == pay.price_list("lt")["one_eye_art"] == 2497
      and V.value_of("two", "eu") == pay.price_list("eu")["two_eyes"] == 3997, (V.markets(), V.value_of("one", "lt")))
src = "\n".join(open(os.path.join(API, f), encoding="utf-8").read() for f in ("_lib/voucher.py", "checkout.py", "stripe_webhook.py"))
check("the new server code holds no dash", not re.search(DASH, src), re.findall(DASH, src)[:3])

# ============================================================================================ 2. buying
section("2. buying a voucher: the Stripe session")
n0 = len(H.Fake.creates)
c, j = post("/api/checkout", {"gift": {"kind": "one"}, "market": "lt", "lang": "lt"})
p = H.Fake.creates[-1][0] if len(H.Fake.creates) > n0 else {}
check("POST /api/checkout {gift: one} opens a Stripe page: mode payment, euros, the one-eye art price, the Lithuanian name and note, the voucher metadata, no discount, no order",
      c == 200 and j.get("url", "").startswith("https://") and j.get("value") == 2497 and p.get("mode") == "payment"
      and p.get("line_items[0][price_data][currency]") == "eur" and p.get("line_items[0][price_data][unit_amount]") == "2497"
      and p.get("line_items[0][price_data][product_data][name]") == V.NAME["one"]["lt"] and p.get("custom_text[submit][message]") == V.SUBMIT["lt"]
      and p.get("metadata[kind]") == "voucher" and p.get("metadata[voucher_kind]") == "one" and p.get("metadata[voucher_value]") == "2497"
      and p.get("metadata[market]") == "lt" and "metadata[order]" not in p and not any(k.startswith("discounts") for k in p) and p.get("locale") == "lt", (c, j, p))
check("its success page is /gift with the session id and the language (and the market), its cancel page says cancelled",
      p.get("success_url", "").endswith("/gift?lang=lt&s={CHECKOUT_SESSION_ID}&m=lt") and "/gift?lang=lt&cancelled=1" in p.get("cancel_url", ""), p.get("success_url"))
c, j = post("/api/checkout", {"gift": {"kind": "two"}, "market": "eu", "lang": "en"})
p = H.Fake.creates[-1][0]
check("a two-eye voucher costs the two-eye price, in English on the default market", c == 200 and p.get("line_items[0][price_data][unit_amount]") == "3997"
      and p.get("line_items[0][price_data][product_data][name]") == V.NAME["two"]["en"] and "&m=" not in p.get("success_url", ""), (c, p.get("success_url")))
c, j = post("/api/checkout", {"gift": {"kind": "three"}, "market": "lt", "lang": "lt"})
check("an unknown kind: 400", c == 400, (c, j))
for m in ("au", "us", "hu", "uk"):
    c, j = post("/api/checkout", {"gift": {"kind": "one"}, "market": m, "lang": "en"})
    check(f"market {m}: 409 voucher_market (vouchers are sold in euros only)", c == 409 and j.get("reason") == "voucher_market" and j.get("markets") == ["eu", "lt", "hr"], (c, j))

# ============================================================================================ 3. paid
section("3. paid: the coupon, the record, the email, the note")
H.Fake.emails.clear()
COUPON_CREATES.clear()
c, j = post("/api/checkout", {"gift": {"kind": "one"}, "market": "lt", "lang": "lt"})
sid = next(s for s, x in H.Fake.sessions.items() if x["url"] == j["url"])
code = V.code_for(sid)
cid = V.coupon_id(code)
c0, j0 = get(f"/api/checkout?gift={sid}")
check("before the payment the success page hears pending", c0 == 200 and j0.get("state") == "pending", (c0, j0))
sess = H.pay_session(sid, "pirkejas@example.com")
c, j = webhook(sess)
cp = COUPONS.get(cid) or {}
days = (cp.get("redeem_by", 0) - time.time()) / 86400
check("the webhook makes the coupon: its id from the code, the voucher's value off, one redemption, valid to the end of the day a year on, the session in its metadata",
      c == 200 and j.get("voucher") is True and j.get("state") == "ready" and cp.get("amount_off") == 2497 and cp.get("currency") == "eur"
      and cp.get("max_redemptions") == 1 and 364 < days < 366.1 and cp["metadata"].get("voucher_session") == sid and cp.get("name") == V.COUPON_NAME["lt"], (c, j, cp))
rec = rj(f"vouchers/{cid}.json") or {}
check("the record holds the voucher, not the buyer: kind, value, dates, session, the code's last four; no email address and no code",
      rec.get("kind") == "one" and rec.get("value") == 2497 and rec.get("session_id") == sid and rec.get("code_end") == code[-4:]
      and "pirkejas" not in json.dumps(rec) and code not in json.dumps(rec) and rec.get("valid_until"), rec)
mails = [m for m, _i in H.Fake.emails if m.get("to") == ["pirkejas@example.com"]]
m = mails[0] if mails else {}
check("the buyer gets one email in Lithuanian with the code, its value, its last day and the link to /try, then the withdrawal information and the terms as text",
      len(mails) == 1 and V.shown(code) in m.get("subject", "") and V.shown(code) in m.get("text", "") and pay.price_text(2497, "lt", "eur") in m.get("text", "")
      and "/try?lang=lt" in m.get("text", "") and "Dovanų kuponai" in m.get("text", "") and "14 dienų" in m.get("text", "")
      and len(m.get("text", "")) > 5000 and "Turiu dovanų kuponą" in m.get("text", ""), (len(mails), m.get("subject"), m.get("text", "")[:400]))
check("the owner is told once that a voucher was sold, with the coupon and how to cancel it", any("gift voucher sold" in x.get("subject", "") and cid in x.get("text", "")
      for x, _i in H.Fake.emails), [x.get("subject") for x, _i in H.Fake.emails])
n_mail, n_cp = len(H.Fake.emails), len(COUPON_CREATES)
c, j = webhook(sess)
c2, j2 = get(f"/api/checkout?gift={sid}")
check("a replayed webhook and the success page change nothing: no second email, no second coupon (the record is there)", c == 200 and len(H.Fake.emails) == n_mail
      and len(COUPON_CREATES) == n_cp and j.get("mail") == "done", (c, j, len(H.Fake.emails) - n_mail, len(COUPON_CREATES) - n_cp))
check("GET /api/checkout?gift=<session>: ready, the code as people read it, the kind, the value, the last day, the email sent",
      c2 == 200 and j2.get("state") == "ready" and j2.get("code") == V.shown(code) and j2.get("kind") == "one" and j2.get("value") == 2497
      and j2.get("valid_until") == rec.get("valid_until") and j2.get("mail") == "done", j2)
c, j = get("/api/checkout?gift=cs_test_nonexistent00000")
c3, j3 = get("/api/checkout?gift=nonsense")
check("an unknown session: unknown; a value that is no session id: 400", c == 200 and j.get("state") == "unknown" and c3 == 400, (c, j, c3, j3))
o, k = draft()
c, j = co(o, k)
osid = rj(f"orders/{o}/order.json")["checkout"]["session_id"]
c, j = get(f"/api/checkout?gift={osid}")
check("an ORDER's session id asked as a voucher: unknown (no code is ever derived for it)", c == 200 and j.get("state") == "unknown" and "code" not in j, j)
# a busy email is retried by Stripe
c, j = post("/api/checkout", {"gift": {"kind": "two"}, "market": "hr", "lang": "hr"})
sid_b = next(s for s, x in H.Fake.sessions.items() if x["url"] == j["url"])
H.Fake.fail_mail[:] = [503, 503]      # the owner's note and the buyer's email
cb, jb = webhook(H.pay_session(sid_b, "kupac@example.com"))
H.Fake.fail_mail[:] = []
cb2, jb2 = webhook(H.Fake.sessions[sid_b])
mails_b = [m for m, _i in H.Fake.emails if m.get("to") == ["kupac@example.com"]]
check("Resend busy: the webhook answers 503 (Stripe retries), the retry sends the Croatian email once and the owner's note", cb == 503 and cb2 == 200
      and jb2.get("mail") == "sent" and len(mails_b) == 1 and "poklon-bon" in mails_b[0].get("subject", "").lower()
      and sum(1 for x, _i in H.Fake.emails if "gift voucher sold" in x.get("subject", "") and sid_b in x.get("text", "")) == 1, (cb, jb, cb2, jb2, len(mails_b)))
# a voucher session paid at another amount: no code
c, j = post("/api/checkout", {"gift": {"kind": "one"}, "market": "eu", "lang": "en"})
sid_x = next(s for s, x in H.Fake.sessions.items() if x["url"] == j["url"])
sx = H.pay_session(sid_x, "odd@example.com")
sx["amount_total"] = 100
n_cp = len(COUPONS)
c, j = webhook(sx)
check("a voucher session paid at another amount: refused, no coupon, the owner told to check and refund", c == 200 and j.get("state") == "refused" and len(COUPONS) == n_cp
      and any("does not match its price" in x.get("subject", "") for x, _i in H.Fake.emails), (c, j))

# ============================================================================================ 4. checking a code
section("4. checking a code at the checkout")
c, j = get(f"/api/checkout?voucher={V.shown(code).lower()}&m=lt")
check("GET /api/checkout?voucher=<code>&m=lt: valid, its value and last day (typed in lower case with dashes)", c == 200 and j.get("valid") is True
      and j.get("value") == 2497 and j.get("currency") == "EUR" and j.get("valid_until") == rec.get("valid_until"), (c, j))
for q, why in ((f"{code}&m=au", "currency"), (f"{code}&m=hu", "currency"), ("ABCDEFGHJKLM&m=lt", "unknown"), ("ABC&m=lt", "format"), ("ABCD-EFGH-JKL0&m=lt", "format")):
    c, j = get(f"/api/checkout?voucher={q}")
    check(f"a code checked as {q.split('&')[0][:14]} for {q.split('m=')[1]}: 409 voucher_invalid, why {why}", c == 409 and j.get("reason") == "voucher_invalid"
          and j.get("why") == why, (c, j))

# ============================================================================================ 5. redeeming
section("5. redeeming: the order's checkout and its payment")
price1 = pay.price_cents(1, STYLE, "lt")
o, k = draft(lang="lt")
n0 = len(H.Fake.creates)
c, j = co(o, k, lang="lt", market="lt", voucher=V.shown(code))
p = H.Fake.creates[-1][0] if len(H.Fake.creates) > n0 else {}
check(f"the order's checkout with the code ({price1} cents, a voucher of 2497): the coupon is the session's discount, the metadata names it, nothing is left to pay",
      c == 200 and p.get("discounts[0][coupon]") == cid and p.get("metadata[voucher]") == cid and p.get("metadata[voucher_value]") == "2497"
      and j.get("voucher") == {"value": 2497, "discount": min(2497, price1), "pay": max(0, price1 - 2497)} and j.get("amount") == price1, (c, j, p))
check("a voucher that pays for everything: no payment_intent_data (Stripe makes no PaymentIntent for a no-cost session)",
      price1 > 2497 or not any(k_.startswith("payment_intent_data") for k_ in p), [k_ for k_ in p if k_.startswith("payment_intent_data")])
orec = rj(f"orders/{o}/order.json")["checkout"]
check("order.json's checkout keeps the voucher (its coupon, value and discount)", orec.get("voucher") == {"coupon": cid, "value": 2497, "discount": min(2497, price1)}, orec)
sid_o = orec["session_id"]
H.Fake.emails.clear()
s_o = complete(sid_o)
c, j = webhook(s_o)
pj = rj(f"orders/{o}/paid.json") or {}
check("Stripe completes it as a no-cost session (no_payment_required, 0): the webhook records the order as PAID, with the voucher, and no amount mismatch",
      price1 > 2497 or (c == 200 and pj.get("paid") is True and pj.get("amount_total") == 0 and "amount_mismatch" not in pj
                        and pj.get("voucher", {}).get("coupon") == cid and pj["voucher"].get("discount") == price1 and pj["voucher"].get("price") == price1), (c, j, pj))
conf = next((m for m, _i in H.Fake.emails if o in m.get("subject", "") and m.get("to") == ["kunde@example.com"]), {})
check("the confirmation's price row: the price, the voucher and what was paid (Lithuanian)", "dovanų kuponas −" in conf.get("text", "")
      and "sumokėta 0,00" in conf.get("text", "").replace("\u00a0", " "), conf.get("text", "")[:1200])
check("the owner's note of the order names the voucher", any("Gift voucher: " + cid in x.get("text", "") for x, _i in H.Fake.emails), "")
c, j = get(f"/api/checkout?voucher={code}&m=lt")
check("the code once used: 409 voucher_invalid, why used", c == 409 and j.get("why") == "used", (c, j))
o2, k2 = draft()
n0 = len(H.Fake.creates)
c, j = co(o2, k2, voucher=code)
check("an order's checkout with a used code: 409 voucher_invalid used, no Stripe session made, the order record unchanged", c == 409 and j.get("reason") == "voucher_invalid"
      and j.get("why") == "used" and len(H.Fake.creates) == n0 and "checkout" not in (rj(f"orders/{o2}/order.json") or {}), (c, j))
sid1, code1 = buy_voucher("one", "eu", "en", "a@example.com")
# two eyes with a one-eye voucher: the two-eye price less the voucher is paid by card (the first legacy style that takes two eyes)
sid2, code2 = buy_voucher("one", "lt", "en", "b@example.com")
o4, k4 = draft(lang="en", n=2)
c, j = 0, {}
for s2 in LEGACY:
    c, j = co(o4, k4, eyes=2, style=s2, voucher=code2)
    if c == 200:
        break
if c != 200:
    check("a two-eye order with a one-eye voucher: the checkout opens", False, (c, j))
else:
    price2 = j.get("amount")
    p4 = H.Fake.creates[-1][0]
    check("a two-eye order with a one-eye voucher: the discount is the voucher, the rest is to pay, payment_intent_data stays",
          j.get("voucher") == {"value": 2497, "discount": 2497, "pay": price2 - 2497} and any(k_.startswith("payment_intent_data") for k_ in p4), (j, price2))
    H.Fake.emails.clear()
    s4 = complete(rj(f"orders/{o4}/order.json")["checkout"]["session_id"])
    c, jw = webhook(s4)
    pj4 = rj(f"orders/{o4}/paid.json") or {}
    conf4 = next((m for m, _i in H.Fake.emails if o4 in m.get("subject", "") and m.get("to") == ["kunde@example.com"]), {})
    check("paid by card for the rest (payment_status paid): the order is paid, amount_total the rest, no mismatch, the email says price, voucher and paid",
          pj4.get("paid") is True and pj4.get("amount_total") == price2 - 2497 and "amount_mismatch" not in pj4 and pj4["voucher"]["discount"] == 2497
          and "gift voucher −" in conf4.get("text", "") and "paid " in conf4.get("text", ""), (pj4, conf4.get("text", "")[:900]))
# a cheaper order than the voucher: the rest is not paid out
if BLACK:
    sid5, code5 = buy_voucher("one", "lt", "en", "c@example.com")
    o5, k5 = draft()
    c, j = co(o5, k5, style=BLACK, voucher=code5)
    pb = pay.price_cents(1, BLACK, "eu")
    check(f"a cheaper order ({pb} cents) with a 2497 voucher: the discount is the order's price, nothing to pay, no payment_intent_data",
          c == 200 and j.get("voucher") == {"value": 2497, "discount": pb, "pay": 0}
          and not any(k_.startswith("payment_intent_data") for k_ in H.Fake.creates[-1][0]), (c, j))
    s5 = complete(rj(f"orders/{o5}/order.json")["checkout"]["session_id"])
    webhook(s5)
    pj5 = rj(f"orders/{o5}/paid.json") or {}
    check("its payment: no-cost, paid, no mismatch (the price less the voucher is never below 0)", pj5.get("paid") is True and pj5.get("amount_total") == 0
          and "amount_mismatch" not in pj5 and pj5["voucher"]["discount"] == pb, pj5)
c, j = co(*draft(), market="au", voucher=code1)
check("a voucher at the checkout of an order in another currency (au): 409 voucher_invalid currency", c == 409 and j.get("why") == "currency", (c, j))

# ============================================================================================ 6. session_paid
section("6. pay.session_paid and no-cost sessions")
check("a no-cost session counts as paid only with amount_total 0; an unpaid or open one never",
      pay.session_paid({"status": "complete", "payment_status": "no_payment_required", "amount_total": 0})
      and not pay.session_paid({"status": "complete", "payment_status": "no_payment_required", "amount_total": 100})
      and not pay.session_paid({"status": "open", "payment_status": "no_payment_required", "amount_total": 0})
      and not pay.session_paid({"status": "complete", "payment_status": "unpaid", "amount_total": 0})
      and pay.session_paid({"status": "complete", "payment_status": "paid", "amount_total": 2497}), "")
from _lib import abtest  # noqa: E402
check("a price test's session check adds back what a voucher took off (Stripe's amount_discount), only for a session the server made with a voucher",
      abtest.voucher_discount({"metadata": {"voucher": "gift_" + "0" * 24}, "total_details": {"amount_discount": 2497}}) == 2497
      and abtest.voucher_discount({"metadata": {}, "total_details": {"amount_discount": 2497}}) == 0
      and abtest.voucher_discount({"metadata": {"voucher": "gift_" + "0" * 24}}) == 0, "")

# ============================================================================================ 7. the legal texts
section("7. the legal texts")
docs = PACK.get("docs") or {}
ed = PACK.get("editions") or {}


def text(doc, lang, edition=None):
    d = ((ed.get(edition) or {}).get(lang) if edition else docs.get(lang)) or {}
    return (d.get(doc) or {}).get("text", "")


words = {l: (t, pay.price_text(2497, l, "eur").replace("\u00a0", " "), pay.price_text(3997, l, "eur").replace("\u00a0", " ")) for l, t in
         (("en", "Gift vouchers"), ("de", "Geschenkgutscheine"), ("lt", "Dovanų kuponai"), ("hu", "Ajándékutalványok"), ("hr", "Poklon-bonovi"))}
check("the EU terms in every language have the voucher section with the two prices, 12 months and the 14 days", all(
    w[0] in text("terms", l).replace("\u00a0", " ") and w[1] in text("terms", l).replace("\u00a0", " ") and w[2] in text("terms", l).replace("\u00a0", " ")
    and "12" in text("terms", l) and "14" in text("terms", l) for l, w in words.items()), [l for l, w in words.items() if w[0] not in text("terms", l)])
hu_t = text("terms", "hu", "hu").replace("\u00a0", " ")
check("the Hungarian edition's terms (forints) say vouchers are euros only and print no euro price", "Ajándékutalványok" in hu_t and "csak euróban" in hu_t
      and words["hu"][1] not in hu_t and words["hu"][2] not in hu_t, hu_t[:200])
check("the Australian and the US terms have no voucher", "voucher" not in text("terms", "en", "au").lower() and "voucher" not in text("terms", "en", "us").lower(), "")
check("the EU withdrawal page in every language has the voucher section (14 days while unused)", all(w[0] in text("withdrawal", l) for l, w in words.items()),
      [l for l, w in words.items() if w[0] not in text("withdrawal", l)])
priv = json.dumps(PACK, ensure_ascii=False)
check("the privacy policy's voucher section is in the build (no email address kept in the record, the code derived)", "Our own record of the voucher holds no email address" in priv
      or os.path.isfile(os.path.join(REPO, "src", "legal", "docs", "vouchers.ts")), "")

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
