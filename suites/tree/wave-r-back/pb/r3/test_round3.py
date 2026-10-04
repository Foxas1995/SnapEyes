# -*- coding: utf-8 -*-
"""Round 3 tests (paybackend fixer): the confirmation email's withdrawal link (withdrawal mode, never starts
making), the neutral receipt for statements that match no order (per-address limit, no links echoed, nothing about
any order), and the flood guards (no owner email per anonymous statement but one note a day plus a daily digest; a
separate ceiling for statements that match no order; proven statements never refused on it; slots taken before the
work; the clean-up's receipt retries capped so the deletions always run). Fake Stripe + Resend + legal pack
(../harness.py), local store folders, synthetic keys, the renderer stubbed. No network, no real key.
    python test_round3.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, json, time, base64, re, subprocess, secrets, threading, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__))
PB = os.path.dirname(HERE)
sys.path.insert(0, PB)
import harness as H
import socketserver
socketserver.TCPServer.request_queue_size = 512

stub = H.start_stub()
STORE = os.path.join(HERE, "store_r3")
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


def withdraw(o, k=None, name="Ana Tester", email="kunde@example.com", lang="en", **kw):
    b = {"action": "withdraw", "order": o, "name": name, "email": email, "lang": lang}
    if k:
        b["k"] = k
    b.update(kw)
    return post("/api/order", b)


def fresh(name):
    """A new store folder (today's counters start at zero), email and Stripe on."""
    global STORE
    STORE = os.path.join(HERE, name)
    H.setup_env(STORE, stub.server_address[1])
    H.Fake.emails.clear()
    H.Fake.fail_mail.clear()
    pay._LEGAL.update(pack=None, t=0.0)


def fake_master_eye(body):
    key = f"orders/{body['order']}/eye_{body['eye']}.jpg"
    if store.exists(key):
        return {"ok": True, "existing": True, "seconds": 0.1, "needs_review": False}
    store.put(key, base64.b64decode(body["crop"]), "image/jpeg", upsert=False)
    return {"ok": True, "existing": False, "seconds": 1.0, "needs_review": False}


H.MODS["order"].ME.master_eye = fake_master_eye
H.Fake.legal = PACK

# ======================================================================================== F1. the email's withdrawal link
fresh("store_r3")
n0 = len(H.Fake.emails)
oA, kA, _ = paid_order("en", "anna@example.com")
m = mails_to("anna@example.com", n0)
t, htm = (m[0]["text"], m[0].get("html") or "") if m else ("", "")
wl_en = f"https://snapeyes.com/order?o={oA}&k={kA}&withdraw=1&lang=en"
check("F1 EN confirmation carries the withdrawal-mode link of this order (text and html)", wl_en in t
      and wl_en.replace("&", "&amp;") in htm, t[:3000])
i_right = t.find("Your right of withdrawal")
check("F2 EN: the link sits in the withdrawal paragraph, after the statutory button words and before the texts",
      0 < i_right < t.find("“Withdraw from contract here”") < t.find(wl_en) < t.find("_" * 64), (i_right, t.find(wl_en)))
check("F3 EN: says the order page link starts making and the withdrawal link does not",
      "When you open it, we start making your artwork" in t and "without starting to make your file" in t
      and "by email to info@snapeyes.com or with the model withdrawal form" in t)
check("F4 EN: the normal order page link is still there, once, before the withdrawal link",
      t.count(f"https://snapeyes.com/order?o={oA}&k={kA}&lang=en") == 1
      and t.find(f"order?o={oA}&k={kA}&lang=en") < t.find(wl_en))
n0 = len(H.Fake.emails)
oB, kB, _ = paid_order("de", "berta@example.com")
m = mails_to("berta@example.com", n0)
t = m[0]["text"] if m else ""
wl_de = f"https://snapeyes.com/order?o={oB}&k={kB}&withdraw=1&lang=de"
check("F5 DE confirmation: withdrawal link, Schaltfläche words, Bestellseite starts making", wl_de in t
      and "Schaltfläche „Vertrag hier widerrufen“" in t and "ohne dass wir mit der Erstellung Ihrer Datei beginnen" in t
      and "Sobald Sie diese Seite öffnen, beginnen wir mit der Erstellung" in t
      and t.find("Ihr Widerrufsrecht\n") < t.find(wl_de), t[:3500])
check("F6 withdraw_url matches the page's withdrawHref query (o, k, withdraw=1, lang)",
      re.search(r"/order\?o=[a-z0-9-]+&k=[a-f0-9]{32}&withdraw=1&lang=(en|de)$", pay.withdraw_url(oA, kA, "en"))
      and pay.withdraw_url(oA, kA, "xx").endswith("&lang=en"))
wd_ts = open(os.path.join(H.REPO, "src", "order", "withdraw.ts"), encoding="utf-8").read()
check("F7 the order page reads ?withdraw=1 as its withdrawal mode (src/order/OrderApp.tsx)",
      "get('withdraw') === '1'" in open(os.path.join(H.REPO, "src", "order", "OrderApp.tsx"), encoding="utf-8").read()
      and "q.set('withdraw', '1')" in wd_ts)
# what the withdrawal-mode page asks for (status only) starts nothing: no making.json, the right stays
c, j = get(f"/api/order?o={oA}&k={kA}")
check("F8 the status the withdrawal form reads starts nothing (no making.json)", c == 200 and j["state"] == "paid"
      and not exists(f"orders/{oA}/making.json"), (c, j))
c, j = withdraw(oA, kA, name="Anna", email="anna@example.com")
check("F9 ... so the withdrawal from that page is effective", c == 200 and j["withdrawal"]["state"] == "withdrawn", (c, j))
envs = dict(os.environ, STORE_LOCAL_DIR=STORE)
r = subprocess.run(ADMIN + ["status", oB], capture_output=True, text=True, env=envs, encoding="utf-8")
check("F10 order_admin status prints the withdrawal link too", r.returncode == 0 and wl_de in r.stdout, r.stdout[-600:] + r.stderr[-400:])

# ======================================================================================== F2. neutral receipt
n0 = len(H.Fake.emails)
oR, kR, _ = paid_order("de", "rita@example.com")            # a real GERMAN order, paid with rita@
n1 = len(H.Fake.emails)
c1, j1 = withdraw(oR, None, name="Rita", email="rita.privat@example.org", lang="en")      # real order, other email
c2, j2 = withdraw("260101-" + "0" * 16, None, name="Rita", email="rita.other@example.org", lang="en")   # no such order
c3, j3 = withdraw(oR, "0" * 32, name="Rita", email="rita.third@example.org", lang="en")   # forged k, other email
check("N1 unmatched: 404 not_found, recorded, receipt sent", (c1, c2, c3) == (404, 404, 404)
      and all(j.get("recorded") is True and j["withdrawal"]["mail"] == "sent" for j in (j1, j2, j3)), (j1, j2, j3))
r1, r2 = mails_to("rita.privat@example.org", n1), mails_to("rita.other@example.org", n1)
check("N2 the chosen address gets one receipt each", len(r1) == 1 and len(r2) == 1, (len(r1), len(r2)))
norm = lambda x: re.sub(r"\d{1,2} \w+ \d{4}, \d\d:\d\d:\d\d UTC", "T", x.replace(oR, "O").replace("260101-" + "0" * 16, "O")
                        .replace("rita.privat@example.org", "E").replace("rita.other@example.org", "E"))
check("N3 real order vs no order: the receipts are the same word for word (nothing about the order leaks)",
      r1 and r2 and norm(r1[0]["text"]) == norm(r2[0]["text"]) and r1[0]["subject"] == r2[0]["subject"],
      (r1[0]["text"][:900] if r1 else "", r2[0]["text"][:900] if r2 else ""))
t = r1[0]["text"] if r1 else ""
check("N4 the receipt: statement text, time with seconds, the given order, the address; neutral wording; page language",
      W.STATEMENT["en"].format(order=oR) in t and pay.when_text(j1["withdrawal"]["at"], "en", seconds=True) in t
      and "Email for this receipt: rita.privat@example.org" in t and "could not match your statement" in t
      and "withdrawal link in it" in t and "Widerruf" not in t and "effective" not in t and "€" not in t
      and "refund" not in t.lower() and "SnapEyes" in r1[0]["subject"] and "html" in r1[0], t[:1500])
check("N5 the 404 replies are the same apart from ids and times", all(
      {k: v for k, v in j.items() if k not in ("withdrawal", "ms")} == {k: v for k, v in j1.items() if k not in ("withdrawal", "ms")}
      for j in (j2, j3)) and sorted(j1["withdrawal"]) == sorted(j2["withdrawal"]), (j1, j2))
owner = mails_to(OWNER, n1)
check("N6 the owner: one note at once (the day's first), no note per statement, no attacker text in subjects",
      len(owner) == 1 and "matched no order" in owner[0]["subject"] and "Rita" not in owner[0]["subject"]
      and "rita.privat@example.org" in owner[0]["text"], [x["subject"] for x in owner])
# links in the typed name and order text are never echoed; greetings stay neutral
n2 = len(H.Fake.emails)
evil = "Visit http://evil.example/p or www.evil.example and evil.example/x mail me x@evil.example"
c, j = withdraw("pay at https://evil.example/fee", None, name=evil, email="victim@example.net", lang="de")
m = mails_to("victim@example.net", n2)
tt, hh = (m[0]["text"], m[0].get("html") or "") if m else ("", "")
check("N7 no link from the typed name or order text reaches the receipt (text or html), German page: German receipt",
      c == 404 and m and "evil" not in tt and "evil" not in hh and "http" not in tt.replace("https://snapeyes.com", "")
      and "[...]" in tt and m[0]["subject"] == "Eingangsbestätigung Ihrer Widerrufserklärung bei SnapEyes"
      and "Guten Tag," in tt and "Hiermit widerrufe ich" in tt, tt[:1500])
check("N8 the stored statement keeps what was typed", any(evil in open(p, encoding="utf-8").read()
      for p in files_under("withdrawals") if not p.endswith(("_ack.json", "_note.json"))))
# per-address limit
n3 = len(H.Fake.emails)
codes = [withdraw(f"guess-{i}", None, name="X", email="same@example.net")[1]["withdrawal"]["mail"] for i in range(3)]
check("N9 at most 2 receipts a day to one address; the third statement is still recorded", codes == ["sent", "sent", "not_sent"]
      and len(mails_to("same@example.net", n3)) == 2, codes)
check("N10 plain(): names stay, links go", W.plain("J.R. Smith") == "J.R. Smith" and W.plain("Anna-Lena Müller") == "Anna-Lena Müller"
      and W.plain("Dr. Jūratė O'Neil") == "Dr. Jūratė O'Neil" and W.plain("go to evil.example now") == "go to [...] now"
      and W.plain("HTTPS://X.Y/z") == "[...]" and W.plain("a@b.cd") == "[...]" and W.plain("müller.de") == "[...]")
# the matched receipt uses the cleaned name too (W6 of the review: the order link's holder)
n4 = len(H.Fake.emails)
oM, kM, _ = paid_order("en", "mo@example.com")
withdraw(oM, kM, name="Your parcel: pay at http://evil.example/p", email="mo@example.com")
rm = [x for x in mails_to("mo@example.com", n4) if x["subject"].startswith("We received your withdrawal")]
check("N11 a matched receipt never echoes a link from the name either", rm and "evil" not in rm[0]["text"]
      and "Hello Your parcel: pay at [...]," in rm[0]["text"], rm[0]["text"][:400] if rm else "none")
# no receipt when Resend refuses for good; retried when busy, and the unmatched owner note is never queued
H.Fake.fail_mail[:] = [503]
n5 = len(H.Fake.emails)
c, j = withdraw("busy-order-1", None, name="B", email="busy@example.net")
due = os.listdir(local("withdrawdue")) if exists("withdrawdue") else []
check("N12 Resend busy: receipt pending and queued once", c == 404 and j["withdrawal"]["mail"] == "pending" and len(due) == 1, (j, due))
r = W.retry_due()
check("N13 the clean-up sends it; no owner note is sent one by one for it", r["sent"] == 1
      and len(mails_to("busy@example.net", n5)) == 1 and not [x for x in mails_to(OWNER, n5)], (r, [x["subject"] for x in mails_to(OWNER, n5)]))

# no_contract: no note at once, it goes into the digest
n6 = len(H.Fake.emails)
oU, kU, sidU = new_checkout("en")
c, j = withdraw(oU, kU, name="Uma", email="uma@example.com")
check("N14 an order never paid: 409, no receipt, no owner note at once", c == 409 and not mails_to("uma@example.com", n6)
      and not mails_to(OWNER, n6), (c, j, [x["subject"] for x in mails_to(OWNER, n6)]))
dg = sorted(os.listdir(local(f"cleanup/digest/{pay.day()}")))
check("N15 today's digest entries: u- for no match, n- for never paid, paths only", any(x.startswith("u-") for x in dg)
      and any(x.startswith("n-") for x in dg) and all(set(read_json(f"cleanup/digest/{pay.day()}/{x}")) == {"path"} for x in dg), dg)

# ======================================================================================== F3. flood guards
fresh("store_r3_flood")
vo, vk, _ = paid_order("en", "victim@example.com")
vq, vqk, _ = paid_order("en", "quinn@example.com")
m0 = len(H.Fake.emails)
t0 = time.time()
rs = [withdraw(f"order-{secrets.token_hex(4)}", None, name=f"Visit http://evil.example/{i}", email=f"a{i}@example.com")
      for i in range(W.DAY_MAX + 10)]
codes = [c for c, _ in rs]
own = mails_to(OWNER, m0)
check("S1 statements matching no order: DAY_MAX taken (404), the rest refused (503 withdraw_paused)",
      codes[:W.DAY_MAX] == [404] * W.DAY_MAX and set(codes[W.DAY_MAX:]) == {503}
      and rs[-1][1].get("reason") == "withdraw_paused", codes)
check("S2 owner emails for the whole flood: the day's first + the pause note (2), none per statement",
      len(own) == 2 and any("matched no order" in x["subject"] for x in own)
      and any("paused" in x["subject"] for x in own) and not any("NOT MATCHED" in x["subject"] for x in own),
      [x["subject"] for x in own])
stored = [p for p in files_under("withdrawals") if not p.endswith(("_ack.json", "_note.json"))]
check("S3 only DAY_MAX statements stored, refused slots given back", len(stored) == W.DAY_MAX
      and len([x for x in os.listdir(local(f"withdrawlog/{pay.day()}")) if x.startswith("u-")]) == W.DAY_MAX, len(stored))
c, j = withdraw(vo, vk, name="Real Customer", email="victim@example.com")
check("S4 after the flood a customer with the order link withdraws online (200 withdrawn)", c == 200
      and j["withdrawal"]["state"] == "withdrawn", (c, j))
c, j = withdraw(vq, None, name="Quinn", email="QUINN@example.com")
check("S5 ... and one without the link but with the payment email too", c == 200 and j["withdrawal"]["state"] == "withdrawn", (c, j))
emails_today = len(H.Fake.emails) - m0
check("S6 all emails of the flood day stay far below Resend's free 100 a day", emails_today <= W.DAY_MAX + 2 + 4, emails_today)

# W4 of the review: junk with the victim's order number cannot block the victim
fresh("store_r3_target")
vo, vk, _ = paid_order("en", "victim@example.com")
att = [withdraw(vo, None, email=f"wrong{i}@example.com")[0] for i in range(6)]
c, j = withdraw(vo, vk, name="Victim", email="victim@example.com")
check("S7 junk with the victim's order number: 3 taken, then 429; the victim with the link: 200", att == [404] * 3 + [429] * 3
      and c == 200 and j["withdrawal"]["state"] == "withdrawn", (att, c, j))
codes = [withdraw(vo, vk, name="Victim", email="victim@example.com")[0] for _ in range(5)]
check("S8 proven statements keep their own per-order limit (5 a day)", codes == [200] * 4 + [429], codes)

# slots before the work: a burst cannot pass the ceilings (storage latency as Supabase)
fresh("store_r3_race")
po, pk, _ = paid_order("en", "burst@example.com")
_lf, _put = store.list_folder, store.put


def slow_list(*a, **kw):
    time.sleep(0.25)
    return _lf(*a, **kw)


def slow_put(*a, **kw):
    time.sleep(0.15)
    return _put(*a, **kw)


store.list_folder, store.put = slow_list, slow_put
N = 80
with cf.ThreadPoolExecutor(N) as ex:
    burst = list(ex.map(lambda i: withdraw(f"burst-{i}-{secrets.token_hex(3)}", None, name="B", email=f"b{i}@example.com"), range(N)))
with cf.ThreadPoolExecutor(12) as ex:
    proven = list(ex.map(lambda i: withdraw(po, pk, name="P", email="burst@example.com", nonce=f"proven{i:04d}x"), range(12)))
store.list_folder, store.put = _lf, _put
stored = [p for p in files_under("withdrawals") if not p.endswith(("_ack.json", "_note.json"))]
check("S9 80 concurrent statements matching no order: at most DAY_MAX stored", len(stored) <= W.DAY_MAX
      and sum(1 for c, _ in burst if c == 404) == len(stored) and all(c in (404, 503) for c, _ in burst),
      (len(stored), sorted(set(c for c, _ in burst))))
ok = sum(1 for c, _ in proven if c == 200)
check("S10 12 concurrent proven statements for one order: at most ORDER_DAY_MAX taken, the rest 429",
      1 <= ok <= W.ORDER_DAY_MAX and all(c in (200, 429) for c, _ in proven), [c for c, _ in proven])

# the storage-failure fallback is capped per instance
fresh("store_r3_fallback")
real_put = store.put


def failing_put(path, *a, **kw):
    if path.startswith("withdrawlog/"):
        raise store.StorageError("injected")
    return real_put(path, *a, **kw)


store.put = failing_put
W._FALLBACK.update(day="", n=0)
m0 = len(H.Fake.emails)
codes = [withdraw(f"down-{i}", None, name="D", email=f"d{i}@example.com")[0] for i in range(W.FALLBACK_MAX + 5)]
store.put = real_put
fb = [x for x in mails_to(OWNER, m0) if "NOT stored" in x["subject"]]
check("S11 storage down: 503 each, the owner gets at most FALLBACK_MAX fallback emails, no typed text in the subject",
      set(codes) == {503} and len(fb) == W.FALLBACK_MAX and all(x["subject"] == "SnapEyes: a withdrawal statement arrived but was NOT stored" for x in fb),
      (codes, len(fb)))

# ======================================================================================== the daily clean-up
fresh("store_r3_cron")
os.environ["CRON_SECRET"] = "cron-" + "s" * 30
AUTH = {"Authorization": "Bearer " + os.environ["CRON_SECRET"], "User-Agent": "vercel-cron/1.0"}
# yesterday's statements for the digest (45: 40 listed, 5 counted), and a never-paid one
yd = pay.day(time.time() - 86400)
yt = int(time.time()) - 86400
for i in range(45):
    sid = f"{yd}000000{i:010x}"
    path = f"withdrawals/{time.strftime('%y%m', time.gmtime(yt))}/{sid}.json"
    store.put(path, store.json_bytes({"id": sid, "received_at": yt, "received": pay.iso(yt), "order_given": f"typed-{i} http://evil.example",
                                      "name": "N www.evil.example", "email": f"u{i}@example.com", "outcome": "unmatched"}),
              "application/json", upsert=True)
    store.put(f"cleanup/digest/{yd}/u-{sid}.json", store.json_bytes({"path": path}), "application/json", upsert=True)
store.put(f"orders/{yd}-00000000000000ee/withdrawal_x.json", store.json_bytes({"id": "x", "received_at": yt, "received": pay.iso(yt),
          "order_given": f"{yd}-00000000000000ee", "name": "Nc", "email": "nc@example.com", "outcome": "no_contract"}),
          "application/json", upsert=True)
store.put(f"cleanup/digest/{yd}/n-x.json", store.json_bytes({"path": f"orders/{yd}-00000000000000ee/withdrawal_x.json"}),
          "application/json", upsert=True)
# today's entries wait for tomorrow
withdraw("today-order", None, name="T", email="t@example.com")
m0 = len(H.Fake.emails)
c, j = get("/api/order", AUTH)
dg = [x for x in mails_to(OWNER, m0) if "withdrawal statements to check" in x["subject"]]
check("D1 the daily run sends ONE digest for yesterday: counts, 40 listed, the rest counted, no links echoed", c == 200
      and len(dg) == 1 and "(45 matched no order, 1 on unpaid orders)" in dg[0]["subject"]
      and dg[0]["text"].count("  received     ") == 40 and "more are not listed here" in dg[0]["text"]
      and "evil" not in dg[0]["text"] and j["digest"]["days"] == 1, (c, j, [x["subject"] for x in dg]))
check("D2 yesterday's entries are gone, today's wait", (not exists(f"cleanup/digest/{yd}")
      or not os.listdir(local(f"cleanup/digest/{yd}"))) and bool(os.listdir(local(f"cleanup/digest/{pay.day()}"))))
m1 = len(H.Fake.emails)
c, j = get("/api/order", AUTH)
check("D3 a second run sends no second digest", c == 200 and not [x for x in mails_to(OWNER, m1) if "to check" in x["subject"]], j)
# a queue of receipts Resend would not take cannot crowd out the deletions (W7 of the review)
fresh("store_r3_cron2")
os.environ["CRON_SECRET"] = "cron-" + "s" * 30
H.Fake.fail_mail[:] = [429] * 80
for i in range(W.DAY_MAX):
    withdraw(f"junk-{secrets.token_hex(4)}", None, name="x", email=f"j{i}@example.com")
due = os.listdir(local("withdrawdue"))
d3 = pay.day(time.time() - 3 * 86400)
uo, uk, _ = pay.new_order("en", order=f"{d3}-{secrets.token_hex(8)}")
draft(1, uo, uk)
rec = read_json(f"orders/{uo}/order.json")
rec["created_at"] -= 72 * 3600
store.put(f"orders/{uo}/order.json", store.json_bytes(rec), "application/json", upsert=True)
H.Fake.fail_mail[:] = [429] * 10000
_send = pay.send_mail


def slow_send(*a, **kw):
    time.sleep(0.8)
    return _send(*a, **kw)


pay.send_mail, L.BUDGET = slow_send, 40.0
t0 = time.time()
c, j = get("/api/order", AUTH)
el = time.time() - t0
pay.send_mail, L.BUDGET = _send, 52.0
H.Fake.fail_mail.clear()
check("D4 20 receipts queued while Resend refused: the run gives them at most RETRY_SECONDS, then the deletions run",
      len(due) == W.DAY_MAX and c == 200 and "unpaid" in j and not exists(f"orders/{uo}/order.json")
      and j["receipts"]["waiting"] < len(due) and j["more"] is True, (len(due), c, j, round(el, 1)))
r = W.retry_due()
check("D5 the next run sends what waited", r["sent"] >= 1 and r["waiting"] == 0, r)
m2 = len(H.Fake.emails)
r = W.retry_due()
check("D6 ... once", r == {"sent": 0, "waiting": 0, "dropped": 0} and len(H.Fake.emails) == m2, r)
# the owner's list
envs = dict(os.environ, STORE_LOCAL_DIR=STORE)
r = subprocess.run(ADMIN + ["withdrawals"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("D7 order_admin withdrawals lists the statements that matched no order", r.returncode == 0
      and f"{W.DAY_MAX} statement(s) that matched no order" in r.stdout and "j0@example.com" in r.stdout, r.stdout[-800:] + r.stderr[-400:])
r = subprocess.run(ADMIN + ["withdrawals", "--day", "2609"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("D8 withdrawals --day is checked", r.returncode != 0 and "YYMMDD" in (r.stderr + r.stdout))
r = subprocess.run(ADMIN + ["cleanup"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("D9 order_admin cleanup (dry run) still runs", r.returncode == 0 and "dry run" in r.stdout, r.stdout[-400:] + r.stderr[-400:])
os.environ.pop("CRON_SECRET", None)

# ======================================================================================== hygiene
bad = []
for f in ("api/_lib/pay.py", "api/_lib/withdraw.py", "api/_lib/cleanup.py", "api/order.py", "scripts/order_admin.py"):
    tx = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in tx for ch in DASHES) or any(ord(ch) < 32 and ch not in "\n\t" for ch in tx) or "\r" in tx:
        bad.append(f)
check("H1 my files: no em/en dashes, no control characters, LF", not bad, bad)
allmail = json.dumps([m for m, _ in H.Fake.emails], ensure_ascii=False)
check("H2 no email carries a dash or a secret", not any(d in allmail for d in DASHES) and H.SK not in allmail
      and H.WHSEC not in allmail and H.RESEND not in allmail)
fns = [f for f in os.listdir(H.API) if f.endswith(".py") and not f.startswith("_")]
check("H3 at most 12 Python functions (Hobby allows 12; api/admin.py is the 11th, wave q)", len(fns) <= 12, fns)

failed = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} passed" + (f"; FAILED: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
