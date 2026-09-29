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
     still open or settling is kept, and nothing is deleted when Stripe cannot be asked (pay.stripe_verdict)
  3. the images of WITHDRAWN orders go 14 days after the withdrawal (cleanup/withdrawn/); the record stays. An
     order withdrawn while its payment was still settling is asked of Stripe first, like step 2
  4. the files of PAID orders go 12 months after payment (pay.expire_paid); the records stay (order number, date,
     price, payment, email, the artwork's details, consent, withdrawal statements: the policy's "Order records")
  5. the upload and statement markers older than a few days, the clean-up's own day marks, and withdrawal
     statements that matched no order (withdrawals/<yymm>/) 12 months after their month
Order folders are named by the day they were made (yymmdd-...), so a run lists only the days it needs: the last
UNPAID_WINDOW days for step 2, the EXPIRE_WINDOW days before the 12-month cut-off for step 4, minus the days a run
already finished (cleanup/done_unpaid/<day>, cleanup/done_expired/<day>). The run stops with more: true when less
than stop_left seconds of the 60 s function are left; the next run goes on. Logged line by line ("snapeyes pay: ")."""
import time, calendar
from . import iris as L
from . import store
from . import pay
from . import withdraw as W

UNPAID_WINDOW = 35           # days of orders step 2 looks at (the policy promises deletion within 30 days)
EXPIRE_WINDOW = 60           # days before the 12-month cut-off step 4 looks at (a longer gap: order_admin expire-paid)
WITHDRAWN_FILES_DAYS = 14    # the images of a withdrawn order are kept this long after the withdrawal (the refund)
FIRST_DAY = "260901"         # no order folder is older than this code
UNMATCHED_KEEP_DAYS = 396    # statements that matched no order: kept 12 months after their month ended, then deleted
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
            res["markers"] = pay.purge_markers(yes, stop_left, m) + _old_day_marks(yes)
            res["more"] = m["more"]
        if not res["more"]:
            res["unmatched"] = _old_unmatched(yes, say)
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
    finished = 0
    for d in days:
        # finished: every order made that day is older than the cut-off, and none of them is still unpaid here
        if yes and not r["more"] and _day_ts(d) + 86400 <= cutoff and not any(o in left for o in by_day[d]):
            _mark_done("unpaid", d)
            finished += 1
    r["days"], r["days_finished"] = len(days), finished
    return r


def _withdrawn(yes, stop_left, say):
    """Step 3: the images of orders withdrawn more than WITHDRAWN_FILES_DAYS ago."""
    res = {"orders": 0, "files": 0, "kept": 0, "more": False}
    cutoff = time.time() - WITHDRAWN_FILES_DAYS * 86400
    for row in store.list_all("cleanup/withdrawn"):
        if L.time_left() < stop_left:
            res["more"] = True
            break
        name = row["name"]
        if row["folder"] or not name.endswith(".json") or not store.ORDER_RE.fullmatch(name[:-5]):
            continue
        order, mark = name[:-5], f"cleanup/withdrawn/{name}"
        m = store.get_json(mark, timeout=8.0) or {}
        if not isinstance(m.get("t"), (int, float)) or m["t"] > cutoff:
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
