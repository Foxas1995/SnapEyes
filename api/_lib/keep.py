# -*- coding: utf-8 -*-
"""Kept copies of the free preview (the owner's decision of 2026-11-26: "taip, saugok kiekvieną nuotrauką ir rezultatą"): every photo a visitor
sends to /api/analyze, the crop and the clean restoration of /api/enhance and the large preview of /api/compose are stored for KEEP_DAYS days in
the private Supabase store the orders use (api/_lib/store.py), so that the owner sees in /admin ("Peržiūros", api/_lib/ops.py a_kept) what people
send, what it became and why a photo was refused. The daily clean-up deletes a day's folder KEEP_DAYS days later (purge, from api/_lib/cleanup.py).

What is kept, under kept/<UTC day>/<visit>/:
  <HHMMSS>-<step>-<rand>-<name>.jpg   analyze: photo (the photo as the analysis saw it, at most PHOTO_SIDE px on its long side, JPEG q PHOTO_Q);
                                      enhance: before (the crop as it arrived) and after (the clean 1024 px restoration, as made);
                                      compose: art (the 1024 px preview the visitor is shown large, watermarked, as sent)
  <HHMMSS>-<step>-<rand>.json         beside them: the UTC time, the step, the outcome and the codes the endpoint already computed (the analysis's
                                      verdict or refusal reason, the restoration's gate, the style), and the same anonymous context the usage events
                                      carry (campaign code, device class, browser family, country, page language and price market). No IP address,
                                      no user agent, no e-mail, no cookie, no ticket.
The visit: the "visit" field the page sends with every request of the photo step (src/shared/visit.ts: a random value made when the page loads, held
in memory only, gone with the tab). A request without one (a page of before this release) is grouped by a hash of its work ticket (analyze mints
it, deglare and enhance take it back), else on its own.

Never kept: the AI-made sample eye (enhance's sample path, a compose of the sample's sealed eye), the owner's admin requests (a compose with the
admin key, the admin laboratory's requests, which say nokeep), a robot (the request context's bot class), the paid endpoints (orders keep their own
records), a batch of picker tiles. Nothing here ever costs a preview: the bytes are prepared and written in threads started as soon as they exist,
each step waits at most WAIT seconds for them before its reply (less when the invocation has little time left: below MIN_LEFT nothing is started),
every failure is caught, and the step's usage event says what happened (kept: ok, slow, fail, full, skip, off).

The switch: SNAPEYES_KEEP (on unless off, 0, false or no). Also off without storage or without the daily clean-up (events.retention_ok: the deletion
after KEEP_DAYS must be able to run). Ceilings, so that abuse cannot fill the store: ITEM_DAY_MAX pictures per instance per UTC day, VISIT_ITEMS_MAX per
visit per instance, and VISIT_DAY_MAX visit folders a day across the deployment (counted from a listing every FULL_CHECK_S seconds per instance, in the
background thread). About 0.2 to 0.4 MB a picture: a visit with three photos, one restoration and two previews is about 1.5 to 2 MB, so the ceiling of
visits bounds a day at about 3 GB and the 30 days at about 90 GB in the worst case."""
import os, io, re, json, time, base64, hashlib, secrets, threading
from . import iris as L
from . import store
from . import counter

TOP = "kept"
KEEP_DAYS = 30               # the privacy policy's promise: deleted after 30 days (the daily clean-up)
PHOTO_SIDE = 1280            # a kept photo's long side at most (px)
PHOTO_Q = 82
WAIT = 1.5                   # seconds a step waits for its writes before its reply
MIN_LEFT = 6.0               # below this much of the invocation's time nothing is started
PUT_TIMEOUT = 8.0
ITEM_DAY_MAX = 4000          # pictures one instance keeps in a UTC day
VISIT_ITEMS_MAX = 60         # pictures one visit keeps (on one instance)
VISIT_DAY_MAX = 1500         # visit folders a day across the deployment
FULL_CHECK_S = 600.0         # how often an instance lists the day's folder to count its visits
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_VISIT = re.compile(r"^[a-z0-9][a-z0-9-]{5,39}$")
_FILE = re.compile(r"^([0-9]{6})-(analyze|enhance|compose)-([0-9a-f]{6})(?:-(photo|before|after|art))?\.(jpg|json)$")
_LOCK = threading.Lock()
_COUNT = {"day": "", "items": 0, "visits": {}, "full_day": "", "full_t": 0.0, "full": False}


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
            _COUNT.update(day=day, items=0, visits={})
        n = _COUNT["visits"].get(visit, 0)
        if _COUNT["items"] >= ITEM_DAY_MAX or n >= VISIT_ITEMS_MAX:
            return False
        _COUNT["items"] += 1
        _COUNT["visits"][visit] = n + 1
        return True


def _full(day):
    """Has the deployment reached VISIT_DAY_MAX visit folders today? Listed at most every FULL_CHECK_S seconds per instance (called in a writer
    thread, never on the request's own path). A listing that fails says not full."""
    now = time.time()
    with _LOCK:
        if _COUNT["full_day"] == day and now - _COUNT["full_t"] < FULL_CHECK_S:
            return _COUNT["full"]
    try:
        rows = store.list_folder(f"{TOP}/{day}", limit=1000, timeout=5.0, retry=False)
        n = len(rows)
        if n >= 1000:
            n += len(store.list_folder(f"{TOP}/{day}", limit=1000, offset=1000, timeout=5.0, retry=False))
        full = n >= VISIT_DAY_MAX
    except Exception:  # noqa
        full = False
    with _LOCK:
        _COUNT.update(full_day=day, full_t=now, full=full)
    return full


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
        self.threads, self.box, self.names = [], {"ok": 0, "fail": 0, "full": 0, "room": 0}, []

    def _write(self, name, make, ctype):
        try:
            if _full(self.day):
                self.box["full"] += 1
                return
            data = make()
            if not data:
                return
            store.put(f"{self.prefix}-{name}" if ctype == "image/jpeg" else f"{self.prefix}.json", data, ctype, upsert=False, timeout=PUT_TIMEOUT, retry=False)
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
        written when the wait ended), fail (a write failed), full (a ceiling), and skip, off, time, robot, sample, admin when nothing was started."""
        if self.why is not None:
            return self.why
        if not self.threads:
            return "full" if self.box["room"] else "skip"
        doc = {"v": 1, "t": round(self.t, 3), "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.t)), "step": self.step,
               "pictures": list(self.names)}
        doc.update({k: v for k, v in (meta or {}).items() if v is not None})
        doc["ctx"] = self.ctx
        data = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
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
        if self.box["full"] or self.box["room"]:
            return "full"
        return "ok"


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
        if L.time_left() < MIN_LEFT:
            return Keeper(step, None, "time")
        return Keeper(step, visit_of(body))
    except Exception:  # noqa
        return Keeper(step, None, "skip")


def photo_jpeg(im):
    """The photo as the analysis saw it, at most PHOTO_SIDE px on its long side, JPEG q PHOTO_Q (no metadata)."""
    w, h = im.size
    f = min(1.0, PHOTO_SIDE / float(max(w, h)))
    if f < 1.0:
        im = im.resize((max(1, int(round(w * f))), max(1, int(round(h * f)))), L.Image.LANCZOS)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=PHOTO_Q)
    return buf.getvalue()


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
    """The visit folders of one day, newest activity unknown: sorted by name."""
    if not _DAY.fullmatch(str(day or "")):
        raise ValueError("Not a day.")
    return [r["name"] for r in store.list_all(f"{TOP}/{day}") if r["folder"]]


def visit_files(day, visit):
    """The files of one visit: [{name, time, step, id, picture (photo, before, after, art) or None for the JSON}], in time order."""
    if not _DAY.fullmatch(str(day or "")) or not isinstance(visit, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{3,63}", visit):
        raise ValueError("Not a visit.")
    out = []
    for r in store.list_all(f"{TOP}/{day}/{visit}"):
        m = _FILE.fullmatch(r["name"]) if not r["folder"] else None
        if m:
            out.append({"name": r["name"], "time": m.group(1), "step": m.group(2), "id": m.group(3), "picture": m.group(4) if m.group(5) == "jpg" else None})
    return sorted(out, key=lambda x: (x["time"], x["id"], x["picture"] or ""))


def delete_visit(day, visit):
    """Delete one visit's folder (a person asks us to delete). Returns how many files went."""
    names = [f"{TOP}/{day}/{visit}/{f['name']}" for f in visit_files(day, visit)]
    extra = [f"{TOP}/{day}/{visit}/{r['name']}" for r in store.list_all(f"{TOP}/{day}/{visit}") if not r["folder"]
             and f"{TOP}/{day}/{visit}/{r['name']}" not in names]
    if names or extra:
        store.delete_many(names + extra)
    return len(names) + len(extra)


def purge(days_kept=KEEP_DAYS, yes=True, stop_left=10.0, say=None, now=None):
    """The daily clean-up's step: every kept/<day> folder older than days_kept days goes, with everything in it. Never raises; stops for time with
    more: true (the next run goes on). Returns {days, files, more}."""
    res = {"days": 0, "files": 0, "more": False}
    say = say or (lambda m: None)
    try:
        if not store.configured():
            return dict(res, skipped="storage_not_configured")
        cut = time.strftime("%Y-%m-%d", time.gmtime((time.time() if now is None else now) - int(days_kept) * 86400))
        for day in sorted(d for d in days() if d < cut):
            if L.time_left() < stop_left:
                res["more"] = True
                break
            names = []
            for r in store.list_all(f"{TOP}/{day}"):
                if r["folder"]:
                    names += [f"{TOP}/{day}/{r['name']}/{f['name']}" for f in store.list_all(f"{TOP}/{day}/{r['name']}") if not f["folder"]]
                else:
                    names.append(f"{TOP}/{day}/{r['name']}")
            if yes and names:
                store.delete_many(names)
            res["files"] += len(names)
            res["days"] += 1
        if res["days"]:
            say(f"clean-up: kept previews of {res['days']} day(s) older than {days_kept} days deleted ({res['files']} files)")
    except Exception as e:  # noqa: the rest of the clean-up goes on
        res["error"] = type(e).__name__
    return res
