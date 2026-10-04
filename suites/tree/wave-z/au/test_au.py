# -*- coding: utf-8 -*-
"""The Australian market (build step 4): the Australian edition of the legal texts (terms with "Your rights in
Australia", withdrawal framed as EU law, privacy and imprint), its checkout consent (client = server, recorded,
quoted), Stripe (en-GB, its own submit note), the confirmation email with an "Invoice" (never "Tax invoice") and the
ACL block, the legal pack's "au" edition (required, never swapped for the EU one), the withdrawal receipts, the landing
and order page lines; and that the EU edition, EU emails and EU checkout are exactly as before (the snapshot
eu_before.json and the core's own pay.py / withdraw.py of before this step, loaded side by side).
Fake Stripe + Resend + legal pack (wave-r-back/pb/harness.py), a local store folder, synthetic keys, no network.
    python test_au.py        PASS/FAIL per check, exit 1 on any failure"""
# 0930 refresh (2026-09-30). Two commits changed the product on purpose and 11 checks (A1 A3 A5 B1 B2 B3 C2 D2 E1 E8 G1) still
# pinned the old behaviour; every one was triaged STALE (none is a defect) against the repo and moved to the new behaviour, each
# keeping its id and the old name as the start of its name, with the reason added after " - 0930:":
#   30efee7 (Lithuanian and Hungarian, Hungary selectable): the consent version is 2026-09-30.2 (the lt and hu checkbox texts were
#     added, the en, de and AU texts are the ones of 2026-09-30.1); hu is an edition market of its own (the EU texts with the
#     forint prices; api/_lib/pay.py EDITION_MARKETS = ("au", "hu"), ACL_MARKETS stays ("au",)); the EU terms name four contract
#     languages (the Australian ones stay English and German: its pages exist in those two only); the EU texts gained lt and hu
#     editions; the pack's seller holds lt and hu lines and the pack an editions.hu part; the privacy sentence on the language
#     switch names the language code instead of "en" or "de".
#   1acef38 (price experiments): the EU and Australian terms gained the standard price list sentence; the EU privacy policy gained
#     the anonymous visitor number and two sentences that name the price test (the events, the data passed to Stripe).
# eu_before.json stays the snapshot of the EU edition from before the Australian step (the base of the allowed differences).
# eu_1acef38.json is the EXACT pin of the EU edition (en, de) and of the checkbox wording (en, de, lt, hu) as of 1acef38, so a later
# accidental change still fails; the difference between the two snapshots must be exactly the listed one (doc_diff in section B).
import os, sys, json, time, re, subprocess, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(os.path.dirname(HERE))
PB = os.path.join(SP, "wave-r-back", "pb")
sys.path.insert(0, PB)
import harness as H

stub = H.start_stub()
STORE = os.path.join(HERE, "store_au")
H.setup_env(STORE, stub.server_address[1])
api = H.start_api()
BASE = f"http://127.0.0.1:{api.server_address[1]}"

import requests
sys.path.insert(0, H.API)
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib import ops
from _lib import withdraw as W


def load_before(name):
    """The core's module of before this step (wave-z/au/before), as part of the _lib package."""
    path = os.path.join(HERE, "before", "api", "_lib", name + ".py")
    spec = importlib.util.spec_from_file_location("_lib." + name + "_before", path)
    m = importlib.util.module_from_spec(spec)
    m.__package__ = "_lib"
    spec.loader.exec_module(m)
    return m


PAY0 = load_before("pay")
W0 = load_before("withdraw")

RESULTS = []
DASHES = (chr(0x2013), chr(0x2014))
FORBIDDEN = [re.compile(p, re.I) for p in (r"\bno refunds?\b", r"non-?refundable", r"all sales (are )?final",
                                            r"tax invoice", r"not refundable", r"refunds? (are|is) not")]
AMERICAN = re.compile(r"\b(color|colors|personaliz\w*|Mom|Moms|jewelry|center|favorite|license)\b")
ACCC = "Our services come with guarantees that cannot be excluded under the Australian Consumer Law."


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:900]}"), flush=True)


def bad_words(text):
    return [p.pattern for p in FORBIDDEN if p.search(text)]


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
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


def local(path):
    return os.path.join(STORE, *path.split("/"))


def read_json(path):
    with open(local(path), encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    with open(local(path), "w", encoding="utf-8") as f:
        json.dump(obj, f)


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


def set_pack(pack):
    H.Fake.legal = json.loads(json.dumps(pack))
    pay._LEGAL.update(pack=None, t=0.0, failed=0.0)


def paid_order(market, lang, email, eyes=1, style="studio_black"):
    """An order paid through the webhook: (order, k, paid.json, the customer's emails)."""
    o, k = new_order(eyes, lang)
    c, j = checkout(o, k, eyes, style, lang, **({"market": market} if market else {}))
    assert c == 200, (c, j)
    n0 = len(H.Fake.emails)
    c, j = hook(H.pay_session(sid_of(o), email))
    assert c == 200, (c, j)
    return o, k, read_json(f"orders/{o}/paid.json"), mails_to(email, n0)


PACK = json.load(open(os.path.join(H.REPO, "dist", "legal", "order-mail.json"), encoding="utf-8"))
PACK_AUTO = dict(PACK, making_start="after_confirmation")
EU_BEFORE = json.load(open(os.path.join(HERE, "eu_before.json"), encoding="utf-8"))
EU_NOW = json.load(open(os.path.join(HERE, "eu_1acef38.json"), encoding="utf-8"))   # 0930 refresh: the EU edition as of 1acef38
CONSENT_NOW = "2026-09-30.2"    # 0930 refresh: the consent version since 30efee7 (the lt and hu texts added; en, de, AU as of .1)
LANG2 = ("en", "de")            # the two languages the snapshots of before the Lithuanian and Hungarian work have
set_pack(PACK)

r = subprocess.run(["node", os.path.join(HERE, "au_client_check.mjs")], cwd=H.REPO, capture_output=True, text=True,
                   encoding="utf-8", timeout=300)
try:
    CL = json.loads(r.stdout)
except ValueError:
    CL = None
check("A0 the site's legal editions load through Vite", CL is not None, (r.returncode, r.stderr[-900:]))
if CL is None:
    sys.exit(1)
EDI = CL["editions"]

# ---------------------------------------------------------------------------------------------- A. one wording, two sides
check("A1 consent version: server = client, bumped (2026-09-30.1); LEGAL_UPDATED 2026-09-30 = pack updated"
      " - 0930: bumped again by 30efee7 (lt and hu texts), now 2026-09-30.2; 2026-09-30.1 is still quoted (A3, H1)",
      pay.CONSENT_VERSION == CL["consentVersion"] == CONSENT_NOW and CONSENT_NOW != PAY0.CONSENT_VERSION
      and CL["legalUpdated"] == "2026-09-30" == PACK["updated"],
      (pay.CONSENT_VERSION, CL["consentVersion"], CL["legalUpdated"], PACK["updated"]))
check("A2 AU checkbox: server CONSENT_TEXT_AU = client CHECKOUT_LEGAL_AU, en and de",
      all(pay.CONSENT_TEXT_AU[l] == CL["checkoutAu"][l]["withdrawalConsent"] for l in ("en", "de")),
      (pay.CONSENT_TEXT_AU, {l: CL["checkoutAu"][l]["withdrawalConsent"] for l in ("en", "de")}))
check("A3 EU checkbox and checkout wording exactly as before (text, and the old version still quotes it)"
      " - 0930: en and de word for word as before, lt and hu added by 30efee7 and pinned whole (client = server in all four), "
      "the old versions still quote the en and de text",
      # English and German: as before the AU step, on the page and on the server
      all(CL["checkoutEu"][l] == EU_BEFORE["checkout"][l] for l in LANG2)
      and all(pay.CONSENT_TEXT[l] == PAY0.CONSENT_TEXT[l] for l in LANG2)
      # the four languages: the page's whole wording is the pin of 1acef38, and the server records the page's checkbox text
      and sorted(CL["checkoutEu"]) == ["de", "en", "hu", "lt"] == sorted(pay.CONSENT_TEXT) and CL["checkoutEu"] == EU_NOW["checkout"]
      and all(pay.CONSENT_TEXT[l] == CL["checkoutEu"][l]["withdrawalConsent"] for l in ("en", "de", "lt", "hu"))
      # the versions: the old ones still quote what their customers ticked (en, de), the current one all four languages
      and pay.CONSENT_TEXTS[PAY0.CONSENT_VERSION] == PAY0.CONSENT_TEXT and pay.CONSENT_TEXTS["2026-09-30.1"] == PAY0.CONSENT_TEXT
      and pay.CONSENT_TEXTS[pay.CONSENT_VERSION] == pay.CONSENT_TEXT,
      (sorted(CL["checkoutEu"]), sorted(pay.CONSENT_TEXT), CL["checkoutEu"] == EU_NOW["checkout"]))
au_en = pay.CONSENT_TEXT_AU["en"]
check("A4 AU checkbox keeps both EU elements and the ACL (express start before the period ends, losing the right, "
      "no change-of-mind cancelling, ACL not affected)",
      "expressly agree" in au_en and "before the withdrawal period ends" in au_en and "I lose my right of withdrawal" in au_en
      and "can't cancel for a change of mind" in au_en and "doesn't affect my rights under the Australian Consumer Law" in au_en
      and "ausdrücklich zu" in pay.CONSENT_TEXT_AU["de"] and "vor Ablauf der Widerrufsfrist" in pay.CONSENT_TEXT_AU["de"]
      and "mein Widerrufsrecht verliere" in pay.CONSENT_TEXT_AU["de"] and "Australian Consumer Law" in pay.CONSENT_TEXT_AU["de"], au_en)
check("A5 editions: au reads the Australian texts; eu, lt, hu and unknown the EU ones; server ACL_MARKETS = client"
      " - 0930: hu now reads the Hungarian edition (30efee7: the EU texts with forint prices, not the ACL one), "
      "server EDITION_MARKETS = client",
      CL["edition"] == {"eu": "eu", "lt": "eu", "au": "au", "hu": "hu", "zz": "eu"} and pay.ACL_MARKETS == ("au",)
      and CL["editionMarkets"] == {"au": "au", "hu": "hu"} and tuple(CL["editionMarkets"]) == pay.EDITION_MARKETS
      and tuple(m for m in CL["edition"] if CL["edition"][m] == "au") == pay.ACL_MARKETS
      and pay.acl_market("au") and not pay.acl_market("eu") and not pay.acl_market(None) and not pay.acl_market("AU")
      and pay.edition_market("au") and pay.edition_market("hu") and not pay.acl_market("hu")
      and not any(pay.edition_market(m) for m in ("eu", "lt", None, "HU", "zz")),
      (CL["edition"], pay.ACL_MARKETS, pay.EDITION_MARKETS, CL["editionMarkets"]))
cf = CL["checkoutFor"]
check("A6 checkoutLegal: au gets the AU checkbox and a link to terms#australia; eu and lt the EU wording as before",
      cf["en_au"]["withdrawalConsent"] == au_en and any(p.get("section") == "australia" and p.get("doc") == "terms"
                                                         for p in cf["en_au"]["acceptance"])
      and cf["de_au"]["withdrawalConsent"] == pay.CONSENT_TEXT_AU["de"] and cf["en_au"]["continueButton"] == "Continue to payment"
      and cf["en_eu"] == EU_BEFORE["checkout"]["en"] and cf["en_lt"] == EU_BEFORE["checkout"]["en"], cf["en_au"]["acceptance"])
check("A7 links: a section link carries the market before the #; the EU link none",
      CL["hrefs"] == {"auSection": "/terms?lang=en&m=au#australia", "euSection": "/terms?lang=en#australia",
                      "plain": "/privacy?lang=de"}, CL["hrefs"])

# ---------------------------------------------------------------------------------------------- B. the EU edition as before
# 0930 refresh. What 30efee7 and 1acef38 changed in the EU edition on purpose (en and de, the two languages the snapshot of before
# has), the ALLOWED difference from eu_before.json; the texts themselves are pinned whole to eu_1acef38.json:
#   terms:      "contract": the contract languages sentence names four languages (30efee7); "prices": one block added, the standard
#               price list sentence of the price experiments (1acef38)
#   privacy:    "website" +1 (the country hint, the AU step); "operations" 1 block changed (price test events, 1acef38); "orders" 1 block
#               changed (price test data passed to Stripe, 1acef38); "storage" +3 and -1 (the language switch sentence rewritten by
#               30efee7, the market key of the AU step, the anonymous visitor number of 1acef38)
#   withdrawal page and legal notice: unchanged
CONTRACT_LANGS = {"en": ("The contract languages are English and German.",
                         "The contract languages are English, German, Lithuanian and Hungarian."),
                  "de": ("Vertragssprachen sind Deutsch und Englisch.",
                         "Vertragssprachen sind Deutsch, Englisch, Litauisch und Ungarisch.")}
PRICE_TEST = {"en": "standard price list", "de": "Standardpreisliste"}
PRIV_ALLOWED = {   # section id: (blocks added, blocks removed, phrases the added ones hold, phrases the removed ones hold)
    "en": {"website": (1, 0, ["country that Vercel derives"], []),
           "operations": (1, 1, ["While we test prices"], ["Our admin panel shows them to us, mostly as counts per day"]),
           "orders": (1, 1, ["when a price test applied"], ["the order number, the price, the number of eyes"]),
           "storage": (3, 1, ["snapeyes.market", "snapeyes.vid", "with the language switch"], ["EN/DE switch"])},
    "de": {"website": (1, 0, ["Land lesen, das Vercel"], []),
           "operations": (1, 1, ["Solange wir Preise testen"], ["Unser Admin-Bereich zeigt sie uns, meist als Zahlen pro Tag"]),
           "orders": (1, 1, ["wenn ein Preistest galt"], ["Bestellnummer, Preis, Anzahl der Augen"]),
           "storage": (3, 1, ["snapeyes.market", "snapeyes.vid", "mit dem Sprachschalter"], ["Schalter EN/DE"])},
}


def doc_diff(new, old):
    """(same frame, {section id: (blocks added, blocks removed)}): the frame (title, lead, description, toc, the sections' ids, order and
    titles) must be equal and the blocks both keep must stay in their order; the dict names what differs, nothing else."""
    frame = ({k: v for k, v in new.items() if k != "sections"} == {k: v for k, v in old.items() if k != "sections"}
             and [(x["id"], x["title"]) for x in new["sections"]] == [(x["id"], x["title"]) for x in old["sections"]])
    out = {}
    for sn, so in zip(new["sections"], old["sections"]):
        if sn == so:
            continue
        add = [b for b in sn["blocks"] if b not in so["blocks"]]
        rem = [b for b in so["blocks"] if b not in sn["blocks"]]
        frame = frame and [b for b in sn["blocks"] if b not in add] == [b for b in so["blocks"] if b not in rem]
        out[sn["id"]] = (add, rem)
    return frame, out


def holds(blocks, phrases):
    """Every phrase is in some block, and every block is one of the phrases' (plain text blocks only)."""
    return (all(isinstance(b, str) and any(p in b for p in phrases) for b in blocks)
            and all(any(isinstance(b, str) and p in b for b in blocks) for p in phrases))


DOCS4 = ("terms", "withdrawal", "privacy", "imprint")
terms_diff = {l: doc_diff(EDI["eu"]["terms"][l], EU_BEFORE["terms"][l]) for l in LANG2}
terms_ok = all(
    fr and sorted(d) == ["contract", "prices"] and d["contract"] == ([CONTRACT_LANGS[l][1]], [CONTRACT_LANGS[l][0]])
    and len(d["prices"][0]) == 1 and not d["prices"][1] and holds(d["prices"][0], [PRICE_TEST[l]])
    for l, (fr, d) in terms_diff.items())
same = {d: all(EDI["eu"][d][l] == EU_BEFORE[d][l] for l in LANG2) for d in ("withdrawal", "imprint")}
same["terms"] = terms_ok
pinned = {d: all(EDI["eu"][d][l] == EU_NOW[d][l] for l in LANG2) for d in DOCS4}
editions4 = {d: sorted(EDI["eu"][d]) for d in DOCS4}
check("B1 EU terms, withdrawal page and legal notice exactly as before (en, de)"
      " - 0930: the terms differ from before by exactly the contract languages sentence (30efee7) and the price list sentence "
      "(1acef38); all pinned to eu_1acef38.json; lt and hu editions present",
      all(same.values()) and all(pinned.values()) and all(v == ["de", "en", "hu", "lt"] for v in editions4.values()),
      (same, pinned, editions4, {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in terms_diff.items()}))
priv_diff = {l: doc_diff(EDI["eu"]["privacy"][l], EU_BEFORE["privacy"][l]) for l in LANG2}
priv_ok = {l: fr and sorted(d) == sorted(PRIV_ALLOWED[l])
           and all(len(d[sec][0]) == na and len(d[sec][1]) == nr and holds(d[sec][0], pa) and holds(d[sec][1], pr)
                   for sec, (na, nr, pa, pr) in PRIV_ALLOWED[l].items() if sec in d)
           for l, (fr, d) in priv_diff.items()}
priv_pinned = {l: EDI["eu"]["privacy"][l] == EU_NOW["privacy"][l] for l in LANG2}
check("B2 EU privacy policy: only two sentences added per language (the market key, the country hint), all else as before"
      " - 0930: plus the language switch sentence (30efee7) and the price test sentences (1acef38: the anonymous visitor number, "
      "the events, the data passed to Stripe); pinned to eu_1acef38.json",
      all(priv_ok.values()) and all(priv_pinned.values()),
      (priv_ok, priv_pinned, {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in priv_diff.items()}))


def _norm(t):
    """The pack's text without its date line (the date changes with every legal change)."""
    return t.replace("2026-09-30", "X").replace("30.09.2026", "X")


def _terms_pack_ok(l):
    """The pack's EU terms = the old pack's, plus exactly one paragraph (the price list sentence) and the four contract languages."""
    pars = PACK["docs"][l]["terms"]["text"].split("\n\n")
    back = "\n\n".join(p for p in pars if PRICE_TEST[l] not in p)
    return (len([p for p in pars if PRICE_TEST[l] in p]) == 1 and back.count(CONTRACT_LANGS[l][1]) == 1
            and _norm(back.replace(CONTRACT_LANGS[l][1], CONTRACT_LANGS[l][0])) == _norm(EU_BEFORE["pack"]["docs"][l]["terms"]["text"]))


seller_en_de = {k: ({l: v[l] for l in LANG2} if isinstance(v, dict) else v) for k, v in PACK["seller"].items()}
pack_docs_eq = lambda a, b, l, d: (_norm(a[l][d]["text"]) == _norm(b[l][d]["text"]) and a[l][d]["url"] == b[l][d]["url"]
                                    and a[l][d]["title"] == b[l][d]["title"])
eu_pack_same = (
    all(_terms_pack_ok(l) for l in LANG2)
    and all(pack_docs_eq(PACK["docs"], EU_BEFORE["pack"]["docs"], l, "withdrawal") for l in LANG2)
    and all(PACK["docs"][l]["terms"]["url"] == EU_BEFORE["pack"]["docs"][l]["terms"]["url"] for l in LANG2)
    and all(pack_docs_eq(PACK["docs"], EU_NOW["pack"]["docs"], l, d) for l in LANG2 for d in ("terms", "withdrawal"))
    and sorted(PACK["docs"]) == ["de", "en", "hu", "lt"])
seller_same = (seller_en_de == EU_BEFORE["pack"]["seller"] and PACK["seller"] == EU_NOW["pack"]["seller"]
               and all(sorted(PACK["seller"][k]) == ["de", "en", "hu", "lt"] for k in ("company", "address", "contact")))
check("B3 the built pack's EU texts are the same as before (the date line aside), links without m="
      " - 0930: the terms by exactly the two sentences of 30efee7 and 1acef38, the seller with its lt and hu lines; "
      "all pinned to eu_1acef38.json",
      eu_pack_same and "m=" not in json.dumps(PACK["docs"]) and seller_same and PACK["updated"] == EU_NOW["pack"]["updated"],
      (eu_pack_same, seller_same, [_terms_pack_ok(l) for l in LANG2]))
check("B4 landing copy: eu and lt read the language's own copy object (unchanged)",
      CL["copySame"] == {"euEn": True, "euDe": True, "ltEn": True}, CL["copySame"])

# ---------------------------------------------------------------------------------------------- C. the Australian edition
T = EDI["au"]["terms"]
ids_eu = [s["id"] for s in EDI["eu"]["terms"]["en"]["sections"]]
ids_au = [s["id"] for s in T["en"]["sections"]]
check("C1 AU terms: the EU sections in order, with 'australia' right after 'defects' (en, de)",
      ids_au == ids_eu[:ids_eu.index("defects") + 1] + ["australia"] + ids_eu[ids_eu.index("defects") + 1:]
      and [s["id"] for s in T["de"]["sections"]] == ids_au, ids_au)
changed = {"preview", "prices", "withdrawal", "defects", "liability", "disputes", "australia",
           "contract"}   # 0930: "contract" since 30efee7, held to one sentence by contract_au below
shared_same = all(s == e for lang in ("en", "de") for s in T[lang]["sections"] if s["id"] not in changed
                  for e in EDI["eu"]["terms"][lang]["sections"] if e["id"] == s["id"])
pv = {lang: [next(s for s in e[lang]["sections"] if s["id"] == "preview") for e in (T, EDI["eu"]["terms"])] for lang in ("en", "de")}
# 0930 (30efee7): the EU terms name four contract languages, the Australian pages exist in English and German only, so the AU
# "contract" section is the EU one with exactly that one sentence as it was (edition_langs "au")
eu_contract = {l: json.dumps(next(s for s in EDI["eu"]["terms"][l]["sections"] if s["id"] == "contract"), ensure_ascii=False) for l in LANG2}
au_contract = {l: json.dumps(next(s for s in T[l]["sections"] if s["id"] == "contract"), ensure_ascii=False) for l in LANG2}
contract_au = all(eu_contract[l].count(CONTRACT_LANGS[l][1]) == 1
                  and eu_contract[l].replace(CONTRACT_LANGS[l][1], CONTRACT_LANGS[l][0]) == au_contract[l] for l in LANG2)
check("C2 AU terms: every other section is the EU one word for word; 'preview' only names the AU complaints title"
      " - 0930: and 'contract' only names English and German as the contract languages (30efee7)",
      shared_same and contract_au and json.dumps(pv["en"][1]).replace("Complaints and defects", "Complaints and faulty files") == json.dumps(pv["en"][0])
      and json.dumps(pv["de"][1], ensure_ascii=False).replace("Reklamationen und Mängel", "Reklamationen und mangelhafte Dateien")
      == json.dumps(pv["de"][0], ensure_ascii=False)
      and "Complaints and defects" not in json.dumps(EDI["au"]) and "Reklamationen und Mängel" not in json.dumps(EDI["au"], ensure_ascii=False))
aus = {lang: next(s for s in T[lang]["sections"] if s["id"] == "australia") for lang in ("en", "de")}
check("C3 'Your rights in Australia' opens with the ACCC sentence, word for word (en, de)",
      aus["en"]["title"] == "Your rights in Australia" and aus["en"]["blocks"][0] == f"**{ACCC}**"
      and aus["de"]["blocks"][0].startswith(f"**{ACCC}**") and aus["de"]["title"] == "Ihre Rechte in Australien",
      (aus["en"]["blocks"][0], aus["de"]["blocks"][0][:120]))
au_text = " ".join(b if isinstance(b, str) else json.dumps(b, ensure_ascii=False) for b in aus["en"]["blocks"])
# (fixer, after the legal review: the remedies are the prescribed services text word for word, never more than the ACL)
check("C4 the ACL remedies as the prescribed services text (major: cancel, refund of the unused portion or compensation; "
      "foreseeable loss; minor: rectified in a reasonable time, else cancel and refund), change of mind, the claim route, "
      "the non-exclusion clause, a link to the privacy section",
      all(x in au_text for x in ("For major failures with the service, you are entitled: to cancel your service contract with us",
                                  "a refund for the unused portion, or to compensation for its reduced value",
                                  "any other reasonably foreseeable loss or damage",
                                  "If the failure does not amount to a major failure, you are entitled to have problems with the "
                                  "service rectified in a reasonable time",
                                  "can't cancel just because you changed your mind",
                                  "cannot lawfully be excluded, restricted or modified", "doc:privacy#australia",
                                  "due care and skill", "reasonable time"))
      and "making your file again" not in au_text, au_text[:600])
prices = next(s for s in T["en"]["sections"] if s["id"] == "prices")
dl = prices["blocks"][0]["dl"]
ap = CL["auPrices"]
want = ["A$" + str(ap["one_eye_studio_black"] // 100), "A$" + str(ap["one_eye_art"] // 100), "A$" + str(ap["two_eyes"] // 100),
        "+A$" + str(ap["each_further_eye"] // 100)]
check("C5 AU prices in the terms from api/_lib/markets.py (A$ totals, no GST, no surcharge, invoice), never a bare $",
      [dl[0][1], dl[1][1].split(" ")[0], dl[2][1], dl[3][1].split(",")[0]] == want
      and "no GST is charged" in prices["blocks"][1] and "no card surcharge" in prices["blocks"][1]
      and "invoice" in prices["blocks"][1] and "euro" not in json.dumps(prices) and "VAT" not in json.dumps(prices)
      and not re.search(r"(?<!A)\$\d", json.dumps(prices)), (dl, prices["blocks"][1]))
wd_au = next(s for s in T["en"]["sections"] if s["id"] == "withdrawal")
check("C6 AU terms: the withdrawal right framed as EU law and as cancelling for a change of mind only",
      "EU consumer law gives consumers a 14-day right of withdrawal" in wd_au["blocks"][0]
      and "Lithuanian law" in wd_au["blocks"][0] and wd_au["blocks"][1].startswith("**This is only about cancelling for a change of mind.**")
      and "#australia" in wd_au["blocks"][1], wd_au)
dfx = next(s for s in T["en"]["sections"] if s["id"] == "defects")["blocks"][0]
check("C7 AU complaints: no promise of our own to redo or refund (no reg 90 warranty), the law's rights named",
      "render the file again" not in dfx and "free of charge" not in dfx and "Australian Consumer Law" in dfx
      and "do not limit them" in dfx, dfx)
lia = next(s for s in T["en"]["sections"] if s["id"] == "liability")["blocks"][0]
dis = " ".join(next(s for s in T["en"]["sections"] if s["id"] == "disputes")["blocks"])
check("C8 AU liability keeps the ACL first, no 'essential obligations' limit; disputes name the AU route and keep the EU one",
      lia.startswith("Nothing in these terms excludes, restricts or modifies your rights under the Australian Consumer Law")
      and "essential contractual obligations" not in lia and "fair trading" in dis and "accc.gov.au" in dis
      and "vvtat.lt" in dis and "Lithuanian law applies" in dis and "Australian Consumer Law" in dis, (lia, dis[:400]))
WAU = EDI["au"]["withdrawal"]
exp_en = next(s for s in WAU["en"]["sections"] if s["id"] == "expiry")
exp_de = next(s for s in WAU["de"]["sections"] if s["id"] == "expiry")
boxes = [b for b in exp_en["blocks"] if isinstance(b, dict) and "box" in b]
check("C9 AU withdrawal page: EU statutory text kept, lead framed as EU law, the AU checkbox in its box, ACL links",
      "under EU consumer law" in WAU["en"]["lead"] and "doc:terms#australia" in WAU["en"]["lead"]
      and boxes and boxes[0]["box"] == [au_en]
      and any(isinstance(b, dict) and b.get("box") == [pay.CONSENT_TEXT_AU["de"]] for b in exp_de["blocks"])
      and "doc:terms#australia" in json.dumps(exp_en) and "doc:terms#australia" in json.dumps(exp_de, ensure_ascii=False)
      and [s for s in WAU["en"]["sections"] if s["id"] == "right"] == [s for s in EDI["eu"]["withdrawal"]["en"]["sections"] if s["id"] == "right"],
      WAU["en"]["lead"])
PAU = EDI["au"]["privacy"]
pids = [s["id"] for s in PAU["en"]["sections"]]
psec = {lang: next(s for s in PAU[lang]["sections"] if s["id"] == "australia") for lang in ("en", "de")}
ptext = " ".join(psec["en"]["blocks"])
check("C10 AU privacy: 'australia' right after 'rights' (biometric info never used to identify, outside Australia, APPs and "
      "the small business exemption, the tort of 10 June 2025, OAIC); all else = the EU policy",
      pids[pids.index("rights") + 1] == "australia" and [p for p in pids if p != "australia"] == [s["id"] for s in EDI["eu"]["privacy"]["en"]["sections"]]
      and all(x in ptext for x in ("biometric information", "sensitive information", "never identify or verify anyone",
                                   "outside Australia", "Australian Privacy Principles", "A$3 million", "10 June 2025",
                                   "oaic.gov.au", "#iris", "#services"))
      and "oaic.gov.au" in " ".join(psec["de"]["blocks"])
      and all(s == e for s in PAU["en"]["sections"] if s["id"] != "australia" for e in EDI["eu"]["privacy"]["en"]["sections"] if e["id"] == s["id"]),
      pids)
imp = EDI["au"]["imprint"]["en"]["sections"][0]["blocks"][1]["dl"]
check("C11 AU legal notice: the EU rows plus 'GST (Australia): not registered, no GST charged'",
      imp[:-1] == EDI["eu"]["imprint"]["en"]["sections"][0]["blocks"][1]["dl"] and imp[-1][0] == "GST (Australia)"
      and "no GST is charged" in imp[-1][1] and EDI["au"]["imprint"]["de"]["sections"][0]["blocks"][1]["dl"][-1][0] == "GST (Australien)", imp[-1])
au_all = json.dumps(EDI["au"], ensure_ascii=False)
check("C12 no AU text reads as 'no refunds', 'non-refundable', 'all sales final' or 'tax invoice'", not bad_words(au_all),
      bad_words(au_all))
en_au_strings = json.dumps([EDI["au"][d]["en"] for d in EDI["au"]], ensure_ascii=False)
check("C13 Australian (British) spelling in the AU English texts: colour, personalised, licence (no color, personalized, "
      "Mom, jewelry, center)", not AMERICAN.findall(en_au_strings) and "personalised" in en_au_strings
      and "colour" in en_au_strings.lower() and "licence" in en_au_strings, AMERICAN.findall(en_au_strings)[:10])
check("C14 no en or em dash in any edition", not any(d in json.dumps(EDI, ensure_ascii=False) for d in DASHES))

# the pack's Australian edition
ED = PACK["editions"]["au"]
links = re.findall(r"https://snapeyes\.com/(?:terms|privacy|withdrawal|imprint)\?[^\s)]*", json.dumps(ED))
check("C15 pack editions.au: en and de, terms and withdrawal, every legal link carries m=au; its terms hold the ACL block",
      sorted(ED) == ["de", "en"] and all(sorted(ED[l]) == ["terms", "withdrawal"] for l in ED) and links
      and all("m=au" in x for x in links) and ACCC in ED["en"]["terms"]["text"] and ACCC in ED["de"]["terms"]["text"]
      and ED["en"]["terms"]["url"] == "https://snapeyes.com/terms?lang=en&m=au" and ED["en"]["terms"]["text"] == CL["plainAuTerms"]
      and CL["pack"]["editions"]["au"]["en"]["terms"]["text"] == ED["en"]["terms"]["text"],
      [x for x in links if "m=au" not in x][:5])

# landing and order page lines
faq_au = [it for it in CL["copy"]["auEn"]["faq"]["items"] if it["q"] == "Can I cancel an order?"]
faq_de = [it for it in CL["copy"]["auDe"]["faq"]["items"] if it["q"] == "Kann ich eine Bestellung stornieren?"]
faq_eu = [it for it in CL["copy"]["eu"]["faq"]["items"] if it["q"] == "Can I withdraw from an order?"]
check("C16 landing FAQ for au: cancelling framed as EU law, the ACCC words, no 'we render it again' promise; eu as before",
      len(faq_au) == 1 and len(faq_de) == 1 and len(faq_eu) == 1 and "EU consumer law" in faq_au[0]["a"]
      and "guarantees that cannot be excluded under the Australian Consumer Law" in faq_au[0]["a"]
      and "render it again" not in faq_au[0]["a"] and "we render it again or refund you" in faq_eu[0]["a"]
      and len(CL["copy"]["auEn"]["faq"]["items"]) == len(CL["copy"]["eu"]["faq"]["items"])
      and not bad_words(json.dumps(CL["copy"]["auEn"])) and not AMERICAN.findall(json.dumps(CL["copy"]["auEn"])),
      faq_au)
check("C17 order page: an ACL line for Australian orders (en, de)", CL["orderAcl"] and "Australian Consumer Law" in CL["orderAcl"]["en"]
      and "Australian Consumer Law" in CL["orderAcl"]["de"] and not bad_words(CL["orderAcl"]["en"]), CL["orderAcl"])

# ---------------------------------------------------------------------------------------------- D. checkout
c, j = get("/api/checkout")
check("D1 GET /api/checkout: consent en/de the EU text as before; consent.markets.au the AU text (en, de)",
      c == 200 and j["consent"]["version"] == pay.CONSENT_VERSION and j["consent"]["en"] == PAY0.CONSENT_TEXT["en"]
      and j["consent"]["de"] == PAY0.CONSENT_TEXT["de"] and j["consent"]["markets"] == {"au": pay.CONSENT_TEXT_AU}, j.get("consent"))
oA, kA = new_order(2)
c, j = checkout(oA, kA, 2, "studio_black", "en", market="au")
p = H.Fake.creates[-1][0]
rec = read_json(f"orders/{oA}/order.json")
check("D2 au checkout: Stripe locale en-GB, aud, the AU submit note; order.json keeps the AU text, its version and fingerprint"
      " - 0930: the version recorded is the current one, 2026-09-30.2 (30efee7), the AU text is unchanged",
      c == 200 and p["locale"] == "en-GB" and p["line_items[0][price_data][currency]"] == "aud"
      and p["custom_text[submit][message]"] == pay.SUBMIT_NOTE_AU["en"] and "Australian Consumer Law" in p["custom_text[submit][message]"]
      and rec["checkout"]["consent"]["text"] == au_en and rec["checkout"]["consent"]["version"] == CONSENT_NOW
      and p["metadata[consent_version]"] == CONSENT_NOW, (p.get("locale"), p.get("custom_text[submit][message]"), rec["checkout"]["consent"]))
c, j = checkout(oA, kA, 2, "studio_black", "de", market="au")
p = H.Fake.creates[-1][0]
rec = read_json(f"orders/{oA}/order.json")
check("D3 au in German: Stripe de, the German AU note and checkbox text", c == 200 and p["locale"] == "de"
      and p["custom_text[submit][message]"] == pay.SUBMIT_NOTE_AU["de"] and rec["checkout"]["consent"]["text"] == pay.CONSENT_TEXT_AU["de"],
      p.get("custom_text[submit][message]"))
for lang in ("en", "de"):
    c, j = checkout(oA, kA, 2, "studio_black", lang)
    p = H.Fake.creates[-1][0]
    rec = read_json(f"orders/{oA}/order.json")
    check(f"D4 eu checkout ({lang}): the EU submit note and checkbox text exactly as before", c == 200
          and p["custom_text[submit][message]"] == PAY0.SUBMIT_NOTE[lang] and p["locale"] == lang
          and rec["checkout"]["consent"]["text"] == PAY0.CONSENT_TEXT[lang], p.get("custom_text[submit][message]"))
c, j = checkout(oA, kA, 2, "studio_black", "en", market="lt")
rec = read_json(f"orders/{oA}/order.json")
check("D5 lt checkout: the EU wording (lt reads the EU edition)", c == 200 and rec["checkout"]["consent"]["text"] == PAY0.CONSENT_TEXT["en"]
      and H.Fake.creates[-1][0]["custom_text[submit][message]"] == PAY0.SUBMIT_NOTE["en"])
check("D6 no Stripe text for au reads as 'no refunds'", not bad_words(json.dumps(pay.SUBMIT_NOTE_AU) + json.dumps(pay.CONSENT_TEXT_AU)))

# ---------------------------------------------------------------------------------------------- E. the AU confirmation
oE, kE, pE, mE = paid_order("au", "en", "sydney@example.com", eyes=2)
t = mE[0]["text"] if mE else ""
head = t.split("_" * 64)[0]
check("E1 AU paid: paid.json market au, the AU consent text recorded; one confirmation, subject with 'invoice'"
      " - 0930: recorded under the current version 2026-09-30.2 (30efee7), the AU text unchanged",
      pE["market"] == "au" and pE["consent"]["text"] == au_en and pE["consent"]["version"] == CONSENT_NOW
      and len(mE) == 1 and mE[0]["subject"] == f"Your SnapEyes order {oE}: order confirmation and invoice", (pE.get("consent"), [m["subject"] for m in mE]))
inv = f"Invoice\nInvoice number: {oE}\nInvoice date: "
check("E2 the invoice: number, date, supplier with company code and address, customer, what was supplied, total A$79, "
      "'No GST has been charged', paid in full", inv in head and "Supplier: MB \"Portretizuokis\", company code 305605052, " in head
      and "Customer: sydney@example.com" in head and "Supplied: 1 x SnapEyes iris artwork, 2 eyes, Studio Black" in head
      and f"Total: A${pay.price_list('au')['two_eyes'] // 100}\n" in head and "GST: No GST has been charged. The supplier is not registered for GST in Australia." in head
      and "Payment: paid in full through Stripe on " in head, head[:2500])
check("E3 never 'Tax invoice' (anywhere in the email, legal texts included), no euro, no VAT sentence before the legal texts",
      not re.search(r"tax invoice", t, re.I) and "€" not in head and "VAT" not in head and "Price: A$79. This is the total price: no GST is charged." in head)
i_rights, i_cancel = head.find("Your rights in Australia\n" + ACCC), head.find("Cancelling before we start\n")
check("E4 'Your rights in Australia' opens with the ACCC sentence and links terms#australia (m=au), before 'Cancelling before we start'",
      0 < i_rights < i_cancel and "https://snapeyes.com/terms?lang=en&m=au#australia" in head
      and "EU consumer law, with its right of withdrawal, applies to your contract." in head and "get a full refund" in head
      and "Your right of withdrawal\n" not in head, head[:3000])
check("E5 the consent quoted is the AU text; the confirmation keeps the ACL",
      "“" + au_en + "”" in head and "your right of withdrawal under EU consumer law has ended and you can't cancel for a change of mind. "
      "This doesn't affect your rights under the Australian Consumer Law (see below)." in head)
check("E6 the full AU withdrawal information and AU terms are attached (not the EU ones); the terms link carries m=au",
      ED["en"]["withdrawal"]["text"] in t and ED["en"]["terms"]["text"] in t and PACK["docs"]["en"]["terms"]["text"] not in t
      and "https://snapeyes.com/terms?lang=en&m=au\n" in head)
check("E7 the AU email: no 'no refunds' wording, no en or em dash", not bad_words(t) and not any(d in t for d in DASHES), bad_words(t))
md = read_json(f"orders/{oE}/mail_delivery.json")
check("E8 mail_delivery.json sent with the new consent version and the pack date"
      " - 0930: the new version is 2026-09-30.2 (30efee7)", md.get("state") == "sent"
      and md.get("consent") == CONSENT_NOW and md.get("legal") == "2026-09-30", md)
with open(os.path.join(HERE, "sample_au_confirmation_en.txt"), "w", encoding="utf-8") as f:
    f.write(head)

oG, kG, pG, mG = paid_order("au", "de", "perth@example.com", eyes=1, style="deep_nebula")
t = mG[0]["text"] if mG else ""
head = t.split("_" * 64)[0]
check("E9 German AU confirmation: Rechnung, 'Es wurde keine GST berechnet', Gesamtbetrag A$49, the ACCC sentence, "
      "the German AU consent and texts", len(mG) == 1 and mG[0]["subject"].endswith("Bestellbestätigung und Rechnung")
      and f"Rechnung\nRechnungsnummer: {oG}" in head and "GST: Es wurde keine GST berechnet." in head
      and f"Gesamtbetrag: A${pay.price_list('au')['one_eye_art'] // 100}\n" in head and ACCC in head
      and "„" + pay.CONSENT_TEXT_AU["de"] + "“" in head and ED["de"]["terms"]["text"] in t and ED["de"]["withdrawal"]["text"] in t
      and "Widerruf, bevor wir beginnen" in head and not re.search(r"steuerrechnung|tax invoice", t, re.I)
      and not any(d in t for d in DASHES), head[:2500])
with open(os.path.join(HERE, "sample_au_confirmation_de.txt"), "w", encoding="utf-8") as f:
    f.write(head)

# ---------------------------------------------------------------------------------------------- F. EU emails exactly as before
oU, kU, pU, mU = paid_order(None, "en", "dublin@example.com", eyes=2, style="supernova")
oD, kD, pD, mD = paid_order("lt", "de", "vilnius@example.com")
pay.start_clock()
PAY0.start_clock()
diffs = []
for o, k, paid in ((oU, kU, pU), (oD, kD, pD)):
    consent = pay.paid_consent(o, read_json(f"orders/{o}/order.json"), paid)
    for pk in (PACK, PACK_AUTO):
        a = pay.confirmation_mail(o, paid, k, pk, consent)
        b = PAY0.confirmation_mail(o, paid, k, pk, consent)
        if a != b:
            diffs.append((o, pk is PACK_AUTO))
check("F1 EU and lt confirmation emails (en, de; order page start and server start) are byte for byte the core's own",
      not diffs and len(mU) == 1 and len(mD) == 1 and "Invoice" not in mU[0]["text"] and "Australia" not in mU[0]["text"]
      and mU[0]["subject"] == f"Your SnapEyes order {oU}: order confirmation", diffs)
a = pay.confirmation_mail(oE, pE, kE, PACK_AUTO, pay.paid_consent(oE, read_json(f"orders/{oE}/order.json"), pE))
check("F2 the AU email with the server start: same invoice and rights, the 'right after this email' wording",
      "so that right usually ends within a few moments" in a[1] and "Invoice number: " + oE in a[1] and ACCC in a[1])
try:
    PAY0.confirmation_mail(oE, pE, kE, PACK, pay.paid_consent(oE, read_json(f"orders/{oE}/order.json"), pE))
    old_au = True
except Exception:
    old_au = False
check("F3 (the core's code would have sent an AU order the EU email: this step is what changes it)", old_au)

# ---------------------------------------------------------------------------------------------- G. the pack's AU edition is required
nopack = json.loads(json.dumps(PACK))
del nopack["editions"]
halfpack = json.loads(json.dumps(PACK))
halfpack["editions"]["au"]["de"]["terms"]["text"] = "short"
nohu = json.loads(json.dumps(PACK))
del nohu["editions"]["hu"]
halfhu = json.loads(json.dumps(PACK))
halfhu["editions"]["hu"]["lt"]["terms"]["text"] = "short"
check("G1 pack_docs: EU docs for eu/lt/hu, the AU edition for au; None when it is missing or incomplete"
      " - 0930: hu reads its own edition (editions.hu, links with m=hu; 30efee7), never the EU docs, and au has en and de only",
      pay.pack_docs(PACK, "en", "au") == PACK["editions"]["au"]["en"] and pay.pack_docs(PACK, "de", "lt") == PACK["docs"]["de"]
      and pay.pack_docs(PACK, "en", None) == PACK["docs"]["en"]
      and all(pay.pack_docs(PACK, l, "hu") == PACK["editions"]["hu"][l] != PACK["docs"][l]
              and "m=hu" in PACK["editions"]["hu"][l]["terms"]["url"] for l in ("en", "de", "lt", "hu"))
      and pay.pack_docs(PACK, "lt", "au") is None and pay.pack_docs(PACK, "hu", "au") is None
      and pay.pack_docs(PACK, "lt", "lt") == PACK["docs"]["lt"] and pay.pack_docs(PACK, "hu", None) == PACK["docs"]["hu"]
      and pay.pack_docs(nopack, "en", "au") is None and pay.pack_docs(halfpack, "de", "au") is None
      and pay.pack_docs(halfpack, "en", "au") is not None and pay._legal_ok(nopack)
      and pay.pack_docs(nohu, "en", "hu") is None and pay.pack_docs(nohu, "en", "au") is not None
      and pay.pack_docs(halfhu, "lt", "hu") is None and pay.pack_docs(halfhu, "en", "hu") is not None)
set_pack(nopack)
why = pay.legal_problem()
set_pack(halfpack)
why2 = pay.legal_problem()
set_pack(PACK)
check("G2 legal_problem: a pack without the au edition (or half of it) keeps live sales closed while au is selectable; the "
      "full pack passes", "au market" in why and "au market" in why2 and pay.legal_problem() == "", (why, why2, pay.legal_problem()))
# an AU order paid while the site serves a pack without the AU texts: its confirmation waits (never the EU texts)
oW, kW = new_order(1)
checkout(oW, kW, 1, "studio_black", "en", market="au")
sW = H.pay_session(sid_of(oW), "melbourne@example.com")
set_pack(nopack)
n0 = len(H.Fake.emails)
c, j = hook(sW)
sent_early = mails_to("melbourne@example.com", n0)
md = read_json(f"orders/{oW}/mail_delivery.json") if exists(f"orders/{oW}/mail_delivery.json") else None
check("G3 AU order, pack without its texts: paid, no confirmation sent, nothing claimed, Stripe asked to retry",
      exists(f"orders/{oW}/paid.json") and not sent_early and md is None and c == 503, (c, j, md, [m["subject"] for m in sent_early]))
oX, kX, pX, mX = paid_order(None, "en", "cork@example.com")
check("G4 ... while an EU order in the same moment gets its EU confirmation", len(mX) == 1
      and PACK["docs"]["en"]["terms"]["text"] in mX[0]["text"], [m["subject"] for m in mX])
try:
    pay.confirmation_mail(oW, read_json(f"orders/{oW}/paid.json"), kW, nopack,
                          pay.paid_consent(oW, read_json(f"orders/{oW}/order.json"), read_json(f"orders/{oW}/paid.json")))
    raised = False
except pay.PayError:
    raised = True
check("G5 confirmation_mail itself refuses an AU order without its texts (PayError), never falls back to the EU ones", raised)
set_pack(PACK)
n0 = len(H.Fake.emails)
c, j = hook(sW)
got = mails_to("melbourne@example.com", n0)
check("G6 once the pack has the AU texts, the retried webhook sends the AU confirmation", c == 200 and len(got) == 1
      and ACCC in got[0]["text"] and ED["en"]["terms"]["text"] in got[0]["text"], (c, j))

# the admin's copy of a sent confirmation: the AU texts, or 503 when the pack lacks them
set_pack(nopack)
try:
    ops.act_resend_confirmation({"order": oE}, "test")
    busy = None
except store.Answer as e:
    busy = e
set_pack(PACK)
n0 = len(H.Fake.emails)
res = ops.act_resend_confirmation({"order": oE}, "test")
cp = mails_to("sydney@example.com", n0)
check("G7 admin 'send the confirmation again' for an AU order: 503 legal_unavailable without the AU texts; with them a copy "
      "with the invoice and the AU terms", busy is not None and getattr(busy, "status", None) == 503 and res.get("copy") is True
      and len(cp) == 1 and "Invoice number: " + oE in cp[0]["text"] and ED["en"]["terms"]["text"] in cp[0]["text"],
      (busy and vars(busy), res))

# ---------------------------------------------------------------------------------------------- H. consent fallbacks
check("H1 consent_text: the AU text for au at the new version; none for au at the old version; EU for the rest"
      " - 0930: 2026-09-30.1 (the AU step's) and the current 2026-09-30.2 both quote it; au never has an lt or hu text",
      pay.consent_text(CONSENT_NOW, "en", "au") == au_en and pay.consent_text(CONSENT_NOW, "de", "au") == pay.CONSENT_TEXT_AU["de"]
      and pay.consent_text(CONSENT_NOW, "lt", "au") is None and pay.consent_text(CONSENT_NOW, "hu", "au") is None
      and pay.consent_text(CONSENT_NOW, "lt") == pay.CONSENT_TEXT["lt"] and pay.consent_text(CONSENT_NOW, "hu", "hu") == pay.CONSENT_TEXT["hu"]
      and pay.consent_text("2026-09-30.1", "lt") is None
      and pay.consent_text("2026-09-30.1", "en", "au") == au_en and pay.consent_text("2026-09-29.1", "en", "au") is None
      and pay.consent_text("2026-09-29.1", "de") == PAY0.CONSENT_TEXT["de"] and pay.consent_text("2026-09-30.1", "en", "lt") == PAY0.CONSENT_TEXT["en"]
      and pay.consent_text("2026-09-30.1", "en") == pay.consent_for("eu", "en") and pay.consent_for("au", "de") == pay.CONSENT_TEXT_AU["de"])
bare = dict(pE, consent={k: v for k, v in pE["consent"].items() if k != "text"})
recE = read_json(f"orders/{oE}/order.json")
recE_nocons = dict(recE, checkout=dict(recE["checkout"], consent={}))
check("H2 paid_consent without a stored text: the AU text of its version for an AU order, the EU text for an EU one",
      pay.paid_consent(oE, recE_nocons, bare)["text"] == au_en
      and pay.paid_consent(oU, {}, dict(pU, consent={k: v for k, v in pU["consent"].items() if k != "text"}))["text"] == PAY0.CONSENT_TEXT["en"])
check("H3 paid_market: paid.json's, else its spec's, else eu", pay.paid_market(pE) == "au" and pay.paid_market({"spec": {"market": "lt"}}) == "lt"
      and pay.paid_market({}) == "eu" and pay.paid_market(None) == "eu" and pay.paid_market({"market": "zz"}) == "eu")

# ---------------------------------------------------------------------------------------------- I. withdrawal receipts
def lapse(order):
    """Make a paid order's 14-day period over (paid 40 days ago)."""
    p = read_json(f"orders/{order}/paid.json")
    p["paid_at"] = int(time.time()) - 40 * 86400
    write_json(f"orders/{order}/paid.json", p)


def withdraw_now(order, k, email, lang="en"):
    n0 = len(H.Fake.emails)
    c, j = post("/api/order", {"action": "withdraw", "order": order, "k": k, "name": "Test Person", "email": email, "lang": lang})
    return c, j, mails_to(email, n0)


for o in (oG, oX):
    lapse(o)
c, j, rG = withdraw_now(oG, kG, "perth@example.com", "de")
c2, j2, rX = withdraw_now(oX, kX, "cork@example.com")
stG = [x for x in os.listdir(local(f"orders/{oG}")) if x.startswith("withdrawal_") and x.endswith(".json") and "_ack" not in x and "_note" not in x]
check("I1 lapsed statement on an AU order: the receipt adds the ACL line (German order: German); the statement keeps market au",
      c == 200 and (j.get("withdrawal") or {}).get("state") == "lapsed" and len(rG) == 1
      and "Ihre Rechte nach dem Australian Consumer Law bleiben unberührt" in rG[0]["text"] and not bad_words(rG[0]["text"])
      and any(read_json(f"orders/{oG}/{x}").get("market") == "au" for x in stG), (c, j, rG[0]["text"][:1500] if rG else None, stG))
check("I2 ... the EU order's lapsed receipt is the core's own (no ACL line)", c2 == 200 and len(rX) == 1
      and "Australian" not in rX[0]["text"] and (j2.get("withdrawal") or {}).get("state") == "lapsed", rX[0]["text"][:800] if rX else None)
# the same receipt text from the core's withdraw.py for the EU statement (byte for byte), and the AU one differs only by its line
stX = [read_json(f"orders/{oX}/{x}") for x in os.listdir(local(f"orders/{oX}")) if x.startswith("withdrawal_") and x.endswith(".json")
       and "_ack" not in x and "_note" not in x and x != "withdrawal.json"]
stGs = [read_json(f"orders/{oG}/{x}") for x in stG if x != "withdrawal.json"]
same_eu = stX and W.receipt_mail(stX[0], PACK) == W0.receipt_mail(stX[0], PACK)
a_au, b_au = (W.receipt_mail(stGs[0], PACK), W0.receipt_mail(stGs[0], PACK)) if stGs else (None, None)
check("I3 receipt_mail: EU statement byte for byte as before; AU statement = before plus one paragraph",
      same_eu and a_au and a_au[0] == b_au[0] and len(a_au[1]) > len(b_au[1]) and "Australian Consumer Law" in a_au[1]
      and "Australian Consumer Law" not in b_au[1], (same_eu, a_au and a_au[1][:300]))
# a lapsed statement because making began (English AU order)
oM, kM, pM, mM = paid_order("au", "en", "adelaide@example.com")
store.put(f"orders/{oM}/making.json", store.json_bytes({"t": int(time.time())}), "application/json", upsert=True)
c, j, rM = withdraw_now(oM, kM, "adelaide@example.com")
check("I4 making began on an AU order: lapsed, the receipt keeps 'statutory rights' and adds the ACL line, never 'no refunds'",
      c == 200 and (j.get("withdrawal") or {}).get("state") == "lapsed" and len(rM) == 1
      and "Your rights under the Australian Consumer Law are not affected" in rM[0]["text"]
      and "Your statutory rights for a defective file are not affected." in rM[0]["text"] and not bad_words(rM[0]["text"]),
      (c, j, rM[0]["text"][:1500] if rM else None))
# an effective withdrawal on an AU order: refund in A$ (the core's path), no ACL line needed
oR, kR, pR, mR = paid_order("au", "en", "hobart@example.com", style="supernova")
c, j, rR = withdraw_now(oR, kR, "hobart@example.com")
w = j.get("withdrawal") or {}
check("I5 effective withdrawal on an AU order: refund of A$49 in AUD", c == 200 and w.get("state") == "withdrawn"
      and w.get("currency") == "AUD" and w.get("amount") == pay.price_list("au")["one_eye_art"] and rR and "A$49" in rR[0]["text"], (c, j))

# ---------------------------------------------------------------------------------------------- K. the /try buy card
r = subprocess.run(["node", os.path.join(HERE, "buycard_check.mjs"), HERE], cwd=H.REPO, capture_output=True, text=True,
                   encoding="utf-8", timeout=300)
try:
    BC = json.loads(r.stdout)
except ValueError:
    BC = None
check("K0 the /try buy card renders (react-dom/server through Vite) for au en/de, eu en, lt de", BC is not None
      and sorted(BC) == ["au_de", "au_en", "eu_en", "lt_de"], (r.returncode, r.stderr[-900:]))
if BC:
    card = {k: (re.sub(r"<[^>]+>", " ", v["html"]), re.sub(r"<[^>]+>", " ", v["noServer"]), v["html"]) for k, v in BC.items()}
    A39 = "A$" + str(pay.price_list("au")["one_eye_studio_black"] // 100)
    check("K1 au: the server's AU checkbox text (en, de), the line links terms#australia (m=au), A$ price",
          "SERVER AU EN" in card["au_en"][0] and "SERVER AU DE" in card["au_de"][0] and "SERVER EU" not in card["au_en"][0] + card["au_de"][0]
          and "/terms?lang=en&amp;m=au#australia" in card["au_en"][2] and "/terms?lang=de&amp;m=au#australia" in card["au_de"][2]
          and A39 in card["au_en"][0] and "€" not in card["au_en"][0], card["au_en"][0][:600])
    check("K2 au without a server text: the site's own AU checkbox (the same words the server records)",
          pay.CONSENT_TEXT_AU["en"].replace("'", "&#x27;") in card["au_en"][1] or pay.CONSENT_TEXT_AU["en"] in card["au_en"][1],
          card["au_en"][1][:800])
    check("K3 eu and lt: the EU checkbox text and line as before (no Australia), euro prices",
          "SERVER EU EN" in card["eu_en"][0] and "SERVER EU DE" in card["lt_de"][0] and "australia" not in card["eu_en"][2]
          and "australia" not in card["lt_de"][2] and "€" in card["eu_en"][0]
          and PAY0.CONSENT_TEXT["de"] in card["lt_de"][1], card["eu_en"][0][:400])

# ---------------------------------------------------------------------------------------------- J. hygiene
bad = []
for f in ("api/_lib/pay.py", "api/checkout.py", "api/_lib/withdraw.py", "api/_lib/ops.py", "src/shared/legal.ts",
          "src/shared/LegalLinks.tsx", "src/legal/patch.ts", "src/legal/editions.ts", "src/legal/docs/terms.ts",
          "src/legal/docs/withdrawal.ts", "src/legal/docs/privacy.ts", "src/legal/docs/imprint.ts", "src/legal/LegalApp.tsx",
          "src/legal/plain.ts", "src/legal/facts.ts", "src/landing/copy.ts", "src/landing/lang.tsx", "src/order/copy.ts",
          "src/order/WithdrawPanel.tsx", "src/order/api.ts", "src/try/BuyCard.tsx"):
    t = open(os.path.join(H.REPO, f), encoding="utf-8").read()
    if any(ch in t for ch in DASHES) or any(ord(ch) < 32 and ch not in "\n\t\r" for ch in t):
        bad.append(f)
check("J1 no en/em dashes or control characters in the files of this step", not bad, bad)
r = subprocess.run(["node", os.path.join(H.REPO, "scripts", "check_prices.mjs")], cwd=H.REPO, capture_output=True, text=True,
                   encoding="utf-8", timeout=120)
check("J2 npm run check:prices passes (no AU price written by hand in the new texts)", r.returncode == 0 and "price check ok" in r.stdout,
      (r.stdout, r.stderr))
customer = json.dumps([PACK, pay.CONSENT_TEXT_AU, pay.SUBMIT_NOTE_AU, CL["copy"], CL["checkoutAu"], CL["orderAcl"]], ensure_ascii=False)
check("J3 no customer-facing text anywhere says 'Tax invoice'", not re.search(r"tax invoice", customer, re.I))

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
api.shutdown()
stub.shutdown()
sys.exit(1 if fails else 0)
