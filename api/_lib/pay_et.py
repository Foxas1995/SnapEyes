"""Estonian ("et") strings and email texts for api/_lib/pay.py, key for key (the twin of pay_hr.py).

What is here, and where pay.py uses it once "et" is in LANGS:
  SELLER_ET            SELLER["et"]            the seller line of the short emails when the legal pack is missing
  CONSENT_TEXT_ET      CONSENT_TEXT["et"]      word for word src/shared/legal.ts CHECKOUT_LEGAL.et.withdrawalConsent
  SUBMIT_NOTE_ET       SUBMIT_NOTE["et"]       Stripe's note above its pay button (custom_text.submit), with the
                                               order button words of Art. 8(2) Directive 2011/83/EU in Estonian,
                                               „tellimus koos maksekohustusega“ (Võlaõigusseadus § 62¹ lg 3)
  ITEM_DESC_ET         ITEM_DESC["et"]         the Stripe line item's description
  item_name_et()       item_name() for "et"
  price_text_et()      price_text() for "et": "24,97 €" (EUR); amount_text_et() the plain one ("24,97 EUR")
  when_text_et()       when_text() for "et": "29.09.2026 kell 10:15 UTC"
  date_text_et()       date_text() for "et": "29.09.2026"
  quoted_et()          quoted() for "et": „...“
  seller_lines_et()    seller_lines() for "et"
  confirmation_et()    the "et" branch of confirmation_mail(): (subject, blocks) before the legal texts are appended
  ready_et()           the "et" branch of ready_mail(): (subject, blocks)
  et_form()            the Estonian noun form after a number (1 silm, 2 silma), a helper of item_name_et

Estonian: Estonia pays in euros, so a price is the euro amount as Estonians write it, "24,97 €" (decimal comma,
no-break space before the sign, thousands with a no-break space), as pay_lt.py does for Lithuania and
src/shared/markets.ts money() does on the page. Dates are numeric, day.month.year with two digits for the day and the
month and no spaces ("29.09.2026"), so a mail client cannot break one across lines; a date has no final dot of its own,
so a sentence may end right after one. A noun after a number has two forms (et_form): the nominative after 1, the
partitive after every other number. Informal singular "sina", as the Estonian page writes; the legal texts appended to
the confirmation are formal. The greeting carries no name. The withdrawal right is "taganemisõigus" and the online
function's label „Taganen lepingust“ (Võlaõigusseadus § 56⁴, Art. 11a Directive 2011/83/EU).
The confirmation is the durable-medium confirmation of Art. 8(7) Directive 2011/83/EU: it repeats the consent
checkbox word for word and confirms it, before anything is made (as the English one does).
No en or em dashes anywhere (owner rule). Stand-alone on purpose: no import of pay, so it can be reviewed and tested
on its own; pay.py passes in what it has computed.
"""
import calendar
import time
from . import catalogue
from . import words as W

SELLER_ET = "MB „Portretizuokis“, registrikood: 305605052, Gedimino g. 22A-14, LT-44319 Kaunas, Leedu"

# The withdrawal waiver, word for word as the checkout shows it (src/shared/legal.ts CHECKOUT_LEGAL.et). Adding it means a new
# CONSENT_VERSION in pay.py AND src/shared/legal.ts together (old versions keep their texts in CONSENT_TEXTS). Both elements of
# Art. 16(m) Directive 2011/83/EU (Võlaõigusseadus § 53 lg 4 p 7¹): the express consent to start before the period ends, and
# the knowledge of losing the right.
CONSENT_TEXT_ET = ("Nõustun sõnaselgelt, et SnapEyes alustab minu digitaalse kunstiteose valmistamist kohe, enne "
                   "taganemistähtaja lõppu. Olen teadlik, et kaotan oma taganemisõiguse, kui valmistamine on alanud.")

# Stripe shows this right above its pay button, the click that makes the order binding: so the statutory words of
# Art. 8(2) Directive 2011/83/EU in Estonian („tellimus koos maksekohustusega“) stand at that click too.
SUBMIT_NOTE_ET = ("Ostad digitaalse faili (JPEG, 4096 px). Trükitud pilti ega raami me ei saada. Nõustusid, et alustame "
                  "kohe ja et sinu taganemisõigus lõpeb, kui oleme alustanud. Maksenupule vajutades esitad tellimuse "
                  "koos maksekohustusega.")

ITEM_DESC_ET = "Ainult digitaalne fail: JPEG, 4096 px pikimal küljel. Ei trükitud pilti ega raami."

STYLE_NAMES = catalogue.names()      # the brand name of every style id, English in every language (api/_lib/styles_registry.py)

# the months as Estonian writes a date in words ("29. september 2026"); the emails write dates in numbers
# ("29.09.2026", the common form in Estonian mail), so these are only for a caller that wants the word
MONTHS_ET = ("jaanuar", "veebruar", "märts", "aprill", "mai", "juuni", "juuli", "august", "september", "oktoober",
             "november", "detsember")

NBSP = " "


def et_form(n, one, other):
    """The Estonian noun form after a number: one (1 only: the nominative), other (0, 2, 3 ... 21 ...: the partitive)."""
    return one if abs(int(n)) == 1 else other


def item_name_et(spec, layout=True):
    """The Stripe line item and the confirmation's "Kunstiteos" row: "SnapEyesi iirisekunstiteos, 2 silma, Clean Iris,
    4096 px digitaalne fail". The style is as an order prints it (catalogue.style_label: the look is part of it, "Universe, Vortex");
    a style of the v3 engine with two or more eyes names its layout after the style ("3 silma, Family Colours, Triangle, ...") unless
    layout is False (the confirmation adds its own "paigutus: ..." phrase). The layout word is catalogue.layout_name("et", ...): English
    until api/_lib/layout_names.py has Estonian words."""
    n, style = int(spec["eyes"]), catalogue.style_label(spec["style"], int(spec["eyes"]), spec.get("opts"))
    word = ""
    if layout and n > 1 and catalogue.known(spec["style"]) and not catalogue.is_legacy(spec["style"]):
        word = catalogue.layout_name("et", spec.get("layout"))
    eyes = et_form(n, "silm", "silma")
    return f"SnapEyesi iirisekunstiteos, {n} {eyes}, {style}{', ' + word if word else ''}, 4096 px digitaalne fail"


def _group(n):
    """Thousands with a no-break space ("1 000"); below 10 000 too, as the euro amounts here never reach it."""
    return f"{int(n):,}".replace(",", NBSP)


def price_text_et(minor, currency="eur"):
    """A price as the Estonian site shows it, in the currency the order was paid in: "24,97 €" (EUR, Estonia's currency).
    HUF (an Estonian-language order on the forint list, unlikely): Stripe sends it as a two-decimal amount, shown in whole
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


def amount_text_et(minor, currency="eur"):
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
    """"29.09.2026" of a struct_time: day.month.year, two digits for the day and the month, no spaces."""
    return f"{g.tm_mday:02d}.{g.tm_mon:02d}.{g.tm_year}"


def when_text_et(ts, seconds=False):
    """A moment for a customer: "29.09.2026 kell 10:15 UTC". ts: unix seconds or an ISO text."""
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
    return f"{_day(g)} kell {hm} UTC"


def date_text_et(day_iso):
    """A date for a customer from "YYYY-MM-DD": "29.09.2026"."""
    try:
        g = time.strptime(str(day_iso)[:10], "%Y-%m-%d")
    except ValueError:
        return str(day_iso)
    return _day(g)


def quoted_et(text):
    return f"„{text}“"


def seller_lines_et(pack=None, contact="info@snapeyes.com"):
    """The seller as an Estonian email signs: company and code, address, representative and phone when set, email.
    pack: the legal pack (its seller company/address in "et" once plain.ts LANGS has "et")."""
    s = (pack or {}).get("seller") if isinstance(pack, dict) else None
    if not isinstance(s, dict) or not isinstance((s.get("company") or {}).get("et"), str):
        return SELLER_ET.replace(", Gedimino", "\nGedimino") + f"\nE-post: {contact}"
    out = [f"{s['company']['et']}, registrikood: {s['code']}", s["address"]["et"]]
    if s.get("representative"):
        out.append(f"Esindaja: {s['representative']}")
    if s.get("phone"):
        out.append(f"Telefon: {s['phone']}")
    out.append(f"E-post: {s.get('email') or contact}")
    return "\n".join(out)


SIGN_OFF_ET = "Parimate soovidega\nSnapEyes"
QUESTIONS_ET = "Küsimusi? Vasta lihtsalt sellele e-kirjale."
GREETING_ET = "Tere!"
BUTTON_ET = "Taganen lepingust"       # src/shared/legal.ts WITHDRAWAL_ONLINE.et.button (Võlaõigusseadus § 56⁴ lg 1)


def confirmation_et(*, order, spec, n, layout, price, paid_at, consent_at, consent_text, auto, link, wlink,
                    terms_url, updated_day, seller):
    """The "et" branch of confirmation_mail(): (subject, blocks). pay.py computes what it computes for English
    (link, wlink, price with price_text_et, layout as catalogue.layout_name("et", id) gives it, auto = server_starts(pack), the terms URL and
    the pack's "updated" day, seller = seller_lines_et(pack)) and then appends the rule and the two legal texts."""
    rows = [("Tellimuse number", order),
            ("Lepingu sõlmimise aeg", when_text_et(paid_at)),
            ("Kunstiteos", item_name_et(dict(spec, eyes=n), False) + (f", paigutus: {layout}" if n > 1 and layout else ""))]
    names = W.names_text(spec.get("names"))
    if names:
        rows.append(("Nimed kunstiteosel", names))
    if spec.get("title"):
        rows.append(("Pealkiri kunstiteosel", spec["title"]))
    if spec.get("date"):
        rows.append(("Kuupäev kunstiteosel", spec["date"]))
    rows += [("Üleandmine", "digitaalne fail (JPEG, 4096 px pikimal küljel) sinu tellimuse lehel; trükitud pilti ega "
                            "raami me ei saada"),
             ("Hind", f"{price}. See on lõpphind: me ei ole käibemaksukohustuslane, seega käibemaksu ei "
                      f"lisandu."),
             ("Maksmine", "makstud Stripe’i kaudu")]
    subject = f"Sinu SnapEyesi tellimus {order}: tellimuse kinnitus"
    blocks = [
        ("p", GREETING_ET),
        ("p", "Aitäh tellimuse eest. See e-kiri kinnitab sinu lepingut meiega. Palun hoia see alles: selles on sinu "
              "tellimus, sinu nõusolek kohe alustada, taganemisõiguse teave koos taganemisavalduse tüüpvormiga ja meie "
              "müügitingimused."),
        ("h", "Sinu tellimuse leht"),
        ("link", link),
        ("p", ("Hakkame sinu kunstiteost valmistama kohe pärast selle e-kirja saatmist; sa ei pea ühtki lehte avatuna "
               "hoidma. Tavaliselt on see valmis mõne minutiga: faili laadid alla oma tellimuse lehelt ja kui see on "
               "valmis, saadame sulle e-kirja. "
               if auto else
               "Kui selle avad, hakkame sinu kunstiteost valmistama (tavaliselt on see valmis mõne minutiga) ja sealt "
               "laadid faili alla. ") +
              "Palun hoia see link enda teada: igaüks, kellel see on, saab sinu kunstiteose alla laadida."),
        ("h", "Sinu tellimus"),
        ("rows", rows),
        ("h", "Sinu nõusolek kohe alustada"),
        ("p", f"Enne maksmist ({when_text_et(consent_at)}) märkisid selle kasti:"),
        ("quote", quoted_et(consent_text)),
        ("p", "Kinnitame sinu sõnaselget nõusolekut ja sinu kinnitust, et oled selle tagajärjest teadlik. Hakkame sinu "
              "faili valmistama alles pärast selle e-kirja saatmist. Kui oleme alustanud, on sinu taganemisõigus "
              "lõppenud."),
        ("h", "Sinu taganemisõigus"),
        ("p", "Hakkame sinu faili valmistama kohe pärast selle e-kirja saatmist, seega lõpeb sinu taganemisõigus "
              "tavaliselt juba mõne hetke pärast. Kuni me ei ole alustanud, saad lepingust taganeda nupuga "
              f"„{BUTTON_ET}“ oma tellimuse taganemislehel:"
         if auto else
              f"Kuni me ei ole alustanud, saad lepingust taganeda nupuga „{BUTTON_ET}“ oma tellimuse taganemislehel. "
              "See link avab selle lehe, ilma et sinu faili valmistamine algaks (erinevalt ülal olevast tellimuse lehe "
              "lingist):"),
        ("link", wlink),
        ("p", "Lepingust saad taganeda ka e-kirjaga aadressil info@snapeyes.com või taganemisavalduse tüüpvormiga. "
              "Kogu taganemisõiguse teave on selle e-kirja lõpus."),
        ("h", "Meie müügitingimused"),
        ("p", f"Sinu tellimuse suhtes kehtivad meie müügitingimused seisuga {date_text_et(updated_day)}. Nende "
              f"täistekst on selle e-kirja lõpus; võid neid lugeda ka siit:"),
        ("link", terms_url),
        ("p", QUESTIONS_ET),
        ("p", SIGN_OFF_ET),
        ("p", seller),
    ]
    return subject, blocks


def ready_et(*, order, link, checked, seller):
    """The "et" branch of ready_mail(): (subject, blocks)."""
    subject = "Sinu SnapEyesi kunstiteos on valmis"
    blocks = [("p", GREETING_ET),
              ("p", ("Sinu iirisekunstiteos on valmis ja kontrollitud." if checked else
                     "Sinu iirisekunstiteos on valmis.") +
                    " Laadi see alla oma tellimuse lehelt:"),
              ("link", link), ("p", f"Tellimus: {order}"), ("p", QUESTIONS_ET),
              ("p", SIGN_OFF_ET), ("p", seller)]
    return subject, blocks
