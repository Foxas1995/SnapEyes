# -*- coding: utf-8 -*-
"""The anonymous feedback box of /try (2026-10-20): one of six answers and, if the visitor wants, a few words, with no e-mail, no name, no account and no identifier.

WHAT IT IS. On the result screen and on the card that asks for another photo, /try (src/try/Feedback.tsx) offers six chips and an optional text of up to 300 characters. When the
visitor presses Send, ONE request goes to the beacon route (POST /api/checkout {feedback: {w, c, x, eyes, t, hp}, camp, lang, market}, api/checkout.py: no new function). submit() checks
it, drops what looks like a robot or a flood, and writes up to two things:
  1. an event (events.py kind "fb") of codes only: the place (w: result or retake), the chip (c), the style on screen or the block reason (x), the number of eyes, what became of the
     text (txt: kept, or contact, link, junk, dup), and the same campaign code and classes as the counter (src, med, cmp, trm, cnt, lang, market, dev, br, cc). It is counted per day (fx
     metrics fb_result, fb_retake, fb_style, fb_block, fb_text of events.add) and kept for twelve months with the other events. It never holds the text.
  2. the text itself, only when there is one and it passes the filter below: ops/feedback/<YYYY-MM-DD>/<HHMMSS>-<rand>.json with the text, the chip, the place, the context code and the
     same classes, and NOTHING else. It is deleted after RETENTION_DAYS (90) days by the daily clean-up (events.purge_old -> purge_text), and the owner can delete one by hand
     (admin action feedback_delete).

WHAT IT NEVER HOLDS. No e-mail field (a text that holds an "@", a mail host, a telephone number or a link is NOT kept: the answer is counted, the text is dropped, and the visitor is told),
no name, no cookie, no visitor number, no address, no user agent. The box asks the visitor not to write personal details; the filter is the second line. Nothing about the photo.
Nobody gets a reply: it is a box, not a support channel (the page says where the support address is).

SPAM. A honeypot field (hp: a person never sees it), a robot's user agent (counter.ua_classes), a per-client limit (CLIENT_MAX answers in CLIENT_WINDOW seconds, a keyed hash of the
connection address held in this process's memory only, as the counter's), the per-instance budget of events.py (RATE["fb"], FB_DAY_MAX), the same text twice (DUP_KEPT hashes, in
memory), and the text filter (clean_text). Every refusal is silent: the request is always answered 200 {ok, counted, text}.

THE SWITCH. SNAPEYES_FEEDBACK (api/_lib/iris.py FEEDBACK_ON, read once at import, on by default): off, 0, false or no turns it off. Off, submit() keeps nothing and GET /api/health and
GET /api/checkout say feedback false, which is how /try knows not to show the box. It also needs somewhere to keep the answers and the daily clean-up that deletes them (on()).

Module rule: nothing heavy is imported at module level (events imports this file lazily from purge_old; iris and events are imported inside the functions that need them)."""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import threading
import time
import unicodedata

PLACES = ("result", "retake")
CHIPS = {
    "result": ("love", "likeness", "colour", "style", "price", "other"),        # I love it; it does not look like my eye; the colours look off; I wanted another style; the price is too high; something else
    "retake": ("unclear", "fine", "device", "only", "effort", "other"),         # I do not understand what is wrong; my photo is fine; my phone cannot do better; it is the only photo I have; too much effort; something else
}
TEXT_MAX = 300               # characters a text keeps (the page's own limit is the same)
PASTE_MAX = 900              # a text this long is a paste, not an answer: it is dropped as junk
RETENTION_DAYS = 90          # the privacy policy says the texts are deleted after this many days
FOLDER = "ops/feedback"
CLIENT_MAX = 4               # answers per client per CLIENT_WINDOW seconds
CLIENT_WINDOW = 600.0
CLIENTS_KEPT = 2000
DUP_KEPT = 300               # hashes of the last texts of this process (a flood of the same text is dropped)
WAIT = 1.2                   # seconds the event may take to be written
TEXT_TIMEOUT = 4.0           # the storage call of the text row
LIST_MAX = 100               # rows the admin page lists
READ_MAX = 40000             # bytes of one stored row that are read back

_KEY = os.urandom(16)        # the rate limit hash's key: made when the process starts, never stored
_LOCK = threading.Lock()
_CLIENTS: dict[str, list[float]] = {}
_DUPS: list[str] = []
_ID = re.compile(r"^[0-9]{8}-[0-9]{6}-[0-9a-f]{12}$")
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_NAME = re.compile(r"^[0-9]{6}-[0-9a-f]{12}[.]json$")

# the text filter (clean_text): contact details, links, markup and noise are not kept
_MAILHOST = re.compile(r"(gmail|googlemail|hotmail|outlook|yahoo|icloud|proton|gmx|t-online|freenet|mail[.]ru|yandex|abv[.]bg|inbox[.]lt|one[.]lt)", re.I)
_PHONE = re.compile(r"(?<![0-9A-Za-z])(?:[+]|00)?[0-9](?:[ ().-]?[0-9]){7,}")
_LINK = re.compile(r"(?:https?:|ftp:|www[.]|//)|[A-Za-z0-9-]+[.](?:com|net|org|info|biz|io|ru|cn|xyz|top|shop|site|online|club|link|click|lt|de|hu|eu|co|me|ly|app|dev|ee|lv|pl)(?![A-Za-z0-9])", re.I)
_MARKUP = re.compile(r"[<>{}]|&#?[A-Za-z0-9]+;|javascript:|union[ ]+select|select[ ]+.{1,40}[ ]+from", re.I)
_REPEAT = re.compile(r"(.)\1{7,}|\b(\w+)(?:[ ]+\2\b){5,}", re.I)


def on() -> bool:
    """Is the box on here? The switch (iris.FEEDBACK_ON, read once at import), somewhere to keep the answers and the daily clean-up that deletes them (events.retention_ok)."""
    try:
        from . import iris as L
        from . import events as E
        from . import store
        return bool(L.FEEDBACK_ON and store.configured() and E.retention_ok())
    except Exception:  # noqa
        return False


def clean_text(raw):
    """(the text to keep, why it was not kept) for what a page sent. ("", None) for no text. The text is normalised (NFC, control characters and runs of white space become one space) and
    cut to TEXT_MAX. It is NOT kept when it holds an "@", a mail host, a run of eight or more digits (a telephone number), a link, markup, nothing that is a letter, a character or a word
    repeated many times, or is longer than PASTE_MAX before the cut: why is contact, link or junk."""
    if raw is None or raw == "":
        return "", None
    if not isinstance(raw, str):
        return "", "junk"
    if len(raw) > PASTE_MAX:
        return "", "junk"
    t = unicodedata.normalize("NFC", raw)
    t = "".join(" " if (ch.isspace() or unicodedata.category(ch)[0] == "C") else ch for ch in t)
    t = re.sub(r"[ ]+", " ", t).strip()
    if not t:
        return "", None
    t = t[:TEXT_MAX].rstrip()
    if "@" in t or _MAILHOST.search(t) or _PHONE.search(t):
        return "", "contact"
    if _LINK.search(t):
        return "", "link"
    if _MARKUP.search(t) or not re.search(r"[^\W\d_]", t) or _REPEAT.search(t):
        return "", "junk"
    return t, None


def _tag(req) -> str:
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


def _duplicate(text) -> bool:
    """Has this process seen this text lately? The text is hashed (with the process key) and only the hash is kept, in memory."""
    h = hmac.new(_KEY, text.lower().encode("utf-8", "replace"), hashlib.sha256).hexdigest()[:16]
    with _LOCK:
        if h in _DUPS:
            return True
        _DUPS.append(h)
        del _DUPS[:-DUP_KEPT]
    return False


def row_path(now, rand=None):
    g = time.gmtime(now)
    return f"{FOLDER}/{time.strftime('%Y-%m-%d', g)}/{time.strftime('%H%M%S', g)}-{rand or secrets.token_hex(6)}.json"


def row_id(path) -> str | None:
    """The id of a stored row from its path ("20261020-123105-0123456789ab"), None for a path that is not one."""
    parts = path.split("/")
    if len(parts) != 4 or not _DAY.fullmatch(parts[2]) or not _NAME.fullmatch(parts[3]):
        return None
    return f"{parts[2].replace('-', '')}-{parts[3][:6]}-{parts[3][7:19]}"


def id_path(rid) -> str | None:
    """The path of a row from its id, None for an id that is not one."""
    if not isinstance(rid, str) or not _ID.fullmatch(rid):
        return None
    d, t, r = rid.split("-")
    return f"{FOLDER}/{d[:4]}-{d[4:6]}-{d[6:]}/{t}-{r}.json"


def submit(body):
    """POST /api/checkout {feedback: {w, c[, x, eyes, t, hp]}, camp, lang, market}: one answer of the feedback box. Always answered 200 {ok, counted, text}: counted is whether the answer
    was written, text is kept (the text was stored), none (no text came), dropped (it was not kept: it looked like contact details, a link or noise) or lost (storage did not take it).
    Counted only when the box is on, w and c are a place and one of its chips, the request does not look like a robot or fill the honeypot hp, and the client and the instance are under their
    limits. x (the style on screen, or the block reason) must be a short code. The text goes through clean_text."""
    from . import iris as L
    from . import events as E
    from . import counter as CN
    from . import store
    fb = body.get("feedback")
    if not isinstance(fb, dict):
        return {"ok": True, "counted": False}
    place, chip = fb.get("w"), fb.get("c")
    if place not in PLACES or chip not in CHIPS[place]:
        return {"ok": True, "counted": False}
    if not on():
        return {"ok": True, "counted": False, "on": False}
    ctx = L.ctx() or {}
    if ctx.get("bot") or fb.get("hp") not in (None, ""):
        return {"ok": True, "counted": False}
    now = time.time()
    if not _client_ok(ctx.get("tag"), now):
        return {"ok": True, "counted": False}
    f = CN.attach({"w": place, "c": chip}, ctx)
    x = fb.get("x")
    if CN.is_code(x):
        f["x"] = x
    eyes = fb.get("eyes")
    if isinstance(eyes, int) and not isinstance(eyes, bool) and 1 <= eyes <= 8:
        f["eyes"] = eyes
    text, why = clean_text(fb.get("t"))
    if text and _duplicate(text):
        text, why = "", "dup"
    if text:
        f["txt"] = "kept"
    elif why:
        f["txt"] = why
    counted = bool(E.record("fb", _wait=WAIT, **f))
    if not counted:
        return {"ok": True, "counted": False}
    if not text:
        return {"ok": True, "counted": True, "text": "dropped" if why else "none"}
    row = {"v": 1, "t": int(now), "w": place, "c": chip, "txt": text}
    for k in ("x", "eyes", "src", "med", "cmp", "trm", "cnt", "dev", "br", "cc", "lang", "market"):
        if f.get(k) is not None:
            row[k] = f[k]
    try:
        store.put(row_path(now), store.json_bytes(row), "application/json", upsert=False, timeout=TEXT_TIMEOUT, retry=False)
    except Exception:  # noqa: the answer is counted; only the text is lost
        return {"ok": True, "counted": True, "text": "lost"}
    return {"ok": True, "counted": True, "text": "kept"}


# ----------------------------------------------------------------------------- reading, deleting and the clean-up (the admin page, the daily clean-up)
def day_list(days, now=None):
    """The UTC days of the last `days` days, newest first."""
    now = time.time() if now is None else now
    return [time.strftime("%Y-%m-%d", time.gmtime(now - i * 86400)) for i in range(max(1, int(days)))]


def texts(days=RETENTION_DAYS, flt=None, limit=LIST_MAX, stop_left=6.0):
    """(rows, more): the stored texts of the last `days` days, newest first, at most `limit`; each is the row plus its id, day and time. flt keeps the rows whose src, cmp, dev, br and
    lang match what it names. more is True when the time ran out or there are more rows than the limit."""
    from . import iris as L
    from . import store
    flt = flt or {}
    out, more = [], False
    for day in day_list(min(int(days), RETENTION_DAYS)):
        if L.time_left() < stop_left:
            more = True
            break
        try:
            names = sorted((r["name"] for r in store.list_all(f"{FOLDER}/{day}") if not r["folder"] and _NAME.fullmatch(r["name"])), reverse=True)
        except Exception:  # noqa
            continue
        for name in names:
            if len(out) >= limit:
                return out, True
            if L.time_left() < stop_left:
                return out, True
            path = f"{FOLDER}/{day}/{name}"
            try:
                row = store.get_json(path, timeout=6.0)
            except Exception:  # noqa
                continue
            if not isinstance(row, dict) or not isinstance(row.get("txt"), str):
                continue
            if any(flt.get(k) and row.get(k) != flt[k] for k in ("src", "cmp", "dev", "br", "lang", "market")):
                continue
            rid = row_id(path)
            if rid:
                out.append(dict(row, id=rid, day=day, at=name[:6]))
    return out, more


def delete_text(rid) -> bool:
    """Delete one stored text by its id: True when it was there. A bad id is a ValueError."""
    from . import store
    path = id_path(rid)
    if path is None:
        raise ValueError("not a feedback id")
    if not store.exists(path, timeout=8.0):
        return False
    store.delete(path, timeout=8.0)
    return True


def purge_text(days=RETENTION_DAYS, yes=True, stop_left=10.0):
    """Delete the stored texts older than `days` days (the daily clean-up calls it from events.purge_old). Never raises. Returns {texts, days, more}."""
    from . import iris as L
    from . import store
    res = {"texts": 0, "days": 0, "more": False}
    try:
        if not store.configured():
            return res
        cut = time.strftime("%Y-%m-%d", time.gmtime(time.time() - max(1, int(days)) * 86400))
        for row in store.list_all(FOLDER):
            if not row["folder"] or not _DAY.fullmatch(row["name"]) or row["name"] >= cut:
                continue
            if L.time_left() < stop_left:
                res["more"] = True
                break
            names = [f"{FOLDER}/{row['name']}/{r['name']}" for r in store.list_all(f"{FOLDER}/{row['name']}") if not r["folder"]]
            if yes and names:
                store.delete_many(names)
            res["texts"] += len(names)
            res["days"] += 1
    except Exception:  # noqa: the clean-up goes on without this step
        res["more"] = True
    return res
