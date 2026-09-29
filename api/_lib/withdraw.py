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
    it"; nothing about any order)
  - paid, nothing made yet (making.json, a stored eye or artwork), within 14 days: EFFECTIVE. withdrawn.json stops
    the order (make and compose answer 409 withdrawn), the owner is told to refund the payment within 14 days, and
    the order's images are deleted 14 days later (cleanup/withdrawn/, api/_lib/cleanup.py)
  - paid, making began after the customer's consent and after the order confirmation email: the right had LAPSED
    (Art. 16(m); § 356 Abs. 5 BGB). The statement is still recorded and answered, honestly, with the reason and the
    times; the owner looks at it and replies. Making began without those conditions: effective after all
  - paid more than 14 days ago and nothing made: lapsed (the period ended)
  - not paid: Stripe is asked first. A session paid meanwhile is recorded and handled as paid; one still settling
    (a delayed method) makes the withdrawal effective, and a payment that arrives later is flagged for a refund
    (pay.record_paid). Otherwise there is no contract: open sessions are closed so the order cannot be paid by
    accident, and the page hears 409 not_paid
The receipt (the statement's content with the date and time it arrived) goes to the given address at once, on a
durable medium, for every statement taken except one on an order that was never paid (no contract); when Resend is
busy it is sent again by the daily clean-up (withdrawdue/).

The owner hears of every statement: at once, one by one, for the statements the order's link key or its payment
email proves (they are bounded by ORDER_DAY_MAX per order); the statements that match no order, and those on
orders that were never paid, anyone can send, so they go into ONE digest per day, sent by the daily clean-up
(cleanup/digest/<day>/, send_digests()), plus one note at once for the day's first statement that matched no
order. That keeps a flood of statements from using up the email provider's daily quota, which the order
confirmations need.

The flood guards (_room, receipt_room), each a slot marker in withdrawlog/<today>/ written BEFORE the work and
counted after it (so a burst cannot all pass a check made before any of them wrote; no personal data):
  v-<order tag>-<id>     proven statements: ORDER_DAY_MAX per order a day, never a site-wide ceiling
  u-<text tag>-<id>      statements that matched no order: DAY_MAX a day in all (past it the page asks for an
                         email instead), UNMATCHED_TEXT_MAX a day for one typed order text
  r-<address tag>-<id>   receipts for statements that matched no order: RECEIPT_ADDR_MAX a day to one address

Storage: orders/<order>/withdrawal_<id>.json (the statement: name, email, time, text, outcome), _ack.json and
_note.json beside it (the two emails, each once), withdrawal.json (the latest statement without personal data: what
the order page shows) and withdrawn.json (the order is stopped). Kept with the order record (privacy policy)."""
import re, time, hmac, hashlib, secrets, threading
from . import iris as L
from . import store
from . import pay

NAME_MAX = 100
EMAIL_MAX = 254
DAY_MAX = 20                 # statements that match NO order, taken per UTC day (anyone can send one; past it the
                             # page asks for an email instead). Proven statements never count against it
UNMATCHED_TEXT_MAX = 3       # of those, for one typed order text per day
ORDER_DAY_MAX = 5            # proven statements (link key or payment email) for one order per day
RECEIPT_ADDR_MAX = 2         # receipts per day to one address for statements that matched no order
WITHDRAW_DAYS = 14           # the withdrawal period, from the contract (the payment)
REFUND_DAYS = 14             # the refund is due within 14 days of the withdrawal (Art. 13)
DUE_DAYS = 3                 # a receipt Resend would not take is tried again by the daily clean-up this long
RETRY_SECONDS = 12.0         # the daily clean-up spends at most this long on receipts to send again
DIGEST_SECONDS = 8.0         # ... and at most this long on the owner's digests (a backlog of days goes on next run)
DIGEST_LIST = 40             # statements listed one by one in the owner's daily digest (the rest are counted)
FALLBACK_MAX = 10            # owner emails per day and instance for statements storage could not take
DIGEST_OUTCOMES = ("unmatched", "no_contract")      # the owner hears of these in the daily digest
NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
# what a mail client could turn into a link: a scheme://, www., an address, a domain name (a name never needs one)
_LINKISH = re.compile(r"(?i)(?:\b[a-z][a-z0-9+.-]*://\S*|\bwww\.\S*|\S+@\S+|(?:[\w-]+\.)+[^\W\d_]{2,}\b\S*)")

STATEMENT = {   # as the order page shows it before "Confirm withdrawal" (src/order/copy.ts withdraw.statement)
    "en": "I hereby withdraw from the contract I concluded for the supply of the following digital content: SnapEyes "
          "artwork, order {order}.",
    "de": "Hiermit widerrufe ich den von mir abgeschlossenen Vertrag über die Bereitstellung der folgenden digitalen "
          "Inhalte: SnapEyes-Kunstwerk, Bestellung {order}.",
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


def _take(kind, tag, sid, count):
    """Take this statement's slot FIRST, then count: withdrawlog/<today>/<kind>-<tag>-<id>.json. Returns (path, the
    names in today's folder that start with `count`, ours included; a listing stops at 1000, which is past every
    ceiling here). A statement sent again (the same id) finds its slot taken and is counted once. Every request that
    counts its own slot within the ceiling keeps it, so at most the ceiling many pass, however many arrive at once
    (the last of them to count sees all the others' slots)."""
    d = pay.day()
    path = f"withdrawlog/{d}/{kind}-{tag}-{sid[-10:]}.json"
    try:
        store.put(path, b"{}", "application/json", upsert=False, timeout=6.0)
    except store.StorageExists:
        pass
    names = [r["name"] for r in store.list_folder(f"withdrawlog/{d}", limit=1000, timeout=8.0, search=count)
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
    """May a receipt for a statement that matched no order go to its address? At most RECEIPT_ADDR_MAX a day to one
    address (a slot like _room's), so a typed address cannot be flooded with our receipts."""
    tag = _addr_tag(stmt.get("email"))
    path, names = _take("r", tag, str(stmt.get("id") or secrets.token_hex(5)), f"r-{tag}-")
    if len(names) > RECEIPT_ADDR_MAX:
        _give_back(path)
        return False
    return True


def plain(s):
    """A customer's typed text as our emails echo it: anything a mail client could turn into a link is left out,
    so a typed name or order text never makes our receipt carry someone's link."""
    return re.sub(r"\s+", " ", _LINKISH.sub("[...]", str(s or ""))).strip()


# ----------------------------------------------------------------------------- what the statement means
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
    if isinstance(paid_at, (int, float)) and now > paid_at + WITHDRAW_DAYS * 86400:
        return dict(facts, outcome="lapsed", reason="period_over", period_end=paid_at + WITHDRAW_DAYS * 86400)
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
                stmt.update(a)
        if paid is not None:
            stmt.update(_assess_paid(order, rec, paid, now))
            stmt["lang"] = lang = pay.lang_of((paid.get("spec") or {}).get("lang"))
        if stmt.get("outcome") == "withdrawn" and paid is not None and stmt.get("amount"):
            first = stmt.get("first_at") if isinstance(stmt.get("first_at"), (int, float)) else t
            stmt.update(refund="due", refund_by=int(first) + REFUND_DAYS * 86400)
    try:
        store.put(path, store.json_bytes(stmt), "application/json", upsert=False, timeout=10.0)
    except store.StorageExists:
        prev = store.get_json(path, timeout=8.0)
        return _finish(prev if isinstance(prev, dict) else stmt, path, repeat=True)
    pay.log(f"withdrawal {sid}: order {order or '(none)'} {stmt['outcome']} ({stmt.get('reason')}), "
            f"verified {verified or 'no'}")
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
        reply.update(amount=stmt["amount"], currency="EUR", refund="due", refund_by=pay.iso(stmt.get("refund_by")))
    if outcome == "lapsed":
        reply.update(began_at=stmt.get("began_at"), confirmation_at=stmt.get("confirmation_at"),
                     consent_at=stmt.get("consent_at"), period_end=stmt.get("period_end"))
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
    return {"sent": "sent", "done": "sent", "transient": "pending", "off": "off"}.get(ack, "not_sent")


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
    again (never raises). At most FALLBACK_MAX a day from one instance (storage cannot count them now), so a storage
    outage during a flood cannot use up the email quota; the rest are logged."""
    with _FALLBACK_LOCK:
        if _FALLBACK["day"] != pay.day():
            _FALLBACK.update(day=pay.day(), n=0)
        _FALLBACK["n"] += 1
        over = _FALLBACK["n"] > FALLBACK_MAX
    if over:
        pay.log(f"withdrawal {sid}: storage failed, owner mail skipped (over {FALLBACK_MAX} today on this instance)")
        return
    try:
        res = pay.send_mail(pay.owner_mail(), "SnapEyes: a withdrawal statement arrived but was NOT stored",
                            f"A withdrawal statement arrived at {pay.iso(t)}, but storage did not answer, so it is not "
                            f"stored and the customer was asked to try again.\nOrder given: {plain(given)}\nName: "
                            f"{plain(name)}\nEmail: {email}\nStatement: "
                            f"{STATEMENT[page_lang].format(order=plain(given))}\n\n"
                            f"If no stored statement for this order follows, handle it by hand: it counts from the time "
                            f"above.\n", f"snapeyes-withdraw-fallback-{sid}")
        pay.log(f"withdrawal {sid}: storage failed, owner mail {res}")
    except Exception as e:  # noqa
        pay.log(f"withdrawal {sid}: storage failed and the owner mail too: {type(e).__name__}")


# ----------------------------------------------------------------------------- the two emails
def send_receipt(stmt, path):
    """The receipt to the customer (Art. 11a(4) of the directive, § 356a BGB): the statement's content and the date
    and time it arrived, on a durable medium, to the address the customer gave. Once per statement. A proven
    statement gets receipt_mail (what it means for the order); one that matched no order gets unmatched_mail, a
    NEUTRAL receipt that says nothing about any order, at most RECEIPT_ADDR_MAX a day to one address (receipt_room:
    a typed address cannot be flooded). None for an order that was never paid (no contract). Returns send_mail's
    result, "done" (sent before), "none", "off", "limited" or "transient"."""
    outcome = stmt.get("outcome")
    if outcome == "no_contract" or not (stmt.get("verified") or outcome == "unmatched"):
        return "none"
    if not pay.email_configured():
        return "off"
    claim = path[:-5] + "_ack.json"
    if not pay.claim_once(claim):
        return "done"
    if not stmt.get("verified"):
        try:
            room = receipt_room(stmt)
        except store.StorageError as e:
            pay.log(f"withdrawal {stmt.get('id')}: receipt slot not taken: {e}")
            pay._mark(claim, "retry")
            return "transient"
        if not room:
            pay._mark(claim, "failed", result="limited")
            pay.log(f"withdrawal {stmt['id']}: no receipt, {RECEIPT_ADDR_MAX} went to that address today")
            return "limited"
    subject, text, html_body = (receipt_mail if stmt.get("verified") else unmatched_mail)(stmt, pay.legal_pack())
    res = pay.send_mail(stmt["email"], subject, text, f"snapeyes-withdrawal-{stmt['id']}", html_body)
    pay._mark(claim, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res)
    pay.log(f"withdrawal {stmt['id']}: receipt {res}")
    return res


def _money(stmt, lang):
    return pay.price_text(stmt.get("amount") or 0, lang)


def receipt_mail(stmt, pack):
    """(subject, text, html) of the receipt, in the order's language."""
    lang = pay.lang_of(stmt.get("lang"))
    de = lang == "de"
    order = stmt.get("order") or plain(stmt.get("order_given"))
    name = plain(stmt.get("name"))
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
        end = pay.date_text(pay.iso(stmt.get("period_end") or stmt["received_at"]), lang)
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
    if de:
        subject = f"Eingangsbestätigung Ihres Widerrufs: SnapEyes-Bestellung {order}"
        blocks = [("p", f"Guten Tag {name}," if name else "Guten Tag,"),
                  ("p", "Ihr Widerruf ist bei uns eingegangen. Diese E-Mail bestätigt den Eingang; bitte bewahren Sie "
                        "sie auf."),
                  ("h", "Ihre Widerrufserklärung"), ("rows", rows), ("quote", pay.quoted(stmt["text"], "de")),
                  ("h", "Wie es weitergeht")] + [("p", x) for x in what] + [
                  ("p", "Fragen? Antworten Sie einfach auf diese E-Mail."),
                  ("p", "Mit freundlichen Grüßen\nSnapEyes"), ("p", pay.seller_lines(lang, pack))]
    else:
        subject = f"We received your withdrawal: SnapEyes order {order}"
        blocks = [("p", f"Hello {name}," if name else "Hello,"),
                  ("p", "we have received your withdrawal. This email confirms its receipt; please keep it."),
                  ("h", "Your withdrawal statement"), ("rows", rows), ("quote", pay.quoted(stmt["text"], "en")),
                  ("h", "What happens now")] + [("p", x) for x in what] + [
                  ("p", "Questions? Simply reply to this email."),
                  ("p", "Kind regards\nSnapEyes"), ("p", pay.seller_lines(lang, pack))]
    text, html_body = pay.render_mail(blocks, lang, subject)
    return subject, text, html_body


def unmatched_mail(stmt, pack):
    """(subject, text, html) of the NEUTRAL receipt for a statement that matched no order: the statement as it
    arrived (the typed texts without anything a mail client could turn into a link), the date and time, and that we
    are checking it. It says nothing about any order (whether it exists, its language, its state)."""
    lang = pay.lang_of(stmt.get("lang"))
    de = lang == "de"
    given = plain(stmt.get("order_given")) or "-"
    rows = [("Eingegangen am" if de else "Received on", pay.when_text(stmt["received_at"], lang, seconds=True)),
            ("Angegebene Bestellnummer" if de else "Order number given", given),
            ("Name", plain(stmt.get("name")) or "-"),
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
    """The owner hears of every statement once, with what to do. A proven statement: its own note at once
    (_note.json beside it). One that matched no order, or one on an order that was never paid (anyone can send
    those): the daily digest instead (_to_digest). Returns note_once's result, or "digest"."""
    outcome, reason = stmt.get("outcome"), stmt.get("reason")
    if outcome in DIGEST_OUTCOMES:
        return _to_digest(stmt, path)
    order = stmt.get("order")
    amount = pay.amount_text(stmt.get("amount") or 0, "en")
    if outcome == "withdrawn" and reason in ("payment_settling", "payment_unknown"):
        head = "withdrawn while the payment was unsettled"
        todo = ("Nothing is made for the order. If the payment arrives, you get a note to refund it (paid after "
                "withdrawal). Check the order in the Stripe Dashboard.")
    elif outcome == "withdrawn":
        head = f"WITHDRAWN, refund {amount}"
        todo = (f"The withdrawal is effective ({reason}). Nothing is made for the order. REFUND {amount} in the Stripe "
                f"Dashboard (Payments, search {stmt.get('payment_intent') or stmt.get('session_id')}, Refund) by "
                f"{pay.iso(stmt.get('refund_by'))} at the latest. The order's images are deleted 14 days after the "
                f"withdrawal; its record and this statement stay.")
    else:
        head = "the right had ended, please look"
        todo = (f"The right of withdrawal had already ended ({reason}: consent {stmt.get('consent_at')}, confirmation "
                f"email {pay.iso(stmt['confirmation_at']) if stmt.get('confirmation_at') else '-'}, making began "
                f"{pay.iso(stmt['began_at']) if stmt.get('began_at') else '-'}). The customer was told so and that you "
                f"will look at it personally: please reply to them at {stmt.get('email')}.")
    subject = f"SnapEyes: withdrawal for order {order} ({head})"
    text = (f"A withdrawal statement arrived on {stmt.get('received')} (UTC).\n"
            f"  order        {order}\n  matched by   {stmt.get('verified')}\n"
            f"  name         {plain(stmt.get('name'))}\n  email        {stmt.get('email')}\n"
            f"  statement    {stmt.get('text')}\n\n"
            f"{todo}\n\nReceipt to the customer: sent automatically.\n"
            f"Status: python scripts/order_admin.py status {order}\n")
    return pay.note_once(path[:-5] + "_note.json", f"withdrawal {stmt.get('id')}", subject, text)


# ----------------------------------------------------------------------------- the owner's daily digest
def _entry(stmt, path):
    """One statement as the owner's notes list it (the typed texts without links)."""
    return (f"  received     {stmt.get('received')} (UTC)\n  order given  {plain(stmt.get('order_given')) or '-'}\n"
            f"  name         {plain(stmt.get('name')) or '-'}\n  email        {stmt.get('email')}\n"
            f"  kept at      {path}\n")


def _to_digest(stmt, path):
    """A statement for the owner's daily digest: its entry in cleanup/digest/<day it arrived>/ (u- matched no
    order, n- an order never paid; the path only). The day's first statement that matched no order is also sent at
    once, in one note a day, so a real customer who mistyped is looked at soon. Returns "digest"."""
    d = pay.day(stmt.get("received_at") or time.time())
    kind = "u" if stmt.get("outcome") == "unmatched" else "n"
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
    listing that day's statements that matched no order and those on orders never paid (DIGEST_LIST of them one by
    one, the rest counted), then the day's entries go. Without yes nothing is sent or removed. At most max_seconds
    of the run. Returns {days, statements} (+ more when it stopped for time)."""
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
        marks = [f"cleanup/digest/{d}/{n}" for n in sorted(names, key=lambda n: (not n.startswith("u-"), n))]
        if not marks:
            continue
        n_u = sum(1 for n in names if n.startswith("u-"))
        n_n = len(names) - n_u
        res["days"] += 1
        res["statements"] += len(names)
        if not yes:
            say(f"would send the withdrawal digest of {d}: {n_u} matched no order, {n_n} on unpaid orders")
            continue
        shown = []
        for i in range(0, min(len(marks), DIGEST_LIST), 8):
            ptrs = pay.parallel([lambda m=m: store.get_json(m, timeout=8.0) for m in marks[i:min(i + 8, DIGEST_LIST)]])
            paths = [p.get("path") if isinstance(p, dict) and isinstance(p.get("path"), str) else None for p in ptrs]
            stmts = pay.parallel([lambda p=p: store.get_json(p, timeout=8.0) if p else None for p in paths])
            shown += [(s, p) for s, p in zip(stmts, paths) if isinstance(s, dict)]
        date = pay.date_text(f"20{d[:2]}-{d[2:4]}-{d[4:]}", "en")
        un = [x for x in shown if x[0].get("outcome") == "unmatched"]
        nc = [x for x in shown if x[0].get("outcome") != "unmatched"]
        text = (f"Withdrawal statements that came through the online function on {date} (UTC) and were not sent to "
                f"you one by one.\n\nMatched NO order: {n_u}. The order number is unknown, or the order was paid with "
                f"another email address and the order link was not used. Please find each order by hand (python "
                f"scripts/order_admin.py status <order>) and reply to the email given: a withdrawal counts from the "
                f"time it arrived. Each sender got a neutral receipt (at most {RECEIPT_ADDR_MAX} a day to one "
                f"address).\n\n" + "\n".join(_entry(s, p) for s, p in un) +
                f"\nOn orders that were never paid: {n_n}. No contract, nothing to do: their open payment pages were "
                f"closed.\n\n" + "\n".join(_entry(s, p) for s, p in nc) +
                (f"\n{len(names) - len(shown)} more are not listed here: python scripts/order_admin.py withdrawals "
                 f"--day {d}\n" if len(names) > len(shown) else ""))
        r = pay.note_once(f"notes/digest_{d}.json", f"withdrawal digest {d}",
                          f"SnapEyes: withdrawal statements to check from {date} ({n_u} matched no order, {n_n} on "
                          f"unpaid orders)", text)
        say(f"withdrawal digest of {d}: {n_u} matched no order, {n_n} on unpaid orders: {r}")
        if r != "transient":
            store.delete_many(marks)
    return res
