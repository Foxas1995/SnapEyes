# -*- coding: utf-8 -*-
"""POST /api/admin {action, ...} with "Authorization: Bearer <admin key>": the owner's admin panel (/admin, src/admin/).
One function for every admin action (Vercel Hobby counts functions): api/_lib/ops.py has the login check, the views
and the actions; scripts/mint_admin.py makes the key. Every reply is JSON; refusals are {ok: false, reason, error,
retry} (403 admin_denied, 429 too_many_attempts, 409/410 for an action that does not fit the order's state, 503 when
storage or Stripe is missing or busy)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler
from _lib import ops


def handle(req):
    ops.serve(req)


class handler(BaseHTTPRequestHandler):
    def do_POST(self): handle(self)
