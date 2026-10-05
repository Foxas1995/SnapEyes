"""Hungarian ("hu") strings and email texts for api/_lib/pay.py, key for key.

What is here, and where pay.py uses it ("hu" is in LANGS):
  SELLER_HU            SELLER["hu"]            the seller line of the short emails when the legal pack is missing
  CONSENT_TEXT_HU      CONSENT_TEXT["hu"]      word for word src/shared/legal.ts CHECKOUT_LEGAL.hu.withdrawalConsent
  SUBMIT_NOTE_HU       SUBMIT_NOTE["hu"]       Stripe's note above its pay button (custom_text.submit), with the
                                               15. § (2) words „fizetési kötelezettséggel járó megrendelés”
  ITEM_DESC_HU         ITEM_DESC["hu"]         the Stripe line item's description
  item_name_hu()       item_name() for "hu"
  price_text_hu()      price_text() for "hu": "6 990 Ft" (HUF), "19,97 €" (EUR); amount_text_hu() the plain one
  when_text_hu()       when_text() for "hu": "2026. szeptember 29., 10:15 UTC"
  date_text_hu()       date_text() for "hu": "2026. szeptember 29."
  quoted_hu()          quoted() for "hu": „...”
  seller_lines_hu()    seller_lines() for "hu"
  confirmation_hu()    the "hu" branch of confirmation_mail(): (subject, blocks) before the legal texts are appended
  ready_hu()           the "hu" branch of ready_mail(): (subject, blocks)

Tone: friendly "te", as the site and the checkout; the legal texts attached to the confirmation (the ÁSZF and the
Elállási tájékoztató from /legal/order-mail.json) stay in their own "Ön" register.
The confirmation is the durable-medium confirmation of 45/2014. (II. 26.) Korm. rendelet 18. § and 29. § (1) m): it
repeats the consent checkbox word for word and confirms it, before anything is made (as the English one does).
No en or em dashes anywhere (owner rule). Stand-alone on purpose: no import of pay, so it can be reviewed and tested
on its own; pay.py passes in what it has computed.
"""
import calendar
import time
from . import catalogue
from . import words as W

SELLER_HU = "MB „Portretizuokis”, cégazonosító szám: 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Litvánia"

# The withdrawal waiver, word for word as the checkout shows it (src/shared/legal.ts CHECKOUT_LEGAL.hu). Adding it means a new
# CONSENT_VERSION in pay.py AND src/shared/legal.ts together (old versions keep their en/de texts in CONSENT_TEXTS).
CONSENT_TEXT_HU = ("Kifejezetten hozzájárulok ahhoz, hogy a SnapEyes még az elállási határidő lejárta előtt azonnal "
                   "megkezdje a digitális alkotásom elkészítését. Tudomásul veszem, hogy a teljesítés megkezdését "
                   "követően elveszítem az elállási jogomat.")

# Stripe shows this right above its pay button, the click that makes the order binding: so the decree's own words
# (45/2014. Korm. rendelet 15. § (2): „fizetési kötelezettséggel járó megrendelés”) stand at that click too.
SUBMIT_NOTE_HU = ("Digitális fájlt vásárolsz (JPEG, 4096 px). Nyomatot és keretet nem küldünk. Hozzájárultál, hogy "
                  "azonnal elkezdjük, és tudomásul vetted, hogy a kezdéssel megszűnik az elállási jogod. A fizetési "
                  "gombbal fizetési kötelezettséggel járó megrendelést adsz le.")

ITEM_DESC_HU = "Csak digitális fájl: JPEG, a hosszabbik oldalán 4096 px. Nyomat és keret nélkül."

STYLE_NAMES = catalogue.names()      # the brand name of every style id, English in every language (api/_lib/styles_registry.py)

MONTHS_HU = ("január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember",
             "október", "november", "december")

NBSP = " "


def item_name_hu(spec, layout=True):
    """The Stripe line item and the confirmation's "Alkotás" row. A noun stays singular after a number (2 szem). The style is as an order prints it
    (catalogue.style_label: the look is part of it, "Universe, Vortex"); a style of the v3 engine with two or more eyes names its layout after the style
    ("3 szem, Family Colours, Háromszög, 4096 px-es digitális fájl") unless layout is False (the confirmation adds its own "elrendezés: ..." phrase)."""
    n, style = int(spec["eyes"]), catalogue.style_label(spec["style"], int(spec["eyes"]), spec.get("opts"))
    word = ""
    if layout and n > 1 and catalogue.known(spec["style"]) and not catalogue.is_legacy(spec["style"]):
        word = catalogue.layout_name("hu", spec.get("layout"))
    return f"SnapEyes íriszalkotás, {n} szem, {style}{', ' + word if word else ''}, 4096 px-es digitális fájl"


def _group(n):
    """Thousands with a no-break space, also for four digits ("6 990")."""
    return f"{int(n):,}".replace(",", NBSP)


def price_text_hu(minor, currency="huf"):
    """A price as the Hungarian site shows it, in the currency the order was paid in. Stripe sends HUF as a
    two-decimal amount (6 990 Ft = 699000), so HUF is minor / 100 in whole forints: "6 990 Ft". EUR: "19,97 €".
    AUD (a Hungarian-language order on the AUD list, unlikely): "39,00 AUD"."""
    try:
        c = int(minor)
    except (TypeError, ValueError):
        c = 0
    cur = str(currency or "huf").lower()
    if cur == "huf":
        return f"{_group(round(c / 100))}{NBSP}Ft"
    whole, cents = f"{_group(c // 100)}", f"{c % 100:02d}"
    if cur == "eur":
        return f"{whole},{cents}{NBSP}€"
    return f"{whole},{cents}{NBSP}{cur.upper()}"


def amount_text_hu(minor, currency="huf"):
    """The plain amount with the currency code, as amount_text() writes it ("6 990 HUF", "19,97 EUR")."""
    try:
        c = int(minor)
    except (TypeError, ValueError):
        c = 0
    cur = str(currency or "huf").upper()
    if cur == "HUF":
        return f"{_group(round(c / 100))} HUF"
    return f"{_group(c // 100)},{c % 100:02d} {cur}"


def when_text_hu(ts, seconds=False):
    """A moment for a customer: "2026. szeptember 29., 10:15 UTC". ts: unix seconds or an ISO text."""
    if isinstance(ts, str):
        try:
            ts = calendar.timegm(time.strptime(ts.strip()[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return ts
    try:
        g = time.gmtime(float(ts))
    except (TypeError, ValueError, OverflowError):
        return str(ts)
    hm = f"{g.tm_hour:02d}:{g.tm_min:02d}" + (f":{g.tm_sec:02d}" if seconds else "")
    return f"{g.tm_year}. {MONTHS_HU[g.tm_mon - 1]} {g.tm_mday}., {hm} UTC"


def date_text_hu(day_iso):
    """A date for a customer from "YYYY-MM-DD": "2026. szeptember 29." (a sentence adds „napján” / „napjáig”)."""
    try:
        g = time.strptime(str(day_iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(day_iso)
    return f"{g.tm_year}. {MONTHS_HU[g.tm_mon - 1]} {g.tm_mday}."


def quoted_hu(text):
    return f"„{text}”"


def seller_lines_hu(pack=None, contact="info@snapeyes.com"):
    """The seller as a Hungarian email signs: company and code, address, representative and phone when set, email.
    pack: the legal pack (its seller company/address in "hu" once plain.ts LANGS has "hu")."""
    s = (pack or {}).get("seller") if isinstance(pack, dict) else None
    if not isinstance(s, dict) or not isinstance((s.get("company") or {}).get("hu"), str):
        return SELLER_HU.replace(", Gedimino", "\nGedimino") + f"\nE-mail: {contact}"
    out = [f"{s['company']['hu']}, cégazonosító szám: {s['code']}", s["address"]["hu"]]
    if s.get("representative"):
        out.append(f"Képviseli: {s['representative']}")
    if s.get("phone"):
        out.append(f"Telefon: {s['phone']}")
    out.append(f"E-mail: {s.get('email') or contact}")
    return "\n".join(out)


SIGN_OFF_HU = "Üdvözlettel:\nSnapEyes"
QUESTIONS_HU = "Kérdésed van? Egyszerűen válaszolj erre az e-mailre."
GREETING_HU = "Kedves Vásárlónk!"
BUTTON_HU = "Elállás a szerződéstől"          # src/shared/legal.ts WITHDRAWAL_ONLINE.hu.button


def confirmation_hu(*, order, spec, n, layout, price, paid_at, consent_at, consent_text, auto, link, wlink,
                    terms_url, updated_day, seller):
    """The "hu" branch of confirmation_mail(): (subject, blocks). pay.py computes what it computes for English
    (link, wlink, price with price_text_hu, layout as catalogue.layout_name("hu", id) gives it, auto = server_starts(pack), the terms URL and
    the pack's "updated" day, seller = seller_lines_hu(pack)) and then appends the rule and the two legal texts."""
    rows = [("Rendelésszám", order),
            ("A szerződés létrejötte", when_text_hu(paid_at)),
            ("Alkotás", item_name_hu(dict(spec, eyes=n), False) + (f", elrendezés: {layout}" if n > 1 and layout else ""))]
    names = W.names_text(spec.get("names"))
    if names:
        rows.append(("Nevek az alkotáson", names))
    if spec.get("title"):
        rows.append(("Cím az alkotáson", spec["title"]))
    if spec.get("date"):
        rows.append(("Dátum az alkotáson", spec["date"]))
    rows += [("Teljesítés", "digitális fájl (JPEG, a hosszabbik oldalán 4096 px) a rendelési oldaladon; nyomatot és "
                            "keretet nem küldünk"),
             ("Ár", f"{price}. Ez a végső ár: nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem "
                    f"számítunk fel."),
             ("Fizetés", "kifizetve a Stripe-on keresztül")]
    subject = f"A SnapEyes-rendelésed visszaigazolása: {order}"
    blocks = [
        ("p", GREETING_HU),
        ("p", "Köszönjük a rendelésedet. Ez az e-mail visszaigazolja a velünk kötött szerződésedet. Kérjük, őrizd meg: "
              "benne van a rendelésed, az azonnali kezdéshez adott hozzájárulásod, az elállási tájékoztató az "
              "elállásinyilatkozat-mintával, valamint az ÁSZF."),
        ("h", "A rendelési oldalad"),
        ("link", link),
        ("p", ("Az alkotásod elkészítését közvetlenül ennek az e-mailnek az elküldése után megkezdjük; ehhez egyetlen "
               "oldalt sem kell nyitva tartanod. Általában néhány percen belül elkészül: a fájlt a rendelési oldaladon "
               "töltheted le, és e-mailt is küldünk, amikor kész. "
               if auto else
               "Amint megnyitod ezt az oldalt, megkezdjük az alkotásod elkészítését (általában néhány percen belül kész), "
               "és ott töltheted le a fájlt. ") +
              "Kérjük, ezt a linket ne add tovább: aki ismeri, letöltheti az alkotásodat."),
        ("h", "A rendelésed"),
        ("rows", rows),
        ("h", "Hozzájárulásod az azonnali kezdéshez"),
        ("p", f"Fizetés előtt ({when_text_hu(consent_at)}) bejelölted ezt a négyzetet:"),
        ("quote", quoted_hu(consent_text)),
        ("p", "Visszaigazoljuk a kifejezett hozzájárulásodat, és azt, hogy tudomásul vetted a következményét. A fájlod "
              "elkészítését csak ennek az e-mailnek az elküldése után kezdjük meg. A kezdéssel megszűnik az elállási "
              "jogod."),
        ("h", "Az elállási jogod"),
        ("p", "A fájlod elkészítését közvetlenül ennek az e-mailnek az elküldése után megkezdjük, ezért az elállási "
              "jogod általában már néhány pillanattal később megszűnik. Amíg nem kezdtük el, elállhatsz a szerződéstől "
              f"a rendelésed elállási oldalán, az „{BUTTON_HU}” gombbal:"
         if auto else
              f"Amíg nem kezdtük el, elállhatsz a szerződéstől a rendelésed elállási oldalán, az „{BUTTON_HU}” "
              "gombbal. Ez a link úgy nyitja meg az oldalt, hogy nem kezdjük el a fájlod elkészítését (a fenti "
              "rendelési oldal linkjével ellentétben):"),
        ("link", wlink),
        ("p", "E-mailben is elállhatsz az info@snapeyes.com címen, vagy az elállásinyilatkozat-mintával. A teljes "
              "elállási tájékoztatót ennek az e-mailnek az alján találod."),
        ("h", "ÁSZF"),
        ("p", f"A rendelésedre az Általános Szerződési Feltételeink {date_text_hu(updated_day)} napján hatályos "
              f"változata vonatkozik. A teljes szövegét ennek az e-mailnek a végén találod, és itt is elolvashatod:"),
        ("link", terms_url),
        ("p", QUESTIONS_HU),
        ("p", SIGN_OFF_HU),
        ("p", seller),
    ]
    return subject, blocks


def ready_hu(*, order, link, checked, seller):
    """The "hu" branch of ready_mail(): (subject, blocks)."""
    subject = "Elkészült a SnapEyes-alkotásod"
    blocks = [("p", GREETING_HU),
              ("p", ("Az íriszalkotásod elkészült, és ellenőriztük." if checked else "Az íriszalkotásod elkészült.") +
                    " A rendelési oldaladon töltheted le:"),
              ("link", link), ("p", f"Rendelés: {order}"), ("p", QUESTIONS_HU),
              ("p", SIGN_OFF_HU), ("p", seller)]
    return subject, blocks
