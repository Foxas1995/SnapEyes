# -*- coding: utf-8 -*-
"""The print partner's API (merchOne, the print-on-demand brand of Picanova GmbH): REST JSON over HTTPS with HTTP Basic auth, no SDK.
Used by api/_lib/prints.py (the order of a print, its status) and scripts/print_rates.py (the rate table). Nothing here knows an order of ours.

Environment (Vercel, Production; values are never logged or returned):
  MERCHONE_API_USER, MERCHONE_API_KEY   the API user and key of the store "SnapEyes" (merchOne dashboard, Stores, API). Without both nothing is
                                        sent and every call raises NotConfigured.
  MERCHONE_LIVE                         "1" (or on, yes, true): orders go to production (is_test false) for LIVE Stripe payments. Anything else,
                                        or unset: every order is a TEST order (is_test true: accepted, not produced, not charged). A Stripe test
                                        payment is a test order whatever this says (prints.py). While the store is inactive at merchOne (its
                                        sandbox) every order is a test order on their side anyway.
Tests only, ignored whenever VERCEL is set: MERCHONE_API_BASE = http://127.0.0.1:<port> (a local stub). It replaces both bases.

Limits (docs.merchone.com): 60 calls a minute per account, 99 items an order, 40 MB a file. The v1 API makes and reads orders; the beta API
(same credentials) cancels one and shows its shipments (tracking)."""
import os, re, time
import requests
from . import iris as L
from . import store

BASE_V1 = "https://api.merchone.com/api/v1"
BASE_BETA = "https://api.merchone.com/api/beta"
_TEST_BASE = re.compile(r"^http://(localhost|127\.0\.0\.1):[0-9]{1,5}$")
_TOKEN = re.compile(r"^[A-Za-z0-9._~+/=-]{4,256}$")
ORDER_ID_RE = re.compile(r"^[A-Z]{2,5}[0-9]{4,14}T?$")      # "PPO31186620T": a test order ends in T


class NotConfigured(RuntimeError):
    """MERCHONE_API_USER or MERCHONE_API_KEY is not set (or not well formed)."""


class Busy(RuntimeError):
    """merchOne did not answer in time, or answered 429 or 5xx: a later try can succeed."""


class Refused(RuntimeError):
    """merchOne refused the request (a 4xx other than 429). .status, .message (merchOne's own sentence, at most 300 characters), .errors."""

    def __init__(self, status, message, errors=None):
        super().__init__(f"HTTP {status}: {message}")
        self.status, self.message, self.errors = status, message, errors if isinstance(errors, dict) else {}


def _env(name):
    return store._clean(os.environ.get(name))


def credentials():
    """(user, key), or None when they are not both set and well formed."""
    u, k = _env("MERCHONE_API_USER"), _env("MERCHONE_API_KEY")
    return (u, k) if _TOKEN.fullmatch(u or "") and _TOKEN.fullmatch(k or "") else None


def configured():
    return credentials() is not None


def problem():
    """What is missing, in words that never include a value ("" when ready)."""
    if not _env("MERCHONE_API_USER") or not _env("MERCHONE_API_KEY"):
        return "MERCHONE_API_USER and MERCHONE_API_KEY are not set"
    if credentials() is None:
        return "MERCHONE_API_USER or MERCHONE_API_KEY is malformed (the value is not logged)"
    return ""


def live():
    """Does this deployment send production orders (MERCHONE_LIVE)? The default is no: every order is a test order."""
    return _env("MERCHONE_LIVE").lower() in ("1", "on", "yes", "true")


def secrets_list():
    """The values pay.scrub must never let into a log line."""
    return [v for v in (_env("MERCHONE_API_USER"), _env("MERCHONE_API_KEY")) if len(v) >= 6]


def _base(beta=False):
    if not os.environ.get("VERCEL"):
        t = _env("MERCHONE_API_BASE").rstrip("/")
        if _TEST_BASE.fullmatch(t):
            return t + ("/api/beta" if beta else "/api/v1")
    return BASE_BETA if beta else BASE_V1


def _scrub(s):
    s = str(s or "")
    for v in secrets_list():
        s = s.replace(v, "***")
    return s[:300]


def call(method, path, body=None, beta=False, timeout=20.0, retry=True, deadline=True):
    """One API call: the parsed JSON reply (a dict; {} for an empty 2xx reply). Raises NotConfigured, Busy or Refused. A GET is tried once more
    after a connection error or a 429/5xx when the second try still fits the invocation's time (deadline=False: a script, no invocation clock).
    A POST is never repeated here: the caller decides (an order is made once; prints.py asks merchOne whether it exists before a second try)."""
    cred = credentials()
    if cred is None:
        raise NotConfigured(problem() or "merchOne is not configured")
    url = _base(beta) + path
    label = f"merchone {method} {path.split('?')[0][:60]}"
    tries = 2 if (retry and method == "GET") else 1
    for attempt in range(1, tries + 1):
        t = timeout if not deadline else min(timeout, L.time_left(99.0) - 2.0)
        if t < 2.0:
            raise Busy(f"{label}: out of time")
        try:
            r = requests.request(method, url, json=body, auth=cred, headers={"Accept": "application/json"}, timeout=t)
        except requests.RequestException as e:
            if attempt < tries:
                time.sleep(0.6)
                continue
            raise Busy(f"{label}: {type(e).__name__}") from None
        if r.status_code in (429, 500, 502, 503, 504):
            if attempt < tries:
                time.sleep(1.2)
                continue
            raise Busy(f"{label}: HTTP {r.status_code}")
        try:
            j = r.json() if r.content else {}
        except ValueError:
            j = None
        if 200 <= r.status_code < 300:
            return j if isinstance(j, dict) else {}
        msg = _scrub((j or {}).get("message") if isinstance(j, dict) else r.text[:200])
        if r.status_code in (401, 403):
            raise NotConfigured(f"{label}: HTTP {r.status_code} (the API user or key was refused)")
        raise Refused(r.status_code, msg or f"HTTP {r.status_code}", (j or {}).get("errors") if isinstance(j, dict) else None)
    raise Busy(f"{label}: no try left")


def existing_id(err):
    """The id of an order merchOne already has with the same external id, from its refusal ("This store already has a previous order with an
    external ID 260101-abcd (PPO31186620T) in our system."), or None. The guard that makes a repeated create adopt the first order."""
    if not isinstance(err, Refused) or err.status != 422:
        return None
    text = " ".join([err.message] + [" ".join(v) if isinstance(v, list) else str(v) for v in (err.errors.get("external_id") or [])])
    if "external" not in text.lower():
        return None
    m = re.search(r"\(([A-Z]{2,5}[0-9]{4,14}T?)\)", text)
    return m.group(1) if m else None


# ----------------------------------------------------------------------------- the calls prints.py makes
def create_order(payload):
    """POST /orders (v1): the new order's id ("PPO...", a test order ends in T). Raises Refused with existing_id() set when the external id is taken."""
    j = call("POST", "/orders", payload, timeout=30.0)
    oid = j.get("order_id") or ((j.get("data") or {}).get("order_id") if isinstance(j.get("data"), dict) else None)
    if not isinstance(oid, str) or not ORDER_ID_RE.fullmatch(oid):
        raise Busy("merchone create order: the reply names no order id")
    return oid


def get_order(oid):
    """GET /orders/{id} (beta): {id, external_id, is_test, status, status_label, shipments: [{tracking_number, tracking_url, shipped_at,
    shipping_method}], ...}, or None when merchOne has no such order."""
    if not isinstance(oid, str) or not ORDER_ID_RE.fullmatch(oid):
        return None
    try:
        j = call("GET", f"/orders/{oid}", beta=True)
    except Refused as e:
        if e.status == 404:
            return None
        raise
    d = j.get("data")
    return d if isinstance(d, dict) else None


def cancel_order(oid):
    """DELETE /orders/{id} (beta): cancels an order merchOne has not accepted into production yet. True when it is cancelled now."""
    if not isinstance(oid, str) or not ORDER_ID_RE.fullmatch(oid):
        raise Refused(400, "not an order id of merchOne")
    call("DELETE", f"/orders/{oid}", beta=True, timeout=20.0, retry=False)
    return True


def shipping_rates(country, zipcode, sku, quantity=1, deadline=False):
    """POST /shipment/rates (v1): [{type, cost, currency}] for one product to one country (scripts/print_rates.py)."""
    j = call("POST", "/shipment/rates", {"address": {"zipcode": zipcode, "country": country}, "order": [{"product_sku": sku, "quantity": quantity}]},
             deadline=deadline)
    d = j.get("data")
    return d if isinstance(d, list) else []


def variant_options(blueprint, variant, deadline=False):
    """GET /blueprints/{id}/variants/{vid}/options (v1): the SKUs of a variant with price and print areas."""
    j = call("GET", f"/blueprints/{int(blueprint)}/variants/{int(variant)}/options", deadline=deadline)
    return j.get("data") if isinstance(j.get("data"), dict) else {}


def variants(blueprint, deadline=False):
    """GET /blueprints/{id}/variants (v1): the sizes of a product, with the design area and the print file size (trim) of each."""
    j = call("GET", f"/blueprints/{int(blueprint)}/variants", deadline=deadline)
    return j.get("data") if isinstance(j.get("data"), list) else []
