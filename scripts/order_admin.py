# -*- coding: utf-8 -*-
"""order_admin.py - the owner's tool for paid orders and old drafts. Runs on the owner's machine, never deployed
(vercel.json excludeFiles "scripts/**").

    python scripts/order_admin.py status ORDER          what is stored, paid, made, held; the order page link
    python scripts/order_admin.py link ORDER            only the order page link (to send to a customer)
    python scripts/order_admin.py release ORDER [--no-mail]   hand out a delivery that waited for review (state
                                                        "review" after compose) and email the customer that it is
                                                        ready (the terms promise it; --no-mail skips the email)
    python scripts/order_admin.py clear-review ORDER    let /api/order make an eye again after a refused render
                                                        (the next attempt costs one more 4K render)
    python scripts/order_admin.py resend-mail ORDER     send the order confirmation email again after it failed
                                                        (Resend fixed); once sent, the order page goes on
    python scripts/order_admin.py mailed-by-hand ORDER  you sent the confirmation yourself (for example to a
                                                        corrected address): mark it sent, the order page goes on
    python scripts/order_admin.py purge [--hours 48] [--yes]   delete UNPAID orders older than --hours (their eye
                                                        photos); without --yes it only lists them. An order that
                                                        had a checkout is asked of Stripe first: a paid one is
                                                        recorded as paid instead, an open one kept (this needs
                                                        STRIPE_SECRET_KEY here; without it such orders are kept).
                                                        The site runs the same clean-up daily (GET
                                                        /api/order?cron=purge, vercel.json crons + CRON_SECRET).
    python scripts/order_admin.py expire-paid [--months 12] [--yes]   delete the files of PAID orders paid more than
                                                        --months ago (the privacy policy keeps them 12 months); every
                                                        order, not only the days the daily run looks at
    python scripts/order_admin.py erase ORDER [--yes]   delete one order's files now (a customer's request)
    python scripts/order_admin.py cleanup [--yes]       the site's whole daily clean-up (api/_lib/cleanup.py: receipts
                                                        to send again, the withdrawal digest, unpaid orders, withdrawn
                                                        orders' images, paid orders after 12 months, markers), here and
                                                        without a time limit; without --yes it only lists what it would do
    python scripts/order_admin.py withdrawals [--day YYMMDD] [--months 2]   the online withdrawal statements that
                                                        matched NO order (withdrawals/<yymm>/: you check them by hand),
                                                        newest first, and the days whose digest email is still due

What stays of an erased PAID order: its records (pay.kept_record: order.json and paid.json with date, price, payment,
email, the artwork's details and consent; the mail and note marks; withdrawal statements), plus deleted.json, so its
order page answers "deleted" (410) instead of failing. An erased UNPAID order is removed completely.

Environment: the same as the site. SNAPEYES_SUPABASE_URL + SNAPEYES_SUPABASE_SERVICE_KEY (or STORE_LOCAL_DIR for a
local test folder); the link needs the ticket secret the order was made with (SNAPEYES_TICKET_SECRET, or the
Gemini key when that is unset); --mail and resend-mail need RESEND_API_KEY; purge asks Stripe with
STRIPE_SECRET_KEY. Nothing secret is printed; the order link itself is a credential for that one order: send it
only to its customer."""
import os, sys, time, json, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))
from _lib import store  # noqa: E402
from _lib import pay  # noqa: E402
from _lib import cleanup  # noqa: E402


def _order(v):
    try:
        return store.check_order(v)
    except Exception:
        raise SystemExit("ORDER must be an order id: lower-case letters, digits and '-', 4-64 characters")


def _rec(order):
    rec = store.get_json(f"orders/{order}/order.json")
    if not isinstance(rec, dict):
        raise SystemExit(f"no order {order}")
    return rec


def _files(folder):
    return pay.folder_files(folder)


def cmd_status(order):
    rec = _rec(order)
    paid = pay.get_paid(order)
    print(f"order     {order}  made {rec.get('created')}  lang {rec.get('lang')}")
    co = rec.get("checkout") or {}
    if co:
        print(f"checkout  {co.get('session_id')}  {co.get('amount')} cents  spec {json.dumps(co.get('spec'), ensure_ascii=False)}")
    if paid:
        print(f"PAID      {paid.get('paid_iso')} via {paid.get('source')}  {paid.get('amount_total')} {paid.get('currency')}"
              f"  live={paid.get('livemode')}  email {paid.get('email')}")
        print(f"spec      {json.dumps(paid.get('spec'), ensure_ascii=False)}")
        if paid.get("amount_mismatch"):
            print(f"WARNING   amount differs from the price: {paid['amount_mismatch']}")
    else:
        left = pay.expires_at(rec) - time.time()
        print(f"unpaid    {'EXPIRED' if left <= 0 else f'{left / 3600:.1f} h left to pay'}")
    for name in ("review.json", "delivery.json", "release.json", "mail_delivery.json", "making.json", "withdrawn.json",
                 "withdrawal.json", "deleted.json", "expired.json"):
        j = store.get_json(f"orders/{order}/{name}")
        if j is not None:
            print(f"{name:<18}{json.dumps(j, ensure_ascii=False)}")
    if paid and pay.confirmation_needed(paid):
        m = store.get_json(f"orders/{order}/mail_delivery.json")
        if not (isinstance(m, dict) and m.get("state") == "sent"):
            print("WARNING   the order confirmation email has NOT gone out: nothing is made until it has "
                  "(resend-mail or mailed-by-hand)")
    if paid and not pay.paid_counts(paid):
        print("WARNING   a Stripe TEST payment: this machine's settings make nothing for it")
    for p in _files(f"orders/{order}"):
        base = p.rsplit("/", 1)[-1]
        if base.startswith("withdrawal_") and not base.endswith(("_ack.json", "_note.json")):
            w = store.get_json(p) or {}
            print(f"WITHDRAWAL {w.get('received')}  {w.get('outcome')} ({w.get('reason')})  by {w.get('name')} "
                  f"<{w.get('email')}>  matched by {w.get('verified')}"
                  + (f"  REFUND due by {pay.iso(w['refund_by'])}" if w.get("refund") == "due" and w.get("refund_by") else ""))
        if p.rsplit("/", 1)[-1].startswith("extra_payment_"):
            x = store.get_json(p) or {}
            print(f"EXTRA PAYMENT (refund it) {x.get('amount_total')} {x.get('currency')}  session {x.get('session_id')}"
                  f"  payment {x.get('payment_intent')}  paid {x.get('paid_iso')}")
    for n in range(1, 9):
        j = store.get_json(f"orders/{order}/eye_{n}.json")
        if j:
            print(f"eye {n}     needs_review={store.needs_review(j)}  qa.ok={(j.get('qa') or {}).get('ok')}  "
                  f"preview.ok={(j.get('preview') or {}).get('ok')}  render {j.get('render_seconds')} s")
    print("files:")
    for p in _files(f"orders/{order}"):
        print("   ", p)
    k = pay.link_key(order, rec)
    print("link     ", pay.order_url(order, k, rec.get("lang")) if k else "cannot be rebuilt: the ticket secret changed")
    if k:
        print("withdraw ", pay.withdraw_url(order, k, rec.get("lang")), " (the withdrawal form: opening it starts nothing)")


def cmd_link(order):
    rec = _rec(order)
    k = pay.link_key(order, rec)
    if not k:
        raise SystemExit("the link cannot be rebuilt here: this machine's ticket secret is not the one the order was made with")
    print(pay.order_url(order, k, rec.get("lang")))


def cmd_release(order, mail=True):
    rec = _rec(order)
    paid = pay.get_paid(order)
    if not paid:
        raise SystemExit("not paid: nothing to release")
    dl = store.get_json(f"orders/{order}/delivery.json")
    if not isinstance(dl, dict):
        raise SystemExit("no artwork yet: the order page composes it once every eye is made")
    store.put(f"orders/{order}/release.json", store.json_bytes({"t": int(time.time()), "iso": pay.iso(), "by": "owner"}),
              "application/json", upsert=True)
    store.delete(f"orders/{order}/review.json")
    print(f"released {dl.get('key')} ({'it was held for review' if dl.get('needs_review') else 'it was not held'})")
    if mail:
        k = pay.link_key(order, rec)
        if not k:
            raise SystemExit("released, but no email: the link cannot be rebuilt with this machine's ticket secret")
        subject, text, html_body = pay.ready_mail(order, paid, k)
        print("ready email:", pay.send_mail(paid.get("email"), subject, text, f"snapeyes-ready-{order}", html_body))


def cmd_clear_review(order):
    _rec(order)
    print("review.json removed" if store.delete(f"orders/{order}/review.json") else "there was no review.json")


def cmd_purge(hours, yes):
    res = pay.purge_unpaid(hours, yes=yes, out=print, stop_left=-1e9)
    if yes:
        print(f"{res['deleted']} unpaid orders deleted, {res['recorded']} found PAID at Stripe and recorded, "
              f"{res['kept']} kept (Stripe session open, settling or unknown), {res['markers']} old markers removed")
    else:
        print(f"dry run: {res['deleted']} would be deleted, {res['recorded']} are PAID at Stripe and would be recorded, "
              f"{res['kept']} kept; add --yes")


def _mail_hold_cleared(order):
    rv = store.get_json(f"orders/{order}/review.json")
    if isinstance(rv, dict) and str(rv.get("reason") or "").startswith(pay.MAIL_REVIEW):
        store.delete(f"orders/{order}/review.json")
        print("the review hold for the confirmation email is lifted: the order page goes on")
    elif isinstance(rv, dict):
        print(f"review.json stays (reason {rv.get('reason')}): look at it, then clear-review")


def cmd_resend_mail(order):
    rec = _rec(order)
    paid = pay.get_paid(order)
    if not paid:
        raise SystemExit("not paid: there is no confirmation to send")
    if not pay.email_configured():
        raise SystemExit("RESEND_API_KEY is not set here")
    m = store.get_json(f"orders/{order}/mail_delivery.json")
    if isinstance(m, dict) and m.get("state") == "sent":
        print("the confirmation was sent before")
        _mail_hold_cleared(order)
        return
    store.delete(f"orders/{order}/mail_delivery.json")          # the failed mark: try again
    res = pay.deliver_mail(order, rec, paid, idem_suffix=f"-r{int(time.time())}")
    print("confirmation email:", res)
    if res == "sent":
        _mail_hold_cleared(order)
    else:
        raise SystemExit("not sent: fix the cause and run this again, or send it yourself and run mailed-by-hand")


def cmd_mailed_by_hand(order):
    _rec(order)
    if not pay.get_paid(order):
        raise SystemExit("not paid: there is no confirmation to mark")
    store.put(f"orders/{order}/mail_delivery.json", store.json_bytes({"state": "sent", "by": "owner", "result": "by_hand",
                                                                      "t": round(time.time(), 3), "iso": pay.iso()}),
              "application/json", upsert=True)
    print("the confirmation is marked sent (by you)")
    _mail_hold_cleared(order)


def cmd_erase(order, yes):
    _rec(order)
    pay.erase_files(order, "request", yes, print)
    if not yes:
        print("dry run: add --yes to delete")


def cmd_expire_paid(months, yes):
    res = pay.expire_paid(round(months * 30.44), yes=yes, out=print, stop_left=-1e9)
    print(f"{res['expired']} paid orders' files deleted ({res['files']} files)" if yes else
          f"dry run: {res['expired']} paid orders would lose their files; add --yes")


def cmd_cleanup(yes):
    res = cleanup.run(yes=yes, stop_left=-1e9, out=print, lock=yes)
    if not yes:
        print("dry run: nothing was changed; add --yes")
    return res


def cmd_withdrawals(day=None, months=2):
    """The statements that matched no order, newest first: when, the order text and email given, the name, what the
    receipt did, and where it is kept. Plus the days whose digest email the daily clean-up still has to send."""
    now = time.time()
    months_list = []
    for i in range(max(1, int(months))):
        yymm = time.strftime("%y%m", time.gmtime(now - i * 30.44 * 86400))
        if yymm not in months_list:
            months_list.append(yymm)
    if day:
        months_list = [day[:4]]
    rows = []
    for yymm in months_list:
        for p in _files(f"withdrawals/{yymm}"):
            if p.endswith(("_ack.json", "_note.json")):
                continue
            w = store.get_json(p) or {}
            if day and pay.day(w.get("received_at") or 0) != day:
                continue
            ack = store.get_json(p[:-5] + "_ack.json") or {}
            rows.append((w.get("received_at") or 0, w, p, ack))
    for _, w, p, ack in sorted(rows, key=lambda r: r[0], reverse=True):
        print(f"{w.get('received')}  order given {w.get('order_given')!r}  email {w.get('email')}  name {w.get('name')!r}  "
              f"receipt {ack.get('result') or ack.get('state') or 'none'}  lang {w.get('lang')}\n    {p}")
    print(f"{len(rows)} statement(s) that matched no order" + (f" on {day}" if day else f" in {', '.join(months_list)}"))
    due = [r["name"] for r in store.list_all("cleanup/digest") if r["folder"]]
    if due:
        print("digest email still to come for:", ", ".join(sorted(due)))


def main(argv=None):
    ap = argparse.ArgumentParser(description="SnapEyes orders: status, link, release, clear-review, resend-mail, "
                                             "mailed-by-hand, purge, expire-paid, erase, cleanup, withdrawals.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("status", "link", "clear-review", "resend-mail", "mailed-by-hand"):
        sub.add_parser(name).add_argument("order")
    r = sub.add_parser("release")
    r.add_argument("order")
    r.add_argument("--no-mail", action="store_true", help="do not send the customer the 'ready' email")
    r.add_argument("--mail", action="store_true", help=argparse.SUPPRESS)   # the default now; kept for old notes
    p = sub.add_parser("purge")
    p.add_argument("--hours", type=float, default=48.0, help="age of unpaid orders to delete (at least 25)")
    p.add_argument("--yes", action="store_true", help="really delete (default: list only)")
    e = sub.add_parser("expire-paid")
    e.add_argument("--months", type=float, default=12.0, help="how long paid orders' files are kept (at least 1)")
    e.add_argument("--yes", action="store_true", help="really delete (default: list only)")
    x = sub.add_parser("erase")
    x.add_argument("order")
    x.add_argument("--yes", action="store_true", help="really delete (default: list only)")
    c = sub.add_parser("cleanup")
    c.add_argument("--yes", action="store_true", help="really do it (default: list only)")
    w = sub.add_parser("withdrawals")
    w.add_argument("--day", help="only this UTC day, YYMMDD")
    w.add_argument("--months", type=int, default=2, help="how many months back to list (default 2)")
    a = ap.parse_args(argv)
    if not store.configured():
        raise SystemExit("storage is not configured here: " + store.problem())
    if a.cmd == "status":
        cmd_status(_order(a.order))
    elif a.cmd == "link":
        cmd_link(_order(a.order))
    elif a.cmd == "release":
        cmd_release(_order(a.order), not a.no_mail)
    elif a.cmd == "clear-review":
        cmd_clear_review(_order(a.order))
    elif a.cmd == "resend-mail":
        cmd_resend_mail(_order(a.order))
    elif a.cmd == "mailed-by-hand":
        cmd_mailed_by_hand(_order(a.order))
    elif a.cmd == "purge":
        if a.hours < 25:
            raise SystemExit("--hours must be at least 25: a younger unpaid order can still be paid")
        cmd_purge(a.hours, a.yes)
    elif a.cmd == "expire-paid":
        if a.months < 1:
            raise SystemExit("--months must be at least 1")
        cmd_expire_paid(a.months, a.yes)
    elif a.cmd == "erase":
        cmd_erase(_order(a.order), a.yes)
    elif a.cmd == "cleanup":
        cmd_cleanup(a.yes)
    elif a.cmd == "withdrawals":
        if a.day is not None and not (len(a.day) == 6 and a.day.isdigit()):
            raise SystemExit("--day must be YYMMDD, for example 260929")
        cmd_withdrawals(a.day, a.months)
    return 0


if __name__ == "__main__":
    sys.exit(main())
