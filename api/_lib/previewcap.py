# -*- coding: utf-8 -*-
"""The day's ceiling of free previews per connection (2026-11-11, the owner: "8 a day, with a message that says the limit is reached").

Each restoration /api/enhance makes with the image model leaves a marker in the private storage, ops/previewcap/<UTC day>/<tag>-<random>.json,
with nothing in it. tag is 12 hex characters of a keyed hash of the connection's address and of that day: never the address, and the same
address gets another tag the next day. A connection with CEILING markers today is refused (iris.PreviewLimit: 429 preview_limit and a sentence
in the page's language) by /api/analyze, before the photo is checked, and by /api/enhance, before the model is called, until 00:00 UTC. The
daily clean-up deletes the days older than two (events.purge_old), as the privacy policy says.

It counts only where that clean-up runs (events.retention_ok: CRON_SECRET is set) and storage is configured; elsewhere nothing is stored and
nothing is refused. SNAPEYES_PREVIEW_DAY sets the ceiling (0 turns it off); unset it is DAY_MAX on Vercel and off on a developer's machine and in
the suites, which set it themselves where they test it. A storage error lets the preview through: the page must not stop on our bookkeeping."""
import os, time, hmac, hashlib, secrets
from . import iris as L
from . import store
from . import events as E

TOP = "ops/previewcap"
DAY_MAX = 8
KEEP_DAYS = 2


def ceiling():
    """The number of previews a connection may make in a UTC day; 0: no ceiling."""
    raw = (os.environ.get("SNAPEYES_PREVIEW_DAY") or "").strip().lstrip("﻿")
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            return DAY_MAX
    return DAY_MAX if os.environ.get("VERCEL") else 0


def active():
    return ceiling() > 0 and store.configured() and E.retention_ok()


def day(now=None):
    return time.strftime("%Y%m%d", time.gmtime(time.time() if now is None else now))


def tag(req, now=None):
    """The connection's tag for the day (Vercel sets x-real-ip / x-forwarded-for itself). Only the tag leaves this function."""
    h = getattr(req, "headers", None)
    ip = ""
    if h is not None:
        ip = str(h.get("x-real-ip") or "").strip() or str(h.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip:
        try:
            ip = str(req.client_address[0])
        except Exception:  # noqa
            ip = "unknown"
    msg = b"snapeyes-previewcap-v1:" + day(now).encode("ascii") + b":" + ip[:64].encode("utf-8", "replace")
    return hmac.new(L._ticket_secret(), msg, hashlib.sha256).hexdigest()[:12]


def _seconds_left(now=None):
    now = time.time() if now is None else now
    return int((now // 86400 + 1) * 86400 - now) + 1


def check():
    """Refuse (iris.PreviewLimit) the request this thread serves when its connection has had its ceiling of previews today. Returns the tag
    to mark a made preview with, or None when nothing is counted here."""
    req = L.request()
    if req is None or not active():
        return None
    t = tag(req)
    try:
        n = len([r for r in store.list_folder(f"{TOP}/{day()}", timeout=4.0, retry=False, search=t) if not r["folder"]])
    except store.StorageError:
        return t
    if n >= ceiling():
        print(f"snapeyes preview ceiling: connection {t} had {n} previews today", flush=True)
        raise L.PreviewLimit(ceiling(), _seconds_left())
    return t


def mark(t):
    """One preview made by this connection (best effort: a lost marker lets one more preview through)."""
    if not t:
        return
    try:
        store.put(f"{TOP}/{day()}/{t}-{secrets.token_hex(4)}.json", b"{}", "application/json", upsert=False, timeout=4.0, retry=False)
    except store.StorageError:
        pass
