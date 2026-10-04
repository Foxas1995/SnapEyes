# -*- coding: utf-8 -*-
"""Round 4 tests (wave q, role payfix): the withdrawal function's bounded emails under load (owner notes: first
statement per order and outcome at once, NOTE_DAY_MAX a day, the rest in one digest; repeat receipts; receipts to
other addresses than the payment email; neutral receipts per address a day and a month; storage-failure emails
capped across instances), the 14-day period counted to the end of the 14th day, neutral receipts without links or
phone numbers, no anonymous writes where nothing can be sold, the live-sales gate on the legal texts and
CRON_SECRET, and the clean-up's new steps (events.purge_old, the 24-month audit log purge, the monthly receipt
marks, the refund reminder). Fake Stripe + Resend + legal pack (../harness.py), local store folders, synthetic keys,
the renderer stubbed. No network, no real key.
    python test_round4.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, json, time, base64, re, shutil, subprocess, secrets, calendar, hashlib, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
PB = os.path.dirname(HERE)
sys.path.insert(0, PB)
import harness as H
import socketserver
socketserver.TCPServer.request_queue_size = 512

stub = H.start_stub()
STORE = os.path.join(HERE, "store_r4")
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib import withdraw as W
from _lib import cleanup as C

RESULTS = []
ADMIN = [sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py")]
PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
DASHES = (chr(0x2013), chr(0x2014))
OWNER = "info@snapeyes.com"
LIVE_SK = "sk_live_" + "Fake0123456789abcdefGHIJ"


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:900]}"), flush=True)


def post(path, body, headers=None):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    r = requests.post(BASE + path, data=json.dumps(body), headers=h, timeout=120)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def get(path, headers=None):
    r = requests.get(BASE + path, headers=headers or {}, timeout=120)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {"raw": r.text[:200]}


def hook(obj, typ="checkout.session.completed"):
    body, sig = H.signed_event(obj, typ)
    r = requests.post(BASE + "/api/stripe_webhook", data=body,
                      headers={"Content-Type": "application/json", "Stripe-Signature": sig}, timeout=60)
    return r.status_code, r.json()


def local(path):
    return os.path.join(STORE, *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    store.put(path, store.json_bytes(obj), "application/json", upsert=True)


def exists(path):
    return os.path.exists(local(path))


def files_under(top):
    out = []
    for dp, _, fs in os.walk(local(top)):
        out += [os.path.join(dp, f) for f in fs]
    return out


SMALL = H.jpeg_b64(256, 1)


def draft(eye, order=None, k=None, lang="en"):
    b = {"action": "draft", "eye": eye, "crop": SMALL, "preview": SMALL, "pad": 1.12, "lang": lang, "ref": f"e{eye}",
         "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work")}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def checkout(order, k, lang="en"):
    return post("/api/checkout", {"order": order, "k": k, "eyes": 1, "style": "studio_black", "names": "",
                                  "title": "", "lang": lang, "consent_digital": True})


def new_checkout(lang="en"):
    c, d = draft(1, lang=lang)
    assert c == 200, (c, d)
    o, k = d["order"], d["k"]
    c, co = checkout(o, k, lang)
    assert c == 200, (c, co)
    return o, k, read_json(f"orders/{o}/order.json")["checkout"]["session_id"]


def paid_order(lang="en", email="kunde@example.com"):
    o, k, sid = new_checkout(lang)
    c, j = hook(H.pay_session(sid, email))
    assert c == 200, (c, j)
    return o, k, sid


def mails_to(addr, since=0):
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [addr]]


def owner_since(n0, exclude_new_orders=True):
    return [m for m in mails_to(OWNER, n0) if not (exclude_new_orders and m["subject"].startswith("SnapEyes: new order"))]


def withdraw(o, k=None, name="Ana Tester", email="kunde@example.com", lang="en", **kw):
    b = {"action": "withdraw", "order": o, "name": name, "email": email, "lang": lang}
    if k:
        b["k"] = k
    b.update(kw)
    return post("/api/order", b)


def fresh(name):
    """A new store folder (today's counters start at zero), email and Stripe on (a test key, local: sells)."""
    global STORE
    STORE = os.path.join(HERE, name)
    H.setup_env(STORE, stub.server_address[1])
    H.Fake.emails.clear()
    H.Fake.fail_mail.clear()
    H.Fake.legal = json.loads(json.dumps(PACK))
    H.Fake.legal_fail = 0
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)


def next_day():
    """Today's slot folder goes, as it would tomorrow (the daily counters start again; the monthly ones stay)."""
    shutil.rmtree(local(f"withdrawlog/{pay.day()}"), ignore_errors=True)


def fake_master_eye(body):
    key = f"orders/{body['order']}/eye_{body['eye']}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False}
    store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
    return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False}


H.MODS["order"].ME.master_eye = fake_master_eye
ts = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))

# ======================================================================================== P. the 14-day period
fresh("store_r4")
oP, kP, _ = paid_order("de", "pia@example.com")
recP, paidP = read_json(f"orders/{oP}/order.json"), read_json(f"orders/{oP}/paid.json")
base = dict(paidP, paid_at=ts("2026-10-01T15:00:00"))
A = lambda now: W._assess_paid(oP, recP, base, ts(now))
check("P1 paid 1 Oct 15:00 UTC: the 14th day after it (15 Oct) is in time until its end (18:00 and 23:59 UTC)",
      A("2026-10-15T18:00:00")["outcome"] == "withdrawn" and A("2026-10-15T23:59:59")["outcome"] == "withdrawn")
check("P2 ... and in every EU time zone: 16 Oct 00:30 UTC (still 15 Oct on the Azores) is in time",
      A("2026-10-16T00:30:00")["outcome"] == "withdrawn")
late = A("2026-10-16T04:00:00")
# wave r (role back): the end is now taken where it comes latest in the EU (UTC-4, overseas) for the contract's day
# where it is latest (UTC+4), and a weekend or holiday last day moves to the next working day. P3 to P6 below are
# the old checks rewritten to that rule (they encoded the earlier end: 16 Oct 01:00 UTC, "14 to 15 days")
check("P3 16 Oct 04:00 UTC (the end of 15 Oct at UTC-4): over, lapsed period_over, last day 15 Oct; 03:59 in time",
      late["outcome"] == "lapsed"
      and late["reason"] == "period_over" and late["period_last_day"] == "2026-10-15"
      and late["period_end"] == ts("2026-10-16T04:00:00") and A("2026-10-16T03:59:59")["outcome"] == "withdrawn", late)
end2, last2 = W.period_end(ts("2026-10-01T22:30:00"))
check("P4 paid 1 Oct 22:30 UTC (2 Oct in Berlin and Helsinki): the period runs to the end of Fri 16 Oct, everywhere",
      last2 == "2026-10-16" and end2 == ts("2026-10-17T04:00:00"), (last2, end2))
end3, last3 = W.period_end(ts("2026-10-01T00:05:00"))
check("P5 paid 1 Oct 00:05 UTC (30 Sep on the Azores): the latest end is used, never an earlier one",
      end3 >= ts("2026-10-15T22:00:00") and end3 == ts("2026-10-16T04:00:00") and last3 == "2026-10-15", (last3, end3))


def _bound(t):
    end, last = W.period_end(t)
    base = int((t + 4 * 3600) // 86400) + 14
    moved = (calendar.timegm(time.strptime(last, "%Y-%m-%d")) // 86400) - base
    return t + 14 * 86400 < end <= t + 15 * 86400 + 8 * 3600 + moved * 86400 and 0 <= moved <= 5


check("P6 the period always ends after 14 days, and at most 15 days and 8 hours after the payment plus the days a "
      "weekend or holiday moved it", all(_bound(ts("2026-01-01T00:00:00") + h * 3607) for h in range(0, 24 * 40)))
pp = read_json(f"orders/{oP}/paid.json")
pp["paid_at"] = int(time.time()) - 21 * 86400      # wave r: over whatever the hour or a moved last day
write_json(f"orders/{oP}/paid.json", pp)
n0 = len(H.Fake.emails)
c, j = withdraw(oP, kP, name="Pia", email="pia@example.com", lang="de")
last = W.period_end(pp["paid_at"])[1]
rm = mails_to("pia@example.com", n0)
check("P7 the lapsed reply names the last day; the German receipt says the period ended on that day",
      c == 200 and j["withdrawal"]["state"] == "lapsed" and j["withdrawal"]["period_last_day"] == last and rm
      and f"ist am {pay.date_text(last, 'de')} abgelaufen" in rm[0]["text"], (c, j, rm[0]["text"][:1500] if rm else ""))

# ======================================================================================== N. no anonymous writes where nothing is sold
fresh("store_r4_closed")
oX, kX, _ = paid_order("en", "xena@example.com")
for k in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
    os.environ.pop(k, None)
n0 = len(H.Fake.emails)
c, j = withdraw("260101-" + "0" * 16, None, name="Anon", email="anon@example.com")
c2, j2 = withdraw("not an order at all", None, name="Anon", email="anon@example.com")
check("N1 no Stripe keys (the live site before launch): a statement for an order that does not exist is 409 no_order, "
      "recorded false, nothing stored, no email", c == 409 and j.get("reason") == "no_order" and j.get("recorded") is False
      and c2 == 409 and not exists("withdrawals") and not exists(f"withdrawlog/{pay.day()}") and len(H.Fake.emails) == n0,
      (c, j, c2, j2))
c, j = withdraw(oX, None, name="Xena", email="other@example.com")
check("N2 ... a stored order with another email is still recorded apart (404 not_found)", c == 404 and j.get("recorded") is True
      and len([p for p in files_under("withdrawals") if not p.endswith(("_ack.json", "_note.json"))]) == 1, (c, j))
c, j = withdraw(oX, kX, name="Xena", email="xena@example.com")
check("N3 ... and the order's own customer withdraws as ever (200 withdrawn)", c == 200 and j["withdrawal"]["state"] == "withdrawn", (c, j))
os.environ.update(STRIPE_SECRET_KEY=H.SK, STRIPE_WEBHOOK_SECRET=H.WHSEC, VERCEL_ENV="production")
c, j = withdraw("260101-" + "1" * 16, None, name="Anon", email="anon@example.com")
check("N4 a TEST key on production (no payment counts): no_order too", c == 409 and j.get("reason") == "no_order", (c, j))
os.environ.pop("VERCEL_ENV")
c, j = withdraw("260101-" + "2" * 16, None, name="Anon", email="anon@example.com")
check("N5 where test orders count (local): recorded as before (404 not_found)", c == 404 and j.get("recorded") is True, (c, j))

# ======================================================================================== G. the live-sales gate
fresh("store_r4_gate")
os.environ.update(STRIPE_SECRET_KEY=LIVE_SK, CRON_SECRET="cron-" + "s" * 30)


def gate(pack=None, fail=False):
    H.Fake.legal = json.loads(json.dumps(pack if pack is not None else PACK))
    H.Fake.legal_fail = 10 ** 6 if fail else 0
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
    return pay.ordering_problem()


check("G1 live key + Resend + CRON_SECRET + complete legal texts: ordering open", gate() == "" and pay.ordering_open(),
      gate())
c, h = get("/api/health")
c2, ck = get("/api/checkout")
check("G2 health: ordering, stripe_live, cron, legal all true; checkout open", h.get("ordering") is True
      and h.get("stripe_live") is True and h.get("cron") is True and h.get("legal") is True and ck.get("open") is True, (h, ck))
why = gate(fail=True)
check("G3 the legal texts cannot be read: closed, and the reason says so (no value in it)",
      "order-mail.json cannot be read" in why and not pay.ordering_open(), why)
c, h = get("/api/health")
c2, ck = get("/api/checkout")
c3, d = draft(1)
check("G4 ... health legal false, ordering false; checkout closed; draft 503 payments_not_configured",
      h.get("legal") is False and h.get("ordering") is False and ck.get("open") is False and c3 == 503
      and d.get("reason") == "payments_not_configured", (h, ck, c3, d))
g0 = H.Fake.legal_gets
for _ in range(5):
    pay.ordering_problem()
    get("/api/health")
check("G5 after a failed fetch the gate does not fetch again for a minute (public pages cannot make it wait)",
      H.Fake.legal_gets == g0, (g0, H.Fake.legal_gets))
H.Fake.legal_fail = 0
pay._LEGAL["failed"] = time.time() - pay.LEGAL_RETRY - 1
check("G6 ... after that it fetches again and opens", pay.ordering_problem() == "" and H.Fake.legal_gets == g0 + 1,
      (pay.ordering_problem(), H.Fake.legal_gets - g0))
bad = json.loads(json.dumps(PACK))
bad["missing"] = ["seller.email"]
why = gate(bad)
check("G7 a pack whose missing list is not empty: closed, naming the fact", "seller.email" in why and "missing" in why, why)
ok = json.loads(json.dumps(PACK))
ok["missing"], ok["waived"] = [], ["seller.phone"]
ok["seller"]["phone"] = ""
check("G8 the phone left out by the owner's decision (waived, missing empty): open", gate(ok) == "", gate(ok))
bad = json.loads(json.dumps(PACK))
bad["seller"]["code"] = " "
check("G9 an empty company code: closed", "seller.code" in gate(bad), gate(bad))
bad = json.loads(json.dumps(PACK))
bad["seller"]["address"]["de"] = ""
check("G10 an empty German address: closed", "seller.address.de" in gate(bad), gate(bad))
bad = json.loads(json.dumps(PACK))
bad["missing"] = "seller.phone"
check("G11 a missing list that is not a list: closed", "missing" in gate(bad), gate(bad))
nomiss = json.loads(json.dumps(PACK))
nomiss.pop("missing", None)
check("G12 an older pack without the missing list: open", gate(nomiss) == "", gate(nomiss))
gate()
os.environ["CRON_SECRET"] = "short"
why = pay.ordering_problem()
check("G13 CRON_SECRET shorter than 16: closed, naming CRON_SECRET", "CRON_SECRET" in why and "short" not in why, why)
os.environ.pop("CRON_SECRET")
check("G14 no CRON_SECRET: closed", "CRON_SECRET" in pay.ordering_problem())
os.environ.pop("RESEND_API_KEY")
check("G15 no Resend: the Resend reason comes first", "RESEND_API_KEY" in pay.ordering_problem(), pay.ordering_problem())
os.environ.update(RESEND_API_KEY=H.RESEND, STRIPE_SECRET_KEY=H.SK)
check("G16 a TEST key (local): the legal and cron gates do not apply (the tests and previews run as before)",
      gate(fail=True) == "", gate(fail=True))
gate()

# ======================================================================================== L. bounded emails under load
fresh("store_r4_load")
orders = [paid_order("en", f"cust{i}@example.com") for i in range(W.NOTE_DAY_MAX + 4)]
m0 = len(H.Fake.emails)
_lf, _put = store.list_folder, store.put


def slow_list(*a, **kw):
    time.sleep(0.2)
    return _lf(*a, **kw)


def slow_put(*a, **kw):
    time.sleep(0.1)
    return _put(*a, **kw)


store.list_folder, store.put = slow_list, slow_put
with cf.ThreadPoolExecutor(len(orders)) as ex:
    firsts = list(ex.map(lambda x: withdraw(x[1][0], x[1][1], name=f"Cust {chr(65 + x[0])}", email=f"cust{x[0]}@example.com",
                                            nonce=f"first{x[0]:04d}ab"), enumerate(orders)))
store.list_folder, store.put = _lf, _put
notes = [m for m in owner_since(m0) if "withdrawal for order" in m["subject"]]
capped = [m for m in owner_since(m0) if "many withdrawals today" in m["subject"]]
pdig = [n for n in os.listdir(local(f"cleanup/digest/{pay.day()}")) if n.startswith("p-")] \
    if exists(f"cleanup/digest/{pay.day()}") else []
check("L1 14 first statements at once (storage latency): all effective, each customer gets a receipt",
      all(c == 200 and j["withdrawal"]["state"] == "withdrawn" for c, j in firsts)
      and all(len(mails_to(f"cust{i}@example.com", m0)) == 1 for i in range(len(orders))), [c for c, _ in firsts])
check("L2 owner notes at once: at most NOTE_DAY_MAX, the rest in the digest as NEED ACTION, one 'many today' note",
      len(notes) <= W.NOTE_DAY_MAX and len(notes) + len(pdig) == len(orders) and len(capped) == (1 if pdig else 0)
      and all("WITHDRAWN, refund" in m["subject"] for m in notes), (len(notes), len(pdig), len(capped)))
# repeats: later statements on withdrawn orders, to strangers, all at once
m1 = len(H.Fake.emails)
reps = [(o, k) for o, k, _ in orders[:3] for _ in range(6)]
store.list_folder, store.put = slow_list, slow_put
with cf.ThreadPoolExecutor(len(reps)) as ex:
    rr = list(ex.map(lambda x: withdraw(x[1][0], x[1][1], name="R", email=f"stranger{x[0]}@example.net"), enumerate(reps)))
store.list_folder, store.put = _lf, _put
taken = [j for c, j in rr if c == 200]
strangers = [m for m in H.Fake.emails[m1:] if m[0]["to"][0].startswith("stranger")]
check("L3 repeats: at most ORDER_DAY_MAX-1 more statements per order today (5 with the first), the rest 429",
      all(c in (200, 429) for c, _ in rr) and len(taken) <= 3 * (W.ORDER_DAY_MAX - 1)
      and all(j["withdrawal"]["already"] for j in taken), [c for c, _ in rr])
check("L4 repeats: no owner email at all, receipts at most one per order (and REPEAT_RECEIPT_DAY_MAX in all)",
      not owner_since(m1) and len(strangers) <= min(3 * W.REPEAT_RECEIPT_ORDER_MAX, W.REPEAT_RECEIPT_DAY_MAX)
      , (len(owner_since(m1)), len(strangers)))
rdig = [n for n in os.listdir(local(f"cleanup/digest/{pay.day()}")) if n.startswith("r-")]
check("L5 every repeat taken is in the digest (r-)", len(rdig) == len(taken), (len(rdig), len(taken)))
# a flood of statements that match no order, several to one address
m2 = len(H.Fake.emails)
store.list_folder, store.put = slow_list, slow_put
with cf.ThreadPoolExecutor(60) as ex:
    fl = list(ex.map(lambda i: withdraw(f"guess-{i}-{secrets.token_hex(3)}", None, name="Z",
                                        email="target@example.org" if i % 3 == 0 else f"z{i}@example.org"), range(150)))
store.list_folder, store.put = _lf, _put
stored_u = [p for p in files_under("withdrawals") if not p.endswith(("_ack.json", "_note.json"))]
tgt = mails_to("target@example.org", m2)
neutral = [m for m in H.Fake.emails[m2:] if m[0]["to"][0].endswith("@example.org")]
check("L6 150 unmatched statements at once: at most DAY_MAX stored and answered 404, the rest 429/503",
      len(stored_u) <= W.DAY_MAX and sum(1 for c, _ in fl if c == 404) == len(stored_u)
      and all(c in (404, 429, 503) for c, _ in fl), (len(stored_u), sorted(set(c for c, _ in fl))))
check("L7 neutral receipts: at most one per statement taken, at most RECEIPT_ADDR_MAX to one address today",
      len(neutral) <= len(stored_u) and len(tgt) <= W.RECEIPT_ADDR_MAX, (len(neutral), len(tgt)))
own_day = owner_since(m0)
check("L8 the whole load day: owner emails at once stay within NOTE_DAY_MAX + 3 fixed notes",
      len(own_day) <= W.NOTE_DAY_MAX + 3, [m["subject"] for m in own_day])
check("L9 the whole load day: every withdrawal email together stays far below Resend's free 100 a day",
      len(H.Fake.emails) - m0 <= len(orders) + W.NOTE_DAY_MAX + 3 + W.REPEAT_RECEIPT_DAY_MAX + W.DAY_MAX,
      len(H.Fake.emails) - m0)
# the digest the next day: one email, NEED ACTION first
today = pay.day()
yd = pay.day(time.time() - 86400)
os.rename(local(f"cleanup/digest/{today}"), local(f"cleanup/digest/{yd}"))
m3 = len(H.Fake.emails)
r = W.send_digests()
dg = mails_to(OWNER, m3)
t = dg[0]["text"] if dg else ""
check("L10 one digest: NEED ACTION first with the refund lines, then no match, then repeats; subject counts them",
      r["days"] == 1 and len(dg) == 1 and (not pdig or (t.startswith("NEED ACTION") and "REFUND" in t
      and f"{len(pdig)} NEED ACTION" in dg[0]["subject"])) and "matched no order" in dg[0]["subject"]
      and f"{len(rdig)} repeats" in dg[0]["subject"] and "evil" not in t, (dg[0]["subject"] if dg else None, t[:600]))

# ======================================================================================== O. receipts to other addresses, over days
fresh("store_r4_other")
oO, kO, _ = paid_order("en", "payer@example.com")
m0 = len(H.Fake.emails)
res = []
for i in range(W.RECEIPT_OTHER_MAX + 2):
    c, j = withdraw(oO, kO, name="O", email=f"other{i}@example.net")
    res.append((c, j["withdrawal"]["mail"]))
    next_day()
got = [len(mails_to(f"other{i}@example.net", m0)) for i in range(W.RECEIPT_OTHER_MAX + 2)]
payer = mails_to("payer@example.com", m0)
check("O1 the link's holder: receipts to other addresses stop after RECEIPT_OTHER_MAX for the order, then they go "
      "to the payment email (mail: redirected)", got == [1] * W.RECEIPT_OTHER_MAX + [0, 0]
      and [m for _, m in res] == ["sent"] * W.RECEIPT_OTHER_MAX + ["redirected"] * 2 and len(payer) == 2, (got, res))
check("O2 the redirected receipt says so, and shows the payment email as its address",
      payer and "You gave another address for this receipt" in payer[0]["text"]
      and "Email for this receipt: payer@example.com" in payer[0]["text"], payer[0]["text"][:900] if payer else "")
own = [m for m in owner_since(m0) if "withdrawal for order" in m["subject"]]
check("O3 the owner: ONE note for the order (the first statement), no second 'WITHDRAWN, refund'",
      len(own) == 1 and "WITHDRAWN, refund" in own[0]["subject"], [m["subject"] for m in own])
c, j = withdraw(oO, kO, name="O", email="payer@example.com", nonce="samenonce01")
c2, j2 = withdraw(oO, kO, name="O", email="payer@example.com", nonce="samenonce01")
check("O4 the same statement again (its nonce): the same answer about its receipt", j["withdrawal"]["mail"] == j2["withdrawal"]["mail"]
      and j2["withdrawal"]["already"] is True, (j["withdrawal"]["mail"], j2["withdrawal"]["mail"]))
# lapsed: the first gets the note, a repeat goes to the digest
oL, kL, _ = paid_order("en", "lars@example.com")
c, j = get(f"/api/order?o={oL}&k={kL}")
post("/api/order", {"action": "make", "order": oL, "k": kL, "eye": 1})
m1 = len(H.Fake.emails)
c1, j1 = withdraw(oL, kL, name="Lars", email="lars@example.com")
c2, j2 = withdraw(oL, kL, name="Lars", email="lars@example.com")
ln = [m for m in owner_since(m1) if "withdrawal for order" in m["subject"]]
check("O5 lapsed twice: one note ('please look'), the second in the digest; both answered lapsed",
      j1["withdrawal"]["state"] == "lapsed" and j2["withdrawal"]["state"] == "lapsed" and len(ln) == 1
      and "please look" in ln[0]["subject"] and any(n.startswith("r-") for n in os.listdir(local(f"cleanup/digest/{pay.day()}"))),
      ([m["subject"] for m in ln], j1["withdrawal"], j2["withdrawal"]))
check("O6 the marks are kept with the order's records (pay.kept_record)", pay.kept_record(f"orders/{oO}/withdrawal-first-withdrawn.json")
      and pay.kept_record(f"orders/{oO}/withdrawal-to-abcdef0123.json") and pay.kept_record(f"orders/{oO}/refunded.json"))

# ======================================================================================== E. what a neutral receipt echoes
fresh("store_r4_echo")
m0 = len(H.Fake.emails)
c, j = withdraw("hotline 0800 123 4567 or +49 (30) 123-45-67", None, name="Call +49 30 1234567 now, Anna 2 go",
                email="echo@example.net")
m = mails_to("echo@example.net", m0)
tt, hh = (m[0]["text"], m[0].get("html") or "") if m else ("", "")
check("E1 no phone number from the typed name or order text reaches the neutral receipt (text or html)",
      c == 404 and m and "1234567" not in tt and "123 4567" not in tt and "123-45-67" not in tt
      and "1234567" not in hh and "Name: Call [...] now, Anna 2 go" in tt, tt[:1400])
c, j = withdraw(" #260929-3f9a0c1d2e4b5a6 ", None, name="Anna", email="typo@example.net")
m = mails_to("typo@example.net", m0)
check("E2 an order number with a typo stays readable in the receipt", m and "Order number given: #260929-3f9a0c1d2e4b5a6" in m[0]["text"],
      m[0]["text"][:900] if m else "")
check("E3 echo_name / echo_order: names and links as before, digits of a phone gone",
      W.echo_name("Anna-Lena Müller") == "Anna-Lena Müller" and W.echo_name("J.R. Smith") == "J.R. Smith"
      and W.echo_name("x http://evil.example y") == "x [...] y" and W.echo_name("Tel 555 0100") == "Tel [...]"
      and W.echo_order("260929-3f9a0c1d2e4b5a6c") == "260929-3f9a0c1d2e4b5a6c"
      and W.echo_order("call 0800 123 4567") == "call [...]")
# the month's limit per address
fresh("store_r4_month")
m0 = len(H.Fake.emails)
sent = []
for d in range(3):
    for i in range(W.RECEIPT_ADDR_MAX + 1):
        sent.append(withdraw(f"month-{d}-{i}", None, name="M", email="month@example.net")[1]["withdrawal"]["mail"])
    next_day()
check("E4 one address: RECEIPT_ADDR_MAX a day, RECEIPT_ADDR_MONTH_MAX a month (a third day sends none)",
      len(mails_to("month@example.net", m0)) == W.RECEIPT_ADDR_MONTH_MAX
      and sent == ["sent", "sent", "not_sent", "sent", "sent", "not_sent", "not_sent", "not_sent", "not_sent"], sent)

# ======================================================================================== F. storage failure emails, capped across instances
fresh("store_r4_fallback")
real_put = store.put


def failing_put(path, *a, **kw):
    if path.startswith("withdrawlog/"):
        raise store.StorageError("injected")
    return real_put(path, *a, **kw)


store.put = failing_put
W._FALLBACK.update(day="", n=0)
m0 = len(H.Fake.emails)
codes = [withdraw(f"down-{i}", None, name="D", email=f"d{i}@example.com")[0] for i in range(W.FALLBACK_MAX + 3)]
W._FALLBACK.update(day="", n=0)          # a second instance
codes += [withdraw(f"down2-{i}", None, name="D", email=f"e{i}@example.com")[0] for i in range(W.FALLBACK_MAX + 3)]
store.put = real_put
fb = [(m, idem) for m, idem in H.Fake.emails[m0:] if "NOT stored" in m["subject"]]
keys = [idem for _, idem in fb]
check("F1 storage down: 503 each; each instance sends at most FALLBACK_MAX, numbered by day",
      set(codes) == {503} and len(fb) == 2 * W.FALLBACK_MAX
      and all(re.fullmatch(r"snapeyes-withdraw-fallback-\d{6}-[1-9][0-9]*", k or "") for k in keys), (codes, keys))
check("F2 ... and the two instances use the SAME FALLBACK_MAX keys, so Resend sends each once a day",
      len(set(keys)) == W.FALLBACK_MAX, sorted(set(keys)))

# ======================================================================================== C. the clean-up's new steps
fresh("store_r4_cron")
os.environ["CRON_SECRET"] = "cron-" + "s" * 30
AUTH = {"Authorization": "Bearer " + os.environ["CRON_SECRET"], "User-Agent": "vercel-cron/1.0"}
now = time.time()
g = time.gmtime(now)
old_day = time.strftime("%Y-%m-%d", time.gmtime(now - 25 * 31 * 86400))
keep_day = time.strftime("%Y-%m-%d", time.gmtime(now - 23 * 30 * 86400))
for d in (old_day, keep_day, time.strftime("%Y-%m-%d", g)):
    write_json(f"ops/audit/{d}/101500-abcd.json", {"action": "test"})
write_json("ops/audit/undated-note.json", {"x": 1})
write_json(f"ops/audit/{time.strftime('%y%m', time.gmtime(now - 26 * 31 * 86400))}/x.json", {"x": 1})
old_ev = time.strftime("%Y-%m-%d", time.gmtime(now - 400 * 86400))
write_json(f"ops/events/{old_ev}/000000-aaaa.json", {"kind": "analyze"})
write_json(f"withdrawaddr/{time.strftime('%y%m', time.gmtime(now - 100 * 86400))}/m-aaaa-bbbb.json", {})
write_json(f"withdrawaddr/{time.strftime('%y%m', g)}/m-cccc-dddd.json", {})
# a withdrawn paid order 11 days ago, not refunded; one marked refunded; one refunded in the admin panel
rem = []
for i in range(3):
    o, k, _ = paid_order("en", f"ref{i}@example.com")
    withdraw(o, k, name="R", email=f"ref{i}@example.com")
    write_json(f"cleanup/withdrawn/{o}.json", {"t": int(now) - 11 * 86400, "order": o})
    rem.append(o)
envs = dict(os.environ, STORE_LOCAL_DIR=STORE)
r = subprocess.run(ADMIN + ["refunded", rem[1], "--note", "refunded in Stripe"], capture_output=True, text=True, env=envs,
                   encoding="utf-8")
check("C1 order_admin refunded marks the order (refunded.json)", r.returncode == 0 and exists(f"orders/{rem[1]}/refunded.json"),
      r.stdout[-400:] + r.stderr[-400:])
pi = read_json(f"orders/{rem[2]}/paid.json")["payment_intent"]
write_json(f"ops/refunds/{rem[2]}/{hashlib.sha256(pi.encode()).hexdigest()[:16]}.json", {"refund": "re_x", "status": "succeeded"})
r = subprocess.run(ADMIN + ["cleanup"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("C2 the dry run lists the audit deletion and the reminder, and changes nothing", r.returncode == 0
      and "would delete" in r.stdout and "audit log" in r.stdout and "would remind the owner to refund " + rem[0] in r.stdout
      and exists(f"ops/audit/{old_day}/101500-abcd.json"), r.stdout[-1500:] + r.stderr[-600:])
m0 = len(H.Fake.emails)
c, j = get("/api/order", AUTH)
check("C3 the daily run: 200, events.purge_old ran (its reply), audit files deleted", c == 200
      and isinstance(j.get("events"), dict) and j["events"].get("ok") is True and j["audit"]["files"] == 2, (c, j))
check("C4 audit log: older than 24 months gone (a day folder and a yymm folder), younger and undated kept",
      not exists(f"ops/audit/{old_day}/101500-abcd.json") and exists(f"ops/audit/{keep_day}/101500-abcd.json")
      and exists(f"ops/audit/{time.strftime('%Y-%m-%d', g)}/101500-abcd.json") and exists("ops/audit/undated-note.json"))
check("C5 events older than their retention are gone (events.purge_old)", not exists(f"ops/events/{old_ev}/000000-aaaa.json"))
check("C6 the monthly receipt marks: months before the previous one gone, this month kept",
      not exists(f"withdrawaddr/{time.strftime('%y%m', time.gmtime(now - 100 * 86400))}/m-aaaa-bbbb.json")
      and exists(f"withdrawaddr/{time.strftime('%y%m', g)}/m-cccc-dddd.json"))
rn = [m for m in mails_to(OWNER, m0) if "reminder, refund order" in m["subject"]]
check("C7 one refund reminder: only for the order neither marked nor refunded in the admin panel", len(rn) == 1
      and rem[0] in rn[0]["subject"] and "order_admin.py refunded" in rn[0]["text"] and j["withdrawn"]["reminders"] == 1,
      ([m["subject"] for m in rn], j.get("withdrawn")))
m1 = len(H.Fake.emails)
c, j = get("/api/order", AUTH)
check("C8 a second run: no second reminder", not [m for m in mails_to(OWNER, m1) if "reminder" in m["subject"]]
      and j["withdrawn"]["reminders"] == 0, j.get("withdrawn"))
# events.py failing, or a purge_old that takes no arguments: the run goes on
_imp = C._import
C._import = lambda name: (_ for _ in ()).throw(RuntimeError("boom"))
rr = C._events(True, 10.0, print)
C._import = _imp
check("C9 events.py failing to import: logged, the run goes on", rr == {"error": "RuntimeError"}, rr)


class _E:
    @staticmethod
    def purge_old():
        return {"ok": True, "n": 1}


C._import = lambda name: _E
r_yes, r_dry = C._events(True, 10.0, print), C._events(False, 10.0, print)
C._import = _imp
check("C10 a purge_old without arguments: called on a real run, not on a dry run", r_yes == {"ok": True, "n": 1}
      and r_dry == {"skipped": "dry_run"}, (r_yes, r_dry))
per = C._period
check("C11 audit names: dates read the way the site writes them",
      per("2024-05-06")[0] == ts("2024-05-06T00:00:00") and per("2024-05")[1] == ts("2024-06-01T00:00:00")
      and per("20240506-x.json")[0] == ts("2024-05-06T00:00:00") and per("240506")[0] == ts("2024-05-06T00:00:00")
      and per("202405")[1] == ts("2024-06-01T00:00:00") and per("2405")[1] == ts("2024-06-01T00:00:00")
      and per("2024")[1] == ts("2025-01-01T00:00:00") and per("1790746842-x.json")[0] == 1790746842
      and per("101500-abcd.json") is None and per("undated") is None and per("2024-13-01") is None)
os.environ.pop("CRON_SECRET", None)
# the owner's list shows what waits for a digest, NEED ACTION first
fresh("store_r4_admin")
o1, k1, _ = paid_order("en", "adm@example.com")
W.NOTE_DAY_MAX, keep = 0, W.NOTE_DAY_MAX
withdraw(o1, k1, name="Adm", email="adm@example.com")
W.NOTE_DAY_MAX = keep
envs = dict(os.environ, STORE_LOCAL_DIR=STORE)
r = subprocess.run(ADMIN + ["withdrawals"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("C12 order_admin withdrawals lists the NEED ACTION statements with the refund due", r.returncode == 0
      and "NEED ACTION" in r.stdout and o1 in r.stdout and "REFUND" in r.stdout, r.stdout[-800:] + r.stderr[-400:])

# ======================================================================================== K. unpaid orders Stripe cannot vouch for
fresh("store_r4_kept")
now = time.time()


def unpaid_rec(days_old, sessions):
    t0 = now - days_old * 86400
    oid = time.strftime("%y%m%d", time.gmtime(t0)) + "-" + secrets.token_hex(8)
    rec = {"v": 1, "order": oid, "created_at": int(t0), "created": pay.iso(t0), "key_sha": "0" * 32, "lang": "en"}
    if sessions:
        rec.update(checkout={"session_id": sessions[0]}, sessions=sessions)
    write_json(f"orders/{oid}/order.json", rec)
    write_json(f"orders/{oid}/draft/eye_1.json", {"eye": 1})
    return oid


live_sid = "cs_live_" + "z" * 20
o40 = unpaid_rec(40, [live_sid])            # outside the 35-day window: only the kept mark keeps it in view
o28 = unpaid_rec(28, [live_sid])            # inside the window
onone = unpaid_rec(41, [])                  # kept once (Stripe did not answer), no session any more: deletable
write_json(f"cleanup/kept/{o40}.json", {"t": int(now) - 5 * 86400})
write_json(f"cleanup/kept/{onone}.json", {"t": int(now) - 5 * 86400})
write_json("cleanup/kept/260901-" + "d" * 16 + ".json", {"t": int(now) - 9 * 86400})   # its order is gone
os.environ["CRON_SECRET"] = "cron-" + "s" * 30
AUTH = {"Authorization": "Bearer " + os.environ["CRON_SECRET"], "User-Agent": "vercel-cron/1.0"}
m0 = len(H.Fake.emails)
c, j = get("/api/order", AUTH)
kn = [m for m in mails_to(OWNER, m0) if "could not be deleted" in m["subject"]]
check("K1 a live session and a test key (Stripe cannot vouch): both kept, the 28-day one now marked too", c == 200
      and exists(f"orders/{o40}/order.json") and exists(f"orders/{o28}/order.json") and exists(f"cleanup/kept/{o28}.json")
      and exists(f"cleanup/kept/{o40}.json"), (c, j.get("unpaid")))
check("K2 ONE owner note names both (25 days or more), with what to do", len(kn) == 1 and o40 in kn[0]["text"]
      and o28 in kn[0]["text"] and "order_admin.py erase" in kn[0]["text"] and live_sid in kn[0]["text"],
      [m["subject"] for m in kn])
check("K3 a kept order that has no session any more is deleted outside the window, its mark goes; a gone order's mark "
      "goes", not exists(f"orders/{onone}/order.json") and not exists(f"cleanup/kept/{onone}.json")
      and not exists("cleanup/kept/260901-" + "d" * 16 + ".json") and j["unpaid"]["kept_later"]["deleted"] == 1,
      j.get("unpaid"))
m1 = len(H.Fake.emails)
c, j = get("/api/order", AUTH)
check("K4 a second run the same day: no second note", c == 200 and not [m for m in mails_to(OWNER, m1)
                                                                       if "could not be deleted" in m["subject"]])
os.environ.pop("CRON_SECRET", None)

# ======================================================================================== hygiene
bad = []
for f in ("api/_lib/pay.py", "api/_lib/withdraw.py", "api/_lib/cleanup.py", "api/order.py", "api/checkout.py",
          "api/health.py", "api/stripe_webhook.py", "scripts/order_admin.py", "vercel.json"):
    tx = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in tx for ch in DASHES) or any(ord(ch) < 32 and ch not in "\n\t" for ch in tx) or "\r" in tx:
        bad.append(f)
check("H1 my files: no em/en dashes, no control characters, LF", not bad, bad)
allmail = json.dumps([m for m, _ in H.Fake.emails], ensure_ascii=False)
check("H2 no email of the last store carries a dash or a secret", not any(d in allmail for d in DASHES)
      and H.SK not in allmail and H.WHSEC not in allmail and H.RESEND not in allmail and LIVE_SK not in allmail)
fns = [f for f in os.listdir(H.API) if f.endswith(".py") and not f.startswith("_")]
check("H3 at most 12 Python functions (Hobby)", len(fns) <= 12, fns)

failed = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} passed" + (f"; FAILED: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
