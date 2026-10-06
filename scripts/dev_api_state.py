# -*- coding: utf-8 -*-
"""The local dev API (scripts/dev_api.py) put in ONE STATE of the owner's style catalogue, so that the landing page can be looked at against the real GET /api/checkout:

    python scripts/dev_api_state.py --state closed|open_none|one|ceilings [--port 5051] [--style <registry id>]

  closed      no payments configured: GET /api/checkout says open false (the state of a deployment before the owner opens ordering)
  open_none   ordering open (a Stripe TEST key and a webhook secret of the right shape, both placeholders: nothing is ever sent to Stripe, no payment is made here, a local folder stands
              for the bucket) and the owner has ticked nothing: open true, orderable_max_eyes 0 (the state the cutover leaves)
  one         as open_none with ONE style ticked live for one eye (--style, default: the first art style of the registry whose ceiling is live): orderable_max_eyes 1
  ceilings    as open_none with every style ticked up to its ceiling (what the cutover's table allows: five singles and the Trio): orderable_max_eyes 3

The code that answers is the real api/ (api/checkout.py, api/health.py, api/_lib/catalogue.py); only the place the owner's override is read from is stood in for
(catalogue.set_override_source: in production api/_lib/stage_overrides.py reads it from private storage). No image model is called, no key is read, nothing is written outside the
temporary folder the store uses. For tests and for looking: scripts/check_landing_states.mjs --api dev starts one of these per state.
"""
import argparse
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "api")

ap = argparse.ArgumentParser()
ap.add_argument("--state", required=True, choices=["closed", "open_none", "one", "ceilings"])
ap.add_argument("--port", type=int, default=5051)
ap.add_argument("--style", default="")
args = ap.parse_args()

if args.state != "closed":
    # placeholders of the right SHAPE (api/_lib/pay.py _SK and _WHSEC): the server only checks their form, the dev server never contacts Stripe
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_" + "a" * 24
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_" + "b" * 24
    os.environ["STORE_LOCAL_DIR"] = tempfile.mkdtemp(prefix="snapeyes_dev_state_")
    os.environ.pop("VERCEL", None)
    os.environ.pop("VERCEL_ENV", None)
else:
    for k in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET"):
        os.environ.pop(k, None)

sys.path.insert(0, API)
from _lib import catalogue as CT  # noqa: E402

if args.state in ("one", "ceilings"):
    one = args.style
    if args.state == "one" and not one:
        pool = [i for i, d in CT.STYLES.items() if not CT.is_legacy(i) and d["tile_order"] > 0 and CT.price_class(i) == "art" and CT.ceiling(i, 1) == "live"]
        one = sorted(pool, key=lambda i: CT.STYLES[i]["tile_order"])[0]

    def ticked(style_id, n):
        """The owner's override: a stage the style is held at (the ceiling is the most), or None for none."""
        if args.state == "ceilings":
            return "live"
        return "live" if style_id == one and n == 1 else None

    CT.set_override_source(ticked)
    print(f"dev api state {args.state}" + (f", ticked: {one}" if args.state == "one" else ""), flush=True)
else:
    CT.set_override_source(None if args.state == "closed" else (lambda style_id, n: None))
    print(f"dev api state {args.state}", flush=True)

sys.path.insert(0, os.path.join(ROOT, "scripts"))
import dev_api  # noqa: E402  (loads every api/*.py handler; it serves only when run as a script)
from http.server import ThreadingHTTPServer  # noqa: E402

ThreadingHTTPServer(("127.0.0.1", args.port), dev_api.Dispatch).serve_forever()
