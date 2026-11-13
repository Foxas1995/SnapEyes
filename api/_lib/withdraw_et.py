"""Estonian ("et") strings and email texts for api/_lib/withdraw.py, key for key (the twin of withdraw_hr.py).

  STATEMENT_ET        STATEMENT["et"]: word for word src/order/copy.et.ts withdraw.statement (the model form of
                      justiitsministri 17.12.2013 määrus nr 41, lisa 1, and Annex I(B) Directive 2011/83/EU:
                      „Käesolevaga taganen ... lepingust, mille esemeks on ...“, here for the supply of digital content)
  HOLIDAYS_ET,        Estonia's public holidays (Pühade ja tähtpäevade seadus § 1 and § 2): 1 Jan, 24 Feb (the national
  EASTER_ET           day), Good Friday, Easter Sunday, 1 May, Pentecost Sunday, 23 Jun, 24 Jun, 20 Aug, 24-26 Dec. Easter
                      Monday is not a public holiday in Estonia. Easter Sunday and Pentecost always fall on a Sunday, so
                      they never move a deadline; they are listed because the Act lists them. New against the LT + DE +
                      HU + HR table: 24 Feb and 23 Jun (24 Jun and 24 Dec are Lithuanian holidays too, 20 Aug a Hungarian one, Good Friday
                      is a German one); period_end() takes the latest end anywhere, so adding them only ever lengthens a
                      period (the consumer's side). withdraw.py must add them to holidays() to count.
  receipt_et()        the "et" branch of receipt_mail(): (subject, blocks)
  unmatched_et()      the "et" branch of unmatched_mail(): (subject, blocks)

The receipt is the acknowledgement of receipt on a durable medium (Art. 11a(4) Directive 2011/83/EU; Võlaõigusseadus
§ 56⁴ lg 4): it names the content of the withdrawal and the date and time it was received. Informal singular "sina", as
the order page's withdrawal form. The greeting carries no name (see pay_et.py); the name stays in the rows. No en or
em dashes (owner rule).
Stand-alone: the dates and the money come in formatted by pay_et (when_text_et, date_text_et, price_text_et); a date
has no final dot, so a sentence below may end right after one.
"""
from .pay_et import (GREETING_ET, QUESTIONS_ET, SIGN_OFF_ET, date_text_et, quoted_et, when_text_et)

STATEMENT_ET = ("Käesolevaga taganen lepingust, mille esemeks on järgmise digitaalse sisu üleandmine: SnapEyesi "
                "kunstiteos, tellimus {order}.")

HOLIDAYS_ET = ((1, 1), (2, 24), (5, 1), (6, 23), (6, 24), (8, 20), (12, 24), (12, 25), (12, 26))
EASTER_ET = (-2, 0, 49)                   # Good Friday (suur reede), Easter Sunday (ülestõusmispühade 1. püha), Pentecost (nelipühade 1. püha)

UNKNOWN_ET = "teadmata"


def _w(ts):
    return when_text_et(ts) if ts else UNKNOWN_ET


def receipt_et(stmt, *, order, name, money, by_day, last_day, seller):
    """The "et" branch of receipt_mail(). withdraw.py passes what it computes for English: order (or the echoed
    order given), name = echo_name(...), money = _money(stmt, "et") with price_text_et in the order's currency,
    by_day = the refund-by day "YYYY-MM-DD", last_day = _last_day(stmt) for a lapsed period, seller =
    seller_lines_et(pack)."""
    got = when_text_et(stmt["received_at"], seconds=True)
    rows = [("Kätte saadud", got), ("Tellimus", order), ("Nimi", name or "-"),
            ("E-posti aadress selle kinnituse jaoks", stmt["email"])]
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    by = date_text_et(by_day)
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        what = ["Selle tellimuse jaoks ei valmistata midagi. Kui sa lepingust taganesid, oli sinu makse veel "
                "töötlemisel. Kui see meieni jõuab, saad selle täies ulatuses tagasi samale makseviisile, mida "
                "kasutasid, hiljemalt 14 päeva jooksul. Sa ei maksa selle eest mingeid tasusid."]
    elif outcome == "withdrawn":
        first = ""
        if stmt.get("already") and stmt.get("first_at"):
            first = f" (olime sinu taganemisavalduse juba varem kätte saanud: {_w(stmt['first_at'])})"
        what = [f"Sinu taganemine on jõustunud{first}. Sinu tellimus on peatatud: midagi ei valmistata. Nagu meie "
                f"taganemisõiguse teabes kirjas, saad makstud summa ({money}) tagasi viivitamata, hiljemalt {by}, "
                f"samale makseviisile, mida kasutasid. Sa ei maksa selle eest mingeid tasusid."]
    elif outcome == "lapsed" and reason == "period_over":
        end = date_text_et(last_day)
        what = [f"Selle tellimuse 14-päevane taganemistähtaeg lõppes {end}. Seetõttu oli sinu taganemisõigus avalduse "
                f"saabumise ajaks juba lõppenud. Vaatame sinu avalduse siiski isiklikult üle ja vastame sulle "
                f"e-kirjaga."]
    else:   # lapsed: making began after the consent and the confirmation
        what = [f"Tellimisel nõustusid sõnaselgelt, et hakkame sinu faili kohe valmistama, ja kinnitasid, et kaotad oma "
                f"taganemisõiguse, kui oleme alustanud (sinu nõusoleku aeg: {_w(stmt.get('consent_at'))}). Kinnitasime "
                f"seda tellimuse kinnituskirjas (saadetud: {_w(stmt.get('confirmation_at'))}) ja alustasime sinu faili "
                f"valmistamist (algus: {_w(stmt.get('began_at'))}). Seetõttu oli sinu taganemisõigus avalduse "
                f"saabumise ajaks juba lõppenud. Sinu tellimus jääb kehtima ja faili saad kätte oma tellimuse lehelt.",
                "Vaatame sinu avalduse siiski isiklikult üle ja vastame sulle e-kirjaga. See ei mõjuta sinu seadusest "
                "tulenevaid õigusi puudusega faili korral."]
    moved = []
    if stmt.get("email_given"):
        moved = ["Andsid selle kinnituse jaoks teise aadressi. Saadame selle e-posti aadressile, millega maksid, sest "
                 "selle tellimuse kohta on juba mitu kinnitust läinud teistele aadressidele."]
    subject = f"Saime sinu taganemisavalduse kätte: SnapEyesi tellimus {order}"
    blocks = [("p", GREETING_ET),
              ("p", "Oleme sinu taganemisavalduse kätte saanud. See e-kiri kinnitab selle kättesaamist; palun hoia see "
                    "alles.")] + [
              ("p", x) for x in moved] + [
              ("h", "Sinu taganemisavaldus"), ("rows", rows), ("quote", quoted_et(stmt["text"])),
              ("h", "Mis edasi saab")] + [("p", x) for x in what] + [
              ("p", QUESTIONS_ET), ("p", SIGN_OFF_ET), ("p", seller)]
    return subject, blocks


def unmatched_et(stmt, *, given, name, seller):
    """The "et" branch of unmatched_mail(): the NEUTRAL receipt for a statement that matched no order. It says
    nothing about any order. given = echo_order(...) or "-", name = echo_name(...)."""
    rows = [("Kätte saadud", when_text_et(stmt["received_at"], seconds=True)),
            ("Esitatud tellimuse number", given),
            ("Nimi", name or "-"),
            ("E-posti aadress selle kinnituse jaoks", stmt["email"])]
    said = quoted_et(STATEMENT_ET.format(order=given))
    subject = "Saime sinu taganemisavalduse kätte: SnapEyes"
    blocks = [("p", GREETING_ET),
              ("p", "Oleme sinu taganemisavalduse kätte saanud. See e-kiri kinnitab selle kättesaamist; palun hoia see "
                    "alles."),
              ("h", "Sinu taganemisavaldus"), ("rows", rows), ("quote", said),
              ("h", "Mis edasi saab"),
              ("p", "Nende andmete põhjal ei saanud me sinu avaldust automaatselt ühegi tellimusega kokku viia. "
                    "Kontrollime seda isiklikult ja vastame sulle e-kirjaga."),
              ("p", "Kui sul on tellimuse kinnituskiri, võid kasutada ka selles olevat taganemislinki. Või vasta "
                    "lihtsalt sellele e-kirjale ja ütle meile oma tellimuse number."),
              ("p", SIGN_OFF_ET), ("p", seller)]
    return subject, blocks
