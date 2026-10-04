# -*- coding: utf-8 -*-
"""Markets and currencies (eu, lt, au, hu): the one price table (api/_lib/markets.py), the price per market, the
market whitelist at checkout, the Stripe session (currency, amount, metadata, locale, no Adaptive Pricing), the
checks of every paid session (a wrong currency or market refused, an amount mismatch recorded and told), paid.json,
the emails and owner notes in the right currency, the order page and withdrawal replies, the admin row, and the site's
own market code agreeing with the server (src/shared/markets.ts through Vite, client_check.mjs).
Fake Stripe + Resend + legal pack (wave-r-back/pb/harness.py), a local store folder, synthetic keys, no network.
    python test_markets.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, json, time, base64, re, subprocess, secrets, shutil, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(os.path.dirname(HERE))
PB = os.path.join(SP, "wave-r-back", "pb")
sys.path.insert(0, PB)
import harness as H

stub = H.start_stub()
STORE = os.path.join(HERE, "store_markets")
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib import ops
from _lib import markets as MK

RESULTS = []
DASHES = (chr(0x2013), chr(0x2014))
NBSP = " "


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


@contextlib.contextmanager
def hu_paused():
    """Hungary paused the way the owner pauses a market: "selectable": 0 in api/_lib/markets.py. Commit 30efee7 made hu
    selectable (with the Hungarian edition of the legal texts), so the checks that pinned "hu is priced but refused"
    (A3, C1, C2, D9, G5, G6) now pin that rule for a market that is paused instead. The API of this harness runs in this
    process and reads pay.SELECTABLE and pay.MARKETS at every request, so the flip is seen by /api/checkout; it is put
    back on exit, whatever happens."""
    was_flag, was_tuple = pay.MARKETS["hu"]["selectable"], pay.SELECTABLE
    pay.MARKETS["hu"]["selectable"] = 0
    pay.SELECTABLE = tuple(m for m in was_tuple if m != "hu")
    try:
        yield
    finally:
        pay.MARKETS["hu"]["selectable"] = was_flag
        pay.SELECTABLE = was_tuple


H.Fake.legal = None
pay._LEGAL.update(pack=None, t=0.0)

# ---------------------------------------------------------------------------------------------- A. the one table
src = open(os.path.join(H.API, "_lib", "markets.py"), encoding="utf-8").read()
lit = json.loads(src[src.index("\nMARKETS = {") + len("\nMARKETS = "):])
check("A1 markets.py: the MARKETS literal is plain JSON and equals what the server imports", lit == MK.MARKETS == pay.MARKETS,
      (lit, MK.MARKETS))
check("A2 markets and currencies: eu/lt EUR, au AUD, hu HUF; default eu", MK.DEFAULT_MARKET == "eu"
      and {m: v["currency"] for m, v in pay.MARKETS.items()} == {"eu": "eur", "lt": "eur", "au": "aud", "hu": "huf"}, pay.MARKETS)
# 30efee7: hu is selectable now (before: SELECTABLE ("eu", "lt", "au") and hu "selectable": 0). The rule it stays under:
# a selectable market in another currency than the default's has its own edition of the legal texts (the build checks it,
# G7), so hu must be in EDITION_MARKETS with the four languages of its edition, and pausing it (hu_paused) gives back the old list.
with hu_paused():
    paused_selectable = pay.SELECTABLE
check("A3 selectable: eu, lt, au (hu priced but not selectable)" " - 0930: hu is selectable since 30efee7, with its own legal edition; paused (hu_paused) it gives the old list", pay.SELECTABLE == ("eu", "lt", "au", "hu")
      and [pay.MARKETS[m]["selectable"] for m in ("eu", "lt", "au", "hu")] == [1, 1, 1, 1]
      and pay.edition_market("hu") and pay.edition_market("au") and not pay.edition_market("eu") and not pay.edition_market("lt")
      and tuple(pay.edition_langs("hu")) == ("en", "de", "lt", "hu") and paused_selectable == ("eu", "lt", "au"),
      (pay.SELECTABLE, pay.EDITION_MARKETS, pay.EDITION_LANGS, paused_selectable))
want = {"eu": (1997, 2497, 3997, 1500), "lt": (1997, 2497, 3997, 1500), "au": (3900, 4900, 7900, 2900),
        "hu": (699000, 899000, 1399000, 499000)}
check("A4 owner prices per market (Stripe units; HUF forint x 100)",
      all(tuple(pay.price_list(m)[k] for k in pay.PRICE_KEYS) == v for m, v in want.items()), {m: pay.price_list(m) for m in want})
tab = {(m, n, s): pay.price_cents(n, s, m) for m in pay.MARKETS for n in range(1, 9) for s in L.STYLES}
check("A5 price_cents: 1 eye by style, 2 eyes, +extra per eye, every market",
      all(tab[(m, 1, "studio_black")] == want[m][0] and tab[(m, 1, "supernova")] == want[m][1]
          and all(tab[(m, n, s)] == want[m][2] + (n - 2) * want[m][3] for n in range(2, 9) for s in L.STYLES) for m in want),
      {k: v for k, v in tab.items() if k[1] in (1, 2, 8) and k[2] == "studio_black"})
check("A6 examples: A$253 for 8 eyes, 43 930 Ft for 8, 129.97 EUR for 8", tab[("au", 8, "studio_black")] == 25300
      and tab[("hu", 8, "supernova")] == 4393000 and tab[("eu", 8, "deep_nebula")] == 12997)
check("A7 price_cents without a market is the default market (old callers)", pay.price_cents(2, "studio_black") == 3997
      and pay.price_cents(1, "studio_black") == 1997)
try:
    pay.price_cents(1, "studio_black", "zz")
    bad = False
except L.ClientError:
    bad = True
check("A8 price_cents refuses an unknown market", bad)

# ---------------------------------------------------------------------------------------------- B. money text
cases = [((1997, "en", "eur"), "€19.97"), ((1997, "de", "eur"), "19,97 €"), ((3997, "en", None), "€39.97"),
         ((3900, "en", "aud"), "A$39"), ((3900, "de", "aud"), "A$39"), ((25300, "en", "AUD"), "A$253"),
         ((3950, "en", "aud"), "A$39.50"), ((3950, "de", "aud"), "A$39,50"), ((125300, "en", "aud"), "A$1,253"),
         ((699000, "en", "huf"), "6 990 Ft"), ((1399000, "de", "HUF"), "13 990 Ft"), ((4393000, "en", "huf"), "43 930 Ft"),
         ((1997, "en", "xyz"), "€19.97")]
got = {c: pay.price_text(*c) for c, _ in cases}
check("B1 price_text per currency and language (emails)", all(got[c] == w for c, w in cases), got)
at = {c: pay.amount_text(*c) for c in [(3997, "en", "eur"), (3997, "de", None), (7900, "en", "aud"), (1399000, "en", "huf")]}
check("B2 amount_text for the owner: 39.97 EUR, 39,97 EUR, 79.00 AUD, 13990 HUF",
      list(at.values()) == ["39.97 EUR", "39,97 EUR", "79.00 AUD", "13990 HUF"], at)
check("B3 tax_note: EUR/HUF not VAT registered, AUD no GST (en, de)",
      pay.tax_note("eur", "en") == "This is the final price: we are not registered for VAT, so no VAT is charged."
      and "keine Umsatzsteuer" in pay.tax_note("eur", "de") and pay.tax_note("aud", "en") == "This is the total price: no GST is charged."
      and "keine GST" in pay.tax_note("aud", "de") and "VAT" in pay.tax_note("huf", "en") and "GST" not in pay.tax_note("huf", "en"))
check("B4 no text anywhere says 'Tax invoice' or 'no refunds'", all(("Tax invoice" not in x and "no refund" not in x.lower())
      for x in [pay.tax_note(c, l) for c in ("eur", "aud", "huf") for l in ("en", "de")]))
check("B5 stripe_locale: en-GB for Australia's English, the page language otherwise",
      pay.stripe_locale({"lang": "en", "market": "au"}) == "en-GB" and pay.stripe_locale({"lang": "de", "market": "au"}) == "de"
      and pay.stripe_locale({"lang": "en", "market": "eu"}) == "en" and pay.stripe_locale({"lang": "de"}) == "de"
      and pay.stripe_locale({"lang": "en", "market": "lt"}) == "en")

# ---------------------------------------------------------------------------------------------- C. GET /api/checkout
c, j = get("/api/checkout")
with hu_paused():       # 30efee7: hu is offered now; a paused hu is what "hu not in markets" pinned before
    cP, jP = get("/api/checkout")
    hintP = get("/api/checkout", {"x-vercel-ip-country": "HU"})[1]
check("C1 GET: legacy currency/prices = eu, markets eu/lt/au only, in their currencies" " - 0930: hu is listed now (30efee7); with hu paused it is the old eu/lt/au list",
      c == 200 and j["currency"] == "EUR" and j["prices"]["two_eyes"] == 3997 and j["market"] == "eu"
      and sorted(j["markets"]) == ["au", "eu", "hu", "lt"] and j["markets"]["au"] == {"currency": "AUD", "prices": pay.price_list("au")}
      and j["markets"]["hu"] == {"currency": "HUF", "prices": pay.price_list("hu")}
      and j["markets"]["lt"]["currency"] == "EUR"
      and cP == 200 and sorted(jP["markets"]) == ["au", "eu", "lt"] and "hu" not in jP["markets"]
      and jP["currency"] == "EUR" and jP["prices"]["two_eyes"] == 3997 and jP["market"] == "eu", (j, jP))
hints = {cc: get("/api/checkout", {"x-vercel-ip-country": cc})[1] for cc in ("AU", "au", "HU", "LT", "DE", "", "A1B")}
check("C2 country hint: AU suggests au; HU (not selectable), LT (same currency), DE: none; junk: no country" " - 0930: HU suggests hu now (30efee7); with hu paused it suggests none",
      hints["AU"]["country"] == "AU" and hints["AU"]["suggest"] == "au" and hints["au"]["suggest"] == "au"
      and hints["HU"]["country"] == "HU" and hints["HU"]["suggest"] == "hu"
      and hintP["country"] == "HU" and hintP["suggest"] is None
      and hints["LT"]["suggest"] is None and hints["DE"]["suggest"] is None
      and hints[""]["country"] == "" and hints["A1B"]["country"] == "" and get("/api/checkout")[1]["country"] == "",
      {k: (v.get("country"), v.get("suggest")) for k, v in hints.items()})

# ---------------------------------------------------------------------------------------------- D. checkout per market
oA, kA = new_order(2)
n_creates = len(H.Fake.creates)
c, j = checkout(oA, kA, 1, "studio_black", "en", market="au")
p, hd = H.Fake.creates[-1]
check("D1 au, 1 eye Studio Black: A$39 (3900 aud), reply AUD and market au", c == 200 and j["amount"] == 3900
      and j["currency"] == "AUD" and j["market"] == "au", (c, j))
check("D2 Stripe: currency aud, unit_amount 3900, locale en-GB, no Adaptive Pricing, one item",
      p["line_items[0][price_data][currency]"] == "aud" and p["line_items[0][price_data][unit_amount]"] == "3900"
      and p["locale"] == "en-GB" and p["adaptive_pricing[enabled]"] == "false" and not any(k.startswith("line_items[1]") for k in p), p)
check("D3 metadata: market au, currency aud, amount 3900 (server-written)", p["metadata[market]"] == "au"
      and p["metadata[currency]"] == "aud" and p["metadata[amount]"] == "3900", {k: v for k, v in p.items() if k.startswith("metadata")})
check("D4 cancel_url carries m=au; success_url as before (the order page reads the market from the server)",
      p["cancel_url"] == f"https://snapeyes.com/try?checkout=cancelled&o={oA}&lang=en&m=au"
      and p["success_url"] == f"https://snapeyes.com/order?o={oA}&k={kA}&lang=en&s={{CHECKOUT_SESSION_ID}}", (p["cancel_url"], p["success_url"]))
rec = read_json(f"orders/{oA}/order.json")
check("D5 order.json checkout: amount, currency aud, market au, spec.market au", rec["checkout"]["amount"] == 3900
      and rec["checkout"]["currency"] == "aud" and rec["checkout"]["market"] == "au" and rec["checkout"]["spec"]["market"] == "au",
      rec["checkout"])
au_prices = {}
for n, st in ((1, "celestial_gold"), (2, "studio_black")):
    c, j = checkout(oA, kA, n, st, "en", market="au")
    au_prices[(n, st)] = (c, j.get("amount"), j.get("currency"))
check("D6 au prices: A$49 art background, A$79 two eyes", au_prices == {(1, "celestial_gold"): (200, 4900, "AUD"),
      (2, "studio_black"): (200, 7900, "AUD")}, au_prices)
c, j = checkout(oA, kA, 2, "studio_black", "de", market="au")
p = H.Fake.creates[-1][0]
check("D7 au in German: Stripe page in de (Stripe has no en-AU; German stays German)", c == 200 and p["locale"] == "de"
      and p["cancel_url"].endswith("&lang=de&m=au"), p["locale"])
c, j = checkout(oA, kA, 2, "studio_black", "en", market="au", amount=1, price=1, unit_amount=1, currency="usd", total=1)
p = H.Fake.creates[-1][0]
check("D8 tampered amount/currency fields ignored: still 7900 aud", c == 200 and j["amount"] == 7900 and j["currency"] == "AUD"
      and p["line_items[0][price_data][currency]"] == "aud" and p["line_items[0][price_data][unit_amount]"] == "7900", (c, j))
refused = {}
hu_p = None
for v in ("hu", "zz", "AU", "", None, 7, ["au"], {"m": "au"}, "eu ", "au;eu"):
    before = len(H.Fake.creates)
    body = {} if v is None else {"market": v}
    c, j = checkout(oA, kA, 2, "studio_black", "en", **body)
    refused[repr(v)] = (c, len(H.Fake.creates) - before, j.get("currency"))
    if v == "hu" and len(H.Fake.creates) > before:
        hu_p = H.Fake.creates[-1][0]
# 30efee7: hu is selectable, so it sells (forints, its own cancel_url) like lt does in D12; paused, it is refused as before
paused_hu = {}
with hu_paused():
    before = len(H.Fake.creates)
    c, j = checkout(oA, kA, 2, "studio_black", "en", market="hu")
    paused_hu = (c, len(H.Fake.creates) - before)
check("D9 market whitelist: hu, zz, AU, lists, objects, padded or joined values -> 400, no Stripe session" " - 0930: hu sells now (200, HUF; 30efee7), it is refused only while paused",
      all(refused[repr(v)][:2] == (400, 0) for v in ("zz", "AU", 7, ["au"], {"m": "au"}, "eu ", "au;eu"))
      and refused["'hu'"] == (200, 1, "HUF") and hu_p is not None
      and hu_p["line_items[0][price_data][currency]"] == "huf" and hu_p["line_items[0][price_data][unit_amount]"] == "1399000"
      and hu_p["metadata[market]"] == "hu" and hu_p["metadata[currency]"] == "huf"
      and hu_p["cancel_url"] == f"https://snapeyes.com/try?checkout=cancelled&o={oA}&lang=en&m=hu"
      and paused_hu == (400, 0), (refused, paused_hu, hu_p))
check("D10 no market or an empty one: the default market eu (3997 EUR), exactly as before",
      refused["''"] == (200, 1, "EUR") and refused["None"] == (200, 1, "EUR"), refused)
p = H.Fake.creates[-1][0]
check("D11 eu session: eur, locale = page language, cancel_url without m (unchanged)", p["line_items[0][price_data][currency]"] == "eur"
      and p["locale"] == "en" and p["cancel_url"] == f"https://snapeyes.com/try?checkout=cancelled&o={oA}&lang=en"
      and p["metadata[market]"] == "eu" and p["metadata[currency]"] == "eur", p)
oL, kL = new_order(1)
c, j = checkout(oL, kL, 1, "supernova", "de", market="lt")
p = H.Fake.creates[-1][0]
check("D12 lt: the euro prices (24.97), market lt, cancel_url m=lt, locale de", c == 200 and j["amount"] == 2497
      and j["currency"] == "EUR" and j["market"] == "lt" and p["line_items[0][price_data][currency]"] == "eur"
      and p["cancel_url"].endswith("&lang=de&m=lt") and p["locale"] == "de" and p["metadata[market]"] == "lt", (c, j))

# ---------------------------------------------------------------------------------------------- E. paying: webhook checks
# the AU order: its latest session becomes the 2-eye A$79 one again (the whitelist checks above left an eu one last)
c, j = checkout(oA, kA, 2, "studio_black", "en", market="au")
sidA = sid_of(oA)
check("E0 the AU order's latest session is 7900 aud", H.Fake.sessions[sidA]["currency"] == "aud"
      and H.Fake.sessions[sidA]["amount_total"] == 7900 and H.Fake.sessions[sidA]["metadata"]["market"] == "au")
recA = read_json(f"orders/{oA}/order.json")
sess = H.pay_session(sidA, "aussie@example.com")
# a paid session of ours in the wrong currency: refused, not recorded, the owner told once
n0 = len(H.Fake.emails)
wrong = dict(sess, currency="eur")
c, j = hook(wrong)
c2, j2 = hook(wrong)
notes = [m for m in mails_to("info@snapeyes.com", n0) if "unexpected currency" in m["subject"]]
check("E1 webhook: a paid session of ours in eur for market au -> ignored, not paid, owner told once",
      c == 200 and j.get("ignored") == "session does not match" and c2 == 200 and not exists(f"orders/{oA}/paid.json")
      and len(notes) == 1 and oA in notes[0]["subject"] and "NOT recorded" in notes[0]["text"], (c, j, [m["subject"] for m in notes]))
check("E2 session_matches: the market's currency and the named currency must agree",
      not pay.session_matches(dict(sess, metadata=dict(sess["metadata"], market="hu")), oA, recA)
      and not pay.session_matches(dict(sess, metadata=dict(sess["metadata"], market="zz")), oA, recA)
      and not pay.session_matches(dict(sess, metadata=dict(sess["metadata"], currency="eur")), oA, recA)
      and not pay.session_matches(dict(sess, currency="usd"), oA, recA)
      and not pay.session_matches(dict(sess, currency="AUD ", metadata=dict(sess["metadata"])), oA, recA)
      and pay.session_matches(sess, oA, recA) and pay.session_matches(dict(sess, currency="AUD"), oA, recA))
old_style = {k: v for k, v in sess["metadata"].items() if k not in ("market", "currency")}
check("E3 a session from before markets (no market in its metadata) counts as eu: eur yes, aud no",
      pay.session_matches(dict(sess, currency="eur", metadata=old_style), oA, recA)
      and not pay.session_matches(dict(sess, currency="aud", metadata=old_style), oA, recA))
c, j = hook(dict(sess, metadata=dict(sess["metadata"], market="hu")))
c3, j3 = hook(dict(sess, metadata=dict(sess["metadata"], market="zz")))
check("E4 webhook: market hu or unknown on an aud session -> ignored", c == 200 and j.get("ignored") == "session does not match"
      and c3 == 200 and j3.get("ignored") == "session does not match" and not exists(f"orders/{oA}/paid.json"), (j, j3))
n0 = len(H.Fake.emails)
c, j = hook(sess)
paid = read_json(f"orders/{oA}/paid.json")
check("E5 the right AUD session: paid, currency aud, market au, 7900, no mismatch", c == 200 and j.get("new") is True
      and paid["currency"] == "aud" and paid["market"] == "au" and paid["amount_total"] == 7900
      and paid["spec"]["market"] == "au" and "amount_mismatch" not in paid, (c, j, paid))
conf = mails_to("aussie@example.com", n0)
t = conf[0]["text"] if conf else ""
check("E6 confirmation email (en): A$79, total price, no GST; no euro sign, no VAT sentence, never 'Tax invoice'",
      len(conf) == 1 and "Price: A$79. This is the total price: no GST is charged." in t and "€" not in t.split("______")[0]
      and "VAT" not in t.split("______")[0] and "Tax invoice" not in t, t[:1500])
with open(os.path.join(HERE, "sample_au_confirmation.txt"), "w", encoding="utf-8") as f:
    f.write(t.split("______")[0])
note = [m for m in mails_to("info@snapeyes.com", n0) if m["subject"].startswith("SnapEyes: new order")]
check("E7 owner note: 79.00 AUD, market au", len(note) == 1 and note[0]["subject"].endswith("79.00 AUD")
      and "Market: au" in note[0]["text"] and "CHECK THE AMOUNT" not in note[0]["text"], [m["subject"] for m in note])
check("E8 emails carry no en or em dash", all(not any(d in m["text"] for d in DASHES) for m in conf + note))
c, j = get(f"/api/order?o={oA}&k={kA}")
check("E9 order page status: currency AUD, market au, amount 7900", c == 200 and j.get("currency") == "AUD"
      and j.get("market") == "au" and j.get("amount") == 7900, (c, j))

# German AU order: A$ in the German email with the GST sentence
oD, kD = new_order(1, "de")
c, j = checkout(oD, kD, 1, "studio_black", "de", market="au")
sD = H.pay_session(sid_of(oD), "kaenguru@example.com")
n0 = len(H.Fake.emails)
c, j = hook(sD)
t = (mails_to("kaenguru@example.com", n0) or [{"text": ""}])[0]["text"]
check("E10 German confirmation for au: Preis: A$39. Gesamtpreis, keine GST", c == 200
      and "Preis: A$39. Das ist der Gesamtpreis: Es wird keine GST berechnet." in t and "Umsatzsteuer" not in t.split("______")[0], t[:1200])

# an EUR order through the same path is unchanged
oE, kE = new_order(1, "de")
c, j = checkout(oE, kE, 1, "studio_black", "de")
sE = H.pay_session(sid_of(oE), "euro@example.com")
n0 = len(H.Fake.emails)
c, j = hook(sE)
t = (mails_to("euro@example.com", n0) or [{"text": ""}])[0]["text"]
pE = read_json(f"orders/{oE}/paid.json")
check("E11 eu order: 19,97 EUR text as before, paid.json market eu", c == 200 and pE["market"] == "eu" and pE["currency"] == "eur"
      and "Preis: 19,97 €. Das ist der Endpreis: Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet." in t, t[:1200])

# an amount the server did not price: recorded, delivered, the owner told
oM, kM = new_order(1)
c, j = checkout(oM, kM, 1, "studio_black", "en", market="au")
sM = H.pay_session(sid_of(oM), "mismatch@example.com")
sM["amount_total"] = 100
n0 = len(H.Fake.emails)
c, j = hook(sM)
pM = read_json(f"orders/{oM}/paid.json")
nM = [m for m in mails_to("info@snapeyes.com", n0) if m["subject"].startswith("SnapEyes: new order")]
check("E12 amount mismatch (100 for a 3900 aud order): recorded with expected 3900 aud, owner told",
      c == 200 and pM["amount_mismatch"] == {"expected": 3900, "currency": "aud", "market": "au"}
      and len(nM) == 1 and "CHECK THE AMOUNT" in nM[0]["text"] and "3900" not in nM[0]["subject"] and "39.00 AUD" in nM[0]["text"],
      (pM.get("amount_mismatch"), [m["text"][:400] for m in nM]))

# a HUF order (hu is not selectable, so its session is made the way /api/checkout would make it, straight at the stub)
oH, kH = new_order(2, "en")
recH = read_json(f"orders/{oH}/order.json")
specH = {"eyes": 2, "style": "supernova", "layout": "duo", "names": "", "title": "", "lang": "en", "market": "hu"}
consentH = {"version": pay.CONSENT_VERSION, "at": pay.iso(), "lang": "en", "text": pay.CONSENT_TEXT["en"]}
pay.start_clock()
sessH = pay.create_session(oH, kH, specH, pay.price_cents(2, "supernova", "hu"), consentH, int(time.time()) + 7200)
pH = H.Fake.creates[-1][0]
check("E13 a hu session: huf 1399000 (13 990 Ft x 100), locale en", pH["line_items[0][price_data][currency]"] == "huf"
      and pH["line_items[0][price_data][unit_amount]"] == "1399000" and pH["metadata[market]"] == "hu" and pH["locale"] == "en", pH)
recH["checkout"] = {"session_id": sessH["id"], "amount": 1399000, "currency": "huf", "market": "hu", "spec": specH,
                    "consent": dict(consentH, text_sha256="x")}
store.put(f"orders/{oH}/order.json", store.json_bytes(recH), "application/json", upsert=True)
sHp = H.pay_session(sessH["id"], "magyar@example.com")
n0 = len(H.Fake.emails)
c, j = hook(sHp)
pHp = read_json(f"orders/{oH}/paid.json") if exists(f"orders/{oH}/paid.json") else {}
t = (mails_to("magyar@example.com", n0) or [{"text": ""}])[0]["text"]
nH = [m for m in mails_to("info@snapeyes.com", n0) if m["subject"].startswith("SnapEyes: new order")]
check("E14 a paid hu session still counts (a known market): paid huf, email 13 990 Ft, owner 13990 HUF",
      c == 200 and pHp.get("currency") == "huf" and pHp.get("market") == "hu" and "amount_mismatch" not in pHp
      and "Price: 13 990 Ft." in t and len(nH) == 1 and nH[0]["subject"].endswith("13990 HUF"), (c, j, pHp, t[:900]))
c, j = hook(dict(sHp, currency="eur"))
check("E15 ... but a hu session paid in eur is refused (the currency of its market)", c == 200
      and j.get("ignored") == "session does not match" and not pay.session_matches(dict(sHp, currency="eur"), oH, recH), (c, j))

# unpaid status with a checkout names its currency
oU, kU = new_order(1)
checkout(oU, kU, 1, "studio_black", "en", market="au")
c, j = get(f"/api/order?o={oU}&k={kU}")
check("E16 unpaid status: checkout amount 3900, currency AUD, market au", c == 200 and j["state"] == "unpaid"
      and j["checkout"] == {"eyes": 1, "style": "studio_black", "amount": 3900, "currency": "AUD", "market": "au"}, j.get("checkout"))

# ---------------------------------------------------------------------------------------------- F. withdrawal and admin
oW, kW = new_order(1)
checkout(oW, kW, 1, "celestial_gold", "en", market="au")
sW = H.pay_session(sid_of(oW), "withdraw.au@example.com")
hook(sW)
n0 = len(H.Fake.emails)
c, j = post("/api/order", {"action": "withdraw", "order": oW, "k": kW, "name": "Bruce Test", "email": "withdraw.au@example.com",
                           "lang": "en"})
w = j.get("withdrawal") or {}
rc = mails_to("withdraw.au@example.com", n0)
on = [m for m in mails_to("info@snapeyes.com", n0) if "withdrawal for order" in m["subject"]]
check("F1 AU withdrawal: reply amount 4900 AUD, receipt names A$49, owner note 49.00 AUD",
      c == 200 and w.get("state") == "withdrawn" and w.get("amount") == 4900 and w.get("currency") == "AUD"
      and len(rc) == 1 and "A$49" in rc[0]["text"] and "€" not in rc[0]["text"]
      and len(on) == 1 and "49.00 AUD" in on[0]["subject"], (c, j, [m["subject"] for m in on], rc[0]["text"][:600] if rc else ""))
pay.start_clock()
row = ops.order_row(oA)
rowE = ops.order_row(oE)
rowU = ops.order_row(oU)
check("F2 admin rows: currency and market per order (AUD au paid, EUR eu paid, AUD au unpaid checkout)",
      row["currency"] == "AUD" and row["market"] == "au" and row["amount"] == 7900
      and rowE["currency"] == "EUR" and rowE["market"] == "eu" and rowU["currency"] == "AUD" and rowU["market"] == "au",
      (row, rowE, rowU))

# ---------------------------------------------------------------------------------------------- G. the site agrees
# The site's own market code read against a markets.py whose hu is paused ("selectable": 0): 30efee7 made hu selectable, so the
# expectations that said "hu is ignored in links and detection" (G5, G6) moved to this copy; the copy holds only
# src/shared/markets.ts (no other import) and a markets.py that is the real table with hu paused. client_check.mjs reads it as argv[2].
ALT = os.path.join(HERE, "store_markets_hu_paused")
shutil.rmtree(ALT, ignore_errors=True)
os.makedirs(os.path.join(ALT, "src", "shared"))
os.makedirs(os.path.join(ALT, "api", "_lib"))
shutil.copy(os.path.join(H.REPO, "src", "shared", "markets.ts"), os.path.join(ALT, "src", "shared", "markets.ts"))
alt_markets = json.loads(json.dumps(MK.MARKETS))
alt_markets["hu"]["selectable"] = 0
with open(os.path.join(ALT, "api", "_lib", "markets.py"), "w", encoding="utf-8") as f:
    f.write(f'DEFAULT_MARKET = "{MK.DEFAULT_MARKET}"' + chr(10) + "MARKETS = " + json.dumps(alt_markets, indent=4) + chr(10))
r = subprocess.run(["node", os.path.join(HERE, "client_check.mjs"), ALT], cwd=H.REPO, capture_output=True, text=True,
                   encoding="utf-8", timeout=300)
try:
    cl = json.loads(r.stdout)
except ValueError:
    cl = None
check("G0 the site's market code loads through Vite", cl is not None, (r.returncode, r.stderr[-800:]))
if cl:
    check("G1 the site reads the same table as the server", cl["defaultMarket"] == pay.DEFAULT_MARKET
          and cl["markets"] == pay.MARKETS and cl["selectable"] == list(pay.SELECTABLE), cl["markets"])
    diff = [(m, n, s, cl["table"][m][str(n)][s], pay.price_cents(n, s, m)) for m in pay.MARKETS for n in range(1, 9)
            for s in L.STYLES if cl["table"][m][str(n)][s] != pay.price_cents(n, s, m)]
    check("G2 client priceMinor == server price_cents for every market, 1-8 eyes, every style", not diff, diff[:5])
    mdiff = [(mi, cu, lg, txt, pay.price_text(mi, lg, cu)) for mi, cu, lg, txt in cl["money"]
             if txt.replace(NBSP, " ") != pay.price_text(mi, lg, cu)]
    check("G3 client money() writes every price as the emails do (spaces aside)", not mdiff, mdiff)
    check("G4 server price lists override only their own keys; bad values ignored; legacy list only for the default",
          cl["priceWithServerList"] == 7000 and cl["priceWithBadList"] == 3900
          and cl["serverPrices"] == {"own": {"two_eyes": 7900}, "legacyDefault": {"two_eyes": 3997}, "legacyOther": None}, cl)
    # 30efee7: hu is selectable, so its links carry m=hu like au's; with hu paused (cl["paused"]) they stay plain, as hu's did before
    check("G5 links: m= only for a selectable non-default market, before #section; the printed address never has it",
          cl["links"] == {"legalPlain": "/terms?lang=en#prices", "withdrawPlain": "/order?withdraw=1&lang=de",
                          "address": "snapeyes.com/order?withdraw=1&lang=de", "au": "/terms?lang=en&m=au#prices",
                          "auNoQuery": "/try?m=au", "eu": "/terms?lang=en", "hu": "/terms?lang=en&m=hu", "bogus": "/terms?lang=en"}
          and cl["paused"]["selectable"] == ["eu", "lt", "au"]
          and cl["paused"]["links"] == {"au": "/terms?lang=en&m=au#prices", "hu": "/terms?lang=en", "eu": "/terms?lang=en",
                                        "bogus": "/terms?lang=en"},
          (cl["links"], cl["paused"]))
    # 30efee7: hu is selectable, so a hu link or a stored hu is taken and remembered like au and lt; with hu paused
    # (cl["paused"]) both are ignored exactly as before (the market is eu, the stored value is left as it was)
    check("G6 detectMarket: URL > stored > eu; hu and junk ignored; a URL market is remembered, eu clears it" " - 0930: a hu link or a stored hu is taken now (30efee7), ignored only while hu is paused",
          cl["detect"] == {"url_au": {"market": "au", "stored": "au"}, "url_lt": {"market": "lt", "stored": "lt"},
                           "url_hu": {"market": "hu", "stored": "hu"}, "url_bogus": {"market": "eu", "stored": None},
                           "stored_au": {"market": "au", "stored": "au"}, "stored_hu": {"market": "hu", "stored": "hu"},
                           "url_beats_store": {"market": "eu", "stored": None}, "nothing": {"market": "eu", "stored": None}}
          and cl["paused"]["detect"] == {"url_au": {"market": "au", "stored": "au"},
                                         "url_hu_ignored": {"market": "eu", "stored": None},
                                         "stored_hu_ignored": {"market": "eu", "stored": "hu"}},
          (cl["detect"], cl["paused"]["detect"]))
    check("G7a admin revenue summed per currency (EUR, AUD, HUF apart; a row without currency is EUR)",
          cl["revenue"] == {"eur": {"live": 3997 + 1997 + 2497, "test": 0, "n": 3}, "aud": {"live": 7900, "test": 3900, "n": 1},
                            "huf": {"live": 1399000, "test": 0, "n": 1}}, cl["revenue"])
    check("G7b admin amounts in their currency", [x.replace(NBSP, " ") for x in cl["fmtMoney"]]
          == ["39,97 €", "79,00 A$", "13 990 Ft", "39,97 €", "19,97 €", "-"], cl["fmtMoney"])
r = subprocess.run(["node", os.path.join(H.REPO, "scripts", "check_prices.mjs")], cwd=H.REPO, capture_output=True, text=True,
                   encoding="utf-8", timeout=120)
check("G7 npm run check:prices passes on the repo", r.returncode == 0 and "price check ok" in r.stdout, (r.stdout, r.stderr))
PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
check("G8 the built legal pack's links carry no market", "m=" not in json.dumps([PACK["docs"][l][d]["url"]
      for l in PACK["docs"] for d in PACK["docs"][l]]))

# ---------------------------------------------------------------------------------------------- H. hygiene
bad = []
for f in ("api/_lib/markets.py", "api/_lib/pay.py", "api/checkout.py", "api/order.py", "api/stripe_webhook.py", "api/_lib/ops.py",
          "api/_lib/withdraw.py", "api/_lib/cleanup.py", "scripts/order_admin.py", "scripts/check_prices.mjs",
          "scripts/check_prices.d.mts", "src/shared/markets.ts", "src/shared/useMarket.ts", "vite.config.ts"):
    t = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in t for ch in DASHES) or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in t):
        bad.append(f)
check("H1 no en/em dashes or control characters in the market files", not bad, bad)

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
api.shutdown()
stub.shutdown()
sys.exit(1 if fails else 0)
