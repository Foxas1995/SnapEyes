"""Latvian ("lv") strings and email texts for api/_lib/withdraw.py, key for key (the twin of withdraw_hr.py).

  STATEMENT_LV        STATEMENT["lv"]: word for word src/order/copy.lv.ts withdraw.statement (the model withdrawal form
                      of Annex I(B) Directive 2011/83/EU in its Latvian text, „Atteikuma veidlapas paraugs”: „... paziņoju,
                      ka ... atteikties no manis noslēgtā ... līguma ...”, here for the supply of digital content)
  HOLIDAYS_LV,        Latvia's public holidays (likums „Par svētku, atceres un atzīmējamām dienām”, 1. pants): 1 Jan,
  EASTER_LV           Good Friday, Easter Sunday and Monday, 1 May, 4 May, Pentecost, 23-24 Jun, 18 Nov, 24-26 Dec,
                      31 Dec. New against the LT + DE + HU + HR table: 4 May, 23 Jun, 31 Dec (Pentecost is a Sunday);
                      period_end() takes the latest end anywhere, so adding them only ever lengthens a period (the
                      consumer's side). withdraw.py must add them to holidays() to count.
                      NOT in the table, because a fixed date or an Easter offset cannot say them: Mother's Day (the
                      second Sunday of May, always a Sunday, so it never ends a period anyway); the closing day of the
                      Song and Dance Festival (no fixed date, set for each festival); and the law's substitute day
                      (when 4 May or 18 Nov falls on a Saturday or Sunday, the next working day is a day off: first on
                      Monday 20 Nov 2028). The owner looks at every lapsed statement by hand, as for the holidays of
                      other countries; a rule for the substitute day would belong in withdraw.py holidays().
  receipt_lv()        the "lv" branch of receipt_mail(): (subject, blocks)
  unmatched_lv()      the "lv" branch of unmatched_mail(): (subject, blocks)

The receipt is the acknowledgement of receipt on a durable medium (Art. 11a(4) Directive 2011/83/EU, „apstiprinājums
par atteikuma saņemšanu uz pastāvīga informācijas nesēja”): it names the content of the withdrawal and the date and
time it was received. Polite plural "jūs" (lowercase inside a sentence), as the order page's withdrawal form. The
greeting carries no name (see pay_lv.py); the name stays in the rows. No en or em dashes (owner rule).
Stand-alone: the dates and the money come in formatted by pay_lv (when_text_lv, date_text_lv, price_text_lv); a date
ends in its own dot, so no sentence below puts a full stop right after one.
"""
from .pay_lv import (GREETING_LV, QUESTIONS_LV, SIGN_OFF_LV, date_text_lv, quoted_lv, when_text_lv)

STATEMENT_LV = ("Ar šo paziņoju, ka atsakos no manis noslēgtā līguma par šāda digitālā satura piegādi: SnapEyes mākslas "
                "darbs, pasūtījums {order}.")

HOLIDAYS_LV = ((1, 1), (5, 1), (5, 4), (6, 23), (6, 24), (11, 18), (12, 24), (12, 25), (12, 26), (12, 31))
EASTER_LV = (-2, 0, 1, 49)                # Good Friday (Lielā Piektdiena), Easter Sunday and Monday (Lieldienas), Pentecost (Vasarsvētki)

UNKNOWN_LV = "nav zināms"


def _w(ts):
    return when_text_lv(ts) if ts else UNKNOWN_LV


def receipt_lv(stmt, *, order, name, money, by_day, last_day, seller):
    """The "lv" branch of receipt_mail(). withdraw.py passes what it computes for English: order (or the echoed
    order given), name = echo_name(...), money = _money(stmt, "lv") with price_text_lv in the order's currency,
    by_day = the refund-by day "YYYY-MM-DD", last_day = _last_day(stmt) for a lapsed period, seller =
    seller_lines_lv(pack)."""
    got = when_text_lv(stmt["received_at"], seconds=True)
    rows = [("Saņemts", got), ("Pasūtījums", order), ("Vārds un uzvārds", name or "-"),
            ("E-pasta adrese šim apstiprinājumam", stmt["email"])]
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    by = date_text_lv(by_day)
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        what = ["Šim pasūtījumam nekas netiks veidots. Kad atteicāties no līguma, jūsu maksājums vēl tika apstrādāts. "
                "Ja tas mūs sasniegs, atmaksāsim to pilnībā ar to pašu maksāšanas līdzekli, ar kuru maksājāt, ne vēlāk "
                "kā 14 dienu laikā. Par to jums nekas nav jāmaksā."]
    elif outcome == "withdrawn":
        first = ""
        if stmt.get("already") and stmt.get("first_at"):
            first = f" (jūsu atteikumu bijām saņēmuši jau agrāk: {_w(stmt['first_at'])})"
        what = [f"Jūsu atteikums no līguma ir spēkā{first}. Jūsu pasūtījums ir apturēts: nekas netiks veidots. Kā "
                f"norādīts mūsu informācijā par atteikuma tiesībām, samaksāto summu ({money}) atmaksāsim bez "
                f"nepamatotas kavēšanās, ne vēlāk kā {by}, ar to pašu maksāšanas līdzekli, ar kuru maksājāt. Par to "
                f"jums nekas nav jāmaksā."]
    elif outcome == "lapsed" and reason == "period_over":
        end = date_text_lv(last_day)
        what = [f"14 dienu atteikuma termiņš šim pasūtījumam beidzās {end}, tāpēc jūsu atteikuma tiesības jau bija "
                f"beigušās, kad saņēmām jūsu paziņojumu. Jūsu paziņojumu tomēr izskatīsim personīgi un atbildēsim "
                f"jums e-pastā."]
    else:   # lapsed: making began after the consent and the confirmation
        what = [f"Pasūtot jūs skaidri piekritāt, ka jūsu failu sākam veidot uzreiz, un apliecinājāt, ka līdz ar to "
                f"zaudējat atteikuma tiesības, tiklīdz esam sākuši (jūsu piekrišanas laiks: "
                f"{_w(stmt.get('consent_at'))}). To jums apstiprinājām pasūtījuma apstiprinājuma e-pastā (nosūtīts: "
                f"{_w(stmt.get('confirmation_at'))}), un jūsu failu sākām veidot (sākums: "
                f"{_w(stmt.get('began_at'))}). Tāpēc jūsu atteikuma tiesības jau bija beigušās, kad saņēmām jūsu "
                f"paziņojumu. Jūsu pasūtījums paliek spēkā, un failu saņemat savā pasūtījuma lapā.",
                "Jūsu paziņojumu tomēr izskatīsim personīgi un atbildēsim jums e-pastā. Tas neietekmē jūsu likumīgās "
                "tiesības, ja failam ir trūkumi."]
    moved = []
    if stmt.get("email_given"):
        moved = ["Šim apstiprinājumam jūs norādījāt citu adresi. Sūtām to uz e-pasta adresi, ar kuru maksājāt, jo par "
                 "šo pasūtījumu jau vairāki apstiprinājumi ir nosūtīti uz citām adresēm."]
    subject = f"Esam saņēmuši jūsu atteikumu: SnapEyes pasūtījums {order}"
    blocks = [("p", GREETING_LV),
              ("p", "Esam saņēmuši jūsu paziņojumu par atteikumu no līguma. Šis e-pasts apstiprina tā saņemšanu; lūdzu, "
                    "saglabājiet to.")] + [
              ("p", x) for x in moved] + [
              ("h", "Jūsu paziņojums par atteikumu"), ("rows", rows), ("quote", quoted_lv(stmt["text"])),
              ("h", "Kas notiks tālāk")] + [("p", x) for x in what] + [
              ("p", QUESTIONS_LV), ("p", SIGN_OFF_LV), ("p", seller)]
    return subject, blocks


def unmatched_lv(stmt, *, given, name, seller):
    """The "lv" branch of unmatched_mail(): the NEUTRAL receipt for a statement that matched no order. It says
    nothing about any order. given = echo_order(...) or "-", name = echo_name(...)."""
    rows = [("Saņemts", when_text_lv(stmt["received_at"], seconds=True)),
            ("Norādītais pasūtījuma numurs", given),
            ("Vārds un uzvārds", name or "-"),
            ("E-pasta adrese šim apstiprinājumam", stmt["email"])]
    said = quoted_lv(STATEMENT_LV.format(order=given))
    subject = "Esam saņēmuši jūsu paziņojumu par atteikumu: SnapEyes"
    blocks = [("p", GREETING_LV),
              ("p", "Esam saņēmuši jūsu paziņojumu par atteikumu no līguma. Šis e-pasts apstiprina tā saņemšanu; lūdzu, "
                    "saglabājiet to."),
              ("h", "Jūsu paziņojums par atteikumu"), ("rows", rows), ("quote", said),
              ("h", "Kas notiks tālāk"),
              ("p", "Pēc šiem datiem jūsu paziņojumu nevarējām automātiski sasaistīt ne ar vienu pasūtījumu. "
                    "Pārbaudīsim to personīgi un atbildēsim jums e-pastā."),
              ("p", "Ja jums ir pasūtījuma apstiprinājuma e-pasts, varat izmantot arī tajā esošo atteikuma saiti. Vai "
                    "arī vienkārši atbildiet uz šo e-pastu un norādiet sava pasūtījuma numuru."),
              ("p", SIGN_OFF_LV), ("p", seller)]
    return subject, blocks
