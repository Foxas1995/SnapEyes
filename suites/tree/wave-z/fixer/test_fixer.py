# -*- coding: utf-8 -*-
"""The fixer's checks for the markets build (review findings): the legal pack read from a protected Preview with the
protection bypass (and only there), the Australian invoice dated in Sydney with a date of supply, the daily clean-up
and a session PAID in the wrong currency (kept, owner told once), order_admin status in the order's currency, the
withdrawal answer naming the order's market, the build's price check refusing a selectable market without its own
legal texts, and the site code (fixer_client.mjs: ?m= spelling, the country offer, a paused Australian market, the
corrected Australian texts). Fake Stripe + Resend + legal pack (wave-r-back/pb/harness.py), own store folder.
    python test_fixer.py        PASS/FAIL per check, exit 1 on any failure
Refreshed 2026-09-30 for 30efee7 (Lithuanian and Hungarian; Hungary selectable with its own legal edition: hu is now an
offer, a link and a legal edition like au) and 1acef38 (price experiments: the build's price check also reads
api/_lib/experiments.py). Comments "30efee7" / "1acef38" mark the expectations that changed with them."""
import os, sys, json, time, io, re, shutil, subprocess, calendar, contextlib, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.environ.get("SNAPEYES_SP") or os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(SP, "wave-r-back", "pb"))
import harness as H

stub = H.start_stub()
STORE = os.path.join(HERE, "store_fixer")
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay

RESULTS = []
DASHES = (chr(0x2013), chr(0x2014))


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:1200]}"), flush=True)


def post(path, body):
    r = requests.post(BASE + path, data=json.dumps(body), headers={"Content-Type": "application/json"}, timeout=60)
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


def notes(since=0, words=""):
    return [m for m in mails_to(pay.owner_mail(), since) if words in m["subject"]]


def paid_order(market, lang, email, eyes=1, style="studio_black"):
    o, k = new_order(eyes, lang)
    c, j = checkout(o, k, eyes, style, lang, **({"market": market} if market else {}))
    assert c == 200, (c, j)
    n0 = len(H.Fake.emails)
    c, j = hook(H.pay_session(sid_of(o), email))
    assert c == 200, (c, j)
    return o, k, read_json(f"orders/{o}/paid.json"), mails_to(email, n0)


PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
H.Fake.legal = json.loads(json.dumps(PACK))
pay._LEGAL.update(pack=None, t=0.0, failed=0.0)

# ---------------------------------------------------------------------------------------------- A. Sydney dates
ts = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M"))
cases = {"2026-09-29T20:30": "2026-09-30",    # AEST +10: the Australian morning is the next UTC day
         "2026-06-30T13:30": "2026-06-30",    # AEST: 23:30 the same day
         "2026-12-31T13:30": "2027-01-01",    # AEDT +11: already New Year in Sydney
         "2026-10-03T15:59": "2026-10-04",    # one minute before summer time starts (Sun 4 Oct 2026, 2:00 AEST)
         "2026-10-03T16:00": "2026-10-04",    # summer time: 03:00 AEDT
         "2027-04-03T15:59": "2027-04-04",    # the last minute of summer time (Sun 4 Apr 2027, 3:00 AEDT)
         "2027-04-03T16:00": "2027-04-04",    # standard time again: 02:00 AEST
         "2026-03-01T12:59": "2026-03-01",    # AEDT: 23:59
         "2026-03-01T13:00": "2026-03-02"}
got = {k: pay.sydney_day(ts(k)) for k in cases}
check("A1 sydney_day: AEST/AEDT with the first-Sunday rules, around midnight and both switches", got == cases, got)
check("A2 sydney_day without a time: today in Sydney (no crash)", re.fullmatch(r"\d{4}-\d{2}-\d{2}", pay.sydney_day(None) or "")
      and pay.sydney_day("junk") == pay.sydney_day(None))

# ---------------------------------------------------------------------------------------------- B. the Australian invoice
fake_paid = {"paid_at": ts("2026-09-29T20:30"), "amount_total": 7900, "currency": "aud", "email": "a@example.com",
             "spec": {"eyes": 2, "style": "studio_black", "layout": "duo", "market": "au"}}
rows_en = dict(pay.invoice_rows("260929-abc", fake_paid, PACK, "en"))
rows_de = dict(pay.invoice_rows("260929-abc", fake_paid, PACK, "de"))
check("B1 invoice date and payment day are Sydney's (paid 20:30 UTC on 29 Sep = 30 September 2026)",
      rows_en["Invoice date"] == "30 September 2026" and rows_en["Payment"].endswith("on 30 September 2026")
      and rows_de["Rechnungsdatum"] == "30.09.2026", (rows_en, rows_de))
check("B2 invoice has a date of supply (when the file is ready, at the latest 48 hours after payment), en and de",
      rows_en.get("Date of supply") == "when your file is ready for download on your order page, at the latest 48 hours after your payment"
      and rows_de.get("Leistungsdatum", "").startswith("wenn Ihre Datei auf Ihrer Bestellseite zum Download bereitsteht, spätestens 48 Stunden"),
      (rows_en, rows_de))
oI, kI, pI, mI = paid_order("au", "en", "melbourne@example.com", eyes=2)
head = mI[0]["text"].split("_" * 64)[0] if mI else ""
want_day = pay.date_text(pay.sydney_day(pI["paid_at"]), "en")
check("B3 the AU confirmation email: the invoice rows with the Sydney date and the date of supply, never 'Tax invoice'",
      f"Invoice date: {want_day}\n" in head and "Date of supply: when your file is ready for download on your order page, "
      "at the latest 48 hours after your payment\n" in head and not re.search("tax invoice", mI[0]["text"] if mI else "", re.I)
      and not any(d in head for d in DASHES), head[:1800])
check("B4 the terms promise the same 48 hours as the invoice (src/landing/config.ts DELIVERY_MAX_HOURS)",
      re.search(r"DELIVERY_MAX_HOURS\s*=\s*48\b", open(os.path.join(H.REPO, "src", "landing", "config.ts"), encoding="utf-8").read())
      and pay.DELIVERY_MAX_HOURS == 48)
oE, kE, pE, mE = paid_order(None, "en", "dublin@example.com")
check("B5 an EU confirmation has no invoice rows (unchanged)", mE and "Invoice date" not in mE[0]["text"]
      and "Date of supply" not in mE[0]["text"])

# ---------------------------------------------------------------------------------------------- C. clean-up and a wrong-currency payment
oC, kC = new_order(1)
checkout(oC, kC, 1, "studio_black", "en", market="au")
sC = H.Fake.sessions[sid_of(oC)]
H.pay_session(sC["id"], "converted@example.com")
sC["currency"] = "eur"                  # a Stripe-side conversion: our session, paid, in another currency
recC = read_json(f"orders/{oC}/order.json")
n0 = len(H.Fake.emails)
pay.start_clock()
v_dry = pay.stripe_verdict(oC, recC, record=False)
check("C1 stripe_verdict (dry run) of an unpaid order whose session is PAID in the wrong currency: unknown, nobody told",
      v_dry == "unknown" and not notes(n0, "unexpected currency") and not exists(f"orders/{oC}/paid.json"), (v_dry, notes(n0)))
pay.start_clock()
v1 = pay.stripe_verdict(oC, recC, record=True)
pay.start_clock()
v2 = pay.stripe_verdict(oC, recC, record=True)
n1 = notes(n0, "unexpected currency")
check("C2 ... with record: unknown (kept), the owner told ONCE (a second run adds nothing), never recorded as paid",
      v1 == "unknown" and v2 == "unknown" and len(n1) == 1 and "The order is kept" in n1[0]["text"]
      and "19.97 EUR" not in n1[0]["text"] and "39.00 EUR" in n1[0]["text"] and not exists(f"orders/{oC}/paid.json"),
      (v1, v2, [m["text"][:400] for m in n1]))
c, j = hook(sC)
check("C3 the same session later by webhook: refused, and still one note in all (the same note kind)",
      c == 200 and j.get("ignored") == "session does not match" and len(notes(n0, "unexpected currency")) == 1
      and not exists(f"orders/{oC}/paid.json"), (c, j, len(notes(n0, "unexpected currency"))))
# the purge keeps it (made long enough ago)
recC["created_at"] = int(time.time()) - 30 * 3600
store.put(f"orders/{oC}/order.json", store.json_bytes(recC), "application/json", upsert=True)
pay.start_clock()
said = []
res = pay.purge_unpaid(hours=26, yes=True, out=said.append, names=[oC], markers=False)
check("C4 purge_unpaid keeps that order (kept_orders) and says why; its record stays",
      oC in res["kept_orders"] and res["deleted"] == 0 and exists(f"orders/{oC}/order.json")
      and any("paid in another currency" in s for s in said), (res, said))
# a right-currency session of the same kind is still recorded by the clean-up (unchanged)
oP, kP = new_order(1)
checkout(oP, kP, 1, "supernova", "en", market="au")
H.pay_session(sid_of(oP), "perthclean@example.com")
recP = read_json(f"orders/{oP}/order.json")
pay.start_clock()
check("C5 a session paid in its own currency: the clean-up records it (paid), as before",
      pay.stripe_verdict(oP, recP, record=True) == "paid" and read_json(f"orders/{oP}/paid.json")["currency"] == "aud")

# a wrong-currency session does not hide an earlier session of the same order that IS its payment
oW, kW = new_order(1)
checkout(oW, kW, 1, "studio_black", "en", market="au")
sidA = sid_of(oW)
checkout(oW, kW, 1, "studio_black", "en")                  # switched to eu: the AU session is expired, a new EUR one made
sidB = sid_of(oW)
H.Fake.sessions[sidA].update(status="complete", payment_status="paid", customer_details={"email": "race@example.com"},
                             payment_intent="pi_test_race_a")                      # the old AU tab paid anyway (a race)
H.pay_session(sidB, "race@example.com")
H.Fake.sessions[sidB]["currency"] = "aud"                  # and the newest one paid in the wrong currency
recW = read_json(f"orders/{oW}/order.json")
n0 = len(H.Fake.emails)
pay.start_clock()
vW = pay.stripe_verdict(oW, recW, record=True)
pW = read_json(f"orders/{oW}/paid.json") if exists(f"orders/{oW}/paid.json") else {}
check("C6 newest session paid in the wrong currency, an older one paid in its own: the older is recorded (paid), the owner "
      "told about the other", sidA != sidB and vW == "paid" and pW.get("session_id") == sidA and pW.get("currency") == "aud"
      and len(notes(n0, "unexpected currency")) == 1, (vW, pW.get("session_id"), sidA, sidB))

# ---------------------------------------------------------------------------------------------- D. order_admin status
oS, kS = new_order(1)
checkout(oS, kS, 1, "studio_black", "en", market="au")
spec = importlib.util.spec_from_file_location("order_admin_fixer", os.path.join(H.REPO, "scripts", "order_admin.py"))
OA = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OA)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    OA.cmd_status(oS)
line = next((x for x in buf.getvalue().splitlines() if x.startswith("checkout")), "")
check("D1 order_admin status: the checkout line names the amount in its currency and the market (no bare 'cents')",
      "39.00 AUD" in line and "market au" in line and "cents" not in line, buf.getvalue()[:600])
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    OA.cmd_status(oE)
line = next((x for x in buf.getvalue().splitlines() if x.startswith("checkout")), "")
check("D2 ... an EU order: 19.97 EUR, market eu", "19.97 EUR" in line and "market eu" in line, line)

# ---------------------------------------------------------------------------------------------- E. the withdrawal answer names the market
def withdraw_now(order, k, email, lang="en", **kw):
    b = {"action": "withdraw", "order": order, "k": k, "name": "Test Person", "email": email, "lang": lang}
    b.update(kw)
    return post("/api/order", b)


store.put(f"orders/{oI}/making.json", store.json_bytes({"t": int(time.time())}), "application/json", upsert=True)
c, j = withdraw_now(oI, kI, "melbourne@example.com")
w = j.get("withdrawal") or {}
check("E1 a lapsed statement on an AU order: the answer names market au", c == 200 and w.get("state") == "lapsed"
      and w.get("market") == "au", (c, j))
c, j = withdraw_now(oE, kE, "dublin@example.com")
w = j.get("withdrawal") or {}
check("E2 an effective withdrawal on an EU order: market eu, amount and currency as before",
      c == 200 and w.get("state") == "withdrawn" and w.get("market") == "eu" and w.get("currency") == "EUR"
      and w.get("amount") == 1997, (c, j))
c, j = withdraw_now(oP, None, "someone.else@example.com")
w = j.get("withdrawal") or {}
check("E3 an unmatched statement (another email, no key): 404 and no market in the answer (nobody learns it)",
      c == 404 and "market" not in w, (c, j))

# ---------------------------------------------------------------------------------------------- F. the legal pack from a protected Preview
SECRET = "bypass_secret_for_tests_0123456789"
saved = {k: os.environ.get(k) for k in ("VERCEL", "VERCEL_ENV", "VERCEL_URL", "VERCEL_AUTOMATION_BYPASS_SECRET",
                                        "SNAPEYES_SITE", "LEGAL_PACK_BASE")}
real_get = pay.requests.get
calls = []


class Resp:
    def __init__(self, code, body):
        self.status_code, self._b = code, body

    def json(self):
        return self._b


def fake_get(own_code):
    def get(url, timeout=None, headers=None):
        calls.append((url, dict(headers or {})))
        if url.startswith("https://snapeyes-git-x.vercel.app"):
            return Resp(own_code, PACK if own_code == 200 else {"error": "login"})
        return Resp(200, {k: v for k, v in PACK.items() if k != "editions"})    # production's pack before AU
    return get


def run_pack(env, own_code=200):
    calls.clear()
    for k in saved:
        os.environ.pop(k, None)
    os.environ.update(env)
    pay.requests.get = fake_get(own_code)
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)
    pay.start_clock()
    try:
        return pay.legal_pack(fresh=True), list(calls)
    finally:
        pay.requests.get = real_get


try:
    prev = {"VERCEL": "1", "VERCEL_ENV": "preview", "VERCEL_URL": "snapeyes-git-x.vercel.app",
            "VERCEL_AUTOMATION_BYPASS_SECRET": SECRET}
    p1, c1 = run_pack(prev)
    check("F1 Preview: the pack is read from the Preview itself WITH the bypass header, and it is the Preview's own (au edition)",
          len(c1) == 1 and c1[0][0] == "https://snapeyes-git-x.vercel.app/legal/order-mail.json"
          and c1[0][1].get("x-vercel-protection-bypass") == SECRET and p1 is not None and "editions" in p1
          and pay.pack_docs(p1, "en", "au") is not None, c1)
    p2, c2 = run_pack(prev, own_code=401)
    check("F2 Preview answering 401: snapeyes.com is asked next WITHOUT the header",
          len(c2) == 2 and c2[1][0] == "https://snapeyes.com/legal/order-mail.json"
          and "x-vercel-protection-bypass" not in c2[1][1] and c2[0][1].get("x-vercel-protection-bypass") == SECRET, c2)
    p3, c3 = run_pack({"VERCEL": "1", "VERCEL_ENV": "production", "VERCEL_URL": "snapeyes-git-x.vercel.app",
                       "VERCEL_AUTOMATION_BYPASS_SECRET": SECRET})
    check("F3 production: snapeyes.com only, never the header", [u for u, _ in c3] == ["https://snapeyes.com/legal/order-mail.json"]
          and all("x-vercel-protection-bypass" not in h for _, h in c3), c3)
    p4, c4 = run_pack(dict(prev, SNAPEYES_SITE="https://example.org"))
    check("F4 a Preview whose SNAPEYES_SITE names another site: no header to it or to snapeyes.com",
          all("x-vercel-protection-bypass" not in h for _, h in c4) and c4 and c4[0][0].startswith("https://example.org"), c4)
    p5, c5 = run_pack(dict(prev, VERCEL_AUTOMATION_BYPASS_SECRET="bad secret!"))
    check("F5 a malformed bypass secret is never sent", c5 and all("x-vercel-protection-bypass" not in h for _, h in c5), c5)
    p6, c6 = run_pack({"VERCEL_AUTOMATION_BYPASS_SECRET": SECRET, "VERCEL_URL": "snapeyes-git-x.vercel.app",
                       "LEGAL_PACK_BASE": f"http://127.0.0.1:{stub.server_address[1]}"})
    check("F6 local runs (no VERCEL): the test base only, no header", c6 and all("x-vercel-protection-bypass" not in h for _, h in c6)
          and c6[0][0].startswith("http://127.0.0.1:"), c6)
finally:
    pay.requests.get = real_get
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)

# ---------------------------------------------------------------------------------------------- G. the build's price check
def check_prices(root):
    r = subprocess.run(["node", "-e", "import(process.argv[1]).then(M=>console.log(JSON.stringify(M.checkPrices(process.argv[2]))))",
                        "file:///" + os.path.join(H.REPO, "scripts", "check_prices.mjs").replace("\\", "/"), root],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    return json.loads(r.stdout or "null"), r.stderr


# A negative scenario edits COPIES of the real files. Each edit must find its premise exactly once in the file: an edit
# that matches nothing would leave a copy of the real files, and its check would pass or fail for the wrong reason.
NEG_PROBLEMS = {}


def sub(name, text, old, new):
    if "\r\n" in text:                        # a checkout with CRLF line ends
        old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
    if text.count(old) != 1:
        NEG_PROBLEMS.setdefault(name, []).append((text.count(old), old[:90]))
        return text
    return text.replace(old, new)


def edit_file(root, rel, fn):
    path = os.path.join(root, *rel.split("/"))
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(fn(text))


def neg_root(name, markets_sub=None, pay_sub=None):
    root = os.path.join(HERE, "neg", name)
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(os.path.join(root, "api", "_lib"))
    os.makedirs(os.path.join(root, "src", "shared"))
    mk = open(os.path.join(H.REPO, "api", "_lib", "markets.py"), encoding="utf-8").read()
    py = open(os.path.join(H.REPO, "api", "_lib", "pay.py"), encoding="utf-8").read()
    if markets_sub:
        mk = markets_sub(mk)
    if pay_sub:
        py = pay_sub(py)
    open(os.path.join(root, "api", "_lib", "markets.py"), "w", encoding="utf-8").write(mk)
    open(os.path.join(root, "api", "_lib", "pay.py"), "w", encoding="utf-8").write(py)
    # 1acef38: the price check also reads the price experiments' ladders, so a minimal root needs that file too
    shutil.copy(os.path.join(H.REPO, "api", "_lib", "experiments.py"), os.path.join(root, "api", "_lib", "experiments.py"))
    # WP1 of the v3 work: the price rule reads the registry's price classes (api/_lib/styles_registry.py), so a minimal root needs it
    shutil.copy(os.path.join(H.REPO, "api", "_lib", "styles_registry.py"), os.path.join(root, "api", "_lib", "styles_registry.py"))
    shutil.copy(os.path.join(H.REPO, "src", "shared", "legal.ts"), os.path.join(root, "src", "shared", "legal.ts"))
    return root


r = subprocess.run(["node", os.path.join(H.REPO, "scripts", "check_prices.mjs")], cwd=H.REPO, capture_output=True, text=True,
                   encoding="utf-8", timeout=120)
check("G1 npm run check:prices on the repo: ok", r.returncode == 0 and "price check ok" in r.stdout, (r.stdout, r.stderr))
ok_root = neg_root("same")
got, err = check_prices(ok_root)
check("G2 a copy of the real files: no problem", got == [], (got, err))
# 30efee7: hu IS selectable now, with its own edition of the legal texts, so flipping hu to selectable (what this scenario
# used to do) changes nothing. The same rule, the same market: hu selectable (as in the file) while no edition of the
# legal texts is listed for it, in the pages' lists and the server's (legal.ts and pay.py EDITION_MARKETS, EDITION_LANGS).
hu_on = neg_root("hu_selectable", pay_sub=lambda s: sub("hu_selectable", sub(
    "hu_selectable", s, 'EDITION_MARKETS = ("au", "hu")', 'EDITION_MARKETS = ("au",)'),
    ', "hu": ("en", "de", "lt", "hu")}', '}'))
edit_file(hu_on, "src/shared/legal.ts", lambda t: sub("hu_selectable", sub(
    "hu_selectable", t, "{ au: 'au', hu: 'hu' }", "{ au: 'au' }"),
    "  hu: ['en', 'de', 'lt', 'hu'],\n", ""))
def hu_is_selectable(root):
    txt = open(os.path.join(root, "api", "_lib", "markets.py"), encoding="utf-8").read()
    return json.loads(txt[txt.index("MARKETS = ") + len("MARKETS = "):])["hu"]["selectable"] == 1


got, err = check_prices(hu_on)
check("G3 hu set selectable without Hungarian texts: the build is refused, naming the market and the rule",
      not NEG_PROBLEMS.get("hu_selectable") and got and hu_is_selectable(hu_on)
      and any('market "hu": selectable, but no edition of the legal texts prints its HUF prices' in x for x in got),
      (got, err, NEG_PROBLEMS.get("hu_selectable")))
# 30efee7: the server's list of markets with an edition is pay.py EDITION_MARKETS (ACL_MARKETS became the Australian part of
# it, no longer compared with the pages' list); the build compares EDITION_MARKETS
drift = neg_root("acl_drift", pay_sub=lambda s: sub("acl_drift", s, 'EDITION_MARKETS = ("au", "hu")', 'EDITION_MARKETS = ("au", "hu", "lt")'))
got, err = check_prices(drift)
check("G4 pay.py EDITION_MARKETS and legal.ts EDITION_MARKETS disagree: refused",
      not NEG_PROBLEMS.get("acl_drift") and got and any("must name the same markets" in x for x in got),
      (got, err, NEG_PROBLEMS.get("acl_drift")))
au_off = neg_root("au_paused", markets_sub=lambda s: s.replace('"currency": "aud",\n        "prices": {"one_eye_studio_black": 3900, "one_eye_art": 4900, "two_eyes": 7900, "each_further_eye": 2900},\n        "selectable": 1',
                                                                   '"currency": "aud",\n        "prices": {"one_eye_studio_black": 3900, "one_eye_art": 4900, "two_eyes": 7900, "each_further_eye": 2900},\n        "selectable": 0'))
got, err = check_prices(au_off)
check("G5 pausing au (selectable 0) passes the check (the owner's one-flag pause)",
      got == [] and '"selectable": 0' in open(os.path.join(au_off, "api", "_lib", "markets.py"), encoding="utf-8").read().split('"au"')[1][:300],
      (got, err))
# 30efee7: the build also compares the languages each edition has (EDITION_LANGS in legal.ts and in pay.py): a new check
# of the same kind as G4, added with the Lithuanian and Hungarian editions
lang_drift = neg_root("edition_langs_drift", pay_sub=lambda s: sub("edition_langs_drift", s, '"au": ("en", "de"),', '"au": ("en", "de", "lt"),'))
got, err = check_prices(lang_drift)
check("G6 pay.py EDITION_LANGS and legal.ts EDITION_LANGS disagree: refused, naming the rule",
      not NEG_PROBLEMS.get("edition_langs_drift") and got and any("must list the same languages per edition" in x for x in got),
      (got, err, NEG_PROBLEMS.get("edition_langs_drift")))
# 30efee7 split pay.py's list in two: EDITION_MARKETS (every market with an edition; the build compares it with legal.ts, G4)
# and ACL_MARKETS (the Australian part: its checkbox, note and invoice). The build compares ACL_MARKETS with nothing (a drift
# to ("au", "hu") passes it: observed 2026-09-30), so this check keeps the guard G4 had before the split, on the real files.
lg_txt = open(os.path.join(H.REPO, "src", "shared", "legal.ts"), encoding="utf-8").read()
m_lg = re.search(r"export const EDITION_MARKETS[^=]*=\s*\{([^}]*)\}", lg_txt)
page_ed = dict(re.findall(r"\b([a-z]+)\s*:\s*'([a-z]{2,8})'", m_lg.group(1))) if m_lg else {}
check("G7 pay.py ACL_MARKETS is exactly the market legal.ts EDITION_MARKETS gives the au edition, inside EDITION_MARKETS",
      bool(page_ed) and sorted(pay.ACL_MARKETS) == sorted(m for m, e in page_ed.items() if e == "au") and set(pay.ACL_MARKETS) <= set(pay.EDITION_MARKETS)
      and pay.acl_market("au") and not pay.acl_market("hu") and not pay.acl_market("eu") and not pay.acl_market("lt")
      and pay.edition_market("hu") and not pay.edition_market("lt"), (page_ed, pay.ACL_MARKETS, pay.EDITION_MARKETS))

# ---------------------------------------------------------------------------------------------- H. the site's code
r = subprocess.run(["node", os.path.join(HERE, "fixer_client.mjs"), HERE], cwd=H.REPO, capture_output=True, text=True,
                   encoding="utf-8", timeout=300)
try:
    CL = json.loads(r.stdout)
except ValueError:
    CL = None
    check("H0 fixer_client.mjs ran", False, (r.stdout[-800:], r.stderr[-1500:]))
if CL:
    check("H1 ?m= spelled AU or padded: the au market (stored as au); Hu stays ignored (not selectable)" " - 0930: ?m=Hu is taken now (hu selectable since 30efee7), ignored only while hu is paused",
          CL["detect"] == {"upper": {"market": "au", "stored": "au"}, "padded": {"market": "au", "stored": "au"},
                           # 30efee7: hu is selectable now, so ?m=Hu is taken like ?m=AU; "Hu stays ignored" holds for hu PAUSED
                           "mixed_hu": {"market": "hu", "stored": "hu"}, "upper_lt": {"market": "lt", "stored": "lt"},
                           "mixed_hu_paused": {"market": "eu", "stored": None}}, CL["detect"])
    check("H2 linkMarket: any market the link names (hu too), junk and none: null",
          CL["link"] == {"hu": "hu", "au": "au", "junk": None, "none": None}, CL["link"])
    h = CL["hint"]
    # 30efee7: hu is selectable, so a Hungarian visitor is offered forints (fresh_hu) and accepting stores hu; "not selectable"
    # is now a market the owner paused before the page loaded (hu, au)
    check("H3 the country offer: only a selectable market in another currency, on the default market, no m= link, no choice "
          "stored; declining stores eu and it never comes back; accepting switches and stores au",
          h["fresh_au"] == "au" and h["fresh_hu"] == "hu" and h["same_currency_lt"] is None and h["not_selectable_hu"] is None
          and h["not_selectable_au"] is None and h["already_au"] is None
          and h["junk"] == [None, None, None, None] and h["declined_store"] == "eu" and h["after_decline"] is None
          and h["after_decline_market"] == "eu" and h["link_named_eu"] is None and h["stored_au_page"] == "au"
          and h["stored_au"] is None and h["after_accept"] == {"market": "au", "stored": "au", "again": None}
          and h["after_accept_hu"] == {"market": "hu", "stored": "hu", "again": None}, h)
    p = CL["paused"]
    check("H4 au paused: prices and /try ignore m=au, but legal links keep m=au and a legal page named m=au adopts it",
          p["detect"] == "eu" and p["tryLink"] == "/try?lang=en" and p["legalAu"] == "/terms?lang=en&m=au#australia"
          and p["legalEu"] == "/terms?lang=en#australia" and p["adopted"] == "au" and p["edition"] == "au"
          and p["legalHere"] == "/privacy?lang=de&m=au" and p["withdrawHere"] == "/order?withdraw=1&lang=en&m=au"
          and p["homeHere"] == "/?lang=en"
          # 30efee7: hu has its own edition now, so a legal page named m=hu shows it (the old expectation: market eu, plain links)
          and p["huPage"] == {"market": "hu", "edition": "hu", "legal": "/terms?lang=en&m=hu"}
          and p["storedOnly"] == {"market": "eu"}
          # paused before the page loads: au and (30efee7) hu keep their legal links and adopt a legal page that names them;
          # a paused market without an edition of its own (lt, the EU texts) is not adopted, links stay plain (the old huPage)
          and p["load_au"] == {"detect": "eu", "stored": None, "tryLink": "/try?lang=en", "adopted": "au", "edition": "au",
                               "legal": "/terms?lang=en&m=au", "withdraw": "/order?withdraw=1&lang=en&m=au", "home": "/?lang=en"}
          and p["load_hu"] == {"detect": "eu", "stored": None, "tryLink": "/try?lang=en", "adopted": "hu", "edition": "hu",
                               "legal": "/terms?lang=en&m=hu", "withdraw": "/order?withdraw=1&lang=en&m=hu", "home": "/?lang=en"}
          and p["load_lt"] == {"detect": "eu", "stored": None, "tryLink": "/try?lang=en", "adopted": "eu", "edition": "eu",
                               "legal": "/terms?lang=en", "withdraw": "/order?withdraw=1&lang=en", "home": "/?lang=en"}, p)
    a = CL["adopt"]
    check("H5 selectable au: links exactly as before; adoptMarket takes any market of the file, never junk",
          a["selectableLinks"] == {"legal": "/terms?lang=en&m=au#australia", "withdraw": "/order?withdraw=1&lang=de&m=au"}
          and a["plainLinks"] == {"legal": "/terms?lang=en#australia", "withdraw": "/order?withdraw=1&lang=de"}
          and a["junk"] == "eu" and a["hu"] == "hu" and a["au"] == {"market": "au", "legal": "/terms?lang=en&m=au"}
          and a["backToEu"] == {"market": "eu", "legal": "/terms?lang=en"}, a)
    check("H6 readWithdrawal keeps the answer's market (none or junk: null)",
          CL["withdraw"] == {"au": "au", "none": None, "bad": None}, CL["withdraw"])
    T = CL["texts"]
    ACCC_SERVICES = ("For major failures with the service, you are entitled: to cancel your service contract with us; and to a "
                     "refund for the unused portion, or to compensation for its reduced value. You are also entitled to be "
                     "compensated for any other reasonably foreseeable loss or damage. If the failure does not amount to a major "
                     "failure, you are entitled to have problems with the service rectified in a reasonable time and, if this is "
                     "not done, to cancel your contract and obtain a refund for the unused portion of the contract.")
    au_en = " ".join(b for b in T["australiaEn"] if isinstance(b, str))
    au_de = " ".join(b for b in T["australiaDe"] if isinstance(b, str))
    check("H7 'Your rights in Australia': the prescribed services remedies word for word; no redo example, no 'cancel and get a "
          "refund' of our own; fitness for any purpose made known",
          ACCC_SERVICES in T["australiaEn"] and "making your file again" not in au_en and "cancel and get a refund" not in au_en
          and "be reasonably fit for any purpose you tell us about or that we describe" in au_en
          and T["australiaEn"][0] == "**Our services come with guarantees that cannot be excluded under the Australian Consumer Law.**",
          T["australiaEn"])
    check("H8 ... German: the same remedies translated, fitness for any purpose made known, no redo example",
          "Bei einem erheblichen Mangel der Leistung (major failure)" in au_de and "für den nicht genutzten Teil" in au_de
          and "für jeden Zweck, den Sie uns mitteilen oder den wir beschreiben" in au_de and "neu erstellen" not in au_de
          and "Geld zurückerhalten" not in au_de, au_de[:900])
    pe, pd = " ".join(T["privacyEn"]), " ".join(T["privacyDe"])
    check("H9 AU privacy: the OAIC only 'if the Australian Privacy Principles apply to us'; 'A$3 million or less' (en, de)",
          "If the Australian Privacy Principles apply to us and you are not satisfied with our answer, you can complain to the "
          "Office of the Australian Information Commissioner" in pe and "A$3 million or less" in pe
          and "Gelten die Australian Privacy Principles für uns und sind Sie mit unserer Antwort nicht zufrieden" in pd
          and "höchstens 3 Millionen australischen Dollar" in pd and "under A$3 million" not in pe, (pe[-700:], pd[-700:]))
    hint = T["hint"]
    # 30efee7: the offer is also made for forints, in en and de (next to A$) and in Lithuanian and Hungarian (no Australian
    # offer there: the Australian pages are English and German only, EDITION_LANGS au); a price in any currency stays out
    hint_all = dict(hint, **T["hintAll"])
    hint_json = json.dumps(hint_all, ensure_ascii=False)
    check("H10 the offer's copy: en and de for A$, no price in it, no dash" " - 0930: plus the forint offer in en and de, and the lt and hu offers (forints only)",
          hint["en"]["aud"]["show"] == "Show prices in A$" and hint["de"]["aud"]["show"] == "Preise in A$ anzeigen"
          and hint["en"]["huf"]["show"] == "Show prices in Ft" and hint["de"]["huf"]["show"] == "Preise in Ft anzeigen"
          and hint["en"]["close"] and hint["de"]["close"] and "eur" not in hint["en"]
          and all(hint_all[l]["label"] and hint_all[l]["close"] and hint_all[l]["huf"]["text"] and hint_all[l]["huf"]["show"]
                  and "eur" not in hint_all[l] for l in ("en", "de", "lt", "hu"))
          and all(hint[l]["aud"]["text"] and hint[l]["aud"]["show"] for l in ("en", "de"))
          and all("aud" not in hint_all[l] for l in ("lt", "hu"))
          and not re.search(r"A\$\s?\d|\d\s?(Ft|HUF|EUR|\u20ac)|[\u20ac]\s?\d", hint_json)
          and not any(d in hint_json for d in DASHES), hint_all)
    eu_terms = json.dumps(T["euTermsEn"], ensure_ascii=False)
    check("H11 the EU terms keep their own texts (the AU fixes did not leak into them)",
          "We will render the file again free of charge" in eu_terms and "For major failures with the service" not in eu_terms
          and "Australian Consumer Law" not in eu_terms, eu_terms[:300])

# ---------------------------------------------------------------------------------------------- I. the built pack
ED = PACK.get("editions", {}).get("au", {})
t_en = ED.get("en", {}).get("terms", {}).get("text", "")
check("I1 the built pack's AU terms (what the email attaches) carry the corrected remedies; the EU terms do not",
      "For major failures with the service, you are entitled:" in t_en and "making your file again" not in t_en
      and "For major failures" not in PACK["docs"]["en"]["terms"]["text"], t_en[:300])

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""), flush=True)
sys.exit(1 if fails else 0)
