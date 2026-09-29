# -*- coding: utf-8 -*-
"""The server's own making of paid orders, so an order is finished without the customer's order page: a customer who
pays and closes the tab still gets the file (the terms promise it within 48 hours of payment).

How it runs on Vercel. A Python function runs until it returns. There is no work after the reply (waitUntil exists
for Node.js only), and a caller that disconnects does not stop the function: request cancellation is opt-in
("supportsCancellation" in vercel.json) and exists for the Node.js runtime only (Vercel docs, Functions API reference,
"Cancel requests", read 2026-09-29; this project sets no such option). So every step here is done BEFORE the function
replies, and the next step is a NEW invocation, asked for by a short self-call:
    kick() -> POST /api/order {action: "advance", order, ticket, hop}  (client timeout 1.5 s: the caller never waits)
    advance(): ONE step (one eye, or the artwork, or the ready email), then kick() for the next one
The callee runs to its end on its own, and a step never relies on anything after its reply. What is not guaranteed
anywhere (a self-call lost on the way, an instance that dies, Vercel's loop protection INFINITE_LOOP_DETECTED, whose
limits are not published) only stops the chain: nothing is half done, because every step is the order page's own
idempotent step (the eye claims of master_eye, compose.lock, the claimed emails). Then:
  - the order page takes over (it drives the steps itself whenever the server is not on it, advance.json), and its
    status call asks for the server again when an order whose making has begun has no live step (nudge; a status
    read never STARTS an order: the withdrawal page reads the status too, and opening it must not start the work
    that ends the right of withdrawal);
  - the daily clean-up advances every paid, confirmed, unfinished order older than CATCHUP_AGE (catch_up), from the
    index pay.index_making writes with paid.json, at most CATCHUP_MAX a run.

Who starts it. Making may start once the order confirmation email went out (pay.confirmation). Whoever sends it
(pay.deliver_mail: the Stripe webhook, the order page's status call, a resend from the admin panel) calls
after_confirmation(), and the webhook does the same for an order that needs no email (a test order where email is
off). The server STARTS an order (the first render, the moment the customer's right of withdrawal ends) only where
the texts the customer was given say so: the confirmation email this order got (mail_delivery.json "making":
"server", written from the legal pack's "making_start": "after_confirmation", pay.server_starts); an email that said
"making starts when you open your order page" keeps it that way for that order. An order the page has started
(making.json, or a stored eye) is always finished by the server: the right of withdrawal has ended then.

The self-call. It goes to this very deployment: on production the site (SNAPEYES_SITE, default snapeyes.com), on a
Vercel Preview its own deployment URL (with VERCEL_AUTOMATION_BYPASS_SECRET as x-vercel-protection-bypass when
Vercel sets it, else the preview's protection answers 401 and the order page drives, as before), in a local run only
SNAPEYES_SELF_BASE (http://127.0.0.1:<port>, tests), never production. It carries an internal ticket of its own kind,
"advance-<order>" (L.mint_ticket, 5 minutes): only the server can mint it, no reply ever carries it, and neither the
customer's access key k nor a work or unlock ticket opens the action (403 forbidden before anything is read).

One step. advance() takes the order's lease (advance.lock; one step at a time, a dead holder's lease is taken over
after LEASE_STALE, and the next hop may take over its own predecessor's), reads the order, and does the first thing
missing, with the order page's own code (api/order.py make_eye / compose_order, the same slot claims and the same
withdrawal and making rules):
  withdrawn / deleted       stop (the index note goes)
  refunded                  stop (refunded.json, or the admin panel's refund of the order's payment; the index
                            note goes)
  a ready artwork           the "your artwork is ready" email, once (ready_mail_once), then stop
  held for review           stop (review.json, a held artwork, or a confirmation that cannot go out): the owner decides
  confirmation not sent     stop: the one who sends it asks for the server again
  not started, and the texts say the page starts it: stop (the page, or the owner)
  an eye missing            make it (an eye another request is rendering is skipped for the next missing one)
  every eye made            compose the artwork (then the ready email in the same step)
Busy answers (the image model or storage busy, an eye or the artwork being made elsewhere, no time left for a
render) back off: the next self-call goes out after a delay, waited inside this invocation when it has the time, else
by a relay hop that only waits; after MAX_BUSY busy steps in a row the chain stops with one owner note
(making_busy) and the page or the daily run goes on. A failure after the image model answered (a paid render that
may be lost: the master not stored, api/order.py make_eye counts it per order) is never retried as busy: the chain
stops with one owner note (render_lost), and the order is held for a person at the order's LOST_MAX-th such loss,
whoever asked. A permanent error stops it with one owner note (making_error). advance.json always says what the
server did last: the order page shows it and drives nothing while the server is on it (view).

What tells the owner that a paid order is not moving (nothing here may fail silently: the terms promise the file
within 48 hours of payment): a self-call answered with an error status (401 a protected preview, 403 a refused ticket
or the Vercel Firewall, 429, 508 Vercel's loop protection, a redirect) sends one owner note per order at once
(self_call); a chain that gives up busy, or on a lost render or an error, sends its note; and the daily run sends one
reminder per order that is paid, not held for the owner (those have their own reminder, cleanup._reviews) and still
not ready LATE_HOURS after payment (late). LATE_HOURS is 12, not 24: the daily run comes once a day, so a reminder
reaches the owner 12 to 36 hours after payment, still inside the 48.

The self-call test (probe): whether Vercel lets a chain of self-calls run on a deployment (its loop protection
publishes no limit; a Community report saw 508 after four nested calls of a Node function) is proven by
scripts/order_admin.py selfcall-probe, on production before orders open and on a Preview: PROBE_HOPS hops of the same
self-call, each working longer than KICK_READ before it answers (so every caller leaves first, as after a render),
recorded under ops/selfcall/<id>/, with no order and nothing paid (probe)."""
import os, re, json, time, hashlib, secrets, threading
import requests
from . import iris as L
from . import store
from . import pay

KIND = "advance-"              # the internal ticket's kind: "advance-<order>", minted only here, never handed out
TICKET_TTL = 300               # seconds the ticket of one self-call is valid
KICK_CONNECT = 1.5             # the self-call's connect timeout
KICK_READ = 1.5                # ... and how long it waits for an answer (it does not wait for the work)
FUNCTION_SECONDS = 60.0        # vercel.json maxDuration of api/**/*.py (L.run gives the work L.BUDGET of it)
SPARE = 4.0                    # of the FUNCTION_SECONDS - L.BUDGET after the work, what a self-call may still use
                               # (the rest covers a cold start's imports, which the deadline does not count)
KICK_NEED = 3.5                # seconds a self-call needs: connect, send, the answer's timeout, a margin
KICK_MEMO = 60.0               # one instance asks for the same order at most once in this long (status polls)
LEASE_STALE = 75.0             # a lease older than this belongs to an invocation that is dead (60 s at most)
FRESH = 100.0                  # advance.json younger than this (a render is at most 60 s): the server is on it
MAX_HOPS = 40                  # steps of one chain (8 eyes, the artwork, the email and many busy answers)
MAX_BUSY = 10                  # busy answers in a row, then the order page and the daily run go on
WAIT_MAX = 40                  # the longest back-off between two steps (seconds)
CATCHUP_AGE = 1800             # the daily run advances paid, confirmed, unfinished orders older than this
CATCHUP_MAX = 8                # ... at most this many a run (the rest the next day, "more")
CATCHUP_SECONDS = 8.0          # ... in at most this long of the run
INDEX_DAYS = 30                # an order still unfinished this long after payment leaves the daily catch-up (logged;
                               # a held one has had its reminders, pay.REVIEW_REMIND_HOURS)
LATE_HOURS = 12                # a paid order not ready this long after payment: one owner reminder from the daily run
                               # (which comes once a day: the reminder arrives 12 to 36 h after payment, inside 48 h)
LATE_MAX = 5                   # ... at most this many reminders a run (the rest the next day)
PROBE_KIND = "selfcall-probe-" # the self-call test's internal ticket: "selfcall-probe-<id>" (scripts/order_admin.py)
PROBE_HOPS = 12                # hops of one test (an 8-eye order needs 10 or more nested self-calls)
PROBE_WORK = 2.5               # seconds each hop works before it asks for the next: longer than KICK_READ, so its
                               # caller has left before it answers, exactly as after a render
PROBE_TOP = "ops/selfcall"     # ops/selfcall/<id>/hop_<nn>.json: what each hop of a test did
FINAL = ("ready", "withdrawn", "deleted", "refunded", "not_paid", "test_payment")   # stops after which the index
                                                                        # note goes
REFUNDS_TOP = "ops/refunds"    # ops.REFUNDS: the admin panel's refund records, ops/refunds/<order>/<payment>.json
_ID = re.compile(r"^[0-9a-f]{12}$")
_HOST = re.compile(r"^[a-z0-9][a-z0-9.-]{2,200}$")
_BYPASS = re.compile(r"^[A-Za-z0-9_-]{8,256}$")


# ----------------------------------------------------------------------------- the self-call
def self_base():
    """Where the self-call goes ("" when nowhere): this deployment itself. Production: the site (pay.site(): the
    canonical domain, which no deployment protection covers). A Vercel Preview: its own deployment URL. A local run:
    only SNAPEYES_SELF_BASE of the form http://127.0.0.1:<port> (tests), so a local script never calls production."""
    if os.environ.get("VERCEL"):
        if pay.on_production():
            return pay.site()
        host = pay._env("VERCEL_URL").lower()
        return f"https://{host}" if _HOST.fullmatch(host) else ""
    return pay._base("SNAPEYES_SELF_BASE", "")


def real_left():
    """Seconds this invocation may still use for a self-call: the work's deadline (L.time_left) plus SPARE of the
    function's own limit beyond it."""
    return L.time_left() + SPARE


def ticket_ok(order, tok):
    return L.check_ticket(tok, kind=KIND + order)


_KICKED = {}                   # order -> (time, went out): this instance's latest self-call for it
_KICKED_LOCK = threading.Lock()
_SAID_OFF = {"yes": False}


def _recent(order):
    """(time, went_out) of this instance's self-call for the order within KICK_MEMO, else None."""
    now = time.time()
    with _KICKED_LOCK:
        for o in [o for o, (t, _) in _KICKED.items() if now - t >= KICK_MEMO]:
            del _KICKED[o]
        return _KICKED.get(order)


def _note_kick(order, went, t=None):
    """Remember a self-call for the order, by the time it was SENT: whatever the step wrote after that (advance.json)
    is newer and wins over this memo (view, nudge)."""
    with _KICKED_LOCK:
        _KICKED[order] = (time.time() if t is None else t, bool(went))


def _post(body):
    """POST body to this deployment's /api/order and do not wait for the work (KICK_READ): (word, code). word "sent"
    (no answer within KICK_READ: the callee runs), "done" (it answered 2xx already), "refused" (code: the error
    status), "failed" (it did not go out; code: the exception's name) or "off" (no self-call here). The bypass secret
    goes in a header, never in a log line."""
    base = self_base()
    if not base:
        return "off", None
    headers = {"Content-Type": "application/json", "Accept": "application/json",
               "User-Agent": "snapeyes-self-call/1"}      # what the Vercel logs show for these requests
    bypass = pay._env("VERCEL_AUTOMATION_BYPASS_SECRET")
    if os.environ.get("VERCEL") and _BYPASS.fullmatch(bypass):
        headers["x-vercel-protection-bypass"] = bypass
    try:
        r = requests.post(base + "/api/order", data=json.dumps(body), headers=headers,
                          timeout=(KICK_CONNECT, KICK_READ), allow_redirects=False)
    except requests.exceptions.ReadTimeout:
        return "sent", None
    except requests.RequestException as e:
        return "failed", type(e).__name__
    code = r.status_code
    r.close()
    return ("done" if 200 <= code < 300 else "refused"), code


def _hint(code):
    """What an error status of the self-call most likely means (log lines and the owner's note)."""
    if code == 401:
        return "a protected preview: set Protection Bypass for Automation"
    if code == 403:
        return ("refused: another SNAPEYES_TICKET_SECRET there, or the Vercel Firewall or Bot Protection challenged "
                "it (User-Agent snapeyes-self-call/1)")
    if code == 429:
        return "rate limited: the Vercel Firewall or Bot Protection"
    if code == 508:
        return "Vercel's loop protection"
    if isinstance(code, int) and 300 <= code < 400:
        return "a redirect: set SNAPEYES_SITE to the canonical address"
    return ""


def _refused_note(order, code, why):
    """One owner note per order when a self-call was answered with an error status: the server cannot move this
    order by itself here, and a configuration (or Vercel) is the likely cause. Never raises."""
    try:
        hint = _hint(code)
        what = {508: ("Vercel's loop protection (INFINITE_LOOP_DETECTED) stopped the server's call to itself. The "
                      "server cannot finish orders by itself on this deployment until that is solved: tell the "
                      "developer (OWNER_SETUP section 9, the self-call test: python scripts/order_admin.py "
                      "selfcall-probe)."),
                401: ("The deployment is protected (Vercel Authentication on a Preview): create Protection Bypass for "
                      "Automation (Vercel, Settings, Deployment Protection) and deploy again."),
                403: ("The call was refused: the deployment it went to has another SNAPEYES_TICKET_SECRET, or the "
                      "Vercel Firewall or Bot Protection challenged it. It sends the User-Agent snapeyes-self-call/1: "
                      "let it through in Vercel, Firewall."),
                429: ("The call was rate limited (the Vercel Firewall or Bot Protection). It sends the User-Agent "
                      "snapeyes-self-call/1: let it through in Vercel, Firewall.")}.get(code)
        if what is None:
            what = (f"The deployment answered HTTP {code}{' (' + hint + ')' if hint else ''}. Look at the Vercel log "
                    f"of /api/order around this time.")
        pay.owner_note(order, "self_call", f"SnapEyes: order {order}, the server could not ask for its next step "
                       f"(HTTP {code})",
                       f"Order {order} is paid. The server makes a paid order by calling itself once per step, and "
                       f"that call ({why}) was answered HTTP {code}.\n{what}\n\n"
                       f"This order is not lost: the customer's order page makes it while it is open, the daily run "
                       f"asks for it again once a day, and you get a reminder if it is still not ready {LATE_HOURS} "
                       f"hours after payment. Look at it in the admin panel (/admin, order {order}) or: python "
                       f"scripts/order_admin.py status {order}\n"
                       f"This note comes once per order.\n")
    except Exception as e:  # noqa: a note must never cost the caller its reply
        pay.log(f"order {order}: self-call note failed: {type(e).__name__}")


def kick(order, hop=0, busy=0, after=None, wait=0, why=""):
    """Ask for the next step of an order: POST /api/order {action: "advance"} to this deployment, and do not wait
    for it (KICK_READ). Returns "sent" (it went out, the step is running: no answer within KICK_READ), "done" (it
    answered 200 already), "refused" (an error status: 401 a protected preview, 403 a ticket this deployment does
    not accept or the Vercel Firewall, 508 Vercel's loop protection; the owner is told once per order), "off" (no
    self-call here), "no_time" or "failed". Never raises; the ticket is never logged."""
    try:
        store.check_order(order)
        if not self_base():
            if not _SAID_OFF["yes"]:
                _SAID_OFF["yes"] = True
                pay.log("server making: no self-call here (a local run without SNAPEYES_SELF_BASE): the order page "
                        "and the daily run drive the orders")
            return "off"
        if real_left() < KICK_NEED:
            pay.log(f"order {order}: no time left for the next step's self-call ({why})")
            _note_kick(order, False)
            return "no_time"
        body = {"action": "advance", "order": order, "ticket": L.mint_ticket(KIND + order, TICKET_TTL),
                "hop": int(hop), "busy": int(busy), "wait": int(wait), "why": str(why)[:40]}
        if isinstance(after, str) and _ID.fullmatch(after):
            body["after"] = after
        t0 = time.time()
        word, code = _post(body)
        if word == "sent":
            _note_kick(order, True, t0)
            pay.log(f"order {order}: next step asked for (hop {hop}{', busy ' + str(busy) if busy else ''}, {why})")
            return "sent"
        if word == "done":
            _note_kick(order, True, t0)
            return "done"
        _note_kick(order, False, t0)
        if word == "failed":
            pay.log(f"order {order}: the self-call did not go out: {code} ({why})")
            return "failed"
        if word != "refused":
            return word
        hint = _hint(code)
        pay.log(f"order {order}: the self-call was answered HTTP {code}{' (' + hint + ')' if hint else ''} ({why})")
        _refused_note(order, code, why)
        return "refused"
    except Exception as e:  # noqa: a self-call must never cost the caller its own reply
        pay.log(f"order {order}: self-call failed: {type(e).__name__}")
        return "failed"


# ----------------------------------------------------------------------------- who may start, who is on it
def may_start(mail=None):
    """May the server START this order (nothing made yet)? As the confirmation email this customer got said
    (mail_delivery.json "making": "server" or "page", written by pay.deliver_mail). A confirmation that went out
    without the mark (sent by hand: the admin panel's mailed_by_hand, or before the mark existed) was worded for the
    page starting it, so the server does not; an order that needs no email follows the texts in force
    (pay.server_starts)."""
    m = mail.get("making") if isinstance(mail, dict) else None
    if m in ("server", "page"):
        return m == "server"
    if isinstance(mail, dict) and mail.get("state") == "sent":
        return False
    return pay.server_starts()


def after_confirmation(order, auto=None):
    """The order confirmation just went out (or none is needed): ask for the first step where the server starts
    orders (auto: what the email just sent said, else the texts in force). Returns kick()'s word, or "page"."""
    try:
        if not (pay.server_starts() if auto is None else auto):
            return "page"
        return kick(order, why="confirmation")
    except Exception as e:  # noqa
        pay.log(f"order {order}: server making not asked for: {type(e).__name__}")
        return "failed"


def view(beat, order=None, now=None):
    """What the order page is told about the server's making (status "server"): {active, step, eye}. Active while
    advance.json is fresh and not "stopped", or when this instance asked for a step a moment ago."""
    now = time.time() if now is None else now
    b = beat if isinstance(beat, dict) else {}
    t = b.get("t") if isinstance(b.get("t"), (int, float)) and not isinstance(b.get("t"), bool) else None
    until = b.get("until") if isinstance(b.get("until"), (int, float)) and not isinstance(b.get("until"), bool) else None
    state = b.get("state")
    grace = max(0.0, until - t) if state == "waiting" and until is not None and t is not None else 0.0
    active = state in ("working", "next", "waiting") and t is not None and -60.0 < now - t < FRESH + grace
    if not active and order is not None:
        # a step asked for from here a moment ago that has not written advance.json yet (its word is older)
        r = _recent(order)
        active = bool(r and r[1] and (t is None or t < r[0]))
    working = active and state == "working"
    eye = b.get("eye") if working and isinstance(b.get("eye"), int) and not isinstance(b.get("eye"), bool) else None
    return {"active": bool(active), "step": b.get("step") if working and b.get("step") in ("eye", "compose") else None,
            "eye": eye}


def nudge(order, beat, why="page"):
    """Ask again for the server's making of an unfinished order whose making has BEGUN (the caller checked:
    making.json or a stored eye) when it has no live step: the order page's status call, and its make after an eye.
    True when a step is running or was just asked for. It never starts an order: only the confirmation email's
    sender (after_confirmation), the daily run (catch_up) and the order page's own make do, so the withdrawal page,
    which only reads the status, can never start the work that ends the right of withdrawal."""
    if view(beat, order)["active"]:
        return True
    r = _recent(order)
    t = beat.get("t") if isinstance(beat, dict) and isinstance(beat.get("t"), (int, float)) else None
    if r is not None and (t is None or t < r[0]):
        return False                     # asked from here a moment ago and it did not go out: not again yet
    return kick(order, why=why) in ("sent", "done")


# ----------------------------------------------------------------------------- the lease and the heartbeat
def take_lease(order, after=None):
    """This invocation's lease on the order's steps (advance.lock), or None when a live one holds it. A lease older
    than LEASE_STALE, unreadable, or held by `after` (the predecessor of this hop, which could not drop it in time)
    is taken over."""
    path = pay.order_path(order, "advance.lock")
    lid = secrets.token_hex(6)
    mine = store.json_bytes({"t": round(time.time(), 3), "id": lid})
    for _ in range(2):
        try:
            store.put(path, mine, "application/json", upsert=False, timeout=5.0, retry=False)
            return lid
        except store.StorageExists:
            pass
        cur = store.get_json(path, timeout=5.0, retry=False)
        if cur is None:
            continue                     # dropped a moment ago
        try:
            age = time.time() - float(cur.get("t"))
        except (TypeError, ValueError):
            age = LEASE_STALE + 1
        if (after and cur.get("id") == after) or not -60.0 < age < LEASE_STALE:
            store.put(path, mine, "application/json", upsert=True, timeout=5.0, retry=False)
            return lid
        return None
    return None


def drop_lease(order, lid):
    try:
        path = pay.order_path(order, "advance.lock")
        cur = store.get_json(path, timeout=4.0, retry=False)
        if isinstance(cur, dict) and cur.get("id") == lid:
            store.delete(path, timeout=4.0, retry=False)
    except Exception as e:  # noqa: the next hop takes it over (after), anyone else after LEASE_STALE
        pay.log(f"order {order}: lease not dropped: {type(e).__name__}")


def beat(order, state, **kw):
    """advance.json: what the server does or did last (state working / next / waiting / stopped). Never raises."""
    now = time.time()
    try:
        store.put(pay.order_path(order, "advance.json"),
                  store.json_bytes(dict(kw, state=state, t=round(now, 3), iso=pay.iso(now))), "application/json",
                  upsert=True, timeout=5.0, retry=False)
    except Exception as e:  # noqa: only the page's view of it is at stake
        pay.log(f"order {order}: advance.json not written: {type(e).__name__}")


# ----------------------------------------------------------------------------- the ready email
def ready_mail_once(order, rec, paid, released=None):
    """"Your artwork is ready" to the customer, once per order (mail_ready.json, claimed before sending), when an
    artwork is ready without a hold: the server's making and the order page's compose both call it. A held artwork
    the owner released had its email from the release (release.json): none is sent here. Returns "sent", "done"
    (sent or being sent before), "released", "off", "no_address", "transient" (tried again by the next step or the
    daily run) or "failed". Never raises."""
    try:
        if not pay.email_configured():
            return "off"
        to = paid.get("email") if isinstance(paid, dict) else None
        if not to:
            return "no_address"
        path = pay.order_path(order, "mail_ready.json")
        if released is None:
            released = store.exists(pay.order_path(order, "release.json"), timeout=6.0)
        if released:
            try:
                store.put(path, store.json_bytes({"state": "sent", "by": "release", "t": round(time.time(), 3)}),
                          "application/json", upsert=False, timeout=6.0)
            except store.StorageExists:
                pass
            return "released"
        if not pay.claim_once(path):
            return "done"
        k = pay.link_key(order, rec)
        if not k:
            pay._mark(path, "failed", result="link_unavailable")
            pay.log(f"order {order}: ready email NOT sent, the ticket secret changed since the order was made")
            return "failed"
        subject, text, html_body = pay.ready_mail(order, paid, k, checked=False)
        res = pay.send_mail(to, subject, text, f"snapeyes-ready-{order}", html_body)
        pay._mark(path, "retry" if res == "transient" else ("sent" if res == "sent" else "failed"), result=res)
        pay.log(f"order {order}: ready email {res}")
        return res
    except Exception as e:  # noqa: the artwork is on the order page all the same
        pay.log(f"order {order}: ready email failed: {type(e).__name__} {e}")
        return "transient"


# ----------------------------------------------------------------------------- one step
def refund_marks(order, paid):
    """Where a refund of the order is recorded: refunded.json (refunded in the Stripe Dashboard: the admin panel's
    mark_refunded, scripts/order_admin.py refunded) and the admin panel's own refund of the order's payment
    (ops.act_refund). A refund of a second, duplicate payment (extra_payment_*) is not a refund of the order."""
    out = [pay.order_path(order, "refunded.json")]
    pi = paid.get("payment_intent") if isinstance(paid, dict) else None
    if isinstance(pi, str) and pi:
        out.append(f"{REFUNDS_TOP}/{order}/{hashlib.sha256(pi.encode()).hexdigest()[:16]}.json")
    return out


def _facts(order, n, paid=None):
    folder = f"orders/{order}"
    js = lambda p: (lambda: store.get_json(f"{folder}/{p}", timeout=5.0, retry=False))
    ex = lambda p: (lambda: store.exists(f"{folder}/{p}", timeout=5.0, retry=False))
    marks = refund_marks(order, paid)
    r = pay.parallel([ex(f"eye_{i}.jpg") for i in range(1, n + 1)] +
                     [js("delivery.json"), js("review.json"), ex("release.json"), ex("deleted.json"), ex("expired.json"),
                      ex("withdrawn.json"), js("mail_delivery.json"), ex("making.json")] +
                     [lambda p=p: store.exists(p, timeout=5.0, retry=False) for p in marks])
    t = r[n:]
    return {"made": list(r[:n]), "delivery": t[0], "review": t[1], "released": bool(t[2]),
            "deleted": bool(t[3]) or bool(t[4]), "withdrawn": bool(t[5]), "mail": t[6], "making": bool(t[7]),
            "refunded": any(bool(x) for x in t[8:])}


def _clamp(v, lo, hi):
    try:
        v = int(v)
    except (TypeError, ValueError):
        v = lo
    return max(lo, min(hi, v))


def _answer(a):
    """What to do after a store.Answer of make_eye or compose_order: ("stop", why), ("next", delay, busy, why) or
    ("error", detail)."""
    reason = str(a.body.get("reason") or "")
    if reason == "withdrawn":
        return ("stop", "withdrawn")
    if reason == "deleted" or a.status == 410:
        return ("stop", "deleted")
    if reason in ("in_review", "render_rejected"):
        return ("stop", "review")
    if reason == "confirming":
        return ("stop", "confirming")
    if reason in ("test_payment", "not_paid", "payment_processing"):
        return ("stop", reason)
    if reason in ("eyes_not_ready", "busy_retry"):
        return ("next", 0, True, reason)
    if reason == "rendering":
        return ("next", _clamp(a.retry_after or 15, 5, WAIT_MAX), True, reason)
    if a.status == 503 or a.body.get("retry") is True:
        return ("next", _clamp(a.retry_after or 20, 5, WAIT_MAX), True, reason or "busy")
    return ("error", f"HTTP {a.status} {reason}")


def _step(order, rec, paid, hop, steps):
    """The first thing the order is missing, done (see the module). Returns a decision as _answer does."""
    spec = paid.get("spec") if isinstance(paid.get("spec"), dict) else {}
    n = spec.get("eyes")
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= pay.MAX_EYES:
        return ("error", "the paid record names no eye count")
    f = _facts(order, n, paid)
    if f["withdrawn"]:
        return ("stop", "withdrawn")
    if f["deleted"]:
        return ("stop", "deleted")
    if f["refunded"]:
        # the owner refunded it: nothing more is made or emailed by the server (a refund while the page drives it is
        # the owner's to explain)
        return ("stop", "refunded")
    dl = f["delivery"]
    if isinstance(dl, dict):
        if dl.get("needs_review") and not f["released"]:
            return ("stop", "review")
        beat(order, "working", step="mail", hop=hop)
        if ready_mail_once(order, rec, paid, f["released"]) == "transient":
            return ("next", 30, True, "ready_mail")
        return ("stop", "ready")
    if isinstance(f["review"], dict):
        if (str(f["review"].get("reason") or "").startswith(pay.MAIL_REVIEW) and isinstance(f["mail"], dict)
                and f["mail"].get("state") == "sent"):
            # the confirmation went out again a moment ago (the admin panel's resend) and its hold is being lifted
            # right after: look again shortly (a hold that stays ends the chain after MAX_BUSY looks)
            return ("next", 10, True, "hold_clearing")
        return ("stop", "review")
    c = pay.confirmation(order, rec, paid, cur=f["mail"], send=False)
    if c == "held":
        return ("stop", "review")
    if c == "waiting":
        return ("stop", "confirming")
    if not (f["making"] or any(f["made"])) and not may_start(f["mail"]):
        return ("stop", "page_starts")
    missing = [i for i, m in enumerate(f["made"], 1) if not m]
    if missing:
        wait = 0
        for eye in missing:
            beat(order, "working", step="eye", eye=eye, hop=hop)
            try:
                steps["make_eye"](order, rec, paid, eye)
                return ("next", 0, False, f"eye_{eye}")
            except store.Answer as a:
                if a.body.get("reason") == "rendering":
                    wait = max(wait, _clamp(a.retry_after or 15, 5, WAIT_MAX))
                    continue                 # another request is on this eye: the next missing one
                return _answer(a)
        return ("next", max(wait, 10), True, "rendering")
    beat(order, "working", step="compose", hop=hop)
    try:
        r = steps["compose_order"](order, rec, paid)
    except store.Answer as a:
        return _answer(a)
    if r.get("state") == "ready":
        if ready_mail_once(order, rec, paid) == "transient":
            return ("next", 30, True, "ready_mail")
        return ("stop", "ready")
    return ("stop", "review" if r.get("state") == "review" else str(r.get("state") or "unknown"))


def _num(v, hi):
    return _clamp(v, 0, hi) if isinstance(v, int) and not isinstance(v, bool) else 0


def _reply(order, state, why, **kw):
    return dict(kw, ok=True, order=order, state=state, why=why)


def advance(body, steps):
    """POST /api/order {action: "advance", order, ticket, hop, busy, wait?, after?}: the server's one step (see the
    module). steps: {"make_eye": fn(order, rec, paid, eye), "compose_order": fn(order, rec, paid)} from api/order.py.
    403 forbidden without this order's internal ticket, before anything is read. With "probe" instead of an order:
    one hop of the self-call test (probe)."""
    if "probe" in body:
        return probe(body)
    order = body.get("order") if isinstance(body.get("order"), str) else ""
    if not store.ORDER_RE.fullmatch(order) or not ticket_ok(order, body.get("ticket")):
        pay.log("advance refused: no valid internal ticket")
        raise store.Answer(403, "forbidden", "Not allowed.", False)
    hop, busy, wait = _num(body.get("hop"), 100000), _num(body.get("busy"), 1000), _num(body.get("wait"), WAIT_MAX)
    after = body.get("after") if isinstance(body.get("after"), str) and _ID.fullmatch(body.get("after")) else None
    why = pay.clean_text(body.get("why"), 40)
    if wait:
        # a relay: the step before had no time left to wait out a busy answer, so this one waits, then asks for it
        wait = min(wait, max(0, int(real_left() - KICK_NEED - 1)))
        beat(order, "waiting", until=round(time.time() + wait, 3), why=why, hop=hop)
        time.sleep(wait)
        return _reply(order, "waited", why, next=kick(order, hop + 1, busy, after=after, why=why))
    rec, paid = pay.parallel([lambda: store.get_json(pay.order_path(order, "order.json"), timeout=6.0, retry=False),
                              lambda: pay.get_paid(order, timeout=6.0)])
    if not isinstance(rec, dict) or not paid:
        pay.unindex_making(order)
        return _reply(order, "stopped", "not_paid")
    if not pay.paid_counts(paid):
        pay.unindex_making(order)
        return _reply(order, "stopped", "test_payment")
    if hop >= MAX_HOPS:
        pay.log(f"order {order}: the server's making stops after {hop} steps: the order page and the daily run go on")
        beat(order, "stopped", why="hops", hop=hop)
        return _reply(order, "stopped", "hops")
    if hop == 0:
        pay.index_making(order, paid.get("paid_at"))
    lid = take_lease(order, after)
    if lid is None:
        pay.log(f"order {order}: a step is running already, this call leaves (hop {hop}, {why})")
        return _reply(order, "busy", "lease")
    try:
        d = _step(order, rec, paid, hop, steps)
    except store.Answer as a:
        d = _answer(a)
    except Exception as e:  # noqa: sorted below
        if store.lost(e):
            # a paid render may be lost (api/order.py make_eye counted it): never retried as busy, since each retry
            # would be another paid render; the page or the daily run tries once more, the next loss holds it
            d = ("lost", f"{type(e).__name__}: {e}", store.lost(e))
        elif isinstance(e, (store.StorageError, pay.PayBusy)):
            pay.log(f"order {order}: step not done, storage or Stripe busy: {pay.scrub(str(e))[:200]}")
            d = ("next", 10, True, "storage_busy")
        else:                            # anything else is an error a person must see
            d = ("error", f"{type(e).__name__}: {e}")
    finally:
        drop_lease(order, lid)
    return _then(order, hop, busy, lid, d)


def _then(order, hop, busy, lid, d):
    """After a step: stop, or ask for the next one (after its back-off)."""
    if d[0] == "error":
        detail = pay.scrub(str(d[1]))[:300]
        pay.log(f"order {order}: the server's making stopped on an error: {detail}")
        beat(order, "stopped", why="error", hop=hop)
        pay.owner_note(order, "making_error", f"SnapEyes: order {order} could not be finished automatically",
                       f"Order {order} is paid, but the server could not make it by itself: {detail}.\n"
                       f"Nothing is lost: the customer's order page tries again whenever it is opened, and the daily "
                       f"run tries once a day. Look at it in the admin panel (/admin, order {order}) or: python "
                       f"scripts/order_admin.py status {order}\n")
        return _reply(order, "stopped", "error")
    if d[0] == "lost":
        detail = pay.scrub(str(d[1]))[:300]
        pay.log(f"order {order}: the server's making stopped: a paid render may be lost ({detail})")
        beat(order, "stopped", why="render_lost", hop=hop)
        pay.owner_note(order, "render_lost", f"SnapEyes: order {order} could not be finished automatically "
                       f"(a paid render was lost)",
                       f"Order {order} is paid. The server had an eye rendered (the image model answered, about "
                       f"$0.15), but the result was lost: {detail}.\n"
                       f"The server does not try again by itself right away, since every try is another paid render. "
                       f"One more try comes when the customer's order page asks for it or the daily run does; if "
                       f"that one is lost too, the order is held for you (review) and nothing more is rendered for "
                       f"it until you clear the review.\n"
                       f"Check the storage (Supabase: is it up, the project's quota, the bucket's file size limit) "
                       f"and the Vercel log of /api/order for this order. Look at it in the admin panel (/admin, "
                       f"order {order}) or: python scripts/order_admin.py status {order}\n"
                       f"This note comes once per order.\n")
        return _reply(order, "stopped", "render_lost")
    if d[0] == "stop":
        why = d[1]
        beat(order, "stopped", why=why, hop=hop)
        if why in FINAL:
            pay.unindex_making(order)
        pay.log(f"order {order}: server making stops: {why} (step {hop})")
        return _reply(order, "stopped", why)
    _, delay, counts, why = d
    busy = busy + 1 if counts else 0
    if busy > MAX_BUSY:
        beat(order, "stopped", why="busy", hop=hop)
        pay.log(f"order {order}: still busy after {MAX_BUSY} tries ({why}): the order page and the daily run go on")
        pay.owner_note(order, "making_busy", f"SnapEyes: order {order} could not be finished automatically (busy)",
                       f"Order {order} is paid, but the server's making gave up after {MAX_BUSY} busy answers in a "
                       f"row (the last: {why}): the image model, the storage or Stripe did not take the work. "
                       f"Nothing was paid for twice.\n"
                       f"The order is not lost: the customer's order page goes on while it is open (and asks the "
                       f"server again), the daily run asks for it once a day, and you get a reminder if it is still "
                       f"not ready {LATE_HOURS} hours after payment. If it stays busy, look at the Vercel log of "
                       f"/api/order and the admin panel (/admin, order {order}) or: python scripts/order_admin.py "
                       f"status {order}\n"
                       f"This note comes once per order.\n")
        return _reply(order, "stopped", "busy")
    wait = 0
    if delay > 0:
        beat(order, "waiting", until=round(time.time() + delay, 3), why=why, hop=hop)
        if real_left() >= delay + KICK_NEED + 1.0:
            time.sleep(delay)
        else:
            wait = delay                 # a relay hop waits instead
    else:
        beat(order, "next", why=why, hop=hop)
    r = kick(order, hop + 1, busy, after=lid, wait=wait, why=why)
    if r == "failed" and real_left() >= KICK_NEED:
        # it did not go out (a connection that failed on the way): once more. A second callee of the same hop finds
        # the first one's lease and leaves, so nothing is done twice
        r = kick(order, hop + 1, busy, after=lid, wait=wait, why=why)
    if r not in ("sent", "done"):
        beat(order, "stopped", why=f"self_call_{r}", hop=hop)
        pay.log(f"order {order}: the next step could not be asked for ({r}): the order page and the daily run go on")
        return _reply(order, "stopped", f"self_call_{r}")
    return _reply(order, "next", why, delay=delay)


# ----------------------------------------------------------------------------- the daily catch-up
def _catch_facts(order):
    folder = f"orders/{order}"
    js = lambda p: (lambda: store.get_json(f"{folder}/{p}", timeout=8.0))
    ex = lambda p: (lambda: store.exists(f"{folder}/{p}", timeout=8.0))
    r = pay.parallel([lambda: pay.get_paid(order), js("delivery.json"), js("review.json"), ex("release.json"),
                      ex("withdrawn.json"), ex("deleted.json"), ex("expired.json"), js("mail_delivery.json"),
                      ex("making.json"), js("advance.json"), js("mail_ready.json"), ex("note_late.json")])
    f = dict(zip(("paid", "delivery", "review", "released", "withdrawn", "deleted", "expired", "mail", "making",
                  "beat", "ready", "late_noted"), r))
    f["refunded"] = bool(f["paid"]) and any(bool(x) for x in pay.parallel(
        [lambda p=p: store.exists(p, timeout=8.0) for p in refund_marks(order, f["paid"])]))
    return f


def _verdict(f, now):
    """What the daily run does with one indexed order: "drop" (nothing more to do, or too old), "kick", "held"
    (waits for the owner) or "wait" (young, confirmation not out, the server on it, or the page starts it)."""
    paid = f["paid"]
    if not paid or not pay.paid_counts(paid) or f["withdrawn"] or f["deleted"] or f["expired"] or f.get("refunded"):
        return "drop"
    t = paid.get("paid_at")
    t = t if isinstance(t, (int, float)) and not isinstance(t, bool) else None
    if t is not None and now - t > INDEX_DAYS * 86400:
        return "drop"
    dl = f["delivery"]
    if isinstance(dl, dict):
        if dl.get("needs_review") and not f["released"]:
            return "held"
        rm = f["ready"]
        if (f["released"] or not pay.email_configured() or not paid.get("email")
                or (isinstance(rm, dict) and rm.get("state") in ("sent", "failed"))):
            return "drop"                # ready, and its email went out (or cannot): nothing left
    elif isinstance(f["review"], dict):
        return "held"
    else:
        mail = f["mail"]
        if pay.confirmation_needed(paid) and not (isinstance(mail, dict) and mail.get("state") == "sent"):
            return "wait"                # the webhook's retries and the owner's note handle the confirmation
        if not f["making"] and not may_start(mail):
            return "wait"                # the texts this customer got say the order page starts it
    if t is None or now - t < CATCHUP_AGE or view(f["beat"], now=now)["active"]:
        return "wait"
    return "kick"


def _late(f, now):
    """Why an indexed paid order is still not ready LATE_HOURS after payment, or None: not late, reminded before
    (note_late.json), ready, or held for the owner (a hold has its own notes and reminder, cleanup._reviews)."""
    paid = f["paid"]
    if (not paid or not pay.paid_counts(paid) or f["withdrawn"] or f["deleted"] or f["expired"] or f["late_noted"]
            or f.get("refunded") or isinstance(f["delivery"], dict) or isinstance(f["review"], dict)):
        return None
    t = paid.get("paid_at")
    if not isinstance(t, (int, float)) or isinstance(t, bool) or now - t < LATE_HOURS * 3600:
        return None
    mail = f["mail"]
    if pay.confirmation_needed(paid) and not (isinstance(mail, dict) and mail.get("state") == "sent"):
        return ("its order confirmation email has not gone out, and nothing is made before it has (Resend, the legal "
                "texts at /legal/order-mail.json); send it again from the admin panel once the cause is fixed")
    if not f["making"] and not may_start(mail):
        return ("making has not begun: the texts this customer was given say it starts when they open their order "
                "page, and they have not opened it since. Nothing may be started for them (that would end their "
                "right of withdrawal); you could write to them")
    b = f["beat"] if isinstance(f["beat"], dict) else None
    if b is None:
        return "the server has not taken a step for it"
    return (f"the server's making {'stopped' if b.get('state') == 'stopped' else 'last did: ' + str(b.get('state'))}"
            f" ({b.get('why') or b.get('step') or 'no reason recorded'}, {b.get('iso') or '?'} UTC)")


def _late_note(order, f, why, kicked, now):
    """The one reminder for a paid order that is not ready LATE_HOURS after payment. Returns owner_note's word."""
    paid = f["paid"]
    n = (paid.get("spec") or {}).get("eyes")
    made = "?"
    if isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= pay.MAX_EYES:
        got = pay.parallel([lambda i=i: store.exists(f"orders/{order}/eye_{i}.jpg", timeout=6.0)
                            for i in range(1, n + 1)])
        made = f"{sum(1 for g in got if g)} of {n}"
    hours = int((now - paid["paid_at"]) // 3600)
    return pay.owner_note(order, "late", f"SnapEyes: order {order} is paid but not ready after {hours} h",
                          f"Order {order} was paid on {pay.iso(paid['paid_at'])} (UTC), {hours} hours ago, and its "
                          f"file is not ready yet. Our terms promise it within 48 hours of payment.\n"
                          f"Why: {why}.\nEyes made: {made}.\n"
                          + ("The daily run has just asked the server to go on with it: look again in a few "
                             "minutes.\n" if kicked else "") +
                          f"\nLook at it in the admin panel (/admin, order {order}): 'render' makes a missing eye "
                          f"(the server then goes on with the rest), 'recompose' the artwork; or: python "
                          f"scripts/order_admin.py status {order}\n"
                          f"This is the only such reminder for this order.\n")


def catch_up(yes=True, stop_left=10.0, out=None, max_seconds=CATCHUP_SECONDS):
    """The daily clean-up's part (api/_lib/cleanup.py): every paid, confirmed, unfinished order older than
    CATCHUP_AGE that nobody is making (no live advance.json) gets the server's making asked for again, at most
    CATCHUP_MAX a run (the self-calls go out at once; each runs in its own invocation). Orders that need nothing more
    leave the index. Then every indexed paid order that is not held for the owner and still not ready LATE_HOURS after
    payment gets ONE owner reminder (note_late.json), at most LATE_MAX a run. yes=False: nothing is asked for, sent
    or changed. Never raises. Returns {orders, kicked, dropped, held, waiting, late} (+ more, + off when this run
    cannot make self-calls: a local run)."""
    say = out or pay.log
    res = {"orders": 0, "kicked": 0, "dropped": 0, "held": 0, "waiting": 0, "late": 0, "more": False}
    until = time.time() + max_seconds
    try:
        base = self_base()
        if not base:
            res["off"] = True
        names = [r["name"][:-5] for r in store.list_all(pay.MAKING_INDEX)
                 if not r["folder"] and r["name"].endswith(".json") and store.ORDER_RE.fullmatch(r["name"][:-5])]
        todo, late = [], []
        now = time.time()
        for i in range(0, len(names), 4):
            if L.time_left() < stop_left or time.time() > until:
                res["more"] = True
                break
            batch = names[i:i + 4]
            facts = pay.parallel([lambda o=o: _catch_facts(o) for o in batch])
            for order, f in zip(batch, facts):
                res["orders"] += 1
                v = _verdict(f, now)
                if v == "drop":
                    res["dropped"] += 1
                    say(f"{'catch-up: done with' if yes else 'catch-up: would be done with'} order {order}")
                    if yes:
                        pay.unindex_making(order)
                elif v == "kick":
                    todo.append(order)
                elif v == "held":
                    res["held"] += 1
                else:
                    res["waiting"] += 1
                why = _late(f, now) if v != "drop" else None
                if why:
                    late.append((order, f, why))
        if len(todo) > CATCHUP_MAX:
            res["more"] = True
            todo = todo[:CATCHUP_MAX]
        kicked = set()
        if not yes:
            for o in todo:
                say(f"catch-up: would ask the server to go on with order {o}")
            res["kicked"] = len(todo)
        elif todo and base:
            got = pay.parallel([lambda o=o: kick(o, why="daily") for o in todo])
            res["kicked"] = sum(1 for g in got if g in ("sent", "done"))
            for o, g in zip(todo, got):
                say(f"catch-up: order {o} unfinished, the server was asked to go on: {g}")
                if g in ("sent", "done"):
                    kicked.add(o)
        elif todo:
            say(f"catch-up: {len(todo)} unfinished order(s), but no self-call here: {', '.join(todo)}")
        # the owner hears of every paid order that is not moving, in time for the 48 hours the terms promise
        if len(late) > LATE_MAX:
            res["more"] = True
            late = late[:LATE_MAX]
        for order, f, why in late:
            if not yes:
                say(f"catch-up: would remind the owner: order {order} not ready {LATE_HOURS} h after payment ({why})")
                res["late"] += 1
                continue
            if L.time_left() < stop_left:
                res["more"] = True
                break
            r = _late_note(order, f, why, order in kicked, now)
            say(f"catch-up: order {order} not ready {LATE_HOURS} h after payment, the owner reminded: {r}")
            if r == "sent":
                res["late"] += 1
    except Exception as e:  # noqa: the deletions of the clean-up must not wait on this
        pay.log(f"clean-up: catch-up failed: {type(e).__name__} {e}")
    return res


# ----------------------------------------------------------------------------- the self-call test
def probe(body):
    """POST /api/order {action: "advance", probe: <id>, ticket, hop}: one hop of the self-call test
    (scripts/order_admin.py selfcall-probe). A hop does what one step of an order does, without the order: it notes
    that it ran (ops/selfcall/<id>/hop_<nn>.json), works PROBE_WORK seconds (longer than KICK_READ, so its caller has
    left before it answers, as after a render), then asks for the next hop with the same self-call (the same
    address, headers and timeouts as kick), up to PROBE_HOPS, and notes what that call got. No order is read or
    written, nothing is paid. 403 forbidden without the test's own ticket ("selfcall-probe-<id>"), which only the
    ticket secret signs, before anything is written."""
    pid = body.get("probe")
    if not (isinstance(pid, str) and _ID.fullmatch(pid)) or not L.check_ticket(body.get("ticket"), kind=PROBE_KIND + pid):
        pay.log("self-call test refused: no valid ticket")
        raise store.Answer(403, "forbidden", "Not allowed.", False)
    hop = _num(body.get("hop"), PROBE_HOPS)
    path = f"{PROBE_TOP}/{pid}/hop_{hop:02d}.json"
    t0 = time.time()
    rec = {"hop": hop, "t": round(t0, 3), "iso": pay.iso(t0), "left": round(L.time_left(), 1)}
    store.put(path, store.json_bytes(rec), "application/json", upsert=True, timeout=5.0, retry=False)
    time.sleep(PROBE_WORK)
    if hop + 1 >= PROBE_HOPS:
        rec["next"] = "last"
    elif real_left() < KICK_NEED:
        rec["next"] = "no_time"
    else:
        rec["next"], rec["code"] = _post({"action": "advance", "probe": pid, "hop": hop + 1,
                                          "ticket": L.mint_ticket(PROBE_KIND + pid, TICKET_TTL)})
    rec["done"] = round(time.time(), 3)
    try:
        store.put(path, store.json_bytes(rec), "application/json", upsert=True, timeout=5.0, retry=False)
    except store.StorageError as e:
        pay.log(f"self-call test {pid}: hop {hop} not noted: {e}")
    code = rec.get("code")
    hint = _hint(code) if isinstance(code, int) else ""
    pay.log(f"self-call test {pid}: hop {hop} ran, the next: {rec['next']}{' ' + str(code) if code else ''}"
            f"{' (' + hint + ')' if hint else ''}")
    return {"ok": True, "probe": pid, "hop": hop, "next": rec["next"], "code": code}
