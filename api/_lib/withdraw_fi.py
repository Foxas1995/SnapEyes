"""Finnish ("fi") strings and email texts for api/_lib/withdraw.py, key for key (the twin of withdraw_hr.py).

  STATEMENT_FI        STATEMENT["fi"]: word for word src/order/copy.fi.ts withdraw.statement (the model withdrawal form
                      of Annex I(B) Directive 2011/83/EU in its official Finnish text, "Malliperuuttamislomake":
                      "Ilmoitan, että haluan peruuttaa tekemäni sopimuksen, joka koskee ...", here for the supply of
                      digital content)
  HOLIDAYS_FI,        Finland's public holidays, as Finland lists them for Regulation 1182/71 (the EU e-Justice Portal,
  EASTER_FI           "Time limits on procedures", Finland, question 2; the church holidays come from the Church Order
                      under kirkkolaki, Independence Day and May Day from their own acts): 1 Jan, 6 Jan, Good Friday,
                      Easter Sunday and Monday, 1 May, Ascension Day, Pentecost, 6 Dec, 25-26 Dec. New against the
                      LT + DE + HU + HR table: only 6 Dec (and Pentecost Sunday, Easter + 49, a Sunday anyway);
                      period_end() takes the latest end anywhere, so adding them only ever lengthens a period (the
                      consumer's side). withdraw.py must add them to holidays() to count.
                      THREE Finnish holidays have no fixed date and no Easter offset, so this shape cannot hold them:
                      Midsummer's Day (juhannuspäivä, the Saturday of 20-26 June) and All Saints' Day (pyhäinpäivä, the
                      Saturday of 31 Oct-6 Nov) are always Saturdays, which working_day() skips anyway; Midsummer's Eve
                      (juhannusaatto, the Friday of 19-25 June) is a weekday on Finland's list, and midsummer_eve_fi()
                      below gives its date for withdraw.py to add (until then a period whose 14th day is that Friday
                      ends one working day early for a customer in Finland; the owner reads every lapsed statement).
                      Christmas Eve is no public holiday in Finland, though time limits there treat it like one; it is in HOLIDAYS_LT anyway.
  receipt_fi()        the "fi" branch of receipt_mail(): (subject, blocks)
  unmatched_fi()      the "fi" branch of unmatched_mail(): (subject, blocks)

The receipt is the acknowledgement of receipt on a durable medium (Art. 11a(4) Directive 2011/83/EU, in Finnish
"vastaanottoilmoitus"; kuluttajansuojalaki 6 luku as amended 2026): it names the content of the withdrawal and the date
and time it was received. Informal singular "sinä", as the order page's withdrawal form. The greeting carries no name
(see pay_fi.py); the name stays in the rows. No en or em dashes (owner rule).
Stand-alone: the dates and the money come in formatted by pay_fi (when_text_fi, date_text_fi, price_text_fi); a date
has no final dot, so a sentence may end right after one.
"""
import datetime

from .pay_fi import (GREETING_FI, QUESTIONS_FI, SIGN_OFF_FI, date_text_fi, quoted_fi, when_text_fi)

STATEMENT_FI = ("Ilmoitan, että haluan peruuttaa tekemäni sopimuksen, joka koskee seuraavan digitaalisen sisällön "
                "toimittamista: SnapEyes-taideteos, tilaus {order}.")

HOLIDAYS_FI = ((1, 1), (1, 6), (5, 1), (12, 6), (12, 25), (12, 26))
EASTER_FI = (-2, 0, 1, 39, 49)            # Good Friday (pitkäperjantai), Easter Sunday, Easter Monday, Ascension Day (helatorstai), Pentecost (helluntai)


def midsummer_eve_fi(year):
    """Midsummer's Eve (juhannusaatto) of a year as a datetime.date: the Friday of 19-25 June. Not in HOLIDAYS_FI or
    EASTER_FI (it has no fixed date and no Easter offset); withdraw.py holidays() can add it."""
    d = datetime.date(year, 6, 19)
    return d + datetime.timedelta(days=(4 - d.weekday()) % 7)


UNKNOWN_FI = "ei tiedossa"


def _w(ts):
    return when_text_fi(ts) if ts else UNKNOWN_FI


def receipt_fi(stmt, *, order, name, money, by_day, last_day, seller):
    """The "fi" branch of receipt_mail(). withdraw.py passes what it computes for English: order (or the echoed
    order given), name = echo_name(...), money = _money(stmt, "fi") with price_text_fi in the order's currency,
    by_day = the refund-by day "YYYY-MM-DD", last_day = _last_day(stmt) for a lapsed period, seller =
    seller_lines_fi(pack)."""
    got = when_text_fi(stmt["received_at"], seconds=True)
    rows = [("Vastaanotettu", got), ("Tilaus", order), ("Nimi", name or "-"),
            ("Sähköpostiosoite tätä vahvistusta varten", stmt["email"])]
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    by = date_text_fi(by_day)
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        what = ["Tälle tilaukselle ei tehdä mitään. Maksuasi käsiteltiin vielä, kun peruutit sopimuksen. Jos se saapuu "
                "meille, saat sen kokonaan takaisin käyttämällesi maksutavalle viimeistään 14 päivän kuluessa. Sinulle "
                "ei tule tästä kuluja."]
    elif outcome == "withdrawn":
        first = ""
        if stmt.get("already") and stmt.get("first_at"):
            first = f" (olimme vastaanottaneet peruuttamisilmoituksesi jo aiemmin: {_w(stmt['first_at'])})"
        what = [f"Peruutuksesi on tullut voimaan{first}. Tilauksesi on pysäytetty: mitään ei tehdä. Kuten "
                f"peruuttamisoikeutta koskevissa tiedoissamme kerrotaan, saat maksamasi summan ({money}) takaisin ilman "
                f"aiheetonta viivytystä, viimeistään {by}, käyttämällesi maksutavalle. Sinulle ei tule tästä kuluja."]
    elif outcome == "lapsed" and reason == "period_over":
        end = date_text_fi(last_day)
        what = [f"Tämän tilauksen 14 päivän peruuttamisaika päättyi {end}. Peruuttamisoikeutesi oli siis jo päättynyt, "
                f"kun ilmoituksesi saapui. Katsomme ilmoituksesi silti henkilökohtaisesti ja vastaamme sinulle "
                f"sähköpostitse."]
    else:   # lapsed: making began after the consent and the confirmation
        what = [f"Tilatessasi annoit nimenomaisen suostumuksesi siihen, että alamme tehdä tiedostoasi heti, ja vahvistit, "
                f"että menetät peruuttamisoikeutesi, kun olemme aloittaneet (suostumuksesi ajankohta: "
                f"{_w(stmt.get('consent_at'))}). Vahvistimme tämän tilausvahvistuksessamme (lähetetty: "
                f"{_w(stmt.get('confirmation_at'))}), ja aloimme tehdä tiedostoasi (aloitus: "
                f"{_w(stmt.get('began_at'))}). Peruuttamisoikeutesi oli siis jo päättynyt, kun ilmoituksesi saapui. "
                f"Tilauksesi pysyy voimassa, ja saat tiedostosi tilaussivultasi.",
                "Katsomme ilmoituksesi silti henkilökohtaisesti ja vastaamme sinulle sähköpostitse. Tämä ei vaikuta "
                "lakisääteisiin oikeuksiisi, jos tiedostossa on virhe."]
    moved = []
    if stmt.get("email_given"):
        moved = ["Annoit tätä vahvistusta varten toisen osoitteen. Lähetämme sen sähköpostiosoitteeseen, jolla maksoit, "
                 "koska tämän tilauksen vahvistuksia on jo lähtenyt useita muihin osoitteisiin."]
    subject = f"Vastaanotimme peruuttamisilmoituksesi: SnapEyes-tilaus {order}"
    blocks = [("p", GREETING_FI),
              ("p", "Olemme vastaanottaneet peruuttamisilmoituksesi. Tämä viesti on vastaanottoilmoitus; säilytä "
                    "se.")] + [
              ("p", x) for x in moved] + [
              ("h", "Peruuttamisilmoituksesi"), ("rows", rows), ("quote", quoted_fi(stmt["text"])),
              ("h", "Mitä seuraavaksi tapahtuu")] + [("p", x) for x in what] + [
              ("p", QUESTIONS_FI), ("p", SIGN_OFF_FI), ("p", seller)]
    return subject, blocks


def unmatched_fi(stmt, *, given, name, seller):
    """The "fi" branch of unmatched_mail(): the NEUTRAL receipt for a statement that matched no order. It says
    nothing about any order. given = echo_order(...) or "-", name = echo_name(...)."""
    rows = [("Vastaanotettu", when_text_fi(stmt["received_at"], seconds=True)),
            ("Ilmoitettu tilausnumero", given),
            ("Nimi", name or "-"),
            ("Sähköpostiosoite tätä vahvistusta varten", stmt["email"])]
    said = quoted_fi(STATEMENT_FI.format(order=given))
    subject = "Vastaanotimme peruuttamisilmoituksesi: SnapEyes"
    blocks = [("p", GREETING_FI),
              ("p", "Olemme vastaanottaneet peruuttamisilmoituksesi. Tämä viesti on vastaanottoilmoitus; säilytä "
                    "se."),
              ("h", "Peruuttamisilmoituksesi"), ("rows", rows), ("quote", said),
              ("h", "Mitä seuraavaksi tapahtuu"),
              ("p", "Näillä tiedoilla emme voineet yhdistää ilmoitustasi automaattisesti mihinkään tilaukseen. "
                    "Tarkistamme sen henkilökohtaisesti ja vastaamme sinulle sähköpostitse."),
              ("p", "Jos sinulla on tilausvahvistus sähköpostissasi, voit käyttää myös siinä olevaa peruutuslinkkiä. Tai "
                    "vastaa vain tähän viestiin ja kerro tilausnumerosi."),
              ("p", SIGN_OFF_FI), ("p", seller)]
    return subject, blocks
