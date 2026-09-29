# -*- coding: utf-8 -*-
"""POST /api/stripe_webhook: Stripe's events for this site (endpoint https://snapeyes.com/api/stripe_webhook).

The Stripe-Signature header is verified over the RAW body before anything parses it (t= and v1= HMAC-SHA256 of
"<t>.<body>" with STRIPE_WEBHOOK_SECRET, 5 minutes tolerance, constant-time compare). A bad or missing signature is
a 400 and nothing else happens.

Handled: checkout.session.completed and checkout.session.async_payment_succeeded with payment_status "paid" and
metadata naming an order of ours (with the fingerprint of its access key): the order is marked paid (paid.json,
created once: a replayed or retried event changes nothing), the customer's email is kept with it, the delivery email
(the order confirmation) goes out once when email is configured (EN or DE by the order's language), and the owner
gets a short note. When that email cannot go out (Resend refused it, no or bad address, email off for a live
payment), the order is held for review and the owner told: nothing is made before the confirmation went out.
A second paid session of an order that is already paid is recorded apart and the owner told to refund it.
A test-mode session where test orders are not allowed (production), every other event, and a session that is not
paid yet are answered 200 at once and ignored.

Replies: 200 {ok, ...}; 400 bad signature or body; 413 body too large; 503 when payments or storage are not
configured, storage did not answer, or the email failed in a way a retry can fix (Stripe retries a non-2xx for up to
three days, and every step above is idempotent); 500 for anything unexpected (logged)."""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L
from _lib import store
from _lib import pay

MAX_BODY = 512 << 10         # a Checkout Session event is a few kB
HANDLED = ("checkout.session.completed", "checkout.session.async_payment_succeeded")


def on_event(event):
    """(status, reply) for one verified event."""
    typ = event.get("type") if isinstance(event, dict) else None
    if typ not in HANDLED:
        return 200, {"ok": True, "ignored": str(typ)[:80]}
    obj = ((event.get("data") or {}).get("object")) if isinstance(event.get("data"), dict) else None
    if not isinstance(obj, dict) or obj.get("object") != "checkout.session":
        return 200, {"ok": True, "ignored": "not a checkout session"}
    meta = obj.get("metadata") if isinstance(obj.get("metadata"), dict) else {}
    order = meta.get("order")
    if not isinstance(order, str) or not store.ORDER_RE.fullmatch(order):
        pay.log(f"webhook {event.get('id')}: {typ} for a session without an order of ours, ignored")
        return 200, {"ok": True, "ignored": "no order"}
    if not pay.session_paid(obj):
        pay.log(f"webhook {event.get('id')}: order {order} {typ} payment_status {obj.get('payment_status')}, waiting")
        return 200, {"ok": True, "order": order, "state": "awaiting_payment"}
    rec = store.get_json(f"orders/{order}/order.json", timeout=8.0)
    if not isinstance(rec, dict):
        pay.log(f"webhook {event.get('id')}: order {order} is PAID at Stripe but has no order record here")
        return 200, {"ok": True, "ignored": "unknown order"}
    if not pay.session_matches(obj, order, rec):
        pay.log(f"webhook {event.get('id')}: order {order}: the session does not match the order record, ignored")
        return 200, {"ok": True, "ignored": "session does not match"}
    if not pay.session_counts(obj):
        pay.log(f"webhook {event.get('id')}: order {order}: a TEST-mode payment, and this deployment takes no test "
                f"orders: ignored")
        return 200, {"ok": True, "ignored": "test mode"}
    paid, new = pay.record_paid(order, rec, obj, "webhook", event.get("id"))
    if paid.get("session_id") != obj.get("id"):
        # a second paid session of an order that was already paid: record_paid stored it and told the owner to
        # refund it; the order and its confirmation stay as the first payment made them
        return 200, {"ok": True, "order": order, "new": False, "extra_payment": True}
    mail = pay.deliver_mail(order, rec, paid)      # once per order (claimed), also when the order page came first
    pay.note_paid(order, paid)
    if mail == "transient":
        return 503, {"ok": False, "order": order, "reason": "mail_retry"}
    if mail in ("failed", "bad_address", "no_address") or (mail == "off" and pay.confirmation_needed(paid)):
        # the confirmation cannot go out: nothing is made for the order until the owner sends it
        pay.hold_confirmation(order, paid, mail)
    return 200, {"ok": True, "order": order, "new": new, "mail": mail}


def handle(req):
    t0 = time.time()
    pay.start_clock()
    try:
        n = int(req.headers.get("content-length") or 0)
    except ValueError:
        n = -1
    if n < 0 or n > MAX_BODY:
        store._drain(req)
        return L.send_json(req, 413, {"ok": False, "error": "body too large"})
    payload = req.rfile.read(n) if n else b""
    secrets_list = pay.webhook_secrets()
    if not secrets_list:
        pay.log("webhook refused: STRIPE_WEBHOOK_SECRET is not set or malformed")
        return L.send_json(req, 503, {"ok": False, "reason": "payments_not_configured"})
    if not pay.verify_signature(payload, req.headers.get("stripe-signature"), secrets_list):
        pay.log(f"webhook refused: bad or missing signature ({len(payload)} bytes)")
        return L.send_json(req, 400, {"ok": False, "error": "bad signature"})
    try:
        event = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return L.send_json(req, 400, {"ok": False, "error": "bad body"})
    if not isinstance(event, dict):
        return L.send_json(req, 400, {"ok": False, "error": "bad body"})
    try:
        code, out = on_event(event)
    except store.StorageNotConfigured:
        pay.log("webhook: storage not configured")
        code, out = 503, {"ok": False, "reason": "storage_not_configured"}
    except (store.StorageError, pay.PayBusy) as e:
        pay.log(f"webhook {event.get('id')}: {type(e).__name__} {e}")
        code, out = 503, {"ok": False, "reason": "busy"}
    except Exception as e:  # noqa: logged, Stripe retries
        pay.log(f"webhook {event.get('id')}: error {type(e).__name__} {e}")
        code, out = 500, {"ok": False, "reason": "error"}
    out["ms"] = int((time.time() - t0) * 1000)
    L.send_json(req, code, out)


class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
