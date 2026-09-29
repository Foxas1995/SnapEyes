# -*- coding: utf-8 -*-
"""/api/checkout: opens the Stripe payment page for an order whose eyes are uploaded (/api/order action "draft").

GET  /api/checkout
     {ok, open, currency, prices, max_eyes, consent: {version, en, de}}: whether ordering is open on this deployment
     (Stripe and storage configured), the price list the server charges, and the exact withdrawal-waiver text the
     checkbox must show. Nothing secret, nothing per order.
POST /api/checkout {order, k, eyes: 1-8, style, layout, names, title, lang: "en"|"de", consent_digital: true}
     The server computes the price from eyes and style (a price sent by the client is ignored), refuses without the
     withdrawal waiver, records the consent's version, time and text fingerprint, creates a Stripe Checkout Session
     (mode payment, EUR, one line item, the customer's email collected by Stripe, Stripe's own page in de or en,
     payment methods chosen by Stripe, no Stripe Tax) and returns its URL.
     Reply 200: {ok, url, order, amount, currency, eyes, style, expires_at}; redirect the browser to url.
     Errors ({ok: false, reason, error, retry}):
       503 payments_not_configured / storage_not_configured   ordering is not open on this deployment (no Stripe,
                                a live key without the confirmation email, a test key on production:
                                pay.ordering_problem())
       403 bad_link             order and k do not match
       400                      bad eyes, style or layout (L.run's sentence); consent_required without the waiver
       409 already_paid         the order is paid, or an earlier checkout of it was completed and its payment is
                                still settling (settling: true); order_url says where it lives
     Before a new session is made, the order's earlier sessions are expired at Stripe (one payable session per
     order); one that turns out paid is recorded and answered 409 already_paid.
       409 eyes_missing         eyes 1..n are not all uploaded (missing: [n, ...]); upload them and ask again
       410 draft_expired        the order is older than 24 h (less than 32 min left): start a new one
       503 payments_busy        Stripe did not answer; retry
       502 payments_error       Stripe refused the request; not retryable, logged"""
import os, sys, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L
from _lib import store
from _lib import pay


def info(body):
    return {"ok": True, "open": pay.ordering_open() and store.configured(), "currency": "EUR",
            "prices": {"one_eye_studio_black": pay.PRICE_ONE_STUDIO, "one_eye_art": pay.PRICE_ONE_ART,
                       "two_eyes": pay.PRICE_TWO, "each_further_eye": pay.PRICE_EXTRA},
            "max_eyes": pay.MAX_EYES,
            "consent": {"version": pay.CONSENT_VERSION, "en": pay.CONSENT_TEXT["en"], "de": pay.CONSENT_TEXT["de"]}}


def checkout(body):
    why = pay.ordering_problem()
    if why:
        raise pay.PayNotConfigured(why)
    order, k = body.get("order"), body.get("k")
    rec = pay.load_order(order, k)
    spec = pay.spec_from(body)
    if body.get("consent_digital") is not True:
        raise store.Answer(400, "consent_required", "Please tick the box about the digital file and your right of "
                           "withdrawal.", False)
    n, lang = spec["eyes"], spec["lang"]
    folder = f"orders/{order}"
    found = pay.parallel([lambda: store.exists(f"{folder}/paid.json", timeout=8.0)] +
                         [lambda i=i: store.get_json(f"{folder}/draft/eye_{i}.json", timeout=8.0) for i in range(1, n + 1)])
    if found[0]:
        raise store.Answer(409, "already_paid", "This order is already paid.", False, order_url=pay.order_url(order, k, lang))
    now = time.time()
    # the session ends when the draft does (24 h after the order was made), and always under Stripe's 24 h maximum
    expires = min(pay.expires_at(rec), int(now) + 86400 - 120)
    if expires - now < pay.SESSION_MIN:
        raise store.Answer(410, "draft_expired", "This unpaid order is more than 24 hours old. Please start a new one.",
                           False)
    missing = [i for i, d in enumerate(found[1:], 1) if not isinstance(d, dict)]
    if missing:
        raise store.Answer(409, "eyes_missing", "Some eyes of this artwork are not uploaded yet.", True, None,
                           missing=missing)
    # one payable session per order: the earlier ones are expired at Stripe first, so the old tab cannot be paid too
    paid_sess, settling = pay.close_open_sessions(order, rec)
    if paid_sess is not None:
        paid, new = pay.record_paid(order, rec, paid_sess, "checkout")
        if new:
            pay.after_paid(order, rec, paid)
        raise store.Answer(409, "already_paid", "This order is already paid.", False,
                           order_url=pay.order_url(order, k, lang))
    if settling:
        raise store.Answer(409, "already_paid", "A payment for this order is already being confirmed.", False,
                           order_url=pay.order_url(order, k, lang), settling=True)
    amount = pay.price_cents(n, spec["style"])
    consent = {"version": pay.CONSENT_VERSION, "at": pay.iso(now), "lang": lang,
               "text_sha256": hashlib.sha256(pay.CONSENT_TEXT[lang].encode("utf-8")).hexdigest()[:16]}
    sess = pay.create_session(order, k, spec, amount, consent, expires)
    sid = sess["id"]
    rec = dict(rec, lang=lang, sessions=(list(rec.get("sessions") or [])[-9:] + [sid]),
               checkout={"session_id": sid, "created_at": int(now), "created": pay.iso(now), "amount": amount,
                         "currency": pay.CURRENCY, "spec": spec, "consent": consent, "expires_at": int(expires),
                         "livemode": bool(sess.get("livemode"))})
    pay.write_order(order, rec)
    pay.log(f"order {order}: checkout {sid} {amount} {pay.CURRENCY} {n} eye(s) {spec['style']} {lang}")
    return {"ok": True, "url": sess["url"], "order": order, "amount": amount, "currency": "EUR", "eyes": n,
            "style": spec["style"], "expires_at": int(expires)}


def handle_get(req):
    L.run(req, info, gate=False)


def handle_post(req):
    pay.serve(req, "checkout", checkout)


def handle(req):
    """scripts/dev_api.py calls handle() for GET and POST alike."""
    if req.command == "GET":
        handle_get(req)
    else:
        handle_post(req)


class handler(BaseHTTPRequestHandler):
    def do_GET(self): handle_get(self)
    def do_POST(self): handle_post(self)
