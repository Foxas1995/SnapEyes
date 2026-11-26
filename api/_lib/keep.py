# -*- coding: utf-8 -*-
"""Kept copies of the free preview (the owner's decision of 2026-11-26: "taip, saugok kiekvieną nuotrauką ir rezultatą"): every photo a visitor
sends to /api/analyze, the crop and the clean restoration of /api/enhance and the large preview of /api/compose are stored for up to KEEP_DAYS days
in the private Supabase store the orders use (api/_lib/store.py), so that the owner sees in /admin ("Peržiūros", api/_lib/ops.py a_kept) what people
send, what it became and why a photo was refused. The daily clean-up deletes a day's folder KEEP_DAYS days later, or earlier under the size cap
(purge, from api/_lib/cleanup.py).

What is kept, under kept/<UTC day>/<visit>/:
  <HHMMSS>-<step>-<rand>-<name>.jpg   analyze: photo (the photo as the analysis saw it, at most PHOTO_SIDE px on its long side, JPEG q PHOTO_Q);
                                      enhance: before (the crop as it arrived, at most CROP_SIDE px, JPEG q CROP_Q) and after (the clean 1024 px
                                      restoration, as made); compose: art (the 1024 px preview the visitor is shown large, watermarked, as sent)
  <HHMMSS>-<step>-<rand>.json         beside them: the UTC time, the step, the outcome and the codes the endpoint already computed (the analysis's
                                      verdict or refusal reason, the restoration's gate or "failed" when the restoration failed, the style), and the same
                                      anonymous context the usage events carry (campaign code, device class, browser family, country, page language and
                                      price market). No IP address, no user agent, no e-mail, no cookie, no ticket.
The visit: the "visit" field the page sends with every request of the photo step (src/shared/visit.ts: a random value made when the page loads, held
in memory only, gone with the tab). A request without one (a page of before this release) is grouped by a hash of its work ticket (analyze mints
it, deglare and enhance take it back), else on its own.

Never kept: a visitor in the United States (the price market us or the country US: the US checkbox says the photos are used only to make the preview
and the artwork; the code is market), the AI-made sample eye (enhance's sample path, a compose of the sample's sealed eye), the owner's admin requests
(a compose with the admin key, the admin laboratory's requests, which say nokeep), a robot (the request context's bot class), the paid endpoints
(orders keep their own records), a batch of picker tiles. Nothing here ever costs a preview: the bytes are prepared and written in threads started as
soon as they exist, each step waits at most WAIT seconds for them before its reply (less when the invocation has little time left: below MIN_LEFT
nothing is started), every failure is caught, and the step's usage event says what happened (kept: ok, slow, fail, full, cap, day, skip, off, time,
robot, sample, market).

The switch: SNAPEYES_KEEP (on unless off, 0, false or no). Also off without storage or without the daily clean-up (events.retention_ok: the deletion
must be able to run). THE SIZE, so that the kept area never crowds the paid orders' masters out of the same bucket (the owner's plan is not known; the
free one holds 1 GB):
  - the cap: SNAPEYES_KEEP_MAX_MB (default 500). The daily clean-up, after the 30-day rule, sums the area (each finished day once, kept/<day>/_size.json;
    today from the instances' own reports) and deletes the OLDEST day folders until the area is under the cap; never today's. It writes the sums to
    kept/_area.json.
  - the writer (every FULL_CHECK_S seconds per instance, in its thread, never on the request's path): reports its own bytes of today
    (kept/<day>/_n/<instance>.json), sums the instances' reports and reads the clean-up's sum of the finished days; past the cap plus MARGIN_MB it
    keeps nothing more (code cap), and past VISIT_DAY_MAX visit folders today (SNAPEYES_KEEP_VISITS_DAY, default 100) nothing more either (code day).
  - per instance: ITEM_DAY_MAX pictures a day; per visit: VISIT_ITEMS_MAX pictures.
A picture is 0.15 to 0.6 MB (the photo 1280 px q82, the crop 1024 px q85, the restoration and the preview 1024 px): a visit is about 1.5 to 2 MB, at most
VISIT_ITEMS_MAX x 0.6 = about 7 MB. The worst case between two clean-ups: the cap plus the margin (700 MB) plus what the instances write before each
next looks (FULL_CHECK_S, five minutes, and never more than ITEM_DAY_MAX pictures, about 0.15 GB, per instance and day): with the one or two warm
instances this site runs, under 1 GB; typical, about 100 visits a day, 200 MB a day, the area at the cap."""
import os, io, re, json, time, base64, hashlib, secrets, threading
from . import iris as L
from . import store
from . import counter

TOP = "kept"
KEEP_DAYS = 30               # the privacy policy's promise: deleted at the latest after 30 days (the daily clean-up)
PHOTO_SIDE = 1280            # a kept photo's long side at most (px)
PHOTO_Q = 82
CROP_SIDE = 1024             # the kept crop of enhance (the "before"), re-encoded so that one picture cannot weigh more than about 0.6 MB
CROP_Q = 85
WAIT = 1.5                   # seconds a step waits for its writes before its reply
MIN_LEFT = 6.0               # below this much of the invocation's time nothing is started
PUT_TIMEOUT = 8.0
ITEM_DAY_MAX = 250           # pictures one instance keeps in a UTC day
VISIT_ITEMS_MAX = 12         # pictures one visit keeps (on one instance)
MARGIN_MB = 200              # the writer stops at the cap plus this (the clean-up brings the area back under the cap once a day)
FULL_CHECK_S = 300.0         # how often an instance reports its bytes and reads the area's sums and today's visits
INSTANCE = secrets.token_hex(6)   # this instance's name in kept/<day>/_n/ (made at import, nothing of the request)
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_VISIT = re.compile(r"^[a-z0-9][a-z0-9-]{5,39}$")
_VISIT_DIR = re.compile(r"^[vtr]-[a-z0-9][a-z0-9-]{3,61}$")
_FILE = re.compile(r"^([0-9]{6})-(analyze|enhance|compose)-([0-9a-f]{6})(?:-(photo|before|after|art))?\.(jpg|json)$")
_LOCK = threading.Lock()
_COUNT = {"day": "", "items": 0, "bytes": 0, "visits": {}, "held_day": "", "held_t": 0.0, "held": None}


def _env_int(name, default, lo, hi):
    try:
        v = int(str(os.environ.get(name, "")).strip() or default)
    except ValueError:
        v = default
    return max(lo, min(hi, v))


def max_mb():
    """The cap of the kept area in MB (SNAPEYES_KEEP_MAX_MB, default 500)."""
    return _env_int("SNAPEYES_KEEP_MAX_MB", 500, 10, 100000)


def visit_day_max():
    """Visit folders a UTC day across the deployment (SNAPEYES_KEEP_VISITS_DAY, default 100)."""
    return _env_int("SNAPEYES_KEEP_VISITS_DAY", 100, 1, 100000)


def on():
    """Is keeping on here: the switch, storage, and the daily clean-up that deletes after KEEP_DAYS."""
    if str(os.environ.get("SNAPEYES_KEEP", "on")).strip().lower() in ("off", "0", "false", "no"):
        return False
    try:
        from . import events as E
        return store.configured() and E.retention_ok()
    except Exception:  # noqa
        return False


def visit_of(body):
    """The visit folder of a request: the page's visit field, else a hash of its work ticket, else a random one of its own."""
    v = body.get("visit") if isinstance(body, dict) else None
    if isinstance(v, str) and _VISIT.fullmatch(v.strip().lower()):
        return "v-" + v.strip().lower()
    t = body.get("ticket") if isinstance(body, dict) else None
    if isinstance(t, str) and t:
        return "t-" + hashlib.sha256(("snapeyes-keep:" + t).encode("utf-8", "replace")).hexdigest()[:16]
    return "r-" + secrets.token_hex(8)


def _context():
    """The anonymous context of the request as the usage events carry it: campaign parts, device class, browser family, country, language, market."""
    try:
        return {k: v for k, v in counter.attach({}, L.ctx()).items() if isinstance(v, str) and v}
    except Exception:  # noqa
        return {}


def _room(day, visit):
    """May one more picture be kept now (this instance's day and visit ceilings)? Counts it when yes."""
    with _LOCK:
        if _COUNT["day"] != day:
            _COUNT.update(day=day, items=0, bytes=0, visits={})
        n = _COUNT["visits"].get(visit, 0)
        if _COUNT["items"] >= ITEM_DAY_MAX or n >= VISIT_ITEMS_MAX:
            return False
        _COUNT["items"] += 1
        _COUNT["visits"][visit] = n + 1
        return True


def _json_or_none(path):
    try:
        v = store.get_json(path, timeout=5.0, retry=False)
        return v if isinstance(v, dict) else None
    except Exception:  # noqa
        return None


def _today_bytes(day):
    """The bytes kept today across the deployment, as the instances last reported them (kept/<day>/_n/)."""
    total = 0
    for r in store.list_folder(f"{TOP}/{day}/_n", limit=1000, timeout=5.0, retry=False):
        if not r["folder"]:
            v = _json_or_none(f"{TOP}/{day}/_n/{r['name']}")
            b = (v or {}).get("bytes")
            total += b if isinstance(b, int) and not isinstance(b, bool) and b > 0 else 0
    return total


def _visit_count(day):
    return sum(1 for r in store.list_folder(f"{TOP}/{day}", limit=1000, timeout=5.0, retry=False) if r["folder"] and _VISIT_DIR.fullmatch(r["name"]))


def _held(day):
    """Why keeping must stop now ("cap": the area is past the cap plus the margin; "day": today has VISIT_DAY_MAX visits), or None. Looked at most every
    FULL_CHECK_S seconds per instance, in a writer thread: this instance's report of its bytes is written first, then the reports, the clean-up's sum of
    the finished days and today's visits are read. A look that fails holds nothing back."""
    now = time.time()
    with _LOCK:
        if _COUNT["held_day"] == day and now - _COUNT["held_t"] < FULL_CHECK_S:
            return _COUNT["held"]
        _COUNT.update(held_day=day, held_t=now)        # one look at a time per instance: the others use the last answer meanwhile
        mine = _COUNT["bytes"] if _COUNT["day"] == day else 0
    held = None
    try:
        store.put(f"{TOP}/{day}/_n/{INSTANCE}.json", store.json_bytes({"bytes": int(mine), "t": int(now)}), "application/json", upsert=True,
                  timeout=5.0, retry=False)
        area = _json_or_none(f"{TOP}/_area.json") or {}
        past = area.get("past_bytes")
        past = past if isinstance(past, int) and not isinstance(past, bool) and past > 0 else 0
        if past + _today_bytes(day) > (max_mb() + MARGIN_MB) * 1024 * 1024:
            held = "cap"
        elif _visit_count(day) >= visit_day_max():
            held = "day"
    except Exception:  # noqa
        held = None
    with _LOCK:
        _COUNT["held"] = held
    return held


class Keeper:
    """The kept copies of one request of one step. begin() makes it; image() starts a writer thread; done() writes the JSON beside the pictures, waits
    for them (at most WAIT seconds) and answers the code for the step's usage event. A keeper that is off does nothing and answers why."""

    def __init__(self, step, visit, why=None):
        self.step, self.visit, self.why = step, visit, why
        now = time.time()
        g = time.gmtime(now)
        self.day = time.strftime("%Y-%m-%d", g)
        self.t = now
        self.prefix = f"{TOP}/{self.day}/{visit}/{time.strftime('%H%M%S', g)}-{step}-{secrets.token_hex(3)}" if visit else ""
        self.ctx = _context() if why is None else {}
        self.threads, self.box, self.names, self.ended = [], {"ok": 0, "fail": 0, "cap": 0, "day": 0, "room": 0}, [], False

    def _write(self, name, make, ctype):
        try:
            held = _held(self.day)
            if held:
                self.box[held] += 1
                return
            data = make()
            if not data:
                return
            store.put(f"{self.prefix}-{name}" if ctype == "image/jpeg" else f"{self.prefix}.json", data, ctype, upsert=False, timeout=PUT_TIMEOUT, retry=False)
            with _LOCK:
                if _COUNT["day"] == self.day:
                    _COUNT["bytes"] += len(data)
            self.box["ok"] += 1
        except Exception:  # noqa: a kept copy never costs a preview
            self.box["fail"] += 1

    def image(self, name, make):
        """Keep one picture: make() returns its JPEG bytes (it runs in the writer thread). name: photo, before, after or art."""
        if self.why is not None or L.time_left() < MIN_LEFT:
            self.why = self.why or "time"
            return
        if not _room(self.day, self.visit):
            self.box["room"] += 1
            return
        th = threading.Thread(target=self._write, args=(f"{name}.jpg", make, "image/jpeg"), daemon=True)
        th.start()
        self.threads.append(th)
        self.names.append(name)

    def done(self, meta, wait=None):
        """Write the JSON beside the pictures (when at least one was started) and wait for every write. The code: ok (all written), slow (still being
        written when the wait ended), fail (a write failed), cap or day (the area's cap or today's visits), full (this instance's or this visit's ceiling),
        and skip, off, time, robot, sample, market when nothing was started. Once per keeper; never raises."""
        try:
            if self.why is not None:
                return self.why
            if self.ended:
                return "skip"
            self.ended = True
            if not self.threads:
                return "full" if self.box["room"] else "skip"
            doc = {"v": 1, "t": round(self.t, 3), "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.t)), "step": self.step,
                   "pictures": list(self.names)}
            doc.update({k: v for k, v in (meta or {}).items() if v is not None})
            doc["ctx"] = self.ctx
            data = json.dumps(doc, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
            th = threading.Thread(target=self._write, args=("meta", lambda: data, "application/json"), daemon=True)
            th.start()
            self.threads.append(th)
            w = WAIT if wait is None else wait
            end = time.time() + max(0.0, min(w, L.time_left() - 2.0))
            for t in self.threads:
                t.join(max(0.0, end - time.time()))
            if any(t.is_alive() for t in self.threads):
                return "slow"
            if self.box["fail"]:
                return "fail"
            for k in ("cap", "day"):
                if self.box[k]:
                    return k
            return "full" if self.box["room"] else "ok"
        except Exception:  # noqa
            return "fail"


def _us(c):
    """Is the request a visitor in the United States: the page's price market us, or the country Vercel names US?"""
    return isinstance(c, dict) and (str(c.get("market") or "").lower() == "us" or str(c.get("cc") or "").lower() == "us")


def begin(step, body, skip=None):
    """A keeper for one request of a step (analyze, enhance, compose). skip: why the caller keeps nothing (sample, admin). Never raises."""
    try:
        if skip:
            return Keeper(step, None, skip)
        if not on():
            return Keeper(step, None, "off")
        if isinstance(body, dict) and body.get("nokeep") is True:
            return Keeper(step, None, "skip")
        c = L.ctx()
        if isinstance(c, dict) and c.get("bot"):
            return Keeper(step, None, "robot")
        if _us(c) or (isinstance(body, dict) and str(body.get("market") or "").lower() == "us"):
            return Keeper(step, None, "market")
        if L.time_left() < MIN_LEFT:
            return Keeper(step, None, "time")
        return Keeper(step, visit_of(body))
    except Exception:  # noqa
        return Keeper(step, None, "skip")


def photo_jpeg(im, side=PHOTO_SIDE, q=PHOTO_Q):
    """A picture at most `side` px on its long side, JPEG q `q` (no metadata)."""
    w, h = im.size
    f = min(1.0, side / float(max(w, h)))
    if f < 1.0:
        im = im.resize((max(1, int(round(w * f))), max(1, int(round(h * f)))), L.Image.LANCZOS)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=q)
    return buf.getvalue()


def crop_jpeg(im):
    """enhance's crop as it arrived, at most CROP_SIDE px, JPEG q CROP_Q."""
    return photo_jpeg(im, CROP_SIDE, CROP_Q)


def b64_bytes(s):
    """The bytes of a base64 image as it was sent (a data URL prefix dropped), or None."""
    try:
        if not isinstance(s, str) or not s:
            return None
        if s.strip().startswith("data:") and "," in s[:64]:
            s = s.split(",", 1)[1]
        return base64.b64decode(s)
    except Exception:  # noqa
        return None


# ----------------------------------------------------------------------------- the admin page and the clean-up
def days():
    """The days that have kept copies, newest first."""
    return sorted((r["name"] for r in store.list_all(TOP) if r["folder"] and _DAY.fullmatch(r["name"])), reverse=True)


def visits(day):
    """The visit folders of one day, sorted by name."""
    if not _DAY.fullmatch(str(day or "")):
        raise ValueError("Not a day.")
    return [r["name"] for r in store.list_all(f"{TOP}/{day}") if r["folder"] and _VISIT_DIR.fullmatch(r["name"])]


def visit_files(day, visit):
    """The files of one visit: [{name, time, step, id, picture (photo, before, after, art) or None for the JSON}], in time order."""
    if not _DAY.fullmatch(str(day or "")) or not isinstance(visit, str) or not _VISIT_DIR.fullmatch(visit):
        raise ValueError("Not a visit.")
    out = []
    for r in store.list_all(f"{TOP}/{day}/{visit}"):
        m = _FILE.fullmatch(r["name"]) if not r["folder"] else None
        if m:
            out.append({"name": r["name"], "time": m.group(1), "step": m.group(2), "id": m.group(3), "picture": m.group(4) if m.group(5) == "jpg" else None,
                        "size": r.get("size")})
    return sorted(out, key=lambda x: (x["time"], x["id"], x["picture"] or ""))


def delete_visit(day, visit):
    """Delete one visit's folder (a person asks us to delete). Returns how many files went. The day's size sum is dropped, so the clean-up counts it again."""
    names = [f"{TOP}/{day}/{visit}/{f['name']}" for f in visit_files(day, visit)]
    extra = [f"{TOP}/{day}/{visit}/{r['name']}" for r in store.list_all(f"{TOP}/{day}/{visit}") if not r["folder"]
             and f"{TOP}/{day}/{visit}/{r['name']}" not in names]
    if names or extra:
        store.delete_many(names + extra + [f"{TOP}/{day}/_size.json"])
    return len(names) + len(extra)


def _day_files(day):
    """Every file under kept/<day>/ (its visits, the instances' reports, its size sum): [(path, size)]."""
    out = []
    for r in store.list_all(f"{TOP}/{day}"):
        if r["folder"]:
            out += [(f"{TOP}/{day}/{r['name']}/{f['name']}", f.get("size")) for f in store.list_all(f"{TOP}/{day}/{r['name']}") if not f["folder"]]
        else:
            out.append((f"{TOP}/{day}/{r['name']}", r.get("size")))
    return out


def _day_size(day, yes=True):
    """The bytes of a finished day: its _size.json, else summed from the listing and written there (once; a day is not written to any more)."""
    v = _json_or_none(f"{TOP}/{day}/_size.json")
    if v and isinstance(v.get("bytes"), int):
        return v["bytes"]
    b = sum(s for p, s in _day_files(day) if isinstance(s, int) and not p.endswith("/_size.json") and "/_n/" not in p)
    if yes:
        try:
            store.put(f"{TOP}/{day}/_size.json", store.json_bytes({"bytes": int(b), "t": int(time.time())}), "application/json", upsert=True, timeout=5.0)
        except Exception:  # noqa: counted again at the next run
            pass
    return b


def status():
    """The kept area as the admin page shows it: {on, area_mb (the finished days, as the clean-up last summed them, and today), today_mb, cap_mb,
    margin_mb, visits_today, visits_day_max, held (cap, day or None), checked (the clean-up's time)}. Never raises."""
    day = time.strftime("%Y-%m-%d", time.gmtime())
    out = {"on": on(), "cap_mb": max_mb(), "margin_mb": MARGIN_MB, "visits_day_max": visit_day_max(), "keep_days": KEEP_DAYS}
    try:
        area = _json_or_none(f"{TOP}/_area.json") or {}
        past = area.get("past_bytes") if isinstance(area.get("past_bytes"), int) else 0
        today = _today_bytes(day)
        n = _visit_count(day)
        mb = lambda b: round(b / (1024 * 1024), 1)
        held = "cap" if past + today > (max_mb() + MARGIN_MB) * 1024 * 1024 else "day" if n >= visit_day_max() else None
        out.update(area_mb=mb(past + today), past_mb=mb(past), today_mb=mb(today), visits_today=n, held=held, checked=area.get("iso"))
    except Exception as e:  # noqa
        out["error"] = type(e).__name__
    return out


def purge(days_kept=KEEP_DAYS, yes=True, stop_left=10.0, say=None, now=None):
    """The daily clean-up's step. 1: every kept/<day> folder older than days_kept days goes, with everything in it. 2: the size cap (max_mb): the finished
    days are summed (each once, _size.json), today from the instances' reports, and the OLDEST finished days go until the area is under the cap (never
    today's: today alone past the cap stops the writers, _held). The sums go to kept/_area.json for the writers and the admin page. Never raises; stops for
    time with more: true (the next run goes on). Returns {days, files, cap_days, area_mb, more}."""
    res = {"days": 0, "files": 0, "cap_days": 0, "more": False}
    say = say or (lambda m: None)
    try:
        if not store.configured():
            return dict(res, skipped="storage_not_configured")
        t_now = time.time() if now is None else now
        today = time.strftime("%Y-%m-%d", time.gmtime(t_now))
        cut = time.strftime("%Y-%m-%d", time.gmtime(t_now - int(days_kept) * 86400))
        all_days = sorted(days())
        for day in [d for d in all_days if d < cut]:
            if L.time_left() < stop_left:
                res["more"] = True
                return res
            names = [p for p, _s in _day_files(day)]
            if yes and names:
                store.delete_many(names)
            res["files"] += len(names)
            res["days"] += 1
        if res["days"]:
            say(f"clean-up: kept previews of {res['days']} day(s) older than {days_kept} days deleted ({res['files']} files)")
        past_days = [d for d in all_days if cut <= d < today]
        sizes = {}
        for d in past_days:
            if L.time_left() < stop_left:
                res["more"] = True
                return res
            sizes[d] = _day_size(d, yes)
        today_b = _today_bytes(today)
        cap = max_mb() * 1024 * 1024
        total = sum(sizes.values()) + today_b
        for d in past_days:
            if total <= cap or L.time_left() < stop_left:
                break
            names = [p for p, _s in _day_files(d)]
            if yes and names:
                store.delete_many(names)
            total -= sizes.pop(d)
            res["cap_days"] += 1
            res["files"] += len(names)
        if res["cap_days"]:
            say(f"clean-up: kept previews of the {res['cap_days']} oldest day(s) deleted to keep the area under {max_mb()} MB")
        past = sum(sizes.values())
        if yes:
            store.put(f"{TOP}/_area.json", store.json_bytes({"past_bytes": int(past), "today_bytes": int(today_b), "today": today, "cap_mb": max_mb(),
                                                             "t": int(t_now), "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_now))}),
                      "application/json", upsert=True, timeout=5.0)
        res["area_mb"] = round((past + today_b) / (1024 * 1024), 1)
    except Exception as e:  # noqa: the rest of the clean-up goes on
        res["error"] = type(e).__name__
    return res
