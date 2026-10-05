# -*- coding: utf-8 -*-
"""The owner's admin panel, server side: POST /api/admin {action, ...} (api/admin.py), used by /admin (src/admin/).

Login: every call carries "Authorization: Bearer <admin key>". The key is "<kind>.<expiry>.<32 hex>", kind
admin_kind() = "admin-v<SNAPEYES_ADMIN_EPOCH, default 1>", minted by scripts/mint_admin.py (at most 90 days) with
mint_admin_key(). It is signed with the admin secret ONLY (admin_secret(): SNAPEYES_ADMIN_SECRET, or else
SNAPEYES_TICKET_SECRET, either of at least ADMIN_SECRET_MIN characters, under its own label "snapeyes-admin-v1:", so an
admin key is never an order or unlock ticket and no ticket is an admin key). Never the Gemini key: without such a
secret every admin call answers 503 admin_not_configured (so does an epoch that is not 1 to 6 digits, admin_problem).
The key is checked in constant time on every call; raising SNAPEYES_ADMIN_EPOCH on Vercel revokes every key, and
changing SNAPEYES_ADMIN_SECRET does too without touching the customers' order links. Failed attempts are slowed (FAIL_SLEEP) and limited per client: FAIL_LOCAL failures in
FAIL_WINDOW on one instance, or FAIL_HOURLY in an hour across instances (ops/adminfail/<yymmddHH>/<tag>-<rand>.json,
where tag is a keyed hash of the client address and nothing else is kept; written only while the daily clean-up can
delete them after 2 days, events.retention_ok(): CRON_SECRET set), answer 429 without looking at the key.

Read-only views: me, summary (configuration and ordering state, the price experiments that run), stats (per-day counts
from the usage events, api/_lib/events.py), errors (the latest error events), orders (the order folders, state derived from
the stored files only: nothing is sent, asked of Stripe or changed), order (one order: every record, signed image links
valid 1 h, QA flags, payments, refunds, the admin log, its price experiment), audit, lab_list, experiments (the page
"Kainų testai": every price experiment of api/_lib/experiments.py with its state, variants, the funnel and revenue per
variant, the significance note and the warnings; api/_lib/abtest.py), cpu_probe (a fixed CPU workload run on this very
instance, cold or warm: seconds per phase, the slow factor against a baseline the caller sends, and what the instance says
about its memory, CPUs and /tmp; nothing is read from storage or changed; api/_lib/cpu_probe.py), plates_status (the plate
library as THIS function sees it: the 1K plates and the two atlases in the bundle with their recorded sizes, the 4K plates in
private storage when asked for, the registry's version and hash; read only; api/_lib/styles/plates.py), styles_lab (one style of the
v3 engine drawn on one restored iris, whatever its stage: the laboratory is where a held or not yet visible style is looked at; the eye
is sent as an image or is the stored eye of a lab test order; no image model is called and nothing is stored or audited; a_styles_lab),
order_steps (one order's master plan: the plan, every step with its done and try record, the rerun count, the claims, the capacity at the factor in
force, the eyes' ids, classes and gate results, the current artwork's record; read only; api/_lib/styles/steps.py).

Actions (the page asks for a confirmation first; refund and delete_files also need the order number typed as
"confirm"; rerun_step and lab_steps draw a 4K master through the master plan's step runner, with the claims and guards of a paid order): link (the withdrawal link, and the order page link to copy: opening that one starts making the file),
resend_confirmation, resend_ready, release, clear_review, mailed_by_hand, render (make an eye only once making has
begun on the customer's order page, see act_render, or re-render one by master_eye's rules), recompose, refund
(Stripe POST /v1/refunds on the payment intent), mark_refunded
(refunded.json, as scripts/order_admin.py refunded), delete_files,
lab_start (an unlock ticket for a test order lab-<yymmdd>-<rand>), lab_delete, exp_start and exp_stop (switch a price
experiment on or off: api/_lib/abtest.py start and stop; nothing runs until the owner does this, and both are in the audit
log with the experiment's key). They reuse pay.py, order.py,
master_eye.py, master_compose.py and store.py, and each one is written to the admin audit log:
ops/audit/<YYYY-MM-DD>/<HHMMSS>-<rand>.json and ops/orderlog/<order>/<time>-<rand>.json (action, order, result code;
no email address, no link). The order's copy belongs to its record (privacy policy): it goes whenever the order goes
completely (pay.drop_orderlog: an unpaid order's purge or deletion, a lab test's deletion; the daily clean-up removes
what is left of an order that is gone, cleanup._orphan_logs), no copy is written for an order that is not there
(404) or was just deleted completely, and a paid order keeps it with its records."""
import re, json, time, hmac, base64, hashlib, secrets, threading, importlib
from . import iris as L
from . import store
from . import pay
from . import abtest
from . import events as E
from . import withdraw as W
from . import catalogue as CT
from .styles import steps as SP

ADMIN_TTL_MAX = 90 * 86400   # a key may live this long at most (scripts/mint_admin.py mints 1 to 90 days)
ADMIN_SECRET_MIN = 32        # characters of SNAPEYES_ADMIN_SECRET (or SNAPEYES_TICKET_SECRET) the admin keys need
ADMIN_LABEL = b"snapeyes-admin-v1:"
FAIL_WINDOW = 900.0          # seconds
FAIL_LOCAL = 8               # failed attempts per client in FAIL_WINDOW on one instance, then 429
FAIL_HOURLY = 20             # failed attempts per client in the current and the last hour, across instances, then 429
FAIL_SLEEP = 0.8             # every failed attempt waits this long
SIGN_SECONDS = 3600          # the admin page's image links
LAB_TICKET = 900             # the lab's unlock ticket (seconds)
AUDIT, ORDERLOG, REFUNDS, LAB, ADMINFAIL = "ops/audit", pay.ORDERLOG_TOP, "ops/refunds", "ops/lab", E.ADMINFAIL
# Gemini list prices per call (USD), an ESTIMATE ("įvertis") for the panel: the 4K render measured $0.153
# (master_eye.MASTER_SIDE note, 2026-09-23), a 1K gemini-3.1-flash-image image $0.067 (ai.google.dev pricing, noted
# 2026-09-16), a vision call on gemini-3.8-flash (one photo of up to 1600 px and a short JSON reply) about $0.003.
PRICES_USD = {"vision": 0.003, "image_1k": 0.067, "image_4k": 0.153}
LIST_MAX = 500               # order rows in one reply
STATS_DAYS_MAX = 90

_TOKEN = re.compile(r"^admin-v[0-9]{1,6}\.[0-9]{9,11}\.[0-9a-f]{32}$")
_PI = re.compile(r"^pi_[A-Za-z0-9_]{6,200}$")
_EMAIL_LIKE = re.compile(r"[^\s@]+@[^\s@]+")


# ----------------------------------------------------------------------------- small helpers
def log(msg):
    s = pay.scrub(str(msg))
    own = pay._env("SNAPEYES_ADMIN_SECRET")          # pay.scrub does not know this one
    if len(own) >= 8:
        s = s.replace(own, "***")
    print("snapeyes admin: " + s[:400], flush=True)


def _safe(fn, default=None):
    try:
        return fn()
    except store.StorageNotConfigured:
        raise
    except Exception as e:  # noqa: one unreadable file must not cost the whole view
        log(f"read failed: {type(e).__name__}")
        return default


def each(fns, width=12, tolerant=True):
    """Run many small storage calls, `width` at a time (pay.parallel keeps the invocation's deadline per thread)."""
    out = []
    for i in range(0, len(fns), width):
        part = fns[i:i + width]
        if tolerant:
            part = [lambda f=f: _safe(f) for f in part]
        out += pay.parallel(part)
    return out


def _code(v, n=40):
    s = re.sub(r"[^a-z0-9_.-]", "", str(v or "").lower())[:n]
    return s or None


def _day_iso(t):
    return time.strftime("%Y-%m-%d", time.gmtime(t))


def mask_email(e):
    """a***@g***.com: enough to recognise a customer in the list, not enough to write to them."""
    if not isinstance(e, str) or "@" not in e:
        return None
    local, _, domain = e.strip().partition("@")
    parts = domain.split(".")
    tld = parts[-1] if len(parts) > 1 else ""
    return f"{local[:1]}***@{domain[:1]}***" + (f".{tld}" if tld else "")


def _order(body):
    return store.check_order(body.get("order") if isinstance(body, dict) else None)


def _mod(name):
    """A sibling endpoint module (order, master_eye, master_compose), imported when an action needs it."""
    return importlib.import_module(name)


# ----------------------------------------------------------------------------- login
_AUTH_LOCK = threading.Lock()
_FAILS = {}                  # client tag -> [failure times]
_BLOCKED = {}                # client tag -> blocked until


def admin_kind():
    """admin-v<SNAPEYES_ADMIN_EPOCH> (digits only; 1 when unset). Raising the number revokes every key."""
    ep = pay._env("SNAPEYES_ADMIN_EPOCH")
    return f"admin-v{int(ep) if re.fullmatch(r'[0-9]{1,6}', ep) else 1}"


def _admin_raw():
    """(raw secret, its variable name) for the admin keys, or ("", problem). SNAPEYES_ADMIN_SECRET when it is set (it
    must then be long enough itself: a short one is an error, not a reason to use another secret), else
    SNAPEYES_TICKET_SECRET. Never the Gemini key: that one travels to Google with every model call."""
    own = pay._env("SNAPEYES_ADMIN_SECRET")
    if own:
        if len(own) >= ADMIN_SECRET_MIN:
            return own, "SNAPEYES_ADMIN_SECRET"
        return "", f"SNAPEYES_ADMIN_SECRET is shorter than {ADMIN_SECRET_MIN} characters"
    shared = pay._env("SNAPEYES_TICKET_SECRET")
    if len(shared) >= ADMIN_SECRET_MIN:
        return shared, "SNAPEYES_TICKET_SECRET"
    return "", (f"no admin secret: set SNAPEYES_ADMIN_SECRET ({ADMIN_SECRET_MIN} characters or more) on this "
                f"deployment (the Gemini key is never used for admin keys)")


def admin_secret():
    """The HMAC key of the admin keys (bytes), or None when admin_problem() says why not."""
    raw, _ = _admin_raw()
    return hashlib.sha256(ADMIN_LABEL + raw.encode("utf-8")).digest() if raw else None


def admin_secret_source():
    """The name of the variable the admin keys are signed with, or "" when there is none."""
    raw, name = _admin_raw()
    return name if raw else ""


def admin_problem():
    """Why no admin key can be accepted here ("" when the panel is set up): no admin secret, or an epoch typed wrong
    (it would fall back to admin-v1 and quietly keep the keys it was meant to revoke)."""
    raw, why = _admin_raw()
    if not raw:
        return why
    ep = pay._env("SNAPEYES_ADMIN_EPOCH")
    if ep and not re.fullmatch(r"[0-9]{1,6}", ep):
        return "SNAPEYES_ADMIN_EPOCH is not a whole number of 1 to 6 digits"
    return ""


def _admin_sig(key, kind, exp):
    return hmac.new(key, f"{kind}.{int(exp)}".encode("ascii"), hashlib.sha256).hexdigest()[:32]


def mint_admin_key(ttl, kind=None):
    """An admin key valid for ttl seconds (scripts/mint_admin.py; tests). RuntimeError without an admin secret."""
    key = admin_secret()
    if key is None:
        raise RuntimeError(admin_problem())
    kind = kind or admin_kind()
    exp = int(time.time()) + int(ttl)
    return f"{kind}.{exp}.{_admin_sig(key, kind, exp)}"


def check_admin_key(tok, kind=None):
    """Is tok an unexpired admin key of this kind, signed with this deployment's admin secret? Constant time."""
    try:
        key = admin_secret()
        if key is None:
            return False
        k, exp_s, sig = str(tok or "").split(".", 2)
        if k != (kind or admin_kind()) or not re.fullmatch(r"[0-9]{9,11}", exp_s) or int(exp_s) < time.time():
            return False
        return hmac.compare_digest(sig, _admin_sig(key, k, int(exp_s)))
    except Exception:  # noqa
        return False


def _bearer(req):
    h = str(req.headers.get("authorization") or "")
    return h[7:].strip() if h[:7].lower() == "bearer " else ""


def client_tag(req):
    """A keyed hash of the client address (Vercel sets x-real-ip / x-forwarded-for itself). Only the tag is used."""
    ip = str(req.headers.get("x-real-ip") or "").strip() or str(req.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip:
        try:
            ip = str(req.client_address[0])
        except Exception:  # noqa
            ip = "unknown"
    key = admin_secret() or b"snapeyes-adminfail"      # authorize() tags a client only when the secret is set
    return hmac.new(key, b"snapeyes-adminfail-v1:" + ip[:64].encode("utf-8", "replace"), hashlib.sha256).hexdigest()[:12]


def _too_many(until):
    wait = int(max(60, min(3600, until - time.time())))
    return store.Answer(429, "too_many_attempts", "Too many failed logins. Please wait and try again.", True, wait)


def _failed(tag, now):
    """Count one failed login: in this instance, and as a marker in storage (no address, only the tag)."""
    with _AUTH_LOCK:
        if len(_FAILS) > 2000 or len(_BLOCKED) > 2000:      # a warm instance keeps only what still counts
            for k in [k for k, v in _FAILS.items() if not v or now - v[-1] >= FAIL_WINDOW]:
                _FAILS.pop(k, None)
            for k in [k for k, v in _BLOCKED.items() if v <= now]:
                _BLOCKED.pop(k, None)
        _FAILS[tag] = [t for t in _FAILS.get(tag, []) if now - t < FAIL_WINDOW] + [now]
    log(f"login refused (client {tag})")
    time.sleep(FAIL_SLEEP)
    if not store.configured() or not E.retention_ok():
        # the privacy policy says these markers are deleted after 2 days, and only the daily clean-up deletes them:
        # without CRON_SECRET it never runs, so nothing is stored (this instance's own limit still applies)
        return
    try:
        hour = time.strftime("%y%m%d%H", time.gmtime(now))
        store.put(f"{ADMINFAIL}/{hour}/{tag}-{secrets.token_hex(4)}.json", b"{}", "application/json", upsert=False,
                  timeout=3.0, retry=False)
        n = 0
        for h in (hour, time.strftime("%y%m%d%H", time.gmtime(now - 3600))):
            n += len(store.list_folder(f"{ADMINFAIL}/{h}", timeout=3.0, retry=False, search=tag))
    except store.StorageError:
        return
    if n >= FAIL_HOURLY:
        with _AUTH_LOCK:
            _BLOCKED[tag] = now + 3600
        raise _too_many(now + 3600)


def authorize(req):
    """The admin key of this request, or a 403 (a 429 while this client is blocked; a 503 while this deployment has
    no admin secret, when no key can be right). Constant-time signature check."""
    problem = admin_problem()
    if problem:
        raise store.Answer(503, "admin_not_configured", f"The admin panel is not set up on this deployment: {problem}. "
                           "Fix it in Vercel's environment variables and redeploy.", False, None, detail=problem)
    now = time.time()
    tag = client_tag(req)
    with _AUTH_LOCK:
        until = _BLOCKED.get(tag, 0)
        recent = [t for t in _FAILS.get(tag, []) if now - t < FAIL_WINDOW]
    if until > now:
        raise _too_many(until)
    if len(recent) >= FAIL_LOCAL:
        raise _too_many(min(recent) + FAIL_WINDOW)
    tok, kind = _bearer(req), admin_kind()
    ok, exp = False, 0
    if len(tok) < 80 and _TOKEN.fullmatch(tok):
        exp = int(tok.split(".")[1])
        ok = check_admin_key(tok, kind=kind) and exp <= now + ADMIN_TTL_MAX + 3600
    if ok:
        with _AUTH_LOCK:
            _FAILS.pop(tag, None)
        return {"kind": kind, "exp": exp}
    _failed(tag, now)
    raise store.Answer(403, "admin_denied", "This admin key is not valid here (expired, revoked or for another "
                       "deployment). Mint a new one with scripts/mint_admin.py.", False)


# ----------------------------------------------------------------------------- the audit log
def audit(action, order=None, ok=True, result=None, eye=None, detail=None, orderlog=True):
    """One line of the admin audit log (never raises): what was done, to which order, and how it ended. No email
    address, no link, no key. orderlog=False: no copy in the order's own log (ops/orderlog/<order>/), for an order
    that is not there or was just deleted completely (its log went with it)."""
    try:
        now = time.time()
        g = time.gmtime(now)
        o = order if isinstance(order, str) and store.ORDER_RE.fullmatch(order) else None
        entry = {"v": 1, "t": round(now, 3), "iso": pay.iso(now), "action": _code(action), "order": o, "ok": bool(ok),
                 "result": _code(result)}
        if isinstance(eye, int) and not isinstance(eye, bool):
            entry["eye"] = eye
        if detail:
            entry["detail"] = _EMAIL_LIKE.sub("[email]", pay.scrub(str(detail)))[:200]
        data = store.json_bytes(entry)
        rand = secrets.token_hex(4)
        store.put(f"{AUDIT}/{time.strftime('%Y-%m-%d', g)}/{time.strftime('%H%M%S', g)}-{rand}.json", data,
                  "application/json", upsert=False, timeout=5.0, retry=False)
        if o and orderlog:
            store.put(f"{ORDERLOG}/{o}/{time.strftime('%Y%m%d%H%M%S', g)}-{rand}.json", data, "application/json",
                      upsert=False, timeout=5.0, retry=False)
        log(f"{entry['action']} {o or ''} {'ok' if ok else 'failed'} {entry['result'] or ''}")
    except Exception as e:  # noqa: the action itself is done; its log line must not undo that
        log(f"audit not written: {type(e).__name__}")


def audited(name, fn):
    def run(body, who):
        order = body.get("order") if isinstance(body.get("order"), str) else None
        eye = body.get("eye") if isinstance(body.get("eye"), int) else None
        # a price experiment's start or stop names its test in the log line even when it is refused
        xk = body.get("key") if name.startswith("exp_") and isinstance(body.get("key"), str) and abtest.get(body.get("key")) else None
        try:
            res = fn(body, who)
        except store.Answer as a:
            # a 404 names an order that is not there: no order log is started for it
            audit(name, order, False, a.body.get("reason"), eye, xk, orderlog=a.status != 404)
            raise
        except L.ClientError as e:
            audit(name, order, False, "bad_request", eye, str(e))
            raise
        except Exception as e:  # noqa
            audit(name, order, False, type(e).__name__, eye, xk)
            raise
        # an action that deleted the order completely says orderlog: False (its log went with it); one that made the
        # order (lab_start) names it in its reply
        if order is None and isinstance(res.get("order"), str):
            order = res["order"]
        audit(name, order, True, res.get("result"), eye, res.get("audit_detail"), orderlog=res.pop("orderlog", True))
        res.pop("audit_detail", None)
        return res
    return run


# ----------------------------------------------------------------------------- reading orders
def _json_or_none(path):
    return store.get_json(path, timeout=8.0)


def order_state(order, names, rec, paid, delivery, mail):
    """The order's state from its stored files alone (the order page's states, plus a few only the owner sees):
    lab, unpaid, checkout (a Stripe page was opened), expired (unpaid past 24 h), broken (no order.json), pending
    (paid, the confirmation email not out yet), paid, making, review, ready, withdrawn, deleted, test_payment (paid in
    Stripe's test mode where test payments count for nothing)."""
    if order.startswith("lab-"):
        return "lab"
    if not (isinstance(paid, dict) and paid.get("paid") is True):
        if "withdrawn.json" in names:
            return "withdrawn"
        if not isinstance(rec, dict):
            return "broken"
        if pay.draft_expired(rec):
            return "expired"
        return "checkout" if isinstance(rec.get("checkout"), dict) else "unpaid"
    if not pay.paid_counts(paid):
        return "test_payment"
    if "withdrawn.json" in names:
        return "withdrawn"
    if "deleted.json" in names or "expired.json" in names:
        return "deleted"
    if isinstance(delivery, dict):
        held = bool(delivery.get("needs_review")) and "release.json" not in names
        return "review" if held else "ready"
    if "review.json" in names:
        return "review"
    if pay.confirmation_needed(paid) and not (isinstance(mail, dict) and mail.get("state") == "sent"):
        return "pending"
    if any(re.fullmatch(r"eye_[1-8]\.jpg", n) for n in names):
        return "making"
    return "paid"


def order_facts(order, files=None):
    """(files, top-level names, order.json, paid.json, delivery.json, mail_delivery.json) of one order folder."""
    files = pay.folder_files(f"orders/{order}") if files is None else files
    names = {p.rsplit("/", 1)[-1] for p in files if p.count("/") == 2}
    want = [n for n in ("order.json", "paid.json", "delivery.json", "mail_delivery.json") if n in names]
    got = dict(zip(want, each([lambda n=n: _json_or_none(f"orders/{order}/{n}") for n in want])))
    return files, names, got.get("order.json"), got.get("paid.json"), got.get("delivery.json"), got.get("mail_delivery.json")


def order_row(order):
    files, names, rec, paid, delivery, mail = order_facts(order)
    state = order_state(order, names, rec, paid, delivery, mail)
    drafts = sorted({int(m.group(1)) for m in (re.match(r"^orders/[^/]+/draft/eye_([1-8])\.json$", p) for p in files) if m})
    made = sorted({int(m.group(1)) for m in (re.fullmatch(r"eye_([1-8])\.jpg", n) for n in names) if m})
    is_paid = isinstance(paid, dict) and paid.get("paid") is True
    spec = (paid or {}).get("spec") if is_paid else ((rec or {}).get("checkout") or {}).get("spec")
    spec = spec if isinstance(spec, dict) else {}
    co = (rec or {}).get("checkout") if isinstance(rec, dict) else None
    amount = paid.get("amount_total") if is_paid else (co.get("amount") if isinstance(co, dict) else None)
    currency = pay.currency_of(paid.get("currency") if is_paid else (co.get("currency") if isinstance(co, dict) else None))
    market = (paid.get("market") if is_paid else (co.get("market") if isinstance(co, dict) else None)) or spec.get("market")
    created_at = (rec or {}).get("created_at") if isinstance(rec, dict) else None
    lang = spec.get("lang") or (rec.get("lang") if isinstance(rec, dict) else None)
    xv = abtest.order_view(paid if is_paid else None, rec)
    return {"order": order, "state": state,
            "experiment": {"key": xv["key"], "variant": xv["variant"], "label": xv.get("label")} if xv else None,
            "created_at": created_at if isinstance(created_at, (int, float)) else None,
            "lang": lang if lang in pay.LANGS else None,
            "eyes": spec.get("eyes") or (len(drafts) or None), "style": spec.get("style"), "layout": spec.get("layout"),
            "amount": amount, "currency": currency.upper(), "market": market if market in pay.MARKETS else pay.DEFAULT_MARKET,
            "paid": is_paid, "live": bool(paid.get("livemode")) if is_paid else None,
            "paid_at": paid.get("paid_at") if is_paid else None, "email": mask_email(paid.get("email")) if is_paid else None,
            "drafts": len(drafts), "made": len(made), "files": len(files), "delivery": isinstance(delivery, dict),
            "held": isinstance(delivery, dict) and bool(delivery.get("needs_review")) and "release.json" not in names,
            "review": "review.json" in names, "withdrawal": "withdrawal.json" in names,
            "extra_payments": sum(1 for n in names if n.startswith("extra_payment_")),
            "mail": (mail or {}).get("state") if isinstance(mail, dict) else None}


def order_folders(days=30, lab=False):
    """The order folders made in the last `days` days (order ids start with the day, yymmdd-), newest first."""
    cut = pay.day(time.time() - max(0, days - 1) * 86400)
    out = []
    for r in store.list_all("orders"):
        name = r["name"]
        if not r["folder"] or not store.ORDER_RE.fullmatch(name):
            continue
        if name.startswith("lab-"):
            if lab:
                out.append(name)
            continue
        if re.match(r"^[0-9]{6}-", name) and name[:6] >= cut:
            out.append(name)
    return sorted(out, reverse=True)


# ----------------------------------------------------------------------------- the usage statistics
_ROLLUPS = {}                # day -> the stored counts of a finished day (they never change)
_DAYCACHE = {}               # day -> {event file name: event} for days still being read (today, a day not rolled up)
_CACHE_LOCK = threading.Lock()
DAYCACHE_MAX = 20000


def read_day(day, stop_left=12.0):
    """(counts, complete) of one day, read from its event files; files read before by this instance are not read
    again. complete is False when time ran out first."""
    names = E.day_names(day)
    with _CACHE_LOCK:
        cache = _DAYCACHE.setdefault(day, {})
        todo = [n for n in names if n not in cache]
    complete = True
    for i in range(0, len(todo), 16):
        if L.time_left() < stop_left:
            complete = False
            break
        part = todo[i:i + 16]
        got = each([lambda n=n: E.read_event(day, n) for n in part], width=16)
        with _CACHE_LOCK:
            for n, ev in zip(part, got):
                if isinstance(ev, dict) and sum(len(c) for c in _DAYCACHE.values()) < DAYCACHE_MAX:
                    cache[n] = ev
    with _CACHE_LOCK:
        evs = [cache[n] for n in names if n in cache]
    return E.summarize(evs), complete and len(evs) == len(names)


def collect_days(n):
    """[(day, counts, complete)] for the last n UTC days, oldest first. Finished days come from their stored counts
    (ops/daily/), computed once from the events and stored when missing; today is always read live."""
    now = time.time()
    days = [_day_iso(now - i * 86400) for i in range(n - 1, -1, -1)]
    today = days[-1]
    need = [d for d in days if d != today and d not in _ROLLUPS]
    if need:
        for d, agg in zip(need, each([lambda d=d: E.get_rollup(d) for d in need])):
            if isinstance(agg, dict):
                _ROLLUPS[d] = agg
    out = []
    for d in reversed(days):             # today first: the numbers the owner looks at most
        if d in _ROLLUPS:
            out.append((d, _ROLLUPS[d], True))
            continue
        if L.time_left() < 14:
            out.append((d, E.empty(), False))
            continue
        try:
            agg, complete = read_day(d)
        except store.StorageNotConfigured:
            raise
        except store.StorageError as e:
            log(f"events of {d} not read: {e}")
            agg, complete = E.empty(), False
        if complete and E.day_finished(d, now) and E.put_rollup(d, agg):
            _ROLLUPS[d] = agg
            with _CACHE_LOCK:
                _DAYCACHE.pop(d, None)
        out.append((d, agg, complete))
    return list(reversed(out))


def _slim(agg):
    return {k: v for k, v in agg.items() if k not in ("v", "day", "t", "recent_errors")}


# ----------------------------------------------------------------------------- read-only actions
def a_me(body, who):
    return {"ok": True, "kind": who["kind"], "expires_at": who["exp"], "storage": store.configured(),
            "now": int(time.time())}


def a_summary(body, who):
    """The deployment's configuration and ordering state (environment only, fast)."""
    sp = store.problem()
    op = pay.ordering_problem()
    return {"ok": True, "now": int(time.time()),
            "ordering": {"open": not op and not sp, "problem": op or (f"storage: {sp}" if sp else "")},
            "storage": {"configured": not sp, "problem": sp},
            "payments": {"stripe": pay.stripe_configured(), "live": pay.stripe_configured() and pay.stripe_live(),
                         "problem": pay.problem(), "email": pay.email_configured(), "test_orders": pay.test_orders_allowed(),
                         "production": pay.on_production()},
            "admin": {"kind": who["kind"], "expires_at": who["exp"], "secret": admin_secret_source()},
            # the usage events and the failed-login markers are stored only while the daily clean-up can delete them
            "retention": {"cron": E.retention_ok(), "events": E.retention_ok() and not sp},
            "experiments": _safe(abtest.summary, []),
            "prices_usd": PRICES_USD}


def a_stats(body, who):
    n = body.get("days")
    n = int(n) if isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= STATS_DAYS_MAX else 30
    rows = collect_days(n)
    return {"ok": True, "days": [{"day": d, "counts": _slim(a), "complete": c} for d, a, c in rows],
            "partial": not all(c for _, _, c in rows), "prices_usd": PRICES_USD, "recording": E.retention_ok()}


def a_errors(body, who):
    rows = collect_days(7)
    errs = []
    for d, agg, _ in rows:
        errs += [dict(r, day=d) for r in agg.get("recent_errors") or []]
    errs.sort(key=lambda r: -(r.get("t") or 0))
    return {"ok": True, "errors": errs[:150], "partial": not all(c for _, _, c in rows)}


def a_orders(body, who):
    n = body.get("days")
    days = int(n) if isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= 400 else 30
    names = order_folders(days, lab=body.get("lab") is True)
    rows, more = [], False
    for i in range(0, min(len(names), LIST_MAX), 10):
        if L.time_left() < 8:
            more = True
            break
        rows += [r for r in each([lambda o=o: order_row(o) for o in names[i:i + 10]], width=10) if isinstance(r, dict)]
    state = body.get("state")
    if isinstance(state, str) and state:
        rows = [r for r in rows if r["state"] == state]
    return {"ok": True, "days": days, "orders": rows, "total": len(names), "more": more or len(names) > LIST_MAX}


def _eye_view(order, n, recs, urls):
    """What the page shows of one eye: the draft files, the master and its checks."""
    folder = f"orders/{order}"
    d = recs.get(f"{folder}/draft/eye_{n}.json")
    m = recs.get(f"{folder}/eye_{n}.json")
    out = {"eye": n, "draft": None, "master": None}
    if isinstance(d, dict):
        c, p = d.get("crop") if isinstance(d.get("crop"), dict) else {}, d.get("preview") if isinstance(d.get("preview"), dict) else {}
        out["draft"] = {"pad": d.get("pad"), "uploaded": d.get("uploaded"), "crop_url": urls.get(c.get("path")),
                        "preview_url": urls.get(p.get("path")), "crop_side": c.get("side"), "preview_side": p.get("side")}
    key = f"{folder}/eye_{n}.jpg"
    if key in urls or isinstance(m, dict):
        can = None
        try:
            can = bool(_mod("master_eye")._can_rerender(m)) if isinstance(m, dict) else False
        except Exception:  # noqa
            can = None
        m = m if isinstance(m, dict) else {}
        out["master"] = {"url": urls.get(key), "preview_copy_url": urls.get(f"{folder}/eye_{n}_preview.jpg"),
                         "first_url": urls.get(f"{folder}/eye_{n}_first.jpg"),
                         "second_url": urls.get(f"{folder}/eye_{n}_second.jpg"),
                         "qa": m.get("qa"), "preview": m.get("preview"), "needs_review": store.needs_review(m),
                         "rerendered": bool(m.get("rerendered")), "rerender_available": can,
                         "render_seconds": m.get("render_seconds"), "created": m.get("created"), "bytes": m.get("bytes")}
    return out if (out["draft"] or out["master"]) else None


def a_order(body, who):
    order = _order(body)
    files = pay.folder_files(f"orders/{order}")
    if not files:
        raise store.Answer(404, "not_found", "No files for this order.", False)
    files, names, rec, paid, delivery, mail = order_facts(order, files)
    jsons = [p for p in files if p.endswith(".json")]
    images = [p for p in files if p.endswith((".jpg", ".png"))]
    got = each([lambda p=p: _json_or_none(p) for p in jsons])
    recs = {p: r for p, r in zip(jsons, got) if isinstance(r, dict)}
    signed = each([lambda p=p: store.signed_url(p, SIGN_SECONDS) for p in images])
    urls = {p: u for p, u in zip(images, signed) if isinstance(u, str)}
    logs = each([lambda: [r["name"] for r in store.list_all(f"{ORDERLOG}/{order}") if not r["folder"]],
                 lambda: [r["name"] for r in store.list_all(f"{REFUNDS}/{order}") if not r["folder"]]], width=2)
    log_names = sorted(logs[0] or [], reverse=True)[:60]
    ref_names = logs[1] or []
    extra = each([lambda n=n: _json_or_none(f"{ORDERLOG}/{order}/{n}") for n in log_names] +
                 [lambda n=n: _json_or_none(f"{REFUNDS}/{order}/{n}") for n in ref_names])
    admin_log = [x for x in extra[:len(log_names)] if isinstance(x, dict)]
    refunds = [x for x in extra[len(log_names):] if isinstance(x, dict)]
    is_paid = isinstance(paid, dict) and paid.get("paid") is True
    payments = []
    if is_paid and isinstance(paid.get("payment_intent"), str):
        payments.append({"payment_intent": paid["payment_intent"], "amount": paid.get("amount_total"),
                         "currency": paid.get("currency"), "live": bool(paid.get("livemode")), "kind": "order",
                         "paid": paid.get("paid_iso")})
    for p, r in sorted(recs.items()):
        if p.rsplit("/", 1)[-1].startswith("extra_payment_") and isinstance(r.get("payment_intent"), str):
            payments.append({"payment_intent": r["payment_intent"], "amount": r.get("amount_total"),
                             "currency": r.get("currency"), "live": bool(r.get("livemode")), "kind": "extra",
                             "paid": r.get("paid_iso")})
    refunded = {r.get("payment_intent") for r in refunds}
    for p in payments:
        p["refunded"] = p["payment_intent"] in refunded
    n_eyes = int(((paid or {}).get("spec") or {}).get("eyes") or 0) if is_paid else 0
    eyes = [v for v in (_eye_view(order, n, recs, urls) for n in range(1, 9)) if v]
    arts = []
    for p in sorted(images):
        base = p.rsplit("/", 1)[-1]
        if base.startswith("artwork_") and p.count("/") == 2:
            r = recs.get(p[:-4] + ".json") or {}
            arts.append({"key": p, "url": urls.get(p), "created": r.get("created"), "bytes": r.get("bytes"),
                         "width": r.get("width"), "height": r.get("height"), "qa": r.get("qa"), "style": r.get("style"),
                         "current": isinstance(delivery, dict) and delivery.get("key") == p})
    k_ok = False
    if isinstance(rec, dict):
        try:
            k_ok = pay.link_key(order, rec) is not None
        except Exception:  # noqa: no ticket secret here
            k_ok = False
    began = _began_in(names, n_eyes)
    over = is_paid and _period_over(paid)
    rel = lambda p: p[len(f"orders/{order}/"):]
    return {"ok": True, "order": order, "state": order_state(order, names, rec, paid, delivery, mail),
            "lab": order.startswith("lab-"), "paid": is_paid, "count": n_eyes,
            "email": paid.get("email") if is_paid else None,
            "consent": (paid or {}).get("consent") if is_paid else None,
            "files": [{"path": rel(p), "url": urls.get(p)} for p in files],
            "records": {rel(p): r for p, r in recs.items()},
            "eyes": eyes, "artworks": arts, "payments": payments, "refunds": refunds, "log": admin_log,
            "experiment": abtest.order_view(paid if is_paid else None, rec),
            "making": {"began": began, "period_over": over},
            "can": {"email": pay.email_configured(), "stripe": pay.stripe_configured(), "link": k_ok,
                    "counts": bool(is_paid and pay.paid_counts(paid)), "start": bool(began or over)}}


def _gate_of(prof):
    """{lid, fill} ok flags of a sealed eye profile record (None: unknown)."""
    g = prof.get("gate") if isinstance(prof, dict) else None
    return {r: (g[r].get("ok") if isinstance(g, dict) and isinstance(g.get(r), dict) else None) for r in ("lid", "fill")}


def _steps_view(order, st, spec=None, eyes=None):
    """What the admin needs of one order's master plan: the state SP.read_state read, the capacity at the factor in force, the claims with their age,
    the eyes' ids and sealed results. Everything is a plain number, a code or a record the order folder holds."""
    plan = st["plan"]
    now = time.time()
    locks = {}
    for name, p in (("compose", f"orders/{order}/compose.lock"), (SP.ART, SP.path(order, f"{SP.ART}.lock"))):
        cur = _safe(lambda p=p: store.get_json(p, timeout=5.0, retry=False))
        t = cur.get("t") if isinstance(cur, dict) else None
        locks[name] = {"age_s": round(now - t, 1), "stale": now - t > SP.LOCK_STALE} if isinstance(t, (int, float)) and not isinstance(t, bool) else None
    steps = []
    for s in (plan["steps"] if plan else []):
        steps.append({"name": s["name"], "kind": s["kind"], "eyes": s.get("eyes"), "need_s": s.get("need_s"), "est_mb": s.get("est_mb"),
                      "done": st["done"].get(s["name"]), "try": st["tries"].get(s["name"])})
    cap = SP.capacity(plan) if plan else None
    return {"plan": plan, "steps": steps, "rerun": st["rerun"], "progress": SP.progress(st), "locks": locks, "capacity": cap,
            "factor": SP.CO.slow_factor(), "registry_hash": CT.registry_hash(), "engine_v": SP.ENGINE_V, "eyes": eyes or []}


def a_order_steps(body, who):
    """{order}: one order's master plan for the admin page (read only, nothing is sent or changed): the plan (plan.json), every step with its done record
    (time, CPU, the increase of the resident size, outputs, inputs, drift) and its try record (kills, plate faults, errors, the watchdog), the rerun
    count, the claims and their age, the capacity of the plan at the slow factor in force, the eyes' ids, colour classes and sealed gate results, and
    the record of the artwork the plan made (checks, self checks, seed, plates)."""
    order = _order(body)
    st = SP.read_state(order)
    recs = each([lambda i=i: _json_or_none(f"orders/{order}/draft/eye_{i}.json") for i in range(1, 9)] +
                [lambda: pay.get_paid(order)], tolerant=True)
    paid = recs[8]
    eyes = []
    for i, r in enumerate(recs[:8], 1):
        if isinstance(r, dict):
            prof = r.get("profile") if isinstance(r.get("profile"), dict) else None
            eyes.append({"eye": i, "eye_id": r.get("eye_id"), "cls": prof.get("cls") if prof else None,
                         "pupil": (prof.get("pupil") or {}).get("cls") if prof else None, "gate": _gate_of(prof)})
    out = _steps_view(order, st, (paid or {}).get("spec"), eyes)
    done = st["done"].get((st["plan"] or {"steps": [{"name": SP.ART}]})["steps"][-1]["name"]) if st["plan"] else None
    key = ((done or {}).get("result") or {}).get("key")
    out["artwork"] = _safe(lambda: store.get_json(key[:-4] + ".json", timeout=6.0, retry=False)) if isinstance(key, str) else None
    return dict(out, ok=True, order=order)


def a_lab_steps(body, who):
    """{order: a lab test order (lab-...), style, n (eyes, default every stored eye), layout, names, date, opts, fresh, dry}: the master steps of a v3
    style on the 4096 px masters stored for a lab test order: the same plan, guards, claim and executor as a paid order's (api/_lib/styles/steps.py),
    with no payment and no image model call. Reply: the plan, the capacity, the steps with their wall time, CPU and the increase of the resident size
    (from a fresh instance this is VE1: compare with the cost table), and a link to the artwork. fresh: draw again (a new file beside the old). dry: the
    plan and the capacity only, nothing drawn. 409 step_held when the step must be held (too big for this function, an engine version mismatch, a
    plate missing twice)."""
    order = _order(body)
    if not order.startswith("lab-"):
        raise L.ClientError("Only a lab test order (lab-...) is run this way.")
    style = body.get("style")
    if not isinstance(style, str) or not CT.known(style) or CT.is_legacy(style):
        raise L.ClientError("Name a style of the v3 engine.")
    present = [i for i in range(1, 9) if store.exists(f"orders/{order}/eye_{i}.jpg")]
    n = body.get("n", len(present))
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 8 or present[:n] != list(range(1, n + 1)):
        raise L.ClientError("That test order does not hold the eyes 1 to n as 4096 px masters.")
    if not CT.renderable(style, n):
        raise L.ClientError("This deployment cannot draw that style for that number of eyes.")
    layouts = CT.layouts_for(style, n)
    layout = body.get("layout") or (layouts[0] if layouts else None)
    if layout not in layouts:
        raise L.ClientError(f"{n} eye{'s' if n > 1 else ''} can use: " + ", ".join(layouts) + ".")
    spec = {"eyes": n, "style": style, "layout": layout, "names": body.get("names") if isinstance(body.get("names"), (str, list)) else "",
            "date": body.get("date") if isinstance(body.get("date"), str) else "", "title": "",
            "opts": body.get("opts") if isinstance(body.get("opts"), dict) else {}}
    ctx = SP.Ctx(order, spec, by="lab", lab=True, eyes_from="master", arrival_left=L.time_left())
    ORD = _mod("order")
    claim = ORD._compose_claim(order)
    try:
        try:
            got = SP.lab_run(ctx, fresh=body.get("fresh") is True, dry=body.get("dry") is True)
        except SP.Hold as h:
            raise store.Answer(409, "step_held", f"The master step was held: {h.note}", False, None, hold=h.reason) from h
    finally:
        ORD._compose_release(claim)
    if got.get("dry"):
        return {"ok": True, "result": "dry", "plan": got["plan"], "capacity": got["capacity"], "factor": SP.CO.slow_factor(),
                "audit_detail": f"{style} {n} dry"}
    st = SP.read_state(order)
    view = _steps_view(order, st)
    r = got["artwork"] or {}
    return dict(view, ok=True, order=order, result="same" if r.get("existing") else "made", artwork=r,
                audit_detail=f"{style} {n} eyes {SP.SIZE}")


def a_audit(body, who):
    out = []
    now = time.time()
    for i in range(14):
        if len(out) >= 100 or L.time_left() < 10:
            break
        d = _day_iso(now - i * 86400)
        names = sorted((r["name"] for r in store.list_all(f"{AUDIT}/{d}") if not r["folder"]), reverse=True)
        names = names[:100 - len(out)]
        out += [x for x in each([lambda n=n, d=d: _json_or_none(f"{AUDIT}/{d}/{n}") for n in names]) if isinstance(x, dict)]
    return {"ok": True, "entries": out}


# ----------------------------------------------------------------------------- actions on one order
def _paid_order(order):
    rec, paid = each([lambda: _json_or_none(f"orders/{order}/order.json"), lambda: pay.get_paid(order)], width=2,
                     tolerant=False)
    if not isinstance(rec, dict):
        raise store.Answer(404, "not_found", "There is no such order.", False)
    if not paid:
        raise store.Answer(409, "not_paid", "This order is not paid.", False)
    return rec, paid


def _began_in(names, n):
    """Has making begun, by the files of the order folder (the rule of withdraw._began: making.json, delivery.json
    or any stored eye of the order's n eyes)?"""
    return bool({"making.json", "delivery.json"} & set(names)) or any(f"eye_{i}.jpg" in names for i in range(1, max(1, n) + 1))


def _period_over(paid):
    """Is the 14-day withdrawal period of this paid order over (withdraw.period_end)? Then making it ends nothing."""
    t = paid.get("paid_at") if isinstance(paid, dict) else None
    return isinstance(t, (int, float)) and not isinstance(t, bool) and time.time() >= W.period_end(t)[0]


def _stopped(order):
    w, d, x = each([lambda: store.exists(f"orders/{order}/withdrawn.json"),
                    lambda: store.exists(f"orders/{order}/deleted.json"),
                    lambda: store.exists(f"orders/{order}/expired.json")], width=3, tolerant=False)
    if w:
        raise store.Answer(409, "withdrawn", "The customer withdrew this order: nothing is made for it.", False)
    if d or x:
        raise store.Answer(410, "deleted", "The files of this order are deleted.", False)


def _key(order, rec):
    k = pay.link_key(order, rec)
    if not k:
        raise store.Answer(409, "link_unavailable", "The order link cannot be rebuilt here: the ticket secret changed "
                           "since the order was made.", False)
    return k


def _mail_hold_cleared(order):
    rv = store.get_json(f"orders/{order}/review.json")
    if isinstance(rv, dict) and str(rv.get("reason") or "").startswith(pay.MAIL_REVIEW):
        store.delete(f"orders/{order}/review.json")
        return True
    return False


def act_link(body, who):
    """The customer's two links: withdraw_url (the order page in its withdrawal mode: opening it starts nothing) and
    order_url, to copy into a message to the customer. Opening order_url starts making the file of a paid order, and
    with that the customer's right of withdrawal ends, so the page shows it as text to copy, never as a link."""
    order = _order(body)
    rec = _json_or_none(f"orders/{order}/order.json")
    if not isinstance(rec, dict):
        raise store.Answer(404, "not_found", "There is no such order.", False)
    k = _key(order, rec)
    lang = pay.lang_of(rec.get("lang"))
    paid = pay.get_paid(order)
    if paid:
        lang = pay.lang_of((paid.get("spec") or {}).get("lang"))
    return {"ok": True, "result": "shown", "withdraw_url": pay.withdraw_url(order, k, lang),
            "order_url": pay.order_url(order, k, lang)}


def act_resend_confirmation(body, who):
    order = _order(body)
    rec, paid = _paid_order(order)
    if not pay.email_configured():
        raise store.Answer(409, "email_off", "RESEND_API_KEY is not set on this deployment.", False)
    if not paid.get("email"):
        raise store.Answer(409, "no_address", "No email address is recorded for this order.", False)
    m = store.get_json(f"orders/{order}/mail_delivery.json")
    state = m.get("state") if isinstance(m, dict) else None
    if state == "sent":
        # the customer lost it: the same confirmation once more (a new message; the "sent" mark stays as it was)
        k = _key(order, rec)
        consent = pay.paid_consent(order, rec, paid)
        if consent is None:
            raise store.Answer(409, "no_consent", "No consent is recorded for this order, so there is no confirmation "
                               "to send.", False)
        pack = pay.legal_pack()
        if pack is None or pay.pack_docs(pack, (paid.get("spec") or {}).get("lang"), pay.paid_market(paid)) is None:
            # unreadable, or without the texts of this order's market (the Australian edition): never another's
            raise store.busy("legal_unavailable", 30, "The legal texts (/legal/order-mail.json) could not be read. Try "
                             "again in a moment.")
        subject, text, html_body = pay.confirmation_mail(order, paid, k, pack, consent)
        res = pay.send_mail(paid["email"], subject, text, f"snapeyes-delivery-{order}-copy-{int(time.time())}", html_body)
        return {"ok": True, "result": res, "sent": res == "sent", "copy": True}
    if state == "sending":
        try:
            age = time.time() - float(m.get("t"))
        except (TypeError, ValueError):
            age = pay.CLAIM_STALE + 1
        if age < pay.CLAIM_STALE:
            raise store.Answer(409, "mail_in_progress", "The confirmation is being sent right now. Look again in a "
                               "minute.", True, 60)
    store.delete(f"orders/{order}/mail_delivery.json")          # the failed mark: try again
    res = pay.deliver_mail(order, rec, paid, idem_suffix=f"-r{int(time.time())}")
    cleared = _mail_hold_cleared(order) if res == "sent" else False
    return {"ok": True, "result": res, "sent": res == "sent", "copy": False, "hold_cleared": cleared}


def act_resend_ready(body, who):
    order = _order(body)
    rec, paid = _paid_order(order)
    _stopped(order)
    if not pay.email_configured():
        raise store.Answer(409, "email_off", "RESEND_API_KEY is not set on this deployment.", False)
    dl, released = each([lambda: store.get_json(f"orders/{order}/delivery.json"),
                         lambda: store.exists(f"orders/{order}/release.json")], width=2, tolerant=False)
    if not isinstance(dl, dict):
        raise store.Answer(409, "no_artwork", "The artwork is not made yet.", False)
    if dl.get("needs_review") and not released:
        raise store.Answer(409, "held", "The artwork waits for your review: release it first (that sends the email).", False)
    k = _key(order, rec)
    subject, text, html_body = pay.ready_mail(order, paid, k)
    res = pay.send_mail(paid.get("email"), subject, text, f"snapeyes-ready-{order}-r{int(time.time())}", html_body)
    return {"ok": True, "result": res, "sent": res == "sent"}


def act_release(body, who):
    order = _order(body)
    rec, paid = _paid_order(order)
    _stopped(order)
    dl = store.get_json(f"orders/{order}/delivery.json")
    if not isinstance(dl, dict):
        raise store.Answer(409, "no_artwork", "No artwork yet: the order page composes it once every eye is made.", False)
    store.put(f"orders/{order}/release.json", store.json_bytes({"t": int(time.time()), "iso": pay.iso(), "by": "admin"}),
              "application/json", upsert=True)
    store.delete(f"orders/{order}/review.json")
    mail = None
    held = bool(dl.get("needs_review"))
    if body.get("mail") is not False and not held:
        # an artwork that was never held had its "ready" email when it was made (maker.ready_mail_once): a second
        # one would be a duplicate (and Resend refuses the same idempotency key with another text for 24 h). The
        # panel's resend_ready sends it again on purpose
        mail = "not_held"
    elif body.get("mail") is not False:
        if not pay.email_configured():
            mail = "off"
        else:
            k = pay.link_key(order, rec)
            if not k:
                mail = "link_unavailable"
            else:
                subject, text, html_body = pay.ready_mail(order, paid, k)
                mail = pay.send_mail(paid.get("email"), subject, text, f"snapeyes-ready-{order}", html_body)
    return {"ok": True, "result": "released", "mail": mail, "was_held": held, "audit_detail": f"mail {mail}"}


def act_clear_review(body, who):
    order = _order(body)
    if not isinstance(_json_or_none(f"orders/{order}/order.json"), dict):
        raise store.Answer(404, "not_found", "There is no such order.", False)
    removed = store.delete(f"orders/{order}/review.json")
    return {"ok": True, "result": "removed" if removed else "none", "removed": bool(removed),
            "server": _ask_server(order) if removed else None}


def _ask_server(order):
    """After a hold is lifted: the server's making is asked to go on at once (api/_lib/maker.py kick; its step reads
    the order again and does only what is due), instead of at the customer's next visit or the next daily run.
    Returns kick()'s word; never raises."""
    try:
        from . import maker
        return maker.kick(order, why="admin")
    except Exception as e:  # noqa: the hold is lifted all the same
        log(f"order {order}: server making not asked for: {type(e).__name__}")
        return "failed"


def act_mailed_by_hand(body, who):
    order = _order(body)
    _paid_order(order)
    store.put(f"orders/{order}/mail_delivery.json",
              store.json_bytes({"state": "sent", "by": "owner", "result": "by_hand", "t": round(time.time(), 3),
                                "iso": pay.iso()}), "application/json", upsert=True)
    return {"ok": True, "result": "marked", "hold_cleared": _mail_hold_cleared(order)}


def _draft_input(order, eye):
    """The crop and preview a master is made from (as order.make reads them), checked against their fingerprints."""
    drec = store.get_json(f"orders/{order}/draft/eye_{eye}.json")
    c = drec.get("crop") if isinstance(drec, dict) else None
    p = drec.get("preview") if isinstance(drec, dict) else None
    if not (isinstance(c, dict) and isinstance(p, dict) and isinstance(c.get("path"), str) and isinstance(p.get("path"), str)):
        raise store.Answer(409, "draft_missing", "The uploaded crop and preview of this eye are missing.", False)
    craw, praw = each([lambda: store.get(c["path"], max_bytes=8 << 20, timeout=8.0),
                       lambda: store.get(p["path"], max_bytes=8 << 20, timeout=8.0)], width=2, tolerant=False)
    sha = lambda b: hashlib.sha256(b).hexdigest()
    if craw is None or praw is None or sha(craw) != c.get("sha256") or sha(praw) != p.get("sha256"):
        raise store.Answer(409, "draft_changed", "The uploaded crop or preview of this eye is missing or changed.", False)
    return base64.b64encode(craw).decode("ascii"), base64.b64encode(praw).decode("ascii"), drec.get("pad")


def act_render(body, who):
    """Make one eye that is not made yet (exactly as the order page does: order.make), or render a stored one a
    second time by master_eye's rules: only when its master failed the check and was not rendered again, from the
    same preview. About 30 to 50 s and one 4K render (about $0.15).

    An eye that is not made yet is made here only once making has begun (withdraw._began: the customer's order page
    started it) or the 14-day withdrawal period is over. Making ends the customer's right of withdrawal, and the
    published texts (withdrawal.ts, terms.ts) say we start only while the customer's order page is open or when
    they open it again: the owner starting it here is not among them, so it is refused (409 making_not_started)."""
    order = _order(body)
    rec, paid = _paid_order(order)
    ME = _mod("master_eye")
    eye = ME._eye(body.get("eye"))
    n = int((paid.get("spec") or {}).get("eyes") or 0)
    if eye > n:
        raise L.ClientError(f"This order has {n} eye{'s' if n != 1 else ''}.")
    if not pay.paid_counts(paid):
        raise store.Answer(409, "test_payment", "Paid in Stripe's test mode: nothing is made for it here.", False)
    _stopped(order)
    folder = f"orders/{order}"
    if not store.exists(f"{folder}/eye_{eye}.jpg"):
        began, _ = W._began(order, max(1, n))
        if not began and not _period_over(paid):
            raise store.Answer(409, "making_not_started", "Making has not begun for this order: the customer's order "
                               "page starts it. Starting it here would end the customer's right of withdrawal, which "
                               "the published withdrawal and terms texts do not provide for. Wait until the customer "
                               "opens the order page (the confirmation email links it), or write to them.", False)
        r = _mod("order").make({"order": order, "k": _key(order, rec), "eye": eye})
        return {"ok": True, "result": "made" if not r.get("existing") else "stored", "reply": r}
    erec = store.get_json(f"{folder}/eye_{eye}.json")
    if not ME._can_rerender(erec):
        why = ("it was rendered a second time already" if isinstance(erec, dict) and erec.get("rerendered") else
               "its master passed the check")
        raise store.Answer(409, "rerender_not_allowed", f"master_eye renders an eye a second time only when its master "
                           f"failed the check and was not rendered again: {why}.", False)
    crop, preview, pad = _draft_input(order, eye)
    req = {"order": order, "eye": eye, "ticket": L.mint_ticket(store.unlock_kind(order), 300), "pad": pad,
           "crop": crop, "preview": preview, "rerender": True}
    del crop, preview
    r = ME.master_eye(req)
    return {"ok": True, "result": "rerendered" if r.get("rerendered") and not r.get("existing") else "stored", "reply": r}


def _remake(order, mode):
    """The artwork of a paid order made again by the admin through the master plan (api/_lib/styles/steps.py), under the same claims as the chain: the
    order's compose.lock and the step's own. mode "recompose": the same file when no input changed, a new one when a master was re-rendered (the
    legacy engine decides that itself); "rerun": always a new file (the digest is salted: the delivered file is never deleted, the new one lies beside
    it). The new artwork becomes the order's delivery; one that a check flags waits for your release again."""
    rec, paid = _paid_order(order)
    if not pay.paid_counts(paid):
        raise store.Answer(409, "test_payment", "Paid in Stripe's test mode: nothing is made for it here.", False)
    _stopped(order)
    spec = paid.get("spec") or {}
    n = int(spec.get("eyes") or 0)
    folder = f"orders/{order}"
    made = each([lambda i=i: store.exists(f"{folder}/eye_{i}.jpg") for i in range(1, n + 1)], tolerant=False)
    missing = [i for i, m in enumerate(made, 1) if not m]
    if not n or missing:
        raise store.Answer(409, "eyes_not_ready", "Not every eye is made yet.", False, None, missing=missing)
    ORD = _mod("order")
    arrival = L.time_left()
    claim = ORD._compose_claim(order)
    try:
        try:
            got = SP.advance(ORD.master_ctx(order, rec, paid, "admin", arrival_left=arrival, finish=False, arm=False), mode)
        except SP.Hold as h:
            raise store.Answer(409, "step_held", f"The master step was held: {h.note}", False, None, hold=h.reason) from h
    finally:
        ORD._compose_release(claim)
    r = got["artwork"]
    prev = store.get_json(f"{folder}/delivery.json")
    now = int(time.time())
    delivery = {"key": r["key"], "width": r.get("width"), "height": r.get("height"), "bytes": r.get("bytes"),
                "style": r.get("style"), "layout": r.get("layout"), "count": r.get("count"),
                "needs_review": bool(r.get("needs_review")), "created_at": now, "created": pay.iso(now), "by": "admin"}
    for k in ("design_used", "plan8"):
        if got.get(k) and not CT.is_legacy(spec.get("style")):
            delivery[k] = got[k]
    store.put(f"{folder}/delivery.json", store.json_bytes(delivery), "application/json", upsert=True)
    released = store.exists(f"{folder}/release.json")
    changed = not (isinstance(prev, dict) and prev.get("key") == r["key"])
    if delivery["needs_review"] and released and changed:
        store.delete(f"{folder}/release.json")       # a new, flagged artwork: it waits for your release again
        released = False
    if delivery["needs_review"] and not released:
        pay.index_review(order, now)                  # held: the daily clean-up's reminder after 36 h
    return {"ok": True, "result": "composed" if changed else "same", "changed": changed, "delivery": delivery,
            "held": delivery["needs_review"] and not released, "url": r.get("url"), "ran": got.get("ran"), "plan8": got.get("plan8")}


def act_recompose(body, who):
    """Compose the artwork again from the stored masters (after a re-render: the same file when nothing changed, a new one when an eye did), and make
    it the order's delivery. A new artwork that a check flags waits for your release again. Under the order's compose claim (a compose that is running
    is answered 409 rendering, never doubled)."""
    return _remake(_order(body), "recompose")


def act_rerun_step(body, who):
    """{order, step: "art"}: draw the artwork again whatever changed (a new file beside the delivered one: the digest is salted with the order's rerun
    count, so a link already mailed keeps working), and make it the order's delivery; a flagged one waits for your release. Not for an order of the
    legacy engine (re-render an eye and recompose instead). Same claims as the chain."""
    step = body.get("step", SP.ART)
    if step != SP.ART:
        raise L.ClientError(f"The only step an order has is {SP.ART}.")
    out = _remake(_order(body), "rerun")
    out["result"] = "rerun" if out["changed"] else "same"
    out["audit_detail"] = f"{SP.ART} {out.get('plan8') or ''}"
    return out


def act_refund(body, who):
    """Refund one payment of the order in full through Stripe (POST /v1/refunds). Only with the order number typed as
    confirm, only for a payment intent recorded for this order, once per payment intent."""
    order = _order(body)
    if body.get("confirm") != order:
        raise L.ClientError("Type the order number to confirm the refund.")
    if not pay.stripe_configured():
        raise store.Answer(409, "stripe_off", "Stripe is not configured on this deployment.", False)
    pi = body.get("payment_intent")
    if not isinstance(pi, str) or not _PI.fullmatch(pi):
        raise L.ClientError("Choose the payment to refund.")
    paid = pay.get_paid(order)
    extras = [p for p in pay.folder_files(f"orders/{order}") if p.rsplit("/", 1)[-1].startswith("extra_payment_")]
    known = [paid.get("payment_intent")] if paid else []
    known += [x.get("payment_intent") for x in each([lambda p=p: _json_or_none(p) for p in extras]) if isinstance(x, dict)]
    if pi not in known:
        raise store.Answer(409, "unknown_payment", "This payment is not recorded for this order.", False)
    path = f"{REFUNDS}/{order}/{hashlib.sha256(pi.encode()).hexdigest()[:16]}.json"
    prev = store.get_json(path)
    if isinstance(prev, dict):
        raise store.Answer(409, "already_refunded", "This payment was refunded before.", False, None, refund=prev)
    r = pay._stripe("POST", "/v1/refunds", [("payment_intent", pi), ("reason", "requested_by_customer"),
                                            ("metadata[order]", order), ("metadata[by]", "snapeyes-admin")],
                    idem=f"snapeyes-refund-{pi}"[:255], timeout=20.0)
    if r.status_code != 200:
        pay._raise_for(r, "stripe refund")
    try:
        ref = r.json()
    except ValueError:
        raise pay.PayBusy("stripe refund: unreadable reply") from None
    rec = {"refund": ref.get("id"), "status": ref.get("status"), "amount": ref.get("amount"),
           "currency": ref.get("currency"), "payment_intent": pi, "t": int(time.time()), "iso": pay.iso(), "by": "admin"}
    try:
        store.put(path, store.json_bytes(rec), "application/json", upsert=True)
    except store.StorageError as e:
        log(f"order {order}: refund {rec['refund']} done at Stripe, its record not stored: {e}")
    return {"ok": True, "result": _code(rec["status"]) or "refunded", "refund": rec,
            "audit_detail": f"{rec['refund']} {rec['amount']} {rec['currency']}"}


def act_mark_refunded(body, who):
    """You refunded the order in the Stripe Dashboard yourself: orders/<order>/refunded.json, the same mark as
    scripts/order_admin.py refunded ORDER (kept with the order's records), so the daily clean-up sends no reminder."""
    order = _order(body)
    _, paid = _paid_order(order)
    note = str(body.get("note") or "")[:200]
    store.put(f"orders/{order}/refunded.json", store.json_bytes({"t": int(time.time()), "iso": pay.iso(), "by": "admin",
                                                                "amount": paid.get("amount_total"), "note": note}),
              "application/json", upsert=True)
    return {"ok": True, "result": "marked"}


def act_delete_files(body, who):
    """Delete the order's files now (a customer's request): pay.erase_files, so a paid order keeps its records (and
    its admin log) and says "deleted"; an unpaid order or a lab test goes completely, its admin log
    (ops/orderlog/<order>/) with it, and this action writes no new entry there. Only with the order number typed as
    confirm."""
    order = _order(body)
    if body.get("confirm") != order:
        raise L.ClientError("Type the order number to confirm the deletion.")
    if order.startswith("lab-"):
        files = pay.folder_files(f"orders/{order}")
        if files:
            store.delete_many(files)
        pay.drop_orderlog(order, out=log)
        store.delete(f"{LAB}/{order}.json")
        return {"ok": True, "result": "deleted", "deleted": len(files), "of": len(files), "orderlog": False}
    gone, total = pay.erase_files(order, "admin", yes=True, out=log)
    if not total:
        raise store.Answer(404, "not_found", "No files for this order.", False)
    # everything went (an unpaid order: erase_files dropped its admin log too), or a paid order's records stay
    return {"ok": True, "result": "deleted", "deleted": gone, "of": total, "audit_detail": f"{gone} of {total} files",
            "orderlog": gone < total}


# ----------------------------------------------------------------------------- the price experiments
def _returned(order, row):
    """Was this paid order given back: withdrawn by the customer, refunded in the Stripe Dashboard (refunded.json) or
    refunded from the admin panel (maker.refund_marks)?"""
    if row.get("state") == "withdrawn":
        return True
    from . import maker
    marks = maker.refund_marks(order, pay.get_paid(order))
    return any(store.exists(p, timeout=5.0, retry=False) for p in marks)


def _exp_orders(days):
    """(rows, more): the order rows of the last `days` days, with "returned" set on the live payments of price tests."""
    res = a_orders({"days": days}, None)
    rows = res["orders"]
    todo = [r for r in rows if r.get("experiment") and r.get("paid") and r.get("live") is True]
    for r, x in zip(todo, each([lambda r=r: _returned(r["order"], r) for r in todo])):
        r["returned"] = x is True
    return rows, bool(res.get("more"))


def a_experiments(body, who):
    """The page "Kainų testai": the definitions, states, per-variant funnel, revenue, significance and warnings, and the
    experiments' lines of the audit log (abtest.admin_view; the visitors, previews and payment pages come from the events
    through collect_days like the statistics, the paid orders and the revenue from the order records)."""
    try:
        entries = a_audit({}, who)["entries"]
    except store.StorageNotConfigured:
        raise
    except Exception as e:  # noqa: the page works without the log
        log(f"experiments: audit not read: {type(e).__name__}")
        entries = []
    st = abtest.states(force=True)
    started = [k for k in abtest.DEFS if (st.get(k) or {}).get("since")]
    orders, more = None, False
    if started:
        try:
            orders, more = _exp_orders(max(abtest.window_days(st[k]) for k in started))
        except store.StorageNotConfigured:
            raise
        except Exception as e:  # noqa: the page then counts from the events
            log(f"experiments: orders not read: {type(e).__name__}")
    return abtest.admin_view(collect_days, audit=entries, ordering_open=not pay.ordering_problem() and not store.problem(),
                             orders=orders, orders_more=more, collecting=E.retention_ok())


def act_exp_start(body, who):
    """Switch a price experiment on (abtest.start: 409 when it runs, when another runs in one of its markets, and when a
    variant would sell at a loss unless accept_loss is true; 409 stats_not_collected when this deployment stores no events
    (no CRON_SECRET) unless accept_no_stats is true). From then on visitors of its markets are assigned to a variant and
    charged that variant's ladder; nothing else about an order changes. The audit line says which risks were accepted."""
    key = abtest.check_key(body.get("key"))
    no_stats = body.get("accept_no_stats") is True
    if not E.retention_ok() and not no_stats:
        raise store.Answer(409, "stats_not_collected", "This deployment stores no usage events (CRON_SECRET), so the visitor "
                           "and preview counts would stay at zero.", False)
    loss = body.get("accept_loss") is True
    st = abtest.start(key, accept_loss=loss)
    flags = (" accept_loss" if loss else "") + (" accept_no_stats" if no_stats and not E.retention_ok() else "")
    return {"ok": True, "result": "started", "key": key, "state": st, "audit_detail": key + flags}


def act_exp_stop(body, who):
    """Switch a price experiment off (abtest.stop): no new visitor is assigned, everybody pays the standard ladder again;
    a checkout already open keeps its variant's price and is still recorded."""
    key = abtest.check_key(body.get("key"))
    st = abtest.stop(key)
    return {"ok": True, "result": "stopped", "key": key, "state": st, "audit_detail": key}


# ----------------------------------------------------------------------------- the lab
def act_lab_start(body, who):
    """A test order for the lab's 4K master: an id lab-<yymmdd>-<rand>, its marker ops/lab/<id>.json, and an unlock
    ticket for it (LAB_TICKET seconds) the page sends to /api/master_eye and /api/master_compose itself."""
    if not store.configured():
        raise store.StorageNotConfigured(store.problem())
    order = f"lab-{pay.day()}-{secrets.token_hex(4)}"
    store.put(f"{LAB}/{order}.json", store.json_bytes({"order": order, "t": int(time.time()), "iso": pay.iso(),
                                                      "test": True, "by": "admin"}), "application/json", upsert=False)
    return {"ok": True, "result": "started", "order": order, "ticket": L.mint_ticket(store.unlock_kind(order), LAB_TICKET),
            "expires_in": LAB_TICKET, "prices_usd": PRICES_USD}


def a_lab_list(body, who):
    marked = {r["name"][:-5] for r in store.list_all(LAB) if not r["folder"] and r["name"].endswith(".json")}
    stored = {o for o in order_folders(1, lab=True) if o.startswith("lab-")}
    rows = sorted((o for o in marked | stored if store.ORDER_RE.fullmatch(o) and o.startswith("lab-")), reverse=True)[:30]

    def one(o):
        files = pay.folder_files(f"orders/{o}")
        arts = [p for p in files if p.rsplit("/", 1)[-1].startswith("artwork_") and p.endswith(".jpg")]
        eyes = [p for p in files if re.fullmatch(r"eye_[1-8]\.jpg", p.rsplit("/", 1)[-1])]
        return {"order": o, "files": len(files), "eyes": len(eyes),
                "artwork_url": store.signed_url(arts[-1], SIGN_SECONDS) if arts else None,
                "eye_url": store.signed_url(eyes[0], SIGN_SECONDS) if eyes else None}
    got = [r for r in each([lambda o=o: one(o) for o in rows], width=8) if isinstance(r, dict)]
    # a folder with nothing left in it and no marker is a deleted test (the local test store keeps empty folders)
    return {"ok": True, "lab": [r for r in got if r["files"] or r["order"] in marked]}


# ----------------------------------------------------------------------------- the CPU probe
def a_cpu_probe(body, who):
    """{mode: "cold"|"warm", runs: 1 to 5, baseline: {phases|total}}: a fixed CPU workload run on this instance (api/_lib/
    cpu_probe.py). Seconds per phase and in all, the slow factor against the baseline the caller sends (the same code run on
    the developer machine the same day: scripts/cpu_probe.py --remote does both), the configured STYLE_SLOW_CPU, and the
    instance's own facts (memory, CPUs, /tmp). It reads nothing from storage and changes nothing, so it is not in the audit
    log. 400 for a bad request, 503 probe_running while another probe of this instance is under way."""
    from . import cpu_probe as P
    try:
        return P.run_action(body, L.time_left)
    except BlockingIOError:
        raise store.busy("probe_running", 10, "Another probe is running on this instance. Try again in a few seconds.")
    except ValueError as e:
        raise L.ClientError(str(e))


# ----------------------------------------------------------------------------- the plate library
def a_plates_status(body, who):
    """{deep: bool, storage: bool, families: [family ids]}: the plate library as this function sees it. bundle: every usable plate's 1K
    file in api/_assets/plates with the size the baked registry records (deep: and its sha256), the two atlases; registry: the style
    registry's hash and plates version, the plates version of the baked library, the number of plates; storage (only when asked: one
    request per plate, so it is bounded to the families named, default the families of the first release): the 4K plates in private
    storage, with a downloaded and hashed sample. Reads and changes nothing (no write, no audit line); this function is a rendering
    one, so its bundle is the bundle of compose, master_compose and order."""
    from . import catalogue as CT
    from . import plates_registry as PR
    from .styles import atlas as AT, plates as PL, costs as CO
    deep = bool(body.get("deep"))
    out = {"ok": True, "bundle": PL.bundle_status(deep=deep), "atlas": AT.status(),
           "registry": {"styles_hash": CT.registry_hash(), "plates_version": CT.PLATES_VERSION, "library_version": PR.PLATES_VERSION,
                        "plates": len(PR.PLATES_REGISTRY["plates"]), "usable": sum(PL.families().values()),
                        "families": {f: {"usable": n, "store4k": PR.PLATES_REGISTRY["families"][f]["store4k"],
                                         "release1": PR.PLATES_REGISTRY["families"][f]["release1"]} for f, n in PL.families().items()}},
           "function": {"memory_mb": CO.FUNCTION_MEM_MB, "memory_budget_mb": CO.MEM_BUDGET_MB, "cache": PL.cache_dir()}}
    if body.get("storage"):
        fams = body.get("families")
        if fams is None:
            fams = [f for f, d in PR.PLATES_REGISTRY["families"].items() if d["release1"]]
        if not isinstance(fams, list) or not all(isinstance(f, str) and f in PR.PLATES_REGISTRY["families"] for f in fams):
            raise L.ClientError("families must be a list of plate family ids")
        out["storage"] = PL.storage_status(fams, deep=True)
    out["ok"] = out["bundle"]["ok"] and out["atlas"]["ok"] and out["registry"]["library_version"] == out["registry"]["plates_version"]         and out.get("storage", {"ok": True})["ok"]
    return out


# ----------------------------------------------------------------------------- the style laboratory
LAB_SIZES = (480, 1024, 2048, 4096)       # the long side of a laboratory render
LAB_VIEW = 1536                           # a render above 2048 px comes back reduced to this (a 4096 px JPEG does not fit a 4.5 MB reply)
LAB_CROP = 1280                           # ... with one window of it at 100 percent, where the rim of the iris is
LAB_EYE_B64 = 4_300_000                   # an eye sent as an image: the reply and request bodies are limited to 4.5 MB


def _lab_number(v):
    """A finite number of a request (a JSON number), else None: a boolean, a text, NaN, an infinity and an integer too large for a float are no number."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    try:
        f = float(v)
    except OverflowError:
        return None
    return f if f - f == 0.0 else None


def _lab_words(value, what):
    """The customer's words of a laboratory request as the drawer takes them: the names as one cleaned lockup line (text, or a list of up to 16 texts),
    the date as one cleaned line. What the drawer would refuse is a 400 that says so, never the generic "could not read that image" that a ValueError
    of the drawer would become: a line over the drawer's limit, and a letter the artwork font cannot draw (checkout refuses such a name too: the
    laboratory shows what a delivered file would hold, so it does not leave the letter out as a free preview does)."""
    from .styles import text as TX
    if value is None or value == "":
        return ""
    if not (isinstance(value, str) or (what == "names" and isinstance(value, (list, tuple)) and len(value) <= 16 and all(isinstance(v, str) for v in value))):
        raise L.ClientError(f"{what} is text" + (", or a list of up to 16 texts." if what == "names" else "."))
    line = TX.lockup(value) if what == "names" else TX.clean(value)
    if len(line) > TX.LINE_MAX:
        raise L.ClientError(f"{what} is {len(line)} characters long once cleaned: one line of the artwork takes at most {TX.LINE_MAX}.")
    bad = TX.unsupported(line)
    if bad:
        raise L.ClientError(f"{what} holds letters the artwork font cannot draw ({' '.join(bad[:10])}): a delivered file would print them as empty boxes.")
    return line


def a_styles_lab(body, who):
    """{style, eye | order + n, format, size, names, date, crop}: one style of the v3 engine (api/_lib/styles) drawn on ONE restored iris,
    whatever the style's stage (a held or not yet visible style is looked at here, never by a customer). eye: the base64 of a restored iris
    square (the 1024 px square the site's own restoration makes, the iris centred as /api/enhance leaves it); or order: the id of a lab test
    order (lab-...) and n its eye number: the stored 4K master eye of that test order, so a style can be looked at on a real master without
    another call to the image model. This action calls no image model, stores nothing and is not audited (it only costs CPU).
    format: a canvas id of the style ("1:1" ...); size: 480, 1024, 2048 or 4096 (the long side). names and date are the customer's words,
    drawn under the iris when given (a line the drawer cannot take, over 256 characters or with a letter the font lacks, is a 400 that says which).
    crop: [x, y] the centre of the 100 percent window, in canvas pixels (default: the upper right rim).
    A render above 2048 px comes back as a reduced view plus the window at full size. 4096 px is refused when the cost table says it cannot
    finish inside the time or the memory this function has (the rule a paid master is held to), and answers 409 plate_unavailable when a
    plate of the design has no 4K file in storage. Without a style the reply is the list of styles to choose from ({styles, sizes}).
    Reply: ok, style, design, canvas, width, height, image (JPEG, b64), view, crop, cls, seed (a text: a 64 bit number is not safe in a page's JSON),
    facts, plan, selfcheck, times, estimate."""
    import io as _io
    from . import catalogue as CT
    from . import styles as ST
    from .styles import core as SC
    from .styles import costs as CO
    from .styles import plates as PL
    style = body.get("style")
    if style is None:
        # no style: the list the page builds its menu from (the styles of the v3 engine this deployment can draw, with their stage)
        rows = []
        for i in CT.renderable_ids(1):
            e = CT.engine_for(i, 1)
            if CT.is_legacy(i) or e is None:
                continue
            rows.append({"id": i, "name": CT.name_of(i), "design": e["design"], "module": e["module"], "ceiling": CT.ceiling(i, 1),
                         "stage": CT.stage_of(i, 1), "gate": CT.gate_policy(i), "canvases": e["canvases"], "plates": e["plates"]})
        return {"ok": True, "styles": rows, "sizes": list(LAB_SIZES)}
    if not isinstance(style, str) or not CT.renderable(style, 1) or CT.is_legacy(style):
        raise L.ClientError("Not a style of the v3 engine.")
    eng = CT.engine_for(style, 1)
    if eng is None or eng.get("module") == "legacy":
        raise L.ClientError("Not a style of the v3 engine.")
    size = body.get("size", 1024)
    if isinstance(size, bool) or size not in LAB_SIZES:
        raise L.ClientError(f"size is one of {', '.join(str(x) for x in LAB_SIZES)}.")
    fmt = body.get("format") if body.get("format") in eng["canvases"] else eng["canvases"][0]
    # the eye: an image sent, or the stored eye of a lab test order
    order = body.get("order")
    if order is not None:
        n = body.get("n", 1)
        if (not isinstance(order, str) or not order.startswith("lab-") or not store.ORDER_RE.fullmatch(order) or isinstance(n, bool)
                or n not in range(1, 9)):
            raise L.ClientError("order is a lab test order (lab-...) and n an eye number from 1 to 8.")
        if not store.configured():
            raise store.StorageNotConfigured(store.problem())
        data = store.get(f"orders/{order}/eye_{n}.jpg", max_bytes=16 << 20)
        if data is None:
            raise L.ClientError("That test order has no such eye.")
    else:
        eye = body.get("eye")
        if not isinstance(eye, str) or not eye or len(eye) > LAB_EYE_B64:
            raise L.ClientError("Send eye as the base64 of a restored iris square, or order and n.")
        try:
            data = base64.b64decode(eye.split(",", 1)[1] if (eye.startswith("data:") and "," in eye[:64]) else eye)
        except Exception:
            raise L.ClientError("That is not a readable image.") from None
    try:
        probe = L.Image.open(_io.BytesIO(data))
        pixels = probe.size[0] * probe.size[1]
        probe.verify()
    except L.Image.DecompressionBombError:
        raise L.ClientError(f"That image is too large (over {2 * L.MAX_PIXELS // 1_000_000} megapixels).") from None
    except Exception:
        raise L.ClientError("That is not a readable image.") from None
    if pixels > L.MAX_PIXELS:      # the limit of every request that carries a photo (a flat 9000 px file is a few KB and 240 MB of pixels)
        raise L.ClientError(f"That image is too large ({pixels // 1_000_000} megapixels, the limit is {L.MAX_PIXELS // 1_000_000}).")
    design_key = CO.cost_key(eng)
    try:
        est = CO.assess(design_key, 1) if size == 4096 else {"need_s": round(CO.preview_need(design_key, 1, size), 2), "ok": True, "why": None, "est_mb": None}
    except CO.NoCost:
        est = {"need_s": None, "ok": True, "why": "no_cost", "est_mb": None}
    if not est.get("ok") and est.get("why") in ("time", "memory"):
        raise L.ClientError(f"A 4096 px render of this design would not fit this function ({est['why']}: needs about {est.get('need_s')} s and "
                            f"{est.get('est_mb')} MB).")
    spec = {"style": style, "layout": "single", "eyes": 1, "canvas": fmt, "names": _lab_words(body.get("names"), "names"), "date": _lab_words(body.get("date"), "date")}
    try:
        iris = SC.Iris(data, "lab", max_side=4096 if size == 4096 else 2048)
    except (OSError, SyntaxError, ValueError, L.Image.DecompressionBombError):     # a truncated file passes verify() and fails when its pixels are decoded
        raise L.ClientError("That is not a readable image.") from None
    try:
        pv = ST.preview([iris], spec, size=size, check=True)
    except PL.PlateUnavailable as e:
        raise store.Answer(409, "plate_unavailable", "A plate this design needs is not in storage.", False, None, plate=str(e.plate_id)[:80], why=e.why)
    img = pv.img
    out = {"ok": True, "style": style, "design": pv.design, "canvas": pv.fmt, "width": img.size[0], "height": img.size[1], "cls": pv.cls, "seed": str(pv.seed),
           "facts": pv.log, "plan": ST.resolve(spec, None), "selfcheck": pv.selfcheck, "times": pv.times, "estimate": est}
    if size > 2048:
        crop = body.get("crop")
        d = pv.discs[0]
        xy = [_lab_number(v) for v in crop] if isinstance(crop, list) and len(crop) == 2 else []
        if len(xy) == 2 and None not in xy:
            cx, cy = xy
        else:
            cx, cy = d[0] + 0.72 * d[2], d[1] - 0.72 * d[2]
        x0 = int(min(max(cx - LAB_CROP / 2.0, 0), max(img.size[0] - LAB_CROP, 0)))
        y0 = int(min(max(cy - LAB_CROP / 2.0, 0), max(img.size[1] - LAB_CROP, 0)))
        win = img.crop((x0, y0, min(x0 + LAB_CROP, img.size[0]), min(y0 + LAB_CROP, img.size[1])))
        f = LAB_VIEW / float(max(img.size))
        view = img.resize((max(1, round(img.size[0] * f)), max(1, round(img.size[1] * f))), L.Image.LANCZOS)
        out["image"], out["view"] = L.pil_to_b64(view, "JPEG", 90), list(view.size)
        out["crop"] = {"x": x0, "y": y0, "w": win.size[0], "h": win.size[1], "image": L.pil_to_b64(win, "JPEG", 92)}
    else:
        out["image"], out["view"], out["crop"] = L.pil_to_b64(img, "JPEG", 90), list(img.size), None
    return out


# ----------------------------------------------------------------------------- serving
ACTIONS = {
    "me": a_me, "summary": a_summary, "stats": a_stats, "errors": a_errors, "orders": a_orders, "order": a_order,
    "audit": a_audit, "lab_list": a_lab_list, "experiments": a_experiments, "cpu_probe": a_cpu_probe, "plates_status": a_plates_status,
    "styles_lab": a_styles_lab, "order_steps": a_order_steps,
    "exp_start": audited("exp_start", act_exp_start),
    "exp_stop": audited("exp_stop", act_exp_stop),
    "link": audited("link", act_link),
    "resend_confirmation": audited("resend_confirmation", act_resend_confirmation),
    "resend_ready": audited("resend_ready", act_resend_ready),
    "release": audited("release", act_release),
    "clear_review": audited("clear_review", act_clear_review),
    "mailed_by_hand": audited("mailed_by_hand", act_mailed_by_hand),
    "render": audited("render", act_render),
    "recompose": audited("recompose", act_recompose),
    "rerun_step": audited("rerun_step", act_rerun_step),
    "lab_steps": audited("lab_steps", a_lab_steps),
    "refund": audited("refund", act_refund),
    "mark_refunded": audited("mark_refunded", act_mark_refunded),
    "delete_files": audited("delete_files", act_delete_files),
    "lab_start": audited("lab_start", act_lab_start),
    "lab_delete": audited("lab_delete", lambda body, who: act_delete_files(dict(body, confirm=body.get("order")), who)
                          if str(body.get("order") or "").startswith("lab-") else _not_lab()),
}


def _not_lab():
    raise L.ClientError("Only a lab test order (lab-...) can be deleted this way.")


def dispatch(req, body):
    who = authorize(req)
    act = body.get("action")
    fn = ACTIONS.get(act) if isinstance(act, str) else None
    if fn is None:
        raise L.ClientError("Unknown action.")
    return fn(body, who)


def serve(req):
    """L.run with its gates (application/json, this site's Origin), the admin key checked first, and the replies of
    store.Answer and the payment errors mapped to their own status (as pay.serve does, but the panel also works on a
    deployment without storage: its summary says what is missing)."""
    box = store._StatusReq(req)

    def wrapped(body):
        try:
            return dispatch(req, body)
        except store.StorageNotConfigured:
            a = store.Answer(503, "storage_not_configured", "Storage is not configured on this deployment.", False)
        except store.StorageError as e:
            log(f"storage error: {e}")
            a = store.busy("storage_busy", 10, "Storage did not answer. Please try again in a moment.")
        except pay.PayNotConfigured as e:
            a = store.Answer(503, "payments_not_configured", "Stripe refused the key or is not configured.", False,
                             None, detail=pay.scrub(str(e))[:240])
        except pay.PayBusy as e:
            a = store.busy("payments_busy", 10, "Stripe did not answer. Please try again in a moment.")
            a.body["detail"] = pay.scrub(str(e))[:240]
        except pay.PayError as e:
            a = store.Answer(502, "payments_error", "Stripe refused the request.", False, None,
                             detail=pay.scrub(str(e))[:240])
        except store.Answer as e:
            a = e
        box.status, box.retry_after = a.status, a.retry_after
        return dict(a.body)
    L.run(box, wrapped)
