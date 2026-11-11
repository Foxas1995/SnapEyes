# -*- coding: utf-8 -*-
"""Gift vouchers (owner's word 2026-11-11, "darom taip kaip siūlai"): someone buys a voucher now, the person they give it to photographs their own eye
later and enters the code at the checkout of /try.

What a voucher is
  - Two kinds: "one" (the price of a one-eye artwork in any style, the market's one_eye_art) and "two" (the price of a two-eye artwork, two_eyes).
    The value is taken from the market's standard price list when the voucher is bought (api/_lib/markets.py), never from the page.
  - Sold and redeemed in euros only, on the markets that read the EU edition of the legal texts (VOUCHER_MARKETS: eu, lt, hr). The legal texts of
    that edition say what a voucher is (src/legal/docs/vouchers.ts); the Australian, the US and the Hungarian (forint) editions sell none.
  - Valid for 12 months (VALID_DAYS), for one order. When the order costs less than the voucher, the rest is not paid out; when it costs more, the
    customer pays the difference on Stripe's page.
  - Withdrawal: an unused voucher can be withdrawn within 14 days of its purchase (the owner refunds it in the Stripe Dashboard and deletes its
    coupon there: a deleted coupon is "unknown" here at once). Nothing of that is automatic.

How it works at Stripe
  - Buying: a Checkout Session (mode payment, euros, one line item, the buyer's email collected by Stripe) whose metadata says kind "voucher",
    voucher_kind, voucher_value, market and lang. No order, no order key. It is made by POST /api/checkout {gift: {kind}, market, lang}.
  - Paid (the webhook's checkout.session.completed, or the success page asking GET /api/checkout?gift=<session id>): the code is derived from the
    session id with the server's secret (code_for: the same code every time, so a retried webhook and the success page agree without storing it),
    a Stripe coupon is made for it (amount_off the value, the currency, max_redemptions 1, redeem_by the last day; its id is coupon_id(code), a
    one-way hash of the code), the record vouchers/<coupon id>.json is written once (no email address in it: the buyer's address stays at Stripe),
    and the buyer gets the code by email once (with the terms and the withdrawal information of the EU edition as text, the contract on a durable
    medium). The owner gets a short note.
  - Redeeming: the order's checkout (api/checkout.py) checks the code (for_checkout: the coupon exists at Stripe, is still valid, is in the
    market's currency) and adds discounts[0][coupon] to the order's session; Stripe counts the one redemption when that session completes. A session
    the voucher pays entirely is a no-cost session (payment_status no_payment_required, no PaymentIntent): pay.session_paid accepts it, and
    pay.record_paid checks the amount against the price less the voucher.
  - The code the customer types is never sent to Stripe as a code: only its coupon id is. Codes are 12 characters of a 32-letter alphabet without
    0, O, 1 and I (60 bits): they cannot be guessed, and a malformed one is refused before anything is asked of Stripe."""
import calendar
import hashlib
import hmac
import re
import secrets
import time

from . import iris as L
from . import store
from . import pay
from . import counter

KINDS = {"one": 1, "two": 2}                 # the kind and the number of eyes its value pays for
KIND_PRICE = {"one": "one_eye_art", "two": "two_eyes"}
VALID_DAYS = 365
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_RE = re.compile(r"^[A-Z2-9]{12}$")
CID_RE = re.compile(r"^gift_[0-9a-f]{24}$")
TOP = "vouchers"
SESSION_TTL = 3600                           # a voucher's payment page stays open an hour (Stripe's minimum is 30 minutes)


def markets():
    """The markets a voucher is sold and redeemed in: selectable, in euros, reading the EU edition of the legal texts."""
    return tuple(m for m in pay.SELECTABLE if pay.market_currency(m) == "eur" and not pay.edition_market(m))


def market_ok(market):
    return isinstance(market, str) and market in markets()


def value_of(kind, market):
    """The value of a voucher of this kind in this market (the standard price list, the market's smallest unit)."""
    return int(pay.price_list(market)[KIND_PRICE[kind]])


# ----------------------------------------------------------------------------- the code
def code_for(sid):
    """The voucher code of a paid voucher session: always the same for the same session (the server's secret over the session id)."""
    d = hmac.new(L._ticket_secret(), ("snapeyes-voucher-v1:" + sid).encode("ascii", "replace"), hashlib.sha256).digest()
    n = int.from_bytes(d[:8], "big")
    return "".join(ALPHABET[(n >> (5 * i)) & 31] for i in range(12))


def normal(code):
    """The code as typed (any case, spaces, dashes) in its plain form, or None when it cannot be a code."""
    if not isinstance(code, str) or len(code) > 40:
        return None
    c = re.sub(r"[\s\-]", "", code).upper()
    return c if CODE_RE.fullmatch(c) and all(ch in ALPHABET for ch in c) else None


def shown(code):
    """The code as people read it: ABCD-EFGH-JKLM."""
    return f"{code[:4]}-{code[4:8]}-{code[8:]}"


def coupon_id(code):
    """The Stripe coupon id of a code (one way: the id does not give the code back)."""
    return "gift_" + hashlib.sha256(("snapeyes-voucher-coupon:" + code).encode("ascii")).hexdigest()[:24]


def record_path(cid):
    return f"{TOP}/{cid}.json"


# ----------------------------------------------------------------------------- the words
NAME = {
    "one": {"en": "SnapEyes gift voucher: iris artwork of one eye",
            "de": "SnapEyes-Geschenkgutschein: Iris-Kunstwerk mit einem Auge",
            "lt": "SnapEyes dovanų kuponas: vienos akies rainelės kūrinys",
            "hu": "SnapEyes ajándékutalvány: íriszalkotás egy szemről",
            "hr": "SnapEyes poklon-bon: umjetnička slika šarenice jednog oka"},
    "two": {"en": "SnapEyes gift voucher: iris artwork of two eyes",
            "de": "SnapEyes-Geschenkgutschein: Iris-Kunstwerk mit zwei Augen",
            "lt": "SnapEyes dovanų kuponas: dviejų akių rainelės kūrinys",
            "hu": "SnapEyes ajándékutalvány: íriszalkotás két szemről",
            "hr": "SnapEyes poklon-bon: umjetnička slika šarenice dvaju očiju"},
}
DESC = {
    "en": "A code for one order on snapeyes.com, valid for 12 months. The person you give it to photographs their own eye.",
    "de": "Ein Code für eine Bestellung auf snapeyes.com, 12 Monate gültig. Die beschenkte Person fotografiert ihr eigenes Auge.",
    "lt": "Kodas vienam užsakymui snapeyes.com, galioja 12 mėnesių. Apdovanotas žmogus nusifotografuoja savo akį pats.",
    "hu": "Kód egy rendeléshez a snapeyes.com oldalon, 12 hónapig érvényes. A megajándékozott a saját szemét fotózza le.",
    "hr": "Kod za jednu narudžbu na snapeyes.com, vrijedi 12 mjeseci. Osoba kojoj ga darujete sama fotografira svoje oko.",
}
SUBMIT = {
    "en": "You receive the voucher code by email right after paying. An unused voucher can be withdrawn within 14 days.",
    "de": "Den Gutscheincode erhalten Sie direkt nach der Zahlung per E-Mail. Einen unbenutzten Gutschein können Sie innerhalb von 14 Tagen widerrufen.",
    "lt": "Kupono kodą gausite el. paštu iškart po apmokėjimo. Nepanaudoto kupono galite atsisakyti per 14 dienų.",
    "hu": "Az utalvány kódját a fizetés után azonnal megkapja e-mailben. A fel nem használt utalványtól 14 napon belül elállhat.",
    "hr": "Kod bona dobit ćete e-poštom odmah nakon plaćanja. Ugovor o neiskorištenom bonu možete jednostrano raskinuti u roku od 14 dana.",
}
# the coupon's name: Stripe shows it beside the discount on its payment page and receipt (at most 40 characters)
COUPON_NAME = {"en": "SnapEyes gift voucher", "de": "SnapEyes-Geschenkgutschein", "lt": "SnapEyes dovanų kuponas",
               "hu": "SnapEyes ajándékutalvány", "hr": "SnapEyes poklon-bon"}
# the confirmation e-mail's price row of an order a voucher paid for, in part or entirely: "{price}, gift voucher -{discount}, paid {paid}"
PRICE_ROW = {
    "en": "{price}, gift voucher −{discount}, paid {paid}",
    "de": "{price}, Geschenkgutschein −{discount}, bezahlt {paid}",
    "lt": "{price}, dovanų kuponas −{discount}, sumokėta {paid}",
    "hu": "{price}, ajándékutalvány −{discount}, fizetve {paid}",
    "hr": "{price}, poklon-bon −{discount}, plaćeno {paid}",
}

MAIL = {
    "en": {
        "subject": "Your SnapEyes gift voucher {code}",
        "hello": "Hello,",
        "thanks": "thank you for buying a SnapEyes gift voucher. Here is the code to give:",
        "rows": ("Voucher code", "Value", "For", "Valid until"),
        "how_h": "How the voucher is used",
        "how": ("1. The person you give it to opens snapeyes.com on their phone and photographs their own eye.\n"
                "2. They choose a style and see a free preview.\n"
                "3. At the checkout they tap \"I have a gift voucher\" and enter the code. The voucher pays for the artwork; "
                "if they choose a larger one, they pay only the difference."),
        "rules": ("The voucher can be used once, within 12 months. If the artwork costs less than the voucher, the rest is not paid out. "
                  "Please keep the code safe: anyone who has it can use it."),
        "wd_h": "If you change your mind",
        "wd": ("You can withdraw from this purchase within 14 days, as long as the voucher has not been used: write to info@snapeyes.com "
               "with the voucher code, and we refund the full amount and cancel the code."),
        "bye": "Warm wishes,\nSnapEyes",
        "kind": {"one": "an iris artwork of one eye, any style", "two": "an iris artwork of two eyes, any style"},
        "legal": "Below are our terms of sale and the withdrawal information, as text.",
    },
    "de": {
        "subject": "Ihr SnapEyes-Geschenkgutschein {code}",
        "hello": "Guten Tag,",
        "thanks": "vielen Dank für den Kauf eines SnapEyes-Geschenkgutscheins. Hier ist der Code zum Verschenken:",
        "rows": ("Gutscheincode", "Wert", "Für", "Gültig bis"),
        "how_h": "So wird der Gutschein eingelöst",
        "how": ("1. Die beschenkte Person öffnet snapeyes.com auf dem Smartphone und fotografiert ihr eigenes Auge.\n"
                "2. Sie wählt einen Stil und sieht eine kostenlose Vorschau.\n"
                "3. An der Kasse tippt sie auf „Ich habe einen Geschenkgutschein“ und gibt den Code ein. Der Gutschein bezahlt das "
                "Kunstwerk; wählt sie ein größeres, zahlt sie nur die Differenz."),
        "rules": ("Der Gutschein gilt für eine Bestellung innerhalb von 12 Monaten. Kostet das Kunstwerk weniger als der Gutschein, wird "
                  "der Rest nicht ausgezahlt. Bitte bewahren Sie den Code sicher auf: Wer ihn hat, kann ihn einlösen."),
        "wd_h": "Wenn Sie es sich anders überlegen",
        "wd": ("Sie können diesen Kauf innerhalb von 14 Tagen widerrufen, solange der Gutschein nicht eingelöst ist: Schreiben Sie an "
               "info@snapeyes.com mit dem Gutscheincode, und wir erstatten den vollen Betrag und sperren den Code."),
        "bye": "Herzliche Grüße\nSnapEyes",
        "kind": {"one": "ein Iris-Kunstwerk mit einem Auge, jeder Stil", "two": "ein Iris-Kunstwerk mit zwei Augen, jeder Stil"},
        "legal": "Unten finden Sie unsere AGB und die Widerrufsbelehrung als Text.",
    },
    "lt": {
        "subject": "Jūsų SnapEyes dovanų kuponas {code}",
        "hello": "Laba diena,",
        "thanks": "ačiū, kad pirkote SnapEyes dovanų kuponą. Štai kodas, kurį galite padovanoti:",
        "rows": ("Kupono kodas", "Vertė", "Kam", "Galioja iki"),
        "how_h": "Kaip panaudoti kuponą",
        "how": ("1. Apdovanotas žmogus telefone atsidaro snapeyes.com ir nusifotografuoja savo akį.\n"
                "2. Pasirenka stilių ir pamato nemokamą peržiūrą.\n"
                "3. Kasoje paspaudžia „Turiu dovanų kuponą“ ir įveda kodą. Kuponas apmoka paveikslą; "
                "jei pasirenkamas didesnis, reikia primokėti tik skirtumą."),
        "rules": ("Kuponą galima panaudoti vieną kartą per 12 mėnesių. Jei paveikslas kainuoja mažiau nei kuponas, likutis negrąžinamas. "
                  "Saugokite kodą: juo gali pasinaudoti bet kas, kas jį žino."),
        "wd_h": "Jei persigalvosite",
        "wd": ("Per 14 dienų galite atsisakyti šio pirkimo, jei kuponas dar nepanaudotas: parašykite info@snapeyes.com ir nurodykite kupono kodą. "
               "Grąžinsime visą sumą, o kodą panaikinsime."),
        "bye": "Šiltai,\nSnapEyes",
        "kind": {"one": "vienos akies rainelės kūrinys, bet kuris stilius", "two": "dviejų akių rainelės kūrinys, bet kuris stilius"},
        "legal": "Žemiau pateikiame pardavimo sąlygas ir informaciją apie teisę atsisakyti sutarties.",
    },
    "hu": {
        "subject": "Az Ön SnapEyes ajándékutalványa: {code}",
        "hello": "Jó napot kívánunk!",
        "thanks": "Köszönjük, hogy SnapEyes ajándékutalványt vásárolt. Íme a kód, amelyet ajándékba adhat:",
        "rows": ("Utalványkód", "Érték", "Mire", "Érvényes"),
        "how_h": "Így lehet felhasználni az utalványt",
        "how": ("1. A megajándékozott megnyitja a snapeyes.com oldalt a telefonján, és lefotózza a saját szemét.\n"
                "2. Kiválaszt egy stílust, és megnéz egy ingyenes előnézetet.\n"
                "3. A pénztárnál a „Van ajándékutalványom” gombra koppint, és beírja a kódot. Az utalvány kifizeti az alkotást; "
                "ha nagyobbat választ, csak a különbözetet kell kifizetnie."),
        "rules": ("Az utalvány egyszer, 12 hónapon belül használható fel. Ha az alkotás kevesebbe kerül, mint az utalvány, a maradékot nem fizetjük ki. "
                  "Kérjük, őrizze meg biztonságban a kódot: bárki felhasználhatja, akinél megvan."),
        "wd_h": "Ha meggondolja magát",
        "wd": ("A vásárlástól 14 napon belül elállhat, amíg az utalványt nem használták fel: írjon az info@snapeyes.com címre az utalvány kódjával, "
               "és a teljes összeget visszatérítjük, a kódot pedig érvénytelenítjük."),
        "bye": "Üdvözlettel:\nSnapEyes",
        "kind": {"one": "íriszalkotás egy szemről, bármilyen stílusban", "two": "íriszalkotás két szemről, bármilyen stílusban"},
        "legal": "Alább szövegként olvashatók az általános szerződési feltételeink és az elállási tájékoztató.",
    },
    "hr": {
        "subject": "Vaš SnapEyes poklon-bon {code}",
        "hello": "Dobar dan,",
        "thanks": "hvala vam što ste kupili SnapEyes poklon-bon. Ovo je kod koji možete darovati:",
        "rows": ("Kod bona", "Vrijednost", "Za", "Vrijedi do"),
        "how_h": "Kako se bon koristi",
        "how": ("1. Osoba kojoj ga darujete otvori snapeyes.com na mobitelu i fotografira svoje oko.\n"
                "2. Odabere stil i vidi besplatni pregled.\n"
                "3. Na blagajni dodirne „Imam poklon-bon” i upiše kod. Bon plaća umjetničku sliku; "
                "ako odabere veću, plaća samo razliku."),
        "rules": ("Bon se može iskoristiti jednom, u roku od 12 mjeseci. Ako slika košta manje od bona, ostatak se ne isplaćuje. "
                  "Čuvajte kod: svatko tko ga ima može ga iskoristiti."),
        "wd_h": "Ako se predomislite",
        "wd": ("Ugovor o ovoj kupnji možete jednostrano raskinuti u roku od 14 dana dok bon nije iskorišten: pišite na info@snapeyes.com i "
               "navedite kod bona. Vratit ćemo cijeli iznos i poništiti kod."),
        "bye": "Srdačan pozdrav,\nSnapEyes",
        "kind": {"one": "umjetnička slika šarenice jednog oka, bilo koji stil", "two": "umjetnička slika šarenice dvaju očiju, bilo koji stil"},
        "legal": "U nastavku su naši uvjeti prodaje i informacije o pravu na jednostrani raskid ugovora, kao tekst.",
    },
}


def lang_of(v):
    return v if v in pay.LANGS else "en"


# ----------------------------------------------------------------------------- buying
def buy(body):
    """POST /api/checkout {gift: {kind}, market, lang}: the Stripe payment page of a voucher. {ok, url, kind, value, currency, market}."""
    why = pay.ordering_problem()
    if why:
        raise pay.PayNotConfigured(why)
    g = body.get("gift") if isinstance(body.get("gift"), dict) else {}
    kind = g.get("kind")
    if kind not in KINDS:
        raise L.ClientError("Choose a voucher: one or two eyes.")
    market = body.get("market") if body.get("market") is not None else pay.DEFAULT_MARKET
    if not market_ok(market):
        raise store.Answer(409, "voucher_market", "Gift vouchers are sold in euros only.", False, markets=list(markets()))
    lang = lang_of(body.get("lang"))
    value = value_of(kind, market)
    now = int(time.time())
    ref = "gift-" + secrets.token_hex(8)
    site = pay.site()
    params = [
        ("mode", "payment"),
        ("success_url", f"{site}/gift?lang={lang}&s={{CHECKOUT_SESSION_ID}}" + (f"&m={market}" if market != pay.DEFAULT_MARKET else "")),
        ("cancel_url", f"{site}/gift?lang={lang}&cancelled=1" + (f"&m={market}" if market != pay.DEFAULT_MARKET else "")),
        ("locale", pay.stripe_locale({"lang": lang, "market": market})),
        ("client_reference_id", ref),
        ("expires_at", str(now + SESSION_TTL)),
        ("adaptive_pricing[enabled]", "false"),
        ("line_items[0][quantity]", "1"),
        ("line_items[0][price_data][currency]", pay.market_currency(market)),
        ("line_items[0][price_data][unit_amount]", str(value)),
        ("line_items[0][price_data][product_data][name]", NAME[kind][lang]),
        ("line_items[0][price_data][product_data][description]", DESC[lang]),
        ("custom_text[submit][message]", SUBMIT[lang]),
        ("payment_intent_data[description]", f"SnapEyes gift voucher {ref}"),
        ("payment_intent_data[metadata][voucher]", ref),
    ]
    meta = {"kind": "voucher", "voucher_kind": kind, "voucher_value": str(value), "market": market,
            "currency": pay.market_currency(market), "lang": lang, "ref": ref}
    camp = counter.pack(counter.parse(body.get("camp")))
    if camp:
        meta["src"] = camp
    params += [(f"metadata[{k}]", v) for k, v in meta.items()]
    r = pay._stripe("POST", "/v1/checkout/sessions", params, idem=f"snapeyes-voucher-{ref}")
    if r.status_code != 200:
        pay._raise_for(r, "stripe create voucher session")
    try:
        sess = r.json()
    except ValueError:
        raise pay.PayBusy("stripe create voucher session: unreadable reply") from None
    sid, url = (sess.get("id"), sess.get("url")) if isinstance(sess, dict) else (None, None)
    if not (isinstance(sid, str) and pay.SID_RE.fullmatch(sid) and isinstance(url, str) and url.startswith("https://")):
        raise pay.PayError("stripe create voucher session: the reply has no session id or no https url")
    pay.log(f"voucher {ref}: checkout {sid} {kind} {value} ({market}) {lang}")
    return {"ok": True, "url": url, "kind": kind, "value": value, "currency": pay.market_currency(market).upper(), "market": market}


# ----------------------------------------------------------------------------- paid
def is_voucher_session(sess):
    meta = sess.get("metadata") if isinstance(sess, dict) and isinstance(sess.get("metadata"), dict) else {}
    return isinstance(sess, dict) and sess.get("object") == "checkout.session" and meta.get("kind") == "voucher"


def _session_terms(sess):
    """(kind, value, market, lang) the server wrote into a voucher session, or None when they do not hold together."""
    meta = sess.get("metadata") if isinstance(sess.get("metadata"), dict) else {}
    kind, market = meta.get("voucher_kind"), meta.get("market")
    if kind not in KINDS or not market_ok(market):
        return None
    try:
        value = int(meta.get("voucher_value"))
    except (TypeError, ValueError):
        return None
    if value <= 0 or str(meta.get("currency") or "") != pay.market_currency(market):
        return None
    return kind, value, market, lang_of(meta.get("lang"))


def valid_day(paid_at):
    """The last day a voucher bought at paid_at can be used (YYYY-MM-DD, UTC)."""
    return time.strftime("%Y-%m-%d", time.gmtime(int(paid_at) + VALID_DAYS * 86400))


def redeem_by(day):
    """The end of that day (UTC) as Stripe's redeem_by."""
    return calendar.timegm(time.strptime(day, "%Y-%m-%d")) + 86399


def _coupon(cid, code, value, currency, day, sid, kind, lang):
    """Make the coupon of a voucher at Stripe, once (a coupon with this id that exists already is taken as made: same id, same code)."""
    params = [("id", cid), ("amount_off", str(value)), ("currency", currency), ("duration", "once"), ("max_redemptions", "1"),
              ("redeem_by", str(redeem_by(day))), ("name", COUPON_NAME[lang]),
              ("metadata[voucher_session]", sid), ("metadata[voucher_kind]", kind), ("metadata[code_end]", code[-4:])]
    r = pay._stripe("POST", "/v1/coupons", params, idem=f"snapeyes-voucher-coupon-{sid}")
    if r.status_code == 200:
        return
    try:
        err = (r.json() or {}).get("error") or {}
    except (ValueError, AttributeError):
        err = {}
    if r.status_code == 400 and err.get("code") == "resource_already_exists":
        return
    pay._raise_for(r, "stripe create voucher coupon")


def on_paid(sess, source):
    """A paid voucher session: its coupon, its record and its email, each once. Returns (state, info): state "ready" with {code, kind, value,
    currency, valid_until, mail}; "pending" (not paid yet); "refused" (not a voucher this server sold at its price: the owner is told)."""
    sid = sess.get("id")
    terms = _session_terms(sess)
    if terms is None or not isinstance(sid, str) or not pay.SID_RE.fullmatch(sid):
        pay.log(f"voucher session {str(sid)[:40]}: metadata unreadable, ignored")
        return "refused", {}
    if not pay.session_paid(sess):
        return "pending", {}
    kind, value, market, lang = terms
    currency = pay.market_currency(market)
    cur = str(sess.get("currency") or "").lower()
    if sess.get("amount_total") != value or cur != currency:
        pay.note_once(f"{TOP}/note_mismatch_{pay._order_tag(sid)}.json", "voucher_mismatch",
                      f"SnapEyes: a gift voucher payment does not match its price, please check {sid}",
                      f"Stripe session {sid} of a gift voucher ({kind}) was paid {pay.amount_text(sess.get('amount_total') or 0, 'en', cur)}, "
                      f"but the voucher costs {pay.amount_text(value, 'en', currency)}. No code was issued. Please check it in the "
                      f"Stripe Dashboard and refund it, then write to the buyer.\n")
        return "refused", {}
    if not pay.session_counts(sess):
        pay.log(f"voucher session {sid}: a TEST-mode payment, and this deployment takes no test orders: ignored")
        return "refused", {}
    code = code_for(sid)
    cid = coupon_id(code)
    path = record_path(cid)
    rec = store.get_json(path, timeout=8.0)
    if not isinstance(rec, dict):
        now = int(time.time())
        day = valid_day(now)
        _coupon(cid, code, value, currency, day, sid, kind, lang)
        rec = {"voucher": True, "coupon": cid, "session_id": sid, "kind": kind, "value": value, "currency": currency, "market": market,
               "lang": lang, "paid_at": now, "paid_iso": pay.iso(now), "valid_until": day, "livemode": bool(sess.get("livemode")),
               "source": source, "code_end": code[-4:]}
        meta = sess.get("metadata") if isinstance(sess.get("metadata"), dict) else {}
        camp = counter.parse(meta.get("src"))
        if camp:
            rec["camp"] = counter.pack(camp)
        try:
            store.put(path, store.json_bytes(rec), "application/json", upsert=False, timeout=8.0)
            pay.log(f"voucher {cid} SOLD via {source}: {kind} {pay.amount_text(value, 'en', currency)} ({market}) live={rec['livemode']}")
        except store.StorageExists:
            rec = store.get_json(path, timeout=8.0) or rec
    # the owner's note, once (claimed: a note Resend could not take is tried again at the next call, the webhook's retry or the success page)
    pay.note_once(f"{TOP}/note_sold_{cid}.json", "voucher_sold",
                  f"SnapEyes: gift voucher sold, {pay.amount_text(rec['value'], 'en', rec['currency'])}",
                  f"A gift voucher was bought ({rec['kind']}: {pay.amount_text(rec['value'], 'en', rec['currency'])}, "
                  f"{'live' if rec.get('livemode') else 'TEST mode'}), valid until {rec.get('valid_until')}.\nStripe session {sid}, coupon {cid} "
                  f"(code ending {code[-4:]}).\nIf the buyer withdraws within 14 days and the voucher is unused: refund the payment "
                  f"in the Stripe Dashboard and delete the coupon {cid} (Product catalogue, Coupons).\n")
    mail = mail_once(sess, rec, code)
    return "ready", {"code": shown(code), "kind": kind, "value": value, "currency": currency.upper(), "valid_until": rec.get("valid_until"),
                     "mail": mail, "lang": lang}


def mail_once(sess, rec, code):
    """The buyer's email with the code, once (claimed): "sent", "done" (sent before), "off", "bad_address", "transient", "failed",
    "legal_unavailable"."""
    cd = sess.get("customer_details") if isinstance(sess.get("customer_details"), dict) else {}
    to = cd.get("email") or sess.get("customer_email")
    if not pay.email_configured():
        return "off"
    claim = f"{TOP}/{rec['coupon']}.mail.json"
    if not pay.claim_once(claim):
        cur = store.get_json(claim, timeout=6.0)
        return "done" if isinstance(cur, dict) and cur.get("state") == "sent" else "sending"
    try:
        pack = pay.legal_pack()
        docs = pay.pack_docs(pack, rec["lang"], rec["market"]) if pack else None
        if docs is None:
            pay._mark(claim, "retry")
            return "legal_unavailable"
        subject, text, html_body = mail(rec, code, docs)
        res = pay.send_mail(to, subject, text, f"snapeyes-voucher-mail-{rec['session_id']}", html_body)
    except Exception as e:  # noqa: the claim must not stay "sending" for the stale period
        pay._mark(claim, "retry")
        raise e
    pay._mark(claim, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res)
    if res in ("bad_address", "failed"):
        pay.note_once(f"{TOP}/note_mail_{rec['coupon']}.json", "voucher_mail",
                      "SnapEyes: a gift voucher email could not be sent",
                      f"The email with the gift voucher code (session {rec['session_id']}, coupon {rec['coupon']}) could not be sent ({res}).\n"
                      f"The buyer sees the code on the page they came back to after paying. Please write to them (their address is in the "
                      f"Stripe session).\n")
    return res


def mail(rec, code, docs):
    """(subject, text, html) of the buyer's email: the code, its value, what it pays for, how it is used, the rules, the withdrawal, then the terms
    and the withdrawal information of the EU edition as text."""
    lang = rec["lang"]
    w = MAIL[lang]
    money = pay.price_text(rec["value"], lang, rec["currency"])
    subject = w["subject"].format(code=shown(code))
    blocks = [("p", w["hello"]), ("p", w["thanks"]),
              ("rows", list(zip(w["rows"], (shown(code), money, w["kind"][rec["kind"]], pay.date_text(rec["valid_until"], lang))))),
              ("link", f"{pay.site()}/try?lang={lang}"),
              ("h", w["how_h"]), ("p", w["how"]), ("p", w["rules"]),
              ("h", w["wd_h"]), ("p", w["wd"]),
              ("p", w["bye"]), ("p", w["legal"]),
              ("rule",), ("doc", docs["withdrawal"]["text"]), ("rule",), ("doc", docs["terms"]["text"])]
    text, html_body = pay.render_mail(blocks, lang, subject)
    return subject, text, html_body


def status(sid):
    """GET /api/checkout?gift=<session id>: the success page's question. {ok, state: ready (with the code) | pending | expired | unknown}."""
    if not isinstance(sid, str) or not pay.SID_RE.fullmatch(sid):
        raise L.ClientError("This is not a voucher payment.")
    if not pay.stripe_key():
        raise pay.PayNotConfigured("STRIPE_SECRET_KEY is not set")
    sess = pay.retrieve_session(sid)
    if not is_voucher_session(sess):
        return {"ok": True, "state": "unknown"}
    state, info = on_paid(sess, "gift_page")
    if state == "pending":
        st = "expired" if sess.get("status") == "expired" else "pending"
        return {"ok": True, "state": st}
    if state != "ready":
        return {"ok": True, "state": "unknown"}
    return dict({"ok": True, "state": "ready"}, **info)


# ----------------------------------------------------------------------------- redeeming
def lookup(code, market):
    """The voucher of a typed code for an order in this market: {coupon, value, currency, valid_until}. Raises store.Answer 409 voucher_invalid
    {why: format, unknown, used, expired, currency} when it cannot pay for this order."""
    c = normal(code)
    if c is None:
        raise store.Answer(409, "voucher_invalid", "This is not a voucher code. Please check it.", False, why="format")
    cid = coupon_id(c)
    r = pay._stripe("GET", f"/v1/coupons/{cid}", timeout=10.0)
    if r.status_code == 404:
        raise store.Answer(409, "voucher_invalid", "We do not know this voucher code. Please check it.", False, why="unknown")
    if r.status_code != 200:
        pay._raise_for(r, "stripe retrieve voucher coupon")
    try:
        cp = r.json()
    except ValueError:
        raise pay.PayBusy("stripe retrieve voucher coupon: unreadable reply") from None
    if not isinstance(cp, dict) or cp.get("id") != cid or not isinstance(cp.get("amount_off"), int):
        raise store.Answer(409, "voucher_invalid", "We do not know this voucher code. Please check it.", False, why="unknown")
    times, cap = cp.get("times_redeemed") or 0, cp.get("max_redemptions")
    if isinstance(cap, int) and times >= cap:
        raise store.Answer(409, "voucher_invalid", "This voucher has already been used.", False, why="used")
    rb = cp.get("redeem_by")
    if cp.get("valid") is False or (isinstance(rb, int) and rb < time.time()):
        raise store.Answer(409, "voucher_invalid", "This voucher has expired.", False, why="expired")
    if str(cp.get("currency") or "").lower() != pay.market_currency(market) or not market_ok(market):
        raise store.Answer(409, "voucher_invalid", "This voucher can be used for orders in euros only.", False, why="currency")
    until = time.strftime("%Y-%m-%d", time.gmtime(rb)) if isinstance(rb, int) else None
    return {"coupon": cid, "value": int(cp["amount_off"]), "currency": pay.market_currency(market), "valid_until": until}


def check(code, market):
    """GET /api/checkout?voucher=<code>&m=<market>: the checkout's look at a typed code before it opens Stripe. {ok, valid, value, currency,
    valid_until} or the 409 voucher_invalid of lookup."""
    if market is None:
        market = pay.DEFAULT_MARKET
    if not pay.stripe_key():
        raise pay.PayNotConfigured("STRIPE_SECRET_KEY is not set")
    v = lookup(code, market)
    return {"ok": True, "valid": True, "value": v["value"], "currency": v["currency"].upper(), "valid_until": v["valid_until"]}


def price_row(paid, lang, currency, price_text):
    """The confirmation e-mail's price for an order a voucher paid (paid["voucher"]): "<price>, gift voucher -<discount>, paid <paid>"; None without one."""
    v = paid.get("voucher") if isinstance(paid, dict) else None
    if not isinstance(v, dict):
        return None
    try:
        listed, discount = int(v["price"]), int(v["discount"])
    except (KeyError, TypeError, ValueError):
        return None
    return PRICE_ROW[lang_of(lang)].format(price=price_text(listed, lang, currency), discount=price_text(discount, lang, currency),
                                           paid=price_text(paid.get("amount_total") or 0, lang, currency))
