# -*- coding: utf-8 -*-
"""The Meta (Facebook) pixel's server half, the Conversions API (the owner's decision of 2026-11-25: the pixel and the Conversions API
"the way TaleInTune does it", for everyone, with no cookie banner; the privacy policy says so, src/legal/docs/privacy*.ts section "meta").

WHAT IT SENDS. One event, Purchase, once per payment, when the payment's record is made for the first time: the artwork (pay.record_paid,
paid.json), a gift voucher (voucher.on_paid, the voucher's record) and a print bought after the artwork (prints.addon_record, print_paid.json).
The event carries its name, its time, action_source "website", the page's address WITHOUT its query (the order page's address holds the order's
key: never sent), the amount and the currency, a content category ("artwork", "voucher" or "print"), and the user data: SHA-256 of the buyer's
e-mail address (lower case, trimmed; also as external_id), the hashed country when Stripe or the market names one, and the four values the
checkout carried in the Stripe session's metadata (checkout_meta): the _fbp and _fbc cookie values, the client's IP address and user agent.
NOTHING about the photo, the iris, the eye colour, the style, the names or any image ever goes into it: purchase() builds the payload from
those fields alone (suites: scripts/styles_tests/test_meta.py).

DEDUPLICATION. The browser fires the same Purchase (src/shared/metaPixel.ts) with the same event id, and Meta keeps one of the two:
"purchase_<Stripe session id>" for the artwork and the print. For a gift voucher the id is "purchase_" and the first 32 hex characters of
SHA-256 of the session id (event_id): the voucher's session id is what GET /api/checkout?gift= answers the CODE for, so the raw id must never
reach Meta (the one id that is not the raw session id, on purpose).

WHEN IT DOES NOTHING. No pixel id (META_PIXEL_ID set to an empty or malformed value), no access token (META_CAPI_TOKEN, set by the owner in
Vercel; said once in the log per instance), a payment in Stripe test mode (livemode false: the test orders of a Preview), or too little time
left in the invocation. The token is read from the environment only, sent in the POST body (never in the address, which logs and exceptions
can show), and never logged. A failure (a timeout, a refusal, anything) is caught and logged without the token and without the payload: the
payment's own handling never fails or waits more than TIMEOUT seconds for it. Optional META_TEST_EVENT_CODE adds test_event_code (Meta's
Test Events tab). Outgoing HTTP as the rest of api/_lib does it (requests, as pay._stripe and the Resend calls).

THE CHECKOUT'S HALF (checkout_meta): while the Conversions API is configured, the three checkouts (api/checkout.py, voucher.buy,
prints.addon_buy) put fbp, fbc (sent by the page: src/shared/metaPixel.ts metaIds), the client's IP (x-real-ip, else the first
x-forwarded-for) and its user agent into the Stripe session's metadata (keys fbp, fbc, cip, cua), where the campaign code travels too (src).
Without a token nothing of it is collected. They are stored nowhere else by this site (not in order.json, not in paid.json)."""
import os, re, json, time, hashlib, ipaddress
import requests
from . import iris as L

PIXEL_ID = "1804549607500630"      # THE ONE PLACE of the dataset id (public). vite.config.ts reads it from here for the pages; META_PIXEL_ID overrides it
GRAPH_API = "https://graph.facebook.com"
API_VERSION = "v21.0"
TIMEOUT = 3.0                       # seconds: a hung Meta endpoint must not hold the payment's handling
TIME_MARGIN = 10.0                  # seconds the invocation keeps for its own work after the call
CATEGORIES = ("artwork", "voucher", "print")
META_KEYS = ("fbp", "fbc", "cip", "cua")        # the Stripe metadata keys of checkout_meta
UA_MAX = 400                        # Stripe takes 500 characters a metadata value
_FBP = re.compile(r"^fb\.[0-9]\.[0-9]{10,14}\.[0-9]{1,30}$")
_FBC = re.compile(r"^fb\.[0-9]\.[0-9]{10,14}\.[A-Za-z0-9_-]{8,300}$")
_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,500}$")
_TEST_CODE = re.compile(r"^[A-Za-z0-9]{3,40}$")
_SAID = {"no_token": False, "bad_id": False}


def _env(name):
    v = str(os.environ.get(name) or "")
    return v.replace("﻿", "").strip()


def log(msg):
    """One log line; the token is never part of it (scrubbed anyway, should a caller ever pass it)."""
    t = token()
    s = str(msg)
    if t:
        s = s.replace(t, "***")
    print("snapeyes meta: " + L._scrub(s)[:400], flush=True)


def pixel_id():
    """The dataset id: META_PIXEL_ID when it is set (an empty value switches the pixel and the Conversions API off; a value that is not a
    plain run of digits too, said once), else PIXEL_ID."""
    if "META_PIXEL_ID" not in os.environ:
        return PIXEL_ID
    v = _env("META_PIXEL_ID")
    if v and not re.fullmatch(r"[0-9]{5,20}", v):
        if not _SAID["bad_id"]:
            _SAID["bad_id"] = True
            print("snapeyes meta: META_PIXEL_ID is not a plain number: the Conversions API is off", flush=True)
        return ""
    return v


def token():
    v = _env("META_CAPI_TOKEN")
    return v if _TOKEN.fullmatch(v) else ""


def pixel_on():
    """Does this deployment name a pixel (GET /api/health meta_pixel)? The pages are built with the same id (vite.config.ts)."""
    return bool(pixel_id())


def capi_on():
    """Can purchases be sent from the server (GET /api/health meta_capi): a pixel id and a well formed token."""
    return bool(pixel_id()) and bool(token())


def sha(value):
    """SHA-256 of the normalised value (trimmed, lower case), as Meta wants every personal identifier."""
    return hashlib.sha256(str(value).strip().lower().encode("utf-8")).hexdigest()


def event_id(sid, kind):
    """The event id the browser sends too (src/shared/metaPixel.ts purchaseId): purchase_<session id>; a voucher's session id hashed (see above)."""
    sid = str(sid or "")
    if kind == "voucher":
        return "purchase_" + hashlib.sha256(sid.encode("utf-8")).hexdigest()[:32]
    return "purchase_" + sid


# ----------------------------------------------------------------------------- the checkout's half
def _client_ip(req):
    h = getattr(req, "headers", None)
    if h is None:
        return ""
    ip = str(h.get("x-real-ip") or "").strip() or str(h.get("x-forwarded-for") or "").split(",")[0].strip()
    try:
        return str(ipaddress.ip_address(ip))
    except ValueError:
        return ""


def _user_agent(req):
    h = getattr(req, "headers", None)
    ua = str((h.get("user-agent") if h is not None else "") or "")
    return re.sub(r"[\x00-\x1f\x7f]", "", ua).strip()[:UA_MAX]


def checkout_meta(body, req=None):
    """The Stripe metadata a checkout adds for the Conversions API: {fbp, fbc, cip, cua}, each only when it is there and well formed. Nothing
    at all while the Conversions API is not configured (no token: nothing is collected that nothing would send). body: the checkout request
    (fbp and fbc as the page read them from its cookies, src/shared/metaPixel.ts metaIds); req: the request (L.request() when not given)."""
    if not capi_on():
        return {}
    req = req if req is not None else L.request()
    out = {}
    b = body if isinstance(body, dict) else {}
    fbp, fbc = b.get("fbp"), b.get("fbc")
    if isinstance(fbp, str) and _FBP.fullmatch(fbp):
        out["fbp"] = fbp
    if isinstance(fbc, str) and _FBC.fullmatch(fbc):
        out["fbc"] = fbc
    ip, ua = _client_ip(req), _user_agent(req)
    if ip:
        out["cip"] = ip
    if ua:
        out["cua"] = ua
    return out


# ----------------------------------------------------------------------------- the purchase
def _send(url, payload, timeout):
    """The one outgoing call (the suites replace it). Returns (status, error dict or None)."""
    r = requests.post(url, json=payload, timeout=timeout)
    try:
        err = (r.json() or {}).get("error") if r.status_code != 200 else None
    except (ValueError, AttributeError):
        err = None
    return r.status_code, err if isinstance(err, dict) else None


def payload(kind, sess, email, amount, currency, source_url, country=None, now=None):
    """The request body of one Purchase, without the token: only the fields named in the module's docstring."""
    meta = sess.get("metadata") if isinstance(sess, dict) and isinstance(sess.get("metadata"), dict) else {}
    em = sha(email)
    user = {"em": [em], "external_id": [em]}
    if isinstance(meta.get("fbp"), str) and _FBP.fullmatch(meta["fbp"]):
        user["fbp"] = meta["fbp"]
    if isinstance(meta.get("fbc"), str) and _FBC.fullmatch(meta["fbc"]):
        user["fbc"] = meta["fbc"]
    if isinstance(meta.get("cip"), str) and meta["cip"]:
        user["client_ip_address"] = meta["cip"][:64]
    if isinstance(meta.get("cua"), str) and meta["cua"]:
        user["client_user_agent"] = meta["cua"][:UA_MAX]
    if isinstance(country, str) and re.fullmatch(r"[A-Za-z]{2}", country):
        user["country"] = [sha(country)]
    event = {"event_name": "Purchase", "event_time": int(now if now is not None else time.time()), "event_id": event_id(sess.get("id"), kind),
             "action_source": "website", "event_source_url": str(source_url).split("?")[0].split("#")[0], "user_data": user,
             "custom_data": {"value": round(int(amount or 0) / 100.0, 2), "currency": str(currency or "").upper()[:3],
                             "content_category": kind}}
    out = {"data": [event]}
    code = _env("META_TEST_EVENT_CODE")
    if code and _TEST_CODE.fullmatch(code):
        out["test_event_code"] = code
    return out


def country_of(sess, market_countries=()):
    """The buyer's country as Stripe collected it (customer_details.address.country), else the market's one country when it names exactly one."""
    cd = sess.get("customer_details") if isinstance(sess, dict) and isinstance(sess.get("customer_details"), dict) else {}
    addr = cd.get("address") if isinstance(cd.get("address"), dict) else {}
    cc = addr.get("country")
    if isinstance(cc, str) and re.fullmatch(r"[A-Za-z]{2}", cc):
        return cc.upper()
    mc = [c for c in (market_countries or ()) if isinstance(c, str)]
    return mc[0] if len(mc) == 1 else None


def purchase(kind, sess, email, amount, currency, source_url, country=None):
    """Send one Purchase to Meta. Never raises; returns what happened: "sent", "off" (no pixel id or no token), "test" (Stripe test mode),
    "no_email", "no_time", "refused" or "failed". Called once per payment, right after its record was made."""
    try:
        if kind not in CATEGORIES or not isinstance(sess, dict):
            return "failed"
        pid = pixel_id()
        tok = token()
        if not pid or not tok:
            if pid and not _SAID["no_token"]:
                _SAID["no_token"] = True
                log("META_CAPI_TOKEN is not set: purchases are not sent to Meta from the server (the browser pixel still reports them)")
            return "off"
        if sess.get("livemode") is not True:
            return "test"
        if not (isinstance(email, str) and "@" in email):
            log(f"{kind} {str(sess.get('id'))[:40]}: no e-mail address, not sent")
            return "no_email"
        t = min(TIMEOUT, L.time_left() - TIME_MARGIN)
        if t < 1.0:
            log(f"{kind} {str(sess.get('id'))[:40]}: too little time left in this call, not sent")
            return "no_time"
        body = payload(kind, sess, email, amount, currency, source_url, country)
        eid = body["data"][0]["event_id"]
        body["access_token"] = tok
        status, err = _send(f"{GRAPH_API}/{API_VERSION}/{pid}/events", body, t)
        if status != 200:
            e = err or {}
            log(f"{kind} {eid[:60]}: Meta refused the Purchase: HTTP {status} {e.get('type')} {e.get('code')} {str(e.get('message') or '')[:120]}")
            return "refused"
        log(f"{kind} {eid[:60]}: Purchase sent ({body['data'][0]['custom_data']['value']} {body['data'][0]['custom_data']['currency']})")
        return "sent"
    except Exception as e:  # noqa: never the payment's failure, never the exception's text (it can hold the request)
        try:
            log(f"{kind}: the Purchase was not sent: {type(e).__name__}")
        except Exception:  # noqa
            pass
        return "failed"
