"""Finnish ("fi") strings and email texts for api/_lib/pay.py, key for key (the twin of pay_hr.py).

What is here, and where pay.py uses it once "fi" is in LANGS:
  SELLER_FI            SELLER["fi"]            the seller line of the short emails when the legal pack is missing
  CONSENT_TEXT_FI      CONSENT_TEXT["fi"]      word for word src/shared/legal.ts CHECKOUT_LEGAL.fi.withdrawalConsent
  SUBMIT_NOTE_FI       SUBMIT_NOTE["fi"]       Stripe's note above its pay button (custom_text.submit), with the
                                               order button words of Art. 8(2) Directive 2011/83/EU in its official
                                               Finnish text, "tilaukseen liittyy maksuvelvollisuus"
  ITEM_DESC_FI         ITEM_DESC["fi"]         the Stripe line item's description
  item_name_fi()       item_name() for "fi"
  price_text_fi()      price_text() for "fi": "24,97 €" (EUR); amount_text_fi() the plain one ("24,97 EUR")
  when_text_fi()       when_text() for "fi": "29.9.2026 klo 10.15 UTC"
  date_text_fi()       date_text() for "fi": "29.9.2026"
  quoted_fi()          quoted() for "fi": ”...”
  seller_lines_fi()    seller_lines() for "fi"
  confirmation_fi()    the "fi" branch of confirmation_mail(): (subject, blocks) before the legal texts are appended
  ready_fi()           the "fi" branch of ready_mail(): (subject, blocks)
  READY_PRINT_FI       READY_PRINT["fi"]       the ready email's section about a print (heading, paragraph), when the order can buy one
  fi_form()            the Finnish noun form after a number (1 silmä, 2 silmää), a helper of item_name_fi

Finnish: Finland pays in euros, so a price is the euro amount as Finns write it, "24,97 €" (decimal comma, no-break
space before the sign, thousands with a no-break space), as src/shared/markets.ts money() writes it on the page. Dates
are numeric without leading zeros and without a final dot ("29.9.2026"), the time takes a full stop and "klo" before it
("klo 10.15", the hour without a leading zero), joined by a no-break space so a mail client never breaks them apart.
A noun after a number has two forms (fi_form). Informal singular "sinä", as the page and Finnish shop mail write. The
greeting carries no name ("Hei,"). The withdrawal right is "peruuttamisoikeus", the period "peruuttamisaika", and the
online function's label "Peruuta sopimus tästä" (Art. 11a Directive 2011/83/EU in its official Finnish text;
kuluttajansuojalaki 6 luku calls the function "peruuttamistoiminto").
The confirmation is the durable-medium confirmation of Art. 8(7) Directive 2011/83/EU: it repeats the consent
checkbox word for word and confirms it, before anything is made (as the English one does).
No en or em dashes anywhere (owner rule). Stand-alone on purpose: no import of pay, so it can be reviewed and tested
on its own; pay.py passes in what it has computed.
"""
import calendar
import time
from . import catalogue
from . import words as W

SELLER_FI = "MB ”Portretizuokis”, yritystunnus 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Liettua"

# The withdrawal waiver, word for word as the checkout shows it (src/shared/legal.ts CHECKOUT_LEGAL.fi). Adding it means a new
# CONSENT_VERSION in pay.py AND src/shared/legal.ts together (old versions keep their texts in CONSENT_TEXTS). Both elements of
# Art. 16(m) Directive 2011/83/EU: the express consent to start before the period ends, and the knowledge of losing the right.
CONSENT_TEXT_FI = ("Annan nimenomaisen suostumukseni siihen, että SnapEyes alkaa tehdä digitaalista taideteostani heti, "
                   "ennen peruuttamisajan päättymistä. Tiedän, että menetän peruuttamisoikeuteni, kun tekeminen on "
                   "alkanut.")

# Stripe shows this right above its pay button, the click that makes the order binding: so the statutory words of
# Art. 8(2) Directive 2011/83/EU in Finnish ("tilaukseen liittyy maksuvelvollisuus") stand at that click too.
SUBMIT_NOTE_FI = ("Aloitamme tiedostosi tekemisen heti maksun jälkeen. Maksupainiketta painamalla teet tilauksen, ja tilaukseen liittyy maksuvelvollisuus.")

ITEM_DESC_FI = "Digitaalinen tiedosto, JPEG, 4096 px."

STYLE_NAMES = catalogue.names()      # the brand name of every style id, English in every language (api/_lib/styles_registry.py)

# the months in the partitive, as Finnish writes a date in words ("29. syyskuuta 2026"); the emails write dates in
# numbers ("29.9.2026", the common form in Finnish mail), so these are only for a caller that wants the word
MONTHS_FI = ("tammikuuta", "helmikuuta", "maaliskuuta", "huhtikuuta", "toukokuuta", "kesäkuuta", "heinäkuuta", "elokuuta",
             "syyskuuta", "lokakuuta", "marraskuuta", "joulukuuta")

NBSP = " "


def fi_form(n, one, many):
    """The Finnish noun form after a number: one (1 only, the nominative), many (0, 2, 3 ..., the partitive singular)."""
    return one if abs(int(n)) == 1 else many


def item_name_fi(spec, layout=True):
    """The Stripe line item and the confirmation's "Taideteos" row: "SnapEyes-iiristaideteos, 2 silmää, Clean Iris,
    4096 px:n digitaalinen tiedosto". The style is as an order prints it (catalogue.style_label: the look is part of it, "Universe, Vortex");
    a style of the v3 engine with two or more eyes names its layout after the style ("3 silmää, Family Colours, Triangle, ...") unless layout
    is False (the confirmation adds its own "asettelu: ..." phrase). The layout word is catalogue.layout_name("fi", ...): English until
    api/_lib/layout_names.py has Finnish words."""
    n, style = int(spec["eyes"]), catalogue.style_label(spec["style"], int(spec["eyes"]), spec.get("opts"))
    word = ""
    if layout and n > 1 and catalogue.known(spec["style"]) and not catalogue.is_legacy(spec["style"]):
        word = catalogue.layout_name("fi", spec.get("layout"))
    eyes = fi_form(n, "silmä", "silmää")
    return f"SnapEyes-iiristaideteos, {n} {eyes}, {style}{', ' + word if word else ''}, 4096 px:n digitaalinen tiedosto"


def _group(n):
    """Thousands with a no-break space ("1 000"); below 10 000 too, as the euro amounts here never reach it."""
    return f"{int(n):,}".replace(",", NBSP)


def price_text_fi(minor, currency="eur"):
    """A price as the Finnish site shows it, in the currency the order was paid in: "24,97 €" (EUR, Finland's currency).
    HUF (a Finnish-language order on the forint list, unlikely): Stripe sends it as a two-decimal amount, shown in whole
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


def amount_text_fi(minor, currency="eur"):
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
    """"29.9.2026" of a struct_time: day.month.year without leading zeros, without spaces and without a final dot."""
    return f"{g.tm_mday}.{g.tm_mon}.{g.tm_year}"


def when_text_fi(ts, seconds=False):
    """A moment for a customer: "29.9.2026 klo 10.15 UTC". ts: unix seconds or an ISO text."""
    if isinstance(ts, str):
        try:
            ts = calendar.timegm(time.strptime(ts.strip()[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return ts
    try:
        g = time.gmtime(float(ts))
    except (TypeError, ValueError, OverflowError):
        return str(ts)
    hm = f"{g.tm_hour}.{g.tm_min:02d}" + (f".{g.tm_sec:02d}" if seconds else "")
    return f"{_day(g)} klo{NBSP}{hm} UTC"


def date_text_fi(day_iso):
    """A date for a customer from "YYYY-MM-DD": "29.9.2026" (no final dot: a sentence may end right after it)."""
    try:
        g = time.strptime(str(day_iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(day_iso)
    return _day(g)


def quoted_fi(text):
    return f"”{text}”"


def seller_lines_fi(pack=None, contact="info@snapeyes.com"):
    """The seller as a Finnish email signs: company and code, address, representative and phone when set, email.
    pack: the legal pack (its seller company/address in "fi" once plain.ts LANGS has "fi")."""
    s = (pack or {}).get("seller") if isinstance(pack, dict) else None
    if not isinstance(s, dict) or not isinstance((s.get("company") or {}).get("fi"), str):
        return SELLER_FI.replace(", Gedimino", "\nGedimino") + f"\nSähköposti: {contact}"
    out = [f"{s['company']['fi']}, yritystunnus {s['code']}", s["address"]["fi"]]
    if s.get("representative"):
        out.append(f"Edustaja: {s['representative']}")
    if s.get("phone"):
        out.append(f"Puhelin: {s['phone']}")
    out.append(f"Sähköposti: {s.get('email') or contact}")
    return "\n".join(out)


SIGN_OFF_FI = "Ystävällisin terveisin\nSnapEyes"
QUESTIONS_FI = "Kysyttävää? Vastaa vain tähän viestiin."
GREETING_FI = "Hei,"
BUTTON_FI = "Peruuta sopimus tästä"          # src/shared/legal.ts WITHDRAWAL_ONLINE.fi.button (Art. 11a(1) Directive 2011/83/EU)


def confirmation_fi(*, order, spec, n, layout, price, paid_at, consent_at, consent_text, auto, link, wlink,
                    terms_url, updated_day, seller):
    """The "fi" branch of confirmation_mail(): (subject, blocks). pay.py computes what it computes for English
    (link, wlink, price with price_text_fi, layout as catalogue.layout_name("fi", id) gives it, auto = server_starts(pack), the terms URL and
    the pack's "updated" day, seller = seller_lines_fi(pack)) and then appends the rule and the two legal texts."""
    rows = [("Tilausnumero", order),
            ("Sopimuksen tekoaika", when_text_fi(paid_at)),
            ("Taideteos", item_name_fi(dict(spec, eyes=n), False) + (f", asettelu: {layout}" if n > 1 and layout else ""))]
    names = W.names_text(spec.get("names"))
    if names:
        rows.append(("Nimet taideteoksessa", names))
    if spec.get("title"):
        rows.append(("Otsikko taideteoksessa", spec["title"]))
    if spec.get("date"):
        rows.append(("Päivämäärä taideteoksessa", spec["date"]))
    rows += [("Toimitus", "digitaalinen tiedosto (JPEG, 4096 px pisimmältä sivulta) tilaussivullasi; tulostetta tai "
                          "kehystä ei lähetetä"),
             ("Hinta", f"{price}. Tämä on lopullinen hinta: emme ole arvonlisäverovelvollisia, joten arvonlisäveroa ei "
                       f"peritä."),
             ("Maksu", "maksettu Stripen kautta")]
    subject = f"SnapEyes-tilauksesi {order}: tilausvahvistus"
    blocks = [
        ("p", GREETING_FI),
        ("p", "Kiitos tilauksestasi. Tämä viesti vahvistaa sopimuksesi kanssamme. Säilytä se: siinä ovat tilauksesi, "
              "tiedot peruuttamisoikeudesta ja malliperuuttamislomake sekä "
              "myyntiehtomme."),
        ("h", "Tilaussivusi"),
        ("link", link),
        ("p", ("Alamme tehdä taideteostasi heti, kun tämä viesti on lähetetty; sinun ei tarvitse pitää mitään sivua "
               "auki. Se on yleensä valmis muutamassa minuutissa: lataat tiedoston tilaussivultasi, ja lähetämme "
               "sinulle sähköpostia, kun se on valmis. "
               if auto else
               "Kun avaat sen, alamme tehdä taideteostasi (se on yleensä valmis muutamassa minuutissa), ja lataat "
               "tiedoston sieltä. ") +
              "Älä jaa tätä linkkiä: kuka tahansa, jolla se on, voi ladata taideteoksesi."),
        ("h", "Tilauksesi"),
        ("rows", rows),
        ("h", "Suostumuksesi välittömään aloittamiseen"),
        ("p", f"Ennen maksamista ({when_text_fi(consent_at)}) rastitit tämän ruudun:"),
        ("quote", quoted_fi(consent_text)),
        ("p", "Vahvistamme nimenomaisen suostumuksesi ja sen, että ilmoitit tietäväsi sen seurauksen. Alamme tehdä "
              "tiedostoasi vasta, kun tämä viesti on lähetetty. Kun olemme aloittaneet, peruuttamisoikeutesi on "
              "päättynyt."),
        ("h", "Peruuttamisoikeutesi"),
        ("p", "Alamme tehdä tiedostoasi heti, kun tämä viesti on lähetetty, joten peruuttamisoikeutesi päättyy "
              "yleensä jo muutaman hetken kuluttua. Niin kauan kuin emme ole aloittaneet, voit peruuttaa sopimuksen "
              f"painikkeella ”{BUTTON_FI}” tilauksesi peruuttamissivulla:"
         if auto else
              f"Niin kauan kuin emme ole aloittaneet, voit peruuttaa sopimuksen painikkeella ”{BUTTON_FI}” tilauksesi "
              "peruuttamissivulla. Tämä linkki avaa sivun aloittamatta tiedostosi tekemistä (toisin kuin yllä oleva "
              "tilaussivun linkki):"),
        ("link", wlink),
        ("p", "Voit peruuttaa sopimuksen myös sähköpostitse osoitteeseen info@snapeyes.com tai "
              "malliperuuttamislomakkeella. Kaikki tiedot peruuttamisoikeudesta ovat tämän viestin lopussa."),
        ("h", "Myyntiehtomme"),
        ("p", f"Tilaukseesi sovelletaan myyntiehtojamme sellaisina kuin ne olivat voimassa {date_text_fi(updated_day)}. "
              f"Niiden koko teksti on tämän viestin lopussa; voit lukea ne myös täältä:"),
        ("link", terms_url),
        ("p", QUESTIONS_FI),
        ("p", SIGN_OFF_FI),
        ("p", seller),
    ]
    return subject, blocks


# the section pay.ready_mail adds when the order can buy a print now (pay.READY_PRINT["fi"]): heading, paragraph, no price
READY_PRINT_FI = ("Taideteoksesi tulosteena",
                  "Voit tilata taideteoksesi myös tulosteena: akryylilasin taakse, kiiltävälle metallille, canvakselle, julisteeksi tai "
                  "akryylilohkoksi. Myös avaimenperäksi. Jokainen tuloste tehdään tilauksesi mukaan ja lähetetään sinulle. Löydät sen tilaussivultasi, "
                  "taideteoksesi alta.")


def ready_fi(*, order, link, checked, seller):
    """The "fi" branch of ready_mail(): (subject, blocks)."""
    subject = "SnapEyes-taideteoksesi on valmis"
    blocks = [("p", GREETING_FI),
              ("p", ("Iiristaideteoksesi on valmis ja tarkistettu." if checked else
                     "Iiristaideteoksesi on valmis.") +
                    " Lataa se tilaussivultasi:"),
              ("link", link), ("p", f"Tilaus: {order}"), ("p", QUESTIONS_FI),
              ("p", SIGN_OFF_FI), ("p", seller)]
    return subject, blocks
