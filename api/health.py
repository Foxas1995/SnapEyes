# -*- coding: utf-8 -*-
"""GET /api/health - shows which pieces are configured on this deployment (no secrets).
commit lets the owner check that the live code is the reviewed code. Model names and the style list are
left out on purpose: a public endpoint has no reason to describe the engine to strangers."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import iris as L
from _lib import store
from _lib import pay
from _lib.styles import plates
import deglare

def handle(req):
    pay.start_clock()             # this handler does not go through L.run: the legal pack fetch needs a deadline
    info = {"ok": True, "commit": os.environ.get("VERCEL_GIT_COMMIT_SHA", "")[:7],
            "gemini_key": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
            "blob_store": bool(os.environ.get("BLOB_READ_WRITE_TOKEN", "").strip()),
            # the private Supabase store for paid 4K files (env only, no network call). Separate from blob_store,
            # which /try reads to decide whether to offer the training-memory opt-in: that must stay off.
            "master_store": store.configured(),
            # payments (booleans only): Stripe secret key + webhook secret both usable, whether that key is a live
            # one, and whether the delivery email (Resend) is configured. /api/checkout GET says whether ordering is open.
            "stripe": pay.stripe_configured(),
            "stripe_live": pay.stripe_configured() and pay.stripe_live(),
            "email": pay.email_configured(),
            # whether this deployment takes new orders (a live key needs the email, CRON_SECRET and complete legal
            # texts; a test key never on production) and whether a Stripe TEST payment unlocks files here (a Preview
            # with SNAPEYES_ALLOW_TEST_ORDERS=1 only)
            "ordering": pay.ordering_open() and store.configured(),
            "test_orders": pay.test_orders_allowed(),
            # whether the daily clean-up can run here (CRON_SECRET set; vercel.json crons calls GET /api/order)
            "cron": len(pay._env("CRON_SECRET")) >= 16,
            # whether /legal/order-mail.json is readable and complete enough for live sales (pay.legal_problem)
            "legal": not pay.legal_problem(),
            # whether /api/deglare calls the image model for reflections (off by default, see deglare.DEGLARE_MODEL)
            "deglare_model": deglare.DEGLARE_MODEL,
            "sr_model": os.path.exists(os.path.join(L.ASSETS, "models", "realesr_general_x4v3.onnx"))}
    # the style engine (booleans only): the registries agree, and the 4K plates the visible styles fetch are in storage (api/_lib/styles/plates.py health)
    info.update(plates.health())
    L.send_json(req, 200, info)

class handler(BaseHTTPRequestHandler):
    def do_GET(self): handle(self)
