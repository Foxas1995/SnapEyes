"""Croatian ("hr") strings and email texts for api/_lib/withdraw.py, key for key (the twin of withdraw_hu.py).

  STATEMENT_HR        STATEMENT["hr"]: word for word src/order/copy.hr.ts withdraw.statement (the model form of the
                      Pravilnik o sadržaju i obliku obavijesti o pravu potrošača na jednostrani raskid ugovora, NN 105/26,
                      and Annex I(B) Directive 2011/83/EU: „... ovim izjavljujem da jednostrano raskidam ugovor ...“,
                      here for the supply of digital content)
  HOLIDAYS_HR,        Croatia's public holidays (Zakon o blagdanima, spomendanima i neradnim danima u Republici Hrvatskoj,
  EASTER_HR           NN 110/19): 1 Jan, 6 Jan, Easter Sunday and Monday, 1 May, 30 May, Corpus Christi, 22 Jun, 5 Aug,
                      15 Aug, 1 Nov, 18 Nov, 25-26 Dec. New against the LT + DE + HU table: 6 Jan, 30 May, Corpus Christi
                      (Easter + 60), 22 Jun, 5 Aug, 18 Nov; period_end() takes the latest end anywhere, so adding them only
                      ever lengthens a period (the consumer's side). withdraw.py must add them to holidays() to count.
  receipt_hr()        the "hr" branch of receipt_mail(): (subject, blocks)
  unmatched_hr()      the "hr" branch of unmatched_mail(): (subject, blocks)

The receipt is the acknowledgement of receipt on a durable medium (Art. 11a(4) Directive 2011/83/EU; Zakon o zaštiti
potrošača čl. 81.a as amended in NN 59/26): it names the content of the withdrawal and the date and time it was
received. Polite plural "vi" (lowercase inside a sentence), as the order page's withdrawal form. The greeting carries no
name (see pay_hr.py); the name stays in the rows. No en or em dashes (owner rule).
Stand-alone: the dates and the money come in formatted by pay_hr (when_text_hr, date_text_hr, price_text_hr); a date
ends in its own dot, so no sentence below puts a full stop right after one.
"""
from .pay_hr import (GREETING_HR, QUESTIONS_HR, SIGN_OFF_HR, date_text_hr, quoted_hr, when_text_hr)

STATEMENT_HR = ("Ovime izjavljujem da jednostrano raskidam ugovor o isporuci sljedećeg digitalnog sadržaja: umjetničko "
                "djelo SnapEyes, narudžba {order}.")

HOLIDAYS_HR = ((1, 1), (1, 6), (5, 1), (5, 30), (6, 22), (8, 5), (8, 15), (11, 1), (11, 18), (12, 25), (12, 26))
EASTER_HR = (0, 1, 60)                    # Easter Sunday (Uskrs), Easter Monday (Uskrsni ponedjeljak), Corpus Christi (Tijelovo)

UNKNOWN_HR = "nepoznato"


def _w(ts):
    return when_text_hr(ts) if ts else UNKNOWN_HR


def receipt_hr(stmt, *, order, name, money, by_day, last_day, seller):
    """The "hr" branch of receipt_mail(). withdraw.py passes what it computes for English: order (or the echoed
    order given), name = echo_name(...), money = _money(stmt, "hr") with price_text_hr in the order's currency,
    by_day = the refund-by day "YYYY-MM-DD", last_day = _last_day(stmt) for a lapsed period, seller =
    seller_lines_hr(pack)."""
    got = when_text_hr(stmt["received_at"], seconds=True)
    rows = [("Zaprimljeno", got), ("Narudžba", order), ("Ime i prezime", name or "-"),
            ("E-adresa za ovu potvrdu", stmt["email"])]
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    by = date_text_hr(by_day)
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        what = ["Za ovu narudžbu ništa se neće izraditi. Kad ste raskinuli ugovor, vaše plaćanje još je bilo u obradi. "
                "Ako stigne do nas, vratit ćemo vam ga u cijelosti, na način plaćanja kojim ste platili, najkasnije u "
                "roku od 14 dana. Za to ne plaćate nikakve naknade."]
    elif outcome == "withdrawn":
        first = ""
        if stmt.get("already") and stmt.get("first_at"):
            first = f" (vaš raskid zaprimili smo već ranije: {_w(stmt['first_at'])})"
        what = [f"Ugovor je jednostrano raskinut{first}. Vaša narudžba je zaustavljena: ništa se neće izraditi. Kako "
                f"je navedeno u našoj obavijesti o pravu na jednostrani raskid ugovora, plaćeni iznos ({money}) vratit "
                f"ćemo vam bez nepotrebnog odgađanja, najkasnije do {by}, na način plaćanja kojim ste platili. Za to ne "
                f"plaćate nikakve naknade."]
    elif outcome == "lapsed" and reason == "period_over":
        end = date_text_hr(last_day)
        what = [f"Rok od 14 dana za jednostrani raskid ugovora za ovu narudžbu istekao je {end}, pa je vaše pravo na "
                f"jednostrani raskid ugovora već bilo prestalo kad je stigla vaša izjava. Vašu izjavu ipak ćemo osobno "
                f"pogledati i odgovoriti vam e-poštom."]
    else:   # lapsed: making began after the consent and the confirmation
        what = [f"Pri narudžbi ste izričito pristali da odmah počnemo izrađivati vašu datoteku i potvrdili da time "
                f"gubite pravo na jednostrani raskid ugovora čim započnemo (vrijeme vaše privole: "
                f"{_w(stmt.get('consent_at'))}). To smo vam potvrdili u e-poruci s potvrdom narudžbe (poslano: "
                f"{_w(stmt.get('confirmation_at'))}), a izradu vaše datoteke smo započeli (početak: "
                f"{_w(stmt.get('began_at'))}). Zato je vaše pravo na jednostrani raskid ugovora već bilo prestalo kad je "
                f"stigla vaša izjava. Vaša narudžba ostaje na snazi, a datoteku dobivate na stranici svoje narudžbe.",
                "Vašu izjavu ipak ćemo osobno pogledati i odgovoriti vam e-poštom. To ne utječe na vaša zakonska prava "
                "ako datoteka ima nedostatak."]
    moved = []
    if stmt.get("email_given"):
        moved = ["Za ovu potvrdu naveli ste drugu adresu. Šaljemo je na e-adresu kojom ste platili jer je za ovu "
                 "narudžbu već nekoliko potvrda otišlo na druge adrese."]
    subject = f"Zaprimili smo vaš raskid ugovora: SnapEyes narudžba {order}"
    blocks = [("p", GREETING_HR),
              ("p", "Zaprimili smo vašu izjavu o jednostranom raskidu ugovora. Ova e-poruka potvrda je primitka; molimo "
                    "sačuvajte je.")] + [
              ("p", x) for x in moved] + [
              ("h", "Vaša izjava o jednostranom raskidu ugovora"), ("rows", rows), ("quote", quoted_hr(stmt["text"])),
              ("h", "Što slijedi")] + [("p", x) for x in what] + [
              ("p", QUESTIONS_HR), ("p", SIGN_OFF_HR), ("p", seller)]
    return subject, blocks


def unmatched_hr(stmt, *, given, name, seller):
    """The "hr" branch of unmatched_mail(): the NEUTRAL receipt for a statement that matched no order. It says
    nothing about any order. given = echo_order(...) or "-", name = echo_name(...)."""
    rows = [("Zaprimljeno", when_text_hr(stmt["received_at"], seconds=True)),
            ("Navedeni broj narudžbe", given),
            ("Ime i prezime", name or "-"),
            ("E-adresa za ovu potvrdu", stmt["email"])]
    said = quoted_hr(STATEMENT_HR.format(order=given))
    subject = "Zaprimili smo vašu izjavu o jednostranom raskidu ugovora: SnapEyes"
    blocks = [("p", GREETING_HR),
              ("p", "Zaprimili smo vašu izjavu o jednostranom raskidu ugovora. Ova e-poruka potvrda je primitka; molimo "
                    "sačuvajte je."),
              ("h", "Vaša izjava o jednostranom raskidu ugovora"), ("rows", rows), ("quote", said),
              ("h", "Što slijedi"),
              ("p", "Na temelju ovih podataka vašu izjavu nismo mogli automatski povezati ni s jednom narudžbom. "
                    "Provjerit ćemo je osobno i odgovoriti vam e-poštom."),
              ("p", "Ako imate e-poruku s potvrdom narudžbe, možete upotrijebiti i poveznicu za raskid iz nje. Ili "
                    "jednostavno odgovorite na ovu e-poruku i navedite broj svoje narudžbe."),
              ("p", SIGN_OFF_HR), ("p", seller)]
    return subject, blocks
