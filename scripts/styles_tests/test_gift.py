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
  8.  value vouchers (the owner's decision of 2026-11-25): an amount and a balance. The ledger (a reservation per checkout, write-once entries, a fresh
      single-use coupon per session), the balance across two orders, the release when a checkout is replaced, the commit when it is paid, the settling of a
      reservation nobody closed (expired: released; redeemed: paid), two checkouts at once never spend the same balance, a voucher more and less than the
      total, an expired one, another currency, the check of the page with its own order left out; the voucher's own coupon is never redeemed
  9.  the latest checkout of a value voucher wins: a new order's checkout expires the pages of the voucher's other open reservations and releases them (a
      paid page is marked paid, never released; a settling page and a checkout in flight stay); a remainder to pay is 0 or at least 0.50 EUR; Stripe's note
      when a voucher is bought says nothing about withdrawal
Since the owner's decision of 2026-11-25 (value vouchers) the gift page sells amounts only; a voucher of the old kinds (one, two) is made here as a payment page
opened before that day and paid after it (old_voucher), and sections 3 to 5 hold that such a voucher works exactly as it was sold.

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


def buy_value(amount=10000, market="lt", lang="lt", email="pirkejas@example.com"):
    """A value voucher bought on the gift page and paid (the owner's decision of 2026-11-25): (session id, code)."""
    c, j = post("/api/checkout", {"gift": {"amount": amount}, "market": market, "lang": lang})
    assert c == 200, (c, j)
    sid = next(s for s, x in H.Fake.sessions.items() if x["url"] == j["url"])
    c2, j2 = webhook(H.pay_session(sid, email))
    assert c2 == 200, (c2, j2)
    return sid, V.code_for(sid)


def old_session(kind="one", market="lt", lang="lt"):
    """The Stripe session of a voucher of an OLD kind, as the server made it before the owner's decision of 2026-11-25 (still open at the release, paid after it)."""
    value = V.value_of(kind, market)
    sid = "cs_test_" + os.urandom(12).hex()
    meta = {"kind": "voucher", "voucher_kind": kind, "voucher_value": str(value), "market": market, "currency": "eur", "lang": lang, "ref": "gift-" + os.urandom(8).hex()}
    H.Fake.sessions[sid] = {"id": sid, "object": "checkout.session", "mode": "payment", "status": "open", "payment_status": "unpaid", "currency": "eur",
                            "amount_total": value, "metadata": meta, "url": f"https://checkout.stripe.test/c/pay/{sid}", "livemode": False, "customer_details": None,
                            "payment_intent": None, "expires_at": int(time.time()) + 3600}
    return sid


def buy_voucher(kind="one", market="lt", lang="lt", email="pirkejas@example.com"):
    """A voucher of an old kind, paid after the change (old_session): (session id, code)."""
    sid = old_session(kind, market, lang)
    c2, j2 = webhook(H.pay_session(sid, email))
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
check("vouchers are sold in the euro markets of the EU edition only (eu, lt, hr), at the standard one-eye art and two-eye prices"
      " - 1125 (value vouchers): the old kinds keep their values (read for the vouchers sold before); what is sold now is one of five amounts",
      V.markets() == ("eu", "lt", "hr") and V.value_of("one", "lt") == pay.price_list("lt")["one_eye_art"] == 2497
      and V.value_of("two", "eu") == pay.price_list("eu")["two_eyes"] == 3997 and V.AMOUNTS == (3000, 6000, 10000, 12000, 17000), (V.markets(), V.value_of("one", "lt")))
src = "\n".join(open(os.path.join(API, f), encoding="utf-8").read() for f in ("_lib/voucher.py", "checkout.py", "stripe_webhook.py"))
check("the new server code holds no dash", not re.search(DASH, src), re.findall(DASH, src)[:3])

# ============================================================================================ 2. buying
section("2. buying a voucher: the Stripe session")
n0 = len(H.Fake.creates)
c, j = post("/api/checkout", {"gift": {"amount": 10000}, "market": "lt", "lang": "lt"})
p = H.Fake.creates[-1][0] if len(H.Fake.creates) > n0 else {}
check("POST /api/checkout {gift: one} opens a Stripe page: mode payment, euros, the one-eye art price, the Lithuanian name and note, the voucher metadata, no discount, no order"
      " - 1125 (value vouchers): {gift: {amount: 10000}}, the amount as the price, the voucher's name and its description (artworks and prints, 12 months), kind value",
      c == 200 and j.get("url", "").startswith("https://") and j.get("value") == 10000 and j.get("kind") == "value" and p.get("mode") == "payment"
      and p.get("line_items[0][price_data][currency]") == "eur" and p.get("line_items[0][price_data][unit_amount]") == "10000"
      and p.get("line_items[0][price_data][product_data][name]") == V.NAME["value"]["lt"] == "SnapEyes dovanų kuponas"
      and p.get("line_items[0][price_data][product_data][description]") == V.DESC_VALUE["lt"] and "spaudiniams" in V.DESC_VALUE["lt"]
      and p.get("custom_text[submit][message]") == V.SUBMIT["lt"]
      and p.get("metadata[kind]") == "voucher" and p.get("metadata[voucher_kind]") == "value" and p.get("metadata[voucher_value]") == "10000"
      and p.get("metadata[market]") == "lt" and "metadata[order]" not in p and not any(k.startswith("discounts") for k in p) and p.get("locale") == "lt", (c, j, p))
check("its success page is /gift with the session id and the language (and the market), its cancel page says cancelled",
      p.get("success_url", "").endswith("/gift?lang=lt&s={CHECKOUT_SESSION_ID}&m=lt") and "/gift?lang=lt&cancelled=1" in p.get("cancel_url", ""), p.get("success_url"))
got = []
for a in (3000, 6000, 12000, 17000):
    c, j = post("/api/checkout", {"gift": {"amount": a}, "market": "eu", "lang": "en"})
    got.append((c, H.Fake.creates[-1][0].get("line_items[0][price_data][unit_amount]"), "&m=" in H.Fake.creates[-1][0].get("success_url", "")))
check("a two-eye voucher costs the two-eye price, in English on the default market - 1125: every one of the five amounts is sold at its amount (the default market: no m)",
      got == [(200, "3000", False), (200, "6000", False), (200, "12000", False), (200, "17000", False)], got)
bad = [post("/api/checkout", {"gift": g, "market": "lt", "lang": "lt"})[0] for g in ({"kind": "three"}, {"kind": "one"}, {"kind": "two"}, {"amount": 5000}, {"amount": "10000"},
                                                                                   {"amount": 10000.0}, {"amount": True}, {})]
check("an unknown kind: 400 - 1125: the old kinds are not sold any more, and an amount that is not one of the five (or not a whole number of cents): 400",
      bad == [400] * 8, bad)
for m in ("au", "us", "hu", "uk"):
    c, j = post("/api/checkout", {"gift": {"amount": 3000}, "market": m, "lang": "en"})
    check(f"market {m}: 409 voucher_market (vouchers are sold in euros only)", c == 409 and j.get("reason") == "voucher_market" and j.get("markets") == ["eu", "lt", "hr"], (c, j))

# ============================================================================================ 3. paid
section("3. paid: the coupon, the record, the email, the note")
H.Fake.emails.clear()
COUPON_CREATES.clear()
# 1125: a voucher of the old kind "one" (a payment page opened before the owner's decision of 2026-11-25, paid after it): it is made as it was sold
sid = old_session("one", "lt", "lt")
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
check("the owner is told once that a voucher was sold, with the coupon and how to cancel it", any("nupirktas dovanų kuponas" in x.get("subject", "") and cid in x.get("text", "")
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
sid_b = old_session("two", "hr", "hr")
H.Fake.fail_mail[:] = [503, 503]      # the owner's note and the buyer's email
cb, jb = webhook(H.pay_session(sid_b, "kupac@example.com"))
H.Fake.fail_mail[:] = []
cb2, jb2 = webhook(H.Fake.sessions[sid_b])
mails_b = [m for m, _i in H.Fake.emails if m.get("to") == ["kupac@example.com"]]
check("Resend busy: the webhook answers 503 (Stripe retries), the retry sends the Croatian email once and the owner's note", cb == 503 and cb2 == 200
      and jb2.get("mail") == "sent" and len(mails_b) == 1 and "poklon-bon" in mails_b[0].get("subject", "").lower()
      and sum(1 for x, _i in H.Fake.emails if "nupirktas dovanų kuponas" in x.get("subject", "") and sid_b in x.get("text", "")) == 1, (cb, jb, cb2, jb2, len(mails_b)))
# a voucher session paid at another amount: no code
sid_x = old_session("one", "eu", "en")
sx = H.pay_session(sid_x, "odd@example.com")
sx["amount_total"] = 100
n_cp = len(COUPONS)
c, j = webhook(sx)
check("a voucher session paid at another amount: refused, no coupon, the owner told to check and refund", c == 200 and j.get("state") == "refused" and len(COUPONS) == n_cp
      and any("does not match its price" in x.get("subject", "") for x, _i in H.Fake.emails), (c, j))
check("the record of a voucher of an old kind has no ledger (it is used once, as it was sold), its coupon pays its value", "ledger" not in rec and rec.get("kind") == "one"
      and (COUPONS.get(cid) or {}).get("metadata", {}).get("voucher_kind") == "one", rec)
# 1125: a value voucher (the owner's decision of 2026-11-25), paid
H.Fake.emails.clear()
c, j = post("/api/checkout", {"gift": {"amount": 12000}, "market": "lt", "lang": "lt"})
sid_v = next(s for s, x in H.Fake.sessions.items() if x["url"] == j["url"])
vcode = V.code_for(sid_v)
vcid = V.coupon_id(vcode)
cv, jv = webhook(H.pay_session(sid_v, "dovana@example.com"))
vrec = rj(f"vouchers/{vcid}.json") or {}
vcp = COUPONS.get(vcid) or {}
check("a value voucher paid: its own coupon (the amount, kind value, one redemption, a year), its record with kind value, the amount and ledger 1 (no email, no code)",
      cv == 200 and jv.get("state") == "ready" and vcp.get("amount_off") == 12000 and vcp.get("metadata", {}).get("voucher_kind") == "value" and vcp.get("max_redemptions") == 1
      and vrec.get("kind") == "value" and vrec.get("value") == 12000 and vrec.get("ledger") == 1 and "dovana" not in json.dumps(vrec) and vcode not in json.dumps(vrec), (vrec, vcp))
vm = next((m for m, _i in H.Fake.emails if m.get("to") == ["dovana@example.com"]), {})
vt = vm.get("text", "")
check("its e-mail in Lithuanian: the code, the amount, \"Kam\" artworks and prints, the third step (what is left pays for a print or another order), the rules of a balance, "
      "the 14 days, the terms; never the rule of the old kinds (once, the rest not paid out)",
      V.shown(vcode) in vt and pay.price_text(12000, "lt", "eur") in vt and V.MAIL_VALUE["lt"]["kind"] in vt and V.MAIL_VALUE["lt"]["step3"] in vt
      and V.MAIL_VALUE["lt"]["rules"] in vt and "kelis užsakymus" in vt and "vieną kartą" not in vt.split("_____")[0] and "Turiu dovanų kuponą" in vt and "14 dienų" in vt
      and "Dovanų kuponai" in vt, [V.shown(vcode) in vt, V.MAIL_VALUE["lt"]["kind"] in vt, V.MAIL_VALUE["lt"]["step3"] in vt, V.MAIL_VALUE["lt"]["rules"] in vt, "vieną kartą" not in vt.split("_____")[0], vt[600:1800]])
cg, jg = get(f"/api/checkout?gift={sid_v}")
check("GET /api/checkout?gift=<session> of a value voucher: ready, kind value, the amount", cg == 200 and jg.get("state") == "ready" and jg.get("kind") == "value"
      and jg.get("value") == 12000 and jg.get("code") == V.shown(vcode), jg)
check("every language has the value voucher's e-mail words, without dashes", set(V.MAIL_VALUE) == set(V.MAIL) and all(
    v["step3"].startswith("3. ") and v["rules"] and v["kind"] and not re.search(DASH, json.dumps(v, ensure_ascii=False)) for v in V.MAIL_VALUE.values())
      and all(not re.search(DASH, x) for x in list(V.DESC_VALUE.values()) + list(V.NAME["value"].values())), "")

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


# 1125 (value vouchers): the terms list the five amounts the gift page sells (30 and 170 are looked for), no more the two prices of the old kinds
words = {l: (t, pay.price_text(3000, l, "eur").replace("\u00a0", " "), pay.price_text(17000, l, "eur").replace("\u00a0", " ")) for l, t in
         (("en", "Gift vouchers"), ("de", "Geschenkgutscheine"), ("lt", "Dovanų kuponai"), ("hu", "Ajándékutalványok"), ("hr", "Poklon-bonovi"),
          # 2026-11-13: the Finnish, Estonian and Latvian terms of the EU edition
          ("fi", "Lahjakortit"), ("et", "Kinkekaardid"), ("lv", "Dāvanu kartes"))}
check("the EU terms in every language have the voucher section with the two prices, 12 months and the 14 days"
      " - 1113: every language is eight (Finnish, Estonian, Latvian), exactly the languages of the pack - 1125: the amounts 30 and 170 instead of the two prices", set(words) == set(docs) and len(words) == 8 and all(
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


# ============================================================================================ 8. value vouchers
section("8. value vouchers (the owner's decision of 2026-11-25): the balance, the ledger, the races")
import threading  # noqa: E402
price1 = pay.price_cents(1, STYLE, "lt")


def sid_of(o_):
    return (rj(f"orders/{o_}/order.json") or {}).get("checkout", {}).get("session_id")


def states(cid_):
    return [e["state"] for e in V.view(cid_)]


sid30, code30 = buy_value(3000, "lt", "lt", "v30@example.com")
c30 = V.coupon_id(code30)
oa, ka = draft(lang="lt")
n0 = len(H.Fake.creates)
c, j = co(oa, ka, lang="lt", market="lt", voucher=V.shown(code30))
p = H.Fake.creates[-1][0] if len(H.Fake.creates) > n0 else {}
fresh = COUPONS.get(f"{c30}_s001") or {}
check(f"a 30 EUR voucher at the checkout of a {price1} cent artwork: a FRESH single-use coupon of its own (gift_<24 hex>_s001, the amount it pays, redeemable a little after the "
      "session ends), the metadata voucher, voucher_value, voucher_base, voucher_n, nothing to pay and no payment_intent_data; the voucher's own coupon is never the discount",
      c == 200 and price1 <= 3000 and p.get("discounts[0][coupon]") == f"{c30}_s001" and p.get("metadata[voucher]") == f"{c30}_s001"
      and p.get("metadata[voucher_value]") == str(price1) and p.get("metadata[voucher_base]") == c30 and p.get("metadata[voucher_n]") == "1"
      and j.get("voucher") == {"value": 3000, "discount": price1, "pay": 0} and not any(k_.startswith("payment_intent_data") for k_ in p)
      and fresh.get("amount_off") == price1 and fresh.get("max_redemptions") == 1 and 0 < fresh.get("redeem_by", 0) - int(p.get("expires_at", 0)) <= V.COUPON_MARGIN
      and fresh.get("metadata", {}).get("voucher") == c30 and fresh.get("metadata", {}).get("order") == oa, (c, j, {k_: v for k_, v in p.items() if "voucher" in k_ or "discount" in k_}, fresh))
led = V.view(c30)
first = sid_of(oa)
check("the ledger: entry 1 reserved for the artwork of that order, its amount, its session; order.json's checkout names the voucher, the entry and the balance it saw",
      len(led) == 1 and led[0]["state"] == "reserved" and led[0]["order"] == oa and led[0]["use"] == "artwork" and led[0]["amount"] == price1 and led[0]["session"] == first
      and (rj(f"orders/{oa}/order.json") or {}).get("checkout", {}).get("voucher") == {"coupon": f"{c30}_s001", "value": price1, "discount": price1, "base": c30, "n": 1,
                                                                                      "balance": 3000}, led)
cc1, jc1 = get(f"/api/checkout?voucher={code30}&m=lt")
cc2, jc2 = get(f"/api/checkout?voucher={code30}&m=lt&o={oa}")
check("the page's check: a reservation counts against the balance for everyone else (30.00 less the artwork left), but not for the order that holds it (o: all 30.00)"
      " - 1125 (the latest checkout wins): a reservation whose page exists is left out for everyone, since the next checkout expires that page first (section 9)",
      cc1 == 200 and jc1.get("value") == 3000 and cc2 == 200 and jc2.get("value") == 3000, (jc1, jc2))
c, j = co(oa, ka, lang="lt", market="lt", voucher=code30)
second = sid_of(oa)
check("the customer comes back from Stripe and checks out again: the earlier session is expired at Stripe and its reservation RELEASED; a new entry reserves anew, with a new coupon (s002)",
      c == 200 and first in H.Fake.expires and states(c30) == ["released", "reserved"] and H.Fake.creates[-1][0].get("discounts[0][coupon]") == f"{c30}_s002"
      and j.get("voucher") == {"value": 3000, "discount": price1, "pay": 0}, (c, j, states(c30)))
H.Fake.emails.clear()
cw, jw = webhook(complete(second, "pirmas@example.com"))
pj = rj(f"orders/{oa}/paid.json") or {}
check("paid as a no-cost session: the order is PAID with amount 0 and no mismatch, paid.json's voucher names the voucher (base) and its fresh coupon, entry 2 is PAID, "
      "and the voucher's own coupon was never redeemed",
      cw == 200 and pj.get("paid") is True and pj.get("amount_total") == 0 and "amount_mismatch" not in pj and pj.get("voucher", {}).get("base") == c30
      and pj["voucher"].get("coupon") == f"{c30}_s002" and pj["voucher"].get("discount") == price1 and states(c30) == ["released", "paid"]
      and COUPONS[c30]["times_redeemed"] == 0, (cw, jw, pj.get("voucher"), states(c30)))
conf = next((m for m, _i in H.Fake.emails if oa in m.get("subject", "") and m.get("to") == ["pirmas@example.com"]), {})
check("its confirmation's price row: the price, the gift voucher and 0 paid", "dovanų kuponas −" in conf.get("text", "") and "sumokėta 0,00" in conf.get("text", "").replace(" ", " "),
      conf.get("text", "")[:600])
cw2, _ = webhook(H.Fake.sessions[second])
check("a replayed webhook changes nothing in the ledger", cw2 == 200 and states(c30) == ["released", "paid"], states(c30))
cc, jc = get(f"/api/checkout?voucher={code30}&m=lt")
left = 3000 - price1
check("what is left stays on the voucher: the check says 30.00 less the artwork", cc == 200 and jc.get("value") == left, (cc, jc))
ob, kb = draft(lang="en")
c, j = co(ob, kb, voucher=code30)
pb = H.Fake.creates[-1][0]
check("a second order with the rest: the voucher pays what is left, the card the difference (payment_intent_data stays), the next entry and coupon (s003)",
      c == 200 and j.get("voucher") == {"value": left, "discount": left, "pay": price1 - left} and any(k_.startswith("payment_intent_data") for k_ in pb)
      and pb.get("discounts[0][coupon]") == f"{c30}_s003" and pb.get("metadata[voucher_value]") == str(left), (c, j))
webhook(complete(sid_of(ob)))
pjb = rj(f"orders/{ob}/paid.json") or {}
check("paid by card for the rest: amount_total is the price less the rest of the voucher, no mismatch; the voucher is spent (entry 3 paid)",
      pjb.get("paid") is True and pjb.get("amount_total") == price1 - left and "amount_mismatch" not in pjb and states(c30) == ["released", "paid", "paid"], (pjb, states(c30)))
cc, jc = get(f"/api/checkout?voucher={code30}&m=lt")
oc, kc = draft()
n0 = len(H.Fake.creates)
c, j = co(oc, kc, voucher=code30)
check("spent: the check says used, and a third order's checkout is 409 voucher_invalid used with no Stripe session and no order record touched",
      cc == 409 and jc.get("why") == "used" and c == 409 and j.get("why") == "used" and len(H.Fake.creates) == n0 and "checkout" not in (rj(f"orders/{oc}/order.json") or {}), (jc, j))

# more than the total, less than the total
s170, code170 = buy_value(17000, "hr", "hr", "v170@example.com")
od_, kd_ = draft(lang="hr")
c, j = co(od_, kd_, lang="hr", market="hr", voucher=code170)
webhook(complete(sid_of(od_)))
cc, jc = get(f"/api/checkout?voucher={code170}&m=lt")
check("a voucher worth more than the order (170.00 on an artwork): the artwork is free, the rest stays (170.00 less the artwork), in any euro market of the EU edition",
      c == 200 and j.get("voucher") == {"value": 17000, "discount": price1, "pay": 0} and (rj(f"orders/{od_}/paid.json") or {}).get("amount_total") == 0
      and jc.get("value") == 17000 - price1, (j, jc))
s30b, code30b = buy_value(3000, "eu", "en", "two@example.com")
oe, ke = draft(lang="en", n=2)
c, j = 0, {}
for s2 in LEGACY:
    c, j = co(oe, ke, eyes=2, style=s2, voucher=code30b)
    if c == 200:
        break
if c != 200:
    check("a voucher worth less than the order: the checkout opens", False, (c, j))
else:
    price2 = j.get("amount")
    webhook(complete(sid_of(oe)))
    pje = rj(f"orders/{oe}/paid.json") or {}
    check("a voucher worth less than the order (30.00 on two eyes): all of it is taken, the difference paid by card, no mismatch, nothing left",
          j.get("voucher") == {"value": 3000, "discount": 3000, "pay": price2 - 3000} and pje.get("amount_total") == price2 - 3000 and "amount_mismatch" not in pje
          and get(f"/api/checkout?voucher={code30b}&m=eu")[1].get("why") == "used", (j, pje))

# two checkouts at the same moment never spend the same balance twice
s60, code60 = buy_value(6000, "lt", "lt", "race@example.com")
c60 = V.coupon_id(code60)
g60 = V.lookup(code60, "lt")
got, errs = [], []


def racer(i):
    try:
        got.append(V.spend(g60, f"261125-race{i:02d}aaaaaaaaaaa", "artwork", 2497, int(time.time()) + 3600, "lt"))
    except Exception as e:  # noqa
        errs.append((getattr(e, "body", None) or {}).get("why") or type(e).__name__)


ts = [threading.Thread(target=racer, args=(i,)) for i in range(6)]
for t in ts:
    t.start()
for t in ts:
    t.join()
amounts = sorted(x["value"] for x in got)
check("six checkouts reserve a 60.00 voucher at once (a one-eye artwork each): exactly 60.00 is reserved (two artworks and the 10.06 left), each in an entry of its own; the other three are "
      "refused used; no balance is spent twice",
      amounts == [1006, 2497, 2497] and sorted(x["n"] for x in got) == [1, 2, 3] and errs == ["used"] * 3
      and sum(e["amount"] for e in V.view(c60) if e["state"] != "released") == 6000 and len({x["coupon"] for x in got}) == 3, (amounts, errs))
s30c, code30c = buy_value(3000, "lt", "lt", "race2@example.com")
o1, k1 = draft()
o2, k2 = draft()
both = []
th = [threading.Thread(target=lambda o_, k_: both.append(co(o_, k_, voucher=code30c)), args=a) for a in ((o1, k1), (o2, k2))]
for t in th:
    t.start()
for t in th:
    t.join()
disc = sorted((j_.get("voucher") or {}).get("discount", 0) for c_, j_ in both if c_ == 200)
v30c = V.view(V.coupon_id(code30c))
sess_ok = all(H.Fake.sessions[e["session"]]["status"] == ("expired" if e["state"] == "released" else "open") for e in v30c if e["session"])
check("two orders check out with one 30.00 voucher at the same moment: together they take exactly 30.00 (an artwork and the rest)"
      " - 1125 (the latest checkout wins): either both pages stand (an artwork and the rest, when neither saw the other's page) or the later one expired the earlier"
      " page and took the artwork's price; never more than 30.00 on open pages, and every released entry's page is expired at Stripe",
      len(both) == 2 and all(c_ == 200 for c_, _j in both) and disc in ([3000 - price1, price1], [price1, price1]) and sess_ok
      and sum(e["amount"] for e in v30c if e["state"] != "released") == (3000 if disc == [3000 - price1, price1] else price1), (disc, v30c))

# a reservation nobody closed is settled after its session's end from its own coupon
s30d, code30d = buy_value(3000, "lt", "lt", "settle@example.com")
c30d = V.coupon_id(code30d)
g = V.lookup(code30d, "lt")
past = int(time.time()) - V.SETTLE_GRACE - 30
sp_a = V.spend(g, "261125-settleaaaaaaaaaaaa", "artwork", 2000, past, "lt")
sp_b = V.spend(g, "261125-settlebbbbbbbbbbbb", "artwork", 500, past, "lt")
COUPONS[sp_b["coupon"]]["times_redeemed"] = 1         # Stripe counted its redemption: that session was paid (the webhook was lost)
sp_c = V.spend(g, "261125-settlecccccccccccc", "artwork", 300, int(time.time()) + 3600, "lt")
cc, jc = get(f"/api/checkout?voucher={code30d}&m=lt")
check("a reservation whose session ended and nobody closed: its own coupon decides (not redeemed: released, redeemed: paid); one still open keeps counting",
      [e["state"] for e in V.view(c30d)] == ["released", "paid", "reserved"] and jc.get("value") == 3000 - 500 - 300, (V.view(c30d), jc))
V.unspend(sp_c, "test")
check("a reservation whose session could not be made is given back (unspend)", states(c30d)[-1] == "released" and get(f"/api/checkout?voucher={code30d}&m=lt")[1].get("value") == 2500)

# expired, another currency, a print asked with an old voucher
s30e, code30e = buy_value(3000, "lt", "lt", "exp@example.com")
c30e = V.coupon_id(code30e)
rec_e = rj(f"vouchers/{c30e}.json")
store_path = os.path.join(STORE, "vouchers", f"{c30e}.json")
with open(store_path, "w", encoding="utf-8") as f:
    json.dump(dict(rec_e, valid_until="2025-11-24"), f)
ce, je = get(f"/api/checkout?voucher={code30e}&m=lt")
of_, kf_ = draft()
ce2, je2 = co(of_, kf_, voucher=code30e)
ca, ja = get(f"/api/checkout?voucher={code170}&m=au")
cau, jau = co(*draft(), market="au", voucher=code170)
check("an expired value voucher (its last day passed): 409 voucher_invalid expired, at the check and at the checkout; one of another market's currency (au): why currency",
      ce == 409 and je.get("why") == "expired" and ce2 == 409 and je2.get("why") == "expired" and ca == 409 and ja.get("why") == "currency"
      and cau == 409 and jau.get("why") == "currency", (je, je2, ja, jau))
s_old, code_old = buy_voucher("one", "lt", "lt", "old2@example.com")
cp1, jp1 = get(f"/api/checkout?voucher={code_old}&m=lt&o={oa}&u=print")
cp2, jp2 = get(f"/api/checkout?voucher={code30d}&m=lt&o={oa}&u=print")
check("the print offer's check (u=print): a voucher of an old kind pays for an artwork only (why artwork); a value voucher answers its balance",
      cp1 == 409 and jp1.get("why") == "artwork" and cp2 == 200 and jp2.get("value") == 2500, (jp1, jp2))
src_v = open(os.path.join(API, "_lib", "voucher.py"), encoding="utf-8").read()
check("the voucher's server code holds no dash (with the ledger)", not re.search(DASH, src_v), re.findall(DASH, src_v)[:3])

# ============================================================================================ 9. the latest checkout wins, the minimum charge
section("9. the latest checkout of a value voucher wins (an abandoned page never holds the balance); a remainder is 0 or at least Stripe's minimum")
s9, code9 = buy_value(3000, "lt", "lt", "latest@example.com")
c9 = V.coupon_id(code9)
oA, kA = draft(lang="lt")
c, jA = co(oA, kA, lang="lt", market="lt", voucher=code9)
sA = sid_of(oA)
cl, jl = get(f"/api/checkout?voucher={code9}&m=lt")
check("order A opens its payment page with the voucher and leaves the tab: a NEW order's check of the code already sees the full balance (A's page will be expired)",
      c == 200 and states(c9) == ["reserved"] and cl == 200 and jl.get("value") == 3000, (jA, jl))
oB, kB = draft(lang="lt")
n_exp = len(H.Fake.expires)
c, jB = co(oB, kB, lang="lt", market="lt", voucher=code9)
check("order B checks out with the same code: it gets the whole balance; A's session is expired at Stripe and A's entry released",
      c == 200 and jB.get("voucher") == {"value": 3000, "discount": price1, "pay": 0} and sA in H.Fake.expires[n_exp:]
      and H.Fake.sessions[sA]["status"] == "expired" and states(c9) == ["released", "reserved"]
      and (V.view(c9)[0].get("session") == sA), (jB, states(c9), H.Fake.sessions[sA]["status"]))
cs, js = get(f"/api/order?o={oA}&k={kA}&s={sA}")
check("A comes back to its old payment page: Stripe holds it expired (it cannot be paid there), and A's order is not paid",
      not pay.session_paid(H.Fake.sessions[sA]) and not os.path.exists(os.path.join(STORE, "orders", oA, "paid.json")) and js.get("state") != "ready", (cs, js.get("state")))
c, jA2 = co(oA, kA, lang="lt", market="lt", voucher=code9)
check("A checks out again: now A's page is the latest; B's open page is expired and released in its turn, A gets the whole balance",
      c == 200 and jA2.get("voucher", {}).get("discount") == price1 and H.Fake.sessions[sid_of(oB)]["status"] == "expired" and states(c9) == ["released", "released", "reserved"],
      (jA2, states(c9)))
webhook(complete(sid_of(oA)))
check("A pays: its entry is paid; what is left is 30.00 less the artwork", states(c9)[-1] == "paid" and get(f"/api/checkout?voucher={code9}&m=lt")[1].get("value") == 3000 - price1)
# a PAID session is never expired nor released
s9p, code9p = buy_value(6000, "lt", "lt", "paid@example.com")
c9p = V.coupon_id(code9p)
oC, kC = draft(lang="lt")
co(oC, kC, lang="lt", market="lt", voucher=code9p)
sC = sid_of(oC)
complete(sC)                                       # paid at Stripe; its webhook has not arrived yet
oD, kD = draft(lang="lt")
c, jD = co(oD, kD, lang="lt", market="lt", voucher=code9p)
check("order C has PAID its page but the webhook has not come yet; order D checks out: C's session is not expired (Stripe refuses, it is complete), C's entry is marked "
      "PAID and never released, and D gets only what is left (60.00 less the artwork)",
      c == 200 and H.Fake.sessions[sC]["status"] == "complete" and states(c9p) == ["paid", "reserved"] and jD.get("voucher") == {"value": 6000 - price1, "discount": price1, "pay": 0},
      (jD, states(c9p)))
cwc, jwc = webhook(H.Fake.sessions[sC])
check("C's webhook then records C as paid with its voucher; the ledger is unchanged", cwc == 200 and (rj(f"orders/{oC}/paid.json") or {}).get("paid") is True
      and states(c9p) == ["paid", "reserved"], (cwc, jwc))
# completed and still settling: never released; a checkout in flight (no session yet): untouched
s9s, code9s = buy_value(6000, "lt", "lt", "settling@example.com")
c9s = V.coupon_id(code9s)
oE, kE = draft(lang="lt")
co(oE, kE, lang="lt", market="lt", voucher=code9s)
H.Fake.sessions[sid_of(oE)].update(status="complete", payment_status="unpaid")   # a bank payment that settles later
g9s = V.lookup(code9s, "lt")
flight = V.spend(g9s, "261125-inflightaaaaaaaaaa", "artwork", 1000, int(time.time()) + 3600, "lt")    # reserved, its session not made yet (no bind)
oF, kF = draft(lang="lt")
c, jF = co(oF, kF, lang="lt", market="lt", voucher=code9s)
check("a page completed with a method that settles later stays reserved (not expired, not released), and so does a checkout in flight that has no session yet; "
      "the next checkout gets what is left after both",
      c == 200 and states(c9s) == ["reserved", "reserved", "reserved"] and jF.get("voucher") == {"value": 6000 - price1 - 1000, "discount": price1, "pay": 0},
      (jF, states(c9s)))
# the minimum charge
s9m, code9m = buy_value(3000, "lt", "lt", "min@example.com")
gm = V.lookup(code9m, "lt")
sp_m = V.spend(gm, "261125-minchargeaaaaaaaa", "artwork", 3020, int(time.time()) + 3600, "lt")
check("a remainder under Stripe's minimum charge is never left: a 30.00 voucher on a 30.20 total pays 29.70 and leaves 0.50 to pay (and 0.30 on the voucher); "
      "a total the voucher covers is paid in full; 0.50 or more is left as it is",
      V.MIN_CHARGE == 50 and sp_m["value"] == 2970 and V.pays(3000, 3000) == 3000 and V.pays(3049, 3000) == 2999 and V.pays(3050, 3000) == 3000
      and V.pays(2000, 3000) == 2000 and V.pays(3001, 3000) == 2951 and get(f"/api/checkout?voucher={code9m}&m=lt")[1].get("value") == 3000 - 2970, sp_m)
check("Stripe's note above the pay button when a voucher is bought says only that the code comes by e-mail: nothing about withdrawal, in every language",
      all("14" not in v and len(v) < 75 for v in V.SUBMIT.values()) and V.SUBMIT["lt"] == "Kupono kodą gausite el. paštu iškart po apmokėjimo." and set(V.SUBMIT) == set(V.MAIL),
      V.SUBMIT)
print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed")
sys.exit(0 if all(RESULTS) else 1)
