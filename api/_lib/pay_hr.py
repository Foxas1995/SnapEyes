"""Croatian ("hr") strings and email texts for api/_lib/pay.py, key for key (the twin of pay_hu.py).

What is here, and where pay.py uses it once "hr" is in LANGS:
  SELLER_HR            SELLER["hr"]            the seller line of the short emails when the legal pack is missing
  CONSENT_TEXT_HR      CONSENT_TEXT["hr"]      word for word src/shared/legal.ts CHECKOUT_LEGAL.hr.withdrawalConsent
  SUBMIT_NOTE_HR       SUBMIT_NOTE["hr"]       Stripe's note above its pay button (custom_text.submit), with the
                                               order button words of Art. 8(2) Directive 2011/83/EU in Croatian,
                                               „narudžba s obvezom plaćanja“ (Zakon o zaštiti potrošača)
  ITEM_DESC_HR         ITEM_DESC["hr"]         the Stripe line item's description
  item_name_hr()       item_name() for "hr"
  price_text_hr()      price_text() for "hr": "24,97 €" (EUR); amount_text_hr() the plain one ("24,97 EUR")
  when_text_hr()       when_text() for "hr": "29. 9. 2026. u 10:15 UTC"
  date_text_hr()       date_text() for "hr": "29. 9. 2026."
  quoted_hr()          quoted() for "hr": „...“
  seller_lines_hr()    seller_lines() for "hr"
  confirmation_hr()    the "hr" branch of confirmation_mail(): (subject, blocks) before the legal texts are appended
  ready_hr()           the "hr" branch of ready_mail(): (subject, blocks)
  hr_form()            the Croatian noun form after a number (1 oko, 2 oka, 5 očiju), a helper of item_name_hr

Croatian: Croatia pays in euros, so a price is the euro amount as Croatians write it, "24,97 €" (decimal comma,
no-break space before the sign, thousands with a no-break space), as pay_lt.py does for Lithuania. Dates are numeric
with a dot after day, month and year ("29. 9. 2026."), the parts joined by no-break spaces so a mail client never
breaks a date across lines; a date already ends in its dot, so the sentences below never put a full stop right after
one. A noun after a number has three forms (hr_form). Polite plural "vi", written lowercase inside a sentence, as
modern Croatian web copy does. The greeting carries no name (a Croatian name after a greeting wants the vocative,
which code cannot build from a typed name). The withdrawal right is "pravo na jednostrani raskid ugovora" and the
online function's label „Raskid ugovora“ (Zakon o zaštiti potrošača čl. 81.a as amended in NN 59/26, Art. 11a
Directive 2011/83/EU).
The confirmation is the durable-medium confirmation of Art. 8(7) Directive 2011/83/EU: it repeats the consent
checkbox word for word and confirms it, before anything is made (as the English one does).
No en or em dashes anywhere (owner rule). Stand-alone on purpose: no import of pay, so it can be reviewed and tested
on its own; pay.py passes in what it has computed.
"""
import calendar
import time
from . import catalogue
from . import words as W

SELLER_HR = "MB „Portretizuokis“, matični broj: 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Litva"

# The withdrawal waiver, word for word as the checkout shows it (src/shared/legal.ts CHECKOUT_LEGAL.hr). Adding it means a new
# CONSENT_VERSION in pay.py AND src/shared/legal.ts together (old versions keep their texts in CONSENT_TEXTS). Both elements of
# Art. 16(m) Directive 2011/83/EU: the express consent to start before the period ends, and the knowledge of losing the right.
CONSENT_TEXT_HR = ("Izričito pristajem da SnapEyes odmah, prije isteka roka za jednostrani raskid ugovora, počne izrađivati "
                   "moje digitalno umjetničko djelo. Znam da time gubim pravo na jednostrani raskid ugovora čim izrada "
                   "započne.")

# Stripe shows this right above its pay button, the click that makes the order binding: so the statutory words of
# Art. 8(2) Directive 2011/83/EU in Croatian („narudžba s obvezom plaćanja“) stand at that click too.
SUBMIT_NOTE_HR = ("Kupujete digitalnu datoteku (JPEG, 4096 px). Ne šaljemo ispis ni okvir. Pristali ste da odmah "
                  "započnemo i da vaše pravo na jednostrani raskid ugovora prestaje čim započnemo. Klikom na gumb za "
                  "plaćanje dajete narudžbu s obvezom plaćanja.")

ITEM_DESC_HR = "Samo digitalna datoteka: JPEG, 4096 px na duljoj stranici. Bez ispisa, bez okvira."

STYLE_NAMES = catalogue.names()      # the brand name of every style id, English in every language (api/_lib/styles_registry.py)

# the months in the genitive, as Croatian writes a date in words ("29. rujna 2026."); the emails write dates in numbers
# ("29. 9. 2026.", the common form in Croatian mail), so these are only for a caller that wants the word
MONTHS_HR = ("siječnja", "veljače", "ožujka", "travnja", "svibnja", "lipnja", "srpnja", "kolovoza", "rujna", "listopada",
             "studenoga", "prosinca")

NBSP = " "


def hr_form(n, one, few, many):
    """The Croatian noun form after a number: one (1, 21, 31 ...), few (2-4, 22-24 ...), many (0, 5-20, 25-30 ...)."""
    a = abs(int(n))
    d, h = a % 10, a % 100
    if d == 1 and h != 11:
        return one
    if 2 <= d <= 4 and not 12 <= h <= 14:
        return few
    return many


def item_name_hr(spec, layout=True):
    """The Stripe line item and the confirmation's "Umjetničko djelo" row: "SnapEyes umjetnička slika šarenice, 2 oka, Clean Iris,
    digitalna datoteka od 4096 px". The style is as an order prints it (catalogue.style_label: the look is part of it, "Universe, Vortex");
    a style of the v3 engine with two or more eyes names its layout after the style ("3 oka, Family Colours, Triangle, ...") unless layout
    is False (the confirmation adds its own "raspored: ..." phrase). The layout word is catalogue.layout_name("hr", ...): English until
    api/_lib/layout_names.py has Croatian words."""
    n, style = int(spec["eyes"]), catalogue.style_label(spec["style"], int(spec["eyes"]), spec.get("opts"))
    word = ""
    if layout and n > 1 and catalogue.known(spec["style"]) and not catalogue.is_legacy(spec["style"]):
        word = catalogue.layout_name("hr", spec.get("layout"))
    eyes = hr_form(n, "oko", "oka", "očiju")
    return f"SnapEyes umjetnička slika šarenice, {n} {eyes}, {style}{', ' + word if word else ''}, digitalna datoteka od 4096 px"


def _group(n):
    """Thousands with a no-break space ("1 000"); below 10 000 too, as the euro amounts here never reach it."""
    return f"{int(n):,}".replace(",", NBSP)


def price_text_hr(minor, currency="eur"):
    """A price as the Croatian site shows it, in the currency the order was paid in: "24,97 €" (EUR, Croatia's currency).
    HUF (a Croatian-language order on the forint list, unlikely): Stripe sends it as a two-decimal amount, shown in whole
    forints, "6 990 HUF". Any other currency: "39,00 AUD"."""
    try:
        c = int(minor)
    except (TypeError, ValueError):
        c = 0
    cur = str(currency or "eur").lower()
    if cur == "huf":
        return f"{_group(round(c / 100))}{NBSP}HUF"
    whole, cents = f"{_group(c // 100)}", f"{c % 100:02d}"
    if cur == "eur":
        return f"{whole},{cents}{NBSP}€"
    return f"{whole},{cents}{NBSP}{cur.upper()}"


def amount_text_hr(minor, currency="eur"):
    """The plain amount with the currency code, as amount_text() writes it ("24,97 EUR", "6 990 HUF")."""
    try:
        c = int(minor)
    except (TypeError, ValueError):
        c = 0
    cur = str(currency or "eur").upper()
    if cur == "HUF":
        return f"{_group(round(c / 100))} HUF"
    return f"{_group(c // 100)},{c % 100:02d} {cur}"


def _day(g):
    """"29. 9. 2026." of a struct_time, the parts joined by no-break spaces."""
    return f"{g.tm_mday}.{NBSP}{g.tm_mon}.{NBSP}{g.tm_year}."


def when_text_hr(ts, seconds=False):
    """A moment for a customer: "29. 9. 2026. u 10:15 UTC". ts: unix seconds or an ISO text."""
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
    return f"{_day(g)} u {hm} UTC"


def date_text_hr(day_iso):
    """A date for a customer from "YYYY-MM-DD": "29. 9. 2026." (it ends in its own dot)."""
    try:
        g = time.strptime(str(day_iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(day_iso)
    return _day(g)


def quoted_hr(text):
    return f"„{text}“"


def seller_lines_hr(pack=None, contact="info@snapeyes.com"):
    """The seller as a Croatian email signs: company and code, address, representative and phone when set, email.
    pack: the legal pack (its seller company/address in "hr" once plain.ts LANGS has "hr")."""
    s = (pack or {}).get("seller") if isinstance(pack, dict) else None
    if not isinstance(s, dict) or not isinstance((s.get("company") or {}).get("hr"), str):
        return SELLER_HR.replace(", Gedimino", "\nGedimino") + f"\nE-pošta: {contact}"
    out = [f"{s['company']['hr']}, matični broj: {s['code']}", s["address"]["hr"]]
    if s.get("representative"):
        out.append(f"Zastupa: {s['representative']}")
    if s.get("phone"):
        out.append(f"Telefon: {s['phone']}")
    out.append(f"E-pošta: {s.get('email') or contact}")
    return "\n".join(out)


SIGN_OFF_HR = "Srdačan pozdrav\nSnapEyes"
QUESTIONS_HR = "Imate pitanja? Jednostavno odgovorite na ovu e-poruku."
GREETING_HR = "Dobar dan,"
BUTTON_HR = "Raskid ugovora"          # src/shared/legal.ts WITHDRAWAL_ONLINE.hr.button (Zakon o zaštiti potrošača čl. 81.a)


def confirmation_hr(*, order, spec, n, layout, price, paid_at, consent_at, consent_text, auto, link, wlink,
                    terms_url, updated_day, seller):
    """The "hr" branch of confirmation_mail(): (subject, blocks). pay.py computes what it computes for English
    (link, wlink, price with price_text_hr, layout as catalogue.layout_name("hr", id) gives it, auto = server_starts(pack), the terms URL and
    the pack's "updated" day, seller = seller_lines_hr(pack)) and then appends the rule and the two legal texts."""
    rows = [("Broj narudžbe", order),
            ("Datum sklapanja ugovora", when_text_hr(paid_at)),
            ("Umjetničko djelo", item_name_hr(dict(spec, eyes=n), False) + (f", raspored: {layout}" if n > 1 and layout else ""))]
    names = W.names_text(spec.get("names"))
    if names:
        rows.append(("Imena na djelu", names))
    if spec.get("title"):
        rows.append(("Naslov na djelu", spec["title"]))
    if spec.get("date"):
        rows.append(("Datum na djelu", spec["date"]))
    rows += [("Isporuka", "digitalna datoteka (JPEG, 4096 px na duljoj stranici) na stranici vaše narudžbe; ne šaljemo "
                          "ispis ni okvir"),
             ("Cijena", f"{price}. To je konačna cijena: nismo registrirani kao obveznik PDV-a, stoga PDV ne "
                        f"obračunavamo."),
             ("Plaćanje", "plaćeno putem Stripea")]
    subject = f"Vaša SnapEyes narudžba {order}: potvrda narudžbe"
    blocks = [
        ("p", GREETING_HR),
        ("p", "Hvala vam na narudžbi. Ova e-poruka potvrđuje vaš ugovor s nama. Molimo sačuvajte je: u njoj su vaša "
              "narudžba, vaša privola da odmah započnemo, obavijest o pravu na jednostrani raskid ugovora s obrascem za "
              "jednostrani raskid ugovora te naši uvjeti prodaje."),
        ("h", "Stranica vaše narudžbe"),
        ("link", link),
        ("p", ("Vaše umjetničko djelo počinjemo izrađivati odmah nakon slanja ove e-poruke; ne morate držati otvorenu "
               "nijednu stranicu. Obično je gotovo za nekoliko minuta: datoteku preuzimate na stranici svoje narudžbe, "
               "a kad bude gotova, poslat ćemo vam e-poruku. "
               if auto else
               "Kad je otvorite, počinjemo izrađivati vaše umjetničko djelo (obično je gotovo za nekoliko minuta) i "
               "ondje preuzimate datoteku. ") +
              "Molimo ne dijelite ovu poveznicu: svatko tko je ima može preuzeti vaše umjetničko djelo."),
        ("h", "Vaša narudžba"),
        ("rows", rows),
        ("h", "Vaša privola da odmah započnemo"),
        ("p", f"Prije plaćanja ({when_text_hr(consent_at)}) označili ste ovo polje:"),
        ("quote", quoted_hr(consent_text)),
        ("p", "Potvrđujemo vašu izričitu privolu i to da ste prihvatili njezinu posljedicu. Vašu datoteku počinjemo "
              "izrađivati tek nakon slanja ove e-poruke. Čim započnemo, vaše pravo na jednostrani raskid ugovora "
              "prestaje."),
        ("h", "Vaše pravo na jednostrani raskid ugovora"),
        ("p", "Vašu datoteku počinjemo izrađivati odmah nakon slanja ove e-poruke, pa vaše pravo na jednostrani raskid "
              "ugovora obično prestaje već nekoliko trenutaka poslije. Dok ne započnemo, ugovor možete jednostrano "
              f"raskinuti gumbom „{BUTTON_HR}“ na stranici za raskid svoje narudžbe:"
         if auto else
              f"Dok ne započnemo, ugovor možete jednostrano raskinuti gumbom „{BUTTON_HR}“ na stranici za raskid "
              "svoje narudžbe. Ova poveznica otvara tu stranicu, a da ne započne izrada vaše datoteke (za razliku od "
              "gornje poveznice na stranicu narudžbe):"),
        ("link", wlink),
        ("p", "Ugovor možete jednostrano raskinuti i e-poštom na info@snapeyes.com ili obrascem za jednostrani raskid "
              "ugovora. Cijelu obavijest o pravu na jednostrani raskid ugovora naći ćete na dnu ove e-poruke."),
        ("h", "Naši uvjeti prodaje"),
        ("p", f"Na vašu narudžbu primjenjuju se naši uvjeti prodaje u verziji od {date_text_hr(updated_day)}, a njihov "
              f"cijeli tekst nalazi se na kraju ove e-poruke. Možete ih pročitati i ovdje:"),
        ("link", terms_url),
        ("p", QUESTIONS_HR),
        ("p", SIGN_OFF_HR),
        ("p", seller),
    ]
    return subject, blocks


def ready_hr(*, order, link, checked, seller):
    """The "hr" branch of ready_mail(): (subject, blocks)."""
    subject = "Vaše SnapEyes umjetničko djelo je gotovo"
    blocks = [("p", GREETING_HR),
              ("p", ("Vaša umjetnička slika šarenice je gotova i provjerena." if checked else
                     "Vaša umjetnička slika šarenice je gotova.") +
                    " Preuzmite je na stranici svoje narudžbe:"),
              ("link", link), ("p", f"Narudžba: {order}"), ("p", QUESTIONS_HR),
              ("p", SIGN_OFF_HR), ("p", seller)]
    return subject, blocks
