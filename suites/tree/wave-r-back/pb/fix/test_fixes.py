# -*- coding: utf-8 -*-
"""Tests for the review fixes (paybackend): the ordering gate, one order per work ticket, the daily upload ceiling,
test-mode payments on production, the confirmation-email gate, one payable Checkout Session per order, extra
payments, the clean-up that asks Stripe first, and the cron entry. Fake Stripe + Resend (../harness.py), local store
folders, synthetic keys, the renderer stubbed. No network, no real key.
    python test_fixes.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, io, json, time, base64, threading, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
PB = os.path.dirname(HERE)
sys.path.insert(0, PB)
import harness as H

stub = H.start_stub()
STORES = {n: os.path.join(HERE, "store_" + n) for n in ("gate", "ticket", "budget", "mode", "mail", "sess", "purge")}
H.setup_env(STORES["gate"], stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay

RESULTS = []
ADMIN = [sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py")]


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:600]}"), flush=True)


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path, headers=None):
    r = requests.get(BASE + path, headers=headers or {}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def hook(obj, typ="checkout.session.completed"):
    body, sig = H.signed_event(obj, typ)
    r = requests.post(BASE + "/api/stripe_webhook", data=body,
                      headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=60)
    return r.status_code, r.json()


def env(**kw):
    for k, v in kw.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def root():
    return os.environ["STORE_LOCAL_DIR"]


def local(path):
    return os.path.join(root(), *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


def orders_made():
    d = local("orders")
    return sorted(o for o in os.listdir(d) if os.path.isfile(os.path.join(d, o, "order.json"))) if os.path.isdir(d) else []


def stored_bytes():
    """Bytes stored, without the admin panel's usage events (ops/: api/_lib/events.py records every refusal as a
    small event with no personal data since wave q; they are not order data)."""
    tot = 0
    for r, _, fs in os.walk(root()):
        if os.path.relpath(r, root()).replace(os.sep, "/").split("/")[0] == "ops":
            continue
        tot += sum(os.path.getsize(os.path.join(r, f)) for f in fs)
    return tot


SMALL = H.jpeg_b64(256, 1)


def draft(eye, order=None, k=None, ticket=None, crop=SMALL, preview=SMALL):
    b = {"action": "draft", "eye": eye, "crop": crop, "preview": preview, "pad": 1.12, "lang": "en", "ref": f"e{eye}",
         "ticket": ticket or (H.fresh_ticket() if order is None else L.mint_ticket("work"))}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def checkout(order, k, eyes=1, style="studio_black"):
    return post("/api/checkout", {"order": order, "k": k, "eyes": eyes, "style": style, "names": "", "title": "",
                                  "lang": "en", "consent_digital": True})


def sid_of(order):
    return read_json(f"orders/{order}/order.json")["checkout"]["session_id"]


def paid_order(email="kunde@example.com", send_hook=True):
    """A 1-eye order, checked out and paid at the fake Stripe (the webhook sent when send_hook)."""
    c, d = draft(1)
    o, k = d["order"], d["k"]
    c, co = checkout(o, k)
    assert c == 200, (c, co)
    sid = sid_of(o)
    sess = H.pay_session(sid, email)
    res = hook(sess) if send_hook else None
    return o, k, sid, res


def mails_to(addr, since=0):
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [addr]]


# ---------------------------------------------------------------------------------------- renderer stubs
ORDER = H.MODS["order"]
renders = []


def fake_master_eye(body):
    order = body["order"]
    assert L.check_ticket(body["ticket"], kind=store.unlock_kind(order))
    key = f"orders/{order}/eye_{body['eye']}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False}
    renders.append((order, body["eye"]))
    store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
    return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False}


def fake_master_compose(body):
    order = body["order"]
    key = f"orders/{order}/artwork_t.jpg"
    store.put(key, b"artwork", "image/jpeg", upsert=True)
    return {"ok": True, "url": store.signed_url(key, 604800), "key": key, "width": 4096, "height": 4096, "bytes": 7,
            "style": body["style"], "layout": body["layout"], "count": len(body["keys"]), "needs_review": False}


ORDER.ME.master_eye, ORDER.MC.master_compose = fake_master_eye, fake_master_compose


def make(o, k, eye=1):
    return post("/api/order", {"action": "make", "order": o, "k": k, "eye": eye})


# ======================================================================================== A. the ordering gate
env(STRIPE_SECRET_KEY=None, STRIPE_WEBHOOK_SECRET=None, RESEND_API_KEY=None)
c, h = get("/api/health")
c2, ck = get("/api/checkout")
check("A no Stripe: health stripe false, ordering false; checkout GET open false",
      h.get("stripe") is False and h.get("ordering") is False and ck.get("open") is False, (h, ck))
before = stored_bytes()
c, j = draft(1, crop=H.jpeg_b64(1024, 3), preview=H.jpeg_b64(1024, 4))
c2, j2 = post("/api/order", {"action": "arrange", "order": "260929-0123456789abcdef", "k": "a" * 32, "slots": [1]})
check("A no Stripe: draft and arrange -> 503 payments_not_configured, nothing stored",
      c == 503 and j.get("reason") == "payments_not_configured" and c2 == 503 and j2.get("reason") == "payments_not_configured"
      and stored_bytes() == before and not orders_made(), (c, j, c2, j2, stored_bytes()))
c, j = draft(1, ticket="work.1.bad")
check("A no Stripe: even a bad ticket gets the 503 first (nothing about tickets is revealed)", c == 503, (c, j))
H.setup_env(STORES["gate"], stub.server_address[1], fresh=False)
c, j = draft(1)
check("A Stripe set again: draft works", c == 200 and j.get("created") is True, (c, j))

# ======================================================================================== A2. one ticket, one order
H.setup_env(STORES["ticket"], stub.server_address[1])
T = H.fresh_ticket()
c, j = draft(1, ticket=T)
c2, j2 = draft(1, ticket=T)
check("A2 the same ticket again (a lost reply): the same order back, not a new one",
      c == 200 and c2 == 200 and j["created"] is True and j2["created"] is False and j2["order"] == j["order"]
      and j2["k"] == j["k"] and orders_made() == [j["order"]], (j, j2, orders_made()))
O_T, K_T = j["order"], j["k"]
T2 = H.fresh_ticket()
out = []
ths = [threading.Thread(target=lambda: out.append(draft(1, ticket=T2))) for _ in range(6)]
[t.start() for t in ths]
[t.join() for t in ths]
got = {r[1].get("order") for r in out if r[0] == 200}
check("A2 six parallel drafts with one ticket: all answered, ONE order", len(out) == 6 and all(r[0] == 200 for r in out)
      and len(got) == 1 and len(orders_made()) == 2, (out, orders_made()))
tick = [f for _, _, fs in os.walk(local("ticketuse")) for f in fs]
check("A2 the ticket markers are stored (one per ticket)", len(tick) == 2, tick)
c, co = checkout(O_T, K_T)
hook(H.pay_session(sid_of(O_T)))
c, j = draft(1, ticket=T)
c2, j2 = draft(1, ticket=T)
check("A2 once that order is paid, the same photo may start ONE new order (a second artwork is a new purchase)",
      c == 200 and j.get("created") is True and j["order"] != O_T and c2 == 200 and j2.get("created") is False
      and j2["order"] == j["order"] and len(orders_made()) == 3, (c, j, c2, j2, orders_made()))
O_T3, K_T3 = j["order"], j["k"]
p3 = local(f"orders/{O_T3}/order.json")
r3 = json.load(open(p3, encoding="utf-8"))
r3["created_at"] -= 86400 + 60
open(p3, "w", encoding="utf-8").write(json.dumps(r3))
c, j = draft(1, ticket=T)
check("A2 ... and when that one expired unpaid: 403 (the page asks for the photo again), no new order",
      c == 403 and not j.get("reason") and len(orders_made()) == 3, (c, j))
c, j = draft(2, O_T, K_T)
check("A2 a paid order takes no eye either (409 order_paid)", c == 409 and j.get("reason") == "order_paid", (c, j))


# ======================================================================================== A3. the daily ceiling
def noise_jpeg_b64(max_chars, quality=95, seed=7):
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    side = 1400
    while side >= 64:
        a = rng.integers(0, 255, size=(side, side, 3), dtype=np.uint8)
        buf = io.BytesIO()
        Image.fromarray(a).save(buf, "JPEG", quality=quality)
        s = base64.b64encode(buf.getvalue()).decode()
        if len(s) <= max_chars:
            return s
        side -= 24
    raise SystemExit("no size fits")


H.setup_env(STORES["budget"], stub.server_address[1])
env(SNAPEYES_DRAFT_DAY_MB="10")
BIG_C = noise_jpeg_b64(2_690_000)
BIG_P = noise_jpeg_b64(min(1_590_000, 4_290_000 - len(BIG_C)), seed=8)
n0 = len(H.Fake.emails)
codes = []
for i in range(6):
    c, j = draft(1, crop=BIG_C, preview=BIG_P)
    codes.append((c, j.get("reason")))
refused = [x for x in codes if x[0] == 503]
check("A3 10 MB a day: three 3.15 MB uploads pass, then 503 uploads_paused (retry later)",
      [x[0] for x in codes[:3]] == [200] * 3 and refused and all(r == "uploads_paused" for _, r in refused)
      and len(orders_made()) == 3, (codes, orders_made()))
check("A3 stored stays under the ceiling", stored_bytes() < 10.5 * (1 << 20), stored_bytes())
notes = [m for m in mails_to("info@snapeyes.com", n0) if "uploads paused" in m["subject"]]
check("A3 the owner is told once", len(notes) == 1, [m["subject"] for m in mails_to("info@snapeyes.com", n0)])
env(SNAPEYES_DRAFT_DAY_MB=None)
c, j = draft(1)
check("A3 back at the default ceiling: small uploads pass again", c == 200, (c, j))
oa, ka = j["order"], j["k"]
keep_max, pay.DRAFT_ORDER_MAX = pay.DRAFT_ORDER_MAX, 4
res = [draft(1, oa, ka)[0] for _ in range(4)]
c, j2 = draft(1)
pay.DRAFT_ORDER_MAX = keep_max
check("A3 one order retaking an eye over and over: capped per day (429 too_many_uploads); other orders unaffected",
      res == [200, 200, 200, 429] and c == 200, (res, c, j2))

# ======================================================================================== B. test payments
H.setup_env(STORES["mode"], stub.server_address[1])
O_B, K_B, SID_B, res = paid_order()                                    # paid in test mode while test orders counted
c, d = draft(1)
O_B2, K_B2 = d["order"], d["k"]
checkout(O_B2, K_B2)
SID_B2 = sid_of(O_B2)
env(VERCEL_ENV="production")
c, h = get("/api/health")
c2, ck = get("/api/checkout")
check("B test key on production: health ordering false, test_orders false; checkout GET open false",
      h.get("ordering") is False and h.get("test_orders") is False and h.get("stripe") is True and ck.get("open") is False,
      (h, ck))
c, j = checkout(O_B2, K_B2)
c2, j2 = draft(1)
check("B test key on production: checkout and draft -> 503 payments_not_configured",
      c == 503 and j.get("reason") == "payments_not_configured" and c2 == 503, (c, j, c2, j2))
n_r = len(renders)
c, j = make(O_B, K_B)
c2, j2 = post("/api/order", {"action": "compose", "order": O_B, "k": K_B})
c3, j3 = get(f"/api/order?o={O_B}&k={K_B}")
check("B an order paid in TEST mode: make and compose 402 test_payment, status unpaid (test_mode), nothing rendered",
      c == 402 and j.get("reason") == "test_payment" and c2 == 402 and j2.get("reason") == "test_payment"
      and j3.get("state") == "unpaid" and j3.get("payment_check") == "test_mode" and len(renders) == n_r, (j, j2, j3))
n0 = len(H.Fake.emails)
c, j = hook(H.pay_session(SID_B2))
check("B a test-mode webhook on production: 200 ignored, not marked paid, no email",
      c == 200 and j.get("ignored") == "test mode" and not os.path.exists(local(f"orders/{O_B2}/paid.json"))
      and len(H.Fake.emails) == n0, (c, j))
c, j = get(f"/api/order?o={O_B2}&k={K_B2}&s={SID_B2}")
check("B ... nor by the success page (Stripe asked, test session not counted)",
      j.get("state") == "unpaid" and not os.path.exists(local(f"orders/{O_B2}/paid.json")) and len(H.Fake.emails) == n0, j)
env(VERCEL_ENV="preview")
c, h = get("/api/health")
check("B a preview without SNAPEYES_ALLOW_TEST_ORDERS: closed too", h.get("ordering") is False, h)
env(SNAPEYES_ALLOW_TEST_ORDERS="1")
c, h = get("/api/health")
c2, j2 = make(O_B, K_B)
check("B a preview WITH SNAPEYES_ALLOW_TEST_ORDERS=1: open, the test order is made", h.get("ordering") is True
      and h.get("test_orders") is True and c2 == 200 and j2.get("made"), (h, c2, j2))
env(VERCEL_ENV="production")
c, h = get("/api/health")
check("B the switch is ignored on production", h.get("ordering") is False and h.get("test_orders") is False, h)
env(VERCEL_ENV=None, SNAPEYES_ALLOW_TEST_ORDERS=None, STRIPE_SECRET_KEY="sk_live_" + "Fake0123456789abcdefGHIJ",
    RESEND_API_KEY=None)
c, ck = get("/api/checkout")
check("B a LIVE key without the confirmation email: ordering closed", ck.get("open") is False
      and "RESEND_API_KEY" in pay.ordering_problem(), (ck, pay.ordering_problem()))
H.setup_env(STORES["mode"], stub.server_address[1], fresh=False)
keep_dir = os.environ.pop("STORE_LOCAL_DIR")
no_switch = pay.test_orders_allowed()
env(SNAPEYES_ALLOW_TEST_ORDERS="1")
with_switch = pay.test_orders_allowed()
env(SNAPEYES_ALLOW_TEST_ORDERS=None, STORE_LOCAL_DIR=keep_dir)
check("B a local run on the REAL bucket (no STORE_LOCAL_DIR): test orders only with the switch",
      no_switch is False and with_switch is True and pay.test_orders_allowed() is True, (no_switch, with_switch))

# ======================================================================================== M. confirmation first
H.setup_env(STORES["mail"], stub.server_address[1])
# M1: Resend refuses the confirmation (422, e.g. the domain is not verified)
n0 = len(H.Fake.emails)
c, d = draft(1)
o1, k1 = d["order"], d["k"]
checkout(o1, k1)
H.Fake.fail_mail[:] = [422]
c, j = hook(H.pay_session(sid_of(o1), "m1@example.com"))
rv = read_json(f"orders/{o1}/review.json") if os.path.exists(local(f"orders/{o1}/review.json")) else {}
held = [m for m in mails_to("info@snapeyes.com", n0) if "confirmation email did not go out" in m["subject"]]
check("M1 Resend refuses: webhook 200 mail failed, order HELD (review.json), owner told how to go on",
      c == 200 and j.get("mail") == "failed" and str(rv.get("reason", "")).startswith("confirmation_email")
      and len(held) == 1 and "resend-mail" in held[0]["text"], (c, j, rv, [m["subject"] for m in mails_to("info@snapeyes.com", n0)]))
n_r = len(renders)
c, j = make(o1, k1)
c2, j2 = get(f"/api/order?o={o1}&k={k1}")
check("M1 held: make 409 in_review, status review, NOTHING rendered", c == 409 and j.get("reason") == "in_review"
      and j2.get("state") == "review" and len(renders) == n_r, (c, j, j2))
r = subprocess.run(ADMIN + ["resend-mail", o1], capture_output=True, text=True, env=dict(os.environ))
c, j = get(f"/api/order?o={o1}&k={k1}")
c2, j2 = make(o1, k1)
check("M1 owner: resend-mail sends it and lifts the hold; then paid and made",
      r.returncode == 0 and "sent" in r.stdout and len(mails_to("m1@example.com", n0)) == 1 and j.get("state") == "paid"
      and c2 == 200 and j2.get("made"), (r.stdout, r.stderr, j, c2, j2))

# M2: a temporary Resend failure: nothing is made until the status call got it out
n0 = len(H.Fake.emails)
c, d = draft(1)
o2, k2 = d["order"], d["k"]
checkout(o2, k2)
sess2 = H.pay_session(sid_of(o2), "m2@example.com")
H.Fake.fail_mail[:] = [503, 503]
c, j = hook(sess2)
check("M2 Resend 503: webhook 503 (Stripe retries), paid, no confirmation yet", c == 503
      and os.path.exists(local(f"orders/{o2}/paid.json")) and not os.path.exists(local(f"orders/{o2}/mail_delivery.json")), (c, j))
n_r = len(renders)
c, j = make(o2, k2)
check("M2 make before the confirmation: 402 confirming (retry), nothing rendered",
      c == 402 and j.get("reason") == "confirming" and j.get("retry") is True and len(renders) == n_r, (c, j))
H.Fake.fail_mail[:] = [503]
c, j = get(f"/api/order?o={o2}&k={k2}")
check("M2 status while it still fails: pending, waiting_for confirmation_email", j.get("state") == "pending"
      and j.get("waiting_for") == "confirmation_email" and not mails_to("m2@example.com", n0), j)
c, j = get(f"/api/order?o={o2}&k={k2}")
c2, j2 = make(o2, k2)
check("M2 the next status call sends it: paid; then make renders", j.get("state") == "paid"
      and len(mails_to("m2@example.com", n0)) == 1 and c2 == 200 and j2.get("made"), (j, c2, j2))
c, j = hook(sess2)
check("M2 Stripe's retry: 200, no second email", c == 200 and j.get("mail") == "done"
      and len(mails_to("m2@example.com", n0)) == 1, (c, j))

# M3: sent by hand
c, d = draft(1)
o3, k3 = d["order"], d["k"]
checkout(o3, k3)
H.Fake.fail_mail[:] = [422]
hook(H.pay_session(sid_of(o3), "m3@example.com"))
r = subprocess.run(ADMIN + ["mailed-by-hand", o3], capture_output=True, text=True, env=dict(os.environ))
c, j = get(f"/api/order?o={o3}&k={k3}")
check("M3 owner sent it by hand: mailed-by-hand lifts the hold, status paid", r.returncode == 0 and j.get("state") == "paid",
      (r.stdout, r.stderr, j))

# M4: a paid record with no confirmation record at all (the webhook's send still in flight elsewhere)
c, d = draft(1)
o4, k4 = d["order"], d["k"]
checkout(o4, k4)
sess4 = H.pay_session(sid_of(o4), "m4@example.com")
paid4, _ = pay.record_paid(o4, read_json(f"orders/{o4}/order.json"), sess4, "test")
store.put(f"orders/{o4}/mail_delivery.json", store.json_bytes({"state": "sending", "t": time.time(), "id": "x"}),
          "application/json", upsert=True)
c, j = make(o4, k4)
c2, j2 = get(f"/api/order?o={o4}&k={k4}")
check("M4 another call is sending it right now: make 402 confirming, status pending (no double send)",
      c == 402 and j2.get("state") == "pending" and not mails_to("m4@example.com"), (c, j, j2))

# M5: email off: a TEST order is made without it (local tests); a LIVE payment is held
env(RESEND_API_KEY=None)
c, d = draft(1)
o5, k5 = d["order"], d["k"]
checkout(o5, k5)
c, j = hook(H.pay_session(sid_of(o5)))
c2, j2 = make(o5, k5)
check("M5 email off, test order: webhook mail off, made (no confirmation needed without email)",
      j.get("mail") == "off" and c2 == 200, (j, c2, j2))
c, d = draft(1)
o6, k6 = d["order"], d["k"]
checkout(o6, k6)
s6 = H.pay_session(sid_of(o6))
s6["livemode"] = True
c, j = hook(s6)
c2, j2 = get(f"/api/order?o={o6}&k={k6}")
c3, j3 = make(o6, k6)
check("M5 email off, LIVE payment: held (review), make 409", c == 200 and j2.get("state") == "review"
      and c3 == 409, (j, j2, c3, j3))
H.setup_env(STORES["mail"], stub.server_address[1], fresh=False)

# ======================================================================================== C. sessions and payments
H.setup_env(STORES["sess"], stub.server_address[1])
# C1: the old tab was paid before the customer came back: the next checkout records it, makes no new session
c, d = draft(1)
oc, kc = d["order"], d["k"]
draft(2, oc, kc)
checkout(oc, kc, 1)
sid_a = sid_of(oc)
H.pay_session(sid_a, "c1@example.com")
n_create, n0 = len(H.Fake.creates), len(H.Fake.emails)
c, j = checkout(oc, kc, 2)
paid = read_json(f"orders/{oc}/paid.json") if os.path.exists(local(f"orders/{oc}/paid.json")) else {}
check("C1 old tab already paid: checkout 409 already_paid, no new session, the payment recorded + confirmed",
      c == 409 and j.get("reason") == "already_paid" and j.get("order_url") and len(H.Fake.creates) == n_create
      and paid.get("session_id") == sid_a and paid.get("source") == "checkout" and len(mails_to("c1@example.com", n0)) == 1,
      (c, j, paid))
# C2: completed but still settling (a delayed method): no second session
c, d = draft(1)
oc2, kc2 = d["order"], d["k"]
checkout(oc2, kc2, 1)
H.Fake.sessions[sid_of(oc2)].update(status="complete", payment_status="unpaid")
n_create = len(H.Fake.creates)
c, j = checkout(oc2, kc2, 1)
check("C2 old session completed, payment settling: 409 already_paid settling, no new session",
      c == 409 and j.get("settling") is True and len(H.Fake.creates) == n_create, (c, j))
# C3: a second paid session of a paid order (race, two tabs): recorded apart, the owner told to refund
c, d = draft(1)
oc3, kc3 = d["order"], d["k"]
checkout(oc3, kc3, 1)
sid_1 = sid_of(oc3)
hook(H.pay_session(sid_1, "c3@example.com"))
extra = json.loads(json.dumps(H.Fake.sessions[sid_1]))
extra.update(id="cs_test_" + "e" * 24, amount_total=3997, payment_intent="pi_test_extra1")
extra["metadata"] = dict(extra["metadata"], eyes="2", amount="3997", layout="duo")
H.Fake.sessions[extra["id"]] = extra
n0 = len(H.Fake.emails)
c, j = hook(extra)
xs = [f for f in os.listdir(local(f"orders/{oc3}")) if f.startswith("extra_payment_")]
xrec = read_json(f"orders/{oc3}/{xs[0]}") if xs else {}
owner = [m for m in mails_to("info@snapeyes.com", n0)]
check("C3 second paid session: webhook 200 extra_payment, stored with amount, owner told to refund, order unchanged",
      c == 200 and j.get("extra_payment") is True and len(xs) == 1 and xrec.get("amount_total") == 3997
      and xrec.get("paid") is False and len(owner) == 1 and "refund" in owner[0]["subject"] and "39.97" in owner[0]["subject"]
      and read_json(f"orders/{oc3}/paid.json")["session_id"] == sid_1 and not mails_to("c3@example.com", n0),
      (c, j, xs, [m["subject"] for m in owner]))
c, j = hook(extra)
check("C3 replayed: no second note", c == 200 and len(mails_to("info@snapeyes.com", n0)) == 1, (c, j))
bad = json.loads(json.dumps(extra))
bad.update(id="cs_test_" + "f" * 24, amount_total=1997, payment_intent="pi_test_extra2")
bad["metadata"] = dict(bad["metadata"], eyes="99")
H.Fake.sessions[bad["id"]] = bad
n1 = len(H.Fake.emails)
c, j = hook(bad)
check("C3 a second payment whose metadata cannot be read: still 200, stored and told",
      c == 200 and len([f for f in os.listdir(local(f"orders/{oc3}")) if f.startswith("extra_payment_")]) == 2
      and len(mails_to("info@snapeyes.com", n1)) == 1, (c, j))
r = subprocess.run(ADMIN + ["status", oc3], capture_output=True, text=True, env=dict(os.environ))
check("C3 order_admin status shows the extra payment", "EXTRA PAYMENT" in r.stdout and "3997" in r.stdout, r.stdout)

# ======================================================================================== D. clean-up asks Stripe
H.setup_env(STORES["purge"], stub.server_address[1])


def age(order, hours):
    p = local(f"orders/{order}/order.json")
    rec = json.load(open(p, encoding="utf-8"))
    rec["created_at"] = int(time.time() - hours * 3600)
    open(p, "w", encoding="utf-8").write(json.dumps(rec))


c, d = draft(1)
od1, kd1 = d["order"], d["k"]
checkout(od1, kd1)
H.pay_session(sid_of(od1), "d1@example.com")                    # paid at Stripe, the webhook never came
c, d = draft(1)
od2, kd2 = d["order"], d["k"]
checkout(od2, kd2)                                              # still open at Stripe
c, d = draft(1)
od3, kd3 = d["order"], d["k"]                                   # never checked out
for o in (od1, od2, od3):
    age(o, 49)
old = pay.day(time.time() - 6 * 86400)
for top in ("draftlog", "ticketuse"):
    store.put(f"{top}/{old}/1-old.json", b"{}", "application/json")
dry = subprocess.run(ADMIN + ["purge"], capture_output=True, text=True, env=dict(os.environ))
check("D dry run changes nothing", dry.returncode == 0 and os.path.exists(local(f"orders/{od3}/order.json"))
      and not os.path.exists(local(f"orders/{od1}/paid.json")), (dry.stdout, dry.stderr))
noenv = {k: v for k, v in os.environ.items() if k != "STRIPE_SECRET_KEY"}
r0 = subprocess.run(ADMIN + ["purge", "--yes"], capture_output=True, text=True, env=noenv)
check("D without a Stripe key here: orders that had a checkout are KEPT, the one without is deleted",
      r0.returncode == 0 and os.path.exists(local(f"orders/{od1}/order.json")) and os.path.exists(local(f"orders/{od2}/order.json"))
      and not os.path.exists(local(f"orders/{od3}/order.json")), (r0.stdout, r0.stderr))
n0 = len(H.Fake.emails)
r = subprocess.run(ADMIN + ["purge", "--yes"], capture_output=True, text=True, env=dict(os.environ))
p1 = read_json(f"orders/{od1}/paid.json") if os.path.exists(local(f"orders/{od1}/paid.json")) else {}
check("D paid at Stripe without paid.json: RECORDED (not deleted), confirmation to the customer, note to the owner",
      r.returncode == 0 and p1.get("source") == "cleanup" and os.path.exists(local(f"orders/{od1}/draft/eye_1.json"))
      and len(mails_to("d1@example.com", n0)) == 1 and mails_to("info@snapeyes.com", n0), (r.stdout, r.stderr, p1))
check("D an order whose session is still open is kept", os.path.exists(local(f"orders/{od2}/order.json")), r.stdout)
check("D old ticket and upload markers removed", not os.path.exists(local(f"draftlog/{old}/1-old.json"))
      and not os.path.exists(local(f"ticketuse/{old}/1-old.json")), r.stdout)
c, j = hook(H.Fake.sessions[sid_of(od1)])
check("D the late webhook then finds it paid: 200, nothing new", c == 200 and j.get("new") is False, (c, j))

# the daily cron entry
c, j = get("/api/order?cron=purge")
check("cron without CRON_SECRET: 503 cron_not_configured", c == 503 and j.get("reason") == "cron_not_configured", (c, j))
env(CRON_SECRET="cron-" + "s" * 30)
c, j = get("/api/order?cron=purge", {"Authorization": "Bearer wrong"})
c2, j2 = get("/api/order?cron=purge")
check("cron with a wrong or no Authorization: 403", c == 403 and c2 == 403, (c, j, c2, j2))
H.Fake.sessions[sid_of(od2)]["status"] = "expired"               # its session ran out
oldday = pay.day(time.time() - 3 * 86400)
oc_id, oc_k, _ = pay.new_order("en", order=f"{oldday}-00000000c0ffee00")   # an order made three days ago
store.put(f"orders/{oc_id}/draft/eye_1.json", b"{}", "application/json")
age(oc_id, 72)
c, j = get("/api/order?cron=purge", {"Authorization": "Bearer " + os.environ["CRON_SECRET"]})
check("cron with the secret: 200, the three-day-old unpaid order deleted, the expired-session one (made today) left "
      "for a later run", c == 200 and j.get("ok") and (j.get("unpaid") or {}).get("deleted", 0) >= 1 and not os.path.exists(local(f"orders/{oc_id}/order.json"))
      and os.path.exists(local(f"orders/{od1}/paid.json")), (c, j))

# ---------------------------------------------------------------------------------------- hygiene
bad = []
for f in ("api/_lib/pay.py", "api/order.py", "api/checkout.py", "api/stripe_webhook.py", "api/health.py",
          "scripts/order_admin.py", "api/_lib/store.py"):
    t = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in t for ch in (chr(0x2013), chr(0x2014))) or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in t):
        bad.append(f)
check("my files: no em/en dashes, no control characters", not bad, bad)

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
api.shutdown()
stub.shutdown()
sys.exit(1 if fails else 0)
