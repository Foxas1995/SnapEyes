"""Latvian ("lv") strings and email texts for api/_lib/pay.py, key for key (the twin of pay_hr.py).

What is here, and where pay.py uses it once "lv" is in LANGS:
  SELLER_LV            SELLER["lv"]            the seller line of the short emails when the legal pack is missing
  CONSENT_TEXT_LV      CONSENT_TEXT["lv"]      word for word src/shared/legal.ts CHECKOUT_LEGAL.lv.withdrawalConsent
  SUBMIT_NOTE_LV       SUBMIT_NOTE["lv"]       Stripe's note above its pay button (custom_text.submit), with the
                                               order button words of Art. 8(2) Directive 2011/83/EU in its official
                                               Latvian text, „pasūtījums ar pienākumu maksāt”
  ITEM_DESC_LV         ITEM_DESC["lv"]         the Stripe line item's description
  item_name_lv()       item_name() for "lv"
  price_text_lv()      price_text() for "lv": "24,97 €" (EUR); amount_text_lv() the plain one ("24,97 EUR")
  when_text_lv()       when_text() for "lv": "29.09.2026. plkst. 10:15 UTC"
  date_text_lv()       date_text() for "lv": "29.09.2026."
  quoted_lv()          quoted() for "lv": „...”
  seller_lines_lv()    seller_lines() for "lv"
  confirmation_lv()    the "lv" branch of confirmation_mail(): (subject, blocks) before the legal texts are appended
  ready_lv()           the "lv" branch of ready_mail(): (subject, blocks)
  READY_PRINT_LV       READY_PRINT["lv"]       the ready email's section about a print (heading, paragraph), when the order can buy one
  lv_form()            the Latvian noun form after a number (1 acs, 2 acis, 10 acu), a helper of item_name_lv

Latvian: Latvia pays in euros, so a price is the euro amount as Latvians write it, "24,97 €" (decimal comma, no-break
space before the sign, thousands with a no-break space), as pay_lt.py does for Lithuania and src/shared/markets.ts
money() does on the page. Dates are numeric, day.month.year with two-digit day and month and a dot after the year
("29.09.2026.", the year being an ordinal in Latvian); a date already ends in its dot, so the sentences below never put
a full stop right after one. A noun after a number has three forms (lv_form). Polite plural "jūs", written lowercase
inside a sentence, as Latvian web copy does. The greeting carries no name (a Latvian name after a greeting wants the
vocative, which code cannot build from a typed name). The withdrawal right is "atteikuma tiesības" and the online
function's label „Atteikties no līguma” (Art. 11a Directive 2011/83/EU in its Latvian text, OJ L, 2023/2673).
The confirmation is the durable-medium confirmation of Art. 8(7) Directive 2011/83/EU: it repeats the consent
checkbox word for word and confirms it, before anything is made (as the English one does).
No en or em dashes anywhere (owner rule). Stand-alone on purpose: no import of pay, so it can be reviewed and tested
on its own; pay.py passes in what it has computed.
"""
import calendar
import time
from . import catalogue
from . import words as W

SELLER_LV = "MB „Portretizuokis”, reģistrācijas numurs: 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Lietuva"

# The withdrawal waiver, word for word as the checkout shows it (src/shared/legal.ts CHECKOUT_LEGAL.lv). Adding it means a new
# CONSENT_VERSION in pay.py AND src/shared/legal.ts together (old versions keep their texts in CONSENT_TEXTS). Both elements of
# Art. 16(m) Directive 2011/83/EU: the express consent to start before the period ends, and the knowledge of losing the right.
CONSENT_TEXT_LV = ("Es skaidri piekrītu, ka SnapEyes sāk veidot manu digitālo mākslas darbu uzreiz, pirms atteikuma "
                   "termiņa beigām. Es zinu, ka zaudēju atteikuma tiesības, tiklīdz veidošana ir sākta.")

# Stripe shows this right above its pay button, the click that makes the order binding: so the statutory words of
# Art. 8(2) Directive 2011/83/EU in Latvian („pasūtījums ar pienākumu maksāt”) stand at that click too.
SUBMIT_NOTE_LV = ("Jūs piekritāt, ka sākam uzreiz "
                  "un ka jūsu atteikuma tiesības beidzas, tiklīdz esam sākuši. Nospiežot maksāšanas pogu, jūs veicat "
                  "pasūtījumu ar pienākumu maksāt.")

ITEM_DESC_LV = "Digitāls fails, JPEG, 4096 px."

STYLE_NAMES = catalogue.names()      # the brand name of every style id, English in every language (api/_lib/styles_registry.py)

# the months in the nominative, as Latvian writes a date in words ("2026. gada 29. septembris"); the emails write dates
# in numbers ("29.09.2026.", the common form in Latvian mail), so these are only for a caller that wants the word
MONTHS_LV = ("janvāris", "februāris", "marts", "aprīlis", "maijs", "jūnijs", "jūlijs", "augusts", "septembris", "oktobris",
             "novembris", "decembris")

NBSP = "\u00a0"


def lv_form(n, one, few, many):
    """The Latvian noun form after a number: one (1, 21, 31 ...), few (2-9, 22-29 ...), many (0, 10-20, 30 ...)."""
    a = abs(int(n))
    d, h = a % 10, a % 100
    if d == 1 and h != 11:
        return one
    if 2 <= d <= 9 and not 12 <= h <= 19:
        return few
    return many


def item_name_lv(spec, layout=True):
    """The Stripe line item and the confirmation's "Mākslas darbs" row: "SnapEyes varavīksnenes mākslas darbs, 2 acis, Clean Iris,
    4096 px digitālais fails". The style is as an order prints it (catalogue.style_label: the look is part of it, "Universe, Vortex");
    a style of the v3 engine with two or more eyes names its layout after the style ("3 acis, Family Colours, Triangle, ...") unless layout
    is False (the confirmation adds its own "izkārtojums: ..." phrase). The layout word is catalogue.layout_name("lv", ...): English until
    api/_lib/layout_names.py has Latvian words."""
    n, style = int(spec["eyes"]), catalogue.style_label(spec["style"], int(spec["eyes"]), spec.get("opts"))
    word = ""
    if layout and n > 1 and catalogue.known(spec["style"]) and not catalogue.is_legacy(spec["style"]):
        word = catalogue.layout_name("lv", spec.get("layout"))
    eyes = lv_form(n, "acs", "acis", "acu")
    return f"SnapEyes varavīksnenes mākslas darbs, {n} {eyes}, {style}{', ' + word if word else ''}, 4096 px digitālais fails"


def _group(n):
    """Thousands with a no-break space ("1 000"); below 10 000 too, as the euro amounts here never reach it."""
    return f"{int(n):,}".replace(",", NBSP)


def price_text_lv(minor, currency="eur"):
    """A price as the Latvian site shows it, in the currency the order was paid in: "24,97 €" (EUR, Latvia's currency).
    HUF (a Latvian-language order on the forint list, unlikely): Stripe sends it as a two-decimal amount, shown in whole
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


def amount_text_lv(minor, currency="eur"):
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
    """"29.09.2026." of a struct_time: two-digit day and month, and the dot after the year."""
    return f"{g.tm_mday:02d}.{g.tm_mon:02d}.{g.tm_year}."


def when_text_lv(ts, seconds=False):
    """A moment for a customer: "29.09.2026. plkst. 10:15 UTC". ts: unix seconds or an ISO text."""
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
    return f"{_day(g)} plkst. {hm} UTC"


def date_text_lv(day_iso):
    """A date for a customer from "YYYY-MM-DD": "29.09.2026." (it ends in its own dot)."""
    try:
        g = time.strptime(str(day_iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(day_iso)
    return _day(g)


def quoted_lv(text):
    return f"„{text}”"


def seller_lines_lv(pack=None, contact="info@snapeyes.com"):
    """The seller as a Latvian email signs: company and code, address, representative and phone when set, email.
    pack: the legal pack (its seller company/address in "lv" once plain.ts LANGS has "lv")."""
    s = (pack or {}).get("seller") if isinstance(pack, dict) else None
    if not isinstance(s, dict) or not isinstance((s.get("company") or {}).get("lv"), str):
        return SELLER_LV.replace(", Gedimino", "\nGedimino") + f"\nE-pasts: {contact}"
    out = [f"{s['company']['lv']}, reģistrācijas numurs: {s['code']}", s["address"]["lv"]]
    if s.get("representative"):
        out.append(f"Pārstāv: {s['representative']}")
    if s.get("phone"):
        out.append(f"Tālrunis: {s['phone']}")
    out.append(f"E-pasts: {s.get('email') or contact}")
    return "\n".join(out)


SIGN_OFF_LV = "Ar cieņu\nSnapEyes"
QUESTIONS_LV = "Jautājumi? Vienkārši atbildiet uz šo e-pastu."
GREETING_LV = "Labdien!"
BUTTON_LV = "Atteikties no līguma"    # src/shared/legal.ts WITHDRAWAL_ONLINE.lv.button (Art. 11a(1) Directive 2011/83/EU, Latvian text)


def confirmation_lv(*, order, spec, n, layout, price, paid_at, consent_at, consent_text, auto, link, wlink,
                    terms_url, updated_day, seller):
    """The "lv" branch of confirmation_mail(): (subject, blocks). pay.py computes what it computes for English
    (link, wlink, price with price_text_lv, layout as catalogue.layout_name("lv", id) gives it, auto = server_starts(pack), the terms URL and
    the pack's "updated" day, seller = seller_lines_lv(pack)) and then appends the rule and the two legal texts."""
    rows = [("Pasūtījuma numurs", order),
            ("Līguma noslēgšanas datums", when_text_lv(paid_at)),
            ("Mākslas darbs", item_name_lv(dict(spec, eyes=n), False) + (f", izkārtojums: {layout}" if n > 1 and layout else ""))]
    names = W.names_text(spec.get("names"))
    if names:
        rows.append(("Vārdi mākslas darbā", names))
    if spec.get("title"):
        rows.append(("Nosaukums mākslas darbā", spec["title"]))
    if spec.get("date"):
        rows.append(("Datums mākslas darbā", spec["date"]))
    rows += [("Piegāde", "digitāls fails (JPEG, 4096 px garākajā malā) jūsu pasūtījuma lapā; izdruku un rāmi "
                         "nesūtām"),
             ("Cena", f"{price}. Tā ir galīgā cena: neesam reģistrēti kā PVN maksātāji, tāpēc PVN netiek "
                      f"pieskaitīts."),
             ("Maksājums", "samaksāts, izmantojot Stripe")]
    subject = f"Jūsu SnapEyes pasūtījums {order}: pasūtījuma apstiprinājums"
    blocks = [
        ("p", GREETING_LV),
        ("p", "Paldies par pasūtījumu. Šis e-pasts apstiprina jūsu līgumu ar mums. Lūdzu, saglabājiet to: tajā ir jūsu "
              "pasūtījums, jūsu piekrišana sākt uzreiz, informācija par atteikuma tiesībām ar atteikuma veidlapas "
              "paraugu un mūsu pārdošanas noteikumi."),
        ("h", "Jūsu pasūtījuma lapa"),
        ("link", link),
        ("p", ("Jūsu mākslas darbu sākam veidot uzreiz pēc šī e-pasta nosūtīšanas; jums nav jātur atvērta neviena "
               "lapa. Parasti tas ir gatavs dažu minūšu laikā: failu lejupielādējat savā pasūtījuma lapā, un, kad tas "
               "būs gatavs, nosūtīsim jums e-pastu. "
               if auto else
               "Kad to atvērsiet, sāksim veidot jūsu mākslas darbu (parasti tas ir gatavs dažu minūšu laikā), un tur "
               "lejupielādēsiet failu. ") +
              "Lūdzu, nedalieties ar šo saiti: ikviens, kam tā ir, var lejupielādēt jūsu mākslas darbu."),
        ("h", "Jūsu pasūtījums"),
        ("rows", rows),
        ("h", "Jūsu piekrišana sākt uzreiz"),
        ("p", f"Pirms maksāšanas ({when_text_lv(consent_at)}) jūs atzīmējāt šo rūtiņu:"),
        ("quote", quoted_lv(consent_text)),
        ("p", "Apstiprinām jūsu skaidri pausto piekrišanu un jūsu apliecinājumu. Jūsu failu sākam veidot tikai pēc šī "
              "e-pasta nosūtīšanas. Tiklīdz esam sākuši, jūsu atteikuma tiesības ir beigušās."),
        ("h", "Jūsu atteikuma tiesības"),
        ("p", "Jūsu failu sākam veidot uzreiz pēc šī e-pasta nosūtīšanas, tāpēc jūsu atteikuma tiesības parasti "
              "beidzas jau pēc dažiem mirkļiem. Kamēr neesam sākuši, no līguma varat atteikties ar pogu "
              f"„{BUTTON_LV}” sava pasūtījuma atteikuma lapā:"
         if auto else
              f"Kamēr neesam sākuši, no līguma varat atteikties ar pogu „{BUTTON_LV}” sava pasūtījuma atteikuma "
              "lapā. Šī saite to atver, nesākot veidot jūsu failu (atšķirībā no augstāk esošās pasūtījuma lapas "
              "saites):"),
        ("link", wlink),
        ("p", "No līguma varat atteikties arī pa e-pastu uz info@snapeyes.com vai ar atteikuma veidlapas paraugu. "
              "Pilna informācija par atteikuma tiesībām ir šī e-pasta beigās."),
        ("h", "Mūsu pārdošanas noteikumi"),
        ("p", f"Jūsu pasūtījumam piemērojami mūsu pārdošanas noteikumi {date_text_lv(updated_day)} redakcijā, un "
              f"pilns to teksts ir šī e-pasta beigās. Tos varat izlasīt arī šeit:"),
        ("link", terms_url),
        ("p", QUESTIONS_LV),
        ("p", SIGN_OFF_LV),
        ("p", seller),
    ]
    return subject, blocks


# the section pay.ready_mail adds when the order can buy a print now (pay.READY_PRINT["lv"]): heading, paragraph, no price
READY_PRINT_LV = ("Jūsu mākslas darbs kā izdruka",
                  "Savu mākslas darbu varat pasūtīt arī kā izdruku: aiz akrila stikla, uz spīdīga metāla, uz audekla, kā plakātu vai kā "
                  "akrila bloku. Arī kā atslēgu piekariņu. Katru izdruku izgatavojam pēc pasūtījuma un nosūtām jums. Piedāvājumu atradīsiet savā pasūtījuma lapā, "
                  "zem mākslas darba.")


def ready_lv(*, order, link, checked, seller):
    """The "lv" branch of ready_mail(): (subject, blocks)."""
    subject = "Jūsu SnapEyes mākslas darbs ir gatavs"
    blocks = [("p", GREETING_LV),
              ("p", ("Jūsu varavīksnenes mākslas darbs ir gatavs un pārbaudīts." if checked else
                     "Jūsu varavīksnenes mākslas darbs ir gatavs.") +
                    " Lejupielādējiet to savā pasūtījuma lapā:"),
              ("link", link), ("p", f"Pasūtījums: {order}"), ("p", QUESTIONS_LV),
              ("p", SIGN_OFF_LV), ("p", seller)]
    return subject, blocks
