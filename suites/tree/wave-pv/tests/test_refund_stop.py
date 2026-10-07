# -*- coding: utf-8 -*-
"""The refund stop and the unmarked-confirmation rule of api/_lib/maker.py (added after the review round): reuses the
setup of test_advance.py (its part before section A: harness, local store, stubbed renderers with the real eye claim),
in its own store folder.
    python test_refund_stop.py        PASS/FAIL per check, exit 1 on any failure"""
import os, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
__file__ = os.path.join(HERE, "test_advance.py")          # the head computes its paths from this
src = open(os.path.join(HERE, "test_advance.py"), encoding="utf-8").read()
head = src.split("# ======================================================================================= A.")[0]
head = head.replace('"store_adv"', '"store_refund"')
exec(compile(head, "test_advance_head", "exec"))

import shutil  # noqa: after the head (it set STORE)

def refund_record(o, pi):
    path = f"{M.REFUNDS_TOP}/{o}/{hashlib.sha256(pi.encode()).hexdigest()[:16]}.json"
    os.makedirs(os.path.dirname(local(path)), exist_ok=True)
    wj(path, {"refund": "re_test", "status": "succeeded", "payment_intent": pi, "by": "admin"})
    return path

# R1: refunded in the Stripe Dashboard (refunded.json) before the page made eye 1: the page's own make is refused 'refunded' (409) at once, like the server's
# steps (release review, regression m1: a refund used to stop only the server's chain, the page could still make and show the eyes): no eye, no artwork, no email
gate(False)
n0 = len(H.Fake.emails)
o1, k1, _ = new_order(2, "en", "rita@example.com")
wj(f"orders/{o1}/refunded.json", {"by": "admin", "note": "test"})
c, j = post("/api/order", {"action": "make", "order": o1, "k": k1, "eye": 1})
# (the order stays in the index of paid orders nobody finished until the daily run drops it: maker._verdict says "drop" for a refunded order, so the marker is no part of this check)
check("R1 refunded.json: the page's make is refused 'refunded' (409) before any eye is made: no eye, no artwork, no 'ready' email",
      c == 409 and j.get("reason") == "refunded" and j.get("retry") is False and renders(o1) == [] and COMPOSES.count(o1) == 0
      and not mails("rita@example.com", READY_EN, n0), (c, j, renders(o1)))

# R2: the admin panel's own refund of the order's payment (ops/refunds/<order>/<sha(pi)>.json)
n0 = len(H.Fake.emails)
o2, k2, _ = new_order(2, "en", "sven@example.com")
pi = (pay.get_paid(o2) or {}).get("payment_intent")
refund_record(o2, pi or "pi_missing")
c, j = post("/api/order", {"action": "make", "order": o2, "k": k2, "eye": 1})
check("R2 the panel's refund of the order's payment: the page's make is refused 'refunded' (409), no eye, no 'ready' email", bool(pi) and c == 409
      and j.get("reason") == "refunded" and renders(o2) == [] and not mails("sven@example.com", READY_EN, n0), (pi, c, j))

# R3: a refund of another (duplicate) payment is not a refund of the order: it is finished as usual
n0 = len(H.Fake.emails)
o3, k3, _ = new_order(2, "en", "tina@example.com")
refund_record(o3, "pi_duplicate_second_payment")
c, j = post("/api/order", {"action": "make", "order": o3, "k": k3, "eye": 1})
done = wait_for(lambda: stopped(o3, "ready"), 30)
check("R3 a refund of a second payment does not stop the order: ready, one 'ready' email", bool(done)
      and renders(o3) == [1, 2] and COMPOSES.count(o3) == 1 and len(mails("tina@example.com", READY_EN, n0)) == 1,
      (done, renders(o3)))

# R4: the daily run drops a refunded order and sends it no 'late' reminder
now = time.time()
f = M._catch_facts(o1)
check("R4 daily run: a refunded order's verdict is 'drop' and it gets no late reminder", f.get("refunded") is True
      and M._verdict(f, now + 86400) == "drop" and M._late(f, now + 86400) is None, {k: f.get(k) for k in ("refunded",)})
f3 = M._catch_facts(o3)
check("R4b ... and an order with only a second payment refunded is not seen as refunded", f3.get("refunded") is False, f3.get("refunded"))

# R5: may_start: a confirmation sent without the 'making' mark (by hand, or before the mark) means the page starts it
gate(True)
check("R5 may_start: unmarked sent confirmation -> page, even where the texts say the server starts",
      M.may_start({"state": "sent"}) is False and M.may_start({"state": "sent", "making": "server"}) is True
      and M.may_start({"state": "sent", "making": "page"}) is False and M.may_start(None) is True
      and M.may_start({"state": "failed"}) is True)
gate(False)
check("R5b ... and with today's texts nothing unmarked starts on the server", M.may_start(None) is False
      and M.may_start({"state": "sent"}) is False)

fails = [n for n, ok in RESULTS if not ok]
print(f"\n{len(RESULTS) - len(fails)} of {len(RESULTS)} passed" + (f"; FAILED: {fails}" if fails else ""))
time.sleep(1.0)
api.shutdown()
stub.shutdown()
sys.exit(1 if fails else 0)
