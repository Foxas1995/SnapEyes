# -*- coding: utf-8 -*-
"""The online withdrawal function (Art. 11a Directive 2011/83/EU, added by Directive (EU) 2023/2673 and applied
from 19 June 2026; in Germany § 356a BGB): POST /api/order {action: "withdraw", order, k?, name, email, lang, nonce?}.

The customer gives their name, the order and an email address for the receipt; the order page sends it after its
"Confirm withdrawal" step. Every statement taken is recorded with the time it arrived, whatever it turns out to
mean: a statement taken is never lost (when even storage fails, the owner is emailed the statement before the page
is told to try again). Then:
  - who sent it: the order's link key k proves it; without k, the email address must be the one the order was paid
    with. A statement that matches no order that way is kept apart (withdrawals/<yymm>/) and the owner checks it by
    hand; the page hears 404 not_found (as for an order that does not exist, so nobody learns which orders exist),
    and the given address gets a neutral receipt (the statement, the date and time it arrived, "we are checking
    it"; nothing about any order). On a deployment that cannot have sold anything (pay.sells(): no Stripe keys that
    count, as the live site before launch, and no live payment ever recorded in the bucket) a statement that names
    no stored order is neither stored nor answered by email: 409 with the reason code no_order and recorded false
    ("nothing was recorded, please check the number or email us"; _no_order), so the function is no anonymous
    write path into the bucket there
  - paid, nothing made yet (making.json, a stored eye or artwork), within the period: EFFECTIVE. withdrawn.json stops
    the order (make and compose answer 409 withdrawn), the owner is told to refund the payment within 14 days, and
    the order's images are deleted 14 days later (cleanup/withdrawn/, api/_lib/cleanup.py)
  - paid, making began after the customer's consent and after the order confirmation email: the right had LAPSED
    (Art. 16(m); § 356 Abs. 5 BGB). The statement is still recorded and answered, honestly, with the reason and the
    times; the owner looks at it and replies. Making began without those conditions: effective after all
  - paid, nothing made, and the withdrawal period is over: lapsed. The period is counted as the law counts it
    (Regulation 1182/71 Art. 3; §§ 187(1), 188(1), 193 BGB): the day of the contract is not counted, the period ends
    at the END of the 14th day after it, in the customer's own calendar, and a last day on a Saturday, a Sunday or a
    public holiday moves to the next working day (period_end(): the latest such end anywhere in the EU, so nobody
    loses a day to UTC, to summer time or to a holiday; see "working days" below)
  - not paid: Stripe is asked first. A session paid meanwhile is recorded and handled as paid; one still settling
    (a delayed method) makes the withdrawal effective, and a payment that arrives later is flagged for a refund
    (pay.record_paid). Otherwise there is no contract: open sessions are closed so the order cannot be paid by
    accident, and the page hears 409 not_paid
The receipt (the statement's content with the date and time it arrived) goes to the given address at once, on a
durable medium, for every statement taken except one on an order that was never paid (no contract); when Resend is
busy it is sent again by the daily clean-up (withdrawdue/). Where it goes (_receipt_to):
  - a statement that matched no order: its NEUTRAL receipt, at most RECEIPT_ADDR_MAX a day and
    RECEIPT_ADDR_MONTH_MAX a month to one address, inside DAY_MAX statements a day in all; the typed name and order
    text are echoed without anything a mail client could turn into a link or a phone number (echo_name,
    echo_order), so nobody can make our receipts carry their message
  - a proven statement: to the given address when it is the payment email; another address gets at most
    RECEIPT_OTHER_MAX receipts per order in all (the order link's holder cannot mail strangers without end), then
    the receipt goes to the payment email instead ("redirected")
  - a later statement on an order whose first statement of the same outcome was handled (a repeat: the order is
    withdrawn already, or its right had ended already): at most REPEAT_RECEIPT_ORDER_MAX a day for the order and
    REPEAT_RECEIPT_DAY_MAX a day on the whole site; it changes nothing, and its first statement had its receipt

The owner hears of every statement, in bounded email:
  - the FIRST statement of an order with each outcome (withdrawn: refund it; lapsed: reply personally), proven by
    the link key or the payment email: its own note at once, at most NOTE_DAY_MAX a day on the whole site
  - everything else goes into ONE digest per day, sent by the daily clean-up (cleanup/digest/<day>/, send_digests):
    notes over NOTE_DAY_MAX (p-, flagged NEED ACTION), statements that matched no order (u-, plus one note at once
    for the day's first), those on orders never paid (n-) and repeats (r-)
  - fixed notes, each at most once a day: the day's first unmatched statement, the pause of unmatched statements,
    notes over the daily cap; and when storage fails, at most FALLBACK_MAX emails a day with the statement (capped
    across all instances by Resend's idempotency keys)
That keeps a flood of statements from using up the email provider's daily quota, which the order confirmations need.

The flood guards, each a slot marker written BEFORE the work and counted after it (so a burst cannot all pass a
check made before any of them wrote; no personal data): in withdrawlog/<today>/
  v-<order tag>-<id>     proven statements: ORDER_DAY_MAX per order a day, never a site-wide ceiling
  u-<text tag>-<id>      statements that matched no order: DAY_MAX a day in all (past it the page asks for an
                         email instead), UNMATCHED_TEXT_MAX a day for one typed order text
  r-<address tag>-<id>   neutral receipts: RECEIPT_ADDR_MAX a day to one address
  q-<order tag>-<id>     receipts for repeats: REPEAT_RECEIPT_ORDER_MAX per order, REPEAT_RECEIPT_DAY_MAX in all
  o-n-<id>               owner notes at once: NOTE_DAY_MAX a day
in withdrawaddr/<yymm>/m-<address tag>-<id> (neutral receipts per month; removed by the clean-up after the next
month), and in the order's folder: withdrawal-first-<outcome>.json (which statement was the first) and
withdrawal-to-<id>.json (receipts that went to another address than the payment email).

Storage: orders/<order>/withdrawal_<id>.json (the statement: name, email, time, text, outcome), _ack.json and
_note.json beside it (the two emails, each once), withdrawal.json (the latest statement without personal data: what
the order page shows) and withdrawn.json (the order is stopped). Kept with the order record (privacy policy)."""
import re, time, hmac, hashlib, secrets, threading, datetime
from . import iris as L
from . import store
from . import pay
from . import withdraw_lt, withdraw_hu

NAME_MAX = 100
EMAIL_MAX = 254
DAY_MAX = 20                 # statements that match NO order, taken per UTC day (anyone can send one; past it the
                             # page asks for an email instead). Proven statements never count against it
UNMATCHED_TEXT_MAX = 3       # of those, for one typed order text per day
ORDER_DAY_MAX = 5            # proven statements (link key or payment email) for one order per day
RECEIPT_ADDR_MAX = 2         # neutral receipts (statements that matched no order) per UTC day to one address
RECEIPT_ADDR_MONTH_MAX = 4   # ... and per calendar month (UTC) to one address
RECEIPT_OTHER_MAX = 3        # receipts of proven statements to addresses other than the payment email, per order, ever
REPEAT_RECEIPT_ORDER_MAX = 1  # receipts per order and day for repeats (not the first statement of its outcome)
REPEAT_RECEIPT_DAY_MAX = 5   # ... and per day on the whole site
NOTE_DAY_MAX = 10            # owner notes at once per UTC day (first statements); the rest come in the daily digest
WITHDRAW_DAYS = 14           # the withdrawal period: 14 days after the day of the contract (the payment)
PERIOD_EAST = 4              # hours east of UTC of the EU's easternmost clock (Réunion; Finland to Cyprus are +2/+3)
PERIOD_WEST = -4             # ... and of its westernmost (Guadeloupe, Martinique, Saint-Martin; the Azores are -1/0)
REFUND_DAYS = 14             # the refund is due within 14 days of the withdrawal (Art. 13)
DUE_DAYS = 3                 # a receipt Resend would not take is tried again by the daily clean-up this long
RETRY_SECONDS = 12.0         # the daily clean-up spends at most this long on receipts to send again
DIGEST_SECONDS = 8.0         # ... and at most this long on the owner's digests (a backlog of days goes on next run)
DIGEST_LIST = 40             # statements listed one by one in the owner's daily digest (the rest are counted)
FALLBACK_MAX = 5             # owner emails per day for statements storage could not take (all instances together)
DIGEST_OUTCOMES = ("unmatched", "no_contract")      # the owner hears of these in the daily digest
DIGEST_KINDS = "punr"        # digest entries, in the order the digest lists them: p need action, u matched no order,
                             # n never paid, r repeats
ADDR_TOP = "withdrawaddr"
NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
# what a mail client could turn into a link: a scheme://, www., an address, a domain name (a name never needs one)
_LINKISH = re.compile(r"(?i)(?:\b[a-z][a-z0-9+.-]*://\S*|\bwww\.\S*|\S+@\S+|(?:[\w-]+\.)+[^\W\d_]{2,}\b\S*)")
# what reads as a phone number: seven or more digits, whatever joins them; in a name any run of three digits
_PHONEISH = re.compile(r"\+?\(?\d(?:[\s().\/-]*\d){6,}")
_NAME_DIGITS = re.compile(r"\+?\(?\d(?:[\s().\/-]*\d){2,}")
_ORDERISH = re.compile(r"(?i)#?[0-9]{6}-[0-9a-z]{1,24}")

STATEMENT = {   # as the order page shows it before "Confirm withdrawal" (src/order/copy.ts withdraw.statement)
    "en": "I hereby withdraw from the contract I concluded for the supply of the following digital content: SnapEyes "
          "artwork, order {order}.",
    "de": "Hiermit widerrufe ich den von mir abgeschlossenen Vertrag über die Bereitstellung der folgenden digitalen "
          "Inhalte: SnapEyes-Kunstwerk, Bestellung {order}.",
    "lt": withdraw_lt.STATEMENT_LT,
    "hu": withdraw_hu.STATEMENT_HU,
}


# ----------------------------------------------------------------------------- the request
def _input(body):
    """(name, email, order_given, order or None, k or None, nonce or None, page lang), or ClientError."""
    name = re.sub(r"\s+", " ", pay.clean_text(body.get("name"), NAME_MAX))
    email = body.get("email").strip() if isinstance(body.get("email"), str) else ""
    if not name:
        raise L.ClientError("Please enter your name.")
    if len(email) > EMAIL_MAX or not pay._EMAIL.fullmatch(email):
        raise L.ClientError("Please enter a valid email address.")
    given = pay.clean_text(body.get("order"), 80)
    if not given:
        raise L.ClientError("Please enter your order number.")
    order = given.lower() if store.ORDER_RE.fullmatch(given.lower()) else None
    k = body.get("k") if isinstance(body.get("k"), str) and pay.KEY_RE.fullmatch(body.get("k")) else None
    nonce = body.get("nonce") if isinstance(body.get("nonce"), str) and NONCE_RE.fullmatch(body.get("nonce")) else None
    return name, email, given, order, k, nonce, pay.lang_of(body.get("lang"))


def _statement_id(given, email, nonce, t):
    """A retry with the same nonce finds the same statement; without a nonce every call is a new one."""
    if nonce:
        return "n" + hashlib.sha256(f"{given}|{email.lower()}|{nonce}".encode("utf-8")).hexdigest()[:23]
    return time.strftime("%y%m%d%H%M%S", time.gmtime(t)) + secrets.token_hex(5)


# ----------------------------------------------------------------------------- the ceilings (slots)
def _take(kind, tag, sid, count, folder=None):
    """Take this statement's slot FIRST, then count: <folder>/<kind>-<tag>-<id>.json, folder withdrawlog/<today> by
    default. Returns (path, the names in the folder that start with `count`, ours included; a listing stops at
    1000, which is past every ceiling here). A statement sent again (the same id) finds its slot taken and is
    counted once. Every request that counts its own slot within the ceiling keeps it, so at most the ceiling many
    pass, however many arrive at once (the last of them to count sees all the others' slots)."""
    folder = folder or f"withdrawlog/{pay.day()}"
    path = f"{folder}/{kind}-{tag}-{sid[-10:]}.json"
    try:
        store.put(path, b"{}", "application/json", upsert=False, timeout=6.0)
    except store.StorageExists:
        pass
    names = [r["name"] for r in store.list_folder(folder, limit=1000, timeout=8.0, search=count)
             if not r["folder"] and r["name"].startswith(count)]
    return path, names


def _give_back(path):
    """A refused request's slot goes again (best effort), so refusals never fill the ceiling themselves."""
    try:
        store.delete(path, timeout=5.0, retry=False)
    except store.StorageError as e:
        pay.log(f"withdraw slot not removed: {e}")


def _too_many():
    return store.Answer(429, "too_many", "We already received several withdrawal statements for this order today. "
                        "Please email info@snapeyes.com if something is missing.", False)


def _room(verified, tag, sid):
    """The flood guards before a statement is taken (see the module): a PROVEN statement (verified: the link key
    or the payment email) only against ORDER_DAY_MAX for its order, never against a site-wide ceiling, so nobody
    can switch the function off for real customers; one that matches no order against DAY_MAX a day in all and
    UNMATCHED_TEXT_MAX for one typed order text (its own slots: junk never counts against a real order's)."""
    if verified:
        path, names = _take("v", tag, sid, f"v-{tag}-")
        if len(names) > ORDER_DAY_MAX:
            _give_back(path)
            raise _too_many()
        return
    path, names = _take("u", tag, sid, "u-")
    if len(names) > DAY_MAX:
        _give_back(path)
        pay.note_once(f"notes/withdraw_paused_{pay.day()}.json", "withdraw_paused",
                      "SnapEyes: online withdrawals that match no order paused for today",
                      f"The site received {DAY_MAX} withdrawal statements today that matched no order (the ceiling is "
                      f"DAY_MAX = {DAY_MAX}). Further statements that match no order are refused until 00:00 UTC, "
                      f"and the page asks the sender to email their withdrawal to {pay.CONTACT} instead. Statements "
                      f"that the order link or the payment email proves are NOT affected: customers with their order "
                      f"link can still withdraw online.\nToday's statements come in tomorrow's digest (or: python "
                      f"scripts/order_admin.py withdrawals). If they are real, raise DAY_MAX in "
                      f"api/_lib/withdraw.py.\n")
        raise store.Answer(503, "withdraw_paused", "We cannot take online withdrawals for the moment. Please email your "
                           "withdrawal to info@snapeyes.com: an email is just as valid.", True, 3600)
    if sum(1 for n in names if n.startswith(f"u-{tag}-")) > UNMATCHED_TEXT_MAX:
        _give_back(path)
        raise _too_many()


def _addr_tag(email):
    return hashlib.sha256(b"snapeyes-receipt-v1:" + str(email).strip().lower().encode("utf-8")).hexdigest()[:10]


def receipt_room(stmt):
    """May a NEUTRAL receipt (a statement that matched no order) go to its address? At most RECEIPT_ADDR_MAX a day
    and RECEIPT_ADDR_MONTH_MAX a calendar month to one address (slots like _room's), so a typed address cannot be
    flooded with our receipts."""
    tag = _addr_tag(stmt.get("email"))
    sid = str(stmt.get("id") or secrets.token_hex(5))
    path, names = _take("r", tag, sid, f"r-{tag}-")
    if len(names) > RECEIPT_ADDR_MAX:
        _give_back(path)
        return False
    mpath, mnames = _take("m", tag, sid, f"m-{tag}-", folder=f"{ADDR_TOP}/{time.strftime('%y%m', time.gmtime())}")
    if len(mnames) > RECEIPT_ADDR_MONTH_MAX:
        _give_back(mpath)
        _give_back(path)
        return False
    return True


def _repeat_room(stmt):
    """May the receipt of a REPEAT (a later statement on an order whose first statement of that outcome was
    handled) go out? At most REPEAT_RECEIPT_ORDER_MAX a day for the order and REPEAT_RECEIPT_DAY_MAX a day on the
    whole site."""
    tag = pay._order_tag(stmt.get("order"))
    path, names = _take("q", tag, str(stmt["id"]), "q-")
    if len(names) > REPEAT_RECEIPT_DAY_MAX or sum(1 for n in names if n.startswith(f"q-{tag}-")) > REPEAT_RECEIPT_ORDER_MAX:
        _give_back(path)
        return False
    return True


def _other_room(stmt):
    """May the receipt of a proven statement go to an address that is not the payment email? At most
    RECEIPT_OTHER_MAX such receipts per order, ever (orders/<order>/withdrawal-to-<id>.json)."""
    path, names = _take("withdrawal", "to", str(stmt["id"]), "withdrawal-to-", folder=f"orders/{stmt['order']}")
    if len(names) > RECEIPT_OTHER_MAX:
        _give_back(path)
        return False
    return True


def _note_room(stmt):
    """May the owner's note on this statement go out at once? At most NOTE_DAY_MAX a day on the whole site."""
    path, names = _take("o", "n", str(stmt["id"]), "o-")
    if len(names) > NOTE_DAY_MAX:
        _give_back(path)
        return False
    return True


def _first_of(order, outcome, sid, t):
    """Is this statement the FIRST of its order with this outcome? The first one writes
    orders/<order>/withdrawal-first-<outcome>.json (created once, never overwritten); the same statement again (its
    nonce) finds its own id there."""
    path = pay.order_path(order, f"withdrawal-first-{outcome}.json")
    try:
        store.put(path, store.json_bytes({"id": sid, "t": t}), "application/json", upsert=False, timeout=8.0)
        return True
    except store.StorageExists:
        cur = store.get_json(path, timeout=8.0)
        return isinstance(cur, dict) and cur.get("id") == sid


# ----------------------------------------------------------------------------- the typed texts as our emails echo them
def plain(s):
    """A customer's typed text as our emails echo it: anything a mail client could turn into a link is left out,
    so a typed name or order text never makes our receipt carry someone's link."""
    return re.sub(r"\s+", " ", _LINKISH.sub("[...]", str(s or ""))).strip()


def echo_name(s):
    """The typed name in a receipt: plain(), and no run of digits either (a name needs none; a phone number would
    turn our receipt into someone's call to action)."""
    return re.sub(r"\s+", " ", _NAME_DIGITS.sub("[...]", plain(s))).strip()[:NAME_MAX]


def echo_order(s):
    """The typed order number in a NEUTRAL receipt: as typed when it has the shape of an order number (six digits,
    a dash, letters and digits; a typo in it stays readable), else plain() without anything that reads as a phone
    number."""
    t = re.sub(r"\s+", "", str(s or ""))
    if _ORDERISH.fullmatch(t):
        return t[:40]
    return re.sub(r"\s+", " ", _PHONEISH.sub("[...]", plain(s))).strip()[:80]


# ----------------------------------------------------------------------------- working days
# When the last day of the period is a Saturday, a Sunday or a public holiday, the period ends at the end of the
# next working day: Regulation 1182/71 Art. 3(4) (which recital 41 of Directive 2011/83/EU applies to its periods)
# and § 193 BGB. Whose holidays count is the customer's place, and we do not reliably know the customer's country
# (the order stores no address), so the rule here is the conservative one: every Saturday and Sunday, and every
# national public holiday of Lithuania (the seller's country), of Germany (the main market) or of Hungary (the
# Hungarian market). Holidays of other countries and the holidays of single German states are NOT in it; the owner
# looks at every lapsed statement by hand (the note says so), so a customer whose own holiday was the last day is
# answered personally.
# The dates follow from fixed rules (Easter by the Gregorian computus, easter()), so the table never runs out:
#   Lithuania (Labour Code Art. 123): 1 Jan, 16 Feb, 11 Mar, Easter Sunday and Monday, 1 May, 24 Jun, 6 Jul,
#     15 Aug, 1 Nov, 2 Nov, 24 Dec, 25 Dec, 26 Dec (Mother's and Father's Day are Sundays anyway)
#   Germany, the nine holidays of every state: 1 Jan, Good Friday, Easter Monday, 1 May, Ascension Day,
#     Whit Monday, 3 Oct, 25 Dec, 26 Dec
# For 2026 to 2028 that gives these moving dates (checked against the published calendars on 2026-09-29):
#   2026: Good Friday 3 Apr, Easter 5/6 Apr, Ascension 14 May, Whit Monday 25 May
#   2027: Good Friday 26 Mar, Easter 28/29 Mar, Ascension 6 May, Whit Monday 17 May
#   2028: Good Friday 14 Apr, Easter 16/17 Apr, Ascension 25 May, Whit Monday 5 Jun
# If a country adds or moves a holiday by law, change HOLIDAYS_LT / HOLIDAYS_DE / HOLIDAYS_HU (or their Easter offsets).
# Hungary (Mt. 102. § (1), for the Hungarian market): 1 Jan, 15 Mar, Good Friday, Easter Monday, 1 May, Whit Monday,
# 20 Aug, 23 Oct, 1 Nov, 25 and 26 Dec. Only 15 Mar, 20 Aug and 23 Oct are new against the two above, and the latest end
# anywhere is taken, so adding them only ever lengthens a period, on the consumer's side.
HOLIDAYS_LT = ((1, 1), (2, 16), (3, 11), (5, 1), (6, 24), (7, 6), (8, 15), (11, 1), (11, 2), (12, 24), (12, 25),
               (12, 26))
EASTER_LT = (0, 1)                        # days after Easter Sunday: Easter Sunday, Easter Monday
HOLIDAYS_DE = ((1, 1), (5, 1), (10, 3), (12, 25), (12, 26))
EASTER_DE = (-2, 1, 39, 50)               # Good Friday, Easter Monday, Ascension Day, Whit Monday
HOLIDAYS_HU = withdraw_hu.HOLIDAYS_HU     # Hungary (Mt. 102. § (1)): 1 Jan, 15 Mar, 1 May, 20 Aug, 23 Oct, 1 Nov, 25-26 Dec
EASTER_HU = withdraw_hu.EASTER_HU         # Good Friday, Easter Monday, Whit Monday (only 15 Mar, 20 Aug, 23 Oct are new)
_EPOCH = datetime.date(1970, 1, 1)
_HOLIDAYS = {}                            # year -> the set of its holidays (dates)


def easter(year):
    """Easter Sunday of a Gregorian year (the anonymous Gregorian computus, Meeus/Jones/Butcher)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l) // 433
    month = (h + l - 7 * m + 90) // 25
    return datetime.date(year, month, (h + l - 7 * m + 33 * month + 19) % 32)


def holidays(year):
    """The public holidays of a year that stop a period ending on them: the national ones of Lithuania, Germany and
    Hungary, for every order whatever its market (the latest end anywhere is taken: an English, German or Australian
    order's period also runs past 15 Mar, 20 Aug and 23 Oct, one working day longer, on the consumer's side)."""
    got = _HOLIDAYS.get(year)
    if got is None:
        e = easter(year)
        got = {datetime.date(year, m, d) for m, d in HOLIDAYS_LT + HOLIDAYS_DE + HOLIDAYS_HU}
        got |= {e + datetime.timedelta(days=n) for n in EASTER_LT + EASTER_DE + EASTER_HU}
        _HOLIDAYS[year] = got = frozenset(got)
    return got


def working_day(day):
    """Is this date (datetime.date) a working day: not a Saturday or Sunday, and no holiday in holidays()?"""
    return day.weekday() < 5 and day not in holidays(day.year)


# ----------------------------------------------------------------------------- what the statement means
def period_end(paid_at):
    """(end, last_day) of the withdrawal period of a contract made at paid_at (unix seconds): the day of the
    contract is not counted, the period runs to the END of the 14th day after it (Regulation 1182/71 Art. 3(1)(b),
    (2)(b); §§ 187(1), 188(1) BGB), and when that day is a Saturday, a Sunday or a holiday, to the end of the next
    working day (Art. 3(4); § 193 BGB; working_day()). Days are the customer's own calendar days, and we know
    neither their time zone nor whether summer time changed in between, so the contract's day is taken where it is
    latest (PERIOD_EAST) and the last day's end where it comes latest (PERIOD_WEST): the result is never earlier
    than the period's true end anywhere in the EU, overseas regions included (the time zones make it at most 32
    hours later; a holiday of another of the three countries can add a day or two). end: the first moment after the
    period (unix seconds); last_day: "YYYY-MM-DD", the period's last day (after any move to a working day)."""
    d0 = int((float(paid_at) + PERIOD_EAST * 3600) // 86400)    # the contract's day, as days since 1970
    last = _EPOCH + datetime.timedelta(days=d0 + WITHDRAW_DAYS)
    while not working_day(last):
        last += datetime.timedelta(days=1)
    end = ((last - _EPOCH).days + 1) * 86400 - PERIOD_WEST * 3600
    return end, last.isoformat()


def _began(order, n):
    """(began, when): has making begun for this paid order, and when (unix seconds or None when unknown)."""
    folder = f"orders/{order}"
    res = pay.parallel([lambda: store.get_json(f"{folder}/making.json", timeout=8.0),
                        lambda: store.get_json(f"{folder}/delivery.json", timeout=8.0)] +
                       [lambda i=i: store.exists(f"{folder}/eye_{i}.jpg", timeout=8.0) for i in range(1, n + 1)])
    making, delivery, eyes = res[0], res[1], res[2:]
    when = None
    for rec in (making, delivery):
        if isinstance(rec, dict) and isinstance(rec.get("t" if rec is making else "created_at"), (int, float)):
            when = rec.get("t" if rec is making else "created_at")
            break
    began = isinstance(making, dict) or isinstance(delivery, dict) or any(eyes)
    return began, (when if began else None)


def _assess_paid(order, rec, paid, now):
    """{outcome, reason, ...} for a statement on a PAID order: "withdrawn" or "lapsed", with the facts behind it."""
    spec = paid.get("spec") or {}
    n = int(spec.get("eyes") or 1)
    stopped, mail = pay.parallel([lambda: store.get_json(pay.order_path(order, "withdrawn.json"), timeout=8.0),
                                  lambda: store.get_json(pay.order_path(order, "mail_delivery.json"), timeout=8.0)])
    consent = pay.paid_consent(order, rec, paid)
    facts = {"paid_at": paid.get("paid_at"), "amount": paid.get("amount_total"), "currency": paid.get("currency"),
             "market": pay.paid_market(paid),
             "session_id": paid.get("session_id"), "payment_intent": paid.get("payment_intent"),
             "consent_at": consent.get("at") if consent else None,
             "consent_version": consent.get("version") if consent else None}
    mail_sent = isinstance(mail, dict) and mail.get("state") == "sent"
    mail_t = mail.get("t") if mail_sent and isinstance(mail.get("t"), (int, float)) else None
    facts["confirmation_at"] = mail_t
    if isinstance(stopped, dict):
        return dict(facts, outcome="withdrawn", reason=stopped.get("reason") or "withdrawn", already=True,
                    first_at=stopped.get("t"))
    began, began_at = _began(order, n)
    facts["began_at"] = began_at
    if began:
        in_order = mail_t is None or began_at is None or mail_t <= began_at + 1
        if consent is not None and mail_sent and in_order:
            return dict(facts, outcome="lapsed", reason="making_began")
        # making began without the express consent or before the confirmation: the right did not lapse
        return dict(facts, outcome="withdrawn", reason="began_without_confirmation")
    paid_at = paid.get("paid_at")
    if isinstance(paid_at, (int, float)):
        end, last_day = period_end(paid_at)
        if now >= end:
            return dict(facts, outcome="lapsed", reason="period_over", period_end=end, period_last_day=last_day)
    return dict(facts, outcome="withdrawn", reason="nothing_made")


def _assess_unpaid(order, rec):
    """For a statement on an order without paid.json: ask Stripe first. (assessment, paid record or None)."""
    try:
        sess, settling = pay.close_open_sessions(order, rec)
    except (pay.PayBusy, pay.PayError, pay.PayNotConfigured) as e:
        pay.log(f"order {order}: withdrawal: Stripe could not be asked: {e}")
        if pay.order_sessions(rec):
            return {"outcome": "withdrawn", "reason": "payment_unknown"}, None
        return {"outcome": "no_contract", "reason": "not_paid"}, None
    if sess is not None:
        paid, new = pay.record_paid(order, rec, sess, "withdraw")
        if new:
            pay.note_paid(order, paid)
        return None, paid
    if settling:
        return {"outcome": "withdrawn", "reason": "payment_settling"}, None
    return {"outcome": "no_contract", "reason": "not_paid"}, None


# ----------------------------------------------------------------------------- the action
def withdraw(body):
    """POST /api/order {action: "withdraw", ...}: record the statement, act on it, confirm it. See the module."""
    now = time.time()
    t = int(now)
    name, email, given, order, k, nonce, page_lang = _input(body)
    sid = _statement_id(given, email, nonce, t)
    try:
        return _withdraw(now, t, sid, name, email, given, order, k, nonce, page_lang)
    except store.StorageError:
        _owner_fallback(t, sid, name, email, given, page_lang)
        raise


def _no_order():
    """409 for a statement naming no stored order where nothing can have been sold (pay.sells() false). The reply
    carries the reason code "no_order" (a code of its own: no other reply of /api/order uses it), retry false and
    recorded false, and no "withdrawal" object: nothing was stored and nobody was emailed. The page shows its own
    text for it (we could not find an order with this number, nothing was recorded; check the number or email the
    withdrawal), never the "unmatched" text (that one says the statement was kept)."""
    return store.Answer(409, "no_order", "We could not find an order with this number, so nothing was recorded. Please "
                        "check the order number, or email your withdrawal to info@snapeyes.com: an email is just as "
                        "valid.", False, recorded=False)


def _withdraw(now, t, sid, name, email, given, order, k, nonce, page_lang):
    rec = store.get_json(pay.order_path(order, "order.json"), timeout=8.0) if order else None
    verified = None
    if isinstance(rec, dict) and k and isinstance(rec.get("key_sha"), str) \
            and hmac.compare_digest(rec["key_sha"], pay.key_sha(k)):
        verified = "link"
    paid = pay.get_paid(order) if isinstance(rec, dict) else None
    if isinstance(rec, dict) and not verified and paid and isinstance(paid.get("email"), str) \
            and paid["email"].strip().lower() == email.lower():
        verified = "email"
    if not verified and not isinstance(rec, dict) and not pay.sells():
        # this deployment cannot have taken a payment (no Stripe keys, or test keys where test orders do not
        # count, and no live payment was ever recorded here), and no such order is stored: there is no contract to
        # withdraw from and nothing to keep
        pay.log(f"withdrawal for an order that does not exist, while this deployment sells nothing: not recorded")
        raise _no_order()
    if verified:
        path = pay.order_path(order, f"withdrawal_{sid}.json")
    else:
        path = f"withdrawals/{time.strftime('%y%m', time.gmtime(t))}/{sid}.json"
    if nonce:
        prev = store.get_json(path, timeout=8.0)
        if isinstance(prev, dict):
            # the same statement again (a reply lost on the way): its effects and emails, each once, and its answer
            return _finish(prev, path, repeat=True)
    _room(bool(verified), pay._order_tag(order) if verified else pay._order_tag("text:" + given.lower()), sid)
    if verified:
        lang = pay.lang_of((paid.get("spec") or {}).get("lang") if paid else (rec or {}).get("lang"))
    else:
        lang = page_lang          # never the order's own language: that would tell a stranger the order exists
    stmt = {"v": 1, "id": sid, "received_at": t, "received": pay.iso(t), "order": order if verified else None,
            "order_given": given, "name": name, "email": email, "lang": lang, "page_lang": page_lang,
            "text": STATEMENT[page_lang].format(order=order or given), "verified": verified}
    if not verified:
        stmt.update(outcome="unmatched", reason="order_not_found_or_email_differs")
    else:
        if paid is None:
            a, paid = _assess_unpaid(order, rec)
            if a is not None:
                if a.get("outcome") == "withdrawn":
                    stopped = store.get_json(pay.order_path(order, "withdrawn.json"), timeout=8.0)
                    if isinstance(stopped, dict):
                        a.update(already=True, first_at=stopped.get("t"))
                stmt.update(a)
        if paid is not None:
            stmt.update(_assess_paid(order, rec, paid, now))
            stmt["lang"] = lang = pay.lang_of((paid.get("spec") or {}).get("lang"))
        if stmt.get("outcome") == "withdrawn" and paid is not None and stmt.get("amount"):
            first = stmt.get("first_at") if isinstance(stmt.get("first_at"), (int, float)) else t
            stmt.update(refund="due", refund_by=int(first) + REFUND_DAYS * 86400)
        if stmt.get("outcome") in ("withdrawn", "lapsed"):
            # the first statement of this order with this outcome gets the owner's note at once; later ones (the
            # order is withdrawn already, or its right had ended already) change nothing: they are repeats
            stmt["first"] = (not stmt.get("already")) and _first_of(order, stmt["outcome"], sid, t)
    try:
        store.put(path, store.json_bytes(stmt), "application/json", upsert=False, timeout=10.0)
    except store.StorageExists:
        prev = store.get_json(path, timeout=8.0)
        return _finish(prev if isinstance(prev, dict) else stmt, path, repeat=True)
    pay.log(f"withdrawal {sid}: order {order or '(none)'} {stmt['outcome']} ({stmt.get('reason')}), "
            f"verified {verified or 'no'}{'' if stmt.get('first', True) else ', a repeat'}")
    return _finish(stmt, path, repeat=False)


def _finish(stmt, path, repeat):
    """The statement's effects (stop the order), its two emails and the reply. Idempotent: a repeat does what is
    still missing and answers the same."""
    order, outcome = stmt.get("order"), stmt.get("outcome")
    if order and outcome == "withdrawn":
        _stop(order, stmt)
    if order and outcome == "no_contract":
        pass                      # nothing to stop: the sessions were closed while assessing
    ack = send_receipt(stmt, path)
    note = send_owner_note(stmt, path)
    if ack == "transient" or note == "transient":
        _due(stmt, path)
    if order:
        summary = {"id": stmt["id"], "at": stmt["received_at"], "received": stmt["received"], "state": outcome,
                   "effective": outcome == "withdrawn", "reason": stmt.get("reason"), "mail": _mail_word(ack)}
        try:
            store.put(pay.order_path(order, "withdrawal.json"), store.json_bytes(summary), "application/json",
                      upsert=True, timeout=8.0)
        except store.StorageError as e:
            pay.log(f"order {order}: withdrawal summary not stored: {e}")
    reply = {"id": stmt["id"], "state": outcome, "effective": outcome == "withdrawn" if outcome in ("withdrawn", "lapsed")
             else None, "at": stmt["received_at"], "received": stmt["received"], "mail": _mail_word(ack),
             "reason": stmt.get("reason"), "already": bool(stmt.get("already")) or repeat, "text": stmt.get("text"),
             "name": stmt.get("name"), "email": stmt.get("email")}
    if outcome == "withdrawn" and stmt.get("amount"):
        reply.update(amount=stmt["amount"], currency=pay.currency_of(stmt.get("currency")).upper(), refund="due",
                     refund_by=pay.iso(stmt.get("refund_by")))
    if outcome in ("withdrawn", "lapsed") and pay.market_of(stmt.get("market")):
        # the order's market (a matched order only): the page shows the notes of that market's texts (an Australian
        # order: the Australian Consumer Law next to the end of the withdrawal right), whatever the browser remembers
        reply["market"] = stmt["market"]
    if outcome == "lapsed":
        reply.update(began_at=stmt.get("began_at"), confirmation_at=stmt.get("confirmation_at"),
                     consent_at=stmt.get("consent_at"), period_end=stmt.get("period_end"),
                     period_last_day=stmt.get("period_last_day"))
    if outcome == "unmatched":
        # the same words whatever the reason (no such order, another email, a wrong key): nobody learns which
        # orders exist. "mail" says whether the neutral receipt went to the given address
        raise store.Answer(404, "not_found", "We could not match this to an order with these details. We have recorded "
                           "your statement and will check it by hand; please also check the order number, or email "
                           "info@snapeyes.com.", False, recorded=True, withdrawal=reply)
    if outcome == "no_contract":
        raise store.Answer(409, "not_paid", "This order was never paid, so there is no contract to withdraw from. "
                           "Nothing was charged.", False, recorded=True, withdrawal=reply)
    return {"ok": True, "order": order, "withdrawal": reply}


def _mail_word(ack):
    """The receipt as the page hears it: sent, pending (sent again later), redirected (it went to the payment email,
    not the given address), off (no email here) or not_sent."""
    return {"sent": "sent", "done": "sent", "transient": "pending", "off": "off",
            "redirected": "redirected"}.get(ack, "not_sent")


def _stop(order, stmt):
    """withdrawn.json (make and compose refuse from now on) and the clean-up's note to delete the images later."""
    try:
        store.put(pay.order_path(order, "withdrawn.json"),
                  store.json_bytes({"t": stmt["received_at"], "iso": stmt["received"], "statement": stmt["id"],
                                    "reason": stmt.get("reason")}), "application/json", upsert=False, timeout=8.0)
    except store.StorageExists:
        pass
    try:
        store.put(f"cleanup/withdrawn/{order}.json", store.json_bytes({"t": stmt["received_at"], "order": order}),
                  "application/json", upsert=False, timeout=8.0)
    except store.StorageExists:
        pass


def _due(stmt, path):
    try:
        store.put(f"withdrawdue/{stmt['id']}.json", store.json_bytes({"path": path, "t": int(time.time())}),
                  "application/json", upsert=False, timeout=6.0, retry=False)
    except store.StorageExists:
        pass
    except store.StorageError as e:
        pay.log(f"withdrawal {stmt['id']}: retry mark not stored: {e}")


def retry_due(stop_left=8.0, out=None, max_seconds=RETRY_SECONDS):
    """The daily clean-up's part: send the receipts and owner notes Resend did not take at the time (withdrawdue/).
    At most max_seconds of the run (the deletions after it always get their time; what is left waits for the next
    run, more: true). The owner notes of statements that go into the daily digest are never sent again one by one.
    Gives up after DUE_DAYS. Returns {sent, waiting, dropped} (+ more)."""
    say = out or pay.log
    res = {"sent": 0, "waiting": 0, "dropped": 0}
    until = time.time() + max_seconds
    for row in store.list_all("withdrawdue"):
        if L.time_left() < stop_left or time.time() > until:
            res["more"] = True
            break
        if row["folder"] or not row["name"].endswith(".json"):
            continue
        mark = f"withdrawdue/{row['name']}"
        due = store.get_json(mark, timeout=8.0) or {}
        path = due.get("path") if isinstance(due.get("path"), str) else None
        stmt = store.get_json(path, timeout=8.0) if path else None
        if not isinstance(stmt, dict):
            store.delete(mark, timeout=6.0)
            continue
        ack = send_receipt(stmt, path)
        note = "digest" if stmt.get("outcome") in DIGEST_OUTCOMES else send_owner_note(stmt, path)
        if "transient" not in (ack, note):
            store.delete(mark, timeout=6.0)
            res["sent"] += 1
            say(f"withdrawal {stmt.get('id')}: receipt {ack}, owner note {note}")
        elif time.time() - float(due.get("t") or 0) > DUE_DAYS * 86400:
            store.delete(mark, timeout=6.0)
            res["dropped"] += 1
            say(f"withdrawal {stmt.get('id')}: receipt still not sent after {DUE_DAYS} days, given up")
        else:
            res["waiting"] += 1
    return res


_FALLBACK = {"day": "", "n": 0}
_FALLBACK_LOCK = threading.Lock()


def _owner_fallback(t, sid, name, email, given, page_lang):
    """Storage failed: the statement must not be lost, so the owner gets it by email before the page is told to try
    again (never raises). At most FALLBACK_MAX a day, even across instances: storage cannot count them now, so each
    instance numbers its own 1..FALLBACK_MAX and sends them with the idempotency key <day>-<number>, which Resend
    sends once a day whichever instance asks (another instance's email of the same number is refused, 409). A storage
    outage during a flood therefore cannot use up the email quota; the rest are logged."""
    d = pay.day(t)
    with _FALLBACK_LOCK:
        if _FALLBACK["day"] != d:
            _FALLBACK.update(day=d, n=0)
        _FALLBACK["n"] += 1
        n = _FALLBACK["n"]
    if n > FALLBACK_MAX:
        pay.log(f"withdrawal {sid}: storage failed, owner mail skipped (over {FALLBACK_MAX} today)")
        return
    try:
        res = pay.send_mail(pay.owner_mail(), "SnapEyes: a withdrawal statement arrived but was NOT stored",
                            f"A withdrawal statement arrived at {pay.iso(t)}, but storage did not answer, so it is not "
                            f"stored and the customer was asked to try again.\nOrder given: {plain(given)}\nName: "
                            f"{plain(name)}\nEmail: {email}\nStatement: "
                            f"{STATEMENT[page_lang].format(order=plain(given))}\n\n"
                            f"If no stored statement for this order follows, handle it by hand: it counts from the time "
                            f"above. At most {FALLBACK_MAX} of these emails go out a day; Vercel's logs have the rest "
                            f"(\"storage failed\").\n", f"snapeyes-withdraw-fallback-{d}-{n}")
        pay.log(f"withdrawal {sid}: storage failed, owner mail {res}")
    except Exception as e:  # noqa
        pay.log(f"withdrawal {sid}: storage failed and the owner mail too: {type(e).__name__}")


# ----------------------------------------------------------------------------- the two emails
def _receipt_to(stmt):
    """(address, how) the receipt goes to: how "given" (the address the customer gave) or "paid" (the payment
    email, when the given one had its share); (None, why) when none goes (see the module). Raises StorageError."""
    given = stmt["email"]
    if not stmt.get("verified"):
        return (given, "given") if receipt_room(stmt) else (None, "address_limit")
    if not stmt.get("first", True) and not _repeat_room(stmt):
        return None, "repeat_limit"
    paid = pay.get_paid(stmt["order"])
    paid_email = paid.get("email").strip() if paid and isinstance(paid.get("email"), str) else ""
    if paid_email and paid_email.lower() == str(given).strip().lower():
        return given, "given"
    if _other_room(stmt):
        return given, "given"
    if paid_email and pay._EMAIL.fullmatch(paid_email):
        return paid_email, "paid"
    return None, "other_limit"


def send_receipt(stmt, path):
    """The receipt to the customer (Art. 11a(4) of the directive, § 356a BGB): the statement's content and the date
    and time it arrived, on a durable medium, to the address the customer gave (_receipt_to has the limits). Once
    per statement. A proven statement gets receipt_mail (what it means for the order); one that matched no order
    gets unmatched_mail, a NEUTRAL receipt that says nothing about any order. None for an order that was never paid
    (no contract). Returns send_mail's result, "redirected" (sent to the payment email), "done" (sent before),
    "none", "off", "limited" or "transient"."""
    outcome = stmt.get("outcome")
    if outcome == "no_contract" or not (stmt.get("verified") or outcome == "unmatched"):
        return "none"
    if not pay.email_configured():
        return "off"
    claim = path[:-5] + "_ack.json"
    if not pay.claim_once(claim):
        cur = store.get_json(claim, timeout=8.0)
        cur = cur if isinstance(cur, dict) else {}
        if cur.get("state") == "failed":
            return "limited" if cur.get("result") == "limited" else "failed"
        return "redirected" if cur.get("to") == "paid" else "done"
    try:
        to, how = _receipt_to(stmt)
    except store.StorageError as e:
        pay.log(f"withdrawal {stmt.get('id')}: receipt slot not taken: {e}")
        pay._mark(claim, "retry")
        return "transient"
    if to is None:
        pay._mark(claim, "failed", result="limited", why=how)
        pay.log(f"withdrawal {stmt['id']}: no receipt ({how})")
        return "limited"
    shown = stmt if how == "given" else dict(stmt, email=to, email_given=stmt["email"])
    subject, text, html_body = (receipt_mail if stmt.get("verified") else unmatched_mail)(shown, pay.legal_pack())
    res = pay.send_mail(to, subject, text, f"snapeyes-withdrawal-{stmt['id']}", html_body)
    pay._mark(claim, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res, to=how)
    pay.log(f"withdrawal {stmt['id']}: receipt {res}" + ("" if how == "given" else " (to the payment email)"))
    return "redirected" if res == "sent" and how == "paid" else res


def _money(stmt, lang):
    return pay.price_text(stmt.get("amount") or 0, lang, stmt.get("currency"))


def _last_day(stmt):
    """The last day of the withdrawal period of a lapsed statement, "YYYY-MM-DD"."""
    if isinstance(stmt.get("period_last_day"), str):
        return stmt["period_last_day"]
    return pay.iso(float(stmt.get("period_end") or stmt["received_at"]) - 1)[:10]


def _receipt_other(stmt, pack, lang, order, name):
    """(subject, text, html) of the receipt in Lithuanian or Hungarian (api/_lib/withdraw_lt.py, withdraw_hu.py), the
    same paragraphs as the English one, branch for branch. Neither language belongs to an Australian market, so there
    is no Australian Consumer Law paragraph."""
    seller = pay.seller_lines(lang, pack)
    by_at = stmt.get("refund_by") or stmt["received_at"] + REFUND_DAYS * 86400
    if lang == "hu":
        subject, blocks = withdraw_hu.receipt_hu(stmt, order=order, name=name, money=_money(stmt, lang),
                                                 by_day=pay.iso(by_at), last_day=_last_day(stmt), seller=seller)
    else:
        outcome, reason = stmt.get("outcome"), stmt.get("reason")
        unknown = withdraw_lt.RECEIPT_LT["unknown"]
        w = lambda ts: pay.when_text(ts, lang) if ts else unknown
        first = w(stmt["first_at"]) if stmt.get("already") and stmt.get("first_at") else None
        what = withdraw_lt.receipt_what_lt(
            outcome, reason, money=_money(stmt, lang), by=pay.date_text(pay.iso(by_at), lang),
            end=pay.date_text(_last_day(stmt), lang) if outcome == "lapsed" and reason == "period_over" else "",
            first_when=first, consent_at=w(stmt.get("consent_at")), confirmation_at=w(stmt.get("confirmation_at")),
            began_at=w(stmt.get("began_at")))
        rows = withdraw_lt.receipt_rows_lt(pay.when_text(stmt["received_at"], lang, seconds=True), order, name,
                                           stmt["email"])
        subject = withdraw_lt.RECEIPT_LT["subject"].format(order=order)
        blocks = withdraw_lt.receipt_blocks_lt(rows, pay.quoted(stmt["text"], lang), what, bool(stmt.get("email_given")),
                                               seller)
    text, html_body = pay.render_mail(blocks, lang, subject)
    return subject, text, html_body


def receipt_mail(stmt, pack):
    """(subject, text, html) of the receipt, in the order's language."""
    lang = pay.lang_of(stmt.get("lang"))
    de = lang == "de"
    order = stmt.get("order") or echo_order(stmt.get("order_given"))
    name = echo_name(stmt.get("name"))
    if lang in ("lt", "hu"):
        return _receipt_other(stmt, pack, lang, order, name)
    got = pay.when_text(stmt["received_at"], lang, seconds=True)
    rows = [("Eingegangen am" if de else "Received on", got), ("Bestellung" if de else "Order", order),
            ("Name", name or "-"), ("E-Mail für diese Bestätigung" if de else "Email for this receipt", stmt["email"])]
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    w = lambda ts: pay.when_text(ts, lang) if ts else ("unbekannt" if de else "unknown")
    by = pay.date_text(pay.iso(stmt.get("refund_by") or stmt["received_at"] + REFUND_DAYS * 86400), lang)
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        what = ([("Für diese Bestellung wird nichts erstellt. Ihre Zahlung war bei Ihrem Widerruf noch in Bearbeitung. "
                  "Falls sie eingeht, erstatten wir sie Ihnen vollständig über das Zahlungsmittel, mit dem Sie bezahlt "
                  "haben, spätestens binnen 14 Tagen. Dafür fallen für Sie keine Gebühren an.")] if de else
                [("Nothing will be made for this order. Your payment was still being processed when you withdrew. If it "
                  "reaches us, you get it back in full, to the payment method you used, within 14 days at the latest. "
                  "You pay no fees for this.")])
    elif outcome == "withdrawn":
        first = ""
        if stmt.get("already") and stmt.get("first_at"):
            first = (f" (Ihr Widerruf lag uns bereits seit dem {w(stmt['first_at'])} vor.)" if de else
                     f" (We had already received your withdrawal on {w(stmt['first_at'])}.)")
        what = ([f"Ihr Widerruf ist wirksam{first}. Ihre Bestellung ist gestoppt: Es wird nichts erstellt. Wie in "
                 f"unserer Widerrufsbelehrung beschrieben, erstatten wir Ihnen die gezahlten {_money(stmt, lang)} "
                 f"unverzüglich, spätestens bis zum {by}, über das Zahlungsmittel, mit dem Sie bezahlt haben. Dafür "
                 f"fallen für Sie keine Gebühren an."] if de else
                [f"Your withdrawal is effective{first}. Your order is stopped: nothing will be made. As our withdrawal "
                 f"information sets out, you get back the {_money(stmt, lang)} you paid without undue delay, by {by} at "
                 f"the latest, to the payment method you used. You pay no fees for this."])
    elif outcome == "lapsed" and reason == "period_over":
        end = pay.date_text(_last_day(stmt), lang)
        what = ([f"Die 14-tägige Widerrufsfrist für diese Bestellung ist am {end} abgelaufen. Ihr Widerrufsrecht war "
                 f"daher bei Eingang Ihrer Erklärung bereits erloschen. Wir sehen uns Ihre Erklärung trotzdem "
                 f"persönlich an und antworten Ihnen per E-Mail."] if de else
                [f"The 14-day withdrawal period for this order ended on {end}. Your right of withdrawal had therefore "
                 f"already ended when your statement arrived. We will still look at your statement personally and "
                 f"reply to you by email."])
    else:   # lapsed: making began after the consent and the confirmation
        what = ([f"Bei Ihrer Bestellung haben Sie ausdrücklich zugestimmt, dass wir sofort mit der Erstellung Ihrer "
                 f"Datei beginnen, und bestätigt, dass Sie Ihr Widerrufsrecht mit diesem Beginn verlieren (Ihre "
                 f"Zustimmung vom {w(stmt.get('consent_at'))}). Das haben wir Ihnen mit unserer Bestellbestätigung per "
                 f"E-Mail vom {w(stmt.get('confirmation_at'))} bestätigt, und am {w(stmt.get('began_at'))} haben wir "
                 f"mit der Erstellung begonnen. Ihr Widerrufsrecht war daher bei Eingang Ihrer Erklärung bereits "
                 f"erloschen. Ihre Bestellung bleibt bestehen, und Sie erhalten Ihre Datei auf Ihrer Bestellseite.",
                 "Wir sehen uns Ihre Erklärung trotzdem persönlich an und antworten Ihnen per E-Mail. Ihre gesetzlichen "
                 "Rechte bei einer mangelhaften Datei bleiben unberührt."] if de else
                [f"When you ordered, you expressly agreed that we start making your file right away and confirmed that "
                 f"you lose your right of withdrawal once we have started (your consent of "
                 f"{w(stmt.get('consent_at'))}). We confirmed this in our order confirmation email of "
                 f"{w(stmt.get('confirmation_at'))}, and we started making your file on {w(stmt.get('began_at'))}. "
                 f"Your right of withdrawal had therefore already ended when your statement arrived. Your order stays "
                 f"in place, and your file is delivered on your order page.",
                 "We will still look at your statement personally and reply to you by email. Your statutory rights "
                 "for a defective file are not affected."])
    if outcome == "lapsed" and pay.acl_market(stmt.get("market")):
        # an Australian order: the end of the EU right of withdrawal must never read as "no refunds" (the Australian
        # Consumer Law's guarantees cannot be excluded; the terms' "Your rights in Australia")
        what = what + [("Das betraf nur den Widerruf ohne Angabe von Gründen nach dem EU-Verbraucherrecht. Ihre Rechte "
                        "nach dem Australian Consumer Law bleiben unberührt: Ist Ihre Datei mangelhaft oder entspricht sie "
                        "nicht der Beschreibung, antworten Sie einfach auf diese E-Mail. Siehe „Ihre Rechte in "
                        "Australien“ in unseren AGB.") if de else
                       ("That was only about cancelling for a change of mind under EU consumer law. Your rights under "
                        "the Australian Consumer Law are not affected: if your file is faulty or not as described, simply "
                        "reply to this email. See “Your rights in Australia” in our terms of sale.")]
    moved = []
    if stmt.get("email_given"):
        moved = [("Sie haben für diese Bestätigung eine andere Adresse angegeben. Wir senden sie an die E-Mail-Adresse, "
                  "mit der Sie bezahlt haben, weil für diese Bestellung schon mehrere Bestätigungen an andere Adressen "
                  "gegangen sind.") if de else
                 ("You gave another address for this receipt. We send it to the email address you paid with, because "
                  "several receipts for this order have already gone to other addresses.")]
    if de:
        subject = f"Eingangsbestätigung Ihres Widerrufs: SnapEyes-Bestellung {order}"
        blocks = [("p", f"Guten Tag {name}," if name else "Guten Tag,"),
                  ("p", "Ihr Widerruf ist bei uns eingegangen. Diese E-Mail bestätigt den Eingang; bitte bewahren Sie "
                        "sie auf.")] + [("p", x) for x in moved] + [
                  ("h", "Ihre Widerrufserklärung"), ("rows", rows), ("quote", pay.quoted(stmt["text"], "de")),
                  ("h", "Wie es weitergeht")] + [("p", x) for x in what] + [
                  ("p", "Fragen? Antworten Sie einfach auf diese E-Mail."),
                  ("p", "Mit freundlichen Grüßen\nSnapEyes"), ("p", pay.seller_lines(lang, pack))]
    else:
        subject = f"We received your withdrawal: SnapEyes order {order}"
        blocks = [("p", f"Hello {name}," if name else "Hello,"),
                  ("p", "we have received your withdrawal. This email confirms its receipt; please keep it.")] + [
                  ("p", x) for x in moved] + [
                  ("h", "Your withdrawal statement"), ("rows", rows), ("quote", pay.quoted(stmt["text"], "en")),
                  ("h", "What happens now")] + [("p", x) for x in what] + [
                  ("p", "Questions? Simply reply to this email."),
                  ("p", "Kind regards\nSnapEyes"), ("p", pay.seller_lines(lang, pack))]
    text, html_body = pay.render_mail(blocks, lang, subject)
    return subject, text, html_body


def unmatched_mail(stmt, pack):
    """(subject, text, html) of the NEUTRAL receipt for a statement that matched no order: the statement as it
    arrived (the typed texts without anything a mail client could turn into a link, and without phone numbers:
    echo_name, echo_order), the date and time, and that we are checking it. It says nothing about any order
    (whether it exists, its language, its state)."""
    lang = pay.lang_of(stmt.get("lang"))
    de = lang == "de"
    given = echo_order(stmt.get("order_given")) or "-"
    if lang in ("lt", "hu"):
        seller = pay.seller_lines(lang, pack)
        if lang == "hu":
            subject, blocks = withdraw_hu.unmatched_hu(stmt, given=given, name=echo_name(stmt.get("name")), seller=seller)
        else:
            subject = withdraw_lt.UNMATCHED_LT["subject"]
            blocks = withdraw_lt.unmatched_blocks_lt(
                pay.when_text(stmt["received_at"], lang, seconds=True), given, echo_name(stmt.get("name")), stmt["email"],
                pay.quoted(STATEMENT[lang].format(order=given), lang), seller)
        text, html_body = pay.render_mail(blocks, lang, subject)
        return subject, text, html_body
    rows = [("Eingegangen am" if de else "Received on", pay.when_text(stmt["received_at"], lang, seconds=True)),
            ("Angegebene Bestellnummer" if de else "Order number given", given),
            ("Name", echo_name(stmt.get("name")) or "-"),
            ("E-Mail für diese Bestätigung" if de else "Email for this receipt", stmt["email"])]
    said = pay.quoted(STATEMENT[lang].format(order=given), lang)
    if de:
        subject = "Eingangsbestätigung Ihrer Widerrufserklärung bei SnapEyes"
        blocks = [("p", "Guten Tag,"),
                  ("p", "Ihre Widerrufserklärung ist bei uns eingegangen. Diese E-Mail bestätigt den Eingang; bitte "
                        "bewahren Sie sie auf."),
                  ("h", "Ihre Widerrufserklärung"), ("rows", rows), ("quote", said),
                  ("h", "Wie es weitergeht"),
                  ("p", "Mit diesen Angaben konnten wir Ihre Erklärung nicht automatisch einer Bestellung zuordnen. Wir "
                        "prüfen sie persönlich und antworten Ihnen per E-Mail."),
                  ("p", "Wenn Sie Ihre Bestellbestätigung per E-Mail haben, können Sie auch den Widerrufslink darin "
                        "verwenden. Oder antworten Sie einfach auf diese E-Mail und nennen Sie uns Ihre Bestellnummer."),
                  ("p", "Mit freundlichen Grüßen\nSnapEyes"), ("p", pay.seller_lines(lang, pack))]
    else:
        subject = "We received your withdrawal statement: SnapEyes"
        blocks = [("p", "Hello,"),
                  ("p", "we have received your withdrawal statement. This email confirms its receipt; please keep it."),
                  ("h", "Your withdrawal statement"), ("rows", rows), ("quote", said),
                  ("h", "What happens now"),
                  ("p", "With these details we could not match your statement to an order automatically. We are "
                        "checking it personally and will reply to you by email."),
                  ("p", "If you have your order confirmation email, you can also use the withdrawal link in it. Or "
                        "simply reply to this email and tell us your order number."),
                  ("p", "Kind regards\nSnapEyes"), ("p", pay.seller_lines(lang, pack))]
    text, html_body = pay.render_mail(blocks, lang, subject)
    return subject, text, html_body


def send_owner_note(stmt, path):
    """The owner hears of every statement once, with what to do (see the module). The FIRST proven statement of an
    order with its outcome: its own note at once (_note.json beside it), within NOTE_DAY_MAX a day; past that, and
    for everything anyone can send (no match, an order never paid) and for repeats: the daily digest (_to_digest).
    Returns note_once's result, or "digest"."""
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    if outcome in DIGEST_OUTCOMES:
        return _to_digest(stmt, path)
    if not stmt.get("first", True):
        return _to_digest(stmt, path, "r")
    try:
        room = _note_room(stmt)
    except store.StorageError as e:
        pay.log(f"withdrawal {stmt.get('id')}: note slot not taken ({e}), the note goes at once")
        room = True
    if not room:
        pay.note_once(f"notes/withdraw_notes_capped_{pay.day()}.json", "withdraw_notes_capped",
                      "SnapEyes: many withdrawals today, the rest come in tomorrow's digest",
                      f"More than {NOTE_DAY_MAX} withdrawal statements that need your attention arrived today "
                      f"(NOTE_DAY_MAX = {NOTE_DAY_MAX} notes at once a day). So that they cannot use up the email "
                      f"quota the order confirmations need, the rest come in ONE digest after the day ends (the daily "
                      f"clean-up), marked NEED ACTION. Every customer got their receipt as usual.\nSee them now: python "
                      f"scripts/order_admin.py withdrawals\n")
        return _to_digest(stmt, path, "p")
    order = stmt.get("order")
    head, todo = _todo(stmt)
    subject = f"SnapEyes: withdrawal for order {order} ({head})"
    text = (f"A withdrawal statement arrived on {stmt.get('received')} (UTC).\n"
            f"  order        {order}\n  matched by   {stmt.get('verified')}\n"
            f"  name         {plain(stmt.get('name'))}\n  email        {stmt.get('email')}\n"
            f"  statement    {stmt.get('text')}\n\n"
            f"{todo}\n\nReceipt to the customer: sent automatically.\n"
            f"Later statements on this order come in the daily digest, not one by one.\n"
            f"Status: python scripts/order_admin.py status {order}\n")
    return pay.note_once(path[:-5] + "_note.json", f"withdrawal {stmt.get('id')}", subject, text)


def _todo(stmt):
    """(subject head, what to do) of a proven statement, for its note and for the digest."""
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    amount = pay.amount_text(stmt.get("amount") or 0, "en", stmt.get("currency"))
    if outcome == "withdrawn" and stmt.get("already"):
        return "repeat, already withdrawn", (f"The order was withdrawn already on "
                                             f"{pay.iso(stmt['first_at']) if stmt.get('first_at') else 'an earlier day'}"
                                             f": nothing new to do (the refund was due from the first statement).")
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        return "withdrawn while the payment was unsettled", (
            "Nothing is made for the order. If the payment arrives, you get a note to refund it (paid after "
            "withdrawal). Check the order in the Stripe Dashboard.")
    if outcome == "withdrawn":
        return f"WITHDRAWN, refund {amount}", (
            f"The withdrawal is effective ({reason}). Nothing is made for the order. REFUND {amount} in the Stripe "
            f"Dashboard (Payments, search {stmt.get('payment_intent') or stmt.get('session_id')}, Refund) by "
            f"{pay.iso(stmt.get('refund_by'))} at the latest. The order's images are deleted 14 days after the "
            f"withdrawal; its record and this statement stay.")
    if reason == "period_over":
        detail = (f"period_over: the last day was {_last_day(stmt)}, already moved past weekends and the national "
                  f"holidays of Lithuania, Germany and Hungary; if the customer's own country or German state had a "
                  f"public holiday on that day, the period ran to the end of the next working day there: then treat "
                  f"the withdrawal as effective and refund it")
    else:
        detail = (f"{reason}: consent {stmt.get('consent_at')}, confirmation email "
                  f"{pay.iso(stmt['confirmation_at']) if stmt.get('confirmation_at') else '-'}, making began "
                  f"{pay.iso(stmt['began_at']) if stmt.get('began_at') else '-'}")
    return "the right had ended, please look", (
        f"The right of withdrawal had already ended ({detail}). The customer was told so and that you will look at it "
        f"personally: please reply to them at {stmt.get('email')}.")


# ----------------------------------------------------------------------------- the owner's daily digest
def _entry(stmt, path):
    """One statement as the owner's notes list it (the typed texts without links)."""
    if stmt.get("verified") and stmt.get("order") and stmt.get("outcome") in ("withdrawn", "lapsed"):
        head, todo = _todo(stmt)
        what = (f"  order        {stmt.get('order')} (matched by {stmt.get('verified')}): {head}\n"
                f"  to do        {todo}\n")
    elif stmt.get("order"):
        what = f"  order        {stmt.get('order')}: never paid, nothing to do\n"
    else:
        what = f"  order given  {plain(stmt.get('order_given')) or '-'}\n"
    return (f"  received     {stmt.get('received')} (UTC)\n{what}"
            f"  name         {plain(stmt.get('name')) or '-'}\n  email        {stmt.get('email')}\n"
            f"  kept at      {path}\n")


def _to_digest(stmt, path, kind=None):
    """A statement for the owner's daily digest: its entry in cleanup/digest/<today>/<kind>-<id>.json (the path
    only; today, not the day it arrived: a note the daily clean-up retries on a later day must not land in a day
    whose digest has gone out already). kind: u matched no order, n an order never paid (the default for those
    outcomes), p a proven statement whose note did not go out at once (over NOTE_DAY_MAX), r a repeat. The day's
    first statement that matched no order is also sent at once, in one note a day, so a real customer who mistyped
    is looked at soon. Returns "digest"."""
    d = pay.day()
    kind = kind or ("u" if stmt.get("outcome") == "unmatched" else "n")
    try:
        store.put(f"cleanup/digest/{d}/{kind}-{stmt['id']}.json", store.json_bytes({"path": path}),
                  "application/json", upsert=False, timeout=6.0)
    except store.StorageExists:
        pass
    except store.StorageError as e:
        pay.log(f"withdrawal {stmt.get('id')}: digest entry not stored: {e}")
    if kind == "u":
        day_text = pay.date_text(pay.iso(stmt.get("received_at") or time.time()), "en")
        pay.note_once(f"notes/unmatched_first_{d}.json", "withdrawal matched no order",
                      f"SnapEyes: a withdrawal statement matched no order ({day_text})",
                      "A withdrawal statement came through the online function that matches no order: the order "
                      "number is unknown, or the order was paid with another email address and the order link was "
                      "not used.\n\n" + _entry(stmt, path) +
                      f"\nPlease find the order by hand (python scripts/order_admin.py status <order>) and reply to "
                      f"{stmt.get('email')}: a withdrawal counts from the time it arrived. The sender got a neutral "
                      f"receipt (the statement and its time, and that we are checking it), unless "
                      f"{RECEIPT_ADDR_MAX} had gone to that address that day.\n\n"
                      f"This is the only note at once today. Further statements that match no order, and statements "
                      f"on orders that were never paid, come in ONE digest after the day ends (the daily clean-up), "
                      f"so that a flood of them cannot use up the email quota the order confirmations need. List them "
                      f"any time: python scripts/order_admin.py withdrawals\n")
    return "digest"


def send_digests(yes=True, stop_left=8.0, out=None, max_seconds=DIGEST_SECONDS):
    """The daily clean-up's part: for every finished UTC day with entries in cleanup/digest/<day>/, ONE owner email
    listing that day's statements the owner did not get one by one (DIGEST_LIST of them one by one, NEED ACTION
    first, the rest counted), then the day's entries go. Without yes nothing is sent or removed. At most
    max_seconds of the run. Returns {days, statements} (+ more when it stopped for time)."""
    say = out or pay.log
    res = {"days": 0, "statements": 0}
    today = pay.day()
    until = time.time() + max_seconds
    for row in store.list_all("cleanup/digest"):
        d = row["name"]
        if not row["folder"] or not re.fullmatch(r"[0-9]{6}", d) or d >= today:
            continue
        if L.time_left() < stop_left or time.time() > until:
            res["more"] = True
            break
        names = [r["name"] for r in store.list_all(f"cleanup/digest/{d}")
                 if not r["folder"] and r["name"].endswith(".json")]
        rank = lambda n: (DIGEST_KINDS.index(n[0]) if n[:1] in DIGEST_KINDS and n[1:2] == "-" else 9, n)
        marks = [f"cleanup/digest/{d}/{n}" for n in sorted(names, key=rank)]
        if not marks:
            continue
        count = {k: sum(1 for n in names if n.startswith(k + "-")) for k in DIGEST_KINDS}
        n_u, n_p, n_r = count["u"], count["p"], count["r"]
        n_n = len(names) - n_u - n_p - n_r
        res["days"] += 1
        res["statements"] += len(names)
        if not yes:
            say(f"would send the withdrawal digest of {d}: {n_p} need action, {n_u} matched no order, {n_n} on unpaid "
                f"orders, {n_r} repeats")
            continue
        shown = []
        for i in range(0, min(len(marks), DIGEST_LIST), 8):
            part = marks[i:min(i + 8, DIGEST_LIST)]
            ptrs = pay.parallel([lambda m=m: store.get_json(m, timeout=8.0) for m in part])
            paths = [p.get("path") if isinstance(p, dict) and isinstance(p.get("path"), str) else None for p in ptrs]
            stmts = pay.parallel([lambda p=p: store.get_json(p, timeout=8.0) if p else None for p in paths])
            shown += [(m.rsplit("/", 1)[-1][:1], s, p) for m, s, p in zip(part, stmts, paths) if isinstance(s, dict)]
        date = pay.date_text(f"20{d[:2]}-{d[2:4]}-{d[4:]}", "en")
        of = lambda k: "\n".join(_entry(s, p) for kk, s, p in shown if kk == k)
        text = ""
        if n_p:
            text += (f"NEED ACTION: {n_p} statement(s) proven by the order link or the payment email whose note did not "
                     f"go out at once (more than {NOTE_DAY_MAX} notes that day). Handle each as its line says (refund "
                     f"it, or reply personally).\n\n" + of("p") + "\n")
        text += (f"Withdrawal statements that came through the online function on {date} (UTC) and were not sent to "
                 f"you one by one.\n\nMatched NO order: {n_u}. The order number is unknown, or the order was paid with "
                 f"another email address and the order link was not used. Please find each order by hand (python "
                 f"scripts/order_admin.py status <order>) and reply to the email given: a withdrawal counts from the "
                 f"time it arrived. Each sender got a neutral receipt (at most {RECEIPT_ADDR_MAX} a day to one "
                 f"address).\n\n" + of("u") +
                 f"\nOn orders that were never paid: {n_n}. No contract, nothing to do: their open payment pages were "
                 f"closed.\n\n" + of("n"))
        if n_r:
            text += (f"\nLater statements on orders you already had a note about: {n_r}. Nothing new to do.\n\n" + of("r"))
        if len(names) > len(shown):
            text += f"\n{len(names) - len(shown)} more are not listed here: python scripts/order_admin.py withdrawals --day {d}\n"
        counts = f"{n_u} matched no order, {n_n} on unpaid orders"
        if n_p or n_r:
            counts = f"{n_p} NEED ACTION, {counts}, {n_r} repeats"
        r = pay.note_once(f"notes/digest_{d}.json", f"withdrawal digest {d}",
                          f"SnapEyes: withdrawal statements to check from {date} ({counts})", text)
        say(f"withdrawal digest of {d}: {counts}: {r}")
        if r != "transient":
            store.delete_many(marks)
    return res


def purge_addr_marks(yes=True):
    """The monthly receipt slots per address (withdrawaddr/<yymm>/) are needed for the running month only; the
    clean-up removes the months before the previous one. Returns how many files went (or would go)."""
    keep = time.strftime("%y%m", time.gmtime(time.time() - 40 * 86400))
    n = 0
    for row in store.list_all(ADDR_TOP):
        if row["folder"] and re.fullmatch(r"[0-9]{4}", row["name"]) and row["name"] < keep:
            files = pay.folder_files(f"{ADDR_TOP}/{row['name']}")
            if yes and files:
                store.delete_many(files)
            n += len(files)
    return n
