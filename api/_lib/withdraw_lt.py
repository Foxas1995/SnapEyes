"""Lithuanian strings of api/_lib/withdraw.py: the withdrawal statement the order page sends and the two receipts (the
acknowledgement of receipt on a durable medium, CK 6.228(10) straipsnio 14 dalis; Art. 11a(4) Directive 2011/83/EU).
withdraw.py uses them for an order whose language is "lt". Block lists are the English branch's, block for block.

Dates and times come from api/_lib/pay_lt.py (when_text_lt, date_text_lt, price_text_lt, quoted_lt, seller_lines_lt), as
the English ones come from pay.py. The greeting has no name (see pay_lt.py).

Keep in step with:
  STATEMENT_LT == src/order/copy.lt.ts withdraw.statement ({order} there); the order page shows it before the customer
                  presses "Patvirtinti sutarties atsisakymą", and the server stores it
"""

# withdraw.STATEMENT["lt"]
STATEMENT_LT = ("Pranešu, kad atsisakau sutarties, kurią sudariau dėl šio skaitmeninio turinio teikimo: SnapEyes "
                "kūrinys, užsakymas {order}.")

RECEIPT_LT = {
    "subject": "Gavome Jūsų pareiškimą apie sutarties atsisakymą: SnapEyes užsakymas {order}",
    "hello": "Laba diena,",
    "intro": "Jūsų pareiškimą apie sutarties atsisakymą gavome. Šis el. laiškas patvirtina jo gavimą; išsaugokite jį.",
    "row_received": "Gavimo laikas",
    "row_order": "Užsakymas",
    "row_name": "Vardas ir pavardė",
    "row_email": "El. paštas šiam patvirtinimui",
    "unknown": "nežinoma",
    "h_statement": "Jūsų pareiškimas apie sutarties atsisakymą",
    "h_next": "Kas vyksta toliau",
    # outcome "withdrawn", reason payment_settling / payment_unknown
    "settling": ("Pagal šį užsakymą nieko nebus kuriama. Kai atsisakėte sutarties, Jūsų mokėjimas dar buvo "
                 "apdorojamas. Jei jis mus pasieks, visą sumą grąžinsime tuo pačiu mokėjimo būdu, kuriuo mokėjote, "
                 "ne vėliau kaip per 14 dienų. Jokių mokesčių už tai nemokėsite."),
    # outcome "withdrawn": {first} is "" or first_note below
    "first_note": " (Jūsų pareiškimą apie sutarties atsisakymą jau buvome gavę {when})",
    "withdrawn": ("Jūsų sutarties atsisakymas įsigaliojo{first}. Jūsų užsakymas sustabdytas: nieko nebus kuriama. "
                  "Kaip nurodyta mūsų informacijoje apie teisę atsisakyti sutarties, sumokėtą sumą ({money}) "
                  "grąžinsime nedelsdami, ne vėliau kaip iki {by}, tuo pačiu mokėjimo būdu, kuriuo mokėjote. Jokių "
                  "mokesčių už tai nemokėsite."),
    # outcome "lapsed", reason period_over
    "period_over": ("Šio užsakymo 14 dienų sutarties atsisakymo terminas baigėsi {end}, todėl, kai gavome Jūsų "
                    "pareiškimą, Jūsų teisė atsisakyti sutarties jau buvo pasibaigusi. Jūsų pareiškimą vis tiek "
                    "asmeniškai peržiūrėsime ir atsakysime el. paštu."),
    # outcome "lapsed": making began after the consent and the confirmation (two paragraphs)
    "began": ("Užsakymo metu aiškiai sutikote, kad Jūsų failą pradėtume kurti iš karto, ir pripažinote, kad pradėjus "
              "kurti netenkate teisės atsisakyti sutarties (Jūsų sutikimo laikas: {consent_at}). Tai patvirtinome "
              "užsakymo patvirtinimo el. laiške, išsiųstame {confirmation_at}, o Jūsų failą pradėjome kurti "
              "{began_at}. Todėl, kai gavome Jūsų pareiškimą, Jūsų teisė atsisakyti sutarties jau buvo pasibaigusi. "
              "Jūsų užsakymas lieka galioti ir failą gausite savo užsakymo puslapyje."),
    "began_help": ("Jūsų pareiškimą vis tiek asmeniškai peržiūrėsime ir atsakysime el. paštu. Tai neturi įtakos Jūsų "
                   "įstatymų numatytoms teisėms, jei failas turi trūkumų."),
    # the receipt went to the payment email instead of the given address (_receipt_to)
    "moved": ("Šiam patvirtinimui nurodėte kitą adresą. Siunčiame jį el. pašto adresu, kurį nurodėte apmokėjimo metu, "
              "nes dėl šio užsakymo kitais adresais jau išsiųsti keli patvirtinimai."),
    "questions": "Turite klausimų? Tiesiog atsakykite į šį el. laišką.",
    "sign": "Pagarbiai\nSnapEyes",
}


def receipt_what_lt(outcome, reason, money="", by="", end="", first_when=None, consent_at="", confirmation_at="",
                    began_at=""):
    """The "Kas vyksta toliau" paragraphs of withdraw.receipt_mail for "lt", branch for branch the English ones.
    money: pay_lt.price_text_lt(amount); by, end: pay_lt.date_text_lt(...); first_when and the three moments:
    pay_lt.when_text_lt(...) (or RECEIPT_LT["unknown"])."""
    r = RECEIPT_LT
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        return [r["settling"]]
    if outcome == "withdrawn":
        first = r["first_note"].format(when=first_when) if first_when else ""
        return [r["withdrawn"].format(first=first, money=money, by=by)]
    if outcome == "lapsed" and reason == "period_over":
        return [r["period_over"].format(end=end)]
    return [r["began"].format(consent_at=consent_at, confirmation_at=confirmation_at, began_at=began_at),
            r["began_help"]]


def receipt_blocks_lt(rows, statement_quoted, what, moved, seller):
    """withdraw.receipt_mail's blocks for "lt": rows = receipt_rows_lt(...), statement_quoted =
    pay_lt.quoted_lt(stmt["text"]), what = receipt_what_lt(...), moved = bool(stmt.get("email_given"))."""
    r = RECEIPT_LT
    return ([("p", r["hello"]), ("p", r["intro"])] + ([("p", r["moved"])] if moved else []) +
            [("h", r["h_statement"]), ("rows", rows), ("quote", statement_quoted), ("h", r["h_next"])] +
            [("p", x) for x in what] +
            [("p", r["questions"]), ("p", r["sign"]), ("p", seller)])


def receipt_rows_lt(received_text, order, name, email):
    r = RECEIPT_LT
    return [(r["row_received"], received_text), (r["row_order"], order), (r["row_name"], name or "-"),
            (r["row_email"], email)]


UNMATCHED_LT = {
    "subject": "Gavome Jūsų pareiškimą apie sutarties atsisakymą: SnapEyes",
    "hello": "Laba diena,",
    "intro": "Jūsų pareiškimą apie sutarties atsisakymą gavome. Šis el. laiškas patvirtina jo gavimą; išsaugokite jį.",
    "row_received": "Gavimo laikas",
    "row_order_given": "Nurodytas užsakymo numeris",
    "row_name": "Vardas ir pavardė",
    "row_email": "El. paštas šiam patvirtinimui",
    "h_statement": "Jūsų pareiškimas apie sutarties atsisakymą",
    "h_next": "Kas vyksta toliau",
    "checking": ("Pagal šiuos duomenis Jūsų pareiškimo nepavyko automatiškai susieti su užsakymu. Jį peržiūrėsime "
                 "asmeniškai ir atsakysime Jums el. paštu."),
    "link_hint": ("Jei turite užsakymo patvirtinimo el. laišką, taip pat galite pasinaudoti jame esančia sutarties "
                  "atsisakymo nuoroda. Arba tiesiog atsakykite į šį el. laišką ir nurodykite savo užsakymo numerį."),
    "sign": "Pagarbiai\nSnapEyes",
}


def unmatched_blocks_lt(received_text, given, name, email, statement_quoted, seller):
    """withdraw.unmatched_mail's blocks for "lt" (the NEUTRAL receipt: nothing about any order).
    statement_quoted = pay_lt.quoted_lt(STATEMENT_LT.format(order=given))."""
    u = UNMATCHED_LT
    rows = [(u["row_received"], received_text), (u["row_order_given"], given), (u["row_name"], name or "-"),
            (u["row_email"], email)]
    return [("p", u["hello"]), ("p", u["intro"]), ("h", u["h_statement"]), ("rows", rows),
            ("quote", statement_quoted), ("h", u["h_next"]), ("p", u["checking"]), ("p", u["link_hint"]),
            ("p", u["sign"]), ("p", seller)]
