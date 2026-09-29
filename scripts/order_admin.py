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
                                                        newest first, and the statements still waiting for a digest
                                                        email (NEED ACTION first: notes over the daily limit)
    python scripts/order_admin.py refunded ORDER [--note TEXT]   you refunded a withdrawn order in Stripe: mark it
                                                        (refunded.json), so the daily clean-up sends no reminder
    python scripts/order_admin.py selfcall-probe [--site URL] [--keep]   the self-call test: can the server call
                                                        itself as many times in a row as an order needs (Vercel's
                                                        loop protection publishes no limit)? About a minute, no order
                                                        touched, nothing paid; PASS or FAIL with the reason. --site:
                                                        default the site (SNAPEYES_SITE, https://snapeyes.com); a
                                                        Preview address needs VERCEL_AUTOMATION_BYPASS_SECRET here

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
        print(f"checkout  {co.get('session_id')}  {pay.amount_text(co.get('amount') or 0, 'en', co.get('currency'))}  "
              f"market {co.get('market') or pay.DEFAULT_MARKET}  spec {json.dumps(co.get('spec'), ensure_ascii=False)}")
    if paid:
        print(f"PAID      {paid.get('paid_iso')} via {paid.get('source')}  {paid.get('amount_total')} {paid.get('currency')}"
              f"  live={paid.get('livemode')}  email {paid.get('email')}")
        print(f"spec      {json.dumps(paid.get('spec'), ensure_ascii=False)}")
        if paid.get("amount_mismatch"):
            print(f"WARNING   amount differs from the price: {paid['amount_mismatch']}")
    else:
        left = pay.expires_at(rec) - time.time()
        print(f"unpaid    {'EXPIRED' if left <= 0 else f'{left / 3600:.1f} h left to pay'}")
    for name in ("review.json", "delivery.json", "release.json", "mail_delivery.json", "making.json", "advance.json",
                 "withdrawn.json", "withdrawal.json", "refunded.json", "deleted.json", "expired.json"):
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
    due = sorted(r["name"] for r in store.list_all("cleanup/digest") if r["folder"])
    if day:
        due = [d for d in due if d == day]
    if due:
        print("digest email still to come for:", ", ".join(due))
    kinds = {"p": "NEED ACTION (note over the daily limit)", "r": "repeat, nothing new to do",
             "n": "order never paid, nothing to do"}
    for d in due:
        names = sorted((r["name"] for r in store.list_all(f"cleanup/digest/{d}") if not r["folder"]),
                       key=lambda n: ("prnu".find(n[:1]) if n[:1] in "prnu" else 9, n))
        for n in names:
            if n[:1] not in kinds:
                continue                 # u-: listed above
            ptr = store.get_json(f"cleanup/digest/{d}/{n}") or {}
            w = store.get_json(ptr["path"]) if isinstance(ptr.get("path"), str) else None
            if not isinstance(w, dict):
                continue
            extra = ""
            if w.get("refund") == "due" and w.get("refund_by") and n.startswith("p-"):
                extra = f"  REFUND {pay.amount_text(w.get('amount') or 0, 'en', w.get('currency'))} due by {pay.iso(w['refund_by'])}"
            print(f"{w.get('received')}  {kinds[n[:1]]}: order {w.get('order')}  {w.get('outcome')} ({w.get('reason')})  "
                  f"email {w.get('email')}{extra}\n    {ptr.get('path')}")


def cmd_refunded(order, note=""):
    """The owner refunded a withdrawn order: refunded.json (kept with the order's records), so the daily clean-up
    sends no refund reminder. The refund itself is made in the Stripe Dashboard."""
    _rec(order)
    paid = pay.get_paid(order)
    if not paid:
        raise SystemExit("not paid: there is nothing to refund")
    if not store.exists(f"orders/{order}/withdrawn.json"):
        print("note: this order is not withdrawn; the mark is stored anyway")
    store.put(f"orders/{order}/refunded.json", store.json_bytes({"t": int(time.time()), "iso": pay.iso(), "by": "owner",
                                                                "amount": paid.get("amount_total"),
                                                                "note": str(note or "")[:200]}),
              "application/json", upsert=True)
    print(f"marked refunded ({pay.amount_text(paid.get('amount_total') or 0, 'en', paid.get('currency'))}); no reminder will come")


def _probe_why(h, rec):
    """Why the self-call test stopped after hop h (its record rec), for the owner."""
    word, code = rec.get("next"), rec.get("code")
    if "done" not in rec:
        return (f"hop {h} started but never finished: its invocation was stopped before it could ask for the next "
                f"one (Vercel may cancel a function whose caller has left; the server's making needs it to run on)")
    if word == "refused":
        extra = {508: "Vercel's loop protection (INFINITE_LOOP_DETECTED) refused the call after "
                      f"{h + 1} nested self-calls: the server cannot finish orders by itself on this deployment",
                 401: "a protected deployment: create Protection Bypass for Automation in Vercel and deploy again",
                 403: "refused: another SNAPEYES_TICKET_SECRET there, or the Vercel Firewall or Bot Protection "
                      "challenged the User-Agent snapeyes-self-call/1 (let it through in Vercel, Firewall)",
                 429: "rate limited by the Vercel Firewall or Bot Protection (let snapeyes-self-call/1 through)"}
        return f"hop {h} asked for hop {h + 1} and was answered HTTP {code}: " + extra.get(
            code, "a redirect: SNAPEYES_SITE must be the canonical address" if isinstance(code, int) and 300 <= code < 400
            else "look at the Vercel log of /api/order")
    if word == "failed":
        return f"hop {h} could not send its call for hop {h + 1} ({code})"
    if word == "off":
        return f"hop {h} found no address to call (SNAPEYES_SITE, VERCEL_URL)"
    if word == "no_time":
        return f"hop {h} had no time left to ask for hop {h + 1}"
    return (f"hop {h} asked for hop {h + 1} ({word}), but hop {h + 1} never ran: a call is lost when its caller "
            f"stops waiting before the called function starts (a cold start); the server's making needs that call")


def cmd_selfcall_probe(site=None, keep=False):
    """The self-call test (api/_lib/maker.py probe): does this deployment let the server call itself as many times in
    a row as an order needs (an 8-eye order: 10 or more)? Vercel's loop protection publishes no limit. Starts
    maker.PROBE_HOPS hops on the site (each works longer than the caller waits, as a render step does), follows them
    in storage (ops/selfcall/<id>/), prints what each did and PASS or FAIL, and deletes the test's files. No order is
    touched and nothing is paid. Needs the site's SNAPEYES_TICKET_SECRET here (the site refuses another), and on a
    protected Preview VERCEL_AUTOMATION_BYPASS_SECRET too."""
    import re, secrets, requests
    from _lib import iris as L
    from _lib import maker as M
    base = (site or pay.site()).strip().rstrip("/")
    if not re.fullmatch(r"https://[a-z0-9][a-z0-9.-]{2,200}|http://127\.0\.0\.1:[0-9]{2,5}", base):
        raise SystemExit("--site must be https://<host> (or http://127.0.0.1:<port> for a local test)")
    pid = secrets.token_hex(6)
    folder = f"{M.PROBE_TOP}/{pid}"
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "snapeyes-self-call/1"}
    bypass = os.environ.get("VERCEL_AUTOMATION_BYPASS_SECRET", "").strip()
    if bypass:
        headers["x-vercel-protection-bypass"] = bypass
    print(f"self-call test {pid} on {base}: {M.PROBE_HOPS} hops of about {M.PROBE_WORK + 0.5:.0f} s each")
    body = {"action": "advance", "probe": pid, "hop": 0, "ticket": L.mint_ticket(M.PROBE_KIND + pid, M.TICKET_TTL)}
    t0 = time.time()
    ok = False
    try:
        try:
            r = requests.post(base + "/api/order", data=json.dumps(body), headers=headers, timeout=(10, 1.5),
                              allow_redirects=False)
            code = r.status_code
            r.close()
            if code != 200:
                why = {403: "the site refused the test's ticket: SNAPEYES_TICKET_SECRET here is not the site's (or the "
                            "Vercel Firewall challenged the call)",
                       401: "the deployment is protected: set VERCEL_AUTOMATION_BYPASS_SECRET here to its bypass secret",
                       400: "the site does not know the self-call test yet: deploy this version first"}.get(code, "")
                raise SystemExit(f"FAIL: the site answered HTTP {code} to the first hop{': ' + why if why else ''}")
        except requests.exceptions.ReadTimeout:
            pass                          # the first hop is working (it answers only after PROBE_WORK)
        except requests.RequestException as e:
            raise SystemExit(f"FAIL: the site could not be reached: {type(e).__name__}")
        deadline = t0 + M.PROBE_HOPS * (M.PROBE_WORK + 6.0) + 30.0
        hops, stall = {}, None
        while time.time() < deadline:
            time.sleep(2.0)
            for row in store.list_all(folder):
                m = re.fullmatch(r"hop_([0-9]{2})\.json", row["name"])
                if m and not row["folder"]:
                    rec = store.get_json(f"{folder}/{row['name']}")
                    if isinstance(rec, dict):
                        hops[int(m.group(1))] = rec
            top = max(hops) if hops else -1
            last = hops.get(top) or {}
            if top == M.PROBE_HOPS - 1 and "done" in last:
                break
            if "done" in last and last.get("next") not in ("sent", "done"):
                break                     # the chain ended here: why below
            if "done" in last:
                stall = stall if stall and stall[0] == top else (top, time.time())
                if time.time() - stall[1] > 25.0:
                    break                 # it asked for the next hop, which never came
        for h in sorted(hops):
            rec = hops[h]
            code = f" HTTP {rec['code']}" if isinstance(rec.get("code"), int) else ""
            print(f"  hop {h:2d}  ran {rec.get('t', t0) - t0:6.1f} s after the start, {rec.get('left')} s of its "
                  f"invocation left; the next: {rec.get('next', 'still working')}{code}")
        n = len(hops)
        top = max(hops) if hops else -1
        if n == M.PROBE_HOPS and hops.get(M.PROBE_HOPS - 1, {}).get("next") == "last":
            ok = True
            print(f"PASS: the server called itself {M.PROBE_HOPS - 1} times in a row, each call answered after its "
                  f"caller had left (an 8-eye order needs about 10). The server's own making works on {base}.")
        elif top < 0:
            print("FAIL: the first hop never ran (look at the Vercel log of /api/order)")
        else:
            print(f"FAIL after {n} of {M.PROBE_HOPS} hops: {_probe_why(top, hops[top])}. Until this is solved, paid "
                  f"orders are finished by the customer's order page while it is open and by the daily run.")
    finally:
        if not keep:
            try:
                store.delete_many(pay.folder_files(folder))
            except Exception as e:  # noqa: a few small files; the next test does not need them gone
                print(f"(the test's files under {folder} were not deleted: {type(e).__name__})")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description="SnapEyes orders: status, link, release, clear-review, resend-mail, "
                                             "mailed-by-hand, purge, expire-paid, erase, cleanup, withdrawals, refunded, "
                                             "selfcall-probe.")
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
    f = sub.add_parser("refunded")
    f.add_argument("order")
    f.add_argument("--note", default="", help="optional: how or when you refunded it")
    sp = sub.add_parser("selfcall-probe")
    sp.add_argument("--site", default=None, help="the address to test (default: the site, SNAPEYES_SITE)")
    sp.add_argument("--keep", action="store_true", help="keep the test's files in storage (ops/selfcall/)")
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
    elif a.cmd == "refunded":
        cmd_refunded(_order(a.order), a.note)
    elif a.cmd == "selfcall-probe":
        return 0 if cmd_selfcall_probe(a.site, a.keep) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
