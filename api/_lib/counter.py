# -*- coding: utf-8 -*-
"""The anonymous counter (2026-10-20): which page and step a visit reached, and through which advertisement, with no cookie and no identifier.

WHAT IT IS. The pages send one tiny beacon per step (POST /api/checkout {hit, camp, lang, market}, api/checkout.py: the same route as the price test's
beacon, so the function count of the deployment does not move). hit() checks the step against an allow list, drops what looks like a robot, and writes ONE
small event (events.py kind "hit") of numbers and short codes: the step, the campaign code, the page language, the price market, the device class, the browser
family and the country. context() gives the other requests of the site (analyze, enhance, compose, checkout) the same campaign code and classes, through the
thread local iris._LOCAL.ctx, so that events.record() can attach them to the events those endpoints already write.

WHAT IT NEVER HOLDS. No cookie, no visitor number, no IP address, no user agent, no URL and no referrer: the user agent and the connection address are read in
memory, turned into a class (ios, android, desktop; fb, ig, chrome, safari, ...) or a rate-limit hash, and dropped with the request. The country is the two letter
code Vercel derives from the address (x-vercel-ip-country), nothing finer. The campaign code is the same text for everyone who followed one advertisement
(utm_source, utm_medium, utm_campaign, utm_term, utm_content as the advertiser typed them, each a short code of letters, digits and _ . -), or the class of the page
the visitor came from (facebook, instagram, tiktok, google, direct, other); the browser keeps it in sessionStorage "snapeyes.c" for the life of the tab.

THE RATE LIMIT HASH. A client that sends too many beacons is held back by a count kept in this process's memory only: a keyed hash of the connection address (a random
key made when the process starts, so the hash is neither stored nor stable), the times of its last beacons, nothing else. It is pruned as it grows and never written
anywhere. (The admin sign-in guard, ops.client_tag, does the same with a hash that it writes for two days; this one is never written.)

THE SWITCH. SNAPEYES_COUNTER (api/_lib/iris.py COUNTER_ON, read once at import, on by default): off, 0, false or no turns it off. Off, hit() counts nothing and
GET /api/health and GET /api/checkout say counter false, which is how the pages know to send nothing.

Module rule: nothing heavy is imported at module level (iris.run imports this file; events and iris are imported inside the functions that need them)."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import threading
import time
from urllib.parse import unquote_plus

CODE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,39}$")
_ADDRESS = re.compile(r"^[0-9]{1,3}(\.[0-9]{1,3}){3}$")        # a dotted number that is an IPv4 address is no campaign code (events.py holds the same rule for every code it stores)
_UTM = {"utm_source": "src", "utm_medium": "med", "utm_campaign": "cmp", "utm_term": "trm", "utm_content": "cnt"}
PARTS = ("src", "med", "cmp", "trm", "cnt")        # utm_source, utm_medium, utm_campaign, utm_term (the ad set), utm_content (the advertisement)
LANGS = ("en", "de", "lt", "hu")
MARKETS = ("eu", "lt", "hu", "au")                  # api/_lib/markets.py keys; a copy so that this file imports nothing (a test holds the two equal)
STEPS = ("landing", "try", "photo", "result", "soon", "buy", "order")
REFERRERS = ("facebook", "instagram", "tiktok", "google", "direct", "other")
TOOK_MAX_MS = 900_000       # a client measured time to a preview above fifteen minutes is not a time
BEACON_WAIT = 0.6           # seconds a beacon waits for its event to be written
CLIENT_MAX = 40             # beacons per client per CLIENT_WINDOW seconds (a visit sends at most about eight)
CLIENT_WINDOW = 60.0
CLIENTS_KEPT = 2000         # the in-memory rate table is cut back above this

_BOT = re.compile(
    r"bot\b|crawl|spider|slurp|facebookexternalhit|facebookcatalog|meta-externalagent|meta-externalfetcher|headless|lighthouse|pagespeed|gtmetrix|pingdom|"
    r"uptime|monitor|python|curl/|wget|java/|okhttp|go-http|axios|libwww|httpclient|node-fetch|postman|scanner|preview|phantom|puppeteer|playwright|selenium|"
    r"semrush|ahrefs|mj12|dataprovider|bytespider|petalbot|embedly|vkshare|skypeuripreview|snapeyes-self-call", re.I)      # the last one: the server's own relay calls (api/_lib/maker.py)
_IOS = re.compile(r"iPhone|iPad|iPod")
_DESKTOP = re.compile(r"Windows|Macintosh|X11|Linux|CrOS")

_KEY = os.urandom(16)          # the rate limit hash's key: made when the process starts, never stored, so the hash is neither kept nor stable
_LOCK = threading.Lock()
_CLIENTS: dict[str, list[float]] = {}


# ----------------------------------------------------------------------------- classes of a user agent and of a country
def ua_classes(ua) -> tuple[str, str, bool]:
    """(device class, browser family, robot) of a user agent. The string is looked at and dropped; only the classes leave this function.
    device: ios, android, desktop, other, unknown. browser: ig (Instagram's in-app browser), fb (Facebook's and Messenger's), tt (TikTok's), wv (another in-app web view),
    samsung, edge, opera, firefox, chrome, safari, other. robot: a user agent that is empty, too short to be a browser, or names a crawler, a link preview or a script."""
    ua = ua if isinstance(ua, str) else ""
    ua = ua[:500]
    if len(ua) < 20 or _BOT.search(ua):
        return "unknown", "other", True
    if _IOS.search(ua):
        dev = "ios"
    elif "Android" in ua:
        dev = "android"
    elif _DESKTOP.search(ua):
        dev = "desktop"
    else:
        dev = "other"
    if "Instagram" in ua:
        br = "ig"
    elif re.search(r"FBAN|FBAV|FB_IAB|FBIOS|FB4A|FBMD|MESSENGER", ua):
        br = "fb"
    elif re.search(r"TikTok|musical_ly|BytedanceWebview|Bytedance", ua):
        br = "tt"
    elif "SamsungBrowser" in ua:
        br = "samsung"
    elif re.search(r"EdgA|EdgiOS|Edg/|Edge/", ua):
        br = "edge"
    elif re.search(r"OPR/|OPiOS|Opera", ua):
        br = "opera"
    elif re.search(r"Firefox|FxiOS", ua):
        br = "firefox"
    elif re.search(r"; wv\)|\bwv\b", ua) or (dev == "ios" and "Safari/" not in ua and "CriOS" not in ua and "FxiOS" not in ua):
        br = "wv"                  # an Android web view, or an iPhone browser without the Safari token: another app's in-app browser
    elif re.search(r"CriOS|Chrome/|Chromium", ua):
        br = "chrome"
    elif "Safari/" in ua:
        br = "safari"
    else:
        br = "other"
    return dev, br, False


def country(value) -> str:
    """The two letter country code Vercel derives from the address, in lower case; "xx" when it names none."""
    v = value.strip().lower() if isinstance(value, str) else ""
    return v if re.fullmatch(r"[a-z]{2}", v) else "xx"


def is_code(value) -> bool:
    """Is value a short code (letters, digits and _ . -, at most 40, starting with a letter or a digit) that is not an IPv4 address?"""
    return isinstance(value, str) and bool(CODE.fullmatch(value)) and not _ADDRESS.fullmatch(value)


def _one(value, allowed):
    v = value.strip().lower() if isinstance(value, str) else ""
    return v if v in allowed else None


# ----------------------------------------------------------------------------- the campaign code
def parse(value):
    """The campaign code a page sent as {src, med, cmp, trm, cnt} with only the parts that are valid codes, or None when there is no source. Two forms are read. The wire form is what the pages
    carry (src/shared/counter.ts capture): the utm_ parameters of the address as they stand, "utm_source=fb&utm_medium=paid&utm_campaign=se-p0-test&utm_term=lt-a1-eye&utm_content=a1-lt-s1"
    (percent-encoded as in the link), or "ref=facebook" (the kind of page the visitor came from: facebook, instagram, tiktok, google, direct, other) when the link named no campaign. The
    stored form is pack()'s "src|med|cmp|trm|cnt" (the order record, Stripe's metadata). A part that is not a short code of letters, digits and _ . - (at most 40 characters, starting with a
    letter or a digit, not an IPv4 address) is dropped on its own, so a stranger's text can never reach an event; the source decides whether anything is kept at all."""
    if not isinstance(value, str) or not value or len(value) > 500:
        return None
    out = {}
    if "=" in value:
        ref = None
        for pair in value.split("&")[:12]:
            k, _, v = pair.partition("=")
            v = unquote_plus(v)[:80].strip().lower()
            if k == "ref":
                ref = v if v in REFERRERS else None
            elif k in _UTM and is_code(v):
                out.setdefault(_UTM[k], v)
        if not out.get("src") and ref:
            out = {"src": ref}
    else:
        parts = value.split("|")
        for name, p in zip(PARTS, parts[:len(PARTS)]):
            p = p.strip().lower()
            if is_code(p):
                out[name] = p
    return out if out.get("src") else None


def pack(camp) -> str:
    """The campaign dict as the one string that travels (Stripe metadata src, the order record): "src|med|cmp|trm|cnt", empty parts empty."""
    if not isinstance(camp, dict):
        return ""
    return "|".join(str(camp.get(k) or "") for k in PARTS).rstrip("|")


# ----------------------------------------------------------------------------- the context of a request
def _tag(req) -> str:
    """The rate limit hash of the connection address: 12 hex characters of a keyed hash, held in memory only."""
    h = getattr(req, "headers", None)
    ip = ""
    if h is not None:
        ip = str(h.get("x-real-ip") or "").strip() or str(h.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip:
        try:
            ip = str(req.client_address[0])
        except Exception:  # noqa
            ip = "unknown"
    return hmac.new(_KEY, ip[:64].encode("utf-8", "replace"), hashlib.sha256).hexdigest()[:12]


def context(req, body):
    """What the request says about where it came from, as classes: {camp, dev, br, bot, cc, lang, market, tag}. Never raises (None on a failure). The user agent and the address
    are read here and not kept; tag is the rate limit hash and lives in this dict for the length of the request. The body's "camp" is the page's campaign code and its "lang" and
    "market" the page's language and price market (each checked against the lists above)."""
    try:
        h = getattr(req, "headers", None)
        get = (lambda k: h.get(k)) if h is not None else (lambda k: None)
        dev, br, bot = ua_classes(get("user-agent"))
        b = body if isinstance(body, dict) else {}
        return {"camp": parse(b.get("camp")), "dev": dev, "br": br, "bot": bot, "cc": country(get("x-vercel-ip-country")),
                "lang": _one(b.get("lang"), LANGS), "market": _one(b.get("market"), MARKETS),
                "tag": _tag(req) if ("hit" in b or "feedback" in b) else None}
    except Exception:  # noqa: the context is a convenience; a request never fails for it
        return None


def attach(fields, ctx):
    """fields (the arguments of an events.record call) completed from the request's context: the campaign parts, the device class, the browser family, the country, and the page's
    language and price market where the call named none. A value the caller gave is kept. Returns a new dict."""
    out = dict(fields)
    if not isinstance(ctx, dict):
        return out
    camp = ctx.get("camp") or {}
    for k in PARTS:
        if out.get(k) is None and camp.get(k):
            out[k] = camp[k]
    for k in ("dev", "br", "cc", "lang", "market"):
        if out.get(k) is None and ctx.get(k):
            out[k] = ctx[k]
    return out


# ----------------------------------------------------------------------------- the beacon
def on() -> bool:
    """Is the counter on here? The switch (iris.COUNTER_ON, read once at import) and somewhere to keep the counts that the daily clean-up can delete (events.record's own rule)."""
    try:
        from . import iris as L
        from . import events as E
        from . import store
        return bool(L.COUNTER_ON and store.configured() and E.retention_ok())
    except Exception:  # noqa
        return False


def _client_ok(tag, now) -> bool:
    if not tag:
        return True
    with _LOCK:
        if len(_CLIENTS) > CLIENTS_KEPT:
            for k in [k for k, v in _CLIENTS.items() if not v or now - v[-1] >= CLIENT_WINDOW]:
                _CLIENTS.pop(k, None)
            if len(_CLIENTS) > CLIENTS_KEPT:
                _CLIENTS.clear()
        q = [t for t in _CLIENTS.get(tag, []) if now - t < CLIENT_WINDOW]
        if len(q) >= CLIENT_MAX:
            _CLIENTS[tag] = q
            return False
        q.append(now)
        _CLIENTS[tag] = q
        return True


def hit(body):
    """POST /api/checkout {hit: <step>, camp, lang, market[, took, eyes, style]}: one anonymous count of a step a page reached. Always answered 200 {ok, counted}: a beacon
    is best effort and the page never shows a failure for it. Counted only when the counter is on, the step is one of STEPS, the request does not look like a robot and the
    client has not sent more than CLIENT_MAX beacons in the last CLIENT_WINDOW seconds. took (result only): the milliseconds the page measured from the photo to the preview."""
    from . import iris as L
    from . import events as E
    step = body.get("hit")
    if step not in STEPS:
        return {"ok": True, "counted": False}
    if not on():
        return {"ok": True, "counted": False, "on": False}
    ctx = L.ctx() or {}
    if ctx.get("bot") or not _client_ok(ctx.get("tag"), time.time()):
        return {"ok": True, "counted": False}
    f = attach({"step": step}, ctx)
    took = body.get("took")
    if step == "result" and isinstance(took, (int, float)) and not isinstance(took, bool) and 0 <= took <= TOOK_MAX_MS:
        f["took"] = int(took)
    eyes = body.get("eyes")
    if isinstance(eyes, int) and not isinstance(eyes, bool) and 1 <= eyes <= 8:
        f["eyes"] = eyes
    style = body.get("style")
    if is_code(style):
        f["style"] = style
    return {"ok": True, "counted": bool(E.record("hit", _wait=BEACON_WAIT, **f))}
