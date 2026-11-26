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
# 1005 refresh (2026-10-05, WP12 of the v3 engine build: checkout, e-mails, legal texts). The EU edition changed on purpose, and A1, B1, B2, B3 and E8
# (every one a pin of the old text or date, none a defect) moved to the new text, each keeping its id and the old name as the start of its name, with the
# reason added after " - 1005:". eu_wp12.json is the EXACT pin of the EU edition as of that work (same layout as eu_1acef38.json, which stays as the base:
# the old differences from eu_before.json are still checked on it, and the new difference from it is listed in TERMS12 and PRIV12 below):
#   terms:   "preview" (the same arrangement of the eyes; a preview of five to eight eyes is coarser), "prices" (price classes: Clean Iris, any other
#            style, two eyes in any style, each further eye; no list of styles, no number of eyes), "delivery" (no promise of half a minute per eye)
#   privacy: "iris" (the example names no style), "orders" (the order of the eyes, the date, the look, the derived eye profile, the plan code to Stripe),
#            "retention" and "storage" (the same facts in the lists); one LEGAL_UPDATED (2026-10-05) for every page and the pack; the consent
#            version and the checkbox texts are untouched.
# 1006 refresh (2026-10-06, WP18 of the v3 engine build: the catalogue switch). The cutover publishes the AI-made material sentence (src/shared/aiMaterial.ts) in the
# terms of every language and moves LEGAL_UPDATED to 2026-10-06. A1, B1, B3 and E8 (pins of the date and of the terms text, none a defect) moved to the new text, each
# keeping its id and the older names, with " - 1006:" added. eu_wp18.json is the EXACT pin of the EU edition as of that work (same layout as eu_wp12.json, which stays
# as the base: the 1005 differences from eu_1acef38.json are still checked on it, and the 1006 difference from it is ONE block of the terms ("product": the sentence,
# in en and de) and one paragraph of the pack's terms; the withdrawal page, the privacy policy, the imprint, the checkbox wording and the seller are equal to the pin of WP12):
#   terms:   "product" gains the sentence about AI-made material from a shared library (decision 10 of the specification, published with the first plate style)
#   one LEGAL_UPDATED (2026-10-06) for every page and the pack; the consent version and the checkbox texts are untouched.
# 1028 refresh (2026-10-28, Croatian, the fifth language, in the EU edition only). The consent version moves to 2026-10-28.1 (the Croatian checkbox text added; the
# en, de, lt, hu and AU texts are the ones of 2026-09-30.2, which still quotes them), LEGAL_UPDATED to 2026-10-28, and the EU edition changed on purpose in two blocks:
# the terms' "contract" sentence names Croatian too, and the legal notice's "images" says "our own eye" instead of "the founder's own eye" (the owner's rule: no
# founder named). A1, A3, B1, B3, C2, D2, E1 and E8 (pins of the version, the date and these two blocks, none a defect) moved, each keeping its id and the older
# names, with " - 1028:" added. eu_hr.json is the EXACT pin of the EU edition as of this work (same layout as eu_counter.json, which stays as the base: the 1006
# difference is now checked between the pins of WP12 and of the counter, and the 1028 difference from the counter's pin is TERMS28 and IMPRINT28 below).
# 1028b refresh (2026-10-28, the US market and its legal edition, the owner's decisions of 2026-10-27/28). The consent version moves to 2026-10-28.2 (the US
# checkbox text added, with the consent to the use of the eye photos; the EU and AU texts are the ones of 2026-10-28.1, which still quotes them); LEGAL_UPDATED
# stays 2026-10-28 (no EU text changed: the US edition is new). us is an edition market of its own (EDITION_MARKETS au, hu, us; US_MARKETS us, ACL_MARKETS stays
# au), hr and uk read the EU edition (uk is not sold in: selectable 0), and GET /api/checkout names the US checkbox under consent.markets. A1, A5, D1, D2, E1, E8
# and K0 (pins of the version, of the list of editions, of consent.markets and of the buy cards rendered; none a defect) moved, each keeping its id and the
# older names, with " - 1028b:" added; section U is the US market, checked the way sections A to K check the Australian one.
# 1028c refresh (2026-10-28, prints of the artwork: src/legal/docs/prints.ts, api/_lib/prints.py). The consent version moves to 2026-10-28.3 (the print box added in
# five languages, CHECKOUT_LEGAL[l].printConsent; every withdrawal waiver as it was and still quoted under 2026-10-28.2); LEGAL_UPDATED stays 2026-10-28. The EU
# edition (src/legal/editions.ts: the raw docs with the print sections applied) changed on purpose: the terms gain the section "prints" after "delivery" and one block
# each in product and prices (replaced) and in withdrawal and defects (added); the withdrawal page the section "prints" after "expiry"; the privacy policy the section
# "prints" after "orders", one item in the list of services and one line in retention. eu_prints.json is the EXACT pin of the EU edition as of this work
# (snap_eu_edition.mjs: from the editions), eu_hr.json stays as the base of the steps before it. A1, A3, B1, B2b, B3 and U3 moved, each keeping its id and the older
# names, with " - 1028c:" added; the AU and US editions are made from the texts before and carry no print (C and U pin them as before).
# 1111g refresh (2026-11-11, gift vouchers: src/legal/docs/vouchers.ts, api/_lib/voucher.py). The EU edition changed on purpose, the raw docs did not (the AU and US
# editions are made from them and sell no voucher): the terms gain the section "vouchers" after "prices" and one block added in "prices" (the sentence that points to
# it); the withdrawal page the section "vouchers" after "expiry"; the privacy policy the section "vouchers" after "orders" and one row in the retention table (the
# block with the row replaces the one without it). The legal notice, the checkout wording, the consent version and LEGAL_UPDATED (2026-11-11, the same day) are as
# they were. eu_gift.json is the EXACT pin of the EU edition as of this work (snap_eu_edition.mjs), eu_cap.json stays as the base of the 1111 step, which is now
# checked between the pins of the prints and of the ceiling. B1, B2b and B3 moved, each keeping its id and the older names, with " - 1111g:" added.
# 1113 refresh (2026-11-13, Finnish, Estonian and Latvian: the site's sixth, seventh and eighth language, in the EU edition only, src/legal/docs/*.fi.ts,
# *.et.ts, *.lv.ts). The consent version moves to 2026-11-13.1 (the three checkbox texts and print boxes added; every older text as it was and still quoted
# under 2026-10-28.3), LEGAL_UPDATED to 2026-11-13, and the EU edition changed on purpose in ONE block of its English and German texts: the terms'
# "contract" sentence names the three languages too. eu_langs3.json is the EXACT pin of the EU edition as of this work (snap_eu_edition.mjs: eight
# languages), eu_gift.json stays as the base: the 1111g step is now checked between the pins of the ceiling and of the vouchers. A1, A3, B1, B3 and U3
# moved, each keeping its id and the older names, with " - 1113:" added; the AU, US and HU editions carry none of the three languages.
# 1121 refresh (2026-11-21, the print offered AFTER the purchase: a print is ordered from the order page once the artwork is delivered, as a contract of its
# own; src/legal/docs/prints.ts, api/_lib/prints.py the add-on). The EU edition changed on purpose in its print paragraphs, in every language: the terms'
# product sentence ("afterwards, from your order page") and three paragraphs of the section "prints" (the first one: where and when a print is ordered; the
# delivery paragraph: production starts when it is ordered; the no-withdrawal paragraph: its last sentence, a contract of its own), the withdrawal page's
# paragraph of its section "prints" and the first paragraph of the privacy policy's section "prints". The print box, the checkout wording, the consent version
# and the legal notice are as they were; LEGAL_UPDATED moves to 2026-11-21. eu_printlater.json is the EXACT pin of the EU edition as of this work
# (snap_eu_edition.mjs), eu_langs3.json stays as the base: the 1113 step is now checked between the pins of the vouchers and of the three languages.
# A1, B1, B3 and E8 moved, each keeping its id and the older names, with " - 1121:" added; the AU and US editions are made from the raw docs and carry no print.
# The same release carries the legal wording fixes of the machine proofreading (Finnish, Estonian and Latvian only: PROOF1121 names every sentence), so the
# step of those three languages is the print paragraphs AND those sentences, each held by its words.
# 1124 refresh (2026-11-24, the owner's decisions: the final list of prints, api/_lib/print_offer.py: acrylic glass 30, 40 and 60 cm as before; glossy metal 30,
# 40 and 60 cm; the canvas WITHOUT an outer frame, on its wooden stretcher frame, 40 and 60 cm (the canvas in a black floating frame is gone); the poster as
# before; the acrylic block 10 and 20 cm; the keyring is in the offer but not offered, so the terms do not list it). The EU edition changed on purpose in ONE
# block, in every language: the list of prints and prices of the terms' section "prints" (src/legal/docs/prints.ts productRows makes it from the offer): eleven
# rows where five were, the three acrylic rows and the poster's exactly as they were, the canvas' old row gone; and the shipping table under it, a second
# block: its four rows as they were, and three rows more for the metal print and the canvas of 60 cm, which ship on a tariff of their own (6.99 EUR to Germany,
# 8.49 to seven countries near it, 13.49 to the others). The other prints ship at the prices of before. And a third block, the delivery paragraph: ONE
# passage of it is other in every language, the times (they were "about 3 business days" of production for every print and "2 to 9 business days" of delivery
# with four examples; they are merchOne's published times from api/_lib/print_times.py: 2 business days for a canvas or a poster and 3 for every other print,
# then 4 to 6 working days to Lithuania, Latvia and Estonia, 5 to 8 to Finland, 3 to 6 to Germany, about a week to the other countries); the paragraph's
# beginning (production starts when the print is ordered) and its end (the tracked parcel, 30 days at the latest) are word for word. As they were: the withdrawal page,
# the privacy policy, the legal notice, the print box, the checkout wording and the consent version; LEGAL_UPDATED moves to 2026-11-24. eu_block.json is the
# EXACT pin of the EU edition as of this work (snap_eu_edition.mjs), eu_printlater.json stays as the base: the 1121 step is now checked between the pins of
# the three languages and of the print offered later. A1, B1, B3 and E8 moved, each keeping its id and the older names, with " - 1124:" added; the AU and US
# editions are made from the raw docs and carry no print.
# 1125 refresh (2026-11-25, the owner's decision: the Meta pixel and the Conversions API, for everyone, no banner). The EU edition changed on purpose in its PRIVACY
# POLICY only, in every one of the eight languages: a new section "meta" right after "operations" (seven blocks: who and what, the reports, what is never sent, the
# cookies and the session storage key, the server's report of a payment, the purpose, the legal basis and the joint responsibility, how to object), and one block each
# of "website" (the tools of other companies: one, the Meta pixel), "orders" (the Stripe metadata of a payment also carries fbp, fbc, the IP and the user agent),
# "retention" (a row for Meta's cookies and reports: the table is one block), two of "services" (Meta in the list, which is one block, and Meta named beside Stripe
# in the paragraph after it) and two of "storage" (the first block: our pages set no cookie of their own, the pixel sets two; and the click number in the campaign
# code's paragraph). The terms, the withdrawal page, the legal notice, the checkout wording and the consent version are as they were; LEGAL_UPDATED moves to
# 2026-11-25. eu_pixel.json is the EXACT pin of the EU edition as of this work (snap_eu_edition.mjs), eu_block.json stays as the base: the 1124 step is now checked
# between the pins of the print offered later and of the list of prints. eu_pixel_raw.json (snap_eu.mjs) is the raw docs as of this work, the base of the
# Australian and US editions' privacy policy, held to eu_cap_raw.json plus exactly the same blocks (en, de). A1, B1, B3 and E8 moved with " - 1125:" added.
# 1125c refresh (2026-11-25, the owner's decision, the SECOND one of that day: no checkbox in the buy card but on the US market; the rule is stated in the refund
# conditions only: by paying, the customer agrees that we start making the file at once and that the contract can no longer be withdrawn from once we have
# started; nothing about it on Stripe's page, in the confirmation email or elsewhere; the first decision of that day, an order without the box keeping its 14
# days, was never released). The EU edition changed on purpose in its TERMS and its WITHDRAWAL PAGE only, in all eight languages: the terms by exactly the
# section "withdrawal" (two blocks for its one: the rule in plain words, and the withdrawal before we start); the withdrawal page by its lead, the blocks of
# "expiry" (three for the four with the checkbox) and the first block of "online" (no withdrawal link in the email any more). The privacy policy, the legal
# notice and the checkout wording (the box texts stay, for the US market and the old orders that quote them) as they were; the consent version and
# LEGAL_UPDATED (2026-11-25) as they were. eu_terms.json is the EXACT pin of the EU edition as of this work (snap_eu_edition.mjs), eu_pixel.json stays as the
# base: the 1125 step is now checked between the pins of the list of prints and of the pixel; eu_terms_raw.json (snap_eu.mjs) holds the raw docs the same
# way. A new order of every market but the US records that it was placed under the terms of that date (consent kind "by_terms", version LEGAL_NOW, box false)
# and is treated as an order with the ticked consent was (I4: lapsed once making began); its confirmation carries nothing about withdrawing (E4, E5, E9, F1,
# F2); Stripe shows no note in English and German and none on the Australian market (D2 to D5). Orders that hold a ticked consent are read and mailed as
# before (F1 to F3, H2). The US market keeps its box (U). B1, B3, C9, C16, D2 to D5, E1, E4, E5, E8, E9, F1 to F3, H2, I4, K1 to K3 and U8 moved with
# " - 1125c:" added.
# 1125v refresh (2026-11-25, the owner's decision of 2026-11-25 (value vouchers): a gift voucher is an amount, 30, 60, 100, 120 or 170 EUR, and a balance
# spent on several orders, artworks and prints, until it is used up within its 12 months; api/_lib/voucher.py). The EU edition changed on purpose in its
# TERMS and its PRIVACY POLICY only, in all eight languages, and only inside their section "vouchers": the terms by exactly THREE blocks of it replaced
# (the intro: a code worth the amount chosen, for artworks and prints; the table: one row of the five amounts for the two rows of the old kinds' prices;
# the rules: several orders until spent, the difference paid, the rest at the end not paid out), its contract and withdrawal blocks word for word (the
# withdrawal from an unused voucher is as it was); the privacy policy by exactly ONE block of it (the record notes the order, the amount and the session of
# each order paid with the voucher, and each such order gets a single-use discount of that amount at Stripe). The withdrawal page, the legal notice and
# the checkout wording as they were; the consent version and LEGAL_UPDATED (2026-11-25) as they were. eu_value.json is the EXACT pin of the EU edition as
# of this work (snap_eu_edition.mjs), eu_terms.json stays as the base: the 1125c step is now checked between the pins of the pixel and of the refund
# conditions. eu_value_raw.json (snap_eu.mjs) holds the raw docs: they did not change (the AU and US editions sell no voucher), only the pack inside it.
# B1, B2 and B3 moved with " - 1125v:" added.
# 1126 refresh (2026-11-26, the owner's decision: every free preview's photo and result are kept 30 days for his quality checks, api/_lib/keep.py). The EU
# edition changed on purpose in its PRIVACY POLICY and in ONE line of the checkout wording only, in all eight languages: the policy's lead (one sentence:
# the photo is used to make the artwork and to check its quality; the free previews are kept 30 days) and exactly these blocks: "preview" its second block
# replaced and one block added after its legal basis (what is kept, why, who sees it, where, 30 days, not linked to a name, an email or an IP address; the
# legal basis Art. 6(1)(f) and how to object or ask for deletion), "orders" its first block (the order keeps no full phone photo, the preview's copy apart),
# "retention" its table (the free previews' row), "services" its list (Supabase holds the copies too); the checkout wording by photoNotice alone (the photo
# step's line: kept 30 days to check quality). The terms, the withdrawal page, the legal notice, the pack and the consent version as they were; LEGAL_UPDATED
# is the lead's to raise. eu_keep.json is the EXACT pin of the EU edition as of this work (snap_eu_edition.mjs), eu_value.json stays as the base: the 1125v
# step is now checked between the pins of the refund conditions and of the value vouchers. eu_keep_raw.json (snap_eu.mjs) holds the raw docs the same way
# (their privacy policy, en and de, is the base of the AU and US editions, whose own sections say the 30 days too). A3, A6, B1, B2, C10 and U4 moved with
# " - 1126:" added.
import os, sys, json, time, re, subprocess, importlib.util, calendar
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
EU_1ACEF = json.load(open(os.path.join(HERE, "eu_1acef38.json"), encoding="utf-8"))   # 0930 refresh: the EU edition as of 1acef38 (the base of the 1005 refresh)
EU_WP12 = json.load(open(os.path.join(HERE, "eu_wp12.json"), encoding="utf-8"))   # 1005 refresh: the EU edition as of WP12 (the base of the 1006 refresh)
EU_WP18 = json.load(open(os.path.join(HERE, "eu_wp18.json"), encoding="utf-8"))   # 1006 refresh: the EU edition as of WP18 (the catalogue switch), the base of the 1020 refresh
EU_COUNTER = json.load(open(os.path.join(HERE, "eu_counter.json"), encoding="utf-8"))   # 1020 refresh: the EU edition with the anonymous counter's privacy paragraphs (the terms are WP18's), the base of the 1028 refresh
EU_HR = json.load(open(os.path.join(HERE, "eu_hr.json"), encoding="utf-8"))   # 1028 refresh: the EU edition with its Croatian texts (the contract sentence and the legal notice's images block changed in en and de)
EU_PRINTS = json.load(open(os.path.join(HERE, "eu_prints.json"), encoding="utf-8"))   # 1028c refresh: the EU edition with the prints (snap_eu_edition.mjs), the base is eu_hr.json
EU_CAP = json.load(open(os.path.join(HERE, "eu_cap.json"), encoding="utf-8"))   # 1111 refresh: the EU edition with the privacy paragraph of the daily ceiling of free previews (snap_eu_edition.mjs), the base is eu_prints.json; 1111g: the base of the gift vouchers
EU_GIFT = json.load(open(os.path.join(HERE, "eu_gift.json"), encoding="utf-8"))   # 1111g refresh: the EU edition with the gift vouchers (snap_eu_edition.mjs), the base is eu_cap.json; 1113: the base of the three languages
EU_LANGS3 = json.load(open(os.path.join(HERE, "eu_langs3.json"), encoding="utf-8"))   # 1113 refresh: the EU edition with its Finnish, Estonian and Latvian texts (snap_eu_edition.mjs), the base is eu_gift.json; 1121: the base of the print paragraphs
EU_PRINTLATER = json.load(open(os.path.join(HERE, "eu_printlater.json"), encoding="utf-8"))   # 1121 refresh: the EU edition whose print paragraphs say that a print is ordered after the artwork (snap_eu_edition.mjs), the base is eu_langs3.json; 1124: the base of the list of prints
EU_BLOCK = json.load(open(os.path.join(HERE, "eu_block.json"), encoding="utf-8"))   # 1124 refresh: the EU edition whose list of prints has the acrylic block and the canvas' new price (snap_eu_edition.mjs), the base is eu_printlater.json
EU_PIXEL = json.load(open(os.path.join(HERE, "eu_pixel.json"), encoding="utf-8"))   # 1125 refresh: the EU edition whose privacy policy describes the Meta pixel (snap_eu_edition.mjs), the base is eu_block.json; 1125c: the base of the refund conditions
EU_NOW = json.load(open(os.path.join(HERE, "eu_terms.json"), encoding="utf-8"))   # 1125c refresh: the EU edition with the refund conditions of the owner's second decision of 2026-11-25 (snap_eu_edition.mjs), the base is eu_pixel.json
EU_TERMS_RAW = json.load(open(os.path.join(HERE, "eu_terms_raw.json"), encoding="utf-8"))   # 1125c refresh: the raw docs the same way (snap_eu.mjs), held to eu_pixel_raw.json
EU_VALUE = json.load(open(os.path.join(HERE, "eu_value.json"), encoding="utf-8"))   # 1125v refresh: the EU edition with the value vouchers (snap_eu_edition.mjs), the base is eu_terms.json
EU_VALUE_RAW = json.load(open(os.path.join(HERE, "eu_value_raw.json"), encoding="utf-8"))   # 1125v refresh: the raw docs (snap_eu.mjs), equal to eu_terms_raw.json but for the pack
EU_KEEP = json.load(open(os.path.join(HERE, "eu_keep.json"), encoding="utf-8"))   # 1126 refresh: the EU edition whose privacy policy says the free previews are kept 30 days (snap_eu_edition.mjs), the base is eu_value.json
EU_KEEP_RAW = json.load(open(os.path.join(HERE, "eu_keep_raw.json"), encoding="utf-8"))   # 1126 refresh: the raw docs the same way (snap_eu.mjs), held to eu_value_raw.json
EU_PIXEL_RAW = json.load(open(os.path.join(HERE, "eu_pixel_raw.json"), encoding="utf-8"))   # 1125 refresh: the raw docs with the Meta pixel's privacy passages (snap_eu.mjs), the base of the AU and US editions' privacy policy
EU_CAP_RAW = json.load(open(os.path.join(HERE, "eu_cap_raw.json"), encoding="utf-8"))   # 1111 refresh: the raw docs (snap_eu.mjs), the base of the Australian and US editions' privacy policy
LEGAL_NOW = "2026-11-25"        # 1125 refresh: the Meta pixel in the privacy policy. 1124 refresh: the terms' list of prints and prices (the acrylic block, the canvas' price). 1121 refresh (2026-11-21): the print paragraphs (a print is ordered after the artwork). 1113 refresh (2026-11-13): the Finnish, Estonian and Latvian texts of the EU edition. 1111 refresh (2026-11-11): the ceiling of free previews in the privacy policy. 1028 refresh: LEGAL_UPDATED, one date for every legal page and the pack (2026-10-20 for the counter, 2026-10-06 since WP18, 2026-10-05 at WP12, 2026-09-30 before)
CONSENT_NOW = "2026-11-13.1"    # 1113 refresh: the Finnish, Estonian and Latvian texts and print boxes added, every older text as it was
CONSENT_1028C = "2026-10-28.3"  # 1028c refresh: the print box added (2026-10-28.2 since the US text, every waiver as it was). 1028b refresh: the consent version since the US text (2026-10-28.1 since the Croatian text; 2026-09-30.2 since 30efee7: the lt and hu texts added; en, de, AU as of .1)
CONSENT_1028B = "2026-10-28.2"  # 1028c refresh: the version of the US text, which still quotes every waiver
CONSENT_1028 = "2026-10-28.1"   # 1028b refresh: the version before the US text, which still quotes the EU and the AU texts of its customers
CONSENT_0930 = "2026-09-30.2"   # 1028 refresh: the version before the Croatian text, which still quotes the four texts of its customers
LANG5 = ("en", "de", "lt", "hu", "hr")   # 1113: the languages of before Finnish, Estonian and Latvian
LANG2 = ("en", "de")            # the two languages the snapshots of before the Lithuanian and Hungarian work have


def nopc(x):
    """1028c: a checkout wording without the print box (printConsent), to compare it with the pins of before the prints. 1126: and without the photo step's
    line (photoNotice), which the kept free previews changed (nophoto holds it to the pins)."""
    return {k: v for k, v in x.items() if k not in ("printConsent", "photoNotice")} if isinstance(x, dict) else x


def nophoto(x):
    """1126: a checkout wording without the photo step's line, to compare it with the pins of before the kept free previews."""
    return {k: v for k, v in x.items() if k != "photoNotice"} if isinstance(x, dict) else x


def photo_1126(new, old):
    """1126: the photo step's line of every language: the same link, and its text the old one with its sentence about the photo's use replaced by one that
    names the 30 days (and no "only" any more)."""
    return (isinstance(new, list) and isinstance(old, list) and len(new) == len(old) == 2 and new[1] == old[1] and new[0]["text"] != old[0]["text"]
            and "30" in new[0]["text"] and new[0]["text"].split(". ")[0] == old[0]["text"].split(". ")[0])
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
      " - 0930: bumped again by 30efee7 (lt and hu texts), now 2026-09-30.2; 2026-09-30.1 is still quoted (A3, H1)"
      " - 1005: LEGAL_UPDATED is 2026-10-05 (WP12), the consent version is not bumped"
      " - 1006: LEGAL_UPDATED is 2026-10-06 (WP18: the AI-made material sentence), the consent version is still not bumped"
      " - 1020: LEGAL_UPDATED is 2026-10-20 (the anonymous counter's privacy paragraphs), the consent version is still not bumped"
      " - 1028: LEGAL_UPDATED is 2026-10-28 and the consent version 2026-10-28.1 (the Croatian texts and checkbox)"
      " - 1028b: the consent version 2026-10-28.2 (the US checkbox text), LEGAL_UPDATED still 2026-10-28 (no EU text changed)"
      " - 1028c: the consent version 2026-10-28.3 (the print box), LEGAL_UPDATED still 2026-10-28"
      " - 1111: LEGAL_UPDATED is 2026-11-11 (the privacy paragraph of the daily ceiling of free previews), the consent version is not bumped"
      " - 1113: LEGAL_UPDATED is 2026-11-13 and the consent version 2026-11-13.1 (the Finnish, Estonian and Latvian texts, checkboxes and print boxes)"
      " - 1121: LEGAL_UPDATED is 2026-11-21 (the print paragraphs: a print is ordered after the artwork), the consent version is not bumped (the print box is as it was)"
      " - 1124: LEGAL_UPDATED is 2026-11-24 (the terms' list of prints and prices: the acrylic block, the canvas' price), the consent version is not bumped"
      " - 1125: LEGAL_UPDATED is 2026-11-25 (the Meta pixel in the privacy policy), the consent version is not bumped",
      pay.CONSENT_VERSION == CL["consentVersion"] == CONSENT_NOW and CONSENT_NOW != PAY0.CONSENT_VERSION
      and CL["legalUpdated"] == LEGAL_NOW == PACK["updated"],
      (pay.CONSENT_VERSION, CL["consentVersion"], CL["legalUpdated"], PACK["updated"]))
check("A2 AU checkbox: server CONSENT_TEXT_AU = client CHECKOUT_LEGAL_AU, en and de",
      all(pay.CONSENT_TEXT_AU[l] == CL["checkoutAu"][l]["withdrawalConsent"] for l in ("en", "de")),
      (pay.CONSENT_TEXT_AU, {l: CL["checkoutAu"][l]["withdrawalConsent"] for l in ("en", "de")}))
check("A3 EU checkbox and checkout wording exactly as before (text, and the old version still quotes it)"
      " - 0930: en and de word for word as before, lt and hu added by 30efee7 and pinned whole (client = server in all four), "
      "the old versions still quote the en and de text - 1028: hr added and pinned whole (client = server in all five), 2026-09-30.2 still quotes the four texts it had"
      " - 1028c: every wording as before but the print box (printConsent) added in all five languages, pinned whole to eu_prints.json"
      " - 1113: fi, et and lv added and pinned whole to eu_langs3.json (client = server in all eight); the five older wordings exactly as the pin of the vouchers has them"
      " - 1126: pinned whole to eu_keep.json; the photo step's line (photoNotice) of every language names the 30 days the free preview is kept, the rest of every wording as before",
      # English and German: as before the AU step, on the page and on the server (1028c: the print box aside, which is new)
      all(nopc(CL["checkoutEu"][l]) == nopc(EU_BEFORE["checkout"][l]) for l in LANG2)
      and all(CL["checkoutEu"][l]["printConsent"] and nopc(CL["checkoutEu"][l]) == nopc(EU_HR["checkout"][l]) and nophoto(CL["checkoutEu"][l]) == nophoto(EU_GIFT["checkout"][l]) for l in LANG5)
      and all(pay.CONSENT_TEXT[l] == PAY0.CONSENT_TEXT[l] for l in LANG2)
      # the four languages: the page's whole wording is the pin of 1acef38, and the server records the page's checkbox text
      and sorted(CL["checkoutEu"]) == ["de", "en", "et", "fi", "hr", "hu", "lt", "lv"] == sorted(pay.CONSENT_TEXT) and CL["checkoutEu"] == EU_KEEP["checkout"]
      and all(nophoto(EU_KEEP["checkout"][l]) == nophoto(EU_NOW["checkout"][l]) and photo_1126(EU_KEEP["checkout"][l]["photoNotice"], EU_NOW["checkout"][l]["photoNotice"]) for l in sorted(EU_NOW["checkout"]))
      and all(pay.CONSENT_TEXT[l] == CL["checkoutEu"][l]["withdrawalConsent"] for l in pay.LANGS) and len(pay.LANGS) == 8
      # 1028: the four texts of before the Croatian one are word for word the counter's pin, and their version still quotes them
      and all(nopc(CL["checkoutEu"][l]) == nopc(EU_COUNTER["checkout"][l]) for l in ("en", "de", "lt", "hu"))
      and pay.CONSENT_TEXTS[CONSENT_0930] == {l: EU_COUNTER["checkout"][l]["withdrawalConsent"] for l in ("en", "de", "lt", "hu")}
      # the versions: the old ones still quote what their customers ticked (en, de), the current one all four languages
      and pay.CONSENT_TEXTS[PAY0.CONSENT_VERSION] == PAY0.CONSENT_TEXT and pay.CONSENT_TEXTS["2026-09-30.1"] == PAY0.CONSENT_TEXT
      and pay.CONSENT_TEXTS[pay.CONSENT_VERSION] == pay.CONSENT_TEXT,
      (sorted(CL["checkoutEu"]), sorted(pay.CONSENT_TEXT), CL["checkoutEu"] == EU_KEEP["checkout"]))
au_en = pay.CONSENT_TEXT_AU["en"]
check("A4 AU checkbox keeps both EU elements and the ACL (express start before the period ends, losing the right, "
      "no change-of-mind cancelling, ACL not affected)",
      "expressly agree" in au_en and "before the withdrawal period ends" in au_en and "I lose my right of withdrawal" in au_en
      and "can't cancel for a change of mind" in au_en and "doesn't affect my rights under the Australian Consumer Law" in au_en
      and "ausdrücklich zu" in pay.CONSENT_TEXT_AU["de"] and "vor Ablauf der Widerrufsfrist" in pay.CONSENT_TEXT_AU["de"]
      and "mein Widerrufsrecht verliere" in pay.CONSENT_TEXT_AU["de"] and "Australian Consumer Law" in pay.CONSENT_TEXT_AU["de"], au_en)
check("A5 editions: au reads the Australian texts; eu, lt, hu and unknown the EU ones; server ACL_MARKETS = client"
      " - 0930: hu now reads the Hungarian edition (30efee7: the EU texts with forint prices, not the ACL one), "
      "server EDITION_MARKETS = client - 1028b: us reads the US edition (EDITION_MARKETS au, hu, us), hr and uk the EU one",
      CL["edition"] == {"eu": "eu", "lt": "eu", "au": "au", "hu": "hu", "zz": "eu", "us": "us", "hr": "eu", "uk": "eu"} and pay.ACL_MARKETS == ("au",)
      and CL["editionMarkets"] == {"au": "au", "hu": "hu", "us": "us"} and tuple(CL["editionMarkets"]) == pay.EDITION_MARKETS
      and tuple(m for m in CL["edition"] if CL["edition"][m] == "au") == pay.ACL_MARKETS
      and pay.acl_market("au") and not pay.acl_market("eu") and not pay.acl_market(None) and not pay.acl_market("AU")
      and pay.edition_market("au") and pay.edition_market("hu") and not pay.acl_market("hu")
      and not any(pay.edition_market(m) for m in ("eu", "lt", None, "HU", "zz")),
      (CL["edition"], pay.ACL_MARKETS, pay.EDITION_MARKETS, CL["editionMarkets"]))
cf = CL["checkoutFor"]
check("A6 checkoutLegal: au gets the AU checkbox and a link to terms#australia; eu and lt the EU wording as before - 1028c: and the print box - 1126: and the photo step's line",
      cf["en_au"]["withdrawalConsent"] == au_en and any(p.get("section") == "australia" and p.get("doc") == "terms"
                                                         for p in cf["en_au"]["acceptance"])
      and cf["de_au"]["withdrawalConsent"] == pay.CONSENT_TEXT_AU["de"] and cf["en_au"]["continueButton"] == "Continue to payment"
      and nopc(cf["en_eu"]) == nopc(EU_BEFORE["checkout"]["en"]) and nopc(cf["en_lt"]) == nopc(EU_BEFORE["checkout"]["en"])   # 1028c: the print box aside; 1126: the photo step's line too
      and cf["en_eu"]["printConsent"] == cf["en_lt"]["printConsent"], cf["en_au"]["acceptance"])
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
terms_diff = {l: doc_diff(EU_1ACEF["terms"][l], EU_BEFORE["terms"][l]) for l in LANG2}   # 1005: the old differences, on the pin of 1acef38
terms_ok = all(
    fr and sorted(d) == ["contract", "prices"] and d["contract"] == ([CONTRACT_LANGS[l][1]], [CONTRACT_LANGS[l][0]])
    and len(d["prices"][0]) == 1 and not d["prices"][1] and holds(d["prices"][0], [PRICE_TEST[l]])
    for l, (fr, d) in terms_diff.items())
same = {d: all(EU_HR[d][l] == EU_BEFORE[d][l] for l in LANG2) for d in ("withdrawal",)}   # 1028c: the withdrawal page was as before up to the pin of hr (PRINTS28C checks the step after it)
same["imprint"] = all(EU_COUNTER["imprint"][l] == EU_BEFORE["imprint"][l] for l in LANG2)   # 1028: the legal notice was as before up to the counter's pin (IMPRINT28 checks the step after it)
same["terms"] = terms_ok


def _txt(b):
    return b if isinstance(b, str) else json.dumps(b, ensure_ascii=False)


def wp12_ok(d, allowed):
    """1005: d is doc_diff's {section id: (added, removed)}: exactly the allowed sections, each with its number of blocks added and removed, every phrase of
    "has" in some added block, no phrase of "lacks" in any added block, every phrase of "was" in some removed block."""
    if sorted(d) != sorted(allowed):
        return False
    for sec, (na, nr, has, lacks, was) in allowed.items():
        add, rem = d[sec]
        if len(add) != na or len(rem) != nr:
            return False
        if not all(any(ph in _txt(b) for b in add) for ph in has) or any(ph in _txt(b) for ph in lacks for b in add):
            return False
        if not all(any(ph in _txt(b) for b in rem) for ph in was):
            return False
    return True


# 1005 refresh: what WP12 changed in the EU edition on purpose (en and de), the ALLOWED difference from eu_1acef38.json (section: blocks added, blocks removed,
# phrases the added ones hold, phrases they do not hold, phrases the removed ones hold); the texts themselves are pinned whole to eu_wp12.json
TERMS12 = {
    "en": {"preview": (1, 1, ["arrangement of the eyes", "coarser than your file"], [], []),
           "prices": (1, 1, ["One eye, Clean Iris", "One eye, any other style", "Two eyes, any style", "Each further eye"],
                      ["Studio Black", "Couple Duo", "Celestial Gold", "up to 8 eyes"], ["One eye, Studio Black", "Couple Duo"]),
           "delivery": (1, 1, [], ["half a minute"], ["about half a minute per eye"])},
    "de": {"preview": (1, 1, ["Reihenfolge der Augen", "gröber als Ihre Datei"], [], []),
           "prices": (1, 1, ["Ein Auge, Clean Iris", "Ein Auge, jeder andere Stil", "Zwei Augen, jeder Stil", "Jedes weitere Auge"],
                      ["Studio Black", "Couple Duo", "Celestial Gold", "bis zu 8 Augen"], ["Ein Auge, Studio Black", "Couple Duo"]),
           "delivery": (1, 1, [], ["halbe Minute"], ["etwa eine halbe Minute pro Auge"])},
}
PRIV12 = {
    "en": {"iris": (1, 1, ["for a pair"], ["Couple Duo"], ["Couple Duo"]),
           "orders": (3, 3, ["order of the eyes", "short record of measurements", "identifies the plan"], [], []),
           "retention": (1, 1, ["summary of the measurements"], [], []),
           "storage": (1, 1, ["a few numbers measured"], [], [])},
    "de": {"iris": (1, 1, ["Paar"], ["Couple Duo"], ["Couple Duo"]),
           "orders": (3, 3, ["Reihenfolge der Augen", "Aufzeichnung von Messwerten", "Kennung des Plans"], [], []),
           "retention": (1, 1, ["Zusammenfassung der aus Ihren Vorschauen"], [], []),
           "storage": (1, 1, ["einige daraus gemessene Zahlen"], [], [])},
}
terms12 = {l: doc_diff(EU_WP12["terms"][l], EU_1ACEF["terms"][l]) for l in LANG2}      # 1006: the 1005 step, between the two pins
terms12_ok = all(fr and wp12_ok(d, TERMS12[l]) for l, (fr, d) in terms12.items())
# 1006 refresh: what WP18 changed in the EU terms on purpose: ONE block of "product" holding the AI-made material sentence, nothing removed
TERMS18 = {"en": {"product": (1, 0, ["AI-made material from a shared library", "another customer's artwork can contain the same piece"], [], [])},
           "de": {"product": (1, 0, ["KI-erzeugtes Material aus einer gemeinsamen Bibliothek", "Kunstwerk einer anderen Person"], [], [])}}
terms18 = {l: doc_diff(EU_COUNTER["terms"][l], EU_WP12["terms"][l]) for l in LANG2}   # 1028: the 1006 step, between the pins of WP12 and of the counter (the terms of the counter's pin are WP18's)
terms18_ok = all(fr and wp12_ok(d, TERMS18[l]) for l, (fr, d) in terms18.items())
# 1028 refresh: what the Croatian work changed in the EU edition on purpose (en and de): ONE block of the terms' "contract" (the sentence of the contract languages names
# Croatian) and ONE block of the legal notice's "images" (our own eye, no founder named), each one block added and one removed
TERMS28 = {"en": {"contract": (1, 1, ["The contract languages are English, German, Lithuanian, Hungarian and Croatian."], [], [CONTRACT_LANGS["en"][1]])},
           "de": {"contract": (1, 1, ["Vertragssprachen sind Deutsch, Englisch, Litauisch, Ungarisch und Kroatisch."], [], [CONTRACT_LANGS["de"][1]])}}
IMPRINT28 = {"en": {"images": (1, 1, ["show our own eye"], ["founder"], ["the founder's own eye"])},
             "de": {"images": (1, 1, ["zeigen unser eigenes Auge"], ["Gründer"], ["das eigene Auge des Gründers"])}}
terms28 = {l: doc_diff(EU_HR["terms"][l], EU_COUNTER["terms"][l]) for l in LANG2}   # 1028c: the 1028 step, between the pins of the counter and of hr
imprint28 = {l: doc_diff(EDI["eu"]["imprint"][l], EU_COUNTER["imprint"][l]) for l in LANG2}
terms28_ok = all(fr and wp12_ok(d, TERMS28[l]) for l, (fr, d) in terms28.items()) and all(fr and wp12_ok(d, IMPRINT28[l]) for l, (fr, d) in imprint28.items())


def without(doc, sid):
    """1028c: a legal page without one of its sections (the print section is new, so doc_diff's frame compares the rest)."""
    return dict(doc, sections=[x for x in doc["sections"] if x["id"] != sid])


def after(doc, sid, prev):
    ids = [x["id"] for x in doc["sections"]]
    return sid in ids and ids.index(sid) == ids.index(prev) + 1


# 1028c refresh: what the prints changed in the EU edition on purpose (en and de): the terms' new section "prints" after "delivery", and four blocks of the shared
# sections (product and prices: the sentence replaced; withdrawal and defects: one sentence added); the withdrawal page's new section "prints" after "expiry"
TERMS28C = {"en": {"product": (1, 1, ["see [Prints](#prints)"], ["We do not sell prints"], ["We do not sell prints"]),
                   "prices": (1, 1, ["for a print, see [Prints](#prints)"], [], ["There are no delivery costs."]),
                   "withdrawal": (1, 0, ["does not apply to prints"], [], []), "defects": (1, 0, ["For prints, see"], [], [])},
            "de": {"product": (1, 1, ["siehe [Drucke](#prints)"], ["verkaufen wir nicht"], ["verkaufen wir nicht"]),
                   "prices": (1, 1, ["zu Drucken siehe [Drucke](#prints)"], [], ["Versandkosten fallen nicht an."]),
                   "withdrawal": (1, 0, ["kein Widerrufsrecht"], [], []), "defects": (1, 0, ["Zu Drucken siehe"], [], [])}}
terms28c = {l: doc_diff(without(EU_CAP["terms"][l], "prints"), EU_HR["terms"][l]) for l in LANG2}   # 1111g: the 1028c step, between the pins of hr and of the ceiling
prints28c_ok = (all(fr and wp12_ok(d, TERMS28C[l]) for l, (fr, d) in terms28c.items())
                and all(after(EU_CAP["terms"][l], "prints", "delivery") and after(EU_CAP["withdrawal"][l], "prints", "expiry")
                        and without(EU_CAP["withdrawal"][l], "prints") == EU_HR["withdrawal"][l] for l in LANG2))
# 1111g refresh: what the gift vouchers changed in the EU terms and withdrawal page on purpose (en and de): the terms' new section "vouchers" after "prices" and ONE block
# added in "prices" (the sentence that points to it), nothing removed; the withdrawal page's new section "vouchers" after "expiry", nothing else; the legal notice as it was
TERMS1111G = {"en": {"prices": (1, 0, ["A gift voucher can pay for an order", "[Gift vouchers](#vouchers)"], [], [])},
              "de": {"prices": (1, 0, ["Ein Geschenkgutschein kann eine Bestellung", "[Geschenkgutscheine](#vouchers)"], [], [])}}
terms1111g = {l: doc_diff(without(EU_GIFT["terms"][l], "vouchers"), EU_CAP["terms"][l]) for l in LANG2}   # 1113: the 1111g step, between the pins of the ceiling and of the vouchers
gift1111g_ok = (all(fr and wp12_ok(d, TERMS1111G[l]) for l, (fr, d) in terms1111g.items())
                and all(after(EU_GIFT["terms"][l], "vouchers", "prices") and after(EU_GIFT["withdrawal"][l], "vouchers", "expiry")
                        and without(EU_GIFT["withdrawal"][l], "vouchers") == EU_CAP["withdrawal"][l] and EU_GIFT["imprint"][l] == EU_CAP["imprint"][l] for l in LANG2))
# 1113 refresh: what the three languages changed in the EU edition's English and German texts on purpose: ONE block of the terms' "contract" (the sentence of the
# contract languages names Finnish, Estonian and Latvian too), one added and one removed; the withdrawal page, the privacy policy and the legal notice not at all
TERMS1113 = {"en": {"contract": (1, 1, ["The contract languages are English, German, Lithuanian, Hungarian, Croatian, Finnish, Estonian and Latvian."], [],
                                 ["The contract languages are English, German, Lithuanian, Hungarian and Croatian."])},
             "de": {"contract": (1, 1, ["Vertragssprachen sind Deutsch, Englisch, Litauisch, Ungarisch, Kroatisch, Finnisch, Estnisch und Lettisch."], [],
                                 ["Vertragssprachen sind Deutsch, Englisch, Litauisch, Ungarisch und Kroatisch."])}}
terms1113 = {l: doc_diff(EU_LANGS3["terms"][l], EU_GIFT["terms"][l]) for l in LANG2}   # 1121: the 1113 step, between the pins of the vouchers and of the three languages
langs1113_ok = (all(fr and wp12_ok(d, TERMS1113[l]) for l, (fr, d) in terms1113.items())
                and all(EU_LANGS3[d][l] == EU_GIFT[d][l] for d in ("withdrawal", "privacy", "imprint") for l in LANG2)
                and all(sorted(x["id"] for x in EDI["eu"][d][l]["sections"]) == sorted(x["id"] for x in EDI["eu"][d]["en"]["sections"]) for d in DOCS4 for l in ("fi", "et", "lv")))
# 1121 refresh: what the print offered after the purchase changed in the EU edition on purpose (en and de; section: blocks added, blocks removed, phrases the
# added blocks have, phrases they must not have, phrases the removed blocks had). The terms: the product sentence and three paragraphs of the section prints;
# the withdrawal page and the privacy policy: one paragraph of their section prints each; the legal notice: nothing
TERMS1121 = {"en": {"product": (1, 1, ["afterwards, from your order page"], ["you can also order a print"], ["you can also order a print of it"]),
                    "prints": (3, 3, ["once it is delivered", "as a contract of its own beside", "as soon as you have ordered it", "it changes nothing in the contract for your file"],
                               ["the checkout can offer", "as soon as your file is ready", "we do not make the print either"],
                               ["the checkout can offer", "as soon as your file is ready", "we do not make the print either"])},
             "de": {"product": (1, 1, ["danach auf Ihrer Bestellseite"], ["zusätzlich einen Druck"], ["zusätzlich einen Druck davon bestellen"]),
                    "prints": (3, 3, ["sobald es geliefert ist", "als eigenen Vertrag neben", "sobald Sie ihn bestellt haben", "am Vertrag über Ihre Datei ändert er nichts"],
                               ["kann die Kasse optional", "sobald Ihre Datei fertig ist", "fertigen wir auch den Druck nicht an"],
                               ["kann die Kasse optional", "sobald Ihre Datei fertig ist", "fertigen wir auch den Druck nicht an"])}}
WD1121 = {"en": {"prints": (1, 1, ["from your order page after your file is delivered, as a contract of its own"], ["that you order with it"], ["that you order with it", "we do not make the print either"])},
          "de": {"prints": (1, 1, ["auf Ihrer Bestellseite, nachdem Ihre Datei geliefert ist, als eigenen Vertrag"], ["den Sie mitbestellen"], ["den Sie mitbestellen", "fertigen wir auch den Druck nicht an"])}}
PRIV1121 = {"en": {"prints": (1, 1, ["If you order a print of your artwork", "payment page for the print"], ["If you add a print to your order"], ["If you add a print to your order"])},
            "de": {"prints": (1, 1, ["Bestellen Sie einen Druck Ihres Kunstwerks", "für den Druck"], ["Fügen Sie Ihrer Bestellung einen Druck hinzu"], ["Fügen Sie Ihrer Bestellung einen Druck hinzu"])}}
# 1121, the same release: the wording fixes of the machine proofreading of 2026-11-21 in the legal texts (they waited for a release that moves the date anyway).
# Finnish, Estonian and Latvian only; English and German are untouched. Each is one sentence in one block, named here: (blocks added, blocks removed, the new
# words, words the new block must not have, the words it replaced). Where the block is one the print paragraphs changed too (the first paragraph of the Finnish
# section prints, the Estonian product paragraph), the entry holds both; the Latvian section prints has one more block than the others (the damage paragraph).
#   fi privacy  website: "sen ainoa jälki on" (the verb agrees with "jälki"); preview and retention: "Ne poistetaan" (discarded, not "rejected")
#   fi terms    prints: the file "pysyy samana, tilasittepa tulosteen tai ette" (not the calque "on sama tulosteen kanssa tai ilman sitä")
#   et terms    product: "teie enda silmafotost (või mitme silma fotodest)"; licence: "anda teistele selle suhtes õigusi" (rights to it, every right)
#   et privacy  operations: "et fotoleht näitas" (the page has no word "ostukaart") and "kes selle reklaami kaudu tulid"; withdrawal and retention: "pärast
#               makse laekumist" (once the payment has settled); storage: "ei salvesta teie seadmesse küpsiseid" and "kes sama reklaami kaudu tulid"
#   lv terms    prints: "plaisa vai iedobums" (a dent; "iespiedums" is an imprint)
#   lv privacy  operations and storage: "kas atnāca, noklikšķinot uz šīs / tās pašas reklāmas" (who came by the advertisement, not "followed" it)
# Not applied, on purpose: the capitals "Te", "Teile", "Teilt", "Teie" of the Estonian withdrawal page's section effects are the national model's own (the file's
# header keeps the model word for word), so that page differs by its print paragraph alone.
PROOF1121 = {
    "fi": {"privacy": {"website": (1, 1, ["sen ainoa jälki on maan kaksi kirjainta"], ["jälki ovat"], ["sen ainoa jälki ovat maan kaksi kirjainta"]),
                       "preview": (1, 1, ["Ne poistetaan, kun pyyntö päättyy."], ["Ne hylätään"], ["Ne hylätään, kun pyyntö päättyy."]),
                       "retention": (1, 1, ["Ne poistetaan, kun pyyntö päättyy."], ["Ne hylätään"], ["Ne hylätään, kun pyyntö päättyy."])},
           "terms": {"prints": (3, 3, ["digitaalinen tiedostonne pysyy samana, tilasittepa tulosteen tai ette"], ["on sama tulosteen kanssa tai ilman sitä"],
                                ["on sama tulosteen kanssa tai ilman sitä"])}},
    "et": {"terms": {"product": (1, 1, ["teie enda silmafotost (või mitme silma fotodest)", "oma tellimuse lehelt"], ["fotost silmast"], ["teie enda fotost silmast (või mitmest silmast)"]),
                     "licence": (1, 1, ["anda teistele selle suhtes õigusi"], ["anda teistele sellele õigusi"], ["anda teistele sellele õigusi"])},
           "privacy": {"operations": (2, 2, ["et fotoleht näitas, et tellimine ei ole veel avatud", "kes selle reklaami kaudu tulid"], ["ostukaart", "järgisid"],
                                      ["et ostukaart näitas", "kes seda reklaami järgisid"]),
                       "withdrawal": (1, 1, ["siis alles pärast makse laekumist"], ["pärast selle lõpetamist"], ["siis alles pärast selle lõpetamist"]),
                       "retention": (1, 1, ["siis pärast makse laekumist"], ["pärast selle lõpetamist"], ["siis pärast selle lõpetamist"]),
                       "storage": (2, 2, ["See veebileht ei salvesta teie seadmesse küpsiseid.", "kes sama reklaami kaudu tulid"], ["ei sea küpsiseid", "järgisid"],
                                   ["See veebileht ei sea küpsiseid.", "kes sama reklaami järgisid"])}},
    "lv": {"terms": {"prints": (4, 4, ["plaisa vai iedobums"], ["iespiedums"], ["plaisa vai iespiedums"])},
           "privacy": {"operations": (1, 1, ["kas atnāca, noklikšķinot uz šīs reklāmas"], ["sekoja šai reklāmai"], ["kas sekoja šai reklāmai"]),
                       "storage": (1, 1, ["kas atnāca, noklikšķinot uz tās pašas reklāmas"], ["sekoja tai pašai reklāmai"], ["kas sekoja tai pašai reklāmai"])}},
}


def _step1121(l, name, allowed_en):
    """1121: one page of one of the six later languages against the pin of the three languages: exactly the sections the print paragraphs changed in English, with
    the same numbers of blocks, and exactly the sections and sentences PROOF1121 names for that language; nothing else, and the frame equal."""
    want = {k: (v[0], v[1], [], [], []) for k, v in allowed_en.items()}
    want.update((PROOF1121.get(l) or {}).get(name) or {})
    fr, d = doc_diff(EU_PRINTLATER[name][l], EU_LANGS3[name][l])   # 1124: the 1121 step, between the pins of the three languages and of the print offered later
    return fr and wp12_ok(d, want)


later1121 = {d: {l: doc_diff(EU_PRINTLATER[d][l], EU_LANGS3[d][l]) for l in LANG2} for d in ("terms", "withdrawal", "privacy")}   # 1124: between the two pins
later1121_ok = (all(fr and wp12_ok(d, allowed[l]) for name, allowed in (("terms", TERMS1121), ("withdrawal", WD1121), ("privacy", PRIV1121)) for l, (fr, d) in later1121[name].items())
                and all(EU_PRINTLATER["imprint"][l] == EU_LANGS3["imprint"][l] for l in LANG2)
                # the other six languages changed in the same sections, block for block the same count, and nowhere else but in the sentences PROOF1121 names
                and all(_step1121(l, name, allowed["en"]) for name, allowed in (("terms", TERMS1121), ("withdrawal", WD1121), ("privacy", PRIV1121))
                        for l in ("lt", "hu", "hr", "fi", "et", "lv"))
                and all(EU_PRINTLATER["imprint"][l] == EU_LANGS3["imprint"][l] for l in ("lt", "hu", "hr", "fi", "et", "lv")))
# 1125 (2026-11-25, the owner's decision: the keyring is 20 EUR and offered): nothing of 2026-11-24 was released, so the same step holds it: the list has
# twelve rows (the keyring last, by its name alone: it has no size) and the shipping table twelve (the keyring ships on a tariff of its own: five rows
# after the three of the metal print and the canvas of 60 cm). The date stays 2026-11-24, the day the texts were last changed in words.
# 1124 refresh: what the final list of prints changed in the EU edition on purpose, in every one of the eight languages: ONE block of the terms' section
# prints, the list of prints and prices (a "dl" of [name, price] rows). Its rows are now exactly the prints that api/_lib/print_offer.py offers (on 1), in
# its order, each by the name of its kind in api/_lib/print_names.py with its size and with its price: eleven rows. The three acrylic rows and the poster's
# are the rows of before, word for word; the old fourth row (the canvas in its black floating frame, 69 EUR) is gone and no row carries its name. Nothing
# else of the terms, and nothing at all of the withdrawal page, the privacy policy and the legal notice. The names and the prices are read from the server's
# own tables, so the pin and the offer cannot drift apart.
LANG8 = ("en", "de", "lt", "hu", "hr", "fi", "et", "lv")
from _lib import print_names as _PN, print_offer as _PO, print_times as _PT
_digits = lambda t: re.sub(r"[^0-9]", "", t)


def _rows1124(l):
    """The rows the terms must list: every print the offer has on, by its kind's name in the language and its size, with the digits of its price in cents."""
    return [(_PN.PRINT_NAMES["kinds"][p["kind"]][l] + (f" {p['cm']}" if p["cm"] else ""), str(p["price"])) for p in _PO.PRINT_OFFER["products"] if p["on"] == 1]


def _ship1124(new, old, l):
    """The shipping table of the terms (rows [price, countries]): the four rows of before, word for word, then exactly three rows more for the prints that ship
    on a tariff of their own, each beginning with the names of the metal print and the canvas of 60 cm."""
    metal, canvas = _PN.PRINT_NAMES["kinds"]["metal"][l], _PN.PRINT_NAMES["kinds"]["canvas"][l]
    keyring = _PN.PRINT_NAMES["kinds"]["keyring"][l]
    return (len(old) == 4 and len(new) == 12 and new[:4] == old
            and all(r[1].startswith(metal + " 60") and (", " + canvas + " 60") in r[1] and ": " in r[1] for r in new[4:7])
            and [_digits(r[0]) for r in new[4:7]] == ["699", "849", "1349"]
            # 1125: the keyring's own tariff, five rows named by it
            and all(r[1].startswith(keyring + ": ") for r in new[7:]) and [_digits(r[0]) for r in new[7:]] == ["499", "599", "699", "849", "999"])


def _times1124(new, old):
    """The delivery paragraph (a text block, or the pack's paragraph): the same beginning and the same end, and between them the old times (3; 2 to 9; the
    examples 2 to 3, 3 to 4, 4 to 5, 5 to 6) replaced by the table's (2 and 3; 4 to 6, 5 to 8, 3 to 6), read from api/_lib/print_times.py itself."""
    if not isinstance(new, str) or not isinstance(old, str):
        return False
    i = len(os.path.commonprefix([new, old]))
    j = len(os.path.commonprefix([new[::-1], old[::-1]]))
    t = _PT.PRINT_TIMES
    want = [min(t["production"].values()), max(t["production"].values())] + t["transit"]["LT"] + t["transit"]["FI"] + t["transit"]["DE"]
    return (i >= 60 and j >= 60 and re.findall(r"[0-9]+", new[i - 1:len(new) - j + 1]) == [str(x) for x in want] == ["2", "3", "4", "6", "5", "8", "3", "6"]
            and re.findall(r"[0-9]+", old[i - 1:len(old) - j + 1]) == ["3", "2", "9", "2", "3", "3", "4", "4", "5", "5", "6"]
            and t["transit"]["LT"] == t["transit"]["LV"] == t["transit"]["EE"] and sorted(t["transit"]) == ["DE", "EE", "FI", "LT", "LV"])


def _step1124(l):
    fr, d = doc_diff(EU_BLOCK["terms"][l], EU_PRINTLATER["terms"][l])      # 1125: between the two pins
    if not fr or sorted(d) != ["prints"]:
        return False
    add, rem = d["prints"]
    if len(add) != 3 or len(rem) != 3 or not all(isinstance(b, dict) and sorted(b) == ["dl"] for b in add[:2] + rem[:2]):
        return False
    new, old = add[0]["dl"], rem[0]["dl"]
    want = _rows1124(l)
    return (len(old) == 5 and len(new) == len(want) == 12
            and all(r[0].startswith(n) and _digits(r[1]) == pr for r, (n, pr) in zip(new, want)) and all(r[0].endswith("cm") for r in new[:11])
            and new[11][0] == _PN.PRINT_NAMES["kinds"]["keyring"][l] and _digits(new[11][1]) == "2000"      # 1125: the keyring, by its name alone
            and new[:3] == old[:3] and old[4] in new and _digits(old[3][1]) == "6900" and not any(r[0] == old[3][0] for r in new)
            and _ship1124(add[1]["dl"], rem[1]["dl"], l) and _times1124(add[2], rem[2])
            and [p["id"] for p in _PO.PRINT_OFFER["products"] if p["on"] == 1] == ["acrylic30", "acrylic40", "acrylic60", "metal30", "metal40", "metal60", "canvas40",
                                                                                   "canvas60", "poster50", "block10", "block20", "keyring"]
            and [p["id"] for p in _PO.PRINT_OFFER["products"] if p["on"] != 1] == [])


block1124 = {l: _step1124(l) for l in LANG8}
block1124_ok = (all(block1124.values())
                and all(EU_BLOCK[d][l] == EU_PRINTLATER[d][l] for d in ("withdrawal", "privacy", "imprint") for l in LANG8)
                and EU_BLOCK["checkout"] == EU_PRINTLATER["checkout"])
# 1125: the Meta pixel (see the header): the privacy policy differs from the pin of the list of prints by exactly the section "meta" after "operations" and these
# blocks (added, removed) of the sections it names, each new one about the pixel; the other three pages and the checkout wording not at all, in all eight languages
PRIV1125 = {"website": (1, 1), "orders": (1, 1), "services": (2, 2), "retention": (1, 1), "storage": (2, 2)}


def _step1125(new, old):
    meta = [s for s in new["sections"] if s["id"] == "meta"]
    if len(meta) != 1 or not after(new, "meta", "operations") or len(meta[0]["blocks"]) != 7:
        return False
    first = meta[0]["blocks"][0]
    fr, d = doc_diff(without(new, "meta"), old)
    return (fr and sorted(d) == sorted(PRIV1125) and all((len(d[k][0]), len(d[k][1])) == n for k, n in PRIV1125.items())
            and "Meta Platforms Ireland Limited" in first and all(any(w in json.dumps(d[k][0], ensure_ascii=False) for w in ("#meta", "_fbp")) for k in PRIV1125))


pixel1125 = {l: _step1125(EU_PIXEL["privacy"][l], EU_BLOCK["privacy"][l]) for l in LANG8}      # 1125c: between the two pins
pixel1125_raw = {l: _step1125(EU_PIXEL_RAW["privacy"][l], EU_CAP_RAW["privacy"][l]) for l in LANG2}
pixel1125_ok = (all(pixel1125.values()) and all(pixel1125_raw.values())
                and all(EU_PIXEL[d][l] == EU_BLOCK[d][l] for d in ("terms", "withdrawal", "imprint") for l in LANG8)
                and EU_PIXEL["checkout"] == EU_BLOCK["checkout"])
# 1125c (the owner's second decision of 2026-11-25, see the header): the terms differ from the pin of the pixel by exactly the section "withdrawal" (two blocks for
# one, the first with the rule in bold); the withdrawal page by its lead, the blocks of "expiry" (three for four, the box gone) and the first block of "online"; the
# privacy policy, the legal notice and the checkout wording not at all, in all eight languages; the raw docs the same way (en, de)


def _step1125c(ed, was):
    t_fr, t_d = doc_diff(ed["terms"], was["terms"])
    nw = dict(ed["withdrawal"], lead=was["withdrawal"]["lead"])
    w_fr, w_d = doc_diff(nw, was["withdrawal"])
    exp_new = next(s for s in ed["withdrawal"]["sections"] if s["id"] == "expiry")
    exp_old = next(s for s in was["withdrawal"]["sections"] if s["id"] == "expiry")
    return (t_fr and sorted(t_d) == ["withdrawal"] and (len(t_d["withdrawal"][0]), len(t_d["withdrawal"][1])) == (2, 1)
            and t_d["withdrawal"][0][0].count("**") == 2 and ed["withdrawal"]["lead"] != was["withdrawal"]["lead"]
            and w_fr and sorted(w_d) == ["expiry", "online"] and (len(w_d["expiry"][0]), len(w_d["expiry"][1])) == (3, 4)
            and (len(w_d["online"][0]), len(w_d["online"][1])) == (1, 1)
            and not any(isinstance(b, dict) and "box" in b for b in exp_new["blocks"]) and any(isinstance(b, dict) and "box" in b for b in exp_old["blocks"]))


def _doc_of(pin, l):
    return {d: pin[d][l] for d in ("terms", "withdrawal")}


terms1125c = {l: _step1125c(_doc_of(EU_NOW, l), _doc_of(EU_PIXEL, l)) for l in LANG8}      # 1125v: between the pins of the pixel and of the refund conditions
terms1125c_raw = {l: _step1125c(_doc_of(EU_TERMS_RAW, l), _doc_of(EU_PIXEL_RAW, l)) for l in LANG2}
terms1125c_ok = (all(terms1125c.values()) and all(terms1125c_raw.values())
                 and all(EU_NOW[d][l] == EU_PIXEL[d][l] for d in ("privacy", "imprint") for l in LANG8)
                 and EU_NOW["checkout"] == EU_PIXEL["checkout"] and all(EU_TERMS_RAW["privacy"][l] == EU_PIXEL_RAW["privacy"][l] for l in LANG2))
# 1125v (value vouchers, see the header): the terms differ from the pin of the refund conditions by exactly three blocks of the section vouchers (intro, the table
# of the amounts, the rules), its contract and withdrawal blocks word for word; the privacy policy by exactly one block of its section vouchers; the withdrawal
# page, the legal notice and the checkout wording not at all, in all eight languages; the raw docs not at all
_AMOUNTS = (3000, 6000, 10000, 12000, 17000)


def _step1125v(l):
    t_fr, t_d = doc_diff(EU_VALUE["terms"][l], EU_NOW["terms"][l])      # 1126: between the pins of the refund conditions and of the value vouchers
    p_fr, p_d = doc_diff(EU_VALUE["privacy"][l], EU_NOW["privacy"][l])
    if not (t_fr and p_fr and sorted(t_d) == ["vouchers"] and sorted(p_d) == ["vouchers"]):
        return False
    add, rem = t_d["vouchers"]
    new = next(s for s in EU_VALUE["terms"][l]["sections"] if s["id"] == "vouchers")["blocks"]
    old = next(s for s in EU_NOW["terms"][l]["sections"] if s["id"] == "vouchers")["blocks"]
    table = next((b for b in add if isinstance(b, dict) and "dl" in b), None)
    eur = [_digits(r[1]) for r in (table or {}).get("dl", [])]
    return ((len(add), len(rem)) == (3, 3) and len(new) == len(old) == 5 and new[3:] == old[3:] and table is not None and len(table["dl"]) == 1
            and all(str(a) in eur[0] for a in _AMOUNTS) and len(next(b for b in rem if isinstance(b, dict) and "dl" in b)["dl"]) == 2
            and (len(p_d["vouchers"][0]), len(p_d["vouchers"][1])) == (1, 1) and "12" in new[2])


value1125v = {l: _step1125v(l) for l in LANG8}
value1125v_ok = (all(value1125v.values()) and all(EU_VALUE[d][l] == EU_NOW[d][l] for d in ("withdrawal", "imprint") for l in LANG8)
                 and EU_VALUE["checkout"] == EU_NOW["checkout"] and all(EU_VALUE_RAW[d] == EU_TERMS_RAW[d] for d in ("terms", "withdrawal", "privacy", "imprint", "checkout")))
# 1126 (the kept free previews, see the header): the privacy policy differs from the pin of the value vouchers by its lead and exactly the blocks of PRIV1126, each
# new one about the 30 days; the terms, the withdrawal page and the legal notice not at all, in all eight languages; the raw docs (en, de) the same way
PRIV1126 = {"preview": (2, 1), "orders": (1, 1), "retention": (1, 1), "services": (1, 1)}


def _step1126(new, old, basis=None):
    """1126: one language's policy against the pin of the value vouchers: the lead and exactly the blocks of PRIV1126, every new one naming the 30 days; basis: a
    phrase of the legal basis the new blocks of "preview" must hold (the English one)."""
    fr, d = doc_diff(dict(new, lead=old["lead"]), old)
    return (fr and new["lead"] != old["lead"] and "30" in new["lead"] and sorted(d) == sorted(PRIV1126)
            and all((len(d[k][0]), len(d[k][1])) == n for k, n in PRIV1126.items())
            and all("30" in json.dumps(d[k][0], ensure_ascii=False) for k in PRIV1126)
            and (basis is None or basis in json.dumps(d["preview"][0], ensure_ascii=False)))


keep1126 = {l: _step1126(EU_KEEP["privacy"][l], EU_VALUE["privacy"][l], "Art. 6(1)(f) GDPR" if l == "en" else None) for l in LANG8}
keep1126_raw = {l: _step1126(EU_KEEP_RAW["privacy"][l], EU_VALUE_RAW["privacy"][l]) for l in LANG2}
keep1126_ok = (all(keep1126.values()) and all(keep1126_raw.values())
               and all(EDI["eu"][d][l] == EU_VALUE[d][l] for d in ("terms", "withdrawal", "imprint") for l in LANG8)
               and all(EU_KEEP_RAW[d] == EU_VALUE_RAW[d] for d in ("terms", "withdrawal", "imprint")) and EU_KEEP["pack"] == EU_VALUE["pack"])
pinned = {d: all(EDI["eu"][d][l] == EU_KEEP[d][l] for l in LANG2) for d in DOCS4}
editions4 = {d: sorted(EDI["eu"][d]) for d in DOCS4}
check("B1 EU terms, withdrawal page and legal notice exactly as before (en, de)"
      " - 0930: the terms differ from before by exactly the contract languages sentence (30efee7) and the price list sentence "
      "(1acef38); all pinned to eu_1acef38.json; lt and hu editions present"
      " - 1005: the pin is eu_wp12.json, and the terms differ from the pin of 1acef38 by exactly the three blocks of TERMS12 (preview, prices, delivery)"
      " - 1006: the pin is eu_wp18.json, and the terms differ from the pin of WP12 by exactly the one block of TERMS18 (the AI-made material sentence)"
      " - 1028: the pin is eu_hr.json; the terms and the legal notice differ from the counter's pin by exactly the blocks of TERMS28 and IMPRINT28 (Croatian named as a"
      " contract language, our own eye); hr editions present"
      " - 1028c: the pin is eu_prints.json; the terms differ from the pin of hr by exactly the section prints and the four blocks of TERMS28C, the withdrawal page by"
      " exactly its section prints"
      " - 1111g: the pin is eu_gift.json; the 1028c step is checked between the pins of hr and of the ceiling; the terms differ from the pin of the ceiling by exactly the section"
      " vouchers and the one block of TERMS1111G, the withdrawal page by exactly its section vouchers, the legal notice not at all"
      " - 1113: the pin is eu_langs3.json; the 1111g step is checked between the pins of the ceiling and of the vouchers; the terms differ from the pin of the vouchers by"
      " exactly the one block of TERMS1113 (Finnish, Estonian and Latvian named as contract languages), the other three pages not at all; fi, et and lv editions present"
      " with the sections of the English ones"
      " - 1121: the pin is eu_printlater.json; the 1113 step is checked between the pins of the vouchers and of the three languages; the terms differ from the pin of the three"
      " languages by exactly the product sentence and three paragraphs of the section prints (a print is ordered from the order page after the artwork is delivered, as a"
      " contract of its own), the withdrawal page and the privacy policy by exactly one paragraph of their section prints, the legal notice not at all, in all eight languages;"
      " the Finnish, Estonian and Latvian texts also by exactly the sentences of the proofreading that PROOF1121 names (their new words there, their old words gone)"
      " - 1124: the pin is eu_block.json; the 1121 step is checked between the pins of the three languages and of the print offered later; the terms differ from the pin"
      " of the print offered later by exactly ONE block in each of the eight languages, the list of prints and prices of the section prints (the eleven prints the"
      " offer has on, by the server's own names and prices: the acrylic rows and the poster's as they were, the canvas in its floating frame gone), and by the"
      " shipping table under it (its four rows as they were, three more for the metal print and the canvas of 60 cm), and by ONE passage of the delivery"
      " paragraph, the times (merchOne's published ones from api/_lib/print_times.py for the one sentence of before); the withdrawal"
      " page, the privacy policy and the legal notice not at all"
      " - 1125: the pin is eu_pixel.json; the 1124 step is checked between the pins of the print offered later and of the list of prints; the privacy policy differs from"
      " the pin of the list of prints by exactly the section meta (the Meta pixel) and the blocks of PRIV1125, in all eight languages, and the raw docs from eu_cap_raw.json"
      " the same way (en, de); the terms, the withdrawal page and the legal notice not at all"
      " - 1125c: the pin is eu_terms.json; the 1125 step is checked between the pins of the list of prints and of the pixel; the refund conditions of the owner's"
      " second decision of 2026-11-25: the terms differ from the pin of the pixel by exactly the section withdrawal (two blocks for one, the rule in bold), the"
      " withdrawal page by its lead, the blocks of expiry (three for the four with the checkbox) and the first block of online, in all eight languages, and the raw"
      " docs from eu_pixel_raw.json the same way (en, de); the privacy policy, the legal notice and the checkout wording not at all"
      " - 1125v: the pin is eu_value.json; the 1125c step is checked between the pins of the pixel and of the refund conditions; the value vouchers (the owner's"
      " decision of 2026-11-25): the terms differ from the pin of the refund conditions by exactly three blocks of the section vouchers (the intro, one row of the"
      " five amounts for the two prices, the rules), its contract and withdrawal blocks as they were, and the privacy policy by exactly one block of its section"
      " vouchers, in all eight languages; the withdrawal page, the legal notice, the checkout wording and the raw docs not at all"
      " - 1126: the pin is eu_keep.json; the 1125v step is checked between the pins of the refund conditions and of the value vouchers; the kept free previews (the owner's"
      " decision of 2026-11-26): the privacy policy differs from the pin of the value vouchers by its lead and exactly the blocks of PRIV1126 (preview two for one, orders,"
      " retention and services one each), in all eight languages, and the raw docs the same way (en, de); the terms, the withdrawal page, the legal notice and the pack not at all",
      all(same.values()) and terms12_ok and terms18_ok and terms28_ok and prints28c_ok and gift1111g_ok and langs1113_ok and later1121_ok and block1124_ok and pixel1125_ok and terms1125c_ok and value1125v_ok and keep1126_ok and all(pinned.values()) and all(v == ["de", "en", "et", "fi", "hr", "hu", "lt", "lv"] for v in editions4.values()),
      (same, keep1126, keep1126_raw, value1125v, terms12_ok, terms18_ok, terms28_ok, prints28c_ok, gift1111g_ok, langs1113_ok, later1121_ok, block1124_ok, block1124, pixel1125, pixel1125_raw, terms1125c, terms1125c_raw, {n: {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in x.items()} for n, x in later1121.items()}, {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in terms1111g.items()}, {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in terms28c.items()}, pinned, editions4, {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in terms18.items()}))
priv_diff = {l: doc_diff(EU_1ACEF["privacy"][l], EU_BEFORE["privacy"][l]) for l in LANG2}   # 1005: the old differences, on the pin of 1acef38
priv_ok = {l: fr and sorted(d) == sorted(PRIV_ALLOWED[l])
           and all(len(d[sec][0]) == na and len(d[sec][1]) == nr and holds(d[sec][0], pa) and holds(d[sec][1], pr)
                   for sec, (na, nr, pa, pr) in PRIV_ALLOWED[l].items() if sec in d)
           for l, (fr, d) in priv_diff.items()}
priv_diff12 = {l: doc_diff(EU_WP18["privacy"][l], EU_1ACEF["privacy"][l]) for l in LANG2}      # 1020: the policy as of WP18 against the pin of 1acef38 (the live one is checked against WP18 in B2b)
priv12_ok = {l: fr and wp12_ok(d, PRIV12[l]) for l, (fr, d) in priv_diff12.items()}
priv_pinned = {l: EDI["eu"]["privacy"][l] == EU_KEEP["privacy"][l] for l in LANG2}      # 1125v: the pin of the value vouchers; 1126: of the kept free previews
check("B2 EU privacy policy: only two sentences added per language (the market key, the country hint), all else as before"
      " - 0930: plus the language switch sentence (30efee7) and the price test sentences (1acef38: the anonymous visitor number, "
      "the events, the data passed to Stripe); pinned to eu_1acef38.json"
      " - 1005: pinned to eu_wp12.json; the policy differs from the pin of 1acef38 by exactly the blocks of PRIV12 (the example without a style, the order of the "
      "eyes, the date, the look, the derived eye profile, the plan code to Stripe, the same facts in the retention and storage lists)"
      " - 1125v: pinned to eu_value.json (its one block of the section vouchers is held by B1) - 1126: pinned to eu_keep.json (the kept free previews, held by B1)",
      all(priv_ok.values()) and all(priv12_ok.values()) and all(priv_pinned.values()),
      (priv_ok, priv12_ok, priv_pinned, {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in priv_diff12.items()}))


# 1020: the privacy policy now differs from the WP18 pin by exactly the anonymous counter's paragraphs (api/_lib/counter.py): the country sentence (website), the counter and campaign paragraphs
# (operations), the session storage key (storage), the Stripe sentence (orders) and the order records row (retention); every other section, the frame and the terms are WP18's.
# Later the same day the feedback box's paragraphs joined them: the feedback paragraph (operations: one more block), the two sentences that changed in "content" and "basis" (one block added and
# one removed each) and the retention row of the feedback texts (the same table block as the order records row): operations is now 5 blocks added (counter, campaign, feedback, content, basis) and 2 removed
PRIV20 = {"website": (1, 1), "operations": (5, 2), "storage": (1, 0), "orders": (1, 1), "retention": (1, 1)}
priv20 = {l: doc_diff(EU_HR["privacy"][l], EU_WP18["privacy"][l]) for l in LANG2}   # 1028c: the 1020 step, between the pins of WP18 and of hr
priv20_ok = {l: fr and sorted(d) == sorted(PRIV20) and all((len(d[sec][0]), len(d[sec][1])) == n for sec, n in PRIV20.items()) for l, (fr, d) in priv20.items()}
# 1028c: the prints in the privacy policy: the section "prints" after "orders" (the partner, the name and the address, not the e-mail), one item of the list of
# services (the list is one block: replaced) and one line in retention
PRIV28C = {"services": (1, 1), "retention": (1, 0)}
priv28c = {l: doc_diff(without(EU_PRINTS["privacy"][l], "prints"), EU_HR["privacy"][l]) for l in LANG2}   # 1111: the 1028c step, between the pins of hr and of the prints
priv28c_ok = {l: fr and sorted(d) == sorted(PRIV28C) and all((len(d[sec][0]), len(d[sec][1])) == n for sec, n in PRIV28C.items())
              and after(EU_CAP["privacy"][l], "prints", "orders") and "Picanova" in json.dumps(EU_CAP["privacy"][l]["sections"], ensure_ascii=False)   # 1111g: on the pin of the ceiling
              for l, (fr, d) in priv28c.items()}
# 1111: the daily ceiling of free previews per connection (api/_lib/previewcap.py): one paragraph in "operations" and one line in retention, nothing else; the raw docs (the
# base of the Australian and US editions) by exactly the same two
PRIV1111 = {"operations": (1, 0), "retention": (1, 1)}   # retention is one table: the block with the new line replaces the one without it
priv1111 = {l: doc_diff(EU_CAP["privacy"][l], EU_PRINTS["privacy"][l]) for l in LANG2}   # 1111g: the 1111 step, between the pins of the prints and of the ceiling
priv1111_raw = {l: doc_diff(EU_CAP_RAW["privacy"][l], EU_HR["privacy"][l]) for l in LANG2}
priv1111_ok = {l: all(fr and sorted(d) == sorted(PRIV1111) and all((len(d[sec][0]), len(d[sec][1])) == n for sec, n in PRIV1111.items())
                      and "IP" in json.dumps(d["operations"][0], ensure_ascii=False) for fr, d in (priv1111[l], priv1111_raw[l])) for l in LANG2}
# 1111g: the gift vouchers in the privacy policy: the section "vouchers" after "orders" (the buyer's e-mail only at Stripe and in the e-mail, the code not stored) and one
# row in the retention table (the block with the row replaces the one without it), nothing else; the raw docs (the base of the AU and US editions) carry none of it
PRIV1111G = {"retention": (1, 1)}
priv1111g = {l: doc_diff(without(EU_GIFT["privacy"][l], "vouchers"), EU_CAP["privacy"][l]) for l in LANG2}   # 1113: between the pins of the ceiling and of the vouchers (B1 holds the policy of now to the pin of the vouchers)
priv1111g_ok = {l: fr and sorted(d) == sorted(PRIV1111G) and all((len(d[sec][0]), len(d[sec][1])) == n for sec, n in PRIV1111G.items())
                and after(EU_GIFT["privacy"][l], "vouchers", "orders") and not any(x["id"] == "vouchers" for x in EU_CAP_RAW["privacy"][l]["sections"])
                for l, (fr, d) in priv1111g.items()}
check("B2b EU privacy policy since WP18 (1020): only the anonymous counter's and the feedback box's paragraphs differ, in the sections website, operations, storage, orders and retention, nothing else, en and de"
      " - 1028c: checked between the pins of WP18 and of hr; the policy as it is now differs from the pin of hr by exactly the section prints, one item of the services and one retention line"
      " - 1111: the 1028c step checked between the pins of hr and of the prints; the policy as it is now differs from the pin of the prints, and the raw docs from the pin of hr, by"
      " exactly the paragraph of the daily ceiling of free previews (operations) and its retention line"
      " - 1111g: the 1111 step checked between the pins of the prints and of the ceiling; the policy as it is now differs from the pin of the ceiling by exactly the section"
      " vouchers after orders and one retention row, the raw docs carry no voucher",
      all(priv20_ok.values()) and all(priv28c_ok.values()) and all(priv1111_ok.values()) and all(priv1111g_ok.values()),
      (priv20_ok, priv28c_ok, priv1111_ok, priv1111g_ok, {l: {k: [len(v[0]), len(v[1])] for k, v in d.items()} for l, (fr, d) in priv1111g.items()}))


def _norm(t):
    """The pack's text without its date line (the date changes with every legal change)."""
    return (t.replace("2026-09-30", "X").replace("30.09.2026", "X").replace("2026-10-05", "X").replace("05.10.2026", "X")      # 1005: and the date of WP12
             .replace("2026-10-06", "X").replace("06.10.2026", "X")                                                               # 1006: and the date of WP18
             .replace("2026-10-20", "X").replace("20.10.2026", "X")                                                               # 1020: and the date of the counter's privacy paragraphs
             .replace("2026-10-28", "X").replace("28.10.2026", "X")                                                               # 1028: and the date of the Croatian texts
             .replace("2026-11-11", "X").replace("11.11.2026", "X")
             .replace("2026-11-13", "X").replace("13.11.2026", "X")
             .replace("2026-11-21", "X").replace("21.11.2026", "X")
             .replace("2026-11-24", "X").replace("24.11.2026", "X").replace("2026-11-25", "X").replace("25.11.2026", "X")                                                               # 1124: and the date of the list of prints
             # 1124: the pack of that step is compared in all eight languages, so the date line's Hungarian and Croatian forms are read too (those of the two pins compared)
             .replace("2026. 11. 21.", "X").replace("21. 11. 2026.", "X").replace("2026. 11. 24.", "X").replace("24. 11. 2026.", "X").replace("2026. 11. 25.", "X").replace("25. 11. 2026.", "X"))                                                              # 1113: and the date of the three languages                                                              # 1111: and the date of the ceiling of free previews


def _terms_pack_ok(l, pack=None):
    """The pack's EU terms = the old pack's, plus exactly one paragraph (the price list sentence) and the four contract languages.
    1005: checked on the pack of the pin of 1acef38 (the base), where it still holds; _terms_pack_12 checks the pack as it is now against that pin."""
    pack = EU_1ACEF["pack"] if pack is None else pack
    pars = pack["docs"][l]["terms"]["text"].split("\n\n")
    back = "\n\n".join(p for p in pars if PRICE_TEST[l] not in p)
    return (len([p for p in pars if PRICE_TEST[l] in p]) == 1 and back.count(CONTRACT_LANGS[l][1]) == 1
            and _norm(back.replace(CONTRACT_LANGS[l][1], CONTRACT_LANGS[l][0])) == _norm(EU_BEFORE["pack"]["docs"][l]["terms"]["text"]))


def _terms_pack_12(l):
    """1005: the pack's EU terms of the pin of WP12 = the pin of 1acef38 (date aside) with exactly the three paragraphs of the changed blocks replaced: the
    preview paragraph, the price rows, the delivery paragraph. 1006: this is checked between the two pins; _terms_pack_18 checks the pack as it is now."""
    now = _norm(EU_WP12["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    was = _norm(EU_1ACEF["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
    return (len(now) == len(was) and len(add) == 3 == len(rem) and any("Clean Iris" in p for p in add) and any("Studio Black" in p for p in rem)
            and not any("Studio Black" in p or "Couple Duo" in p for p in now)
            )


def _terms_pack_18(l):
    """1006: the pack's EU terms as they are now = the pin of WP12 (date aside) plus exactly one paragraph, the AI-made material sentence, and nothing removed; and
    the pinned pack of WP18 holds the same text. 1028: checked between the pins of WP12 and of the counter; _terms_pack_28 checks the pack as it is now."""
    now = _norm(EU_COUNTER["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    was = _norm(EU_WP12["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
    return (len(now) == len(was) + 1 and len(add) == 1 and not rem and any(k in add[0] for k in ("AI-made material from a shared library", "KI-erzeugtes Material aus einer gemeinsamen Bibliothek")))


def _terms_pack_28(l):
    """1028: the pack's EU terms as they are now = the counter's pin (date aside) with exactly one paragraph replaced, the contract languages' sentence that names
    Croatian, and nothing else; and the pinned pack of this work holds the same text."""
    now = _norm(EU_HR["pack"]["docs"][l]["terms"]["text"]).split("\n\n")      # 1028c: between the pins of the counter and of hr
    was = _norm(EU_COUNTER["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
    return (len(now) == len(was) and add == [TERMS28[l]["contract"][2][0]] and rem == [CONTRACT_LANGS[l][1]]
            and _norm(PACK["docs"][l]["terms"]["text"]) == _norm(EU_VALUE["pack"]["docs"][l]["terms"]["text"]))      # 1125v: the pack of now is the pin of the value vouchers


def _terms_pack_28c(l):
    """1028c: the pack's EU terms as they are now = the pin of hr (date aside) with the print paragraphs added and exactly the two replaced (product, prices),
    and the pinned pack of this work holds the same text. The numbered headings after the new section move by one, so the numbers are left out."""
    num = lambda p: re.sub(r"^[0-9]{1,2}\. ", "", p)
    now = [num(p) for p in _norm(EU_CAP["pack"]["docs"][l]["terms"]["text"]).split("\n\n")]   # 1111g: between the pins of hr and of the ceiling
    was = [num(p) for p in _norm(EU_HR["pack"]["docs"][l]["terms"]["text"]).split("\n\n")]
    add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
    return len(rem) == 2 and len(add) > 8 and any("Picanova GmbH" in p for p in add) and any("16" in p for p in add)


def _pack_1111g(l):
    """1111g: the pack's EU terms as they are now = the pin of the ceiling (date aside) with exactly the paragraphs of the gift vouchers added (the sentence in
    prices, the section's title and its five blocks) and nothing removed; the withdrawal page with exactly its two (title and paragraph); the pinned pack of
    this work holds the same texts. The numbered headings after the new section move by one, so the numbers are left out."""
    num = lambda p: re.sub(r"^[0-9]{1,2}\. ", "", p)
    ok = True
    for d, n, key in (("terms", 7, ("#vouchers", "12")), ("withdrawal", 2, ("14",))):
        now = [num(p) for p in _norm(EU_GIFT["pack"]["docs"][l][d]["text"]).split("\n\n")]   # 1113: between the pins of the ceiling and of the vouchers
        was = [num(p) for p in _norm(EU_CAP["pack"]["docs"][l][d]["text"]).split("\n\n")]
        add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
        ok = ok and not rem and len(add) == n and len(now) == len(was) + n and all(any(k in p for p in add) for k in key)
    return ok


def _pack_1113(l):
    """1113: the pack's EU terms of the pin of the three languages = the pin of the vouchers (date aside) with exactly one paragraph replaced, the sentence of the
    contract languages that names Finnish, Estonian and Latvian too; the withdrawal page word for word. 1121: this is checked between the two pins; _pack_1121
    checks the pack as it is now."""
    now = _norm(EU_LANGS3["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    was = _norm(EU_GIFT["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
    return (len(now) == len(was) and add == [TERMS1113[l]["contract"][2][0]] and rem == [TERMS1113[l]["contract"][4][0]]
            and _norm(EU_LANGS3["pack"]["docs"][l]["withdrawal"]["text"]) == _norm(EU_GIFT["pack"]["docs"][l]["withdrawal"]["text"]))


def _pack_1121(l):
    """1121: the pack's EU texts of the pin of the print offered later = the pin of the three languages (date aside) with exactly the print paragraphs replaced:
    four paragraphs of the terms (the product sentence's, and of the section prints the first, the delivery and the no-withdrawal one) and one of the withdrawal
    page, none added and none dropped; every new paragraph has its phrase of TERMS1121 or WD1121. 1124: this is checked between the two pins; _pack_1124 checks
    the pack as it is now."""
    ok = True
    for d, n, has in (("terms", 4, TERMS1121[l]["product"][2] + TERMS1121[l]["prints"][2]), ("withdrawal", 1, WD1121[l]["prints"][2])):
        now = _norm(EU_PRINTLATER["pack"]["docs"][l][d]["text"]).split("\n\n")
        was = _norm(EU_LANGS3["pack"]["docs"][l][d]["text"]).split("\n\n")
        add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
        ok = ok and len(now) == len(was) and len(add) == n == len(rem) and all(any(ph in p for p in add) for ph in has)
    return ok


def _pack_1124(l):
    """1124: the pack's EU terms as they are now = the pin of the print offered later (date aside) with exactly TWO paragraphs replaced: the list of prints and
    prices (eleven lines, the prints the offer has on by the server's own names, the three acrylic lines and the poster's as they were, the old canvas line
    gone) and the shipping table (its four lines of before, then three for the metal print and the canvas of 60 cm); the withdrawal page word for word; the
    pinned pack of this work holds the same texts."""
    now = _norm(EU_PIXEL["pack"]["docs"][l]["terms"]["text"]).split("\n\n")      # 1125c: the pin of the pixel (the pack of now is held to it by _pack_1125c)
    was = _norm(EU_PRINTLATER["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
    if not (len(now) == len(was) and len(add) == 3 == len(rem) and _times1124(add[2], rem[2])):      # the third: the delivery paragraph, its times from the table
        return False
    new, old = add[0].split("\n"), rem[0].split("\n")
    ship_new, ship_old = add[1].split("\n"), rem[1].split("\n")
    want = _rows1124(l)
    metal = _PN.PRINT_NAMES["kinds"]["metal"][l]
    return (len(old) == 5 and len(new) == len(want) == 12 and all(x.startswith(n) and _digits(x).endswith(pr) for x, (n, pr) in zip(new, want))
            and new[:3] == old[:3] and old[4] in new and old[3] not in new and _digits(old[3]).endswith("6900")
            and len(ship_old) == 4 and len(ship_new) == 12 and ship_new[:4] == ship_old and all((metal + " 60") in x for x in ship_new[4:7])
            and all((": " + _PN.PRINT_NAMES["kinds"]["keyring"][l] + ": ") in x for x in ship_new[7:])
            and _norm(EU_PIXEL["pack"]["docs"][l]["withdrawal"]["text"]) == _norm(EU_PRINTLATER["pack"]["docs"][l]["withdrawal"]["text"]))


def _pack_1125c(l):
    """1125c (the owner's second decision of 2026-11-25): the pack's EU terms = the pin of the pixel with exactly ONE paragraph replaced by TWO (the section
    withdrawal), the withdrawal page with exactly five paragraphs for six (the lead, the blocks of "expiry", the first of "online"), the checkbox text gone;
    the pinned pack of this work holds the same texts."""
    ok = True
    for d, n_add, n_rem in (("terms", 2, 1), ("withdrawal", 5, 6)):
        now = _norm(EU_NOW["pack"]["docs"][l][d]["text"]).split("\n\n")      # 1125v: between the pins of the pixel and of the refund conditions (_pack_1125v checks the pack of now)
        was = _norm(EU_PIXEL["pack"]["docs"][l][d]["text"]).split("\n\n")
        add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
        ok = ok and len(now) - len(was) == n_add - n_rem and (len(add), len(rem)) == (n_add, n_rem)
    return ok and pay.CONSENT_TEXT[l] not in EU_NOW["pack"]["docs"][l]["withdrawal"]["text"] and pay.CONSENT_TEXT[l] in EU_PIXEL["pack"]["docs"][l]["withdrawal"]["text"]


def _pack_1125v(l):
    """1125v (the owner's decision of 2026-11-25 (value vouchers)): the pack's EU terms = the pin of the refund conditions with exactly THREE paragraphs replaced (the
    voucher section's intro, its table of the amounts and its rules), none added and none dropped; the withdrawal page word for word; the pinned pack of this work
    holds the same texts."""
    now = _norm(PACK["docs"][l]["terms"]["text"]).split("\n\n")
    was = _norm(EU_NOW["pack"]["docs"][l]["terms"]["text"]).split("\n\n")
    add, rem = [p for p in now if p not in was], [p for p in was if p not in now]
    return (len(now) == len(was) and len(add) == 3 == len(rem) and any(all(_digits(pay.price_text(a, l, "eur")) in _digits(p) for a in _AMOUNTS) for p in add)
            and _norm(PACK["docs"][l]["withdrawal"]["text"]) == _norm(EU_NOW["pack"]["docs"][l]["withdrawal"]["text"])
            and all(_norm(PACK["docs"][l][d]["text"]) == _norm(EU_VALUE["pack"]["docs"][l][d]["text"]) for d in ("terms", "withdrawal")))


seller_en_de = {k: ({l: v[l] for l in LANG2} if isinstance(v, dict) else v) for k, v in PACK["seller"].items()}
pack_docs_eq = lambda a, b, l, d: (_norm(a[l][d]["text"]) == _norm(b[l][d]["text"]) and a[l][d]["url"] == b[l][d]["url"]
                                    and a[l][d]["title"] == b[l][d]["title"])
eu_pack_same = (
    all(_terms_pack_ok(l) for l in LANG2) and all(_terms_pack_12(l) for l in LANG2) and all(_terms_pack_18(l) for l in LANG2) and all(_terms_pack_28(l) for l in LANG2)
    and all(_terms_pack_28c(l) for l in LANG2) and all(_pack_1111g(l) for l in LANG2) and all(_pack_1113(l) for l in LANG2) and all(_pack_1121(l) for l in LANG2) and all(_pack_1124(l) for l in LANG8) and all(_pack_1125c(l) for l in LANG8) and all(_pack_1125v(l) for l in LANG8)
    and all(pack_docs_eq(EU_HR["pack"]["docs"], EU_BEFORE["pack"]["docs"], l, "withdrawal") for l in LANG2)
    and all(PACK["docs"][l]["terms"]["url"] == EU_BEFORE["pack"]["docs"][l]["terms"]["url"] for l in LANG2)
    and all(pack_docs_eq(PACK["docs"], EU_VALUE["pack"]["docs"], l, d) for l in LANG2 for d in ("terms", "withdrawal"))
    and sorted(PACK["docs"]) == ["de", "en", "et", "fi", "hr", "hu", "lt", "lv"])
seller_same = (seller_en_de == EU_BEFORE["pack"]["seller"] and PACK["seller"] == EU_NOW["pack"]["seller"]
               and all(sorted(PACK["seller"][k]) == ["de", "en", "et", "fi", "hr", "hu", "lt", "lv"] for k in ("company", "address", "contact"))
               and all(PACK["seller"][k][l] == EU_GIFT["pack"]["seller"][k][l] for k in ("company", "address", "contact") for l in LANG5)
               and all(PACK["seller"][k][l] == EU_COUNTER["pack"]["seller"][k][l] for k in ("company", "address", "contact") for l in ("en", "de", "lt", "hu")))
check("B3 the built pack's EU texts are the same as before (the date line aside), links without m="
      " - 0930: the terms by exactly the two sentences of 30efee7 and 1acef38, the seller with its lt and hu lines; "
      "all pinned to eu_1acef38.json - 1005: pinned to eu_wp12.json, the terms by exactly the three paragraphs of the changed blocks (_terms_pack_12)"
      " - 1006: pinned to eu_wp18.json, the terms by exactly one more paragraph, the AI-made material sentence (_terms_pack_18)"
      " - 1028: pinned to eu_hr.json, the terms by exactly the one paragraph of the contract languages (_terms_pack_28), the seller with its hr lines"
      " - 1028c: pinned to eu_prints.json, the terms by the print paragraphs and the two sentences replaced (_terms_pack_28c), the withdrawal page by its print paragraph"
      " - 1111g: pinned to eu_gift.json, the terms and the withdrawal page by exactly the paragraphs of the gift vouchers, nothing removed (_pack_1111g)"
      " - 1113: pinned to eu_langs3.json, the terms by exactly the one paragraph of the contract languages (_pack_1113), the seller with its fi, et and lv lines"
      " - 1121: pinned to eu_printlater.json, the terms by exactly four paragraphs replaced (the product sentence's and three of the section prints) and the withdrawal"
      " page by exactly one (_pack_1121); the 1113 step is checked between the pins of the vouchers and of the three languages"
      " - 1124: pinned to eu_block.json, the terms by exactly ONE paragraph replaced in each of the eight languages, the list of prints and prices (the eleven prints"
      " of the offer), the shipping table and the delivery paragraph's times, the withdrawal page word for word (_pack_1124); the 1121 step is checked between the"
      " two pins before it - 1125c: pinned to eu_terms.json; the 1124 step is checked on the pin of the pixel; the owner's second decision of 2026-11-25: the terms"
      " by exactly one paragraph replaced by two, the withdrawal page by five paragraphs for six, the checkbox text gone (_pack_1125c)"
      " - 1125v: pinned to eu_value.json; the 1125c step is checked between the pins of the pixel and of the refund conditions; the value vouchers: the terms by"
      " exactly three paragraphs of the voucher section replaced (the intro, the five amounts, the rules), the withdrawal page word for word (_pack_1125v)",
      eu_pack_same and "m=" not in json.dumps(PACK["docs"]) and seller_same and PACK["updated"] == EU_NOW["pack"]["updated"],
      (eu_pack_same, seller_same, [_terms_pack_ok(l) for l in LANG2], [_terms_pack_12(l) for l in LANG2], [_terms_pack_18(l) for l in LANG2], [_terms_pack_28(l) for l in LANG2]))
check("B4 landing copy: eu and lt read the language's own copy object (unchanged)",
      CL["copySame"] == {"euEn": True, "euDe": True, "ltEn": True}, CL["copySame"])

# ---------------------------------------------------------------------------------------------- C. the Australian edition
T = EDI["au"]["terms"]
# 1028c: the Australian edition is made from the EU texts BEFORE the prints (src/legal/editions.ts applies src/legal/docs/prints.ts to the EU edition only): its base
# is the pin of hr, the EU edition as it was before the prints, which the EU edition of now differs from by exactly PRINTS28C and PRIV28C (B1, B2b)
EU_BASE = {d: EU_HR[d] for d in DOCS4}
EU_BASE["privacy"] = EU_KEEP_RAW["privacy"]   # 1126: the raw policy with the kept free previews (B1 holds it to eu_value_raw.json plus exactly those). 1125: the raw policy with the Meta pixel's passages (B1 holds it to eu_cap_raw.json plus exactly those). 1111: the raw policy with the paragraph of the daily ceiling of free previews (B2b holds it to the pin of hr plus exactly that)
ids_eu = [s["id"] for s in EU_BASE["terms"]["en"]["sections"]]
ids_au = [s["id"] for s in T["en"]["sections"]]
check("C1 AU terms: the EU sections in order, with 'australia' right after 'defects' (en, de) - 1028c: the EU sections before the prints (the pin of hr)",
      ids_au == ids_eu[:ids_eu.index("defects") + 1] + ["australia"] + ids_eu[ids_eu.index("defects") + 1:]
      and [s["id"] for s in T["de"]["sections"]] == ids_au, ids_au)
changed = {"preview", "prices", "withdrawal", "defects", "liability", "disputes", "australia",
           "contract"}   # 0930: "contract" since 30efee7, held to one sentence by contract_au below
shared_same = all(s == e for lang in ("en", "de") for s in T[lang]["sections"] if s["id"] not in changed
                  for e in EU_BASE["terms"][lang]["sections"] if e["id"] == s["id"])
pv = {lang: [next(s for s in e[lang]["sections"] if s["id"] == "preview") for e in (T, EU_BASE["terms"])] for lang in ("en", "de")}
# 0930 (30efee7): the EU terms name four contract languages, the Australian pages exist in English and German only, so the AU
# "contract" section is the EU one with exactly that one sentence as it was (edition_langs "au")
eu_contract = {l: json.dumps(next(s for s in EU_BASE["terms"][l]["sections"] if s["id"] == "contract"), ensure_ascii=False) for l in LANG2}
au_contract = {l: json.dumps(next(s for s in T[l]["sections"] if s["id"] == "contract"), ensure_ascii=False) for l in LANG2}
# 1028: the EU sentence names Croatian too (TERMS28); the AU one still names English and German only
contract_au = all(eu_contract[l].count(TERMS28[l]["contract"][2][0]) == 1
                  and eu_contract[l].replace(TERMS28[l]["contract"][2][0], CONTRACT_LANGS[l][0]) == au_contract[l] for l in LANG2)
check("C2 AU terms: every other section is the EU one word for word; 'preview' only names the AU complaints title"
      " - 0930: and 'contract' only names English and German as the contract languages (30efee7) - 1028: the EU sentence it replaces names Croatian too"
      " - 1028c: the EU sections before the prints (the pin of hr)",
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
check("C9 AU withdrawal page: EU statutory text kept, lead framed as EU law, the AU checkbox in its box, ACL links"
      " - 1125c: no checkbox (the owner's second decision of 2026-11-25): 'expiry' says that by paying the customer agrees, and holds no box",
      "under EU consumer law" in WAU["en"]["lead"] and "doc:terms#australia" in WAU["en"]["lead"]
      and "By paying, you agree that we start at once" in json.dumps(exp_en) and "Mit Ihrer Zahlung stimmen Sie zu" in json.dumps(exp_de, ensure_ascii=False)
      and not boxes and not any(isinstance(b, dict) and "box" in b for b in exp_de["blocks"]) and au_en not in json.dumps(WAU, ensure_ascii=False)
      and "doc:terms#australia" in json.dumps(exp_en) and "doc:terms#australia" in json.dumps(exp_de, ensure_ascii=False)
      and [s for s in WAU["en"]["sections"] if s["id"] == "right"] == [s for s in EU_BASE["withdrawal"]["en"]["sections"] if s["id"] == "right"],
      WAU["en"]["lead"])
PAU = EDI["au"]["privacy"]
pids = [s["id"] for s in PAU["en"]["sections"]]
psec = {lang: next(s for s in PAU[lang]["sections"] if s["id"] == "australia") for lang in ("en", "de")}
ptext = " ".join(psec["en"]["blocks"])
check("C10 AU privacy: 'australia' right after 'rights' (biometric info never used to identify, outside Australia, APPs and "
      "the small business exemption, the tort of 10 June 2025, OAIC); all else = the EU policy - 1028c: the EU policy before the prints (the pin of hr)"
      " - 1126: the raw policy with the kept free previews (eu_keep_raw.json); its section says the 30 days too",
      "30 days" in ptext and
      pids[pids.index("rights") + 1] == "australia" and [p for p in pids if p != "australia"] == [s["id"] for s in EU_BASE["privacy"]["en"]["sections"]]
      and all(x in ptext for x in ("biometric information", "sensitive information", "never identify or verify anyone",
                                   "outside Australia", "Australian Privacy Principles", "A$3 million", "10 June 2025",
                                   "oaic.gov.au", "#iris", "#services"))
      and "oaic.gov.au" in " ".join(psec["de"]["blocks"])
      and all(s == e for s in PAU["en"]["sections"] if s["id"] != "australia" for e in EU_BASE["privacy"]["en"]["sections"] if e["id"] == s["id"]),
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
un_au = [it for it in CL["copy"]["auEn"]["faq"]["items"] if it["id"] == "unhappy"]
un_eu = [it for it in CL["copy"]["eu"]["faq"]["items"] if it["id"] == "unhappy"]
check("C16 landing FAQ for au: cancelling framed as EU law, the ACCC words, no 'we render it again' promise; eu as before"
      " - 1125c: the owner's second decision of 2026-11-25: no FAQ item about withdrawing or cancelling (au, eu); the AU answer about a result you do not like keeps"
      " the ACCC words and makes no promise, the EU one says we make a faulty file again and names no refund",
      not faq_au and not faq_de and not faq_eu and len(un_au) == 1 and len(un_eu) == 1
      and "guarantees that cannot be excluded under the Australian Consumer Law" in un_au[0]["a"] and "render it again" not in un_au[0]["a"]
      and un_eu[0]["a"].endswith("write to us: we render it again.") and "refund" not in json.dumps(CL["copy"]["eu"]["faq"]).lower()
      and "cancel" not in un_au[0]["a"].lower()
      and len(CL["copy"]["auEn"]["faq"]["items"]) == len(CL["copy"]["eu"]["faq"]["items"])
      and not bad_words(json.dumps(CL["copy"]["auEn"])) and not AMERICAN.findall(json.dumps(CL["copy"]["auEn"])),
      faq_au)
check("C17 order page: an ACL line for Australian orders (en, de)", CL["orderAcl"] and "Australian Consumer Law" in CL["orderAcl"]["en"]
      and "Australian Consumer Law" in CL["orderAcl"]["de"] and not bad_words(CL["orderAcl"]["en"]), CL["orderAcl"])

# ---------------------------------------------------------------------------------------------- D. checkout
c, j = get("/api/checkout")
check("D1 GET /api/checkout: consent en/de the EU text as before; consent.markets.au the AU text (en, de)"
      " - 1028b: consent.markets.us the US text (en) beside it",
      c == 200 and j["consent"]["version"] == pay.CONSENT_VERSION and j["consent"]["en"] == PAY0.CONSENT_TEXT["en"]
      and j["consent"]["de"] == PAY0.CONSENT_TEXT["de"] and j["consent"]["markets"] == {"au": pay.CONSENT_TEXT_AU, "us": pay.CONSENT_TEXT_US}, j.get("consent"))
oA, kA = new_order(2)
c, j = checkout(oA, kA, 2, "studio_black", "en", market="au")
p = H.Fake.creates[-1][0]
rec = read_json(f"orders/{oA}/order.json")
check("D2 au checkout: Stripe locale en-GB, aud, the AU submit note; order.json keeps the AU text, its version and fingerprint"
      " - 0930: the version recorded is the current one, 2026-09-30.2 (30efee7), the AU text is unchanged - 1028: the current one is 2026-10-28.1 (the Croatian text), the AU text unchanged"
      " - 1028b: the current one is 2026-10-28.2 (the US text), the AU text unchanged"
      " - 1125c: no checkbox on the AU market (the owner's second decision of 2026-11-25): Stripe shows no note; order.json and the metadata record that the order"
      " was placed under the terms of LEGAL_NOW (kind by_terms, no box)",
      c == 200 and p["locale"] == "en-GB" and p["line_items[0][price_data][currency]"] == "aud"
      and "custom_text[submit][message]" not in p and pay.SUBMIT_NOTE_AU == {"en": "", "de": ""}
      and rec["checkout"]["consent"] == {"kind": "by_terms", "version": LEGAL_NOW, "at": rec["checkout"]["created"], "lang": "en", "box": False}
      and p["metadata[consent_version]"] == LEGAL_NOW and p["metadata[consent_kind]"] == "by_terms", (p.get("locale"), p.get("custom_text[submit][message]"), rec["checkout"]["consent"]))
c, j = checkout(oA, kA, 2, "studio_black", "de", market="au")
p = H.Fake.creates[-1][0]
rec = read_json(f"orders/{oA}/order.json")
check("D3 au in German: Stripe de, the German AU note and checkbox text - 1125c: no note, placed under the terms", c == 200 and p["locale"] == "de"
      and "custom_text[submit][message]" not in p and rec["checkout"]["consent"]["kind"] == "by_terms" and rec["checkout"]["consent"]["lang"] == "de",
      p.get("custom_text[submit][message]"))
for lang in ("en", "de"):
    c, j = checkout(oA, kA, 2, "studio_black", lang)
    p = H.Fake.creates[-1][0]
    rec = read_json(f"orders/{oA}/order.json")
    # 1125b (the owner's decision of 2026-11-25, less text on Stripe's page): the note above the pay button is the one of before WITHOUT its first two
    # sentences (the digital file, "no print and no frame"); the rest of it, word for word
    # 1125c (the owner's second decision of 2026-11-25): no note above the pay button in English and German, the order placed under the terms
    check(f"D4 eu checkout ({lang}): the EU submit note and checkbox text exactly as before - 1125b: the note without its first two sentences"
          f" - 1125c: no note at all, the order placed under the terms of LEGAL_NOW", c == 200
          and "custom_text[submit][message]" not in p and pay.SUBMIT_NOTE[lang] == "" and p["locale"] == lang
          and rec["checkout"]["consent"]["kind"] == "by_terms" and rec["checkout"]["consent"]["version"] == LEGAL_NOW, p.get("custom_text[submit][message]"))
c, j = checkout(oA, kA, 2, "studio_black", "en", market="lt")
rec = read_json(f"orders/{oA}/order.json")
check("D5 lt checkout: the EU wording (lt reads the EU edition) - 1125c: no note, placed under the terms", c == 200 and rec["checkout"]["consent"]["kind"] == "by_terms"
      and "custom_text[submit][message]" not in H.Fake.creates[-1][0])
check("D6 no Stripe text for au reads as 'no refunds'", not bad_words(json.dumps(pay.SUBMIT_NOTE_AU) + json.dumps(pay.CONSENT_TEXT_AU)))

# ---------------------------------------------------------------------------------------------- E. the AU confirmation
oE, kE, pE, mE = paid_order("au", "en", "sydney@example.com", eyes=2)
t = mE[0]["text"] if mE else ""
head = t.split("_" * 64)[0]
check("E1 AU paid: paid.json market au, the AU consent text recorded; one confirmation, subject with 'invoice'"
      " - 0930: recorded under the current version 2026-09-30.2 (30efee7), the AU text unchanged - 1028: the current version is 2026-10-28.1 - 1028b: 2026-10-28.2"
      " - 1125c: placed under the terms of LEGAL_NOW, no box (the owner's second decision of 2026-11-25)",
      pE["market"] == "au" and pE["consent"]["kind"] == "by_terms" and pE["consent"]["version"] == LEGAL_NOW and pE["consent"]["box"] is False
      and len(mE) == 1 and mE[0]["subject"] == f"Your SnapEyes order {oE}: order confirmation and invoice", (pE.get("consent"), [m["subject"] for m in mE]))
inv = f"Invoice\nInvoice number: {oE}\nInvoice date: "
check("E2 the invoice: number, date, supplier with company code and address, customer, what was supplied, total A$79, "
      "'No GST has been charged', paid in full", inv in head and "Supplier: MB \"Portretizuokis\", company code 305605052, " in head
      and "Customer: sydney@example.com" in head and "Supplied: 1 x SnapEyes iris artwork, 2 eyes, Studio Black" in head
      and f"Total: A${pay.price_list('au')['two_eyes'] // 100}\n" in head and "GST: No GST has been charged. The supplier is not registered for GST in Australia." in head
      and "Payment: paid in full through Stripe on " in head, head[:2500])
check("E3 never 'Tax invoice' (anywhere in the email, legal texts included), no euro, no VAT sentence before the legal texts",
      not re.search(r"tax invoice", t, re.I) and "€" not in head and "VAT" not in head and "Price: A$79. This is the total price: no GST is charged." in head)
i_rights = head.find("Your rights in Australia\n" + ACCC)
check("E4 'Your rights in Australia' opens with the ACCC sentence and links terms#australia (m=au), before 'Cancelling before we start'"
      " - 1125c: the owner's second decision of 2026-11-25: nothing about withdrawing or cancelling in the email's body (no section, no withdrawal link); the rights"
      " in Australia stay",
      0 < i_rights and "https://snapeyes.com/terms?lang=en&m=au#australia" in head
      and "Cancelling before we start" not in head and "withdraw" not in head.lower() and "refund" not in head.lower() and "Your right of withdrawal\n" not in head
      and pay.withdraw_url(oE, kE, "en") not in head, head[:3000])
check("E5 the consent quoted is the AU text; the confirmation keeps the ACL - 1125c: nothing quoted, nothing said about what was agreed; the intro names the order, the"
      " invoice, the rights in Australia and the terms; the ACL kept",
      au_en not in head and "consent" not in head.lower() and "agree" not in head.lower() and pay.INTRO_TERMS_AU["en"] in head
      and "Our services come with guarantees that cannot be excluded under the Australian Consumer Law." in head, head[:3000])
check("E6 the full AU withdrawal information and AU terms are attached (not the EU ones); the terms link carries m=au",
      ED["en"]["withdrawal"]["text"] in t and ED["en"]["terms"]["text"] in t and PACK["docs"]["en"]["terms"]["text"] not in t
      and "https://snapeyes.com/terms?lang=en&m=au\n" in head)
check("E7 the AU email: no 'no refunds' wording, no en or em dash", not bad_words(t) and not any(d in t for d in DASHES), bad_words(t))
md = read_json(f"orders/{oE}/mail_delivery.json")
check("E8 mail_delivery.json sent with the new consent version and the pack date"
      " - 0930: the new version is 2026-09-30.2 (30efee7) - 1005: the pack date is 2026-10-05 (WP12) - 1006: the pack date is 2026-10-06 (WP18) - 1020: the pack date is 2026-10-20 (the counter's privacy paragraphs) - 1028: the version 2026-10-28.1 and the pack date 2026-10-28 (the Croatian texts) - 1028b: the version 2026-10-28.2 (the US text), the same pack date"
      " - 1121: the version and the date of now (LEGAL_NOW: 2026-11-21 since the print paragraphs; 2026-11-13.1 since the three languages)"
      " - 1124: the date of now is 2026-11-24 (the terms' list of prints and prices), the version as it was"
      " - 1125c: the order was placed under the terms of LEGAL_NOW, which is the version it names", md.get("state") == "sent"
      and md.get("consent") == LEGAL_NOW and md.get("legal") == LEGAL_NOW, md)
with open(os.path.join(HERE, "sample_au_confirmation_en.txt"), "w", encoding="utf-8") as f:
    f.write(head)

oG, kG, pG, mG = paid_order("au", "de", "perth@example.com", eyes=1, style="deep_nebula")
t = mG[0]["text"] if mG else ""
head = t.split("_" * 64)[0]
check("E9 German AU confirmation: Rechnung, 'Es wurde keine GST berechnet', Gesamtbetrag A$49, the ACCC sentence, "
      "the German AU consent and texts - 1125c: nothing quoted, nothing about withdrawing in the body (the owner's second decision of 2026-11-25)",
      len(mG) == 1 and mG[0]["subject"].endswith("Bestellbestätigung und Rechnung")
      and f"Rechnung\nRechnungsnummer: {oG}" in head and "GST: Es wurde keine GST berechnet." in head
      and f"Gesamtbetrag: A${pay.price_list('au')['one_eye_art'] // 100}\n" in head and ACCC in head
      and pay.CONSENT_TEXT_AU["de"] not in head and ED["de"]["terms"]["text"] in t and ED["de"]["withdrawal"]["text"] in t
      and "widerruf" not in head.lower() and "zustimm" not in head.lower() and not re.search(r"steuerrechnung|tax invoice", t, re.I)
      and not any(d in t for d in DASHES), head[:2500])
with open(os.path.join(HERE, "sample_au_confirmation_de.txt"), "w", encoding="utf-8") as f:
    f.write(head)

# ---------------------------------------------------------------------------------------------- F. EU emails exactly as before
oU, kU, pU, mU = paid_order(None, "en", "dublin@example.com", eyes=2, style="supernova")
oD, kD, pD, mD = paid_order("lt", "de", "vilnius@example.com")
pay.start_clock()
PAY0.start_clock()
# 1125c (the owner's second decision of 2026-11-25): an order placed now is placed under the terms; one placed before holds a ticked consent and gets its email as
# before. The consent of such an order, as paid.json kept it: the version, the time, the language and the text of its market
def old_consent(paid):
    lang = pay.lang_of((paid.get("spec") or {}).get("lang"))
    return {"version": CONSENT_NOW, "at": pay.iso(paid.get("paid_at")), "lang": lang, "text": pay.consent_for(pay.paid_market(paid), lang)}


def old_paid(paid):
    return dict(paid, consent=old_consent(paid))


def body_of(mail_text):
    return mail_text.split("_" * 64)[0]


diffs, terms_bad = [], []
for o, k, paid in ((oU, kU, pU), (oD, kD, pD)):
    for pk in (PACK, PACK_AUTO):
        a = pay.confirmation_mail(o, old_paid(paid), k, pk, old_consent(paid))
        b = PAY0.confirmation_mail(o, old_paid(paid), k, pk, old_consent(paid))
        if a != b:
            diffs.append((o, pk is PACK_AUTO))
        c_ = pay.paid_consent(o, read_json(f"orders/{o}/order.json"), paid)
        n = body_of(pay.confirmation_mail(o, paid, k, pk, c_)[1])
        lang = pay.lang_of(paid["spec"]["lang"])
        if not (c_["kind"] == "by_terms" and pay.INTRO_TERMS[lang] in n and pay.withdraw_url(o, k, lang) not in n
                and not any(w in n.lower() for w in ("withdraw", "widerruf", "refund", "erstatt", "consent", "zustimm", "agree"))):
            terms_bad.append((o, pk is PACK_AUTO))
check("F1 EU and lt confirmation emails (en, de; order page start and server start) are byte for byte the core's own"
      " - 1125c: for an order that holds a ticked consent (placed before the owner's second decision of 2026-11-25); an order placed under the terms gets an email"
      " whose body says nothing about withdrawing, refunds or what was agreed, with the intro pay.INTRO_TERMS and no withdrawal link",
      not diffs and not terms_bad and len(mU) == 1 and len(mD) == 1 and "Invoice" not in mU[0]["text"] and "Australia" not in mU[0]["text"]
      and mU[0]["subject"] == f"Your SnapEyes order {oU}: order confirmation", (diffs, terms_bad))
a = pay.confirmation_mail(oE, pE, kE, PACK_AUTO, pay.paid_consent(oE, read_json(f"orders/{oE}/order.json"), pE))
a_old = pay.confirmation_mail(oE, old_paid(pE), kE, PACK_AUTO, old_consent(pE))
check("F2 the AU email with the server start: same invoice and rights, the 'right after this email' wording"
      " - 1125c: placed under the terms: the invoice and the rights, nothing about withdrawing; an AU order that holds a ticked consent: the wording of before",
      "withdraw" not in body_of(a[1]).lower() and "Invoice number: " + oE in a[1] and ACCC in a[1]
      and "so that right usually ends within a few moments" in a_old[1] and "“" + au_en + "”" in a_old[1] and ACCC in a_old[1])
try:
    PAY0.confirmation_mail(oE, old_paid(pE), kE, PACK, old_consent(pE))
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
# 1125c: an order placed now is placed under the terms (the owner's second decision of 2026-11-25); an order that holds a ticked consent is read as before
bare = dict(old_paid(pE), consent={k: v for k, v in old_consent(pE).items() if k != "text"})
recE = read_json(f"orders/{oE}/order.json")
recE_nocons = dict(recE, checkout=dict(recE["checkout"], consent={}))
check("H2 paid_consent without a stored text: the AU text of its version for an AU order, the EU text for an EU one"
      " - 1125c: for orders that hold a ticked consent; one placed under the terms is read as such (kind by_terms, nothing to quote)",
      pay.paid_consent(oE, recE_nocons, bare)["text"] == au_en
      and pay.paid_consent(oU, {}, dict(old_paid(pU), consent={k: v for k, v in old_consent(pU).items() if k != "text"}))["text"] == PAY0.CONSENT_TEXT["en"]
      and pay.paid_consent(oE, recE, pE)["kind"] == "by_terms" and pay.paid_consent(oE, recE, pE)["text"] == "")
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
check("I4 making began on an AU order: lapsed, the receipt keeps 'statutory rights' and adds the ACL line, never 'no refunds'"
      " - 1125c: the order was placed under the terms (the owner's second decision of 2026-11-25): lapsed with the reason of before, the receipt names the terms"
      " and no ticked consent, the answer says terms",
      c == 200 and (j.get("withdrawal") or {}).get("state") == "lapsed" and (j.get("withdrawal") or {}).get("reason") == "making_began"
      and (j.get("withdrawal") or {}).get("terms") is True and len(rM) == 1 and "Under our terms of sale, which apply to your order, by paying you agreed" in rM[0]["text"]
      and "expressly agreed" not in rM[0]["text"]
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
check("K0 the /try buy card renders (react-dom/server through Vite) for au en/de, eu en, lt de - 1028b: and us en", BC is not None
      and sorted(BC) == ["au_de", "au_en", "eu_en", "lt_de", "us_en"], (r.returncode, r.stderr[-900:]))
if BC:
    card = {k: (re.sub(r"<[^>]+>", " ", v["html"]), re.sub(r"<[^>]+>", " ", v["noServer"]), v["html"]) for k, v in BC.items()}
    A39 = "A$" + str(pay.price_list("au")["one_eye_studio_black"] // 100)
    # 1125c (the owner's decisions of 2026-11-25): no consent box but on the US market, so neither the server's text nor the site's own one is shown for au, eu and lt
    check("K1 au: the server's AU checkbox text (en, de), the line links terms#australia (m=au), A$ price - 1125c: no checkbox at all",
          'data-testid="waiver"' not in card["au_en"][2] + card["au_de"][2] and "SERVER AU" not in card["au_en"][0] + card["au_de"][0]
          and "SERVER EU" not in card["au_en"][0] + card["au_de"][0]
          and "/terms?lang=en&amp;m=au#australia" in card["au_en"][2] and "/terms?lang=de&amp;m=au#australia" in card["au_de"][2]
          and A39 in card["au_en"][0] and "€" not in card["au_en"][0], card["au_en"][0][:600])
    check("K2 au without a server text: the site's own AU checkbox (the same words the server records) - 1125c: no checkbox, no checkbox text",
          pay.CONSENT_TEXT_AU["en"].replace("'", "&#x27;") not in card["au_en"][1] and pay.CONSENT_TEXT_AU["en"] not in card["au_en"][1], card["au_en"][1][:800])
    check("K3 eu and lt: the EU checkbox text and line as before (no Australia), euro prices - 1125c: no checkbox, no checkbox text",
          'data-testid="waiver"' not in card["eu_en"][2] + card["lt_de"][2] and "SERVER EU" not in card["eu_en"][0] + card["lt_de"][0]
          and "australia" not in card["eu_en"][2] and "australia" not in card["lt_de"][2] and "€" in card["eu_en"][0]
          and PAY0.CONSENT_TEXT["de"] not in card["lt_de"][1], card["eu_en"][0][:400])

# ---------------------------------------------------------------------------------------------- U. the US market (1028b)
us_en = pay.CONSENT_TEXT_US["en"]
DRAFT_US = ("I expressly agree that SnapEyes starts making my personalised digital artwork right away, before the withdrawal period ends. I know that once this "
            "has started, I lose my right of withdrawal and can't cancel for a change of mind; my rights if the file is faulty are not affected. I also agree "
            "that SnapEyes uses the photos of my eyes only to make my preview and my artwork, never to identify anyone, and deletes them as its privacy policy "
            "describes.")
check("U1 US checkbox: the owner's words, server CONSENT_TEXT_US = client CHECKOUT_LEGAL_US (English only)",
      us_en == DRAFT_US == CL["checkoutUs"]["en"]["withdrawalConsent"] and sorted(pay.CONSENT_TEXT_US) == ["en"] and sorted(CL["checkoutUs"]) == ["en"],
      (us_en, CL["checkoutUs"]))
check("U2 the US checkbox keeps both EU elements, no change-of-mind cancelling, the rights for a faulty file and the consent to the use of the eye photos; "
      "no 'no refunds', no dash", "expressly agree" in us_en and "before the withdrawal period ends" in us_en and "I lose my right of withdrawal" in us_en
      and "can't cancel for a change of mind" in us_en and "my rights if the file is faulty are not affected" in us_en
      and "uses the photos of my eyes only to make my preview and my artwork, never to identify anyone" in us_en
      and not bad_words(us_en + json.dumps(pay.SUBMIT_NOTE_US)) and not any(d in us_en for d in DASHES), us_en)
check("U3 consent versions: the US text only under 2026-10-28.2; 2026-10-28.1 still quotes the EU and AU texts; a US order is English whatever it asked"
      " - 1028c: and under 2026-10-28.3 (the print box, which a US order never shows), the same text"
      " - 1113: and under 2026-11-13.1 (the three languages, none of them in the US edition), the same text; the versions before it quote the five texts they had",
      pay.CONSENT_TEXTS_US == {CONSENT_1028B: pay.CONSENT_TEXT_US, CONSENT_1028C: pay.CONSENT_TEXT_US, CONSENT_NOW: pay.CONSENT_TEXT_US}
      and pay.CONSENT_TEXTS[CONSENT_1028] == pay.CONSENT_TEXTS[CONSENT_1028C] == {l: pay.CONSENT_TEXT[l] for l in LANG5} and pay.CONSENT_TEXTS[CONSENT_NOW] == pay.CONSENT_TEXT
      and pay.CONSENT_TEXTS_AU[CONSENT_1028] == pay.CONSENT_TEXT_AU and pay.consent_text(CONSENT_NOW, "en", "us") == us_en
      and pay.consent_text(CONSENT_1028, "en", "us") is None and pay.consent_text(CONSENT_NOW, "de", "us") is None
      and pay.consent_for("us", "de") == us_en and pay.lang_for("us", "hu") == "en" and pay.submit_note("us", "de") == pay.SUBMIT_NOTE_US["en"]
      and pay.US_MARKETS == ("us",) and pay.us_market("us") and not pay.us_market("au") and not pay.acl_market("us") and pay.edition_market("us")
      and not pay.edition_market("hr") and not pay.edition_market("uk") and tuple(pay.edition_langs("us")) == ("en",),
      (pay.CONSENT_TEXTS_US, pay.US_MARKETS))
check("U4 checkoutLegal: us gets the US checkbox in English (a German page too) and a link to terms#united-states; hr the EU wording; the links carry m=us, m=hr"
      " - 1126: hr's wording is the pin of the kept free previews",
      cf["en_us"]["withdrawalConsent"] == us_en == cf["de_us"]["withdrawalConsent"] and cf["de_us"]["continueButton"] == "Continue to payment"
      and any(p.get("section") == "united-states" and p.get("doc") == "terms" for p in cf["en_us"]["acceptance"])
      and cf["en_hr"] == EU_KEEP["checkout"]["en"] and CL["usHrefs"] == {"usSection": "/terms?lang=en&m=us#united-states", "hrPlain": "/terms?lang=hr&m=hr"},
      (cf["en_us"]["acceptance"], CL["usHrefs"]))
EUS = PACK["editions"]["us"]
links_us = re.findall(r"https://snapeyes\.com/(?:terms|privacy|withdrawal|imprint)\?[^\s)]*", json.dumps(EUS))
check("U5 pack editions.us: English only, terms and withdrawal, every legal link carries m=us; its terms print the US prices, the US rights and one contract language",
      sorted(EUS) == ["en"] and sorted(EUS["en"]) == ["terms", "withdrawal"] and links_us and all("m=us" in x for x in links_us)
      and EUS["en"]["terms"]["text"] == CL["plainUsTerms"] and EUS["en"]["terms"]["url"] == "https://snapeyes.com/terms?lang=en&m=us"
      and "Your rights in the United States\n" in EUS["en"]["terms"]["text"] and "One eye, Clean Iris: $21.97" in EUS["en"]["terms"]["text"]
      and "Each further eye: +$16.00" in EUS["en"]["terms"]["text"] and "The contract language is English." in EUS["en"]["terms"]["text"]
      and "€" not in EUS["en"]["terms"]["text"] and "A$" not in EUS["en"]["terms"]["text"] and us_en in EUS["en"]["withdrawal"]["text"]
      and CL["usMoney"] == ["$21.97", "$16.00"] and CL["copyUs"] and not any(d in json.dumps(EUS) for d in DASHES),
      [x for x in links_us if "m=us" not in x][:5])
c, j = get("/api/checkout")
check("U6 GET /api/checkout: markets us (USD, its own list) and hr (EUR, the euro list), never uk; the country hint offers us to the US, nothing to Croatia or the UK",
      c == 200 and j["markets"]["us"] == {"currency": "USD", "prices": pay.price_list("us")} and j["markets"]["hr"] == {"currency": "EUR", "prices": pay.price_list("eu")}
      and "uk" not in j["markets"] and get("/api/checkout", {"x-vercel-ip-country": "US"})[1]["suggest"] == "us"
      and get("/api/checkout", {"x-vercel-ip-country": "HR"})[1]["suggest"] is None and get("/api/checkout", {"x-vercel-ip-country": "GB"})[1]["suggest"] is None,
      (j.get("markets"), j.get("suggest")))
oV, kV = new_order(2)
c, j = checkout(oV, kV, 2, "studio_black", "de", market="us")
p = H.Fake.creates[-1][0]
rec = read_json(f"orders/{oV}/order.json")
check("U7 us checkout (a German page): Stripe in English, usd, $44.97 for two eyes, the US submit note; order.json keeps the US text, its version and fingerprint",
      c == 200 and j.get("currency", "").lower() == "usd" and j.get("amount") == pay.price_list("us")["two_eyes"] and p["locale"] == "en"
      and p["line_items[0][price_data][currency]"] == "usd" and p["line_items[0][price_data][unit_amount]"] == str(pay.price_list("us")["two_eyes"])
      and p["custom_text[submit][message]"] == pay.SUBMIT_NOTE_US["en"] and p["metadata[market]"] == "us" and p["metadata[lang]"] == "en"
      and rec["checkout"]["consent"]["text"] == us_en and rec["checkout"]["consent"]["version"] == CONSENT_NOW and rec["checkout"]["consent"]["lang"] == "en"
      and p["metadata[consent_version]"] == CONSENT_NOW, (c, j, p.get("locale"), p.get("custom_text[submit][message]"), rec.get("checkout", {}).get("consent")))
oH, kH = new_order(1, "hr")
c, j = checkout(oH, kH, 1, "studio_black", "hr", market="hr")
pH = H.Fake.creates[-1][0]
recH = read_json(f"orders/{oH}/order.json")
cK, jK = checkout(oH, kH, 1, "studio_black", "en", market="uk")
check("U8 hr checkout: euros at the euro price, the Croatian EU checkbox and note, market hr in the metadata; uk is refused (priced, not selectable)"
      " - 1125c: no checkbox on the Croatian market either (the owner's second decision of 2026-11-25): placed under the terms; the note is the order button sentence",
      c == 200 and pH["line_items[0][price_data][currency]"] == "eur" and pH["line_items[0][price_data][unit_amount]"] == str(pay.price_list("eu")["one_eye_studio_black"])
      and pH["metadata[market]"] == "hr" and recH["checkout"]["consent"]["kind"] == "by_terms" and pH["custom_text[submit][message]"] == pay.SUBMIT_NOTE["hr"]
      and pay.SUBMIT_NOTE["hr"] == "Klikom na gumb za plaćanje dajete narudžbu s obvezom plaćanja."
      and cK == 400 and "uk" not in pay.SELECTABLE and pay.MARKETS["uk"]["selectable"] == 0, (c, j, cK, jK))
oS, kS, pS, mS = paid_order("us", "en", "boston@example.com", eyes=2)
tS = mS[0]["text"] if mS else ""
headS = tS.split("_" * 64)[0]
check("U9 US paid: paid.json market us in USD, the US consent text recorded; one confirmation, subject with 'invoice'",
      pS["market"] == "us" and pS["currency"] == "usd" and pS["consent"]["text"] == us_en and pS["consent"]["version"] == CONSENT_NOW
      and len(mS) == 1 and mS[0]["subject"] == f"Your SnapEyes order {oS}: order confirmation and invoice", (pS.get("consent"), [m["subject"] for m in mS]))
want_day = pay.date_text(pay.new_york_day(pS["paid_at"]), "en")
check("U10 the US invoice: number, the New York date, supplier with company code and address, customer, what was supplied, total $44.97, "
      "'No sales tax has been charged', paid in full; no GST, never 'Tax invoice'",
      f"Invoice\nInvoice number: {oS}\nInvoice date: {want_day}\n" in headS and "Supplier: MB \"Portretizuokis\", company code 305605052, " in headS
      and "Customer: boston@example.com" in headS and "Supplied: 1 x SnapEyes iris artwork, 2 eyes, Studio Black" in headS
      and "Total: $44.97\n" in headS and "Sales tax: No sales tax has been charged. The supplier is not registered to collect sales tax in any US state." in headS
      and f"Payment: paid in full through Stripe on {want_day}" in headS and "GST" not in headS and not re.search(r"tax invoice", tS, re.I)
      and "Price: $44.97. This is the total price: no sales tax is charged." in headS and "€" not in headS and "VAT" not in headS, headS[:2500])
i_rs, i_cs = headS.find("Your rights in the United States\n"), headS.find("Cancelling before we start\n")
check("U11 'Your rights in the United States' (a faulty file made again or refunded) links terms#united-states (m=us), before 'Cancelling before we start'; "
      "the US consent quoted with the use of the eye photos",
      0 < i_rs < i_cs and "https://snapeyes.com/terms?lang=en&m=us#united-states" in headS and "we make the file again free of charge, or refund you in full" in headS
      and "Your right of withdrawal\n" not in headS and "Your rights in Australia" not in headS and "“" + us_en + "”" in headS
      and "We use the photos of your eyes only to make your preview and your artwork, never to identify anyone" in headS and "get a full refund" in headS, headS[:3000])
check("U12 the full US withdrawal information and US terms are attached (not the EU or AU ones); no 'no refunds', no dash",
      EUS["en"]["withdrawal"]["text"] in tS and EUS["en"]["terms"]["text"] in tS and PACK["docs"]["en"]["terms"]["text"] not in tS
      and PACK["editions"]["au"]["en"]["terms"]["text"] not in tS and "https://snapeyes.com/terms?lang=en&m=us\n" in headS
      and not bad_words(tS) and not any(d in tS for d in DASHES), bad_words(tS))
with open(os.path.join(HERE, "sample_us_confirmation_en.txt"), "w", encoding="utf-8") as f:
    f.write(headS)
_t = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M"))
NY = {"2026-01-15T04:59": "2026-01-14", "2026-01-15T05:00": "2026-01-15",     # EST, UTC-5
      "2026-03-08T04:30": "2026-03-07",                                         # before summer time starts (Sun 8 Mar 2026, 2:00 EST = 7:00 UTC)
      "2026-03-09T04:30": "2026-03-09",                                         # EDT, UTC-4: 00:30
      "2026-07-01T03:59": "2026-06-30", "2026-07-01T04:00": "2026-07-01",     # EDT around midnight
      "2026-11-01T04:30": "2026-11-01",                                         # the last hours of summer time (Sun 1 Nov 2026, 2:00 EDT = 6:00 UTC)
      "2026-11-02T04:30": "2026-11-01"}                                         # EST again: 23:30 the day before
gotNY = {k: pay.new_york_day(_t(k)) for k in NY}
check("U13 new_york_day: EST/EDT with the second-Sunday-of-March and first-Sunday-of-November rules, around midnight and both switches; no time: today",
      gotNY == NY and re.fullmatch(r"\d{4}-\d{2}-\d{2}", pay.new_york_day(None) or "") and pay.new_york_day("junk") == pay.new_york_day(None), gotNY)
nous = json.loads(json.dumps(PACK))
del nous["editions"]["us"]
set_pack(nous)
whyU = pay.legal_problem()
set_pack(PACK)
check("U14 legal_problem: a pack without the us edition keeps live sales closed while us is selectable; pack_docs never gives a US order the EU texts",
      "us market" in whyU and pay.legal_problem() == "" and pay.pack_docs(nous, "en", "us") is None and pay.pack_docs(PACK, "en", "us") == EUS["en"]
      and pay.pack_docs(PACK, "de", "us") is None and pay.pack_docs(PACK, "en", "hr") == PACK["docs"]["en"], whyU)
oL, kL, pL, mL = paid_order("us", "en", "denver@example.com")
lapse(oL)
c, j, rL = withdraw_now(oL, kL, "denver@example.com")
check("U15 a lapsed statement on a US order: the receipt keeps the statutory sentence and adds the US line (never 'no refunds')",
      c == 200 and (j.get("withdrawal") or {}).get("state") == "lapsed" and (j.get("withdrawal") or {}).get("market") == "us" and len(rL) == 1
      and "Your rights if the file is faulty are not affected" in rL[0]["text"] and "Your rights in the United States" in rL[0]["text"]
      and "Australian" not in rL[0]["text"] and not bad_words(rL[0]["text"]), (c, j, rL[0]["text"][:1500] if rL else None))
if BC:
    check("U16 the /try buy card on the US market: the server's US checkbox text, the line links terms#united-states (m=us), the price in US$, no euro",
          "SERVER US EN" in card["us_en"][0] and "SERVER EU" not in card["us_en"][0] and "/terms?lang=en&amp;m=us#united-states" in card["us_en"][2]
          and "$" + f"{pay.price_list('us')['one_eye_studio_black'] // 100}.{pay.price_list('us')['one_eye_studio_black'] % 100:02d}" in card["us_en"][0]
          # 2026-11-25 (the owner's decision, less text): the card's file line is one short line; "no sales tax is charged" is in the US terms' prices
          and "€" not in card["us_en"][0] and "Digital file, 4096 px, without watermark." in card["us_en"][0]
          and (pay.CONSENT_TEXT_US["en"].replace("'", "&#x27;") in card["us_en"][1] or pay.CONSENT_TEXT_US["en"] in card["us_en"][1]), card["us_en"][0][:700])
check("U17 the order page has a line for US orders that keeps the rights for a faulty file and names no Australian law",
      CL["orderAcl"] and isinstance(CL["orderAcl"].get("us"), str) and "faulty" in CL["orderAcl"]["us"] and "Australian" not in CL["orderAcl"]["us"]
      and not bad_words(CL["orderAcl"]["us"]), CL["orderAcl"])

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
