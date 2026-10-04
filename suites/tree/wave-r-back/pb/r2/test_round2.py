# -*- coding: utf-8 -*-
"""Round 2 tests (paybackend): the order confirmation email as the contract on a durable medium, the order's own
language in Stripe's links and the emails, the online withdrawal function, and the daily clean-up (unpaid,
withdrawn, 12-month expiry, receipts, lock, time box, cron entry). Fake Stripe + Resend + legal pack
(../harness.py), local store folders, synthetic keys, the renderer stubbed. No network, no real key.
    python test_round2.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, io, json, time, base64, re, subprocess, calendar
HERE = os.path.dirname(os.path.abspath(__file__))
PB = os.path.dirname(HERE)
sys.path.insert(0, PB)
import harness as H

stub = H.start_stub()
STORE = os.path.join(HERE, "store_r2")
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


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:700]}"), flush=True)


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


def local(path):
    return os.path.join(STORE, *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    store.put(path, store.json_bytes(obj), "application/json", upsert=True)


def exists(path):
    return os.path.exists(local(path))


SMALL = H.jpeg_b64(256, 1)


def draft(eye, order=None, k=None, lang="en"):
    b = {"action": "draft", "eye": eye, "crop": SMALL, "preview": SMALL, "pad": 1.12, "lang": lang, "ref": f"e{eye}",
         "ticket": H.fresh_ticket() if order is None else L.mint_ticket("work")}
    if order:
        b.update(order=order, k=k)
    return post("/api/order", b)


def checkout(order, k, eyes=1, style="studio_black", lang="en", names="", title=""):
    return post("/api/checkout", {"order": order, "k": k, "eyes": eyes, "style": style, "names": names,
                                  "title": title, "lang": lang, "consent_digital": True})


def sid_of(order):
    return read_json(f"orders/{order}/order.json")["checkout"]["session_id"]


def new_checkout(lang="en", eyes=1, style="studio_black", names="", title=""):
    c, d = draft(1, lang=lang)
    o, k = d["order"], d["k"]
    for e in range(2, eyes + 1):
        draft(e, o, k, lang=lang)
    c, co = checkout(o, k, eyes, style, lang, names, title)
    assert c == 200, (c, co)
    return o, k, sid_of(o)


def paid_order(lang="en", email="kunde@example.com", eyes=1, style="studio_black", names="", title="", send_hook=True):
    o, k, sid = new_checkout(lang, eyes, style, names, title)
    sess = H.pay_session(sid, email)
    res = hook(sess) if send_hook else None
    return o, k, sid, res


def mails_to(addr, since=0):
    return [m for m, _ in H.Fake.emails[since:] if m["to"] == [addr]]


def fresh_pack(pack=None):
    H.Fake.legal = json.loads(json.dumps(pack or PACK))
    pay._LEGAL.update(pack=None, t=0.0)


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


def old_checkout(days_ago, lang="en"):
    """An order whose id carries an earlier day (the daily run lists order folders by that day), checked out."""
    import secrets as _s
    d = pay.day(time.time() - days_ago * 86400)
    # a real order only ever gets the day it is made, so an earlier run may have finished that day already
    store.delete(f"cleanup/done_unpaid/{d}.json")
    o, k, _ = pay.new_order(lang, order=f"{d}-{_s.token_hex(8)}")
    c, d = draft(1, o, k, lang=lang)
    assert c == 200, (c, d)
    c, co = checkout(o, k, 1, "studio_black", lang)
    assert c == 200, (c, co)
    return o, k, sid_of(o)


def status(o, k):
    return get(f"/api/order?o={o}&k={k}")


def withdraw(o, k=None, name="Ana Tester", email="kunde@example.com", lang="en", **kw):
    b = {"action": "withdraw", "order": o, "name": name, "email": email, "lang": lang}
    if k:
        b["k"] = k
    b.update(kw)
    return post("/api/order", b)


fresh_pack()

# ======================================================================================== A. the confirmation email
n0 = len(H.Fake.emails)
oA, kA, sidA, (c, j) = paid_order("en", "anna@example.com", eyes=2, style="celestial_gold", names="Anna & Ben")
m = mails_to("anna@example.com", n0)
check("A1 webhook 200, one confirmation email", c == 200 and j.get("mail") == "sent" and len(m) == 1, (c, j, len(m)))
m = m[0]
t, htm = m["text"], m.get("html") or ""
paid = read_json(f"orders/{oA}/paid.json")
rec = read_json(f"orders/{oA}/order.json")
check("A2 subject names the order", m["subject"] == f"Your SnapEyes order {oA}: order confirmation", m["subject"])
check("A3 order page link in the order's language (lang=en)", f"https://snapeyes.com/order?o={oA}&k={kA}&lang=en" in t, t[:600])
check("A4 seller: company, code, address, email (from the legal pack)",
      'MB "Portretizuokis", company code 305605052' in t and "Gedimino g. 22A-14, LT-44319 Kaunas, Lithuania" in t
      and "Email: info@snapeyes.com" in t and "Represented by: Mantas Bakšys" in t and "Phone:" not in t, t[-9000:-7000])
check("A5 what was bought: eyes, style, layout, names, digital file, no print",
      "SnapEyes iris artwork, 2 eyes, Celestial Gold, 4096 px digital file, layout Side by side" in t
      and "Names on the artwork: Anna & Ben" in t and "no print and no frame are shipped" in t, t[:2500])
check("A6 final price and no VAT", "Price: €39.97. This is the final price: we are not registered for VAT, so no VAT is "
      "charged." in t, t[:2500])
check("A7 consent: exact recorded text and time", pay.CONSENT_TEXT["en"] in t and "“" + pay.CONSENT_TEXT["en"] + "”" in t
      and pay.when_text(paid["consent"]["at"], "en") in t and "you ticked this box" in t, t[:3000])
check("A8 consent text kept with the order and the payment", rec["checkout"]["consent"]["text"] == pay.CONSENT_TEXT["en"]
      and paid["consent"]["text"] == pay.CONSENT_TEXT["en"] and paid["consent"]["version"] == pay.CONSENT_VERSION
      and paid["consent"]["lang"] == "en", (rec["checkout"]["consent"], paid["consent"]))
check("A9 withdrawal information and model form in full", PACK["docs"]["en"]["withdrawal"]["text"] in t
      and "Model withdrawal form" in t and "Withdraw from contract here" in t, len(t))
check("A10 terms of sale in full, with their link", PACK["docs"]["en"]["terms"]["text"] in t
      and PACK["docs"]["en"]["terms"]["url"] in t, len(t))
check("A11 HTML part: same content, escaped, no script", htm.startswith("<!doctype html>") and 'lang="en"' in htm
      and "Anna &amp; Ben" in htm and "<script" not in htm.lower() and f"lang=en" in htm
      and "Model withdrawal form" in htm, htm[:400])
check("A12 no em/en dashes in either part", not any(d in t or d in htm for d in DASHES))
check("A13 the owner note is separate and carries no customer link key", all(kA not in x["text"] for x in mails_to("info@snapeyes.com", n0)))
md = read_json(f"orders/{oA}/mail_delivery.json")
check("A14 mail_delivery.json: sent, with the legal version and consent version", md["state"] == "sent"
      and md["legal"] == PACK["updated"] and md["consent"] == pay.CONSENT_VERSION, md)

# German
n0 = len(H.Fake.emails)
oB, kB, sidB, (c, j) = paid_order("de", "berta@example.com", eyes=1, style="deep_nebula", names="Jūratė")
m = mails_to("berta@example.com", n0)[0]
t = m["text"]
check("A15 DE subject", m["subject"] == f"Ihre SnapEyes-Bestellung {oB}: Bestellbestätigung", m["subject"])
check("A16 DE content: link lang=de, seller, price, no VAT, consent quote, withdraw button, texts",
      f"&k={kB}&lang=de" in t and "MB „Portretizuokis“, Unternehmenscode 305605052" in t and "Litauen" in t
      and "Preis: 24,97 €. Das ist der Endpreis: Wir sind nicht umsatzsteuerlich registriert" in t
      and "„" + pay.CONSENT_TEXT["de"] + "“" in t and "Vertrag hier widerrufen" in t and "Uhr UTC" in t
      and PACK["docs"]["de"]["withdrawal"]["text"] in t and PACK["docs"]["de"]["terms"]["text"] in t
      and "SnapEyes-Iris-Kunstwerk, 1 Auge, Deep Nebula" in t, t[:3000])
check("A17 DE HTML lang=de", 'lang="de"' in (m.get("html") or ""))

# representative and phone, once the owner sets them
pk = json.loads(json.dumps(PACK))
pk["seller"].update(representative="Mantas Test", phone="+370 600 00000")
fresh_pack(pk)
n0 = len(H.Fake.emails)
oC, kC, sidC, _ = paid_order("en", "carl@example.com")
t = mails_to("carl@example.com", n0)[0]["text"]
check("A18 representative and phone appear when set", "Represented by: Mantas Test" in t and "Phone: +370 600 00000" in t,
      t[-9500:-8000])
fresh_pack()

# the legal texts cannot be read: nothing is sent, nothing is made, Stripe retries, the page waits
H.Fake.legal_fail = 10 ** 6
pay._LEGAL.update(pack=None, t=0.0)
n0 = len(H.Fake.emails)
oD, kD, sidD, (c, j) = paid_order("en", "dora@example.com")
check("A19 legal texts unreadable: webhook 503 mail_retry, no confirmation sent", c == 503 and j.get("reason") == "mail_retry"
      and not mails_to("dora@example.com", n0) and not exists(f"orders/{oD}/mail_delivery.json"), (c, j))
c, j = status(oD, kD)
check("A20 status: pending, waiting_for confirmation_email", c == 200 and j["state"] == "pending"
      and j.get("waiting_for") == "confirmation_email", (c, j))
c, j = make(oD, kD)
check("A21 make: 402 confirming, nothing rendered", c == 402 and j.get("reason") == "confirming"
      and not any(o == oD for o, _ in renders), (c, j))
pd = read_json(f"orders/{oD}/paid.json")
pd["paid_at"] -= 1200
write_json(f"orders/{oD}/paid.json", pd)
c, j = status(oD, kD)
slow = [x for x in mails_to("info@snapeyes.com", n0) if "still waits for its confirmation email" in x["subject"]]
check("A22 after 15 minutes the owner is told once, naming the legal texts", len(slow) == 1
      and "/legal/order-mail.json" in slow[0]["text"], [x["subject"] for x in mails_to("info@snapeyes.com", n0)])
c, j = status(oD, kD)
slow = [x for x in mails_to("info@snapeyes.com", n0) if "still waits" in x["subject"]]
check("A23 ... only once", len(slow) == 1, len(slow))
H.Fake.legal_fail = 0
c, j = status(oD, kD)
check("A24 texts back: the status call sends it, state paid", c == 200 and j["state"] == "paid"
      and len(mails_to("dora@example.com", n0)) == 1, (c, j))
c, j = make(oD, kD)
check("A25 make now renders", c == 200 and j.get("made") is True, (c, j))
check("A26 making.json records when making began, after the confirmation", exists(f"orders/{oD}/making.json")
      and read_json(f"orders/{oD}/making.json")["t"] >= read_json(f"orders/{oD}/mail_delivery.json")["t"]
      and read_json(f"orders/{oD}/making.json")["confirmation_at"] == read_json(f"orders/{oD}/mail_delivery.json")["t"])

# a cached pack is used when a fresh fetch fails; a stale one (older than a day) is not
H.Fake.legal_fail = 10 ** 6
pay._LEGAL["t"] = time.time() - pay.LEGAL_CACHE - 5
check("A27 a pack fetched within the day is used when the site does not answer", pay.legal_pack() is not None)
pay._LEGAL["t"] = time.time() - pay.LEGAL_STALE - 5
check("A28 an older one is not", pay.legal_pack() is None)
H.Fake.legal_fail = 0
bad = json.loads(json.dumps(PACK))
bad["docs"]["de"]["terms"]["text"] = "short"
fresh_pack(bad)
check("A29 a pack with a missing text is refused", pay.legal_pack() is None)
fresh_pack()

# no consent recorded: nothing to confirm, the order is held for the owner
oE, kE, sidE, _ = paid_order("en", "eve@example.com", send_hook=False)
sess = H.Fake.sessions[sidE]
sess["metadata"].pop("consent_version", None)
recE = read_json(f"orders/{oE}/order.json")
recE["checkout"]["consent"]["version"] = "1999-01-01.0"
write_json(f"orders/{oE}/order.json", recE)
c, j = hook(sess)
check("A30 no consent recorded: 200, held for review, no confirmation", c == 200 and j.get("mail") == "no_consent"
      and read_json(f"orders/{oE}/review.json")["reason"] == "confirmation_email_no_consent", (c, j))

# the email quotes the text the customer ticked, even after CONSENT_TEXT changed
old = dict(pay.CONSENT_TEXT)
oF, kF, sidF, _ = paid_order("en", "fay@example.com", send_hook=False)
pay.CONSENT_TEXT["en"] = "A changed consent text."
n0 = len(H.Fake.emails)
c, j = hook(H.Fake.sessions[sidF])
t = mails_to("fay@example.com", n0)[0]["text"]
check("A31 the recorded text is quoted, not the current one", old["en"] in t and "A changed consent text." not in t)
pay.CONSENT_TEXT.update(old)

# ======================================================================================== B. the order's language
H.Fake.creates.clear()
oG, kG, sidG = new_checkout("en")
p = H.Fake.creates[-1][0]
check("B1 English order: success and cancel links say lang=en", p["success_url"].endswith(f"&k={kG}&lang=en&s={{CHECKOUT_SESSION_ID}}")
      and p["cancel_url"] == f"https://snapeyes.com/try?checkout=cancelled&o={oG}&lang=en" and p["locale"] == "en", p)
oH, kH, sidH = new_checkout("de")
p = H.Fake.creates[-1][0]
check("B2 German order: lang=de", "&lang=de&s=" in p["success_url"] and p["cancel_url"].endswith("&lang=de")
      and p["locale"] == "de", p)
check("B3 order_url always carries the language", pay.order_url("abcd-1", "k" * 32, "en").endswith("&lang=en")
      and pay.order_url("abcd-1", "k" * 32, "xx").endswith("&lang=en") and pay.order_url("abcd-1", "k" * 32, "de").endswith("&lang=de"))
s1, t1, h1 = pay.ready_mail(oA, read_json(f"orders/{oA}/paid.json"), kA)
s2, t2, h2 = pay.ready_mail(oB, read_json(f"orders/{oB}/paid.json"), kB)
check("B4 ready email in the order's language, with html", s1 == "Your SnapEyes artwork is ready" and "&lang=en" in t1
      and s2 == "Ihr SnapEyes-Kunstwerk ist fertig" and "&lang=de" in t2 and 'lang="de"' in h2, (s1, s2))

# ======================================================================================== C. withdrawal
# C1 paid, confirmation sent, nothing made: effective
n0 = len(H.Fake.emails)
oW, kW, sidW, _ = paid_order("en", "wanda@example.com", eyes=2, style="supernova")
c, j = withdraw(oW, kW, name="Wanda Test", email="wanda.receipt@example.com")
w = j.get("withdrawal") or {}
check("C1 effective: 200, state withdrawn, amount, refund due, receipt sent", c == 200 and w.get("state") == "withdrawn"
      and w.get("effective") is True and w.get("amount") == 3997 and w.get("refund") == "due" and w.get("mail") == "sent"
      and isinstance(w.get("at"), int) and w.get("already") is False, (c, j))
stmts = [f for f in os.listdir(local(f"orders/{oW}")) if re.fullmatch(r"withdrawal_[0-9a-f]+\.json", f)]
st = read_json(f"orders/{oW}/{stmts[0]}") if stmts else {}
check("C2 the statement is stored: name, email, time, text, outcome", len(stmts) == 1 and st["name"] == "Wanda Test"
      and st["email"] == "wanda.receipt@example.com" and st["received_at"] == w["at"] and st["verified"] == "link"
      and st["text"] == W.STATEMENT["en"].format(order=oW) and st["outcome"] == "withdrawn"
      and st["reason"] == "nothing_made", st)
check("C3 withdrawn.json and the clean-up mark", exists(f"orders/{oW}/withdrawn.json") and exists(f"cleanup/withdrawn/{oW}.json"))
rc = mails_to("wanda.receipt@example.com", n0)
check("C4 receipt: to the given address, content, date and time, refund", len(rc) == 1
      and rc[0]["subject"] == f"We received your withdrawal: SnapEyes order {oW}"
      and pay.when_text(w["at"], "en", seconds=True) in rc[0]["text"] and "Wanda Test" in rc[0]["text"]
      and W.STATEMENT["en"].format(order=oW) in rc[0]["text"] and "€39.97" in rc[0]["text"]
      and "within 14 days" not in rc[0]["text"] and "by " in rc[0]["text"] and "html" in rc[0], rc)
on = [x for x in mails_to("info@snapeyes.com", n0) if "withdrawal for order" in x["subject"]]
check("C5 owner note: refund, amount, payment", len(on) == 1 and "WITHDRAWN, refund 39.97 EUR" in on[0]["subject"]
      and "REFUND 39.97 EUR" in on[0]["text"], [x["subject"] for x in on])
c, j = status(oW, kW)
check("C6 status: state withdrawn, withdrawal view without personal data", c == 200 and j["state"] == "withdrawn"
      and j["withdrawal"]["state"] == "withdrawn" and "email" not in j["withdrawal"] and "name" not in j["withdrawal"]
      and "download" not in j, (c, j))
c1, j1 = make(oW, kW)
c2, j2 = post("/api/order", {"action": "compose", "order": oW, "k": kW})
check("C7 make and compose: 409 withdrawn, nothing rendered", c1 == 409 and j1.get("reason") == "withdrawn"
      and c2 == 409 and j2.get("reason") == "withdrawn" and not any(o == oW for o, _ in renders), (c1, j1, c2, j2))
c, j = withdraw(oW, kW, name="Wanda Test", email="wanda.receipt@example.com")
w2 = j.get("withdrawal") or {}
check("C8 a second statement: recorded too, already, first date named", c == 200 and w2.get("already") is True
      and w2.get("state") == "withdrawn" and len([f for f in os.listdir(local(f"orders/{oW}"))
                                                  if re.fullmatch(r"withdrawal_[0-9a-f]+\.json", f)]) == 2
      and "We had already received your withdrawal" in mails_to("wanda.receipt@example.com", n0)[-1]["text"], (c, j))

# C9 the same statement again with its nonce: one statement, one receipt
n0 = len(H.Fake.emails)
oN, kN, sidN, _ = paid_order("de", "nina@example.com")
c, j = withdraw(oN, kN, name="Nina", email="nina@example.com", lang="de", nonce="abcdefgh1234")
c2, j2 = withdraw(oN, kN, name="Nina", email="nina@example.com", lang="de", nonce="abcdefgh1234")
check("C9 nonce: the same id, one receipt, the repeat says already", c == 200 and c2 == 200
      and j["withdrawal"]["id"] == j2["withdrawal"]["id"] and j2["withdrawal"]["already"] is True
      and len(mails_to("nina@example.com", n0)) == 2, (j, j2, len(mails_to("nina@example.com", n0))))
rcd = [x for x in mails_to("nina@example.com", n0) if x["subject"].startswith("Eingangsbestätigung")]
check("C10 German receipt", len(rcd) == 1 and rcd[0]["subject"] == f"Eingangsbestätigung Ihres Widerrufs: SnapEyes-Bestellung {oN}"
      and "Ihr Widerruf ist wirksam" in rcd[0]["text"] and "Uhr UTC" in rcd[0]["text"]
      and W.STATEMENT["de"].format(order=oN) in rcd[0]["text"], rcd)

# C11 making began after the consent and the confirmation: lapsed, recorded, answered honestly
n0 = len(H.Fake.emails)
oL, kL, sidL, _ = paid_order("en", "lars@example.com", eyes=2)
make(oL, kL, 1)
c, j = withdraw(oL, kL, name="Lars", email="lars@example.com")
w = j.get("withdrawal") or {}
check("C11 lapsed: 200, effective false, reason making_began, times named", c == 200 and w.get("state") == "lapsed"
      and w.get("effective") is False and w.get("reason") == "making_began" and w.get("began_at")
      and w.get("confirmation_at") and w.get("consent_at"), (c, j))
check("C12 lapsed: order not stopped, make goes on", not exists(f"orders/{oL}/withdrawn.json") and make(oL, kL, 2)[0] == 200)
rl = [x for x in mails_to("lars@example.com", n0) if x["subject"].startswith("We received your withdrawal")]
check("C13 lapsed receipt: reason, the three facts, personal look, defect rights", len(rl) == 1
      and "had therefore already ended" in rl[0]["text"] and "order confirmation email of" in rl[0]["text"]
      and "we started making your file on" in rl[0]["text"] and "look at your statement personally" in rl[0]["text"]
      and "defective file" in rl[0]["text"], rl)
on = [x for x in mails_to("info@snapeyes.com", n0) if "withdrawal for order" in x["subject"]]
check("C14 owner note asks for a look", len(on) == 1 and "the right had ended, please look" in on[0]["subject"], on)
c, j = status(oL, kL)
check("C15 status keeps its state and shows the lapsed statement", j["state"] in ("making", "paid") and j["withdrawal"]["state"] == "lapsed", j)

# C16 making began WITHOUT the confirmation having gone out first: the right did not lapse
oM, kM, sidM, _ = paid_order("en", "mia@example.com")
md = read_json(f"orders/{oM}/mail_delivery.json")
write_json(f"orders/{oM}/making.json", {"t": md["t"] - 60})
c, j = withdraw(oM, kM, name="Mia", email="mia@example.com")
check("C16 making before the confirmation: effective after all", c == 200 and j["withdrawal"]["state"] == "withdrawn"
      and j["withdrawal"]["reason"] == "began_without_confirmation", (c, j))

# C17 the 14 days are over and nothing was made
oP, kP, sidP, _ = paid_order("en", "pia@example.com")
pp = read_json(f"orders/{oP}/paid.json")
pp["paid_at"] -= 21 * 86400      # wave r: over whatever the hour or a weekend-moved last day
write_json(f"orders/{oP}/paid.json", pp)
c, j = withdraw(oP, kP, name="Pia", email="pia@example.com")
check("C17 period over: lapsed, period_over", c == 200 and j["withdrawal"]["state"] == "lapsed"
      and j["withdrawal"]["reason"] == "period_over" and not exists(f"orders/{oP}/withdrawn.json"), (c, j))

# C18 without the link: the payment email identifies the customer
oQ, kQ, sidQ, _ = paid_order("en", "Quinn@Example.com")
c, j = withdraw(oQ, None, name="Quinn", email="quinn@example.COM")
check("C18 no k, the paid email (any case): effective", c == 200 and j["withdrawal"]["state"] == "withdrawn", (c, j))
check("C19 ... recorded as matched by email", read_json(f"orders/{oQ}/" + [f for f in os.listdir(local(f"orders/{oQ}"))
      if re.fullmatch(r"withdrawal_[0-9a-f]+\.json", f)][0])["verified"] == "email")

# C20 without the link and another email: kept apart, owner checks, no mail to the typed address, order untouched
n0 = len(H.Fake.emails)
oR, kR, sidR, _ = paid_order("en", "rita@example.com")
c, j = withdraw(oR, None, name="Stranger", email="stranger@example.com")
yymm = time.strftime("%y%m", time.gmtime())
apart = os.listdir(local(f"withdrawals/{yymm}")) if exists(f"withdrawals/{yymm}") else []
check("C20 unmatched: 404 not_found, recorded apart", c == 404 and j.get("reason") == "not_found" and j.get("recorded") is True
      and any(x.endswith(".json") and not x.endswith(("_ack.json", "_note.json")) for x in apart), (c, j, apart))
# round 3: the typed address gets a NEUTRAL receipt (nothing about the order), the owner one note a day at once
# (the rest in the daily digest), never one per statement
rs = mails_to("stranger@example.com", n0)
check("C21 unmatched: a neutral receipt to the typed address, the owner is told once, the order runs on",
      len(rs) == 1 and rs[0]["subject"] == "We received your withdrawal statement: SnapEyes" and oR in rs[0]["text"]
      and "rita" not in rs[0]["text"] and not exists(f"orders/{oR}/withdrawn.json")
      and any("matched no order" in x["subject"] for x in mails_to("info@snapeyes.com", n0))
      and not any("NOT MATCHED" in x["subject"] for x in mails_to("info@snapeyes.com", n0)),
      ([x["subject"] for x in rs], [x["subject"] for x in mails_to("info@snapeyes.com", n0)]))
c, j = withdraw("260101-0000000000000000", None, name="X", email="x@example.com")
c2, j2 = withdraw("not an order", None, name="X", email="x@example.com")
check("C22 an unknown order or a typed text: 404 not_found, recorded", c == 404 and c2 == 404 and j.get("recorded")
      and j2.get("recorded"), (c, j, c2, j2))
c, j = withdraw(oR, "0" * 32, name="X", email="rita@example.com")
check("C23 a wrong link key with the paid email still matches by email", c == 200 and j["withdrawal"]["state"] == "withdrawn", (c, j))

# C24 unpaid order: no contract; its open payment page is closed
H.Fake.expires.clear()
oU, kU, sidU = new_checkout("en")
n0 = len(H.Fake.emails)
c, j = withdraw(oU, kU, name="Uma", email="uma@example.com")
check("C24 unpaid: 409 not_paid, recorded, session expired at Stripe, no receipt", c == 409 and j.get("reason") == "not_paid"
      and j.get("recorded") is True and sidU in H.Fake.expires and H.Fake.sessions[sidU]["status"] == "expired"
      and not mails_to("uma@example.com", n0), (c, j))

# C25 unpaid here but PAID at Stripe (the webhook has not arrived): recorded as paid, then effective
oV, kV, sidV = new_checkout("en")
H.pay_session(sidV, "vera@example.com")
n0 = len(H.Fake.emails)
c, j = withdraw(oV, kV, name="Vera", email="vera@example.com")
check("C25 paid at Stripe: recorded (source withdraw), effective", c == 200 and j["withdrawal"]["state"] == "withdrawn"
      and read_json(f"orders/{oV}/paid.json")["source"] == "withdraw", (c, j))
c, j = hook(H.Fake.sessions[sidV])
check("C26 the late webhook: 200, no confirmation email (withdrawn)", c == 200 and j.get("mail") == "withdrawn"
      and not [x for x in mails_to("vera@example.com", n0) if "order confirmation" in x["subject"]], (c, j))

# C27 the payment is still settling: effective; when it arrives, the owner is told to refund it
oS, kS, sidS = new_checkout("en")
H.Fake.sessions[sidS].update(status="complete", payment_status="unpaid", created=int(time.time()))
n0 = len(H.Fake.emails)
c, j = withdraw(oS, kS, name="Sam", email="sam@example.com")
check("C27 settling: effective, payment_settling, withdrawn.json", c == 200 and j["withdrawal"]["state"] == "withdrawn"
      and j["withdrawal"]["reason"] == "payment_settling" and exists(f"orders/{oS}/withdrawn.json"), (c, j))
c, j = status(oS, kS)
check("C28 status of the unpaid withdrawn order: withdrawn", c == 200 and j["state"] == "withdrawn", (c, j))
c, j = checkout(oS, kS)
check("C29 checkout of a withdrawn order: 409 withdrawn", c == 409 and j.get("reason") == "withdrawn", (c, j))
c, j = draft(2, oS, kS)
check("C30 draft into a withdrawn order: 409 withdrawn", c == 409 and j.get("reason") == "withdrawn", (c, j))
H.pay_session(sidS, "sam@example.com")
c, j = hook(H.Fake.sessions[sidS])
paw = [x for x in mails_to("info@snapeyes.com", n0) if "paid after it was withdrawn" in x["subject"]]
check("C31 the settled payment: recorded, owner told to refund, no confirmation to the customer", c == 200
      and len(paw) == 1 and not [x for x in mails_to("sam@example.com", n0) if "order confirmation" in x["subject"]], (c, j))
c, j = status(oS, kS)
check("C32 ... and the order stays withdrawn", j["state"] == "withdrawn", j)

# C33 input checks
c1, _ = withdraw(oA, kA, name="")
c2, _ = withdraw(oA, kA, email="nope")
c3, _ = post("/api/order", {"action": "withdraw", "name": "A", "email": "a@example.com"})
c4, _ = withdraw(oA, kA, name="A" * 500)
check("C33 name, email and order are required (400); a long name is cut, not refused", (c1, c2, c3) == (400, 400, 400)
      and c4 == 200, (c1, c2, c3, c4))

# C34 per-order ceiling
oX, kX, sidX, _ = paid_order("en", "xena@example.com")
codes = [withdraw(oX, kX, name="Xena", email="xena@example.com")[0] for _ in range(6)]
check("C34 five statements a day for one order, then 429", codes[:5] == [200] * 5 and codes[5] == 429, codes)

# C35 Resend busy for the receipt: pending, then the clean-up sends it
oY, kY, sidY, _ = paid_order("en", "yara@example.com")
H.Fake.fail_mail[:] = [503, 503, 503, 503]
n0 = len(H.Fake.emails)
c, j = withdraw(oY, kY, name="Yara", email="yara@example.com")
due = os.listdir(local("withdrawdue")) if exists("withdrawdue") else []
check("C35 receipt pending, a retry mark", c == 200 and j["withdrawal"]["mail"] == "pending" and len(due) >= 1, (c, j, due))
H.Fake.fail_mail[:] = []
r = W.retry_due()
check("C36 the clean-up sends it and removes the mark", r["sent"] >= 1 and len(mails_to("yara@example.com", n0)) == 1
      and not (exists("withdrawdue") and os.listdir(local("withdrawdue"))), r)

# C37 storage fails while recording: the owner gets the statement, the page is told to try again
real_put = store.put


def failing_put(path, *a, **kw):
    if "/withdrawal_" in path or path.startswith(("withdrawals/", "withdrawlog/")):
        raise store.StorageError("injected")
    return real_put(path, *a, **kw)


store.put = failing_put
n0 = len(H.Fake.emails)
oZ, kZ, sidZ, _ = paid_order("en", "zoe@example.com")
c, j = withdraw(oZ, kZ, name="Zoe", email="zoe@example.com")
store.put = real_put
fb = [x for x in mails_to("info@snapeyes.com", n0) if "NOT stored" in x["subject"]]
check("C37 storage down: 503 storage_busy, the statement reaches the owner by email", c == 503
      and j.get("reason") == "storage_busy" and len(fb) == 1 and "zoe@example.com" in fb[0]["text"], (c, j))

# C38 the photo of a withdrawn order may start a new one
tk = H.fresh_ticket()
b = {"action": "draft", "eye": 1, "crop": SMALL, "preview": SMALL, "pad": 1.12, "lang": "en", "ref": "e1", "ticket": tk}
c, d1 = post("/api/order", b)
o1, k1 = d1["order"], d1["k"]
checkout(o1, k1)
H.Fake.sessions[sid_of(o1)].update(status="complete", payment_status="unpaid", created=int(time.time()))
withdraw(o1, k1, name="T", email="t@example.com")
c, d2 = post("/api/order", b)
check("C38 same ticket after a withdrawal: a new order", c == 200 and d2.get("created") is True and d2["order"] != o1, (c, d2))

# C39 the draft files are gone: the order goes to review, and making has NOT begun (a withdrawal stays effective)
oG2, kG2, sidG2, _ = paid_order("en", "gus@example.com")
d1 = read_json(f"orders/{oG2}/draft/eye_1.json")
os.remove(local(d1["crop"]["path"]))
c, j = make(oG2, kG2)
check("C39 missing draft file: 409 in_review, no making.json", c == 409 and j.get("reason") == "in_review"
      and not exists(f"orders/{oG2}/making.json"), (c, j))
c, j = withdraw(oG2, kG2, name="Gus", email="gus@example.com")
check("C40 ... so a withdrawal is effective", c == 200 and j["withdrawal"]["state"] == "withdrawn", (c, j))

# ======================================================================================== D. the daily clean-up
os.environ["CRON_SECRET"] = "cron-" + "s" * 30
AUTH = {"Authorization": "Bearer " + os.environ["CRON_SECRET"]}
c, j = get("/api/order", {"x-vercel-cron-schedule": "17 3 * * *"})
c2, j2 = get("/api/order", {"User-Agent": "vercel-cron/1.0"})
check("D1 a Vercel Cron request without the secret: 403", c == 403 and c2 == 403, (c, j, c2, j2))
c, j = get("/api/order", dict(AUTH, **{"x-vercel-cron-schedule": "17 3 * * *", "User-Agent": "vercel-cron/1.0"}))
check("D2 the cron path /api/order with the secret runs the clean-up", c == 200 and j.get("ok") is True
      and "unpaid" in j and "withdrawn" in j and "expired" in j, (c, j))
c, j = get("/api/health")
check("D3 health says cron true (a boolean only)", j.get("cron") is True and os.environ["CRON_SECRET"] not in json.dumps(j), j)

# withdrawn orders' images go after 14 days; the records stay
m = read_json(f"cleanup/withdrawn/{oW}.json")
m["t"] -= 15 * 86400
write_json(f"cleanup/withdrawn/{oW}.json", m)
before = sorted(os.listdir(local(f"orders/{oW}")))
c, j = get("/api/order", dict(AUTH, **{"x-vercel-cron-schedule": "17 3 * * *"}))
after = sorted(os.listdir(local(f"orders/{oW}")))
check("D4 withdrawn 15 days ago: images deleted, records kept, mark removed", c == 200 and j["withdrawn"]["orders"] >= 1
      and (not exists(f"orders/{oW}/draft") or not os.listdir(local(f"orders/{oW}/draft"))), (j, before, after))
check("D5 ... order.json, paid.json, statements, withdrawn.json and deleted.json stay",
      all(x in after for x in ("order.json", "paid.json", "withdrawn.json", "deleted.json", "mail_delivery.json"))
      and any(x.startswith("withdrawal_") for x in after) and not exists(f"cleanup/withdrawn/{oW}.json"), after)
c, j = status(oW, kW)
check("D6 its order page still says withdrawn", j["state"] == "withdrawn", j)

# a withdrawn order whose payment is still settling is kept; one whose payment failed long ago goes
m = read_json(f"cleanup/withdrawn/{oS}.json") if exists(f"cleanup/withdrawn/{oS}.json") else None
oS2, kS2, sidS2 = new_checkout("en")
H.Fake.sessions[sidS2].update(status="complete", payment_status="unpaid", created=int(time.time()))
withdraw(oS2, kS2, name="S2", email="s2@example.com")
mk = read_json(f"cleanup/withdrawn/{oS2}.json")
mk["t"] -= 15 * 86400
write_json(f"cleanup/withdrawn/{oS2}.json", mk)
r = C.run(yes=True, lock=False)
check("D7 withdrawn while settling, still settling: kept", exists(f"orders/{oS2}/order.json") and r["withdrawn"]["kept"] >= 1, r)
H.Fake.sessions[sidS2]["created"] = int(time.time()) - 25 * 86400
r = C.run(yes=True, lock=False)
check("D8 settling for 25 days (failed): the unpaid order goes completely", not exists(f"orders/{oS2}/order.json")
      and not exists(f"cleanup/withdrawn/{oS2}.json"), r)

# 12 months after payment: files go, records stay; a day not yet due is left
C.FIRST_DAY = "240101"
now = time.time()
old_day = pay.day(now - 370 * 86400)
oO, kO, _ = pay.new_order("en", order=f"{old_day}-00000000000000aa")
for name, data in (("draft/eye_1.json", b"{}"), ("eye_1.jpg", b"jpeg"), ("artwork_x.jpg", b"art"),
                   ("delivery.json", b"{}"), ("mail_delivery.json", b'{"state": "sent"}'), ("note_paid.json", b"{}")):
    store.put(f"orders/{oO}/{name}", data, "application/json", upsert=True)
write_json(f"orders/{oO}/paid.json", {"paid": True, "order": oO, "paid_at": int(now - 369 * 86400), "email": "old@example.com",
                                      "spec": {"eyes": 1, "style": "studio_black", "layout": "single", "names": "Old",
                                               "title": "", "lang": "en"}, "amount_total": 1997, "livemode": True})
due_day = pay.day(now - 365 * 86400)
oT, kT, _ = pay.new_order("en", order=f"{due_day}-00000000000000bb")
store.put(f"orders/{oT}/eye_1.jpg", b"jpeg", "image/jpeg", upsert=True)
write_json(f"orders/{oT}/paid.json", {"paid": True, "order": oT, "paid_at": int(now - 364 * 86400), "spec": {"eyes": 1},
                                      "amount_total": 1997, "livemode": True})
r = C.run(yes=True, lock=False)
left = sorted(os.listdir(local(f"orders/{oO}")))
check("D9 paid 369 days ago: files deleted, records stay, expired.json", r["expired"]["expired"] == 1
      and not exists(f"orders/{oO}/eye_1.jpg") and not exists(f"orders/{oO}/artwork_x.jpg")
      and all(x in left for x in ("order.json", "paid.json", "mail_delivery.json", "note_paid.json", "expired.json",
                                  "deleted.json")), (r, left))
check("D10 the record keeps email and names (the policy's order records)", read_json(f"orders/{oO}/paid.json")["email"] == "old@example.com")
check("D11 paid 364 days ago: untouched, its day not finished", exists(f"orders/{oT}/eye_1.jpg")
      and not exists(f"cleanup/done_expired/{due_day}.json") and exists(f"cleanup/done_expired/{old_day}.json"), r)
r2 = C.run(yes=True, lock=False)
check("D12 a second run: nothing more, the finished days skipped", r2["expired"]["expired"] == 0
      and r2["expired"]["days"] < r["expired"]["days"] and r2["unpaid"]["deleted"] == 0, (r["expired"], r2["expired"]))
c, j = status(oO, kO)
check("D13 the expired order's page says deleted", c == 200 and j["state"] == "deleted", (c, j))

# time box, lock, dry run
r = C.run(yes=True, stop_left=1000.0, lock=False)
check("D14 no time left: stops at once with more: true", r["more"] is True, r)
write_json(C.LOCK, {"t": int(time.time())})
c, j = get("/api/order", dict(AUTH, **{"x-vercel-cron-schedule": "17 3 * * *"}))
check("D15 a run already going on: the second leaves", c == 200 and j.get("skipped") == "running", (c, j))
write_json(C.LOCK, {"t": int(time.time()) - 600})
c, j = get("/api/order?cron=purge", AUTH)
check("D16 a stale lock is taken over, and released after", c == 200 and "unpaid" in j and not exists(C.LOCK), (c, j))
oK, kK, sidK = old_checkout(2)
H.Fake.sessions[sidK]["status"] = "expired"
recK = read_json(f"orders/{oK}/order.json")
recK["created_at"] -= 30 * 3600
write_json(f"orders/{oK}/order.json", recK)
r = C.run(yes=False, lock=False)
check("D17 a dry run changes nothing", exists(f"orders/{oK}/order.json") and r["unpaid"]["deleted"] >= 1, r["unpaid"])
r = C.run(yes=True, lock=False)
check("D18 the real run deletes the unpaid order older than 26 h", not exists(f"orders/{oK}/order.json"), r["unpaid"])

# statements that matched no order: kept 12 months after their month, then deleted
store.put("withdrawals/2001/old-statement.json", b"{}", "application/json", upsert=True)
r = C.run(yes=True, lock=False)
check("D18b unmatched statements of an old month are deleted, this month's stay", not exists("withdrawals/2001/old-statement.json")
      and os.listdir(local(f"withdrawals/{yymm}")) and r.get("unmatched", 0) >= 1, r)

# unpaid order paid at Stripe without paid.json: recorded, never deleted (Stripe asked first)
oJ, kJ, sidJ = old_checkout(2)
H.pay_session(sidJ, "jo@example.com")
recJ = read_json(f"orders/{oJ}/order.json")
recJ["created_at"] -= 30 * 3600
write_json(f"orders/{oJ}/order.json", recJ)
r = C.run(yes=True, lock=False)
check("D19 paid at Stripe, no paid.json: recorded as paid, not deleted", exists(f"orders/{oJ}/paid.json")
      and exists(f"orders/{oJ}/order.json") and r["unpaid"]["recorded"] >= 1, r["unpaid"])

# the unknown order webhook tells the owner
n0 = len(H.Fake.emails)
ghost = dict(H.Fake.sessions[sidJ], id="cs_test_ghost0001", metadata=dict(H.Fake.sessions[sidJ]["metadata"],
                                                                         order="260101-00000000deadbeef"))
c, j = hook(ghost)
check("D20 a paid session for an order that is gone: 200, the owner is told to refund", c == 200
      and any("the order is gone" in x["subject"] for x in mails_to("info@snapeyes.com", n0)), (c, j))

# ======================================================================================== E. the admin script
envs = dict(os.environ, STORE_LOCAL_DIR=STORE)
r = subprocess.run(ADMIN + ["cleanup"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("E1 order_admin cleanup (dry run) runs and says so", r.returncode == 0 and "dry run" in r.stdout, r.stdout[-400:] + r.stderr[-400:])
r = subprocess.run(ADMIN + ["status", oL], capture_output=True, text=True, env=envs, encoding="utf-8")
check("E2 status shows the withdrawal statement", r.returncode == 0 and "WITHDRAWAL" in r.stdout and "lapsed" in r.stdout,
      r.stdout[-600:] + r.stderr[-400:])
r = subprocess.run(ADMIN + ["erase", oL, "--yes"], capture_output=True, text=True, env=envs, encoding="utf-8")
left = os.listdir(local(f"orders/{oL}"))
check("E3 erase keeps the records and the statements", r.returncode == 0 and "paid.json" in left
      and any(x.startswith("withdrawal_") for x in left) and not exists(f"orders/{oL}/eye_1.jpg"), (r.stdout, left))
r = subprocess.run(ADMIN + ["expire-paid", "--months", "12"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("E4 expire-paid dry run", r.returncode == 0 and "dry run" in r.stdout, r.stdout + r.stderr)
r = subprocess.run(ADMIN + ["release", "--help"], capture_output=True, text=True, env=envs, encoding="utf-8")
check("E5 release mails by default (--no-mail)", "--no-mail" in r.stdout, r.stdout)

# ======================================================================================== hygiene
bad = []
for f in ("api/_lib/pay.py", "api/_lib/withdraw.py", "api/_lib/cleanup.py", "api/order.py", "api/checkout.py",
          "api/stripe_webhook.py", "api/health.py", "scripts/order_admin.py", "vercel.json"):
    t = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in t for ch in DASHES) or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in t) or "\r" in t:
        bad.append(f)
check("H1 my files: no em/en dashes, no control characters, LF", not bad, bad)
allmail = json.dumps([m for m, _ in H.Fake.emails], ensure_ascii=False)
check("H2 no email carries a dash, a Stripe key, a webhook secret or the Resend key", not any(d in allmail for d in DASHES)
      and H.SK not in allmail and H.WHSEC not in allmail and H.RESEND not in allmail)
vj = json.load(open(os.path.join(H.REPO, "vercel.json"), encoding="utf-8"))
check("H3 vercel.json: one daily cron on /api/order, functions unchanged", vj["crons"] == [{"path": "/api/order",
      "schedule": "17 3 * * *"}] and vj["functions"]["api/**/*.py"]["maxDuration"] == 60, vj)
fns = [f for f in os.listdir(H.API) if f.endswith(".py") and not f.startswith("_")]
check("H4 at most 12 Python functions (Hobby allows 12; api/admin.py is the 11th, wave q)", len(fns) <= 12, fns)

failed = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(failed)} of {len(RESULTS)} passed" + (f"; FAILED: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
