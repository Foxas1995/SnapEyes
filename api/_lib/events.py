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
  enhance   mode, qa_ok, ring_de00, fallback, used_sr, fidelity; and the eye profile (api/_lib/styles/eye.py): gate (ok, lid, fill,
            both, or unknown when the profile was not measured), reason (the first reason code of a failure, else none), cls (the
            colour class: own, dark_brown, grey), pupil (round, slit, bar), profile_ms (the time it took); and the Reveal
            (api/_lib/styles/reveal.py, WP9): reveal (ok: the page shows the cut; colour or registration: withheld, the page shows the strip
            without the cut; none: not measured, no time left; error), reveal_ms (the time it took, when measured)
  compose   style, eyes, layout, format, clean (unwatermarked), qa_ok; gate: the SET-level result of the request under the style's
            gate rule (ok, unknown, or the first failing eye's reason code); and, from the compose API v3 (api/compose.py, WP10): size (the
            preview's long side, 1024 or 480), tile (this event is one tile of a batch, not a preview the customer asked for), tiles (on the
            FIRST event of a request only: how many tiles the request makes, so a request is counted once whatever its tiles), look (the
            Universe look), pick (the style is the recommended tile), fallback (what the geometry fell back to: kiss, stack_contrast, ...),
            stage (the effective stage of the style asked: live or preview, so that the demand for a Soon style is counted), retake (how
            many eyes of the set the page replaced since its last compose), lang and market (page language, price market), ms (a tile: its
            own render time), cls (the set's colour class: own, dark_brown, grey). tiles 0 is a request that judged
            a set of eyes and drew nothing for it (the tile list alone, a batch whose tiles the gate held back, a style or a pick the eyes cannot
            take): it carries the set level fields (gate, eyes, cls, retake, lang, market) and reaches the gate funnel and nothing else.
            again (WP13a: this request asks about a set of eyes the page has already asked about, the second request of a pick and a
            batch for example; absent means a new set): the gate funnel counts a set once, by its first request, so a passing set that is
            asked about twice is not worth two sets
  master    step (eye/compose/art), order, eye, count, needs_review, attempts, rerender, existing, render_s, style, lab; and, from the master plan's steps
            (api/_lib/styles/steps.py: one event per step, "art" for the artwork): part and of (the step and how many the plan has), ms (the step's
            wall time), need_s (the estimate it was planned with), cpu_s, peak_mb (the INCREASE of the process's resident size over the step, VmRSS) and
            hwm_mb (the instance's own high-water mark, labelled as that: it never falls on a warm instance), kills (the killed attempts of the step),
            design (the design drawn), d_rgb (how far the master's ring colour drifted from the preview's, levels), hold (a code: the order was held
            instead of made: style_step_too_big, engine_skew, class_changed, style_step_failed, plate_unavailable, ...)
  error     endpoint, class (the error's kind: busy/400/403/429/500/502/503), reason (the reply's reason code),
            status. ("class", because "kind" names the event itself.) style: the style the refused request asked for, when it said.
  help      route (manual: the customer chose to send photos by e-mail for the owner to look at, see 1.6.2; soon: the customer pressed the buy
            button of a style that opens soon; blocked: the checkout refused a style that cannot be bought (409 style_unavailable), WP12), eyes,
            why (the reason code the retake state showed), lang, style (soon and blocked: the style): a count of clicks, nothing else
            (api/compose.py action help)
  exp       a price experiment's funnel (api/_lib/abtest.py; only while the owner has one running): stage (visit,
            preview, checkout, paid), exp (the experiment's key), variant, market, eyes, amount and currency (checkout
            and paid), hit (the artwork's price differs between the variants), live (paid: a real payment). No visitor
            id and no order number: the counts per variant are all it can give

The reading side (the admin panel) is here too: day_events() reads one day, summarize() turns events into counts,
rollup() stores a finished day's counts once (ops/daily/<YYYY-MM-DD>.json), purge_old() is the clean-up."""
import os, re, json, time, math, calendar, secrets, threading
from . import iris as L
from . import store

CRON_MIN = 16                # characters of CRON_SECRET (pay.ordering_problem and /api/health use the same rule)
WAIT = 1.5                   # seconds a request waits for its event to be written, at most
PUT_TIMEOUT = 1.2            # the storage call itself
RATE = {"all": (240, 60.0), "error": (30, 60.0), "exp": (60, 60.0), "help": (20, 60.0)}   # events per instance per window (seconds)
HELP_DAY_MAX = 1000          # help beacons per instance per UTC day (anybody can send one without an order, so they are capped like the price test's)
ERROR_DAY_MAX = 1500         # error events per instance per UTC day
EXP_DAY_MAX = 5000           # price-test visit and preview beacons per instance per UTC day (they need no order, so they are capped)
EVENTS = "ops/events"
DAILY = "ops/daily"
ADMINFAIL = "ops/adminfail"
ROLLUP_GRACE = 300           # a day is rolled up only this long after it ended (writes still on their way)
ROLLUP_MAX_BYTES = 2 << 20   # a stored day is read back with this ceiling (the day's counts are about 20 KB for a quiet day, 400 KB for a stress test of every combination)
RECENT_ERRORS = 40           # error events kept one by one in a day's counts

_CODE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,39}$")
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_NAME = re.compile(r"^[0-9]{6}-[0-9a-f]{8,16}\.json$")

FIELDS = {
    "analyze": {"ok": "b", "verdict": "c", "detail": "n", "blocked": "b", "block_reason": "c", "locked": "b",
                "shake_asked": "b", "lang": "c", "device": "c", "source": "c"},
    "deglare": {"glare_pct": "n", "lid_pct": "n", "changed": "b", "used_sr": "b", "model_call": "b"},
    "enhance": {"mode": "c", "qa_ok": "b", "ring_de00": "n", "fallback": "b", "used_sr": "b", "fidelity": "n",
                "gate": "c", "reason": "c", "cls": "c", "pupil": "c", "profile_ms": "n", "reveal": "c", "reveal_ms": "n"},
    "compose": {"style": "c", "eyes": "n", "layout": "c", "format": "c", "clean": "b", "qa_ok": "b", "gate": "c",
                "size": "n", "tiles": "n", "tile": "b", "look": "c", "pick": "b", "fallback": "c", "stage": "c", "retake": "n",
                "lang": "c", "market": "c", "cls": "c", "again": "b"},
    "master": {"step": "c", "order": "o", "eye": "n", "count": "n", "needs_review": "b", "attempts": "n",
               "rerender": "b", "existing": "b", "render_s": "n", "style": "c",
               "part": "n", "of": "n", "need_s": "n", "cpu_s": "n", "peak_mb": "n", "hwm_mb": "n", "kills": "n", "design": "c", "d_rgb": "n",
               "hold": "c", "fallback": "c"},
    "error": {"endpoint": "c", "class": "c", "reason": "c", "status": "n", "style": "c"},
    "help": {"route": "c", "eyes": "n", "why": "c", "lang": "c", "style": "c"},
    "exp": {"stage": "c", "exp": "c", "variant": "c", "market": "c", "eyes": "n", "amount": "n", "currency": "c",
            "hit": "b", "live": "b"},
}
EXP_STAGES = ("visit", "preview", "checkout", "paid")
SOURCES = ("camera", "gallery", "live", "sample", "lab")


# ----------------------------------------------------------------------------- writing
_RATE_LOCK = threading.Lock()
_SEEN = {"all": [], "error": [], "exp": [], "help": [], "day": "", "errors_today": 0, "exp_day": "", "exp_today": 0, "help_day": "", "help_today": 0}


def _allow(kind, now, stage=None):
    """The per-instance ceiling: True when this event may be written. A price test's visit and preview beacons (the only
    events anybody can send without an order) have a small budget of their own, per minute and per day, so a flood of them
    can neither fill the bucket nor use up the ceiling of the ordinary events. The test's paid events follow a real payment
    and are never held back."""
    if kind == "exp" and stage == "paid":
        return True
    with _RATE_LOCK:
        if kind == "exp" and stage in ("visit", "preview"):
            n, win = RATE.get("exp", (60, 60.0))
            q = [t for t in _SEEN["exp"] if now - t < win]
            _SEEN["exp"] = q
            d = time.strftime("%Y-%m-%d", time.gmtime(now))
            if _SEEN["exp_day"] != d:
                _SEEN["exp_day"], _SEEN["exp_today"] = d, 0
            if len(q) >= n or _SEEN["exp_today"] >= EXP_DAY_MAX:
                return False
            _SEEN["exp_today"] += 1
            q.append(now)
            return True
        if kind == "help":                  # a click on the manual route: no order behind it, so a small budget of its own (as the price test's beacons)
            n, win = RATE["help"]
            q = [t for t in _SEEN["help"] if now - t < win]
            _SEEN["help"] = q
            d = time.strftime("%Y-%m-%d", time.gmtime(now))
            if _SEEN["help_day"] != d:
                _SEEN["help_day"], _SEEN["help_today"] = d, 0
            if len(q) >= n or _SEEN["help_today"] >= HELP_DAY_MAX:
                return False
            _SEEN["help_today"] += 1
            q.append(now)
            return True
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
        cap = fields.pop("_wait", None)       # a caller that must not hold its request long (the price test's beacons)
        if kind not in FIELDS or not store.configured() or not retention_ok():
            return False
        now = time.time()
        wait = min(WAIT if not isinstance(cap, (int, float)) or isinstance(cap, bool) else float(cap), L.time_left() - 1.0)
        if wait < 0.2 or not _allow(kind, now, fields.get("stage") if isinstance(fields.get("stage"), str) else None):
            return False
        ev = build(kind, fields, now)
        box = {}
        th = threading.Thread(target=_put, args=(event_path(now), store.json_bytes(ev), box), daemon=True)
        th.start()
        th.join(wait)
        return bool(box.get("ok"))
    except Exception:  # noqa
        return False


def record_many(kind, rows, _wait=None):
    """Store several events of one kind (the tiles of one batch) at once and wait for all of them together, not one after the other: a batch of six
    tiles must not spend six storage round trips of its own time on its counts. rows: a list of field dicts, as record() takes them. The same rules as
    record(): nothing is written without storage or the clean-up, the per-instance ceiling counts every event, a field outside FIELDS is dropped.
    Returns how many were written in time; never raises."""
    try:
        if kind not in FIELDS or not rows or not store.configured() or not retention_ok():
            return 0
        now = time.time()
        cap = WAIT if not isinstance(_wait, (int, float)) or isinstance(_wait, bool) else float(_wait)
        wait = min(cap, L.time_left() - 1.0)
        if wait < 0.2:
            return 0
        started = []
        for fields in rows:
            if not _allow(kind, now, fields.get("stage") if isinstance(fields.get("stage"), str) else None):
                break
            box = {}
            th = threading.Thread(target=_put, args=(event_path(now), store.json_bytes(build(kind, dict(fields), now)), box), daemon=True)
            th.start()
            started.append((th, box))
        end = time.time() + wait
        for th, _ in started:
            th.join(max(0.0, end - time.time()))
        return sum(1 for _, box in started if box.get("ok"))
    except Exception:  # noqa
        return 0


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


def error(req, kind, reason=None, status=None, style=None):
    """The error event of one reply (iris.run calls it): the endpoint from the request path, the error class, the
    reply's reason code and, when the reply says which style was asked for, that style's id. No message text."""
    try:
        m = re.match(r"^/api/([a-z_]{1,24})(?:[/?]|$)", str(getattr(req, "path", "") or ""))
        endpoint = m.group(1) if m else "other"
        if status is None:
            status = 503 if kind == "busy" else (int(kind) if str(kind).isdigit() else None)
        return record("error", endpoint=endpoint, reason=reason, status=status, style=style, **{"class": str(kind)})
    except Exception:  # noqa
        return False


def answer(req, out):
    """After L.run sent an endpoint's own refusal (a store.Answer through a _StatusReq box, which carries .status):
    an error event for 5xx, 403 and 429 replies. The ordinary steps of the order flow (402 confirming, 409
    rendering, 410 ...) are not errors. One 409 is demand and not an error: a checkout that refused a style that cannot be
    bought (409 style_unavailable: it opens soon, it was taken back, its gate failed) is a help event with route blocked, the style
    and the eye count the reply names (WP13a: the owner sees the demand for a style before it can be bought)."""
    try:
        st = getattr(req, "status", None)
        reason = out.get("reason") if isinstance(out, dict) else None
        if st == 409 and reason == "style_unavailable":
            return record("help", route="blocked", style=out.get("style"), eyes=out.get("eyes"), why=out.get("why"), _wait=0.5)
        if not isinstance(st, int) or isinstance(st, bool) or st < 400 or not (st >= 500 or st in (403, 429)):
            return False
        return error(req, "busy" if reason == "model_busy" else str(st), reason, st, style=out.get("style") if isinstance(out, dict) else None)
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
            "deglare_lid": 0, "compose_style": {}, "compose_eyes": {}, "compose_clean": 0,
            # the compose API v3 (WP10): tiles are counted apart from the previews the customer asked for (compose_style and compose_eyes count the
            # previews only, as before); a request is counted once (compose_gate, compose_funnel, compose_lang, compose_market, compose_tiles: the
            # event that carries "tiles"); compose_demand "<style>|<eyes>|<stage>|<tile or large>" counts what was looked at, so a Soon style's demand
            # shows; compose_funnel "<eyes>|<set gate code>|<retakes 0, 1 or 2 for two or more>" is the set level gate funnel; compose_chosen counts the
            # previews of the recommended tile against the others; compose_funnel_cls "<eyes>|<colour class>|<set gate code>|<retakes>" is the same
            # funnel by the set's colour class (grey, dark_brown, own); a request that judged a set and drew nothing (tiles 0) is counted in the
            # funnel, the gate, lang, market and compose_tiles (key 0) and in nothing that is about a picture
            "compose_tile_style": {}, "compose_tile_eyes": {}, "compose_demand": {}, "compose_size": {}, "compose_look": {}, "compose_fallback": {},
            "compose_chosen": {}, "compose_funnel": {}, "compose_funnel_cls": {}, "compose_lang": {}, "compose_market": {}, "compose_tiles": {},
            "help_route": {}, "help_why": {}, "help_eyes": {}, "error_style": {},
            # the Stiliai page (WP13a): a set is counted once, by its first request (an event with again is left out of every set level table);
            # compose_slice "<lang:xx or market:xx>|<table>|<key>" repeats the tables the page filters by language and by market (compose_funnel,
            # compose_demand of the styles that are Soon, compose_chosen, compose_style, compose_tile_style, compose_fallback, compose_tiles) so that a filter
            # needs no raw event (the funnel by colour class and the demand for live styles are not sliced: the size of a day's counts); ms_hist
            # "<tile, compose or art>|<style>|<eyes>|<bucket>" counts render times in the buckets of HIST_MS (a p50 and a p95 need the spread, a sum and a count
            # give only a mean); master_review_style is the artworks that were held for a look, by style; help_demand "<soon or blocked>|<style>|<eyes>" is
            # the demand for a style that cannot be bought yet
            "compose_slice": {}, "ms_hist": {}, "master_review_style": {}, "help_demand": {},
            # the restoration gate (eye profile): per eye at enhance, per request at compose; the colour and pupil classes seen
            "enhance_gate": {}, "enhance_reason": {}, "enhance_class": {}, "enhance_pupil": {}, "compose_gate": {}, "master_eye": 0,
            # the Reveal (WP9): per eye at enhance, the code of what the page shows (ok, colour, registration, none, error)
            "enhance_reveal": {},
            "master_compose": 0, "master_review": 0, "master_rerender": 0, "master_lab": 0, "master_existing": 0,
            # the master plan's steps (kind master, step art): steps made, by style; orders held instead of made, by code (sums of peak_mb and need_s
            # are in "ms" as art_peak_mb and art_need_s with their counts, so averages need no new shape)
            "master_art": 0, "master_art_style": {}, "master_hold": {},
            # ... and the fallback a pair was made with (overlap_fallback: the Kiss geometry for a wide pupil; stack_contrast: the stacked lens, WP7B), by code
            "master_fallback": {},
            "errors": {}, "error_endpoint": {}, "error_reason": {}, "busy": 0,
            "gemini": {"vision": 0, "image_1k": 0, "image_4k": 0}, "ms": {}, "recent_errors": [],
            # price experiments (kind "exp"): "<experiment>|<variant>|<stage>" -> events (exp_stage; exp_hit counts only the
            # events whose artwork's price differs between the variants; stage "paid_test" is a Stripe test payment) and
            # "<experiment>|<variant>|<currency>" -> the paid amounts in the smallest unit (exp_rev; exp_rev_hit the affected ones)
            "exp_stage": {}, "exp_hit": {}, "exp_rev": {}, "exp_rev_hit": {}}


def _inc(d, k, n=1):
    k = str(k)
    d[k] = d.get(k, 0) + n


def _ms(agg, step, ev):
    v = ev.get("ms")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
        s = agg["ms"].setdefault(step, [0, 0])
        s[0] += v
        s[1] += 1


def _undrawn(ev):
    """Is this compose event a request that judged a set of eyes and drew nothing for it (tiles 0)? It is a set seen, not a picture."""
    t = ev.get("tiles")
    return isinstance(t, (int, float)) and not isinstance(t, bool) and t == 0


HIST_MS = (250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 12000, 16000, 24000, 32000, 48000, 64000)    # upper bounds, ms; one more bucket above
SLICE_FIELDS = (("lang", "lang"), ("market", "market"))


def hist_bucket(ms):
    """The bucket (an index into HIST_MS, len(HIST_MS) for above the last bound) a time in milliseconds falls in."""
    for i, ub in enumerate(HIST_MS):
        if ms <= ub:
            return i
    return len(HIST_MS)


def _hist(agg, what, style, eyes, ms):
    if style and isinstance(ms, (int, float)) and not isinstance(ms, bool) and ms >= 0:
        _inc(agg["ms_hist"], f"{what}|{style}|{eyes}|{hist_bucket(ms)}")


def _cinc(agg, ev, table, key, n=1):
    """Count into a table and, for the Stiliai page's filters, into the slices of the event's language and market (compose_slice)."""
    _inc(agg[table], key, n)
    for field, dim in SLICE_FIELDS:
        v = ev.get(field)
        if isinstance(v, str) and v:
            _inc(agg["compose_slice"], f"{dim}:{v}|{table}|{key}", n)


def _set_counts(agg, ev, eyes):
    """What a compose request says of the SET of eyes (never of a picture): the set level gate, the funnel by eye count, gate code and retakes, the same
    by the set's colour class, the page's language and the price market."""
    if ev.get("gate") and ev.get("again") is not True:       # a set is counted once, by its first request (again: the page has asked about these eyes already)
        _inc(agg["compose_gate"], ev["gate"])
        retake = ev.get("retake")
        retake = int(retake) if isinstance(retake, (int, float)) and not isinstance(retake, bool) and retake > 0 else 0
        _cinc(agg, ev, "compose_funnel", f"{eyes}|{ev['gate']}|{min(2, retake)}")
        if ev.get("cls"):
            _inc(agg["compose_funnel_cls"], f"{eyes}|{ev['cls']}|{ev['gate']}|{min(2, retake)}")      # not sliced: class by language by market is too many cells
    for field, key in (("lang", "compose_lang"), ("market", "compose_market")):
        if ev.get(field):
            _inc(agg[key], ev[field])


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
        for field, key in (("gate", "enhance_gate"), ("cls", "enhance_class"), ("pupil", "enhance_pupil")):
            if ev.get(field):
                _inc(agg[key], ev[field])
        if ev.get("reason") and ev["reason"] != "none":
            _inc(agg["enhance_reason"], ev["reason"])
        pm = ev.get("profile_ms")
        if isinstance(pm, (int, float)) and not isinstance(pm, bool) and pm >= 0:
            cur = agg["ms"].setdefault("profile", [0, 0])
            cur[0] += pm
            cur[1] += 1
        if ev.get("reveal"):
            _inc(agg["enhance_reveal"], ev["reveal"])
        rm = ev.get("reveal_ms")
        if isinstance(rm, (int, float)) and not isinstance(rm, bool) and rm >= 0:
            cur = agg["ms"].setdefault("reveal", [0, 0])
            cur[0] += rm
            cur[1] += 1
    elif kind == "compose" and _undrawn(ev):
        _set_counts(agg, ev, ev.get("eyes") or 1)
        _cinc(agg, ev, "compose_tiles", 0)
    elif kind == "compose":
        tile = ev.get("tile") is True
        request = (not tile) or ev.get("tiles") is not None       # a request is counted once: by its first event when it is a batch of tiles
        style, eyes = ev.get("style") or "unknown", ev.get("eyes") or 1
        _cinc(agg, ev, "compose_tile_style" if tile else "compose_style", style)
        _inc(agg["compose_tile_eyes" if tile else "compose_eyes"], eyes)
        if ev.get("stage"):
            key = f"{style}|{eyes}|{ev['stage']}|{'tile' if tile else 'large'}"
            if ev["stage"] == "preview":         # the demand for a style that is Soon is what the page filters by language and market; a live style's is not sliced (size)
                _cinc(agg, ev, "compose_demand", key)
            else:
                _inc(agg["compose_demand"], key)
        if ev.get("size"):
            _inc(agg["compose_size"], ev["size"])
        if ev.get("look"):
            _inc(agg["compose_look"], f"{style}|{ev['look']}")
        if ev.get("fallback") and ev["fallback"] != "none":
            _cinc(agg, ev, "compose_fallback", f"{style}|{ev['fallback']}")
        if not tile and ev.get("pick") is not None:
            _cinc(agg, ev, "compose_chosen", "pick" if ev["pick"] else "other")
        if request:
            _set_counts(agg, ev, eyes)
            if ev.get("clean"):
                agg["compose_clean"] += 1
            if ev.get("tiles") is not None:
                _cinc(agg, ev, "compose_tiles", ev["tiles"])
        _ms(agg, "compose_tile" if tile else "compose", ev)
        _hist(agg, "tile" if tile else "compose", style, eyes, ev.get("ms"))
    elif kind == "help":
        route = ev.get("route") or "unknown"
        _inc(agg["help_route"], route)
        if route in ("soon", "blocked"):         # the demand for a style that cannot be bought yet, by style and eye count
            _inc(agg["help_demand"], f"{route}|{ev.get('style') or 'unknown'}|{ev.get('eyes') or 0}")
        else:
            _inc(agg["help_why"], ev.get("why") or "unknown")
            _inc(agg["help_eyes"], ev.get("eyes") or 0)
    elif kind == "master" and ev.get("step") == "art":
        if ev.get("hold"):
            _inc(agg["master_hold"], ev["hold"])
        else:
            if ev.get("existing"):
                agg["master_existing"] += 1
            else:
                agg["master_art"] += 1
                _inc(agg["master_art_style"], ev.get("style") or "unknown")
                if ev.get("fallback"):
                    _inc(agg["master_fallback"], ev["fallback"])
                _ms(agg, "master_art", ev)
                _hist(agg, "art", ev.get("style") or "unknown", ev.get("count") or 1, ev.get("ms"))
                for field, key in (("peak_mb", "art_peak_mb"), ("need_s", "art_need_s")):
                    v = ev.get(field)
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
                        cur = agg["ms"].setdefault(key, [0, 0])
                        cur[0] += v
                        cur[1] += 1
            if ev.get("needs_review"):
                agg["master_review"] += 1
                _inc(agg["master_review_style"], ev.get("style") or "unknown")
            if ev.get("lab"):
                agg["master_lab"] += 1
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
    elif kind == "exp":
        stage, key, var = ev.get("stage"), ev.get("exp"), ev.get("variant")
        if stage in EXP_STAGES and key and var:
            live = stage == "paid" and ev.get("live") is not False
            if stage == "paid" and not live:
                stage = "paid_test"
            base = f"{key}|{var}"
            _inc(agg["exp_stage"], f"{base}|{stage}")
            if ev.get("hit"):
                _inc(agg["exp_hit"], f"{base}|{stage}")
            amount = ev.get("amount")
            if live and isinstance(amount, (int, float)) and not isinstance(amount, bool) and amount > 0:
                cur = ev.get("currency") or "eur"
                _inc(agg["exp_rev"], f"{base}|{cur}", amount)
                if ev.get("hit"):
                    _inc(agg["exp_rev_hit"], f"{base}|{cur}", amount)
    elif kind == "error":
        k = ev.get("class") or "unknown"
        _inc(agg["errors"], k)
        _inc(agg["error_endpoint"], ev.get("endpoint") or "other")
        if ev.get("reason"):
            _inc(agg["error_reason"], ev["reason"])
        if ev.get("style"):
            _inc(agg["error_style"], ev["style"])
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
    raw = store.get(rollup_path(day), max_bytes=ROLLUP_MAX_BYTES, timeout=8.0)
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
