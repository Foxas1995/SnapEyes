"""Hungarian ("hu") strings and email texts for api/_lib/withdraw.py, key for key.

  STATEMENT_HU        STATEMENT["hu"]: word for word src/order/copy.hu.ts withdraw.statement (the model form of
                      45/2014. (II. 26.) Korm. rendelet 2. melléklet: „Alulírott ... kijelentem, hogy gyakorlom
                      elállási jogomat ... szerződés tekintetében”)
  HOLIDAYS_HU,        Hungary's public holidays (munkaszüneti napok, Mt. 102. § (1), checked on net.jogtar.hu on
  EASTER_HU           2026-09-29): 1 Jan, 15 Mar, Good Friday, Easter Monday, 1 May, Whit Monday, 20 Aug, 23 Oct,
                      1 Nov, 25-26 Dec. Only 15 Mar, 20 Aug and 23 Oct are new against the LT + DE table; period_end()
                      takes the latest end anywhere, so adding them only ever lengthens a period (the consumer's side).
  receipt_hu()        the "hu" branch of receipt_mail(): (subject, blocks)
  unmatched_hu()      the "hu" branch of unmatched_mail(): (subject, blocks)

The receipt is the „átvételi elismervény” of 22. § (1c): it names the content of the withdrawal and the date and time
it was received. Tone: friendly "te", as the order page's withdrawal form. No en or em dashes (owner rule).
Stand-alone: the dates and the money come in formatted by pay_hu (when_text_hu, date_text_hu, price_text_hu).
"""
from .pay_hu import (GREETING_HU, QUESTIONS_HU, SIGN_OFF_HU, date_text_hu, quoted_hu, when_text_hu)

STATEMENT_HU = ("Alulírott kijelentem, hogy gyakorlom elállási jogomat az alábbi digitális tartalom szolgáltatására "
                "irányuló szerződés tekintetében: SnapEyes-alkotás, rendelésszám: {order}.")

HOLIDAYS_HU = ((1, 1), (3, 15), (5, 1), (8, 20), (10, 23), (11, 1), (12, 25), (12, 26))
EASTER_HU = (-2, 1, 50)                   # Good Friday (nagypéntek), Easter Monday, Whit Monday (pünkösdhétfő)

UNKNOWN_HU = "ismeretlen"


def _w(ts):
    return when_text_hu(ts) if ts else UNKNOWN_HU


def receipt_hu(stmt, *, order, name, money, by_day, last_day, seller):
    """The "hu" branch of receipt_mail(). withdraw.py passes what it computes for English: order (or the echoed
    order given), name = echo_name(...), money = _money(stmt, "hu") with price_text_hu in the order's currency,
    by_day = the refund-by day "YYYY-MM-DD", last_day = _last_day(stmt) for a lapsed period, seller =
    seller_lines_hu(pack)."""
    got = when_text_hu(stmt["received_at"], seconds=True)
    rows = [("Beérkezett", got), ("Rendelés", order), ("Név", name or "-"),
            ("E-mail-cím ehhez az elismervényhez", stmt["email"])]
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    by = date_text_hu(by_day)
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        what = ["Ehhez a rendeléshez semmi nem készül. Amikor elálltál, a fizetésed még feldolgozás alatt állt. Ha "
                "megérkezik hozzánk, legkésőbb 14 napon belül teljes egészében visszatérítjük arra a fizetési módra, "
                "amellyel fizettél. Ez neked semmilyen díjjal nem jár."]
    elif outcome == "withdrawn":
        first = ""
        if stmt.get("already") and stmt.get("first_at"):
            first = f" (az elállásodat már korábban megkaptuk: {_w(stmt['first_at'])})"
        what = [f"Az elállásod hatályos{first}. A rendelésedet leállítottuk: semmi nem készül el. Ahogy az elállási "
                f"tájékoztatónkban is szerepel, a kifizetett összeget ({money}) indokolatlan késedelem nélkül, "
                f"legkésőbb {by} napjáig visszatérítjük arra a fizetési módra, amellyel fizettél. Ez neked semmilyen "
                f"díjjal nem jár."]
    elif outcome == "lapsed" and reason == "period_over":
        end = date_text_hu(last_day)
        what = [f"Ennek a rendelésnek a 14 napos elállási határideje {end} napján lejárt. Így a nyilatkozatod "
                f"beérkezésekor az elállási jogod már megszűnt. A nyilatkozatodat ennek ellenére személyesen is "
                f"megnézzük, és e-mailben válaszolunk."]
    else:   # lapsed: making began after the consent and the confirmation
        what = [f"A rendeléskor kifejezetten hozzájárultál, hogy azonnal megkezdjük a fájlod elkészítését, és "
                f"tudomásul vetted, hogy a kezdéssel elveszíted az elállási jogodat (a hozzájárulásod időpontja: "
                f"{_w(stmt.get('consent_at'))}). Ezt a rendelés visszaigazolását tartalmazó e-mailünkben megerősítettük "
                f"(elküldve: {_w(stmt.get('confirmation_at'))}), a fájlod elkészítését pedig megkezdtük (kezdés: "
                f"{_w(stmt.get('began_at'))}). Így a nyilatkozatod beérkezésekor az elállási jogod már megszűnt. A "
                f"rendelésed érvényben marad, a fájlodat a rendelési oldaladon kapod meg.",
                "A nyilatkozatodat ennek ellenére személyesen is megnézzük, és e-mailben válaszolunk. Hibás fájl esetén "
                "a jogszabályon alapuló jogaidat ez nem érinti."]
    moved = []
    if stmt.get("email_given"):
        moved = ["Ehhez az elismervényhez másik címet adtál meg. Arra az e-mail-címre küldjük, amellyel fizettél, mert "
                 "ehhez a rendeléshez már több elismervény is ment más címekre."]
    subject = f"Megkaptuk az elállásodat: SnapEyes-rendelés {order}"
    blocks = [("p", f"Kedves {name}!" if name else GREETING_HU),
              ("p", "Megkaptuk az elállásodat. Ez az e-mail az átvételi elismervény; kérjük, őrizd meg.")] + [
              ("p", x) for x in moved] + [
              ("h", "Az elállási nyilatkozatod"), ("rows", rows), ("quote", quoted_hu(stmt["text"])),
              ("h", "Mi történik ezután")] + [("p", x) for x in what] + [
              ("p", QUESTIONS_HU), ("p", SIGN_OFF_HU), ("p", seller)]
    return subject, blocks


def unmatched_hu(stmt, *, given, name, seller):
    """The "hu" branch of unmatched_mail(): the NEUTRAL receipt for a statement that matched no order. It says
    nothing about any order. given = echo_order(...) or "-", name = echo_name(...)."""
    rows = [("Beérkezett", when_text_hu(stmt["received_at"], seconds=True)),
            ("Megadott rendelésszám", given),
            ("Név", name or "-"),
            ("E-mail-cím ehhez az elismervényhez", stmt["email"])]
    said = quoted_hu(STATEMENT_HU.format(order=given))
    subject = "Megkaptuk az elállási nyilatkozatodat: SnapEyes"
    blocks = [("p", GREETING_HU),
              ("p", "Megkaptuk az elállási nyilatkozatodat. Ez az e-mail az átvételi elismervény; kérjük, őrizd meg."),
              ("h", "Az elállási nyilatkozatod"), ("rows", rows), ("quote", said),
              ("h", "Mi történik ezután"),
              ("p", "Ezekkel az adatokkal nem tudtuk automatikusan egyetlen rendeléshez sem hozzárendelni a "
                    "nyilatkozatodat. Személyesen ellenőrizzük, és e-mailben válaszolunk."),
              ("p", "Ha megvan a rendelésed visszaigazoló e-mailje, az abban lévő elállási linket is használhatod. Vagy "
                    "egyszerűen válaszolj erre az e-mailre, és írd meg a rendelésszámodat."),
              ("p", SIGN_OFF_HU), ("p", seller)]
    return subject, blocks
