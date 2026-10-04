# -*- coding: utf-8 -*-
"""Payments review (markets): adversarial cases the builders' suites do not cover. Fake Stripe + Resend + legal pack
(wave-r-back/pb/harness.py), own store folder, synthetic keys, no network.
    python test_payrev.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, json, time, secrets
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.environ.get("SNAPEYES_SP") or os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(SP, "wave-r-back", "pb"))
import harness as H

stub = H.start_stub()
STORE = os.path.join(HERE, "store_payrev")
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib import ops

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:900]}"), flush=True)


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path):
    r = requests.get(BASE + path, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def hook(obj, typ="checkout.session.completed", eid=None):
    body, sig = H.signed_event(obj, typ, eid=eid)
    r = requests.post(BASE + "/api/stripe_webhook", data=body,
                      headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=60)
    return r.status_code, r.json()


def local(path):
    return os.path.join(STORE, *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


def exists(path):
    return os.path.exists(local(path))


SMALL = H.jpeg_b64(256, 1)


def draft(eye, order=None, k=None, lang="en"):
    b = {"action": "draft", "eye": eye, "crop": SMALL, "preview": SMALL, "pad": 1.12, "lang": lang, "ref": f"e{eye}",
         "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work")}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def new_order(eyes=1, lang="en"):
    c, d = draft(1, lang=lang)
    assert c == 200, (c, d)
    o, k = d["order"], d["k"]
    for e in range(2, eyes + 1):
        c, d = draft(e, o, k, lang=lang)
        assert c == 200, (c, d)
    return o, k


def checkout(order, k, eyes=1, style="studio_black", lang="en", **kw):
    b = {"order": order, "k": k, "eyes": eyes, "style": style, "names": "", "title": "", "lang": lang,
         "consent_digital": True}
    b.update(kw)
    return post("/api/checkout", b)


def sid_of(order):
    return read_json(f"orders/{order}/order.json")["checkout"]["session_id"]


def mails_to(addr, since=0):
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [addr]]


H.Fake.legal = None
pay._LEGAL.update(pack=None, t=0.0)

# ------------------------------------------------------------------ 1. an EUR order from before markets, paid after the deploy
o1, k1 = new_order(2, "de")
c, j = checkout(o1, k1, 2, "celestial_gold", "de")
s1 = H.Fake.sessions[sid_of(o1)]
# strip what the new code adds, as a session made by HEAD would look
for key in ("market", "currency", "amount"):
    s1["metadata"].pop(key, None)
rec1 = read_json(f"orders/{o1}/order.json")
for key in ("market",):
    rec1["checkout"].pop(key, None)
    rec1["checkout"]["spec"].pop(key, None)
rec1["checkout"]["consent"] = dict(rec1["checkout"]["consent"], version="2026-09-29.1", text=pay.CONSENT_TEXT["de"])
s1["metadata"]["consent_version"] = "2026-09-29.1"
store.put(f"orders/{o1}/order.json", store.json_bytes(rec1), "application/json", upsert=True)
H.pay_session(s1["id"], "alt@example.com")
n0 = len(H.Fake.emails)
c, j = hook(s1)
p1 = read_json(f"orders/{o1}/paid.json") if exists(f"orders/{o1}/paid.json") else {}
m1 = mails_to("alt@example.com", n0)
t1 = m1[0]["text"] if m1 else ""
check("1a old EUR session (no market/currency/amount in metadata) paid after deploy: recorded eu, eur, no mismatch",
      c == 200 and p1.get("market") == "eu" and p1.get("currency") == "eur" and "amount_mismatch" not in p1
      and p1.get("amount_total") == 3997, (c, j, p1))
check("1b its German confirmation: 39,97 EUR text, the old consent text quoted, EU edition",
      "Preis: 39,97 €." in t1 and pay.CONSENT_TEXT["de"] in t1 and "Australi" not in t1.split("______")[0], t1[:900])
c, j = get(f"/api/order?o={o1}&k={k1}")
check("1c old order status: EUR, market eu", c == 200 and j.get("currency") == "EUR" and j.get("market") == "eu", j)

# a record exactly as HEAD wrote it (paid.json without market, spec without market)
p_old = dict(p1)
p_old.pop("market", None)
p_old["spec"] = {k: v for k, v in p_old["spec"].items() if k != "market"}
check("1d paid_market/currency_of of a HEAD record: eu / eur; texts in euros",
      pay.paid_market(p_old) == "eu" and pay.currency_of(None) == "eur"
      and pay.amount_text(3997, "en", p_old.get("currency")) == "39.97 EUR"
      and pay.price_text(3997, "en", None) == "€39.97")

# ------------------------------------------------------------------ 2. webhook replays and duplicates (AUD)
o2, k2 = new_order(1)
checkout(o2, k2, 1, "supernova", "en", market="au")
s2 = H.pay_session(sid_of(o2), "replay@example.com")
n0 = len(H.Fake.emails)
eid = "evt_test_" + secrets.token_hex(6)
r_a = hook(s2, eid=eid)
r_b = hook(s2, eid=eid)
r_c = hook(s2, typ="checkout.session.async_payment_succeeded")
conf2 = mails_to("replay@example.com", n0)
notes2 = [m for m in mails_to("info@snapeyes.com", n0) if m["subject"].startswith("SnapEyes: new order")]
p2 = read_json(f"orders/{o2}/paid.json")
check("2a AUD webhook replayed 3x: paid once, one confirmation, one owner note, A$49",
      r_a[1].get("new") is True and r_b[1].get("new") is False and r_c[1].get("new") is False and len(conf2) == 1
      and len(notes2) == 1 and p2["amount_total"] == 4900 and p2["currency"] == "aud" and "A$49" in conf2[0]["text"],
      (r_a, r_b, r_c, len(conf2), len(notes2)))

# ------------------------------------------------------------------ 3. unlocking with a session of another currency / another order
o3, k3 = new_order(1)
checkout(o3, k3, 1, "studio_black", "en", market="au")
s3 = H.Fake.sessions[sid_of(o3)]
H.pay_session(s3["id"], "wrongcur@example.com")
s3["currency"] = "eur"            # Stripe-side conversion (the case the check exists for)
c, j = get(f"/api/order?o={o3}&k={k3}&s={s3['id']}")
check("3a order page with its own session paid in the wrong currency: not unlocked (unpaid)",
      c == 200 and j.get("state") == "unpaid" and not exists(f"orders/{o3}/paid.json"), (c, j))
# a paid AU session of order o2 presented on the order page of o3
c, j = get(f"/api/order?o={o3}&k={k3}&s={s2['id']}")
check("3b another order's paid session on this order page: not unlocked", c == 200 and j.get("state") == "unpaid"
      and not exists(f"orders/{o3}/paid.json"), (c, j))
# the same session delivered by webhook with metadata that names another order (it is signed by Stripe, but a session
# of ours for another order cannot pay this one)
c, j = hook(dict(s2, metadata=dict(s2["metadata"], order=o3)))
check("3c a session whose metadata names order o3 but carries o2's key fingerprint: ignored",
      c == 200 and j.get("ignored") == "session does not match" and not exists(f"orders/{o3}/paid.json"), (c, j))

# ------------------------------------------------------------------ 4. the daily clean-up and a paid session of the wrong currency
pay.start_clock()
rec3 = read_json(f"orders/{o3}/order.json")
v = pay.stripe_verdict(o3, rec3, record=False)
# (fixer: the clean-up now keeps such an order and tells the owner, instead of deleting it in silence)
check("4a stripe_verdict of an unpaid order whose only session is PAID in the wrong currency: unknown (kept)",
      v == "unknown", f"verdict={v!r}")
# the clean-up records a paid AU session the webhook never delivered
o4, k4 = new_order(2)
checkout(o4, k4, 2, "studio_black", "en", market="au")
H.pay_session(sid_of(o4), "nohook@example.com")
rec4 = read_json(f"orders/{o4}/order.json")
n0 = len(H.Fake.emails)
pay.start_clock()
v4 = pay.stripe_verdict(o4, rec4, record=True)
p4 = read_json(f"orders/{o4}/paid.json") if exists(f"orders/{o4}/paid.json") else {}
m4 = mails_to("nohook@example.com", n0)
check("4b clean-up records a paid AU session without webhook: market au, 7900 aud, AU invoice email",
      v4 == "paid" and p4.get("market") == "au" and p4.get("amount_total") == 7900 and p4.get("source") == "cleanup"
      and len(m4) == 1 and "A$79" in m4[0]["text"] and "Invoice" in m4[0]["text"], (v4, p4, len(m4)))

# ------------------------------------------------------------------ 5. market switch within one order: old sessions closed, extra payment in its own currency
o5, k5 = new_order(1)
checkout(o5, k5, 1, "studio_black", "en", market="au")
sA = sid_of(o5)
c, j = checkout(o5, k5, 1, "studio_black", "en", market="eu")
sE = sid_of(o5)
check("5a switching au -> eu: the AU session is expired before the EUR one is made, EUR 1997",
      c == 200 and j["amount"] == 1997 and j["currency"] == "EUR" and H.Fake.sessions[sA]["status"] == "expired", (c, j))
# Stripe let the old AU tab be paid anyway (a race) and the EUR one too: the second is an extra payment in AUD
H.Fake.sessions[sA]["status"] = "open"
H.pay_session(sE, "switch@example.com")
H.pay_session(sA, "switch@example.com")
n0 = len(H.Fake.emails)
hook(H.Fake.sessions[sE])
c, j = hook(H.Fake.sessions[sA])
notes5 = [m for m in mails_to("info@snapeyes.com", n0) if "paid twice" in m["subject"]]
check("5b second payment in AUD after the EUR one: extra payment, owner told to refund 39.00 AUD (and the first 19.97 EUR)",
      j.get("extra_payment") is True and len(notes5) == 1 and "39.00 AUD" in notes5[0]["subject"]
      and "19.97 EUR" in notes5[0]["text"], (j, [(m["subject"], m["text"][:300]) for m in notes5]))

# ------------------------------------------------------------------ 6. checkout body tampering
o6, k6 = new_order(3)
res = {}
for label, extra in {"lt+price": dict(market="lt", amount=1, unit_amount=1, currency="huf"),
                     "au+prices": dict(market="au", prices={"two_eyes": 1, "each_further_eye": 1}),
                     "null": dict(market=None), "proto": dict(market="__proto__"), "upper": dict(market="EU"),
                     "hu_list": dict(market=["hu"]), "tab": dict(market="au\t")}.items():
    n = len(H.Fake.creates)
    c, j = checkout(o6, k6, 3, "studio_black", "en", **extra)
    p = H.Fake.creates[-1][0] if len(H.Fake.creates) > n else {}
    res[label] = (c, j.get("amount"), j.get("currency"), p.get("line_items[0][price_data][unit_amount]"),
                  p.get("line_items[0][price_data][currency]"))
check("6a tampered bodies: lt 3 eyes = 5497 EUR; au 3 eyes = 10800 AUD; null = eu; __proto__/EU/list/tab refused",
      res["lt+price"] == (200, 5497, "EUR", "5497", "eur") and res["au+prices"] == (200, 10800, "AUD", "10800", "aud")
      and res["null"][:3] == (200, 5497, "EUR") and all(res[x][0] == 400 and res[x][3] is None for x in ("proto", "upper", "hu_list", "tab")),
      res)
c, j = checkout(o6, k6, 3, "studio_black", "en", market="au", eyes_billable=1)
check("6b eyes stays what the body says (3) even with extra fields: A$108", c == 200 and j["amount"] == 10800, (c, j))
c, j = checkout(o6, k6, 1, "studio_black", "de", market="au", consent_digital="true")
check("6c consent_digital must be the JSON true (a string is refused) for au too", c == 400 and j.get("reason") == "consent_required", (c, j))
c, j = checkout(o6, k6, 1, "studio_black", "de", market="au")
rec6 = read_json(f"orders/{o6}/order.json")
check("6d au in German records the Australian German consent text", c == 200
      and rec6["checkout"]["consent"]["text"] == pay.CONSENT_TEXT_AU["de"], rec6["checkout"]["consent"])

# ------------------------------------------------------------------ 7. HUF units end to end (a hu session made the way checkout would)
o7, k7 = new_order(8, "de")
rec7 = read_json(f"orders/{o7}/order.json")
spec7 = {"eyes": 8, "style": "deep_nebula", "layout": pay.L.multi_layout(8), "names": "", "title": "", "lang": "de", "market": "hu"}
cons7 = {"version": pay.CONSENT_VERSION, "at": pay.iso(), "lang": "de", "text": pay.CONSENT_TEXT["de"]}
pay.start_clock()
amt7 = pay.price_cents(8, "deep_nebula", "hu")
sess7 = pay.create_session(o7, k7, spec7, amt7, cons7, int(time.time()) + 7200)
rec7["checkout"] = {"session_id": sess7["id"], "amount": amt7, "currency": "huf", "market": "hu", "spec": spec7,
                    "consent": dict(cons7, text_sha256="x")}
store.put(f"orders/{o7}/order.json", store.json_bytes(rec7), "application/json", upsert=True)
H.pay_session(sess7["id"], "forint@example.com")
n0 = len(H.Fake.emails)
c, j = hook(H.Fake.sessions[sess7["id"]])
t7 = (mails_to("forint@example.com", n0) or [{"text": ""}])[0]["text"]
check("7a HUF 8 eyes: 4393000 fillér = 43 930 Ft in the German email; admin 43930 HUF",
      amt7 == 4393000 and "Preis: 43 930 Ft." in t7 and pay.amount_text(amt7, "en", "huf") == "43930 HUF", t7[:700])
c, j = post("/api/order", {"action": "withdraw", "order": o7, "k": k7, "name": "Test Elek", "email": "forint@example.com", "lang": "de"})
w7 = j.get("withdrawal") or {}
check("7b HUF withdrawal reply: 4393000 HUF", w7.get("amount") == 4393000 and w7.get("currency") == "HUF", (c, j))

# ------------------------------------------------------------------ 8. admin row of a HEAD-era record
pay.start_clock()
store.put(f"orders/{o1}/paid.json", store.json_bytes(p_old), "application/json", upsert=True)
row = ops.order_row(o1)
check("8a admin row of an old paid record: EUR, eu", row["currency"] == "EUR" and row["market"] == "eu" and row["amount"] == 3997, row)

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
api.shutdown()
stub.shutdown()
sys.exit(1 if fails else 0)
