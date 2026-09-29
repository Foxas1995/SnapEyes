# -*- coding: utf-8 -*-
"""The daily clean-up: the deletions the privacy policy promises, run by Vercel Cron once a day (vercel.json
"crons": GET /api/order with "Authorization: Bearer <CRON_SECRET>", api/order.py cron_purge) and by the owner with
scripts/order_admin.py cleanup. Each step is idempotent and safe to repeat or to miss (Vercel may skip a run or send
it twice): a missed day is caught up by the next run, and a second run finds nothing left to do.

  1. receipts of withdrawal statements Resend did not take at the time are sent again (withdraw.retry_due), for at
     most withdraw.RETRY_SECONDS, so a queue of them never crowds out the deletions below; then the owner's digest
     of the finished days' withdrawal statements that matched no order or named an order never paid
     (withdraw.send_digests: one email a day instead of one per statement)
  2. UNPAID orders older than 26 h are deleted with their images (policy: within 30 days). Only after Stripe was
     asked: a session paid without paid.json is recorded as paid instead (the customer gets the confirmation), one
     still open or settling is kept, and nothing is deleted when Stripe cannot be asked (pay.stripe_verdict). A
     kept order is marked in cleanup/kept/ and asked again every day, also after its day left the window (_kept);
     from KEPT_NOTE_DAYS on, the owner gets one note a day naming those still kept
  3. the images of WITHDRAWN orders go 14 days after the withdrawal (cleanup/withdrawn/); the record stays. An
     order withdrawn while its payment was still settling is asked of Stripe first, like step 2. From
     REFUND_REMIND_DAYS after the withdrawal, a paid order the owner has not marked refunded
     (scripts/order_admin.py refunded ORDER) gets ONE reminder note before the refund is due
  4. the files of PAID orders go 12 months after payment (pay.expire_paid); the records stay (order number, date,
     price, payment, email, the artwork's details, consent, withdrawal statements: the policy's "Order records")
  5. the upload and statement markers older than a few days (and the withdrawal function's monthly receipt marks
     after the next month), the clean-up's own day marks, and withdrawal statements that matched no order
     (withdrawals/<yymm>/) 12 months after their month
  6. the site's other logs: events.purge_old() when api/_lib/events.py exists (the owner's admin tools keep their
     own retention there), and the audit log ops/audit/ after AUDIT_KEEP_MONTHS (24 months), by the dates in its
     names (_audit)
Order folders are named by the day they were made (yymmdd-...), so a run lists only the days it needs: the last
UNPAID_WINDOW days for step 2, the EXPIRE_WINDOW days before the 12-month cut-off for step 4, minus the days a run
already finished (cleanup/done_unpaid/<day>, cleanup/done_expired/<day>). The run stops with more: true when less
than stop_left seconds of the 60 s function are left; the next run goes on. Logged line by line ("snapeyes pay: ")."""
import os, re, time, hashlib, calendar, inspect, importlib
from . import iris as L
from . import store
from . import pay
from . import withdraw as W

UNPAID_WINDOW = 35           # days of orders step 2 looks at (the policy promises deletion within 30 days)
EXPIRE_WINDOW = 60           # days before the 12-month cut-off step 4 looks at (a longer gap: order_admin expire-paid)
WITHDRAWN_FILES_DAYS = 14    # the images of a withdrawn order are kept this long after the withdrawal (the refund)
REFUND_REMIND_DAYS = 10      # a withdrawn paid order not marked refunded this long after the withdrawal: one reminder
KEPT_TOP = "cleanup/kept"    # unpaid orders kept because Stripe could not vouch for them: asked again every day
KEPT_NOTE_DAYS = 25          # ... and named to the owner once a day when they are this old (the policy says 30)
FIRST_DAY = "260901"         # no order folder is older than this code
UNMATCHED_KEEP_DAYS = 396    # statements that matched no order: kept 12 months after their month ended, then deleted
AUDIT_TOP = "ops/audit"      # the admin tools' audit log (api/_lib/ops.py: ops/audit/<YYYY-MM-DD>/...), kept
AUDIT_KEEP_MONTHS = 24       # 24 months, then deleted by its day
REFUNDS_TOP = "ops/refunds"  # the admin panel's refund records (api/_lib/ops.py act_refund): a refund made there counts
LOCK = "cleanup/running.json"
LOCK_STALE = 120             # a lock older than this belongs to a run that died (a function lives at most 60 s)


def _day_ts(d):
    """The start (00:00 UTC) of a yymmdd day as unix seconds."""
    return calendar.timegm(time.strptime("20" + d, "%Y%m%d"))


def _days(t0, t1):
    """The yymmdd days from t0 to t1 (unix seconds), both included, none before FIRST_DAY."""
    out, t = [], t0 - (t0 % 86400)
    while t <= t1:
        d = pay.day(t)
        if d >= FIRST_DAY:
            out.append(d)
        t += 86400
    return out


def _done(kind):
    return {r["name"][:-5] for r in store.list_all(f"cleanup/done_{kind}") if r["name"].endswith(".json")}


def _mark_done(kind, d):
    try:
        store.put(f"cleanup/done_{kind}/{d}.json", store.json_bytes({"t": int(time.time())}), "application/json",
                  upsert=True, timeout=6.0)
    except store.StorageError as e:
        pay.log(f"clean-up: day mark {kind} {d} not stored: {e}")


def _lock():
    """Only one run at a time (a second Vercel invocation of the same run leaves at once)."""
    mine = store.json_bytes({"t": int(time.time())})
    try:
        store.put(LOCK, mine, "application/json", upsert=False, timeout=6.0)
        return True
    except store.StorageExists:
        cur = store.get_json(LOCK, timeout=6.0) or {}
        if time.time() - float(cur.get("t") or 0) < LOCK_STALE:
            return False
        store.put(LOCK, mine, "application/json", upsert=True, timeout=6.0)
        return True


def _unlock():
    try:
        store.delete(LOCK, timeout=6.0)
    except store.StorageError as e:
        pay.log(f"clean-up: lock not removed (the next run takes it over after {LOCK_STALE} s): {e}")


def run(yes=True, stop_left=10.0, out=None, lock=True):
    """One clean-up run. yes=False: nothing is changed anywhere (a dry run for the owner: Stripe is still asked,
    nothing recorded). Returns the counts of every step and more: true when it stopped for time."""
    say = out or pay.log
    t0 = time.time()
    if lock and yes and not _lock():
        say("clean-up: another run is going on, this one leaves")
        return {"ok": True, "skipped": "running"}
    res = {"ok": True, "more": False}
    try:
        # the receipts are due without delay, so they go first, but only for their fixed share of the run
        # (RETRY_SECONDS): whatever is still queued waits for the next run, and the deletions below always run
        boxed = stop_left >= 0        # the owner's run (scripts/order_admin.py cleanup) has no time limit
        res["receipts"] = W.retry_due(stop_left, say, W.RETRY_SECONDS if boxed else 1e9) if yes else {}
        late = bool(res["receipts"].pop("more", False))
        res["digest"] = W.send_digests(yes, stop_left, say, W.DIGEST_SECONDS if boxed else 1e9)
        late = bool(res["digest"].pop("more", False)) or late
        if not res["more"]:
            res["unpaid"] = _unpaid(yes, stop_left, say)
            res["more"] = res["unpaid"].pop("more", False)
        if not res["more"]:
            res["withdrawn"] = _withdrawn(yes, stop_left, say)
            res["more"] = res["withdrawn"].pop("more", False)
        if not res["more"]:
            res["expired"] = _expire(yes, stop_left, say)
            res["more"] = res["expired"].pop("more", False)
        if not res["more"]:
            m = {"more": False}
            res["markers"] = pay.purge_markers(yes, stop_left, m) + _old_day_marks(yes) + W.purge_addr_marks(yes)
            res["more"] = m["more"]
        if not res["more"]:
            res["unmatched"] = _old_unmatched(yes, say)
        if not res["more"]:
            res["events"] = _events(yes, stop_left, say)
            res["audit"] = _audit(yes, stop_left, say)
            res["more"] = bool(isinstance(res["events"], dict) and res["events"].get("more")) or \
                res["audit"].pop("more", False)
        res["more"] = res["more"] or late
    finally:
        if lock and yes:
            _unlock()
    res["seconds"] = round(time.time() - t0, 1)
    say(f"clean-up {'done' if not res['more'] else 'stopped for time (the next run goes on)'}: "
        f"{ {k: v for k, v in res.items() if k != 'ok'} }")
    return res


def _unpaid(yes, stop_left, say):
    now = time.time()
    cutoff = now - pay.PURGE_HOURS * 3600
    done = _done("unpaid")
    days = [d for d in _days(now - UNPAID_WINDOW * 86400, cutoff) if d not in done]
    by_day = pay.day_folders(days)
    names = sorted({o for rows in by_day.values() for o in rows})
    r = pay.purge_unpaid(pay.PURGE_HOURS, yes=yes, out=say, names=names, stop_left=stop_left, markers=False)
    left = set(r.pop("left"))
    kept = r.pop("kept_orders", [])
    if yes:
        for o in kept:
            # asked again every day by _kept, also once its day has left the window (never forgotten)
            try:
                store.put(f"{KEPT_TOP}/{o}.json", store.json_bytes({"t": int(now)}), "application/json", upsert=False,
                          timeout=6.0)
            except store.StorageExists:
                pass
            except store.StorageError as e:
                pay.log(f"clean-up: kept mark of {o} not stored: {e}")
    finished = 0
    for d in days:
        # finished: every order made that day is older than the cut-off, and none of them is still unpaid here
        if yes and not r["more"] and _day_ts(d) + 86400 <= cutoff and not any(o in left for o in by_day[d]):
            _mark_done("unpaid", d)
            finished += 1
    r["days"], r["days_finished"] = len(days), finished
    if not r["more"]:
        k = _kept(yes, stop_left, say, set(names))
        r["kept_later"] = k
        r["more"] = k.pop("more", False)
    return r


def _kept(yes, stop_left, say, seen):
    """Unpaid orders a run had to keep because Stripe could not vouch for them (pay.stripe_verdict "open" or
    "unknown": no Stripe key any more, a live session and a test key, no answer) are listed in cleanup/kept/ and
    asked again every day, also once their day has left UNPAID_WINDOW, so none is forgotten. A mark goes when its
    order is deleted, recorded as paid or gone. Those kept longer than KEPT_NOTE_DAYS since they were made reach the
    owner in ONE note a day (the privacy policy promises the deletion of unpaid orders within 30 days: check the
    session in Stripe, then python scripts/order_admin.py erase ORDER --yes). Returns {marks, deleted, noted}."""
    res = {"marks": 0, "deleted": 0, "noted": 0, "more": False}
    now = time.time()
    late = []
    for row in store.list_all(KEPT_TOP):
        name = row["name"]
        if row["folder"] or not name.endswith(".json") or not store.ORDER_RE.fullmatch(name[:-5]):
            continue
        if L.time_left() < stop_left:
            res["more"] = True
            break
        order, mark = name[:-5], f"{KEPT_TOP}/{name}"
        res["marks"] += 1
        rec, paid = pay.parallel([lambda: store.get_json(f"orders/{order}/order.json", timeout=8.0),
                                  lambda: store.exists(f"orders/{order}/paid.json", timeout=8.0)])
        if not isinstance(rec, dict) or paid:
            if yes:
                store.delete(mark, timeout=6.0)
            continue
        if order not in seen:
            r = pay.purge_unpaid(pay.PURGE_HOURS, yes=yes, out=say, names=[order], stop_left=stop_left, markers=False)
            if r["deleted"] or r["recorded"]:
                res["deleted"] += r["deleted"]
                if yes:
                    store.delete(mark, timeout=6.0)
                continue
        made = rec.get("created_at") if isinstance(rec.get("created_at"), (int, float)) else now
        if now - made >= KEPT_NOTE_DAYS * 86400:
            late.append((order, rec.get("created"), pay.order_sessions(rec, n=3)))
    if late:
        res["noted"] = len(late)
        lines = "\n".join(f"  {o}  made {c}  Stripe sessions {', '.join(s) or '-'}" for o, c, s in late[:40])
        if not yes:
            say(f"would tell the owner about {len(late)} unpaid order(s) kept for {KEPT_NOTE_DAYS} days or more")
        else:
            pay.note_once(f"notes/unpaid_kept_{pay.day()}.json", "unpaid_kept",
                          f"SnapEyes: {len(late)} unpaid order(s) could not be deleted, please check",
                          f"These unpaid orders are {KEPT_NOTE_DAYS} days old or more, but the daily clean-up cannot "
                          f"delete them: Stripe could not confirm that their payment page was never paid (no Stripe "
                          f"key here, a live payment page and a test key, or Stripe did not answer). The privacy "
                          f"policy promises to delete unpaid orders within 30 days.\n\n{lines}\n"
                          + (f"  ... and {len(late) - 40} more\n" if len(late) > 40 else "") +
                          f"\nFor each: look up the session in the Stripe Dashboard. Not paid: python "
                          f"scripts/order_admin.py erase ORDER --yes. Paid: python scripts/order_admin.py purge "
                          f"--yes records it (with STRIPE_SECRET_KEY set). This note comes once a day while any is "
                          f"left.\n")
    return res


def _withdrawn(yes, stop_left, say):
    """Step 3: the images of orders withdrawn more than WITHDRAWN_FILES_DAYS ago, and the refund reminders."""
    res = {"orders": 0, "files": 0, "kept": 0, "reminders": 0, "more": False}
    cutoff = time.time() - WITHDRAWN_FILES_DAYS * 86400
    remind = time.time() - REFUND_REMIND_DAYS * 86400
    for row in store.list_all("cleanup/withdrawn"):
        if L.time_left() < stop_left:
            res["more"] = True
            break
        name = row["name"]
        if row["folder"] or not name.endswith(".json") or not store.ORDER_RE.fullmatch(name[:-5]):
            continue
        order, mark = name[:-5], f"cleanup/withdrawn/{name}"
        m = store.get_json(mark, timeout=8.0) or {}
        if not isinstance(m.get("t"), (int, float)):
            continue
        if m["t"] <= remind:
            res["reminders"] += _refund_reminder(order, m["t"], yes, say)
        if m["t"] > cutoff:
            continue
        if not store.exists(f"orders/{order}/paid.json"):
            rec = store.get_json(f"orders/{order}/order.json")
            if isinstance(rec, dict):
                # withdrawn while a payment was settling: has it arrived meanwhile? (then it is recorded, and the
                # owner told to refund it). One still settling, or Stripe not reachable: ask again tomorrow
                verdict = pay.stripe_verdict(order, rec, record=yes)
                if verdict in ("open", "unknown"):
                    res["kept"] += 1
                    say(f"withdrawn {order}: its payment is still settling or unknown, kept for now")
                    continue
        n, _ = pay.erase_files(order, "withdrawn", yes, say)
        res["orders"] += 1
        res["files"] += n
        if yes:
            store.delete(mark, timeout=6.0)
    return res


def _refund_reminder(order, t, yes, say):
    """One note to the owner before the refund of a withdrawn PAID order is due (the statement's refund_by: 14 days
    after the withdrawal, withdraw.REFUND_DAYS), unless
    it is marked refunded: orders/<order>/refunded.json (scripts/order_admin.py refunded ORDER), or the admin
    panel's refund record of that payment (ops/refunds/<order>/<sha256(payment intent)[:16]>.json, api/_lib/ops.py
    act_refund). The note at the withdrawal was the only one before. Returns 1 when a reminder went (or would go),
    else 0. Never raises."""
    try:
        paid = pay.get_paid(order)
        if not paid:
            return 0
        pi = paid.get("payment_intent") if isinstance(paid.get("payment_intent"), str) else ""
        checks = [f"orders/{order}/refunded.json", f"orders/{order}/note_refund_reminder.json"]
        if pi:
            checks.append(f"{REFUNDS_TOP}/{order}/{hashlib.sha256(pi.encode('utf-8')).hexdigest()[:16]}.json")
        if any(pay.parallel([lambda p=p: store.exists(p, timeout=8.0) for p in checks])):
            return 0
        amount = pay.amount_text(paid.get("amount_total") or 0, "en")
        due = pay.iso(t + W.REFUND_DAYS * 86400)
        if not yes:
            say(f"would remind the owner to refund {order} ({amount}, due by {due})")
            return 1
        r = pay.owner_note(order, "refund_reminder", f"SnapEyes: reminder, refund order {order} ({amount}) by {due[:10]}",
                           f"Order {order} was withdrawn on {pay.iso(t)} (UTC). Its refund of {amount} is due by {due} "
                           f"at the latest (14 days after the withdrawal; the customer's receipt names that date).\n"
                           f"Refund it in the Stripe Dashboard: Payments, search "
                           f"{paid.get('payment_intent') or paid.get('session_id')}, Refund.\n"
                           f"Then mark it, so no reminder comes again: python scripts/order_admin.py refunded {order}\n"
                           f"If you refunded it already, just mark it.\n")
        say(f"refund reminder for {order}: {r}")
        return 1 if r == "sent" else 0
    except Exception as e:  # noqa: a reminder must never stop the clean-up
        pay.log(f"clean-up: refund reminder for {order} failed: {type(e).__name__}")
        return 0


def _expire(yes, stop_left, say):
    """Step 4: the files of paid orders paid more than 12 months ago (pay.PAID_KEEP_DAYS)."""
    cutoff = time.time() - pay.PAID_KEEP_DAYS * 86400
    done = _done("expired")
    days = [d for d in _days(cutoff - EXPIRE_WINDOW * 86400, cutoff) if d not in done]
    if not days:
        return {"expired": 0, "files": 0, "days": 0, "days_finished": 0, "more": False}
    by_day = pay.day_folders(days)
    names = sorted({o for rows in by_day.values() for o in rows})
    r = pay.expire_paid(pay.PAID_KEEP_DAYS, yes=yes, out=say, names=names, stop_left=stop_left)
    left = set(r.pop("left"))
    finished = 0
    for d in days:
        # an order is paid within 24 h of being made, so a day whose last possible payment is before the cut-off
        # and that has no paid order left is finished
        if yes and not r["more"] and _day_ts(d) + 2 * 86400 <= cutoff and not any(o in left for o in by_day[d]):
            _mark_done("expired", d)
            finished += 1
    r["days"], r["days_finished"] = len(days), finished
    return r


def _old_unmatched(yes, say):
    """Withdrawal statements that matched no order (withdrawals/<yymm>/: the owner handled them by hand) are kept
    UNMATCHED_KEEP_DAYS, then deleted with their month. Statements of real orders stay with the order record."""
    oldest = time.strftime("%y%m", time.gmtime(time.time() - UNMATCHED_KEEP_DAYS * 86400))
    n = 0
    for row in store.list_all("withdrawals"):
        if row["folder"] and len(row["name"]) == 4 and row["name"].isdigit() and row["name"] < oldest:
            files = pay.folder_files(f"withdrawals/{row['name']}")
            say(f"{'DELETE' if yes else 'would delete'} {len(files)} unmatched withdrawal statement files of "
                f"20{row['name'][:2]}-{row['name'][2:]}")
            if yes:
                store.delete_many(files)
            n += len(files)
    return n


def _old_day_marks(yes):
    """The clean-up's own day marks that fell out of their window."""
    now = time.time()
    n = 0
    for kind, oldest in (("unpaid", pay.day(now - (UNPAID_WINDOW + 5) * 86400)),
                         ("expired", pay.day(now - pay.PAID_KEEP_DAYS * 86400 - (EXPIRE_WINDOW + 5) * 86400))):
        old = [f"cleanup/done_{kind}/{d}.json" for d in _done(kind) if d < oldest]
        if yes and old:
            store.delete_many(old)
        n += len(old)
    return n


# ----------------------------------------------------------------------------- step 6: the site's other logs
def _json_safe(v):
    """What a module returned, as the run's reply may carry it."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v if not isinstance(v, str) else v[:200]
    try:
        import json
        json.dumps(v)
        return v
    except (TypeError, ValueError):
        return str(v)[:200]


def _events(yes, stop_left, say):
    """Step 6a: events.purge_old() when api/_lib/events.py exists (the owner's admin tools keep their events there
    and decide their own retention). Only the arguments its signature names are passed (yes, stop_left, out; never
    through **kwargs); a dry run (yes=False) calls it only when it takes yes. Never raises: a failure there is
    logged and costs the run nothing. Returns what it returned (JSON-safe), or None when there is no such module."""
    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.py")):
        return None
    try:
        mod = _import(f"{__package__}.events" if __package__ else "events")
        fn = getattr(mod, "purge_old", None)
        if not callable(fn):
            say("clean-up: api/_lib/events.py has no purge_old(), skipped")
            return {"skipped": "no_purge_old"}
        try:
            params = {k for k, p in inspect.signature(fn).parameters.items()
                      if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)}
        except (TypeError, ValueError):
            params = set()
        if not yes and "yes" not in params:
            say("clean-up: would run events.purge_old() (it has no dry run, so it is not called now)")
            return {"skipped": "dry_run"}
        offer = {"yes": yes, "stop_left": stop_left, "out": say}
        got = fn(**{k: v for k, v in offer.items() if k in params})
        say(f"clean-up: events.purge_old(): {_json_safe(got)}")
        return _json_safe(got)
    except Exception as e:  # noqa: another module's failure must not stop the deletions this run promises
        pay.log(f"clean-up: events.purge_old() failed: {type(e).__name__}: {e}")
        return {"error": type(e).__name__}


_import = importlib.import_module     # tests replace it


def _valid(y, m, d=1):
    return 2000 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= calendar.monthrange(y, m)[1]


def _period(name):
    """(start, end) in unix seconds of the time an audit log name stands for, read from the date it BEGINS with,
    or None when it begins with none. Understood: 2026-09-29..., 2026-09..., 20260929..., the site's own yymmdd
    (260929..., as pay.day()) and yymm (2609..., as withdrawals/<yymm>), yyyymm, yyyy, and unix seconds or
    milliseconds (10 or 13 digits)."""
    s = name
    day = lambda y, m, d: (calendar.timegm((y, m, d, 0, 0, 0)), calendar.timegm((y, m, d, 0, 0, 0)) + 86400)
    month = lambda y, m: (calendar.timegm((y, m, 1, 0, 0, 0)),
                          calendar.timegm((y + (m == 12), m % 12 + 1, 1, 0, 0, 0)))
    g = re.match(r"^(\d{4})-(\d{2})-(\d{2})(?!\d)", s)
    if g:
        y, m, d = map(int, g.groups())
        return day(y, m, d) if _valid(y, m, d) else None
    g = re.match(r"^(\d{4})-(\d{2})(?!\d)", s)
    if g:
        y, m = map(int, g.groups())
        return month(y, m) if _valid(y, m) else None
    g = re.match(r"^(\d+)", s)
    if not g:
        return None
    digits = g.group(1)
    if len(digits) in (10, 13):
        t = int(digits) / (1000 if len(digits) == 13 else 1)
        return (t, t + 1) if 946684800 <= t <= 4102444800 else None
    if len(digits) == 8:
        y, m, d = int(digits[:4]), int(digits[4:6]), int(digits[6:])
        return day(y, m, d) if _valid(y, m, d) else None
    if len(digits) == 6:
        y, m, d = 2000 + int(digits[:2]), int(digits[2:4]), int(digits[4:])
        if _valid(y, m, d):
            return day(y, m, d)
        y, m = int(digits[:4]), int(digits[4:])
        return month(y, m) if _valid(y, m) else None
    if len(digits) == 4:
        y, m = 2000 + int(digits[:2]), int(digits[2:])
        if _valid(y, m):
            return month(y, m)
        y = int(digits)
        return (calendar.timegm((y, 1, 1, 0, 0, 0)), calendar.timegm((y + 1, 1, 1, 0, 0, 0))) if 2000 <= y <= 2100 else None
    return None


def _audit_cutoff(now=None):
    """The moment AUDIT_KEEP_MONTHS calendar months ago: an audit entry whose time ended before it goes."""
    g = time.gmtime(time.time() if now is None else now)
    months = g.tm_year * 12 + (g.tm_mon - 1) - AUDIT_KEEP_MONTHS
    y, m = divmod(months, 12)
    return calendar.timegm((y, m + 1, min(g.tm_mday, calendar.monthrange(y, m + 1)[1]), g.tm_hour, g.tm_min, g.tm_sec))


def _audit(yes, stop_left, say, top=AUDIT_TOP, depth=3):
    """Step 6b: the admin tools' audit log (ops/audit/) is kept AUDIT_KEEP_MONTHS (24 months): every file or folder
    in it whose name begins with a date (_period) that ended before the cut-off goes, a folder with all it holds. A
    folder without a date in its name is looked into (depth levels); a file without one is kept (its age is not
    known). Returns {files, more}."""
    res = {"files": 0, "more": False}
    cut = _audit_cutoff()

    def walk(folder, level):
        for row in store.list_all(folder):
            if L.time_left() < stop_left:
                res["more"] = True
                return
            path = f"{folder}/{row['name']}"
            span = _period(row["name"])
            if span is None:
                if row["folder"] and level < depth:
                    walk(path, level + 1)
                continue
            if span[1] > cut:
                continue
            files = pay.folder_files(path) if row["folder"] else [path]
            if files:
                say(f"{'DELETE' if yes else 'would delete'} {len(files)} audit log file(s) of {path} (older than "
                    f"{AUDIT_KEEP_MONTHS} months)")
                if yes:
                    store.delete_many(files)
            res["files"] += len(files)
            if res["more"]:
                return

    try:
        walk(top, 1)
    except store.StorageError as e:
        pay.log(f"clean-up: audit log not purged: {e}")
    return res
