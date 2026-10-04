# -*- coding: utf-8 -*-
"""Payments backend tests without real keys: fake Stripe + Resend stub, real signature checks with a synthetic whsec,
local store folder, master_eye / master_compose stubbed (the real render is real_run.py).
    python test_pay.py        prints PASS/FAIL per check and exits 1 on any failure"""
import os, sys, io, json, time, base64, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H

STORE = os.path.join(HERE, "store_unit")
stub = H.start_stub()
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:400]}"), flush=True)


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path):
    r = requests.get(BASE + path, timeout=60)
    return r.status_code, r.json()


def hook(body, sig):
    h = {"Content-Type": "application/json; charset=utf-8"}
    if sig is not None:
        h["Stripe-Signature"] = sig
    r = requests.post(BASE + "/api/stripe_webhook", data=body, headers=h, timeout=60)
    return r.status_code, r.json()


def local(path):
    return os.path.join(STORE, *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


WORK = L.mint_ticket("work")
CROP = H.jpeg_b64(512, 1)
PREV = H.jpeg_b64(1024, 2)
PREV_PNG = H.jpeg_b64(300, 3, fmt="PNG")


_AUTO = object()


def draft(eye, order=None, k=None, crop=CROP, preview=PREV, ticket=_AUTO, **kw):
    if ticket is _AUTO:
        # a new order needs a ticket no other order was made with (one work ticket, one order)
        ticket = H.fresh_ticket() if order is None and k is None else WORK
    b = {"action": "draft", "eye": eye, "crop": crop, "preview": preview, "pad": 1.12, "ticket": ticket, "lang": "de",
         "ref": f"eye-{eye}"}
    if order is not None:
        b["order"] = order
    if k is not None:
        b["k"] = k
    b.update(kw)
    return post("/api/order", b)


def checkout(order, k, eyes, style="deep_nebula", **kw):
    b = {"order": order, "k": k, "eyes": eyes, "style": style, "names": "Jūratė & Tomas", "title": "", "lang": "de",
         "consent_digital": True}
    b.update(kw)
    return post("/api/checkout", b)


# ------------------------------------------------------------------ health and info
c, j = get("/api/health")
check("health reports stripe/email booleans", c == 200 and j.get("stripe") is True and j.get("email") is True
      and j.get("stripe_live") is False, j)
check("health: ordering open, test orders allowed (local run)", j.get("ordering") is True and j.get("test_orders") is True, j)
check("health carries no key text", H.SK not in json.dumps(j) and "sk_" not in json.dumps(j) and "whsec" not in json.dumps(j), j)
c, j = get("/api/checkout")
check("checkout GET: open, prices, consent texts", c == 200 and j.get("open") is True and j["prices"]["two_eyes"] == 3997
      and j["consent"]["version"] == pay.CONSENT_VERSION and "Widerrufsrecht" in j["consent"]["de"], j)

# ------------------------------------------------------------------ drafts
c, j = draft(1, ticket=None)
check("draft without work ticket -> 403", c == 403, (c, j))
c, j = draft(1, ticket="work.1.deadbeef")
check("draft with forged ticket -> 403", c == 403, (c, j))
c, j = draft(1)
check("draft creates order", c == 200 and j.get("created") is True and store.ORDER_RE.fullmatch(j.get("order") or "")
      and pay.KEY_RE.fullmatch(j.get("k") or ""), (c, j))
O1, K1 = j["order"], j["k"]
check("access key is the HMAC of the order id", K1 == pay.access_key(O1))
rec = read_json(f"orders/{O1}/order.json")
check("order.json keeps only the key fingerprint", rec.get("key_sha") == pay.key_sha(K1) and K1 not in json.dumps(rec), rec)
check("expires_at = created + 24 h", j["expires_at"] == rec["created_at"] + 86400, (j, rec))
c, j = draft(2, O1, K1, preview=PREV_PNG)
check("second eye (PNG preview) added", c == 200 and j.get("created") is False and j["order"] == O1, (c, j))
d2 = read_json(f"orders/{O1}/draft/eye_2.json")
check("draft record points at the files, with sha256", d2["preview"]["type"] == "image/png"
      and os.path.isfile(local(d2["crop"]["path"])) and d2["crop"]["sha256"] == hashlib.sha256(base64.b64decode(CROP)).hexdigest(), d2)
c, j = draft(2, O1, K1, crop=H.jpeg_b64(512, 9))
d2b = read_json(f"orders/{O1}/draft/eye_2.json")
check("re-upload replaces the slot and removes the old files", c == 200 and d2b["crop"]["path"] != d2["crop"]["path"]
      and not os.path.exists(local(d2["crop"]["path"])) and not os.path.exists(local(d2["preview"]["path"])), (c, j))
c, j = draft(3, O1, "0" * 32)
check("draft with wrong access key -> 403 bad_link", c == 403 and j.get("reason") == "bad_link", (c, j))
c, j = draft(3, O1, None)
check("draft with order but no key -> 403", c == 403, (c, j))
c, j = draft(9, O1, K1)
check("eye 9 -> 400", c == 400, (c, j))
c, j = draft(0, O1, K1)
check("eye 0 -> 400", c == 400, (c, j))
c, j = draft(3, O1, K1, crop="A" * 3_000_004)
check("oversized crop -> 413 too_large", c == 413 and j.get("reason") == "too_large", (c, j))
c, j = draft(3, O1, K1, preview="A" * 1_600_004)
check("oversized preview -> 413 too_large", c == 413 and j.get("reason") == "too_large", (c, j))
c, j = draft(3, O1, K1, crop=H.jpeg_b64(w=300, h=200))
check("non-square crop -> 400", c == 400, (c, j))
from PIL import Image as _I
_b = io.BytesIO(); _I.new("RGB", (3000, 3000), (90, 60, 40)).save(_b, "JPEG", quality=80)
c, j = draft(3, O1, K1, crop=base64.b64encode(_b.getvalue()).decode())
check("crop over 2048 px -> 400", c == 400, (c, j))
c, j = draft(3, O1, K1, crop=base64.b64encode(b"not an image at all").decode())
check("not an image -> 400", c == 400, (c, j))
c, j = draft(3, O1, K1, crop="@@@not base64@@@")
check("not base64 -> 400", c == 400, (c, j))
c, j = draft(3, O1, K1, crop=H.jpeg_b64(256, 5, fmt="GIF"))
check("GIF -> 400", c == 400, (c, j))
jpg = base64.b64decode(H.jpeg_b64(512, 6))
c, j = draft(3, O1, K1, crop=base64.b64encode(jpg[: len(jpg) // 2]).decode())
check("truncated JPEG -> 400", c == 400, (c, j))
r = requests.post(BASE + "/api/order", data=json.dumps({"action": "status", "order": O1, "k": K1}),
                  headers={"Content-Type": "text/plain"}, timeout=30)
check("POST without JSON content type -> 415", r.status_code == 415, r.status_code)
r = requests.post(BASE + "/api/order", data=json.dumps({"action": "status", "order": O1, "k": K1}),
                  headers={"Content-Type": "application/json", "Origin": "https://evil.example"}, timeout=30)
check("POST from a foreign origin -> 403", r.status_code == 403, r.status_code)
c, j = post("/api/order", {"action": "nope"})
check("unknown action -> 400", c == 400, (c, j))

# ------------------------------------------------------------------ status (unpaid)
c, j = get(f"/api/order?o={O1}&k={K1}")
check("GET status unpaid, eyes 1 and 2 uploaded", c == 200 and j["state"] == "unpaid" and [e["eye"] for e in j["eyes"]] == [1, 2]
      and j["eyes"][0]["ref"] == "eye-1", (c, j))
c, j = get(f"/api/order?o={O1}&k={'f' * 32}")
check("GET status wrong key -> 403", c == 403 and j.get("reason") == "bad_link", (c, j))
c, j = get(f"/api/order?o={O1}")
check("GET status missing key -> 403", c == 403, (c, j))
c, j = get(f"/api/order?o=zzzz-not-an-order&k={K1}")
check("GET status unknown order -> 403 (same answer)", c == 403 and j.get("reason") == "bad_link", (c, j))

# ------------------------------------------------------------------ checkout
c, j = checkout(O1, K1, 2, consent_digital=None)
check("checkout without consent -> 400 consent_required", c == 400 and j.get("reason") == "consent_required", (c, j))
c, j = checkout(O1, K1, 2, consent_digital="true")
check("checkout with consent 'true' (string) -> 400", c == 400 and j.get("reason") == "consent_required", (c, j))
c, j = checkout(O1, K1, 3)
check("checkout for 3 eyes with 2 uploaded -> 409 eyes_missing [3]", c == 409 and j.get("missing") == [3], (c, j))
c, j = checkout(O1, K1, 9)
check("checkout 9 eyes -> 400", c == 400, (c, j))
c, j = checkout(O1, K1, 2, style="gold_leaf")
check("checkout unknown style -> 400", c == 400, (c, j))
c, j = checkout(O1, K1, 2, layout="galaxy")
check("checkout layout not for 2 eyes -> 400", c == 400, (c, j))
c, j = checkout(O1, "1" * 32, 2)
check("checkout wrong key -> 403", c == 403, (c, j))
n_before = len(H.Fake.creates)
c, j = checkout(O1, K1, 2, amount=1, price=1, unit_amount=1, total=1, currency="usd")
check("checkout ok (tampered price fields ignored)", c == 200 and j.get("amount") == 3997 and j["url"].startswith("https://"), (c, j))
p, hd = H.Fake.creates[-1]
check("Stripe got 3997 EUR, one line item, quantity 1", p["line_items[0][price_data][unit_amount]"] == "3997"
      and p["line_items[0][price_data][currency]"] == "eur" and p["line_items[0][quantity]"] == "1"
      and not any(k.startswith("line_items[1]") for k in p), p)
check("Stripe params: payment mode, de locale, no payment_method_types, no tax", p["mode"] == "payment" and p["locale"] == "de"
      and not any(k.startswith("payment_method_types") or k.startswith("automatic_tax") for k in p), p)
check("success_url carries o, k and {CHECKOUT_SESSION_ID}", p["success_url"] ==
      f"https://snapeyes.com/order?o={O1}&k={K1}&lang=de&s={{CHECKOUT_SESSION_ID}}", p["success_url"])
check("cancel_url goes back to /try, without the access key", p["cancel_url"] == f"https://snapeyes.com/try?checkout=cancelled&o={O1}&lang=de"
      and K1 not in p["cancel_url"], p["cancel_url"])
check("metadata: order, key fingerprint (not the key), spec, consent", p["metadata[order]"] == O1 and
      p["metadata[key_sha]"] == pay.key_sha(K1) and K1 not in json.dumps({k: v for k, v in p.items() if k.startswith("metadata")})
      and p["metadata[eyes]"] == "2" and p["metadata[names]"] == "Jūratė & Tomas" and p["metadata[consent_version]"] == pay.CONSENT_VERSION
      and "metadata[title]" not in p, p)
check("item name says 2 eyes, digital file", "2 Augen" in p["line_items[0][price_data][product_data][name]"]
      and "digitale Datei" in p["line_items[0][price_data][product_data][name]"], p)
check("Stripe-Version pinned and Idempotency-Key sent", hd.get("Stripe-Version") == pay.STRIPE_VERSION and hd.get("Idempotency-Key"), hd)
rec = read_json(f"orders/{O1}/order.json")
check("expires_at sent to Stripe = order created + 24 h, kept under Stripe's 24 h", rec["created_at"] + 86400 - 130
      <= int(p["expires_at"]) <= rec["created_at"] + 86400 and int(p["expires_at"]) < time.time() + 86400, (p["expires_at"], rec))
check("order.json records the checkout and consent", rec["checkout"]["session_id"] == j["url"].rsplit("/", 1)[1]
      and rec["checkout"]["consent"]["version"] == pay.CONSENT_VERSION and rec["checkout"]["amount"] == 3997, rec)
SID1 = rec["checkout"]["session_id"]

# every price
prices = {}
c, j = draft(1)                      # a fresh order for the 1-eye prices
O2, K2 = j["order"], j["k"]
for st in ("studio_black", "celestial_gold"):
    c, j = checkout(O2, K2, 1, style=st)
    prices[(1, st)] = j.get("amount")
c, j = draft(3, O1, K1)
for i in (4, 5, 6, 7, 8):
    draft(i, O1, K1)
for n in (3, 5, 8):
    c, j = checkout(O1, K1, n, style="studio_black")
    prices[(n, "studio_black")] = j.get("amount")
check("prices: 1997 / 2497 / 5497 (3) / 8497 (5) / 12997 (8)", prices == {(1, "studio_black"): 1997, (1, "celestial_gold"): 2497,
      (3, "studio_black"): 5497, (5, "studio_black"): 8497, (8, "studio_black"): 12997}, prices)
check("pay.price_cents 2 eyes any style = 3997", pay.price_cents(2, "studio_black") == 3997 == pay.price_cents(2, "supernova"))

# Stripe failures
H.Fake.fail_create[:] = [500, 500]
c, j = checkout(O2, K2, 1, style="studio_black")
check("Stripe 500 twice -> 503 payments_busy (retried once with the same idempotency key)", c == 503 and j.get("reason") == "payments_busy"
      and H.Fake.creates[-1][1].get("Idempotency-Key") == H.Fake.creates[-2][1].get("Idempotency-Key"), (c, j))
H.Fake.fail_create[:] = [400]
c, j = checkout(O2, K2, 1, style="studio_black")
check("Stripe 400 -> 502 payments_error, not retryable", c == 502 and j.get("reason") == "payments_error" and j.get("retry") is False, (c, j))
os.environ["STRIPE_SECRET_KEY"] = "sk_test_WrongKey0123456789"
c, j = checkout(O2, K2, 1, style="studio_black")
check("Stripe 401 (key rejected) -> 503 payments_not_configured", c == 503 and j.get("reason") == "payments_not_configured", (c, j))
os.environ["STRIPE_SECRET_KEY"] = H.SK
os.environ.pop("STRIPE_WEBHOOK_SECRET")
c, j = checkout(O2, K2, 1, style="studio_black")
c2, j2 = get("/api/health")
check("no webhook secret -> checkout 503 payments_not_configured, health stripe false", c == 503
      and j.get("reason") == "payments_not_configured" and j2.get("stripe") is False, (c, j, j2))
body, sig = H.signed_event({"object": "checkout.session"})
c, j = hook(body, sig)
check("webhook without a configured secret -> 503", c == 503, (c, j))
os.environ["STRIPE_WEBHOOK_SECRET"] = H.WHSEC

# ------------------------------------------------------------------ not paid yet
c, j = post("/api/order", {"action": "make", "order": O1, "k": K1, "eye": 1})
check("make before payment -> 402 not_paid", c == 402 and j.get("reason") == "not_paid", (c, j))
c, j = post("/api/order", {"action": "compose", "order": O1, "k": K1})
check("compose before payment -> 402 not_paid", c == 402 and j.get("reason") == "not_paid", (c, j))

# ------------------------------------------------------------------ webhook signatures
# pay the 2-eye session SID1 (the order record's latest session is now the 8-eye one)
sess = H.pay_session(SID1)
body, sig = H.signed_event(sess)
c, j = hook(body, None)
check("webhook without signature -> 400", c == 400, (c, j))
c, j = hook(body, sig.replace("v1=", "v1=0"))
check("webhook malformed signature -> 400", c == 400, (c, j))
c, j = hook(body.replace(b'"paid"', b'"PAID"', 1), sig)
check("webhook tampered body -> 400", c == 400, (c, j))
b_old, s_old = H.signed_event(sess, t=int(time.time()) - 400)
c, j = hook(b_old, s_old)
check("webhook older than 5 min -> 400", c == 400, (c, j))
b_new, s_new = H.signed_event(sess, t=int(time.time()) + 400)
c, j = hook(b_new, s_new)
check("webhook 400 s in the future -> 400", c == 400, (c, j))
b_w, s_w = H.signed_event(sess, secret="whsec_" + "b3RoZXItc2VjcmV0LW5vdC1vdXJz")
c, j = hook(b_w, s_w)
check("webhook signed with another secret -> 400", c == 400, (c, j))
check("nothing marked paid by refused events", not os.path.exists(local(f"orders/{O1}/paid.json")))
r = requests.post(BASE + "/api/stripe_webhook", data=b"x" * (600 << 10), headers={"Stripe-Signature": sig}, timeout=30)
check("webhook body over 512 kB -> 413", r.status_code == 413, r.status_code)
bi, si = H.signed_event({"object": "payment_intent", "id": "pi_1"}, typ="payment_intent.succeeded")
c, j = hook(bi, si)
check("other event types -> 200 ignored", c == 200 and j.get("ignored") == "payment_intent.succeeded", (c, j))
unpaid = dict(sess, payment_status="unpaid")
bu, su = H.signed_event(unpaid)
c, j = hook(bu, su)
check("completed but unpaid (delayed method) -> 200 awaiting_payment, not paid",
      c == 200 and j.get("state") == "awaiting_payment" and not os.path.exists(local(f"orders/{O1}/paid.json")), (c, j))
forged = dict(sess, metadata=dict(sess["metadata"], key_sha="0" * 32))
bf, sf = H.signed_event(forged)
c, j = hook(bf, sf)
check("session whose key fingerprint does not match -> ignored", c == 200 and j.get("ignored") == "session does not match"
      and not os.path.exists(local(f"orders/{O1}/paid.json")), (c, j))
ghost = dict(sess, metadata=dict(sess["metadata"], order="260101-00000000deadbeef"))
bg, sg = H.signed_event(ghost)
c, j = hook(bg, sg)
check("paid session for an unknown order -> 200 ignored", c == 200 and j.get("ignored") == "unknown order", (c, j))

mails_before = len(H.Fake.emails)
c, j = hook(body, sig)
check("valid webhook -> 200, order paid, new", c == 200 and j.get("new") is True and j.get("mail") == "sent", (c, j))
paid = read_json(f"orders/{O1}/paid.json")
check("paid.json: spec from the PAID session (2 eyes), email, amount", paid["spec"]["eyes"] == 2 and paid["amount_total"] == 3997
      and paid["email"] == "kunde@example.com" and paid["source"] == "webhook" and "amount_mismatch" not in paid, paid)
sent = H.Fake.emails[mails_before:]
deliv = [m for m, idem in sent if m["to"] == ["kunde@example.com"]]
notes = [m for m, idem in sent if m["to"] == ["info@snapeyes.com"]]
check("one delivery email (DE) with the order link, one owner note", len(deliv) == 1 and len(notes) == 1
      and deliv[0]["subject"] == f"Ihre SnapEyes-Bestellung {O1}: Bestellbestätigung" and f"/order?o={O1}&k={K1}&lang=de" in deliv[0]["text"]
      and "Widerrufsrecht" in deliv[0]["text"] and deliv[0]["from"] == "SnapEyes <info@snapeyes.com>", sent)
check("emails carry no dash characters and no key", all(chr(0x2013) not in m["text"] and chr(0x2014) not in m["text"]
      and H.SK not in m["text"] for m, _ in sent), sent)
c, j = hook(body, sig)
b2, s2 = H.signed_event(sess)          # Stripe's retry of the same session under a new signature/event id
c2, j2 = hook(b2, s2)
check("replays: 200, nothing new, no second email", c == 200 and j.get("new") is False and c2 == 200 and j2.get("new") is False
      and len(H.Fake.emails) == mails_before + 2 and read_json(f"orders/{O1}/paid.json") == paid, (j, j2, len(H.Fake.emails)))

# ------------------------------------------------------------------ paid order: drafts and checkout closed
c, j = draft(1, O1, K1)
check("draft into a paid order -> 409 order_paid", c == 409 and j.get("reason") == "order_paid", (c, j))
c, j = checkout(O1, K1, 2)
check("checkout of a paid order -> 409 already_paid", c == 409 and j.get("reason") == "already_paid", (c, j))

# ------------------------------------------------------------------ make and compose (stubs for the renderer)
ME, MC = H.MODS["order"].ME, H.MODS["order"].MC
REAL_ME, REAL_MC = ME.master_eye, MC.master_compose
seen = []
mode = {"eye": "ok", "compose_review": False}


def fake_master_eye(body):
    order = body["order"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    key = f"orders/{order}/eye_{body['eye']}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False, "key": key}
    if mode["eye"] == "reject":
        raise store.Answer(502, "render_rejected", "We could not finish this artwork automatically.", False)
    seen.append(body)
    store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
    return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False, "key": key}


def fake_master_compose(body):
    order = body["order"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order)), "unlock ticket"
    for k in body["keys"]:
        assert store.exists(k), k
    key = f"orders/{order}/artwork_fake{len(body['keys'])}.jpg"
    store.put(key, b"artwork", "image/jpeg", upsert=True)
    seen.append(body)
    return {"ok": True, "url": store.signed_url(key, 604800), "key": key, "width": 4096, "height": 2600, "bytes": 7,
            "style": body["style"], "layout": body["layout"], "count": len(body["keys"]), "needs_review": mode["compose_review"]}


ME.master_eye, MC.master_compose = fake_master_eye, fake_master_compose
c, j = post("/api/order", {"action": "make", "order": O1, "k": K1, "eye": 3})
check("make eye 3 of a 2-eye order -> 400", c == 400, (c, j))
c, j = post("/api/order", {"action": "compose", "order": O1, "k": K1})
check("compose before the eyes -> 409 eyes_not_ready [1, 2]", c == 409 and j.get("missing") == [1, 2], (c, j))
c, j = post("/api/order", {"action": "make", "order": O1, "k": "a" * 32, "eye": 1})
check("make with wrong key -> 403", c == 403, (c, j))
c, j = post("/api/order", {"action": "make", "order": O1, "k": K1, "eye": 1})
d1 = read_json(f"orders/{O1}/draft/eye_1.json")
check("make eye 1 -> made, from the stored crop + preview + pad", c == 200 and j.get("made") and not j.get("existing")
      and base64.b64decode(seen[-1]["crop"]) == open(local(d1["crop"]["path"]), "rb").read()
      and base64.b64decode(seen[-1]["preview"]) == open(local(d1["preview"]["path"]), "rb").read() and seen[-1]["pad"] == 1.12, (c, j))
c, j = get(f"/api/order?o={O1}&k={K1}")
check("status making after one eye", c == 200 and j["state"] == "making" and j["eyes"] == [{"eye": 1, "made": True}, {"eye": 2, "made": False}], j)
c, j = post("/api/order", {"action": "make", "order": O1, "k": K1, "eye": 1})
check("make eye 1 again -> existing, not rendered twice", c == 200 and j.get("existing") is True, (c, j))
c, j = post("/api/order", {"action": "make", "order": O1, "k": K1, "eye": 2})
c, j = post("/api/order", {"action": "compose", "order": O1, "k": K1})
cb = seen[-1]
check("compose uses the PAID spec (2 eyes, deep_nebula, names) -> ready + link", c == 200 and j["state"] == "ready"
      and cb["style"] == "deep_nebula" and cb["names"] == "Jūratė & Tomas" and len(cb["keys"]) == 2
      and j["download"]["url"] and "download=SnapEyes-" in j["download"]["download_url"] and j["download"]["expires_in"] == 604800, (c, j))
c, j = get(f"/api/order?o={O1}&k={K1}&p=1")
check("GET status ready: fresh link, preview thumbnails", c == 200 and j["state"] == "ready" and j["download"]["url"]
      and all(e.get("preview_url") for e in j["eyes"]), j)
n_seen = len(seen)
c, j = post("/api/order", {"action": "compose", "order": O1, "k": K1})
check("compose again -> the stored delivery, not composed twice", c == 200 and j["state"] == "ready" and len(seen) == n_seen, (c, j))

# confirmation without the webhook, a double checkout, and a held delivery
c, j = draft(1)
O3, K3 = j["order"], j["k"]
draft(2, O3, K3)
c, j = checkout(O3, K3, 1, style="studio_black")
sid_a = read_json(f"orders/{O3}/order.json")["checkout"]["session_id"]
c, j = checkout(O3, K3, 2, style="studio_black")      # the customer came back and chose 2 eyes
sid_b = read_json(f"orders/{O3}/order.json")["checkout"]["session_id"]
check("a new checkout expires the order's earlier session at Stripe (the old tab can no longer be paid)",
      H.Fake.sessions[sid_a]["status"] == "expired" and H.Fake.sessions[sid_b]["status"] == "open" and sid_a in H.Fake.expires,
      (H.Fake.sessions[sid_a]["status"], H.Fake.sessions[sid_b]["status"]))
c, j = checkout(O3, K3, 1, style="studio_black")      # and back to 1 eye: this is the one they pay
sid_one = read_json(f"orders/{O3}/order.json")["checkout"]["session_id"]
check("... and again for the third one", H.Fake.sessions[sid_b]["status"] == "expired" and H.Fake.sessions[sid_one]["status"] == "open")
c, j = get(f"/api/order?o={O3}&k={K3}&s={sid_b}")
check("the success page of an expired, unpaid session: still unpaid", c == 200 and j["state"] == "unpaid", j)
H.pay_session(sid_one, email="zweite@example.com")
mails_before = len(H.Fake.emails)
c, j = get(f"/api/order?o={O3}&k={K3}&s={sid_one}")
got = H.Fake.emails[mails_before:]
check("order page confirmation sends the delivery email and the owner note (once each)",
      [m["to"] for m, _ in got] == [["zweite@example.com"], ["info@snapeyes.com"]], got)
c2, j2 = get(f"/api/order?o={O3}&k={K3}")
check("asked again without s: paid, no second email", c2 == 200 and j2["state"] == "paid" and len(H.Fake.emails) == mails_before + 2, j2)
p3 = read_json(f"orders/{O3}/paid.json") if os.path.exists(local(f"orders/{O3}/paid.json")) else {}
check("with s from the success page: confirmed with Stripe, paid for 1 eye (what was paid)", c == 200 and j["state"] == "paid"
      and j["count"] == 1 and p3.get("source") == "order_page" and p3["spec"]["eyes"] == 1 and p3["amount_total"] == 1997, (j, p3))
c, j = get(f"/api/order?o={O2}&k={K2}&s={sid_one}")
check("another order's paid session does not pay this one", c == 200 and j["state"] == "unpaid", j)
mails_before = len(H.Fake.emails)
b3, s3 = H.signed_event(H.Fake.sessions[sid_one])
c, j = hook(b3, s3)
check("webhook after the order page: not new, no second email or note", c == 200 and j.get("new") is False
      and j.get("mail") == "done" and len(H.Fake.emails) == mails_before, (c, j, H.Fake.emails[mails_before:]))
mode["compose_review"] = True
post("/api/order", {"action": "make", "order": O3, "k": K3, "eye": 1})
c, j = post("/api/order", {"action": "compose", "order": O3, "k": K3})
check("compose flagged needs_review -> state review, no link", c == 200 and j["state"] == "review" and "download" not in j, (c, j))
import subprocess
env = dict(os.environ)
r = subprocess.run([sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py"), "release", O3], capture_output=True, text=True, env=env)
c, j = get(f"/api/order?o={O3}&k={K3}")
check("order_admin release -> ready with link", r.returncode == 0 and c == 200 and j["state"] == "ready" and j["download"]["url"], (r.stdout, r.stderr, j))
mode["compose_review"] = False

# a refused render holds the order
c, j = draft(1)
O4, K4 = j["order"], j["k"]
checkout(O4, K4, 1, style="supernova")
sid4 = read_json(f"orders/{O4}/order.json")["checkout"]["session_id"]
H.pay_session(sid4)
b4, s4 = H.signed_event(H.Fake.sessions[sid4])
hook(b4, s4)
mode["eye"] = "reject"
c, j = post("/api/order", {"action": "make", "order": O4, "k": K4, "eye": 1})
check("render refused -> 502 render_rejected, retry false", c == 502 and j.get("reason") == "render_rejected" and j.get("retry") is False, (c, j))
c, j = post("/api/order", {"action": "make", "order": O4, "k": K4, "eye": 1})
check("then make -> 409 in_review (no second paid render)", c == 409 and j.get("reason") == "in_review", (c, j))
c, j = get(f"/api/order?o={O4}&k={K4}")
check("status review", c == 200 and j["state"] == "review", j)
mode["eye"] = "ok"
r = subprocess.run([sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py"), "clear-review", O4], capture_output=True, text=True, env=env)
c, j = post("/api/order", {"action": "make", "order": O4, "k": K4, "eye": 1})
check("clear-review lets make run again", r.returncode == 0 and c == 200 and j.get("made"), (r.stdout, r.stderr, c, j))

# email that fails transiently: webhook 503 so Stripe retries, then sent once
c, j = draft(1)
O5, K5 = j["order"], j["k"]
checkout(O5, K5, 1, style="studio_black", lang="en")
sid5 = read_json(f"orders/{O5}/order.json")["checkout"]["session_id"]
H.pay_session(sid5, email="third@example.com")
H.Fake.fail_mail[:] = [503, 503]
b5, s5 = H.signed_event(H.Fake.sessions[sid5])
c, j = hook(b5, s5)
check("delivery email 503 -> webhook 503 (Stripe retries), order already paid", c == 503 and os.path.exists(local(f"orders/{O5}/paid.json"))
      and not os.path.exists(local(f"orders/{O5}/mail_delivery.json")), (c, j))
H.Fake.fail_mail[:] = []
b5, s5 = H.signed_event(H.Fake.sessions[sid5])
c, j = hook(b5, s5)
en = [m for m, _ in H.Fake.emails if m["to"] == ["third@example.com"]]
check("Stripe's retry -> 200, English email sent once", c == 200 and j.get("mail") == "sent" and len(en) == 1
      and en[0]["subject"].startswith("Your SnapEyes order ") and en[0]["subject"].endswith(": order confirmation") and "right of withdrawal" in en[0]["text"], (c, j, en))

# expired drafts
c, j = draft(1)
O6, K6 = j["order"], j["k"]
p6 = local(f"orders/{O6}/order.json")
rec6 = read_json(f"orders/{O6}/order.json")
rec6["created_at"] -= 86400 - 1500          # 25 min left: less than Stripe's 30 min session minimum
open(p6, "w").write(json.dumps(rec6))
c, j = checkout(O6, K6, 1, style="studio_black")
check("checkout with < 32 min of draft left -> 410 draft_expired", c == 410 and j.get("reason") == "draft_expired", (c, j))
rec6["created_at"] -= 3600
open(p6, "w").write(json.dumps(rec6))
c, j = checkout(O6, K6, 1, style="studio_black")
c2, j2 = draft(1, O6, K6)
c3, j3 = get(f"/api/order?o={O6}&k={K6}")
check("expired draft: checkout 410, draft 410, status expired", c == 410 and c2 == 410 and j2.get("reason") == "draft_expired"
      and j3.get("expired") is True, (c, j, c2, j2, j3))

# purge (dry run then real) removes only old unpaid orders
rec6["created_at"] = int(time.time()) - 26 * 3600
open(p6, "w").write(json.dumps(rec6))
r = subprocess.run([sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py"), "purge", "--hours", "25"], capture_output=True, text=True, env=env)
check("purge dry run lists the expired unpaid order only", r.returncode == 0 and O6 in r.stdout and O1 not in r.stdout
      and os.path.exists(p6), (r.stdout, r.stderr))
r = subprocess.run([sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py"), "purge", "--hours", "25", "--yes"], capture_output=True, text=True, env=env)
check("purge --yes deletes it, keeps paid orders", r.returncode == 0 and not os.path.exists(p6)
      and os.path.exists(local(f"orders/{O1}/paid.json")), (r.stdout, r.stderr))

# arrange: remove / reorder eyes without uploading again
c, j = draft(1)
O7, K7 = j["order"], j["k"]
draft(2, O7, K7); draft(3, O7, K7)
d7 = {i: read_json(f"orders/{O7}/draft/eye_{i}.json") for i in (1, 2, 3)}
c, j = post("/api/order", {"action": "arrange", "order": O7, "k": K7, "slots": [3, 1]})
st = get(f"/api/order?o={O7}&k={K7}")[1]
check("arrange [3, 1]: slot 1 = old 3, slot 2 = old 1, slot 3 dropped with its eye-2 files", c == 200
      and [e["ref"] for e in j["eyes"]] == ["eye-3", "eye-1"] and [e["ref"] for e in st["eyes"]] == ["eye-3", "eye-1"]
      and not os.path.exists(local(f"orders/{O7}/draft/eye_3.json")) and not os.path.exists(local(d7[2]["crop"]["path"]))
      and os.path.exists(local(d7[3]["crop"]["path"])) and os.path.exists(local(d7[1]["preview"]["path"])), (c, j, st))
bad_slots = [[], [1, 1], [0], [9], [True], ["1"], None, list(range(1, 10))]
res = [post("/api/order", {"action": "arrange", "order": O7, "k": K7, "slots": b})[0] for b in bad_slots]
check("arrange with bad slots -> 400 each", res == [400] * len(bad_slots), res)
c, j = post("/api/order", {"action": "arrange", "order": O7, "k": K7, "slots": [1, 3]})
check("arrange with a slot that is not uploaded -> 409 eyes_missing", c == 409 and j.get("missing") == [3], (c, j))
c, j = post("/api/order", {"action": "arrange", "order": O7, "k": "e" * 32, "slots": [1]})
check("arrange with wrong key -> 403", c == 403, (c, j))
c, j = post("/api/order", {"action": "arrange", "order": O1, "k": K1, "slots": [2, 1]})
check("arrange a paid order -> 409 order_paid", c == 409 and j.get("reason") == "order_paid", (c, j))
c, j = checkout(O7, K7, 2, style="studio_black")
check("checkout after arrange (2 eyes) -> ok", c == 200 and j.get("amount") == 3997, (c, j))

# erase on request, and the 12-month expiry of paid orders
ADMIN = [sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py")]
r = subprocess.run(ADMIN + ["erase", O1], capture_output=True, text=True, env=env)
check("erase dry run deletes nothing", r.returncode == 0 and os.path.exists(local(f"orders/{O1}/eye_1.jpg")), (r.stdout, r.stderr))
r = subprocess.run(ADMIN + ["erase", O1, "--yes"], capture_output=True, text=True, env=env)
c, j = get(f"/api/order?o={O1}&k={K1}")
c2, j2 = post("/api/order", {"action": "make", "order": O1, "k": K1, "eye": 1})
c3, j3 = post("/api/order", {"action": "compose", "order": O1, "k": K1})
left = sorted(os.listdir(local(f"orders/{O1}")))
check("erase a paid order: state deleted, make/compose 410, only records left", r.returncode == 0 and c == 200
      and j["state"] == "deleted" and "download" not in j and c2 == 410 and j2.get("reason") == "deleted" and c3 == 410
      and all(not f.endswith((".jpg", ".png")) for f in left) and "paid.json" in left and "order.json" in left
      and "deleted.json" in left and ("draft" not in left or not os.listdir(local(f"orders/{O1}/draft"))), (r.stdout, r.stderr, j, left))
r = subprocess.run(ADMIN + ["erase", O2, "--yes"], capture_output=True, text=True, env=env)
c, j = get(f"/api/order?o={O2}&k={K2}")
check("erase an unpaid order: everything gone, link answers 403", r.returncode == 0 and c == 403
      and not any(files for _, _, files in os.walk(local(f"orders/{O2}"))), (r.stdout, r.stderr, c, j))
p3 = read_json(f"orders/{O3}/paid.json")
p3["paid_at"] = int(time.time()) - 400 * 86400
open(local(f"orders/{O3}/paid.json"), "w").write(json.dumps(p3))
r = subprocess.run(ADMIN + ["expire-paid", "--yes"], capture_output=True, text=True, env=env)
c, j = get(f"/api/order?o={O3}&k={K3}")
c4, j4 = get(f"/api/order?o={O4}&k={K4}")
check("expire-paid: the 13-month-old order deleted, a recent one untouched", r.returncode == 0 and j["state"] == "deleted"
      and j4["state"] != "deleted" and O3 in r.stdout and O4 not in r.stdout, (r.stdout, r.stderr, j, j4))

# ------------------------------------------------------------------ helpers
s = pay.scrub(f"key {H.SK} secret {H.WHSEC} resend {H.RESEND} url https://snapeyes.com/order?o={O1}&k={K1} "
              f"sk_live_abcdefghijklmnop whsec_zzzzzzzzzzzzzzzzzz https://x.supabase.co/object/sign/a?token=eyJabc.def")
check("scrub hides keys, secrets, access keys and link tokens", all(x not in s for x in (H.SK, H.WHSEC, H.RESEND, K1, "abcdefghijklmnop",
      "zzzzzzzz", "eyJabc")), s)
now = int(time.time())
payload = b'{"a":1}'
good = pay.verify_signature(payload, f"t={now},v1=" + __import__("hmac").new(H.WHSEC.encode(), f"{now}.".encode() + payload, hashlib.sha256).hexdigest(), [H.WHSEC])
multi = pay.verify_signature(payload, f"t={now},v1={'0' * 64},v1=" + __import__("hmac").new(H.WHSEC.encode(), f"{now}.".encode() + payload, hashlib.sha256).hexdigest(), ["whsec_" + "x" * 20, H.WHSEC])
check("signature: good one, several v1 and rolled secrets", good and multi)
check("signature: garbage headers never raise", not any(pay.verify_signature(payload, h, [H.WHSEC]) for h in
      ("", "t=", "v1=", "t=abc,v1=def", None, "t=1," + "v1=" * 2000, f"t={now}")))
ME.master_eye, MC.master_compose = REAL_ME, REAL_MC

# ------------------------------------------------------------------ source hygiene
bad = []
for f in ("api/_lib/pay.py", "api/order.py", "api/checkout.py", "api/stripe_webhook.py", "api/health.py", "scripts/order_admin.py", "api/_lib/store.py"):
    t = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in t for ch in (chr(0x2013), chr(0x2014))) or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in t):
        bad.append(f)
check("my files: no em/en dashes, no control characters", not bad, bad)

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
api.shutdown()
stub.shutdown()
sys.exit(1 if fails else 0)
