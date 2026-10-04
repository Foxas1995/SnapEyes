"""Lithuanian strings of api/_lib/pay.py: what Stripe shows, the order confirmation email and the "ready" email, for an
order whose spec says "lang": "lt" (pay.py LANGS has "lt"; Stripe Checkout runs with locale "lt"). Every block list
below is the English branch's list, block for block, in the same order, so the two emails stay the same email in two
languages (they are rendered with pay.render_mail, as the English ones).

Polite "Jūs" (capitalised in every form), no en or em dashes. The greeting has no name on purpose: a Lithuanian name
after a greeting is in the vocative ("Laba diena, Mantai"), which code cannot build from a typed name, and the
nominative there reads as a form letter.

Keep in step with:
  CONSENT_TEXT_LT   == src/shared/legal.ts CHECKOUT_LEGAL.lt.withdrawalConsent (scripts/check_texts.mjs compares them at
                       build time); a new text needs a new CONSENT_VERSION in pay.py and legal.ts
  WITHDRAW_BUTTON_LT == src/shared/legal.ts WITHDRAWAL_ONLINE.lt.button (CK 6.228(10) str. 11 d.)
"""
import calendar
import time

LANG = "lt"

# pay.SELLER["lt"]: the seller as the short emails sign when the legal pack cannot be read
SELLER_LT = "MB „Portretizuokis“, įmonės kodas 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Lietuva"

# pay.CONSENT_TEXT["lt"] (the withdrawal waiver the customer ticks; CK 6.228(10) str. 2 d. 13 p. a ir b)
CONSENT_TEXT_LT = ("Aiškiai sutinku, kad SnapEyes pradėtų kurti mano skaitmeninį kūrinį iš karto, dar nepasibaigus "
                   "sutarties atsisakymo terminui. Pripažįstu, kad pradėjus kurti kūrinį neteksiu teisės atsisakyti "
                   "sutarties.")

# pay.SUBMIT_NOTE["lt"]: shown by Stripe above its pay button (custom_text.submit). Stripe Checkout itself runs with
# locale "lt" (a locale Stripe supports), so its own labels, the pay button "Mokėti" included, are Lithuanian. Stripe's
# button is the click that makes the order binding, and CK 6.228(8) str. 3 d. asks for "užsakymas su prievole sumokėti"
# (or an equally clear wording) at that click: the last sentence puts the statutory words right above it (as
# pay_hu.SUBMIT_NOTE_HU does with the Hungarian decree's). Not part of the consent, so not part of its version.
SUBMIT_NOTE_LT = ("Perkate skaitmeninį failą (JPEG, 4096 px). Joks spaudinys ar rėmelis nesiunčiamas. Sutikote, kad "
                  "pradėtume iš karto ir kad Jūsų teisė atsisakyti sutarties baigsis, kai tik pradėsime. Paspausdami "
                  "mokėjimo mygtuką, pateikiate užsakymą su prievole sumokėti.")

# pay.ITEM_DESC["lt"]
ITEM_DESC_LT = "Tik skaitmeninis failas: JPEG, ilgoji kraštinė 4096 px. Be spaudinio, be rėmelio."

# the online withdrawal function's button, as the order page and the legal pages name it
WITHDRAW_BUTTON_LT = "Atsisakyti sutarties čia"

# months in the genitive, as Lithuanian writes a date in words ("2026 m. rugsėjo 29 d.")
MONTHS_GEN_LT = ("sausio", "vasario", "kovo", "balandžio", "gegužės", "birželio", "liepos", "rugpjūčio", "rugsėjo",
                 "spalio", "lapkričio", "gruodžio")


def lt_form(n, one, few, many):
    """The Lithuanian noun form after a number: one (1, 21, 31 ...), few (2-9, 22-29 ...), many (0, 10-20, 30 ...)."""
    a = abs(int(n))
    d, h = a % 10, a % 100
    if d == 1 and h != 11:
        return one
    if 2 <= d <= 9 and not 12 <= h <= 19:
        return few
    return many


def item_name_lt(n, style_name):
    """pay.item_name for "lt": "SnapEyes rainelės kūrinys, 2 akys, Celestial Gold, skaitmeninis 4096 px failas"."""
    return f"SnapEyes rainelės kūrinys, {n} {lt_form(n, 'akis', 'akys', 'akių')}, {style_name}, skaitmeninis 4096 px failas"


def amount_text_lt(cents):
    """pay.amount_text for "lt": "19,97 EUR"."""
    return f"{int(cents) // 100},{int(cents) % 100:02d} EUR"


def price_text_lt(cents):
    """pay.price_text for "lt": "19,97 €" (as the site writes a price)."""
    try:
        c = int(cents)
    except (TypeError, ValueError):
        c = 0
    return f"{c // 100},{c % 100:02d} €"


def when_text_lt(ts, seconds=False):
    """pay.when_text for "lt": "2026 m. rugsėjo 29 d. 10:15 UTC". ts: unix seconds or an ISO text."""
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
    return f"{g.tm_year} m. {MONTHS_GEN_LT[g.tm_mon - 1]} {g.tm_mday} d. {hm} UTC"


def date_text_lt(day_iso):
    """pay.date_text for "lt": "2026 m. rugsėjo 29 d." from "YYYY-MM-DD"."""
    try:
        g = time.strptime(str(day_iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(day_iso)
    return f"{g.tm_year} m. {MONTHS_GEN_LT[g.tm_mon - 1]} {g.tm_mday} d."


def quoted_lt(text):
    """pay.quoted for "lt": Lithuanian quotation marks, as the German ones."""
    return f"„{text}“"


# pay.seller_lines: the words it puts around the pack's seller facts
SELLER_WORDS_LT = {"company_code": "įmonės kodas", "represented_by": "Atstovas", "phone": "Telefonas",
                   "email": "El. paštas"}


def seller_lines_lt(pack=None, contact="info@snapeyes.com"):
    """pay.seller_lines for "lt": company and code, address, representative and phone when set, email."""
    s = (pack or {}).get("seller") if isinstance(pack, dict) else None
    if not isinstance(s, dict):
        return SELLER_LT.replace(", Gedimino", "\nGedimino") + f"\n{SELLER_WORDS_LT['email']}: {contact}"
    w = SELLER_WORDS_LT
    out = [f"{s['company'][LANG]}, {w['company_code']} {s['code']}", s["address"][LANG]]
    if s.get("representative"):
        out.append(f"{w['represented_by']}: {s['representative']}")
    if s.get("phone"):
        out.append(f"{w['phone']}: {s['phone']}")
    out.append(f"{w['email']}: {s.get('email') or contact}")
    return "\n".join(out)


# ----------------------------------------------------------------------------- the order confirmation
CONFIRMATION_LT = {
    "subject": "Jūsų SnapEyes užsakymas {order}: užsakymo patvirtinimas",
    "row_order": "Užsakymo numeris",
    "row_contract": "Sutarties sudarymo data",
    "row_artwork": "Kūrinys",
    "layout": "išdėstymas",                 # "..., išdėstymas Greta"
    "row_names": "Vardai kūrinyje",
    "row_title": "Pavadinimas kūrinyje",
    "row_delivery": "Pristatymas",
    "delivery": ("skaitmeninis failas (JPEG, ilgoji kraštinė 4096 px) Jūsų užsakymo puslapyje; joks spaudinys ar "
                 "rėmelis nesiunčiamas"),
    "row_price": "Kaina",
    "price": "{price}. Tai galutinė kaina: MB „Portretizuokis“ nėra PVM mokėtoja, todėl PVM netaikomas.",
    "row_payment": "Mokėjimas",
    "payment": "apmokėta per Stripe",
    "hello": "Laba diena,",
    "intro": ("Dėkojame už Jūsų užsakymą. Šis el. laiškas patvirtina su mumis sudarytą sutartį. Išsaugokite jį: jame "
              "yra Jūsų užsakymas, Jūsų sutikimas, kad pradėtume iš karto, informacija apie teisę atsisakyti sutarties "
              "su pavyzdine sutarties atsisakymo forma ir mūsų pardavimo sąlygos."),
    "h_page": "Jūsų užsakymo puslapis",
    # auto: the server starts right after this email (pay.server_starts(pack)); else the order page starts it
    "page_auto": ("Jūsų kūrinį pradedame kurti iš karto po šio el. laiško išsiuntimo; jokio puslapio laikyti "
                  "atidaryto nereikia. Paprastai jis būna paruoštas per kelias minutes: failą atsisiųsite savo "
                  "užsakymo puslapyje, o kai jis bus paruoštas, parašysime Jums el. laišką. "),
    "page_open": ("Kai jį atidarysite, pradėsime kurti Jūsų kūrinį (paprastai jis būna paruoštas per kelias minutes) "
                  "ir ten atsisiųsite failą. "),
    "page_private": "Niekam neperduokite šios nuorodos: kiekvienas, kas ją turi, gali atsisiųsti Jūsų kūrinį.",
    "h_order": "Jūsų užsakymas",
    "h_consent": "Jūsų sutikimas, kad pradėtume iš karto",
    "consent_when": "Prieš mokėjimą pažymėjote šį langelį ({when}):",
    "consent_confirmed": ("Patvirtiname Jūsų aiškų sutikimą ir pripažinimą. Jūsų failą pradedame kurti tik po šio el. "
                          "laiško išsiuntimo. Kai tik pradedame, Jūsų teisė atsisakyti sutarties baigiasi."),
    "h_withdraw": "Jūsų teisė atsisakyti sutarties",
    "withdraw_auto": ("Jūsų failą pradedame kurti iš karto po šio el. laiško išsiuntimo, todėl Jūsų teisė atsisakyti "
                      "sutarties paprastai baigiasi po kelių akimirkų. Kol dar nepradėjome, sutarties galite "
                      f"atsisakyti mygtuku „{WITHDRAW_BUTTON_LT}“ savo užsakymo sutarties atsisakymo puslapyje:"),
    "withdraw_open": (f"Kol dar nepradėjome, sutarties galite atsisakyti mygtuku „{WITHDRAW_BUTTON_LT}“ savo užsakymo "
                      "sutarties atsisakymo puslapyje. Ši nuoroda jį atidaro, nepradėdama kurti Jūsų failo (kitaip "
                      "nei aukščiau pateikta užsakymo puslapio nuoroda):"),
    "withdraw_other": ("Sutarties taip pat galite atsisakyti el. laišku adresu info@snapeyes.com arba pavyzdine "
                       "sutarties atsisakymo forma. Visa informacija apie teisę atsisakyti sutarties pateikta šio el. "
                       "laiško apačioje."),
    "h_terms": "Mūsų pardavimo sąlygos",
    "terms": ("Jūsų užsakymui taikoma mūsų pardavimo sąlygų redakcija, galiojanti nuo {date}; visas jų tekstas "
              "pateiktas šio el. laiško pabaigoje, o jas taip pat galite perskaityti čia:"),
    "questions": "Turite klausimų? Tiesiog atsakykite į šį el. laišką.",
    "sign": "Pagarbiai\nSnapEyes",
}


def confirmation_rows_lt(order, contract_when, artwork, layout_name, n, names, title, price):
    """The ("rows", ...) of the confirmation, as pay.confirmation_mail builds them for "en": contract_when is
    when_text_lt(paid_at), artwork item_name_lt(n, style), layout_name catalogue.layout_name("lt", layout) or "", price
    price_text_lt(amount_total)."""
    c = CONFIRMATION_LT
    rows = [(c["row_order"], order), (c["row_contract"], contract_when),
            (c["row_artwork"], artwork + (f", {c['layout']} {layout_name}" if n > 1 and layout_name else ""))]
    if names:
        rows.append((c["row_names"], names))
    if title:
        rows.append((c["row_title"], title))
    rows += [(c["row_delivery"], c["delivery"]), (c["row_price"], c["price"].format(price=price)),
             (c["row_payment"], c["payment"])]
    return rows


def confirmation_blocks_lt(link, wlink, rows, consent_at_text, consent_text, auto, updated_text, terms_url, seller):
    """The confirmation's blocks before the attached legal texts, block for block the English branch of
    pay.confirmation_mail. consent_at_text: when_text_lt(consent["at"]); updated_text: date_text_lt(pack["updated"]);
    seller: seller_lines_lt(pack). pay.py then appends [("rule",), ("doc", withdrawal text), ("rule",), ("doc", terms
    text)] from pack["docs"]["lt"]."""
    c = CONFIRMATION_LT
    return [
        ("p", c["hello"]),
        ("p", c["intro"]),
        ("h", c["h_page"]),
        ("link", link),
        ("p", (c["page_auto"] if auto else c["page_open"]) + c["page_private"]),
        ("h", c["h_order"]),
        ("rows", rows),
        ("h", c["h_consent"]),
        ("p", c["consent_when"].format(when=consent_at_text)),
        ("quote", quoted_lt(consent_text)),
        ("p", c["consent_confirmed"]),
        ("h", c["h_withdraw"]),
        ("p", c["withdraw_auto"] if auto else c["withdraw_open"]),
        ("link", wlink),
        ("p", c["withdraw_other"]),
        ("h", c["h_terms"]),
        ("p", c["terms"].format(date=updated_text)),
        ("link", terms_url),
        ("p", c["questions"]),
        ("p", c["sign"]),
        ("p", seller),
    ]


# ----------------------------------------------------------------------------- the "it is ready" email
READY_LT = {
    "subject": "Jūsų SnapEyes kūrinys paruoštas",
    "hello": "Laba diena,",
    "ready_checked": "Jūsų rainelės kūrinys paruoštas ir patikrintas.",
    "ready": "Jūsų rainelės kūrinys paruoštas.",
    "download": " Atsisiųskite jį savo užsakymo puslapyje:",
    "order": "Užsakymas: {order}",
    "questions": "Turite klausimų? Tiesiog atsakykite į šį el. laišką.",
    "sign": "Pagarbiai\nSnapEyes",
}


def ready_blocks_lt(link, order, checked, seller):
    """pay.ready_mail's blocks for "lt", block for block the English ones."""
    r = READY_LT
    return [("p", r["hello"]), ("p", (r["ready_checked"] if checked else r["ready"]) + r["download"]),
            ("link", link), ("p", r["order"].format(order=order)), ("p", r["questions"]),
            ("p", r["sign"]), ("p", seller)]
