# -*- coding: utf-8 -*-
"""Round 5 tests (wave r, role back): the withdrawal period's weekend and holiday rule (Regulation 1182/71 Art. 3(4),
§ 193 BGB; Lithuanian, German and (since 30efee7) Hungarian national holidays) and its time-zone bound checked against
zoneinfo; 409 no_order
and its code, and sells() staying true once a live payment was recorded; the admin log of an order
(ops/orderlog/<order>/) deleted with the order whenever it goes completely, kept with a paid order's records, and
the daily sweep of what is left; the daily reminder for paid orders held for review longer than 36 h (one owner note
per order). Fake Stripe + Resend + legal pack (../harness.py), local store folders, synthetic keys, the renderer
stubbed. No network, no real key.
    python test_round5.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, json, time, base64, re, shutil, subprocess, calendar, datetime, zoneinfo, secrets
HERE = os.path.dirname(os.path.abspath(__file__))
PB = os.path.dirname(HERE)
sys.path.insert(0, PB)
import harness as H

stub = H.start_stub()
STORE = os.path.join(HERE, "store_r5")
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
from _lib import ops

RESULTS = []
ADMIN = [sys.executable, os.path.join(H.REPO, "scripts", "order_admin.py")]
PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
OWNER = "info@snapeyes.com"
WHO = {"kind": "admin-v1", "exp": int(time.time()) + 3600}
ORDER = H.MODS["order"]


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


def new_draft(lang="en"):
    c, d = draft(1, lang=lang)
    assert c == 200, (c, d)
    return d["order"], d["k"]


def new_checkout(lang="en"):
    o, k = new_draft(lang)
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


def withdraw(o, k=None, name="Ana Tester", email="kunde@example.com", lang="en", **kw):
    b = {"action": "withdraw", "order": o, "name": name, "email": email, "lang": lang}
    if k:
        b["k"] = k
    b.update(kw)
    return post("/api/order", b)


def fresh(name):
    global STORE
    STORE = os.path.join(HERE, name)
    H.setup_env(STORE, stub.server_address[1])
    H.Fake.emails.clear()
    H.Fake.fail_mail.clear()
    H.Fake.legal = json.loads(json.dumps(PACK))
    H.Fake.legal_fail = 0
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
    pay._SOLD["yes"] = False


def fake_master_eye(body):
    key = f"orders/{body['order']}/eye_{body['eye']}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False}
    store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
    return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False}


COMPOSE = {"review": True, "n": 0}


def fake_master_compose(body):
    COMPOSE["n"] += 1
    key = f"orders/{body['order']}/artwork_{COMPOSE['n']}.jpg"
    store.put(key, b"artwork", "image/jpeg", upsert=True)
    return {"ok": True, "url": store.signed_url(key, 604800), "key": key, "width": 4096, "height": 4096, "bytes": 7,
            "style": body["style"], "layout": body["layout"], "count": len(body["keys"]),
            "needs_review": COMPOSE["review"]}


ORDER.ME.master_eye, ORDER.MC.master_compose = fake_master_eye, fake_master_compose
ts = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))
day = lambda s: datetime.date.fromisoformat(s)

# ======================================================================================== P. the period
# typed by hand from the published calendars (timeanddate, kalenderpedia, the Lithuanian Labour Code Art. 123)
LT = {2026: "01-01 02-16 03-11 04-05 04-06 05-01 06-24 07-06 08-15 11-01 11-02 12-24 12-25 12-26",
      2027: "01-01 02-16 03-11 03-28 03-29 05-01 06-24 07-06 08-15 11-01 11-02 12-24 12-25 12-26",
      2028: "01-01 02-16 03-11 04-16 04-17 05-01 06-24 07-06 08-15 11-01 11-02 12-24 12-25 12-26"}
DE = {2026: "01-01 04-03 04-06 05-01 05-14 05-25 10-03 12-25 12-26",
      2027: "01-01 03-26 03-29 05-01 05-06 05-17 10-03 12-25 12-26",
      2028: "01-01 04-14 04-17 05-01 05-25 06-05 10-03 12-25 12-26"}
# 30efee7 (Hungary selectable): withdraw.holidays() now also counts Hungary's national public holidays, for every order
# whatever its market (Mt. 102. § (1); the latest end anywhere is taken). Typed by hand from the published calendars, like
# the two tables above, and in the same way: without Whit Sunday (a Sunday, in no table; Easter Sunday is in LT). Against
# LT + DE exactly three days are new: 15 Mar, 20 Aug, 23 Oct (HU_NEW, pinned below), so a holiday that is added, dropped
# or moved later, in any of the three countries, still fails P1.
HU = {2026: "01-01 03-15 04-03 04-06 05-01 05-25 08-20 10-23 11-01 12-25 12-26",
      2027: "01-01 03-15 03-26 03-29 05-01 05-17 08-20 10-23 11-01 12-25 12-26",
      2028: "01-01 03-15 04-14 04-17 05-01 06-05 08-20 10-23 11-01 12-25 12-26"}
HU_NEW = "03-15 08-20 10-23"
want_ltde = {y: sorted({f"{y}-{md}" for md in (LT[y] + " " + DE[y]).split()}) for y in LT}
want = {y: sorted({f"{y}-{md}" for md in (LT[y] + " " + DE[y] + " " + HU[y]).split()}) for y in LT}
hu_new_ok = all(sorted(set(want[y]) - set(want_ltde[y])) == sorted(f"{y}-{md}" for md in HU_NEW.split()) for y in LT)
got = {y: sorted(d.isoformat() for d in W.holidays(y)) for y in LT}
check("P1 the holidays of 2026 to 2028 are exactly Lithuania's and Germany's national ones" " - 0930: plus Hungary's 15 Mar, 20 Aug and 23 Oct (30efee7)", got == want and hu_new_ok,
      ({y: (sorted(set(got[y]) ^ set(want[y]))) for y in LT}, "hu_new_ok", hu_new_ok))
EASTER = {2026: "04-05", 2027: "03-28", 2028: "04-16", 2029: "04-01", 2030: "04-21", 2031: "04-13", 2032: "03-28",
          2033: "04-17", 2034: "04-09", 2035: "03-25", 2038: "04-25", 2285: "03-22"}
check("P2 Easter by the computus matches the known dates (2026 to 2035, the latest 2038, the earliest 2285)",
      all(W.easter(y).isoformat() == f"{y}-{md}" for y, md in EASTER.items()),
      {y: W.easter(y).isoformat() for y in EASTER})
check("P3 working days: Saturday, Sunday, 3 Oct, 24 Dec (LT only), Good Friday (DE only) are not; a plain Tuesday is" " - 0930: Good Friday is a Hungarian holiday too (30efee7)",
      not any(W.working_day(day(s)) for s in ("2026-10-10", "2026-10-11", "2026-10-03", "2026-12-24", "2027-03-26"))
      and W.working_day(day("2026-10-13")))
for paid_s, last_s, why in (("2026-09-19T12:00:00", "2026-10-05", "a Saturday that is also 3 October"),
                            ("2026-10-03T12:00:00", "2026-10-19", "a Saturday"),
                            ("2026-10-04T12:00:00", "2026-10-19", "a Sunday"),
                            ("2026-04-30T10:00:00", "2026-05-15", "Ascension Day"),
                            ("2026-12-10T10:00:00", "2026-12-28", "24 Dec, then Christmas and a weekend"),
                            ("2027-03-12T10:00:00", "2027-03-30", "Good Friday, then Easter"),
                            ("2026-10-01T15:00:00", "2026-10-15", "a Thursday: not moved"),
                            # since 30efee7 the period also runs past Hungary's national days (P1 pins the table, these
                            # rows pin that period_end() moves the last day over them; the table is also what P10 to
                            # P12 measure with, so they could not catch a wrong table by themselves)
                            ("2026-10-09T12:00:00", "2026-10-26", "Fri 23 Oct, Hungary's national day, then Monday"),
                            ("2026-08-06T12:00:00", "2026-08-21", "Thu 20 Aug, Hungary's national day"),
                            ("2027-03-01T12:00:00", "2027-03-16", "Mon 15 Mar, Hungary's national day")):
    end, last = W.period_end(ts(paid_s))
    check(f"P4 paid {paid_s[:16]} UTC: the 14th day is {why}; the last day is {last_s}",
          last == last_s and end == ts(last_s + "T00:00:00") + 86400 + 4 * 3600, (last, end))

fresh("store_r5")
oP, kP, _ = paid_order("de", "pia@example.com")
recP, paidP = read_json(f"orders/{oP}/order.json"), read_json(f"orders/{oP}/paid.json")
A = lambda paid_s, now_s: W._assess_paid(oP, recP, dict(paidP, paid_at=ts(paid_s)), ts(now_s))
check("P5 paid Sat 3 Oct 2026: a statement on Mon 19 Oct 10:00 UTC is in time (was lapsed before: review A4)",
      A("2026-10-03T12:00:00", "2026-10-19T10:00:00")["outcome"] == "withdrawn"
      and A("2026-10-03T12:00:00", "2026-10-20T03:59:59")["outcome"] == "withdrawn")
late = A("2026-10-03T12:00:00", "2026-10-20T04:00:00")
check("P6 ... and from 20 Oct 04:00 UTC (the end of 19 Oct in the EU's westernmost zone) lapsed, last day 19 Oct",
      late["outcome"] == "lapsed" and late["reason"] == "period_over" and late["period_last_day"] == "2026-10-19", late)
check("P7 paid Sat 19 Sep 2026: a statement on Sun 4 Oct is in time (was lapsed with a Saturday last day: review D)",
      A("2026-09-19T12:00:00", "2026-10-04T12:00:00")["outcome"] == "withdrawn")
check("P8 the summer-time case (paysec A1): paid 10 Oct 2026 21:16 UTC, 25 Oct 23:30 Helsinki time is in time",
      A("2026-10-10T21:16:00", "2026-10-25T21:30:00")["outcome"] == "withdrawn")
check("P9 the overseas case (paysec A2): paid 1 Jan 2026 07:01 UTC, 15 Jan 23:00 in Guadeloupe (16 Jan 03:00 UTC) "
      "is in time", A("2026-01-01T07:01:00", "2026-01-16T03:00:00")["outcome"] == "withdrawn")

# against real time zones: never earlier than the true end in any EU zone, never more than 8 h after the latest one
ZONES = ["Atlantic/Azores", "Atlantic/Canary", "Europe/Lisbon", "Europe/Dublin", "Europe/Paris", "Europe/Berlin",
         "Europe/Vilnius", "Europe/Helsinki", "Europe/Athens", "Europe/Bucharest", "Asia/Nicosia", "America/Guadeloupe",
         "America/Martinique", "America/Cayenne", "Indian/Reunion", "Indian/Mayotte"]
TZ = [zoneinfo.ZoneInfo(z) for z in ZONES]


def true_end(t, tz):
    d = datetime.datetime.fromtimestamp(t, tz).date() + datetime.timedelta(days=14)
    while not W.working_day(d):
        d += datetime.timedelta(days=1)
    return datetime.datetime.combine(d + datetime.timedelta(days=1), datetime.time(0), tzinfo=tz).timestamp()


def plain_end(t, tz):
    """The statute without the weekend rule (the old code's idea), for the count below."""
    d = datetime.datetime.fromtimestamp(t, tz).date() + datetime.timedelta(days=15)
    return datetime.datetime.combine(d, datetime.time(0), tzinfo=tz).timestamp()


early, far, n, old_early = [], [], 0, 0
t = ts("2026-01-01T00:00:00")
while t < ts("2028-12-31T00:00:00"):
    end = W.period_end(t)[0]
    trues = [true_end(t, tz) for tz in TZ]
    n += 1
    if any(end < x for x in trues):
        early.append(t)
    if end > max(trues) + 8 * 3600:
        far.append(t)
    t += 3 * 3600 + 17 * 60
check(f"P10 {n} payment times 2026 to 2028 in {len(ZONES)} EU zones (overseas and summer time included): the end is "
      f"never before the true end", not early, [time.strftime('%Y-%m-%dT%H:%M', time.gmtime(x)) for x in early[:5]])
check("P11 ... and at most 8 h after the latest true end of any zone (the generosity stays bounded)", not far,
      [time.strftime('%Y-%m-%dT%H:%M', time.gmtime(x)) for x in far[:5]])
check("P12 ... and never before the plain statutory end (14th day, no weekend rule) either",
      all(W.period_end(x)[0] >= max(plain_end(x, tz) for tz in TZ)
          for x in range(ts("2026-03-20T00:00:00"), ts("2026-11-10T00:00:00"), 5 * 3600 + 11 * 60)))

pp = read_json(f"orders/{oP}/paid.json")
pp["paid_at"] = ts("2026-08-29T12:00:00")        # a Saturday: its 14th day, Sat 12 Sep, moves to Mon 14 Sep
write_json(f"orders/{oP}/paid.json", pp)
n0 = len(H.Fake.emails)
c, j = withdraw(oP, kP, name="Pia", email="pia@example.com", lang="de")
rm = mails_to("pia@example.com", n0)
on = [m for m in mails_to(OWNER, n0) if "withdrawal for order" in m["subject"]]
check("P13 a lapsed reply names the moved last day, the German receipt says the period ended on it, the owner's note too",
      c == 200 and j["withdrawal"]["state"] == "lapsed" and j["withdrawal"]["period_last_day"] == "2026-09-14"
      and rm and f"ist am {pay.date_text('2026-09-14', 'de')} abgelaufen" in rm[0]["text"]
      and on and "the last day was 2026-09-14" in on[0]["text"], (c, j, rm[0]["text"][:800] if rm else ""))
check("P14 the admin panel uses the same period (ops._period_over)",
      ops._period_over(pp) is True and ops._period_over(dict(pp, paid_at=time.time() - 3600)) is False)

# ======================================================================================== N. 409 no_order
fresh("store_r5_closed")
for k in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
    os.environ.pop(k, None)
n0 = len(H.Fake.emails)
c, j = withdraw("260101-" + "0" * 16, None, name="Anon", email="anon@example.com")
c2, j2 = withdraw("260101-" + "1" * 16, None, name="Anon", email="anon@example.com", lang="de")
check("N1 nothing sold here: 409 with the reason code no_order, recorded false, retry false, no withdrawal object",
      c == 409 and j.get("reason") == "no_order" and j.get("recorded") is False and j.get("retry") is False
      and "withdrawal" not in j and j.get("ok") is False and c2 == 409 and j2.get("reason") == "no_order", (c, j, c2, j2))
check("N2 ... nothing stored and nobody emailed", not exists("withdrawals") and not exists(f"withdrawlog/{pay.day()}")
      and len(H.Fake.emails) == n0)
src = "".join(open(os.path.join(H.API, *p), encoding="utf-8").read()
              for p in [("order.py",), ("checkout.py",), ("stripe_webhook.py",), ("health.py",)] +
              [("_lib", f) for f in os.listdir(os.path.join(H.API, "_lib")) if f.endswith(".py")])
check("N3 the code no_order is used by exactly one reply of the API (the page can map it to its own text)",
      len(re.findall(r"Answer\(\s*409,\s*\"no_order\"", src)) == 1
      and len(re.findall(r"Answer\(\s*[0-9]+,\s*\"no_order\"", src)) == 1
      and len(re.findall(r"(?:Answer\(|busy\()\s*(?:[0-9]+,\s*)?[\"']no_order[\"']", src)) == 1,
      re.findall(r".{40}no_order.{10}", src))

fresh("store_r5_sold")
oS, kS, sidS = new_checkout()
sess = dict(H.pay_session(sidS, "live@example.com"), livemode=True)
paidS, newS = pay.record_paid(oS, read_json(f"orders/{oS}/order.json"), sess, "test")
check("N4 the first LIVE payment recorded writes marks/sold_live.json", newS and exists(pay.SOLD_MARK)
      and read_json(pay.SOLD_MARK).get("order") == oS)
for k in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
    os.environ.pop(k, None)
pay._SOLD["yes"] = False                         # a new instance
c, j = withdraw("260101-" + "2" * 16, None, name="Typo", email="typo@example.com")
check("N5 keys removed after a live sale: a mistyped order number is still RECORDED (404 not_found, recorded true)",
      c == 404 and j.get("reason") == "not_found" and j.get("recorded") is True and files_under("withdrawals")
      and pay.sells() is True, (c, j))
fresh("store_r5_test")
oT, kT, _ = paid_order()
check("N6 a TEST-mode payment writes no sold mark (a preview with test orders can go back to no_order)",
      not exists(pay.SOLD_MARK) and exists(f"orders/{oT}/paid.json"))
os.environ.pop("STRIPE_SECRET_KEY", None)
real_exists = pay.store.exists


def boom(path, **kw):
    if path == pay.SOLD_MARK:
        raise store.StorageError("injected")
    return real_exists(path, **kw)


pay.store.exists = boom
got_sold = pay.ever_sold()
pay.store.exists = real_exists
check("N7 the sold mark unreadable (a storage error): counted as sold, so a statement is recorded rather than refused",
      got_sold is True and pay._SOLD["yes"] is False)
os.environ["STRIPE_SECRET_KEY"] = H.SK

# ======================================================================================== O. the admin log of an order
fresh("store_r5_log")
logs = lambda o: files_under(f"ops/orderlog/{o}")
audits = lambda o: [json.load(open(p, encoding="utf-8")) for p in files_under("ops/audit")
                    if json.load(open(p, encoding="utf-8")).get("order") == o]
oU, kU = new_draft()
ops.ACTIONS["link"]({"order": oU}, WHO)
had = len(logs(oU))
rec = read_json(f"orders/{oU}/order.json")
write_json(f"orders/{oU}/order.json", dict(rec, created_at=int(time.time()) - 30 * 3600))
r = pay.purge_unpaid(yes=True, names=[oU], markers=False)
check("O1 the unpaid purge deletes the order's admin log with its files", had == 1 and r["deleted"] == 1
      and not files_under(f"orders/{oU}") and not logs(oU), (had, r, logs(oU)))
oV, kV, _ = new_checkout()
ops.ACTIONS["link"]({"order": oV}, WHO)
ops.ACTIONS["clear_review"]({"order": oV}, WHO)
had = len(logs(oV))
res = ops.ACTIONS["delete_files"]({"order": oV, "confirm": oV}, WHO)
check("O2 the admin delete of an unpaid order: its admin log goes too, and the delete writes no new entry there "
      "(only the site-wide audit log has it)", had == 2 and res.get("result") == "deleted" and "orderlog" not in res
      and not files_under(f"orders/{oV}") and not logs(oV)
      and any(a["action"] == "delete_files" and a["ok"] for a in audits(oV)), (had, res, logs(oV)))
lab = ops.ACTIONS["lab_start"]({}, WHO)["order"]
store.put(f"orders/{lab}/eye_1.jpg", b"x", "image/jpeg", upsert=True)
write_json(f"ops/orderlog/{lab}/20260901101500-abcd1234.json", {"action": "render", "order": lab})
res = ops.ACTIONS["lab_delete"]({"order": lab}, WHO)
check("O3 deleting a lab test deletes its admin log", res.get("result") == "deleted" and not logs(lab)
      and not files_under(f"orders/{lab}") and not exists(f"ops/lab/{lab}.json"), (res, logs(lab)))
oW, kW, _ = paid_order("en", "keep@example.com")
ops.ACTIONS["link"]({"order": oW}, WHO)
res = ops.ACTIONS["delete_files"]({"order": oW, "confirm": oW}, WHO)
check("O4 a PAID order's files deleted on request: its records stay and so does its admin log (with a new entry)",
      res.get("result") == "deleted" and exists(f"orders/{oW}/paid.json") and exists(f"orders/{oW}/deleted.json")
      and len(logs(oW)) == 2, (res, logs(oW)))
pw = read_json(f"orders/{oW}/paid.json")
write_json(f"orders/{oW}/paid.json", dict(pw, paid_at=int(time.time()) - 400 * 86400))
os.remove(local(f"orders/{oW}/deleted.json"))
rx = pay.expire_paid(yes=True, names=[oW])
check("O5 the 12-month expiry keeps the admin log with the order record (privacy policy)", rx["expired"] == 1
      and exists(f"orders/{oW}/expired.json") and len(logs(oW)) == 2, (rx, logs(oW)))
ghost = "260101-" + "ab" * 8
try:
    ops.ACTIONS["link"]({"order": ghost}, WHO)
    c404 = None
except store.Answer as a:
    c404 = a.status
check("O6 an action on an order number that does not exist (404): audited site-wide, but no order log is started",
      c404 == 404 and not logs(ghost) and any(a["result"] == "not_found" for a in audits(ghost)), (c404, logs(ghost)))
oE, kE = new_draft()
ops.ACTIONS["link"]({"order": oE}, WHO)
envs = dict(os.environ, STORE_LOCAL_DIR=STORE)
r = subprocess.run(ADMIN + ["erase", oE, "--yes"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("O7 order_admin.py erase of an unpaid order deletes its admin log too", r.returncode == 0
      and not files_under(f"orders/{oE}") and not logs(oE), r.stdout[-600:] + r.stderr[-600:])
# the daily sweep
old, young = "20260101101500-aaaa0000.json", time.strftime("%Y%m%d%H%M%S", time.gmtime()) + "-bbbb0000.json"
orph, orph_y, lab_m = "260102-" + "cd" * 8, "260103-" + "ef" * 8, "lab-260104-0a0b0c0d"
lab_gone = "lab-260105-0e0f0a0b"
for o, n in ((orph, old), (orph_y, young), (oW, old), (lab_m, old), (lab_gone, old)):
    write_json(f"ops/orderlog/{o}/{n}", {"action": "link", "order": o})
write_json(f"ops/lab/{lab_m}.json", {"order": lab_m})
dry = C._orphan_logs(False, 0.0, print)
check("O8 the sweep's dry run counts the orphans and deletes nothing", dry["orders"] == 2 and logs(orph) and logs(lab_gone),
      dry)
res = C._orphan_logs(True, 0.0, print)
check("O9 the sweep deletes the log of an order of which nothing is left (an old id, a deleted lab test)",
      res["orders"] == 2 and not logs(orph) and not logs(lab_gone), res)
check("O10 ... and keeps a young one (grace), a paid order's (its record), a lab test with its marker",
      logs(orph_y) and len(logs(oW)) == 3 and logs(lab_m), (logs(orph_y), logs(oW), logs(lab_m)))
os.environ["CRON_SECRET"] = "cron-" + "s" * 30
AUTH = {"Authorization": "Bearer " + os.environ["CRON_SECRET"], "User-Agent": "vercel-cron/1.0"}
write_json(f"ops/orderlog/{orph}/{old}", {"action": "link", "order": orph})
c, j = get("/api/order", AUTH)
check("O11 the daily run sweeps too (orderlog in its reply)", c == 200 and isinstance(j.get("orderlog"), dict)
      and j["orderlog"].get("orders") == 1 and not logs(orph), (c, j))

# ======================================================================================== R. the review reminder
fresh("store_r5_review")
os.environ["CRON_SECRET"] = "cron-" + "s" * 30
AUTH = {"Authorization": "Bearer " + os.environ["CRON_SECRET"], "User-Agent": "vercel-cron/1.0"}
idx = lambda o: exists(f"cleanup/review/{o}.json")
reminders = lambda since, o=None: [m for m in mails_to(OWNER, since) if "reminder, order" in m["subject"]
                                   and (o is None or o in m["subject"])]
now = int(time.time())
oA, kA, _ = paid_order("en", "a@example.com")
ORDER._to_review(oA, 1, "render_rejected")
check("R1 a hold by the order page (order._to_review) writes the index", idx(oA) and exists(f"orders/{oA}/review.json"))
oB, kB, _ = paid_order("en", "b@example.com")
pay.hold_confirmation(oB, read_json(f"orders/{oB}/paid.json"), "failed")
check("R2 a held confirmation email (pay.mark_review) writes the index", idx(oB))
oC, kC, _ = paid_order("en", "c@example.com")
c1, j1 = post("/api/order", {"action": "make", "order": oC, "k": kC, "eye": 1})
COMPOSE["review"] = True
c2, j2 = post("/api/order", {"action": "compose", "order": oC, "k": kC})
check("R3 an artwork a check holds (order compose) writes the index", c1 == 200 and c2 == 200 and j2.get("state") == "review"
      and idx(oC), (c1, j1, c2, j2))
oD, kD, _ = paid_order("en", "d@example.com")
post("/api/order", {"action": "make", "order": oD, "k": kD, "eye": 1})
COMPOSE["review"] = False
post("/api/order", {"action": "compose", "order": oD, "k": kD})
check("R4 an artwork that is not held writes no index", not idx(oD) and exists(f"orders/{oD}/delivery.json"))
COMPOSE["review"] = True
store.put(f"orders/{oD}/release.json", b"{}", "application/json", upsert=True)
res = ops.ACTIONS["recompose"]({"order": oD}, WHO)
check("R5 the admin recompose that makes a new held artwork writes the index", res.get("held") is True and idx(oD), res)
oE, kE, _ = paid_order("en", "e@example.com")
pay.mark_review(oE, "render_rejected", 1)
write_json(f"orders/{oE}/withdrawn.json", {"t": now})
oF, kF, _ = paid_order("en", "f@example.com")
pay.mark_review(oF, "draft_missing", 1)
os.remove(local(f"orders/{oF}/review.json"))       # the owner cleared it
# ages: A 37 h (review.json), B 10 h, C 40 h (the held artwork), D 2 h, E and F old
for o, h in ((oA, 37), (oB, 10), (oE, 50)):
    rv = read_json(f"orders/{o}/review.json")
    write_json(f"orders/{o}/review.json", dict(rv, t=now - h * 3600))
dl = read_json(f"orders/{oC}/delivery.json")
write_json(f"orders/{oC}/delivery.json", dict(dl, created_at=now - 40 * 3600))
n0 = len(H.Fake.emails)
dry = C._reviews(False, 0.0, print)
check("R6 the dry run: A and C would be reminded, E and F cleared, nothing sent or removed",
      dry["reminded"] == 2 and dry["cleared"] == 2 and dry["held"] == 4 and not reminders(n0)
      and all(idx(o) for o in (oA, oB, oC, oD, oE, oF)), dry)
res = C._reviews(True, 0.0, print)
rA, rC = reminders(n0, oA), reminders(n0, oC)
check("R7 one reminder each for A (held 37 h) and C (artwork held 40 h), none for B (10 h) and D (2 h)",
      res["reminded"] == 2 and len(reminders(n0)) == 2 and len(rA) == 1 and len(rC) == 1, (res, [m["subject"] for m in reminders(n0)]))
check("R8 the reminders say why, how long, the 48 h promise and what to do",
      rA and "render_rejected" in rA[0]["text"] and "48 hours" in rA[0]["text"] and "37 hours" in rA[0]["text"]
      and f"clear-review {oA}" in rA[0]["text"] and rC and f"release {oC}" in rC[0]["text"]
      and f"status {oC}" in rC[0]["text"], (rA[0]["text"] if rA else "", rC[0]["text"] if rC else ""))
check("R9 the index: reminded A and C, withdrawn E and cleared F go; B and D stay (still waiting)",
      not idx(oA) and not idx(oC) and not idx(oE) and not idx(oF) and idx(oB) and idx(oD)
      and exists(f"orders/{oA}/note_review_late.json"), res)
n1 = len(H.Fake.emails)
C._reviews(True, 0.0, print)
check("R10 a second run sends nothing", not reminders(n1))
rv = read_json(f"orders/{oB}/review.json")
write_json(f"orders/{oB}/review.json", dict(rv, t=now - 37 * 3600))
ORDER._to_review(oA, 1, "render_rejected")          # A is held again: still one reminder per order
rv = read_json(f"orders/{oA}/review.json")
write_json(f"orders/{oA}/review.json", dict(rv, t=now - 40 * 3600))
n2 = len(H.Fake.emails)
c, j = get("/api/order", AUTH)
rB = reminders(n2, oB)
check("R11 the daily run (GET /api/order, cron): B now reminded (resend-mail), A not again, reviews in the reply",
      c == 200 and isinstance(j.get("reviews"), dict) and len(rB) == 1 and f"resend-mail {oB}" in rB[0]["text"]
      and not reminders(n2, oA) and not idx(oA) and not idx(oB), (c, j.get("reviews"), [m["subject"] for m in reminders(n2)]))
bad = [m for m in reminders(0) if any(ch in m["text"] + m["subject"] for ch in (chr(0x2013), chr(0x2014)))]
check("R12 no em or en dash in the reminders", not bad)

# ======================================================================================== the files
DASH = (chr(0x2013), chr(0x2014))
own = ["api/_lib/withdraw.py", "api/_lib/cleanup.py", "api/_lib/pay.py", "api/_lib/ops.py", "api/order.py", "api/admin.py"]
txt = {f: open(os.path.join(H.REPO, *f.split("/")), encoding="utf-8").read() for f in own}
check("F1 my files: no em or en dash, no control character", all(
      not any(ch in s for ch in DASH) and not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", s) for s in txt.values()))

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
sys.exit(1 if fails else 0)
