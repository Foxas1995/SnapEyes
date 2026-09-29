# -*- coding: utf-8 -*-
"""Small usage events for the owner's admin panel (/admin, api/admin.py, api/_lib/ops.py).

record(kind, **fields) stores ONE small JSON object per event in the private bucket (store.py):

    ops/events/<YYYY-MM-DD>/<HHMMSS>-<rand>.json      (UTC)

What an event may hold is fixed below (FIELDS): numbers, booleans and short lower-case codes only. No image, no text
a person typed, no name, no email, no IP address, no user agent, no signed link, no ticket. An order id only in an
order event ("master"). Any other field, or a value that is not of its type (a code with "@" or a space in it, say),
is dropped, so a caller cannot put personal data into an event by mistake.

Retention: the privacy policy says events and day counts are deleted after 12 months (and the admin panel's
failed-login markers, ops/adminfail/, after 2 days). Only purge_old() deletes them, and only the daily clean-up calls it
(vercel.json crons -> GET /api/order with CRON_SECRET -> api/_lib/cleanup.py). So nothing of this is written while
that clean-up cannot run here: retention_ok() (CRON_SECRET of 16 characters or more, the rule of /api/health "cron").

Best effort: it never raises, it is skipped entirely when storage is not configured, and a request waits at most
WAIT seconds (1.5) for the write (less when the invocation is near its deadline); a write that takes longer goes on
in the background or is lost. A per-instance ceiling (RATE) keeps a flood of bad requests from filling the bucket.

The kinds (all with "ms", the time since the request started, when known):
  analyze   ok, verdict (good/ok/weak/no_eye), detail, blocked, block_reason, locked, shake_asked, lang, device
            (ios/android/desktop/other/unknown), source (camera/gallery/live/sample/lab/other/unknown)
  deglare   glare_pct, lid_pct, changed, used_sr, model_call (the reflection call to the image model)
  enhance   mode, qa_ok, ring_de00, fallback, used_sr, fidelity
  compose   style, eyes, layout, format, clean (unwatermarked), qa_ok
  master    step (eye/compose), order, eye, count, needs_review, attempts, rerender, existing, render_s, style, lab
  error     endpoint, class (the error's kind: busy/400/403/429/500/502/503), reason (the reply's reason code),
            status. ("class", because "kind" names the event itself.)

The reading side (the admin panel) is here too: day_events() reads one day, summarize() turns events into counts,
rollup() stores a finished day's counts once (ops/daily/<YYYY-MM-DD>.json), purge_old() is the clean-up."""
import os, re, json, time, math, calendar, secrets, threading
from . import iris as L
from . import store

CRON_MIN = 16                # characters of CRON_SECRET (pay.ordering_problem and /api/health use the same rule)
WAIT = 1.5                   # seconds a request waits for its event to be written, at most
PUT_TIMEOUT = 1.2            # the storage call itself
RATE = {"all": (240, 60.0), "error": (30, 60.0)}   # events per instance per window (seconds)
ERROR_DAY_MAX = 1500         # error events per instance per UTC day
EVENTS = "ops/events"
DAILY = "ops/daily"
ADMINFAIL = "ops/adminfail"
ROLLUP_GRACE = 300           # a day is rolled up only this long after it ended (writes still on their way)
RECENT_ERRORS = 40           # error events kept one by one in a day's counts

_CODE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,39}$")
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_NAME = re.compile(r"^[0-9]{6}-[0-9a-f]{8,16}\.json$")

FIELDS = {
    "analyze": {"ok": "b", "verdict": "c", "detail": "n", "blocked": "b", "block_reason": "c", "locked": "b",
                "shake_asked": "b", "lang": "c", "device": "c", "source": "c"},
    "deglare": {"glare_pct": "n", "lid_pct": "n", "changed": "b", "used_sr": "b", "model_call": "b"},
    "enhance": {"mode": "c", "qa_ok": "b", "ring_de00": "n", "fallback": "b", "used_sr": "b", "fidelity": "n"},
    "compose": {"style": "c", "eyes": "n", "layout": "c", "format": "c", "clean": "b", "qa_ok": "b"},
    "master": {"step": "c", "order": "o", "eye": "n", "count": "n", "needs_review": "b", "attempts": "n",
               "rerender": "b", "existing": "b", "render_s": "n", "style": "c"},
    "error": {"endpoint": "c", "class": "c", "reason": "c", "status": "n"},
}
SOURCES = ("camera", "gallery", "live", "sample", "lab")


# ----------------------------------------------------------------------------- writing
_RATE_LOCK = threading.Lock()
_SEEN = {"all": [], "error": [], "day": "", "errors_today": 0}


def _allow(kind, now):
    """The per-instance ceiling: True when this event may be written."""
    with _RATE_LOCK:
        for name in (("all", "error") if kind == "error" else ("all",)):
            n, win = RATE[name]
            q = [t for t in _SEEN[name] if now - t < win]
            if len(q) >= n:
                _SEEN[name] = q
                return False
            _SEEN[name] = q
        if kind == "error":
            d = time.strftime("%Y-%m-%d", time.gmtime(now))
            if _SEEN["day"] != d:
                _SEEN["day"], _SEEN["errors_today"] = d, 0
            if _SEEN["errors_today"] >= ERROR_DAY_MAX:
                return False
            _SEEN["errors_today"] += 1
            _SEEN["error"].append(now)
        _SEEN["all"].append(now)
        return True


def _value(typ, v):
    """v as the field's type, or None (dropped)."""
    if typ == "b":
        return v if isinstance(v, bool) else None
    if typ == "n":
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        if not math.isfinite(v) or abs(v) > 1e9:
            return None
        return int(v) if isinstance(v, int) else round(float(v), 3)
    if typ == "c":
        return v if isinstance(v, str) and _CODE.fullmatch(v) else None
    if typ == "o":
        return v if isinstance(v, str) and store.ORDER_RE.fullmatch(v) else None
    return None


def elapsed_ms():
    """Milliseconds since the request started (iris.run sets the deadline), or None outside a request."""
    d = L.deadline()
    if d <= 0:
        return None
    return int(max(0.0, time.time() - (d - L.BUDGET)) * 1000)


def build(kind, fields, now=None):
    """The event object as it is stored (or None for an unknown kind). Only the fields FIELDS allows, each of its type."""
    spec = FIELDS.get(kind)
    if spec is None:
        return None
    now = time.time() if now is None else now
    ev = {"v": 1, "kind": kind, "t": round(now, 3)}
    ms = fields.get("ms")
    ms = _value("n", ms) if ms is not None else elapsed_ms()
    if ms is not None:
        ev["ms"] = ms
    for k, typ in spec.items():
        if k in fields:
            x = _value(typ, fields[k])
            if x is not None:
                ev[k] = x
    if kind == "master" and isinstance(ev.get("order"), str):
        ev["lab"] = ev["order"].startswith("lab-")
    return ev


def event_path(now):
    g = time.gmtime(now)
    return f"{EVENTS}/{time.strftime('%Y-%m-%d', g)}/{time.strftime('%H%M%S', g)}-{secrets.token_hex(6)}.json"


def _put(path, data, box):
    try:
        store.ensure_private(timeout=PUT_TIMEOUT, retry=False)
        store.put(path, data, "application/json", upsert=False, timeout=PUT_TIMEOUT, retry=False)
        box["ok"] = True
    except Exception as e:  # noqa: an event must never cost a request
        box["error"] = type(e).__name__


def retention_ok():
    """Can the daily clean-up run on this deployment (CRON_SECRET set), so what is written here is deleted on time?"""
    try:
        return len(store._clean(os.environ.get("CRON_SECRET"))) >= CRON_MIN
    except Exception:  # noqa
        return False


def record(kind, **fields):
    """Store one event (see the module text). True when it was written in time; never raises. Skipped (False) while
    storage is not configured or the daily clean-up cannot run here (retention_ok)."""
    try:
        if kind not in FIELDS or not store.configured() or not retention_ok():
            return False
        now = time.time()
        wait = min(WAIT, L.time_left() - 1.0)
        if wait < 0.2 or not _allow(kind, now):
            return False
        ev = build(kind, fields, now)
        box = {}
        th = threading.Thread(target=_put, args=(event_path(now), store.json_bytes(ev), box), daemon=True)
        th.start()
        th.join(wait)
        return bool(box.get("ok"))
    except Exception:  # noqa
        return False


def device_class(device):
    """The kind of device a capture came from, from the telemetry's user agent (the user agent itself is not kept)."""
    try:
        ua = str(device.get("ua") or "") if isinstance(device, dict) else ""
        if not ua:
            return "unknown"
        if re.search(r"iPhone|iPad|iPod", ua):
            return "ios"
        if "Android" in ua:
            return "android"
        if re.search(r"Windows|Macintosh|X11|Linux|CrOS", ua):
            return "desktop"
        return "other"
    except Exception:  # noqa
        return "unknown"


def device_source(device):
    s = device.get("source") if isinstance(device, dict) else None
    return s if s in SOURCES else ("other" if s else "unknown")


def error(req, kind, reason=None, status=None):
    """The error event of one reply (iris.run calls it): the endpoint from the request path, the error class, the
    reply's reason code. No message text."""
    try:
        m = re.match(r"^/api/([a-z_]{1,24})(?:[/?]|$)", str(getattr(req, "path", "") or ""))
        endpoint = m.group(1) if m else "other"
        if status is None:
            status = 503 if kind == "busy" else (int(kind) if str(kind).isdigit() else None)
        return record("error", endpoint=endpoint, reason=reason, status=status, **{"class": str(kind)})
    except Exception:  # noqa
        return False


def answer(req, out):
    """After L.run sent an endpoint's own refusal (a store.Answer through a _StatusReq box, which carries .status):
    an error event for 5xx, 403 and 429 replies. The ordinary steps of the order flow (402 confirming, 409
    rendering, 410 ...) are not errors."""
    try:
        st = getattr(req, "status", None)
        if not isinstance(st, int) or isinstance(st, bool) or st < 400 or not (st >= 500 or st in (403, 429)):
            return False
        reason = out.get("reason") if isinstance(out, dict) else None
        return error(req, "busy" if reason == "model_busy" else str(st), reason, st)
    except Exception:  # noqa
        return False


# ----------------------------------------------------------------------------- reading (the admin panel)
def day_names(day):
    """The event files of one UTC day (YYYY-MM-DD), oldest first."""
    if not _DAY.fullmatch(day):
        return []
    return [r["name"] for r in store.list_all(f"{EVENTS}/{day}") if not r["folder"] and _NAME.fullmatch(r["name"])]


def read_event(day, name):
    ev = store.get_json(f"{EVENTS}/{day}/{name}", timeout=8.0)
    return ev if isinstance(ev, dict) and ev.get("kind") in FIELDS else None


def empty():
    return {"events": 0, "kinds": {}, "verdict": {}, "block_reason": {}, "blocked": 0, "locked": 0, "unlocked": 0,
            "device": {}, "source": {}, "lang": {}, "enhance_qa_fail": 0, "enhance_fallback": 0, "deglare_glare": 0,
            "deglare_lid": 0, "compose_style": {}, "compose_eyes": {}, "compose_clean": 0, "master_eye": 0,
            "master_compose": 0, "master_review": 0, "master_rerender": 0, "master_lab": 0, "master_existing": 0,
            "errors": {}, "error_endpoint": {}, "error_reason": {}, "busy": 0,
            "gemini": {"vision": 0, "image_1k": 0, "image_4k": 0}, "ms": {}, "recent_errors": []}


def _inc(d, k, n=1):
    k = str(k)
    d[k] = d.get(k, 0) + n


def _ms(agg, step, ev):
    v = ev.get("ms")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
        s = agg["ms"].setdefault(step, [0, 0])
        s[0] += v
        s[1] += 1


def add(agg, ev):
    """Count one event into agg (from empty())."""
    kind = ev.get("kind")
    if kind not in FIELDS:
        return agg
    agg["events"] += 1
    _inc(agg["kinds"], kind)
    g = agg["gemini"]
    if kind == "analyze":
        _inc(agg["verdict"], ev.get("verdict") or ("ok" if ev.get("ok", True) else "no_eye"))
        if ev.get("blocked"):
            agg["blocked"] += 1
            _inc(agg["block_reason"], ev.get("block_reason") or "unknown")
        if ev.get("locked") is True:
            agg["locked"] += 1
        elif ev.get("locked") is False:
            agg["unlocked"] += 1
        _inc(agg["device"], ev.get("device") or "unknown")
        _inc(agg["source"], ev.get("source") or "unknown")
        _inc(agg["lang"], ev.get("lang") or "en")
        g["vision"] += 1 + (1 if ev.get("shake_asked") else 0)
        _ms(agg, "analyze", ev)
    elif kind == "deglare":
        if (ev.get("glare_pct") or 0) > 0:
            agg["deglare_glare"] += 1
        if (ev.get("lid_pct") or 0) > 0:
            agg["deglare_lid"] += 1
        g["image_1k"] += 1 if ev.get("model_call") else 0
        _ms(agg, "deglare", ev)
    elif kind == "enhance":
        if ev.get("qa_ok") is False:
            agg["enhance_qa_fail"] += 1
        if ev.get("fallback"):
            agg["enhance_fallback"] += 1
        g["image_1k"] += 1
        _ms(agg, "enhance", ev)
    elif kind == "compose":
        _inc(agg["compose_style"], ev.get("style") or "unknown")
        _inc(agg["compose_eyes"], ev.get("eyes") or 1)
        if ev.get("clean"):
            agg["compose_clean"] += 1
        _ms(agg, "compose", ev)
    elif kind == "master":
        step = "master_compose" if ev.get("step") == "compose" else "master_eye"
        if ev.get("existing"):
            agg["master_existing"] += 1
        else:
            agg[step] += 1
            _ms(agg, step, ev)
            if step == "master_eye":
                a = ev.get("attempts")
                g["image_4k"] += int(a) if isinstance(a, (int, float)) and not isinstance(a, bool) and 0 < a < 10 else 1
        if ev.get("needs_review"):
            agg["master_review"] += 1
        if ev.get("rerender"):
            agg["master_rerender"] += 1
        if ev.get("lab"):
            agg["master_lab"] += 1
    elif kind == "error":
        k = ev.get("class") or "unknown"
        _inc(agg["errors"], k)
        _inc(agg["error_endpoint"], ev.get("endpoint") or "other")
        if ev.get("reason"):
            _inc(agg["error_reason"], ev["reason"])
        if k == "busy":
            agg["busy"] += 1
        row = {x: ev.get(x) for x in ("t", "endpoint", "reason", "status", "ms") if ev.get(x) is not None}
        row["kind"] = k
        agg["recent_errors"] = sorted(agg["recent_errors"] + [row], key=lambda r: -(r.get("t") or 0))[:RECENT_ERRORS]
    return agg


def summarize(events):
    agg = empty()
    for ev in events:
        if isinstance(ev, dict):
            add(agg, ev)
    return agg


def merge(a, b):
    """a + b of two summaries (numbers add, count tables add, the recent errors are merged, newest first)."""
    out = empty()
    for src in (a, b):
        for k, v in (src or {}).items():
            if k == "recent_errors":
                out[k] = sorted(out[k] + list(v or []), key=lambda r: -(r.get("t") or 0))[:RECENT_ERRORS]
            elif k == "ms":
                for step, (s, n) in (v or {}).items():
                    cur = out["ms"].setdefault(step, [0, 0])
                    cur[0] += s
                    cur[1] += n
            elif isinstance(v, dict):
                d = out.setdefault(k, {})
                for kk, vv in v.items():
                    if isinstance(vv, (int, float)) and not isinstance(vv, bool):
                        d[kk] = d.get(kk, 0) + vv
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                out[k] = out.get(k, 0) + v
    return out


def rollup_path(day):
    return f"{DAILY}/{day}.json"


def get_rollup(day):
    raw = store.get(rollup_path(day), max_bytes=512 << 10, timeout=8.0)
    if raw is None:
        return None
    try:
        agg = json.loads(raw)
    except ValueError:
        return None
    return agg if isinstance(agg, dict) and agg.get("v") == 1 else None


def day_finished(day, now=None):
    """Has this UTC day ended (plus ROLLUP_GRACE), so its counts will not change any more?"""
    try:
        start = calendar.timegm(time.strptime(day, "%Y-%m-%d"))
    except (ValueError, OverflowError):
        return False
    now = time.time() if now is None else now
    return now >= start + 86400 + ROLLUP_GRACE


def put_rollup(day, agg):
    """Store a finished day's counts (once; they do not change any more)."""
    try:
        store.put(rollup_path(day), store.json_bytes(dict(agg, v=1, day=day, t=int(time.time()))), "application/json",
                  upsert=True, timeout=8.0)
        return True
    except store.StorageError:
        return False


# ----------------------------------------------------------------------------- clean-up
def purge_old(days=365, yes=True, stop_left=10.0, out=None):
    """Delete events and day counts older than `days` days, and the admin panel's failed-login markers older than 2
    days. For the daily clean-up (api/_lib/cleanup.py may call it). Never raises; stops for time with more: true.
    Returns {ok, events, days, rollups, adminfail, more}."""
    res = {"ok": True, "events": 0, "days": 0, "rollups": 0, "adminfail": 0, "more": False}
    say = out or (lambda m: print("snapeyes events: " + str(m)[:300], flush=True))
    try:
        if not store.configured():
            return dict(res, skipped="storage_not_configured")
        days = max(1, int(days))
        cut = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))
        for row in store.list_all(EVENTS):
            if not row["folder"] or not _DAY.fullmatch(row["name"]) or row["name"] >= cut:
                continue
            if L.time_left() < stop_left:
                res["more"] = True
                break
            names = [f"{EVENTS}/{row['name']}/{r['name']}" for r in store.list_all(f"{EVENTS}/{row['name']}")
                     if not r["folder"]]
            if yes and names:
                store.delete_many(names)
            res["events"] += len(names)
            res["days"] += 1
        if not res["more"]:
            old = [f"{DAILY}/{r['name']}" for r in store.list_all(DAILY)
                   if not r["folder"] and r["name"].endswith(".json") and r["name"][:-5] < cut]
            if yes and old:
                store.delete_many(old)
            res["rollups"] = len(old)
        if not res["more"]:
            hour_cut = time.strftime("%y%m%d%H", time.gmtime(time.time() - 2 * 86400))
            for row in store.list_all(ADMINFAIL):
                if not row["folder"] or not re.fullmatch(r"[0-9]{8}", row["name"]) or row["name"] >= hour_cut:
                    continue
                if L.time_left() < stop_left:
                    res["more"] = True
                    break
                names = [f"{ADMINFAIL}/{row['name']}/{r['name']}" for r in store.list_all(f"{ADMINFAIL}/{row['name']}")
                         if not r["folder"]]
                if yes and names:
                    store.delete_many(names)
                res["adminfail"] += len(names)
        say(f"purge_old{'' if yes else ' (dry run)'}: {res}")
    except Exception as e:  # noqa: the clean-up must go on without this step
        res.update(ok=False, error=type(e).__name__)
        say(f"purge_old failed: {type(e).__name__}")
    return res
