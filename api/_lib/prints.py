# -*- coding: utf-8 -*-
"""Prints of the artwork, an option of an order on the euro markets: the offer, its switch, the checkout's part of it, the paid record, the
order at the print partner (merchOne, api/_lib/merchone.py), its status, the shipping e-mail and the admin's view.

THE OFFER is api/_lib/print_offer.py (the products and their retail prices, the markets that offer prints), the COST is api/_lib/print_rates.py
(merchOne's price and print file of every SKU, its shipping per country, written by scripts/print_rates.py), the WORDS of the products and the
countries are api/_lib/print_names.py. The checkout never asks merchOne: it reads those tables.

THE SWITCH (the owner's, in the admin page "Spaudiniai"; OFF until he turns it on): ops/prints/switch.json in the private bucket, written only
by the admin action print_switch (audited). A storage error reads as OFF, never as on (fail closed). While it is off, GET /api/checkout says
prints: {on: false} and POST /api/checkout refuses a print (409 print_unavailable); orders that were paid with a print are still made and
sent to merchOne (the switch is about selling, not about fulfilling what was sold). Prints are also off without MERCHONE_API_USER and
MERCHONE_API_KEY.

AT CHECKOUT (api/checkout.py): the request may carry print {product, country} and consent_print true. The server prices it (the product's
price, and the shipping of that product to that country: merchOne's rate with VAT, rounded up to the next .49 or .99, ship_price), adds a
second line item, Stripe's shipping address form limited to that ONE country (the shipping price is the country's, so the address cannot be
in another), one fixed shipping rate, the print's own note above the pay button, and records it in the metadata (print, print_sku,
print_amount, ship_amount, ship_cc) and in order.json (checkout.print, with the print consent: version, time, text, fingerprint). The
artwork's own price, its consent and every other check are unchanged; a session without a print is byte for byte what it was before.

WHEN PAID (pay.record_paid): paid.json gains print {product, sku, kind, cm, country, price, ship, name, address, consent, mismatch?}: the
address Stripe collected (shipping_details, or collected_information.shipping_details in the newer API versions). A country other than the
priced one, or no address, is recorded as mismatch and the print is held for the owner (it is never sent to another country's price).

A PRINT BOUGHT AFTER THE ARTWORK (the add-on, 2026-11-21; the owner: a big price at the first checkout scares, so the print is offered once the
customer has the file). The order page of a paid, DELIVERED order without a print shows the offer (addon_offer in the status reply; who gets it
is addon_problem: a payment that counts, delivered and not waiting for the owner's look, not withdrawn, deleted, expired or refunded, no print
yet, a market that offers prints, the switch on, merchOne configured). The order link (order id and key) is the authentication, as for
everything on that page. POST /api/checkout {addon: {order, key}, print: {product, country}, consent_print: true[, print_shown], lang}
(addon_buy) makes a Checkout Session OF ITS OWN: the print as its only line item, the country's shipping rate, the address form for that one
country, the print's own note above the pay button, metadata kind "print_addon" with order, key_sha, print, print_sku, print_amount,
ship_amount, ship_cc, lang, market, currency, consent_version and consent_at; no voucher and no price experiment. One payable add-on session
per order: the earlier ones are expired at Stripe first, and one that turns out paid is recorded instead.
  orders/<order>/print_checkout.json   the latest add-on checkout: its session, the earlier ones, the print with the print box the customer
                                       ticked (version, time, text, fingerprint)
  orders/<order>/print_paid.json       created once (upsert False), by the Stripe webhook or by the order page's own check of the session
                                       (GET /api/checkout?addon=<session>&o=<order>&k=<key>, addon_status): {paid, session_id, payment_intent,
                                       amount_total, currency, at, livemode, email, print: the shape paid_part makes}. An amount other than the
                                       print's price plus its shipping (or another currency) is recorded with mismatch ["amount"]: held
  orders/<order>/print_confirmation.json   the add-on's own confirmation e-mail, claimed before sending (addon_mail_once)
pay.get_paid reads print_paid.json beside paid.json and merges it (pay.merge_addon): a paid record without a print gains print and
print_addon {session_id, payment_intent, amount_total, at, livemode, email}, so the fulfilment, the status, the tracking and the shipping
e-mail below read paid["print"] as they always did. What differs for an add-on is only the money: its payment is print_payment(paid), not
the order's, so the admin's refund of THAT payment cancels the print and a refund of the artwork's payment alone leaves it (_refunded), and
the artwork's confirmation and price checks never count it (amend_confirmation, abtest.paid_extra). A second paid add-on session of an order
that has its print already is stored as extra_payment_<id>.json and the owner told to refund it (_addon_extra); nothing is printed twice.

FULFILMENT (step): once the artwork is DELIVERED (delivery.json exists and is not waiting for the owner's look, or he released it), the
master is scaled to the SKU's print file (its design area at the resolution the master allows, at least merchOne's minimum and at most
PRINT_DPI; the trim around it filled by continuing the artwork's own edge; an artwork that is not square is centred and its background
continued), stored as orders/<order>/print_<product>.jpg and handed to merchOne as a signed link that expires (SIGNED_DAYS days). The
merchOne order carries external_id = our order id (a re-created order after one that failed: "<order>-2", "-3"), is_test unless MERCHONE_LIVE
is on and the payment was live, the customer's name and delivery address, our own address as its e-mail (merchOne gets the name and the
address, nothing else of the customer) and our company as the billing address. The record is orders/<order>/print.json:
  {state, attempts, series, merchone_id, external_id, is_test, file, error, tracking, history, ...}
  state: waiting (not sent yet: the artwork is not delivered, merchOne was busy, or not configured), creating (a try is on it),
         created (merchOne has it), shipped (merchOne sent it: tracking), failed (merchOne refused it, or MAX_ATTEMPTS tries failed: the
         owner is told and retries in the admin page), held (the address does not match the priced country: the owner decides), canceled
Idempotency: one try at a time (print.lock, created atomically, taken over after LOCK_STALE), a try never runs for an order whose
print.json says created or later, and merchOne itself refuses a second order with the same external id and names the first one (adopted).
So a Stripe retry, a second page, the server's chain and the daily run can never make two merchOne orders.
Who asks for it: the server's own making right after the artwork is ready (api/_lib/maker.py _step: a fresh step of the chain, after the
ready e-mail), the admin's release of a held artwork (it asks the server's chain), the daily clean-up (daily: every print of the index
cleanup/print/<order>.json that is waiting, and the status of every created one: the shipping as a fallback for a lost webhook), and the
admin's retry. Nothing here ever raises into the order's making: a print that cannot be sent waits and is visible in the admin page.

THE WEBHOOK of merchOne (shipment_sent, shipment_tracking_event, order_canceled, order_failed, order_commented): POST
/api/order?hook=merchone&token=<hook_token()> (the admin page shows the URL to paste into the merchOne store settings: merchOne signs nothing,
so the token in the URL is the proof; the event's order is then read back from merchOne's own API before anything is believed). The customer
gets the shipping e-mail with the tracking link once (print_mail.json, claimed before sending)."""
import io, os, re, json, time, hmac, hashlib, secrets, threading
from . import iris as L
from . import store
from . import pay
from . import merchone as M
from .print_offer import PRINT_OFFER
from .print_rates import PRINT_RATES
from .print_names import PRINT_NAMES
from .print_times import PRINT_TIMES

LANGS = ("en", "de", "lt", "hu", "hr", "fi", "et", "lv")
SWITCH_PATH = "ops/prints/switch.json"
SWITCH_TTL = 30.0            # one read of the switch per instance per 30 s
SWITCH_FAIL_TTL = 5.0        # a failed read is remembered this long (read as OFF)
INDEX = "cleanup/print"      # cleanup/print/<order>.json {"t"}: the prints that are not shipped or closed yet (daily)
LOCK_STALE = 150             # a try's claim (print.lock) older than this belongs to an invocation that died
MAX_ATTEMPTS = 6             # tries before the print is "failed" and waits for the owner (the daily run does one a day)
SIGNED_DAYS = 7              # the print file's link merchOne downloads from
PRINT_DPI = 200              # the print file's resolution at most (the master allows about 170 dpi at 60 cm, more at the smaller sizes)
TIME_NEED = 22.0             # seconds a try needs: read the 4K master, scale it, store it, sign it, one merchOne call
DAILY_SECONDS = 15.0         # the daily run spends at most this long on prints
DAILY_MAX = 6                # ... and at most this many tries or status reads a run
# how long a print takes is api/_lib/print_times.py (production per kind, delivery per country): production_days, transit_days, time_text below
CONTACT = pay.CONTACT
# merchOne's billing address: the seller (src/landing/config.ts SELLER); merchOne invoices the print with German VAT to it
BILLING = {"firstname": "MB", "lastname": "Portretizuokis", "company": "MB Portretizuokis", "street_primary": "Gedimino g. 22A-14",
           "city": "Kaunas", "postcode": "44319", "country": "LT"}
PRODUCER = "Picanova GmbH (merchOne), Eupener Straße 67, 50933 Köln"
PRODUCER_COUNTRY = {"en": "Germany", "de": "Deutschland", "lt": "Vokietija", "hu": "Németország", "hr": "Njemačka", "fi": "Saksa", "et": "Saksamaa", "lv": "Vācija"}
FINAL = ("shipped", "canceled")
PARKED = ("held", "failed", "canceled_partner")   # wait for the owner (admin page, Spaudiniai): the daily run does not spend its turns on them
_TRACK_URL = re.compile(r"^https://[A-Za-z0-9.-]{3,120}(/[^\s<>\"']{0,600})?$")


class Unavailable(Exception):
    pass


# ----------------------------------------------------------------------------- the tables
def products(offered=True):
    """The prints of the offer, in its order (offered=False: also the ones taken off it, which paid orders may still name)."""
    return [p for p in PRINT_OFFER["products"] if not offered or p.get("on") == 1]


def product(pid, offered=True):
    return next((p for p in products(offered) if p["id"] == pid), None) if isinstance(pid, str) else None


def sku_rec(sku):
    r = PRINT_RATES["skus"].get(sku) if isinstance(sku, str) else None
    return r if isinstance(r, dict) else None


def countries():
    """The countries prints ship to (the rate table's, which holds only countries merchOne ships every SKU to), by code."""
    return sorted(PRINT_RATES["shipping"])


def ship_cost(country, sku):
    """merchOne's shipping of one print to a country, in cents without VAT, or None."""
    row = PRINT_RATES["shipping"].get(country) if isinstance(country, str) else None
    v = row.get(sku) if isinstance(row, dict) else None
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def with_vat(cents):
    """cents x (100 + vat_pct) / 100, rounded up to the cent."""
    return -(-int(cents) * (100 + int(PRINT_OFFER["vat_pct"])) // 100)


def ship_price(cost):
    """What the customer pays for shipping: the cost with VAT, rounded UP to the next amount that ends in .49 or .99 (src/shared/prints.ts
    shipPrice is the same rule, and scripts/check_prices.mjs compares them)."""
    c = with_vat(cost)
    for v in range(c, c + 100):
        if v % 100 in (49, 99):
            return v
    return c


def shipping(country, pid):
    """The shipping the customer pays for this print to this country (cents), or None when it does not ship there."""
    p = product(pid, offered=False)
    cost = ship_cost(country, p["sku"]) if p else None
    return ship_price(cost) if cost is not None else None


def margin(pid, country):
    """What a print earns (cents): its price and shipping, less merchOne's price and shipping with VAT and the payment fee (fee_pct of what the
    customer pays for the print). The build refuses a price below PRINT_OFFER margin_floor in any country (scripts/check_prices.mjs)."""
    p = product(pid, offered=False)
    s = sku_rec(p["sku"]) if p else None
    sc = ship_cost(country, p["sku"]) if p else None
    if not p or not s or sc is None:
        return None
    paid = p["price"] + ship_price(sc)
    return paid - with_vat(s["cost"] + sc) - -(-paid * int(PRINT_OFFER["fee_pct"]) // 100)


def size_text(cm):
    return f"{int(cm)} × {int(cm)} cm"


def lang_of(lang):
    return lang if lang in LANGS else "en"


def product_name(pid, lang):
    """"Acrylic glass print 40 × 40 cm" in the language."""
    p = product(pid, offered=False)
    if not p:
        return str(pid)
    name = PRINT_NAMES["kinds"][p["kind"]][lang_of(lang)]
    return f"{name} {size_text(p['cm'])}" if p["cm"] else name       # cm 0: a thing that is not named by a size (the keyring)


def country_name(cc, lang):
    row = PRINT_NAMES["countries"].get(cc) if isinstance(cc, str) else None
    return row[lang_of(lang)] if isinstance(row, dict) else str(cc or "")


def markets():
    return tuple(PRINT_OFFER["markets"])


def production_days(pid):
    """merchOne's production time of a print, in business days (api/_lib/print_times.py production, by the print's kind; a print the offer does
    not know: the longest one)."""
    p = product(pid, offered=False)
    t = PRINT_TIMES["production"]
    return int(t[p["kind"]]) if p and p["kind"] in t else max(int(v) for v in t.values())


def transit_days(country):
    """(from, to, published) working days on the way to a country: merchOne's published time (print_times.py transit), or the general estimate
    of every other country (transit_other, published False: the words then say "about a week" and name no number)."""
    t = PRINT_TIMES["transit"].get(country) if isinstance(country, str) else None
    if isinstance(t, list) and len(t) == 2:
        return int(t[0]), int(t[1]), True
    return int(PRINT_TIMES["transit_other"][0]), int(PRINT_TIMES["transit_other"][1]), False


def time_text(pid, country, lang):
    """The two short sentences of a print's time in a language: "Production: about 2 business days. Delivery (Lithuania): then usually 4 to 6
    working days." (the words of api/_lib/print_names.py times; for a country without a published time: "then usually about a week")."""
    w = PRINT_NAMES["times"][lang_of(lang)]
    a, b, published = transit_days(country)
    name = country_name(country, lang)
    way = w["way"].format(country=name, a=a, b=b) if published else w["way_other"].format(country=name)
    return f"{w['made'].format(n=production_days(pid))} {way}"


# ----------------------------------------------------------------------------- the switch
_SW = {"v": None, "t": 0.0, "failed": 0.0}
_SW_LOCK = threading.Lock()


def _read_switch():
    try:
        v = store.get_json(SWITCH_PATH, timeout=5.0, retry=False)
    except store.StorageNotConfigured:
        return {"on": False, "why": "storage"}
    return v if isinstance(v, dict) else {"on": False}


def switch_state(fresh=False):
    """{on, t, iso, by, rev} of the owner's switch; on is False when it was never turned on or cannot be read (fail closed: a storage error
    is OFF, and is remembered SWITCH_FAIL_TTL seconds so a storage that does not answer costs one slow call)."""
    now = time.time()
    with _SW_LOCK:
        if not fresh and _SW["v"] is not None and now - _SW["t"] < SWITCH_TTL:
            return dict(_SW["v"])
        if not fresh and now - _SW["failed"] < SWITCH_FAIL_TTL:
            return {"on": False, "why": "unreadable"}
    try:
        v = _read_switch()
    except store.StorageError as e:
        pay.log(f"prints: the switch could not be read ({type(e).__name__}): prints are off")
        with _SW_LOCK:
            _SW["failed"] = now
        return {"on": False, "why": "unreadable"}
    v = dict(v, on=v.get("on") is True)
    with _SW_LOCK:
        _SW.update(v=v, t=now, failed=0.0)
    return dict(v)


def set_switch(on, who, rev=None):
    """The admin action print_switch: writes the switch (rev: the revision the page saw; another one is a 409 stale_view). Returns the new state."""
    cur = switch_state(fresh=True)
    if cur.get("why") == "unreadable":
        raise store.StorageError("the print switch could not be read")
    have = cur.get("rev") if isinstance(cur.get("rev"), int) else 0
    if rev is not None and rev != have:
        raise store.Answer(409, "stale_view", "The switch was changed in another tab. Reload the page.", False, None, rev=have)
    now = int(time.time())
    new = {"on": bool(on), "t": now, "iso": pay.iso(now), "by": str(who or "admin")[:40], "rev": have + 1}
    store.put(SWITCH_PATH, store.json_bytes(new), "application/json", upsert=True, timeout=8.0)
    with _SW_LOCK:
        _SW.update(v=new, t=time.time(), failed=0.0)
    return new


def offer_problem(market=None):
    """Why prints cannot be bought now (in this market), or "": the switch, the credentials, the market."""
    if not M.configured():
        return "not_configured"
    if not switch_state().get("on"):
        return "off"
    if market is not None and market not in markets():
        return "market"
    return ""


def public_info():
    """What GET /api/checkout says about prints: {on: false} while they cannot be bought; else the markets that offer them, the products (id,
    kind, cm, price in cents) and the shipping per product and country (cents, VAT included), all in euros. No cost, no SKU, nothing secret."""
    if offer_problem():
        return {"on": False}
    return {"on": True, "currency": PRINT_OFFER["currency"].upper(), "markets": list(markets()),
            "products": [{"id": p["id"], "kind": p["kind"], "cm": p["cm"], "price": p["price"],
                          "ship": {cc: shipping(cc, p["id"]) for cc in countries()}} for p in products()]}


# ----------------------------------------------------------------------------- the checkout's part
PRINT_CONSENT_TEXT = {
    "en": ("I know that my print is made to my order from my personal artwork, so I cannot withdraw from buying it; my rights if it arrives "
           "faulty or damaged are not affected."),
    "de": ("Mir ist bekannt, dass mein Druck nach meiner Bestellung aus meinem persönlichen Kunstwerk angefertigt wird und ich seinen Kauf "
           "deshalb nicht widerrufen kann; meine Rechte bei einem fehlerhaften oder beschädigten Druck bleiben unberührt."),
    "lt": ("Žinau, kad mano spaudinys gaminamas pagal mano užsakymą iš mano asmeninio kūrinio, todėl jo pirkimo atsisakyti negalėsiu; tai "
           "neriboja mano teisių, jei jis atkeliaus su trūkumais ar sugadintas."),
    "hu": ("Tudomásul veszem, hogy a nyomatom a megrendelésemre, a személyes alkotásomból készül, ezért a megvásárlásától nem állhatok el; "
           "ez nem érinti a jogaimat, ha hibásan vagy sérülten érkezik."),
    "hr": ("Znam da se moj ispis izrađuje po mojoj narudžbi iz mojeg osobnog umjetničkog djela, pa za njegovu kupnju nemam pravo na "
           "jednostrani raskid ugovora; to ne utječe na moja prava ako stigne neispravan ili oštećen."),
    "fi": ("Tiedän, että tulosteeni tehdään tilaukseni mukaan henkilökohtaisesta taideteoksestani, joten en voi peruuttaa sen ostoa; "
           "tämä ei vaikuta oikeuksiini, jos se saapuu virheellisenä tai vahingoittuneena."),
    "et": ("Tean, et minu trükitud pilt valmistatakse minu tellimuse järgi minu isiklikust kunstiteosest, seega ei saa ma selle ostust "
           "taganeda; see ei mõjuta minu õigusi, kui see saabub puudusega või kahjustatuna."),
    "lv": ("Es zinu, ka mana izdruka tiek izgatavota pēc mana pasūtījuma no mana personīgā mākslas darba, tāpēc no tās pirkuma atteikties "
           "nevaru; tas neietekmē manas tiesības, ja tā pienāk ar trūkumiem vai bojāta."),
}
# every print consent text ever shown, by consent version (pay.CONSENT_VERSION): an order quotes the text its customer ticked. As pay.CONSENT_TEXTS:
# the version it came with is named, and the current version maps to the current text, so a new CONSENT_VERSION (a waiver that changes) keeps
# the print box quotable under every version; a changed print box needs a new version and its old text kept here under the old ones
# 2026-11-13.1 added the Finnish, Estonian and Latvian boxes: the version before keeps exactly the five boxes it had (as pay.CONSENT_TEXT_1028)
PRINT_CONSENT_TEXT_1028 = {l: PRINT_CONSENT_TEXT[l] for l in ("en", "de", "lt", "hu", "hr")}
PRINT_CONSENT_TEXTS = {"2026-10-28.3": PRINT_CONSENT_TEXT_1028, pay.CONSENT_VERSION: PRINT_CONSENT_TEXT}

SUBMIT_NOTE_PRINT = {   # what Stripe shows above its pay button when the order has a print (the order's language; the EU edition only)
    "en": ("You are buying a digital file (JPEG, 4096 px) and a print of it, shipped to the address above. You agreed that we start the file "
           "right away and that your right of withdrawal ends once we have started; the print is made to your order and cannot be withdrawn "
           "from."),
    "de": ("Sie kaufen eine digitale Datei (JPEG, 4096 px) und einen Druck davon, der an die obige Adresse versandt wird. Sie haben "
           "zugestimmt, dass wir mit der Datei sofort beginnen und Ihr Widerrufsrecht damit erlischt; der Druck wird nach Ihrer Bestellung "
           "angefertigt und ist vom Widerruf ausgeschlossen."),
    "lt": ("Perkate skaitmeninį failą (JPEG, 4096 px) ir jo spaudinį, kuris bus išsiųstas aukščiau nurodytu adresu. Sutikote, kad failą "
           "pradėtume kurti iš karto ir kad Jūsų teisė atsisakyti sutarties baigsis, kai tik pradėsime; spaudinys gaminamas pagal Jūsų "
           "užsakymą, todėl jo pirkimo atsisakyti negalima. Paspausdami mokėjimo mygtuką, pateikiate užsakymą su prievole sumokėti."),
    "hu": ("Digitális fájlt (JPEG, 4096 px) és annak nyomatát vásárolod, amelyet a fenti címre küldünk. Hozzájárultál, hogy a fájlt azonnal "
           "elkezdjük, és tudomásul vetted, hogy a kezdéssel megszűnik az elállási jogod; a nyomat a megrendelésedre készül, ezért attól nem "
           "lehet elállni. A fizetési gombbal fizetési kötelezettséggel járó megrendelést adsz le."),
    "hr": ("Kupujete digitalnu datoteku (JPEG, 4096 px) i njezin ispis, koji šaljemo na gornju adresu. Pristali ste da odmah započnemo s "
           "datotekom i da vaše pravo na jednostrani raskid ugovora prestaje čim započnemo; ispis se izrađuje po vašoj narudžbi pa za njega "
           "nema prava na jednostrani raskid. Klikom na gumb za plaćanje dajete narudžbu s obvezom plaćanja."),
    "fi": ("Ostat digitaalisen tiedoston (JPEG, 4096 px) ja siitä tehdyn tulosteen, joka lähetetään yllä olevaan osoitteeseen. Olet "
           "hyväksynyt, että aloitamme tiedoston heti ja että peruuttamisoikeutesi päättyy, kun olemme aloittaneet; tuloste tehdään "
           "tilauksesi mukaan, eikä sen ostoa voi peruuttaa. Maksupainiketta painamalla teet tilauksen, ja tilaukseen liittyy "
           "maksuvelvollisuus."),
    "et": ("Ostad digitaalse faili (JPEG, 4096 px) ja sellest trükitud pildi, mis saadetakse ülaltoodud aadressile. Nõustusid, et "
           "alustame failiga kohe ja et sinu taganemisõigus lõpeb, kui oleme alustanud; trükitud pilt valmistatakse sinu tellimuse "
           "järgi ja selle ostust ei saa taganeda. Maksenupule vajutades esitad tellimuse koos maksekohustusega."),
    "lv": ("Jūs pērkat digitālu failu (JPEG, 4096 px) un tā izdruku, ko nosūtām uz augstāk norādīto adresi. Jūs piekritāt, ka failu "
           "sākam veidot uzreiz un ka jūsu atteikuma tiesības beidzas, tiklīdz esam sākuši; izdruka tiek izgatavota pēc jūsu pasūtījuma, "
           "un no tās pirkuma atteikties nevar. Nospiežot maksāšanas pogu, jūs veicat pasūtījumu ar pienākumu maksāt."),
}
ITEM_DESC_PRINT = {
    "en": "Made to order from your artwork. Shipped tracked from our print partner's workshop in Europe.",
    "de": "Nach Ihrer Bestellung aus Ihrem Kunstwerk angefertigt. Versand mit Sendungsverfolgung aus der Werkstatt unseres Druckpartners in Europa.",
    "lt": "Gaminamas pagal užsakymą iš Jūsų kūrinio. Siunčiamas su siuntos sekimu iš mūsų spaudos partnerio dirbtuvių Europoje.",
    "hu": "A megrendelésedre, az alkotásodból készül. Nyomon követhető csomagként küldjük nyomdai partnerünk európai üzeméből.",
    "hr": "Izrađuje se po narudžbi iz vašeg umjetničkog djela. Šalje se s praćenjem pošiljke iz radionice našeg partnera za ispis u Europi.",
    "fi": "Tehdään tilauksesi mukaan taideteoksestasi. Lähetetään seurannalla tulostuskumppanimme työpajasta Euroopasta.",
    "et": "Valmistatakse tellimuse järgi sinu kunstiteosest. Saadetakse jälgitava saadetisena meie trükipartneri töökojast Euroopas.",
    "lv": "Tiek izgatavota pēc pasūtījuma no jūsu mākslas darba. Tiek nosūtīta ar sūtījuma izsekošanu no mūsu drukas partnera darbnīcas Eiropā.",
}
# the description of the artwork's own line item (0) when the order has a print: the file, without the "no print, no frame" of pay.ITEM_DESC
ITEM_DESC_FILE = {
    "en": "The digital file of your artwork: JPEG, 4096 px on the longest side. Your print is the next line.",
    "de": "Die digitale Datei Ihres Kunstwerks: JPEG, 4096 px an der längsten Seite. Ihr Druck ist die nächste Zeile.",
    "lt": "Skaitmeninis Jūsų kūrinio failas: JPEG, ilgoji kraštinė 4096 px. Spaudinys nurodytas kitoje eilutėje.",
    "hu": "Az alkotásod digitális fájlja: JPEG, a hosszabbik oldalán 4096 px. A nyomatod a következő sorban van.",
    "hr": "Digitalna datoteka vašeg umjetničkog djela: JPEG, 4096 px na duljoj stranici. Vaš ispis je u sljedećem retku.",
    "fi": "Taideteoksesi digitaalinen tiedosto: JPEG, 4096 px pisimmältä sivulta. Tulosteesi on seuraavalla rivillä.",
    "et": "Sinu kunstiteose digitaalne fail: JPEG, 4096 px pikimal küljel. Sinu trükitud pilt on järgmisel real.",
    "lv": "Jūsu mākslas darba digitālais fails: JPEG, 4096 px garākajā malā. Jūsu izdruka ir nākamajā rindā.",
}
SHIP_LABEL = {"en": "Tracked shipping: {country}", "de": "Versand mit Sendungsverfolgung: {country}", "lt": "Siuntimas su sekimu: {country}",
              "hu": "Nyomon követhető szállítás: {country}", "hr": "Dostava s praćenjem: {country}",
              "fi": "Toimitus seurannalla: {country}",
              "et": "Jälgitav tarne: {country}",
              "lv": "Piegāde ar izsekošanu: {country}"}
SHIP_ADDRESS_NOTE = {"en": "Your print ships to this address ({country}).", "de": "Ihr Druck wird an diese Adresse versandt ({country}).",
                     "lt": "Jūsų spaudinys bus išsiųstas šiuo adresu ({country}).", "hu": "A nyomatodat erre a címre küldjük ({country}).",
                     "hr": "Vaš ispis šaljemo na ovu adresu ({country}).",
                     "fi": "Tulosteesi lähetetään tähän osoitteeseen ({country}).",
                     "et": "Sinu trükitud pilt saadetakse sellele aadressile ({country}).",
                     "lv": "Jūsu izdruku nosūtīsim uz šo adresi ({country})."}


def consent_text(version, lang):
    t = PRINT_CONSENT_TEXTS.get(version) if isinstance(version, str) else None
    return t.get(lang_of(lang)) if isinstance(t, dict) else None


def checkout_part(body, spec, now=None):
    """The print of a checkout request, priced by the server, or None for an order of the digital file only. Refusals (nothing is created):
    409 print_unavailable {why: off, not_configured, market, product, country}, 400 print_consent_required, 409 print_price_changed (only
    when the page sent print_shown: what it showed for the print and its shipping is not what would be charged)."""
    want = body.get("print")
    if want in (None, False, ""):
        return None
    if not isinstance(want, dict):
        raise L.ClientError("Send print as {product, country}.")
    why = offer_problem(spec.get("market"))
    p = product(want.get("product"))
    cc = want.get("country").strip().upper() if isinstance(want.get("country"), str) else ""
    if not why and p is None:
        why = "product"
    if not why and shipping(cc, p["id"]) is None:
        why = "country"
    if why:
        raise store.Answer(409, "print_unavailable", "This print cannot be ordered right now. You can order the digital file alone.", False, None, why=why)
    if body.get("consent_print") is not True:
        raise store.Answer(400, "print_consent_required", "Please tick the box about your print.", False)
    ship = shipping(cc, p["id"])
    shown = body.get("print_shown")
    if shown is not None and not (isinstance(shown, int) and not isinstance(shown, bool) and shown == p["price"] + ship):
        raise store.Answer(409, "print_price_changed", "The price of the print has changed. Please look at it again.", True, None,
                           print={"product": p["id"], "country": cc, "price": p["price"], "ship": ship})
    lang = lang_of(spec.get("lang"))
    text = PRINT_CONSENT_TEXT[lang]
    t = time.time() if now is None else now
    return {"product": p["id"], "sku": p["sku"], "kind": p["kind"], "cm": p["cm"], "country": cc, "price": p["price"], "ship": ship,
            "consent": {"version": pay.CONSENT_VERSION, "at": pay.iso(t), "lang": lang, "text": text,
                        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]}}


def total(part):
    return (part["price"] + part["ship"]) if part else 0


def stripe_params(part, lang, item=1):
    """The Stripe parameters a print adds to the Checkout Session: its line item (item 1, after the artwork's line item 0; item 0 in the
    session of a print bought after the artwork, where it is the only one), the address form and the shipping rate."""
    lang = lang_of(lang)
    cc = part["country"]
    country = country_name(cc, lang)
    made, way = production_days(part["product"]), transit_days(cc)      # Stripe's estimate: this print's production and this country's delivery
    lo, hi = made + way[0], made + way[1]
    li = f"line_items[{int(item)}]"
    return [
        (f"{li}[quantity]", "1"),
        (f"{li}[price_data][currency]", PRINT_OFFER["currency"]),
        (f"{li}[price_data][unit_amount]", str(int(part["price"]))),
        (f"{li}[price_data][product_data][name]", product_name(part["product"], lang)),
        (f"{li}[price_data][product_data][description]", ITEM_DESC_PRINT[lang]),
        ("shipping_address_collection[allowed_countries][0]", cc),
        ("shipping_options[0][shipping_rate_data][type]", "fixed_amount"),
        ("shipping_options[0][shipping_rate_data][fixed_amount][amount]", str(int(part["ship"]))),
        ("shipping_options[0][shipping_rate_data][fixed_amount][currency]", PRINT_OFFER["currency"]),
        ("shipping_options[0][shipping_rate_data][display_name]", SHIP_LABEL[lang].format(country=country)),
        ("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][unit]", "business_day"),
        ("shipping_options[0][shipping_rate_data][delivery_estimate][minimum][value]", str(lo)),
        ("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][unit]", "business_day"),
        ("shipping_options[0][shipping_rate_data][delivery_estimate][maximum][value]", str(hi)),
        ("shipping_options[0][shipping_rate_data][tax_behavior]", "unspecified"),
        ("custom_text[shipping_address][message]", SHIP_ADDRESS_NOTE[lang].format(country=country)),
    ]


def metadata(part):
    """The metadata keys of a print (the server writes them; record_paid and abtest.session_ok read them back)."""
    if not part:
        return {}
    return {"print": part["product"], "print_sku": part["sku"], "print_amount": str(int(part["price"])), "ship_amount": str(int(part["ship"])),
            "ship_cc": part["country"]}


def _digits(v):
    return int(v) if isinstance(v, str) and re.fullmatch(r"[0-9]{1,7}", v) else None


def extra_cents(meta):
    """The print and its shipping a session's metadata names (cents), 0 for a session without a print (abtest.session_ok and pay.record_paid
    take it off the session's amount before they compare the artwork's price)."""
    if not isinstance(meta, dict) or not meta.get("print"):
        return 0
    a, b = _digits(meta.get("print_amount")), _digits(meta.get("ship_amount"))
    return (a or 0) + (b or 0)


def _shipping_details(sess):
    ci = sess.get("collected_information") if isinstance(sess.get("collected_information"), dict) else {}
    sd = ci.get("shipping_details") if isinstance(ci.get("shipping_details"), dict) else None
    if sd is None and isinstance(sess.get("shipping_details"), dict):
        sd = sess["shipping_details"]
    return sd


def _clean(v, n):
    return pay.clean_text(v, n) if isinstance(v, str) else ""


def paid_part(sess, rec):
    """The print of a PAID session for paid.json, or None (a session without one). What was priced comes from the metadata the server wrote;
    the consent from order.json's checkout block of this very session; the address from Stripe's shipping details. A missing address or one
    in another country than the priced one is recorded as mismatch (the print is held for the owner, never sent elsewhere)."""
    meta = sess.get("metadata") if isinstance(sess.get("metadata"), dict) else {}
    pid = meta.get("print")
    if not pid:
        return None
    p = product(pid, offered=False)
    out = {"product": str(pid)[:20], "sku": str(meta.get("print_sku") or "")[:40], "country": str(meta.get("ship_cc") or "")[:2],
           "price": _digits(meta.get("print_amount")) or 0, "ship": _digits(meta.get("ship_amount")) or 0}
    if p:
        out.update(kind=p["kind"], cm=p["cm"])
    co = rec.get("checkout") if isinstance(rec, dict) else None
    cp = co.get("print") if isinstance(co, dict) and co.get("session_id") == sess.get("id") and isinstance(co.get("print"), dict) else {}
    c = cp.get("consent") if isinstance(cp.get("consent"), dict) else None
    if c is None and isinstance(meta.get("consent_version"), str):
        lang = (meta.get("lang") if meta.get("lang") in LANGS else "en")
        text = consent_text(meta["consent_version"], lang)
        if text:
            c = {"version": meta["consent_version"], "at": meta.get("consent_at"), "lang": lang, "text": text,
                 "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]}
    out["consent"] = c
    sd = _shipping_details(sess)
    addr = sd.get("address") if isinstance(sd, dict) and isinstance(sd.get("address"), dict) else {}
    out["name"] = _clean((sd or {}).get("name"), 120)
    out["address"] = {"line1": _clean(addr.get("line1"), 120), "line2": _clean(addr.get("line2"), 120), "city": _clean(addr.get("city"), 80),
                      "postal_code": _clean(addr.get("postal_code"), 20), "state": _clean(addr.get("state"), 60),
                      "country": _clean(addr.get("country"), 2).upper()}
    why = []
    if not p or p["sku"] != out["sku"]:
        why.append("product")
    if not out["name"] or not out["address"]["line1"] or not out["address"]["city"] or not out["address"]["postal_code"]:
        why.append("address")
    if out["address"]["country"] != out["country"]:
        why.append("country")
    if c is None:
        why.append("consent")
    if why:
        out["mismatch"] = why
    return out


def paid_print(paid):
    pp = paid.get("print") if isinstance(paid, dict) else None
    return pp if isinstance(pp, dict) and pp.get("product") else None


def pending(order, paid):
    """Does a paid order have a print that was not sent to merchOne yet (and is not held, failed or closed)? One read of print.json; never raises."""
    if not paid_print(paid):
        return False
    try:
        cur = record(order, timeout=5.0)
    except store.StorageError:
        return True
    return (cur or {}).get("state") in (None, "waiting", "creating")


# ----------------------------------------------------------------------------- the e-mails' words
CONF = {
    "en": {"delivery": "the digital file (JPEG, 4096 px on the longest side) on your order page, and the print, shipped to the address you gave on the payment page",
           "file": "Artwork file", "print": "Print", "ship": "Shipping", "address": "Delivery address", "h": "Your print",
           "p1": ("We send your print to production as soon as your file is ready. {time} We email you the tracking link when it ships. Your "
                  "print is made for us by our print partner {producer}."),
           "p2": ("Please check your print when it arrives. If it is damaged in transit or faulty, please write to info@snapeyes.com within 7 "
                  "days if you can, with your order number, a photo of the damage and a photo of the whole print: then we can have it replaced "
                  "fastest. Your statutory rights, including the legal guarantee of two years for defects, apply in full and do not depend on "
                  "that time."),
           "p3": "Before paying, on {at}, you ticked this box about your print:"},
    "de": {"delivery": "die digitale Datei (JPEG, 4096 px an der längsten Seite) auf Ihrer Bestellseite und der Druck, versandt an die Adresse, die Sie auf der Zahlungsseite angegeben haben",
           "file": "Kunstwerk-Datei", "print": "Druck", "ship": "Versand", "address": "Lieferadresse", "h": "Ihr Druck",
           "p1": ("Wir geben Ihren Druck in die Produktion, sobald Ihre Datei fertig ist. {time} Sobald er versandt ist, senden wir Ihnen den "
                  "Link zur Sendungsverfolgung. Ihr Druck wird für uns von unserem Druckpartner {producer} hergestellt."),
           "p2": ("Bitte prüfen Sie Ihren Druck, wenn er ankommt. Ist er auf dem Transport beschädigt worden oder fehlerhaft, schreiben Sie bitte "
                  "möglichst innerhalb von 7 Tagen an info@snapeyes.com, mit Ihrer Bestellnummer, einem Foto des Schadens und einem Foto des "
                  "ganzen Drucks: Dann können wir ihn am schnellsten ersetzen lassen. Ihre gesetzlichen Rechte, auch die gesetzliche "
                  "Gewährleistung von zwei Jahren für Mängel, gelten uneingeschränkt und hängen nicht von dieser Frist ab."),
           "p3": "Vor der Zahlung haben Sie am {at} bei diesem Text zu Ihrem Druck das Häkchen gesetzt:"},
    "lt": {"delivery": "skaitmeninis failas (JPEG, ilgoji kraštinė 4096 px) Jūsų užsakymo puslapyje ir spaudinys, išsiųstas mokėjimo puslapyje nurodytu adresu",
           "file": "Kūrinio failas", "print": "Spaudinys", "ship": "Siuntimas", "address": "Pristatymo adresas", "h": "Jūsų spaudinys",
           "p1": ("Spaudinį perduodame gaminti, kai tik Jūsų failas būna paruoštas. {time} Kai spaudinys išsiunčiamas, el. paštu atsiunčiame "
                  "siuntos sekimo nuorodą. Spaudinį mums gamina mūsų spaudos partneris {producer}."),
           "p2": ("Gavę spaudinį, jį patikrinkite. Jei jis sugadintas pervežant ar turi trūkumų, jei galite, per 7 dienas parašykite adresu "
                  "info@snapeyes.com, nurodykite užsakymo numerį ir pridėkite pažeidimo nuotrauką bei viso spaudinio nuotrauką: tada greičiausiai "
                  "pasirūpinsime jo pakeitimu. Jūsų įstatyminės teisės, įskaitant dvejų metų įstatyminę garantiją dėl trūkumų, galioja visa "
                  "apimtimi ir nuo šio termino nepriklauso."),
           "p3": "Prieš mokėdami, {at}, pažymėjote šį langelį apie savo spaudinį:"},
    "hu": {"delivery": "digitális fájl (JPEG, a hosszabbik oldalán 4096 px) a rendelési oldaladon, valamint a nyomat, amelyet a fizetési oldalon megadott címre küldünk",
           "file": "Az alkotás fájlja", "print": "Nyomat", "ship": "Szállítás", "address": "Szállítási cím", "h": "A nyomatod",
           "p1": ("A nyomatot azonnal gyártásba adjuk, amint elkészült a fájlod. {time} Amikor elküldték, e-mailben megküldjük a csomagkövetési"
                  " linket. A nyomatot nyomdai partnerünk, a {producer} készíti nekünk."),
           "p2": ("Kérjük, nézd meg a nyomatot, amikor megérkezik. Ha szállítás közben megsérült vagy hibás, lehetőleg 7 napon belül írj az "
                  "info@snapeyes.com címre a rendelésszámmal, a sérülésről és a teljes nyomatról készült fotóval: így tudjuk a leggyorsabban "
                  "kicseréltetni. A törvényes jogaid, köztük a hibákra vonatkozó kétéves kellékszavatosság, teljes körűen megilletnek, és "
                  "nem függnek ettől a határidőtől."),
           "p3": "Fizetés előtt, {at}, ezt a négyzetet jelölted be a nyomatodról:"},
    "hr": {"delivery": "digitalna datoteka (JPEG, 4096 px na duljoj stranici) na stranici vaše narudžbe i ispis, poslan na adresu koju ste naveli na stranici za plaćanje",
           "file": "Datoteka djela", "print": "Ispis", "ship": "Dostava", "address": "Adresa za dostavu", "h": "Vaš ispis",
           "p1": ("Vaš ispis predajemo u izradu čim je vaša datoteka gotova. {time} Kad ga pošaljemo, e-poštom vam šaljemo poveznicu za "
                  "praćenje pošiljke. Vaš ispis za nas izrađuje naš partner za ispis {producer}."),
           "p2": ("Pregledajte ispis kad stigne. Ako je oštećen u prijevozu ili neispravan, ako možete, pišite nam u roku od 7 dana na "
                  "info@snapeyes.com s brojem narudžbe, fotografijom oštećenja i fotografijom cijelog ispisa: tada ga najbrže možemo zamijeniti. "
                  "Vaša zakonska prava, uključujući zakonsko jamstvo od dvije godine za nedostatke, vrijede u cijelosti i ne ovise o tom roku."),
           "p3": "Prije plaćanja, {at}, označili ste ovu kućicu o svojem ispisu:"},
    "fi": {"delivery": "digitaalinen tiedosto (JPEG, 4096 px pisimmältä sivulta) tilaussivullasi ja tuloste, joka lähetetään maksusivulla antamaasi osoitteeseen",
           "file": "Taideteoksen tiedosto", "print": "Tuloste", "ship": "Toimitus", "address": "Toimitusosoite", "h": "Tulosteesi",
           "p1": ("Lähetämme tulosteesi tuotantoon heti, kun tiedostosi on valmis. {time} Lähetämme seurantalinkin sähköpostiisi, kun tuloste "
                  "lähtee matkaan. Tulosteesi tekee meille tulostuskumppanimme {producer}."),
           "p2": ("Tarkista tulosteesi, kun se saapuu. Jos se on vahingoittunut kuljetuksessa tai siinä on virhe, kirjoita mahdollisuuksien "
                  "mukaan 7 päivän kuluessa osoitteeseen info@snapeyes.com ja liitä mukaan tilausnumerosi, kuva vauriosta ja kuva koko "
                  "tulosteesta: silloin saamme sen vaihdettua nopeimmin. Lakisääteiset oikeutesi, myös kahden vuoden lakisääteinen "
                  "virhevastuu, ovat voimassa täysimääräisinä eivätkä riipu tästä ajasta."),
           "p3": "Ennen maksamista, {at}, rastitit tämän tulostettasi koskevan ruudun:"},
    "et": {"delivery": "digitaalne fail (JPEG, 4096 px pikimal küljel) sinu tellimuse lehel ja trükitud pilt, mis saadetakse makselehel antud aadressile",
           "file": "Kunstiteose fail", "print": "Trükitud pilt", "ship": "Tarne", "address": "Tarneaadress", "h": "Sinu trükitud pilt",
           "p1": ("Saadame sinu trükitud pildi tootmisse kohe, kui sinu fail on valmis. {time} Kui see teele läheb, saadame sulle e-kirjaga "
                  "jälgimislingi. Sinu trükitud pildi valmistab meile meie trükipartner {producer}."),
           "p2": ("Palun kontrolli oma trükitud pilti, kui see saabub. Kui see on transpordil kahjustada saanud või puudusega, kirjuta palun "
                  "võimaluse korral 7 päeva jooksul aadressile info@snapeyes.com ning lisa oma tellimuse number, foto kahjustusest ja foto "
                  "kogu trükitud pildist: nii saame selle kõige kiiremini välja vahetada. Sinu seadusest tulenevad õigused, sealhulgas "
                  "seadusest tulenev kaheaastane vastutus puuduste eest, kehtivad täies ulatuses ega sõltu sellest tähtajast."),
           "p3": "Enne maksmist ({at}) märkisid oma trükitud pildi kohta selle kasti:"},
    "lv": {"delivery": "digitālais fails (JPEG, 4096 px garākajā malā) jūsu pasūtījuma lapā un izdruka, ko nosūtām uz adresi, kuru norādījāt maksājuma lapā",
           "file": "Mākslas darba fails", "print": "Izdruka", "ship": "Piegāde", "address": "Piegādes adrese", "h": "Jūsu izdruka",
           "p1": ("Jūsu izdruku nodosim ražošanā, tiklīdz jūsu fails būs gatavs. {time} Kad izdruka būs izsūtīta, nosūtīsim jums e-pastā "
                  "izsekošanas saiti. Jūsu izdruku mums izgatavo mūsu drukas partneris {producer}."),
           "p2": ("Lūdzu, pārbaudiet izdruku, kad tā pienāk. Ja tā ir bojāta pārvadāšanas laikā vai ar trūkumiem, lūdzu, ja iespējams, 7 "
                  "dienu laikā rakstiet uz info@snapeyes.com, norādot pasūtījuma numuru un pievienojot bojājuma fotogrāfiju un visas "
                  "izdrukas fotogrāfiju: tad varēsim to nomainīt visātrāk. Jūsu likumīgās tiesības, tostarp likumā noteiktā divu gadu "
                  "garantija par trūkumiem, ir spēkā pilnībā un nav atkarīgas no šī termiņa."),
           "p3": "Pirms maksāšanas ({at}) jūs atzīmējāt šo rūtiņu par savu izdruku:"},
}
SHIPPED = {
    "en": {"subject": "Your SnapEyes print is on its way", "hello": "Hello,", "line": "your print ({name}) has left the workshop and is on its way to you.",
           "track": "You can follow it here:", "number": "Tracking number: {number}", "order": "Order: {order}",
           "check": ("Please check it when it arrives. If it is damaged or faulty, please write to us within 7 days if you can, with a photo of "
                     "the damage and one of the whole print: then we can have it replaced fastest. Your statutory rights are not affected."),
           "bye": "Kind regards\nSnapEyes"},
    "de": {"subject": "Ihr SnapEyes-Druck ist unterwegs", "hello": "Guten Tag,", "line": "Ihr Druck ({name}) hat die Werkstatt verlassen und ist auf dem Weg zu Ihnen.",
           "track": "Hier können Sie die Sendung verfolgen:", "number": "Sendungsnummer: {number}", "order": "Bestellung: {order}",
           "check": ("Bitte prüfen Sie ihn, wenn er ankommt. Ist er beschädigt oder fehlerhaft, schreiben Sie uns bitte möglichst innerhalb von "
                     "7 Tagen, mit einem Foto des Schadens und einem des ganzen Drucks: Dann können wir ihn am schnellsten ersetzen lassen. Ihre "
                     "gesetzlichen Rechte bleiben unberührt."),
           "bye": "Mit freundlichen Grüßen\nSnapEyes"},
    "lt": {"subject": "Jūsų SnapEyes spaudinys jau keliauja", "hello": "Laba diena,", "line": "Jūsų spaudinys ({name}) išsiųstas ir keliauja pas Jus.",
           "track": "Siuntą galite sekti čia:", "number": "Siuntos numeris: {number}", "order": "Užsakymas: {order}",
           "check": ("Gavę jį patikrinkite. Jei jis sugadintas ar turi trūkumų, jei galite, per 7 dienas mums parašykite ir pridėkite pažeidimo "
                     "nuotrauką bei viso spaudinio nuotrauką: tada greičiausiai pasirūpinsime jo pakeitimu. Jūsų įstatyminės teisės dėl to "
                     "nesumažėja."),
           "bye": "Pagarbiai\nSnapEyes"},
    "hu": {"subject": "Úton van a SnapEyes nyomatod", "hello": "Szia!", "line": "A nyomatod ({name}) elhagyta a műhelyt, és úton van hozzád.",
           "track": "Itt követheted:", "number": "Csomagszám: {number}", "order": "Rendelés: {order}",
           "check": ("Kérjük, nézd meg, amikor megérkezik. Ha sérült vagy hibás, lehetőleg 7 napon belül írj nekünk egy fotóval a sérülésről és "
                     "egy fotóval a teljes nyomatról: így tudjuk a leggyorsabban kicseréltetni. A törvényes jogaidat ez nem érinti."),
           "bye": "Üdvözlettel:\nSnapEyes"},
    "hr": {"subject": "Vaš SnapEyes ispis je na putu", "hello": "Poštovani,", "line": "vaš ispis ({name}) napustio je radionicu i na putu je do vas.",
           "track": "Pošiljku možete pratiti ovdje:", "number": "Broj pošiljke: {number}", "order": "Narudžba: {order}",
           "check": ("Pregledajte ga kad stigne. Ako je oštećen ili neispravan, ako možete, pišite nam u roku od 7 dana s fotografijom oštećenja i "
                     "fotografijom cijelog ispisa: tada ga najbrže možemo zamijeniti. Vaša zakonska prava time nisu ograničena."),
           "bye": "Srdačan pozdrav,\nSnapEyes"},
    "fi": {"subject": "SnapEyes-tulosteesi on matkalla", "hello": "Hei,", "line": "tulosteesi ({name}) on lähtenyt työpajasta ja on matkalla luoksesi.",
           "track": "Voit seurata sitä täällä:", "number": "Seurantanumero: {number}", "order": "Tilaus: {order}",
           "check": ("Tarkista se, kun se saapuu. Jos se on vahingoittunut tai siinä on virhe, kirjoita meille mahdollisuuksien mukaan 7 päivän "
                     "kuluessa ja liitä mukaan kuva vauriosta ja kuva koko tulosteesta: silloin saamme sen vaihdettua nopeimmin. Tämä ei "
                     "vaikuta lakisääteisiin oikeuksiisi."),
           "bye": "Ystävällisin terveisin\nSnapEyes"},
    "et": {"subject": "Sinu SnapEyesi trükitud pilt on teel", "hello": "Tere!", "line": "Sinu trükitud pilt ({name}) on töökojast lahkunud ja on teel sinu juurde.",
           "track": "Saad seda jälgida siin:", "number": "Saadetise number: {number}", "order": "Tellimus: {order}",
           "check": ("Palun kontrolli seda, kui see saabub. Kui see on kahjustatud või puudusega, kirjuta meile palun võimaluse korral 7 päeva "
                     "jooksul ning lisa foto kahjustusest ja foto kogu trükitud pildist: nii saame selle kõige kiiremini välja vahetada. See "
                     "ei mõjuta sinu seadusest tulenevaid õigusi."),
           "bye": "Parimate soovidega\nSnapEyes"},
    "lv": {"subject": "Jūsu SnapEyes izdruka ir ceļā", "hello": "Labdien!", "line": "Jūsu izdruka ({name}) ir izsūtīta no darbnīcas un ir ceļā pie jums.",
           "track": "Tai varat sekot šeit:", "number": "Sūtījuma numurs: {number}", "order": "Pasūtījums: {order}",
           "check": ("Lūdzu, pārbaudiet to, kad tā pienāk. Ja tā ir bojāta vai ar trūkumiem, lūdzu, ja iespējams, 7 dienu laikā rakstiet "
                     "mums, pievienojot bojājuma fotogrāfiju un visas izdrukas fotogrāfiju: tad varēsim to nomainīt visātrāk. Tas "
                     "neietekmē jūsu likumīgās tiesības."),
           "bye": "Ar cieņu\nSnapEyes"},
}


def address_text(pp):
    a = pp.get("address") or {}
    city = " ".join(x for x in (a.get("postal_code"), a.get("city")) if x)
    return ", ".join(x for x in (pp.get("name"), a.get("line1"), a.get("line2"), city) if x)


def amend_confirmation(blocks, lang, paid):
    """The order confirmation of an order with a print (pay.confirmation_mail, every language): the delivery row names the print too, rows for
    the file, the print, the shipping and the delivery address stand before the price row (the price is the total), and a section "Your
    print" follows the rows: production and delivery time, the producer, damage in transit, and the print box the customer ticked."""
    pp = paid_print(paid)
    if not pp or isinstance(paid.get("print_addon"), dict):
        # a print bought after the artwork is a contract and a payment of its own with its own confirmation (addon_mail): the artwork's
        # confirmation, sent again later (the admin's copy), stays what the customer got, and its price is never split by that print
        return blocks
    lang = lang_of(lang)
    w = CONF[lang]
    cur = pay.currency_of(paid.get("currency"))
    # the file's own price: the total less the print and its shipping, plus what a gift voucher took off (api/_lib/voucher.py: it applies to the whole total)
    gv = paid.get("voucher") if isinstance(paid.get("voucher"), dict) else {}
    art = int(paid.get("amount_total") or 0) + int(gv.get("discount") or 0) - int(pp.get("price") or 0) - int(pp.get("ship") or 0)
    out = []
    for b in blocks:
        if b and b[0] == "rows" and isinstance(b[1], list) and len(b[1]) >= 3 and not any(r[0] == w["print"] for r in b[1]):
            rows = b[1]
            rows[-3] = (rows[-3][0], w["delivery"])
            extra = [(w["file"], pay.price_text(art, lang, cur)),
                     (w["print"], f"{product_name(pp['product'], lang)}, {pay.price_text(pp.get('price') or 0, lang, cur)}"),
                     (w["ship"], f"{country_name(pp.get('country'), lang)}, {pay.price_text(pp.get('ship') or 0, lang, cur)}"),
                     (w["address"], address_text(pp) + (f", {country_name(pp.get('country'), lang)}" if pp.get("country") else ""))]
            rows[-2:-2] = extra
            out.append(b)
            c = pp.get("consent") if isinstance(pp.get("consent"), dict) else None
            out += [("h", w["h"]), ("p", w["p1"].format(time=time_text(pp.get("product"), pp.get("country"), lang), producer=f"{PRODUCER}, {PRODUCER_COUNTRY[lang]}")), ("p", w["p2"])]
            if c and c.get("text"):
                at = pay.when_text(c.get("at"), lang) if isinstance(c.get("at"), str) else ""
                out += [("p", w["p3"].format(at=at)), ("quote", pay.quoted(c["text"], lang))]
            continue
        out.append(b)
    return out


# ----------------------------------------------------------------------------- the record of one print
def _path(order, name):
    return pay.order_path(order, name)


def record(order, timeout=6.0):
    r = store.get_json(_path(order, "print.json"), timeout=timeout)
    return r if isinstance(r, dict) else None


# how far a print has come: a write never moves it back (a stale copy in one invocation cannot undo what another recorded); only the owner's
# retry (back=True) starts a failed, held or cancelled print again
RANK = {"waiting": 0, "creating": 0, "held": 0, "failed": 0, "canceled_partner": 0, "created": 1, "shipped": 2, "canceled": 2}


def _write(order, rec, back=False, **kw):
    """print.json, written on top of what is stored NOW (re-read: never a blind write of the caller's copy), with kw merged in. A state that
    would go back (created to waiting, shipped to anything else) is not written unless back (the owner's retry); the other fields are."""
    now = int(time.time())
    try:
        fresh = record(order)
    except store.StorageError:
        fresh = None
    base = fresh if isinstance(fresh, dict) else rec
    want = kw.get("state")
    have = base.get("state")
    if want and want != have and have in RANK and (have == "shipped" or (RANK.get(want, 0) < RANK[have] and not back)):
        pay.log(f"order {order}: print state {have} kept (a write wanted {want})")
        kw = {k: v for k, v in kw.items() if k not in ("state", "error", "why")}
        want = None
    hist = list(base.get("history") or [])[-11:]
    if want and want != have:
        hist.append({"t": now, "state": want, "why": str(kw.get("why") or kw.get("error") or "")[:160]})
    new = dict(base, **kw, history=hist, updated=now, updated_iso=pay.iso(now))
    new.pop("why", None)
    store.put(_path(order, "print.json"), store.json_bytes(new), "application/json", upsert=True, timeout=8.0)
    return new


def index(order, t=None):
    try:
        store.put(f"{INDEX}/{store.check_order(order)}.json", store.json_bytes({"t": int(t or time.time())}), "application/json",
                  upsert=True, timeout=6.0)
    except store.StorageError as e:
        pay.log(f"order {order}: print index not written: {e}")


def unindex(order):
    try:
        store.delete(f"{INDEX}/{store.check_order(order)}.json", timeout=6.0)
    except store.StorageError as e:
        pay.log(f"order {order}: print index not removed: {e}")


def on_paid(order, paid):
    """pay.record_paid of a new paid record with a print: print.json (waiting) and the index, and the owner told when it is held. Never raises."""
    pp = paid_print(paid)
    if not pp:
        return
    try:
        state = "held" if pp.get("mismatch") else "waiting"
        rec = {"v": 1, "state": state, "attempts": 0, "series": 1, "product": pp["product"], "sku": pp.get("sku"),
               "country": pp.get("country"), "created": pay.iso()}
        try:
            store.put(_path(order, "print.json"), store.json_bytes(dict(rec, history=[{"t": int(time.time()), "state": state,
                      "why": ",".join(pp.get("mismatch") or [])}])), "application/json", upsert=False, timeout=8.0)
        except store.StorageExists:
            return
        index(order)
        if pp.get("mismatch"):
            # how to give the money back depends on where it sits. A print bought after the artwork has a payment of its own: the admin panel's
            # refund of THAT payment is the one the server sees (it cancels the print, _refunded); a refund in the Stripe Dashboard would leave the
            # print "held" here for ever. A print of the artwork's own checkout shares the order's payment, so only the Dashboard can refund a part
            addon = isinstance(paid.get("print_addon"), dict)
            how = (f"refund the print's own payment in the admin page (order {order}, Mokėjimai, \"Spaudinio mokėjimas\": {print_payment(paid) or 'see the order'}): "
                   f"the server sees that refund and cancels the print. Do not refund it in the Stripe Dashboard: the server would not know."
                   if addon else "refund the print in the Stripe Dashboard.")
            _note(order, "print_held", f"SnapEyes: the print of order {order} is held",
                  f"Order {order} was paid with a print ({pp.get('product')}, priced for {pp.get('country')}), but "
                  f"{', '.join(pp['mismatch'])} does not match what was priced (the address Stripe collected, the product, the consent"
                  f"{' or the amount paid' if addon else ''}).\n"
                  f"Nothing is sent to the print partner. Look at it in the admin page (Spaudiniai, order {order}): retry once it is clear, or "
                  f"{how}\n")
    except Exception as e:  # noqa: a print must never cost the payment record
        pay.log(f"order {order}: print record not written: {type(e).__name__} {e}")


def _note(order, kind, subject, text):
    return pay.owner_note(order, kind, subject, text)


# ----------------------------------------------------------------------------- the print file
def _fill_edges(a, pad):
    """The array a (h, w, 3) grown by pad[0..3] (top, bottom, left, right) pixels: the artwork's own edge continued, then softened, so the trim
    and the border of an artwork that is not square read as its background. Only the border strips are blurred and blended (a 60 cm print file
    is 4,000 px a side: full-frame float arrays would take most of a function's memory); the artwork itself is never touched."""
    import numpy as np
    from PIL import Image, ImageFilter
    top, bottom, left, right = pad
    if not any(pad):
        return a
    big = np.pad(a, ((top, bottom), (left, right), (0, 0)), mode="edge")
    h, w = big.shape[:2]
    radius = max(2, int(0.02 * max(h, w)))
    ctx = 3 * radius                        # the blur's reach into the artwork, so a strip blurs as the whole picture would

    def soft(y0, y1, x0, x1):
        """The blurred block [y0:y1, x0:x1] of big, blurred with its context around it (uint8)."""
        cy0, cy1, cx0, cx1 = max(0, y0 - ctx), min(h, y1 + ctx), max(0, x0 - ctx), min(w, x1 + ctx)
        b = np.asarray(Image.fromarray(big[cy0:cy1, cx0:cx1]).filter(ImageFilter.GaussianBlur(radius)))
        return b[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0]

    def blend(y0, y1, x0, x1, weight):
        """big[y0:y1, x0:x1] = big blended with its blur by weight (h, w) in 0..1."""
        if y1 <= y0 or x1 <= x0:
            return
        s = soft(y0, y1, x0, x1).astype(np.float32)
        o = big[y0:y1, x0:x1].astype(np.float32)
        wgt = weight[..., None]
        big[y0:y1, x0:x1] = np.clip(o * (1 - wgt) + s * wgt + 0.5, 0, 255).astype(np.uint8)

    ramp = lambda d: np.clip(d / float(radius), 0.0, 1.0).astype(np.float32)     # 0 at the artwork's edge, 1 a radius away
    if top:
        d = top - np.arange(top, dtype=np.float32)
        blend(0, top, 0, w, np.repeat(ramp(d)[:, None], w, axis=1))
    if bottom:
        d = np.arange(1, bottom + 1, dtype=np.float32)
        blend(h - bottom, h, 0, w, np.repeat(ramp(d)[:, None], w, axis=1))
    rows = h - top - bottom
    if left:
        d = left - np.arange(left, dtype=np.float32)
        blend(top, top + rows, 0, left, np.repeat(ramp(d)[None, :], rows, axis=0))
    if right:
        d = np.arange(1, right + 1, dtype=np.float32)
        blend(top, top + rows, w - right, w, np.repeat(ramp(d)[None, :], rows, axis=0))
    return big


def file_box(sku, master_side):
    """((file w, file h), (design w, design h), dpi) in px of the print file of a SKU for a master whose LONG side is master_side px: the design
    area at the resolution the master allows (at least merchOne's minimum, at most PRINT_DPI; reckoned on the area's longer side, so nothing is
    ever enlarged), the print file is the design area plus the trim on every side. A print area that is not square (the keyring's 56 x 76 mm)
    keeps its shape."""
    s = sku_rec(sku)
    dmm, fmm, least = [float(x) for x in s["design_mm"][:2]], [float(x) for x in s["file_mm"][:2]], int(s["dpi"]) or 72
    dpi = max(least, min(PRINT_DPI, int(master_side / (max(dmm) / 25.4))))
    design = tuple(int(round(x / 25.4 * dpi)) for x in dmm)
    filepx = []
    for d, x in zip(design, fmm):
        f = max(d, int(round(x / 25.4 * dpi)))
        filepx.append(f + 1 if (f - d) % 2 else f)
    return tuple(filepx), design, dpi


def file_geometry(sku, master_side):
    """(file_px, design_px, dpi) of a SKU whose print area is square (every print but the keyring): file_box, one side."""
    filepx, design, dpi = file_box(sku, master_side)
    return filepx[0], design[0], dpi


def make_print_file(raw, sku):
    """(jpeg bytes, info) of the print file for a SKU from the delivered master's bytes."""
    import numpy as np
    from PIL import Image
    im = Image.open(io.BytesIO(raw))
    im.load()
    im = im.convert("RGB")
    w, h = im.size
    (fw, fh), (dw, dh), dpi = file_box(sku, max(w, h))
    k = min(dw / w, dh / h)              # the whole artwork inside the design area, never cut (a square print: the design's side over the long side)
    nw, nh = max(1, min(dw, int(round(w * k)))), max(1, min(dh, int(round(h * k))))
    art = np.asarray(im.resize((nw, nh), Image.LANCZOS))
    im.close()
    top = (fh - nh) // 2
    left = (fw - nw) // 2
    out = _fill_edges(art, (top, fh - nh - top, left, fw - nw - left))
    pic = Image.fromarray(out)
    data = store.jpeg_bytes(pic, quality=93)
    return data, {"width": fw, "height": fh, "design": dw, "dpi": dpi, "bytes": len(data), "art": [nw, nh]}


# ----------------------------------------------------------------------------- one try
def _claim(order, gen=0):
    """One try at a time: the lock print_<gen>.lock, created atomically. A lock older than LOCK_STALE (its invocation died) is never deleted to
    take it over (two takers could each delete the other's fresh lock): the taker creates the NEXT generation's lock instead, which only one of
    them can create; print.json records the generation (lock_gen) with the try. Returns (path, id, gen) or None."""
    mine = {"t": round(time.time(), 3), "id": secrets.token_hex(6)}
    for g in (gen, gen + 1, gen + 2):
        path = _path(order, f"print_{g}.lock")
        try:
            store.put(path, store.json_bytes(mine), "application/json", upsert=False, timeout=6.0, retry=False)
            return path, mine["id"], g
        except store.StorageExists:
            pass
        cur = store.get_json(path, timeout=6.0, retry=False)
        try:
            age = time.time() - float(cur.get("t")) if isinstance(cur, dict) else LOCK_STALE + 1
        except (TypeError, ValueError):
            age = LOCK_STALE + 1
        if age < LOCK_STALE:
            return None
    return None


def _release(claim):
    if not claim:
        return
    path, cid = claim[0], claim[1]
    try:
        cur = store.get_json(path, timeout=5.0, retry=False)
        if isinstance(cur, dict) and cur.get("id") == cid:
            store.delete(path, timeout=5.0, retry=False)
    except store.StorageError as e:
        pay.log(f"print claim not released (taken over after {LOCK_STALE} s): {e}")


def _external(order, series):
    return order if int(series or 1) <= 1 else f"{order}-{int(series)}"


def _split_name(name):
    parts = (name or "").split()
    if len(parts) >= 2:
        return " ".join(parts[:-1])[:60], parts[-1][:60]
    return (name or "Customer")[:60], (name or "Customer")[:60]


def payload(order, paid, pp, url, series, is_test):
    a = pp.get("address") or {}
    first, last = _split_name(pp.get("name"))
    ship = {"email": CONTACT, "firstname": first, "lastname": last, "street_primary": a.get("line1") or "", "city": a.get("city") or "",
            "postcode": a.get("postal_code") or "", "country": pp.get("country")}
    if a.get("line2"):
        ship["street_secondary"] = a["line2"]
    ext = _external(order, series)
    return {"external_id": ext, "shipping_type": "tracked", "is_test": bool(is_test), "shipping": ship, "billing": dict(BILLING),
            "items": [{"external_id": f"{ext}-1", "quantity": 1, "product_sku": pp["sku"], "file": {"front": {"url": url}}}]}


def print_payment(paid):
    """The payment intent that paid for the order's print: the add-on's own when the print was bought after the artwork (print_addon, merged
    in by pay.get_paid), else the order's (the print was a line item of the artwork's checkout). None when there is none on record."""
    pa = paid.get("print_addon") if isinstance(paid, dict) else None
    pi = pa.get("payment_intent") if isinstance(pa, dict) else (paid.get("payment_intent") if isinstance(paid, dict) else None)
    return pi if isinstance(pi, str) and pi else None


def print_live(paid):
    """Was the print paid LIVE? The add-on's own payment says it for a print bought after the artwork, else the order's."""
    pa = paid.get("print_addon") if isinstance(paid, dict) else None
    return (pa if isinstance(pa, dict) else paid).get("livemode") is True


def _refunded(order, paid):
    """Was the payment that paid for the print refunded? A print of the artwork's own checkout: the order's refund marks (refunded.json, or
    the admin's refund of the order's payment). A print bought after the artwork has a payment of its own: only the admin's refund of THAT
    payment counts, so a refund of the artwork's payment alone (and refunded.json, which marks that one) leaves the print alone."""
    from . import maker
    if isinstance(paid.get("print_addon"), dict):
        pi = print_payment(paid)
        marks = [f"{maker.REFUNDS_TOP}/{order}/{hashlib.sha256(pi.encode()).hexdigest()[:16]}.json"] if pi else []
    else:
        marks = maker.refund_marks(order, paid)
    return any(store.exists(p, timeout=5.0, retry=False) for p in marks)


def due(order, paid, f=None):
    """Why the print of a paid order is not to be sent now ("" when it is): the artwork is not delivered (or waits for the owner's look),
    the order is withdrawn, deleted, refunded or a test payment where those do not count."""
    if not paid_print(paid):
        return "none"
    if not pay.paid_counts(paid):
        return "test_payment"
    folder = f"orders/{order}"
    if f is None:
        r = pay.parallel([lambda: store.get_json(f"{folder}/delivery.json", timeout=6.0), lambda: store.exists(f"{folder}/release.json", timeout=6.0),
                          lambda: store.exists(f"{folder}/withdrawn.json", timeout=6.0), lambda: store.exists(f"{folder}/deleted.json", timeout=6.0),
                          lambda: store.exists(f"{folder}/expired.json", timeout=6.0)])
        f = {"delivery": r[0], "released": bool(r[1]), "withdrawn": bool(r[2]), "deleted": bool(r[3]) or bool(r[4])}
    if f.get("withdrawn"):
        return "withdrawn"
    if f.get("deleted"):
        return "deleted"
    dl = f.get("delivery")
    if not isinstance(dl, dict) or not dl.get("key"):
        return "not_ready"
    if dl.get("needs_review") and not f.get("released"):
        return "review"
    if _refunded(order, paid):
        return "refunded"
    return ""


def step(order, rec, paid, f=None, by="server", force=False):
    """Send the print of a paid order to merchOne when it is due (see the module). Returns "none" (no print), "done" (merchOne has it, or it
    is closed), "created" (sent now), "wait" (not due yet, or a try is on it), "transient" (merchOne or the storage was busy: a later step
    tries again), "held" or "failed" (the owner is told and the admin page shows why). force: the admin's retry of a failed or held print.
    Never raises."""
    try:
        return _step(order, rec, paid, f, by, force)
    except Exception as e:  # noqa: the artwork and its e-mails never depend on the print
        pay.log(f"order {order}: print step error {type(e).__name__}: {pay.scrub(str(e))[:200]}")
        return "transient"


def _step(order, rec, paid, f, by, force):
    pp = paid_print(paid)
    if not pp:
        return "none"
    cur = record(order)
    if cur is None:
        on_paid(order, paid)
        cur = record(order) or {"state": "waiting", "attempts": 0, "series": 1}
    state = cur.get("state")
    if state in ("created", "shipped"):
        return "done"
    if state in ("held", "failed", "canceled_partner", "canceled") and not force:
        return "done" if state == "canceled" else state
    why = due(order, paid, f)
    if why in ("withdrawn", "deleted", "refunded"):
        _write(order, cur, state="canceled", why=why)
        unindex(order)
        return "done"
    if why:
        return "wait"
    if pp.get("mismatch") and not force:
        return "held"
    if print_live(paid) and not M.live():
        # a LIVE payment and this deployment sends test orders (MERCHONE_LIVE is not set): never a test order for a paid print. Held for the owner
        if cur.get("error") != "not_live":
            _write(order, cur, state="held", error="not_live", why="MERCHONE_LIVE is not set")
            _note(order, "print_not_live", f"SnapEyes: the print of order {order} is held: MERCHONE_LIVE is not set",
                  f"Order {order} was paid LIVE with a print, but this deployment sends only TEST orders to merchOne (MERCHONE_LIVE is not set), "
                  f"and a paid print is never sent as a test order.\nSet MERCHONE_LIVE=1 in Vercel (Production), redeploy, then press Retry in the "
                  f"admin page (Spaudiniai, order {order}).\n")
        return "held"
    if not M.configured():
        if cur.get("error") != "not_configured":
            _write(order, cur, state="waiting", error="not_configured")
            _note(order, "print_not_configured", f"SnapEyes: the print of order {order} waits: merchOne is not configured",
                  f"Order {order} is ready and paid with a print, but MERCHONE_API_USER / MERCHONE_API_KEY are not set on this deployment.\n"
                  f"Set them in Vercel and redeploy; the daily run and the admin page (Spaudiniai) send it then.\n")
        return "wait"
    if L.time_left(99.0) < TIME_NEED:
        return "transient"
    claim = _claim(order, int(cur.get("lock_gen") or 0))
    if claim is None:
        return "wait"
    try:
        cur = record(order) or cur
        if cur.get("state") in ("created", "shipped") or (cur.get("state") != state and not force):
            return "done" if cur.get("state") in ("created", "shipped") else "wait"
        attempts = 1 if force else int(cur.get("attempts") or 0) + 1
        series = int(cur.get("series") or 1)
        if force and cur.get("merchone_id"):
            series += 1              # merchOne's order failed or was cancelled: a new one, under a new external id ("<order>-2")
        cur = _write(order, cur, back=force, state="creating", attempts=attempts, series=series, by=by, lock_gen=claim[2], why=f"try {attempts}")
        dl = (f or {}).get("delivery") if f else None
        if not isinstance(dl, dict):
            dl = store.get_json(f"orders/{order}/delivery.json", timeout=8.0)
        name = f"orders/{order}/print_{pp['product']}.jpg"
        info = cur.get("file") if isinstance(cur.get("file"), dict) and cur["file"].get("path") == name and cur["file"].get("from") == dl.get("key") else None
        if info is None or not store.exists(name, timeout=6.0):
            raw = store.get(dl["key"], timeout=25.0)
            if not raw:
                raise store.StorageError("the delivered artwork could not be read")
            data, info = make_print_file(raw, pp["sku"])
            store.put(name, data, "image/jpeg", upsert=True, timeout=25.0)
            info = dict(info, path=name, sha256=hashlib.sha256(data).hexdigest()[:16], **{"from": dl["key"]})
        url = store.signed_url(name, SIGNED_DAYS * 86400)
        is_test = not print_live(paid)       # a live payment reaches here only with MERCHONE_LIVE on (held above otherwise)
        body = payload(order, paid, pp, url, series, is_test)
        try:
            oid = M.create_order(body)
        except M.Refused as e:
            old = M.existing_id(e)
            if not old:
                raise
            oid = old
            pay.log(f"order {order}: merchOne already had the print order {oid} (external id {body['external_id']}): adopted")
        cur = _write(order, cur, state="created", merchone_id=oid, external_id=body["external_id"], is_test=is_test, file=info, error=None,
                     sent_at=int(time.time()), why=f"merchOne {oid}")
        pay.log(f"order {order}: print {pp['product']} sent to merchOne {oid} ({'TEST' if is_test else 'LIVE'}), {info['width']} px")
        return "created"
    except M.Refused as e:
        msg = pay.scrub(e.message)[:300]
        cur = _write(order, cur, state="failed", error=f"refused {e.status}: {msg}", why="refused")
        _note(order, f"print_failed_{int(cur.get('attempts') or 0)}", f"SnapEyes: merchOne refused the print of order {order}",
              f"Order {order}: merchOne refused the print order ({e.status}): {msg}\nNothing was charged by merchOne for it. Fix the cause "
              f"(the store, the billing, the wallet, the SKU) and press Retry in the admin page (Spaudiniai, order {order}).\n")
        return "failed"
    except (M.Busy, M.NotConfigured, store.StorageError, pay.PayBusy) as e:
        detail = pay.scrub(f"{type(e).__name__}: {e}")[:240]
        attempts = int(cur.get("attempts") or 0)
        if attempts >= MAX_ATTEMPTS:
            _write(order, cur, state="failed", error=detail, why="tries")
            _note(order, "print_failed_tries", f"SnapEyes: the print of order {order} could not be sent",
                  f"Order {order}: {attempts} tries to send the print to merchOne failed (the last: {detail}).\nNothing more is tried by "
                  f"itself. Press Retry in the admin page (Spaudiniai, order {order}) once merchOne answers.\n")
            return "failed"
        _write(order, cur, state="waiting", error=detail, why="busy")
        return "transient"
    finally:
        _release(claim)


# ----------------------------------------------------------------------------- shipping
def _tracking(data):
    """{number, url, carrier, shipped_at} of merchOne's first shipment (a webhook event's data or an order read from the API), or None."""
    ships = []
    if isinstance(data, dict):
        if isinstance(data.get("shipment"), dict):
            ships.append(data["shipment"])
        o = data.get("order") if isinstance(data.get("order"), dict) else data
        ships += [s for s in (o.get("shipments") or []) if isinstance(s, dict)]
    for s in ships:
        url = s.get("tracking_url") if isinstance(s.get("tracking_url"), str) and _TRACK_URL.fullmatch(s["tracking_url"]) else None
        num = str(s.get("tracking_number") or "")[:60]
        if url or num:
            sm = s.get("shipping_method") if isinstance(s.get("shipping_method"), dict) else {}
            return {"number": num or None, "url": url, "carrier": str(sm.get("name") or "")[:60] or None, "shipped_at": str(s.get("shipped_at") or "")[:40] or None}
    return None


def shipped_mail(order, paid, tr):
    """(subject, text, html) of "your print is on its way", in the order's language."""
    lang = lang_of((paid.get("spec") or {}).get("lang"))
    w = SHIPPED[lang]
    pp = paid_print(paid) or {}
    blocks = [("p", w["hello"]), ("p", w["line"].format(name=product_name(pp.get("product"), lang)))]
    if tr.get("url"):
        blocks += [("p", w["track"]), ("link", tr["url"])]
    if tr.get("number"):
        blocks.append(("p", w["number"].format(number=tr["number"]) + (f" ({tr['carrier']})" if tr.get("carrier") else "")))
    blocks += [("p", w["order"].format(order=order)), ("p", w["check"]), ("p", w["bye"]), ("p", pay.seller_lines(lang, pay.legal_pack(quick=True)))]
    text, html_body = pay.render_mail(blocks, lang, w["subject"])
    return w["subject"], text, html_body


def print_email(paid):
    """Where the print's e-mails go: the address of the payment that bought the print (the add-on's own, when the print was bought after the
    artwork and Stripe collected one there), else the order's."""
    pa = paid.get("print_addon") if isinstance(paid, dict) else None
    e = pa.get("email") if isinstance(pa, dict) else None
    return e or (paid.get("email") if isinstance(paid, dict) else None)


def ship_mail(order, paid, tr):
    """The customer's "your print is on its way" e-mail, once (print_mail.json, claimed before sending). Returns "sent", "done" (sent, or being
    sent, before), "off" (no e-mail here or no address), "failed" (Resend refused it) or "transient" (try again later: the claim is given back)."""
    path = _path(order, "print_mail.json")
    try:
        to = print_email(paid)
        if not pay.email_configured() or not to:
            return "off"
        if not pay.claim_once(path):
            return "done"
        subject, text, html_body = shipped_mail(order, paid, tr)
        res = pay.send_mail(to, subject, text, f"snapeyes-print-shipped-{order}", html_body)
        pay._mark(path, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res)
        return res
    except Exception as e:  # noqa: the shipping is recorded all the same; the daily run tries the e-mail again
        pay.log(f"order {order}: print shipped e-mail failed: {type(e).__name__}")
        try:
            pay._mark(path, "retry")
        except Exception:  # noqa
            pass
        return "transient"


def mark_shipped(order, paid, cur, tr, source):
    """The print is on its way: print.json shipped with its tracking and the customer's e-mail once. The order leaves the index only once that
    e-mail is settled (sent, refused or not possible): a transient failure is tried again by the daily run."""
    _write(order, cur, state="shipped", tracking=tr, why=f"shipped ({source})")
    res = ship_mail(order, paid, tr)
    if res != "transient":
        unindex(order)
    pay.log(f"order {order}: print shipped ({source}), e-mail {res}")
    return res


def refresh(order, paid=None, cur=None):
    """Read the merchOne order of a created print back from merchOne (the daily run, the admin page, a webhook): shipped, canceled or failed
    there is recorded. Returns the state."""
    paid = paid or pay.get_paid(order)
    cur = cur or record(order)
    if not paid or not cur or not cur.get("merchone_id"):
        return (cur or {}).get("state") or "none"
    o = M.get_order(cur["merchone_id"])
    if o is None:
        return cur.get("state")
    st = str(o.get("status") or "").upper()
    tr = _tracking(o)
    if tr and cur.get("state") != "shipped":
        mark_shipped(order, paid, cur, tr, "status")
        return "shipped"
    if st in ("CANCELLED", "CANCELED") and cur.get("state") not in ("canceled", "shipped"):
        _write(order, cur, state="canceled_partner", partner_status=st, why="canceled at merchOne")
        _note(order, "print_canceled", f"SnapEyes: merchOne cancelled the print of order {order}",
              f"Order {order}: merchOne says its print order {cur['merchone_id']} is cancelled. The customer paid for a print: make it again "
              f"with Retry in the admin page (Spaudiniai, order {order}) or refund the print in the Stripe Dashboard.\n")
        return "canceled_partner"
    if st in ("ERROR", "FAILED") and cur.get("state") != "failed":
        _write(order, cur, state="failed", partner_status=st, error="failed at merchOne", why="failed at merchOne")
        _note(order, "print_partner_failed", f"SnapEyes: merchOne could not make the print of order {order}",
              f"Order {order}: merchOne reports its print order {cur['merchone_id']} as failed. Look at it in the merchOne dashboard, then "
              f"Retry in the admin page (Spaudiniai, order {order}).\n")
        return "failed"
    if st and st != str(cur.get("partner_status") or ""):
        _write(order, cur, partner_status=st)
    return cur.get("state")


def cancel(order):
    """The admin's cancel of a created print at merchOne (before it is produced). Returns the new state."""
    cur = record(order)
    if not cur or not cur.get("merchone_id"):
        raise store.Answer(409, "no_print_order", "merchOne has no order for this print.", False)
    if cur.get("state") == "shipped":
        raise store.Answer(409, "shipped", "This print is shipped already.", False)
    try:
        M.cancel_order(cur["merchone_id"])
    except M.Refused as e:
        # merchOne cancels during its hold time only (one hour after the order by default, then it is in production), and not in the
        # first seconds while it still reads the order in ("Order cannot be cancelled")
        raise store.Answer(409, "not_cancellable", f"merchOne did not cancel it: {pay.scrub(e.message)[:200]}. In the first minute, try again; after the "
                           "hold time (one hour by default) it is in production.", True, 30) from None
    _write(order, cur, state="canceled", why="canceled by the owner")
    unindex(order)
    return "canceled"


# ----------------------------------------------------------------------------- the webhook
def hook_token():
    """The secret of the webhook's URL (merchOne signs nothing): from the ticket secret, so it needs no variable of its own."""
    return hmac.new(L._ticket_secret(), b"snapeyes-merchone-hook-v1", hashlib.sha256).hexdigest()[:40]


def hook_url():
    return f"{pay.site()}/api/order?hook=merchone&token={hook_token()}"


def _orders_of(o):
    """The orders of ours a merchOne order's external id can name: itself, and without a re-creation's "-2" suffix."""
    ext = str(o.get("external_id") or "") if isinstance(o, dict) else ""
    out = [ext] if store.ORDER_RE.fullmatch(ext) else []
    m = re.fullmatch(r"(.+)-([0-9]{1,2})", ext)
    if m and store.ORDER_RE.fullmatch(m.group(1)):
        out.append(m.group(1))
    return out


def on_hook(event):
    """(status, reply) for one merchOne event whose URL token was right. The event only says which order to look at: its state is read
    back from merchOne's API before anything is recorded (an event with a token that leaked still cannot invent a shipment)."""
    typ = str(event.get("type") or "")[:40] if isinstance(event, dict) else ""
    data = event.get("data") if isinstance(event, dict) and isinstance(event.get("data"), dict) else {}
    o = data.get("order") if isinstance(data.get("order"), dict) else {}
    oid = str(o.get("id") or "")
    if not M.ORDER_ID_RE.fullmatch(oid):
        return 200, {"ok": True, "ignored": "not an order of ours"}
    order, cur = None, None
    for cand in _orders_of(o):
        r = record(cand)
        if isinstance(r, dict) and r.get("merchone_id") == oid:
            order, cur = cand, r
            break
    if not order:
        pay.log(f"merchOne hook {typ}: {oid} is not a print order on record: ignored")
        return 200, {"ok": True, "ignored": "unknown print order"}
    paid = pay.get_paid(order)
    if not paid:
        return 200, {"ok": True, "ignored": "not paid"}
    if typ == "order_commented":
        # the comment's text is not passed on: nothing in the event is verified (merchOne signs nothing), so the note only says where to read it
        _note(order, f"print_comment_{hashlib.sha256(json.dumps(data.get('comment'), sort_keys=True).encode()).hexdigest()[:10]}",
              f"SnapEyes: merchOne commented on the print of order {order}",
              f"merchOne reports a comment on its print order {oid} (order {order}). Read it in the merchOne dashboard (Orders, {oid}).\n")
        return 200, {"ok": True, "order": order, "state": cur.get("state")}
    try:
        state = refresh(order, paid, cur)
    except (M.Busy, M.NotConfigured, store.StorageError) as e:
        pay.log(f"merchOne hook {typ} for {order}: {type(e).__name__}: retried by merchOne")
        return 503, {"ok": False, "reason": "busy"}
    return 200, {"ok": True, "order": order, "state": state}


def serve_hook(req, q):
    """POST /api/order?hook=merchone&token=...: the merchOne webhook (api/order.py routes it here before anything else)."""
    pay.start_clock()
    t0 = time.time()
    try:
        n = int(req.headers.get("content-length") or 0)
    except ValueError:
        n = -1
    if n < 0 or n > (256 << 10):
        store._drain(req)
        return L.send_json(req, 413, {"ok": False, "error": "body too large"})
    raw = req.rfile.read(n) if n else b""
    tok = q.get("token") if isinstance(q.get("token"), str) else ""
    if not hmac.compare_digest(tok.encode("utf-8", "replace"), hook_token().encode("ascii")):
        pay.log("merchOne hook refused: wrong or missing token")
        return L.send_json(req, 403, {"ok": False, "error": "forbidden"})
    try:
        event = json.loads(raw.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return L.send_json(req, 400, {"ok": False, "error": "bad body"})
    try:
        code, out = on_hook(event if isinstance(event, dict) else {})
    except store.StorageNotConfigured:
        code, out = 503, {"ok": False, "reason": "storage_not_configured"}
    except Exception as e:  # noqa: logged, merchOne retries
        pay.log(f"merchOne hook error {type(e).__name__}: {pay.scrub(str(e))[:200]}")
        code, out = 500, {"ok": False, "reason": "error"}
    out["ms"] = int((time.time() - t0) * 1000)
    L.send_json(req, code, out)


# ----------------------------------------------------------------------------- the daily run
def daily(yes, stop_left, say, max_seconds=DAILY_SECONDS):
    """The prints of the index (cleanup/print/): a waiting one that is due is sent (once its artwork is delivered), a created one is read back
    from merchOne (the shipping, when a webhook was lost), a closed one leaves the index. At most DAILY_MAX a run, for at most max_seconds."""
    t0 = time.time()
    out = {"looked": 0, "sent": 0, "shipped": 0, "waiting": 0, "more": False}
    try:
        names = [x.get("name") for x in store.list_all(INDEX)]
    except store.StorageNotConfigured:
        return out
    except store.StorageError as e:
        say(f"prints: index not readable: {e}")
        return out
    orders = [n[:-5] for n in names if isinstance(n, str) and n.endswith(".json") and store.ORDER_RE.fullmatch(n[:-5])]
    recs = {}
    for i in range(0, len(orders), 10):
        if time.time() - t0 > max_seconds / 2 or L.time_left(99.0) < stop_left + TIME_NEED:
            out["more"] = True
            break
        chunk = orders[i:i + 10]
        got = pay.parallel([lambda o=o: _safe_record(o) for o in chunk])
        recs.update(zip(chunk, got))
    # the ones that wait for the owner (held, failed, cancelled at merchOne) stay listed for the admin page but take no turn here; the others
    # go oldest-checked first, so a print never starves behind older ones
    todo = sorted((o for o in recs if (recs[o] or {}).get("state") not in PARKED), key=lambda o: ((recs[o] or {}).get("checked") or 0, o))
    out["parked"] = len(recs) - len(todo)
    for order in todo:
        if out["looked"] >= DAILY_MAX or time.time() - t0 > max_seconds or L.time_left(99.0) < stop_left + TIME_NEED:
            out["more"] = True
            break
        out["looked"] += 1
        if not yes:
            continue
        try:
            paid = pay.get_paid(order)
            cur = recs[order]
            if not paid or not paid_print(paid):
                unindex(order)
                continue
            st = (cur or {}).get("state")
            if st == "shipped":
                # the shipping e-mail did not go out yet (a transient failure): once more; the order leaves the index when it is settled
                if ship_mail(order, paid, cur.get("tracking") or {}) != "transient":
                    unindex(order)
                continue
            if st in FINAL:
                unindex(order)
                continue
            if cur:
                _write(order, cur, checked=int(time.time()))
            if st == "created":
                if cur.get("is_test") is True:
                    unindex(order)          # a test order is never produced or shipped: nothing to read back (the admin can still ask)
                    continue
                if refresh(order, paid, None) == "shipped":
                    out["shipped"] += 1
                continue
            rec = store.get_json(f"orders/{order}/order.json", timeout=6.0)
            r = step(order, rec, paid, by="daily")
            if r == "created":
                out["sent"] += 1
            elif r in ("wait", "transient", "held", "failed"):
                out["waiting"] += 1
        except Exception as e:  # noqa: one order never stops the run
            say(f"prints: order {order}: {type(e).__name__}: {pay.scrub(str(e))[:160]}")
    return out


def _safe_record(order):
    try:
        return record(order, timeout=5.0)
    except store.StorageError:
        return None


# ----------------------------------------------------------------------------- a print bought AFTER the artwork (the add-on)
ADDON = "print_addon"                 # the metadata kind of an add-on's Checkout Session: the webhook and the order page's check know it by this
ADDON_CHECKOUT = "print_checkout.json"
ADDON_PAID = "print_paid.json"
ADDON_MAIL = "print_confirmation.json"
ADDON_TTL = 3600                      # the add-on's payment page stays open an hour (Stripe's minimum is 30 minutes), as a gift voucher's
ADDON_SESSIONS = 3                    # how many of an order's latest add-on sessions a new checkout closes first (as pay.PREVIOUS_SESSIONS)

SUBMIT_NOTE_ADDON = {   # what Stripe shows above its pay button for a print bought after the artwork (the sentences of SUBMIT_NOTE_PRINT without the file's)
    "en": "You are buying a print of your artwork, shipped to the address above. The print is made to your order and cannot be withdrawn from.",
    "de": ("Sie kaufen einen Druck Ihres Kunstwerks, der an die obige Adresse versandt wird. Der Druck wird nach Ihrer Bestellung angefertigt "
           "und ist vom Widerruf ausgeschlossen."),
    "lt": ("Perkate savo kūrinio spaudinį, kuris bus išsiųstas aukščiau nurodytu adresu. Spaudinys gaminamas pagal Jūsų užsakymą, todėl jo "
           "pirkimo atsisakyti negalima. Paspausdami mokėjimo mygtuką, pateikiate užsakymą su prievole sumokėti."),
    "hu": ("Az alkotásod nyomatát vásárolod meg, amelyet a fenti címre küldünk. A nyomat a megrendelésedre készül, ezért attól nem lehet "
           "elállni. A fizetési gombbal fizetési kötelezettséggel járó megrendelést adsz le."),
    "hr": ("Kupujete ispis svojeg umjetničkog djela, koji šaljemo na gornju adresu. Ispis se izrađuje po vašoj narudžbi pa za njega nema "
           "prava na jednostrani raskid. Klikom na gumb za plaćanje dajete narudžbu s obvezom plaćanja."),
    "fi": ("Ostat taideteoksestasi tehdyn tulosteen, joka lähetetään yllä olevaan osoitteeseen. Tuloste tehdään tilauksesi mukaan, eikä sen "
           "ostoa voi peruuttaa. Maksupainiketta painamalla teet tilauksen, ja tilaukseen liittyy maksuvelvollisuus."),
    "et": ("Ostad oma kunstiteosest trükitud pildi, mis saadetakse ülaltoodud aadressile. Trükitud pilt valmistatakse sinu tellimuse järgi "
           "ja selle ostust ei saa taganeda. Maksenupule vajutades esitad tellimuse koos maksekohustusega."),
    "lv": ("Jūs pērkat sava mākslas darba izdruku, ko nosūtām uz augstāk norādīto adresi. Izdruka tiek izgatavota pēc jūsu pasūtījuma, un "
           "no tās pirkuma atteikties nevar. Nospiežot maksāšanas pogu, jūs veicat pasūtījumu ar pienākumu maksāt."),
}
# the add-on's own confirmation e-mail (addon_mail): what CONF and SHIPPED do not say already. The greeting is SHIPPED's, the rows' print,
# shipping and address labels, the damage paragraph (p2) and the sentence before the quoted print box (p3) are CONF's
ADDON_CONF = {
    "en": {"subject": "Your SnapEyes print for order {order}: order confirmation",
           "intro": ("thank you for ordering a print of your artwork. This email confirms that order: a contract of its own, beside the one for "
                     "your digital file. Please keep it."),
           "order": "Order number", "date": "Contract date", "total": "Total",
           "note": "This is the final price: we are not registered for VAT, so no VAT is charged.", "payment": "Payment", "paid": "paid through Stripe",
           "p1": ("Your file is ready, so we send your print to production right away. {time} We email you the tracking link when it ships. "
                  "Your print is made for us by our print partner {producer}."),
           "page": "You can follow your print on your order page:",
           "terms": "Our terms of sale as of {date} apply to this order. Their full text is at the end of this email; you can also read them here:"},
    "de": {"subject": "Ihr SnapEyes-Druck zur Bestellung {order}: Bestellbestätigung",
           "intro": ("vielen Dank für Ihre Bestellung eines Drucks Ihres Kunstwerks. Diese E-Mail bestätigt diese Bestellung: einen eigenen "
                     "Vertrag neben dem über Ihre digitale Datei. Bitte bewahren Sie sie auf."),
           "order": "Bestellnummer", "date": "Vertragsschluss", "total": "Gesamtbetrag",
           "note": "Das ist der Endpreis: Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet.",
           "payment": "Zahlung", "paid": "bezahlt über Stripe",
           "p1": ("Ihre Datei ist fertig, daher geben wir Ihren Druck sofort in die Produktion. {time} Sobald er versandt ist, senden wir Ihnen"
                  " den Link zur Sendungsverfolgung. Ihr Druck wird für uns von unserem Druckpartner {producer} hergestellt."),
           "page": "Auf Ihrer Bestellseite sehen Sie, wie weit Ihr Druck ist:",
           "terms": ("Für diese Bestellung gelten unsere Allgemeinen Geschäftsbedingungen in der Fassung vom {date}. Der vollständige Text "
                     "steht am Ende dieser E-Mail; Sie finden die AGB auch hier:")},
    "lt": {"subject": "Jūsų SnapEyes spaudinys, užsakymas {order}: užsakymo patvirtinimas",
           "intro": ("Dėkojame, kad užsisakėte savo kūrinio spaudinį. Šis el. laiškas patvirtina šį užsakymą: atskirą sutartį šalia sutarties "
                     "dėl Jūsų skaitmeninio failo. Išsaugokite jį."),
           "order": "Užsakymo numeris", "date": "Sutarties sudarymo data", "total": "Iš viso",
           "note": "Tai galutinė kaina: MB „Portretizuokis“ nėra PVM mokėtoja, todėl PVM netaikomas.", "payment": "Mokėjimas", "paid": "apmokėta per Stripe",
           "p1": ("Jūsų failas jau paruoštas, todėl spaudinį perduodame gaminti iš karto. {time} Kai spaudinys išsiunčiamas, el. paštu "
                  "atsiunčiame siuntos sekimo nuorodą. Spaudinį mums gamina mūsų spaudos partneris {producer}."),
           "page": "Spaudinio eigą matysite savo užsakymo puslapyje:",
           "terms": ("Šiam užsakymui taikoma mūsų pardavimo sąlygų redakcija, galiojanti nuo {date}; visas jų tekstas pateiktas šio el. laiško "
                     "pabaigoje, o jas taip pat galite perskaityti čia:")},
    "hu": {"subject": "A SnapEyes-nyomatod a(z) {order} rendeléshez: rendelés-visszaigazolás",
           "intro": ("Köszönjük, hogy megrendelted az alkotásod nyomatát. Ez az e-mail ezt a rendelést igazolja vissza: ez külön szerződés a "
                     "digitális fájlodra vonatkozó mellett. Kérjük, őrizd meg."),
           "order": "Rendelésszám", "date": "A szerződés létrejötte", "total": "Összesen",
           "note": "Ez a végső ár: nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel.", "payment": "Fizetés",
           "paid": "kifizetve a Stripe-on keresztül",
           "p1": ("A fájlod már elkészült, ezért a nyomatot azonnal gyártásba adjuk. {time} Amikor elküldték, e-mailben megküldjük a "
                  "csomagkövetési linket. A nyomatot nyomdai partnerünk, a {producer} készíti nekünk."),
           "page": "A nyomatod állapotát a rendelési oldaladon követheted:",
           "terms": ("Erre a rendelésre az Általános Szerződési Feltételeink {date} napján hatályos változata vonatkozik. A teljes szövegét "
                     "ennek az e-mailnek a végén találod, és itt is elolvashatod:")},
    "hr": {"subject": "Vaš SnapEyes ispis uz narudžbu {order}: potvrda narudžbe",
           "intro": ("hvala vam što ste naručili ispis svojeg umjetničkog djela. Ova e-poruka potvrđuje tu narudžbu: zaseban ugovor uz ugovor "
                     "o vašoj digitalnoj datoteci. Sačuvajte je."),
           "order": "Broj narudžbe", "date": "Datum sklapanja ugovora", "total": "Ukupno",
           "note": "To je konačna cijena: nismo registrirani kao obveznik PDV-a, stoga PDV ne obračunavamo.", "payment": "Plaćanje",
           "paid": "plaćeno putem Stripea",
           "p1": ("Vaša je datoteka gotova, pa vaš ispis odmah predajemo u izradu. {time} Kad ga pošaljemo, e-poštom vam šaljemo poveznicu za "
                  "praćenje pošiljke. Vaš ispis za nas izrađuje naš partner za ispis {producer}."),
           "page": "Svoj ispis možete pratiti na stranici svoje narudžbe:",
           "terms": ("Na ovu narudžbu primjenjuju se naši uvjeti prodaje u verziji od {date}, a njihov cijeli tekst nalazi se na kraju ove "
                     "e-poruke. Možete ih pročitati i ovdje:")},
    "fi": {"subject": "SnapEyes-tulosteesi tilaukseen {order}: tilausvahvistus",
           "intro": ("kiitos, että tilasit tulosteen taideteoksestasi. Tämä viesti vahvistaa tuon tilauksen: se on oma sopimuksensa "
                     "digitaalista tiedostoasi koskevan sopimuksen rinnalla. Säilytä tämä viesti."),
           "order": "Tilausnumero", "date": "Sopimuksen tekoaika", "total": "Yhteensä",
           "note": "Tämä on lopullinen hinta: emme ole arvonlisäverovelvollisia, joten arvonlisäveroa ei peritä.", "payment": "Maksu",
           "paid": "maksettu Stripen kautta",
           "p1": ("Tiedostosi on valmis, joten lähetämme tulosteesi tuotantoon heti. {time} Lähetämme seurantalinkin sähköpostiisi, kun tuloste"
                  " lähtee matkaan. Tulosteesi tekee meille tulostuskumppanimme {producer}."),
           "page": "Voit seurata tulostettasi tilaussivullasi:",
           "terms": ("Tähän tilaukseen sovelletaan myyntiehtojamme sellaisina kuin ne olivat voimassa {date}. Niiden koko teksti on tämän "
                     "viestin lopussa; voit lukea ne myös täältä:")},
    "et": {"subject": "Sinu SnapEyesi trükitud pilt tellimusele {order}: tellimuse kinnitus",
           "intro": ("Aitäh, et tellisid oma kunstiteosest trükitud pildi. See e-kiri kinnitab seda tellimust: see on omaette leping sinu "
                     "digitaalse faili lepingu kõrval. Palun hoia see alles."),
           "order": "Tellimuse number", "date": "Lepingu sõlmimise aeg", "total": "Kokku",
           "note": "See on lõpphind: me ei ole käibemaksukohustuslane, seega käibemaksu ei lisandu.", "payment": "Maksmine",
           "paid": "makstud Stripe’i kaudu",
           "p1": ("Sinu fail on valmis, seega saadame sinu trükitud pildi kohe tootmisse. {time} Kui see teele läheb, saadame sulle e-kirjaga "
                  "jälgimislingi. Sinu trükitud pildi valmistab meile meie trükipartner {producer}."),
           "page": "Oma trükitud pildi käekäiku saad jälgida oma tellimuse lehel:",
           "terms": ("Selle tellimuse suhtes kehtivad meie müügitingimused seisuga {date}. Nende täistekst on selle e-kirja lõpus; võid neid "
                     "lugeda ka siit:")},
    "lv": {"subject": "Jūsu SnapEyes izdruka pasūtījumam {order}: pasūtījuma apstiprinājums",
           "intro": ("Paldies, ka pasūtījāt sava mākslas darba izdruku. Šis e-pasts apstiprina šo pasūtījumu: tas ir atsevišķs līgums līdzās "
                     "līgumam par jūsu digitālo failu. Lūdzu, saglabājiet to."),
           "order": "Pasūtījuma numurs", "date": "Līguma noslēgšanas datums", "total": "Kopā",
           "note": "Tā ir galīgā cena: neesam reģistrēti kā PVN maksātāji, tāpēc PVN netiek pieskaitīts.", "payment": "Maksājums",
           "paid": "samaksāts, izmantojot Stripe",
           "p1": ("Jūsu fails ir gatavs, tāpēc jūsu izdruku nododam ražošanā uzreiz. {time} Kad izdruka būs izsūtīta, nosūtīsim jums e-pastā "
                  "izsekošanas saiti. Jūsu izdruku mums izgatavo mūsu drukas partneris {producer}."),
           "page": "Izdrukas gaitai varat sekot savā pasūtījuma lapā:",
           "terms": ("Šim pasūtījumam piemērojami mūsu pārdošanas noteikumi {date} redakcijā, un pilns to teksts ir šī e-pasta beigās. Tos "
                     "varat izlasīt arī šeit:")},
}


def is_addon_session(sess):
    meta = sess.get("metadata") if isinstance(sess, dict) and isinstance(sess.get("metadata"), dict) else {}
    return isinstance(sess, dict) and sess.get("object") == "checkout.session" and meta.get("kind") == ADDON


def _addon_ours(sess, order, rec):
    """Is this an add-on session the server made for THIS order (the kind, the order id and the fingerprint of its key, all written by the
    server into the metadata)? The same proof as pay.session_ours asks of the order's own session."""
    return is_addon_session(sess) and pay.session_ours(sess, order, rec)


def addon_problem(order, paid, f=None):
    """Why a print cannot be bought for this PAID order now, as a code ("" when it can): not_paid, has_print (it has one, bought at the first
    checkout or after it), not_configured / off / market (offer_problem, for the order's own market), test_payment (a payment that does not
    count here), withdrawn, deleted (also expired), not_ready (no artwork delivered), review (the artwork waits for the owner's look and
    is not released), refunded (the order's payment was refunded: refunded.json or the admin's refund).
    The cheap answers come first (the record, the tables, the environment, the switch's cached state), so while prints are off this reads
    nothing from storage; the order's marks are read only for an order that is otherwise eligible. f: the facts a caller has read already
    ({delivery, released, withdrawn, deleted}, as due() takes them)."""
    if not isinstance(paid, dict) or paid.get("paid") is not True:
        return "not_paid"
    if paid_print(paid):
        return "has_print"
    why = offer_problem(pay.paid_market(paid))
    if why:
        return why
    if not pay.paid_counts(paid):
        return "test_payment"
    folder = f"orders/{order}"
    if f is None:
        r = pay.parallel([lambda: store.get_json(f"{folder}/delivery.json", timeout=6.0), lambda: store.exists(f"{folder}/release.json", timeout=6.0),
                          lambda: store.exists(f"{folder}/withdrawn.json", timeout=6.0), lambda: store.exists(f"{folder}/deleted.json", timeout=6.0),
                          lambda: store.exists(f"{folder}/expired.json", timeout=6.0)])
        f = {"delivery": r[0], "released": bool(r[1]), "withdrawn": bool(r[2]), "deleted": bool(r[3]) or bool(r[4])}
    if f.get("withdrawn"):
        return "withdrawn"
    if f.get("deleted"):
        return "deleted"
    dl = f.get("delivery")
    if not isinstance(dl, dict) or not dl.get("key"):
        return "not_ready"
    if dl.get("needs_review") and not f.get("released"):
        return "review"
    from . import maker
    if any(pay.parallel([lambda p=p: store.exists(p, timeout=5.0, retry=False) for p in maker.refund_marks(order, paid)])):
        return "refunded"
    return ""


def addon_offer(order, paid, f=None):
    """The print offer of the order page (the status reply's print_offer), or None for an order that cannot buy one now (addon_problem):
    {currency, products: [{id, kind, cm, price, ship: {country: cents}}], consent: {lang: the print box's exact text}}: the prices and the
    shipping the server would charge, in euros. Never raises: an offer that cannot be worked out (the storage did not answer) is no offer, and
    the order page is the page it was."""
    try:
        if addon_problem(order, paid, f):
            return None
        info = public_info()
        if not info.get("on"):
            return None
        return {"currency": info["currency"], "products": info["products"], "consent": dict(PRINT_CONSENT_TEXT)}
    except Exception as e:  # noqa: the order's status never depends on the offer
        pay.log(f"order {order}: print offer not worked out: {type(e).__name__}")
        return None


def _addon_checkout(order):
    pc = store.get_json(_path(order, ADDON_CHECKOUT), timeout=8.0)
    return pc if isinstance(pc, dict) else None


def _addon_ids(pc, n=ADDON_SESSIONS):
    """The ids of the order's latest add-on sessions, newest first (as pay.order_sessions reads order.json)."""
    ids = []
    earlier = list(pc.get("sessions") or []) if isinstance(pc, dict) and isinstance(pc.get("sessions"), list) else []
    for sid in [pc.get("session_id") if isinstance(pc, dict) else None] + earlier[::-1]:
        if isinstance(sid, str) and pay.SID_RE.fullmatch(sid) and sid not in ids:
            ids.append(sid)
    return ids[:n]


def _addon_close(order, rec, pc):
    """Before a new add-on session is made, the order's earlier ones must stop being payable, or the customer could pay the old tab AND the new
    one (pay.close_open_sessions does the same for the artwork). Returns (a session the customer has already paid or None, settling)."""
    ids = _addon_ids(pc)
    if not ids:
        return None, False
    found = pay.parallel([lambda s=s: pay.retrieve_session(s) for s in ids])
    paid, settling = None, False
    for sid, sess in zip(ids, found):
        if not _addon_ours(sess, order, rec):
            continue
        if sess.get("status") == "open":
            sess = pay.expire_session(sid)
            gone = isinstance(sess, dict) and sess.get("status") == "expired"
            pay.log(f"order {order}: earlier print checkout {sid} {'expired' if gone else 'was no longer open'}")
            if not _addon_ours(sess, order, rec):
                continue
        if pay.session_paid(sess) and pay.session_counts(sess):
            paid = paid or sess
        elif sess.get("status") == "complete" and pay.session_counts(sess):
            settling = True
    return paid, settling


def _addon_refusal(why):
    """The answer for an order that cannot buy a print now: the offer's own reasons as the first checkout words them (409 print_unavailable),
    the order's reasons as 409 print_not_offered; both carry why and nothing was created."""
    if why in ("not_configured", "off", "market"):
        return store.Answer(409, "print_unavailable", "Prints cannot be ordered right now.", False, None, why=why)
    return store.Answer(409, "print_not_offered", "A print cannot be ordered for this order.", False, None, why=why)


def _already():
    return store.Answer(409, "print_not_offered", "This order has a print already.", False, None, why="has_print")


def addon_buy(body):
    """POST /api/checkout {addon: {order, key}, print: {product, country}, consent_print: true[, print_shown], lang}: the Stripe payment page
    of a print for a delivered order (see the module). {ok, url, order, print {product, country, price, ship}, total, currency, expires_at}.
    Refusals (nothing is created): 403 bad_link, 409 print_not_offered {why} and 409 print_unavailable {why} (addon_problem, and the
    product or the country: checkout_part), 400 print_consent_required, 409 print_price_changed {print} (only with print_shown), and
    409 print_not_offered {why: has_print[, settling]} when an earlier add-on session of the order turns out paid (it is recorded) or is
    settling."""
    why = pay.ordering_problem()
    if why:
        raise pay.PayNotConfigured(why)
    a = body.get("addon") if isinstance(body.get("addon"), dict) else {}
    order, k = a.get("order"), a.get("key")
    rec = pay.load_order(order, k)
    paid = pay.get_paid(order)
    why = addon_problem(order, paid)
    if why:
        raise _addon_refusal(why)
    if not isinstance(body.get("print"), dict):
        raise L.ClientError("Send print as {product, country}.")
    market = pay.paid_market(paid)
    # the language of the page the customer ticked the print box on (the Stripe page and the recorded box are in it); the e-mails stay in the order's
    lang = pay.lang_for(market, body.get("lang"))
    part = checkout_part(body, {"market": market, "lang": lang})
    pc = _addon_checkout(order)
    # one payable add-on session per order: the earlier ones are expired at Stripe first; one that turns out paid is recorded, and the order has its print
    paid_sess, settling = _addon_close(order, rec, pc)
    if paid_sess is not None:
        merged, state = addon_record(order, rec, paid_sess, "checkout")
        addon_after(order, rec, merged, state)
        raise _already()
    if settling:
        raise store.Answer(409, "print_not_offered", "A payment for a print of this order is already being confirmed.", False, None,
                           why="has_print", settling=True)
    now = int(time.time())
    expires = now + ADDON_TTL
    currency = PRINT_OFFER["currency"]
    site = pay.site()
    back = f"{site}/order?o={order}&k={k}&lang={lang}"
    params = [
        ("mode", "payment"),
        # the order page again (its link is the order's key, as in every e-mail): ps names this session, so the page can confirm the payment
        # before Stripe's webhook has arrived (addon_status); print=cancelled is Stripe's back link
        ("success_url", back + "&ps={CHECKOUT_SESSION_ID}"),
        ("cancel_url", back + "&print=cancelled"),
        ("locale", pay.stripe_locale({"lang": lang, "market": market})),
        ("client_reference_id", order),
        ("expires_at", str(expires)),
        ("adaptive_pricing[enabled]", "false"),
        ("custom_text[submit][message]", SUBMIT_NOTE_ADDON[lang]),
        ("payment_intent_data[description]", f"SnapEyes print for order {order}"),
        ("payment_intent_data[metadata][order]", order),
        ("payment_intent_data[metadata][kind]", ADDON),
    ] + stripe_params(part, lang, item=0)
    meta = dict({"kind": ADDON, "order": order, "key_sha": pay.key_sha(k), "lang": lang, "market": market, "currency": currency,
                 "consent_version": part["consent"]["version"], "consent_at": part["consent"]["at"]}, **metadata(part))
    # the Meta Conversions API's identifiers of this visit (api/_lib/meta.py checkout_meta), only while it is configured
    from . import meta as MC
    meta.update(MC.checkout_meta(body))
    params += [(f"metadata[{name}]", v) for name, v in meta.items()]
    r = pay.create_checkout_session(params, f"snapeyes-print-{order}-{secrets.token_hex(8)}", "stripe create print session",
                                    pay.payment_methods(pay.visitor_country(market), currency))
    if r.status_code != 200:
        pay._raise_for(r, "stripe create print session")
    try:
        sess = r.json()
    except ValueError:
        raise pay.PayBusy("stripe create print session: unreadable reply") from None
    sid, url = (sess.get("id"), sess.get("url")) if isinstance(sess, dict) else (None, None)
    if not (isinstance(sid, str) and pay.SID_RE.fullmatch(sid) and isinstance(url, str) and url.startswith("https://")):
        raise pay.PayError("stripe create print session: the reply has no session id or no https url")
    earlier = [s for s in (pc.get("sessions") if isinstance(pc, dict) and isinstance(pc.get("sessions"), list) else []) if isinstance(s, str)]
    store.put(_path(order, ADDON_CHECKOUT), store.json_bytes({
        "v": 1, "order": order, "session_id": sid, "sessions": earlier[-9:] + [sid], "created_at": now, "created": pay.iso(now),
        "amount": total(part), "currency": currency, "market": market, "lang": lang, "expires_at": expires,
        "livemode": bool(sess.get("livemode")), "print": part}), "application/json", upsert=True)
    pay.log(f"order {order}: print checkout {sid} {part['product']} to {part['country']} {part['price']}+{part['ship']} {currency} ({market}) {lang}")
    return {"ok": True, "url": url, "order": order, "print": {x: part[x] for x in ("product", "country", "price", "ship")},
            "total": total(part), "currency": currency.upper(), "expires_at": expires}


def _addon_extra(order, cur, sess, source):
    """A PAID add-on session of an order that has its print already (bought at the first checkout, or by another add-on session): the customer
    paid for a print twice. As pay.extra_payment does for a second payment of the artwork: stored beside the order (extra_payment_<id>.json:
    the admin's order page lists the payment and can refund it), logged, and the owner told to refund it, once. Nothing goes to merchOne."""
    sid = str(sess.get("id") or "")
    tag = hashlib.sha256(sid.encode("utf-8")).hexdigest()[:16]
    meta = sess.get("metadata") if isinstance(sess.get("metadata"), dict) else {}
    pa = cur.get("print_addon") if isinstance(cur.get("print_addon"), dict) else {}
    cd = sess.get("customer_details") if isinstance(sess.get("customer_details"), dict) else {}
    extra = {"paid": False, "extra_payment": True, "kind": ADDON, "session_id": sid, "first_session": pa.get("session_id") or cur.get("session_id"),
             "amount_total": sess.get("amount_total"), "currency": str(sess.get("currency") or "").lower(), "livemode": bool(sess.get("livemode")),
             "payment_intent": sess.get("payment_intent") if isinstance(sess.get("payment_intent"), str) else None,
             "email": cd.get("email") if isinstance(cd.get("email"), str) else None, "paid_iso": pay.iso(), "source": source, "spec": None,
             "print": {"product": str(meta.get("print") or "")[:20], "country": str(meta.get("ship_cc") or "")[:2]}}
    try:
        store.put(pay.order_path(order, f"extra_payment_{tag}.json"), store.json_bytes(extra), "application/json", upsert=False)
    except store.StorageExists:
        return            # recorded and told before (a replayed event, or the page's second check)
    amount = pay.amount_text(extra["amount_total"] or 0, "en", extra["currency"])
    pay.log(f"order {order}: EXTRA PRINT PAYMENT {amount} session {sid} payment {extra['payment_intent']} (the order has its print, "
            f"paid by {extra['first_session']}): REFUND IT")
    pay.owner_note(order, "extra_" + tag[:12], f"SnapEyes: a print for order {order} was paid twice, please refund {amount}",
                   f"Order {order} has its print already (paid by Stripe session {extra['first_session']}).\n"
                   f"A second payment for a print of the same order arrived:\n"
                   f"  amount   {amount} ({'live' if extra['livemode'] else 'TEST mode'})\n"
                   f"  session  {sid}\n  payment  {extra['payment_intent']}\n  customer {extra['email'] or 'no email'}\n"
                   f"  it was for {extra['print']['product']} to {extra['print']['country']}\n"
                   f"Nothing is sent to merchOne for this second payment: the order's print stays as the first payment made it. Please "
                   f"refund the second payment (the admin page's order detail lists it, or the Stripe Dashboard: Payments, search "
                   f"{extra['payment_intent'] or sid}, Refund), and write to the customer if they wanted the other print instead.\n")


def addon_record(order, rec, sess, source, event_id=None):
    """Record a PAID add-on session of this order, once: print_paid.json is created atomically and never overwritten, so a replayed webhook
    or the order page's second check finds it and changes nothing. Returns (the order's paid record with the print merged in, state):
    "new" (recorded now: print.json and the print index were made, on_paid), "known" (this very session was recorded before), "extra"
    (the order had a print already: this payment is stored apart and the owner told to refund it, _addon_extra). The callers check first
    that the session is the order's (_addon_ours), paid and counts here. PayError for an order that is not paid or a session without a print."""
    cur = pay.get_paid(order)
    if cur is None:
        raise pay.PayError(f"order {order}: a print was paid for, but the order itself has no payment on record")
    sid = sess.get("id")

    def again(now_paid):
        pa = now_paid.get("print_addon") if isinstance(now_paid.get("print_addon"), dict) else None
        if pa and pa.get("session_id") == sid:
            return now_paid, "known"
        _addon_extra(order, now_paid, sess, source)
        return now_paid, "extra"

    if paid_print(cur):
        return again(cur)
    pc = _addon_checkout(order)
    pp = paid_part(sess, {"checkout": pc})
    if pp is None:
        raise pay.PayError(f"order {order}: the paid print session names no print")
    amount, currency = sess.get("amount_total"), str(sess.get("currency") or "").lower()
    if amount != pp["price"] + pp["ship"] or currency != PRINT_OFFER["currency"]:
        # only the server makes a session, so this is a price that changed under an open session or a conversion at Stripe: the money is
        # recorded as it came, and the print is held for the owner (never sent on an amount nobody priced)
        pp["mismatch"] = list(pp.get("mismatch") or []) + ["amount"]
        pay.log(f"order {order}: the print was paid {amount} {currency}, priced {pp['price']}+{pp['ship']} {PRINT_OFFER['currency']}: held for the owner")
    meta = sess.get("metadata") if isinstance(sess.get("metadata"), dict) else {}
    cd = sess.get("customer_details") if isinstance(sess.get("customer_details"), dict) else {}
    email = cd.get("email") or sess.get("customer_email") or None
    email = email.strip() if isinstance(email, str) and pay._EMAIL.fullmatch(email.strip()) else None
    now = int(time.time())
    addon = {"paid": True, "kind": ADDON, "order": order, "session_id": sid,
             "payment_intent": sess.get("payment_intent") if isinstance(sess.get("payment_intent"), str) else None,
             "amount_total": amount, "currency": currency, "paid_at": now, "at": pay.iso(now), "livemode": bool(sess.get("livemode")),
             "email": email, "lang": meta.get("lang") if meta.get("lang") in LANGS else None, "source": source,
             "event_id": event_id if isinstance(event_id, str) else None, "print": pp}
    try:
        store.put(_path(order, ADDON_PAID), store.json_bytes(addon), "application/json", upsert=False)
    except store.StorageExists:
        return again(pay.get_paid(order) or cur)
    merged = pay.merge_addon(cur, addon)
    pay.log(f"order {order}: PRINT PAID via {source}: {amount} {currency} {pp['product']} to {pp['country']} live={addon['livemode']}"
            + (f" HELD ({', '.join(pp['mismatch'])})" if pp.get("mismatch") else ""))
    on_paid(order, merged)           # print.json (waiting, or held on a mismatch) and the print index of the daily run
    # the Meta Conversions API's Purchase, once (print_paid.json was made just now), with the event id the order page's pixel sends too
    # (api/_lib/meta.py: nothing in test mode or without the token; never raises)
    from . import meta as MC
    MC.purchase("print", sess, email, amount, currency, f"{pay.site()}/order", MC.country_of(sess, (pp.get("country"),)))
    return merged, "new"


def addon_mail(order, paid, k, pack, docs):
    """(subject, text, html) of the add-on's own confirmation, in the ORDER's language: the print, its shipping, the delivery address, what
    was paid, production and delivery, damage in transit, the print box the customer ticked, the order page (when its link can be built) and
    the terms of sale, in full at the end. The print has no right of withdrawal (made to order), so no withdrawal information goes with it:
    the quoted box and the terms' section on prints say so."""
    lang = lang_of((paid.get("spec") or {}).get("lang"))
    w, c = ADDON_CONF[lang], CONF[lang]
    pp = paid_print(paid) or {}
    pa = paid.get("print_addon") if isinstance(paid.get("print_addon"), dict) else {}
    cur = pay.currency_of(PRINT_OFFER["currency"])
    country = country_name(pp.get("country"), lang)
    rows = [(w["order"], order), (w["date"], pay.when_text(pa.get("at"), lang)),
            (c["print"], f"{product_name(pp.get('product'), lang)}, {pay.price_text(pp.get('price') or 0, lang, cur)}"),
            (c["ship"], f"{country}, {pay.price_text(pp.get('ship') or 0, lang, cur)}"),
            (c["address"], address_text(pp) + (f", {country}" if pp.get("country") else "")),
            (w["total"], f"{pay.price_text(pa.get('amount_total') or 0, lang, cur)}. {w['note']}"),
            (w["payment"], w["paid"])]
    subject = w["subject"].format(order=order)
    blocks = [("p", SHIPPED[lang]["hello"]), ("p", w["intro"]), ("rows", rows),
              ("h", c["h"]), ("p", w["p1"].format(time=time_text(pp.get("product"), pp.get("country"), lang), producer=f"{PRODUCER}, {PRODUCER_COUNTRY[lang]}")), ("p", c["p2"])]
    box = pp.get("consent") if isinstance(pp.get("consent"), dict) else None
    if box and box.get("text"):
        at = pay.when_text(box.get("at"), lang) if isinstance(box.get("at"), str) else ""
        # the box is quoted in the language the customer ticked it in (the order page's at that moment), in this e-mail's quotation marks
        blocks += [("p", c["p3"].format(at=at)), ("quote", pay.quoted(box["text"], lang))]
    if k:
        blocks += [("p", w["page"]), ("link", pay.order_url(order, k, lang))]
    blocks += [("p", w["terms"].format(date=pay.date_text(pack["updated"], lang))), ("link", docs["terms"]["url"]),
               ("p", SHIPPED[lang]["bye"]), ("p", pay.seller_lines(lang, pack)), ("rule",), ("doc", docs["terms"]["text"])]
    text, html_body = pay.render_mail(blocks, lang, subject)
    return subject, text, html_body


def addon_mail_once(order, rec, paid):
    """The add-on's confirmation e-mail, at most once per order (print_confirmation.json, claimed before sending). Returns "sent", "done"
    (sent, refused or being sent before), "off" (no e-mail here), "no_address", "legal_unavailable" (the terms could not be read: nothing
    sent, try again), "transient" (the claim is given back: the webhook's retry or the page's next check sends it) or "failed" / "bad_address"
    (the owner is told to write to the customer). Never raises: the print itself never waits for this e-mail (it is made to order whether or
    not the confirmation went out; the confirmation is owed by the delivery, which is days away)."""
    path = _path(order, ADDON_MAIL)
    try:
        if not pay.email_configured():
            return "off"
        to = print_email(paid)
        if not to:
            res = "no_address"
        else:
            lang, market = (paid.get("spec") or {}).get("lang"), pay.paid_market(paid)
            pack = pay.legal_pack()
            docs = pay.pack_docs(pack, lang, market) if pack else None
            if docs is None:
                pay.log(f"order {order}: print confirmation waits, the legal texts ({pay.LEGAL_PACK_PATH}) could not be read")
                return "legal_unavailable"
            if not pay.claim_once(path):
                return "done"
            subject, text, html_body = addon_mail(order, paid, pay.link_key(order, rec), pack, docs)
            res = pay.send_mail(to, subject, text, f"snapeyes-print-order-{order}", html_body)
            pay._mark(path, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res, legal=pack.get("updated"))
            pay.log(f"order {order}: print confirmation {res}")
        if res in ("failed", "bad_address", "no_address"):
            _note(order, "print_confirmation", f"SnapEyes: the print confirmation of order {order} did not go out",
                  f"A print was bought for order {order} after its artwork, but the customer's confirmation e-mail of that purchase could not "
                  f"be sent ({res}).\nThe print is made all the same. Please write to the customer ({to or 'no email on record: see the payment at Stripe'}) "
                  f"and confirm the purchase: the print, its price and shipping, the delivery address and that it is made to order "
                  f"(admin page, order {order}).\n")
        return res
    except Exception as e:  # noqa: the payment is recorded and the print is made; the next call tries the e-mail again
        pay.log(f"order {order}: print confirmation failed: {type(e).__name__}")
        try:
            pay._mark(path, "retry")
        except Exception:  # noqa
            pass
        return "transient"


def addon_after(order, rec, paid, state):
    """After an add-on payment is on record (the webhook, the order page's check, a checkout that found an earlier session paid): the owner's
    note and the customer's confirmation, each once, and the server's step for the print (the artwork is delivered, so nothing else would ask
    for it before the daily run). Every part is idempotent, so a replayed event repeats nothing. Returns the confirmation's word ("extra" for
    a payment that was stored apart: its only note is the owner's refund note). Never raises."""
    if state == "extra":
        return "extra"
    try:
        pp = paid_print(paid) or {}
        pa = paid.get("print_addon") if isinstance(paid.get("print_addon"), dict) else {}
        cur = PRINT_OFFER["currency"]
        _note(order, "print_addon", f"SnapEyes: a print for order {order}, {pay.amount_text(pa.get('amount_total') or 0, 'en', cur)}",
              f"A print was bought for order {order} after its artwork ({'live' if pa.get('livemode') else 'TEST mode'}).\n"
              f"Print: {pp.get('product')} to {pp.get('country')} ({pay.amount_text(pp.get('price') or 0, 'en', cur)} + shipping "
              f"{pay.amount_text(pp.get('ship') or 0, 'en', cur)}){', HELD: ' + ', '.join(pp['mismatch']) if pp.get('mismatch') else ''}; "
              f"it goes to merchOne now (admin: Spaudiniai)\n"
              f"Customer: {print_email(paid) or 'no email'}\nStripe session: {pa.get('session_id')}\nPayment: {pa.get('payment_intent')}\n")
    except Exception as e:  # noqa: a note never costs the print
        pay.log(f"order {order}: print note failed: {type(e).__name__}")
    mail = addon_mail_once(order, rec, paid)
    try:
        if pending(order, paid):
            from . import maker
            maker.kick(order, why="print")
    except Exception as e:  # noqa: the daily run sends it
        pay.log(f"order {order}: print step not asked for: {type(e).__name__}")
    return mail


def addon_event(obj, event_id=None):
    """(status, reply) for the Stripe webhook's event of an add-on session (api/stripe_webhook.py routes a session of kind "print_addon" here,
    never to the order's own payment path). 503 while the confirmation e-mail must be tried again (Stripe retries; every step is idempotent)."""
    meta = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    order = meta.get("order")
    sid = str(obj.get("id") or "")
    if not isinstance(order, str) or not store.ORDER_RE.fullmatch(order):
        pay.log(f"webhook {event_id}: a print session without an order of ours, ignored")
        return 200, {"ok": True, "print": True, "ignored": "no order"}
    if not pay.session_paid(obj):
        return 200, {"ok": True, "print": True, "order": order, "state": "awaiting_payment"}
    rec = store.get_json(f"orders/{order}/order.json", timeout=8.0)
    if not isinstance(rec, dict) or not _addon_ours(obj, order, rec):
        if not isinstance(rec, dict) and pay.session_counts(obj):
            # a payment for a print of an order this site no longer has: never silent, the owner refunds it
            pay.note_once(f"notes/unknown_print_{pay._order_tag(sid)}.json", "unknown_print",
                          f"SnapEyes: a payment for a print of order {order} arrived, but the order is gone",
                          f"Stripe reports a PAID Checkout Session {sid} ({pay.amount_text(obj.get('amount_total') or 0, 'en', obj.get('currency'))}, "
                          f"{'live' if obj.get('livemode') else 'TEST mode'}) for a print of order {order}, but this site has no record of that "
                          f"order any more.\nNothing can be printed for it. Please refund it in the Stripe Dashboard (Payments, search "
                          f"{obj.get('payment_intent') or sid}, Refund) and write to the customer "
                          f"({(obj.get('customer_details') or {}).get('email') or 'email at Stripe'}).\n")
        pay.log(f"webhook {event_id}: order {order}: the print session does not match the order record, ignored")
        return 200, {"ok": True, "print": True, "ignored": "session does not match"}
    if not pay.session_counts(obj):
        pay.log(f"webhook {event_id}: order {order}: a TEST-mode payment for a print, and this deployment takes no test orders: ignored")
        return 200, {"ok": True, "print": True, "ignored": "test mode"}
    paid, state = addon_record(order, rec, obj, "webhook", event_id)
    mail = addon_after(order, rec, paid, state)
    if mail in ("transient", "legal_unavailable"):
        return 503, {"ok": False, "print": True, "order": order, "reason": "mail_retry"}
    return 200, {"ok": True, "print": True, "order": order, "state": state, "mail": mail}


def addon_status(sid, order, k):
    """GET /api/checkout?addon=<session id>&o=<order>&k=<key>: the order page's question after Stripe's success page, asked until the print is
    on record (the webhook may not have arrived yet; the gift page asks about its voucher the same way). {ok, state}: "paid" (recorded, by the
    webhook or by this very call: with print, the order page's print block), "extra" (the order had a print already: this payment is stored
    apart and refunded by the owner), "pending" (not paid yet), "processing" (completed with a method that settles later), "expired",
    "unknown" (not a print session of this order, or a test payment where those do not count). 403 bad_link for a wrong key."""
    rec = pay.load_order(order, k)
    if not isinstance(sid, str) or not pay.SID_RE.fullmatch(sid):
        raise L.ClientError("This is not a print payment.")
    paid = pay.get_paid(order)
    pa = paid.get("print_addon") if isinstance(paid, dict) and isinstance(paid.get("print_addon"), dict) else None
    if pa and pa.get("session_id") == sid:
        # on record already (the webhook came first): no call to Stripe. The confirmation and the step are asked for again, each a no-op once done
        addon_after(order, rec, paid, "known")
        return {"ok": True, "state": "paid", "print": order_view(order, paid), **_paid_amount(pa)}
    if not pay.stripe_key():
        raise pay.PayNotConfigured("STRIPE_SECRET_KEY is not set")
    sess = pay.retrieve_session(sid)
    if not _addon_ours(sess, order, rec):
        return {"ok": True, "state": "unknown"}
    if not pay.session_paid(sess):
        st = "expired" if sess.get("status") == "expired" else "processing" if sess.get("status") == "complete" else "pending"
        return {"ok": True, "state": st}
    if not pay.session_counts(sess):
        pay.log(f"order {order}: print session {sid} is a TEST payment and this deployment takes none, not recorded")
        return {"ok": True, "state": "unknown"}
    paid, state = addon_record(order, rec, sess, "order_page")
    addon_after(order, rec, paid, state)
    if state == "extra":
        return {"ok": True, "state": "extra", "print": order_view(order, paid)}
    pa = paid.get("print_addon") if isinstance(paid.get("print_addon"), dict) else {}
    return {"ok": True, "state": "paid", "print": order_view(order, paid), **_paid_amount(pa)}


def _paid_amount(pa):
    """What the print's own payment was (amount in cents, currency): the order page's Meta pixel reports it as the Purchase of the print
    (src/shared/metaPixel.ts), with the same event id as the server's (api/_lib/meta.py). Nothing when the record does not say it."""
    amount, currency = pa.get("amount_total"), pa.get("currency")
    if isinstance(amount, int) and isinstance(currency, str) and currency:
        return {"amount": amount, "currency": currency.upper()}
    return {}


# ----------------------------------------------------------------------------- what the pages and the admin see
def order_view(order, paid):
    """The order page's print block: {product, name, country, state, tracking_url} (state: preparing, sent, shipped, canceled)."""
    pp = paid_print(paid)
    if not pp:
        return None
    try:
        cur = record(order, timeout=5.0) or {}
    except store.StorageError:
        cur = {}
    st = cur.get("state") or "waiting"
    view = "shipped" if st == "shipped" else "canceled" if st == "canceled" else "sent" if st == "created" else "preparing"
    tr = cur.get("tracking") if isinstance(cur.get("tracking"), dict) else {}
    return {"product": pp.get("product"), "kind": pp.get("kind"), "cm": pp.get("cm"), "country": pp.get("country"), "state": view,
            "tracking_url": tr.get("url") if view == "shipped" else None}


def admin_view(order, paid):
    """The admin's block of one order: the paid print (no address line beyond the city and country), the record, the margin."""
    pp = paid_print(paid)
    if not pp:
        return None
    cur = record(order) or {}
    a = pp.get("address") or {}
    return {"product": pp.get("product"), "name": product_name(pp.get("product"), "lt"), "country": pp.get("country"), "price": pp.get("price"),
            "ship": pp.get("ship"), "city": a.get("city"), "mismatch": pp.get("mismatch"), "margin": margin(pp.get("product"), pp.get("country")),
            "state": cur.get("state") or "waiting", "attempts": cur.get("attempts"), "merchone_id": cur.get("merchone_id"),
            "external_id": cur.get("external_id"), "is_test": cur.get("is_test"), "error": cur.get("error"),
            "partner_status": cur.get("partner_status"), "tracking": cur.get("tracking"), "file": cur.get("file"),
            "history": cur.get("history"), "updated_iso": cur.get("updated_iso"),
            # bought after the artwork, with a payment of its own (the order detail's payments list has it as its own line)
            "addon": isinstance(paid.get("print_addon"), dict)}


def admin_status(check_api=False):
    """The admin page "Spaudiniai": the switch, the configuration, the webhook URL, the rate table, the offer with its margins, the prints
    in the index. check_api: one cheap call to merchOne (the shipping rate of the first product to Lithuania) to say whether it answers."""
    sw = switch_state(fresh=True)
    api = None
    if check_api and M.configured():
        try:
            p = products()[0]
            M.shipping_rates("LT", "01100", p["sku"], deadline=True)
            api = "ok"
        except M.NotConfigured:
            api = "refused"
        except (M.Busy, M.Refused) as e:
            api = f"error: {type(e).__name__}"
    rows = []
    try:
        names = [x.get("name") for x in store.list_all(INDEX)]
    except store.StorageError:
        names = []
    for name in sorted((n for n in names if isinstance(n, str) and n.endswith(".json")), reverse=True)[:50]:
        order = name[:-5]
        try:
            cur = record(order, timeout=5.0) or {}
        except store.StorageError:
            cur = {}
        rows.append({"order": order, "state": cur.get("state"), "product": cur.get("product"), "country": cur.get("country"),
                     "attempts": cur.get("attempts"), "error": cur.get("error"), "merchone_id": cur.get("merchone_id"),
                     "updated_iso": cur.get("updated_iso")})
    offer = []
    for p in products(offered=False):
        ms = [m for m in (margin(p["id"], cc) for cc in countries()) if m is not None]
        offer.append({"id": p["id"], "name": product_name(p["id"], "lt"), "on": p.get("on") == 1, "price": p["price"], "sku": p["sku"],
                      "cost": (sku_rec(p["sku"]) or {}).get("cost"), "margin_min": min(ms) if ms else None, "margin_max": max(ms) if ms else None,
                      "ship_min": min(shipping(cc, p["id"]) for cc in countries()), "ship_max": max(shipping(cc, p["id"]) for cc in countries())})
    return {"switch": {"on": sw.get("on") is True, "iso": sw.get("iso"), "by": sw.get("by"), "rev": sw.get("rev") or 0,
                       "unreadable": sw.get("why") == "unreadable"},
            "configured": M.configured(), "problem": M.problem(), "live": M.live(), "api": api, "hook_url": hook_url(),
            "rates_fetched": PRINT_RATES.get("fetched"), "countries": len(countries()), "markets": list(markets()), "offer": offer,
            "margin_floor": PRINT_OFFER["margin_floor"], "open": rows}
